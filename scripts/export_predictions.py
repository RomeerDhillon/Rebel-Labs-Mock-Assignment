"""
Export final 2024 NC presidential election predictions.

Runs the full simulation using all available pre-election data
and exports predictions for all 100 counties.

No 2024 election results are used anywhere in this pipeline.
"""

import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sim.run_simulation import run_full_simulation

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
PREDICTIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "predictions")


def main() -> None:
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)

    print("=" * 60)
    print("  NC 2024 Presidential Election — County Predictions")
    print("  Voter-Level Behavioral Simulation")
    print("=" * 60)

    features_path = os.path.join(PROCESSED_DIR, "county_features.csv")
    if not os.path.exists(features_path):
        print(f"ERROR: Features file not found: {features_path}")
        print("Run scripts/fetch_data.py and scripts/build_features.py first.")
        sys.exit(1)

    print("\nRunning simulation...")
    results = run_full_simulation(
        features_path=features_path,
        n_voters=2000,
        n_iterations=50,
        seed=42,
        turnout_sensitivity=1.0,
        partisan_elasticity=1.0,
        statewide_shift=0.01,  # Slight R shift for 2024 environment
        verbose=True,
    )

    # Format output
    predictions = results[[
        "county_fips", "county_name", "predicted_margin_r",
        "margin_std", "ci_low", "ci_high", "avg_turnout_rate",
    ]].copy()

    predictions = predictions.sort_values("county_name").reset_index(drop=True)

    # Save predictions CSV
    csv_path = os.path.join(PREDICTIONS_DIR, "nc_2024_predictions.csv")
    predictions.to_csv(csv_path, index=False)
    print(f"\nSaved predictions to {csv_path}")

    # Save as JSON for the frontend
    json_path = os.path.join(PREDICTIONS_DIR, "nc_2024_predictions.json")
    records = predictions.to_dict(orient="records")
    with open(json_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Saved JSON predictions to {json_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("  PREDICTION SUMMARY")
    print("=" * 60)
    print(f"  Total counties: {len(predictions)}")

    r_counties = (predictions["predicted_margin_r"] > 0).sum()
    d_counties = (predictions["predicted_margin_r"] <= 0).sum()
    print(f"  R-leaning counties: {r_counties}")
    print(f"  D-leaning counties: {d_counties}")

    avg_margin = predictions["predicted_margin_r"].mean()
    print(f"  Average county margin (unweighted): {avg_margin:+.4f}")

    # Top 5 most R and most D counties
    print("\n  Top 5 most Republican counties:")
    top_r = predictions.nlargest(5, "predicted_margin_r")
    for _, row in top_r.iterrows():
        print(f"    {row['county_name']}: R+{row['predicted_margin_r']:.3f}")

    print("\n  Top 5 most Democratic counties:")
    top_d = predictions.nsmallest(5, "predicted_margin_r")
    for _, row in top_d.iterrows():
        margin = abs(row["predicted_margin_r"])
        print(f"    {row['county_name']}: D+{margin:.3f}")

    print("\n  Top 5 closest counties:")
    predictions["abs_margin"] = predictions["predicted_margin_r"].abs()
    closest = predictions.nsmallest(5, "abs_margin")
    for _, row in closest.iterrows():
        party = "R" if row["predicted_margin_r"] > 0 else "D"
        print(f"    {row['county_name']}: {party}+{row['abs_margin']:.3f}")


if __name__ == "__main__":
    main()
