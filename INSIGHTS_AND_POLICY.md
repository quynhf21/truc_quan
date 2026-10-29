# Insight và chiến lược đề xuất cho bản demo

Các số dưới đây từ `data/cell2celltrain.csv` qua pipeline hiện tại. Đây là các **liên hệ quan sát**; nhóm can thiệp là giả thuyết cần kiểm chứng bằng treatment/control. Mỗi dashboard filter sẽ tính lại mẫu số, vì vậy số trên trang sau lọc có thể khác bảng toàn nguồn này.

| Câu hỏi | Bằng chứng toàn nguồn | Diễn giải và hành động có thể thử |
|---|---|---|
| Quy mô churn | 14.711/51.047 = 28,82% | Churn đủ lớn để cần ưu tiên nguồn lực. |
| Tenure | 12–18 tháng: 4.865/14.654 = 33,20%; 6–11 tháng: 3.421/14.238 = 24,03% | Thử check-in trước hoặc trong cửa sổ 12–18 tháng. Không gán cho hết ưu đãi vì thiếu dữ liệu hợp đồng. |
| Thiết bị | >730 ngày: 1.855/5.141 = 36,08%; ≤180 ngày: 2.238/9.759 = 22,93% | Device review hoặc education/upgrade pilot có cả risk và reach. Giá trị âm được gắn nhãn QA riêng. |
| Web capability | `No`: 1.868/5.001 = 37,35%; `Yes`: 12.843/46.046 = 27,89% | Kiểm tra tương tác với tuổi thiết bị và tenure trước khi chọn treatment. |
| Usage | ≤150 minutes: 4.044/12.214 = 33,11%; >500 minutes: 5.132/19.452 = 26,38% | Low-engagement là nhóm đáng khám phá; usage thấp không tự chứng minh không hài lòng. |
| Thay đổi minutes | Nguồn ≤-83: 4.090/12.728 = 32,13%; 0–66: 2.572/10.178 = 25,27% | Thử re-engagement sau khi xác minh đơn vị và lead time. 367 trường hợp thiếu có churn cao và phải hiện riêng. |
| Phí định kỳ | >60: 2.250/9.362 = 24,03%; ≤30: 4.690/14.008 = 33,48% | Không diễn giải rằng tăng phí sẽ làm giảm churn. Rule charge cao + usage thấp hiện chỉ có 319 khách, 23,51% churn nên chưa đủ cơ sở đưa lên pilot ưu tiên. |

## Thứ tự đề xuất cho pilot

1. **Device review:** tập trung risk decile ≥7 có tín hiệu thiết bị. Thử tư vấn/hướng dẫn trước; upgrade/trade-in cần kiểm soát chi phí trợ giá và khiếu nại.
2. **Usage decline:** risk decile ≥7 và mức thay đổi minutes nguồn ≤-83. Thử re-engagement hoặc plan review; đo opt-out/contact fatigue.
3. **Lifecycle check-in:** risk decile ≥7 trong 12–18 tháng. Thử giải thích gói, kiểm tra trải nghiệm và hỗ trợ; đo số lần liên hệ.

Price/plan mismatch được giữ ở mục **khám phá thêm**. “Rà soát chung” là fallback, chưa phải treatment hàng loạt. Các nhóm reason code loại trừ nhau theo thứ tự rule trong pipeline; tín hiệu nguồn có thể chồng lắp. Mọi pilot cần randomize trong cùng nhóm eligibility, khóa outcome window, đo incremental churn reduction và guardrail trước khi scale.
