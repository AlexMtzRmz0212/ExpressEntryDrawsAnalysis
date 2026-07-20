import DrawCadenceStat from './DrawCadenceStat';
import HistoryStats from './HistoryStats';
import DrawRhythm from '../overview/DrawRhythm';
import CategoryBars from '../overview/CategoryBars';

export default function Cadence({ draws }) {
  return (
    <div>
      <div style={{ marginTop: 22, display: 'grid', gap: 14, gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <DrawCadenceStat draws={draws} />
        <HistoryStats draws={draws} />
      </div>
      <DrawRhythm draws={draws} />
      <div style={{ marginTop: 14 }}>
        <CategoryBars draws={draws} />
      </div>
    </div>
  );
}
