export const CAT = {
  General:     { label: 'General',        color: '#16223d' },
  CEC:         { label: 'Canadian Exp',  color: '#3a6ea8' },
  PNP:         { label: 'Provincial',     color: '#6d4c91' },
  French:      { label: 'French',         color: '#c8362b' },
  Healthcare:  { label: 'Healthcare',     color: '#2f8f6b' },
  Education:   { label: 'Education',      color: '#c08a2d' },
  Trades:      { label: 'Trades',         color: '#cc6b33' },
  Agriculture: { label: 'Agriculture',    color: '#7a9a3a' },
  STEM:        { label: 'STEM',           color: '#4a5fb0' },
  Transport:   { label: 'Transport',      color: '#3d9098' },
};

export function getDrawType(drawName) {
  if (!drawName) return 'General';
  const n = drawName.toLowerCase().trim();
  if (n.includes('provincial'))                         return 'PNP';
  if (n.includes('canadian experience') || n.includes('canadian work experience') || n === 'cec') return 'CEC';
  if (n.includes('french'))                             return 'French';
  if (n.includes('healthcare') || n.includes('health care')) return 'Healthcare';
  if (n.includes('education'))                          return 'Education';
  if (n.includes('trade'))                              return 'Trades';
  if (n.includes('agriculture') || n.includes('agri-food')) return 'Agriculture';
  if (n.includes('stem'))                               return 'STEM';
  if (n.includes('transport'))                          return 'Transport';
  return drawName.trim();
}

export function cat(type) {
  return CAT[type] ?? { label: type || 'General', color: '#8a8f9e' };
}

export function getDrawSubcategory(drawName) {
  return drawName ? drawName.trim() : null;
}
