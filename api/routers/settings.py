from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.db import get_db
from api.models import BotSetting
from api.auth import verify_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/settings", tags=["settings"])

DEFAULTS = {
    "daily_limit_free":  "5",
    "max_file_mb":       "50",
    "default_quality":   "720p",
    "welcome_msg":       "مرحباً {name}! أرسل رابط الفيديو 🎬",
    "maintenance":       "false",
    "platform_tiktok":   "true",
    "platform_youtube":  "true",
    "platform_instagram":"true",
    "platform_twitter":  "false",
    "pro_price_usd":     "4.99",
    "referral_bonus_referrer": "3",
    "referral_bonus_referred": "1",
    "referral_daily_max":      "20",
    "bulk_limit_free":   "3",
    "bulk_limit_pro":    "10",
}


class SettingsUpdate(BaseModel):
    settings: dict[str, str]


@router.get("/")
async def get_settings(db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    rows = await db.execute(select(BotSetting))
    db_s = {r.key: r.value for r in rows.scalars()}
    return {**DEFAULTS, **db_s}


@router.put("/")
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(verify_token),
):
    for key, value in body.settings.items():
        existing = await db.scalar(select(BotSetting).where(BotSetting.key == key))
        if existing:
            existing.value = value
        else:
            db.add(BotSetting(key=key, value=value))
    await db.commit()
    return {"ok": True, "updated": list(body.settings.keys())}
