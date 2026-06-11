#!/usr/bin/env bash
# start_frontend.sh — Start the React dev server
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend"

echo "[INFO] Installing npm dependencies (first run only)..."
npm install

echo "[INFO] Starting Vite dev server on port 5173..."
npm run dev
