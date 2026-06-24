"""
Shared utility functions for the voter simulation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import warnings


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid, vectorized.

    Works on scalars, 1-D arrays, or N-D arrays.
    """
    x = np.asarray(x, dtype=float)
    out = np.empty_like(x)
    pos = x >= 0
    neg = ~pos
    # For x >= 0: 1 / (1 + exp(-x))
    z_pos = np.exp(-x[pos])
    out[pos] = 1.0 / (1.0 + z_pos)
    # For x < 0: exp(x) / (1 + exp(x))
    z_neg = np.exp(x[neg])
    out[neg] = z_neg / (1.0 + z_neg)
    return out


def logit(p: float) -> float:
    """Convert probability to log-odds. Clips to avoid ±inf."""
    p = np.clip(p, 1e-6, 1.0 - 1e-6)
    return float(np.log(p / (1.0 - p)))


def validate_county_features(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean a county features DataFrame.

    Logs warnings for anomalies but does not drop rows, so the
    simulation always runs on all available counties.

    Returns the cleaned DataFrame.
    """
    df = df.copy()

    # Ensure county_fips is zero-padded string
    df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)

    # Check for duplicates
    dupes = df["county_fips"].duplicated()
    if dupes.any():
        dupe_fips = df.loc[dupes, "county_fips"].tolist()
        warnings.warn(f"Duplicate county FIPS codes found: {dupe_fips}")
        df = df.drop_duplicates(subset="county_fips", keep="first")

    # Validate margin columns are in [-1, 1]
    margin_cols = [c for c in df.columns if c.startswith("margin_r_")]
    for col in margin_cols:
        if col in df.columns:
            out_of_range = (df[col].abs() > 1.0) & df[col].notna()
            if out_of_range.any():
                bad = df.loc[out_of_range, ["county_fips", col]]
                warnings.warn(f"Margin column {col} has values outside [-1,1]: {bad.to_dict('records')}")
                df.loc[out_of_range, col] = np.clip(df.loc[out_of_range, col], -1.0, 1.0)

    # Validate demographic percentages in [0, 1]
    pct_cols = [c for c in df.columns if c.startswith("pct_") or c.endswith("_share")]
    for col in pct_cols:
        if col in df.columns:
            out_of_range = ((df[col] < 0) | (df[col] > 1.0)) & df[col].notna()
            if out_of_range.any():
                warnings.warn(f"Column {col} has values outside [0,1], clipping.")
                df[col] = df[col].clip(0.0, 1.0)

    # Validate populations are positive
    if "total_pop" in df.columns:
        bad_pop = (df["total_pop"] <= 0) & df["total_pop"].notna()
        if bad_pop.any():
            warnings.warn(f"Counties with non-positive population: {df.loc[bad_pop, 'county_fips'].tolist()}")

    n_counties = len(df)
    if n_counties != 100:
        warnings.warn(f"Expected 100 NC counties, found {n_counties}")

    return df
