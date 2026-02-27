"""HTTP server exposing faster-whisper as a Whisper ASR Webservice-compatible API."""

import logging
import os
import tempfile
import threading

from flask import Flask, request, jsonify, Response

from .transcriber import transcribe_file
from .config import load_config
from .logger import log_text

log = logging.getLogger("voice_commander.http")

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    cfg = load_config()
    return jsonify({
        "status": "ok",
        "model": cfg["whisper_model"],
        "device": cfg["whisper_device"],
        "compute_type": cfg["whisper_compute_type"],
    })


@app.route("/asr", methods=["POST"])
def asr():
    """Whisper ASR Webservice-compatible endpoint.

    The Android app sends:
      POST /asr?encode=true&task=transcribe&language=es&word_timestamps=false&output=txt
      Content-Type: multipart/form-data
      Field: audio_file (M4A or OGG)

    Returns: plain text transcription.
    """
    language = request.args.get("language", None)
    task = request.args.get("task", "transcribe")
    output_format = request.args.get("output", "txt")

    audio_file = request.files.get("audio_file")
    if audio_file is None:
        return Response("No audio_file field in request", status=400)

    suffix = _guess_suffix(audio_file.filename or "audio.m4a")
    tmp_dir = _get_tmp_dir()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=tmp_dir) as tmp:
        audio_file.save(tmp)
        tmp_path = tmp.name

    try:
        result = transcribe_file(tmp_path, language=language, task=task)
    finally:
        _safe_delete(tmp_path)

    cfg = load_config()
    log_text(
        transcription=result.text,
        detected_language=result.language,
        audio_duration_sec=result.audio_duration_sec,
        whisper_model=cfg["whisper_model"],
        latency_stt_ms=result.latency_ms,
    )

    log.info(
        "[asr] %s (%s, %.1fs audio, %dms)",
        result.text[:80],
        result.language,
        result.audio_duration_sec,
        result.latency_ms,
    )

    if output_format == "json":
        return jsonify({
            "text": result.text,
            "language": result.language,
            "audio_duration_sec": result.audio_duration_sec,
            "latency_ms": result.latency_ms,
        })

    return Response(result.text, mimetype="text/plain")


# ── Helpers ────────────────────────────────────────────────────


def _guess_suffix(filename: str) -> str:
    if "." in filename:
        return "." + filename.rsplit(".", 1)[-1]
    return ".m4a"


def _get_tmp_dir() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tmp_dir = os.path.join(base, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir


def _safe_delete(path: str):
    try:
        os.unlink(path)
    except OSError:
        pass


def start_server(cfg: dict) -> threading.Thread:
    """Start the Flask HTTP server in a daemon thread."""
    host = cfg.get("http_host", "0.0.0.0")
    port = cfg.get("http_port", 9090)
    max_mb = cfg.get("http_max_content_mb", 25)

    app.config["MAX_CONTENT_LENGTH"] = max_mb * 1024 * 1024

    # Suppress Flask/Werkzeug startup banner and per-request logs
    werkzeug_log = logging.getLogger("werkzeug")
    werkzeug_log.setLevel(logging.WARNING)

    def _run():
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

    thread = threading.Thread(target=_run, daemon=True, name="http-server")
    thread.start()
    return thread
