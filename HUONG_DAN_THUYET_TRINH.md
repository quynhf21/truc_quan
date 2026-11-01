# Kịch bản thuyết trình — thống nhất 10 biến mô hình

Mô hình, notebook 04 và dashboard dùng cùng 10 predictor. `Churn` là nhãn; mã khách chỉ để đối soát. Các band và điểm rủi ro được suy ra từ bộ biến này. CSV nguồn được giữ nguyên, số cột trong CSV không phải số predictor được chọn.

## 2.2. Phân tích thời gian sử dụng và thiết bị

- `MonthsInService`: C05/C05b là đường tỷ lệ và cột chồng số khách theo tháng; C14 là treemap số khách rời bỏ theo nhóm thời gian sử dụng.
- `CurrentEquipmentDays`: C03 phân bố tuổi máy, C04 box plot, C06 bar theo tuổi thiết bị, C07 kết hợp với thời gian sử dụng.
- `HandsetWebCapable`: C09 grouped bar Có/Không hỗ trợ truy cập web.
- Đỉnh quanh một năm là tín hiệu quan sát, chưa xác nhận nguyên nhân hết hợp đồng.

## 2.3. Phân tích doanh thu, cước phí và mức sử dụng

- `MonthlyRevenue`: C04 box plot và C04b histogram chồng giữa nhóm rời bỏ/ở lại.
- `TotalRecurringCharge`: C04c histogram chồng, C04d bar tỷ lệ rời bỏ theo nhóm phí có baseline toàn mẫu.
- `MonthlyMinutes`: C12 bubble theo nhóm phút gọi, kích thước là số khách, trục dọc là tỷ lệ rời bỏ.

## 2.4. Phân tích biến động mức sử dụng và doanh thu

- `PercChangeMinutes`: C10 bar theo các nhóm Giảm, Không đổi, Tăng.
- `PercChangeRevenues`: C11 giữ cùng form bar và baseline.
- Chỉ phân nhóm theo dấu của giá trị nguồn; chưa gọi đây là phần trăm thay đổi khi chưa xác nhận đơn vị. Đọc số khách và nhận xét được tính lại trong notebook.

## 2.5. Phân tích cuộc gọi giờ cao điểm

- `PeakCallsInOut`: C13 bar ngang theo nhóm số cuộc gọi giờ cao điểm, kèm churn trung bình.
- Đây là số cuộc gọi giờ cao điểm, không phải số lần liên hệ CSKH hoặc hoạt động giữ chân.

## 2.6. Phân tích hạng tín dụng khách hàng

- `CreditRating`: C16 giữ đúng thứ tự hạng 1–7. Không suy diễn thu nhập, nghề nghiệp hoặc hôn nhân từ hạng tín dụng.

## 2.7. Phân tích tương quan giữa các biến

- C18 có đúng 10 predictor cộng nhãn rời bỏ. Hai biến phân loại được mã hóa rõ trong notebook.
- Tương quan tuyến tính không phải mức độ quan trọng trong CatBoost và không chứng minh nhân quả.

## Mô hình và hành động

- Mô hình đã chạy dùng 10 biến: ROC-AUC ngoài mẫu 0,6725, AP 0,4549, lift top 10% toàn nguồn 1,88×. Việc thay biểu đồ không huấn luyện lại hoặc đổi điểm.
- C19 dùng điểm đó để phân tầng và đánh giá phạm vi liên hệ. C20/C20b/C20c giữ nguyên các nhóm Hết hợp đồng, Máy cũ, Rủi ro cao theo mô hình và Ổn định.
- Chính sách cần thử nghiệm đối chứng; doanh thu tháng bị đe dọa chưa phải số tiền chắc chắn giữ được.

Các biểu đồ chỉ dùng biến ngoài mô hình đã được bỏ khỏi notebook và dashboard; không giữ ô thông báo trống.
