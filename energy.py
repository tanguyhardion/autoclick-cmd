from pywinauto.application import Application
import pyautogui
import time


def main():

    print("Starting...")
    time.sleep(0.5)

    app = Application().connect(title="Kings call")
    kings_call = app.window(title="Kings call")
    kings_call.set_focus()

    energy = 0
    max_energy = 40
    energy_pos = (1075, 345)
    use_energy_pos = (1000, 610)

    while energy < max_energy:
        pyautogui.doubleClick(energy_pos)
        time.sleep(0.1)
        pyautogui.click(use_energy_pos)

        # Check if mouse has moved
        current_mouse_pos = pyautogui.position()
        if current_mouse_pos != use_energy_pos:
            print("Mouse moved, stopping script.")
            break


if __name__ == "__main__":
    main()
