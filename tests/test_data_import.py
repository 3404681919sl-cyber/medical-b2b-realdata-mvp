import pandas as pd

from src.data_import import (
    prepare_analysis_transactions,
    standardize_transactions,
    validate_transactions,
)


def test_standardize_transactions_maps_published_source_columns():
    """Catches a broken source-to-canonical field mapping."""
    source = pd.DataFrame(
        {
            "TGL": ["2015-01-02"],
            "KD_OBAT": ["MED-001"],
            "QTY": [3],
            "HNA": [10.0],
            "HJ": [15.0],
        }
    )

    result = standardize_transactions(source)

    assert list(result.columns) == [
        "sale_date",
        "sku_id",
        "quantity",
        "unit_cost",
        "unit_price",
    ]
    assert result.iloc[0].to_dict() == {
        "sale_date": pd.Timestamp("2015-01-02"),
        "sku_id": "MED-001",
        "quantity": 3,
        "unit_cost": 10.0,
        "unit_price": 15.0,
    }


def test_standardize_transactions_accepts_explicit_user_mapping():
    """Catches a regression that hard-codes only the published dataset headers."""
    source = pd.DataFrame(
        {
            "业务日期": ["2026/10/01"],
            "商品编码": ["A-9"],
            "销售数量": [2],
            "采购成本": [7.5],
            "销售价格": [9.0],
        }
    )
    mapping = {
        "业务日期": "sale_date",
        "商品编码": "sku_id",
        "销售数量": "quantity",
        "采购成本": "unit_cost",
        "销售价格": "unit_price",
    }

    result = standardize_transactions(source, column_mapping=mapping)

    assert result.iloc[0]["sku_id"] == "A-9"
    assert result.iloc[0]["sale_date"] == pd.Timestamp("2026-10-01")
    assert result.iloc[0]["quantity"] == 2


def test_validate_transactions_reports_stable_issue_codes():
    """Catches silent acceptance of malformed dates, empty SKUs and invalid quantities."""
    transactions = pd.DataFrame(
        {
            "sale_date": [pd.NaT, pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-02")],
            "sku_id": ["A", "", "C"],
            "quantity": [1, 2, 0],
            "unit_cost": [3.0, 4.0, 5.0],
            "unit_price": [4.0, 5.0, 4.0],
        }
    )

    issues = validate_transactions(transactions)

    assert issues[["row_index", "code", "severity"]].to_dict("records") == [
        {"row_index": 0, "code": "MISSING_SALE_DATE", "severity": "error"},
        {"row_index": 1, "code": "MISSING_SKU_ID", "severity": "error"},
        {"row_index": 2, "code": "NON_POSITIVE_QUANTITY", "severity": "error"},
        {"row_index": 2, "code": "PRICE_BELOW_COST", "severity": "warning"},
    ]


def test_validate_transactions_reports_exact_duplicate_rows():
    """Catches duplicate rows being counted as independent sales."""
    transactions = pd.DataFrame(
        {
            "sale_date": [pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-01")],
            "sku_id": ["A", "A"],
            "quantity": [1, 1],
            "unit_cost": [3.0, 3.0],
            "unit_price": [4.0, 4.0],
        }
    )

    issues = validate_transactions(transactions)

    duplicate_issues = issues.loc[issues["code"] == "EXACT_DUPLICATE"]
    assert duplicate_issues["row_index"].tolist() == [1]
    assert duplicate_issues["severity"].tolist() == ["warning"]


def test_prepare_analysis_transactions_excludes_only_documented_invalid_rows():
    """Catches silent cleaning or valid negative-margin sales being discarded."""
    transactions = pd.DataFrame(
        {
            "sale_date": [
                "2026-01-01",
                "2026-01-01",
                "2026-01-02",
                "bad-date",
                "2026-01-04",
                "2026-01-05",
            ],
            "sku_id": ["A", "A", "B", "C", "", "E"],
            "quantity": [2.0, 2.0, 0.0, 1.0, 1.0, 3.0],
            "unit_cost": [4.0, 4.0, 2.0, 2.0, 2.0, 8.0],
            "unit_price": [5.0, 5.0, 3.0, 3.0, 3.0, 7.0],
        }
    )

    result = prepare_analysis_transactions(transactions)

    assert result.clean["sku_id"].tolist() == ["A", "E"]
    assert result.exclusion_counts == {
        "EXACT_DUPLICATE": 1,
        "NON_POSITIVE_QUANTITY": 1,
        "INVALID_SALE_DATE": 1,
        "MISSING_SKU_ID": 1,
    }

