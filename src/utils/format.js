export const fmtNum = (n) => Number(n).toLocaleString('en-US');

export const fmtDate = (s) =>
  new Date(s + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });

export const fmtShort = (s) =>
  new Date(s + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric',
  });

export const fmtMonth = (s) =>
  new Date(s + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short', year: '2-digit',
  });

export const daysBetween = (a, b) =>
  Math.round((new Date(b) - new Date(a)) / 86_400_000);

// Relative "time ago" for a full ISO timestamp (e.g. the last sync's ran_at).
export const fmtRelative = (iso) => {
  if (!iso) return 'never';
  const secs = Math.round((Date.now() - new Date(iso)) / 1000);
  if (secs < 0) return 'just now';
  if (secs < 45) return 'just now';
  if (secs < 90) return '1 min ago';
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} h ago`;
  const days = Math.round(hrs / 24);
  return `${days} d ago`;
};

// Local wall-clock time, e.g. "2:23 PM" — used for a cooldown's unlock_at.
export const fmtTime = (iso) =>
  new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
