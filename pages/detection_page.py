"""
detection_page.py

Layout:
- live camera on the left
- sign guide cards directly under the camera
- current result and all-class confidence on the right
"""

import os
import tkinter as tk
import webbrowser
from collections import deque

from PIL import Image, ImageTk

import config


class DetectionPage(tk.Frame):
    GUIDE_ORDER = [
        "MAAF",
        "HELLO",
        "TERIMA KASIH",
        "SAMA-SAMA",
        "JUMPA LAGI",
    ]

    def __init__(self, master, labels, on_back, on_quit):
        super().__init__(master, bg=config.COLOR_BG_DARK)

        self.labels = labels
        self.on_back = on_back
        self.on_quit = on_quit

        self._video_photo = None
        self._guide_photos = {}
        self._recent_results = deque(maxlen=4)
        self._class_rows = {}

        self._build_layout()
        self.reset_detection()

    # ------------------------------------------------------------------
    # Main layout
    # ------------------------------------------------------------------

    def _build_layout(self):
        self._build_topbar()

        body = tk.Frame(self, bg=config.COLOR_BG_DARK)
        body.pack(fill="both", expand=True, padx=22, pady=(18, 22))

        body.columnconfigure(0, weight=1)
        body.columnconfigure(
            1,
            weight=0,
            minsize=config.RIGHT_PANEL_WIDTH,
        )
        body.rowconfigure(0, weight=1)

        self._build_left_column(body)
        self._build_right_column(body)

    def _build_topbar(self):
        topbar = tk.Frame(
            self,
            bg=config.COLOR_PANEL,
            height=64,
        )
        topbar.pack(side="top", fill="x")
        topbar.pack_propagate(False)

        tk.Label(
            topbar,
            text="🤟  Sign Language Recognizer",
            font=("Segoe UI", 15, "bold"),
            fg=config.COLOR_TEXT_PRIMARY,
            bg=config.COLOR_PANEL,
        ).pack(side="left", padx=(22, 18))

        self.status_label = tk.Label(
            topbar,
            text="● Camera is off",
            font=("Segoe UI", 10, "bold"),
            fg=config.COLOR_TEXT_MUTED,
            bg=config.COLOR_PANEL,
        )
        self.status_label.pack(side="left")

        self._make_button(
            topbar,
            text="Exit",
            bg=config.COLOR_PANEL,
            hover_bg=config.COLOR_DANGER,
            fg=config.COLOR_TEXT_SECONDARY,
            command=self.on_quit,
        ).pack(side="right", padx=(8, 18), pady=12)

        self._make_button(
            topbar,
            text="←  Back",
            bg=config.COLOR_PANEL_LIGHT,
            hover_bg=config.COLOR_BORDER,
            fg=config.COLOR_TEXT_PRIMARY,
            command=self.on_back,
        ).pack(side="right", padx=8, pady=12)

    def _build_left_column(self, parent):
        left = tk.Frame(parent, bg=config.COLOR_BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        left.rowconfigure(0, weight=1)
        left.rowconfigure(1, weight=0)
        left.columnconfigure(0, weight=1)

        camera_card = self._make_card(left)
        camera_card.grid(row=0, column=0, sticky="nsew")

        camera_header = tk.Frame(
            camera_card,
            bg=config.COLOR_PANEL,
            height=52,
        )
        camera_header.pack(fill="x")
        camera_header.pack_propagate(False)

        tk.Label(
            camera_header,
            text="LIVE CAMERA",
            font=("Segoe UI", 11, "bold"),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_PANEL,
        ).pack(side="left", padx=18)

        self.hand_badge = tk.Label(
            camera_header,
            text="No hand detected",
            font=("Segoe UI", 10, "bold"),
            fg=config.COLOR_TEXT_MUTED,
            bg=config.COLOR_PANEL_LIGHT,
            padx=12,
            pady=6,
        )
        self.hand_badge.pack(side="right", padx=16, pady=10)

        video_container = tk.Frame(camera_card, bg=config.COLOR_BLACK)
        video_container.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12),
        )

        self.video_label = tk.Label(
            video_container,
            bg=config.COLOR_BLACK,
            fg=config.COLOR_TEXT_SECONDARY,
            font=("Segoe UI", 13),
        )
        self.video_label.pack(fill="both", expand=True)

        self._build_sign_guide(left)

    def _build_sign_guide(self, parent):
        guide_card = self._make_card(parent)
        guide_card.configure(height=150)
        guide_card.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(7, 0),
        )
        guide_card.grid_propagate(False)
        guide_card.pack_propagate(False)

        header = tk.Frame(guide_card, bg=config.COLOR_PANEL)
        header.pack(fill="x", padx=14, pady=(6, 3))

        tk.Label(
            header,
            text="SIGN GUIDE",
            font=("Segoe UI", 10, "bold"),
            fg=config.COLOR_TEXT_MUTED,
            bg=config.COLOR_PANEL,
        ).pack(side="left")
        
        tk.Label(
            header,
            text="Click a sign to open its YouTube tutorial",
            font=("Segoe UI", 9),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_PANEL,
        ).pack(side="right")

        cards_row = tk.Frame(guide_card, bg=config.COLOR_PANEL)
        cards_row.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        for column, sign_name in enumerate(self.GUIDE_ORDER):
            cards_row.columnconfigure(column, weight=1, uniform="guide")

            card = tk.Frame(
                cards_row,
                bg=config.COLOR_BG_SOFT,
                highlightthickness=1,
                highlightbackground=config.COLOR_BORDER,
                cursor="hand2",
            )
            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=4,
            )

            image_label = tk.Label(
                card,
                text="100 × 100",
                font=("Segoe UI", 9),
                fg=config.COLOR_TEXT_MUTED,
                bg=config.COLOR_BG_SOFT,
                width=11,
                height=4,
                cursor="hand2",
            )
            image_label.pack(padx=5, pady=(5, 2))

            image_path = config.SIGN_REFERENCE_IMAGES.get(sign_name)

            if image_path and os.path.exists(image_path):
                image = Image.open(image_path).convert("RGB")
                image = image.resize(
                    (62, 62),
                    Image.Resampling.LANCZOS,
                )
                photo = ImageTk.PhotoImage(image)
                self._guide_photos[sign_name] = photo
                image_label.configure(
                    image=photo,
                    text="",
                    width=70,
                    height=70,
                )

            title_label = tk.Label(
                card,
                text=sign_name.title(),
                font=("Segoe UI", 9, "bold"),
                fg=config.COLOR_TEXT_PRIMARY,
                bg=config.COLOR_BG_SOFT,
                cursor="hand2",
                wraplength=125,
                justify="center",
                anchor="center",
            )
            title_label.pack(fill="x", padx=4, pady=(2, 5))

            for widget in (card, image_label, title_label):
                widget.bind(
                    "<Button-1>",
                    lambda _event, sign=sign_name: self._open_video(sign),
                )

    def _build_right_column(self, parent):
        right = tk.Frame(
            parent,
            bg=config.COLOR_BG_DARK,
            width=config.RIGHT_PANEL_WIDTH,
        )
        right.grid(row=0, column=1, sticky="ns", padx=(12, 0))
        right.grid_propagate(False)
        right.pack_propagate(False)

        self._build_result_card(right)
        self._build_all_confidence_card(right)
        self._build_explanation_card(right)
        self._build_recent_card(right)

    # ------------------------------------------------------------------
    # Result card
    # ------------------------------------------------------------------

    def _build_result_card(self, parent):
        card = self._make_card(parent)
        card.pack(fill="x", pady=(0, 10))

        content = tk.Frame(card, bg=config.COLOR_PANEL)
        content.pack(fill="x", padx=22, pady=20)

        tk.Label(
            content,
            text="CURRENT RESULT",
            font=("Segoe UI", 10, "bold"),
            fg=config.COLOR_TEXT_MUTED,
            bg=config.COLOR_PANEL,
        ).pack(anchor="w")

        self.sign_text_label = tk.Label(
            content,
            text="—",
            font=("Segoe UI", 29, "bold"),
            fg=config.COLOR_ACCENT,
            bg=config.COLOR_PANEL,
            wraplength=310,
            justify="left",
        )
        self.sign_text_label.pack(anchor="w", pady=(8, 3))

        self.confirmation_label = tk.Label(
            content,
            text="Waiting for a hand",
            font=("Segoe UI", 10, "bold"),
            fg=config.COLOR_TEXT_MUTED,
            bg=config.COLOR_PANEL,
        )
        self.confirmation_label.pack(anchor="w", pady=(0, 16))

        confidence_row = tk.Frame(content, bg=config.COLOR_PANEL)
        confidence_row.pack(fill="x")

        tk.Label(
            confidence_row,
            text="Top confidence",
            font=("Segoe UI", 10),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_PANEL,
        ).pack(side="left")

        self.confidence_value_label = tk.Label(
            confidence_row,
            text="0%",
            font=("Segoe UI", 13, "bold"),
            fg=config.COLOR_TEXT_PRIMARY,
            bg=config.COLOR_PANEL,
        )
        self.confidence_value_label.pack(side="right")

        self.confidence_bar_bg = tk.Frame(
            content,
            bg=config.COLOR_PANEL_LIGHT,
            height=10,
        )
        self.confidence_bar_bg.pack(fill="x", pady=(8, 0))

        self.confidence_bar_fill = tk.Frame(
            self.confidence_bar_bg,
            bg=config.COLOR_ACCENT,
            height=10,
            width=0,
        )
        self.confidence_bar_fill.place(
            x=0,
            y=0,
            relheight=1,
            width=0,
        )

        dots_row = tk.Frame(content, bg=config.COLOR_PANEL)
        dots_row.pack(anchor="w", pady=(15, 0))

        tk.Label(
            dots_row,
            text="Confirmation",
            font=("Segoe UI", 10),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_PANEL,
        ).pack(side="left", padx=(0, 10))

        self.confirmation_dots = []

        for _ in range(config.REQUIRED_STABLE_PREDICTIONS):
            dot = tk.Label(
                dots_row,
                text="●",
                font=("Segoe UI", 12),
                fg=config.COLOR_BORDER,
                bg=config.COLOR_PANEL,
            )
            dot.pack(side="left", padx=2)
            self.confirmation_dots.append(dot)

    # ------------------------------------------------------------------
    # All class confidence
    # ------------------------------------------------------------------

    def _build_all_confidence_card(self, parent):
        card = self._make_card(parent)
        card.configure(height=245)
        card.pack(fill="x", pady=(0, 10))
        card.pack_propagate(False)

        content = tk.Frame(card, bg=config.COLOR_PANEL)
        content.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            content,
            text="CONFIDENCE BY SIGN",
            font=("Segoe UI", 10, "bold"),
            fg=config.COLOR_TEXT_MUTED,
            bg=config.COLOR_PANEL,
        ).pack(anchor="w", pady=(0, 10))

        ordered_labels = self._ordered_model_labels()

        for label in ordered_labels:
            row = tk.Frame(content, bg=config.COLOR_PANEL)
            row.pack(fill="x", pady=5)

            name_label = tk.Label(
                row,
                text=label.title(),
                font=("Segoe UI", 10),
                fg=config.COLOR_TEXT_PRIMARY,
                bg=config.COLOR_PANEL,
                width=14,
                anchor="w",
            )
            name_label.pack(side="left")

            bar_bg = tk.Frame(
                row,
                bg=config.COLOR_PANEL_LIGHT,
                height=9,
            )
            bar_bg.pack(
                side="left",
                fill="x",
                expand=True,
                padx=8,
            )

            bar_fill = tk.Frame(
                bar_bg,
                bg=config.COLOR_BORDER,
                height=9,
                width=0,
            )
            bar_fill.place(x=0, y=0, relheight=1, width=0)

            value_label = tk.Label(
                row,
                text="0%",
                font=("Segoe UI", 9, "bold"),
                fg=config.COLOR_TEXT_SECONDARY,
                bg=config.COLOR_PANEL,
                width=5,
                anchor="e",
            )
            value_label.pack(side="right")

            self._class_rows[self._normalise_label(label)] = {
                "bar_bg": bar_bg,
                "bar_fill": bar_fill,
                "value_label": value_label,
            }

    def _ordered_model_labels(self):
        wanted = [
            "MAAF",
            "HELLO",
            "TERIMA KASIH",
            "SAMA-SAMA",
            "JUMPA LAGI",
        ]

        actual_by_normalised = {
            self._normalise_label(label): label
            for label in self.labels
        }

        ordered = []

        for label in wanted:
            normalised = self._normalise_label(label)

            if normalised in actual_by_normalised:
                ordered.append(actual_by_normalised[normalised])

        for label in self.labels:
            if label not in ordered:
                ordered.append(label)

        return ordered

    def update_class_confidences(self, ranked):
        top_label = ranked[0][0] if ranked else None

        for label, score in ranked:
            row = self._class_rows.get(
                self._normalise_label(label)
            )

            if row is None:
                continue

            row["value_label"].configure(
                text=f"{score * 100:.0f}%"
            )

            is_top = label == top_label

            row["bar_fill"].configure(
                bg=(
                    config.COLOR_ACCENT
                    if is_top
                    else config.COLOR_BORDER
                )
            )

            self._set_bar_width(
                row["bar_bg"],
                row["bar_fill"],
                score,
            )

    def reset_class_confidences(self):
        for row in self._class_rows.values():
            row["value_label"].configure(text="0%")
            row["bar_fill"].configure(bg=config.COLOR_BORDER)
            self._set_bar_width(
                row["bar_bg"],
                row["bar_fill"],
                0,
            )


    # ------------------------------------------------------------------
    # Why this class was selected
    # ------------------------------------------------------------------

    def _build_explanation_card(self, parent):
        card = self._make_card(parent)
        card.configure(height=160)   # increase height
        card.pack(fill="x", pady=(0, 10))
        card.pack_propagate(False)

        content = tk.Frame(card, bg=config.COLOR_PANEL)
        content.pack(fill="both", expand=True, padx=16, pady=12)

        tk.Label(
            content,
            text="WHY THIS RESULT?",
            font=("Segoe UI", 10, "bold"),
            fg=config.COLOR_TEXT_MUTED,
            bg=config.COLOR_PANEL,
        ).pack(anchor="w")

        self.explanation_title_label = tk.Label(
            content,
            text="No prediction yet",
            font=("Segoe UI", 11, "bold"),
            fg=config.COLOR_TEXT_PRIMARY,
            bg=config.COLOR_PANEL,
        )
        self.explanation_title_label.pack(anchor="w", pady=(8, 4))

        self.explanation_body_label = tk.Label(
            content,
            text=(
                "The system will compare all sign classes and explain "
                "why the highest-scoring class was selected."
            ),
            font=("Segoe UI", 9),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_PANEL,
            justify="left",
            wraplength=310,
        )
        self.explanation_body_label.pack(anchor="w")

    def update_explanation(self, ranked, hand_detected=True):
        """
        Explain the decision using only model confidence scores.

        This intentionally avoids claiming exact physical causes such as
        finger angle or hand orientation because the current model output
        only provides class probabilities.
        """
        if not hand_detected:
            self.reset_explanation()
            return

        if not ranked:
            self.reset_explanation()
            return

        ordered = sorted(
            ranked,
            key=lambda item: item[1],
            reverse=True,
        )

        top_label, top_score = ordered[0]
        second_label, second_score = (
            ordered[1] if len(ordered) > 1 else ("Other classes", 0.0)
        )

        difference = max(top_score - second_score, 0.0)

        self.explanation_title_label.configure(
            text=f"Selected: {top_label.title()}",
            fg=config.COLOR_ACCENT,
        )

        if top_score < config.CONFIDENCE_THRESHOLD:
            explanation = (
                f"{top_label.title()} currently has the highest score "
                f"at {top_score * 100:.0f}%, but it has not reached the "
                f"{config.CONFIDENCE_THRESHOLD * 100:.0f}% confirmation "
                "threshold."
                " Why not the others? Their confidence scores are even lower, "
                "so none of the classes is reliable enough yet."
            )
        else:
            explanation = (
                f"{top_label.title()} was selected because it received the "
                f"highest confidence score at {top_score * 100:.0f}%."
                f" Why not {second_label.title()}? It scored "
                f"{second_score * 100:.0f}%, which is "
                f"{difference * 100:.0f} percentage points lower. "
                " The remaining classes also received lower confidence scores."
            )

        self.explanation_body_label.configure(text=explanation)

    def reset_explanation(self):
        if not hasattr(self, "explanation_title_label"):
            return

        self.explanation_title_label.configure(
            text="No prediction yet",
            fg=config.COLOR_TEXT_PRIMARY,
        )
        self.explanation_body_label.configure(
            text=(
                "Show a hand to the camera. The system will compare all "
                "sign classes and explain why the highest-scoring class "
                "was selected."
            )
        )

    # ------------------------------------------------------------------
    # Recent results
    # ------------------------------------------------------------------

    def _build_recent_card(self, parent):
        card = self._make_card(parent)
        card.pack(fill="x")

        content = tk.Frame(card, bg=config.COLOR_PANEL)
        content.pack(fill="x", padx=18, pady=14)

        tk.Label(
            content,
            text="RECENT RESULTS",
            font=("Segoe UI", 10, "bold"),
            fg=config.COLOR_TEXT_MUTED,
            bg=config.COLOR_PANEL,
        ).pack(anchor="w")

        self.recent_results_label = tk.Label(
            content,
            text="No confirmed signs yet",
            font=("Segoe UI", 10),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_PANEL,
            justify="left",
            wraplength=310,
        )
        self.recent_results_label.pack(anchor="w", pady=(7, 0))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_label(label):
        return (
            label.strip()
            .upper()
            .replace("_", " ")
            .replace("-", " ")
        )

    def _open_video(self, sign_name):
        url = config.SIGN_YOUTUBE_URLS.get(sign_name)

        if url:
            webbrowser.open_new_tab(url)

    @staticmethod
    def _make_card(parent):
        return tk.Frame(
            parent,
            bg=config.COLOR_PANEL,
            highlightthickness=1,
            highlightbackground=config.COLOR_BORDER,
        )

    @staticmethod
    def _make_button(parent, text, bg, hover_bg, fg, command):
        button = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=config.COLOR_TEXT_PRIMARY,
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
            command=command,
        )

        button.bind(
            "<Enter>",
            lambda _event: button.configure(bg=hover_bg),
        )
        button.bind(
            "<Leave>",
            lambda _event: button.configure(bg=bg),
        )

        return button

    # ------------------------------------------------------------------
    # Public update methods
    # ------------------------------------------------------------------

    def set_status(self, text, color=None):
        self.status_label.configure(
            text=text,
            fg=color or config.COLOR_TEXT_SECONDARY,
        )

    def update_video_frame(self, pil_image):
        self._video_photo = ImageTk.PhotoImage(pil_image)
        self.video_label.configure(
            image=self._video_photo,
            text="",
        )

    def show_camera_placeholder(self, text):
        self._video_photo = None
        self.video_label.configure(
            image="",
            text=text,
            fg=config.COLOR_TEXT_SECONDARY,
            font=("Segoe UI", 13),
        )

    def set_hand_state(self, hand_detected):
        if hand_detected:
            self.hand_badge.configure(
                text="● Hand detected",
                fg=config.COLOR_SUCCESS,
                bg=config.COLOR_PANEL_LIGHT,
            )
        else:
            self.hand_badge.configure(
                text="No hand detected",
                fg=config.COLOR_TEXT_PRIMARY,
                bg=config.COLOR_DANGER,
            )

    def show_no_hand(self):
        self.set_hand_state(False)
        self.sign_text_label.configure(
            text="—",
            fg=config.COLOR_ACCENT,
        )
        self.confidence_value_label.configure(text="0%")
        self.confirmation_label.configure(
            text="Waiting for a hand",
            fg=config.COLOR_TEXT_MUTED,
        )
        self._set_bar_width(
            self.confidence_bar_bg,
            self.confidence_bar_fill,
            0,
        )
        self._update_confirmation_dots(0)
        self.reset_class_confidences()
        self.reset_explanation()

    def show_checking_prediction(
        self,
        label,
        confidence,
        confirmation_count,
    ):
        self.set_hand_state(True)

        self.sign_text_label.configure(
            text=label,
            fg=config.COLOR_TEXT_PRIMARY,
        )
        self.confidence_value_label.configure(
            text=f"{confidence * 100:.0f}%"
        )
        self.confirmation_label.configure(
            text=(
                f"Checking… {confirmation_count}/"
                f"{config.REQUIRED_STABLE_PREDICTIONS}"
            ),
            fg=config.COLOR_WARNING,
        )
        self.confidence_bar_fill.configure(bg=config.COLOR_WARNING)
        self._set_bar_width(
            self.confidence_bar_bg,
            self.confidence_bar_fill,
            confidence,
        )
        self._update_confirmation_dots(confirmation_count)

    def show_low_confidence(self, confidence):
        self.set_hand_state(True)

        self.sign_text_label.configure(
            text="Not recognised",
            fg=config.COLOR_WARNING,
        )
        self.confidence_value_label.configure(
            text=f"{confidence * 100:.0f}%"
        )
        self.confirmation_label.configure(
            text="Try holding the sign more clearly",
            fg=config.COLOR_WARNING,
        )
        self.confidence_bar_fill.configure(bg=config.COLOR_WARNING)
        self._set_bar_width(
            self.confidence_bar_bg,
            self.confidence_bar_fill,
            confidence,
        )
        self._update_confirmation_dots(0)

    def show_confirmed_prediction(self, label, confidence):
        self.set_hand_state(True)

        self.sign_text_label.configure(
            text=label,
            fg=config.COLOR_ACCENT,
        )
        self.confidence_value_label.configure(
            text=f"{confidence * 100:.0f}%"
        )
        self.confirmation_label.configure(
            text="✓ Sign confirmed",
            fg=config.COLOR_SUCCESS,
        )
        self.confidence_bar_fill.configure(bg=config.COLOR_ACCENT)
        self._set_bar_width(
            self.confidence_bar_bg,
            self.confidence_bar_fill,
            confidence,
        )
        self._update_confirmation_dots(
            config.REQUIRED_STABLE_PREDICTIONS
        )
        self.add_recent_result(label)

    def add_recent_result(self, label):
        if self._recent_results and self._recent_results[-1] == label:
            return

        self._recent_results.append(label)

        self.recent_results_label.configure(
            text="  •  ".join(reversed(self._recent_results)),
            fg=config.COLOR_TEXT_PRIMARY,
        )

    def reset_detection(self):
        self._recent_results.clear()

        if hasattr(self, "recent_results_label"):
            self.recent_results_label.configure(
                text="No confirmed signs yet",
                fg=config.COLOR_TEXT_SECONDARY,
            )

        if hasattr(self, "status_label"):
            self.set_status(
                "● Camera is off",
                config.COLOR_TEXT_MUTED,
            )

        if hasattr(self, "show_camera_placeholder"):
            self.show_camera_placeholder(
                "Camera is off\n\nStart recognition from the main menu."
            )

        if hasattr(self, "show_no_hand"):
            self.show_no_hand()

        if hasattr(self, "reset_explanation"):
            self.reset_explanation()

    def _update_confirmation_dots(self, active_count):
        for index, dot in enumerate(self.confirmation_dots):
            dot.configure(
                fg=(
                    config.COLOR_ACCENT
                    if index < active_count
                    else config.COLOR_BORDER
                )
            )

    @staticmethod
    def _set_bar_width(bar_bg, bar_fill, fraction):
        bar_bg.update_idletasks()

        total_width = bar_bg.winfo_width() or 1
        fraction = max(0.0, min(1.0, fraction))

        bar_fill.place(
            x=0,
            y=0,
            relheight=1,
            width=int(total_width * fraction),
        )
