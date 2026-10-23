#!/usr/bin/env python3
"""Vẽ biểu đồ từ số liệu benchmark, dùng cho slide.

Dùng:  python make_charts.py <thư_mục_bench> <thư_mục_ra>
"""

import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Bảng màu: xanh đậm cho dữ liệu chính, cam cho đối chiếu, xám cho nền
C_MAIN, C_ALT, C_GREY = "#1f4e79", "#e07b39", "#9aa5b1"
plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "figure.dpi": 150,
})


def save(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {os.path.basename(path)}")


def chart_fidelity(rows, out):
    """Biểu đồ chủ lực: bản mã so với bản rõ — phải nằm trên đường chéo."""
    plain = np.array([float(r["ban_ro"]) for r in rows])
    fhe = np.array([float(r["ban_ma"]) for r in rows])
    gen = np.array([r["cung_ngon"] == "1" for r in rows])

    fig, ax = plt.subplots(figsize=(6.5, 6))
    lim = [min(plain.min(), fhe.min()) * 0.97, max(plain.max(), fhe.max()) * 1.03]
    ax.plot(lim, lim, "--", color=C_GREY, lw=1.5, zorder=1, label="trùng khớp tuyệt đối")
    ax.scatter(plain[~gen], fhe[~gen], s=9, alpha=0.45, color=C_MAIN, zorder=2,
               label=f"cặp khác ngón ({(~gen).sum()})")
    ax.scatter(plain[gen], fhe[gen], s=16, alpha=0.8, color=C_ALT, zorder=3,
               label=f"cặp cùng ngón ({gen.sum()})")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Khoảng cách tính trên dữ liệu gốc")
    ax.set_ylabel("Khoảng cách tính trên dữ liệu đã mã hoá")
    ax.set_title(f"Mã hoá không làm lệch kết quả\n{len(rows)} cặp vân tay thật — FVC2004 DB3_B",
                 fontsize=12, pad=12)
    ax.legend(loc="upper left", framealpha=0.95, fontsize=9)
    save(fig, os.path.join(out, "01_do_trung_thuc.png"))


def chart_error(rows, out):
    """Phân bố sai số tương đối."""
    plain = np.array([float(r["ban_ro"]) for r in rows])
    err = np.array([float(r["sai_so_tuyet_doi"]) for r in rows])
    rel = err[plain > 1e-9] / plain[plain > 1e-9] * 100

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(rel, bins=50, color=C_MAIN, alpha=0.85)
    ax.axvline(rel.mean(), color=C_ALT, lw=2,
               label=f"trung bình {rel.mean():.4f}%")
    ax.set_xlabel("Sai số tương đối so với tính trên dữ liệu gốc (%)")
    ax.set_ylabel("Số cặp")
    ax.set_title("Sai số do mã hoá gây ra", fontsize=12, pad=10)
    ax.legend(fontsize=9)
    save(fig, os.path.join(out, "02_sai_so.png"))


def numeric_rows(bench):
    """CSV co phan thu hai voi cot khac, nen phai bo qua dong khong phai so."""
    out = {}
    for r in bench:
        k, v = r.get("hang_muc"), r.get("trung_binh_ms")
        if not k or v is None:
            continue
        try:
            out[k] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def chart_breakdown(bench, out):
    """Thời gian từng bước trong một phép so khớp."""
    want = [("sub", "Trừ hai vector"), ("square", "Bình phương"),
            ("relinearize", "Relinearize"), ("rescale", "Rescale"),
            ("rotation_sum", "Cộng dồn 512 chiều")]
    lut = numeric_rows(bench)
    labels = [lbl for k, lbl in want if k in lut]
    vals = [lut[k] for k, _ in want if k in lut]
    if not vals:
        return
    total = sum(vals)

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    colors = [C_ALT if v == max(vals) else C_MAIN for v in vals]
    bars = ax.barh(labels, vals, color=colors, height=0.6)
    for b, v in zip(bars, vals):
        ax.text(v + total * 0.012, b.get_y() + b.get_height() / 2,
                f"{v:.1f} ms  ({v / total * 100:.0f}%)", va="center", fontsize=9)
    ax.set_xlim(0, total * 1.28)
    ax.set_xlabel("Thời gian (ms)")
    ax.set_title(f"Một phép so khớp = {total:.1f} ms", fontsize=12, pad=10)
    ax.invert_yaxis()
    save(fig, os.path.join(out, "03_phan_ra_thoi_gian.png"))


def chart_scaling(per_match_ms, out):
    """Thời gian quét toàn bộ cơ sở dữ liệu theo quy mô."""
    n = np.array([10, 100, 1_000, 10_000, 100_000])
    t1 = n * per_match_ms / 1000.0
    t4 = t1 / 4.0

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(n, t1, "o-", color=C_MAIN, lw=2, ms=6, label="1 nhân")
    ax.plot(n, t4, "s-", color=C_ALT, lw=2, ms=6, label="4 nhân")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Số người trong cơ sở dữ liệu")
    ax.set_ylabel("Thời gian quét (giây)")
    ax.set_title("Thời gian quét theo quy mô", fontsize=12, pad=10)
    for x, y in zip(n, t4):
        lab = f"{y:.1f}s" if y < 60 else f"{y/60:.0f}ph"
        ax.annotate(lab, (x, y), textcoords="offset points", xytext=(0, -16),
                    ha="center", fontsize=8, color=C_ALT)
    ax.legend(fontsize=9)
    save(fig, os.path.join(out, "04_quy_mo.png"))


def main():
    bdir = sys.argv[1] if len(sys.argv) > 1 else "seal_flow/bench"
    out = sys.argv[2] if len(sys.argv) > 2 else "seal_flow/bench/charts"
    os.makedirs(out, exist_ok=True)

    fid_path = os.path.join(bdir, "fidelity.csv")
    bench_path = os.path.join(bdir, "server_benchmark.csv")

    print("Đang vẽ:")
    rows = list(csv.DictReader(open(fid_path))) if os.path.exists(fid_path) else []
    if rows:
        chart_fidelity(rows, out)
        chart_error(rows, out)

    bench = []
    if os.path.exists(bench_path):
        with open(bench_path) as f:
            bench = [r for r in csv.DictReader(f) if r.get("hang_muc")]
        chart_breakdown(bench, out)
        lut = numeric_rows(bench)
        if "tong_mot_phep_khop" in lut:
            chart_scaling(lut["tong_mot_phep_khop"], out)

    print(f"\nẢnh nằm ở: {out}")


if __name__ == "__main__":
    main()
