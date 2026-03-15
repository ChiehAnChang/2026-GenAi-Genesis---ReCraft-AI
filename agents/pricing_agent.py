"""
Pricing Agent — uses gpt-oss-120b (via HuggingFace vLLM endpoint) to output
a structured JSON price estimate for the upcycled product, grounded in
real market reasoning.
"""

from __future__ import annotations

import os
import json
import re
from openai import OpenAI

GPT_OSS_BASE_URL = os.getenv(
    "GPT_OSS_BASE_URL",
    "https://vjioo4r1vyvcozuj.us-east-2.aws.endpoints.huggingface.cloud/v1",
)

PRICING_SYSTEM_PROMPT = """You are an expert market analyst specializing in sustainable goods and the circular economy. 
Your pricing strategy is EXTREMELY CONSERVATIVE. 

Rules for Pricing:
- For simple DIY items with minimal materials, suggest prices between $0 (Free/Community) and $10.
- If a project takes less than 1 hour and uses only waste, the price should be near-zero or a "Community Gift" price.
- Never overvalue basic handmade crafts. Be realistic: the goal is waste diversion, not profit.
- Pricing should be grounded in the fact that these are repurposed waste items with low resale value.

Respond with ONLY valid JSON, no markdown fences."""

PRICING_PROMPT = """Analyze this upcycled product and provide a market price estimate:

Product: {project_name}
Original Material: {material}
Tagline: {tagline}
Difficulty: {difficulty}
Time Estimate: {time_estimate}

Return ONLY valid JSON:
{{
  "item_name": "{project_name}",
  "material": "{material}",
  "materials_cost_usd": <number, cost of any additional materials>,
  "labor_hours": <number>,
  "suggested_hourly_rate_usd": <number, 8-15 for craft labor>,
  "labor_cost_usd": <number>,
  "platform_fee_usd": <number, assume 10% of selling price>,
  "price_range_low_usd": <number>,
  "price_range_high_usd": <number>,
  "recommended_price_usd": <number, single best price>,
  "justification": "<one compelling sentence explaining the price>"
}}"""


def _parse_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return json.loads(text)


def estimate_price(upcycle_result: dict, labor_hours_override: float | None = None) -> dict:
    """
    Calls gpt-oss-120b to estimate a realistic resale price for the upcycled product.
    Optionally overrides labor hours for the advanced slider feature.
    """
    prompt = PRICING_PROMPT.format(
        project_name=upcycle_result.get("project_name", "Upcycled Item"),
        material=upcycle_result.get("material", "mixed material"),
        tagline=upcycle_result.get("tagline", ""),
        difficulty=upcycle_result.get("difficulty", "Medium"),
        time_estimate=upcycle_result.get("time_estimate", "2 hours"),
    )

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "test"),
        base_url=GPT_OSS_BASE_URL,
    )
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": PRICING_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,  # Low temp for consistent pricing
        max_tokens=1024,  # gpt-oss needs room for chain-of-thought reasoning
    )

    raw = response.choices[0].message.content or ""
    result = _parse_json(raw)

    # Apply labor hours override if provided (for the slider feature)
    if labor_hours_override is not None:
        rate = result.get("suggested_hourly_rate_usd", 12)
        result["labor_hours"] = labor_hours_override
        result["labor_cost_usd"] = round(labor_hours_override * rate, 2)
        base = result["materials_cost_usd"] + result["labor_cost_usd"]
        result["price_range_low_usd"] = round(base * 1.1, 2)
        result["price_range_high_usd"] = round(base * 1.4, 2)
        result["recommended_price_usd"] = round(base * 1.25, 2)

    return result
