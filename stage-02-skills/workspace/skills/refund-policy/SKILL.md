---
name: refund-policy
description: Tra cứu và kiểm tra điều kiện hoàn tiền trong data/policies/ theo ngày mua và trạng thái kích hoạt. Dùng khi người dùng hỏi về hoàn tiền, chính sách hoàn tiền hoặc yêu cầu trả hàng.
---

# Refund policy

Hướng dẫn tra cứu và áp dụng chính sách hoàn tiền đúng phiên bản.

## 1. ⚠️ ĐIỀU KIỆN BẮT BUỘC TRƯỚC KHI XỬ LÝ (STOP CONDITION)

Trước khi tra cứu tài liệu hoặc kết luận, bạn BẮT BUỘC phải kiểm tra 3 thông tin đầu vào trong câu hỏi của người dùng:
1. **Ngày mua hàng**
2. **Ngày yêu cầu hoàn tiền**
3. **Trạng thái kích hoạt sản phẩm** (`Đã kích hoạt` hoặc `Chưa kích hoạt`)

> ⛔ **QUY TẮC NGHIÊM NGẶT VỀ THÔNG TIN KHÁCH HÀNG:**
> - Nếu câu hỏi của người dùng **chưa cung cấp thông tin trạng thái kích hoạt** (hoặc thiếu ngày mua / ngày yêu cầu), bạn **KHÔNG ĐƯỢC tự giả định** (ví dụ: KHÔNG ĐƯỢC tự cho là sản phẩm chưa kích hoạt).
> - Bạn phải **DỪNG LẠI NGAY** và đặt câu hỏi cho người dùng để làm rõ thông tin còn thiếu (ví dụ: *"Bạn vui lòng cho biết sản phẩm của bạn đã kích hoạt chưa?"*).
> - **KHÔNG ĐƯỢC** tra cứu tài liệu hay đưa ra bất kỳ kết luận nào khi chưa nhận được câu trả lời bổ sung từ người dùng.

---

## 2. 📋 QUY TRÌNH THỰC HIỆN (Khi đã có ĐẦY ĐỦ 3 thông tin trên)

### Bước 1: Tìm kiếm tài liệu
- Dùng tool `list_files` với `path: "data/policies"` để liệt kê các file tài liệu trong `data/policies/`.
- Dùng tool `read_file` đọc nội dung từng file chính sách tìm được để kiểm tra quy định về ngày mua và số ngày hoàn tiền.

### Bước 2: Chọn chính sách áp dụng (RẤT QUAN TRỌNG)
- **Căn cứ chọn chính sách:** BẮT BUỘC chỉ dựa vào **NGÀY MUA HÀNG** (Purchase Date). **TUYỆT ĐỐI KHÔNG** dựa vào Ngày yêu cầu hoàn tiền.
  - Ngày mua **trước 2026-10-01** (ví dụ: 28/09/2026) -> BẮT BUỘC áp dụng chính sách áp dụng cho ngày mua trước 2026-10-01 (ví dụ: `policy-before...`).
  - Ngày mua **từ 2026-10-01 trở đi** (ví dụ: 02/10/2026) -> BẮT BUỘC áp dụng chính sách áp dụng cho ngày mua từ 2026-10-01 (ví dụ: `policy-from...`).

### Bước 3: Tính toán và đối chiếu điều kiện
- Tính số ngày đã qua = `Ngày yêu cầu hoàn` - `Ngày mua` (tính theo ngày lịch).
- Đối chiếu với quy định trong chính sách đã chọn:
  - **Đủ điều kiện:** Số ngày đã qua <= Thời hạn được hoàn trong chính sách AND Sản phẩm `Chưa kích hoạt`.
  - **Không đủ điều kiện:** Số ngày đã qua > Thời hạn được hoàn trong chính sách OR Sản phẩm `Đã kích hoạt`.

### Bước 4: Trình bày câu trả lời
- Dùng `read_file` đọc mẫu câu trả lời tại `references/answer-template.md` (`skills/refund-policy/references/answer-template.md`).
- Trình bày đầy đủ: Chính sách áp dụng, Ngày mua, Ngày yêu cầu hoàn, Số ngày đã qua, Trạng thái kích hoạt, Kết luận, Phí hoàn tiền và File căn cứ.
