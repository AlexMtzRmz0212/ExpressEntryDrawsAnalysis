import { useState, useEffect, useCallback } from 'react';
import { getDrawType, getDrawSubcategory, cat } from '../utils/categories';
import { fmtDate, fmtNum } from '../utils/format';

// How often an already-open tab silently re-checks the DB for new data.
const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 min

function enrich(d) {
  const type = getDrawType(d.draw_name);
  const { label, color } = cat(type);
  const subcategory = getDrawSubcategory(d.draw_name);
  return {
    ...d,
    type,
    typeLabel: label,
    color,
    subcategory,
    dateLabel: fmtDate(d.draw_date),
    invLabel: fmtNum(d.invitations),
  };
}

export function useDraws() {
  const [draws, setDraws] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null); // { last_sync, manual_check }

  const fetchDraws = useCallback(async () => {
    const r = await fetch('/api/draws');
    if (!r.ok) throw new Error(`API returned ${r.status}`);
    const data = await r.json();
    const enriched = data
      .map(enrich)
      .sort((a, b) => new Date(a.draw_date) - new Date(b.draw_date));
    setDraws(enriched);
  }, []);

  // Heartbeat + button-cooldown state. Non-critical: a failure here must never
  // surface the full-page error screen, so it's swallowed.
  const fetchStatus = useCallback(async () => {
    try {
      const r = await fetch('/api/status');
      if (r.ok) setStatus(await r.json());
    } catch {
      /* status is best-effort */
    }
  }, []);

  // `silent` background refreshes (interval / tab refocus / post-button) keep the
  // current UI on failure instead of blowing it away — only the initial load
  // surfaces a hard error.
  const refetch = useCallback(
    async ({ silent = false } = {}) => {
      try {
        await Promise.all([fetchDraws(), fetchStatus()]);
        setError(null);
      } catch (err) {
        if (!silent) setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [fetchDraws, fetchStatus],
  );

  useEffect(() => {
    refetch();

    const id = setInterval(() => refetch({ silent: true }), REFRESH_INTERVAL);
    const onVisible = () => {
      if (document.visibilityState === 'visible') refetch({ silent: true });
    };
    document.addEventListener('visibilitychange', onVisible);

    return () => {
      clearInterval(id);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [refetch]);

  return { draws, loading, error, status, refetch };
}
