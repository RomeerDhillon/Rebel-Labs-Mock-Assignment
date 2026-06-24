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


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        z = np.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = np.exp(x)
        return z / (1.0 + z)


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


def compute_turnout_probability(
    voter: Dict[str, Any],
    county_baseline_logit: float,
    turnout_sensitivity: float = 1.0,
) -> float:
    """
    Compute the probability that a voter turns out.

    Parameters
    ----------
    voter : dict
        Synthetic voter with attributes (age_band, party_reg, etc.)
    county_baseline_logit : float
        County-level baseline turnout in logit space, calibrated from
        historical county turnout rates.
    turnout_sensitivity : float
        Multiplier on demographic effects. 1.0 = default.
        >1.0 amplifies demographic differentials,
        <1.0 shrinks them toward the county average.

    Returns
    -------
    float
        Probability of turning out, in [0, 1].
    """
    logit = county_baseline_logit

    # Add demographic adjustments scaled by sensitivity
    logit += turnout_sensitivity * AGE_TURNOUT_LOGIT.get(voter["age_band"], 0.0)
    logit += turnout_sensitivity * PARTY_TURNOUT_LOGIT.get(voter["party_reg"], 0.0)
    logit += turnout_sensitivity * URBAN_TURNOUT_LOGIT.get(voter["urban_rural"], 0.0)
    logit += turnout_sensitivity * EDUCATION_TURNOUT_LOGIT.get(voter["education"], 0.0)
    logit += turnout_sensitivity * RACE_TURNOUT_LOGIT.get(voter["race"], 0.0)

    return _sigmoid(logit)


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
    return np.log(rate / (1 - rate))


def simulate_turnout(
    voters: List[Dict[str, Any]],
    county_baseline_logit: float,
    rng: np.random.RandomState,
    turnout_sensitivity: float = 1.0,
) -> List[bool]:
    """
    Simulate turnout for a list of voters.

    Returns a list of booleans (True = voted, False = stayed home).
    """
    turnout_probs = np.array([
        compute_turnout_probability(v, county_baseline_logit, turnout_sensitivity)
        for v in voters
    ])

    draws = rng.random(len(voters))
    return list(draws < turnout_probs)
