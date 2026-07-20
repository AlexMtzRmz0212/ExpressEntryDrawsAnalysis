import { useState, useMemo } from 'react';
import { fmtDate, fmtNum, fmtMonth } from '../../utils/format';
import { cat } from '../../utils/categories';

const W = 1000, H = 360, padL = 52, padR = 18, padT = 22, padB = 34;

// Preferred chip / series order; any other category present in the data is appended.
const ORDER = ['General', 'CEC', 'PNP', 'French', 'Healthcare', 'Education', 'Trades', 'Agriculture', 'STEM', 'Transport'];

const ms = (dateStr) => new Date(dateStr + 'T00:00:00').getTime();

export default function TrendChart({ draws }) {
  // Default to General + CEC — the economic mainstream ("core") view.
  const [selected, setSelected] = useState(['General', 'CEC']);
  const [mode, setMode] = useState('combined'); // 'combined' = one line | 'series' = one line per category
  const [hover, setHover] = useState(null);      // hovered draw_number

  const categories = useMemo(() => {
    const present = [...new Set(draws.map(d => d.type))];
    return present.slice().sort((a, b) => {
      const ia = ORDER.indexOf(a), ib = ORDER.indexOf(b);
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    });
  }, [draws]);

  const orderTypes = (types) =>
    ORDER.filter(t => types.includes(t)).concat(types.filter(t => !ORDER.includes(t)));

  const toggle = (type) => {
    setHover(null);
    setSelected(prev => prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]);
  };

  const { series, yTicks, xTicks, flatPoints } = useMemo(() => {
    const view = draws.filter(d => selected.includes(d.type));
    if (!view.length) return { series: [], yTicks: [], xTicks: [], flatPoints: [] };

    // Shared Y scale over every selected draw so lines stay comparable.
    const ys = view.map(d => d.crs_cutoff);
    let vmin = Math.min(...ys), vmax = Math.max(...ys);
    const span = Math.max(vmax - vmin, 1), padv = span * 0.12;
    vmin = Math.floor((vmin - padv) / 5) * 5;
    vmax = Math.ceil((vmax + padv) / 5) * 5;
    const yFor = v => padT + (1 - (v - vmin) / (vmax - vmin)) * (H - padT - padB);

    // Shared time-based X scale so category series overlay correctly by date.
    const times = view.map(d => ms(d.draw_date));
    const tMin = Math.min(...times), tMax = Math.max(...times);
    const xFor = t => tMax === tMin
      ? padL + (W - padL - padR) / 2
      : padL + (t - tMin) / (tMax - tMin) * (W - padL - padR);

    const mk = d => {
      const cx = xFor(ms(d.draw_date));
      const cy = yFor(d.crs_cutoff);
      return {
        ...d, cx, cy,
        dateLabel: fmtDate(d.draw_date),
        invLabel: fmtNum(d.invitations),
        leftPct: (cx / W * 100) + '%',
        topPct: (cy / H * 100) + '%',
      };
    };
    const lineOf = pts => pts.map((p, i) => `${i ? 'L' : 'M'}${p.cx.toFixed(1)} ${p.cy.toFixed(1)}`).join(' ');
    const baseY = H - padB;

    let series;
    if (mode === 'series') {
      const groups = {};
      view.forEach(d => { (groups[d.type] ||= []).push(d); });
      series = orderTypes(Object.keys(groups)).map(type => {
        const pts = groups[type].map(mk); // view is already date-sorted
        return { type, color: cat(type).color, label: cat(type).label, points: pts, linePath: lineOf(pts) };
      });
    } else {
      const pts = view.map(mk);
      const areaPath = `M${pts[0].cx.toFixed(1)} ${baseY} ${pts.map(p => `L${p.cx.toFixed(1)} ${p.cy.toFixed(1)}`).join(' ')} L${pts[pts.length - 1].cx.toFixed(1)} ${baseY} Z`;
      series = [{ type: 'combined', color: '#16223d', label: 'Combined', points: pts, linePath: lineOf(pts), areaPath }];
    }

    const yTicks = Array.from({ length: 5 }, (_, i) => {
      const v = Math.round(vmin + (vmax - vmin) * i / 4);
      const y = yFor(v);
      return { y, ty: y + 4, label: v };
    });

    const tn = Math.min(6, Math.max(2, view.length));
    const xTicks = Array.from({ length: tMax === tMin ? 1 : tn }, (_, i) => {
      const t = tMin + (tMax - tMin) * i / (tn - 1);
      return { x: xFor(t), label: fmtMonth(new Date(t).toISOString().slice(0, 10)) };
    });

    const flatPoints = series.flatMap(s => s.points);
    return { series, yTicks, xTicks, flatPoints };
  }, [draws, selected, mode]);

  const hoverPoint = hover !== null ? flatPoints.find(p => p.draw_number === hover) : null;

  return (
    <section style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: '22px 24px 18px', marginTop: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>CRS cutoff over time</h2>
          <div style={{ display: 'inline-flex', gap: 4, background: '#f1efe9', padding: 3, borderRadius: 8, marginTop: 10 }}>
            {[['combined', 'Combined'], ['series', 'By category']].map(([m, label]) => (
              <button key={m} onClick={() => { setMode(m); setHover(null); }} style={{
                border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 12, fontWeight: 600,
                padding: '5px 12px', borderRadius: 6,
                background: mode === m ? '#16223d' : 'transparent',
                color: mode === m ? '#fff' : '#5b6172',
              }}>
                {label}
              </button>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', maxWidth: '100%', justifyContent: 'flex-start' }}>
          {categories.map(type => {
            const on = selected.includes(type);
            const { label, color } = cat(type);
            return (
              <button key={type} onClick={() => toggle(type)} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                border: `1px solid ${on ? '#16223d' : '#e2ded3'}`,
                cursor: 'pointer', fontFamily: 'inherit', fontSize: 12, fontWeight: 600,
                padding: '5px 11px', borderRadius: 999,
                background: on ? '#16223d' : '#fff',
                color: on ? '#fff' : '#42485a',
              }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block', opacity: on ? 1 : 0.55 }} />
                {label}
              </button>
            );
          })}
          <button
            onClick={() => { setHover(null); setSelected(categories.slice()); }}
            style={{ border: '1px solid #e2ded3', cursor: 'pointer', fontFamily: 'inherit', fontSize: 12, fontWeight: 600, padding: '5px 11px', borderRadius: 999, background: '#fff', color: '#5b6172' }}
          >All</button>
          <button
            onClick={() => { setHover(null); setSelected([]); }}
            style={{ border: '1px solid #e2ded3', cursor: 'pointer', fontFamily: 'inherit', fontSize: 12, fontWeight: 600, padding: '5px 11px', borderRadius: 999, background: '#fff', color: '#5b6172' }}
          >Clear</button>
        </div>
      </div>

      {flatPoints.length === 0 ? (
        <div style={{
          marginTop: 16, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
          border: '1px dashed #e2ded3', borderRadius: 10, color: '#8a8f9e', fontSize: 13.5,
        }}>
          Pick at least one category to plot.
        </div>
      ) : (
      <div style={{ position: 'relative', marginTop: 16 }} onMouseLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}>
          {yTicks.map((t, i) => (
            <g key={i}>
              <line x1={padL} y1={t.y} x2={W - padR} y2={t.y} stroke="#eceae3" strokeWidth={1} />
              <text x={padL - 8} y={t.ty} textAnchor="end" fontSize={12} fill="#a3a7b3" fontFamily="'Spline Sans Mono',monospace">{t.label}</text>
            </g>
          ))}
          {xTicks.map((t, i) => (
            <text key={i} x={t.x} y={H - 8} textAnchor="middle" fontSize={11.5} fill="#a3a7b3" fontFamily="'Spline Sans Mono',monospace">{t.label}</text>
          ))}
          {series.map(s => (
            <g key={s.type}>
              {s.areaPath && <path d={s.areaPath} fill="rgba(22,34,61,0.06)" />}
              <path d={s.linePath} fill="none" stroke={s.color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
            </g>
          ))}
          {hoverPoint && (
            <line x1={hoverPoint.cx} y1={padT} x2={hoverPoint.cx} y2={H - padB} stroke="#c8362b" strokeWidth={1} strokeDasharray="4 4" />
          )}
          {flatPoints.map(p => (
            <g key={p.draw_number}>
              <circle cx={p.cx} cy={p.cy} r={4} fill={p.color} stroke="#fff" strokeWidth={1.5} />
              <circle cx={p.cx} cy={p.cy} r={12} fill="#fff" fillOpacity={0} onMouseEnter={() => setHover(p.draw_number)} style={{ cursor: 'pointer' }} />
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
      )}
    </section>
  );
}
