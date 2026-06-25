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
