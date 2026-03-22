# 🤖 TikTok Downloader Bot

بوت تيليغرام متكامل لتحميل مقاطع الفيديو من TikTok وYouTube وInstagram وTwitter، مع لوحة تحكم ويب للأدمن.

---

## 📁 هيكل المشروع

```
botproject/
├── bot/
│   ├── main.py                  ← نقطة تشغيل البوت
│   ├── handlers/
│   │   ├── download.py          ← استقبال الروابط + bulk
│   │   ├── inline.py            ← Inline mode
│   │   └── settings_cmd.py      ← /settings + تغيير اللغة
│   └── utils/
│       ├── downloader.py        ← محرك yt-dlp
│       ├── rate_limiter.py      ← الحد اليومي
│       ├── url_extractor.py     ← استخراج الروابط
│       └── i18n.py              ← نظام الترجمة
│
├── api/
│   ├── main.py                  ← FastAPI app
│   ├── auth.py                  ← JWT authentication
│   ├── models.py                ← SQLAlchemy models
│   └── routers/
│       ├── stats.py             ← إحصائيات
│       ├── users.py             ← إدارة المستخدمين
│       ├── broadcast.py         ← البث الجماعي
│       └── settings.py          ← إعدادات البوت
│
├── worker/
│   ├── celery_app.py            ← إعداد Celery
│   └── tasks.py                 ← مهام التحميل (single + bulk)
│
├── shared/
│   └── db.py                    ← قاعدة البيانات المشتركة
│
├── payments/
│   ├── stars.py                 ← Telegram Stars
│   └── referral.py              ← نظام الإحالة
│
├── locales/
│   ├── ar.json                  ← العربية
│   ├── en.json                  ← الإنجليزية
│   └── fr.json                  ← الفرنسية
│
├── nginx/
│   ├── nginx.conf               ← إعداد Nginx الرئيسي
│   └── conf.d/bot.conf          ← Virtual host + SSL
│
├── scripts/
│   ├── setup_server.sh          ← إعداد السيرفر (مرة واحدة)
│   ├── deploy.sh                ← نشر التحديثات
│   ├── health_check.sh          ← فحص الخدمات
│   ├── backup.sh                ← نسخ احتياطي
│   └── set_webhook.sh           ← ربط Webhook تيليغرام
│
├── .github/workflows/
│   ├── deploy.yml               ← CI/CD النشر التلقائي
│   └── test.yml                 ← تشغيل الاختبارات
│
├── admin-dashboard.html         ← لوحة تحكم الأدمن
├── docker-compose.yml           ← تشغيل جميع الخدمات
├── Dockerfile                   ← بناء الصورة
├── config.py                    ← إعدادات مركزية
├── requirements.txt
└── .env.example                 ← نموذج ملف البيئة
```

---

## 🚀 النشر السريع

### 1. إعداد السيرفر (مرة واحدة)
```bash
ssh root@YOUR_SERVER_IP
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git /opt/botproject
cd /opt/botproject
bash scripts/setup_server.sh yourdomain.com admin@yourdomain.com
```

### 2. إعداد البيئة
```bash
cp .env.example .env.prod
nano .env.prod   # عبّي القيم

# توليد JWT_SECRET و WEBHOOK_SECRET
echo "JWT_SECRET=$(openssl rand -hex 32)"
echo "WEBHOOK_SECRET=$(openssl rand -hex 16)"
```

### 3. تحديث الدومين في Nginx
```bash
sed -i 's/yourdomain.com/YOUR_DOMAIN/g' nginx/conf.d/bot.conf
```

### 4. تشغيل المشروع
```bash
docker compose up -d --build
```

### 5. ربط Webhook
```bash
bash scripts/set_webhook.sh
```

### 6. نسخ لوحة الأدمن
```bash
cp admin-dashboard.html /var/www/dashboard/index.html
```

---

## 🔧 الخدمات

| الخدمة | الوصف | البورت |
|--------|-------|--------|
| nginx | Reverse proxy + SSL | 80, 443 |
| api | FastAPI Admin API | 8000 (internal) |
| bot | Telegram Bot | 8443 (internal) |
| worker_pro | Celery Pro Queue | - |
| worker_free | Celery Free Queue | - |
| postgres | قاعدة البيانات | 5432 (internal) |
| redis | Cache + Queue Broker | 6379 (internal) |
| flower | Celery Monitor | 5555 (internal) |

---

## 📋 الأوامر المفيدة

```bash
# حالة الخدمات
docker compose ps

# اللوغز
docker compose logs -f bot
docker compose logs -f worker_pro worker_free

# إعادة تشغيل خدمة
docker compose restart bot

# تحديث بعد تغيير الكود
git pull && docker compose up -d --build bot worker_pro worker_free

# فحص الصحة
bash scripts/health_check.sh

# نسخ احتياطي يدوي
bash scripts/backup.sh

# دخول قاعدة البيانات
docker compose exec postgres psql -U botuser -d botdb
```

---

## 🌐 المنصات المدعومة

- ✅ TikTok (مع/بدون علامة مائية)
- ✅ YouTube (فيديو + Shorts)
- ✅ Instagram (Reels + Posts)
- ✅ Twitter / X
- ✅ Facebook
- ✅ Pinterest
- ✅ 1000+ موقع عبر yt-dlp

---

## 💎 مقارنة الخطط

| الميزة | مجاني | Pro |
|--------|-------|-----|
| تحميلات/يوم | 5 | غير محدود |
| جودة | حتى 1080p | أفضل جودة |
| Bulk روابط/دفعة | 3 | 10 |
| أولوية Queue | عادية | عالية ⚡ |
| إزالة Watermark | ❌ | ✅ |

---

## 🔐 API Endpoints

| Method | Path | الوظيفة |
|--------|------|---------|
| POST | `/api/auth/login` | تسجيل دخول الأدمن |
| GET | `/api/stats/overview` | إحصائيات عامة |
| GET | `/api/stats/weekly` | تحميلات أسبوعية |
| GET | `/api/stats/platforms` | توزيع المنصات |
| GET | `/api/users/` | قائمة المستخدمين |
| PATCH | `/api/users/{id}` | تعديل مستخدم |
| POST | `/api/broadcast/send` | إرسال بث |
| GET | `/api/broadcast/history` | تاريخ البث |
| GET | `/api/settings/` | جلب الإعدادات |
| PUT | `/api/settings/` | تحديث الإعدادات |
| GET | `/api/health` | فحص صحة API |

Swagger UI: `https://yourdomain.com/api/docs`
