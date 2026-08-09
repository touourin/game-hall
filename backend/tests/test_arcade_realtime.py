import asyncio
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from backend.app.arcade.realtime import ActionPayload, ArcadeRealtime


class DelayedPikafish:
    async def best_move(self, fen: str, difficulty: str) -> str:
        await asyncio.sleep(0.01)
        return "a6a5"

    async def close(self) -> None:
        pass


class FakeSocketServer:
    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}
        self.emissions: list[tuple[str, object, dict]] = []

    async def get_session(self, sid: str) -> dict:
        return self.sessions[sid]

    async def save_session(self, sid: str, session: dict) -> None:
        self.sessions[sid] = session

    async def enter_room(self, sid: str, room: str) -> None:
        return None

    async def leave_room(self, sid: str, room: str) -> None:
        return None

    async def emit(self, event: str, data=None, **kwargs) -> None:
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
