# KỊCH BẢN & HƯỚNG DẪN QUAY VIDEO DEMO 3 PHÚT
## Vòng Chung Kết Cuộc Thi Khởi Nghiệp Sinh Viên — VNUK Innovation Challenge 2026
**Dự án:** BioCipher — Hệ thống xác thực dữ liệu vân tay bảo mật bằng mã hoá đồng cấu (FHE CKKS)  
**Nhóm tác giả:** Ngô Hoàng Nhật Khang & Hồ Anh Tuấn (Computer Science Engineering, VNUK)

---

## I. QUY ĐỊNH KỸ THUẬT BẮT BUỘC (THEO THỂ LỆ)

| Tiêu chí | Quy định của Ban Tổ Chức | Khuyến nghị khi quay dựng |
|---|---|---|
| **Thời lượng** | **Tối đa 03:00** (Vượt giờ bị trừ điểm/dừng video) | Kịch bản này được căn chuẩn **02:50** (dư 10s an toàn) |
| **Dung lượng** | **$\le$ 500 MB** | Xuất 1080p H.264 bitrate 8 Mbps chỉ tốn ~130 MB |
| **Độ phân giải** | **Tối thiểu 720p** | Bắt buộc quay ở **1080p (1920×1080)** |
| **Định dạng** | **MP4** | Video H.264 + Audio AAC |
| **Người thực hiện** | **Bắt buộc do chính thành viên nhóm quay** | Khang và Tuấn phải xuất hiện trực tiếp trước ống kính |
| **Hạn nộp** | **Trước 11:00 ngày 24/01/2026** | Gửi email: `innovationchallenge@vnuk.udn.vn` |

> [!IMPORTANT]
> **Lưu ý tiêu chí 8.2 chấm điểm tinh thần làm việc nhóm:** Ban giám khảo yêu cầu cả hai thành viên phải cùng xuất hiện và nói rõ phần việc của mình. Do đó, các cảnh có người (Cảnh 1, 6, 8) các bạn dùng điện thoại/webcam quay thật, các cảnh demo phần mềm (Cảnh 3, 4, 5, 7) thì quay màn hình máy tính.

---

## II. KỊCH BẢN CHI TIẾT TỪNG GIÂY (CHIA THEO 8 CẢNH BẮT BUỘC)

### Cảnh 1 · 0:00 – 0:20 (20 giây) · Giới thiệu đội thi
- **Khung hình:** Quay trực diện hai bạn Khang và Tuấn đứng cạnh nhau tại phòng lab VNUK hoặc thư viện. Ánh sáng tự nhiên, máy quay đặt ngang tầm mắt.
- **Phân vai & Lời thoại:**
  - **Khang:** *"Xin chào ban giám khảo, tôi là Nhật Khang."*
  - **Tuấn:** *"Còn tôi là Anh Tuấn, sinh viên Kỹ thuật Khoa học Máy tính tại Viện VNUK, Đại học Đà Nẵng."*
  - **Khang:** *"Dự án của chúng tôi là BioCipher — Hệ thống xác thực vân tay bảo mật bằng mã hoá đồng cấu, được chúng tôi nghiên cứu và vận hành thực tế trong sáu tháng qua."*

---

### Cảnh 2 · 0:20 – 0:45 (25 giây) · Vấn đề nhức nhối & Tính cần thiết
- **Khung hình:** Đồ hoạ chữ số nổi bật trên nền tối: **56 VỤ MUA BÁN TRÁI PHÉP** — **110 TRIỆU BẢN GHI LỘ LỌT** (6 tháng đầu năm 2025). Cắt sang hình ảnh ngón tay đang quét vào đầu đọc.
- **Người nói:** Tuấn
- **Lời thoại:**
  > *"Sáu tháng đầu năm 2025, cơ quan chức năng phát hiện 56 vụ mua bán dữ liệu cá nhân trái phép, liên quan khoảng 110 triệu bản ghi.*  
  > *Mật khẩu bị lộ thì đổi được trong mười giây. Nhưng vân tay bị lộ thì không thể đổi — nó theo người đó suốt đời, và mọi hệ thống dùng vân tay đó đều mất an toàn vĩnh viễn."*

---

### Cảnh 3 · 0:45 – 1:05 (20 giây) · Lỗ hổng chết người của hệ thống hiện tại
- **Khung hình:** Quay màn hình máy tính mở Dashboard tại tab **"Kiến Trúc & An Toàn"** ([http://localhost:8080](http://localhost:8080)), con trỏ chuột chỉ vào ô cảnh báo màu đỏ: **"Máy chủ buộc phải giải mã ra bản rõ"**.
- **Người nói:** Khang
- **Lời thoại:**
  > *"Các hệ thống sinh trắc hiện nay đã mã hoá khi lưu trữ, đã mã hoá khi truyền qua mạng. Nhưng để so khớp được, máy chủ buộc phải giải mã trước.*  
  > *Ngay khoảnh khắc đó, mẫu vân tay nằm nguyên bản trong bộ nhớ RAM. Quản trị viên đọc được, hacker xâm nhập máy chủ cũng chiếm đoạt được toàn bộ."*

---

### Cảnh 4 · 1:05 – 1:30 (25 giây) · Đột phá công nghệ Mã hoá đồng cấu (FHE CKKS)
- **Khung hình:** Chuyển sang tab **"Live Pipeline"** trên Dashboard, chỉ vào khối Server Raspberry Pi 5 có chữ **"KHÔNG GIẢI MÃ"**.
- **Người nói:** Tuấn
- **Lời thoại:**
  > *"Chúng tôi ứng dụng mã hoá đồng cấu CKKS. Lược đồ mật mã này cho phép thực hiện phép trừ, bình phương và cộng dồn trực tiếp trên bản mã.*  
  > *Thiết bị nhúng mã hoá vector vân tay rồi mới gửi đi. Máy chủ tính toán khoảng cách giữa hai bản mã mà không cần giải mã. Máy chủ không giải mã được — đơn giản vì nó hoàn toàn không có khoá bí mật!"*

---

### Cảnh 5 · 1:30 – 2:05 (35 giây) · Demo chạy thật trên phần cứng (Trọng tâm kỹ thuật)
- **Khung hình:** **Quay màn hình thật**. Gạt bật công tắc **"AUTOMATION / TỰ ĐỘNG CHU KỲ"** trên Dashboard (hoặc mở Terminal chạy lệnh `python demo_dashboard/auto_runner.py 101_1`).
  - Để bảng kết quả đối chiếu hiện ra.
  - Zoom chuột vào hai cột: **Bản Rõ** vs **Bản Mã (FHE)** và hai cột thứ hạng **#1 / #1**.
- **Người nói:** Khang
- **Lời thoại:**
  > *"Đây là hệ thống đang chạy thật trên phần cứng Raspberry Pi 5. Một mẫu vân tay được so khớp với 79 bản ghi trong cơ sở dữ liệu.*  
  > *(Dừng 2 giây để bảng số liệu hiện ra)*  
  > *Hai cột này là cùng một đại lượng khoảng cách. Cột trái tính theo cách thông thường, cột phải tính hoàn toàn trên bản mã FHE. Thứ hạng của hai cột trùng khớp nhau tuyệt đối.*  
  > *Chúng tôi kiểm chứng trên bộ chuẩn quốc tế FVC2002 gồm 3.160 cặp vân tay thật: sai số trung bình chỉ 0,0096%. Cả 80/80 truy vấn đều cho kết quả giống hệt khi tính trên dữ liệu gốc.*  
  > *Một lượt truy vấn chỉ tốn 26,51 mili giây!"*

---

### Cảnh 6 · 2:05 – 2:20 (15 giây) · Chiều sâu công nghệ lõi & Năng lực R&D
- **Khung hình:** Quay màn hình cuộn nhanh qua mã nguồn C hoặc Báo cáo Kỹ thuật (Mục 12 — vá lỗi GCC strict-aliasing). Khang và Tuấn cùng ngồi trao đổi trước màn hình code.
- **Người nói:** Tuấn
- **Lời thoại:**
  > *"Trong quá trình xây dựng, nhóm đã phát hiện và tự khắc phục một lỗi vi phạm strict-aliasing trong thư viện gốc của Microsoft — lỗi khiến trình biên dịch sinh mã sai trên kiến trúc 64-bit. Toàn bộ quy trình truy vết lỗi được chúng tôi ghi lại chi tiết trong hồ sơ nghiên cứu."*

---

### Cảnh 7 · 2:20 – 2:40 (20 giây) · Phân khúc thị trường & Cú huých pháp lý
- **Khung hình:** Chuyển sang tab **"Mô Hình Khởi Nghiệp (BMC)"** trên Dashboard, trỏ vào mốc **01/01/2026** và khối **Doanh nghiệp chấm công**.
- **Người nói:** Khang
- **Lời thoại:**
  > *"Khách hàng đầu tiên của chúng tôi là các doanh nghiệp đang dùng máy chấm công và kiểm soát ra vào bằng vân tay.*  
  > *Từ ngày 01/01/2026, Luật Bảo vệ dữ liệu cá nhân 91/2025 có hiệu lực, xếp vân tay vào nhóm dữ liệu nhạy cảm. Chúng tôi không bắt khách hàng phải vứt bỏ thiết bị hiện có — BioCipher chỉ thay thế đúng khâu so khớp, cắm là chạy."*

---

### Cảnh 8 · 2:40 – 2:50 (10 giây) · Thông điệp kết thúc & Lời chào
- **Khung hình:** Hai bạn nhìn thẳng vào ống kính. Dưới màn hình hiện dòng chữ thông tin dự án và địa chỉ GitHub.
- **Lời thoại (Đồng thanh hoặc Tuấn nói):**
  > *"Quyền riêng tư không nên là cái giá của sự tiện lợi.*  
  > *Toàn bộ mã nguồn dự án được công khai minh bạch. Xin trân trọng cảm ơn ban giám khảo!"*
- **Chữ hiện cuối màn hình:**
  ```text
  BioCipher — Hệ Thống Bảo Mật Dữ Liệu Vân Tay (FHE CKKS)
  GitHub: github.com/khang-ngo4444/encrypted-fingerprint-matching
  Ngô Hoàng Nhật Khang · Hồ Anh Tuấn — Viện VNUK, Đại học Đà Nẵng
  ```

---

## III. HƯỚNG DẪN THỰC HÀNH QUAY & DỰNG

### 1. Chuẩn bị quay màn hình máy tính (Cảnh 3, 4, 5, 7)
- **Cách 1 (Đơn giản nhất, có sẵn trên Windows 11/10):**
  - Mở [http://localhost:8080](http://localhost:8080).
  - Bấm phím `F11` trên trình duyệt để toàn màn hình.
  - Bấm tổ hợp phím `Win + Alt + R` (Xbox Game Bar) để bắt đầu quay màn hình độ phân giải 1080p sắc nét. Bấm lại `Win + Alt + R` để dừng quay.
  - File video quay xong nằm ở thư mục: `C:\Users\hotua\Videos\Captures`.
- **Cách 2 (Quay Terminal đen như Cảnh 5):**
  - Mở PowerShell, chỉnh font chữ to lên (Properties ➔ Font ➔ 18pt hoặc 20pt).
  - Chạy lệnh:
    ```powershell
    python D:\Document(D)\CodeTools\encrypted-fingerprint-matching\demo_dashboard\auto_runner.py 101_1
    ```

### 2. Chuẩn bị quay hình người thật (Cảnh 1, 6, 8)
- Đặt điện thoại lên giá đỡ (tripod) ngang tầm mắt, quay ngang màn hình (16:9).
- Đứng ở nơi đủ ánh sáng (trước cửa sổ phòng lab hoặc bật đủ đèn).
- Thu âm bằng tai nghe có mic hoặc micro cài áo để tiếng rõ ràng, không bị vang.

### 3. Dựng video
- Bạn có thể kéo các đoạn video vào **CapCut** (đã có sẵn shortcut trên Desktop của bạn: `CapCut.lnk`) hoặc Premiere Pro.
- Chèn nhạc nền nhẹ nhàng (âm lượng nhạc nền để khoảng -20 dB để không át tiếng nói).
- Kiểm tra lại độ dài video: bảo đảm **dưới 03:00**.

---

## IV. CÁC CÔNG CỤ TÔI CÓ THỂ LÀM GIÙM BẠN NGAY BÂY GIỜ

Nếu bạn cần hỗ trợ các khâu kỹ thuật:
1. **Chuyển đổi / Nén video bằng FFmpeg**: Nếu sau khi bạn quay xong dung lượng vượt quá 500 MB, tôi có thể chạy lệnh FFmpeg nén xuống đúng chuẩn 1080p dung lượng ~100 MB mà không giảm chất lượng.
2. **Xuất ảnh bảng số liệu, biểu đồ slide độ phân giải cao**: Tôi có thể tự động trích xuất các biểu đồ benchmark FVC2002 ra định dạng ảnh chuẩn để bạn chèn vào phần dựng CapCut.
3. **Chỉnh sửa số liệu / kịch bản theo yêu cầu**: Nếu bạn muốn điều chỉnh phần thuyết trình nào, chỉ cần nhắn tôi sẽ sửa ngay.
