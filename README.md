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
model on modern TensorFlow — see note below), OpenCV, Pillow, and NumPy.

## 3. Run the app

```bash
python app.py
```

A window opens with the landing page. Click **Start Camera** to load the
model and begin detection, or **End Program** to quit.

On the detection screen:
- **Left** — your live camera feed
- **Right** — the currently detected sign, its confidence %, and a bar chart
  of all 5 classes
- **Back to Menu** returns to the landing page (camera is released)
- **End Program** closes the app

## Project structure

```
SignLanguageDetector/
├── app.py              # main controller — run this file
├── config.py            # paths, colors, window size, thresholds
├── sign_model.py         # loads keras_model.h5 and runs predictions
├── camera_worker.py      # background thread: webcam capture + inference
├── landing_page.py       # landing page UI (background + buttons)
├── detection_page.py     # detection page UI (camera + results panel)
├── requirements.txt
├── model/
│   ├── keras_model.h5    # your trained Teachable Machine model
│   └── labels.txt
└── assets/
    └── background.png    # landing page background
```

## Notes & troubleshooting

**Model compatibility:** This model was exported from Google's Teachable
Machine using an older Keras version. Current TensorFlow (Keras 3) can't load
it directly because of a `DepthwiseConv2D` config mismatch. The app works
around this automatically by using the `tf-keras` legacy-Keras-2 loader
(set via `TF_USE_LEGACY_KERAS=1` in `sign_model.py`) — you don't need to do
anything extra, just make sure `tf-keras` is installed (it's in
`requirements.txt`).

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
