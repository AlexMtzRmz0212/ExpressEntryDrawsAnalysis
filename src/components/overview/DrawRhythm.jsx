import { useMemo } from 'react';
import { computeGaps } from '../../utils/stats';

export default function DrawRhythm({ draws }) {
  const { gaps, avgGap, minGap, maxGap, gapMax } = useMemo(() => {
    const gaps = computeGaps(draws);
    const vals = gaps.map(g => g.days);
    if (!vals.length) return { gaps: [], avgGap: 0, minGap: 0, maxGap: 0, gapMax: 1 };
    const avgGap = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
    return { gaps, avgGap, minGap: Math.min(...vals), maxGap: Math.max(...vals), gapMax: Math.max(...vals) };
  }, [draws]);

  return (
    <section style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: '22px 24px' }}>
      <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>Draw rhythm</h2>
      <p style={{ margin: '4px 0 0', fontSize: 13, color: '#5b6172' }}>Days between consecutive draws</p>

      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 96, marginTop: 18, overflow: 'hidden' }}>
        {gaps.slice(-80).map((g, i) => (
          <div key={i} title={`${g.days} days · before #${g.draw.draw_number}`} style={{
            flex: 1,
            minWidth: 0,
            height: (8 + (g.days / gapMax) * 88) + 'px',
            background: g.days <= avgGap ? '#3a6ea8' : '#c08a2d',
            borderRadius: '3px 3px 0 0',
            minHeight: 3,
          }} />
        ))}
      </div>

      <div style={{ display: 'flex', gap: 14, marginTop: 18, paddingTop: 16, borderTop: '1px solid #eceae3' }}>
        {[
          { val: avgGap, label: 'Average' },
          { val: minGap, label: 'Shortest' },
          { val: maxGap, label: 'Longest' },
        ].map(({ val, label }) => (
          <div key={label} style={{ flex: 1 }}>
            <div style={{ fontSize: 26, fontWeight: 800, fontFamily: "'Spline Sans Mono',monospace" }}>{val}d</div>
            <div style={{ fontSize: 11.5, color: '#8a8f9e', textTransform: 'uppercase', letterSpacing: '.08em', marginTop: 2 }}>{label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
