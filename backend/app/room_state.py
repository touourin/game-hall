from __future__ import annotations

import hashlib
import logging
import pickle
from typing import Any

from redis.asyncio import Redis


ROOM_STATE_KEY = "game-hall:room-state:v1"


class RedisRoomStateStore:
    """Persist trusted in-process room objects in the private Redis instance."""

    def __init__(self, connection_url: str | None) -> None:
        self.logger = logging.getLogger(__name__)
        self.client = (
            Redis.from_url(
                connection_url,
                decode_responses=False,
                socket_connect_timeout=2,
                socket_timeout=2,
                health_check_interval=30,
            )
            if connection_url is not None
            else None
        )
        self._last_digest: bytes | None = None

    async def load(self) -> dict[str, Any] | None:
        if self.client is None:
            return None
        try:
            payload = await self.client.get(ROOM_STATE_KEY)
            if payload is None:
                return None
            state = pickle.loads(payload)
            if not isinstance(state, dict) or state.get("version") != 1:
                raise ValueError("unsupported room state payload")
            self._last_digest = hashlib.sha256(payload).digest()
            return state
        except Exception:
            self.logger.exception("Failed to restore room state from Redis")
            return None

    async def save(self, state: dict[str, Any]) -> None:
        if self.client is None:
            return
        try:
            payload = pickle.dumps(
                {"version": 1, **state},
                protocol=pickle.HIGHEST_PROTOCOL,
            )
            digest = hashlib.sha256(payload).digest()
            if digest == self._last_digest:
                return
            await self.client.set(ROOM_STATE_KEY, payload)
            self._last_digest = digest
        except Exception:
            self.logger.exception("Failed to persist room state to Redis")

    async def close(self) -> None:
        if self.client is not None:
            await self.client.aclose()
