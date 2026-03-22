from celery import Celery
import os

REDIS_URL  = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("bot_worker", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_queues={
        "pro":  {"exchange": "pro",  "routing_key": "pro"},
        "free": {"exchange": "free", "routing_key": "free"},
    },
    task_default_queue="free",
    task_default_exchange="free",
    task_default_routing_key="free",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    result_expires=3600,
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
)
