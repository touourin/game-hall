from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .game.models import Room, Role


SESSION_LIFETIME = timedelta(days=30)


class AccountError(ValueError):
    pass


@dataclass(frozen=True)
class Account:
    id: str
    username: str
    display_name: str
    created_at: str

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "username": self.username,
            "displayName": self.display_name,
            "createdAt": self.created_at,
        }


class AccountStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)

    def initialize(self) -> None:
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    username_key TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    password_salt BLOB NOT NULL,
                    password_hash BLOB NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS account_sessions (
                    token_hash TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL REFERENCES accounts(id)
                        ON DELETE CASCADE,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS account_sessions_account_idx
                    ON account_sessions(account_id);

                CREATE TABLE IF NOT EXISTS matches (
                    id TEXT PRIMARY KEY,
                    room_code TEXT NOT NULL,
                    player_count INTEGER NOT NULL,
                    winner TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    ranked INTEGER NOT NULL,
                    assassination_hit INTEGER,
                    started_at TEXT NOT NULL,
                    ended_at TEXT NOT NULL,
                    details_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS match_players (
                    match_id TEXT NOT NULL REFERENCES matches(id)
                        ON DELETE CASCADE,
                    account_id TEXT NOT NULL REFERENCES accounts(id)
                        ON DELETE CASCADE,
                    display_name TEXT NOT NULL,
                    seat INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    alignment TEXT NOT NULL,
                    won INTEGER NOT NULL,
                    is_host INTEGER NOT NULL,
                    PRIMARY KEY (match_id, account_id)
                );

                CREATE INDEX IF NOT EXISTS match_players_account_idx
                    ON match_players(account_id, match_id);
                """
            )

    def register(
        self, username: str, password: str, display_name: str
    ) -> tuple[Account, str]:
        normalized_username, username_key = self._normalize_username(username)
        normalized_display_name = self._normalize_display_name(display_name)
        self._validate_password(password)
        salt = secrets.token_bytes(16)
        password_hash = self._password_hash(password, salt)
        account = Account(
            id=secrets.token_urlsafe(12),
            username=normalized_username,
            display_name=normalized_display_name,
            created_at=self._now().isoformat(timespec="seconds"),
        )
        self.initialize()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO accounts (
                        id, username, username_key, display_name,
                        password_salt, password_hash, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        account.id,
                        account.username,
                        username_key,
                        account.display_name,
                        salt,
                        password_hash,
                        account.created_at,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise AccountError("这个账号名已经被注册") from exc
        return account, self._create_session(account.id)

    def login(self, username: str, password: str) -> tuple[Account, str]:
        _, username_key = self._normalize_username(username)
        self._validate_password(password)
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, username, display_name, password_salt,
                       password_hash, created_at
                FROM accounts
                WHERE username_key = ?
                """,
                (username_key,),
            ).fetchone()
        if row is None:
            raise AccountError("账号或密码不正确")
        candidate_hash = self._password_hash(password, row["password_salt"])
        if not secrets.compare_digest(candidate_hash, row["password_hash"]):
            raise AccountError("账号或密码不正确")
        account = self._account_from_row(row)
        return account, self._create_session(account.id)

    def account_for_token(self, token: str | None) -> Account | None:
        if not token:
            return None
        self.initialize()
        now = self._now().isoformat(timespec="seconds")
        token_hash = self._token_hash(token)
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM account_sessions WHERE expires_at <= ?",
                (now,),
            )
            row = connection.execute(
                """
                SELECT accounts.id, accounts.username,
                       accounts.display_name, accounts.created_at
                FROM account_sessions
                JOIN accounts ON accounts.id = account_sessions.account_id
                WHERE account_sessions.token_hash = ?
                  AND account_sessions.expires_at > ?
                """,
                (token_hash, now),
            ).fetchone()
        return self._account_from_row(row) if row is not None else None

    def logout(self, token: str | None) -> None:
        if not token:
            return
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM account_sessions WHERE token_hash = ?",
                (self._token_hash(token),),
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
        assassination_target = (
            room.player(room.assassin_target_id)
            if room.assassin_target_id is not None
            else None
        )
        assassination_hit = (
            assassination_target.role == Role.MERLIN
            if assassination_target is not None
            else None
        )
        ended_at = self._now().isoformat(timespec="seconds")
        details = self._match_details(room)
        self.initialize()
        with self._connect() as connection:
            inserted = connection.execute(
                """
                INSERT OR IGNORE INTO matches (
                    id, room_code, player_count, winner, reason, ranked,
                    assassination_hit, started_at, ended_at, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    room.game_id,
                    room.code,
                    len(room.players),
                    room.winner.value,
                    room.win_reason,
                    int(ranked),
                    (
                        int(assassination_hit)
                        if assassination_hit is not None
                        else None
                    ),
                    room.game_started_at,
                    ended_at,
                    json.dumps(details, ensure_ascii=False),
                ),
            ).rowcount
            if not inserted:
                return False
            connection.executemany(
                """
                INSERT INTO match_players (
                    match_id, account_id, display_name, seat, role,
                    alignment, won, is_host
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        room.game_id,
                        player.account_id,
                        player.name,
                        player.seat,
                        player.role.value,
                        player.alignment.value,
                        int(player.alignment == room.winner),
                        int(player.id == room.host_id),
                    )
                    for player in human_players
                    if player.account_id is not None
                ],
            )
        return True

    def history_for_account(
        self, account_id: str, *, limit: int = 50
    ) -> list[dict]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT matches.id, matches.room_code, matches.player_count,
                       matches.winner, matches.reason, matches.ranked,
                       matches.assassination_hit, matches.ended_at,
                       match_players.display_name, match_players.role,
                       match_players.alignment, match_players.won
                FROM match_players
                JOIN matches ON matches.id = match_players.match_id
                WHERE match_players.account_id = ?
                ORDER BY matches.ended_at DESC
                LIMIT ?
                """,
                (account_id, min(max(limit, 1), 100)),
            ).fetchall()
        return [self._history_row(row) for row in rows]

    def summary_for_account(self, account_id: str) -> dict[str, int | float]:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS games,
                       COALESCE(SUM(won), 0) AS wins,
                       COALESCE(SUM(alignment = 'good'), 0) AS good_games,
                       COALESCE(SUM(alignment = 'good' AND won = 1), 0)
                           AS good_wins,
                       COALESCE(SUM(alignment = 'evil'), 0) AS evil_games,
                       COALESCE(SUM(alignment = 'evil' AND won = 1), 0)
                           AS evil_wins
                FROM match_players
                WHERE account_id = ?
                """,
                (account_id,),
            ).fetchone()
        games = int(row["games"])
        wins = int(row["wins"])
        return {
            "games": games,
            "wins": wins,
            "winRate": round(wins / games * 100, 1) if games else 0,
            "goodGames": int(row["good_games"]),
            "goodWins": int(row["good_wins"]),
            "evilGames": int(row["evil_games"]),
            "evilWins": int(row["evil_wins"]),
        }

    def leaderboard(self, *, limit: int = 50) -> list[dict]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT accounts.id, accounts.display_name,
                       COUNT(*) AS games,
                       SUM(match_players.won) AS wins
                FROM match_players
                JOIN matches ON matches.id = match_players.match_id
                JOIN accounts ON accounts.id = match_players.account_id
                WHERE matches.ranked = 1
                GROUP BY accounts.id, accounts.display_name
                ORDER BY wins DESC,
                         (1.0 * wins / COUNT(*)) DESC,
                         games DESC,
                         accounts.created_at ASC
                LIMIT ?
                """,
                (min(max(limit, 1), 100),),
            ).fetchall()
        return [
            {
                "rank": index,
                "accountId": row["id"],
                "displayName": row["display_name"],
                "games": int(row["games"]),
                "wins": int(row["wins"]),
                "winRate": round(row["wins"] / row["games"] * 100, 1),
            }
            for index, row in enumerate(rows, start=1)
        ]

    def match_for_account(
        self, match_id: str, account_id: str
    ) -> dict | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT matches.id, matches.room_code, matches.player_count,
                       matches.winner, matches.reason, matches.ranked,
                       matches.assassination_hit, matches.started_at,
                       matches.ended_at, matches.details_json
                FROM matches
                JOIN match_players ON match_players.match_id = matches.id
                WHERE matches.id = ? AND match_players.account_id = ?
                """,
                (match_id, account_id),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
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
            "startedAt": row["started_at"],
            "endedAt": row["ended_at"],
            "details": json.loads(row["details_json"]),
        }

    def _create_session(self, account_id: str) -> str:
        token = secrets.token_urlsafe(32)
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO account_sessions (
                    token_hash, account_id, expires_at, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    self._token_hash(token),
                    account_id,
                    (now + SESSION_LIFETIME).isoformat(timespec="seconds"),
                    now.isoformat(timespec="seconds"),
                ),
            )
        return token

    @staticmethod
    def _history_row(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
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
            "endedAt": row["ended_at"],
            "displayName": row["display_name"],
            "role": row["role"],
            "alignment": row["alignment"],
            "won": bool(row["won"]),
        }

    @staticmethod
    def _match_details(room: Room) -> dict:
        return {
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "seat": player.seat,
                    "isBot": player.is_bot,
                    "role": player.role.value,
                    "alignment": player.alignment.value,
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
        }

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        if self.database_path != ":memory:":
            connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @staticmethod
    def _account_from_row(row: sqlite3.Row) -> Account:
        return Account(
            id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _normalize_username(username: str) -> tuple[str, str]:
        normalized = username.strip()
        if not 2 <= len(normalized) <= 20:
            raise AccountError("账号名需要 2–20 个字符")
        if not all(character.isalnum() or character in "_-" for character in normalized):
            raise AccountError("账号名只能使用文字、数字、下划线或短横线")
        return normalized, normalized.casefold()

    @staticmethod
    def _normalize_display_name(display_name: str) -> str:
        normalized = " ".join(display_name.strip().split())
        if not normalized:
            raise AccountError("请输入显示名称")
        if len(normalized) > 12:
            raise AccountError("显示名称最多 12 个字符")
        return normalized

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
        return datetime.now(timezone.utc)


_stores: dict[str, AccountStore] = {}


def account_store() -> AccountStore:
    default_path = Path(__file__).resolve().parents[2] / ".data" / "avalon.sqlite3"
    path = os.environ.get("AVALON_DB_PATH", str(default_path))
    if path not in _stores:
        _stores[path] = AccountStore(path)
    return _stores[path]
