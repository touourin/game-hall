from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom, utc_now_iso
from backend.app.games.base import GameRuleError


DIFFICULTIES: dict[str, dict[str, int | str]] = {
    "beginner": {
        "label": "初级",
        "rows": 9,
        "columns": 9,
        "mines": 10,
    },
    "intermediate": {
        "label": "中级",
        "rows": 16,
        "columns": 16,
        "mines": 40,
    },
    "expert": {
        "label": "高级",
        "rows": 16,
        "columns": 30,
        "mines": 99,
    },
}
DEFAULT_DIFFICULTY = "beginner"


@dataclass
class MinesweeperState:
    difficulty: str
    rows: int
    columns: int
    mine_count: int
    mines: list[bool] = field(default_factory=list)
    revealed: list[bool] = field(default_factory=list)
    flagged: list[bool] = field(default_factory=list)
    revealed_count: int = 0
    started_monotonic: float | None = None
    elapsed_ms: int = 0
    exploded_index: int | None = None


class MinesweeperEngine:
    key = "minesweeper"
    name = "扫雷"
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

    def initial_state(self) -> MinesweeperState:
        return self._new_state(DEFAULT_DIFFICULTY)

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        difficulty = options.get("difficulty", DEFAULT_DIFFICULTY)
        if difficulty not in DIFFICULTIES:
            raise GameRuleError("扫雷难度不正确")
        return {"difficulty": difficulty}

    def start(self, room: ArcadeRoom) -> None:
        difficulty = room.options.get("difficulty", DEFAULT_DIFFICULTY)
        room.state = self._new_state(difficulty)
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if player.id != room.host_id:
            raise GameRuleError("只有挑战者本人可以操作雷区")
        if action == "reset":
            room.started_at = utc_now_iso()
            self.start(room)
            return
        if action not in {"open", "toggle_flag", "chord"}:
            raise GameRuleError("不支持这个扫雷操作")

        state: MinesweeperState = room.state
        index = self._valid_index(state, payload.get("index"))
        if action == "toggle_flag":
            self._toggle_flag(state, index)
        elif action == "chord":
            self._chord(room, player, state, index)
        else:
            self._open(room, player, state, index)

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: MinesweeperState = room.state
        elapsed_ms = (
            self._elapsed_ms(state)
            if state.started_monotonic is not None and room.phase == "playing"
            else state.elapsed_ms
        )
        cells = []
        for index in range(state.rows * state.columns):
            mine = bool(state.mines and state.mines[index])
            if state.revealed[index]:
                cell_state = "exploded" if index == state.exploded_index else "open"
                adjacent = None if mine else self._adjacent_mines(state, index)
            elif room.phase == "finished" and mine:
                cell_state = "flagged" if state.flagged[index] else "mine"
                adjacent = None
            elif room.phase == "finished" and state.flagged[index]:
                cell_state = "wrong_flag"
                adjacent = None
            elif state.flagged[index]:
                cell_state = "flagged"
                adjacent = None
            else:
                cell_state = "hidden"
                adjacent = None
            cells.append({"state": cell_state, "adjacent": adjacent})

        config = DIFFICULTIES[state.difficulty]
        total_safe = state.rows * state.columns - state.mine_count
        return {
            "difficulty": state.difficulty,
            "difficultyLabel": config["label"],
            "rows": state.rows,
            "columns": state.columns,
            "mineCount": state.mine_count,
            "cells": cells,
            "started": state.started_monotonic is not None,
            "revealedCount": state.revealed_count,
            "safeCellCount": total_safe,
            "flaggedCount": sum(state.flagged),
            "remainingMines": state.mine_count - sum(state.flagged),
            "elapsedMs": elapsed_ms,
            "explodedIndex": state.exploded_index,
            "firstMoveSafe": True,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        return "sweeper", "solo", player.id in room.winner_player_ids

    def player_score(self, room: ArcadeRoom, player: ArcadePlayer) -> int | None:
        state: MinesweeperState = room.state
        if room.phase != "finished" or player.id not in room.winner_player_ids:
            return None
        return state.elapsed_ms

    def record_state(self, room: ArcadeRoom) -> dict[str, Any]:
        state: MinesweeperState = room.state
        return {
            "difficulty": state.difficulty,
            "rows": state.rows,
            "columns": state.columns,
            "mine_count": state.mine_count,
            "revealed_count": state.revealed_count,
            "flagged_count": sum(state.flagged),
            "elapsed_ms": state.elapsed_ms,
            "result": (
                "completed" if room.winner == "completed" else "mine"
            ),
        }

    def _new_state(self, difficulty: str) -> MinesweeperState:
        config = DIFFICULTIES[difficulty]
        rows = int(config["rows"])
        columns = int(config["columns"])
        cell_count = rows * columns
        return MinesweeperState(
            difficulty=difficulty,
            rows=rows,
            columns=columns,
            mine_count=int(config["mines"]),
            revealed=[False] * cell_count,
            flagged=[False] * cell_count,
        )

    def _open(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        state: MinesweeperState,
        index: int,
    ) -> None:
        if state.flagged[index] or state.revealed[index]:
            return
        if not state.mines:
            self._generate_mines(state, index)
        if state.mines[index]:
            self._finish_loss(room, state, index)
            return
        self._reveal_safe_region(state, index)
        self._finish_if_cleared(room, player, state)

    def _toggle_flag(self, state: MinesweeperState, index: int) -> None:
        if state.revealed[index]:
            return
        if not state.flagged[index] and sum(state.flagged) >= state.mine_count:
            raise GameRuleError("旗帜数量已经达到本局地雷总数")
        state.flagged[index] = not state.flagged[index]

    def _chord(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        state: MinesweeperState,
        index: int,
    ) -> None:
        if not state.mines or not state.revealed[index]:
            return
        adjacent_mines = self._adjacent_mines(state, index)
        if adjacent_mines == 0:
            return
        neighbors = self._neighbors(state, index)
        if sum(1 for neighbor in neighbors if state.flagged[neighbor]) != adjacent_mines:
            return
        for neighbor in neighbors:
            if state.flagged[neighbor] or state.revealed[neighbor]:
                continue
            if state.mines[neighbor]:
                self._finish_loss(room, state, neighbor)
                return
            self._reveal_safe_region(state, neighbor)
        self._finish_if_cleared(room, player, state)

    def _generate_mines(self, state: MinesweeperState, first_index: int) -> None:
        protected = {first_index, *self._neighbors(state, first_index)}
        candidates = [
            index
            for index in range(state.rows * state.columns)
            if index not in protected
        ]
        mine_indexes = set(self.rng.sample(candidates, state.mine_count))
        state.mines = [
            index in mine_indexes
            for index in range(state.rows * state.columns)
        ]
        state.started_monotonic = self.clock()

    def _reveal_safe_region(self, state: MinesweeperState, start: int) -> None:
        queue = [start]
        queued = {start}
        while queue:
            index = queue.pop()
            if state.revealed[index] or state.flagged[index] or state.mines[index]:
                continue
            state.revealed[index] = True
            state.revealed_count += 1
            if self._adjacent_mines(state, index) != 0:
                continue
            for neighbor in self._neighbors(state, index):
                if neighbor not in queued and not state.mines[neighbor]:
                    queued.add(neighbor)
                    queue.append(neighbor)

    def _finish_if_cleared(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        state: MinesweeperState,
    ) -> None:
        safe_cell_count = state.rows * state.columns - state.mine_count
        if state.revealed_count != safe_cell_count:
            return
        elapsed_ms = self._elapsed_ms(state)
        state.elapsed_ms = elapsed_ms
        label = str(DIFFICULTIES[state.difficulty]["label"])
        room.finish(
            "completed",
            [player.id],
            f"{label}扫雷完成，用时 {self._format_duration(elapsed_ms)}",
        )

    def _finish_loss(
        self,
        room: ArcadeRoom,
        state: MinesweeperState,
        exploded_index: int,
    ) -> None:
        state.revealed[exploded_index] = True
        state.exploded_index = exploded_index
        state.elapsed_ms = self._elapsed_ms(state)
        room.finish("mine", [], "踩中地雷，本轮挑战结束")

    def _adjacent_mines(self, state: MinesweeperState, index: int) -> int:
        return sum(1 for neighbor in self._neighbors(state, index) if state.mines[neighbor])

    @staticmethod
    def _neighbors(state: MinesweeperState, index: int) -> list[int]:
        row, column = divmod(index, state.columns)
        return [
            neighbor_row * state.columns + neighbor_column
            for neighbor_row in range(max(0, row - 1), min(state.rows, row + 2))
            for neighbor_column in range(
                max(0, column - 1), min(state.columns, column + 2)
            )
            if neighbor_row != row or neighbor_column != column
        ]

    @staticmethod
    def _valid_index(state: MinesweeperState, value: Any) -> int:
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value < state.rows * state.columns
        ):
            raise GameRuleError("请选择正确的扫雷方格")
        return value

    def _elapsed_ms(self, state: MinesweeperState) -> int:
        if state.started_monotonic is None:
            return 0
        return max(0, round((self.clock() - state.started_monotonic) * 1_000))

    @staticmethod
    def _format_duration(elapsed_ms: int) -> str:
        total_seconds = elapsed_ms // 1_000
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes} 分 {seconds} 秒" if minutes else f"{seconds}.{elapsed_ms % 1_000 // 100} 秒"
