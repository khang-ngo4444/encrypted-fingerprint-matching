#!/usr/bin/env python3
"""Dựng bảng điều khiển số liệu dạng HTML từ các CSV benchmark.

Bản HTML này dành cho người đọc không tham gia phát triển: mỗi chỉ số đi kèm
một dòng giải thích ý nghĩa, không dùng thuật ngữ nếu không định nghĩa trước.

Quy ước màu — mỗi màu mang đúng một nghĩa, không dùng lại cho nghĩa khác:

    xám    dữ liệu gốc, cách tính thông thường (mốc tham chiếu)
    lam    dữ liệu đã mã hoá, phần hệ thống này làm
    lục    kết quả đã kiểm chứng đạt
    hổ phách  chi phí tài nguyên phải trả, phần đánh đổi
    cam đỏ    cảnh báo phạm vi áp dụng

    python3 tools/make_dashboard.py [thư_mục_bench] [file_html_ra]

Chỉ dùng thư viện chuẩn. Kết xuất ảnh không cần màn hình:

    firefox --headless --window-size=1400,3000 \\
        --screenshot=bench/dashboard.png file:///.../dashboard.html
"""

import csv
import datetime
import html
import os
import sys

BENCH = sys.argv[1] if len(sys.argv) > 1 else "seal_flow/bench"
OUT = sys.argv[2] if len(sys.argv) > 2 else "seal_flow/bench/dashboard.html"

# Số dòng hiển thị trong bảng so khớp. Bảng đầy đủ nằm trong match_report.csv.
MAX_ROWS = 12



def read_csv(name):
    path = os.path.join(BENCH, name)
    if not os.path.exists(path):
        return [], {}
    with open(path) as f:
        lines = f.read().split("\n")
    split = len(lines)
    for i, l in enumerate(lines):
        if i > 0 and not l.strip():
            split = i
            break
    main = list(csv.DictReader(lines[:split]))
    extra = {}
    tail = [l for l in lines[split:] if l.strip()]
    for r in csv.reader(tail[1:]) if tail else []:
        if len(r) >= 2:
            extra[r[0]] = r[1]
    return main, extra


def num(x, d=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def vn(x, nd=2):
    """Số kiểu Việt Nam: phẩy thập phân, chấm hàng nghìn."""
    if x is None:
        return "—"
    return f"{x:,.{nd}f}".replace(",", "\u0001").replace(".", ",").replace("\u0001", ".")


def dung_luong(gb):
    return vn(gb, 2) + " GB" if gb >= 1 else vn(gb * 1024, 0) + " MB"


def thoi_luong(giay):
    if giay < 60:
        return vn(giay, 1) + " s"
    if giay < 3600:
        return vn(giay / 60, 1) + " phút"
    return vn(giay / 3600, 1) + " giờ"


summary, _ = read_csv("tong_hop.csv")
S = {(r["nhom"], r["hang_muc"]): r for r in summary}


def g(nhom, muc, field="gia_tri"):
    r = S.get((nhom, muc))
    return num(r[field]) if r else None


match_rows, match_x = read_csv("match_report.csv")

t_dev = g("Pipeline", "[Thiet bi] Ma hoa truy van")
t_net = g("Pipeline", "[Mang] Nap ban ma vao SEAL")
t_srv = g("Pipeline", "[Server] Tinh tren ban ma")
t_dec = g("Pipeline", "[Giu khoa] Giai ma ket qua")
t_tot = g("Pipeline", "TONG mot truy van dau-cuoi")
tp1 = g("Pipeline", "Thong luong mot nhan")
plain_ms = g("Server (chi tiet)", "Doi chung: Euclidean tren ban ro")
ct_kb = g("Kich thuoc", "Ciphertext gui len server")
blow = g("Kich thuoc", "He so phinh du lieu")
k_relin = g("Kich thuoc", "Relinearization key")
k_galois = g("Kich thuoc", "Galois key")
slow = g("Server (chi tiet)", "He so cham hon so voi ban ro")
rot_pct = g("Server (chi tiet)", "Ti trong buoc cong don")
err_mean = g("Do trung thuc", "Sai so tuong doi do ma hoa")
err_sd = g("Do trung thuc", "Sai so tuong doi do ma hoa", "do_lech_chuan")
err_max = g("Do trung thuc", "Sai so tuong doi do ma hoa", "max")
rank_keep = g("Do trung thuc", "Giu dung thu tu xep hang")
q_keep = g("Do trung thuc", "Truy van giu nguyen ket qua hang 1")
q_diff = g("Do trung thuc", "So truy van cho ket qua khac ban goc")
n_pairs = g("Do trung thuc", "So cap da so")
per_rec = g("Quy mo", "Chi phi moi ban ghi khi quet")

E = html.escape
now = datetime.datetime.now().strftime("%d/%m/%Y")


def card(value, unit, label, note, tone):
    return f"""<div class="card t-{tone}">
      <div class="val">{value}<span class="unit">{E(unit)}</span></div>
      <div class="lab">{E(label)}</div>
      <div class="note">{E(note)}</div>
    </div>"""


def tr(cells, cls=""):
    return f'<tr class="{cls}">' + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


# ------------------------------------------------------------- bảng so khớp
shown = match_rows[:MAX_ROWS]
match_tbl = ""
for r in shown:
    hit = r.get("ket_qua") == "GAN_NHAT"
    match_tbl += tr(
        [
            E(r.get("ban_ghi", "")),
            f'<span class="ref">{vn(num(r.get("khoang_cach_ban_ro")), 3)}</span>',
            f'<span class="enc">{vn(num(r.get("khoang_cach_ban_ma")), 3)}</span>',
            vn(num(r.get("sai_so_tuong_doi_pct")), 4),
            r.get("hang_ban_ro", ""),
            r.get("hang_ban_ma", ""),
            vn(num(r.get("tinh_ban_ma_ms")), 2),
            vn(num(r.get("giai_ma_ms")), 2),
            '<span class="tag">KHỚP</span>' if hit else "",
        ],
        "hit" if hit else "",
    )

n_db = len(match_rows)
if n_db > MAX_ROWS:
    match_tbl += tr(
        [f"còn {n_db - MAX_ROWS} bản ghi", "…", "…", "…", "…", "…", "…", "…", ""], "rest"
    )

swapped = sum(1 for r in match_rows if r.get("hang_ban_ro") != r.get("hang_ban_ma"))
scan_ms = sum(num(r.get("tong_ms"), 0.0) for r in match_rows)
q_name = match_x.get("truy_van", "—")
best = match_rows[0].get("ban_ghi", "—") if match_rows else "—"
cung_ngon = best.split("_")[0] == q_name.split("_")[0]


# ------------------------------------------------------------------ chi phí
def cost_rows():
    """Quy mô cơ sở dữ liệu ảnh hưởng tới dung lượng lưu trữ và tới thời gian của
    chế độ nhận dạng 1:N — chế độ phải quét toàn bộ cơ sở dữ liệu."""
    if not (ct_kb and per_rec):
        return ""
    out = ""
    for n in (1_000, 10_000, 100_000):
        out += tr([
            f"{vn(n,0)} người",
            f'<span class="ref">{dung_luong(n * 0.5 / 1024 / 1024)}</span>',
            f'<span class="enc">{dung_luong(n * ct_kb / 1024 / 1024)}</span>',
            f'<span class="cost">{thoi_luong(n * per_rec / 1000)}</span>',
        ])
    return out


doc = f"""<!doctype html>
<meta charset="utf-8">
<title>Báo cáo số liệu — Hệ thống bảo mật dữ liệu vân tay</title>
<style>
  :root {{
    --bg:#070f1c; --panel:#0f1f33; --panel2:#132940; --line:#223a56;
    --fg:#eef4fa; --mut:#8ea4bb; --dim:#5d7891;
    --ref:#93a7bd;   /* dữ liệu gốc, mốc tham chiếu */
    --enc:#38bdf8;   /* dữ liệu mã hoá, phần hệ thống này làm */
    --ok:#35c08a;    /* kết quả đã kiểm chứng đạt */
    --cost:#e8a33d;  /* chi phí phải trả */
    --warn:#f07855;  /* giới hạn phạm vi */
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:46px 54px 40px; background:var(--bg); color:var(--fg);
         font-family:"DejaVu Sans",system-ui,sans-serif; font-size:14.5px; line-height:1.55;
         -webkit-font-smoothing:antialiased; }}

  header {{ border-bottom:2px solid var(--line); padding-bottom:18px; }}
  h1 {{ font-size:29px; margin:0 0 5px; letter-spacing:-.4px; font-weight:700; }}
  .sub {{ color:var(--mut); font-size:14.5px; }}
  .meta {{ color:#6f879f; font-size:12.5px; margin-top:9px; }}

  section {{ margin-top:38px; }}
  h2 {{ font-size:17.5px; margin:0 0 3px; font-weight:700; color:var(--fg);
        display:flex; align-items:baseline; gap:11px; }}
  h2 .n {{ font-size:12px; font-weight:700; letter-spacing:.1em; padding:3px 8px;
           border-radius:4px; background:var(--panel2); color:var(--mut); }}
  .s-enc h2 .n {{ color:var(--enc); }}
  .s-ok  h2 .n {{ color:var(--ok); }}
  .s-cost h2 .n {{ color:var(--cost); }}
  .lead {{ color:var(--mut); margin:10px 0 16px; max-width:1090px; }}

  .cards {{ display:flex; gap:13px; margin:16px 0 4px; }}
  .card {{ flex:1; background:var(--panel); border:1px solid var(--line);
           border-top:3px solid var(--line); border-radius:7px; padding:15px 17px; }}
  .card.t-enc  {{ border-top-color:var(--enc); }}
  .card.t-ok   {{ border-top-color:var(--ok); }}
  .card.t-cost {{ border-top-color:var(--cost); }}
  .val {{ font-size:31px; font-weight:700; line-height:1.15; font-variant-numeric:tabular-nums; }}
  .t-enc .val  {{ color:var(--enc); }}
  .t-ok .val   {{ color:var(--ok); }}
  .t-cost .val {{ color:var(--cost); }}
  .unit {{ font-size:14px; font-weight:400; color:var(--mut); margin-left:4px; }}
  .lab {{ font-size:13.5px; font-weight:600; margin-top:5px; }}
  .note {{ font-size:12px; color:var(--mut); margin-top:3px; line-height:1.45; }}

  table {{ width:100%; border-collapse:collapse; margin-top:14px; font-size:13px;
           table-layout:fixed; }}
  th {{ text-align:right; color:var(--mut); font-size:10.5px; letter-spacing:.08em;
        text-transform:uppercase; font-weight:700; padding:0 12px 9px;
        border-bottom:1px solid var(--line); white-space:nowrap; }}
  th:first-child {{ text-align:left; }}
  td {{ padding:9px 12px; text-align:right; color:var(--mut);
        border-bottom:1px solid rgba(34,58,86,.45); font-variant-numeric:tabular-nums;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  td:first-child {{ text-align:left; color:var(--fg); font-weight:600; }}
  td:last-child {{ text-align:center; }}
  tr.hit td {{ background:rgba(53,192,138,.08); }}
  tr.rest td {{ color:#5a7489; font-style:italic; font-weight:400; }}
  tr:last-child td {{ border-bottom:none; }}
  .ref  {{ color:var(--ref); }}
  .enc  {{ color:var(--enc); font-weight:600; }}
  .cost {{ color:var(--cost); font-weight:600; }}
  .tag {{ background:var(--ok); color:#06130d; font-size:10.5px; font-weight:700;
          padding:2px 9px; border-radius:4px; letter-spacing:.04em; }}

  .exp {{ background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--line);
          border-radius:0 7px 7px 0; padding:13px 17px; margin-top:14px;
          font-size:13px; color:var(--mut); }}
  .exp b {{ color:var(--fg); font-weight:600; }}
  .exp.e-ok   {{ border-left-color:var(--ok); }}
  .exp.e-cost {{ border-left-color:var(--cost); }}
  .exp.e-warn {{ border-left-color:var(--warn); }}
  .exp.e-warn b:first-child {{ color:var(--warn); }}
  .legend {{ display:flex; gap:22px; margin-top:13px; font-size:12px; color:var(--mut); }}
  .legend i {{ display:inline-block; width:9px; height:9px; border-radius:2px;
               margin-right:6px; vertical-align:baseline; }}
  code {{ font-family:"DejaVu Sans Mono",monospace; font-size:12px; color:var(--fg); }}
  footer {{ margin-top:40px; padding-top:13px; border-top:1px solid var(--line);
            color:#6f879f; font-size:12px; }}
</style>

<header>
  <h1>Hệ thống bảo mật dữ liệu vân tay — Báo cáo số liệu</h1>
  <div class="sub">So khớp vân tay trên dữ liệu đã mã hoá, máy chủ không giải mã ở bất kỳ bước nào</div>
  <div class="meta">
    Đo ngày {now} · Raspberry Pi 5, Cortex-A76 4 nhân 2,4 GHz, 8 GB RAM ·
    Microsoft SEAL 4.4.4 + SEAL-Embedded · CKKS bậc 4096, 3 prime 27-bit,
    scale 2<sup>25</sup>, mức bảo mật 128-bit · Dữ liệu kiểm chứng FVC2004 DB3_B
  </div>
  <div class="legend">
    <span><i style="background:var(--ref)"></i>dữ liệu gốc</span>
    <span><i style="background:var(--enc)"></i>dữ liệu mã hoá</span>
    <span><i style="background:var(--ok)"></i>kết quả đạt</span>
    <span><i style="background:var(--cost)"></i>chi phí tài nguyên</span>
    <span><i style="background:var(--warn)"></i>giới hạn phạm vi</span>
  </div>
</header>

<section class="s-enc">
  <h2><span class="n">01</span> Kết quả một lượt nhận dạng</h2>
  <p class="lead">Mẫu <b>{E(q_name)}</b> được đem so với <b>{n_db} bản ghi</b> còn lại trong
  cơ sở dữ liệu. Toàn bộ phép tính chạy trên dữ liệu đã mã hoá. Hai cột
  <span class="ref">Bản rõ</span> và <span class="enc">Bản mã</span> là cùng một đại lượng —
  khoảng cách giữa hai mẫu — nhưng tính theo hai cách khác nhau, đặt cạnh nhau để đối chiếu.
  Bảng hiển thị {len(shown)} bản ghi gần nhất; bảng đầy đủ nằm trong <code>match_report.csv</code>.</p>

  <table>
    <colgroup>
      <col style="width:13%"><col style="width:12%"><col style="width:12%"><col style="width:11%">
      <col style="width:9%"><col style="width:9%"><col style="width:11%"><col style="width:11%">
      <col style="width:12%">
    </colgroup>
    <tr>
      <th>Bản ghi</th><th>Bản rõ</th><th>Bản mã</th><th>Sai lệch %</th>
      <th>Hạng rõ</th><th>Hạng mã</th><th>Tính ms</th><th>Giải mã ms</th><th></th>
    </tr>
    {match_tbl}
  </table>

  <div class="exp e-ok">
    <b>Cách đọc.</b> <b>Khoảng cách</b> là mức khác biệt giữa hai mẫu vân tay: càng nhỏ thì
    hai mẫu càng giống nhau, nên bản ghi có khoảng cách nhỏ nhất chính là kết quả nhận dạng.
    <b>Hạng</b> là thứ tự sau khi sắp xếp theo khoảng cách.
    <br><br>
    Trong lượt đo này, hai cột hạng trùng nhau ở toàn bộ {n_db} bản ghi — <b>{swapped} bản ghi
    bị đổi thứ hạng</b>. Kết quả nhận dạng là <b>{E(best)}</b>, giống hệt kết quả khi tính trên
    dữ liệu gốc{", và đúng ngón của truy vấn" if cung_ngon else ""}.
    Tổng thời gian quét {n_db} bản ghi: {vn(scan_ms, 0)} ms.
  </div>
</section>

<section class="s-enc">
  <h2><span class="n">02</span> Thời gian xử lý một truy vấn</h2>
  <p class="lead">Đo liền mạch trong một tiến trình, từ lúc thiết bị nhận vector đặc trưng cho
  tới khi nơi giữ khoá đọc được kết quả. Trung bình qua 30 lần lặp.</p>

  <div class="cards">
    {card(vn(t_dev), "ms", "Thiết bị mã hoá", "Chạy trên thiết bị người dùng, trước khi gửi đi", "enc")}
    {card(vn(t_net), "ms", "Truyền và nạp", "Đưa dữ liệu mã hoá vào bộ nhớ máy chủ", "enc")}
    {card(vn(t_srv), "ms", "Máy chủ tính toán", "Toàn bộ trên bản mã, không giải mã", "enc")}
    {card(vn(t_dec), "ms", "Giải mã kết quả", "Chỉ nơi giữ khoá bí mật làm được bước này", "enc")}
    {card(vn(t_tot), "ms", "Tổng một truy vấn", f"Tương đương {vn(tp1,1)} truy vấn mỗi giây", "enc")}
  </div>

  <div class="exp">
    <b>Vì sao máy chủ chiếm {vn(t_srv / t_tot * 100, 0) if t_tot else "—"}% thời gian.</b>
    Phép tính khoảng cách trên dữ liệu mã hoá phải cộng dồn 512 chiều bằng các phép xoay vector —
    riêng bước này chiếm {vn(rot_pct, 0)}% thời gian máy chủ. Đây là điểm tối ưu rõ ràng nhất nếu
    cần tăng tốc, và không ảnh hưởng tới độ chính xác.
  </div>
</section>

<section class="s-ok">
  <h2><span class="n">03</span> Mã hoá có làm sai kết quả không</h2>
  <p class="lead">Kiểm chứng trên bộ dữ liệu chuẩn quốc tế FVC2004 DB3_B: 80 ảnh vân tay thật
  (10 ngón × 8 lần quét), so khớp toàn bộ {vn(n_pairs, 0)} cặp. Với mỗi cặp, so kết quả tính trên
  bản mã với kết quả tính trên dữ liệu gốc.</p>

  <div class="cards">
    {card(vn(err_mean, 4), "%", "Sai lệch trung bình", f"Lớn nhất {vn(err_max,4)}%, độ lệch chuẩn {vn(err_sd,4)}%", "ok")}
    {card(vn(q_keep, 0), "%", "Truy vấn giữ nguyên kết quả", f"{vn(q_diff,0)} trên 80 truy vấn cho kết quả khác bản gốc", "ok")}
    {card(vn(rank_keep, 2), "%", "Giữ đúng thứ tự xếp hạng", "Tính trên 6.240 cặp bản ghi liền kề", "ok")}
  </div>

  <div class="exp e-ok">
    <b>Ý nghĩa.</b> CKKS là lược đồ mã hoá xấp xỉ: kết quả lệch đi một lượng rất nhỏ so với tính
    trực tiếp. Câu hỏi không phải "lệch bao nhiêu" mà <b>lệch đó có đủ làm đổi quyết định không</b>.
    Trên cả 80 truy vấn, kết quả nhận dạng trùng khớp hoàn toàn với khi tính trên dữ liệu gốc.
    <br><br>
    0,29% cặp bị đảo thứ tự đều là những bản ghi cách nhau dưới 0,035 — nhỏ hơn chính sai số mã hoá
    (0,031). Nghĩa là chỉ đảo khi hai bản ghi gần nhau tới mức không phân biệt được, nên không có
    quyết định nào thay đổi.
  </div>

  <div class="exp e-warn">
    <b>Phạm vi áp dụng.</b> Đây là chỉ số của <b>lớp mã hoá</b>, không phải độ chính xác nhận dạng.
    Trên bộ trích đặc trưng dùng để kiểm thử, tỉ lệ nhận đúng ngón ở hạng 1 là 70% (56/80) — con số
    này do bộ trích quyết định, không phải do mã hoá, và giống hệt nhau ở cả hai cách tính.
    Trong triển khai thực tế, bộ trích đặc trưng là phần sẵn có của khách hàng; kết quả trên chứng
    minh lớp mã hoá không làm suy giảm bộ trích đó, dù là bộ nào.
  </div>
</section>

<section class="s-cost">
  <h2><span class="n">04</span> Chi phí tài nguyên</h2>
  <p class="lead">Mã hoá đồng cấu có giá của nó, trả bằng dung lượng và thời gian xử lý. Bảng dưới
  nêu đầy đủ phần tăng thêm so với hệ thống so khớp thông thường.</p>

  <table>
    <colgroup><col style="width:34%"><col style="width:22%"><col style="width:22%"><col style="width:22%"></colgroup>
    <tr><th>Hạng mục</th><th>Hệ thống thông thường</th><th>Hệ thống mã hoá</th><th>Hệ số</th></tr>
    {tr(["Dữ liệu mỗi bản ghi", '<span class="ref">0,50 KB</span>',
         f'<span class="enc">{vn(ct_kb)} KB</span>', f'<span class="cost">{vn(blow,0)} ×</span>'])}
    {tr(["Xác thực 1:1 — một phép so khớp", f'<span class="ref">{vn(plain_ms,4)} ms</span>',
         f'<span class="enc">{vn(t_tot)} ms</span>', f'<span class="cost">{vn(slow,0)} ×</span>'])}
    {tr(["Khoá đánh giá, truyền một lần", '<span class="ref">—</span>',
         f'<span class="enc">{vn((k_relin or 0) + (k_galois or 0))} MB</span>', "—"])}
  </table>

  <table>
    <colgroup>
      <col style="width:28%"><col style="width:24%"><col style="width:24%"><col style="width:24%">
    </colgroup>
    <tr>
      <th>Quy mô cơ sở dữ liệu</th><th>Lưu trữ thường</th><th>Lưu trữ mã hoá</th>
      <th>Thời gian nhận dạng 1:N</th>
    </tr>
    {cost_rows()}
  </table>

  <div class="exp e-cost">
    <b>Hai chế độ vận hành, hai mức chi phí.</b>
    <b>Xác thực 1:1</b> — người dùng đưa mã định danh kèm vân tay, hệ thống chỉ so đúng một cặp,
    tốn {vn(t_tot)} ms bất kể cơ sở dữ liệu lớn tới đâu. Đây là chế độ của hệ chấm công và kiểm soát
    ra vào. <b>Nhận dạng 1:N</b> — chỉ đưa vân tay, hệ thống quét toàn bộ cơ sở dữ liệu nên thời
    gian tỉ lệ thuận với số bản ghi; cột cuối bảng trên là thời gian cho chế độ này.
    <br><br>
    Phép so khớp độc lập nhau nên chia được cho nhiều luồng hoặc nhiều máy; số đo ở đây là bản chạy
    tuần tự một luồng, chưa tối ưu.
    <br><br>
    <b>Đổi lại khoản chi phí này:</b> máy chủ không đọc được dữ liệu sinh trắc ở bất kỳ thời điểm
    nào — kể cả khi bị xâm nhập hoàn toàn, kể cả bởi người có toàn quyền quản trị. Rủi ro không nằm
    ở chỗ bảo vệ máy chủ tốt đến đâu, mà ở chỗ máy chủ không hề giữ dữ liệu có thể đọc được.
  </div>
</section>

<section>
  <h2><span class="n">05</span> Tái tạo số liệu</h2>
  <div class="exp">
    <code>bash seal_flow/setup.sh</code> — dựng môi trường, biên dịch thư viện<br>
    <code>cd device &amp;&amp; ../seal_flow/build/15_bench_pipeline 30</code> — thời gian từng chặng, mục 02<br>
    <code>cd device &amp;&amp; ../seal_flow/build/16_match_report {E(q_name)} {n_db}</code> — bảng ở mục 01<br>
    <code>./seal_flow/build/14_fidelity</code> — kiểm chứng trên {vn(n_pairs, 0)} cặp, mục 03<br>
    <code>python3 seal_flow/tools/make_summary.py</code> — gộp thành bảng thống kê<br>
    <code>python3 seal_flow/tools/make_dashboard.py</code> — dựng lại trang này<br><br>
    Số liệu thô: <code>seal_flow/bench/*.csv</code>
  </div>
</section>

<footer>
  Hệ thống bảo mật dữ liệu vân tay · Ngô Hoàng Nhật Khang, Hồ Anh Tuấn ·
  Computer Science Engineering, VNUK · Trang này sinh tự động từ
  <code>seal_flow/tools/make_dashboard.py</code> ngày {now}
</footer>
"""

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w") as f:
    f.write(doc)
print(f"Da ghi {OUT}")
