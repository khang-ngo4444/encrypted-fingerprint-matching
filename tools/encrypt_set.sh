#!/usr/bin/env bash
# Mã hóa một tập vector vân tay bằng thư viện thiết bị.
#   bash tools/encrypt_set.sh <thư_mục_bin> <thư_mục_ct_ra> [mẫu_lọc]

set -euo pipefail

ROOT="${CME_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
BIN_DIR="${1:?Thiếu thư_mục_bin}"
CT_DIR="${2:?Thiếu thư_mục_ct_ra}"
PATTERN="${3:-*}"

ENC="$ROOT/seal_flow/build/10_fingerprint_encrypt"
[ -x "$ENC" ] || { echo "Thiếu $ENC — chạy 'bash seal_flow/setup.sh' trước."; exit 1; }

mkdir -p "$CT_DIR"
# Phải chạy từ device/ vì SE_DATA_PATH là đường dẫn tương đối.
cd "$ROOT/device"

total=0
for f in "$BIN_DIR"/$PATTERN; do
    [ -e "$f" ] || continue
    base="$(basename "$f" .bin)"
    out="$CT_DIR/$base.txt"
    [ -s "$out" ] && continue
    "$ENC" "$f" "$out" >/dev/null 2>&1
    total=$((total + 1))
    [ $((total % 20)) -eq 0 ] && printf '  %d\n' "$total"
done

echo "Xong. $total mẫu mới được mã hóa vào $CT_DIR"
echo "Tổng số tệp ciphertext: $(find "$CT_DIR" -name '*.txt' | wc -l)"
