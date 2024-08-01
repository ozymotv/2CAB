import cv2
import numpy as np
import win32api
import math
import pyautogui
from capture import Capture
from mouse import Mouse
from settings import Settings

class Colorbot:
    settings = Settings()

    def __init__(self, x, y, xfov=None, yfov=None, game_fov=103):
        self.settings = Settings()
        self.mouse = Mouse()

        # Auto-detect screen resolution if xfov and yfov are not provided
        if xfov is None or yfov is None:
            screen_width, screen_height = pyautogui.size()
            xfov = screen_width
            yfov = screen_height

        self.grabber = Capture(x, y, xfov, yfov)
        self.LOWER_COLOR, self.UPPER_COLOR = self.get_colors()
        self.toggled = False
        self.configure()

        # Calculate Cx and Cy based on the game's FOV
        self.Cx, self.Cy = self.calculate_fov_constants(game_fov, xfov, yfov)

    def configure(self):
        self.AIMBOT_KEY = int(self.settings.get('AIMBOT', 'toggleKey'), 16)
        self.ALT_AIMBOT_KEY = int(self.settings.get('AIMBOT', 'altToggleKey'), 16)
        self.TARGET_OFFSET = float(self.settings.get('AIMBOT', 'targetOffset'))

    def get_colors(self):
        lower_color = np.array([140, 120, 180])
        upper_color = np.array([160, 200, 255])
        return lower_color, upper_color

    def calculate_fov_constants(self, fov_degrees, screen_width, screen_height):
        # Convert FOV from degrees to radians
        fov_radians = fov_degrees * math.pi / 180

        # Calculate Cx and Cy based on the screen dimensions and FOV
        Cx = screen_width / (2 * math.tan(fov_radians / 2))
        Cy = screen_height / (2 * math.tan(fov_radians / 2))
        return Cx, Cy

    def listen(self):
        while True:
            if win32api.GetAsyncKeyState(self.AIMBOT_KEY) < 0 or win32api.GetAsyncKeyState(self.ALT_AIMBOT_KEY) < 0:
                self.process()

    def fov(self, ax, ay, px, py):
        dx = (ax - px / 2) * 1.5
        dy = (ay - py / 2) * 1.5
        Rx = self.Cx / 2 / math.pi
        Ry = self.Cy / 2 / math.pi
        mx = math.atan2(dx, Rx) * Rx
        my = (math.atan2(dy, math.sqrt(dx * dx + Rx * Rx))) * Ry
        return mx, my

    def process(self):
        hsv = cv2.cvtColor(self.grabber.get_screen(), cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.LOWER_COLOR, self.UPPER_COLOR)
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(mask, kernel, iterations=5)
        thresh = cv2.threshold(dilated, 60, 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if contours:
            screen_center = (self.grabber.xfov // 2, self.grabber.yfov // 2)
            min_distance = float('inf')
            closest_contour = None

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                center = (x + w // 2, y + h // 2)
                distance = ((center[0] - screen_center[0]) ** 2 + (center[1] - screen_center[1]) ** 2) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    closest_contour = contour

            x, y, w, h = cv2.boundingRect(closest_contour)
            center = (x + w // 2, y + h // 2)
            cX = center[0]
            cY = y + int(h * self.TARGET_OFFSET)

            # Use fov to calculate mouse movement
            mx, my = self.fov(cX, cY, self.grabber.xfov, self.grabber.yfov)
            self.mouse.move(mx, my)

# Example usage with auto-detected screen resolution and game FOV of 103
colorbot = Colorbot(0, 0, game_fov=103)
colorbot.listen()
