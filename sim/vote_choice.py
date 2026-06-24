"""
Vote choice model for the voter-level behavioral simulation.

For each voter who turns out, assigns a probability of voting Republican
(vs. Democratic) using a logistic model with interpretable coefficients.

Inputs to the model:
- County historical partisan baseline (from weighted blend of recent margins)
- Party registration (strongest predictor)
- Race/ethnicity (from national exit poll priors, pre-2024)
- Education (college realignment effect, documented since 2016)
- Age (mild age gradient)
- Urbanicity (urban-rural divide)

All coefficients are derived from publicly documented patterns in
pre-2024 elections and exit polls. No 2024 results are used.

IMPORTANT: Coefficients are intentionally small because the county
baseline already captures most partisan lean. Demographics here
represent RESIDUAL effects — the marginal shift a voter's attributes
produce on top of their county's established pattern. Larger values
would double-count the demographic signal already embedded in
county history (demographics correlate r>0.7 with margins).
"""

import numpy as np
from typing import Dict, Any, List, Optional

from sim.utils import sigmoid


# -----------------------------------------------------------------------
# Vote choice logit adjustments (RESIDUAL effects)
# Positive = more likely Republican, Negative = more likely Democratic
#
# Sources:
# - 2020 National Exit Polls (CNN/Edison)
# - 2020 NC-specific exit poll (where available)
# - Catalist/TargetSmart group analysis of NC 2020
# - Pew Research validated voter studies
#
# These are ADDITIVE shifts on top of the county baseline.
# Scaled down from raw exit-poll differentials because the county
# baseline already captures most of the demographic-driven lean.
# -----------------------------------------------------------------------

PARTY_VOTE_LOGIT = {
    "rep": 0.10,    # Registered R → lean R (residual on top of county baseline)
    "dem": -0.10,   # Registered D → lean D
    "unaf": 0.0,    # Unaffiliated → follow county baseline + other demographics
}

RACE_VOTE_LOGIT = {
    "white": 0.02,    # White voters lean R (small residual)
    "black": -0.12,   # Black voters lean D (small residual; baseline captures most)
    "hispanic": -0.03, # Hispanic voters lean D
    "other": -0.02,   # Asian/other lean D
}

EDUCATION_VOTE_LOGIT = {
    "college": -0.03,   # College-educated shifted D post-2016
    "no_college": 0.015, # Non-college shifted R
}

AGE_VOTE_LOGIT = {
    "18-24": -0.03,   # Younger voters lean D
    "25-34": -0.015,
    "35-44": -0.005,
    "45-54": 0.005,
    "55-64": 0.015,
    "65+": 0.02,      # Older voters lean R (mild effect)
}

URBAN_VOTE_LOGIT = {
    "urban": -0.02,
    "suburban": 0.0,
    "rural": 0.02,
}

SEX_VOTE_LOGIT = {
    "M": 0.015,   # Men lean slightly R
    "F": -0.015,  # Women lean slightly D
}

# Lookup arrays for vectorized computation. Built once at import time.
_PARTY_KEYS = list(PARTY_VOTE_LOGIT.keys())
_RACE_KEYS = list(RACE_VOTE_LOGIT.keys())
_EDU_KEYS = list(EDUCATION_VOTE_LOGIT.keys())
_AGE_KEYS = list(AGE_VOTE_LOGIT.keys())
_URBAN_KEYS = list(URBAN_VOTE_LOGIT.keys())
_SEX_KEYS = list(SEX_VOTE_LOGIT.keys())


def _build_lookup(d: Dict[str, float], keys: List[str]) -> Dict[str, float]:
    """Return the dict unchanged — kept for clarity."""
    return d


def compute_vote_probabilities_r(
    voters: Dict[str, np.ndarray],
    county_baseline_logit: float,
    partisan_elasticity: float = 1.0,
) -> np.ndarray:
    """
    Compute Republican vote probability for all voters (vectorized).

    Parameters
    ----------
    voters : dict of arrays
        Keys: 'party_reg', 'race', 'education', 'age_band',
        'urban_rural', 'sex' — each a 1-D array of strings.
    county_baseline_logit : float
        County-level partisan baseline in logit space.
    partisan_elasticity : float
        Multiplier on demographic effects.

    Returns
    -------
    np.ndarray
        Probability of voting Republican for each voter, shape (n,).
    """
    n = len(voters["party_reg"])
    logits = np.full(n, county_baseline_logit)

    # Vectorized lookup for each attribute
    for attr, lookup in [
        ("party_reg", PARTY_VOTE_LOGIT),
        ("race", RACE_VOTE_LOGIT),
        ("education", EDUCATION_VOTE_LOGIT),
        ("age_band", AGE_VOTE_LOGIT),
        ("urban_rural", URBAN_VOTE_LOGIT),
        ("sex", SEX_VOTE_LOGIT),
    ]:
        arr = voters[attr]
        shifts = np.array([lookup.get(v, 0.0) for v in arr])
        logits += partisan_elasticity * shifts

    return sigmoid(logits)


# Backward-compatible scalar interface (used by tests / external callers)
def compute_vote_probability_r(
    voter: Dict[str, Any],
    county_baseline_logit: float,
    partisan_elasticity: float = 1.0,
) -> float:
    """Scalar wrapper — computes P(R) for a single voter dict."""
    batch = {k: np.array([voter[k]]) for k in
             ["party_reg", "race", "education", "age_band", "urban_rural", "sex"]}
    return float(compute_vote_probabilities_r(batch, county_baseline_logit, partisan_elasticity)[0])


# Residual scale: fraction of the raw historical margin used as baseline.
# Set < 1.0 to account for overlap between county history and the
# demographic composition of synthetic voters. Demographics (race,
# registration, education) correlate r > 0.7 with county margins,
# so using the full raw margin AND adding demographic shifts
# double-counts ~15-20% of the partisan signal.
RESIDUAL_SCALE = 0.98


def compute_county_partisan_baseline(
    margin_r_recent: float,
    margin_r_prior: Optional[float] = None,
    statewide_shift: float = 0.0,
    margin_trend: Optional[float] = None,
) -> float:
    """
    Compute the county partisan baseline in logit space.

    Uses a weighted blend of recent election margins plus an
    optional extrapolated trend, then attenuates by RESIDUAL_SCALE
    to avoid double-counting demographics.

    Parameters
    ----------
    margin_r_recent : float
        Most recent presidential margin (R - D) / (R + D). E.g. 2020.
    margin_r_prior : float or None
        Prior presidential margin. E.g. 2016.
    statewide_shift : float
        Statewide shift to apply (in margin space).
    margin_trend : float or None
        Observed trend (recent - prior). If provided, a fraction
        is extrapolated forward.

    Returns
    -------
    float
        Partisan baseline in logit space.
    """
    if margin_r_prior is not None and not np.isnan(margin_r_prior):
        # Weighted blend: 60% recent, 30% prior, 10% trend-extrapolated
        blended = 0.60 * margin_r_recent + 0.30 * margin_r_prior
        if margin_trend is not None and not np.isnan(margin_trend):
            # Extrapolate: carry forward 50% of the observed trend
            blended += 0.10 * (margin_r_recent + margin_trend * 0.5)
        else:
            blended += 0.10 * margin_r_recent
    else:
        blended = margin_r_recent

    # Apply statewide shift
    blended += statewide_shift

    # Attenuate to avoid double-counting demographics
    scaled_margin = blended * RESIDUAL_SCALE

    # Convert margin to logit
    # margin = (R - D) / (R + D) = 2 * R_share - 1
    # R_share = (margin + 1) / 2
    r_share = np.clip((scaled_margin + 1) / 2, 0.02, 0.98)
    return float(np.log(r_share / (1 - r_share)))


def simulate_vote_choice(
    voters: Dict[str, np.ndarray],
    turned_out: np.ndarray,
    county_baseline_logit: float,
    rng: np.random.RandomState,
    partisan_elasticity: float = 1.0,
) -> np.ndarray:
    """
    Simulate vote choice for voters who turned out (vectorized).

    Parameters
    ----------
    voters : dict of arrays
        Columnar voter attributes.
    turned_out : np.ndarray of bool
        True for voters who turned out.
    county_baseline_logit : float
        County partisan baseline in logit space.
    rng : RandomState
        For reproducibility.
    partisan_elasticity : float
        Multiplier on demographic effects.

    Returns
    -------
    np.ndarray of int
        1 = Republican, 0 = Democratic, -1 = did not vote.
    """
    n = len(turned_out)
    votes = np.full(n, -1, dtype=np.int8)

    voted_mask = turned_out
    n_voted = int(np.sum(voted_mask))
    if n_voted == 0:
        return votes

    # Subset voters who turned out
    voted_voters = {k: v[voted_mask] for k, v in voters.items()}

    probs_r = compute_vote_probabilities_r(
        voted_voters, county_baseline_logit, partisan_elasticity
    )

    draws = rng.random(n_voted)
    votes[voted_mask] = (draws < probs_r).astype(np.int8)

    return votes
