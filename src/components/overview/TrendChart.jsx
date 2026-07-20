import { useState, useMemo } from 'react';
import { fmtDate, fmtNum, fmtMonth } from '../../utils/format';
import { cat } from '../../utils/categories';

const W = 1000, H = 360, padL = 52, padR = 18, padT = 22, padB = 34;

const FILTER_DEFS = [
  { key: 'Core',       label: 'Core',          dot: '#16223d', test: d => d.type === 'General' || d.type === 'CEC' },
  { key: 'All',        label: 'All draws',     dot: '#8a8f9e', test: () => true },
  { key: 'General',    label: 'General',       dot: '#16223d', test: d => d.type === 'General' },
  { key: 'CEC',        label: 'CEC', dot: '#3a6ea8', test: d => d.type === 'CEC' },
  { key: 'PNP',        label: 'Provincial',    dot: '#6d4c91', test: d => d.type === 'PNP' },
  { key: 'French',     label: 'French',        dot: '#c8362b', test: d => d.type === 'French' },
  { key: 'Healthcare', label: 'Healthcare',    dot: '#2f8f6b', test: d => d.type === 'Healthcare' },
];

export default function TrendChart({ draws }) {
  const [filter, setFilter] = useState('Core');
  const [hover, setHover] = useState(null);

  const { points, linePath, areaPath, yTicks, xTicks, subtitle } = useMemo(() => {
    const def = FILTER_DEFS.find(f => f.key === filter) || FILTER_DEFS[0];
    const view = draws.filter(def.test);
    if (!view.length) return { points: [], linePath: '', areaPath: '', yTicks: [], xTicks: [], subtitle: '' };

    const ys = view.map(d => d.crs_cutoff);
    let vmin = Math.min(...ys), vmax = Math.max(...ys);
    const span = Math.max(vmax - vmin, 1), padv = span * 0.12;
    vmin = Math.floor((vmin - padv) / 5) * 5;
    vmax = Math.ceil((vmax + padv) / 5) * 5;

    const xFor = i => view.length <= 1
      ? padL + (W - padL - padR) / 2
      : padL + i * (W - padL - padR) / (view.length - 1);
    const yFor = v => padT + (1 - (v - vmin) / (vmax - vmin)) * (H - padT - padB);
    const baseY = H - padB;

    const points = view.map((d, i) => ({
      ...d,
      cx: xFor(i),
      cy: yFor(d.crs_cutoff),
      dateLabel: fmtDate(d.draw_date),
      invLabel: fmtNum(d.invitations),
      leftPct: (xFor(i) / W * 100) + '%',
      topPct: (yFor(d.crs_cutoff) / H * 100) + '%',
    }));

    const linePath = points.map((p, i) => `${i ? 'L' : 'M'}${p.cx.toFixed(1)} ${p.cy.toFixed(1)}`).join(' ');
    const areaPath = `M${points[0].cx.toFixed(1)} ${baseY} ${points.map(p => `L${p.cx.toFixed(1)} ${p.cy.toFixed(1)}`).join(' ')} L${points[points.length - 1].cx.toFixed(1)} ${baseY} Z`;

    const yTicks = Array.from({ length: 5 }, (_, i) => {
      const v = Math.round(vmin + (vmax - vmin) * i / 4);
      const y = yFor(v);
      return { y, ty: y + 4, label: v };
    });

    const tn = Math.min(6, view.length);
    const xTicks = Array.from({ length: tn }, (_, i) => {
      const idx = tn === 1 ? 0 : Math.round(i * (view.length - 1) / (tn - 1));
      return { x: xFor(idx), label: fmtMonth(view[idx].draw_date) };
    });

    const subtitle =
      filter === 'All'  ? 'Every stream. Note the high Provincial Nominee spikes (CRS includes the 600-point nomination).' :
      filter === 'Core' ? 'General and Canadian Experience Class rounds, the economic mainstream.' :
      cat(filter).label + ' rounds only.';

    return { points, linePath, areaPath, yTicks, xTicks, subtitle };
  }, [draws, filter]);

  const hoverPoint = hover !== null ? points[hover] : null;

  return (
    <section style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: '22px 24px 18px', marginTop: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>CRS cutoff over time</h2>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: '#5b6172' }}>{subtitle}</p>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', maxWidth: '100%', justifyContent: 'flex-start' }}>
          {FILTER_DEFS.map(f => (
            <button key={f.key} onClick={() => { setFilter(f.key); setHover(null); }} style={{
              display: 'flex', alignItems: 'center', gap: 6,
              border: `1px solid ${filter === f.key ? '#16223d' : '#e2ded3'}`,
              cursor: 'pointer', fontFamily: 'inherit', fontSize: 12, fontWeight: 600,
              padding: '5px 11px', borderRadius: 999,
              background: filter === f.key ? '#16223d' : '#fff',
              color: filter === f.key ? '#fff' : '#42485a',
            }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: f.dot, display: 'inline-block' }} />
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ position: 'relative', marginTop: 16 }} onMouseLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Line chart of CRS cutoff over time. ${subtitle}`} style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}>
          {yTicks.map((t, i) => (
            <g key={i}>
              <line x1={padL} y1={t.y} x2={W - padR} y2={t.y} stroke="#eceae3" strokeWidth={1} />
              <text x={padL - 8} y={t.ty} textAnchor="end" fontSize={12} fill="#6b7180" fontFamily="'Spline Sans Mono',monospace">{t.label}</text>
            </g>
          ))}
          {xTicks.map((t, i) => (
            <text key={i} x={t.x} y={H - 8} textAnchor="middle" fontSize={11.5} fill="#6b7180" fontFamily="'Spline Sans Mono',monospace">{t.label}</text>
          ))}
          <path d={areaPath} fill="rgba(22,34,61,0.06)" />
          <path d={linePath} fill="none" stroke="#16223d" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
          {hoverPoint && (
            <line x1={hoverPoint.cx} y1={padT} x2={hoverPoint.cx} y2={H - padB} stroke="#c8362b" strokeWidth={1} strokeDasharray="4 4" />
          )}
          {points.map((p, i) => (
            <g key={p.draw_number}>
              <circle cx={p.cx} cy={p.cy} r={4} fill={p.color} stroke="#fff" strokeWidth={1.5} />
              <circle cx={p.cx} cy={p.cy} r={12} fill="#fff" fillOpacity={0} onMouseEnter={() => setHover(i)} style={{ cursor: 'pointer' }} />
            </g>
          ))}
        </svg>

        {hoverPoint && (
          <div style={{
            position: 'absolute', left: hoverPoint.leftPct, top: hoverPoint.topPct,
            transform: 'translate(-50%, -120%)',
            background: '#16223d', color: '#fff', padding: '10px 13px',
            borderRadius: 8, fontSize: 12.5, pointerEvents: 'none',
            whiteSpace: 'nowrap', boxShadow: '0 8px 24px rgba(22,34,61,.25)', zIndex: 5,
          }}>
            <div style={{ fontWeight: 700, marginBottom: 3 }}>#{hoverPoint.draw_number} · {hoverPoint.typeLabel}</div>
            <div style={{ fontFamily: "'Spline Sans Mono',monospace", color: '#cdd6ea' }}>{hoverPoint.dateLabel}</div>
            <div style={{ display: 'flex', gap: 14, marginTop: 6, fontFamily: "'Spline Sans Mono',monospace" }}>
              <span><span style={{ color: '#9fb0d4' }}>CRS </span>{hoverPoint.crs_cutoff}</span>
              <span><span style={{ color: '#9fb0d4' }}>ITAs </span>{hoverPoint.invLabel}</span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
