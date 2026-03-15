"""
Sample 2: Function Calling (Tool Use) via Chat Completions API
Run after: vllm serve openai/gpt-oss-20b (or 120b)
"""

from openai import OpenAI
import json

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY"
)

MODEL = "openai/gpt-oss-20b"  # or gpt-oss-120b

# Define the tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather in a given city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            },
        },
    }
]

messages = [{"role": "user", "content": "What's the weather in Berlin right now?"}]

print("🤖 Sending request to model...")
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    tools=tools
)

msg = response.choices[0].message
print(f"Model response: finish_reason={response.choices[0].finish_reason}")

# ── Handle tool call loop (chain-of-thought) ─────────────────────────────────
while response.choices[0].finish_reason == "tool_calls":
    messages.append(msg)  # Append assistant message with tool call

    for tool_call in msg.tool_calls:
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)
        print(f"📞 Tool called: {fn_name}({fn_args})")

        # ── Simulate the actual function ──────────────────────────────────────
        if fn_name == "get_weather":
            tool_result = f"The weather in {fn_args['city']} is 18°C and mostly cloudy."
        else:
            tool_result = "Unknown function"

        # Append the tool result back to messages
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": tool_result,
        })

    # Send the next request including tool result
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools
    )
    msg = response.choices[0].message

print("\n✅ Final answer:")
print(msg.content)
