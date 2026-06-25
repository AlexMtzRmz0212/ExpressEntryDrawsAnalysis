export function linearRegression(ys) {
  const n = ys.length;
  if (n === 0) return { slope: 0, intercept: 0, predict: () => 0, std: 0 };
  const mx = (n - 1) / 2;
  const my = ys.reduce((a, b) => a + b, 0) / n;
  let num = 0, den = 0;
  for (let i = 0; i < n; i++) {
    num += (i - mx) * (ys[i] - my);
    den += (i - mx) ** 2;
  }
  const slope = den ? num / den : 0;
  const intercept = my - slope * mx;
  const residuals = ys.map((y, i) => y - (slope * i + intercept));
  const std = Math.sqrt(residuals.reduce((a, b) => a + b * b, 0) / n);
  return { slope, intercept, predict: (x) => slope * x + intercept, std };
}

export function computeGaps(draws) {
  const gaps = [];
  for (let i = 1; i < draws.length; i++) {
    gaps.push({
      days: Math.round(
        (new Date(draws[i].draw_date) - new Date(draws[i - 1].draw_date)) / 86_400_000
      ),
      draw: draws[i],
    });
  }
  return gaps;
}

export function computePrediction(draws) {
  const core = draws.filter(d => d.type === 'General' || d.type === 'CEC');
  if (!core.length) return null;

  const wN = Math.min(8, core.length);
  const recent = core.slice(-wN);
  const reg = linearRegression(recent.map(d => d.crs_cutoff));
  const predCrs = Math.round(reg.predict(wN));
  const crsBand = Math.max(3, Math.round(reg.std));

  // avg gap between recent core draws
  const coreGaps = [];
  for (let i = 1; i < core.length; i++) {
    coreGaps.push(
      Math.round((new Date(core[i].draw_date) - new Date(core[i - 1].draw_date)) / 86_400_000)
    );
  }
  const recentGaps = coreGaps.slice(-6);
  const coreGap = recentGaps.length
    ? Math.round(recentGaps.reduce((a, b) => a + b, 0) / recentGaps.length)
    : 14;

  const lastCore = core[core.length - 1];
  const center = new Date(lastCore.draw_date + 'T00:00:00');
  center.setDate(center.getDate() + coreGap);
  const lo = new Date(center); lo.setDate(lo.getDate() - 3);
  const hi = new Date(center); hi.setDate(hi.getDate() + 3);

  const sizeSample = recent.slice(-4);
  const predSize =
    Math.round(sizeSample.reduce((a, b) => a + b.invitations, 0) / sizeSample.length / 100) * 100;

  const confidence = reg.std < 8 ? 'High' : reg.std < 16 ? 'Medium' : 'Lower';
  const confColor  = reg.std < 8 ? '#7ed6a8' : reg.std < 16 ? '#f0c674' : '#e89b87';

  return { crs: predCrs, crsBand, lo: lo.toISOString().slice(0, 10), hi: hi.toISOString().slice(0, 10), size: predSize, confidence, confColor, window: wN, lastCore };
}
