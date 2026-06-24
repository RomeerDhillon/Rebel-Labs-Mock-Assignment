"""
Main simulation orchestrator.

For each county:
1. Generate synthetic voter population
2. Simulate turnout
3. Simulate vote choice
4. Compute county-level margin
5. Repeat for K Monte Carlo iterations
6. Average results and compute uncertainty

This module ties together population.py, turnout.py, and vote_choice.py.
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

from sim.population import generate_county_population
from sim.turnout import simulate_turnout, compute_county_baseline_logit
from sim.vote_choice import simulate_vote_choice, compute_county_partisan_baseline
from sim.utils import validate_county_features


DEFAULT_VOTERS_PER_COUNTY = 2000  # Synthetic voters per county per iteration
DEFAULT_ITERATIONS = 50           # Monte Carlo iterations
DEFAULT_SEED = 42                 # Master random seed
DEFAULT_TURNOUT_SENSITIVITY = 1.0
DEFAULT_PARTISAN_ELASTICITY = 1.0

# Urbanicity-aware statewide shift for 2024 prediction.
# In NC 2016→2020, urban counties shifted D by ~2-3 pts while rural
# shifted R by ~1-2 pts. For 2024, pre-election indicators suggest
# a slight R shift overall with continued urban/rural divergence.
# These are calibrated from the 2016→2020 differential, NOT from 2024 results.
URBANICITY_SHIFT = {
    "urban": -0.005,   # Urban areas: slight D shift continues
    "suburban": 0.01,  # Suburban: slight R shift
    "rural": 0.015,    # Rural: continued R shift
}
DEFAULT_STATEWIDE_SHIFT = 0.01   # Fallback if urbanicity unavailable


def _get_statewide_shift(county_features: Dict[str, Any], default_shift: float) -> float:
    """Return urbanicity-aware statewide shift for this county."""
    urban_rural = county_features.get("urban_rural", None)
    if urban_rural and not pd.isna(urban_rural) and urban_rural in URBANICITY_SHIFT:
        return URBANICITY_SHIFT[urban_rural]
    return default_shift


def simulate_county(
    county_features: Dict[str, Any],
    n_voters: int = DEFAULT_VOTERS_PER_COUNTY,
    n_iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
    turnout_sensitivity: float = DEFAULT_TURNOUT_SENSITIVITY,
    partisan_elasticity: float = DEFAULT_PARTISAN_ELASTICITY,
    statewide_shift: float = DEFAULT_STATEWIDE_SHIFT,
    use_urbanicity_shift: bool = True,
) -> Dict[str, Any]:
    """
    Run the full simulation for one county.

    Returns a dict with:
    - county_fips, county_name
    - predicted_margin_r: average R-D margin across iterations
    - margin_std: standard deviation across iterations
    - ci_low, ci_high: 95% confidence interval (2.5th/97.5th percentile)
    - avg_turnout_rate: average simulated turnout rate
    - n_iterations: number of iterations run
    """
    cf = county_features
    county_fips = str(cf.get("county_fips", ""))
    county_name = cf.get("county_name", "")

    # Compute county baselines
    margin_2020 = cf.get("margin_r_2020", 0.0)
    margin_2016 = cf.get("margin_r_2016", None)

    if pd.isna(margin_2020):
        margin_2020 = cf.get("avg_margin_r", 0.0)
        if pd.isna(margin_2020):
            margin_2020 = 0.0
    if margin_2016 is not None and pd.isna(margin_2016):
        margin_2016 = None

    # Extract margin trend for trend-aware baseline
    margin_trend = cf.get("margin_trend_16_20", None)
    if margin_trend is not None and pd.isna(margin_trend):
        margin_trend = None

    # Urbanicity-aware statewide shift (disabled for backtesting)
    if use_urbanicity_shift:
        county_shift = _get_statewide_shift(cf, statewide_shift)
    else:
        county_shift = statewide_shift

    # Turnout baseline from historical rates
    turnout_2020 = cf.get("turnout_2020", 0)

    # Estimate registered voters from total votes / turnout rate
    # NC average turnout rate ~75% of registered in presidential years
    total_registered_est = cf.get("reg_total", None)
    if total_registered_est is None or pd.isna(total_registered_est):
        if turnout_2020 and not pd.isna(turnout_2020) and turnout_2020 > 0:
            total_registered_est = turnout_2020 / 0.75
        else:
            total_registered_est = 30000  # Fallback

    # Historical turnout rate
    if total_registered_est > 0 and turnout_2020 and not pd.isna(turnout_2020):
        hist_turnout_rate = min(turnout_2020 / total_registered_est, 0.95)
    else:
        hist_turnout_rate = 0.72  # NC average

    turnout_baseline_logit = compute_county_baseline_logit(hist_turnout_rate)
    partisan_baseline_logit = compute_county_partisan_baseline(
        margin_2020, margin_2016, county_shift, margin_trend
    )

    # Run Monte Carlo iterations
    iteration_margins = np.empty(n_iterations)
    iteration_turnout_rates = np.empty(n_iterations)

    # Deterministic per-county seed using int(FIPS) instead of hash()
    county_seed_base = seed + int(county_fips) * 7

    for it in range(n_iterations):
        iter_seed = county_seed_base + it * 1000
        rng = np.random.RandomState(iter_seed)

        # 1. Generate population (dict of arrays)
        voters = generate_county_population(cf, n_voters, rng)

        # 2. Simulate turnout (bool array)
        turned_out = simulate_turnout(
            voters, turnout_baseline_logit, rng, turnout_sensitivity
        )

        # 3. Simulate vote choice (int8 array: 1=R, 0=D, -1=abstain)
        votes = simulate_vote_choice(
            voters, turned_out, partisan_baseline_logit, rng, partisan_elasticity
        )

        # 4. Aggregate (vectorized)
        n_voted = int(np.sum(turned_out))
        if n_voted == 0:
            iteration_margins[it] = 0.0
            iteration_turnout_rates[it] = 0.0
            continue

        n_r = int(np.sum(votes == 1))
        n_d = int(np.sum(votes == 0))
        total_2party = n_r + n_d

        if total_2party > 0:
            iteration_margins[it] = (n_r - n_d) / total_2party
        else:
            iteration_margins[it] = 0.0

        iteration_turnout_rates[it] = n_voted / n_voters

    # Compute summary statistics
    predicted_margin = float(np.mean(iteration_margins))
    margin_std = float(np.std(iteration_margins))
    # True 95% CI: 2.5th and 97.5th percentiles
    ci_low = float(np.percentile(iteration_margins, 2.5))
    ci_high = float(np.percentile(iteration_margins, 97.5))

    return {
        "county_fips": county_fips,
        "county_name": county_name,
        "predicted_margin_r": round(predicted_margin, 6),
        "margin_std": round(margin_std, 6),
        "ci_low": round(ci_low, 6),
        "ci_high": round(ci_high, 6),
        "avg_turnout_rate": round(float(np.mean(iteration_turnout_rates)), 4),
        "n_iterations": n_iterations,
    }


def run_full_simulation(
    features_path: Optional[str] = None,
    n_voters: int = DEFAULT_VOTERS_PER_COUNTY,
    n_iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
    turnout_sensitivity: float = DEFAULT_TURNOUT_SENSITIVITY,
    partisan_elasticity: float = DEFAULT_PARTISAN_ELASTICITY,
    statewide_shift: float = DEFAULT_STATEWIDE_SHIFT,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Run simulation for all 100 NC counties.

    Returns DataFrame with one row per county.
    """
    if features_path is None:
        features_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "processed", "county_features.csv"
        )

    df = pd.read_csv(features_path)

    # Validate input data
    df = validate_county_features(df)

    if verbose:
        print(f"  Loaded {len(df)} counties from {features_path}")

    results = []
    for idx, row in df.iterrows():
        county_name = row.get("county_name", "Unknown")
        if verbose and idx % 10 == 0:
            print(f"  Simulating county {idx+1}/{len(df)}: {county_name}...")

        result = simulate_county(
            county_features=row.to_dict(),
            n_voters=n_voters,
            n_iterations=n_iterations,
            seed=seed,
            turnout_sensitivity=turnout_sensitivity,
            partisan_elasticity=partisan_elasticity,
            statewide_shift=statewide_shift,
        )
        results.append(result)

    results_df = pd.DataFrame(results)

    if verbose:
        print(f"\nSimulation complete: {len(results_df)} counties")
        r_counties = (results_df["predicted_margin_r"] > 0).sum()
        d_counties = (results_df["predicted_margin_r"] <= 0).sum()
        print(f"  R-leaning counties: {r_counties}")
        print(f"  D-leaning counties: {d_counties}")
        avg = results_df["predicted_margin_r"].mean()
        party = "R" if avg > 0 else "D"
        print(f"  Avg county margin (unweighted): {party}+{abs(avg)*100:.1f}%")

    return results_df
