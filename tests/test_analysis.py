import pandas as pd

from src.analysis import classify_abc, summarize_skus


def test_summarize_skus_uses_quantity_weighted_revenue_and_profit():
    """Catches totals being calculated from unit prices without quantities."""
    transactions = pd.DataFrame(
        {
            "sale_date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-02"]),
            "sku_id": ["A", "A", "B"],
            "quantity": [2, 3, 4],
            "unit_cost": [6.0, 6.0, 2.0],
            "unit_price": [10.0, 10.0, 5.0],
        }
    )

    result = summarize_skus(transactions).set_index("sku_id")

    assert result.loc["A", ["units_sold", "revenue", "cost", "gross_profit"]].to_dict() == {
        "units_sold": 5,
        "revenue": 50.0,
        "cost": 30.0,
        "gross_profit": 20.0,
    }
    assert result.loc["B", "revenue"] == 20.0


def test_classify_abc_uses_cumulative_revenue_share():
    """Catches ABC classes being assigned from row count or unit volume."""
    summary = pd.DataFrame(
        {
            "sku_id": ["A", "B", "C"],
            "revenue": [80.0, 15.0, 5.0],
        }
    )

    result = classify_abc(summary).set_index("sku_id")

    assert result["abc_class"].to_dict() == {"A": "A", "B": "B", "C": "C"}
    assert result["revenue_share"].round(2).to_dict() == {
        "A": 0.80,
        "B": 0.15,
        "C": 0.05,
    }


def test_classify_abc_handles_zero_revenue_without_dividing_by_zero():
    """Catches undefined shares and unstable classes for an all-zero period."""
    summary = pd.DataFrame({"sku_id": ["A", "B"], "revenue": [0.0, 0.0]})

    result = classify_abc(summary)

    assert result["revenue_share"].tolist() == [0.0, 0.0]
    assert result["abc_class"].tolist() == ["C", "C"]

