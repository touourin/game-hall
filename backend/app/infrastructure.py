from __future__ import annotations

import os
from functools import lru_cache

from redis import Redis


def redis_url() -> str | None:
    value = os.environ.get("REDIS_URL", "").strip()
    return value or None


@lru_cache(maxsize=4)
def redis_client(connection_url: str) -> Redis:
    return Redis.from_url(
        connection_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )


def redis_status() -> str:
    connection_url = redis_url()
    if connection_url is None:
        return "disabled"
    if redis_client(connection_url).ping() is not True:
        raise ConnectionError("Redis ping failed")
    return "ok"
