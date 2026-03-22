from sqlalchemy import select
from shared.db import AsyncSessionLocal
from api.models import User, Referral
from telegram import Bot
import os

bot = Bot(token=os.getenv("BOT_TOKEN", ""))


async def handle_referral(new_user_id: int, referrer_id: int):
    """يُستدعى عند انضمام مستخدم جديد عبر رابط إحالة"""
    if new_user_id == referrer_id:
        return

    async with AsyncSessionLocal() as db:
        # منع الإحالة المزدوجة
        existing = await db.scalar(
            select(Referral).where(Referral.referred_id == new_user_id)
        )
        if existing:
            return

        referral = Referral(referrer_id=referrer_id, referred_id=new_user_id)
        db.add(referral)

        # مكافأة المحيل
        referrer = await db.scalar(select(User).where(User.telegram_id == referrer_id))
        bonus = 3
        if referrer and referrer.plan == "free":
            referrer.daily_limit = min((referrer.daily_limit or 5) + bonus, 20)
            referral.bonus_given = bonus

        await db.commit()

    # إشعار المحيل
    try:
        await bot.send_message(
            chat_id=referrer_id,
            text=f"🎁 صديق انضم عبر رابطك! حصلت على {bonus} تحميلات إضافية."
        )
    except Exception:
        pass


async def get_referral_link(telegram_id: int, bot_username: str) -> str:
    return f"https://t.me/{bot_username}?start=ref_{telegram_id}"
