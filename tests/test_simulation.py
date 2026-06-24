"""Tests for sim.run_simulation — end-to-end county simulation."""

import numpy as np
import pytest

from sim.run_simulation import simulate_county


def _make_county_features(**overrides):
    defaults = {
        "county_fips": "37001",
        "county_name": "TestCounty",
        "margin_r_2020": 0.10,
        "margin_r_2016": 0.12,
        "margin_trend_16_20": -0.02,
        "avg_margin_r": 0.11,
        "turnout_2020": 50000,
        "turnout_2016": 45000,
        "reg_total": 70000,
        "median_age": 39.0,
        "pct_white": 0.60,
        "pct_black": 0.25,
        "pct_hispanic": 0.10,
        "pct_college": 0.30,
        "reg_dem_share": 0.33,
        "reg_rep_share": 0.33,
        "reg_unaf_share": 0.34,
        "urban_rural": "suburban",
    }
    defaults.update(overrides)
    return defaults


class TestSimulateCounty:
    def test_returns_required_keys(self):
        cf = _make_county_features()
        result = simulate_county(cf, n_voters=200, n_iterations=5, seed=42)
        for key in ["county_fips", "county_name", "predicted_margin_r",
                     "margin_std", "ci_low", "ci_high", "avg_turnout_rate",
                     "n_iterations"]:
            assert key in result, f"Missing key: {key}"

    def test_margin_in_valid_range(self):
        cf = _make_county_features()
        result = simulate_county(cf, n_voters=500, n_iterations=10, seed=42)
        assert -1 <= result["predicted_margin_r"] <= 1

    def test_ci_contains_mean(self):
        cf = _make_county_features()
        result = simulate_county(cf, n_voters=500, n_iterations=20, seed=42)
        assert result["ci_low"] <= result["predicted_margin_r"] <= result["ci_high"]

    def test_r_county_predicts_r(self):
        cf = _make_county_features(margin_r_2020=0.40, margin_r_2016=0.45)
        result = simulate_county(cf, n_voters=500, n_iterations=10, seed=42)
        assert result["predicted_margin_r"] > 0

    def test_d_county_predicts_d(self):
        cf = _make_county_features(margin_r_2020=-0.30, margin_r_2016=-0.28)
        result = simulate_county(cf, n_voters=500, n_iterations=10, seed=42)
        assert result["predicted_margin_r"] < 0

    def test_reproducible(self):
        cf = _make_county_features()
        r1 = simulate_county(cf, n_voters=500, n_iterations=10, seed=42)
        r2 = simulate_county(cf, n_voters=500, n_iterations=10, seed=42)
        assert r1["predicted_margin_r"] == r2["predicted_margin_r"]
        assert r1["margin_std"] == r2["margin_std"]

    def test_different_seeds_differ(self):
        cf = _make_county_features()
        r1 = simulate_county(cf, n_voters=500, n_iterations=10, seed=42)
        r2 = simulate_county(cf, n_voters=500, n_iterations=10, seed=99)
        # Different seeds should generally produce different results
        # (extremely unlikely to be exactly equal)
        assert r1["predicted_margin_r"] != r2["predicted_margin_r"]

    def test_turnout_rate_reasonable(self):
        cf = _make_county_features()
        result = simulate_county(cf, n_voters=500, n_iterations=10, seed=42)
        assert 0.3 < result["avg_turnout_rate"] < 1.0

    def test_nan_margin_fallback(self):
        cf = _make_county_features(margin_r_2020=float("nan"), avg_margin_r=0.05)
        result = simulate_county(cf, n_voters=200, n_iterations=5, seed=42)
        assert np.isfinite(result["predicted_margin_r"])

    def test_nan_all_margins_fallback(self):
        cf = _make_county_features(
            margin_r_2020=float("nan"),
            margin_r_2016=float("nan"),
            avg_margin_r=float("nan"),
        )
        result = simulate_county(cf, n_voters=200, n_iterations=5, seed=42)
        assert np.isfinite(result["predicted_margin_r"])

    def test_urbanicity_shift_flag(self):
        cf = _make_county_features(urban_rural="rural")
        r_urban = simulate_county(cf, n_voters=500, n_iterations=10, seed=42,
                                  use_urbanicity_shift=True)
        r_flat = simulate_county(cf, n_voters=500, n_iterations=10, seed=42,
                                 use_urbanicity_shift=False, statewide_shift=0.0)
        # Rural urbanicity shift is positive (R shift), so with it on,
        # margin should be slightly more R
        assert r_urban["predicted_margin_r"] >= r_flat["predicted_margin_r"] - 0.01

    def test_std_positive(self):
        cf = _make_county_features()
        result = simulate_county(cf, n_voters=500, n_iterations=20, seed=42)
        assert result["margin_std"] > 0
