import kmNet
import win32api
import numpy as np
import cv2
import time
import math
import dxcam
import logging
import threading
import json
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for color detection bounds
LOWER_BOUND = np.array([190, 40, 190])
UPPER_BOUND = np.array([310, 160, 310])
LEFT_MOUSE_BUTTON = 0x01

class CameraApp:
    def __init__(self, config):
        self.camera = dxcam.create()
        self.thread_running = False
        self.thread_lock = threading.Lock()

        # Initialize with config values
        self.ip = config['kmNet']['ip']
        self.port = config['kmNet']['port']
        self.uid = config['kmNet']['uid']
        self.speed = config['movement']['defaultSpeed']
        self.fov = config['movement']['defaultFOV']
        self.trigger_button = int(config['triggerKey']['keyCode'], 16)

        self.SCREEN_WIDTH = win32api.GetSystemMetrics(0)
        self.SCREEN_HEIGHT = win32api.GetSystemMetrics(1)
        self.middle_x = self.SCREEN_WIDTH // 2
        self.middle_y = self.SCREEN_HEIGHT // 2
        self.update_grab_zone()

    def left_click(self):
        """Simulate a left mouse click."""
        kmNet.enc_left(1)
        time.sleep(np.random.uniform(0.08, 0.17))
        kmNet.enc_left(0)

    def toggle_thread(self):
        """Toggle the state of the capture thread."""
        with self.thread_lock:
            self.thread_running = not self.thread_running
        if self.thread_running:
            logging.info("Thread started.")
            threading.Thread(target=self.threaded_capture).start()
        else:
            logging.info("Thread stopped.")

    def update_speed(self, value):
        """Update the speed variable."""
        self.speed = float(value)

    def update_fov(self, value):
        """Update the FOV variable."""
        self.fov = int(round(float(value)))
        self.update_grab_zone()

    def update_grab_zone(self):
        """Update the GRAB_ZONE based on the current FOV."""
        self.zone = self.fov * 10
        self.GRAB_ZONE = (
            int(self.SCREEN_WIDTH / 2 - self.zone),
            int(self.SCREEN_HEIGHT / 2 - self.zone),
            int(self.SCREEN_WIDTH / 2 + self.zone),
            int(self.SCREEN_HEIGHT / 2 + self.zone),
        )

    def smooth_move(self, x, y, speed):
        """Smoothly move the cursor to a target position."""
        start_x, start_y = win32api.GetCursorPos()
        distance = math.sqrt(x**2 + y**2)
        num_steps = max(int(distance / (speed * 0.2)), 1)
        step_x = x / num_steps
        step_y = y / num_steps

        for i in range(num_steps):
            if win32api.GetKeyState(self.trigger_button) < 0:
                new_x = int(start_x + (i + 1) * step_x)
                new_y = int(start_y + (i + 1) * step_y)
                current_x, current_y = win32api.GetCursorPos()
                move_x = new_x - current_x
                move_y = new_y - current_y
                if abs(new_x - start_x - x) <= 3 and abs(new_y - start_y - y) <= 3:
                    break
                kmNet.enc_move(move_x, move_y)
                time.sleep(0.001)

                # Check if cursor position has been manually changed
                if win32api.GetCursorPos() != (new_x, new_y):
                    self.smooth_move(new_x - current_x, new_y - current_y, speed)
                    break

    def check_rgb_values(self, frame):
        """Check if specific RGB values are present in the frame."""
        mask = cv2.inRange(frame, LOWER_BOUND, UPPER_BOUND)
        coordinates = cv2.findNonZero(mask)
        if coordinates is not None and coordinates.size > 0:
            xpos, ypos = coordinates[0][0]
            xpos += self.GRAB_ZONE[0]
            ypos += self.GRAB_ZONE[1] + 3
            return True, xpos, ypos
        return False, None, None

    def main_process(self, frame):
        """Main function to process the frame."""
        color_present, x, y = self.check_rgb_values(frame)
        if color_present:
            self.smooth_move(x - self.middle_x, y - self.middle_y, self.speed)

    def threaded_capture(self):
        """Capture frames in a separate thread."""
        while self.thread_running:
            if win32api.GetKeyState(self.trigger_button) < 0:
                try:
                    screenshot = self.camera.grab(region=self.GRAB_ZONE)
                    if screenshot is not None:
                        self.main_process(screenshot)
                except Exception as e:
                    logging.error(f'Error: {e}')
        self.camera.release()

    def save_trigger(self, key_code):
        """Save the trigger key code."""
        self.trigger_button = int(key_code, 16)

    def run(self):
        """Run the application."""
        logging.info("Starting application.")
        self.toggle_thread()  # Start the thread initially

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Camera App with Threaded Capture")
    parser.add_argument('--config', '-c', default='config.json', help="Path to config file (default: config.json)")
    args = parser.parse_args()

    # Load configuration from file
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error(f"Config file '{args.config}' not found.")
        exit(1)
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in config file '{args.config}'.")
        exit(1)

    # Initialize the application with loaded configuration
    app = CameraApp(config)
    app.run()
