# Kịch bản video demo — 3 phút

## Ràng buộc kỹ thuật

| Tiêu chí | Yêu cầu | Ghi chú khi quay |
|---|---|---|
| Thời lượng | ≤ 03:00 | Kịch bản này dài 02:50 |
| Dung lượng | ≤ 500 MB | 1080p, H.264, bitrate 8 Mbps cho ra ~130 MB |
| Định dạng | MP4 | Xuất H.264 + AAC |
| Độ phân giải | ≥ 720p | Nên quay 1080p |
| Người thực hiện | **Thành viên trong đội** | Bắt buộc, không thuê ngoài |

## Tám nội dung bắt buộc

Thể lệ liệt kê tám nội dung phải có. Bảng dưới đối chiếu với từng cảnh:

| # | Nội dung bắt buộc | Cảnh |
|---|---|---|
| 1 | Giới thiệu đội thi và các thành viên | 1 |
| 2 | Ý nghĩa xã hội, giá trị cộng đồng | 2 |
| 3 | Tóm tắt sản phẩm, lợi thế cạnh tranh, mục tiêu, giá trị, tầm nhìn | 3, 4, 8 |
| 4 | Phân khúc khách hàng và tính khả thi | 7 |
| 5 | Yếu tố công nghệ, đổi mới sáng tạo | 4, 5 |
| 6 | Thông điệp cốt lõi | 2, 8 |
| 7 | Tác động tích cực, ESG, giáo dục STEM, chuyển đổi số | 7, 8 |
| 8 | Bản sắc nhóm, tinh thần khởi nghiệp | 1, 6 |

---

## Cảnh 1 · 0:00 – 0:20 · Giới thiệu đội

**Hình:** Hai thành viên đứng cạnh nhau, phông nền phòng thí nghiệm hoặc thư viện. Ánh sáng
tự nhiên. Máy đặt ngang tầm mắt.

**Lời:**
> Chúng tôi là Khang và Tuấn, sinh viên ngành Kỹ thuật Khoa học Máy tính tại VNUK.
> Đây là Hệ thống bảo mật dữ liệu vân tay — dự án chúng tôi đã xây dựng và chạy được
> trong sáu tháng qua.

**Lưu ý:** mỗi người tự giới thiệu tên và phần việc của mình. Tiêu chí 8.2 chấm tinh thần
làm việc nhóm.

---

## Cảnh 2 · 0:20 – 0:45 · Vấn đề

**Hình:** Đồ hoạ số liệu trên nền tối — 56 vụ, 110 triệu bản ghi. Cắt sang hình minh hoạ
một mẫu vân tay đang được quét.

**Lời:**
> Sáu tháng đầu năm 2025, cơ quan chức năng phát hiện 56 vụ mua bán dữ liệu cá nhân trái
> phép, liên quan khoảng 110 triệu bản ghi.
>
> Mật khẩu bị lộ thì đổi được. Vân tay bị lộ thì theo người đó suốt đời, và mọi hệ thống
> dùng vân tay đó đều mất an toàn vĩnh viễn.

---

## Cảnh 3 · 0:45 – 1:05 · Lỗ hổng

**Hình:** Sơ đồ luồng từ slide 3 — Cảm biến → Mã hoá → **Giải mã** → So khớp → Kết quả.
Làm nổi ô "Giải mã" bằng màu cam, các ô khác mờ đi.

**Lời:**
> Hệ thống hiện nay đã mã hoá khi lưu, đã mã hoá khi truyền. Nhưng để so khớp, máy chủ
> buộc phải giải mã. Ngay khoảnh khắc đó, mẫu vân tay nằm nguyên bản trong bộ nhớ.

---

## Cảnh 4 · 1:05 – 1:30 · Giải pháp

**Hình:** Sơ đồ từ slide 5. Dùng hiệu ứng để ô "So khớp trên bản mã" sáng lên, kèm dòng chữ
"KHÔNG GIẢI MÃ".

**Lời:**
> Chúng tôi dùng mã hoá đồng cấu CKKS. Lược đồ này cho phép cộng, trừ và nhân trực tiếp
> trên dữ liệu đã mã hoá.
>
> Thiết bị mã hoá vector đặc trưng rồi mới gửi. Máy chủ tính khoảng cách giữa hai bản mã.
> Chỉ nơi giữ khoá bí mật mới đọc được kết quả. Máy chủ không giải mã, vì nó không có khoá.

---

## Cảnh 5 · 1:30 – 2:05 · Demo chạy thật

**Hình:** **Quay màn hình thật**, không dựng lại. Mở terminal, gõ lệnh, để bảng kết quả hiện
ra. Phóng to vùng hai cột Bản rõ và Bản mã.

```bash
cd device && ../build/16_match_report 101_1 79
```

**Lời:**
> Đây là hệ thống chạy thật. Lệnh này so một mẫu vân tay với 79 bản ghi trong cơ sở dữ
> liệu, toàn bộ trên dữ liệu đã mã hoá.
>
> *(dừng cho bảng hiện ra)*
>
> Hai cột này là cùng một đại lượng. Cột trái tính theo cách thông thường, cột phải tính
> hoàn toàn trên bản mã. Hai cột thứ hạng trùng nhau ở cả 79 dòng.
>
> Chúng tôi kiểm chứng trên FVC2002 — bộ dữ liệu chuẩn quốc tế, 3.160 cặp. Sai lệch trung
> bình 0,0096%. Cả 80 truy vấn đều cho kết quả giống hệt khi tính trên dữ liệu gốc.
>
> Một truy vấn mất 26,51 mili giây.

**Lưu ý quay:** đây là cảnh quan trọng nhất. Tăng cỡ chữ terminal lên 16–18pt trước khi
quay. Nếu chạy mất vài giây thì cắt dựng cho liền mạch, nhưng **không được dựng lại kết
quả giả**.

---

## Cảnh 6 · 2:05 – 2:20 · Chiều sâu kỹ thuật

**Hình:** Cuộn qua mã nguồn hoặc trang báo cáo. Có thể quay cảnh hai người đang trao đổi
trước màn hình.

**Lời:**
> Trong quá trình xây dựng, chúng tôi phát hiện một lỗi trong thư viện mã hoá của
> Microsoft — lỗi khiến toàn bộ phép mã hoá cho kết quả sai khi biên dịch ở mức tối ưu cao.
> Chúng tôi đã truy ra nguyên nhân và vá lại. Toàn bộ quá trình ghi trong báo cáo kỹ thuật.

**Lưu ý:** cảnh này thể hiện năng lực thật, không phải trình bày suông. Tiêu chí 3.3 chấm
hàm lượng công nghệ lõi.

---

## Cảnh 7 · 2:20 – 2:40 · Khách hàng và tác động

**Hình:** Đồ hoạ ba nhóm khách hàng. Sau đó là ngày 01/01/2026 với dòng chữ Luật 91/2025.

**Lời:**
> Khách hàng đầu tiên là doanh nghiệp đang dùng vân tay cho chấm công và kiểm soát ra vào.
> Họ đã có sẵn thiết bị, đang giữ dữ liệu nhạy cảm, và chịu áp lực tuân thủ trước tiên.
>
> Từ 01/01/2026, Luật Bảo vệ dữ liệu cá nhân xếp vân tay vào nhóm nhạy cảm. Chúng tôi
> không bắt khách hàng thay hệ thống đang chạy — chỉ thay đúng khâu so khớp.

---

## Cảnh 8 · 2:40 – 2:50 · Thông điệp cốt lõi

**Hình:** Hai thành viên, chính diện. Cuối cảnh hiện tên dự án và địa chỉ repo.

**Lời:**
> Quyền riêng tư không nên là cái giá của sự tiện lợi.
>
> Toàn bộ mã nguồn của chúng tôi công khai. Mọi con số vừa nêu đều tự chạy lại được.

**Chữ cuối màn hình:**
```
Hệ thống bảo mật dữ liệu vân tay
github.com/khang-ngo4444/encrypted-fingerprint-matching
Ngô Hoàng Nhật Khang · Hồ Anh Tuấn — VNUK
```

---

## Danh sách cần chuẩn bị trước khi quay

**Quay hình**
- [ ] Cảnh hai thành viên — cảnh 1, 6, 8
- [ ] Quay màn hình terminal chạy `16_match_report` — cảnh 5, cỡ chữ ≥16pt
- [ ] Quay màn hình cuộn mã nguồn hoặc báo cáo — cảnh 6

**Đồ hoạ**
- [ ] Số liệu 56 vụ / 110 triệu — cảnh 2
- [ ] Sơ đồ luồng có ô Giải mã nổi bật — cảnh 3 *(lấy từ slide 3)*
- [ ] Sơ đồ giải pháp — cảnh 4 *(lấy từ slide 5)*
- [ ] Ba nhóm khách hàng và mốc 01/01/2026 — cảnh 7

**Âm thanh**
- [ ] Thu lời bằng micro rời hoặc tai nghe có mic, không thu bằng mic máy tính xách tay
- [ ] Nhạc nền không bản quyền, âm lượng dưới lời nói ít nhất 15 dB

**Kiểm tra trước khi nộp**
- [ ] Thời lượng ≤ 3:00
- [ ] Dung lượng ≤ 500 MB
- [ ] Định dạng MP4, độ phân giải ≥ 720p
- [ ] Mọi hình ảnh, nhạc nền có nguồn hợp lệ
- [ ] Ngôn ngữ thống nhất với slide và phần thuyết trình
