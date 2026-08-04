from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
import pytest

from backend.app.access import access_token
from backend.app.arcade.realtime import arcade_realtime
from backend.app.arcade.rooms import ArcadeRoomError, ArcadeRoomManager
from backend.app.arcade.views import build_room_view
from backend.app.games.registry import build_engine_registry
from backend.app.guests import guest_for_token, issue_guest_session
from backend.app.main import api
from backend.app.realtime import connect, sio


def test_guest_token_is_signed_and_expires(monkeypatch) -> None:
    monkeypatch.setenv("GAME_HALL_SIGNING_SECRET", "guest-secret")
    now = datetime(2026, 8, 2, 8, 0, tzinfo=timezone.utc)

    guest, token = issue_guest_session(" 临时  玩家 ", now=now)

    restored = guest_for_token(token, now=now + timedelta(days=6))
    assert restored is not None
    assert restored.id == guest.id
    assert restored.player_name == "临时 玩家"
    assert restored.as_dict()["isGuest"] is True
    assert guest_for_token(f"{token}tampered", now=now) is None
    assert guest_for_token(token, now=now + timedelta(days=8)) is None
    assert guest_for_token("非 ASCII.签名", now=now) is None
    assert guest_for_token("x" * 1025, now=now) is None


def test_guest_http_session_can_restore_and_view_leaderboard(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("GAME_HALL_SIGNING_SECRET", "guest-secret")
    monkeypatch.setenv("GAME_HALL_DB_PATH", str(tmp_path / "guests.sqlite3"))
    access_header = {"X-Game-Hall-Access": access_token()}

    with TestClient(api) as client:
        created = client.post(
            "/api/auth/guest",
            headers=access_header,
            json={"player_name": "观战骑士"},
        )
        token = created.json()["token"]
        authenticated = {
            **access_header,
            "Authorization": f"Bearer {token}",
        }
        restored = client.get("/api/auth/me", headers=authenticated)
        leaderboard = client.get(
            "/api/leaderboard?game=gomoku", headers=authenticated
        )
        stats = client.get("/api/stats/me", headers=authenticated)

    assert created.status_code == 200
    assert created.json()["account"]["isGuest"] is True
    assert restored.status_code == 200
    assert restored.json()["account"]["playerName"] == "观战骑士"
    assert leaderboard.status_code == 200
    assert stats.status_code == 401


async def test_socket_accepts_a_signed_guest_identity(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("GAME_HALL_SIGNING_SECRET", "guest-secret")
    monkeypatch.setenv("GAME_HALL_DB_PATH", str(tmp_path / "socket.sqlite3"))
    guest, guest_token = issue_guest_session("临时骑士")
    emit = AsyncMock()
    save_session = AsyncMock()
    monkeypatch.setattr(sio, "emit", emit)
    monkeypatch.setattr(sio, "save_session", save_session)

    assert await connect(
        "guest-socket",
        {},
        {"token": access_token(), "accountToken": guest_token},
    ) is None

    saved = save_session.await_args.args[1]
    assert saved["account_id"] == guest.id
    assert saved["player_name"] == "临时骑士"
    assert saved["is_guest"] is True
    emit.assert_awaited_once()


def test_guest_room_access_and_stats_eligibility_are_platform_rules() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    ranked_room, _, _ = manager.create_room(
        "gomoku",
        "正式玩家",
        "account-1",
        {"allowGuests": False},
    )
    try:
        manager.join_room(
            ranked_room.code,
            "gomoku",
            "游客玩家",
            "guest:blocked",
            is_guest=True,
        )
    except ArcadeRoomError as error:
        assert "仅允许登录玩家" in str(error)
    else:
        raise AssertionError("游客不应进入仅登录玩家房间")

    casual_room, host, _ = manager.create_room(
        "gomoku",
        "正式玩家",
        "account-2",
        {"allowGuests": True, "firstPlayer": "host"},
    )
    _, guest, _ = manager.join_room(
        casual_room.code,
        "gomoku",
        "游客玩家",
        "guest:allowed",
        is_guest=True,
    )
    assert casual_room.stats_eligible is False

    with pytest.raises(ArcadeRoomError, match="已有游客"):
        manager.update_options(
            casual_room,
            host.id,
            {"allowGuests": False, "firstPlayer": "host"},
        )

    manager.start(casual_room, host.id)
    assert casual_room.stats_eligible is False
    view = build_room_view(casual_room, guest, manager.engine("gomoku"))
    assert view["statsEligible"] is False
    assert view["self"]["isGuest"] is True
    assert view["players"][1]["isGuest"] is True

    casual_room.finish("black", [host.id], "测试结束")
    arcade_realtime._record_room(casual_room)
    assert casual_room.recorded is True


def test_guest_can_only_create_guest_enabled_multiplayer_rooms() -> None:
    manager = ArcadeRoomManager(build_engine_registry())

    try:
        manager.create_room(
            "xiangqi",
            "游客玩家",
            "guest:creator",
            {"allowGuests": False},
            is_guest=True,
        )
    except ArcadeRoomError as error:
        assert "游客只能创建" in str(error)
    else:
        raise AssertionError("游客不应创建仅登录玩家房间")

    room, player, _ = manager.create_room(
        "xiangqi",
        "游客玩家",
        "guest:creator",
        {"allowGuests": True},
        is_guest=True,
    )
    assert player.is_guest is True
    assert room.stats_eligible is False


def test_avalon_keeps_platform_guest_access_without_changing_game_rules() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room(
        "avalon",
        "正式玩家",
        "account-avalon",
        {"allowGuests": False, "mode": "standard"},
    )
    for _ in range(4):
        manager.act(room, host.id, "add_ai", {})

    assert room.options["allowGuests"] is False
    manager.start(room, host.id)
    assert room.options["allowGuests"] is False
    assert room.stats_eligible is True


def test_single_character_guest_nickname_is_allowed() -> None:
    guest, token = issue_guest_session("王")

    assert guest.player_name == "王"
    assert guest_for_token(token) is not None
