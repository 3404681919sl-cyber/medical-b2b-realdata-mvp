"""Transparent sales-analysis measures."""

from __future__ import annotations

import pandas as pd


def summarize_skus(transactions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate units, revenue, cost and gross profit by SKU."""
    working = transactions.copy()
    working["revenue"] = working["quantity"] * working["unit_price"]
    working["cost"] = working["quantity"] * working["unit_cost"]
    summary = (
        working.groupby("sku_id", as_index=False)
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("revenue", "sum"),
            cost=("cost", "sum"),
        )
        .sort_values("revenue", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
    summary["gross_profit"] = summary["revenue"] - summary["cost"]
    return summary


def classify_abc(summary: pd.DataFrame) -> pd.DataFrame:
    """Classify SKUs from cumulative revenue contribution."""
    result = summary.sort_values("revenue", ascending=False, kind="stable").reset_index(
        drop=True
    )
    total_revenue = result["revenue"].sum()
    if total_revenue <= 0:
        result["revenue_share"] = 0.0
        result["cumulative_revenue_share"] = 0.0
        result["abc_class"] = "C"
        return result

    result["revenue_share"] = result["revenue"] / total_revenue
    result["cumulative_revenue_share"] = result["revenue_share"].cumsum()
    previous_share = result["cumulative_revenue_share"] - result["revenue_share"]
    result["abc_class"] = "C"
    result.loc[previous_share < 0.95, "abc_class"] = "B"
    result.loc[previous_share < 0.80, "abc_class"] = "A"
    return result

