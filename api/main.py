from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import login
from api.routers import stats, users, broadcast, settings
from shared.db import engine, Base
import os

app = FastAPI(title="BotPanel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"https://{os.getenv('DOMAIN','localhost')}", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.post("/api/auth/login")(login)
app.include_router(stats.router)
app.include_router(users.router)
app.include_router(broadcast.router)
app.include_router(settings.router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ API جاهز")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
