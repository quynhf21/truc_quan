# Cách đọc và chạy notebook

Chọn kernel Python của `.venv`. Mỗi notebook đã lưu output thực thi gồm bảng, nhận xét và biểu đồ PNG inline; không cần chạy lại chỉ để xem kết quả.

1. **01_data_preparation_and_eda.ipynb**: import → kiểm tra đường dẫn → nạp raw → hợp đồng ID/target → EDA target/missing → chuẩn hóa → kiểm tra → EDA numeric/missing/âm → tạo band → xuất và xác nhận manifest.
2. **02_analysis_and_visualization.ipynb**: import → đường dẫn → xác nhận processed layer → công thức → bảy phần phân tích risk/reach → nhận xét từng phần → xuất bảng đối soát.
3. **03_model_training_and_evaluation.ipynb**: import → xác nhận processed → cấu hình → X/y → OOF/inner tuning → metric so baseline → ROC/PR → decile/calibration → capacity/gain → phân khúc/policy → xuất và đọc lại kiểm tra.

Chạy 01 trước khi chạy lại 02 hoặc 03. Sau đó 02 và 03 có thể chạy riêng bằng **Restart Kernel → Run All**; chúng không chia sẻ biến trong bộ nhớ. Đường dẫn tương đối hỗ trợ cả project root và thư mục notebook. Nếu raw, QA hoặc processed đã đổi, cần chạy lại 01 để tạo manifest mới.

Từ project root:

```powershell
.\.venv\Scripts\python.exe work\pipeline\run_all.py
```

Chạy từng notebook (mỗi lệnh tạo một kernel mới và lưu output):

```powershell
.\.venv\Scripts\python.exe work\pipeline\run_all.py --only 01
.\.venv\Scripts\python.exe work\pipeline\run_all.py --only 02
.\.venv\Scripts\python.exe work\pipeline\run_all.py --only 03
```

Thêm `--cwd project` để kiểm tra notebook khi working directory là project root. Mặc định working directory là `work/pipeline/`.

```powershell
.\.venv\Scripts\python.exe work\pipeline\verify_notebooks.py
.\.venv\Scripts\python.exe work\dashboard\verify.py
```

`verify_notebooks.py` kiểm tra execution count, lỗi, output bảng/biểu đồ; đồng thời thử dữ liệu hợp lệ, thiếu manifest/processed, raw/QA/parquet bị đổi và manifest chưa PASS trong fixture riêng.

Phần modeling (v2) dùng 52 cột nguồn, depth 4/6, tối đa 1500 vòng; cấu hình CPU 4 threads được in trong notebook. Kết quả mới nhất nằm trong output notebook 03 và `work/build/model_metrics.json`; không ép metric bằng kết quả lịch sử. So sánh với Logistic regression và LightGBM nằm ở `work/experiments/compare_models.py`.
