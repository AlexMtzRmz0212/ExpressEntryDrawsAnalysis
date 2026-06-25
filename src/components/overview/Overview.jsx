import HeroStats from './HeroStats';
import TrendChart from './TrendChart';
import CategoryBars from './CategoryBars';
import DrawRhythm from './DrawRhythm';
import ScoreChecker from './ScoreChecker';

export default function Overview({ draws }) {
  return (
    <div>
      <HeroStats draws={draws} />
      <TrendChart draws={draws} />
      <div style={{ display: 'grid', gridTemplateColumns: '1.35fr 1fr', gap: 14, marginTop: 14 }}>
        <CategoryBars draws={draws} />
        <DrawRhythm draws={draws} />
      </div>
      <ScoreChecker draws={draws} />
    </div>
  );
}
