#!/usr/bin/env python3
"""Chụp kết quả chạy thật thành ảnh, không cần màn hình.

Chạy chương trình, bắt lấy toàn bộ output, bọc trong một khung cửa sổ terminal
rồi kết xuất ra HTML. Dùng firefox --headless để biến thành PNG.

Lý do không chụp màn hình thật: máy đo là Raspberry Pi chạy không có màn hình,
mà output cần nguyên văn chứ không phải ảnh chụp lại của ảnh chụp.

    python3 tools/make_terminal_shot.py <file_html_ra> <lenh...>
"""

import html
import os
import subprocess
import sys

if len(sys.argv) < 3:
    sys.exit(f"Dung: {sys.argv[0]} <file_html_ra> <lenh...>")

out = sys.argv[1]
cmd = sys.argv[2:]
cwd = os.environ.get("SHOT_CWD")

proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
body = proc.stdout + (proc.stderr if proc.returncode else "")
lines = body.rstrip("\n").split("\n")

CSS_HL = {
    "KET LUAN": "hl",
    "GAN NHAT": "ok",
    "TRUNG NHAU": "ok",
    "GIU NGUYEN": "ok",
    "DUNG NGON": "ok",
}


def fmt(line):
    e = html.escape(line)
    if set(line.strip()) in ({"="}, {"-"}):
        return f'<span class="dim">{e}</span>'
    for key, cls in CSS_HL.items():
        if key in line:
            e = e.replace(key, f'<span class="{cls}">{key}</span>')
    if line.startswith(" ") and ":" in line:
        head, _, tail = e.partition(":")
        return f'<span class="key">{head}</span>:{tail}'
    return e


prompt = " ".join(cmd[-3:]) if len(cmd) > 2 else " ".join(cmd)
doc = f"""<!doctype html>
<meta charset="utf-8">
<style>
  body {{ margin:0; padding:34px; background:#060d18;
          font-family:"DejaVu Sans",system-ui,sans-serif; }}
  .win {{ background:#0a1628; border:1px solid #28415e; border-radius:10px;
          overflow:hidden; box-shadow:0 18px 50px rgba(0,0,0,.55); }}
  .bar {{ background:#13263d; padding:10px 16px; display:flex; align-items:center;
          gap:8px; border-bottom:1px solid #28415e; }}
  .dot {{ width:11px; height:11px; border-radius:50%; }}
  .t {{ margin-left:12px; color:#9fb2c6; font-size:12.5px;
        font-family:"DejaVu Sans Mono",monospace; }}
  pre {{ margin:0; padding:22px 24px; color:#cfe0ee; font-size:13.5px; line-height:1.5;
         font-family:"DejaVu Sans Mono",monospace; white-space:pre; }}
  .cmd {{ color:#22d3ee; }}
  .dim {{ color:#3b566f; }}
  .key {{ color:#9fb2c6; }}
  .ok  {{ color:#43d9a3; font-weight:700; }}
  .hl  {{ color:#22d3ee; font-weight:700; }}
</style>
<div class="win">
  <div class="bar">
    <span class="dot" style="background:#ef5b5b"></span>
    <span class="dot" style="background:#e0a23a"></span>
    <span class="dot" style="background:#43d9a3"></span>
    <span class="t">ourpi@raspberrypi5: ~/CoreMetEncrypt</span>
  </div>
  <pre><span class="cmd">$ {html.escape(prompt)}</span>
{chr(10).join(fmt(l) for l in lines)}</pre>
</div>
"""

os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
with open(out, "w") as f:
    f.write(doc)
print(f"Da ghi {out}  ({len(lines)} dong)")
