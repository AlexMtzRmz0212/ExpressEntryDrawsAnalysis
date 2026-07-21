"""
Supabase database layer.

All database access goes through this module so the rest of the app
never imports supabase directly.
"""

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from supabase import Client, create_client

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    """Return a cached Supabase client. Raises on missing env vars."""
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        if not url or not key:
            raise EnvironmentError(
                "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set."
            )
        _client = create_client(url, key)
    return _client


def get_all_draws() -> list[dict]:
    """Return all draws ordered newest first."""
    client = get_client()
    response = (
        client.table("draws")
        .select("*")
        .order("draw_date", desc=True)
        .order("draw_number", desc=True)  # tiebreaker for same-date draws (e.g. 91a/91b)
        .execute()
    )
    return response.data or []


def get_existing_draw_numbers() -> set[str]:
    """
    Return the set of draw_numbers already stored, as strings.

    Used for change detection by set membership, which is robust to letter
    suffixes (e.g. "91a") and to the DB ever getting ahead of the feed — unlike
    a plain count comparison.
    """
    client = get_client()
    response = client.table("draws").select("draw_number").execute()
    return {str(row["draw_number"]) for row in (response.data or [])}


def upsert_draws(draws: list[dict]) -> tuple[int, int]:
    """
    Upsert a list of draw dicts into the draws table.

    Compares the row count before and after to approximate how many rows
    were inserted vs already existed. Returns (inserted, already_present).
    """
    if not draws:
        return 0, 0

    client = get_client()

    count_before = (
        client.table("draws").select("draw_number", count="exact").execute().count or 0
    )

    client.table("draws").upsert(
        draws,
        on_conflict="draw_number",
    ).execute()

    count_after = (
        client.table("draws").select("draw_number", count="exact").execute().count or 0
    )

    inserted = count_after - count_before
    already_present = len(draws) - inserted

    logger.info(
        "Upsert complete — inserted=%d, already_present=%d", inserted, already_present
    )
    return inserted, already_present


def record_sync_run(
    status: str,
    *,
    ircc_count: int | None = None,
    db_count: int | None = None,
    inserted: int | None = None,
    error: str | None = None,
) -> None:
    """
    Insert a heartbeat row into sync_runs. Best-effort: never raise.

    A failure to log a run (e.g. the sync_runs table does not exist yet) must not
    break the actual refresh, so all errors here are swallowed with a warning.
    """
    try:
        get_client().table("sync_runs").insert(
            {
                "status": status,
                "ircc_count": ircc_count,
                "db_count": db_count,
                "inserted": inserted,
                "error": error,
            }
        ).execute()
    except Exception as exc:  # noqa: BLE001 — heartbeat must never break the caller
        logger.warning("Could not record sync run: %s", exc)


def get_last_sync() -> dict | None:
    """Return the most recent sync_runs row, or None if there are none."""
    client = get_client()
    response = (
        client.table("sync_runs")
        .select("*")
        .order("ran_at", desc=True)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def get_last_updated_sync_since(since_iso: str) -> dict | None:
    """
    Return the most recent sync_runs row with status='updated' whose ran_at is
    at or after `since_iso` (an ISO-8601 timestamp), or None.

    Used by the public "Check now" cooldown to answer "has a new draw already
    been found today?" — checking *any* updated run in the window, not just the
    latest row, so a subsequent no_change cron run cannot erase the lock.
    """
    client = get_client()
    response = (
        client.table("sync_runs")
        .select("*")
        .eq("status", "updated")
        .gte("ran_at", since_iso)
        .order("ran_at", desc=True)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


# ---------------------------------------------------------------------------
# Subscribers (double opt-in mailing list)
# ---------------------------------------------------------------------------

# An unconfirmed signup is deleted after this long, as stated in the privacy policy.
PENDING_TTL = timedelta(days=7)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_token() -> str:
    """Opaque, unguessable token used for both confirm and unsubscribe links."""
    return secrets.token_urlsafe(32)


def get_subscriber_by_email(email: str) -> dict | None:
    """Look up a subscriber by their normalised address."""
    response = (
        get_client().table("subscribers").select("*").eq("email", email).limit(1).execute()
    )
    data = response.data or []
    return data[0] if data else None


def get_subscriber_by_token(token: str) -> dict | None:
    """Look up a subscriber by their confirm/unsubscribe token."""
    if not token:
        return None
    response = (
        get_client().table("subscribers").select("*").eq("token", token).limit(1).execute()
    )
    data = response.data or []
    return data[0] if data else None


def create_or_refresh_subscriber(email: str, ip: str | None, user_agent: str | None) -> dict | None:
    """
    Start (or restart) a subscription for `email` and return the row to confirm.

    Behaviour by existing status:
      * no row          — insert a pending row with a fresh token.
      * pending         — reissue a fresh token and resend, so a lost confirmation
                          email is recoverable without support.
      * unsubscribed    — treat as a brand new opt-in: back to pending with a new
                          token. Re-subscribing must require confirming again.
      * confirmed       — return None. Nothing to do, and re-sending a
                          confirmation to an active subscriber is just noise.

    The caller sends the confirmation mail; this function only touches the row.
    """
    client = get_client()
    existing = get_subscriber_by_email(email)

    if existing and existing.get("status") == "confirmed":
        return None

    token = new_token()

    if existing:
        response = (
            client.table("subscribers")
            .update(
                {
                    "status": "pending",
                    "token": token,
                    "created_at": _now_iso(),
                    "confirmed_at": None,
                    "unsubscribed_at": None,
                    "consent_ip": ip,
                    "consent_user_agent": user_agent,
                }
            )
            .eq("id", existing["id"])
            .execute()
        )
    else:
        response = (
            client.table("subscribers")
            .insert(
                {
                    "email": email,
                    "status": "pending",
                    "token": token,
                    "consent_ip": ip,
                    "consent_user_agent": user_agent,
                }
            )
            .execute()
        )

    data = response.data or []
    return data[0] if data else None


def confirm_subscriber(token: str) -> dict | None:
    """
    Flip a pending row to confirmed. Returns the updated row.

    An already-confirmed token returns the row unchanged so the landing page can
    say "you are already subscribed" instead of showing an error, which is what
    happens whenever someone clicks the link twice.
    """
    subscriber = get_subscriber_by_token(token)
    if subscriber is None:
        return None
    if subscriber.get("status") == "confirmed":
        return subscriber

    response = (
        get_client()
        .table("subscribers")
        .update({"status": "confirmed", "confirmed_at": _now_iso(), "unsubscribed_at": None})
        .eq("id", subscriber["id"])
        .execute()
    )
    data = response.data or []
    return data[0] if data else subscriber


def unsubscribe_by_token(token: str) -> dict | None:
    """
    Mark a subscriber as unsubscribed. Returns the row, or None for a bad token.

    The row is kept (not deleted) so a replayed one-click unsubscribe stays
    idempotent and so the address cannot be silently re-added. Actual deletion
    happens in purge_unsubscribed(), on the 30 day schedule the policy states.
    """
    subscriber = get_subscriber_by_token(token)
    if subscriber is None:
        return None
    if subscriber.get("status") == "unsubscribed":
        return subscriber

    response = (
        get_client()
        .table("subscribers")
        .update({"status": "unsubscribed", "unsubscribed_at": _now_iso()})
        .eq("id", subscriber["id"])
        .execute()
    )
    data = response.data or []
    return data[0] if data else subscriber


def get_confirmed_subscribers() -> list[dict]:
    """Every address that should receive draw notifications."""
    response = (
        get_client()
        .table("subscribers")
        .select("id,email,token")
        .eq("status", "confirmed")
        .execute()
    )
    return response.data or []


def count_confirmed() -> int:
    """Running total of confirmed subscribers, used in the owner alerts."""
    try:
        response = (
            get_client()
            .table("subscribers")
            .select("id", count="exact")
            .eq("status", "confirmed")
            .execute()
        )
        return response.count or 0
    except Exception as exc:  # noqa: BLE001 - a count must never break a signup
        logger.warning("Could not count subscribers: %s", exc)
        return 0


def count_recent_signups_from_ip(ip: str, window: timedelta) -> int:
    """
    How many signups this IP has made inside `window`. Drives the rate limit.

    Returns 0 when the IP is unknown or the query fails, so a database hiccup
    blocks nobody. The honeypot and the double opt-in are the real defences.
    """
    if not ip:
        return 0
    since = (datetime.now(timezone.utc) - window).isoformat()
    try:
        response = (
            get_client()
            .table("subscribers")
            .select("id", count="exact")
            .eq("consent_ip", ip)
            .gte("created_at", since)
            .execute()
        )
        return response.count or 0
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not check signup rate for an IP: %s", exc)
        return 0


def purge_stale_records() -> dict:
    """
    Delete data the privacy policy promises not to keep.

    Unconfirmed signups older than PENDING_TTL, and unsubscribed rows older than
    30 days. Best-effort: errors are logged, never raised.
    """
    client = get_client()
    result = {"pending_deleted": 0, "unsubscribed_deleted": 0}

    try:
        cutoff = (datetime.now(timezone.utc) - PENDING_TTL).isoformat()
        response = (
            client.table("subscribers")
            .delete()
            .eq("status", "pending")
            .lt("created_at", cutoff)
            .execute()
        )
        result["pending_deleted"] = len(response.data or [])

        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        response = (
            client.table("subscribers")
            .delete()
            .eq("status", "unsubscribed")
            .lt("unsubscribed_at", cutoff)
            .execute()
        )
        result["unsubscribed_deleted"] = len(response.data or [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Purge of stale subscriber records failed: %s", exc)

    return result


# ---------------------------------------------------------------------------
# Notification outbox
# ---------------------------------------------------------------------------


def get_unnotified_draws() -> list[dict]:
    """
    Draws that have no row in draw_notifications yet, newest first.

    Two queries rather than a join, because PostgREST cannot express an
    anti-join. Both tables are small (a few hundred rows), so this is cheap.
    """
    client = get_client()
    handled = {
        str(row["draw_number"])
        for row in (client.table("draw_notifications").select("draw_number").execute().data or [])
    }
    all_draws = client.table("draws").select("*").order("draw_date", desc=True).execute().data or []
    return [d for d in all_draws if str(d["draw_number"]) not in handled]


def claim_draw_notification(draw_number: str) -> bool:
    """
    Try to claim a draw for sending. Returns True only for the winning caller.

    The claim is an INSERT against a PRIMARY KEY, so the database decides the
    winner. This is what stops /api/cron, /api/check, and /api/refresh from
    double-sending when they overlap.
    """
    try:
        get_client().table("draw_notifications").insert(
            {"draw_number": str(draw_number), "status": "sending"}
        ).execute()
        return True
    except Exception as exc:  # noqa: BLE001 - a duplicate key here is the expected path
        logger.info("Draw %s already claimed by another run (%s)", draw_number, exc)
        return False


def finish_draw_notification(
    draw_number: str,
    status: str,
    *,
    recipients: int = 0,
    error: str | None = None,
) -> None:
    """Close out a claimed notification. Best-effort, never raises."""
    try:
        get_client().table("draw_notifications").update(
            {
                "status": status,
                "recipients": recipients,
                "error": error,
                "sent_at": _now_iso(),
            }
        ).eq("draw_number", str(draw_number)).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not finalise notification for %s: %s", draw_number, exc)


def touch_subscribers_sent(subscriber_ids: list[int]) -> None:
    """Record that these subscribers were just mailed. Best-effort."""
    if not subscriber_ids:
        return
    try:
        get_client().table("subscribers").update({"last_sent_at": _now_iso()}).in_(
            "id", subscriber_ids
        ).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not update last_sent_at: %s", exc)
