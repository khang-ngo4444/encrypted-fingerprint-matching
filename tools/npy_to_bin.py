#!/usr/bin/env python3
"""Chuyển vector .npy sang .bin thô (512 double little-endian, không phần đầu tệp).

    python npy_to_bin.py <thư_mục_npy> <thư_mục_bin>
"""

import os
import sys

import numpy as np

FEATURE_DIM = 512


def main():
    if len(sys.argv) < 3:
        sys.exit(f"Dùng: {sys.argv[0]} <thư_mục_npy> <thư_mục_bin>")
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)

    files = sorted(f for f in os.listdir(src) if f.endswith(".npy"))
    if not files:
        sys.exit(f"Không thấy .npy trong {src}")

    for n, fn in enumerate(files, 1):
        v = np.load(os.path.join(src, fn)).astype(np.float64)
        if v.shape != (FEATURE_DIM,):
            sys.exit(f"{fn}: kích thước {v.shape}, cần ({FEATURE_DIM},)")
        v.tofile(os.path.join(dst, fn[:-4] + ".bin"))
        if n % 100 == 0 or n == len(files):
            print(f"  {n}/{len(files)}", flush=True)

    print(f"Xong. {len(files)} tệp .bin nằm ở {dst}")


if __name__ == "__main__":
    main()
