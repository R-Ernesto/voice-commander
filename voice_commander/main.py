"""Voice Commander - Entry point and CLI orchestrator."""

import io
import os
import sys
import threading
from datetime import datetime

import pyperclip
from colorama import Fore, Style, init as colorama_init

from .recorder import Recorder
from .transcriber import transcribe, warmup, spinner
from .commander import generate_command
from .executor import run_command
from .logger import log_command, log_text
from .config import load_config

# ── UI helpers ──────────────────────────────────────────────────

DIM = Style.DIM
R = Style.RESET_ALL
B = Style.BRIGHT
CYN = Fore.CYAN
GRN = Fore.GREEN
YLW = Fore.YELLOW
RED = Fore.RED
WHT = Fore.WHITE
MAG = Fore.MAGENTA


def _dim(text: str) -> str:
    return f"{DIM}{text}{R}"


def _replace_line(text: str):
    """Overwrite spinner line on TTY, or just print on pipe."""
    from .transcriber import _is_tty
    if _is_tty:
        sys.stdout.write(f"\r{text}{'  ' * 10}\n")
    else:
        sys.stdout.write(f"{text}\n")
    sys.stdout.flush()


def _clear_line():
    from .transcriber import _is_tty
    if _is_tty:
        sys.stdout.write(f"\r{'  ' * 30}\r")
        sys.stdout.flush()


def _print_banner(cfg: dict):
    w = 52
    print()
    print(f"{CYN}{'~' * w}{R}")
    print(f"{CYN}  * Voice Commander{R}  {DIM}v0.1.0{R}")
    print(f"{CYN}{'~' * w}{R}")
    print()
    print(f"  {DIM}STT{R}  {cfg['whisper_model']}  {DIM}(faster-whisper){R}")
    print(f"  {DIM}LLM{R}  {cfg['ollama_model']}  {DIM}(Ollama){R}")
    if cfg.get("http_enabled"):
        print(f"  {DIM}HTTP{R} :{cfg['http_port']}  {DIM}(remote STT){R}")
    print()
    print(f"  {B}Ctrl+Alt+V{R}  {DIM}comando{R}   voz -> terminal")
    print(f"  {B}Ctrl+Alt+T{R}  {DIM}texto{R}     voz -> clipboard")
    print(f"  {B}Ctrl+C{R}      {DIM}salir{R}")
    print()


def _waiting():
    print(f"\n{CYN}  >{R} {DIM}Esperando...{R}  {DIM}(manten hotkey mientras hablas){R}\n")


def _section(label: str):
    print(f"\n{DIM}{'- ' * 26}{R}")
    print(f"  {CYN}{label}{R}")


# ── Command mode ────────────────────────────────────────────────

def _handle_command_mode(rec):
    """Process a command-mode recording: transcribe -> LLM -> CLI menu."""
    _section("Modo Comando")

    # STT
    stop = threading.Event()
    t = threading.Thread(target=spinner, args=("Transcribiendo...", stop), daemon=True)
    t.start()
    stt = transcribe(rec.audio, rec.sample_rate)
    stop.set()
    t.join()

    if not stt.text:
        _replace_line(f"  {RED}! No se detecto voz.{R}")
        return

    _replace_line(f"  {GRN}*{R} {B}{stt.text}{R}")
    print(f"    {DIM}{stt.language} | {stt.latency_ms}ms | {stt.audio_duration_sec}s audio{R}")

    # LLM
    stop = threading.Event()
    t = threading.Thread(target=spinner, args=("Generando comando...", stop), daemon=True)
    t.start()
    try:
        cmd = generate_command(stt.text)
    except RuntimeError as e:
        stop.set()
        t.join()
        _replace_line(f"  {RED}! {e}{R}")
        return
    stop.set()
    t.join()

    # Show command
    _clear_line()
    print(f"\n  {DIM}comando:{R}")
    print(f"  {YLW}{B}{cmd.command}{R}")
    print(f"    {DIM}{cmd.latency_ms}ms{R}")

    # CLI menu
    user_action = None
    edited_command = None
    exec_output = None
    exec_code = None
    final_command = cmd.command

    while True:
        print()
        print(f"  {GRN}e{R} ejecutar  {CYN}c{R} copiar  {YLW}r{R} editar  {RED}x{R} cancelar")
        choice = input(f"  {CYN}>{R} ").strip().lower()

        if choice == "e":
            user_action = "executed"
            stop = threading.Event()
            t = threading.Thread(target=spinner, args=("Ejecutando...", stop), daemon=True)
            t.start()
            result = run_command(final_command)
            stop.set()
            t.join()
            exec_output = result.stdout or result.stderr
            exec_code = result.exit_code

            _clear_line()
            if result.stdout:
                print(f"\n{WHT}{result.stdout.rstrip()}{R}")
            if result.stderr:
                print(f"\n{RED}{result.stderr.rstrip()}{R}")

            color = GRN if result.exit_code == 0 else RED
            print(f"\n  {color}exit {result.exit_code}{R}")
            break

        elif choice == "c":
            user_action = "copied"
            pyperclip.copy(final_command)
            print(f"  {GRN}* Copiado al clipboard{R}")
            break

        elif choice == "r":
            new_cmd = input(f"  {YLW}>{R} ").strip()
            if new_cmd:
                edited_command = new_cmd
                final_command = new_cmd
                print(f"  {DIM}comando:{R} {YLW}{B}{final_command}{R}")
            continue

        elif choice == "x":
            user_action = "cancelled"
            print(f"  {DIM}cancelado{R}")
            break

    cfg = load_config()
    log_command(
        transcription=stt.text,
        detected_language=stt.language,
        audio_duration_sec=stt.audio_duration_sec,
        whisper_model=cfg["whisper_model"],
        ollama_model=cmd.model,
        generated_command=cmd.command,
        user_action=user_action or "cancelled",
        edited_command=edited_command,
        execution_output=exec_output,
        execution_exit_code=exec_code,
        latency_stt_ms=stt.latency_ms,
        latency_llm_ms=cmd.latency_ms,
    )


# ── Text mode ──────────────────────────────────────────────────

def _handle_text_mode(rec):
    """Process a text-mode recording: transcribe -> clipboard."""
    _section("Modo Texto")

    stop = threading.Event()
    t = threading.Thread(target=spinner, args=("Transcribiendo...", stop), daemon=True)
    t.start()
    stt = transcribe(rec.audio, rec.sample_rate)
    stop.set()
    t.join()

    if not stt.text:
        _replace_line(f"  {RED}! No se detecto voz.{R}")
        return

    pyperclip.copy(stt.text)
    _replace_line(f"  {GRN}* Copiado:{R} {B}{stt.text}{R}")
    print(f"    {DIM}{stt.language} | {stt.latency_ms}ms | {stt.audio_duration_sec}s audio{R}")

    cfg = load_config()
    log_text(
        transcription=stt.text,
        detected_language=stt.language,
        audio_duration_sec=stt.audio_duration_sec,
        whisper_model=cfg["whisper_model"],
        latency_stt_ms=stt.latency_ms,
    )


# ── Main ───────────────────────────────────────────────────────

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    colorama_init()

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{DIM}--- session {ts} ---{R}")

    cfg = load_config()
    _print_banner(cfg)
    warmup()

    if cfg.get("http_enabled"):
        from .http_server import start_server
        start_server(cfg)

    recorder = Recorder()
    _waiting()

    try:
        while True:
            rec = recorder.wait_for_recording()
            if rec.audio.size == 0:
                print(f"  {RED}! Grabacion vacia{R}")
                _waiting()
                continue

            if rec.mode == "command":
                _handle_command_mode(rec)
            elif rec.mode == "text":
                _handle_text_mode(rec)

            _waiting()
    except KeyboardInterrupt:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{DIM}--- ended {ts} ---{R}")
        sys.exit(0)


if __name__ == "__main__":
    main()
