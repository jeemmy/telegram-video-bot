#!/bin/bash
source /opt/botproject/.env.prod 2>/dev/null || true

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M)

mkdir -p "$BACKUP_DIR"
echo "💾 بدء النسخ الاحتياطي — $DATE"

docker compose -f /opt/botproject/docker-compose.yml exec -T postgres pg_dump \
    -U "$POSTGRES_USER" "$POSTGRES_DB" \
    | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"
echo "  ✅ قاعدة البيانات: db_$DATE.sql.gz"

cp /opt/botproject/.env.prod "$BACKUP_DIR/env_$DATE.bak"
echo "  ✅ ملف البيئة"

find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.bak"    -mtime +7 -delete
echo "  🗑️ حُذفت النسخ القديمة (+7 أيام)"

echo "✅ النسخ الاحتياطي اكتمل"
