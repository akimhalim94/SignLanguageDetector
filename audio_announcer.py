"""
audio_announcer.py
Stable pyttsx3 announcer for real-time sign detection.
Fix: creates fresh engine per speech (prevents Windows freeze bug)
"""

import queue
import threading
import config


class AudioAnnouncer:
    MAX_QUEUE_SIZE = 5

    def __init__(self, rate=None, volume=None):
        self._rate = rate if rate is not None else config.TTS_RATE
        self._volume = volume if volume is not None else config.TTS_VOLUME

        self._queue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)

        self._stop_event = threading.Event()
        self._thread = None

        self._init_error = None

    # ---------------- START ----------------
    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ---------------- STOP ----------------
    def stop(self):
        self._stop_event.set()

        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass

        if self._thread:
            self._thread.join(timeout=2.0)

    # ---------------- ANNOUNCE ----------------
    def announce(self, text):
        if not text:
            return

        try:
            self._queue.put_nowait(text)

        except queue.Full:
            # flush old items, keep only latest
            try:
                while not self._queue.empty():
                    self._queue.get_nowait()
            except:
                pass

            try:
                self._queue.put_nowait(text)
            except:
                pass

    # ---------------- WORKER THREAD ----------------
    def _run(self):
        import pyttsx3

        while not self._stop_event.is_set():
            try:
                text = self._queue.get(timeout=1)
            except queue.Empty:
                continue

            if text is None:
                break

            print("QUEUE:", text)
            self._speak_once(text)

    # ---------------- SPEAK ----------------
    def _speak_once(self, text):
        try:
            print("SPEAKING:", text)

            import pyttsx3

            # 🔥 IMPORTANT: fresh engine every speech (fix Windows bug)
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)

            engine.say(text)
            engine.runAndWait()

            try:
                engine.stop()
            except:
                pass

        except Exception as exc:
            self._init_error = str(exc)

    # ---------------- DEBUG ----------------
    @property
    def last_error(self):
        return self._init_error