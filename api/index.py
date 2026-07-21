"""
Express Entry Draws Intelligence — API

Routes:
  GET  /api/draws       — return all draws from the database (newest first)
  GET  /api/status      — most recent sync run + public-button cooldown state
  POST /api/refresh     — fetch live IRCC data and upsert into the database (secret)
  POST /api/check       — public "Check now" trigger; change-detection, rate-limited
  GET  /api/cron        — change-detection check; upserts only when IRCC has new draws
  POST /api/subscribe   — public double opt-in signup for new-draw email alerts
  GET  /api/confirm     — confirmation landing page for the opt-in link
  GET  /api/unsubscribe — one-click unsubscribe landing page
  POST /api/unsubscribe — RFC 8058 one-click unsubscribe target for mail clients
  POST /api/notify      — drain the notification outbox and send draw emails (secret)

The `handler` name is required by Vercel's Python runtime (Mangum adapter).
"""

import logging
import os
import re
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from mangum import Mangum
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

from lib import checker, db, emailer, ircc, notifier, templates

# Public "Check now" cooldown: after a check that finds NO new draw, the button
# is locked for this long (anti-spam). After a check that DOES find a draw, it is
# locked until the next UTC day instead. Both are tunable one-liners.
MISS_COOLDOWN = timedelta(hours=1)

# Signup abuse limits. The honeypot field catches most bots; this bounds the rest
# without a CAPTCHA. Double opt-in means a flood of signups still sends at most
# one confirmation email per address.
SIGNUP_WINDOW = timedelta(hours=1)
SIGNUP_LIMIT_PER_IP = 3

# Deliberately permissive: real address validity is proven by the confirmation
# click, so a strict pattern here only rejects legitimate unusual addresses.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]+$")
MAX_EMAIL_LENGTH = 254  # RFC 5321

load_dotenv()  # picks up .env in local dev; Vercel injects env vars directly

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="EE Draws API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to EE.bittobyte.qzz.io in a later module
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


def _parse_ts(value: str | None) -> datetime | None:
    """Parse a Supabase timestamptz string to an aware UTC datetime, or None."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _manual_check_state() -> dict:
    """
    Decide whether the public "Check now" button may trigger a live IRCC fetch.

    Enforced server-side (not just hidden in the UI) so it can't be bypassed by a
    reload, a fresh browser, or a direct API call. Derived entirely from the
    existing sync_runs heartbeat — no extra table.

    Returns {allowed, reason, unlock_at}:
      * updated_today    — a new draw was already found today (UTC); locked until
                           the next UTC midnight. The scheduled cron keeps running.
      * recently_checked — some sync ran within MISS_COOLDOWN; locked until then.
      * None reason      — allowed.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Rule 1 — has any run already found a new draw today?
    updated = db.get_last_updated_sync_since(today_start.isoformat())
    if updated is not None:
        return {
            "allowed": False,
            "reason": "updated_today",
            "unlock_at": (today_start + timedelta(days=1)).isoformat(),
        }

    # Rule 2 — did any run happen within the miss-cooldown window?
    last = db.get_last_sync()
    ran_at = _parse_ts(last.get("ran_at")) if last else None
    if ran_at is not None and now - ran_at < MISS_COOLDOWN:
        return {
            "allowed": False,
            "reason": "recently_checked",
            "unlock_at": (ran_at + MISS_COOLDOWN).isoformat(),
        }

    return {"allowed": True, "reason": None, "unlock_at": None}


async def _notify_quietly() -> None:
    """
    Drain the notification outbox without letting mail problems surface.

    Run in a worker thread because the notifier and the Resend client are
    synchronous, and blocking the event loop inside an async route would stall
    anything else the same function instance is serving.
    """
    try:
        await run_in_threadpool(notifier.notify_new_draws)
    except Exception as exc:  # noqa: BLE001 - refresh success must not depend on mail
        logging.getLogger(__name__).error("Notification run failed: %s", exc)


def _client_ip(request: Request) -> str:
    """
    Caller's IP, preferring the proxy header Vercel sets.

    Stored only as CASL proof of consent, as disclosed in the privacy policy,
    and used for the signup rate limit.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def _normalise_email(value: str) -> str | None:
    """Trim and lowercase an address, or return None if it is not usable."""
    email = (value or "").strip().lower()
    if not email or len(email) > MAX_EMAIL_LENGTH or not EMAIL_RE.match(email):
        return None
    return email


@app.get("/api/draws")
def get_draws() -> list[dict]:
    """Return all Express Entry draws, newest first."""
    try:
        return db.get_all_draws()
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/status")
def get_status() -> dict:
    """
    Return the most recent sync run so silent update failures are visible.

    Useful to answer "when did the data last update, and did the last run
    succeed?" without opening the database.
    """
    try:
        last = db.get_last_sync()
        manual_check = _manual_check_state()
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"last_sync": last, "manual_check": manual_check}


@app.post("/api/refresh")
async def refresh_draws(authorization: str = Header(default="")) -> dict:
    """
    Fetch the latest draw data from IRCC and upsert into Supabase.

    Requires:  Authorization: Bearer <REFRESH_SECRET>
    """
    secret = os.environ.get("REFRESH_SECRET", "")
    expected = f"Bearer {secret}"
    if not secret or authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing refresh secret.")

    try:
        draws = await ircc.fetch_draws()
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch IRCC data: {exc}"
        ) from exc

    if not draws:
        raise HTTPException(status_code=502, detail="IRCC returned no draws.")

    try:
        inserted, already_present = db.upsert_draws(draws)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    total = db.get_client().table("draws").select("draw_number", count="exact").execute().count or 0

    # Heartbeat so /api/status reflects refreshes too (e.g. the GitHub Actions
    # backup scheduler), not just /api/cron runs.
    db.record_sync_run(
        "updated" if inserted else "no_change",
        ircc_count=len(draws),
        db_count=total - inserted,
        inserted=inserted,
    )

    # The GitHub Actions backup scheduler reaches draws through this route rather
    # than through checker, so mail has to be triggered here too. The outbox makes
    # this safe to call unconditionally: it no-ops when there is nothing new.
    if inserted:
        await _notify_quietly()

    return {
        "inserted": inserted,
        "already_present": already_present,
        "total_in_db": total,
    }


@app.post("/api/check")
async def manual_check() -> dict:
    """
    Public, unauthenticated "Check now" trigger for the frontend button.

    Lets a visitor who believes a new draw just dropped force a live IRCC check,
    without exposing REFRESH_SECRET. Abuse is bounded server-side by a two-tier
    cooldown (see `_manual_check_state`): at most one IRCC fetch per hour, and
    none for the rest of the UTC day once a new draw has been found.

    Response:
      { allowed: false, reason, unlock_at }            — locked; no IRCC call made
      { allowed: true, result: {...}, manual_check }   — ran; result is the
                                                          check_and_refresh() dict,
                                                          manual_check is the new lock
    """
    try:
        state = _manual_check_state()
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not state["allowed"]:
        return state

    # Allowed — run change detection (fetches IRCC, writes only if new + records
    # a heartbeat). check_and_refresh handles its own errors and never raises.
    result = await checker.check_and_refresh()

    if result.get("status") == "updated":
        await _notify_quietly()

    # Recompute so the client immediately gets the fresh lock: "updated" → locked
    # until tomorrow, "no_change" → locked for MISS_COOLDOWN.
    return {"allowed": True, "result": result, "manual_check": _manual_check_state()}


@app.get("/api/cron")
async def cron_detect(authorization: str = Header(default="")) -> dict:
    """
    Change-detection cron endpoint — called by Vercel's scheduler every day.

    Checks if the IRCC feed has a draw_number higher than what is in the DB.
    Only performs a DB write when new draws are actually found; most calls do
    nothing and return immediately.

    Vercel automatically includes  Authorization: Bearer <CRON_SECRET>  in
    cron requests when the CRON_SECRET environment variable is set.
    """
    secret = os.environ.get("CRON_SECRET", "")
    if not secret or authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await checker.check_and_refresh()

    if result.get("status") == "updated":
        await _notify_quietly()

    # Housekeeping on the same daily tick: delete unconfirmed signups and old
    # unsubscribed rows, which is what the privacy policy promises.
    await run_in_threadpool(db.purge_stale_records)

    return result


# ---------------------------------------------------------------------------
# Email subscriptions
# ---------------------------------------------------------------------------


class SubscribeRequest(BaseModel):
    email: str = ""
    website: str = ""  # honeypot: real people never see or fill this field


# One response for every outcome. Returning "already subscribed" for a known
# address would turn this endpoint into a way to test whether someone is on the
# list, so success, duplicate, and rate-limited all look identical from outside.
SUBSCRIBE_OK = {
    "ok": True,
    "message": "Check your inbox and click the confirmation link to finish subscribing.",
}


@app.post("/api/subscribe")
async def subscribe(payload: SubscribeRequest, request: Request) -> dict:
    """
    Public double opt-in signup for new-draw email alerts.

    Nothing is added to the mailing list here. A pending row is created and a
    confirmation email is sent; only clicking that link makes the address active.
    That is what CASL means by express consent, and it also means the endpoint
    cannot be used to sign somebody else up.
    """
    email = _normalise_email(payload.email)
    if email is None:
        raise HTTPException(status_code=400, detail="Enter a valid email address.")

    # Honeypot tripped: behave exactly like success, but write nothing. A bot that
    # gets an error learns to avoid the field next time.
    if payload.website.strip():
        logging.getLogger(__name__).info("Honeypot tripped on a signup, ignoring.")
        return SUBSCRIBE_OK

    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent", "")[:500]

    def _work() -> None:
        if db.count_recent_signups_from_ip(ip, SIGNUP_WINDOW) >= SIGNUP_LIMIT_PER_IP:
            logging.getLogger(__name__).warning("Signup rate limit hit for an IP.")
            return

        subscriber = db.create_or_refresh_subscriber(email, ip, user_agent)
        if subscriber is None:
            return  # already confirmed; re-sending would just be noise

        subject, html, text = templates.confirm_email(subscriber["token"])
        emailer.send_one(email, subject, html, text=text)

    try:
        await run_in_threadpool(_work)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SUBSCRIBE_OK


@app.get("/api/confirm", response_class=HTMLResponse)
async def confirm(token: str = "") -> HTMLResponse:
    """
    Landing page for the confirmation link in the opt-in email.

    Returns a real HTML page rather than redirecting: the dashboard is a
    single-page app with no router, so there is nothing on the client side to
    handle this URL.
    """
    subscriber = await run_in_threadpool(db.get_subscriber_by_token, token)

    if subscriber is None:
        return HTMLResponse(
            templates.landing_page(
                "That link is not valid",
                "It may have already been used, or it may have expired. Unconfirmed "
                "signups are deleted after 7 days. Subscribe again from the dashboard "
                "and a fresh link will be on its way.",
                tone="bad",
            ),
            status_code=404,
        )

    was_confirmed = subscriber.get("status") == "confirmed"
    updated = await run_in_threadpool(db.confirm_subscriber, token)

    if not was_confirmed and updated is not None:
        await run_in_threadpool(notifier.alert_owner, "subscribed", updated["email"])
        return HTMLResponse(
            templates.landing_page(
                "You are subscribed",
                "You will get an email each time IRCC publishes a new Express Entry "
                "round, with the CRS cutoff, the invitation count, and how it compares "
                "to recent rounds. Every message has a one-click unsubscribe link.",
            )
        )

    return HTMLResponse(
        templates.landing_page(
            "Already subscribed",
            "This address is confirmed, so there is nothing more to do. The next "
            "draw notification will arrive automatically.",
            tone="neutral",
        )
    )


def _unsubscribe_page(token: str) -> HTMLResponse:
    """Shared body for both unsubscribe methods."""
    subscriber = db.get_subscriber_by_token(token)
    if subscriber is None:
        return HTMLResponse(
            templates.landing_page(
                "That link is not valid",
                "This address may already have been removed. If you keep getting "
                "emails, reply to one of them and it will be sorted out by hand.",
                tone="bad",
            ),
            status_code=404,
        )

    already_gone = subscriber.get("status") == "unsubscribed"
    updated = db.unsubscribe_by_token(token)

    if not already_gone and updated is not None:
        notifier.alert_owner("unsubscribed", updated["email"])

    return HTMLResponse(
        templates.landing_page(
            "You are unsubscribed",
            "No more draw notifications will be sent to this address. Your record "
            "is deleted within 30 days. The dashboard is still free to use without "
            "an account.",
            tone="neutral",
        )
    )


@app.get("/api/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(token: str = "") -> HTMLResponse:
    """
    One-click unsubscribe. No login, no confirmation step, no survey.

    CASL requires the mechanism to work in a single step and to be honoured
    promptly, so this takes effect on the spot.
    """
    return await run_in_threadpool(_unsubscribe_page, token)


@app.post("/api/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_post(token: str = "") -> HTMLResponse:
    """
    RFC 8058 one-click target, used by Gmail's and Apple Mail's own unsubscribe
    button. Same effect as the GET, so a mail client that POSTs works too.
    """
    return await run_in_threadpool(_unsubscribe_page, token)


@app.post("/api/notify")
async def notify(authorization: str = Header(default="")) -> dict:
    """
    Drain the notification outbox: email subscribers about any unsent draw.

    Protected by the same REFRESH_SECRET as /api/refresh. Safe to call at any
    time and as often as you like; with an empty queue it is a single query.
    """
    secret = os.environ.get("REFRESH_SECRET", "")
    if not secret or authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Invalid or missing refresh secret.")

    await run_in_threadpool(notifier.retry_failed)
    return await run_in_threadpool(notifier.notify_new_draws)


# Vercel Python runtime entry point
handler = Mangum(app, lifespan="off")
