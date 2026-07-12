-- Run this once in the Supabase SQL Editor before first deploy.
-- Table Editor → SQL Editor → paste → Run

CREATE TABLE IF NOT EXISTS draws (
  draw_number   TEXT        PRIMARY KEY,          -- IRCC draw # as text: usually numeric ("308") but sometimes suffixed ("91a", "91b")
  draw_date     DATE        NOT NULL,             -- date of the draw
  draw_name     TEXT        NOT NULL,             -- e.g. "Provincial Nominee Program"
  crs_cutoff    INTEGER     NOT NULL,             -- minimum CRS score for this round
  invitations   INTEGER     NOT NULL,             -- number of ITAs issued
  draw_url      TEXT,                             -- link to the official IRCC draw page
  raw_data      JSONB,                            -- full original IRCC record (future-proof)
  fetched_at    TIMESTAMPTZ DEFAULT NOW()         -- when we last upserted this row
);

-- Speed up newest-first and date-range queries
CREATE INDEX IF NOT EXISTS draws_date_idx ON draws (draw_date DESC);
-- Speed up JSONB queries on raw_data if needed later
CREATE INDEX IF NOT EXISTS draws_raw_gin  ON draws USING GIN (raw_data);


-- Heartbeat log — one row per cron / refresh run so silent failures are visible.
-- Query the newest row (or GET /api/status) to see when data last updated.
CREATE TABLE IF NOT EXISTS sync_runs (
  id          BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ran_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- when this run executed
  status      TEXT        NOT NULL,                -- updated | no_change | ircc_error | db_error | ...
  ircc_count  INTEGER,                             -- valid draws seen in the IRCC feed
  db_count    INTEGER,                             -- draws already in the DB
  inserted    INTEGER,                             -- new draws written this run
  error       TEXT                                 -- error detail, if any
);

-- Speed up "latest run" lookups
CREATE INDEX IF NOT EXISTS sync_runs_ran_at_idx ON sync_runs (ran_at DESC);
