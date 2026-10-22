"""RED: this film's SFX catalog, built on audio.dsp (and a few audio.sfx helpers).

    render(name, dur=None, params=None, seed=0)       -> float32 (n, 2) at 48 kHz
    render_sync(name, dur=None, params=None, seed=0)  -> (float32 (n, 2), sync_s)

`sync_s` is where the sound's sync point (impact, slam, landing) sits inside the rendered
buffer: a cue at film time t is placed at t - sync_s, so the slam lands ON the word.
Names prefixed 'lib:' render from the shared catalog (e.g. 'lib:whip'), sync 0.

Level convention (same as the shared library): every sound renders at REF_LUFS = -16, one-shots
by their loudest 400 ms, sustained sounds by integrated loudness, never above a true-peak cap
(-4 dBTP one-shots, -1 dBTP designed hits / sustained). Physical level differences (a child's
step vs the wolf's paw, a far door vs a near one) are applied after the cap. Cue gain_db then
places the sound in the mix.

Design notes
  snow ......... granular micro-fracture model: a Poisson train of ice-bond breaks whose density
                 follows the load curve of the foot (heel strike, roll), band-limited by grain
                 size; + low compaction 'whump' + (cold snow) stick-slip squeak. Deep snow adds the
                 leg's plunge swish and the powder spray.
  voices ....... jittered glottal pulse trains (period jitter, shimmer, period-doubling for
                 roughness) through formant banks; breath = turbulence noise through the same
                 tract. Child (formants high), wolf (big tract, low f0 55-90 Hz growl).
  chitin ....... dry hollow plates: sub-ms transients + short inharmonic modes; stridulation =
                 a file-and-scraper click train whose rate sweeps into a buzz.
  thread ....... silk cable under load: slow stick-slip creak + a bowed-wire tension tone that
                 glides down as the thread pays out.
  fire ......... turbulent roar (brown, surging) + flame flutter (8-16 Hz AM) + crackle (resonant
                 pops) + hiss; whooshes sweep a band upward and pan along the web.
  wood/metal ... modal impacts (plank modes, iron latch), stick-slip hinges.
"""
from __future__ import annotations

import math

import numpy as np

from .common import SR, place, pan_curve  # noqa: F401  (also sets sys.path)
from audio import dsp
from audio import sfx as libsfx
from audio.dsp import (TWO_PI, ar_env, bandpass, brown, crackle, db2lin, exp_env, fade, n_of, onepole_lp,
                       pink, saturate, smooth_noise, sos, t_axis, to_stereo, tv_bandpass, tv_lowpass, white)
from audio.sfx import _burst, _click, _drop, _hit, _thump  # shared helpers (read-only use)

REF_LUFS = -16.0
PEAK_CAP_DBTP = -4.0
HIT_PEAK_CAP_DBTP = -1.0
SUSTAINED_PEAK_CAP_DBTP = -1.0
_REG: dict = {}
_CACHE: dict = {}


class Out:
    """A rendered sound with its physical level offset (dB, applied after the cap) and sync point."""
    __slots__ = ("x", "db", "sync")

    def __init__(self, x, db=0.0, sync=0.0):
        self.x, self.db, self.sync = x, float(db), float(sync)


def _sfx(name, kind="oneshot", norm="max", default_dur=None, space=1.0, hit=False, trim=0.0, family=None):
    """Register a sound. space: send factor for the mixer's scene reverb (0 = carries its own
    acoustics). hit: designed hit (lightly ducked). family: for matching scene cue hints."""
    def deco(fn):
        _REG[name] = dict(fn=fn, kind=kind, norm=norm, default_dur=default_dur, space=space, hit=hit,
                          trim=trim, family=family or name, name=name, doc=(fn.__doc__ or "").strip())
        return fn
    return deco


def names():
    return sorted(_REG)


def exists(name):
    return name in _REG or (name.startswith("lib:") and libsfx.exists(name[4:]))


def spec(name):
    if name.startswith("lib:"):
        s = libsfx.spec(name[4:])
        return dict(kind=s["kind"], norm=s["norm"], default_dur=s["default_dur"], space=s["space"], hit=s["hit"],
                    trim=s["trim"], family=name, name=name, doc=(s["fn"].__doc__ or "").strip())
    return _REG[name]


def _measure(x, mode):
    if mode == "int" and len(x) >= n_of(0.8):
        v = dsp.loudness_integrated(x)
        if np.isfinite(v):
            return v
    y = x if len(x) >= n_of(0.4) else dsp.pad_to(x, n_of(0.4))
    _, lk = dsp.loudness_curve(y, win=0.4, hop=0.05)
    return float(np.max(lk)) if len(lk) else -70.0


def render_sync(name, dur=None, params=None, seed=0):
    """Render -> (float32 (n, 2), sync seconds). See module docstring."""
    if name.startswith("lib:"):
        return libsfx.render(name[4:], dur=dur, params=params, seed=seed), 0.0
    if name not in _REG:
        raise KeyError(f"unknown RED SFX {name!r}")
    sp = _REG[name]
    p = dict(params or {})
    key = (name, None if dur is None else round(float(dur), 4), tuple(sorted((k, str(v)) for k, v in p.items())),
           int(seed))
    if key in _CACHE:
        x, s = _CACHE[key]
        return x.copy(), s
    rng = np.random.default_rng(dsp.stable_seed("red-sfx", name, seed))
    d = dur if (dur is not None and sp["kind"] == "sustained") else sp["default_dur"]
    if sp["kind"] == "sustained":
        d = max(0.05, float(d if d is not None else 3.0))
    res = sp["fn"](d, p, rng)
    if not isinstance(res, Out):
        res = Out(res)
    x = to_stereo(np.asarray(res.x, dtype=np.float64))
    x = sos(x, "highpass", 18.0, 2)
    if sp["kind"] == "sustained":
        x = dsp.pad_to(x, n_of(d))
    else:
        x = fade(x, 0.0002, 0.015, shape="lin")
    lvl = _measure(x, sp["norm"])
    if np.isfinite(lvl) and lvl > -120:
        x = x * db2lin(REF_LUFS + sp["trim"] - lvl)
    cap = (HIT_PEAK_CAP_DBTP if sp["hit"] else PEAK_CAP_DBTP) if sp["kind"] == "oneshot" else SUSTAINED_PEAK_CAP_DBTP
    tp = dsp.true_peak_db(x)
    if tp > cap:
        x = x * db2lin(cap - tp)
    x = x * db2lin(res.db)
    if sp["kind"] == "oneshot":
        if dur is not None and dur > 0 and n_of(dur) < len(x):
            x = fade(x[:n_of(dur)], 0.0, min(0.03, dur / 3))
    else:
        x = fade(x, 0.002, 0.004)
    out = x.astype(np.float32)
    if len(_CACHE) > 600:
        _CACHE.clear()
    _CACHE[key] = (out, res.sync)
    return out.copy(), res.sync


def render(name, dur=None, params=None, seed=0):
    return render_sync(name, dur, params, seed)[0]


# ============================================================================ helpers
def _N(t):
    return max(1, n_of(t))


def _pk(x):
    """Peak-normalise a layer (so layer gains below read as relative dB)."""
    m = np.max(np.abs(x)) if len(x) else 0.0
    return x / m if m > 1e-12 else x


def _g(db):
    return float(db2lin(db))


def _clip01(v):
    return float(np.clip(v, 0.0, 1.0))


def _grains(n, rng, rate, env, spread=0.8):
    """Sparse impulse signal: Poisson events at rate*env per second, log-normal amplitudes."""
    p = np.clip(rate * env / SR, 0.0, 0.8)
    hit = rng.random(n) < p
    amps = np.exp(rng.normal(0.0, spread, n)) * rng.choice([-1.0, 1.0], n)
    return np.where(hit, amps, 0.0)


def _crunch(n, rng, env, rate=4000.0, lo=700.0, hi=7500.0, res=(), spread=0.8, load=0.6):
    """Granular snow crunch (see module docstring)."""
    imp = _grains(n, rng, rate, env, spread) * np.power(np.clip(env, 0, None), load)
    x = bandpass(imp, lo, hi, 2)
    for f, q, g in res:
        x = x + g * dsp.biquad(imp, "bandpass", f, q)
    return x


def _env_hr(t, a, L, roll, roll_amt, roll_w):
    """Heel + roll load curve for a foot / paw in snow."""
    e1 = np.clip(t / a, 0, 1) ** 1.5 * np.exp(-np.maximum(t - a, 0) / (L * 0.30))
    e2 = roll_amt * np.exp(-0.5 * ((t - roll) / roll_w) ** 2)
    return np.clip(e1 + e2, 0, 1.3)


def _swish(n, rng, f0, f1, q=0.9, color="pink", curve=1.0):
    """Band of noise sweeping f0 -> f1 (log), unit-peak envelope applied by caller."""
    u = np.linspace(0, 1, n) ** curve
    fc = f0 * (f1 / f0) ** u
    src = pink(n, rng) if color == "pink" else white(n, rng)
    return tv_bandpass(src, fc, q=q, block=64)


def _pulses(n, f0, rng, jitter=0.02, shimmer=0.15, double=0.0, sr=SR):
    """Glottal impulse train: per-sample f0 array, random period jitter, amplitude shimmer,
    period-doubling (alternate pulses weaker by `double`) for vocal roughness. Spectral tilt
    -12 dB/oct above ~f0 (two one-poles)."""
    f = np.full(n, float(f0)) if np.ndim(f0) == 0 else np.asarray(f0, dtype=np.float64)
    out = np.zeros(n)
    t = 0.0
    k = 0
    while t < n:
        i = int(t)
        fi = max(20.0, f[min(i, n - 1)])
        a = math.exp(rng.normal(0, shimmer))
        if double and k % 2:
            a *= (1.0 - double)
        out[i] += a
        t += sr / fi * (1.0 + jitter * rng.normal())
        k += 1
    fm = float(np.median(f))
    out = onepole_lp(out, fm * 1.2, sr)
    out = onepole_lp(out, fm * 2.5, sr)
    return out - onepole_lp(out, 30.0, sr)


def _formants(x, forms, sr=SR):
    """Static parallel formant bank: [(f, bw, gain_db)]."""
    y = np.zeros_like(np.asarray(x, dtype=np.float64))
    for f, bw, g in forms:
        if f < 0.47 * sr:
            y += db2lin(g) * dsp.biquad(x, "bandpass", f, max(0.5, f / bw), sr=sr)
    return y


def _tv_formants(x, tracks, sr=SR, block=64):
    """Time-varying formant bank: [(f_array, bw, gain_db)] (f arrays per sample)."""
    y = np.zeros_like(np.asarray(x, dtype=np.float64))
    for f, bw, g in tracks:
        q = np.maximum(0.5, np.asarray(f) / bw)
        y += db2lin(g) * tv_bandpass(x, f, q=q, sr=sr, block=block)
    return y


def _wide(x, rng, amount=0.5):
    return dsp.decorrelate(np.asarray(x, dtype=np.float64), rng, amount=amount)


def _spray(n, rng, t60=0.25, lo=2500.0, hi=11000.0, attack=0.004):
    """Fine powder / snow spray hiss (sparse high grains + air)."""
    e = ar_env(n, attack, t60)
    g = _grains(n, rng, 2500, e, 1.0) * e
    return bandpass(g, lo, hi, 2) * 0.8 + bandpass(white(n, rng), lo, hi, 2) * e * 0.12


def _whump(n, rng, lp=260.0, tau=0.05, attack=0.006):
    t = t_axis(n)
    return sos(brown(n, rng), "lowpass", lp, 2) * np.clip(t / attack, 0, 1) * np.exp(-t / tau)


# ============================================================================ the girl
@_sfx("snow_step", family="step_girl")
def _snow_step(dur, p, rng):
    """A child's footstep in cold snow: heel strike + roll (granular micro-fracture crunch),
    a small compaction whump, sometimes the squeak of cold snow. weight 0..1 (0.25 child,
    0.7 adult) · pace walk/run/slow/back · depth 0 (packed path) .. 1 (powder)."""
    w = _clip01(p.get("weight", 0.25))
    pace = p.get("pace", "walk")
    depth = _clip01(p.get("depth", 0.2))
    run = pace == "run"
    slow = pace in ("slow", "back")
    L = (0.15 if run else 0.30 if slow else 0.23) * (1 + 0.5 * depth) * (0.85 + 0.35 * w) * rng.uniform(0.88, 1.12)
    n = _N(L + 0.3)
    t = t_axis(n)
    a = 0.008 if run else 0.016
    if pace == "back":           # toe first, heel second
        a = 0.03
    env = _env_hr(t, a, L, L * rng.uniform(0.5, 0.65), rng.uniform(0.4, 0.75) * (0.6 if run else 1.0), L * 0.14)
    rate = (3200 + 4200 * w) * (1.25 if run else 1.0)
    lo = max(250.0, 780 - 380 * w - 250 * depth)
    hi = 8200 - 2200 * depth - 1500 * w
    res = [(rng.uniform(1300, 2100), 2.2, 0.5), (rng.uniform(2900, 4300), 2.8, 0.35)]
    cr = _pk(_crunch(n, rng, env, rate, lo, hi, res))
    wh = _pk(_whump(n, rng, 230 + 150 * (1 - depth), 0.03 + 0.04 * w + 0.04 * depth))
    th = _pk(_thump(n, 125 - 35 * w, 64 - 14 * w, 0.010, 0.045 + 0.06 * w))
    x = cr + wh * _g(-11 + 8 * w + 3 * depth) + th * _g(-17 + 11 * w)
    if rng.uniform() < float(p.get("squeak", 0.35)) and not run:
        m = _N(L * 0.55)
        sq = dsp.friction(m, rng.uniform(650, 1150) * np.linspace(1.0, 0.82, m), rng, jitter=0.22,
                          body=[(rng.uniform(1500, 2100), 6, 1.0), (rng.uniform(3000, 3700), 8, 0.45)])
        place(x, _pk(sq) * np.hanning(m), L * 0.28, _g(-15))
    if run:
        place(x, _pk(_spray(_N(0.25), rng, 0.12)), 0.01, _g(-10))
    level = -9.0 * (0.7 - w) + (2.0 if run else 0.0) + (-2.5 if slow else 0.0)
    return Out(x, level + rng.uniform(-1.2, 1.2), 0.0)


@_sfx("snow_wade", family="step_girl")
def _snow_wade(dur, p, rng):
    """Wading through deep snow: the leg's plunge (rising swish), the deep crunch and whump at
    the bottom (sync), the pull-out and the powder that slides back. weight 0..1."""
    w = _clip01(p.get("weight", 0.3))
    n = _N(0.95)
    t = t_axis(n)
    sync = rng.uniform(0.11, 0.15)
    out = np.zeros(n)
    m = _N(sync + 0.02)
    pl = _swish(m, rng, 380, 1500, q=0.8) * np.linspace(0, 1, m) ** 1.6
    place(out, _pk(pl), 0.0, _g(-7))
    L = rng.uniform(0.2, 0.28) * (0.9 + 0.3 * w)
    ns = _N(L + 0.15)
    ts = t_axis(ns)
    env = _env_hr(ts, 0.02, L, L * 0.55, 0.6, L * 0.2)
    cr = _pk(_crunch(ns, rng, env, 3000 + 2500 * w, 380, 5200, [(rng.uniform(900, 1500), 2.0, 0.6)]))
    place(out, cr, sync, 1.0)
    place(out, _pk(_whump(_N(0.4), rng, 240, 0.07 + 0.04 * w)), sync, _g(-4 + 3 * w))
    place(out, _pk(_thump(_N(0.3), 105, 55, 0.012, 0.08)), sync, _g(-12 + 6 * w))
    po = _swish(_N(0.25), rng, 1400, 520, q=0.8) * np.hanning(_N(0.25))
    place(out, _pk(po), sync + L * 0.9, _g(-11))
    place(out, _pk(_spray(_N(0.5), rng, 0.3, 2000, 9000)), sync + 0.02, _g(-13))
    return Out(out, -6.0 * (0.7 - w) + rng.uniform(-1, 1), sync)


@_sfx("snow_scramble", family="scramble")
def _snow_scramble(dur, p, rng):
    """Scrambling on hands and knees in deep snow: fast irregular crunches, cloth, powder."""
    n = _N(1.7)
    out = np.zeros(n)
    tt = 0.0
    k = 0
    while tt < 1.35:
        L = rng.uniform(0.06, 0.16)
        m = _N(L + 0.1)
        e = _env_hr(t_axis(m), 0.006, L, L * 0.5, 0.5, L * 0.2)
        c = _pk(_crunch(m, rng, e, rng.uniform(3000, 6000), rng.uniform(400, 700), 7000))
        place(out, c, tt, _g(rng.uniform(-9, 0) - 4 * (tt > 1.0)))
        if rng.uniform() < 0.4:
            place(out, _pk(_whump(_N(0.2), rng, 260, 0.04)), tt, _g(-8))
        tt += rng.uniform(0.07, 0.17)
        k += 1
    ru = bandpass(pink(n, rng), 400, 4000, 2) * (0.5 + 0.5 * np.abs(smooth_noise(n, 14, rng)))
    ru *= dsp.env_bp([(0, 0), (0.05, 1), (1.3, 0.7), (1.65, 0)], n)
    out += _pk(ru) * _g(-14)
    out += _pk(_spray(n, rng, 1.0, 2500, 9000)) * _g(-18)
    return Out(out, -3.0, 0.0)


@_sfx("snow_skid", family="skid")
def _snow_skid(dur, p, rng):
    """Feet skidding to a stop in snow: plowing friction swish + continuous crunch, ending in a
    planted crunch. who: girl | wolf (heavier, lower, four paws)."""
    wolf = p.get("who", "girl") == "wolf"
    L = rng.uniform(0.5, 0.65) * (1.25 if wolf else 1.0)
    n = _N(L + 0.5)
    t = t_axis(n)
    env = np.clip(t / 0.02, 0, 1) * np.clip(1.0 - t / L, 0, 1) ** 0.6
    out = np.zeros(n)
    lo, hi = (260, 5000) if wolf else (500, 7500)
    for k in range(4 if wolf else 2):
        dly = rng.uniform(0.0, 0.06) + (0.05 * k if wolf else 0.08 * k)
        sh = _swish(n, rng, 2600 if not wolf else 1600, 700 if not wolf else 380, q=0.7) * env
        cr = _crunch(n, rng, env, 5500 if not wolf else 4000, lo, hi, [(rng.uniform(900, 1700), 2, 0.5)])
        place(out, _pk(sh) * _g(-6) + _pk(cr), dly, _g(-2 * k))
    m = _N(0.3)
    stop = _pk(_crunch(m, rng, _env_hr(t_axis(m), 0.01, 0.12, 0.06, 0.6, 0.03), 7000, lo, hi))
    place(out, stop, L, _g(-1))
    place(out, _pk(_whump(_N(0.3), rng, 240, 0.06)), L, _g(-6 if wolf else -10))
    place(out, _pk(_spray(_N(0.6), rng, 0.4)), 0.05, _g(-12))
    return Out(out, 2.0 if wolf else -1.0, 0.0)


@_sfx("fall_deep_snow", family="fall", hit=True)
def _fall_deep_snow(dur, p, rng):
    """A child falling face-down into deep powder: cloak whoosh, the WHUMPF (sync), a punch of
    crunch, the knocked-out breath, spray falling back, settling powder."""
    n = _N(2.3)
    out = np.zeros(n)
    sync = 0.16
    m = _N(sync)
    cl = _swish(m, rng, 500, 2600, q=0.8) * np.linspace(0, 1, m) ** 2
    place(out, _pk(cl), 0.0, _g(-9))
    place(out, _pk(_whump(_N(0.6), rng, 300, 0.11, 0.012)), sync, 1.0)
    place(out, _pk(_thump(_N(0.6), 90, 42, 0.03, 0.22)), sync, _g(-4))
    ns = _N(0.35)
    e = _env_hr(t_axis(ns), 0.01, 0.18, 0.1, 0.8, 0.05)
    place(out, _pk(_crunch(ns, rng, e, 9000, 280, 6500, [(rng.uniform(800, 1300), 1.8, 0.7)])), sync + 0.004, _g(-3))
    nb = _N(0.3)
    br = _formants(white(nb, rng), [(900, 250, 0), (1650, 300, -4), (3200, 400, -10)]) * ar_env(nb, 0.01, 0.22)
    place(out, _pk(br), sync + 0.02, _g(-15))
    place(out, _pk(_spray(_N(1.0), rng, 0.7, 1800, 9000, 0.02)), sync + 0.03, _g(-9))
    m2 = _N(1.4)
    set_ = _grains(m2, rng, 160, np.exp(-t_axis(m2) / 0.7), 0.9)
    set_ = bandpass(set_, 900, 7000, 2) + 0.4 * bandpass(white(m2, rng), 2500, 8000, 2) * np.exp(-t_axis(m2) / 0.5) * 0.05
    place(out, _pk(set_), sync + 0.35, _g(-17))
    st = _wide(out, rng, 0.25)
    return Out(st, 1.0, sync)


@_sfx("girl_breath_run", kind="sustained", norm="int", default_dur=6.0, space=0.6, family="breath_girl")
def _girl_breath_run(dur, p, rng):
    """A seven-year-old's breathing while running: quick ragged in/out cycles (child tract:
    high formants), exhales partly voiced ('huh'), occasional catch. rate (cycles/s, ~2.4),
    intensity 0..1, voiced 0..1."""
    rate = float(p.get("rate", 2.4))
    inten = _clip01(p.get("intensity", 0.7))
    voiced = _clip01(p.get("voiced", 0.35))
    n = _N(dur)
    t = t_axis(n)
    e_in = np.zeros(n)
    e_out = np.zeros(n)
    e_v = np.zeros(n)
    tt = rng.uniform(0.0, 0.15)
    while tt < dur:
        per = 1.0 / rate * rng.uniform(0.85, 1.18)
        li = per * rng.uniform(0.32, 0.42)
        lo_ = per * rng.uniform(0.42, 0.55)
        a, b = n_of(tt), min(n, n_of(tt + li))
        if b > a:
            u = np.linspace(0, 1, b - a)
            e_in[a:b] = np.maximum(e_in[a:b], (np.sin(np.pi * u) ** 1.2) * rng.uniform(0.5, 0.9))
        c = n_of(tt + li + per * 0.03)
        d = min(n, c + n_of(lo_))
        if d > c:
            u = np.linspace(0, 1, d - c)
            amp = rng.uniform(0.75, 1.0)
            shape = np.clip(u / 0.12, 0, 1) * np.exp(-np.maximum(u - 0.12, 0) / 0.45)
            e_out[c:d] = np.maximum(e_out[c:d], shape * amp)
            if rng.uniform() < voiced:
                e_v[c:d] = np.maximum(e_v[c:d], shape * amp * rng.uniform(0.4, 1.0))
        tt += per
    sm = lambda e: onepole_lp(e, 40.0)  # noqa: E731
    e_in, e_out, e_v = sm(e_in), sm(e_out), sm(e_v)
    nz = white(n, rng)
    inh = _formants(nz, [(1300, 350, -2), (2700, 500, 0), (4300, 700, -2), (6500, 1500, -6)])
    exh = _formants(white(n, rng), [(1050, 260, 0), (1900, 330, -3), (3400, 450, -8), (5200, 900, -14)])
    f0 = 330 * (1 + 0.04 * smooth_noise(n, 2.0, rng)) * (1 + 0.05 * e_out)
    vs = _formants(_pulses(n, f0, rng, jitter=0.03, shimmer=0.2), [(1000, 140, 0), (1850, 180, -4), (3300, 260, -10)])
    x = (_pk(inh) * e_in * _g(-6) + _pk(exh) * e_out + _pk(vs) * e_v * _g(-9 + 4 * inten)) * (0.55 + 0.45 * inten)
    x *= 1 + 0.15 * smooth_noise(n, 1.0, rng)
    return Out(_wide(x, rng, 0.2), 0.0, 0.0)


@_sfx("girl_gasp", family="breath_girl")
def _girl_gasp(dur, p, rng):
    """A sharp frightened inhale ('hhk!'), a child's voice catching."""
    n = _N(0.6)
    t = t_axis(n)
    L = rng.uniform(0.18, 0.26)
    e = np.clip(t / 0.025, 0, 1) * np.exp(-np.maximum(t - 0.04, 0) / (L * 0.5))
    inh = _formants(white(n, rng), [(1400, 300, 0), (2900, 400, -1), (4500, 700, -3)]) * e
    f0 = 420 * (1 + 0.25 * np.exp(-t / 0.08))
    v = _formants(_pulses(n, f0, rng, 0.04, 0.2), [(1100, 150, 0), (2200, 200, -5)]) * e * (t < 0.08)
    return Out(_pk(inh) + _pk(v) * _g(-14), -2.0, 0.0)


@_sfx("cloth_rustle", family="cloth", space=0.8)
def _cloth_rustle(dur, p, rng):
    """Wool cloak / dress movement: soft broadband rustle with irregular hand-motion swells.
    size 0..1."""
    s = _clip01(p.get("size", 0.5))
    L = 0.35 + 0.8 * s
    n = _N(L + 0.1)
    t = t_axis(n)
    mot = np.abs(smooth_noise(n, 9.0, rng)) ** 1.5
    env = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.8 * (0.3 + 0.7 * mot)
    x = bandpass(pink(n, rng), 280, 4200, 2) * env
    x += 0.35 * bandpass(_grains(n, rng, 900, env, 0.7), 1500, 7000, 2)
    return Out(_wide(x, rng, 0.3), -6.0 + 4 * s, 0.0)


@_sfx("hood_up", family="cloth", space=0.8)
def _hood_up(dur, p, rng):
    """The hood pulled up over her head: a quick fabric swish and a soft 'fwump' as it settles."""
    n = _N(0.75)
    out = np.zeros(n)
    m = _N(0.2)
    place(out, _pk(_swish(m, rng, 700, 3200, q=0.7) * np.linspace(0, 1, m) ** 1.5), 0.0, _g(-4))
    place(out, _pk(_burst(_N(0.12), rng, 120, 1100, t60=0.08, attack=0.004)), 0.19, 1.0)
    r = bandpass(pink(_N(0.4), rng), 400, 3500, 2) * np.hanning(_N(0.4)) * (0.5 + 0.5 * np.abs(smooth_noise(_N(0.4), 15, rng)))
    place(out, _pk(r), 0.22, _g(-10))
    return Out(_wide(out, rng, 0.3), -5.0, 0.19)


@_sfx("ribbon_tie", family="cloth", space=0.8)
def _ribbon_tie(dur, p, rng):
    """Mother's hands tying the ribbon under the chin: two quick fabric pulls and a soft tug."""
    n = _N(0.8)
    out = np.zeros(n)
    for k, tt in enumerate((0.0, 0.22)):
        m = _N(0.09)
        z = dsp.friction(m, np.linspace(900, 1600, m), rng, jitter=0.4, body=[(2400, 3, 1.0), (4200, 4, 0.5)])
        z = _pk(z) * np.hanning(m) + _pk(bandpass(white(m, rng), 1500, 6000, 2)) * np.hanning(m) * 0.5
        place(out, z, tt + rng.uniform(0, 0.02), _g(-2 * k))
    place(out, _pk(_burst(_N(0.08), rng, 150, 900, t60=0.05)), 0.42, _g(-6))
    return Out(out, -9.0, 0.0)


@_sfx("basket_handle", family="basket", space=0.8)
def _basket_handle(dur, p, rng):
    """The wicker basket handed over: handle creak (willow stick-slip) + cloth cover flap."""
    n = _N(0.9)
    t = t_axis(n)
    sw = np.sin(np.pi * np.clip(t / 0.6, 0, 1)) ** 1.2
    cr = dsp.friction(n, 90 + 260 * sw, rng, jitter=0.45, body=[(620, 5, 1.0), (1350, 7, 0.7), (2600, 9, 0.4)])
    cr *= sw
    tw = _grains(n, rng, 120, sw, 0.9)
    tw = dsp.resonator_bank(tw, [900, 1900, 3300], [9, 11, 12], [1, 0.6, 0.3])
    x = _pk(cr) + _pk(tw) * _g(-6)
    place(x, _pk(_burst(_N(0.1), rng, 200, 2500, t60=0.06)), 0.45, _g(-8))
    return Out(x, -6.0, 0.0)


@_sfx("basket_creak", family="basket", space=0.8)
def _basket_creak(dur, p, rng):
    """A small wicker creak (the basket on her arm as she walks)."""
    n = _N(0.35)
    t = t_axis(n)
    sw = np.sin(np.pi * np.clip(t / 0.3, 0, 1)) ** 1.5
    cr = dsp.friction(n, 140 + 300 * sw * rng.uniform(0.7, 1.2), rng, jitter=0.5,
                      body=[(rng.uniform(600, 900), 5, 1.0), (rng.uniform(1500, 2100), 7, 0.6)])
    return Out(cr * sw, -12.0, 0.0)


@_sfx("kneel_snow", family="kneel", space=0.9)
def _kneel_snow(dur, p, rng):
    """Kneeling down into snow: two knees (soft deep crunches) + cloak settling. weight 0..1."""
    w = _clip01(p.get("weight", 0.3))
    n = _N(1.0)
    out = np.zeros(n)
    for k, tt in enumerate((0.0, rng.uniform(0.14, 0.22))):
        L = 0.16
        m = _N(L + 0.15)
        e = _env_hr(t_axis(m), 0.02, L, L * 0.6, 0.5, L * 0.2)
        place(out, _pk(_crunch(m, rng, e, 3500 + 2000 * w, 350, 5500)), tt, _g(-2 * k))
        place(out, _pk(_whump(_N(0.3), rng, 220, 0.06)), tt, _g(-7 + 3 * w))
    r = bandpass(pink(_N(0.6), rng), 300, 3000, 2) * np.hanning(_N(0.6))
    place(out, _pk(r), 0.05, _g(-12))
    return Out(out, -7.0 + 4 * w, 0.0)


@_sfx("fur_touch", family="touch", space=0.6)
def _fur_touch(dur, p, rng):
    """A small hand on the wolf's muzzle: a soft, brushy fur rustle."""
    n = _N(0.8)
    t = t_axis(n)
    e = np.sin(np.pi * np.clip(t / 0.7, 0, 1)) ** 2 * (0.6 + 0.4 * np.abs(smooth_noise(n, 7, rng)))
    x = bandpass(white(n, rng), 1800, 9000, 2) * e + 0.3 * bandpass(pink(n, rng), 300, 1500, 2) * e
    return Out(x, -10.0, 0.0)


# ============================================================================ the wolf
@_sfx("wolf_paw", family="step_wolf")
def _wolf_paw(dur, p, rng):
    """A huge wolf's paw in snow: padded thump + broad, low crunch + whump; gallop adds spray.
    pace walk|gallop · depth 0..1."""
    pace = p.get("pace", "walk")
    gal = pace == "gallop"
    depth = _clip01(p.get("depth", 0.4))
    L = (0.13 if gal else 0.22) * (1 + 0.4 * depth) * rng.uniform(0.85, 1.15)
    n = _N(L + 0.35)
    t = t_axis(n)
    env = _env_hr(t, 0.008 if gal else 0.014, L, L * 0.55, 0.45, L * 0.18)
    cr = _pk(_crunch(n, rng, env, 4200, 260, 5600 - 1200 * depth, [(rng.uniform(700, 1100), 1.8, 0.7),
                                                                    (rng.uniform(1800, 2600), 2.4, 0.4)]))
    wh = _pk(_whump(n, rng, 210, 0.05 + 0.04 * depth))
    th = _pk(_thump(n, 82, 44, 0.014, 0.1))
    pad = _pk(_burst(_N(0.05), rng, 140, 900, t60=0.03, attack=0.002))
    x = cr + wh * _g(-3) + th * _g(-7)
    place(x, pad, 0.0, _g(-6))
    if gal:
        place(x, _pk(_spray(_N(0.4), rng, 0.2, 1800, 8500)), 0.01, _g(-9))
    return Out(x, 1.5 + rng.uniform(-1.2, 1.2), 0.0)


def _wolf_tract(x, kind="breath", sr=SR):
    """Big canine vocal tract (long muzzle, nasal coupling)."""
    if kind == "growl":
        return _formants(x, [(330, 130, 0), (980, 220, -3), (2050, 300, -9), (3000, 400, -15)], sr)
    if kind == "snarl":
        return _formants(x, [(620, 200, 0), (1500, 300, -2), (2700, 450, -6), (3900, 600, -12)], sr)
    return _formants(x, [(260, 120, -3), (720, 220, 0), (1450, 320, -5), (2500, 450, -11)], sr)


@_sfx("wolf_huff", family="wolf_breath", space=0.8)
def _wolf_huff(dur, p, rng):
    """A forceful nasal exhale: nostril flutter onset, big tract, chest under it. double 0/1."""
    n = _N(1.1)
    out = np.zeros(n)
    for k in range(2 if p.get("double", 0) else 1):
        L = rng.uniform(0.28, 0.42)
        m = _N(L + 0.15)
        t = t_axis(m)
        e = np.clip(t / 0.006, 0, 1) * np.exp(-t / (L * 0.45))
        flut = 1.0 + 0.7 * np.sin(TWO_PI * rng.uniform(28, 40) * t) * np.exp(-t / 0.07)
        x = _wolf_tract(white(m, rng)) * e * flut
        ch = sos(brown(m, rng), "lowpass", 220, 2) * e
        place(out, _pk(x) + _pk(ch) * _g(-8), k * rng.uniform(0.32, 0.4), _g(-3 * k))
    return Out(out, 0.0, 0.0)


@_sfx("wolf_breath", kind="sustained", norm="int", default_dur=6.0, space=0.8, family="wolf_breath")
def _wolf_breath(dur, p, rng):
    """Slow, deep breathing of a very large animal: long inhale, heavier exhale with a faint
    chest rumble. rate (breaths/s, ~0.4), intensity 0..1."""
    rate = float(p.get("rate", 0.4))
    inten = _clip01(p.get("intensity", 0.5))
    n = _N(dur)
    ei = np.zeros(n)
    eo = np.zeros(n)
    tt = rng.uniform(0, 0.5)
    while tt < dur:
        per = rng.uniform(0.85, 1.15) / rate
        li, lo_ = per * 0.4, per * 0.48
        for (t0, L, e, amp) in ((tt, li, ei, rng.uniform(0.4, 0.6)), (tt + li + 0.04 * per, lo_, eo, rng.uniform(0.8, 1.0))):
            a, b = n_of(t0), min(n, n_of(t0 + L))
            if b > a:
                u = np.linspace(0, 1, b - a)
                e[a:b] = np.maximum(e[a:b], np.sin(np.pi * u ** 0.7) ** 1.5 * amp)
        tt += per
    nz_i = _wolf_tract(white(n, rng)) * ei
    nz_o = _wolf_tract(white(n, rng)) * eo
    rum = _formants(_pulses(n, 52 * (1 + 0.03 * smooth_noise(n, 1, rng)), rng, 0.04, 0.3), [(300, 140, 0), (900, 250, -6)]) * eo
    x = _pk(nz_i) * _g(-5) + _pk(nz_o) + _pk(rum) * _g(-16 + 8 * inten)
    return Out(_wide(x, rng, 0.25), 0.0, 0.0)


@_sfx("wolf_pant", kind="sustained", norm="int", default_dur=5.0, space=0.6, family="wolf_breath")
def _wolf_pant(dur, p, rng):
    """Running wolf: heavy rhythmic breaths locked to the gallop stride. rate (strides/s)."""
    rate = float(p.get("rate", 2.2))
    n = _N(dur)
    e = np.zeros(n)
    tt = 0.0
    while tt < dur:
        per = 1.0 / rate * rng.uniform(0.95, 1.05)
        a, b = n_of(tt), min(n, n_of(tt + per * 0.55))
        if b > a:
            u = np.linspace(0, 1, b - a)
            e[a:b] = np.maximum(e[a:b], np.clip(u / 0.15, 0, 1) * np.exp(-u / 0.4) * rng.uniform(0.7, 1.0))
        a2, b2 = b, min(n, n_of(tt + per * 0.95))
        if b2 > a2:
            u = np.linspace(0, 1, b2 - a2)
            e[a2:b2] = np.maximum(e[a2:b2], np.sin(np.pi * u) * 0.35)
        tt += per
    e = onepole_lp(e, 50.0)
    x = _wolf_tract(white(n, rng), "snarl") * 0.5 + _wolf_tract(white(n, rng))
    x = x * e
    return Out(_wide(x, rng, 0.2), 0.0, 0.0)


def _growl_core(n, rng, f0=70.0, rough=0.6, tract="growl", breath=0.25):
    t = t_axis(n)
    f = f0 * (1 + 0.05 * smooth_noise(n, 1.3, rng) + 0.02 * smooth_noise(n, 9, rng))
    src = _pulses(n, f, rng, jitter=0.03 + 0.05 * rough, shimmer=0.25 + 0.3 * rough, double=0.35 * rough)
    am = 1.0 + 0.45 * rough * np.sin(TWO_PI * np.cumsum(28 + 8 * smooth_noise(n, 2, rng)) / SR)
    v = _wolf_tract(src * am, tract)
    b = _wolf_tract(white(n, rng), tract)
    rattle = sos(crackle(n, 35, rng), "bandpass", (150, 900), 2)
    return _pk(v) + _pk(b) * _g(-20 + 12 * breath) + _pk(rattle) * _g(-22)


@_sfx("wolf_growl", kind="sustained", norm="max", default_dur=2.5, space=0.8, family="wolf_growl")
def _wolf_growl(dur, p, rng):
    """A low growl (f0 ~55-90 Hz: a very big animal), rough, in breath-long phrases with short
    noisy inhales between them. f0, rough 0..1."""
    f0 = float(p.get("f0", 66.0))
    rough = _clip01(p.get("rough", 0.6))
    n = _N(dur)
    x = _growl_core(n, rng, f0, rough)
    t = t_axis(n)
    env = np.zeros(n)
    tt = 0.0
    while tt < dur:
        L = rng.uniform(1.4, 2.4)
        a, b = n_of(tt), min(n, n_of(tt + L))
        u = np.linspace(0, 1, b - a)
        env[a:b] = np.clip(u / 0.12, 0, 1) ** 1.5 * np.clip((1 - u) / 0.12, 0, 1) * (0.8 + 0.2 * np.sin(np.pi * u))
        tt += L + rng.uniform(0.25, 0.4)
    env = onepole_lp(env, 30.0)
    inh = _wolf_tract(white(n, rng)) * onepole_lp((env < 0.05).astype(float), 20.0) * 0.18
    return Out(_wide(x * env + inh, rng, 0.2) * fade(np.ones(n), 0.08, 0.15)[:, None], 0.0, 0.0)


@_sfx("wolf_snarl", family="wolf_growl", hit=True)
def _wolf_snarl(dur, p, rng):
    """The fight snarl: lips back, teeth bared - higher, harsh, chaotic, with teeth clacks."""
    L = rng.uniform(0.7, 1.05)
    n = _N(L + 0.3)
    t = t_axis(n)
    f = (150 + 90 * np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.5) * (1 + 0.12 * smooth_noise(n, 14, rng))
    src = _pulses(n, f, rng, jitter=0.09, shimmer=0.45, double=0.5)
    v = _wolf_tract(saturate(src * 3, 2.0), "snarl")
    b = _wolf_tract(white(n, rng), "snarl")
    env = np.clip(t / 0.03, 0, 1) * np.clip((L - t) / 0.12, 0, 1) * (0.7 + 0.3 * np.abs(smooth_noise(n, 11, rng)))
    x = (_pk(v) + _pk(b) * _g(-6)) * env
    x += _pk(_growl_core(n, rng, 72, 1.0)) * env * _g(-5)
    for _ in range(rng.integers(1, 3)):
        place(x, _pk(_hit(rng, [1450, 2300, 3500], [0.02, 0.015, 0.01], click=1.0, n=_N(0.05))), rng.uniform(0.1, L - 0.1), _g(-10))
    return Out(_wide(saturate(x, 1.4), rng, 0.25), 0.0, 0.0)


@_sfx("wolf_bite", family="wolf_bite", hit=True)
def _wolf_bite(dur, p, rng):
    """Jaws snap shut on a spider leg: bony double clack (sync), the chitin CRACK, fracture
    crackle, a hollow knock and a growl through clenched teeth."""
    n = _N(1.3)
    out = np.zeros(n)
    for k in range(2):
        place(out, _pk(_hit(rng, [1250, 2150, 3400, 4700], [0.025, 0.02, 0.015, 0.01], click=1.0, n=_N(0.06))),
              k * rng.uniform(0.012, 0.02), _g(-3 * k))
    place(out, _pk(_burst(_N(0.03), rng, 900, 11000, t60=0.012, attack=0.0002)), 0.02, _g(1))
    cr = crackle(_N(0.25), 900, rng, amp_spread=1.1) * exp_env(_N(0.25), 0.18)
    place(out, _pk(sos(cr, "highpass", 1800, 2)), 0.022, _g(-5))
    place(out, _pk(_hit(rng, [420, 760, 1310, 2050], [0.06, 0.05, 0.035, 0.03], click=0.4)), 0.02, _g(-6))
    gr = _growl_core(_N(0.9), rng, 80, 0.9) * dsp.env_bp([(0, 0), (0.05, 1), (0.6, 0.7), (0.9, 0)], _N(0.9))
    place(out, sos(_pk(gr), "lowpass", 2200, 2), 0.06, _g(-4))
    return Out(_wide(out, rng, 0.2), 0.0, 0.0)


@_sfx("wolf_yelp", family="wolf_growl", hit=True)
def _wolf_yelp(dur, p, rng):
    """Pinned: a big animal's pained yelp (pitch jumps up, breaks, falls)."""
    L = rng.uniform(0.3, 0.42)
    n = _N(L + 0.25)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    f = 380 + 360 * np.sin(np.pi * np.clip(u * 1.4, 0, 1)) ** 0.7 - 140 * u
    src = _pulses(n, f, rng, jitter=0.04, shimmer=0.25, double=0.2)
    v = _formants(src, [(800, 220, 0), (1700, 300, -3), (2900, 450, -8)])
    b = _formants(white(n, rng), [(900, 300, 0), (2000, 500, -4)])
    env = np.clip(t / 0.015, 0, 1) * np.clip((L - t) / 0.08, 0, 1)
    return Out((_pk(v) + _pk(b) * _g(-9)) * env, -1.0, 0.0)


@_sfx("wolf_wounded", kind="sustained", norm="int", default_dur=10.0, space=0.6, family="wolf_breath")
def _wolf_wounded(dur, p, rng):
    """Wounded at dawn: slow shallow uneven breaths, a faint wheeze on the inhale, a wet rattle
    on some exhales, a soft whimper now and then. rate (breaths/s ~0.33)."""
    rate = float(p.get("rate", 0.33))
    n = _N(dur)
    t = t_axis(n)
    ei = np.zeros(n)
    eo = np.zeros(n)
    er = np.zeros(n)
    whims = []
    tt = rng.uniform(0.2, 0.8)
    k = 0
    while tt < dur:
        per = rng.uniform(0.8, 1.25) / rate
        li, lo_ = per * rng.uniform(0.25, 0.32), per * rng.uniform(0.32, 0.4)
        for (t0, L, e, amp) in ((tt, li, ei, rng.uniform(0.5, 0.8)), (tt + li + 0.05, lo_, eo, rng.uniform(0.7, 1.0))):
            a, b = n_of(t0), min(n, n_of(t0 + L))
            if b > a:
                u = np.linspace(0, 1, b - a)
                e[a:b] = np.maximum(e[a:b], np.sin(np.pi * u ** 0.8) ** 1.6 * amp)
        if rng.uniform() < 0.45:
            a, b = n_of(tt + li + 0.05), min(n, n_of(tt + li + 0.05 + lo_))
            er[a:b] = eo[a:b]
        if k % 3 == 2 and tt + per < dur:
            whims.append(tt + li + lo_ + 0.2)
        tt += per
        k += 1
    nz_i = _wolf_tract(white(n, rng)) * ei
    wh = dsp.biquad(white(n, rng), "bandpass", rng.uniform(950, 1250), 18) * ei ** 2
    nz_o = _wolf_tract(white(n, rng)) * eo
    rat = sos(crackle(n, 60, rng, amp_spread=0.9), "bandpass", (120, 700), 2) * er
    x = _pk(nz_i) * _g(-4) + _pk(wh) * _g(-20) + _pk(nz_o) + _pk(rat) * _g(-14)
    for tw in whims:
        m = _N(0.7)
        tm = t_axis(m)
        f = 560 + 90 * np.sin(np.pi * np.clip(tm / 0.6, 0, 1)) - 80 * tm
        v = _formants(_pulses(m, f, rng, 0.015, 0.1), [(700, 200, 0), (1600, 300, -6)])
        v = sos(v, "lowpass", 2400, 2) * np.sin(np.pi * np.clip(tm / 0.6, 0, 1)) ** 2
        place(x, _pk(v), tw, _g(-11))
    return Out(_wide(x, rng, 0.2), 0.0, 0.0)


@_sfx("wolf_whine", family="wolf_growl", space=0.7)
def _wolf_whine(dur, p, rng):
    """A soft, low whine through the nose."""
    n = _N(1.0)
    t = t_axis(n)
    L = 0.8
    f = 520 + 120 * np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.8 - 60 * t
    v = _formants(_pulses(n, f, rng, 0.012, 0.08), [(650, 180, 0), (1500, 260, -5), (2600, 400, -12)])
    b = _formants(white(n, rng), [(700, 300, 0)])
    env = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 1.5
    return Out(sos((_pk(v) + _pk(b) * _g(-14)) * env, "lowpass", 3000, 2), -4.0, 0.0)


@_sfx("wolf_settle", family="wolf_body")
def _wolf_settle(dur, p, rng):
    """The wolf sits down in the snow: haunches settle (heavy soft whump + crunch), a breath out."""
    n = _N(1.4)
    out = np.zeros(n)
    m = _N(0.45)
    e = _env_hr(t_axis(m), 0.04, 0.3, 0.18, 0.6, 0.06)
    place(out, _pk(_crunch(m, rng, e, 3000, 260, 4800)), 0.0, 1.0)
    place(out, _pk(_whump(_N(0.5), rng, 200, 0.12, 0.03)), 0.0, _g(-2))
    place(out, _pk(_thump(_N(0.4), 70, 42, 0.03, 0.18)), 0.02, _g(-8))
    hm = _N(0.6)
    hx = _wolf_tract(white(hm, rng)) * np.clip(t_axis(hm) / 0.02, 0, 1) * np.exp(-t_axis(hm) / 0.22)
    place(out, _pk(hx), 0.42, _g(-6))
    return Out(out, 0.0, 0.0)


@_sfx("wolf_land", family="wolf_body", hit=True)
def _wolf_land(dur, p, rng):
    """A huge wolf landing on the path: front paws then hind paws (sync = first contact),
    a deep whump, crunch and spray, a short grunt."""
    n = _N(1.4)
    out = np.zeros(n)
    for k, tt in enumerate((0.0, 0.03, 0.11, 0.15)):
        x, _ = render_sync("wolf_paw", params=dict(pace="gallop", depth=0.6), seed=int(rng.integers(1 << 30)))
        place(out, dsp.mono(x), tt + rng.uniform(0, 0.012), _g(-2 * (k % 2)))
    place(out, _pk(_whump(_N(0.6), rng, 190, 0.14, 0.01)), 0.0, _g(2))
    place(out, _pk(_thump(_N(0.6), 75, 36, 0.03, 0.3)), 0.0, _g(-2))
    place(out, _pk(_spray(_N(0.9), rng, 0.5, 1800, 8000)), 0.02, _g(-8))
    gm = _N(0.35)
    gx = _growl_core(gm, rng, 70, 0.7) * np.clip(t_axis(gm) / 0.02, 0, 1) * np.exp(-t_axis(gm) / 0.12)
    place(out, _pk(gx), 0.08, _g(-6))
    return Out(_wide(out, rng, 0.2), 0.0, 0.0)


@_sfx("wolf_leap", family="wolf_body", hit=True, space=0.4)
def _wolf_leap(dur, p, rng):
    """The wolf leaps over her: a huge body of air and fur passing overhead left to right, a
    snarl at the apex (sync)."""
    n = _N(1.6)
    t = t_axis(n)
    sync = 0.38
    u = np.clip(t / 0.85, 0, 1)
    env = np.where(u < 0.45, (u / 0.45) ** 2, np.exp(-(u - 0.45) / 0.18))
    x = _swish(n, rng, 180, 900, q=0.6, curve=0.8) * env
    x += 0.5 * bandpass(pink(n, rng), 600, 3500, 2) * env * (0.6 + 0.4 * np.abs(np.sin(TWO_PI * 26 * t)))
    st = pan_curve(_pk(x), np.clip(-0.8 + 1.8 * u, -1, 1))
    sn, _ = render_sync("wolf_snarl", seed=int(rng.integers(1 << 30)))
    place(st, sn.astype(np.float64) * 0.9, sync - 0.1)
    return Out(st, 0.0, sync)


# ============================================================================ the spider
def _click_one(rng, size=0.6):
    """One dry chitin click: sub-ms transient + short hollow plate modes."""
    sc = 1.6 - size
    fr = np.array([rng.uniform(500, 900), rng.uniform(1300, 2000), rng.uniform(2600, 3600), rng.uniform(4500, 6500)]) * sc
    t60 = np.array([0.03, 0.022, 0.016, 0.01]) * (0.7 + 0.6 * size)
    x = _hit(rng, fr, t60, amps=np.array([0.6, 1.0, 0.6, 0.35]) * rng.uniform(0.6, 1, 4), click=1.2, click_hp=2500, n=_N(0.06))
    x += _pk(_hit(rng, [rng.uniform(230, 380)], [0.03], click=0.0, n=_N(0.06))) * 0.25 * size
    return _pk(x)


@_sfx("chitin_click", family="spider_click", space=0.8)
def _chitin_click(dur, p, rng):
    """Dry chitin clicks (mandibles, leg joints): a burst of 1-4 hollow clicks. count, size."""
    cnt = int(p.get("count", rng.integers(2, 5)))
    size = _clip01(p.get("size", 0.7))
    n = _N(0.12 * cnt + 0.15)
    out = np.zeros(n)
    tt = 0.0
    for k in range(cnt):
        place(out, _click_one(rng, size), tt, _g(-rng.uniform(0, 5)))
        tt += rng.uniform(0.025, 0.07)
    return Out(out, -2.0, 0.0)


@_sfx("spider_skitter", kind="sustained", norm="int", default_dur=2.0, space=0.6, family="spider_move")
def _spider_skitter(dur, p, rng):
    """Eight legs moving fast: alternating tetrapod gait (two groups of four, each foot a
    chitin tick + a tiny snow pierce), dry hairy body rustle. speed (strides/s ~6), size."""
    speed = float(p.get("speed", 6.0))
    size = _clip01(p.get("size", 0.8))
    n = _N(dur)
    out = np.zeros((n, 2))
    pans = np.linspace(-0.8, 0.8, 8)
    tt = 0.0
    g = 0
    while tt < dur - 0.05:
        legs = range(0, 8, 2) if g % 2 == 0 else range(1, 8, 2)
        for lg in legs:
            dt = rng.uniform(0.0, 0.035)
            c = _click_one(rng, size) * _g(-rng.uniform(0, 8))
            m = _N(0.06)
            pr = _crunch(m, rng, np.exp(-t_axis(m) / 0.012), 9000, 900, 8000) * 0.5
            dsp.mix_into(out, pan_curve(c[:m] + _pk(pr) * _g(-8) if len(c) >= m else c, pans[lg]), n_of(tt + dt))
        tt += 0.5 / speed * rng.uniform(0.85, 1.15)
        g += 1
    ru = bandpass(white(n, rng), 2500, 9000, 2) * (0.4 + 0.6 * np.abs(smooth_noise(n, 25, rng)))
    out += _wide(_pk(ru) * _g(-20), rng, 0.6)
    return Out(out, 0.0, 0.0)


@_sfx("thread_creak", family="thread", space=0.7)
def _thread_creak(dur, p, rng):
    """A thick silk thread taking an enormous weight as Grandmother descends: slow stick-slip
    creak (rope on wood), a bowed-wire tension tone gliding down as the thread pays out, tiny
    fibre snaps. length (s, default 2.8), pitch (Hz, ~110)."""
    L = float(p.get("length", 2.8))
    f0 = float(p.get("pitch", 110.0))
    n = _N(L + 0.4)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    env = np.clip(t / 0.35, 0, 1) ** 1.5 * np.clip((L - t) / 0.5, 0, 1)
    rate = 18 + 45 * np.abs(smooth_noise(n, 0.9, rng)) + 25 * np.sin(np.pi * u)
    cr = dsp.friction(n, rate, rng, jitter=0.35, body=[(175, 5, 1.0), (410, 6, 0.8), (1050, 9, 0.4), (2300, 12, 0.15)])
    f = f0 * (1.0 - 0.18 * u) * (1 + 0.004 * smooth_noise(n, 3, rng))
    bow = dsp.saw(f, n) * (0.6 + 0.4 * np.abs(smooth_noise(n, 30, rng)))
    bow = _formants(bow, [(f0 * 3.1, 120, 0), (f0 * 7.2, 260, -4), (1900, 500, -10)])
    sn = _grains(n, rng, 6, env, 0.6)
    sn = sos(sn, "highpass", 2500, 2)
    x = _pk(cr) * env + _pk(bow) * env * _g(-9) + _pk(sn) * _g(-14)
    return Out(_wide(x, rng, 0.3), 0.0, 0.0)


@_sfx("leg_stab", family="spider_leg", hit=True, space=0.8)
def _leg_stab(dur, p, rng):
    """A spider leg stabbing into snow: a fast cut of air, then the impact (sync): a dense,
    pointed crunch, a chitin click on contact, a low thud of weight, a puff of powder."""
    n = _N(0.9)
    out = np.zeros(n)
    sync = rng.uniform(0.04, 0.06)
    m = _N(sync)
    place(out, _pk(_swish(m, rng, 900, 5000, q=1.0, color="white")) * np.linspace(0, 1, m) ** 2.5, 0.0, _g(-9))
    ns = _N(0.12)
    e = np.clip(t_axis(ns) / 0.002, 0, 1) * np.exp(-t_axis(ns) / 0.03)
    place(out, _pk(_crunch(ns, rng, e, 14000, 500, 9500, [(rng.uniform(1100, 1700), 2.5, 0.5)])), sync, 1.0)
    place(out, _click_one(rng, 0.85), sync, _g(-3))
    place(out, _pk(_thump(_N(0.35), 95, 48, 0.012, 0.1)), sync, _g(-5))
    place(out, _pk(_whump(_N(0.3), rng, 260, 0.04, 0.003)), sync, _g(-7))
    place(out, _pk(_spray(_N(0.45), rng, 0.25, 2200, 9500)), sync + 0.01, _g(-12))
    return Out(out, 0.0, sync)


@_sfx("spider_hiss", family="spider_voice", space=0.6)
def _spider_hiss(dur, p, rng):
    """Inhuman hiss + stridulation: a file-and-scraper click train sweeping into a rasping buzz
    through chitin plates, air hissing from spiracles, a sub rumble of size."""
    L = float(p.get("length", rng.uniform(1.8, 2.4)))
    n = _N(L + 0.4)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    rate = 60 + 220 * np.sin(np.pi * u) ** 1.3 + 30 * smooth_noise(n, 3, rng)
    st = dsp.friction(n, rate, rng, jitter=0.18, body=[(880, 6, 1.0), (1650, 8, 0.8), (2900, 10, 0.55), (4300, 12, 0.3)])
    env = np.clip(t / 0.25, 0, 1) * np.clip((L - t) / 0.35, 0, 1) ** 1.2
    hs = bandpass(white(n, rng), 2500, 9500, 2) * (np.clip(t / 0.4, 0, 1) * np.clip((L + 0.2 - t) / 0.6, 0, 1))
    sub = _formants(_pulses(n, 41 * (1 + 0.05 * smooth_noise(n, 2, rng)), rng, 0.08, 0.4, 0.4), [(180, 90, 0), (420, 150, -6)])
    x = _pk(st) * env + _pk(hs) * _g(-7) + _pk(sub) * env * _g(-9)
    return Out(_wide(x, rng, 0.45), 0.0, 0.0)


@_sfx("spider_shriek", family="spider_voice", hit=True, space=0.5)
def _spider_shriek(dur, p, rng):
    """Burning shriek: stridulation accelerating into a screech, metallic squeal partials gliding
    up then collapsing, ring-modulated rasp, burning hiss and crackle."""
    L = float(p.get("length", rng.uniform(1.6, 2.1)))
    n = _N(L + 0.5)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    rate = 160 + 900 * np.sin(np.pi * np.clip(u * 1.3, 0, 1)) ** 0.8
    st = dsp.friction(n, rate, rng, jitter=0.12, body=[(1300, 7, 1.0), (2300, 9, 0.8), (3700, 11, 0.5)])
    sq = np.zeros(n)
    for k, (fa, fb) in enumerate(((1800, 2700), (2350, 3500), (3100, 4300))):
        f = fa + (fb - fa) * np.sin(np.pi * np.clip(u * 1.15, 0, 1)) ** 0.6 - 900 * np.clip(u - 0.75, 0, 1)
        f = f * (1 + 0.02 * smooth_noise(n, 12, rng))
        sq += np.sin(TWO_PI * np.cumsum(f) / SR + rng.uniform(0, 6)) / (k + 1)
    sq *= 1 + 0.6 * np.sin(TWO_PI * np.cumsum(38 + 10 * smooth_noise(n, 3, rng)) / SR)
    rm = bandpass(white(n, rng), 600, 3200, 2) * np.sin(TWO_PI * 117 * t)
    env = np.clip(t / 0.05, 0, 1) * np.clip((L - t) / 0.4, 0, 1) * (0.75 + 0.25 * np.abs(smooth_noise(n, 9, rng)))
    hs = bandpass(white(n, rng), 3000, 11000, 2) * np.clip(t / 0.1, 0, 1) * np.clip((L + 0.4 - t) / 0.6, 0, 1)
    cr = sos(crackle(n, 70, rng), "highpass", 2000, 2)
    x = (_pk(st) + _pk(sq) * _g(-5) + _pk(rm) * _g(-8)) * env + _pk(hs) * _g(-14) + _pk(cr) * _g(-16)
    return Out(_wide(saturate(x, 1.5), rng, 0.4), 0.0, 0.0)


@_sfx("spider_drop", family="spider_body", hit=True)
def _spider_drop(dur, p, rng):
    """Grandmother drops to the ground: the body's heavy whump (sync), eight legs planting in a
    ragged ring, a chitin rattle, snow thrown up."""
    n = _N(1.8)
    out = np.zeros((n, 2))
    m = _N(0.7)
    body = _pk(_whump(m, rng, 170, 0.18, 0.01)) + _pk(_thump(m, 62, 32, 0.04, 0.35)) * _g(-3)
    dsp.mix_into(out, to_stereo(body), 0)
    pans = rng.uniform(-0.85, 0.85, 8)
    for k in range(8):
        x, s = render_sync("leg_stab", seed=int(rng.integers(1 << 30)))
        dsp.mix_into(out, dsp.pan_stereo(x.astype(np.float64), pans[k]), n_of(max(0.0, rng.uniform(-0.03, 0.14) - s)),
                     _g(-6 - rng.uniform(0, 5)))
    ra = np.zeros(n)
    for k in range(10):
        place(ra, _click_one(rng, 0.7), rng.uniform(0.05, 0.6), _g(-rng.uniform(4, 12)))
    out += _wide(ra, rng, 0.5) * _g(-4)
    out += _wide(_pk(_spray(n, rng, 0.8, 1500, 8000)), rng, 0.5) * _g(-9)
    return Out(out, 1.0, 0.0)


@_sfx("spider_eyes", family="spider_eyes", space=0.4)
def _spider_eyes(dur, p, rng):
    """The eye cluster opens: eight small wet clicks (lids) and a cold glassy shimmer."""
    n = _N(2.2)
    out = np.zeros((n, 2))
    for k in range(8):
        m = _N(0.03)
        tm = t_axis(m)
        f = rng.uniform(1400, 2600) * (1 + 0.6 * tm / 0.03)
        c = np.sin(TWO_PI * np.cumsum(f) / SR) * np.exp(-tm / 0.008)
        dsp.mix_into(out, pan_curve(c, rng.uniform(-0.5, 0.5)), n_of(0.03 * k + rng.uniform(0, 0.03)), _g(-rng.uniform(0, 6)))
    t = t_axis(n)
    sh = np.zeros(n)
    for f in (3520.0, 3730.0, 4190.0, 4980.0):
        sh += np.sin(TWO_PI * f * t + rng.uniform(0, 6)) * (1 + 0.3 * np.sin(TWO_PI * rng.uniform(1.5, 4) * t))
    sh *= np.clip((t - 0.15) / 0.5, 0, 1) * np.exp(-np.maximum(t - 0.65, 0) / 0.6)
    out += _wide(_pk(sh) * _g(-10), rng, 0.6)
    return Out(out, -6.0, 0.0)


# ============================================================================ the basket
def _wicker_hit(rng, n, size=1.0):
    e = np.exp(-t_axis(n) / 0.03)
    tw = _grains(n, rng, 1800, e, 0.9)
    tw = dsp.resonator_bank(tw, [rng.uniform(650, 900), rng.uniform(1400, 1900), rng.uniform(2700, 3500)], [7, 9, 10], [1, 0.7, 0.4])
    return _pk(tw) + _pk(_burst(n, rng, 90, 700, t60=0.04, attack=0.002)) * _g(-4 + 4 * size)


@_sfx("basket_tumble", family="basket")
def _basket_tumble(dur, p, rng):
    """The basket hits the snow and tumbles: wicker crunches on each bounce (first one = sync),
    soft thuds, contents knocking inside, creaks and the cloth cover fluttering between."""
    n = _N(1.9)
    out = np.zeros(n)
    times = [0.0, 0.3, 0.52, 0.7, 0.84, 0.95]
    for k, tt in enumerate(times):
        a = _g(-3.0 * k)
        place(out, _wicker_hit(rng, _N(0.2), 1.0 - 0.12 * k), tt, a)
        place(out, _pk(_whump(_N(0.2), rng, 300, 0.035)), tt, a * _g(-4))
        m = _N(0.15)
        place(out, _pk(_crunch(m, rng, np.exp(-t_axis(m) / 0.04), 5000, 500, 7000)), tt, a * _g(-7))
        if k < 4:
            place(out, _pk(_hit(rng, [230, 410, 690], [0.05, 0.04, 0.03], click=0.2)), tt + 0.03, a * _g(-10))
    ln = _N(1.2)
    tl = t_axis(ln)
    cr = dsp.friction(ln, 120 + 200 * np.abs(smooth_noise(ln, 4, rng)), rng, jitter=0.5,
                      body=[(700, 5, 1.0), (1600, 7, 0.6), (2900, 9, 0.3)]) * np.exp(-tl / 0.6)
    place(out, _pk(cr), 0.05, _g(-12))
    fl = bandpass(pink(ln, rng), 300, 2500, 2) * (0.4 + 0.6 * np.abs(smooth_noise(ln, 20, rng))) * np.exp(-tl / 0.4)
    place(out, _pk(fl), 0.0, _g(-14))
    return Out(_wide(out, rng, 0.25), -1.0, 0.0)


@_sfx("bread_thump", family="bread")
def _bread_thump(dur, p, rng):
    """A round loaf tumbling out into snow: dense soft thump (sync), crust crackle, a smaller
    bounce and two soft rolls."""
    n = _N(0.9)
    out = np.zeros(n)
    for k, (tt, a) in enumerate(((0.0, 0.0), (0.19, -6.0), (0.33, -11.0), (0.45, -15.0))):
        m = _N(0.15)
        th = _pk(_burst(m, rng, 110, 650, t60=0.05, attack=0.002)) + _pk(_thump(m, 150, 95, 0.01, 0.05)) * _g(-4)
        place(out, th, tt, _g(a))
        place(out, _pk(sos(crackle(_N(0.06), 700, rng), "highpass", 1500, 2) * exp_env(_N(0.06), 0.04)), tt, _g(a - 12))
        place(out, _pk(_crunch(m, rng, np.exp(-t_axis(m) / 0.03), 3500, 500, 6000)), tt, _g(a - 8))
    return Out(out, -3.0, 0.0)


def _glass_ring(rng, n, base=None, t60=0.4):
    base = base or rng.uniform(820, 1050)
    fr = np.array([1.0, 2.32, 3.89, 5.6, 7.3]) * base
    return _hit(rng, fr, np.array([1.0, 0.7, 0.5, 0.35, 0.25]) * t60, amps=np.array([1.0, 0.7, 0.5, 0.35, 0.2]),
                click=0.6, click_hp=4000, n=n)


@_sfx("bottle_roll", family="bottle")
def _bottle_roll(dur, p, rng):
    """The wine bottle drops out and rolls: a dull glass knock in the snow (sync), the slosh and
    glug of the wine as it turns, the soft rumble of rolling, then it CLINKS against the lantern
    and rocks still. clink 0/1."""
    n = _N(2.4)
    t = t_axis(n)
    out = np.zeros(n)
    place(out, _pk(_burst(_N(0.1), rng, 150, 900, t60=0.05)), 0.0, 1.0)
    place(out, _pk(_glass_ring(rng, _N(0.6), t60=0.18)), 0.0, _g(-12))
    roll_e = np.clip((t - 0.08) / 0.1, 0, 1) * np.clip((1.62 - t) / 0.25, 0, 1)
    rot = 0.5 + 0.5 * np.sin(TWO_PI * np.cumsum(3.2 - 1.2 * np.clip(t / 1.6, 0, 1)) / SR)
    rum = sos(brown(n, rng), "lowpass", 600, 2) * roll_e * (0.4 + 0.6 * rot)
    sl = bandpass(pink(n, rng), 180, 900, 2) * roll_e * (0.3 + 0.7 * np.abs(smooth_noise(n, 4, rng)))
    out += _pk(rum) * _g(-6) + _pk(sl) * _g(-9)
    for tt in np.sort(rng.uniform(0.2, 1.4, 5)):
        place(out, _drop(rng, rng.uniform(280, 520), rng.uniform(0.012, 0.025), chirp=0.4), tt, _g(-14))
    cr = _crunch(n, rng, roll_e * 0.6, 900, 600, 5000)
    out += _pk(cr) * _g(-12)
    if int(p.get("clink", 1)):
        tc = 1.62
        place(out, _pk(_hit(rng, [2350, 3870, 5640, 7210], [0.6, 0.45, 0.3, 0.2], click=1.0, click_hp=3500, n=_N(0.8))), tc, _g(-1))
        place(out, _pk(_hit(rng, [1720, 2960, 4400], [0.3, 0.2, 0.12], click=0.3, n=_N(0.4))), tc + 0.001, _g(-8))
        place(out, _pk(_hit(rng, [2350, 3870], [0.3, 0.2], click=0.5, n=_N(0.4))), tc + 0.21, _g(-12))
    return Out(_wide(out, rng, 0.2), -1.0, 0.0)


@_sfx("bottle_clink", family="bottle")
def _bottle_clink(dur, p, rng):
    """Glass against metal: a bright clink and its ring."""
    n = _N(1.0)
    out = np.zeros(n)
    place(out, _pk(_hit(rng, [2350, 3870, 5640, 7210], [0.6, 0.45, 0.3, 0.2], click=1.0, click_hp=3500, n=_N(0.8))), 0.0)
    place(out, _pk(_hit(rng, [1720, 2960, 4400], [0.3, 0.2, 0.12], click=0.3, n=_N(0.4))), 0.001, _g(-8))
    return Out(out, -3.0, 0.0)


@_sfx("lantern_roll", family="lantern")
def _lantern_roll(dur, p, rng):
    """The lit lantern rolls out of the basket: tin frame clatter and loose handle on each turn,
    the glass chimney rattling in its cage, a soft crunch of rolling, the flame fluttering;
    it settles with a clank and the handle drops with a 'ting'."""
    n = _N(2.6)
    t = t_axis(n)
    out = np.zeros(n)
    tt, gap, a = 0.0, 0.3, 0.0
    while tt < 1.5:
        place(out, _pk(_hit(rng, [1180, 2290, 3650, 5120], [0.12, 0.09, 0.07, 0.05], spread=0.03, click=0.9)), tt, _g(a))
        if rng.uniform() < 0.7:
            place(out, _pk(_hit(rng, [4200, 6100, 8300], [0.06, 0.05, 0.03], spread=0.04, click=0.5)), tt + rng.uniform(0.02, 0.08), _g(a - 9))
        tt += gap * rng.uniform(0.85, 1.15)
        gap *= 0.86
        a -= 1.5
    place(out, _pk(_hit(rng, [980, 1870, 3010, 4400], [0.2, 0.15, 0.1, 0.07], click=0.8)), tt + 0.05, _g(-3))
    place(out, _pk(_hit(rng, [3150, 5300, 7400], [0.5, 0.35, 0.2], click=0.4, n=_N(0.7))), tt + 0.3, _g(-12))
    re = np.clip(t / 0.05, 0, 1) * np.clip((tt - t) / 0.2, 0, 1)
    out += _pk(_crunch(n, rng, re * 0.7, 1500, 500, 6000)) * _g(-10)
    fl = bandpass(pink(n, rng), 180, 1300, 2) * (0.5 + 0.5 * np.abs(smooth_noise(n, 12, rng)))
    out += _pk(fl) * _g(-20) * np.clip(t / 0.3, 0, 1)
    return Out(_wide(out, rng, 0.2), -1.0, 0.0)


# ============================================================================ fire
def _flutter(n, rng, rate=12.0, depth=0.6):
    return 1.0 + depth * smooth_noise(n, rate, rng)


@_sfx("lantern_smash", family="lantern_smash", hit=True, trim=1.0, space=0.4)
def _lantern_smash(dur, p, rng):
    """The lantern smashed against the web: tin frame crumples (inharmonic clang + crunch),
    the glass chimney shatters, oil splashes and catches with a low 'FWOOMP'. Sync = impact."""
    n = _N(2.8)
    t = t_axis(n)
    out = np.zeros((n, 2))
    m = _N(1.0)
    metal = _hit(rng, [430, 980, 1530, 2210, 3170, 4420, 5900], [0.5, 0.42, 0.35, 0.28, 0.2, 0.14, 0.1], spread=0.02, click=1.0, n=m)
    dent = _burst(_N(0.05), rng, 900, 7000, t60=0.025, attack=0.0002)
    dsp.mix_into(out, to_stereo(_pk(metal) * _g(-2)), 0)
    dsp.mix_into(out, to_stereo(_pk(dent)), 0)
    gl, _ = render_sync("lib:glass_break", seed=int(rng.integers(1 << 30)))
    dsp.mix_into(out, gl.astype(np.float64) * _g(-3), n_of(0.004))
    sp = np.zeros(_N(0.6))
    for tt in rng.exponential(0.08, 18):
        place(sp, _drop(rng, rng.uniform(900, 3000), rng.uniform(0.004, 0.01)), min(0.5, tt), rng.uniform(0.2, 0.6))
    sp += bandpass(white(len(sp), rng), 800, 5000, 2) * exp_env(len(sp), 0.15) * 0.3
    dsp.mix_into(out, _wide(_pk(sp), rng, 0.5) * _g(-9), n_of(0.01))
    nf = _N(1.6)
    tf = t_axis(nf)
    fw = tv_lowpass(white(nf, rng), lambda x: 300 + 2700 * (1 - math.exp(-x / 0.12)) * math.exp(-x / 0.9), q=0.7, block=64)
    fw = sos(fw, "highpass", 70, 2) * np.clip(tf / 0.06, 0, 1) ** 1.5 * np.exp(-tf / 0.55) * _flutter(nf, rng, 14, 0.5)
    lo = sos(brown(nf, rng), "lowpass", 180, 2) * np.clip(tf / 0.05, 0, 1) * np.exp(-tf / 0.4)
    dsp.mix_into(out, _wide(_pk(fw) * _g(-1) + _pk(lo) * _g(-4), rng, 0.4), n_of(0.05))
    cr = sos(crackle(n, 60, rng), "highpass", 1800, 2) * np.clip((t - 0.1) / 0.2, 0, 1) * np.exp(-t / 1.6)
    out += _wide(_pk(cr) * _g(-12), rng, 0.6)
    return Out(out, 0.0, 0.0)


@_sfx("fire_whoosh", family="fire_whoosh", hit=True, trim=1.0, space=0.3)
def _fire_whoosh(dur, p, rng):
    """Fire racing along the web: a roaring band sweeping up, flame turbulence, crackle racing
    with it, panned along the strand (pan0 -> pan1). size 0..1."""
    s = _clip01(p.get("size", 0.8))
    L = 1.6 + 1.4 * s
    n = _N(L + 0.6)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    env = np.clip(t / 0.12, 0, 1) ** 1.6 * np.where(u < 0.45, 1.0, np.exp(-(u - 0.45) / 0.22))
    fc = 260 + 2200 * np.sin(np.pi * np.clip(u * 0.9, 0, 1)) ** 0.8
    roar = tv_bandpass(pink(n, rng), fc, q=0.6, block=64) * _flutter(n, rng, 13, 0.55)
    low = sos(brown(n, rng), "lowpass", 260, 2) * (1 + 0.4 * smooth_noise(n, 6, rng))
    cre = np.clip(t / 0.08, 0, 1) * np.exp(-np.maximum(t - 0.3, 0) / (L * 0.4))
    cr = sos(_grains(n, rng, 380, cre, 1.0), "highpass", 1500, 2)
    hs = bandpass(white(n, rng), 3500, 11000, 2)
    mono = (_pk(roar) + _pk(low) * _g(-3) + _pk(cr) * _g(-6) + _pk(hs) * _g(-16)) * env
    p0, p1 = float(p.get("pan0", -0.7)), float(p.get("pan1", 0.7))
    st = pan_curve(mono, p0 + (p1 - p0) * np.clip(u * 1.2, 0, 1))
    st = 0.75 * st + 0.25 * _wide(mono, rng, 0.7)
    return Out(st, 4.0 * (s - 0.6), 0.0)


def fire_bed(n, rng, intensity=1.0):
    """The burning web: turbulent roar, flame flutter, crackle/pops, hiss (stereo)."""
    out = np.zeros((n, 2))
    surge = 0.75 + 0.25 * smooth_noise(n, 0.35, rng)
    for ch in range(2):
        roar = sos(brown(n, rng), "lowpass", 380 + 120 * intensity, 2) * surge
        fl = bandpass(pink(n, rng), 220, 1800, 2) * _flutter(n, rng, 11, 0.6) * surge
        pops = _grains(n, rng, 55 * intensity + 8, np.ones(n), 1.1)
        pops = dsp.resonator_bank(pops, [rng.uniform(1200, 1800), rng.uniform(2600, 3600), rng.uniform(4800, 6200)],
                                  [6, 7, 8], [1.0, 0.8, 0.5])
        big = dsp.resonator_bank(_grains(n, rng, 3 * intensity + 0.5, np.ones(n), 0.8), [380, 720, 1150], [5, 6, 7], [1, 0.7, 0.4])
        hs = bandpass(white(n, rng), 3500, 11000, 2)
        out[:, ch] = (_pk(roar) + _pk(fl) * _g(-4) + _pk(pops) * _g(-3) + _pk(big) * _g(-6) + _pk(hs) * _g(-22))
    return out


@_sfx("fire_roar", kind="sustained", norm="int", default_dur=4.0, space=0.0, family="fire_bed")
def _fire_roar(dur, p, rng):
    """Crackle and roar of the burning web (intensity 0..1)."""
    n = _N(dur)
    return Out(fire_bed(n, rng, _clip01(p.get("intensity", 1.0))), 0.0, 0.0)


def ember_bed(n, rng, density=1.0):
    out = np.zeros((n, 2))
    for ch in range(2):
        cr = _grains(n, rng, 7 * density, np.ones(n), 1.0)
        cr = dsp.resonator_bank(cr, [rng.uniform(2200, 3200), rng.uniform(4200, 5600)], [6, 8], [1.0, 0.6])
        sm = sos(brown(n, rng), "lowpass", 160, 2) * (0.6 + 0.4 * smooth_noise(n, 0.3, rng))
        sz = bandpass(white(n, rng), 4000, 10000, 2) * np.clip(smooth_noise(n, 0.5, rng), 0, 1) ** 2
        out[:, ch] = _pk(cr) + _pk(sm) * _g(-14) + _pk(sz) * _g(-26)
    return out


@_sfx("embers", kind="sustained", norm="int", default_dur=4.0, space=0.0, family="embers")
def _embers(dur, p, rng):
    """Embers: sparse tiny crackles, a faint smoulder, a breath of sizzle."""
    return Out(ember_bed(_N(dur), rng, float(p.get("density", 1.0))), 0.0, 0.0)


@_sfx("fire_flare", family="flash", hit=True, space=0.0)
def _fire_flare(dur, p, rng):
    """The fire flares to white (the flash transition): a roaring swell rising into a bright
    bloom at sync (0.9 s), then a soft airy decay."""
    n = _N(2.6)
    t = t_axis(n)
    sync = 0.9
    env = np.where(t < sync, (t / sync) ** 2.4, np.exp(-(t - sync) / 0.45))
    fc = np.where(t < sync, 300 + 4200 * (t / sync) ** 2, 4500 * np.exp(-(t - sync) / 0.5) + 500)
    x = tv_bandpass(pink(n, rng), fc, q=0.5, block=64) * _flutter(n, rng, 15, 0.4)
    x += 0.6 * sos(brown(n, rng), "lowpass", 300, 2)
    air = bandpass(white(n, rng), 3000, 12000, 2) * np.exp(-np.abs(t - sync) / 0.3)
    return Out(_wide(_pk(x * env) + _pk(air) * _g(-10), rng, 0.6), 0.0, sync)


# ============================================================================ the village
@_sfx("door_wood", family="door")
def _door_wood(dur, p, rng):
    """A heavy plank door pulled shut across a snowy street: swing (iron strap-hinge squeak +
    air), the SLAM (sync: slab thump, plank modes, frame knock), the latch bar dropping,
    a rattle. force 0..1."""
    f = _clip01(p.get("force", 0.75))
    sync = rng.uniform(0.2, 0.3)
    n = _N(sync + 1.3)
    out = np.zeros(n)
    m = _N(sync)
    tm = t_axis(m)
    sw = np.clip(tm / sync, 0, 1)
    hinge = dsp.friction(m, 300 + 500 * sw, rng, jitter=0.25, body=[(720, 10, 1.0), (1430, 12, 0.6), (2150, 14, 0.3)])
    place(out, _pk(hinge) * sw ** 1.5, 0.0, _g(-14 + 4 * f))
    air = sos(pink(m, rng), "lowpass", 600, 2) * sw ** 2
    place(out, _pk(air), 0.0, _g(-14))
    slab = _pk(_thump(_N(0.5), 150 + 30 * f, 70, 0.015, 0.14 + 0.06 * f))
    planks = _pk(_hit(rng, [96, 182, 263, 415, 640, 985, 1510], [0.3, 0.26, 0.22, 0.18, 0.13, 0.09, 0.06], spread=0.05, click=0.6, n=_N(0.6)))
    cont = _pk(_burst(_N(0.06), rng, 120, 3200, t60=0.02, attack=0.0004))
    place(out, slab + planks * _g(-2) + 0 * slab, sync, 1.0)
    place(out, cont, sync, _g(-3))
    lt = sync + rng.uniform(0.04, 0.08)
    place(out, _pk(_hit(rng, [1850, 2720, 4180, 6050], [0.12, 0.1, 0.07, 0.05], click=1.0)), lt, _g(-7))
    for k in range(rng.integers(2, 4)):
        place(out, _pk(_hit(rng, [rng.uniform(500, 1100), rng.uniform(1500, 2400)], [0.04, 0.03], click=0.2)),
              sync + 0.06 + 0.05 * k + rng.uniform(0, 0.03), _g(-14 - 3 * k))
    place(out, _pk(_burst(_N(0.15), rng, hi=200, t60=0.08, attack=0.004)), sync + 0.005, _g(-6))
    return Out(out, -6.0 * (1 - f), sync)


@_sfx("gate_creak", family="gate")
def _gate_creak(dur, p, rng):
    """The village gate on iron hinges: a long rising-falling creak (wood groan + iron squeal),
    then it swings to with a soft wooden knock."""
    L = rng.uniform(1.5, 1.9)
    n = _N(L + 0.8)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    sw = np.sin(np.pi * u) ** 0.9
    iron = dsp.friction(n, 90 + 330 * sw + 40 * smooth_noise(n, 2, rng), rng, jitter=0.15,
                        body=[(880, 12, 1.0), (1560, 14, 0.7), (2440, 16, 0.4), (3500, 18, 0.2)])
    wood = dsp.friction(n, 25 + 45 * sw, rng, jitter=0.35, body=[(190, 5, 1.0), (420, 7, 0.7), (980, 10, 0.3)])
    x = (_pk(iron) * _g(-3) + _pk(wood)) * sw
    place(x, _pk(_hit(rng, [180, 340, 610, 1020], [0.15, 0.12, 0.08, 0.05], click=0.4)), L + 0.05, _g(-6))
    return Out(x, -3.0, 0.0)


def flutter_bed(n, rng, wind=0.5):
    """Oil-lantern flame in the wind: soft low-mid flutter, gutters on gusts, wick ticks."""
    t = t_axis(n)
    gust = np.clip(smooth_noise(n, 0.4, rng) * 0.8 + 0.4, 0, 1.2)
    fl = bandpass(pink(n, rng), 160, 1300, 2) * _flutter(n, rng, 12, 0.7) * (0.6 + wind * gust)
    tick = sos(_grains(n, rng, 2.0, np.ones(n), 0.8), "highpass", 2200, 2)
    return _pk(fl) + _pk(tick) * _g(-16) + 0 * t


@_sfx("flame_flutter", kind="sustained", norm="int", default_dur=3.0, space=0.5, family="flame")
def _flame_flutter(dur, p, rng):
    """A lantern flame fluttering in the wind (wind 0..1)."""
    n = _N(dur)
    return Out(_wide(flutter_bed(n, rng, float(p.get("wind", 0.5))), rng, 0.3), 0.0, 0.0)


@_sfx("hood_fall", family="hood", space=0.7)
def _hood_fall(dur, p, rng):
    """A red hood falling from the burnt web: cloth fluttering as it drifts down, a soft
    landing on snow (~1.4 s)."""
    L = rng.uniform(1.2, 1.6)
    n = _N(L + 0.5)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    drift = np.sin(np.pi * u) ** 0.7 * (0.5 + 0.5 * np.abs(smooth_noise(n, 2.5, rng)))
    fl = bandpass(pink(n, rng), 350, 3200, 2) * (0.3 + 0.7 * np.abs(smooth_noise(n, 24, rng))) * drift
    st = pan_curve(_pk(fl), rng.uniform(-0.6, 0.6) + 0.25 * smooth_noise(n, 0.8, rng))
    m = _N(0.25)
    land = _pk(_burst(m, rng, 150, 1200, t60=0.06, attack=0.006)) + _pk(_crunch(m, rng, np.exp(-t_axis(m) / 0.03), 1500, 600, 6000)) * _g(-8)
    dsp.mix_into(st, to_stereo(land) * _g(-5), n_of(L))
    return Out(st, -4.0, 0.0)


@_sfx("sign_creak", family="sign", space=0.8)
def _sign_creak(dur, p, rng):
    """A hanging wooden sign swinging on iron rings: two creaks at the ends of its swing."""
    n = _N(2.6)
    out = np.zeros(n)
    for k, tt in enumerate((0.0, rng.uniform(1.1, 1.35))):
        L = rng.uniform(0.45, 0.7)
        m = _N(L)
        tm = t_axis(m)
        sw = np.sin(np.pi * tm / L) ** 1.4
        sq = dsp.friction(m, 200 + 380 * sw * rng.uniform(0.8, 1.2), rng, jitter=0.18,
                          body=[(rng.uniform(950, 1200), 11, 1.0), (rng.uniform(1900, 2300), 13, 0.5), (3100, 15, 0.25)])
        gr = dsp.friction(m, 30 + 40 * sw, rng, jitter=0.4, body=[(260, 6, 1.0), (600, 8, 0.5)])
        place(out, (_pk(sq) * _g(-4) + _pk(gr)) * sw, tt, _g(-3 * k))
    return Out(out, -4.0, 0.0)


@_sfx("dog_bark", family="dog", space=0.0)
def _dog_bark(dur, p, rng):
    """A village dog barking far off across the snow (count 1-3, dist 0..1)."""
    cnt = int(p.get("count", rng.integers(1, 4)))
    dist = _clip01(p.get("dist", 0.8))
    n = _N(0.5 * cnt + 1.2)
    out = np.zeros(n)
    tt = 0.0
    for k in range(cnt):
        L = rng.uniform(0.11, 0.17)
        m = _N(L + 0.05)
        tm = t_axis(m)
        f = rng.uniform(380, 460) * (1 + 0.35 * np.exp(-tm / 0.025)) * (1 - 0.25 * tm / L)
        src = _pulses(m, f, rng, 0.05, 0.3, 0.3)
        v = _formants(src, [(650, 200, 0), (1450, 300, -3), (2600, 450, -9)])
        b = _formants(white(m, rng), [(800, 300, 0), (1900, 500, -4)])
        e = np.clip(tm / 0.008, 0, 1) * np.clip((L - tm) / 0.04, 0, 1)
        place(out, (_pk(v) + _pk(b) * _g(-8)) * e, tt, _g(-2 * k))
        tt += rng.uniform(0.28, 0.45)
    out = sos(out, "lowpass", 3800 - 2600 * dist, 2)
    st = space_tail(out, "village", -2.0 - 4 * (1 - dist))
    return Out(st, -10.0 * dist, 0.0)


def space_tail(x, kind, wet_db):
    from .common import space
    return space(x, kind, wet_db=wet_db, dry=1.0)


@_sfx("crow_caw", family="crow", space=0.0)
def _crow_caw(dur, p, rng):
    """A crow in the cold forest: harsh nasal caws (count 1-4), distant (dist 0..1)."""
    cnt = int(p.get("count", rng.integers(2, 5)))
    dist = _clip01(p.get("dist", 0.6))
    n = _N(0.55 * cnt + 1.6)
    out = np.zeros(n)
    tt = 0.0
    base = rng.uniform(470, 560)
    for k in range(cnt):
        L = rng.uniform(0.24, 0.36)
        m = _N(L + 0.05)
        tm = t_axis(m)
        u = np.clip(tm / L, 0, 1)
        f = base * (0.9 + 0.2 * np.sin(np.pi * u) - 0.12 * u) * (1 + 0.04 * smooth_noise(m, 30, rng))
        src = _pulses(m, f, rng, 0.06, 0.35, 0.45)
        v = _formants(src, [(1150, 260, 0), (1850, 300, -2), (2900, 450, -7)])
        b = _formants(white(m, rng), [(1300, 400, 0), (2400, 600, -3)])
        e = np.clip(tm / 0.02, 0, 1) * np.clip((L - tm) / 0.06, 0, 1)
        place(out, (_pk(v) + _pk(b) * _g(-6)) * e, tt, _g(-1.5 * k))
        tt += L + rng.uniform(0.18, 0.32)
    out = sos(out, "lowpass", 5200 - 3000 * dist, 2)
    st = space_tail(out, "snow_forest", -1.0 - 5 * (1 - dist))
    return Out(st, -9.0 * dist, 0.0)


@_sfx("crow_flap", family="crow", space=0.0)
def _crow_flap(dur, p, rng):
    """A crow taking off: wing beats (soft 'whup's) receding."""
    n = _N(1.4)
    out = np.zeros(n)
    tt = 0.0
    a = 0.0
    for k in range(rng.integers(5, 8)):
        m = _N(0.09)
        w = bandpass(pink(m, rng), 180, 1400, 2) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2
        place(out, _pk(w), tt, _g(a))
        tt += rng.uniform(0.12, 0.17)
        a -= 1.8
    st = space_tail(sos(out, "lowpass", 3000, 2), "snow_forest", -4.0)
    return Out(st, -8.0, 0.0)


@_sfx("owl_hoot", family="owl", space=0.0)
def _owl_hoot(dur, p, rng):
    """A tawny owl at dusk, far in the trees: 'hoo ... hu-hoooo'."""
    n = _N(3.0)
    out = np.zeros(n)
    for (tt, L, f0, a) in ((0.0, 0.42, 395, 0.0), (1.05, 0.12, 410, -5), (1.25, 0.75, 400, -1)):
        m = _N(L + 0.05)
        tm = t_axis(m)
        u = np.clip(tm / L, 0, 1)
        f = f0 * (1 + 0.04 * np.sin(np.pi * u) - 0.03 * u)
        v = np.sin(TWO_PI * np.cumsum(f) / SR) + 0.08 * np.sin(2 * TWO_PI * np.cumsum(f) / SR)
        v *= (1 + 0.15 * np.sin(TWO_PI * 22 * tm)) if L > 0.5 else 1.0
        e = np.sin(np.pi * u) ** 0.8
        place(out, v * e + 0.04 * bandpass(white(m, rng), 300, 900, 2) * e, tt, _g(a))
    st = space_tail(sos(out, "lowpass", 1800, 2), "clearing", -2.0)
    return Out(st, -8.0, 0.0)


@_sfx("bird_chirp", family="bird", space=0.0)
def _bird_chirp(dur, p, rng):
    """A small winter bird at dawn, far away: a short high warbled phrase."""
    n = _N(1.6)
    out = np.zeros(n)
    tt = 0.0
    for k in range(rng.integers(4, 8)):
        L = rng.uniform(0.04, 0.11)
        m = _N(L)
        tm = t_axis(m)
        f0 = rng.uniform(3000, 5800)
        f = f0 * (1 + rng.uniform(-0.25, 0.25) * tm / L) * (1 + 0.04 * np.sin(TWO_PI * rng.uniform(40, 90) * tm))
        v = np.sin(TWO_PI * np.cumsum(f) / SR) * np.sin(np.pi * tm / L) ** 2
        place(out, v, tt, _g(-rng.uniform(0, 6)))
        tt += L + rng.uniform(0.02, 0.09)
    st = space_tail(out, "clearing", -4.0)
    return Out(st, -12.0, 0.0)


@_sfx("branch_creak", family="branch", space=0.0)
def _branch_creak(dur, p, rng):
    """A frozen tree creaking in the cold (slow stick-slip, woody body), far (dist 0..1)."""
    dist = _clip01(p.get("dist", 0.6))
    L = rng.uniform(0.9, 1.8)
    n = _N(L + 0.3)
    t = t_axis(n)
    sw = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 1.2
    x = dsp.friction(n, 20 + 55 * sw * rng.uniform(0.7, 1.3) + 10 * smooth_noise(n, 1.5, rng), rng, jitter=0.4,
                     body=[(rng.uniform(140, 190), 5, 1.0), (rng.uniform(300, 380), 6, 0.8), (rng.uniform(650, 800), 8, 0.45),
                           (1500, 10, 0.2)])
    x = sos(_pk(x) * sw, "lowpass", 3500 - 2000 * dist, 2)
    st = space_tail(x, "snow_forest", -3.0 - 3 * (1 - dist))
    return Out(dsp.pan_stereo(st, rng.uniform(-0.8, 0.8)), -8.0 * dist, 0.0)


@_sfx("snow_plop", family="snow_plop", space=0.0)
def _snow_plop(dur, p, rng):
    """A clump of snow sliding off a branch: brief sift, a soft 'pff' landing, powder."""
    dist = _clip01(p.get("dist", 0.5))
    n = _N(1.2)
    out = np.zeros(n)
    m = _N(0.3)
    sift = bandpass(white(m, rng), 2500, 9000, 2) * np.linspace(0, 1, m) ** 2
    place(out, _pk(sift), 0.0, _g(-14))
    land = _pk(_burst(_N(0.15), rng, 120, 1100, t60=0.06, attack=0.004)) + _pk(_crunch(_N(0.15), rng, np.exp(-t_axis(_N(0.15)) / 0.03), 3000, 600, 6000)) * _g(-6)
    place(out, land, 0.3, 1.0)
    place(out, _pk(_spray(_N(0.6), rng, 0.4, 2500, 9000)), 0.31, _g(-12))
    out = sos(out, "lowpass", 6000 - 3500 * dist, 2)
    st = space_tail(out, "snow_forest", -6.0)
    return Out(dsp.pan_stereo(st, rng.uniform(-0.9, 0.9)), -9.0 * dist, 0.0)


@_sfx("lantern_light", family="lantern_light", space=0.8)
def _lantern_light(dur, p, rng):
    """Old Red lights the last lantern: a match struck (rasp, crack), the wick catches with a
    soft 'fwup' (sync), the little glass door clicks shut."""
    n = _N(2.0)
    t = t_axis(n)
    out = np.zeros(n)
    ns = _N(0.08)
    grit = bandpass(crackle(ns, 2200, rng, amp_spread=0.9), 1800, 9000, 2) * np.clip(t_axis(ns) / 0.05, 0, 1)
    place(out, _pk(grit), 0.0, _g(-6))
    place(out, _pk(_click(rng, 3000, 0.002)), 0.06, _g(-4))
    nf = _N(0.5)
    fl = tv_lowpass(white(nf, rng), lambda x: 1800 + 5000 * math.exp(-x / 0.08), q=0.6, block=64)
    fl = sos(fl, "highpass", 300, 2) * np.clip(t_axis(nf) / 0.006, 0, 1) * np.exp(-t_axis(nf) / 0.15)
    place(out, _pk(fl), 0.065, _g(-7))
    sync = 0.55
    nw = _N(0.9)
    tw = t_axis(nw)
    wk = tv_lowpass(white(nw, rng), lambda x: 300 + 1500 * math.exp(-x / 0.12), q=0.7, block=64)
    wk = sos(wk, "highpass", 90, 2) * np.clip(tw / 0.03, 0, 1) * np.exp(-tw / 0.35) * _flutter(nw, rng, 12, 0.4)
    place(out, _pk(wk), sync, _g(-2))
    place(out, _pk(_hit(rng, [2900, 4600, 6800], [0.06, 0.05, 0.03], click=0.8)), sync + 0.75, _g(-12))
    place(out, _pk(_hit(rng, [3800, 5900], [0.25, 0.15], click=0.3, n=_N(0.4))), sync + 0.751, _g(-20))
    tail = bandpass(pink(n, rng), 200, 1200, 2) * np.clip((t - sync) / 0.3, 0, 1) * _flutter(n, rng, 12, 0.5) * np.exp(-np.maximum(t - sync, 0) / 1.0)
    out += _pk(tail) * _g(-18)
    return Out(out, -3.0, sync)


# ============================================================================ Bass graphics (s01, s06, s11)
@_sfx("ink_draw", kind="sustained", norm="int", default_dur=1.4, space=0.5, family="graphic")
def _ink_draw(dur, p, rng):
    """The path drawn as a cut-paper line: a soft dry brush / blade drag on paper, the stroke
    speeding up and easing out."""
    n = _N(dur)
    t = t_axis(n)
    u = np.clip(t / dur, 0, 1)
    sp = np.sin(np.pi * u) ** 0.8 * (0.8 + 0.2 * smooth_noise(n, 3, rng))
    tooth = bandpass(_grains(n, rng, 2500, sp, 0.7), 1200, 7000, 2)
    hiss = bandpass(pink(n, rng), 700, 5000, 2) * sp
    body = bandpass(pink(n, rng), 150, 600, 2) * sp
    x = _pk(tooth) * sp + _pk(hiss) * _g(-6) + _pk(body) * _g(-14)
    return Out(_wide(x, rng, 0.2), 0.0, 0.0)


@_sfx("paper_pop", family="graphic", space=0.5)
def _paper_pop(dur, p, rng):
    """A cut-paper shape snapping into place: soft card 'tok' + crisp paper snap."""
    n = _N(0.4)
    out = np.zeros(n)
    place(out, _pk(_thump(_N(0.1), 380, 210, 0.006, 0.03)), 0.0, 1.0)
    place(out, _pk(_burst(_N(0.03), rng, 1800, 7500, t60=0.01, attack=0.0003)), 0.0, _g(-4))
    place(out, _pk(_burst(_N(0.08), rng, 400, 3000, t60=0.04, attack=0.002)), 0.006, _g(-9))
    return Out(out, -4.0, 0.0)


@_sfx("paper_slide", kind="sustained", norm="int", default_dur=2.0, space=0.5, family="graphic")
def _paper_slide(dur, p, rng):
    """A paper shape gliding along the line: a faint smooth slide."""
    n = _N(dur)
    t = t_axis(n)
    e = np.clip(t / 0.2, 0, 1) * np.clip((dur - t) / 0.3, 0, 1)
    x = bandpass(pink(n, rng), 900, 5000, 2) * e * (0.85 + 0.15 * smooth_noise(n, 2, rng))
    return Out(x, 0.0, 0.0)


@_sfx("stakes_pop", family="graphic", space=0.5)
def _stakes_pop(dur, p, rng):
    """Stakes popping up along both sides of the path (staggered, out-back): small woody tocks
    alternating left/right."""
    cnt = int(p.get("count", 10))
    span = float(p.get("span", 0.7))
    n = _N(span + 0.5)
    out = np.zeros((n, 2))
    for k in range(cnt):
        tt = span * (k / max(cnt - 1, 1)) ** 0.85 + rng.uniform(-0.01, 0.01)
        x = _pk(_hit(rng, [rng.uniform(520, 700), rng.uniform(1250, 1500), rng.uniform(2300, 2800)], [0.05, 0.035, 0.025], click=0.8, n=_N(0.12)))
        x += _pk(_burst(_N(0.03), rng, 2000, 7000, t60=0.008)) * _g(-10)
        dsp.mix_into(out, pan_curve(x, (-0.55 if k % 2 else 0.55) * rng.uniform(0.7, 1.0)), n_of(max(0.0, tt)), _g(-rng.uniform(0, 4) - 4 * k / cnt))
    return Out(out, -3.0, 0.0)


@_sfx("thicket_grow", family="graphic", space=0.5)
def _thicket_grow(dur, p, rng):
    """Black thickets blooming beside the path: an ink bloom (dark swelling rustle) with twig
    crackles growing outward."""
    n = _N(1.5)
    t = t_axis(n)
    e = np.clip(t / 0.5, 0, 1) ** 1.5 * np.exp(-np.maximum(t - 0.55, 0) / 0.35)
    x = bandpass(pink(n, rng), 120, 1800, 2) * e
    tw = dsp.resonator_bank(_grains(n, rng, 260, e, 1.0), [900, 1900, 3200], [6, 8, 9], [1.0, 0.7, 0.4])
    st = np.stack([_pk(x) + _pk(tw) * _g(-8), np.roll(_pk(x), 400) + _pk(np.roll(tw, 900)) * _g(-8)], axis=1)
    return Out(st, -2.0, 0.0)


@_sfx("eyes_glint", family="eyes", space=0.3)
def _eyes_glint(dur, p, rng):
    """Eyes opening in the dark: a low intake of air and a soft cold glint (two beating glassy
    partials). low 0/1 (wolf: lower glint)."""
    low = int(p.get("low", 0))
    n = _N(2.0)
    t = t_axis(n)
    f = 1046.5 if low else 2093.0
    gl = (np.sin(TWO_PI * f * t) + 0.8 * np.sin(TWO_PI * (f * 1.003 + 1.7) * t) + 0.25 * np.sin(TWO_PI * f * 2.76 * t))
    gl *= np.clip(t / 0.06, 0, 1) * np.exp(-t / 0.7)
    air = _swish(n, rng, 250, 900, q=0.7) * np.clip(t / 0.35, 0, 1) * np.exp(-np.maximum(t - 0.35, 0) / 0.25)
    st = np.stack([_pk(gl) * _g(-3) + _pk(air) * _g(-9), _pk(np.roll(gl, 37)) * _g(-3) + _pk(air) * _g(-9)], axis=1)
    return Out(st, -6.0, 0.0)


@_sfx("eyes_out", family="eyes", space=0.3)
def _eyes_out(dur, p, rng):
    """Eyes blinking out: a short soft downward blip, a breath of air closing."""
    n = _N(0.6)
    t = t_axis(n)
    f = 1800 * np.exp(-t / 0.08) + 300
    x = np.sin(TWO_PI * np.cumsum(f) / SR) * np.clip(t / 0.005, 0, 1) * np.exp(-t / 0.06)
    x += 0.3 * bandpass(white(n, rng), 600, 3000, 2) * np.exp(-t / 0.05)
    return Out(_wide(x, rng, 0.3), -8.0, 0.0)


@_sfx("paper_swing", family="graphic", space=0.4)
def _paper_swing(dur, p, rng):
    """The top-down world tilting into a side view: a big sheet of paper swinging through the
    air (slow low swish) and settling with a soft flap."""
    n = _N(1.8)
    t = t_axis(n)
    u = np.clip(t / 1.3, 0, 1)
    e = np.sin(np.pi * u) ** 1.3
    x = _swish(n, rng, 160, 700, q=0.6) * e
    x += 0.4 * bandpass(pink(n, rng), 700, 3000, 2) * e * (0.6 + 0.4 * np.abs(smooth_noise(n, 18, rng)))
    place(x, _pk(_burst(_N(0.12), rng, 120, 900, t60=0.06)) * 0.6, 1.3)
    return Out(pan_curve(_pk(x), np.linspace(-0.3, 0.3, n)), -2.0, 0.0)


@_sfx("letter_fall", family="graphic", space=0.8)
def _letter_fall(dur, p, rng):
    """A tall cut-paper letter tipping over into the snow: a card swish, then the flat 'fwap'
    landing (sync ~0.32 s) with a puff of powder."""
    n = _N(1.1)
    out = np.zeros(n)
    sync = rng.uniform(0.28, 0.36)
    m = _N(sync)
    sw = _swish(m, rng, 300, 1500, q=0.7) * np.linspace(0, 1, m) ** 2
    place(out, _pk(sw), 0.0, _g(-8))
    flap = _pk(_burst(_N(0.1), rng, 140, 2500, t60=0.035, attack=0.001)) + _pk(_thump(_N(0.2), 160, 90, 0.01, 0.06)) * _g(-5)
    place(out, flap, sync, 1.0)
    place(out, _pk(_spray(_N(0.6), rng, 0.4, 2000, 8000)), sync + 0.01, _g(-12))
    return Out(out, -2.0, sync)


@_sfx("grid_tick", family="graphic", space=0.4)
def _grid_tick(dur, p, rng):
    """A row of paper triangles snapping into the grid: a crisp ripple of tiny paper snaps."""
    n = _N(0.35)
    out = np.zeros((n, 2))
    k = int(p.get("count", 7))
    for i in range(k):
        x = _pk(_burst(_N(0.02), rng, 1800, 8000, t60=0.006, attack=0.0002)) + _pk(_thump(_N(0.04), 520, 330, 0.004, 0.012)) * _g(-6)
        dsp.mix_into(out, pan_curve(x, -0.7 + 1.4 * i / max(k - 1, 1)), n_of(0.012 * i), _g(-rng.uniform(0, 4)))
    return Out(out, -6.0, 0.0)


@_sfx("grid_pulse", family="graphic", hit=True, space=0.0)
def _grid_pulse(dur, p, rng):
    """The grid of winters pulses once: a deep soft boom with a paper 'breath'."""
    n = _N(2.6)
    t = t_axis(n)
    x = _pk(_thump(n, 75, 38, 0.05, 1.1)) + 0.25 * _pk(sos(saturate(_thump(n, 75, 38, 0.05, 1.1) * 3, 2), "bandpass", (90, 400), 2))
    air = _swish(n, rng, 200, 1200, q=0.6) * np.clip(t / 0.15, 0, 1) * np.exp(-t / 0.4)
    st = to_stereo(x) + _wide(_pk(air) * _g(-12), rng, 0.6)
    return Out(st, 0.0, 0.0)


@_sfx("flatten", family="graphic", space=0.3)
def _flatten(dur, p, rng):
    """The live world flattening into cut paper (or back): a dry, papery swish that snaps."""
    n = _N(1.3)
    t = t_axis(n)
    u = np.clip(t / 0.9, 0, 1)
    e = u ** 2 * (u < 1) + (u >= 1) * np.exp(-(t - 0.9) / 0.05)
    x = _swish(n, rng, 500, 3500, q=0.7, color="white") * e
    place(x, _pk(_burst(_N(0.04), rng, 1200, 7000, t60=0.012, attack=0.0003)), 0.9, 0.8)
    return Out(_wide(_pk(x), rng, 0.4), -4.0, 0.9)


@_sfx("white_swell", family="flash", space=0.0)
def _white_swell(dur, p, rng):
    """A soft airy swell into white (the dip to snow-white: 'years pass'), sync at its crest."""
    L = float(p.get("length", 2.0))
    n = _N(L + 1.5)
    t = t_axis(n)
    env = np.where(t < L / 2, (t / (L / 2)) ** 2, np.exp(-(t - L / 2) / (L * 0.4)))
    x = bandpass(pink(n, rng), 1500, 9000, 2) * env
    x += 0.4 * bandpass(pink(n, rng), 300, 1200, 2) * env
    return Out(_wide(x, rng, 0.7), -6.0, L / 2)


# ============================================================================ preview list (QA)
PREVIEWS = [
    ("snow_step", {}), ("snow_step", dict(pace="run")), ("snow_step", dict(weight=0.7)), ("snow_step", dict(pace="back")),
    ("snow_wade", {}), ("snow_scramble", {}), ("snow_skid", {}), ("snow_skid", dict(who="wolf")), ("fall_deep_snow", {}),
    ("girl_breath_run", dict(_dur=4.0)), ("girl_gasp", {}), ("cloth_rustle", {}), ("hood_up", {}), ("ribbon_tie", {}),
    ("basket_handle", {}), ("basket_creak", {}), ("kneel_snow", {}), ("fur_touch", {}),
    ("wolf_paw", {}), ("wolf_paw", dict(pace="gallop")), ("wolf_huff", dict(double=1)), ("wolf_breath", dict(_dur=6.0)),
    ("wolf_pant", dict(_dur=3.0)), ("wolf_growl", dict(_dur=4.0)), ("wolf_snarl", {}), ("wolf_bite", {}), ("wolf_yelp", {}),
    ("wolf_wounded", dict(_dur=9.0)), ("wolf_whine", {}), ("wolf_settle", {}), ("wolf_land", {}), ("wolf_leap", {}),
    ("chitin_click", {}), ("spider_skitter", dict(_dur=2.0)), ("thread_creak", {}), ("leg_stab", {}), ("spider_hiss", {}),
    ("spider_shriek", {}), ("spider_drop", {}), ("spider_eyes", {}),
    ("basket_tumble", {}), ("bread_thump", {}), ("bottle_roll", {}), ("bottle_clink", {}), ("lantern_roll", {}),
    ("lantern_smash", {}), ("fire_whoosh", {}), ("fire_roar", dict(_dur=4.0)), ("embers", dict(_dur=4.0)), ("fire_flare", {}),
    ("door_wood", {}), ("door_wood", dict(force=0.4)), ("gate_creak", {}), ("flame_flutter", dict(_dur=3.0)), ("hood_fall", {}),
    ("sign_creak", {}), ("dog_bark", {}), ("crow_caw", {}), ("crow_flap", {}), ("owl_hoot", {}), ("bird_chirp", {}),
    ("branch_creak", {}), ("snow_plop", {}), ("lantern_light", {}),
    ("ink_draw", dict(_dur=1.4)), ("paper_pop", {}), ("paper_slide", dict(_dur=2.0)), ("stakes_pop", {}), ("thicket_grow", {}),
    ("eyes_glint", {}), ("eyes_glint", dict(low=1)), ("eyes_out", {}), ("paper_swing", {}), ("letter_fall", {}), ("grid_tick", {}),
    ("grid_pulse", {}), ("flatten", {}), ("white_swell", {}),
]
