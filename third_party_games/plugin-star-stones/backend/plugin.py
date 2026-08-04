from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


STARTING_STONES = 15
MAX_TAKE = 3


@dataclass
class StarStonesState:
    remaining: int = STARTING_STONES
    current_player_id: str | None = None
    moves: list[dict[str, Any]] = field(default_factory=list)


class StarStonesEngine:
    key = "plugin-star-stones"
    name = "星石争夺"
    min_players = 2
    max_players = 2

    def __init__(self, rng: random.Random | random.SystemRandom | None = None) -> None:
        self.rng = rng or random.SystemRandom()

    def initial_state(self) -> StarStonesState:
        return StarStonesState()

    def start(self, room: ArcadeRoom) -> None:
        first_player = (
            room.players[0]
            if room.options.get("firstPlayer") == "host"
            else self.rng.choice(room.players)
        )
        room.state = StarStonesState(current_player_id=first_player.id)
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if action != "take":
            raise GameRuleError("不支持这个星石操作")
        state: StarStonesState = room.state
        if state.current_player_id != player.id:
            raise GameRuleError("还没有轮到你")
        raw_count = payload.get("count")
        if isinstance(raw_count, bool) or not isinstance(raw_count, int):
            raise GameRuleError("取石数量必须是整数")
        if not 1 <= raw_count <= min(MAX_TAKE, state.remaining):
            raise GameRuleError("每次只能取走 1–3 颗现有星石")

        state.remaining -= raw_count
        state.moves.append({
            "playerId": player.id,
            "playerName": player.name,
            "count": raw_count,
        })
        if state.remaining == 0:
            room.finish("player", [player.id], f"{player.name} 取得最后一颗星石")
            return

        state.current_player_id = next(
            member.id for member in room.players if member.id != player.id
        )

    def manual_forfeit(self, room: ArcadeRoom, player: ArcadePlayer) -> bool:
        opponent = next(
            member for member in room.players
            if member.id != player.id and not member.left_room
        )
        room.finish("player", [opponent.id], f"{player.name} 认输，{opponent.name} 获胜")
        return True

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: StarStonesState = room.state
        return {
            "startingStones": STARTING_STONES,
            "maxTake": MAX_TAKE,
            "remaining": state.remaining,
            "currentPlayerId": state.current_player_id,
            "moves": list(state.moves[-8:]),
            "winnerPlayerId": room.winner_player_ids[0] if room.winner_player_ids else None,
            "isMyTurn": room.phase == "playing" and state.current_player_id == viewer.id,
        }

    def player_result(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> tuple[str, str, bool]:
        return "collector", f"seat-{player.seat + 1}", player.id in room.winner_player_ids


def create_engine() -> StarStonesEngine:
    return StarStonesEngine()
