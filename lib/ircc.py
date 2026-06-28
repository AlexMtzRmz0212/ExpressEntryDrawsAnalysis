"""
Fetches and parses the IRCC Express Entry rounds JSON.

IRCC endpoint returns a top-level object with a "rounds" array.
Each round looks like:
  {
    "drawNumber":    "308",
    "drawDate":      "August 19, 2024",   # human-readable, English
    "drawName":      "Provincial Nominee Program",
    "drawSize":      "600",               # may be null; use drawSizeStr fallback
    "drawSizeStr":   "600",
    "drawCRS":       "690",               # may be null; use drawCRSStr fallback
    "drawCRSStr":    "690",
    "drawNumberURL": "https://..."
  }
"""

import logging
from datetime import date, datetime

import httpx

IRCC_URL = (
    "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
)

# IRCC sometimes blocks default user-agents; mimic a browser.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, */*",
}

logger = logging.getLogger(__name__)


def _parse_int(value: object) -> int | None:
    """Convert string/int/None to int, stripping commas."""
    if value is None:
        return None
    try:
        return int(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _parse_date(value: str) -> date | None:
    """Parse IRCC date strings such as 'August 19, 2024'."""
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    logger.warning("Could not parse date: %r", value)
    return None


def _coerce_round(raw: dict) -> dict | None:
    """
    Normalise a single IRCC round dict into our schema shape.
    Returns None if mandatory fields are missing.
    """
    draw_number = str(raw.get("drawNumber") or "").strip()
    if not draw_number:
        logger.warning("Skipping round with missing drawNumber: %s", raw)
        return None

    raw_date = raw.get("drawDate") or raw.get("drawDateFull", "")
    draw_date = _parse_date(raw_date)
    if draw_date is None:
        logger.warning("Skipping draw #%s — unparseable date: %r", draw_number, raw_date)
        return None

    # invitations — prefer numeric field, fall back to the formatted string
    invitations = _parse_int(raw.get("drawSize")) or _parse_int(raw.get("drawSizeStr"))
    if invitations is None:
        logger.warning("Draw #%s has no invitation count", draw_number)
        invitations = 0

    # CRS cutoff
    crs_cutoff = _parse_int(raw.get("drawCRS")) or _parse_int(raw.get("drawCRSStr"))
    if crs_cutoff is None:
        logger.warning("Draw #%s has no CRS cutoff", draw_number)
        return None

    draw_name = (raw.get("drawName") or "").strip()

    return {
        "draw_number": draw_number,
        "draw_date": draw_date.isoformat(),
        "draw_name": draw_name,
        "crs_cutoff": crs_cutoff,
        "invitations": invitations,
        "draw_url": (raw.get("drawNumberURL") or "").strip() or None,
        "raw_data": raw,  # full original IRCC record stored as JSONB
    }


async def fetch_draws() -> list[dict]:
    """
    Fetch all rounds from IRCC and return a list of normalised draw dicts.
    Raises httpx.HTTPError on network/HTTP failure.
    """
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(IRCC_URL, headers=_HEADERS)
        response.raise_for_status()

    data = response.json()

    # Log top-level keys on first run so field names can be verified.
    logger.debug("IRCC JSON top-level keys: %s", list(data.keys()))

    # The array may live under "rounds" or directly at the root as a list.
    if isinstance(data, list):
        rounds = data
    else:
        rounds = data.get("rounds") or data.get("drawList") or []
        if not rounds:
            # Dump the first key's value if it's a list
            for v in data.values():
                if isinstance(v, list):
                    rounds = v
                    break

    if not rounds:
        logger.error("No rounds found in IRCC response. Keys: %s", list(data.keys()))
        return []

    logger.info("Fetched %d raw rounds from IRCC", len(rounds))

    draws = [_coerce_round(r) for r in rounds]
    draws = [d for d in draws if d is not None]
    logger.info("Parsed %d valid draws", len(draws))
    return draws
