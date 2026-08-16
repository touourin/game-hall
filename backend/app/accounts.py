from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import case, delete, func, insert, inspect, or_, select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from .database import (
    account_sessions,
    build_engine,
    email_send_quotas,
    email_verification_challenges,
    games,
    match_players,
    matches,
    metadata,
    normalize_database_url,
    player_name_claims,
    registration_email_challenges,
    users,
)
from .email_delivery import (
    BIND_EMAIL_PURPOSE,
    REGISTER_EMAIL_PURPOSE,
    RESET_PASSWORD_PURPOSE,
    UNBIND_EMAIL_PURPOSE,
    EmailPolicy,
)
from .games.definition import GameRecordQueryError
from .games.registry import GAME_NAMES, GAME_REGISTRY, game_registration


logger = logging.getLogger(__name__)
SESSION_LIFETIME = timedelta(days=30)
PLAYER_NAME_CHANGE_INTERVAL = timedelta(days=30)
USERNAME_MIN_LENGTH = 2
USERNAME_MAX_LENGTH = 50
EMAIL_MAX_LENGTH = 254
EMAIL_LOCAL_PART_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$"
)
SCORED_GAME_KEYS = GAME_REGISTRY.scored_game_keys
AVATAR_PRESET_IDS = (
    "moon-fox",
    "jade-owl",
    "sun-lion",
    "cloud-rabbit",
    "ember-cat",
    "frost-wolf",
    "star-deer",
    "ink-dragon",
)


def _game_score_kind(game_key: str | None) -> str:
    if game_key is None:
        return "outcome"
    definition = game_registration(game_key)
    return definition.records.score_kind if definition else "outcome"


class AccountError(ValueError):
    pass


@dataclass(frozen=True)
class Account:
    id: str
    username: str
    player_name: str
    player_name_changed_at: str | None
    avatar_preset: str
    avatar_token: str | None
    email: str | None
    email_verified_at: str | None
    created_at: str

    @property
    def avatar_type(self) -> str:
        return "custom" if self.avatar_token is not None else "preset"

    @property
    def avatar_url(self) -> str:
        if self.avatar_token is not None:
            return f"/api/avatars/{self.avatar_token}"
        return f"/avatars/{self.avatar_preset}.webp"

    def as_dict(self) -> dict[str, str | bool | None]:
        next_rename_at = None
        if self.player_name_changed_at is not None:
            changed_at = datetime.fromisoformat(self.player_name_changed_at)
            next_rename_at = AccountStore._iso_datetime(
                changed_at + PLAYER_NAME_CHANGE_INTERVAL
            )
        return {
            "id": self.id,
            "username": self.username,
            "playerName": self.player_name,
            "nextRenameAt": next_rename_at,
            "avatarType": self.avatar_type,
            "avatarPreset": self.avatar_preset,
            "avatarUrl": self.avatar_url,
            "email": self.email,
            "emailVerified": self.email_verified_at is not None,
            "createdAt": self.created_at,
            "isGuest": False,
        }


@dataclass(frozen=True)
class EmailChallenge:
    id: str
    account_id: str | None
    email: str
    purpose: str
    code: str
    expires_at: str


class AccountStore:
    def __init__(self, database_source: str | Path) -> None:
        self.database_url = normalize_database_url(database_source)
        self.engine: Engine = build_engine(self.database_url)
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        if self.engine.dialect.name == "sqlite":
            self._upgrade_local_sqlite_schema()
            metadata.create_all(self.engine)
            self._ensure_local_sqlite_indexes()
        now = self._now()
        with self.engine.begin() as connection:
            existing_games = set(
                connection.execute(select(games.c.key)).scalars().all()
            )
            missing_games = [
                {
                    "key": key,
                    "name": name,
                    "enabled": True,
                    "created_at": now,
                }
                for key, name in GAME_NAMES.items()
                if key not in existing_games
            ]
            if missing_games:
                connection.execute(insert(games), missing_games)
            for key, name in GAME_NAMES.items():
                connection.execute(
                    update(games)
                    .where(games.c.key == key, games.c.name != name)
                    .values(name=name)
                )
        self._initialized = True

    def _upgrade_local_sqlite_schema(self) -> None:
        """Keep the migration-free local SQLite database compatible.

        Production databases are upgraded by Alembic before the app starts. The
        local fallback database is created directly from SQLAlchemy metadata, so
        an existing file also needs the one historical column rename that
        ``create_all`` cannot apply on its own.
        """
        inspector = inspect(self.engine)
        with self.engine.begin() as connection:
            table_names = set(inspector.get_table_names())
            if "match_players" in table_names:
                match_columns = {
                    column["name"]
                    for column in inspector.get_columns("match_players")
                }
                if (
                    "score_ms" in match_columns
                    and "score_value" not in match_columns
                ):
                    connection.exec_driver_sql(
                        "ALTER TABLE match_players "
                        "RENAME COLUMN score_ms TO score_value"
                    )
                    logger.info("Upgraded local SQLite match score column")
            if "users" in table_names:
                user_columns = {
                    column["name"]
                    for column in inspector.get_columns("users")
                }
                email_columns = {
                    "email": "VARCHAR(254)",
                    "email_key": "VARCHAR(254)",
                    "email_verified_at": "DATETIME",
                }
                for name, sql_type in email_columns.items():
                    if name not in user_columns:
                        connection.exec_driver_sql(
                            f"ALTER TABLE users ADD COLUMN {name} {sql_type}"
                        )
                        logger.info(
                            "Upgraded local SQLite account email column",
                            extra={"column": name},
                        )

    def _ensure_local_sqlite_indexes(self) -> None:
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email_key "
                "ON users (email_key)"
            )

    def ping(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(select(1)).scalar_one()

    def dispose(self) -> None:
        self.engine.dispose()

    def register(
        self,
        username: str,
        password: str,
        player_name: str,
        *,
        email: str | None = None,
        email_code: str | None = None,
        policy: EmailPolicy | None = None,
        now: datetime | None = None,
    ) -> tuple[Account, str]:
        normalized_username, username_key = self._normalize_username(username)
        normalized_name, name_key = self._normalize_player_name(player_name)
        self._validate_password(password)
        normalized_email: str | None = None
        email_key: str | None = None
        if email is not None or email_code is not None:
            if not email or not email_code or policy is None:
                raise AccountError("填写邮箱后必须输入邮箱验证码")
            normalized_email, email_key = self._normalize_email(email)
            self._validate_email_code(email_code)
        salt = secrets.token_bytes(16)
        password_hash = self._password_hash(password, salt)
        created_at = now or self._now()
        avatar_preset = secrets.choice(AVATAR_PRESET_IDS)
        account = Account(
            id=secrets.token_urlsafe(12),
            username=normalized_username,
            player_name=normalized_name,
            player_name_changed_at=None,
            avatar_preset=avatar_preset,
            avatar_token=None,
            email=normalized_email,
            email_verified_at=(
                self._iso_datetime(created_at)
                if normalized_email is not None
                else None
            ),
            created_at=self._iso_datetime(created_at),
        )
        self.initialize()
        verification_error: str | None = None
        try:
            with self.engine.begin() as connection:
                if normalized_email is not None and email_key is not None:
                    owner_id = connection.execute(
                        select(users.c.id).where(users.c.email_key == email_key)
                    ).scalar_one_or_none()
                    if owner_id is not None:
                        verification_error = "此邮箱已经绑定到其他账号"
                    else:
                        verification_error = (
                            self._consume_registration_email_challenge(
                                connection,
                                email_key=email_key,
                                code=email_code,
                                policy=policy,
                                now=created_at,
                            )
                        )
                if verification_error is None:
                    connection.execute(
                        insert(users).values(
                            id=account.id,
                            username=account.username,
                            username_key=username_key,
                            player_name=account.player_name,
                            password_salt=salt,
                            password_hash=password_hash,
                            player_name_changed_at=None,
                            avatar_preset=avatar_preset,
                            avatar_token=None,
                            avatar_mime=None,
                            avatar_data=None,
                            email=normalized_email,
                            email_key=email_key,
                            email_verified_at=(
                                created_at
                                if normalized_email is not None
                                else None
                            ),
                            created_at=created_at,
                        )
                    )
                    connection.execute(
                        insert(player_name_claims).values(
                            name_key=name_key,
                            account_id=account.id,
                            claimed_at=created_at,
                        )
                    )
        except IntegrityError as exc:
            message = (
                "账号名、游戏昵称或邮箱已经被使用"
                if normalized_email is not None
                else "账号名或游戏昵称已经被使用"
            )
            raise AccountError(message) from exc
        if verification_error is not None:
            raise AccountError(verification_error)
        return account, self._create_session(account.id)

    def login(self, username: str, password: str) -> tuple[Account, str]:
        _, username_key = self._normalize_username(username)
        self._validate_password(password)
        self.initialize()
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    select(
                        users.c.id,
                        users.c.username,
                        users.c.player_name,
                        users.c.player_name_changed_at,
                        users.c.avatar_preset,
                        users.c.avatar_token,
                        users.c.email,
                        users.c.email_verified_at,
                        users.c.password_salt,
                        users.c.password_hash,
                        users.c.created_at,
                    ).where(users.c.username_key == username_key)
                )
                .mappings()
                .first()
            )
        if row is None:
            raise AccountError("账号名或密码不正确")
        candidate_hash = self._password_hash(password, row["password_salt"])
        if not secrets.compare_digest(candidate_hash, row["password_hash"]):
            raise AccountError("账号名或密码不正确")
        account = self._account_from_row(row)
        return account, self._create_session(account.id)

    def account_for_token(self, token: str | None) -> Account | None:
        if not token:
            return None
        self.initialize()
        now = self._now()
        token_hash = self._token_hash(token)
        with self.engine.begin() as connection:
            connection.execute(
                delete(account_sessions).where(
                    account_sessions.c.expires_at <= now
                )
            )
            row = (
                connection.execute(
                    select(
                        users.c.id,
                        users.c.username,
                        users.c.player_name,
                        users.c.player_name_changed_at,
                        users.c.avatar_preset,
                        users.c.avatar_token,
                        users.c.email,
                        users.c.email_verified_at,
                        users.c.created_at,
                    )
                    .select_from(
                        account_sessions.join(
                            users,
                            users.c.id == account_sessions.c.account_id,
                        )
                    )
                    .where(
                        account_sessions.c.token_hash == token_hash,
                        account_sessions.c.expires_at > now,
                    )
                )
                .mappings()
                .first()
            )
        return self._account_from_row(row) if row is not None else None

    def account_for_id(self, account_id: str) -> Account | None:
        self.initialize()
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    select(
                        users.c.id,
                        users.c.username,
                        users.c.player_name,
                        users.c.player_name_changed_at,
                        users.c.avatar_preset,
                        users.c.avatar_token,
                        users.c.email,
                        users.c.email_verified_at,
                        users.c.created_at,
                    ).where(users.c.id == account_id)
                )
                .mappings()
                .first()
            )
        return self._account_from_row(row) if row is not None else None

    def rename_player(self, account_id: str, player_name: str) -> Account:
        normalized_name, name_key = self._normalize_player_name(player_name)
        self.initialize()
        now = self._now()
        try:
            with self.engine.begin() as connection:
                row = (
                    connection.execute(
                        select(
                            users.c.id,
                            users.c.username,
                            users.c.player_name,
                            users.c.player_name_changed_at,
                            users.c.avatar_preset,
                            users.c.avatar_token,
                            users.c.email,
                            users.c.email_verified_at,
                            users.c.created_at,
                        ).where(users.c.id == account_id)
                    )
                    .mappings()
                    .first()
                )
                if row is None:
                    raise AccountError("账号不存在")
                current_name_key = self._normalize_player_name(
                    row["player_name"]
                )[1]
                if current_name_key == name_key:
                    return self._account_from_row(row)
                changed_at = row["player_name_changed_at"]
                if (
                    changed_at is not None
                    and changed_at + PLAYER_NAME_CHANGE_INTERVAL > now
                ):
                    available_at = self._iso_datetime(
                        changed_at + PLAYER_NAME_CHANGE_INTERVAL
                    )
                    raise AccountError(
                        f"每 30 天只能改名一次，下次可改名时间：{available_at}"
                    )
                owner_id = connection.execute(
                    select(player_name_claims.c.account_id).where(
                        player_name_claims.c.name_key == name_key
                    )
                ).scalar_one_or_none()
                if owner_id is not None and owner_id != account_id:
                    raise AccountError("这个游戏昵称已归其他账号所有")
                connection.execute(
                    update(users)
                    .where(users.c.id == account_id)
                    .values(
                        player_name=normalized_name,
                        player_name_changed_at=now,
                    )
                )
                if owner_id is None:
                    connection.execute(
                        insert(player_name_claims).values(
                            name_key=name_key,
                            account_id=account_id,
                            claimed_at=now,
                        )
                    )
                return Account(
                    id=account_id,
                    username=row["username"],
                    player_name=normalized_name,
                    player_name_changed_at=self._iso_datetime(now),
                    avatar_preset=row["avatar_preset"],
                    avatar_token=row["avatar_token"],
                    email=row["email"],
                    email_verified_at=(
                        self._iso_datetime(row["email_verified_at"])
                        if row["email_verified_at"] is not None
                        else None
                    ),
                    created_at=self._iso_datetime(row["created_at"]),
                )
        except IntegrityError as exc:
            raise AccountError("这个游戏昵称已经被使用") from exc

    def set_avatar_preset(self, account_id: str, preset: str) -> Account:
        if preset not in AVATAR_PRESET_IDS:
            raise AccountError("请选择有效的内置头像")
        self.initialize()
        with self.engine.begin() as connection:
            result = connection.execute(
                update(users)
                .where(users.c.id == account_id)
                .values(
                    avatar_preset=preset,
                    avatar_token=None,
                    avatar_mime=None,
                    avatar_data=None,
                )
            )
            if result.rowcount == 0:
                raise AccountError("账号不存在")
        updated = self.account_for_id(account_id)
        if updated is None:
            raise AccountError("账号不存在")
        return updated

    def set_custom_avatar(
        self,
        account_id: str,
        data: bytes,
        mime_type: str,
    ) -> Account:
        if not data or mime_type != "image/webp":
            raise AccountError("头像数据不正确")
        self.initialize()
        avatar_token = secrets.token_urlsafe(24)
        with self.engine.begin() as connection:
            result = connection.execute(
                update(users)
                .where(users.c.id == account_id)
                .values(
                    avatar_token=avatar_token,
                    avatar_mime=mime_type,
                    avatar_data=data,
                )
            )
            if result.rowcount == 0:
                raise AccountError("账号不存在")
        updated = self.account_for_id(account_id)
        if updated is None:
            raise AccountError("账号不存在")
        return updated

    def custom_avatar(self, avatar_token: str) -> tuple[bytes, str] | None:
        if not avatar_token or len(avatar_token) > 48:
            return None
        self.initialize()
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    select(users.c.avatar_data, users.c.avatar_mime).where(
                        users.c.avatar_token == avatar_token,
                        users.c.avatar_data.is_not(None),
                        users.c.avatar_mime.is_not(None),
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return bytes(row["avatar_data"]), str(row["avatar_mime"])

    def logout(self, token: str | None) -> None:
        if not token:
            return
        self.initialize()
        with self.engine.begin() as connection:
            connection.execute(
                delete(account_sessions).where(
                    account_sessions.c.token_hash == self._token_hash(token)
                )
            )

    def begin_registration_email_verification(
        self,
        email: str,
        policy: EmailPolicy,
        *,
        now: datetime | None = None,
    ) -> EmailChallenge:
        normalized_email, email_key = self._normalize_email(email)
        self.initialize()
        created_at = now or self._now()
        with self.engine.begin() as connection:
            owner_id = connection.execute(
                select(users.c.id).where(users.c.email_key == email_key)
            ).scalar_one_or_none()
            if owner_id is not None:
                raise AccountError("此邮箱已经绑定到其他账号")

            connection.execute(
                delete(registration_email_challenges).where(
                    registration_email_challenges.c.created_at
                    < created_at - timedelta(days=2)
                )
            )
            latest_sent_at = connection.execute(
                select(
                    func.max(registration_email_challenges.c.created_at)
                ).where(
                    registration_email_challenges.c.email_key == email_key
                )
            ).scalar_one_or_none()
            self._enforce_email_cooldown(
                latest_sent_at,
                policy=policy,
                now=created_at,
            )
            self._claim_email_send_quota(
                connection,
                identity_scope="email",
                identity_key=hashlib.sha256(
                    email_key.encode("utf-8")
                ).hexdigest(),
                identity_label="邮箱",
                policy=policy,
                now=created_at,
            )
            connection.execute(
                update(registration_email_challenges)
                .where(
                    registration_email_challenges.c.email_key == email_key,
                    registration_email_challenges.c.consumed_at.is_(None),
                )
                .values(consumed_at=created_at)
            )
            challenge_id = secrets.token_urlsafe(18)
            code = f"{secrets.randbelow(1_000_000):06d}"
            salt = secrets.token_bytes(16)
            expires_at = created_at + timedelta(
                minutes=policy.code_ttl_minutes
            )
            connection.execute(
                insert(registration_email_challenges).values(
                    id=challenge_id,
                    email=normalized_email,
                    email_key=email_key,
                    code_salt=salt,
                    code_hash=self._email_code_hash(code, salt),
                    expires_at=expires_at,
                    failed_attempts=0,
                    consumed_at=None,
                    created_at=created_at,
                )
            )
        return EmailChallenge(
            id=challenge_id,
            account_id=None,
            email=normalized_email,
            purpose=REGISTER_EMAIL_PURPOSE,
            code=code,
            expires_at=self._iso_datetime(expires_at),
        )

    def begin_email_binding(
        self,
        account_id: str,
        email: str,
        policy: EmailPolicy,
        *,
        now: datetime | None = None,
    ) -> EmailChallenge:
        normalized_email, email_key = self._normalize_email(email)
        self.initialize()
        created_at = now or self._now()
        with self.engine.begin() as connection:
            row = connection.execute(
                select(users.c.id, users.c.email_key).where(
                    users.c.id == account_id
                )
            ).mappings().first()
            if row is None:
                raise AccountError("账号不存在")
            if row["email_key"] == email_key:
                raise AccountError("此邮箱已经绑定到当前账号")
            owner_id = connection.execute(
                select(users.c.id).where(users.c.email_key == email_key)
            ).scalar_one_or_none()
            if owner_id is not None and owner_id != account_id:
                raise AccountError("此邮箱已经绑定到其他账号")
            return self._create_email_challenge(
                connection,
                account_id=account_id,
                email=normalized_email,
                email_key=email_key,
                purpose=BIND_EMAIL_PURPOSE,
                policy=policy,
                now=created_at,
            )

    def begin_email_unbinding(
        self,
        account_id: str,
        policy: EmailPolicy,
        *,
        now: datetime | None = None,
    ) -> EmailChallenge:
        self.initialize()
        created_at = now or self._now()
        with self.engine.begin() as connection:
            row = connection.execute(
                select(users.c.email, users.c.email_key).where(
                    users.c.id == account_id
                )
            ).mappings().first()
            if row is None:
                raise AccountError("账号不存在")
            if not row["email"] or not row["email_key"]:
                raise AccountError("当前账号尚未绑定邮箱")
            return self._create_email_challenge(
                connection,
                account_id=account_id,
                email=row["email"],
                email_key=row["email_key"],
                purpose=UNBIND_EMAIL_PURPOSE,
                policy=policy,
                now=created_at,
            )

    def begin_password_reset(
        self,
        identifier: str,
        policy: EmailPolicy,
        *,
        now: datetime | None = None,
    ) -> EmailChallenge | None:
        self.initialize()
        created_at = now or self._now()
        with self.engine.begin() as connection:
            row = self._account_email_for_identifier(connection, identifier)
            if row is None or not row["email"] or not row["email_key"]:
                return None
            return self._create_email_challenge(
                connection,
                account_id=row["id"],
                email=row["email"],
                email_key=row["email_key"],
                purpose=RESET_PASSWORD_PURPOSE,
                policy=policy,
                now=created_at,
            )

    def cancel_email_challenge(self, challenge_id: str) -> None:
        if not challenge_id:
            return
        self.initialize()
        with self.engine.begin() as connection:
            connection.execute(
                delete(email_verification_challenges).where(
                    email_verification_challenges.c.id == challenge_id
                )
            )
            connection.execute(
                delete(registration_email_challenges).where(
                    registration_email_challenges.c.id == challenge_id
                )
            )

    def verify_and_bind_email(
        self,
        account_id: str,
        email: str,
        code: str,
        policy: EmailPolicy,
        *,
        now: datetime | None = None,
    ) -> Account:
        normalized_email, email_key = self._normalize_email(email)
        self._validate_email_code(code)
        self.initialize()
        verified_at = now or self._now()
        verification_error: str | None = None
        updated_row: Mapping[str, Any] | None = None
        try:
            with self.engine.begin() as connection:
                verification_error = self._consume_email_challenge(
                    connection,
                    account_id=account_id,
                    purpose=BIND_EMAIL_PURPOSE,
                    email_key=email_key,
                    code=code,
                    policy=policy,
                    now=verified_at,
                )
                if verification_error is None:
                    owner_id = connection.execute(
                        select(users.c.id).where(
                            users.c.email_key == email_key,
                            users.c.id != account_id,
                        )
                    ).scalar_one_or_none()
                    if owner_id is not None:
                        verification_error = "此邮箱已经绑定到其他账号"
                    else:
                        result = connection.execute(
                            update(users)
                            .where(users.c.id == account_id)
                            .values(
                                email=normalized_email,
                                email_key=email_key,
                                email_verified_at=verified_at,
                            )
                        )
                        if result.rowcount == 0:
                            verification_error = "账号不存在"
                        else:
                            updated_row = self._select_account_row(
                                connection, account_id
                            )
        except IntegrityError as error:
            raise AccountError("此邮箱已经绑定到其他账号") from error
        if verification_error is not None:
            raise AccountError(verification_error)
        if updated_row is None:
            raise AccountError("账号不存在")
        return self._account_from_row(updated_row)

    def verify_and_unbind_email(
        self,
        account_id: str,
        code: str,
        policy: EmailPolicy,
        *,
        now: datetime | None = None,
    ) -> Account:
        self._validate_email_code(code)
        self.initialize()
        verified_at = now or self._now()
        verification_error: str | None = None
        updated_row: Mapping[str, Any] | None = None
        with self.engine.begin() as connection:
            row = connection.execute(
                select(users.c.email_key).where(users.c.id == account_id)
            ).mappings().first()
            if row is None:
                verification_error = "账号不存在"
            elif not row["email_key"]:
                verification_error = "当前账号尚未绑定邮箱"
            else:
                verification_error = self._consume_email_challenge(
                    connection,
                    account_id=account_id,
                    purpose=UNBIND_EMAIL_PURPOSE,
                    email_key=row["email_key"],
                    code=code,
                    policy=policy,
                    now=verified_at,
                )
                if verification_error is None:
                    connection.execute(
                        update(users)
                        .where(users.c.id == account_id)
                        .values(
                            email=None,
                            email_key=None,
                            email_verified_at=None,
                        )
                    )
                    connection.execute(
                        update(email_verification_challenges)
                        .where(
                            email_verification_challenges.c.account_id
                            == account_id,
                            email_verification_challenges.c.consumed_at.is_(
                                None
                            ),
                        )
                        .values(consumed_at=verified_at)
                    )
                    updated_row = self._select_account_row(
                        connection, account_id
                    )
        if verification_error is not None:
            raise AccountError(verification_error)
        if updated_row is None:
            raise AccountError("账号不存在")
        return self._account_from_row(updated_row)

    def reset_password_with_code(
        self,
        identifier: str,
        code: str,
        new_password: str,
        policy: EmailPolicy,
        *,
        now: datetime | None = None,
    ) -> str:
        self._validate_email_code(code)
        self._validate_password(new_password)
        self.initialize()
        reset_at = now or self._now()
        verification_error: str | None = None
        account_id: str | None = None
        with self.engine.begin() as connection:
            row = self._account_email_for_identifier(connection, identifier)
            if row is None or not row["email_key"]:
                verification_error = "验证码无效或已过期"
            else:
                verification_error = self._consume_email_challenge(
                    connection,
                    account_id=row["id"],
                    purpose=RESET_PASSWORD_PURPOSE,
                    email_key=row["email_key"],
                    code=code,
                    policy=policy,
                    now=reset_at,
                )
                if verification_error is None:
                    account_id = row["id"]
                    salt = secrets.token_bytes(16)
                    connection.execute(
                        update(users)
                        .where(users.c.id == row["id"])
                        .values(
                            password_salt=salt,
                            password_hash=self._password_hash(
                                new_password, salt
                            ),
                        )
                    )
                    connection.execute(
                        delete(account_sessions).where(
                            account_sessions.c.account_id == row["id"]
                        )
                    )
        if verification_error is not None:
            raise AccountError(verification_error)
        if account_id is None:
            raise AccountError("验证码无效或已过期")
        return account_id

    def _create_email_challenge(
        self,
        connection,
        *,
        account_id: str,
        email: str,
        email_key: str,
        purpose: str,
        policy: EmailPolicy,
        now: datetime,
    ) -> EmailChallenge:
        connection.execute(
            delete(email_verification_challenges).where(
                email_verification_challenges.c.created_at
                < now - timedelta(days=2)
            )
        )
        latest_sent_at = connection.execute(
            select(func.max(email_verification_challenges.c.created_at)).where(
                email_verification_challenges.c.account_id == account_id
            )
        ).scalar_one_or_none()
        self._enforce_email_cooldown(
            latest_sent_at,
            policy=policy,
            now=now,
        )
        self._claim_email_send_quota(
            connection,
            identity_scope="account",
            identity_key=account_id,
            identity_label="账号",
            policy=policy,
            now=now,
        )
        connection.execute(
            update(email_verification_challenges)
            .where(
                email_verification_challenges.c.account_id == account_id,
                email_verification_challenges.c.purpose == purpose,
                email_verification_challenges.c.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        challenge_id = secrets.token_urlsafe(18)
        code = f"{secrets.randbelow(1_000_000):06d}"
        salt = secrets.token_bytes(16)
        expires_at = now + timedelta(minutes=policy.code_ttl_minutes)
        connection.execute(
            insert(email_verification_challenges).values(
                id=challenge_id,
                account_id=account_id,
                purpose=purpose,
                email=email,
                email_key=email_key,
                code_salt=salt,
                code_hash=self._email_code_hash(code, salt),
                expires_at=expires_at,
                failed_attempts=0,
                consumed_at=None,
                created_at=now,
            )
        )
        return EmailChallenge(
            id=challenge_id,
            account_id=account_id,
            email=email,
            purpose=purpose,
            code=code,
            expires_at=self._iso_datetime(expires_at),
        )

    @staticmethod
    def _enforce_email_cooldown(
        latest_sent_at: datetime | None,
        *,
        policy: EmailPolicy,
        now: datetime,
    ) -> None:
        if latest_sent_at is None:
            return
        next_send_at = latest_sent_at + timedelta(
            seconds=policy.cooldown_seconds
        )
        if next_send_at <= now:
            return
        remaining = max(
            1,
            int((next_send_at - now).total_seconds()) + 1,
        )
        raise AccountError(f"请等待 {remaining} 秒后再发送验证码")

    def _claim_email_send_quota(
        self,
        connection,
        *,
        identity_scope: str,
        identity_key: str,
        identity_label: str,
        policy: EmailPolicy,
        now: datetime,
    ) -> None:
        quota_day = self._email_quota_day(now, policy.timezone_name)
        scopes = (
            ("server", "all", policy.server_daily_limit),
            (
                identity_scope,
                identity_key,
                policy.account_daily_limit,
            ),
        )
        for scope, scope_key, limit in scopes:
            values = {
                "scope": scope,
                "scope_key": scope_key,
                "quota_day": quota_day,
                "send_count": 0,
                "updated_at": now,
            }
            if connection.dialect.name == "mysql":
                statement = mysql_insert(email_send_quotas).values(**values)
                connection.execute(
                    statement.on_duplicate_key_update(
                        updated_at=now
                    )
                )
            elif connection.dialect.name == "sqlite":
                connection.execute(
                    sqlite_insert(email_send_quotas)
                    .values(**values)
                    .on_conflict_do_nothing(
                        index_elements=["scope", "scope_key", "quota_day"]
                    )
                )
            else:
                existing = connection.execute(
                    select(email_send_quotas.c.scope).where(
                        email_send_quotas.c.scope == scope,
                        email_send_quotas.c.scope_key == scope_key,
                        email_send_quotas.c.quota_day == quota_day,
                    )
                ).first()
                if existing is None:
                    connection.execute(insert(email_send_quotas).values(**values))

            result = connection.execute(
                update(email_send_quotas)
                .where(
                    email_send_quotas.c.scope == scope,
                    email_send_quotas.c.scope_key == scope_key,
                    email_send_quotas.c.quota_day == quota_day,
                    email_send_quotas.c.send_count < limit,
                )
                .values(
                    send_count=email_send_quotas.c.send_count + 1,
                    updated_at=now,
                )
            )
            if result.rowcount != 1:
                if scope == identity_scope:
                    raise AccountError(
                        f"每个{identity_label}每天最多发送 "
                        f"{limit} 封验证码邮件"
                    )
                raise AccountError("今天的邮件发送额度已经用完")

    def _consume_email_challenge(
        self,
        connection,
        *,
        account_id: str,
        purpose: str,
        email_key: str,
        code: str,
        policy: EmailPolicy,
        now: datetime,
    ) -> str | None:
        return self._consume_challenge(
            connection,
            challenge_table=email_verification_challenges,
            conditions=(
                email_verification_challenges.c.account_id == account_id,
                email_verification_challenges.c.purpose == purpose,
                email_verification_challenges.c.email_key == email_key,
            ),
            code=code,
            policy=policy,
            now=now,
        )

    def _consume_registration_email_challenge(
        self,
        connection,
        *,
        email_key: str,
        code: str,
        policy: EmailPolicy,
        now: datetime,
    ) -> str | None:
        return self._consume_challenge(
            connection,
            challenge_table=registration_email_challenges,
            conditions=(
                registration_email_challenges.c.email_key == email_key,
            ),
            code=code,
            policy=policy,
            now=now,
        )

    def _consume_challenge(
        self,
        connection,
        *,
        challenge_table,
        conditions: tuple,
        code: str,
        policy: EmailPolicy,
        now: datetime,
    ) -> str | None:
        row = connection.execute(
            select(
                challenge_table.c.id,
                challenge_table.c.code_salt,
                challenge_table.c.code_hash,
                challenge_table.c.expires_at,
                challenge_table.c.failed_attempts,
            )
            .where(
                *conditions,
                challenge_table.c.consumed_at.is_(None),
            )
            .order_by(challenge_table.c.created_at.desc())
            .limit(1)
            .with_for_update()
        ).mappings().first()
        if row is None or row["expires_at"] <= now:
            return "验证码无效或已过期"
        if row["failed_attempts"] >= policy.max_code_attempts:
            return "验证码尝试次数过多，请重新获取"
        candidate_hash = self._email_code_hash(code, row["code_salt"])
        if not secrets.compare_digest(candidate_hash, row["code_hash"]):
            failed_attempts = row["failed_attempts"] + 1
            values: dict[str, Any] = {"failed_attempts": failed_attempts}
            if failed_attempts >= policy.max_code_attempts:
                values["consumed_at"] = now
            connection.execute(
                update(challenge_table)
                .where(challenge_table.c.id == row["id"])
                .values(**values)
            )
            if failed_attempts >= policy.max_code_attempts:
                return "验证码尝试次数过多，请重新获取"
            return "验证码不正确"
        connection.execute(
            update(challenge_table)
            .where(challenge_table.c.id == row["id"])
            .values(consumed_at=now)
        )
        return None

    @staticmethod
    def _select_account_row(connection, account_id: str):
        return connection.execute(
            select(
                users.c.id,
                users.c.username,
                users.c.player_name,
                users.c.player_name_changed_at,
                users.c.avatar_preset,
                users.c.avatar_token,
                users.c.email,
                users.c.email_verified_at,
                users.c.created_at,
            ).where(users.c.id == account_id)
        ).mappings().first()

    def _account_email_for_identifier(self, connection, identifier: str):
        normalized = identifier.strip()
        if not normalized or len(normalized) > EMAIL_MAX_LENGTH:
            return None
        conditions = []
        if len(normalized) <= USERNAME_MAX_LENGTH:
            conditions.append(users.c.username_key == normalized.casefold())
        if "@" in normalized:
            try:
                _, email_key = self._normalize_email(normalized)
            except AccountError:
                email_key = ""
            if email_key:
                conditions.append(users.c.email_key == email_key)
        if not conditions:
            return None
        return connection.execute(
            select(
                users.c.id,
                users.c.email,
                users.c.email_key,
            ).where(or_(*conditions))
        ).mappings().first()

    def session_is_active(self, account_id: str, token_hash: str) -> bool:
        if not account_id or not token_hash:
            return False
        self.initialize()
        now = self._now()
        with self.engine.connect() as connection:
            return connection.execute(
                select(account_sessions.c.token_hash).where(
                    account_sessions.c.account_id == account_id,
                    account_sessions.c.token_hash == token_hash,
                    account_sessions.c.expires_at > now,
                )
            ).first() is not None

    def record_game_match(
        self,
        *,
        game_key: str,
        game_name: str | None = None,
        match_id: str,
        room_code: str,
        winner: str,
        reason: str,
        started_at: str,
        ended_at: str,
        details: dict[str, Any],
        players: list[dict[str, Any]],
        ranked: bool = True,
        participant_count: int | None = None,
    ) -> bool:
        if (
            not players
            or len(game_key) > 32
            or game_key not in GAME_NAMES
        ):
            return False
        self.initialize()
        try:
            with self.engine.begin() as connection:
                stored_game_name = game_name or GAME_NAMES.get(
                    game_key, game_key
                )
                existing_game = connection.execute(
                    select(games.c.name).where(games.c.key == game_key)
                ).scalar_one_or_none()
                if existing_game is None:
                    connection.execute(
                        insert(games).values(
                            key=game_key,
                            name=stored_game_name,
                            enabled=True,
                            created_at=self._now(),
                        )
                    )
                elif existing_game != stored_game_name:
                    connection.execute(
                        update(games)
                        .where(games.c.key == game_key)
                        .values(name=stored_game_name, enabled=True)
                    )
                existing = connection.execute(
                    select(matches.c.id).where(matches.c.id == match_id)
                ).scalar_one_or_none()
                if existing is not None:
                    return False
                connection.execute(
                    insert(matches).values(
                        id=match_id,
                        game_key=game_key,
                        room_code=room_code,
                        mode=self._match_mode(game_key, details),
                        player_count=participant_count or len(players),
                        winner=winner,
                        reason=reason,
                        ranked=ranked,
                        assassination_hit=None,
                        ending_route=None,
                        recruitment_hit=None,
                        started_at=self._parse_datetime(started_at),
                        ended_at=self._parse_datetime(ended_at),
                        details_json=details,
                    )
                )
                connection.execute(
                    insert(match_players),
                    [
                        {
                            "match_id": match_id,
                            "account_id": player["accountId"],
                            "player_name": player["playerName"],
                            "seat": player["seat"],
                            "role": player["role"],
                            "alignment": player["alignment"],
                            "won": player["won"],
                            "outcome": self._game_outcome(
                                game_key=game_key,
                                winner=winner,
                                won=bool(player["won"]),
                            ),
                            "is_host": player["isHost"],
                            "score_value": player.get(
                                "scoreValue", player.get("scoreMs")
                            ),
                        }
                        for player in players
                    ],
                )
        except IntegrityError:
            return False
        return True

    def history_for_account(
        self,
        account_id: str,
        *,
        game_key: str | None = None,
        game_mode: str | None = None,
        game_variant: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        self.initialize()
        statement = (
            select(
                matches.c.id,
                matches.c.game_key,
                games.c.name.label("game_name"),
                matches.c.room_code,
                matches.c.mode,
                matches.c.player_count,
                matches.c.winner,
                matches.c.reason,
                matches.c.ranked,
                matches.c.assassination_hit,
                matches.c.ended_at,
                match_players.c.player_name,
                match_players.c.role,
                match_players.c.alignment,
                match_players.c.won,
                match_players.c.outcome,
                match_players.c.score_value,
                matches.c.details_json,
            )
            .select_from(
                match_players.join(
                    matches, matches.c.id == match_players.c.match_id
                ).join(games, games.c.key == matches.c.game_key)
            )
            .where(match_players.c.account_id == account_id)
            .order_by(matches.c.ended_at.desc())
            .limit(min(max(limit, 1), 100))
        )
        if game_key is not None:
            statement = statement.where(matches.c.game_key == game_key)
        if game_mode is not None:
            statement = statement.where(matches.c.mode == game_mode)
        statement = self._filter_game_variant(
            statement, game_key, game_variant
        )
        with self.engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [self._history_row(row) for row in rows]

    def summary_for_account(
        self,
        account_id: str,
        *,
        game_key: str | None = None,
        game_mode: str | None = None,
        game_variant: str | None = None,
    ) -> dict[str, int | float | None]:
        self.initialize()
        if _game_score_kind(game_key) == "time_trial":
            statement = (
                select(
                    func.count().label("games"),
                    func.min(match_players.c.score_value).label("best_ms"),
                    func.avg(match_players.c.score_value).label("average_ms"),
                )
                .select_from(
                    match_players.join(
                        matches, matches.c.id == match_players.c.match_id
                    )
                )
                .where(
                    match_players.c.account_id == account_id,
                    matches.c.game_key == game_key,
                    match_players.c.score_value.is_not(None),
                )
            )
            if game_mode is not None:
                statement = statement.where(matches.c.mode == game_mode)
            statement = self._filter_game_variant(
                statement, game_key, game_variant
            )
            with self.engine.connect() as connection:
                row = connection.execute(statement).mappings().one()
            return {
                "games": int(row["games"]),
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "winRate": 0,
                "goodGames": 0,
                "goodWins": 0,
                "evilGames": 0,
                "evilWins": 0,
                "bestMs": (
                    int(row["best_ms"])
                    if row["best_ms"] is not None
                    else None
                ),
                "averageMs": (
                    round(float(row["average_ms"]))
                    if row["average_ms"] is not None
                    else None
                ),
            }
        if _game_score_kind(game_key) == "high_score":
            statement = (
                select(
                    func.count().label("games"),
                    func.max(match_players.c.score_value).label("best_score"),
                    func.avg(match_players.c.score_value).label("average_score"),
                )
                .select_from(
                    match_players.join(
                        matches, matches.c.id == match_players.c.match_id
                    )
                )
                .where(
                    match_players.c.account_id == account_id,
                    matches.c.game_key == game_key,
                    match_players.c.score_value.is_not(None),
                )
            )
            if game_mode is not None:
                statement = statement.where(matches.c.mode == game_mode)
            with self.engine.connect() as connection:
                row = connection.execute(statement).mappings().one()
            return {
                "games": int(row["games"]),
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "winRate": 0,
                "goodGames": 0,
                "goodWins": 0,
                "evilGames": 0,
                "evilWins": 0,
                "bestMs": None,
                "averageMs": None,
                "bestScore": (
                    int(row["best_score"])
                    if row["best_score"] is not None
                    else None
                ),
                "averageScore": (
                    round(float(row["average_score"]))
                    if row["average_score"] is not None
                    else None
                ),
            }
        statement = (
            select(
                func.count().label("games"),
                func.coalesce(
                    func.sum(case((match_players.c.outcome == "win", 1), else_=0)),
                    0,
                ).label("wins"),
                func.coalesce(
                    func.sum(case((match_players.c.outcome == "draw", 1), else_=0)),
                    0,
                ).label("draws"),
                func.coalesce(
                    func.sum(case((match_players.c.outcome == "loss", 1), else_=0)),
                    0,
                ).label("losses"),
                func.coalesce(
                    func.sum(
                        case((match_players.c.alignment == "good", 1), else_=0)
                    ),
                    0,
                ).label("good_games"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (match_players.c.alignment == "good")
                                & (match_players.c.outcome == "win"),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("good_wins"),
                func.coalesce(
                    func.sum(
                        case((match_players.c.alignment == "evil", 1), else_=0)
                    ),
                    0,
                ).label("evil_games"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (match_players.c.alignment == "evil")
                                & (match_players.c.outcome == "win"),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("evil_wins"),
                func.coalesce(
                    func.sum(
                        case((matches.c.ending_route == "missions", 1), else_=0)
                    ),
                    0,
                ).label("mission_route_games"),
                func.coalesce(
                    func.sum(
                        case((matches.c.recruitment_hit.is_not(None), 1), else_=0)
                    ),
                    0,
                ).label("recruitment_attempts"),
                func.coalesce(
                    func.sum(
                        case((matches.c.recruitment_hit.is_(True), 1), else_=0)
                    ),
                    0,
                ).label("recruitment_hits"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                matches.c.ending_route
                                == "dissenting_assassination",
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("dissenting_assassination_attempts"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (
                                    matches.c.ending_route
                                    == "dissenting_assassination"
                                )
                                & matches.c.assassination_hit.is_(True),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("dissenting_assassination_hits"),
            )
            .select_from(
                match_players.join(
                    matches, matches.c.id == match_players.c.match_id
                )
            )
            .where(match_players.c.account_id == account_id)
        )
        if game_key is not None:
            statement = statement.where(matches.c.game_key == game_key)
        else:
            statement = statement.where(matches.c.game_key.not_in(SCORED_GAME_KEYS))
        if game_mode is not None:
            statement = statement.where(matches.c.mode == game_mode)
        statement = self._filter_game_variant(
            statement, game_key, game_variant
        )
        with self.engine.connect() as connection:
            row = connection.execute(statement).mappings().one()
        game_count = int(row["games"])
        win_count = int(row["wins"])
        return {
            "games": game_count,
            "wins": win_count,
            "draws": int(row["draws"]),
            "losses": int(row["losses"]),
            "winRate": round(win_count / game_count * 100, 1) if game_count else 0,
            "goodGames": int(row["good_games"]),
            "goodWins": int(row["good_wins"]),
            "evilGames": int(row["evil_games"]),
            "evilWins": int(row["evil_wins"]),
            "missionRouteGames": int(row["mission_route_games"]),
            "recruitmentAttempts": int(row["recruitment_attempts"]),
            "recruitmentHits": int(row["recruitment_hits"]),
            "dissentingAssassinationAttempts": int(
                row["dissenting_assassination_attempts"]
            ),
            "dissentingAssassinationHits": int(
                row["dissenting_assassination_hits"]
            ),
        }

    def leaderboard(
        self,
        *,
        game_key: str,
        game_mode: str | None = None,
        game_variant: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        self.initialize()
        if _game_score_kind(game_key) == "time_trial":
            attempt_count = func.count().label("games")
            best_ms = func.min(match_players.c.score_value).label("best_ms")
            average_ms = func.avg(match_players.c.score_value).label("average_ms")
            statement = (
                select(
                    users.c.id,
                    users.c.player_name,
                    users.c.avatar_preset,
                    users.c.avatar_token,
                    attempt_count,
                    best_ms,
                    average_ms,
                )
                .select_from(
                    match_players.join(
                        matches, matches.c.id == match_players.c.match_id
                    ).join(users, users.c.id == match_players.c.account_id)
                )
                .where(
                    matches.c.game_key == game_key,
                    matches.c.ranked.is_(True),
                    match_players.c.score_value.is_not(None),
                )
                .group_by(
                    users.c.id,
                    users.c.player_name,
                    users.c.avatar_preset,
                    users.c.avatar_token,
                    users.c.created_at,
                )
                .order_by(
                    best_ms.asc(),
                    average_ms.asc(),
                    attempt_count.desc(),
                    users.c.created_at.asc(),
                )
                .limit(min(max(limit, 1), 100))
            )
            if game_mode is not None:
                statement = statement.where(matches.c.mode == game_mode)
            statement = self._filter_game_variant(
                statement, game_key, game_variant
            )
            with self.engine.connect() as connection:
                rows = connection.execute(statement).mappings().all()
            return [
                {
                    "rank": index,
                    "accountId": row["id"],
                    "playerName": row["player_name"],
                    "avatarUrl": self._avatar_url_from_row(row),
                    "games": int(row["games"]),
                    "wins": 0,
                    "draws": 0,
                    "winRate": 0,
                    "bestMs": int(row["best_ms"]),
                    "averageMs": round(float(row["average_ms"])),
                }
                for index, row in enumerate(rows, start=1)
            ]
        if _game_score_kind(game_key) == "high_score":
            attempt_count = func.count().label("games")
            best_score = func.max(match_players.c.score_value).label("best_score")
            average_score = func.avg(match_players.c.score_value).label("average_score")
            statement = (
                select(
                    users.c.id,
                    users.c.player_name,
                    users.c.avatar_preset,
                    users.c.avatar_token,
                    attempt_count,
                    best_score,
                    average_score,
                )
                .select_from(
                    match_players.join(
                        matches, matches.c.id == match_players.c.match_id
                    ).join(users, users.c.id == match_players.c.account_id)
                )
                .where(
                    matches.c.game_key == game_key,
                    matches.c.ranked.is_(True),
                    match_players.c.score_value.is_not(None),
                )
                .group_by(
                    users.c.id,
                    users.c.player_name,
                    users.c.avatar_preset,
                    users.c.avatar_token,
                    users.c.created_at,
                )
                .order_by(
                    best_score.desc(),
                    average_score.desc(),
                    attempt_count.desc(),
                    users.c.created_at.asc(),
                )
                .limit(min(max(limit, 1), 100))
            )
            if game_mode is not None:
                statement = statement.where(matches.c.mode == game_mode)
            with self.engine.connect() as connection:
                rows = connection.execute(statement).mappings().all()
            return [
                {
                    "rank": index,
                    "accountId": row["id"],
                    "playerName": row["player_name"],
                    "avatarUrl": self._avatar_url_from_row(row),
                    "games": int(row["games"]),
                    "wins": 0,
                    "draws": 0,
                    "winRate": 0,
                    "bestScore": int(row["best_score"]),
                    "averageScore": round(float(row["average_score"])),
                }
                for index, row in enumerate(rows, start=1)
            ]
        game_count = func.count().label("games")
        win_count = func.coalesce(
            func.sum(case((match_players.c.outcome == "win", 1), else_=0)), 0
        ).label("wins")
        draw_count = func.coalesce(
            func.sum(case((match_players.c.outcome == "draw", 1), else_=0)), 0
        ).label("draws")
        statement = (
            select(
                users.c.id,
                users.c.player_name,
                users.c.avatar_preset,
                users.c.avatar_token,
                game_count,
                win_count,
                draw_count,
            )
            .select_from(
                match_players.join(
                    matches, matches.c.id == match_players.c.match_id
                ).join(users, users.c.id == match_players.c.account_id)
            )
            .where(matches.c.ranked.is_(True))
            .group_by(
                users.c.id,
                users.c.player_name,
                users.c.avatar_preset,
                users.c.avatar_token,
                users.c.created_at,
            )
            .order_by(
                win_count.desc(),
                (win_count * 1.0 / game_count).desc(),
                game_count.desc(),
                users.c.created_at.asc(),
            )
            .limit(min(max(limit, 1), 100))
        )
        statement = statement.where(matches.c.game_key == game_key)
        if game_mode is not None:
            statement = statement.where(matches.c.mode == game_mode)
        statement = self._filter_game_variant(
            statement, game_key, game_variant
        )
        with self.engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            {
                "rank": index,
                "accountId": row["id"],
                "playerName": row["player_name"],
                "avatarUrl": self._avatar_url_from_row(row),
                "games": int(row["games"]),
                "wins": int(row["wins"]),
                "draws": int(row["draws"]),
                "winRate": round(row["wins"] / row["games"] * 100, 1),
            }
            for index, row in enumerate(rows, start=1)
        ]

    @staticmethod
    def _filter_game_variant(
        statement,
        game_key: str | None,
        game_variant: str | None,
    ):
        if game_variant is None:
            return statement
        definition = (
            game_registration(game_key)
            if game_key is not None
            else None
        )
        if definition is None:
            raise AccountError("这个游戏不支持战绩统计分组")
        try:
            selector = definition.records.variant_selector(game_variant)
        except GameRecordQueryError as error:
            raise AccountError(str(error)) from error

        detail_value = matches.c.details_json[selector.details_key]
        if isinstance(selector.value, bool):
            expression = detail_value.as_boolean()
            if selector.include_missing:
                return statement.where(expression.is_not(not selector.value))
            return statement.where(expression.is_(selector.value))
        if isinstance(selector.value, int):
            expression = detail_value.as_integer()
        else:
            expression = detail_value.as_string()
        criterion = expression == selector.value
        if selector.include_missing:
            criterion = or_(criterion, expression.is_(None))
        return statement.where(criterion)

    def match_for_account(
        self, match_id: str, account_id: str
    ) -> dict | None:
        self.initialize()
        statement = (
            select(
                matches.c.id,
                matches.c.game_key,
                games.c.name.label("game_name"),
                matches.c.room_code,
                matches.c.mode,
                matches.c.player_count,
                matches.c.winner,
                matches.c.reason,
                matches.c.ranked,
                matches.c.assassination_hit,
                matches.c.ending_route,
                matches.c.recruitment_hit,
                matches.c.started_at,
                matches.c.ended_at,
                matches.c.details_json,
            )
            .select_from(
                matches.join(
                    match_players,
                    match_players.c.match_id == matches.c.id,
                ).join(games, games.c.key == matches.c.game_key)
            )
            .where(
                matches.c.id == match_id,
                match_players.c.account_id == account_id,
            )
        )
        with self.engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        details = row["details_json"]
        if isinstance(details, str):
            details = json.loads(details)
        return {
            "id": row["id"],
            "gameKey": row["game_key"],
            "gameName": row["game_name"],
            "roomCode": row["room_code"],
            "gameMode": row["mode"],
            "playerCount": row["player_count"],
            "winner": row["winner"],
            "reason": row["reason"],
            "ranked": bool(row["ranked"]),
            "assassinationHit": (
                bool(row["assassination_hit"])
                if row["assassination_hit"] is not None
                else None
            ),
            "endingRoute": row["ending_route"],
            "recruitmentHit": (
                bool(row["recruitment_hit"])
                if row["recruitment_hit"] is not None
                else None
            ),
            "startedAt": self._iso_datetime(row["started_at"]),
            "endedAt": self._iso_datetime(row["ended_at"]),
            "details": details,
        }

    def _create_session(self, account_id: str) -> str:
        token = secrets.token_urlsafe(32)
        now = self._now()
        replaced_existing = False
        with self.engine.begin() as connection:
            # Serialize simultaneous logins for the same account. The unique
            # account index is the final database-level invariant.
            connection.execute(
                select(users.c.id)
                .where(users.c.id == account_id)
                .with_for_update()
            ).scalar_one()
            deleted = connection.execute(
                delete(account_sessions).where(
                    account_sessions.c.account_id == account_id
                )
            )
            replaced_existing = bool(deleted.rowcount)
            connection.execute(
                insert(account_sessions).values(
                    token_hash=self._token_hash(token),
                    account_id=account_id,
                    expires_at=now + SESSION_LIFETIME,
                    created_at=now,
                )
            )
        if replaced_existing:
            logger.info(
                "Previous account login session replaced",
                extra={
                    "account_id": account_id,
                    "event": "account.session_replaced",
                },
            )
        return token

    @classmethod
    def _history_row(cls, row: Mapping[str, Any]) -> dict:
        details = row.get("details_json")
        if isinstance(details, str):
            details = json.loads(details)
        score_kind = _game_score_kind(row["game_key"])
        return {
            "id": row["id"],
            "gameKey": row["game_key"],
            "gameName": row["game_name"],
            "roomCode": row["room_code"],
            "playerCount": row["player_count"],
            "winner": row["winner"],
            "reason": row["reason"],
            "ranked": bool(row["ranked"]),
            "assassinationHit": (
                bool(row["assassination_hit"])
                if row["assassination_hit"] is not None
                else None
            ),
            "endedAt": cls._iso_datetime(row["ended_at"]),
            "playerName": row["player_name"],
            "role": row["role"],
            "alignment": row["alignment"],
            "won": bool(row["won"]),
            "outcome": row["outcome"],
            "scoreMs": (
                int(row["score_value"])
                if row["score_value"] is not None
                and score_kind == "time_trial"
                else None
            ),
            "scoreValue": (
                int(row["score_value"])
                if row["score_value"] is not None
                and score_kind == "high_score"
                else None
            ),
            "gameMode": row["mode"],
        }

    @staticmethod
    def _game_outcome(*, game_key: str, winner: str, won: bool) -> str:
        if _game_score_kind(game_key) != "outcome" and won:
            return "completed"
        if winner == "draw":
            return "draw"
        return "win" if won else "loss"

    @staticmethod
    def _match_mode(game_key: str, details: dict[str, Any]) -> str:
        definition = game_registration(game_key)
        return (
            definition.records.match_mode(details)
            if definition
            else "standard"
        )

    @classmethod
    def _account_from_row(cls, row: Mapping[str, Any]) -> Account:
        return Account(
            id=row["id"],
            username=row["username"],
            player_name=row["player_name"],
            player_name_changed_at=(
                cls._iso_datetime(row["player_name_changed_at"])
                if row["player_name_changed_at"] is not None
                else None
            ),
            avatar_preset=row["avatar_preset"],
            avatar_token=row["avatar_token"],
            email=row.get("email"),
            email_verified_at=(
                cls._iso_datetime(row["email_verified_at"])
                if row.get("email_verified_at") is not None
                else None
            ),
            created_at=cls._iso_datetime(row["created_at"]),
        )

    @staticmethod
    def _avatar_url_from_row(row: Mapping[str, Any]) -> str:
        avatar_token = row.get("avatar_token")
        if avatar_token:
            return f"/api/avatars/{avatar_token}"
        return f"/avatars/{row['avatar_preset']}.webp"

    @staticmethod
    def _normalize_username(username: str) -> tuple[str, str]:
        normalized = username.strip()
        if not USERNAME_MIN_LENGTH <= len(normalized) <= USERNAME_MAX_LENGTH:
            raise AccountError("账号名需要 2–50 个字符")
        if not all(
            character.isalnum() or character in "._@+-"
            for character in normalized
        ):
            raise AccountError(
                "账号名只能使用文字、数字及 . _ @ + -"
            )
        return normalized, normalized.casefold()

    @staticmethod
    def _normalize_player_name(player_name: str) -> tuple[str, str]:
        normalized = " ".join(player_name.strip().split())
        if not 1 <= len(normalized) <= 12:
            raise AccountError("游戏昵称需要 1–12 个字符")
        return normalized, normalized.casefold()

    @staticmethod
    def _normalize_email(email: str) -> tuple[str, str]:
        normalized = email.strip()
        if (
            not normalized
            or len(normalized) > EMAIL_MAX_LENGTH
            or normalized.count("@") != 1
            or any(character.isspace() for character in normalized)
        ):
            raise AccountError("请输入有效的邮箱地址")
        local_part, domain = normalized.rsplit("@", 1)
        if (
            not local_part
            or len(local_part) > 64
            or local_part.startswith(".")
            or local_part.endswith(".")
            or ".." in local_part
            or EMAIL_LOCAL_PART_PATTERN.fullmatch(local_part) is None
        ):
            raise AccountError("请输入有效的邮箱地址")
        try:
            ascii_domain = domain.rstrip(".").encode("idna").decode("ascii")
        except UnicodeError as error:
            raise AccountError("请输入有效的邮箱地址") from error
        labels = ascii_domain.split(".")
        if (
            len(labels) < 2
            or len(ascii_domain) > 253
            or any(
                not label
                or len(label) > 63
                or label.startswith("-")
                or label.endswith("-")
                or not all(
                    character.isalnum() or character == "-"
                    for character in label
                )
                for label in labels
            )
        ):
            raise AccountError("请输入有效的邮箱地址")
        canonical = f"{local_part}@{ascii_domain.lower()}"
        if len(canonical) > EMAIL_MAX_LENGTH:
            raise AccountError("请输入有效的邮箱地址")
        return canonical, canonical.casefold()

    @staticmethod
    def _validate_email_code(code: str) -> None:
        if len(code) != 6 or not code.isascii() or not code.isdigit():
            raise AccountError("验证码需要是 6 位数字")

    @staticmethod
    def _email_code_hash(code: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            code.encode("ascii"),
            salt,
            120_000,
            dklen=32,
        )

    @staticmethod
    def _email_quota_day(now: datetime, timezone_name: str):
        try:
            local_timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            local_timezone = ZoneInfo("Asia/Shanghai")
        aware_utc = now.replace(tzinfo=timezone.utc)
        return aware_utc.astimezone(local_timezone).date()

    @staticmethod
    def _validate_password(password: str) -> None:
        if not 6 <= len(password) <= 128:
            raise AccountError("密码需要 6–128 个字符")

    @staticmethod
    def _password_hash(password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=32,
        )

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def session_fingerprint(cls, token: str) -> str:
        return cls._token_hash(token)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed

    @staticmethod
    def _iso_datetime(value: datetime | str) -> str:
        if isinstance(value, str):
            return value
        return value.replace(tzinfo=timezone.utc).isoformat(timespec="seconds")


_stores: dict[str, AccountStore] = {}


def account_store() -> AccountStore:
    source = os.environ.get("DATABASE_URL")
    if source is None:
        default_path = (
            Path(__file__).resolve().parents[2] / ".data" / "game-hall.sqlite3"
        )
        source = os.environ.get("GAME_HALL_DB_PATH") or os.environ.get(
            "AVALON_DB_PATH", str(default_path)
        )
    key = normalize_database_url(source)
    if key not in _stores:
        _stores[key] = AccountStore(key)
    return _stores[key]
