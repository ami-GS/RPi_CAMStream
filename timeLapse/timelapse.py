import cv2
from datetime import datetime
import os
import subprocess
import cameraset

WIDTH = 860 # 2592 max
HEIGHT = 720 # 1944 max
DIRNAME = "TL_%s" % datetime.now().strftime("%Y%m%d-%H%M%S")
ZFILL = 7

def makeVideo(FPS):
    os.chdir(DIRNAME)
    print(["ffmpeg", "-r", "%d" % FPS, "-i", "%%0%dd.jpg" % ZFILL,
                     "-vcodec", "libx264", "-qscale", "0", "-vf",
                     "'scale=1620:1080,pad=1920:1080:150:0,setdar=16:9'",
                     "%s-%dfps.mp4" % (DIRNAME, FPS)])
    subprocess.call(["ffmpeg", "-r", "%d" % FPS, "-i", "%%0%dd.jpg" % ZFILL,
                     "-vcodec", "libx264", "-q", "0", "-vf",
                     "scale=1620:1080,pad=1920:1080:150:0,setdar=16:9",
                     "%s-%dfps.mp4" % (DIRNAME, FPS)])
def mainLoop(camera, FPS):
    while True:
        print camera.num
        camera.takeImage()
        if cv2.waitKey(int(1000/FPS)) == 27 or camera.num == 100:
            camera.terminalte()
            makeVideo(FPS)
            break

def main():
    try:
        camera = cameraset.piCamera(DIRNAME, ZFILL, WIDTH, HEIGHT)
    except:
        camera = cameraset.usbCamera(DIRNAME, ZFILL, WIDTH, HEIGHT)
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
