import sys
import time
import kmNet
from settings import Settings

class Mouse:
    settings = Settings()
    
    def __init__(self):
        kmNet.init("192.168.2.188", "16896", "46405C53")
        kmNet.monitor(10000)
 
    def move(self, x, y):
        kmNet.enc_move(int(x), int(y))
        #self.serial_port.write(f'M{x},{y}\n'.encode())