---
name: csv-quality
description: Kiểm tra chất lượng file CSV danh sách công việc (cột task_id, owner, hours) và kiểm tra quá tải công việc theo người bằng script có sẵn, rồi ghi báo cáo Markdown dưới output/. Dùng khi người dùng yêu cầu kiểm tra, rà soát chất lượng dữ liệu CSV, tính tổng giờ hoặc xác định người quá tải.
---

# CSV quality

Kiểm tra chất lượng CSV công việc và xác định người quá tải bằng script, không tự tính bằng mắt hay phán đoán chủ quan.

## Quy tắc ngưỡng giờ (max-hours)

- Tham số `--max-hours` là **bắt buộc** khi chạy script `check_csv.py`.
- **Xác định ngưỡng giờ**:
  - Nếu câu hỏi của người dùng có chứa mốc/ngưỡng giờ (ví dụ: *"người nào vượt 8 giờ?"*, *"vượt 9 giờ"*, *"ngưỡng 8 giờ"*), hãy lấy số giờ đó làm ngưỡng và truyền chính xác vào tham số `--max-hours` (ví dụ: `--max-hours 8`).
  - **Nếu yêu cầu hoàn toàn không cung cấp mốc giờ hay ngưỡng nào** (ví dụ: *"Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải"*): Bắt buộc phải **hỏi lại người dùng** để lấy ngưỡng giờ trước khi kết luận hoặc phân tích quá tải. **Không tự ý giả định** bất kỳ ngưỡng mặc định nào (không tự chọn 8) và **không dùng lại ngưỡng** từ các cuộc trò chuyện cũ.

## Chạy script

Dùng tool `bash` (cwd là workspace). Lệnh đầy đủ:

```
python skills/csv-quality/scripts/check_csv.py --input <đường dẫn CSV> --max-hours <ngưỡng>
```

Ví dụ: `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8`

Không cần đọc source script để chạy. Chỉ đọc `scripts/check_csv.py` khi cần hiểu một hành vi mà tài liệu chưa mô tả.

## Kiểm tra kết quả

- `exit_code` 0: Phân tích thành công. `stdout` là JSON chứa các thông tin:
  - `max_hours`: ngưỡng giờ đã nhận.
  - `hours_by_owner`: object tổng giờ theo từng người (chỉ gồm người có ít nhất 1 dòng hợp lệ được cộng).
  - `overloaded_owners`: danh sách người vượt ngưỡng (tổng giờ > max_hours), sắp xếp theo tên.
  - `excluded_rows`: danh sách các dòng bị loại khỏi tính giờ kèm danh sách lý do (`wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`).
  - Các thống kê chất lượng dữ liệu cũ: `row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `duplicate_ids`, `issues`.
  - Dữ liệu có lỗi hoặc có người quá tải script vẫn trả về exit 0.
- `exit_code` khác 0: **Lỗi thực thi** (file không tồn tại, thiếu cột bắt buộc, lỗi parse, thiếu hoặc sai tham số `--max-hours`). Đọc `stderr`, báo lỗi trực tiếp cho người dùng. Không bịa thống kê, không đưa ra tổng giờ hay ghi báo cáo như khi phân tích thành công.
- `timed_out` true hoặc `ok` false: Lệnh không chạy xong; báo lỗi, không suy đoán kết quả.

## Viết báo cáo

1. Đọc template `references/report-template.md` trong thư mục skill này (`skills/csv-quality/references/report-template.md`).
2. Lấy mọi dữ liệu từ JSON của script:
   - Ngưỡng giờ và danh sách tổng giờ theo người.
   - Danh sách người bị quá tải.
   - Các dòng bị loại và lý do loại dòng đó.
   - Các cảnh báo và lỗi chất lượng dữ liệu.
3. Không tự ý chỉnh sửa file CSV đầu vào khi người dùng không yêu cầu.
4. Ghi báo cáo bằng `write_file` vào đường dẫn người dùng yêu cầu (ví dụ `output/workload.md` hoặc `output/csv-quality.md`), sau đó thông báo đường dẫn file và tóm tắt kết quả cho người dùng.
