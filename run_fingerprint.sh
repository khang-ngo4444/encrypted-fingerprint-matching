#!/usr/bin/env bash
# Phase 2: mã hóa mẫu vân tay trên "thiết bị" rồi so khớp trên bản mã.
#
# Chạy từ gốc repo:  bash run_fingerprint.sh [tên_mẫu_truy_vấn]
# Ví dụ:             bash run_fingerprint.sh enroll_5

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

QUERY="${1:-enroll_1}"
FP_DIR="demo/client/fingerprint_templates"
CT_DIR="ct"
NDB=11
THRESHOLD=1.0

for f in build/10_fingerprint_encrypt build/11_fingerprint_match; do
    [ -x "$f" ] || { echo "Thiếu $f — chạy 'bash setup.sh' trước."; exit 1; }
done

mkdir -p "$CT_DIR"

# Thiết bị mã hóa. Phải chạy từ device/ vì SE_DATA_PATH là đường dẫn tương đối.
echo "==> Thiết bị mã hóa $NDB mẫu trong CSDL"
( cd device
  for i in $(seq 1 $NDB); do
      "$ROOT/build/10_fingerprint_encrypt" \
          "$ROOT/$FP_DIR/enroll_$i.bin" "$ROOT/$CT_DIR/enroll_$i.txt" >/dev/null 2>&1
      printf "%s " "$i"
  done
  echo ""

  echo "==> Thiết bị mã hóa truy vấn ($QUERY)"
  "$ROOT/build/10_fingerprint_encrypt" \
      "$ROOT/$FP_DIR/$QUERY.bin" "$ROOT/$CT_DIR/query.txt" >/dev/null 2>&1
)

echo ""
echo "==> Server so khớp trên bản mã"
./build/11_fingerprint_match query "$NDB" "$THRESHOLD" "$QUERY"
