"""Cut-continuity sheet: last frame of each scene beside the first frame of the next.

  python3 tools/qa_cuts.py            -> qa/cuts_sheet.png  (only pairs whose scenes exist)
"""
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PIL import Image, ImageDraw  # noqa: E402

from engine.core import FPS  # noqa: E402
from engine.render import render_frame  # noqa: E402
from engine.timing import SceneTiming, timeline  # noqa: E402

SCALE = 0.2


def exists(sid):
    return bool(glob.glob(os.path.join(ROOT, "scenes", f"{sid}_*.py")))


def main():
    ids = [s["id"] for s in timeline()["scenes"]]
    pairs = [(a, b) for a, b in zip(ids, ids[1:]) if exists(a) and exists(b)]
    w, h = int(1080 * SCALE), int(1920 * SCALE)
    cols = 3
    rows = (len(pairs) + cols - 1) // cols
    cell_w = 2 * w + 12
    sheet = Image.new("RGB", (cols * (cell_w + 20) + 20, rows * (h + 34) + 20), (45, 45, 45))
    d = ImageDraw.Draw(sheet)
    for k, (a, b) in enumerate(pairs):
        Ta = SceneTiming(a)
        fa = render_frame(a, Ta.duration - 1.0 / FPS, SCALE)
        fb = render_frame(b, 0.0, SCALE)
        r, c = divmod(k, cols)
        x, y = 20 + c * (cell_w + 20), 20 + r * (h + 34)
        sheet.paste(Image.fromarray(fa[..., [2, 1, 0]]), (x, y))
        sheet.paste(Image.fromarray(fb[..., [2, 1, 0]]), (x + w + 12, y))
        d.text((x, y + h + 6), f"{a} end  |  {b} start", fill=(235, 235, 235))
    out = os.path.join(ROOT, "qa", "cuts_sheet.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print(out, f"{len(pairs)} cuts")


if __name__ == "__main__":
    main()
