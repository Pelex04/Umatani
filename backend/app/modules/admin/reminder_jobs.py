"""
Daily reminder cascade, auto-suspension, and admin digest — core logic.

Callable two ways:
  1. `python -m scripts.daily_digest_and_reminders` — direct CLI run,
     opens its own DB session. Useful for local testing.
  2. `POST /internal/cron/daily-digest-and-reminders` — the one actually
     used in production. Triggered by a GitHub Actions schedule, but
     runs inside this backend process so outbound Brevo calls come from
     Render's already-authorized IP instead of GitHub's constantly
     rotating runner IPs, which Brevo's IP-authorization security
     feature otherwise blocks.

Two independent tracks, each checked once per run:

  Track A — verified their email but never uploaded a student ID.
            Anchored on User.email_verified_at.
  Track B — ID was approved but never created a business.
            Anchored on User.id_verified_at.

For each track: every REMINDER_INTERVAL_DAYS (default 3) since the
anchor, send the next reminder and bump the counter, up to
REMINDER_MAX_COUNT (default 3). One more interval past the final
reminder with still no action -> suspend the account and notify them
why.

After processing both tracks, sends one digest email to
settings.ADMIN_DIGEST_EMAIL covering: new users in the last 24h, new
businesses in the last 24h, and businesses still PENDING after more
than 24h (the ones actually at risk of being forgotten).
"""
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.email import (
    send_account_suspended_email,
    send_admin_digest_email,
    send_business_creation_reminder_email,
    send_id_upload_reminder_email,
)
from app.modules.auth.models import User, UserStatus
from app.modules.businesses.models import Business, BusinessStatus
from app.shared.audit_service import record_audit_event

settings = get_settings()


def _due_for_next_step(anchor: datetime, count: int, interval_days: int) -> bool:
    """True once `count + 1` intervals have elapsed since anchor."""
    threshold = anchor + timedelta(days=interval_days * (count + 1))
    return datetime.now(UTC) >= threshold


async def _process_id_upload_track(db: AsyncSession) -> dict:
    reminded, suspended = 0, 0
    result = await db.execute(
        select(User).where(
            User.status == UserStatus.PENDING_ID_REVIEW,
            User.student_id_storage_key.is_(None),
            User.email_verified_at.is_not(None),
        )
    )
    for user in result.scalars().all():
        if not _due_for_next_step(user.email_verified_at, user.id_reminder_count, settings.REMINDER_INTERVAL_DAYS):
            continue

        if user.id_reminder_count >= settings.REMINDER_MAX_COUNT:
            user.status = UserStatus.SUSPENDED
            await record_audit_event(
                db, action="user.auto_suspended", resource_type="user",
                resource_id=str(user.id), actor_id=None, actor_role="system",
            )
            await send_account_suspended_email(
                to=user.email, full_name=user.full_name,
                reason="student ID was not uploaded after 3 reminders",
            )
            suspended += 1
        else:
            user.id_reminder_count += 1
            await send_id_upload_reminder_email(
                to=user.email, full_name=user.full_name, reminder_number=user.id_reminder_count,
            )
            reminded += 1
    return {"id_reminders_sent": reminded, "id_suspensions": suspended}


async def _process_business_creation_track(db: AsyncSession) -> dict:
    reminded, suspended = 0, 0
    result = await db.execute(
        select(User).where(
            User.status == UserStatus.VERIFIED,
            User.id_verified_at.is_not(None),
        )
    )
    for user in result.scalars().all():
        existing = await db.execute(select(Business.id).where(Business.owner_id == user.id))
        if existing.scalar_one_or_none() is not None:
            continue  # already created one — nothing to remind about

        if not _due_for_next_step(user.id_verified_at, user.business_reminder_count, settings.REMINDER_INTERVAL_DAYS):
            continue

        if user.business_reminder_count >= settings.REMINDER_MAX_COUNT:
            user.status = UserStatus.SUSPENDED
            await record_audit_event(
                db, action="user.auto_suspended", resource_type="user",
                resource_id=str(user.id), actor_id=None, actor_role="system",
            )
            await send_account_suspended_email(
                to=user.email, full_name=user.full_name,
                reason="no business profile was created after 3 reminders",
            )
            suspended += 1
        else:
            user.business_reminder_count += 1
            await send_business_creation_reminder_email(
                to=user.email, full_name=user.full_name, reminder_number=user.business_reminder_count,
            )
            reminded += 1
    return {"business_reminders_sent": reminded, "business_suspensions": suspended}


async def _send_admin_digest(db: AsyncSession) -> dict:
    since = datetime.now(UTC) - timedelta(hours=24)

    new_users_result = await db.execute(select(User).where(User.created_at >= since))
    new_users = [
        {"full_name": u.full_name, "email": u.email} for u in new_users_result.scalars().all()
    ]

    new_biz_result = await db.execute(select(Business).where(Business.created_at >= since))
    new_businesses = []
    for b in new_biz_result.scalars().all():
        owner = await db.get(User, b.owner_id)
        new_businesses.append({"name": b.name, "owner_email": owner.email if owner else "?"})

    stale_result = await db.execute(
        select(Business).where(
            Business.status == BusinessStatus.PENDING,
            Business.created_at < since,
        )
    )
    stale_pending = []
    for b in stale_result.scalars().all():
        owner = await db.get(User, b.owner_id)
        hours = int((datetime.now(UTC) - b.created_at).total_seconds() // 3600)
        stale_pending.append(
            {"name": b.name, "owner_email": owner.email if owner else "?", "hours_pending": hours}
        )

    await send_admin_digest_email(
        to=settings.ADMIN_DIGEST_EMAIL,
        new_users=new_users,
        new_businesses=new_businesses,
        stale_pending_businesses=stale_pending,
    )
    return {
        "new_users": len(new_users),
        "new_businesses": len(new_businesses),
        "stale_pending_businesses": len(stale_pending),
    }


async def run_daily_digest_and_reminders(db: AsyncSession | None = None) -> dict:
    """Runs the full job. Pass an existing session (e.g. from a FastAPI
    request) to reuse it, or omit to open a standalone one — used by the
    CLI script."""
    owns_session = db is None
    session = db or AsyncSessionLocal()
    try:
        id_summary = await _process_id_upload_track(session)
        biz_summary = await _process_business_creation_track(session)
        await session.commit()

        digest_summary = await _send_admin_digest(session)

        return {**id_summary, **biz_summary, **digest_summary}
    finally:
        if owns_session:
            await session.close()
