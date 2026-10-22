"""RED sound: shared helpers - paths, the film clock, word anchors, acoustic spaces, cache.

Film clock: N = frames / fps * 48000 samples (154.0 s -> 7 392 000). Times are film seconds
unless a name says otherwise. Word anchors come straight from the locked timeline.json:

    A(5, 'quieter')        film time of 'quieter' in narration line 5 (34.391)
    S('s03', 10.4)         film time of scene-local 10.4 s in s03
    END('s03')             film time of the end of s03

Spaces: outdoor winter acoustics the shared library does not have (snow is a strong absorber:
short, dark tails; trunks give dense, diffuse early reflections; the valley gives a late,
dark slap). make_space_ir() follows audio.dsp.make_ir's recipe with this film's specs.
"""
from __future__ import annotations

import functools
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILM_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(FILM_DIR))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from audio import dsp  # noqa: E402
from audio.dsp import SR, n_of  # noqa: E402

OUT = os.path.join(FILM_DIR, "out")
CACHE_DIR = os.path.join(OUT, "cache")
VO_WAV = os.path.join(HERE, "vo", "narration_full.wav")
VO_FLAC = os.path.join(HERE, "vo", "narration_full.flac")
TL_PATH = os.path.join(FILM_DIR, "timeline", "timeline.json")

with open(TL_PATH) as _fh:
    TL = json.load(_fh)
FPS = TL["fps"]
FRAMES = TL["frames"]
N = int(round(FRAMES * SR / FPS))
DURATION = N / SR
SCENES = {s["id"]: s for s in TL["scenes"]}
SCENE_IDS = [s["id"] for s in TL["scenes"]]
VO = {v["n"]: v for v in TL["vo"]}


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def A(line, word, k=0):
    """Film time (s) of the k-th occurrence of `word` in narration line `line`."""
    hits = [w for w in VO[line]["words"] if norm(w["w"]) == norm(word)]
    if not hits:
        raise KeyError(f"word {word!r} not in line {line}: {VO[line]['text']}")
    return hits[min(k, len(hits) - 1)]["t0"]


def A_end(line, word, k=0):
    hits = [w for w in VO[line]["words"] if norm(w["w"]) == norm(word)]
    return hits[min(k, len(hits) - 1)]["t1"]


def S(sid, t=0.0):
    """Film time of scene-local time t."""
    return SCENES[sid]["start"] + t


def END(sid):
    return SCENES[sid]["start"] + SCENES[sid]["duration"]


def scene_at(g):
    sid = SCENE_IDS[0]
    for s in TL["scenes"]:
        if s["start"] <= g + 1e-9:
            sid = s["id"]
    return sid


def word_spans():
    """[(t0, t1)] of every narration word on the film clock."""
    return [(w["t0"], w["t1"]) for v in TL["vo"] for w in v["words"]]


# ============================================================================ small DSP helpers
def place(dst, x, t, gain=1.0, sr=SR):
    """Add x into dst at time t (s); stereo/mono aware."""
    return dsp.mix_into(dst, x, int(round(t * sr)), gain)


def pan_curve(x, pans):
    """Equal-power pan of a mono signal by a per-sample pan array (-1..1) -> (n, 2)."""
    x = np.asarray(x, dtype=np.float64)
    p = np.clip(np.broadcast_to(pans, x.shape), -1, 1)
    th = (p + 1.0) * np.pi / 4.0
    return np.stack([x * np.cos(th), x * np.sin(th)], axis=1)


def stereo_pair(x_left, x_right):
    return np.stack([x_left, x_right], axis=1)


def env_pts(points, n, sr=SR):
    """Piecewise-linear envelope from [(t, v)] (s)."""
    return dsp.env_bp(points, n, sr)


def lin_ramp(n, a, b):
    return np.linspace(a, b, max(n, 1))[:n]


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p


# ============================================================================ spaces
_SPACES = {
    # t60 (s), low mult, high mult, predelay, ER count, ER span, ER gain, LP (Hz),
    # slaps: [(delay s, gain, lp Hz)] discrete late reflections
    "snow_forest": dict(t60=0.95, lo=1.0, hi=0.35, pre=0.012, er=26, er_span=0.12, er_g=0.45, lp=4200,
                        slaps=[]),
    "dark_forest": dict(t60=1.25, lo=1.1, hi=0.3, pre=0.018, er=30, er_span=0.16, er_g=0.4, lp=3400,
                        slaps=[(0.31, 0.12, 1800)]),
    "village":     dict(t60=0.85, lo=0.95, hi=0.4, pre=0.010, er=12, er_span=0.09, er_g=0.5, lp=4800,
                        slaps=[(0.072, 0.22, 3500), (0.13, 0.12, 2600)]),
    "ridge":       dict(t60=0.6, lo=1.0, hi=0.4, pre=0.02, er=6, er_span=0.08, er_g=0.25, lp=4000,
                        slaps=[(0.55, 0.10, 1400)]),
    "valley":      dict(t60=2.4, lo=1.2, hi=0.3, pre=0.05, er=10, er_span=0.25, er_g=0.25, lp=2600,
                        slaps=[(0.42, 0.22, 1600), (0.83, 0.12, 1100)]),
    "clearing":    dict(t60=1.05, lo=1.05, hi=0.35, pre=0.014, er=20, er_span=0.13, er_g=0.4, lp=4000,
                        slaps=[(0.24, 0.10, 2200)]),
    "paper":       dict(t60=0.35, lo=1.0, hi=0.6, pre=0.003, er=8, er_span=0.02, er_g=0.5, lp=7000,
                        slaps=[]),
    "hall":        dict(t60=2.6, lo=1.25, hi=0.5, pre=0.024, er=14, er_span=0.09, er_g=0.30, lp=6500,
                        slaps=[]),
    "chapel":      dict(t60=3.6, lo=1.3, hi=0.45, pre=0.03, er=16, er_span=0.12, er_g=0.28, lp=5500,
                        slaps=[]),
    "box":         dict(t60=0.22, lo=1.0, hi=0.7, pre=0.001, er=8, er_span=0.008, er_g=0.6, lp=9000,
                        slaps=[]),
}
SPACE_KINDS = tuple(_SPACES)


@functools.lru_cache(maxsize=32)
def make_space_ir(kind, seed=0):
    """Stereo IR (unit energy per channel) for one of this film's spaces (see _SPACES)."""
    sp = _SPACES[kind]
    rng = np.random.default_rng(dsp.stable_seed("red-ir", kind, seed))
    t60 = sp["t60"]
    length = min(6.0, t60 * 1.3 + sp["pre"] + 0.08 + (max([s[0] for s in sp["slaps"]]) if sp["slaps"] else 0.0))
    n = n_of(length)
    t = dsp.t_axis(n)
    ir = np.zeros((n, 2))
    for ch in range(2):
        nz = rng.standard_normal(n)
        lo = dsp.sos(nz, "lowpass", 400.0, 2)
        hi = dsp.sos(nz, "highpass", 3000.0, 2)
        mid = nz - lo - hi
        tail = (lo * np.power(10.0, -3.0 * t / (t60 * sp["lo"]))
                + mid * np.power(10.0, -3.0 * t / t60)
                + hi * np.power(10.0, -3.0 * t / (t60 * sp["hi"])))
        tail *= 1.0 - np.exp(-t / max(0.004, 0.07 * t60))
        tail = dsp.onepole_lp(tail, sp["lp"])
        tail /= max(dsp.EPS, np.sqrt(np.sum(tail ** 2)))
        er = np.zeros(n)
        if sp["er"]:
            times = np.sort(rng.uniform(0.0015, sp["er_span"], sp["er"]))
            gains = sp["er_g"] * rng.uniform(0.3, 1.0, sp["er"]) * np.exp(-times / max(sp["er_span"], 1e-3))
            gains *= rng.choice([-1.0, 1.0], sp["er"])
            for tt, gg in zip(times, gains):
                i = n_of(tt)
                if i < n:
                    er[i] += gg
            er = dsp.onepole_lp(er, sp["lp"] * 0.8)
            e = np.sqrt(np.sum(er ** 2))
            if e > 0:
                er *= 0.55 / e
        for (d, g, lp) in sp["slaps"]:
            i = n_of(d * (1.0 + 0.03 * (ch - 0.5)))
            if i < n:
                sl = np.zeros(n)
                sl[i] = g * 3.0
                sl = dsp.sos(sl, "lowpass", lp, 2)
                # a smeared slap: diffuse it a little
                k = n_of(0.03)
                v = rng.standard_normal(k) * np.exp(-np.arange(k) / (0.008 * SR))
                er += np.convolve(sl, v / np.sqrt(np.sum(v ** 2)))[:n] * 0.6
        ch_ir = tail + er
        pre = n_of(sp["pre"])
        ch_ir = np.concatenate([np.zeros(pre), ch_ir])[:n]
        ramp = min(n, n_of(0.002))
        ch_ir[:ramp] *= np.linspace(0, 1, ramp)
        ch_ir = dsp.fade(ch_ir, 0.0, min(0.25, length * 0.2))
        ir[:, ch] = ch_ir / max(dsp.EPS, np.sqrt(np.sum(ch_ir ** 2)))
    return ir


def space(x, kind, wet_db=-12.0, dry=1.0, keep_len=False):
    """Dry + convolution wet in one of the film's spaces (stereo out, tail kept unless keep_len)."""
    x = np.asarray(x, dtype=np.float64)
    ir = make_space_ir(kind)
    src = x.mean(axis=1) if x.ndim == 2 else x
    wet = dsp.convolve(src, ir) * dsp.db2lin(wet_db)
    n = len(x) if keep_len else len(wet)
    out = np.zeros((n, 2))
    out[:len(x)] += dsp.to_stereo(x)[:n] * dry
    out += wet[:n]
    return out


def sparse_convolve(x, ir, wet_db=0.0, thresh=1e-7, gap=1.5):
    """Convolve only the active regions of a long send (FFT per region, tails kept)."""
    x = np.asarray(x, dtype=np.float64)
    act = (np.max(np.abs(x), axis=1) if x.ndim == 2 else np.abs(x)) > thresh
    out = np.zeros((len(x), 2))
    idx = np.nonzero(act)[0]
    if len(idx) == 0:
        return out
    brk = np.nonzero(np.diff(idx) > gap * SR)[0]
    starts = np.concatenate([[idx[0]], idx[brk + 1]])
    ends = np.concatenate([idx[brk], [idx[-1]]])
    g = dsp.db2lin(wet_db)
    for a, b in zip(starts, ends):
        seg = x[a:b + 1]
        seg = seg.mean(axis=1) if seg.ndim == 2 else seg
        wet = dsp.convolve(seg, ir) * g
        dsp.mix_into(out, wet, a)
    return out


# ============================================================================ cache
def _src_hash(paths):
    h = hashlib.sha1()
    for p in paths:
        with open(p, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:16]


def source_key(*module_files, extra=""):
    """Hash of the given source files + the shared library + the timeline (+ extra)."""
    base = [os.path.join(ROOT, "audio", "dsp.py"), os.path.join(ROOT, "audio", "sfx.py"), TL_PATH,
            os.path.join(HERE, "common.py")]
    files = base + [f if os.path.isabs(f) else os.path.join(HERE, f) for f in module_files]
    return _src_hash(files) + (hashlib.sha1(extra.encode()).hexdigest()[:8] if extra else "")


def cache_load(name, key):
    p = os.path.join(CACHE_DIR, f"{name}_{key}.npz")
    if os.path.exists(p):
        try:
            d = np.load(p, allow_pickle=False)
            info = json.loads(str(d["info"])) if "info" in d else {}
            return d["x"], info
        except Exception:  # noqa: BLE001
            return None
    return None


def cache_save(name, key, x, info=None):
    ensure_dir(CACHE_DIR)
    # drop older entries of the same name
    for f in os.listdir(CACHE_DIR):
        if f.startswith(name + "_") and f.endswith(".npz"):
            try:
                os.remove(os.path.join(CACHE_DIR, f))
            except OSError:
                pass
    p = os.path.join(CACHE_DIR, f"{name}_{key}.npz")
    np.savez(p, x=np.asarray(x, dtype=np.float32), info=json.dumps(info or {}, default=str))
    return p
