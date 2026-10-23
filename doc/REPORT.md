# Báo cáo: dựng luồng SEAL-Embedded → Microsoft SEAL → giải mã

Ngày: 2026-09-04, cập nhật 2026-10-18 · Nền: Raspberry Pi 5 (Cortex-A76 4 nhân
2,4 GHz, 8 GB RAM), aarch64, GCC 13.3.0

---

## 0. Mục tiêu và kết quả

**Mục tiêu:** dựng luồng mã hóa đồng cấu đầu-cuối.

```
   THIET BI (SEAL-Embedded)          SERVER (Microsoft SEAL)         GIAI MA
   ------------------------          -----------------------         -------
   ma hoa a, b bang pk        --->   d = a - b
   (chi ma hoa, khong tinh)          d^2  + relinearize
                                     rescale
                                     rotation-sum 9 tang       --->   sk
                                     (tong 10 lan key switching)      -> khoang cach
```

Phân vai đúng thiết kế của bài báo gốc (Natarajan & Dai, TCHES 2021, Figure 1):
thiết bị **chỉ mã hóa**, server tính trên bản mã, chỉ nơi giữ `sk` mới giải được.

**Kết quả: chạy được.** Khoảng cách Euclidean 512 chiều, chạy 5 lần:

```
tinh chay: 512.000000
giai ma  : 512.021819  511.919612  512.036290  511.926327  511.908129
sai so   : 4.26e-05    1.57e-04    7.09e-05    1.44e-04    1.79e-04
5/5 DAT
```

Trên đường đi phát hiện **một lỗi undefined behavior trong SEAL-Embedded** làm hỏng
toàn bộ đường mã hóa khi biên dịch ở mức tối ưu cao trên nền 64-bit.

---

## 1. Xuất phát: repo không build được

### 1.1 Hiện trạng ban đầu

Repo chứa **ba bản Microsoft SEAL lệch nhau** (4.1, 3.7.2, 4.3), cùng build artifact
đã commit vào git mang đường dẫn tuyệt đối của một máy khác. CMake từ chối:

```
CMake Error at CMakeLists.txt:7 (add_subdirectory):
  The source directory
    /home/ourpi/CoreMetEncrypt/lib
  does not contain a CMakeLists.txt file.
```

```
CMake Error: The current CMakeCache.txt directory
  /home/ourpi/CoreMetEncrypt/adapter/thirdparty/seal-subbuild/CMakeCache.txt
is different than the directory
  /home/ourpi/SEAL-Embedded/adapter/thirdparty/seal-subbuild
where CMakeCache.txt was created.
```

Nguyên nhân: mã nguồn SEAL-Embedded đã được dời từ `lib/` sang `device/`, nhưng
`CMakeLists.txt` gốc vẫn trỏ vào `lib/`.

### 1.2 Xử lý

Trước khi xóa, đối chiếu `diff -rq` với upstream: `adapter/` (nguồn), `device/lib`,
`device/bench`, `device/test` **giống hệt upstream**, không có sửa đổi riêng nào bị mất.

Đã xóa ~249 MB: `SEAL/`, `SEAL-Build/`, `adapter/`, `device/`, `lib/`, `build-demo/`.
Sao lưu `device/adapter_output_data/` (75 file dữ liệu sinh, không có trong upstream).

Clone lại và build:

| Thư viện | Phiên bản | Artifact |
|---|---|---|
| Microsoft SEAL | 4.4.4 (`96ae20d`) | `SEAL/build/lib/libseal-4.4.a` |
| SEAL-Embedded | 1.1.0 (`0913fa9`) | `device/build/bin/libseal_embedded.a` |
| SE-Adapter | — | `adapter/build-seal44/bin/se_adapter` |

### 1.3 Quy ước tên — đọc trước phần sau

Repo có **hai thư viện khác nhau**, tên thư mục dễ gây nhầm:

| Ký hiệu | Thư mục thật | Là gì |
|---|---|---|
| **SE** | `device/` | SEAL-Embedded, thư viện thiết bị, chỉ mã hóa |
| **SE-Adapter** | `adapter/` | SEAL-Embedded, adapter chạy trên PC |
| **MS-SEAL** | `SEAL/` | Microsoft SEAL, tính toán + giải mã |

Điểm dễ nhầm nhất: **`adapter/` là của SEAL-Embedded, không phải của Microsoft SEAL.**
Và bên trong `adapter/thirdparty/` lại có một bản Microsoft SEAL riêng.

---

## 2. Thống nhất phiên bản Microsoft SEAL

**Vấn đề:** upstream ghim cứng SEAL 3.7.2 cho SE-Adapter, trong khi phía tính toán
dùng 4.4.4. Hai bản serialize key và ciphertext khác nhau.

### Thay đổi 1 — `adapter/CMakeLists.txt:97`

```diff
- GIT_TAG        79234726053c45eede688400aa219fdec0810bd8 # 3.7.2
+ GIT_TAG        96ae20db6649bc7c24e9a34994bedd70f4951f60 # 4.4.4
```

### Thay đổi 2 — `adapter/CMakeLists.txt:115`

```diff
- find_package(SEAL 3.7 QUIET REQUIRED)
+ find_package(SEAL 4.4 QUIET REQUIRED)
```

**Kết quả:** build sạch, **không một lỗi hay cảnh báo**. Lo ngại API 3.7 → 4.4 gãy
không xảy ra — adapter chỉ dùng phần API ổn định (`KeyGenerator`,
`EncryptionParameters`, `CoeffModulus::Create`, `SEALContext`).

Build vào thư mục riêng `adapter/build-seal44/` để giữ bản 3.7.2 cũ mà đối chiếu.

---

## 3. Chứng minh bộ tham số

Trước khi nối thiết bị, kiểm bộ tham số bằng **Microsoft SEAL thuần** — cô lập câu
hỏi "tham số có gánh nổi 1 relinearize + 9 rotation không?" khỏi mọi thứ liên quan
tới SEAL-Embedded.

Code: `src/01_seal_only_euclidean.cpp`

### 3.1 Special prime 19-bit quá nhỏ cho key switching

Bài báo gốc, mục 5.1:

> *"Microsoft SEAL requires a prime to be reserved for the purposes of noise reduction.
> This prime does not need to be added during encryption, but is automatically added
> during key generation for evaluation keys. Therefore, an encryption with 3 primes on
> SEAL-Embedded corresponds to an evaluation with 4 primes in Microsoft SEAL."*

Bộ mặc định `{30,30,30,19}`: special prime `P = 2^19`, working prime `2^30`. Nhiễu mỗi
lần key switching tỉ lệ `q_max/P = 2^11` — khuếch đại ~2000 lần. Flow cần **10 lần**
key switching (1 relin + 9 rotation cho `log₂512 = 9`). Không sống nổi.

SEAL-Embedded có sẵn cấu hình thay thế, chọn bằng cặp `#ifdef` song song ở
`adapter/utils.cpp:115-125` và `device/lib/parameters.c:204-218`:

| Cấu hình | Working primes | Special prime | Tổng bit | Quan hệ |
|---|---|---|---|---|
| Mặc định | 30, 30, 30 | **19** | 109 | `P` nhỏ hơn `q` ~2000 lần |
| `SE_DEFAULT_4K_27BIT` | 27, 27, 27 | **28** | 109 | `P` **lớn hơn** `q` |

Cả hai đều đúng 109 bit — chạm trần bảo mật 128-bit ở n=4096 theo Homomorphic
Encryption Security Standard. Khác nhau ở cách chia ngân sách.

#### Thay đổi 3 — `device/lib/user_defines.h:162`

```diff
- // #define SE_DEFAULT_4K_27BIT
+ #define SE_DEFAULT_4K_27BIT
```

#### Thay đổi 4 — `adapter/utils.h:24`

```diff
- // #define SEALE_DEFAULT_4K_27BIT
+ #define SEALE_DEFAULT_4K_27BIT
```

**Phải sửa cả hai, đồng bộ.** Upstream cảnh báo ở `adapter/utils.h:22`:
*"Make sure to uncomment SE_DEFAULT_4K_27BIT in the device as well."* Lệch một bên là
hai phía hiểu khác nhau về modulus.

Moduli sinh ra sau khi đổi, đọc từ tên file trong `device/adapter_output_data/`:

| | Working primes | Special prime |
|---|---|---|
| Cũ | 1053818881, 1054015489, 1054212097 (≈2^30) | 417793 (≈2^19) |
| Mới | 134012929, 134111233, 134176769 (≈2^27) | **268369921** (≈2^28) |

### 3.2 Scale 2^20 quá thấp so với prime 27-bit

Chạy lần đầu với cấu hình 27-bit: **sai số 5.9%**, vượt xa ngưỡng 1%.

```
sau encrypt            level=2 scale=2^20.0 size=2
sau square             level=2 scale=2^40.0 size=3
sau relinearize        level=2 scale=2^40.0 size=2
sau rescale            level=1 scale=2^13.0 size=2     <-- dang ngo
sau rotation-sum       level=1 scale=2^13.0 size=2
```

**Tách nguyên nhân.** Hai nghi phạm không phân biệt được bằng một phép đo: (A) scale
tụt quá thấp, (B) nhiễu tích lũy qua 9 lần key switching. Cách tách: đo sai số ở
**hai mốc** trong cùng một lần chạy — ngay sau rescale (chỉ chứa A) và sau
rotation-sum (chứa A+B).

Code: `src/02_scale_sweep.cpp`

```
scale   scale sau resc  sai so d^2      sai so tong     level
--------------------------------------------------------------
2^16    2^5             2199.029%       2633.059%       1
2^18    2^9             137.8859%       167.5110%       1
2^20    2^13            8.329031%       0.749521%       1
2^22    2^17            0.505398%       0.575012%       1
2^24    2^21            0.032384%       0.046073%       1
2^25    2^23            0.010031%       0.011394%       1
2^26    2^25            0.003042%       0.008668%       1
2^27    2^27            0.001232%       0.000013%       1
```

**Kết luận A — rotation vô can.** Ở mọi mức scale, `sai so tong` xấp xỉ `sai so d^2`.
Chín lần key switching gần như không thêm nhiễu. Điều này **xác nhận việc đổi special
prime 19→28 bit đã có tác dụng**: nếu vẫn là 19-bit, cột `sai so tong` phải nổ tung.

**Kết luận B — thủ phạm là scale.** `2^20` bình phương thành `2^40`, rescale chia cho
prime `2^27`, còn `2^13`. Quy tắc chung: scale nên xấp xỉ độ lớn prime.

**Cảnh báo phương pháp.** Nhìn bảng dễ tưởng scale 2^20 đạt ngưỡng 1% (0.75%).
Chạy lại bài 01 năm lần:

```
sai so tuong doi: 3.5%,  21.0%,  17.2%,  2.6%,  10.7%
```

Dao động 2.6% → 21%. Nhiễu mã hóa ngẫu nhiên mỗi lần chạy; ở scale 2^13 biên độ nhiễu
ngang ngửa tín hiệu. **Một lần chạy đạt không chứng minh được gì.**

#### Thay đổi 5 — `device/lib/parameters.c:210`

```diff
  #ifdef SE_DEFAULT_4K_27BIT
          case 4096:
              se_assert(parms->nprimes <= 3);
              set_parms_ckks_27bit_helper(parms);
-             parms->scale = pow(2, 20);
+             // Upstream dat 2^20. Doi sang 2^25 vi 2^20 sau square+rescale chi
+             // con 2^13, sai so 3-21%.
+             parms->scale = pow(2, 25);
              break;
```

#### Thay đổi 6 — `adapter/adapter.cpp:243-244`

```diff
          case 4096:
-             cout << "27, 27, 27, 28}, scale = pow(2, 20)" << endl;
-             scale = pow(2, 20);
+             cout << "27, 27, 27, 28}, scale = pow(2, 25)" << endl;
+             scale = pow(2, 25);
              break;
```

Cả hai đều nằm trong nhánh `#ifdef` của cấu hình 27-bit, không đụng cấu hình 30-bit
gốc của upstream.

**Kết quả sau khi sửa**, chạy 5 lần:

```
sai so tuong doi: 0.0016%,  0.0346%,  0.0200%,  0.0040%,  0.0237%     5/5 DAT
```

Cải thiện ba bậc độ lớn, hết dao động loạn.

---

## 4. Nối SE → MS-SEAL: cuộc truy lỗi

### 4.1 Cầu nối có sẵn của upstream

Không cần tự viết. `verify_ciphertexts` ở `adapter/adapter.cpp:32` chính là đường
SE → MS-SEAL, gọi qua menu option 2.

| Bước | Code |
|---|---|
| Thiết bị in ciphertext ra stdout | `device/test/api_tests.c:30` (`test_print_ciphertexts`) đóng vai hàm gửi mạng giả |
| Hứng stdout vào file text | `./build/bin/seal_embedded_tests > device/out_asym_api_tests` |
| Adapter nạp vào SEAL Ciphertext | `adapter/fileops.h:203` (`ct_string_file_load`) |
| Adapter nạp khóa bí mật | `adapter/fileops.h:102` (`sk_bin_file_load`) |

`device/test/main.c:133-134` xác nhận đúng cách dùng: *"Check the result with the
adapter by writing output to a text file and passing that to the adapter verify
ciphertexts functionality"*.

#### Thay đổi 7 — `device/test/main.c:107-141`

Tắt toàn bộ test khác, chỉ chạy một bài. Lý do: output của binary được hứng vào file
ciphertext; nếu chạy cả bộ test thì file lẫn output của fft/ntt/modulo, adapter parse sai.

```diff
- test_sample_poly_uniform(n);
- test_add_uint();
- test_fft(n);
- test_ckks_encode_encrypt_sym(n, nprimes);
+ // test_sample_poly_uniform(n);
+ // test_add_uint();
+ // test_fft(n);
+ // test_ckks_encode_encrypt_sym(n, nprimes);
  ...
- // test_ckks_api_asym();
+ test_ckks_api_asym();
```

### 4.2 Chế độ đối xứng bế tắc — thiếu sót của upstream

Chạy `test_ckks_api_sym()` rồi verify:

```
(ntt) ct1[0] : { 0, 0, 0, 0, 0, 0, 0, 0 }
msg_d        : { -8.2e+18, -1.3e+19, 3.6e+19, ... }
```

`c1` toàn số 0. Không phải lỗi parse — chính thiết bị in ra `c1 : { 0, 0, ... }`.
Ba mảnh code ghép lại:

1. `device/lib/seal_embedded.c:155-158` gọi `ckks_encode_encrypt_sym(...)` với hai
   tham số cuối `s_save` và `c1_save` đều là **`NULL`** — không lưu c1.
2. `device/lib/ckks_sym.c:219-227` sinh c1, ghi chú *"At this point, it is safe to
   send c1 away. This will allow us to re-use c1's memory."*, rồi vùng nhớ của c1 bị
   dùng lại cho `ntt_pte`.
3. `device/lib/seal_embedded.c:202` mới gửi `c1_ptr` — **sau khi** vùng nhớ bị ghi đè.

Bằng chứng phụ, thiết bị tự in ra ngay đầu output:

```
	           c1: 0xaaaaf74dd2b0
	      ntt_pte: 0xaaaaf74dd2b0      <- trung dia chi
```

Đường thay thế đúng đắn là gửi seed thay cho cả đa thức c1, nằm sau
`#ifdef SE_ENABLE_SYM_SEED_CT` (`seal_embedded.c:185`) — nhưng ngay trên nó là:

```c
// TODO: Finish this feature, add to defines
```

Define đó **không tồn tại ở đâu trong thư viện**. Tính năng bỏ dở.

### 4.3 Chuyển sang chế độ bất đối xứng

Hợp mô hình IoT hơn: thiết bị giữ khóa công khai, server giữ khóa bí mật.

`SE_USE_MALLOC` đang bật (`user_defines.h:141`), mà khối define chọn chế độ mã hóa chỉ
áp dụng **khi malloc tắt** (`user_defines.h:167-173`). Nên không cần đổi define — chỉ
cần gọi hàm test khác, cộng một sửa ở adapter.

#### Thay đổi 8 — `adapter/adapter.cpp:332`

```diff
- bool is_sym = true;  // TODO: Make this command line settable
+ bool is_sym = false;
```

Cũng là một `TODO` upstream chưa làm.

**Kết quả:** `c1` hết số 0, giải mã từ `1e19` xuống `1e-4`. Tiến bộ, nhưng vẫn sai.

### 4.4 Cái bẫy: adapter báo "pass" giả

`verify_ciphertexts` in `All tests passed!! :) :)` **kể cả khi sai hoàn toàn**, vì
đoạn so sánh thật bị comment sẵn trong upstream.

#### Thay đổi 9 — `adapter/adapter.cpp:181-183`

```diff
- // int precision = 4;
- // print_poly("values_orig", values_orig, print_size, precision);
- // bool are_equal = are_equal_poly(msg_d, values_orig, slot_count);
- // assert(are_equal);
- // if (!are_equal) nfailures++;
+ int precision = 4;
+ print_poly("values_orig", values_orig, print_size, precision);
+ bool are_equal = are_equal_poly(msg_d, values_orig, slot_count);
+ if (!are_equal) nfailures++;
```

#### Thay đổi 10 — `adapter/adapter.cpp:62` (công cụ chẩn đoán, giữ lại)

Thêm biến môi trường `SE_USE_SEAL_SK` để chọn đường nạp khóa, phục vụ loại trừ:

```c
bool use_seal_format_sk = (getenv("SE_USE_SEAL_SK") != nullptr);
```

### 4.5 Triệu chứng

Thiết bị mã hóa xung đơn vị `{1.00, 0, 0, ...}`, SEAL giải ra:

```
msg_d : { 0.00015, -3e-05, 0.00042, 0.0001, -7.9e-05, ... }
```

Định lượng: `pt ≈ 3355`, lẽ ra phải là `Δ·1 = 2^25 = 33554432`. Chênh 4 bậc. Các giá
trị mang dấu ngẫu nhiên → **nhiễu**, không phải `1.0` bị chia sai tỉ lệ. Thông điệp
**biến mất hẳn**.

Nghịch lý: **thiết bị tự nhất quán hoàn toàn** — tự mã hóa rồi tự giải mã khớp, build
Debug bật hết `se_assert` vẫn sạch — **nhưng SEAL không giải được bằng đúng khóa
tương ứng.**

### 4.6 Loại trừ có hệ thống

Mọi kết luận đều dựa trên phép đo, không phải suy đoán.

| # | Nghi phạm | Cách kiểm | Kết quả |
|---|---|---|---|
| 1 | Bộ tham số 27-bit ta đổi | Quay về 30-bit gốc upstream, sinh lại toàn bộ, build lại | **Sai y hệt** → thay đổi của ta vô can |
| 2 | Khóa nạp sai định dạng | Nạp song song `sk_bin_file_load` (dạng SE) và `sk_seal_load` (dạng SEAL) | `msg_d` **trùng khít từng chữ số** |
| 3 | Dạng NTT của `sk` | `adapter/fileops.cpp:165-170` có chuyển ngược; in `is_ntt_form()` | `= 1`, đúng |
| 4 | Cặp khóa pk/sk không khớp | Vòng tròn khép kín trong SEAL bằng **chính khóa đọc từ file** | `{0.999993, 1.99997, 3.00001}` — chính xác |
| 5 | Scale lệch hai phía | Thiết bị in `scale: 33554432.00` | `= 2^25`, khớp adapter |
| 6 | Lệch vị trí đọc file | Bật `print_poly("values_orig", ...)` | Đọc đúng `{1,0,0}`, `{2,0,0}`, `{1,1,1}`, `{2,2,2}` đúng thứ tự |
| 7 | Dữ liệu bị cắt | Đếm giá trị mỗi dòng | `c0`/`c1` đủ 4096, `v (cleartext)` đủ 2048 |
| 8 | Thứ tự modulus | `parameters.c:138-140` vs `utils.cpp:32-34` | Cùng thứ tự |
| 9 | Miền NTT không tương thích | `src/03_ntt_order_check.cpp`, thử hoán vị đảo bit | **Tệ đi 23 bậc độ lớn** |
| 10 | `pk` cắt special prime không hợp lệ | `src/04_pk_restrict_check.cpp`: `(pk0 + m, pk1)` với `u=1` | `{1, 8.3e-07, -2.9e-06}` — **hợp lệ** |
| 11 | Dữ liệu ở miền hệ số | `src/05_domain_check.cpp` | NTT đúng; miền hệ số ra `1e+20` |
| 12 | Bộ file pk từng prime sai | `src/06_pkfile_check.cpp`, so từng bit với bản SEAL | **Lệch 0/4096 hệ số** cả 3 prime |
| 13 | Bước encode của thiết bị sai | `src/07_pte_compare.cpp` | Lệch tối đa **12/16384** — sai số làm tròn IFFT |
| 14 | Quy ước dấu ngược | `src/08_sign_check.cpp`, thử 4 tổ hợp dấu | Không tổ hợp nào ra `{1,0,0}` |
| 15 | Thiết bị tự sinh khóa riêng | `seal_embedded.c:38-39` | `pk_from_file = 1`, `sample_s = 0` |
| 16 | Gọi khóa ở chỗ khác | Gắn print vào `load_pki`, và giấu 7 thư mục `adapter_output_data` từng cái | Chỉ **một** thư mục có tác dụng, đúng thư mục adapter ghi vào |

Phép loại trừ mạnh nhất là **#4, vòng tròn khép kín**: mã hóa bằng pk đọc từ file,
giải bằng sk đọc từ file, cùng context, cùng scale — chỉ bỏ thiết bị ra ngoài. Chính
xác tới 5 chữ số. Toàn bộ phía SEAL sạch; biến duy nhất còn lại là dữ liệu thiết bị.

Phép **#16** đáng chú ý về phương pháp: giấu cả 7 thư mục cùng tên trên máy rồi bật
lại từng cái. Chỉ `CoreMetEncrypt/device/adapter_output_data` làm thiết bị chết
(exit 1, 0 ciphertext); 6 thư mục còn lại — kể cả bộ ở `/home/ourpi/SEAL-Embedded/`
từ repo cũ — hoàn toàn không được đụng tới.

---

## 5. Nguyên nhân gốc: undefined behavior

### 5.1 Truy vết

Bật dòng in mà upstream để sẵn ở `device/lib/seal_embedded.c:143` và
`device/lib/ckks_asym.c:283`, đo từng bước:

```
conj_vals_int truoc reduce : 4095 he so khac 0, bien do lon nhat 16391    <- DUNG
pte sau reduce             : { 0, 0, ..., 1053818881, 1053818881 }        <- HONG
ntt_pte dev                : 4095/4095 he so bang 0                       <- HONG
```

`1053818881` chính là `q0`. Nửa đầu `0`, nửa sau `q0` — **cả hai đều đồng dư 0 mod q0**.
Đa thức sau quy giản hoàn toàn bằng 0, nên NTT của nó bằng 0, nên phép cộng `m` vào
`c0` cộng **số không**.

Khoanh tiếp bằng cách in modulus và thử quy giản trực tiếp:

```
[reduce] mod->value=1053818881 const_ratio=[324793530, 4]
[reduce] reduce_pte_core(16384) = 0   (ky vong 16384)
[reduce] reduce_pte_core(1)     = 0   (ky vong 1)
```

Quy giản **số 1** theo modulus `1053818881` ra **0**. `const_ratio` đúng bằng
`floor(2^64/q)`, tức tỉ số Barrett lành.

### 5.2 Bằng chứng quyết định

Cùng một dòng code, cùng dữ liệu, **chỉ khác mức tối ưu**:

| Build | `reduce_pte_core(1)` | `reduce_pte_core(16384)` |
|---|---|---|
| Release `-O3` | **0** | **0** |
| Debug không tối ưu | **1** | **16384** |

Đó là định nghĩa của undefined behavior bị trình tối ưu khai thác.

### 5.3 Dòng code gây lỗi

`device/lib/ckks_common.c:229` (bản gốc upstream):

```c
ZZ reduce_pte_core(int64_t conj_vals_int, const Modulus *mod)
{
    uint64_t coeff_abs = (uint64_t)(llabs(conj_vals_int));
    ZZ mask            = (ZZ)(conj_vals_int < 0);

    ZZ *coeff_abs_vec = (ZZ *)&coeff_abs;          // <-- VI PHAM STRICT ALIASING
    ZZ coeff_crt      = barrett_reduce_64input_32modulus(coeff_abs_vec, mod);
    ...
}
```

`ZZ` là `uint32_t`. Đọc một biến `uint64_t` qua con trỏ `uint32_t*` là undefined
behavior. Trình biên dịch được phép giả định hai kiểu này không bao giờ trỏ chung vùng
nhớ, nên ở `-O3` nó bỏ qua hoặc sắp xếp lại phép ghi vào `coeff_abs`. Barrett đọc rác.

### 5.4 Chuỗi hậu quả

```
reduce_pte_core tra 0 cho moi he so
        |
        v
pte sau reduce = { 0, 0, ..., q0, q0, ... }     <- deu dong du 0 mod q0
        |
        v
ntt(m + e0) = 0 hoan toan
        |
        v
poly_add_mod_inpl(pk_c0, ...) cong SO KHONG vao c0
        |
        v
c0 = pk0·u  (khong chua m)
        |
        v
c0 + c1·s = u·e_pk + e0 + e1·s = NHIEU THUAN
```

Con số khớp: đa thức giải mã có hệ số cỡ **3355**, đúng tầm biên độ của riêng số hạng
nhiễu, trong khi `m` lẽ ra cỡ **16384**.

### 5.5 Cách sửa

#### Thay đổi 11 — `device/lib/ckks_common.c:229-239` (nguyên nhân gốc)

```diff
  uint64_t coeff_abs = (uint64_t)(llabs(conj_vals_int));
  ZZ mask            = (ZZ)(conj_vals_int < 0);

- ZZ *coeff_abs_vec = (ZZ *)&coeff_abs;
- ZZ coeff_crt      = barrett_reduce_64input_32modulus(coeff_abs_vec, mod);
+ ZZ coeff_abs_vec[2];
+ memcpy(coeff_abs_vec, &coeff_abs, sizeof(coeff_abs));
+ ZZ coeff_crt = barrett_reduce_64input_32modulus(coeff_abs_vec, mod);
```

Kèm `#include <string.h>` ở `ckks_common.c:8`.

`memcpy` là cách chuẩn để reinterpret bytes trong C mà không phạm strict aliasing;
trình biên dịch tối ưu nó thành lệnh load/store trực tiếp, **không mất hiệu năng**.

### 5.6 Kết quả

Bản **Release `-O3`**, không hạ mức tối ưu:

```
reduce_pte_core(16384) = 16384     (dung)
reduce_pte_core(1)     = 1         (dung)
```

Thiết bị mã hóa `{1, 0, 0, ...}`, Microsoft SEAL giải ra:

```
{ 0.999859, -0.00013846, -0.000141995, -0.000790191 }
```

Sai số 0.014%.

### 5.7 Phạm vi ảnh hưởng

`reduce_pte_core` được gọi bởi `reduce_set_pte` và `reduce_add_pte`
(`ckks_common.c:248, 258`) — dùng trong **cả hai** chế độ đối xứng và bất đối xứng.
Lỗi ảnh hưởng toàn bộ đường mã hóa của SEAL-Embedded khi biên dịch ở mức tối ưu cao
trên nền 64-bit.

Đây là lỗi upstream, không do cấu hình của ta: phép thử đối chứng ở bộ 30-bit gốc cho
kết quả sai y hệt.

---

## 6. Ba cơ chế báo "pass" giả

Cả ba cùng che đúng một lỗi, và là lý do nó ẩn lâu. Đáng đưa vào báo cáo.

**1. Bộ test của thiết bị.** In `values[0]: -6.5` cạnh `values_decoded[0]: -0.026`
— lệch 250 lần — nhưng vẫn kết luận `...done with all tests. All tests passed.`

Dấu hiệu này xuất hiện ngay từ lần chạy test đầu tiên và đã bị bỏ qua vì tin dòng
tổng kết.

**2. `verify_ciphertexts` của adapter.** In `All tests passed!! :) :)` kể cả khi sai
hoàn toàn, vì đoạn so sánh thật bị comment sẵn (`adapter/adapter.cpp:147-149` bản gốc).

**3. Bài test asym của thiết bị tự sinh khóa cục bộ.**
`device/test/ckks_tests_asym.c:205`:

```c
se_assert(!parms.pk_from_file);
```

kèm chú thích dòng 203: *"...check the 'decryption'. Need to generate pk here instead..."*

| Bài test | Dùng pk nào | Tự kiểm chứng |
|---|---|---|
| `test_ckks_encode_encrypt_asym` | tự sinh cục bộ | Có |
| `test_ckks_api_asym` | **từ file** | **Không** — chỉ in ra |

Đường mà flow này cần — mã hóa bằng pk từ file rồi chuyển sang SEAL — **không có bài
test nào của upstream phủ**.

---

## 7. Luồng đầy đủ

Code: `src/09_end_to_end.cpp`

### 7.1 Mắt xích SEAL-Embedded không tự làm được

SEAL-Embedded chỉ mã hóa, không sinh được relinearization key lẫn Galois key. Hai khóa
này sinh bằng Microsoft SEAL **từ chính `sk` mà adapter đã lưu**:

```cpp
SecretKey sk = keygen_tmp.secret_key();
{ ifstream f(keydir + "sk_4096_seal.dat", ios::binary); sk.load(context, f); }

KeyGenerator keygen(context, sk);          // dung dung sk cua adapter
keygen.create_relin_keys(relin_keys);
keygen.create_galois_keys(steps, galois_keys);
```

`steps` chỉ gồm 9 bước lũy thừa 2 (`1, 2, 4, ..., 256`) — sinh thừa chỉ làm phình
bộ nhớ.

### 7.2 Tham số cuối cùng

| | Giá trị |
|---|---|
| degree | 4096 |
| moduli | 134012929, 134111233, 134176769 (27-bit) + 268369921 (28-bit special) |
| scale | 2^25 |
| n (số chiều) | 512 → 9 lần rotation |

### 7.3 Diễn biến level và scale

```
sau khi nap          level=2 scale=2^25.0 size=2
sau sub              level=2 scale=2^25.0 size=2
sau square           level=2 scale=2^50.0 size=3
sau relinearize      level=2 scale=2^50.0 size=2
sau rescale          level=1 scale=2^23.0 size=2
sau rotation-sum     level=1 scale=2^23.0 size=2
```

`square` đẩy scale lên 2^50 và ciphertext phình size 3; `relinearize` kéo về size 2
(tiêu relin key); `rescale` hạ scale về 2^23 và tiêu một prime. Rotation-sum giữ
nguyên cả hai. **Còn dư 1 level** — bộ tham số vẫn có chỗ cho một phép nhân nữa.

### 7.4 Kết quả

Thiết bị mã hóa `a = {1,1,1,...}` và `b = {2,2,2,...}`. SEAL giải kiểm từng cái trước
khi tính: `0.999954` và `1.99903`.

Euclidean 512 chiều, tính chay `512 × (1-2)² = 512`. Chạy 5 lần:

```
giai ma (slot0): 512.021819   sai so tuong doi: 4.26e-05   DAT
giai ma (slot0): 511.919612   sai so tuong doi: 1.57e-04   DAT
giai ma (slot0): 512.036290   sai so tuong doi: 7.09e-05   DAT
giai ma (slot0): 511.926327   sai so tuong doi: 1.44e-04   DAT
giai ma (slot0): 511.908129   sai so tuong doi: 1.79e-04   DAT
```

5/5 đạt, sai số 0.004%–0.018%, ổn định.

---

## 8. Tổng hợp mọi thay đổi

**Tất cả đều thuộc SEAL-Embedded. Microsoft SEAL không bị sửa dòng nào.**

| # | File | Dòng | Trước | Sau | Mục đích |
|---|---|---|---|---|---|
| 1 | `adapter/CMakeLists.txt` | 97 | `GIT_TAG 7923472... # 3.7.2` | `GIT_TAG 96ae20d... # 4.4.4` | thống nhất phiên bản SEAL |
| 2 | `adapter/CMakeLists.txt` | 115 | `find_package(SEAL 3.7 ...)` | `find_package(SEAL 4.4 ...)` | như trên |
| 3 | `device/lib/user_defines.h` | 162 | `// #define SE_DEFAULT_4K_27BIT` | `#define SE_DEFAULT_4K_27BIT` | special prime 19→28 bit |
| 4 | `adapter/utils.h` | 24 | `// #define SEALE_DEFAULT_4K_27BIT` | `#define SEALE_DEFAULT_4K_27BIT` | phải đồng bộ với #3 |
| 5 | `device/lib/parameters.c` | 210 | `parms->scale = pow(2, 20);` | `parms->scale = pow(2, 25);` | scale quá thấp |
| 6 | `adapter/adapter.cpp` | 243-244 | `scale = pow(2, 20);` | `scale = pow(2, 25);` | phải đồng bộ với #5 |
| 7 | `device/test/main.c` | 107-141 | chạy cả bộ test | chỉ `test_ckks_api_asym()` | tránh lẫn output vào file ciphertext |
| 8 | `adapter/adapter.cpp` | 332 | `bool is_sym = true;` | `bool is_sym = false;` | chuyển sang bất đối xứng |
| 9 | `adapter/adapter.cpp` | 181-183 | đoạn so sánh bị comment | bỏ comment | để adapter báo lỗi thật |
| 10 | `adapter/adapter.cpp` | 62 | — | thêm `SE_USE_SEAL_SK` | công cụ chẩn đoán, giữ lại |
| 11 | `device/lib/ckks_common.c` | 229-239 | `ZZ *v = (ZZ *)&coeff_abs;` | `ZZ v[2]; memcpy(v, &coeff_abs, ...)` | **sửa lỗi UB, nguyên nhân gốc** |
| 12 | `device/lib/ckks_common.c` | 8 | — | `#include <string.h>` | cho `memcpy` |

Ba nhóm: **#1-2** thống nhất phiên bản, **#3-6** chọn tham số đúng, **#11-12** sửa lỗi
thật của thư viện. **#7-10** là công cụ để chạy và chẩn đoán.

---

## 9. Code mới

Thư mục `seal_flow/`, có `CMakeLists.txt` riêng, độc lập với `CMakeLists.txt` gốc của
repo (đang hỏng, chưa sửa vì ngoài phạm vi).

| File | Vai trò | Kết quả |
|---|---|---|
| `src/09_end_to_end.cpp` | **Luồng đầy đủ SE → MS-SEAL → giải mã** | 5/5 đạt |
| `src/01_seal_only_euclidean.cpp` | Euclidean n=512 bằng SEAL thuần | 5/5 đạt |
| `src/02_scale_sweep.cpp` | Quét scale, tách nguyên nhân sai số | tìm ra lỗi scale |
| `src/03_ntt_order_check.cpp` | Thử hoán vị đảo bit | loại giả thuyết NTT |
| `src/04_pk_restrict_check.cpp` | Kiểm `pk` cắt special prime | `pk\|₃` hợp lệ |
| `src/05_domain_check.cpp` | Miền NTT vs miền hệ số | NTT đúng |
| `src/06_pkfile_check.cpp` | So bộ file pk từng prime với bản SEAL | lệch 0/4096 |
| `src/07_pte_compare.cpp` | So bản mã hóa thiết bị vs SEAL | lệch 12/16384 |
| `src/08_sign_check.cpp` | Thử 4 tổ hợp quy ước dấu | loại giả thuyết dấu |

Bài 03–08 là các bước loại trừ. Giữ lại vì chúng là bằng chứng, và vì harness đọc file
thiết bị dùng lại được cho các thử nghiệm sau.

Một chi tiết đáng tin: bài `03_ntt_order_check.cpp` biến thể A tái hiện **chính xác
từng chữ số** kết quả của adapter. Điều đó chứng minh harness độc lập này trung thực,
nên mọi kết luận rút từ nó có giá trị ngang với chạy qua adapter.

---

## 10. Trạng thái và việc còn lại

**Trạng thái repo:**

- Đang ở bộ tham số **27-bit, scale 2^25** — cấu hình đã chứng minh chạy đúng.
- `CMakeLists.txt` gốc của repo vẫn hỏng (4 dòng trỏ sai layout cũ: 7, 11, 45, 56).
  `seal_flow/` không phụ thuộc vào nó.
- Mã nguồn đã tách thành repo riêng, không kèm thư viện Microsoft (mục 12.6).

**Giới hạn của demo hiện tại:**

- Hai vector đầu vào là vector test cố định của thiết bị (`{1,1,...}`, `{2,2,...}`),
  không phải đặc trưng vân tay thật.
- Mọi thứ chạy trên **một máy**. Chưa truyền qua mạng, chưa tách vai thiết bị/server.
- Hiệu năng đã đo ở mục 12.2.

**Việc còn lại:**

1. Nạp vector đặc trưng thật — cần sửa `device/test/api_tests.c` để mã hóa dữ liệu
   truyền vào thay cho `set_encode_encrypt_test`.
2. ~~Đo hiệu năng~~ — đã làm, mục 12.2.
3. Cân nhắc thêm `-fno-strict-aliasing` vào `device/CMakeLists.txt` — có thể còn chỗ
   vi phạm aliasing khác trong thư viện mà ta chưa gặp.
4. Báo lỗi UB lên upstream SEAL-Embedded.

---

## 11. Phase 2 — chạy với mẫu vân tay thật

### 11.1 Dữ liệu tìm được trong repo

| Đường dẫn | Nội dung |
|---|---|
| `demo/client/fingerprint_templates/enroll_1..11.bin` | 11 mẫu, mỗi file **512 byte** |
| `demo/client/entries_real/enroll_1..11.bin` | bản sao giống hệt (`cmp` xác nhận) |
| `demo/client/fingerprint.bin` | 1 mẫu đơn, 512 byte |

**Định dạng: 512 byte = 512 giá trị `uint8` (0–255), mỗi byte một chiều.** Khớp chính
xác `n = 512` của thiết kế, không cần cắt hay đệm.

### 11.2 Cách tiếp cận: ứng dụng riêng, không sửa file test

Ở mục 7, luồng đầy đủ dùng vector test cố định của thư viện. Sang dữ liệu thật, thay
vì sửa `device/test/api_tests.c`, ta **liên kết thẳng `libseal_embedded.a` vào một ứng
dụng riêng** — đúng cách một thiết bị IoT thật dùng thư viện:

```c
SE_PARMS *se_parms = se_setup_default(SE_ASYM_ENCR);
...
bool ret = se_encrypt(&write_ciphertext, v, vlen * sizeof(flpt), false, se_parms);
```

`write_ciphertext` đóng vai hàm gửi mạng, ghi ra file text thay vì gửi đi thật.

Code: `src/10_fingerprint_encrypt.c` (thiết bị), `src/11_fingerprint_match.cpp` (server).

### 11.3 Chuẩn hóa — và vì sao cần

Giá trị thô tới 255, nên tổng Euclidean tối đa là `512 × 255² = 3.3e7 ≈ 2^25`. Với
scale `2^23` sau rescale, bản rõ chạm `2^48`, trong khi modulus còn lại ở level 1 chỉ
`2^27 × 2^27 = 2^54`. Dư 6 bit — quá sát trần, độ chính xác sẽ suy giảm.

Chuẩn hóa về `[0,1]` bằng cách chia 255 đưa tổng tối đa về `512 = 2^9`, đúng tầm đã
kiểm chứng ở mục 7. Cả hai phía dùng cùng phép chuẩn hóa.

### 11.4 Kết quả

Truy vấn là `enroll_1.bin`, mã hóa **độc lập** (nhiễu ngẫu nhiên khác với bản trong
CSDL), so với cả 11 mẫu:

```
mau         tinh chay       tren ban ma     sai so        ket qua
----------------------------------------------------------------------
enroll_1    0.0000          0.0129          1.29e-02      KHOP
enroll_2    28.0783         28.1033         2.50e-02      khong
enroll_3    18.5690         18.5913         2.23e-02      khong
enroll_4    18.1335         18.1442         1.07e-02      khong
enroll_5    23.2519         23.2726         2.07e-02      khong
enroll_6    17.3619         17.3794         1.75e-02      khong
enroll_7    19.8846         19.8969         1.23e-02      khong
enroll_8    19.5496         19.5709         2.13e-02      khong
enroll_9    20.5049         20.5270         2.21e-02      khong
enroll_10   21.0113         21.0284         1.72e-02      khong
enroll_11   39.8205         39.8218         1.26e-03      khong
```

Khoảng cách đúng người **0.0129**, gần nhất trong nhóm khác **17.38** — **cách nhau
1345 lần**. Biên phân tách rất rộng.

Sai số tuyệt đối so với tính chay nằm trong khoảng `1.3e-03` đến `2.5e-02` trên mọi
mẫu, không phụ thuộc độ lớn khoảng cách — đúng đặc trưng của sàn nhiễu cộng tính.

Kiểm thêm bốn truy vấn khác nhau:

| Truy vấn | Khớp tốt nhất | Khoảng cách | Kết quả |
|---|---|---|---|
| enroll_1 | enroll_1 | 0.0129 | Đúng |
| enroll_5 | enroll_5 | 0.0894 | Đúng |
| enroll_8 | enroll_8 | 0.0326 | Đúng |
| enroll_11 | enroll_11 | 0.0275 | Đúng |

**4/4 nhận diện đúng.**

Toàn bộ phép trừ, bình phương, relinearize, rescale và rotation-sum chạy trên bản mã.
Server không lúc nào thấy dữ liệu thô.

### 11.5 Giới hạn — cần nói rõ khi báo cáo

**Ngưỡng chưa hiệu chỉnh.** Ngưỡng `1.0` trong code chỉ là giá trị đặt tạm cho demo,
không có căn cứ thống kê. Muốn đặt ngưỡng đúng phải đo phân bố khoảng cách **cùng
người** và **khác người**, rồi chọn điểm cân bằng FAR/FRR theo yêu cầu ứng dụng.

**Bộ dữ liệu không đủ để làm việc đó.** 11 mẫu, mỗi người **một mẫu duy nhất**. Không
có cặp cùng-người-khác-lần-chụp, nên không đo được phân bố khoảng cách cùng người.
Trường hợp "đúng người" ở trên là mã hóa lại **cùng một file**, tức khoảng cách thật
bằng 0 — dễ hơn thực tế rất nhiều, nơi hai lần quét cùng ngón vẫn lệch nhau.

Nói cách khác: kết quả trên chứng minh **đường ống mã hóa và tính toán chạy đúng**,
chưa chứng minh **hệ thống nhận diện hoạt động tốt trên dữ liệu thực tế**. Hai việc
khác nhau.

**Chưa đo hiệu năng.** Thời gian mã hóa, thời gian so khớp một cặp, thời gian quét cả
CSDL — đo ở mục 12.2.

**Bộ dữ liệu quá nhỏ.** Giải quyết ở mục 12 bằng FVC2004 DB3_B: 80 ảnh, 10 ngón, mỗi
ngón 8 lần quét — có cặp cùng-ngón-khác-lần-chụp, đúng thứ mục này nói là thiếu.

---

## 12. Phase 3 — đo hiệu năng và kiểm chứng trên dữ liệu chuẩn

Mục 11 kết thúc với hai thiếu sót đã nêu rõ: bộ dữ liệu không có cặp cùng-ngón-khác-
lần-chụp, và chưa đo hiệu năng. Mục này xử lý cả hai.

### 12.1 Dữ liệu: FVC2004 DB3_B

| | |
|---|---|
| Nguồn | FVC2004, cơ sở dữ liệu DB3_B |
| Quy mô | 80 ảnh — 10 ngón × 8 lần quét mỗi ngón |
| Số cặp so khớp | C(80,2) = 3.160 |

Bộ này được chọn sau khi tải về toàn bộ 12 bộ ảnh công khai của FVC2000, FVC2002 và
FVC2004 — 960 ảnh thuộc 120 ngón — rồi đo tỉ lệ nhận đúng hạng 1 của bộ trích đặc
trưng trên từng bộ bằng `tools/rank_survey.py`:

| Bộ ảnh | Leave-one-out | Một bản mẫu mỗi ngón |
|---|---:|---:|
| FVC2000 DB4_B *(ảnh tổng hợp)* | 97,5 % | 77,1 % |
| **FVC2004 DB3_B** | **90,0 %** | **71,4 %** |
| FVC2000 DB1_B, DB3_B | 81,2 % | 54–63 % |
| FVC2002 DB1_B *(bộ dùng trước đây)* | 70,0 % | 41,4 % |

FVC2000 DB4_B cao hơn nhưng là ảnh sinh bằng máy, không phải vân tay người thật, nên
chọn FVC2004 DB3_B — bộ tốt nhất trong nhóm dùng cảm biến thật.

Khác bộ 11 mẫu ở mục 11, tập này có **nhiều lần quét của cùng một ngón**, nên đo được
phân bố khoảng cách cùng-ngón và khác-ngón — điều mục 11.5 chỉ ra là không làm được.

Trích đặc trưng theo phương pháp FingerCode: ngân hàng lọc Gabor 8 hướng × lưới 8×8 ô
= 512 chiều (`tools/extract_features.py`). Vector được chuẩn hóa L2 rồi nhân hệ số
`K = 32`.

Lý do nhân hệ số: nhiễu CKKS là **tuyệt đối**, không phải tương đối — sàn nhiễu gần như
cố định ở mức 0,065. Vector đơn vị cho khoảng cách chỉ 0,3–0,5 nên nhiễu chiếm tới 17%.
Nhân cả hai vector cùng một hệ số `K` thì khoảng cách tăng `K²` trong khi nhiễu đứng
yên, đưa sai số tương đối về mức 0,01%. Nhân cùng một hằng số không đổi thứ tự xếp
hạng, nên tương đương về mặt so khớp.

### 12.2 Hiệu năng

Đo bằng `src/15_bench_pipeline.cpp` — nối cả hai đầu trong **một tiến trình**, nên tổng
thời gian là số đo thật chứ không phải cộng các số rời. 30 lần lặp:

| Chặng | Trung bình | Độ lệch chuẩn | Tỉ trọng |
|---|---:|---:|---:|
| Mã hoá phía thiết bị | 3,145 ms | 0,060 | 11,9 % |
| Truyền và nạp bản mã | 0,130 ms | 0,007 | 0,5 % |
| Tính trên bản mã | 22,514 ms | 0,221 | 84,9 % |
| Giải mã kết quả | 0,719 ms | 0,018 | 2,7 % |
| **Tổng một truy vấn** | **26,510 ms** | **0,260** | |

Chia nhỏ phần máy chủ (`src/12_benchmark.cpp`):

| Phép toán | Thời gian |
|---|---:|
| Trừ hai vector | 0,129 ms |
| Bình phương | 0,552 ms |
| Relinearize | 3,186 ms |
| Rescale | 0,832 ms |
| Cộng dồn 512 chiều, 9 vòng xoay | 17,882 ms |

Bước cộng dồn chiếm **79%** thời gian máy chủ. Đây là hướng tối ưu rõ nhất nếu cần
tăng tốc, và không ảnh hưởng độ chính xác.

Kích thước dữ liệu: vân tay gốc 0,5 KB, ciphertext 96 KB — hệ số phình **192×**. Khoá
đánh giá truyền một lần lúc thiết lập: 0,75 MB relin + 6,78 MB galois.

### 12.3 Độ trung thực trên 3.160 cặp

`src/14_fidelity.cpp` duyệt toàn bộ cặp, mỗi cặp so khoảng cách tính trên bản mã với
khoảng cách tính trên dữ liệu gốc. Thời gian chạy 73,3 giây, trung bình 23,2 ms mỗi cặp.

| Chỉ số | Giá trị |
|---|---:|
| Sai số tuyệt đối trung bình | 0,0335 |
| Sai số tuyệt đối lớn nhất | 0,0960 |
| Sai số tương đối trung bình | 0,0091 % |
| Sai số tương đối lớn nhất | 0,231 % |
| Truy vấn cho kết quả gần nhất trùng với tính trên dữ liệu gốc | 80/80 |
| Quyết định khớp/không-khớp không đổi, quét 211 ngưỡng | 99,91 % |

Câu hỏi không phải "lệch bao nhiêu" mà **lệch đó có đủ làm đổi quyết định không**.
Trên cả 80 truy vấn, bản ghi gần nhất tính trên bản mã trùng với bản ghi gần nhất tính
trên dữ liệu gốc.

### 12.4 Thứ tự xếp hạng — cách đo quyết định con số

Phép đo sẵn có trong `14_fidelity` lấy mẫu thưa, chỉ 561 phép so trên 3.160 cặp, và
cho ra "100% giữ đúng thứ tự". Con số tròn trịa đó là sản phẩm của cách lấy mẫu chứ
không phải của hệ thống.

Đo lại đầy đủ theo từng truy vấn: với mỗi ảnh, xếp 79 ảnh còn lại theo khoảng cách
rồi đếm số cặp bị đảo chiều giữa hai cách tính.

| Chỉ số | Giá trị |
|---|---:|
| Cặp thứ tự đã xét | 246.480 |
| Cặp bị đảo thứ tự | 19 |
| Tỉ lệ giữ đúng thứ tự | **99,9923 %** |
| Cách biệt lớn nhất giữa hai bản ghi bị đảo | 0,028 |
| Sai số tuyệt đối lớn nhất do mã hoá | 0,096 |

Cả 19 cặp bị đảo đều cách nhau **dưới 0,028**, nhỏ hơn hẳn sai số tuyệt đối lớn nhất
do mã hoá là 0,096. Nói cách khác, thứ tự chỉ đổi khi hai bản ghi gần nhau tới mức
chính sàn nhiễu không phân biệt nổi. Bản ghi gần nhất không đổi ở truy vấn nào.

Ghi lại cách đo thay vì chỉ ghi kết quả, vì chênh lệch giữa hai phép đo lớn hơn chênh
lệch giữa hai bộ dữ liệu: lấy mẫu thưa che mất hiện tượng.

### 12.5 Giới hạn của bộ trích đặc trưng

Tỉ lệ nhận đúng ngón ở hạng 1 theo giao thức leave-one-out: **72/80 = 90,0%**. Theo mô
hình vận hành thật — mỗi ngón một bản mẫu đăng ký, các lần quét sau đem so với bản đó —
là **50/70 = 71,4%**. Hai con số đo hai thứ khác nhau, nên luôn nói rõ giao thức nào.

Con số này **không phải** chỉ số của lớp mã hoá. Nó giống hệt nhau khi tính trên dữ
liệu gốc và khi tính trên bản mã — nghĩa là do bộ trích đặc trưng, không do mã hoá.
Nguyên nhân: `extract_features.py` không dò điểm lõi và khử xoay chỉ ở mức thô, nên hai
lần quét cùng ngón bị xoay nhiều sẽ cho vector khác nhau đáng kể.

Trong triển khai thực tế, bộ trích đặc trưng là thành phần sẵn có của hệ thống tiếp
nhận. Kết quả mục 12.3 chứng minh lớp mã hoá không làm suy giảm bộ trích đó, bất kể
đó là bộ nào.

### 12.6 Chương trình và công cụ bổ sung

| Tệp | Chức năng |
|---|---|
| `src/12_benchmark.cpp` | Đo từng phép toán đồng cấu phía máy chủ |
| `src/13_bench_device.c` | Đo thời gian mã hoá phía gửi |
| `src/14_fidelity.cpp` | Kiểm chứng độ trung thực trên 3.160 cặp |
| `src/17_workflow.cpp` | Chạy trọn một lượt xác thực qua bốn chặng |
| `src/15_bench_pipeline.cpp` | Đo tổng thời gian toàn luồng trong một tiến trình |
| `src/15_device_shim.c` | Lớp vỏ C cho thư viện mã hoá phía gửi |
| `src/16_match_report.cpp` | Sinh bảng kết quả một lượt nhận dạng, xuất CSV |
| `tools/extract_features.py` | Trích vector đặc trưng 512 chiều từ ảnh |
| `tools/make_summary.py` | Tổng hợp các CSV đo đạc thành một bảng |
| `tools/make_dashboard.py` | Dựng trang báo cáo HTML từ CSV |
| `tools/make_terminal_shot.py` | Thực thi chương trình, thu kết quả, kết xuất thành ảnh |

`15_device_shim.c` tồn tại vì một lý do kỹ thuật: header của thư viện mã hoá phía gửi
dùng cú pháp chỉ hợp lệ trong C — trường tên `complex`, gán `void*` sang `uint8_t*`
không ép kiểu — nên không biên dịch được bằng trình biên dịch C++. Ngoài ra cả hai thư
viện đều định nghĩa một kiểu tên `Modulus`, phải ghi đầy đủ `seal::Modulus` để tránh
nhập nhằng.

### 12.7 Tái tạo

```bash
bash setup.sh
cd device && ../build/15_bench_pipeline 30   # mục 12.2
cd device && ../build/16_match_report 101_1 79
./build/14_fidelity                           # mục 12.3
python3 tools/make_summary.py                 # gộp số liệu
python3 tools/make_dashboard.py               # dựng trang báo cáo
```

Số liệu thô nằm ở `bench/*.csv`.
