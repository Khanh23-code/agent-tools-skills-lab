# Báo cáo khối lượng công việc và chất lượng dữ liệu: `{đường dẫn CSV}`

Công cụ: `skills/csv-quality/scripts/check_csv.py` | exit code: {exit_code}

## 1. Kiểm tra quá tải theo người
- **Ngưỡng giờ tối đa (max_hours)**: {max_hours} giờ

### Tổng giờ theo người
| Người thực hiện (owner) | Tổng số giờ | Tình trạng quá tải (> {max_hours} giờ) |
|---|---|---|
| {owner} | {total_hours} | {Quá tải / Bình thường} |

*(Chỉ tính các dòng dữ liệu hợp lệ, không tính các dòng bị loại)*

### Danh sách người quá tải
{Danh sách người có tổng giờ vượt ngưỡng max_hours, ví dụ:
- **{owner}**: {total_hours} giờ (vượt ngưỡng {total_hours - max_hours} giờ)
Nếu không có ai vượt ngưỡng: "Không có nhân sự nào bị quá tải."}

### Các dòng bị loại khỏi tính tổng giờ (excluded_rows)
| Dòng (Line) | task_id | Lý do loại (reasons) |
|---|---|---|
| {line} | {task_id} | {reasons} |

*(Mã lý do gồm: wrong_field_count, missing_task_id, duplicate_id, missing_owner, invalid_hours)*

## 2. Thống kê chất lượng dữ liệu
| Chỉ số | Giá trị |
|---|---|
| Số dòng dữ liệu (không tính header) | {row_count} |
| Dòng thiếu owner | {missing_owner_count} |
| Dòng hours không hợp lệ | {invalid_hours_count} |
| Số task_id bị lặp (distinct) | {duplicate_id_count} ({duplicate_ids}) |

## 3. Chi tiết lỗi dữ liệu (issues)
| Line | Cột | Loại | task_id | Mô tả |
|---|---|---|---|---|
| {line} | {column} | {type} | {task_id} | {message} |

## 4. Đánh giá & Khuyến nghị
- **Đánh giá**: {Đánh giá tình trạng phân bổ công việc và độ tin cậy của tập dữ liệu}
- **Khuyến nghị**: {Khuyến nghị điều chỉnh công việc hoặc chuẩn hóa dữ liệu, không tự ý sửa file nguồn}
