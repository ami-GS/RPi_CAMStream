import cv2.cv as cv
from tornado.websocket import WebSocketHandler
import tornado.web
import tornado.httpserver
from tornado.ioloop import IOLoop, PeriodicCallback
import time


WIDTH = 480
HEIGHT = 360
FPS = 30
class HttpHandler(tornado.web.RequestHandler):
    def initialize(self):
            pass

    def get(self):
        with open("./index.html") as f:
            for line in f.readlines():
                self.write(line)
            self.finish()

sessions = {}
class WSHandler(WebSocketHandler):
    def initialize(self, camera):
        self.camera = camera
        self.state = True

    def open(self):
        print(self.request.remote_ip, ": connection opened")

        global sessions
        sessions[self.request.remote_ip] = self
        if isinstance(self.camera, Camera):
            self.callback = PeriodicCallback(self.loop, 1000/FPS)
        else:
            #TODO implement for non-blocking structure
            for foo in self.camera.capture_continuous(self.camera.stream, "jpeg", use_video_port=True):
                self.camera.stream.seek(0)
                self.write_message(self.camera.stream.read(), binary=True)
                self.camera.stream.seek(0)
                self.camera.stream.truncate()
                if not self.state:
                    self.on_close()
                    break
        self.callback.start()

    def loop(self):
        img = self.camera.takeImage()
        for ip in sessions.keys():
            sessions[ip].write_message(img, binary=True)

    def on_message(self, message):
        try:
            if str(message) == "close":
                self.on_close()
        except Exception as e:
            print e

    def on_close(self):
        session = sessions.pop(self.request.remote_ip)
        session.callback.stop()
        print(self.request.remote_ip, ": connection closed")

class Camera():
    def __init__(self):
        self.capture = cv.CaptureFromCAM(0)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, WIDTH)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, HEIGHT)
    
    def takeImage(self):
        img = cv.QueryFrame(self.capture)
        img = cv.EncodeImage(".jpg", img).tostring()
        return img

def piCamera():
    import picamera, io
    camera = picamera.PiCamera()
    camera.resolution = (WIDTH, HEIGHT)
    camera.framerate = FPS
    camera.led = False
    camera.stream = io.BytesIO()
    time.sleep(2)
    return camera

def main():
    try:
        camera = piCamera()
    except ImportError:
        camera = Camera()
    print "complete initialization"
    app = tornado.web.Application([
        (r"/", HttpHandler),
        (r"/camera", WSHandler, dict(camera=camera)),
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8080)
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
