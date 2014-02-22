import cv

class ImageProcess():
    def __init__(self, img):
        self.grayImage = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_8U, 1)
        self.movingAvg = cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_32F, 3)
        self.diff = cv.CloneImage(img)
        self.tmp = cv.CloneImage(img)

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
            cv.Rectangle(img, pt1, pt2, cv.CV_RGB(255,0,0), 1)

        return img
