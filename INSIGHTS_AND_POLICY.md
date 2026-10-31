# Insight và chính sách giữ chân khách hàng

Nguồn: `data/cell2celltrain.csv`, 51.047 khách, 14.711 khách rời bỏ (**28,8%**). Số liệu tính bằng
`work/viz/04_eda_truc_quan.ipynb`, ảnh biểu đồ ở `reports/figures/`. Đây là các **quan hệ quan sát** trên một snapshot,
chưa chứng minh nhân quả.

## 10 insight

| # | Phát hiện | Số liệu | Biểu đồ | Hành động |
|---|---|---|---|---|
| 1 | Churn ở mức cao, thiệt hại lớn | 28,8% khách rời bỏ; doanh thu tháng của nhóm này ≈ $849 nghìn (28,4% tổng doanh thu tháng) | [C01](reports/figures/C01_ty_le_churn.png) | Ưu tiên ngân sách giữ chân |
| 2 | **Đỉnh hết hợp đồng** | Tháng 7–9 churn ~15%, **tháng 11 lên 44,6%**, tháng 12 lên 40,2%, sau tháng 18 về mức trung bình | [C05](reports/figures/C05_vong_doi.png) | Liên hệ chủ động từ tháng 10 |
| 3 | Máy càng cũ churn càng cao | ≤180 ngày 22,9% → >730 ngày **36,1%** (gấp 1,6 lần); là biến numeric tương quan mạnh nhất (r = 0,10) | [C06](reports/figures/C06_tuoi_thiet_bi.png), [C18](reports/figures/C18_tuong_quan.png) | Chương trình đổi máy |
| 4 | Tenure × máy cộng dồn | Khách > 36 tháng dùng máy > 2 năm churn 40,3% (máy mới chỉ 15,5%); khách 7–12 tháng dùng máy 1–2 năm churn 39,4% | [C07](reports/figures/C07_heatmap_tenure_thiet_bi.png) | Đổi máy cho cả khách trung thành |
| 5 | Máy đời cũ | Không hỗ trợ web 37,4% so với 27,9%; máy tân trang 32,2% so với 28,3% | [C09](reports/figures/C09_dac_diem_thiet_bi.png) | Ưu tiên khách máy không web |
| 6 | **Ưu đãi giữ chân hiện tại không hiệu quả** | 1.745 khách gọi retention team churn 45,0%; 881 khách đã nhận ưu đãi vẫn churn 41,1% | [C08](reports/figures/C08_retention_funnel.png) | Thiết kế lại ưu đãi |
| 7 | Khách im lặng nguy hiểm hơn khách phàn nàn | Không gọi CSKH churn 30,7% (gọi > 10 lần: 23,2%); không có cuộc gọi rớt nào (ít dùng) churn 34,3% | [C10](reports/figures/C10_goi_cskh.png), [C11](reports/figures/C11_cuoc_goi_rot.png) | Theo dõi mức sử dụng, không chờ khiếu nại |
| 8 | Lệch gói cước | Dùng ≤150 phút churn 33,1%; vượt gói > 200 phút churn 32,7%; dùng nhiều mà không vượt gói ~22% | [C12](reports/figures/C12_goi_cuoc.png) | Tư vấn đúng gói |
| 9 | Địa lý | SEA 34,2%, MIA 33,1% so với STL 22,3% (chênh 11,9 điểm %); 20/53 vùng chiếm 80% churner; NYC mất nhiều khách nhất (11,1%) | [C13](reports/figures/C13_vung.png), [C14](reports/figures/C14_treemap_vung.png), [C15](reports/figures/C15_pareto_vung.png) | Bắt đầu ở 20 vùng Pareto |
| 10 | Khách tín dụng tốt dễ đi; nhân khẩu học ít phân biệt | Hạng 1–3 churn 30,5% so với 24,9% ở hạng 4–7; thu nhập, hôn nhân chênh 3–4 điểm % | [C16](reports/figures/C16_tin_dung.png), [C17](reports/figures/C17_nhan_khau_hoc.png) | Chọn khách theo hành vi, không theo nhân khẩu |

Mô hình rủi ro có sẵn (CatBoost, notebook 03): decile 10 churn 54,4%. Liên hệ 10% khách rủi ro nhất bắt được 19% churner
(lift 1,9×), liên hệ 20% bắt được 34% ([C19](reports/figures/C19b_gain_curve.png)).

## Phân khúc hành động

Rule xét theo thứ tự ưu tiên, khách khớp rule đầu tiên sẽ thuộc nhóm đó ([C20](reports/figures/C20_phan_khuc.png)):

| Ưu tiên | Phân khúc | Điều kiện | Khách | Churn | Doanh thu/tháng bị đe dọa* | Chính sách đề xuất | KPI |
|---|---|---|---:|---:|---:|---|---|
| 1 | Đã báo động | Đã gọi retention team | 1.745 | 45,0% | $48,1 nghìn | Thiết kế lại ưu đãi; chuyên viên cấp cao xử lý trong 24h; ghi nhận lý do rời bỏ | Churn 60 ngày, tỷ lệ nhận ưu đãi |
| 2 | Hết hợp đồng | Tháng sử dụng 10–13 | 11.161 | 35,5% | $230,1 nghìn | Gọi chăm sóc từ tháng 10; ưu đãi gia hạn 12 tháng trước tháng 11 | Tỷ lệ gia hạn, churn tháng 11–13 |
| 3 | Máy cũ | Máy > 730 ngày, hoặc ≥ 365 ngày và không hỗ trợ web | 6.837 | 35,5% | $104,8 nghìn | Đổi máy trả góp/trợ giá gắn cam kết 12 tháng | % nhận đổi máy, churn 90 ngày, chi phí/khách giữ được |
| 4 | Rủi ro cao (mô hình) | Còn lại, risk decile 8–10 | 4.879 | 42,4% | $135,0 nghìn | Khảo sát hài lòng, tư vấn gói, ưu đãi cá nhân hóa (doanh thu/khách cao nhất: $65,7) | Churn 90 ngày, doanh thu giữ được |
| — | Ổn định | Còn lại | 26.425 | 20,7% | — | Duy trì, chương trình thân thiết | Theo dõi |

\* Doanh thu/tháng của nhóm × churn rate của nhóm. Đây là mức kỳ vọng, chưa phải lợi nhuận hay CLV.

Tổng cộng 4 nhóm cần can thiệp gồm **24.622 khách** (48%), churn 37,5%, doanh thu bị đe dọa ≈ **$518 nghìn/tháng**.

So với plan ban đầu đã đổi hai điểm, theo số liệu thật:

- Cửa sổ hợp đồng thu hẹp từ 10–18 xuống **10–13 tháng** để bám sát đỉnh tháng 11–12.
- Bỏ nhóm "Sai gói" (vượt gói > 100 phút) và "Im lặng". Sau khi tách các nhóm trước, hai nhóm này churn **thấp hơn** trung bình (24,3% và 25,1%).
  Thay vào đó là nhóm "Rủi ro cao (mô hình)".

## Triển khai

1. Pilot tại 20 vùng chiếm 80% churner, ưu tiên SEA, MIA (rate cao) và NYC, LAX (số lượng lớn).
2. Mỗi phân khúc chia ngẫu nhiên nhóm thử/nhóm đối chứng và khóa trước thời gian đo (60–90 ngày) để đo mức giảm churn thực tế.
3. Mở rộng chính sách nào giảm churn có ý nghĩa và chi phí/khách giữ được thấp hơn doanh thu giữ được.
