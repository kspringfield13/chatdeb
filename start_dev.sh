#!/usr/bin/env bash
# start_dev.sh - run backend and frontend for local development.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "chatbot_env" ]; then
  # shellcheck disable=SC1091
  source chatbot_env/bin/activate
fi

# Ensure PYTHONPATH includes current directory so `kydxbot.server` is resolvable
export PYTHONPATH="$SCRIPT_DIR"

# Start backend via uvicorn using kydxbot.server:app
uvicorn kydxbot.server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Run frontend
cd kydxbot/ReactApp
npm run dev

# Kill backend when frontend stops
kill $BACKEND_PID
