from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Float
from sqlalchemy.sql import func
from shared.db import Base


class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True)
    telegram_id      = Column(BigInteger, unique=True, index=True, nullable=False)
    username         = Column(String(64), nullable=True)
    full_name        = Column(String(128), nullable=True)
    plan             = Column(String(16), default="free")       # free | pro | banned
    daily_limit      = Column(Integer, default=5)
    downloads_total  = Column(Integer, default=0)
    is_banned        = Column(Boolean, default=False)
    lang             = Column(String(4), default="ar")          # ar | en | fr
    joined_at        = Column(DateTime, server_default=func.now())
    last_seen        = Column(DateTime, onupdate=func.now())


class Download(Base):
    __tablename__ = "downloads"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, index=True)
    telegram_id = Column(BigInteger, index=True)
    url         = Column(String(2048))
    platform    = Column(String(32))    # tiktok | youtube | instagram | twitter
    quality     = Column(String(16))    # best | 1080p | 720p | 480p | audio
    file_size   = Column(Float)         # MB
    status      = Column(String(16))    # success | failed | too_large
    error_msg   = Column(String(256), nullable=True)
    created_at  = Column(DateTime, server_default=func.now(), index=True)


class BotSetting(Base):
    __tablename__ = "bot_settings"

    key   = Column(String(64), primary_key=True)
    value = Column(String(512))


class BroadcastLog(Base):
    __tablename__ = "broadcast_logs"

    id           = Column(Integer, primary_key=True)
    target       = Column(String(32))
    message_text = Column(String(4096))
    sent_count   = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status       = Column(String(16), default="pending")
    created_at   = Column(DateTime, server_default=func.now())


class Referral(Base):
    __tablename__ = "referrals"

    id          = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, index=True)
    referred_id = Column(BigInteger, index=True)
    bonus_given = Column(Integer, default=0)
    created_at  = Column(DateTime, server_default=func.now())
