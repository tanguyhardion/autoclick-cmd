from pywinauto.application import Application
import pyautogui
import time
from PIL import ImageGrab

level = (1303, 453)
start = (1233, 673)
auto_pos = (1500, 717)
color_pos = (1695, 188)


def get_pixel_color(x, y):
    # Capture the screen and get the color at (x, y)
    img = ImageGrab.grab()
    return img.getpixel((x, y))


def main():
    print("Starting...")

    app = Application().connect(title="Kings call")
    kings_call = app.window(title="Kings call")
    kings_call.set_focus()

    loop_count = 1
    while loop_count < 40:
        print(f"\n--- Loop {loop_count} ---")

        time.sleep(2)

        # Click at level pos
        print(f"Clicking at {level} (level pos)...")
        pyautogui.click(level)
        time.sleep(1)

        # Click at start pos
        print(f"Clicking at {start} (start pos)...")
        pyautogui.click(start)
        time.sleep(1)

        # Click at auto pos
        print(f"Clicking at {auto_pos} (auto pos)...")
        pyautogui.click(auto_pos)

        # Record initial color at color_pos
        initial_color = get_pixel_color(*color_pos)
        print(f"Recorded initial color at {color_pos}: {initial_color}")

        print(f"Waiting for color at {color_pos} to change...")
        wait_loops = 0

        # Poll color_pos until it changes
        while True:
            current_color = get_pixel_color(*color_pos)
            if current_color != initial_color:
                print(f"\nColor at {color_pos} changed to {current_color}")
                break
            print("...still waiting for color change...", end="\r", flush=True)
            wait_loops += 1
            time.sleep(0.1)

        # Wait 1s then click at middle of screen
        time.sleep(1)
        screen_width, screen_height = pyautogui.size()
        center_x, center_y = screen_width // 2, screen_height // 2
        print(f"Clicking at screen center ({center_x}, {center_y})...")
        pyautogui.click(center_x, center_y)
        pyautogui.click(center_x, center_y)
        pyautogui.click(center_x, center_y)
        pyautogui.click(center_x, center_y)
        pyautogui.click(center_x, center_y)

        # Loop back
        loop_count += 1


if __name__ == "__main__":
    main()
