"""Allow longer email-style account usernames.

Revision ID: 20260803_12
Revises: 20260803_11
Create Date: 2026-08-03
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260803_12"
down_revision: str | None = "20260803_11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=20),
            type_=sa.String(length=64),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "username_key",
            existing_type=sa.String(length=40),
            type_=sa.String(length=192),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "username_key",
            existing_type=sa.String(length=192),
            type_=sa.String(length=40),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=64),
            type_=sa.String(length=20),
            existing_nullable=False,
        )
