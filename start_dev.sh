#!/usr/bin/env bash
# start_dev.sh — Run backend in new terminal, frontend in current shell

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

if [ -d "$PROJECT_ROOT/chatbot_env" ]; then
  source "$PROJECT_ROOT/chatbot_env/bin/activate"
fi

export PYTHONPATH="$PROJECT_ROOT"

# Safely escape the command string for AppleScript
SERVER_CMD="cd $PROJECT_ROOT; source chatbot_env/bin/activate; export PYTHONPATH=$PROJECT_ROOT; uvicorn kydxbot.server:app --host 0.0.0.0 --port 8000 --reload"

# Launch backend in new Terminal window
osascript <<EOF
tell application "Terminal"
    activate
    do script "bash -c '$SERVER_CMD'"
end tell
EOF

# Launch React frontend in current terminal
FRONTEND_DIR="$PROJECT_ROOT/ReactApp"
if [ -d "$FRONTEND_DIR" ]; then
  cd "$FRONTEND_DIR"
  npm run dev
else
  echo "❌ ReactApp directory not found at $FRONTEND_DIR"
fi
