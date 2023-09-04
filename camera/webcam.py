import cv2 as cv


class Webcam:
    def __init__(self, device_idx):
        self.cap = cv.VideoCapture(device_idx)

    def get_frame(self):
        if not self.cap or not self.cap.isOpened():
            return None

        result, frame = self.cap.read()
        if not result:
            return None

        return frame

    def get_frame_size(self):
        if not self.cap or not self.cap.isOpened():
            return None

        return (
            self.cap.get(cv.CAP_PROP_FRAME_WIDTH),
            self.cap.get(cv.CAP_PROP_FRAME_HEIGHT),
        )

    def get_fps(self):
        if not self.cap or not self.cap.isOpened():
            return 0

        self.cap.get(cv.CAP_PROP_FPS)
