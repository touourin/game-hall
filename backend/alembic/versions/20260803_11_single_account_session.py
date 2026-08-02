"""Keep only one active login session for each registered account.

Revision ID: 20260803_11
Revises: 20260802_10
Create Date: 2026-08-03
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260803_11"
down_revision: str | None = "20260802_10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Existing deployments may have several valid tokens for one account.
    # Preserve the newest one so an ordinary upgrade does not log everybody
    # out, then make the invariant enforceable by the database.
    sessions = sa.table(
        "account_sessions",
        sa.column("token_hash", sa.String(length=64)),
        sa.column("account_id", sa.String(length=32)),
        sa.column("created_at", sa.DateTime()),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(
            sessions.c.token_hash,
            sessions.c.account_id,
            sessions.c.created_at,
        ).order_by(
            sessions.c.account_id,
            sessions.c.created_at.desc(),
            sessions.c.token_hash.desc(),
        )
    ).all()
    seen_accounts: set[str] = set()
    stale_tokens: list[str] = []
    for token_hash, account_id, _ in rows:
        if account_id in seen_accounts:
            stale_tokens.append(token_hash)
        else:
            seen_accounts.add(account_id)
    if stale_tokens:
        connection.execute(
            sa.delete(sessions).where(sessions.c.token_hash.in_(stale_tokens))
        )
    op.create_index(
        "ux_account_sessions_account_id",
        "account_sessions",
        ["account_id"],
        unique=True,
    )
    op.drop_index(
        "ix_account_sessions_account_id",
        table_name="account_sessions",
    )


def downgrade() -> None:
    op.create_index(
        "ix_account_sessions_account_id",
        "account_sessions",
        ["account_id"],
        unique=False,
    )
    op.drop_index(
        "ux_account_sessions_account_id",
        table_name="account_sessions",
    )
