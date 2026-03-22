import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    CallbackQueryHandler, InlineQueryHandler,
    PreCheckoutQueryHandler, filters,
)
from bot.handlers.download import handle_message, handle_quality_choice, handle_bulk_quality
from bot.handlers.inline import handle_inline
from bot.handlers.settings_cmd import settings_cmd, handle_lang_change
from payments.stars import send_invoice_stars, pre_checkout, payment_success_stars
from payments.referral import handle_referral, get_referral_link
from shared.db import AsyncSessionLocal
from api.models import User
from sqlalchemy import select
from config import BOT_TOKEN, ENV, DOMAIN, WEBHOOK_SECRET


async def start(update: Update, context):
    args    = context.args
    user    = update.effective_user
    user_id = user.id

    # تسجيل المستخدم في DB إذا لم يكن موجوداً
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.telegram_id == user_id))
        if not existing:
            new_user = User(
                telegram_id=user_id,
                username=user.username,
                full_name=user.full_name,
                lang=user.language_code[:2] if user.language_code else "ar",
            )
            db.add(new_user)
            await db.commit()

    # معالجة الإحالة
    if args and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0].replace("ref_", ""))
            await handle_referral(user_id, referrer_id)
        except ValueError:
            pass

    name = user.first_name or "صديق"
    await update.message.reply_text(
        f"مرحباً {name}! 👋\n\n"
        "أرسل رابط فيديو من TikTok أو YouTube أو Instagram وسأحمّله لك فوراً.\n\n"
        "💎 /pro — اشترك في Pro\n"
        "🔗 /referral — رابط الإحالة\n"
        "⚙️ /settings — إعداداتك"
    )


async def referral_cmd(update: Update, context):
    bot_username = (await context.bot.get_me()).username
    link = await get_referral_link(update.effective_user.id, bot_username)
    await update.message.reply_text(
        f"🔗 رابط الإحالة الخاص بك:\n{link}\n\n"
        "كل صديق ينضم عبر رابطك = 3 تحميلات مجانية إضافية لك!"
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("pro",      send_invoice_stars))
    app.add_handler(CommandHandler("referral", referral_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))

    # Messages — رابط واحد أو bulk
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r"https?://"),
        handle_message,
    ))

    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_quality_choice, pattern="^quality:"))
    app.add_handler(CallbackQueryHandler(handle_bulk_quality,   pattern="^bulk_q:"))
    app.add_handler(CallbackQueryHandler(handle_lang_change,    pattern="^setlang:"))

    # Inline mode
    app.add_handler(InlineQueryHandler(handle_inline))

    # Payments
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success_stars))

    print("✅ البوت يعمل...")

    if ENV == "production":
        # Webhook mode
        app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            webhook_path=f"/webhook/{WEBHOOK_SECRET}",
            webhook_url=f"https://{DOMAIN}/webhook/{WEBHOOK_SECRET}",
        )
    else:
        # Polling للتطوير
        app.run_polling()


if __name__ == "__main__":
    main()
