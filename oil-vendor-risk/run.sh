#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Start the Oil Vendor Risk FastAPI application
# ─────────────────────────────────────────────────────────────────────────────
set -e

# Activate venv if it exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

set -a; source .env 2>/dev/null; set +a

HOST=${APP_HOST:-0.0.0.0}
PORT=${APP_PORT:-7860}

echo ""
echo "══════════════════════════════════════════════════════"
echo "  OIL Vendor Risk Management"
echo "  http://${HOST}:${PORT}"
echo "══════════════════════════════════════════════════════"
echo ""

python3 main.py
