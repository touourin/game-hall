import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError

from backend.app.arcade.realtime import (
    ActionPayload,
    ArcadeRealtime,
    RealtimeInputPayload,
)
from backend.app.arcade.bots import BotAction
from backend.app.arcade.models import ArcadePlayer, ArcadeRoom


class DelayedPikafish:
    async def best_move(self, fen: str, difficulty: str) -> str:
        await asyncio.sleep(0.01)
        return "a6a5"

    async def close(self) -> None:
        pass


class PacedBotEngine:
    key = "paced-bot-test"
    name = "节奏测试"
    min_players = 3
    max_players = 3
    bot_difficulties = ("normal",)
    bot_action_interval_seconds = 0.02

    def initial_state(self) -> dict[str, Any]:
        return {"turnSeat": 1, "moves": []}

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
        assert action == "move"
        assert player.seat == room.state["turnSeat"]
        room.state["moves"].append(player.id)
        room.state["turnSeat"] = (player.seat + 1) % 3

    async def choose_bot_action_async(
        self,
        room: ArcadeRoom,
    ) -> BotAction | None:
        player = room.players[room.state["turnSeat"]]
        return BotAction(player.id, "move") if player.is_bot else None

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        return {"moves": list(room.state["moves"])}

    def player_result(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> tuple[str, str, bool]:
        return "player", "player", False


class FakeSocketServer:
    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}
        self.emissions: list[tuple[str, object, dict]] = []
        self.emission_times: list[float] = []

    async def get_session(self, sid: str) -> dict:
        return self.sessions[sid]

    async def save_session(self, sid: str, session: dict) -> None:
        self.sessions[sid] = session

    async def enter_room(self, sid: str, room: str) -> None:
        return None

    async def leave_room(self, sid: str, room: str) -> None:
        return None

    async def emit(self, event: str, data=None, **kwargs) -> None:
        self.emission_times.append(time.perf_counter())
        self.emissions.append((event, data, kwargs))


def test_action_payload_accepts_legacy_council_action_from_open_browser() -> None:
    payload = ActionPayload.model_validate(
        {
            "action": "exile_council_assassination_decision",
            "payload": {"assassinate": False},
        }
    )

    assert payload.action == "exile_council_assassination_decision"


def test_action_payload_still_rejects_unbounded_action_names() -> None:
    with pytest.raises(ValidationError):
        ActionPayload.model_validate({"action": "a" * 65})


def test_realtime_input_payload_has_bounded_integer_fields() -> None:
    payload = RealtimeInputPayload.model_validate(
        {"sequence": 12, "input_mask": 17}
    )

    assert payload.sequence == 12
    assert payload.input_mask == 17
    with pytest.raises(ValidationError):
        RealtimeInputPayload.model_validate(
            {"sequence": -1, "input_mask": 0}
        )


async def test_realtime_game_uses_a_dedicated_input_and_frame_loop() -> None:
    realtime = ArcadeRealtime()
    server = FakeSocketServer()
    realtime.sio = server  # type: ignore[assignment]
    room, host, _ = realtime.rooms.create_room(
        "pixel_push",
        "玩家一",
        "account-1",
        {"arena": "moon_station"},
    )
    _, opponent, _ = realtime.rooms.join_room(
        room.code,
        "pixel_push",
        "玩家二",
        "account-2",
    )
    realtime.rooms.start(room, host.id)
    server.sessions["player-sid"] = {
        "account_id": host.account_id,
        "arcade_room_code": room.code,
        "arcade_player_id": host.id,
        "arcade_role": "player",
    }

    response = await realtime.realtime_input(
        "player-sid",
        {"sequence": 1, "input_mask": 8 | 16},
    )

    assert response == {"ok": True, "accepted": True, "sequence": 1}
    assert room.state.players[host.id].last_input_sequence == 1
    assert room.state.players[opponent.id].last_input_sequence == -1

    realtime.schedule_realtime_game(room)
    await asyncio.sleep(0.12)

    assert room.state.tick >= 2
    assert any(event == "arcade:frame" for event, _, _ in server.emissions)
    frame = next(
        payload
        for event, payload, _ in reversed(server.emissions)
        if event == "arcade:frame"
    )
    assert frame["roomCode"] == room.code
    host_frame = next(
        player for player in frame["players"] if player["id"] == host.id
    )
    assert host_frame["lastInputSequence"] == 1
    await realtime.close()


async def test_completed_realtime_driver_reschedules_an_immediate_rematch() -> None:
    realtime = ArcadeRealtime()
    room, host, _ = realtime.rooms.create_room(
        "pixel_push",
        "玩家一",
        "account-1",
        {"arena": "moon_station"},
    )
    realtime.rooms.join_room(
        room.code,
        "pixel_push",
        "玩家二",
        "account-2",
    )
    realtime.rooms.start(room, host.id)
    completed = asyncio.create_task(asyncio.sleep(0))
    await completed
    realtime.realtime_tasks[room.code] = completed
    schedule = Mock()
    realtime.schedule_realtime_game = schedule  # type: ignore[method-assign]

    realtime._realtime_task_done(room.code, completed)

    schedule.assert_called_once_with(room)
    assert room.code not in realtime.realtime_tasks
    await realtime.close()


async def test_external_bot_turn_runs_after_releasing_the_room_lock() -> None:
    realtime = ArcadeRealtime()
    server = FakeSocketServer()
    realtime.sio = server  # type: ignore[assignment]
    engine = realtime.engines["xiangqi"]
    engine.bot_strategy.client = DelayedPikafish()
    room, host, _ = realtime.rooms.create_room(
        "xiangqi",
        "玩家一",
        "account-1",
        {"firstPlayer": "host"},
    )
    realtime.rooms.add_ai_player(room, host.id)
    realtime.rooms.start(room, host.id)
    realtime.rooms.act(
        room,
        host.id,
        "move",
        {"fromRow": 6, "fromColumn": 0, "toRow": 5, "toColumn": 0},
    )

    realtime.schedule_bot_turns(room)
    task = realtime.bot_tasks[room.code]
    await asyncio.sleep(0)

    assert room.lock.locked() is False
    await task
    assert room.state.turn_color == "red"
    assert room.state.last_move["fromRow"] == 3
    await realtime.close()


async def test_consecutive_bot_actions_respect_the_game_presentation_interval() -> None:
    realtime = ArcadeRealtime()
    server = FakeSocketServer()
    realtime.sio = server  # type: ignore[assignment]
    engine = PacedBotEngine()
    realtime.engines[engine.key] = engine
    realtime.rooms.engines[engine.key] = engine
    room, host, _ = realtime.rooms.create_room(
        engine.key,
        "真人",
        "account-host",
        {"firstPlayer": "host"},
    )
    first_bot = realtime.rooms.bots.add_player(room, engine)
    second_bot = realtime.rooms.bots.add_player(room, engine)
    realtime.rooms.start(room, host.id)

    await realtime._run_bot_turns(room)

    host_snapshot_indexes = [
        index
        for index, (event, payload, _) in enumerate(server.emissions)
        if event == "arcade:snapshot"
        and isinstance(payload, dict)
        and payload["self"]["id"] == host.id
    ]
    assert room.state["moves"] == [first_bot.id, second_bot.id]
    assert len(host_snapshot_indexes) == 2
    first_time, second_time = (
        server.emission_times[index] for index in host_snapshot_indexes
    )
    assert second_time - first_time >= 0.015
    await realtime.close()


async def test_optional_game_engines_are_warmed_in_the_background() -> None:
    realtime = ArcadeRealtime()
    go_client = realtime.engines["go"].bot_strategy.client
    go_client.warm_up = AsyncMock()

    await realtime.warm_up()

    go_client.warm_up.assert_awaited_once_with()
    await realtime.close()


async def test_first_person_spectator_is_visible_fixed_and_read_only() -> None:
    realtime = ArcadeRealtime()
    server = FakeSocketServer()
    realtime.sio = server  # type: ignore[assignment]
    room, host, _ = realtime.rooms.create_room(
        "gomoku", "玩家一", "account-1", {"allowSpectators": True}
    )
    room, opponent, _ = realtime.rooms.join_room(
        room.code, "gomoku", "玩家二", "account-2"
    )
    realtime.rooms.start(room, host.id)
    server.sessions["spectator-sid"] = {
        "account_id": "spectator-account",
        "player_name": "观众甲",
        "is_guest": True,
    }

    inspected = await realtime.inspect_watch_room(
        "spectator-sid",
        {"game_key": "gomoku", "room_code": room.code},
    )
    assert inspected["ok"] is True
    assert inspected["room"]["watchable"] is True
    assert {player["id"] for player in inspected["room"]["players"]} == {
        host.id,
        opponent.id,
    }

    watched = await realtime.watch_room(
        "spectator-sid",
        {
            "game_key": "gomoku",
            "room_code": room.code,
            "target_id": opponent.id,
        },
    )
    assert watched["ok"] is True
    assert len(room.players) == 2
    assert len(realtime._room_spectators(room.code)) == 1

    spectator_snapshot = next(
        payload
        for event, payload, kwargs in reversed(server.emissions)
        if event == "arcade:snapshot"
        and kwargs.get("room", "").startswith("arcade-spectator:")
    )
    assert spectator_snapshot["viewer"]["mode"] == "spectator"
    assert spectator_snapshot["self"]["id"] == opponent.id
    assert "accountId" not in spectator_snapshot["self"]
    assert not any(spectator_snapshot["actions"].values())
    assert spectator_snapshot["spectators"][0]["name"] == "观众甲"
    assert spectator_snapshot["spectators"][0]["targetPlayerId"] == opponent.id

    board_before = [row[:] for row in room.state.board]
    rejected_action = await realtime.game_action(
        "spectator-sid",
        {"action": "place", "payload": {"row": 7, "column": 7}},
    )
    assert rejected_action["ok"] is False
    assert room.state.board == board_before

    rejected_switch = await realtime.watch_room(
        "spectator-sid",
        {
            "game_key": "gomoku",
            "room_code": room.code,
            "target_id": host.id,
        },
    )
    assert rejected_switch["ok"] is False
    assert "不能切换视角" in rejected_switch["error"]

    left = await realtime.unwatch_room("spectator-sid")
    assert left["ok"] is True
    assert realtime._room_spectators(room.code) == []


async def test_local_game_frame_is_forwarded_only_to_its_fixed_spectators() -> None:
    realtime = ArcadeRealtime()
    server = FakeSocketServer()
    realtime.sio = server  # type: ignore[assignment]
    room, player, _ = realtime.rooms.create_room(
        "reaction",
        "测试者",
        "player-account",
        {"allowSpectators": True},
    )
    realtime.rooms.start(room, player.id)
    server.sessions["player-sid"] = {
        "account_id": player.account_id,
        "arcade_room_code": room.code,
        "arcade_player_id": player.id,
        "arcade_role": "player",
    }
    server.sessions["spectator-sid"] = {
        "account_id": "spectator-account",
        "player_name": "观众甲",
        "is_guest": False,
    }
    watched = await realtime.watch_room(
        "spectator-sid",
        {
            "game_key": "reaction",
            "room_code": room.code,
            "target_id": player.id,
        },
    )
    assert watched["ok"] is True
    server.emissions.clear()

    response = await realtime.spectator_frame(
        "player-sid",
        {
            "sequence": 7,
            "state": {"stage": "ready", "localResult": None},
        },
    )

    assert response == {"ok": True, "sequence": 7}
    event, frame, kwargs = server.emissions[-1]
    assert event == "arcade:spectator:frame"
    assert frame == {
        "roomCode": room.code,
        "gameKey": "reaction",
        "roundNumber": room.round_number,
        "targetPlayerId": player.id,
        "sequence": 7,
        "state": {"stage": "ready", "localResult": None},
    }
    assert kwargs["room"].startswith("arcade-spectator:")

    rejected = await realtime.spectator_frame(
        "spectator-sid",
        {"sequence": 8, "state": {"stage": "finished"}},
    )
    assert rejected["ok"] is False
