import cv2
import numpy as np
import win32api
import logging
from capture import Capture
from mouse import Mouse
from settings import Settings

class Colorbot:
    def __init__(self, x, y, xfov, yfov):
        self.settings = Settings()
        self.mouse = Mouse()
        self.grabber = Capture()
        self.x = x
        self.y = y
        self.xfov = xfov
        self.yfov = yfov
        self.LOWER_COLOR, self.UPPER_COLOR = self.get_colors()
        self.toggled = False
        self.configure()

    def configure(self):
        self.sensitivity = self.settings.get_float('AIMBOT', 'aimSpeed')
        self.AIMBOT_KEY = self.settings.get('Hotkeys', 'hotkey_targeting')
        self.EXIT_KEY = self.settings.get('Hotkeys', 'hotkey_exit')
        self.PAUSE_KEY = self.settings.get('Hotkeys', 'hotkey_pause')
        self.RELOAD_KEY = self.settings.get('Hotkeys', 'hotkey_reload_config')
        self.TARGET_OFFSET = self.settings.get_float('AIMBOT', 'targetOffset')
        self.FOV = self.settings.get_float('AIMBOT', 'fov')

    def get_colors(self):
        lower_color = np.array([140, 120, 180])
        upper_color = np.array([160, 200, 255])
        return lower_color, upper_color

    def listen(self):
        while True:
            if win32api.GetAsyncKeyState(ord(self.AIMBOT_KEY)) < 0:
                self.process()
            if win32api.GetAsyncKeyState(ord(self.EXIT_KEY)) < 0:
                break
            if win32api.GetAsyncKeyState(ord(self.PAUSE_KEY)) < 0:
                self.toggled = not self.toggled
            if win32api.GetAsyncKeyState(ord(self.RELOAD_KEY)) < 0:
                self.configure()

    def process(self):
        if self.toggled:
            return

        try:
            hsv = cv2.cvtColor(self.grabber.get_new_frame(), cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.LOWER_COLOR, self.UPPER_COLOR)
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(mask, kernel, iterations=5)
            thresh = cv2.threshold(dilated, 60, 255, cv2.THRESH_BINARY)[1]
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            if contours:
                screen_center = (self.xfov // 2, self.yfov // 2)
                closest_contour = min(contours, key=lambda cnt: cv2.pointPolygonTest(cnt, screen_center, True))

                if closest_contour is not None:
                    x, y, w, h = cv2.boundingRect(closest_contour)
                    center = (x + w // 2, y + h // 2)
                    cX = center[0]
                    cY = y + int(h * self.TARGET_OFFSET)
                    x_diff = cX - self.xfov // 2
                    y_diff = cY - self.yfov // 2

                    # Adjust sensitivity calculation
                    sensitivity_x = self.sensitivity * (self.FOV / 90)
                    sensitivity_y = self.sensitivity * (self.FOV / 90)

                    # Move the mouse with adjusted sensitivity
                    self.mouse.move(sensitivity_x * x_diff, sensitivity_y * y_diff)
        except Exception as e:
            logging.error(f"Error in process: {e}")
