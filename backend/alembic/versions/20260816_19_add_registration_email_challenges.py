"""Add email challenges for registration before an account exists.

Revision ID: 20260816_19
Revises: 20260816_18
Create Date: 2026-08-16
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260816_19"
down_revision: str | None = "20260816_18"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "registration_email_challenges",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("email_key", sa.String(length=254), nullable=False),
        sa.Column("code_salt", sa.LargeBinary(length=32), nullable=False),
        sa.Column("code_hash", sa.LargeBinary(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column(
            "failed_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_registration_email_challenges"),
        ),
    )
    op.create_index(
        "ix_registration_email_challenges_email_created",
        "registration_email_challenges",
        ["email_key", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_registration_email_challenges_expires_at",
        "registration_email_challenges",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_registration_email_challenges_expires_at",
        table_name="registration_email_challenges",
    )
    op.drop_index(
        "ix_registration_email_challenges_email_created",
        table_name="registration_email_challenges",
    )
    op.drop_table("registration_email_challenges")
