"""Pure retrospective statistics and coverage; no API dependencies."""
import numpy as np
import pandas as pd
from .models import Accuracy, Coverage


def coverage(frame: pd.DataFrame) -> Coverage:
    hourly = frame.startTime.dt.minute.eq(0)
    return Coverage(
        expected_half_hours=len(frame), expected_hourly_targets=int(hourly.sum()),
        forecast_observations=int(frame.forecastMw.notna().sum()),
        actual_observations=int(frame.actualMw.notna().sum()),
        matched_observations=int(frame.loc[hourly, ['forecastMw', 'actualMw']].notna().all(axis=1).sum()),
        missing_hourly_forecasts=int(frame.loc[hourly, 'forecastMw'].isna().sum()),
        missing_half_hour_actuals=int(frame.actualMw.isna().sum()),
        structural_half_hour_forecast_gaps=int((~hourly).sum()),
        excluded_hourly_pairs=int(frame.loc[hourly, ['forecastMw', 'actualMw']].isna().any(axis=1).sum()))


def calculate_accuracy(frame: pd.DataFrame) -> Accuracy:
    # Compute directly from values rather than trusting an externally cached error column.
    pairs = frame.loc[frame.startTime.dt.minute.eq(0), ['forecastMw', 'actualMw']].dropna()
    values = pairs.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('Metrics require finite observations')
    n = len(pairs)
    if not n:
        return Accuracy(status='no_matched_observations', observation_count=0,
                        mae_mw=None, rmse_mw=None, bias_mw=None)
    errors = values[:, 0] - values[:, 1]
    return Accuracy(status='ok', observation_count=n, mae_mw=float(np.abs(errors).mean()),
                    rmse_mw=float(np.sqrt(np.square(errors).mean())), bias_mw=float(errors.mean()))
