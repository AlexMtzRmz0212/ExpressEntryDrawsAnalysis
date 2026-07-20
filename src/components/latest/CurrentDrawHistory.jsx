import { useMemo } from 'react';
import { fmtNum } from '../../utils/format';

export default function CurrentDrawHistory({ draws }) {
  const { latest, rows } = useMemo(() => {
    if (!draws.length) return { latest: null, rows: [] };
    const latest = draws[draws.length - 1];
    const sameType = draws.filter(d => d.type === latest.type);
    // Most recent first, newest ~4 rounds of the current draw's category.
    const rows = sameType.slice(-4).reverse();
    return { latest, rows };
  }, [draws]);

  if (!latest || rows.length < 2) return null;

  return (
    <section style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: '22px 24px', marginTop: 14 }}>
      <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>Recent {latest.typeLabel} rounds</h2>
      <p style={{ margin: '4px 0 0', fontSize: 13, color: '#5b6172' }}>How the current round compares to the last few of its category</p>

      <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column' }}>
        {rows.map((d, i) => {
          const prev = rows[i + 1];
          const delta = prev ? d.crs_cutoff - prev.crs_cutoff : null;
          const deltaColor = delta === null ? '#8a8f9e' : delta > 0 ? '#c8362b' : delta < 0 ? '#2f8f6b' : '#8a8f9e';
          const isLatest = i === 0;
          return (
            <div key={d.draw_number} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
              padding: '11px 0', borderTop: i ? '1px solid #eceae3' : 'none',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: d.color, flexShrink: 0 }} />
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 13.5, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                    #{d.draw_number}
                    {isLatest && (
                      <span style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase', color: '#c8362b' }}>Latest</span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: '#8a8f9e', fontFamily: "'Spline Sans Mono',monospace" }}>{d.dateLabel}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, fontFamily: "'Spline Sans Mono',monospace" }}>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: 15, fontWeight: 700 }}>{d.crs_cutoff}</span>
                  {delta !== null && (
                    <span style={{ fontSize: 12, fontWeight: 600, color: deltaColor, marginLeft: 6 }}>
                      {delta > 0 ? '+' : ''}{delta}
                    </span>
                  )}
                  <div style={{ fontSize: 10.5, color: '#a3a7b3', textTransform: 'uppercase', letterSpacing: '.06em' }}>CRS</div>
                </div>
                <div style={{ textAlign: 'right', minWidth: 56 }}>
                  <span style={{ fontSize: 15, fontWeight: 700 }}>{fmtNum(d.invitations)}</span>
                  <div style={{ fontSize: 10.5, color: '#a3a7b3', textTransform: 'uppercase', letterSpacing: '.06em' }}>ITAs</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
