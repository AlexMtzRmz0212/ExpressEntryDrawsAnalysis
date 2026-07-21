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


-- ---------------------------------------------------------------------------
-- Email notifications (Module: subscribe to new draws)
-- ---------------------------------------------------------------------------

-- Double opt-in mailing list. Deliberately minimal: no name, no CRS score, no
-- country. The less personal data stored, the less there is to disclose, secure,
-- and delete. consent_ip / consent_user_agent exist only as proof of express
-- consent under CASL and are deleted together with the row.
CREATE TABLE IF NOT EXISTS subscribers (
  id                 BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email              TEXT        NOT NULL UNIQUE,            -- stored lowercased + trimmed
  status             TEXT        NOT NULL DEFAULT 'pending', -- pending | confirmed | unsubscribed
  token              TEXT        NOT NULL UNIQUE,            -- opaque; used for confirm AND unsubscribe
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  confirmed_at       TIMESTAMPTZ,
  unsubscribed_at    TIMESTAMPTZ,
  consent_ip         TEXT,                                   -- CASL proof of consent
  consent_user_agent TEXT,
  last_sent_at       TIMESTAMPTZ,
  bounce_count       INTEGER     NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS subscribers_status_idx     ON subscribers (status);
CREATE INDEX IF NOT EXISTS subscribers_created_at_idx ON subscribers (created_at DESC);

-- No policies are defined, so the anon/public key can read nothing. All access
-- goes through the service key in lib/db.py, which bypasses RLS.
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;


-- Outbox: one row per draw that has been handled by the notifier. Sending is
-- driven by "which draws are in draws but not here?" rather than inline in the
-- refresh path, because three different code paths insert draws (/api/cron,
-- /api/check, /api/refresh) and any of them could race. Inserting the row is
-- the claim; the UNIQUE primary key is what makes a double send impossible.
CREATE TABLE IF NOT EXISTS draw_notifications (
  draw_number TEXT        PRIMARY KEY REFERENCES draws(draw_number) ON DELETE CASCADE,
  claimed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sent_at     TIMESTAMPTZ,
  recipients  INTEGER     NOT NULL DEFAULT 0,
  status      TEXT        NOT NULL DEFAULT 'sending',  -- sending | sent | skipped_backfill | failed
  error       TEXT
);

-- One-time backfill guard: mark every draw that already exists as handled, so
-- the first deploy does not email the entire historical archive. Safe to re-run.
INSERT INTO draw_notifications (draw_number, status, sent_at)
SELECT draw_number, 'skipped_backfill', NOW() FROM draws
ON CONFLICT (draw_number) DO NOTHING;
