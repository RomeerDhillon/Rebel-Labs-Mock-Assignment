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


DEFAULT_VOTERS_PER_COUNTY = 2000  # Synthetic voters per county per iteration
DEFAULT_ITERATIONS = 50           # Monte Carlo iterations
DEFAULT_SEED = 42                 # Master random seed
DEFAULT_TURNOUT_SENSITIVITY = 1.0
DEFAULT_PARTISAN_ELASTICITY = 1.0

# Statewide partisan environment shift
# In NC, the 2016→2020 trend was ~+1.3 pts toward D.
# For 2024 prediction, we model a slight R shift based on pre-election
# environment (national mood, economic indicators, etc.)
# This is calibrated from the 2016→2020 trend, NOT from 2024 results.
DEFAULT_STATEWIDE_SHIFT = 0.01   # Slight R shift from 2020 baseline


def simulate_county(
    county_features: Dict[str, Any],
    n_voters: int = DEFAULT_VOTERS_PER_COUNTY,
    n_iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
    turnout_sensitivity: float = DEFAULT_TURNOUT_SENSITIVITY,
    partisan_elasticity: float = DEFAULT_PARTISAN_ELASTICITY,
    statewide_shift: float = DEFAULT_STATEWIDE_SHIFT,
) -> Dict[str, Any]:
    """
    Run the full simulation for one county.

    Returns a dict with:
    - county_fips, county_name
    - predicted_margin_r: average R-D margin across iterations
    - margin_std: standard deviation across iterations
    - ci_low, ci_high: 90% confidence interval
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
    if margin_2016 is not None and pd.isna(margin_2016):
        margin_2016 = None

    # Turnout baseline from historical rates
    turnout_2020 = cf.get("turnout_2020", 0)
    turnout_2016 = cf.get("turnout_2016", 0)

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
        margin_2020, margin_2016, statewide_shift
    )

    # Run Monte Carlo iterations
    iteration_margins = []
    iteration_turnout_rates = []
    master_rng = np.random.RandomState(seed)

    # Create per-county seed from master + county FIPS
    county_seed_base = seed + hash(county_fips) % 10000

    for it in range(n_iterations):
        iter_seed = county_seed_base + it * 1000
        rng = np.random.RandomState(iter_seed)

        # 1. Generate population
        voters = generate_county_population(cf, n_voters, rng)

        # 2. Simulate turnout
        turned_out = simulate_turnout(
            voters, turnout_baseline_logit, rng, turnout_sensitivity
        )

        # 3. Simulate vote choice
        votes = simulate_vote_choice(
            voters, turned_out, partisan_baseline_logit, rng, partisan_elasticity
        )

        # 4. Aggregate
        n_voted = sum(turned_out)
        if n_voted == 0:
            iteration_margins.append(0.0)
            iteration_turnout_rates.append(0.0)
            continue

        n_r = sum(1 for v in votes if v == 1)
        n_d = sum(1 for v in votes if v == 0)
        total_2party = n_r + n_d

        if total_2party > 0:
            margin_r = (n_r - n_d) / total_2party
        else:
            margin_r = 0.0

        iteration_margins.append(margin_r)
        iteration_turnout_rates.append(n_voted / n_voters)

    # Compute summary statistics
    margins = np.array(iteration_margins)
    turnout_rates = np.array(iteration_turnout_rates)

    predicted_margin = float(np.mean(margins))
    margin_std = float(np.std(margins))
    ci_low = float(np.percentile(margins, 5))
    ci_high = float(np.percentile(margins, 95))

    return {
        "county_fips": county_fips,
        "county_name": county_name,
        "predicted_margin_r": round(predicted_margin, 6),
        "margin_std": round(margin_std, 6),
        "ci_low": round(ci_low, 6),
        "ci_high": round(ci_high, 6),
        "avg_turnout_rate": round(float(np.mean(turnout_rates)), 4),
        "n_iterations": n_iterations,
    }


def run_full_simulation(
    features_path: str = None,
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
    df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)

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
        print(f"  Statewide margin (pop-weighted): would need county pop for exact)")

    return results_df
