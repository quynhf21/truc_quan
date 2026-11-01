# Model card — Cell2Cell churn ranking demo

## Purpose and scope

CatBoost xếp hạng rủi ro churn cho dashboard và so sánh campaign capacity. Đây là mô hình demo trên snapshot quan sát, không phải hệ thống quyết định tự động hoặc một ước lượng tác động của chính sách.

## Training contract

- Nguồn: `data/cell2celltrain.csv`, 51.047 khách có `CustomerID` và `Churn` hợp lệ.
- Target: `Churn = Yes` → 1; `No` → 0. Baseline 14.711/51.047 = 28,82%.
- Predictor của phiên bản `cell2cell-catboost-oof-10-v1`: đúng 10 biến `MonthsInService`, `CurrentEquipmentDays`, `HandsetWebCapable`, `MonthlyRevenue`, `TotalRecurringCharge`, `CreditRating`, `MonthlyMinutes`, `PercChangeMinutes`, `PercChangeRevenues`, `PeakCallsInOut`. Không dùng ID, nhãn, band hoặc ghép thêm cột raw làm đầu vào.
- Bộ 10 biến được khôi phục theo yêu cầu hiện tại. Kết quả của các cấu hình trước trong tài liệu T9 là lịch sử; kết quả chính thức hiện hành lấy từ lần chạy lại notebook 03. EDA hiện chỉ dùng cùng bộ 10 biến, nhãn và các đại lượng suy ra từ chúng. Việc bỏ biến ngoài phạm vi khỏi EDA không thay đổi mô hình đã huấn luyện.
- Missing numeric được CatBoost xử lý; categorical missing được gắn `Unknown`.
- Score để đánh giá: 3-fold out-of-fold. Trong mỗi outer training fold, một inner split chọn depth 4/6 và vòng dừng sớm (tối đa 1500 vòng, dừng sau 100 vòng không cải thiện) bằng validation log loss. Model fit lại outer training fold rồi dự đoán outer holdout. Seed outer split 2026; seed inner split 43–45.
- Không có feature thời gian thực hoặc timestamp xác minh feature tồn tại trước churn. Cần audit timing trước vận hành.

## Kết quả ngoài mẫu

Kết quả chạy lại notebook 03 trên **51.047 khách**, chỉ dùng **10 biến**:

| Metric | Giá trị |
|---|---:|
| ROC-AUC | 0,6725 |
| PR-AUC / AP | 0,4549 |
| Log loss | 0,5602 |
| Brier score | 0,1888 |
| Depth của 3 fold | 6 / 4 / 6 |

| Capacity | Khách được chọn | Churner quá khứ trong nhóm | Precision | Recall | Lift so baseline |
|---:|---:|---:|---:|---:|---:|
| 5% | 2.553 | 1.577 | 61,8% | 10,7% | 2,14× |
| 10% | 5.105 | 2.766 | 54,2% | 18,8% | 1,88× |
| 20% | 10.210 | 4.947 | 48,5% | 33,6% | 1,68× |

Số liệu lấy từ `work/build/model_metrics.json` và `customer_mart.parquet` của cùng lần chạy. Notebook 04 loại dòng có số âm bất thường trước EDA nên một số chỉ số theo lát cắt có thể khác bảng toàn nguồn này. Churner quá khứ được tiếp cận không phải số khách đã được chính sách cứu giữ.


## Giới hạn và governance

- Snapshot không chứng minh thứ tự thời gian hay quan hệ nhân quả; hai trường `PercChange*` chưa rõ đơn vị và thời điểm sẵn có.
- Điểm rủi ro chỉ dùng để xếp hạng. Không dùng mặc định ngưỡng 0,5 để quyết định liên hệ.
- Reason code trong demo là rule diễn giải tín hiệu nguồn, không phải SHAP của một dự đoán và không phải nguyên nhân churn.
- `CreditRating` có rủi ro fairness. Trước sử dụng thật cần kiểm tra disparity, phê duyệt chính sách và ngăn dùng để từ chối hỗ trợ/áp giá bất lợi.
- Chưa có external holdout theo thời gian, drift check hoặc thử nghiệm treatment/control. Không công bố ROI hay hiệu quả chính sách.
- Khi dùng cho khách hàng mới, cần train một model phiên bản sản xuất trên dữ liệu quá khứ phù hợp, kiểm tra schema/timing, lưu version và giám sát calibration/lift.
