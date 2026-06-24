import data from "./predictions-data.json";

export interface CountyPrediction {
  county_fips: string;
  county_name: string;
  predicted_margin_r: number;
  margin_std: number;
  ci_low: number;
  ci_high: number;
  avg_turnout_rate: number;
}

const predictions: CountyPrediction[] = data as CountyPrediction[];
export default predictions;
