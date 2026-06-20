"""
camera_worker.py
Runs webcam capture + model inference on a background thread so the
Tkinter UI never freezes while OpenCV grabs frames or the model predicts.

The worker pushes results onto a thread-safe queue; the UI polls that
queue on its own schedule (via root.after) and updates widgets from the
main thread only, which is required by Tkinter.

Each frame also gets hand/face landmark detection (MediaPipe) so the UI
can draw bounding boxes + hand keypoints. This runs every frame (it's
cheap) while the heavier sign-classification model only runs periodically
(see config.PREDICTION_INTERVAL_MS).
"""

import queue
import threading
import time

import cv2

import config
from landmark_detector import LandmarkDetector
from audio_announcer import AudioAnnouncer


class CameraWorker:
    """Background thread that owns the webcam, the model, and the landmark detector."""

    def __init__(self, model, camera_index=config.CAMERA_INDEX):
        self.model = model
        self.camera_index = camera_index
        self.landmark_detector = LandmarkDetector(
            detect_hands=config.DETECT_HANDS,
            detect_face=config.DETECT_FACE,
            max_num_hands=config.MAX_NUM_HANDS,
            min_detection_confidence=config.LANDMARK_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.LANDMARK_MIN_TRACKING_CONFIDENCE,
        )

        self.audio_announcer = None
        if config.ENABLE_AUDIO:
            self.audio_announcer = AudioAnnouncer()
            self.audio_announcer.start()
        self._last_announced_label = None

        self.frame_queue = queue.Queue(maxsize=1)   # latest (frame, detections) for display
        self.result_queue = queue.Queue(maxsize=1)  # latest prediction
        self.error_queue = queue.Queue(maxsize=1)    # startup / runtime errors

        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._drain(self.frame_queue)
        self._drain(self.result_queue)
        self.landmark_detector.close()
        if self.audio_announcer is not None:
            self.audio_announcer.stop()

    @staticmethod
    def _drain(q):
        while True:
            try:
                q.get_nowait()
            except queue.Empty:
                break

    def _push_latest(self, q, item):
        """Keeps only the most recent item in a size-1 queue."""
        self._drain(q)
        try:
            q.put_nowait(item)
        except queue.Full:
            pass

    def _run(self):
        cap = cv2.VideoCapture(self.camera_index)

        # Try to give the camera a decent default resolution; harmless if
        # the device ignores these requests.
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not cap.isOpened():
            self._push_latest(
                self.error_queue,
                "Could not access the webcam. Check that it's connected "
                "and not in use by another application.",
            )
            return

        last_predict_time = 0.0
        audio_error_reported = False

        try:
            while not self._stop_event.is_set():
                ok, frame_bgr = cap.read()
                if not ok:
                    self._push_latest(
                        self.error_queue, "Lost connection to the webcam."
                    )
                    break

                frame_bgr = cv2.flip(frame_bgr, 1)  # mirror for natural framing
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

                detections = self.landmark_detector.process(frame_rgb)
                detections["hand_connections"] = self.landmark_detector.hand_connections

                self._push_latest(self.frame_queue, (frame_rgb, detections))

                if (
                    not audio_error_reported
                    and self.audio_announcer is not None
                    and self.audio_announcer.last_error
                ):
                    # Don't block the app over this - just let the user know
                    # once that voice announcements aren't working.
                    audio_error_reported = True
                    self._push_latest(
                        self.error_queue,
                        "Voice announcements are unavailable "
                        f"({self.audio_announcer.last_error}). The rest of "
                        "the app will keep working normally.",
                    )

                now = time.time()
                if (now - last_predict_time) * 1000 >= config.PREDICTION_INTERVAL_MS:
                    last_predict_time = now
                    try:
                        label, confidence, ranked = self.model.predict(frame_rgb)
                        self._push_latest(
                            self.result_queue, (label, confidence, ranked)
                        )
                        self._maybe_announce(label, confidence)
                    except Exception as exc:  # noqa: BLE001
                        self._push_latest(
                            self.error_queue, f"Prediction error: {exc}"
                        )
        finally:
            cap.release()

    def _maybe_announce(self, label, confidence):
        """Speaks the label aloud only when it's a confident, *new* sign
        (different from the last one announced) - not on every tick."""
        if self.audio_announcer is None:
            return

        if confidence < config.CONFIDENCE_THRESHOLD:
            # Below threshold: nothing solid is being shown right now, so
            # reset tracking. This lets the same sign be announced again
            # next time it's confidently shown (e.g. after lowering your
            # hand and raising it again).
            self._last_announced_label = None
            return

        if label == self._last_announced_label:
            return

        self._last_announced_label = label
        self.audio_announcer.announce(label)
