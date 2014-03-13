RPi_CAMStream
=============

Take Picture using raspberry pi and send it to client with WebSocket

### TODO
* Implement Tree Based P2P Network
* Increase camera's fps as fast as possible
* Process image in Client side and send to leef clients


# Usage

## Server (Raspberry Pi side)

```
python piCamera.py usb # if you use usb camera
python piCamera.py rpi # if you use raspberry pi camera module
```

## Client
```
python piCameraClient.py [host] [port]
```
Default host is 'localhost' and port is '8080'
