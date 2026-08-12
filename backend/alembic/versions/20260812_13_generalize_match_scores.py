"""Generalize recorded solo scores beyond milliseconds.

Revision ID: 20260812_13
Revises: 20260803_12
Create Date: 2026-08-12
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260812_13"
down_revision: str | None = "20260803_12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("match_players") as batch_op:
        batch_op.alter_column(
            "score_ms",
            new_column_name="score_value",
            existing_type=sa.Integer(),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("match_players") as batch_op:
        batch_op.alter_column(
            "score_value",
            new_column_name="score_ms",
            existing_type=sa.Integer(),
            existing_nullable=True,
        )
