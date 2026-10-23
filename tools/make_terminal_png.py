#!/usr/bin/env python3
"""Chạy một lệnh và chụp dòng ra thật của nó thành ảnh PNG khung terminal.

Chiều cao ảnh tự tính theo số dòng nên không bị cắt.

    python make_terminal_png.py <ảnh_ra.png> <lệnh...>
"""

import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

PAD = 40
BAR_H = 44
LINE_H = 28
FONT_SIZE = 20
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

BG = (15, 28, 46)
FG = (223, 231, 240)
DIM = (120, 140, 160)
TITLE_BAR = (22, 38, 60)

ANSI = {
    "0": FG,
    "1;97": (255, 255, 255),
    "38;5;80": (34, 211, 238),
    "38;5;245": (138, 150, 164),
}
ANSI_RE = re.compile(r"\033\[([0-9;]*)m")


def split_ansi(line):
    out, pos, color = [], 0, FG
    for m in ANSI_RE.finditer(line):
        if m.start() > pos:
            out.append((line[pos : m.start()], color))
        color = ANSI.get(m.group(1), FG if m.group(1) in ("", "0") else color)
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], color))
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(f"Dùng: {sys.argv[0]} <ảnh_ra.png> <lệnh...>")
    out_path, cmd = sys.argv[1], sys.argv[2:]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        print(f"CẢNH BÁO: lệnh trả về mã {proc.returncode}", file=sys.stderr)
    lines = proc.stdout.rstrip("\n").split("\n")

    font = ImageFont.truetype(MONO, FONT_SIZE)
    bold = ImageFont.truetype(MONO_BOLD, FONT_SIZE)

    plain = ["".join(c for c, _ in split_ansi(ln)) for ln in lines]
    width = max(int(font.getlength(p)) for p in plain) + PAD * 2
    height = BAR_H + PAD + len(lines) * LINE_H + PAD

    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, width, BAR_H], fill=TITLE_BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([PAD + i * 24 - 7, BAR_H // 2 - 7, PAD + i * 24 + 7, BAR_H // 2 + 7], fill=c)
    label = "ourpi@raspberrypi: ~/CoreMetEncrypt"
    d.text((width // 2 - font.getlength(label) / 2, BAR_H // 2 - 11), label, font=font, fill=DIM)

    y = BAR_H + PAD
    for line in lines:
        x = PAD
        for chunk, color in split_ansi(line):
            d.text((x, y), chunk, font=bold if color == (255, 255, 255) else font, fill=color)
            x += font.getlength(chunk)
        y += LINE_H

    img.save(out_path)
    print(f"Xong: {out_path}  ·  {width}x{height}  ·  {len(lines)} dòng")


if __name__ == "__main__":
    main()
