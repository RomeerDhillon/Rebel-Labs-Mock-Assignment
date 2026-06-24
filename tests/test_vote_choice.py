"""Tests for sim.vote_choice — vote choice model and baseline computation."""

import numpy as np
import pytest

from sim.vote_choice import (
    compute_vote_probability_r,
    compute_vote_probabilities_r,
    compute_county_partisan_baseline,
    simulate_vote_choice,
    RESIDUAL_SCALE,
)


class TestComputeCountyPartisanBaseline:
    def test_neutral_margin(self):
        result = compute_county_partisan_baseline(0.0)
        # margin=0 → R_share=0.5 → logit=0 (after scaling)
        # With RESIDUAL_SCALE < 1: scaled_margin ~ 0 → logit ~ 0
        assert result == pytest.approx(0.0, abs=0.05)

    def test_strong_r_margin(self):
        result = compute_county_partisan_baseline(0.5)
        assert result > 0

    def test_strong_d_margin(self):
        result = compute_county_partisan_baseline(-0.5)
        assert result < 0

    def test_with_prior(self):
        result_with_prior = compute_county_partisan_baseline(0.1, margin_r_prior=0.2)
        result_no_prior = compute_county_partisan_baseline(0.1)
        # With prior > recent, baseline should be pulled upward
        assert result_with_prior > result_no_prior

    def test_with_trend(self):
        # Positive trend means county is getting more R
        result_trend = compute_county_partisan_baseline(0.1, 0.0, margin_trend=0.1)
        result_no_trend = compute_county_partisan_baseline(0.1, 0.0, margin_trend=None)
        assert result_trend > result_no_trend

    def test_statewide_shift_applied(self):
        result_shift = compute_county_partisan_baseline(0.0, statewide_shift=0.05)
        result_no_shift = compute_county_partisan_baseline(0.0, statewide_shift=0.0)
        assert result_shift > result_no_shift

    def test_nan_prior_ignored(self):
        result = compute_county_partisan_baseline(0.1, margin_r_prior=float("nan"))
        result_none = compute_county_partisan_baseline(0.1, margin_r_prior=None)
        assert result == pytest.approx(result_none)

    def test_residual_scale_effect(self):
        # Verify residual scale < 1.0
        assert RESIDUAL_SCALE < 1.0
        assert RESIDUAL_SCALE > 0.5

    def test_extreme_margins_clipped(self):
        result_high = compute_county_partisan_baseline(0.99)
        result_low = compute_county_partisan_baseline(-0.99)
        assert np.isfinite(result_high)
        assert np.isfinite(result_low)


class TestComputeVoteProbabilityR:
    def _make_voter(self, party="unaf", race="white", education="no_college",
                    age="45-54", urban="suburban", sex="M"):
        return {
            "party_reg": party,
            "race": race,
            "education": education,
            "age_band": age,
            "urban_rural": urban,
            "sex": sex,
        }

    def test_returns_valid_probability(self):
        voter = self._make_voter()
        prob = compute_vote_probability_r(voter, 0.0)
        assert 0 < prob < 1

    def test_neutral_baseline_near_half(self):
        voter = self._make_voter()
        prob = compute_vote_probability_r(voter, 0.0)
        # With small coefficients, should be near 0.5
        assert 0.4 < prob < 0.6

    def test_rep_voter_leans_r(self):
        rep = compute_vote_probability_r(self._make_voter(party="rep"), 0.0)
        dem = compute_vote_probability_r(self._make_voter(party="dem"), 0.0)
        assert rep > dem

    def test_black_voter_leans_d(self):
        black = compute_vote_probability_r(self._make_voter(race="black"), 0.0)
        white = compute_vote_probability_r(self._make_voter(race="white"), 0.0)
        assert black < white

    def test_college_leans_d(self):
        college = compute_vote_probability_r(self._make_voter(education="college"), 0.0)
        no_col = compute_vote_probability_r(self._make_voter(education="no_college"), 0.0)
        assert college < no_col

    def test_elasticity_zero_equals_baseline(self):
        voter = self._make_voter()
        baseline_logit = 0.3
        prob = compute_vote_probability_r(voter, baseline_logit, partisan_elasticity=0.0)
        from sim.utils import sigmoid
        expected = float(sigmoid(np.array([baseline_logit]))[0])
        assert prob == pytest.approx(expected, abs=1e-6)


class TestComputeVoteProbabilitiesR:
    def test_vectorized_matches_scalar(self):
        voters = {
            "party_reg": np.array(["rep", "dem", "unaf"]),
            "race": np.array(["white", "black", "hispanic"]),
            "education": np.array(["college", "no_college", "college"]),
            "age_band": np.array(["18-24", "45-54", "65+"]),
            "urban_rural": np.array(["urban", "suburban", "rural"]),
            "sex": np.array(["M", "F", "M"]),
        }
        probs = compute_vote_probabilities_r(voters, 0.0)
        assert probs.shape == (3,)

        for i in range(3):
            v = {k: voters[k][i] for k in voters}
            scalar = compute_vote_probability_r(v, 0.0)
            assert probs[i] == pytest.approx(scalar, abs=1e-10)


class TestSimulateVoteChoice:
    def test_basic_output(self):
        voters = {
            "party_reg": np.array(["rep"] * 100),
            "race": np.array(["white"] * 100),
            "education": np.array(["no_college"] * 100),
            "age_band": np.array(["45-54"] * 100),
            "urban_rural": np.array(["rural"] * 100),
            "sex": np.array(["M"] * 100),
        }
        turned_out = np.array([True] * 60 + [False] * 40)
        rng = np.random.RandomState(42)
        votes = simulate_vote_choice(voters, turned_out, 0.0, rng)
        assert len(votes) == 100
        assert np.sum(votes == -1) == 40  # non-voters
        assert np.sum(votes >= 0) == 60   # actual voters

    def test_all_abstain(self):
        voters = {
            "party_reg": np.array(["rep"] * 10),
            "race": np.array(["white"] * 10),
            "education": np.array(["no_college"] * 10),
            "age_band": np.array(["45-54"] * 10),
            "urban_rural": np.array(["rural"] * 10),
            "sex": np.array(["M"] * 10),
        }
        turned_out = np.array([False] * 10)
        rng = np.random.RandomState(42)
        votes = simulate_vote_choice(voters, turned_out, 0.0, rng)
        assert np.all(votes == -1)

    def test_reproducible(self):
        voters = {
            "party_reg": np.array(["rep", "dem", "unaf"] * 20),
            "race": np.array(["white", "black", "hispanic"] * 20),
            "education": np.array(["college", "no_college", "college"] * 20),
            "age_band": np.array(["18-24", "45-54", "65+"] * 20),
            "urban_rural": np.array(["urban", "suburban", "rural"] * 20),
            "sex": np.array(["M", "F", "M"] * 20),
        }
        turned_out = np.array([True] * 60)
        rng1 = np.random.RandomState(42)
        v1 = simulate_vote_choice(voters, turned_out, 0.0, rng1)
        rng2 = np.random.RandomState(42)
        v2 = simulate_vote_choice(voters, turned_out, 0.0, rng2)
        assert np.array_equal(v1, v2)
