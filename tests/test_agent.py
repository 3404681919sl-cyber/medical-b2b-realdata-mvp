import pandas as pd

from src.agent import execute_analysis_agent, route_analysis_intent


def summary_fixture() -> dict[str, object]:
    return {
        "sku_id": "SKU-1",
        "product_name": "Example product",
        "abc_class": "A",
        "units_sold": 120.0,
        "revenue": 3600.0,
        "gross_profit": 900.0,
    }


def weekly_fixture() -> pd.Series:
    return pd.Series(
        [1.0, 10.0] * 15,
        index=pd.date_range("2026-01-04", periods=30, freq="W-SUN"),
    )


def test_intent_router_uses_explicit_business_intents_with_procurement_priority():
    assert route_analysis_intent("这个商品销售额怎么样") == "sales_snapshot"
    assert route_analysis_intent("未来需求预测是否稳定") == "demand_forecast"
    assert route_analysis_intent("检查稀疏需求和异常风险") == "risk_diagnosis"
    assert route_analysis_intent("根据预测结果给我采购量") == "procurement"
    assert route_analysis_intent("介绍一下你自己") == "unknown"


def test_sales_agent_returns_observed_metrics_and_named_tool_trace():
    result = execute_analysis_agent(
        "这个商品销售表现如何",
        sku_id="SKU-1",
        sku_summary=summary_fixture(),
        weekly_demand=weekly_fixture(),
    )

    assert result["intent"] == "sales_snapshot"
    assert result["tool_calls"][0]["tool"] == "sales_analysis.sku_snapshot"
    assert result["evidence"]["revenue"] == 3600.0
    assert result["evidence"]["abc_class"] == "A"


def test_forecast_agent_uses_rolling_origin_and_exposes_candidate_evidence():
    result = execute_analysis_agent(
        "请预测未来需求并说明模型",
        sku_id="SKU-1",
        sku_summary=summary_fixture(),
        weekly_demand=weekly_fixture(),
    )

    assert result["intent"] == "demand_forecast"
    assert result["tool_calls"][0]["tool"] == "forecasting.rolling_origin"
    assert result["tool_calls"][0]["status"] == "completed"
    assert result["evidence"]["folds"] == 3
    assert result["evidence"]["candidate_id"] == "seasonal_naive:4"
    assert result["evidence"]["wape"] == 0.0


def test_procurement_agent_refuses_quantity_when_inventory_inputs_are_missing():
    result = execute_analysis_agent(
        "建议采购多少",
        sku_id="SKU-1",
        sku_summary=summary_fixture(),
        weekly_demand=weekly_fixture(),
    )

    assert result["intent"] == "procurement"
    assert result["tool_calls"][0]["status"] == "needs_input"
    assert "recommended_order_qty" not in result["evidence"]
    assert result["missing_inputs"] == [
        "current_stock",
        "in_transit",
        "safety_stock_units",
        "minimum_order_qty",
    ]
