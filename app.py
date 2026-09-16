import os
import json
import hmac
import hashlib
from urllib.parse import parse_qsl
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import database as db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.init_db()


def validate_init_data(init_data: str):
    """Проверка подписи initData от Telegram."""
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if calculated_hash != received_hash:
            return None

        user = json.loads(parsed.get("user", "{}"))
        return user
    except Exception:
        return None


class LoadRequest(BaseModel):
    initData: str


class SaveRequest(BaseModel):
    initData: str
    data: dict


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/load")
async def api_load(req: LoadRequest):
    user = validate_init_data(req.initData)
    if not user or not user.get("id"):
        raise HTTPException(403, "Invalid initData")

    user_id = user["id"]
    await db.upsert_user(user_id, user.get("first_name", ""), user.get("username", ""))
    data = await db.load_user_data(user_id)
    return {"data": data}


@app.post("/api/save")
async def api_save(req: SaveRequest):
    user = validate_init_data(req.initData)
    if not user or not user.get("id"):
        raise HTTPException(403, "Invalid initData")

    user_id = user["id"]
    await db.upsert_user(user_id, user.get("first_name", ""), user.get("username", ""))
    await db.save_user_data(user_id, req.data)
    return {"ok": True}