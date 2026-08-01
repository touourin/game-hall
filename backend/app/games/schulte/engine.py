from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


GRID_SIZE = 5
CELL_COUNT = GRID_SIZE * GRID_SIZE
MIN_COMPLETION_MS = 2_000


@dataclass
class SchulteState:
    grid: list[int] = field(default_factory=list)
    next_number: int = 1
    mistakes: int = 0
    started_monotonic: float = 0.0
    elapsed_ms: int = 0
    last_value: int | None = None
    last_correct: bool | None = None


class SchulteEngine:
    key = "schulte"
    name = "舒尔特方格"
    min_players = 1
    max_players = 1
    public_rooms = False

    def __init__(
        self,
        clock: Callable[[], float] | None = None,
        rng: random.Random | random.SystemRandom | None = None,
    ) -> None:
        self.clock = clock or time.monotonic
        self.rng = rng or random.SystemRandom()

    def initial_state(self) -> SchulteState:
        return SchulteState()

    def start(self, room: ArcadeRoom) -> None:
        room.state = self.initial_state()
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if player.id != room.host_id:
            raise GameRuleError("只有挑战者本人可以操作方格")
        if action == "reset":
            room.state = self.initial_state()
            return
        if action == "begin":
            self._begin(room)
            return
        if action != "tap":
            raise GameRuleError("不支持这个舒尔特方格操作")
        self._tap(room, player, payload.get("value"))

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: SchulteState = room.state
        started = bool(state.grid)
        elapsed_ms = (
            self._elapsed_ms(state)
            if started and room.phase == "playing"
            else state.elapsed_ms
        )
        completed_count = min(state.next_number - 1, CELL_COUNT)
        return {
            "gridSize": GRID_SIZE,
            "cellCount": CELL_COUNT,
            "grid": list(state.grid),
            "started": started,
            "nextNumber": min(state.next_number, CELL_COUNT),
            "completedCount": completed_count,
            "mistakes": state.mistakes,
            "elapsedMs": elapsed_ms,
            "averageCellMs": (
                round(state.elapsed_ms / CELL_COUNT)
                if room.phase == "finished"
                else None
            ),
            "accuracy": (
                round(CELL_COUNT / (CELL_COUNT + state.mistakes) * 100)
                if room.phase == "finished"
                else None
            ),
            "lastValue": state.last_value,
            "lastCorrect": state.last_correct,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        return "challenger", "solo", player.id in room.winner_player_ids

    def player_score(self, room: ArcadeRoom, player: ArcadePlayer) -> int | None:
        state: SchulteState = room.state
        return state.elapsed_ms if room.phase == "finished" else None

    def _begin(self, room: ArcadeRoom) -> None:
        state: SchulteState = room.state
        if state.grid:
            raise GameRuleError("本轮挑战已经开始")
        grid = list(range(1, CELL_COUNT + 1))
        self.rng.shuffle(grid)
        state.grid = grid
        state.next_number = 1
        state.mistakes = 0
        state.elapsed_ms = 0
        state.last_value = None
        state.last_correct = None
        state.started_monotonic = self.clock()

    def _tap(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        value: Any,
    ) -> None:
        state: SchulteState = room.state
        if not state.grid:
            raise GameRuleError("请先开始挑战")
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 1 <= value <= CELL_COUNT
        ):
            raise GameRuleError("方格数字不正确")

        state.last_value = value
        if value != state.next_number:
            state.last_correct = False
            state.mistakes += 1
            return

        if value == CELL_COUNT:
            elapsed_ms = self._elapsed_ms(state)
            if elapsed_ms < MIN_COMPLETION_MS:
                raise GameRuleError("完成速度异常，请按顺序继续挑战")
            state.last_correct = True
            state.next_number = CELL_COUNT + 1
            state.elapsed_ms = elapsed_ms
            room.finish(
                "completed",
                [player.id],
                f"5×5 舒尔特方格完成，用时 {self._format_duration(elapsed_ms)}",
            )
            return

        state.last_correct = True
        state.next_number += 1

    def _elapsed_ms(self, state: SchulteState) -> int:
        return max(0, round((self.clock() - state.started_monotonic) * 1_000))

    @staticmethod
    def _format_duration(elapsed_ms: int) -> str:
        seconds, milliseconds = divmod(elapsed_ms, 1_000)
        return f"{seconds}.{milliseconds:03d} 秒"
