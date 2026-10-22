"""Smoke test: every scene module imports, renders its edge frames and returns its cues.

    python3 tools/smoke.py                      (all films)
    python3 tools/smoke.py --film red --scale 0.125

Renders, per scene, the first handle frame, t=0, the middle, the last frame and the last
handle frame at a tiny scale, and calls cues(T). Missing scenes are listed, not failed.
Exit status 1 if any scene raised.
"""
import argparse
import os
import sys
import time
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from engine import render as R  # noqa: E402
from engine.timing import timeline  # noqa: E402

FPS = 24.0


def check_film(film, scale):
    ok, bad, missing = [], [], []
    for s in timeline(film)["scenes"]:
        sid = s["id"]
        if R.scene_path(film, sid) is None:
            missing.append(sid)
            continue
        t0 = time.time()
        try:
            mod, T = R.scene_module(film, sid)
            times = [-T.handle_in, 0.0, T.duration / 2, T.duration - 1 / FPS, T.duration + T.handle_out - 1 / FPS]
            for t in times:
                R.render_scene(film, sid, t, scale)
            n = len(mod.cues(T)) if hasattr(mod, "cues") else 0
            ok.append(f"{sid} ({n} cues, {time.time() - t0:.1f}s)")
        except Exception as e:  # noqa: BLE001 - report every failure, keep going
            tb = traceback.extract_tb(e.__traceback__)[-1]
            bad.append(f"{sid}: {type(e).__name__}: {e}  [{os.path.relpath(tb.filename, ROOT)}:{tb.lineno}]")
    return ok, bad, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", default="all")
    ap.add_argument("--scale", type=float, default=0.125)
    a = ap.parse_args()
    films = ["salvage", "shadowplay", "red"] if a.film == "all" else [a.film]
    failed = False
    for film in films:
        ok, bad, missing = check_film(film, a.scale)
        print(f"== {film}: {len(ok)} ok, {len(bad)} failed, {len(missing)} missing")
        for line in ok:
            print("   ok   ", line)
        for line in bad:
            print("   FAIL ", line)
        if missing:
            print("   missing:", " ".join(missing))
        failed |= bool(bad)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
