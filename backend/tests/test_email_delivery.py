import smtplib

import pytest

from backend.app.email_delivery import (
    BIND_EMAIL_PURPOSE,
    EmailDeliveryError,
    EmailDeliveryUnavailable,
    RESET_PASSWORD_PURPOSE,
    send_verification_email,
    smtp_settings,
)


def smtp_environment(monkeypatch) -> None:
    monkeypatch.setenv("SMTP_HOST", "smtp.qq.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_SECURE", "true")
    monkeypatch.setenv("SMTP_USER", "2955693049@qq.com")
    monkeypatch.setenv("SMTP_PASS", "authorization-code")
    monkeypatch.setenv("SMTP_FROM_NAME", "Orange Play")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "orangeplay@qq.com")


def test_sends_a_multipart_verification_email_over_smtp_ssl(monkeypatch) -> None:
    smtp_environment(monkeypatch)
    captured = {}

    class FakeSmtp:
        def __init__(self, host, port, *, timeout, context):
            captured.update(host=host, port=port, timeout=timeout, context=context)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, username, password):
            captured.update(username=username, password=password)

        def send_message(self, message, *, from_addr):
            captured["message"] = message
            captured["envelope_from"] = from_addr

    monkeypatch.setattr("backend.app.email_delivery.smtplib.SMTP_SSL", FakeSmtp)

    send_verification_email(
        "player@example.com",
        "123456",
        BIND_EMAIL_PURPOSE,
        ttl_minutes=10,
    )

    message = captured["message"]
    assert captured["host"] == "smtp.qq.com"
    assert captured["port"] == 465
    assert captured["username"] == "2955693049@qq.com"
    assert captured["envelope_from"] == "2955693049@qq.com"
    assert message["To"] == "player@example.com"
    assert "Orange Play" in str(message["From"])
    assert "绑定邮箱验证码" in str(message["Subject"])
    assert "123456" in message.get_body(preferencelist=("plain",)).get_content()
    assert "ORANGE PLAY" in message.get_body(preferencelist=("html",)).get_content()


def test_requires_a_qq_authorization_code_instead_of_the_login_password(
    monkeypatch,
) -> None:
    monkeypatch.setenv("SMTP_USER", "2955693049@qq.com")
    monkeypatch.delenv("SMTP_PASS", raising=False)

    with pytest.raises(EmailDeliveryUnavailable, match="SMTP_PASS"):
        smtp_settings()


def test_hides_low_level_smtp_errors(monkeypatch) -> None:
    smtp_environment(monkeypatch)

    class FailingSmtp:
        def __init__(self, *args, **kwargs):
            raise smtplib.SMTPException("sensitive provider detail")

    monkeypatch.setattr(
        "backend.app.email_delivery.smtplib.SMTP_SSL",
        FailingSmtp,
    )

    with pytest.raises(EmailDeliveryError, match="邮件发送失败") as error:
        send_verification_email(
            "player@example.com",
            "123456",
            RESET_PASSWORD_PURPOSE,
            ttl_minutes=10,
        )

    assert "sensitive provider detail" not in str(error.value)
