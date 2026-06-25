import { useMemo } from 'react';
import { fmtShort } from '../../utils/format';
import { cat } from '../../utils/categories';

const OUTLOOK_TYPES = ['General', 'CEC', 'PNP', 'French', 'Healthcare', 'Education'];

export default function CategoryOutlook({ draws }) {
  const outlook = useMemo(() => {
    return OUTLOOK_TYPES.map(type => {
      const list = draws.filter(d => d.type === type);
      if (!list.length) return null;
      const last = list[list.length - 1];
      let trend = '→', trendColor = '#8a8f9e';
      if (list.length >= 2) {
        const prev = list[list.length - 2];
        const dd = last.crs_cutoff - prev.crs_cutoff;
        if (dd > 2)       { trend = `▲ ${dd}`;          trendColor = '#c8362b'; }
        else if (dd < -2) { trend = `▼ ${Math.abs(dd)}`; trendColor = '#2f8f6b'; }
      }
      return { type, label: cat(type).label, color: cat(type).color, crs: last.crs_cutoff, trend, trendColor, dateLabel: fmtShort(last.draw_date) };
    }).filter(Boolean);
  }, [draws]);

  return (
    <section style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: 24, marginTop: 14 }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 16, fontWeight: 700 }}>Category outlook</h2>
      <p style={{ margin: '0 0 16px', fontSize: 13, color: '#5b6172' }}>Most recent cutoff per stream, with its short-term direction.</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: 12 }}>
        {outlook.map(o => (
          <div key={o.type} style={{ border: '1px solid #eceae3', borderRadius: 10, padding: '15px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 9, height: 9, borderRadius: '50%', background: o.color, display: 'inline-block' }} />
              <span style={{ fontSize: 13, fontWeight: 600 }}>{o.label}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: 12 }}>
              <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Spline Sans Mono',monospace" }}>{o.crs}</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: o.trendColor }}>{o.trend}</div>
            </div>
            <div style={{ fontSize: 11.5, color: '#8a8f9e', marginTop: 4 }}>last round · {o.dateLabel}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
