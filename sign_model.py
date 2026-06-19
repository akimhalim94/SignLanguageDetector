"""
sign_model.py
Wraps the Teachable Machine Keras model so the rest of the app doesn't need
to know anything about TensorFlow internals.

NOTE ON COMPATIBILITY:
Teachable Machine exports were generated with an older Keras (2.4.0) and use
a DepthwiseConv2D config that includes a 'groups' argument. Modern Keras
(3.x, bundled with current TensorFlow) does not accept that argument and
will throw a TypeError when loading the .h5 file directly. To keep this
project working out-of-the-box on current TensorFlow installs, we:
  1. Force TensorFlow to use its bundled legacy Keras 2 implementation
     (via the TF_USE_LEGACY_KERAS environment variable), which can read
     these older model files correctly.
  2. Patch DepthwiseConv2D to silently drop the unsupported 'groups' kwarg,
     as a safety net for environments where the legacy loader still
     forwards it.
"""

import os

# Must be set BEFORE tensorflow is imported anywhere in the process.
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")  # quiet TF startup logs

import numpy as np

import config


class SignLanguageModel:
    """Loads the trained model once and exposes a simple predict() method."""

    def __init__(self, model_path=config.MODEL_PATH, labels_path=config.LABELS_PATH):
        self.model_path = model_path
        self.labels = self._load_labels(labels_path)
        self.model = self._load_model(model_path)

    # -- loading -----------------------------------------------------------

    @staticmethod
    def _load_labels(labels_path):
        labels = []
        with open(labels_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" ", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    labels.append(parts[1].strip())
                else:
                    labels.append(line)
        return labels

    @staticmethod
    def _load_model(model_path):
        import tf_keras
        from tf_keras.layers import DepthwiseConv2D as _DepthwiseConv2D

        class DepthwiseConv2D(_DepthwiseConv2D):
            """Drops the legacy 'groups' kwarg that newer Keras rejects."""

            def __init__(self, *args, **kwargs):
                kwargs.pop("groups", None)
                super().__init__(*args, **kwargs)

        model = tf_keras.models.load_model(
            model_path,
            compile=False,
            custom_objects={"DepthwiseConv2D": DepthwiseConv2D},
        )
        return model

    # -- inference -----------------------------------------------------------

    def preprocess(self, frame_rgb):
        """
        Converts an RGB numpy frame (any size, uint8) into the normalized
        224x224x3 batch tensor that Teachable Machine models expect.
        """
        import cv2

        resized = cv2.resize(
            frame_rgb,
            (config.IMAGE_SIZE, config.IMAGE_SIZE),
            interpolation=cv2.INTER_AREA,
        )
        arr = resized.astype(np.float32)
        arr = (arr / 127.5) - 1.0  # Teachable Machine normalization: [-1, 1]
        return np.expand_dims(arr, axis=0)

    def predict(self, frame_rgb):
        """
        Runs a forward pass on a single RGB frame.
        Returns (label, confidence, all_scores) where all_scores is a list
        of (label, confidence) pairs sorted high to low.
        """
        batch = self.preprocess(frame_rgb)
        scores = self.model.predict(batch, verbose=0)[0]

        ranked = sorted(
            zip(self.labels, scores.tolist()), key=lambda p: p[1], reverse=True
        )
        best_label, best_score = ranked[0]
        return best_label, best_score, ranked
