import { useMemo } from 'react';
import { fmtNum } from '../../utils/format';

function StatCard({ label, value, unit, sub }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: 20 }}>
      <div style={{ fontSize: 11.5, letterSpacing: '.1em', textTransform: 'uppercase', color: '#6b7180', fontWeight: 600 }}>
        {label}
      </div>
      <div style={{ fontSize: 34, fontWeight: 800, fontFamily: "'Spline Sans Mono',monospace", marginTop: 8, letterSpacing: '-.02em' }}>
        {value}
        {unit && <span style={{ fontSize: 16, color: '#6b7180' }}>{unit}</span>}
      </div>
      <div style={{ fontSize: 12.5, color: '#5b6172', marginTop: 6 }}>{sub}</div>
    </div>
  );
}

export default function HeroStats({ draws }) {
  const { latest, deltaLabel, deltaColor } = useMemo(() => {
    if (!draws.length) return {};
    const latest = draws[draws.length - 1];

    const sameType = draws.filter(d => d.type === latest.type);
    const prior = sameType.length > 1 ? sameType[sameType.length - 2] : null;
    const delta = prior ? latest.crs_cutoff - prior.crs_cutoff : null;
    const deltaLabel = delta === null ? '—' : (delta > 0 ? '+' : '') + delta;
    const deltaColor = delta === null ? '#6b7180' : delta > 0 ? '#c8362b' : delta < 0 ? '#2f8f6b' : '#6b7180';

    return { latest, deltaLabel, deltaColor };
  }, [draws]);

  if (!latest) return null;

  return (
    <div className="hero-grid">
      {/* Latest draw */}
      <div style={{ background: '#16223d', color: '#fff', borderRadius: 12, padding: '22px 24px', position: 'relative', overflow: 'hidden' }}>
        <div style={{ fontSize: 12, letterSpacing: '.12em', textTransform: 'uppercase', color: '#9fb0d4', fontWeight: 600 }}>
          Latest draw · #{latest.draw_number}
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginTop: 10 }}>
          <div style={{ fontSize: 54, fontWeight: 800, fontFamily: "'Spline Sans Mono',monospace", lineHeight: .9, letterSpacing: '-.03em' }}>
            {latest.crs_cutoff}
          </div>
          <div style={{ fontSize: 13, color: '#9fb0d4' }}>CRS cutoff</div>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12.5, fontWeight: 600, padding: '5px 11px', borderRadius: 999, background: latest.color, color: '#fff' }}>
            {latest.typeLabel}
          </span>
          <span style={{ fontSize: 12.5, padding: '5px 11px', borderRadius: 999, background: 'rgba(255,255,255,.1)', fontFamily: "'Spline Sans Mono',monospace" }}>
            {latest.dateLabel}
          </span>
        </div>
      </div>

      <StatCard label="Invitations" value={fmtNum(latest.invitations)} sub="this round" />

      {/* vs prior */}
      <div style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 11.5, letterSpacing: '.1em', textTransform: 'uppercase', color: '#6b7180', fontWeight: 600 }}>
          vs. prior {latest.typeLabel}
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 8 }}>
          <span style={{ fontSize: 34, fontWeight: 800, fontFamily: "'Spline Sans Mono',monospace", color: deltaColor, letterSpacing: '-.02em' }}>
            {deltaLabel}
          </span>
        </div>
        <div style={{ fontSize: 12.5, color: '#5b6172', marginTop: 6 }}>CRS points</div>
      </div>

    </div>
  );
}
