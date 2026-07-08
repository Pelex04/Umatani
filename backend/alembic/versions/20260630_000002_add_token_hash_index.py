"""Add index on email_verification_tokens.token_hash for O(log n) lookups

Revision ID: 20260630_000002
Revises: 20260630_000001
Create Date: 2026-06-30

The email verification token lookup in AuthService.verify_email queries
by token_hash. Without an index this is a full table scan; with even
modest user volume the index pays for itself immediately.
"""
from collections.abc import Sequence

from alembic import op

revision: str = "20260630_000002"
down_revision: str | None = "20260630_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_email_verification_tokens_token_hash",
        "email_verification_tokens",
        ["token_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_email_verification_tokens_token_hash",
        table_name="email_verification_tokens",
    )
