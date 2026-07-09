"""
Email service.

Uses Python's built-in smtplib with async execution in a thread pool so
SMTP I/O doesn't block the event loop. No external email SDK dependency.

In development (ENVIRONMENT != production and SMTP_HOST is unset), emails
are printed to stdout so the verification flow is testable without a real
mail server — the token appears in the console.

In production, configure SMTP_HOST/SMTP_USER/SMTP_PASSWORD via environment
variables (e.g. Brevo, Mailgun, or a self-hosted SMTP relay).
"""
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _send_smtp(*, to: str, subject: str, html: str, plain: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.SMTP_FROM_EMAIL, to, msg.as_string())


async def send_email(*, to: str, subject: str, html: str, plain: str) -> None:
    if not settings.SMTP_HOST:
        # Development fallback — print to stdout so the flow is testable.
        logger.info("=" * 60)
        logger.info(f"[DEV EMAIL] To: {to}")
        logger.info(f"[DEV EMAIL] Subject: {subject}")
        logger.info(f"[DEV EMAIL] Body:\n{plain}")
        logger.info("=" * 60)
        return

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None,
            partial(_send_smtp, to=to, subject=subject, html=html, plain=plain),
        )
    except Exception:
        # Email delivery is best-effort and must never take down the
        # request that triggered it (e.g. registration already committed
        # the account to the database by this point — losing the email
        # shouldn't lose the account too). Many hosts, including Render's
        # free/starter tiers, block outbound raw SMTP entirely, which
        # surfaces as "Network is unreachable" rather than an auth or
        # timeout error — that's an infrastructure/transport problem, not
        # a per-request one, so retrying here won't help; it needs a
        # different transport (see module docstring).
        logger.exception(f"Failed to send email to {to} (subject: {subject!r})")


async def send_verification_email(*, to: str, full_name: str, token: str) -> None:
    verify_url = f"https://umatani.app/verify-email?token={token}"
    subject = "Verify your UMATANI email address"
    plain = (
        f"Hi {full_name},\n\n"
        f"Welcome to UMATANI! Please verify your school email by visiting:\n\n"
        f"{verify_url}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours.\n\n"
        f"If you did not sign up for UMATANI, you can safely ignore this email.\n\n"
        f"— The UMATANI Team"
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
        f"Great news — your student ID has been verified and your UMATANI account "
        f"is now fully active. You can now create your business profile.\n\n"
        f"Visit https://umatani.app to get started.\n\n"
        f"— The UMATANI Team"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2>You're verified! 🎉</h2>
      <p>Hi {full_name},</p>
      <p>Your student ID has been reviewed and your account is now fully active.
         You can now create your business profile on UMATANI.</p>
      <p style="margin:32px 0;">
        <a href="https://umatani.app/dashboard"
           style="background:#16a34a;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:600;">
          Create Your Profile
        </a>
      </p>
    </div>
    """
    await send_email(to=to, subject=subject, html=html, plain=plain)
