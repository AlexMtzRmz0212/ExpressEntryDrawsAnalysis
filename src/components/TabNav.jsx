const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'predict',  label: 'Predictions' },
  { id: 'table',    label: 'All draws' },
];

export default function TabNav({ tab, setTab }) {
  return (
    <nav style={{
      display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 18, background: '#e6e2d8',
      padding: 4, borderRadius: 10, width: 'max-content', maxWidth: '100%',
    }}>
      {TABS.map(t => (
        <button
          key={t.id}
          onClick={() => setTab(t.id)}
          style={{
            border: 'none', cursor: 'pointer', fontFamily: 'inherit',
            fontSize: 13.5, fontWeight: 600, padding: '9px 18px', borderRadius: 7,
            background: tab === t.id ? '#16223d' : 'transparent',
            color: tab === t.id ? '#fff' : '#5b6172',
            boxShadow: tab === t.id ? '0 1px 3px rgba(22,34,61,.25)' : 'none',
            transition: 'all .15s',
          }}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}
