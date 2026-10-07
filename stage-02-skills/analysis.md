# BÁO CÁO PHÂN TÍCH VÀ KẾT QUẢ KIỂM THỬ

---

## I. KẾT QUẢ KIỂM TRA TOOL TRỰC TIẾP (`list_files`)

Công cụ `list_files` được thiết kế để liệt kê các file/thư mục trực tiếp trong workspace, tuân thủ nghiêm ngặt cơ chế Sandbox bảo mật và kiểm tra lỗi có cấu trúc:

| Kịch bản kiểm thử         | Đầu vào (`path`)            | Trạng thái  | Kết quả trả về / Mã lỗi                                                          | Giải thích                                                                   |
| :------------------------ | :-------------------------- | :---------- | :------------------------------------------------------------------------------- | :--------------------------------------------------------------------------- |
| **Thư mục hợp lệ**        | `"data/policies"`           | `ok: true`  | Danh sách chứa `policy-before-oct.md` & `policy-from-oct.md` với `type: "file"`. | Liệt kê thành công các mục trực tiếp, sắp xếp theo tên.                      |
| **Đường dẫn file lẻ**     | `"data/weekly_notes.md"`    | `ok: false` | Mã lỗi: `NOT_A_DIRECTORY`                                                        | Từ chối thao tác vì đối tượng là file văn bản, không phải thư mục.           |
| **Thư mục không tồn tại** | `"data/khong_ton_tai"`      | `ok: false` | Mã lỗi: `DIRECTORY_NOT_FOUND`                                                    | Trả về thông báo lỗi rõ ràng thay vì danh sách rỗng.                         |
| **Thoát khỏi Workspace**  | `"../"` hoặc path tuyệt đối | `ok: false` | Mã lỗi: `PATH_OUTSIDE_WORKSPACE`                                                 | Cơ chế `_resolve` phát hiện và chặn hành vi Path Traversal / Symlink Escape. |

---

## II. KẾT QUẢ KIỂM THỬ CÁC TRƯỜNG HỢP NGIỆM THU

### 1. Trường hợp A: Mua trước ngày đổi chính sách (28/09/2026)

- **Prompt gửi Agent:**
  > `"Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?"`
- **Kết quả xử lý của Agent:**
  - **Chính sách áp dụng:** Chính sách hoàn tiền trước tháng 10 (`policy-before-oct.md`).
  - **Tính toán:** Ngày mua `28/09/2026`, Ngày yêu cầu `06/10/2026` $\rightarrow$ Đã qua **8 ngày** (tính theo ngày lịch).
  - **Kết luận:** **Không đủ điều kiện hoàn tiền** (Chính sách quy định thời hạn tối đa là 7 ngày).
- **Bằng chứng trong Trace (`traces/*.jsonl`):**
  - **Model Call #1:** Nhận biết task hoàn tiền $\rightarrow$ Gọi `read_file("skills/refund-policy/SKILL.md")`.
  - **Model Call #2:** Nạp nội dung skill $\rightarrow$ Gọi `list_files("data/policies")` để liệt kê danh sách tài liệu.
  - **Model Call #3:** Gọi `read_file("data/policies/policy-before-oct.md")` để xác định chính sách áp dụng cho ngày mua trước `2026-10-01`.
  - **Model Call #4:** Đọc `skills/refund-policy/references/answer-template.md` và trình bày câu trả lời kết luận không đủ điều kiện.

---

### 2. Trường hợp B: Mua từ ngày đổi chính sách (02/10/2026)

- **Prompt gửi Agent:**
  > `"Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?"`
- **Kết quả xử lý của Agent:**
  - **Chính sách áp dụng:** Chính sách hoàn tiền từ tháng 10 (`policy-from-oct.md`).
  - **Tính toán:** Ngày mua `02/10/2026`, Ngày yêu cầu `12/10/2026` $\rightarrow$ Đã qua **10 ngày**.
  - **Kết luận:** **Đủ điều kiện hoàn tiền**, Phí hoàn tiền: **0%** (Không thu phí).
- **Bằng chứng trong Trace (`traces/*.jsonl`):**
  - **Model Call:** Agent gọi `read_file("data/policies/policy-from-oct.md")` xác nhận hiệu lực áp dụng từ `2026-10-01` trở đi với thời hạn 14 ngày. Trả lời khớp mẫu template.

---

### 3. Trường hợp Đổi tên file tài liệu (Dynamic File Lookup)

- **Thao tác:** Đổi tên file trong `workspace/data/policies/` (ví dụ thành `policy-before.md` và `policy-from.md`). Mở cuộc trò chuyện mới.
- **Prompt gửi Agent:** Tương tự Trường hợp A & B.
- **Kết quả xử lý:**
  - Agent không bị ảnh hưởng bởi việc đổi tên file.
  - Kết luận vẫn giữ nguyên tính chính xác tuyệt đối.
- **Bằng chứng trong Trace (`traces/*.jsonl`):**
  - Trong cuộc trò chuyện mới, Agent gọi `list_files("data/policies")` và nhận về danh sách file với tên mới.
  - Agent đọc nội dung từ file tên mới bằng `read_file`, xác định đúng phạm vi ngày mua mà không dựa vào tên file cố định hay lịch sử cũ.

---

### 4. Trường hợp Thiếu thông tin (Missing Information)

- **Prompt gửi Agent:**
  > `"Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026."` _(Thiếu thông tin trạng thái kích hoạt)_
- **Kết quả xử lý của Agent:**
  - Agent **KHÔNG tự giả định** sản phẩm "chưa kích hoạt".
  - Agent **DỪNG LẠI NGAY LẬP TỨC** và phản hồi hỏi lại người dùng:
    > _"Bạn vui lòng cho biết sản phẩm của bạn đã được kích hoạt hay chưa để tôi có thể kiểm tra chính xác điều kiện hoàn tiền."_
- **Bằng chứng trong Trace (`traces/*.jsonl`):**
  - Trong `model_response`, Agent phát hiện thiếu 1 trong 3 tham số bắt buộc theo mục `ĐIỀU KIỆN BẮT BUỘC TRƯỚC KHI XỬ LÝ` trong `SKILL.md`.
  - Agent dừng luồng gọi tool tra cứu tài liệu hoàn tiền cho tới khi người dùng bổ sung câu trả lời.

---

## III. GIẢI ĐÁP CÂU HỎI THẢO LUẬN CỦA BÀI HỌC

### Câu hỏi: Vì sao cần tool để tìm file và skill để hướng dẫn chọn chính sách? If agent chưa có tool tìm file, việc sửa prompt có giải quyết được yêu cầu đổi tên file không? Giải thích.

#### 1. Vì sao cần Tool để tìm file (`list_files`)?

- **Khả năng quan sát môi trường thực tế (Environment Awareness):** Agent không thể tự "đoán" hoặc "nhìn thấy" cấu trúc thư mục nếu không được trang bị công cụ tương tác. Công cụ `list_files` đóng vai trò là "mắt thần" giúp Agent phát hiện động các file đang tồn tại trong thư mục dữ liệu tại thời điểm thực thi.

#### 2. Vì sao cần Skill để hướng dẫn chọn chính sách (`refund-policy`)?

- **Định hình quy trình nghiệp vụ (Business Workflow Standards):** Skill giúp chuẩn hóa logic xử lý phức tạp của doanh nghiệp: kiểm tra tham số bắt buộc, quy tắc dừng hỏi lại khi thiếu thông tin, tiêu chí phân định chính sách dựa trên _Ngày mua_ (không dựa vào _Ngày yêu cầu_), và định dạng báo cáo đầu ra chuẩn chỉnh.

#### 3. Nếu Agent chưa có tool tìm file, việc sửa Prompt có giải quyết được yêu cầu đổi tên file không?

=> **KHÔNG THỂ GIẢI QUYẾT ĐƯỢC.**

- **Lý do:**
  1. Nếu không có tool `list_files`, Agent chỉ có thể dựa vào các đường dẫn được viết cứng (hardcoded) trong Prompt (ví dụ: `data/policies/policy-before.md`).
  2. Khi quản trị viên hoặc hệ thống đổi tên file trên đĩa (ví dụ thành `policy-before-oct.md`), Prompt cũ lập tức trở nên vô hiệu. Nếu Agent cố gắng gọi `read_file` với path cũ, hệ thống sẽ trả về lỗi `FILE_NOT_FOUND`.
  3. Việc sửa Prompt thủ công mỗi khi đổi tên file làm mất đi tính tự động và khả năng linh hoạt (Autonomy) của AI Agent, biến Agent thành một script tĩnh cứng nhắc thay vì một Agent thông minh thực sự.
