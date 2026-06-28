import TrendChart from '../overview/TrendChart';
import ScoreChecker from '../overview/ScoreChecker';
import CategoryOutlook from '../predictions/CategoryOutlook';

export default function CRS({ draws }) {
  return (
    <div>
      <TrendChart draws={draws} />
      <ScoreChecker draws={draws} />
      <CategoryOutlook draws={draws} />
    </div>
  );
}
