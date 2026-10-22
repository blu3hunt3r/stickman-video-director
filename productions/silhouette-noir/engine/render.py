"""Renderer CLI (run from the production root, the folder that contains engine/ and films/).

  python3 -m engine.render --film red s03                 # scene alone, full res -> films/red/out/scenes/s03.mp4
  python3 -m engine.render --film red s03 --scale 0.5     # half-res preview
  python3 -m engine.render --film red s03 --handles       # include the pre/post-roll handles
  python3 -m engine.render --film red s03 --sheet 12      # contact sheet PNG -> films/red/qa/
  python3 -m engine.render --film red s03 --times 0,2.5   # PNG stills at scene times -> films/red/qa/s03/
  python3 -m engine.render --film red --cut s03 --scale 0.5     # the transition into s03, composited
  python3 -m engine.render --film red --range 30:42 --sheet 12  # any film-time span, composited
  python3 -m engine.render --film red all                 # whole film -> films/red/out/red_master.mp4

The whole film is rendered as segments (each scene's body, and each transition window between
two scenes) into films/<film>/out/seg_x<scale>/ and joined without re-encoding. Segments that
already exist are kept: pass --only s05,s06 to re-render the segments touching those scenes, or
--force to re-render everything.

Scene modules live in films/<film>/scenes/sNN_<slug>.py and define:
    render(f, t, T)          required - draw the frame at scene time t (seconds); t may be < 0
                             or >= T.duration inside the transition handles
    cues(T) -> list          optional - sound cues (engine.timing.Cue) for the sound team
    motion_blur(t, T) -> int optional - sub-frames for motion blur at time t (default 1)
Set RENDER_WORKERS=1 when several people share the machine.
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

from engine.core import FPS, W, H  # noqa: E402
from engine.frame import Frame  # noqa: E402
from engine.palette import PALETTES  # noqa: E402
from engine.timing import SceneTiming, film_dir, timeline  # noqa: E402

_MODS = {}
PLACEHOLDERS = os.environ.get("RENDER_PLACEHOLDERS", "1") != "0"


def scene_path(film, sid):
    paths = sorted(glob.glob(film_dir(film, "scenes", f"{sid}_*.py")))
    return paths[0] if paths else None


def scene_module(film, sid):
    key = (film, sid)
    if key not in _MODS:
        p = scene_path(film, sid)
        if p is None:
            if not PLACEHOLDERS:
                raise FileNotFoundError(f"no scene module films/{film}/scenes/{sid}_*.py")
            mod = None
        else:
            name = os.path.splitext(os.path.basename(p))[0]
            mod = importlib.import_module(f"films.{film}.scenes.{name}")
        _MODS[key] = (mod, SceneTiming(film, sid))
    return _MODS[key]


def _slate(film, T, t, scale):
    """Stand-in frame for a scene that has not been written yet."""
    pal = PALETTES[film]
    f = Frame(t, scale, pal=pal)
    f.sky(pal.fog_at(0.9), pal.fog_at(0.2))
    with f.screen() as c:
        c.set_source_rgb(*pal.ink)
        c.select_font_face("Sans")
        c.set_font_size(90)
        c.move_to(120, 900)
        c.show_text(f"{T.id}  {T.slug}")
        c.set_font_size(60)
        c.move_to(120, 1000)
        c.show_text(f"t = {t:5.2f} / {T.duration:.2f}")
    return f.finish()


def render_scene(film, sid, t, scale=1.0):
    """One frame of scene `sid` at scene time t (BGRA uint8)."""
    mod, T = scene_module(film, sid)
    if mod is None:
        return _slate(film, T, t, scale)
    pal = PALETTES[film]
    n = max(1, int(mod.motion_blur(t, T))) if hasattr(mod, "motion_blur") else 1
    if n == 1:
        f = Frame(t, scale, pal=pal)
        mod.render(f, t, T)
        return f.finish()
    acc = None
    shutter = 0.5 / FPS
    for i in range(n):
        ts = t + shutter * (i / (n - 1) - 0.5)
        f = Frame(ts, scale, pal=pal)
        mod.render(f, ts, T)
        a = f.finish().astype(np.float32)
        acc = a if acc is None else acc + a
    return np.clip(acc / n, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------- film clock
def _window(tr, cut):
    d, al = tr.get("dur", 0.0), tr.get("align", 0.5)
    return cut - d * al, cut + d * (1 - al)


def _active(tr):
    return bool(tr) and tr.get("kind", "cut") != "cut" and tr.get("dur", 0) > 0


def owner(film, t):
    """What the film shows at film time t: ('s', sid) or ('x', sid_a, sid_b) in a transition."""
    sc = timeline(film)["scenes"]
    i = len(sc) - 1
    for k, s in enumerate(sc):
        if t < s["start"] + s["duration"]:
            i = k
            break
    s = sc[i]
    if i > 0 and _active(s["trans_in"]):
        w0, w1 = _window(s["trans_in"], s["start"])
        if w0 <= t < w1:
            return ("x", sc[i - 1]["id"], s["id"])
    if i + 1 < len(sc) and _active(s["trans_out"]):
        w0, w1 = _window(s["trans_out"], s["start"] + s["duration"])
        if w0 <= t < w1:
            return ("x", s["id"], sc[i + 1]["id"])
    return ("s", s["id"])


def _scene(film, sid):
    return next(s for s in timeline(film)["scenes"] if s["id"] == sid)


def film_frame(film, t, scale=1.0):
    """One composited frame of the film at film time t."""
    o = owner(film, t)
    if o[0] == "s":
        return render_scene(film, o[1], t - _scene(film, o[1])["start"], scale)
    from engine import transitions
    a, b = _scene(film, o[1]), _scene(film, o[2])
    tr = a["trans_out"]
    w0, w1 = _window(tr, b["start"])
    u = (t - w0) / max(w1 - w0, 1e-9)
    A = render_scene(film, a["id"], t - a["start"], scale)
    B = render_scene(film, b["id"], t - b["start"], scale)
    params = {k: v for k, v in tr.items() if k not in ("kind", "dur", "align")}
    return transitions.apply(tr["kind"], A, B, u, t=t - w0, **params)


# ----------------------------------------------------------------------------- jobs + encode
def _job(args):
    kind, film, key, t, scale = args
    if kind == "scene":
        arr = render_scene(film, key, t, scale)
    else:
        arr = film_frame(film, t, scale)
    return np.ascontiguousarray(arr).tobytes()


def _ffmpeg(out, w, h, crf=15, preset="medium"):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}",
           "-r", str(FPS), "-i", "-",
           "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-movflags", "+faststart", out]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _workers(n=None):
    return max(1, int(n or os.environ.get("RENDER_WORKERS", os.cpu_count() or 1)))


class _Pool:
    """Process pool, or plain in-process mapping when workers == 1."""

    def __init__(self, workers):
        self.workers = workers
        self.pool = mp.get_context("fork").Pool(workers) if workers > 1 else None

    def imap(self, fn, jobs):
        if self.pool is None:
            return map(fn, jobs)
        return self.pool.imap(fn, jobs, chunksize=2)

    def close(self):
        if self.pool is not None:
            self.pool.close()
            self.pool.join()


def encode(jobs, out, scale, pool, label=""):
    w, h = int(round(W * scale)), int(round(H * scale))
    proc = _ffmpeg(out, w, h)
    t0 = time.time()
    for k, buf in enumerate(pool.imap(_job, jobs)):
        proc.stdin.write(buf)
        if k % 48 == 0 and k:
            print(f"  {label} frame {k}/{len(jobs)}  {time.time() - t0:.0f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    print(f"wrote {out}  ({len(jobs)} frames, {time.time() - t0:.0f}s)", flush=True)
    return out


def _sfx(scale):
    return "" if scale == 1.0 else f"_x{scale:g}"


def render_scene_video(film, sid, scale=1.0, workers=None, handles=False, frame_range=None, out=None):
    T = SceneTiming(film, sid)
    k0, k1 = 0, T.frames
    if handles:
        k0 = -int(math.ceil(T.handle_in * FPS - 1e-9))
        k1 = T.frames + int(math.ceil(T.handle_out * FPS - 1e-9))
    if frame_range:
        k0, k1 = max(k0, frame_range[0]), min(k1, frame_range[1])
    jobs = [("scene", film, sid, k / FPS, scale) for k in range(k0, k1)]
    out = out or film_dir(film, "out", "scenes", f"{sid}{'_h' if handles else ''}{_sfx(scale)}.mp4")
    pool = _Pool(_workers(workers))
    try:
        return encode(jobs, out, scale, pool, sid)
    finally:
        pool.close()


def render_range(film, t0, t1, scale=1.0, workers=None, out=None):
    k0, k1 = int(math.floor(t0 * FPS + 1e-9)), int(math.ceil(t1 * FPS - 1e-9))
    jobs = [("film", film, None, k / FPS, scale) for k in range(k0, k1)]
    out = out or film_dir(film, "out", "ranges", f"{t0:07.2f}-{t1:07.2f}{_sfx(scale)}.mp4")
    pool = _Pool(_workers(workers))
    try:
        return encode(jobs, out, scale, pool, f"{t0:.1f}-{t1:.1f}")
    finally:
        pool.close()


def film_plan(film):
    """Partition the film's frames into segments: [(label, k0, k1, scenes_touched)]."""
    n = timeline(film)["frames"]
    segs = []
    for k in range(n):
        o = owner(film, k / FPS)
        if segs and segs[-1][0] == o:
            segs[-1][2] = k + 1
        else:
            segs.append([o, k, k + 1])
    plan = []
    for o, k0, k1 in segs:
        label = o[1] if o[0] == "s" else f"{o[1]}-{o[2]}"
        plan.append((label, k0, k1, set(o[1:])))
    return plan


def render_film(film, scale=1.0, workers=None, only=None, force=False, out=None):
    plan = film_plan(film)
    sdir = film_dir(film, "out", f"seg{_sfx(scale) or '_x1'}")
    os.makedirs(sdir, exist_ok=True)
    keep, todo = [], []
    for label, k0, k1, touched in plan:
        p = os.path.join(sdir, f"{k0:05d}_{label}.mp4")
        keep.append(p)
        if force or not os.path.exists(p) or (only and touched & set(only)):
            todo.append((label, k0, k1, p))
    for p in glob.glob(os.path.join(sdir, "*.mp4")):
        if p not in keep:
            os.remove(p)
    print(f"{film}: {len(plan)} segments, rendering {len(todo)}", flush=True)
    pool = _Pool(_workers(workers))
    try:
        for label, k0, k1, p in todo:
            jobs = [("film", film, None, k / FPS, scale) for k in range(k0, k1)]
            encode(jobs, p, scale, pool, label)
    finally:
        pool.close()
    lst = os.path.join(sdir, "concat.txt")
    with open(lst, "w") as fh:
        for p in keep:
            fh.write(f"file '{p}'\n")
    out = out or film_dir(film, "out", f"{film}_master{_sfx(scale)}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", out], check=True)
    print(f"wrote {out}", flush=True)
    return out


# ----------------------------------------------------------------------------- QA images
def _sheet(arrs, labels, scale, cols, out):
    from PIL import Image, ImageDraw
    w, h = int(round(W * scale)), int(round(H * scale))
    rows = math.ceil(len(arrs) / cols)
    sheet = Image.new("RGB", (cols * (w + 8) + 8, rows * (h + 30) + 8), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for k, (arr, lab) in enumerate(zip(arrs, labels)):
        r, c = divmod(k, cols)
        x, y = 8 + c * (w + 8), 8 + r * (h + 30)
        sheet.paste(Image.fromarray(arr[..., [2, 1, 0]]), (x, y))
        d.text((x + 4, y + h + 6), lab, fill=(230, 230, 230))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    return out


def _render_many(jobs, workers):
    pool = _Pool(_workers(workers))
    try:
        bufs = list(pool.imap(_job, jobs))
    finally:
        pool.close()
    out = []
    for (kind, film, key, t, scale), b in zip(jobs, bufs):
        w, h = int(round(W * scale)), int(round(H * scale))
        out.append(np.frombuffer(b, np.uint8).reshape(h, w, 4))
    return out


def contact_sheet(film, sid, n=12, scale=0.25, cols=6, out=None, times=None, workers=None):
    """Grid of frames with time labels (QA only - labels never enter the film)."""
    T = SceneTiming(film, sid)
    if times is None:
        times = [min(T.duration - 1 / FPS, (i + 0.5) * T.duration / n) for i in range(n)]
    arrs = _render_many([("scene", film, sid, t, scale) for t in times], workers)
    out = out or film_dir(film, "qa", f"{sid}_sheet.png")
    return _sheet(arrs, [f"{sid} t={t:.2f}s" for t in times], scale, cols, out)


def range_sheet(film, t0, t1, n=12, scale=0.25, cols=6, out=None, workers=None):
    times = [t0 + (i + 0.5) * (t1 - t0) / n for i in range(n)]
    arrs = _render_many([("film", film, None, t, scale) for t in times], workers)
    out = out or film_dir(film, "qa", f"range_{t0:.2f}-{t1:.2f}_sheet.png")
    return _sheet(arrs, [f"{film} {t:.2f}s {'/'.join(owner(film, t)[1:])}" for t in times], scale, cols, out)


def stills(film, sid, times, scale=0.5, outdir=None, workers=None):
    import cv2
    outdir = outdir or film_dir(film, "qa", sid)
    os.makedirs(outdir, exist_ok=True)
    arrs = _render_many([("scene", film, sid, t, scale) for t in times], workers)
    paths = []
    for t, arr in zip(times, arrs):
        p = os.path.join(outdir, f"{sid}_t{t:07.3f}.png")
        cv2.imwrite(p, arr)
        paths.append(p)
    return paths


def collect_cues(film):
    """All scenes' cues(T) on the film clock: [{t, sfx, ..., scene}]."""
    out = []
    for s in timeline(film)["scenes"]:
        mod, T = scene_module(film, s["id"])
        if mod is not None and hasattr(mod, "cues"):
            for c in mod.cues(T):
                c = dict(c)
                c["scene"] = s["id"]
                c["t"] = round(c["t"] + s["start"], 4)
                out.append(c)
    return sorted(out, key=lambda c: c["t"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="?", default="", help="scene id(s) comma-separated, or 'all'")
    ap.add_argument("--film", required=True, choices=sorted(PALETTES))
    ap.add_argument("--scale", type=float, default=None)
    ap.add_argument("--sheet", type=int, default=0, help="contact sheet with N frames")
    ap.add_argument("--times", type=str, default="", help="comma-separated scene times for PNG stills")
    ap.add_argument("--frames", type=str, default="", help="frame range a:b (scene frames)")
    ap.add_argument("--handles", action="store_true", help="also render the transition handles")
    ap.add_argument("--cut", type=str, default="", help="render the transition into this scene")
    ap.add_argument("--range", type=str, default="", help="film-time span a:b in seconds")
    ap.add_argument("--only", type=str, default="", help="with 'all': re-render segments touching these scenes")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--cues", action="store_true", help="print all scene cues on the film clock as JSON")
    ap.add_argument("--out", type=str, default="")
    ap.add_argument("--workers", type=int, default=0)
    a = ap.parse_args()
    film = a.film
    if a.cues:
        import json
        print(json.dumps(collect_cues(film), indent=1))
        return
    span = None
    if a.cut:
        s = _scene(film, a.cut)
        hin = max(s["handle_in"], 0.5)
        prev = _scene(film, s["prev"]) if s["prev"] else None
        hout = max(prev["handle_out"], 0.5) if prev else 0.5
        span = (max(0.0, s["start"] - hin - 1.0), s["start"] + hout + 1.0)
    elif a.range:
        span = tuple(float(x) for x in a.range.split(":"))
    if span:
        scale = a.scale if a.scale is not None else (0.25 if a.sheet else 0.5)
        if a.sheet:
            print(range_sheet(film, span[0], span[1], a.sheet, scale, out=a.out or None, workers=a.workers or None))
        else:
            print(render_range(film, span[0], span[1], scale, a.workers or None, a.out or None))
        return
    if a.scenes == "all":
        scale = a.scale if a.scale is not None else 1.0
        only = [x for x in a.only.split(",") if x] or None
        render_film(film, scale, a.workers or None, only, a.force, a.out or None)
        return
    sids = [x for x in a.scenes.split(",") if x]
    if not sids:
        ap.error("give scene id(s), 'all', --cut or --range")
    if a.sheet:
        for sid in sids:
            print(contact_sheet(film, sid, a.sheet, scale=a.scale if a.scale is not None else 0.25,
                                workers=a.workers or None))
        return
    if a.times:
        ts = [float(x) for x in a.times.split(",")]
        for sid in sids:
            for p in stills(film, sid, ts, scale=a.scale if a.scale is not None else 0.5, workers=a.workers or None):
                print(p)
        return
    fr = tuple(int(x) for x in a.frames.split(":")) if a.frames else None
    scale = a.scale if a.scale is not None else 1.0
    for sid in sids:
        render_scene_video(film, sid, scale, a.workers or None, a.handles, fr, a.out or None)


if __name__ == "__main__":
    main()
