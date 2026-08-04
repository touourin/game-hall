from __future__ import annotations

import hashlib
import hmac
import os


TOKEN_MESSAGE = b"game-hall-access-v1"
DEFAULT_SIGNING_SECRET = "game-hall-local-session-v1"


def access_signing_secret() -> str:
    return os.environ.get("GAME_HALL_SIGNING_SECRET", DEFAULT_SIGNING_SECRET)


def access_token() -> str:
    return hmac.new(
        access_signing_secret().encode("utf-8"),
        TOKEN_MESSAGE,
        hashlib.sha256,
    ).hexdigest()


def verify_access_token(candidate: object) -> bool:
    return isinstance(candidate, str) and hmac.compare_digest(
        candidate, access_token()
    )
