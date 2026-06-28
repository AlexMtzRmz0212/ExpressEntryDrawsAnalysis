import { useMemo } from 'react';
import { computeGaps } from '../../utils/stats';

export default function DrawCadenceStat({ draws }) {
  const avgGap = useMemo(() => {
    const gaps = computeGaps(draws).map(g => g.days);
    return gaps.length ? Math.round(gaps.reduce((a, b) => a + b, 0) / gaps.length) : 0;
  }, [draws]);

  return (
    <div style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: 20 }}>
      <div style={{ fontSize: 11.5, letterSpacing: '.1em', textTransform: 'uppercase', color: '#8a8f9e', fontWeight: 600 }}>
        Draw cadence
      </div>
      <div style={{ fontSize: 34, fontWeight: 800, fontFamily: "'Spline Sans Mono',monospace", marginTop: 8, letterSpacing: '-.02em' }}>
        {String(avgGap)}
        <span style={{ fontSize: 16, color: '#8a8f9e' }}>d</span>
      </div>
      <div style={{ fontSize: 12.5, color: '#5b6172', marginTop: 6 }}>avg between draws</div>
    </div>
  );
}
