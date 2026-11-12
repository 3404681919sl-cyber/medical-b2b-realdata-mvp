import json
from pathlib import Path

import pandas as pd
import pytest

from src.deployment_data import build_deploy_bundle, load_application_tables


def write_interim_fixture(project_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    interim = project_root / "data" / "interim"
    metadata = project_root / "data" / "metadata"
    interim.mkdir(parents=True)
    metadata.mkdir(parents=True)
    transactions = pd.DataFrame(
        {
            "receipt_id": ["R1", "R2"],
            "sale_date": ["2015-01-01", "2015-01-02"],
            "sku_id": ["SKU-1", "SKU-2"],
            "quantity": [2, 3],
            "unit_cost": [1.5, 2.5],
            "unit_price": [2.0, 3.0],
        }
    )
    products = pd.DataFrame(
        {"sku_id": ["SKU-1", "SKU-2"], "product_name": ["A", "B"]}
    )
    transactions.to_csv(interim / "transactions.csv", index=False)
    products.to_csv(interim / "products.csv", index=False)
    (metadata / "source.json").write_text(
        json.dumps(
            {
                "title": "Fixture pharmacy data",
                "doi": "10.1234/fixture",
                "license": "CC BY 4.0",
                "local_sha256": "source-hash",
            }
        ),
        encoding="utf-8",
    )
    return transactions, products


def test_build_deploy_bundle_is_reproducible_and_auditable(tmp_path):
    expected_transactions, expected_products = write_interim_fixture(tmp_path)

    first_manifest = build_deploy_bundle(tmp_path)
    first_bytes = {
        name: (tmp_path / "data" / "deploy" / name).read_bytes()
        for name in ("transactions.csv.gz", "products.csv.gz")
    }
    second_manifest = build_deploy_bundle(tmp_path)

    assert first_manifest == second_manifest
    assert first_manifest["schema_version"] == 1
    assert first_manifest["source"]["doi"] == "10.1234/fixture"
    assert first_manifest["files"]["transactions.csv.gz"]["row_count"] == 2
    assert first_manifest["files"]["products.csv.gz"]["row_count"] == 2
    for name, expected_bytes in first_bytes.items():
        deploy_path = tmp_path / "data" / "deploy" / name
        assert deploy_path.read_bytes() == expected_bytes
        assert first_manifest["files"][name]["size_bytes"] == len(expected_bytes)

    pd.testing.assert_frame_equal(
        pd.read_csv(tmp_path / "data" / "deploy" / "transactions.csv.gz"),
        expected_transactions,
        check_dtype=False,
    )
    pd.testing.assert_frame_equal(
        pd.read_csv(tmp_path / "data" / "deploy" / "products.csv.gz"),
        expected_products,
        check_dtype=False,
    )
    on_disk_manifest = json.loads(
        (tmp_path / "data" / "deploy" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert on_disk_manifest == first_manifest


def test_load_application_tables_prefers_verified_deploy_bundle(tmp_path):
    write_interim_fixture(tmp_path)
    build_deploy_bundle(tmp_path)
    interim_path = tmp_path / "data" / "interim" / "transactions.csv"
    interim_transactions = pd.read_csv(interim_path)
    interim_transactions.loc[0, "quantity"] = 999
    interim_transactions.to_csv(interim_path, index=False)

    transactions, products = load_application_tables(tmp_path)

    assert transactions.loc[0, "quantity"] == 2
    assert products["product_name"].tolist() == ["A", "B"]


def test_load_application_tables_falls_back_to_interim_csv(tmp_path):
    expected_transactions, expected_products = write_interim_fixture(tmp_path)

    transactions, products = load_application_tables(tmp_path)

    pd.testing.assert_frame_equal(
        transactions, expected_transactions, check_dtype=False
    )
    pd.testing.assert_frame_equal(products, expected_products, check_dtype=False)


def test_load_application_tables_rejects_tampered_deploy_file(tmp_path):
    write_interim_fixture(tmp_path)
    build_deploy_bundle(tmp_path)
    deploy_file = tmp_path / "data" / "deploy" / "transactions.csv.gz"
    deploy_file.write_bytes(deploy_file.read_bytes() + b"tampered")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        load_application_tables(tmp_path)
