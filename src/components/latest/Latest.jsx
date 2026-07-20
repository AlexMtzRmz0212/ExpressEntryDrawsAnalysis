import HeroStats from '../overview/HeroStats';
import LatestStats from './LatestStats';
import CurrentDrawHistory from './CurrentDrawHistory';

export default function Latest({ draws }) {
  return (
    <div>
      <HeroStats draws={draws} />
      <LatestStats draws={draws} />
      <CurrentDrawHistory draws={draws} />
    </div>
  );
}
