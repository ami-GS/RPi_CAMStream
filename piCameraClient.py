import numpy
from ws4py.client.tornadoclient import TornadoWebSocketClient
import zlib
from tornado.ioloop import IOLoop
import cv2.cv as cv
import cv2
from threading import Thread
import sys
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
                decimg = self._decode_image(Frames.pop(0))
                self._show_image(decimg)
                if cv.WaitKey(30) == 27:
                    break

    def _decode_image(self, img):
        narray = numpy.fromstring(img, dtype="uint8")
        decimg = cv2.imdecode(narray, 1)
        return decimg

    def _show_image(self, img):
        cv2.imshow('RPiCAM', img) 


def wsFuncCli(host, port):
    ws = ReceiveWebSocket("ws://"+host+":"+port+"/camera", protocols=["http-only", "chat"])
    ws.connect()
    IOLoop.instance().start()


def main(host="localhost", port="8080"):    
    Show = ShowPicture()
    t = Thread(target=wsFuncCli, args=(host, port))
    t.setDaemon(True)
    t.start()
    Show.run()
            

HELP = "Usage : piCameraClient.py [host] [port]"

if __name__ == "__main__":
    args = sys.argv
    if len(args) == 1:
        print HELP
        main()
    elif len(args) == 2:
        main(args[1])
    elif len(args) == 3:
        main(args[1], args[2])
    else:
        print HELP


