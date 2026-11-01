# Insight và chính sách giữ chân khách hàng

Nguồn: 51.047 khách; sau khi loại 85 dòng có số âm bất thường, tập EDA còn **50.962 khách**, **14.695 khách rời bỏ (28,84%)**.

Mô hình **cell2cell-catboost-oof-10-v1** chỉ dùng **10 biến đầu vào**. Mô hình và EDA dùng cùng bộ 10 biến; các band và điểm rủi ro được suy ra từ chúng.

## Các phát hiện từ dữ liệu hiện hành

| Biểu đồ | Nhận xét tính từ dữ liệu |
|---|---|
| [C01](reports/figures/C01_ty_le_churn.png) | Cứ khoảng 3,5 khách thì có 1 khách rời bỏ |
| [C05](reports/figures/C05_vong_doi.png) | Tỷ lệ rời bỏ vọt lên 44,6% ở tháng 11: thời điểm hết hợp đồng 1 năm |
| [C06](reports/figures/C06_tuoi_thiet_bi.png) | Máy “>730 ngày” có tỷ lệ rời bỏ 36,1%, gấp 1,6 lần nhóm “≤180 ngày” |
| [C07](reports/figures/C07_heatmap_tenure_thiet_bi.png) | Điểm nóng: >36 tháng + máy >730 ngày có tỷ lệ rời bỏ 40,3% |
| [C04b](reports/figures/C04b_phan_bo_doanh_thu.png) | Khách rời bỏ có doanh thu tháng ($) trung vị thấp hơn khách ở lại |
| [C04d](reports/figures/C04d_churn_phi_dinh_ky.png) | Phí định kỳ “≤30” có tỷ lệ rời bỏ 33,5%, gấp 1,4 lần nhóm “>60” |
| [C12](reports/figures/C12_muc_su_dung.png) | Nhóm ≤150 phút có tỷ lệ rời bỏ cao nhất (33,1%) |
| [C10](reports/figures/C10_bien_dong_phut_goi.png) | Thay đổi phút gọi “Không đổi” có tỷ lệ rời bỏ 46,9%, gấp 1,8 lần nhóm “Tăng” |
| [C11](reports/figures/C11_bien_dong_doanh_thu.png) | Thay đổi doanh thu “Không đổi” có tỷ lệ rời bỏ 30,7%, gấp 1,1 lần nhóm “Tăng” |
| [C13](reports/figures/C13_goi_gio_cao_diem.png) | Cuộc gọi giờ cao điểm “≤50” có tỷ lệ rời bỏ 30,7%, gấp 1,3 lần nhóm “>300” |
| [C14](reports/figures/C14_treemap_thoi_gian.png) | Nhóm 7–12 tháng có nhiều khách rời bỏ nhất (4.371 khách) |
| [C16](reports/figures/C16_tin_dung.png) | Khách tín dụng tốt (hạng 1–3) có tỷ lệ rời bỏ 30,5%, cao hơn nhóm 4–7 (24,9%) |
| [C18](reports/figures/C18_tuong_quan.png) | Tương quan với rời bỏ cao nhất: tuổi thiết bị (r = 0,10) |
| [C19b](reports/figures/C19b_gain_curve.png) | Liên hệ 20% khách rủi ro nhất bắt được 34% số khách sẽ rời bỏ |

## Kết quả mô hình 10 biến

Đánh giá ngoài mẫu trên 51.047 khách nguồn: ROC-AUC **0.6725**, AP **0.4549**, lift top 10% **1,9×**, recall top 20% **33,6%**.

Trong tập EDA sau xử lý: lift top 10% **1,9×**, gain top 20% **33,6%**. Hai tập có mẫu số khác nhau do bước loại số âm bất thường.

## Phân khúc và chính sách

| Phân khúc | Số khách | Tỷ lệ rời bỏ | Doanh thu tháng bị đe dọa | Chính sách đề xuất | KPI |
|---|---:|---:|---:|---|---|
| Hết hợp đồng | 11.417 | 36,1% | $239,6 nghìn | Chăm sóc từ tháng 10; ưu đãi gia hạn 12 tháng trước tháng 11 | Tỷ lệ gia hạn; tỷ lệ rời bỏ tháng 11–13 |
| Máy cũ | 7.089 | 36,0% | $110,0 nghìn | Đổi máy trả góp hoặc trợ giá gắn cam kết 12 tháng; ưu tiên máy không hỗ trợ web | Tỷ lệ nhận đổi máy; tỷ lệ rời bỏ sau 90 ngày; chi phí giữ một khách |
| Rủi ro cao (mô hình) | 5.253 | 43,4% | $148,0 nghìn | Khảo sát hài lòng; tư vấn gói phù hợp; ưu đãi cá nhân hóa | Tỷ lệ rời bỏ sau 90 ngày; doanh thu giữ được |
| Ổn định | 27.203 | 21,1% | $354,1 nghìn | Duy trì chất lượng và chương trình khách hàng thân thiết | Theo dõi định kỳ |

Các nhóm cần can thiệp gồm **23.759 khách**; doanh thu tháng bị đe dọa **$497,5 nghìn**.

Doanh thu tháng bị đe dọa = tổng doanh thu tháng của nhóm × tỷ lệ rời bỏ; chưa phải doanh thu chắc chắn giữ được. Dữ liệu tại một thời điểm không chứng minh nhân quả; chính sách cần thử nghiệm đối chứng.
