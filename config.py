import os

BOT_TOKEN          = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID      = int(os.getenv("ADMIN_CHAT_ID", "0"))
MAX_FILE_SIZE_MB   = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
DAILY_LIMIT_FREE   = int(os.getenv("DAILY_LIMIT_FREE", "5"))
TEMP_DIR           = os.getenv("TEMP_DIR", "/tmp/downloads")
ENV                = os.getenv("ENV", "development")
DOMAIN             = os.getenv("DOMAIN", "localhost")
WEBHOOK_SECRET     = os.getenv("WEBHOOK_SECRET", "")
