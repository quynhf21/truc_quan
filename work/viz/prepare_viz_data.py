"""Chuẩn bị bảng phân tích cho phần trực quan hóa: python work/viz/prepare_viz_data.py"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "cell2celltrain.csv"
BUILD = ROOT / "work" / "build"
MART = BUILD / "customer_mart.parquet"
OUT = BUILD / "viz_customers.parquet"

NUMERIC = [
    "MonthlyRevenue", "MonthlyMinutes", "TotalRecurringCharge", "DirectorAssistedCalls", "OverageMinutes",
    "RoamingCalls", "PercChangeMinutes", "PercChangeRevenues", "DroppedBlockedCalls", "UnansweredCalls",
    "CustomerCareCalls", "ThreewayCalls", "ReceivedCalls", "OutboundCalls", "InboundCalls", "PeakCallsInOut",
    "OffPeakCallsInOut", "CallWaitingCalls", "MonthsInService", "UniqueSubs", "ActiveSubs", "Handsets",
    "HandsetModels", "CurrentEquipmentDays", "AgeHH1", "RetentionCalls", "RetentionOffersAccepted",
    "ReferralsMadeBySubscriber", "AdjustmentsToCreditRating",
]
CATEGORICAL = [
    "ServiceArea", "HandsetWebCapable", "HandsetRefurbished", "HandsetPrice", "MadeCallToRetentionTeam",
    "CreditRating", "IncomeGroup", "PrizmCode", "Occupation", "MaritalStatus",
]

# Các mức thay đổi có thể âm hợp lệ; các đại lượng còn lại không được âm.
SIGNED_COLUMNS = {"PercChangeMinutes", "PercChangeRevenues"}
NON_NEGATIVE_COLUMNS = [column for column in NUMERIC if column not in SIGNED_COLUMNS]


def remove_invalid_negative_rows(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Loại dòng có số âm bất thường, kèm số trường hợp theo từng cột để đối soát."""
    negative = raw[NON_NEGATIVE_COLUMNS].lt(0)
    counts = negative.sum().loc[lambda values: values.gt(0)].astype(int)
    return raw.loc[~negative.any(axis=1)].copy(), counts

# Ngưỡng band công khai; pd.cut đóng bên phải.
BANDS = {
    "TenureBand": ("MonthsInService", [0, 6, 12, 18, 24, 36, np.inf],
                   ["0–6 tháng", "7–12 tháng", "13–18 tháng", "19–24 tháng", "25–36 tháng", ">36 tháng"]),
    "EquipmentAgeBand": ("CurrentEquipmentDays", [-0.1, 180, 365, 730, np.inf],
                         ["≤180 ngày", "181–365 ngày", "366–730 ngày", ">730 ngày"]),
    "CareCallsBand": ("CustomerCareCalls", [-0.1, 0, 1, 3, 10, np.inf], ["0", "≤1", "1–3", "3–10", ">10"]),
    "DroppedBand": ("DroppedBlockedCalls", [-0.1, 0, 5, 15, 40, np.inf], ["0", "≤5", "5–15", "15–40", ">40"]),
    "OverageBand": ("OverageMinutes", [-0.1, 0, 50, 200, np.inf], ["0", "≤50", "50–200", ">200"]),
    "MinutesBand": ("MonthlyMinutes", [-0.1, 150, 500, np.inf], ["≤150 phút", "150–500 phút", ">500 phút"]),
}

def add_bands(df: pd.DataFrame) -> pd.DataFrame:
    for band, (col, bins, labels) in BANDS.items():
        values = pd.cut(df[col], bins=bins, labels=labels, include_lowest=True).astype("object")
        values[df[col].lt(0)] = "Bất thường"
        values[df[col].isna()] = "Không rõ"
        order = labels + [x for x in ["Bất thường", "Không rõ"] if x in set(values)]
        df[band] = pd.Categorical(values, categories=order, ordered=True)
    return df


SEGMENTS = ["Đã báo động", "Hết hợp đồng", "Máy cũ", "Rủi ro cao (mô hình)", "Ổn định"]


def add_segment(df: pd.DataFrame) -> pd.DataFrame:
    # Rule có thứ tự ưu tiên: điều kiện đầu tiên khớp sẽ quyết định segment.
    # Tháng 10–13 bao quanh đỉnh churn tháng 11–12 (hết hợp đồng 1 năm).
    conditions = [
        df.MadeCallToRetentionTeam.eq("Yes"),
        df.MonthsInService.between(10, 13),
        df.CurrentEquipmentDays.gt(730) | (df.CurrentEquipmentDays.ge(365) & df.HandsetWebCapable.eq("No")),
    ]
    labels = SEGMENTS[:3]
    if "RiskDecile" in df:
        conditions.append(df.RiskDecile.ge(8))
        labels.append(SEGMENTS[3])
    segment = np.select(conditions, labels, default=SEGMENTS[-1])
    df["ActionSegment"] = pd.Categorical(segment, categories=[*labels, SEGMENTS[-1]], ordered=True)
    return df


def prepare_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa bảng đã kiểm tra; không đọc lại dữ liệu nguồn hoặc huấn luyện mô hình."""
    if raw[NON_NEGATIVE_COLUMNS].lt(0).any().any():
        raise ValueError("Dữ liệu còn số âm bất thường. Hãy chạy remove_invalid_negative_rows trước.")
    df = raw[["CustomerID", "Churn", *NUMERIC, *CATEGORICAL]].copy()
    if not df.Churn.isin(["Yes", "No"]).all():
        raise SystemExit("Cột Churn có giá trị khác Yes/No.")
    df["ChurnFlag"] = df.Churn.eq("Yes").astype(int)
    for col in CATEGORICAL:
        df[col] = df[col].fillna("Unknown").astype(str)
    df["Region"] = df.ServiceArea.where(df.ServiceArea.ne("Unknown"), None).str[:3].fillna("Unknown")
    df["RetentionOfferAccepted"] = np.where(df.RetentionOffersAccepted.gt(0), "Yes", "No")
    df = add_bands(df)

    if MART.exists():
        mart = pd.read_parquet(MART, columns=["CustomerID", "RiskScore", "RiskDecile"])
        mart["CustomerID"] = mart.CustomerID.astype("int64")
        df = df.merge(mart, on="CustomerID", how="left", validate="one_to_one")
    else:
        print(f"Không thấy {MART.name}: bỏ qua RiskScore/RiskDecile (chạy work/pipeline/run_all.py nếu cần).")
    return add_segment(df)


def build() -> pd.DataFrame:
    raw = pd.read_csv(RAW, na_values=["NA"])
    cleaned, _ = remove_invalid_negative_rows(raw)
    return prepare_data(cleaned)


def fmt_n(value) -> str:
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value) -> str:
    return f"{100 * value:.2f}%".replace(".", ",")


def main() -> None:
    raw = pd.read_csv(RAW, na_values=["NA"])
    cleaned, negative_counts = remove_invalid_negative_rows(raw)
    df = prepare_data(cleaned)
    BUILD.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)

    print(f"Đã ghi {OUT.relative_to(ROOT)}: {fmt_n(len(df))} dòng, {df.shape[1]} cột")
    print(f"Đã loại {fmt_n(len(raw) - len(cleaned))} dòng có số âm bất thường; còn {fmt_n(len(cleaned))} khách.")
    print("Số âm theo cột (một dòng có thể xuất hiện ở nhiều cột):")
    print(negative_counts.to_string() if len(negative_counts) else "Không có.")
    print(f"Rời bỏ: {fmt_n(df.ChurnFlag.sum())} khách ({fmt_pct(df.ChurnFlag.mean())})")
    missing = df[NUMERIC].isna().mean().loc[lambda s: s.gt(0)].sort_values(ascending=False)
    print("\n% missing (cột numeric có missing):")
    print((100 * missing).round(2).to_string())
    print("\nSố khách theo ActionSegment:")
    print(df.groupby("ActionSegment", observed=False).ChurnFlag.agg(n="size", churn_rate="mean").round(3).to_string())
    if "RiskDecile" in df:
        print(f"\nRiskDecile có cho {fmt_n(df.RiskDecile.notna().sum())} khách.")


if __name__ == "__main__":
    main()
