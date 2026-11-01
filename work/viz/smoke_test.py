"""Gọi mọi hàm vẽ trên dữ liệu thật và các lát cắt nhỏ: python work/viz/smoke_test.py"""

from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import charts  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "build" / "viz_customers.parquet"


def check(df, name) -> bool:
    errors = []
    for key, build in charts.FIGURES.items():
        try:
            build(df)
        except Exception as exc:  # gom lỗi để báo hết một lần
            errors.append(f"{key}: {type(exc).__name__}: {exc}")
    print(f"{name} ({len(df)} dòng):", "OK" if not errors else "")
    for err in errors:
        print("   ", err)
    return not errors


if __name__ == "__main__":
    df = pd.read_parquet(DATA)
    for key, build in charts.FIGURES.items():
        title = build(df).layout.title.text.split("<br>")[0]
        print(key, "|", title.replace("<b>", "").replace("</b>", ""))
    # Dashboard tự chặn lát cắt rỗng; ở đây thử các lát cắt nhỏ/lệch mà bộ lọc có thể tạo ra.
    slices = {"không web": df[df.HandsetWebCapable == "No"], "50 dòng": df.head(50),
              "chỉ churner": df[df.ChurnFlag == 1].head(300), "chỉ khách ở lại": df[df.ChurnFlag == 0].head(300),
              "1 khách": df.head(1)}
    ok = all([check(part, name) for name, part in slices.items()])
    sys.exit(0 if ok else 1)
