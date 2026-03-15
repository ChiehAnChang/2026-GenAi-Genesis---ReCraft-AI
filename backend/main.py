"""
FastAPI backend for ReCraft AI.
Handles: upcycling pipeline, pricing agent, community marketplace, auth, chat.
"""

from __future__ import annotations

import json
import os
import sys
import base64
import traceback
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agents.analyze_agent import analyze_item
from agents.upcycle_agent import generate_top_3_plans, generate_diy_plan, run_pipeline
from agents.pricing_agent import estimate_price
from agents.image_agent import generate_product_image, edit_image_with_flux2

# ── Init DB first — must run before auth.py is imported (auth seeds test user on import) ──
try:
    from database import get_conn, init_db, seed_marketplace_if_empty
except ImportError:
    from backend.database import get_conn, init_db, seed_marketplace_if_empty

init_db()

try:
    import auth
except ImportError:
    from backend import auth

seed_marketplace_if_empty()

app = FastAPI(title="ReCraft AI API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────
class GeneratePlansRequest(BaseModel):
    description: str
    dimensions: str = "Standard size"


class PriceRequest(BaseModel):
    upcycle_result: dict
    labor_hours: Optional[float] = None


class MarketplaceItem(BaseModel):
    project_name: str
    material: str
    tagline: str
    price: str
    recommended_price_usd: float
    steps: List[str]
    image_url: Optional[str] = None
    image_b64: Optional[str] = None


class DIYGenerateRequest(BaseModel):
    material: str
    condition: str
    dimensions: str = "Standard size"
    original_image_b64: Optional[str] = None


class AuthRequest(BaseModel):
    username: str
    password: str
    email: str = ""


class SaveRequest(BaseModel):
    token: str
    item: dict


class ChatMessage(BaseModel):
    token: str
    msg_type: str = "text"   # text | image | link | price_ask
    content: Optional[str] = None
    image_b64: Optional[str] = None
    link_url: Optional[str] = None
    reply_to_id: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ok", "service": "ReCraft AI API"}


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Analyze / Identify
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Step 1: Identify material from image using Qwen-VL."""
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPG/PNG/WEBP images accepted.")
    image_bytes = await file.read()
    try:
        result = analyze_item(image_bytes)
        result["original_image_b64"] = base64.b64encode(image_bytes).decode()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.post("/api/identify")
async def identify(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Alias for /api/analyze — backward compatibility."""
    return await analyze(file)


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Generate Plans
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/generate-plans")
async def generate_plans(req: GeneratePlansRequest) -> Dict[str, Any]:
    """Step 2: Generate 3 DIY plans + Flux images. Returns {plans: [...]}."""
    try:
        plans = generate_top_3_plans(req.description, req.dimensions)

        # Generate a Flux image for each plan
        for plan in plans:
            flux_prompt = plan.get(
                "flux_image_prompt",
                f"Photorealistic {plan.get('project_name', 'upcycled craft')}, studio lighting, product photography"
            )
            try:
                plan["image_url"] = generate_product_image(flux_prompt)
            except Exception:
                plan["image_url"] = None

        return {"plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation error: {str(e)}")


@app.post("/api/generate_diy")
async def generate_diy(req: DIYGenerateRequest) -> Dict[str, Any]:
    """Single-plan endpoint — backward compatibility with older frontend."""
    try:
        material_info = {"material": req.material, "condition": req.condition}
        result = generate_diy_plan(material_info, req.dimensions)

        result["material"] = req.material
        result["condition"] = req.condition
        result["dimensions"] = req.dimensions

        flux_prompt = result.get(
            "flux_image_prompt",
            f"Photorealistic {result.get('project_name', 'upcycled craft')}, studio lighting, product photography"
        )
        result["image_url"] = generate_product_image(flux_prompt)

        if req.original_image_b64:
            edit_prompt = f"Transform this object into: {result.get('project_name')}. Keep the same lighting and environment. Photorealistic."
            result["edited_image_url"] = edit_image_with_flux2(req.original_image_b64, edit_prompt)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DIY Generation error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Pricing
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/price")
def get_price(request: PriceRequest) -> Dict[str, Any]:
    if not request.upcycle_result:
        raise HTTPException(status_code=400, detail="upcycle_result is required.")
    try:
        return estimate_price(request.upcycle_result, request.labor_hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pricing agent error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Marketplace (SQLite-backed)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/marketplace")
def get_marketplace() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM marketplace ORDER BY likes DESC").fetchall()
    return [{**dict(r), "steps": json.loads(r["steps_json"])} for r in rows]


@app.post("/api/marketplace")
def publish_to_marketplace(item: MarketplaceItem) -> dict:
    import uuid
    new_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO marketplace
               (id, project_name, material, tagline, price, recommended_price_usd,
                steps_json, image_url, image_b64, likes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (new_id, item.project_name, item.material, item.tagline,
             item.price, item.recommended_price_usd,
             json.dumps(item.steps), item.image_url, item.image_b64),
        )
    return {"status": "published", "id": new_id}


@app.post("/api/marketplace/{item_id}/like")
def like_item(item_id: str) -> dict:
    with get_conn() as conn:
        conn.execute("UPDATE marketplace SET likes = likes + 1 WHERE id = ?", (item_id,))
        row = conn.execute("SELECT likes FROM marketplace WHERE id = ?", (item_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found.")
    return {"likes": row["likes"]}


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────
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
# Saves
# ─────────────────────────────────────────────────────────────────────────────
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
# Community Chat
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/chat")
def get_chat(limit: int = 50) -> list:
    """Return latest chat messages with reply context."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()

    messages = [dict(r) for r in reversed(rows)]

    ids = {m["id"]: m for m in messages}
    for m in messages:
        if m.get("reply_to_id") and m["reply_to_id"] in ids:
            parent = ids[m["reply_to_id"]]
            m["reply_preview"] = {
                "username": parent["username"],
                "content": (parent.get("content") or "")[:80],
                "msg_type": parent["msg_type"],
            }
        else:
            m["reply_preview"] = None

    return messages


@app.post("/api/chat")
def post_chat(msg: ChatMessage) -> dict:
    """Post a new chat message."""
    import uuid

    username = auth._tokens.get(msg.token)
    if not username:
        raise HTTPException(status_code=401, detail="Not logged in.")

    with get_conn() as conn:
        user = conn.execute(
            "SELECT avatar_emoji FROM users WHERE username = ?", (username,)
        ).fetchone()
        avatar = user["avatar_emoji"] if user else "🌱"

        if msg.reply_to_id:
            exists = conn.execute(
                "SELECT 1 FROM chat_messages WHERE id = ?", (msg.reply_to_id,)
            ).fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail="Reply target not found.")

        msg_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO chat_messages
               (id, username, avatar_emoji, msg_type, content, image_b64, link_url, reply_to_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, username, avatar, msg.msg_type,
             msg.content, msg.image_b64, msg.link_url, msg.reply_to_id),
        )

    return {"id": msg_id}


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
