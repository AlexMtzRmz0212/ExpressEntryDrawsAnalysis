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
│   ├── db.py                 # Supabase client, get_all_draws(), upsert_draws()
│   └── checker.py            # Change detection — compares IRCC vs DB draw numbers
│
├── sql/
│   └── schema.sql            # Run once in Supabase to create the draws table
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
| `POST` | `/api/refresh` | Fetch live IRCC data and upsert into Supabase | `Authorization: Bearer <REFRESH_SECRET>` |
| `GET` | `/api/cron` | Change-detection check — upserts only if IRCC has new draws | `Authorization: Bearer <CRON_SECRET>` |

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
  draw_number  INTEGER     PRIMARY KEY,
  draw_date    DATE        NOT NULL,
  draw_name    TEXT        NOT NULL,
  crs_cutoff   INTEGER     NOT NULL,
  invitations  INTEGER     NOT NULL,
  draw_url     TEXT,
  raw_data     JSONB,
  fetched_at   TIMESTAMPTZ DEFAULT NOW()
);
```

The `raw_data JSONB` column stores the complete original IRCC record. Any fields IRCC adds in the future are automatically preserved there, even before a schema migration.

### Environment variables

| Variable | Where to find it |
|---|---|
| `SUPABASE_URL` | Supabase project → Settings → API → Project URL |
| `SUPABASE_SERVICE_KEY` | Supabase project → Settings → API → `service_role` key (`sb_secret_...`) |
| `REFRESH_SECRET` | Any long random string you choose |
| `CRON_SECRET` | Any long random string you choose — Vercel injects it as a Bearer token on cron calls |

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

1. Reads the highest `draw_number` in Supabase (one row query)
2. Fetches the full IRCC JSON (~100 KB)
3. Compares: if `ircc_max > db_max` → upserts **only the new draws**
4. Otherwise returns `{"status": "no_change"}` and does nothing

Vercel calls `GET /api/cron` every 4 hours and automatically sends `Authorization: Bearer <CRON_SECRET>`. Add `CRON_SECRET` in **Vercel → Project → Settings → Environment Variables**.

> **Vercel plan note:** Cron jobs require the **Pro plan** for intervals shorter than 1 day. Free (Hobby) accounts can use `"0 20 * * *"` (once daily at 8 PM UTC / 4 PM EDT) as a fallback. Change the `schedule` field in `vercel.json` accordingly.

To test the cron locally:

```bash
curl http://localhost:8000/api/cron \
  -H "Authorization: Bearer your-cron-secret"
```

---

## Data source

Official IRCC Express Entry rounds JSON feed — updated by the Canadian government after each draw.

Not affiliated with IRCC or the Government of Canada. For informational purposes only.
