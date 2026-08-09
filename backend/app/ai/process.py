from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Sequence


logger = logging.getLogger(__name__)


class EngineNotConfigured(RuntimeError):
    """Raised when an optional local engine has not been installed."""


class ManagedLineProcess:
    """A lazily-started line protocol process with deterministic cleanup."""

    def __init__(self, name: str, command: Sequence[str] | None) -> None:
        self.name = name
        self.command = tuple(command) if command else None
        self.request_lock = asyncio.Lock()
        self._process: asyncio.subprocess.Process | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._stderr_tail: deque[str] = deque(maxlen=20)

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def ensure_started(self) -> bool:
        if self.running:
            return False
        if not self.command:
            raise EngineNotConfigured(f"{self.name} 尚未配置")
        await self.stop()
        self._stderr_tail.clear()
        self._process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._stderr_task = asyncio.create_task(
            self._drain_stderr(self._process),
            name=f"{self.name}-stderr",
        )
        return True

    async def send(self, line: str) -> None:
        process = self._require_process()
        if process.stdin is None:
            raise RuntimeError(f"{self.name} 标准输入不可用")
        process.stdin.write(f"{line}\n".encode())
        await process.stdin.drain()

    async def readline(self) -> str:
        process = self._require_process()
        if process.stdout is None:
            raise RuntimeError(f"{self.name} 标准输出不可用")
        raw_line = await process.stdout.readline()
        if raw_line:
            return raw_line.decode(errors="replace").strip()
        detail = "；".join(self._stderr_tail)
        message = f"{self.name} 已意外退出"
        if detail:
            message = f"{message}：{detail}"
        raise RuntimeError(message)

    async def stop(self) -> None:
        process = self._process
        self._process = None
        if process is not None and process.returncode is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except TimeoutError:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await process.wait()
        stderr_task = self._stderr_task
        self._stderr_task = None
        if stderr_task is not None:
            stderr_task.cancel()
            await asyncio.gather(stderr_task, return_exceptions=True)

    async def close(self) -> None:
        async with self.request_lock:
            await self.stop()

    def _require_process(self) -> asyncio.subprocess.Process:
        if not self.running or self._process is None:
            raise RuntimeError(f"{self.name} 没有运行")
        return self._process

    async def _drain_stderr(
        self, process: asyncio.subprocess.Process
    ) -> None:
        if process.stderr is None:
            return
        while line := await process.stderr.readline():
            message = line.decode(errors="replace").strip()
            if message:
                self._stderr_tail.append(message)
                logger.debug("%s: %s", self.name, message)
