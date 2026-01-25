import time
import requests
import os
import easyocr
import numpy as np
from PIL import ImageGrab
import pyautogui
from pywinauto.application import Application
from utils.email_sender import send_email
import threading
import base64
from io import BytesIO
import socket

def is_local_backend_available():
    """Check if local backend at localhost:3001 is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 3001))
        sock.close()
        return result == 0
    except Exception:
        return False

# Determine API URL based on local backend availability
if is_local_backend_available():
    API_URL = "http://localhost:3001/api"
    print("[Bot] Using LOCAL development API")
else:
    API_URL = os.getenv("API_URL")
    if not API_URL:
        raise ValueError("API_URL environment variable not set and local backend not available")
    print(f"[Bot] Using PRODUCTION API: {API_URL}")

MASTER_PASSWORD = os.getenv("MASTER_PASSWORD")

# Globals for thread communication
CURRENT_COMMAND = "WAIT"
CURRENT_SERVER_LEVEL = 1
TARGET_LEVEL = 0
TRIGGER_RELAUNCH = False
HEARTBEAT_LOCK = threading.Lock()

# OCR Config
reader = easyocr.Reader(['en'])
SQUARE_TOP_LEFT = (810, 287)
SQUARE_BOTTOM_RIGHT = (870, 321)

# Game Config
START_CONTINUE_POS = (1434, 732)
WON_LOST_POS = (1700, 187)
AUTO_POS = (1500, 717)
LOST_RGB = (58, 63, 68)

def log(msg):
    print(f"[Bot] {msg}")

def focus_kings_call():
    try:
        app = Application().connect(title="Kings call")
        kings_call = app.window(title="Kings call")
        kings_call.set_focus()
        log("Window focused.")
        time.sleep(0.5)
    except Exception as e:
        log(f"Error focusing window: {e}")

def get_pixel_color(x, y):
    img = ImageGrab.grab()
    return img.getpixel((x, y))

def api_post(endpoint, payload):
    try:
        payload["masterPassword"] = MASTER_PASSWORD
        url = f"{API_URL}/{endpoint}"
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log(f"API Error ({endpoint}): {e}")
        return None

def get_ocr_level():
    log("Reading level via OCR...")
    bbox = (SQUARE_TOP_LEFT[0], SQUARE_TOP_LEFT[1], SQUARE_BOTTOM_RIGHT[0], SQUARE_BOTTOM_RIGHT[1])
    screenshot = ImageGrab.grab(bbox=bbox)
    screenshot_np = np.array(screenshot)
    results = reader.readtext(screenshot_np)
    text = "".join([r[1] for r in results])
    
    # Clean text to int
    try:
        # filter digits
        digits = "".join(filter(str.isdigit, text))
        val = int(digits)
        log(f"OCR detected level: {val}")
        return val
    except:
        log(f"OCR failed to parse level from '{text}', defaulting to 1")
        return 1

def take_and_upload_screenshot():
    log("Taking requested screenshot...")
    try:
        # focus_kings_call() # Optional: ensure window is visible
        img = ImageGrab.grab()
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=60)
        img_str = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()
        
        api_post("bot/upload_screenshot", { "image": img_str })
        log("Screenshot uploaded.")
    except Exception as e:
        log(f"Screenshot failed: {e}")

def heartbeat_thread_func():
    global CURRENT_COMMAND, CURRENT_SERVER_LEVEL, TARGET_LEVEL, TRIGGER_RELAUNCH
    log("Heartbeat thread started.")
    while True:
        try:
            res = api_post("bot/heartbeat", {})
            if res and res.get("success"):
                data = res.get("data", {})
                with HEARTBEAT_LOCK:
                    CURRENT_COMMAND = data.get("command", "WAIT")
                    CURRENT_SERVER_LEVEL = data.get("current_level", 1)
                    TARGET_LEVEL = data.get("target_level", 0)
                    TRIGGER_RELAUNCH = data.get("trigger_relaunch", False)
                
                if data.get("trigger_screenshot"):
                    take_and_upload_screenshot()
        except Exception as e:
            log(f"Heartbeat Loop Error: {e}")
        
        time.sleep(2)

def check_backend_instruction():
    # Returns (command, server_level, target_level, trigger_relaunch) from local cache (updated by thread)
    with HEARTBEAT_LOCK:
        return CURRENT_COMMAND, CURRENT_SERVER_LEVEL, TARGET_LEVEL, TRIGGER_RELAUNCH

def kill_game():
    """Kill the game process"""
    log("Killing Game.exe...")
    try:
        os.system("taskkill /f /im Game.exe")
        time.sleep(2)
        log("Game process killed.")
        return True
    except Exception as e:
        log(f"Error killing game: {e}")
        return False

def launch_game():
    """Launch the game via Steam and navigate through menus"""
    log("Launching game via Steam...")
    try:
        os.system("start steam://rungameid/2674290")
        
        # Wait for game to load
        log("Waiting 30 seconds for game to load...")
        time.sleep(30)
        
        # Click sequence to navigate through menus
        log("Clicking at (967, 814)...")
        pyautogui.click(967, 814)
        
        log("Waiting 1 minute...")
        time.sleep(60)
        
        log("Clicking at (1679, 208)...")
        pyautogui.click(1679, 208)
        time.sleep(1)
        
        log("Clicking at (879, 587)...")
        pyautogui.click(879, 587)
        time.sleep(1)
        
        log("Clicking at (675, 412)...")
        pyautogui.click(675, 412)
        time.sleep(1)
        
        log("Clicking at (769, 719)...")
        pyautogui.click(769, 719)
        time.sleep(1)
        
        log("Game launch complete.")
        return True
    except Exception as e:
        log(f"Error during launch: {e}")
        return False

def relaunch_game():
    """Kill and relaunch the game"""
    log("Relaunching game...")
    
    if not kill_game():
        return False
    
    if not launch_game():
        return False
    
    # Clear the relaunch flag
    log("Clearing relaunch flag...")
    api_post("bot/heartbeat", {})
    
    # Reset the local flag
    global TRIGGER_RELAUNCH
    with HEARTBEAT_LOCK:
        TRIGGER_RELAUNCH = False
    
    log("Game relaunch complete. Ready to resume.")
    return True

def report_outcome(result, level, duration):
    log(f"Reporting {result} for Level {level} (Duration: {duration:.2f}s)")
    api_post("bot/report", {
        "result": result,
        "level": int(level),
        "duration": duration
    })

def play_level(level_number):
    start_time = time.time()
    
    # 1. Click Start
    log(f"Starting Level {level_number}...")
    pyautogui.click(START_CONTINUE_POS)
    time.sleep(2)
    
    # 2. Click Auto
    pyautogui.click(AUTO_POS)
    time.sleep(1)
    
    # 3. Wait for result
    initial_color = get_pixel_color(*WON_LOST_POS)
    log(f"Waiting for game end (watched color: {initial_color})...")

    while True:
        # Check for relaunch request during gameplay
        _, _, _, should_relaunch = check_backend_instruction()
        if should_relaunch:
            log("Relaunch requested during gameplay, aborting level...")
            return None, 0  # Special return value to signal relaunch
        
        current_color = get_pixel_color(*WON_LOST_POS)
        if current_color != initial_color:
            break
        time.sleep(0.5)

    duration = time.time() - start_time
    
    # Check Result
    color_after = get_pixel_color(*WON_LOST_POS)
    if color_after == LOST_RGB:
        log("Result: LOSS")
        return False, duration
    
    log("Result: WIN")
    return True, duration

def handle_rewards():
    # Reward logic from v2
    time.sleep(1)
    screen_width, screen_height = pyautogui.size()
    center_x, center_y = screen_width // 2, screen_height // 2
    log("Clicking reward (center)...")
    pyautogui.click(center_x, center_y)
    
    log("Waiting 7s for summary...")
    time.sleep(7)
    
    log("Dismissing summary...")
    pyautogui.click(1250, 450)
    time.sleep(1)

def main():
    log("Initializing Tower V3 Bot...")
    
    # Launch the game on script start
    launch_game()
    
    # Reset levels completed on launch
    log("Resetting levels completed count...")
    api_post("control/reset_levels", {})
    
    focus_kings_call()

    # Start Heartbeat Thread
    t = threading.Thread(target=heartbeat_thread_func, daemon=True)
    t.start()
    
    # 1. Detect Level
    current_level = get_ocr_level()
    
    # 2. Sync Initial State
    report_outcome("INIT", current_level, 0)
    
    levels_since_email = 0
    
    while True:
        # Check if relaunch requested
        _, _, _, should_relaunch = check_backend_instruction()
        if should_relaunch:
            success = relaunch_game()
            if success:
                # Re-detect level after relaunch
                focus_kings_call()
                current_level = get_ocr_level()
                log(f"After relaunch, detected level: {current_level}")
            continue
        
        # Check if reached target level
        with HEARTBEAT_LOCK:
            target = TARGET_LEVEL
        
        if target > 0 and current_level >= target:
            log(f"Reached target level {target}! Bot completed assigned levels. Idling...")
            time.sleep(5)
            continue
        
        # Check Backend (from cache)
        cmd, _, _, _ = check_backend_instruction()
        
        if cmd == "STOP":
            log("Backend said STOP. Idling...")
            time.sleep(5)
            continue

        # cmd == "CONTINUE" -> We are allowed to play.
        # We use our local current_level tracker, but we could sync with server if we wanted.
        # Requirement: "Increment locally, Sync updates to the backend"
        
        result = play_level(current_level)
        
        # Handle relaunch during gameplay
        if result[0] is None:
            log("Level aborted due to relaunch request")
            continue  # Go back to top of loop which will handle the relaunch
        
        won, duration = result
        
        if won:
            report_outcome("WIN", current_level, duration)
            handle_rewards()
            
            levels_since_email += 1
            if levels_since_email >= 5: # Email every 5 levels won
                send_email(
                    subject=f"Auto-Click: {levels_since_email} Levels Won (Total: {current_level})",
                    body=f"Progress update. Just beat level {current_level}."
                )
                levels_since_email = 0
            
            current_level += 1
            
        else: # LOSS
            report_outcome("LOSS", current_level, duration)
            send_email(
                subject="Auto-Click: Level Lost",
                body=f"Level {current_level} lost. Bot going IDLE."
            )
            # Loop continues, next heartbeat will likely be WAIT because we sent LOSS (backend sets IDLE)
            # Backend logic: report(LOSS) -> status=IDLE.
            # Next check_backend_instruction() -> returns WAIT.
            # Loop waits until user sets CONTINUE via frontend.
            
            # Important: When user clicks Continue, backend status -> RUNNING.
            # Next heartbeat -> CONTINUE.
            # We Play Level (current_level) again. Retrying SAME level (since we didn't increment).
            # This matches desire: "Do NOT retry automatically... Resume only when explicitly told".
            
            # Simple sleep to prevent rapid polling right after loss
            time.sleep(2)

if __name__ == "__main__":
    main()
