# Hướng dẫn chạy, sử dụng và chỉnh sửa dự án

File này dành cho người mới mở repo (kể cả Codex/AI agent). Kịch bản trình bày nằm ở
[`HUONG_DAN_THUYET_TRINH.md`](HUONG_DAN_THUYET_TRINH.md), insight và chính sách ở [`INSIGHTS_AND_POLICY.md`](INSIGHTS_AND_POLICY.md).

## 1. Cài đặt (một lần, Windows/PowerShell)

```powershell
cd D:\project\iu_anhHuy
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r work/requirements.txt
```

- Cần Python 3.11 (các bản 3.10–3.12 thường cũng chạy được).
- PowerShell chặn `Activate.ps1` → chạy `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` một lần.
- Xuất ảnh PNG cần Chrome hoặc Edge. Nếu báo thiếu Chrome thì chạy `kaleido_get_chrome` một lần.

## 2. Chạy theo thứ tự

| Bước | Lệnh | Kết quả | Thời gian |
|---|---|---|---|
| 1 | `python work/pipeline/run_all.py` | Điểm rủi ro CatBoost 10 biến `work/build/customer_mart.parquet` | vài phút |
| 2 (tùy chọn) | `python work/viz/prepare_viz_data.py` | Bảng phân tích sau khi loại số âm bất thường | vài giây |
| 3 | Mở notebook 04 và chạy tất cả các ô; hoặc `python work/pipeline/run_all.py --only 04 --cwd project` | Output, PNG, báo cáo insight và bộ kết quả dashboard | vài phút |
| 4 | `python work/dashboard/dashboard.py` | Dashboard tại http://127.0.0.1:8050/ | — |

- Khi đã có processed từ notebook 01, chỉ cần `python work/pipeline/run_all.py --only 03 --cwd project` để chạy lại mô hình 10 biến. Sau đó chạy bước 3 để đồng bộ EDA và dashboard; không dùng lại điểm của cấu hình trước.
- Notebook 04 tự đọc nguồn, kiểm tra, loại số âm bất thường và tạo bảng phân tích; không bắt buộc chạy bước 2 trước.
- Bước 3 là bắt buộc trước khi mở dashboard. Notebook xuất biểu đồ Plotly và bản dữ liệu cùng lần chạy. Khi cập nhật dữ liệu hoặc biểu đồ, chạy lại bước 2–3 rồi khởi động lại dashboard.
- `work/build/` bị gitignore: máy mới clone về phải chạy lại từ bước 1 hoặc bước 2.
- Các lệnh thực thi ghi lại output notebook và ảnh; không commit phần output chạy lại. Giữ các thay đổi mã nguồn khi tạo commit.

Nguồn hiện tại có 51.047 khách. Sau khi loại 85 dòng có số âm bất thường, bảng phân tích còn **50.962 khách**, gồm **14.695 khách rời bỏ (28,84%)**. Hai cột mức thay đổi vẫn giữ số âm hợp lệ. Notebook hiển thị bảng trước/sau và số trường hợp âm theo từng trường.

Kiểm tra nhanh sau khi sửa code:

```powershell
python work/viz/smoke_test.py             # gọi các hàm vẽ trên dữ liệu thật + các lát cắt nhỏ, phải in toàn "OK"
python work/pipeline/verify_notebooks.py  # sau bước 1: 3 AUDIT PASS + 14 GUARD PASS
```

So sánh CatBoost, Logistic và LightGBM trên cùng 10 biến: `python work/experiments/compare_models.py`;
`--quick` chỉ chạy CatBoost. Kết quả ở `work/build/model_comparison.csv`; cấu hình so sánh không thay thế đánh giá chính thức của notebook 03. Chi tiết mô hình: [`MODEL_CARD.md`](MODEL_CARD.md).

## 3. Dùng dashboard

- **Thanh bên trái:** Tổng quan → Thiết bị và dịch vụ → Hồ sơ và rủi ro → Phân khúc khách hàng.
- **Bộ lọc trên cùng:** Thời gian sử dụng, Tuổi thiết bị, Hạng tín dụng. Được chọn nhiều giá trị; để trống nghĩa là "Tất cả". Bộ lọc vùng đã bỏ vì không thuộc 10 biến.
  Chỉ số và biểu đồ cập nhật theo lát cắt từ bản dữ liệu do notebook xuất. **Xóa lọc** đưa về toàn bộ khách và biểu đồ đã lưu.
- **KPI:** ▲ đỏ = xấu hơn toàn công ty, ▼ xanh = tốt hơn.
- **Biểu đồ:** rê chuột để xem số khách, số khách rời bỏ và tỷ lệ rời bỏ. Nút máy ảnh góc phải để tải PNG. Dashboard hiển thị tiêu đề trung tính; nhận xét và chính sách nằm trong notebook.
- Thử nhanh: lọc "13–18 tháng" trên bảng đã làm sạch thì có 11.902 khách, tỷ lệ rời bỏ 31,6%.

## 4. Cấu trúc và nơi cần sửa

| Muốn làm gì | Sửa ở đâu |
|---|---|
| Đổi ngưỡng band, rule phân khúc | `work/viz/prepare_viz_data.py` (`BANDS`, `add_segment`) → chạy lại bước 2–4 |
| Sửa/thêm biểu đồ | `work/viz/charts.py`: viết hàm nhận `df` trả `go.Figure`, thêm vào `FIGURES` |
| Đổi màu, font, định dạng số | Đầu file `charts.py` (`CHURN`, `STAY`, `ACCENT`, `apply_style`, `fmt_*`) |
| Bố cục trang, chỉ số, bảng phân khúc, tên biểu đồ | `work/dashboard/dashboard.py` (`page_*`, `CHART_TITLES`) |
| Giao diện dashboard | `work/dashboard/assets_bi/bi.css` |
| Nội dung phân tích, insight | `work/viz/04_eda_truc_quan.ipynb` |

Notebook dùng `charts.py` để vẽ và xuất kết quả. Dashboard đọc các biểu đồ đã xuất ở chế độ toàn bộ khách; khi lọc, nó dùng cùng hàm vẽ trên bản dữ liệu đã xuất. Vì vậy sửa biểu đồ xong cần chạy lại notebook và khởi động lại dashboard.

Thêm một biểu đồ mới:

1. Viết hàm trong `charts.py`. Tiêu đề phải là câu kết luận tính từ số liệu, gọi `apply_style(fig, title, subtitle)`,
   và gọi `add_baseline(...)` nếu vẽ churn rate.
2. Thêm vào `FIGURES` với khóa `Cxx_ten_khong_dau`.
3. Chạy `python work/viz/smoke_test.py`.
4. Thêm ô `show("Cxx_...")` và ô **Nhận xét** vào notebook; nếu cần hiện trên dashboard thì thêm tiêu đề vào `CHART_TITLES` và gọi `graph(...)` trong `page_*`. Chạy lại toàn bộ notebook để xuất kết quả. C05 gồm hai hình riêng: đường tỷ lệ rời bỏ và cột chồng số khách rời bỏ/ở lại theo tháng.

Các file **không** sửa: `data/cell2celltrain.csv`, notebook `work/pipeline/01–03`, `pages_src/`, `export_pages.py`
(bản cũ, xem [`AGENTS.md`](AGENTS.md)).

## 5. Lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `Chưa có kết quả dashboard` | Chạy bước 2 rồi chạy toàn bộ notebook ở bước 3 |
| Dashboard không có điểm rủi ro | Chạy bước 1–3 rồi khởi động lại dashboard |
| `ModuleNotFoundError` | Chưa kích hoạt `.venv` hoặc chưa `pip install -r work/requirements.txt` |
| Lỗi Chrome/Kaleido khi `write_image` | Chạy `kaleido_get_chrome`, hoặc tạm bỏ dòng `fig.write_image` trong hàm `show` của notebook |
| Cổng 8050 đang bận | Tắt dashboard cũ (Ctrl+C), hoặc đổi `port=` cuối file `dashboard.py` |
| Notebook không tìm thấy dữ liệu | Mở notebook từ trong repo; nó tự tìm thư mục chứa `data/cell2celltrain.csv` |

## 6. Giao việc tiếp cho Codex

Codex tự đọc `AGENTS.md`. Mỗi lần chỉ giao một việc nhỏ, có tiêu chí kiểm tra, ví dụ:

```
Đọc AGENTS.md và docs/TASK_T10_CHAY_LAI_LOCAL.md. Làm T10, trả lời đúng mẫu ở mục 5.
```

Ví dụ việc nhỏ khác:

```
Đọc AGENTS.md và HUONG_DAN.md. Thêm biểu đồ churn theo HandsetPrice vào charts.py theo mục 4,
chạy smoke_test.py, thêm vào notebook 04 mục 5. Không sửa file khác. Commit.
```
