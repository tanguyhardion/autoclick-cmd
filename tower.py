from pywinauto.application import Application
import pyautogui
import time
from PIL import ImageGrab


def get_pixel_color(x, y):
    # Capture the screen and get the color at (x, y)
    img = ImageGrab.grab()
    return img.getpixel((x, y))


def main():

    print("Starting...")
    time.sleep(0.5)

    app = Application().connect(title="Kings call")
    kings_call = app.window(title="Kings call")
    kings_call.set_focus()

    start_continue_pos = (1434, 732)
    won_lost_pos = (1700, 187)
    auto_pos = (1500, 717)
    lost_rgb = (58, 63, 68)

    loop_count = 1
    while True:
        print(f"\n--- Loop {loop_count} ---")

        # Start/Continue
        print(f"Clicking at {start_continue_pos} (start_continue_pos)...")
        pyautogui.click(start_continue_pos)
        time.sleep(2)

        # Auto
        print(f"Clicking at {auto_pos} (auto_pos)...")
        pyautogui.click(auto_pos)
        time.sleep(1)

        initial_color = get_pixel_color(*won_lost_pos)
        print(f"Recorded initial color at {won_lost_pos}: {initial_color}")

        print(f"Waiting for color at {won_lost_pos} to change...")
        wait_loops = 0

        # While level isn't finished
        while True:
            current_color = get_pixel_color(*won_lost_pos)
            if current_color != initial_color:
                print(f"\nColor at {won_lost_pos} changed to {current_color}")
                break
            print("...still waiting for color change...", end="\r", flush=True)
            wait_loops += 1
            time.sleep(0.2)

        # After level finished, check if color at won_lost_pos is lost_rgb
        color_after = get_pixel_color(*won_lost_pos)
        print(f"Checking if color at {won_lost_pos} is (63, 67, 71): {color_after}")
        if color_after == lost_rgb:
            print(f"Color at {won_lost_pos} is (63, 67, 71). Level lost, ending script.")
            break

        # Level won
        print("\nLevel won!")
        time.sleep(1)

        # Click at the dead center of the screen to pick a reward
        screen_width, screen_height = pyautogui.size()
        center_x, center_y = screen_width // 2, screen_height // 2
        print(f"Clicking at screen center ({center_x}, {center_y}) to get reward...")
        pyautogui.click(center_x, center_y)

        print("Waiting 7 seconds for summary screen to appear...")
        time.sleep(7)

        print("Clicking at (1250, 450) to dismiss summary screen...")
        pyautogui.click(1250, 450)
        time.sleep(1)

        print("Repeating loop.")
        loop_count += 1
        # Continue looping


if __name__ == "__main__":
    main()
