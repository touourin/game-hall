from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


MINIMUM = 1
MAXIMUM = 20
MAX_ATTEMPTS = 6


@dataclass
class NumberVaultState:
    secret: int | None = None
    guesses: list[int] = field(default_factory=list)
    hint: str = "ready"


class NumberVaultEngine:
    key = "plugin-number-vault"
    name = "数字密匣"
    min_players = 1
    max_players = 1
    public_rooms = False

    def __init__(self, rng: random.Random | random.SystemRandom | None = None) -> None:
        self.rng = rng or random.SystemRandom()

    def initial_state(self) -> NumberVaultState:
        return NumberVaultState()

    def start(self, room: ArcadeRoom) -> None:
        room.state = NumberVaultState(secret=self.rng.randint(MINIMUM, MAXIMUM))
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if action != "guess":
            raise GameRuleError("不支持这个破解操作")
        raw_value = payload.get("value")
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise GameRuleError("请输入一个整数")
        if not MINIMUM <= raw_value <= MAXIMUM:
            raise GameRuleError(f"请输入 {MINIMUM}–{MAXIMUM} 之间的数字")

        state: NumberVaultState = room.state
        if state.secret is None:
            raise GameRuleError("密匣尚未准备完成")
        if raw_value in state.guesses:
            raise GameRuleError("这个数字已经猜过了")

        state.guesses.append(raw_value)
        if raw_value == state.secret:
            state.hint = "correct"
            room.finish("completed", [player.id], f"{player.name} 破解了数字密匣")
            return

        state.hint = "higher" if raw_value < state.secret else "lower"
        if len(state.guesses) >= MAX_ATTEMPTS:
            room.finish("failed", [], f"挑战结束，答案是 {state.secret}")

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: NumberVaultState = room.state
        finished = room.phase == "finished"
        return {
            "minimum": MINIMUM,
            "maximum": MAXIMUM,
            "maxAttempts": MAX_ATTEMPTS,
            "remainingAttempts": max(0, MAX_ATTEMPTS - len(state.guesses)),
            "guesses": list(state.guesses),
            "hint": state.hint,
            "answer": state.secret if finished else None,
            "won": viewer.id in room.winner_player_ids,
        }

    def player_result(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> tuple[str, str, bool]:
        return "solver", "solo", player.id in room.winner_player_ids


def create_engine() -> NumberVaultEngine:
    return NumberVaultEngine()
