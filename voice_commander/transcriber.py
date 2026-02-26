"""Speech-to-text using faster-whisper."""

import sys
import threading
import time
from dataclasses import dataclass

import numpy as np
from faster_whisper import WhisperModel

from .config import load_config


@dataclass
class TranscriptionResult:
    text: str
    language: str
    audio_duration_sec: float
    latency_ms: int


_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        cfg = load_config()
        _model = WhisperModel(
            cfg["whisper_model"],
            device=cfg["whisper_device"],
            compute_type=cfg["whisper_compute_type"],
        )
    return _model


_is_tty = hasattr(sys.stdout, "buffer") and hasattr(sys.stdout.buffer, "isatty") and sys.stdout.buffer.isatty()


def spinner(message: str, stop_event: threading.Event):
    """Display a spinner animation. Falls back to static line when piped."""
    if not _is_tty:
        sys.stdout.write(f"  ~ {message}\n")
        sys.stdout.flush()
        stop_event.wait()
        return
    frames = ["|", "/", "-", "\\"]
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r  {frames[i % len(frames)]} {message}")
        sys.stdout.flush()
        i += 1
        stop_event.wait(0.12)


def warmup() -> None:
    """Pre-load the Whisper model with a spinner animation."""
    if _model is not None:
        return
    stop = threading.Event()
    cfg = load_config()
    t = threading.Thread(target=spinner, args=(f"Loading {cfg['whisper_model']} model...", stop), daemon=True)
    t.start()
    t0 = time.perf_counter()
    _get_model()
    elapsed = time.perf_counter() - t0
    stop.set()
    t.join()
    if _is_tty:
        sys.stdout.write(f"\r  * Model loaded ({elapsed:.1f}s)              \n")
    else:
        sys.stdout.write(f"  * Model loaded ({elapsed:.1f}s)\n")
    sys.stdout.flush()


def transcribe(audio: np.ndarray, sample_rate: int = 16000) -> TranscriptionResult:
    """Transcribe audio buffer to text."""
    cfg = load_config()
    model = _get_model()
    audio_duration = len(audio) / sample_rate

    t0 = time.perf_counter()
    segments, info = model.transcribe(
        audio,
        language=None,
        initial_prompt=cfg["whisper_initial_prompt"],
        vad_filter=True,
    )
    text = " ".join(seg.text.strip() for seg in segments)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    return TranscriptionResult(
        text=text.strip(),
        language=info.language,
        audio_duration_sec=round(audio_duration, 2),
        latency_ms=latency_ms,
    )
