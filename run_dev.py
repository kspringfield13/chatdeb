#!/usr/bin/env python3
"""Helper to launch backend and frontend for local development."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / "chatbot_env"


def ensure_venv() -> Path:
    """Create the Python virtual environment if it doesn't exist."""
    if not VENV.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    return VENV


def ensure_node() -> None:
    """Install Node dependencies if needed."""
    react_dir = ROOT / "ReactApp"
    if not (react_dir / "node_modules").exists():
        subprocess.check_call(["npm", "install"], cwd=react_dir)


def start_backend(env: dict[str, str]) -> subprocess.Popen:
    """Start the FastAPI backend using uvicorn."""
    python = str(VENV / "bin" / "python")
    return subprocess.Popen(
        [python, "-m", "uvicorn", "kydxbot.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        env=env,
    )


def start_frontend() -> subprocess.Popen:
    """Run the React development server."""
    react_dir = ROOT / "ReactApp"
    return subprocess.Popen(["npm", "run", "dev"], cwd=react_dir)


def main() -> None:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT))
    ensure_venv()
    ensure_node()
    backend = start_backend(env)
    frontend = start_frontend()
    try:
        frontend.wait()
    finally:
        backend.terminate()
        backend.wait()


if __name__ == "__main__":
    main()
