"""
Turnout model for the voter-level behavioral simulation.

Assigns each synthetic voter a probability of turning out, then
draws a Bernoulli outcome. The model uses a logistic function with
interpretable coefficients derived from publicly known turnout patterns:

- Age: older voters turn out at higher rates
- Party registration: partisans turn out more than unaffiliated
- County baseline: calibrated to historical county turnout rates
- Urbanicity: slight urban/rural differential

Coefficients are set from publicly documented turnout differentials
in NC (NCSBE turnout reports, national CPS voting supplements).
No 2024 data is used.
"""

import numpy as np
from typing import Dict, List, Any

from sim.utils import sigmoid


# Turnout logit adjustments by attribute
# These represent additive shifts to the log-odds of turning out.
# Calibrated from CPS Nov 2020 voting supplement and NCSBE turnout data.

AGE_TURNOUT_LOGIT = {
    "18-24": -0.8,   # ~50% turnout
    "25-34": -0.4,   # ~57% turnout
    "35-44": -0.1,   # ~63% turnout
    "45-54": 0.1,    # ~68% turnout
    "55-64": 0.3,    # ~73% turnout
    "65+": 0.5,      # ~77% turnout
}

PARTY_TURNOUT_LOGIT = {
    "dem": 0.3,      # Registered partisans turn out more
    "rep": 0.4,      # Registered R slightly higher than D historically in NC
    "unaf": -0.4,    # Unaffiliated voters turn out less
}

URBAN_TURNOUT_LOGIT = {
    "urban": 0.05,
    "suburban": 0.10,
    "rural": -0.05,
}

EDUCATION_TURNOUT_LOGIT = {
    "college": 0.3,
    "no_college": -0.15,
}

RACE_TURNOUT_LOGIT = {
    "white": 0.1,
    "black": 0.0,     # Varies by year; roughly equal in 2020
    "hispanic": -0.3,  # Lower overall turnout
    "other": -0.2,
}


def compute_turnout_probabilities(
    voters: Dict[str, np.ndarray],
    county_baseline_logit: float,
    turnout_sensitivity: float = 1.0,
) -> np.ndarray:
    """
    Compute turnout probability for all voters (vectorized).

    Parameters
    ----------
    voters : dict of arrays
        Keys: 'age_band', 'party_reg', 'urban_rural', 'education',
        'race' — each a 1-D array of strings.
    county_baseline_logit : float
        County baseline turnout in logit space.
    turnout_sensitivity : float
        Multiplier on demographic effects.

    Returns
    -------
    np.ndarray
        Turnout probability for each voter, shape (n,).
    """
    n = len(voters["age_band"])
    logits = np.full(n, county_baseline_logit)

    for attr, lookup in [
        ("age_band", AGE_TURNOUT_LOGIT),
        ("party_reg", PARTY_TURNOUT_LOGIT),
        ("urban_rural", URBAN_TURNOUT_LOGIT),
        ("education", EDUCATION_TURNOUT_LOGIT),
        ("race", RACE_TURNOUT_LOGIT),
    ]:
        arr = voters[attr]
        shifts = np.array([lookup.get(v, 0.0) for v in arr])
        logits += turnout_sensitivity * shifts

    return sigmoid(logits)


# Backward-compatible scalar interface
def compute_turnout_probability(
    voter: Dict[str, Any],
    county_baseline_logit: float,
    turnout_sensitivity: float = 1.0,
) -> float:
    """Scalar wrapper — computes turnout probability for a single voter dict."""
    batch = {k: np.array([voter[k]]) for k in
             ["age_band", "party_reg", "urban_rural", "education", "race"]}
    return float(compute_turnout_probabilities(batch, county_baseline_logit, turnout_sensitivity)[0])


def compute_county_baseline_logit(
    historical_turnout_rate: float,
) -> float:
    """
    Convert a county's historical turnout rate to logit space.

    Parameters
    ----------
    historical_turnout_rate : float
        Fraction of registered voters who turned out (0 to 1).

    Returns
    -------
    float
        Logit (log-odds) of the turnout rate.
    """
    rate = np.clip(historical_turnout_rate, 0.1, 0.95)
    return float(np.log(rate / (1 - rate)))


def simulate_turnout(
    voters: Dict[str, np.ndarray],
    county_baseline_logit: float,
    rng: np.random.RandomState,
    turnout_sensitivity: float = 1.0,
) -> np.ndarray:
    """
    Simulate turnout for all voters (vectorized).

    Returns np.ndarray of bool (True = voted, False = stayed home).
    """
    turnout_probs = compute_turnout_probabilities(
        voters, county_baseline_logit, turnout_sensitivity
    )
    draws = rng.random(len(turnout_probs))
    return draws < turnout_probs
