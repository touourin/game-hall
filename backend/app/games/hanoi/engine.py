from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom, utc_now_iso
from backend.app.games.base import GameRuleError


MIN_DISC_COUNT = 3
MAX_DISC_COUNT = 8
DEFAULT_DISC_COUNT = 5


@dataclass
class HanoiState:
    disc_count: int
    towers: list[list[int]]
    moves: int = 0
    elapsed_ms: int = 0
    move_history: list[dict[str, int]] = field(default_factory=list)
    started_monotonic: float = 0.0


class HanoiEngine:
    key = "hanoi"
    name = "汉诺塔"
    min_players = 1
    max_players = 1
    public_rooms = False

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self.clock = clock or time.monotonic

    def initial_state(self) -> HanoiState:
        return self._new_state(DEFAULT_DISC_COUNT)

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        disc_count = options.get("discCount", DEFAULT_DISC_COUNT)
        if (
            not isinstance(disc_count, int)
            or isinstance(disc_count, bool)
            or not MIN_DISC_COUNT <= disc_count <= MAX_DISC_COUNT
        ):
            raise GameRuleError(
                f"汉诺塔层数必须在 {MIN_DISC_COUNT} 到 {MAX_DISC_COUNT} 之间"
            )
        return {"discCount": disc_count}

    def start(self, room: ArcadeRoom) -> None:
        disc_count = room.options.get("discCount", DEFAULT_DISC_COUNT)
        room.state = self._new_state(disc_count)
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if player.id != room.host_id:
            raise GameRuleError("只有挑战者本人可以移动圆盘")
        if action == "reset":
            room.started_at = utc_now_iso()
            self.start(room)
            return
        if action != "move":
            raise GameRuleError("不支持这个汉诺塔操作")

        source = payload.get("fromTower")
        target = payload.get("toTower")
        if not self._valid_tower_index(source) or not self._valid_tower_index(target):
            raise GameRuleError("请选择正确的起点和目标柱")
        if source == target:
            raise GameRuleError("圆盘需要移动到另一根柱子")

        state: HanoiState = room.state
        source_tower = state.towers[source]
        target_tower = state.towers[target]
        if not source_tower:
            raise GameRuleError("这根柱子上没有可以移动的圆盘")
        disc = source_tower[-1]
        if target_tower and target_tower[-1] < disc:
            raise GameRuleError("大圆盘不能放在小圆盘上")

        source_tower.pop()
        target_tower.append(disc)
        state.moves += 1
        state.move_history.append(
            {"fromTower": source, "toTower": target, "disc": disc}
        )
        state.elapsed_ms = self._elapsed_ms(state)

        if state.towers[2] == list(range(state.disc_count, 0, -1)):
            room.finish(
                "completed",
                [player.id],
                (
                    f"用 {state.moves} 步完成 {state.disc_count} 层汉诺塔，"
                    f"耗时 {self._format_duration(state.elapsed_ms)}"
                ),
            )

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: HanoiState = room.state
        elapsed_ms = (
            self._elapsed_ms(state) if room.phase == "playing" else state.elapsed_ms
        )
        optimal_moves = 2**state.disc_count - 1
        return {
            "discCount": state.disc_count,
            "towers": [list(tower) for tower in state.towers],
            "moves": state.moves,
            "optimalMoves": optimal_moves,
            "elapsedMs": elapsed_ms,
            "isOptimal": room.phase == "finished" and state.moves == optimal_moves,
            "lastMove": state.move_history[-1] if state.move_history else None,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        return "solver", "solo", player.id in room.winner_player_ids

    def player_score(self, room: ArcadeRoom, player: ArcadePlayer) -> int | None:
        state: HanoiState = room.state
        return state.elapsed_ms if room.phase == "finished" else None

    def _new_state(self, disc_count: int) -> HanoiState:
        return HanoiState(
            disc_count=disc_count,
            towers=[list(range(disc_count, 0, -1)), [], []],
            started_monotonic=self.clock(),
        )

    def _elapsed_ms(self, state: HanoiState) -> int:
        return max(0, round((self.clock() - state.started_monotonic) * 1_000))

    @staticmethod
    def _valid_tower_index(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 2

    @staticmethod
    def _format_duration(elapsed_ms: int) -> str:
        total_seconds = elapsed_ms // 1_000
        minutes, seconds = divmod(total_seconds, 60)
        if minutes:
            return f"{minutes} 分 {seconds} 秒"
        return f"{seconds}.{elapsed_ms % 1_000 // 100} 秒"
