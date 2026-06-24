"""Tests for sim.turnout — turnout probability and simulation."""

import numpy as np
import pytest

from sim.turnout import (
    compute_turnout_probability,
    compute_turnout_probabilities,
    compute_county_baseline_logit,
    simulate_turnout,
)


class TestComputeCountyBaselineLogit:
    def test_fifty_percent(self):
        result = compute_county_baseline_logit(0.5)
        assert result == pytest.approx(0.0, abs=0.01)

    def test_high_turnout(self):
        result = compute_county_baseline_logit(0.8)
        assert result > 0

    def test_low_turnout(self):
        result = compute_county_baseline_logit(0.3)
        assert result < 0

    def test_clips_extreme_low(self):
        # Should clip to 0.1, not blow up
        result = compute_county_baseline_logit(0.0)
        assert np.isfinite(result)

    def test_clips_extreme_high(self):
        result = compute_county_baseline_logit(1.0)
        assert np.isfinite(result)

    def test_monotonic(self):
        rates = [0.2, 0.4, 0.6, 0.8]
        logits = [compute_county_baseline_logit(r) for r in rates]
        assert all(logits[i] < logits[i + 1] for i in range(len(logits) - 1))


class TestComputeTurnoutProbability:
    def _make_voter(self, age="45-54", party="unaf", urban="suburban",
                    education="no_college", race="white"):
        return {
            "age_band": age,
            "party_reg": party,
            "urban_rural": urban,
            "education": education,
            "race": race,
        }

    def test_returns_valid_probability(self):
        voter = self._make_voter()
        prob = compute_turnout_probability(voter, 0.5)
        assert 0 < prob < 1

    def test_older_voters_higher_turnout(self):
        young = compute_turnout_probability(self._make_voter(age="18-24"), 0.5)
        old = compute_turnout_probability(self._make_voter(age="65+"), 0.5)
        assert old > young

    def test_partisan_higher_than_unaffiliated(self):
        rep = compute_turnout_probability(self._make_voter(party="rep"), 0.5)
        unaf = compute_turnout_probability(self._make_voter(party="unaf"), 0.5)
        assert rep > unaf

    def test_college_higher_turnout(self):
        college = compute_turnout_probability(self._make_voter(education="college"), 0.5)
        no_college = compute_turnout_probability(self._make_voter(education="no_college"), 0.5)
        assert college > no_college

    def test_sensitivity_zero_equals_baseline(self):
        voter = self._make_voter()
        baseline_logit = 0.5
        prob = compute_turnout_probability(voter, baseline_logit, turnout_sensitivity=0.0)
        from sim.utils import sigmoid
        expected = float(sigmoid(np.array([baseline_logit]))[0])
        assert prob == pytest.approx(expected, abs=1e-6)


class TestComputeTurnoutProbabilities:
    def test_vectorized_matches_scalar(self):
        voters = {
            "age_band": np.array(["18-24", "65+"]),
            "party_reg": np.array(["dem", "rep"]),
            "urban_rural": np.array(["urban", "rural"]),
            "education": np.array(["college", "no_college"]),
            "race": np.array(["white", "black"]),
        }
        probs = compute_turnout_probabilities(voters, 0.5)
        assert probs.shape == (2,)

        # Compare with scalar version
        for i in range(2):
            v = {k: voters[k][i] for k in voters}
            scalar = compute_turnout_probability(v, 0.5)
            assert probs[i] == pytest.approx(scalar, abs=1e-10)


class TestSimulateTurnout:
    def test_returns_bool_array(self):
        voters = {
            "age_band": np.array(["45-54"] * 100),
            "party_reg": np.array(["rep"] * 100),
            "urban_rural": np.array(["suburban"] * 100),
            "education": np.array(["college"] * 100),
            "race": np.array(["white"] * 100),
        }
        rng = np.random.RandomState(42)
        result = simulate_turnout(voters, 0.5, rng)
        assert result.dtype == bool
        assert len(result) == 100

    def test_reproducible_with_seed(self):
        voters = {
            "age_band": np.array(["45-54"] * 50),
            "party_reg": np.array(["rep"] * 50),
            "urban_rural": np.array(["suburban"] * 50),
            "education": np.array(["college"] * 50),
            "race": np.array(["white"] * 50),
        }
        rng1 = np.random.RandomState(42)
        result1 = simulate_turnout(voters, 0.5, rng1)
        rng2 = np.random.RandomState(42)
        result2 = simulate_turnout(voters, 0.5, rng2)
        assert np.array_equal(result1, result2)
