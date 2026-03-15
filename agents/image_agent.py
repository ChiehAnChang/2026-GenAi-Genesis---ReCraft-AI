"""
Image Generation Agent — uses a Hugging Face Inference Endpoint to generate
photorealistic images of the finished upcycled product.
Returns a base64 Data URI that can be directly displayed in the frontend.
"""

from __future__ import annotations
import os
import requests
import base64

# New Hugging Face Image Endpoint provided by user
HF_IMAGE_ENDPOINT = "https://jjx1c75qu4j1zt5s.us-east-1.aws.endpoints.huggingface.cloud"
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

def generate_product_image(prompt: str) -> str | None:
    """
    Calls the Hugging Face Inference Endpoint to generate an image.
    Uses the exact working payload structure provided by the user.
    """
    if not HUGGINGFACE_API_KEY:
        print("[ImageAgent] HUGGINGFACE_API_KEY is missing.")
        return None

    headers = {
        "Accept" : "image/png",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
    }
    
    # Matches the user's working snippet structure
    payload = {
        "inputs": prompt,
        "parameters": {}
    }

    try:
        response = requests.post(
            HF_IMAGE_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        # Convert bytes to base64 Data URI
        img_b64 = base64.b64encode(response.content).decode('utf-8')
        return f"data:image/png;base64,{img_b64}"
        
    except Exception as e:
        print(f"[ImageAgent] Hugging Face image generation failed: {e}")
        return None

def edit_image_with_flux2(original_image_b64: str, edit_prompt: str) -> str | None:
    """Legacy Flux-2 function — no longer active with HF migration."""
    return None
