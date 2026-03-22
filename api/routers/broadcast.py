from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.db import get_db
from api.models import User, BroadcastLog
from api.auth import verify_token
from pydantic import BaseModel
from telegram import Bot
import os

router = APIRouter(prefix="/api/broadcast", tags=["broadcast"])
bot = Bot(token=os.getenv("BOT_TOKEN", ""))


class BroadcastRequest(BaseModel):
    message: str
    target:  str = "all"


async def _send(msg: str, target: str, log_id: int, db: AsyncSession):
    q = select(User.telegram_id).where(User.is_banned == False)
    if target == "pro":  q = q.where(User.plan == "pro")
    if target == "free": q = q.where(User.plan == "free")
    result = await db.execute(q)
    ids = [r[0] for r in result]
    sent = failed = 0
    for tg_id in ids:
        try:
            await bot.send_message(chat_id=tg_id, text=msg, parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
    log = await db.get(BroadcastLog, log_id)
    log.sent_count = sent; log.failed_count = failed; log.status = "done"
    await db.commit()


@router.post("/send")
async def send_broadcast(
    body: BroadcastRequest, background: BackgroundTasks,
    db: AsyncSession = Depends(get_db), _=Depends(verify_token),
):
    log = BroadcastLog(target=body.target, message_text=body.message, status="pending")
    db.add(log); await db.commit(); await db.refresh(log)
    background.add_task(_send, body.message, body.target, log.id, db)
    return {"ok": True, "log_id": log.id}


@router.get("/history")
async def history(db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    rows = await db.execute(select(BroadcastLog).order_by(BroadcastLog.created_at.desc()).limit(20))
    return [{"id": r.id, "target": r.target, "sent": r.sent_count,
             "failed": r.failed_count, "status": r.status, "at": str(r.created_at)}
            for r in rows.scalars()]
