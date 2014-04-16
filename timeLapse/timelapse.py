import time
import cv2
from datetime import datetime
import os

WIDTH = 480
HEIGHT = 360
DIRNAME = "TL"
class Camera(object):
    def __init__(self):
        self.num = 1

    def takeImage(self):
        pass

    def timeStamp(self):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")+str(self.num)
        self.num += 1
        return stamp

class usbCamera(Camera):
    def __init__(self):
        super(usbCamera, self).__init__()
        self.camera = cv2.VideoCapture(0)

    def takeImage(self):
        _, img = self.camera.read()
        if _:
            cv2.imwrite("./%s/TL_%s.jpg" % (DIRNAME, self.timeStamp()), img)

class piCamera(Camera):
    def __init__(self):
        super(piCamera, self).__init__()
        import picamera
        self.camera = picamera.PiCamera()
        self.camera.resolution = (WIDTH, HEIGHT)
        time.sleep(2)

    def takeImage(self):
        self.camera.capture("./%s/TL_%s.jpg" % (DIRNAME, self.timeStamp()))


def mainLoop(camera, FPS):
    while True:
        camera.takeImage()
        time.sleep(1/FPS)

def main():
    try:
        camera = piCamera()
    except:
        camera = usbCamera()
    while True:
        try:
            FPS = float(raw_input("Input FPS to start >> "))
            break
        except:
            print "0 < FPS <= 10"
    if DIRNAME not in os.listdir("./"):
        os.mkdir("./%s" % DIRNAME)
    mainLoop(camera, FPS)

if __name__ == "__main__":
    main()
