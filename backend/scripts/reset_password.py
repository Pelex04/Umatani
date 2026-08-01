"""
Reset an existing account's password.

create_admin.py deliberately refuses to touch an account that already
exists (to avoid accidentally overwriting someone's password from a typo
in an --email argument). This is the separate, explicit tool for the
case where you actually do want to reset one — same security posture as
create_admin.py: run once, directly against the database, by someone
with deploy access. Not exposed as an API endpoint.

Usage:
    python -m scripts.reset_password --email admin@umatani.app

Prompts for the new password interactively (never accepted as a CLI
arg, so it doesn't end up in shell history).
"""
import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password

# All mapped models must be imported before SQLAlchemy configures its
# mappers, or foreign keys pointing at tables whose model was never
# imported (e.g. users.school_id -> schools.id) fail to resolve at
# flush time. Kept in sync with alembic/env.py's import list.
from app.modules.auth.models import EmailVerificationToken, PasswordResetToken, RefreshToken, User  # noqa: F401
from app.modules.businesses.models import Business, PortfolioItem, Service  # noqa: F401
from app.modules.categories.models import Category  # noqa: F401
from app.modules.reviews.models import Review, ReviewPhoto, ReviewReply  # noqa: F401
from app.modules.schools.models import School  # noqa: F401
from app.modules.support.models import Report, SupportTicket  # noqa: F401
from app.shared.audit import AuditLog  # noqa: F401


def _validate_password(password: str) -> None:
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one digit")


async def reset_password(email: str, password: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        user = result.scalar_one_or_none()
        if user is None:
            print(f"Error: no user found with email '{email}'.", file=sys.stderr)
            sys.exit(1)

        user.hashed_password = hash_password(password)
        # A stuck lockout would otherwise still block login even with the
        # correct new password.
        user.failed_login_attempts = 0
        user.locked_until = None
        await session.commit()
        print(f"Password reset for: {email} (role: {user.role}, status: {user.status})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset an existing Umata? account's password")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Set new password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Error: passwords do not match.", file=sys.stderr)
        sys.exit(1)

    try:
        _validate_password(password)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(reset_password(args.email, password))


if __name__ == "__main__":
    main()
