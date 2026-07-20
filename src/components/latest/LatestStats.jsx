import { useMemo } from 'react';
import { fmtNum, daysBetween } from '../../utils/format';

function StatCard({ label, value, unit, sub }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: 20 }}>
      <div style={{ fontSize: 11.5, letterSpacing: '.1em', textTransform: 'uppercase', color: '#8a8f9e', fontWeight: 600 }}>
        {label}
      </div>
      <div style={{ fontSize: 34, fontWeight: 800, fontFamily: "'Spline Sans Mono',monospace", marginTop: 8, letterSpacing: '-.02em' }}>
        {value}
        {unit && <span style={{ fontSize: 16, color: '#8a8f9e' }}>{unit}</span>}
      </div>
      <div style={{ fontSize: 12.5, color: '#5b6172', marginTop: 6 }}>{sub}</div>
    </div>
  );
}

// Stats scoped to the LATEST draw's own category — "how has THIS stream done
// this year". Aggregate all-category year-to-date figures live on the History tab.
export default function LatestStats({ draws }) {
  const stats = useMemo(() => {
    if (!draws.length) return null;
    const latest = draws[draws.length - 1];
    const year = latest.draw_date.slice(0, 4);
    const sameCat = draws.filter(d => d.type === latest.type && d.draw_date.slice(0, 4) === year);

    const daysSince = daysBetween(latest.draw_date, new Date());
    const rounds = sameCat.length;
    const itas = sameCat.reduce((a, d) => a + d.invitations, 0);
    const lowest = sameCat.length ? Math.min(...sameCat.map(d => d.crs_cutoff)) : null;

    return { year, typeLabel: latest.typeLabel, daysSince, rounds, itas, lowest };
  }, [draws]);

  if (!stats) return null;

  const { year, typeLabel } = stats;

  return (
    <div className="latest-stats-grid" style={{ marginTop: 14, display: 'grid', gap: 14, gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
      <StatCard label="Days since last draw" value={String(stats.daysSince)} unit="d" sub="since the most recent round" />
      <StatCard label={`${typeLabel} rounds`} value={String(stats.rounds)} sub={`in ${year}, this category`} />
      <StatCard label={`${typeLabel} invitations`} value={fmtNum(stats.itas)} sub={`ITAs in ${year}, this category`} />
      <StatCard label={`${typeLabel} lowest CRS`} value={stats.lowest ?? '—'} sub={`in ${year}, this category`} />
    </div>
  );
}
