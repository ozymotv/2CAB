import cv2
import bettercam
from screeninfo import get_monitors
import threading
import queue
from settings import Settings
import logging

logging.basicConfig(level=logging.INFO)

class Capture(threading.Thread):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Capture, cls).__new__(cls, *args, **kwargs)
        else:
            logging.warning("You already created a BetterCam Instance for Device 0--Output 0!")
            logging.warning("Returning the existed instance...")
            logging.warning("To change capture parameters you can manually delete the old object using `del obj`.")
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        super().__init__()
        self.daemon = True
        self.name = "Capture"
        self.settings = Settings()
        
        self.print_startup_messages()
        
        self._custom_region = []
        self._offset_x = None
        self._offset_y = None
        
        self.screen_x_center = int(self.settings.get_int('Capture', 'detection_window_width') / 2)
        self.screen_y_center = int(self.settings.get_int('Capture', 'detection_window_height') / 2)

        self.prev_detection_window_width = self.settings.get_int('Capture', 'detection_window_width')
        self.prev_detection_window_height = self.settings.get_int('Capture', 'detection_window_height')
        self.prev_bettercam_capture_fps = self.settings.get_int('Capture', 'bettercam_capture_fps')
        
        self.frame_queue = queue.Queue(maxsize=1)
        self.running = True
        
        if self.settings.get_boolean('Capture', 'Bettercam_capture'):
            try:
                self.setup_bettercam()
            except Exception as e:
                logging.error(f"Failed to setup Bettercam: {e}")
        elif self.settings.get_boolean('Capture', 'Obs_capture'):
            self.setup_obs()
        
        self._initialized = True

    def setup_bettercam(self):
        self.bc = bettercam.create(device_idx=self.settings.get_int('Capture', 'bettercam_monitor_id'),
                                   output_idx=self.settings.get_int('Capture', 'bettercam_gpu_id'),
                                   output_color="BGR",
                                   max_buffer_len=16,
                                   region=self.Calculate_screen_offset())
        if not self.bc.is_capturing:
            self.bc.start(region=self.Calculate_screen_offset(custom_region=[] if len(self._custom_region) <= 0 else self._custom_region,
                                                              x_offset=None if self._offset_x is None else self._offset_x,
                                                              y_offset=None if self._offset_y is None else self._offset_y),
                          target_fps=self.settings.get_int('Capture', 'bettercam_capture_fps'))

    def setup_obs(self):
        if self.settings.get('Capture', 'Obs_camera_id') == 'auto':
            camera_id = self.find_obs_virtual_camera()
            if camera_id == -1:
                logging.error('OBS Virtual Camera not found')
                exit(0)
        elif self.settings.get('Capture', 'Obs_camera_id').isdigit():
            camera_id = int(self.settings.get('Capture', 'Obs_camera_id'))
        self.obs_camera = cv2.VideoCapture(camera_id)
        self.obs_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.get_int('Capture', 'detection_window_width'))
        self.obs_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.get_int('Capture', 'detection_window_height'))
        self.obs_camera.set(cv2.CAP_PROP_FPS, self.settings.get_int('Capture', 'Obs_capture_fps'))
        
    def run(self):
        while self.running:
            frame = self.capture_frame()
            if frame is not None:
                if self.frame_queue.full():
                    self.frame_queue.get()
                self.frame_queue.put(frame)
            
    def capture_frame(self):
        if self.settings.get_boolean('Capture', 'Bettercam_capture'):
            return self.bc.get_latest_frame()
        elif self.settings.get_boolean('Capture', 'Obs_capture'):
            ret_val, img = self.obs_camera.read()
            if ret_val:
                return img
            else:
                logging.error('Failed to capture frame from OBS Virtual Camera')
                return None
            
    def get_new_frame(self):
        try:
            return self.frame_queue.get(timeout=1)
        except queue.Empty:
            return None
    
    def restart(self):
        if self.settings.get_boolean('Capture', 'Bettercam_capture') and (
                self.prev_detection_window_height != self.settings.get_int('Capture', 'detection_window_height') or 
                self.prev_detection_window_width != self.settings.get_int('Capture', 'detection_window_width') or 
                self.prev_bettercam_capture_fps != self.settings.get_int('Capture', 'bettercam_capture_fps')):
            self.bc.stop()
            del self.bc
            self.setup_bettercam()

            self.screen_x_center = self.settings.get_int('Capture', 'detection_window_width') / 2
            self.screen_y_center = self.settings.get_int('Capture', 'detection_window_height') / 2

            self.prev_detection_window_width = self.settings.get_int('Capture', 'detection_window_width')
            self.prev_detection_window_height = self.settings.get_int('Capture', 'detection_window_height')

            logging.info('Capture reloaded')
            
    def Calculate_screen_offset(self, custom_region=[], x_offset=None, y_offset=None):
        if x_offset is None:
            x_offset = 0
        if y_offset is None:
            y_offset = 0
        
        if len(custom_region) <= 0:
            left, top = self.get_primary_display_resolution()
        else:
            left, top = custom_region
        
        left = left / 2 - self.settings.get_int('Capture', 'detection_window_width') / 2 + x_offset
        top = top / 2 - self.settings.get_int('Capture', 'detection_window_height') / 2 - y_offset
        width = left + self.settings.get_int('Capture', 'detection_window_width')
        height = top + self.settings.get_int('Capture', 'detection_window_height')
        
        return (int(left), int(top), int(width), int(height))
    
    def get_primary_display_resolution(self):
        monitors = get_monitors()
        for monitor in monitors:
            if monitor.is_primary:
                return monitor.width, monitor.height
            
    def find_obs_virtual_camera(self):
        max_tested = 20
        obs_camera_name = 'DSHOW'
        
        for i in range(max_tested):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if not cap.isOpened():
                continue
            backend_name = cap.getBackendName()
            if backend_name == obs_camera_name:
                logging.info(f'OBS Virtual Camera found at index {i}')
                cap.release()
                return i
            cap.release()
        return -1
    
    def print_startup_messages(self):
        version = "unknown"
        try:
            with open('./version', 'r') as f:
                lines = f.read().split('\n')
                version = lines[0].split('=')[1]
        except FileNotFoundError:
            logging.warning('Version file not found')

        logging.info(f'(Version {version})\n\n'
              f'Hotkeys:\n'
              f'[{self.settings.get("Hotkeys", "hotkey_targeting")}] - Aiming at the target\n'
              f'[{self.settings.get("Hotkeys", "hotkey_exit")}] - EXIT\n'
              f'[{self.settings.get("Hotkeys", "hotkey_pause")}] - PAUSE AIM\n'
              f'[{self.settings.get("Hotkeys", "hotkey_reload_config")}] - Reload config\n')
            
    def Quit(self):
        self.running = False
        if self.settings.get_boolean('Capture', 'Bettercam_capture') and self.bc.is_capturing:
            self.bc.stop()
        if self.settings.get_boolean('Capture', 'Obs_capture'):
            self.obs_camera.release()
        self.join()

capture = Capture()
capture.start()
