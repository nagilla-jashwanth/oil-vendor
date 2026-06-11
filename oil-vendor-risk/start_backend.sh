#!/usr/bin/env bash
# start_backend.sh — Start the FastAPI backend
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

# Activate venv if it exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Copy .env.example to .env if not present
if [ ! -f ".env" ]; then
  echo "[INFO] .env not found. Copying from .env.example..."
  cp .env.example .env
fi

echo "[INFO] Starting FastAPI backend on port 8080..."
python main.py
