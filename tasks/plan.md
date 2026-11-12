# Implementation Plan

## Checkpoint 1: provenance and raw-data audit

1. Retrieve the original Mendeley archive.
2. Record DOI metadata, license, retrieval time, byte size and SHA-256.
3. Extract into `data/interim/` without altering the archive.
4. Inspect file names, encodings, schemas, row counts, date coverage and nulls.
5. Publish an evidence-based data quality report before choosing forecast settings.

## Checkpoint 2: tested data-import vertical slice

1. Define the canonical sales and product schemas from observed fields.
2. Write failing tests for source parsing and validation.
3. Implement the minimum parser and validation report.
4. Verify with small fixtures, then the full source files.

## Checkpoint 3: tested sales analysis

1. Write metric and ABC classification tests.
2. Implement documented measures.
3. Compare computed totals with direct source aggregations.

## Checkpoint 4: tested temporal backtest

1. Select horizon based on audited coverage and sparsity.
2. Write tests for chronological splitting, baselines, MAE and WAPE.
3. Run backtests and record both positive and negative findings.

## Checkpoint 5: tested procurement calculator

1. Write tests that reject missing inventory fields.
2. Implement transparent reorder formulas and minimum-order rounding.
3. Keep public-source demand results separate from user-entered stock values.

## Checkpoint 6: UI and export

1. Build a restrained operations-console UI centered on the evidence chain.
2. Add provenance, quality, analysis, backtest and optional procurement views.
3. Add Excel export and startup smoke verification.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Dataset lacks inventory snapshots | Do not infer inventory; make procurement inputs explicit and optional |
| Historical Indonesian data has limited China relevance | Display limitation in product, README and portfolio |
| Source contains inconsistent dates or sparse SKUs | Audit first; choose aggregation and eligible SKU rules from evidence |
| Python 3.14 package compatibility | Use compatible versions available on the host; report any unresolved dependency issue |
| LLM/API unavailable | Keep explanations template-based in V1; never block core analysis |

