# PLAN — Làm lại dự án theo hướng môn Trực quan hóa dữ liệu (2 giờ)

Ngày lập: 31/10/2026. Người thực hiện: Codex, làm tuần tự từng task T0 → T8 bên dưới.
Mỗi task có **đầu vào, việc cần làm, tiêu chí xong (Definition of Done)**. Làm xong task nào
thì commit task đó, không gộp.

---

## 0. Bối cảnh và mục tiêu

**Vai trò:** chuyên viên phân tích dữ liệu của công ty viễn thông Cell2Cell.
**Bài toán:** khách nào có khả năng rời bỏ (churn), vì sao, và nên giữ chân bằng chính sách gì.
**Môn học:** Trực quan hóa dữ liệu. Vì vậy trọng tâm chấm điểm là:

1. Xử lý dữ liệu cơ bản (làm sạch, missing, outlier, tạo nhóm/band).
2. Phân tích khám phá (EDA) bằng **nhiều loại biểu đồ khác nhau**, mỗi biểu đồ trả lời một câu hỏi.
3. **Insight** rút ra từ dữ liệu, có số liệu cụ thể.
4. **Dashboard** trình bày theo chuẩn BI doanh nghiệp.
5. Đề xuất chính sách giữ chân dựa trên insight.

**Hiện trạng repo:** đã chạy được, nhưng phần lớn công sức nằm ở mô hình CatBoost nested-CV,
manifest/hash SHA256, verify, audit UI, Pages export. Các phần đó **không phải trọng tâm môn học**.
Dữ liệu chỉ dùng 10/58 cột, nên bỏ sót nhiều insight hay (cuộc gọi retention team, chăm sóc khách hàng,
cuộc gọi rớt, vùng phục vụ, máy refurbished, credit rating...).

### Giữ lại / Bỏ qua / Làm mới

| Hạng mục | Quyết định | Lý do |
|---|---|---|
| `data/cell2celltrain.csv` | **Giữ**, không sửa | Nguồn raw |
| Notebook `01`, `02`, `03` | **Giữ nguyên, không sửa** | Kết quả cũ, notebook 03 vẫn cung cấp risk score (OOF) cho trang Phân khúc |
| `work/build/customer_mart.parquet` (risk score, decile) | **Tái sử dụng** nếu có, không bắt buộc | Trang 3 dashboard dùng `RiskDecile`; nếu không có thì bỏ phần score |
| `verify_notebooks.py`, `audit_ui*.py`, `verify_ui.py`, manifest/hash | **Bỏ qua**, không mở rộng, không viết thêm loại này | Không phục vụ môn học, tốn thời gian |
| `pages_src/`, `export_pages.py` | **Đóng băng** | Viết lại JS song song với Dash sẽ gấp đôi việc |
| `.github/workflows/pages.yml` | Đổi trigger sang chỉ `workflow_dispatch` (T0) | Tránh CI đỏ khi dashboard đổi |
| Script chuẩn bị dữ liệu trực quan | **Làm mới** `work/viz/prepare_viz_data.py` | Dùng ~25 cột thay vì 10 |
| Notebook EDA trực quan | **Làm mới** `work/viz/04_eda_truc_quan.ipynb` | 15+ biểu đồ đa dạng, mỗi biểu đồ có insight |
| Dashboard | **Làm lại** `work/dashboard/dashboard.py` theo chuẩn BI (mục 2) | Hiện chưa đạt chuẩn BI |
| Báo cáo insight + chính sách | **Viết lại** `INSIGHTS_AND_POLICY.md` | Theo cấu trúc insight → bằng chứng → hành động |

---

## 1. Đánh giá dashboard hiện tại so với chuẩn BI doanh nghiệp

**Kết luận: chưa đạt chuẩn BI doanh nghiệp.** Kỹ thuật tốt (filter, Wilson CI, responsive), nhưng
về mặt trình bày cho người ra quyết định thì còn các lỗi sau:

| # | Vấn đề | Chuẩn BI mong đợi |
|---|---|---|
| B1 | KPI hàng đầu là thuật ngữ kỹ thuật (ROC-AUC, PR-AUC, log loss, "Depth phổ biến"); có KPI vô nghĩa với lãnh đạo như "Policy đã được thử nghiệm: 0" | KPI kinh doanh: số khách, churn rate, số khách churn, doanh thu/tháng đang bị đe dọa, % khách rủi ro cao. Model metric đưa xuống phần phụ/tooltip |
| B2 | Gần như chỉ có bar chart (rate + volume lặp lại cho từng band) | Mỗi trang 4–6 visual, đa dạng loại theo đúng mục đích: so sánh, phân bố, tương quan, cơ cấu, xu hướng |
| B3 | Tiêu đề biểu đồ mô tả ("Churn theo tenure") | **Action title**: tiêu đề là câu kết luận ("Khách dùng máy > 2 năm churn 36%, gấp 1,6 lần máy mới") |
| B4 | Quá nhiều chữ cảnh báo/giới hạn trên trang chính | Caveat gom về 1 dòng footnote hoặc trang "Phương pháp"; trang chính để số và hình |
| B5 | Không có so sánh với mốc (baseline) trên visual | Đường tham chiếu churn trung bình 28,8% trên mọi biểu đồ churn rate; KPI có delta so với trung bình |
| B6 | Chỉ 10 cột được phân tích | Thêm hành vi dịch vụ (retention call, care call, dropped call, overage), thiết bị (refurbished, giá máy), nhân khẩu (credit, income, Prizm, nghề), địa lý (ServiceArea) |
| B7 | Màu sắc chưa mang nghĩa nhất quán | Một bảng màu cố định: churn = đỏ/cam, ở lại = xám xanh, nhấn mạnh 1 màu, còn lại xám |
| B8 | Không có luồng kể chuyện rõ (What → Why → Who → Action) | 4 trang theo đúng luồng: Tổng quan → Nguyên nhân → Ai cần giữ → Hành động |

---

## 2. Chuẩn BI áp dụng cho dashboard mới (checklist bắt buộc)

1. **Bố cục Z-pattern:** hàng 1 là thanh tiêu đề + bộ lọc; hàng 2 là 4–5 thẻ KPI; bên dưới là lưới biểu đồ
   2 cột, biểu đồ quan trọng nhất ở trên bên trái.
2. **KPI card** gồm: tên, giá trị lớn, so sánh (delta so với toàn công ty hoặc ▲▼), chú thích 1 dòng.
3. **Action title** cho mọi biểu đồ, kèm phụ đề nhỏ ghi mẫu số (`n = ...`).
4. **Đường baseline** churn trung bình (nét đứt, xám) trên mọi biểu đồ churn rate.
5. **Bảng màu cố định** (định nghĩa 1 lần trong code, dùng ở cả notebook lẫn dashboard):
   - `CHURN = "#D64545"` (đỏ), `STAY = "#8FA3B5"` (xám xanh), `ACCENT = "#1F6FB2"` (xanh nhấn), `NEUTRAL = "#C9D3DC"`.
   - Thang tuần tự cho heatmap: `Reds`; thang phân kỳ cho tương quan: `RdBu_r` tâm 0.
6. **Sắp xếp:** bar phân loại (không có thứ tự tự nhiên) luôn sort giảm dần; band có thứ tự thì giữ thứ tự.
7. **Định dạng số tiếng Việt:** `51.047`, `28,8%`, `$58,8`. Không quá 1 chữ số thập phân trên visual.
8. **Không dùng:** 3D, pie > 4 lát, trục y bị cắt với bar, 2 trục y, màu cầu vồng cho dữ liệu phân loại.
9. **Bộ lọc toàn cục (slicer):** Tenure band, Vùng (ServiceArea 3 ký tự đầu), Tuổi thiết bị, Credit rating.
   Mọi KPI và biểu đồ phải cập nhật theo bộ lọc. Có nút "Xóa lọc".
10. **Tooltip** hiển thị: nhóm, `n`, số churn, churn rate.
11. Mỗi trang ≤ 6 biểu đồ + 1 hộp "Insight chính" (3 gạch đầu dòng có số).
12. Caveat (dữ liệu snapshot, tương quan ≠ nhân quả) chỉ để **1 footnote** cuối trang.

---

## 3. Insight đã kiểm chứng nhanh (dùng làm "đáp án" để đối chiếu)

Các số dưới đây tính trực tiếp từ raw CSV (đọc với `na_values=["NA"]`), n = 51.047, baseline churn
**28,82%**. Codex phải tính lại bằng code, không hard-code, và dùng để kiểm tra kết quả của mình.

| # | Insight | Bằng chứng |
|---|---|---|
| I1 | **Tuổi thiết bị là tín hiệu mạnh nhất** (tương quan cao nhất với churn trong nhóm numeric, \|r\| ≈ 0,10) | ≤180 ngày: 22,9% · 181–365: 26,6% · 366–730: 32,5% · >730: 36,1% (n=5.141) |
| I2 | **Đỉnh churn ở tháng 12–18** của vòng đời (khả năng hết hợp đồng 1 năm) | 0–6 tháng: 19,3% · 6–12: 27,0% · **12–18: 31,6%** · 18–24: 29,7% · >36: 27,3% |
| I3 | **Gọi tới retention team mà vẫn churn 45%**; nhận ưu đãi giữ chân vẫn churn ≈ 41% → chương trình retention hiện tại kém hiệu quả | MadeCallToRetentionTeam=Yes: 1.745 khách, 45,0% vs No 28,2% |
| I4 | **Máy không hỗ trợ web churn 37,4%** vs 27,9%; máy refurbished 32,2% vs 28,3% | HandsetWebCapable, HandsetRefurbished |
| I5 | **Nghịch lý chăm sóc khách hàng:** khách *không* gọi CSKH churn cao nhất (30,7%), gọi > 10 lần/tháng chỉ 23,2% → khách im lặng = khách đã rời lòng | CustomerCareCalls |
| I6 | **Khách không có cuộc gọi rớt nào churn 34,3%** (cao nhất) → không phải chất lượng mạng, mà là khách ít dùng/ngừng dùng | DroppedBlockedCalls = 0: n=5.793 |
| I7 | **Vượt gói nhiều churn cao hơn:** Overage > 200 phút: 32,7% → gói cước không phù hợp | OverageMinutes |
| I8 | **Chênh lệch theo vùng** đến 12 điểm %: SEA 34,2%, MIA 33,1% vs STL 22,3% | ServiceArea[:3], chỉ lấy vùng n > 800 |
| I9 | Credit rating tốt (1–3) churn **cao hơn** (≈30–31%) so với 5-Low (22,1%) → khách tín dụng tốt dễ chuyển mạng (đối thủ săn đón) | CreditRating |
| I10 | Nhân khẩu học (income, nghề, Prizm, hôn nhân) **chênh lệch nhỏ** (≤ 4 điểm %) → ưu tiên tín hiệu hành vi & thiết bị hơn nhân khẩu | IncomeGroup, Occupation, PrizmCode |

---

## 4. Danh mục biểu đồ (≥ 16 loại visual, mỗi cái gắn 1 câu hỏi)

Notebook `04_eda_truc_quan.ipynb` vẽ **tất cả** biểu đồ dưới đây bằng Plotly (để tái sử dụng hàm vẽ cho
dashboard). Mỗi biểu đồ theo khuôn: **Markdown câu hỏi → code → biểu đồ → Markdown "Insight:" có số**.

| ID | Câu hỏi | Loại biểu đồ | Cột | Insight kỳ vọng |
|---|---|---|---|---|
| C01 | Tỷ lệ churn tổng là bao nhiêu? | KPI card + **donut** 2 lát | Churn | 28,8% |
| C02 | Dữ liệu thiếu ở đâu? | **Bar ngang** % missing theo cột (chỉ cột có missing) | toàn bộ | missing nhỏ, tập trung vài cột |
| C03 | Phân bố doanh thu/phút gọi khác nhau giữa churn và ở lại? | **Histogram chồng (overlay)** hoặc **violin** | MonthlyRevenue, MonthlyMinutes | |
| C04 | Outlier nằm ở đâu? | **Box plot** theo Churn | MonthlyRevenue, OverageMinutes, CurrentEquipmentDays | máy cũ hơn ở nhóm churn |
| C05 | Churn thay đổi thế nào theo vòng đời? | 2 subplot xếp dọc chung trục x: trên là **line** churn rate theo MonthsInService (gộp mỗi 3 tháng), dưới là **bar** số khách (không dùng 2 trục y) | MonthsInService | I2 |
| C06 | Tuổi thiết bị ảnh hưởng ra sao? | **Bar có baseline** + nhãn % | EquipmentAgeBand | I1 |
| C07 | Tenure × tuổi thiết bị kết hợp thế nào? | **Heatmap** churn rate (ô có n < 100 để trống) | TenureBand × EquipmentAgeBand | ô nóng nhất: 12–24 tháng + máy > 1 năm |
| C08 | Chương trình retention hiện tại có hiệu quả? | **Funnel** hoặc bar 3 bậc: Tất cả → Gọi retention team → Nhận ưu đãi, kèm churn rate từng bậc | MadeCallToRetentionTeam, RetentionOffersAccepted | I3 |
| C09 | Thiết bị (web/refurbished) liên quan churn? | **Grouped bar** hoặc **100% stacked bar** | HandsetWebCapable, HandsetRefurbished | I4 |
| C10 | Gọi CSKH nhiều có phải dấu hiệu bất mãn? | **Bar theo band** + baseline | CustomerCareCalls band | I5 nghịch lý |
| C11 | Chất lượng mạng (dropped/blocked) có gây churn? | **Bar theo band** | DroppedBlockedCalls band | I6 |
| C12 | Gói cước có phù hợp? | **Scatter/bubble**: x = MonthlyMinutes band, y = churn rate, size = n, màu = Overage band; hoặc bar Overage | OverageMinutes, MonthlyMinutes | I7 |
| C13 | Vùng nào churn cao? | **Bar ngang sort giảm** + baseline, tô đỏ vùng > baseline | ServiceArea[:3] (n > 800) | I8 |
| C14 | Churner tập trung ở đâu (quy mô)? | **Treemap**: Vùng → TenureBand, kích thước = số churner, màu = churn rate | Region, TenureBand | nơi mất nhiều khách nhất (khác nơi rate cao nhất) |
| C15 | Pareto: bao nhiêu vùng chiếm 80% churner? | **Pareto** (bar + line % tích lũy, cùng 1 subplot dùng trục phần trăm riêng là ngoại lệ được phép) | Region | |
| C16 | Credit rating và churn? | **Bar** theo thứ tự 1→7 | CreditRating | I9 |
| C17 | Nhân khẩu học có quan trọng? | **Small multiples** (facet 4 ô bar): IncomeGroup, Occupation, PrizmCode, MaritalStatus, cùng thang y | | I10 chênh nhỏ |
| C18 | Biến numeric nào tương quan với churn và với nhau? | **Correlation heatmap** (~15 biến numeric chính + Churn), thang RdBu_r | numeric | |
| C19 | Mô hình xếp hạng rủi ro giúp gì? (chỉ nếu có `customer_mart.parquet`) | **Cumulative gain / lift curve** + bar churn rate theo RiskDecile | RiskDecile, oof score | top 10% bắt được ~19% churner (lift ≈ 1,9×) |
| C20 | Phân khúc nào cần ưu tiên? | **Bubble matrix**: x = churn rate, y = doanh thu TB/tháng, size = số khách, 1 bubble = 1 phân khúc hành động (mục 5) | Segment | 2×2 "giữ gấp / nuôi dưỡng / theo dõi / để tự nhiên" |

---

## 5. Phân khúc hành động và chính sách giữ chân

Tạo cột `ActionSegment` bằng rule đơn giản, có thứ tự ưu tiên (rule đầu tiên khớp thì gán):

| Thứ tự | Segment | Điều kiện | Chính sách đề xuất | KPI đo |
|---|---|---|---|---|
| 1 | **Đã báo động** | MadeCallToRetentionTeam = Yes | Thiết kế lại ưu đãi retention (ưu đãi hiện tại không giữ được 41–45%); chuyển chuyên viên cấp cao xử lý | Churn rate nhóm này sau 60 ngày |
| 2 | **Máy cũ** | CurrentEquipmentDays > 730 hoặc (≥ 365 và HandsetWebCapable = No) | Chương trình đổi máy trả góp / trợ giá máy smartphone gắn cam kết 12 tháng | % nhận đổi máy, churn 90 ngày |
| 3 | **Sắp hết hợp đồng** | MonthsInService 10–18 | Gọi chăm sóc chủ động tháng 10–11, ưu đãi gia hạn | Tỷ lệ gia hạn |
| 4 | **Sai gói** | OverageMinutes > 100 | Tư vấn nâng gói phù hợp, không tính phí vượt tháng đầu | Overage giảm, churn |
| 5 | **Im lặng** | CustomerCareCalls = 0 và MonthlyMinutes < 150 | Chiến dịch tái kích hoạt (SMS/app), khảo sát hài lòng | Minutes tăng |
| 6 | **Ổn định** | còn lại | Duy trì, chương trình loyalty | |

Trên dashboard trang 4 hiển thị cho mỗi segment: số khách, churn rate, doanh thu/tháng đang bị đe dọa
(`sum(MonthlyRevenue) của khách trong segment × churn rate`), chính sách, KPI. Ghi rõ: chính sách là
đề xuất, cần A/B test (nhóm thử/nhóm đối chứng) trước khi triển khai rộng — **chỉ 1 dòng**, không viết dài.

---

## 6. Dashboard mới — 4 trang

Giữ Dash + Plotly (đã có trong `work/requirements.txt`). Tách code thành:
- `work/viz/charts.py`: bảng màu, hàm format số, **mọi hàm vẽ biểu đồ** (dùng chung notebook 04 và dashboard).
- `work/dashboard/dashboard.py`: layout, bộ lọc, callback. Đọc `work/build/viz_customers.parquet`.

| Trang | Câu hỏi | KPI (hàng 2) | Biểu đồ |
|---|---|---|---|
| **1. Tổng quan** | Churn lớn đến đâu, mất bao nhiêu tiền? | Tổng khách · Số churn · Churn rate (delta vs toàn công ty) · Doanh thu/tháng của khách churn · Tenure TB | C01 donut, C05 vòng đời, C13 vùng, C14 treemap |
| **2. Nguyên nhân** | Tín hiệu nào đi cùng churn? | Churn máy > 2 năm · Churn máy không web · Churn khách gọi retention | C06, C07 heatmap, C10, C11, C12 |
| **3. Chân dung & rủi ro** | Ai đang có nguy cơ? | % khách rủi ro cao (decile 8–10) · Lift top 10% | C08 funnel, C16, C17 small multiples, C19 (nếu có score) |
| **4. Hành động** | Giữ ai, bằng cách nào? | Số khách cần can thiệp · Doanh thu bị đe dọa | C20 bubble matrix, bảng chính sách (mục 5) dạng card |

Bộ lọc dùng chung đặt ở thanh trên cùng (mục 2.9). Sidebar điều hướng 4 trang, trang hiện tại được
đánh dấu. Footer 1 dòng: nguồn dữ liệu + "Tương quan quan sát, không phải nhân quả".

---

## 7. Kế hoạch thực hiện 2 giờ (cho Codex)

> Quy tắc chung: chạy được trên Windows/PowerShell, Python 3.11, đường dẫn tương đối từ root repo.
> Sau mỗi task: chạy lệnh kiểm tra ghi trong DoD, rồi `git commit` với message `T<n>: <mô tả>`.

### T0 — Chuẩn bị (5 phút)
- Thêm vào `work/requirements.txt`: `kaleido>=0.2,<2` (xuất PNG từ Plotly) và `nbconvert>=7,<8` (chạy notebook).
- Tạo `.venv`, `pip install -r work/requirements.txt`.
- Sửa `.github/workflows/pages.yml`: bỏ trigger `push`, chỉ giữ `workflow_dispatch`.
- **DoD:** `python -c "import pandas, plotly, dash, kaleido, nbconvert"` chạy được.

### T1 — Chuẩn bị dữ liệu trực quan (15 phút)
File `work/viz/prepare_viz_data.py`:
- Đọc raw `data/cell2celltrain.csv` với `na_values=["NA"]`. Không sửa file raw.
- Giữ cột: `CustomerID, Churn, MonthlyRevenue, MonthlyMinutes, TotalRecurringCharge, OverageMinutes,
  RoamingCalls, PercChangeMinutes, DroppedBlockedCalls, CustomerCareCalls, MonthsInService,
  CurrentEquipmentDays, HandsetWebCapable, HandsetRefurbished, HandsetPrice, ServiceArea,
  MadeCallToRetentionTeam, RetentionCalls, RetentionOffersAccepted, CreditRating, IncomeGroup,
  PrizmCode, Occupation, MaritalStatus, AgeHH1` và các cột numeric khác cần cho C18.
- Tạo: `ChurnFlag` (0/1), `Region = ServiceArea[:3]` (thiếu → "Unknown"), các band:
  `TenureBand` (0–6, 7–12, 13–18, 19–24, 25–36, >36), `EquipmentAgeBand` (≤180, 181–365, 366–730, >730, âm → "Bất thường"),
  `CareCallsBand` (0, ≤1, 1–3, 3–10, >10), `DroppedBand` (0, ≤5, 5–15, 15–40, >40), `OverageBand` (0, ≤50, 50–200, >200),
  `MinutesBand` (≤150, 150–500, >500), `ActionSegment` (mục 5).
- Nếu tồn tại `work/build/customer_mart.parquet` thì merge `RiskScore`/`RiskDecile` theo `CustomerID` (kiểm tra tên cột thật trong file).
- In bảng tóm tắt: số dòng, % missing cột chính, số khách mỗi segment.
- Xuất `work/build/viz_customers.parquet`.
- **DoD:** chạy script in ra 51.047 dòng, churn 14.711 (28,82%); tổng các segment = 51.047.

### T2 — Thư viện biểu đồ dùng chung (15 phút)
File `work/viz/charts.py`:
- Hằng số màu (mục 2.5), `fmt_n`, `fmt_pct` kiểu Việt Nam, `BASELINE` tính từ dữ liệu truyền vào.
- Hàm `rate_by(df, col, order=None)` → DataFrame `[col, n, churners, rate]`.
- Hàm vẽ C01–C20, mỗi hàm nhận `df` (đã lọc) và trả về `go.Figure`; hàm tự sinh **action title** từ số
  thật (ví dụ: lấy nhóm có rate cao nhất và so với baseline), không hard-code chữ số.
- Hàm `apply_style(fig)` thống nhất font, nền trắng, lưới nhạt, legend ngang.
- **DoD:** `python -c "from work.viz import charts"` (hoặc import theo cấu trúc package đã chọn) không lỗi.

### T3 — Notebook EDA trực quan (30 phút)
File `work/viz/04_eda_truc_quan.ipynb`, tiếng Việt, cấu trúc:
1. Giới thiệu bài toán (vai trò chuyên viên phân tích, câu hỏi kinh doanh).
2. Tổng quan dữ liệu: shape, kiểu dữ liệu, missing (C02), thống kê mô tả.
3. Xử lý dữ liệu: giải thích từng bước của T1 (band, missing, giá trị âm).
4. EDA theo 5 nhóm: Tổng quan (C01, C03, C04) → Vòng đời & thiết bị (C05, C06, C07, C09) →
   Hành vi dịch vụ (C08, C10, C11, C12) → Địa lý (C13, C14, C15) → Khách hàng (C16, C17, C18).
5. Mô hình rủi ro (C19, dùng lại kết quả notebook 03, chỉ diễn giải — **không train lại**).
6. Phân khúc & chính sách (C20 + bảng mục 5).
7. Tổng kết: 5–7 insight chính đánh số, mỗi insight 1 câu có số.
- Mỗi biểu đồ: 1 ô Markdown câu hỏi, 1 ô code ngắn gọi hàm từ `charts.py`, 1 ô Markdown "**Insight:** ..." có số.
- Vì Plotly không hiện trên GitHub, mỗi biểu đồ còn lưu PNG vào `reports/figures/Cxx_<ten>.png`
  (`fig.write_image`, cần `kaleido`; nếu không cài được kaleido thì lưu `.html` và ghi chú trong README).
- **DoD:** `jupyter nbconvert --to notebook --execute --inplace work/viz/04_eda_truc_quan.ipynb` chạy hết không lỗi;
  số liệu khớp mục 3 (sai lệch do band khác chút là chấp nhận được, nhưng phải giải thích).

### T4 — Dashboard trang 1–2 (20 phút)
- Viết lại `work/dashboard/dashboard.py` theo mục 6, dùng `charts.py`. Có thể giữ lại CSS cũ trong
  `work/dashboard/assets/style.css` nhưng sửa theo checklist mục 2.
- Bộ lọc toàn cục + nút xóa lọc; callback cập nhật KPI và biểu đồ.
- **DoD:** `python work/dashboard/dashboard.py` mở `http://127.0.0.1:8050/`, trang 1–2 hiển thị đủ; lọc
  TenureBand 13–18 thì KPI churn rate thay đổi đúng số tính bằng pandas.

### T5 — Dashboard trang 3–4 (15 phút)
- Trang 3 chân dung & rủi ro; nếu không có `RiskDecile` thì ẩn C19 và KPI liên quan, không crash.
- Trang 4: bubble matrix C20 + các card chính sách (mục 5) có số khách, churn rate, doanh thu bị đe dọa.
- **DoD:** cả 4 trang chạy, không có lỗi trong console Dash; lọc về 0 khách thì hiện thông báo thay vì lỗi.

### T6 — Rà soát chuẩn BI (10 phút)
Tự kiểm tra từng mục trong checklist mục 2 và ghi kết quả (✅/❌ + sửa) vào `docs/BI_CHECKLIST.md`.
Chụp ảnh 4 trang (thủ công hoặc Playwright nếu có sẵn) vào `reports/dashboard/`.
- **DoD:** không còn ❌ ở mục 1–8, 11.

### T7 — Viết lại tài liệu (8 phút)
- `INSIGHTS_AND_POLICY.md`: 7–10 insight (mỗi cái: phát hiện → số liệu → biểu đồ minh họa (link PNG) → hành động) +
  bảng chính sách mục 5.
- `README.md`: thêm mục "Bản trực quan hóa (môn học)" ở **đầu file**: cách chạy 3 lệnh
  (`prepare_viz_data.py` → notebook 04 → dashboard), cấu trúc thư mục mới, link insight.
  Phần README cũ về CatBoost/Pages giữ ở dưới, đặt tiêu đề "Phụ lục: pipeline mô hình (bản trước)".
- `HUONG_DAN_THUYET_TRINH.md`: thay bằng kịch bản 5–7 phút theo 4 trang dashboard (What → Why → Who → Action).

### T8 — Kiểm tra cuối và push (2 phút)
- Chạy lại tuần tự: `prepare_viz_data.py` → execute notebook 04 → mở dashboard.
- `git status` sạch (không commit `.venv`, `work/build/`), `git push`.

---

## 8. Ngoài phạm vi (KHÔNG làm trong 2 giờ)
- Train lại / tuning mô hình, SHAP, nested CV mới.
- Manifest, hash SHA256, verify script, audit UI tự động mới.
- Sửa `pages_src/`, `export_pages.py`, deploy GitHub Pages.
- Power BI/Tableau (không làm bằng Codex được). Nếu giảng viên yêu cầu Power BI, xuất `viz_customers.parquet`
  ra CSV và dựng thủ công theo đúng 4 trang + checklist mục 2.

---

## 9. Prompt mẫu để giao cho Codex (copy từng cái, chờ xong mới gửi cái tiếp theo)

```
Đọc AGENTS.md và docs/PLAN_TRUC_QUAN_HOA.md. Làm task T0 và T1. Chỉ làm 2 task này.
Chạy lệnh trong DoD, dán output thật, rồi commit từng task.
```
```
Làm task T2 theo plan. Hàm vẽ phải sinh action title từ số liệu thật, không hard-code.
Viết một đoạn test nhanh gọi mọi hàm vẽ với dữ liệu thật để chắc không lỗi. Commit.
```
```
Làm task T3. Đối chiếu số liệu với bảng Insight mục 3; chỗ nào lệch thì giải thích trong notebook. Commit.
```
```
Làm task T4 rồi T5. Dashboard dùng chung charts.py, theo đúng bảng 4 trang mục 6 và checklist mục 2. Commit từng task.
```
```
Làm task T6, T7, T8. Báo cáo những mục checklist chưa đạt (nếu có) thay vì tự bỏ qua.
```

Nếu Codex làm sai hướng: nhắc lại *"Quay về plan mục X, không làm ngoài phạm vi mục 8"*.
