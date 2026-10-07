# Báo Cáo Phân Tích & Kết Quả Thực Hiện: Block 2 - Kiểm Tra Quá Tải Theo Người (Stage 04)

## 1. Tổng Quan Các Thay Đổi Đã Thực Hiện

### 1.1. Script `skills/csv-quality/scripts/check_csv.py` (đồng bộ giữa `workspace/` và `fixtures/`)
- **Bổ sung tham số bắt buộc `--max-hours`**:
  - Nhận số thực/nguyên hữu hạn, không âm (`>= 0`).
  - Nếu thiếu tham số hoặc giá trị không hợp lệ (số âm, chuỗi chữ, `NaN`, `inf`), script ghi thông báo lỗi rõ ràng ra `stderr` và trả mã thoát khác 0 (exit code `1` hoặc `2`).
- **Mở rộng logic tính tổng giờ & xác định người quá tải**:
  - Chuẩn hóa khoảng trắng (`strip()`) ở các trường `task_id`, `owner`, `hours`. Phân biệt chữ hoa/thường cho `owner`.
  - **Quy tắc trùng ID**: Theo dõi `first_seen`. Mỗi `task_id` không rỗng chỉ giữ lần xuất hiện đầu tiên trong file. Các lần xuất hiện tiếp theo bị đánh dấu `duplicate_id` và loại bỏ, kể cả khi lần đầu chứa dữ liệu lỗi (không thay bằng "lần hợp lệ đầu tiên").
  - **Quy tắc loại dòng**: Chỉ cộng dòng có đầy đủ các điều kiện: đúng số cột, `task_id` không rỗng, không trùng `task_id`, `owner` không rỗng, và `hours` là số hữu hạn không âm (`>= 0`). Giá trị `0` là hợp lệ.
  - **Cấu trúc `excluded_rows`**: Mỗi dòng bị loại xuất hiện một lần với đầy đủ các lý do, các lý do được sắp xếp cố định theo thứ tự: `["wrong_field_count", "missing_task_id", "duplicate_id", "missing_owner", "invalid_hours"]`. Dòng trống được bỏ qua.
  - **Cấu trúc `hours_by_owner`**: Object ánh xạ `owner -> total_hours`. Chỉ chứa những nhân sự có ít nhất một dòng hợp lệ được cộng dồn.
  - **Cấu trúc `overloaded_owners`**: Danh sách `[{"owner": ..., "total_hours": ...}]` gồm những người có tổng giờ **lớn hơn hẳn** (`>`) `max_hours`, sắp xếp theo tên (`owner`). Bằng ngưỡng không bị coi là quá tải.
  - Giữ nguyên các trường thống kê chất lượng dữ liệu cũ (`row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `duplicate_ids`, `issues`).

### 1.2. Hướng dẫn Skill `skills/csv-quality/SKILL.md` (đồng bộ giữa `workspace/` và `fixtures/`)
- Cập nhật mô tả để phản ánh khả năng kiểm tra quá tải công việc theo người.
- **Quy tắc ngưỡng giờ**:
  - Quy định rõ nếu người dùng yêu cầu kiểm tra quá tải hoặc tổng giờ mà **chưa cung cấp ngưỡng**, agent **bắt buộc phải hỏi lại người dùng** để lấy ngưỡng. Tuyệt đối không tự giả định ngưỡng mặc định (như 8) và không dùng lại ngưỡng từ hội thoại cũ.
  - Cập nhật cú pháp gọi lệnh Bash: `python skills/csv-quality/scripts/check_csv.py --input <đường dẫn CSV> --max-hours <ngưỡng>`.
  - Cập nhật hướng dẫn đọc kết quả JSON mới và quy tắc ghi báo cáo.

### 1.3. Template Báo Cáo `skills/csv-quality/references/report-template.md` (đồng bộ giữa `workspace/` và `fixtures/`)
- Mở rộng cấu trúc báo cáo gồm:
  1. Ngưỡng giờ áp dụng (`max_hours`).
  2. Bảng tổng giờ theo từng người (`hours_by_owner`) và trạng thái quá tải.
  3. Danh sách người quá tải (`overloaded_owners`).
  4. Bảng các dòng bị loại khỏi tính tổng giờ (`excluded_rows`) kèm chi tiết mã lý do.
  5. Thống kê chất lượng dữ liệu và chi tiết lỗi dữ liệu cũ (`issues`).
  6. Phần đánh giá và khuyến nghị khắc phục.

### 1.4. Dữ Liệu Kiểm Thử & Test Tự Động
- Tạo `workspace/data/workload.csv` và `fixtures/data/workload.csv`.
- Tạo `workspace/data/workload-edge.csv` và `fixtures/data/workload-edge.csv`.
- Mở rộng `tests/test_check_csv.py`:
  - Kiểm tra các trường hợp CLI thiếu hoặc sai `--max-hours`.
  - Kiểm tra bộ dữ liệu fixture và bộ dữ liệu `workload.csv` với ngưỡng 8 và 9.
  - Kiểm tra trường hợp biên (edge case) `workload-edge.csv` với ngưỡng 0: đảm bảo `E01` dòng 2 bị loại vì `invalid_hours`, dòng 3 bị loại vì `duplicate_id`, Lan không được cộng 5 giờ và không có mặt trong `hours_by_owner`. Toàn bộ 22 bài test đều vượt qua (100% PASSED).

---

## 2. Kết Quả Chạy Trực Tiếp Các Trường Hợp

### Trường Hợp 1: `workload.csv` với `--max-hours 8`
**Lệnh chạy:**
```bash
python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv --max-hours 8
```
**JSON Đầu Ra:**
```json
{
  "input": "workspace/data/workload.csv",
  "max_hours": 8,
  "row_count": 6,
  "missing_owner_count": 1,
  "invalid_hours_count": 1,
  "duplicate_id_count": 1,
  "duplicate_ids": [
    "T02"
  ],
  "issues": [
    {
      "line": 5,
      "column": "hours",
      "type": "invalid_hours",
      "task_id": "T04",
      "value": "abc",
      "message": "hours 'abc' không phải số hữu hạn không âm."
    },
    {
      "line": 6,
      "column": "task_id",
      "type": "duplicate_id",
      "task_id": "T02",
      "message": "task_id T02 đã xuất hiện ở line 3."
    },
    {
      "line": 7,
      "column": "owner",
      "type": "missing_owner",
      "task_id": "T05",
      "message": "owner trống."
    }
  ],
  "hours_by_owner": {
    "Lan": 9,
    "Minh": 3
  },
  "overloaded_owners": [
    {
      "owner": "Lan",
      "total_hours": 9
    }
  ],
  "excluded_rows": [
    {
      "line": 5,
      "task_id": "T04",
      "reasons": [
        "invalid_hours"
      ]
    },
    {
      "line": 6,
      "task_id": "T02",
      "reasons": [
        "duplicate_id"
      ]
    },
    {
      "line": 7,
      "task_id": "T05",
      "reasons": [
        "missing_owner"
      ]
    }
  ]
}
```
**Nhận xét:**
- Lan có 9 giờ (4 + 5), Minh có 3 giờ.
- Chỉ có Lan bị quá tải (`overloaded_owners` có Lan với 9 giờ, vượt ngưỡng 8).
- Dòng 5 bị loại vì `invalid_hours`, dòng 6 bị loại vì `duplicate_id`, dòng 7 bị loại vì `missing_owner`.

---

### Trường Hợp 2: `workload.csv` với `--max-hours 9`
**Lệnh chạy:**
```bash
python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv --max-hours 9
```
**JSON Đầu Ra:**
```json
{
  "input": "workspace/data/workload.csv",
  "max_hours": 9,
  "row_count": 6,
  "missing_owner_count": 1,
  "invalid_hours_count": 1,
  "duplicate_id_count": 1,
  "duplicate_ids": [
    "T02"
  ],
  "issues": [
    {
      "line": 5,
      "column": "hours",
      "type": "invalid_hours",
      "task_id": "T04",
      "value": "abc",
      "message": "hours 'abc' không phải số hữu hạn không âm."
    },
    {
      "line": 6,
      "column": "task_id",
      "type": "duplicate_id",
      "task_id": "T02",
      "message": "task_id T02 đã xuất hiện ở line 3."
    },
    {
      "line": 7,
      "column": "owner",
      "type": "missing_owner",
      "task_id": "T05",
      "message": "owner trống."
    }
  ],
  "hours_by_owner": {
    "Lan": 9,
    "Minh": 3
  },
  "overloaded_owners": [],
  "excluded_rows": [
    {
      "line": 5,
      "task_id": "T04",
      "reasons": [
        "invalid_hours"
      ]
    },
    {
      "line": 6,
      "task_id": "T02",
      "reasons": [
        "duplicate_id"
      ]
    },
    {
      "line": 7,
      "task_id": "T05",
      "reasons": [
        "missing_owner"
      ]
    }
  ]
}
```
**Nhận xét:**
- Tổng giờ và các dòng bị loại giữ nguyên.
- Lan có 9 giờ, bằng đúng ngưỡng 9 nên **không bị coi là quá tải** (`overloaded_owners: []`).

---

### Trường Hợp 3: Trường Hợp Biên `workload-edge.csv` với `--max-hours 0`
**Dữ liệu đầu vào (`data/workload-edge.csv`):**
```csv
task_id,owner,hours
E01,Lan,abc
E01,Lan,5
E02,Minh,0
```
**Lệnh chạy:**
```bash
python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload-edge.csv --max-hours 0
```
**JSON Đầu Ra:**
```json
{
  "input": "workspace/data/workload-edge.csv",
  "max_hours": 0,
  "row_count": 3,
  "missing_owner_count": 0,
  "invalid_hours_count": 1,
  "duplicate_id_count": 1,
  "duplicate_ids": [
    "E01"
  ],
  "issues": [
    {
      "line": 2,
      "column": "hours",
      "type": "invalid_hours",
      "task_id": "E01",
      "value": "abc",
      "message": "hours 'abc' không phải số hữu hạn không âm."
    },
    {
      "line": 3,
      "column": "task_id",
      "type": "duplicate_id",
      "task_id": "E01",
      "message": "task_id E01 đã xuất hiện ở line 2."
    }
  ],
  "hours_by_owner": {
    "Minh": 0
  },
  "overloaded_owners": [],
  "excluded_rows": [
    {
      "line": 2,
      "task_id": "E01",
      "reasons": [
        "invalid_hours"
      ]
    },
    {
      "line": 3,
      "task_id": "E01",
      "reasons": [
        "duplicate_id"
      ]
    }
  ]
}
```
**Nhận xét:**
- `E01` xuất hiện lần đầu ở dòng 2 bị loại vì `invalid_hours`.
- `E01` xuất hiện lần thứ hai ở dòng 3 bị loại vì `duplicate_id`.
- Lan không được cộng 5 giờ và hoàn toàn không có tên trong `hours_by_owner`.
- Chỉ Minh có dòng hợp lệ với 0 giờ (`hours_by_owner: {"Minh": 0}`).
- Ngưỡng 0 giờ: Minh có 0 giờ không vượt 0 nên `overloaded_owners: []`.

---

### Trường Hợp 4: Không Cung Cấp Ngưỡng Giờ
**Yêu cầu người dùng:**
> *"Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải."*

**Hành vi của Agent theo `SKILL.md` (Bằng chứng trong trace: `traces/20261007-232611_d3581288_turn01_e308e6ec.jsonl`):**
- Agent đọc `skills/csv-quality/SKILL.md`.
- Phát hiện trong yêu cầu chưa có ngưỡng giờ làm việc tối đa (`max-hours`).
- Thay vì tự ý chạy script với ngưỡng ngầm định (như 8), agent **dừng lại và hỏi người dùng**:
  > *"Đã đọc file CSV và hướng dẫn skill. Bạn chưa cung cấp ngưỡng giờ để xác định người quá tải. Bạn có thể cung cấp ngưỡng giờ không?"*

---

### Trường Hợp 5: File Không Tồn Tại
**Lệnh chạy trực tiếp:**
```bash
python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/khong-ton-tai.csv --max-hours 8
```
**Kết quả thực tế:**
- Exit code: `1` (khác 0).
- `stderr`: `ERROR: Không đọc được file workspace/data/khong-ton-tai.csv: No such file or directory`.
- `stdout`: Rỗng.

**Hành vi của Agent (Bằng chứng trong trace: `traces/20261007-232613_69110c44_turn01_18a7c256.jsonl`):**
- Agent nhận thấy `exit_code: 1` hoặc công cụ đọc file báo lỗi, đọc `stderr`.
- Thông báo lỗi trực tiếp cho người dùng: *"Không tìm thấy file data/khong-ton-tai.csv. Vui lòng kiểm tra lại đường dẫn."*
- Tuyệt đối không tự suy diễn số liệu, không tính tổng giờ hay ghi báo cáo.

---

## Bằng Chứng Các File Trace Đã Sinh Ra Trong Lab
1. **Ca 1 (Ngưỡng 8 - Thành công tạo báo cáo `output/workload.md`):**
   - File trace: `traces/20261007-232601_4ec8b403_turn01_d5aa9b9b.jsonl`
   - Bằng chứng tool `bash` gọi script: dòng 8-11.
   - Bằng chứng tool `write_file` ghi file: dòng 16-17.
2. **Ca 2 (Ngưỡng 9 - Không ai quá tải):**
   - File trace: `traces/20261007-232608_0d646bc1_turn01_1073f9e4.jsonl`
3. **Ca 3 (Thiếu ngưỡng - Agent dừng lại hỏi ngưỡng):**
   - File trace: `traces/20261007-232611_d3581288_turn01_e308e6ec.jsonl`
   - Bằng chứng câu trả lời của agent: dòng 9.
4. **Ca 4 (File không tồn tại - Báo lỗi không phân tích được):**
   - File trace: `traces/20261007-232613_69110c44_turn01_18a7c256.jsonl`

---

## 3. Trả Lời Câu Hỏi Cuối Bài

### Câu hỏi 1: Phần nào do script tính, phần nào do model diễn giải?
- **Phần do Script tính toán (Deterministic Computation)**:
  - Kiểm tra tính toàn vẹn của file và cấu trúc CSV (số cột, định dạng UTF-8, sự hiện diện của header).
  - Phân loại và phát hiện lỗi dữ liệu chi tiết (`wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`).
  - Lọc và loại trừ các dòng vi phạm theo quy tắc chặt chẽ (giữ lần xuất hiện đầu tiên của `task_id`, loại trừ các dòng kế tiếp).
  - Tính tổng số giờ chính xác (`hours_by_owner`) cho từng nhân sự dựa trên các dòng dữ liệu hợp lệ.
  - So sánh tổng số giờ với ngưỡng `max_hours` để xác định danh sách nhân sự quá tải (`overloaded_owners`).
  - Xuất toàn bộ dữ liệu dưới dạng JSON có cấu trúc chuẩn mực.
- **Phần do Model diễn giải (Language Model Reasoning & Presentation)**:
  - Hiểu ý định người dùng (cần kiểm tra chất lượng hay kiểm tra quá tải, trích xuất tham số ngưỡng hoặc nhận biết khi thiếu ngưỡng để hỏi lại).
  - Lựa chọn skill phù hợp từ Skill Catalog và gọi tool `bash` với đúng đối số.
  - Đọc template tham chiếu (`report-template.md`) và map các trường dữ liệu từ JSON đầu ra vào cấu trúc báo cáo Markdown.
  - Viết phần **Đánh giá** tổng quan và đưa ra **Khuyến nghị** cải tiến, chuẩn hóa dữ liệu cho người quản lý dựa trên bối cảnh cụ thể mà không tự sửa đổi dữ liệu nguồn.

---

### Câu hỏi 2: Nếu sửa script nhưng không cập nhật skill và reference, báo cáo có thể sai hoặc thiếu thông tin gì?
1. **Agent không truyền đúng tham số CLI**: `SKILL.md` cũ không có hướng dẫn về `--max-hours`. Model sẽ tiếp tục gọi lệnh không có `--max-hours`, khiến script bị crash với lỗi tham số và exit code khác 0.
2. **Model tự giả định ngưỡng hoặc tự cộng nhẩm**: Nếu không có quy tắc bắt buộc hỏi lại khi thiếu ngưỡng trong `SKILL.md`, model có thể tự bịa ra ngưỡng (ví dụ tự đoán là 8 giờ) hoặc tự đọc file CSV bằng tool khác và cộng nhẩm bằng mắt, dẫn đến sai sót (ví dụ cộng trùng dòng 6 của Lan dẫn đến tổng 14 giờ thay vì 9 giờ).
3. **Báo cáo thiếu các mục quan trọng**: Do `references/report-template.md` cũ chỉ có các mục đếm số dòng lỗi (`missing_owner_count`, `invalid_hours_count`, `duplicate_ids`), báo cáo tạo ra sẽ **hoàn toàn không có**:
   - Ngưỡng giờ áp dụng (`max_hours`).
   - Tổng giờ làm việc của từng nhân sự (`hours_by_owner`).
   - Danh sách người bị quá tải (`overloaded_owners`).
   - Bảng các dòng bị loại khỏi tính giờ và lý do cụ thể (`excluded_rows`).
4. **Không nhất quán trong kết luận**: Model có thể kết luận rằng dữ liệu "không dùng được" thay vì nhận diện được phần dữ liệu hợp lệ đã được script bóc tách và tính toán chính xác.
