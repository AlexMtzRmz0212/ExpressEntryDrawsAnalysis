import { useState } from 'react';
import { useDraws } from './hooks/useDraws';
import { fmtDate } from './utils/format';
import Header from './components/Header';
import TabNav from './components/TabNav';
import Overview from './components/overview/Overview';
import Predictions from './components/predictions/Predictions';
import DrawsTable from './components/table/DrawsTable';

export default function App() {
  const [tab, setTab] = useState('overview');
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
        <Header updatedAt={updatedAt} loading={loading} />
        <TabNav tab={tab} setTab={setTab} />

        {loading ? (
          <div style={{ marginTop: 32, color: '#8a8f9e', fontSize: 14 }}>Loading draw data…</div>
        ) : (
          <>
            {tab === 'overview' && <Overview draws={draws} />}
            {tab === 'predict'  && <Predictions draws={draws} />}
            {tab === 'table'    && <DrawsTable draws={draws} />}
          </>
        )}

        <footer style={{ marginTop: 26, fontSize: 12, color: '#9a9eaa', textAlign: 'center', lineHeight: 1.6 }}>
          Data sourced from the live IRCC feed · Not affiliated with IRCC or the Government of Canada
        </footer>
      </div>
    </div>
  );
}
