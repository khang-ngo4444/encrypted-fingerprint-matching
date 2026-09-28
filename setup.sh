#!/usr/bin/env bash
# Dựng lại toàn bộ môi trường từ số không.
#
# Repo này KHÔNG chứa mã nguồn của Microsoft SEAL hay SEAL-Embedded. Script tải
# hai thư viện từ upstream rồi áp các sửa đổi cần thiết bằng lệnh sed — mô tả
# phép sửa, không sao chép mã nguồn.
#
# Sửa đổi quan trọng nhất là bản vá lỗi undefined behavior ở bước [4]; thiếu nó
# thì toàn bộ luồng chạy ra nhiễu (xem doc/REPORT.md mục 5).
#
# Chạy từ gốc repo:  bash setup.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SEAL_TAG="v4.4.4"
SE_COMMIT="0913fa9"   # SEAL-Embedded 1.1.0
JOBS="${JOBS:-4}"

say() { printf "\n\033[1m==> %s\033[0m\n" "$1"; }

# Sửa một chuỗi trong file, báo lỗi nếu không tìm thấy (tránh sửa hụt âm thầm)
subst() {
    local file="$1" from="$2" to="$3"
    grep -qF -- "$from" "$file" || { echo "LỖI: không thấy trong $file: $from"; exit 1; }
    python3 - "$file" "$from" "$to" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
p.write_text(s.replace(sys.argv[2], sys.argv[3], 1))
PY
    printf "    %s\n" "$(basename "$file"): $from  ->  $to"
}

# ------------------------------------------------------------ 1. Microsoft SEAL
if [ ! -d SEAL ]; then
    say "[1] Clone Microsoft SEAL $SEAL_TAG"
    git clone --quiet --branch "$SEAL_TAG" --depth 1 https://github.com/microsoft/SEAL.git SEAL
fi
if [ ! -f SEAL/build/lib/libseal-4.4.a ]; then
    say "[2] Build Microsoft SEAL (khoảng 10 phút trên Pi 4)"
    cmake -S SEAL -B SEAL/build -DCMAKE_BUILD_TYPE=Release -DSEAL_BUILD_DEPS=ON
    cmake --build SEAL/build -j"$JOBS"
fi

# --------------------------------------------------- 2. SEAL-Embedded + sửa đổi
if [ ! -d device ] || [ ! -d adapter ]; then
    say "[3] Clone SEAL-Embedded $SE_COMMIT"
    tmp=$(mktemp -d)
    git clone --quiet https://github.com/microsoft/SEAL-Embedded.git "$tmp/se"
    git -C "$tmp/se" checkout --quiet "$SE_COMMIT"
    cp -a "$tmp/se/device" "$tmp/se/adapter" .
    rm -rf "$tmp"

    say "[4] Sửa lỗi undefined behavior (BẮT BUỘC — xem doc/REPORT.md mục 5)"
    # Đọc uint64_t qua con trỏ uint32_t là vi phạm strict aliasing. Với -O3 trên
    # nền 64-bit, phép quy giản Barrett trả về 0 cho mọi đầu vào.
    subst device/lib/ckks_common.c \
        'ZZ *coeff_abs_vec = (ZZ *)&coeff_abs;' \
        'ZZ coeff_abs_vec[2]; memcpy(coeff_abs_vec, &coeff_abs, sizeof(coeff_abs));'
    subst device/lib/ckks_common.c \
        '#include "ckks_common.h"' \
        '#include <string.h>
#include "ckks_common.h"'

    say "[5] Đổi bộ tham số sang {27,27,27,28} — special prime phải lớn hơn working prime"
    subst device/lib/user_defines.h '// #define SE_DEFAULT_4K_27BIT'    '#define SE_DEFAULT_4K_27BIT'
    subst adapter/utils.h           '// #define SEALE_DEFAULT_4K_27BIT' '#define SEALE_DEFAULT_4K_27BIT'

    say "[6] Nâng scale 2^20 -> 2^25 (cả hai phía, nhánh 27-bit)"
    subst device/lib/parameters.c \
        'set_parms_ckks_27bit_helper(parms);
            parms->scale = pow(2, 20);' \
        'set_parms_ckks_27bit_helper(parms);
            parms->scale = pow(2, 25);'
    subst adapter/adapter.cpp \
        'cout << "27, 27, 27, 28}, scale = pow(2, 20)" << endl;
            scale = pow(2, 20);' \
        'cout << "27, 27, 27, 28}, scale = pow(2, 25)" << endl;
            scale = pow(2, 25);'

    say "[7] Thống nhất phiên bản SEAL cho adapter: 3.7.2 -> 4.4.4"
    subst adapter/CMakeLists.txt \
        'GIT_TAG        79234726053c45eede688400aa219fdec0810bd8 # 3.7.2' \
        'GIT_TAG        96ae20db6649bc7c24e9a34994bedd70f4951f60 # 4.4.4'
    subst adapter/CMakeLists.txt 'find_package(SEAL 3.7 QUIET REQUIRED)' \
                                 'find_package(SEAL 4.4 QUIET REQUIRED)'

    say "[8] Chuyển adapter sang chế độ bất đối xứng"
    subst adapter/adapter.cpp 'bool is_sym = true;' 'bool is_sym = false;'

    say "[9] Bộ test thiết bị: chỉ chạy test_ckks_api_asym"
    # Output của binary này được hứng vào file ciphertext cho bộ kiểm thử.
    # Chạy cả bộ test thì file lẫn output của fft/ntt/modulo, parser đọc sai.
    python3 - <<'PY'
import pathlib, re
p = pathlib.Path("device/test/main.c"); s = p.read_text()
# Comment mọi lời gọi test_ đang bật, trừ test_ckks_api_asym
s = re.sub(r'^(    )(test_(?!ckks_api_asym)\w+\()', r'\1// \2', s, flags=re.M)
# Bật test_ckks_api_asym
s = s.replace('// test_ckks_api_asym();', 'test_ckks_api_asym();')
p.write_text(s)
PY
    n=$(grep -cE '^    test_[a-z]' device/test/main.c)
    [ "$n" -eq 1 ] || { echo "LỖI: còn $n bài test đang bật, cần đúng 1"; exit 1; }
    echo "    đang bật: $(grep -E '^    test_[a-z]' device/test/main.c | tr -d ' ')"
fi

# ------------------------------------------------------- 3. Adapter + sinh khóa
if [ ! -f adapter/build-seal44/bin/se_adapter ]; then
    say "[9] Build SE-Adapter (tự tải Microsoft SEAL 4.4.4 riêng)"
    cmake -S adapter -B adapter/build-seal44 -DCMAKE_BUILD_TYPE=Release
    cmake --build adapter/build-seal44 -j"$JOBS"
fi
if [ ! -f device/adapter_output_data/sk_4096_seal.dat ]; then
    say "[10] Sinh khóa và bảng NTT"
    mkdir -p device/adapter_output_data
    ( cd adapter && printf '1\n0\n' | ./build-seal44/bin/se_adapter 4096 >/dev/null )
    echo "    đã sinh $(ls device/adapter_output_data | wc -l) file"
fi

# ----------------------------------------------------------- 4. Thư viện thiết bị
if [ ! -f device/build/bin/libseal_embedded.a ]; then
    say "[11] Build thư viện thiết bị"
    cmake -S device -B device/build -DCMAKE_BUILD_TYPE=Release -DSE_BUILD_LOCAL=ON
    cmake --build device/build -j"$JOBS"
fi

# ------------------------------------------------------------------ 5. Build
say "[12] Build chương trình"
cmake -S . -B build
cmake --build build -j"$JOBS"

say "Xong. Chạy thử:"
cat <<'EOF'
    cd device && ../build/16_match_report 101_1 79   # bảng kết quả so khớp
    cd device && ../build/15_bench_pipeline 30        # thời gian từng chặng
    ./build/14_fidelity                               # kiểm chứng 3.160 cặp
EOF
