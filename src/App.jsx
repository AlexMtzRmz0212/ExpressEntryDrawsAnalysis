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

export default function App() {
  const [tab, setTab] = useState('latest');
  const [glossaryOpen, setGlossaryOpen] = useState(false);
  const { draws, loading, error } = useDraws();

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
        <Header updatedAt={updatedAt} loading={loading} onGlossary={() => setGlossaryOpen(true)} />
        <TabNav tab={tab} setTab={setTab} />

        {loading ? (
          <div style={{ marginTop: 32, color: '#8a8f9e', fontSize: 14 }}>Loading draw data…</div>
        ) : (
          <>
            {tab === 'latest'     && <Latest draws={draws} />}
            {tab === 'crs'        && <CRS draws={draws} />}
            {tab === 'cadence'    && <Cadence draws={draws} />}
            {tab === 'prediction' && <Predictions draws={draws} />}
            {tab === 'table'      && <DrawsTable draws={draws} />}
          </>
        )}

        <footer style={{ marginTop: 26, fontSize: 12, color: '#9a9eaa', textAlign: 'center', lineHeight: 1.6 }}>
          Data sourced from the live IRCC feed · Not affiliated with IRCC or the Government of Canada
          <div style={{ marginTop: 6 }}>
            Built by{' '}
            <a
              href="https://alex.bittobyte.qzz.io"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#5b6172', fontWeight: 600, textDecoration: 'underline' }}
            >
              BitToByte
            </a>
            {' '}· let's connect
          </div>
        </footer>
      </div>

      <Glossary open={glossaryOpen} onClose={() => setGlossaryOpen(false)} />
    </div>
  );
}
