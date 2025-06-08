#!/usr/bin/env python3
"""Helper to launch backend and frontend for local development."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / "chatbot_env"


def venv_bin(executable: str) -> Path:
    """Return the path to an executable inside the virtual env."""
    folder = "Scripts" if os.name == "nt" else "bin"
    exe = executable + (".exe" if os.name == "nt" else "")
    return VENV / folder / exe


def ensure_venv() -> Path:
    """Create the Python virtual environment if it doesn't exist."""
    if not VENV.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    return VENV


def ensure_node() -> None:
    """Install Node dependencies if needed."""
    react_dir = ROOT / "ReactApp"
    if not (react_dir / "node_modules").exists():
        npm = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.check_call([npm, "install"], cwd=react_dir)


def start_backend(env: dict[str, str]) -> subprocess.Popen:
    """Start the FastAPI backend using uvicorn."""
    python = str(venv_bin("python"))
    return subprocess.Popen(
        [python, "-m", "uvicorn", "kydxbot.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        env=env,
    )


def start_frontend() -> subprocess.Popen:
    """Run the React development server."""
    react_dir = ROOT / "ReactApp"
    npm = "npm.cmd" if os.name == "nt" else "npm"
    return subprocess.Popen([npm, "run", "dev"], cwd=react_dir)


def main() -> None:
    env = os.environ.copy()
    # Ensure our project package is importable by adding the repo's parent
    # directory to PYTHONPATH. This mirrors running uvicorn from one level above
    # the package so "kydxbot.*" modules resolve correctly.
    parent = ROOT.parent
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(parent) + (os.pathsep + current if current else "")
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
