from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
from shared.db import AsyncSessionLocal
from api.models import User
from sqlalchemy import select

PLANS = {
    "monthly": {"label": "BotPro شهري",        "price": 499,  "days": 30},
    "yearly":  {"label": "BotPro سنوي (وفر 40%)", "price": 2999, "days": 365},
}


async def send_invoice_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan_key = context.args[0] if context.args else "monthly"
    plan     = PLANS.get(plan_key, PLANS["monthly"])

    await update.message.reply_invoice(
        title=plan["label"],
        description=(
            "✅ تحميلات غير محدودة\n"
            "⚡ أولوية في قائمة الانتظار\n"
            "🚿 إزالة العلامة المائية\n"
            "🎵 استخراج صوت MP3\n"
            "📦 تحميل مجمّع حتى 10 روابط"
        ),
        payload=f"pro_{plan_key}_{update.effective_user.id}",
        currency="XTR",
        prices=[LabeledPrice(plan["label"], plan["price"])],
    )


async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def payment_success_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment  = update.message.successful_payment
    payload  = payment.invoice_payload
    user_id  = update.effective_user.id
    plan_key = payload.split("_")[1]
    days     = PLANS.get(plan_key, PLANS["monthly"])["days"]

    await _activate_pro(user_id, days)
    await update.message.reply_text(
        f"🎉 تم الاشتراك بنجاح!\n\n"
        f"✅ حسابك الآن Pro لمدة {days} يوم\n"
        f"⚡ استمتع بالتحميل غير المحدود!"
    )


async def _activate_pro(telegram_id: int, days: int):
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.telegram_id == telegram_id))
        if user:
            user.plan        = "pro"
            user.daily_limit = 0
            await db.commit()
