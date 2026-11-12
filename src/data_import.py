"""Canonical transaction import and validation contracts."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


CANONICAL_COLUMNS = [
    "sale_date",
    "sku_id",
    "quantity",
    "unit_cost",
    "unit_price",
]

PUBLISHED_TRANSACTION_MAPPING = {
    "TGL": "sale_date",
    "KD_OBAT": "sku_id",
    "QTY": "quantity",
    "HNA": "unit_cost",
    "HJ": "unit_price",
}


@dataclass(frozen=True)
class CleaningResult:
    clean: pd.DataFrame
    exclusion_counts: dict[str, int]


def prepare_analysis_transactions(transactions: pd.DataFrame) -> CleaningResult:
    """Apply documented row exclusions while retaining valid negative-margin sales."""
    working = transactions.copy()
    working["sale_date"] = pd.to_datetime(working["sale_date"], errors="coerce")
    working["sku_id"] = working["sku_id"].astype("string").str.strip().fillna("")
    reasons = pd.Series(pd.NA, index=working.index, dtype="string")

    duplicate_mask = working.duplicated(keep="first")
    reasons.loc[duplicate_mask] = "EXACT_DUPLICATE"

    available = reasons.isna()
    reasons.loc[available & (working["quantity"].isna() | (working["quantity"] <= 0))] = (
        "NON_POSITIVE_QUANTITY"
    )
    available = reasons.isna()
    reasons.loc[available & working["sale_date"].isna()] = "INVALID_SALE_DATE"
    available = reasons.isna()
    reasons.loc[available & working["sku_id"].eq("")] = "MISSING_SKU_ID"

    clean = working.loc[reasons.isna()].reset_index(drop=True)
    exclusion_counts = {
        str(code): int(count) for code, count in reasons.dropna().value_counts().items()
    }
    return CleaningResult(clean=clean, exclusion_counts=exclusion_counts)


def standardize_transactions(
    source: pd.DataFrame,
    column_mapping: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Map a transaction table to the canonical schema."""
    mapping = column_mapping or PUBLISHED_TRANSACTION_MAPPING
    renamed = source.rename(columns=mapping)
    missing = [column for column in CANONICAL_COLUMNS if column not in renamed.columns]
    if missing:
        raise ValueError(f"Missing canonical columns: {', '.join(missing)}")

    result = renamed.loc[:, CANONICAL_COLUMNS].copy()
    result["sale_date"] = pd.to_datetime(result["sale_date"], errors="coerce")
    result["sku_id"] = result["sku_id"].astype("string").str.strip().fillna("")
    for column in ["quantity", "unit_cost", "unit_price"]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def validate_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    """Return one stable issue record for each failed transaction rule."""
    issues: list[dict[str, object]] = []

    for index, row in transactions.iterrows():
        if pd.isna(row["sale_date"]):
            issues.append(_issue(index, "MISSING_SALE_DATE", "error"))
        if pd.isna(row["sku_id"]) or not str(row["sku_id"]).strip():
            issues.append(_issue(index, "MISSING_SKU_ID", "error"))
        if pd.isna(row["quantity"]) or row["quantity"] <= 0:
            issues.append(_issue(index, "NON_POSITIVE_QUANTITY", "error"))
        if (
            pd.notna(row["unit_cost"])
            and pd.notna(row["unit_price"])
            and row["unit_price"] < row["unit_cost"]
        ):
            issues.append(_issue(index, "PRICE_BELOW_COST", "warning"))

    duplicate_mask = transactions.duplicated(keep="first")
    for index in transactions.index[duplicate_mask]:
        issues.append(_issue(index, "EXACT_DUPLICATE", "warning"))

    return pd.DataFrame(issues, columns=["row_index", "code", "severity"])


def _issue(row_index: object, code: str, severity: str) -> dict[str, object]:
    return {"row_index": row_index, "code": code, "severity": severity}

