import { useMemo } from 'react';
import { fmtNum } from '../../utils/format';

function StatCard({ label, value, sub }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: 20 }}>
      <div style={{ fontSize: 11.5, letterSpacing: '.1em', textTransform: 'uppercase', color: '#8a8f9e', fontWeight: 600 }}>
        {label}
      </div>
      <div style={{ fontSize: 34, fontWeight: 800, fontFamily: "'Spline Sans Mono',monospace", marginTop: 8, letterSpacing: '-.02em' }}>
        {value}
      </div>
      <div style={{ fontSize: 12.5, color: '#5b6172', marginTop: 6 }}>{sub}</div>
    </div>
  );
}

// Aggregate, all-category year-to-date figures — the "overall" historical read.
// Category-specific versions of these live on the Latest tab.
export default function HistoryStats({ draws }) {
  const stats = useMemo(() => {
    if (!draws.length) return null;
    const year = draws[draws.length - 1].draw_date.slice(0, 4);
    const thisYear = draws.filter(d => d.draw_date.slice(0, 4) === year);

    const rounds = thisYear.length;
    const itas = thisYear.reduce((a, d) => a + d.invitations, 0);

    // Core (General/CEC) avoids the 600-point PNP-nomination distortion;
    // fall back to every round this year if there were no core rounds yet.
    const core = thisYear.filter(d => d.type === 'General' || d.type === 'CEC');
    const lowSet = core.length ? core : thisYear;
    const lowest = lowSet.length ? Math.min(...lowSet.map(d => d.crs_cutoff)) : null;

    return { year, rounds, itas, lowest, lowestCore: core.length > 0 };
  }, [draws]);

  if (!stats) return null;

  return (
    <>
      <StatCard label={`Rounds in ${stats.year}`} value={String(stats.rounds)} sub="all draws year-to-date" />
      <StatCard label={`Invitations in ${stats.year}`} value={fmtNum(stats.itas)} sub="ITAs issued year-to-date" />
      <StatCard label={`Lowest CRS in ${stats.year}`} value={stats.lowest ?? '—'} sub={stats.lowestCore ? 'General / CEC rounds' : 'all rounds'} />
    </>
  );
}
