-- Run this once in the Supabase SQL Editor before first deploy.
-- Table Editor → SQL Editor → paste → Run

CREATE TABLE IF NOT EXISTS draws (
  draw_number   INTEGER     PRIMARY KEY,          -- IRCC sequential draw # (e.g. 308)
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
