"""
Sample 1: Basic Chat Completions & Responses API
Run after: vllm serve openai/gpt-oss-20b (or 120b)
"""

from openai import OpenAI

# Point to local vLLM server (no real API key needed)
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY"
)

MODEL_20B = "openai/gpt-oss-20b"
MODEL_120B = "openai/gpt-oss-120b"

# ── Chat Completions API ───────────────────────────────────────────────────────
print("=" * 60)
print("📡 Chat Completions API")
print("=" * 60)

result = client.chat.completions.create(
    model=MODEL_20B,  # Change to MODEL_120B if using the larger model
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain what MXFP4 quantization is in 2-3 sentences."}
    ]
)

print(result.choices[0].message.content)

# ── Responses API ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("📡 Responses API")
print("=" * 60)

response = client.responses.create(
    model=MODEL_20B,
    instructions="You are a helpful assistant.",
    input="What is MXFP4 quantization?"
)

print(response.output_text)
