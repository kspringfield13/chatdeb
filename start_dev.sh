#!/usr/bin/env bash
# start_dev.sh - Run backend and frontend for local development.

set -e

# Resolve the absolute path to the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"  # assuming start_dev.sh is at root level of project

# Move to project root
cd "$PROJECT_ROOT"

# Activate Python virtual environment if it exists
if [ -d "$PROJECT_ROOT/chatbot_env" ]; then
  source "$PROJECT_ROOT/chatbot_env/bin/activate"
fi

# Set PYTHONPATH to include project root
export PYTHONPATH="$PROJECT_ROOT"

# Start FastAPI backend
uvicorn kydxbot.server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start React frontend
FRONTEND_DIR="$PROJECT_ROOT/ReactApp"
if [ -d "$FRONTEND_DIR" ]; then
  cd "$FRONTEND_DIR"
  npm run dev
else
  echo "❌ ReactApp directory not found at $FRONTEND_DIR"
fi

# Clean up backend process when frontend exits
kill $BACKEND_PID
