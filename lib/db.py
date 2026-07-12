"""
Supabase database layer.

All database access goes through this module so the rest of the app
never imports supabase directly.
"""

import logging
import os

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
