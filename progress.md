# Tiến độ dự án Cell2Cell Churn & Retention

Cập nhật lần cuối: **30/10/2026 (Asia/Bangkok)**. Đây là nhật ký trạng thái của bản demo rút gọn trong `M0_project_contract.md`. Cập nhật file này ngay khi hoàn thành một mốc hoặc khi xuất hiện/tháo gỡ điểm chặn; không đánh dấu `DONE` chỉ vì đã viết xong code mà chưa kiểm tra đầu ra.

## Quy ước trạng thái

- `PENDING`: chưa bắt đầu hoặc còn việc trong phạm vi mốc.
- `IN PROGRESS`: đang triển khai, chưa qua tiêu chí hoàn thành.
- `BLOCKED`: không thể tiếp tục vì thiếu đầu vào/quyết định từ bên ngoài; ghi rõ điều kiện gỡ chặn.
- `DONE`: đã có artifact và kiểm tra tương ứng.

## Tổng quan hiện tại

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Bản demo local M0–M6 | **DONE** | Pipeline, dashboard, tài liệu và kiểm tra đã hoàn thành. |
| Git local | **DONE** | Repository đã init; commit đầu `242a873`; chưa cấu hình remote. |
| Dọn file phiên bản cũ | **DONE** | Ba file cũ nằm tại `C:\Users\Admin\Documents\back`; root dự án không còn timeline. |
| Triển khai công khai | **PENDING** | Chưa nằm trong phạm vi demo; hiện chạy trên máy local. |
| Sử dụng để chạy campaign thật | **BLOCKED** | Cần xác minh timing/đơn vị feature, dữ liệu chi phí và thiết kế pilot được phê duyệt. |

## Các mốc thực hiện

| Mốc | Trạng thái | Kết quả và bằng chứng |
|---|---|---|
| **M0 — Khóa phạm vi và hợp đồng dữ liệu** | **DONE** | `M0_project_contract.md`; raw 51.047 dòng/58 cột, target và hai cohort complete-case đã đối soát; khóa 9 câu hỏi và 4 trang. |
| **M1 — Làm sạch và QA nguồn** | **DONE** | `pipeline.py` đọc raw, chuẩn hóa `NA`/target/category, kiểm tra ID, missing, giá trị âm; `build/qa_report.json` tái tạo 51.047 khách và 14.711 churner. |
| **M2 — EDA và insight trực quan** | **DONE** | Band tenure, thiết bị, value/phí, usage và mức thay đổi; biểu đồ risk/reach trong trang Drivers; `INSIGHTS_AND_POLICY.md` ghi bằng chứng và giới hạn. |
| **M3 — Mô hình và risk decile** | **DONE** | CatBoost dùng đúng 10 feature; chọn depth trong train của từng outer fold; OOF score cho 51.047 khách trong `build/customer_mart.parquet`; ROC-AUC 0,6715 và lift@10% 1,88× trong `build/model_metrics.json`/`MODEL_CARD.md`. |
| **M4 — Web dashboard BI** | **DONE** | `dashboard.py` và `assets/style.css`: Overview, Drivers, Risk & Segments, Retention Strategy; bộ lọc chung, reset, bảng capacity và diễn giải; kiểm tra trực tiếp trên browser local. |
| **M5 — Chính sách giữ chân** | **DONE** | `build/policy_matrix.csv` và trang Strategy: ba hướng ưu tiên pilot, nhóm plan review để khám phá thêm, fallback; có KPI, guardrail và khung treatment/control. |
| **M6 — Đối soát, tài liệu và demo readiness** | **DONE** | `verify.py` pass đối soát nguồn/score/segment/policy và render bốn route, kể cả lát cắt sau lọc; HTTP local trả 200; `README.md` có lệnh chạy và kịch bản demo. |

## Block và pending

**Không có block đang ngăn bản demo local.** Những việc sau nằm ngoài điều kiện hoàn thành M0–M6:

| Loại | Việc còn chờ | Điều kiện xử lý |
|---|---|---|
| `BLOCKED` cho vận hành thật | Xác nhận đơn vị và thời điểm sẵn có của `PercChangeMinutes`, `PercChangeRevenues` và các predictor khác | Có metadata/source owner và mốc scoring rõ ràng. |
| `BLOCKED` cho đánh giá chính sách | Chưa có treatment/control, outcome window, contact/offer cost, margin/CLV và uplift | Thiết kế pilot, thu thập dữ liệu và phê duyệt KPI/guardrail. |
| `PENDING` tùy chọn | Deploy dashboard, phân quyền và bảo vệ dữ liệu khách hàng | Chỉ thực hiện nếu có yêu cầu host bên ngoài và phương án truy cập dữ liệu phù hợp. |
| `PENDING` tùy chọn | Kiểm định theo thời gian, fairness và drift trước sử dụng thật | Cần snapshot mới và định nghĩa kiểm tra vận hành. |

## Nhật ký cập nhật

| Ngày (Asia/Bangkok) | Mốc | Thay đổi trạng thái | Ghi chú |
|---|---|---|---|
| 29/10/2026 | M0 | `PENDING` → `DONE` | Khóa scope 20 giờ và quyết định dùng một pipeline thay cho ba tầng vật lý. |
| 30/10/2026 | M1–M3 | `PENDING` → `DONE` | QA raw, EDA, nested 3-fold OOF scoring và artifact dữ liệu. |
| 30/10/2026 | M4–M6 | `PENDING` → `DONE` | Dashboard bốn trang, policy matrix, tài liệu và kiểm tra tự động/giao diện. |
| 30/10/2026 | Sắp xếp & Git | `PENDING` → `DONE` cho code/Git; `BLOCKED` cho timeline | Code vào `work/`, notebook vào `work/pipeline/`, hai tài liệu cũ vào `Documents/back`; Git commit đầu `242a873`, chưa có remote. Timeline gốc bị Excel khóa. |
| 30/10/2026 | Kho phiên bản cũ | `BLOCKED` → `DONE` | Xác minh `Documents/back` có đủ ba file và root dự án không còn timeline/file khóa tạm. |

### Mẫu ghi cho mốc tiếp theo

Khi có mốc mới, thêm một dòng vào bảng mốc và nhật ký: **ngày, trạng thái trước → sau, artifact, kiểm tra đã chạy, block/pending còn lại, người hoặc đầu vào cần để gỡ block**. Giữ số liệu và trạng thái nhất quán với artifact thực tế.
