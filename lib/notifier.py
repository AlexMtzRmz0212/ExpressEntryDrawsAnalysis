"""
Draw notification outbox.

Three separate code paths insert draws (/api/cron and /api/check via
lib/checker.py, plus /api/refresh called by the GitHub Actions scheduler), and
any of them can run concurrently. Sending mail inline from one of them would
miss the others and risk sending the same draw twice.

So sending is driven by a queue instead: draw_notifications holds one row per
draw that has been handled, and this module asks "which draws are missing a
row?". Claiming a row is an INSERT against a primary key, so the database picks
a single winner even if two functions wake up at the same moment.

Nothing here raises. A mail failure must leave the draw data correct and the
API responses successful.
"""

import logging
from datetime import date, datetime, timedelta, timezone

from lib import db, drawstats, emailer, templates

logger = logging.getLogger(__name__)

# Never email about a draw older than this. The schema seeds draw_notifications
# from the existing draws table, but if that table is ever wiped and rebuilt,
# this is what stops the whole historical archive going out as mail.
MAX_NOTIFY_AGE = timedelta(days=10)


def _unsubscribe_url(token: str) -> str:
    return f"{emailer.site_url()}/api/unsubscribe?token={token}"


def _draw_date(draw: dict) -> date | None:
    try:
        return datetime.strptime(str(draw.get("draw_date"))[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def notify_new_draws() -> dict:
    """
    Send notifications for any draw that has not been handled yet.

    Returns a summary dict. The common case is an empty queue, which costs one
    small query and returns immediately, matching how checker.check_and_refresh()
    stays cheap on the many days nothing happens.
    """
    if not emailer.is_configured():
        logger.info("Email is not configured, skipping notifications.")
        return {"status": "not_configured", "sent": 0}

    try:
        pending = db.get_unnotified_draws()
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not read the notification queue: %s", exc)
        return {"status": "db_error", "error": str(exc), "sent": 0}

    if not pending:
        return {"status": "nothing_to_send", "sent": 0}

    logger.info("Notification queue: %d draw(s)", len(pending))

    try:
        all_draws = db.get_all_draws()
        subscribers = db.get_confirmed_subscribers()
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not load draws or subscribers: %s", exc)
        return {"status": "db_error", "error": str(exc), "sent": 0}

    today = datetime.now(timezone.utc).date()
    results = []

    # Oldest first, so a burst of draws arrives in the order they happened.
    for draw in sorted(pending, key=lambda d: str(d.get("draw_date", ""))):
        number = str(draw["draw_number"])

        drawn_on = _draw_date(draw)
        if drawn_on is None or (today - drawn_on) > MAX_NOTIFY_AGE:
            if db.claim_draw_notification(number):
                db.finish_draw_notification(number, "skipped_backfill")
            logger.info("Draw %s is too old to notify about, skipping.", number)
            results.append({"draw_number": number, "status": "skipped_backfill"})
            continue

        if not db.claim_draw_notification(number):
            results.append({"draw_number": number, "status": "already_claimed"})
            continue

        results.append(_send_for_draw(draw, all_draws, subscribers))

    sent = sum(r.get("recipients", 0) for r in results)
    db.record_sync_run(
        "notified" if sent else "notify_noop",
        inserted=sent,
        error=None,
    )
    return {"status": "done", "sent": sent, "draws": results}


def _send_for_draw(draw: dict, all_draws: list[dict], subscribers: list[dict]) -> dict:
    """Render and send one draw to every confirmed subscriber. Never raises."""
    number = str(draw["draw_number"])

    if not subscribers:
        db.finish_draw_notification(number, "sent", recipients=0)
        logger.info("Draw %s: no confirmed subscribers, nothing to send.", number)
        return {"draw_number": number, "status": "sent", "recipients": 0}

    try:
        context = drawstats.build_context(draw, all_draws)
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not build stats for draw %s: %s", number, exc)
        db.finish_draw_notification(number, "failed", error=str(exc))
        return {"draw_number": number, "status": "failed", "error": str(exc)}

    messages = []
    for subscriber in subscribers:
        unsubscribe = _unsubscribe_url(subscriber["token"])
        subject, html, text = templates.draw_email(context, unsubscribe)
        messages.append(
            {
                "to": [subscriber["email"]],
                "subject": subject,
                "html": html,
                "text": text,
                # RFC 8058: lets Gmail and Apple Mail show their own unsubscribe
                # button, which is both a CASL nicety and a deliverability signal.
                "headers": {
                    "List-Unsubscribe": f"<{unsubscribe}>",
                    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                },
            }
        )

    recipients = emailer.send_batch(messages)

    if recipients == 0:
        # Leave the row marked failed so a later /api/notify retries this draw.
        db.finish_draw_notification(number, "failed", error="all sends failed")
        logger.error("Draw %s: every send failed.", number)
        return {"draw_number": number, "status": "failed", "recipients": 0}

    if recipients < len(messages):
        logger.warning(
            "Draw %s: only %d of %d messages were accepted. Check the provider's "
            "daily cap or rate limit.",
            number,
            recipients,
            len(messages),
        )

    db.finish_draw_notification(number, "sent", recipients=recipients)
    db.touch_subscribers_sent([s["id"] for s in subscribers])
    logger.info("Draw %s: notified %d subscriber(s).", number, recipients)
    return {"draw_number": number, "status": "sent", "recipients": recipients}


def retry_failed() -> None:
    """
    Clear rows left in 'sending' or 'failed' so the next run picks them up again.

    'sending' rows are orphans from a function that was killed mid-send (a
    serverless timeout, for instance). Called at the start of /api/notify.
    """
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        client = db.get_client()
        stale = (
            client.table("draw_notifications")
            .select("draw_number")
            .in_("status", ["sending", "failed"])
            .lt("claimed_at", cutoff)
            .execute()
            .data
            or []
        )
        for row in stale:
            client.table("draw_notifications").delete().eq(
                "draw_number", row["draw_number"]
            ).execute()
            logger.info("Released stuck notification claim for draw %s", row["draw_number"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not release stuck notification claims: %s", exc)


# ---------------------------------------------------------------------------
# Owner alerts
# ---------------------------------------------------------------------------


def alert_owner(event: str, email: str) -> None:
    """
    Tell the site owner that someone subscribed or unsubscribed. Never raises.

    Called after the database write, so a mail provider outage cannot make a
    subscription or an unsubscribe appear to fail to the person who clicked.
    """
    try:
        when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        subject, html, text = templates.admin_alert(event, email, when, db.count_confirmed())
        emailer.notify_admin(subject, html, text=text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not send the owner alert for %s: %s", event, exc)
