"""Extract application tables from the published MariaDB dump."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.sql_dump import iter_table_rows


@dataclass(frozen=True)
class ExtractionResult:
    transaction_csv: Path
    product_csv: Path
    transaction_rows: int
    product_rows: int


def extract_public_dataset(
    dump_path: str | Path, output_dir: str | Path
) -> ExtractionResult:
    """Stream public `transaction` and `ms_product` tables into canonical CSVs."""
    dump = Path(dump_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    transaction_csv = destination / "transactions.csv"
    product_csv = destination / "products.csv"

    transaction_rows = _extract_transactions(dump, transaction_csv)
    product_rows = _extract_products(dump, product_csv)
    return ExtractionResult(
        transaction_csv=transaction_csv,
        product_csv=product_csv,
        transaction_rows=transaction_rows,
        product_rows=product_rows,
    )


def _extract_transactions(dump_path: Path, output_path: Path) -> int:
    count = 0
    with dump_path.open("r", encoding="utf-8", newline="") as source, output_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as destination:
        writer = csv.writer(destination)
        writer.writerow(
            ["receipt_id", "sale_date", "sku_id", "quantity", "unit_cost", "unit_price"]
        )
        for row in iter_table_rows(source, "transaction"):
            receipt_id, sale_date, _customer_id, sku_id, quantity, unit_cost, unit_price = row
            writer.writerow(
                [
                    receipt_id,
                    sale_date,
                    sku_id,
                    float(quantity),
                    float(unit_cost),
                    float(unit_price),
                ]
            )
            count += 1
    return count


def _extract_products(dump_path: Path, output_path: Path) -> int:
    count = 0
    with dump_path.open("r", encoding="utf-8", newline="") as source, output_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as destination:
        writer = csv.writer(destination)
        writer.writerow(
            ["sku_id", "product_name", "sales_unit", "manufacturer_code", "list_price"]
        )
        for row in iter_table_rows(source, "ms_product"):
            sku_id, product_name, sales_unit, manufacturer_code, list_price = row
            writer.writerow(
                [sku_id, product_name, sales_unit, manufacturer_code, float(list_price)]
            )
            count += 1
    return count

