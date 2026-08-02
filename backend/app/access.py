from __future__ import annotations

import hashlib
import hmac


FIXED_ACCESS_PASSWORD = "avalon"
TOKEN_MESSAGE = b"game-hall-access-v1"


def access_password() -> str:
    return FIXED_ACCESS_PASSWORD


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
