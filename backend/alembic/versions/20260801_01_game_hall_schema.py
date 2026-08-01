"""Create the initial game hall account and match schema.

Revision ID: 20260801_01
Revises:
Create Date: 2026-08-01
"""

from typing import Sequence
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=20), nullable=False),
        sa.Column("username_key", sa.String(length=40), nullable=False),
        sa.Column("player_name", sa.String(length=12), nullable=False),
        sa.Column("password_salt", sa.LargeBinary(length=32), nullable=False),
        sa.Column("password_hash", sa.LargeBinary(length=64), nullable=False),
        sa.Column("player_name_changed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username_key", name=op.f("uq_users_username_key")),
    )
    op.create_table(
        "player_name_claims",
        sa.Column("name_key", sa.String(length=24), nullable=False),
        sa.Column("account_id", sa.String(length=32), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["users.id"],
            name=op.f("fk_player_name_claims_account_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("name_key", name=op.f("pk_player_name_claims")),
    )
    op.create_index(
        "ix_player_name_claims_account_id",
        "player_name_claims",
        ["account_id"],
        unique=False,
    )
    op.create_table(
        "games",
        sa.Column("key", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_games")),
    )
    op.create_table(
        "account_sessions",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("account_id", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["users.id"],
            name=op.f("fk_account_sessions_account_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("token_hash", name=op.f("pk_account_sessions")),
    )
    op.create_index(
        "ix_account_sessions_account_id",
        "account_sessions",
        ["account_id"],
        unique=False,
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("game_key", sa.String(length=32), nullable=False),
        sa.Column("room_code", sa.String(length=8), nullable=False),
        sa.Column("player_count", sa.Integer(), nullable=False),
        sa.Column("winner", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("ranked", sa.Boolean(), nullable=False),
        sa.Column("assassination_hit", sa.Boolean(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["game_key"],
            ["games.key"],
            name=op.f("fk_matches_game_key_games"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matches")),
    )
    op.create_index(
        "ix_matches_game_ended",
        "matches",
        ["game_key", "ended_at"],
        unique=False,
    )
    op.create_table(
        "match_players",
        sa.Column("match_id", sa.String(length=32), nullable=False),
        sa.Column("account_id", sa.String(length=32), nullable=False),
        sa.Column("player_name", sa.String(length=12), nullable=False),
        sa.Column("seat", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("alignment", sa.String(length=16), nullable=False),
        sa.Column("won", sa.Boolean(), nullable=False),
        sa.Column("is_host", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["users.id"],
            name=op.f("fk_match_players_account_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["matches.id"],
            name=op.f("fk_match_players_match_id_matches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "match_id", "account_id", name=op.f("pk_match_players")
        ),
    )
    op.create_index(
        "ix_match_players_account_match",
        "match_players",
        ["account_id", "match_id"],
        unique=False,
    )
    games_table = sa.table(
        "games",
        sa.column("key", sa.String()),
        sa.column("name", sa.String()),
        sa.column("enabled", sa.Boolean()),
        sa.column("created_at", sa.DateTime()),
    )
    op.bulk_insert(
        games_table,
        [
            {
                "key": "avalon",
                "name": "阿瓦隆",
                "enabled": True,
                "created_at": datetime(2026, 8, 1),
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_match_players_account_match", table_name="match_players")
    op.drop_table("match_players")
    op.drop_index("ix_matches_game_ended", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_account_sessions_account_id", table_name="account_sessions")
    op.drop_table("account_sessions")
    op.drop_table("games")
    op.drop_index("ix_player_name_claims_account_id", table_name="player_name_claims")
    op.drop_table("player_name_claims")
    op.drop_table("users")
