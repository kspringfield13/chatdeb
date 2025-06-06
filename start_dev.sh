#!/usr/bin/env bash
# start_dev.sh — launch backend and frontend in separate Terminal windows

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

if [ -d "$PROJECT_ROOT/chatbot_env" ]; then
  source "$PROJECT_ROOT/chatbot_env/bin/activate"
fi

export PYTHONPATH="$PROJECT_ROOT"

# Commands to run in the spawned terminals
BACKEND_CMD="cd '$PROJECT_ROOT' && source chatbot_env/bin/activate && export PYTHONPATH='$PROJECT_ROOT' && uvicorn kydxbot.server:app --host 0.0.0.0 --port 8000 --reload"
FRONTEND_CMD="cd '$PROJECT_ROOT/ReactApp' && npm run dev"

# Open two new Terminal windows running backend and frontend
osascript <<EOF
tell application "Terminal"
    activate
    do script "bash -c '$BACKEND_CMD'"
    do script "bash -c '$FRONTEND_CMD'"
end tell
EOF

# Open the chatbot UI in the default browser
sleep 2
open http://localhost:5173
