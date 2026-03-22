import json
from pathlib import Path
from functools import lru_cache

SUPPORTED_LANGS = ["ar", "en", "fr"]
DEFAULT_LANG    = "ar"

TG_LANG_MAP = {
    "ar": "ar",
    "en": "en", "en-US": "en", "en-GB": "en",
    "fr": "fr", "fr-FR": "fr", "fr-BE": "fr",
}


@lru_cache(maxsize=10)
def load_locale(lang: str) -> dict:
    path = Path(__file__).parent.parent.parent / "locales" / f"{lang}.json"
    if not path.exists():
        path = Path(__file__).parent.parent.parent / "locales" / f"{DEFAULT_LANG}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    locale = load_locale(lang)
    text   = locale.get(key, load_locale(DEFAULT_LANG).get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text


def detect_lang(telegram_lang_code: str | None) -> str:
    if not telegram_lang_code:
        return DEFAULT_LANG
    return TG_LANG_MAP.get(telegram_lang_code, DEFAULT_LANG)


async def get_user_lang(user_id: int, tg_lang: str | None = None) -> str:
    try:
        from shared.db import AsyncSessionLocal
        from api.models import User
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            user = await db.scalar(select(User).where(User.telegram_id == user_id))
            if user and getattr(user, "lang", None):
                return user.lang
    except Exception:
        pass
    return detect_lang(tg_lang)
