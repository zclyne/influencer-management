from collections.abc import Callable
from typing import Any

import redis
from rq import Queue

from app.core.config import get_settings


def get_default_queue() -> Queue:
    settings = get_settings()
    connection = redis.from_url(settings.redis_url)
    return Queue("default", connection=connection)


def enqueue_job(
    task: Callable[..., Any],
    *args: object,
    queue: Queue | None = None,
    **kwargs: object,
) -> str:
    selected_queue = queue or get_default_queue()
    rq_job = selected_queue.enqueue(task, *args, **kwargs)
    return rq_job.id
