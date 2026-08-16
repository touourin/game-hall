from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any

from .douzero_models import find_model_paths
from .process import ManagedLineProcess


class DouZeroClient:
    """JSON-lines client around one reusable, CPU-bounded DouZero worker."""

    def __init__(
        self,
        *,
        model_dir: str | None = None,
        python_executable: str | None = None,
        threads: int | None = None,
    ) -> None:
        configured_dir = model_dir or os.getenv("DOUZERO_MODEL_DIR")
        self.model_paths = self._model_paths(configured_dir)
        self.threads = (
            threads
            if threads is not None
            else int(os.getenv("DOUZERO_THREADS", "1"))
        )
        if self.threads < 1:
            raise ValueError("DouZero CPU 线程数必须大于零")

        command: tuple[str, ...] | None = None
        if self.model_paths is not None:
            command = (
                python_executable
                or os.getenv("DOUZERO_PYTHON_PATH")
                or sys.executable,
                "-m",
                "backend.app.ai.douzero_worker",
                "--model-dir",
                str(self.model_paths["landlord"].parent),
                "--threads",
                str(self.threads),
            )
        self.process = ManagedLineProcess("DouZero", command)
        self._operational = False

    @property
    def configured(self) -> bool:
        return self.process.command is not None

    @property
    def available(self) -> bool:
        return self.configured and self._operational

    async def warm_up(self) -> None:
        """Load and verify all three role models before seats are offered."""
        if not self.configured:
            return
        response = await self._request({"type": "ping"})
        if response.get("ready") is not True:
            raise RuntimeError("DouZero 预热失败")

    async def best_action(self, infoset: dict[str, Any]) -> list[int]:
        response = await self._request({"type": "act", "infoset": infoset})
        action = response.get("action")
        if not isinstance(action, list) or not all(
            isinstance(rank, int) for rank in action
        ):
            raise RuntimeError("DouZero 返回了无效动作")
        return action

    async def opening_values(
        self,
        infosets: list[dict[str, Any]],
    ) -> list[float]:
        response = await self._request(
            {"type": "evaluate_openings", "infosets": infosets}
        )
        values = response.get("values")
        if not isinstance(values, list) or len(values) != len(infosets):
            raise RuntimeError("DouZero 返回了无效叫抢估值")
        if not all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value)
            for value in values
        ):
            raise RuntimeError("DouZero 返回了无效叫抢估值")
        return [float(value) for value in values]

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with self.process.request_lock:
            try:
                await self.process.ensure_started()
                await self.process.send(
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                )
                response = self._decode_response(await self.process.readline())
                self._operational = True
                return response
            except BaseException:
                self._operational = False
                await self.process.stop()
                raise

    async def close(self) -> None:
        await self.process.close()
        self._operational = False

    @staticmethod
    def _model_paths(model_dir: str | None) -> dict[str, Path] | None:
        return find_model_paths(model_dir)

    @staticmethod
    def _decode_response(line: str) -> dict[str, Any]:
        try:
            response = json.loads(line)
        except json.JSONDecodeError as error:
            raise RuntimeError("DouZero 返回了无效数据") from error
        if not isinstance(response, dict):
            raise RuntimeError("DouZero 返回了无效数据")
        error_message = response.get("error")
        if isinstance(error_message, str) and error_message:
            raise RuntimeError(f"DouZero：{error_message}")
        return response
