#!/usr/bin/env bash
# start_dev.sh — cross‐platform dev launcher

set -euo pipefail

# 1) Locate script directory and cd into it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 2) Detect & source the virtualenv activation script
if [ -f "chatbot_env/bin/activate" ]; then
  # Unix / macOS venv
  # shellcheck disable=SC1091
  source "chatbot_env/bin/activate"
elif [ -f "chatbot_env/Scripts/activate" ]; then
  # Windows venv (Git Bash / WSL)
  # shellcheck disable=SC1091
  source "chatbot_env/Scripts/activate"
else
  echo "ERROR: No virtualenv found in chatbot_env/(bin|Scripts)"
  exit 1
fi

# 3) Launch the backend on a background job
#    Use `python -m uvicorn` to be explicit about interpreter
python -m uvicorn kydxbot.server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 4) Change into your React app and start it
cd ReactApp
npm run dev

# 5) When npm exits (Ctrl+C), tear down the backend
kill "$BACKEND_PID"
