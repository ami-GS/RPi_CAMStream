#To do: adapt tree p2p network
from tornado.websocket import WebSocketHandler
from tornado.web import asynchronous
from tornado.ioloop import IOLoop
import tornado
import tornado.httpserver
import cv2.cv as cv
from threading import Thread
import zlib
import time
from imageprocess import ImageProcess
import json
import sys

IMAGE_WIDTH = 480
IMAGE_HEIGHT = 360
INTERVAL = 10
FPS = 30#may be better to rpi camera module

status = False
clients = {} # [ip:WSHandler object]
class RpiWSHandler(WebSocketHandler):
    def initialize(self, camera):
        self.camera = camera
        self.camType = camera.camType
        self.duplicate = False

    def open(self):
        cli_ip = self.request.remote_ip
        if cli_ip in clients.keys():
            print "The IP address (",cli_ip, ") is already connected"
            self.write_message(json.dumps(["EXIT"]), binary = True)
            self.duplicate = True
            return

        clients[cli_ip] = self
        if len(clients) == 1:
            global status
            status = True

        #=======For tree p2p==========
        #self._p2p_proto(cli_ip)
        #==============================
        print "WebSocket to", cli_ip, "opened"

    #==============For tree p2p=================#redirect to ip & port
    def _p2p_proto(self,cli_ip):
        port = len(clients)+8080
        if len(clients) > 1:
            clients[cli_ip] = ["REDIRECT", cli_ip, str(port), str(port+1)]
        else:
            clients[cli_ip] = ["KEEP", cli_ip, str(port), str(port+1)]
        message = json.dumps(clients[cli_ip])
        self.write_message(message, binary = True)
    #===============================

    @staticmethod
    def rloop(camera):
        for foo in camera.camera.capture_continuous(camera.stream, "jpeg", use_video_port=True):
            camera.stream.seek(0)
            img = camera.stream.read()
            img = zlib.compress(img)
            for ip in clients.keys():
                clients[ip].write_message(img, binary=True)
            camera.stream.seek(0)
            camera.stream.truncate()

    @staticmethod
    def loop(camera):
        while True:
            img = camera._takeFrameUSB()
            img = zlib.compress(img)
            for ip in clients.keys():
                clients[ip].write_message(img, binary=True)
            cv.WaitKey(1000/FPS)

    def on_message(self):
        pass

    def on_close(self):
        if self.duplicate:
            return
        cli_ip = self.request.remote_ip
        clients.pop(cli_ip)

        if len(clients) == 0:
            global status
            status = False
        print "WebSocket to", cli_ip, "closed "



class TakePicture():
    def __init__(self, camType):
        self.camType = camType
        self._cameraInitialize(camType)
        print "Complete initialization"

    def _cameraInitialize(self, camType):
        if camType == "usb":
            try:
                self.capture = cv.CaptureFromCAM(0)
                cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
                cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)
                img = cv.QueryFrame(self.capture)
                self.ImageProcess = ImageProcess(img) #initialize ImageProcess
                self.t = Thread(target=RpiWSHandler.loop, args=(self,))
                self.t.setDaemon(True)
                self.t.start()
            except Exception as e:
                print "Error:", e
                sys.exit(-1)
        elif camType == "rpi":
            import picamera
            import io
            try:
                self.camera = picamera.PiCamera()
                self.camera.resolution = (IMAGE_WIDTH, IMAGE_HEIGHT)
                self.camera.framerate = FPS
                self.camera.led = False
                time.sleep(2)
                self.stream = io.BytesIO()
                self.t = Thread(target=RpiWSHandler.rloop, args=(self,))
                self.t.setDaemon(True)
                self.t.start()
            except picamera.PiCameraError as e:
                print e
                sys.exit(-1)

    def _takeFrameUSB(self):
        frame = cv.QueryFrame(self.capture)
        jpgString = cv.EncodeImage(".jpg", frame).tostring()
        return jpgString


def startWSServer(camera):
    app = tornado.web.Application([
        (r"/camera", RpiWSHandler, dict(camera=camera)),
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8080)
    IOLoop.instance().start()

def main(camType="usb"):
    camera = TakePicture(camType.lower())
    startWSServer(camera)

HELP = "Usage: piCamera.py [cameraType(rpi or usb)]"

if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 1:
        main()
    else:
        print "Too many arguments"
        print HELP
