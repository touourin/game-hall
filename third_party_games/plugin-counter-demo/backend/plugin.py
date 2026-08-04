from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


TARGET_SCORE = 10


@dataclass
class CounterState:
    scores: dict[str, int] = field(default_factory=dict)
    current_player_id: str | None = None


class CounterDemoEngine:
    key = "plugin-counter-demo"
    name = "计数竞速"
    min_players = 2
    max_players = 2

    def initial_state(self) -> CounterState:
        return CounterState()

    def start(self, room: ArcadeRoom) -> None:
        room.state = CounterState(
            scores={player.id: 0 for player in room.players},
            current_player_id=room.players[0].id,
        )
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if action != "increment":
            raise GameRuleError("不支持这个计数操作")
        state: CounterState = room.state
        if state.current_player_id != player.id:
            raise GameRuleError("还没有轮到你")
        state.scores[player.id] = state.scores.get(player.id, 0) + 1
        if state.scores[player.id] >= TARGET_SCORE:
            room.finish("completed", [player.id], f"{player.name} 率先达到 {TARGET_SCORE} 分")
            return
        opponent = next(member for member in room.players if member.id != player.id)
        state.current_player_id = opponent.id

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: CounterState = room.state
        return {
            "targetScore": TARGET_SCORE,
            "currentPlayerId": state.current_player_id,
            "scores": dict(state.scores),
        }

    def player_result(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> tuple[str, str, bool]:
        return "counter", "solo", player.id in room.winner_player_ids


def create_engine() -> CounterDemoEngine:
    return CounterDemoEngine()
