from PIL import Image, ImageGrab
import easyocr
import pyautogui
from pywinauto.application import Application
import time
import numpy as np

# Initialize EasyOCR reader (runs once)
reader = easyocr.Reader(['en'])

square_top_left = (829, 288)
square_bottom_right = (862, 317)


def focus_kings_call():
    """Focus the Kings Call window."""
    try:
        app = Application().connect(title="Kings call")
        kings_call = app.window(title="Kings call")
        kings_call.set_focus()
        print("Kings Call window focused.")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error focusing Kings Call window: {e}")


def ocr_screenshot_region(top_left, bottom_right):
    """
    Take a screenshot of a specific region and perform OCR.
    
    Args:
        top_left: Tuple (x1, y1) for top-left corner
        bottom_right: Tuple (x2, y2) for bottom-right corner
    
    Returns:
        str: OCR text result
    """
    # Define bounding box (left, top, right, bottom)
    bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
    
    # Take screenshot of the region
    screenshot = ImageGrab.grab(bbox=bbox)
    
    # Convert PIL Image to numpy array
    screenshot_np = np.array(screenshot)
    
    # Perform OCR using EasyOCR
    results = reader.readtext(screenshot_np)
    
    # Extract text from results
    text = '\n'.join([detection[1] for detection in results])
    
    return text


def main():
    # Focus Kings Call window
    focus_kings_call()
    
    # Perform OCR on the specified region
    print(f"Capturing region from {square_top_left} to {square_bottom_right}...")
    ocr_text = ocr_screenshot_region(square_top_left, square_bottom_right)
    
    print("\n--- OCR Result ---")
    print(ocr_text)
    print("--- End Result ---\n")


if __name__ == "__main__":
    main()