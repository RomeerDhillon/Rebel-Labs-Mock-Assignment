"""
Fetch all pre-election public data for the NC 2024 voter simulation.

Sources:
  1. County presidential election results 2008-2020 (tonmcg GitHub)
  2. NC voter registration statistics (NCSBE, pre-election snapshot)
  3. US Census ACS 5-Year 2022 county demographics

IMPORTANT: No 2024 election results are fetched or used.
"""

import os
import csv
import json
import io
import requests
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
NC_FIPS_STATE = "37"

# All 100 NC county FIPS codes (odd numbers 001-199)
NC_COUNTY_FIPS = [f"{i:03d}" for i in range(1, 200, 2)]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Historical Election Results (2008, 2012, 2016, 2020) — NO 2024
# ---------------------------------------------------------------------------

# Source 1: 2008-2016 wide-format CSV from tonmcg's older repo
URL_08_16 = "https://raw.githubusercontent.com/tonmcg/US_County_Level_Election_Results_08-16/master/US_County_Level_Presidential_Results_08-16.csv"

# Source 2: 2020 results from the main repo
URL_2020 = "https://raw.githubusercontent.com/tonmcg/US_County_Level_Election_Results_08-24/master/2020_US_County_Level_Presidential_Results.csv"


def fetch_election_results() -> None:
    """Download county-level presidential results for 2008-2020, filter to NC."""
    print("Fetching historical election results (2008-2020)...")
    all_years = []

    # --- Fetch 2008, 2012, 2016 from the wide-format CSV ---
    print("  Downloading 2008-2016 combined file...")
    resp = requests.get(URL_08_16, timeout=60)
    resp.raise_for_status()
    df_wide = pd.read_csv(io.StringIO(resp.text))
    df_wide.columns = [c.lower().strip() for c in df_wide.columns]

    # Columns: fips_code, county, total_YYYY, dem_YYYY, gop_YYYY, oth_YYYY
    fips_col = "fips_code"
    county_col = "county"
    df_wide[fips_col] = df_wide[fips_col].astype(str).str.zfill(5)
    nc_wide = df_wide[df_wide[fips_col].str.startswith(NC_FIPS_STATE)].copy()

    for year in [2008, 2012, 2016]:
        dem_c = f"dem_{year}"
        gop_c = f"gop_{year}"
        total_c = f"total_{year}"
        if dem_c in nc_wide.columns and gop_c in nc_wide.columns:
            yr_df = pd.DataFrame({
                "year": year,
                "county_fips": nc_wide[fips_col].values,
                "county_name": nc_wide[county_col].values,
                "votes_dem": pd.to_numeric(nc_wide[dem_c], errors="coerce").values,
                "votes_gop": pd.to_numeric(nc_wide[gop_c], errors="coerce").values,
                "total_votes": pd.to_numeric(nc_wide[total_c], errors="coerce").values if total_c in nc_wide.columns else 0,
            })
            all_years.append(yr_df)
            print(f"    Found {len(yr_df)} NC counties for {year}")

    # --- Fetch 2020 from the separate CSV ---
    print("  Downloading 2020...")
    resp = requests.get(URL_2020, timeout=60)
    resp.raise_for_status()
    df_2020 = pd.read_csv(io.StringIO(resp.text))
    df_2020.columns = [c.lower().strip() for c in df_2020.columns]

    # 2020 columns: state_name, county_fips, county_name, votes_gop, votes_dem, total_votes, ...
    df_2020["county_fips"] = df_2020["county_fips"].astype(str).str.zfill(5)
    nc_2020 = df_2020[df_2020["county_fips"].str.startswith(NC_FIPS_STATE)].copy()

    yr_df = pd.DataFrame({
        "year": 2020,
        "county_fips": nc_2020["county_fips"].values,
        "county_name": nc_2020["county_name"].values,
        "votes_dem": pd.to_numeric(nc_2020["votes_dem"], errors="coerce").values,
        "votes_gop": pd.to_numeric(nc_2020["votes_gop"], errors="coerce").values,
        "total_votes": pd.to_numeric(nc_2020["total_votes"], errors="coerce").values,
    })
    all_years.append(yr_df)
    print(f"    Found {len(yr_df)} NC counties for 2020")

    if all_years:
        combined = pd.concat(all_years, ignore_index=True)
        # Clean county names
        combined["county_name"] = combined["county_name"].str.replace(" County", "", regex=False).str.strip()
        out_path = os.path.join(RAW_DIR, "nc_election_history.csv")
        combined.to_csv(out_path, index=False)
        print(f"  Saved {len(combined)} rows to {out_path}")
    else:
        print("  ERROR: No election data fetched!")


# ---------------------------------------------------------------------------
# 2. NC Voter Registration & Demographics (embedded public data)
# ---------------------------------------------------------------------------

def save_registration_data() -> None:
    """Save embedded NCSBE voter registration data (Oct 2024 pre-election snapshot)."""
    print("Saving NC voter registration data (NCSBE Oct 12, 2024)...")
    from scripts.nc_registration_data import get_registration_dataframe
    df = get_registration_dataframe()
    df.to_csv(os.path.join(RAW_DIR, "nc_registration_by_party.csv"), index=False)
    print(f"  Saved registration for {len(df)} counties")


def save_demographics_data() -> None:
    """Save embedded ACS 2022 demographic data for all 100 NC counties."""
    print("Saving ACS 2022 demographics (embedded)...")
    from scripts.nc_county_data import get_demographics_dataframe
    df = get_demographics_dataframe()
    df.to_csv(os.path.join(RAW_DIR, "nc_acs_demographics.csv"), index=False)
    print(f"  Saved demographics for {len(df)} counties")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ensure_dir(RAW_DIR)
    fetch_election_results()
    save_demographics_data()
    save_registration_data()
    print("\nData fetching complete!")
    print(f"Raw data saved to: {os.path.abspath(RAW_DIR)}")


if __name__ == "__main__":
    main()
