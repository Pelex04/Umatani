"""Add categories, businesses, services, and portfolio_items tables

Revision ID: 20260630_000003
Revises: 20260630_000002
Create Date: 2026-06-30
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260630_000003"
down_revision: str | None = "20260630_000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon_url", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)
    op.create_index("ix_categories_is_active", "categories", ["is_active"])

    op.create_table(
        "businesses",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False, unique=True,
        ),
        sa.Column(
            "school_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("schools.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "category_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(280), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("logo_storage_key", sa.String(512), nullable=True),
        sa.Column("cover_storage_key", sa.String(512), nullable=True),
        sa.Column("whatsapp", sa.String(30), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("instagram", sa.String(255), nullable=True),
        sa.Column("twitter", sa.String(255), nullable=True),
        sa.Column("facebook", sa.String(255), nullable=True),
        sa.Column("tiktok", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("average_rating", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_businesses_owner_id", "businesses", ["owner_id"], unique=True)
    op.create_index("ix_businesses_slug", "businesses", ["slug"], unique=True)
    op.create_index("ix_businesses_school_id", "businesses", ["school_id"])
    op.create_index("ix_businesses_category_id", "businesses", ["category_id"])
    op.create_index("ix_businesses_status", "businesses", ["status"])
    op.create_index("ix_businesses_created_at", "businesses", ["created_at"])

    op.create_table(
        "services",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_range", sa.String(100), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_services_business_id", "services", ["business_id"])

    op.create_table(
        "portfolio_items",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id", sa.Uuid(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("storage_key_or_url", sa.String(512), nullable=False),
        sa.Column("caption", sa.String(500), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_portfolio_items_business_id", "portfolio_items", ["business_id"])


def downgrade() -> None:
    op.drop_table("portfolio_items")
    op.drop_table("services")
    op.drop_table("businesses")
    op.drop_table("categories")
