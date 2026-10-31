"""Cell2Cell BI demo. Run `python work/pipeline/run_all.py` before this file."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from sklearn.metrics import roc_auc_score, average_precision_score


ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
BUILD = WORK / "build"
MART = BUILD / "customer_mart.parquet"
if not MART.exists():
    raise SystemExit("Chưa có dữ liệu dashboard. Hãy chạy: python work/pipeline/run_all.py")
DATA = pd.read_parquet(MART)
QA = json.loads((BUILD / "qa_report.json").read_text(encoding="utf-8"))
MODEL = json.loads((BUILD / "model_metrics.json").read_text(encoding="utf-8"))
POLICY = pd.read_csv(BUILD / "policy_matrix.csv")

INK = "#12304A"
BLUE = "#1769AA"
TEAL = "#00A99B"
RED = "#DC5964"
MUTED = "#64788B"
GRID = "#E8EEF3"
BG = "#F5F8FB"
PLOT_TEMPLATE = "plotly_white"


def fmt_n(value):
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value, digits=1):
    return f"{100 * value:.{digits}f}%".replace(".", ",")


def wilson(churn, n):
    n = np.asarray(n, dtype=float)
    p = np.asarray(churn, dtype=float) / n
    z = 1.96
    center = (p + z*z/(2*n)) / (1+z*z/n)
    margin = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/(1+z*z/n)
    return center-margin, center+margin


def styled(fig, height=340, percent=False):
    fig.update_layout(
        template=PLOT_TEMPLATE, height=height, margin=dict(l=45, r=45, t=30, b=65),
        font=dict(family="Inter, Segoe UI, sans-serif", color=INK),
        paper_bgcolor="white", plot_bgcolor="white", title_font_size=15,
        colorway=[BLUE, TEAL, RED, "#99B6CC"],
        hoverlabel=dict(bgcolor="white", font_color=INK),
        legend=dict(orientation="h", y=1.15, x=0),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True)
    if percent:
        fig.update_yaxes(tickformat=".0%", range=[0, None])
    return fig


def card(label, value, note=""):
    return html.Div([html.Div(label, className="kpi-label"), html.Div(value, className="kpi-value"),
                     html.Div(note, className="kpi-note")], className="kpi")


def panel(title, item, note="", span=False):
    caption = None
    if isinstance(item, go.Figure):
        caption = html.Div(item.layout.title.text, className="chart-caption")
        item.update_layout(title=None, autosize=True)
        child = dcc.Graph(figure=item, responsive=True, style={"height": "380px", "width": "100%"}, config={"responsive": True, "displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})
    else:
        child = item
    return html.Div([html.Div(title, className="panel-title"), caption, child,
                     html.Div(note, className="panel-note") if note else None],
                    className="panel" + (" wide" if span else ""))


def section(title, sub=""):
    return html.Div([html.H2(title), html.P(sub) if sub else None], className="section-heading")


def insight(label, message):
    return html.Div([html.Span(label, className="insight-label"), html.P(message)], className="insight")


def group_comparison(frame, column, left, right, prefix):
    a = frame[frame[column] == left]
    b = frame[frame[column] == right]
    if not len(a) or not len(b):
        return f"{prefix}: bộ lọc hiện tại không đủ cả hai nhóm để so sánh."
    diff = 100 * (a.Churn.mean() - b.Churn.mean())
    return (f"{prefix}: {left} có churn {fmt_pct(a.Churn.mean())} (n={fmt_n(len(a))}), "
            f"so với {fmt_pct(b.Churn.mean())} (n={fmt_n(len(b))}) ở nhóm {right}; "
            f"chênh {diff:+.1f} điểm %. Đây là liên hệ quan sát, chưa phải tác động nhân quả.")


def group_metrics(frame, column, order=None):
    summary = (frame.groupby(column, dropna=False, observed=True)["Churn"]
               .agg(n="size", churners="sum").reset_index())
    if not pd.api.types.is_numeric_dtype(summary[column]):
        summary[column] = summary[column].astype(str).replace("<NA>", "Không rõ")
    summary["rate"] = summary["churners"] / summary["n"]
    summary["low"], summary["high"] = wilson(summary["churners"], summary["n"])
    if order:
        summary["ord"] = pd.Categorical(summary[column], categories=order, ordered=True)
        summary = summary.sort_values("ord")
    return summary


def rate_chart(frame, column, title, order=None):
    s = group_metrics(frame, column, order)
    horizontal = max(s[column].astype(str).str.len(), default=0) > 14
    fig = go.Figure(go.Bar(
        x=s["rate"] if horizontal else s[column],
        y=s[column] if horizontal else s["rate"],
        orientation="h" if horizontal else "v", marker_color=BLUE,
        **{("error_x" if horizontal else "error_y"): dict(type="data", symmetric=False, array=s["high"]-s["rate"],
                     arrayminus=s["rate"]-s["low"], color=MUTED, thickness=1),
        },
        customdata=np.stack([s["n"], s["churners"]], axis=-1),
        hovertemplate=("%{y}<br>Churn: %{x:.1%}" if horizontal else "%{x}<br>Churn: %{y:.1%}") + "<br>Khách: %{customdata[0]:,}<br>Churner: %{customdata[1]:,}<extra></extra>",
    ))
    fig.update_layout(title=title, xaxis_title=None, yaxis_title="Tỷ lệ churn")
    fig = styled(fig, percent=not horizontal)
    if horizontal:
        fig.update_layout(xaxis_title="Tỷ lệ churn", yaxis_title=None)
        fig.update_xaxes(tickformat=".0%", rangemode="tozero")
        fig.update_yaxes(autorange="reversed", automargin=True)
        fig.update_yaxes(tickvals=s[column], ticktext=["<br>".join(textwrap.wrap(str(v), 18)) for v in s[column]])
    return fig


def volume_chart(frame, column, title, order=None):
    s = group_metrics(frame, column, order)
    horizontal = max(s[column].astype(str).str.len(), default=0) > 14
    fig = px.bar(s, x="n" if horizontal else column, y=column if horizontal else "n", text="n", title=title,
                 orientation="h" if horizontal else "v")
    fig.update_traces(marker_color=TEAL, textposition="outside", cliponaxis=False,
                      hovertemplate=("%{y}<br>Khách: %{x:,}<extra></extra>" if horizontal else "%{x}<br>Khách: %{y:,}<extra></extra>"))
    fig.update_layout(xaxis_title="Số khách hàng" if horizontal else None, yaxis_title=None if horizontal else "Số khách hàng")
    if horizontal:
        fig.update_yaxes(autorange="reversed", tickvals=s[column], ticktext=["<br>".join(textwrap.wrap(str(v), 18)) for v in s[column]])
        fig.update_xaxes(range=[0, float(s.n.max()) * 1.2])
    return styled(fig)


def make_table(frame, columns, max_rows=20):
    return html.Div(html.Table([
        html.Thead(html.Tr([html.Th(label) for _, label in columns])),
        html.Tbody([html.Tr([html.Td(str(row[key])) for key, _ in columns])
                    for _, row in frame.head(max_rows).iterrows()]),
    ], className="data-table"), className="table-wrap")


def overview(frame):
    churn = int(frame.Churn.sum())
    rate = frame.Churn.mean()
    high = frame[frame.RiskDecile >= 9]
    kpis = html.Div([
        card("Khách hàng trong lát cắt", fmt_n(len(frame)), "Mẫu số của mọi KPI dưới đây"),
        card("Khách hàng churn", fmt_n(churn), "Churn = Yes trong cùng lát cắt"),
        card("Tỷ lệ churn", fmt_pct(rate, 2), "Baseline toàn nguồn: " + fmt_pct(QA["baseline_churn_rate"], 2)),
        card("Khách thuộc decile 9–10", fmt_n(len(high)), "Top 20% toàn nguồn, trong lát cắt hiện tại"),
    ], className="kpi-grid")
    tenure_order = ["6–11 tháng", "12–18 tháng", "19–24 tháng", "25+ tháng"]
    reason = group_metrics(frame, "ReasonCode").sort_values("churners", ascending=False)
    fig_reason = px.bar(reason, x="churners", y="ReasonCode", orientation="h", text="churners",
                        title="Số churner theo tín hiệu rà soát")
    fig_reason.update_traces(marker_color=RED, textposition="outside", cliponaxis=False)
    fig_reason.update_layout(xaxis_title="Số churner", yaxis_title=None, yaxis=dict(autorange="reversed"))
    fig_reason.update_xaxes(range=[0, max(1, float(reason.churners.max())) * 1.2])
    fig_reason.update_yaxes(tickvals=reason.ReasonCode, ticktext=["<br>".join(textwrap.wrap(v, 18)) for v in reason.ReasonCode])
    return [html.Div([html.Span("01 / EXECUTIVE VIEW", className="eyebrow"), html.H1("Churn đang tập trung ở đâu?"),
                      html.P("Bắt đầu từ quy mô vấn đề, sau đó đi sâu vào tín hiệu và nhóm cần ưu tiên.")], className="page-intro"),
            kpis,
            insight("ĐỌC NHANH", group_comparison(frame, "TenureBand", "12–18 tháng", "6–11 tháng", "Cửa sổ tenure")),
            section("Quy mô và phân bố", "Các nhóm có rủi ro cao chỉ hữu ích khi có đủ khách hàng để hành động."),
            html.Div([
                panel("Churn theo tenure", rate_chart(frame, "TenureBand", "Tỷ lệ churn và CI 95%", tenure_order),
                      "Snapshot theo nhóm thâm niên; không phải đường thời gian."),
                panel("Quy mô tenure", volume_chart(frame, "TenureBand", "Số khách hàng", tenure_order)),
                panel("Tín hiệu rà soát", styled(fig_reason),
                      "Reason code là rule vận hành sơ bộ, chưa chứng minh nguyên nhân."),
                panel("Chất lượng nguồn", html.Div([
                    html.Div([html.Strong(fmt_n(QA["raw_rows"])), " dòng raw / ", html.Strong(str(QA["raw_columns"])), " cột"], className="quality-line"),
                    html.Div([html.Strong(fmt_n(QA["missing_any_model_feature_rows"])), " khách thiếu ít nhất một predictor"], className="quality-line"),
                    html.Div([html.Strong(fmt_n(QA["complete_58_column_rows"])), " khách complete-case cả 58 cột"], className="quality-line"),
                    html.P("Raw được giữ nguyên; missing numeric được CatBoost xử lý trong huấn luyện. Không dùng 49.752 làm mẫu số mặc định.", className="quality-note"),
                ], className="quality-box")),
            ], className="panel-grid")]


def drivers(frame):
    tenure_order = ["6–11 tháng", "12–18 tháng", "19–24 tháng", "25+ tháng"]
    equipment_order = ["≤180 ngày", "181–365 ngày", "366–730 ngày", ">730 ngày", "Giá trị âm", "Không rõ"]
    value_order = ["Thấp (≤35)", "Trung bình (35–70)", "Cao (>70)", "Giá trị âm", "Không rõ"]
    usage_order = ["Giảm mạnh (≤-83)", "Giảm nhẹ (-83–0)", "Tăng nhẹ (0–66)", "Tăng mạnh (>66)", "Không rõ"]
    return [html.Div([html.Span("02 / DRIVERS", className="eyebrow"), html.H1("Những tín hiệu nào đi cùng churn?"),
                      html.P("Mỗi cặp biểu đồ đặt tỷ lệ rủi ro cạnh quy mô nhóm để tránh ưu tiên một ô quá nhỏ.")], className="page-intro"),
            insight("TÍN HIỆU 1", group_comparison(frame, "EquipmentAgeBand", ">730 ngày", "≤180 ngày", "Tuổi thiết bị")),
            section("Vòng đời & thiết bị", "Mối liên hệ quan sát được; chưa suy ra nguyên nhân."),
            html.Div([
                panel("Tenure", rate_chart(frame, "TenureBand", "Churn theo thời gian sử dụng", tenure_order)),
                panel("Quy mô", volume_chart(frame, "TenureBand", "Khách hàng theo tenure", tenure_order)),
                panel("Tuổi thiết bị", rate_chart(frame, "EquipmentAgeBand", "Churn theo tuổi thiết bị", equipment_order)),
                panel("Quy mô", volume_chart(frame, "EquipmentAgeBand", "Khách hàng theo tuổi thiết bị", equipment_order)),
            ], className="panel-grid"),
            insight("TÍN HIỆU 2", group_comparison(frame, "UsageTrendBand", "Giảm mạnh (≤-83)", "Tăng nhẹ (0–66)", "Thay đổi sử dụng")),
            section("Giá trị, phí & hành vi", "MonthlyRevenue là proxy giá trị; PercChangeMinutes giữ đơn vị nguồn chưa xác minh."),
            html.Div([
                panel("Value tier", rate_chart(frame, "ValueTier", "Churn theo doanh thu tháng", value_order)),
                panel("Quy mô", volume_chart(frame, "ValueTier", "Khách hàng theo value tier", value_order)),
                panel("Phí định kỳ", rate_chart(frame, "ChargeBand", "Churn theo recurring charge")),
                panel("Mức sử dụng", rate_chart(frame, "MinutesBand", "Churn theo monthly minutes")),
                panel("Thay đổi sử dụng", rate_chart(frame, "UsageTrendBand", "Churn theo mức thay đổi minutes", usage_order),
                      "Ngưỡng theo giá trị nguồn; không diễn giải là phần trăm."),
                panel("Độ phủ của tín hiệu", volume_chart(frame, "UsageTrendBand", "Khách hàng theo mức thay đổi minutes", usage_order)),
            ], className="panel-grid")]


def risk(frame):
    y = frame.Churn.to_numpy()
    score = frame.RiskScore.to_numpy()
    auc = roc_auc_score(y, score) if len(np.unique(y)) == 2 else np.nan
    pr = average_precision_score(y, score) if len(np.unique(y)) == 2 else np.nan
    decile = group_metrics(frame, "RiskDecile").sort_values("RiskDecile")
    fig_decile = go.Figure(go.Bar(x=decile.RiskDecile, y=decile.rate, marker_color=BLUE,
                                   customdata=np.stack([decile.n, decile.churners], axis=-1),
                                   hovertemplate="Decile %{x}<br>Churn: %{y:.1%}<br>n=%{customdata[0]:,}<br>Churner=%{customdata[1]:,}<extra></extra>"))
    fig_decile.update_layout(title="Tỷ lệ churn theo risk decile", xaxis_title="Decile (10 = cao nhất)", yaxis_title="Tỷ lệ churn")
    sorted_frame = frame.sort_values("RiskScore", ascending=False).reset_index(drop=True)
    curve = pd.DataFrame({"population": np.arange(1, len(frame)+1)/len(frame),
                          "captured": sorted_frame.Churn.cumsum()/max(1, int(frame.Churn.sum()))})
    fig_gain = go.Figure()
    fig_gain.add_trace(go.Scatter(x=curve.population, y=curve.captured, mode="lines", name="Mô hình", line=dict(color=TEAL, width=3)))
    fig_gain.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Ngẫu nhiên", line=dict(color=MUTED, dash="dash")))
    fig_gain.update_layout(title="Cumulative gain", xaxis_title="Tỷ lệ khách được liên hệ", yaxis_title="Tỷ lệ churner được tiếp cận")
    fig_gain.update_xaxes(tickformat=".0%")
    fig_gain.update_yaxes(tickformat=".0%")
    cal = frame.assign(score_bin=pd.qcut(frame.RiskScore, min(10, len(frame)), duplicates="drop"))
    cal = cal.groupby("score_bin", observed=True).agg(predicted=("RiskScore", "mean"), observed=("Churn", "mean"), n=("Churn", "size"))
    fig_cal = go.Figure()
    fig_cal.add_trace(go.Scatter(x=cal.predicted, y=cal.observed, mode="lines+markers", name="Quan sát", line=dict(color=BLUE, width=3)))
    fig_cal.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Lý tưởng", line=dict(color=MUTED, dash="dash")))
    fig_cal.update_layout(title="Calibration theo 10 nhóm score", xaxis_title="Xác suất dự đoán", yaxis_title="Churn quan sát")
    fig_cal.update_xaxes(tickformat=".0%", range=[0, max(.5, float(cal.predicted.max())+.05)])
    fig_cal.update_yaxes(tickformat=".0%", range=[0, max(.5, float(cal.observed.max())+.05)])
    segments = frame.groupby("PrioritySegment").agg(n=("Churn", "size"), churners=("Churn", "sum"),
                                                      avg_risk=("RiskScore", "mean"), avg_revenue=("MonthlyRevenue", "mean")).reset_index()
    segments["churn_rate"] = segments.churners / segments.n
    segments = segments.sort_values("PrioritySegment")
    segments["n"] = segments.n.map(fmt_n)
    segments["churners"] = segments.churners.map(fmt_n)
    segments["churn_rate"] = segments.churn_rate.map(fmt_pct)
    segments["avg_risk"] = segments.avg_risk.map(fmt_pct)
    segments["avg_revenue"] = segments.avg_revenue.map(lambda v: f"{v:.1f}" if pd.notna(v) else "n.a.")
    capacity = []
    for pct in (5, 10, 20):
        selected = frame.nlargest(max(1, int(np.ceil(len(frame)*pct/100))), "RiskScore")
        capacity.append({"Capacity": f"{pct}%", "Khách": fmt_n(len(selected)),
                         "Churner tiếp cận": fmt_n(selected.Churn.sum()),
                         "Precision": fmt_pct(selected.Churn.mean()),
                         "Recall": fmt_pct(selected.Churn.sum()/max(1, frame.Churn.sum())),
                         "Lift": f"{selected.Churn.mean()/frame.Churn.mean():.2f}×" if frame.Churn.mean() else "n.a."})
    return [html.Div([html.Span("03 / RISK & SEGMENTS", className="eyebrow"), html.H1("Ai nên được ưu tiên?"),
                      html.P("RiskScore dùng dự đoán 3-fold ngoài mẫu; các chỉ số của bộ lọc chỉ mô tả lát cắt hiện tại.")], className="page-intro"),
            html.Div([card("ROC-AUC", f"{auc:.3f}" if np.isfinite(auc) else "n.a.", "Ngoài mẫu, cohort sau lọc"),
                      card("PR-AUC", f"{pr:.3f}" if np.isfinite(pr) else "n.a.", "Baseline PR = churn rate"),
                      card("Log loss toàn nguồn", f"{MODEL['log_loss']:.3f}", "Mô hình 10 feature"),
                      card("Depth phổ biến", str(MODEL["chosen_depth"]), "Chọn trong train của từng fold")], className="kpi-grid"),
            insight("Ý NGHĨA VẬN HÀNH", f"Nếu chỉ liên hệ top 10% risk trong lát cắt này, nhóm có {fmt_n(min(len(frame), max(1, int(np.ceil(len(frame)*.10)))))} khách. Đường gain và bảng capacity bên dưới cho thấy bao nhiêu churner quá khứ được tiếp cận; chúng chưa đo hiệu quả của chính sách giữ chân."),
            html.Div([panel("Phân tầng rủi ro", styled(fig_decile, percent=True)),
                      panel("Giới hạn capacity", styled(fig_gain)),
                      panel("Độ tin cậy score", styled(fig_cal), "Calibration chỉ phản ánh snapshot và dữ liệu đánh giá hiện tại."),
                      panel("Capacity 5 / 10 / 20%", make_table(pd.DataFrame(capacity), [(x, x) for x in capacity[0]]),
                            "Churner tiếp cận là kết quả đối chiếu với nhãn quá khứ, không phải uplift của chính sách."),
                      panel("Phân khúc ưu tiên", make_table(segments, [("PrioritySegment", "Nhóm"), ("n", "Khách"),
                        ("churners", "Churner"), ("churn_rate", "Churn"), ("avg_risk", "Risk TB"),
                        ("avg_revenue", "Revenue TB")]),
                        "P1–P4 loại trừ nhau; MonthlyRevenue là value proxy.", span=True)], className="panel-grid")]


def strategy(frame):
    s = group_metrics(frame, "ReasonCode").sort_values("churners", ascending=False)
    s["n"] = s.n.map(fmt_n)
    s["churners"] = s.churners.map(fmt_n)
    s["rate"] = s.rate.map(fmt_pct)
    cards = []
    for _, row in POLICY.iterrows():
        matched = frame[(frame.ReasonCode == row.ReasonCode) & (frame.RiskDecile >= 7)]
        cards.append(html.Div([
            html.Div([html.Span(row.Status.upper(), className="tag"), html.H3(row.ReasonCode)], className="policy-head"),
            html.P(row["Eligibility hypothesis"], className="policy-eligibility"),
            html.Div([html.Strong(fmt_n(len(matched))), " khách đủ điều kiện · ", html.Strong(fmt_pct(matched.Churn.mean()) if len(matched) else "n.a."), " churn"], className="policy-stat"),
            html.Div([html.Small("CAN THIỆP ĐỀ XUẤT"), html.P(row["Treatment hypothesis"])], className="policy-detail"),
            html.Div([html.Small("KPI CHÍNH"), html.P(row["Primary KPI"])], className="policy-detail"),
            html.Div([html.Small("GUARDRAIL"), html.P(row.Guardrail)], className="policy-detail"),
        ], className="policy-card"))
    return [html.Div([html.Span("04 / RETENTION STRATEGY", className="eyebrow"), html.H1("Can thiệp nào đáng thử?"),
                      html.P("Reason code là tín hiệu để rà soát. Mọi treatment cần so với nhóm eligible control trước khi mở rộng.")], className="page-intro"),
            html.Div([card("Nhóm ưu tiên P1–P3", fmt_n(frame.PrioritySegment.ne("P4 · Theo dõi").sum()), "Ứng viên xem xét liên hệ"),
                      card("Reason code", str(frame.ReasonCode.nunique()), "Rule giả thuyết, có fallback"),
                      card("Policy đã được thử nghiệm", "0", "Chưa có treatment/control trong nguồn")], className="kpi-grid three"),
            section("Tín hiệu và quy mô", "Mỗi khách có một reason code ưu tiên theo thứ tự rule; các tín hiệu có thể chồng lắp."),
            panel("Quy mô theo reason", make_table(s, [("ReasonCode", "Reason code"), ("n", "Khách"),
                ("churners", "Churner"), ("rate", "Churn rate")])),
            section("Policy matrix", "Ưu tiên thử device, usage decline và lifecycle trong nhóm risk decile ≥7. Plan review cần thêm bằng chứng; không báo ROI khi thiếu cost/uplift."),
            html.Div(cards, className="policy-grid"),
            html.Div([html.H3("Thiết kế phép thử tối thiểu"),
                      html.P("Trong từng nhóm đủ điều kiện, chia ngẫu nhiên treatment và business-as-usual control. Khóa outcome window, KPI churn và guardrail trước khi chạy. So sánh theo intent-to-treat; chỉ mở rộng khi có hiệu quả tăng thêm và chi phí chấp nhận được."),
                      html.P("CreditRating chỉ nằm trong mô hình đã khóa và đánh giá fairness; không dùng đơn lẻ để từ chối hỗ trợ hoặc đưa ra điều kiện bất lợi.")], className="callout")]


app = Dash(
    __name__,
    title="Cell2Cell | Retention Intelligence",
    suppress_callback_exceptions=True,
    assets_folder=str(ROOT / "assets"),
)
app.layout = html.Div([
    dcc.Location(id="url"),
    html.Aside([
        html.Div([html.Div("C2C", className="brand-mark"), html.Div([html.Strong("Cell2Cell"), html.Span("RETENTION INTELLIGENCE")])], className="brand"),
        html.Div("WORKSPACE", className="nav-label"),
        dcc.Link("◫  Overview", href="/", className="nav-item"),
        dcc.Link("▥  Drivers", href="/drivers", className="nav-item"),
        dcc.Link("◉  Risk & Segments", href="/risk", className="nav-item"),
        dcc.Link("◇  Retention Strategy", href="/strategy", className="nav-item"),
        html.Div([html.Div("DATA SNAPSHOT", className="nav-label"),
                  html.Div("51.047 khách hàng · 58 cột", className="side-note"),
                  html.Div("Churn là outcome trong một snapshot.", className="side-note")], className="sidebar-bottom"),
    ], className="sidebar"),
    html.Main([
        html.Div([html.Div([html.Span("CELL2CELL / BUSINESS INTELLIGENCE"), html.Button("Đặt lại bộ lọc ↺", id="reset-filters", className="reset-button")], className="topbar-line"),
                  html.Div([html.Div([html.Label("TENURE"), dcc.Dropdown(id="tenure-filter", options=[{"label": x, "value": x} for x in ["6–11 tháng", "12–18 tháng", "19–24 tháng", "25+ tháng"]], multi=True, placeholder="Tất cả")]),
                            html.Div([html.Label("WEB CAPABILITY"), dcc.Dropdown(id="web-filter", options=[{"label": x, "value": x} for x in ["Yes", "No"]], multi=True, placeholder="Tất cả")]),
                            html.Div([html.Label("VALUE TIER"), dcc.Dropdown(id="value-filter", options=[{"label": x, "value": x} for x in ["Thấp (≤35)", "Trung bình (35–70)", "Cao (>70)", "Giá trị âm", "Không rõ"]], multi=True, placeholder="Tất cả")]),
                            html.Div([html.Label("RISK DECILE"), dcc.Dropdown(id="risk-filter", options=[{"label": str(x), "value": x} for x in range(1,11)], multi=True, placeholder="Tất cả")])], className="filters")], className="topbar"),
        html.Div(id="page-content", className="content"),
        html.Footer("Nguồn: data/cell2celltrain.csv · Tỷ lệ luôn theo cohort sau lọc · Chỉ số mô hình từ dự đoán ngoài mẫu · Chính sách là giả thuyết", className="footer"),
    ], className="main"),
], className="shell")


@app.callback(Output("page-content", "children"), Input("url", "pathname"),
              Input("tenure-filter", "value"), Input("web-filter", "value"),
              Input("value-filter", "value"), Input("risk-filter", "value"))
def render_page(path, tenure, web, value, risk_decile):
    frame = DATA
    if tenure:
        frame = frame[frame.TenureBand.isin(tenure)]
    if web:
        frame = frame[frame.HandsetWebCapable.isin(web)]
    if value:
        frame = frame[frame.ValueTier.isin(value)]
    if risk_decile:
        frame = frame[frame.RiskDecile.isin(risk_decile)]
    if frame.empty:
        return html.Div([html.H2("Không có khách hàng cho bộ lọc này"), html.P("Hãy nới bộ lọc để xem lại phân tích.")], className="empty")
    return {"/": overview, "/drivers": drivers, "/risk": risk, "/strategy": strategy}.get(path, overview)(frame)


@app.callback(Output("tenure-filter", "value"), Output("web-filter", "value"),
              Output("value-filter", "value"), Output("risk-filter", "value"),
              Input("reset-filters", "n_clicks"), prevent_initial_call=True)
def reset_filters(_):
    return None, None, None, None


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
