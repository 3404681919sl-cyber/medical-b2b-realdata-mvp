# Public dataset quality report

## Source boundary

This report describes the untouched public archive after a deterministic SQL-to-CSV extraction. The source is historical Indonesian pharmacy data and does not establish current Chinese pharmacy behavior. No live inventory or expiry fields are present.

## Observed transaction table

| Measure | Observed value |
|---|---:|
| Rows | 399,738 |
| Unique receipts | 126,954 |
| Unique SKUs | 2,043 |
| Date range | 2015-01-01 to 2015-12-31 |
| Exact duplicate rows | 391 |
| Invalid sale dates | 0 |
| Non-positive quantities | 268 |
| Price below cost rows | 1,302 |
| Rows whose SKU is absent from product master | 92 |

## Observed product table

| Measure | Observed value |
|---|---:|
| Rows | 6,878 |
| Unique SKUs | 6,878 |
| Duplicate SKU rows | 0 |

## Interpretation rule

These values are observations, not automatically corrected results. Cleaning decisions must be documented separately before analysis or backtesting.
