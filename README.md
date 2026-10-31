# Cell2Cell — Churn & Retention Intelligence

Web dashboard BI phục vụ demo đề tài: phân tích khách hàng viễn thông có khả năng rời bỏ, xếp hạng nhóm cần ưu tiên và đề xuất chính sách giữ chân để thử nghiệm. Trọng tâm là **trực quan hóa trả lời câu hỏi kinh doanh**. Nguồn là một snapshot quan sát; không có lịch sử can thiệp hoặc kết quả A/B test.

## Chạy bản demo

Yêu cầu Python 3.11+ và file `data/cell2celltrain.csv` trong thư mục dự án.

Cấu trúc hiện tại: `data/` giữ nguồn raw; `work/pipeline/` chứa ba notebook được đánh số và trình chạy tuần tự; `work/dashboard/` chứa Dash, kiểm tra giao diện, bộ xuất Pages, CSS và JavaScript; `work/build/` chứa artifact tái tạo được nên không đưa vào Git. Tài liệu demo và `progress.md` ở root.

```powershell
python -m pip install -r work/requirements.txt
python work/pipeline/run_all.py
python work/dashboard/verify.py
python work/dashboard/dashboard.py
```

Mở `http://127.0.0.1:8050/`. `run_all.py` chạy lần lượt ba notebook theo số thứ tự; bước 03 huấn luyện CatBoost và sinh score 3-fold ngoài mẫu nên có thể mất vài phút. Khi cập nhật nguồn hoặc notebook, chạy lại pipeline rồi khởi động lại dashboard.

### Chạy pipeline bằng notebook

Mở và chạy theo thứ tự:

1. `work/pipeline/01_data_preparation_and_eda.ipynb` — hợp đồng raw, chuẩn hóa, QA, EDA nguồn, band và processed layer.
2. `work/pipeline/02_analysis_and_visualization.ipynb` — phân tích risk/reach, biểu đồ, giải thích và kết luận cho từng nhóm câu hỏi.
3. `work/pipeline/03_model_training_and_evaluation.ipynb` — CatBoost OOF, đánh giá, capacity, P1–P4, ReasonCode và policy.

Mỗi notebook có cell import riêng, đường dẫn tương đối, giải thích từng bước, bảng kiểm tra và output đã thực thi. Notebook 02–03 đọc processed layer từ 01 bằng kernel mới; không phụ thuộc biến trong bộ nhớ. `preparation_manifest.json` xác nhận schema, số dòng và SHA256 của raw/processed/QA; dữ liệu thiếu hoặc đã thay đổi sẽ bị chặn với thông báo chạy lại 01.

`run_all.py` thực thi bằng Jupyter kernel mới cho từng notebook và lưu output thật vào file. Mặc định kernel chạy tại `work/pipeline/`; có thể kiểm tra từ project root:

```powershell
python work/pipeline/run_all.py --only 01 --cwd project
python work/pipeline/run_all.py --only 02
python work/pipeline/run_all.py --only 03
python work/pipeline/verify_notebooks.py
```

Chọn kernel `.venv` khi mở trong VS Code/Jupyter. `verify_notebooks.py` kiểm tra output đã lưu và thử các trường hợp thiếu manifest/processed, hash nguồn/QA/parquet thay đổi và manifest chưa PASS trong thư mục kiểm tra riêng.

## GitHub Pages sau khi kết nối repository

GitHub Pages chỉ phục vụ file tĩnh, không chạy Dash/Python trên server. Nguồn Pages nằm tại `work/dashboard/pages_src/`; lệnh sau xuất `site/` từ `work/build/` với bốn trang, bộ lọc một lựa chọn cho mỗi chiều, biểu đồ Plotly tương tác và policy matrix:

```powershell
python work/pipeline/run_all.py
python work/dashboard/verify.py
python work/dashboard/export_pages.py
python -m http.server 8765 --directory site
```

Mở `http://127.0.0.1:8765/` để xem trước. Workflow [`.github/workflows/pages.yml`](.github/workflows/pages.yml) tự chạy pipeline, kiểm tra, xuất site và deploy sau khi push lên **default branch** (`main` hoặc `master`), hoặc có thể chạy thủ công bằng Actions. Trên GitHub, vào **Settings → Pages → Build and deployment → Source: GitHub Actions**. Workflow cần Pages và Actions được bật; URL triển khai sẽ hiện trong job `deploy`.

Chỉ thư mục `site/` được upload thành Pages artifact. Nó chứa **dữ liệu từng khách ở mức band, score và target** để bộ lọc chạy trên trình duyệt, nhưng không chứa `CustomerID` hoặc giá trị doanh thu/phí chính xác. Đây vẫn là dữ liệu cấp dòng, không thể coi là đã ẩn danh hoàn toàn. Repository hiện đang track `data/cell2celltrain.csv` với `CustomerID`: nếu chọn repository public, chính CSV trong Git cũng public. Cần quyết định phạm vi công khai dữ liệu trước lần push đầu tiên. Không dùng Pages làm backend chấm điểm khách hàng mới.

## Bốn trang dashboard

1. **Overview:** baseline, số churner, quy mô nhóm, QA nguồn.
2. **Drivers:** churn và số khách theo tenure, thiết bị, revenue/phí và sử dụng.
3. **Risk & Segments:** score ngoài mẫu, ROC-AUC/PR-AUC, calibration, lift/capacity và P1–P4.
4. **Retention Strategy:** tín hiệu, quy mô, treatment hypothesis, KPI/guardrail và phép thử tối thiểu.

Bộ lọc chung gồm tenure, web capability, value tier và risk decile. Số liệu trên trang được tính theo lát cắt sau lọc. Các tỷ lệ churn khi so sánh nhóm thể hiện `n`, churn count và Wilson CI 95% trong hover của biểu đồ. Nút trên từng biểu đồ cho phép xuất PNG.

## Pipeline theo công đoạn

`01 raw/QA/processed → 02 phân tích/trực quan → 03 OOF model/segment/policy → dashboard`.

Raw không bị sửa. Ba notebook tạo các artifact tái lập trong `work/build/`:

| Artifact | Nội dung |
|---|---|
| `qa_report.json` | Số dòng, target, missing, duplicate, giá trị âm và giới hạn nguồn |
| `preparation_manifest.json` | Trạng thái PASS và hash xác nhận raw/processed/QA |
| `processed_customers.parquet` | Dữ liệu đã chuẩn hóa và band; đầu vào chung cho notebook 02–03 |
| `data_dictionary.csv` | Vai trò, dtype và missing của các cột processed |
| `eda_group_summary.csv` | Bảng risk/reach và Wilson CI dùng đối soát phân tích |
| `eda_insights.json` | Các insight chính của bước 02 |
| `customer_mart.parquet` | Một dòng/khách; feature, band, OOF risk score, decile, segment, reason code |
| `model_metrics.json` | Depth được chọn trong inner train, metric ngoài mẫu, lift@capacity |
| `policy_matrix.csv` | Điều kiện, treatment giả thuyết, KPI và guardrail |

`CustomerID` chỉ dùng để đối soát, không là predictor. Mô hình chỉ dùng 10 feature đã khóa ở [project_contract.md](project_contract.md). CatBoost xử lý missing ở numeric và categorical unknown; không loại 1.295 dòng để lấy complete-case toàn bộ 58 cột. Các giá trị âm bất thường được ghi trong QA và giữ nguyên ở bảng nguồn; band biểu đồ gắn nhãn `Giá trị âm` khi thích hợp.

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

- [project_contract.md](project_contract.md): phạm vi rút gọn và quyết định cohort.
- Tài liệu phiên bản cũ (`project_context (1).md`, `analysis_pipeline (1).md`, `timeline (1).xlsx`) đã chuyển ngoài repository vào `C:\Users\Admin\Documents\back`.
