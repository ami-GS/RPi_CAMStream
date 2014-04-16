import time
import cv2
from datetime import datetime
import os, subprocess

WIDTH = 480
HEIGHT = 360
DIRNAME = "TL_%s" % datetime.now().strftime("%Y%m%d-%H%M%S")
ZFILL = 7
class Camera(object):
    def __init__(self):
        self.num = 1

    def takeImage(self):
        pass

    def timeStamp(self):
        stamp = str(self.num).zfill(ZFILL)
        self.num += 1
        return stamp

class usbCamera(Camera):
    def __init__(self):
        super(usbCamera, self).__init__()
        self.camera = cv2.VideoCapture(0)

    def takeImage(self):
        _, img = self.camera.read()
        if _:
            cv2.imwrite("./%s/%s.jpg" % (DIRNAME, self.timeStamp()), img)

class piCamera(Camera):
    def __init__(self):
        super(piCamera, self).__init__()
        import picamera
        self.camera = picamera.PiCamera()
        self.camera.resolution = (WIDTH, HEIGHT)
        time.sleep(2)

    def takeImage(self):
        self.camera.capture("./%s/%s.jpg" % (DIRNAME, self.timeStamp()))

def makeVideo(FPS):
    os.chdir(DIRNAME)
    subprocess.call("ffmpeg -r "+str(FPS)+" -i %07d.jpg -vcodec libx264 -sameq -vf 'scale=1620:1080,pad=1920:1080:150:0,setdar=16:9' "+"%s-%dfps.mp4"
                    % (DIRNAME, FPS))

def mainLoop(camera, FPS):
    while True:
        print camera.num
        camera.takeImage()
        if cv2.waitKey(int(1000/FPS)) == 27:
            break

def main():
    try:
        camera = piCamera()
    except:
        camera = usbCamera()
    while True:
        try:
            FPS = float(raw_input("Input FPS to start >> "))
            if not 0 < FPS <= 10:
                print "0 < FPS <= 10"
                continue
            break
        except:
            print "FPS should be number"
    if DIRNAME not in os.listdir("./"):
        os.mkdir("./%s" % DIRNAME)
    mainLoop(camera, FPS)

if __name__ == "__main__":
    main()
