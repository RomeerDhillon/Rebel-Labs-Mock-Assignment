import predictions, { CountyPrediction } from "./predictions";

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "");
}

const bySlug: Record<string, CountyPrediction> = {};
const byFips: Record<string, CountyPrediction> = {};

for (const p of predictions) {
  bySlug[toSlug(p.county_name)] = p;
  byFips[p.county_fips] = p;
}

export function getCountyByIdOrSlug(
  id: string,
): CountyPrediction | undefined {
  return byFips[id] || bySlug[id];
}

export function getCountySlug(name: string): string {
  return toSlug(name);
}

export function getAllSlugs(): string[] {
  return predictions.map((p) => toSlug(p.county_name));
}

export function getAllFips(): string[] {
  return predictions.map((p) => p.county_fips);
}
