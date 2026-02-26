"""JSONL interaction logger for dataset collection."""

import json
import os
import threading
import uuid
from datetime import datetime, timezone

from .config import load_config

_lock = threading.Lock()


def _get_log_path() -> str:
    cfg = load_config()
    log_dir = cfg["log_dir"]
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "interactions.jsonl")
    # Rotate if file exceeds max size
    if os.path.exists(path) and os.path.getsize(path) > cfg["log_max_bytes"]:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated = os.path.join(log_dir, f"interactions_{ts}.jsonl")
        os.rename(path, rotated)
    return path


def log_command(
    transcription: str,
    detected_language: str,
    audio_duration_sec: float,
    whisper_model: str,
    ollama_model: str,
    generated_command: str,
    user_action: str,
    edited_command: str | None,
    execution_output: str | None,
    execution_exit_code: int | None,
    latency_stt_ms: int,
    latency_llm_ms: int,
) -> None:
    """Log a command-mode interaction."""
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "mode": "command",
        "audio_duration_sec": audio_duration_sec,
        "whisper_model": whisper_model,
        "transcription": transcription,
        "detected_language": detected_language,
        "ollama_model": ollama_model,
        "generated_command": generated_command,
        "user_action": user_action,
        "edited_command": edited_command,
        "execution_output": execution_output,
        "execution_exit_code": execution_exit_code,
        "latency_stt_ms": latency_stt_ms,
        "latency_llm_ms": latency_llm_ms,
    }
    _write(entry)


def log_text(
    transcription: str,
    detected_language: str,
    audio_duration_sec: float,
    whisper_model: str,
    latency_stt_ms: int,
) -> None:
    """Log a text-mode interaction."""
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "mode": "text",
        "audio_duration_sec": audio_duration_sec,
        "whisper_model": whisper_model,
        "transcription": transcription,
        "detected_language": detected_language,
        "latency_stt_ms": latency_stt_ms,
    }
    _write(entry)


def _write(entry: dict) -> None:
    path = _get_log_path()
    with _lock:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
