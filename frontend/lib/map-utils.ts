import predictions, { CountyPrediction } from "./predictions";

const predictionsByFips: Record<string, CountyPrediction> = {};
for (const p of predictions) {
  predictionsByFips[p.county_fips] = p;
}

export function getCountyPrediction(
  fips: string,
): CountyPrediction | undefined {
  return predictionsByFips[fips];
}

export function getCountyFillColor(margin: number): string {
  const abs = Math.abs(margin);
  if (abs < 0.005) return "#9ca3af"; // gray-400 — tie

  if (margin > 0) {
    // Republican — red scale
    if (abs > 0.4) return "#991b1b"; // red-800
    if (abs > 0.25) return "#b91c1c"; // red-700
    if (abs > 0.15) return "#dc2626"; // red-600
    if (abs > 0.08) return "#ef4444"; // red-500
    return "#f87171"; // red-400
  } else {
    // Democratic — blue scale
    if (abs > 0.4) return "#1e3a8a"; // blue-900
    if (abs > 0.25) return "#1d4ed8"; // blue-700
    if (abs > 0.15) return "#2563eb"; // blue-600
    if (abs > 0.08) return "#3b82f6"; // blue-500
    return "#60a5fa"; // blue-400
  }
}

export function getCountyHoverColor(margin: number): string {
  const abs = Math.abs(margin);
  if (abs < 0.005) return "#6b7280"; // gray-500

  if (margin > 0) {
    if (abs > 0.25) return "#7f1d1d"; // red-900
    if (abs > 0.15) return "#991b1b"; // red-800
    return "#b91c1c"; // red-700
  } else {
    if (abs > 0.25) return "#1e3a8a"; // blue-900
    if (abs > 0.15) return "#1d4ed8"; // blue-700
    return "#1e40af"; // blue-800
  }
}

export function formatMargin(margin: number): string {
  const party = margin > 0 ? "R" : "D";
  const abs = Math.abs(margin);
  if (abs < 0.005) return "Tie";
  return `${party}+${(abs * 100).toFixed(1)}%`;
}

export function getPartyLabel(margin: number): string {
  if (Math.abs(margin) < 0.005) return "Tie";
  return margin > 0 ? "Republican" : "Democratic";
}

export function getPartyLabelShort(margin: number): string {
  if (Math.abs(margin) < 0.005) return "Tie";
  return margin > 0 ? "GOP" : "Dem";
}
