import cv2
import cv2.cv as cv

class ImageProcess():
    def __init__(self, img):
        self.grayImage = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_8U, 1)
        self.movingAvg = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 3)
        self.diff = cv.CloneImage(img)
        self.tmp = cv.CloneImage(img)
        self.cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")

    def motionDetect(self, img):
        cv.Smooth(img, img, cv.CV_GAUSSIAN, 3, 0)

        cv.RunningAvg(img, self.movingAvg, 0.020, None)
        cv.ConvertScale(self.movingAvg, self.tmp, 1.0, 0.0)
        cv.AbsDiff(img, self.tmp, self.diff)
        cv.CvtColor(self.diff, self.grayImage, cv.CV_RGB2GRAY)
        cv.Threshold(self.grayImage, self.grayImage, 70,255, cv.CV_THRESH_BINARY)
        cv.Dilate(self.grayImage, self.grayImage, None, 18)#18   
        cv.Erode(self.grayImage, self.grayImage, None, 10)#10
        storage = cv.CreateMemStorage(0)
        contour = cv.FindContours(self.grayImage, storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE)
#        points = []                                                                                      
        while contour:
            boundRect = cv.BoundingRect(list(contour))
            contour = contour.h_next()
            pt1 = (boundRect[0], boundRect[1])
            pt2 = (boundRect[0] + boundRect[2], boundRect[1] + boundRect[3])
            cv.Rectangle(img, pt1, pt2, cv.CV_RGB(255,255,0), 1)

        return img

    def faceDetect(self, img):
        print type(img)
        rects = self.cascade.detectMultiScale(img, 1.3, 4, cv2.cv.CV_HAAR_SCALE_IMAGE)
#        rects = cascade.detectMultiScale(img,scaleFactor=1.3,minNeighbors=4,flags=cv.CV_HAAR_SCALE_IMAGE,minSize=(20,20),maxSize=(400,400))

        rects[:, 2:] += rects[:, :2]
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), (127, 255, 0), 2)
            
        return img

