"""Demand baselines and chronological backtest measures."""

from __future__ import annotations

import math

import pandas as pd


def forecast_naive(train: pd.Series, horizon: int) -> pd.Series:
    """Repeat the latest observed demand for every forecast period."""
    if train.empty:
        raise ValueError("Naive forecast requires at least one training period")
    if horizon <= 0:
        raise ValueError("Forecast horizon must be greater than zero")
    return pd.Series([float(train.iloc[-1])] * horizon, dtype="float64")


def forecast_seasonal_naive(
    train: pd.Series, horizon: int, seasonal_period: int
) -> pd.Series:
    """Repeat the latest complete seasonal cycle over the forecast horizon."""
    if seasonal_period <= 0:
        raise ValueError("seasonal_period must be greater than zero")
    if len(train) < seasonal_period:
        raise ValueError("Training history is shorter than seasonal_period")
    if horizon <= 0:
        raise ValueError("Forecast horizon must be greater than zero")
    season = train.iloc[-seasonal_period:].astype(float).tolist()
    return pd.Series(
        [season[index % seasonal_period] for index in range(horizon)],
        dtype="float64",
    )


def backtest_forecast_candidates(
    series: pd.Series,
    holdout_periods: int,
    moving_windows: tuple[int, ...],
    seasonal_periods: tuple[int, ...],
) -> pd.DataFrame:
    """Evaluate auditable baseline candidates on one chronological holdout."""
    train, test = chronological_holdout(series, holdout_periods)
    rows: list[dict[str, object]] = []

    candidates: list[tuple[str, str, int | None, pd.Series]] = [
        ("naive:last", "朴素预测（最近值）", None, forecast_naive(train, len(test)))
    ]
    for window in moving_windows:
        candidates.append(
            (
                f"moving_average:{window}",
                f"移动平均（{window}周）",
                window,
                forecast_moving_average(train, len(test), window),
            )
        )
    for period in seasonal_periods:
        if len(train) < period:
            continue
        candidates.append(
            (
                f"seasonal_naive:{period}",
                f"季节性朴素（{period}周周期）",
                period,
                forecast_seasonal_naive(train, len(test), period),
            )
        )

    for candidate_id, label, parameter, predicted in candidates:
        rows.append(
            {
                "candidate_id": candidate_id,
                "model_label": label,
                "parameter": parameter,
                "mae": mean_absolute_error(test, predicted),
                "wape": weighted_absolute_percentage_error(test, predicted),
                "train_periods": len(train),
                "test_periods": len(test),
            }
        )
    return pd.DataFrame(rows)


def recommend_forecast_candidate(candidates: pd.DataFrame) -> pd.Series:
    """Return the lowest-WAPE candidate, breaking ties with MAE and id."""
    valid = candidates.loc[candidates["wape"].map(math.isfinite)].copy()
    if valid.empty:
        raise ValueError("No candidate has a finite WAPE")
    ordered = valid.sort_values(
        ["wape", "mae", "candidate_id"], ascending=[True, True, True], kind="stable"
    )
    return ordered.iloc[0]


def diagnose_demand_series(
    series: pd.Series,
    holdout_periods: int,
    min_history_periods: int,
    sparse_threshold: float = 0.25,
) -> dict[str, object]:
    """Describe forecast eligibility separately from demand-pattern warnings."""
    ordered = series.sort_index().astype(float)
    history_periods = len(ordered)
    nonzero_share = float(ordered.ne(0).mean()) if history_periods else 0.0
    mean = float(ordered.mean()) if history_periods else 0.0
    coefficient_of_variation = (
        float(ordered.std(ddof=0) / abs(mean)) if mean != 0 else math.nan
    )
    holdout = ordered.iloc[-holdout_periods:]
    holdout_demand = float(holdout.abs().sum())

    reason_codes: list[str] = []
    if history_periods < min_history_periods:
        reason_codes.append("SHORT_HISTORY")
    if holdout_demand == 0:
        reason_codes.append("ZERO_HOLDOUT_DEMAND")
    if nonzero_share < sparse_threshold:
        reason_codes.append("SPARSE_DEMAND")
    if math.isfinite(coefficient_of_variation) and coefficient_of_variation > 2.0:
        reason_codes.append("HIGH_VARIATION")

    blocking = {"SHORT_HISTORY", "ZERO_HOLDOUT_DEMAND"}
    return {
        "eligible": not any(code in blocking for code in reason_codes),
        "reason_codes": reason_codes,
        "history_periods": history_periods,
        "nonzero_share": nonzero_share,
        "coefficient_of_variation": coefficient_of_variation,
        "holdout_demand": holdout_demand,
    }


def build_sku_diagnostics(
    transactions: pd.DataFrame,
    sku_ids: list[str],
    holdout_periods: int,
    min_history_periods: int,
    sparse_threshold: float = 0.25,
) -> pd.DataFrame:
    """Build one auditable eligibility and risk record per SKU."""
    rows: list[dict[str, object]] = []
    selected = transactions.loc[transactions["sku_id"].isin(sku_ids)]
    grouped = {
        str(sku_id): group for sku_id, group in selected.groupby("sku_id", sort=False)
    }
    for sku_id in sku_ids:
        group = grouped.get(str(sku_id), selected.iloc[0:0])
        weekly = build_weekly_demand(group, sku_id)
        diagnostic = diagnose_demand_series(
            weekly,
            holdout_periods=holdout_periods,
            min_history_periods=min_history_periods,
            sparse_threshold=sparse_threshold,
        )
        rows.append(
            {
                "sku_id": sku_id,
                "eligible": diagnostic["eligible"],
                "reason_codes": "|".join(diagnostic["reason_codes"]),
                "history_periods": diagnostic["history_periods"],
                "nonzero_share": diagnostic["nonzero_share"],
                "coefficient_of_variation": diagnostic[
                    "coefficient_of_variation"
                ],
                "holdout_demand": diagnostic["holdout_demand"],
            }
        )
    return pd.DataFrame(rows)


def build_weekly_demand(transactions: pd.DataFrame, sku_id: str) -> pd.Series:
    """Aggregate one SKU to continuous Sunday-ending weeks."""
    selected = transactions.loc[
        transactions["sku_id"] == sku_id, ["sale_date", "quantity"]
    ].copy()
    selected["sale_date"] = pd.to_datetime(selected["sale_date"], errors="coerce")
    selected = selected.dropna(subset=["sale_date"]).set_index("sale_date").sort_index()
    weekly = selected["quantity"].resample("W-SUN").sum().fillna(0.0)
    weekly.name = "weekly_demand"
    return weekly


def backtest_moving_average_windows(
    series: pd.Series, holdout_periods: int, windows: tuple[int, ...]
) -> pd.DataFrame:
    """Evaluate several moving-average windows on one chronological holdout."""
    train, test = chronological_holdout(series, holdout_periods)
    rows = []
    for window in windows:
        predicted = forecast_moving_average(train, len(test), window)
        rows.append(
            {
                "window": window,
                "mae": mean_absolute_error(test, predicted),
                "wape": weighted_absolute_percentage_error(test, predicted),
                "forecast_per_period": float(predicted.iloc[0]),
                "train_periods": len(train),
                "test_periods": len(test),
            }
        )
    return pd.DataFrame(rows)


def chronological_holdout(
    series: pd.Series, holdout_periods: int
) -> tuple[pd.Series, pd.Series]:
    """Sort a time series and reserve its latest periods for evaluation."""
    ordered = series.sort_index()
    return ordered.iloc[:-holdout_periods], ordered.iloc[-holdout_periods:]


def forecast_moving_average(
    train: pd.Series, horizon: int, window: int
) -> pd.Series:
    """Forecast a constant equal to the latest-window arithmetic mean."""
    prediction = float(train.iloc[-window:].mean())
    return pd.Series([prediction] * horizon, dtype="float64")


def mean_absolute_error(actual: pd.Series, predicted: pd.Series) -> float:
    """Return the arithmetic mean of absolute forecast errors."""
    return float((actual.reset_index(drop=True) - predicted.reset_index(drop=True)).abs().mean())


def weighted_absolute_percentage_error(
    actual: pd.Series, predicted: pd.Series
) -> float:
    """Return sum(abs(error)) / sum(abs(actual)), or NaN for zero demand."""
    aligned_actual = actual.reset_index(drop=True)
    aligned_predicted = predicted.reset_index(drop=True)
    denominator = float(aligned_actual.abs().sum())
    if denominator == 0:
        return math.nan
    return float((aligned_actual - aligned_predicted).abs().sum() / denominator)

