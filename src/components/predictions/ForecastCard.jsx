import { useMemo } from 'react';
import { fmtNum, fmtShort } from '../../utils/format';
import { computePrediction } from '../../utils/stats';

export default function ForecastCard({ draws }) {
  const pred = useMemo(() => computePrediction(draws), [draws]);
  if (!pred) return null;

  return (
    <section style={{ background: '#16223d', color: '#fff', borderRadius: 12, padding: '26px 28px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ fontSize: 12, letterSpacing: '.12em', textTransform: 'uppercase', color: '#c8362b', fontWeight: 700 }}>
        Forecast · Next core draw
      </div>
      <p style={{ margin: '6px 0 18px', fontSize: 13, color: '#9fb0d4' }}>
        General + Canadian Experience rounds
      </p>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
        <div style={{ fontSize: 62, fontWeight: 800, fontFamily: "'Spline Sans Mono',monospace", lineHeight: .9, letterSpacing: '-.03em' }}>
          {pred.crs}
        </div>
        <div style={{ fontSize: 15, color: '#9fb0d4' }}>± {pred.crsBand} CRS</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginTop: 24 }}>
        {[
          { label: 'Expected window', value: `${fmtShort(pred.lo)} – ${fmtShort(pred.hi)}` },
          { label: 'Est. invitations', value: `~${fmtNum(pred.size)}` },
        ].map(({ label, value }) => (
          <div key={label} style={{ background: 'rgba(255,255,255,.06)', borderRadius: 9, padding: '14px 16px' }}>
            <div style={{ fontSize: 11.5, color: '#9fb0d4', textTransform: 'uppercase', letterSpacing: '.08em' }}>{label}</div>
            <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "'Spline Sans Mono',monospace", marginTop: 5 }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 20 }}>
        <span style={{ fontSize: 12, color: '#9fb0d4' }}>Confidence</span>
        <span style={{ fontSize: 12.5, fontWeight: 700, padding: '4px 12px', borderRadius: 999, background: pred.confColor, color: '#16223d' }}>
          {pred.confidence}
        </span>
      </div>
    </section>
  );
}
