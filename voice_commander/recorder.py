"""Audio recording with push-to-talk hotkeys."""

import threading
from dataclasses import dataclass

import keyboard
import numpy as np
import sounddevice as sd

from .config import load_config


@dataclass
class Recording:
    audio: np.ndarray
    mode: str  # "command" or "text"
    sample_rate: int


class Recorder:
    """Push-to-talk audio recorder with dual hotkeys."""

    def __init__(self):
        cfg = load_config()
        self.sample_rate = cfg["sample_rate"]
        self.channels = cfg["channels"]
        self.hotkey_command = cfg["hotkey_command"]
        self.hotkey_text = cfg["hotkey_text"]

        self._buffer: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording = False
        self._current_mode: str | None = None
        self._result_event = threading.Event()
        self._result: Recording | None = None

    def _audio_callback(self, indata, frames, time_info, status):
        if self._recording:
            self._buffer.append(indata.copy())

    def _start_recording(self, mode: str):
        if self._recording:
            return
        self._current_mode = mode
        self._buffer.clear()
        self._recording = True

    def _stop_recording(self):
        if not self._recording:
            return
        self._recording = False
        if self._buffer:
            audio = np.concatenate(self._buffer, axis=0).flatten()
        else:
            audio = np.array([], dtype=np.float32)
        self._result = Recording(
            audio=audio,
            mode=self._current_mode,
            sample_rate=self.sample_rate,
        )
        self._result_event.set()

    def wait_for_recording(self) -> Recording:
        """Block until a hotkey press-and-release cycle completes.

        Returns:
            Recording with audio data, mode, and sample rate.
        """
        self._result_event.clear()
        self._result = None

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()

        keyboard.on_press_key(
            self.hotkey_command.split("+")[-1],
            lambda e: self._start_recording("command")
            if keyboard.is_pressed(self.hotkey_command) else None,
            suppress=False,
        )
        keyboard.on_press_key(
            self.hotkey_text.split("+")[-1],
            lambda e: self._start_recording("text")
            if keyboard.is_pressed(self.hotkey_text) else None,
            suppress=False,
        )
        keyboard.on_release_key(
            self.hotkey_command.split("+")[-1],
            lambda e: self._stop_recording() if self._current_mode == "command" else None,
            suppress=False,
        )
        keyboard.on_release_key(
            self.hotkey_text.split("+")[-1],
            lambda e: self._stop_recording() if self._current_mode == "text" else None,
            suppress=False,
        )

        self._result_event.wait()

        keyboard.unhook_all()
        self._stream.stop()
        self._stream.close()
        self._stream = None

        return self._result
