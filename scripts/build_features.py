"""
Build processed county feature table from raw data.
Combines election history, voter registration, and ACS demographics
into a single county_features.csv for the simulation.

No 2024 election results are used.
"""

import os
import pandas as pd
import numpy as np

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


def load_election_history() -> pd.DataFrame:
    """Load and reshape election history into one row per county."""
    path = os.path.join(RAW_DIR, "nc_election_history.csv")
    df = pd.read_csv(path)

    df["total_2party"] = df["votes_dem"] + df["votes_gop"]
    df["margin_r"] = (df["votes_gop"] - df["votes_dem"]) / df["total_2party"]
    df["turnout_total"] = df["total_votes"]

    # Pivot to one row per county with columns for each year
    years = sorted(df["year"].unique())
    county_list = df[["county_fips", "county_name"]].drop_duplicates()

    result = county_list.copy()
    for year in years:
        yr = df[df["year"] == year][["county_fips", "margin_r", "turnout_total", "votes_dem", "votes_gop"]].copy()
        yr = yr.rename(columns={
            "margin_r": f"margin_r_{year}",
            "turnout_total": f"turnout_{year}",
            "votes_dem": f"votes_dem_{year}",
            "votes_gop": f"votes_gop_{year}",
        })
        result = result.merge(yr, on="county_fips", how="left")

    # Compute trend features
    if "margin_r_2016" in result.columns and "margin_r_2020" in result.columns:
        result["margin_trend_16_20"] = result["margin_r_2020"] - result["margin_r_2016"]
    if "margin_r_2012" in result.columns and "margin_r_2020" in result.columns:
        result["margin_trend_12_20"] = result["margin_r_2020"] - result["margin_r_2012"]

    # Average margin across available years
    margin_cols = [c for c in result.columns if c.startswith("margin_r_")]
    result["avg_margin_r"] = result[margin_cols].mean(axis=1)

    # Turnout trend
    if "turnout_2016" in result.columns and "turnout_2020" in result.columns:
        result["turnout_growth_16_20"] = (
            result["turnout_2020"] - result["turnout_2016"]
        ) / result["turnout_2016"].replace(0, np.nan)

    return result


def load_demographics() -> pd.DataFrame:
    """Load ACS demographics."""
    path = os.path.join(RAW_DIR, "nc_acs_demographics.csv")
    df = pd.read_csv(path)

    # Keep key columns
    keep_cols = ["county_fips", "county_name", "total_pop",
                 "pct_white", "pct_black", "pct_hispanic", "pct_college",
                 "median_age", "median_household_income",
                 "land_area_sqmi", "pop_density", "urban_rural"]

    available = [c for c in keep_cols if c in df.columns]
    return df[available].copy()


def load_county_area() -> pd.DataFrame:
    """Load county land area for density calculation."""
    path = os.path.join(RAW_DIR, "nc_county_area.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=["county_fips", "land_area_sqmi"])


def load_registration() -> pd.DataFrame:
    """Load voter registration data."""
    party_path = os.path.join(RAW_DIR, "nc_registration_by_party.csv")
    if os.path.exists(party_path):
        return pd.read_csv(party_path)
    return pd.DataFrame()


def classify_urban_rural(pop_density: float) -> str:
    """Classify county as urban/suburban/rural based on density."""
    if pop_density >= 750:
        return "urban"
    elif pop_density >= 250:
        return "suburban"
    else:
        return "rural"


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print("Building county features...")

    # Load all data sources
    print("  Loading election history...")
    elections = load_election_history()

    print("  Loading demographics...")
    demographics = load_demographics()

    print("  Loading registration data...")
    registration = load_registration()

    # Merge everything
    # Start with elections as base (has all 100 counties)
    features = elections.copy()
    features["county_fips"] = features["county_fips"].astype(str).str.zfill(5)

    # Merge demographics (includes pop_density and urban_rural)
    if len(demographics) > 0:
        demographics["county_fips"] = demographics["county_fips"].astype(str).str.zfill(5)
        demo_cols = [c for c in demographics.columns if c != "county_name"]
        features = features.merge(demographics[demo_cols], on="county_fips", how="left")

    # Merge registration
    if len(registration) > 0:
        # Match on county name
        reg_cols = [c for c in registration.columns if c != "county_fips" or "county_fips" not in registration.columns]
        if "county_name" in registration.columns:
            registration["county_name"] = registration["county_name"].str.strip()
            features["county_name"] = features["county_name"].str.strip()

            # Try merge on county_name
            reg_merge_cols = [c for c in registration.columns if c not in ["county_name"]]
            reg_for_merge = registration[["county_name"] + reg_merge_cols].copy()
            features = features.merge(reg_for_merge, on="county_name", how="left")
        elif "county_fips" in registration.columns:
            registration["county_fips"] = registration["county_fips"].astype(str).str.zfill(5)
            reg_merge_cols = [c for c in registration.columns if c not in ["county_fips", "county_name"]]
            features = features.merge(registration[["county_fips"] + reg_merge_cols], on="county_fips", how="left")

    # Fill NaN registration with estimates from election history
    if "reg_dem_share" not in features.columns:
        if "margin_r_2020" in features.columns:
            features["reg_dem_share"] = 0.30 + 0.15 * (0.50 - features["margin_r_2020"].fillna(0) / 2 - 0.25)
            features["reg_rep_share"] = 0.30 + 0.15 * (features["margin_r_2020"].fillna(0) / 2 + 0.25 - 0.50)
            features["reg_unaf_share"] = 1.0 - features["reg_dem_share"] - features["reg_rep_share"]

    # --- Validation ---
    n_counties = len(features)
    print(f"  Total counties: {n_counties}")
    if n_counties != 100:
        print(f"  WARNING: Expected 100 counties, got {n_counties}")

    dupes = features["county_fips"].duplicated()
    if dupes.any():
        print(f"  WARNING: Duplicate FIPS codes: {features.loc[dupes, 'county_fips'].tolist()}")
        features = features.drop_duplicates(subset="county_fips", keep="first")

    margin_cols = [c for c in features.columns if c.startswith("margin_r_")]
    for col in margin_cols:
        bad = features[col].abs() > 1.0
        if bad.any():
            print(f"  WARNING: {col} has {bad.sum()} values outside [-1, 1], clipping")
            features[col] = features[col].clip(-1.0, 1.0)

    if "reg_dem_share" in features.columns:
        share_sum = features[["reg_dem_share", "reg_rep_share", "reg_unaf_share"]].sum(axis=1)
        bad_sums = (share_sum < 0.95) | (share_sum > 1.05)
        if bad_sums.any():
            print(f"  WARNING: {bad_sums.sum()} counties have registration shares not summing to ~1.0")

    if "total_pop" in features.columns:
        bad_pop = features["total_pop"] <= 0
        if bad_pop.any():
            print(f"  WARNING: {bad_pop.sum()} counties have non-positive population")

    # Save
    out_path = os.path.join(PROCESSED_DIR, "county_features.csv")
    features.to_csv(out_path, index=False)
    print(f"  Saved features to {out_path}")
    print(f"  Columns: {list(features.columns)}")

    # Also save a summary
    summary = features[["county_fips", "county_name"]].copy()
    if "margin_r_2020" in features.columns:
        summary["margin_r_2020"] = features["margin_r_2020"]
    if "avg_margin_r" in features.columns:
        summary["avg_margin_r"] = features["avg_margin_r"]
    if "total_pop" in features.columns:
        summary["total_pop"] = features["total_pop"]
    if "urban_rural" in features.columns:
        summary["urban_rural"] = features["urban_rural"]

    summary_path = os.path.join(PROCESSED_DIR, "county_summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"  Saved summary to {summary_path}")


if __name__ == "__main__":
    main()
