import { useState, useEffect } from 'react';
import { fmtRelative, fmtTime } from '../utils/format';

const STALE_MS = 8 * 60 * 60 * 1000; // dot turns amber once a sync is this old

// Dot colour by how long since the last successful sync — makes silent
// scheduler failures visible instead of the page looking healthy forever.
function dotColor(ranAt) {
  if (!ranAt) return '#d98a2b'; // amber — never synced
  const age = Date.now() - new Date(ranAt);
  if (age > 3 * STALE_MS) return '#c8362b'; // red  — > 24h
  if (age > STALE_MS) return '#d98a2b';      // amber — > 8h
  return '#2f8f6b';                          // green — fresh
}

export default function Header({ updatedAt, loading, status, refetch, onGlossary }) {
  const [checking, setChecking] = useState(false);
  const [msg, setMsg] = useState(null);

  // Transient result message auto-clears.
  useEffect(() => {
    if (!msg) return;
    const t = setTimeout(() => setMsg(null), 6000);
    return () => clearTimeout(t);
  }, [msg]);

  const lastSync = status?.last_sync;
  const ranAt = lastSync?.ran_at;
  const manualCheck = status?.manual_check;
  const statusLoaded = !!status;

  // Server is the source of truth for whether the button may fire. Until status
  // loads we keep it disabled; if an older API omits manual_check, default to on.
  const canCheck =
    statusLoaded && (manualCheck ? manualCheck.allowed : true) && !checking;

  const lockNote =
    manualCheck && !manualCheck.allowed
      ? manualCheck.reason === 'updated_today'
        ? 'Updated today'
        : manualCheck.unlock_at
          ? `Back at ${fmtTime(manualCheck.unlock_at)}`
          : 'Checked recently'
      : null;

  async function handleCheck() {
    if (!canCheck) return;
    setChecking(true);
    setMsg(null);
    try {
      const r = await fetch('/api/check', { method: 'POST' });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        setMsg('Check failed — try later');
      } else if (data.allowed === false) {
        setMsg(data.reason === 'updated_today' ? 'Already updated today' : 'Checked recently');
      } else {
        const s = data.result?.status;
        if (s === 'updated') setMsg('New draw added!');
        else if (s === 'no_change') setMsg('No new draw yet');
        else setMsg('Couldn’t reach IRCC — try later');
      }
    } catch {
      setMsg('Check failed — try later');
    } finally {
      setChecking(false);
      refetch?.({ silent: true }); // pull any new draws + refresh the lock state
    }
  }

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

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <button
          onClick={onGlossary}
          style={{
            border: '1px solid #e2ded3', cursor: 'pointer', fontFamily: 'inherit',
            display: 'flex', alignItems: 'center', gap: 6, padding: '9px 14px',
            background: '#fff', borderRadius: 999, fontSize: 12.5, fontWeight: 600,
            color: '#42485a', transition: 'background .15s',
          }}
          onMouseEnter={e => e.currentTarget.style.background = '#f0ede6'}
          onMouseLeave={e => e.currentTarget.style.background = '#fff'}
        >
          <span style={{ fontSize: 14 }}>📖</span> Glossary
        </button>

        <button
          onClick={handleCheck}
          disabled={!canCheck}
          title={lockNote || 'Check IRCC for a new draw right now'}
          style={{
            border: '1px solid #e2ded3', cursor: canCheck ? 'pointer' : 'default',
            fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 6,
            padding: '9px 14px', background: canCheck ? '#16223d' : '#f0ede6',
            color: canCheck ? '#fff' : '#8a8f9e', borderRadius: 999,
            fontSize: 12.5, fontWeight: 600, transition: 'opacity .15s',
            opacity: checking ? 0.7 : 1,
          }}
        >
          <span style={{ fontSize: 14 }}>{checking ? '⏳' : '🔄'}</span>
          {checking ? 'Checking…' : msg || lockNote || 'Check now'}
        </button>

        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, padding: '9px 14px',
          background: '#fff', border: '1px solid #e2ded3', borderRadius: 999,
          fontSize: 12.5, fontFamily: "'Spline Sans Mono',monospace",
        }}>
          <span className="pulse-dot" style={{ width: 8, height: 8, borderRadius: '50%', background: dotColor(ranAt), display: 'inline-block' }} />
          <span style={{ color: '#5b6172' }}>
            Checked {loading && !status ? '…' : fmtRelative(ranAt)}
          </span>
          <span style={{ color: '#16223d', fontWeight: 500 }}>
            · latest draw {loading ? '…' : updatedAt}
          </span>
        </div>
      </div>
    </header>
  );
}
