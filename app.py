"""
app.py
Main application controller. Wires together:
  - LandingPage   (background image + Start Camera / End Program)
  - DetectionPage (camera feed left, sign + accuracy right)
  - CameraWorker  (background thread doing capture + inference)
  - SignLanguageModel (loads the Teachable Machine .h5 model)

Run this file to launch the app: `python app.py`
"""

import queue
import sys
import tkinter as tk
from tkinter import messagebox

from PIL import Image

import config
from camera_worker import CameraWorker
from detection_page import DetectionPage
from landing_page import LandingPage
from sign_model import SignLanguageModel
from overlay_drawing import draw_detections


class SignLanguageApp:
    def __init__(self, root):
        self.root = root
        self.root.title(config.APP_TITLE)
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.minsize(config.MIN_WINDOW_WIDTH, config.MIN_WINDOW_HEIGHT)
        self.root.configure(bg=config.COLOR_BG_DARK)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        self.model = None          # lazily loaded on first "Start Camera" click
        self.camera_worker = None
        self._poll_job = None

        self.container = tk.Frame(self.root, bg=config.COLOR_BG_DARK)
        self.container.pack(fill="both", expand=True)

        self.landing_page = LandingPage(
            self.container, on_start=self.start_camera, on_quit=self.quit_app
        )
        self.detection_page = None  # built after labels are known

        self.landing_page.pack(fill="both", expand=True)

    # -- navigation -------------------------------------------------------------

    def start_camera(self):
        self.landing_page.start_btn.configure(state="disabled", text="Loading model...")
        self.root.update_idletasks()

        try:
            if self.model is None:
                self.model = SignLanguageModel()
        except Exception as exc:  # noqa: BLE001
            self.landing_page.start_btn.configure(state="normal", text="▶   Start Camera")
            messagebox.showerror(
                "Model Load Error",
                f"Could not load the sign language model:\n\n{exc}",
            )
            return

        if self.detection_page is None:
            self.detection_page = DetectionPage(
                self.container,
                labels=self.model.labels,
                on_back=self.stop_camera_and_go_back,
                on_quit=self.quit_app,
            )

        self.landing_page.pack_forget()
        self.detection_page.pack(fill="both", expand=True)
        self.detection_page.set_status("● Starting camera...", config.COLOR_TEXT_SECONDARY)

        self.camera_worker = CameraWorker(self.model)
        self.camera_worker.start()
        self._poll_camera_worker()

        self.landing_page.start_btn.configure(state="normal", text="▶   Start Camera")

    def stop_camera_and_go_back(self):
        self._stop_camera()
        self.detection_page.pack_forget()
        self.landing_page.pack(fill="both", expand=True)

    def quit_app(self):
        self._stop_camera()
        self.root.destroy()
        sys.exit(0)

    # -- camera worker polling loop -------------------------------------------

    def _stop_camera(self):
        if self._poll_job is not None:
            self.root.after_cancel(self._poll_job)
            self._poll_job = None
        if self.camera_worker is not None:
            self.camera_worker.stop()
            self.camera_worker = None

    def _poll_camera_worker(self):
        if self.camera_worker is None:
            return

        # -- errors ---------------------------------------------------------
        try:
            err = self.camera_worker.error_queue.get_nowait()
            if err.startswith("Voice announcements"):
                # Non-fatal: keep the camera loop running, just let the
                # user know once via a small dialog.
                messagebox.showwarning("Audio Notice", err)
            else:
                self.detection_page.set_status("● Camera error", config.COLOR_DANGER)
                self.detection_page.show_camera_placeholder(err)
                messagebox.showerror("Camera Error", err)
                self._poll_job = None
                return  # stop polling; user can go Back and retry
        except queue.Empty:
            pass

        # -- latest frame -----------------------------------------------------
        try:
            frame_rgb, detections = self.camera_worker.frame_queue.get_nowait()
            draw_detections(frame_rgb, detections)
            self._render_frame(frame_rgb)
            self.detection_page.set_status("● Live", config.COLOR_ACCENT)
        except queue.Empty:
            pass

        # -- latest prediction --------------------------------------------------
        try:
            label, confidence, ranked = self.camera_worker.result_queue.get_nowait()
            below_threshold = confidence < config.CONFIDENCE_THRESHOLD
            self.detection_page.update_prediction(label, confidence, ranked, below_threshold)
        except queue.Empty:
            pass

        self._poll_job = self.root.after(33, self._poll_camera_worker)  # ~30 fps UI refresh

    def _render_frame(self, frame_rgb):
        label = self.detection_page.video_label
        target_w = max(label.winfo_width(), 1)
        target_h = max(label.winfo_height(), 1)

        img = Image.fromarray(frame_rgb)
        img_w, img_h = img.size

        # Scale to fill the label while preserving aspect ratio, then
        # center-crop any overflow so the feed always fills the panel.
        scale = max(target_w / img_w, target_h / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))

        self.detection_page.update_video_frame(img)


def main():
    root = tk.Tk()
    SignLanguageApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
