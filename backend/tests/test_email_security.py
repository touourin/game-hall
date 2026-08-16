from fastapi.testclient import TestClient

from backend.app.access import access_token
from backend.app.email_delivery import EmailPolicy
from backend.app.main import api


def test_email_binding_and_password_reset_api(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GAME_HALL_SIGNING_SECRET", "test-secret")
    monkeypatch.setenv(
        "GAME_HALL_DB_PATH",
        str(tmp_path / "email-api.sqlite3"),
    )
    monkeypatch.setenv("SMTP_USER", "orangeplay@qq.com")
    monkeypatch.setenv("SMTP_PASS", "test-authorization-code")
    delivered: list[dict[str, str]] = []

    def capture_email(recipient, code, purpose, *, ttl_minutes):
        delivered.append(
            {
                "recipient": recipient,
                "code": code,
                "purpose": purpose,
                "ttl": str(ttl_minutes),
            }
        )

    monkeypatch.setattr(
        "backend.app.main.send_verification_email",
        capture_email,
    )
    monkeypatch.setattr(
        "backend.app.main.email_policy",
        lambda: EmailPolicy(
            account_daily_limit=3,
            server_daily_limit=20,
            cooldown_seconds=0,
            code_ttl_minutes=10,
            max_code_attempts=5,
            timezone_name="Asia/Shanghai",
        ),
    )
    access_header = {"X-Game-Hall-Access": access_token()}

    with TestClient(api) as client:
        registered = client.post(
            "/api/auth/register",
            headers=access_header,
            json={
                "username": "mail_api_player",
                "password": "secret123",
                "player_name": "邮件玩家",
            },
        )
        token = registered.json()["token"]
        authenticated = {
            **access_header,
            "Authorization": f"Bearer {token}",
        }
        requested = client.post(
            "/api/auth/me/email/code",
            headers=authenticated,
            json={"email": "mail-player@example.com"},
        )
        verified = client.post(
            "/api/auth/me/email/verify",
            headers=authenticated,
            json={
                "email": "mail-player@example.com",
                "code": delivered[-1]["code"],
            },
        )
        reset_requested = client.post(
            "/api/auth/password-reset/code",
            headers=access_header,
            json={"identifier": "mail_api_player"},
        )
        reset_confirmed = client.post(
            "/api/auth/password-reset/confirm",
            headers=access_header,
            json={
                "identifier": "mail-player@example.com",
                "code": delivered[-1]["code"],
                "new_password": "new-secret-456",
            },
        )
        old_login = client.post(
            "/api/auth/login",
            headers=access_header,
            json={"username": "mail_api_player", "password": "secret123"},
        )
        new_login = client.post(
            "/api/auth/login",
            headers=access_header,
            json={
                "username": "mail_api_player",
                "password": "new-secret-456",
            },
        )

    assert requested.status_code == 200
    assert delivered[0]["recipient"] == "mail-player@example.com"
    assert verified.status_code == 200
    assert verified.json()["account"]["email"] == "mail-player@example.com"
    assert verified.json()["account"]["emailVerified"] is True
    assert reset_requested.status_code == 200
    assert delivered[1]["purpose"] == "reset_password"
    assert reset_confirmed.status_code == 200
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_password_reset_request_does_not_reveal_unknown_account(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("GAME_HALL_SIGNING_SECRET", "test-secret")
    monkeypatch.setenv(
        "GAME_HALL_DB_PATH",
        str(tmp_path / "unknown-email-api.sqlite3"),
    )
    monkeypatch.setenv("SMTP_USER", "orangeplay@qq.com")
    monkeypatch.setenv("SMTP_PASS", "test-authorization-code")
    delivered = []
    monkeypatch.setattr(
        "backend.app.main.send_verification_email",
        lambda *args, **kwargs: delivered.append((args, kwargs)),
    )

    with TestClient(api) as client:
        response = client.post(
            "/api/auth/password-reset/code",
            headers={"X-Game-Hall-Access": access_token()},
            json={"identifier": "missing-account"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "如果账号已经绑定邮箱，验证码将发送到该邮箱"
    )
    assert delivered == []
