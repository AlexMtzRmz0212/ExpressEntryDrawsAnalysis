import { useState } from 'react';
import { useDraws } from './hooks/useDraws';
import { fmtDate } from './utils/format';
import Header from './components/Header';
import TabNav from './components/TabNav';
import Latest from './components/latest/Latest';
import CRS from './components/crs/CRS';
import Cadence from './components/cadence/Cadence';
import Predictions from './components/predictions/Predictions';
import DrawsTable from './components/table/DrawsTable';
import Glossary from './components/Glossary';
import Legal from './components/Legal';

export default function App() {
  const [tab, setTab] = useState('latest');
  const [glossaryOpen, setGlossaryOpen] = useState(false);
  const [legalOpen, setLegalOpen] = useState(false);
  const { draws, loading, error, status, refetch } = useDraws();

  const latest = draws[draws.length - 1];
  const updatedAt = latest ? fmtDate(latest.draw_date) : '—';

  if (error) {
    return (
      <div style={{ padding: 40, color: '#c8362b', fontFamily: "'Spline Sans Mono',monospace", fontSize: 14 }}>
        Failed to load draw data: {error}
      </div>
    );
  }

  return (
    <div className="app-padding min-h-screen bg-warm-bg">
      <div style={{ maxWidth: 1180, margin: '0 auto' }}>
        <Header
          updatedAt={updatedAt}
          loading={loading}
          status={status}
          refetch={refetch}
          onGlossary={() => setGlossaryOpen(true)}
        />
        <TabNav tab={tab} setTab={setTab} />

        {loading ? (
          <div style={{ marginTop: 32, color: '#5b6172', fontSize: 14 }}>Loading draw data…</div>
        ) : (
          <>
            {tab === 'latest'     && <Latest draws={draws} />}
            {tab === 'crs'        && <CRS draws={draws} />}
            {tab === 'cadence'    && <Cadence draws={draws} />}
            {tab === 'prediction' && <Predictions draws={draws} />}
            {tab === 'table'      && <DrawsTable draws={draws} />}
          </>
        )}

        <footer style={{ marginTop: 26, fontSize: 12, color: '#5b6172', textAlign: 'center', lineHeight: 1.6 }}>
          Data sourced from the live IRCC feed · Not affiliated with IRCC or the Government of Canada
          <div style={{ marginTop: 8, display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => setLegalOpen(true)}
              style={{
                border: 'none', background: 'none', padding: 0, cursor: 'pointer',
                font: 'inherit', color: '#5b6172', textDecoration: 'underline',
              }}
            >
              Privacy Policy
            </button>
            <button
              onClick={() => setLegalOpen(true)}
              style={{
                border: 'none', background: 'none', padding: 0, cursor: 'pointer',
                font: 'inherit', color: '#5b6172', textDecoration: 'underline',
              }}
            >
              Terms of Use
            </button>
          </div>
          <div style={{ marginTop: 6 }}>
            Built by{' '}
            <a
              href="https://alex.bittobyte.qzz.io"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#5b6172', fontWeight: 600, textDecoration: 'underline' }}
            >
              Alex
            </a>
            {' '}· let's connect
          </div>
          <div
            style={{
              marginTop: 10,
              display: 'flex',
              gap: 16,
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}
          >
            {[
              { label: 'BitToByte', href: 'https://bittobyte.qzz.io' },
              { label: 'Portfolio', href: 'https://alex.bittobyte.qzz.io' },
              { label: 'Express Entry', href: 'https://EE.bittobyte.qzz.io' },
              { label: 'AI Checklist', href: 'https://checklist.bittobyte.qzz.io' },
            ].map((l) => (
              <a
                key={l.href}
                href={l.href}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#5b6172', textDecoration: 'none' }}
              >
                {l.label}
              </a>
            ))}
          </div>
        </footer>
      </div>

      <Glossary open={glossaryOpen} onClose={() => setGlossaryOpen(false)} />
      <Legal open={legalOpen} onClose={() => setLegalOpen(false)} />
    </div>
  );
}
