#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Start vLLM on AMD ROCm GPU
# Run this FIRST, in a separate terminal, before run.sh
# ─────────────────────────────────────────────────────────────────────────────

# Load .env
set -a; source .env 2>/dev/null; set +a

MODEL=${VLLM_MODEL_NAME:-"mistralai/Mistral-7B-Instruct-v0.3"}
PORT=8000

echo ""
echo "▶ Starting vLLM server"
echo "  Model : ${MODEL}"
echo "  Port  : ${PORT}"
echo ""
echo "  AMD GPU info:"
rocm-smi --showid --showproductname 2>/dev/null || echo "  (rocm-smi not found — proceeding)"
echo ""

# vLLM with ROCm uses the same CLI as CUDA; ROCm is auto-detected
python3 -m vllm.entrypoints.openai.api_server \
  --model "${MODEL}" \
  --port ${PORT} \
  --host 0.0.0.0 \
  --dtype float16 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85 \
  --trust-remote-code

# Notes:
# • For larger models (13B+) lower --gpu-memory-utilization to 0.75
# • Add --tensor-parallel-size 2 if you have 2 GPUs
# • Mistral-7B-Instruct fits comfortably on a single MI250/MI300 in float16
