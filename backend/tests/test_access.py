from collections import defaultdict
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.app import realtime
from backend.app.access import access_token, verify_access_token, verify_password
from backend.app.accounts import account_store
from backend.app.games.avalon.rooms import RoomManager
from backend.app.main import api, game_hall_access_header
from backend.app.realtime import connect, sio


def test_password_and_token_are_verified_server_side(monkeypatch) -> None:
    monkeypatch.setenv("GAME_HALL_ACCESS_PASSWORD", "test-secret")

    assert verify_password("test-secret") is True
    assert verify_password("wrong") is False
    assert verify_access_token(access_token()) is True
    assert verify_access_token("wrong-token") is False
    assert verify_access_token(None) is False


def test_legacy_avalon_access_password_is_still_accepted(monkeypatch) -> None:
    monkeypatch.delenv("GAME_HALL_ACCESS_PASSWORD", raising=False)
    monkeypatch.setenv("AVALON_ACCESS_PASSWORD", "legacy-secret")

    assert verify_password("legacy-secret") is True


def test_legacy_avalon_access_header_is_still_accepted() -> None:
    assert game_hall_access_header(None, "legacy-token") == "legacy-token"
    assert game_hall_access_header("new-token", "legacy-token") == "new-token"


def test_access_endpoints_reject_wrong_password(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GAME_HALL_ACCESS_PASSWORD", "test-secret")
    monkeypatch.setenv("GAME_HALL_DB_PATH", str(tmp_path / "access.sqlite3"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))

    with TestClient(api) as client:
        rejected = client.post(
            "/api/access/unlock", json={"password": "wrong"}
        )
        accepted = client.post(
            "/api/access/unlock", json={"password": "test-secret"}
        )
        token = accepted.json()["token"]
        unauthorized = client.get("/api/access/status")
        authorized = client.get(
            "/api/access/status",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert len(rejected.headers["X-Request-ID"]) == 16
    application_log = (tmp_path / "logs" / "app.log").read_text(
        encoding="utf-8"
    )
    assert '"event": "http.completed"' in application_log
    assert '"path": "/api/access/unlock"' in application_log
    assert "test-secret" not in application_log
    assert '"password"' not in application_log


def test_account_registration_login_and_session(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GAME_HALL_ACCESS_PASSWORD", "test-secret")
    monkeypatch.setenv("GAME_HALL_DB_PATH", str(tmp_path / "accounts.sqlite3"))
    access_header = {"X-Game-Hall-Access": access_token()}

    with TestClient(api) as client:
        registered = client.post(
            "/api/auth/register",
            headers=access_header,
            json={
                "username": "round_player",
                "password": "secret123",
                "player_name": "圆桌玩家",
            },
        )
        duplicate = client.post(
            "/api/auth/register",
            headers=access_header,
            json={
                "username": "ROUND_PLAYER",
                "password": "secret123",
                "player_name": "另一玩家",
            },
        )
        token = registered.json()["token"]
        profile = client.get(
            "/api/auth/me",
            headers={
                **access_header,
                "Authorization": f"Bearer {token}",
            },
        )
        renamed = client.patch(
            "/api/auth/me",
            headers={
                **access_header,
                "Authorization": f"Bearer {token}",
            },
            json={"player_name": "新游戏昵称"},
        )
        bad_login = client.post(
            "/api/auth/login",
            headers=access_header,
            json={"username": "round_player", "password": "wrong12"},
        )
        login = client.post(
            "/api/auth/login",
            headers=access_header,
            json={"username": "round_player", "password": "secret123"},
        )

    assert registered.status_code == 200
    assert registered.json()["account"]["username"] == "round_player"
    assert registered.json()["account"]["playerName"] == "圆桌玩家"
    assert duplicate.status_code == 400
    assert profile.status_code == 200
    assert renamed.status_code == 200
    assert renamed.json()["account"]["username"] == "round_player"
    assert renamed.json()["account"]["playerName"] == "新游戏昵称"
    assert bad_login.status_code == 401
    assert login.status_code == 200


async def test_socket_connection_requires_both_tokens(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("GAME_HALL_ACCESS_PASSWORD", "test-secret")
    monkeypatch.setenv("GAME_HALL_DB_PATH", str(tmp_path / "socket.sqlite3"))
    _, account_token = account_store().register(
        "socket_player", "secret123", "连接玩家"
    )
    emit = AsyncMock()
    save_session = AsyncMock()
    monkeypatch.setattr(sio, "emit", emit)
    monkeypatch.setattr(sio, "save_session", save_session)

    assert await connect("blocked", {}, None) is False
    emit.assert_not_awaited()
    assert await connect("no-account", {}, {"token": access_token()}) is False

    assert await connect(
        "allowed",
        {},
        {"token": access_token(), "accountToken": account_token},
    ) is None
    save_session.assert_awaited_once()
    assert emit.await_count == 2
    assert {call.args[0] for call in emit.await_args_list} == {
        "lobby:rooms",
        "arcade:lobby",
    }


async def test_leaving_avalon_preserves_socket_account_identity(
    monkeypatch,
) -> None:
    manager = RoomManager()
    room, player, _ = manager.create_room("亚瑟", account_id="account-1")
    session = {
        "account_id": "account-1",
        "room_code": room.code,
        "player_id": player.id,
        "arcade_room_code": "GMKU",
        "arcade_player_id": "arcade-player",
    }
    get_session = AsyncMock(return_value=session)
    save_session = AsyncMock()
    leave_socket_room = AsyncMock()
    broadcast_lobby = AsyncMock()
    monkeypatch.setattr(realtime, "avalon_rooms", manager)
    monkeypatch.setattr(
        realtime,
        "avalon_active_sids",
        defaultdict(set, {(room.code, player.id): {"socket-1"}}),
    )
    monkeypatch.setattr(sio, "get_session", get_session)
    monkeypatch.setattr(sio, "save_session", save_session)
    monkeypatch.setattr(sio, "leave_room", leave_socket_room)
    monkeypatch.setattr(
        realtime, "broadcast_avalon_lobby", broadcast_lobby
    )

    response = await realtime.leave_room("socket-1")

    assert response == {"ok": True, "seatPreserved": False}
    save_session.assert_awaited_once_with(
        "socket-1",
        {
            "account_id": "account-1",
            "arcade_room_code": "GMKU",
            "arcade_player_id": "arcade-player",
        },
    )


async def test_leaving_avalon_without_room_session_is_idempotent(
    monkeypatch,
) -> None:
    session = {"account_id": "account-1"}
    get_session = AsyncMock(return_value=session)
    save_session = AsyncMock()
    broadcast_lobby = AsyncMock()
    monkeypatch.setattr(sio, "get_session", get_session)
    monkeypatch.setattr(sio, "save_session", save_session)
    monkeypatch.setattr(
        realtime, "broadcast_avalon_lobby", broadcast_lobby
    )

    response = await realtime.leave_room("socket-without-room")

    assert response == {"ok": True, "seatPreserved": False}
    save_session.assert_awaited_once_with(
        "socket-without-room",
        {"account_id": "account-1"},
    )


async def test_dissolving_avalon_ejects_every_player_and_clears_sessions(
    monkeypatch,
) -> None:
    manager = RoomManager()
    room, host, _ = manager.create_room("亚瑟", account_id="account-1")
    _, guest, _ = manager.join_room(
        room.code, "兰斯洛特", account_id="account-2"
    )
    sessions = {
        "host-socket": {
            "account_id": "account-1",
            "room_code": room.code,
            "player_id": host.id,
        },
        "guest-socket": {
            "account_id": "account-2",
            "room_code": room.code,
            "player_id": guest.id,
        },
    }

    async def get_session(sid: str):
        return sessions[sid]

    emit = AsyncMock()
    save_session = AsyncMock()
    leave_socket_room = AsyncMock()
    broadcast_lobby = AsyncMock()
    persist_state = AsyncMock()
    monkeypatch.setattr(realtime, "avalon_rooms", manager)
    monkeypatch.setattr(
        realtime,
        "avalon_active_sids",
        defaultdict(
            set,
            {
                (room.code, host.id): {"host-socket"},
                (room.code, guest.id): {"guest-socket"},
            },
        ),
    )
    monkeypatch.setattr(sio, "get_session", get_session)
    monkeypatch.setattr(sio, "emit", emit)
    monkeypatch.setattr(sio, "save_session", save_session)
    monkeypatch.setattr(sio, "leave_room", leave_socket_room)
    monkeypatch.setattr(
        realtime, "broadcast_avalon_lobby", broadcast_lobby
    )
    monkeypatch.setattr(realtime, "persist_room_state", persist_state)

    response = await realtime.dissolve_room("host-socket")

    assert response == {"ok": True}
    assert room.code not in manager.rooms
    assert emit.await_count == 2
    assert all(call.args[0] == "room:closed" for call in emit.await_args_list)
    payloads = {
        call.kwargs["to"]: call.args[1] for call in emit.await_args_list
    }
    assert payloads["host-socket"]["silent"] is True
    assert payloads["guest-socket"] == {
        "message": "房主已解散房间",
        "silent": False,
    }
    assert save_session.await_count == 2
    assert sessions == {
        "host-socket": {"account_id": "account-1"},
        "guest-socket": {"account_id": "account-2"},
    }
    assert not realtime.avalon_active_sids
    broadcast_lobby.assert_awaited_once()
    persist_state.assert_awaited_once()
