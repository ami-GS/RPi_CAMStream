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
import time

Frames = []
interval = 100
class ReceiveWebSocket(TornadoWebSocketClient):
    def __init__(self, url, protocols=None, Show=None, extensions=None,
                io_loop=None, ssl_options=None, headers=None):

        TornadoWebSocketClient.__init__(self, url, protocols=protocols, extensions=extensions, 
                               io_loop=io_loop, ssl_options=ssl_options, headers=headers)
        self.connecting = False
        self.Show = Show
        self.url = url
        self.protocols = protocols

    def opened(self):
        print "\nconnected (press [esc] to exit)"
        self.connecting = True
    
    def received_message(self, message):
        try:
            m = zlib.decompress(str(message))
            self.Show.set_image(m)
        except Exception as e:
            print e
    
    def closed(self, code, reason=None):
        IOLoop.instance().stop()

    def wait_until_connect(self):
        print "connecting",
        while not self.connecting:
            print ".",
            time.sleep(0.5)
            ws = ReceiveWebSocket(self.url, protocols=self.protocols, Show=self.Show)
            ws.connect()
            IOLoop.instance().start()

class ShowPicture():
    def __init__(self):
        cv.NamedWindow("RPiCAM", 1)
        self.Frames = []

    def run(self):
        while True:
            if len(self.Frames):
                decimg = self._decode_image(self.Frames.pop(0))
                self._show_image(decimg)
                if cv.WaitKey(interval) == 27:
                    IOLoop.instance().stop()
                    break

    def _decode_image(self, img):
        narray = numpy.fromstring(img, dtype="uint8")
        decimg = cv2.imdecode(narray, 1)
        return decimg

    def _show_image(self, img):
        cv2.imshow('RPiCAM', img) 

    def set_image(self, img):
        self.Frames.append(img)

def wsFuncCli(host, port, Show):
    ReceiveWebSocket("ws://"+host+":"+port+"/camera",
                     protocols=["http-only", "chat"], Show=Show).wait_until_connect()
#    IOLoop.instance().start()


def main(host="localhost", port="8080"):    
    Show = ShowPicture()
    t = Thread(target=wsFuncCli, args=(host, port, Show,))
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


