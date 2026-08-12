from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


MAX_SCORE = 100_000_000
MAX_LINES = 10_000
MAX_PIECES = 100_000
MAX_ELAPSED_MS = 24 * 60 * 60 * 1_000


@dataclass
class TetrisState:
    score: int = 0
    lines: int = 0
    level: int = 1
    pieces: int = 0
    elapsed_ms: int = 0


class TetrisEngine:
    key = "tetris"
    name = "落块挑战"
    min_players = 1
    max_players = 1
    public_rooms = False

    def initial_state(self) -> TetrisState:
        return TetrisState()

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
            raise GameRuleError("只有挑战者本人可以提交成绩")
        if action != "finish":
            raise GameRuleError("不支持这个落块挑战操作")

        score = self._bounded_int(payload.get("score"), "得分", 0, MAX_SCORE)
        lines = self._bounded_int(payload.get("lines"), "消行数", 0, MAX_LINES)
        pieces = self._bounded_int(payload.get("pieces"), "方块数", 1, MAX_PIECES)
        elapsed_ms = self._bounded_int(
            payload.get("elapsedMs"), "挑战用时", 1_000, MAX_ELAPSED_MS
        )
        expected_level = lines // 10 + 1
        level = self._bounded_int(payload.get("level"), "等级", 1, 1_001)
        if level != expected_level:
            raise GameRuleError("等级与消行数不匹配")
        if lines > pieces * 4:
            raise GameRuleError("消行数超过本局方块数量能够达到的范围")
        # The browser owns the real-time simulation. This deliberately loose
        # ceiling rejects malformed submissions while allowing line clears,
        # soft/hard-drop points and future scoring bonuses.
        if score > pieces * (1_000 * level + 100):
            raise GameRuleError("得分超过本局可达到的范围")

        state: TetrisState = room.state
        state.score = score
        state.lines = lines
        state.level = level
        state.pieces = pieces
        state.elapsed_ms = elapsed_ms
        room.finish(
            "completed",
            [player.id],
            f"最终得分 {score:,} · 消除 {lines} 行",
        )

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: TetrisState = room.state
        return {
            "score": state.score,
            "lines": state.lines,
            "level": state.level,
            "pieces": state.pieces,
            "elapsedMs": state.elapsed_ms,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        return "stacker", "solo", player.id in room.winner_player_ids

    def player_score(self, room: ArcadeRoom, player: ArcadePlayer) -> int | None:
        state: TetrisState = room.state
        return state.score if room.phase == "finished" else None

    def record_state(self, room: ArcadeRoom) -> dict[str, int]:
        state: TetrisState = room.state
        return {
            "score": state.score,
            "lines": state.lines,
            "level": state.level,
            "pieces": state.pieces,
            "elapsed_ms": state.elapsed_ms,
        }

    @staticmethod
    def _bounded_int(value: Any, label: str, minimum: int, maximum: int) -> int:
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not minimum <= value <= maximum
        ):
            raise GameRuleError(f"{label}数据不正确")
        return value
