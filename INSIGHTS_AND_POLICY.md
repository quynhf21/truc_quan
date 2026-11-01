# Insight và chính sách giữ chân khách hàng

Nguồn: 51.047 khách; sau khi loại 85 dòng có số âm bất thường, tập EDA còn **50.962 khách**, **14.695 khách rời bỏ (28,84%)**.

Mô hình **cell2cell-catboost-oof-10-v1** chỉ dùng **10 biến đầu vào**. Các biến khảo sát bổ sung trong EDA không phải predictor của mô hình.

## Các phát hiện từ dữ liệu hiện hành

| Biểu đồ | Nhận xét tính từ dữ liệu |
|---|---|
| [C01](reports/figures/C01_ty_le_churn.png) | Cứ khoảng 3,5 khách thì có 1 khách rời bỏ |
| [C05](reports/figures/C05_vong_doi.png) | Tỷ lệ rời bỏ vọt lên 44,6% ở tháng 11: thời điểm hết hợp đồng 1 năm |
| [C06](reports/figures/C06_tuoi_thiet_bi.png) | Máy “>730 ngày” có tỷ lệ rời bỏ 36,1%, gấp 1,6 lần nhóm “≤180 ngày” |
| [C07](reports/figures/C07_heatmap_tenure_thiet_bi.png) | Điểm nóng: >36 tháng + máy >730 ngày có tỷ lệ rời bỏ 40,3% |
| [C08](reports/figures/C08_retention_funnel.png) | Nhận ưu đãi giữ chân rồi vẫn có tỷ lệ rời bỏ 41,2%: chương trình hiện tại không giữ được khách |
| [C10](reports/figures/C10_goi_cskh.png) | Số cuộc gọi CSKH “0” có tỷ lệ rời bỏ 30,7%, gấp 1,3 lần nhóm “>10” |
| [C11](reports/figures/C11_cuoc_goi_rot.png) | Số cuộc gọi rớt “0” có tỷ lệ rời bỏ 34,3%, gấp 1,2 lần nhóm “>40” |
| [C13](reports/figures/C13_vung.png) | Vùng SEA có tỷ lệ rời bỏ 34,2%, cao hơn STL 11,9 điểm % |
| [C18](reports/figures/C18_tuong_quan.png) | Tương quan với rời bỏ cao nhất: tuổi thiết bị (r = 0,10) |
| [C19b](reports/figures/C19b_gain_curve.png) | Liên hệ 20% khách rủi ro nhất bắt được 34% số khách sẽ rời bỏ |

## Kết quả mô hình 10 biến

Đánh giá ngoài mẫu trên 51.047 khách nguồn: ROC-AUC **0.6725**, AP **0.4549**, lift top 10% **1,9×**, recall top 20% **33,6%**.

Trong tập EDA sau xử lý: lift top 10% **1,9×**, gain top 20% **33,6%**. Hai tập có mẫu số khác nhau do bước loại số âm bất thường.

## Phân khúc và chính sách

| Phân khúc | Số khách | Tỷ lệ rời bỏ | Doanh thu tháng bị đe dọa | Chính sách đề xuất | KPI |
|---|---:|---:|---:|---|---|
| Đã báo động | 1.739 | 45,0% | $47,8 nghìn | Thiết kế lại ưu đãi; chuyên viên cấp cao xử lý trong 24 giờ; ghi nhận lý do rời bỏ | Tỷ lệ rời bỏ sau 60 ngày; tỷ lệ nhận ưu đãi |
| Hết hợp đồng | 11.143 | 35,5% | $229,9 nghìn | Chăm sóc từ tháng 10; ưu đãi gia hạn 12 tháng trước tháng 11 | Tỷ lệ gia hạn; tỷ lệ rời bỏ tháng 11–13 |
| Máy cũ | 6.837 | 35,5% | $104,8 nghìn | Đổi máy trả góp hoặc trợ giá gắn cam kết 12 tháng; ưu tiên máy không hỗ trợ mạng | Tỷ lệ nhận đổi máy; tỷ lệ rời bỏ sau 90 ngày; chi phí giữ một khách |
| Rủi ro cao (mô hình) | 4.950 | 42,2% | $135,9 nghìn | Khảo sát hài lòng; tư vấn gói phù hợp; ưu đãi cá nhân hóa | Tỷ lệ rời bỏ sau 90 ngày; doanh thu giữ được |
| Ổn định | 26.293 | 20,7% | $334,4 nghìn | Duy trì chất lượng và chương trình khách hàng thân thiết | Theo dõi định kỳ |

Các nhóm cần can thiệp gồm **24.669 khách**; doanh thu tháng bị đe dọa **$518,4 nghìn**.

Doanh thu tháng bị đe dọa = tổng doanh thu tháng của nhóm × tỷ lệ rời bỏ; chưa phải doanh thu chắc chắn giữ được. Dữ liệu tại một thời điểm không chứng minh nhân quả; chính sách cần thử nghiệm đối chứng.
