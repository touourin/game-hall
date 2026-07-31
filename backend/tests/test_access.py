from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.app.access import access_token, verify_access_token, verify_password
from backend.app.main import api
from backend.app.realtime import connect, sio


def test_password_and_token_are_verified_server_side(monkeypatch) -> None:
    monkeypatch.setenv("AVALON_ACCESS_PASSWORD", "test-secret")

    assert verify_password("test-secret") is True
    assert verify_password("wrong") is False
    assert verify_access_token(access_token()) is True
    assert verify_access_token("wrong-token") is False
    assert verify_access_token(None) is False


def test_access_endpoints_reject_wrong_password(monkeypatch) -> None:
    monkeypatch.setenv("AVALON_ACCESS_PASSWORD", "test-secret")

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


async def test_socket_connection_requires_access_token(monkeypatch) -> None:
    monkeypatch.setenv("AVALON_ACCESS_PASSWORD", "test-secret")
    emit = AsyncMock()
    monkeypatch.setattr(sio, "emit", emit)

    assert await connect("blocked", {}, None) is False
    emit.assert_not_awaited()

    assert await connect("allowed", {}, {"token": access_token()}) is None
    emit.assert_awaited_once()
