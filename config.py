"""
config.py
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

MODEL_PATH = os.path.join(MODEL_DIR, "keras_model.h5")
LABELS_PATH = os.path.join(MODEL_DIR, "labels.txt")
BACKGROUND_IMAGE_PATH = os.path.join(ASSETS_DIR, "background.png")

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
APP_TITLE = "Sign Language Detector"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 650

# ---------------------------------------------------------------------------
# Model / inference
# ---------------------------------------------------------------------------
IMAGE_SIZE = 224              # Teachable Machine models expect 224x224 input
CAMERA_INDEX = 0              # change if have more than one webcam
PREDICTION_INTERVAL_MS = 200  # how often (ms) to run a new prediction
CONFIDENCE_THRESHOLD = 0.60   # below this, the UI shows "..." instead of a guess

# ---------------------------------------------------------------------------
# Hand / face landmark detection
# ---------------------------------------------------------------------------
DETECT_HANDS = True
DETECT_FACE = True
MAX_NUM_HANDS = 2
LANDMARK_MIN_DETECTION_CONFIDENCE = 0.5
LANDMARK_MIN_TRACKING_CONFIDENCE = 0.5

COLOR_HAND_BOX_BGR = (178, 196, 64)    # teal-ish accent box around each hand
COLOR_HAND_LINE_BGR = (200, 220, 150)  # skeleton connector lines
COLOR_HAND_POINT_BGR = (78, 230, 255)  # knuckle/fingertip dots
COLOR_FACE_BOX_BGR = (76, 76, 225)     # box around detected face

# ---------------------------------------------------------------------------
# Audio announcement (text-to-speech)
# ---------------------------------------------------------------------------
ENABLE_AUDIO = True
TTS_RATE = 170      # words per minute
TTS_VOLUME = 1.0    # 0.0 - 1.0

# ---------------------------------------------------------------------------
# Color palette (matches the generated background)
# ---------------------------------------------------------------------------
COLOR_BG_DARK = "#0A192F"
COLOR_PANEL = "#10243F"
COLOR_PANEL_LIGHT = "#16314F"
COLOR_ACCENT = "#40C4B2"
COLOR_ACCENT_HOVER = "#54D8C6"
COLOR_DANGER = "#E14C4C"
COLOR_DANGER_HOVER = "#F06262"
COLOR_TEXT_PRIMARY = "#F4FAFF"
COLOR_TEXT_SECONDARY = "#9FB3C8"
COLOR_BORDER = "#23415F"


def load_labels():
    """
    Reads labels.txt (Teachable Machine format: "<index> <label name>")
    and returns ordered list of label strings.
    """
    labels = []
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Lines look like "0 HELLO" -> split off the leading index
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[0].isdigit():
                labels.append(parts[1].strip())
            else:
                labels.append(line)
    return labels
