import cv2 as cv
import time
import threading


class Webcam:
    def __init__(self, device_idx):
        self.capture = cv.VideoCapture(device_idx)
        self.capture.set(cv.CAP_PROP_FOURCC, cv.VideoWriter.fourcc("M", "J", "P", "G"))
        self.capture.set(cv.CAP_PROP_FPS, 30)
        self.capture.set(cv.CAP_PROP_BUFFERSIZE, 2)

        def capture_thread():
            while True:
                if self.capture.isOpened():
                    (self.status, self.frame) = self.capture.read()
                time.sleep(1 / self.get_fps())

        # Start frame capture thread
        self.capture_thread = threading.Thread(target=capture_thread, daemon=True)
        self.capture_thread.start()

    def get_frame(self):
        return self.frame

    def get_frame_size(self):
        if not self.capture.isOpened():
            return None

        return (
            self.capture.get(cv.CAP_PROP_FRAME_WIDTH),
            self.capture.get(cv.CAP_PROP_FRAME_HEIGHT),
        )

    def get_fps(self):
        if not self.capture.isOpened():
            return 0

        return self.capture.get(cv.CAP_PROP_FPS)
