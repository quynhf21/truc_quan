# Hướng dẫn cho Codex / AI agent

Đọc **`docs/PLAN_TRUC_QUAN_HOA.md` trước khi làm bất cứ việc gì**. Đó là plan đã duyệt.

Task hiện tại theo yêu cầu người dùng: thống nhất mô hình, toàn bộ EDA và dashboard theo đúng 10 predictor của mô hình. Mỗi predictor phải có trực quan trực tiếp, gồm hai mức thay đổi và số cuộc gọi giờ cao điểm. Bỏ các biểu đồ/chiều chỉ dùng biến ngoài mô hình; không để ô trống. Có thể dùng nhãn rời bỏ, band và điểm suy ra từ bộ 10. Giữ form Plotly, bảng màu và các quy tắc C20 hiện tại; không huấn luyện lại. Các mốc 52 biến trong tài liệu T9/T10 là lịch sử.

## Mục tiêu
Đồ án môn **Trực quan hóa dữ liệu**: xử lý dữ liệu cơ bản → nhiều biểu đồ đa dạng → insight có số →
dashboard chuẩn BI → chính sách giữ chân. Mô hình ML chỉ là phần phụ, đã có sẵn.

## Cách làm việc
- Làm đúng từng task T0 → T8 trong plan, theo thứ tự. Mỗi lượt chỉ làm task được giao.
- Xong task: chạy lệnh trong **DoD**, báo kết quả thật (kể cả lỗi), rồi commit `T<n>: <mô tả>`.
- Không tự mở rộng phạm vi. Nếu thấy cần làm thêm thì **đề xuất**, chưa làm.
- Không chắc yêu cầu → hỏi lại, không đoán.

## Cấm
- Sửa `data/cell2celltrain.csv`, notebook `work/pipeline/01–03`, `pages_src/`, `export_pages.py`, `.github/workflows/` (token push không có quyền workflow).
- Thêm manifest/hash/verify/audit script mới hoặc huấn luyện lại mô hình trong task bổ sung EDA hiện tại.
- T9 (nâng cấp mô hình lên 52 cột, [`docs/TASK_T9_NANG_CAP_MO_HINH.md`](docs/TASK_T9_NANG_CAP_MO_HINH.md)) **đã xong**.
  Yêu cầu mới về 10 biến thay thế cấu hình T9; không dùng kết quả 52 biến làm kết quả hiện hành.
- Chạy lại pipeline để kiểm tra thì được, nhưng **không commit** output notebook/ảnh sinh ra (xem T10).
- Hard-code số liệu (churn rate, n...) trong code hoặc tiêu đề biểu đồ; mọi số phải tính từ dữ liệu.
- Commit `.venv/`, `work/build/`, file dữ liệu sinh ra.
- Viết dài dòng caveat trên dashboard (tối đa 1 footnote/trang).

## Quy ước
- Ngôn ngữ: tiếng Việt cho nội dung, tên biến/hàm tiếng Anh.
- Môi trường: Windows + PowerShell, Python 3.11, `.venv` ở root, đường dẫn tương đối từ root repo.
- Biểu đồ: Plotly, hàm vẽ đặt trong `work/viz/charts.py`, dùng chung cho notebook và dashboard.
- Màu: churn `#D64545`, ở lại `#8FA3B5`, nhấn `#1F6FB2`, trung tính `#C9D3DC`.
- Số kiểu Việt Nam: `51.047`, `28,8%`.
- Mỗi biểu đồ có action title (câu kết luận) + đường baseline churn trung bình khi vẽ churn rate.
