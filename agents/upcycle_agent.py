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
Material Description(s): {description}
Dimension(s): {dimensions}

Generate exactly THREE diverse, SIMPLE, and HIGHLY FEASIBLE upcycling DIY projects.
IMPORTANT: You must treat the provided dimensions as FIXED PHYSICAL CONSTRAINTS. Do not suggest projects that are physically impossible or poorly scaled (e.g., if an item is only 5cm long, don't suggest it as a book shelf).
Ensure the construction steps are easy enough for a beginner and strictly incorporate the provided dimensions into the manual steps.
Be UNUSUALLY CONSERVATIVE with time estimates—err on the side of longer durations to ensure users are not discouraged by unexpected delays.
Keep pricing EXTREMELY CONSERVATIVE.

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
    "flux_image_prompt": "STRICTLY ISOLATED on a PURE SOLID WHITE BACKGROUND. High-end professional studio product photography of the finished product ONLY. No shadows, no floor, no environment, no other objects. Transparent-style isolation on #FFFFFF white."
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

def generate_diy_plan(material_info: dict, dimensions: str = "Standard size") -> dict:
    """Legacy wrapper for backward compatibility."""
    desc = (
        f"{material_info.get('material', material_info.get('material_name', 'item'))} "
        f"- {material_info.get('condition', material_info.get('description', ''))}"
    )
    plans = generate_top_3_plans(description=desc, dimensions=dimensions)
    return plans[0] if plans else {}

def run_pipeline(image_bytes: bytes) -> dict:
    """Legacy wrapper to avoid startup errors if anything still points here."""
    from .analyze_agent import analyze_item
    info = analyze_item(image_bytes)
    return generate_diy_plan(info)
