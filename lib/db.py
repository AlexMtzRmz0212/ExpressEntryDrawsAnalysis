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
