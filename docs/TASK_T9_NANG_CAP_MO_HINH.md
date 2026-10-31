# T9 — Nâng cấp mô hình churn (CatBoost 10 cột → 52 cột)

Task này là **ngoại lệ duy nhất** được sửa notebook 03 và train lại mô hình (xem `AGENTS.md`).
Làm đúng các bước dưới đây, theo thứ tự. Không sửa notebook 01–02, không đổi thuật toán, không tuning thêm.

## 1. Vì sao làm

Mô hình hiện tại chỉ dùng 10 cột trong 58 cột nguồn. Đã so sánh 5 cấu hình cùng giao thức của notebook 03
(3-fold OOF, seed 2026, dừng sớm bằng inner validation 20%) bằng `work/experiments/compare_models.py`:

| Cấu hình | Số cột | ROC-AUC (min–max fold) | AP | Lift top 10% | Recall khi gọi 20% |
|---|---:|---|---:|---:|---:|
| A. CatBoost 10 cột (hiện tại) | 10 | 0,672 (0,669–0,674) | 0,454 | 1,90× | 33,6% |
| B. Logistic regression | 52 | 0,613 (0,611–0,617) | 0,373 | 1,49× | 28,0% |
| C. CatBoost tất cả cột (vi phạm contract, chỉ tham khảo) | 56 | 0,682 (0,678–0,686) | 0,463 | 1,95× | 34,1% |
| **D. CatBoost cột v2 (chọn)** | **52** | **0,681 (0,679–0,683)** | **0,464** | **1,93×** | **34,2%** |
| E. LightGBM cột v2 | 52 | 0,684 (0,678–0,689) | 0,463 | 1,93× | 34,3% |

Kết luận:

- Thêm cột: AUC +0,010, lớn hơn hẳn độ lệch giữa các fold (~0,003–0,005). Đây là cải thiện thật.
- Đổi thuật toán: LightGBM ngang CatBoost (chênh nằm trong độ lệch fold), Logistic kém hẳn. **Giữ CatBoost**
  vì notebook 03, dashboard và verify đều đã xây quanh nó, và CatBoost xử lý cột phân loại trực tiếp.
- Bỏ 3 cột retention gần như không mất gì (C so với D), đồng thời tránh leakage: cuộc gọi tới đội giữ chân
  có thể xảy ra ngay trước khi rời bỏ. `ServiceArea` bị loại theo `project_contract.md` mục 5.
- Trần của bộ dữ liệu khoảng 0,68–0,70. Không tốn thời gian tuning thêm.

**Cột v2** = mọi cột trong `data/cell2celltrain.csv` trừ `CustomerID`, `Churn`, `ServiceArea`, `RetentionCalls`,
`RetentionOffersAccepted`, `MadeCallToRetentionTeam` → 52 cột (20 phân loại, 32 số).

## 2. Các bước

### Bước 0 — Chuẩn bị

```powershell
git pull
.\.venv\Scripts\Activate.ps1
python -m pip install -r work/requirements.txt     # có thêm lightgbm
python work/pipeline/run_all.py --only 01           # nếu work/build/ chưa có processed_customers.parquet
python work/experiments/compare_models.py --quick   # A và D, ~1,5 phút
```

Kỳ vọng: A ≈ 0,672, D ≈ 0,681 (±0,002 do khác máy/phiên bản). Lệch nhiều hơn thì **dừng và báo lại**.

### Bước 1 — Sửa `work/pipeline/03_model_training_and_evaluation.ipynb`

Sửa bằng Jupyter hoặc `nbformat`, không sửa JSON bằng tay. **Không sửa các ô 0–6 về code** (ô import, đường dẫn,
`FEATURES`, kiểm tra input): `verify_notebooks.py` chạy lại 7 ô đầu với raw CSV giả để kiểm tra guard,
nên đọc raw CSV thật phải nằm sau các ô đó. Chỉ số ô dưới đây đếm từ 0, tính cả ô markdown.

| Ô | Loại | Sửa |
|---|---|---|
| 0 | markdown | Câu hỏi đổi thành: "Mô hình CatBoost trên 52 cột nguồn (không dùng ID, retention, ServiceArea) xếp hạng churn tốt hơn baseline bao nhiêu?". Bỏ câu "Giữ cấu hình model hiện tại..." |
| 7 | markdown | `tối đa 450 vòng` → `tối đa 1500 vòng, dừng sớm sau 100 vòng` |
| 8 | code | `MAX_ITERATIONS = 1500`, `EARLY_STOPPING = 100` (bản cũ dừng ở vòng 448/450 ở fold 3, gần chạm trần) |
| 9 | markdown | Thêm: "Mô hình v2 ghép thêm các cột nguồn từ raw CSV (đã xác nhận SHA256 ở mục 2), trừ `ServiceArea` và 3 trường retention." |
| 10 | code | Thay toàn bộ bằng đoạn code bên dưới |
| 12 | code | `cat_features=CATEGORICAL` → `cat_features=MODEL_CATEGORICAL` |
| 13 | code | `model.fit(..., cat_features=CATEGORICAL)` → `cat_features=MODEL_CATEGORICAL` |
| 16 | code | `"model_version": "cell2cell-catboost-oof-v2"`, thêm khóa `"features": MODEL_FEATURES,` ngay sau |
| 29 | markdown | `Phạm vi 10 feature/depth 4–6/450 vòng còn hạn chế;` → `Mô hình dùng 52 cột nguồn, depth 4–6, tối đa 1500 vòng; đã so sánh với Logistic/LightGBM trong work/experiments/compare_models.py;`. Xóa "chưa có benchmark nhiều model," |

Code mới cho ô 10 (đã chạy thử, ra `X: (51047, 52)`):

```python
# Mô hình v2: mọi cột nguồn trừ ID/target, ServiceArea (theo contract) và 3 trường retention (nguy cơ leakage).
EXCLUDE_FROM_MODEL = [
    "CustomerID", "Churn", "ServiceArea",
    "RetentionCalls", "RetentionOffersAccepted", "MadeCallToRetentionTeam",
]
raw_source = pd.read_csv(source_path, na_values=["NA"])
MODEL_FEATURES = [c for c in raw_source.columns if c not in EXCLUDE_FROM_MODEL]
MODEL_CATEGORICAL = [c for c in MODEL_FEATURES if raw_source[c].dtype == object]
extra = raw_source[["CustomerID", *[c for c in MODEL_FEATURES if c not in data.columns]]].copy()
extra["CustomerID"] = extra.CustomerID.astype(str).astype(data.CustomerID.dtype)
X = data[["CustomerID", *[c for c in MODEL_FEATURES if c in data.columns]]].merge(
    extra, on="CustomerID", how="left", validate="one_to_one",
)
if len(X) != len(data) or not (X.CustomerID.to_numpy() == data.CustomerID.to_numpy()).all():
    raise ValueError("Ghép cột nguồn làm lệch thứ tự khách.")
X = X[MODEL_FEATURES].copy()
X[MODEL_CATEGORICAL] = X[MODEL_CATEGORICAL].fillna("Unknown").astype(str)
y = data.Churn.astype(int).to_numpy()
if "CustomerID" in X or "Churn" in X or set(y) != {0, 1}:
    raise ValueError("X/y sai hợp đồng.")
print(f"X: {X.shape}; y: {y.shape}; churn baseline: {y.mean():.2%}")
display(X.isna().sum().loc[lambda s: s.gt(0)].to_frame("Missing numeric"))
```

### Bước 2 — Chạy lại

```powershell
python work/pipeline/run_all.py --only 03             # ~5–8 phút
python work/pipeline/verify_notebooks.py
python work/dashboard/verify.py
python work/viz/prepare_viz_data.py
jupyter nbconvert --to notebook --execute --inplace work/viz/04_eda_truc_quan.ipynb
python work/viz/smoke_test.py
```

`run_all.py --only 03` chỉ ghi lại output của notebook 03. Nếu notebook 01/02 bị đổi (`git status`), chạy
`git checkout -- work/pipeline/01_data_preparation_and_eda.ipynb work/pipeline/02_analysis_and_visualization.ipynb`.

### Bước 3 — Cập nhật số trong tài liệu

Lấy số mới từ `work/build/model_metrics.json`, output notebook 04 và dashboard. **Không tự bịa số.**

| File | Chỗ cần sửa |
|---|---|
| `MODEL_CARD.md` | Dòng "Predictor": 52 cột v2 (liệt kê cột bị loại và lý do); bảng metric và capacity; depth/vòng |
| `project_contract.md` mục 5 | Danh sách predictor → "cột v2" như mục 1 file này; ghi ngày đổi 2026-10-31 và lý do. Giữ câu loại retention/ServiceArea |
| `README.md` | Dòng 145 (10 feature); dòng 57 nếu số khách/doanh thu phân khúc đổi |
| `INSIGHTS_AND_POLICY.md` | Dòng 23 (lift, "20% bắt được x%"); dòng 39 (số khách 4 nhóm, churn, doanh thu bị đe dọa) |
| `HUONG_DAN_THUYET_TRINH.md` | Dòng 37 (decile 10, gain curve), 42 (tổng khách, doanh thu), 63 (ROC-AUC ≈ 0,68) |
| `work/viz/04_eda_truc_quan.ipynb` | Các ô markdown **Insight** của C19, C19b, C20 và mục 7 insight chính: số decile 10, lift, gain, số khách 4 nhóm |
| `work/pipeline/README.md` | Dòng 34 (phạm vi 10 feature) |
| `PIPELINE_VA_CAU_TRUC_DU_AN.md` | Dòng 136 (notebook 03 dùng 10 feature) → 52 cột v2. Dòng 68/87/295 nói về notebook 01, giữ nguyên |

`dashboard_v1.py` dòng 280 ghi "Mô hình 10 feature": đổi thành "Mô hình 52 cột". Đây là sửa chữ duy nhất được phép trong file này.

Vì nhóm "Rủi ro cao (mô hình)" dựa trên `RiskDecile ≥ 8`, số khách các phân khúc sẽ đổi một chút. Đó là kết quả đúng.

## 3. Definition of Done

- [ ] `compare_models.py --quick`: D lớn hơn A ít nhất 0,005 AUC.
- [ ] `model_metrics.json`: `model_version` = `cell2cell-catboost-oof-v2`, có `features` gồm 52 cột, `roc_auc` ≈ 0,68.
- [ ] `verify_notebooks.py`, `verify.py`, `smoke_test.py` đều PASS; notebook 04 chạy không lỗi.
- [ ] Trong `git diff`, notebook 01–02 không đổi.
- [ ] Mọi file ở bước 3 không còn số AUC 0,67 hay chữ "10 feature" khi nói về mô hình (`git grep -n "0,67\|10 feature"`).
- [ ] Commit `T9: CatBoost 52 cột (AUC 0,672 → <số mới>)`, push lên branch của PR này.

## 4. Không làm

- Không dùng LightGBM/blend trong pipeline chính (chênh nằm trong nhiễu).
- Không thêm feature tự tạo (đã thử: AUC gần như không đổi).
- Không đưa `ServiceArea`, `Region` hay 3 cột retention vào mô hình.
- Không đổi số fold, seed hay cách chia inner validation.

## 5. Prompt cho Codex

```
Đọc AGENTS.md và docs/TASK_T9_NANG_CAP_MO_HINH.md. Làm đúng bước 0 → 3, báo kết quả thật của từng lệnh
ở bước 0 và 2 (dán số AUC). Nếu một lệnh lỗi hoặc AUC lệch kỳ vọng thì dừng và báo, không tự sửa vòng vo.
Xong thì tick DoD, commit và push lên branch hiện tại.
```
