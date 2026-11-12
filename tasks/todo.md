# Task Checklist

- [x] Retrieve and fingerprint the original public archive
  - Acceptance: metadata and SHA-256 are saved; archive size matches the provider metadata.
  - Verify: compare local hash and size with recorded manifest.
  - Files: `data/raw/*`, `data/metadata/source.json`

- [x] Audit untouched source files
  - Acceptance: report covers schemas, encodings, row counts, dates, nulls, duplicates and join integrity.
  - Verify: rerun the audit command from README.
  - Files: `scripts/extract_and_audit.py`, `docs/data-quality-report.md`

- [x] Implement standard import and validation
  - Acceptance: source and mapped user files produce canonical tables and stable issue codes.
  - Verify: unit tests plus full-source import.
  - Files: `src/data_import.py`, `tests/test_data_import.py`

- [x] Implement sales analysis
  - Acceptance: metrics and ABC categories match documented fixture calculations.
  - Verify: `python -m pytest tests/test_analysis.py -q`
  - Files: `src/analysis.py`, `tests/test_analysis.py`

- [x] Implement chronological forecast backtest
  - Acceptance: baselines and metrics pass fixtures; full-data result records eligible coverage.
  - Verify: `python -m pytest tests/test_forecasting.py -q`
  - Files: `src/forecasting.py`, `tests/test_forecasting.py`

- [x] Implement optional procurement calculator
  - Acceptance: missing required inputs block output; valid inputs produce auditable quantities.
  - Verify: `python -m pytest tests/test_procurement.py -q`
  - Files: `src/procurement.py`, `tests/test_procurement.py`

- [x] Build Streamlit UI and Excel export
  - Acceptance: source provenance, limitations and every analytical checkpoint are visible; export opens successfully.
  - Verify: startup smoke test, browser walkthrough and workbook read-back test.
  - Files: `app.py`, `src/exports.py`, UI tests or smoke scripts

- [x] Compare forecast candidates and preserve the decision trail
  - Acceptance: naive, moving-average and seasonal-naive candidates share one holdout; automatic and manual choices remain separate.
  - Verify: forecasting unit tests plus Streamlit decision-record test.
  - Files: `src/forecasting.py`, `app.py`, `docs/forecast-model-selection.md`

- [x] Add SKU coverage and BadCase analysis
  - Acceptance: coverage is computed by SKU; short history and zero-holdout cases block full comparison while sparse/high-variation cases remain warnings.
  - Verify: diagnostic unit tests and the full-data coverage snapshot.
  - Files: `src/forecasting.py`, `app.py`, `docs/forecast-model-selection.md`

