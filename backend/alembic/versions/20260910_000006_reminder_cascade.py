"""Add reminder cascade columns to users

Supports the 3-day reminder cascade for (a) users who verified their
email but haven't uploaded a student ID, and (b) users whose ID was
approved but haven't created a business yet. email_verified_at and
id_verified_at are the anchors the reminder job measures elapsed time
from — deliberately separate from updated_at, which changes on
unrelated updates. The *_reminder_count columns track how many
reminders have gone out so the job can suspend after 3 without
resending indefinitely.

Revision ID: 20260910_000006
Revises: 20260801_000005
Create Date: 2026-09-10
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260910_000006"
down_revision: str | None = "20260801_000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("id_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column("id_reminder_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("business_reminder_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "business_reminder_count")
    op.drop_column("users", "id_reminder_count")
    op.drop_column("users", "id_verified_at")
    op.drop_column("users", "email_verified_at")
