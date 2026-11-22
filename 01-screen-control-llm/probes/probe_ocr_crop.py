"""Reproducible probe for A8: RapidOCR full frame vs 400x800 panel crop.

Renders a synthetic 1456x818 UI frame (editor-like text on the left,
chat-panel-like text on the right at x>1000) so the measurement can be
repeated without a private screenshot or a live desktop. Outputs live in a
temp dir; nothing private is committed.

Usage: python probes/probe_ocr_crop.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from rapidocr_onnxruntime import RapidOCR

W, H = 1456, 818


def render_frame() -> Image.Image:
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    y = 40
    for i in range(70):  # editor-like block on the left
        d.text((40, y), f"def process_row({i}): return data[{i}] * 2  # column {i}", fill="black", font=font)
        y += 12
    y = 40
    for i in range(45):  # chat-panel-like text on the right (x > 1000)
        d.text((1040, y), f"[Agent] step {i}: proceeding with the plan on target row {i}", fill="black", font=font)
        y += 18
    d.text((1040, y + 24), "Keep   Undo   Allow all   Describe what to build", fill="black", font=font)
    return img


def main() -> int:
    frame = render_frame()
    out = Path(tempfile.mkdtemp(prefix="ocr_probe_"))
    frame_png = out / "ocr_frame_1456x818.png"
    crop_png = out / "ocr_crop_400x800.png"
    frame.save(frame_png)
    frame.crop((1040, 0, 1440, 800)).save(crop_png)  # 400x800; PIL box = (left, top, right, bottom)

    ocr = RapidOCR()
    t0 = time.time()
    res_full, _ = ocr(str(frame_png))
    t_full = time.time() - t0
    t0 = time.time()
    res_crop, _ = ocr(str(crop_png))
    t_crop = time.time() - t0

    print(f"FULL_FRAME  {t_full:.2f}s  boxes={len(res_full or [])}  {frame_png}")
    print(f"CROP_400x800 {t_crop:.2f}s  boxes={len(res_crop or [])}  {crop_png}")
    print(f"SPEEDUP     {t_full / t_crop:.1f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
