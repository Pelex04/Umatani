"""Add reviews, review_photos, review_replies, reports, support_tickets

Revision ID: 20260701_000004
Revises: 20260630_000003
Create Date: 2026-07-01
"""
from collections.abc import Sequence
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "20260701_000004"
down_revision: str | None = "20260630_000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("business_id", sa.Uuid(as_uuid=True),
                  sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("service_received", sa.String(255), nullable=True),
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("business_id", "reviewer_id", name="uq_review_business_reviewer"),
    )
    op.create_index("ix_reviews_business_id", "reviews", ["business_id"])
    op.create_index("ix_reviews_reviewer_id", "reviews", ["reviewer_id"])
    op.create_index("ix_reviews_created_at", "reviews", ["created_at"])

    op.create_table(
        "review_photos",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("review_id", sa.Uuid(as_uuid=True),
                  sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False),
    )
    op.create_index("ix_review_photos_review_id", "review_photos", ["review_id"])

    op.create_table(
        "review_replies",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("review_id", sa.Uuid(as_uuid=True),
                  sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_review_replies_review_id", "review_replies", ["review_id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.String(100), nullable=False),
        sa.Column("reporter_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_report_type", "reports", ["report_type"])
    op.create_index("ix_reports_created_at", "reports", ["created_at"])

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("ticket_type", sa.String(20), nullable=False),
        sa.Column("submitter_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("admin_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"])
    op.create_index("ix_support_tickets_created_at", "support_tickets", ["created_at"])


def downgrade() -> None:
    op.drop_table("support_tickets")
    op.drop_table("reports")
    op.drop_table("review_replies")
    op.drop_table("review_photos")
    op.drop_table("reviews")
