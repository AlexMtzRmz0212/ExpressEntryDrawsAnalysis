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
      <div className="side-grid">
        <CategoryBars draws={draws} />
        <DrawRhythm draws={draws} />
      </div>
      <ScoreChecker draws={draws} />
    </div>
  );
}
