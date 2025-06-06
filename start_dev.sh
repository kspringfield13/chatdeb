#!/usr/bin/env bash
# start_dev.sh - run backend and frontend for local development.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "chatbot_env" ]; then
  # shellcheck disable=SC1091
  source chatbot_env/bin/activate
fi

# Run the FastAPI backend. We invoke the app via its package path so
# that Python treats it as part of the "kydxbot" package. This allows
# relative imports like "from .chatbot import ..." in server.py to
# resolve correctly regardless of where the script is launched from.
uvicorn kydxbot.server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ReactApp
npm run dev

kill $BACKEND_PID

