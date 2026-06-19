"""
camera_worker.py
Runs webcam capture + model inference on a background thread so the
Tkinter UI never freezes while OpenCV grabs frames or the model predicts.

The worker pushes results onto a thread-safe queue; the UI polls that
queue on its own schedule (via root.after) and updates widgets from the
main thread only, which is required by Tkinter.
"""

import queue
import threading
import time

import cv2

import config


class CameraWorker:
    """Background thread that owns the webcam and the model."""

    def __init__(self, model, camera_index=config.CAMERA_INDEX):
        self.model = model
        self.camera_index = camera_index

        self.frame_queue = queue.Queue(maxsize=1)   # latest frame for display
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

                self._push_latest(self.frame_queue, frame_rgb)

                now = time.time()
                if (now - last_predict_time) * 1000 >= config.PREDICTION_INTERVAL_MS:
                    last_predict_time = now
                    try:
                        label, confidence, ranked = self.model.predict(frame_rgb)
                        self._push_latest(
                            self.result_queue, (label, confidence, ranked)
                        )
                    except Exception as exc:  # noqa: BLE001
                        self._push_latest(
                            self.error_queue, f"Prediction error: {exc}"
                        )
        finally:
            cap.release()
