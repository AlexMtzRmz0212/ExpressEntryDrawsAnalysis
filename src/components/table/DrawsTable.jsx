import { useState, useMemo } from 'react';
import { cat } from '../../utils/categories';

const COLUMNS = [
  { key: 'draw_number', label: 'Draw',        align: 'left'  },
  { key: 'draw_date',   label: 'Date',        align: 'left'  },
  { key: 'type',        label: 'Category',    align: 'left'  },
  { key: 'invitations', label: 'Invitations', align: 'right' },
  { key: 'crs_cutoff',  label: 'CRS',        align: 'right' },
];

export default function DrawsTable({ draws }) {
  const [search,    setSearch]    = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [sortKey,   setSortKey]   = useState('draw_date');
  const [sortDir,   setSortDir]   = useState('desc');

  const typeOptions = useMemo(() => {
    const types = [...new Set(draws.map(d => d.type))].sort();
    return [{ value: 'All', label: 'All types' }, ...types.map(t => ({ value: t, label: cat(t).label }))];
  }, [draws]);

  const rows = useMemo(() => {
    let list = [...draws];
    if (typeFilter !== 'All') list = list.filter(d => d.type === typeFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(d =>
        String(d.draw_number).includes(q) ||
        d.typeLabel.toLowerCase().includes(q) ||
        d.draw_name.toLowerCase().includes(q) ||
        d.draw_date.includes(q) ||
        d.dateLabel.toLowerCase().includes(q)
      );
    }
    const dir = sortDir === 'asc' ? 1 : -1;
    list.sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey];
      return av < bv ? -dir : av > bv ? dir : 0;
    });
    return list;
  }, [draws, search, typeFilter, sortKey, sortDir]);

  function toggleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDir('desc'); }
  }

  const arrow = (key) => sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : '';

  return (
    <section style={{ background: '#fff', border: '1px solid #e2ded3', borderRadius: 12, padding: '22px 24px', marginTop: 22 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap', marginBottom: 16 }}>
        <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>
          All draws{' '}
          <span style={{ fontFamily: "'Spline Sans Mono',monospace", color: '#6b7180', fontWeight: 500, fontSize: 14 }}>
            ({rows.length})
          </span>
        </h2>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search #, type, date…"
            style={{ fontFamily: 'inherit', fontSize: 13, padding: '8px 13px', borderRadius: 8, border: '1px solid #e2ded3', background: '#faf9f6', width: 200 }}
          />
          <select
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            style={{ fontFamily: 'inherit', fontSize: 13, padding: '8px 13px', borderRadius: 8, border: '1px solid #e2ded3', background: '#faf9f6', cursor: 'pointer' }}
          >
            {typeOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13.5 }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #16223d' }}>
              {COLUMNS.map(col => (
                <th
                  key={col.key}
                  onClick={() => toggleSort(col.key)}
                  style={{
                    textAlign: col.align, padding: '10px 12px',
                    fontSize: 11.5, letterSpacing: '.06em', textTransform: 'uppercase',
                    color: '#5b6172', fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap',
                  }}
                >
                  {col.label}{arrow(col.key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.draw_number} style={{ borderBottom: '1px solid #f0eee7' }}>
                <td style={{ padding: '11px 12px', fontFamily: "'Spline Sans Mono',monospace", fontWeight: 600 }}>
                  #{r.draw_number}
                </td>
                <td style={{ padding: '11px 12px', fontFamily: "'Spline Sans Mono',monospace", color: '#5b6172' }}>
                  {r.dateLabel}
                </td>
                <td style={{ padding: '11px 12px' }}>
                  <span style={{ display: 'inline-flex', flexDirection: 'column', gap: 2 }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
                      <span style={{ width: 9, height: 9, borderRadius: '50%', background: r.color, flexShrink: 0, display: 'inline-block' }} />
                      {r.typeLabel}
                    </span>
                    {r.subcategory && (
                      <span style={{ fontSize: 11, color: '#6b7180', paddingLeft: 16 }}>
                        {r.subcategory}
                      </span>
                    )}
                  </span>
                </td>
                <td style={{ padding: '11px 12px', textAlign: 'right', fontFamily: "'Spline Sans Mono',monospace" }}>
                  {r.invLabel}
                </td>
                <td style={{ padding: '11px 12px', textAlign: 'right', fontFamily: "'Spline Sans Mono',monospace", fontWeight: 700 }}>
                  {r.crs_cutoff}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
