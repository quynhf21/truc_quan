# Kiểm tra UI/UX dashboard Cell2Cell

Ngày kiểm tra: 30/10/2026. Phạm vi: Dash local và bản Pages hiện có, không sửa giao diện trong lượt audit.

## Trạng thái sau khắc phục

Tám lỗi UI-01–UI-08 đã được xử lý theo hướng dẫn UI/UX Pro Max. Đã chạy lại 12 view Dash và 9 view Pages tại 1440/768/375px; không ghi nhận document overflow hoặc text vượt khung chart. Decile được kiểm tra từ calcdata trên trình duyệt và có đúng thứ tự 1–10 ở cả ba chiều rộng.

- Tiêu đề chart chuyển thành caption HTML có thể xuống dòng; Graph có chiều cao rõ ràng và resize theo container.
- Chart/policy chuyển một cột ở tablet; sidebar thành navigation ngang trên màn hình nhỏ. Nhãn dài ở biểu đồ phù hợp được chuyển sang bar ngang.
- Menu Dash/Pages có active và aria-current. Pages đồng bộ route khi hashchange, Back/Forward.
- Label bộ lọc Dash được liên kết với trigger và giá trị đang chọn; bốn control mở bằng Enter và đóng bằng Escape.
- Nút reset cao 44px; chữ ghi chú chuyển sang #526777 trên nền trắng và đã đo đạt 4,5:1.
- Cỡ chữ nội dung/ghi chú được tăng; policy title và badge xếp dọc, brand mark không bị co.
- Filter/reset tiếp tục đối soát đúng 14.654 → 51.047 khách.

Ảnh mới: [Overview tablet](work/build/ui-audit-after/dash-overview-768.png), [Risk desktop](work/build/ui-audit-after/dash-risk-1440.png), [Risk mobile Pages](work/build/ui-audit-after/pages-risk-375.png). Số đo mới và regression nằm trong `work/build/ui-audit-after/`.

`work/dashboard/verify_ui.py` kiểm tra số đo đã lưu, chart decile thực, nhãn/keyboard và contrast. Cài dependency tùy chọn từ `work/dashboard/requirements-ui.txt` để chạy lại audit.

## Skill và phương pháp

- Đã cài `ui-ux-pro-max` từ https://github.com/nextlevelbuilder/ui-ux-pro-max-skill tại `C:/Users/Admin/.codex/skills/ui-ux-pro-max`.
- Đã đọc SKILL.md, quick-reference.md, pro-rules.md; áp dụng các mục web về responsive, active navigation, contrast, labels và charts. Không áp tiêu chuẩn native mobile một cách máy móc cho web.
- Đã chạy search về responsive dashboard overflow, navigation current page và bar comparison. Chọn kết quả Compare Categories/Bar Chart phù hợp, không dùng các kết quả 3D/radar không khớp dashboard.
- Công cụ browser/computer-use không khởi tạo được Node runtime; audit thực tế dùng Playwright với Microsoft Edge headless có sẵn.
- Dash: 4 route × 3 viewport (1440×1000, 768×1024, 375×812). Pages: 3 trang × 3 chiều rộng (1440, 768, 375). Thêm ca filter/reset và browser Back.
- Skill là hướng dẫn review, không phải công cụ tự phát hiện mọi lỗi. Kết luận dưới đây dựa trên ảnh, DOM, số đo và code.

## Lỗi cần sửa

| ID | Ưu tiên | Lỗi và bằng chứng | Vị trí / hướng sửa |
|---|---|---|---|
| UI-01 | P1 | Risk decile Dash xếp `1,10,2,3,…,9`. Ảnh mobile cho thấy cột 54% nằm thứ hai, dễ khiến người xem hiểu sai phân tầng. | `work/dashboard/dashboard.py:103` chuyển khóa nhóm thành string; `:211` sort string. Giữ decile numeric hoặc đặt category order 1–10. |
| UI-02 | P1 | Tablet 768px vẫn có sidebar 190px và 2 cột chart. Chart chỉ rộng khoảng 200px: tiêu đề reason/usage/calibration bị cắt; giá trị 4930 vượt vùng chart; nhãn tenure bị xoay dọc. DOM xác nhận text vượt khung, ảnh xác nhận clipping. | `work/dashboard/assets/style.css` breakpoint 760px quá muộn cho panel-grid; `dashboard.py:54` margin/height cố định. Chuyển chart một cột sớm hơn, responsive margin/title và ưu tiên bar ngang cho nhãn dài. |
| UI-03 | P1 | Pages browser Back không cập nhật nội dung: đang Strategy → Back → URL `#risk`, H1 vẫn “Can thiệp nào đáng thử?”, active nav vẫn Strategy. | `work/dashboard/pages_src/app.js:168` đổi hash khi click nhưng không có hashchange/popstate để cập nhật page/render. |
| UI-04 | P2 | Dash không đánh dấu menu hiện tại. Cả bốn nav đều class `nav-item`, không có active hoặc aria-current trên tất cả route đã kiểm tra. | `dashboard.py:310` trở đi; thêm state theo route và `aria-current="page"`, CSS active rõ ràng. |
| UI-05 | P2 | Bốn label bộ lọc có htmlFor rỗng, không bọc control. Dropdown được đặt tên qua nội dung giá trị “Tất cả”, không liên kết với TENURE/WEB CAPABILITY/VALUE TIER/RISK DECILE. | `dashboard.py:320`–`:323`; liên kết ID nhãn và control bằng cơ chế accessible-name phù hợp với Dash Dropdown đang dùng. |
| UI-06 | P2 | Chữ phụ trên nền trắng có contrast thấp: KPI note #8294a2 ≈3,13:1; footer #8b9ca8 ≈2,83:1; topbar #88a0af ≈2,73:1; policy detail #8799a7 ≈2,94:1. Đây đều là text nhỏ, cần 4,5:1 theo checklist skill. | Hai file CSS Dash/Pages; dùng token secondary text đủ tương phản và kiểm tra màu thực tế sau sửa. |
| UI-07 | P2 | Nút reset Dash chỉ cao 17px, font 11px ở desktop/tablet/mobile. Nhỏ hơn mục tiêu web 24 CSS px không có ngoại lệ được chứng minh; không thuận tiện khi chạm. | `.reset-button`; tăng hit area/padding/min-height, giữ focus indicator. Không coi 44px native là điều kiện WCAG mặc định của web. |
| UI-08 | P2 | Phần lớn note/body phụ 10–12px; tablet policy title bị ép nhiều dòng trong card nhỏ, icon brand bị co. Nội dung đọc khó khi thuyết trình và trên màn hình hẹp. | CSS typography, `.brand-mark` cần chống co; `.policy-grid`/`.policy-head` cần breakpoint/wrap phù hợp. |

P1: ảnh hưởng cách hiểu dữ liệu hoặc tương tác chính. P2: ảnh hưởng khả năng đọc, định hướng và accessibility.

## Các kiểm tra đã đạt

- Dash 12/12 lượt mở route có H1 và chart/nội dung; không ghi nhận JavaScript pageerror.
- Không đo được overflow ngang toàn document trong 12 lượt Dash. Điều này không loại trừ clipping bên trong SVG/chart.
- Lọc tenure 12–18 tháng: 14.654 khách, 4.865 churner, churn 33,20%.
- Reset: trở lại 51.047 khách, 14.711 churner, churn 28,82%.
- Bảng capacity/segment có wrapper cuộn ngang trên mobile; việc phải cuộn bảng riêng không được tính là vỡ layout toàn trang.
- Desktop 1440px không ghi nhận text vượt chart trong các phép đo đã dùng.

## Bằng chứng

- [Dash Overview tablet](work/build/ui-audit/dash-overview-768.png)
- [Dash Drivers tablet](work/build/ui-audit/dash-drivers-768.png)
- [Dash Risk mobile — decile sai thứ tự](work/build/ui-audit/dash-risk-375.png)
- [Dash Strategy tablet](work/build/ui-audit/dash-strategy-768.png)
- [Dropdown mở](work/build/ui-audit/dash-dropdown-open.png)
- [Trạng thái sau lọc](work/build/ui-audit/dash-filtered.png)
- [Số đo Dash và filter/reset](work/build/ui-audit/measurements.json)
- [Số đo Pages và Back](work/build/ui-audit/pages-measurements.json)

Ảnh và JSON nằm trong build (đầu ra tái tạo, đang gitignore).

## Chạy lại

Cần server Dash tại 127.0.0.1:8050, Playwright trong .venv và Microsoft Edge Windows. Script Pages tự mở HTTP server tạm ở loopback và đóng sau audit.

```powershell
.\.venv\Scripts\python.exe work\dashboard\audit_ui.py
.\.venv\Scripts\python.exe work\dashboard\audit_pages_ui.py
```

Audit script không sửa mart, không huấn luyện và không publish. Chưa kiểm tra screen reader thực, mọi tổ hợp filter, zoom 200%, mọi kích thước màn hình hoặc hiệu năng máy người dùng. Các kết quả này không thay thế kiểm định WCAG toàn diện.
