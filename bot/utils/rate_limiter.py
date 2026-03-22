from datetime import date
from collections import defaultdict

# في الإنتاج: استبدل بـ Redis
_usage: dict = defaultdict(lambda: {"count": 0, "date": None})


def check_limit(user_id: int, limit: int = 5) -> tuple[bool, int]:
    today  = str(date.today())
    record = _usage[user_id]
    if record["date"] != today:
        record["count"] = 0
        record["date"]  = today
    if record["count"] >= limit:
        return False, 0
    return True, limit - record["count"]


def increment(user_id: int):
    _usage[user_id]["count"] += 1
