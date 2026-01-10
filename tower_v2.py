from pywinauto.application import Application
import pyautogui
import time
from PIL import ImageGrab
from utils.email_sender import send_email



def get_pixel_color(x, y):
    # Capture the screen and get the color at (x, y)
    img = ImageGrab.grab()
    return img.getpixel((x, y))


def play_level(start_continue_pos, won_lost_pos, auto_pos, lost_rgb, level_number=None):
    """
    Play a single level and return True if won, False if lost.
    """
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
    print(f"Checking if color at {won_lost_pos} is {lost_rgb}: {color_after}")
    if color_after == lost_rgb:
        print(f"Level lost!")
        return False

    # Level won
    print("\nLevel won!")
    return True


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
    max_retries = 3
    levels_won = 0
    i = 0
    number_of_levels_to_win = 60

    # while True:
    while i < number_of_levels_to_win:
        i += 1
        print(f"\n--- Loop {loop_count} ---")

        retry_count = 0
        level_won = False

        # Try to play the level up to 3 times if lost
        while retry_count < max_retries:
            if retry_count > 0:
                print(f"\nRetry attempt {retry_count}/{max_retries}...")

            level_won = play_level(start_continue_pos, won_lost_pos, auto_pos, lost_rgb, level_number=loop_count)

            if level_won:
                break
            else:
                # Send email when losing and retrying
                send_email(
                    subject=f"Auto-Click: Level {loop_count} Lost - Retrying",
                    body=f"Level {loop_count} was lost.\n\nAttempt {retry_count + 1}/{max_retries}\nLevels won so far: {levels_won}"
                )
                retry_count += 1

        # If level was lost after all retries, stop and send email
        if not level_won:
            print(f"\nLevel still lost after {max_retries} attempts. Ending script.")
            send_email(
                subject="Auto-Click: Level Lost",
                body=f"Your game has ended.\n\nLevels won before loss: {levels_won}\nLevel number: {loop_count}"
            )
            break

        # Level won - increment counter
        levels_won += 1
        print(f"Total levels won: {levels_won}")

        # Send email every 5 levels won
        if levels_won % 5 == 0:
            send_email(
                subject=f"Auto-Click: {levels_won} Levels Won!",
                body=f"Congratulations! You've won {levels_won} levels.\n\nCurrent level: {loop_count}"
            )

        # Level won - handle reward
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
