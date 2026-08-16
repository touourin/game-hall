"""Add verified account emails, email challenges, and send quotas.

Revision ID: 20260816_18
Revises: 20260815_17
Create Date: 2026-08-16
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260816_18"
down_revision: str | None = "20260815_17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("email", sa.String(length=254), nullable=True)
        )
        batch_op.add_column(
            sa.Column("email_key", sa.String(length=254), nullable=True)
        )
        batch_op.add_column(
            sa.Column("email_verified_at", sa.DateTime(), nullable=True)
        )
        batch_op.create_index(
            "ux_users_email_key",
            ["email_key"],
            unique=True,
        )

    op.create_table(
        "email_verification_challenges",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("account_id", sa.String(length=32), nullable=False),
        sa.Column("purpose", sa.String(length=24), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["users.id"],
            name=op.f(
                "fk_email_verification_challenges_account_id_users"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_email_verification_challenges"),
        ),
    )
    op.create_index(
        "ix_email_challenges_account_purpose_created",
        "email_verification_challenges",
        ["account_id", "purpose", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_email_challenges_expires_at",
        "email_verification_challenges",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "email_send_quotas",
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("scope_key", sa.String(length=64), nullable=False),
        sa.Column("quota_day", sa.Date(), nullable=False),
        sa.Column(
            "send_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint(
            "scope",
            "scope_key",
            "quota_day",
            name=op.f("pk_email_send_quotas"),
        ),
    )


def downgrade() -> None:
    op.drop_table("email_send_quotas")
    op.drop_index(
        "ix_email_challenges_expires_at",
        table_name="email_verification_challenges",
    )
    op.drop_index(
        "ix_email_challenges_account_purpose_created",
        table_name="email_verification_challenges",
    )
    op.drop_table("email_verification_challenges")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ux_users_email_key")
        batch_op.drop_column("email_verified_at")
        batch_op.drop_column("email_key")
        batch_op.drop_column("email")
