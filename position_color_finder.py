import pyautogui
import time
from pynput.mouse import Listener

print("Move your mouse to the target position. Press Ctrl+C to stop.\n")

def on_click(x, y, button, pressed):
    if pressed:
        color = pyautogui.pixel(x, y)
        print(f"Mouse clicked at: ({x}, {y}) | Color: {color}")

try:
    previousx, previousy = pyautogui.position()
    previous_color = pyautogui.pixel(previousx, previousy)

    # Start mouse listener
    listener = Listener(on_click=on_click)
    listener.start()

    while True:
        x, y = pyautogui.position()
        color = pyautogui.pixel(x, y)
        print(f"Mouse position: ({x}, {y}) | Color: {color}    ", end='\r')
        if (x, y) != (previousx, previousy) or color != previous_color:
            previousx, previousy = x, y
            previous_color = color
        time.sleep(0.05)
except KeyboardInterrupt:
    print(f"\nStopped.")
    listener.stop()
