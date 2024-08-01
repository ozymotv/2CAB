import numpy as np
from mss import mss
import pyautogui

class Capture:
    def __init__(self, x, y, xfov, yfov, region=None):
        self.mss = mss()
        self.xfov = xfov
        self.yfov = yfov
        
        if region:
            # Region is a tuple (x, y, width, height)
            self.monitor = {
                'top': region[1],
                'left': region[0],
                'width': region[2],
                'height': region[3]
            }
        else:
            # Use full screen dimensions
            self.monitor = {
                'top': y,
                'left': x,
                'width': xfov,
                'height': yfov
            }

    def get_screen(self):
        # Capture the screen or the specified region
        screenshot = self.mss.grab(self.monitor)
        return np.array(screenshot)

    def update_region(self, region):
        # Update the region dynamically
        self.monitor = {
            'top': region[1],
            'left': region[0],
            'width': region[2],
            'height': region[3]
        }

def get_screen_resolution():
    return pyautogui.size()
