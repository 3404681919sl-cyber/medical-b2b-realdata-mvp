# Spec: 药采智析——医药零售销量洞察与采购计划助手

## Assumptions

1. V1 是本地运行的单用户 Web 应用，目标是作品集与小范围试用，不是生产采购系统。
2. V1 的公开基准数据来自 Mendeley Data 数据集 `10.17632/2ym7v78wtd.1`，其页面声明数据直接取自真实药店数据库，许可为 CC BY 4.0。
3. 该数据属于印度尼西亚历史药店数据，不能代表当前中国医药 B2B 市场。
4. 原始公开数据可用于销量分析和需求回测；只有用户额外提供实际库存与采购参数时，系统才生成采购建议。
5. 所有确定性数值由 Python 规则或统计方法计算；大模型只解释结果且为可选能力。
6. 原始经营数据默认只在本地处理，不发送给大模型。

## Objective

为药店采购或经营人员提供一条可审计的数据处理链：导入真实历史销售数据，发现数据质量问题，分析商品表现，以时间顺序回测简单需求预测方法，并在库存参数完整时生成可解释的采购计划。

主要用户故事：

- 作为采购人员，我能上传销售与商品 Excel/CSV，并把原字段映射到标准字段。
- 作为采购人员，我能在分析前看到缺失、重复、非法数量和关联失败等质量问题。
- 作为采购人员，我能查看商品销售趋势、ABC 分类和异常风险。
- 作为采购人员，我能看到需求预测在历史测试集上的误差，而不是只看到未来预测值。
- 作为采购人员，我能比较朴素、移动平均和季节性朴素策略，保留自动推荐与人工选择的差异。
- 作为采购人员，我能通过多折滚动回测比较普通与间歇需求策略，而不是依赖单次留出结果。
- 作为采购人员，我能用自然语言提出销售、预测、风险和采购问题，并看到意图、工具调用、证据与拒绝原因。
- 作为采购人员，我能看到哪些 SKU 因历史不足、测试期零需求、稀疏或高波动而需要谨慎解释。
- 作为采购人员，我只有在填写当前库存、在途、提前期、安全库存和最小采购量后才会得到采购建议。
- 作为面试官，我能复现数据来源、处理步骤、指标口径与结果导出。

## Data provenance

- Title: Retail sales dataset of a pharmacy in Indonesia
- Author: Rendra Gustriansyah
- DOI: https://doi.org/10.17632/2ym7v78wtd.1
- Publisher: Mendeley Data
- Published: 2022-02-14
- License: CC BY 4.0
- Project use: raw archive is kept unchanged; SHA-256 and retrieval metadata are recorded locally.

## Tech Stack

- Python 3.11+; current development host reports Python 3.14.5.
- Streamlit for the local Web UI.
- pandas and openpyxl for tabular data processing and Excel I/O.
- Plotly for interactive analytical charts.
- pytest for unit and integration tests.
- No database in V1; standardized tables are processed in memory and exported as files.

## Commands

```powershell
# install
python -m pip install -r requirements.txt

# test
python -m pytest -q

# run
python -m streamlit run app.py
```

## Project Structure

```text
medical-b2b-realdata-mvp/
├─ app.py                    # Streamlit entrypoint
├─ src/
│  ├─ data_import.py         # parsing, mapping and validation
│  ├─ analysis.py            # sales metrics and ABC analysis
│  ├─ forecasting.py         # baselines and temporal backtesting
│  ├─ procurement.py         # deterministic procurement rules
│  └─ exports.py             # downloadable reports
├─ tests/                    # pytest tests written before production code
├─ data/
│  ├─ raw/                   # unchanged source archive; not committed if oversized
│  ├─ interim/               # extracted source files
│  └─ metadata/              # provenance, hashes and field dictionary
├─ docs/                     # decisions, data report and product notes
├─ tasks/                    # implementation plan and checklist
├─ requirements.txt
└─ README.md
```

## Code Style

- Functions use English `snake_case`; user-facing copy is Chinese.
- Core functions are pure where practical and accept/return DataFrames explicitly.
- Validation issues use stable codes rather than matching prose.
- No hidden global business parameters.

```python
def calculate_reorder_quantity(
    forecast_demand: float,
    safety_stock: float,
    on_hand: float,
    in_transit: float,
) -> float:
    """Return a non-negative deterministic reorder quantity."""
    return max(0.0, forecast_demand + safety_stock - on_hand - in_transit)
```

## Testing Strategy

- Unit tests cover column normalization, invalid rows, duplicates, joins, metrics, chronological splits, forecast baselines and procurement formulas.
- Integration tests load a small fixture through import → analysis → forecast → export.
- Every production behavior begins with a failing test and follows red-green-refactor.
- The full suite runs before a completion claim.
- Streamlit startup receives a smoke test; major UI paths receive manual browser verification.

## Boundaries

### Always

- Preserve the original archive unchanged and record SHA-256.
- Show the source, license, geography, time period and known limitations.
- Split forecasting data chronologically; never randomly shuffle time series.
- Keep numerical decisions deterministic and auditable.
- Distinguish missing data from zero values.
- Refuse procurement output when required inventory parameters are absent.

### Ask first

- Uploading or publishing any non-public business dataset.
- Adding a hosted database, authentication or external API.
- Sending row-level data to any large-model provider.
- Changing the product from decision support to automatic ordering.

### Never

- Claim that public historical data represent current Chinese pharmacy operations.
- Claim business impact without a documented backtest or pilot.
- Include patient, prescription, customer or identifiable personal data.
- Generate diagnosis, treatment, prescription or medication advice.
- Present synthetic or manually fabricated values as observed data.

## Success Criteria

1. The source metadata and raw archive SHA-256 are reproducible.
2. The application imports the published source tables and reports row counts and data-quality issues.
3. A user can map alternative CSV/XLSX column names to the standard schema.
4. Sales analysis produces documented, test-covered metrics and ABC categories.
5. Forecast evaluation uses a chronological holdout and reports at least MAE and WAPE against a named baseline.
6. Procurement recommendations appear only when all required inventory inputs are supplied.
7. Every recommendation exposes its inputs and formula.
8. Results export to a readable Excel workbook.
9. The app starts locally from the documented command and the automated test suite passes.
10. UI and README display the data provenance and product limitations prominently.
11. Candidate selection records WAPE, MAE, the deterministic recommendation rule and any manual override.
12. BadCase coverage is measured by SKU and never treats zero sales as proof of stockout.
13. Forecast selection aggregates three expanding-window folds and includes a Croston-SBA intermittent-demand baseline.
14. The analysis assistant records a deterministic intent and named tool trace for every supported question.
15. The assistant refuses to produce procurement quantities when real inventory inputs are absent.

## Open Questions

- Whether the published archive contains sufficient date continuity for weekly or monthly backtesting will be decided after profiling the untouched source.
- The exact forecast horizon and holdout length depend on the observed date range and sparsity.
- A real Chinese pharmacy pilot remains future work and must not be implied by V1.

