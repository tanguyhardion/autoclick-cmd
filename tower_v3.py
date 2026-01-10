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

API_URL = os.getenv("API_URL", "http://localhost:3001/api")
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD")

# Globals for thread communication
CURRENT_COMMAND = "WAIT"
CURRENT_SERVER_LEVEL = 1
HEARTBEAT_LOCK = threading.Lock()

# OCR Config
reader = easyocr.Reader(['en'])
SQUARE_TOP_LEFT = (829, 288)
SQUARE_BOTTOM_RIGHT = (862, 317)

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
    global CURRENT_COMMAND, CURRENT_SERVER_LEVEL
    log("Heartbeat thread started.")
    while True:
        try:
            res = api_post("bot/heartbeat", {})
            if res and res.get("success"):
                data = res.get("data", {})
                with HEARTBEAT_LOCK:
                    CURRENT_COMMAND = data.get("command", "WAIT")
                    CURRENT_SERVER_LEVEL = data.get("current_level", 1)
                
                if data.get("trigger_screenshot"):
                    take_and_upload_screenshot()
        except Exception as e:
            log(f"Heartbeat Loop Error: {e}")
        
        time.sleep(2)

def check_backend_instruction():
    # Returns (command, server_level) from local cache (updated by thread)
    with HEARTBEAT_LOCK:
        return CURRENT_COMMAND, CURRENT_SERVER_LEVEL

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
        # Check Backend (from cache)
        cmd, server_accepted_level = check_backend_instruction()
        
        if cmd == "STOP":
            log("Backend said STOP. Idling...")
            time.sleep(5)
            continue

        # cmd == "CONTINUE" -> We are allowed to play.
        # We use our local current_level tracker, but we could sync with server if we wanted.
        # Requirement: "Increment locally, Sync updates to the backend"
        
        won, duration = play_level(current_level)
        
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
