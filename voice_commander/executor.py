"""Safe command execution via subprocess."""

import subprocess
from dataclasses import dataclass

from .config import load_config


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int


def run_command(command: str) -> ExecResult:
    """Execute a shell command with timeout and output capture.

    Args:
        command: the command string to execute.

    Returns:
        ExecResult with stdout, stderr, and exit code.
    """
    cfg = load_config()
    try:
        result = subprocess.run(
            ["pwsh", "-Command", command],
            capture_output=True,
            text=True,
            timeout=cfg["exec_timeout"],
            encoding="utf-8",
            errors="replace",
        )
        return ExecResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return ExecResult(
            stdout="",
            stderr=f"Command timed out after {cfg['exec_timeout']}s",
            exit_code=-1,
        )
