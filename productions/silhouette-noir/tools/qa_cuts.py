"""Cut-continuity sheets: for every scene boundary, the outgoing scene's last body frame,
three composited frames across the transition window, and the incoming scene's first body
frame, side by side. Also measures how much of each frame is RED (STYLE.md rule 5).

  RENDER_WORKERS=4 python3 tools/qa_cuts.py --film red [--scale 0.2] [--only s03,s04]
  -> films/<film>/qa/cuts.png and films/<film>/qa/red_share.json
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from engine.core import FPS  # noqa: E402
from engine.render import _render_many, _sheet, _window, _active  # noqa: E402
from engine.timing import film_dir, timeline  # noqa: E402


def red_share(arr):
    b, g, r = (arr[..., i].astype(np.int32) for i in range(3))
    m = (r > 90) & (r > 2 * g) & (r > 2 * b)
    return float(m.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", required=True)
    ap.add_argument("--scale", type=float, default=0.2)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    sc = timeline(a.film)["scenes"]
    only = set(x for x in a.only.split(",") if x)
    jobs, labels = [], []
    for A, B in zip(sc, sc[1:]):
        if only and not ({A["id"], B["id"]} & only):
            continue
        cut = B["start"]
        tr = A["trans_out"]
        w0, w1 = _window(tr, cut) if _active(tr) else (cut, cut)
        pre, post = w0 - 1.0 / FPS, w1
        ts = [pre] + ([w0 + (w1 - w0) * k for k in (0.25, 0.5, 0.75)] if w1 > w0 else [cut - 0.5 / FPS] * 0) + [post]
        for t in ts:
            jobs.append(("film", a.film, None, max(0.0, t), a.scale))
            kind = tr["kind"] if _active(tr) else "cut"
            labels.append(f"{A['id']}>{B['id']} {kind} {t:.2f}")
    arrs = _render_many(jobs, None)
    cols = 5
    out = film_dir(a.film, "qa", "cuts.png")
    # pad rows of hard cuts (2 frames) to 5 columns for a clean grid
    grid_a, grid_l = [], []
    i = 0
    while i < len(arrs):
        n = 5 if (i + 4 < len(labels) and labels[i].split()[0] == labels[i + 4].split()[0]) else 2
        row_a, row_l = arrs[i:i + n], labels[i:i + n]
        while len(row_a) < cols:
            row_a.append(np.zeros_like(arrs[0]))
            row_l.append("")
        grid_a += row_a
        grid_l += row_l
        i += n
    print(_sheet(grid_a, grid_l, a.scale, cols, out))
    share = {lab: round(red_share(x) * 100, 2) for lab, x in zip(labels, arrs)}
    with open(film_dir(a.film, "qa", "red_share.json"), "w") as fh:
        json.dump(share, fh, indent=1)
    worst = sorted(share.items(), key=lambda kv: -kv[1])[:5]
    print("most red (% of frame):", worst)


if __name__ == "__main__":
    main()
