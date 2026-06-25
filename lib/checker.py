"""
Change detection for IRCC Express Entry draws.

Fetches the IRCC JSON, compares the latest draw_number against what is
already in Supabase, and only triggers an upsert when new draws are found.
This keeps cron runs cheap — most of the time they do nothing.
"""

import logging

from lib import db, ircc

logger = logging.getLogger(__name__)


def get_latest_db_draw_number() -> int:
    """Return the highest draw_number currently in Supabase, or 0 if empty."""
    client = db.get_client()
    response = (
        client.table("draws")
        .select("draw_number")
        .order("draw_number", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]["draw_number"]
    return 0


async def check_and_refresh() -> dict:
    """
    Core change-detection logic.

    1. Read the highest draw_number from the DB (one row query — fast).
    2. Fetch all draws from IRCC (one HTTP request — ~100 KB JSON).
    3. If IRCC has draws with a higher number → upsert only the new ones.
    4. Otherwise return immediately — nothing to do.

    Returns a status dict that the /api/cron endpoint passes back as JSON.
    """
    # Step 1 — what is the latest draw we already have?
    try:
        db_latest = get_latest_db_draw_number()
    except Exception as exc:
        logger.error("DB read failed: %s", exc)
        return {"status": "db_error", "error": str(exc)}

    logger.info("DB latest draw_number: %d", db_latest)

    # Step 2 — fetch IRCC
    try:
        all_draws = await ircc.fetch_draws()
    except Exception as exc:
        logger.error("IRCC fetch failed: %s", exc)
        return {"status": "ircc_error", "error": str(exc), "db_latest": db_latest}

    if not all_draws:
        logger.warning("IRCC returned zero draws")
        return {"status": "ircc_empty", "db_latest": db_latest}

    # Step 3 — compare
    ircc_latest = max(d["draw_number"] for d in all_draws)
    logger.info("IRCC latest draw_number: %d", ircc_latest)

    if ircc_latest <= db_latest:
        logger.info(
            "No new draws (IRCC latest=%d, DB latest=%d) — nothing to do.",
            ircc_latest,
            db_latest,
        )
        return {
            "status": "no_change",
            "db_latest": db_latest,
            "ircc_latest": ircc_latest,
        }

    # Step 4 — upsert only draws we don't already have
    new_draws = [d for d in all_draws if d["draw_number"] > db_latest]
    new_numbers = [d["draw_number"] for d in new_draws]
    logger.info("New draw(s) detected: %s — upserting.", new_numbers)

    try:
        inserted, already_present = db.upsert_draws(new_draws)
    except Exception as exc:
        logger.error("Upsert failed: %s", exc)
        return {
            "status": "db_error",
            "error": str(exc),
            "db_latest": db_latest,
            "ircc_latest": ircc_latest,
            "new_draw_numbers": new_numbers,
        }

    return {
        "status": "updated",
        "db_latest_before": db_latest,
        "ircc_latest": ircc_latest,
        "new_draw_numbers": new_numbers,
        "inserted": inserted,
    }
