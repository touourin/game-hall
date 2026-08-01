"""Add the Texas Hold'em game catalog entry.

Revision ID: 20260801_08
Revises: 20260801_07
Create Date: 2026-08-01
"""

from datetime import datetime
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_08"
down_revision: str | None = "20260801_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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
                "key": "poker",
                "name": "德州扑克",
                "enabled": True,
                "created_at": datetime(2026, 8, 1),
            }
        ],
    )


def downgrade() -> None:
    games_table = sa.table("games", sa.column("key", sa.String()))
    op.execute(games_table.delete().where(games_table.c.key == "poker"))
