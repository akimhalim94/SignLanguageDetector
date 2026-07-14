"""
landmark_detector.py
Wraps Hands and Face Detection solutions so the rest of the
app can ask "where are the hands/face in this frame?" and get back simple
data (bounding boxes + hand keypoints) ready for drawing.

This is independent of the sign-language Keras model: MediaPipe locates
hands/face, the Keras model classifies the sign. They run side-by-side on
every frame.
"""

import mediapipe as mp

import config


class LandmarkDetector:
    def __init__(
        self,
        detect_hands=True,
        detect_face=True,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ):
        self.detect_hands = detect_hands
        self.detect_face = detect_face

        self._hands = None
        self._face = None
        self._mp_hands_module = mp.solutions.hands  # keep for HAND_CONNECTIONS

        if detect_hands:
            self._hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=max_num_hands,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )

        if detect_face:
            self._face = mp.solutions.face_detection.FaceDetection(
                min_detection_confidence=min_detection_confidence
            )

    def process(self, frame_rgb):
        result = {"hands": [], "faces": []}

        if self._hands is not None:
            hands_result = self._hands.process(frame_rgb)
            if hands_result.multi_hand_landmarks:
                handedness_list = hands_result.multi_handedness or []
                for i, hand_landmarks in enumerate(hands_result.multi_hand_landmarks):
                    xs = [lm.x for lm in hand_landmarks.landmark]
                    ys = [lm.y for lm in hand_landmarks.landmark]
                    box = (min(xs), min(ys), max(xs), max(ys))
                    points = [(lm.x, lm.y) for lm in hand_landmarks.landmark]

                    label = None
                    if i < len(handedness_list):
                        label = handedness_list[i].classification[0].label

                    result["hands"].append(
                        {"box": box, "points": points, "label": label}
                    )

        if self._face is not None:
            face_result = self._face.process(frame_rgb)
            if face_result.detections:
                for detection in face_result.detections:
                    rb = detection.location_data.relative_bounding_box
                    xmin = rb.xmin
                    ymin = rb.ymin
                    xmax = rb.xmin + rb.width
                    ymax = rb.ymin + rb.height
                    result["faces"].append({"box": (xmin, ymin, xmax, ymax)})

        return result

    @property
    def hand_connections(self):
        """Pairs of point indices to draw as skeleton lines between."""
        return self._mp_hands_module.HAND_CONNECTIONS

    def close(self):
        if self._hands is not None:
            self._hands.close()
        if self._face is not None:
            self._face.close()
