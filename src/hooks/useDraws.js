import { useState, useEffect } from 'react';
import { getDrawType, getDrawSubcategory, cat } from '../utils/categories';
import { fmtDate, fmtNum } from '../utils/format';

function enrich(d) {
  const type = getDrawType(d.draw_name);
  const { label, color } = cat(type);
  const subcategory = getDrawSubcategory(d.draw_name);
  return {
    ...d,
    type,
    typeLabel: label,
    color,
    subcategory,
    dateLabel: fmtDate(d.draw_date),
    invLabel: fmtNum(d.invitations),
  };
}

export function useDraws() {
  const [draws, setDraws] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/draws')
      .then(r => {
        if (!r.ok) throw new Error(`API returned ${r.status}`);
        return r.json();
      })
      .then(data => {
        const enriched = data
          .map(enrich)
          .sort((a, b) => new Date(a.draw_date) - new Date(b.draw_date));
        setDraws(enriched);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { draws, loading, error };
}
