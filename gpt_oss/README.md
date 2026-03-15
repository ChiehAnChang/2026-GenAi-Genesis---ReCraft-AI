# GPT-OSS via vLLM — Sample Code

This folder contains ready-to-run samples for using OpenAI's `gpt-oss-20b` / `gpt-oss-120b` models via vLLM at the hackathon.

## ⚠️ Hardware Requirement

> **vLLM requires a CUDA-capable NVIDIA GPU.**  
> Your Mac does not have one. You need to run these on a provided hackathon GPU server (e.g. H100).

| Model | Minimum VRAM |
|-------|-------------|
| `gpt-oss-20b` | ~16 GB |
| `gpt-oss-120b` | ~60 GB (single H100 or multi-GPU) |

---

## 🚀 Quick Start (on GPU server)

### 1. Install everything
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Start the vLLM server (in one terminal, keep it running)
```bash
source .venv/bin/activate

# Smaller model (~16GB VRAM)
vllm serve openai/gpt-oss-20b

# OR larger model (~60GB VRAM)
vllm serve openai/gpt-oss-120b
```

The server will download the model from HuggingFace and start an OpenAI-compatible API at `http://localhost:8000`.

### 3. Run the samples (in a second terminal)
```bash
source .venv/bin/activate

python 1_basic_chat.py         # Chat Completions + Responses API
python 2_function_calling.py   # Tool/function calling
python 3_agents_sdk.py         # Agents SDK integration
python 4_direct_sampling.py    # Direct vLLM (no HTTP server)
```

---

## 📁 File Overview

| File | What it shows |
|------|--------------|
| `setup.sh` | Install uv, vLLM, all dependencies |
| `1_basic_chat.py` | Chat Completions & Responses API |
| `2_function_calling.py` | Tool calling with CoT loop |
| `3_agents_sdk.py` | Agents SDK with custom tools (weather + upcycling) |
| `4_direct_sampling.py` | Direct vLLM + Harmony encoding (advanced) |

---

## 🔗 Integration with ReCraft AI Backend

To swap your current backend from Gemini/GPT-4o to gpt-oss, in `backend/main.py` or the agents, change:

```python
# Before (OpenAI cloud)
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# After (gpt-oss via local vLLM)
from openai import OpenAI
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY"
)
# model name → "openai/gpt-oss-20b" or "openai/gpt-oss-120b"
```

Everything else (chat completions, tool calling, etc.) stays the same!
