"""
Express Entry Draws Intelligence — API

Routes:
  GET  /api/draws    — return all draws from the database (newest first)
  GET  /api/status   — return the most recent sync run (heartbeat / last update)
  POST /api/refresh  — fetch live IRCC data and upsert into the database
  GET  /api/cron     — change-detection check; upserts only when IRCC has new draws

The `handler` name is required by Vercel's Python runtime (Mangum adapter).
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from lib import checker, db, ircc

load_dotenv()  # picks up .env in local dev; Vercel injects env vars directly

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="EE Draws API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to EE.bittobyte.qzz.io in a later module
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
)


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
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"last_sync": last}


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
