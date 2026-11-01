"""Bảng điều khiển Cell2Cell, đọc bộ kết quả do notebook 04 xuất ra."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from dash import Dash, Input, Output, dcc, html

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "viz"))
import charts as c  # noqa: E402

RESULTS_DIR = ROOT / "work" / "build" / "dashboard"
DATA_PATH = RESULTS_DIR / "customers.parquet"
if not DATA_PATH.is_file():
    raise SystemExit("Chưa có kết quả dashboard. Hãy chạy toàn bộ notebook work/viz/04_eda_truc_quan.ipynb.")
DATA = pd.read_parquet(DATA_PATH)
NOTEBOOK_FIGURES = {key: pio.read_json(RESULTS_DIR / "figures" / f"{key}.json")
                    for key in c.FIGURES if (RESULTS_DIR / "figures" / f"{key}.json").is_file()}
COMPANY = c.kpis(DATA)
HAS_RISK = "RiskDecile" in DATA
UPDATED_AT = datetime.fromtimestamp(DATA_PATH.stat().st_mtime).strftime("%d/%m/%Y %H:%M")

FILTERS = [
    ("tenure", "Thời gian sử dụng", "TenureBand"),
    ("usage", "Biến động phút gọi", "UsageTrendBand"),
    ("equipment", "Tuổi thiết bị", "EquipmentAgeBand"),
    ("credit", "Hạng tín dụng", "CreditRating"),
]
PAGES = [
    ("/", "Tổng quan"),
    ("/nguyen-nhan", "Thiết bị và mức sử dụng"),
    ("/rui-ro", "Hồ sơ và rủi ro"),
    ("/hanh-dong", "Phân khúc khách hàng"),
]
CHART_TITLES = {
    "C01_ty_le_churn": "Cơ cấu khách hàng",
    "C05_vong_doi": "Tỷ lệ rời bỏ theo tháng sử dụng",
    "C05b_so_khach": "Số khách rời bỏ và ở lại theo tháng sử dụng",
    "C06_tuoi_thiet_bi": "Tỷ lệ rời bỏ theo tuổi thiết bị",
    "C07_heatmap_tenure_thiet_bi": "Tỷ lệ rời bỏ theo thời gian sử dụng và tuổi thiết bị",
    "C09_dac_diem_thiet_bi": "Tỷ lệ rời bỏ theo đặc điểm thiết bị",
    "C10_bien_dong_phut_goi": "Tỷ lệ rời bỏ theo biến động phút gọi",
    "C11_bien_dong_doanh_thu": "Tỷ lệ rời bỏ theo biến động doanh thu",
    "C12_muc_su_dung": "Tỷ lệ rời bỏ theo mức sử dụng phút gọi",
    "C13_goi_gio_cao_diem": "Tỷ lệ rời bỏ theo số cuộc gọi giờ cao điểm",
    "C14_treemap_thoi_gian": "Số khách rời bỏ theo thời gian sử dụng",
    "C16_tin_dung": "Tỷ lệ rời bỏ theo hạng tín dụng",
    "C04c_phan_bo_phi_dinh_ky": "Phân bố phí định kỳ theo trạng thái rời bỏ",
    "C04d_churn_phi_dinh_ky": "Tỷ lệ rời bỏ theo mức phí định kỳ",
    "C19a_risk_decile": "Tỷ lệ rời bỏ theo nhóm rủi ro",
    "C19b_gain_curve": "Tỷ lệ khách rời bỏ được xác định theo phạm vi liên hệ",
    "C20_phan_khuc": "Tỷ lệ rời bỏ và doanh thu theo phân khúc",
}
missing_figures = set(CHART_TITLES) - NOTEBOOK_FIGURES.keys()
if missing_figures:
    raise SystemExit("Kết quả biểu đồ chưa đầy đủ. Hãy chạy toàn bộ notebook 04.")


def options(column):
    values = DATA[column]
    if isinstance(values.dtype, pd.CategoricalDtype):
        items = [value for value in values.cat.categories if value in set(values)]
    elif column == "CreditRating":
        items = [value for value in c.CREDIT_ORDER if value in set(values)]
    else:
        items = sorted(values.dropna().unique())
    return [{"label": c.display_value(column, value), "value": str(value)} for value in items]


def apply_filters(values):
    data = DATA
    for (_, _, column), selected in zip(FILTERS, values):
        if selected:
            data = data[data[column].astype(str).isin(selected)]
    return data


def kpi(label, value, delta=None, note=""):
    children = [html.Div(label, className="kpi-label"), html.Div(value, className="kpi-value")]
    if delta is not None:
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
        children.append(html.Div(
            f"{arrow} {c.fmt_ratio(abs(100 * delta))} điểm % so với toàn bộ khách",
            className="kpi-delta " + ("bad" if delta > 0 else "good"),
        ))
    if note:
        children.append(html.Div(note, className="kpi-note"))
    return html.Div(children, className="kpi")


def rate_kpi(label, data):
    if data.empty:
        return kpi(label, "—", note="0 khách")
    rate = c.baseline(data)
    return kpi(label, c.fmt_pct(rate), rate - COMPANY["rate"], note=f"{c.fmt_n(len(data))} khách")


def graph(key, data, wide=False):
    # Toàn bộ dữ liệu dùng nguyên biểu đồ đã xuất; lát cắt dùng bản dữ liệu của cùng lần chạy.
    figure = go.Figure(NOTEBOOK_FIGURES[key]) if len(data) == len(DATA) else c.FIGURES[key](data)
    figure.update_layout(title={"text": None}, margin={"l": 16, "r": 20, "t": 36, "b": 52})
    complex_chart = key == "C18_tuong_quan"
    return html.Section([
        html.H2(CHART_TITLES[key], className="chart-title"),
        html.Div(dcc.Graph(
            figure=figure,
            config={"displaylogo": False, "responsive": True, "displayModeBar": "hover",
                    "modeBarButtons": [["toImage"]], "toImageButtonOptions": {"scale": 2}},
            responsive=True,
        ), className="chart-scroll", tabIndex=0 if complex_chart else None,
            role="region", **{"aria-label": CHART_TITLES[key]}),
    ], className="panel" + (" wide" if wide else "") + (" complex-chart" if complex_chart else ""),
        **{"aria-label": CHART_TITLES[key]})


def header(path, data):
    name = dict(PAGES)[path]
    return html.Div([
        html.H1(name),
        html.Span(f"{c.fmt_n(len(data))} / {c.fmt_n(len(DATA))} khách", className="scope"),
    ], className="page-head")


def page_overview(data):
    values = c.kpis(data)
    revenue = data.MonthlyRevenue.sum()
    cards = html.Div([
        kpi("Tổng khách hàng", c.fmt_n(values["customers"])),
        kpi("Khách rời bỏ", c.fmt_n(values["churners"])),
        kpi("Tỷ lệ rời bỏ", c.fmt_pct(values["rate"]),
            values["rate"] - COMPANY["rate"] if len(data) != len(DATA) else None),
        kpi("Doanh thu tháng của nhóm rời bỏ", c.fmt_money(values["lost_revenue"]),
            note=f"{c.fmt_pct(values['lost_revenue'] / revenue)} doanh thu" if revenue else "—"),
        kpi("Thời gian sử dụng trung bình", f"{c.fmt_ratio(values['tenure_mean'])} tháng"),
    ], className="kpi-grid five")
    return [cards, html.Div([
        graph("C05_vong_doi", data, wide=True),
        graph("C05b_so_khach", data, wide=True),
        graph("C01_ty_le_churn", data),
        graph("C14_treemap_thoi_gian", data),
        graph("C13_goi_gio_cao_diem", data, wide=True),
    ], className="grid")]


def page_drivers(data):
    cards = html.Div([
        rate_kpi("Tỷ lệ rời bỏ · thiết bị trên 2 năm", data[data.EquipmentAgeBand == ">730 ngày"]),
        rate_kpi("Tỷ lệ rời bỏ · thiết bị không hỗ trợ web", data[data.HandsetWebCapable == "No"]),
        rate_kpi("Tỷ lệ rời bỏ · tháng sử dụng 11–12", data[data.MonthsInService.between(11, 12)]),
        rate_kpi("Tỷ lệ rời bỏ · phút gọi giảm", data[data.PercChangeMinutes < 0]),
    ], className="kpi-grid")
    keys = ["C06_tuoi_thiet_bi", "C07_heatmap_tenure_thiet_bi", "C09_dac_diem_thiet_bi",
            "C10_bien_dong_phut_goi", "C11_bien_dong_doanh_thu", "C12_muc_su_dung"]
    return [cards, html.Div([graph(key, data) for key in keys], className="grid")]


def page_risk(data):
    cards = [
        rate_kpi("Tỷ lệ rời bỏ · doanh thu giảm", data[data.PercChangeRevenues < 0]),
        rate_kpi("Tỷ lệ rời bỏ · tín dụng hạng 1–3", data[data.CreditRating.isin(c.CREDIT_ORDER[:3])]),
    ]
    if HAS_RISK:
        high = data[data.RiskDecile >= 8]
        cards.extend([
            kpi("Khách rủi ro nhóm 8–10", c.fmt_n(len(high)),
                note=f"{c.fmt_pct(len(high) / len(data))} khách đang chọn"),
            rate_kpi("Tỷ lệ rời bỏ · nhóm rủi ro 8–10", high),
        ])
    panels = [graph("C04d_churn_phi_dinh_ky", data, wide=True)]
    if HAS_RISK:
        panels.extend([graph("C19a_risk_decile", data), graph("C19b_gain_curve", data)])
    panels.extend([graph("C16_tin_dung", data, wide=True), graph("C04c_phan_bo_phi_dinh_ky", data, wide=True)])
    return [html.Div(cards, className="kpi-grid"), html.Div(panels, className="grid")]


def segment_table(summary):
    headings = ["Phân khúc", "Số khách", "Khách rời bỏ", "Tỷ lệ rời bỏ",
                "Doanh thu trung bình / tháng", "Doanh thu ước tính có rủi ro / tháng"]
    rows = []
    for row in summary.itertuples():
        rows.append(html.Tr([
            html.Th(str(row.ActionSegment), scope="row"),
            *[html.Td(value, className="numeric") for value in (
                c.fmt_n(row.n), c.fmt_n(row.churners), c.fmt_pct(row.rate),
                c.fmt_money(row.avg_revenue), c.fmt_money(row.revenue_at_risk),
            )],
        ]))
    return html.Section([
        html.H2("Số liệu theo phân khúc", className="chart-title"),
        html.Div(html.Table([
            html.Thead(html.Tr([html.Th(label, scope="col") for label in headings])),
            html.Tbody(rows),
        ], className="data-table"), className="table-scroll", tabIndex=0,
            role="region", **{"aria-label": "Số liệu theo phân khúc"}),
    ], className="panel wide")


def page_action(data):
    summary = c.segment_summary(data)
    selected = summary[summary.ActionSegment != "Ổn định"]
    count = selected.n.sum()
    rate = selected.churners.sum() / count if count else None
    cards = html.Div([
        kpi("Khách thuộc phân khúc ưu tiên", c.fmt_n(count),
            note=f"{c.fmt_pct(count / len(data))} khách đang chọn"),
        kpi("Doanh thu ước tính có rủi ro / tháng", c.fmt_money(selected.revenue_at_risk.sum())),
        kpi("Tỷ lệ rời bỏ · phân khúc ưu tiên", c.fmt_pct(rate) if rate is not None else "—",
            rate - COMPANY["rate"] if rate is not None else None),
    ], className="kpi-grid three")
    return [cards, html.Div([graph("C20_phan_khuc", data, wide=True), segment_table(summary)], className="grid")]


RENDERERS = {"/": page_overview, "/nguyen-nhan": page_drivers, "/rui-ro": page_risk, "/hanh-dong": page_action}
app = Dash(__name__, title="Cell2Cell · Phân tích khách hàng", assets_folder="assets_bi", suppress_callback_exceptions=True)
server = app.server
app.layout = html.Div([
    dcc.Location(id="url"),
    html.Aside([
        html.Div([html.Div("C2C", className="brand-mark"),
                  html.Div([html.Strong("Cell2Cell"), html.Span("Phân tích khách hàng")])], className="brand"),
        html.Nav(id="nav", className="nav", **{"aria-label": "Điều hướng"}),
        html.Div(f"{c.fmt_n(len(DATA))} khách hàng", className="side-note"),
    ], className="sidebar"),
    html.Main([
        html.Div([
            *[html.Label([
                html.Span(label, className="filter-label"),
                dcc.Dropdown(id=f"f-{key}", options=options(column), multi=True, placeholder="Tất cả"),
            ], className="filter") for key, label, column in FILTERS],
            html.Button("Xóa lọc", id="reset", className="reset", n_clicks=0),
        ], className="filters"),
        dcc.Loading(html.Div(id="page"), type="dot", color=c.ACCENT),
        html.Footer(f"Cập nhật: {UPDATED_AT}", className="footer"),
    ], className="main"),
], className="shell")


@app.callback(Output("nav", "children"), Input("url", "pathname"))
def render_nav(path):
    path = path if path in RENDERERS else "/"
    return [dcc.Link([html.Span(f"0{index}", className="nav-num"),
                      html.Span(name, **{"aria-current": "page" if href == path else "false"})], href=href,
                     className="nav-item active" if href == path else "nav-item")
            for index, (href, name) in enumerate(PAGES, start=1)]


@app.callback(Output("page", "children"), Input("url", "pathname"), *[Input(f"f-{key}", "value") for key, _, _ in FILTERS])
def render_page(path, *values):
    path = path if path in RENDERERS else "/"
    data = apply_filters(values)
    if data.empty:
        return [header(path, data), html.Div("Không có dữ liệu", className="empty")]
    return [header(path, data), *RENDERERS[path](data)]


@app.callback(*[Output(f"f-{key}", "value") for key, _, _ in FILTERS], Input("reset", "n_clicks"), prevent_initial_call=True)
def reset_filters(_):
    return [None] * len(FILTERS)


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
