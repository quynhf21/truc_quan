# Hướng dẫn thuyết trình dự án Cell2Cell Churn & Retention

## 1. Dự án này đang làm gì?

Đây là đề tài **trực quan hóa và phân tích nguy cơ khách hàng viễn thông rời bỏ dịch vụ — Customer Churn** trên bộ dữ liệu Cell2Cell.

Câu hỏi điều hành của dự án là:

> Khách hàng nào có nguy cơ rời bỏ cao, những tín hiệu nào liên quan đến churn, và doanh nghiệp nên ưu tiên thử chính sách giữ chân nào?

Dự án không dừng ở việc vẽ biểu đồ. Nó tạo một chuỗi phân tích hoàn chỉnh:

```text
CSV gốc
  → kiểm tra chất lượng dữ liệu
  → tạo các nhóm phân tích
  → khám phá các yếu tố liên quan churn
  → huấn luyện mô hình CatBoost
  → chấm RiskScore ngoài mẫu
  → chia risk decile và P1–P4
  → dashboard tương tác
  → đề xuất phép thử giữ chân
```

Sản phẩm cuối gồm:

- Dashboard Dash/Python chạy local.
- Dashboard tĩnh chạy trên GitHub Pages.
- Mô hình xếp hạng rủi ro churn.
- Ma trận chính sách giữ chân.
- Notebook, model card và tài liệu giải thích kết quả.

---

## 2. Các công đoạn của dự án

### M0 — Xác định phạm vi

Dự án khóa trước:

- Đơn vị quan sát: một khách hàng tại một thời điểm snapshot.
- Target: `Churn = Yes/No`.
- Chín câu hỏi kinh doanh.
- Mười biến đầu vào cho mô hình.
- Bốn trang dashboard.
- Các giới hạn diễn giải.

Phần này nằm trong `project_contract.md`.

### M1 — Đọc, chuẩn hóa và kiểm tra dữ liệu

Nguồn có:

- 51.047 khách hàng.
- 58 cột.
- 51.047 `CustomerID` duy nhất.
- 14.711 churner.
- Không có ID thiếu, ID trùng hay target không hợp lệ.

Pipeline xử lý `NA`, ép kiểu số, chuẩn hóa biến phân loại và thống kê missing/giá trị âm. Dữ liệu raw không bị sửa.

### M2 — Tạo nhóm để trực quan hóa

Các biến liên tục được chia thành nhóm dễ đọc:

- Tenure: 6–11, 12–18, 19–24 và 25+ tháng.
- Tuổi thiết bị: ≤180, 181–365, 366–730 và >730 ngày.
- Doanh thu: thấp, trung bình, cao.
- Phí định kỳ.
- Mức sử dụng.
- Xu hướng tăng/giảm sử dụng.

Mục đích của band không phải tăng độ chính xác mô hình, mà là làm biểu đồ dễ giải thích.

### M3 — Huấn luyện và đánh giá mô hình

CatBoost sử dụng đúng 10 biến:

1. `MonthsInService`
2. `CurrentEquipmentDays`
3. `HandsetWebCapable`
4. `MonthlyRevenue`
5. `TotalRecurringCharge`
6. `CreditRating`
7. `MonthlyMinutes`
8. `PercChangeMinutes`
9. `PercChangeRevenues`
10. `PeakCallsInOut`

`CustomerID` không được dùng để dự đoán.

Mô hình tạo điểm bằng **3-fold out-of-fold**: mỗi khách được dự đoán bởi một mô hình không dùng chính khách đó để huấn luyện. Nhờ vậy các chỉ số trên dashboard ít bị “ảo” hơn so với đánh giá trên chính tập train.

### M4 — Tạo customer mart và phân khúc

Mỗi khách được bổ sung:

- `RiskScore`: xác suất/ranking churn.
- `RiskDecile`: nhóm 1–10, trong đó 10 rủi ro cao nhất.
- `PrioritySegment`: P1–P4.
- `ReasonCode`: tín hiệu vận hành để rà soát.
- Các band phục vụ biểu đồ.

### M5 — Xây dashboard

Bốn trang tạo thành một câu chuyện:

1. **Overview:** vấn đề lớn đến đâu?
2. **Drivers:** tín hiệu nào đi cùng churn?
3. **Risk & Segments:** ai cần được ưu tiên?
4. **Retention Strategy:** nên thử hành động gì?

### M6–M7 — Kiểm tra và xuất bản

- `work/dashboard/verify.py` đối soát nguồn, score, phân khúc và bốn route.
- `work/dashboard/export_pages.py` tạo bản tĩnh.
- JavaScript tính lại biểu đồ khi lọc.
- GitHub Actions có thể build và deploy lên Pages.

---

## 3. Giải thích code từng phần

### 3.1. Pipeline phân tích — `work/pipeline/`

Pipeline được chia thành ba notebook có phụ thuộc một chiều:

#### `01_data_preparation_and_eda.ipynb`

- Đọc CSV và kiểm tra hợp đồng schema, ID, target.
- Chuyển `Yes → 1`, `No → 0`, ép kiểu numeric và chuẩn hóa categorical.
- Thống kê missing, complete-case, giá trị âm và phân bố target.
- Tạo `TenureBand`, `EquipmentAgeBand`, `ValueTier`, `ChargeBand`, `MinutesBand`, `UsageTrendBand`, `RevenueTrendBand`.
- Xuất `processed_customers.parquet`, `qa_report.json` và `data_dictionary.csv`.

#### `02_analysis_and_visualization.ipynb`

- Chỉ đọc processed layer từ bước 01, không làm sạch lại.
- Tính risk, reach và Wilson CI 95% theo tenure, thiết bị, web capability, value/phí và usage.
- Vẽ các cặp biểu đồ tỷ lệ churn – quy mô nhóm.
- Sau mỗi nhóm biểu đồ có cell Markdown giải thích và kết luận.
- Xuất `eda_group_summary.csv` và `eda_insights.json` để đối soát.

#### `03_model_training_and_evaluation.ipynb`

- Dùng đúng 10 feature gốc; band không đi vào mô hình.
- Inner validation chọn depth 4/6 và số vòng trong từng outer training fold.
- Outer 3-fold tạo OOF score cho toàn bộ 51.047 khách.
- Đánh giá ROC-AUC, PR-AUC, log loss, Brier, decile, gain, calibration và capacity.
- Tạo P1–P4, ReasonCode và policy matrix.
- Xuất `customer_mart.parquet`, `model_metrics.json` và `policy_matrix.csv`.

`work/pipeline/run_all.py` chỉ chạy ba notebook theo thứ tự; nó không chứa logic xử lý dữ liệu hay mô hình hóa. Mỗi notebook có checkpoint bằng `assert` và dừng ngay tại công đoạn sai lệch.

### 3.2. Dashboard Dash/Python — `work/dashboard/dashboard.py`

Dashboard chỉ đọc artifact đã sinh, không huấn luyện lại mô hình.

#### Đọc dữ liệu — dòng 16–24

Chương trình nạp:

- Customer mart.
- Báo cáo QA.
- Model metrics.
- Policy matrix.

Nếu chưa có mart, chương trình yêu cầu chạy pipeline trước.

#### Tính khoảng tin cậy — hàm `wilson()`, dòng 44–50

Hàm tính Wilson 95% CI cho churn rate.

Ý nghĩa: hai cột có tỷ lệ khác nhau chưa chắc khác nhau đáng tin cậy nếu mẫu quá nhỏ. Error bar giúp người xem thấy độ bất định.

#### Các hàm dựng biểu đồ chung — dòng 88–138

- `group_comparison()`: so sánh hai nhóm và tạo câu nhận xét.
- `group_metrics()`: tính `n`, số churner, churn rate và CI.
- `rate_chart()`: biểu đồ tỷ lệ churn.
- `volume_chart()`: biểu đồ quy mô.
- `make_table()`: tạo bảng HTML.

Thiết kế luôn đặt **risk cạnh reach**:

- Risk: tỷ lệ churn cao thế nào?
- Reach: nhóm đó có bao nhiêu khách?

Đây là một nguyên tắc trực quan hóa quan trọng: không ưu tiên một nhóm chỉ vì tỷ lệ cao nếu nhóm đó quá nhỏ.

#### Trang Overview — hàm `overview()`, dòng 141–174

Trang này trả lời:

- Có bao nhiêu khách?
- Có bao nhiêu churner?
- Baseline churn là bao nhiêu?
- Nhóm top 20% risk lớn thế nào?
- Churn khác nhau ra sao theo tenure?
- Chất lượng dữ liệu nguồn thế nào?

#### Trang Drivers — hàm `drivers()`, dòng 177–202

Trang này vẽ churn và quy mô theo:

- Tenure.
- Tuổi thiết bị.
- Web capability.
- Value tier.
- Recurring charge.
- Monthly minutes.
- Xu hướng thay đổi minutes.

#### Trang Risk & Segments — hàm `risk()`, dòng 205–264

Trang này gồm:

- ROC-AUC và PR-AUC.
- Churn rate theo risk decile.
- Cumulative gain.
- Calibration.
- Capacity 5%, 10%, 20%.
- Phân khúc P1–P4.

#### Trang Retention Strategy — hàm `strategy()`, dòng 267–295

Trang này nối phân tích với hành động:

- Thống kê ReasonCode.
- Xác định khách đủ điều kiện trong decile ≥7.
- Hiển thị treatment giả thuyết.
- Hiển thị KPI chính.
- Hiển thị guardrail.
- Đề xuất thiết kế treatment/control.

#### Layout và callback — dòng 299–346

Layout tạo sidebar, bốn route và bốn bộ lọc:

- Tenure.
- Web capability.
- Value tier.
- Risk decile.

Callback `render_page()`:

1. Nhận route và bộ lọc.
2. Lọc dataframe.
3. Kiểm tra lát cắt có dữ liệu hay không.
4. Gọi hàm trang tương ứng.
5. Tính lại KPI và biểu đồ theo mẫu số sau lọc.

Vì vậy khi lọc, churn rate không dùng mẫu số 51.047 nữa mà dùng số khách còn lại trong lát cắt.

### 3.3. Giao diện — `work/dashboard/assets/style.css`

CSS chịu trách nhiệm:

- Bố cục sidebar, topbar và panel.
- KPI card, bảng và policy card.
- Màu xanh dương cho risk.
- Teal cho quy mô/tín hiệu.
- Đỏ cho churner hoặc cảnh báo.
- Responsive cho màn hình nhỏ.

### 3.4. Bản GitHub Pages

GitHub Pages không chạy được Python/Dash, nên dự án có bản tĩnh riêng.

#### `work/dashboard/export_pages.py`

Hàm `build_site()`:

- Đọc customer mart.
- Kiểm tra ID không trùng.
- Loại `CustomerID` khỏi dữ liệu xuất bản.
- Mã hóa các nhãn bằng dictionary để giảm dung lượng.
- Xuất `data.json`, HTML, CSS, JavaScript và Plotly.
- Kiểm tra số dòng và số churner khớp QA.
- Kiểm tra không có chuỗi `CustomerID` trong dữ liệu publish.

#### `work/dashboard/pages_src/index.html`

Đây là bộ khung HTML của bản tĩnh:

- Sidebar bốn trang.
- Bốn bộ lọc.
- Vùng `content` để JavaScript render dashboard.
- Nạp Plotly, CSS và `app.js`.

#### `work/dashboard/pages_src/app.js`

JavaScript thực hiện trực tiếp trên trình duyệt:

- Tải `data.json`.
- Lọc các dòng.
- Group dữ liệu.
- Tính churn rate và Wilson CI.
- Tính capacity, gain và calibration.
- Vẽ Plotly.
- Render bốn trang.
- Xử lý điều hướng và nút reset.

Bản Dash cho phép multi-select, còn bản tĩnh hiện dùng một lựa chọn trên mỗi chiều.

### 3.5. Kiểm tra tự động — `work/dashboard/verify.py`

File này kiểm tra:

- Đúng 51.047 dòng và 14.711 churner.
- ID duy nhất.
- Có đủ ba fold.
- RiskScore nằm trong `[0,1]` và không missing.
- Có đủ decile 1–10.
- P1–P4 phủ toàn bộ dữ liệu.
- Metric trong JSON khớp mart.
- ReasonCode được policy matrix bao phủ.
- Bốn trang render được cả toàn nguồn lẫn sau lọc.

### 3.6. Thứ tự chạy notebook

1. `01_data_preparation_and_eda.ipynb`: tạo processed layer và QA.
2. `02_analysis_and_visualization.ipynb`: đọc processed layer, vẽ biểu đồ và đưa ra kết luận.
3. `03_model_training_and_evaluation.ipynb`: đọc processed layer, huấn luyện, đánh giá và tạo artifact dashboard.

Ba notebook không gọi lẫn code cell của nhau; chúng giao tiếp qua artifact trong `work/build/`. Có thể chạy tự động toàn bộ bằng `python work/pipeline/run_all.py`.

---

## 4. Trả lời chín câu hỏi trọng tâm

### Q1. Dữ liệu và mẫu số phân tích có đáng tin không?

Đủ tin cậy cho demo học thuật:

- 51.047 ID duy nhất.
- Không có target sai.
- Không có ID thiếu hoặc trùng.
- Baseline đối soát được.

Tuy nhiên:

- 368 khách thiếu ít nhất một predictor.
- Chỉ 49.752 khách đầy đủ cả 58 cột.
- Một số trường có giá trị âm.
- Đơn vị và thời điểm sẵn có của `PercChange*` chưa được xác minh.

Vì vậy dữ liệu phù hợp cho phân tích quan sát, chưa đủ điều kiện triển khai vận hành thật.

### Q2. Churn lớn đến đâu và nhóm nào đóng góp nhiều churner?

- 14.711/51.047 khách churn.
- Tỷ lệ churn: **28,82%**.

Theo tenure, nhóm 12–18 tháng vừa có tỷ lệ cao nhất, vừa đóng góp nhiều churner nhất:

- 4.865/14.654 = **33,20%**.

Đây là cửa sổ đáng chú ý, nhưng chưa thể nói “đến tháng 12 khách bắt đầu churn” vì dữ liệu không phải chuỗi thời gian.

### Q3. Risk khác nhau thế nào theo tenure?

| Tenure | Khách | Churner | Tỷ lệ churn |
|---|---:|---:|---:|
| 6–11 tháng | 14.238 | 3.421 | 24,03% |
| 12–18 tháng | 14.654 | 4.865 | 33,20% |
| 19–24 tháng | 9.505 | 2.825 | 29,72% |
| 25+ tháng | 12.650 | 3.600 | 28,46% |

Nhóm 12–18 tháng cao hơn nhóm 6–11 tháng khoảng **9,2 điểm phần trăm**.

### Q4. Tuổi và khả năng thiết bị liên quan thế nào đến churn?

Tuổi thiết bị:

- >730 ngày: 1.855/5.141 = **36,08%** churn.
- ≤180 ngày: 2.238/9.759 = **22,93%** churn.

Web capability:

- Không web-capable: 1.868/5.001 = **37,35%**.
- Có web-capable: 12.843/46.046 = **27,89%**.

Thiết bị cũ hoặc không hỗ trợ web là tín hiệu có cả risk và quy mô đủ lớn để cân nhắc pilot. Đây vẫn là liên hệ quan sát, chưa chứng minh nâng cấp thiết bị sẽ trực tiếp làm giảm churn.

### Q5. Revenue và phí liên quan thế nào đến risk/value?

Value tier:

| Value tier | Tỷ lệ churn |
|---|---:|
| Thấp | 30,99% |
| Trung bình | 27,84% |
| Cao | 27,91% |

Recurring charge:

| Charge | Tỷ lệ churn |
|---|---:|
| ≤30 | 33,51% |
| 30–60 | 27,94% |
| >60 | 24,03% |

Không được kết luận “tăng phí làm giảm churn”. Các nhóm phí có thể khác nhau về gói cước, mức sử dụng, tenure và đặc điểm khách hàng.

`MonthlyRevenue` chỉ là proxy cho giá trị khách hàng, không phải lợi nhuận hay CLV.

### Q6. Mức và thay đổi sử dụng có nhận diện disengagement không?

Mức sử dụng:

- ≤150 phút: 4.044/12.214 = **33,11%** churn.
- >500 phút: 5.132/19.452 = **26,38%**.

Thay đổi sử dụng:

- Giảm mạnh: 4.090/12.728 = **32,13%**.
- Tăng nhẹ: 2.572/10.178 = **25,27%**.

Điều này hỗ trợ giả thuyết rằng sử dụng thấp hoặc giảm mạnh là tín hiệu disengagement.

Tuy nhiên, 367 khách thiếu `PercChangeMinutes` có churn cao; missing phải được hiển thị riêng và không được âm thầm loại bỏ. Đơn vị của biến thay đổi cũng chưa được xác minh, nên không tự gọi nó là phần trăm.

### Q7. Mô hình xếp hạng risk đáng tin và hữu ích đến đâu?

Kết quả ngoài mẫu:

| Metric | Giá trị |
|---|---:|
| ROC-AUC | 0,6715 |
| PR-AUC | 0,4524 |
| Log loss | 0,5609 |
| Brier score | 0,1891 |
| Depth được chọn | 6/6/6 fold |

Diễn giải:

- ROC-AUC 0,6715: khả năng xếp hạng ở mức vừa phải, tốt hơn ngẫu nhiên nhưng chưa phải mô hình rất mạnh.
- PR-AUC 0,4524 cao hơn baseline churn 0,2882.
- Decile 1 có churn 10,15%, decile 10 có 54,22%.
- Mô hình phân tầng risk khá rõ và hữu ích để ưu tiên nguồn lực.
- Không nên dùng làm quyết định tự động với từng cá nhân.

Churn rate theo decile:

| Decile | Tỷ lệ churn |
|---:|---:|
| 1 | 10,15% |
| 2 | 15,46% |
| 3 | 19,67% |
| 4 | 22,75% |
| 5 | 26,29% |
| 6 | 30,11% |
| 7 | 32,11% |
| 8 | 35,32% |
| 9 | 42,12% |
| 10 | 54,22% |

### Q8. Với capacity hữu hạn, nên ưu tiên phân khúc nào?

| Capacity | Khách | Churner quá khứ | Precision | Recall | Lift |
|---:|---:|---:|---:|---:|---:|
| 5% | 2.553 | 1.558 | 61,0% | 10,6% | 2,12× |
| 10% | 5.105 | 2.768 | 54,2% | 18,8% | 1,88× |
| 20% | 10.210 | 4.918 | 48,2% | 33,4% | 1,67× |

Nếu chỉ liên hệ 10% khách có score cao nhất, nhóm đó chứa 18,8% churner quá khứ và có churn rate gần gấp 1,88 lần baseline.

Các phân khúc:

| Nhóm | Khách | Churner | Churn rate |
|---|---:|---:|---:|
| P1 — risk cao/value cao | 2.444 | 1.127 | 46,11% |
| P2 — risk cao | 7.766 | 3.791 | 48,82% |
| P3 — value cao/risk khá | 2.022 | 677 | 33,48% |
| P4 — theo dõi | 38.815 | 9.116 | 23,49% |

- Nếu mục tiêu là bảo vệ khách giá trị cao: ưu tiên P1.
- Nếu mục tiêu là tiếp cận nhiều churner nhất: ưu tiên top risk/P1–P2.
- P3 phù hợp khi còn thêm capacity.
- P4 chủ yếu theo dõi.

### Q9. Nên thử chính sách nào, đo bằng KPI và guardrail nào?

Ba hướng ưu tiên:

1. **Thiết bị cần rà soát:** tư vấn, hướng dẫn hoặc upgrade pilot.
2. **Sử dụng suy giảm:** re-engagement hoặc plan review.
3. **Giai đoạn vòng đời:** check-in trong nhóm 12–18 tháng.

Các nhóm `RiskDecile ≥7` hiện có quy mô:

| ReasonCode | Khách đủ điều kiện | Churn rate quan sát |
|---|---:|---:|
| Thiết bị cần rà soát | 5.638 | 40,00% |
| Sử dụng suy giảm | 5.467 | 43,17% |
| Giai đoạn vòng đời | 4.469 | 38,98% |
| Gói cước cần rà soát | 96 | 52,08% |
| Rà soát chung | 4.749 | 41,12% |

Gói cước chỉ nên khám phá thêm vì reason group nhỏ và phụ thuộc thứ tự rule.

Để chứng minh chính sách hiệu quả phải:

- Randomize treatment/control trong cùng eligibility.
- Khóa outcome window trước khi chạy.
- Đo incremental retention, không chỉ retention thô.
- Theo dõi chi phí, opt-out, contact fatigue, khiếu nại và revenue dilution.

---

## 5. Ý nghĩa các biểu đồ và metric

### Churn rate

```text
Churn rate = Số khách Churn = Yes / Tổng khách trong cùng lát cắt
```

Khi thay đổi bộ lọc, cả tử số và mẫu số đều được tính lại.

### Wilson confidence interval

Khoảng tin cậy 95% cho tỷ lệ churn. Nó giúp thể hiện độ bất định, đặc biệt khi một nhóm có ít khách.

### ROC-AUC

Xác suất mô hình xếp một churner ngẫu nhiên cao hơn một non-churner ngẫu nhiên. AUC 0,5 tương đương ngẫu nhiên; AUC 1 là phân biệt hoàn hảo.

### PR-AUC

Tóm tắt quan hệ precision–recall, phù hợp khi lớp churn không chiếm đa số. Baseline PR gần bằng tỷ lệ churn 28,82%.

### Log loss

Phạt mạnh những dự đoán xác suất sai nhưng quá tự tin. Thấp hơn là tốt hơn.

### Brier score

Sai số bình phương trung bình giữa xác suất dự đoán và nhãn thật. Thấp hơn là tốt hơn.

### Calibration

So sánh xác suất dự đoán trung bình với tỷ lệ churn thực tế. Nếu nhóm được dự đoán 40% có khoảng 40% churn thì score được xem là hiệu chỉnh tốt tại vùng đó.

### Cumulative gain

Cho biết khi liên hệ một tỷ lệ khách nhất định, có thể tiếp cận bao nhiêu phần trăm churner quá khứ.

### Precision

```text
Precision = Churner trong nhóm được chọn / Tổng khách được chọn
```

### Recall

```text
Recall = Churner trong nhóm được chọn / Tổng churner toàn cohort
```

### Lift

```text
Lift = Churn rate của nhóm được chọn / Churn rate baseline
```

Lift 1,88× nghĩa là nhóm được chọn có tỷ lệ churn bằng 1,88 lần baseline.

---

## 6. Kịch bản thuyết trình 5–7 phút

### Phút 1 — Bài toán và dữ liệu

> Đề tài phân tích 51.047 khách hàng viễn thông để xác định churn đang lớn đến đâu, tín hiệu nào liên quan và nên ưu tiên khách nào. Baseline churn là 28,82%.

Giới thiệu bốn câu hỏi lớn:

1. Vấn đề lớn đến đâu?
2. Tín hiệu nào đi cùng churn?
3. Ai nên được ưu tiên?
4. Chính sách nào đáng thử?

### Phút 2 — Thiết kế trực quan

> Các biểu đồ tỷ lệ luôn được đặt cạnh biểu đồ quy mô. Tỷ lệ cao nhưng nhóm quá nhỏ có thể không đáng ưu tiên. Error bar là Wilson CI 95%, giúp thể hiện độ bất định.

Trình bày bộ lọc chung và giải thích rằng mọi KPI được tính lại theo lát cắt sau lọc.

### Phút 3 — Drivers

Nêu ba insight:

- 12–18 tháng: 33,20%.
- Thiết bị >730 ngày: 36,08%.
- Sử dụng giảm mạnh: 32,13%.

Nhấn mạnh:

> Đây là liên hệ quan sát, không phải quan hệ nhân quả.

### Phút 4 — Mô hình

> Mô hình CatBoost dùng 10 biến và được đánh giá bằng dự đoán 3-fold ngoài mẫu. ROC-AUC là 0,6715. Decile cao nhất có churn 54,22%, so với 10,15% ở decile thấp nhất.

Giải thích score được dùng để xếp hạng, không dùng ngưỡng 0,5 một cách máy móc.

### Phút 5 — Capacity và phân khúc

> Nếu chỉ có thể liên hệ 10% khách, mô hình giúp tiếp cận 18,8% churner quá khứ, với lift 1,88 lần. Nhóm P1 bảo vệ khách value cao; P2 tập trung risk cao.

### Phút 6 — Chính sách và giới hạn

> Dashboard không tuyên bố chính sách nào đã hiệu quả. Nó chỉ đề xuất device review, usage re-engagement và lifecycle check-in để thử bằng treatment/control.

Kết thúc bằng:

> Giá trị của dự án không phải dự đoán hoàn hảo từng cá nhân, mà là biến dữ liệu thành một quy trình ưu tiên minh bạch, có trực quan, có kiểm tra và có giới hạn diễn giải.

---

## 7. Các câu giảng viên dễ hỏi và cách trả lời

### Tại sao dùng CatBoost?

Vì dữ liệu gồm số, phân loại và missing. CatBoost xử lý trực tiếp các loại dữ liệu này, mô hình hóa quan hệ phi tuyến và ít cần tiền xử lý.

### Tại sao không dùng accuracy?

Accuracy phụ thuộc ngưỡng và dễ gây hiểu sai với dữ liệu lệch lớp. Bài toán này cần xếp hạng theo capacity nên dùng AUC, PR-AUC, lift, precision và recall.

### Lift 1,88× nghĩa là gì?

Top 10% risk có tỷ lệ churn bằng 1,88 lần tỷ lệ churn toàn nguồn.

### Tại sao không dùng ngưỡng score 0,5?

Chiến dịch bị giới hạn bởi ngân sách và capacity. Vì vậy chọn top 5%, 10% hoặc 20% phù hợp với vận hành hơn một ngưỡng xác suất cố định.

### Tại sao phải đánh giá out-of-fold?

Nếu đánh giá trên dữ liệu đã dùng để train, kết quả có thể quá lạc quan. OOF bảo đảm mỗi score đánh giá được tạo bởi mô hình không train trên chính dòng đó.

### Vì sao có inner split bên trong outer fold?

Inner split dùng để chọn depth và số vòng. Outer holdout vẫn hoàn toàn chưa được dùng để chọn cấu hình, nên metric ngoài mẫu đáng tin hơn.

### ReasonCode có giải thích mô hình không?

Không. Nó là rule vận hành, không phải SHAP hoặc feature attribution.

### Có thể khẳng định nguyên nhân churn không?

Không. Đây là snapshot quan sát; correlation không chứng minh causation.

### Tại sao phải xem cả tỷ lệ và quy mô?

Một nhóm có churn rate rất cao nhưng chỉ có vài chục khách có thể đóng góp ít churner hơn một nhóm tỷ lệ thấp hơn nhưng có hàng nghìn khách.

### Tại sao dùng Wilson CI?

Wilson CI ổn định hơn khoảng tin cậy xấp xỉ đơn giản khi tỷ lệ gần 0/1 hoặc mẫu nhỏ. Nó cho người xem biết mức độ không chắc chắn của churn rate.

### Tại sao không dùng pie chart?

Đề tài cần so sánh nhiều nhóm và mức chênh lệch. Bar chart dùng chung một trục nên dễ so sánh chính xác hơn góc hoặc diện tích của pie chart.

### Tại sao chưa tính ROI?

Chưa có chi phí offer, margin, CLV và uplift từ treatment/control.

### Tại sao chưa khẳng định policy hiệu quả?

Dữ liệu chỉ chứa outcome quan sát, chưa có nhóm treatment và control. Vì vậy chưa thể ước lượng tác động tăng thêm của chính sách.

### `MonthlyRevenue` có phải CLV không?

Không. Nó chỉ là proxy giá trị hiện tại, chưa bao gồm margin, thời gian duy trì, chi phí phục vụ hoặc giá trị tương lai.

### `CreditRating` có rủi ro gì?

Nó có thể tạo rủi ro fairness. Không được dùng đơn lẻ để từ chối hỗ trợ hoặc áp điều kiện bất lợi. Trước vận hành cần đánh giá disparity và phê duyệt chính sách.

### Dashboard tĩnh có ẩn danh hoàn toàn không?

Không. Nó bỏ `CustomerID` nhưng vẫn chứa dữ liệu cấp dòng ở dạng band, score và target. Nếu publish repository, CSV raw có ID cũng có thể bị công khai.

### Tại sao GitHub Pages cần bản JavaScript riêng?

GitHub Pages chỉ phục vụ file tĩnh, không chạy Python hoặc Dash trên server. Vì vậy các phép lọc, group và vẽ biểu đồ phải được thực hiện bằng JavaScript trong trình duyệt.

---

## 8. Điểm mạnh của đề tài về trực quan hóa dữ liệu

### Có cấu trúc kể chuyện rõ ràng

```text
Overview → Drivers → Risk & Segments → Retention Strategy
```

Người xem đi từ vấn đề tổng thể đến tín hiệu, nhóm ưu tiên và hành động.

### Phân biệt risk và reach

Mỗi chủ đề quan trọng đều đặt tỷ lệ churn cạnh quy mô nhóm, tránh đưa ra quyết định dựa trên một tỷ lệ cao nhưng mẫu nhỏ.

### Mẫu số thay đổi đúng theo bộ lọc

KPI và biểu đồ luôn được tính lại trên cùng lát cắt. Điều này tránh lỗi lấy churn count của nhóm nhỏ chia cho tổng toàn nguồn.

### Thể hiện độ bất định

Wilson CI 95% được đưa vào biểu đồ tỷ lệ thay vì chỉ hiển thị một con số điểm.

### Kết nối biểu đồ với quyết định

Dashboard không kết thúc ở “nhóm nào churn cao” mà tiếp tục trả lời:

- Liên hệ bao nhiêu khách?
- Ưu tiên P1–P4 thế nào?
- Thử treatment gì?
- Đo KPI và guardrail gì?

### Công khai giới hạn

Dashboard ghi rõ snapshot không chứng minh nguyên nhân, score không phải uplift và policy mới là giả thuyết.

---

## 9. Giới hạn bắt buộc phải nói trong phần bảo vệ

1. Dữ liệu là một snapshot, không phải chuỗi thời gian.
2. Chưa xác minh mọi predictor tồn tại trước thời điểm churn.
3. Đơn vị của `PercChangeMinutes` và `PercChangeRevenues` chưa rõ.
4. Correlation, feature importance hoặc SHAP không chứng minh nguyên nhân.
5. ReasonCode là rule vận hành, không phải lý do thực sự của từng dự đoán.
6. `MonthlyRevenue` không phải margin hoặc CLV.
7. Chưa có chi phí, uplift hoặc treatment/control nên không thể báo ROI.
8. Chưa có external holdout theo thời gian, drift check hoặc fairness audit hoàn chỉnh.
9. Mô hình chỉ phù hợp để xếp hạng trong demo, chưa phải hệ thống quyết định tự động.
10. Bản Pages bỏ ID nhưng dữ liệu cấp dòng vẫn chưa được xem là ẩn danh hoàn toàn.

---

## 10. Cách chạy dự án

### Cài thư viện

```powershell
python -m pip install -r work/requirements.txt
```

### Chạy pipeline

```powershell
python work/pipeline/run_all.py
```

### Kiểm tra artifact và dashboard

```powershell
python work/dashboard/verify.py
```

### Chạy dashboard Dash

```powershell
python work/dashboard/dashboard.py
```

Mở:

```text
http://127.0.0.1:8050/
```

### Tạo và xem bản tĩnh

```powershell
python work/dashboard/export_pages.py
python -m http.server 8765 --directory site
```

Mở:

```text
http://127.0.0.1:8765/
```

---

## 11. Các điểm cần xử lý trước khi thuyết trình

### Chọn đúng môi trường và chạy verify

Dự án đã có `.venv` cục bộ. Trước demo, kích hoạt môi trường hoặc gọi Python trong `.venv`, sau đó chạy:

```powershell
python -m pip install -r work/requirements.txt
python work/pipeline/run_all.py
python work/dashboard/verify.py
python work/dashboard/dashboard.py
```

### Kiểm tra quyền công khai dữ liệu

Trước khi đẩy repository lên GitHub public cần quyết định:

- Có được công khai CSV raw chứa `CustomerID` hay không.
- Có được công khai dữ liệu cấp dòng trong `site/data.json` hay không.
- Có cần thay bằng dữ liệu tổng hợp hoặc repository private hay không.

---

## 12. Câu kết luận ngắn gọn

> Dự án xây dựng một quy trình phân tích churn có thể tái tạo: bắt đầu từ kiểm tra dữ liệu, trực quan hóa risk và reach, chấm điểm ngoài mẫu, chia nhóm ưu tiên và chuyển insight thành giả thuyết chính sách. Kết quả cho thấy churn tập trung hơn ở giai đoạn 12–18 tháng, thiết bị cũ hoặc không hỗ trợ web, và nhóm sử dụng thấp hoặc suy giảm. Mô hình có khả năng xếp hạng ở mức vừa phải, với ROC-AUC 0,6715 và lift 1,88 lần tại capacity 10%. Tuy nhiên, các chính sách giữ chân vẫn cần được kiểm chứng bằng treatment/control trước khi triển khai thật.
