from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from shared.db import get_db
from api.models import User
from api.auth import verify_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/users", tags=["users"])


class UserUpdate(BaseModel):
    plan:        str | None = None
    is_banned:   bool | None = None
    daily_limit: int | None = None
    lang:        str | None = None


@router.get("/")
async def list_users(
    page:   int = Query(1, ge=1),
    limit:  int = Query(50, le=200),
    search: str | None = None,
    plan:   str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    q = select(User).order_by(User.joined_at.desc())
    if search:
        q = q.where(or_(
            User.username.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%"),
        ))
    if plan:
        q = q.where(User.plan == plan)

    total  = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.offset((page - 1) * limit).limit(limit))
    users  = result.scalars().all()

    return {
        "total": total, "page": page,
        "users": [
            {"id": u.id, "telegram_id": u.telegram_id, "username": u.username,
             "full_name": u.full_name, "plan": u.plan, "downloads_total": u.downloads_total,
             "is_banned": u.is_banned, "lang": u.lang,
             "joined_at": str(u.joined_at), "last_seen": str(u.last_seen)}
            for u in users
        ],
    }


@router.patch("/{telegram_id}")
async def update_user(
    telegram_id: int, body: UserUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(verify_token),
):
    user = await db.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        raise HTTPException(404, "User not found")
    if body.plan is not None:        user.plan = body.plan
    if body.is_banned is not None:   user.is_banned = body.is_banned
    if body.daily_limit is not None: user.daily_limit = body.daily_limit
    if body.lang is not None:        user.lang = body.lang
    await db.commit()
    return {"ok": True}
