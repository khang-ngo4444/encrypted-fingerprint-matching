#!/usr/bin/env bash
# Chạy workflow đầy đủ một lượt xác thực.
#   bash demo.sh [tên_truy_vấn] [số_bản_ghi]

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HERE/build/17_workflow"
[ -x "$BIN" ] || { echo "Thiếu $BIN — chạy 'bash setup.sh' trước."; exit 1; }

# Thư mục device nằm cạnh script (repo nguồn) hoặc ở cấp trên (cây làm việc).
for d in "$HERE/device" "$HERE/../device"; do
    [ -d "$d/adapter_output_data" ] && DEVICE="$d" && break
done
[ -n "${DEVICE:-}" ] || { echo "Không thấy thư mục device/"; exit 1; }

for d in "$HERE/data" "$HERE/../datasets/fvc_all/bin"; do
    [ -d "$d" ] && BIN_DIR="$d" && break
done

cd "$DEVICE"
CME_CT_DIR="${CME_CT_DIR:-$HERE/ct_demo}" \
CME_BIN_DIR="${CME_BIN_DIR:-${BIN_DIR:-$HERE/data}}" \
CME_CSV_OUT="${CME_CSV_OUT:-$HERE/bench/workflow.csv}" \
    "$BIN" "${1:-04d3-103_5}" "${2:-10}"
