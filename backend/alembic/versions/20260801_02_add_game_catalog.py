"""Add the first game hall catalog entries.

Revision ID: 20260801_02
Revises: 20260801_01
Create Date: 2026-08-01
"""

from datetime import datetime
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_02"
down_revision: str | None = "20260801_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


GAME_ROWS = [
    ("gomoku", "五子棋"),
    ("xiangqi", "中国象棋"),
    ("go", "围棋"),
    ("doudizhu", "斗地主"),
]


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
                "key": key,
                "name": name,
                "enabled": True,
                "created_at": datetime(2026, 8, 1),
            }
            for key, name in GAME_ROWS
        ],
    )


def downgrade() -> None:
    games_table = sa.table("games", sa.column("key", sa.String()))
    op.execute(
        games_table.delete().where(
            games_table.c.key.in_([key for key, _ in GAME_ROWS])
        )
    )
