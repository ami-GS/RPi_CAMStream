import ws4py
import numpy
from ws4py.client.tornadoclient import TornadoWebSocketClient
import zlib
from tornado.ioloop import IOLoop
import cv2.cv as cv
import cv2
from threading import Thread
import wsaccel
wsaccel.patch_tornado()

Frames = []
class ReceiveWebSocket(TornadoWebSocketClient):
    def opened(self):
        print "connected"
    
    def received_message(self, message):
        try:
            m = zlib.decompress(str(message))
            Frames.append(m)
        except Exception as e:
            print e
    
    def closed(self, code, reason=None):
        print "closed"
        IOLoop.instance().stop()


class ShowPicture():
    def __init__(self):
        cv.NamedWindow("RPiCAM", 1)

    def run(self):
        while True:
            if len(Frames):
                narray = numpy.fromstring(Frames.pop(0), dtype="uint8")
                decimg = cv2.imdecode(narray, 1)
                self._show_image(decimg)
                if cv.WaitKey(30) == 27:
                    break

    def _show_image(self, img):
        cv2.imshow('RPiCAM', img) 


def wsFuncCli():
    ws = ReceiveWebSocket("ws://localhost:8080/camera", protocols=["http-only", "chat"])
    ws.connect()
    IOLoop.instance().start()


def main():    
    Show = ShowPicture()
    t = Thread(target=wsFuncCli)
    t.setDaemon(True)
    t.start()
    Show.run()
            

if __name__ == "__main__":
    main()
