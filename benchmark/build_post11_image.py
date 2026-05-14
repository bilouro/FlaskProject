"""Generate the post 11 image with throughput bars from real benchmark numbers.

Reads `benchmark/results/bench_summary.csv` (rows: framework × workload)
and picks the `fanout` row for each framework — that's the headline
number for the post.

Output: writes the same PNG three times for the LinkedIn scheduler:
  - <stem>.png         (the source)
  - <stem>-en.png      (used by linkedin scheduler for EN post)
  - <stem>-pt.png      (used by linkedin scheduler for PT post)

Run after `bash run.sh && python results/aggregate.py`.
"""
from __future__ import annotations

import csv
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W = H = 1200
NAVY = (17, 28, 48)
TEAL = (0, 150, 136)
TEAL_DIM = (0, 110, 100)
CREAM = (243, 237, 224)
DIM = (120, 135, 160)
ACCENT = (174, 156, 108)
FLASK_COL = (208, 92, 70)  # warm rust for sync

HELV = "/System/Library/Fonts/Helvetica.ttc"
HELV_NEUE = "/System/Library/Fonts/HelveticaNeue.ttc"

POSTS_DIR = Path("/Users/victor/Documents/GitHub/linkedin/knowledge-base/posts")
CSV_PATH = Path(__file__).parent / "results" / "bench_summary.csv"
STEM = "11-async-fastapi-measured"


def font(size, neue=False, idx=0):
    try:
        return ImageFont.truetype(HELV_NEUE if neue else HELV, size, index=idx)
    except Exception:
        return ImageFont.load_default()


def bolt(d, cx, cy, scale=1.0, fill=TEAL):
    s = scale
    pts = [
        (cx + 0 * s, cy - 90 * s), (cx - 50 * s, cy + 10 * s),
        (cx - 5 * s, cy + 10 * s), (cx - 25 * s, cy + 90 * s),
        (cx + 50 * s, cy - 15 * s), (cx + 5 * s, cy - 15 * s),
    ]
    d.polygon(pts, fill=fill)


def hex_ring(d, cx, cy, R, fill=TEAL, w=8):
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 90)
        pts.append((cx + math.cos(a) * R, cy + math.sin(a) * R))
    d.polygon(pts, outline=fill, width=w)


def load_fanout_rps() -> tuple[float, float]:
    """Return (flask_rps, fastapi_rps) for the fanout workload."""
    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))
    by_fw = {r["framework"]: r for r in rows if r["workload"] == "fanout"}
    flask = float(by_fw["flask"]["rps_median"])
    fastapi = float(by_fw["fastapi"]["rps_median"])
    return flask, fastapi


def build(flask_rps: float, fastapi_rps: float, out_path: Path) -> None:
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)

    # blueprint grid
    for x in range(0, W, 80):
        d.line([(x, 0), (x, H)], fill=(28, 40, 62), width=1)
    for y in range(0, H, 80):
        d.line([(0, y), (W, y)], fill=(28, 40, 62), width=1)

    # top-left wordmark
    cx, cy = 130, 130
    hex_ring(d, cx, cy, 56, fill=TEAL, w=6)
    bolt(d, cx, cy, scale=0.55, fill=TEAL)
    f_wm = font(48, neue=True, idx=2)
    d.text((205, 95), "FastAPI", font=f_wm, fill=CREAM)

    # series tag top-right
    f_tag = font(28, neue=True, idx=0)
    tag = "SERIES · 4/4"
    bbox = d.textbbox((0, 0), tag, font=f_tag)
    tw = bbox[2] - bbox[0]
    d.text((W - 90 - tw, 115), tag, font=f_tag, fill=DIM)
    d.line([(W - 90 - tw, 158), (W - 90, 158)], fill=TEAL, width=3)

    # kicker
    f_kicker = font(34, neue=True, idx=0)
    d.text((110, 295), "PART 4 OF 4", font=f_kicker, fill=TEAL)

    # title
    f_title = font(80, neue=True, idx=2)
    d.text((110, 360), "Async,", font=f_title, fill=CREAM)
    d.text((110, 450), "measured", font=f_title, fill=CREAM)

    # subtitle
    f_sub = font(28, neue=True, idx=0)
    d.text((110, 555), "I/O fanout workload · req/s (median of 3 runs)",
           font=f_sub, fill=DIM)

    # ---- Two framework boxes side by side with horizontal bars ----
    box_w = 480
    box_h = 380
    pad_top = 640
    gap = 40
    total_w = box_w * 2 + gap
    start_x = (W - total_w) // 2

    f_label = font(38, neue=True, idx=2)
    f_value = font(54, neue=True, idx=2)
    f_unit = font(24, neue=True, idx=0)

    max_rps = max(flask_rps, fastapi_rps)

    def draw_box(x, label, rps, bar_color):
        # outer box
        d.rectangle([x, pad_top, x + box_w, pad_top + box_h],
                    outline=CREAM, width=3)
        # label at top
        d.text((x + 30, pad_top + 25), label, font=f_label, fill=CREAM)

        # horizontal bar — width proportional to rps / max_rps
        bar_y = pad_top + 110
        bar_h = 80
        bar_pad_x = 30
        max_bar_w = box_w - 2 * bar_pad_x
        bar_w = int(max_bar_w * (rps / max_rps)) if max_rps else 0
        d.rectangle(
            [x + bar_pad_x, bar_y, x + bar_pad_x + bar_w, bar_y + bar_h],
            fill=bar_color,
        )
        # bar baseline ticks
        for tick in (0.0, 0.25, 0.5, 0.75, 1.0):
            tx = x + bar_pad_x + int(max_bar_w * tick)
            d.line(
                [(tx, bar_y + bar_h + 6), (tx, bar_y + bar_h + 14)],
                fill=DIM, width=2,
            )

        # value
        val_str = f"{rps:,.0f}"
        d.text((x + 30, pad_top + 230), val_str, font=f_value, fill=bar_color)
        d.text((x + 30, pad_top + 305), "req/s · fanout (median)",
               font=f_unit, fill=DIM)

    draw_box(start_x, "Flask  (sync)", flask_rps, FLASK_COL)
    draw_box(start_x + box_w + gap, "FastAPI  (async)", fastapi_rps, TEAL)

    # ratio caption below
    if flask_rps > 0:
        ratio = fastapi_rps / flask_rps
        f_ratio = font(26, neue=True, idx=0)
        cap = f"FastAPI ≈ {ratio:.1f}× Flask on this workload"
        bbox = d.textbbox((0, 0), cap, font=f_ratio)
        cw = bbox[2] - bbox[0]
        d.text(((W - cw) // 2, pad_top + box_h + 20), cap,
               font=f_ratio, fill=DIM)

    # footer
    f_auth = font(22, neue=True, idx=0)
    auth = "bilouro · github.com/bilouro/FastAPIProject"
    bbox = d.textbbox((0, 0), auth, font=f_auth)
    aw = bbox[2] - bbox[0]
    d.text((W - 90 - aw, H - 75), auth, font=f_auth, fill=DIM)

    img.save(out_path)
    print(f"saved {out_path}")


def main() -> int:
    flask_rps, fastapi_rps = load_fanout_rps()
    print(f"flask fanout rps = {flask_rps:.0f}")
    print(f"fastapi fanout rps = {fastapi_rps:.0f}")

    out_base = POSTS_DIR / f"{STEM}.png"
    build(flask_rps, fastapi_rps, out_base)

    # duplicate for the per-language schedule entries (same image, three names)
    for suffix in ("-en", "-pt"):
        target = POSTS_DIR / f"{STEM}{suffix}.png"
        target.write_bytes(out_base.read_bytes())
        print(f"copied  {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
