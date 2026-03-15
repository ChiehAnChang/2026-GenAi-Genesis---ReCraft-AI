"""
Sample 3: Agents SDK Integration with gpt-oss via vLLM
Run after: vllm serve openai/gpt-oss-120b
Install:   uv pip install openai-agents
"""

import asyncio
from openai import AsyncOpenAI
from agents import Agent, Runner, function_tool, OpenAIResponsesModel, set_tracing_disabled

# Disable tracing (no OpenAI account needed in hackathon)
set_tracing_disabled(True)

# Point to local vLLM server
vllm_client = AsyncOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",
)

MODEL = "openai/gpt-oss-120b"  # or gpt-oss-20b


@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    print(f"[debug] getting weather for {city}")
    return f"The weather in {city} is sunny and 22°C."


@function_tool
def get_upcycling_idea(material: str) -> str:
    """Get a creative upcycling idea for a given material."""
    print(f"[debug] getting upcycling idea for {material}")
    ideas = {
        "plastic bottle": "Turn it into a self-watering planter!",
        "cardboard box": "Make a modular desk organiser!",
        "glass jar": "Create a terrarium for succulents!",
        "t-shirt": "Cut it into a no-sew tote bag!",
    }
    return ideas.get(material.lower(), f"Try making a mosaic or collage with {material}!")


async def main():
    agent = Agent(
        name="ReCraft Assistant",
        instructions=(
            "You are a creative sustainability assistant. "
            "Help users find upcycling ideas and weather info. "
            "Always be enthusiastic about eco-friendly crafts!"
        ),
        model=OpenAIResponsesModel(
            model=MODEL,
            openai_client=vllm_client,
        ),
        tools=[get_weather, get_upcycling_idea],
    )

    # Test 1: Weather query
    print("=" * 60)
    print("🌤️  Test 1: Weather query")
    print("=" * 60)
    result = await Runner.run(agent, "What's the weather in Tokyo?")
    print(result.final_output)

    # Test 2: Upcycling idea
    print("\n" + "=" * 60)
    print("♻️  Test 2: Upcycling idea")
    print("=" * 60)
    result = await Runner.run(agent, "I have an old plastic bottle, what can I make with it?")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
