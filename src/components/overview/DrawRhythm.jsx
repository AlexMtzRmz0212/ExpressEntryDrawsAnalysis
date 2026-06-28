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

  const visible = gaps.slice(-80);
  const n = visible.length;

  return (
    <section style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: '22px 24px' }}>
      <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>Draw rhythm</h2>
      <p style={{ margin: '4px 0 0', fontSize: 13, color: '#5b6172' }}>Days between consecutive draws</p>

      {n > 0 && (
        <svg
          viewBox={`0 0 ${n} 100`}
          preserveAspectRatio="none"
          aria-hidden="true"
          style={{ width: '100%', height: 96, display: 'block', marginTop: 18 }}
        >
          {visible.map((g, i) => {
            const h = Math.max(3, 8 + (g.days / gapMax) * 92);
            return (
              <rect
                key={i}
                x={i + 0.08}
                y={100 - h}
                width={0.84}
                height={h}
                fill={g.days <= avgGap ? '#3a6ea8' : '#c08a2d'}
                rx={0.25}
              >
                <title>{g.days} days · before #{g.draw.draw_number}</title>
              </rect>
            );
          })}
        </svg>
      )}

      <div style={{ display: 'flex', gap: 14, marginTop: 18, paddingTop: 16, borderTop: '1px solid #eceae3' }}>
        {[
          { val: avgGap, label: 'Average' },
          { val: minGap, label: 'Shortest' },
          { val: maxGap, label: 'Longest' },
        ].map(({ val, label }) => (
          <div key={label} style={{ flex: 1, minWidth: 0 }}>
            <div className="rhythm-stat-val">{val}d</div>
            <div style={{ fontSize: 11.5, color: '#8a8f9e', textTransform: 'uppercase', letterSpacing: '.08em', marginTop: 2 }}>{label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
