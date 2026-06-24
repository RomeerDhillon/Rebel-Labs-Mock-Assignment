import predictions from "./predictions";

// Single pass: compute counts, sum, closest, largest margin, and population-weighted margin
let _rCounties = 0;
let _dCounties = 0;
let _marginSum = 0;
let _weightedMarginSum = 0;
let _totalVotes = 0;
let _closest = predictions[0];
let _largest = predictions[0];
let _closestAbs = Math.abs(predictions[0]?.predicted_margin_r ?? 0);
let _largestAbs = _closestAbs;

for (const p of predictions) {
  const m = p.predicted_margin_r;
  const v = p.total_votes_2020 ?? 0;
  _marginSum += m;
  _weightedMarginSum += m * v;
  _totalVotes += v;
  if (m > 0.005) _rCounties++;
  else if (m < -0.005) _dCounties++;
  const absM = Math.abs(m);
  if (absM < _closestAbs) {
    _closestAbs = absM;
    _closest = p;
  }
  if (absM > _largestAbs) {
    _largestAbs = absM;
    _largest = p;
  }
}

export const rCounties = _rCounties;
export const dCounties = _dCounties;
export const tieCounties = predictions.length - rCounties - dCounties;

export const avgMargin =
  predictions.length > 0 ? _marginSum / predictions.length : 0;

// Population-weighted statewide margin (the actual predicted popular vote)
export const statewideMargin =
  _totalVotes > 0 ? _weightedMarginSum / _totalVotes : avgMargin;

export const closestCounty = _closest;
export const largestMarginCounty = _largest;

export const statewideWinnerByCounties =
  rCounties > dCounties ? "Republican" : "Democratic";

export const statewideRPct = (((statewideMargin + 1) / 2) * 100).toFixed(2);
export const statewideRPctNum = ((statewideMargin + 1) / 2) * 100;
export const statewideDPct = (((1 - statewideMargin) / 2) * 100).toFixed(2);
export const statewideDPctNum = ((1 - statewideMargin) / 2) * 100;

export const statewideWinner =
  statewideMargin > 0 ? "Republican" : "Democratic";
