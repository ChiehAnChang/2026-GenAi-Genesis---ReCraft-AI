"""
Image Generation Agent — calls Flux-1 to generate a photorealistic image
of the finished upcycled product based on the AI-generated prompt.
Falls back gracefully if Flux is unavailable.
"""

from __future__ import annotations

import os
import time
import httpx

FLUX_API_URL = os.getenv("FLUX_API_URL", "https://api.bfl.ml/v1")
FLUX_API_KEY = os.getenv("FLUX_API_KEY", "")


def generate_product_image(flux_prompt: str, width: int = 1024, height: int = 768) -> str | None:
    """
    Calls Flux-1 schnell to generate a photorealistic image of the upcycled product.
    Returns a public image URL, or None on failure.
    
    Flux API pattern: POST to submit → poll for result URL.
    """
    if not FLUX_API_KEY:
        return None

    headers = {
        "x-key": FLUX_API_KEY,
        "Content-Type": "application/json",
    }

    # Step 1: Submit generation job
    try:
        resp = httpx.post(
            f"{FLUX_API_URL}/flux-pro-1.1",
            headers=headers,
            json={
                "prompt": flux_prompt,
                "width": width,
                "height": height,
                "steps": 20,
                "guidance": 3.5,
                "output_format": "jpeg",
            },
            timeout=30,
        )
        resp.raise_for_status()
        task_id = resp.json().get("id")
    except Exception as e:
        print(f"[ImageAgent] Flux submit failed: {e}")
        return None

    if not task_id:
        return None

    # Step 2: Poll for result (max 60 seconds)
    for _ in range(30):
        time.sleep(2)
        try:
            poll = httpx.get(
                f"{FLUX_API_URL}/get_result",
                headers=headers,
                params={"id": task_id},
                timeout=10,
            )
            data = poll.json()
            status = data.get("status")
            if status == "Ready":
                return data.get("result", {}).get("sample")
            elif status in ("Error", "Failed"):
                return None
        except Exception:
            continue

    return None  # Timeout


def edit_image_with_flux2(original_image_b64: str, edit_prompt: str) -> str | None:
    """
    Advanced: Uses Flux-2 (flux-kontext-pro) to contextually edit the user's
    original photo into the upcycled product in the same environment.
    Returns image URL or None.
    """
    if not FLUX_API_KEY:
        return None

    headers = {
        "x-key": FLUX_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        resp = httpx.post(
            f"{FLUX_API_URL}/flux-kontext-pro",
            headers=headers,
            json={
                "prompt": edit_prompt,
                "input_image": original_image_b64,
                "output_format": "jpeg",
            },
            timeout=30,
        )
        resp.raise_for_status()
        task_id = resp.json().get("id")
    except Exception as e:
        print(f"[ImageAgent] Flux-2 submit failed: {e}")
        return None

    if not task_id:
        return None

    for _ in range(30):
        time.sleep(2)
        try:
            poll = httpx.get(
                f"{FLUX_API_URL}/get_result",
                headers=headers,
                params={"id": task_id},
                timeout=10,
            )
            data = poll.json()
            if data.get("status") == "Ready":
                return data.get("result", {}).get("sample")
            elif data.get("status") in ("Error", "Failed"):
                return None
        except Exception:
            continue

    return None
