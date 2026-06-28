import DrawCadenceStat from './DrawCadenceStat';
import DrawRhythm from '../overview/DrawRhythm';

export default function Cadence({ draws }) {
  return (
    <div>
      <div style={{ marginTop: 22 }}>
        <DrawCadenceStat draws={draws} />
      </div>
      <DrawRhythm draws={draws} />
    </div>
  );
}
