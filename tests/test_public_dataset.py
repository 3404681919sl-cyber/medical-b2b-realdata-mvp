import pandas as pd

from src.public_dataset import extract_public_dataset


def test_extract_public_dataset_writes_standard_transaction_and_product_files(tmp_path):
    """Catches a broken bridge between the published SQL dump and application tables."""
    dump_path = tmp_path / "sales.sql"
    dump_path.write_text(
        "\n".join(
            [
                "INSERT INTO `ms_product` (`KD_OBAT`, `NAMA`, `SAT_JUAL`, `KD_PABRIK`, `HJ_RP`) VALUES",
                "('SKU-1', 'Drug, One', 'BOX', 'M-1', 16.0);",
                "INSERT INTO `transaction` (`NO_RESEP`, `TGL`, `KD_CUST`, `KD_OBAT`, `QTY`, `HNA`, `HJ`) VALUES",
                "('RX-1', '2015-01-02', 'C-1', 'SKU-1', 2, 10.0, 15.0);",
            ]
        ),
        encoding="utf-8",
    )

    result = extract_public_dataset(dump_path, tmp_path)

    transactions = pd.read_csv(result.transaction_csv)
    products = pd.read_csv(result.product_csv)
    assert result.transaction_rows == 1
    assert result.product_rows == 1
    assert transactions.iloc[0].to_dict() == {
        "receipt_id": "RX-1",
        "sale_date": "2015-01-02",
        "sku_id": "SKU-1",
        "quantity": 2.0,
        "unit_cost": 10.0,
        "unit_price": 15.0,
    }
    assert products.iloc[0].to_dict() == {
        "sku_id": "SKU-1",
        "product_name": "Drug, One",
        "sales_unit": "BOX",
        "manufacturer_code": "M-1",
        "list_price": 16.0,
    }

