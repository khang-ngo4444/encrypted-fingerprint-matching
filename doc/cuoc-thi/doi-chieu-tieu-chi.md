# Đối chiếu dự án với thang điểm vòng chung kết

Tám nhóm tiêu chí, tổng 100 điểm. Mỗi mục nêu bằng chứng hiện có và phần còn thiếu.

Ký hiệu: **Đã có** — có bằng chứng cụ thể, trích dẫn được. **Thiếu** — chưa có dữ liệu,
đội cần bổ sung trước khi nộp.

---

## 1. Sự cần thiết, mức độ ứng dụng — 20 điểm

### 1.1 Sự cần thiết đối với nhu cầu thị trường và cộng đồng (5 điểm) — Đã có

Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP có hiệu lực từ
01/01/2026, xếp dữ liệu sinh trắc vào nhóm nhạy cảm. Mọi tổ chức đang lưu vân tay nhân
viên hoặc khách hàng phải chứng minh được biện pháp bảo vệ.

Sáu tháng đầu năm 2025, cơ quan chức năng phát hiện 56 vụ mua bán dữ liệu cá nhân trái
phép, liên quan khoảng 110 triệu bản ghi.

Khác biệt cốt lõi của dữ liệu sinh trắc: mật khẩu lộ thì đổi được, vân tay lộ thì theo
người đó suốt đời, và mọi hệ thống dùng vân tay đó mất an toàn vĩnh viễn.

### 1.2 Giá trị mang lại cho khách hàng, cộng đồng, xã hội (5 điểm) — Đã có

Hệ thống loại bỏ hoàn toàn thời điểm dữ liệu sinh trắc tồn tại ở dạng đọc được trên máy
chủ. Rủi ro không còn phụ thuộc vào việc bảo vệ máy chủ tốt đến đâu.

Ba nhóm rủi ro bị loại trừ: quản trị viên lạm quyền, máy chủ bị xâm nhập, dữ liệu bị
sao chép khi chuyển giao hạ tầng.

### 1.3 Xác định và đánh giá đúng đối tượng, phân khúc khách hàng (5 điểm) — Đã có một phần

Phân khúc đầu tiên: doanh nghiệp đang dùng vân tay cho chấm công và kiểm soát ra vào.
Lý do chọn nhóm này — đã có sẵn thiết bị, đang giữ dữ liệu nhạy cảm, và chịu áp lực
tuân thủ sớm nhất.

Phân khúc mở rộng: ngân hàng và fintech dùng eKYC, hãng sản xuất thiết bị sinh trắc.

**Thiếu:** quy mô từng phân khúc tại Việt Nam — số doanh nghiệp, số thiết bị đang vận
hành. Chưa khảo sát.

### 1.4 Mức độ giải quyết vấn đề thực tiễn bằng công nghệ (5 điểm) — Đã có

Sản phẩm chạy được, không dừng ở ý tưởng. Toàn bộ số liệu tái tạo được bằng năm lệnh
nêu trong `README.md` của repo.

| Bằng chứng | Giá trị |
|---|---|
| Thời gian một truy vấn, đo đầu đến cuối | 26,51 ms |
| Sai lệch so với tính trên dữ liệu gốc | 0,0096 % |
| Truy vấn cho kết quả giống hệt bản gốc | 80/80 |
| Quy mô kiểm chứng | 3.160 cặp, dữ liệu chuẩn quốc tế FVC2002 DB1_B |

---

## 2. Tính khả thi, tiềm năng phát triển — 10 điểm

### 2.1 Tính khả thi trong sản xuất, kinh doanh (4 điểm) — Đã có

Hệ thống không yêu cầu khách hàng thay cảm biến, thay bộ trích đặc trưng hay đổi cơ sở
dữ liệu. Chỉ thay khâu so khớp. Giao diện tích hợp đơn giản: nhận vector đặc trưng, trả
khoảng cách.

Phần mã hoá chạy được trên thiết bị tài nguyên hạn chế, không đòi máy chủ chuyên dụng.

### 2.2 Tính hiệu quả: cơ cấu chi phí, giá thành so với sản phẩm đã có (4 điểm) — Thiếu

Phần chi phí **tài nguyên** đã đo đầy đủ:

| Hạng mục | Hệ thống thông thường | Hệ thống mã hoá | Hệ số |
|---|---:|---:|---:|
| Dữ liệu mỗi bản ghi | 0,50 KB | 96,00 KB | 192 × |
| Thời gian xác thực 1:1 | 0,0004 ms | 26,51 ms | 51.866 × |
| Khoá đánh giá, truyền một lần | — | 7,53 MB | — |

**Thiếu:** quy đổi sang giá thành. Cần đơn giá hạ tầng thực tế và mô hình định giá sản
phẩm thì mới so sánh được với giải pháp sẵn có trên thị trường.

### 2.3 Hệ thống giám sát, kế hoạch ứng phó rủi ro, vận hành an toàn dữ liệu (2 điểm) — Thiếu

Chưa có tài liệu về quy trình vận hành, phương án quản lý khoá bí mật, kịch bản ứng phó
khi khoá bị lộ, hay cơ chế giám sát.

Đây là điểm cần chuẩn bị kỹ vì sản phẩm thuộc lĩnh vực bảo mật — ban giám khảo nhiều
khả năng hỏi sâu. Gợi ý nội dung tối thiểu:

- Khoá bí mật lưu ở đâu, ai giữ, quy trình luân chuyển khoá
- Nếu khoá bị lộ thì mất gì, khôi phục thế nào
- Nhật ký truy cập và cơ chế phát hiện bất thường

---

## 3. Tính mới, độc đáo, sáng tạo — 15 điểm

### 3.1 Tính độc đáo so với sản phẩm đã có trên thị trường (5 điểm) — Đã có

| Nhóm | Hạn chế của họ |
|---|---|
| Zama, Duality, Enveil | Nền tảng mã hoá đồng cấu đa dụng; khách hàng vẫn phải tự xây toàn bộ phần sinh trắc |
| Microsoft SEAL | Là thư viện mật mã, không phải sản phẩm; tự dùng phải tự chọn tham số, tự tối ưu, tự kiểm chứng |
| Nhà cung cấp sinh trắc hiện nay | Bắt buộc giải mã mẫu ra bản rõ trong lúc so khớp |

### 3.2 Lợi thế cạnh tranh (5 điểm) — Đã có

Ba điểm khác biệt:

1. **Chuyên một bài toán** — chỉ giải bài toán so khớp vector sinh trắc, nên tối ưu được
   sâu hơn một nền tảng đa dụng.
2. **Không giải mã** — dữ liệu ở dạng mã từ thiết bị cho tới khi ra kết quả.
3. **Cắm vào hệ sẵn có** — nhận vector đặc trưng vào, trả khoảng cách ra, khách hàng
   không phải viết lại hệ thống.

### 3.3 Hàm lượng công nghệ lõi (5 điểm) — Đã có

Mã hoá đồng cấu CKKS, bậc đa thức 4096, ba prime 27-bit kèm một special prime 28-bit,
scale 2²⁵, đạt mức bảo mật 128-bit theo Homomorphic Encryption Security Standard.

Phần đáng kể nhất về chiều sâu kỹ thuật: quá trình truy lỗi được ghi lại đầy đủ trong
[`doc/REPORT.md`](../REPORT.md). Nhóm phát hiện một lỗi trong thư viện mã hoá phía gửi —
hàm `reduce_pte_core` vi phạm quy tắc strict aliasing, khiến trình biên dịch sinh mã sai
ở mức tối ưu `-O2` trở lên và toàn bộ phép mã hoá cho kết quả rác. Lỗi nằm ở thư viện
upstream, không phải ở mã của nhóm.

---

## 4. Mô hình kinh doanh, phát triển thị trường — 10 điểm

### 4.1 Kế hoạch sản xuất, kinh doanh (3 điểm) — Đã có một phần

Business Model Canvas đã dựng, nằm ở trang 12 của slide. Các ô đã điền: đối tác chính,
hoạt động chính, nguồn lực, giá trị mang lại, quan hệ khách hàng, kênh, phân khúc khách
hàng, cơ cấu chi phí, dòng doanh thu.

**Thiếu:** lộ trình theo mốc thời gian — làm gì trong 6 tháng, 12 tháng, 24 tháng tới.

### 4.2 Phân tích và đánh giá rủi ro (2 điểm) — Thiếu

Chưa có. Bốn nhóm rủi ro nên nêu:

| Nhóm | Nội dung |
|---|---|
| Kỹ thuật | Mã hoá đồng cấu chậm hơn 51.866 lần so với tính trên bản rõ; giới hạn quy mô ở chế độ nhận dạng 1:N |
| Thị trường | Khách hàng chưa quen khái niệm, chu kỳ bán hàng dài |
| Pháp lý | Quy định mới, cách diễn giải còn có thể thay đổi |
| Cạnh tranh | Nhà cung cấp sinh trắc lớn có thể tự làm tính năng tương tự |

### 4.3 Kênh phân phối (2 điểm) — Đã có một phần

Ba kênh đã xác định: bán trực tiếp, qua đối tác tích hợp hệ thống, qua sandbox kỹ thuật
cho khách hàng tự thử.

**Thiếu:** tỉ trọng dự kiến từng kênh, chi phí tiếp cận khách hàng.

### 4.4 Kế hoạch phát triển, mở rộng thị trường (3 điểm) — Thiếu

Chưa có lộ trình mở rộng. Hướng tự nhiên: vân tay trước, sau đó khuôn mặt và mống mắt —
cùng bài toán so khớp vector nên dùng lại được phần lớn công nghệ.

---

## 5. Tiềm năng dự án — 10 điểm

### 5.1 Kết quả dự kiến: doanh thu, lợi nhuận (5 điểm) — Thiếu hoàn toàn

Chưa có số liệu nào. **Đây là mục mất điểm nặng nhất nếu để trống.**

Cần tối thiểu: mô hình định giá (phí theo thiết bị, phí triển khai, gói hỗ trợ), số khách
hàng dự kiến theo năm, doanh thu và chi phí tương ứng cho 3 năm đầu.

### 5.2 Khả năng tăng trưởng, tốc độ phát triển (5 điểm) — Đã có một phần

Thị trường mã hoá đồng cấu toàn cầu được dự báo đạt 352–518 triệu USD vào năm 2030, tăng
trưởng kép 8,3–9,6% mỗi năm.

**Thiếu:** quy mô thị trường tại Việt Nam và tốc độ tăng trưởng dự kiến của chính dự án.

---

## 6. Khả năng huy động nguồn lực — 10 điểm

### 6.1 Nguồn lực thực hiện, tính sẵn sàng của đội, cơ cấu tổ chức, đối tác (5 điểm) — Thiếu

Đội hiện có hai thành viên. Cần nêu rõ:

- Vai trò từng người
- Năng lực còn thiếu và cách bù đắp
- Đối tác đã tiếp xúc hoặc dự kiến tiếp xúc

### 6.2 Giải pháp huy động vốn, kết nối ươm tạo, nhà đầu tư (5 điểm) — Thiếu

Chưa có. Cần nêu: cần bao nhiêu vốn, dùng vào việc gì, dự kiến tiếp cận nguồn nào.

---

## 7. Truyền thông và Marketing — 10 điểm

### 7.1 Kênh truyền thông, kế hoạch tổng thể (5 điểm) — Thiếu

Chưa có kế hoạch.

### 7.2 Giải pháp truyền thông độc đáo, khai thác nội dung số (5 điểm) — Có lợi thế sẵn

Dự án có một lợi thế mà phần lớn dự án khác không có: **mọi tuyên bố đều kiểm chứng được
bằng mã nguồn công khai**. Hướng khai thác:

- Repo công khai, người quan tâm tự chạy lại được toàn bộ số liệu
- Trang báo cáo số liệu sinh tự động từ dữ liệu đo, không vẽ tay
- Bài viết kỹ thuật về quá trình truy lỗi strict aliasing trong thư viện upstream — nội
  dung có giá trị thật với cộng đồng lập trình, không phải quảng cáo

---

## 8. Năng lực triển khai — 15 điểm

### 8.1 Khả năng thuyết trình (5 điểm) — Đã chuẩn bị

Kịch bản 5 phút ở [`kich-ban-thuyet-trinh.md`](kich-ban-thuyet-trinh.md). Câu hỏi dự kiến
và câu trả lời ở [`hoi-dap.md`](hoi-dap.md).

### 8.2 Tinh thần làm việc nhóm và kỹ năng mềm (5 điểm) — Thiếu

Cần thể hiện trong video demo: cả hai thành viên cùng xuất hiện, nói rõ phần việc của
mình.

### 8.3 Poster trưng bày và sản phẩm mẫu (5 điểm) — Đã chuẩn bị một phần

Nội dung poster ở [`poster.md`](poster.md).

Sản phẩm mẫu: hệ thống chạy được, trình diễn trực tiếp bằng lệnh `16_match_report`, in ra
bảng đối chiếu giữa kết quả tính trên dữ liệu gốc và kết quả tính trên bản mã.

---

## Tổng kết

| Nhóm tiêu chí | Điểm tối đa | Đã có bằng chứng | Còn thiếu |
|---|---:|---:|---:|
| 1. Sự cần thiết, mức độ ứng dụng | 20 | 20 | 0 |
| 2. Tính khả thi, tiềm năng phát triển | 10 | 4 | 6 |
| 3. Tính mới, độc đáo, sáng tạo | 15 | 15 | 0 |
| 4. Mô hình kinh doanh, phát triển thị trường | 10 | 3 | 7 |
| 5. Tiềm năng dự án | 10 | 2 | 8 |
| 6. Khả năng huy động nguồn lực | 10 | 0 | 10 |
| 7. Truyền thông và Marketing | 10 | 3 | 7 |
| 8. Năng lực triển khai | 15 | 10 | 5 |
| **Tổng** | **100** | **57** | **43** |

Phần kỹ thuật và tính mới gần như trọn điểm. Phần kinh doanh, tài chính, nguồn lực và
truyền thông chiếm 43 điểm đang để trống — đây là nơi cần dồn công sức chuẩn bị, không
phải phần công nghệ.
