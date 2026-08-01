"""Reset reaction results for the frame-aligned timing model.

Revision ID: 20260801_06
Revises: 20260801_05
Create Date: 2026-08-01
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_06"
down_revision: str | None = "20260801_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    matches = sa.table(
        "matches",
        sa.column("id", sa.String(length=64)),
        sa.column("game_key", sa.String(length=32)),
    )
    match_players = sa.table(
        "match_players",
        sa.column("match_id", sa.String(length=64)),
    )
    reaction_match_ids = sa.select(matches.c.id).where(
        matches.c.game_key == "reaction"
    )
    connection = op.get_bind()
    connection.execute(
        sa.delete(match_players).where(
            match_players.c.match_id.in_(reaction_match_ids)
        )
    )
    connection.execute(
        sa.delete(matches).where(matches.c.game_key == "reaction")
    )


def downgrade() -> None:
    # Deleted timing results cannot be reconstructed.
    pass
