"""
Synthetic voter population generator.

Creates individual simulated voters for each county based on:
- County voter registration data (party, race, gender distributions)
- ACS demographic profiles (age, education, race)
- County urbanicity

Each voter is a dictionary with demographic attributes that drive
turnout and vote-choice models downstream.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any


# Age band definitions and their approximate share of the registered voter population
AGE_BANDS = {
    "18-24": 0.10,
    "25-34": 0.16,
    "35-44": 0.17,
    "45-54": 0.17,
    "55-64": 0.18,
    "65+": 0.22,
}

# Adjust age distribution based on county median age
def _adjust_age_distribution(base_dist: Dict[str, float], median_age: float) -> Dict[str, float]:
    """Shift age distribution based on county median age vs. state average (39)."""
    age_shift = (median_age - 39.0) / 39.0  # Positive = older county
    adjusted = {}
    young_bands = ["18-24", "25-34"]
    old_bands = ["55-64", "65+"]

    for band, share in base_dist.items():
        if band in young_bands:
            adjusted[band] = max(0.03, share * (1 - age_shift * 0.3))
        elif band in old_bands:
            adjusted[band] = max(0.03, share * (1 + age_shift * 0.3))
        else:
            adjusted[band] = share

    # Renormalize
    total = sum(adjusted.values())
    return {k: v / total for k, v in adjusted.items()}


def generate_county_population(
    county_features: Dict[str, Any],
    n_voters: int,
    rng: np.random.RandomState,
) -> Dict[str, np.ndarray]:
    """
    Generate a synthetic voter population for a single county.

    Parameters
    ----------
    county_features : dict
        Row from county_features.csv with demographics, registration, etc.
    n_voters : int
        Number of synthetic voters to generate.
    rng : np.random.RandomState
        Random state for reproducibility.

    Returns
    -------
    dict of np.ndarray
        Columnar representation with keys:
        - age_band, sex, race, education, party_reg, urban_rural, county_fips
        Each value is a 1-D array of strings with length n_voters.
    """
    cf = county_features

    # --- Age distribution ---
    median_age = cf.get("median_age", 39.0)
    if pd.isna(median_age):
        median_age = 39.0
    age_dist = _adjust_age_distribution(AGE_BANDS.copy(), median_age)
    age_labels = list(age_dist.keys())
    age_probs = np.array(list(age_dist.values()))

    # --- Race distribution ---
    pct_white = cf.get("pct_white", 0.63)
    pct_black = cf.get("pct_black", 0.21)
    pct_hispanic = cf.get("pct_hispanic", 0.10)
    for val_name in ["pct_white", "pct_black", "pct_hispanic"]:
        val = cf.get(val_name, 0.0)
        if pd.isna(val):
            if val_name == "pct_white":
                pct_white = 0.63
            elif val_name == "pct_black":
                pct_black = 0.21
            else:
                pct_hispanic = 0.10

    pct_other = max(0.01, 1.0 - pct_white - pct_black - pct_hispanic)
    race_probs = np.array([pct_white, pct_black, pct_hispanic, pct_other])
    race_probs = np.maximum(race_probs, 0.001)
    race_probs /= race_probs.sum()
    race_labels = ["white", "black", "hispanic", "other"]

    # --- Education distribution ---
    pct_college = cf.get("pct_college", 0.30)
    if pd.isna(pct_college):
        pct_college = 0.30
    pct_college = np.clip(pct_college, 0.05, 0.80)

    # --- Party registration ---
    reg_dem = cf.get("reg_dem_share", 0.33)
    reg_rep = cf.get("reg_rep_share", 0.30)
    reg_unaf = cf.get("reg_unaf_share", 0.37)
    for val_name, default in [("reg_dem_share", 0.33), ("reg_rep_share", 0.30), ("reg_unaf_share", 0.37)]:
        val = cf.get(val_name, default)
        if pd.isna(val):
            if val_name == "reg_dem_share":
                reg_dem = default
            elif val_name == "reg_rep_share":
                reg_rep = default
            else:
                reg_unaf = default

    party_probs = np.array([reg_dem, reg_rep, reg_unaf])
    party_probs = np.maximum(party_probs, 0.01)
    party_probs /= party_probs.sum()
    party_labels = ["dem", "rep", "unaf"]

    # --- Urban/rural ---
    urban_rural = cf.get("urban_rural", "rural")
    if pd.isna(urban_rural):
        urban_rural = "rural"

    # --- Sex (approximate 52% F, 48% M among voters) ---
    sex_probs = np.array([0.48, 0.52])

    # --- Generate voters (columnar) ---
    return {
        "age_band": rng.choice(age_labels, size=n_voters, p=age_probs),
        "sex": rng.choice(["M", "F"], size=n_voters, p=sex_probs),
        "race": rng.choice(race_labels, size=n_voters, p=race_probs),
        "education": rng.choice(
            ["college", "no_college"],
            size=n_voters,
            p=[pct_college, 1 - pct_college],
        ),
        "party_reg": rng.choice(party_labels, size=n_voters, p=party_probs),
        "urban_rural": np.full(n_voters, urban_rural),
        "county_fips": np.full(n_voters, str(cf.get("county_fips", "00000"))),
    }
