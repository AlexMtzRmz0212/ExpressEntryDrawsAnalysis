import { useState, useMemo } from 'react';
import { fmtNum } from '../../utils/format';
import { cat } from '../../utils/categories';

export default function CategoryBars({ draws }) {
  const years = useMemo(() => {
    const set = new Set(draws.map(d => d.draw_date.slice(0, 4)));
    return [...set].sort();
  }, [draws]);

  const [catYear, setCatYear] = useState('');
  const activeYear = years.includes(catYear) ? catYear : (years[years.length - 1] ?? '');

  const bars = useMemo(() => {
    const subset = draws.filter(d => d.draw_date.slice(0, 4) === activeYear);
    const byCat = {};
    subset.forEach(d => { byCat[d.type] = (byCat[d.type] ?? 0) + d.invitations; });
    const entries = Object.entries(byCat).sort((a, b) => b[1] - a[1]);
    const max = entries[0]?.[1] ?? 1;
    return entries.map(([type, val]) => ({
      label: cat(type).label,
      color: cat(type).color,
      valLabel: fmtNum(val),
      width: (val / max * 100) + '%',
    }));
  }, [draws, activeYear]);

  return (
    <section style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: '22px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
        <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>Invitations by category</h2>
        <div style={{ display: 'flex', gap: 4, background: '#f1efe9', padding: 3, borderRadius: 8 }}>
          {years.map(y => (
            <button key={y} onClick={() => setCatYear(y)} style={{
              border: 'none', cursor: 'pointer',
              fontFamily: "'Spline Sans Mono',monospace", fontSize: 12.5, fontWeight: 600,
              padding: '5px 12px', borderRadius: 6,
              background: activeYear === y ? '#16223d' : 'transparent',
              color: activeYear === y ? '#fff' : '#5b6172',
            }}>
              {y}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 11 }}>
        {bars.map(b => (
          <div key={b.label}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, marginBottom: 5 }}>
              <span style={{ fontWeight: 600 }}>{b.label}</span>
              <span style={{ fontFamily: "'Spline Sans Mono',monospace", color: '#5b6172' }}>{b.valLabel}</span>
            </div>
            <div style={{ height: 10, background: '#f1efe9', borderRadius: 999, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: b.width, background: b.color, borderRadius: 999 }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
