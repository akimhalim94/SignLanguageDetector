"""
audio_announcer.py

Plays a separate MP3 file for each confirmed sign.
"""

import os
import queue
import threading

import pygame

import config


class AudioAnnouncer:
    MAX_QUEUE_SIZE = 3

    def __init__(self):
        self._queue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self._stop_event = threading.Event()
        self._thread = None
        self._last_queued_label = None
        self._last_error = None
        self._lock = threading.Lock()

        try:
            pygame.mixer.init()
        except pygame.error as error:
            self._last_error = str(error)

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self.clear()

        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass

        if self._thread:
            self._thread.join(timeout=2.0)

        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except pygame.error:
            pass

    def clear(self):
        """Remove MP3 files that have not started playing."""
        with self._lock:
            while True:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

            self._last_queued_label = None

        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def announce(self, label):
        label = str(label).strip().upper()

        if not label:
            return

        audio_path = config.SIGN_AUDIO_PATHS.get(label)

        if not audio_path:
            self._last_error = f"No audio path configured for: {label}"
            return

        if not os.path.exists(audio_path):
            self._last_error = f"Audio file was not found: {audio_path}"
            return

        with self._lock:
            if label == self._last_queued_label:
                return

            self._last_queued_label = label

            try:
                self._queue.put_nowait((label, audio_path))

            except queue.Full:
                self.clear()

                try:
                    self._queue.put_nowait((label, audio_path))
                except queue.Full:
                    self._last_queued_label = None

    def _run(self):
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if item is None:
                break

            label, audio_path = item
            self._play_audio(audio_path)

            with self._lock:
                if self._last_queued_label == label:
                    self._last_queued_label = None

    def _play_audio(self, audio_path):
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()

            while (
                pygame.mixer.music.get_busy()
                and not self._stop_event.is_set()
            ):
                pygame.time.wait(50)

        except pygame.error as error:
            self._last_error = str(error)

    @property
    def last_error(self):
        return self._last_error
    
    
# import queue
# import threading
# import config


# class AudioAnnouncer:
#     MAX_QUEUE_SIZE = 3

#     def __init__(self, rate=None, volume=None):
#         self._rate = rate if rate is not None else config.TTS_RATE
#         self._volume = volume if volume is not None else config.TTS_VOLUME

#         self._queue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)
#         self._stop_event = threading.Event()
#         self._thread = None
#         self._init_error = None

#         self._last_queued_text = None
#         self._lock = threading.Lock()

#     def start(self):
#         if self._thread and self._thread.is_alive():
#             return

#         self._stop_event.clear()
#         self._thread = threading.Thread(target=self._run, daemon=True)
#         self._thread.start()

#     def stop(self):
#         self._stop_event.set()
#         self.clear()

#         try:
#             self._queue.put_nowait(None)
#         except queue.Full:
#             pass

#         if self._thread:
#             self._thread.join(timeout=2.0)

#     def clear(self):
#         with self._lock:
#             while True:
#                 try:
#                     self._queue.get_nowait()
#                 except queue.Empty:
#                     break

#             self._last_queued_text = None

#     def announce(self, text):
#         text = str(text).strip()

#         if not text:
#             return

#         with self._lock:
#             if text == self._last_queued_text:
#                 return

#             self._last_queued_text = text

#             try:
#                 self._queue.put_nowait(text)

#             except queue.Full:
#                 while True:
#                     try:
#                         self._queue.get_nowait()
#                     except queue.Empty:
#                         break

#                 try:
#                     self._queue.put_nowait(text)
#                 except queue.Full:
#                     self._last_queued_text = None

#     def _run(self):
#         while not self._stop_event.is_set():
#             try:
#                 text = self._queue.get(timeout=1.0)
#             except queue.Empty:
#                 continue

#             if text is None:
#                 break

#             self._speak_once(text)

#             with self._lock:
#                 if self._last_queued_text == text:
#                     self._last_queued_text = None

#     def _speak_once(self, text):
#         try:
#             import pyttsx3

#             engine = pyttsx3.init()
#             engine.setProperty("rate", self._rate)
#             engine.setProperty("volume", self._volume)
#             engine.say(text)
#             engine.runAndWait()

#             try:
#                 engine.stop()
#             except Exception:
#                 pass

#         except Exception as error:
#             self._init_error = str(error)

#     @property
#     def last_error(self):
#         return self._init_error
