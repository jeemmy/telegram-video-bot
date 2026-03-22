import uuid
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.utils.downloader import VideoDownloader
from bot.utils.url_extractor import SUPPORTED_DOMAINS

downloader = VideoDownloader()


def is_url(text: str) -> bool:
    return text.startswith("http") and any(d in text for d in SUPPORTED_DOMAINS)


async def handle_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    text  = query.query.strip()

    if not text:
        await query.answer(
            results=[],
            switch_pm_text="أرسل رابط فيديو هنا...",
            switch_pm_parameter="inline_help",
            cache_time=0,
        )
        return

    if not is_url(text):
        await query.answer(
            results=[InlineQueryResultArticle(
                id="invalid",
                title="❌ رابط غير مدعوم",
                description="يدعم: TikTok · YouTube · Instagram · Twitter",
                input_message_content=InputTextMessageContent("❌ الرابط غير مدعوم"),
            )],
            cache_time=5,
        )
        return

    try:
        info     = await downloader.get_info(text)
        title    = info.get("title", "فيديو")[:60]
        thumb    = info.get("thumbnail", "")
        duration = info.get("duration", 0)
        platform = next((d.split(".")[0] for d in SUPPORTED_DOMAINS if d in text), "video")
        dur_str  = f"{duration//60}:{duration%60:02d}" if duration else ""
        desc     = f"{platform.title()} · {dur_str}" if dur_str else platform.title()

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "⬇️ تحميل في البوت",
                url=f"https://t.me/{context.bot.username}?start=dl_{uuid.uuid4().hex[:8]}"
            )
        ]])

        await query.answer(
            results=[InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"⬇️ {title}",
                description=desc,
                thumbnail_url=thumb or None,
                input_message_content=InputTextMessageContent(
                    f"🎬 *{title}*\n🔗 {text}", parse_mode="Markdown",
                ),
                reply_markup=keyboard,
            )],
            cache_time=30,
        )
    except Exception:
        await query.answer(
            results=[InlineQueryResultArticle(
                id="error",
                title="⚠️ تعذّر جلب معلومات الفيديو",
                description="جرّب فتح البوت مباشرة",
                input_message_content=InputTextMessageContent("⚠️ فشل جلب الفيديو"),
            )],
            cache_time=5,
        )
