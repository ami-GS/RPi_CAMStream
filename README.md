RPi_CAMStream
=============
Take Picture using raspberry pi and send it to client with WebSocket

###at present
broser version is suitable to use



# Usage

## Browser version

### Server (Rspberry Pi side)
```
python camera.py
```

### Client (Browser)
Access "http://raspberrypi:8080"


## Local client version

### Server (Raspberry Pi side)

```
python piCamera.py usb # if you use usb camera
python piCamera.py rpi # if you use raspberry pi camera module
```

### Client
```
python piCameraClient.py [host] [port]
```
Default host is 'localhost' and port is '8080'

### TODO
* Implement Tree Based P2P Network
* Increase camera's fps as fast as possible : Done
* Process image in Client side and send to leef clients
