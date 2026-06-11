#!/usr/bin/env bash
# start_vllm.sh — Launch vLLM server on AMD GPU (ROCm)
#
# Prerequisites:
#   - ROCm 6.x installed
#   - vLLM installed (pip install vllm)
#   - At least 16 GB GPU VRAM for Mistral-7B (use fp16)
#
# Usage: bash start_vllm.sh [model_name]

MODEL="${1:-mistralai/Mistral-7B-Instruct-v0.3}"
HOST="0.0.0.0"
PORT="8000"

echo "================================================"
echo " Starting vLLM OpenAI-compatible server"
echo " Model : $MODEL"
echo " Device: AMD GPU (ROCm)"
echo " URL   : http://$HOST:$PORT/v1"
echo "================================================"

python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" \
  --host "$HOST" \
  --port "$PORT" \
  --dtype float16 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.90 \
  --trust-remote-code

# If you run into VRAM issues, try:
#   --quantization awq
# Or switch to a smaller model:
#   mistralai/Mistral-7B-Instruct-v0.1
#   TinyLlama/TinyLlama-1.1B-Chat-v1.0  (for testing)
