import cv2.cv as cv
from tornado.websocket import WebSocketHandler
import tornado.web
import tornado.httpserver
from tornado.ioloop import IOLoop
import time
from threading import Thread


WIDTH = 480
HEIGHT = 360
FPS = 30
sessions = {}
class HttpHandler(tornado.web.RequestHandler):
    def initialize(self):
            pass

    def get(self):
        self.render("./index.html")

class WSHandler(WebSocketHandler):
    def initialize(self, camera):
        self.camera = camera
        self.state = True

    def open(self):
        print(self.request.remote_ip, ": connection opened")
        sessions[self.request.remote_ip] = self

    @staticmethod
    def rloop(camera):
        for foo in camera.capture_continuous(camera.stream, "jpeg", use_video_port=True):
            camera.stream.seek(0)
            img = camera.stream.read()
            for ip in sessions.keys():
                sessions[ip].write_message(img, binary=True)
            camera.stream.seek(0)
            camera.stream.truncate()

    @staticmethod
    def loop(camera):
        while True:
            img = camera.takeImage()
            for ip in sessions.keys():
                sessions[ip].write_message(img, binary=True)
            cv.WaitKey(1000/FPS)

    def on_close(self):
        self.state = False
        session = sessions.pop(self.request.remote_ip)
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
        t = Thread(target = WSHandler.rloop, args=(camera,))
    except ImportError:
        camera = Camera()
        t = Thread(target = WSHandler.loop, args=(camera,))
    t.setDaemon(True)
    t.start()
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
