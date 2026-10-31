# Hướng dẫn cho Codex / AI agent

Đọc **`docs/PLAN_TRUC_QUAN_HOA.md` trước khi làm bất cứ việc gì**. Đó là plan đã duyệt.

## Mục tiêu
Đồ án môn **Trực quan hóa dữ liệu**: xử lý dữ liệu cơ bản → nhiều biểu đồ đa dạng → insight có số →
dashboard chuẩn BI → chính sách giữ chân. Mô hình ML chỉ là phần phụ, đã có sẵn.

## Cách làm việc
- Làm đúng từng task T0 → T8 trong plan, theo thứ tự. Mỗi lượt chỉ làm task được giao.
- Xong task: chạy lệnh trong **DoD**, báo kết quả thật (kể cả lỗi), rồi commit `T<n>: <mô tả>`.
- Không tự mở rộng phạm vi. Nếu thấy cần làm thêm thì **đề xuất**, chưa làm.
- Không chắc yêu cầu → hỏi lại, không đoán.

## Cấm
- Sửa `data/cell2celltrain.csv`, notebook `work/pipeline/01–03`, `pages_src/`, `export_pages.py`.
- Train lại mô hình, thêm manifest/hash/verify/audit script mới.
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
