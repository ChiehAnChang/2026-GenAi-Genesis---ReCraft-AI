#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# ReCraft AI — GPT-OSS vLLM Setup Script
# Run this on a CUDA-capable GPU server (e.g. H100 / A100)
# ─────────────────────────────────────────────────────────────────

set -e

echo "🔧 Step 1: Install uv (Python package manager)"
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

echo "🐍 Step 2: Create Python 3.12 virtual environment"
uv venv --python 3.12 --seed
source .venv/bin/activate

echo "📦 Step 3: Install vLLM (gpt-oss build)"
uv pip install --pre vllm==0.10.1+gptoss \
    --extra-index-url https://wheels.vllm.ai/gpt-oss/ \
    --extra-index-url https://download.pytorch.org/whl/nightly/cu128 \
    --index-strategy unsafe-best-match

echo "📦 Step 4: Install OpenAI SDK + Agents SDK + Harmony"
uv pip install openai openai-agents openai-harmony

echo "✅ Setup complete! Now run one of:"
echo "   vllm serve openai/gpt-oss-20b     # ~16GB VRAM"
echo "   vllm serve openai/gpt-oss-120b    # ~60GB VRAM"
