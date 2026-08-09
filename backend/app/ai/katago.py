from __future__ import annotations

import json
import os
import secrets
from typing import Any

from .process import ManagedLineProcess


DEFAULT_VISITS = {
    "easy": 8,
    "normal": 40,
    "hard": 160,
}


class KataGoAnalysisClient:
    """JSON-lines client around one reusable KataGo analysis process."""

    def __init__(
        self,
        executable: str | None = None,
        *,
        model: str | None = None,
        config: str | None = None,
    ) -> None:
        path = executable or os.getenv("KATAGO_PATH")
        self.model = model or os.getenv("KATAGO_MODEL_PATH")
        self.config = config or os.getenv("KATAGO_CONFIG_PATH")
        command = None
        if path and self.model and self.config:
            command = (
                path,
                "analysis",
                "-model",
                self.model,
                "-config",
                self.config,
            )
        self.process = ManagedLineProcess("KataGo", command)

    @property
    def configured(self) -> bool:
        return self.process.command is not None

    async def analyze(
        self,
        query: dict[str, Any],
        difficulty: str,
    ) -> dict[str, Any]:
        request_id = secrets.token_hex(8)
        request = {
            **query,
            "id": request_id,
            "maxVisits": DEFAULT_VISITS.get(
                difficulty, DEFAULT_VISITS["normal"]
            ),
        }
        async with self.process.request_lock:
            try:
                await self.process.ensure_started()
                await self.process.send(
                    json.dumps(request, separators=(",", ":"))
                )
                while True:
                    line = await self.process.readline()
                    if not line:
                        continue
                    response = json.loads(line)
                    if response.get("id") != request_id:
                        continue
                    if "error" in response:
                        raise RuntimeError(f"KataGo：{response['error']}")
                    return response
            except (json.JSONDecodeError, KeyError) as error:
                await self.process.stop()
                raise RuntimeError("KataGo 返回了无效数据") from error
            except BaseException:
                await self.process.stop()
                raise

    async def close(self) -> None:
        await self.process.close()
