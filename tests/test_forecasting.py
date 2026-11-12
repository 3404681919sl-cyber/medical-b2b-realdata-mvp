import math

import pandas as pd

from src.forecasting import (
    backtest_forecast_candidates,
    backtest_moving_average_windows,
    build_sku_diagnostics,
    build_weekly_demand,
    chronological_holdout,
    diagnose_demand_series,
    forecast_naive,
    forecast_seasonal_naive,
    forecast_moving_average,
    mean_absolute_error,
    recommend_forecast_candidate,
    weighted_absolute_percentage_error,
)


def test_chronological_holdout_sorts_dates_and_keeps_latest_periods_for_test():
    """Catches time leakage caused by unsorted or randomly split observations."""
    series = pd.Series(
        [30.0, 10.0, 40.0, 20.0],
        index=pd.to_datetime(["2026-01-03", "2026-01-01", "2026-01-04", "2026-01-02"]),
    )

    train, test = chronological_holdout(series, holdout_periods=2)

    assert train.tolist() == [10.0, 20.0]
    assert test.tolist() == [30.0, 40.0]
    assert train.index.max() < test.index.min()


def test_forecast_moving_average_repeats_mean_of_latest_window():
    """Catches a baseline using the earliest rather than latest observations."""
    train = pd.Series([2.0, 4.0, 8.0, 12.0])

    result = forecast_moving_average(train, horizon=2, window=3)

    assert result.tolist() == [8.0, 8.0]


def test_forecast_naive_repeats_the_latest_observation():
    """Catches naive forecasting accidentally using an average or early value."""
    train = pd.Series([2.0, 4.0, 9.0])

    result = forecast_naive(train, horizon=3)

    assert result.tolist() == [9.0, 9.0, 9.0]


def test_forecast_seasonal_naive_cycles_the_latest_complete_season():
    """Catches seasonal forecasts losing phase when the horizon exceeds one cycle."""
    train = pd.Series([1.0, 2.0, 3.0, 4.0])

    result = forecast_seasonal_naive(train, horizon=3, seasonal_period=2)

    assert result.tolist() == [3.0, 4.0, 3.0]


def test_forecast_metrics_use_hand_calculated_errors():
    """Catches incorrect denominators or percentage averaging."""
    actual = pd.Series([10.0, 20.0])
    predicted = pd.Series([12.0, 18.0])

    assert mean_absolute_error(actual, predicted) == 2.0
    assert round(weighted_absolute_percentage_error(actual, predicted), 4) == 0.1333


def test_wape_is_undefined_when_actual_demand_is_all_zero():
    """Catches a divide-by-zero result being presented as a valid zero error."""
    actual = pd.Series([0.0, 0.0])
    predicted = pd.Series([1.0, 1.0])

    assert math.isnan(weighted_absolute_percentage_error(actual, predicted))


def test_build_weekly_demand_inserts_zero_weeks_between_sales():
    """Catches missing weeks being dropped and demand history becoming artificially dense."""
    transactions = pd.DataFrame(
        {
            "sale_date": pd.to_datetime(["2026-01-01", "2026-01-03", "2026-01-12"]),
            "sku_id": ["A", "A", "A"],
            "quantity": [1.0, 2.0, 4.0],
        }
    )

    result = build_weekly_demand(transactions, "A")

    assert result.tolist() == [3.0, 0.0, 4.0]


def test_backtest_compares_windows_on_the_same_chronological_holdout():
    """Catches models being compared on different or leaked holdout periods."""
    series = pd.Series(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        index=pd.date_range("2026-01-04", periods=8, freq="W-SUN"),
    )

    result = backtest_moving_average_windows(
        series, holdout_periods=2, windows=(2, 4)
    ).set_index("window")

    assert result.loc[2, "mae"] == 2.0
    assert round(result.loc[2, "wape"], 4) == 0.2667
    assert result.loc[4, "mae"] == 3.0


def test_candidate_sweep_compares_naive_moving_and_seasonal_on_one_holdout():
    """Catches candidate families being omitted or evaluated on different periods."""
    series = pd.Series(
        [1.0, 10.0, 1.0, 10.0, 1.0, 10.0, 1.0, 10.0],
        index=pd.date_range("2026-01-04", periods=8, freq="W-SUN"),
    )

    result = backtest_forecast_candidates(
        series,
        holdout_periods=2,
        moving_windows=(2,),
        seasonal_periods=(2,),
    )

    assert result["candidate_id"].tolist() == [
        "naive:last",
        "moving_average:2",
        "seasonal_naive:2",
    ]
    seasonal = result.set_index("candidate_id").loc["seasonal_naive:2"]
    assert seasonal["mae"] == 0.0
    assert seasonal["wape"] == 0.0


def test_recommendation_uses_lowest_wape_and_preserves_candidate_row():
    """Catches automatic selection ignoring the auditable candidate table."""
    candidates = pd.DataFrame(
        [
            {"candidate_id": "naive:last", "wape": 0.20, "mae": 2.0},
            {"candidate_id": "moving_average:4", "wape": 0.15, "mae": 3.0},
            {"candidate_id": "seasonal_naive:4", "wape": 0.15, "mae": 1.0},
        ]
    )

    result = recommend_forecast_candidate(candidates)

    assert result["candidate_id"] == "seasonal_naive:4"
    assert result["wape"] == 0.15


def test_diagnostics_separate_ineligible_history_from_risk_warnings():
    """Catches sparse or volatile demand being silently treated as reliable."""
    short = pd.Series([1.0, 0.0, 0.0, 2.0])
    sparse = pd.Series([0.0] * 15 + [8.0])

    short_result = diagnose_demand_series(
        short, holdout_periods=2, min_history_periods=8
    )
    sparse_result = diagnose_demand_series(
        sparse, holdout_periods=2, min_history_periods=8, sparse_threshold=0.25
    )

    assert short_result["eligible"] is False
    assert "SHORT_HISTORY" in short_result["reason_codes"]
    assert sparse_result["eligible"] is True
    assert "SPARSE_DEMAND" in sparse_result["reason_codes"]


def test_sku_diagnostics_reports_coverage_from_each_products_weekly_history():
    """Catches coverage being calculated from rows instead of eligible SKUs."""
    dates = pd.date_range("2026-01-04", periods=8, freq="W-SUN")
    transactions = pd.DataFrame(
        {
            "sale_date": list(dates) + list(dates[:3]),
            "sku_id": ["A"] * 8 + ["B"] * 3,
            "quantity": [1.0] * 11,
        }
    )

    result = build_sku_diagnostics(
        transactions,
        sku_ids=["A", "B"],
        holdout_periods=2,
        min_history_periods=6,
    ).set_index("sku_id")

    assert bool(result.loc["A", "eligible"]) is True
    assert bool(result.loc["B", "eligible"]) is False
    assert result.loc["B", "reason_codes"] == "SHORT_HISTORY"

