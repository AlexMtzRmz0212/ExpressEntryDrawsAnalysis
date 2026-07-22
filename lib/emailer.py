"""
Email delivery via Resend.

All outbound mail goes through this module so the rest of the app never talks to
a mail provider directly (same containment rule as lib/db.py and Supabase).

Uses plain httpx against the Resend REST API rather than the `resend` SDK: httpx
is already a dependency for the IRCC fetch, and the API surface we need is two
endpoints.

Nothing here raises on a send failure. A mail problem must never turn a
successful draw refresh into a 500, so failures are logged and reported as
counts, mirroring how db.record_sync_run() swallows heartbeat errors.
"""

import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.resend.com"

# Resend accepts at most 100 messages per call to /emails/batch.
BATCH_SIZE = 100

# Resend's free tier rate-limits at roughly 2 requests/second. Pause between
# batch calls so a large list does not start collecting 429s.
BATCH_PAUSE_SECONDS = 0.6

TIMEOUT = httpx.Timeout(20.0)


def _api_key() -> str:
    key = os.environ.get("RESEND_API_KEY", "")
    if not key:
        raise EnvironmentError("RESEND_API_KEY must be set to send email.")
    return key


def mail_from() -> str:
    """The From header, e.g. 'Express Entry Draws <notifications@ee.bittobyte.qzz.io>'."""
    value = os.environ.get("MAIL_FROM", "")
    if not value:
        raise EnvironmentError("MAIL_FROM must be set to send email.")
    return value


def admin_email() -> str:
    """Where owner alerts go. Empty string disables them rather than erroring."""
    return os.environ.get("ADMIN_EMAIL", "").strip()


def site_url() -> str:
    """Public base URL, used to build confirm and unsubscribe links."""
    return os.environ.get("SITE_URL", "https://ee.bittobyte.qzz.io").rstrip("/")


def sender_address() -> str:
    """
    Postal address printed in the footer of every subscriber email.

    CASL requires a physical or postal mailing address in commercial email, so
    this is intentionally required config rather than an optional nicety.
    """
    return os.environ.get("MAIL_SENDER_ADDRESS", "").strip()


def is_configured() -> bool:
    """True when enough env is present to send. Lets callers degrade quietly."""
    return bool(os.environ.get("RESEND_API_KEY") and os.environ.get("MAIL_FROM"))


def from_domain() -> str:
    """
    The domain part of MAIL_FROM, e.g. 'updates.bittobyte.qzz.io'.

    Handles both bare addresses and the 'Name <addr@domain>' form. Returns an
    empty string when MAIL_FROM is unset or unparseable, so callers can report
    the problem rather than crash on it.
    """
    raw = os.environ.get("MAIL_FROM", "").strip()
    if not raw:
        return ""
    # 'Display Name <a@b.com>' → 'a@b.com'; a bare address is left as-is.
    if "<" in raw and ">" in raw:
        raw = raw[raw.rfind("<") + 1 : raw.rfind(">")]
    _, _, domain = raw.strip().partition("@")
    return domain.strip().lower()


def check_config() -> list[str]:
    """
    Report everything wrong with the mail configuration, worst first.

    Deliberately does not call Resend: the API keys this app uses are restricted
    to sending, so /domains answers 401 and cannot confirm verification. What is
    checkable locally is checked here; the rest is caught at send time by
    _log_send_failure(), which knows how to read Resend's rejection.
    """
    problems = []

    if not os.environ.get("RESEND_API_KEY"):
        problems.append("RESEND_API_KEY is not set - no mail can be sent.")

    if not os.environ.get("MAIL_FROM"):
        problems.append("MAIL_FROM is not set - no mail can be sent.")
    elif not from_domain():
        problems.append(
            f"MAIL_FROM is not a usable address: {os.environ.get('MAIL_FROM')!r}. "
            "Expected 'Name <user@domain>' or 'user@domain'."
        )

    if not sender_address():
        problems.append(
            "MAIL_SENDER_ADDRESS is not set - CASL requires a postal address in "
            "the footer of commercial email."
        )

    site = site_url()
    if "localhost" in site or "127.0.0.1" in site:
        problems.append(
            f"SITE_URL is {site!r} - confirm and unsubscribe links in real email "
            "will point at a machine the recipient does not have."
        )

    return problems


def log_config_status() -> None:
    """Log the mail configuration once at startup. Never raises."""
    try:
        problems = check_config()
    except Exception as exc:  # noqa: BLE001 - a diagnostic must never break boot
        logger.warning("Could not check the mail configuration: %s", exc)
        return

    if problems:
        for problem in problems:
            logger.error("MAIL CONFIG: %s", problem)
    else:
        logger.info("Mail configured - sending as %s", os.environ.get("MAIL_FROM"))


def _log_send_failure(context: str, exc: Exception) -> None:
    """
    Log a send failure with the provider's own explanation attached.

    httpx raises HTTPStatusError with a message like "Client error '403
    Forbidden'" and drops the response body, which is exactly where Resend puts
    the reason. Without this the most common misconfiguration — a From domain
    that is not verified — is invisible in the logs.
    """
    detail = ""
    response = getattr(exc, "response", None)
    if response is not None:
        detail = (response.text or "").strip()[:500]

    logger.error("%s: %s%s", context, exc, f" | {detail}" if detail else "")

    # The one failure worth spelling out, because the fix is not obvious from the
    # raw message: Resend verifies domains, and MAIL_FROM must sit on one.
    if "not verified" in detail:
        logger.error(
            "MAIL CONFIG: the %r domain in MAIL_FROM is not verified in Resend. "
            "Verify that exact domain at https://resend.com/domains, or change "
            "MAIL_FROM to an address on a domain that already is.",
            from_domain(),
        )


def send_one(
    to: str,
    subject: str,
    html: str,
    *,
    text: str | None = None,
    headers: dict | None = None,
    reply_to: str | None = None,
) -> bool:
    """Send a single email. Returns True on success, False on any failure."""
    payload = {
        "from": mail_from(),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    if headers:
        payload["headers"] = headers
    if reply_to:
        payload["reply_to"] = reply_to

    try:
        response = httpx.post(
            f"{API_BASE}/emails",
            json=payload,
            headers={"Authorization": f"Bearer {_api_key()}"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001 - mail failure must not break the caller
        _log_send_failure(f"Failed to send email to {_redact(to)}", exc)
        return False


def send_batch(messages: list[dict]) -> int:
    """
    Send many emails, chunked to Resend's per-call limit.

    `messages` are payload dicts without the `from` field, which is filled in
    here. Returns the number of messages successfully handed to Resend; a failed
    chunk contributes zero rather than aborting the remaining chunks.
    """
    if not messages:
        return 0

    try:
        key = _api_key()
        sender = mail_from()
    except EnvironmentError as exc:
        logger.error("Cannot send batch: %s", exc)
        return 0

    sent = 0
    chunks = [messages[i : i + BATCH_SIZE] for i in range(0, len(messages), BATCH_SIZE)]

    for index, chunk in enumerate(chunks):
        payload = [{"from": sender, **message} for message in chunk]
        try:
            response = httpx.post(
                f"{API_BASE}/emails/batch",
                json=payload,
                headers={"Authorization": f"Bearer {key}"},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            sent += len(chunk)
        except Exception as exc:  # noqa: BLE001 - keep going with the next chunk
            _log_send_failure(
                f"Batch {index + 1}/{len(chunks)} failed ({len(chunk)} recipients)",
                exc,
            )

        if index < len(chunks) - 1:
            time.sleep(BATCH_PAUSE_SECONDS)

    logger.info("Batch send complete: %d/%d messages accepted", sent, len(messages))
    return sent


def notify_admin(subject: str, html: str, *, text: str | None = None) -> bool:
    """Send an owner alert. No-ops when ADMIN_EMAIL is unset."""
    to = admin_email()
    if not to:
        logger.info("ADMIN_EMAIL not set, skipping admin alert: %s", subject)
        return False
    return send_one(to, subject, html, text=text)


def _redact(email: str) -> str:
    """Log-safe address: 'al***@gmail.com'. Keeps logs useful without leaking."""
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    return f"{local[:2]}***@{domain}"
