"""Tests for sim.metrics — evaluation metric calculations."""

import numpy as np
import pytest

from sim.metrics import compute_metrics, compare_to_baseline


class TestComputeMetrics:
    def test_perfect_prediction(self):
        predicted = np.array([0.1, 0.2, -0.3, 0.4])
        actual = np.array([0.1, 0.2, -0.3, 0.4])
        m = compute_metrics(predicted, actual)
        assert m["mae"] == pytest.approx(0.0)
        assert m["rmse"] == pytest.approx(0.0)
        assert m["pearson_r"] == pytest.approx(1.0)
        assert m["directional_accuracy"] == pytest.approx(1.0)

    def test_directional_accuracy(self):
        predicted = np.array([0.1, -0.2, 0.3, -0.4])
        actual = np.array([0.05, -0.1, -0.1, -0.5])  # 3rd is wrong direction
        m = compute_metrics(predicted, actual)
        assert m["directional_accuracy"] == pytest.approx(0.75)

    def test_mae_and_rmse(self):
        predicted = np.array([0.1, 0.2])
        actual = np.array([0.0, 0.0])
        m = compute_metrics(predicted, actual)
        assert m["mae"] == pytest.approx(0.15)
        assert m["rmse"] == pytest.approx(np.sqrt(0.025), abs=1e-3)

    def test_handles_nan(self):
        predicted = np.array([0.1, float("nan"), 0.3, 0.2])
        actual = np.array([0.05, 0.2, float("nan"), 0.15])
        m = compute_metrics(predicted, actual)
        assert m["n_counties"] == 2  # Only 1st and 4th pairs are valid
        assert np.isfinite(m["mae"])

    def test_empty_input(self):
        m = compute_metrics(np.array([]), np.array([]))
        assert m["n_counties"] == 0
        assert np.isnan(m["mae"])

    def test_all_nan(self):
        predicted = np.array([float("nan"), float("nan")])
        actual = np.array([float("nan"), float("nan")])
        m = compute_metrics(predicted, actual)
        assert m["n_counties"] == 0

    def test_max_error(self):
        predicted = np.array([0.5, -0.1, 0.0])
        actual = np.array([0.0, -0.1, 0.3])
        m = compute_metrics(predicted, actual)
        assert m["max_error"] == pytest.approx(0.5)

    def test_median_error(self):
        predicted = np.array([0.1, 0.2, 0.5])
        actual = np.array([0.0, 0.0, 0.0])
        m = compute_metrics(predicted, actual)
        assert m["median_error"] == pytest.approx(0.2)


class TestCompareToBaseline:
    def test_returns_three_dicts(self):
        predicted = np.array([0.1, 0.2, -0.3])
        actual = np.array([0.05, 0.25, -0.35])
        baseline = np.array([0.0, 0.15, -0.2])
        result = compare_to_baseline(predicted, actual, baseline)
        assert "simulation" in result
        assert "baseline" in result
        assert "improvement" in result

    def test_improvement_positive_when_better(self):
        actual = np.array([0.1, 0.2, -0.3])
        # Simulation exactly right
        predicted = actual.copy()
        # Baseline off by 0.1
        baseline = actual + 0.1
        result = compare_to_baseline(predicted, actual, baseline)
        assert result["improvement"]["mae_improvement"] > 0
