import HeroStats from '../overview/HeroStats';
import CategoryBars from '../overview/CategoryBars';

export default function Latest({ draws }) {
  return (
    <div>
      <HeroStats draws={draws} />
      <CategoryBars draws={draws} />
    </div>
  );
}
