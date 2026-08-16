"""Allow unrestricted player name changes.

Revision ID: 20260816_20
Revises: 20260816_19
Create Date: 2026-08-16
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260816_20"
down_revision: str | None = "20260816_19"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _player_name_key(player_name: str) -> str:
    return " ".join(player_name.strip().split()).casefold()


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("player_name_key", sa.String(length=24), nullable=True)
        )

    connection = op.get_bind()
    users = sa.table(
        "users",
        sa.column("id", sa.String(length=32)),
        sa.column("player_name", sa.String(length=12)),
        sa.column("player_name_key", sa.String(length=24)),
    )
    rows = connection.execute(sa.select(users.c.id, users.c.player_name))
    for row in rows:
        connection.execute(
            users.update()
            .where(users.c.id == row.id)
            .values(player_name_key=_player_name_key(row.player_name))
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "player_name_key",
            existing_type=sa.String(length=24),
            nullable=False,
        )
        batch_op.create_unique_constraint(
            "uq_users_player_name_key",
            ["player_name_key"],
        )
        batch_op.drop_column("player_name_changed_at")

    op.drop_table("player_name_claims")


def downgrade() -> None:
    op.create_table(
        "player_name_claims",
        sa.Column("name_key", sa.String(length=24), nullable=False),
        sa.Column("account_id", sa.String(length=32), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["users.id"],
            name=op.f("fk_player_name_claims_account_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "name_key",
            name=op.f("pk_player_name_claims"),
        ),
    )
    op.create_index(
        "ix_player_name_claims_account_id",
        "player_name_claims",
        ["account_id"],
        unique=False,
    )

    connection = op.get_bind()
    users = sa.table(
        "users",
        sa.column("id", sa.String(length=32)),
        sa.column("player_name_key", sa.String(length=24)),
        sa.column("created_at", sa.DateTime()),
    )
    claims = sa.table(
        "player_name_claims",
        sa.column("name_key", sa.String(length=24)),
        sa.column("account_id", sa.String(length=32)),
        sa.column("claimed_at", sa.DateTime()),
    )
    rows = connection.execute(
        sa.select(users.c.id, users.c.player_name_key, users.c.created_at)
    )
    claim_rows = [
        {
            "name_key": row.player_name_key,
            "account_id": row.id,
            "claimed_at": row.created_at,
        }
        for row in rows
    ]
    if claim_rows:
        connection.execute(claims.insert(), claim_rows)

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_player_name_key", type_="unique")
        batch_op.drop_column("player_name_key")
        batch_op.add_column(
            sa.Column("player_name_changed_at", sa.DateTime(), nullable=True)
        )
