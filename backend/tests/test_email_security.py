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
    assert reset_requested.json()["sent"] is True
    assert delivered[1]["purpose"] == "reset_password"
    assert reset_confirmed.status_code == 200
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_password_reset_request_does_not_distinguish_unknown_and_unbound_accounts(
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
        registered = client.post(
            "/api/auth/register",
            headers={"X-Game-Hall-Access": access_token()},
            json={
                "username": "unbound-account",
                "password": "secret123",
                "player_name": "未绑定玩家",
            },
        )
        unknown_response = client.post(
            "/api/auth/password-reset/code",
            headers={"X-Game-Hall-Access": access_token()},
            json={"identifier": "missing-account"},
        )
        unbound_response = client.post(
            "/api/auth/password-reset/code",
            headers={"X-Game-Hall-Access": access_token()},
            json={"identifier": "unbound-account"},
        )

    assert registered.status_code == 200
    assert unknown_response.status_code == 200
    assert unbound_response.status_code == 200
    assert unknown_response.json() == unbound_response.json()
    assert unknown_response.json() == {
        "ok": True,
        "sent": False,
        "message": "未找到已绑定邮箱的账号，无法发送验证码",
    }
    assert delivered == []


def test_registration_email_verification_and_unbinding_api(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("GAME_HALL_SIGNING_SECRET", "test-secret")
    monkeypatch.setenv(
        "GAME_HALL_DB_PATH",
        str(tmp_path / "registration-email-api.sqlite3"),
    )
    monkeypatch.setenv("SMTP_USER", "orangeplay@qq.com")
    monkeypatch.setenv("SMTP_PASS", "test-authorization-code")
    delivered: list[dict[str, str]] = []

    def capture_email(recipient, code, purpose, *, ttl_minutes):
        delivered.append(
            {"recipient": recipient, "code": code, "purpose": purpose}
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
        code_requested = client.post(
            "/api/auth/register/email/code",
            headers=access_header,
            json={"email": "new-player@example.com"},
        )
        registered = client.post(
            "/api/auth/register",
            headers=access_header,
            json={
                "username": "registration_email_api",
                "password": "secret123",
                "player_name": "注册邮箱",
                "email": "new-player@example.com",
                "email_code": delivered[-1]["code"],
            },
        )
        authenticated = {
            **access_header,
            "Authorization": f"Bearer {registered.json()['token']}",
        }
        unbind_requested = client.post(
            "/api/auth/me/email/unbind/code",
            headers=authenticated,
        )
        unbound = client.post(
            "/api/auth/me/email/unbind",
            headers=authenticated,
            json={"code": delivered[-1]["code"]},
        )
        reset_requested = client.post(
            "/api/auth/password-reset/code",
            headers=access_header,
            json={"identifier": "new-player@example.com"},
        )

    assert code_requested.status_code == 200
    assert delivered[0]["purpose"] == "register_email"
    assert registered.status_code == 200
    assert registered.json()["account"]["email"] == "new-player@example.com"
    assert registered.json()["account"]["emailVerified"] is True
    assert unbind_requested.status_code == 200
    assert delivered[1]["purpose"] == "unbind_email"
    assert unbound.status_code == 200
    assert unbound.json()["account"]["email"] is None
    assert unbound.json()["account"]["emailVerified"] is False
    assert reset_requested.json()["sent"] is False
