import os
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.downloader import VideoDownloader
from bot.utils.rate_limiter import check_limit, increment
from bot.utils.url_extractor import extract_urls, get_bulk_limit
from bot.utils.i18n import t, get_user_lang
from shared.db import AsyncSessionLocal
from api.models import User
from sqlalchemy import select

downloader = VideoDownloader()

SUPPORTED_DOMAINS = [
    "tiktok.com", "youtube.com", "youtu.be",
    "instagram.com", "twitter.com", "x.com",
]


def is_valid_url(text: str) -> bool:
    return text.startswith("http") and any(d in text for d in SUPPORTED_DOMAINS)


def quality_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_best",  lang), callback_data="quality:best"),
            InlineKeyboardButton(t("btn_1080",  lang), callback_data="quality:1080p"),
        ],
        [
            InlineKeyboardButton(t("btn_720",   lang), callback_data="quality:720p"),
            InlineKeyboardButton(t("btn_480",   lang), callback_data="quality:480p"),
        ],
        [InlineKeyboardButton(t("btn_audio", lang), callback_data="quality:audio")],
    ])


def bulk_quality_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_best",  lang), callback_data="bulk_q:best"),
            InlineKeyboardButton(t("btn_1080",  lang), callback_data="bulk_q:1080p"),
        ],
        [
            InlineKeyboardButton(t("btn_720",   lang), callback_data="bulk_q:720p"),
            InlineKeyboardButton(t("btn_480",   lang), callback_data="bulk_q:480p"),
        ],
        [InlineKeyboardButton(t("btn_audio", lang), callback_data="bulk_q:audio")],
    ])


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler موحّد: رابط واحد أو bulk"""
    text    = update.message.text.strip()
    user_id = update.effective_user.id
    lang    = await get_user_lang(user_id, update.effective_user.language_code)
    urls    = extract_urls(text)

    if not urls:
        await update.message.reply_text(t("unsupported_url", lang))
        return

    # رابط واحد
    if len(urls) == 1:
        allowed, remaining = check_limit(user_id)
        if not allowed:
            await update.message.reply_text(t("limit_reached", lang, limit=5))
            return
        context.user_data["pending_url"] = urls[0]
        context.user_data["bulk_mode"]   = False
        context.user_data["user_lang"]   = lang
        await update.message.reply_text(
            t("choose_quality", lang, remaining=remaining),
            reply_markup=quality_keyboard(lang),
        )
        return

    # Bulk mode
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.telegram_id == user_id))
        plan = user.plan if user else "free"

    limit    = get_bulk_limit(plan)
    urls     = urls[:limit]
    allowed, remaining = check_limit(user_id)
    if not allowed:
        await update.message.reply_text(t("limit_reached", lang, limit=5))
        return

    urls = urls[:min(len(urls), remaining)]
    context.user_data["bulk_urls"] = urls
    context.user_data["bulk_mode"] = True
    context.user_data["user_plan"] = plan
    context.user_data["user_lang"] = lang

    plan_label = "Pro 💎" if plan == "pro" else ("مجاني" if lang == "ar" else "Free")
    await update.message.reply_text(
        t("bulk_confirm", lang, count=len(urls), plan=plan_label),
        reply_markup=bulk_quality_keyboard(lang),
        parse_mode="Markdown",
    )


async def handle_quality_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بعد اختيار الجودة — رابط واحد"""
    query   = update.callback_query
    await query.answer()
    quality = query.data.split(":")[1]
    url     = context.user_data.get("pending_url")
    lang    = context.user_data.get("user_lang", "ar")
    user_id = update.effective_user.id

    if not url:
        await query.edit_message_text("❌ انتهت الجلسة، أعد إرسال الرابط.")
        return

    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.telegram_id == user_id))
        plan = user.plan if user else "free"

    queue    = "pro" if plan == "pro" else "free"
    priority = t("queue_priority_pro", lang) if plan == "pro" else t("queue_priority_free", lang)

    from worker.tasks import download_video_task
    download_video_task.apply_async(
        args=[update.effective_chat.id, url, quality, plan, lang],
        queue=queue,
        priority=10 if plan == "pro" else 5,
    )

    await query.edit_message_text(t("in_queue", lang, priority=priority))


async def handle_bulk_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بعد اختيار الجودة — bulk"""
    query   = update.callback_query
    await query.answer()
    quality = query.data.split(":")[1]
    lang    = context.user_data.get("user_lang", "ar")
    urls    = context.user_data.get("bulk_urls", [])
    plan    = context.user_data.get("user_plan", "free")
    user_id = update.effective_user.id

    if not urls:
        await query.edit_message_text("❌ انتهت الجلسة، أعد إرسال الروابط.")
        return

    queue = "pro" if plan == "pro" else "free"
    from worker.tasks import bulk_download_task
    bulk_download_task.apply_async(
        args=[update.effective_chat.id, urls, quality, plan, lang],
        queue=queue,
        priority=10 if plan == "pro" else 5,
    )

    for _ in urls:
        increment(user_id)

    queue_label = t("bulk_queue_pro", lang) if plan == "pro" else t("bulk_queue_free", lang)
    await query.edit_message_text(
        t("bulk_queued", lang, count=len(urls), queue=queue_label)
    )
