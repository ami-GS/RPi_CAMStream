#To do: adapt multi client
from tornado.websocket import WebSocketHandler
from tornado.ioloop import PeriodicCallback, IOLoop
import tornado
import tornado.httpserver
import cv2.cv as cv
from threading import Thread
import zlib
import time
from imageprocess import ImageProcess
import sys

IMAGE_WIDTH = 240
IMAGE_HEIGHT = 180
INTERVAL = 30
FPS = 30

status = False
clients = {} # [ip:WSHandler object]
class RpiWSHandler(WebSocketHandler):
    def initialize(self, camera):
        self.camera = camera
        self.period = 1
        self.clientNum = 0
        self.duplicate = False

    def open(self):
        cli_ip = self.request.remote_ip
        if cli_ip in clients.keys():
            print "The IP address (",cli_ip, ") is already connected"
            self.write_message("EXIT", binary = True)
            self.duplicate = True
            return

        global status
        status = True
        clients[cli_ip] = self
        self.callback = PeriodicCallback(self._send_image, self.period)
        self.callback.start()
        print "WebSocket to", cli_ip, "opened"

    def _send_image(self):
        S_Multiclient(self.camera)

    def on_message(self):
        pass

    def on_close(self):
        if self.duplicate:
            return

        global status
        cli_ip = self.request.remote_ip
        clients.pop(cli_ip)
        self.callback.stop()
        self.camera.init_frame()
        if len(clients) == 0:
            status = False
        print "WebSocket to", cli_ip, "closed "

#one to many
def S_Multiclient(camera):
    frame = camera.get_frame()
    if frame:
        m = zlib.compress(frame)
        for ip in clients:
            clients[ip].write_message(m, binary = True)


class TakePicture():
    def __init__(self, camType="rpi"):
        self.init_frame()
        self.camType = camType
        if camType == "usb":
            #for USB cam
            try:
                self.capture = cv.CaptureFromCAM(0)
            except Exception as e:
                print "Error:",e
                sys.exit(-1)
            cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
            cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)
            img = cv.QueryFrame(self.capture)
            self.ImageProcess = ImageProcess(img) #initialize ImageProcess
            
        elif camType == "rpi":
            #RPi_EXP
            import picamera
            import io
            try:
                self.camera = picamera.PiCamera()
            except picamera.PiCameraError as e:
                print e
                sys.exit(-1)
            self.camera.resolution = (IMAGE_WIDTH, IMAGE_HEIGHT)
            self.camera.framerate = FPS
            self.camera.led = False
            #img = self.camera.capture() #initialize ImageProcess
            #self.ImageProcess = ImageProcess(img)
            time.sleep(2)
            self.stream = io.BytesIO()
        else:
            print "Input camera type 'rpi' or 'usb'"
            sys.exit(-1)
        
    def start(self):
        def run():
            if self.camType == "usb":
                self._run_USBCAM()
            elif self.camType == "rpi":
                self._run_RPiCAM()
       
        while True:
            time.sleep(0.3) #wait until websocket is opened
            run()
            
    def _run_USBCAM(self):
        while status:
            img = cv.QueryFrame(self.capture)
#            img = self.ImageProcess.motionDetect(img)
#            img = self.ImageProcess.faceDetect(img)
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
                
                    
    def init_frame(self):
        self.Frames = []
                
    def get_frame(self):
        if len(self.Frames):
            return self.Frames.pop(0)
        else:
            return 0

def wsFunc(camera):
    app = tornado.web.Application([
        (r"/camera", RpiWSHandler, dict(camera=camera)),
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8080)
    IOLoop.instance().start()
    

def main(camType="rpi"):
    camera = TakePicture(camType.lower())
    t = Thread(target=wsFunc, args=(camera,))
    t.setDaemon(True)
    t.start()
    camera.start()

HELP = "Usage: piCamera.py cameraType(rpi or usb)"

if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 1:
        main()
    else:
        print "Too many arguments"
        print HELP
