"""
detection_page.py
The second screen: live camera feed on the left, detected sign text and
confidence on the right
"""

import tkinter as tk

from PIL import Image, ImageTk

import config

import os


class DetectionPage(tk.Frame):
    def __init__(self, master, labels, on_back, on_quit):
        super().__init__(master, bg=config.COLOR_BG_DARK)
        self.labels = labels
        self.on_back = on_back
        self.on_quit = on_quit

        self._video_photo = None  # keep a reference alive for Tkinter

        self._build_layout()

    # -- layout ---------------------------------------------------------------

    def _build_layout(self):
        # Top bar -------------------------------------------------------------
        topbar = tk.Frame(self, bg=config.COLOR_PANEL, height=56)
        topbar.pack(side="top", fill="x")
        topbar.pack_propagate(False)

        title = tk.Label(
            topbar,
            text="🤟  Sign Language Detector",
            font=("Segoe UI", 14, "bold"),
            fg=config.COLOR_TEXT_PRIMARY,
            bg=config.COLOR_PANEL,
        )
        title.pack(side="left", padx=20)

        self.status_label = tk.Label(
            topbar,
            text="● Camera starting...",
            font=("Segoe UI", 10, "bold"),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_PANEL,
        )
        self.status_label.pack(side="left", padx=10)

        end_btn = self._make_small_button(
            topbar,
            text="■  End Program",
            bg=config.COLOR_DANGER,
            hover_bg=config.COLOR_DANGER_HOVER,
            fg="#2B0B0B",
            command=self.on_quit,
        )
        end_btn.pack(side="right", padx=(10, 20), pady=10)

        back_btn = self._make_small_button(
            topbar,
            text="←  Back to Menu",
            bg=config.COLOR_PANEL_LIGHT,
            hover_bg=config.COLOR_BORDER,
            fg=config.COLOR_TEXT_PRIMARY,
            command=self.on_back,
        )
        back_btn.pack(side="right", padx=10, pady=10)

        # Body: left camera / right results ------------------------------------
        body = tk.Frame(self, bg=config.COLOR_BG_DARK)
        body.pack(side="top", fill="both", expand=True)
        body.columnconfigure(0, weight=3, uniform="cols")
        body.columnconfigure(1, weight=2, uniform="cols")
        body.rowconfigure(0, weight=1)

        self._build_camera_panel(body)
        self._build_results_panel(body)

    def _build_camera_panel(self, parent):
        left = tk.Frame(parent, bg=config.COLOR_BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)

        # ---------- Reference image ----------
        self.reference_frame = tk.Frame(
            left,
            bg=config.COLOR_PANEL,
            height=130
        )
        ref_title = tk.Label(
            left,
            text="REFERENCE",
            font=("Segoe UI", 11, "bold"),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_BG_DARK
        )
        ref_title.pack(anchor="w", pady=(0,5))

        self.reference_frame.pack(
            fill="x",
            pady=(0,10)
        )
        self.reference_frame.pack_propagate(False)


        path = os.path.join("assets", "reference.png")

        if os.path.exists(path):

            img = Image.open(path)

            # landscape
            img.thumbnail((700, 110))

            photo = ImageTk.PhotoImage(img)

            self.reference_label = tk.Label(
                self.reference_frame,
                image=photo,
                bg=config.COLOR_PANEL
            )

            self.reference_label.image = photo
            self.reference_label.pack(
                expand=True
            )

        # ---------- Camera view ----------
        header = tk.Label(
            left,
            text="CAMERA VIEW",
            font=("Segoe UI", 11, "bold"),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_BG_DARK,
        )
        header.pack(anchor="w", pady=(0, 8))

        video_frame = tk.Frame(
            left, bg="#000000", highlightthickness=2,
            highlightbackground=config.COLOR_BORDER,
        )
        video_frame.pack(fill="both", expand=True)

        self.video_label = tk.Label(video_frame, bg="#000000")
        self.video_label.pack(fill="both", expand=True)

    def _build_results_panel(self, parent):
        right = tk.Frame(parent, bg=config.COLOR_BG_DARK)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)

        header = tk.Label(
            right,
            text="DETECTION RESULT",
            font=("Segoe UI", 11, "bold"),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_BG_DARK,
        )
        header.pack(anchor="w", pady=(0, 8))

        # --- Main prediction card -------------------------------------------------
        card = tk.Frame(
            right, bg=config.COLOR_PANEL, highlightthickness=1,
            highlightbackground=config.COLOR_BORDER,
        )
        card.pack(fill="x", pady=(0, 16))

        inner = tk.Frame(card, bg=config.COLOR_PANEL)
        inner.pack(fill="x", padx=24, pady=24)

        tk.Label(
            inner, text="Detected Sign", font=("Segoe UI", 11),
            fg=config.COLOR_TEXT_SECONDARY, bg=config.COLOR_PANEL,
        ).pack(anchor="w")

        self.sign_text_label = tk.Label(
            inner,
            text="—",
            font=("Segoe UI", 30, "bold"),
            fg=config.COLOR_ACCENT,
            bg=config.COLOR_PANEL,
            wraplength=380,
            justify="left",
        )
        self.sign_text_label.pack(anchor="w", pady=(4, 16))

        tk.Label(
            inner, text="Confidence", font=("Segoe UI", 11),
            fg=config.COLOR_TEXT_SECONDARY, bg=config.COLOR_PANEL,
        ).pack(anchor="w")

        conf_row = tk.Frame(inner, bg=config.COLOR_PANEL)
        conf_row.pack(fill="x", pady=(4, 4))

        self.confidence_value_label = tk.Label(
            conf_row,
            text="0%",
            font=("Segoe UI", 20, "bold"),
            fg=config.COLOR_TEXT_PRIMARY,
            bg=config.COLOR_PANEL,
        )
        self.confidence_value_label.pack(side="left")

        self.confidence_bar_bg = tk.Frame(
            inner, bg=config.COLOR_PANEL_LIGHT, height=14
        )
        self.confidence_bar_bg.pack(fill="x", pady=(8, 0))
        self.confidence_bar_fill = tk.Frame(
            self.confidence_bar_bg, bg=config.COLOR_ACCENT, height=14, width=0
        )
        self.confidence_bar_fill.place(x=0, y=0, relheight=1, width=0)

        # --- All-class breakdown ----------------------------------------------
        breakdown_header = tk.Label(
            right,
            text="ALL CLASSES",
            font=("Segoe UI", 11, "bold"),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_BG_DARK,
        )
        breakdown_header.pack(anchor="w", pady=(8, 8))

        breakdown_card = tk.Frame(
            right, bg=config.COLOR_PANEL, highlightthickness=1,
            highlightbackground=config.COLOR_BORDER,
        )
        breakdown_card.pack(fill="both", expand=True)

        self._class_rows = {}
        breakdown_inner = tk.Frame(breakdown_card, bg=config.COLOR_PANEL)
        breakdown_inner.pack(fill="both", expand=True, padx=20, pady=18)

        for label in self.labels:
            row = tk.Frame(breakdown_inner, bg=config.COLOR_PANEL)
            row.pack(fill="x", pady=6)

            name_lbl = tk.Label(
                row, text=label, font=("Segoe UI", 11),
                fg=config.COLOR_TEXT_PRIMARY, bg=config.COLOR_PANEL,
                width=16, anchor="w",
            )
            name_lbl.pack(side="left")

            bar_bg = tk.Frame(row, bg=config.COLOR_PANEL_LIGHT, height=10)
            bar_bg.pack(side="left", fill="x", expand=True, padx=10)
            bar_fill = tk.Frame(bar_bg, bg=config.COLOR_BORDER, height=10, width=0)
            bar_fill.place(x=0, y=0, relheight=1, width=0)

            pct_lbl = tk.Label(
                row, text="0%", font=("Segoe UI", 10),
                fg=config.COLOR_TEXT_SECONDARY, bg=config.COLOR_PANEL,
                width=5, anchor="e",
            )
            pct_lbl.pack(side="left")

            self._class_rows[label] = {
                "bar_bg": bar_bg,
                "bar_fill": bar_fill,
                "pct_lbl": pct_lbl,
            }

    # -- helpers ---------------------------------------------------------------

    def _make_small_button(self, parent, text, bg, hover_bg, fg, command):
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=command,
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        return btn

    # -- public update API -------------------------------------------------------

    def set_status(self, text, color=None):
        self.status_label.configure(text=text, fg=color or config.COLOR_TEXT_SECONDARY)

    def update_video_frame(self, pil_image):
        """pil_image: a PIL.Image already sized to fit the video label."""
        self._video_photo = ImageTk.PhotoImage(pil_image)
        self.video_label.configure(image=self._video_photo)

    def show_camera_placeholder(self, text):
        self.video_label.configure(image="", text=text, fg=config.COLOR_TEXT_SECONDARY,
                                    font=("Segoe UI", 13))

    def update_prediction(self, best_label, best_confidence, ranked, below_threshold):
        display_text = best_label if not below_threshold else "Detecting..."
        self.sign_text_label.configure(text=display_text)

        pct = best_confidence * 100
        self.confidence_value_label.configure(text=f"{pct:.0f}%")

        bar_color = config.COLOR_ACCENT if not below_threshold else config.COLOR_BORDER
        self.confidence_bar_fill.configure(bg=bar_color)
        self._set_bar_width(self.confidence_bar_bg, self.confidence_bar_fill, best_confidence)

        for label, score in ranked:
            row = self._class_rows.get(label)
            if not row:
                continue
            row["pct_lbl"].configure(text=f"{score * 100:.0f}%")
            is_top = label == best_label and not below_threshold
            row["bar_fill"].configure(
                bg=config.COLOR_ACCENT if is_top else config.COLOR_BORDER
            )
            self._set_bar_width(row["bar_bg"], row["bar_fill"], score)

    @staticmethod
    def _set_bar_width(bar_bg, bar_fill, fraction):
        bar_bg.update_idletasks()
        total_width = bar_bg.winfo_width() or 1
        fraction = max(0.0, min(1.0, fraction))
        bar_fill.place(x=0, y=0, relheight=1, width=int(total_width * fraction))
