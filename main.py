import pyautogui
import ctypes
import ctypes.wintypes as wintypes
import os
from colorbot import Colorbot
from settings import Settings

class Main:
    def __init__(self):
        self.settings = Settings()
        self.monitor = pyautogui.size()
        self.CENTER_X, self.CENTER_Y = self.monitor.width // 2, self.monitor.height // 2
        self.XFOV = self.settings.get_int('AIMBOT', 'xFov')
        self.YFOV = self.settings.get_int('AIMBOT', 'yFov')
        self.Colorbot = Colorbot(self.CENTER_X - self.XFOV // 2, self.CENTER_Y - self.YFOV // 2, self.XFOV, self.YFOV)

    def better_cmd(self, width, height):
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
            style &= ~0x00080000  # Remove WS_MAXIMIZEBOX
            style &= ~0x00C00000  # Remove WS_SIZEBOX
            ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)
        
        STD_OUTPUT_HANDLE_ID = -11
        windll = ctypes.windll.kernel32
        handle = windll.GetStdHandle(STD_OUTPUT_HANDLE_ID)
        
        if not handle:
            raise Exception("Failed to get standard output handle")

        # Set console buffer size
        windll.SetConsoleScreenBufferSize(handle, wintypes._COORD(width, height))

        # Set console window size
        rect = wintypes.SMALL_RECT(0, 0, width - 1, height - 1)
        windll.SetConsoleWindowInfo(handle, True, ctypes.byref(rect))

    def info(self):
        os.system('cls')
        print('github.com/kaanosu/ValorantArduinoColorbot\n')
        print('Enemy Outline Color: Purple')

    def run(self):
        self.better_cmd(120, 30)
        self.info()
        self.Colorbot.listen()

if __name__ == '__main__':
    Main().run()
