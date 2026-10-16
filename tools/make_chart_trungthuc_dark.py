#!/usr/bin/env python3
"""Biểu đồ độ trung thực, nền tối khớp màu slide Canva.

Mỗi điểm là một cặp vân tay. Trục hoành: khoảng cách tính trên dữ liệu gốc.
Trục tung: cùng khoảng cách đó nhưng tính hoàn toàn trên bản mã. Nằm trên
đường chéo nghĩa là mã hoá không làm lệch kết quả.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Nền phải trùng đúng màu nền slide, nếu lệch sẽ thành một ô chữ nhật đậm hơn
BG, FG, ACC, MUT = "#0f1c2e", "#f4f8fb", "#22d3ee", "#9fb2c6"
ALT = "#f59e0b"  # cam, cho cặp cùng ngón

plt.rcParams["font.family"] = "DejaVu Sans"

src = sys.argv[1] if len(sys.argv) > 1 else "seal_flow/bench/fidelity.csv"
out = sys.argv[2] if len(sys.argv) > 2 else "seal_flow/bench/charts/06_do_trung_thuc_dark.png"
os.makedirs(os.path.dirname(out), exist_ok=True)

rows = list(csv.DictReader(open(src)))
plain = np.array([float(r["ban_ro"]) for r in rows])
fhe = np.array([float(r["ban_ma"]) for r in rows])
gen = np.array([r["cung_ngon"] == "1" for r in rows])

fig, ax = plt.subplots(figsize=(7.4, 7.0))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

lim = [min(plain.min(), fhe.min()) * 0.97, max(plain.max(), fhe.max()) * 1.03]
ax.plot(lim, lim, "--", color=MUT, lw=1.6, zorder=1, label="trùng khớp tuyệt đối")
ax.scatter(plain[~gen], fhe[~gen], s=12, alpha=0.45, color=ACC, zorder=2,
           label=f"cặp khác ngón ({(~gen).sum()})")
ax.scatter(plain[gen], fhe[gen], s=20, alpha=0.9, color=ALT, zorder=3,
           label=f"cặp cùng ngón ({gen.sum()})")

ax.set_xlim(lim)
ax.set_ylim(lim)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("bottom", "left"):
    ax.spines[s].set_color("#28415e")
ax.tick_params(colors=MUT, labelsize=12)
ax.grid(True, alpha=0.15, color=MUT)
ax.set_xlabel("Khoảng cách tính trên dữ liệu gốc", color=FG, fontsize=15, labelpad=10)
ax.set_ylabel("Khoảng cách tính trên bản mã", color=FG, fontsize=15, labelpad=10)
ax.legend(fontsize=12, facecolor=BG, edgecolor="#28415e", labelcolor=FG, loc="upper left")

fig.tight_layout()
fig.savefig(out, facecolor=BG, dpi=170, bbox_inches="tight")
print(out)
