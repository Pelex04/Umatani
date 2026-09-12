"""
Internal endpoints — for infrastructure to call, not the frontend.

Not nested under /admin because that router requires an admin user's
JWT (Depends(require_role(UserRole.ADMIN))), which a GitHub Actions
runner doesn't have. Secured instead by a shared secret header, checked
with a constant-time comparison to avoid timing attacks.
"""
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.modules.admin.reminder_jobs import run_daily_digest_and_reminders

router = APIRouter(prefix="/internal", tags=["internal"])
settings = get_settings()


def _check_cron_secret(x_cron_secret: str | None) -> None:
    expected = settings.CRON_SECRET
    if not expected:
        # Not configured — refuse rather than silently accepting an
        # unauthenticated call, in case someone forgets to set it.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cron endpoint not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing cron secret")


@router.post("/cron/daily-digest-and-reminders")
async def trigger_daily_digest_and_reminders(
    x_cron_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _check_cron_secret(x_cron_secret)
    summary = await run_daily_digest_and_reminders(db)
    return {"status": "completed", **summary}
