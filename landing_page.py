"""
landing_page.py
The first screen the user sees: a full-window background image with a
title and two buttons - "Start Camera" and "End Program".
"""

import tkinter as tk

from PIL import Image, ImageTk, ImageDraw, ImageFilter

import config


def _rounded_rect_mask(size, radius):
    """Returns an 'L' mode mask image with rounded corners, used to crop
    a blurred background crop into a soft glass-panel shape."""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return mask


class LandingPage(tk.Frame):
    CARD_W = 620
    CARD_H = 430
    CARD_RADIUS = 28

    def __init__(self, master, on_start, on_quit):
        super().__init__(master, bg=config.COLOR_BG_DARK)
        self.on_start = on_start
        self.on_quit = on_quit

        self._bg_image_raw = Image.open(config.BACKGROUND_IMAGE_PATH).convert("RGB")
        self._bg_photo = None
        self._card_photo = None

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

        self._bg_item = None
        self._card_item = None
        self._build_overlay_widgets()

    # -- background + glass card rendering -----------------------------------

    def _on_resize(self, event):
        width, height = max(event.width, 1), max(event.height, 1)
        resized = self._bg_image_raw.resize((width, height), Image.LANCZOS)
        self._bg_photo = ImageTk.PhotoImage(resized)

        if self._bg_item is None:
            self._bg_item = self.canvas.create_image(0, 0, image=self._bg_photo, anchor="nw")
        else:
            self.canvas.itemconfig(self._bg_item, image=self._bg_photo)
            self.canvas.coords(self._bg_item, 0, 0)
        self.canvas.tag_lower(self._bg_item)

        self._render_glass_card(resized, width, height)
        self._reposition_overlay_to_center(width, height)

    def _render_glass_card(self, full_bg_image, width, height):
        """Crops the region behind where the card sits, blurs + darkens it,
        and composites a rounded-corner 'frosted glass' panel."""
        cw, ch = min(self.CARD_W, width - 40), min(self.CARD_H, height - 40)
        cx, cy = width // 2, int(height * 0.46)
        left, top = cx - cw // 2, cy - ch // 2
        left, top = max(left, 0), max(top, 0)
        right, bottom = min(left + cw, width), min(top + ch, height)

        crop = full_bg_image.crop((left, top, right, bottom))
        crop = crop.filter(ImageFilter.GaussianBlur(18))

        # darken for contrast with white text
        overlay = Image.new("RGB", crop.size, (5, 14, 26))
        crop = Image.blend(crop, overlay, alpha=0.55)

        mask = _rounded_rect_mask(crop.size, self.CARD_RADIUS)
        glass = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        glass.paste(crop, (0, 0), mask)

        self._card_photo = ImageTk.PhotoImage(glass)
        if self._card_item is None:
            self._card_item = self.canvas.create_image(
                left, top, image=self._card_photo, anchor="nw"
            )
        else:
            self.canvas.itemconfig(self._card_item, image=self._card_photo)
            self.canvas.coords(self._card_item, left, top)
        self.canvas.tag_raise(self._card_item, self._bg_item)
        self.canvas.tag_raise("overlay")

        self._card_bounds = (left, top, right, bottom)

    # -- overlay content -------------------------------------------------------

    def _build_overlay_widgets(self):
        overlay = tk.Frame(self.canvas, bg=config.COLOR_BG_DARK)
        overlay.configure(highlightthickness=0)

        self._overlay_window = self.canvas.create_window(
            0, 0, window=overlay, anchor="center", tags="overlay"
        )
        self._overlay = overlay

        icon = tk.Label(
            overlay, text="\U0001F91F", font=("Segoe UI Emoji", 50), bg=config.COLOR_BG_DARK
        )
        icon.pack(pady=(0, 6))

        title = tk.Label(
            overlay,
            text="Sign Language Detector",
            font=("Segoe UI", 30, "bold"),
            fg=config.COLOR_TEXT_PRIMARY,
            bg=config.COLOR_BG_DARK,
        )
        title.pack()

        subtitle = tk.Label(
            overlay,
            text="Real-time sign recognition powered by your trained model",
            font=("Segoe UI", 13),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_BG_DARK,
        )
        subtitle.pack(pady=(6, 32))

        button_row = tk.Frame(overlay, bg=config.COLOR_BG_DARK)
        button_row.pack()

        self.start_btn = self._make_button(
            button_row,
            text="\u25B6   Start Camera",
            bg=config.COLOR_ACCENT,
            hover_bg=config.COLOR_ACCENT_HOVER,
            fg="#06251F",
            command=self.on_start,
        )
        self.start_btn.pack(side="left", padx=10)

        self.quit_btn = self._make_button(
            button_row,
            text="\u25A0   End Program",
            bg=config.COLOR_DANGER,
            hover_bg=config.COLOR_DANGER_HOVER,
            fg="#2B0B0B",
            command=self.on_quit,
        )
        self.quit_btn.pack(side="left", padx=10)

        footer = tk.Label(
            overlay,
            text="Tip: make sure your hands are well-lit and centered in frame.",
            font=("Segoe UI", 10),
            fg=config.COLOR_TEXT_SECONDARY,
            bg=config.COLOR_BG_DARK,
        )
        footer.pack(pady=(26, 0))

        for w in (overlay, icon, title, subtitle, button_row, footer):
            w.configure(bg=config.COLOR_BG_DARK)
            try:
                w.lower()
            except Exception:
                pass

    def _reposition_overlay_to_center(self, width, height):
        self.canvas.coords(self._overlay_window, width / 2, height * 0.46)

    def _make_button(self, parent, text, bg, hover_bg, fg, command):
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 13, "bold"),
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=26,
            pady=14,
            cursor="hand2",
            command=command,
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        return btn

