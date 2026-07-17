"""
landing_page.py
Modern landing screen for the sign-language recognizer.
"""

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFilter

import config


def _rounded_rect_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1],
        radius=radius,
        fill=255,
    )
    return mask


class LandingPage(tk.Frame):
    CARD_W = 570
    CARD_H = 450
    CARD_RADIUS = 34

    def __init__(self, master, on_start, on_quit):
        super().__init__(master, bg=config.COLOR_BG_DARK)

        self.on_start = on_start
        self.on_quit = on_quit

        self._bg_image_raw = Image.open(
            config.BACKGROUND_IMAGE_PATH
        ).convert("RGB")

        self._bg_photo = None
        self._card_photo = None
        self._card_bounds = (0, 0, 0, 0)

        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bd=0,
            bg=config.COLOR_BG_DARK,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

        self._bg_item = None
        self._card_item = None

        self._build_overlay_widgets()

    def _on_resize(self, event):
        width = max(event.width, 1)
        height = max(event.height, 1)

        resized = self._bg_image_raw.resize(
            (width, height),
            Image.Resampling.LANCZOS,
        )
        self._bg_photo = ImageTk.PhotoImage(resized)

        if self._bg_item is None:
            self._bg_item = self.canvas.create_image(
                0,
                0,
                image=self._bg_photo,
                anchor="nw",
            )
        else:
            self.canvas.itemconfigure(
                self._bg_item,
                image=self._bg_photo,
            )

        self.canvas.coords(self._bg_item, 0, 0)
        self.canvas.tag_lower(self._bg_item)

        self._render_card(resized, width, height)
        self.canvas.coords(
            self._overlay_window,
            width / 2,
            height * 0.49,
        )

    def _render_card(self, background, width, height):
        card_width = min(self.CARD_W, max(width - 50, 1))
        card_height = min(self.CARD_H, max(height - 50, 1))

        center_x = width // 2
        center_y = int(height * 0.49)

        left = max(center_x - card_width // 2, 0)
        top = max(center_y - card_height // 2, 0)
        right = min(left + card_width, width)
        bottom = min(top + card_height, height)

        crop = background.crop((left, top, right, bottom))
        crop = crop.filter(ImageFilter.GaussianBlur(22))

        dark_overlay = Image.new(
            "RGB",
            crop.size,
            (7, 20, 38),
        )
        crop = Image.blend(crop, dark_overlay, 0.62)

        mask = _rounded_rect_mask(
            crop.size,
            self.CARD_RADIUS,
        )

        card = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        card.paste(crop, (0, 0), mask)

        border = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border)
        border_draw.rounded_rectangle(
            [1, 1, crop.size[0] - 2, crop.size[1] - 2],
            radius=self.CARD_RADIUS,
            outline=(90, 130, 160, 75),
            width=2,
        )
        card = Image.alpha_composite(card, border)

        self._card_photo = ImageTk.PhotoImage(card)

        if self._card_item is None:
            self._card_item = self.canvas.create_image(
                left,
                top,
                image=self._card_photo,
                anchor="nw",
            )
        else:
            self.canvas.itemconfigure(
                self._card_item,
                image=self._card_photo,
            )
            self.canvas.coords(self._card_item, left, top)

        self.canvas.tag_raise(self._card_item, self._bg_item)
        self.canvas.tag_raise("overlay")

    def _build_overlay_widgets(self):
        # Tkinter widgets cannot be truly transparent, so use one matching
        # panel colour instead of placing a second visible rectangle.
        overlay = tk.Frame(
            self.canvas,
            bg=config.COLOR_PANEL,
            padx=44,
            pady=32,
        )

        self._overlay = overlay
        self._overlay_window = self.canvas.create_window(
            0,
            0,
            window=overlay,
            anchor="center",
            tags="overlay",
        )

        icon_circle = tk.Label(
            overlay,
            text="🤟",
            font=("Segoe UI Emoji", 38),
            fg=config.COLOR_TEXT_PRIMARY,
            bg=config.COLOR_PANEL_LIGHT,
            width=3,
            height=1,
        )
        icon_circle.pack(pady=(0, 18))

        title = tk.Label(
            overlay,
            text="Sign Language Recognizer",
            font=("Segoe UI", 27, "bold"),
            fg=config.COLOR_TEXT_PRIMARY,
            bg=config.COLOR_PANEL,
        )
        title.pack()

        subtitle = tk.Label(
            overlay,
            text=(
                "Recognise common Malaysian sign-language gestures\n"
                "in real time using your camera."
            ),
            font=("Segoe UI", 12),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_PANEL,
            justify="center",
        )
        subtitle.pack(pady=(10, 28))

        self.start_btn = self._make_button(
            overlay,
            text="Start Recognition  →",
            bg=config.COLOR_ACCENT,
            hover_bg=config.COLOR_ACCENT_HOVER,
            fg="#06251F",
            command=self.on_start,
            width=24,
        )
        self.start_btn.pack()

        privacy_label = tk.Label(
            overlay,
            text="● Camera processing stays on this device",
            font=("Segoe UI", 10),
            fg=config.COLOR_TEXT_MUTED,
            bg=config.COLOR_PANEL,
        )
        privacy_label.pack(pady=(22, 4))

        exit_btn = tk.Button(
            overlay,
            text="Exit application",
            font=("Segoe UI", 10, "underline"),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_PANEL,
            activeforeground=config.COLOR_TEXT_PRIMARY,
            activebackground=config.COLOR_PANEL,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.on_quit,
        )
        exit_btn.pack(pady=(6, 0))

    @staticmethod
    def _make_button(parent, text, bg, hover_bg, fg, command, width):
        button = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 13, "bold"),
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            width=width,
            padx=18,
            pady=14,
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
