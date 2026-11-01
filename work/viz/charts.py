"""Hàm vẽ dùng chung cho notebook 04 và dashboard. Mỗi hàm nhận DataFrame đã lọc, trả về go.Figure.

Tiêu đề biểu đồ là action title sinh từ số liệu truyền vào, không hard-code con số.
"""

from __future__ import annotations

from textwrap import wrap

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

FIELD_LABELS = {
    "CustomerID": "Mã khách hàng", "Churn": "Trạng thái rời bỏ", "ChurnFlag": "Rời bỏ",
    "MonthlyRevenue": "Doanh thu tháng", "MonthlyMinutes": "Phút gọi mỗi tháng",
    "TotalRecurringCharge": "Phí định kỳ", "DirectorAssistedCalls": "Cuộc gọi qua tổng đài hỗ trợ",
    "OverageMinutes": "Phút vượt gói", "RoamingCalls": "Cuộc gọi chuyển vùng",
    "PercChangeMinutes": "Thay đổi phút gọi", "PercChangeRevenues": "Thay đổi doanh thu",
    "DroppedCalls": "Cuộc gọi bị rớt", "BlockedCalls": "Cuộc gọi bị chặn",
    "UnansweredCalls": "Cuộc gọi không trả lời", "CustomerCareCalls": "Cuộc gọi chăm sóc khách hàng",
    "ThreewayCalls": "Cuộc gọi ba bên", "ReceivedCalls": "Cuộc gọi nhận được",
    "OutboundCalls": "Cuộc gọi đi", "InboundCalls": "Cuộc gọi đến",
    "PeakCallsInOut": "Cuộc gọi giờ cao điểm", "OffPeakCallsInOut": "Cuộc gọi ngoài giờ cao điểm",
    "DroppedBlockedCalls": "Cuộc gọi rớt hoặc bị chặn", "CallForwardingCalls": "Cuộc gọi chuyển tiếp",
    "CallWaitingCalls": "Cuộc gọi chờ", "MonthsInService": "Tháng sử dụng dịch vụ",
    "UniqueSubs": "Số thuê bao đã đăng ký", "ActiveSubs": "Số thuê bao hoạt động",
    "ServiceArea": "Mã vùng phục vụ", "Handsets": "Số thiết bị", "HandsetModels": "Số mẫu thiết bị",
    "CurrentEquipmentDays": "Tuổi thiết bị", "AgeHH1": "Tuổi thành viên thứ nhất",
    "AgeHH2": "Tuổi thành viên thứ hai", "ChildrenInHH": "Có trẻ em trong hộ",
    "HandsetRefurbished": "Thiết bị tân trang", "HandsetWebCapable": "Thiết bị hỗ trợ mạng",
    "TruckOwner": "Sở hữu xe tải", "RVOwner": "Sở hữu xe du lịch lưu động",
    "Homeownership": "Tình trạng sở hữu nhà", "BuysViaMailOrder": "Mua hàng qua thư",
    "RespondsToMailOffers": "Phản hồi ưu đãi qua thư", "OptOutMailings": "Từ chối nhận thư",
    "NonUSTravel": "Du lịch ngoài Hoa Kỳ", "OwnsComputer": "Sở hữu máy tính",
    "HasCreditCard": "Có thẻ tín dụng", "RetentionCalls": "Cuộc gọi giữ chân",
    "RetentionOffersAccepted": "Số ưu đãi giữ chân được nhận", "NewCellphoneUser": "Người mới dùng điện thoại",
    "NotNewCellphoneUser": "Người đã dùng điện thoại", "ReferralsMadeBySubscriber": "Số lượt giới thiệu",
    "IncomeGroup": "Nhóm thu nhập", "OwnsMotorcycle": "Sở hữu xe máy",
    "AdjustmentsToCreditRating": "Điều chỉnh hạng tín dụng", "HandsetPrice": "Giá thiết bị",
    "MadeCallToRetentionTeam": "Đã gọi bộ phận giữ chân", "CreditRating": "Hạng tín dụng",
    "PrizmCode": "Khu vực sinh sống", "Occupation": "Nghề nghiệp", "MaritalStatus": "Đã kết hôn",
    "Region": "Vùng", "RetentionOfferAccepted": "Đã nhận ưu đãi giữ chân",
    "TenureBand": "Nhóm thời gian sử dụng", "EquipmentAgeBand": "Nhóm tuổi thiết bị",
    "CareCallsBand": "Nhóm cuộc gọi chăm sóc", "DroppedBand": "Nhóm cuộc gọi rớt",
    "OverageBand": "Nhóm phút vượt gói", "MinutesBand": "Nhóm phút gọi",
    "ActionSegment": "Phân khúc hành động", "RiskScore": "Điểm rủi ro", "RiskDecile": "Nhóm rủi ro",
    "n": "Số khách", "churners": "Khách rời bỏ", "rate": "Tỷ lệ rời bỏ",
    "revenue": "Tổng doanh thu tháng", "avg_revenue": "Doanh thu tháng trung bình",
    "revenue_at_risk": "Doanh thu tháng bị đe dọa",
}
VALUE_LABELS = {
    "CreditRating": dict(zip(CREDIT_ORDER, ["1-Cao nhất", "2-Cao", "3-Tốt", "4-Trung bình",
                                          "5-Thấp", "6-Rất thấp", "7-Thấp nhất"])),
    "Occupation": {"Clerical": "Văn phòng", "Crafts": "Thủ công", "Homemaker": "Nội trợ",
                   "Other": "Khác", "Professional": "Chuyên môn", "Retired": "Nghỉ hưu",
                   "Self": "Tự kinh doanh", "Student": "Sinh viên"},
    "PrizmCode": {"Other": "Khác", "Rural": "Nông thôn", "Suburban": "Ngoại ô", "Town": "Thị trấn"},
    "Churn": {"Yes": "Rời bỏ", "No": "Ở lại"},
    "Homeownership": {"Known": "Đã xác định"},
}
SUMMARY_LABELS = {"count": "Số giá trị", "mean": "Trung bình", "std": "Độ lệch chuẩn",
                  "min": "Nhỏ nhất", "max": "Lớn nhất", "50%": "Trung vị",
                  "unique": "Số giá trị khác nhau", "top": "Phổ biến nhất", "freq": "Tần suất"}


def field_label(column) -> str:
    return FIELD_LABELS.get(column, str(column))


def display_value(column, value) -> str:
    if pd.isna(value):
        return "Không rõ"
    value = str(value)
    return VALUE_LABELS.get(column, {}).get(value, {"Yes": "Có", "No": "Không", "Unknown": "Không rõ"}.get(value, value))


def display_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Việt hóa bảng trình bày trên bản sao, giữ nguyên bảng dùng để tính toán."""
    result = frame.copy()
    for column in result:
        if pd.api.types.is_object_dtype(result[column]) or isinstance(result[column].dtype, pd.CategoricalDtype):
            result[column] = result[column].astype(object).map(lambda value: display_value(column, value))
    labels = {**FIELD_LABELS, **SUMMARY_LABELS}
    return result.rename(columns=labels, index=labels)


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
    return polish_labels(fig)


def polish_labels(fig: go.Figure) -> go.Figure:
    """Tách nhãn khỏi đường tham chiếu; không đổi dữ liệu hoặc thang trục."""
    for shape in fig.layout.shapes:
        shape.layer = "above"
    for annotation in fig.layout.annotations:
        if "Trung bình " in str(annotation.text) and annotation.yref != "paper":
            annotation.update(
                text=f"Nét đứt · {annotation.text}", x=0, y=1.02, xref="paper", yref="paper",
                xanchor="left", yanchor="bottom", showarrow=False, bgcolor="white", borderpad=3,
            )

    for trace in fig.data:
        text = getattr(trace, "text", None)
        if trace.type == "funnel":
            values = np.asarray(trace.x, dtype=float)
            cutoff = max(values) * 0.2 if len(values) else 0
            trace.update(textposition=["inside" if value > cutoff else "outside" for value in values],
                         textfont=dict(color=INK, size=12))
        elif trace.type == "bar" and text is not None:
            trace.update(textfont=dict(color=INK, size=13), cliponaxis=False)
            horizontal = trace.orientation == "h"
            axis_ref = (trace.xaxis or "x") if horizontal else (trace.yaxis or "y")
            references = [shape.x0 if horizontal else shape.y0 for shape in fig.layout.shapes
                          if (shape.xref if horizontal else shape.yref) == axis_ref
                          and (shape.x0 == shape.x1 if horizontal else shape.y0 == shape.y1)]
            if any("%" in str(value) for value in text) and (not horizontal or references):
                values = np.asarray(trace.x if horizontal else trace.y, dtype=float)
                cutoff = max(float(np.nanmax(values)) * 0.18, 0) if len(values) else 0
                colors = trace.marker.color
                colors = [colors] * len(values) if isinstance(colors, str) else list(colors) if colors is not None else []
                axis = fig.layout[axis_ref[0] + "axis" + axis_ref[1:]]
                span = abs(axis.range[1] - axis.range[0]) if axis.range else max(float(np.nanmax(values)), 0.01)
                near_label = any(abs(value / 2 - reference) < 0.04 * span
                                 for value in values if value > cutoff for reference in references)
                trace.update(
                    textposition=["inside" if value > cutoff else "outside" for value in values],
                    insidetextanchor="start" if near_label else "middle", textangle=0, constraintext="inside",
                    insidetextfont=dict(color=["white" if color in (CHURN, ACCENT) else INK for color in colors]),
                    outsidetextfont=dict(color=INK, size=13),
                )
        elif trace.type == "scatter" and text is not None and "text" in (trace.mode or ""):
            positions = trace.textposition or "top center"
            positions = [positions] * len(text) if isinstance(positions, str) else positions
            bubble = trace.marker.sizemode == "area"
            for i, (x, y, label, position) in enumerate(zip(trace.x, trace.y, text, positions)):
                if label is None or str(label) == "":
                    continue
                right, left = "right" in position, "left" in position
                above, below = "top" in position, "bottom" in position
                xshift = 12 if right else (-8 if left else 0)
                yshift = 12 if above else (-12 if below else 0)
                if bubble:
                    radius = np.sqrt(float(trace.marker.size[i]) / (2 * trace.marker.sizeref))
                    axis = fig.layout["yaxis" + (trace.yaxis or "y")[1:]]
                    low, high = axis.range if axis.range else (min(trace.y), max(trace.y))
                    fraction = (y - low) / (high - low) if high > low else 0.5
                    xaxis = fig.layout["xaxis" + (trace.xaxis or "x")[1:]]
                    xlow, xhigh = xaxis.range if xaxis.range else (min(trace.x), max(trace.x))
                    nearby_above = any(
                        other_y > y and abs(other_x - x) < 0.12 * (xhigh - xlow)
                        and other_y - y < 0.18 * (high - low)
                        for other_x, other_y in zip(trace.x, trace.y)
                    )
                    above = fraction < 0.2 or (fraction < 0.8 and not nearby_above)
                    below = not above
                    yshift = (radius + 16) * (1 if above else -1)
                fig.add_annotation(
                    x=x, y=y, xref=trace.xaxis or "x", yref=trace.yaxis or "y", text=str(label),
                    showarrow=False, xshift=xshift, yshift=yshift,
                    xanchor="left" if right else ("right" if left else "center"),
                    yanchor="bottom" if above else ("top" if below else "middle"),
                    bgcolor="white", borderpad=3, font=dict(color=INK, size=12),
                )
            trace.mode = "+".join(part for part in trace.mode.split("+") if part != "text") or "markers"
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


HOVER = "<b>%{x}</b><br>Số khách: %{customdata[0]}<br>Khách rời bỏ: %{customdata[1]}<br>Tỷ lệ rời bỏ: %{customdata[2]}<extra></extra>"
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
    fig.add_annotation(text=f"<b>{fmt_pct(k['rate'])}</b><br>rời bỏ", showarrow=False, font=dict(size=20, color=INK))
    one_in = 1 / k["rate"] if k["rate"] else float("nan")
    return apply_style(fig, f"Cứ khoảng {fmt_ratio(one_in)} khách thì có 1 khách rời bỏ",
                       f"{fmt_n(k['churners'])} / {fmt_n(k['customers'])} khách", height=460)


def missing_bar(df: pd.DataFrame, columns) -> go.Figure:
    share = df[columns].isna().mean().loc[lambda s: s.gt(0)].sort_values()
    if share.empty:
        return empty_figure("Không có giá trị thiếu trong lát cắt này")
    fig = go.Figure(go.Bar(x=share.values, y=[field_label(c) for c in share.index], orientation="h", marker_color=ACCENT,
                           text=[fmt_pct(v, 2) for v in share.values], textposition="outside",
                           hovertemplate="%{y}: %{x:.2%}<extra></extra>"))
    fig.update_xaxes(tickformat=".1%", title="% dòng bị thiếu", range=[0, share.max() * 1.25])
    return apply_style(fig, f"Dữ liệu thiếu rất ít: cao nhất là {field_label(share.index[-1]).lower()} ({fmt_pct(share.iloc[-1], 2)})",
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
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=table.MonthsInService, y=table.rate, mode="lines+markers", name="Tỷ lệ rời bỏ",
                             line=dict(color=CHURN, width=2.5), marker=dict(size=5), customdata=_hover(table),
                             hovertemplate=HOVER.replace("%{x}", "Tháng %{x}")))
    fig.add_hline(y=base, line_dash="dash", line_color=MUTED, line_width=1,
                  annotation_text=f"Trung bình {fmt_pct(base)}", annotation_position="bottom right",
                  annotation_font=dict(color=MUTED, size=11))
    fig.update_yaxes(tickformat=".0%", title="Tỷ lệ rời bỏ", rangemode="tozero")
    fig.update_xaxes(title="Số tháng sử dụng dịch vụ", dtick=6)
    fig = apply_style(fig, f"Tỷ lệ rời bỏ vọt lên {fmt_pct(peak.rate)} ở tháng {int(peak.MonthsInService)}: thời điểm hết hợp đồng 1 năm",
                      f"Tỷ lệ rời bỏ theo từng tháng (chỉ tháng có ≥{MIN_N} khách, tối đa {max_month} tháng)", height=460)
    fig.update_layout(showlegend=False)
    return fig


def tenure_stacked(df: pd.DataFrame) -> go.Figure:
    table = rate_by(df.dropna(subset=["MonthsInService"]), "MonthsInService").sort_values("MonthsInService")
    if table.empty:
        return empty_figure()
    peak = table.loc[table.churners.idxmax()]
    fig = go.Figure()
    for name, counts, color in [
        ("Rời bỏ", table.churners, CHURN),
        ("Ở lại", table.n - table.churners, STAY),
    ]:
        fig.add_trace(go.Bar(
            x=table.MonthsInService, y=counts, name=name, marker_color=color,
            customdata=_hover(table),
            hovertemplate="<b>Tháng %{x}</b><br>%{fullData.name}: %{y:,.0f} khách"
                          "<br>Tổng khách: %{customdata[0]}<br>Tỷ lệ rời bỏ: %{customdata[2]}<extra></extra>",
        ))
    fig.update_layout(barmode="stack", bargap=0.16)
    fig.update_xaxes(title="Thời gian sử dụng dịch vụ (tháng)", dtick=6, rangemode="tozero")
    fig.update_yaxes(title="Số khách hàng", rangemode="tozero", separatethousands=True)
    return apply_style(fig, f"Tháng {int(peak.MonthsInService)} có nhiều khách rời bỏ nhất: {fmt_n(peak.churners)} khách",
                       f"Mỗi cột là một tháng · {fmt_n(table.n.sum())} khách · toàn bộ thời gian sử dụng", height=460)


def rate_bar(df: pd.DataFrame, col: str, label: str, order=None, horizontal=False, title=None, min_n=MIN_N,
             base=None) -> go.Figure:
    """Bar tỷ lệ rời bỏ theo nhóm, có baseline; nhóm trên trung bình tô đỏ."""
    table = rate_by(df, col, order=order, min_n=min_n)
    if table.empty:
        return empty_figure()
    if order is None:
        table = table.sort_values("rate", ascending=horizontal)
    base = baseline(df) if base is None else base
    colors = [CHURN if r > base else STAY for r in table.rate]
    labels = table[col].astype(str).map(lambda value: display_value(col, value))
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
        title = (f"{label} “{display_value(col, hi[col])}” có tỷ lệ rời bỏ {fmt_pct(hi.rate)}, gấp {fmt_ratio(hi.rate / lo.rate)} lần nhóm “{display_value(col, lo[col])}”"
                 if lo.rate > 0 else f"{label} “{display_value(col, hi[col])}” có tỷ lệ rời bỏ cao nhất ({fmt_pct(hi.rate)})")
    rate_axis = dict(tickformat=".0%", range=[0, table.rate.max() * 1.22], title="Tỷ lệ rời bỏ")
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
                               hovertemplate="%{y} · máy %{x}<br>Tỷ lệ rời bỏ: %{z:.1%}<br>%{customdata}<extra></extra>",
                               colorbar=dict(tickformat=".0%", title="Tỷ lệ rời bỏ")))
    stacked = table.dropna(subset=["rate"])
    if stacked.empty:
        return empty_figure(f"Mọi ô đều có < {MIN_N} khách")
    hot = stacked.loc[stacked.rate.idxmax()]
    fig.update_xaxes(title="Tuổi thiết bị", side="bottom")
    fig.update_yaxes(title="Thời gian sử dụng", autorange="reversed")
    return apply_style(fig, f"Điểm nóng: {hot.TenureBand} + máy {hot.EquipmentAgeBand} có tỷ lệ rời bỏ {fmt_pct(hot.rate)}",
                       f"Ô trống: nhóm có < {MIN_N} khách", height=420)


# ---------- C08–C12: hành vi dịch vụ ----------

def retention_funnel(df: pd.DataFrame) -> go.Figure:
    stages = [
        ("Tất cả khách", df),
        ("Đã gọi bộ phận giữ chân", df[df.MadeCallToRetentionTeam == "Yes"]),
        ("Đã nhận ưu đãi giữ chân", df[df.RetentionOfferAccepted == "Yes"]),
    ]
    names = [s for s, _ in stages]
    n = [len(d) for _, d in stages]
    rates = [baseline(d) if len(d) else 0 for _, d in stages]
    fig = make_subplots(rows=1, cols=2, column_widths=[0.55, 0.45], horizontal_spacing=0.18,
                        subplot_titles=["Số khách", "Tỷ lệ rời bỏ"], specs=[[{"type": "funnel"}, {"type": "bar"}]])
    fig.add_trace(go.Funnel(y=names, x=n, marker=dict(color=[STAY, ACCENT, ACCENT]), textinfo="value",
                            texttemplate="%{value:,.0f}", hovertemplate="%{y}: %{x:,.0f} khách<extra></extra>"), 1, 1)
    fig.add_trace(go.Bar(y=names, x=rates, orientation="h", marker_color=[STAY, CHURN, CHURN],
                         text=[fmt_pct(r) for r in rates], textposition="outside",
                         hovertemplate="%{y}: %{x:.1%}<extra></extra>"), 1, 2)
    fig.update_yaxes(autorange="reversed", showticklabels=False, row=1, col=2)
    fig.update_xaxes(tickformat=".0%", range=[0, max(rates) * 1.3 if max(rates) else 1], row=1, col=2)
    fig = apply_style(fig, f"Nhận ưu đãi giữ chân rồi vẫn có tỷ lệ rời bỏ {fmt_pct(rates[2])}: chương trình hiện tại không giữ được khách",
                      f"So với trung bình {fmt_pct(rates[0])} · khách đã liên hệ bộ phận giữ chân là nhóm báo động", height=360)
    fig.update_layout(showlegend=False)
    fig.update_annotations(font=dict(size=12, color=MUTED))
    return fig


def device_grouped(df: pd.DataFrame) -> go.Figure:
    rows = []
    for col, label in [("HandsetWebCapable", "Máy hỗ trợ mạng"), ("HandsetRefurbished", "Máy tân trang")]:
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
    # Máy không hỗ trợ mạng có tỷ lệ rời bỏ cao hơn → tô đỏ để nhấn mạnh
    web_no = table[(table.feature == "Máy hỗ trợ mạng") & (table.value == "Không")]
    web_yes = table[(table.feature == "Máy hỗ trợ mạng") & (table.value == "Có")]
    add_baseline(fig, baseline(df))
    fig.update_layout(barmode="group")
    fig.update_yaxes(tickformat=".0%", range=[0, table.rate.max() * 1.25], title="Tỷ lệ rời bỏ")
    title = "Đặc điểm thiết bị và tỷ lệ rời bỏ"
    if len(web_no) and len(web_yes):
        title = (f"Máy không hỗ trợ mạng có tỷ lệ rời bỏ {fmt_pct(web_no.rate.iloc[0])} so với "
                 f"{fmt_pct(web_yes.rate.iloc[0])} ở máy có mạng")
    return apply_style(fig, title, "Máy tân trang cũng có tỷ lệ rời bỏ cao hơn máy mới")


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
            x=part.MinutesBand.astype(str), y=part.rate, mode="markers", name=band,
            marker=dict(size=part.n, sizemode="area", sizeref=2 * table.n.max() / 60 ** 2, sizemin=6,
                        color=palette[band], line=dict(color="white", width=1)),
            customdata=_hover(part), hovertemplate=HOVER.replace("%{x}", f"%{{x}} · vượt {band}")))
    add_baseline(fig, baseline(df))
    fig.update_yaxes(tickformat=".0%", title="Tỷ lệ rời bỏ", rangemode="tozero")
    fig.update_xaxes(title="Phút gọi / tháng", type="category",
                     categoryorder="array", categoryarray=["≤150 phút", "150–500 phút", ">500 phút"])
    over = rate_by(data, "OverageBand")
    top = over[over.OverageBand.astype(str) == ">200"]
    title = "Gói cước và tỷ lệ rời bỏ: dùng ít và vượt gói nhiều đều rủi ro"
    if len(top):
        title = f"Vượt gói > 200 phút có tỷ lệ rời bỏ {fmt_pct(top.rate.iloc[0])}; dùng ít (≤150 phút) cũng rủi ro"
    fig = apply_style(fig, title.replace("; ", "<br>"), "Kích thước bong bóng = số khách", height=500)
    fig.update_layout(
        margin=dict(t=115, b=125),
        legend=dict(
            title=dict(text="Số phút vượt gói", side="top"), orientation="h",
            x=0.5, xanchor="center", y=-0.30, yanchor="top",
            font=dict(size=12), itemsizing="constant", bgcolor="white",
        ),
    )
    return fig


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
    return rate_bar(df[df.Region.isin(table.Region)], "Region", "Vùng", horizontal=True, base=baseline(df),
                    title=f"Vùng {hi.Region} có tỷ lệ rời bỏ {fmt_pct(hi.rate)}, cao hơn {lo.Region} {fmt_ratio(gap)} điểm %")


def region_treemap(df: pd.DataFrame, top=12) -> go.Figure:
    churned = df[df[TARGET] == 1]
    if churned.empty:
        return empty_figure()
    top_regions = churned.Region.value_counts().head(top).index
    data = df.assign(Region=df.Region.where(df.Region.isin(top_regions), "Vùng khác"))
    table = (data.groupby(["Region", "TenureBand"], observed=True)[TARGET]
             .agg(n="size", churners="sum").reset_index())
    regions = data.groupby("Region", observed=True)[TARGET].agg(n="size", churners="sum")
    nodes = [("Tất cả", "", "Tất cả", len(data), int(data[TARGET].sum()))]
    for region, row in regions.sort_values("churners", ascending=False).iterrows():
        if row.churners > 0:
            nodes.append((f"Tất cả/{region}", "Tất cả", str(region), int(row.n), int(row.churners)))
    for row in table.loc[table.churners > 0].itertuples():
        parent = f"Tất cả/{row.Region}"
        nodes.append((f"{parent}/{row.TenureBand}", parent, str(row.TenureBand), int(row.n), int(row.churners)))

    rates = [churners / n for _, _, _, n, churners in nodes]
    fig = go.Figure(go.Treemap(
        ids=[node[0] for node in nodes], parents=[node[1] for node in nodes],
        labels=[node[2] for node in nodes], values=[node[4] for node in nodes],
        branchvalues="total", maxdepth=2, root_color="white",
        marker=dict(colors=rates, coloraxis="coloraxis", line=dict(color="white", width=2)),
        tiling=dict(pad=6), pathbar=dict(visible=True, thickness=28),
        customdata=[[fmt_n(n), fmt_n(churners), fmt_pct(churners / n)]
                    for _, _, _, n, churners in nodes],
        texttemplate="<b>%{label}</b><br>%{customdata[1]}",
        textfont=dict(size=16), textposition="middle center",
        hovertemplate=("<b>%{label}</b><br>Số khách: %{customdata[0]}"
                       "<br>Khách rời bỏ: %{customdata[1]}<br>Tỷ lệ rời bỏ: %{customdata[2]}<extra></extra>"),
    ))
    fig.update_layout(uniformtext=dict(minsize=14, mode="hide"),
                      coloraxis=dict(colorscale="Reds", colorbar=dict(
                          tickformat=".0%", title="Tỷ lệ<br>rời bỏ", thickness=16, len=0.85)))
    lead = churned.Region.value_counts()
    lead = lead[lead.index != "Unknown"]
    share = lead.iloc[0] / len(churned) if len(lead) else 0
    title = (f"{lead.index[0]} mất nhiều khách nhất về số lượng ({fmt_pct(share)} tổng khách rời bỏ)"
             if len(lead) else "Khách rời bỏ chưa xác định vùng phục vụ")
    return apply_style(fig, title,
                       "Diện tích = số khách rời bỏ · Màu = tỷ lệ rời bỏ · Bấm vào vùng để xem thời gian sử dụng",
                       height=600)


def region_pareto(df: pd.DataFrame) -> go.Figure:
    churned = df[(df[TARGET] == 1) & (df.Region != "Unknown")]
    if churned.empty:
        return empty_figure()
    counts = churned.Region.value_counts()
    cum = counts.cumsum() / counts.sum()
    k80 = int((cum < 0.8).sum() + 1)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=counts.index, y=counts.values, name="Số khách rời bỏ",
                         marker_color=[CHURN if i < k80 else NEUTRAL for i in range(len(counts))],
                         hovertemplate="%{x}: %{y:,.0f} khách rời bỏ<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=cum.index, y=cum.values, name="% tích lũy", mode="lines",
                             line=dict(color=INK, width=2), hovertemplate="%{x}: %{y:.0%}<extra></extra>"),
                  secondary_y=True)
    fig.add_hline(y=0.8, line_dash="dot", line_color=MUTED, secondary_y=True)
    fig.update_yaxes(title="Số khách rời bỏ", secondary_y=False)
    fig.update_yaxes(title="% tích lũy", tickformat=".0%", range=[0, 1.05], secondary_y=True, showgrid=False)
    fig.update_xaxes(type="category", tickangle=-45)
    return apply_style(fig, f"{k80}/{len(counts)} vùng chiếm 80% số khách rời bỏ",
                       "Pareto: đỏ = nhóm vùng tạo nên 80% khách rời bỏ", height=400)


# ---------- C16–C18: khách hàng ----------

def credit_bar(df: pd.DataFrame) -> go.Figure:
    table = rate_by(df, "CreditRating", order=CREDIT_ORDER, min_n=MIN_N)
    if table.empty:
        return empty_figure()
    good = baseline(df[df.CreditRating.isin(CREDIT_ORDER[:3])])
    low = baseline(df[df.CreditRating.isin(CREDIT_ORDER[3:])])
    return rate_bar(df, "CreditRating", "Hạng tín dụng", order=CREDIT_ORDER,
                    title=f"Khách tín dụng tốt (hạng 1–3) có tỷ lệ rời bỏ {fmt_pct(good)}, cao hơn nhóm 4–7 ({fmt_pct(low)})")


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
        fig.add_trace(go.Bar(x=t[col].astype(str).map(lambda value: display_value(col, value)), y=t.rate, marker_color=[CHURN if r > base else STAY for r in t.rate],
                             customdata=_hover(t), hovertemplate=HOVER, showlegend=False), row=1, col=i)
        fig.add_hline(y=base, line_dash="dash", line_color=MUTED, line_width=1, row=1, col=i)
        fig.update_xaxes(type="category", tickangle=-45, row=1, col=i)
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_yaxes(title="Tỷ lệ rời bỏ", row=1, col=1)
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


C18_FEATURES = [
    "MonthsInService", "CurrentEquipmentDays", "HandsetWebCapable",
    "MonthlyRevenue", "TotalRecurringCharge", "CreditRating",
    "MonthlyMinutes", "PercChangeMinutes", "PercChangeRevenues", "PeakCallsInOut",
]
C18_COLUMNS = [TARGET, *C18_FEATURES]


def correlation_matrix(df: pd.DataFrame, columns=C18_COLUMNS) -> pd.DataFrame:
    """Chỉ mã hóa trên bản sao phục vụ C18, không thay đổi đầu vào mô hình."""
    data = df[columns].copy()
    if "HandsetWebCapable" in data:
        data["HandsetWebCapable"] = data.HandsetWebCapable.map({"Yes": 1, "No": 0, 1: 1, 0: 0})
    if "CreditRating" in data:
        rating = data.CreditRating.astype("string").str.extract(r"^([1-7])(?:-|$)", expand=False)
        data["CreditRating"] = pd.to_numeric(rating, errors="coerce")
    return data.corr()


def correlation_heatmap(df: pd.DataFrame, columns=C18_COLUMNS) -> go.Figure:
    corr = correlation_matrix(df, columns)
    labels = ["<br>".join(wrap(field_label(c), width=20)) for c in columns]
    text = [[f"{value:.2f}".replace(".", ",") if pd.notna(value) else "" for value in row]
            for row in corr.values]
    fig = go.Figure(go.Heatmap(z=corr.values, x=labels, y=labels, zmin=-1, zmax=1, zmid=0, colorscale="RdBu_r",
                               text=text, texttemplate="%{text}", textfont=dict(size=11),
                               hovertemplate="%{y} × %{x}: %{z:.2f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickangle=-45)
    with_target = corr[TARGET].drop(TARGET).dropna()
    if with_target.empty:
        return empty_figure("Lát cắt chỉ có một trạng thái rời bỏ: không tính được tương quan")
    top = with_target.abs().idxmax()
    r = f"{with_target[top]:.2f}".replace(".", ",")
    return apply_style(fig, f"Tương quan với rời bỏ cao nhất: {field_label(top).lower()} (r = {r})",
                       f"{len(columns) - 1} biến đầu vào + Rời bỏ · n = {fmt_n(len(df))} khách · hệ số Pearson", height=740)


# ---------- C19: mô hình rủi ro ----------

def decile_bar(df: pd.DataFrame) -> go.Figure:
    if "RiskDecile" not in df:
        return empty_figure("Chưa có điểm rủi ro: chạy work/pipeline/run_all.py")
    table = rate_by(df, "RiskDecile")
    table["RiskDecile"] = table.RiskDecile.astype(int)
    table = table.sort_values("RiskDecile")
    base = baseline(df)
    fig = go.Figure(go.Bar(x=table.RiskDecile.astype(str), y=table.rate,
                           marker_color=[CHURN if rate > base else STAY for rate in table.rate],
                           text=[fmt_pct(r) for r in table.rate], textposition="outside",
                           customdata=_hover(table), hovertemplate=HOVER.replace("%{x}", "Nhóm rủi ro %{x}")))
    add_baseline(fig, base)
    fig.update_xaxes(title="Nhóm rủi ro (1 = thấp nhất, 10 = cao nhất)", type="category")
    fig.update_yaxes(tickformat=".0%", range=[0, table.rate.max() * 1.2], title="Tỷ lệ rời bỏ thực tế")
    top = table[table.RiskDecile == table.RiskDecile.max()]
    title = "Tỷ lệ rời bỏ thực tế theo nhóm điểm rủi ro"
    if len(top) and base:
        title = f"Nhóm rủi ro cao nhất có tỷ lệ rời bỏ {fmt_pct(top.rate.iloc[0])}, gấp {fmt_ratio(top.rate.iloc[0] / base)} lần trung bình"
    return apply_style(fig, title, "Dự đoán ngoài mẫu từ CatBoost · đỏ = tỷ lệ rời bỏ cao hơn trung bình · mỗi nhóm khoảng 10% khách")


def gain_curve(df: pd.DataFrame) -> go.Figure:
    if "RiskScore" not in df or df[TARGET].sum() == 0:
        return empty_figure("Chưa có điểm rủi ro: chạy work/pipeline/run_all.py")
    ordered = df.sort_values("RiskScore", ascending=False)
    share = np.arange(1, len(ordered) + 1) / len(ordered)
    gain = ordered[TARGET].cumsum().to_numpy() / ordered[TARGET].sum()
    step = max(1, len(ordered) // 400)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=share[::step], y=gain[::step], name="Theo mô hình", line=dict(color=ACCENT, width=3),
                             hovertemplate="Liên hệ %{x:.0%} → bắt được %{y:.0%} khách rời bỏ<extra></extra>"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], name="Chọn ngẫu nhiên", line=dict(color=MUTED, dash="dash")))
    i10 = int(0.1 * len(ordered)) - 1
    i20 = int(0.2 * len(ordered)) - 1
    for i in (i10, i20):
        fig.add_trace(go.Scatter(x=[share[i]], y=[gain[i]], mode="markers+text", showlegend=False,
                                 marker=dict(color=CHURN, size=9), text=[fmt_pct(gain[i], 0)],
                                 textposition="top left", hoverinfo="skip"))
    fig.update_xaxes(tickformat=".0%", title="% khách được liên hệ (xếp theo rủi ro)")
    fig.update_yaxes(tickformat=".0%", title="% khách rời bỏ bắt được")
    return apply_style(fig, f"Liên hệ 20% khách rủi ro nhất bắt được {fmt_pct(gain[i20], 0)} số khách sẽ rời bỏ",
                       f"10% khách rủi ro cao nhất: {fmt_pct(gain[i10], 0)} khách rời bỏ (hiệu quả so với chọn ngẫu nhiên {fmt_ratio(gain[i10] / 0.1)}×)", height=400)


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
        hovertemplate="<b>%{text}</b><br>Khách: %{customdata[0]}<br>Tỷ lệ rời bỏ: %{customdata[1]}"
                      "<br>Doanh thu/tháng bị đe dọa: %{customdata[2]}<extra></extra>"))
    add_baseline(fig, base, axis="x")
    fig.add_hline(y=df.MonthlyRevenue.mean(), line_dash="dot", line_color=NEUTRAL)
    fig.update_xaxes(tickformat=".0%", title="Tỷ lệ rời bỏ", range=[0, table.rate.max() * 1.25])
    fig.update_yaxes(title="Doanh thu TB / khách / tháng ($)", range=[table.avg_revenue.min() * 0.85, table.avg_revenue.max() * 1.15])
    act = table[table.ActionSegment != "Ổn định"]
    title = "Phân khúc ưu tiên giữ chân"
    if len(act):
        top = act.loc[act.revenue_at_risk.idxmax()]
        title = f"“{top.ActionSegment}” có doanh thu bị đe dọa lớn nhất: {fmt_money(top.revenue_at_risk)}/tháng"
    return apply_style(fig, title, "Bong bóng = số khách · phải đường đứt = tỷ lệ rời bỏ trên trung bình", height=440)


def segment_revenue_rank(df: pd.DataFrame) -> go.Figure:
    """Xếp hạng các nhóm cần can thiệp theo quy mô doanh thu bị đe dọa."""
    table = segment_summary(df)
    table = table[table.ActionSegment != "Ổn định"].sort_values("revenue_at_risk", ascending=False)
    if table.empty:
        return empty_figure("Không có nhóm cần can thiệp trong lát cắt này")
    labels = [f"{i}. {row.ActionSegment}<br>{fmt_n(row.n)} khách · {fmt_pct(row.rate)} rời bỏ"
              for i, row in enumerate(table.itertuples(), start=1)]
    custom = np.column_stack([table.n.map(fmt_n), table.churners.map(fmt_n),
                              table.rate.map(fmt_pct), table.revenue_at_risk.map(fmt_money)])
    fig = go.Figure(go.Bar(
        x=table.revenue_at_risk, y=labels, orientation="h", marker_color=ACCENT,
        text=table.revenue_at_risk.map(fmt_money), textposition="outside", cliponaxis=False,
        customdata=custom,
        hovertemplate="<b>%{y}</b><br>Số khách: %{customdata[0]}<br>Khách rời bỏ: %{customdata[1]}"
                      "<br>Tỷ lệ rời bỏ: %{customdata[2]}<br>Doanh thu tháng bị đe dọa: %{customdata[3]}<extra></extra>",
    ))
    top = table.iloc[0]
    fig.update_xaxes(title="Doanh thu tháng bị đe dọa ($)", tickformat=",.0f",
                     range=[0, max(float(table.revenue_at_risk.max()) * 1.35, 1)])
    fig.update_yaxes(title=None, autorange="reversed", categoryorder="array", categoryarray=labels)
    return apply_style(
        fig, f"Ưu tiên theo doanh thu: “{top.ActionSegment}” đứng đầu ({fmt_money(top.revenue_at_risk)}/tháng)",
        f"Chỉ các nhóm cần can thiệp · n = {fmt_n(table.n.sum())} khách · xếp theo doanh thu, chưa xét chi phí giữ chân",
        height=max(380, 80 * len(table) + 150),
    )


def segment_rate_rank(df: pd.DataFrame) -> go.Figure:
    """Biểu đồ chấm có thân nối, xếp hạng tỷ lệ rời bỏ và đối chiếu baseline."""
    table = segment_summary(df).sort_values("rate", ascending=False)
    if table.empty:
        return empty_figure()
    base = baseline(df)
    labels = [f"{row.ActionSegment}<br>{fmt_n(row.n)} khách" for row in table.itertuples()]
    stem_x, stem_y = [], []
    for label, rate in zip(labels, table.rate):
        stem_x.extend([0, rate, None])
        stem_y.extend([label, label, None])
    fig = go.Figure(go.Scatter(x=stem_x, y=stem_y, mode="lines", line=dict(color=NEUTRAL, width=3),
                               hoverinfo="skip", showlegend=False))
    colors = [NEUTRAL if segment == "Ổn định" else (CHURN if rate > base else STAY)
              for segment, rate in zip(table.ActionSegment, table.rate)]
    fig.add_trace(go.Scatter(
        x=table.rate, y=labels, mode="markers+text", marker=dict(size=14, color=colors),
        text=table.rate.map(fmt_pct), textposition="middle right", showlegend=False,
        customdata=_hover(table), hovertemplate=HOVER_H,
    ))
    add_baseline(fig, base, axis="x")
    fig.update_xaxes(title="Tỷ lệ khách thực tế rời bỏ", tickformat=".0%",
                     range=[0, max(float(table.rate.max()), base, 0.01) * 1.25])
    fig.update_yaxes(title=None, autorange="reversed", categoryorder="array", categoryarray=labels)
    top = table.iloc[0]
    return apply_style(
        fig, f"Ưu tiên theo tỷ lệ rời bỏ: “{top.ActionSegment}” cao nhất ({fmt_pct(top.rate)})",
        f"n = {fmt_n(table.n.sum())} khách · đường đứt = trung bình {fmt_pct(base)} · nhóm ổn định để đối chiếu",
        height=max(400, 72 * len(table) + 140),
    )


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
    "C05b_so_khach": tenure_stacked,
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
    "C20b_uu_tien_doanh_thu": segment_revenue_rank,
    "C20c_uu_tien_ty_le": segment_rate_rank,
}
