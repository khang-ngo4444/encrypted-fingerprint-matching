#!/usr/bin/env python3
"""Biểu đồ quy mô, nền tối khớp màu slide Canva.

Chi phí mỗi bản ghi khi quét CSDL = tính trên bản mã + giải mã. Mã hoá truy vấn
chỉ làm một lần cho cả lượt quét nên không tính vào đây.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BG, FG, ACC, MUT = "#0a1628", "#f4f8fb", "#22d3ee", "#9fb2c6"
BENCH = "seal_flow/bench/pipeline_benchmark.csv"


def per_record_ms(path=BENCH):
    """Đọc số đo thật; nếu không có file thì dùng số đã công bố."""
    if not os.path.exists(path):
        return 23.23
    want = {"server_tinh_toan": None, "giai_ma": None}
    with open(path) as f:
        for r in csv.DictReader(f):
            k = r.get("chang")
            if k in want:
                want[k] = float(r["trung_binh_ms"])
    if None in want.values():
        return 23.23
    return sum(want.values())


PER_MATCH_MS = per_record_ms()

plt.rcParams["font.family"] = "DejaVu Sans"

n = np.array([10, 100, 1_000, 10_000, 100_000])
t1 = n * PER_MATCH_MS / 1000.0
t4 = t1 / 4.0

fig, ax = plt.subplots(figsize=(8.6, 5.6))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

ax.plot(n, t1, "o-", color=MUT, lw=2.5, ms=8, label="1 nhân")
ax.plot(n, t4, "s-", color=ACC, lw=2.5, ms=8, label="4 nhân")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(6, 2.2e5)
ax.set_ylim(0.03, 5e3)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("bottom", "left"):
    ax.spines[s].set_color("#28415e")
ax.tick_params(colors=MUT, labelsize=13)
ax.grid(True, alpha=0.18, color=MUT)
ax.set_xlabel("Số người trong cơ sở dữ liệu", color=FG, fontsize=15, labelpad=10)
ax.set_ylabel("Thời gian quét (giây)", color=FG, fontsize=15, labelpad=10)


def fmt(y):
    if y < 60:
        return f"{y:.1f}".replace(".", ",") + " s"
    return f"{y/60:.0f} phút"


for i, (x, y) in enumerate(zip(n, t4)):
    ha = "right" if i == len(n) - 1 else "center"
    dx = -10 if i == len(n) - 1 else 0
    ax.annotate(fmt(y), (x, y), textcoords="offset points", xytext=(dx, -24),
                ha=ha, fontsize=12.5, color=ACC, fontweight="bold")

ax.legend(fontsize=13, facecolor=BG, edgecolor="#28415e", labelcolor=FG,
          loc="upper left")
fig.tight_layout()
out = sys.argv[1] if len(sys.argv) > 1 else "seal_flow/bench/charts/05_quy_mo_dark.png"
fig.savefig(out, facecolor=BG, dpi=170, bbox_inches="tight")
print(out)
