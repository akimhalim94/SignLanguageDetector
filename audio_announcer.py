"""
audio_announcer.py
Speaks the name of a detected sign out loud using pyttsx3 (an offline,
no-internet-required text-to-speech engine).

Speech runs on its own dedicated thread with a queue:
  - pyttsx3's engine.runAndWait() blocks until speech finishes, so it must
    never run on the camera thread (would stall frame capture) or the
    Tkinter main thread (would freeze the UI).
  - The queue is FIFO: if a new sign is detected while a previous word is
    still being spoken, it waits its turn instead of being silently
    dropped.
  - IMPORTANT: a brand-new pyttsx3.init() engine is created for *every*
    utterance instead of reusing one engine across the whole app. Reusing
    a single engine across multiple say()/runAndWait() cycles is known to
    silently stop working after the first utterance on some platforms
    (this is a long-standing pyttsx3 issue, most commonly seen with the
    Windows SAPI5 driver). Creating a fresh engine each time costs a small
    amount of extra startup time per announcement but is far more
    reliable across Windows/macOS/Linux.
"""

import queue
import threading

import config


class AudioAnnouncer:
    # Cap how many pending words we'll let pile up. If the camera produces
    # changes faster than speech can keep up for a long stretch, we drop
    # the *oldest* backlog rather than grow unbounded or freeze the UI
    # with minutes of catch-up speech.
    MAX_QUEUE_SIZE = 5

    def __init__(self, rate=None, volume=None):
        self._rate = rate if rate is not None else config.TTS_RATE
        self._volume = volume if volume is not None else config.TTS_VOLUME

        self._queue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self._stop_event = threading.Event()
        self._thread = None
        self._init_error = None
        self._pyttsx3_available = None  # set on first use

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        # Wake the thread up if it's blocked waiting on the queue.
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        if self._thread:
            self._thread.join(timeout=2.0)

    def announce(self, text):
        """Queues `text` to be spoken, in order. If the queue is full
        (speech is badly backlogged), the oldest pending word is dropped
        to make room, so we favor staying close to "live" over speaking
        every single sign that ever appeared."""
        try:
            self._queue.put_nowait(text)
        except queue.Full:
            try:
                self._queue.get_nowait()  # drop the oldest pending word
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(text)
            except queue.Full:
                pass

    @property
    def last_error(self):
        return self._init_error

    def _run(self):
        # Verify pyttsx3 itself imports and can construct an engine at
        # least once, so we can report a clear error early if e.g.
        # espeak-ng is missing on Linux. We don't keep this engine around
        # for actual speaking (see module docstring).
        try:
            import pyttsx3

            probe_engine = pyttsx3.init()
            probe_engine.stop()
        except Exception as exc:  # noqa: BLE001
            self._init_error = str(exc)
            return

        while not self._stop_event.is_set():
            text = self._queue.get()  # blocks until something is queued
            if text is None or self._stop_event.is_set():
                break
            self._speak_once(text)

    def _speak_once(self, text):
        """Creates a fresh engine, speaks one utterance, and tears the
        engine down again. See module docstring for why this is
        necessary instead of reusing one long-lived engine."""
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
            engine.say(text)
            engine.runAndWait()
            try:
                engine.stop()
            except Exception:  # noqa: BLE001
                pass
        except Exception as exc:  # noqa: BLE001
            self._init_error = str(exc)
