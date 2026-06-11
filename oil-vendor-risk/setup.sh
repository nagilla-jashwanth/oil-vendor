#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Oil Vendor Risk Management – Environment Setup Script
# Compatible with: AMD ROCm vLLM Jupyter Cloud Notebook (Ubuntu 22.04)
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo ""
echo "══════════════════════════════════════════════════════"
echo "  OIL Vendor Risk Management – Setup"
echo "══════════════════════════════════════════════════════"
echo ""

# ── 1. Python virtual environment ────────────────────────────────────────────
echo "▶ Step 1/4 – Creating virtual environment…"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet

# ── 2. Install Python dependencies ───────────────────────────────────────────
echo "▶ Step 2/4 – Installing Python packages…"
pip install -r requirements.txt --quiet

echo ""
echo "  ✓ Packages installed"
echo ""

# ── 3. Copy .env if it doesn't exist ─────────────────────────────────────────
echo "▶ Step 3/4 – Checking .env file…"
if [ ! -f ".env" ]; then
  cp .env.example .env 2>/dev/null || true
  echo "  ⚠  Created .env — please edit it before starting."
else
  echo "  ✓ .env already exists"
fi

# ── 4. Verify vLLM reachability (optional) ───────────────────────────────────
echo "▶ Step 4/4 – Probing vLLM endpoint…"
VLLM_URL=$(grep VLLM_BASE_URL .env | cut -d= -f2 | tr -d ' ')
VLLM_URL=${VLLM_URL:-http://localhost:8000/v1}

if curl -sf "${VLLM_URL}/models" -o /dev/null 2>&1; then
  echo "  ✓ vLLM is reachable at ${VLLM_URL}"
else
  echo "  ⚠  vLLM not reachable at ${VLLM_URL}"
  echo "     Start it first (see START_VLLM.sh), or set USE_AZURE=true in .env"
fi

echo ""
echo "══════════════════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "    1. Edit .env to match your model name / endpoint"
echo "    2. bash start_vllm.sh      (if using local vLLM)"
echo "    3. bash run.sh             (start the FastAPI app)"
echo "══════════════════════════════════════════════════════"
echo ""
