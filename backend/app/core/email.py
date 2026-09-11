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
    subject = "Verify your Umata? email address"
    plain = (
        f"Hi {full_name},\n\n"
        f"Welcome to Umata?! Please verify your school email by visiting:\n\n"
        f"{verify_url}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours.\n\n"
        f"If you did not sign up for Umata?, you can safely ignore this email.\n\n"
        f"The Umata? Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>Welcome to Umata? 👋</h2>
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


async def send_password_reset_email(*, to: str, full_name: str, token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"
    subject = "Reset your Umata? password"
    plain = (
        f"Hi {full_name},\n\n"
        f"We received a request to reset your Umata? password. Visit this link to choose a new one:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s).\n\n"
        f"If you didn't request this, you can safely ignore this email — your password won't be changed.\n\n"
        f"The Umata? Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>Reset your password</h2>
      <p>Hi {full_name},</p>
      <p>We received a request to reset your Umata? password. Click below to choose a new one.</p>
      <p style="margin:32px 0;">
        <a href="{reset_url}"
           style="background:#2563eb;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:600;">
          Reset Password
        </a>
      </p>
      <p style="color:#6b7280;font-size:14px;">
        This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour(s).
        If you didn't request this, you can safely ignore this email — your password won't be changed.
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)


async def send_approval_email(*, to: str, full_name: str) -> None:
    subject = "Your Umata? account has been verified!"
    plain = (
        f"Hi {full_name},\n\n"
        f"Great news: your student ID has been verified and your Umata? account "
        f"is now fully active. You can now create your business profile.\n\n"
        f"Visit {settings.FRONTEND_URL} to get started.\n\n"
        f"The Umata? Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>You're verified! 🎉</h2>
      <p>Hi {full_name},</p>
      <p>Your student ID has been reviewed and your account is now fully active.
         You can now create your business profile on Umata?.</p>
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


async def send_business_approval_email(*, to: str, full_name: str, business_name: str) -> None:
    subject = f'"{business_name}" is now live on Umata?'
    profile_url = f"{settings.FRONTEND_URL}/dashboard"
    plain = (
        f"Hi {full_name},\n\n"
        f'Good news: "{business_name}" has been approved and is now live and '
        f"visible to everyone browsing Umata?.\n\n"
        f"View your listing: {profile_url}\n\n"
        f"The Umata? Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>Your business is live! 🎉</h2>
      <p>Hi {full_name},</p>
      <p>"{business_name}" has been approved and is now visible to everyone browsing Umata?.</p>
      <p style="margin:32px 0;">
        <a href="{profile_url}"
           style="background:#16a34a;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:600;">
          View Your Listing
        </a>
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)


async def send_id_upload_reminder_email(*, to: str, full_name: str, reminder_number: int) -> None:
    upload_url = f"{settings.FRONTEND_URL}/dashboard"
    subject = "Reminder: upload your student ID to finish setting up Umata?"
    plain = (
        f"Hi {full_name},\n\n"
        f"You verified your school email but haven't uploaded your student ID yet "
        f"(reminder {reminder_number} of 3). Until it's reviewed, you can't create a "
        f"business profile.\n\n"
        f"Upload it here: {upload_url}\n\n"
        f"If you don't complete this after {3} reminders, your account will be suspended.\n\n"
        f"The Umata? Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>Finish setting up your account</h2>
      <p>Hi {full_name},</p>
      <p>You verified your school email but haven't uploaded your student ID yet
         (reminder {reminder_number} of 3). Until it's reviewed, you can't create a business profile.</p>
      <p style="margin:32px 0;">
        <a href="{upload_url}"
           style="background:#2563eb;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:600;">
          Upload Student ID
        </a>
      </p>
      <p style="color:#6b7280;font-size:14px;">
        If this isn't completed after 3 reminders, your account will be suspended.
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)


async def send_business_creation_reminder_email(*, to: str, full_name: str, reminder_number: int) -> None:
    create_url = f"{settings.FRONTEND_URL}/dashboard"
    subject = "Reminder: create your business profile on Umata?"
    plain = (
        f"Hi {full_name},\n\n"
        f"Your student ID was verified a while ago but you haven't created a "
        f"business profile yet (reminder {reminder_number} of 3).\n\n"
        f"Create one here: {create_url}\n\n"
        f"If you don't complete this after 3 reminders, your account will be suspended.\n\n"
        f"The Umata? Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>Ready to list your business?</h2>
      <p>Hi {full_name},</p>
      <p>Your student ID was verified a while ago but you haven't created a business
         profile yet (reminder {reminder_number} of 3).</p>
      <p style="margin:32px 0;">
        <a href="{create_url}"
           style="background:#2563eb;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:600;">
          Create Your Business
        </a>
      </p>
      <p style="color:#6b7280;font-size:14px;">
        If this isn't completed after 3 reminders, your account will be suspended.
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)


async def send_account_suspended_email(*, to: str, full_name: str, reason: str) -> None:
    subject = "Your Umata? account has been suspended"
    plain = (
        f"Hi {full_name},\n\n"
        f"Your Umata? account has been suspended: {reason}\n\n"
        f"If you'd like to reactivate it, please contact support.\n\n"
        f"The Umata? Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>Account suspended</h2>
      <p>Hi {full_name},</p>
      <p>Your Umata? account has been suspended: {reason}</p>
      <p style="color:#6b7280;font-size:14px;">
        If you'd like to reactivate it, please contact support.
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)


async def send_admin_digest_email(
    *,
    to: str,
    new_users: list[dict],
    new_businesses: list[dict],
    stale_pending_businesses: list[dict],
) -> None:
    subject = (
        f"Umata? daily digest — {len(new_users)} new users, "
        f"{len(new_businesses)} new businesses, "
        f"{len(stale_pending_businesses)} pending >24h"
    )

    def _rows_plain(items: list[dict], fields: list[str]) -> str:
        if not items:
            return "  (none)\n"
        return "".join(f"  - {' | '.join(str(i.get(f, '')) for f in fields)}\n" for i in items)

    def _rows_html(items: list[dict], fields: list[str]) -> str:
        if not items:
            return "<li style='color:#6b7280;'>None</li>"
        return "".join(
            f"<li>{' &middot; '.join(str(i.get(f, '')) for f in fields)}</li>" for i in items
        )

    plain = (
        f"Umata? daily digest\n\n"
        f"New users (last 24h):\n{_rows_plain(new_users, ['full_name', 'email'])}\n"
        f"New businesses (last 24h):\n{_rows_plain(new_businesses, ['name', 'owner_email'])}\n"
        f"Pending businesses waiting >24h for approval:\n"
        f"{_rows_plain(stale_pending_businesses, ['name', 'owner_email', 'hours_pending'])}\n"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
      <h2>Umata? daily digest</h2>
      <h3>New users (last 24h)</h3>
      <ul>{_rows_html(new_users, ['full_name', 'email'])}</ul>
      <h3>New businesses (last 24h)</h3>
      <ul>{_rows_html(new_businesses, ['name', 'owner_email'])}</ul>
      <h3 style="color:#b91c1c;">Pending businesses waiting &gt;24h for approval</h3>
      <ul>{_rows_html(stale_pending_businesses, ['name', 'owner_email', 'hours_pending'])}</ul>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)


async def send_business_suspended_email(*, to: str, full_name: str, business_name: str) -> None:
    subject = f'"{business_name}" has been suspended'
    plain = (
        f"Hi {full_name},\n\n"
        f'Your business "{business_name}" has been suspended by an admin and is '
        f"no longer visible on Umata?.\n\n"
        f"If you think this is a mistake, please contact support.\n\n"
        f"The Umata? Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>Listing suspended</h2>
      <p>Hi {full_name},</p>
      <p>Your business "{business_name}" has been suspended by an admin and is
         no longer visible on Umata?.</p>
      <p style="color:#6b7280;font-size:14px;">
        If you think this is a mistake, please contact support.
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)


async def send_broadcast_email(*, to: str, subject: str, message: str) -> None:
    """Admin-authored broadcast. `message` is plain text supplied by an
    admin, not a template — line breaks are preserved but no other
    formatting is assumed."""
    html_message = message.replace("\n", "<br>")
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <p>{html_message}</p>
      <p style="color:#9ca3af;font-size:12px;margin-top:32px;">
        Sent by the Umata? team.
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=message)
