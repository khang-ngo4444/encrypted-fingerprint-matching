#!/usr/bin/env python3
"""Trích vector đặc trưng 512 chiều từ ảnh vân tay.

Hướng tiếp cận: FingerCode cổ điển (Jain et al.) — ngân hàng lọc Gabor.
Không dùng mạng nơ-ron, không cần trọng số huấn luyện sẵn.

    8 hướng Gabor  ×  lưới 8×8 ô  =  512 chiều

Quy trình:
  1. Phân vùng tiền cảnh (vùng có vân) bằng phương sai theo khối
  2. Căn tâm theo trọng tâm tiền cảnh — khử lệch tịnh tiến giữa các lần chụp
  3. Cắt cửa sổ cố định, chuẩn hóa tương phản cục bộ
  4. Lọc Gabor 8 hướng, lấy độ lệch tuyệt đối trung bình trong từng ô lưới
  5. Chuẩn hóa L2 về độ dài 1

Bước 5 quan trọng: với vector đơn vị thì ‖q−d‖² = 2 − 2·cos(q,d), nên khoảng
cách Euclidean và độ tương đồng cosine tương đương nhau về mặt xếp hạng.

GIỚI HẠN CẦN BIẾT: bộ trích này không dò điểm lõi (core point) và không khử
xoay. Hai lần quét cùng ngón bị xoay nhiều sẽ ra vector khác nhau đáng kể. Độ
chính xác nhận dạng vì thế thấp hơn hẳn bộ trích thương mại. Đó là giới hạn của
BỘ TRÍCH, không phải của phần mã hóa đồng cấu.

Dùng:
    python extract_features.py <thư_mục_ảnh> <thư_mục_ra>
"""

import os
import sys
import numpy as np
from PIL import Image

DIM_ORIENT = 8          # số hướng Gabor
DIM_GRID = 8            # lưới DIM_GRID × DIM_GRID
FEATURE_DIM = DIM_ORIENT * DIM_GRID * DIM_GRID   # = 512
CROP = 256              # cạnh cửa sổ cắt
RIDGE_FREQ = 1.0 / 9.0  # tần số vân điển hình ở 500 dpi
SCALE_K = 32.0          # hệ số khuếch đại — xem chú thích cuối hàm extract()


def gabor_kernel(theta, freq=RIDGE_FREQ, sigma=4.0, size=17):
    """Nhân Gabor thực, chuẩn hóa về trung bình 0."""
    half = size // 2
    y, x = np.mgrid[-half:half + 1, -half:half + 1].astype(np.float64)
    xr = x * np.cos(theta) + y * np.sin(theta)
    yr = -x * np.sin(theta) + y * np.cos(theta)
    g = np.exp(-(xr ** 2 + yr ** 2) / (2 * sigma ** 2)) * np.cos(2 * np.pi * freq * xr)
    return g - g.mean()


def convolve2d(img, k):
    """Tích chập 2D qua FFT — nhanh hơn hẳn vòng lặp cho ảnh cỡ này."""
    ih, iw = img.shape
    kh, kw = k.shape
    ph, pw = ih + kh - 1, iw + kw - 1
    F = np.fft.rfft2(img, (ph, pw)) * np.fft.rfft2(k, (ph, pw))
    out = np.fft.irfft2(F, (ph, pw))
    return out[kh // 2:kh // 2 + ih, kw // 2:kw // 2 + iw]


def segment_centroid(img, block=16, thresh_ratio=0.3):
    """Trọng tâm vùng tiền cảnh, xác định bằng phương sai theo khối."""
    h, w = img.shape
    bh, bw = h // block, w // block
    var = np.zeros((bh, bw))
    for i in range(bh):
        for j in range(bw):
            var[i, j] = img[i * block:(i + 1) * block, j * block:(j + 1) * block].var()
    mask = var > var.max() * thresh_ratio
    if not mask.any():
        return h / 2.0, w / 2.0
    ys, xs = np.nonzero(mask)
    return (ys.mean() + 0.5) * block, (xs.mean() + 0.5) * block


def crop_centered(img, cy, cx, size=CROP):
    """Cắt cửa sổ size×size quanh (cy,cx); đệm bằng giá trị trung bình nếu tràn."""
    h, w = img.shape
    half = size // 2
    out = np.full((size, size), img.mean(), dtype=np.float64)
    y0, x0 = int(round(cy)) - half, int(round(cx)) - half
    sy0, sx0 = max(0, y0), max(0, x0)
    sy1, sx1 = min(h, y0 + size), min(w, x0 + size)
    if sy1 > sy0 and sx1 > sx0:
        out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
    return out


def normalize_local(img, block=32):
    """Chuẩn hóa tương phản theo khối — khử khác biệt độ sáng giữa các lần quét."""
    out = np.zeros_like(img)
    h, w = img.shape
    for i in range(0, h, block):
        for j in range(0, w, block):
            b = img[i:i + block, j:j + block]
            s = b.std()
            out[i:i + block, j:j + block] = (b - b.mean()) / s if s > 1e-6 else 0.0
    return out


def dominant_orientation(img):
    """Hướng vân trội của toàn ảnh, qua tensor cấu trúc.

    Vân tay là trường sọc, nên hướng chỉ xác định theo modulo 180 độ. Vì vậy
    phải cộng dồn ở miền góc nhân đôi (2θ) rồi mới chia đôi lại — cộng trực
    tiếp các góc θ sẽ triệt tiêu lẫn nhau.
    """
    gy, gx = np.gradient(img)
    gxx, gyy, gxy = (gx * gx).sum(), (gy * gy).sum(), (gx * gy).sum()
    return 0.5 * np.arctan2(2.0 * gxy, gxx - gyy)


def rotate(img, angle, fill):
    """Xoay quanh tâm bằng phép lấy mẫu láng giềng gần nhất."""
    h, w = img.shape
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    dy, dx = yy - cy, xx - cx
    c, s = np.cos(angle), np.sin(angle)
    sy = np.round(cy + c * dy - s * dx).astype(int)
    sx = np.round(cx + s * dy + c * dx).astype(int)
    ok = (sy >= 0) & (sy < h) & (sx >= 0) & (sx < w)
    out = np.full((h, w), fill, dtype=np.float64)
    out[ok] = img[sy[ok], sx[ok]]
    return out


def extract(path):
    """Ảnh -> vector 512 chiều đã chuẩn hóa L2."""
    img = np.asarray(Image.open(path).convert("L"), dtype=np.float64)
    cy, cx = segment_centroid(img)
    img = crop_centered(img, cy, cx)
    # Khử xoay: đưa hướng vân trội về 0 trước khi trích
    img = rotate(img, -dominant_orientation(img), img.mean())
    img = normalize_local(img)

    cell = CROP // DIM_GRID
    feat = np.empty(FEATURE_DIM, dtype=np.float64)
    idx = 0
    for o in range(DIM_ORIENT):
        resp = np.abs(convolve2d(img, gabor_kernel(np.pi * o / DIM_ORIENT)))
        for i in range(DIM_GRID):
            for j in range(DIM_GRID):
                feat[idx] = resp[i * cell:(i + 1) * cell, j * cell:(j + 1) * cell].mean()
                idx += 1

    n = np.linalg.norm(feat)
    if n > 1e-12:
        feat = feat / n
    # Nhan them he so co dinh SCALE_K. Ly do: nhieu cua CKKS la TUYET DOI, khong
    # phai tuong doi — san nhieu ~0.065 gan nhu co dinh. Vector don vi cho khoang
    # cach chi ~0.3-0.5 nen nhieu chiem toi 17%. Nhan ca hai vector cung mot he so
    # K thi khoang cach tang K^2 con nhieu dung yen, dua sai so tuong doi ve ~0.01%.
    # Nhan cung mot hang so khong doi thu tu xep hang, nen tuong duong cosine van giu.
    return feat * SCALE_K


def main():
    if len(sys.argv) < 3:
        sys.exit(f"Dùng: {sys.argv[0]} <thư_mục_ảnh> <thư_mục_ra>")
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)

    files = sorted(f for f in os.listdir(src) if f.lower().endswith((".tif", ".tiff", ".bmp", ".png", ".jpg")))
    if not files:
        sys.exit(f"Không thấy ảnh trong {src}")

    print(f"Trích {FEATURE_DIM} chiều từ {len(files)} ảnh...")
    for n, fn in enumerate(files, 1):
        v = extract(os.path.join(src, fn))
        base = os.path.splitext(fn)[0]
        np.save(os.path.join(dst, base + ".npy"), v)
        if n % 10 == 0 or n == len(files):
            print(f"  {n}/{len(files)}")

    print(f"Xong. Vector .npy nằm ở {dst}")
    print(f"Kiểm tra: ‖v‖ = {np.linalg.norm(v):.4f} (phải bằng SCALE_K = {SCALE_K})")


if __name__ == "__main__":
    main()
