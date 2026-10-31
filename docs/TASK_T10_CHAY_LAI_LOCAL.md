# T10 — Chạy lại toàn bộ dự án trên máy Windows và đối chiếu kết quả

Mục tiêu: xác nhận bản trên master (branch `t10-chay-lai-local` chỉ thêm tài liệu, code giống master) (sau T9 và sau khi sửa notebook 01) chạy được trên laptop Windows của nhóm
và ra **đúng số** như lần chạy trên VPS Linux. Task này **chỉ chạy và báo cáo**, không sửa code hay tài liệu.

## 1. Chuẩn bị

```powershell
cd D:\project\iu_anhHuy
git fetch origin
git checkout t10-chay-lai-local     # branch của PR này = master + file hướng dẫn
git pull
py -3.11 -m venv .venv                 # bỏ qua nếu đã có .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r work/requirements.txt
```

Ghi lại phiên bản đã cài: `python -m pip show catboost lightgbm pandas scikit-learn | findstr "Name Version"`.

## 2. Chạy theo thứ tự

Mỗi lệnh phải kết thúc không lỗi. Lỗi ở lệnh nào thì **dừng lại, dán nguyên thông báo lỗi**, không tự sửa code.

| # | Lệnh | Thời gian | Dòng phải thấy |
|---|---|---|---|
| 1 | `python work/pipeline/run_all.py` | 8–15 phút | `PIPELINE PASS` |
| 2 | `python work/pipeline/verify_notebooks.py` | 1–2 phút | 3 dòng `AUDIT PASS`, 14 dòng `GUARD PASS` |
| 3 | `cd work/dashboard; python verify.py; cd ../..` | vài giây | `PASS: source reconciliation...` |
| 4 | `python work/viz/prepare_viz_data.py` | vài giây | `51.047 dòng`, `Churn: 14.711 khách (28,82%)` |
| 5 | `jupyter nbconvert --to notebook --execute --inplace work/viz/04_eda_truc_quan.ipynb` | ~1 phút | `Writing ... bytes` |
| 6 | `python work/viz/smoke_test.py` | vài giây | toàn bộ `OK` |
| 7 | `python work/experiments/compare_models.py --quick` | ~2 phút | 2 dòng kết quả A và D |
| 8 | `python work/dashboard/dashboard.py` → mở http://127.0.0.1:8050/ | — | 4 trang hiện, không lỗi |

Bước 8: lọc **Thời gian sử dụng = 13–18 tháng** phải ra **11.917 khách, churn 31,6%**; bấm **Xóa lọc** về 51.047. Ctrl+C để tắt.

## 3. Đối chiếu số

Đọc số từ `work/build/model_metrics.json`, `work/build/preparation_manifest.json` và output bước 4, 7.

| Chỉ số | Kết quả trên VPS | Cho phép lệch |
|---|---|---|
| `source_sha256` trong manifest | `3f6b8ff0b8e8f5975aa0de9f1f54967e6c8cb867a9bec6cbb64f4c8990f9a645` | phải khớp tuyệt đối |
| `processed_sha256` trong manifest | `28b181714a82714295d35cfd1906d0bbd252839a3a790fb8df6a6cbfd6a3875e` | có thể khác (phiên bản pyarrow), báo lại |
| `model_version` | `cell2cell-catboost-oof-v2` | khớp tuyệt đối |
| Số phần tử `features` | 52 | khớp tuyệt đối |
| `roc_auc` | 0,6816 | ±0,003 |
| `pr_auc` | 0,4624 | ±0,005 |
| `capacity_10.lift` | 1,93 | ±0,05 |
| Số khách theo `ActionSegment` (bước 4) | Đã báo động 1.745 · Hết hợp đồng 11.161 · Máy cũ 6.837 · Rủi ro cao 5.576 · Ổn định 25.728 | 3 nhóm đầu khớp tuyệt đối; 2 nhóm cuối ±300 |
| compare `--quick` A / D | 0,672 / 0,681 | ±0,003 |

Nếu `source_sha256` khác: nhiều khả năng Git đã đổi xuống dòng của `data/cell2celltrain.csv` sang CRLF.
Kiểm tra `git config core.autocrlf` và báo lại. **Không** sửa file CSV.

## 4. Sau khi chạy

`git status` sẽ thấy các notebook và ảnh `reports/` thay đổi, vì output, thời gian chạy và đường dẫn kiểu Windows được ghi lại.

- Nếu **tất cả** bước 2 PASS và số ở mục 3 nằm trong mức cho phép: **không commit gì**, khôi phục bằng
  `git checkout -- work/ reports/`.
- Nếu có lệch: cũng khôi phục như trên, chỉ báo cáo.

## 5. Báo cáo

Trả lời theo mẫu:

```
T10 — <PASS | FAIL>
Phiên bản: python ..., catboost ..., lightgbm ..., pandas ..., scikit-learn ...
Bước 1–8: <PASS/FAIL từng bước; dán lỗi nếu có>
Đối chiếu: roc_auc=..., pr_auc=..., lift10=..., segment=..., compare A/D=..., source_sha256 khớp: có/không
Ghi chú: <điểm lạ, cảnh báo đáng chú ý>
```
