"""Build a static, identifier-free GitHub Pages edition of the BI dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from shutil import copy2

import pandas as pd
from plotly.offline import get_plotlyjs


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent.parent
BUILD = ROOT.parent / "build"
SOURCE = ROOT / "pages_src"
SITE = PROJECT_ROOT / "site"

COLUMNS = [
    "TenureBand", "EquipmentAgeBand", "HandsetWebCapable", "ValueTier",
    "ChargeBand", "MinutesBand", "UsageTrendBand", "RiskDecile",
    "PrioritySegment", "ReasonCode",
]


def build_site() -> None:
    mart_path = BUILD / "customer_mart.parquet"
    if not mart_path.exists():
        raise SystemExit("Missing customer mart. Run: python work/pipeline/run_all.py")
    mart = pd.read_parquet(mart_path)
    if mart.CustomerID.duplicated().any():
        raise ValueError("Duplicate customer IDs in mart")
    dictionaries = {}
    encoded = []
    for column in COLUMNS:
        values = mart[column].astype(str).fillna("Không rõ")
        categories = list(dict.fromkeys(values.tolist()))
        dictionaries[column] = categories
        encoded.append(values.map({value: index for index, value in enumerate(categories)}).astype(int).to_numpy())
    encoded.append(mart.Churn.astype(int).to_numpy())
    encoded.append(mart.RiskScore.astype(float).round(6).to_numpy())
    rows = [[*[int(value) for value in item[:11]], float(item[11])]
            for item in zip(*encoded)]
    qa = json.loads((BUILD / "qa_report.json").read_text(encoding="utf-8"))
    model = json.loads((BUILD / "model_metrics.json").read_text(encoding="utf-8"))
    policies = pd.read_csv(BUILD / "policy_matrix.csv").to_dict(orient="records")
    payload = {
        "schema": 1,
        "columns": COLUMNS + ["Churn", "RiskScore"],
        "dictionary": dictionaries,
        "rows": rows,
        "qa": {"raw_rows": qa["raw_rows"], "raw_columns": qa["raw_columns"],
               "missing_any_model_feature_rows": qa["missing_any_model_feature_rows"],
               "complete_58_column_rows": qa["complete_58_column_rows"],
               "baseline_churn_rate": qa["baseline_churn_rate"]},
        "model": {key: model[key] for key in ("chosen_depth", "roc_auc", "pr_auc", "log_loss", "brier", "score_type")},
        "policies": policies,
    }
    if len(rows) != qa["raw_rows"] or sum(row[10] for row in rows) != qa["target_counts"]["Yes"]:
        raise AssertionError("Static export does not reconcile with QA")
    if SITE.resolve() != (PROJECT_ROOT / "site").resolve():
        raise AssertionError("Unexpected site output path")
    SITE.mkdir(exist_ok=True)
    copy2(SOURCE / "index.html", SITE / "index.html")
    copy2(SOURCE / "app.js", SITE / "app.js")
    copy2(SOURCE / "style.css", SITE / "style.css")
    (SITE / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
    (SITE / "data.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    published = {item.name for item in SITE.iterdir()}
    expected = {"index.html", "app.js", "style.css", "plotly.min.js", "data.json", ".nojekyll"}
    if published != expected:
        raise AssertionError(f"Unexpected published files: {published ^ expected}")
    if "CustomerID" in (SITE / "data.json").read_text(encoding="utf-8"):
        raise AssertionError("Identifier leaked into Pages data")
    print(f"Built {SITE}: {len(rows):,} identifier-free rows, {sum(row[10] for row in rows):,} churners")


if __name__ == "__main__":
    build_site()
