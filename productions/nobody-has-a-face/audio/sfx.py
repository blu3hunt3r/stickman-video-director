"""SFX catalog for "Nobody Has a Face" - every name in engine/API.md section 11, procedurally.

    render(name, dur=None, params=None, seed=0) -> float32 (n, 2) at 48 kHz

Level convention (library style): every sound renders at the same reference loudness,
REF_LUFS = -16 (about narration level): one-shots by their loudest 400 ms (max momentary
loudness), sustained textures by BS.1770 integrated loudness. A cue's gain_db then places
it in the mix (S01 uses bulb_hum -14 dB, bulb_creak -16 dB, ...). Big designed hits get a
small positive trim so gain 0 really is big. Param-dependent level (footstep weight, thunder
distance, impact/whoosh size) is applied on top of the normalisation.

Design: layered transient + body + tail, band-limited per source, seed-based variation
(different seeds = different takes), fades on every edge. match_strike ignores the seed:
it is the signature sound and is sample-identical on every call.
"""
from __future__ import annotations

import math

import numpy as np

from . import dsp
from .dsp import (SR, TWO_PI, ar_env, bandpass, biquad, crackle, db2lin, exp_env, fade, mix_into,
                  modal, n_of, onepole_lp, pan_mono, pink, brown, resonator_bank, saturate, saw,
                  sine, smooth_noise, sos, t_axis, to_stereo, tv_bandpass, tv_lowpass, white)

REF_LUFS = -16.0
PEAK_CAP_DBTP = -4.0         # one-shots: loudness-normalised, but never above this true peak at gain 0
HIT_PEAK_CAP_DBTP = -1.0     # designed hits (braam, impact, stinger, ...) may go hotter
_REG: dict = {}
_CACHE: dict = {}


def _sfx(name, kind="oneshot", norm="max", default_dur=None, space=1.0, hit=False, trim=0.0):
    """Register a catalog entry. space: factor for the mixer's per-scene reverb send (0 = the
    sound carries its own acoustics). hit: designed hit, exempt from VO ducking."""
    def deco(fn):
        _REG[name] = dict(fn=fn, kind=kind, norm=norm, default_dur=default_dur, space=space, hit=hit,
                          trim=trim, name=name)
        return fn
    return deco


def names():
    return sorted(_REG)


def spec(name):
    return _REG[name]


def exists(name):
    return name in _REG


def _measure(x, mode):
    if mode == "int" and len(x) >= n_of(0.8):
        v = dsp.loudness_integrated(x)
        if np.isfinite(v):
            return v
    y = x if len(x) >= n_of(0.4) else dsp.pad_to(x, n_of(0.4))
    _, lk = dsp.loudness_curve(y, win=0.4, hop=0.05)
    return float(np.max(lk)) if len(lk) else -70.0


def render(name, dur=None, params=None, seed=0):
    """Render a catalog sound as float32 (n, 2). dur: length for sustained sounds (exact);
    for one-shots an optional maximum (truncated with a 30 ms fade)."""
    if name not in _REG:
        raise KeyError(f"unknown SFX {name!r}")
    sp = _REG[name]
    p = dict(params or {})
    if name == "match_strike":
        seed, p = 307, {}                         # the signature: identical every call
    key = (name, None if dur is None else round(float(dur), 4), tuple(sorted((k, str(v)) for k, v in p.items())), int(seed))
    if key in _CACHE:
        return _CACHE[key].copy()
    rng = np.random.default_rng(dsp.stable_seed("sfx", name, seed))
    d = dur if (dur is not None and sp["kind"] == "sustained") else sp["default_dur"]
    if sp["kind"] == "sustained":
        d = max(0.05, float(d if d is not None else 3.0))
    res = sp["fn"](d, p, rng)
    extra = 0.0
    if isinstance(res, tuple):
        res, extra = res
    x = to_stereo(np.asarray(res, dtype=np.float64))
    x = sos(x, "highpass", 16.0, 2)                 # DC / subsonic blocker
    if sp["kind"] == "sustained":
        x = dsp.pad_to(x, n_of(d))
    else:
        x = fade(x, 0.00015, 0.012, shape="lin")
    lvl = _measure(x, sp["norm"])
    if np.isfinite(lvl) and lvl > -120:
        x = x * db2lin(REF_LUFS + sp["trim"] - lvl)
    if sp["kind"] == "oneshot":
        # short transients normalised by a 400 ms loudness window would get enormous peaks: cap
        # the true peak (like a peak-normalised library) - dense sounds stay loudness-normalised.
        # The parameter-dependent level (weight, size, distance) is applied after the cap so the
        # contrast between a light and a heavy step survives.
        cap = HIT_PEAK_CAP_DBTP if sp["hit"] else PEAK_CAP_DBTP
        tp = dsp.true_peak_db(x)
        if tp > cap:
            x = x * db2lin(cap - tp)
    x = x * db2lin(extra)
    if sp["kind"] == "oneshot":
        if dur is not None and dur > 0 and n_of(dur) < len(x):
            x = fade(x[:n_of(dur)], 0.0, min(0.03, dur / 3))
    else:
        x = fade(x, 0.0005, 0.002)
    out = x.astype(np.float32)
    if len(_CACHE) > 400:
        _CACHE.clear()
    _CACHE[key] = out
    return out.copy()


# ============================================================================ helpers
def _N(t):
    return max(1, n_of(t))


def _thump(n, f0, f1, tp, t60, attack=0.0015):
    """Sine 'kick' with exponential pitch drop f0 -> f1 (time constant tp)."""
    t = t_axis(n)
    f = f1 + (f0 - f1) * np.exp(-t / max(tp, 1e-4))
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * exp_env(n, t60)
    k = min(n, n_of(attack))
    if k > 1:
        y[:k] *= np.linspace(0, 1, k)
    return y


def _burst(n, rng, lo=None, hi=None, t60=0.05, attack=0.0005, color="white", order=2, hold=0.0):
    x = white(n, rng) if color == "white" else pink(n, rng) if color == "pink" else brown(n, rng)
    if lo and hi:
        x = bandpass(x, lo, hi, order)
    elif hi:
        x = sos(x, "lowpass", hi, order)
    elif lo:
        x = sos(x, "highpass", lo, order)
    return x * ar_env(n, attack, t60, hold=hold)


def _click(rng, hp=2500.0, t60=0.004, n=None):
    n = n or _N(t60 * 2 + 0.002)
    return _burst(n, rng, lo=hp, t60=t60, attack=0.0001)


def _hit(rng, freqs, t60s, amps=None, spread=0.0, n=None, click=0.3, click_hp=3000.0):
    """Struck object: modal partials (random phases) + a contact click."""
    freqs = np.asarray(freqs, dtype=np.float64) * (1.0 + spread * rng.uniform(-1, 1, len(freqs)))
    t60s = np.broadcast_to(np.asarray(t60s, dtype=np.float64), freqs.shape)
    amps = np.ones(len(freqs)) / np.sqrt(np.arange(1, len(freqs) + 1)) if amps is None else np.asarray(amps, dtype=np.float64)
    amps = amps * rng.uniform(0.6, 1.0, len(freqs))
    n = n or _N(float(np.max(t60s)) * 1.1 + 0.01)
    y = modal(freqs, t60s, amps, n, phases=rng.uniform(0, TWO_PI, len(freqs)))
    if click:
        c = _click(rng, click_hp, 0.003)
        y[:len(c)] += click * c[:n] * np.max(np.abs(y[:n_of(0.02)]) + 1e-9) / max(1e-9, np.max(np.abs(c)))
    return y


def _place(out, x, t, gain=1.0):
    return mix_into(out, x, n_of(t), gain)


def _sum(*xs):
    """Sum arrays of different lengths (zero-padded to the longest)."""
    n = max(len(x) for x in xs)
    out = np.zeros((n,) + np.shape(xs[0])[1:])
    for x in xs:
        out[:len(x)] += x
    return out


def _drop(rng, f0, d, chirp=0.6):
    """Water droplet / bubble: rising-pitch damped sinusoid."""
    m = _N(d * 5)
    tt = t_axis(m)
    f = f0 * (1.0 + chirp * (1.0 - np.exp(-tt / (d * 0.8))))
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * np.exp(-tt / d)
    k = min(m, 6)
    y[:k] *= np.linspace(0, 1, k)
    return y


def _splash(n, rng, size=0.6, t0=0.0):
    """Foot / body into a shallow puddle: slap + spray of droplets + 'shh' body."""
    out = np.zeros(n)
    _place(out, _burst(_N(0.05), rng, 250, 6500, t60=0.035, attack=0.0008), t0, 0.9)
    _place(out, _burst(_N(0.3), rng, 900, 5000, t60=0.11 + 0.08 * size, attack=0.004), t0 + 0.003, 0.5 + 0.3 * size)
    k = int(8 + 34 * size)
    for tt in t0 + 0.004 + rng.exponential(0.03 + 0.03 * size, k):
        f0 = math.exp(rng.uniform(math.log(1300), math.log(5200)))
        _place(out, _drop(rng, f0, rng.uniform(0.003, 0.009)), tt, rng.uniform(0.05, 0.25))
    return out


def _gust_env(n, rng, rise=0.4, smooth=4.0):
    t = np.linspace(0, 1, n)
    e = np.where(t < rise, np.sin(0.5 * np.pi * t / rise) ** 2, np.cos(0.5 * np.pi * (t - rise) / (1 - rise)) ** 1.5)
    return e * (1.0 + 0.25 * smooth_noise(n, smooth, rng))


def _stereo_scatter(parts):
    """parts: list of (mono, pan) -> stereo sum."""
    n = max(len(p[0]) for p in parts)
    out = np.zeros((n, 2))
    for x, pan in parts:
        out[:len(x)] += pan_mono(x, pan)
    return out


def _wide(x, rng, amount=0.6):
    return dsp.decorrelate(x, rng, amount=amount)


def _felt_piano_note(f0, n, vel=0.8, rng=None):
    """Compact felt-piano tone (shared idea with score.py, kept local to avoid import cycles)."""
    t = t_axis(n)
    out = np.zeros(n)
    B = 0.00035
    for k in range(1, 14):
        fk = k * f0 * math.sqrt(1 + B * k * k)
        if fk > 9000:
            break
        a = (1.0 / k ** 1.4) * abs(math.sin(math.pi * k / 7.3)) * math.exp(-k / (3 + 6 * vel))
        t60 = 7.0 / (1 + 0.35 * k) * (220.0 / max(f0, 60)) ** 0.3
        out += a * np.sin(TWO_PI * fk * t) * np.power(10.0, -3 * t / t60)
    out[:_N(0.002)] *= np.linspace(0, 1, _N(0.002))
    return out


# ============================================================================ the signature
@_sfx("match_strike", space=0.0, hit=True)
def _match_strike(dur, p, rng):
    """Head dragged across the striker (gritty scratch) -> ignition crack + sparks -> sulfur
    flare 'fssht' with a low whoomp -> settling flame. Deterministic (seed fixed to 307)."""
    n = _N(1.35)
    out = np.zeros(n)
    # 1) scratch 0-60 ms: granular friction across the strip, rising
    ns = _N(0.075)
    grit = crackle(ns, 2600, rng, amp_spread=0.9)
    grit = bandpass(grit, 1800, 9000, 2) * 3.0 + bandpass(white(ns, rng), 2500, 8000, 2) * 0.35
    rasp = bandpass(white(ns, rng), 700, 2400, 2) * 0.35
    env = np.clip(t_axis(ns) / 0.045, 0, 1) ** 1.6 * np.exp(-np.maximum(t_axis(ns) - 0.05, 0) / 0.008)
    _place(out, (grit + rasp) * env, 0.0, 1.0)
    # 2) ignition at 52 ms: crack + spark crackles
    t_ig = 0.052
    _place(out, _click(rng, 3000, 0.0025, _N(0.008)), t_ig, 1.3)
    sp = crackle(_N(0.22), 160, rng, amp_spread=1.0)
    sp = sos(sp, "highpass", 2500, 2) * exp_env(_N(0.22), 0.25)
    _place(out, sp, t_ig + 0.004, 2.2)
    # 3) flare: broadband burst whose top end closes 9 k -> 2.4 k; low body whoomp
    nf = _N(0.75)
    tf = t_axis(nf)
    fl = tv_lowpass(white(nf, rng), lambda tt: 2400 + 6600 * math.exp(-tt / 0.09), q=0.6, block=64)
    fl = sos(fl, "highpass", 350, 2)
    fl *= np.clip(tf / 0.007, 0, 1) * (0.25 + 0.75 * np.exp(-tf / 0.11)) * np.exp(-tf / 0.38)
    _place(out, fl, t_ig + 0.006, 0.95)
    body = sos(white(nf, rng), "lowpass", 650, 2) * np.clip(tf / 0.02, 0, 1) * np.exp(-tf / 0.16)
    _place(out, sos(body, "highpass", 90, 2), t_ig + 0.008, 0.9)
    # 4) settling flame: soft flickering hiss, fading by 1.3 s
    nh = _N(1.15)
    th = t_axis(nh)
    flick = 1.0 + 0.45 * smooth_noise(nh, 11.0, rng)
    flame = sos(white(nh, rng), "bandpass", (180, 1600), 2) * flick
    flame *= np.clip(th / 0.12, 0, 1) * np.exp(-th / 0.42)
    _place(out, flame, 0.17, 0.32)
    return fade(out, 0.0005, 0.08)


@_sfx("match_flare", space=0.6)
def _match_flare(dur, p, rng):
    """Flame catching / flaring up: soft 'fwump' + crackle + flicker."""
    n = _N(1.0)
    t = t_axis(n)
    nz = white(n, rng)
    x = tv_lowpass(nz, lambda tt: 300 + 2200 * math.exp(-((tt - 0.07) / 0.09) ** 2) + 500 * math.exp(-tt / 0.4), q=0.8, block=64)
    x = sos(x, "highpass", 80, 2)
    env = np.clip(t / 0.035, 0, 1) ** 1.5 * np.exp(-t / 0.33)
    x *= env * (1 + 0.4 * smooth_noise(n, 14.0, rng))
    cr = sos(crackle(n, 45, rng), "highpass", 2200, 2) * np.exp(-t / 0.3) * 2.5
    return _wide(x + cr, rng, 0.3)


@_sfx("flame_out", space=0.8)
def _flame_out(dur, p, rng):
    """A small flame dying: short breathy 'fff' whose band falls, a last flicker and tick."""
    n = _N(0.7)
    t = t_axis(n)
    x = tv_bandpass(white(n, rng), lambda tt: 2600 * math.exp(-tt / 0.12) + 380, q=0.9, block=64)
    x *= np.clip(t / 0.015, 0, 1) * np.exp(-t / 0.12)
    fl = sos(white(n, rng), "bandpass", (200, 900), 2) * (np.sin(np.pi * np.clip(t / 0.35, 0, 1)) ** 2) * 0.25
    fl *= 1 + 0.8 * smooth_noise(n, 18, rng)
    out = x + fl
    _place(out, _click(rng, 3500, 0.002), 0.21, 0.25)
    return out


@_sfx("ember_sizzle", space=0.4)
def _ember_sizzle(dur, p, rng):
    """Glowing ember in the rain: fine crackle, a faint hiss, and two 'tsss' drop hits."""
    n = _N(2.2)
    t = t_axis(n)
    cr = sos(crackle(n, 38, rng, amp_spread=1.1), "highpass", 2500, 2) * 1.6
    hiss = sos(white(n, rng), "bandpass", (4000, 11000), 2) * 0.05 * (1 + 0.5 * smooth_noise(n, 3, rng))
    out = (cr + hiss) * (np.clip(t / 0.05, 0, 1) * np.exp(-t / 1.4))
    for tt in (0.35 + rng.uniform(0, 0.2), 1.1 + rng.uniform(0, 0.3)):
        s = _burst(_N(0.3), rng, 3000, 9000, t60=0.25, attack=0.004) * 0.35
        _place(out, s, tt)
    return out


# ============================================================================ bulb
@_sfx("bulb_hum", kind="sustained", norm="int", default_dur=4.0, space=0.3)
def _bulb_hum(dur, p, rng):
    """Bare tungsten bulb on 60 Hz mains: 120 Hz filament buzz + harmonics, a little 60 Hz
    hum, slow flutter. Exact `dur`, ~15 ms fade in, ~30 ms fade out (light dies = a cut)."""
    n = _N(dur)
    t = t_axis(n)
    fl = 1.0 + 0.004 * smooth_noise(n, 0.7, rng)            # mains drift
    buzz = saturate(np.sin(TWO_PI * np.cumsum(120.0 * fl) / SR), 3.0, "tanh", asym=0.15)
    buzz = sos(buzz, "bandpass", (110, 3200), 2)
    hum = np.zeros(n)
    for k, a in ((1, 0.30), (2, 1.0), (3, 0.25), (4, 0.45), (6, 0.18), (8, 0.08)):
        hum += a * np.sin(TWO_PI * np.cumsum(60.0 * k * fl) / SR + rng.uniform(0, TWO_PI))
    flutter = 1.0 + 0.10 * smooth_noise(n, 2.2, rng) + 0.04 * smooth_noise(n, 9.0, rng)
    x = (0.55 * hum + 0.45 * buzz) * flutter
    x += 0.012 * sos(white(n, rng), "bandpass", (2000, 6000), 2) * flutter   # faint filament hiss
    st = np.stack([x, 0.92 * x + 0.08 * np.roll(x, 37)], axis=1)
    return fade(st, 0.015, 0.03, shape="lin")


@_sfx("bulb_creak", space=0.6)
def _bulb_creak(dur, p, rng):
    """The swinging bulb's hook / cord: a thin stick-slip squeak with a woody undertone."""
    n = _N(0.75 + rng.uniform(0, 0.2))
    t = t_axis(n)
    sw = np.sin(np.pi * t / (n / SR)) ** 2
    rate = 150 + 230 * sw * rng.uniform(0.8, 1.2)
    sq = dsp.friction(n, rate, rng, jitter=0.12,
                      body=[(1750 * rng.uniform(0.9, 1.1), 9, 1.0), (3050, 12, 0.6), (430, 4, 0.5)])
    low = dsp.friction(n, 45 + 30 * sw, rng, jitter=0.25, body=[(260, 3, 1.0), (620, 4, 0.5)])
    return (sq * 0.8 + low * 0.5) * sw ** 0.7


@_sfx("bulb_flicker", space=0.5)
def _bulb_flicker(dur, p, rng):
    """Filament flicker: gated 120 Hz electrical buzz with crackles at the gate edges."""
    n = _N(0.55)
    gate = np.zeros(n)
    tt = 0.0
    while tt < 0.45:
        on = rng.uniform(0.015, 0.07)
        a, b = n_of(tt), min(n, n_of(tt + on))
        gate[a:b] = rng.uniform(0.4, 1.0)
        tt += on + rng.uniform(0.01, 0.06)
    gate = onepole_lp(gate, 400)
    buzz = sos(saturate(np.sin(TWO_PI * 120 * t_axis(n)), 5.0, asym=0.2), "bandpass", (150, 5000), 2)
    edges = np.abs(np.diff(gate, prepend=0)) > 0.002
    cr = crackle(n, 120, rng) * edges * 2.0
    cr = sos(cr, "highpass", 1500, 2)
    out = buzz * gate * 0.6 + cr * 0.5
    _place(out, _hit(rng, [5200, 7400], [0.06, 0.04], n=_N(0.1), click=0.0), 0.47, 0.15)
    return out


@_sfx("bulb_pop", space=0.7)
def _bulb_pop(dur, p, rng):
    """The bulb dies: filament snap (tink), tiny implosion thup, electrical zap, glass ring."""
    n = _N(0.9)
    out = np.zeros(n)
    _place(out, _click(rng, 2500, 0.002, _N(0.01)), 0.0, 1.0)
    _place(out, _hit(rng, [3150, 5070, 7620, 9900], [0.28, 0.2, 0.14, 0.09], spread=0.03, click=0.0), 0.001, 0.55)
    _place(out, _burst(_N(0.06), rng, hi=420, t60=0.03, attack=0.001), 0.002, 0.9)
    nz = _N(0.09)
    zap = sos(saturate(np.sin(TWO_PI * 120 * t_axis(nz)), 6.0), "bandpass", (200, 6000), 2) * exp_env(nz, 0.08)
    _place(out, zap, 0.0, 0.35)
    _place(out, _hit(rng, [6100, 8300], [0.12, 0.08], click=0.0), 0.16 + rng.uniform(0, 0.05), 0.12)
    return out


# ============================================================================ footsteps
def _step(rng, weight, wet, run=False, drag=None):
    w = float(np.clip(weight, 0.0, 1.0))
    n = _N(0.75)
    out = np.zeros(n)
    pitch = rng.uniform(0.92, 1.08)
    t_heel = 0.008
    roll = (0.018 + 0.012 * w) if run else (0.045 + 0.05 * w) * rng.uniform(0.85, 1.15)
    # heel: low thump + band-limited contact
    heel = _sum(_thump(_N(0.25), (120 + 30 * w) * pitch, (62 + 10 * w) * pitch, 0.012, 0.07 + 0.08 * w) * (0.5 + 0.5 * w),
                _burst(_N(0.08), rng, 90, 1400 + 900 * w, t60=0.03 + 0.02 * w, attack=0.0006) * (0.5 + 0.6 * w))
    _place(out, heel, t_heel, 1.0)
    # sole / toe slap (brighter, smaller)
    toe = _burst(_N(0.06), rng, 400 * pitch, 5200, t60=0.022, attack=0.0004) * (0.35 + 0.25 * w)
    _place(out, toe, t_heel + roll, 1.0)
    # grit under the sole
    g = sos(crackle(_N(0.12), 380, rng), "highpass", 3000, 2) * exp_env(_N(0.12), 0.1) * 0.6
    _place(out, g, t_heel, 0.5)
    # drag / scuff of a light (limping) step
    dg = float(np.clip((0.6 - w) / 0.4, 0, 1)) if drag is None else float(drag)
    if dg > 0.01:
        m = _N(0.16)
        tt = t_axis(m)
        sc = tv_bandpass(white(m, rng), lambda x: 1400 + 2600 * x / 0.16, q=0.8, block=64)
        sc += 0.6 * dsp.friction(m, 110, rng, jitter=0.4, body=[(1800, 3, 1.0)])
        sc *= np.sin(np.pi * tt / 0.16) ** 1.5
        _place(out, sc, t_heel + roll * 0.6, 0.28 * dg)
    if wet:
        size = (0.35 + 0.5 * w) * (1.4 if run else 1.0)
        _place(out, _splash(_N(0.45), rng, size), t_heel + 0.002, 0.75 + 0.4 * w)
        if not run:   # soft squelch as the sole lifts
            sq = _burst(_N(0.12), rng, 500, 2500, t60=0.06, attack=0.01) * 0.2
            _place(out, sq, t_heel + roll + 0.12, 1.0)
    level = -9.0 * (0.75 - w) if not run else -6.0 * (0.85 - w)
    return out, level + rng.uniform(-1.0, 1.0)


@_sfx("footstep", space=1.0)
def _footstep(dur, p, rng):
    """weight 0..1 (light/short step quieter, quicker heel-toe, scuffs and drags below ~0.5;
    heavy step = deeper heel, longer roll) · wet 0/1 (puddle splash + squelch) · drag 0..1."""
    return _step(rng, p.get("weight", 0.7), int(bool(p.get("wet", 0))), False, p.get("drag"))


@_sfx("footstep_run", space=1.0)
def _footstep_run(dur, p, rng):
    """Running step: compressed heel-toe, more energy and a bigger splash (wet default 1)."""
    return _step(rng, p.get("weight", 0.85), int(bool(p.get("wet", 1))), True, p.get("drag", 0.0))


# ============================================================================ umbrella / fabric / paper
@_sfx("umbrella_open", space=0.8)
def _umbrella_open(dur, p, rng):
    """Runner slides up the shaft (ratchety metal slide) -> canopy snaps taut (fabric fwump +
    low pop) -> latch click."""
    n = _N(0.8)
    out = np.zeros(n)
    ns = _N(0.19)
    ts = t_axis(ns)
    slide = tv_bandpass(white(ns, rng), lambda x: 1500 + 4000 * x / 0.19, q=1.5, block=64)
    slide += 0.8 * dsp.friction(ns, 140 + 900 * ts / 0.19, rng, jitter=0.2, body=[(3200, 6, 1.0), (5100, 8, 0.6)])
    slide *= np.clip(ts / 0.17, 0, 1) ** 2
    _place(out, slide, 0.0, 0.45)
    t_snap = 0.19
    _place(out, _burst(_N(0.18), rng, 120, 1300, t60=0.09, attack=0.002), t_snap, 1.0)
    _place(out, _thump(_N(0.2), 120, 62, 0.02, 0.11), t_snap, 0.65)
    _place(out, _burst(_N(0.05), rng, 300, 1600, t60=0.02, attack=0.0005), t_snap + 0.004, 0.6)
    _place(out, _hit(rng, [2800, 4400, 6100], [0.05, 0.04, 0.03], click=0.4), t_snap + 0.022, 0.35)
    fl = sos(white(_N(0.3), rng), "bandpass", (300, 2400), 2) * exp_env(_N(0.3), 0.2) * (1 + 0.7 * smooth_noise(_N(0.3), 22, rng))
    _place(out, fl, t_snap + 0.03, 0.18)
    return out


@_sfx("umbrella_flap", space=0.8)
def _umbrella_flap(dur, p, rng):
    """Canopy flapping in a gust: fluttering fabric + two tension snaps + wind."""
    n = _N(1.3)
    t = t_axis(n)
    env = _gust_env(n, rng, 0.35, 3)
    rate = 11 + 6 * env
    flut = 0.5 + 0.5 * np.sign(np.sin(TWO_PI * np.cumsum(rate) / SR)) * rng.uniform(0.6, 1.0)
    flut = onepole_lp(flut, 60)
    fab = sos(white(n, rng), "bandpass", (220, 2600), 2) * flut * env
    out = fab
    for tt in (0.3 + rng.uniform(0, 0.15), 0.75 + rng.uniform(0, 0.2)):
        _place(out, _burst(_N(0.08), rng, 150, 1400, t60=0.04, attack=0.001), tt, 0.9)
    wind = sos(white(n, rng), "bandpass", (200, 900), 2) * env * 0.25
    return _wide(out + wind, rng, 0.5)


@_sfx("paper_rustle", space=0.8)
def _paper_rustle(dur, p, rng):
    """Handled paper: dense micro-crinkles in 1-8 kHz, shaped by hand motion."""
    n = _N(0.9)
    t = t_axis(n)
    motion = np.clip(0.55 + 0.6 * smooth_noise(n, 5, rng), 0, None) * np.sin(np.pi * t / (n / SR)) ** 0.7
    cr = crackle(n, 1400, rng, amp_spread=1.2)
    x = bandpass(cr, 1200, 8000, 2) * 2.0 + 0.12 * bandpass(white(n, rng), 2000, 9000, 2)
    return _wide(x * motion, rng, 0.35)


@_sfx("paper_tear", space=0.8)
def _paper_tear(dur, p, rng):
    """A rip: accelerating fibre-break impulses (rough grain) + fibrous low layer + end snap.
    size 0..1 (0.2 = a match torn from a matchbook, 1 = a sheet)."""
    size = float(p.get("size", 0.5))
    L = 0.12 + 0.45 * size
    n = _N(L + 0.15)
    t = t_axis(n)
    rate = (1500 + 3500 * np.clip(t / L, 0, 1)) * (t < L)
    imp = np.zeros(n)
    ph = np.cumsum(rate * (1 + 0.6 * rng.standard_normal(n) * 0.2)) / SR
    idx = np.nonzero(np.diff(np.floor(ph), prepend=0) > 0)[0]
    imp[idx] = np.exp(rng.normal(0, 0.7, len(idx))) * rng.choice([-1, 1], len(idx))
    grain = bandpass(imp, 900, 7000, 2) * (0.5 + 0.5 * smooth_noise(n, 30, rng))
    fib = bandpass(white(n, rng), 250, 1100, 2) * 0.3 * (t < L)
    env = np.clip(t / 0.02, 0, 1) * np.where(t < L, 0.7 + 0.3 * t / L, np.exp(-(t - L) / 0.01))
    out = (grain + fib) * env
    _place(out, _burst(_N(0.03), rng, 1200, 6000, t60=0.012), L - 0.005, 0.8)
    return out, -4.0 * (0.5 - size)


@_sfx("page_flip", space=0.8)
def _page_flip(dur, p, rng):
    """Page turning: airy swish with paper flex flutter, landing flap."""
    n = _N(0.5)
    t = t_axis(n)
    sw = tv_bandpass(white(n, rng), lambda x: 700 + 2600 * math.sin(math.pi * min(x / 0.32, 1.0)), q=0.9, block=64)
    env = np.sin(np.pi * np.clip(t / 0.32, 0, 1)) ** 1.8
    flex = 1.0 + 0.5 * np.sin(TWO_PI * 28 * t) * smooth_noise(n, 8, rng)
    out = sw * env * flex
    _place(out, _burst(_N(0.04), rng, 300, 3000, t60=0.015), 0.31, 0.7)
    return out


@_sfx("photo_pin", space=0.8)
def _photo_pin(dur, p, rng):
    """Push-pin into cork through a photo: pierce tick, dull cork thup, thumb-press creak."""
    n = _N(0.3)
    out = np.zeros(n)
    _place(out, _click(rng, 3500, 0.0015, _N(0.006)), 0.0, 0.8)
    _place(out, _burst(_N(0.06), rng, 120, 520, t60=0.025, attack=0.0008), 0.004, 1.0)
    _place(out, _thump(_N(0.06), 380, 240, 0.01, 0.03), 0.004, 0.4)
    cr = dsp.friction(_N(0.05), 300, rng, body=[(2200, 4, 1.0)]) * np.hanning(_N(0.05))
    _place(out, cr, 0.03, 0.12)
    return out


# ============================================================================ string / brush / pencil
def _twang_tone(n, f0, rng, bend=0.04, t60=0.8, bright=1.0):
    t = t_axis(n)
    f = f0 * (1 + bend * np.exp(-t / 0.04))
    ph = np.cumsum(f) / SR
    out = np.zeros(n)
    for k in range(1, 12):
        if k * f0 > 9000:
            break
        a = (1.0 / k ** 1.25) * abs(math.sin(math.pi * k * 0.13)) ** 0.5
        out += a * np.sin(TWO_PI * k * ph + rng.uniform(0, TWO_PI)) * np.power(10, -3 * t / (t60 / (1 + 0.25 * k * bright)))
    return out


@_sfx("string_twang", space=0.8)
def _string_twang(dur, p, rng):
    """A taut red string snapped / plucked against its pin: muted 'twang' with a pitch bend,
    the snap of fibre and a tiny pin rattle."""
    n = _N(1.0)
    f0 = 196.0 * rng.uniform(0.9, 1.12)
    out = _twang_tone(n, f0, rng, 0.05, 0.75)
    _place(out, _burst(_N(0.03), rng, 900, 4000, t60=0.012), 0.0, 1.2)
    _place(out, _hit(rng, [3400, 5200], [0.05, 0.04], click=0.0), 0.012, 0.2)
    _place(out, _thump(_N(0.12), 300, 180, 0.01, 0.06), 0.0, 0.25)
    return out


@_sfx("string_tighten", space=0.8)
def _string_tighten(dur, p, rng):
    """Strings pulled taut: fibrous creak rising in pitch (tension), several strings layered,
    ending in a taut 'tung'."""
    L = 1.25
    n = _N(L + 0.7)
    t = t_axis(n)
    out = np.zeros(n)
    for i in range(3):
        m = _N(L)
        tt = t_axis(m)
        r = (60 + 360 * (tt / L) ** 1.6) * rng.uniform(0.85, 1.15)
        cr = dsp.friction(m, r, rng, jitter=0.18, body=[(520 * rng.uniform(0.9, 1.1), 3, 1.0), (1250, 5, 0.6), (2600, 7, 0.3)])
        cr *= np.clip(tt / 0.3, 0, 1) * (0.6 + 0.4 * tt / L)
        _place(out, cr, i * 0.05, 2.2)
    wh = np.sin(TWO_PI * np.cumsum(300 + 600 * np.clip(t / L, 0, 1) ** 2) / SR) * np.clip(t / L, 0, 1) ** 2 * (t < L)
    out += 0.05 * wh
    _place(out, _twang_tone(_N(0.7), 330, rng, 0.02, 0.5), L, 0.35)
    _place(out, _burst(_N(0.02), rng, 1500, 5000, t60=0.01), L, 0.3)
    return out


@_sfx("brush_swish", space=0.8)
def _brush_swish(dur, p, rng):
    """Fingerprint brush dusting glass: two soft bristle strokes."""
    n = _N(0.85)
    t = t_axis(n)
    out = np.zeros(n)
    for t0, L in ((0.0, 0.34), (0.4, 0.38)):
        m = _N(L)
        tt = t_axis(m)
        s = tv_bandpass(white(m, rng), lambda x: 3500 + 3000 * x / L, q=0.7, block=64)
        s += 0.4 * sos(crackle(m, 900, rng), "highpass", 4500, 2)
        s *= np.sin(np.pi * tt / L) ** 1.3
        _place(out, s, t0, 1.0 if t0 == 0 else 0.8)
    return _wide(out, rng, 0.3)


@_sfx("pencil_scratch", kind="sustained", norm="int", default_dur=1.6, space=0.8)
def _pencil_scratch(dur, p, rng):
    """Graphite on paper: strokes of tooth-grain friction with pressure envelopes."""
    n = _N(dur)
    out = np.zeros(n)
    tt = 0.0
    while tt < dur - 0.05:
        L = rng.uniform(0.12, 0.42)
        m = _N(L)
        x = t_axis(m)
        grain = bandpass(crackle(m, 3500, rng, amp_spread=0.8), 1800, 7500, 2) * 1.5
        grain += 0.25 * bandpass(white(m, rng), 1500, 6000, 2)
        grain += 0.1 * bandpass(white(m, rng), 300, 900, 2)
        press = np.sin(np.pi * x / L) ** 0.8 * (0.8 + 0.2 * smooth_noise(m, 12, rng))
        _place(out, grain * press, tt, rng.uniform(0.6, 1.0))
        tt += L + rng.uniform(0.02, 0.12)
    return fade(out, 0.01, 0.05)


# ============================================================================ camera / radio
@_sfx("camera_shutter", space=0.8)
def _camera_shutter(dur, p, rng):
    """Press camera: shutter 'click-clack' (two modal clicks), spring tick, flashbulb 'pff'."""
    n = _N(0.45)
    out = np.zeros(n)
    _place(out, _hit(rng, [1900, 3400, 5200, 7300], [0.05, 0.04, 0.03, 0.02], spread=0.05, click=0.7), 0.0, 1.0)
    _place(out, _hit(rng, [1500, 2900, 4600], [0.06, 0.05, 0.03], spread=0.05, click=0.6), 0.045 + rng.uniform(0, 0.01), 0.8)
    _place(out, _burst(_N(0.12), rng, 300, 3200, t60=0.06, attack=0.001), 0.008, 0.5)
    sz = sos(white(_N(0.25), rng), "highpass", 5000, 2) * exp_env(_N(0.25), 0.2) * 0.08
    _place(out, sz, 0.01)
    return out


def _formant_voice(n, rng, sr=16000, f0=120.0, syl_rate=5.0, words=True):
    """Nonverbal formant babble (pulse source -> 3 moving formants), at sample rate sr."""
    t = np.arange(n) / sr
    contour = f0 * (1 + 0.08 * smooth_noise(n, 1.5, rng, sr) + 0.03 * smooth_noise(n, 6, rng, sr))
    src = dsp.pulse_train(contour, n, sr, jitter=0.01, rng=rng, harmonics=max(4, int(3800 / f0)))
    src = 0.85 * src + 0.15 * white(n, rng)          # some breath
    vowels = [(300, 870, 2240), (400, 2000, 2550), (640, 1190, 2390), (730, 1090, 2440), (500, 1500, 2500),
              (350, 1300, 2400), (450, 1700, 2600), (560, 1000, 2300)]
    nb = max(2, int(n / sr * syl_rate) + 2)
    pick = [vowels[i] for i in rng.integers(0, len(vowels), nb)]
    xs = np.linspace(0, n, nb)
    F = [np.interp(np.arange(n), xs, [v[k] * rng.uniform(0.92, 1.08) for v in pick]) for k in range(3)]
    out = np.zeros(n)
    for k, (q, g) in enumerate(((5, 1.0), (8, 0.6), (10, 0.3))):
        out += g * tv_bandpass(src, F[k], q=q, sr=sr, block=200)
    # syllable envelope with phrase gaps, plus consonant-like noise bursts at syllable onsets
    sph = np.cumsum(syl_rate * (1 + 0.3 * smooth_noise(n, 2, rng, sr))) / sr
    syl = np.clip(np.sin(np.pi * sph) ** 2, 0, 1) ** 1.3
    phrase = (smooth_noise(n, 0.7, rng, sr) > -0.45).astype(float)
    phrase = onepole_lp(phrase, 8, sr)
    if not words:
        return out
    voiced = out * (0.06 + 0.94 * syl)
    onsets = np.nonzero(np.diff(np.floor(sph)) > 0)[0]
    cons = np.zeros(n)
    lvl = np.sqrt(np.mean(voiced ** 2)) + 1e-9
    for k in onsets:
        if rng.uniform() < 0.55:
            m_ = int(sr * rng.uniform(0.02, 0.06))
            lo = rng.uniform(1800, 3500)
            b_ = dsp.bandpass(rng.standard_normal(m_), lo, min(0.45 * sr, lo * 2.2), 2, sr=sr) * np.hanning(m_)
            dsp.mix_into(cons, b_, k, 1.2 * lvl / (np.sqrt(np.mean(b_ ** 2)) + 1e-9))
    return (voiced + cons) * phrase


@_sfx("radio_static", space=0.5)
def _radio_static(dur, p, rng):
    """Police radio burst: squelch open, crackling static with a garbled, unintelligible
    formant 'voice' crushed into a 300-3400 Hz band, squelch tail (sometimes a roger tone)."""
    L = rng.uniform(0.9, 1.4)
    n = _N(L + 0.25)
    t = t_axis(n)
    out = np.zeros(n)
    _place(out, _burst(_N(0.06), rng, 500, 5000, t60=0.04, attack=0.0003), 0.0, 0.9)
    st = bandpass(white(n, rng), 350, 3400, 3)
    st *= 0.35 + 0.65 * np.abs(smooth_noise(n, 40, rng))
    st += 0.6 * bandpass(crackle(n, 220, rng), 600, 4000, 2)
    gate = ((t > 0.03) & (t < L)).astype(float)
    gate = onepole_lp(gate, 200)
    m16 = int(n * 16000 / SR)
    v = _formant_voice(m16, rng, 16000, f0=rng.uniform(105, 135), syl_rate=6.0)
    v = dsp.resample(v, 16000, SR)[:n]
    v = dsp.pad_to(v, n)
    v = bandpass(v, 450, 2600, 3)
    v = np.round(saturate(v / (np.max(np.abs(v)) + 1e-9), 3.0) * 12) / 12        # crushed
    v *= ((t > 0.12) & (t < L - 0.08)) * 0.55
    out += (st * 0.55 + v) * gate
    tail = _burst(_N(0.2), rng, 600, 5000, t60=0.12, attack=0.0005)
    _place(out, tail, L, 0.8)
    if rng.uniform() < 0.5:
        bt = np.sin(TWO_PI * 1400 * t_axis(_N(0.08))) * np.hanning(_N(0.08))
        _place(out, bt, L + 0.02, 0.18)
    return out


# ============================================================================ cars
@_sfx("car_door_open", space=1.0)
def _car_door_open(dur, p, rng):
    """1940s sedan door opening: handle click, heavy latch release, seal unstick, short hinge."""
    n = _N(0.75)
    out = np.zeros(n)
    _place(out, _hit(rng, [2500, 3900], [0.03, 0.02], click=0.6), 0.0, 0.4)
    _place(out, _hit(rng, [600, 1100, 1700, 2600], [0.09, 0.07, 0.05, 0.04], spread=0.04, click=0.5), 0.07, 0.9)
    _place(out, _burst(_N(0.06), rng, 80, 700, t60=0.03), 0.07, 0.8)
    _place(out, _burst(_N(0.08), rng, 150, 900, t60=0.05, attack=0.006), 0.12, 0.5)
    cr = dsp.friction(_N(0.25), 70, rng, body=[(700, 4, 1.0), (1500, 6, 0.4)]) * np.hanning(_N(0.25))
    _place(out, cr, 0.2, 0.25)
    air = sos(white(_N(0.4), rng), "lowpass", 600, 2) * np.hanning(_N(0.4)) * 0.15
    _place(out, air, 0.15)
    return out


@_sfx("car_door_close", space=1.0)
def _car_door_close(dur, p, rng):
    """Solid steel door thunk: low slab thump + panel resonances + latch + rattle + air push."""
    n = _N(0.9)
    out = np.zeros(n)
    _place(out, _thump(_N(0.4), 115, 68, 0.025, 0.2), 0.0, 1.0)
    _place(out, _hit(rng, [180, 262, 410, 655, 900], [0.2, 0.16, 0.12, 0.09, 0.07], spread=0.05, click=0.2), 0.0, 0.5)
    _place(out, _burst(_N(0.08), rng, 60, 900, t60=0.04, attack=0.0008), 0.0, 1.0)
    _place(out, _hit(rng, [1200, 2200, 3500], [0.06, 0.05, 0.03], click=0.5), 0.009, 0.35)
    for k in range(3):
        _place(out, _hit(rng, [700 + 400 * rng.uniform(), 1500 + 800 * rng.uniform()], [0.03, 0.02], click=0.0), 0.06 + 0.03 * k, 0.08)
    _place(out, _burst(_N(0.15), rng, hi=250, t60=0.08, attack=0.004), 0.0, 0.5)
    return out


@_sfx("car_brake", space=1.0)
def _car_brake(dur, p, rng):
    """Car pulling up on a wet street: tyre hiss decaying, a short damp squeal, suspension
    clunk as it stops."""
    n = _N(1.6)
    t = t_axis(n)
    L = 1.15
    slow = np.clip(1 - t / L, 0, 1)
    hiss = bandpass(white(n, rng), 900, 6000, 2) * (0.25 + 0.75 * slow) * (t < L + 0.1) * 0.35
    hiss += bandpass(white(n, rng), 120, 600, 2) * slow * 0.3
    f = 2350 * rng.uniform(0.9, 1.1) * (1 + 0.012 * smooth_noise(n, 20, rng)) * (1 - 0.06 * t / L)
    sq = (np.sin(TWO_PI * np.cumsum(f) / SR) + 0.3 * np.sin(TWO_PI * 2 * np.cumsum(f) / SR))
    sq *= np.clip((t - 0.15) / 0.2, 0, 1) * np.clip((L - t) / 0.25, 0, 1) * (0.6 + 0.4 * np.abs(smooth_noise(n, 15, rng)))
    out = hiss + 0.07 * sq
    _place(out, _thump(_N(0.3), 95, 60, 0.03, 0.15), L - 0.02, 0.6)
    _place(out, _hit(rng, [420, 760, 1300], [0.1, 0.07, 0.05], click=0.2), L, 0.15)
    return _wide(out, rng, 0.3)


@_sfx("wiper_thunk", space=0.6)
def _wiper_thunk(dur, p, rng):
    """Wiper arm reaching its end stop: rubber thup + motor-linkage click."""
    n = _N(0.3)
    out = np.zeros(n)
    _place(out, _burst(_N(0.06), rng, 100, 650, t60=0.03, attack=0.001), 0.0, 1.0)
    _place(out, _thump(_N(0.1), 130, 85, 0.01, 0.06), 0.0, 0.6)
    _place(out, _hit(rng, [1600, 2700], [0.025, 0.02], click=0.4), 0.012, 0.25)
    return out


@_sfx("wipers", kind="sustained", norm="int", default_dur=5.0, space=0.6)
def _wipers(dur, p, rng):
    """Windscreen wipers (period = full back-and-forth cycle, default 1.5 s): wet rubber
    swish/squeak across the glass panning with the blade, thunk at each end, faint motor."""
    period = float(p.get("period", 1.5))
    n = _N(dur)
    t = t_axis(n)
    out = np.zeros((n, 2))
    half = period / 2
    k = 0
    while k * half < dur + half:
        t0 = k * half
        L = half * 0.82
        m = _N(L)
        x = t_axis(m)
        sw = tv_bandpass(white(m, rng), lambda u: 900 + 1600 * math.sin(math.pi * min(u / L, 1)), q=0.8, block=64)
        sq = dsp.friction(m, 500 + 300 * np.sin(np.pi * x / L), rng, jitter=0.25, body=[(1100, 5, 1.0), (2300, 7, 0.5)])
        s = (sw * 0.8 + sq * 0.35) * np.sin(np.pi * x / L) ** 1.2
        pan = np.linspace(-0.6, 0.6, m) if k % 2 == 0 else np.linspace(0.6, -0.6, m)
        th = (pan + 1) * np.pi / 4
        st = np.stack([s * np.cos(th), s * np.sin(th)], axis=1)
        mix_into(out, st, n_of(t0))
        th_ = _sum(_thump(_N(0.08), 130, 85, 0.01, 0.05), _burst(_N(0.05), rng, 100, 650, t60=0.025))
        mix_into(out, pan_mono(th_, 0.6 if k % 2 == 0 else -0.6), n_of(t0 + L))
        k += 1
    motor = sos(saturate(np.sin(TWO_PI * 95 * t), 2.0), "bandpass", (80, 900), 2) * 0.02
    out += motor[:, None]
    return fade(out, 0.05, 0.08)


def _engine(n, rng, rpm, load=0.3):
    """Inline-six firing pulses (3 per rev) -> exhaust resonances; rpm may be an array."""
    fr = np.asarray(rpm, dtype=np.float64) / 60.0 * 3.0
    fr = fr * (1 + 0.015 * smooth_noise(n, 6, rng))
    ph = np.cumsum(fr) / SR
    idx = np.nonzero(np.diff(np.floor(ph), prepend=0) > 0)[0]
    imp = np.zeros(n)
    imp[idx] = np.exp(rng.normal(0, 0.18, len(idx)))
    x = signal_lfilter_decay(imp, 0.004)
    x = resonator_bank(x, [85, 170, 260, 420], [1.5, 2.0, 3.0, 3.0], [1.0, 0.7, 0.4, 0.2 + 0.4 * load])
    x += 0.15 * sos(white(n, rng), "bandpass", (300, 1800), 2) * (0.3 + load)
    tick = sos(crackle(n, 11, rng, amp_spread=0.2), "highpass", 2500, 2) * 0.15
    return x + tick


def signal_lfilter_decay(x, tau):
    a = math.exp(-1.0 / (tau * SR))
    from scipy import signal as _s
    return _s.lfilter([1.0], [1.0, -a], x)


@_sfx("engine_idle", kind="sustained", norm="int", default_dur=4.0, space=0.8)
def _engine_idle(dur, p, rng):
    """1940s straight-six at ~650 rpm idle: uneven firing thrum, exhaust body, lifter tick."""
    n = _N(dur)
    rpm = float(p.get("rpm", 650))
    x = _engine(n, rng, np.full(n, rpm), 0.2)
    return fade(_wide(x, rng, 0.25), 0.15, 0.25)


@_sfx("car_away", kind="sustained", norm="max", default_dur=4.5, space=0.8)
def _car_away(dur, p, rng):
    """Car pulling away into the rain: revs up, gear change, recedes (level falls, top end
    closes, slight Doppler drop), wet tyre hiss."""
    n = _N(dur)
    t = t_axis(n)
    rpm = np.where(t < 1.4, 650 + 1500 * np.clip(t / 1.4, 0, 1) ** 0.8, 1500 + 500 * np.clip((t - 1.7) / 2.0, 0, 1))
    rpm = np.where((t > 1.4) & (t < 1.7), 2150 - 650 * (t - 1.4) / 0.3, rpm)
    eng = _engine(n, rng, rpm * (1 - 0.03 * np.clip(t / dur, 0, 1)), 0.7)
    tyre = bandpass(white(n, rng), 800, 5000, 2) * np.clip(t / 0.8, 0, 1) * 0.5
    dist = np.clip((t - 0.3) / max(dur - 0.3, 0.1), 0, 1)
    gain = db2lin(-24 * dist ** 1.2)
    x = (eng + tyre) * gain
    x = tv_lowpass(x, 6000 * (1 - 0.85 * dist) + 500, q=0.7, block=256)
    st = dsp.pan_stereo(_wide(x, rng, 0.3), 0.0)
    return fade(st, 0.05, 0.3)


# ============================================================================ clocks
@_sfx("clock_tick", space=0.7)
def _clock_tick(dur, p, rng):
    """Escapement tick: crisp metallic click + case 'tok'. Odd seeds give the lower 'tock'."""
    tock = bool(p.get("tock", rng.uniform() < 0.5))
    k = 0.84 if tock else 1.0
    n = _N(0.15)
    out = np.zeros(n)
    _place(out, _hit(rng, np.array([2100, 3900, 6300, 8700]) * k, [0.035, 0.03, 0.022, 0.015], spread=0.02, click=0.9), 0.0, 1.0)
    _place(out, _burst(_N(0.03), rng, 700 * k, 1300 * k, t60=0.012), 0.0, 0.5)
    return out


@_sfx("clock_ticking", kind="sustained", norm="int", default_dur=4.0, space=0.7)
def _clock_ticking(dur, p, rng):
    """Steady tick-tock at bpm (default 60). Ticks are identical-period (clocks don't swing)."""
    bpm = float(p.get("bpm", 60))
    n = _N(dur)
    out = np.zeros(n)
    per = 60.0 / bpm
    k = 0
    while k * per + 0.004 < dur:
        _place(out, _clock_tick(None, {"tock": k % 2 == 1}, rng), k * per + 0.004, 1.0 if k % 2 == 0 else 0.85)
        k += 1
    return fade(out, 0.0, 0.03)


@_sfx("clock_stop", space=0.7)
def _clock_stop(dur, p, rng):
    """The clock stops: last tick, a whirr of the gear train spinning down, a low spring
    'boing' and a final settle click - then nothing."""
    n = _N(1.0)
    out = np.zeros(n)
    _place(out, _clock_tick(None, {"tock": False}, rng), 0.0, 1.0)
    tt, gap = 0.06, 0.012
    while tt < 0.3:
        _place(out, _hit(rng, [3100, 5200], [0.012, 0.01], click=0.5, n=_N(0.03)), tt, 0.35 * (1 - tt / 0.35))
        tt += gap
        gap *= 1.18
    boing = np.sin(TWO_PI * np.cumsum(230 * (1 - 0.08 * t_axis(_N(0.6)))) / SR) * exp_env(_N(0.6), 0.45)
    boing += 0.4 * np.sin(TWO_PI * 345 * t_axis(_N(0.6))) * exp_env(_N(0.6), 0.3)
    _place(out, boing, 0.04, 0.35)
    _place(out, _hit(rng, [1800, 3300], [0.04, 0.03], click=0.7), 0.42, 0.5)
    return out


@_sfx("watch_crack", space=1.0)
def _watch_crack(dur, p, rng):
    """Pocket watch hits the pavement: metal clink, glass crack (burst of micro-fractures,
    fine crackle tail), a small bounce."""
    n = _N(0.8)
    out = np.zeros(n)
    _place(out, _hit(rng, [3100, 4700, 7200, 9100], [0.14, 0.11, 0.08, 0.05], spread=0.03, click=0.8), 0.0, 0.9)
    _place(out, _burst(_N(0.05), rng, 200, 1500, t60=0.02), 0.0, 0.5)
    for k in range(int(rng.integers(7, 12))):
        _place(out, _click(rng, 2500, rng.uniform(0.0008, 0.002), _N(0.006)), 0.004 + rng.exponential(0.012), rng.uniform(0.3, 1.0))
    cr = sos(crackle(_N(0.35), 140, rng), "highpass", 3000, 2) * exp_env(_N(0.35), 0.25)
    _place(out, cr, 0.02, 0.6)
    _place(out, _hit(rng, [3300, 5100], [0.06, 0.04], click=0.5), 0.13 + rng.uniform(0, 0.03), 0.3)
    return out


# ============================================================================ bell / thunder
@_sfx("bell_toll", space=0.0)
def _bell_toll(dur, p, rng):
    """Distant church bell tuned to D (minor-third bell partials: hum, prime, tierce, quint,
    nominal + uppers, each a slowly beating doublet). count tolls, interval s apart."""
    count = int(p.get("count", 1))
    interval = float(p.get("interval", 1.3))
    prime = 293.66
    parts = [(0.5, 0.55, 8.0), (1.0, 0.6, 5.5), (1.2, 0.5, 4.5), (1.5, 0.28, 2.6), (2.0, 1.0, 3.6),
             (2.61, 0.25, 1.6), (3.0, 0.3, 1.9), (4.0, 0.2, 1.2), (5.08, 0.12, 0.8)]
    tail = 4.5
    one_n = _N(tail + 0.5)
    t = t_axis(one_n)

    def toll(seedk):
        r = np.random.default_rng(seedk)
        x = np.zeros((one_n, 2))
        for ratio, a, t60 in parts:
            f = prime * ratio
            for ch in range(2):
                for det in (-0.35, 0.35):
                    ff = f + det * (1 + 0.3 * ch)
                    x[:, ch] += 0.5 * a * np.sin(TWO_PI * ff * t + r.uniform(0, TWO_PI)) * np.power(10, -3 * t / t60)
        strike = bandpass(r.standard_normal(_N(0.03)), 1500, 6000, 2) * exp_env(_N(0.03), 0.02) * 0.8
        x[:len(strike)] += strike[:, None]
        x[:_N(0.002)] *= np.linspace(0, 1, _N(0.002))[:, None]
        return x

    n = _N((count - 1) * interval + tail + 0.5)
    out = np.zeros((n, 2))
    for k in range(count):
        mix_into(out, toll(dsp.stable_seed("bell", k, int(rng.integers(1 << 30)))), n_of(k * interval))
    out = sos(out, "lowpass", 4200, 2)
    out = dsp.reverb(out, "hall", wet_db=-5.0, dry=0.8)[:n + _N(1.0)]
    return fade(out, 0.0, 1.2)


@_sfx("thunder", space=0.0, hit=True)
def _thunder(dur, p, rng):
    """Thunder. distance 0 (close: crack + loud roll) .. 1 (far: low, slow, long roll)."""
    d = float(np.clip(p.get("distance", 0.6), 0, 1))
    L = 5.0 + 3.5 * d
    n = _N(L + 0.5)
    t = t_axis(n)
    onset = 0.02 + 0.5 * d
    rolls = np.zeros(n)
    for _ in range(int(4 + 4 * d)):
        c = onset + rng.uniform(0, L * 0.6) ** 1.1
        w = rng.uniform(0.25, 0.9) * (1 + d)
        rolls += rng.uniform(0.4, 1.0) * np.exp(-0.5 * ((t - c) / w) ** 2)
    rolls += 1.2 * np.exp(-0.5 * ((t - onset - 0.25) / (0.3 + 0.4 * d)) ** 2)
    rolls *= np.exp(-np.maximum(t - onset, 0) / (1.6 + 1.4 * d)) * (t > onset - 0.2)
    rolls = onepole_lp(rolls, 6.0)
    out = np.zeros((n, 2))
    lp = 3800 * (1 - d) + 260
    for ch in range(2):
        body = brown(n, rng) * 0.7 + pink(n, rng) * 0.3
        body = sos(body, "lowpass", lp, 2)
        body *= rolls * (1 + 0.35 * smooth_noise(n, 9, rng))
        out[:, ch] = body
    if d < 0.6:
        k = 1 - d / 0.6
        cr = sos(crackle(_N(0.5), 260, rng), "highpass", 900, 2) * exp_env(_N(0.5), 0.35)
        crack = _burst(_N(0.06), rng, 300, 9000, t60=0.04, attack=0.0003)
        mix_into(out, pan_mono(_sum(cr * 1.5, crack * 2.0), rng.uniform(-0.3, 0.3)) * k, n_of(onset))
    sub = np.sin(TWO_PI * 38 * t) * rolls * 0.25
    out += sub[:, None]
    return fade(out, 0.01, 0.6), -9.0 * d


# ============================================================================ designed hits
@_sfx("impact", space=0.0, hit=True, trim=2.0)
def _impact(dur, p, rng):
    """Cinematic hit (size 0..1): sub boom with pitch drop + punch + crack + grit + hall tail."""
    s = float(np.clip(p.get("size", 0.6), 0, 1))
    n = _N(1.0 + 2.2 * s)
    out = np.zeros(n)
    _place(out, _thump(_N(0.6 + 1.6 * s), 150, 40, 0.035, 0.45 + 1.3 * s), 0.0, 1.0)
    _place(out, _burst(_N(0.1), rng, 60, 1800 + 1500 * s, t60=0.05 + 0.03 * s, attack=0.0006), 0.0, 1.1)
    _place(out, _click(rng, 3000, 0.005, _N(0.015)), 0.0, 0.7 - 0.3 * s)
    grit = bandpass(white(_N(0.35), rng), 300, 1600, 2) * exp_env(_N(0.35), 0.25) * 0.35
    _place(out, grit, 0.002)
    out = saturate(out * 1.3, 1.6) / 1.3
    st = dsp.reverb(out, "hall", wet_db=-11 + 4 * s, dry=1.0)[:n]
    return fade(st, 0.0, 0.3), 6.0 * (s - 0.6)


@_sfx("braam", space=0.0, hit=True, trim=5.0)
def _braam(dur, p, rng):
    """The BRAAM: a low brass-like D-minor power cluster (detuned saw stacks D1 D2 A2 D3 F3)
    whose filter blooms 250 Hz -> 2.4 kHz and closes, saturated for growl, 28 Hz flutter,
    sub layer and a big hall. ~1.4 s sustain, ~2 s release."""
    n = _N(4.6)
    t = t_axis(n)
    notes = [(36.71, 1.0), (73.42, 0.9), (110.0, 0.7), (146.83, 0.55), (174.61, 0.3), (220.0, 0.22)]
    stack = np.zeros((n, 2))
    for f, a in notes:
        for ch in range(2):
            for det in (-11, -3, 6, 13):
                cents = det + (4 if ch else -4)
                stack[:, ch] += a * saw(f * 2 ** (cents / 1200), n, phase0=rng.uniform()) / 4
    cut = 250 + 2150 * np.exp(-np.maximum(t - 0.06, 0) / 0.45) * np.clip(t / 0.06, 0, 1) + 400 * np.exp(-t / 1.6)
    for ch in range(2):
        stack[:, ch] = tv_lowpass(stack[:, ch], cut, q=1.3, block=128)
    flutter = 1 + 0.16 * np.sin(TWO_PI * 28 * t) * np.exp(-t / 1.0)
    env = np.clip(t / 0.03, 0, 1) * np.where(t < 1.4, 1.0, np.exp(-(t - 1.4) / 0.75))
    x = saturate(stack * 1.7, 2.2) * (env * flutter)[:, None]
    sub = np.sin(TWO_PI * np.cumsum(36.71 * (1 - 0.06 * np.clip(t / 2, 0, 1))) / SR) * np.clip(t / 0.02, 0, 1) * np.exp(-t / 1.6)
    x += 0.9 * sub[:, None]
    air = bandpass(white(n, rng), 400, 2200, 2) * env * 0.05
    x += air[:, None]
    out = dsp.reverb(x, "hall", wet_db=-7.0, dry=1.0)[:n]
    return fade(out, 0.0, 0.5)


@_sfx("sub_drop", space=0.0, hit=True, trim=2.0)
def _sub_drop(dur, p, rng):
    """Sub drop: sine falling 95 -> 30 Hz, soft onset thud, a little 2nd harmonic so phones
    hear it."""
    n = _N(3.0)
    t = t_axis(n)
    f = 30 + 65 * np.exp(-t / 0.42)
    x = np.sin(TWO_PI * np.cumsum(f) / SR) * np.clip(t / 0.004, 0, 1) * np.power(10, -3 * t / 2.6)
    h2 = sos(saturate(x * 2.2, 2.0), "highpass", 70, 2) * 0.22
    thud = _burst(_N(0.08), rng, hi=220, t60=0.05, attack=0.001) * 0.5
    y = x + h2
    y[:len(thud)] += thud
    return fade(y, 0.0, 0.4)


@_sfx("stinger", space=0.0, hit=True, trim=3.0)
def _stinger(dur, p, rng):
    """Orchestral shock chord: high string cluster (D Eb A), low brass stab, felt-piano
    cluster, metallic shing, hall reverb."""
    n = _N(3.2)
    t = t_axis(n)
    x = np.zeros((n, 2))
    for f, a in ((587.33, 0.5), (622.25, 0.45), (880.0, 0.35), (293.66, 0.4), (311.13, 0.35), (1174.7, 0.15)):
        for ch in range(2):
            v = np.zeros(n)
            for det in (-9, -2, 4, 11):
                v += saw(f * 2 ** ((det + 3 * (ch - 0.5)) / 1200), n, phase0=rng.uniform()) / 4
            x[:, ch] += a * v
    for ch in range(2):
        x[:, ch] = sos(x[:, ch], "lowpass", 5200, 2)
    trem = 1 + 0.12 * np.sin(TWO_PI * 11 * t + rng.uniform(0, 6))
    x *= (np.clip(t / 0.012, 0, 1) * np.power(10, -3 * t / 2.3) * trem)[:, None]
    br = np.zeros(n)
    for f in (73.42, 110.0, 146.83):
        br += saw(f, n) + saw(f * 1.004, n)
    br = tv_lowpass(br, 200 + 2200 * np.exp(-t / 0.12), q=1.0, block=128) * np.clip(t / 0.01, 0, 1) * np.exp(-t / 0.35) * 0.35
    pn = sum(_felt_piano_note(f, n, 1.0, rng) for f in (36.71, 55.0, 77.78)) * 0.5
    sh = dsp.fm_op(2350.0, n, ratio=1.41, index=4.0, mod_env=np.exp(-t / 0.3)) * np.power(10, -3 * t / 1.6) * 0.12
    x += (br + pn + sh)[:, None]
    out = dsp.reverb(saturate(x, 1.3), "hall", wet_db=-5.0, dry=1.0)[:n + _N(0.8)]
    return fade(out, 0.0, 0.6)


@_sfx("riser", kind="sustained", norm="max", default_dur=3.0, space=0.0)
def _riser(dur, p, rng):
    """Tension riser ending exactly at dur: noise sweep 200 Hz -> 7 kHz, two detuned saws
    gliding up two octaves, accelerating tremolo, exponential swell, hard stop."""
    n = _N(dur)
    t = t_axis(n)
    u = np.clip(t / dur, 0, 1)
    nz = tv_bandpass(white(n, rng), 200 * (35 ** u), q=1.2, block=128)
    f = 146.83 * 4 ** (u ** 1.3)
    tone = saw(f, n) + saw(f * 1.006, n, phase0=0.3) + 0.5 * saw(f * 2.003, n)
    tone = tv_lowpass(tone, 400 + 6000 * u ** 2, q=0.9, block=128)
    trem = 1 + 0.35 * np.sin(TWO_PI * np.cumsum(4 + 16 * u ** 2) / SR)
    env = db2lin(-30 * (1 - u) ** 1.5)
    x = (nz * 0.8 + tone * 0.25) * trem * env
    st = _wide(x, rng, 0.5)
    return fade(st, 0.02, 0.004)


@_sfx("reverse_swell", kind="sustained", norm="max", default_dur=2.0, space=0.0)
def _reverse_swell(dur, p, rng):
    """Reversed reverb of a cymbal + low chord hit: swells into the cut at exactly dur."""
    m = _N(0.6)
    tm = t_axis(m)
    hit = bandpass(white(m, rng), 2500, 12000, 2) * exp_env(m, 0.5) * 0.5
    for f in (73.42, 146.83, 220.0, 293.66):
        hit += 0.3 * np.sin(TWO_PI * f * tm) * exp_env(m, 0.4)
    wet = dsp.convolve(hit, dsp.make_ir("hall"))
    wet = wet[::-1]
    n = _N(dur)
    if len(wet) >= n:
        wet = wet[-n:]
    else:
        wet = dsp.pad_to(wet[::-1], n)[::-1]
    return fade(wet, 0.05, 0.004)


@_sfx("drone_swell", kind="sustained", norm="max", default_dur=4.0, space=0.0)
def _drone_swell(dur, p, rng):
    """Dark low drone swelling in and out (D1 / D2 / A2 detuned saws + air), sin^1.5 shape."""
    n = _N(dur)
    t = t_axis(n)
    x = np.zeros((n, 2))
    for f, a in ((36.71, 1.0), (73.42, 0.7), (110.0, 0.4), (146.83, 0.15)):
        for ch in range(2):
            x[:, ch] += a * (saw(f * 2 ** ((-6 + 12 * ch) / 1200), n, phase0=rng.uniform()) + saw(f * 2 ** ((5 - 9 * ch) / 1200), n, phase0=rng.uniform())) / 2
    for ch in range(2):
        x[:, ch] = sos(x[:, ch], "lowpass", 420, 2)
    air = sos(white(n, rng), "bandpass", (300, 1500), 2) * 0.06
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5 * (1 + 0.1 * smooth_noise(n, 0.5, rng))
    return (x + air[:, None]) * env[:, None]


@_sfx("whoosh", space=0.3)
def _whoosh(dur, p, rng):
    """Air movement past the camera (size 0..1 = length, depth, level), panning across."""
    s = float(np.clip(p.get("size", 0.5), 0, 1))
    L = 0.35 + 0.95 * s
    n = _N(L + 0.1)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    pk = 0.62
    centre = np.where(u < pk, 380 + (2600 - 900 * s) * (u / pk) ** 1.5, 700 + (2300 - 900 * s) * np.exp(-(u - pk) / 0.18))
    x = tv_bandpass(pink(n, rng), centre, q=0.9, block=64)
    x += (0.3 + 0.6 * s) * sos(tv_bandpass(pink(n, rng), centre * 0.4, q=0.7, block=64), "lowpass", 800, 2)
    env = np.where(u < pk, (u / pk) ** 2.2, np.exp(-(u - pk) / 0.12))
    x *= env
    pan = np.clip(-0.7 + 1.4 * u, -1, 1)
    th = (pan + 1) * np.pi / 4
    st = np.stack([x * np.cos(th), x * np.sin(th)], axis=1)
    return st, 5.0 * (s - 0.5)


@_sfx("whip", space=0.2)
def _whip(dur, p, rng):
    """Whip pan: a fast, tight swish that snaps up in pitch and stops."""
    n = _N(0.32)
    t = t_axis(n)
    u = np.clip(t / 0.26, 0, 1)
    x = tv_bandpass(white(n, rng), 1100 * 5.5 ** u, q=1.3, block=32)
    x += 0.3 * sos(white(n, rng), "highpass", 6000, 2)
    env = np.where(u < 0.75, (u / 0.75) ** 2.5, np.exp(-(u - 0.75) / 0.05))
    x *= env
    pan = -0.8 + 1.6 * u
    th = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], axis=1)


# ============================================================================ glass / guns / falls
@_sfx("glass_ring", space=0.4)
def _glass_ring(dur, p, rng):
    """A struck glass / mirror rim ringing on: few high partials with long, beating decays."""
    n = _N(3.8)
    t = t_axis(n)
    f1 = 1318.5 * rng.uniform(0.97, 1.03)
    x = np.zeros((n, 2))
    for ratio, a, t60 in ((1.0, 1.0, 3.6), (2.32, 0.45, 2.4), (3.98, 0.25, 1.5), (6.1, 0.12, 0.8)):
        for ch in range(2):
            beat = 0.6 + 0.4 * ch
            x[:, ch] += a * 0.5 * (np.sin(TWO_PI * (f1 * ratio - beat) * t + rng.uniform(0, 6))
                                   + np.sin(TWO_PI * (f1 * ratio + beat) * t + rng.uniform(0, 6))) * np.power(10, -3 * t / t60)
    x[:_N(0.003)] *= np.linspace(0, 1, _N(0.003))[:, None]
    tink = _click(rng, 4000, 0.002, _N(0.008)) * 0.6
    x[:len(tink)] += tink[:, None]
    return fade(x, 0.0, 0.5)


@_sfx("glass_break", space=0.6, hit=True, trim=1.0)
def _glass_break(dur, p, rng):
    """Pane shattering: crack + thud, then a spray of shards (modal tinkles) thinning out."""
    n = _N(2.0)
    out = np.zeros((n, 2))
    mix_into(out, pan_mono(_burst(_N(0.02), rng, 1500, 14000, t60=0.008, attack=0.0002) * 2.0, 0), 0)
    mix_into(out, pan_mono(_thump(_N(0.15), 160, 80, 0.01, 0.07), 0), 0)
    k = 130
    times = 0.004 + rng.exponential(0.22, k)
    times = times[times < 1.8]
    for tt in times:
        fr = np.exp(rng.uniform(np.log(2200), np.log(11000), 3))
        sh = modal(fr, rng.uniform(0.02, 0.12, 3), rng.uniform(0.3, 1.0, 3), _N(0.15), phases=rng.uniform(0, 6, 3))
        g = rng.uniform(0.15, 0.6) * math.exp(-tt / 0.6)
        mix_into(out, pan_mono(sh, rng.uniform(-0.8, 0.8)), n_of(tt), g)
    noise = bandpass(white(n, rng), 2000, 9000, 2) * exp_env(n, 0.6) * 0.15
    out += noise[:, None]
    return fade(out, 0.0, 0.2)


@_sfx("gunshot_far", space=0.0, hit=True)
def _gunshot_far(dur, p, rng):
    """A shot down a wet alley: band-limited crack + low boom, slapback echoes off brick and a
    long alley tail."""
    n = _N(2.6)
    dry = np.zeros(n)
    _place(dry, _burst(_N(0.02), rng, 350, 4500, t60=0.008, attack=0.0002), 0.0, 1.6)
    _place(dry, _thump(_N(0.3), 140, 55, 0.012, 0.18), 0.0, 1.0)
    _place(dry, _burst(_N(0.25), rng, hi=500, t60=0.14, attack=0.0008), 0.0, 0.6)
    out = to_stereo(dry.copy())
    for dt, g, lp, pan in ((0.068, 0.45, 3500, -0.5), (0.141, 0.32, 2800, 0.6), (0.233, 0.22, 2200, -0.3),
                           (0.38, 0.14, 1600, 0.4), (0.55, 0.08, 1200, -0.6)):
        e = sos(dry, "lowpass", lp, 2) * g
        mix_into(out, pan_mono(e, pan), n_of(dt))
    out = dsp.reverb(out, "alley", wet_db=-3.0, dry=1.0)[:n]
    rumble = sos(brown(n, rng), "lowpass", 180, 2) * exp_env(n, 1.4) * 0.2
    out += rumble[:, None]
    return fade(out, 0.0, 0.4)


@_sfx("body_fall", space=1.0)
def _body_fall(dur, p, rng):
    """A body hitting wet pavement: cloth whoosh, heavy thud, two limb hits, splash."""
    wet = int(bool(p.get("wet", 1)))
    n = _N(1.1)
    out = np.zeros(n)
    cl = tv_bandpass(white(_N(0.12), rng), lambda x: 600 + 2500 * x / 0.12, q=0.8, block=64) * np.linspace(0, 1, _N(0.12)) ** 2
    _place(out, cl, 0.0, 0.4)
    t0 = 0.09
    _place(out, _thump(_N(0.5), 125, 52, 0.025, 0.28), t0, 1.0)
    _place(out, _burst(_N(0.12), rng, 60, 900, t60=0.06, attack=0.001), t0, 1.1)
    _place(out, _burst(_N(0.08), rng, 900, 3000, t60=0.03), t0 + 0.004, 0.25)
    for dt, g in ((0.11, 0.45), (0.23, 0.3)):
        _place(out, _sum(_thump(_N(0.2), 160, 80, 0.015, 0.1), _burst(_N(0.05), rng, 200, 1500, t60=0.025)), t0 + dt + rng.uniform(0, 0.03), g)
    if wet:
        _place(out, _splash(_N(0.6), rng, 1.0), t0, 0.9)
    return out


@_sfx("badge_clatter", space=1.0)
def _badge_clatter(dur, p, rng):
    """A metal badge hits the ground, bounces (shrinking intervals), spins like a coin
    (accelerating contacts) and stops."""
    n = _N(2.0)
    out = np.zeros(n)
    modes = np.array([2240, 3710, 5420, 7930, 10450]) * rng.uniform(0.95, 1.05)
    t60 = np.array([0.35, 0.28, 0.2, 0.14, 0.09])

    def clink(a):
        return _hit(rng, modes, t60, amps=rng.uniform(0.2, 1.0, len(modes)), spread=0.004, click=0.8, n=_N(0.45)) * a
    tt, gap, a = 0.0, 0.16, 1.0
    for k in range(6):
        _place(out, clink(a), tt)
        tt += gap
        gap *= 0.68
        a *= 0.72
    gap = 0.06
    a = 0.4
    while gap > 0.007 and tt < 1.75:
        _place(out, clink(a), tt)
        tt += gap
        gap *= 0.93
        a *= 0.985
    _place(out, clink(0.25) * exp_env(_N(0.45), 0.08), tt + 0.01)
    return out


@_sfx("gavel", space=0.0, hit=True)
def _gavel(dur, p, rng):
    """Wooden gavel on its block in a courtroom: hard wood clack + desk thump + room."""
    n = _N(1.4)
    out = np.zeros(n)
    _place(out, _hit(rng, [520, 1230, 2050, 3100, 4300], [0.12, 0.08, 0.06, 0.045, 0.03], spread=0.03, click=1.0), 0.0, 1.0)
    _place(out, _thump(_N(0.2), 170, 110, 0.012, 0.1), 0.0, 0.7)
    _place(out, _burst(_N(0.03), rng, 1500, 8000, t60=0.006, attack=0.0002), 0.0, 0.8)
    return dsp.reverb(out, "court", wet_db=-7.0)[:n]


# ============================================================================ doors / metal
@_sfx("door_creak", space=1.0)
def _door_creak(dur, p, rng):
    """Old door on dry hinges: slow wooden creak pulses + a thin hinge squeal."""
    n = _N(1.3)
    t = t_axis(n)
    sw = np.sin(np.pi * t / (n / SR)) ** 0.8
    rate = 35 + 70 * np.abs(smooth_noise(n, 1.5, rng)) + 25 * sw
    wood = dsp.friction(n, rate, rng, jitter=0.3, body=[(220, 7, 1.0), (470, 9, 0.8), (1100, 12, 0.45), (2300, 14, 0.15)])
    sq = dsp.friction(n, 600 + 300 * sw, rng, jitter=0.1, body=[(2200, 18, 1.0), (3300, 20, 0.4)])
    return (wood + 0.2 * sq) * sw


@_sfx("door_open", space=1.0)
def _door_open(dur, p, rng):
    """Office door opening: knob rattle, latch release, short creak, air."""
    n = _N(1.0)
    out = np.zeros(n)
    for k in range(3):
        _place(out, _hit(rng, [2900, 4400], [0.02, 0.015], click=0.5, n=_N(0.04)), 0.02 + 0.035 * k, 0.25)
    _place(out, _hit(rng, [1400, 2600, 3900], [0.045, 0.035, 0.025], click=0.8), 0.17, 0.8)
    _place(out, _burst(_N(0.05), rng, 200, 1500, t60=0.02), 0.17, 0.5)
    cr = _door_creak(None, {}, rng)[:_N(0.55)] * np.hanning(_N(0.55))
    _place(out, cr, 0.3, 0.35)
    air = sos(white(_N(0.5), rng), "lowpass", 500, 2) * np.hanning(_N(0.5)) * 0.2
    _place(out, air, 0.3)
    return out


@_sfx("door_close", space=1.0)
def _door_close(dur, p, rng):
    """Office door shut: slab thump, latch click, frame rattle."""
    n = _N(0.8)
    out = np.zeros(n)
    _place(out, _thump(_N(0.3), 140, 78, 0.015, 0.13), 0.0, 1.0)
    _place(out, _burst(_N(0.06), rng, 70, 1100, t60=0.03, attack=0.0006), 0.0, 1.0)
    _place(out, _hit(rng, [1600, 2900, 4100], [0.05, 0.04, 0.03], click=0.7), 0.006, 0.45)
    for k in range(2):
        _place(out, _hit(rng, [650 + 500 * rng.uniform(), 1300 + 700 * rng.uniform()], [0.04, 0.03], click=0.0), 0.05 + 0.04 * k, 0.1)
    return out


@_sfx("cell_door", space=0.5, hit=True)
def _cell_door(dur, p, rng):
    """Steel barred cell door: short roll on its track, the SLAM (big inharmonic clang +
    thump), bars rattling, lock bolt 'ka-chunk'."""
    n = _N(3.0)
    out = np.zeros((n, 2))
    nr = _N(0.38)
    roll = sos(brown(nr, rng), "lowpass", 400, 2) * (1 + 0.5 * smooth_noise(nr, 30, rng))
    roll += 0.3 * dsp.friction(nr, 180, rng, body=[(1300, 5, 1.0), (2400, 7, 0.5)])
    roll *= np.linspace(0.3, 1, nr) ** 1.5
    mix_into(out, to_stereo(roll * 0.5), 0)
    ts = 0.36
    modes = np.array([95, 143, 211, 298, 421, 587, 803, 1130, 1620, 2240]) * rng.uniform(0.96, 1.04)
    t60s = np.array([2.2, 1.9, 1.6, 1.4, 1.2, 1.0, 0.85, 0.7, 0.55, 0.4])
    clang = np.stack([_hit(rng, modes, t60s, spread=0.01, click=0.6, n=_N(2.6)) for _ in range(2)], axis=1)
    mix_into(out, clang, n_of(ts), 1.0)
    mix_into(out, to_stereo(_thump(_N(0.6), 95, 48, 0.02, 0.4)), n_of(ts), 1.1)
    mix_into(out, to_stereo(_burst(_N(0.1), rng, 60, 2500, t60=0.05, attack=0.0004)), n_of(ts), 1.0)
    for k in range(7):
        r = _hit(rng, [700 + 1800 * rng.uniform(), 1500 + 2500 * rng.uniform()], [0.08, 0.05], click=0.3, n=_N(0.12))
        mix_into(out, pan_mono(r, rng.uniform(-0.6, 0.6)), n_of(ts + 0.05 + rng.uniform(0, 0.35)), 0.25)
    bolt = _sum(_hit(rng, [900, 1500, 2600], [0.08, 0.06, 0.04], click=0.9), 0.6 * _thump(_N(0.15), 140, 90, 0.01, 0.07))
    mix_into(out, to_stereo(bolt), n_of(ts + 0.62), 0.6)
    out = dsp.reverb(out, "cell", wet_db=-12.0)[:n]
    return fade(out, 0.0, 0.4)


@_sfx("blinds_rattle", space=1.0)
def _blinds_rattle(dur, p, rng):
    """Venetian blind slats rattling: clusters of tiny aluminium clicks + rustle."""
    n = _N(0.55)
    out = np.zeros(n)
    k = int(rng.integers(28, 42))
    times = np.sort(rng.uniform(0.0, 0.42, k) ** 1.2)
    for tt in times:
        f = rng.uniform(2600, 6800)
        _place(out, _hit(rng, [f, f * 1.47], [0.03, 0.02], click=0.4, n=_N(0.05)), tt, rng.uniform(0.2, 0.8))
    rs = bandpass(white(n, rng), 1500, 7000, 2) * np.hanning(n) * 0.08
    return _wide(out + rs, rng, 0.4)


@_sfx("blinds_snap", space=1.0)
def _blinds_snap(dur, p, rng):
    """A blind slat snapping back: one sharp aluminium clack + a short decaying rattle."""
    n = _N(0.4)
    out = np.zeros(n)
    _place(out, _hit(rng, [2200, 3600, 5100, 7000], [0.06, 0.05, 0.04, 0.03], click=1.0), 0.0, 1.0)
    for k in range(int(rng.integers(6, 10))):
        tt = 0.02 + rng.exponential(0.06)
        f = rng.uniform(2800, 6500)
        _place(out, _hit(rng, [f, f * 1.5], [0.02, 0.015], click=0.3, n=_N(0.04)), tt, 0.3 * math.exp(-tt / 0.1))
    return out


@_sfx("metal_clang", space=1.0)
def _metal_clang(dur, p, rng):
    """Fire-escape steel struck: hollow inharmonic clang (seed varies the structure) + rattle."""
    n = _N(1.5)
    out = np.zeros(n)
    base = rng.uniform(0.85, 1.15)
    modes = np.array([230, 365, 520, 700, 960, 1290, 1750, 2400]) * base
    t60 = np.array([1.2, 1.0, 0.9, 0.75, 0.6, 0.5, 0.4, 0.3])
    _place(out, _hit(rng, modes, t60, spread=0.03, click=0.7), 0.0, 1.0)
    _place(out, _thump(_N(0.2), 110, 70, 0.01, 0.1), 0.0, 0.5)
    for k in range(2):
        _place(out, _hit(rng, modes[2:5] * rng.uniform(1.4, 1.8), [0.15, 0.1, 0.08], click=0.3, n=_N(0.25)), 0.07 + rng.uniform(0, 0.12), 0.2)
    return out


@_sfx("land_thud", space=1.0)
def _land_thud(dur, p, rng):
    """Landing from a leap on a wet tar-and-gravel roof: heavy thud, gravel crunch, splash."""
    n = _N(0.7)
    out = np.zeros(n)
    _place(out, _thump(_N(0.45), 105, 46, 0.02, 0.25), 0.0, 1.0)
    _place(out, _burst(_N(0.12), rng, 60, 650, t60=0.06, attack=0.001), 0.0, 1.0)
    gr = bandpass(crackle(_N(0.16), 900, rng), 1500, 6500, 2) * exp_env(_N(0.16), 0.12) * 1.5
    _place(out, gr, 0.003, 0.6)
    if int(bool(p.get("wet", 1))):
        _place(out, _splash(_N(0.5), rng, 0.8), 0.002, 0.6)
    return out


@_sfx("laundry_flap", space=1.0)
def _laundry_flap(dur, p, rng):
    """A big wet sheet whipping across the frame: cloth flutter, a 'whap', air."""
    n = _N(0.85)
    t = t_axis(n)
    env = np.sin(np.pi * np.clip(t / 0.75, 0, 1)) ** 1.2
    rate = 14 + 6 * env
    flut = onepole_lp(0.5 + 0.5 * np.sign(np.sin(TWO_PI * np.cumsum(rate) / SR)), 80)
    x = bandpass(white(n, rng), 150, 2200, 2) * flut * env
    _place(x, _burst(_N(0.08), rng, 120, 1500, t60=0.04, attack=0.001), 0.33, 1.2)
    wh = sos(pink(n, rng), "lowpass", 700, 2) * env * 0.4
    pan = np.linspace(-0.6, 0.6, n)
    th = (pan + 1) * np.pi / 4
    s = x + wh
    return np.stack([s * np.cos(th), s * np.sin(th)], axis=1)


@_sfx("tape_measure", space=1.0)
def _tape_measure(dur, p, rng):
    """Steel tape run out: ratchety clicks + metallic sheen, then the lock click."""
    n = _N(1.0)
    out = np.zeros(n)
    tt, gap = 0.0, 1 / 95.0
    while tt < 0.68:
        _place(out, _hit(rng, [3500, 5800], [0.008, 0.006], click=0.6, n=_N(0.02)), tt, rng.uniform(0.4, 0.8))
        tt += gap * rng.uniform(0.9, 1.1)
        gap *= 1.008
    sheen = bandpass(white(_N(0.7), rng), 4000, 9000, 2) * np.hanning(_N(0.7)) * 0.06
    _place(out, sheen, 0.0)
    _place(out, _sum(_hit(rng, [2400, 3700], [0.03, 0.025], click=0.9), 0.4 * _thump(_N(0.05), 300, 200, 0.008, 0.025)), 0.76, 0.9)
    return out


@_sfx("handcuffs", space=1.0)
def _handcuffs(dur, p, rng):
    """Cuffs ratcheting shut: accelerating pawl clicks, chain jingle, final lock."""
    n = _N(1.0)
    out = np.zeros(n)
    tt, gap = 0.0, 0.05
    for k in range(8):
        _place(out, _hit(rng, [2900, 4600, 6300], [0.04, 0.03, 0.02], spread=0.02, click=0.7, n=_N(0.06)), tt, 0.7)
        tt += gap
        gap *= 0.9
    for k in range(9):
        f = rng.uniform(3000, 7500)
        _place(out, _hit(rng, [f, f * 1.37, f * 2.1], [0.1, 0.07, 0.05], click=0.2, n=_N(0.15)), 0.3 + rng.uniform(0, 0.45), rng.uniform(0.15, 0.4))
    _place(out, _hit(rng, [1900, 3300, 4800], [0.05, 0.04, 0.03], click=1.0), 0.82, 0.9)
    return out


@_sfx("chair_creak", space=1.0)
def _chair_creak(dur, p, rng):
    """Wooden office chair taking weight: low wood creak + spring squeak."""
    n = _N(0.7)
    t = t_axis(n)
    sw = np.sin(np.pi * t / (n / SR)) ** 0.9
    wood = dsp.friction(n, 40 + 80 * sw, rng, jitter=0.3, body=[(300, 7, 1.0), (750, 9, 0.6), (1600, 11, 0.3)])
    spring = dsp.friction(n, 420 + 160 * sw, rng, jitter=0.1, body=[(2500, 16, 1.0)])
    return (wood + 0.2 * spring) * sw


@_sfx("drip", space=1.0)
def _drip(dur, p, rng):
    """A single water drip into a puddle: the rising 'plink' of the bubble + tiny splash."""
    n = _N(0.6)
    out = np.zeros(n)
    f0 = rng.uniform(780, 1250)
    _place(out, _drop(rng, f0, 0.022, chirp=0.9), 0.0, 1.0)
    _place(out, _burst(_N(0.01), rng, 2500, 9000, t60=0.004), 0.0, 0.25)
    _place(out, _drop(rng, f0 * 1.9, 0.006, chirp=0.5), 0.004, 0.2)
    return out


@_sfx("keys", space=1.0)
def _keys(dur, p, rng):
    """Key ring jingle: two shakes of small metal clinks."""
    n = _N(0.95)
    out = np.zeros((n, 2))
    for s0 in (0.0, 0.32 + rng.uniform(0, 0.08)):
        for k in range(int(rng.integers(10, 16))):
            tt = s0 + rng.uniform(0, 0.2) ** 1.3
            fr = rng.uniform(2500, 9000)
            c = _hit(rng, [fr, fr * rng.uniform(1.3, 1.6), fr * rng.uniform(2.0, 2.6)], [0.12, 0.08, 0.05], click=0.3, n=_N(0.18))
            mix_into(out, pan_mono(c, rng.uniform(-0.3, 0.3)), n_of(tt), rng.uniform(0.2, 0.7))
    return out


# ============================================================================ sustained textures
@_sfx("room_tone", kind="sustained", norm="int", default_dur=5.0, space=0.0)
def _room_tone(dur, p, rng):
    """Interior air: low HVAC rumble, a breath of pink air, a whisper of mains hum."""
    n = _N(dur)
    t = t_axis(n)
    out = np.zeros((n, 2))
    for ch in range(2):
        r = sos(brown(n, rng), "bandpass", (25, 220), 2) * 0.8
        a = sos(pink(n, rng), "bandpass", (150, 2500), 2) * 0.12
        out[:, ch] = (r + a) * (1 + 0.15 * smooth_noise(n, 0.3, rng))
    hum = (0.02 * np.sin(TWO_PI * 60 * t) + 0.012 * np.sin(TWO_PI * 120 * t + 1.0)) * (1 + 0.2 * smooth_noise(n, 0.5, rng))
    out += hum[:, None]
    return fade(out, 0.3, 0.3)


@_sfx("city_far", kind="sustained", norm="int", default_dur=8.0, space=0.0)
def _city_far(dur, p, rng):
    """Distant city: low traffic wash, far cars swelling past, wet-road hiss, a far horn."""
    n = _N(dur)
    t = t_axis(n)
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = sos(brown(n, rng), "bandpass", (30, 320), 2) * 0.7 * (1 + 0.25 * smooth_noise(n, 0.2, rng))
        out[:, ch] += sos(pink(n, rng), "bandpass", (900, 3500), 2) * 0.05
    tt = rng.uniform(0, 2)
    while tt < dur:
        L = rng.uniform(2.5, 6.0)
        m = _N(L)
        car = bandpass(pink(m, rng), 180, 1100, 2) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2
        mix_into(out, pan_mono(car, rng.uniform(-0.8, 0.8)), n_of(tt), rng.uniform(0.15, 0.4))
        tt += rng.uniform(1.5, 4.0)
    if dur > 4 and rng.uniform() < 0.8:
        m = _N(0.55)
        th = t_axis(m)
        horn = (saw(330 * rng.uniform(0.95, 1.05), m) + saw(415, m)) * np.clip(th / 0.03, 0, 1) * np.clip((0.55 - th) / 0.08, 0, 1)
        horn = sos(horn, "lowpass", 900, 2) * 0.08
        horn_st = dsp.reverb(horn, "street", wet_db=0.0, dry=0.4)
        mix_into(out, horn_st, n_of(rng.uniform(1.0, dur - 2.0)))
    return fade(out, 0.5, 0.5)


@_sfx("crowd_walla", kind="sustained", norm="int", default_dur=5.0, space=0.5)
def _crowd_walla(dur, p, rng):
    """Street crowd murmur: ~14 nonverbal formant 'voices' (random vowel trajectories, no
    words), different pitches and pans, band-limited, softened by a little room."""
    n = _N(dur)
    sr2 = 16000
    m = int(math.ceil(dur * sr2))
    nv = int(p.get("voices", 14))
    out = np.zeros((n, 2))
    for v in range(nv):
        male = rng.uniform() < 0.55
        f0 = rng.uniform(95, 140) if male else rng.uniform(170, 240)
        vo = _formant_voice(m, rng, sr2, f0=f0, syl_rate=rng.uniform(3.8, 6.2))
        vo = dsp.pad_to(dsp.resample(vo, sr2, SR), n)
        vo /= (np.std(vo) + 1e-9)
        mix_into(out, pan_mono(vo, rng.uniform(-0.85, 0.85)), 0, rng.uniform(0.4, 1.0) / math.sqrt(nv))
    out = sos(out, "bandpass", (180, 4200), 2)
    out = dsp.reverb(out, "street", wet_db=-6.0, dry=1.0)[:n]
    return fade(out, 0.3, 0.4)


@_sfx("heartbeat", kind="sustained", norm="int", default_dur=4.0, space=0.0)
def _heartbeat(dur, p, rng):
    """Heard-from-inside heartbeat 'lub-dub' at bpm (optional bpm_end ramps the rate)."""
    bpm0 = float(p.get("bpm", 66))
    bpm1 = float(p.get("bpm_end", bpm0))
    n = _N(dur)
    out = np.zeros(n)
    tt = 0.02
    while tt < dur:
        bpm = bpm0 + (bpm1 - bpm0) * min(1.0, tt / max(dur, 1e-3))
        per = 60.0 / bpm
        lub = _sum(_thump(_N(0.3), 70, 46, 0.03, 0.16), 0.4 * _burst(_N(0.08), rng, hi=140, t60=0.05, attack=0.004))
        dub = _thump(_N(0.25), 88, 58, 0.02, 0.11) * 0.62
        _place(out, lub, tt)
        _place(out, dub, tt + 0.27 * per ** 0.5)
        tt += per
    out = sos(out, "lowpass", 190, 2)
    out += 0.18 * sos(saturate(out * 3, 2.0), "bandpass", (90, 400), 2)      # audible on phones
    return fade(out, 0.01, 0.1)


@_sfx("tinnitus", kind="sustained", norm="int", default_dur=3.0, space=0.0)
def _tinnitus(dur, p, rng):
    """Ringing ears after a shock: a thin high tone with a slow beat and a faint band of hiss."""
    n = _N(dur)
    t = t_axis(n)
    f = float(p.get("freq", 6300.0))
    drift = 1 + 0.002 * smooth_noise(n, 0.4, rng)
    x = np.sin(TWO_PI * np.cumsum(f * drift) / SR) + 0.22 * np.sin(TWO_PI * np.cumsum((f + 1.3) * drift) / SR)
    x += 0.15 * bandpass(white(n, rng), f * 0.85, f * 1.2, 2)
    env = np.clip(t / min(0.3, dur / 3), 0, 1) * np.clip((dur - t) / max(dur * 0.4, 1e-3), 0, 1) ** 1.5
    st = np.stack([x, np.roll(x, 11)], axis=1) * env[:, None]
    return st


def _siren_wail(n, rng, period=4.0, f_lo=650, f_hi=1450):
    t = t_axis(n)
    ph = (t / period + rng.uniform()) % 1.0
    up = 0.45
    u = np.where(ph < up, ph / up, 1 - (ph - up) / (1 - up))
    f = f_lo + (f_hi - f_lo) * np.sin(0.5 * np.pi * u) ** 1.3
    return f


def _siren_tone(f, n):
    ph = np.cumsum(f) / SR
    return np.sin(TWO_PI * ph) + 0.35 * np.sin(TWO_PI * 2 * ph) + 0.15 * np.sin(TWO_PI * 3 * ph)


@_sfx("siren_far", kind="sustained", norm="int", default_dur=8.0, space=0.0)
def _siren_far(dur, p, rng):
    """A police siren wailing far across the city: band-limited, mostly reverb, drifting."""
    n = _N(dur)
    f = _siren_wail(n, rng, float(p.get("period", 4.2)))
    x = _siren_tone(f, n)
    x = sos(x, "bandpass", (400, 2400), 2) * (1 + 0.3 * smooth_noise(n, 0.3, rng))
    out = dsp.reverb(x * 0.4, "alley", wet_db=0.0, dry=0.35)[:n]
    return fade(out, 0.8, 0.8)


@_sfx("siren_approach", kind="sustained", norm="max", default_dur=6.0, space=0.0)
def _siren_approach(dur, p, rng):
    """Siren(s) approaching: level rises, the top end opens, reverb gives way to the direct
    sound, slight upward Doppler. Ends close."""
    n = _N(dur)
    t = t_axis(n)
    u = np.clip(t / dur, 0, 1)
    f = _siren_wail(n, rng, 3.6) * (1 + 0.035 * u)
    x = _siren_tone(f, n) * db2lin(-20 * (1 - u) ** 1.4)
    x = tv_lowpass(x, 1400 + 5000 * u ** 1.5, q=0.7, block=256)
    far = dsp.reverb(x, "street", wet_db=0.0, dry=0.0)[:n] * (1 - u)[:, None] * 0.8
    st = to_stereo(x) * (0.3 + 0.7 * u)[:, None] + far
    return fade(st, 0.3, 0.05)


@_sfx("siren_pass", kind="sustained", norm="max", default_dur=5.0, space=0.0)
def _siren_pass(dur, p, rng):
    """Siren passing by (Doppler drop at the middle, level peak, pans left to right)."""
    n = _N(dur)
    t = t_axis(n)
    c, v, d0 = 343.0, 22.0, 6.0
    x_pos = v * (t - dur / 2)
    r = np.sqrt(x_pos ** 2 + d0 ** 2)
    cos_th = -x_pos / r
    dop = c / (c - v * cos_th)
    f = _siren_wail(n, rng, 3.4) * dop
    x = _siren_tone(f, n) / (r / d0)
    x = tv_lowpass(x, 1500 + 5500 * (d0 / r), q=0.7, block=256)
    pan = np.clip(x_pos / 15.0, -1, 1)
    th = (pan + 1) * np.pi / 4
    st = np.stack([x * np.cos(th), x * np.sin(th)], axis=1)
    st += dsp.reverb(x, "street", wet_db=-6.0, dry=0.0)[:n]
    return fade(st, 0.3, 0.3)


@_sfx("wind_gust", kind="sustained", norm="max", default_dur=3.0, space=0.0)
def _wind_gust(dur, p, rng):
    """A gust between buildings: band of moving air following the gust, turbulent flutter,
    a faint whistle."""
    n = _N(dur)
    env = _gust_env(n, rng, 0.4, 6.0)
    out = np.zeros((n, 2))
    for ch in range(2):
        x = tv_bandpass(pink(n, rng), 300 + 700 * env, q=0.8, block=128)
        x += 0.5 * sos(brown(n, rng), "lowpass", 300, 2)
        out[:, ch] = x * env * (1 + 0.2 * smooth_noise(n, 8, rng))
    wh = tv_bandpass(white(n, rng), 1100 + 600 * env, q=14, block=128) * env ** 2 * 0.6
    out += wh[:, None]
    return fade(out, 0.1, 0.2)


# ============================================================================ catalog check
def catalog_names_from_api(path=None):
    """Names listed in engine/API.md section 11 (used by QA to prove full coverage)."""
    import os
    import re
    path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine", "API.md")
    txt = open(path).read().split("## 11. SFX catalog")[1]
    sus = re.search(r"Sustained \(give `dur`\):(.*?)\n", txt).group(1)
    one = re.search(r"One-shots:(.*?)\n", txt).group(1)
    return re.findall(r"`([a-z_]+)`", sus) + re.findall(r"`([a-z_]+)`", one)


if __name__ == "__main__":
    api = catalog_names_from_api()
    missing = [n for n in api if n not in _REG]
    extra = [n for n in _REG if n not in api]
    print(f"catalog: {len(api)} names in API.md, {len(_REG)} implemented; missing={missing} extra={extra}")
