import pandas as pd

from src.audit import audit_tables


def test_audit_tables_reports_observed_quality_and_join_failures():
    """Catches a quality report that hides duplicates, invalid quantities or orphan SKUs."""
    transactions = pd.DataFrame(
        {
            "receipt_id": ["R1", "R1", "R2"],
            "sale_date": ["2015-01-01", "2015-01-01", "bad-date"],
            "sku_id": ["A", "A", "MISSING"],
            "quantity": [2.0, 2.0, 0.0],
            "unit_cost": [4.0, 4.0, 6.0],
            "unit_price": [5.0, 5.0, 5.0],
        }
    )
    products = pd.DataFrame(
        {
            "sku_id": ["A", "A", "B"],
            "product_name": ["A1", "A duplicate", "B"],
        }
    )

    result = audit_tables(transactions, products)

    assert result["transactions"]["row_count"] == 3
    assert result["transactions"]["unique_receipts"] == 2
    assert result["transactions"]["exact_duplicate_rows"] == 1
    assert result["transactions"]["invalid_sale_date_rows"] == 1
    assert result["transactions"]["non_positive_quantity_rows"] == 1
    assert result["transactions"]["price_below_cost_rows"] == 1
    assert result["transactions"]["orphan_sku_rows"] == 1
    assert result["products"]["duplicate_sku_rows"] == 1

