"""Tests for sim.utils — shared sigmoid, logit, and validation."""

import numpy as np
import pandas as pd
import pytest
import warnings

from sim.utils import sigmoid, logit, validate_county_features


class TestSigmoid:
    def test_zero(self):
        assert sigmoid(np.array([0.0]))[0] == pytest.approx(0.5)

    def test_large_positive(self):
        result = sigmoid(np.array([100.0]))[0]
        assert result == pytest.approx(1.0, abs=1e-10)

    def test_large_negative(self):
        result = sigmoid(np.array([-100.0]))[0]
        assert result == pytest.approx(0.0, abs=1e-10)

    def test_symmetry(self):
        x = np.array([2.0, -2.0])
        results = sigmoid(x)
        assert results[0] + results[1] == pytest.approx(1.0)

    def test_vectorized(self):
        x = np.array([-1.0, 0.0, 1.0])
        results = sigmoid(x)
        assert results.shape == (3,)
        assert results[1] == pytest.approx(0.5)
        assert results[0] < 0.5
        assert results[2] > 0.5

    def test_monotonic(self):
        x = np.linspace(-5, 5, 100)
        results = sigmoid(x)
        assert np.all(np.diff(results) > 0)

    def test_scalar_input(self):
        result = sigmoid(np.float64(0.0))
        assert float(result) == pytest.approx(0.5)


class TestLogit:
    def test_half(self):
        assert logit(0.5) == pytest.approx(0.0)

    def test_inverse_of_sigmoid(self):
        for p in [0.1, 0.25, 0.5, 0.75, 0.9]:
            assert sigmoid(np.array([logit(p)]))[0] == pytest.approx(p, abs=1e-5)

    def test_clips_extreme_values(self):
        # Should not return inf
        result = logit(0.0)
        assert np.isfinite(result)
        result = logit(1.0)
        assert np.isfinite(result)


class TestValidateCountyFeatures:
    def _make_df(self, n=5):
        return pd.DataFrame({
            "county_fips": [f"3700{i}" for i in range(1, n + 1)],
            "county_name": [f"County{i}" for i in range(1, n + 1)],
            "margin_r_2020": np.random.uniform(-0.5, 0.5, n),
            "total_pop": np.random.randint(10000, 500000, n),
            "pct_white": np.random.uniform(0.3, 0.9, n),
            "reg_dem_share": np.full(n, 0.33),
            "reg_rep_share": np.full(n, 0.33),
            "reg_unaf_share": np.full(n, 0.34),
        })

    def test_basic_pass(self):
        df = self._make_df()
        result = validate_county_features(df)
        assert len(result) == 5

    def test_deduplicates_fips(self):
        df = self._make_df(3)
        df.loc[2, "county_fips"] = df.loc[0, "county_fips"]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = validate_county_features(df)
            assert len(result) == 2
            assert any("Duplicate" in str(warning.message) for warning in w)

    def test_clips_margins_out_of_range(self):
        df = self._make_df(3)
        df.loc[0, "margin_r_2020"] = 1.5
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = validate_county_features(df)
            assert result.loc[0, "margin_r_2020"] <= 1.0

    def test_warns_wrong_county_count(self):
        df = self._make_df(5)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_county_features(df)
            assert any("Expected 100" in str(warning.message) for warning in w)

    def test_pads_fips(self):
        df = self._make_df(2)
        df.loc[0, "county_fips"] = "37001"
        result = validate_county_features(df)
        assert all(len(f) == 5 for f in result["county_fips"])
