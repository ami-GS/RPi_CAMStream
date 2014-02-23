#To do: I have to know the way to call RpiWSHandler constractor (__init__)

from tornado.websocket import WebSocketHandler
from tornado.ioloop import PeriodicCallback, IOLoop
import tornado
import tornado.httpserver
from threading import Thread
import cv2.cv as cv
import zlib
import time
from imageprocess import ImageProcess


IMAGE_WIDTH = 840
IMAGE_HEIGHT = 630

Frames = []
status = False
class RpiWSHandler(WebSocketHandler):
#    def __init__(self, camera):
#        self.camera = camera
#        super(SendWebsocket, self).__init__(*args, **keys)

    def open(self):
        global status
        self.period = 10
        self.callback = PeriodicCallback(self._send_image, self.period)
        status = True
        self.callback.start()
        print "WebSocket opened"

    def _send_image(self):
        if len(Frames):
            frame = Frames.pop(0)
            m = zlib.compress(frame)
            self.write_message(m, binary = True)

    def on_message(self):
        pass

    def on_close(self):
        global status
        self.callback.stop()
        status = False
        print "WebSocket closed"

class TakePicture():
    def __init__(self):
        self.capture = cv.CaptureFromCAM(0)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)
        img = cv.QueryFrame(self.capture)
        self.ImageProcess = ImageProcess(img) #initialize ImageProcess

    def run(self):
        while True:
            time.sleep(0.3) #wait until websocket is opened
            while status:
                img = cv.QueryFrame(self.capture)

                img = self.ImageProcess.motionDetect(img)

                jpgString = cv.EncodeImage(".jpg", img).tostring()
                Frames.append(jpgString)
                if cv.WaitKey(30) == 27:
                    break
                    

def wsFunc():
    app = tornado.web.Application([
        (r"/camera", RpiWSHandler),
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8080)
    IOLoop.instance().start()
    

def main():
    camera = TakePicture()
    t = Thread(target=wsFunc)
    t.setDaemon(True)
    t.start()
    camera.run()

if __name__ == "__main__":
    main()
