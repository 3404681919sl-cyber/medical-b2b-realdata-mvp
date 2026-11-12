from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.agent import execute_analysis_agent
from src.analysis import classify_abc, summarize_skus
from src.data_import import (
    prepare_analysis_transactions,
    standardize_transactions,
    validate_transactions,
)
from src.deployment_data import load_application_tables
from src.exports import build_excel_report
from src.forecasting import (
    backtest_forecast_candidates,
    build_sku_diagnostics,
    build_weekly_demand,
    chronological_holdout,
    forecast_croston_sba,
    forecast_moving_average,
    forecast_naive,
    forecast_seasonal_naive,
    normalize_candidate_parameter,
    recommend_forecast_candidate,
    rolling_origin_backtest_candidates,
)
from src.procurement import calculate_procurement_plan


BASE_DIR = Path(__file__).resolve().parent
METADATA_DIR = BASE_DIR / "data" / "metadata"

st.set_page_config(
    page_title="药采智析",
    page_icon="▦",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def load_public_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_application_tables(BASE_DIR)


@st.cache_data(show_spinner=False)
def load_evidence() -> tuple[dict, dict]:
    source = json.loads((METADATA_DIR / "source.json").read_text(encoding="utf-8"))
    quality = json.loads(
        (METADATA_DIR / "quality-report.json").read_text(encoding="utf-8")
    )
    return source, quality


@st.cache_data(show_spinner=False)
def build_analysis_tables(
    transactions: pd.DataFrame, products: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    cleaning = prepare_analysis_transactions(transactions)
    clean = cleaning.clean
    summary = classify_abc(summarize_skus(clean))
    product_lookup = products[["sku_id", "product_name"]].drop_duplicates("sku_id")
    summary = summary.merge(product_lookup, on="sku_id", how="left")
    summary["product_name"] = summary["product_name"].fillna("未匹配商品档案")

    monthly = clean.copy()
    monthly["revenue"] = monthly["quantity"] * monthly["unit_price"]
    monthly["month"] = monthly["sale_date"].dt.to_period("M").astype(str)
    monthly = (
        monthly.groupby("month", as_index=False)
        .agg(units=("quantity", "sum"), revenue=("revenue", "sum"), rows=("sku_id", "size"))
    )
    return clean, summary, monthly, cleaning.exclusion_counts


@st.cache_data(show_spinner=False)
def build_diagnostic_table(
    clean: pd.DataFrame, summary: pd.DataFrame
) -> pd.DataFrame:
    diagnostics = build_sku_diagnostics(
        clean,
        sku_ids=summary["sku_id"].astype(str).tolist(),
        holdout_periods=8,
        min_history_periods=21,
        sparse_threshold=0.25,
    )
    lookup = summary[
        ["sku_id", "product_name", "abc_class", "revenue"]
    ].drop_duplicates("sku_id")
    return diagnostics.merge(lookup, on="sku_id", how="left")


def format_number(value: float) -> str:
    return f"{value:,.0f}"


def render_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --porcelain: #f3f6f4;
          --ink: #152a32;
          --trace: #1f6f8b;
          --moss: #5e755e;
          --amber: #c98224;
          --recall: #b4473f;
        }
        .stApp { background: var(--porcelain); color: var(--ink); }
        h1, h2, h3 { color: var(--ink); letter-spacing: -0.025em; }
        [data-testid="stSidebar"] { background: #e8eeeb; border-right: 1px solid #cad6d0; }
        [data-testid="stMetric"] {
          background: rgba(255,255,255,.68);
          border: 1px solid #d5ded9;
          border-radius: 2px;
          padding: .8rem 1rem;
        }
        .evidence-stamp {
          display: inline-block; padding: .24rem .5rem; border: 1px solid #5e755e;
          color: #3f5d45; font: 600 .74rem 'Cascadia Mono', monospace;
          letter-spacing: .06em; text-transform: uppercase;
        }
        .source-card {
          background: rgba(255,255,255,.72); border-left: 4px solid #1f6f8b;
          padding: 1rem 1.15rem; margin: .6rem 0 1rem;
        }
        .boundary {
          border: 1px solid #d7c29f; background: #fff8ea; padding: .85rem 1rem;
          color: #674817;
        }
        .mono { font-family: 'Cascadia Mono', monospace; font-size: .82rem; }
        button:focus, input:focus, [role="radio"]:focus { outline: 3px solid #91bdcc !important; }
        @media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(source: dict) -> str:
    st.sidebar.markdown("### 证据链")
    st.sidebar.markdown(
        '<span class="evidence-stamp">REAL SOURCE · VERIFIED</span>',
        unsafe_allow_html=True,
    )
    section = st.sidebar.radio(
        "检查阶段",
        [
            "来源与质量",
            "经营分析",
            "需求回测",
            "BadCase分析",
            "智能问数",
            "采购计算",
            "导出证据",
        ],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.caption("数据来源")
    st.sidebar.markdown(
        f"**{source['geography']} · 历史药店数据**  \n"
        f"DOI `{source['doi']}`  \n"
        f"许可 `{source['license']}`"
    )
    st.sidebar.caption("边界：不是中国门店现场试用，不包含实时库存、效期或在途数据。")
    return section


def render_source_quality(
    source: dict, quality: dict, transactions: pd.DataFrame
) -> None:
    st.header("来源与质量")
    st.markdown(
        f"""
        <div class="source-card">
          <strong>{source['title']}</strong><br>
          作者：{source['author']} · 发布：{source['published_date']} · 许可：{source['license']}<br>
          <span class="mono">SHA-256 {source['local_sha256']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if source["integrity_verified"]:
        st.success("原始档案的文件大小与 SHA-256 均与提供方元数据一致。")

    tx = quality["transactions"]
    cols = st.columns(4)
    cols[0].metric("交易明细", format_number(tx["row_count"]))
    cols[1].metric("销售单", format_number(tx["unique_receipts"]))
    cols[2].metric("有销量 SKU", format_number(tx["unique_skus"]))
    cols[3].metric("覆盖日期", f"{tx['date_min']} — {tx['date_max']}")

    issues = pd.DataFrame(
        [
            ["完全重复", tx["exact_duplicate_rows"], "分析时排除，原始文件保留"],
            ["非正销量", tx["non_positive_quantity_rows"], "可能是退货/冲销；需求回测排除"],
            ["售价低于成本", tx["price_below_cost_rows"], "保留销量，单独标记利润风险"],
            ["商品档案未匹配", tx["orphan_sku_rows"], "保留交易，商品名显示未匹配"],
        ],
        columns=["质量现象", "观测行数", "处理原则"],
    )
    st.subheader("观测到的数据问题")
    st.dataframe(issues, hide_index=True, width="stretch")
    st.markdown(
        '<div class="boundary">清洗规则不会回写原始档案；分析层仅排除完全重复、非正销量、无效日期和空商品编码。</div>',
        unsafe_allow_html=True,
    )

    with st.expander("上传自己的销售表并检查字段", expanded=False):
        render_upload_checker()

    with st.expander("查看原始交易样例", expanded=False):
        st.dataframe(transactions.head(50), width="stretch", hide_index=True)


def render_upload_checker() -> None:
    uploaded = st.file_uploader("CSV 或 Excel；文件只在当前应用进程中处理", type=["csv", "xlsx"])
    if uploaded is None:
        st.info("上传后可将任意列名映射为日期、商品、数量、成本和售价。")
        return
    raw = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)
    columns = list(raw.columns)
    if len(columns) < 5:
        st.error("至少需要五列：销售日期、商品编码、数量、单位成本和单位售价。")
        return
    targets = {
        "销售日期": "sale_date",
        "商品编码": "sku_id",
        "销售数量": "quantity",
        "单位成本": "unit_cost",
        "单位售价": "unit_price",
    }
    mapping: dict[str, str] = {}
    for label, canonical in targets.items():
        source_column = st.selectbox(f"{label}对应列", columns, key=f"map_{canonical}")
        mapping[source_column] = canonical
    if len(mapping) < 5:
        st.error("五个标准字段必须映射到不同的原始列。")
        return
    standardized = standardize_transactions(raw, mapping)
    issues = validate_transactions(standardized)
    st.write(f"读取 {len(standardized):,} 行；发现 {len(issues):,} 条规则问题。")
    st.dataframe(standardized.head(30), hide_index=True, width="stretch")
    if not issues.empty:
        st.dataframe(issues.head(100), hide_index=True, width="stretch")


def render_analysis(
    clean: pd.DataFrame,
    summary: pd.DataFrame,
    monthly: pd.DataFrame,
    exclusion_counts: dict[str, int],
) -> None:
    st.header("经营分析")
    st.caption(
        f"分析层纳入 {len(clean):,} 行；排除 {sum(exclusion_counts.values()):,} 行。"
    )
    cols = st.columns(4)
    cols[0].metric("分析 SKU", format_number(summary["sku_id"].nunique()))
    cols[1].metric("销售数量", format_number(summary["units_sold"].sum()))
    cols[2].metric("销售额", format_number(summary["revenue"].sum()))
    cols[3].metric("毛利额", format_number(summary["gross_profit"].sum()))

    trend = px.line(
        monthly,
        x="month",
        y="revenue",
        markers=True,
        labels={"month": "月份", "revenue": "销售额"},
        color_discrete_sequence=["#1f6f8b"],
    )
    trend.update_layout(height=360, margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(trend, width="stretch")

    top = summary.nlargest(20, "revenue").sort_values("revenue")
    bar = px.bar(
        top,
        x="revenue",
        y="product_name",
        orientation="h",
        color="abc_class",
        color_discrete_map={"A": "#1f6f8b", "B": "#5e755e", "C": "#c98224"},
        labels={"revenue": "销售额", "product_name": "商品", "abc_class": "ABC"},
    )
    bar.update_layout(height=600, margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(bar, width="stretch")

    shown = summary[
        [
            "sku_id",
            "product_name",
            "abc_class",
            "units_sold",
            "revenue",
            "gross_profit",
            "revenue_share",
        ]
    ].copy()
    shown["revenue_share"] = shown["revenue_share"].map(lambda value: f"{value:.2%}")
    st.dataframe(shown, hide_index=True, width="stretch", height=500)


def sku_options(summary: pd.DataFrame) -> list[str]:
    return summary.nlargest(150, "revenue")["sku_id"].tolist()


def sku_label(summary: pd.DataFrame, sku_id: str) -> str:
    row = summary.loc[summary["sku_id"] == sku_id].iloc[0]
    return f"{sku_id} · {row['product_name']}"


def render_backtest(clean: pd.DataFrame, summary: pd.DataFrame) -> None:
    st.header("需求回测")
    st.markdown(
        '<div class="boundary">回测只使用时间上更早的数据预测最后 8 周，避免把未来信息泄漏给模型。</div>',
        unsafe_allow_html=True,
    )
    options = sku_options(summary)
    selected_sku = st.selectbox(
        "选择高销售额 SKU",
        options,
        format_func=lambda sku: sku_label(summary, sku),
        key="backtest_sku",
    )
    weekly = build_weekly_demand(clean, selected_sku)
    if len(weekly) < 21:
        st.warning("该商品历史周期不足21周，无法公平比较全部候选策略。")
        return
    results = rolling_origin_backtest_candidates(
        weekly,
        fold_horizon=4,
        folds=3,
        moving_windows=(4, 8, 12),
        seasonal_periods=(4, 13),
        croston_alphas=(0.1, 0.2, 0.3),
    )
    recommended = recommend_forecast_candidate(results)
    cols = st.columns(4)
    cols[0].metric("历史周数", len(weekly))
    cols[1].metric("滚动折数", int(recommended["folds"]))
    cols[2].metric("累计评估周", int(recommended["test_periods"]))
    cols[3].metric("自动推荐 WAPE", f"{recommended['wape']:.1%}")

    labels = results.set_index("candidate_id")["model_label"].to_dict()
    candidate_ids = results["candidate_id"].tolist()
    recommended_id = str(recommended["candidate_id"])
    selected_id = st.selectbox(
        "人工选择策略",
        candidate_ids,
        index=candidate_ids.index(recommended_id),
        format_func=lambda candidate_id: labels[candidate_id],
        help="系统按WAPE、MAE和候选ID依次排序；人工选择会保留，但不会覆盖自动推荐记录。",
    )
    selected_candidate = results.loc[
        results["candidate_id"] == selected_id
    ].iloc[0]
    if selected_id != recommended_id:
        st.warning(
            f"当前人工选择为“{selected_candidate['model_label']}”；自动推荐仍保留为“{recommended['model_label']}”。"
        )

    train, test = chronological_holdout(weekly, holdout_periods=8)
    predicted = forecast_selected_candidate(selected_candidate, train, len(test))

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(x=weekly.index, y=weekly.values, mode="lines", name="实际周销量")
    )
    holdout_index = test.index
    figure.add_trace(
        go.Scatter(
            x=holdout_index,
            y=predicted.values,
            mode="lines",
            name=str(selected_candidate["model_label"]),
            line=dict(color="#c98224", dash="dash"),
        )
    )
    figure.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=25, b=10),
        xaxis_title="周",
        yaxis_title="销量",
    )
    st.plotly_chart(figure, width="stretch")
    display = results[
        ["candidate_id", "model_label", "parameter", "folds", "mae", "wape"]
    ].copy()
    display["is_recommended"] = display["candidate_id"].eq(recommended_id)
    display["wape"] = display["wape"].map(lambda value: f"{value:.1%}")
    st.dataframe(display, hide_index=True, width="stretch")
    candidate_records = [
        {
            "candidate_id": str(row.candidate_id),
            "model_label": str(row.model_label),
            "parameter": normalize_candidate_parameter(row.parameter),
            "folds": int(row.folds),
            "mae": float(row.mae),
            "wape": float(row.wape),
        }
        for row in results.itertuples(index=False)
    ]
    decision_record = {
        "sku_id": selected_sku,
        "history_start": weekly.index.min().date().isoformat(),
        "history_end": weekly.index.max().date().isoformat(),
        "evaluation_scheme": "3-fold expanding-window rolling origin",
        "fold_horizon": 4,
        "folds": 3,
        "selection_rule": "minimum rolling WAPE, then MAE, then candidate_id",
        "automatic_recommendation": recommended_id,
        "manual_selection": selected_id,
        "candidates": candidate_records,
    }
    with st.expander("查看策略决策记录", expanded=False):
        st.json(decision_record)
    st.download_button(
        "下载策略决策记录（JSON）",
        data=json.dumps(decision_record, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=f"forecast_decision_{selected_sku}.json",
        mime="application/json",
    )
    st.caption(
        "候选策略采用三折扩展窗口回测与完整遍历；低误差不代表已在当前门店验证。"
    )


def forecast_selected_candidate(
    candidate: pd.Series, train: pd.Series, horizon: int
) -> pd.Series:
    candidate_id = str(candidate["candidate_id"])
    if candidate_id == "naive:last":
        return forecast_naive(train, horizon)
    parameter = int(candidate["parameter"])
    if candidate_id.startswith("moving_average:"):
        return forecast_moving_average(train, horizon, parameter)
    if candidate_id.startswith("seasonal_naive:"):
        return forecast_seasonal_naive(train, horizon, parameter)
    if candidate_id.startswith("croston_sba:"):
        return forecast_croston_sba(train, horizon, float(candidate["parameter"]))
    raise ValueError(f"Unknown forecast candidate: {candidate_id}")


def render_analysis_agent(clean: pd.DataFrame, summary: pd.DataFrame) -> None:
    st.header("智能问数")
    st.caption("规则意图路由 · 真实工具调用 · 证据与边界同时返回")
    st.markdown(
        '<div class="boundary">当前助手不是自由生成的大模型：它只识别销售表现、需求预测、风险诊断和采购建议四类问题，并展示实际调用的分析工具。</div>',
        unsafe_allow_html=True,
    )
    options = sku_options(summary)
    selected_sku = st.selectbox(
        "选择商品",
        options,
        format_func=lambda sku: sku_label(summary, sku),
        key="agent_sku",
    )
    query = st.text_input(
        "输入业务问题",
        value="这个商品的需求预测是否稳定？",
        help="示例：销售表现如何？需求预测是否稳定？有哪些异常风险？建议采购多少？",
    )
    if not st.button("执行分析", type="primary"):
        st.info("助手会保留意图、工具、参数、证据和拒绝原因，便于复盘。")
        return

    summary_row = summary.loc[summary["sku_id"] == selected_sku].iloc[0].to_dict()
    weekly = build_weekly_demand(clean, selected_sku)
    try:
        result = execute_analysis_agent(
            query,
            sku_id=selected_sku,
            sku_summary=summary_row,
            weekly_demand=weekly,
        )
    except ValueError as error:
        st.error(f"当前历史不足以执行该分析：{error}")
        return

    st.success(str(result["answer"]))
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("工具调用轨迹")
        st.json(result["tool_calls"])
    with col2:
        st.subheader("结构化证据")
        st.json(result.get("evidence", {}))
    if result.get("missing_inputs"):
        st.warning("仍需输入：" + "、".join(result["missing_inputs"]))
    st.caption("；".join(result["boundaries"]))


def render_bad_cases(clean: pd.DataFrame, summary: pd.DataFrame) -> None:
    st.header("BadCase分析")
    st.caption("覆盖率按SKU计算，不按交易行数计算；风险标签不等同于模型失败。")
    diagnostics = build_diagnostic_table(clean, summary)
    coverage = float(diagnostics["eligible"].mean()) if len(diagnostics) else 0.0
    reason_text = diagnostics["reason_codes"].fillna("")

    cols = st.columns(4)
    cols[0].metric("SKU总数", format_number(len(diagnostics)))
    cols[1].metric("可完整回测", f"{coverage:.1%}")
    cols[2].metric(
        "历史不足", format_number(reason_text.str.contains("SHORT_HISTORY").sum())
    )
    cols[3].metric(
        "稀疏需求", format_number(reason_text.str.contains("SPARSE_DEMAND").sum())
    )

    reason_labels = {
        "SHORT_HISTORY": "历史不足21周",
        "ZERO_HOLDOUT_DEMAND": "测试期需求为0",
        "SPARSE_DEMAND": "非零需求周占比低",
        "HIGH_VARIATION": "需求波动较高",
    }
    issues = diagnostics.loc[reason_text.ne("")].copy()
    issues["风险说明"] = issues["reason_codes"].map(
        lambda value: "；".join(
            reason_labels.get(code, code) for code in str(value).split("|") if code
        )
    )
    issues["非零周占比"] = issues["nonzero_share"].map(lambda value: f"{value:.1%}")
    shown = issues[
        [
            "sku_id",
            "product_name",
            "abc_class",
            "eligible",
            "history_periods",
            "非零周占比",
            "holdout_demand",
            "风险说明",
        ]
    ].sort_values(["eligible", "history_periods"])
    st.dataframe(shown, hide_index=True, width="stretch", height=520)
    st.markdown(
        '<div class="boundary">公开数据不含库存与缺货记录，因此本页不会把销量为0直接解释为断货；这里只报告可观察到的历史长度、稀疏性、测试期需求和波动风险。</div>',
        unsafe_allow_html=True,
    )


def render_procurement(clean: pd.DataFrame, summary: pd.DataFrame) -> None:
    st.header("采购计算")
    st.warning("公开数据没有当前库存。本页只有在你填写实际库存参数后才计算，不会自动编造。")
    options = sku_options(summary)
    selected = st.selectbox(
        "选择商品",
        options,
        format_func=lambda sku: sku_label(summary, sku),
        key="procurement_sku",
    )
    weekly = build_weekly_demand(clean, selected)
    if len(weekly) < 21:
        st.warning("该商品历史周期不足21周，无法形成完整策略推荐。")
        return
    candidates = backtest_forecast_candidates(
        weekly,
        holdout_periods=8,
        moving_windows=(4, 8, 12),
        seasonal_periods=(4, 13),
        croston_alphas=(0.1, 0.2, 0.3),
    )
    best = recommend_forecast_candidate(candidates)
    forecast_demand = float(
        forecast_selected_candidate(best, weekly, horizon=1).iloc[0]
    )
    st.write(
        f"自动推荐“{best['model_label']}”给出的单周需求为 **{forecast_demand:,.1f}**；其8周回测WAPE为 **{best['wape']:.1%}**。"
    )

    with st.form("procurement_form"):
        col1, col2, col3 = st.columns(3)
        current_stock = col1.number_input("当前可售库存", min_value=0.0, value=0.0)
        in_transit = col2.number_input("在途库存", min_value=0.0, value=0.0)
        safety_stock = col3.number_input("安全库存数量", min_value=0.0, value=0.0)
        col4, col5 = st.columns(2)
        minimum_order = col4.number_input("最小采购量", min_value=1.0, value=1.0)
        unit_cost = col5.number_input("当前采购单价", min_value=0.0, value=0.0)
        submitted = st.form_submit_button("计算采购建议", type="primary")

    if submitted:
        inputs = pd.DataFrame(
            {
                "sku_id": [selected],
                "forecast_demand": [forecast_demand],
                "safety_stock_units": [safety_stock],
                "current_stock": [current_stock],
                "in_transit": [in_transit],
                "minimum_order_qty": [minimum_order],
                "unit_cost": [unit_cost],
            }
        )
        plan = calculate_procurement_plan(inputs)
        row = plan.iloc[0]
        st.metric("建议采购量", format_number(row["recommended_order_qty"]))
        st.write(
            f"原始缺口 = {forecast_demand:,.1f} + {safety_stock:,.1f} − "
            f"{current_stock:,.1f} − {in_transit:,.1f} = {row['raw_reorder_qty']:,.1f}；"
            f"按最小采购量向上取整。预计采购金额 {row['recommended_order_cost']:,.2f}。"
        )
        st.caption("数量由规则计算；最终采购仍需人工确认效期、供应商履约和真实促销条件。")


def render_export(
    quality: dict, summary: pd.DataFrame, monthly: pd.DataFrame
) -> None:
    st.header("导出证据")
    tx = quality["transactions"]
    quality_table = pd.DataFrame(
        {
            "measure": list(tx.keys()),
            "observed_value": [json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value for value in tx.values()],
        }
    )
    workbook = build_excel_report(
        {
            "数据质量": quality_table,
            "SKU经营分析": summary,
            "月度趋势": monthly,
        }
    )
    st.download_button(
        "下载分析证据包（Excel）",
        data=workbook,
        file_name="药采智析_公开真实数据分析.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
    st.markdown(
        "导出内容保留数据来源边界。作品集引用时，应同时附上 `source.json` 和数据质量报告。"
    )


def main() -> None:
    render_styles()
    source, quality = load_evidence()
    transactions, products = load_public_tables()
    clean, summary, monthly, exclusion_counts = build_analysis_tables(
        transactions, products
    )

    section = render_sidebar(source)
    st.title("药采智析")
    st.caption("真实历史数据 · 本地处理 · 数值可追溯 · 缺少库存时不输出补货量")

    if section == "来源与质量":
        render_source_quality(source, quality, transactions)
    elif section == "经营分析":
        render_analysis(clean, summary, monthly, exclusion_counts)
    elif section == "需求回测":
        render_backtest(clean, summary)
    elif section == "BadCase分析":
        render_bad_cases(clean, summary)
    elif section == "智能问数":
        render_analysis_agent(clean, summary)
    elif section == "采购计算":
        render_procurement(clean, summary)
    else:
        render_export(quality, summary, monthly)


if __name__ == "__main__":
    main()

