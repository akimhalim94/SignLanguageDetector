"""
config.py
Central configuration for paths, UI styling, camera behaviour, and prediction validation.
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

# Individual reference images.
# Place the files below inside your assets folder.
SIGN_REFERENCE_IMAGES = {
    "MAAF": os.path.join(ASSETS_DIR, "maaf.png"),
    "HELLO": os.path.join(ASSETS_DIR, "hello.png"),
    "TERIMA KASIH": os.path.join(ASSETS_DIR, "terima_kasih.png"),
    "SAMA-SAMA": os.path.join(ASSETS_DIR, "sama_sama.png"),
    "JUMPA LAGI": os.path.join(ASSETS_DIR, "jumpa_lagi.png"),
}

# Replace each placeholder with the correct YouTube video URL.
SIGN_YOUTUBE_URLS = {
    "MAAF": "youtube.com/watch?v=WzP6REJMWwg&t=1s",
    "HELLO": "https://www.youtube.com/watch?v=J3Yts6SKxOQ&t=1s",
    "TERIMA KASIH": "https://www.youtube.com/watch?v=uQiZ5mBhers&t=1s",
    "SAMA-SAMA": "https://www.youtube.com/watch?v=DBCRj6JNGgk&t=1s",
    "JUMPA LAGI": "https://www.youtube.com/watch?v=cy6oVby5qMk&t=1s",
}

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
APP_TITLE = "Sign Language Recognizer"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 1050
MIN_WINDOW_HEIGHT = 680

# Fixed UI layout sizes
RIGHT_PANEL_WIDTH = 360
SIGN_GUIDE_HEIGHT = 180

# ---------------------------------------------------------------------------
# Model / inference
# ---------------------------------------------------------------------------
IMAGE_SIZE = 224
CAMERA_INDEX = 0
PREDICTION_INTERVAL_MS = 400
CONFIDENCE_THRESHOLD = 0.80
REQUIRED_STABLE_PREDICTIONS = 3
REQUIRE_HAND_FOR_PREDICTION = True

# ---------------------------------------------------------------------------
# Hand / face landmark detection
# ---------------------------------------------------------------------------
DETECT_HANDS = True
DETECT_FACE = True
MAX_NUM_HANDS = 2
LANDMARK_MIN_DETECTION_CONFIDENCE = 0.5
LANDMARK_MIN_TRACKING_CONFIDENCE = 0.5

COLOR_HAND_BOX_BGR = (178, 196, 64)
COLOR_HAND_LINE_BGR = (200, 220, 150)
COLOR_HAND_POINT_BGR = (78, 230, 255)
COLOR_FACE_BOX_BGR = (76, 76, 225)

# ---------------------------------------------------------------------------
# Audio announcement
# ---------------------------------------------------------------------------
ENABLE_AUDIO = True
# TTS_RATE = 170
# TTS_VOLUME = 1.0
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")

SIGN_AUDIO_PATHS = {
    "MAAF": os.path.join(AUDIO_DIR, "maaf.mp3"),
    "HELLO": os.path.join(AUDIO_DIR, "hello.mp3"),
    "TERIMA KASIH": os.path.join(AUDIO_DIR, "terima_kasih.mp3"),
    "SAMA-SAMA": os.path.join(AUDIO_DIR, "sama_sama.mp3"),
    "JUMPA LAGI": os.path.join(AUDIO_DIR, "jumpa_lagi.mp3"),
}

# ---------------------------------------------------------------------------
# UI colour palette
# ---------------------------------------------------------------------------
COLOR_BG_DARK = "#071426"
COLOR_BG_SOFT = "#0B1C32"
COLOR_PANEL = "#10243F"
COLOR_PANEL_LIGHT = "#16314F"
COLOR_ACCENT = "#45D0BE"
COLOR_ACCENT_HOVER = "#61DECD"
COLOR_SUCCESS = "#58D68D"
COLOR_WARNING = "#F5B041"
COLOR_DANGER = "#EF6262"
COLOR_DANGER_HOVER = "#FF7474"
COLOR_TEXT_PRIMARY = "#F5F9FF"
COLOR_TEXT_SECONDARY = "#9CB0C8"
COLOR_TEXT_MUTED = "#70869F"
COLOR_BORDER = "#244563"
COLOR_BLACK = "#000000"


def load_labels():
    labels = []

    if not os.path.exists(LABELS_PATH):
        raise FileNotFoundError(f"Labels file was not found: {LABELS_PATH}")

    with open(LABELS_PATH, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            parts = line.split(" ", 1)

            if len(parts) == 2 and parts[0].isdigit():
                labels.append(parts[1].strip())
            else:
                labels.append(line)

    return labels
