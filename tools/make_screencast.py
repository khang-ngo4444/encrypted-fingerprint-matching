#!/usr/bin/env python3
"""Quay một phiên terminal thành MP4 trên máy không có màn hình.

Chạy thật các lệnh, bắt đúng dòng ra, vẽ lại thành khung hình rồi đẩy sang
ffmpeg. Dòng ra là thật, không dựng lại bằng tay.

Tệp kịch bản:
    # chú thích, không hiện
    $ lệnh       → gõ ra rồi chạy, bắt dòng ra
    > chữ        → in thẳng, không chạy
    @pause 2     → dừng 2 giây
    @clear       → xóa màn hình

    python make_screencast.py <kịch_bản.txt> <video_ra.mp4> [--fps 12] [--cps 28]
"""

import argparse
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 900
PAD = 36
LINE_H = 26
FONT_SIZE = 19
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

MAX_LINES = (H - PAD * 2 - 40) // LINE_H


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


class Screen:
    def __init__(self):
        self.lines = []
        self.font = ImageFont.truetype(MONO, FONT_SIZE)
        self.bold = ImageFont.truetype(MONO_BOLD, FONT_SIZE)

    def write(self, text):
        for raw in text.split("\n"):
            self.lines.append(raw.rstrip("\r"))
        del self.lines[: max(0, len(self.lines) - MAX_LINES)]

    def replace_last(self, text):
        if self.lines:
            self.lines[-1] = text
        else:
            self.lines.append(text)

    def clear(self):
        self.lines = []

    def render(self):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)

        d.rectangle([0, 0, W, 34], fill=TITLE_BAR)
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([PAD + i * 22 - 6, 11, PAD + i * 22 + 6, 23], fill=c)
        d.text((W // 2 - 160, 9), "ourpi@raspberrypi: ~/CoreMetEncrypt", font=self.font, fill=DIM)

        y = PAD + 24
        for line in self.lines:
            x = PAD
            for chunk, color in split_ansi(line):
                font = self.bold if color == (255, 255, 255) else self.font
                d.text((x, y), chunk, font=font, fill=color)
                x += self.font.getlength(chunk)
            y += LINE_H
        return img


def parse_script(path):
    steps = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line.startswith("$ "):
                steps.append(("run", line[2:]))
            elif line.startswith("> "):
                steps.append(("echo", line[2:]))
            elif line.startswith("@pause"):
                steps.append(("pause", float(line.split()[1])))
            elif line.startswith("@clear"):
                steps.append(("clear", None))
            else:
                steps.append(("echo", line))
    return steps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("out")
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--cps", type=float, default=28.0)
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--audio", help="tệp nhạc nền, cắt theo độ dài video và fade 2 giây cuối")
    ap.add_argument("--audio-gain", type=float, default=0.35,
                    help="hệ số âm lượng nhạc nền, mặc định 0.35")
    args = ap.parse_args()

    steps = parse_script(args.script)
    scr = Screen()

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(args.fps), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
         args.out],
        stdin=subprocess.PIPE,
    )

    n_frames = 0

    def emit(count=1):
        nonlocal n_frames
        buf = scr.render().tobytes()
        for _ in range(count):
            ff.stdin.write(buf)
            n_frames += 1

    def hold(seconds):
        emit(max(1, round(seconds * args.fps)))

    prompt = "\033[38;5;80m$\033[0m "
    hold(0.8)

    for kind, payload in steps:
        if kind == "clear":
            scr.clear()
            hold(0.3)

        elif kind == "pause":
            hold(payload)

        elif kind == "echo":
            scr.write(payload)
            hold(0.45)

        elif kind == "run":
            scr.write(prompt)
            per_char = max(1, round(args.fps / args.cps))
            for i in range(1, len(payload) + 1):
                scr.replace_last(prompt + payload[:i])
                emit(per_char)
            hold(0.5)

            # Chạy xong rồi mới vẽ: vừa chạy vừa vẽ thì phần vẽ tranh CPU với
            # phép đo, làm các con số mili giây cao hơn thực tế.
            proc = subprocess.run(
                ["bash", "-c", payload],
                cwd=args.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if proc.returncode != 0:
                print(f"CẢNH BÁO: lệnh trả về mã {proc.returncode}: {payload}", file=sys.stderr)
            for out_line in proc.stdout.split("\n"):
                scr.write(out_line.rstrip("\r"))
                emit(1)
            hold(1.2)

    hold(2.0)
    ff.stdin.close()
    ff.wait()

    if args.audio:
        secs = n_frames / args.fps
        mixed = args.out + ".tmp.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-i", args.out, "-i", args.audio,
             "-filter_complex",
             f"[1:a]volume={args.audio_gain},afade=t=out:st={max(0, secs - 2):.2f}:d=2[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
             "-shortest", mixed],
            check=True,
        )
        os.replace(mixed, args.out)

    print(f"Xong: {args.out}  ·  {n_frames / args.fps:.1f}s  ·  "
          f"{os.path.getsize(args.out) / 1e6:.1f} MB  ·  {W}x{H} @ {args.fps}fps"
          + ("  · có nhạc nền" if args.audio else ""))


if __name__ == "__main__":
    main()
