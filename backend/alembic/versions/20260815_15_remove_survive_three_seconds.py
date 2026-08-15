"""Remove the retired Survive Three Seconds game and its records.

Revision ID: 20260815_15
Revises: 20260812_14
Create Date: 2026-08-15

The historical matches are intentionally discarded.  A downgrade restores
the catalog entry only; deleted match data cannot be reconstructed.
"""

from datetime import datetime
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260815_15"
down_revision: str | None = "20260812_14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RETIRED_GAME_KEY = "survive_three_seconds"


def upgrade() -> None:
    games_table = sa.table(
        "games",
        sa.column("key", sa.String()),
    )
    matches_table = sa.table(
        "matches",
        sa.column("id", sa.String()),
        sa.column("game_key", sa.String()),
    )
    match_players_table = sa.table(
        "match_players",
        sa.column("match_id", sa.String()),
    )
    retired_match_ids = sa.select(matches_table.c.id).where(
        matches_table.c.game_key == RETIRED_GAME_KEY
    )

    op.execute(
        match_players_table.delete().where(
            match_players_table.c.match_id.in_(retired_match_ids)
        )
    )
    op.execute(
        matches_table.delete().where(
            matches_table.c.game_key == RETIRED_GAME_KEY
        )
    )
    op.execute(
        games_table.delete().where(games_table.c.key == RETIRED_GAME_KEY)
    )


def downgrade() -> None:
    games_table = sa.table(
        "games",
        sa.column("key", sa.String()),
        sa.column("name", sa.String()),
        sa.column("enabled", sa.Boolean()),
        sa.column("created_at", sa.DateTime()),
    )
    op.bulk_insert(
        games_table,
        [{
            "key": RETIRED_GAME_KEY,
            "name": "坚持三秒",
            "enabled": True,
            "created_at": datetime(2026, 8, 15),
        }],
    )
