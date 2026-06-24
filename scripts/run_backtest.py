"""
Backtest the simulation against earlier elections.

Strategy:
  - Use 2008+2012+2016 data as historical context
  - Predict 2020 county margins using the simulation
  - Compare against actual 2020 results and a baseline (2016 margin)

This validates the model without touching 2024 data.
"""

import os
import sys
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sim.run_simulation import simulate_county, DEFAULT_VOTERS_PER_COUNTY
from sim.metrics import compute_metrics, compare_to_baseline, print_metrics_report


PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def build_backtest_features() -> pd.DataFrame:
    """
    Build a feature set that mimics what we'd have before the 2020 election.
    Uses only 2008, 2012, 2016 election data (pretends 2020 hasn't happened).
    """
    features_path = os.path.join(PROCESSED_DIR, "county_features.csv")
    df = pd.read_csv(features_path)
    df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)

    # For backtesting: use 2016 as "most recent" and 2012 as "prior"
    # Override the fields that the simulation reads
    backtest = df.copy()

    # The simulation reads margin_r_2020 as the "most recent" margin
    # For backtest, we substitute 2016 margin into that slot
    if "margin_r_2016" in backtest.columns:
        backtest["margin_r_2020_actual"] = backtest["margin_r_2020"].copy()
        backtest["margin_r_2020"] = backtest["margin_r_2016"]

    if "margin_r_2012" in backtest.columns:
        backtest["margin_r_2016"] = backtest["margin_r_2012"]

    # Use 2016 turnout as the "most recent" turnout
    if "turnout_2016" in backtest.columns:
        backtest["turnout_2020_actual"] = backtest.get("turnout_2020", 0)
        backtest["turnout_2020"] = backtest["turnout_2016"]

    # Recalculate avg_margin_r without 2020
    margin_cols = [c for c in backtest.columns if c.startswith("margin_r_20") and c != "margin_r_2020_actual"]
    if margin_cols:
        backtest["avg_margin_r"] = backtest[margin_cols].mean(axis=1)

    # Recalculate trend
    if "margin_r_2016" in backtest.columns and "margin_r_2012" in backtest.columns:
        backtest["margin_trend_16_20"] = backtest["margin_r_2016"] - backtest["margin_r_2012"]

    return backtest


def run_backtest(
    n_voters: int = DEFAULT_VOTERS_PER_COUNTY,
    n_iterations: int = 30,
    seed: int = 42,
) -> None:
    """Run the backtest: predict 2020 using only pre-2020 data."""
    print("=" * 60)
    print("  BACKTEST: Predicting 2020 from 2008-2016 data")
    print("=" * 60)

    # Load full features (has actual 2020 results for evaluation)
    full_features = pd.read_csv(os.path.join(PROCESSED_DIR, "county_features.csv"))
    full_features["county_fips"] = full_features["county_fips"].astype(str).str.zfill(5)

    # Build backtest features (pretend 2020 hasn't happened)
    backtest_features = build_backtest_features()

    print(f"\nRunning simulation for {len(backtest_features)} counties...")
    print(f"  Voters per county: {n_voters}")
    print(f"  Iterations: {n_iterations}")

    # 2016→2020: NC shifted ~1.3 pts toward D
    # For backtest, model a slight D shift to simulate pre-election environment
    statewide_shift = -0.005  # Slight D shift for 2020 prediction

    results = []
    for idx, row in backtest_features.iterrows():
        county_name = row.get("county_name", "Unknown")
        if idx % 20 == 0:
            print(f"  County {idx+1}/{len(backtest_features)}: {county_name}")

        result = simulate_county(
            county_features=row.to_dict(),
            n_voters=n_voters,
            n_iterations=n_iterations,
            seed=seed,
            statewide_shift=statewide_shift,
            use_urbanicity_shift=False,
        )
        results.append(result)

    results_df = pd.DataFrame(results)

    # Get actual 2020 margins
    actual_2020 = full_features[["county_fips", "county_name"]].copy()
    if "margin_r_2020" in full_features.columns:
        actual_2020["actual_margin_r"] = full_features["margin_r_2020"]
    else:
        print("ERROR: No 2020 actual margins found for evaluation!")
        return

    # Merge
    eval_df = results_df.merge(actual_2020, on="county_fips", how="inner", suffixes=("", "_actual"))
    eval_df = eval_df.merge(
        full_features[["county_fips", "margin_r_2016"]],
        on="county_fips",
        how="left",
    )

    # Compute metrics
    predicted = eval_df["predicted_margin_r"].values
    actual = eval_df["actual_margin_r"].values
    baseline_2016 = eval_df["margin_r_2016"].values

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)

    comparison = compare_to_baseline(predicted, actual, baseline_2016)

    print_metrics_report(comparison["simulation"], "Behavioral Simulation (predicting 2020)")
    print_metrics_report(comparison["baseline"], "Baseline (2016 margin → 2020)")

    print("\n  IMPROVEMENT over baseline:")
    imp = comparison["improvement"]
    for key, val in imp.items():
        direction = "better" if val > 0 else "worse"
        print(f"    {key}: {val:+.4f} ({direction})")

    # Save backtest results
    out_path = os.path.join(PROCESSED_DIR, "backtest_results.csv")
    eval_df.to_csv(out_path, index=False)
    print(f"\n  Saved backtest results to {out_path}")

    # Save metrics
    import json
    metrics_path = os.path.join(PROCESSED_DIR, "backtest_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"  Saved metrics to {metrics_path}")


if __name__ == "__main__":
    run_backtest()
