"""Add reaction time scores and game catalog entry.

Revision ID: 20260801_04
Revises: 20260801_03
Create Date: 2026-08-01
"""

from datetime import datetime
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_04"
down_revision: str | None = "20260801_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "match_players",
        sa.Column("score_ms", sa.Integer(), nullable=True),
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
                "key": "reaction",
                "name": "反应时间",
                "enabled": True,
                "created_at": datetime(2026, 8, 1),
            }
        ],
    )


def downgrade() -> None:
    games_table = sa.table("games", sa.column("key", sa.String()))
    op.execute(games_table.delete().where(games_table.c.key == "reaction"))
    op.drop_column("match_players", "score_ms")
