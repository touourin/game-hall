from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


ROUNDS_REQUIRED = 3
MIN_REACTION_MS = 1
MAX_REACTION_MS = 60_000


@dataclass
class ReactionState:
    results_ms: list[int] = field(default_factory=list)


class ReactionEngine:
    key = "reaction"
    name = "反应挑战"
    min_players = 1
    max_players = 1
    public_rooms = False

    def initial_state(self) -> ReactionState:
        return ReactionState()

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
            raise GameRuleError("只有测试者本人可以记录成绩")

        state: ReactionState = room.state
        if action == "false_start":
            state.results_ms.clear()
            return
        if action != "record":
            raise GameRuleError("不支持这个反应测试操作")

        elapsed_ms = payload.get("elapsedMs")
        if (
            not isinstance(elapsed_ms, int)
            or isinstance(elapsed_ms, bool)
            or not MIN_REACTION_MS <= elapsed_ms <= MAX_REACTION_MS
        ):
            raise GameRuleError("反应时间数据不正确")
        if len(state.results_ms) >= ROUNDS_REQUIRED:
            raise GameRuleError("三轮测试已经完成")

        state.results_ms.append(elapsed_ms)
        if len(state.results_ms) == ROUNDS_REQUIRED:
            average_ms = self._average_ms(state.results_ms)
            room.finish(
                "completed",
                [player.id],
                f"三轮平均反应时间 {average_ms} 毫秒",
            )

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: ReactionState = room.state
        return {
            "roundsRequired": ROUNDS_REQUIRED,
            "resultsMs": list(state.results_ms),
            "roundNumber": min(len(state.results_ms) + 1, ROUNDS_REQUIRED),
            "bestMs": min(state.results_ms) if state.results_ms else None,
            "averageMs": (
                self._average_ms(state.results_ms)
                if state.results_ms
                else None
            ),
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        return "tester", "solo", player.id in room.winner_player_ids

    def player_score(self, room: ArcadeRoom, player: ArcadePlayer) -> int | None:
        state: ReactionState = room.state
        if len(state.results_ms) != ROUNDS_REQUIRED:
            return None
        return self._average_ms(state.results_ms)

    @staticmethod
    def _average_ms(results_ms: list[int]) -> int:
        return round(sum(results_ms) / len(results_ms))
