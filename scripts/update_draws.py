"""
Express Entry Draw ETL Script
==============================
Fetches the latest IRCC Express Entry draw data, detects new rounds by comparing
roundNumber to the existing dataset, and writes updated static JSON files that
the React dashboard consumes.

Output files (written only when new data is found):
  public/data/analyses/draw_summary.json   — flattened draw records
  public/data/analyses/module_manifest.json — label → data-path map for the UI

Audit file (always written):
  data/analysis_raw.json                   — full raw IRCC response
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import structlog

# ── Logging ────────────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.get_logger()

# ── Constants ──────────────────────────────────────────────────────────────────
IRCC_JSON_URL = (
    "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
)

REPO_ROOT       = Path(__file__).resolve().parent.parent
DATA_DIR        = REPO_ROOT / "data"
ANALYSES_DIR    = REPO_ROOT / "public" / "data" / "analyses"
RAW_DATA_PATH   = DATA_DIR / "analysis_raw.json"
DRAW_SUMMARY_PATH   = ANALYSES_DIR / "draw_summary.json"
MODULE_MANIFEST_PATH = ANALYSES_DIR / "module_manifest.json"


# ── Directory setup ────────────────────────────────────────────────────────────
def ensure_dirs() -> None:
    ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    log.info("directories_ready", analyses=str(ANALYSES_DIR), raw=str(DATA_DIR))


# ── Load existing data ─────────────────────────────────────────────────────────
def load_existing_summary() -> list[dict]:
    """Return the stored draw list, or an empty list if no file exists yet."""
    if not DRAW_SUMMARY_PATH.exists():
        log.info("no_existing_summary")
        return []
    with DRAW_SUMMARY_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    log.info("loaded_existing_summary", count=len(data))
    return data


# ── Fetch live data ────────────────────────────────────────────────────────────
def fetch_ircc_data() -> dict:
    log.info("fetching_ircc_data", url=IRCC_JSON_URL)
    try:
        resp = requests.get(IRCC_JSON_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.error("fetch_failed", error=str(exc))
        sys.exit(1)
    raw = resp.json()
    log.info("fetch_success", status_code=resp.status_code)
    return raw


def save_raw(raw: dict) -> None:
    """Persist the full IRCC payload for auditing; always written."""
    with RAW_DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, ensure_ascii=False)
    log.info("raw_data_saved", path=str(RAW_DATA_PATH))


# ── Parse & filter ─────────────────────────────────────────────────────────────
def parse_draw(draw: dict) -> dict:
    """
    Normalise one raw IRCC draw object into the draw_summary schema.
    IRCC occasionally restructures their JSON; this function handles
    the most common field name variants.
    """
    round_number = int(
        draw.get("roundNumber")
        or draw.get("drawNumber")
        or 0
    )
    round_date = (
        draw.get("drawDateTime")
        or draw.get("drawDate")
        or draw.get("date")
        or ""
    )
    # drawName can be a dict {"en": "...", "fr": "..."} or a plain string
    draw_name = draw.get("drawName") or draw.get("drawNameEN") or ""
    if isinstance(draw_name, dict):
        draw_name = draw_name.get("en", "")

    return {
        "roundNumber":        round_number,
        "roundDate":          round_date,
        "roundType":          draw_name,
        "invitationsIssued":  int(draw.get("drawSize") or draw.get("invitations") or 0),
        "lowestScoreCutoff":  int(draw.get("drawCRS")  or draw.get("cutoffScore") or 0),
    }


def find_new_draws(raw: dict, existing: list[dict]) -> list[dict]:
    """Return normalised draws whose roundNumber exceeds the stored maximum."""
    highest_known = max((d["roundNumber"] for d in existing), default=0)
    log.info("highest_known_round", number=highest_known)

    # IRCC has used different top-level keys across dataset versions
    raw_draws = (
        raw.get("rounds")
        or raw.get("draws")
        or raw.get("data", {}).get("rounds", [])
        or []
    )
    log.info("raw_draw_count", count=len(raw_draws))

    new_draws: list[dict] = []
    for draw in raw_draws:
        try:
            parsed = parse_draw(draw)
        except Exception as exc:
            log.warning("parse_error", draw=draw, error=str(exc))
            continue
        if parsed["roundNumber"] > highest_known:
            new_draws.append(parsed)

    new_draws.sort(key=lambda d: d["roundNumber"])
    log.info("new_draws_detected", count=len(new_draws))
    return new_draws


# ── Build manifest ─────────────────────────────────────────────────────────────
def build_manifest() -> dict:
    """
    Map analytical UI labels to their static JSON endpoint paths.

    To add a new analysis module:
      1. Create a new script that writes a JSON file to public/data/analyses/
      2. Add an entry here: "Your Label": "/data/analyses/your_file.json"
      3. The React dashboard will automatically render a new container for it.
    """
    return {
        "Historical Cutoff Trends": "/data/analyses/draw_summary.json",
        # "Category Breakdown":       "/data/analyses/category_breakdown.json",
        # "Monthly Invitation Volume":"/data/analyses/monthly_volume.json",
    }


# ── Write outputs ──────────────────────────────────────────────────────────────
def save_summary(summary: list[dict]) -> None:
    with DRAW_SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log.info("summary_saved", records=len(summary), path=str(DRAW_SUMMARY_PATH))


def save_manifest(manifest: dict) -> None:
    with MODULE_MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    log.info("manifest_saved", modules=list(manifest.keys()))


# ── Entry point ────────────────────────────────────────────────────────────────
def main() -> None:
    log.info("etl_start", timestamp=datetime.now(timezone.utc).isoformat())

    ensure_dirs()
    existing  = load_existing_summary()
    raw       = fetch_ircc_data()
    save_raw(raw)

    new_draws = find_new_draws(raw, existing)

    if not new_draws:
        log.info("no_new_data", message="No new rounds found. Skipping file writes.")
        return

    updated_summary = existing + new_draws
    save_summary(updated_summary)
    save_manifest(build_manifest())

    log.info(
        "etl_complete",
        new_draws=len(new_draws),
        total_draws=len(updated_summary),
    )


if __name__ == "__main__":
    main()
