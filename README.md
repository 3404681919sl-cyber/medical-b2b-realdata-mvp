# 药采智析

一个以真实公开药店历史销售数据为基准、支持用户 Excel 导入的数据质量、销量洞察、需求回测与可选采购计划工具。

## Evidence status

- **Observed source:** Mendeley Data, *Retail sales dataset of a pharmacy in Indonesia*, DOI `10.17632/2ym7v78wtd.1`, CC BY 4.0.
- **What the source supports:** sales-data quality checks, product sales analysis and historical demand backtesting.
- **What the source does not prove:** current Chinese pharmacy demand, live inventory, expiry status, supplier performance or business impact.
- **Procurement boundary:** a recommendation is generated only after the user supplies current stock and purchasing parameters.
- **AI boundary:** the current MVP uses auditable statistical baselines and deterministic rules. It does not disguise an LLM-written narrative as a validated prediction.

## Verified local snapshot

- Original archive: `8,560,326` bytes; SHA-256 matches the provider manifest.
- Transactions: `399,738` rows, `126,954` receipts and `2,043` sold SKUs, covering 2015-01-01 through 2015-12-31.
- Product master: `6,878` unique SKUs.
- Analysis layer: `399,079` rows after excluding only exact duplicates, non-positive quantities, invalid dates and empty SKU codes.
- Automated verification: `36 passed`; import, analysis, candidate forecasting, deployment-data integrity, procurement, export and Streamlit startup are covered. All six Streamlit stages are exercised programmatically.
- Forecast eligibility snapshot: `1,361 / 2,042` sold SKUs (`66.65%`) support the complete 21-week-history and 8-week-holdout comparison. Risk labels are non-exclusive.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\extract_and_audit.py
.\.venv\Scripts\python.exe scripts\build_deploy_bundle.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501
```

Then open `http://localhost:8501`. The extraction command expects the verified SQL dump at `data/interim/sales.sql`; download the original archive from the source page and compare its size and SHA-256 with `data/metadata/source.json` before replacing local source files.

## Streamlit Community Cloud deployment

1. Run `scripts/build_deploy_bundle.py` and commit `data/deploy/` with the application code. Raw and interim source files remain excluded from Git.
2. Push the repository to GitHub, then create a Streamlit Community Cloud app with `app.py` as the entrypoint and Python 3.12 as the runtime.
3. The application prefers the compressed deployment bundle, verifies each file against `data/deploy/manifest.json`, and falls back to local interim CSV files only when no deployment artifact exists.
4. Install production dependencies from the exactly pinned `requirements.txt`; use `requirements-dev.txt` only for local development and tests.

The deployment bundle contains historical product and transaction facts from the cited CC BY 4.0 source. It does not contain patient, prescription, customer or credential data. Repository visibility must be chosen deliberately before pushing to GitHub.

## Project documents

- `CAPABILITY-MAP.md`: module boundaries and dependency order.
- `SPEC.md`: objective, technical decisions, safety boundaries and success criteria.
- `tasks/plan.md`: evidence-first implementation plan.
- `docs/ui-design.md`: interface design rationale.
- `docs/data-quality-report.md`: reproducible full-source quality observations.
- `docs/forecast-model-selection.md`: candidate sweep, recommendation rule, coverage and BadCase definitions.

## Data handling

The raw archive is kept unchanged under `data/raw/` and excluded from Git by default. Retrieval metadata, file size and SHA-256 are stored under `data/metadata/`. Do not add patient, prescription, customer or identifiable personal data.

