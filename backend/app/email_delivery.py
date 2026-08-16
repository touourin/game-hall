from __future__ import annotations

import html
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


BIND_EMAIL_PURPOSE = "bind_email"
RESET_PASSWORD_PURPOSE = "reset_password"


class EmailDeliveryError(RuntimeError):
    pass


class EmailDeliveryUnavailable(EmailDeliveryError):
    pass


def _positive_int(name: str, default: int, *, maximum: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise EmailDeliveryUnavailable(f"{name} 必须是整数") from error
    if not 1 <= value <= maximum:
        raise EmailDeliveryUnavailable(
            f"{name} 必须在 1–{maximum} 之间"
        )
    return value


@dataclass(frozen=True)
class EmailPolicy:
    account_daily_limit: int
    server_daily_limit: int
    cooldown_seconds: int
    code_ttl_minutes: int
    max_code_attempts: int
    timezone_name: str


def email_policy() -> EmailPolicy:
    return EmailPolicy(
        account_daily_limit=_positive_int(
            "EMAIL_ACCOUNT_DAILY_LIMIT", 3, maximum=100
        ),
        server_daily_limit=_positive_int(
            "EMAIL_SERVER_DAILY_LIMIT", 20, maximum=100_000
        ),
        cooldown_seconds=_positive_int(
            "EMAIL_SEND_COOLDOWN_SECONDS", 60, maximum=86_400
        ),
        code_ttl_minutes=_positive_int(
            "EMAIL_CODE_TTL_MINUTES", 10, maximum=60
        ),
        max_code_attempts=_positive_int(
            "EMAIL_CODE_MAX_ATTEMPTS", 5, maximum=20
        ),
        timezone_name=os.environ.get("TZ", "Asia/Shanghai").strip()
        or "Asia/Shanghai",
    )


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    secure: bool
    username: str
    password: str
    from_name: str
    from_email: str
    timeout_seconds: int


def smtp_settings() -> SmtpSettings:
    username = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASS", "").strip()
    if not username or not password:
        raise EmailDeliveryUnavailable(
            "邮件服务尚未配置，请设置 SMTP_USER 和 SMTP_PASS"
        )
    from_email = os.environ.get("SMTP_FROM_EMAIL", "").strip() or username
    if (
        from_email.count("@") != 1
        or any(character.isspace() for character in from_email)
    ):
        raise EmailDeliveryUnavailable("SMTP_FROM_EMAIL 必须是有效邮箱地址")
    return SmtpSettings(
        host=os.environ.get("SMTP_HOST", "smtp.qq.com").strip()
        or "smtp.qq.com",
        port=_positive_int("SMTP_PORT", 465, maximum=65_535),
        secure=os.environ.get("SMTP_SECURE", "true").strip().lower()
        not in {"0", "false", "no", "off"},
        username=username,
        password=password,
        from_name=os.environ.get("SMTP_FROM_NAME", "Orange Play").strip()
        or "Orange Play",
        from_email=from_email,
        timeout_seconds=_positive_int(
            "SMTP_TIMEOUT_SECONDS", 12, maximum=60
        ),
    )


def send_verification_email(
    recipient: str,
    code: str,
    purpose: str,
    *,
    ttl_minutes: int,
) -> None:
    settings = smtp_settings()
    purpose_label = (
        "绑定邮箱"
        if purpose == BIND_EMAIL_PURPOSE
        else "重置密码"
    )
    subject = f"【Orange Play】{purpose_label}验证码"
    message = EmailMessage()
    message["From"] = Address(
        display_name=settings.from_name,
        addr_spec=settings.from_email,
    )
    message["To"] = Address(addr_spec=recipient)
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=False)
    message["Message-ID"] = make_msgid(
        domain=settings.from_email.rpartition("@")[2]
    )
    message["Auto-Submitted"] = "auto-generated"
    message.set_content(
        "\n".join(
            [
                f"你正在进行{purpose_label}操作。",
                f"验证码：{code}",
                f"验证码将在 {ttl_minutes} 分钟后失效，请勿转发给他人。",
                "如果不是你本人操作，请忽略这封邮件。",
            ]
        )
    )
    safe_code = html.escape(code)
    message.add_alternative(
        f"""<!doctype html>
<html lang="zh-CN">
  <body style="margin:0;background:#f4f1ea;color:#28251f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;">
    <div style="max-width:520px;margin:0 auto;padding:40px 18px;">
      <div style="overflow:hidden;border:1px solid #e1d8c8;border-radius:18px;background:#fff;box-shadow:0 16px 40px rgba(75,59,32,.10);">
        <div style="padding:24px 28px;background:linear-gradient(135deg,#ff9d45,#f46b35);color:#fff;">
          <div style="font-size:13px;font-weight:700;letter-spacing:.12em;opacity:.9;">ACCOUNT SECURITY</div>
          <h1 style="margin:8px 0 0;font-size:24px;">Orange Play</h1>
        </div>
        <div style="padding:30px 28px 32px;">
          <p style="margin:0 0 18px;font-size:15px;line-height:1.8;">你正在进行<strong>{purpose_label}</strong>操作，请输入下面的验证码：</p>
          <div style="margin:22px 0;padding:18px;border:1px solid #f0c49d;border-radius:14px;background:#fff7ef;color:#d65220;font-size:34px;font-weight:800;letter-spacing:.28em;text-align:center;">{safe_code}</div>
          <p style="margin:0;color:#776f64;font-size:13px;line-height:1.8;">验证码将在 {ttl_minutes} 分钟后失效，请勿转发给任何人。若非本人操作，可以安全忽略此邮件。</p>
        </div>
      </div>
    </div>
  </body>
</html>""",
        subtype="html",
    )

    context = ssl.create_default_context()
    try:
        if settings.secure:
            with smtplib.SMTP_SSL(
                settings.host,
                settings.port,
                timeout=settings.timeout_seconds,
                context=context,
            ) as client:
                client.login(settings.username, settings.password)
                client.send_message(message, from_addr=settings.username)
        else:
            with smtplib.SMTP(
                settings.host,
                settings.port,
                timeout=settings.timeout_seconds,
            ) as client:
                client.ehlo()
                client.starttls(context=context)
                client.ehlo()
                client.login(settings.username, settings.password)
                client.send_message(message, from_addr=settings.username)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailDeliveryError("邮件发送失败，请稍后再试") from error
