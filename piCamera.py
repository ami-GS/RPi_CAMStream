from tornado.websocket import WebSocketHandler
from tornado.ioloop import PeriodicCallback, IOLoop
import tornado
import tornado.httpserver
from threading import Thread
import cv2.cv as cv
import cv2
import zlib
import time
from imageprocess import ImageProcess


IMAGE_WIDTH = 200
IMAGE_HEIGHT = 45
INTERVAL = 80

status = False
class RpiWSHandler(WebSocketHandler):
    def initialize(self, camera):
        self.camera = camera
        self.period = 10

    def open(self):
        global status
        self.callback = PeriodicCallback(self._send_image, self.period)
        status = True
        self.callback.start()
        print "WebSocket opened"

    def _send_image(self):
        frame = self.camera.get_frame()
        if frame:
            m = zlib.compress(frame)
            self.write_message(m, binary = True)

    def on_message(self):
        pass

    def on_close(self):
        global status
        self.callback.stop()
        self.camera.init_frame()
        status = False
        print "WebSocket closed"

class TakePicture():
    def __init__(self):
        self.capture = cv.CaptureFromCAM(-1)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)
        img = cv.QueryFrame(self.capture)
        self.ImageProcess = ImageProcess(img) #initialize ImageProcess
        self.init_frame()

    def start(self):
        self._run()

    def _run(self):
        while True:
            time.sleep(0.3) #wait until websocket is opened
            while status:
                img = cv.QueryFrame(self.capture)

#                img = self.ImageProcess.motionDetect(img)

#                jpgString = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY),90]).tostring()
                jpgString = cv.EncodeImage(".jpg", img).tostring()
                self.Frames.append(jpgString)
                if cv.WaitKey(INTERVAL) == 27:
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
    

def main():
    camera = TakePicture()
    t = Thread(target=wsFunc, args=(camera,))
    t.setDaemon(True)
    t.start()
    camera.start()

if __name__ == "__main__":
    main()
