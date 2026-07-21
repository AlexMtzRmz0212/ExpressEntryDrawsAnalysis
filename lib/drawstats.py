"""
Stats for a single draw, computed for the notification email.

This is a deliberate Python mirror of logic the frontend already has:
  * get_draw_type / CATEGORY_COLORS  <- src/utils/categories.js
  * year-to-date figures             <- src/components/latest/LatestStats.jsx

Same definitions on both sides, so the email and the dashboard never disagree
about the same draw. If a category or a colour changes in one place, change it
in the other.
"""

from datetime import date, datetime

# Mirrors CAT in src/utils/categories.js
CATEGORY_COLORS = {
    "General": "#16223d",
    "CEC": "#3a6ea8",
    "PNP": "#6d4c91",
    "French": "#c8362b",
    "Healthcare": "#2f8f6b",
    "Education": "#c08a2d",
    "Trades": "#cc6b33",
    "Agriculture": "#7a9a3a",
    "STEM": "#4a5fb0",
    "Transport": "#3d9098",
}

CATEGORY_LABELS = {
    "General": "General",
    "CEC": "CEC",
    "PNP": "Provincial",
    "French": "French",
    "Healthcare": "Healthcare",
    "Education": "Education",
    "Trades": "Trades",
    "Agriculture": "Agriculture",
    "STEM": "STEM",
    "Transport": "Transport",
}

FALLBACK_COLOR = "#8a8f9e"

# How many past rounds of the same category the in-email bar chart shows.
CHART_POINTS = 8


def get_draw_type(draw_name: str | None) -> str:
    """Mirror of getDrawType() in src/utils/categories.js."""
    if not draw_name:
        return "General"
    name = draw_name.lower().strip()
    if "provincial" in name:
        return "PNP"
    if "canadian experience" in name or "canadian work experience" in name or name == "cec":
        return "CEC"
    if "french" in name:
        return "French"
    if "healthcare" in name or "health care" in name:
        return "Healthcare"
    if "education" in name:
        return "Education"
    if "trade" in name:
        return "Trades"
    if "agriculture" in name or "agri-food" in name:
        return "Agriculture"
    if "stem" in name:
        return "STEM"
    if "transport" in name:
        return "Transport"
    return draw_name.strip()


def category_color(draw_type: str) -> str:
    return CATEGORY_COLORS.get(draw_type, FALLBACK_COLOR)


def category_label(draw_type: str) -> str:
    return CATEGORY_LABELS.get(draw_type, draw_type or "General")


def _as_date(value) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def format_date(value) -> str:
    """'2026-07-15' -> 'July 15, 2026'. Falls back to the raw value."""
    parsed = _as_date(value)
    if parsed is None:
        return str(value)
    return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"


def format_number(value) -> str:
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def build_context(draw: dict, all_draws: list[dict]) -> dict:
    """
    Build every figure the draw email needs.

    `all_draws` is the full table in any order; it is sorted here. `draw` is the
    newly detected round, which is expected to be present in `all_draws` but is
    handled correctly either way.
    """
    draw_type = get_draw_type(draw.get("draw_name"))
    draw_date = _as_date(draw.get("draw_date"))

    # Oldest first, matching the order the frontend sorts into in useDraws.js.
    ordered = sorted(
        (d for d in all_draws if _as_date(d.get("draw_date")) is not None),
        key=lambda d: (_as_date(d["draw_date"]), str(d.get("draw_number", ""))),
    )

    # Everything strictly before this draw, so the "previous round" comparisons
    # are correct even when /api/notify runs after several draws landed at once.
    number = str(draw.get("draw_number", ""))
    if draw_date is None:
        # Unparseable date should be impossible (lib/ircc.py drops those rounds),
        # but if it happens, compare against nothing rather than crashing.
        prior = []
    else:
        key = (draw_date, number)
        prior = [
            d
            for d in ordered
            if (_as_date(d["draw_date"]), str(d.get("draw_number", ""))) < key
        ]

    same_category_prior = [d for d in prior if get_draw_type(d.get("draw_name")) == draw_type]

    prev_same = same_category_prior[-1] if same_category_prior else None
    prev_any = prior[-1] if prior else None

    crs_delta = None
    invites_delta = None
    days_since_prev = None
    if prev_same:
        crs_delta = int(draw["crs_cutoff"]) - int(prev_same["crs_cutoff"])
        invites_delta = int(draw["invitations"]) - int(prev_same["invitations"])
        prev_date = _as_date(prev_same["draw_date"])
        if prev_date and draw_date:
            days_since_prev = (draw_date - prev_date).days

    days_since_any = None
    if prev_any:
        prev_date = _as_date(prev_any["draw_date"])
        if prev_date and draw_date:
            days_since_any = (draw_date - prev_date).days

    # Year to date, including this draw, matching LatestStats.jsx which scopes to
    # the latest draw's own category and calendar year.
    year = draw_date.year if draw_date else None
    same_cat_ytd = [
        d
        for d in same_category_prior
        if (_as_date(d["draw_date"]) or date.min).year == year
    ] + [draw]
    all_ytd = [d for d in prior if (_as_date(d["draw_date"]) or date.min).year == year] + [draw]

    ytd_cutoffs = [int(d["crs_cutoff"]) for d in same_cat_ytd]
    ytd_lowest_crs = min(ytd_cutoffs) if ytd_cutoffs else None

    # Chart: this draw plus the preceding rounds of the same category.
    chart_source = (same_category_prior + [draw])[-CHART_POINTS:]
    recent_cutoffs = [
        {
            "draw_number": str(d.get("draw_number", "")),
            "date": _as_date(d["draw_date"]),
            "crs": int(d["crs_cutoff"]),
            "invitations": int(d["invitations"]),
            "is_current": str(d.get("draw_number", "")) == number,
        }
        for d in chart_source
    ]

    return {
        "draw_number": number,
        "draw_name": draw.get("draw_name") or "",
        "draw_date": draw_date,
        "draw_url": draw.get("draw_url"),
        "crs_cutoff": int(draw["crs_cutoff"]),
        "invitations": int(draw["invitations"]),
        "category": draw_type,
        "category_label": category_label(draw_type),
        "category_color": category_color(draw_type),
        "crs_delta": crs_delta,
        "invites_delta": invites_delta,
        "days_since_prev": days_since_prev,
        "days_since_any": days_since_any,
        "year": year,
        "ytd_rounds": len(same_cat_ytd),
        "ytd_itas": sum(int(d["invitations"]) for d in same_cat_ytd),
        "ytd_lowest_crs": ytd_lowest_crs,
        "all_ytd_rounds": len(all_ytd),
        "all_ytd_itas": sum(int(d["invitations"]) for d in all_ytd),
        "recent_cutoffs": recent_cutoffs,
        "is_lowest_of_year": (
            ytd_lowest_crs is not None
            and int(draw["crs_cutoff"]) <= ytd_lowest_crs
            and len(same_cat_ytd) > 1
        ),
        "is_largest_of_year": (
            len(same_cat_ytd) > 1
            and int(draw["invitations"]) >= max(int(d["invitations"]) for d in same_cat_ytd)
        ),
    }
