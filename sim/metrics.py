"""
Evaluation metrics for the voter simulation.

Compares predicted county margins against actual margins.
Used for backtesting (against 2020) and final evaluation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from scipy import stats


def compute_metrics(
    predicted: np.ndarray,
    actual: np.ndarray,
) -> Dict[str, float]:
    """
    Compute evaluation metrics for county-level margin predictions.

    Parameters
    ----------
    predicted : array-like
        Predicted R-D margins for each county.
    actual : array-like
        Actual R-D margins for each county.

    Returns
    -------
    dict with keys:
    - pearson_r: Pearson correlation
    - mae: Mean absolute error
    - rmse: Root mean squared error
    - directional_accuracy: Fraction of counties where predicted and
      actual signs match
    - max_error: Largest absolute error across counties
    - median_error: Median absolute error
    """
    predicted = np.asarray(predicted, dtype=float)
    actual = np.asarray(actual, dtype=float)

    # Remove NaN pairs
    mask = ~(np.isnan(predicted) | np.isnan(actual))
    predicted = predicted[mask]
    actual = actual[mask]

    if len(predicted) == 0:
        return {
            "pearson_r": np.nan,
            "mae": np.nan,
            "rmse": np.nan,
            "directional_accuracy": np.nan,
            "max_error": np.nan,
            "median_error": np.nan,
            "n_counties": 0,
        }

    # Pearson correlation
    r, p_value = stats.pearsonr(predicted, actual)

    # Errors
    errors = np.abs(predicted - actual)
    mae = float(np.mean(errors))
    rmse = float(np.sqrt(np.mean((predicted - actual) ** 2)))
    max_error = float(np.max(errors))
    median_error = float(np.median(errors))

    # Directional accuracy
    pred_sign = np.sign(predicted)
    actual_sign = np.sign(actual)
    directional_accuracy = float(np.mean(pred_sign == actual_sign))

    return {
        "pearson_r": round(float(r), 4),
        "p_value": round(float(p_value), 6),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "directional_accuracy": round(directional_accuracy, 4),
        "max_error": round(max_error, 4),
        "median_error": round(median_error, 4),
        "n_counties": int(len(predicted)),
    }


def baseline_prior_margin(
    prior_margins: np.ndarray,
) -> np.ndarray:
    """
    Simple baseline: predict the prior election margin as-is.

    This is the baseline to beat — if the simulation can't do better
    than "just use the last election's margin," it's not adding value.
    """
    return np.asarray(prior_margins, dtype=float)


def compare_to_baseline(
    predicted: np.ndarray,
    actual: np.ndarray,
    baseline: np.ndarray,
) -> Dict[str, Dict[str, float]]:
    """
    Compare simulation predictions against a baseline.

    Returns metrics for both the simulation and the baseline.
    """
    sim_metrics = compute_metrics(predicted, actual)
    base_metrics = compute_metrics(baseline, actual)

    return {
        "simulation": sim_metrics,
        "baseline": base_metrics,
        "improvement": {
            "mae_improvement": round(base_metrics["mae"] - sim_metrics["mae"], 4),
            "rmse_improvement": round(base_metrics["rmse"] - sim_metrics["rmse"], 4),
            "correlation_improvement": round(
                sim_metrics["pearson_r"] - base_metrics["pearson_r"], 4
            ),
            "directional_improvement": round(
                sim_metrics["directional_accuracy"] - base_metrics["directional_accuracy"], 4
            ),
        },
    }


def print_metrics_report(
    metrics: Dict[str, float],
    label: str = "Model",
) -> None:
    """Print a formatted metrics report."""
    print(f"\n{'='*50}")
    print(f"  {label} Evaluation")
    print(f"{'='*50}")
    print(f"  Counties evaluated: {metrics.get('n_counties', 'N/A')}")
    print(f"  Pearson correlation: {metrics.get('pearson_r', 'N/A')}")
    print(f"  Mean Absolute Error: {metrics.get('mae', 'N/A')}")
    print(f"  RMSE:                {metrics.get('rmse', 'N/A')}")
    print(f"  Directional accuracy:{metrics.get('directional_accuracy', 'N/A')}")
    print(f"  Median error:        {metrics.get('median_error', 'N/A')}")
    print(f"  Max error:           {metrics.get('max_error', 'N/A')}")
    print(f"{'='*50}")
