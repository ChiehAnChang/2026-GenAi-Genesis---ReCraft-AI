"""
Upcycle Agent — Two-model pipeline:
  Step 1 (identify_material): Google Gemini 2.0 Flash — multimodal vision (new SDK)
  Step 2 (generate_diy_plan): gpt-oss-120b via HuggingFace vLLM endpoint
"""

import os
import json
import re
import base64
from openai import OpenAI
from PIL import Image
import io

# gpt-oss client for DIY plan generation
GPT_OSS_BASE_URL = os.getenv(
    "GPT_OSS_BASE_URL",
    "https://vjioo4r1vyvcozuj.us-east-2.aws.endpoints.huggingface.cloud/v1",
)
gpt_oss_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "test"),
    base_url=GPT_OSS_BASE_URL,
)

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
Dimensions: {dimensions}

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
    """Step 1: Send image to Qwen-VL via Hugging Face to identify the waste material."""
    hf_client = OpenAI(
        api_key=os.getenv("HUGGINGFACE_API_KEY", ""),
        base_url="https://router.huggingface.co/v1"
    )
    
    # Convert image to base64 for the OpenAI-compatible vision payload
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    image_url = f"data:image/jpeg;base64,{base64_image}"

    response = hf_client.chat.completions.create(
        model="Qwen/Qwen2.5-VL-72B-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": IDENTIFY_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        max_tokens=500,
        temperature=0.1
    )
    
    raw = response.choices[0].message.content or ""
    return _parse_json(raw)


def generate_diy_plan(material_info: dict, dimensions: str = "Standard size") -> dict:
    """Step 2: Generate a 5-step DIY upcycling plan using gpt-oss-120b."""
    prompt = DIY_PROMPT.format(
        material=material_info["material"],
        condition=material_info.get("condition", "good condition"),
        dimensions=dimensions
    )
    response = gpt_oss_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a creative upcycling expert. Always respond with valid JSON only, no markdown."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=1024,  # gpt-oss needs room for chain-of-thought reasoning
    )
    raw = response.choices[0].message.content or ""
    return _parse_json(raw)


def run_pipeline(image_bytes: bytes) -> dict:
    """
    Full Upcycle Pipeline:
    image → identify material (Gemini Vision) → generate DIY plan (gpt-oss) → return combined result
    """
    material_info = identify_material(image_bytes)
    diy_plan = generate_diy_plan(material_info)

    return {
        "material": material_info["material"],
        "condition": material_info.get("condition", ""),
        "confidence": material_info.get("confidence", "medium"),
        **diy_plan,
    }
