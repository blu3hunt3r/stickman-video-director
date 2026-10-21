"""Style-contract QA: palette discipline per scene.

Samples frames, converts to HSV and checks every saturated pixel against the three allowed
accent families (streetlamp amber, blood crimson, siren blue). Everything else in Style 1 Dark
must be white/gray line art on black. Reports the off-palette share and the dominant stray hue.

  python3 tools/qa_palette.py s01 s02 ...      (default: all scenes present)
"""
import glob
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.render import render_frame  # noqa: E402
from engine.timing import SceneTiming, timeline  # noqa: E402

ALLOWED = [(18, 64), (335, 360), (0, 12), (195, 235)]   # amber (incl. hot cores), crimson (wraps), blue


def hsv(arr):
    rgb = arr[..., [2, 1, 0]].astype(np.float32) / 255.0
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-6
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-6), 0)
    return h, s, mx


def check(sid, n=10, scale=0.25):
    T = SceneTiming(sid)
    times = [(i + 0.5) * T.duration / n for i in range(n)]
    worst = []
    tot_sat = tot_bad = 0
    for t in times:
        a = render_frame(sid, t, scale)
        h, s, v = hsv(a)
        sat = (s > 0.35) & (v > 0.18)
        ok = np.zeros_like(sat)
        for lo, hi in ALLOWED:
            ok |= (h >= lo) & (h <= hi)
        bad = sat & ~ok
        ns, nb = int(sat.sum()), int(bad.sum())
        tot_sat += ns
        tot_bad += nb
        if nb:
            hb = h[bad]
            worst.append((t, nb, float(np.median(hb))))
    share = tot_bad / max(1, tot_sat)
    flag = "OK " if share < 0.02 else "CHECK"
    msg = f"{flag} {sid}: saturated px {tot_sat}, off-palette {tot_bad} ({share:.1%})"
    if worst:
        w = max(worst, key=lambda x: x[1])
        msg += f"  worst t={w[0]:.2f}s n={w[1]} median hue {w[2]:.0f}°"
    print(msg, flush=True)
    return share


def main():
    sids = sys.argv[1:] or [s["id"] for s in timeline()["scenes"]
                            if glob.glob(os.path.join(ROOT, "scenes", f"{s['id']}_*.py"))]
    for sid in sids:
        check(sid)


if __name__ == "__main__":
    main()
