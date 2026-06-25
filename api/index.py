"""
Express Entry Draws Intelligence — API

Routes:
  GET  /api/draws    — return all draws from the database (newest first)
  POST /api/refresh  — fetch live IRCC data and upsert into the database

The `handler` name is required by Vercel's Python runtime (Mangum adapter).
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from lib import db, ircc

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

    return {
        "inserted": inserted,
        "already_present": already_present,
        "total_in_db": total,
    }


# Vercel Python runtime entry point
handler = Mangum(app, lifespan="off")
