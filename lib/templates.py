"""
HTML for outbound email and for the confirm / unsubscribe landing pages.

Email clients are not browsers. They strip <style> blocks, JavaScript, flexbox,
grid, and most modern CSS. So everything here is:
  * table-based layout, fixed at 600px wide with a fluid fallback,
  * every style inline on the element,
  * system font stacks, because webfonts do not load in Outlook or Gmail,
  * charts drawn as nested table cells with percentage widths and solid
    background colours, which is the only bar chart that renders everywhere.

Palette is taken from tailwind.config.js so the mail matches the dashboard.
"""

from lib import drawstats, emailer

NAVY = "#16223d"
CRIMSON = "#c8362b"
WARM_BG = "#f1efe9"
WARM_MID = "#e6e2d8"
BORDER = "#e2ded3"
MUTED = "#5b6172"
SLATE = "#42485a"
WHITE = "#ffffff"
GREEN = "#2f8f6b"

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

SITE_NAME = "Express Entry Draws Intelligence"


def _esc(value) -> str:
    """Minimal HTML escaping for interpolated values."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _shell(title: str, body: str, preheader: str = "") -> str:
    """
    Wrap body markup in the outer email document.

    The preheader is the grey preview line inbox lists show next to the subject.
    It is hidden in the rendered message by a zero-size span.
    """
    hidden = (
        f'<span style="display:none;font-size:1px;color:{WARM_BG};line-height:1px;'
        f'max-height:0;max-width:0;opacity:0;overflow:hidden;">{_esc(preheader)}</span>'
        if preheader
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{_esc(title)}</title>
<style>
  /* Progressive enhancement only. Clients that strip this still get the inline
     light-mode styles below, which are the real design. */
  @media only screen and (max-width: 480px) {{
    .stack {{ display:block !important; width:100% !important; }}
    .pad {{ padding-left:18px !important; padding-right:18px !important; }}
    .hero-num {{ font-size:38px !important; }}
  }}
</style>
</head>
<body style="margin:0;padding:0;background:{WARM_BG};">
{hidden}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{WARM_BG};">
  <tr>
    <td align="center" style="padding:24px 12px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">
        {body}
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


def _header_row() -> str:
    """Brand bar, a flat navy block matching the site's logo tile."""
    return f"""
<tr>
  <td class="pad" style="background:{NAVY};border-radius:14px 14px 0 0;padding:22px 28px;">
    <div style="font:700 11px/1 {FONT};letter-spacing:.16em;text-transform:uppercase;color:#9fb0d4;">
      Express Entry, Canada
    </div>
    <div style="font:800 21px/1.2 {FONT};letter-spacing:-.02em;color:{WHITE};padding-top:6px;">
      Draws Intelligence
    </div>
  </td>
</tr>"""


def _footer_row(unsubscribe_url: str | None, *, show_legal: bool = True) -> str:
    """
    Closing block.

    CASL requires sender identification and a working unsubscribe in every
    commercial message, so the mailing address and the link are structural here,
    not decorative.
    """
    address = emailer.sender_address() or "Mailing address not configured"
    site = emailer.site_url()

    unsub = ""
    if unsubscribe_url:
        unsub = f"""
      <div style="font:400 12px/1.6 {FONT};color:{MUTED};padding-top:10px;">
        You are getting this because you confirmed a subscription at
        <a href="{_esc(site)}" style="color:{MUTED};">{_esc(site.replace('https://', ''))}</a>.
        <a href="{_esc(unsubscribe_url)}" style="color:{NAVY};font-weight:600;">Unsubscribe instantly</a>.
      </div>"""

    legal = ""
    if show_legal:
        legal = f"""
      <div style="font:400 12px/1.6 {FONT};color:{MUTED};padding-top:10px;">
        Independent project, not affiliated with or endorsed by IRCC or the Government of Canada.
        Figures come from the public IRCC feed and are informational only, not immigration advice.
      </div>"""

    return f"""
<tr>
  <td class="pad" style="background:{WHITE};border-radius:0 0 14px 14px;border-top:1px solid {BORDER};padding:20px 28px 26px;">
    <div style="font:600 13px/1.5 {FONT};color:{SLATE};">{_esc(SITE_NAME)}</div>
    <div style="font:400 12px/1.6 {FONT};color:{MUTED};padding-top:4px;">{_esc(address)}</div>
    {unsub}{legal}
  </td>
</tr>"""


def _button(label: str, url: str, *, background: str = NAVY) -> str:
    """A link styled as a button. Padding on the <a> keeps the whole box clickable."""
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td style="background:{background};border-radius:8px;">
      <a href="{_esc(url)}" style="display:inline-block;padding:14px 26px;font:700 15px/1 {FONT};color:{WHITE};text-decoration:none;">
        {_esc(label)}
      </a>
    </td>
  </tr>
</table>"""


# ---------------------------------------------------------------------------
# Confirmation email (double opt-in)
# ---------------------------------------------------------------------------

def confirm_email(token: str) -> tuple[str, str, str]:
    """Returns (subject, html, text) for the double opt-in confirmation."""
    url = f"{emailer.site_url()}/api/confirm?token={token}"
    subject = "Confirm your Express Entry draw alerts"

    body = f"""
{_header_row()}
<tr>
  <td class="pad" style="background:{WHITE};padding:30px 28px 8px;">
    <h1 style="margin:0;font:800 24px/1.25 {FONT};letter-spacing:-.02em;color:{NAVY};">
      One click to finish
    </h1>
    <p style="margin:14px 0 0;font:400 15px/1.65 {FONT};color:{SLATE};">
      Confirm this address and you will get an email each time IRCC publishes a new
      Express Entry round, usually within an hour of it going live. Every message
      includes the CRS cutoff, the number of invitations, and how the round compares
      to recent ones in the same category.
    </p>
    <p style="margin:14px 0 0;font:400 15px/1.65 {FONT};color:{SLATE};">
      Draws happen roughly every one to two weeks, so expect two to six emails a month.
      No other mail, ever.
    </p>
    <div style="padding:24px 0 8px;">
      {_button("Confirm subscription", url)}
    </div>
    <p style="margin:12px 0 0;font:400 13px/1.6 {FONT};color:{MUTED};">
      This link expires in 7 days. If you did not request this, ignore this email
      and nothing will be sent. Your address is deleted automatically if you never confirm.
    </p>
  </td>
</tr>
<tr><td style="background:{WHITE};padding:12px 28px 0;"></td></tr>
{_footer_row(None)}"""

    text = f"""Confirm your Express Entry draw alerts

Confirm this address to get an email each time IRCC publishes a new Express Entry
round, usually within an hour. Roughly two to six emails a month. No other mail.

Confirm here:
{url}

This link expires in 7 days. If you did not request this, ignore this email and
nothing will be sent.

{SITE_NAME}
{emailer.sender_address()}
Not affiliated with IRCC or the Government of Canada. Not immigration advice.
"""
    html = _shell(subject, body, "Click once to start getting new draw alerts.")
    return subject, html, text


# ---------------------------------------------------------------------------
# New draw email
# ---------------------------------------------------------------------------

def _delta_chip(delta: int | None, *, lower_is_good: bool, unit: str = "") -> str:
    """
    Small coloured pill showing the change vs the previous round of this category.

    For CRS a drop is good news, for invitations a rise is, so the caller says
    which direction to praise instead of hardcoding green for positive.
    """
    if delta is None:
        return f'<span style="font:600 12px/1 {FONT};color:{MUTED};">first round tracked</span>'
    if delta == 0:
        return (
            f'<span style="font:600 12px/1.4 {FONT};color:{MUTED};background:{WARM_BG};'
            f'padding:4px 8px;border-radius:999px;">no change</span>'
        )

    good = (delta < 0) if lower_is_good else (delta > 0)
    color = GREEN if good else CRIMSON
    arrow = "&#9660;" if delta < 0 else "&#9650;"
    return (
        f'<span style="font:600 12px/1.4 {FONT};color:{color};background:{WARM_BG};'
        f'padding:4px 8px;border-radius:999px;white-space:nowrap;">'
        f"{arrow} {abs(delta):,}{unit} vs last round</span>"
    )


def _stat_tile(label: str, value: str, chip: str) -> str:
    return f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{WHITE};border:1px solid {BORDER};border-radius:12px;">
  <tr>
    <td style="padding:16px 18px;">
      <div style="font:600 11px/1 {FONT};letter-spacing:.1em;text-transform:uppercase;color:#8a8f9e;">{_esc(label)}</div>
      <div style="font:800 30px/1.1 {MONO};letter-spacing:-.02em;color:{NAVY};padding:8px 0 8px;">{_esc(value)}</div>
      <div>{chip}</div>
    </td>
  </tr>
</table>"""


def _bar_chart(ctx: dict) -> str:
    """
    Recent CRS cutoffs for this category, as horizontal bars.

    Bar widths are percentages of a floor-adjusted range so small differences
    stay visible. Built from table cells because Gmail strips inline SVG and
    Outlook ignores CSS-drawn shapes.
    """
    points = ctx["recent_cutoffs"]
    if len(points) < 2:
        return ""

    scores = [p["crs"] for p in points]
    low, high = min(scores), max(scores)
    span = max(high - low, 1)

    rows = []
    for point in points:
        # Floor at 12% so the lowest bar is still a visible bar, not a sliver.
        width = 12 + round((point["crs"] - low) / span * 88)
        color = ctx["category_color"] if point["is_current"] else WARM_MID
        text_color = WHITE if point["is_current"] else SLATE
        weight = "800" if point["is_current"] else "600"
        # Built by hand rather than with %-d / %#d, which differ across platforms.
        label = f"{point['date'].strftime('%b')} {point['date'].day}" if point["date"] else ""

        rows.append(f"""
  <tr>
    <td width="64" style="font:500 11.5px/1.4 {MONO};color:{MUTED};padding:3px 8px 3px 0;white-space:nowrap;">{_esc(label)}</td>
    <td style="padding:3px 0;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="{width}%" style="background:{color};border-radius:4px;padding:5px 8px;font:{weight} 12px/1.3 {MONO};color:{text_color};white-space:nowrap;">{point['crs']}</td>
          <td style="font-size:1px;line-height:1px;">&nbsp;</td>
        </tr>
      </table>
    </td>
  </tr>""")

    return f"""
<tr>
  <td class="pad" style="background:{WHITE};padding:26px 28px 6px;">
    <h2 style="margin:0 0 4px;font:700 15px/1.3 {FONT};color:{NAVY};">
      Last {len(points)} {_esc(ctx['category_label'])} rounds
    </h2>
    <p style="margin:0 0 14px;font:400 13px/1.5 {FONT};color:{MUTED};">
      CRS cutoff by round, oldest at the top. This round is highlighted.
    </p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
      {''.join(rows)}
    </table>
  </td>
</tr>"""


def _callout(ctx: dict) -> str:
    """Highlight bar shown only when the round is a year-to-date record."""
    if ctx["is_lowest_of_year"]:
        message = (
            f"Lowest {ctx['category_label']} cutoff of {ctx['year']} so far, "
            f"at {ctx['crs_cutoff']} points."
        )
    elif ctx["is_largest_of_year"]:
        message = (
            f"Largest {ctx['category_label']} round of {ctx['year']} so far, "
            f"at {drawstats.format_number(ctx['invitations'])} invitations."
        )
    else:
        return ""

    return f"""
<tr>
  <td class="pad" style="background:{WHITE};padding:4px 28px 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{WARM_BG};border-left:3px solid {ctx['category_color']};border-radius:0 8px 8px 0;">
      <tr>
        <td style="padding:12px 16px;font:600 13.5px/1.5 {FONT};color:{NAVY};">{_esc(message)}</td>
      </tr>
    </table>
  </td>
</tr>"""


def draw_email(ctx: dict, unsubscribe_url: str) -> tuple[str, str, str]:
    """Returns (subject, html, text) for a new draw notification."""
    label = ctx["category_label"]
    subject = (
        f"New {label} draw: CRS {ctx['crs_cutoff']}, "
        f"{drawstats.format_number(ctx['invitations'])} invitations"
    )
    date_text = drawstats.format_date(ctx["draw_date"])
    site = emailer.site_url()

    gap_value = (
        f"{ctx['days_since_prev']}" if ctx["days_since_prev"] is not None else "n/a"
    )
    gap_chip = (
        f'<span style="font:600 12px/1.4 {FONT};color:{MUTED};">since the last {_esc(label)} round</span>'
        if ctx["days_since_prev"] is not None
        else f'<span style="font:600 12px/1 {FONT};color:{MUTED};">no earlier round tracked</span>'
    )

    ircc_link = ""
    if ctx.get("draw_url"):
        ircc_link = f"""
      <a href="{_esc(ctx['draw_url'])}" style="font:600 14px/1.4 {FONT};color:{NAVY};">
        Read the official IRCC page for round {_esc(ctx['draw_number'])}
      </a><br>"""

    ytd_lowest = ctx["ytd_lowest_crs"] if ctx["ytd_lowest_crs"] is not None else "n/a"

    body = f"""
{_header_row()}

<tr>
  <td class="pad" style="background:{ctx['category_color']};padding:26px 28px;">
    <div style="font:700 11px/1 {FONT};letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.78);">
      Round {_esc(ctx['draw_number'])}, {_esc(date_text)}
    </div>
    <div class="hero-num" style="font:800 44px/1.05 {FONT};letter-spacing:-.03em;color:{WHITE};padding-top:8px;">
      {_esc(label)} draw
    </div>
    <div style="font:400 14.5px/1.5 {FONT};color:rgba(255,255,255,.88);padding-top:8px;">
      {_esc(ctx['draw_name'])}
    </div>
  </td>
</tr>

<tr>
  <td class="pad" style="background:{WHITE};padding:22px 28px 6px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr>
        <td class="stack" width="33%" valign="top" style="padding:0 5px 10px 0;">
          {_stat_tile("CRS cutoff", str(ctx["crs_cutoff"]), _delta_chip(ctx["crs_delta"], lower_is_good=True))}
        </td>
        <td class="stack" width="34%" valign="top" style="padding:0 5px 10px;">
          {_stat_tile("Invitations", drawstats.format_number(ctx["invitations"]), _delta_chip(ctx["invites_delta"], lower_is_good=False))}
        </td>
        <td class="stack" width="33%" valign="top" style="padding:0 0 10px 5px;">
          {_stat_tile("Days since", gap_value, gap_chip)}
        </td>
      </tr>
    </table>
  </td>
</tr>

{_callout(ctx)}
{_bar_chart(ctx)}

<tr>
  <td class="pad" style="background:{WHITE};padding:22px 28px 6px;">
    <h2 style="margin:0 0 12px;font:700 15px/1.3 {FONT};color:{NAVY};">
      {_esc(ctx['category_label'])} in {_esc(ctx['year'])} so far
    </h2>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{WARM_BG};border-radius:12px;">
      <tr>
        <td style="padding:16px 18px;font:400 13.5px/1.9 {FONT};color:{SLATE};">
          <strong style="font-family:{MONO};color:{NAVY};">{ctx['ytd_rounds']}</strong> rounds held<br>
          <strong style="font-family:{MONO};color:{NAVY};">{drawstats.format_number(ctx['ytd_itas'])}</strong> invitations issued<br>
          <strong style="font-family:{MONO};color:{NAVY};">{_esc(ytd_lowest)}</strong> lowest CRS cutoff<br>
          <span style="color:{MUTED};">
            Across all categories in {_esc(ctx['year'])}:
            {ctx['all_ytd_rounds']} rounds, {drawstats.format_number(ctx['all_ytd_itas'])} invitations.
          </span>
        </td>
      </tr>
    </table>
  </td>
</tr>

<tr>
  <td class="pad" style="background:{WHITE};padding:22px 28px 26px;">
    <div style="padding-bottom:16px;">
      {_button("See the full breakdown", site, background=NAVY)}
    </div>
    {ircc_link}
  </td>
</tr>

{_footer_row(unsubscribe_url)}"""

    text = f"""{subject}

Round {ctx['draw_number']}, {date_text}
{ctx['draw_name']}

CRS cutoff: {ctx['crs_cutoff']}
Invitations: {drawstats.format_number(ctx['invitations'])}
Days since the last {label} round: {gap_value}

{label} in {ctx['year']} so far: {ctx['ytd_rounds']} rounds,
{drawstats.format_number(ctx['ytd_itas'])} invitations, lowest cutoff {ytd_lowest}.
All categories in {ctx['year']}: {ctx['all_ytd_rounds']} rounds,
{drawstats.format_number(ctx['all_ytd_itas'])} invitations.

Full breakdown: {site}
{('Official IRCC page: ' + ctx['draw_url']) if ctx.get('draw_url') else ''}

Unsubscribe instantly: {unsubscribe_url}

{SITE_NAME}
{emailer.sender_address()}
Not affiliated with IRCC or the Government of Canada. Not immigration advice.
"""

    preheader = (
        f"Round {ctx['draw_number']}, CRS {ctx['crs_cutoff']}, "
        f"{drawstats.format_number(ctx['invitations'])} invitations."
    )
    return subject, _shell(subject, body, preheader), text


# ---------------------------------------------------------------------------
# Owner alerts
# ---------------------------------------------------------------------------

def admin_alert(event: str, email: str, when: str, total: int) -> tuple[str, str, str]:
    """
    Short internal notice for the site owner. `event` is 'subscribed' or 'unsubscribed'.

    Kept plain on purpose: this is an operations alert, not a designed message.
    """
    verb = "New subscriber" if event == "subscribed" else "Unsubscribe"
    accent = GREEN if event == "subscribed" else CRIMSON
    subject = f"{verb}: {email} ({total} confirmed)"

    body = f"""
{_header_row()}
<tr>
  <td class="pad" style="background:{WHITE};border-radius:0 0 14px 14px;padding:26px 28px 28px;">
    <div style="font:700 11px/1 {FONT};letter-spacing:.14em;text-transform:uppercase;color:{accent};">
      {_esc(verb)}
    </div>
    <div style="font:800 22px/1.3 {FONT};color:{NAVY};padding:8px 0 16px;word-break:break-all;">
      {_esc(email)}
    </div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{WARM_BG};border-radius:10px;">
      <tr>
        <td style="padding:14px 16px;font:400 13.5px/1.8 {FONT};color:{SLATE};">
          When: <strong style="font-family:{MONO};">{_esc(when)}</strong><br>
          Confirmed subscribers now:
          <strong style="font-family:{MONO};color:{NAVY};">{total}</strong>
        </td>
      </tr>
    </table>
  </td>
</tr>"""

    text = f"{verb}: {email}\nWhen: {when}\nConfirmed subscribers now: {total}\n"
    return subject, _shell(subject, body, subject), text


# ---------------------------------------------------------------------------
# Confirm / unsubscribe landing pages
# ---------------------------------------------------------------------------

def landing_page(title: str, message: str, *, tone: str = "good") -> str:
    """
    Standalone HTML page returned by /api/confirm and /api/unsubscribe.

    The dashboard is a single-page app with no router, so these links resolve to
    a real server-rendered page rather than a deep link the SPA cannot handle.
    """
    accent = {"good": GREEN, "bad": CRIMSON, "neutral": NAVY}.get(tone, NAVY)
    site = emailer.site_url()

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
</head>
<body style="margin:0;background:{WARM_BG};font-family:{FONT};">
  <main style="max-width:520px;margin:0 auto;padding:64px 20px;">
    <div style="background:{WHITE};border:1px solid {BORDER};border-radius:14px;padding:32px 28px;">
      <div style="font:700 11px/1 {FONT};letter-spacing:.16em;text-transform:uppercase;color:{accent};">
        Express Entry, Canada
      </div>
      <h1 style="margin:8px 0 0;font:800 26px/1.25 {FONT};letter-spacing:-.02em;color:{NAVY};">
        {_esc(title)}
      </h1>
      <p style="margin:14px 0 0;font:400 15px/1.65 {FONT};color:{SLATE};">
        {_esc(message)}
      </p>
      <p style="margin:26px 0 0;">
        <a href="{_esc(site)}" style="display:inline-block;background:{NAVY};color:{WHITE};
           text-decoration:none;border-radius:8px;padding:13px 24px;font:700 14px/1 {FONT};">
          Go to the dashboard
        </a>
      </p>
    </div>
    <p style="margin:18px 0 0;text-align:center;font:400 12px/1.6 {FONT};color:{MUTED};">
      {_esc(SITE_NAME)}. Not affiliated with IRCC or the Government of Canada.
    </p>
  </main>
</body>
</html>"""
