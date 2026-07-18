import queue
import threading
import time
import cv2
import config
from src.landmark_detector import LandmarkDetector
from src.audio_announcer import AudioAnnouncer


class CameraWorker:
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

        self.frame_queue = queue.Queue(maxsize=1)
        self.result_queue = queue.Queue(maxsize=1)
        self.error_queue = queue.Queue(maxsize=1)

        self._stop_event = threading.Event()
        self._thread = None

        self._candidate_label = None
        self._candidate_count = 0
        self._last_announced_label = None
        self._required_stable_predictions = getattr(
            config, "REQUIRED_STABLE_PREDICTIONS", 3
        )

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
            self.audio_announcer.clear()
            self.audio_announcer.stop()

        self._reset_prediction_state()

    @staticmethod
    def _drain(target_queue):
        while True:
            try:
                target_queue.get_nowait()
            except queue.Empty:
                break

    def _push_latest(self, target_queue, item):
        self._drain(target_queue)
        try:
            target_queue.put_nowait(item)
        except queue.Full:
            pass

    def _run(self):
        camera = cv2.VideoCapture(self.camera_index)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not camera.isOpened():
            self._push_latest(
                self.error_queue,
                "Could not access the webcam. Check that it is connected and not used by another application.",
            )
            return

        last_prediction_time = 0.0
        audio_error_reported = False

        try:
            while not self._stop_event.is_set():
                success, frame_bgr = camera.read()

                if not success:
                    self._push_latest(
                        self.error_queue,
                        "Lost connection to the webcam.",
                    )
                    break

                frame_bgr = cv2.flip(frame_bgr, 1)
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

                detections = self.landmark_detector.process(frame_rgb)
                detections["hand_connections"] = (
                    self.landmark_detector.hand_connections
                )

                self._push_latest(
                    self.frame_queue,
                    (frame_rgb, detections),
                )

                if (
                    not audio_error_reported
                    and self.audio_announcer is not None
                    and self.audio_announcer.last_error
                ):
                    audio_error_reported = True
                    self._push_latest(
                        self.error_queue,
                        f"Voice announcements are unavailable ({self.audio_announcer.last_error}).",
                    )

                hand_detected = len(detections.get("hands", [])) > 0

                # Main fix: no hand means no prediction and no speech.
                if not hand_detected:
                    self._reset_prediction_state()
                    self._drain(self.result_queue)

                    if self.audio_announcer is not None:
                        self.audio_announcer.clear()

                    continue

                now = time.time()
                if (
                    (now - last_prediction_time) * 1000
                    < config.PREDICTION_INTERVAL_MS
                ):
                    continue

                last_prediction_time = now

                try:
                    label, confidence, ranked = self.model.predict(frame_rgb)

                    self._push_latest(
                        self.result_queue,
                        (label, confidence, ranked),
                    )

                    self._handle_audio_prediction(label, confidence)

                except Exception as error:
                    self._push_latest(
                        self.error_queue,
                        f"Prediction error: {error}",
                    )

        finally:
            camera.release()

    def _handle_audio_prediction(self, label, confidence):
        if self.audio_announcer is None:
            return

        if confidence < config.CONFIDENCE_THRESHOLD:
            self._candidate_label = None
            self._candidate_count = 0
            return

        if label == self._candidate_label:
            self._candidate_count += 1
        else:
            self._candidate_label = label
            self._candidate_count = 1

        if self._candidate_count < self._required_stable_predictions:
            return

        if label == self._last_announced_label:
            return

        self._last_announced_label = label
        self.audio_announcer.announce(label)

    def _reset_prediction_state(self):
        self._candidate_label = None
        self._candidate_count = 0
        self._last_announced_label = None
