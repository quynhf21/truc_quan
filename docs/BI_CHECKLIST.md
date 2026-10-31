# Checklist chuẩn BI — dashboard mới (`work/dashboard/dashboard.py`)

Kiểm tra ngày 31/10/2026 trên Chromium headless ở 1440px và 768px. Ảnh chụp: `reports/dashboard/`.

| # | Tiêu chí (plan mục 2) | Kết quả | Ghi chú |
|---|---|---|---|
| 1 | Bố cục Z-pattern: bộ lọc → KPI → biểu đồ, quan trọng nhất ở trên | ✅ | Biểu đồ chính mỗi trang đặt full-width ngay dưới hộp insight |
| 2 | KPI card có giá trị + so sánh với toàn công ty | ✅ | Delta ▲/▼ điểm %, đỏ = xấu hơn, xanh = tốt hơn; trang 1 hiện delta khi đang lọc |
| 3 | Action title cho mọi biểu đồ, có mẫu số | ✅ | Tiêu đề sinh từ số liệu sau lọc (`charts.py`), phụ đề ghi `n` |
| 4 | Baseline churn trung bình trên biểu đồ churn rate | ✅ | Nét đứt xám; biểu đồ vùng dùng baseline của cả lát cắt, không phải tập con vùng lớn |
| 5 | Bảng màu cố định có nghĩa | ✅ | Đỏ = churn/trên trung bình, xám xanh = ở lại/dưới trung bình, xanh đậm = nhấn |
| 6 | Sắp xếp: phân loại sort giảm dần, band giữ thứ tự | ✅ | Vùng sort theo rate; band/credit/decile theo thứ tự tự nhiên |
| 7 | Số định dạng tiếng Việt | ✅ | `51.047`, `28,8%`, `$849,1 nghìn` (`separators=",."`) |
| 8 | Không 3D, pie ≤ 4 lát, bar trục từ 0, không 2 trục y | ✅ | Ngoại lệ có chủ đích: Pareto (C15) dùng trục phụ % tích lũy, chỉ có trong notebook |
| 9 | Bộ lọc toàn cục + Xóa lọc | ✅ | 4 bộ lọc nhiều lựa chọn; đã thử trên trình duyệt: 13–18 tháng → 11.917 khách, 31,6%; Xóa lọc → 51.047 |
| 10 | Tooltip có nhóm, n, số churn, churn rate | ✅ | Tất cả bar/line/bubble |
| 11 | Mỗi trang ≤ 6 biểu đồ + hộp Insight chính | ✅ | 4 / 6 / 5 / 1 biểu đồ + thẻ chính sách |
| 12 | Caveat gom về 1 footnote | ✅ | Footer chung + 1 dòng ghi chú A/B test ở trang Hành động |

Kiểm tra thêm:

- Không lỗi JavaScript/console trên 4 trang; không tràn ngang ở 1440px và 768px.
- Lọc ra 0 khách → thông báo "Không có khách hàng cho bộ lọc này" thay vì lỗi.
- Các lát cắt nhỏ (1 khách, chỉ churner, chỉ khách ở lại) đã qua `work/viz/smoke_test.py`.

Chưa kiểm tra: màn hình < 500px, trình đọc màn hình, mọi tổ hợp bộ lọc.
