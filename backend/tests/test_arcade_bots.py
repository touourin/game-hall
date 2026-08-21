from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from backend.app.arcade.bots import ArcadeBotService, BotAction, BotAvailability
from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.arcade.rooms import ArcadeRoomError, ArcadeRoomManager
from backend.app.arcade.views import build_room_view


@dataclass
class TurnState:
    turn_seat: int = 0
    moves: list[str] = field(default_factory=list)


class BotTestEngine:
    key = "bot-test"
    name = "AI 测试"
    min_players = 2
    max_players = 2
    bot_difficulties = ("normal", "hard")

    def initial_state(self) -> TurnState:
        return TurnState()

    def start(self, room: ArcadeRoom) -> None:
        room.state = TurnState()
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if action != "move" or player.seat != room.state.turn_seat:
            raise ValueError("invalid move")
        room.state.moves.append(player.id)
        room.state.turn_seat = 1 - room.state.turn_seat

    def choose_bot_action(self, room: ArcadeRoom) -> BotAction | None:
        if room.phase != "playing":
            return None
        player = room.players[room.state.turn_seat]
        return BotAction(player.id, "move") if player.is_bot else None

    def view(
        self,
        room: ArcadeRoom,
        viewer: ArcadePlayer,
    ) -> dict[str, Any]:
        return {"turnPlayerId": room.players[room.state.turn_seat].id}

    def player_result(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> tuple[str, str, bool]:
        return "player", "player", False


class NoBotEngine(BotTestEngine):
    key = "no-bot"

    choose_bot_action = None


class ConditionalBotEngine(BotTestEngine):
    key = "conditional-bot"
    max_players = 3
    bots_available = False

    def bot_availability(self, room: ArcadeRoom) -> BotAvailability:
        if self.bots_available:
            return BotAvailability(True)
        return BotAvailability(False, "当前房间不能添加 AI")


def test_bot_action_interval_uses_a_shared_validated_engine_setting() -> None:
    engine = BotTestEngine()
    assert ArcadeBotService.action_interval_seconds(engine) == 0

    engine.bot_action_interval_seconds = 1.25
    assert ArcadeBotService.action_interval_seconds(engine) == 1.25

    engine.bot_action_interval_seconds = -1
    with pytest.raises(RuntimeError, match="展示间隔"):
        ArcadeBotService.action_interval_seconds(engine)


def test_generic_bot_seat_and_action_pipeline() -> None:
    engine = BotTestEngine()
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(
        engine.key,
        "房主",
        "account-host",
        {"firstPlayer": "host"},
    )

    manager.act(room, host.id, "add_ai", {"difficulty": "hard"})

    bot = room.players[1]
    assert bot.is_bot is True
    assert bot.bot_difficulty == "hard"
    assert bot.name == "AI玩家 1"
    room_view = build_room_view(room, host, engine)
    assert room_view["actions"][
        "canAddAiPlayer"
    ] is False
    assert room_view["ai"] == {
        "difficulties": [
            {"key": "normal", "label": "普通"},
            {"key": "hard", "label": "困难"},
        ],
        "defaultDifficulty": "normal",
    }

    manager.start(room, host.id)
    manager.act(room, host.id, "move", {})

    assert room.state.moves == [host.id, bot.id]
    assert room.state.turn_seat == host.seat


def test_only_host_can_add_supported_ai_in_lobby() -> None:
    engine = BotTestEngine()
    engine.max_players = 3
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(engine.key, "房主", "account-host")
    room, guest, _ = manager.join_room(
        room.code,
        engine.key,
        "玩家二",
        "account-guest",
    )
    with pytest.raises(ArcadeRoomError, match="只有房主"):
        manager.act(room, guest.id, "add_ai", {})


def test_game_without_bot_provider_rejects_ai_seat() -> None:
    engine = NoBotEngine()
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(engine.key, "房主", "account-host")

    assert build_room_view(room, host, engine)["actions"][
        "canAddAiPlayer"
    ] is False
    with pytest.raises(ArcadeRoomError, match="暂时没有接入 AI"):
        manager.act(room, host.id, "add_ai", {})


def test_room_aware_bot_availability_uses_the_shared_ai_seat_flow() -> None:
    engine = ConditionalBotEngine()
    manager = ArcadeRoomManager({engine.key: engine})
    room, host, _ = manager.create_room(engine.key, "房主", "account-host")

    assert build_room_view(room, host, engine)["actions"][
        "canAddAiPlayer"
    ] is False
    with pytest.raises(ArcadeRoomError, match="当前房间不能添加 AI"):
        manager.add_ai_player(room, host.id)

    engine.bots_available = True
    assert build_room_view(room, host, engine)["actions"][
        "canAddAiPlayer"
    ] is True
    assert manager.add_ai_player(room, host.id).is_bot is True
