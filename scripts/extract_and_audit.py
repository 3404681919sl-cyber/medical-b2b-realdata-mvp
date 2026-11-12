"""Extract the verified public SQL dump and publish a reproducible quality report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.audit import audit_tables
from src.public_dataset import extract_public_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", type=Path, default=Path("data/interim/sales.sql"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/interim"))
    parser.add_argument(
        "--report-json", type=Path, default=Path("data/metadata/quality-report.json")
    )
    parser.add_argument(
        "--report-md", type=Path, default=Path("docs/data-quality-report.md")
    )
    args = parser.parse_args()

    extraction = extract_public_dataset(args.dump, args.output_dir)
    transactions = pd.read_csv(extraction.transaction_csv)
    products = pd.read_csv(extraction.product_csv)
    report = audit_tables(transactions, products)

    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.write_text(_to_markdown(report), encoding="utf-8"
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))


def _to_markdown(report: dict[str, dict[str, object]]) -> str:
    tx = report["transactions"]
    products = report["products"]
    return f"""# Public dataset quality report

## Source boundary

This report describes the untouched public archive after a deterministic SQL-to-CSV extraction. The source is historical Indonesian pharmacy data and does not establish current Chinese pharmacy behavior. No live inventory or expiry fields are present.

## Observed transaction table

| Measure | Observed value |
|---|---:|
| Rows | {tx['row_count']:,} |
| Unique receipts | {tx['unique_receipts']:,} |
| Unique SKUs | {tx['unique_skus']:,} |
| Date range | {tx['date_min']} to {tx['date_max']} |
| Exact duplicate rows | {tx['exact_duplicate_rows']:,} |
| Invalid sale dates | {tx['invalid_sale_date_rows']:,} |
| Non-positive quantities | {tx['non_positive_quantity_rows']:,} |
| Price below cost rows | {tx['price_below_cost_rows']:,} |
| Rows whose SKU is absent from product master | {tx['orphan_sku_rows']:,} |

## Observed product table

| Measure | Observed value |
|---|---:|
| Rows | {products['row_count']:,} |
| Unique SKUs | {products['unique_skus']:,} |
| Duplicate SKU rows | {products['duplicate_sku_rows']:,} |

## Interpretation rule

These values are observations, not automatically corrected results. Cleaning decisions must be documented separately before analysis or backtesting.
"""


if __name__ == "__main__":
    main()

