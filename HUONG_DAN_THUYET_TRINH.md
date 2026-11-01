# Kịch bản thuyết trình — phạm vi 10 biến

Mạch kể: **Vấn đề → Thiết bị và mức sử dụng → Rủi ro → Hành động**. Mở notebook 04 và dashboard tại http://127.0.0.1:8050/.

## 1. Giới thiệu và xử lý dữ liệu

- CSV nguồn giữ nguyên; mô hình và EDA chỉ chọn đúng 10 predictor đã thống nhất. Mã khách phục vụ đối soát, `Churn` là nhãn, các band và điểm rủi ro là đại lượng suy ra.
- Các cột gồm thời gian sử dụng, tuổi thiết bị, hỗ trợ web, doanh thu tháng, phí định kỳ, hạng tín dụng, phút gọi, hai mức thay đổi và cuộc gọi giờ cao điểm.
- Notebook tự tính số dòng trước/sau xử lý và số giá trị thiếu. Giữ số âm hợp lệ ở hai mức thay đổi; loại số âm bất thường ở các đại lượng không thể âm.

## 2. Tổng quan và thiết bị

- C01 cho biết tỷ lệ rời bỏ và quy mô mẫu; đọc số hiển thị của lần chạy hiện tại.
- C05 giữ đường tỷ lệ và cột chồng số khách theo tháng sử dụng. Đỉnh quanh một năm là tín hiệu cần khảo sát, chưa xác nhận nguyên nhân hết hợp đồng.
- C04 chỉ còn box plot tuổi thiết bị và doanh thu. C06/C07 giữ nhóm tuổi máy và kết hợp với thời gian sử dụng.
- C09 giữ grouped bar Có/Không hỗ trợ web; không còn nhóm máy tân trang.

## 3. Mức sử dụng và phân bố

- C12 vẫn là bubble: nhóm phút gọi trên trục ngang, tỷ lệ rời bỏ trên trục dọc, kích thước là số khách. Chiều phân màu ngoài phạm vi đã bỏ.
- C14 vẫn là treemap, chỉ còn cấp thời gian sử dụng: diện tích cho biết số khách rời bỏ, màu cho biết tỷ lệ.
- C16 so sánh hạng tín dụng. C18 thể hiện tương quan của 10 predictor và nhãn rời bỏ, có ghi rõ cách mã hóa hai biến phân loại.

## 4. Mô hình và hành động

- CatBoost 10 biến: ROC-AUC ngoài mẫu 0,6725, AP 0,4549, lift top 10% toàn nguồn 1,88×. C19 dùng đúng điểm đã chạy lại.
- C20 chỉ còn các nhóm Hết hợp đồng, Máy cũ, Rủi ro cao theo mô hình và Ổn định. Điều kiện và số liệu cụ thể nằm trong bảng phân khúc và báo cáo insight hiện hành.
- So sánh C20, C20b và C20c: vị trí rủi ro/giá trị, quy mô doanh thu bị đe dọa và tỷ lệ rời bỏ là ba góc nhìn khác nhau.
- Chính sách là đề xuất; cần thử nghiệm đối chứng để đo hiệu quả giữ chân.

## 5. Các vị trí không còn biến phù hợp

C08, C10, C11, C13, C15 và C17 giữ ô thông báo vì toàn bộ biến phân nhóm cũ nằm ngoài bộ 10. Không trình bày chúng như kết quả phân tích và không tự dùng biến khác để thay thế.

## Câu hỏi thường gặp

| Câu hỏi | Trả lời |
|---|---|
| Vì sao CSV vẫn có nhiều cột? | Giữ nguyên dữ liệu nguồn; bảng phân tích chỉ chọn đúng 10 predictor, ID/nhãn và các đại lượng suy ra. |
| Mười biến hay mười một biến ở C18? | Mười predictor cộng nhãn rời bỏ để tính tương quan; nhãn không vào mô hình. |
| Vì sao một số ô không còn hình? | Sau khi bỏ biến ngoài bộ 10, ô đó không còn biến phân nhóm hợp lệ. Giữ vị trí và thông báo thay vì tạo nội dung thay thế. |
| Mô hình có đổi sau khi thu gọn EDA? | Không. Chỉ bỏ biến ngoài phạm vi khỏi biểu đồ và các quy tắc phụ thuộc chúng. |
| Doanh thu bị đe dọa tính thế nào? | Tổng doanh thu tháng của nhóm × tỷ lệ rời bỏ; chưa phải lợi nhuận hay số tiền chắc chắn giữ được. |
