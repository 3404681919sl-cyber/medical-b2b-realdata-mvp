"""Evidence-oriented dataset quality measures."""

from __future__ import annotations

import pandas as pd


def audit_tables(
    transactions: pd.DataFrame, products: pd.DataFrame
) -> dict[str, dict[str, object]]:
    """Measure observed quality without silently cleaning source rows."""
    parsed_dates = pd.to_datetime(transactions["sale_date"], errors="coerce")
    valid_dates = parsed_dates.dropna()
    product_skus = set(products["sku_id"].dropna().astype(str))
    transaction_skus = transactions["sku_id"].fillna("").astype(str)

    return {
        "transactions": {
            "row_count": int(len(transactions)),
            "unique_receipts": int(transactions["receipt_id"].nunique(dropna=True)),
            "unique_skus": int(transactions["sku_id"].nunique(dropna=True)),
            "date_min": valid_dates.min().date().isoformat() if not valid_dates.empty else None,
            "date_max": valid_dates.max().date().isoformat() if not valid_dates.empty else None,
            "missing_by_column": {
                column: int(transactions[column].isna().sum())
                for column in transactions.columns
            },
            "exact_duplicate_rows": int(transactions.duplicated(keep="first").sum()),
            "invalid_sale_date_rows": int(parsed_dates.isna().sum()),
            "non_positive_quantity_rows": int((transactions["quantity"] <= 0).sum()),
            "price_below_cost_rows": int(
                (transactions["unit_price"] < transactions["unit_cost"]).sum()
            ),
            "orphan_sku_rows": int((~transaction_skus.isin(product_skus)).sum()),
        },
        "products": {
            "row_count": int(len(products)),
            "unique_skus": int(products["sku_id"].nunique(dropna=True)),
            "duplicate_sku_rows": int(products["sku_id"].duplicated(keep="first").sum()),
            "missing_by_column": {
                column: int(products[column].isna().sum()) for column in products.columns
            },
        },
    }

