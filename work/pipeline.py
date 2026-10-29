"""Reproducible one-pass Cell2Cell QA, analysis mart, and out-of-fold scoring."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "data" / "cell2celltrain.csv"
OUT = ROOT / "build"
FEATURES = [
    "MonthsInService", "CurrentEquipmentDays", "HandsetWebCapable",
    "MonthlyRevenue", "TotalRecurringCharge", "CreditRating",
    "MonthlyMinutes", "PercChangeMinutes", "PercChangeRevenues",
    "PeakCallsInOut",
]
CATEGORICAL = ["HandsetWebCapable", "CreditRating"]
NUMERIC = [column for column in FEATURES if column not in CATEGORICAL]


def json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    raise TypeError(type(value).__name__)


def load_and_validate() -> tuple[pd.DataFrame, dict]:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    raw = pd.read_csv(SOURCE, na_values=["NA", "N/A", "?", "NULL"], low_memory=False)
    required = ["CustomerID", "Churn", *FEATURES]
    absent = sorted(set(required) - set(raw.columns))
    if absent:
        raise ValueError(f"Missing required columns: {absent}")
    raw_ids = raw["CustomerID"].astype("string")
    target = raw["Churn"].astype("string").str.strip()
    invalid_target = int((~target.isin(["Yes", "No"])).sum())
    missing_id = int(raw_ids.isna().sum())
    duplicate_id = int(raw_ids.duplicated(keep=False).sum())
    if invalid_target or missing_id or duplicate_id:
        raise ValueError(
            f"Source contract failed: invalid_target={invalid_target}, "
            f"missing_id={missing_id}, duplicate_id_rows={duplicate_id}"
        )

    df = raw[required].copy()
    df["CustomerID"] = raw_ids
    df["Churn"] = target.eq("Yes").astype("int8")
    for column in NUMERIC:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in CATEGORICAL:
        df[column] = df[column].astype("string").str.strip().fillna("Unknown")

    missing_any = df[FEATURES].replace("Unknown", np.nan).isna().any(axis=1)
    complete_all = raw.notna().all(axis=1)
    negative_counts = {column: int((df[column] < 0).sum()) for column in NUMERIC}
    qa = {
        "source": str(SOURCE.relative_to(ROOT.parent)),
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "raw_rows": len(raw), "raw_columns": len(raw.columns),
        "unique_customer_ids": int(df["CustomerID"].nunique()),
        "target_counts": {"Yes": int(df["Churn"].sum()), "No": int((1-df["Churn"]).sum())},
        "baseline_churn_rate": float(df["Churn"].mean()),
        "missing_by_feature": {column: int(df[column].isna().sum()) for column in NUMERIC}
        | {column: int(df[column].eq("Unknown").sum()) for column in CATEGORICAL},
        "missing_any_model_feature_rows": int(missing_any.sum()),
        "missing_any_model_feature_churners": int(df.loc[missing_any, "Churn"].sum()),
        "complete_10_feature_rows": int((~missing_any).sum()),
        "complete_58_column_rows": int(complete_all.sum()),
        "negative_numeric_counts": negative_counts,
        "invalid_target_rows": invalid_target,
        "missing_id_rows": missing_id,
        "duplicate_id_rows": duplicate_id,
        "notes": [
            "Negative source values retained and flagged, not silently clipped.",
            "PercChange* units and availability timing remain unverified.",
            "Snapshot data cannot establish causal or temporal order.",
        ],
    }
    return df, qa


def add_bands(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["TenureBand"] = pd.cut(
        df["MonthsInService"], bins=[-np.inf, 11, 18, 24, np.inf],
        labels=["6–11 tháng", "12–18 tháng", "19–24 tháng", "25+ tháng"],
    ).astype("string")
    df["EquipmentAgeBand"] = pd.cut(
        df["CurrentEquipmentDays"], bins=[0, 180, 365, 730, np.inf],
        labels=["≤180 ngày", "181–365 ngày", "366–730 ngày", ">730 ngày"],
        include_lowest=True,
    ).astype("string").fillna("Không rõ")
    df.loc[df["CurrentEquipmentDays"].lt(0), "EquipmentAgeBand"] = "Giá trị âm"
    df["ValueTier"] = pd.cut(
        df["MonthlyRevenue"], bins=[0, 35, 70, np.inf],
        labels=["Thấp (≤35)", "Trung bình (35–70)", "Cao (>70)"],
        include_lowest=True,
    ).astype("string").fillna("Không rõ")
    df.loc[df["MonthlyRevenue"].lt(0), "ValueTier"] = "Giá trị âm"
    df["ChargeBand"] = pd.cut(
        df["TotalRecurringCharge"], bins=[0, 30, 60, np.inf],
        labels=["≤30", "30–60", ">60"],
        include_lowest=True,
    ).astype("string").fillna("Không rõ")
    df.loc[df["TotalRecurringCharge"].lt(0), "ChargeBand"] = "Giá trị âm"
    df["MinutesBand"] = pd.cut(
        df["MonthlyMinutes"], bins=[-np.inf, 150, 500, np.inf],
        labels=["≤150", "151–500", ">500"],
    ).astype("string").fillna("Không rõ")
    # The source's PercChange* units are not verified. These are source-value bands.
    df["UsageTrendBand"] = pd.cut(
        df["PercChangeMinutes"], bins=[-np.inf, -83, 0, 66, np.inf],
        labels=["Giảm mạnh (≤-83)", "Giảm nhẹ (-83–0)", "Tăng nhẹ (0–66)", "Tăng mạnh (>66)"],
    ).astype("string").fillna("Không rõ")
    df["RevenueTrendBand"] = pd.cut(
        df["PercChangeRevenues"], bins=[-np.inf, -7.1, 0, 1.6, np.inf],
        labels=["Giảm mạnh (≤-7,1)", "Giảm nhẹ (-7,1–0)", "Tăng nhẹ (0–1,6)", "Tăng mạnh (>1,6)"],
    ).astype("string").fillna("Không rõ")
    return df


def fit_model(x_train, y_train, x_valid, y_valid, depth):
    model = CatBoostClassifier(
        iterations=450, depth=depth, learning_rate=0.045, loss_function="Logloss",
        eval_metric="Logloss", random_seed=42, verbose=False, thread_count=-1,
        l2_leaf_reg=5,
    )
    model.fit(
        x_train, y_train, cat_features=CATEGORICAL,
        eval_set=(x_valid, y_valid), early_stopping_rounds=45,
        use_best_model=True,
    )
    return model


def model_and_scores(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    x = df[FEATURES].copy()
    for column in CATEGORICAL:
        x[column] = x[column].fillna("Unknown").astype(str)
    y = df["Churn"].astype(int).to_numpy()
    oof = np.full(len(df), np.nan)
    fold_details = []
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=2026)
    for fold, (outer_train, outer_valid) in enumerate(skf.split(x, y), start=1):
        inner_train, inner_valid = train_test_split(
            outer_train, test_size=0.20, stratify=y[outer_train], random_state=42 + fold
        )
        candidates = {}
        for depth in (4, 6):
            candidate = fit_model(x.iloc[inner_train], y[inner_train],
                                  x.iloc[inner_valid], y[inner_valid], depth)
            inner_p = candidate.predict_proba(x.iloc[inner_valid])[:, 1]
            candidates[str(depth)] = {"inner_validation_log_loss": float(log_loss(y[inner_valid], inner_p)),
                                      "best_iteration": int(candidate.best_iteration_)}
        chosen_depth = min(candidates, key=lambda d: candidates[d]["inner_validation_log_loss"])
        best_iter = max(1, candidates[chosen_depth]["best_iteration"] + 1)
        model = CatBoostClassifier(
            iterations=best_iter, depth=int(chosen_depth), learning_rate=0.045,
            loss_function="Logloss", random_seed=42 + fold, verbose=False,
            thread_count=-1, l2_leaf_reg=5,
        )
        model.fit(x.iloc[outer_train], y[outer_train], cat_features=CATEGORICAL)
        oof[outer_valid] = model.predict_proba(x.iloc[outer_valid])[:, 1]
        fold_details.append({"fold": fold, "n": len(outer_valid),
                             "selected_depth": int(chosen_depth), "iterations": best_iter,
                             "depth_candidates": candidates,
                             "log_loss": float(log_loss(y[outer_valid], oof[outer_valid])),
                             "roc_auc": float(roc_auc_score(y[outer_valid], oof[outer_valid]))})
    if np.isnan(oof).any():
        raise AssertionError("Missing OOF predictions")
    df = df.copy()
    df["RiskScore"] = oof
    rank = pd.Series(oof).rank(method="first", pct=True).to_numpy()
    df["RiskDecile"] = np.ceil(rank * 10).astype(int).clip(1, 10)

    df["ValuePriority"] = np.select(
        [df["MonthlyRevenue"].ge(70), df["MonthlyRevenue"].ge(35)],
        ["Cao", "Trung bình"], default="Thấp/không rõ",
    )
    df["PrioritySegment"] = np.select(
        [df["RiskDecile"].ge(9) & df["MonthlyRevenue"].ge(70),
         df["RiskDecile"].ge(9),
         df["RiskDecile"].ge(7) & df["MonthlyRevenue"].ge(70)],
        ["P1 · Risk cao / value cao", "P2 · Risk cao", "P3 · Value cao / risk khá"],
        default="P4 · Theo dõi",
    )
    # Operational hypotheses. These codes describe source signals, not model attribution.
    df["ReasonCode"] = np.select(
        [df["CurrentEquipmentDays"].ge(730) | df["HandsetWebCapable"].eq("No"),
         df["PercChangeMinutes"].le(-83),
         df["MonthsInService"].between(12, 18),
         df["TotalRecurringCharge"].gt(60) & df["MonthlyMinutes"].lt(150)],
        ["Thiết bị cần rà soát", "Sử dụng suy giảm", "Giai đoạn vòng đời", "Gói cước cần rà soát"],
        default="Rà soát chung",
    )

    depths = [fold["selected_depth"] for fold in fold_details]
    metrics = {"chosen_depth": int(pd.Series(depths).mode().iloc[0]),
               "depth_selection": "inside each outer training fold",
               "folds": fold_details, "roc_auc": float(roc_auc_score(y, oof)),
               "pr_auc": float(average_precision_score(y, oof)),
               "log_loss": float(log_loss(y, oof)),
               "brier": float(brier_score_loss(y, oof)),
               "baseline_churn_rate": float(y.mean()), "score_type": "3-fold out-of-fold"}
    for capacity in (0.05, 0.10, 0.20):
        selected = df.nlargest(int(np.ceil(len(df) * capacity)), "RiskScore")
        metrics[f"capacity_{int(capacity*100)}"] = {
            "n": len(selected), "churners": int(selected["Churn"].sum()),
            "precision": float(selected["Churn"].mean()),
            "recall": float(selected["Churn"].sum() / df["Churn"].sum()),
            "lift": float(selected["Churn"].mean() / df["Churn"].mean()),
        }
    return df, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-only", action="store_true", help="Run source QA without fitting a model")
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    df, qa = load_and_validate()
    df = add_bands(df)
    (OUT / "qa_report.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")
    if args.qa_only:
        print(json.dumps({"qa_report": str(OUT / "qa_report.json"), "raw_rows": len(df)}, ensure_ascii=False))
        return
    df, metrics = model_and_scores(df)
    df.to_parquet(OUT / "customer_mart.parquet", index=False)
    (OUT / "model_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")
    policy = pd.DataFrame([
        ["Thiết bị cần rà soát", "Risk decile ≥7; thiết bị >730 ngày hoặc không web-capable", "Device review / hướng dẫn / upgrade pilot", "Incremental retention", "Chi phí trợ giá, khiếu nại", "Ưu tiên pilot"],
        ["Sử dụng suy giảm", "Risk decile ≥7; mức thay đổi minutes nguồn ≤-83", "Re-engagement / plan review", "Incremental retention, usage recovery", "Opt-out, contact fatigue", "Ưu tiên pilot"],
        ["Giai đoạn vòng đời", "Risk decile ≥7; tenure 12–18 tháng", "Check-in và giải thích gói", "Incremental retention", "Contact fatigue, offer cost", "Ưu tiên pilot"],
        ["Gói cước cần rà soát", "Risk decile ≥7; charge >60 và minutes <150", "Bill review / right-size plan", "Incremental retention, plan acceptance", "Revenue dilution", "Khám phá thêm"],
        ["Rà soát chung", "Risk decile ≥7; không khớp rule cụ thể", "Customer care review", "Incremental retention", "Cost per save", "Fallback, chưa pilot"],
    ], columns=["ReasonCode", "Eligibility hypothesis", "Treatment hypothesis", "Primary KPI", "Guardrail", "Status"])
    policy.to_csv(OUT / "policy_matrix.csv", index=False, encoding="utf-8-sig")
    summary = {"rows": len(df), "churners": int(df["Churn"].sum()), "model_auc": metrics["roc_auc"],
               "artifacts": ["qa_report.json", "customer_mart.parquet", "model_metrics.json", "policy_matrix.csv"]}
    print(json.dumps(summary, ensure_ascii=False, default=json_default))


if __name__ == "__main__":
    main()
