# Express Entry Draws Intelligence Dashboard

A fully automated, full-stack web application that visualises historical [Express Entry](https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry.html) draw data from IRCC Canada.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions (cron: daily)                           │
│    └── scripts/update_draws.py                          │
│          ├── Fetches IRCC JSON                          │
│          ├── Detects new rounds (by roundNumber)        │
│          ├── Writes public/data/analyses/*.json         │
│          └── Commits only when new data found           │
└─────────────────────┬───────────────────────────────────┘
                      │ static JSON files
┌─────────────────────▼───────────────────────────────────┐
│  React + Tailwind (GitHub Pages)                        │
│    AnalysisDataContext                                   │
│      └── fetches module_manifest.json on boot           │
│    DashboardGrid                                         │
│      └── maps manifest → AnalysisContainer × N          │
│    AnalysisContainer (per module)                       │
│      ├── Fetches its own data endpoint                  │
│      ├── Reserved visualization canvas                  │
│      └── Raw data table (proves data loaded)            │
└─────────────────────────────────────────────────────────┘
```

**Key design principle:** The Python ETL script drives the UI. Add a new analysis output file, register it in `build_manifest()`, and the dashboard automatically gains a new panel — no frontend changes needed.

---

## Quick Start

### 1 — Fork & clone

```bash
git clone https://github.com/YOUR_USERNAME/express-entry-dashboard.git
cd express-entry-dashboard
```

### 2 — Configure GitHub Pages

In your repo → **Settings → Pages**, set the source to **GitHub Actions**.

### 3 — Set your homepage URL

Edit `package.json`:
```json
"homepage": "https://YOUR_USERNAME.github.io/express-entry-dashboard"
```

### 4 — Enable the Actions

Both workflows are in `.github/workflows/`:
- `update_draws.yml` — runs daily at 05:00 UTC and on manual trigger
- `deploy.yml` — builds and deploys the React app on every push to `main`

Trigger the first ETL run manually:
**Actions → Daily Data Sync → Run workflow**

### 5 — Local development

```bash
npm install
npm start
```

The app will load the bootstrapped `public/data/analyses/` files.
To test with live data locally, run the ETL script first:

```bash
pip install requests structlog
python scripts/update_draws.py
```

---

## Project Structure

```
express-entry-dashboard/
├── .github/workflows/
│   ├── update_draws.yml       # Daily ETL + git commit
│   └── deploy.yml             # React build + GitHub Pages deploy
│
├── scripts/
│   └── update_draws.py        # ETL: fetch → parse → write JSON
│
├── data/
│   └── analysis_raw.json      # Full IRCC response (audit log, not served)
│
├── public/
│   ├── index.html
│   └── data/analyses/
│       ├── module_manifest.json   # Label → path map (drives the UI)
│       └── draw_summary.json      # Flattened draw records
│
└── src/
    ├── App.js
    ├── index.js
    ├── index.css
    ├── context/
    │   └── AnalysisDataContext.js  # Loads manifest; shared via Context
    └── components/
        ├── Header.js               # Title, status, last-updated
        ├── DashboardGrid.js        # Maps manifest → AnalysisContainer grid
        └── AnalysisContainer.js    # Canvas + data table (one per module)
```

---

## Adding a New Analysis Module

1. **Write a Python analysis script** that produces a new JSON file:
   ```python
   # scripts/analyse_categories.py
   import json
   output = [{"category": "...", "count": 42}]
   with open("public/data/analyses/category_breakdown.json", "w") as f:
       json.dump(output, f)
   ```

2. **Register it in the manifest** inside `scripts/update_draws.py`:
   ```python
   def build_manifest() -> dict:
       return {
           "Historical Cutoff Trends":  "/data/analyses/draw_summary.json",
           "Category Breakdown":        "/data/analyses/category_breakdown.json",  # ← new
       }
   ```

3. **Call your script** from the GitHub Action:
   ```yaml
   - name: Run ETL scripts
     run: |
       python scripts/update_draws.py
       python scripts/analyse_categories.py
   ```

4. **Push.** The React dashboard will automatically render a new panel for it.

To add a real visualisation to an existing panel, replace the canvas `<div>` inside `AnalysisContainer.js` with a Recharts, Chart.js, or D3 component — the data is already fetched and available as the `data` state variable.

---

## Data Schema

### `draw_summary.json`

Array of draw objects:

| Field                | Type     | Description                        |
|----------------------|----------|------------------------------------|
| `roundNumber`        | `number` | Sequential draw number             |
| `roundDate`          | `string` | ISO datetime of the draw           |
| `roundType`          | `string` | Draw category (e.g. "No Program Specified") |
| `invitationsIssued`  | `number` | Number of ITAs issued              |
| `lowestScoreCutoff`  | `number` | Minimum CRS score accepted         |

### `module_manifest.json`

Plain object mapping UI label strings to data endpoint paths:

```json
{
  "Historical Cutoff Trends": "/data/analyses/draw_summary.json"
}
```

---

## License

MIT
