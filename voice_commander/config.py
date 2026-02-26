"""Configuration for Voice Commander."""

import json
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULTS = {
    # Hotkeys
    "hotkey_command": "ctrl+alt+v",
    "hotkey_text": "ctrl+alt+t",

    # Audio
    "sample_rate": 16000,
    "channels": 1,

    # Whisper STT
    "whisper_model": "medium",
    "whisper_device": "cuda",
    "whisper_compute_type": "float16",
    "whisper_initial_prompt": (
        "KAPS, Syion, Komoco, llavetina, getSalesOrderToPurchaseOrder, "
        "aftersales, IIS Express, stored procedure, PowerShell, git, "
        "docker, dotnet, npm, SQL Server, Visual Studio"
    ),

    # Ollama LLM
    "ollama_url": "http://localhost:11434",
    "ollama_model": "qwen2.5-coder:14b-instruct",
    "ollama_system_prompt": (
        "You are a terminal command generator for a Windows 11 machine.\n"
        "The user's environment:\n"
        "- OS: Windows 11 Pro\n"
        "- Shell: PowerShell 7 and Git Bash\n"
        "- Installed: git, node, npm, dotnet, python, pip, docker, claude (Claude Code CLI)\n"
        "- Projects: ASP.NET apps, IIS Express, SQL Server databases\n"
        "- Custom terms: KAPS, Syion, Komoco, llavetina, aftersales\n\n"
        "The user has these PowerShell shortcuts (functions in $PROFILE):\n"
        "- shortcuts: shows all available shortcuts from a txt file\n"
        "- go-dev: cd C:\\dev\n"
        "- go-my: cd C:\\dev\\my-adventures\n"
        "- go-syion: cd C:\\dev\\syion\n"
        "- go-kaps: cd C:\\dev\\syion\\kaps\n"
        "- go-sales: cd C:\\dev\\syion\\kaps\\sales\n"
        "- go-after: cd C:\\dev\\syion\\kaps\\after-sales\n"
        "- go-hdi: cd C:\\dev\\hdi\n"
        "- go-llavetina: cd C:\\dev\\hdi\\Llavetina\n"
        "- claude-skills: opens claude in claude-skills project\n"
        "- agent-sales: opens claude in sales project\n"
        "- llavetina: opens Edge workspace + claude in Llavetina project\n"
        "- claude-after-1: opens Edge workspace + claude in after-sales project\n"
        "- edge-hdi: opens HDI Edge workspace\n"
        "- edge-syion: opens Syion Edge workspace\n"
        "- telegram-off: disables telegram hooks\n"
        "- voice-commander: launches voice commander in a new terminal window\n\n"
        "Rules:\n"
        "- Return ONLY the command as a raw string\n"
        "- No markdown, no code fences, no explanation, no yapping\n"
        "- If the user says 'shortcuts' or 'muestra shortcuts', return: shortcuts\n"
        "- Use the user's custom shortcuts when they reference projects or navigation\n"
        "- If multiple commands are needed, separate with ;\n"
        "- Do not include commands requiring interactive input (y/n prompts)\n"
        "- Prefer PowerShell syntax unless the user specifies bash\n"
        "- For SQL queries, wrap in sqlcmd or Invoke-Sqlcmd"
    ),

    # Execution
    "exec_timeout": 30,

    # Logging
    "log_dir": os.path.join(_BASE_DIR, "logs"),
    "log_max_bytes": 50 * 1024 * 1024,  # 50MB
}


def load_config() -> dict:
    """Load config from defaults, overridden by config.json if present."""
    cfg = dict(DEFAULTS)
    config_path = os.path.join(_BASE_DIR, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            overrides = json.load(f)
        cfg.update(overrides)
    return cfg
