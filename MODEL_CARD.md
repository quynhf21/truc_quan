# Model card — Cell2Cell churn ranking demo

## Purpose and scope

CatBoost xếp hạng rủi ro churn cho dashboard và so sánh campaign capacity. Đây là mô hình demo trên snapshot quan sát, không phải hệ thống quyết định tự động hoặc một ước lượng tác động của chính sách.

## Training contract

- Nguồn: `data/cell2celltrain.csv`, 51.047 khách có `CustomerID` và `Churn` hợp lệ.
- Target: `Churn = Yes` → 1; `No` → 0. Baseline 14.711/51.047 = 28,82%.
- Predictor (v2, từ 31/10/2026): 52 cột nguồn, tức mọi cột của raw CSV trừ `CustomerID`, `Churn`, `ServiceArea` (theo `project_contract.md`) và 3 trường retention `RetentionCalls`, `RetentionOffersAccepted`, `MadeCallToRetentionTeam` (có thể xảy ra ngay trước khi rời bỏ, nguy cơ leakage). Không dùng derived bands. Bản v1 dùng 10 base feature, ROC-AUC 0,6715.
- Lý do đổi: `work/experiments/compare_models.py` cho thấy thêm cột tăng AUC ~0,01, lớn hơn độ lệch giữa các fold; LightGBM ngang CatBoost, Logistic regression kém hẳn (0,613). Chi tiết: `docs/TASK_T9_NANG_CAP_MO_HINH.md`.
- Missing numeric được CatBoost xử lý; categorical missing được gắn `Unknown`.
- Score để đánh giá: 3-fold out-of-fold. Trong mỗi outer training fold, một inner split chọn depth 4/6 và vòng dừng sớm (tối đa 1500 vòng, dừng sau 100 vòng không cải thiện) bằng validation log loss. Model fit lại outer training fold rồi dự đoán outer holdout. Seed outer split 2026; seed inner split 43–45.
- Không có feature thời gian thực hoặc timestamp xác minh feature tồn tại trước churn. Cần audit timing trước vận hành.

## Kết quả ngoài mẫu

| Metric | Giá trị |
|---|---:|
| ROC-AUC | 0,6816 |
| PR-AUC | 0,4624 |
| Log loss | 0,5564 |
| Brier score | 0,1873 |
| Depth được chọn trong 3 fold | 6 / 6 / 4 |

| Capacity | Khách được chọn | Churner quá khứ trong nhóm | Precision | Recall | Lift so baseline |
|---:|---:|---:|---:|---:|---:|
| 5% | 2.553 | 1.568 | 61,4% | 10,7% | 2,13× |
| 10% | 5.105 | 2.846 | 55,7% | 19,3% | 1,93× |
| 20% | 10.210 | 5.016 | 49,1% | 34,1% | 1,70× |

Các số này được ghi lại từ `work/build/model_metrics.json` của lần chạy cuối; khi thay nguồn hoặc code phải dùng JSON mới làm số chính thức. Dashboard vẽ calibration, gain và decile từ score ngoài mẫu. Churner quá khứ trong nhóm **không phải** số khách được chính sách cứu giữ.

## Giới hạn và governance

- Snapshot không chứng minh thứ tự thời gian hay quan hệ nhân quả; hai trường `PercChange*` chưa rõ đơn vị và thời điểm sẵn có.
- Điểm rủi ro chỉ dùng để xếp hạng. Không dùng mặc định ngưỡng 0,5 để quyết định liên hệ.
- Reason code trong demo là rule diễn giải tín hiệu nguồn, không phải SHAP của một dự đoán và không phải nguyên nhân churn.
- `CreditRating` có rủi ro fairness. Trước sử dụng thật cần kiểm tra disparity, phê duyệt chính sách và ngăn dùng để từ chối hỗ trợ/áp giá bất lợi.
- Chưa có external holdout theo thời gian, drift check hoặc thử nghiệm treatment/control. Không công bố ROI hay hiệu quả chính sách.
- Khi dùng cho khách hàng mới, cần train một model phiên bản sản xuất trên dữ liệu quá khứ phù hợp, kiểm tra schema/timing, lưu version và giám sát calibration/lift.
