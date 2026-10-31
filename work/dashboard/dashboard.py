"""Dashboard BI churn Cell2Cell (4 trang). Chạy work/viz/prepare_viz_data.py trước, rồi: python work/dashboard/dashboard.py"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from dash import Dash, Input, Output, dcc, html

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "viz"))
import charts as c  # noqa: E402

DATA_PATH = ROOT / "work" / "build" / "viz_customers.parquet"
if not DATA_PATH.exists():
    raise SystemExit("Chưa có dữ liệu dashboard. Hãy chạy: python work/viz/prepare_viz_data.py")
DATA = pd.read_parquet(DATA_PATH)
COMPANY = c.kpis(DATA)
HAS_RISK = "RiskDecile" in DATA

FILTERS = [
    ("tenure", "Thời gian sử dụng", "TenureBand"),
    ("region", "Vùng", "Region"),
    ("equipment", "Tuổi thiết bị", "EquipmentAgeBand"),
    ("credit", "Hạng tín dụng", "CreditRating"),
]

PAGES = [
    ("/", "Tổng quan", "Churn lớn đến đâu và mất bao nhiêu doanh thu?"),
    ("/nguyen-nhan", "Nguyên nhân", "Tín hiệu nào đi cùng khách rời bỏ?"),
    ("/rui-ro", "Chân dung & rủi ro", "Ai đang có nguy cơ rời bỏ?"),
    ("/hanh-dong", "Hành động", "Giữ ai, bằng cách nào?"),
]

POLICIES = {
    "Đã báo động": ("Thiết kế lại ưu đãi giữ chân; chuyên viên cấp cao xử lý trong 24h; ghi nhận lý do rời bỏ.",
                    "Churn 60 ngày · tỷ lệ nhận ưu đãi"),
    "Hết hợp đồng": ("Gọi chăm sóc chủ động từ tháng 10; ưu đãi gia hạn 12 tháng trước tháng 11.",
                     "Tỷ lệ gia hạn · churn tháng 11–13"),
    "Máy cũ": ("Đổi máy smartphone trả góp/trợ giá gắn cam kết 12 tháng; ưu tiên máy không hỗ trợ web.",
               "% nhận đổi máy · churn 90 ngày · chi phí/khách giữ được"),
    "Rủi ro cao (mô hình)": ("Khảo sát hài lòng và tư vấn gói phù hợp; ưu đãi cá nhân hóa cho khách giá trị cao.",
                             "Churn 90 ngày · doanh thu giữ được"),
    "Ổn định": ("Duy trì chất lượng, chương trình khách hàng thân thiết.", "Theo dõi định kỳ"),
}


def options(col):
    values = DATA[col]
    if hasattr(values, "cat"):
        items = [v for v in values.cat.categories if v in set(values)]
    elif col == "CreditRating":
        items = [v for v in c.CREDIT_ORDER if v in set(values)]
    else:
        items = sorted(values.dropna().unique())
    return [{"label": str(v), "value": str(v)} for v in items]


def apply_filters(values) -> pd.DataFrame:
    df = DATA
    for (_, _, col), selected in zip(FILTERS, values):
        if selected:
            df = df[df[col].astype(str).isin(selected)]
    return df


# ---------- thành phần giao diện ----------

def kpi(label, value, delta=None, good_when_negative=True, note=""):
    children = [html.Div(label, className="kpi-label"), html.Div(value, className="kpi-value")]
    if delta is not None:
        worse = delta > 0 if good_when_negative else delta < 0
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "■")
        children.append(html.Div(f"{arrow} {c.fmt_ratio(abs(100 * delta))} điểm % so với toàn công ty",
                                 className="kpi-delta " + ("bad" if worse else "good")))
    if note:
        children.append(html.Div(note, className="kpi-note"))
    return html.Div(children, className="kpi")


def rate_kpi(label, part: pd.DataFrame, note=""):
    if not len(part):
        return kpi(label, "–", note="Không có khách trong lát cắt")
    rate = c.baseline(part)
    return kpi(label, c.fmt_pct(rate), rate - COMPANY["rate"], note=note or f"n = {c.fmt_n(len(part))}")


def graph(fig, wide=False):
    return html.Div(dcc.Graph(figure=fig, config={"displaylogo": False, "responsive": True,
                                                   "displayModeBar": "hover", "modeBarButtons": [["toImage"]],
                                                   "toImageButtonOptions": {"scale": 2}}),
                    className="panel" + (" wide" if wide else ""))


def insight_box(figs):
    titles = [f.layout.title.text.split("<br>")[0].replace("<b>", "").replace("</b>", "") for f in figs]
    return html.Div([html.Div("Insight chính", className="insight-label"),
                     html.Ul([html.Li(t) for t in titles if t])], className="insight")


def header(path, df):
    _, name, question = next(p for p in PAGES if p[0] == path)
    scope = ("Toàn bộ khách hàng" if len(df) == len(DATA)
             else f"Lát cắt đang lọc: {c.fmt_n(len(df))} / {c.fmt_n(len(DATA))} khách")
    return html.Div([html.Div(name.upper(), className="eyebrow"), html.H1(question),
                     html.P(scope, className="scope")], className="page-head")


# ---------- 4 trang ----------

def page_overview(df):
    k = c.kpis(df)
    cards = html.Div([
        kpi("Tổng khách hàng", c.fmt_n(k["customers"])),
        kpi("Khách rời bỏ", c.fmt_n(k["churners"])),
        kpi("Churn rate", c.fmt_pct(k["rate"]), k["rate"] - COMPANY["rate"] if len(df) != len(DATA) else None,
            note="Toàn công ty" if len(df) == len(DATA) else ""),
        kpi("Doanh thu/tháng của khách rời bỏ", c.fmt_money(k["lost_revenue"]),
            note=f"{c.fmt_pct(k['lost_revenue'] / df.MonthlyRevenue.sum())} tổng doanh thu tháng"),
        kpi("Thời gian sử dụng TB", f"{c.fmt_ratio(k['tenure_mean'])} tháng"),
    ], className="kpi-grid five")
    figs = [c.tenure_line(df), c.churn_donut(df), c.region_bar(df), c.region_treemap(df)]
    return [cards, insight_box([figs[0], figs[2], figs[3]]),
            html.Div([graph(figs[0], wide=True), graph(figs[1]), graph(figs[3]), graph(figs[2], wide=True)],
                     className="grid")]


def page_drivers(df):
    cards = html.Div([
        rate_kpi("Churn khách máy > 2 năm", df[df.EquipmentAgeBand == ">730 ngày"]),
        rate_kpi("Churn khách máy không hỗ trợ web", df[df.HandsetWebCapable == "No"]),
        rate_kpi("Churn khách tháng 11–12", df[df.MonthsInService.between(11, 12)]),
        rate_kpi("Churn khách không gọi CSKH", df[df.CustomerCareCalls == 0]),
    ], className="kpi-grid")
    figs = [
        c.FIGURES["C06_tuoi_thiet_bi"](df), c.tenure_equipment_heatmap(df), c.device_grouped(df),
        c.FIGURES["C10_goi_cskh"](df), c.FIGURES["C11_cuoc_goi_rot"](df), c.overage_bubble(df),
    ]
    return [cards, insight_box([figs[0], figs[1], figs[3]]),
            html.Div([graph(f) for f in figs], className="grid")]


def page_risk(df):
    retention = df[df.MadeCallToRetentionTeam == "Yes"]
    cards = [rate_kpi("Churn khách đã gọi retention", retention),
             rate_kpi("Churn khách tín dụng hạng 1–3", df[df.CreditRating.isin(c.CREDIT_ORDER[:3])])]
    if HAS_RISK:
        high = df[df.RiskDecile >= 8]
        cards += [kpi("Khách rủi ro cao (decile 8–10)", c.fmt_n(len(high)),
                      note=f"{c.fmt_pct(len(high) / len(df))} lát cắt"),
                  rate_kpi("Churn thực tế nhóm rủi ro cao", high)]
    funnel, credit, demo = c.retention_funnel(df), c.credit_bar(df), c.demographic_multiples(df)
    risk_figs = [c.decile_bar(df), c.gain_curve(df)] if HAS_RISK else []
    figs = [funnel, *risk_figs, credit, demo]
    panels = [graph(funnel, wide=True), *[graph(f) for f in risk_figs], graph(credit), graph(demo, wide=not HAS_RISK)]
    return [html.Div(cards, className="kpi-grid"), insight_box(figs[:3]), html.Div(panels, className="grid")]


def policy_card(row):
    action, metric = POLICIES.get(str(row.ActionSegment), ("", ""))
    priority = "priority" if row.ActionSegment != "Ổn định" else "stable"
    return html.Div([
        html.Div([html.H3(str(row.ActionSegment)),
                  html.Span(c.fmt_pct(row.rate), className="badge " + ("bad" if row.rate > COMPANY["rate"] else "good"))],
                 className="policy-head"),
        html.Div([html.Span(f"{c.fmt_n(row.n)} khách"), html.Span(f"{c.fmt_money(row.revenue_at_risk)}/tháng bị đe dọa")],
                 className="policy-stats"),
        html.P(action, className="policy-action"),
        html.Div([html.Small("KPI đo: "), html.Span(metric)], className="policy-metric"),
    ], className="policy-card " + priority)


def page_action(df):
    seg = c.segment_summary(df)
    act = seg[seg.ActionSegment != "Ổn định"]
    act_rate = act.churners.sum() / act.n.sum() if act.n.sum() else float("nan")
    cards = html.Div([
        kpi("Khách cần can thiệp", c.fmt_n(act.n.sum()), note=f"{c.fmt_pct(act.n.sum() / len(df))} lát cắt · 4 phân khúc"),
        kpi("Doanh thu/tháng bị đe dọa", c.fmt_money(act.revenue_at_risk.sum()), note="Σ doanh thu × churn rate của nhóm"),
        kpi("Churn nhóm cần can thiệp", c.fmt_pct(act_rate) if act.n.sum() else "–",
            act_rate - COMPANY["rate"] if act.n.sum() else None),
    ], className="kpi-grid three")
    fig = c.segment_bubble(df)
    return [cards, insight_box([fig]),
            html.Div([graph(fig, wide=True)], className="grid"),
            html.H2("Chính sách đề xuất theo phân khúc", className="section-title"),
            html.Div([policy_card(r) for r in seg.itertuples()], className="policy-grid"),
            html.P("Phân khúc xét theo thứ tự ưu tiên: Đã báo động → Hết hợp đồng (tháng 10–13) → Máy cũ → Rủi ro cao. "
                   "Đề xuất cần A/B test (nhóm thử/đối chứng) trước khi triển khai rộng.", className="note")]


RENDERERS = {"/": page_overview, "/nguyen-nhan": page_drivers, "/rui-ro": page_risk, "/hanh-dong": page_action}


# ---------- app ----------

app = Dash(__name__, title="Cell2Cell · Churn BI", assets_folder="assets_bi", suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id="url"),
    html.Aside([
        html.Div([html.Div("C2C", className="brand-mark"),
                  html.Div([html.Strong("Cell2Cell"), html.Span("Churn & Retention BI")])], className="brand"),
        html.Nav(id="nav", className="nav"),
        html.Div(f"Nguồn: cell2celltrain.csv · {c.fmt_n(len(DATA))} khách · snapshot", className="side-note"),
    ], className="sidebar"),
    html.Main([
        html.Div([
            *[html.Div([html.Label(label, htmlFor=f"f-{key}"),
                        dcc.Dropdown(id=f"f-{key}", options=options(col), multi=True, placeholder="Tất cả")],
                       className="filter") for key, label, col in FILTERS],
            html.Button("Xóa lọc", id="reset", className="reset", n_clicks=0),
        ], className="filters"),
        dcc.Loading(html.Div(id="page"), type="dot", color=c.ACCENT),
        html.Footer("Quan hệ trong dashboard là tương quan quan sát trên một snapshot, không phải nhân quả. "
                    "Doanh thu = MonthlyRevenue hiện tại, không phải lợi nhuận/CLV.", className="footer"),
    ], className="main"),
], className="shell")


@app.callback(Output("nav", "children"), Input("url", "pathname"))
def render_nav(path):
    path = path if path in RENDERERS else "/"
    return [dcc.Link([html.Span(f"0{i}", className="nav-num"), name], href=href,
                     className="nav-item active" if href == path else "nav-item")
            for i, (href, name, _) in enumerate(PAGES, start=1)]


@app.callback(Output("page", "children"), Input("url", "pathname"), *[Input(f"f-{k}", "value") for k, _, _ in FILTERS])
def render_page(path, *values):
    path = path if path in RENDERERS else "/"
    df = apply_filters(values)
    if df.empty:
        return [header(path, df), html.Div([html.H2("Không có khách hàng cho bộ lọc này"),
                                            html.P("Hãy bỏ bớt điều kiện lọc.")], className="empty")]
    return [header(path, df), *RENDERERS[path](df)]


@app.callback(*[Output(f"f-{k}", "value") for k, _, _ in FILTERS], Input("reset", "n_clicks"), prevent_initial_call=True)
def reset_filters(_):
    return [None] * len(FILTERS)


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
