from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd


DEPLOY_FILENAMES = ("transactions.csv.gz", "products.csv.gz")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_deterministic_gzip(source: Path, target: Path) -> None:
    compressed = gzip.compress(source.read_bytes(), compresslevel=9, mtime=0)
    target.write_bytes(compressed)


def build_deploy_bundle(project_root: Path) -> dict:
    """Build a deterministic, Git-friendly data bundle from audited CSV files."""
    project_root = Path(project_root).resolve()
    interim_dir = project_root / "data" / "interim"
    deploy_dir = project_root / "data" / "deploy"
    metadata_path = project_root / "data" / "metadata" / "source.json"
    source_paths = {
        "transactions.csv.gz": interim_dir / "transactions.csv",
        "products.csv.gz": interim_dir / "products.csv",
    }
    missing = [str(path) for path in source_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing audited CSV input(s): {', '.join(missing)}")
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Missing source metadata: {metadata_path}")

    deploy_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, int | str]] = {}
    for deploy_name, source_path in source_paths.items():
        target_path = deploy_dir / deploy_name
        _write_deterministic_gzip(source_path, target_path)
        row_count = len(pd.read_csv(source_path, usecols=[0]))
        files[deploy_name] = {
            "sha256": _sha256(target_path),
            "size_bytes": target_path.stat().st_size,
            "row_count": row_count,
        }

    source_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    manifest = {
        "schema_version": 1,
        "source": {
            "title": source_metadata.get("title"),
            "doi": source_metadata.get("doi"),
            "license": source_metadata.get("license"),
            "archive_sha256": source_metadata.get("local_sha256"),
        },
        "files": files,
    }
    (deploy_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def _verify_deploy_bundle(deploy_dir: Path) -> dict:
    manifest_path = deploy_dir / "manifest.json"
    expected_paths = [deploy_dir / name for name in DEPLOY_FILENAMES]
    if not manifest_path.is_file() or not all(path.is_file() for path in expected_paths):
        raise FileNotFoundError(
            "Deployment data bundle is incomplete; expected manifest.json, "
            "transactions.csv.gz and products.csv.gz"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported deployment data manifest schema")
    for path in expected_paths:
        expected = manifest.get("files", {}).get(path.name, {}).get("sha256")
        actual = _sha256(path)
        if not expected or actual != expected:
            raise ValueError(f"SHA-256 mismatch for deployment file: {path.name}")
    return manifest


def load_application_tables(project_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load verified deploy data when present, otherwise audited local CSV files."""
    project_root = Path(project_root).resolve()
    deploy_dir = project_root / "data" / "deploy"
    deploy_artifacts = [deploy_dir / "manifest.json"] + [
        deploy_dir / name for name in DEPLOY_FILENAMES
    ]
    if any(path.exists() for path in deploy_artifacts):
        manifest = _verify_deploy_bundle(deploy_dir)
        transactions = pd.read_csv(deploy_dir / "transactions.csv.gz")
        products = pd.read_csv(deploy_dir / "products.csv.gz")
        tables = {
            "transactions.csv.gz": transactions,
            "products.csv.gz": products,
        }
        for filename, table in tables.items():
            expected_rows = manifest["files"][filename]["row_count"]
            if len(table) != expected_rows:
                raise ValueError(f"Row-count mismatch for deployment file: {filename}")
        return transactions, products

    interim_dir = project_root / "data" / "interim"
    transactions_path = interim_dir / "transactions.csv"
    products_path = interim_dir / "products.csv"
    if not transactions_path.is_file() or not products_path.is_file():
        raise FileNotFoundError(
            "No application data found. Build data/deploy or generate data/interim CSVs."
        )
    return pd.read_csv(transactions_path), pd.read_csv(products_path)
