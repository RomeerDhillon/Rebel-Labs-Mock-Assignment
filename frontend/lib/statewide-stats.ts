import predictions from "./predictions";

const sorted = [...predictions].sort(
  (a, b) => Math.abs(a.predicted_margin_r) - Math.abs(b.predicted_margin_r),
);

const largestMargin = [...predictions].sort(
  (a, b) => Math.abs(b.predicted_margin_r) - Math.abs(a.predicted_margin_r),
)[0];

export const rCounties = predictions.filter(
  (p) => p.predicted_margin_r > 0.005,
).length;
export const dCounties = predictions.filter(
  (p) => p.predicted_margin_r < -0.005,
).length;
export const tieCounties = predictions.length - rCounties - dCounties;

export const avgMargin =
  predictions.reduce((s, p) => s + p.predicted_margin_r, 0) /
  predictions.length;

export const closestCounty = sorted[0];
export const largestMarginCounty = largestMargin;

export const statewideWinnerByCounties =
  rCounties > dCounties ? "Republican" : "Democratic";

export const statewideRPct = (((avgMargin + 1) / 2) * 100).toFixed(1);
export const statewideRPctNum = ((avgMargin + 1) / 2) * 100;
export const statewideDPct = (((1 - avgMargin) / 2) * 100).toFixed(1);
export const statewideDPctNum = ((1 - avgMargin) / 2) * 100;

export const statewideWinner = avgMargin > 0 ? "Republican" : "Democratic";
