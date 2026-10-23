# Kịch bản trình bày — 5 phút

Viết để kết thúc ở phút 4:40, chừa 20 giây dự phòng. Ban giám khảo có quyền dừng nếu
vượt giờ, nên phần nào chậm thì cắt ngay phần được đánh dấu *có thể bỏ*.

Số trang slide theo bản 13 trang hiện có.

---

## 0:00 – 0:30 · Mở đầu · Slide 1–2

> Kính chào ban giám khảo. Chúng tôi là Khang và Tuấn, sinh viên ngành Kỹ thuật Khoa học
> Máy tính, VNUK. Dự án của chúng tôi là Hệ thống bảo mật dữ liệu vân tay.
>
> Xin bắt đầu bằng một con số. Sáu tháng đầu năm 2025, cơ quan chức năng phát hiện 56 vụ
> mua bán dữ liệu cá nhân trái phép, liên quan khoảng 110 triệu bản ghi.
>
> Mật khẩu bị lộ thì đổi được trong mười giây. Vân tay bị lộ thì không đổi được. Nó theo
> người đó suốt đời, và mọi hệ thống dùng vân tay đó đều mất an toàn vĩnh viễn.

**Lưu ý:** nói chậm, dừng một nhịp sau câu cuối. Đây là câu neo cả bài.

---

## 0:30 – 1:15 · Vấn đề nằm ở đâu · Slide 3–4

> Hệ thống sinh trắc hiện nay đã mã hoá dữ liệu khi lưu, đã mã hoá khi truyền. Nhưng còn
> một lớp chưa ai làm được: mã hoá **trong lúc tính toán**.
>
> Để so khớp hai mẫu vân tay, máy chủ buộc phải giải mã trước. Ngay khoảnh khắc đó, mẫu
> vân tay nằm nguyên bản trong bộ nhớ. Quản trị viên đọc được. Kẻ xâm nhập được máy cũng
> lấy được.
>
> Giới nghiên cứu đã có vài hướng bảo vệ — cancelable biometrics, biohashing, fuzzy vault.
> Cả ba đều vướng cùng một vấn đề: muốn an toàn hơn thì phải chấp nhận nhận dạng kém đi.

**Chuyển ý:** *Chúng tôi không bắt khách hàng chọn giữa hai thứ đó.*

---

## 1:15 – 2:00 · Giải pháp · Slide 5

> Chúng tôi dùng mã hoá đồng cấu — cụ thể là lược đồ CKKS của Microsoft SEAL.
>
> Điểm đặc biệt của mã hoá đồng cấu: cộng, trừ và nhân được **trực tiếp trên dữ liệu đã
> mã hoá**, không cần giải. Thiết bị mã hoá vector đặc trưng rồi mới gửi đi. Máy chủ tính
> khoảng cách giữa hai bản mã, trả về một con số cũng đang ở dạng mã. Chỉ nơi giữ khoá bí
> mật mới đọc được kết quả.
>
> Máy chủ không giải mã ở bất kỳ bước nào. Không phải vì chúng tôi cấm, mà vì nó **không
> có khoá để giải**.

---

## 2:00 – 3:00 · Bằng chứng · Slide 6–7

> Câu hỏi đầu tiên ai cũng hỏi: mã hoá như vậy thì kết quả có còn đúng không?
>
> Chúng tôi kiểm chứng trên FVC2004 DB3_B — bộ dữ liệu chuẩn quốc tế, 80 ảnh vân tay thật,
> so khớp toàn bộ 3.160 cặp.
>
> *(chỉ vào biểu đồ)* Mỗi chấm là một cặp vân tay. Trục ngang là khoảng cách tính theo cách
> thông thường. Trục dọc là cùng khoảng cách đó nhưng tính hoàn toàn trên bản mã. Mọi chấm
> đều nằm trên đường chéo.
>
> Sai lệch trung bình 0,0091%. Trên cả 80 truy vấn, bản ghi gần nhất trùng khớp hoàn toàn
> với khi tính trên dữ liệu gốc. Không một quyết định nào bị đổi.
>
> Câu hỏi thứ hai: chậm đến mức nào? Một truy vấn, đo từ lúc thiết bị nhận dữ liệu tới khi
> ra kết quả: **26,51 mili giây**.

**Lưu ý:** nếu đang chậm giờ, bỏ đoạn mô tả biểu đồ, nói thẳng ba con số.

---

## 3:00 – 3:45 · Vì sao khách hàng chuyển · Slide 8–10

> Ba lý do doanh nghiệp chuyển sang.
>
> **Thứ nhất, không phải thay hệ thống đang chạy.** Cảm biến giữ nguyên, bộ trích đặc trưng
> giữ nguyên, cơ sở dữ liệu giữ nguyên. Chỉ đổi đúng một chỗ: thiết bị mã hoá vector trước
> khi gửi.
>
> **Thứ hai, pháp lý.** Luật Bảo vệ dữ liệu cá nhân 91/2025 có hiệu lực từ đầu năm 2026,
> xếp vân tay vào nhóm nhạy cảm. Dữ liệu không bao giờ nằm ở dạng đọc được trên máy chủ thì
> phần rủi ro doanh nghiệp phải gánh nhỏ đi hẳn.
>
> **Thứ ba, rủi ro nội bộ biến mất.** Quản trị viên có toàn quyền trên máy chủ vẫn không đọc
> được vân tay của ai.

---

## 3:45 – 4:15 · Chi phí phải trả · Slide 9

> Chúng tôi nói thẳng cái giá, vì ban giám khảo sẽ hỏi.
>
> Dữ liệu phình 192 lần. Một phép so khớp mất 26,51 mili giây thay vì 0,0004.
>
> Đổi lại, máy chủ không đọc được dữ liệu sinh trắc ở bất kỳ thời điểm nào — kể cả khi bị
> xâm nhập hoàn toàn. Rủi ro không nằm ở chỗ bảo vệ máy chủ tốt đến đâu, mà ở chỗ máy chủ
> không hề giữ dữ liệu có thể đọc được.

---

## 4:15 – 4:40 · Chốt · Slide 11–13

> Khác với các nền tảng mã hoá đa dụng, chúng tôi chỉ giải một bài toán, nên tối ưu được sâu
> hơn. Khác với thư viện mật mã thuần, khách hàng không phải tự xây. Khác với nhà cung cấp
> sinh trắc hiện nay, chúng tôi không giải mã.
>
> Toàn bộ mã nguồn công khai. Mọi con số vừa nêu, ban giám khảo tự chạy lại được bằng năm
> lệnh.
>
> Xin cảm ơn ban giám khảo.

---

## Phân vai

| Phần | Người trình bày |
|---|---|
| 0:00 – 2:00 — vấn đề và giải pháp | [cần phân công] |
| 2:00 – 3:00 — bằng chứng kỹ thuật | [cần phân công] |
| 3:00 – 4:40 — lợi thế, chi phí, chốt | [cần phân công] |

Tiêu chí 8.2 chấm tinh thần làm việc nhóm, nên cả hai thành viên đều nên nói.

---

## Nguyên tắc khi trình bày

**Không đọc slide.** Slide đã viết đủ ý, người nói bổ sung ngữ cảnh chứ không lặp lại.

**Ba con số phải nhớ nằm lòng:** 26,51 ms · 0,0091% · 80/80. Nếu quên mọi thứ khác, ba con
số này vẫn phải nói đúng.

**Nếu bị hỏi giữa chừng:** trả lời ngắn, hẹn phần hỏi đáp cho câu dài. Thời lượng tính cả
phần bị ngắt.

**Nếu thiết bị trình chiếu hỏng:** phần 0:00–2:00 và 3:00–4:40 không phụ thuộc slide, nói
chay được. Chỉ phần bằng chứng cần biểu đồ — khi đó đọc thẳng ba con số.
