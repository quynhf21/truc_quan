# Cell2Cell — Churn & Retention Intelligence

Web dashboard BI phục vụ demo đề tài: phân tích khách hàng viễn thông có khả năng rời bỏ, xếp hạng nhóm cần ưu tiên và đề xuất chính sách giữ chân để thử nghiệm. Trọng tâm là **trực quan hóa trả lời câu hỏi kinh doanh**. Nguồn là một snapshot quan sát; không có lịch sử can thiệp hoặc kết quả A/B test.

## Chạy bản demo

Yêu cầu Python 3.11+ và file `data/cell2celltrain.csv` trong thư mục dự án.

Cấu trúc hiện tại: `data/` giữ nguồn raw; `work/` chứa code, notebook tại `work/pipeline/`, tài nguyên giao diện và artifact sinh ra tại `work/build/`; tài liệu demo và `progress.md` ở root. `work/build/` là đầu ra tái tạo được nên không đưa vào Git.

```powershell
python -m pip install -r work/requirements.txt
python work/pipeline.py
python work/dashboard.py
```

Mở `http://127.0.0.1:8050/`. Lệnh pipeline đầu tiên huấn luyện CatBoost và sinh score 3-fold ngoài mẫu; trên máy thông thường có thể mất vài phút. Chạy `python work/pipeline.py --qa-only` nếu chỉ muốn kiểm tra nguồn. Khi cập nhật nguồn hoặc code pipeline, chạy lại pipeline rồi khởi động lại dashboard.

## Bốn trang dashboard

1. **Overview:** baseline, số churner, quy mô nhóm, QA nguồn.
2. **Drivers:** churn và số khách theo tenure, thiết bị, revenue/phí và sử dụng.
3. **Risk & Segments:** score ngoài mẫu, ROC-AUC/PR-AUC, calibration, lift/capacity và P1–P4.
4. **Retention Strategy:** tín hiệu, quy mô, treatment hypothesis, KPI/guardrail và phép thử tối thiểu.

Bộ lọc chung gồm tenure, web capability, value tier và risk decile. Số liệu trên trang được tính theo lát cắt sau lọc. Các tỷ lệ churn khi so sánh nhóm thể hiện `n`, churn count và Wilson CI 95% trong hover của biểu đồ. Nút trên từng biểu đồ cho phép xuất PNG.

## Pipeline một luồng

`raw CSV → QA/chuẩn hóa → bands phân tích → chọn mô hình trong train fold → OOF score → customer mart → dashboard`.

Raw không bị sửa. `work/pipeline.py` tạo bốn artifact trong `work/build/`:

| Artifact | Nội dung |
|---|---|
| `qa_report.json` | Số dòng, target, missing, duplicate, giá trị âm và giới hạn nguồn |
| `customer_mart.parquet` | Một dòng/khách; feature, band, OOF risk score, decile, segment, reason code |
| `model_metrics.json` | Depth được chọn trong inner train, metric ngoài mẫu, lift@capacity |
| `policy_matrix.csv` | Điều kiện, treatment giả thuyết, KPI và guardrail |

`CustomerID` chỉ dùng để đối soát, không là predictor. Mô hình chỉ dùng 10 feature đã khóa ở [M0_project_contract.md](M0_project_contract.md). CatBoost xử lý missing ở numeric và categorical unknown; không loại 1.295 dòng để lấy complete-case toàn bộ 58 cột. Các giá trị âm bất thường được ghi trong QA và giữ nguyên ở bảng nguồn; band biểu đồ gắn nhãn `Giá trị âm` khi thích hợp.

### Mẫu số và benchmark

Nguồn hiện tại có 51.047 khách, 14.711 churner (28,82%). Con số 49.752 trong tài liệu gốc là complete-case trên 58 cột và chỉ được dùng làm đối chiếu. Tỷ lệ của mỗi band/filter luôn lấy churn count chia cho số khách đủ điều kiện trong cùng band/filter. Mọi con số nguồn được pipeline tính lại khi chạy.

### Cách mô hình được đánh giá

Ba outer folds tạo dự đoán ngoài mẫu cho toàn bộ khách hàng. Trong **từng outer training fold**, dữ liệu được chia tiếp để chọn depth 4/6 và số vòng theo inner validation log loss; model sau đó fit lại trên outer train và dự đoán outer holdout. Vì vậy nhãn của outer holdout không được dùng để chọn mô hình. Dashboard dùng đúng OOF score này cho ROC-AUC, PR-AUC, log loss, calibration, decile và gain. Khi lọc, ROC-AUC/PR-AUC mô tả lát cắt sau lọc; log loss trong KPI giữ giá trị toàn nguồn và được ghi nhãn tương ứng.

## Kịch bản trình bày 5–7 phút

1. **Overview:** chốt baseline, cho thấy raw và complete-case khác nhau.
2. **Drivers:** so sánh tenure và thiết bị; chỉ rõ risk phải đi cùng reach. Tiếp đến value/phí và thay đổi sử dụng.
3. **Risk & Segments:** xem model phân tầng ra sao, sau đó chọn capacity 5/10/20% và nhóm P1–P4.
4. **Retention Strategy:** chọn một reason code, đọc eligibility, treatment, KPI và guardrail; kết thúc bằng kế hoạch treatment/control.

## Giới hạn cần nói trong demo

- Dữ liệu là snapshot: tenure band không phải chuỗi thời gian, correlation và SHAP không chứng minh nguyên nhân.
- Đơn vị và thời điểm sẵn có của `PercChangeMinutes`/`PercChangeRevenues` chưa được metadata nguồn xác nhận. Dashboard gọi chúng là mức thay đổi theo dữ liệu nguồn, không tự ghi là %.
- `ReasonCode` là rule để đề xuất rà soát, không phải đóng góp SHAP hay nguyên nhân của score; thứ tự ưu tiên rule có thể che tín hiệu chồng lắp.
- `MonthlyRevenue` là proxy giá trị, không phải margin hoặc CLV. Chưa có cost và uplift nên không báo ROI.
- Chính sách là hypothesis. Muốn khẳng định hiệu quả phải có nhóm treatment/control, outcome window và guardrail được khóa trước.
- `CreditRating` không được dùng một mình để áp giá bất lợi hoặc loại khách khỏi hỗ trợ.
- Demo chạy local trên máy người trình bày. Không công khai dữ liệu khách hàng hoặc host web ra Internet.

## Tài liệu

- [M0_project_contract.md](M0_project_contract.md): phạm vi rút gọn và quyết định cohort.
- Tài liệu phiên bản cũ (`project_context (1).md`, `analysis_pipeline (1).md`) đã chuyển ngoài repository vào `C:\Users\Admin\Documents\back`. `timeline (1).xlsx` có bản sao cùng kích thước ở đó; file gốc đang bị Excel khóa và sẽ được chuyển sau khi đóng workbook.
