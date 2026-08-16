from __future__ import annotations

import asyncio
import json
import os
import secrets
from contextlib import suppress
from typing import Any

from .process import ManagedLineProcess, resolve_executable, resolve_file


DEFAULT_VISITS = {
    "easy": 4,
    "normal": 16,
    "hard": 48,
}
DEFAULT_MAX_CONCURRENT = 2
DEFAULT_MAX_QUEUED = 2


class KataGoBusyError(RuntimeError):
    """Raised when the bounded interactive analysis queue is full."""


class KataGoAnalysisClient:
    """JSON-lines client around one reusable KataGo analysis process."""

    def __init__(
        self,
        executable: str | None = None,
        *,
        model: str | None = None,
        config: str | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        max_queued: int = DEFAULT_MAX_QUEUED,
    ) -> None:
        if max_concurrent < 1 or max_queued < 0:
            raise ValueError("KataGo 并发配置无效")
        path = resolve_executable(executable or os.getenv("KATAGO_PATH"))
        self.model = resolve_file(model or os.getenv("KATAGO_MODEL_PATH"))
        self.config = resolve_file(config or os.getenv("KATAGO_CONFIG_PATH"))
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
        self.max_concurrent = max_concurrent
        self.max_queued = max_queued
        self._slots = asyncio.Semaphore(max_concurrent)
        self._reservation_lock = asyncio.Lock()
        self._outstanding = 0
        self._start_lock = asyncio.Lock()
        self._send_lock = asyncio.Lock()
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._reader_task: asyncio.Task[None] | None = None
        self._closed = False

    @property
    def configured(self) -> bool:
        return self.process.command is not None

    async def analyze(
        self,
        query: dict[str, Any],
        difficulty: str,
        *,
        max_visits: int | None = None,
    ) -> dict[str, Any]:
        request_id = secrets.token_hex(8)
        request = {
            **query,
            "id": request_id,
            "maxVisits": max_visits
            if max_visits is not None
            else DEFAULT_VISITS.get(
                difficulty,
                DEFAULT_VISITS["normal"],
            ),
        }
        await self._acquire_slot()
        future = asyncio.get_running_loop().create_future()
        try:
            await self._ensure_started()
            self._pending[request_id] = future
            try:
                await self._send_json(request)
            except BaseException as error:
                self._pending.pop(request_id, None)
                if not future.done():
                    future.cancel()
                await self._reset_process(error)
                raise
            try:
                response = await future
            except asyncio.CancelledError:
                self._pending.pop(request_id, None)
                if not future.done():
                    future.cancel()
                await asyncio.shield(self._terminate(request_id))
                raise
            if "error" in response:
                raise RuntimeError(f"KataGo：{response['error']}")
            return response
        finally:
            await self._release_slot()

    async def warm_up(self) -> None:
        """Load the model before a player's first interactive request."""
        if not self.configured:
            return
        await self.analyze(
            {
                "rules": "chinese",
                "komi": 7.5,
                "boardXSize": 9,
                "boardYSize": 9,
                "moves": [],
            },
            "easy",
            max_visits=1,
        )

    async def close(self) -> None:
        async with self._start_lock:
            self._closed = True
            reader_task = self._reader_task
            self._reader_task = None
            if reader_task is not None:
                reader_task.cancel()
                await asyncio.gather(reader_task, return_exceptions=True)
            self._fail_pending(RuntimeError("KataGo 已关闭"))
            await self.process.stop()

    async def _acquire_slot(self) -> None:
        async with self._reservation_lock:
            if self._closed:
                raise RuntimeError("KataGo 已关闭")
            if self._outstanding >= self.max_concurrent + self.max_queued:
                raise KataGoBusyError("KataGo 请求队列已满")
            self._outstanding += 1
        try:
            await self._slots.acquire()
        except BaseException:
            async with self._reservation_lock:
                self._outstanding -= 1
            raise

    async def _release_slot(self) -> None:
        self._slots.release()
        async with self._reservation_lock:
            self._outstanding -= 1

    async def _ensure_started(self) -> None:
        async with self._start_lock:
            if self._closed:
                raise RuntimeError("KataGo 已关闭")
            if (
                self.process.running
                and self._reader_task is not None
                and not self._reader_task.done()
            ):
                return
            reader_task = self._reader_task
            self._reader_task = None
            if reader_task is not None:
                reader_task.cancel()
                await asyncio.gather(reader_task, return_exceptions=True)
            await self.process.stop()
            await self.process.ensure_started()
            self._reader_task = asyncio.create_task(
                self._read_responses(),
                name="KataGo-responses",
            )

    async def _send_json(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, separators=(",", ":"))
        async with self._send_lock:
            await self.process.send(encoded)

    async def _read_responses(self) -> None:
        try:
            while True:
                line = await self.process.readline()
                if not line:
                    continue
                try:
                    response = json.loads(line)
                    request_id = response["id"]
                except (json.JSONDecodeError, KeyError, TypeError) as error:
                    raise RuntimeError("KataGo 返回了无效数据") from error
                if not isinstance(request_id, str):
                    raise RuntimeError("KataGo 返回了无效请求编号")
                future = self._pending.get(request_id)
                if future is None or response.get("isDuringSearch") is True:
                    continue
                self._pending.pop(request_id, None)
                if not future.done():
                    future.set_result(response)
        except asyncio.CancelledError:
            raise
        except BaseException as error:
            await self._reader_failed(error)

    async def _reader_failed(self, error: BaseException) -> None:
        async with self._start_lock:
            if self._reader_task is asyncio.current_task():
                self._reader_task = None
            self._fail_pending(error)
            await self.process.stop()

    async def _reset_process(self, error: BaseException) -> None:
        async with self._start_lock:
            reader_task = self._reader_task
            self._reader_task = None
            if reader_task is not None:
                reader_task.cancel()
                await asyncio.gather(reader_task, return_exceptions=True)
            self._fail_pending(error)
            await self.process.stop()

    async def _terminate(self, request_id: str) -> None:
        if not self.process.running:
            return
        with suppress(Exception):
            await self._send_json(
                {
                    "id": secrets.token_hex(8),
                    "action": "terminate",
                    "terminateId": request_id,
                }
            )

    def _fail_pending(self, error: BaseException) -> None:
        pending = tuple(self._pending.values())
        self._pending.clear()
        for future in pending:
            if not future.done():
                future.set_exception(error)
