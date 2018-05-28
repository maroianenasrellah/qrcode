# import the necessary packages
from imutils.video import VideoStream
from pyzbar import pyzbar
import time
import cv2
import threading
def barcode_scan():
    # initialize the video stream and allow the camera sensor to warm up
    print("[INFO] starting video stream...")
    vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)

    barcodeData=""

    try:
        while True:
            frame = vs.read()
            barcodes = pyzbar.decode(frame)
            for barcode in barcodes:
                barcodeData = barcode.data.decode("utf-8")
                print("Scanned Barcode Data",barcodeData)
                
    except KeyboardInterrupt:
        print("[INFO] cleaning up...")
        vs.stop()
        


w = threading.Thread(name='barcode_scan', target=barcode_scan).start()
    