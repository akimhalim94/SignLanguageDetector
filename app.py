"""
app.py
Main application controller.
"""

import queue
import sys
import tkinter as tk
from tkinter import messagebox

from PIL import Image

import config
from pages.detection_page import DetectionPage
from pages.landing_page import LandingPage
from src.camera_worker import CameraWorker
from src.overlay_drawing import draw_detections
from src.sign_model import SignLanguageModel


class SignLanguageApp:
    def __init__(self, root):
        self.root = root

        self.root.title(config.APP_TITLE)
        self.root.geometry(
            f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}"
        )
        self.root.minsize(
            config.MIN_WINDOW_WIDTH,
            config.MIN_WINDOW_HEIGHT,
        )
        self.root.configure(bg=config.COLOR_BG_DARK)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        self.model = None
        self.camera_worker = None
        self._poll_job = None

        self._hand_detected = False
        self._candidate_label = None
        self._candidate_count = 0
        self._last_confirmed_label = None

        self.container = tk.Frame(
            self.root,
            bg=config.COLOR_BG_DARK,
        )
        self.container.pack(fill="both", expand=True)

        self.landing_page = LandingPage(
            self.container,
            on_start=self.start_camera,
            on_quit=self.quit_app,
        )

        self.detection_page = None
        self.landing_page.pack(fill="both", expand=True)

    def start_camera(self):
        self.landing_page.start_btn.configure(
            state="disabled",
            text="Loading model…",
        )
        self.root.update_idletasks()

        try:
            if self.model is None:
                self.model = SignLanguageModel()

        except Exception as error:
            self.landing_page.start_btn.configure(
                state="normal",
                text="Start Recognition  →",
            )
            messagebox.showerror(
                "Model Load Error",
                f"Could not load the sign-language model:\n\n{error}",
            )
            return

        if self.detection_page is None:
            self.detection_page = DetectionPage(
                self.container,
                labels=self.model.labels,
                on_back=self.stop_camera_and_go_back,
                on_quit=self.quit_app,
            )

        self._reset_prediction_validation()
        self.detection_page.reset_detection()

        self.landing_page.pack_forget()
        self.detection_page.pack(fill="both", expand=True)

        self.detection_page.set_status(
            "● Starting camera…",
            config.COLOR_WARNING,
        )
        self.detection_page.show_camera_placeholder("Starting camera…")

        self.camera_worker = CameraWorker(self.model)
        self.camera_worker.start()
        self._poll_camera_worker()

        self.landing_page.start_btn.configure(
            state="normal",
            text="Start Recognition  →",
        )

    def stop_camera_and_go_back(self):
        self._stop_camera()

        if self.detection_page is not None:
            self.detection_page.reset_detection()
            self.detection_page.pack_forget()

        self.landing_page.pack(fill="both", expand=True)

    def quit_app(self):
        self._stop_camera()
        self.root.destroy()
        sys.exit(0)

    def _stop_camera(self):
        if self._poll_job is not None:
            try:
                self.root.after_cancel(self._poll_job)
            except tk.TclError:
                pass

            self._poll_job = None

        if self.camera_worker is not None:
            self.camera_worker.stop()
            self.camera_worker = None

        self._reset_prediction_validation()

    def _poll_camera_worker(self):
        if self.camera_worker is None:
            return

        self._process_worker_errors()
        self._process_latest_frame()
        self._process_latest_prediction()

        if self.camera_worker is not None:
            self._poll_job = self.root.after(
                33,
                self._poll_camera_worker,
            )

    def _process_worker_errors(self):
        try:
            error = self.camera_worker.error_queue.get_nowait()

            if error.startswith("Voice announcements"):
                messagebox.showwarning("Audio Notice", error)
                return

            self.detection_page.set_status(
                "● Camera error",
                config.COLOR_DANGER,
            )
            self.detection_page.show_camera_placeholder(error)
            self.detection_page.show_no_hand()

            messagebox.showerror("Camera Error", error)
            self._stop_camera()

        except queue.Empty:
            pass

    def _process_latest_frame(self):
        try:
            frame_rgb, detections = (
                self.camera_worker.frame_queue.get_nowait()
            )

        except queue.Empty:
            return

        hands = detections.get("hands", [])
        self._hand_detected = len(hands) > 0

        self.detection_page.set_hand_state(self._hand_detected)

        if not self._hand_detected:
            self._reset_prediction_validation()
            self.detection_page.show_no_hand()

        draw_detections(
            frame_rgb,
            detections,
            draw_hands=True,
            draw_face=False,
        )
        self._render_frame(frame_rgb)

        self.detection_page.set_status(
            "● Camera live",
            config.COLOR_SUCCESS,
        )

    def _process_latest_prediction(self):
        try:
            label, confidence, ranked = (
                self.camera_worker.result_queue.get_nowait()
            )

        except queue.Empty:
            return

        # Always refresh confidence for every model class.
        self.detection_page.update_class_confidences(ranked)
        self.detection_page.update_explanation(
            ranked,
            hand_detected=self._hand_detected,
        )

        if (
            config.REQUIRE_HAND_FOR_PREDICTION
            and not self._hand_detected
        ):
            self._reset_prediction_validation()
            self.detection_page.show_no_hand()
            return

        if confidence < config.CONFIDENCE_THRESHOLD:
            self._reset_prediction_validation()
            self.detection_page.show_low_confidence(confidence)
            return

        self._validate_consecutive_prediction(
            label,
            confidence,
        )

    def _validate_consecutive_prediction(
        self,
        label,
        confidence,
    ):
        if label == self._candidate_label:
            self._candidate_count += 1
        else:
            self._candidate_label = label
            self._candidate_count = 1

        if (
            self._candidate_count
            < config.REQUIRED_STABLE_PREDICTIONS
        ):
            self.detection_page.show_checking_prediction(
                label,
                confidence,
                self._candidate_count,
            )
            return

        self.detection_page.show_confirmed_prediction(
            label,
            confidence,
        )

        self._last_confirmed_label = label
        self._candidate_count = config.REQUIRED_STABLE_PREDICTIONS

    def _reset_prediction_validation(self):
        self._hand_detected = False
        self._candidate_label = None
        self._candidate_count = 0
        self._last_confirmed_label = None

    def _render_frame(self, frame_rgb):
        label = self.detection_page.video_label

        target_width = max(label.winfo_width(), 1)
        target_height = max(label.winfo_height(), 1)

        image = Image.fromarray(frame_rgb)
        image_width, image_height = image.size

        # Fit the entire camera frame inside the panel.
        # Using min() prevents cropping, so the user's full face and body
        # can remain visible. Empty space becomes a dark letterbox area.
        scale = min(
            target_width / image_width,
            target_height / image_height,
        )

        new_width = max(int(image_width * scale), 1)
        new_height = max(int(image_height * scale), 1)

        image = image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS,
        )

        canvas = Image.new(
            "RGB",
            (target_width, target_height),
            (0, 0, 0),
        )

        left = (target_width - new_width) // 2
        top = (target_height - new_height) // 2
        canvas.paste(image, (left, top))

        self.detection_page.update_video_frame(canvas)


def main():
    root = tk.Tk()
    SignLanguageApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
