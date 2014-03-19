#To do: adapt tree p2p network
from tornado.websocket import WebSocketHandler
from tornado.web import RequestHandler, asynchronous
from tornado.ioloop import PeriodicCallback, IOLoop
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
FPS = 7#may be better to rpi camera module

status = False
clients = {} # [ip:WSHandler object]
class RpiWSHandler(WebSocketHandler):
    def initialize(self, camera):
        self.camera = camera
        self.camType = camera.camType
        self.period = 0.1#may be better to rpi camera module
        self.duplicate = False

    def open(self):
        cli_ip = self.request.remote_ip
        if cli_ip in clients.keys():
            print "The IP address (",cli_ip, ") is already connected"
            self.write_message(json.dumps(["EXIT"]), binary = True)
            self.duplicate = True
            return

        global status
        status = True
        clients[cli_ip] = self
        #self.callback = PeriodicCallback(self._send_image, self.period)
        self.callback = PeriodicCallback(self.loop, self.period)
        
        #=======For tree p2p==========
        self._p2p_proto(cli_ip)
        #==============================
        self.callback.start()
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
        if clients[cli_ip][0] == "REDIRECT":
            self.on_close()
        #===============================
    
    def loop(self):
        def _send_image(image):
            m = zlib.compress(image)
            self.write_message(m, binary = True)
        image = self.camera.takeFrame()
        _send_image(image)

    def _send_image(self):
        self._S_Oneclient()

    def on_message(self):
        pass

    def on_close(self):
        if self.duplicate:
            return

        cli_ip = self.request.remote_ip
        clients.pop(cli_ip)
        self.callback.stop()
        self.camera.init_frame()
        if len(clients) == 0:
            global status
            status = False
        print "WebSocket to", cli_ip, "closed "

    def _S_Oneclient(self):
        frame = self.camera.get_frame()
        if frame:
            m = zlib.compress(frame)
            self.write_message(m, binary = True)


class TakePicture():
    def __init__(self, camType):
        self.init_frame()
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
                self.run = self._run_USBCAM
                self.takeFrame = self._takeFrameUSB
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
                #img = self.camera.capture() #initialize ImageProcess
                #self.ImageProcess = ImageProcess(img)
                time.sleep(2)
                self.stream = io.BytesIO()
                self.run = self._run_RPiCAM
                self.takeFrame = self._takeFrameRPi
            except picamera.PiCameraError as e:
                print e
                sys.exit(-1)


    def start(self):
        while True:
            time.sleep(0.3) #wait until websocket is opened
            self.run()

    def _run_USBCAM(self):
        while status:
            img = cv.QueryFrame(self.capture)
            #img = self.ImageProcess.motionDetect(img)
            jpgString = cv.EncodeImage(".jpg", img).tostring()
            self.Frames.append(jpgString)
            if cv.WaitKey(INTERVAL) == 27:
                break

    def _run_RPiCAM(self):
        if status:
            #RPi_CAM experiment
            for foo in self.camera.capture_continuous(self.stream, "jpeg",
                                                      use_video_port=True):
                self.stream.seek(0)
                frame = self.stream.getvalue()
                self.Frames.append(frame)
                self.stream.seek(0)
                self.stream.truncate()
                if not status:
                    self.init_frame()
                    break                

    def run(self):
        pass

    def _takeFrameUSB(self):
        frame = cv.QueryFrame(self.capture)
        jpgString = cv.EncodeImage(".jpg", frame).tostring()
        return jpgString

    def _takeFrameRPi(self, wsHandler):
        self.camera.capture(self.stream, "jpeg")
        self.stream.seek(0)
        frame = self.stream.getvalue()
        self.stream.seel(0)
        self.stream.truncate()
        return frame

    def takeFrame(self):
        pass

    def init_frame(self):
        self.Frames = []
                
    def get_frame(self):
        if len(self.Frames):
            return self.Frames.pop(0)
        else:
            return 0

class AssignIP(RequestHandler):
    @asynchronous
    def get(self):
        import socket
        if len(clients) == 0:
            assignHost = socket.gethostbyname(socket.gethostname())
            print "redirect host", self.request.remote_ip, "to", assignHost
            self.write(assignHost)
        else:
            self.write(clients[1])#?        

        self.finish()

def startWSServer(camera):
    app = tornado.web.Application([
        (r"/", AssignIP),
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
