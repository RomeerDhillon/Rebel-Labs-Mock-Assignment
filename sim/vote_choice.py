"""
Vote choice model for the voter-level behavioral simulation.

For each voter who turns out, assigns a probability of voting Republican
(vs. Democratic) using a logistic model with interpretable coefficients.

Inputs to the model:
- County historical partisan baseline (from 2016+2020 average margin)
- Party registration (strongest predictor)
- Race/ethnicity (from national exit poll priors, pre-2024)
- Education (college realignment effect, documented since 2016)
- Age (mild age gradient)
- Urbanicity (urban-rural divide)

All coefficients are derived from publicly documented patterns in
pre-2024 elections and exit polls. No 2024 results are used.
"""

import numpy as np
from typing import Dict, Any, List


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        z = np.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = np.exp(x)
        return z / (1.0 + z)


# -----------------------------------------------------------------------
# Vote choice logit adjustments
# Positive = more likely Republican, Negative = more likely Democratic
#
# Sources:
# - 2020 National Exit Polls (CNN/Edison)
# - 2020 NC-specific exit poll (where available)
# - Catalist/TargetSmart group analysis of NC 2020
# - Pew Research validated voter studies
#
# These are ADDITIVE shifts on top of the county baseline.
# -----------------------------------------------------------------------

PARTY_VOTE_LOGIT = {
    "rep": 0.25,    # Registered R → lean R (on top of county baseline)
    "dem": -0.25,   # Registered D → lean D
    "unaf": 0.0,    # Unaffiliated → follow county baseline + other demographics
}

RACE_VOTE_LOGIT = {
    "white": 0.05,    # White voters lean R
    "black": -0.35,   # Black voters lean D
    "hispanic": -0.08, # Hispanic voters lean D
    "other": -0.05,   # Asian/other lean D
}

EDUCATION_VOTE_LOGIT = {
    "college": -0.07,   # College-educated shifted D post-2016
    "no_college": 0.03, # Non-college shifted R
}

AGE_VOTE_LOGIT = {
    "18-24": -0.04,   # Younger voters lean D
    "25-34": -0.02,
    "35-44": -0.01,
    "45-54": 0.01,
    "55-64": 0.02,
    "65+": 0.03,      # Older voters lean R (mild effect)
}

URBAN_VOTE_LOGIT = {
    "urban": -0.03,
    "suburban": 0.0,
    "rural": 0.03,
}

SEX_VOTE_LOGIT = {
    "M": 0.02,   # Men lean slightly R
    "F": -0.02,  # Women lean slightly D
}


def compute_vote_probability_r(
    voter: Dict[str, Any],
    county_baseline_logit: float,
    partisan_elasticity: float = 1.0,
) -> float:
    """
    Compute the probability that a voter who turns out votes Republican.

    Parameters
    ----------
    voter : dict
        Synthetic voter with attributes.
    county_baseline_logit : float
        County-level partisan baseline in logit space, derived from
        historical election margins (e.g., average of 2016+2020).
    partisan_elasticity : float
        Multiplier on demographic effects. 1.0 = default.
        >1.0 amplifies demographic polarization,
        <1.0 shrinks effects toward the county baseline.

    Returns
    -------
    float
        Probability of voting Republican, in [0, 1].
    """
    logit = county_baseline_logit

    # Demographic adjustments
    logit += partisan_elasticity * PARTY_VOTE_LOGIT.get(voter["party_reg"], 0.0)
    logit += partisan_elasticity * RACE_VOTE_LOGIT.get(voter["race"], 0.0)
    logit += partisan_elasticity * EDUCATION_VOTE_LOGIT.get(voter["education"], 0.0)
    logit += partisan_elasticity * AGE_VOTE_LOGIT.get(voter["age_band"], 0.0)
    logit += partisan_elasticity * URBAN_VOTE_LOGIT.get(voter["urban_rural"], 0.0)
    logit += partisan_elasticity * SEX_VOTE_LOGIT.get(voter["sex"], 0.0)

    return _sigmoid(logit)


def compute_county_partisan_baseline(
    margin_r_recent: float,
    margin_r_prior: float = None,
    statewide_shift: float = 0.0,
) -> float:
    """
    Compute the county partisan baseline in logit space.

    This baseline represents the RESIDUAL county partisan lean
    after accounting for demographics. Since synthetic voters are
    drawn from county demographic distributions, the demographics
    already encode much of the county lean. This baseline captures
    what's left: local political culture, candidate-specific effects,
    and other county-specific factors.

    We use a scaled-down version of the raw margin to avoid
    double-counting demographics.

    Parameters
    ----------
    margin_r_recent : float
        Most recent presidential margin (R - D) / (R + D). E.g. 2020.
    margin_r_prior : float or None
        Prior presidential margin. E.g. 2016.
    statewide_shift : float
        Uniform statewide shift to apply (in margin space).

    Returns
    -------
    float
        Partisan baseline in logit space.
    """
    if margin_r_prior is not None and not np.isnan(margin_r_prior):
        avg_margin = 0.6 * margin_r_recent + 0.4 * margin_r_prior
    else:
        avg_margin = margin_r_recent

    # Apply statewide shift
    avg_margin += statewide_shift

    # The county historical margin is the primary anchor.
    # Demographics provide small modulations on top of this.
    # Scale factor < 1.0 accounts for partial overlap between
    # county history and demographic composition.
    residual_scale = 1.0
    scaled_margin = avg_margin * residual_scale

    # Convert margin to logit
    # margin = (R - D) / (R + D) = 2 * R_share - 1
    # R_share = (margin + 1) / 2
    r_share = np.clip((scaled_margin + 1) / 2, 0.02, 0.98)
    return np.log(r_share / (1 - r_share))


def simulate_vote_choice(
    voters: List[Dict[str, Any]],
    turned_out: List[bool],
    county_baseline_logit: float,
    rng: np.random.RandomState,
    partisan_elasticity: float = 1.0,
) -> List[int]:
    """
    Simulate vote choice for voters who turned out.

    Returns a list with the same length as voters:
    - 1 = voted Republican
    - 0 = voted Democratic
    - -1 = did not vote (stayed home)
    """
    n = len(voters)
    votes = [-1] * n

    for i in range(n):
        if not turned_out[i]:
            continue

        prob_r = compute_vote_probability_r(
            voters[i], county_baseline_logit, partisan_elasticity
        )
        votes[i] = 1 if rng.random() < prob_r else 0

    return votes
