"""Record explicit win, loss, draw, and completion outcomes.

Revision ID: 20260801_05
Revises: 20260801_04
Create Date: 2026-08-01
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_05"
down_revision: str | None = "20260801_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "match_players",
        sa.Column(
            "outcome",
            sa.String(length=16),
            nullable=False,
            server_default="loss",
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE match_players
            SET outcome = CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM matches
                    WHERE matches.id = match_players.match_id
                      AND matches.winner = 'draw'
                ) THEN 'draw'
                WHEN EXISTS (
                    SELECT 1
                    FROM matches
                    WHERE matches.id = match_players.match_id
                      AND matches.game_key = 'reaction'
                ) THEN 'completed'
                WHEN won = 1 THEN 'win'
                ELSE 'loss'
            END
            """
        )
    )
    with op.batch_alter_table("match_players") as batch_op:
        batch_op.alter_column(
            "outcome",
            existing_type=sa.String(length=16),
            existing_nullable=False,
            server_default=None,
        )


def downgrade() -> None:
    with op.batch_alter_table("match_players") as batch_op:
        batch_op.drop_column("outcome")
