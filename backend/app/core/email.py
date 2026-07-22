"""
Email service.

Sends via Brevo's transactional HTTP API (https://api.brevo.com/v3/smtp/email)
using httpx, not raw SMTP. Many hosts — including Render's free/starter
tiers — block outbound SMTP sockets entirely to prevent spam abuse, which
previously surfaced as "OSError: Network is unreachable" and, worse, took
the whole request down with it. HTTPS is never blocked the same way, and
httpx is natively async, so this also drops the old thread-pool-executor
indirection smtplib needed.

In development (BREVO_API_KEY unset), emails are printed to stdout so the
verification flow is testable without hitting a real provider — the token
appears in the console.

In production, set BREVO_API_KEY (from https://app.brevo.com/settings/keys/api),
plus optionally EMAIL_FROM_ADDRESS / EMAIL_FROM_NAME.
"""
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def send_email(*, to: str, subject: str, html: str, plain: str) -> None:
    if not settings.BREVO_API_KEY:
        # Development fallback — print to stdout so the flow is testable.
        logger.info("=" * 60)
        logger.info(f"[DEV EMAIL] To: {to}")
        logger.info(f"[DEV EMAIL] Subject: {subject}")
        logger.info(f"[DEV EMAIL] Body:\n{plain}")
        logger.info("=" * 60)
        return

    payload = {
        "sender": {"name": settings.EMAIL_FROM_NAME, "email": settings.EMAIL_FROM_ADDRESS},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html,
        "textContent": plain,
    }
    headers = {
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
        "accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(BREVO_API_URL, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Brevo's error responses include a JSON body explaining exactly
        # why (bad key, wrong key type, unrecognised sender, etc.) — log it
        # directly instead of just the status code, or every failure looks
        # identical and has to be guessed at from Render's dashboard blind.
        logger.error(
            f"Failed to send email to {to} (subject: {subject!r}): "
            f"{exc.response.status_code} — {exc.response.text}"
        )
    except Exception:
        # Email delivery is best-effort and must never take down the
        # request that triggered it (e.g. registration already committed
        # the account to the database by this point — losing the email
        # shouldn't lose the account too). Callers should not assume
        # delivery succeeded just because this didn't raise.
        logger.exception(f"Failed to send email to {to} (subject: {subject!r})")


async def send_verification_email(*, to: str, full_name: str, token: str) -> None:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Verify your UMATANI email address"
    plain = (
        f"Hi {full_name},\n\n"
        f"Welcome to UMATANI! Please verify your school email by visiting:\n\n"
        f"{verify_url}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours.\n\n"
        f"If you did not sign up for UMATANI, you can safely ignore this email.\n\n"
        f"The UMATANI Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>Welcome to UMATANI 👋</h2>
      <p>Hi {full_name},</p>
      <p>Please verify your school email address to continue setting up your account.</p>
      <p style="margin:32px 0;">
        <a href="{verify_url}"
           style="background:#2563eb;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:600;">
          Verify Email Address
        </a>
      </p>
      <p style="color:#6b7280;font-size:14px;">
        This link expires in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours.
        If you didn't create an account, you can ignore this email.
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)


async def send_approval_email(*, to: str, full_name: str) -> None:
    subject = "Your UMATANI account has been verified!"
    plain = (
        f"Hi {full_name},\n\n"
        f"Great news: your student ID has been verified and your UMATANI account "
        f"is now fully active. You can now create your business profile.\n\n"
        f"Visit {settings.FRONTEND_URL} to get started.\n\n"
        f"The UMATANI Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>You're verified! 🎉</h2>
      <p>Hi {full_name},</p>
      <p>Your student ID has been reviewed and your account is now fully active.
         You can now create your business profile on UMATANI.</p>
      <p style="margin:32px 0;">
        <a href="{settings.FRONTEND_URL}/dashboard"
           style="background:#16a34a;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:600;">
          Create Your Profile
        </a>
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)
