"""
FastAPI backend for ReCraft AI.
Handles: upcycling pipeline, pricing agent, and community marketplace.
"""

from __future__ import annotations

import os
import sys
import base64
import traceback
from typing import Any, Optional, List, Dict

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env when running locally
load_dotenv()

# ── Ensure agents/ is importable regardless of working directory ──────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agents.analyze_agent import analyze_item
from agents.upcycle_agent import generate_top_3_plans
from agents.pricing_agent import estimate_price
from agents.image_agent import generate_product_image, edit_image_with_flux2

try:
    import auth
except ImportError:
    from backend import auth

app = FastAPI(title="ReCraft AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Seeded synthetic data ─────────────────────────────────────────────────────
def _seed_marketplace() -> List[Dict[str, Any]]:
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
        }
    ]

_marketplace: List[Dict[str, Any]] = _seed_marketplace()

# ── Models (Python 3.9 Compatible) ───────────────────────────────────────────
class PriceRequest(BaseModel):
    upcycle_result: Dict[str, Any]
    labor_hours: Optional[float] = None

class AnalysisResponse(BaseModel):
    material_name: str
    description: str
    confidence: str

class GeneratePlansRequest(BaseModel):
    description: str
    dimensions: str

class ProjectPlan(BaseModel):
    project_name: str
    tagline: str
    difficulty: str
    time_estimate: str
    materials_needed: List[str]
    steps: List[str]
    sustainability_impact: str
    co2_saved_kg: float
    flux_image_prompt: str
    image_url: Optional[str] = None
    price_estimate: Optional[Dict[str, Any]] = None

class MultiPlanResponse(BaseModel):
    plans: List[ProjectPlan]

class UserAuth(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class MarketplaceItem(BaseModel):
    project_name: str
    material: str
    tagline: str
    price: str
    recommended_price_usd: float
    steps: List[str]
    image_url: Optional[str] = None

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ok", "service": "ReCraft AI API"}

@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze(file: UploadFile = File(...)):
    """Stage 1: Analyze image to get material description."""
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPG/PNG/WEBP images accepted.")
    
    image_bytes = file.file.read()
    try:
        result = analyze_item(image_bytes)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-plans", response_model=MultiPlanResponse)
def generate_plans(req: GeneratePlansRequest):
    """Stage 2: Generate 3 DIY plans with pricing and images."""
    try:
        plans_data = generate_top_3_plans(req.description, req.dimensions)
        plans = []
        for p in plans_data:
            # Enrichment
            try:
                p["image_url"] = generate_product_image(p["flux_image_prompt"])
                p["price_estimate"] = estimate_price(p)
            except Exception as inner_e:
                print(f"[Backend] Enrichment error for {p.get('project_name')}: {inner_e}")
            
            plans.append(ProjectPlan(**p))
        
        return MultiPlanResponse(plans=plans)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/price")
def get_price(request: PriceRequest) -> Dict[str, Any]:
    """Fallback/Legacy endpoint for manual price estimates."""
    try:
        return estimate_price(request.upcycle_result, labor_hours=request.labor_hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/marketplace")
def post_to_marketplace(item: MarketplaceItem):
    new_item = item.dict()
    new_item["id"] = f"mkt-{len(_marketplace) + 1}"
    new_item["likes"] = 0
    _marketplace.insert(0, new_item)
    return {"status": "success", "id": new_item["id"]}

@app.get("/api/marketplace")
def get_marketplace():
    return _marketplace

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/api/auth/register")
def register(user: UserAuth):
    try:
        return auth.register(user.username, user.email or "", user.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
def login(user: UserAuth):
    try:
        return auth.login(user.username, user.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/api/auth/me")
def get_me(token: str):
    user = auth.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@app.post("/api/saves")
def save_item(req: Dict[str, Any]):
    try:
        return auth.save_diy(req["token"], req["item"])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/api/saves")
def get_saves(token: str):
    try:
        return auth.get_saves(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.delete("/api/saves/{saved_id}")
def delete_save(saved_id: str, token: str):
    try:
        if auth.delete_save(token, saved_id):
            return {"status": "success"}
        raise HTTPException(status_code=404, detail="Item not found")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
