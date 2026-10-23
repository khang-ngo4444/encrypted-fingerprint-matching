#!/usr/bin/env python3
"""Tỉ lệ nhận đúng hạng 1 trên dữ liệu gốc, theo từng bộ ảnh.

Đo năng lực của bộ trích đặc trưng, không liên quan tới lớp mã hoá.
Tên tệp: <bộ>-<ngón>_<lần quét>.npy. Bản đăng ký là lần quét _1.

    python rank_survey.py <thư_mục_npy>
"""

import os
import sys
from collections import defaultdict

import numpy as np


def load(src):
    out = {}
    for fn in sorted(os.listdir(src)):
        if fn.endswith(".npy"):
            out[fn[:-4]] = np.load(os.path.join(src, fn)).astype(np.float64)
    return out


def identity(name):
    return name[: name.rfind("_")]


def impression(name):
    return name[name.rfind("_") + 1 :]


def subset(name):
    return name.split("-")[0] if "-" in name else "all"


def rank1(vecs, names):
    gallery = [n for n in names if impression(n) == "1"]
    queries = [n for n in names if impression(n) != "1"]
    if not gallery or not queries:
        return 0, 0

    G = np.stack([vecs[n] for n in gallery])
    gid = [identity(n) for n in gallery]
    hit = 0
    for q in queries:
        d = ((G - vecs[q]) ** 2).sum(axis=1)
        if gid[int(np.argmin(d))] == identity(q):
            hit += 1
    return hit, len(queries)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "."
    vecs = load(src)
    if not vecs:
        sys.exit(f"Không thấy .npy trong {src}")

    groups = defaultdict(list)
    for n in vecs:
        groups[subset(n)].append(n)

    print(f"{len(vecs)} vector · {len(set(identity(n) for n in vecs))} ngón riêng biệt\n")
    print(f"{'BỘ ẢNH':<10}{'NGÓN':>7}{'TRUY VẤN':>10}{'ĐÚNG HẠNG 1':>14}{'TỈ LỆ':>9}")
    print("-" * 50)

    for g in sorted(groups):
        names = groups[g]
        hit, tot = rank1(vecs, names)
        nid = len(set(identity(n) for n in names))
        print(f"{g:<10}{nid:>7}{tot:>10}{hit:>14}{hit / tot * 100:>8.1f}%")

    hit, tot = rank1(vecs, list(vecs))
    nid = len(set(identity(n) for n in vecs))
    print("-" * 50)
    print(f"{'GỘP HẾT':<10}{nid:>7}{tot:>10}{hit:>14}{hit / tot * 100:>8.1f}%")
    # Mỗi bộ một loại cảm biến, nên ảnh khác bộ vốn đã dễ phân biệt — dòng gộp
    # không so sánh được với hệ thống dùng chung một cảm biến.


if __name__ == "__main__":
    main()
