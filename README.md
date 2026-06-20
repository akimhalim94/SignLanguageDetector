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

**Linux only:** `pyttsx3` needs the `espeak-ng` system package (not a pip
package) to actually produce speech:

```bash
sudo apt install espeak-ng
```

Windows and macOS use their built-in OS voices and don't need this step.

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
  detects a *new* sign (it won't repeat the same word over and over while
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

## Notes & troubleshooting

**Model compatibility:** This model was exported from Google's Teachable
Machine using an older Keras version. Current TensorFlow (Keras 3) can't load
it directly because of a `DepthwiseConv2D` config mismatch. The app works
around this automatically by using the `tf-keras` legacy-Keras-2 loader
(set via `TF_USE_LEGACY_KERAS=1` in `sign_model.py`) — you don't need to do
anything extra, just make sure `tf-keras` is installed (it's in
`requirements.txt`).

**MediaPipe version:** `requirements.txt` pins `mediapipe<0.10.30` because
the hand/face box feature uses MediaPipe's older `mp.solutions` API, which
was removed in newer releases in favor of a different "Tasks" API. Staying
under that version keeps the simple, no-extra-downloads setup working. If
you ever upgrade mediapipe past that and boxes stop appearing, that's why.

**Turning the boxes on/off:** In `config.py`, set `DETECT_HANDS = False` and/or
`DETECT_FACE = False`. You can also tweak box/skeleton colors there
(`COLOR_HAND_BOX_BGR`, `COLOR_FACE_BOX_BGR`, etc. — note these are in BGR
order since drawing happens with OpenCV).

**Turning audio off / adjusting it:** Set `ENABLE_AUDIO = False` in
`config.py` to disable voice announcements entirely. `TTS_RATE` controls
speech speed (words/minute) and `TTS_VOLUME` controls loudness (0.0–1.0).
Announcements happen every time the detected sign changes to a new,
confident result (above `CONFIDENCE_THRESHOLD`) — holding the same sign
steady won't repeat it on every tick, but switching to a different sign
always announces it, even if you switch quickly. If a sign changes again
while a previous word is still being spoken, it's queued and spoken right
after — it won't get silently skipped. If you see an "Audio Notice" popup
saying voice announcements are unavailable, it usually means the
`espeak-ng` system package is missing (Linux) — see the install step above.
The rest of the app keeps working normally either way.

**"Only the first announcement ever plays, then audio goes silent":** this
was a real bug in earlier versions of this app, caused by reusing one
pyttsx3 engine for every utterance — a known pyttsx3 issue (most common on
Windows' SAPI5 voice driver) where the engine's internal run loop can stop
responding after the first `runAndWait()` call. The fix already in this
version creates a fresh, short-lived engine for each word spoken, which
avoids the issue. If you're still seeing this after updating, double-check
you replaced *all* the files (especially `audio_announcer.py`), not just
some of them.

**Camera not opening:** Make sure no other app is using the webcam, and that
you've granted camera permission to your terminal/Python. If you have more
than one camera, change `CAMERA_INDEX` in `config.py` (0, 1, 2, ...).

**Low accuracy / wrong predictions:** Make sure your hand is well lit,
centered, and reasonably close to the camera — same conditions the model was
trained under in Teachable Machine. You can adjust the sensitivity by
changing `CONFIDENCE_THRESHOLD` in `config.py` (default 0.60).

**Swapping in a new model:** Replace `model/keras_model.h5` and
`model/labels.txt` with a new Teachable Machine export (Image Project, same
file names) and restart the app — no code changes needed.

**Changing the background:** Replace `assets/background.png` with any image
you like (any resolution; it auto-scales to the window).
