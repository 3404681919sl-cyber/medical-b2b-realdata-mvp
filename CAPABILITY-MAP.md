# Capability Map: 药采智析 V1

本地图记录已经确认的能力边界。模块 id 在项目内保持稳定。

| Module id | Responsibility | Depends on |
|---|---|---|
| `data-import` | 导入公开真实数据或用户 Excel，完成字段映射、校验、标准化与数据质量报告 | — |
| `sales-analysis` | 计算销量、销售额、毛利、ABC 分类、时间趋势与异常数据指标 | `data-import` |
| `demand-forecast` | 以三折扩展窗口滚动回测比较朴素、移动平均、季节性朴素与 Croston-SBA，输出回测指标、自动推荐和人工选择记录 | `sales-analysis` |
| `forecast-badcase` | 按 SKU 计算可回测覆盖率，标记历史不足、测试期零需求、稀疏与高波动风险 | `demand-forecast` |
| `analysis-agent` | 以可检查关键词识别销售、预测、风险和采购意图，调用真实分析工具并返回结构化证据、轨迹与拒绝原因 | `sales-analysis`, `demand-forecast`, `forecast-badcase`, `procurement-plan` |
| `procurement-plan` | 仅在用户补充库存、在途、提前期和安全库存后生成确定性采购建议 | `demand-forecast` |
| `explanation` | 基于结构化结果生成可追溯解释；不得修改计算结果 | `sales-analysis`, `demand-forecast`, `procurement-plan` |
| `export-report` | 导出数据质量、分析、回测与采购计划结果 | 前述模块 |

Build order:

`data-import` → `sales-analysis` → `demand-forecast` → `forecast-badcase` → `procurement-plan` → `analysis-agent` → `explanation` → `export-report`

## V1 scope cuts

- 不做登录、多人权限或云数据库。
- 不做自动下单或供应商系统对接。
- 不做诊断、处方或用药推荐。
- 不把模拟库存冒充真实库存。
- 不在缺少库存字段时输出补货数量。
- 不使用来源不明的数据。
- 不把规则意图路由描述为已经接入大语言模型。

