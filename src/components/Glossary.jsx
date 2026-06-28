const TERMS = [
  { term: 'CRS',    def: 'Comprehensive Ranking System — the points-based score used to rank Express Entry candidates.' },
  { term: 'ITA',    def: 'Invitation to Apply — issued by IRCC to top-ranked candidates to apply for permanent residence.' },
  { term: 'Cutoff', def: 'The minimum CRS score required to receive an ITA in a given draw round.' },
  { term: 'Draw',   def: 'A selection round where IRCC issues ITAs to candidates above the cutoff score.' },
  { term: 'EE',     def: 'Express Entry — the online management system for Canada\'s skilled worker immigration streams.' },
  { term: 'CEC',    def: 'Canadian Experience Class — a stream for workers with at least one year of Canadian work experience.' },
  { term: 'PNP',    def: 'Provincial Nominee Program — provincial programs that can nominate candidates, adding 600 CRS points.' },
  { term: 'FSW',    def: 'Federal Skilled Worker — a stream for skilled workers with foreign work experience.' },
  { term: 'FST',    def: 'Federal Skilled Trades — a stream for workers in eligible skilled trade occupations.' },
  { term: 'IRCC',   def: 'Immigration, Refugees and Citizenship Canada — the federal department managing immigration.' },
  { term: 'EOI',    def: 'Expression of Interest — a candidate profile submitted to the Express Entry pool.' },
  { term: 'NOC',    def: 'National Occupational Classification — Canada\'s system for classifying and describing occupations.' },
  { term: 'PR',     def: 'Permanent Residence — the immigration status granted after a successful application.' },
];

export default function Glossary({ open, onClose }) {
  if (!open) return null;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(16,22,40,.55)',
        zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '20px 16px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#fff', borderRadius: 14, width: '100%', maxWidth: 560,
          maxHeight: '80vh', display: 'flex', flexDirection: 'column',
          boxShadow: '0 8px 40px rgba(16,22,40,.22)',
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '20px 24px 16px', borderBottom: '1px solid #e2ded3', flexShrink: 0,
        }}>
          <div>
            <div style={{ fontSize: 11, letterSpacing: '.14em', textTransform: 'uppercase', color: '#c8362b', fontWeight: 700 }}>
              Express Entry
            </div>
            <h2 style={{ margin: '2px 0 0', fontSize: 20, fontWeight: 800, letterSpacing: '-.02em' }}>Glossary</h2>
          </div>
          <button
            onClick={onClose}
            style={{
              border: 'none', background: '#f0ede6', borderRadius: 8,
              width: 32, height: 32, cursor: 'pointer', fontSize: 18, lineHeight: 1,
              color: '#5b6172', display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            ×
          </button>
        </div>

        {/* Term list */}
        <div style={{ overflowY: 'auto', padding: '8px 0 12px' }}>
          {TERMS.map(({ term, def }) => (
            <div
              key={term}
              style={{
                display: 'flex', gap: 16, alignItems: 'flex-start',
                padding: '11px 24px', borderBottom: '1px solid #f0ede6',
              }}
            >
              <div style={{
                flexShrink: 0, minWidth: 56,
                fontFamily: "'Spline Sans Mono',monospace", fontSize: 13, fontWeight: 700,
                color: '#16223d', paddingTop: 1,
              }}>
                {term}
              </div>
              <div style={{ fontSize: 13.5, color: '#42485a', lineHeight: 1.55 }}>{def}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
