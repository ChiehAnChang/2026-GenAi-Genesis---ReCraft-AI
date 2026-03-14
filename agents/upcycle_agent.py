"""
Upcycle Agent — Railtracks-style pipeline using Google Gemini multimodal.
Identifies waste material from an image and generates a DIY upcycling plan.
"""

import os
import base64
import json
import re
import google.generativeai as genai
from PIL import Image
import io

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


IDENTIFY_PROMPT = """You are an expert material scientist and sustainability consultant.
Analyze the uploaded image and identify:
1. The primary material (e.g. "HDPE plastic bottle", "corrugated cardboard box", "glass jar")
2. Its current condition (clean, dirty, broken, etc.)

Respond with ONLY valid JSON, no markdown fences:
{
  "material": "<specific material name>",
  "condition": "<brief condition description>",
  "confidence": "<high|medium|low>"
}"""

DIY_PROMPT = """You are a creative upcycling expert and sustainability educator.
Given this waste material: {material} ({condition})

Generate ONE brilliant upcycling DIY project. Respond with ONLY valid JSON, no markdown fences:
{{
  "project_name": "<catchy project name>",
  "tagline": "<one-line description of the upcycled product>",
  "difficulty": "<Easy|Medium|Hard>",
  "time_estimate": "<e.g. 2 hours>",
  "materials_needed": ["<additional item 1>", "<additional item 2>"],
  "steps": [
    "<Step 1: ...>",
    "<Step 2: ...>",
    "<Step 3: ...>",
    "<Step 4: ...>",
    "<Step 5: ...>"
  ],
  "sustainability_impact": "<one sentence on environmental benefit>",
  "flux_image_prompt": "<detailed prompt for Flux image generation, photorealistic, showing the finished upcycled product>"
}}"""


def _parse_json(text: str) -> dict:
    """Strips markdown fences and parses JSON robustly."""
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return json.loads(text)


def identify_material(image_bytes: bytes) -> dict:
    """Step 1: Send image to Gemini Vision to identify the waste material."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    image = Image.open(io.BytesIO(image_bytes))
    
    response = model.generate_content([IDENTIFY_PROMPT, image])
    return _parse_json(response.text)


def generate_diy_plan(material_info: dict) -> dict:
    """Step 2: Generate a 5-step DIY upcycling plan from identified material."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = DIY_PROMPT.format(
        material=material_info["material"],
        condition=material_info.get("condition", "good condition"),
    )
    response = model.generate_content(prompt)
    return _parse_json(response.text)


def run_pipeline(image_bytes: bytes) -> dict:
    """
    Full Upcycle Pipeline:
    image → identify material → generate DIY plan → return combined result
    """
    material_info = identify_material(image_bytes)
    diy_plan = generate_diy_plan(material_info)
    
    return {
        "material": material_info["material"],
        "condition": material_info.get("condition", ""),
        "confidence": material_info.get("confidence", "medium"),
        **diy_plan,
    }
