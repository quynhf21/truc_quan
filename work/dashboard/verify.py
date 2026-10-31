"""Artifact and dashboard smoke checks for the local demo."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parent
BUILD = ROOT.parent / "build"


def main():
    qa = json.loads((BUILD / "qa_report.json").read_text(encoding="utf-8"))
    model = json.loads((BUILD / "model_metrics.json").read_text(encoding="utf-8"))
    mart = pd.read_parquet(BUILD / "customer_mart.parquet")
    policy = pd.read_csv(BUILD / "policy_matrix.csv")
    assert qa["raw_rows"] == len(mart) == 51047
    assert qa["target_counts"]["Yes"] == int(mart.Churn.sum()) == 14711
    assert qa["unique_customer_ids"] == mart.CustomerID.nunique() == len(mart)
    assert len(model["folds"]) == 3
    assert all("depth_candidates" in fold for fold in model["folds"])
    assert mart.RiskScore.between(0, 1).all() and mart.RiskScore.notna().all()
    assert set(mart.RiskDecile.unique()) == set(range(1, 11))
    assert mart.PrioritySegment.notna().all() and mart.ReasonCode.notna().all()
    assert sum(mart.groupby("PrioritySegment").size()) == len(mart)
    assert np.isclose(roc_auc_score(mart.Churn, mart.RiskScore), model["roc_auc"])
    assert policy.ReasonCode.is_unique and set(mart.ReasonCode.unique()) == set(policy.ReasonCode)
    import dashboard_v1 as dashboard
    for route in ("/", "/drivers", "/risk", "/strategy"):
        assert dashboard.render_page(route, None, None, None, None)
        assert dashboard.render_page(route, ["12–18 tháng"], ["No"], None, [9, 10])
    print("PASS: source reconciliation, OOF scores, segments, policy coverage, four dashboard routes and filtered views")


if __name__ == "__main__":
    main()
