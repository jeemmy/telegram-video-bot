#!/bin/bash
set -e

PROJECT_DIR="/opt/botproject"
COMPOSE="docker compose -f docker-compose.yml"
LOG="deploy_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 بدء النشر — $(date)" | tee -a "$LOG"
cd "$PROJECT_DIR"

echo "📥 سحب الكود..." | tee -a "$LOG"
git pull origin main 2>&1 | tee -a "$LOG"

echo "🔨 بناء الصور..." | tee -a "$LOG"
$COMPOSE build --no-cache api bot worker_pro worker_free 2>&1 | tee -a "$LOG"

echo "🗃️ تحديث قاعدة البيانات..." | tee -a "$LOG"
$COMPOSE run --rm api python -c "
import asyncio
from shared.db import engine, Base
async def migrate():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(migrate())
print('✅ DB جاهز')
" 2>&1 | tee -a "$LOG"

echo "🔄 تحديث الخدمات..." | tee -a "$LOG"
$COMPOSE up -d --no-deps api
sleep 5
$COMPOSE up -d --no-deps bot
sleep 3
$COMPOSE up -d --no-deps worker_pro worker_free
$COMPOSE up -d --no-deps nginx

echo "🩺 فحص الخدمات..." | tee -a "$LOG"
sleep 10
bash scripts/health_check.sh 2>&1 | tee -a "$LOG"

echo "✅ النشر اكتمل — $(date)" | tee -a "$LOG"
