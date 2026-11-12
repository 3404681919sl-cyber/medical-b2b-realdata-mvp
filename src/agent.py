"""Auditable intent routing and tool execution for the analysis assistant."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from src.forecasting import (
    diagnose_demand_series,
    normalize_candidate_parameter,
    recommend_forecast_candidate,
    rolling_origin_backtest_candidates,
)


INTENT_KEYWORDS = {
    "procurement": ("采购", "补货", "进货", "订货"),
    "risk_diagnosis": ("风险", "异常", "稀疏", "波动", "可靠"),
    "demand_forecast": ("预测", "未来需求", "模型", "回测"),
    "sales_snapshot": ("销售", "销量", "销售额", "毛利", "表现", "abc"),
}


def route_analysis_intent(query: str) -> str:
    """Route a Chinese business question with explicit, inspectable keywords."""
    normalized = query.strip().lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return intent
    return "unknown"


def execute_analysis_agent(
    query: str,
    sku_id: str,
    sku_summary: Mapping[str, object],
    weekly_demand: pd.Series,
) -> dict[str, object]:
    """Execute one deterministic tool plan and return its evidence trail."""
    intent = route_analysis_intent(query)
    base: dict[str, object] = {
        "query": query,
        "sku_id": sku_id,
        "intent": intent,
        "tool_calls": [],
        "evidence": {},
        "boundaries": [
            "使用历史销量，不等同于真实库存或未来订单",
            "规则意图路由，不是大语言模型自由生成",
        ],
    }

    if intent == "sales_snapshot":
        evidence = {
            "product_name": str(sku_summary.get("product_name", "未匹配商品档案")),
            "abc_class": str(sku_summary.get("abc_class", "")),
            "units_sold": float(sku_summary.get("units_sold", 0.0)),
            "revenue": float(sku_summary.get("revenue", 0.0)),
            "gross_profit": float(sku_summary.get("gross_profit", 0.0)),
        }
        base["tool_calls"] = [
            {
                "tool": "sales_analysis.sku_snapshot",
                "status": "completed",
                "inputs": {"sku_id": sku_id},
            }
        ]
        base["evidence"] = evidence
        base["answer"] = (
            f"{evidence['product_name']} 属于 ABC-{evidence['abc_class']} 类；"
            f"历史销量 {evidence['units_sold']:,.0f}，销售额 {evidence['revenue']:,.2f}，"
            f"毛利额 {evidence['gross_profit']:,.2f}。"
        )
        return base

    if intent == "demand_forecast":
        candidates = rolling_origin_backtest_candidates(
            weekly_demand,
            fold_horizon=4,
            folds=3,
            moving_windows=(4, 8, 12),
            seasonal_periods=(4, 13),
            croston_alphas=(0.1, 0.2, 0.3),
        )
        recommended = recommend_forecast_candidate(candidates)
        evidence = {
            "candidate_id": str(recommended["candidate_id"]),
            "model_label": str(recommended["model_label"]),
            "parameter": normalize_candidate_parameter(recommended["parameter"]),
            "mae": float(recommended["mae"]),
            "wape": float(recommended["wape"]),
            "folds": int(recommended["folds"]),
            "evaluated_periods": int(recommended["test_periods"]),
        }
        base["tool_calls"] = [
            {
                "tool": "forecasting.rolling_origin",
                "status": "completed",
                "inputs": {
                    "sku_id": sku_id,
                    "fold_horizon": 4,
                    "folds": 3,
                    "candidate_count": len(candidates),
                },
            }
        ]
        base["evidence"] = evidence
        base["answer"] = (
            f"三折滚动回测推荐“{evidence['model_label']}”；"
            f"合并 WAPE 为 {evidence['wape']:.1%}，MAE 为 {evidence['mae']:.2f}。"
        )
        return base

    if intent == "risk_diagnosis":
        diagnostic = diagnose_demand_series(
            weekly_demand,
            holdout_periods=8,
            min_history_periods=21,
            sparse_threshold=0.25,
        )
        evidence = {
            "eligible": bool(diagnostic["eligible"]),
            "reason_codes": list(diagnostic["reason_codes"]),
            "history_periods": int(diagnostic["history_periods"]),
            "nonzero_share": float(diagnostic["nonzero_share"]),
            "coefficient_of_variation": float(
                diagnostic["coefficient_of_variation"]
            ),
            "holdout_demand": float(diagnostic["holdout_demand"]),
        }
        base["tool_calls"] = [
            {
                "tool": "forecasting.diagnose_demand_series",
                "status": "completed",
                "inputs": {"sku_id": sku_id, "holdout_periods": 8},
            }
        ]
        base["evidence"] = evidence
        labels = evidence["reason_codes"] or ["未触发预设风险标签"]
        base["answer"] = "；".join(str(label) for label in labels)
        return base

    if intent == "procurement":
        missing_inputs = [
            "current_stock",
            "in_transit",
            "safety_stock_units",
            "minimum_order_qty",
        ]
        base["tool_calls"] = [
            {
                "tool": "procurement.calculate_plan",
                "status": "needs_input",
                "inputs": {"sku_id": sku_id},
            }
        ]
        base["missing_inputs"] = missing_inputs
        base["answer"] = "缺少真实库存与采购参数，未生成采购量。请前往“采购计算”补充输入。"
        return base

    base["answer"] = "暂支持销售表现、需求预测、风险诊断和采购建议四类问题。"
    return base
