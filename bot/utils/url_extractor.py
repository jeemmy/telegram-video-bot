import re

SUPPORTED_DOMAINS = [
    "tiktok.com", "youtube.com", "youtu.be",
    "instagram.com", "twitter.com", "x.com",
    "facebook.com", "pinterest.com",
]

URL_PATTERN = re.compile(r"https?://[^\s\]\[<>\"']+")

BULK_LIMITS = {"free": 3, "pro": 10}


def extract_urls(text: str) -> list[str]:
    found   = URL_PATTERN.findall(text)
    cleaned = [u.rstrip(".,;:!?)>") for u in found]
    supported = [u for u in cleaned if any(d in u for d in SUPPORTED_DOMAINS)]
    seen, unique = set(), []
    for u in supported:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def get_bulk_limit(plan: str) -> int:
    return BULK_LIMITS.get(plan, 3)
