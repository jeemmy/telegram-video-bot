import os
import asyncio
import uuid
from worker.celery_app import celery_app
from telegram import Bot

bot        = Bot(token=os.getenv("BOT_TOKEN", ""))
TEMP_DIR   = os.getenv("TEMP_DIR", "/tmp/downloads")


# ─── Single download ───────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10, name="worker.download_video")
def download_video_task(self, chat_id: int, url: str, quality: str, user_plan: str, lang: str = "ar"):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_single(self, chat_id, url, quality, user_plan, lang))
    finally:
        loop.close()


async def _run_single(task, chat_id, url, quality, user_plan, lang):
    from bot.utils.downloader import VideoDownloader
    from bot.utils.i18n import t
    downloader = VideoDownloader()
    file_path  = None

    status_msg = await bot.send_message(chat_id=chat_id, text=t("downloading", lang))

    try:
        info      = await downloader.get_info(url)
        title     = info.get("title", "فيديو")[:60]
        file_id   = str(uuid.uuid4())[:8]
        file_path = await downloader.download(url, quality, file_id)
        size_mb   = os.path.getsize(file_path) / (1024 * 1024)

        await bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id,
                                    text=t("uploading", lang))
        with open(file_path, "rb") as f:
            caption = t("success_caption", lang, title=title, size=f"{size_mb:.1f}")
            if quality == "audio":
                await bot.send_audio(chat_id=chat_id, audio=f, title=title, caption=caption)
            else:
                await bot.send_video(chat_id=chat_id, video=f, caption=caption, supports_streaming=True)

        await bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        await _log_download(chat_id, url, quality, size_mb, "success")

    except Exception as exc:
        err = str(exc).lower()
        if "too large" in err or "filesize" in err:
            msg = t("error_too_large", lang)
        elif "private" in err:
            msg = t("error_private", lang)
        else:
            msg = t("error_generic", lang)
        await bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=msg)
        await _log_download(chat_id, url, quality, 0, "failed", str(exc)[:200])
        if "network" in err or "timeout" in err:
            raise task.retry(exc=exc)
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


# ─── Bulk download ─────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=2, name="worker.bulk_download")
def bulk_download_task(self, chat_id: int, urls: list, quality: str, user_plan: str, lang: str = "ar"):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_bulk(self, chat_id, urls, quality, user_plan, lang))
    finally:
        loop.close()


async def _run_bulk(task, chat_id, urls, quality, user_plan, lang):
    from bot.utils.downloader import VideoDownloader
    downloader = VideoDownloader()
    total = len(urls)
    done  = failed = 0

    progress_msg = await bot.send_message(
        chat_id=chat_id,
        text=_progress_text(done, failed, total),
        parse_mode="Markdown",
    )

    for i, url in enumerate(urls, 1):
        file_path = None
        try:
            info  = await downloader.get_info(url)
            title = info.get("title", f"فيديو {i}")[:50]

            await bot.edit_message_text(
                chat_id=chat_id, message_id=progress_msg.message_id,
                text=_progress_text(done, failed, total, current=f"⬇️ {title}"),
                parse_mode="Markdown",
            )

            file_id   = f"bulk_{task.request.id}_{i}"
            file_path = await downloader.download(url, quality, file_id)
            size_mb   = os.path.getsize(file_path) / (1024 * 1024)

            with open(file_path, "rb") as f:
                caption = f"🎬 {title}\n📊 {size_mb:.1f} MB  •  {i}/{total}"
                if quality == "audio":
                    await bot.send_audio(chat_id=chat_id, audio=f, title=title, caption=caption)
                else:
                    await bot.send_video(chat_id=chat_id, video=f, caption=caption, supports_streaming=True)
            done += 1

        except Exception as e:
            failed += 1
            err = str(e).lower()
            reason = "حجم كبير" if "too large" in err else ("خاص" if "private" in err else "فشل")
            await bot.send_message(chat_id=chat_id,
                                   text=f"⚠️ رابط {i}/{total}: {reason}")
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

        await bot.edit_message_text(
            chat_id=chat_id, message_id=progress_msg.message_id,
            text=_progress_text(done, failed, total),
            parse_mode="Markdown",
        )

    emoji = "✅" if failed == 0 else ("⚠️" if done > 0 else "❌")
    await bot.edit_message_text(
        chat_id=chat_id, message_id=progress_msg.message_id,
        text=f"{emoji} *اكتمل التحميل المجمّع*\n\n✅ نجح: {done}/{total}" +
             (f"\n❌ فشل: {failed}/{total}" if failed else ""),
        parse_mode="Markdown",
    )


def _progress_bar(done: int, total: int) -> str:
    filled = int(done / total * 10) if total else 0
    return f"`{'█' * filled}{'░' * (10 - filled)}` {done}/{total}"


def _progress_text(done, failed, total, current=None):
    lines = [
        f"📦 *تحميل مجمّع* — {_progress_bar(done, total)}",
        f"✅ ناجح: {done}  •  ❌ فاشل: {failed}  •  ⏳ متبقي: {total-done-failed}",
    ]
    if current:
        lines.append(f"\n{current}")
    return "\n".join(lines)


# ─── DB logging ────────────────────────────────────────────────────

async def _log_download(chat_id, url, quality, size_mb, status, error=None):
    try:
        from shared.db import AsyncSessionLocal
        from api.models import Download, User
        from sqlalchemy import select

        platform = "other"
        for p in ["tiktok", "youtube", "instagram", "twitter"]:
            if p in url.lower():
                platform = p
                break

        async with AsyncSessionLocal() as db:
            user = await db.scalar(select(User).where(User.telegram_id == chat_id))
            dl = Download(
                user_id=user.id if user else 0,
                telegram_id=chat_id, url=url,
                platform=platform, quality=quality,
                file_size=round(size_mb, 2),
                status=status, error_msg=error,
            )
            db.add(dl)
            if user and status == "success":
                user.downloads_total += 1
            await db.commit()
    except Exception:
        pass
