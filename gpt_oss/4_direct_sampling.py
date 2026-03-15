"""
Sample 4: Direct vLLM Sampling with Harmony Encoding
For advanced use: bypasses the HTTP server, runs inference directly in Python.
Install: uv pip install openai-harmony vllm
Run on a CUDA GPU server only.
"""

import json
from openai_harmony import (
    HarmonyEncodingName,
    load_harmony_encoding,
    Conversation,
    Message,
    Role,
    SystemContent,
    DeveloperContent,
)
from vllm import LLM, SamplingParams

MODEL = "openai/gpt-oss-120b"  # or gpt-oss-20b

# ── Step 1: Build conversation using Harmony encoding ─────────────────────────
print("🔧 Loading Harmony encoding...")
encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)

convo = Conversation.from_messages([
    Message.from_role_and_content(Role.SYSTEM, SystemContent.new()),
    Message.from_role_and_content(
        Role.DEVELOPER,
        DeveloperContent.new().with_instructions(
            "You are a creative sustainability expert for ReCraft AI. "
            "Always suggest eco-friendly upcycling ideas."
        ),
    ),
    Message.from_role_and_content(
        Role.USER,
        "I have an old glass jar. What's a creative upcycling project I can make?"
    ),
])

# Render the conversation into token IDs for the model
prefill_ids = encoding.render_conversation_for_completion(convo, Role.ASSISTANT)

# Get harmony stop tokens so vLLM knows when to stop
stop_token_ids = encoding.stop_tokens_for_assistant_actions()

# ── Step 2: Load model and run inference ─────────────────────────────────────
print(f"🤖 Loading model {MODEL}...")
llm = LLM(
    model=MODEL,
    trust_remote_code=True,
)

sampling = SamplingParams(
    max_tokens=256,
    temperature=0.8,
    stop_token_ids=stop_token_ids,
)

print("⚡ Running inference...")
outputs = llm.generate(
    prompts=[{"prompt_token_ids": prefill_ids}],
    sampling_params=sampling,
)

# ── Step 3: Parse completion tokens back into structured messages ─────────────
gen = outputs[0].outputs[0]
text = gen.text
output_tokens = gen.token_ids

print("\n📝 Raw completion text:")
print(text)

print("\n📦 Structured Harmony messages:")
entries = encoding.parse_messages_from_completion_tokens(output_tokens, Role.ASSISTANT)
for message in entries:
    print(json.dumps(message.to_dict(), indent=2))
