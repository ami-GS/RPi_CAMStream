from ws4py.client.tornadoclient import TornadoWebSocketClient
import zlib
from tornado.ioloop import IOLoop, PeriodicCallback
import tornado, tornado.web, tornado.httpserver
from tornado.websocket import WebSocketHandler
import cv2.cv as cv
import cv2
from threading import Thread
import time
import sys
import wsaccel
wsaccel.patch_tornado()
import json
from imageprocess import ImageProcess

INTERVAL = 10#100
status = True
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
        print("\nconnected to " + 
              self.url[self.url.index("//")+2:self.url.rindex(":")] + 
              " (press [esc] to exit)")
        self.connecting = True
    
    def received_message(self, m):
        #type(message) = <class 'ws4py.messaging.BinaryMessage'>
        try:
            m = zlib.decompress(str(m))
            self.Show.set_image(m)
        except Exception as e:
            m = json.loads(str(m))
            if m[0] == "EXIT":
                print "This client IP is already connecting"
                self.closed()

#============For tree p2p================
#
            self._p2p_proto(m)
#            
#============================= 
    
    def _p2p_proto(self, m):
        openPort = m[3]
        if m[0] == "REDIRECT":
            host, port= m[1], m[2]
            print "Redirected to "+host+":"+port
            ReceiveWebSocket("ws://"+host+":"+port+"/camera",
                             protocols=["http-only", "chat"], Show=self.Show).wait_until_connect("leaf")
        elif m[0] == "KEEP":
            print "Keep connection"
        t = Thread(target=startWSServer, args=(str(openPort), self.Show),)
        t.setDaemon(True)
        t.start()
        
    def closed(self, code, reason=None):
        self.Show._finish()

    def wait_until_connect(self, node="root"):
        print "Now connecting",
        trial = 0
        while not self.connecting and trial < 20:
            time.sleep(0.5)
            ws = ReceiveWebSocket(self.url, protocols=self.protocols, Show=self.Show)
            ws.connect()
            IOLoop.instance().start()
            trial += 1
            print ".",
        else:
            print "\nConnection timeout"
            self._exit()

    
class WSHandler(WebSocketHandler):
    def initialize(self, Show):
        self.Show = Show
        self.period = 0.1
        self.leafClient = False

    def open(self):
        #self.callback = PeriodicCallback(self._send_image, self.period)
        #self.callback.start()
        print self.request.remote_ip, "connected here"
        self.leafClient = True
        while self.leafClient:
            self._send_image()
        
    def _send_image(self):
#        frame = self.Frames[0]
#        m = zlib.compress(frame)
#        self.write_message(m, binary=True)
        pass

    def on_message(self):
        pass

    def on_close(self):
        pass


class ShowPicture():
    def __init__(self):
        import numpy as np
        self.np = np
        cv2.namedWindow("RPiCAM", 1)
        self.Frames = []

    def run(self):
        while status:
            if len(self.Frames):
                decimg = self._decode_image(self.Frames.pop(0))
                self._show_image(decimg)
                if cv.WaitKey(INTERVAL) == 27:
                    self._finish()
                    break

    def _decode_image(self, img):
        narray = self.np.fromstring(img, dtype="uint8")
        decimg = cv2.imdecode(narray, 1)
        return decimg

    def _show_image(self, img):
        cv2.imshow('RPiCAM', img) 

    def set_image(self, img):
        self.Frames.append(img)

    def _finish(self):
        global status
        status = False
        IOLoop.instance().stop()
        cv2.destroyAllWindows()


def connectWS(host, port, Show):
    ReceiveWebSocket("ws://"+host+":"+port+"/camera",
                     protocols=["http-only", "chat"], Show=Show).wait_until_connect("root")


def getTreeP2PHost(host, port):
    request = tornado.httpclient.HTTPRequest(url="http://"+host+":"+port+"/", method="GET")
    client = tornado.httpclient.HTTPClient()
    try:
        response = client.fetch(request)
        if response.body:
            host = response.body
    except Exception as e:
        print e

    return host

def startWSServer(port, Show):
    app = tornado.web.Application([
        (r"/camera", WSHandler, dict(Show=Show)),
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(port)
    print "start server"
    #IOLoop.instance().start()
    #print e
#    should I use different IOLoop instance?????

def main(host="localhost", port="8080"):
    def initThread(thread):
        thread.setDaemon(True)
        return thread
#    host = getTreeP2PHost(host, port)
    Show = ShowPicture()
    initThread(Thread(target=connectWS, args=(host, port, Show,))).start()
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


