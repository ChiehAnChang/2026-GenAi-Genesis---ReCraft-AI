"""
Upcycle Planner Agent — Step 2: Generates 3 DIY plans based on confirmed material info.
Uses gpt-oss-120b.
"""

from __future__ import annotations
import os
from openai import OpenAI
from .utils import parse_json

# gpt-oss client for DIY plan generation
GPT_OSS_BASE_URL = os.getenv(
    "GPT_OSS_BASE_URL",
    "https://vjioo4r1vyvcozuj.us-east-2.aws.endpoints.huggingface.cloud/v1",
)
gpt_oss_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "test"),
    base_url=GPT_OSS_BASE_URL,
)

PLAN_GENERATOR_PROMPT = """You are a master upcycling designer.
Material Description: {description}
Dimensions: {dimensions}

Generate exactly THREE diverse and high-quality upcycling DIY projects for this item.
For each project, provide:
1. Catchy project name
2. One-line tagline
3. Difficulty (Easy, Medium, or Hard)
4. Time estimate
5. Materials needed (list)
6. 5 clear construction steps
7. Sustainability impact
8. Flux image prompt (photorealistic, showing the finished product)

Respond with ONLY valid JSON (a list of 3 objects):
[
  {{
    "project_name": "...",
    "tagline": "...",
    "difficulty": "...",
    "time_estimate": "...",
    "materials_needed": ["...", "..."],
    "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ...", "Step 4: ...", "Step 5: ..."],
    "sustainability_impact": "...",
    "co2_saved_kg": 1.5,
    "flux_image_prompt": "..."
  }},
  ...
]"""

def generate_top_3_plans(description: str, dimensions: str) -> list[dict]:
    """Step 2: Generate 3 distinct DIY plans based on confirmed description and size."""
    prompt = PLAN_GENERATOR_PROMPT.format(
        description=description,
        dimensions=dimensions
    )
    
    response = gpt_oss_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a creative upcycling expert. Always respond with a valid JSON list of 3 objects."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=2048,
    )
    raw = response.choices[0].message.content or ""
    return parse_json(raw)

def generate_diy_plan(material_info: dict) -> dict:
    """Legacy wrapper for backward compatibility."""
    plans = generate_top_3_plans(
        description=f"{material_info.get('material_name', 'item')} - {material_info.get('description', '')}",
        dimensions="Standard size"
    )
    return plans[0] if plans else {}

def run_pipeline(image_bytes: bytes) -> dict:
    """Legacy wrapper to avoid startup errors if anything still points here."""
    from .analyze_agent import analyze_item
    info = analyze_item(image_bytes)
    return generate_diy_plan(info)
