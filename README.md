# Express Entry Draws Intelligence

A live dashboard for Canadian Express Entry draw data — deployed at **EE.bittobyte.qzz.io**.

Pulls official draw data from IRCC, stores it in a Supabase database, and renders an interactive analytics UI with trend charts, predictions, score checking, and a full draws table.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend API | Python 3.11 + FastAPI + Mangum |
| Database | Supabase (hosted Postgres) |
| Hosting | Vercel (static frontend + Python serverless functions) |
| Data source | IRCC official JSON feed |

---

## Project structure

```
ExpressEntryDrawsAnalysis/
│
├── api/
│   └── index.py              # FastAPI app — all API routes (Vercel serverless entry)
│
├── lib/
│   ├── __init__.py
│   ├── ircc.py               # Fetches + parses the IRCC JSON feed
│   ├── db.py                 # Supabase client, draws + sync_runs + subscribers helpers
│   ├── checker.py            # Change detection — set-difference of IRCC vs DB draw numbers
│   ├── emailer.py            # Resend REST client (send_one / send_batch), never raises
│   ├── drawstats.py          # Per-draw stats for the email (Python mirror of src/utils)
│   ├── templates.py          # Email HTML + confirm/unsubscribe landing pages
│   └── notifier.py           # Notification outbox — claims a draw, then sends it
│
├── .github/
│   └── workflows/
│       └── refresh.yml       # Backup scheduler — pings /api/refresh every 3h, 09–21 UTC
│
├── sql/
│   └── schema.sql            # Run once in Supabase to create the draws + sync_runs tables
│
├── src/
│   ├── main.jsx              # React entry point
│   ├── App.jsx               # Root component — tab routing, data fetch
│   ├── index.css             # Tailwind directives + global resets
│   │
│   ├── hooks/
│   │   └── useDraws.js       # Fetches /api/draws, enriches and sorts data
│   │
│   ├── utils/
│   │   ├── categories.js     # Draw type → color/label mapping + getDrawType()
│   │   ├── format.js         # Date and number formatting helpers
│   │   └── stats.js          # Linear regression, gap computation, predictions
│   │
│   └── components/
│       ├── Header.jsx
│       ├── TabNav.jsx
│       ├── overview/
│       │   ├── Overview.jsx
│       │   ├── HeroStats.jsx     # 4 stat cards (latest draw, invitations, delta, cadence)
│       │   ├── TrendChart.jsx    # SVG line chart with hover tooltips + filter chips
│       │   ├── CategoryBars.jsx  # Invitations by category, year selector
│       │   ├── DrawRhythm.jsx    # Bar chart of days between draws
│       │   └── ScoreChecker.jsx  # CRS score input → which draws would invite you
│       ├── predictions/
│       │   ├── Predictions.jsx
│       │   ├── ForecastCard.jsx      # Predicted next CRS, date window, confidence
│       │   └── CategoryOutlook.jsx   # Last cutoff + trend per stream
│       └── table/
│           └── DrawsTable.jsx    # Sortable, filterable, searchable draws table
│
├── index.html                # Vite HTML entry + Google Fonts
├── package.json
├── vite.config.js            # Vite config + dev proxy (/api → localhost:8000)
├── tailwind.config.js        # Custom brand colors and fonts
├── postcss.config.js
├── vercel.json               # Build config + API routing + SPA fallback
├── requirements.txt          # Python dependencies
├── .env.example              # Template for required environment variables
└── .gitignore
```

---

## Backend

### How it works

The backend is a Python **FastAPI** application deployed as a Vercel serverless function via the **Mangum** ASGI adapter.

On every `POST /api/refresh` call:
1. `lib/ircc.py` fetches the IRCC JSON from the official Canadian government endpoint
2. Each draw record is parsed and normalised (string → typed values, date parsed, draw type inferred)
3. `lib/db.py` upserts the records into Supabase using `draw_number` as the conflict key — so re-running is always safe
4. `GET /api/draws` reads all rows from Supabase and returns them as JSON, newest first

### API endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/api/draws` | All draws from the database, newest first | None |
| `GET` | `/api/status` | Most recent sync run + public-button cooldown state | None |
| `POST` | `/api/check` | Public "Check now" trigger — change-detection, rate-limited server-side | None |
| `POST` | `/api/refresh` | Fetch live IRCC data and upsert into Supabase | `Authorization: Bearer <REFRESH_SECRET>` |
| `GET` | `/api/cron` | Change-detection check — upserts only if IRCC has new draws | `Authorization: Bearer <CRON_SECRET>` |
| `POST` | `/api/subscribe` | Double opt-in signup for draw alert emails — sends a confirmation link | None |
| `GET` | `/api/confirm` | Confirmation landing page (`?token=...`) — activates a subscription | None |
| `GET`/`POST` | `/api/unsubscribe` | One-click unsubscribe landing page (`?token=...`) | None |
| `POST` | `/api/notify` | Drain the notification outbox — emails subscribers about unsent draws | `Authorization: Bearer <REFRESH_SECRET>` |

**`GET /api/draws` response shape:**
```json
[
  {
    "draw_number": 393,
    "draw_date": "2026-06-10",
    "draw_name": "Canadian Experience Class",
    "crs_cutoff": 507,
    "invitations": 3000,
    "draw_url": "https://...",
    "raw_data": { "...": "full IRCC record" },
    "fetched_at": "2026-06-24T00:00:00Z"
  }
]
```

**`POST /api/refresh` response shape:**
```json
{ "inserted": 2, "already_present": 86, "total_in_db": 88 }
```

### Database schema

Run `sql/schema.sql` **once** in the Supabase SQL Editor before the first deploy:

```sql
CREATE TABLE IF NOT EXISTS draws (
  draw_number  TEXT        PRIMARY KEY,   -- usually numeric, but IRCC uses suffixes too ("91a", "91b")
  draw_date    DATE        NOT NULL,
  draw_name    TEXT        NOT NULL,
  crs_cutoff   INTEGER     NOT NULL,
  invitations  INTEGER     NOT NULL,
  draw_url     TEXT,
  raw_data     JSONB,
  fetched_at   TIMESTAMPTZ DEFAULT NOW()
);
```

`draw_number` is **`TEXT`**, not an integer: IRCC has issued suffixed rounds such as
`91a`/`91b`, which an integer column cannot store. The full `sql/schema.sql` also creates a
`sync_runs` heartbeat table (see below).

The `raw_data JSONB` column stores the complete original IRCC record. Any fields IRCC adds in the future are automatically preserved there, even before a schema migration.

### Environment variables

| Variable | Where to find it |
|---|---|
| `SUPABASE_URL` | Supabase project → Settings → API → Project URL |
| `SUPABASE_SERVICE_KEY` | Supabase project → Settings → API → `service_role` key (`sb_secret_...`) |
| `REFRESH_SECRET` | Any long random string you choose |
| `CRON_SECRET` | Any long random string you choose — Vercel injects it as a Bearer token on cron calls |
| `RESEND_API_KEY` | resend.com → API Keys. Leave unset to disable all outbound email |
| `MAIL_FROM` | e.g. `Express Entry Draws <notifications@ee.bittobyte.qzz.io>` — domain must be verified in Resend |
| `ADMIN_EMAIL` | Where "someone subscribed / unsubscribed" alerts go. Unset = no alerts |
| `SITE_URL` | Public base URL, used to build confirm and unsubscribe links |
| `MAIL_SENDER_ADDRESS` | Postal address printed in every subscriber email. **Required by CASL** |

Copy `.env.example` to `.env` for local development. On Vercel, add them in **Project → Settings → Environment Variables** — they are never stored in a file on the server.

### Backend setup (first time)

```bash
# 1. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in the env file
cp .env.example .env
# edit .env with your Supabase URL, service key, and a refresh secret

# 4. Run the schema in Supabase SQL Editor (one-time)
# Open sql/schema.sql, copy contents, paste into Supabase → SQL Editor → Run

# 5. Start the dev server
uvicorn api.index:app --reload
```

Test the endpoints:

```bash
# Populate the database from IRCC
curl -X POST http://localhost:8000/api/refresh \
  -H "Authorization: Bearer your-refresh-secret"

# Verify data came back
curl http://localhost:8000/api/draws
```

---

## Frontend

### How it works

A **React + Vite** single-page application. On load, `useDraws.js` fetches `/api/draws`, enriches each record (mapping `draw_name` → a short type key like `CEC`, `PNP`, etc. with its colour), then passes the sorted array down to all components.

All business logic lives in `src/utils/`:
- **`categories.js`** — maps IRCC program names to internal type keys and brand colours
- **`format.js`** — date and number formatting used everywhere
- **`stats.js`** — linear regression for predictions, gap computation between draws

All chart rendering is pure SVG — no chart library dependency.

### Draw type classification

IRCC `draw_name` strings are mapped to short type keys automatically:

| IRCC draw name (contains) | Internal type | Colour |
|---|---|---|
| "Canadian Experience" | `CEC` | Blue |
| "Provincial" | `PNP` | Purple |
| "French" | `French` | Red |
| "Healthcare" | `Healthcare` | Green |
| "Education" | `Education` | Amber |
| "Trade" | `Trades` | Orange |
| "Agriculture" / "Agri-food" | `Agriculture` | Olive |
| "STEM" | `STEM` | Indigo |
| "Transport" | `Transport` | Teal |
| anything else | `General` | Navy |

### Frontend setup

```bash
# Install Node dependencies
npm install

# Start the dev server (proxies /api/* to localhost:8000)
npm run dev
```

The Vite dev server runs on `http://localhost:5173` and automatically proxies all `/api/*` requests to the FastAPI server on port 8000. Both servers must be running simultaneously during development.

### Build for production

```bash
npm run build
# Output goes to dist/ — served by Vercel as static files
```

---

## Development workflow

Two terminals side by side:

```
Terminal 1                          Terminal 2
────────────────────────────────    ────────────────────────────────
uvicorn api.index:app --reload      npm run dev
(Python backend on :8000)           (Vite frontend on :5173)
```

Open `http://localhost:5173`. The frontend proxies API calls to the backend automatically.

After the first `POST /api/refresh`, the UI populates with real IRCC data.

---

## Deployment (Vercel)

### First deploy

```bash
# Install Vercel CLI if you haven't
npm install -g vercel

# Deploy (follow prompts to link your Vercel account and project)
vercel

# Set environment variables
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY
vercel env add REFRESH_SECRET
vercel env add CRON_SECRET

# Deploy to production
vercel --prod
```

Vercel automatically:
- Runs `npm run build` → compiles the React app → serves from `dist/`
- Deploys `api/index.py` as a Python serverless function
- Routes `/api/*` to the Python function (configured in `vercel.json`)
- Falls back all other routes to `index.html` (SPA client-side routing)

### Custom domain (EE.bittobyte.qzz.io)

1. In your domain registrar, add a **CNAME** record:
   - Host: `EE`
   - Value: `cname.vercel-dns.com`
2. In the Vercel dashboard → Project → Settings → Domains → add `EE.bittobyte.qzz.io`
3. Vercel provisions an SSL certificate automatically within a few minutes

### Populate the production database

After deploying, seed the database by calling the refresh endpoint once:

```bash
curl -X POST https://EE.bittobyte.qzz.io/api/refresh \
  -H "Authorization: Bearer your-refresh-secret"
```

---

## Modules

| # | Module | Status |
|---|---|---|
| 1 | Data backend — IRCC fetch, Supabase DB, REST API | Done |
| 2 | Frontend — React + Vite + Tailwind dashboard | Done |
| 3 | Scheduled auto-refresh with change detection | Done |
| 4 | Admin dashboard / manual refresh UI | Planned |
| 5 | CORS hardening + rate limiting | Planned |

### Module 3 — how the cron works

Instead of blindly upserting all draws on a fixed schedule, `/api/cron`:

1. Reads the **set** of `draw_number`s already in Supabase (one query)
2. Fetches the full IRCC JSON (~100 KB)
3. Upserts **only the draws whose `draw_number` is not already stored**
4. Otherwise returns `{"status": "no_change"}` and does nothing
5. Records a row in `sync_runs` (visible via `GET /api/status`)

Set-membership detection is deliberate: comparing counts (or `max(draw_number)`) breaks on
suffixed rounds like `91a`/`91b`, and a count comparison silently stops detecting new draws
forever if the DB ever gets ahead of the feed's valid count.

Vercel calls `GET /api/cron` on the `vercel.json` schedule and automatically sends
`Authorization: Bearer <CRON_SECRET>`. **Cron schedules are always UTC** — `"7 12 * * *"`
fires at 12:07 UTC, which is **8:07 AM EDT** (not noon Eastern). The `:07` minute (rather
than `:00`) avoids the congested top-of-hour cron slot. Add `CRON_SECRET` in
**Vercel → Project → Settings → Environment Variables**.

> **Vercel plan note:** On the **Hobby (free) plan**, cron jobs run at most once/day and are
> **best-effort — they can be delayed or skipped entirely.** Do not rely on the Vercel cron
> alone; the GitHub Actions backup scheduler below is what makes updates reliable.

To test the cron locally:

```bash
curl http://localhost:8000/api/cron \
  -H "Authorization: Bearer your-cron-secret"
```

### Reliable updates — GitHub Actions backup scheduler

Because Hobby-plan Vercel crons are unreliable (and IRCC sometimes publishes its JSON feed a
few hours after a round), `.github/workflows/refresh.yml` runs an **independent** scheduler on
GitHub's infrastructure. It `POST`s `/api/refresh` **every 3 hours across 09:00–21:00 UTC**
(`23 9,12,15,18,21 * * *` → 09:23, 12:23, 15:23, 18:23, 21:23) — the window in which IRCC
realistically publishes a round. There are **no overnight runs**; an off-window draw is caught
by the 09:23 run, the Vercel daily cron, or a user pressing **Check now** (see below). The
`:23` minute dodges the congested top-of-hour slot, and the upsert is idempotent, so the extra
calls are cheap no-ops when there's nothing new.

**One-time setup** — in **GitHub → repo → Settings → Secrets and variables → Actions**:

| Kind | Name | Value |
|---|---|---|
| Secret | `REFRESH_SECRET` | Same value as the `REFRESH_SECRET` env var on Vercel |
| Variable | `BASE_URL` | `https://ee.bittobyte.qzz.io` (optional — this is the default) |

Trigger a run manually any time from the **Actions** tab → *Refresh Express Entry draws* →
**Run workflow**.

> **Note:** GitHub scheduled workflows only run from the **default branch**, may be delayed
> under load, and are **auto-disabled after 60 days of no repo activity**. The manual
> *Run workflow* button (`workflow_dispatch`) is always available as a fallback.

### On-demand updates — the public "Check now" button

A visitor who believes a round just dropped can force a live IRCC check from the header
button, which calls **`POST /api/check`**. It runs the same change-detection as the cron
(fetching IRCC and writing only if there's a genuinely new draw) but needs **no secret** —
abuse is bounded **server-side**, not by hiding the button:

- If a new draw was **already found today** (UTC) — by any scheduler or a previous press — the
  endpoint returns `{ "allowed": false, "reason": "updated_today", "unlock_at": "<next UTC midnight>" }`
  and makes **no** IRCC call. The button stays locked until tomorrow; the scheduled cron keeps
  running normally.
- Otherwise, if **any sync ran within the last hour**, it returns
  `{ "allowed": false, "reason": "recently_checked", "unlock_at": "<ran_at + 1h>" }` — again no
  IRCC call.
- Otherwise it runs the check and returns `{ "allowed": true, "result": { ... }, "manual_check": { ... } }`.

Net effect: IRCC is hit **at most once per hour** from the button (and not again for the rest
of the day once a draw is found), no matter how many people press it. The two thresholds are
one-line constants (`MISS_COOLDOWN` and the UTC day boundary) in `api/index.py`. The current
lock state is also exposed on `GET /api/status` under `manual_check`, which is how the frontend
decides whether to enable the button.

```bash
curl -X POST https://ee.bittobyte.qzz.io/api/check
# → { "allowed": true, "result": { "status": "no_change", ... }, "manual_check": { ... } }
```

### Checking when data last updated

```bash
curl https://ee.bittobyte.qzz.io/api/status
# → { "last_sync": { "ran_at": "...", "status": "updated", ... }, "manual_check": { ... } }
```

---

## Email notifications

Visitors can subscribe to get an email each time IRCC publishes a new round. Each message
carries the CRS cutoff and invitation count, the change versus the previous round in the same
category, a bar chart of recent cutoffs for that category, and year-to-date totals.

### Why the outbox, instead of sending from the refresh code

Three different code paths insert draws: `/api/cron` and `/api/check` (both via
`lib/checker.py`), and `/api/refresh`, which the GitHub Actions scheduler calls directly.
Sending mail inline from `checker` would miss the third, and two paths waking at the same
moment could send the same draw twice.

So sending is queue-driven. `draw_notifications` holds one row per draw that has been handled,
and `lib/notifier.py` asks "which draws have no row?". Claiming a draw is an `INSERT` against a
`PRIMARY KEY`, so the database picks a single winner. Every path calls the notifier afterwards,
and the GitHub workflow calls `/api/notify` on every poll as a retry net.

```
IRCC feed → checker / refresh → draws table
                                     │
                             /api/notify (drain the outbox)
                                     │
                    claim a row in draw_notifications   ← the double-send guard
                                     │
                  build stats → render HTML → Resend batch API → subscribers
```

Two guards stop the historical archive going out as mail: `sql/schema.sql` seeds
`draw_notifications` from every draw that already exists, and `notifier.MAX_NOTIFY_AGE`
refuses to email about any draw dated more than 10 days ago.

### Double opt-in

`POST /api/subscribe` does **not** add anyone to the list. It writes a `pending` row and emails
a confirmation link; only clicking that link sets `status = 'confirmed'`. This is what Canada's
anti-spam legislation (CASL) means by express consent, and it also means the endpoint cannot be
used to sign somebody else up. Unconfirmed rows are deleted after 7 days by the daily cron.

The endpoint returns an identical response for a new address, an already-pending one, an
already-confirmed one, and a rate-limited request, so it cannot be used to test whether a given
address is on the list. A hidden honeypot field and a 3-per-IP-per-hour limit bound abuse
without a CAPTCHA.

### CASL compliance checklist

| Requirement | Where it is handled |
|---|---|
| Express consent | Double opt-in via `/api/confirm` |
| Proof of consent | `subscribers.consent_ip`, `consent_user_agent`, `confirmed_at` |
| Sender identification | `MAIL_SENDER_ADDRESS` in every email footer (`lib/templates.py`) |
| Working unsubscribe | One-click `/api/unsubscribe`, no login, effective immediately |
| Unsubscribe in mail clients | `List-Unsubscribe` + `List-Unsubscribe-Post` headers (RFC 8058) |
| Honoured within 10 business days | Immediate; record deleted within 30 days |

> **Before going live**, set `MAIL_SENDER_ADDRESS` to a real physical or postal address (a PO
> box is fine). CASL requires one in every commercial email, and the footer ships with a
> placeholder until you set it.

### Resend setup

1. Add the domain in Resend → Domains, then create the **DKIM `TXT`**, **SPF `TXT`**, and
   return-path records it generates in your DNS. Without these, mail is rejected or spam-filed.
2. A DMARC record is strongly recommended alongside them:
   `_dmarc` → `v=DMARC1; p=none; rua=mailto:you@example.com`
3. Create an API key and set `RESEND_API_KEY` on Vercel.

> **Free-tier ceiling:** Resend's free plan allows 100 emails/day. That caps the list at about
> 100 confirmed subscribers before a paid plan (or a switch to a provider like Brevo) is
> needed. When a send is truncated, `lib/notifier.py` logs a warning rather than failing
> silently, and the draw is left retryable.

### Testing a send safely

```bash
# Re-send the newest draw to the current list (normally only fires once)
# 1. In Supabase: DELETE FROM draw_notifications WHERE draw_number = '<newest>';
# 2. Then:
curl -X POST https://ee.bittobyte.qzz.io/api/notify \
  -H "Authorization: Bearer $REFRESH_SECRET"

# Run it a second time — it must report 0 sends, proving the claim works.
```

---

## Data source

Official IRCC Express Entry rounds JSON feed — updated by the Canadian government after each draw.

Not affiliated with IRCC or the Government of Canada. For informational purposes only.
