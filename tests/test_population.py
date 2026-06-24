"""Tests for sim.population — synthetic voter generation."""

import numpy as np
import pytest

from sim.population import generate_county_population, _adjust_age_distribution, AGE_BANDS


class TestAdjustAgeDistribution:
    def test_sums_to_one(self):
        for age in [25, 35, 39, 45, 55]:
            dist = _adjust_age_distribution(AGE_BANDS.copy(), age)
            assert sum(dist.values()) == pytest.approx(1.0, abs=1e-10)

    def test_older_county_has_more_seniors(self):
        young_dist = _adjust_age_distribution(AGE_BANDS.copy(), 30.0)
        old_dist = _adjust_age_distribution(AGE_BANDS.copy(), 50.0)
        assert old_dist["65+"] > young_dist["65+"]
        assert young_dist["18-24"] > old_dist["18-24"]

    def test_state_average_unchanged(self):
        dist = _adjust_age_distribution(AGE_BANDS.copy(), 39.0)
        for band, share in AGE_BANDS.items():
            assert dist[band] == pytest.approx(share, abs=1e-10)

    def test_minimum_floor(self):
        # Even extreme ages should have at least 0.03 per band
        dist = _adjust_age_distribution(AGE_BANDS.copy(), 80.0)
        for band, share in dist.items():
            assert share >= 0.02  # After normalization, floor is approximate


class TestGenerateCountyPopulation:
    def _make_features(self, **overrides):
        defaults = {
            "county_fips": "37001",
            "county_name": "TestCounty",
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

    def test_returns_dict_of_arrays(self):
        cf = self._make_features()
        rng = np.random.RandomState(42)
        result = generate_county_population(cf, 100, rng)
        assert isinstance(result, dict)
        assert "age_band" in result
        assert "party_reg" in result
        assert len(result["age_band"]) == 100

    def test_all_keys_present(self):
        cf = self._make_features()
        rng = np.random.RandomState(42)
        result = generate_county_population(cf, 50, rng)
        expected_keys = {"age_band", "sex", "race", "education",
                        "party_reg", "urban_rural", "county_fips"}
        assert set(result.keys()) == expected_keys

    def test_valid_values(self):
        cf = self._make_features()
        rng = np.random.RandomState(42)
        result = generate_county_population(cf, 1000, rng)
        assert set(result["sex"]).issubset({"M", "F"})
        assert set(result["race"]).issubset({"white", "black", "hispanic", "other"})
        assert set(result["education"]).issubset({"college", "no_college"})
        assert set(result["party_reg"]).issubset({"dem", "rep", "unaf"})

    def test_race_distribution_approximate(self):
        cf = self._make_features(pct_white=0.80, pct_black=0.15, pct_hispanic=0.03)
        rng = np.random.RandomState(42)
        result = generate_county_population(cf, 10000, rng)
        white_frac = np.mean(result["race"] == "white")
        assert white_frac == pytest.approx(0.80, abs=0.03)

    def test_reproducible(self):
        cf = self._make_features()
        rng1 = np.random.RandomState(42)
        r1 = generate_county_population(cf, 100, rng1)
        rng2 = np.random.RandomState(42)
        r2 = generate_county_population(cf, 100, rng2)
        assert np.array_equal(r1["age_band"], r2["age_band"])
        assert np.array_equal(r1["party_reg"], r2["party_reg"])

    def test_nan_demographics_use_defaults(self):
        cf = self._make_features(
            pct_white=float("nan"),
            pct_black=float("nan"),
            pct_college=float("nan"),
            median_age=float("nan"),
        )
        rng = np.random.RandomState(42)
        result = generate_county_population(cf, 100, rng)
        assert len(result["age_band"]) == 100
        assert len(set(result["race"])) > 1

    def test_urban_rural_uniform(self):
        cf = self._make_features(urban_rural="urban")
        rng = np.random.RandomState(42)
        result = generate_county_population(cf, 100, rng)
        assert np.all(result["urban_rural"] == "urban")

    def test_county_fips_uniform(self):
        cf = self._make_features(county_fips="37183")
        rng = np.random.RandomState(42)
        result = generate_county_population(cf, 100, rng)
        assert np.all(result["county_fips"] == "37183")
