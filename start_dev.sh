#!/usr/bin/env bash
# start_dev.sh - run backend and frontend for local development.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual env if it exists
if [ -d "chatbot_env" ]; then
  source chatbot_env/bin/activate
fi

# Ensure PYTHONPATH includes the current directory (project root)
export PYTHONPATH="$SCRIPT_DIR"

# Double check: this must exist for `kydxbot` to be importable
touch kydxbot/__init__.py

# Start backend
uvicorn kydxbot.server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
cd ReactApp
npm run dev

# Kill backend when frontend exits
kill $BACKEND_PID
