# M0 — Hợp đồng triển khai demo Cell2Cell Churn & Retention

Trạng thái: **M0 hoàn thành — 29/10/2026**. Đây là phạm vi triển khai rút gọn cho mục tiêu hoàn thành trong tối đa 20 giờ. `project_context (1).md` và `analysis_pipeline (1).md` thuộc phiên bản cũ, đã lưu trong `C:\Users\Admin\Documents\back`; khi số liệu hoặc phạm vi khác nhau, hợp đồng M0 này áp dụng cho bản demo.

## 1. Câu hỏi và sản phẩm cuối

**Câu hỏi điều hành:** Khách hàng nào có khả năng rời bỏ cao, những tín hiệu nào khiến họ đáng chú ý, và nên thử chính sách giữ chân nào với từng nhóm?

Sản phẩm chính là web dashboard BI gồm bốn trang:

1. **Overview:** chất lượng dữ liệu, baseline churn, quy mô nhóm và insight chính.
2. **Drivers:** tenure, thiết bị, revenue/phí và sử dụng/hành vi; mỗi góc nhìn có risk và reach.
3. **Risk & Segments:** chất lượng mô hình, risk decile, capacity 5/10/20%, phân khúc ưu tiên.
4. **Retention Strategy:** reason code, nhóm đủ điều kiện, can thiệp đề xuất, KPI và guardrail.

Mô hình là công cụ xếp hạng cho dashboard. Chính sách là giả thuyết cần thử nghiệm, không phải tác động đã được chứng minh.

## 2. Câu hỏi kinh doanh được khóa cho demo

| ID | Câu hỏi | Trang |
|---|---|---|
| Q1 | Dữ liệu và mẫu số phân tích có đáng tin không? | Overview |
| Q2 | Churn lớn đến đâu và nhóm nào đóng góp nhiều churner? | Overview |
| Q3 | Rủi ro khác nhau thế nào theo tenure? | Drivers |
| Q4 | Tuổi và khả năng thiết bị liên quan thế nào đến churn? | Drivers |
| Q5 | Revenue và phí định kỳ liên quan thế nào đến risk/value? | Drivers |
| Q6 | Mức và thay đổi sử dụng có giúp nhận diện disengagement? | Drivers |
| Q7 | Mô hình xếp hạng rủi ro đáng tin và hữu ích đến đâu? | Risk & Segments |
| Q8 | Với capacity hữu hạn, nên ưu tiên phân khúc nào? | Risk & Segments |
| Q9 | Nên thử chính sách nào, đo bằng KPI và guardrail nào? | Retention Strategy |

Không bắt buộc triển khai đủ 20 BQ của tài liệu dài trong 20 giờ. Chỉ bổ sung biểu đồ khi nó giúp trả lời một trong chín câu hỏi trên.

## 3. Nguồn và đối soát ban đầu

Nguồn raw có sẵn: `data/cell2celltrain.csv`. Kiểm tra trực tiếp CSV cho thấy 51.047 dòng, 58 cột, 51.047 `CustomerID` khác nhau; target `Churn` có 14.711 `Yes` và 36.336 `No`. Dữ liệu dùng chuỗi `NA` cho một số giá trị thiếu.

| Cohort kiểm tra | Khách hàng | Churner | Churn rate |
|---|---:|---:|---:|
| Raw, target hợp lệ | 51.047 | 14.711 | 28,82% |
| Đủ dữ liệu ở 10 base feature | 50.679 | 14.503 | 28,62% |
| Đủ dữ liệu ở cả 58 cột | 49.752 | 14.245 | 28,63% |

Tập 49.752 của tài liệu hiện tại là complete-case trên **toàn bộ 58 cột**; không dùng nó làm baseline chung của demo. Có 368 dòng thiếu ít nhất một trong 10 feature, trong đó 208 churner. Do đó, loại mọi dòng thiếu ở 10 feature cũng cần được cân nhắc và công bố rõ.

## 4. Định nghĩa dữ liệu và mẫu số

- Đơn vị quan sát: một `CustomerID` trong một snapshot; không suy diễn xu hướng thời gian từ snapshot.
- Target: `Churn = Yes` là 1, `Churn = No` là 0; mọi giá trị khác là lỗi QA.
- Baseline Overview: số khách có ID và target hợp lệ sau kiểm tra nguồn, dự kiến 51.047; tính lại từ pipeline chứ không hard-code.
- Churn rate của bất kỳ chart/filter nào: churn count / số khách đủ điều kiện trong **cùng lát cắt**. Luôn hiển thị `n` và churn count; khi so sánh nhóm cần CI.
- Với chart theo một feature bị thiếu, loại missing khỏi phép so sánh theo band hoặc hiển thị nhóm `Unknown` riêng; không dùng mẫu số 51.047 để chia churn count của một nhóm nhỏ hơn.
- Các band dẫn xuất cần lưu công thức và ngưỡng. Không tối ưu ngưỡng trên tập cuối rồi báo hiệu quả trên chính tập đó.
- `MonthlyRevenue` là value proxy, không phải margin hoặc CLV.

## 5. Phạm vi feature và mô hình

Mô hình chính chỉ nhận: `MonthsInService`, `CurrentEquipmentDays`, `HandsetWebCapable`, `MonthlyRevenue`, `TotalRecurringCharge`, `CreditRating`, `MonthlyMinutes`, `PercChangeMinutes`, `PercChangeRevenues`, `PeakCallsInOut`.

`CustomerID` chỉ dùng để ghép kết quả. Các trường retention contact/offer và `ServiceArea` không vào mô hình. Missing được xử lý trong pipeline huấn luyện, học quy tắc từ train fold và áp dụng cho validation/holdout; báo số khách không thể chấm điểm nếu còn. Risk score, decile và lift để trình bày phải dựa trên dự đoán cho dòng chưa dùng fit model. Tối thiểu báo ROC-AUC, PR-AUC, log loss, calibration và lift@5/10/20%.

## 6. Pipeline rút gọn

`raw CSV (giữ nguyên) → kiểm tra/chuẩn hóa → bảng phân tích → EDA và mô hình → bảng phục vụ dashboard → web dashboard`. Code và artifact nằm trong `work/`; raw CSV ở `data/` tại root dự án.

Đây là **một pipeline chạy lại được**, không dựng ba tầng lưu trữ Medallion vật lý. Đầu ra tối thiểu: báo cáo QA, bảng phân tích, bảng score/segment, bảng policy và dữ liệu dashboard. Mỗi lần chạy ghi nguồn, số dòng đầu/cuối, quy tắc làm sạch và phiên bản model.

## 7. Nguyên tắc insight và chính sách

Mỗi insight trên dashboard nêu cohort, `n`, churn count/rate, độ bất định hoặc sensitivity khi so sánh, và một giới hạn diễn giải. Dùng nhãn `Observed`, `Supported`, `Hypothesis`, `Tested` đúng bằng chứng. Snapshot, correlation và SHAP không chứng minh nguyên nhân. Không khẳng định chính sách hiệu quả trước thử nghiệm treatment/control.

## 8. Ngân sách thời gian sau M0

| Công đoạn | Giờ dự kiến |
|---|---:|
| M0 — phạm vi, target, baseline và hợp đồng dữ liệu | 1,5 |
| Làm sạch và QA nguồn | 2,5 |
| EDA và biểu đồ insight | 3 |
| Mô hình và risk decile | 2,5 |
| Web dashboard bốn trang | 6 |
| Policy matrix và nội dung diễn giải | 2 |
| QA, README và tập demo | 2,5 |
| **Tổng** | **20** |

## 9. Điều kiện qua M0

- [x] Raw hiện diện và schema/target/ID đã được kiểm tra.
- [x] Baseline raw và hai cohort complete-case đã đối soát.
- [x] Chín câu hỏi, bốn trang dashboard và bộ 10 feature đã khóa.
- [x] Quy tắc mẫu số và giới hạn nhân quả đã định nghĩa.
- [x] Quyết định dùng một pipeline thay cho ba tầng vật lý đã ghi.

**Bước tiếp theo — M1:** viết pipeline làm sạch/QA có thể chạy lại và xuất báo cáo đối soát tự động. Các số trong M0 là kiểm tra ban đầu; M1 phải tái tạo chúng bằng code trước khi dashboard sử dụng.
