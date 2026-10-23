# Câu hỏi dự kiến và câu trả lời

Xếp theo nhóm. Mỗi câu có **câu trả lời ngắn** để nói ngay, và phần **nếu bị hỏi sâu** cho
trường hợp giám khảo truy tiếp.

Nguyên tắc: con số nào không có thì nói thẳng là chưa đo, không ước lượng tại chỗ.

---

## Nhóm kỹ thuật

### "Mã hoá rồi vẫn so khớp được, nghe vô lý. Giải thích thế nào?"

**Ngắn:** Mã hoá đồng cấu cho phép cộng, trừ và nhân trực tiếp trên bản mã. Kết quả phép
tính cũng ở dạng mã, giải ra thì đúng bằng kết quả tính trên dữ liệu gốc.

**Sâu:** CKKS mã hoá số thực thành đa thức. Cộng hai bản mã tương ứng cộng hai bản rõ, nhân
cũng vậy. Khoảng cách Euclidean chỉ gồm trừ, bình phương và cộng dồn — cả ba đều làm được
trên bản mã. Bước cộng dồn 512 chiều dùng phép xoay vector, 9 vòng cho 512 chiều.

### "Sai số 0,0091% là gì? Tại sao có sai số?"

**Ngắn:** CKKS là mã hoá xấp xỉ, mỗi phép tính thêm một lượng nhiễu rất nhỏ. Câu hỏi quan
trọng không phải lệch bao nhiêu mà lệch đó có đủ đổi quyết định không. Trên cả 80 truy vấn,
bản ghi gần nhất không đổi lấy một lần.

**Sâu:** Nhiễu của CKKS là tuyệt đối, không phải tương đối — sàn nhiễu gần như cố định. Vì
vậy chúng tôi nhân vector với một hệ số cố định trước khi mã hoá: khoảng cách tăng theo bình
phương hệ số trong khi nhiễu đứng yên, đưa sai số tương đối về mức 0,01%.

### "Con số 99,99% giữ thứ tự xếp hạng — phần còn lại thì sao?"

**Ngắn:** 19 trên 246.480 cặp thứ tự bị đảo. Cả 19 cặp đó đều cách nhau dưới 0,028, trong
khi sai lệch tuyệt đối lớn nhất do mã hoá là 0,096. Chỉ đảo khi hai bản ghi gần nhau tới
mức chính sàn nhiễu không phân biệt nổi, nên bản ghi gần nhất không đổi ở truy vấn nào.

**Sâu:** Phép đo sẵn có trong chương trình chỉ lấy mẫu thưa 561 phép so, và cho ra 100%
tròn trịa. Chúng tôi tính lại trên toàn bộ 246.480 cặp thứ tự mới ra con số thật là
99,99%. Quá trình này ghi trong báo cáo, mục 12.4.

### "26 mili giây có chậm không? So với hệ thống thường thì sao?"

**Ngắn:** Chậm hơn khoảng 51.866 lần so với tính trên dữ liệu gốc. Nhưng 26,51 ms vẫn dưới
ngưỡng người dùng cảm nhận được, nên với chấm công và kiểm soát ra vào thì không ảnh hưởng
trải nghiệm.

**Sâu:** Cần phân biệt hai chế độ. Xác thực 1:1 — người dùng đưa mã định danh kèm vân tay,
hệ thống so đúng một cặp, tốn 26,51 ms bất kể cơ sở dữ liệu lớn cỡ nào. Nhận dạng 1:N — chỉ
đưa vân tay, phải quét toàn bộ, thời gian tỉ lệ thuận với số bản ghi. Chấm công dùng chế độ
1:1.

### "Dữ liệu phình 192 lần, lưu trữ có thành vấn đề không?"

**Ngắn:** 10.000 người tốn 938 MB thay vì 5 MB. Với dung lượng lưu trữ hiện nay thì không
phải trở ngại. Chi phí thật của hệ này nằm ở thời gian CPU, không phải lưu trữ.

### "Nếu khoá bí mật bị lộ thì sao?"

**Ngắn:** Khi đó dữ liệu giải được, giống mọi hệ mã hoá khác. Khác biệt là khoá không nằm
trên máy chủ — máy chủ bị xâm nhập cũng không có khoá.

**Lưu ý:** phần quản lý khoá hiện chưa có tài liệu quy trình. Nếu bị hỏi sâu hơn, nói thẳng
đây là phần đang xây dựng. Xem mục 2.3 trong `doi-chieu-tieu-chi.md`.

### "Độ chính xác nhận dạng bao nhiêu phần trăm?"

**Ngắn:** Trên bộ trích đặc trưng chúng tôi tự viết để kiểm thử, tỉ lệ nhận đúng ở hạng 1
là 90,0% theo giao thức leave-one-out, và 71,4% theo mô hình mỗi người đăng ký một bản mẫu.
Con số đó đo năng lực của bộ trích đặc trưng, không phải của lớp mã hoá — nó giống hệt nhau
khi tính trên dữ liệu gốc và khi tính trên bản mã.

Phải nói rõ giao thức nào, vì hai con số chênh nhau gần 20 điểm. Leave-one-out cho mỗi truy
vấn so với 7 lần quét khác của cùng ngón; mô hình một bản mẫu chỉ có đúng một bản để so, và
đó mới là cách hệ thống chấm công chạy thật.

**Sâu:** Chúng tôi bán lớp bảo mật, không bán bộ nhận dạng. Khách hàng đã có bộ trích đặc
trưng của họ, thường là sản phẩm thương mại chính xác hơn nhiều. Việc chúng tôi phải chứng
minh là lớp mã hoá không làm suy giảm bộ trích đó — và đó chính là con số 80/80.

Không né câu hỏi này. Trả lời thẳng kèm lý do thì mạnh hơn là vòng vo.

---

## Nhóm kinh doanh

### "Doanh thu dự kiến bao nhiêu?"

**Trạng thái hiện tại: chưa có số liệu.** Cần chuẩn bị trước khi thi — đây là 5 điểm trong
thang chấm.

Nếu đến lúc thi vẫn chưa có, trả lời trung thực: mô hình định giá đã xác định gồm phí theo
thiết bị, phí triển khai và gói hỗ trợ, nhưng chưa có số liệu dự báo vì chưa khảo sát giá
thị trường. Nói vậy tốt hơn là bịa một con số rồi không bảo vệ được.

### "Ai là đối thủ? Vì sao họ không làm được?"

**Ngắn:** Ba nhóm. Zama, Duality, Enveil làm nền tảng mã hoá đồng cấu đa dụng — khách hàng
vẫn phải tự xây phần sinh trắc. Microsoft SEAL là thư viện, không phải sản phẩm. Nhà cung
cấp sinh trắc hiện nay thì bắt buộc giải mã khi so khớp.

**Sâu:** Họ làm được về mặt kỹ thuật. Khác biệt của chúng tôi là chuyên một bài toán nên
tối ưu sâu hơn, và đã chạy được trên thiết bị tài nguyên hạn chế.

### "Vì sao khách hàng chọn sinh viên thay vì nhà cung cấp lớn?"

**Ngắn:** Vì hiện chưa nhà cung cấp sinh trắc nào tại Việt Nam cung cấp so khớp không giải
mã. Chúng tôi không thay thế họ — chúng tôi bổ sung đúng lớp họ đang thiếu, và tích hợp
được vào hệ thống sẵn có của họ.

### "Bảo vệ tài sản trí tuệ thế nào khi mã nguồn công khai?"

**Ngắn:** Giá trị không nằm ở dòng mã. Thư viện mã hoá vốn đã là nguồn mở của Microsoft.
Giá trị nằm ở việc biết chọn tham số nào, tối ưu ở đâu, và đã kiểm chứng được trên dữ liệu
thật — những thứ đó mất sáu tháng để có.

Công khai mã nguồn còn là lợi thế truyền thông: mọi tuyên bố đều kiểm chứng được.

---

## Nhóm triển khai

### "Đội có hai người, triển khai thế nào?"

**Trạng thái: cần chuẩn bị.** Xem mục 6.1 trong `doi-chieu-tieu-chi.md`.

### "Cần bao nhiêu vốn?"

**Trạng thái: chưa có số liệu.** Xem mục 6.2.

### "Sản phẩm đã có khách hàng thử chưa?"

Trả lời trung thực theo tình hình thực tế tại thời điểm thi. Nếu chưa, nói rõ là chưa và
nêu kế hoạch tiếp cận.

---

## Ba điều không được làm

**Không bịa số.** Mục nào chưa đo thì nói chưa đo. Giám khảo truy một câu là lộ, mất nhiều
hơn được.

**Không nói "hệ thống của chúng tôi chính xác 99%".** Độ chính xác nhận dạng do bộ trích
đặc trưng quyết định. Con số của chúng tôi là độ trung thực của lớp mã hoá.

**Không hứa tính năng chưa có.** Nếu được hỏi về khuôn mặt hay mống mắt, trả lời: cùng bài
toán so khớp vector nên dùng lại được phần lớn công nghệ, nhưng chưa làm và chưa đo.
