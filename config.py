"""
config.py
Central configuration for the Sign Language Detector app.
Keeping these values in one place makes it easy to re-skin the app
or point it at a different Teachable Machine export later.
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
CAMERA_INDEX = 0              # change if you have more than one webcam
PREDICTION_INTERVAL_MS = 200  # how often (ms) to run a new prediction
CONFIDENCE_THRESHOLD = 0.60   # below this, the UI shows "..." instead of a guess

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
    and returns an ordered list of label strings.
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
