"""
CLI entrypoint for the daily reminder cascade + admin digest.

Production runs this via HTTP instead — see
app/modules/internal/routes.py — so that outbound Brevo calls come from
Render's already-authorized IP rather than a GitHub Actions runner's
constantly rotating one. This script is kept for local testing against
a dev DB.

Usage:
    python -m scripts.daily_digest_and_reminders
"""
import asyncio

# Every mapped model must be imported before SQLAlchemy configures its
# mappers, same reasoning as scripts/create_admin.py.
from app.modules.auth.models import (  # noqa: F401
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    User,
    UserRole,
    UserStatus,
)
from app.modules.admin.reminder_jobs import run_daily_digest_and_reminders
from app.modules.businesses.models import Business, BusinessStatus, PortfolioItem, Service  # noqa: F401
from app.modules.categories.models import Category  # noqa: F401
from app.modules.reviews.models import Review, ReviewPhoto, ReviewReply  # noqa: F401
from app.modules.schools.models import School  # noqa: F401
from app.modules.support.models import Report, SupportTicket  # noqa: F401
from app.shared.audit import AuditLog  # noqa: F401

if __name__ == "__main__":
    summary = asyncio.run(run_daily_digest_and_reminders())
    print(summary)
