from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.i18n import t, get_user_lang
from shared.db import AsyncSessionLocal
from api.models import User
from sqlalchemy import select

LANGS = {"ar": "🇸🇦 العربية", "en": "🇬🇧 English", "fr": "🇫🇷 Français"}


async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang    = await get_user_lang(user_id, update.effective_user.language_code)

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(label, callback_data=f"setlang:{code}")
        for code, label in LANGS.items()
    ]])

    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.telegram_id == user_id))
        plan  = user.plan if user else "free"
        used  = 0   # يمكن ربطه بـ rate_limiter
        limit = user.daily_limit if user else 5

    await update.message.reply_text(
        t("settings_title", lang) + "\n\n" +
        t("settings_body", lang, plan=plan, used=used, limit=limit if limit else "∞", lang=lang) +
        "\n\n" + t("btn_change_lang", lang) + ":",
        reply_markup=keyboard,
    )


async def handle_lang_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    new_lang = query.data.split(":")[1]
    user_id  = update.effective_user.id

    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.telegram_id == user_id))
        if user:
            user.lang = new_lang
            await db.commit()

    await query.edit_message_text(t("lang_changed", new_lang))
