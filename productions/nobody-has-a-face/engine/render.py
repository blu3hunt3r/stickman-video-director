"""Renderer CLI.

  python3 -m engine.render s05                    # full-res scene -> out/scenes/s05.mp4
  python3 -m engine.render s05 --scale 0.5        # half-res preview mp4
  python3 -m engine.render s05 --sheet 12         # contact sheet PNG (12 frames) -> qa/
  python3 -m engine.render s05 --times 0,2.5,7.1  # PNG stills at those scene times -> qa/
  python3 -m engine.render all                    # whole film -> out/video_master.mp4
  python3 -m engine.render s01,s02,s03 --scale 0.5   # several scenes back to back

Run from the production root (the folder that contains engine/ and scenes/).
Scene modules live in scenes/sNN_<slug>.py and define:
    render(f, t, T)          required - draw frame at scene time t (seconds)
    cues(T) -> list          optional - SFX cues (engine.timing.Cue)
    motion_blur(t, T) -> int optional - sub-frames for motion blur at time t (default 1)
"""
import argparse
import glob
import importlib
import math
import multiprocessing as mp
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from engine.core import FPS  # noqa: E402
from engine.frame import Frame  # noqa: E402
from engine.timing import SceneTiming, timeline  # noqa: E402

_MODS = {}


def scene_module(sid):
    if sid not in _MODS:
        paths = glob.glob(os.path.join(ROOT, "scenes", f"{sid}_*.py"))
        if not paths:
            raise FileNotFoundError(f"no scene module scenes/{sid}_*.py")
        name = os.path.splitext(os.path.basename(paths[0]))[0]
        _MODS[sid] = (importlib.import_module(f"scenes.{name}"), SceneTiming(sid))
    return _MODS[sid]


def render_frame(sid, t, scale=1.0):
    mod, T = scene_module(sid)
    n = 1
    if hasattr(mod, "motion_blur"):
        n = max(1, int(mod.motion_blur(t, T)))
    if n == 1:
        f = Frame(t, scale)
        mod.render(f, t, T)
        return f.finish()
    acc = None
    shutter = 0.5 / FPS
    for i in range(n):
        ts = t + shutter * (i / (n - 1) - 0.5) if n > 1 else t
        ts = min(max(ts, 0.0), T.duration - 1e-4)
        f = Frame(ts, scale)
        mod.render(f, ts, T)
        a = f.finish().astype(np.float32)
        acc = a if acc is None else acc + a
    return np.clip(acc / n, 0, 255).astype(np.uint8)


def _job(args):
    sid, idx, scale = args
    t = idx / FPS
    return render_frame(sid, t, scale).tobytes()


def _ffmpeg(out, w, h, crf=15, preset="medium"):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _workers():
    return max(1, int(os.environ.get("RENDER_WORKERS", os.cpu_count() or 1)))


def render_video(sids, out, scale=1.0, workers=None, frame_range=None):
    workers = workers or _workers()
    w, h = int(round(1080 * scale)), int(round(1920 * scale))
    jobs = []
    for sid in sids:
        T = SceneTiming(sid)
        rng = range(T.frames)
        if frame_range:
            rng = range(max(0, frame_range[0]), min(T.frames, frame_range[1]))
        jobs += [(sid, i, scale) for i in rng]
    proc = _ffmpeg(out, w, h)
    t0 = time.time()
    with mp.get_context("fork").Pool(workers) as pool:
        for k, buf in enumerate(pool.imap(_job, jobs, chunksize=2)):
            proc.stdin.write(buf)
            if k % 48 == 0:
                el = time.time() - t0
                print(f"  frame {k}/{len(jobs)}  {el:.0f}s elapsed", flush=True)
    proc.stdin.close()
    proc.wait()
    print(f"wrote {out}  ({len(jobs)} frames, {time.time() - t0:.0f}s)")


def stills(sid, times, scale=0.5, outdir=None):
    from PIL import Image
    outdir = outdir or os.path.join(ROOT, "qa", sid)
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for t in times:
        arr = render_frame(sid, t, scale)
        img = Image.fromarray(arr[..., [2, 1, 0]])
        p = os.path.join(outdir, f"{sid}_t{t:06.3f}.png")
        img.save(p)
        paths.append(p)
    return paths


def contact_sheet(sid, n=12, scale=0.25, cols=6, out=None, times=None):
    """Grid of frames with time labels (QA only - labels never enter the film)."""
    from PIL import Image, ImageDraw
    T = SceneTiming(sid)
    if times is None:
        times = [min(T.duration - 1 / FPS, (i + 0.5) * T.duration / n) for i in range(n)]
    w, h = int(1080 * scale), int(1920 * scale)
    rows = math.ceil(len(times) / cols)
    sheet = Image.new("RGB", (cols * (w + 8) + 8, rows * (h + 30) + 8), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    with mp.get_context("fork").Pool(_workers()) as pool:
        arrs = pool.starmap(render_frame, [(sid, t, scale) for t in times])
    for k, (t, arr) in enumerate(zip(times, arrs)):
        r, c = divmod(k, cols)
        x, y = 8 + c * (w + 8), 8 + r * (h + 30)
        sheet.paste(Image.fromarray(arr[..., [2, 1, 0]]), (x, y))
        d.text((x + 4, y + h + 6), f"{sid} t={t:.2f}s", fill=(230, 230, 230))
    out = out or os.path.join(ROOT, "qa", f"{sid}_sheet.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", help="scene id(s) comma-separated, or 'all'")
    ap.add_argument("--scale", type=float, default=None)
    ap.add_argument("--sheet", type=int, default=0, help="contact sheet with N frames")
    ap.add_argument("--times", type=str, default="", help="comma-separated scene times for PNG stills")
    ap.add_argument("--frames", type=str, default="", help="frame range a:b for video")
    ap.add_argument("--out", type=str, default="")
    ap.add_argument("--workers", type=int, default=0)
    a = ap.parse_args()
    sids = [s["id"] for s in timeline()["scenes"]] if a.scenes == "all" else a.scenes.split(",")
    if a.sheet:
        for sid in sids:
            print(contact_sheet(sid, a.sheet, scale=a.scale if a.scale is not None else 0.25))
        return
    if a.times:
        ts = [float(x) for x in a.times.split(",")]
        for sid in sids:
            for p in stills(sid, ts, scale=a.scale if a.scale is not None else 0.5):
                print(p)
        return
    fr = tuple(int(x) for x in a.frames.split(":")) if a.frames else None
    tag = "all" if a.scenes == "all" else "_".join(sids)
    scale = a.scale if a.scale is not None else 1.0
    suffix = "" if scale == 1.0 else f"_x{scale:g}"
    out = a.out or os.path.join(ROOT, "out", "video_master.mp4" if a.scenes == "all" else f"scenes/{tag}{suffix}.mp4")
    render_video(sids, out, scale, a.workers or None, fr)


if __name__ == "__main__":
    main()
