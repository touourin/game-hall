from __future__ import annotations

import hashlib
import hmac
import os


PASSWORD_ENV = "AVALON_ACCESS_PASSWORD"
TOKEN_MESSAGE = b"avalon-lan-access-v1"


def access_password() -> str:
    password = os.getenv(PASSWORD_ENV)
    if not password:
        raise RuntimeError(
            f"{PASSWORD_ENV} is required and must not be empty"
        )
    return password


def access_token() -> str:
    return hmac.new(
        access_password().encode("utf-8"),
        TOKEN_MESSAGE,
        hashlib.sha256,
    ).hexdigest()


def verify_password(candidate: str) -> bool:
    return hmac.compare_digest(candidate, access_password())


def verify_access_token(candidate: object) -> bool:
    return isinstance(candidate, str) and hmac.compare_digest(
        candidate, access_token()
    )
