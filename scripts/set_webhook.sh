#!/bin/bash
# ربط Webhook تيليغرام بالسيرفر
source /opt/botproject/.env.prod 2>/dev/null || { echo "❌ .env.prod غير موجود"; exit 1; }

echo "🔗 ربط Webhook..."
echo "   Bot: ${BOT_TOKEN:0:20}..."
echo "   Domain: $DOMAIN"
echo "   Secret: ${WEBHOOK_SECRET:0:8}..."

RESPONSE=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
    -d "url=https://${DOMAIN}/webhook/${WEBHOOK_SECRET}" \
    -d "max_connections=100" \
    -d "allowed_updates=[\"message\",\"callback_query\",\"inline_query\",\"pre_checkout_query\"]")

echo ""
echo "الرد من تيليغرام:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo ""
    echo "✅ Webhook مربوط بنجاح!"
else
    echo ""
    echo "❌ فشل ربط Webhook. تحقق من:"
    echo "   - BOT_TOKEN صحيح"
    echo "   - DOMAIN صحيح ويشير للسيرفر"
    echo "   - SSL يعمل: curl https://$DOMAIN/api/health"
fi

echo ""
echo "📊 معلومات Webhook الحالية:"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool 2>/dev/null
