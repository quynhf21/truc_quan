# Kịch bản thuyết trình (6–8 phút)

Mạch kể: **Vấn đề → Nguyên nhân → Ai → Hành động**, đi đúng theo 4 trang dashboard. Mở sẵn dashboard
(`python work/dashboard/dashboard.py` → http://127.0.0.1:8050/) và notebook `work/viz/04_eda_truc_quan.ipynb`.
Bản hướng dẫn cũ (thiên về mô hình) vẫn còn trong lịch sử git.

## 0. Mở đầu (30 giây)

> "Em đóng vai chuyên viên phân tích dữ liệu của Cell2Cell. Câu hỏi ban giám đốc đặt ra: khách nào sắp rời bỏ, vì sao, và nên giữ họ bằng cách nào.
> Dữ liệu gồm 51.047 khách, 58 cột."

## 1. Xử lý dữ liệu (1 phút) — notebook mục 2–3

- Dữ liệu khá sạch: missing tối đa 1,78% (C02). Giữ toàn bộ khách, không xóa dòng.
- Chuẩn hóa: `NA` → missing, `Churn` → 0/1, `Region` = 3 ký tự đầu mã vùng, chia band (tenure, tuổi máy, cuộc gọi CSKH...).
- 76 giá trị tuổi máy âm được gắn nhãn "Bất thường", không xóa. Outlier giữ lại vì là khách thật.

## 2. Trang Tổng quan (1 phút)

- KPI: **28,8%** khách rời bỏ, khoảng $849 nghìn doanh thu/tháng.
- Biểu đồ đường: **phát hiện lớn nhất** là churn ~15% ở tháng 7–9 rồi vọt lên **44,6% ở tháng 11**, tức hết hợp đồng 1 năm.
- Bar vùng: SEA 34% so với STL 22%. Treemap: NYC mất nhiều khách nhất về số lượng, dù rate chỉ ở mức trung bình.
  Ý cần nói: **rate cao ≠ mất nhiều khách nhất**.

## 3. Trang Nguyên nhân (1,5 phút)

- Tuổi máy: churn tăng đều, máy > 2 năm 36,1% (gấp 1,6 lần máy mới).
- Heatmap: khách trung thành > 36 tháng mà máy cũ vẫn churn 40%, nghĩa là **máy cũ là tín hiệu mạnh ở mọi tenure**.
- Nghịch lý: khách **không** gọi CSKH và khách **không** có cuộc gọi rớt lại churn cao nhất. Khách im lặng/ít dùng mới đáng lo,
  không phải khách hay phàn nàn.
- Bubble gói cước: dùng quá ít hoặc vượt gói nhiều đều rủi ro, nên cần tư vấn đúng gói.
- Thao tác demo: chọn bộ lọc **Thời gian sử dụng = 13–18 tháng**, KPI và mọi biểu đồ cập nhật theo. Bấm **Xóa lọc**.

## 4. Trang Chân dung & rủi ro (1,5 phút)

- Funnel: khách đã nhận ưu đãi giữ chân **vẫn churn 41%**, tức chương trình hiện tại không giữ được khách.
- Mô hình (CatBoost 52 cột): decile 10 churn 56%. Gain curve: liên hệ 20% khách rủi ro nhất bắt được 34% khách sẽ rời bỏ.
- Tín dụng tốt churn cao hơn; nhân khẩu học (thu nhập, nghề, hôn nhân) chênh rất ít, nên **chọn khách theo hành vi, không theo nhân khẩu**.

## 5. Trang Hành động (1,5 phút)

- Bubble matrix: 4 phân khúc cần can thiệp đều nằm bên phải đường trung bình. Tổng cộng 25.319 khách, ≈ $534 nghìn/tháng bị đe dọa.
- Đọc 4 thẻ chính sách theo thứ tự ưu tiên:
  1. **Đã báo động**: thiết kế lại ưu đãi.
  2. **Hết hợp đồng**: gọi từ tháng 10, ưu đãi gia hạn. Đây là nhóm có doanh thu bị đe dọa lớn nhất.
  3. **Máy cũ**: đổi máy trả góp gắn cam kết.
  4. **Rủi ro cao (mô hình)**: tư vấn gói, ưu đãi cá nhân hóa.

## 6. Kết luận (30 giây)

> "Ba đòn bẩy chính: **thời điểm hết hợp đồng, tuổi thiết bị, và chất lượng của chương trình giữ chân**.
> Các đề xuất dựa trên tương quan quan sát nên cần A/B test trước khi triển khai rộng, bắt đầu ở 20 vùng chiếm 80% khách rời bỏ."

## Câu hỏi có thể gặp

| Câu hỏi | Trả lời |
|---|---|
| Vì sao không xóa missing? | Missing ≤ 1,8%; mỗi biểu đồ chỉ loại missing của cột đang xét để giữ đúng mẫu số |
| Vì sao chia band như vậy? | Ngưỡng có nghĩa kinh doanh (6 tháng, 1 năm, 2 năm); band thể hiện trong `prepare_viz_data.py` |
| Đỉnh tháng 11 có chắc là hết hợp đồng? | Là giả thuyết hợp lý nhất (dữ liệu không có cột hợp đồng); cần xác nhận với bộ phận kinh doanh |
| Doanh thu bị đe dọa tính thế nào? | Tổng `MonthlyRevenue` của nhóm × churn rate của nhóm; là doanh thu, không phải lợi nhuận |
| Vì sao bỏ nhóm "Sai gói"? | Sau khi tách các nhóm ưu tiên trước, nhóm này churn dưới trung bình (24%) nên không đáng can thiệp riêng |
| Mô hình tốt cỡ nào? | ROC-AUC ≈ 0,68 (bản 10 cột 0,67; Logistic 0,61; LightGBM ngang): đủ để xếp hạng ưu tiên, chưa đủ để dự đoán từng khách. Trần của bộ dữ liệu khoảng 0,68–0,70 |
