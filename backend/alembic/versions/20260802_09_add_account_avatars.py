"""Add account avatar fields.

Revision ID: 20260802_09
Revises: 20260801_08
Create Date: 2026-08-02
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import MEDIUMBLOB


revision: str = "20260802_09"
down_revision: str | None = "20260801_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "avatar_preset",
            sa.String(length=32),
            nullable=False,
            server_default="moon-fox",
        ),
    )
    op.add_column(
        "users",
        sa.Column("avatar_token", sa.String(length=48), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("avatar_mime", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "avatar_data",
            sa.LargeBinary().with_variant(MEDIUMBLOB(), "mysql"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_users_avatar_token",
        "users",
        ["avatar_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_avatar_token", table_name="users")
    op.drop_column("users", "avatar_data")
    op.drop_column("users", "avatar_mime")
    op.drop_column("users", "avatar_token")
    op.drop_column("users", "avatar_preset")
