# VideoStream.py
import cv2

class VideoStream:
    def __init__(self, filename):
        # Open the video capture
        self.cap = cv2.VideoCapture(filename)
        if not self.cap.isOpened():
            raise IOError(f"Cannot open video file {filename}")


        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.fps = fps if fps and fps > 0 else 25.0

        self.frameNum = 0

    def nextFrame(self):
        """
        Grab the next frame from the MP4, encode it as JPEG bytes,
        and return the byte array. Returns None when the video ends.
        """
        ret, frame = self.cap.read()
        if not ret:
            return None
        self.frameNum += 1

        # Encode as JPEG
        ok, buf = cv2.imencode('.jpg', frame)
        if not ok:
            return None
        return buf.tobytes()

    def frameNbr(self):
        """Return the current frame number (used for RTP seq)."""
        return self.frameNum
