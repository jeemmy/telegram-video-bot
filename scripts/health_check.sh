#!/bin/bash
source /opt/botproject/.env.prod 2>/dev/null || true

DOMAIN="${DOMAIN:-localhost}"
OK=true

send_alert() {
    if [ -n "$BOT_TOKEN" ] && [ -n "$ADMIN_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
            -d "chat_id=${ADMIN_CHAT_ID}" \
            -d "text=🚨 تنبيه سيرفر: ${1}" > /dev/null
    fi
}

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        echo "  ✅ $name"
    else
        echo "  ❌ $name — FAILED"
        send_alert "${name} فشل"
        OK=false
    fi
}

echo "── فحص الخدمات ──"
check "API Health"      "curl -sf http://localhost:8000/api/health"
check "Nginx"           "docker compose -f /opt/botproject/docker-compose.yml exec nginx nginx -t"
check "PostgreSQL"      "docker compose -f /opt/botproject/docker-compose.yml exec postgres pg_isready"
check "Redis"           "docker compose -f /opt/botproject/docker-compose.yml exec redis redis-cli ping"
check "Worker Pro"      "docker compose -f /opt/botproject/docker-compose.yml ps worker_pro | grep -q Up"
check "Worker Free"     "docker compose -f /opt/botproject/docker-compose.yml ps worker_free | grep -q Up"

echo ""
if $OK; then
    echo "✅ كل الخدمات تعمل"
else
    echo "❌ بعض الخدمات فيها مشاكل"
    exit 1
fi
