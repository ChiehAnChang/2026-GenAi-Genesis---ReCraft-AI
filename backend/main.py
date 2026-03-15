"""
FastAPI backend for ReCraft AI.
Handles: upcycling pipeline, pricing agent, and community marketplace.
"""

from __future__ import annotations

import os
import sys
import base64
import traceback
from typing import Any, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env when running locally (Replit uses Secrets instead)
load_dotenv()

# ── Ensure agents/ is importable regardless of working directory ──────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agents.upcycle_agent import run_pipeline
from agents.pricing_agent import estimate_price
from agents.image_agent import generate_product_image, edit_image_with_flux2
import auth

app = FastAPI(title="ReCraft AI API", version="1.0.0")

# ── CORS — allow Streamlit (any origin during hackathon) ──────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten to Streamlit URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Seeded synthetic data so the marketplace is never empty for judges
# ─────────────────────────────────────────────────────────────────────────────
def _seed_marketplace() -> list[dict]:
    return [
        {
            "id": "seed-1",
            "project_name": "Bottle Cap Mosaic Frame",
            "material": "Plastic bottle caps",
            "tagline": "A colourful mosaic picture frame made from 60+ salvaged bottle caps",
            "price": "$18 – $24",
            "recommended_price_usd": 21,
            "steps": ["Collect 60+ caps", "Arrange by colour", "Glue to cardboard frame", "Seal with varnish", "Add hanging hooks"],
            "image_url": None,
            "likes": 12,
        },
        {
            "id": "seed-2",
            "project_name": "Cardboard Desk Organiser",
            "material": "Corrugated cardboard box",
            "tagline": "Modular desk organiser with 6 compartments — zero glue, zero cost",
            "price": "$8 – $14",
            "recommended_price_usd": 11,
            "steps": ["Cut strips to height", "Score and fold dividers", "Slot dividers together", "Cover with kraft paper", "Label compartments"],
            "image_url": None,
            "likes": 7,
        },
        {
            "id": "seed-3",
            "project_name": "Glass Jar Terrarium",
            "material": "Glass mason jar",
            "tagline": "A self-sustaining mini ecosystem perfect for succulents",
            "price": "$22 – $35",
            "recommended_price_usd": 28,
            "steps": ["Add drainage pebbles", "Layer activated charcoal", "Add potting soil", "Plant succulents", "Mist lightly"],
            "image_url": None,
            "likes": 31,
        },
        {
            "id": "seed-4",
            "project_name": "T-Shirt Tote Bag",
            "material": "Old cotton t-shirt",
            "tagline": "No-sew reusable shopping bag from an old tee in under 15 minutes",
            "price": "$5 – $10",
            "recommended_price_usd": 7,
            "steps": ["Lay shirt flat", "Cut off sleeves", "Cut neckline wider", "Cut fringe at bottom", "Tie fringe knots to close"],
            "image_url": None,
            "likes": 19,
        },
    ]


# ── In-memory marketplace state (shared across all connections) ───────────────
_marketplace: list[dict] = _seed_marketplace()


# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────
class PriceRequest(BaseModel):
    upcycle_result: dict
    labor_hours: Optional[float] = None


class MarketplaceItem(BaseModel):
    project_name: str
    material: str
    tagline: str
    price: str
    recommended_price_usd: float
    steps: list[str]
    image_url: Optional[str] = None


class DIYGenerateRequest(BaseModel):
    material: str
    condition: str
    dimensions: str = "Standard size"
    original_image_b64: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ok", "service": "ReCraft AI API"}


@app.post("/api/identify")
async def identify(file: UploadFile = File(...)) -> dict[str, Any]:
    """Step 1: Identify material from image."""
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPG/PNG/WEBP images accepted.")
    
    image_bytes = await file.read()
    try:
        from agents.upcycle_agent import identify_material
        result = identify_material(image_bytes)
        # Include original image b64 for the next step (Flux-2)
        result["original_image_b64"] = base64.b64encode(image_bytes).decode()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Identification error: {str(e)}")


@app.post("/api/generate_diy")
async def generate_diy(req: DIYGenerateRequest) -> dict[str, Any]:
    """Step 2: Generate DIY plan from confirmed material + dimensions."""
    try:
        from agents.upcycle_agent import generate_diy_plan
        material_info = {"material": req.material, "condition": req.condition}
        result = generate_diy_plan(material_info, req.dimensions)
        
        # Add material/condition back to result for consistent UI
        result["material"] = req.material
        result["condition"] = req.condition
        result["dimensions"] = req.dimensions

        # Generate Flux-1 image
        flux_prompt = result.get("flux_image_prompt", f"Photorealistic {result.get('project_name', 'upcycled craft')}, studio lighting, product photography")
        result["image_url"] = generate_product_image(flux_prompt)

        # Generate Flux-2 contextual edit if original image provided
        if req.original_image_b64:
            edit_prompt = f"Transform this object into: {result.get('project_name')}. Keep the same lighting and environment. Photorealistic."
            result["edited_image_url"] = edit_image_with_flux2(req.original_image_b64, edit_prompt)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DIY Generation error: {str(e)}")


@app.post("/api/upcycle")
def upcycle(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Legacy UC1 endpoint: runs the full pipeline in one go.
    """
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPG/PNG/WEBP images accepted.")

    image_bytes = file.file.read()

    try:
        result = run_pipeline(image_bytes)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI pipeline error: {str(e)}")

    # Medium tier: generate Flux-1 photorealistic image
    flux_prompt = result.get("flux_image_prompt", f"Photorealistic {result.get('project_name', 'upcycled craft')}, studio lighting, product photography")
    image_url = generate_product_image(flux_prompt)
    result["image_url"] = image_url

    # Advanced tier: Flux-2 contextual edit of original photo
    original_b64 = base64.b64encode(image_bytes).decode()
    edit_prompt = f"Transform this object into: {result.get('project_name')}. Keep the same lighting and environment. Photorealistic."
    result["edited_image_url"] = edit_image_with_flux2(original_b64, edit_prompt)

    return result


@app.post("/api/price")
def get_price(request: PriceRequest) -> dict[str, Any]:
    """
    UC2: Accept upcycle result + optional labor_hours override →
    return structured JSON price estimate.
    """
    if not request.upcycle_result:
        raise HTTPException(status_code=400, detail="upcycle_result is required.")
    try:
        return estimate_price(request.upcycle_result, request.labor_hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pricing agent error: {str(e)}")


@app.get("/api/marketplace")
def get_marketplace() -> list[dict]:
    """UC3: Return all published marketplace items."""
    return _marketplace


@app.post("/api/marketplace")
def publish_to_marketplace(item: MarketplaceItem) -> dict:
    """UC3: Publish a new upcycled item to the shared marketplace."""
    import uuid
    new_item = item.model_dump()
    new_item["id"] = str(uuid.uuid4())
    new_item["likes"] = 0
    _marketplace.insert(0, new_item)  # newest first
    return {"status": "published", "id": new_item["id"]}


@app.post("/api/marketplace/{item_id}/like")
def like_item(item_id: str) -> dict:
    """Advanced UC3: Increment like count on a marketplace item."""
    for item in _marketplace:
        if item["id"] == item_id:
            item["likes"] = item.get("likes", 0) + 1
            return {"likes": item["likes"]}
    raise HTTPException(status_code=404, detail="Item not found.")


# ─────────────────────────────────────────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────────────────────────────────────────
class AuthRequest(BaseModel):
    username: str
    password: str
    email: str = ""


@app.post("/api/auth/register")
def register(req: AuthRequest) -> dict:
    try:
        return auth.register(req.username, req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
def login(req: AuthRequest) -> dict:
    try:
        return auth.login(req.username, req.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/auth/me")
def me(token: str) -> dict:
    user = auth.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return user


# ─────────────────────────────────────────────────────────────────────────────
# Saves routes
# ─────────────────────────────────────────────────────────────────────────────
class SaveRequest(BaseModel):
    token: str
    item: dict


@app.post("/api/saves")
def save_item(req: SaveRequest) -> dict:
    try:
        return auth.save_diy(req.token, req.item)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/saves")
def get_saves(token: str) -> list:
    try:
        return auth.get_saves(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.delete("/api/saves/{saved_id}")
def delete_save(saved_id: str, token: str) -> dict:
    try:
        deleted = auth.delete_save(token, saved_id)
        return {"deleted": deleted}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
