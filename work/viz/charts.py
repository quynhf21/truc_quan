"""Hàm vẽ dùng chung cho notebook 04 và dashboard. Mỗi hàm nhận DataFrame đã lọc, trả về go.Figure.

Tiêu đề biểu đồ là action title sinh từ số liệu truyền vào, không hard-code con số.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CHURN = "#D64545"
STAY = "#8FA3B5"
ACCENT = "#1F6FB2"
NEUTRAL = "#C9D3DC"
INK = "#1D2B36"
MUTED = "#5B6B78"
GRID = "#EDF1F4"
FONT = "Inter, Segoe UI, Arial, sans-serif"

TARGET = "ChurnFlag"
MIN_N = 100  # nhóm nhỏ hơn ngưỡng này không đủ tin cậy để so sánh rate

CREDIT_ORDER = ["1-Highest", "2-High", "3-Good", "4-Medium", "5-Low", "6-VeryLow", "7-Lowest"]


# ---------- định dạng ----------

def fmt_n(value) -> str:
    return f"{int(round(value)):,}".replace(",", ".")


def fmt_pct(value, digits=1) -> str:
    return f"{100 * value:.{digits}f}%".replace(".", ",")


def fmt_money(value) -> str:
    if abs(value) >= 1e6:
        return f"${value / 1e6:.2f} triệu".replace(".", ",")
    if abs(value) >= 1e3:
        return f"${value / 1e3:.1f} nghìn".replace(".", ",")
    return f"${value:.1f}".replace(".", ",")


def fmt_ratio(value) -> str:
    return f"{value:.1f}".replace(".", ",")


def baseline(df: pd.DataFrame) -> float:
    return float(df[TARGET].mean()) if len(df) else float("nan")


# ---------- tổng hợp ----------

def rate_by(df: pd.DataFrame, col, order=None, min_n=0) -> pd.DataFrame:
    """Bảng [col, n, churners, rate]; rate = churner / n trong cùng nhóm."""
    table = (df.groupby(col, observed=True, dropna=False)[TARGET]
             .agg(n="size", churners="sum").reset_index())
    table["rate"] = table.churners / table.n
    table = table[table.n >= min_n]
    if order is not None:
        table[col] = pd.Categorical(table[col], categories=[o for o in order if o in set(table[col])], ordered=True)
        table = table.sort_values(col)
    return table.reset_index(drop=True)


def kpis(df: pd.DataFrame) -> dict:
    churned = df[df[TARGET] == 1]
    out = {
        "customers": len(df),
        "churners": int(df[TARGET].sum()),
        "rate": baseline(df),
        "lost_revenue": float(churned.MonthlyRevenue.sum()),
        "tenure_mean": float(df.MonthsInService.mean()) if len(df) else float("nan"),
    }
    if "RiskDecile" in df:
        high = df.RiskDecile >= 8
        out["high_risk_share"] = float(high.mean()) if len(df) else float("nan")
        out["high_risk_n"] = int(high.sum())
    return out


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    table = (df.groupby("ActionSegment", observed=True)
             .agg(n=(TARGET, "size"), churners=(TARGET, "sum"),
                  revenue=("MonthlyRevenue", "sum"), avg_revenue=("MonthlyRevenue", "mean"))
             .reset_index())
    table["rate"] = table.churners / table.n
    table["revenue_at_risk"] = table.revenue * table.rate
    return table


# ---------- style ----------

def apply_style(fig: go.Figure, title: str, subtitle: str = "", height=380) -> go.Figure:
    text = f"<b>{title}</b>" + (f"<br><span style='font-size:12px;color:{MUTED}'>{subtitle}</span>" if subtitle else "")
    fig.update_layout(
        title=dict(text=text, x=0.01, xanchor="left", y=0.98, yanchor="top", pad=dict(t=8), font=dict(size=15, color=INK)),
        template="plotly_white", height=height, separators=",.",
        font=dict(family=FONT, size=12, color=INK),
        margin=dict(l=10, r=20, t=92, b=40),
        paper_bgcolor="white", plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=1, xanchor="right", title=None),
        hoverlabel=dict(bgcolor="white", font=dict(family=FONT, color=INK)),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, automargin=True, title_font=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True, title_font=dict(color=MUTED))
    return fig


def add_baseline(fig: go.Figure, base: float, axis="y", **kwargs) -> go.Figure:
    line = dict(line_dash="dash", line_color=MUTED, line_width=1,
                annotation_text=f"Trung bình {fmt_pct(base)}", annotation_font_color=MUTED,
                annotation_font_size=11, **kwargs)
    if axis == "y":
        fig.add_hline(y=base, annotation_position="top left", **line)
    else:
        fig.add_vline(x=base, annotation_position="top", **line)
    return fig


def _hover(table: pd.DataFrame) -> np.ndarray:
    return np.stack([table.n.map(fmt_n), table.churners.map(fmt_n), table.rate.map(fmt_pct)], axis=-1)


HOVER = "<b>%{x}</b><br>Khách: %{customdata[0]}<br>Churn: %{customdata[1]}<br>Churn rate: %{customdata[2]}<extra></extra>"
HOVER_H = HOVER.replace("%{x}", "%{y}")


def empty_figure(message="Không có dữ liệu cho bộ lọc này") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(color=MUTED, size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return apply_style(fig, "")


# ---------- C01–C02: tổng quan ----------

def churn_donut(df: pd.DataFrame) -> go.Figure:
    k = kpis(df)
    fig = go.Figure(go.Pie(
        labels=["Rời bỏ", "Ở lại"], values=[k["churners"], k["customers"] - k["churners"]],
        hole=0.62, sort=False, marker=dict(colors=[CHURN, STAY]), textinfo="percent",
        hovertemplate="%{label}: %{value:,.0f} khách<extra></extra>"))
    fig.add_annotation(text=f"<b>{fmt_pct(k['rate'])}</b><br>churn", showarrow=False, font=dict(size=20, color=INK))
    one_in = 1 / k["rate"] if k["rate"] else float("nan")
    return apply_style(fig, f"Cứ khoảng {fmt_ratio(one_in)} khách thì có 1 khách rời bỏ",
                       f"{fmt_n(k['churners'])} / {fmt_n(k['customers'])} khách", height=340)


def missing_bar(df: pd.DataFrame, columns) -> go.Figure:
    share = df[columns].isna().mean().loc[lambda s: s.gt(0)].sort_values()
    if share.empty:
        return empty_figure("Không có giá trị thiếu trong lát cắt này")
    fig = go.Figure(go.Bar(x=share.values, y=share.index, orientation="h", marker_color=ACCENT,
                           text=[fmt_pct(v, 2) for v in share.values], textposition="outside",
                           hovertemplate="%{y}: %{x:.2%}<extra></extra>"))
    fig.update_xaxes(tickformat=".1%", title="% dòng bị thiếu", range=[0, share.max() * 1.25])
    return apply_style(fig, f"Dữ liệu thiếu rất ít: cao nhất là {share.index[-1]} ({fmt_pct(share.iloc[-1], 2)})",
                       f"{len(share)} / {len(columns)} cột có giá trị thiếu", height=max(300, 28 * len(share) + 120))


# ---------- C03–C04: phân bố ----------

def distribution_overlay(df: pd.DataFrame, col: str, label: str, clip=0.99) -> go.Figure:
    upper = df[col].quantile(clip)
    data = df[df[col].le(upper)]
    fig = go.Figure()
    for flag, name, color in [(0, "Ở lại", STAY), (1, "Rời bỏ", CHURN)]:
        fig.add_trace(go.Histogram(x=data.loc[data[TARGET] == flag, col], name=name, marker_color=color,
                                   opacity=0.6, histnorm="percent", nbinsx=40))
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title=label)
    fig.update_yaxes(title="% khách trong nhóm")
    med = df.groupby(TARGET)[col].median()
    direction = "thấp hơn" if med.get(1, 0) < med.get(0, 0) else "cao hơn"
    return apply_style(fig, f"Khách rời bỏ có {label.lower()} trung vị {direction} khách ở lại",
                       f"Trung vị: rời bỏ {fmt_ratio(med.get(1, np.nan))} · ở lại {fmt_ratio(med.get(0, np.nan))} "
                       f"· bỏ 1% giá trị lớn nhất cho dễ nhìn")


def box_by_churn(df: pd.DataFrame, cols: dict) -> go.Figure:
    fig = make_subplots(rows=1, cols=len(cols), subplot_titles=list(cols.values()))
    for i, col in enumerate(cols, start=1):
        for flag, name, color in [(0, "Ở lại", STAY), (1, "Rời bỏ", CHURN)]:
            fig.add_trace(go.Box(y=df.loc[df[TARGET] == flag, col], name=name, marker_color=color,
                                 boxpoints=False, showlegend=i == 1, legendgroup=name), row=1, col=i)
    med = df.groupby(TARGET).CurrentEquipmentDays.median() if "CurrentEquipmentDays" in cols else None
    title = ("Khách rời bỏ dùng máy cũ hơn rõ rệt" if med is not None and med.get(1, 0) > med.get(0, 0)
             else "So sánh phân bố giữa khách rời bỏ và ở lại")
    sub = (f"Trung vị tuổi máy: rời bỏ {fmt_n(med.get(1, 0))} ngày · ở lại {fmt_n(med.get(0, 0))} ngày"
           if med is not None else "")
    fig = apply_style(fig, title, sub, height=420)
    fig.update_annotations(font=dict(size=12, color=MUTED))
    return fig


# ---------- C05–C07: vòng đời và thiết bị ----------

def tenure_line(df: pd.DataFrame, max_month=48) -> go.Figure:
    table = rate_by(df[df.MonthsInService.le(max_month)], "MonthsInService", min_n=MIN_N)
    if table.empty:
        return empty_figure()
    base = baseline(df)
    peak = table.loc[table.rate.idxmax()]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.68, 0.32], vertical_spacing=0.06)
    fig.add_trace(go.Scatter(x=table.MonthsInService, y=table.rate, mode="lines+markers", name="Churn rate",
                             line=dict(color=CHURN, width=2.5), marker=dict(size=5), customdata=_hover(table),
                             hovertemplate=HOVER.replace("%{x}", "Tháng %{x}")), row=1, col=1)
    fig.add_trace(go.Bar(x=table.MonthsInService, y=table.n, name="Số khách", marker_color=NEUTRAL,
                         hovertemplate="Tháng %{x}: %{y:,.0f} khách<extra></extra>"), row=2, col=1)
    fig.add_hline(y=base, line_dash="dash", line_color=MUTED, line_width=1, row=1, col=1,
                  annotation_text=f"Trung bình {fmt_pct(base)}", annotation_position="bottom right",
                  annotation_font=dict(color=MUTED, size=11))
    fig.update_yaxes(tickformat=".0%", title="Churn rate", row=1, col=1, rangemode="tozero")
    fig.update_yaxes(title="Số khách", row=2, col=1)
    fig.update_xaxes(title="Số tháng sử dụng dịch vụ", row=2, col=1, dtick=6)
    fig = apply_style(fig, f"Churn vọt lên {fmt_pct(peak.rate)} ở tháng {int(peak.MonthsInService)}: thời điểm hết hợp đồng 1 năm",
                      f"Churn rate theo từng tháng (chỉ tháng có ≥{MIN_N} khách, tối đa {max_month} tháng)", height=460)
    fig.update_layout(showlegend=False)
    return fig


def rate_bar(df: pd.DataFrame, col: str, label: str, order=None, horizontal=False, title=None, min_n=MIN_N) -> go.Figure:
    """Bar churn rate theo nhóm, có baseline; nhóm trên trung bình tô đỏ."""
    table = rate_by(df, col, order=order, min_n=min_n)
    if table.empty:
        return empty_figure()
    if order is None:
        table = table.sort_values("rate", ascending=horizontal)
    base = baseline(df)
    colors = [CHURN if r > base else STAY for r in table.rate]
    labels = table[col].astype(str)
    text = [fmt_pct(r) for r in table.rate]
    if horizontal:
        bar = go.Bar(x=table.rate, y=labels, orientation="h", marker_color=colors, text=text,
                     textposition="outside", customdata=_hover(table), hovertemplate=HOVER_H)
    else:
        bar = go.Bar(x=labels, y=table.rate, marker_color=colors, text=text, textposition="outside",
                     customdata=_hover(table), hovertemplate=HOVER)
    fig = go.Figure(bar)
    hi, lo = table.loc[table.rate.idxmax()], table.loc[table.rate.idxmin()]
    if title is None:
        title = (f"{label} “{hi[col]}” churn {fmt_pct(hi.rate)}, gấp {fmt_ratio(hi.rate / lo.rate)} lần nhóm “{lo[col]}”"
                 if lo.rate > 0 else f"{label} “{hi[col]}” churn cao nhất ({fmt_pct(hi.rate)})")
    rate_axis = dict(tickformat=".0%", range=[0, table.rate.max() * 1.22], title="Churn rate")
    if horizontal:
        fig.update_xaxes(**rate_axis)
        fig.update_yaxes(title=None)
        add_baseline(fig, base, axis="x")
        height = max(340, 26 * len(table) + 130)
    else:
        fig.update_yaxes(**rate_axis)
        fig.update_xaxes(title=label, type="category")
        add_baseline(fig, base)
        height = 380
    return apply_style(fig, title, f"Đỏ = cao hơn trung bình · n = {fmt_n(table.n.sum())} khách", height=height)


def tenure_equipment_heatmap(df: pd.DataFrame) -> go.Figure:
    data = df[~df.EquipmentAgeBand.isin(["Bất thường", "Không rõ"])]
    table = (data.groupby(["TenureBand", "EquipmentAgeBand"], observed=True)[TARGET]
             .agg(n="size", rate="mean").reset_index())
    if table.empty:
        return empty_figure()
    table.loc[table.n < MIN_N, "rate"] = np.nan
    rate = table.pivot(index="TenureBand", columns="EquipmentAgeBand", values="rate")
    count = table.pivot(index="TenureBand", columns="EquipmentAgeBand", values="n").reindex_like(rate)
    text = [[fmt_pct(v) if pd.notna(v) else "" for v in row] for row in rate.values]
    hover = [[f"n = {fmt_n(c)}" if pd.notna(c) else "" for c in row] for row in count.values]
    fig = go.Figure(go.Heatmap(z=rate.values, x=rate.columns.astype(str), y=rate.index.astype(str),
                               colorscale="Reds", text=text, texttemplate="%{text}", customdata=hover,
                               hovertemplate="%{y} · máy %{x}<br>Churn rate: %{z:.1%}<br>%{customdata}<extra></extra>",
                               colorbar=dict(tickformat=".0%", title="Churn")))
    stacked = table.dropna(subset=["rate"])
    if stacked.empty:
        return empty_figure(f"Mọi ô đều có < {MIN_N} khách")
    hot = stacked.loc[stacked.rate.idxmax()]
    fig.update_xaxes(title="Tuổi thiết bị", side="bottom")
    fig.update_yaxes(title="Thời gian sử dụng", autorange="reversed")
    return apply_style(fig, f"Điểm nóng: {hot.TenureBand} + máy {hot.EquipmentAgeBand} churn {fmt_pct(hot.rate)}",
                       f"Ô trống: nhóm có < {MIN_N} khách", height=420)


# ---------- C08–C12: hành vi dịch vụ ----------

def retention_funnel(df: pd.DataFrame) -> go.Figure:
    stages = [
        ("Tất cả khách", df),
        ("Đã gọi retention team", df[df.MadeCallToRetentionTeam == "Yes"]),
        ("Đã nhận ưu đãi giữ chân", df[df.RetentionOfferAccepted == "Yes"]),
    ]
    names = [s for s, _ in stages]
    n = [len(d) for _, d in stages]
    rates = [baseline(d) if len(d) else 0 for _, d in stages]
    fig = make_subplots(rows=1, cols=2, column_widths=[0.55, 0.45], horizontal_spacing=0.18,
                        subplot_titles=["Số khách", "Churn rate"], specs=[[{"type": "funnel"}, {"type": "bar"}]])
    fig.add_trace(go.Funnel(y=names, x=n, marker=dict(color=[STAY, ACCENT, ACCENT]), textinfo="value",
                            texttemplate="%{value:,.0f}", hovertemplate="%{y}: %{x:,.0f} khách<extra></extra>"), 1, 1)
    fig.add_trace(go.Bar(y=names, x=rates, orientation="h", marker_color=[STAY, CHURN, CHURN],
                         text=[fmt_pct(r) for r in rates], textposition="outside",
                         hovertemplate="%{y}: %{x:.1%}<extra></extra>"), 1, 2)
    fig.update_yaxes(autorange="reversed", showticklabels=False, row=1, col=2)
    fig.update_xaxes(tickformat=".0%", range=[0, max(rates) * 1.3 if max(rates) else 1], row=1, col=2)
    fig = apply_style(fig, f"Nhận ưu đãi giữ chân rồi vẫn churn {fmt_pct(rates[2])}: chương trình hiện tại không giữ được khách",
                      f"So với trung bình {fmt_pct(rates[0])} · khách đã liên hệ retention là nhóm báo động", height=360)
    fig.update_layout(showlegend=False)
    fig.update_annotations(font=dict(size=12, color=MUTED))
    return fig


def device_grouped(df: pd.DataFrame) -> go.Figure:
    rows = []
    for col, label in [("HandsetWebCapable", "Máy hỗ trợ web"), ("HandsetRefurbished", "Máy tân trang")]:
        t = rate_by(df[df[col].isin(["Yes", "No"])], col)
        t["feature"] = label
        t["value"] = t[col].map({"Yes": "Có", "No": "Không"})
        rows.append(t)
    table = pd.concat(rows, ignore_index=True)
    if table.empty:
        return empty_figure()
    fig = go.Figure()
    for value, color in [("Có", STAY), ("Không", ACCENT)]:
        part = table[table.value == value]
        fig.add_trace(go.Bar(x=part.feature, y=part.rate, name=value, marker_color=color,
                             text=[fmt_pct(r) for r in part.rate], textposition="outside",
                             customdata=_hover(part), hovertemplate=HOVER.replace("%{x}", f"%{{x}}: {value}")))
    # Máy không web có churn cao hơn → tô đỏ để nhấn mạnh
    web_no = table[(table.feature == "Máy hỗ trợ web") & (table.value == "Không")]
    web_yes = table[(table.feature == "Máy hỗ trợ web") & (table.value == "Có")]
    add_baseline(fig, baseline(df))
    fig.update_layout(barmode="group")
    fig.update_yaxes(tickformat=".0%", range=[0, table.rate.max() * 1.25], title="Churn rate")
    title = "Đặc điểm thiết bị và churn"
    if len(web_no) and len(web_yes):
        title = (f"Máy không hỗ trợ web churn {fmt_pct(web_no.rate.iloc[0])} so với "
                 f"{fmt_pct(web_yes.rate.iloc[0])} ở máy có web")
    return apply_style(fig, title, "Máy tân trang (refurbished) cũng churn cao hơn máy mới")


def overage_bubble(df: pd.DataFrame) -> go.Figure:
    data = df[~df.MinutesBand.isin(["Không rõ"]) & ~df.OverageBand.isin(["Không rõ"])]
    table = (data.groupby(["MinutesBand", "OverageBand"], observed=True)[TARGET]
             .agg(n="size", churners="sum").reset_index())
    table = table[table.n >= MIN_N]
    if table.empty:
        return empty_figure()
    table["rate"] = table.churners / table.n
    palette = {"0": NEUTRAL, "≤50": STAY, "50–200": ACCENT, ">200": CHURN}
    fig = go.Figure()
    for band in [b for b in palette if b in set(table.OverageBand.astype(str))]:
        part = table[table.OverageBand.astype(str) == band]
        fig.add_trace(go.Scatter(
            x=part.MinutesBand.astype(str), y=part.rate, mode="markers", name=f"Vượt gói {band} phút",
            marker=dict(size=part.n, sizemode="area", sizeref=2 * table.n.max() / 60 ** 2, sizemin=6,
                        color=palette[band], line=dict(color="white", width=1)),
            customdata=_hover(part), hovertemplate=HOVER.replace("%{x}", f"%{{x}} · vượt {band}")))
    add_baseline(fig, baseline(df))
    fig.update_yaxes(tickformat=".0%", title="Churn rate", rangemode="tozero")
    fig.update_xaxes(title="Phút gọi / tháng", type="category",
                     categoryorder="array", categoryarray=["≤150 phút", "150–500 phút", ">500 phút"])
    over = rate_by(data, "OverageBand")
    top = over[over.OverageBand.astype(str) == ">200"]
    title = "Gói cước và churn: dùng ít và vượt gói nhiều đều rủi ro"
    if len(top):
        title = f"Vượt gói > 200 phút churn {fmt_pct(top.rate.iloc[0])}; dùng ít (≤150 phút) cũng rủi ro"
    return apply_style(fig, title, "Kích thước bong bóng = số khách", height=400)


# ---------- C13–C15: địa lý ----------

def region_table(df: pd.DataFrame, min_n=800) -> pd.DataFrame:
    return rate_by(df[df.Region != "Unknown"], "Region", min_n=min_n)


def region_bar(df: pd.DataFrame, min_n=800) -> go.Figure:
    table = region_table(df, min_n)
    if len(table) < 2:
        table = region_table(df, MIN_N)
    if table.empty:
        return empty_figure()
    hi, lo = table.loc[table.rate.idxmax()], table.loc[table.rate.idxmin()]
    gap = 100 * (hi.rate - lo.rate)
    return rate_bar(df[df.Region.isin(table.Region)], "Region", "Vùng", horizontal=True,
                    title=f"Vùng {hi.Region} churn {fmt_pct(hi.rate)}, cao hơn {lo.Region} {fmt_ratio(gap)} điểm %")


def region_treemap(df: pd.DataFrame, top=12) -> go.Figure:
    churned = df[df[TARGET] == 1]
    if churned.empty:
        return empty_figure()
    top_regions = churned.Region.value_counts().head(top).index
    data = df.assign(Region=df.Region.where(df.Region.isin(top_regions), "Vùng khác"))
    table = (data.groupby(["Region", "TenureBand"], observed=True)[TARGET]
             .agg(n="size", churners="sum").reset_index())
    table = table[table.churners > 0]
    table["rate"] = table.churners / table.n
    fig = px.treemap(table, path=[px.Constant("Tất cả"), "Region", "TenureBand"], values="churners",
                     color="rate", color_continuous_scale="Reds", custom_data=["n", "rate"])
    fig.update_traces(hovertemplate="<b>%{label}</b><br>Churner: %{value:,.0f}<extra></extra>",
                      texttemplate="%{label}<br>%{value:,.0f}", root_color="white")
    fig.update_coloraxes(colorbar=dict(tickformat=".0%", title="Churn"))
    lead = churned.Region.value_counts()
    lead = lead[lead.index != "Unknown"]
    share = lead.iloc[0] / len(churned) if len(lead) else 0
    return apply_style(fig, f"{lead.index[0]} mất nhiều khách nhất về số lượng ({fmt_pct(share)} tổng churner)",
                       f"Diện tích = số churner, màu = churn rate · top {top} vùng", height=460)


def region_pareto(df: pd.DataFrame) -> go.Figure:
    churned = df[(df[TARGET] == 1) & (df.Region != "Unknown")]
    if churned.empty:
        return empty_figure()
    counts = churned.Region.value_counts()
    cum = counts.cumsum() / counts.sum()
    k80 = int((cum < 0.8).sum() + 1)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=counts.index, y=counts.values, name="Số churner",
                         marker_color=[CHURN if i < k80 else NEUTRAL for i in range(len(counts))],
                         hovertemplate="%{x}: %{y:,.0f} churner<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=cum.index, y=cum.values, name="% tích lũy", mode="lines",
                             line=dict(color=INK, width=2), hovertemplate="%{x}: %{y:.0%}<extra></extra>"),
                  secondary_y=True)
    fig.add_hline(y=0.8, line_dash="dot", line_color=MUTED, secondary_y=True)
    fig.update_yaxes(title="Số churner", secondary_y=False)
    fig.update_yaxes(title="% tích lũy", tickformat=".0%", range=[0, 1.05], secondary_y=True, showgrid=False)
    fig.update_xaxes(type="category", tickangle=-45)
    return apply_style(fig, f"{k80}/{len(counts)} vùng chiếm 80% số khách rời bỏ",
                       "Pareto: đỏ = nhóm vùng tạo nên 80% churner", height=400)


# ---------- C16–C18: khách hàng ----------

def credit_bar(df: pd.DataFrame) -> go.Figure:
    table = rate_by(df, "CreditRating", order=CREDIT_ORDER, min_n=MIN_N)
    if table.empty:
        return empty_figure()
    good = baseline(df[df.CreditRating.isin(CREDIT_ORDER[:3])])
    low = baseline(df[df.CreditRating.isin(CREDIT_ORDER[3:])])
    return rate_bar(df, "CreditRating", "Hạng tín dụng", order=CREDIT_ORDER,
                    title=f"Khách tín dụng tốt (hạng 1–3) churn {fmt_pct(good)}, cao hơn nhóm 4–7 ({fmt_pct(low)})")


def demographic_multiples(df: pd.DataFrame) -> go.Figure:
    dims = [("IncomeGroup", "Nhóm thu nhập"), ("Occupation", "Nghề nghiệp"),
            ("PrizmCode", "Khu vực sống"), ("MaritalStatus", "Hôn nhân")]
    fig = make_subplots(rows=1, cols=4, shared_yaxes=True, subplot_titles=[d[1] for d in dims], horizontal_spacing=0.03)
    base = baseline(df)
    spreads = []
    for i, (col, _) in enumerate(dims, start=1):
        t = rate_by(df, col, min_n=MIN_N)
        if col == "IncomeGroup":
            t = t.sort_values(col, key=lambda s: pd.to_numeric(s, errors="coerce"))
        else:
            t = t.sort_values("rate", ascending=False)
        if len(t):
            spreads.append(t.rate.max() - t.rate.min())
        fig.add_trace(go.Bar(x=t[col].astype(str), y=t.rate, marker_color=[CHURN if r > base else STAY for r in t.rate],
                             customdata=_hover(t), hovertemplate=HOVER, showlegend=False), row=1, col=i)
        fig.add_hline(y=base, line_dash="dash", line_color=MUTED, line_width=1, row=1, col=i)
        fig.update_xaxes(type="category", tickangle=-45, row=1, col=i)
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_yaxes(title="Churn rate", row=1, col=1)
    spread = max(spreads) if spreads else 0
    fig = apply_style(fig, f"Nhân khẩu học chênh lệch nhỏ (tối đa {fmt_ratio(100 * spread)} điểm %): ưu tiên tín hiệu hành vi",
                      f"Cùng thang trục y · nhóm có ≥{MIN_N} khách · nét đứt = trung bình", height=420)
    fig.update_annotations(font=dict(size=12, color=MUTED))
    return fig


CORR_COLUMNS = [
    "ChurnFlag", "MonthsInService", "CurrentEquipmentDays", "MonthlyRevenue", "MonthlyMinutes",
    "TotalRecurringCharge", "OverageMinutes", "PercChangeMinutes", "DroppedBlockedCalls",
    "CustomerCareCalls", "ReceivedCalls", "PeakCallsInOut", "RetentionCalls", "HandsetModels", "AgeHH1",
]


def correlation_heatmap(df: pd.DataFrame, columns=CORR_COLUMNS) -> go.Figure:
    corr = df[columns].corr()
    labels = ["Churn" if c == TARGET else c for c in columns]
    fig = go.Figure(go.Heatmap(z=corr.values, x=labels, y=labels, zmin=-1, zmax=1, colorscale="RdBu_r",
                               text=corr.round(2).values, texttemplate="%{text}", textfont=dict(size=9),
                               hovertemplate="%{y} × %{x}: %{z:.2f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickangle=-45)
    with_target = corr[TARGET].drop(TARGET).dropna()
    if with_target.empty:
        return empty_figure("Lát cắt chỉ có một giá trị churn: không tính được tương quan")
    top = with_target.abs().idxmax()
    r = f"{with_target[top]:.2f}".replace(".", ",")
    return apply_style(fig, f"Không biến đơn lẻ nào tương quan mạnh với churn; cao nhất là {top} (r = {r})",
                       "Hệ số Pearson · các biến sử dụng (minutes, calls, revenue) tương quan mạnh với nhau", height=560)


# ---------- C19: mô hình rủi ro ----------

def decile_bar(df: pd.DataFrame) -> go.Figure:
    if "RiskDecile" not in df:
        return empty_figure("Chưa có điểm rủi ro: chạy work/pipeline/run_all.py")
    table = rate_by(df, "RiskDecile")
    table["RiskDecile"] = table.RiskDecile.astype(int)
    table = table.sort_values("RiskDecile")
    base = baseline(df)
    fig = go.Figure(go.Bar(x=table.RiskDecile.astype(str), y=table.rate,
                           marker_color=[CHURN if d >= 8 else STAY for d in table.RiskDecile],
                           text=[fmt_pct(r) for r in table.rate], textposition="outside",
                           customdata=_hover(table), hovertemplate=HOVER.replace("%{x}", "Decile %{x}")))
    add_baseline(fig, base)
    fig.update_xaxes(title="Nhóm rủi ro (1 = thấp nhất, 10 = cao nhất)", type="category")
    fig.update_yaxes(tickformat=".0%", range=[0, table.rate.max() * 1.2], title="Churn rate thực tế")
    top = table[table.RiskDecile == table.RiskDecile.max()]
    title = "Churn rate thực tế theo nhóm điểm rủi ro"
    if len(top) and base:
        title = f"Nhóm rủi ro cao nhất churn {fmt_pct(top.rate.iloc[0])}, gấp {fmt_ratio(top.rate.iloc[0] / base)} lần trung bình"
    return apply_style(fig, title, "Điểm rủi ro ngoài mẫu từ mô hình CatBoost (notebook 03) · đỏ = decile 8–10")


def gain_curve(df: pd.DataFrame) -> go.Figure:
    if "RiskScore" not in df or df[TARGET].sum() == 0:
        return empty_figure("Chưa có điểm rủi ro: chạy work/pipeline/run_all.py")
    ordered = df.sort_values("RiskScore", ascending=False)
    share = np.arange(1, len(ordered) + 1) / len(ordered)
    gain = ordered[TARGET].cumsum().to_numpy() / ordered[TARGET].sum()
    step = max(1, len(ordered) // 400)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=share[::step], y=gain[::step], name="Theo mô hình", line=dict(color=ACCENT, width=3),
                             hovertemplate="Liên hệ top %{x:.0%} → bắt được %{y:.0%} churner<extra></extra>"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], name="Chọn ngẫu nhiên", line=dict(color=MUTED, dash="dash")))
    i10 = int(0.1 * len(ordered)) - 1
    i20 = int(0.2 * len(ordered)) - 1
    for i in (i10, i20):
        fig.add_trace(go.Scatter(x=[share[i]], y=[gain[i]], mode="markers+text", showlegend=False,
                                 marker=dict(color=CHURN, size=9), text=[fmt_pct(gain[i], 0)],
                                 textposition="top left", hoverinfo="skip"))
    fig.update_xaxes(tickformat=".0%", title="% khách được liên hệ (xếp theo rủi ro)")
    fig.update_yaxes(tickformat=".0%", title="% churner bắt được")
    return apply_style(fig, f"Liên hệ 20% khách rủi ro nhất bắt được {fmt_pct(gain[i20], 0)} số khách sẽ rời bỏ",
                       f"Top 10%: {fmt_pct(gain[i10], 0)} churner (lift {fmt_ratio(gain[i10] / 0.1)}×)", height=400)


# ---------- C20: phân khúc hành động ----------

def segment_bubble(df: pd.DataFrame) -> go.Figure:
    table = segment_summary(df)
    if table.empty:
        return empty_figure()
    base = baseline(df)
    colors = [NEUTRAL if s == "Ổn định" else (CHURN if r > base else STAY) for s, r in zip(table.ActionSegment, table.rate)]
    fig = go.Figure(go.Scatter(
        x=table.rate, y=table.avg_revenue, mode="markers+text", text=table.ActionSegment.astype(str),
        textposition="top center",
        marker=dict(size=table.n, sizemode="area", sizeref=2 * table.n.max() / 70 ** 2, sizemin=10,
                    color=colors, line=dict(color="white", width=1.5)),
        customdata=np.stack([table.n.map(fmt_n), table.rate.map(fmt_pct), table.revenue_at_risk.map(fmt_money)], -1),
        hovertemplate="<b>%{text}</b><br>Khách: %{customdata[0]}<br>Churn rate: %{customdata[1]}"
                      "<br>Doanh thu/tháng bị đe dọa: %{customdata[2]}<extra></extra>"))
    add_baseline(fig, base, axis="x")
    fig.add_hline(y=df.MonthlyRevenue.mean(), line_dash="dot", line_color=NEUTRAL)
    fig.update_xaxes(tickformat=".0%", title="Churn rate", range=[0, table.rate.max() * 1.25])
    fig.update_yaxes(title="Doanh thu TB / khách / tháng ($)", range=[table.avg_revenue.min() * 0.85, table.avg_revenue.max() * 1.15])
    act = table[table.ActionSegment != "Ổn định"]
    title = "Phân khúc ưu tiên giữ chân"
    if len(act):
        top = act.loc[act.revenue_at_risk.idxmax()]
        title = f"“{top.ActionSegment}” có doanh thu bị đe dọa lớn nhất: {fmt_money(top.revenue_at_risk)}/tháng"
    return apply_style(fig, title, "Bong bóng = số khách · phải đường đứt = churn trên trung bình", height=440)


# ---------- danh mục C01–C20 (tên file PNG, hàm dựng) ----------

def _cats(df, col):
    return list(df[col].cat.categories) if hasattr(df[col], "cat") else None


FIGURES = {
    "C01_ty_le_churn": churn_donut,
    "C02_du_lieu_thieu": lambda df: missing_bar(df, CORR_COLUMNS[1:]),
    "C03_phan_bo_tuoi_may": lambda df: distribution_overlay(df, "CurrentEquipmentDays", "Tuổi thiết bị"),
    "C04_box_plot": lambda df: box_by_churn(df, {"CurrentEquipmentDays": "Tuổi thiết bị (ngày)",
                                                "MonthlyRevenue": "Doanh thu/tháng ($)",
                                                "OverageMinutes": "Phút vượt gói"}),
    "C05_vong_doi": tenure_line,
    "C06_tuoi_thiet_bi": lambda df: rate_bar(df, "EquipmentAgeBand", "Máy", order=_cats(df, "EquipmentAgeBand")),
    "C07_heatmap_tenure_thiet_bi": tenure_equipment_heatmap,
    "C08_retention_funnel": retention_funnel,
    "C09_dac_diem_thiet_bi": device_grouped,
    "C10_goi_cskh": lambda df: rate_bar(df, "CareCallsBand", "Số cuộc gọi CSKH", order=_cats(df, "CareCallsBand")),
    "C11_cuoc_goi_rot": lambda df: rate_bar(df, "DroppedBand", "Số cuộc gọi rớt", order=_cats(df, "DroppedBand")),
    "C12_goi_cuoc": overage_bubble,
    "C13_vung": region_bar,
    "C14_treemap_vung": region_treemap,
    "C15_pareto_vung": region_pareto,
    "C16_tin_dung": credit_bar,
    "C17_nhan_khau_hoc": demographic_multiples,
    "C18_tuong_quan": correlation_heatmap,
    "C19a_risk_decile": decile_bar,
    "C19b_gain_curve": gain_curve,
    "C20_phan_khuc": segment_bubble,
}
