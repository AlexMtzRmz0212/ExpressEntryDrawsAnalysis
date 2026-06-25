import ForecastCard from './ForecastCard';
import CategoryOutlook from './CategoryOutlook';
import { computePrediction } from '../../utils/stats';
import { useMemo } from 'react';

export default function Predictions({ draws }) {
  const pred = useMemo(() => computePrediction(draws), [draws]);

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 14, marginTop: 22 }}>
        <ForecastCard draws={draws} />

        <section style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: 24 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>How this is computed</h2>
          <ul style={{ margin: '14px 0 0', paddingLeft: 18, fontSize: 13.5, lineHeight: 1.7, color: '#42485a' }}>
            <li><strong>Cutoff:</strong> least-squares trend on the last {pred?.window ?? 8} core draws.</li>
            <li><strong>Date:</strong> last core draw + average inter-draw gap.</li>
            <li><strong>Size:</strong> mean invitations of recent core rounds.</li>
            <li><strong>Band &amp; confidence:</strong> derived from residual spread around the trend.</li>
          </ul>
          <div style={{ marginTop: 18, paddingTop: 16, borderTop: '1px solid #eceae3', fontSize: 12.5, color: '#8a8f9e', lineHeight: 1.6 }}>
            Estimates recompute automatically each time the live feed refreshes. Not affiliated with IRCC; for guidance only.
          </div>
        </section>
      </div>

      <CategoryOutlook draws={draws} />
    </div>
  );
}
