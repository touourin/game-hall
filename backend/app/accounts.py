from __future__ import annotations

import hashlib
import json
import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import case, delete, func, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from .database import (
    account_sessions,
    build_engine,
    games,
    match_players,
    matches,
    metadata,
    normalize_database_url,
    player_name_claims,
    users,
)
from .games.avalon.models import ROLE_ALIGNMENT, Room, Role


SESSION_LIFETIME = timedelta(days=30)
PLAYER_NAME_CHANGE_INTERVAL = timedelta(days=30)
GAME_KEY = "avalon"
GAME_NAMES = {
    "avalon": "阿瓦隆",
    "gomoku": "五子棋",
    "xiangqi": "中国象棋",
    "go": "围棋",
    "poker": "德州扑克",
    "doudizhu": "斗地主",
    "junqi": "军旗",
    "reaction": "反应挑战",
    "schulte": "舒尔特方格",
    "minesweeper": "扫雷",
    "hanoi": "汉诺塔",
}
TIME_TRIAL_GAMES = {"reaction", "schulte", "minesweeper"}
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
    created_at: str

    @property
    def avatar_type(self) -> str:
        return "custom" if self.avatar_token is not None else "preset"

    @property
    def avatar_url(self) -> str:
        if self.avatar_token is not None:
            return f"/api/avatars/{self.avatar_token}"
        return f"/avatars/{self.avatar_preset}.webp"

    def as_dict(self) -> dict[str, str | None]:
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
            "createdAt": self.created_at,
        }


class AccountStore:
    def __init__(self, database_source: str | Path) -> None:
        self.database_url = normalize_database_url(database_source)
        self.engine: Engine = build_engine(self.database_url)
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        if self.engine.dialect.name == "sqlite":
            metadata.create_all(self.engine)
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

    def ping(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(select(1)).scalar_one()

    def dispose(self) -> None:
        self.engine.dispose()

    def register(
        self, username: str, password: str, player_name: str
    ) -> tuple[Account, str]:
        normalized_username, username_key = self._normalize_username(username)
        normalized_name, name_key = self._normalize_player_name(player_name)
        self._validate_password(password)
        salt = secrets.token_bytes(16)
        password_hash = self._password_hash(password, salt)
        created_at = self._now()
        avatar_preset = secrets.choice(AVATAR_PRESET_IDS)
        account = Account(
            id=secrets.token_urlsafe(12),
            username=normalized_username,
            player_name=normalized_name,
            player_name_changed_at=None,
            avatar_preset=avatar_preset,
            avatar_token=None,
            created_at=self._iso_datetime(created_at),
        )
        self.initialize()
        try:
            with self.engine.begin() as connection:
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
            raise AccountError("账号名或游戏昵称已经被使用") from exc
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

    def record_match(self, room: Room) -> bool:
        if (
            room.game_id is None
            or room.game_started_at is None
            or room.winner is None
            or room.win_reason is None
        ):
            return False
        human_players = [player for player in room.players if not player.is_bot]
        account_ids = [
            player.account_id
            for player in human_players
            if player.account_id is not None
        ]
        if not account_ids:
            return False
        ranked = (
            len(human_players) == len(room.players)
            and len(account_ids) == len(human_players)
            and len(set(account_ids)) == len(account_ids)
        )
        assassination_target_id = (
            room.dissenting_assassination_target_id
            or room.assassin_target_id
        )
        assassination_target = (
            room.player(assassination_target_id)
            if assassination_target_id is not None
            else None
        )
        assassination_hit = (
            assassination_target.role == Role.MERLIN
            if assassination_target is not None
            else None
        )
        ended_at = self._now()
        started_at = self._parse_datetime(room.game_started_at)
        details = self._match_details(room)
        self.initialize()
        try:
            with self.engine.begin() as connection:
                existing = connection.execute(
                    select(matches.c.id).where(matches.c.id == room.game_id)
                ).scalar_one_or_none()
                if existing is not None:
                    return False
                connection.execute(
                    insert(matches).values(
                        id=room.game_id,
                        game_key=GAME_KEY,
                        room_code=room.code,
                        mode=room.settings.mode.value,
                        player_count=len(room.players),
                        winner=room.winner.value,
                        reason=room.win_reason,
                        ranked=ranked,
                        assassination_hit=assassination_hit,
                        ending_route=room.ending_route,
                        recruitment_hit=room.dagger_hit,
                        started_at=started_at,
                        ended_at=ended_at,
                        details_json=details,
                    )
                )
                player_rows = [
                    {
                        "match_id": room.game_id,
                        "account_id": player.account_id,
                        "player_name": player.name,
                        "seat": player.seat,
                        "role": player.role.value,
                        "alignment": player.alignment.value,
                        "won": player.alignment == room.winner,
                        "outcome": (
                            "win" if player.alignment == room.winner else "loss"
                        ),
                        "is_host": player.id == room.host_id,
                    }
                    for player in human_players
                    if player.account_id is not None
                ]
                if player_rows:
                    connection.execute(insert(match_players), player_rows)
        except IntegrityError:
            return False
        return True

    def record_game_match(
        self,
        *,
        game_key: str,
        match_id: str,
        room_code: str,
        winner: str,
        reason: str,
        started_at: str,
        ended_at: str,
        details: dict[str, Any],
        players: list[dict[str, Any]],
        ranked: bool = True,
    ) -> bool:
        if game_key not in GAME_NAMES or not players:
            return False
        self.initialize()
        try:
            with self.engine.begin() as connection:
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
                        player_count=len(players),
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
                            "score_ms": player.get("scoreMs"),
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
                match_players.c.score_ms,
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
        with self.engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [self._history_row(row) for row in rows]

    def summary_for_account(
        self,
        account_id: str,
        *,
        game_key: str | None = None,
        game_mode: str | None = None,
    ) -> dict[str, int | float | None]:
        self.initialize()
        if game_key in TIME_TRIAL_GAMES:
            statement = (
                select(
                    func.count().label("games"),
                    func.min(match_players.c.score_ms).label("best_ms"),
                    func.avg(match_players.c.score_ms).label("average_ms"),
                )
                .select_from(
                    match_players.join(
                        matches, matches.c.id == match_players.c.match_id
                    )
                )
                .where(
                    match_players.c.account_id == account_id,
                    matches.c.game_key == game_key,
                    match_players.c.score_ms.is_not(None),
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
            statement = statement.where(matches.c.game_key.not_in(TIME_TRIAL_GAMES))
        if game_mode is not None:
            statement = statement.where(matches.c.mode == game_mode)
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
        limit: int = 50,
    ) -> list[dict]:
        self.initialize()
        if game_key in TIME_TRIAL_GAMES:
            attempt_count = func.count().label("games")
            best_ms = func.min(match_players.c.score_ms).label("best_ms")
            average_ms = func.avg(match_players.c.score_ms).label("average_ms")
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
                    match_players.c.score_ms.is_not(None),
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
        with self.engine.begin() as connection:
            connection.execute(
                insert(account_sessions).values(
                    token_hash=self._token_hash(token),
                    account_id=account_id,
                    expires_at=now + SESSION_LIFETIME,
                    created_at=now,
                )
            )
        return token

    @classmethod
    def _history_row(cls, row: Mapping[str, Any]) -> dict:
        details = row.get("details_json")
        if isinstance(details, str):
            details = json.loads(details)
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
                int(row["score_ms"])
                if row["score_ms"] is not None
                else None
            ),
            "gameMode": row["mode"],
        }

    @staticmethod
    def _game_outcome(*, game_key: str, winner: str, won: bool) -> str:
        if game_key in TIME_TRIAL_GAMES and won:
            return "completed"
        if winner == "draw":
            return "draw"
        return "win" if won else "loss"

    @staticmethod
    def _match_details(room: Room) -> dict:
        return {
            "mode": room.settings.mode.value,
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "seat": player.seat,
                    "isBot": player.is_bot,
                    "role": player.role.value,
                    "alignment": player.alignment.value,
                    "initialAlignment": ROLE_ALIGNMENT[player.role].value,
                    "finalAlignment": player.alignment.value,
                    "transformed": (
                        player.id == room.transformed_player_id
                    ),
                }
                for player in room.players
            ],
            "missions": [
                {
                    "number": mission.number,
                    "teamIds": mission.team_ids,
                    "success": mission.success,
                    "failCount": mission.fail_count,
                }
                for mission in room.mission_history
            ],
            "proposals": [
                {
                    "missionNumber": proposal.mission_number,
                    "attempt": proposal.attempt,
                    "leaderId": proposal.leader_id,
                    "teamIds": proposal.team_ids,
                    "votes": proposal.votes,
                    "accepted": proposal.accepted,
                }
                for proposal in room.proposal_history
            ],
            "ladyChecks": [
                {
                    "inspectorId": check.inspector_id,
                    "targetId": check.target_id,
                    "alignment": check.alignment.value,
                    "missionNumber": check.mission_number,
                }
                for check in room.lady_checks
            ],
            "assassinTargetId": room.assassin_target_id,
            "assassinationWasEarly": room.assassination_was_early,
            "courtUndercurrent": {
                "daggerCandidateIds": list(room.dagger_candidate_ids),
                "daggerTargetId": room.dagger_target_id,
                "daggerHit": room.dagger_hit,
                "transformedPlayerId": room.transformed_player_id,
                "eligibleTargetIds": (
                    [
                        player.id
                        for player in room.players
                        if player.id != room.transformed_player_id
                        and player.role
                        not in {
                            Role.ASSASSIN,
                            Role.MORGANA,
                            Role.MORDRED,
                            Role.MINION,
                        }
                    ]
                    if room.transformed_player_id is not None
                    else []
                ),
                "assassinationTargetId": (
                    room.dissenting_assassination_target_id
                ),
            },
            "endingRoute": room.ending_route,
        }

    @staticmethod
    def _match_mode(game_key: str, details: dict[str, Any]) -> str:
        if game_key == "minesweeper":
            state = details.get("state")
            if isinstance(state, dict):
                difficulty = state.get("difficulty")
                if isinstance(difficulty, str) and difficulty:
                    return difficulty
        return "standard"

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
        if not 2 <= len(normalized) <= 20:
            raise AccountError("账号名需要 2–20 个字符")
        if not all(
            character.isalnum() or character in "_-" for character in normalized
        ):
            raise AccountError("账号名只能使用文字、数字、下划线或短横线")
        return normalized, normalized.casefold()

    @staticmethod
    def _normalize_player_name(player_name: str) -> tuple[str, str]:
        normalized = " ".join(player_name.strip().split())
        if not 2 <= len(normalized) <= 12:
            raise AccountError("游戏昵称需要 2–12 个字符")
        return normalized, normalized.casefold()

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
