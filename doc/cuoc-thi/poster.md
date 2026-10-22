# Poster trưng bày

Tiêu chí 8.3 dành 5 điểm cho poster và sản phẩm mẫu, yêu cầu thể hiện rõ **ý tưởng**,
**mô hình kinh doanh** và **yếu tố đổi mới sáng tạo**. Bố cục dưới đây phân vùng theo
đúng ba yêu cầu đó.

## Quy cách

| | |
|---|---|
| Khổ | A0 dọc, 841 × 1189 mm |
| Nền | Xanh đậm `#0a1628`, đồng bộ với slide |
| Chữ chính | Trắng ngà `#f4f8fb` |
| Chữ phụ | Xám xanh `#9fb2c6` |
| Nhấn mạnh | Lam `#22d3ee` cho dữ liệu mã hoá, lục `#35c08a` cho kết quả đạt, hổ phách `#e8a33d` cho chi phí |
| Cỡ chữ nhỏ nhất | 24 pt — đọc được từ khoảng cách 1,5 m |

Quy ước màu giống trang báo cáo số liệu: mỗi màu mang đúng một nghĩa, không dùng lại cho
nghĩa khác.

---

## Bố cục

```
┌─────────────────────────────────────────────────┐
│  ① TIÊU ĐỀ                                      │  150 mm
├─────────────────────────────────────────────────┤
│  ② VẤN ĐỀ                                       │  120 mm
├─────────────────────────────────────────────────┤
│                                                 │
│  ③ SƠ ĐỒ GIẢI PHÁP                              │  220 mm
│                                                 │
├──────────────────────┬──────────────────────────┤
│  ④ BẰNG CHỨNG        │  ⑤ BIỂU ĐỒ               │  260 mm
│     (ba con số)      │     (độ trung thực)      │
├──────────────────────┴──────────────────────────┤
│  ⑥ MÔ HÌNH KINH DOANH                           │  200 mm
├─────────────────────────────────────────────────┤
│  ⑦ ĐỔI MỚI SÁNG TẠO                             │  140 mm
├─────────────────────────────────────────────────┤
│  ⑧ CHÂN TRANG — đội ngũ, mã QR                  │   99 mm
└─────────────────────────────────────────────────┘
```

---

## ① Tiêu đề

**HỆ THỐNG BẢO MẬT DỮ LIỆU VÂN TAY** — 120 pt, đậm

So khớp vân tay trên dữ liệu đã mã hoá, máy chủ không giải mã ở bất kỳ bước nào — 42 pt

Logo VNUK góc trái. Tên cuộc thi góc phải.

---

## ② Vấn đề

Ba khối số liệu nằm ngang:

| **56** | **110 TRIỆU** | **KHÔNG ĐỔI ĐƯỢC** |
|---|---|---|
| vụ mua bán dữ liệu cá nhân trái phép, 6 tháng đầu 2025 | bản ghi cá nhân liên quan | vân tay bị lộ thì theo người đó suốt đời |

Số: 90 pt lam. Chú thích: 24 pt xám xanh.

---

## ③ Sơ đồ giải pháp

Lấy sơ đồ từ slide 5, phóng to. Ba khối nối bằng mũi tên:

```
ĐẶC TRƯNG VÂN TAY  →  SO KHỚP TRÊN BẢN MÃ  →  KẾT QUẢ TƯƠNG ĐỒNG
    ĐÃ MÃ HOÁ          KHÔNG GIẢI MÃ
```

Khối giữa tô lam đậm, hai khối ngoài nền tối.

Dưới sơ đồ, một dòng 28 pt:

> CKKS cho phép cộng, trừ và nhân trực tiếp trên dữ liệu đã mã hoá. Máy chủ không giải mã
> vì không giữ khoá.

---

## ④ Bằng chứng

Ba thẻ dọc:

| | |
|---|---|
| **26,51 ms** | một truy vấn, đo từ lúc mã hoá tới khi ra kết quả |
| **0,0096 %** | sai lệch so với tính trên dữ liệu gốc |
| **80/80** | truy vấn cho kết quả giống hệt bản gốc |

Số: 72 pt lục. Chú thích: 24 pt.

Dưới ba thẻ, một dòng nhỏ:

> Kiểm chứng trên FVC2002 DB1_B — 80 ảnh vân tay thật, 3.160 cặp so khớp

---

## ⑤ Biểu đồ

Dùng `bench/charts/06_do_trung_thuc_dark.png` — biểu đồ phân tán, mọi điểm nằm trên đường
chéo.

Chú thích dưới biểu đồ, 24 pt:

> Mỗi chấm là một cặp vân tay. Trục ngang: khoảng cách tính trên dữ liệu gốc. Trục dọc:
> cùng khoảng cách đó, tính hoàn toàn trên bản mã. Nằm trên đường chéo nghĩa là mã hoá
> không làm lệch kết quả.

---

## ⑥ Mô hình kinh doanh

Bốn cột:

| Khách hàng | Giá trị mang lại | Dòng doanh thu | Kênh |
|---|---|---|---|
| Chấm công, kiểm soát ra vào | Tuân thủ Luật 91/2025 | Phí theo thiết bị | Bán trực tiếp |
| Ngân hàng, fintech eKYC | Không đổi hệ thống đang dùng | Phí triển khai | Đối tác tích hợp |
| Hãng sản xuất thiết bị | Không mất độ chính xác | Gói hỗ trợ | Sandbox kỹ thuật |

> **Cần bổ sung:** dự báo doanh thu theo năm. Xem mục 5 trong `doi-chieu-tieu-chi.md`.

---

## ⑦ Đổi mới sáng tạo

Ba điểm, mỗi điểm một dòng 32 pt:

**Chuyên một bài toán** — chỉ giải bài toán so khớp vector sinh trắc, nên tối ưu sâu hơn
nền tảng mã hoá đa dụng.

**Không giải mã** — dữ liệu ở dạng mã từ thiết bị cho tới khi ra kết quả, không có khoảnh
khắc nào lộ bản rõ.

**Cắm vào hệ sẵn có** — nhận vector đặc trưng vào, trả khoảng cách ra. Khách hàng không
phải viết lại hệ thống.

Dưới cùng, cỡ 24 pt hổ phách:

> Trong quá trình xây dựng, nhóm phát hiện và vá một lỗi trong thư viện mã hoá của
> Microsoft khiến toàn bộ phép mã hoá cho kết quả sai ở mức tối ưu cao.

---

## ⑧ Chân trang

Bên trái — đội ngũ:

```
Ngô Hoàng Nhật Khang · Hồ Anh Tuấn
Computer Science Engineering
VNUK Institute for Research & Executive Education
```

Bên phải — mã QR dẫn tới repo, kèm dòng chữ:

> Toàn bộ mã nguồn công khai. Mọi số liệu trên poster tự chạy lại được.

```
github.com/khang-ngo4444/encrypted-fingerprint-matching
```

---

## Sản phẩm mẫu trưng bày cạnh poster

Tiêu chí 8.3 yêu cầu cả poster lẫn sản phẩm mẫu. Phương án: đặt một máy tính chạy sẵn
lệnh demo, người xem tự gõ và xem kết quả.

```bash
cd device && ../build/16_match_report 101_1 79
```

Chuẩn bị trước:
- [ ] Máy đã dựng xong môi trường, chạy thử được
- [ ] Cỡ chữ terminal ≥ 18 pt
- [ ] In sẵn một bản kết quả khổ A4 phòng khi máy trục trặc
- [ ] Một người trực để giải thích hai cột Bản rõ và Bản mã
