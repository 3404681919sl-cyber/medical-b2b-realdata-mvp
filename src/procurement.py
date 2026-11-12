"""Deterministic procurement-planning calculations."""

from __future__ import annotations

import math

import pandas as pd


REQUIRED_COLUMNS = [
    "sku_id",
    "forecast_demand",
    "safety_stock_units",
    "current_stock",
    "in_transit",
    "minimum_order_qty",
    "unit_cost",
]


def calculate_procurement_plan(inputs: pd.DataFrame) -> pd.DataFrame:
    """Calculate transparent reorder quantities from user-supplied stock inputs."""
    missing = [column for column in REQUIRED_COLUMNS if column not in inputs.columns]
    if missing:
        raise ValueError(f"Missing procurement inputs: {', '.join(missing)}")

    result = inputs.loc[:, REQUIRED_COLUMNS].copy()
    result["raw_reorder_qty"] = (
        result["forecast_demand"]
        + result["safety_stock_units"]
        - result["current_stock"]
        - result["in_transit"]
    ).clip(lower=0)
    result["recommended_order_qty"] = result.apply(_round_to_minimum_order, axis=1)
    result["recommended_order_cost"] = (
        result["recommended_order_qty"] * result["unit_cost"]
    )
    return result


def _round_to_minimum_order(row: pd.Series) -> float:
    quantity = float(row["raw_reorder_qty"])
    minimum = float(row["minimum_order_qty"])
    if quantity == 0:
        return 0.0
    if minimum <= 0:
        raise ValueError("minimum_order_qty must be greater than zero")
    return float(math.ceil(quantity / minimum) * minimum)

