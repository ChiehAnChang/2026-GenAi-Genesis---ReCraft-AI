"""
Analyze Agent — Step 1: Identifies the material and condition from an image.
Uses Qwen-VL via Hugging Face.
"""

import os
import base64
from openai import OpenAI
from .utils import parse_json

ANALYZE_PROMPT = """You are an expert material scientist. 
Analyze the image and provide a concise 1-sentence description of the material and its condition. 
Focus on what it is and any visible damage or unique features.

Respond with ONLY valid JSON:
{
  "material_name": "<specific material name>",
  "description": "<concise 1-sentence description>",
  "confidence": "<high|medium|low>"
}"""

def analyze_item(image_bytes: bytes) -> dict:
    """Stage 1: Get a concise description of the material from the image."""
    hf_client = OpenAI(
        api_key=os.getenv("HUGGINGFACE_API_KEY", ""),
        base_url="https://router.huggingface.co/v1"
    )
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    image_url = f"data:image/jpeg;base64,{base64_image}"

    response = hf_client.chat.completions.create(
        model="Qwen/Qwen2.5-VL-72B-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ANALYZE_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        max_tokens=300,
        temperature=0.1
    )
    
    raw = response.choices[0].message.content or ""
    return parse_json(raw)
