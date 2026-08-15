"""Add Critical Crossing to the game catalog.

Revision ID: 20260815_16
Revises: 20260815_15
Create Date: 2026-08-15
"""

from datetime import datetime
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260815_16"
down_revision: str | None = "20260815_15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GAME_KEY = "critical_crossing"


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
        [{
            "key": GAME_KEY,
            "name": "临界穿越",
            "enabled": True,
            "created_at": datetime(2026, 8, 15),
        }],
    )


def downgrade() -> None:
    games_table = sa.table("games", sa.column("key", sa.String()))
    op.execute(games_table.delete().where(games_table.c.key == GAME_KEY))
