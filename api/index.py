"""
Express Entry Draws Intelligence — API

Routes:
  GET  /api/draws    — return all draws from the database (newest first)
  GET  /api/status   — most recent sync run + public-button cooldown state
  POST /api/refresh  — fetch live IRCC data and upsert into the database (secret)
  POST /api/check    — public "Check now" trigger; change-detection, rate-limited
  GET  /api/cron     — change-detection check; upserts only when IRCC has new draws

The `handler` name is required by Vercel's Python runtime (Mangum adapter).
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from lib import checker, db, ircc

# Public "Check now" cooldown: after a check that finds NO new draw, the button
# is locked for this long (anti-spam). After a check that DOES find a draw, it is
# locked until the next UTC day instead. Both are tunable one-liners.
MISS_COOLDOWN = timedelta(hours=1)

load_dotenv()  # picks up .env in local dev; Vercel injects env vars directly

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="EE Draws API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to EE.bittobyte.qzz.io in a later module
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
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

    return await checker.check_and_refresh()


# Vercel Python runtime entry point
handler = Mangum(app, lifespan="off")
