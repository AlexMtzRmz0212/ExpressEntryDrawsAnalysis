import { useState, useMemo } from 'react';
import { cat } from '../../utils/categories';

const TYPES = ['General', 'CEC', 'PNP', 'French', 'Healthcare', 'Education', 'Trades', 'Agriculture'];

export default function ScoreChecker({ draws }) {
  const [input, setInput] = useState('');

  const result = useMemo(() => {
    const sc = parseInt(input.trim(), 10);
    if (!input.trim() || isNaN(sc)) return null;

    const core = draws.filter(d => d.type === 'General' || d.type === 'CEC').slice(-8);
    const wins = core.filter(d => sc >= d.crs_cutoff).length;
    const lastCore = core[core.length - 1];
    const lastCut = lastCore?.crs_cutoff ?? 0;
    const gap = sc - lastCut;

    const chips = TYPES.map(t => {
      const list = draws.filter(d => d.type === t);
      if (!list.length) return null;
      const last = list[list.length - 1];
      const ok = sc >= last.crs_cutoff;
      return { label: `${cat(t).label} ${last.crs_cutoff}`, ok };
    }).filter(Boolean);

    let verdict, verdictColor;
    if (wins >= 6)      { verdict = 'Strong — you clear most core draws';        verdictColor = '#7ed6a8'; }
    else if (wins >= 2) { verdict = 'Competitive — borderline on core draws';    verdictColor = '#f0c674'; }
    else                { verdict = 'Below recent core cutoffs';                  verdictColor = '#e89b87'; }

    const detail = `You would have been invited in ${wins} of the last ${core.length} core (General/CEC) draws. That is ${gap >= 0 ? '+' + gap : gap} vs. the latest core cutoff of ${lastCut}.`;

    return { verdict, verdictColor, detail, chips };
  }, [input, draws]);

  return (
    <section className="score-grid" style={{
      background: '#16223d', color: '#fff', borderRadius: 12, padding: '24px 26px', marginTop: 14,
    }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Check your CRS score</h2>
        <p style={{ margin: '8px 0 16px', fontSize: 13.5, color: '#9fb0d4', lineHeight: 1.5 }}>
          Enter your score to see which recent draws would have invited you.
        </p>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            inputMode="numeric"
            placeholder="e.g. 515"
            style={{
              width: 130, fontFamily: "'Spline Sans Mono',monospace", fontSize: 22, fontWeight: 600,
              padding: '11px 14px', borderRadius: 9, border: '1.5px solid #2f3d5e',
              background: '#0f1830', color: '#fff',
            }}
          />
          <span style={{ fontSize: 13, color: '#9fb0d4' }}>CRS points</span>
        </div>
      </div>

      <div style={{ background: '#0f1830', border: '1px solid #2f3d5e', borderRadius: 10, padding: '18px 20px', minHeight: 120 }}>
        {result ? (
          <>
            <div style={{ fontSize: 14.5, fontWeight: 600, color: result.verdictColor, marginBottom: 4 }}>{result.verdict}</div>
            <div style={{ fontSize: 13, color: '#9fb0d4', lineHeight: 1.5 }}>{result.detail}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 13 }}>
              {result.chips.map((c, i) => (
                <span key={i} style={{
                  fontSize: 11.5, fontWeight: 600, padding: '4px 10px', borderRadius: 999,
                  background: c.ok ? 'rgba(126,214,168,.15)' : 'rgba(255,255,255,.04)',
                  color: c.ok ? '#7ed6a8' : '#9fb0d4',
                  border: `1px solid ${c.ok ? 'rgba(126,214,168,.4)' : '#2f3d5e'}`,
                }}>
                  {c.label}
                </span>
              ))}
            </div>
          </>
        ) : (
          <div style={{ fontSize: 13.5, color: '#6b7187' }}>Enter a score to see your standing.</div>
        )}
      </div>
    </section>
  );
}
