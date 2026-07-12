"""
Change detection for IRCC Express Entry draws.

Fetches the IRCC JSON and compares the set of draw_numbers against what is
already in Supabase, upserting only the draws that are missing. Most runs find
nothing new and return immediately, keeping cron runs cheap.

Set-difference detection (rather than comparing counts or max(draw_number)) is
used because:
  * draw numbers can carry letter suffixes (e.g. "91a", "91b") that are not
    integer-comparable, and
  * a count comparison silently stops detecting new draws forever if the DB ever
    gets ahead of the feed's valid count (IRCC occasionally revises/removes rounds).
"""

import logging

from lib import db, ircc

logger = logging.getLogger(__name__)


async def check_and_refresh() -> dict:
    """
    Core change-detection logic.

    1. Read the set of draw_numbers already in the DB (one query).
    2. Fetch all draws from IRCC (one HTTP request — ~100 KB JSON).
    3. Upsert only the draws whose draw_number is not already stored.
    4. Record a heartbeat row and return a status dict for /api/cron.
    """
    # Step 1 — which draws do we already have?
    try:
        existing = db.get_existing_draw_numbers()
    except Exception as exc:
        logger.error("DB read failed: %s", exc)
        db.record_sync_run("db_error", error=str(exc))
        return {"status": "db_error", "error": str(exc)}

    db_count = len(existing)
    logger.info("DB draw count: %d", db_count)

    # Step 2 — fetch IRCC
    try:
        all_draws = await ircc.fetch_draws()
    except Exception as exc:
        logger.error("IRCC fetch failed: %s", exc)
        db.record_sync_run("ircc_error", db_count=db_count, error=str(exc))
        return {"status": "ircc_error", "error": str(exc), "db_count": db_count}

    if not all_draws:
        logger.warning("IRCC returned zero draws")
        db.record_sync_run("ircc_empty", db_count=db_count)
        return {"status": "ircc_empty", "db_count": db_count}

    ircc_count = len(all_draws)
    logger.info("IRCC draw count: %d", ircc_count)

    # Step 3 — which draws are new?
    missing = [d for d in all_draws if d["draw_number"] not in existing]

    if not missing:
        logger.info(
            "No new draws (IRCC=%d, DB=%d) — nothing to do.", ircc_count, db_count
        )
        db.record_sync_run(
            "no_change", ircc_count=ircc_count, db_count=db_count, inserted=0
        )
        return {
            "status": "no_change",
            "db_count": db_count,
            "ircc_count": ircc_count,
        }

    # Step 4 — upsert only the missing draws; on_conflict keeps this idempotent.
    new_numbers = [d["draw_number"] for d in missing]
    logger.info("New draws detected: %s — upserting.", new_numbers)

    try:
        inserted, _already_present = db.upsert_draws(missing)
    except Exception as exc:
        logger.error("Upsert failed: %s", exc)
        db.record_sync_run(
            "db_error", ircc_count=ircc_count, db_count=db_count, error=str(exc)
        )
        return {
            "status": "db_error",
            "error": str(exc),
            "db_count": db_count,
            "ircc_count": ircc_count,
        }

    db.record_sync_run(
        "updated", ircc_count=ircc_count, db_count=db_count, inserted=inserted
    )
    return {
        "status": "updated",
        "db_count_before": db_count,
        "ircc_count": ircc_count,
        "inserted": inserted,
        "new_draws": new_numbers,
    }
