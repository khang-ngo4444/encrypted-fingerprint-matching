#!/usr/bin/env python3
"""Gộp mọi số đo rời rạc thành một bảng thống kê duy nhất để nộp.

Đọc các CSV do từng chương trình benchmark sinh ra rồi xuất một bảng dạng dài
(long format): mỗi dòng là một chỉ số, kèm đơn vị và độ lệch chuẩn nếu có. Dạng
này chịu được việc các chỉ số khác đơn vị nhau — ms, KB, %, cặp — mà bảng dạng
rộng không làm được.

    python tools/make_summary.py [thư_mục_bench] [file_ra]

Chỉ dùng thư viện chuẩn, chạy được trên Pi không cần cài gì thêm.
"""

import csv
import math
import os
import sys

BENCH = sys.argv[1] if len(sys.argv) > 1 else "seal_flow/bench"
OUT = sys.argv[2] if len(sys.argv) > 2 else "seal_flow/bench/tong_hop.csv"

rows = []


def add(nhom, hang_muc, gia_tri, don_vi="", sd="", lo="", hi="", ghi_chu=""):
    def fmt(x):
        if x == "" or x is None:
            return ""
        if isinstance(x, float):
            return f"{x:.4f}".rstrip("0").rstrip(".") if abs(x) < 1e6 else f"{x:.0f}"
        return str(x)

    rows.append([nhom, hang_muc, fmt(gia_tri), don_vi, fmt(sd), fmt(lo), fmt(hi), ghi_chu])


def read_csv(name):
    """Đọc CSV, bỏ qua phần phụ lục sau dòng trống."""
    path = os.path.join(BENCH, name)
    if not os.path.exists(path):
        return [], {}
    main, extra = [], {}
    with open(path) as f:
        lines = f.read().split("\n")
    # Phần chính: tới dòng trống đầu tiên
    split = len(lines)
    for i, l in enumerate(lines):
        if i > 0 and not l.strip():
            split = i
            break
    main = list(csv.DictReader(lines[:split]))
    # Phần phụ lục: "#,gia_tri,don_vi"
    tail = [l for l in lines[split:] if l.strip()]
    if tail:
        for r in csv.reader(tail[1:]):
            if len(r) >= 2:
                extra[r[0]] = (r[1], r[2] if len(r) > 2 else "")
    return main, extra


def num(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


# --------------------------------------------------- 1. Tham số hệ thống
add("Tham so", "Luoc do ma hoa", "CKKS", "", ghi_chu="so thuc xap xi, Microsoft SEAL 4.4.4")
add("Tham so", "Bac da thuc (degree)", 4096, "")
add("Tham so", "So prime", 3, "", ghi_chu="27-bit, kem mot special prime 28-bit")
add("Tham so", "Scale", "2^25", "")
add("Tham so", "Muc bao mat", 128, "bit", ghi_chu="theo Homomorphic Encryption Security Standard")
add("Tham so", "So chieu vector dac trung", 512, "chieu", ghi_chu="FingerCode: 8 huong Gabor x luoi 8x8")

# --------------------------------------------------- 2. Pipeline đầu-cuối
pipe, pipe_x = read_csv("pipeline_benchmark.csv")
LABEL_PIPE = {
    "thiet_bi_ma_hoa": "[Thiet bi] Ma hoa truy van",
    "nap_ban_ma": "[Mang] Nap ban ma vao SEAL",
    "server_tinh_toan": "[Server] Tinh tren ban ma",
    "giai_ma": "[Giu khoa] Giai ma ket qua",
    "tong_pipeline": "TONG mot truy van dau-cuoi",
}
for r in pipe:
    k = r.get("chang")
    if k in LABEL_PIPE:
        add("Pipeline", LABEL_PIPE[k], num(r["trung_binh_ms"]), "ms",
            num(r["do_lech_chuan_ms"]), num(r["min_ms"]), num(r["max_ms"]))
if "thiet_lap_thiet_bi" in pipe_x:
    add("Pipeline", "Thiet lap thu vien thiet bi", num(pipe_x["thiet_lap_thiet_bi"][0]), "ms",
        ghi_chu="mot lan duy nhat luc khoi dong")
if "thong_luong_1_nhan" in pipe_x:
    add("Pipeline", "Thong luong", num(pipe_x["thong_luong_1_nhan"][0]), "truy van/giay",
        ghi_chu="do tuan tu, mot luong")

# --------------------------------------------------- 3. Server, từng phép
srv, srv_x = read_csv("server_benchmark.csv")
LABEL_SRV = {
    "sub": "Tru hai vector",
    "square": "Binh phuong",
    "relinearize": "Relinearize",
    "rescale": "Rescale",
    "rotation_sum": "Cong don 512 chieu (9 vong xoay)",
    "tong_mot_phep_khop": "TONG mot phep so khop",
    "giai_ma": "Giai ma",
    "ban_ro_doi_chung": "Doi chung: Euclidean tren ban ro",
    "relin_key_gen": "Sinh relinearization key",
    "galois_key_gen": "Sinh galois key",
}
srv_lut = {}
for r in srv:
    k = r.get("hang_muc")
    v = num(r.get("trung_binh_ms"))
    if k is None or v is None:
        continue
    srv_lut[k] = v
    nhom = "Sinh khoa" if k.endswith("_key_gen") else "Server (chi tiet)"
    add(nhom, LABEL_SRV.get(k, k), v, "ms",
        num(r["do_lech_chuan_ms"]), num(r["min_ms"]), num(r["max_ms"]))

if "rotation_sum" in srv_lut and "tong_mot_phep_khop" in srv_lut:
    pct = srv_lut["rotation_sum"] / srv_lut["tong_mot_phep_khop"] * 100
    add("Server (chi tiet)", "Ti trong buoc cong don", pct, "%",
        ghi_chu="huong toi uu ro nhat neu can tang toc")
if "tong_mot_phep_khop" in srv_lut and "ban_ro_doi_chung" in srv_lut:
    add("Server (chi tiet)", "He so cham hon so voi ban ro",
        srv_lut["tong_mot_phep_khop"] / srv_lut["ban_ro_doi_chung"], "lan")

# --------------------------------------------------- 4. Kích thước dữ liệu
add("Kich thuoc", "Van tay goc", 0.5, "KB", ghi_chu="512 gia tri uint8")
for key, label, unit in (
    ("kich_thuoc_ciphertext", "Ciphertext gui len server", "KB"),
    ("kich_thuoc_relin_key", "Relinearization key", "MB"),
    ("kich_thuoc_galois_key", "Galois key", "MB"),
):
    src = pipe_x.get(key) or srv_x.get(key)
    if src:
        add("Kich thuoc", label, num(src[0]), unit or src[1],
            ghi_chu="truyen mot lan luc thiet lap" if "key" in key else "")
ct = pipe_x.get("kich_thuoc_ciphertext") or srv_x.get("kich_thuoc_ciphertext")
if ct:
    add("Kich thuoc", "He so phinh du lieu", num(ct[0]) / 0.5, "lan")

# --------------------------------------------------- 5. Độ trung thực
fid, _ = read_csv("fidelity.csv")
if fid:
    pairs = []
    for r in fid:
        p, m = num(r.get("ban_ro")), num(r.get("ban_ma"))
        if p is None or m is None:
            continue
        pairs.append((p, m, abs(num(r.get("sai_so_tuyet_doi"), 0.0)), r.get("cung_ngon") == "1"))
    rel = [e / p * 100 for p, _, e, _ in pairs if p > 1e-9]
    gen = sum(1 for *_, g in pairs if g)
    add("Do trung thuc", "Tap du lieu", "FVC2004 DB3_B", "",
        ghi_chu="80 anh van tay that, 10 ngon x 8 lan quet")
    add("Do trung thuc", "So cap da so", len(pairs), "cap")
    add("Do trung thuc", "  trong do cung ngon", gen, "cap")
    add("Do trung thuc", "  trong do khac ngon", len(pairs) - gen, "cap")
    if rel:
        mean = sum(rel) / len(rel)
        sd = math.sqrt(sum((x - mean) ** 2 for x in rel) / (len(rel) - 1)) if len(rel) > 1 else 0
        add("Do trung thuc", "Sai so tuong doi do ma hoa", mean, "%", sd, min(rel), max(rel),
            "ban ma so voi ban ro")
    # Thu tu xep hang: phai xet THEO TUNG TRUY VAN, khong phai gop chung mot ro.
    # Voi moi anh, xep toan bo anh con lai theo khoang cach, roi so hai cach xep.
    # Day moi la thu quyet dinh ket qua nhan dang.
    by_query = {}
    for r in fid:
        a, b = r.get("anh_a"), r.get("anh_b")
        p, m = num(r.get("ban_ro")), num(r.get("ban_ma"))
        if not a or not b or p is None or m is None:
            continue
        by_query.setdefault(a, []).append((b, p, m))
        by_query.setdefault(b, []).append((a, p, m))

    if by_query:
        q_ok = q_total = 0
        rank1_ok = 0
        for q, lst in by_query.items():
            op = [x[0] for x in sorted(lst, key=lambda x: x[1])]
            of = [x[0] for x in sorted(lst, key=lambda x: x[2])]
            q_total += 1
            if op == of:
                q_ok += 1
            if op and of and op[0] == of[0]:
                rank1_ok += 1
        # Dem cap lien ke bi dao, va do xem chung cach nhau bao xa. Neu khoang
        # cach do nho hon sai so ma hoa thi viec dao khong doi quyet dinh nao.
        swap = cmp_total = 0
        gaps = []
        for q, lst in by_query.items():
            op = sorted(lst, key=lambda x: x[1])
            for i in range(len(op) - 1):
                cmp_total += 1
                if op[i][2] > op[i + 1][2]:
                    swap += 1
                    gaps.append(abs(op[i][1] - op[i + 1][1]))
        if cmp_total:
            add("Do trung thuc", "Giu dung thu tu xep hang", (1 - swap / cmp_total) * 100, "%",
                ghi_chu=f"{cmp_total - swap}/{cmp_total} cap lien ke")
        if gaps:
            add("Do trung thuc", "Khoang cach giua hai ban ghi bi dao", max(gaps), "",
                ghi_chu="lon nhat; nho hon sai so ma hoa nen khong doi quyet dinh")
        add("Do trung thuc", "Truy van giu nguyen toan bo thu tu", q_ok / q_total * 100, "%",
            ghi_chu=f"{q_ok}/{q_total} truy van, moi truy van xep hang {len(next(iter(by_query.values())))} ban ghi")
        add("Do trung thuc", "Truy van giu nguyen ket qua hang 1", rank1_ok / q_total * 100, "%",
            ghi_chu=f"{rank1_ok}/{q_total} truy van")
        add("Do trung thuc", "So truy van cho ket qua khac ban goc", q_total - rank1_ok, "truy van")

# --------------------------------------------------- 6. Một lần nhận dạng
mr, mr_x = read_csv("match_report.csv")
if mr:
    add("Nhan dang mau", "Truy van", mr_x.get("truy_van", ("", ""))[0], "")
    add("Nhan dang mau", "So ban ghi trong CSDL", num(mr_x.get("so_ban_ghi", ("", ""))[0]), "ban ghi")
    swapped = sum(1 for r in mr if r.get("hang_ban_ro") != r.get("hang_ban_ma"))
    add("Nhan dang mau", "So ban ghi bi doi thu hang", swapped, "ban ghi",
        ghi_chu="ban ma so voi ban ro")
    tot = sum(num(r.get("tong_ms"), 0.0) for r in mr)
    add("Nhan dang mau", "Thoi gian quet het CSDL", tot, "ms")

# --------------------------------------------------- 7. Quy mô
per_rec = None
if "server_tinh_toan" in {r.get("chang") for r in pipe}:
    lut = {r["chang"]: num(r["trung_binh_ms"]) for r in pipe if r.get("chang")}
    if lut.get("server_tinh_toan") and lut.get("giai_ma"):
        per_rec = lut["server_tinh_toan"] + lut["giai_ma"]
if per_rec:
    add("Quy mo", "Chi phi moi ban ghi khi quet", per_rec, "ms",
        ghi_chu="tinh + giai ma; ma hoa truy van chi lam mot lan")
    for n in (1_000, 10_000, 100_000):
        add("Quy mo", f"Quet {n:,} nguoi".replace(",", "."), n * per_rec / 1000.0, "giay",
            ghi_chu="che do nhan dang 1:N, quet toan bo co so du lieu")

# --------------------------------------------------- xuất
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["nhom", "hang_muc", "gia_tri", "don_vi", "do_lech_chuan", "min", "max", "ghi_chu"])
    w.writerows(rows)

print(f"Da ghi {len(rows)} dong vao {OUT}\n")
nhom = None
for r in rows:
    if r[0] != nhom:
        nhom = r[0]
        print(f"  [{nhom}]")
    print(f"    {r[1]:<40} {r[2]:>12} {r[3]}")
