# Sign Language Detector

A desktop Python app that uses your Teachable Machine model to recognize signs
in real time from your webcam.

- **Landing page** — background image with **Start Camera** and **End Program** buttons
- **Detection page** — live camera feed on the left, detected sign + confidence
  (and a full per-class breakdown) on the right

Trained classes (from `model/labels.txt`): HELLO, TERIMA KASIH, JUMPA LAGI,
SAMA-SAMA, MAAF.

## 1. Install Python

Python 3.9–3.12 recommended. Check with:

```bash
python3 --version
```

## 2. Install dependencies

From inside the `SignLanguageDetector` folder:

```bash
pip install -r requirements.txt
```

This installs TensorFlow, `tf-keras` (needed to load this Teachable Machine
model on modern TensorFlow — see note below), OpenCV, Pillow, NumPy,
MediaPipe (for the hand/face detection boxes), and `pyttsx3` (for voice
announcements).

## 3. Run the app

```bash
python app.py
```

A window opens with the landing page. Click **Start Camera** to load the
model and begin detection, or **End Program** to quit.

On the detection screen:

- **Left** — your live camera feed, with a box drawn around any detected
  face and around each detected hand (plus the 21-point hand skeleton)
- **Right** — the currently detected sign, its confidence %, and a bar chart
  of all 5 classes
- The app **speaks the sign name out loud** the moment it confidently
  detects a _new_ sign (it won't repeat the same word over and over while
  you hold a sign steady)
- **Back to Menu** returns to the landing page (camera is released)
- **End Program** closes the app

## Project structure

```
SignLanguageDetector/
├── app.py                # main controller — run this file
├── config.py              # paths, colors, window size, thresholds
├── sign_model.py           # loads keras_model.h5 and runs predictions
├── camera_worker.py        # background thread: webcam capture + inference
├── landmark_detector.py    # MediaPipe hand/face detection (boxes + points)
├── overlay_drawing.py      # draws the boxes/skeleton onto each frame
├── audio_announcer.py      # text-to-speech announcements (offline, pyttsx3)
├── landing_page.py         # landing page UI (background + buttons)
├── detection_page.py       # detection page UI (camera + results panel)
├── requirements.txt
├── model/
│   ├── keras_model.h5      # your trained Teachable Machine model
│   └── labels.txt
└── assets/
    └── background.png      # landing page background
```
