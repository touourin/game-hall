from collections import defaultdict
from io import BytesIO
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from PIL import Image

from backend.app.access import access_token, verify_access_token, verify_password
from backend.app.accounts import account_store
from backend.app.arcade.realtime import arcade_realtime
from backend.app.arcade.rooms import ArcadeRoomManager
from backend.app.games.registry import build_engine_registry
from backend.app.main import api, game_hall_access_header
from backend.app.realtime import connect, sio


def test_password_and_token_are_verified_server_side() -> None:
    assert verify_password("avalon") is True
    assert verify_password("wrong") is False
    assert verify_access_token(access_token()) is True
    assert verify_access_token("wrong-token") is False
    assert verify_access_token(None) is False


def test_environment_cannot_override_fixed_access_password(monkeypatch) -> None:
    monkeypatch.setenv("GAME_HALL_ACCESS_PASSWORD", "configured-secret")
    monkeypatch.setenv("AVALON_ACCESS_PASSWORD", "legacy-secret")

    assert verify_password("avalon") is True
    assert verify_password("configured-secret") is False
    assert verify_password("legacy-secret") is False


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
            "/api/access/unlock", json={"password": "avalon"}
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
    assert "avalon" not in application_log
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


def test_account_avatar_endpoints_normalize_serve_and_log_safely(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("GAME_HALL_ACCESS_PASSWORD", "test-secret")
    monkeypatch.setenv("GAME_HALL_DB_PATH", str(tmp_path / "avatars.sqlite3"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    access_header = {"X-Game-Hall-Access": access_token()}
    source = BytesIO()
    Image.new("RGB", (640, 400), "#d8ae5c").save(source, format="PNG")

    with TestClient(api) as client:
        registered = client.post(
            "/api/auth/register",
            headers=access_header,
            json={
                "username": "avatar_player",
                "password": "secret123",
                "player_name": "头像玩家",
            },
        )
        token = registered.json()["token"]
        authenticated = {
            **access_header,
            "Authorization": f"Bearer {token}",
        }
        selected = client.patch(
            "/api/auth/me/avatar",
            headers=authenticated,
            json={"preset": "jade-owl"},
        )
        uploaded = client.put(
            "/api/auth/me/avatar",
            headers={**authenticated, "Content-Type": "image/png"},
            content=source.getvalue(),
        )
        avatar_url = uploaded.json()["account"]["avatarUrl"]
        served = client.get(avatar_url)
        rejected = client.put(
            "/api/auth/me/avatar",
            headers={**authenticated, "Content-Type": "image/png"},
            content=b"not-an-image",
        )

    assert selected.status_code == 200
    assert selected.json()["account"]["avatarUrl"] == "/avatars/jade-owl.webp"
    assert uploaded.status_code == 200
    assert uploaded.json()["account"]["avatarType"] == "custom"
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/webp"
    assert served.headers["cache-control"].endswith("immutable")
    with Image.open(BytesIO(served.content)) as avatar:
        assert avatar.format == "WEBP"
        assert avatar.size == (512, 512)
    assert rejected.status_code == 400

    application_log = (tmp_path / "logs" / "app.log").read_text(
        encoding="utf-8"
    )
    assert '"event": "account.avatar.preset_changed"' in application_log
    assert '"event": "account.avatar.uploaded"' in application_log
    assert '"event": "account.avatar.upload_rejected"' in application_log
    assert '"reason": "invalid_image"' in application_log
    assert '"path": "/api/avatars/:token"' in application_log
    assert avatar_url.removeprefix("/api/avatars/") not in application_log
    assert "not-an-image" not in application_log


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
    emit.assert_awaited_once()
    assert emit.await_args.args[0] == "arcade:lobby"


async def test_leaving_avalon_through_arcade_preserves_account_identity(
    monkeypatch,
) -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, player, _ = manager.create_room(
        "avalon", "亚瑟", "account-1"
    )
    session = {
        "account_id": "account-1",
        "arcade_room_code": room.code,
        "arcade_player_id": player.id,
    }
    get_session = AsyncMock(return_value=session)
    save_session = AsyncMock()
    leave_socket_room = AsyncMock()
    broadcast_lobby = AsyncMock()
    monkeypatch.setattr(arcade_realtime, "rooms", manager)
    monkeypatch.setattr(
        arcade_realtime,
        "active_sids",
        defaultdict(set, {(room.code, player.id): {"socket-1"}}),
    )
    monkeypatch.setattr(sio, "get_session", get_session)
    monkeypatch.setattr(sio, "save_session", save_session)
    monkeypatch.setattr(sio, "leave_room", leave_socket_room)
    monkeypatch.setattr(arcade_realtime, "broadcast_lobby", broadcast_lobby)
    monkeypatch.setattr(arcade_realtime, "broadcast_room", AsyncMock())

    response = await arcade_realtime.leave_room("socket-1")

    assert response == {"ok": True, "seatPreserved": False}
    save_session.assert_awaited_once_with(
        "socket-1",
        {"account_id": "account-1"},
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
    monkeypatch.setattr(arcade_realtime, "broadcast_lobby", broadcast_lobby)

    response = await arcade_realtime.leave_room("socket-without-room")

    assert response == {"ok": True, "seatPreserved": False}
    save_session.assert_awaited_once_with(
        "socket-without-room",
        {"account_id": "account-1"},
    )


async def test_dissolving_avalon_uses_the_shared_arcade_lifecycle(
    monkeypatch,
) -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room(
        "avalon", "亚瑟", "account-1"
    )
    _, guest, _ = manager.join_room(
        room.code, "avalon", "兰斯洛特", "account-2"
    )
    sessions = {
        "host-socket": {
            "account_id": "account-1",
            "arcade_room_code": room.code,
            "arcade_player_id": host.id,
        },
        "guest-socket": {
            "account_id": "account-2",
            "arcade_room_code": room.code,
            "arcade_player_id": guest.id,
        },
    }

    async def get_session(sid: str):
        return sessions[sid]

    emit = AsyncMock()
    save_session = AsyncMock()
    leave_socket_room = AsyncMock()
    broadcast_lobby = AsyncMock()
    monkeypatch.setattr(arcade_realtime, "rooms", manager)
    monkeypatch.setattr(
        arcade_realtime,
        "active_sids",
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
    monkeypatch.setattr(arcade_realtime, "broadcast_lobby", broadcast_lobby)

    response = await arcade_realtime.dissolve_room("host-socket")

    assert response == {"ok": True}
    assert room.code not in manager.rooms
    assert emit.await_count == 2
    assert all(call.args[0] == "arcade:closed" for call in emit.await_args_list)
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
    assert not arcade_realtime.active_sids
    broadcast_lobby.assert_awaited_once()
