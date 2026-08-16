from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .access import access_signing_secret
from .accounts import AVATAR_PRESET_IDS


GUEST_SESSION_LIFETIME = timedelta(days=7)
GUEST_TOKEN_CONTEXT = b"game-hall-guest-v1:"


class GuestSessionError(ValueError):
    pass


@dataclass(frozen=True)
class GuestIdentity:
    id: str
    player_name: str
    avatar_preset: str
    created_at: str

    @property
    def avatar_url(self) -> str:
        return f"/avatars/{self.avatar_preset}.webp"

    def as_dict(self) -> dict[str, str | bool | None]:
        return {
            "id": self.id,
            "username": "",
            "playerName": self.player_name,
            "avatarType": "preset",
            "avatarPreset": self.avatar_preset,
            "avatarUrl": self.avatar_url,
            "createdAt": self.created_at,
            "isGuest": True,
        }


def issue_guest_session(
    player_name: str,
    *,
    now: datetime | None = None,
) -> tuple[GuestIdentity, str]:
    current = now or datetime.now(timezone.utc)
    normalized_name = _normalize_player_name(player_name)
    guest_id = f"guest:{secrets.token_hex(8)}"
    avatar_preset = secrets.choice(AVATAR_PRESET_IDS)
    payload = {
        "v": 1,
        "id": guest_id,
        "name": normalized_name,
        "avatar": avatar_preset,
        "iat": int(current.timestamp()),
        "exp": int((current + GUEST_SESSION_LIFETIME).timestamp()),
    }
    encoded = _encode_payload(payload)
    signature = _signature(encoded)
    identity = GuestIdentity(
        id=guest_id,
        player_name=normalized_name,
        avatar_preset=avatar_preset,
        created_at=current.isoformat(timespec="seconds"),
    )
    return identity, f"{encoded}.{signature}"


def guest_for_token(
    token: object,
    *,
    now: datetime | None = None,
) -> GuestIdentity | None:
    if not isinstance(token, str) or len(token) > 1024:
        return None
    try:
        encoded, separator, candidate_signature = token.partition(".")
        if (
            not separator
            or not encoded.isascii()
            or not candidate_signature.isascii()
            or not hmac.compare_digest(candidate_signature, _signature(encoded))
        ):
            return None
        payload = _decode_payload(encoded)
        current_timestamp = int((now or datetime.now(timezone.utc)).timestamp())
        issued_at = int(payload["iat"])
        expires_at = int(payload["exp"])
        if (
            payload.get("v") != 1
            or expires_at <= current_timestamp
            or expires_at - issued_at
            > int(GUEST_SESSION_LIFETIME.total_seconds())
        ):
            return None
        guest_id = str(payload["id"])
        if not guest_id.startswith("guest:") or len(guest_id) > 32:
            return None
        avatar_preset = str(payload["avatar"])
        if avatar_preset not in AVATAR_PRESET_IDS:
            return None
        created_at = datetime.fromtimestamp(
            issued_at, timezone.utc
        ).isoformat(timespec="seconds")
        return GuestIdentity(
            id=guest_id,
            player_name=_normalize_player_name(str(payload["name"])),
            avatar_preset=avatar_preset,
            created_at=created_at,
        )
    except (
        GuestSessionError,
        KeyError,
        TypeError,
        ValueError,
        binascii.Error,
        json.JSONDecodeError,
    ):
        return None


def _normalize_player_name(player_name: str) -> str:
    normalized = " ".join(player_name.strip().split())
    if not 1 <= len(normalized) <= 12:
        raise GuestSessionError("游客昵称需要 1–12 个字符")
    return normalized


def _encode_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_payload(encoded: str) -> dict[str, Any]:
    padding = "=" * (-len(encoded) % 4)
    raw = base64.urlsafe_b64decode(encoded + padding)
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise GuestSessionError("游客凭证格式不正确")
    return payload


def _signature(encoded_payload: str) -> str:
    digest = hmac.new(
        access_signing_secret().encode("utf-8"),
        GUEST_TOKEN_CONTEXT + encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
