"""So sánh mô hình churn cùng giao thức với notebook 03: python work/experiments/compare_models.py

3-fold OOF (seed 2026); trong mỗi fold, 20% train làm inner validation để dừng sớm,
rồi fit lại trên cả fold train. Kết quả ghi ra work/build/model_comparison.csv.
Mọi cấu hình dùng cùng 10 biến. Thêm `--quick` để chỉ chạy CatBoost.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "cell2celltrain.csv"
OUT = ROOT / "work" / "build" / "model_comparison.csv"

OLD10 = [
    "MonthsInService", "CurrentEquipmentDays", "HandsetWebCapable", "MonthlyRevenue",
    "TotalRecurringCharge", "CreditRating", "MonthlyMinutes", "PercChangeMinutes",
    "PercChangeRevenues", "PeakCallsInOut",
]


def load():
    raw = pd.read_csv(RAW, na_values=["NA"])
    y = raw.Churn.eq("Yes").astype(int).to_numpy()
    X = raw[OLD10].copy()
    cats = [c for c in X if X[c].dtype == object]
    X[cats] = X[cats].fillna("Unknown").astype(str)
    return X, y, cats


def catboost_fp(depth=6, lr=0.045):
    def fit_predict(xtr, ytr, xho, cats, fold):
        it, iv = train_test_split(np.arange(len(xtr)), test_size=0.2, stratify=ytr, random_state=42 + fold)
        params = dict(depth=depth, learning_rate=lr, l2_leaf_reg=5, loss_function="Logloss", random_seed=42,
                      thread_count=4, verbose=False, allow_writing_files=False)
        probe = CatBoostClassifier(iterations=3000, **params)
        probe.fit(xtr.iloc[it], ytr[it], cat_features=cats, eval_set=(xtr.iloc[iv], ytr[iv]),
                  early_stopping_rounds=100, use_best_model=True)
        model = CatBoostClassifier(iterations=probe.best_iteration_ + 1, **params)
        model.fit(xtr, ytr, cat_features=cats)
        return model.predict_proba(xho)[:, 1]
    return fit_predict


def lightgbm_fp(xtr, ytr, xho, cats, fold):
    xtr, xho = xtr.copy(), xho.copy()
    for c in cats:
        dtype = pd.CategoricalDtype(sorted(xtr[c].unique()))
        xtr[c], xho[c] = xtr[c].astype(dtype), xho[c].astype(dtype)
    it, iv = train_test_split(np.arange(len(xtr)), test_size=0.2, stratify=ytr, random_state=42 + fold)
    params = dict(n_estimators=5000, learning_rate=0.02, num_leaves=31, min_child_samples=100, subsample=0.8,
                  subsample_freq=1, colsample_bytree=0.6, reg_lambda=5, cat_smooth=50, min_data_per_group=200,
                  verbose=-1, n_jobs=4, random_state=42)
    probe = lgb.LGBMClassifier(**params)
    probe.fit(xtr.iloc[it], ytr[it], eval_set=[(xtr.iloc[iv], ytr[iv])],
              callbacks=[lgb.early_stopping(200, verbose=False)])
    params["n_estimators"] = probe.best_iteration_
    return lgb.LGBMClassifier(**params).fit(xtr, ytr).predict_proba(xho)[:, 1]


def logistic_fp(xtr, ytr, xho, cats, fold):
    nums = [c for c in xtr if c not in cats]
    low_card = [c for c in cats if xtr[c].nunique() < 60]
    pre = ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), nums),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), low_card),
    ])
    model = make_pipeline(pre, LogisticRegression(max_iter=2000, C=0.5))
    return model.fit(xtr, ytr).predict_proba(xho)[:, 1]


def oof_scores(fit_predict, X, y, cats):
    scores = np.full(len(y), np.nan)
    folds = StratifiedKFold(n_splits=3, shuffle=True, random_state=2026).split(X, y)
    fold_auc = []
    for fold, (tr, ho) in enumerate(folds, start=1):
        scores[ho] = fit_predict(X.iloc[tr], y[tr], X.iloc[ho], cats, fold)
        fold_auc.append(roc_auc_score(y[ho], scores[ho]))
    return scores, fold_auc


def summarize(name, n_features, y, s, fold_auc, seconds):
    order = np.argsort(-s)
    top = lambda share: order[: int(np.ceil(share * len(s)))]
    return {
        "model": name, "n_features": n_features,
        "roc_auc": roc_auc_score(y, s), "fold_auc_min": min(fold_auc), "fold_auc_max": max(fold_auc),
        "pr_auc": average_precision_score(y, s), "log_loss": log_loss(y, s),
        "lift_10": float(y[top(0.10)].mean() / y.mean()), "recall_20": float(y[top(0.20)].sum() / y.sum()),
        "seconds": round(seconds, 1),
    }


def main() -> None:
    X, y, cats = load()
    experiments = [
        ("A", "CatBoost 10 biến", OLD10, catboost_fp()),
        ("B", "Logistic regression 10 biến", OLD10, logistic_fp),
        ("C", "LightGBM 10 biến", OLD10, lightgbm_fp),
    ]
    if "--quick" in sys.argv:
        experiments = [e for e in experiments if e[0] == "A"]
    rows = []
    for key, name, cols, fit_predict in experiments:
        t0 = time.time()
        s, fold_auc = oof_scores(fit_predict, X[cols], y, [c for c in cats if c in cols])
        rows.append(summarize(f"{key}. {name}", len(cols), y, s, fold_auc, time.time() - t0))
        print({k: round(v, 4) if isinstance(v, float) else v for k, v in rows[-1].items()}, flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"Đã ghi {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
