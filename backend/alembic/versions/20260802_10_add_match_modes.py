"""Add normalized match modes and Avalon ending metrics.

Revision ID: 20260802_10
Revises: 20260802_09
Create Date: 2026-08-02
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260802_10"
down_revision: str | None = "20260802_09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column(
            "mode",
            sa.String(length=32),
            nullable=False,
            server_default="standard",
        ),
    )
    op.add_column(
        "matches",
        sa.Column("ending_route", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column("recruitment_hit", sa.Boolean(), nullable=True),
    )
    connection = op.get_bind()
    if connection.dialect.name == "mysql":
        op.execute(
            sa.text(
                """
                UPDATE matches
                SET mode = CASE
                    WHEN game_key = 'minesweeper' THEN
                        COALESCE(
                            JSON_UNQUOTE(
                                JSON_EXTRACT(details_json, '$.state.difficulty')
                            ),
                            'standard'
                        )
                    ELSE 'standard'
                END
                """
            )
        )
    elif connection.dialect.name == "sqlite":
        op.execute(
            sa.text(
                """
                UPDATE matches
                SET mode = CASE
                    WHEN game_key = 'minesweeper' THEN
                        COALESCE(
                            json_extract(details_json, '$.state.difficulty'),
                            'standard'
                        )
                    ELSE 'standard'
                END
                """
            )
        )
    op.create_index(
        "ix_matches_game_mode_ended",
        "matches",
        ["game_key", "mode", "ended_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_matches_game_mode_ended", table_name="matches")
    with op.batch_alter_table("matches") as batch_op:
        batch_op.drop_column("recruitment_hit")
        batch_op.drop_column("ending_route")
        batch_op.drop_column("mode")
