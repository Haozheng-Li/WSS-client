import cv2
import imutils


class MotionDetector:
    def __init__(self) -> None:
        self.result = False

        self.benchmark_frame = None
        self.frame = None

    def frame_delta_detect(self, frame):
        frame = imutils.resize(frame, width=500)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.benchmark_frame is None:
            self.benchmark_frame = gray
            return False, frame

        frame_delta = cv2.absdiff(self.benchmark_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

        thresh = cv2.dilate(thresh, None, iterations=2)
        counts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in counts:
            if cv2.contourArea(c) < 500:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            self.result = True

        self.frame = frame

        return self.result, frame
