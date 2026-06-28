"""
Change detection for IRCC Express Entry draws.

Fetches the IRCC JSON, compares the total draw count against what is already
in Supabase, and only triggers an upsert when new draws are found.
This keeps cron runs cheap — most of the time they do nothing.

Count-based detection is used instead of max(draw_number) because draw numbers
can contain letter suffixes (e.g. "91a", "91b") that cannot be compared as integers.
"""

import logging

from lib import db, ircc

logger = logging.getLogger(__name__)


def get_db_draw_count() -> int:
    """Return the number of draws currently in Supabase, or 0 if empty."""
    client = db.get_client()
    response = (
        client.table("draws")
        .select("draw_number", count="exact")
        .execute()
    )
    return response.count or 0


async def check_and_refresh() -> dict:
    """
    Core change-detection logic.

    1. Count draws in the DB (one query — fast).
    2. Fetch all draws from IRCC (one HTTP request — ~100 KB JSON).
    3. If IRCC has more draws than DB → upsert all (on_conflict is idempotent).
    4. Otherwise return immediately — nothing to do.

    Returns a status dict that the /api/cron endpoint passes back as JSON.
    """
    # Step 1 — how many draws do we already have?
    try:
        db_count = get_db_draw_count()
    except Exception as exc:
        logger.error("DB read failed: %s", exc)
        return {"status": "db_error", "error": str(exc)}

    logger.info("DB draw count: %d", db_count)

    # Step 2 — fetch IRCC
    try:
        all_draws = await ircc.fetch_draws()
    except Exception as exc:
        logger.error("IRCC fetch failed: %s", exc)
        return {"status": "ircc_error", "error": str(exc), "db_count": db_count}

    if not all_draws:
        logger.warning("IRCC returned zero draws")
        return {"status": "ircc_empty", "db_count": db_count}

    ircc_count = len(all_draws)
    logger.info("IRCC draw count: %d", ircc_count)

    # Step 3 — compare counts
    if ircc_count <= db_count:
        logger.info(
            "No new draws (IRCC=%d, DB=%d) — nothing to do.", ircc_count, db_count
        )
        return {
            "status": "no_change",
            "db_count": db_count,
            "ircc_count": ircc_count,
        }

    # Step 4 — upsert all draws; on_conflict handles existing rows idempotently
    logger.info("New draws detected (IRCC=%d > DB=%d) — upserting.", ircc_count, db_count)

    try:
        inserted, already_present = db.upsert_draws(all_draws)
    except Exception as exc:
        logger.error("Upsert failed: %s", exc)
        return {
            "status": "db_error",
            "error": str(exc),
            "db_count": db_count,
            "ircc_count": ircc_count,
        }

    return {
        "status": "updated",
        "db_count_before": db_count,
        "ircc_count": ircc_count,
        "inserted": inserted,
    }
