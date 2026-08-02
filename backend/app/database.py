from __future__ import annotations

from pathlib import Path

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    event,
)
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)

users = Table(
    "users",
    metadata,
    Column("id", String(32), primary_key=True),
    Column("username", String(20), nullable=False),
    Column("username_key", String(40), nullable=False, unique=True),
    Column("player_name", String(12), nullable=False),
    Column("password_salt", LargeBinary(32), nullable=False),
    Column("password_hash", LargeBinary(64), nullable=False),
    Column("player_name_changed_at", DateTime(), nullable=True),
    Column(
        "avatar_preset",
        String(32),
        nullable=False,
        server_default="moon-fox",
    ),
    Column("avatar_token", String(48), nullable=True, unique=True),
    Column("avatar_mime", String(32), nullable=True),
    Column(
        "avatar_data",
        LargeBinary().with_variant(MEDIUMBLOB(), "mysql"),
        nullable=True,
    ),
    Column("created_at", DateTime(), nullable=False),
)

player_name_claims = Table(
    "player_name_claims",
    metadata,
    Column("name_key", String(24), primary_key=True),
    Column(
        "account_id",
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("claimed_at", DateTime(), nullable=False),
)
Index("ix_player_name_claims_account_id", player_name_claims.c.account_id)

account_sessions = Table(
    "account_sessions",
    metadata,
    Column("token_hash", String(64), primary_key=True),
    Column(
        "account_id",
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("expires_at", DateTime(), nullable=False),
    Column("created_at", DateTime(), nullable=False),
)
Index("ix_account_sessions_account_id", account_sessions.c.account_id)

games = Table(
    "games",
    metadata,
    Column("key", String(32), primary_key=True),
    Column("name", String(80), nullable=False),
    Column("enabled", Boolean(), nullable=False, default=True),
    Column("created_at", DateTime(), nullable=False),
)

matches = Table(
    "matches",
    metadata,
    Column("id", String(32), primary_key=True),
    Column(
        "game_key",
        String(32),
        ForeignKey("games.key", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("room_code", String(8), nullable=False),
    Column(
        "mode",
        String(32),
        nullable=False,
        default="standard",
        server_default="standard",
    ),
    Column("player_count", Integer(), nullable=False),
    Column("winner", String(16), nullable=False),
    Column("reason", Text(), nullable=False),
    Column("ranked", Boolean(), nullable=False),
    Column("assassination_hit", Boolean(), nullable=True),
    Column("ending_route", String(32), nullable=True),
    Column("recruitment_hit", Boolean(), nullable=True),
    Column("started_at", DateTime(), nullable=False),
    Column("ended_at", DateTime(), nullable=False),
    Column("details_json", JSON(), nullable=False),
)
Index("ix_matches_game_ended", matches.c.game_key, matches.c.ended_at)
Index(
    "ix_matches_game_mode_ended",
    matches.c.game_key,
    matches.c.mode,
    matches.c.ended_at,
)

match_players = Table(
    "match_players",
    metadata,
    Column(
        "match_id",
        String(32),
        ForeignKey("matches.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "account_id",
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("player_name", String(12), nullable=False),
    Column("seat", Integer(), nullable=False),
    Column("role", String(32), nullable=False),
    Column("alignment", String(16), nullable=False),
    Column("won", Boolean(), nullable=False),
    Column("outcome", String(16), nullable=False),
    Column("is_host", Boolean(), nullable=False),
    Column("score_ms", Integer(), nullable=True),
)
Index("ix_match_players_account_match", match_players.c.account_id, match_players.c.match_id)


def normalize_database_url(source: str | Path) -> str:
    value = str(source)
    if value == ":memory:":
        return "sqlite+pysqlite:///:memory:"
    if "://" in value:
        return value
    return f"sqlite+pysqlite:///{Path(value).expanduser().resolve()}"


def build_engine(source: str | Path) -> Engine:
    url = normalize_database_url(source)
    options: dict = {"pool_pre_ping": True}
    if url == "sqlite+pysqlite:///:memory:":
        options.update(
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    engine = create_engine(url, **options)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def _enable_sqlite_foreign_keys(dbapi_connection, _) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()
