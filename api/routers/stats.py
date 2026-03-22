from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from datetime import date, timedelta
from shared.db import get_db
from api.models import User, Download
from api.auth import verify_token

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    today = date.today()
    total_users     = await db.scalar(select(func.count(User.id)))
    pro_users       = await db.scalar(select(func.count(User.id)).where(User.plan == "pro"))
    downloads_today = await db.scalar(
        select(func.count(Download.id)).where(cast(Download.created_at, Date) == today)
    )
    success_today = await db.scalar(
        select(func.count(Download.id))
        .where(cast(Download.created_at, Date) == today)
        .where(Download.status == "success")
    )
    return {
        "total_users":     total_users,
        "pro_users":       pro_users,
        "downloads_today": downloads_today,
        "success_rate":    round(success_today / max(downloads_today, 1) * 100, 1),
        "revenue_usd":     round(pro_users * 4.99, 2),
    }


@router.get("/weekly")
async def get_weekly(db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    rows = await db.execute(
        select(cast(Download.created_at, Date).label("day"), func.count(Download.id).label("count"))
        .where(Download.created_at >= date.today() - timedelta(days=7))
        .group_by("day").order_by("day")
    )
    return [{"date": str(r.day), "count": r.count} for r in rows]


@router.get("/platforms")
async def get_platforms(db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    rows = await db.execute(
        select(Download.platform, func.count(Download.id).label("count"))
        .group_by(Download.platform).order_by(func.count(Download.id).desc())
    )
    data = [{"platform": r.platform, "count": r.count} for r in rows]
    total = sum(d["count"] for d in data)
    for d in data:
        d["pct"] = round(d["count"] / max(total, 1) * 100, 1)
    return data
