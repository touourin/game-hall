from __future__ import annotations

import os

from .process import ManagedLineProcess, resolve_executable, resolve_file


DEFAULT_NODES = {
    "easy": 800,
    "normal": 8_000,
    "hard": 60_000,
}


class PikafishClient:
    """Small UCI client around one reusable Pikafish process."""

    def __init__(
        self,
        executable: str | None = None,
        *,
        eval_file: str | None = None,
        threads: int | None = None,
        hash_megabytes: int | None = None,
    ) -> None:
        path = resolve_executable(executable or os.getenv("PIKAFISH_PATH"))
        self.eval_file = resolve_file(
            eval_file or os.getenv("PIKAFISH_EVAL_FILE")
        )
        self.threads = threads or int(os.getenv("PIKAFISH_THREADS", "1"))
        self.hash_megabytes = hash_megabytes or int(
            os.getenv("PIKAFISH_HASH_MB", "64")
        )
        self.process = ManagedLineProcess(
            "Pikafish",
            (path,) if path else None,
        )

    @property
    def configured(self) -> bool:
        return self.process.command is not None and self.eval_file is not None

    async def best_move(self, fen: str, difficulty: str) -> str | None:
        async with self.process.request_lock:
            try:
                started = await self.process.ensure_started()
                if started:
                    await self._initialize()
                await self.process.send(f"position fen {fen}")
                nodes = DEFAULT_NODES.get(difficulty, DEFAULT_NODES["normal"])
                await self.process.send(f"go nodes {nodes}")
                while True:
                    line = await self.process.readline()
                    if not line.startswith("bestmove "):
                        continue
                    move = line.split(maxsplit=2)[1]
                    return None if move in {"(none)", "0000"} else move
            except BaseException:
                await self.process.stop()
                raise

    async def close(self) -> None:
        await self.process.close()

    async def _initialize(self) -> None:
        await self.process.send("uci")
        await self._read_until("uciok")
        await self.process.send(
            f"setoption name Threads value {self.threads}"
        )
        await self.process.send(
            f"setoption name Hash value {self.hash_megabytes}"
        )
        if self.eval_file:
            await self.process.send(
                f"setoption name EvalFile value {self.eval_file}"
            )
        await self.process.send("isready")
        await self._read_until("readyok")

    async def _read_until(self, expected: str) -> None:
        while await self.process.readline() != expected:
            pass
