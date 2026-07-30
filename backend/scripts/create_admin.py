"""
Bootstrap the first admin account.

Admin accounts are deliberately NOT creatable via the public API (no
"become admin" endpoint exists) — that would be a privilege-escalation
vulnerability. This script is the sanctioned way to create the first
admin, intended to be run once against the production database by
someone with direct database/deploy access, not exposed as a service.

Usage:
    python -m scripts.create_admin --email admin@umatani.app --name "Platform Admin"

Prompts for a password interactively (never accepted as a CLI arg, to
avoid it ending up in shell history).
"""
import argparse
import asyncio
import getpass
import sys

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password

# All mapped models must be imported before SQLAlchemy configures its
# mappers, or foreign keys pointing at tables whose model was never
# imported (e.g. users.school_id -> schools.id) fail to resolve at
# flush time. Kept in sync with alembic/env.py's import list.
from app.modules.auth.models import (  # noqa: F401
    EmailVerificationToken,
    RefreshToken,
    User,
    UserRole,
    UserStatus,
)
from app.modules.auth.repository import UserRepository
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


async def create_admin(email: str, full_name: str, password: str) -> None:
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        existing = await repo.get_by_email(email)
        if existing is not None:
            print(f"Error: a user with email '{email}' already exists.", file=sys.stderr)
            sys.exit(1)

        await repo.create(
            email=email.lower().strip(),
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            status=UserStatus.VERIFIED,
            school_id=None,
        )
        await session.commit()
        print(f"Admin account created: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the first Umata? admin account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, dest="full_name")
    args = parser.parse_args()

    password = getpass.getpass("Set admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Error: passwords do not match.", file=sys.stderr)
        sys.exit(1)

    try:
        _validate_password(password)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(create_admin(args.email, args.full_name, password))


if __name__ == "__main__":
    main()
