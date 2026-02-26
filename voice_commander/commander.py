"""Command generation via Ollama LLM."""

import re
import time
from dataclasses import dataclass

import requests

from .config import load_config


@dataclass
class CommandResult:
    command: str
    model: str
    latency_ms: int


def _clean_command(raw: str) -> str:
    """Strip markdown fences, backticks, and excess whitespace from LLM output."""
    text = raw.strip()
    # Remove ```lang ... ``` blocks
    text = re.sub(r"^```\w*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    # Remove inline backticks
    text = text.strip("`").strip()
    return text


def generate_command(transcription: str) -> CommandResult:
    """Send transcription to Ollama and return the generated command.

    Args:
        transcription: the user's spoken text transcribed by Whisper.

    Returns:
        CommandResult with the cleaned command, model name, and latency.
    """
    cfg = load_config()
    url = f"{cfg['ollama_url']}/api/generate"
    payload = {
        "model": cfg["ollama_model"],
        "system": cfg["ollama_system_prompt"],
        "prompt": transcription,
        "stream": False,
    }

    t0 = time.perf_counter()
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
    except requests.ConnectionError:
        raise RuntimeError(
            "No se pudo conectar a Ollama. Asegurate de que este corriendo: ollama serve"
        )
    except requests.HTTPError as e:
        raise RuntimeError(f"Ollama error: {e}")
    latency_ms = int((time.perf_counter() - t0) * 1000)

    raw = resp.json().get("response", "")
    return CommandResult(
        command=_clean_command(raw),
        model=cfg["ollama_model"],
        latency_ms=latency_ms,
    )
