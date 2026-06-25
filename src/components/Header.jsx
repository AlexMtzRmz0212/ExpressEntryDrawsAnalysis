export default function Header({ updatedAt, loading }) {
  return (
    <header style={{
      display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between',
      gap: 24, padding: '30px 0 22px', borderBottom: '2px solid #16223d', flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{
          width: 44, height: 44, background: '#16223d', borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <div style={{ width: 20, height: 20, border: '2.5px solid #fff', borderRadius: '50%', position: 'relative' }}>
            <div style={{ position: 'absolute', top: 3, right: 3, width: 8, height: 8, background: '#c8362b', borderRadius: '50%' }} />
          </div>
        </div>
        <div>
          <div style={{ fontSize: 12, letterSpacing: '.16em', textTransform: 'uppercase', color: '#c8362b', fontWeight: 700 }}>
            Express Entry · Canada
          </div>
          <h1 style={{ margin: '2px 0 0', fontSize: 25, fontWeight: 800, letterSpacing: '-.02em' }}>
            Draws Intelligence
          </h1>
        </div>
      </div>

      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, padding: '9px 14px',
        background: '#fff', border: '1px solid #e2ded3', borderRadius: 999,
        fontSize: 12.5, fontFamily: "'Spline Sans Mono',monospace",
      }}>
        <span className="pulse-dot" style={{ width: 8, height: 8, borderRadius: '50%', background: '#2f8f6b', display: 'inline-block' }} />
        <span style={{ color: '#5b6172' }}>Live feed</span>
        <span style={{ color: '#16223d', fontWeight: 500 }}>
          · updated {loading ? '…' : updatedAt}
        </span>
      </div>
    </header>
  );
}
