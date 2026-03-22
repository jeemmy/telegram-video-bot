#!/bin/bash
# سكريبت الإعداد الأول للسيرفر — شغّله مرة واحدة فقط
set -e

DOMAIN="${1:-yourdomain.com}"
EMAIL="${2:-admin@yourdomain.com}"
PROJECT_DIR="/opt/botproject"

echo "🚀 إعداد السيرفر لـ $DOMAIN"

# ── 1. تحديث النظام ──
echo "📦 تحديث النظام..."
apt update && apt upgrade -y
apt install -y git curl ufw htop nano certbot

# ── 2. تثبيت Docker ──
echo "🐳 تثبيت Docker..."
curl -fsSL https://get.docker.com | sh
systemctl enable docker
apt install -y docker-compose-v2
echo "  ✅ Docker $(docker --version)"

# ── 3. جدار الحماية ──
echo "🔒 إعداد جدار الحماية..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable
echo "  ✅ UFW مفعّل"

# ── 4. مجلدات ──
echo "📁 إنشاء المجلدات..."
mkdir -p /tmp/downloads
mkdir -p /var/www/dashboard
mkdir -p /var/www/certbot
mkdir -p /opt/backups
chmod 777 /tmp/downloads

# ── 5. SSL ──
echo "🔐 الحصول على شهادة SSL لـ $DOMAIN..."
certbot certonly --standalone \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive
echo "  ✅ SSL جاهز"

# ── 6. Cron Jobs ──
echo "⏰ إعداد المهام المجدولة..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $PROJECT_DIR && bash scripts/backup.sh >> /var/log/bot-backup.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "*/5 * * * * cd $PROJECT_DIR && bash scripts/health_check.sh >> /var/log/bot-health.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 4 * * 0 docker compose -f $PROJECT_DIR/docker-compose.yml exec -T bot pip install -U yt-dlp >> /var/log/ytdlp-update.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && docker compose -f $PROJECT_DIR/docker-compose.yml exec nginx nginx -s reload") | crontab -
echo "  ✅ Cron jobs مضافة"

echo ""
echo "════════════════════════════════════"
echo "✅ السيرفر جاهز!"
echo ""
echo "الخطوات التالية:"
echo "  1. cd $PROJECT_DIR"
echo "  2. cp .env.example .env.prod && nano .env.prod"
echo "  3. sed -i 's/yourdomain.com/$DOMAIN/g' nginx/conf.d/bot.conf"
echo "  4. docker compose up -d --build"
echo "════════════════════════════════════"
