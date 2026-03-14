"""
Pricing Agent — uses OpenAI GPT to output a structured JSON price estimate
for the upcycled product, grounded in real market reasoning.
"""

import os
import json
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PRICING_SYSTEM_PROMPT = """You are an expert market analyst specializing in sustainable goods,
upcycled crafts, and the circular economy. You analyze DIY upcycled products and provide
realistic market pricing based on:
- Material costs (cheap if from waste)
- Labor time and skill level
- Platform fees (Etsy, local markets)
- Comparable market trends for handmade sustainable items

Always be conservative and realistic. Never hallucinate — if something is simple, price it low.
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
    Calls OpenAI GPT to estimate a realistic resale price for the upcycled product.
    Optionally overrides labor hours for the advanced slider feature.
    """
    prompt = PRICING_PROMPT.format(
        project_name=upcycle_result.get("project_name", "Upcycled Item"),
        material=upcycle_result.get("material", "mixed material"),
        tagline=upcycle_result.get("tagline", ""),
        difficulty=upcycle_result.get("difficulty", "Medium"),
        time_estimate=upcycle_result.get("time_estimate", "2 hours"),
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PRICING_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,  # Low temp for consistent pricing
        response_format={"type": "json_object"},
    )
    
    result = json.loads(response.choices[0].message.content)
    
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
