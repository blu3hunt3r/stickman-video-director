"""SALVAGE sound catalog: this film's sounds, procedurally, on top of audio.dsp / audio.sfx.

    render(name, dur=None, params=None, seed=0) -> float32 (n, 2) at 48 kHz
    anchor(name, params=None) -> seconds into the rendered sound that sits ON the cue time
    resolve(text) -> (catalog name, params) for a scene's free-text cue ('helmet clank' -> 'helmet_clank')
    names(), spec(name), exists(name)
    breathing_track / hiss_track / pump_track / winch_track / heartbeat_track / swell_track:
        long continuous layers the cue sheet and the beds build from event lists
    space_ir(kind), underwater(x, fc): the film's acoustic spaces (dusk / night air, underwater,
        wreck interior, paper, helmet, the bell's air and water reverbs)

Level convention = the shared library's (audio/sfx.py): at gain 0 every sound sits at REF_LUFS
(-16, narration level): one-shots by their loudest 400 ms, sustained sounds by integrated
loudness, true peak capped (-4 dBTP small one-shots, -1 dBTP designed hits / sustained). A cue's
gain_db then places the sound. Names not in this catalog fall through to audio.sfx.

Design rules: layered transient + body + tail, every component band-limited to its source, soft
onsets (no clicks), seed variation (different seeds = different takes). `anchor` lets a sound
carry pre-roll: the knife's leather scrape starts before the blade rings, the hose cut's swing
before the chop, the helmet's turn before the lock - the cue time is the hit itself.

Registry flags used by the mix: space (reverb-send factor of the scene's acoustic space; 0 = the
sound carries its own), hit (designed hit: lightly ducked), muffle (heard through water/helmet:
the mix low-passes it in underwater spaces; bubbles and breathing are voiced for the helmet
already).
"""
from __future__ import annotations

import functools
import math
import re

import numpy as np
from scipy import signal

from audio import dsp
from audio import sfx as libsfx
from audio.dsp import (SR, TWO_PI, ar_env, bandpass, brown, crackle, db2lin, exp_env, fade, mix_into,
                       n_of, onepole_lp, pink, resonator_bank, saturate, smooth_noise, sos, t_axis,
                       to_stereo, tv_bandpass, tv_lowpass, white)

REF_LUFS = libsfx.REF_LUFS
PEAK_CAP_DBTP = libsfx.PEAK_CAP_DBTP
HIT_PEAK_CAP_DBTP = libsfx.HIT_PEAK_CAP_DBTP
SUSTAINED_PEAK_CAP_DBTP = libsfx.SUSTAINED_PEAK_CAP_DBTP

BELL_PRIME = 146.832          # D3: the Meridian's bell strike note = the score's tonic (D)

_REG: dict = {}
_CACHE: dict = {}


def _sfx(name, kind="oneshot", norm="max", default_dur=None, space=1.0, hit=False, trim=0.0, muffle=True,
         anchor=0.0):
    def deco(fn):
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        _REG[name] = dict(fn=fn, kind=kind, norm=norm, default_dur=default_dur, space=space, hit=hit, trim=trim,
                          muffle=muffle, anchor=anchor, name=name, doc=doc)
        return fn
    return deco


def names():
    return sorted(_REG)


def exists(name):
    return name in _REG or libsfx.exists(name)


def spec(name):
    if name in _REG:
        return _REG[name]
    s = dict(libsfx.spec(name))
    s.setdefault("muffle", True)
    s.setdefault("anchor", 0.0)
    s["shared"] = True
    return s


def anchor(name, params=None):
    a = spec(name).get("anchor", 0.0)
    return float(a(params or {}) if callable(a) else a)


def _freeze(p):
    return tuple(sorted((k, repr(v)) for k, v in p.items()))


def _measure(x, mode):
    if mode == "int" and len(x) >= n_of(0.8):
        v = dsp.loudness_integrated(x)
        if np.isfinite(v):
            return v
    y = x if len(x) >= n_of(0.4) else dsp.pad_to(x, n_of(0.4))
    _, lk = dsp.loudness_curve(y, win=0.4, hop=0.05)
    return float(np.max(lk)) if len(lk) else -70.0


def render(name, dur=None, params=None, seed=0):
    """Render a sound as float32 (n, 2). dur: exact length for sustained sounds; for one-shots an
    optional maximum (truncated with a short fade)."""
    if name not in _REG:
        return libsfx.render(name, dur=dur, params=params, seed=seed)
    sp = _REG[name]
    p = dict(params or {})
    key = (name, None if dur is None else round(float(dur), 4), _freeze(p), int(seed))
    if key in _CACHE:
        return _CACHE[key].copy()
    rng = np.random.default_rng(dsp.stable_seed("salvage", name, seed))
    d = dur if (dur is not None and sp["kind"] == "sustained") else sp["default_dur"]
    if sp["kind"] == "sustained":
        d = max(0.05, float(d if d is not None else 3.0))
    res = sp["fn"](d, p, rng)
    extra = 0.0
    if isinstance(res, tuple):
        res, extra = res
    x = to_stereo(np.asarray(res, dtype=np.float64))
    x = sos(x, "highpass", 16.0, 2)
    if sp["kind"] == "sustained":
        x = dsp.pad_to(x, n_of(d))
    else:
        x = fade(x, 0.00015, 0.012, shape="lin")
    lvl = _measure(x, sp["norm"])
    if np.isfinite(lvl) and lvl > -120:
        x = x * db2lin(REF_LUFS + sp["trim"] - lvl)
    if sp["kind"] == "oneshot":
        cap = HIT_PEAK_CAP_DBTP if sp["hit"] else PEAK_CAP_DBTP
    else:
        cap = SUSTAINED_PEAK_CAP_DBTP
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
    if len(_CACHE) > 300:
        _CACHE.clear()
    _CACHE[key] = out
    return out.copy()


# ============================================================================ helpers
def _N(t):
    return max(1, n_of(t))


def _place(out, x, t, gain=1.0):
    return mix_into(out, x, n_of(t), gain)


def _ramp(x, ms):
    """Raised-sine onset over ms (in place)."""
    k = min(len(x), n_of(ms / 1000.0))
    if k > 1:
        r = np.sin(0.5 * np.pi * np.linspace(0.0, 1.0, k)) ** 2
        x[:k] *= r if x.ndim == 1 else r[:, None]
    return x


def _sum(*xs):
    n = max(len(x) for x in xs)
    out = np.zeros((n,) + np.shape(xs[0])[1:])
    for x in xs:
        out[:len(x)] += x
    return out


def _noise(n, rng, color="white"):
    return white(n, rng) if color == "white" else pink(n, rng) if color == "pink" else brown(n, rng)


def _burst(n, rng, lo=None, hi=None, attack=0.0005, t60=0.05, color="white", order=2, hold=0.0):
    x = _noise(n, rng, color)
    if lo and hi:
        x = bandpass(x, lo, hi, order)
    elif hi:
        x = sos(x, "lowpass", hi, order)
    elif lo:
        x = sos(x, "highpass", lo, order)
    return x * ar_env(n, attack, t60, hold=hold)


def _modes(rng, freqs, t60s, amps=None, n=None, spread=0.0, attack=0.0004, beat=0.0):
    """Struck object: decaying sinusoids, random phases; beat > 0 splits each mode into a beating
    doublet (asymmetric bodies: bells, helmets)."""
    freqs = np.asarray(freqs, dtype=np.float64)
    freqs = freqs * (1.0 + spread * rng.uniform(-1, 1, len(freqs)))
    t60s = np.broadcast_to(np.asarray(t60s, dtype=np.float64), freqs.shape)
    if amps is None:
        amps = 1.0 / np.sqrt(np.arange(1, len(freqs) + 1))
    amps = np.broadcast_to(np.asarray(amps, dtype=np.float64), freqs.shape)
    n = n or _N(float(np.max(t60s)) * 1.15 + 0.01)
    if beat:
        y = dsp.modal(freqs - 0.5 * beat, t60s, amps * 0.56, n, phases=rng.uniform(0, TWO_PI, len(freqs)), attack=attack)
        y += dsp.modal(freqs + 0.5 * beat, t60s, amps * 0.44, n, phases=rng.uniform(0, TWO_PI, len(freqs)), attack=attack)
        return y
    return dsp.modal(freqs, t60s, amps, n, phases=rng.uniform(0, TWO_PI, len(freqs)), attack=attack)


def _thump(n, f0, f1, tp, t60, attack=0.002):
    """Sine thump with an exponential pitch drop f0 -> f1."""
    t = t_axis(n)
    f = f1 + (f0 - f1) * np.exp(-t / max(tp, 1e-4))
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * exp_env(n, t60)
    return _ramp(y, attack * 1000.0)


def _bubble(rng, f0, q=14.0, rise=0.3, onset_ms=1.0):
    """One bubble: a Minnaert-resonance sinusoid (f0 ~ 3.3 / radius m) damped with quality q,
    its pitch rising as the bubble detaches and rises."""
    tau = q / (math.pi * f0)
    m = _N(tau * 6.5)
    tt = t_axis(m)
    f = f0 * (1.0 + rise * (1.0 - np.exp(-tt / (2.5 * tau))))
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * np.exp(-tt / tau)
    return _ramp(y, onset_ms)


def _bubbles(out, rng, times, fmin, fmax, amp=(0.3, 1.0), q=(9.0, 18.0), rise=(0.05, 0.4), size_weight=0.35):
    lf0, lf1 = math.log(fmin), math.log(fmax)
    for tt in times:
        f0 = math.exp(rng.uniform(lf0, lf1))
        b = _bubble(rng, f0, rng.uniform(*q), rng.uniform(*rise))
        _place(out, b, tt, rng.uniform(*amp) * (300.0 / f0) ** size_weight)
    return out


def _droplet(rng, f0, d):
    """A droplet hitting water in air: a short rising 'plip'."""
    m = _N(d * 5)
    tt = t_axis(m)
    f = f0 * (1.0 + 0.7 * (1.0 - np.exp(-tt / (d * 0.8))))
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * np.exp(-tt / d)
    return _ramp(y, 0.15)


def _env_sin(n, a, s, r, sr=SR):
    """Sine-shaped attack a, hold s, sine release r (seconds)."""
    t = t_axis(n, sr)
    e = np.ones(n)
    if a > 0:
        m = t < a
        e[m] = np.sin(0.5 * np.pi * t[m] / a) ** 2
    m = t > a + s
    e[m] = np.cos(0.5 * np.pi * np.clip((t[m] - a - s) / max(r, 1e-4), 0, 1)) ** 2
    return e


def _smoothstep(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)


def underwater(x, fc=1600.0, lift_db=2.5, order=4):
    """Heard through water and a copper helmet: steep low-pass at fc and a little low-mid weight."""
    y = sos(np.asarray(x, dtype=np.float64), "lowpass", fc, order)
    if lift_db:
        y = dsp.biquad(y, "lowshelf", 260.0, 0.7, lift_db)
    return y


def _wide(x, rng, amount=0.5):
    x = np.asarray(x, dtype=np.float64)
    return x if x.ndim == 2 else dsp.decorrelate(x, rng, amount=amount)


def _tf(x, frac=0.3, mx=0.35):
    """Sine fade over the last frac of a sub-buffer (at most mx s): no buffer ends on a cliff."""
    return fade(x, 0.0, min(mx, frac * len(x) / SR))


def _rms(x):
    return max(1e-9, float(np.sqrt(np.mean(np.square(x))))) if len(x) else 1e-9


def _pk(x):
    return max(1e-9, float(np.max(np.abs(x)))) if len(x) else 1e-9


def _pan_sweep(x, p0, p1):
    n = len(x)
    pan = np.linspace(p0, p1, n)
    th = (pan + 1.0) * np.pi / 4.0
    return np.stack([x * np.cos(th), x * np.sin(th)], axis=1)


# ============================================================================ spaces (impulse responses)
# t60 mid (s), low / high T60 multipliers, pre-delay, early-reflection count / span / gain, tail
# brightness LP, flutter (parallel steel walls), modes (resonant ringing of a steel enclosure),
# build (tail diffusion time as a fraction of t60)
_SPACE_SPECS = {
    "dusk_air":   dict(t60=0.85, lo=0.8, hi=0.45, pre=0.011, er=5, er_span=0.06, er_g=0.5, lp=6500),
    "night_air":  dict(t60=1.25, lo=0.9, hi=0.4, pre=0.013, er=5, er_span=0.07, er_g=0.45, lp=5200),
    "underwater": dict(t60=2.5, lo=1.3, hi=0.35, pre=0.007, er=8, er_span=0.03, er_g=0.25, lp=1700, build=0.1),
    "wreck":      dict(t60=2.1, lo=1.1, hi=0.5, pre=0.004, er=14, er_span=0.045, er_g=0.5, lp=2600, flutter=0.0125,
                       modes=((87.0, 30.0, 0.5), (141.0, 35.0, 0.4), (233.0, 40.0, 0.35), (389.0, 45.0, 0.25),
                              (612.0, 50.0, 0.2))),
    "paper":      dict(t60=0.28, lo=0.9, hi=0.7, pre=0.002, er=8, er_span=0.012, er_g=0.5, lp=9000),
    "bell_air":   dict(t60=4.6, lo=1.25, hi=0.45, pre=0.03, er=6, er_span=0.12, er_g=0.3, lp=5200, build=0.08),
    "bell_water": dict(t60=5.5, lo=1.4, hi=0.3, pre=0.02, er=6, er_span=0.06, er_g=0.2, lp=1300, build=0.12),
    "score_hall": dict(t60=3.2, lo=1.3, hi=0.5, pre=0.026, er=14, er_span=0.09, er_g=0.3, lp=6000),
}
SPACES = tuple(_SPACE_SPECS)


@functools.lru_cache(maxsize=16)
def space_ir(kind, seed=0):
    """Synthesised stereo impulse response (unit energy per channel), float64 (m, 2)."""
    sp = _SPACE_SPECS[kind]
    rng = np.random.default_rng(dsp.stable_seed("salvage-ir", kind, seed))
    t60 = sp["t60"]
    length = min(7.0, t60 * 1.3 + sp["pre"] + 0.05)
    n = n_of(length)
    t = t_axis(n)
    ir = np.zeros((n, 2))
    for ch in range(2):
        nz = rng.standard_normal(n)
        lo = sos(nz, "lowpass", 400.0, 2)
        hi = sos(nz, "highpass", 3000.0, 2)
        mid = nz - lo - hi
        tail = (lo * np.power(10.0, -3.0 * t / (t60 * sp["lo"])) + mid * np.power(10.0, -3.0 * t / t60)
                + hi * np.power(10.0, -3.0 * t / (t60 * sp["hi"])))
        tail *= 1.0 - np.exp(-t / max(0.004, sp.get("build", 0.06) * t60))
        tail = onepole_lp(tail, sp["lp"])
        if sp.get("modes"):
            md = sp["modes"]
            tail = tail + 0.8 * resonator_bank(tail, [m[0] * rng.uniform(0.98, 1.02) for m in md], [m[1] for m in md],
                                               [m[2] for m in md])
        er = np.zeros(n)
        if sp["er"]:
            times = np.sort(rng.uniform(0.0015, sp["er_span"], sp["er"]))
            gains = sp["er_g"] * rng.uniform(0.4, 1.0, sp["er"]) * np.exp(-times / max(sp["er_span"], 1e-3))
            gains *= rng.choice([-1.0, 1.0], sp["er"])
            for tt, gg in zip(times, gains):
                i = n_of(tt)
                if i < n:
                    er[i] += gg
        if sp.get("flutter"):
            per = sp["flutter"] * (1.0 + 0.02 * (ch - 0.5))
            k = 1
            while k * per < t60 * 0.5:
                i = n_of(k * per)
                if i < n:
                    er[i] += 0.45 * sp["er_g"] * math.pow(10.0, -3.0 * k * per / (t60 * 0.5)) * (1 if k % 2 else -1)
                k += 1
        er = onepole_lp(er, sp["lp"] * 0.8)
        tail /= max(1e-12, np.sqrt(np.sum(tail ** 2)))
        e_er = np.sqrt(np.sum(er ** 2))
        if e_er > 0:
            er = er / e_er * 0.55
        c = tail + er
        pre = n_of(sp["pre"])
        c = np.concatenate([np.zeros(pre), c])[:n]
        ramp = min(n, n_of(0.002))
        c[:ramp] *= np.linspace(0, 1, ramp)
        c = fade(c, 0.0, min(0.3, length * 0.2))
        ir[:, ch] = c / max(1e-12, np.sqrt(np.sum(c ** 2)))
    return ir


def wet(x, kind, wet_db, seed=0):
    """Wet signal only (stereo, lengthened by the IR tail) of mono/stereo x in space `kind`."""
    x = np.asarray(x, dtype=np.float64)
    m = x if x.ndim == 1 else x.mean(axis=1)
    return dsp.convolve(m, space_ir(kind, seed)) * db2lin(wet_db)


@functools.lru_cache(maxsize=4)
def _helmet_ir(seed=0):
    """Inside the copper helmet: dense reflections within a few ms (a 30 cm metal sphere) and the
    shell's own faint ring."""
    rng = np.random.default_rng(4100 + seed)
    n = _N(0.09)
    ir = np.zeros(n)
    ir[0] = 1.0
    for d, g in ((0.00085, 0.42), (0.0016, -0.30), (0.0024, 0.22), (0.0033, -0.15), (0.0047, 0.10), (0.0061, -0.07)):
        ir[n_of(d)] += g
    ir += dsp.modal([430.0, 1080.0, 1920.0, 2950.0, 4100.0], [0.05, 0.04, 0.03, 0.025, 0.02],
                    [0.05, 0.04, 0.03, 0.02, 0.012], n, phases=rng.uniform(0, TWO_PI, 5), attack=0.0)
    return ir / np.sqrt(np.sum(ir ** 2))


def in_helmet(x):
    return signal.fftconvolve(np.asarray(x, dtype=np.float64), _helmet_ir())[:len(x)]


# ============================================================================ THE BELL
# Minor-third bell partials (ratio to the prime, strike amplitude, T60 s, doublet beat Hz). The
# tierce is the minor third, so the bell itself sounds D minor: hum D2, prime D3, tierce F3,
# quint A3, nominal D4, then the slightly inharmonic uppers that make it a bell, not an organ.
BELL_PARTIALS = (
    (0.500, 0.60, 44.0, 0.09),     # hum        D2
    (1.000, 0.42, 26.0, 0.21),     # prime      D3  (strike note)
    (1.200, 0.55, 20.0, 0.33),     # tierce     F3
    (1.497, 0.14, 8.5, 0.47),      # quint      A3
    (2.000, 1.00, 15.0, 0.58),     # nominal    D4
    (2.515, 0.18, 6.0, 0.83),      # deciem
    (2.662, 0.26, 5.4, 0.97),      # undeciem
    (3.002, 0.34, 5.8, 1.21),      # twelfth    A4
    (3.364, 0.12, 3.9, 1.40),
    (4.000, 0.26, 4.0, 1.63),      # upper octave D5
    (4.240, 0.10, 3.1, 1.90),
    (5.010, 0.15, 2.7, 2.20),
    (5.340, 0.09, 2.3, 2.50),
    (6.010, 0.08, 1.8, 2.90),
    (6.680, 0.06, 1.5, 3.30),
    (7.330, 0.045, 1.2, 3.70),
    (8.020, 0.04, 1.0, 4.10),
    (9.100, 0.03, 0.75, 4.60),
)


def bell_core(rng, n, strike=0.8, prime=BELL_PRIME, swing=None, t60_scale=1.0, soft_ms=0.6):
    """Modal bell (stereo): every partial a beating doublet with its own decay; strike 0..1 sets the
    clapper hardness (upper partials); swing = (period s, Doppler ms, directivity dB) for a bell
    swinging on its davit: a slow pitch sway and the upper partials breathing as the mouth turns."""
    t = t_axis(n)
    out = np.zeros((n, 2))
    sw_ph = rng.uniform(0, TWO_PI)
    for ratio, amp, t60, beat in BELL_PARTIALS:
        f = prime * ratio
        if f > 0.45 * SR:
            continue
        a = amp
        if ratio > 2.05:
            a *= math.exp(-(ratio - 2.0) / (0.3 + 3.2 * strike))
        if ratio < 0.75:
            a *= 1.0 + 0.35 * (1.0 - strike)
        T = t60 * t60_scale
        m = min(n, n_of(T * 1.3) + 1)
        if m < 32:
            continue
        tt = t[:m]
        env = np.power(10.0, -3.0 * tt / T)
        if ratio >= 1.9:                      # the clang: a fast first stage on the upper partials
            env = 0.62 * env + 0.38 * np.power(10.0, -3.0 * tt / (T / 6.0))
        # the doublet's two modes are a property of the bronze (one beat rate); both start in
        # phase at the strike; the two "mics" see the modes' different orientations (amplitude split)
        b = beat * rng.uniform(0.85, 1.2)
        split = rng.uniform(0.5, 0.7)
        ph0 = rng.uniform(-0.25, 0.25)
        for ch in range(2):
            w1 = split if ch == 0 else 1.0 - split + 0.1
            pm = 0.0
            g = a * env
            if swing:
                P, dop_ms, am_db = swing
                arg = TWO_PI * tt / P + sw_ph + 0.35 * ch
                pm = TWO_PI * f * (dop_ms * 1e-3) * np.sin(arg)
                if ratio >= 1.9:
                    g = g * db2lin(am_db * np.sin(arg - 0.7))
            s = (w1 * np.sin(TWO_PI * (f - 0.5 * b) * tt + ph0 + pm)
                 + (1.0 - w1) * np.sin(TWO_PI * (f + 0.5 * b) * tt + ph0 + pm))
            out[:m, ch] += g * s
    return _ramp(out, soft_ms)


def _clapper(rng, strike):
    """The iron clapper hitting the soundbow: a hard tock, a dense inharmonic clang, the mass thud."""
    n = _N(0.6)
    out = np.zeros(n)
    _place(out, _burst(_N(0.03), rng, lo=1100, t60=0.009, attack=0.00015), 0.0, 1.1 * strike)
    fr = np.exp(rng.uniform(math.log(950.0), math.log(7800.0), 22))
    clang = _modes(rng, fr, rng.uniform(0.05, 0.35, 22), rng.uniform(0.3, 1.0, 22) / np.sqrt(fr / 1000.0), n=n, attack=0.0002)
    out += clang * 0.32 * strike ** 1.5
    _place(out, _thump(_N(0.55), 74.0, 47.0, 0.03, 0.42, attack=0.001), 0.0, 0.55 * strike)
    return out


@_sfx("meridian_bell", space=0.0, hit=True, trim=4.0, muffle=False)
def _meridian_bell(dur, p, rng):
    """The Meridian's bell in air: a minor-third bell in D struck by its iron clapper, swinging on
    the davit (slow Doppler sway, the upper partials breathing), a long night-sea reverb.
    params: strike 0..1 (0.85), length s (20), swing period s (3.4; 0 = still), verb air|dry."""
    strike = float(p.get("strike", 0.85))
    L = float(p.get("length", 20.0))
    P = float(p.get("swing", 3.4))
    n = _N(L)
    x = bell_core(rng, n, strike, swing=(P, 1.1, 1.8) if P > 0 else None)
    cl = _clapper(rng, strike)
    k = min(n, len(cl))
    x[:k] += cl[:k, None]
    if p.get("verb", "air") == "air":
        x = x + wet(x, "bell_air", -9.0)[:n]
    return fade(x, 0.0, min(3.0, L * 0.25))


@_sfx("meridian_bell_uw", space=0.0, trim=0.0, muffle=False)
def _meridian_bell_uw(dur, p, rng):
    """The bell heard underwater (s05): nudged by the current, not struck - a dull swelling note on
    D (hum, prime and the tierce's minor third), everything above ~650 Hz lost in the water, a
    slow sway, a long dark underwater reverb. params: length s (9)."""
    L = float(p.get("length", 9.0))
    n = _N(L)
    x = bell_core(rng, n, strike=0.06, swing=(2.6, 0.6, 1.0), t60_scale=0.55, soft_ms=28.0)
    knock = _thump(_N(0.5), 96.0, 58.0, 0.03, 0.3, attack=0.004) * 0.35
    _place(knock, _burst(_N(0.2), rng, hi=420, t60=0.08, attack=0.004, color="brown"), 0.0, 0.25 / 3.0)
    x[:len(knock)] += knock[:, None]
    x = underwater(x, 650.0, lift_db=3.0)
    out = 0.65 * x + wet(x, "bell_water", -3.0)[:n]
    return fade(out, 0.0, min(2.5, L * 0.3))


# ============================================================================ the diver: breathing, hiss, bubbles
def _breath_noise(n, rng, formants, lo, hi):
    src = 0.55 * pink(n, rng) + 0.45 * white(n, rng)
    v = resonator_bank(src, [f for f, _, _ in formants], [q for _, q, _ in formants], [g for _, _, g in formants])
    return bandpass(v, lo, hi, 2) + 0.1 * bandpass(src, 2500.0, 7500.0, 2)


def breath_in(rng, dur, size=1.0):
    """An inhale inside the helmet: breathy noise through the mouth's resonances, swelling, cut."""
    n = _N(dur + 0.12)
    t = t_axis(n)
    v = _breath_noise(n, rng, [(560.0, 3.0, 1.0), (1180.0, 3.5, 0.75), (2450.0, 4.5, 0.45), (3500.0, 5.0, 0.25)], 160.0, 6500.0)
    u = np.clip(t / dur, 0, 1)
    env = np.sin(0.5 * np.pi * u) ** 1.6 * (0.7 + 0.3 * u)
    after = t > dur
    env[after] = env[np.argmax(after) - 1 if after.any() else -1] * np.exp(-(t[after] - dur) / 0.035)
    return v * env * (1.0 + 0.12 * smooth_noise(n, 9.0, rng)) * size


def breath_out(rng, dur, size=1.0):
    """An exhale inside the helmet: lower, softer, quick swell and a long sigh."""
    n = _N(dur + 0.2)
    t = t_axis(n)
    v = _breath_noise(n, rng, [(470.0, 3.0, 1.0), (1020.0, 3.5, 0.6), (2150.0, 4.5, 0.3)], 120.0, 4500.0)
    u = np.clip(t / dur, 0, 1)
    env = np.clip(t / 0.12, 0, 1) ** 1.5 * (1.0 - u) ** 1.4
    return v * env * (1.0 + 0.1 * smooth_noise(n, 7.0, rng)) * 0.75 * size


def exhaust_burst(rng, dur=1.0, size=1.0):
    """The exhaust valve venting an exhale: glugs of big bubbles (85-340 Hz), a few small ones,
    turbulent gurgle under them, tapering - heard through the helmet (low-passed)."""
    n = _N(dur + 0.5)
    out = np.zeros(n)
    t = 0.0
    while t < dur:
        u = t / dur
        rate = 15.0 - 7.0 * u
        a = 1.0 - 0.55 * u
        for j in range(int(rng.integers(1, 4))):
            f0 = math.exp(rng.uniform(math.log(85.0), math.log(340.0))) / size ** 0.3
            _place(out, _bubble(rng, f0, rng.uniform(7.0, 15.0), rng.uniform(0.05, 0.35)), t + j * rng.uniform(0.006, 0.025),
                   a * rng.uniform(0.5, 1.0))
        for _ in range(int(rng.poisson(2.5))):
            f0 = math.exp(rng.uniform(math.log(420.0), math.log(1600.0)))
            _place(out, _bubble(rng, f0, rng.uniform(10.0, 20.0), rng.uniform(0.1, 0.5)), t + rng.uniform(0, 0.05),
                   a * rng.uniform(0.06, 0.22))
        t += float(np.clip(rng.exponential(1.0 / rate), 0.035, 0.2))
    tt = t_axis(n)
    g = bandpass(pink(n, rng), 70.0, 420.0, 2)
    genv = np.clip(tt / 0.04, 0, 1) * _smoothstep((dur + 0.3 - tt) / 0.45)
    pk = max(1e-9, np.max(np.abs(out)))
    out += 0.3 * pk * g / max(1e-9, np.max(np.abs(g))) * genv * (0.6 + 0.4 * np.abs(smooth_noise(n, 12.0, rng)))
    return sos(out, "lowpass", 2200.0, 2)


def breathing_track(events, n, seed=0):
    """The diver's breathing from an event list. events: dict(t, inhale, hold, exhale, size, bub,
    bub_delay, bub_len, bub_size) - seconds relative to the track start; inhale or exhale may be 0
    (a held breath, a lone sigh, a burst of bubbles). Returns (breath (n,), bubbles (n,)): the
    breath is inside the helmet (helmet acoustics), the bubbles outside."""
    rng = np.random.default_rng(dsp.stable_seed("salvage-breathing", seed))
    br = np.zeros(n)
    bub = np.zeros(n)
    for e in events:
        t0 = float(e["t"])
        size = float(e.get("size", 1.0))
        if e.get("inhale", 0) > 0:
            _place(br, breath_in(rng, float(e["inhale"]), size), t0)
            t0 += float(e["inhale"]) + float(e.get("hold", 0.25))
        if e.get("exhale", 0) > 0:
            _place(br, breath_out(rng, float(e["exhale"]), size), t0, 0.8)
        if e.get("bub", 1.0) > 0 and (e.get("exhale", 0) > 0 or e.get("bub_len")):
            ex = float(e.get("exhale", 0) or 1.0)
            bd = t0 + float(e.get("bub_delay", 0.35 * ex))
            _place(bub, exhaust_burst(rng, float(e.get("bub_len", 0.75 * ex)), float(e.get("bub_size", 1.0))), bd,
                   float(e.get("bub", 1.0)))
    return in_helmet(br), bub


def periodic_breaths(t0, t1, period=4.6, rng=None, jitter=0.08, inhale=1.45, exhale=1.9, size=1.0, bub=1.0):
    """Regular free-flow breathing between t0 and t1 (event list for breathing_track)."""
    rng = rng or np.random.default_rng(0)
    ev = []
    t = t0
    while t < t1 - 0.5:
        j = 1.0 + jitter * rng.uniform(-1, 1)
        ev.append(dict(t=t, inhale=inhale * j, hold=0.22 * j, exhale=exhale * j, size=size * rng.uniform(0.85, 1.1),
                       bub=bub * rng.uniform(0.75, 1.0)))
        t += period * j
    return ev


def hiss_track(n, rng, rpm=26.0):
    """Free-flow air entering the helmet: a resonant hiss inside the copper shell, pulsing with the
    pump's strokes (two per revolution)."""
    x = bandpass(white(n, rng), 700.0, 9500.0, 2)
    x = resonator_bank(x, [880.0, 1650.0, 2750.0, 4150.0, 6300.0], [3.0, 3.5, 4.5, 5.0, 4.0],
                       [1.0, 0.85, 0.65, 0.45, 0.25]) + 0.3 * x
    rate = (rpm * 2.0 / 60.0) * (1.0 + 0.04 * smooth_noise(n, 0.3, rng))
    ph = np.cumsum(rate) / SR
    pulse = (0.5 - 0.5 * np.cos(TWO_PI * ph)) ** 1.6
    return x * (0.6 + 0.4 * pulse) * (1.0 + 0.06 * smooth_noise(n, 2.5, rng))


@_sfx("helmet_breath", kind="sustained", norm="int", default_dur=10.0, space=0.0, muffle=False)
def _helmet_breath(dur, p, rng):
    """Free-flow helmet breathing (preview / scene cue): inhale with the air hiss, exhale venting as
    bubble bursts. params: period s (4.6), hiss 0..1 (0.35), bubbles 0..1 (1)."""
    n = _N(dur)
    ev = periodic_breaths(0.2, dur, float(p.get("period", 4.6)), rng)
    br, bub = breathing_track(ev, n, int(rng.integers(1 << 30)))
    hs = hiss_track(n, rng) * float(p.get("hiss", 0.35))
    out = br / _rms(br) * 0.12
    out += bub / _rms(bub) * 0.08 * float(p.get("bubbles", 1.0))
    out += hs / _rms(hs) * 0.03
    return fade(_wide(out, rng, 0.25), 0.1, 0.1)


@_sfx("helmet_hiss", kind="sustained", norm="int", default_dur=5.0, space=0.0, muffle=False)
def _helmet_hiss(dur, p, rng):
    """Free-flow air hissing into the helmet, pulsing with the pump. params: rpm (26)."""
    return fade(_wide(hiss_track(_N(dur), rng, float(p.get("rpm", 26.0))), rng, 0.3), 0.05, 0.05)


@_sfx("breath_single", space=0.0, muffle=False)
def _breath_single(dur, p, rng):
    """One breath in the sealed helmet, no air flowing (s13): phase in|out, length s (1.4)."""
    L = float(p.get("length", 1.4))
    x = breath_in(rng, L) if p.get("phase", "in") == "in" else breath_out(rng, L)
    return in_helmet(x)


@_sfx("exhaust_bubbles", space=0.5, muffle=False)
def _exhaust_bubbles(dur, p, rng):
    """One exhale venting from the helmet's exhaust valve: glugging big bubbles. size 0..2 (1)."""
    s = float(p.get("size", 1.0))
    return _wide(exhaust_burst(rng, 0.7 + 0.5 * s, max(0.3, s)), rng, 0.35)


def _stream(n, rng, rate, fmin=250.0, fmax=1500.0):
    out = np.zeros(n)
    times = dsp.poisson_times(rate, n / SR, rng)
    _bubbles(out, rng, times, fmin, fmax, amp=(0.15, 1.0), q=(10.0, 20.0), rise=(0.1, 0.6))
    return out


@_sfx("bubble_stream", kind="sustained", norm="int", default_dur=4.0, space=0.4, muffle=False)
def _bubble_stream(dur, p, rng):
    """A rising stream of exhaust bubbles seen from outside, bursting into smaller ones, with the
    soft fizz of the column. params: density per s (22)."""
    n = _N(dur)
    r = float(p.get("density", 22.0))
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = _stream(n, rng, r * 0.55, 220.0, 1400.0)
    fizz = bandpass(white(n, rng), 1200.0, 4500.0, 2) * 0.004 * (1 + 0.5 * smooth_noise(n, 3.0, rng))
    out += fizz[:, None]
    return fade(sos(out, "lowpass", 3200.0, 2), 0.2, 0.2)


@_sfx("bubble_release", space=0.6, hit=True, trim=1.0, muffle=False)
def _bubble_release(dur, p, rng):
    """The big release (s13, weights shed): the suit and helmet venting at once - a roaring cloud of
    big bubbles swelling and thinning as he starts to rise, a low rumble under it."""
    n = _N(3.4)
    t = t_axis(n)
    out = np.zeros(n)
    env_rate = lambda tt: 160.0 * (math.exp(-((tt - 0.5) / 0.55) ** 2) + 0.35 * math.exp(-tt / 1.4))  # noqa: E731
    times = dsp.poisson_times(env_rate, 3.0, rng)
    _bubbles(out, rng, times, 60.0, 520.0, amp=(0.3, 1.0), q=(6.0, 14.0), rise=(0.05, 0.4), size_weight=0.45)
    small = np.zeros(n)
    _bubbles(small, rng, dsp.poisson_times(lambda tt: 0.8 * env_rate(tt), 3.0, rng), 500.0, 2200.0, amp=(0.05, 0.3))
    rum = bandpass(brown(n, rng), 35.0, 260.0, 2)
    renv = np.clip(t / 0.15, 0, 1) * np.exp(-np.maximum(t - 0.6, 0) / 0.9)
    pk = max(1e-9, np.max(np.abs(out)))
    out = out + 0.4 * small + 0.55 * pk * rum / max(1e-9, np.max(np.abs(rum))) * renv
    out = sos(out, "lowpass", 2400.0, 2)
    return fade(_wide(out, rng, 0.5), 0.003, 0.4)


@_sfx("surface_pops", space=0.5, muffle=False)
def _surface_pops(dur, p, rng):
    """Bubbles reaching the surface (s02 IN): the last muffled glugs below, then crisp pops and
    tiny droplet plips in the air as they burst."""
    n = _N(1.8)
    out = np.zeros(n)
    below = np.zeros(n)
    _bubbles(below, rng, np.sort(rng.uniform(0.0, 0.7, 14)), 150.0, 900.0, amp=(0.3, 1.0))
    out += sos(below, "lowpass", 1500.0, 2) * 0.8
    for tt in np.sort(0.45 + rng.exponential(0.35, 18)):
        if tt > 1.6:
            continue
        pop = _burst(_N(0.004), rng, lo=2500, t60=0.0015, attack=0.0001) * 0.5
        pop = _sum(pop, _droplet(rng, rng.uniform(1800.0, 4200.0), rng.uniform(0.003, 0.007)) * 0.6)
        _place(out, pop, tt, rng.uniform(0.15, 0.6))
    return _wide(out, rng, 0.4)


@_sfx("hose_bubbles", space=0.8, muffle=False)
def _hose_bubbles(dur, p, rng):
    """The severed hose sinking (s12 OUT): the air left in it escaping in a few lazy big bubbles."""
    n = _N(3.2)
    out = np.zeros(n)
    t = 0.0
    k = 0
    while t < 2.7:
        f0 = math.exp(rng.uniform(math.log(90.0), math.log(260.0)))
        _place(out, _bubble(rng, f0, rng.uniform(6.0, 11.0), rng.uniform(0.1, 0.3)), t, 0.9 * math.exp(-t / 1.8))
        if rng.uniform() < 0.5:
            _place(out, _bubble(rng, f0 * rng.uniform(2.5, 4.0), 14.0, 0.3), t + 0.03, 0.2)
        t += rng.uniform(0.25, 0.75) * (1.0 + 0.4 * k)
        k += 1
    return sos(out, "lowpass", 1800.0, 2)


# ============================================================================ boat and deck
def _chuff(rng, speed=1.0, cyl=0, open_end=False):
    """One compression stroke of the hand pump: air through the valve chest + the leather flap."""
    L = 0.42 / max(speed, 0.35) ** 0.5
    n = _N(L + 0.12)
    t = t_axis(n)
    src = 0.6 * pink(n, rng) + 0.4 * white(n, rng)
    if open_end:      # severed hose: a hard jet
        x = bandpass(src, 900.0, 10000.0, 2) * 1.3
    else:
        x = resonator_bank(src, [390.0 + 40 * cyl, 1060.0 - 60 * cyl, 2350.0], [3.0, 3.5, 4.0], [1.0, 0.6, 0.3])
        x += 0.25 * bandpass(src, 300.0, 4000.0, 2)
    x *= np.clip(t / 0.035, 0, 1) ** 1.5 * np.exp(-t / (0.12 * L / 0.42))
    flap = _modes(rng, [820.0 + 60 * cyl, 1630.0, 2470.0], [0.035, 0.028, 0.02], [1.0, 0.5, 0.25], n=_N(0.06), attack=0.0003)
    _place(x, flap, 0.0, 0.08)
    return x


def pump_track(n, rng, rpm=26.0, spinup=1.5, rundown_at=None, rundown=3.2, open_after=None):
    """The diving pump on deck: two cylinders (a chuff each half turn), leather valves, crank knocks
    at the dead points, the flywheel's spoked whir; optional spin-up and run-down. open_after (s):
    from then on the strokes blow out of a severed hose."""
    t = t_axis(n)
    w0 = rpm / 60.0
    w = np.full(n, w0) * (1.0 + 0.03 * smooth_noise(n, 0.4, rng))
    if spinup > 0:
        w *= _smoothstep(t / spinup) * 0.9 + 0.1 * (t > 0)
    if rundown_at is not None:
        w *= np.where(t < rundown_at, 1.0, np.exp(-np.maximum(t - rundown_at, 0) / max(rundown / 2.5, 1e-3)))
    phase = np.cumsum(w) / SR
    out = np.zeros(n)
    half = np.floor(phase * 2.0)
    idx = np.nonzero(np.diff(half) > 0)[0] + 1
    for k in idx:
        sp = w[k] / w0
        if sp < 0.06:
            continue
        tt = k / SR
        cyl = int(half[k]) % 2
        op = open_after is not None and tt >= open_after
        _place(out, _chuff(rng, sp, cyl, op), tt, (2.2 if op else 1.0) * sp ** 1.2)
        knock = _modes(rng, np.array([300.0, 720.0, 1310.0]) * rng.uniform(0.96, 1.04), [0.12, 0.09, 0.06], [1.0, 0.5, 0.25],
                       n=_N(0.2), attack=0.0005)
        _place(out, knock, tt + 0.5 / max(w[k] * 2.0, 0.2) * 0.5, 0.05 * sp)
    whir = sos(brown(n, rng), "lowpass", 260.0, 2) * (0.55 + 0.45 * (0.5 + 0.5 * np.cos(TWO_PI * 6.0 * phase)))
    whir *= w / w0
    belt = bandpass(pink(n, rng), 300.0, 1200.0, 2) * (0.5 + 0.5 * np.cos(TWO_PI * 3.0 * phase)) ** 3 * (w / w0)
    pk = max(1e-9, np.sqrt(np.mean(out ** 2)))
    out += pk * (0.9 * whir / max(1e-9, np.sqrt(np.mean(whir ** 2))) + 0.3 * belt / max(1e-9, np.sqrt(np.mean(belt ** 2))))
    return out


@_sfx("pump_run", kind="sustained", norm="int", default_dur=6.0, space=1.0, muffle=False)
def _pump_run(dur, p, rng):
    """The hand pump running on deck. params: rpm (26), spinup s (1.5), rundown_at s, rundown s (3.2)."""
    n = _N(dur)
    ra = p.get("rundown_at")
    x = pump_track(n, rng, float(p.get("rpm", 26.0)), float(p.get("spinup", 1.5)), None if ra is None else float(ra),
                   float(p.get("rundown", 3.2)))
    return fade(_wide(x, rng, 0.3), 0.02, 0.05)


def _pawl(rng):
    n = _N(0.09)
    x = _modes(rng, np.array([2350.0, 3650.0, 5300.0, 7400.0]) * rng.uniform(0.95, 1.05), [0.035, 0.028, 0.02, 0.014],
               [1.0, 0.7, 0.45, 0.3], n=n, attack=0.0002)
    x += 0.8 * _modes(rng, np.array([430.0, 790.0, 1380.0]) * rng.uniform(0.95, 1.05), [0.06, 0.045, 0.03], [1.0, 0.6, 0.35],
                      n=n, attack=0.0003)
    x[:_N(0.006)] += _burst(_N(0.006), rng, lo=2500, t60=0.002, attack=0.0001) * 0.6
    return x


def winch_track(n, rng, rate=0.42, load=0.5, teeth=12):
    """A hand winch being cranked: the pawl clacking over the ratchet (uneven human cranking: the
    down-stroke fast, the up-stroke slow), the drum and line groaning with the load, hemp creaks,
    the handle's squeak once a turn."""
    base = rate * (1.0 + 0.05 * smooth_noise(n, 0.3, rng))
    ph0 = np.cumsum(base) / SR
    w = np.maximum(base * (1.0 + 0.55 * np.sin(TWO_PI * ph0 + rng.uniform(0, TWO_PI))), 0.02 * rate)
    phase = np.cumsum(w) / SR
    out = np.zeros(n)
    clicks = [_pawl(rng) for _ in range(4)]
    idx = np.nonzero(np.diff(np.floor(phase * teeth)) > 0)[0] + 1
    for k in idx:
        _place(out, clicks[int(rng.integers(0, 4))], k / SR, 0.65 + 0.35 * rng.uniform())
    rel = np.clip(w / rate, 0, 2.5)
    gr = dsp.friction(n, 18.0 + 60.0 * rel * load, rng, jitter=0.3,
                      body=[(150.0, 7.0, 1.0), (340.0, 8.0, 0.8), (620.0, 10.0, 0.5), (1180.0, 12.0, 0.25)])
    gate = onepole_lp((smooth_noise(n, 1.1, rng) > 0.1).astype(float), 6.0)
    rc = dsp.friction(n, 260.0 + 300.0 * rel, rng, jitter=0.25, body=[(950.0, 9.0, 1.0), (1750.0, 11.0, 0.6), (2900.0, 13.0, 0.3)])
    pk = max(1e-9, np.sqrt(np.mean(out ** 2)))
    out += pk * 1.2 * load * gr / max(1e-9, np.sqrt(np.mean(gr ** 2))) * (0.4 + 0.3 * rel)
    out += pk * 0.5 * load * rc / max(1e-9, np.sqrt(np.mean(rc ** 2))) * gate
    for k in np.nonzero(np.diff(np.floor(phase + 0.3)) > 0)[0] + 1:
        m = _N(0.18)
        sq = dsp.friction(m, 520.0 + 180.0 * rng.uniform(), rng, jitter=0.1, body=[(2300.0, 16.0, 1.0)]) * np.hanning(m)
        _place(out, sq, k / SR, pk * 0.8 / max(1e-9, np.max(np.abs(sq))) * rng.uniform(0.3, 1.0))
    return out


@_sfx("winch_crank", kind="sustained", norm="int", default_dur=5.0, space=1.0, muffle=False)
def _winch_crank(dur, p, rng):
    """The winch cranked steadily. params: rate rev/s (0.42), load 0..1 (0.5), teeth (12)."""
    n = _N(dur)
    x = winch_track(n, rng, float(p.get("rate", 0.42)), float(p.get("load", 0.5)), int(p.get("teeth", 12)))
    return fade(_wide(x, rng, 0.25), 0.02, 0.05)


@_sfx("winch_strain", space=1.0, hit=True, trim=-1.0, muffle=False, anchor=0.0)
def _winch_strain(dur, p, rng):
    """The line snapping taut (s12 tight): the hemp's twanging jerk, the pawl slamming on its tooth,
    the drum and frame groaning under the sudden load."""
    n = _N(2.2)
    out = np.zeros(n)
    ks = dsp.karplus_strong(68.0 * rng.uniform(0.95, 1.05), 1.6, t60=0.9, brightness=0.35, rng=rng)
    _place(out, ks * exp_env(len(ks), 1.2), 0.0, 0.5)
    _place(out, _burst(_N(0.05), rng, 250, 3500, t60=0.025, attack=0.0004), 0.0, 0.9)
    _place(out, _pawl(rng), 0.012, 1.2)
    _place(out, _thump(_N(0.3), 120.0, 70.0, 0.02, 0.15), 0.0, 0.6)
    m = _N(1.7)
    tt = t_axis(m)
    groan = dsp.friction(m, 22.0 + 30.0 * np.exp(-tt / 0.5), rng, jitter=0.35,
                         body=[(140.0, 8.0, 1.0), (310.0, 9.0, 0.8), (590.0, 10.0, 0.5), (1100.0, 12.0, 0.3)])
    groan *= np.clip(tt / 0.05, 0, 1) * np.exp(-tt / 0.6)
    _place(out, groan, 0.03, 1.4 * np.max(np.abs(out)) / max(1e-9, np.max(np.abs(groan))))
    fib = dsp.friction(_N(0.4), 650.0, rng, jitter=0.3, body=[(1300.0, 8.0, 1.0), (2400.0, 10.0, 0.5)]) * np.hanning(_N(0.4))
    _place(out, fib, 0.02, 0.4 * np.max(np.abs(out)) / max(1e-9, np.max(np.abs(fib))))
    return out


# copper helmet shell modes (Hz, T60 s)
_COPPER = np.array([182.0, 297.0, 433.0, 612.0, 845.0, 1130.0, 1490.0, 1960.0, 2580.0, 3350.0])
_COPPER_T60 = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.42, 0.35, 0.28, 0.22, 0.16])


@_sfx("helmet_clank", space=1.0, hit=True, trim=1.0, muffle=False, anchor=0.30)
def _helmet_clank(dur, p, rng):
    """The Mark V bonnet seated on the breastplate and given its eighth-turn: a copper-on-brass
    seat, the interrupted thread grinding round, then the CLANK of the stop lug and safety catch
    (the cue time, 0.30 s in), the copper sphere ringing on."""
    n = _N(2.0)
    out = np.zeros(n)
    seat = _modes(rng, _COPPER * rng.uniform(0.97, 1.03), _COPPER_T60 * 0.6, spread=0.01, n=_N(1.0))
    seat += _thump(_N(1.0), 88.0, 55.0, 0.02, 0.18) * 0.8 + _burst(_N(1.0), rng, 60, 1500, t60=0.03, attack=0.0006) * 0.6
    _place(out, seat, 0.0, 0.45)
    m = _N(0.22)
    tt = t_axis(m)
    grind = dsp.friction(m, 140.0 + 260.0 * np.sin(np.pi * tt / 0.22), rng, jitter=0.35,
                         body=[(1450.0, 6.0, 1.0), (2600.0, 8.0, 0.7), (3900.0, 10.0, 0.4)])
    grind *= np.sin(np.pi * tt / 0.22) ** 1.2
    _place(out, grind, 0.06, 0.35 * np.max(np.abs(seat)) / max(1e-9, np.max(np.abs(grind))))
    lock = _modes(rng, _COPPER * 1.04, _COPPER_T60, spread=0.015, beat=0.7, n=_N(1.6))
    lock += _thump(_N(1.6), 110.0, 62.0, 0.012, 0.22) * 0.9
    lock += _burst(_N(1.6), rng, lo=2000, t60=0.006, attack=0.00015) * 0.8
    lock += _modes(rng, [2900.0, 4400.0, 6100.0], [0.05, 0.04, 0.03], [0.6, 0.4, 0.25], n=_N(1.6), attack=0.0002)
    _place(out, lock, 0.30, 1.0)
    return fade(out, 0.0, 0.3)


@_sfx("helmet_unlock", space=1.0, muffle=False, anchor=0.05)
def _helmet_unlock(dur, p, rng):
    """s15: the safety catch thumbed off (cue time), the bonnet turned back on its thread, the seal
    breaking with a short sigh of air, the helmet lifted off the collar, water dribbling out."""
    n = _N(2.4)
    out = np.zeros(n)
    _place(out, _modes(rng, [2600.0, 3900.0, 5600.0], [0.05, 0.04, 0.03], [1.0, 0.6, 0.3], attack=0.0002), 0.05, 0.7)
    m = _N(0.25)
    tt = t_axis(m)
    grind = dsp.friction(m, 120.0 + 220.0 * np.sin(np.pi * tt / 0.25), rng, jitter=0.35,
                         body=[(1400.0, 6.0, 1.0), (2500.0, 8.0, 0.7), (3800.0, 10.0, 0.4)]) * np.sin(np.pi * tt / 0.25) ** 1.2
    _place(out, grind, 0.1, 0.6 / max(1e-9, np.max(np.abs(grind))))
    _place(out, _modes(rng, _COPPER * 1.02, _COPPER_T60 * 0.5, spread=0.01, n=_N(0.8)), 0.36, 0.45)
    m = _N(0.45)
    tt = t_axis(m)
    sigh = bandpass(white(m, rng), 900.0, 7000.0, 2) * np.clip(tt / 0.01, 0, 1) * np.exp(-tt / 0.12)
    _place(out, sigh, 0.37, 0.5 / max(1e-9, np.max(np.abs(sigh))))
    m = _N(0.4)
    tt = t_axis(m)
    scrape = dsp.friction(m, 300.0, rng, jitter=0.3, body=[(1800.0, 7.0, 1.0), (3100.0, 9.0, 0.5)]) * np.sin(np.pi * tt / 0.4)
    _place(out, scrape, 0.6, 0.25 / max(1e-9, np.max(np.abs(scrape))))
    trick = np.zeros(_N(1.5))
    for tt0 in np.sort(rng.uniform(0.0, 1.3, 26)):
        _place(trick, _droplet(rng, rng.uniform(900.0, 3000.0), rng.uniform(0.004, 0.012)), tt0, rng.uniform(0.2, 1.0))
    trick += bandpass(white(len(trick), rng), 500.0, 3000.0, 2) * 0.05 * np.exp(-t_axis(len(trick)) / 0.5)
    _place(out, trick, 0.7, 0.18 / max(1e-9, np.max(np.abs(trick))))
    return out


@_sfx("lamp_click", space=0.4, hit=True, trim=-2.0, muffle=False)
def _lamp_click(dur, p, rng):
    """The helmet lamp switched on underwater, heard through the shell: a chunky two-stage brass
    toggle (ka-CHK), the filament's tiny 'tink' as it heats, a faint electrical hum swelling in."""
    n = _N(1.2)
    out = np.zeros(n)
    k1 = _modes(rng, [1850.0, 2920.0, 4380.0, 6100.0], [0.03, 0.025, 0.018, 0.012], [1.0, 0.7, 0.45, 0.3], n=_N(0.1), attack=0.0002)
    k1 += _burst(_N(0.1), rng, lo=1800, t60=0.004, attack=0.0001) * 0.5
    _place(out, k1, 0.0, 0.5)
    k2 = _modes(rng, [1480.0, 2380.0, 3720.0, 5600.0], [0.06, 0.045, 0.03, 0.02], [1.0, 0.8, 0.5, 0.3], n=_N(0.15), attack=0.0002)
    k2 += _thump(_N(0.15), 240.0, 170.0, 0.006, 0.04, attack=0.0003) * 0.7
    _place(out, k2, 0.014, 1.0)
    _place(out, _modes(rng, [6400.0, 8900.0], [0.25, 0.18], [1.0, 0.5], attack=0.0005), 0.11, 0.05)
    m = _N(1.0)
    tt = t_axis(m)
    hum = (np.sin(TWO_PI * 100.0 * tt) * 0.6 + 0.3 * np.sin(TWO_PI * 200.0 * tt) + 0.15 * np.sin(TWO_PI * 300.0 * tt))
    hum *= np.clip((tt - 0.05) / 0.15, 0, 1) * np.exp(-tt / 0.5)
    _place(out, _tf(hum, 0.5), 0.02, 0.025)
    return sos(out, "lowpass", 7500.0, 2)


@_sfx("cigar_draw", space=0.8, muffle=False)
def _cigar_draw(dur, p, rng):
    """The client draws on his cigar (the ember flares): a soft breath drawn through the leaf, the
    ember crackling up, a slow exhale of smoke."""
    n = _N(1.8)
    t = t_axis(n)
    out = np.zeros(n)
    m = _N(0.75)
    dr = bandpass(pink(m, rng), 300.0, 3200.0, 2) * _env_sin(m, 0.35, 0.2, 0.2)
    _place(out, dr, 0.0, 0.5)
    cr = sos(crackle(n, 85.0, rng, amp_spread=1.0), "highpass", 2600.0, 2)
    cr *= np.clip(t / 0.4, 0, 1) ** 1.5 * np.exp(-np.maximum(t - 0.55, 0) / 0.35)
    _place(out, cr, 0.0, 2.2 * np.max(np.abs(dr)) / max(1e-9, np.max(np.abs(cr))))
    m = _N(0.9)
    ex = bandpass(pink(m, rng), 200.0, 2500.0, 2) * _env_sin(m, 0.15, 0.2, 0.55)
    _place(out, ex, 0.95, 0.35)
    return out


@_sfx("envelope_pass", space=0.8, muffle=False)
def _envelope_pass(dur, p, rng):
    """A fat envelope of cash held out and taken: stiff paper flexing, a slide between fingers,
    the soft tap of the glove closing on it."""
    n = _N(0.9)
    t = t_axis(n)
    motion = np.clip(0.5 + 0.6 * smooth_noise(n, 6.0, rng), 0, None) * np.sin(np.pi * np.clip(t / 0.75, 0, 1)) ** 0.8
    cr = bandpass(crackle(n, 900.0, rng, amp_spread=1.1), 700.0, 5500.0, 2) * 2.0 + 0.1 * bandpass(white(n, rng), 1200.0, 6000.0, 2)
    out = cr * motion
    sl = tv_bandpass(white(_N(0.3), rng), lambda x: 1500.0 + 2500.0 * x / 0.3, q=0.9, block=64) * np.hanning(_N(0.3))
    _place(out, sl, 0.35, 0.6)
    _place(out, _burst(_N(0.05), rng, 150, 1200, t60=0.025, attack=0.001), 0.66, 0.8)
    return _wide(out, rng, 0.3)


@_sfx("knife_glint", space=0.6, muffle=False)
def _knife_glint(dur, p, rng):
    """A glint on the knife's edge: a soft, high shimmering 'ting' that blooms and hangs."""
    n = _N(1.8)
    x = _modes(rng, [4800.0, 7200.0, 9100.0, 11600.0], [1.3, 1.0, 0.8, 0.6], [1.0, 0.6, 0.4, 0.25], n=n, beat=3.0, attack=0.04)
    sh = bandpass(white(n, rng), 6000.0, 12000.0, 2) * _env_sin(n, 0.06, 0.0, 0.5) * 0.04
    return _wide(x * 0.5 + sh, rng, 0.5)


def _wood_step(rng, weight=1.0, wet=1, rung=True):
    n = _N(1.4)
    out = np.zeros(n)
    _place(out, _thump(_N(0.4), 95.0 + 20 * rng.uniform(), 58.0, 0.02, 0.16 + 0.08 * weight), 0.0, 1.0)
    _place(out, _burst(_N(0.3), rng, hi=300, t60=0.12, attack=0.003, color="brown"), 0.0, 0.35 * weight)
    modes = np.array([210.0, 470.0, 830.0, 1350.0]) * (1.25 if rung else 1.0) * rng.uniform(0.94, 1.06)
    _place(out, _modes(rng, modes, [0.12, 0.09, 0.07, 0.05], [1.0, 0.7, 0.45, 0.3], n=_N(0.3)), 0.0, 0.45)
    _place(out, _burst(_N(0.06), rng, 80, 1600, t60=0.03, attack=0.0008), 0.0, 0.6)
    m = _N(0.4)
    tt = t_axis(m)
    cr = dsp.friction(m, 40.0 + 60.0 * np.sin(np.pi * tt / 0.4), rng, jitter=0.3,
                      body=[(240.0, 7.0, 1.0), (560.0, 9.0, 0.6), (1150.0, 11.0, 0.3)]) * np.sin(np.pi * tt / 0.4)
    _place(out, cr, 0.05, 0.3 * np.max(np.abs(out)) / max(1e-9, np.max(np.abs(cr))))
    if wet:
        dr = np.zeros(_N(1.2))
        for tt0 in np.sort(rng.uniform(0.0, 1.0, 30)):
            _place(dr, _droplet(rng, rng.uniform(1200.0, 4200.0), rng.uniform(0.003, 0.008)), tt0, rng.uniform(0.2, 1.0))
        dr += bandpass(white(len(dr), rng), 800.0, 5000.0, 2) * 0.04 * np.exp(-t_axis(len(dr)) / 0.4)
        _place(out, _tf(dr, 0.4), 0.02, 0.1 * np.max(np.abs(out)) / max(1e-9, np.max(np.abs(dr))))
    return out


@_sfx("ladder_step", space=1.0, muffle=False)
def _ladder_step(dur, p, rng):
    """A lead-soled diving boot on a wooden ladder rung: thud, rung knock, creak; wet 0/1 (1):
    the suit streaming water onto the deck."""
    return _wood_step(rng, float(p.get("weight", 1.0)), int(p.get("wet", 1)), True)


@_sfx("deck_step", space=1.0, muffle=False)
def _deck_step(dur, p, rng):
    """A heavy step on the wooden deck (diving boots, or the client's shoes with weight 0.3)."""
    w = float(p.get("weight", 1.0))
    x = _wood_step(rng, w, int(p.get("wet", 0)), False)
    return x, -8.0 * (1.0 - w)


@_sfx("deck_creak", space=1.0, muffle=False)
def _deck_creak(dur, p, rng):
    """The boat's timbers working on the swell: a slow, low wooden creak."""
    n = _N(1.6)
    t = t_axis(n)
    sw = np.sin(np.pi * t / (n / SR)) ** 0.9
    rate = 22.0 + 40.0 * sw * rng.uniform(0.7, 1.3) + 15.0 * np.abs(smooth_noise(n, 2.0, rng))
    x = dsp.friction(n, rate, rng, jitter=0.35, body=[(170.0, 7.0, 1.0), (390.0, 9.0, 0.8), (780.0, 10.0, 0.5), (1500.0, 12.0, 0.2)])
    return x * sw


@_sfx("rope_creak", space=1.0, muffle=False)
def _rope_creak(dur, p, rng):
    """Hemp rope working against a cleat or the davit block: a fibrous squeak."""
    n = _N(1.0)
    t = t_axis(n)
    sw = np.sin(np.pi * t / (n / SR)) ** 1.2
    x = dsp.friction(n, 240.0 + 280.0 * sw, rng, jitter=0.2, body=[(820.0, 9.0, 1.0), (1500.0, 11.0, 0.6), (2600.0, 12.0, 0.3)])
    return x * sw


@_sfx("gull_call", space=0.0, muffle=False)
def _gull_call(dur, p, rng):
    """A herring gull far off at dusk: two to four raspy 'kyow' cries, falling in pitch, with
    distance (air absorption) and the open sea's reverb. calls (3)."""
    k = int(p.get("calls", rng.integers(2, 5)))
    n = _N(2.8)
    out = np.zeros(n)
    t0 = 0.0
    base = rng.uniform(0.92, 1.1)
    for i in range(k):
        L = rng.uniform(0.28, 0.42)
        m = _N(L + 0.05)
        tt = t_axis(m)
        u = np.clip(tt / L, 0, 1)
        fs, fp, fe = np.array([1080.0, 1480.0, 860.0]) * base * (1.0 - 0.04 * i)
        f = np.where(u < 0.25, fs + (fp - fs) * u / 0.25, fp + (fe - fp) * np.clip((u - 0.25) / 0.75, 0, 1) ** 0.8)
        f = f * (1.0 + 0.012 * smooth_noise(m, 25.0, rng))
        src = dsp.pulse_train(f, m, jitter=0.02, rng=rng, harmonics=7)
        rasp = bandpass(white(m, rng), 1500.0, 6000.0, 2) * np.abs(src) * 0.45
        x = resonator_bank(src + rasp, [2200.0, 3300.0, 4500.0], [3.0, 4.0, 5.0], [1.0, 0.6, 0.3]) + 0.3 * (src + rasp)
        x *= np.clip(tt / 0.02, 0, 1) * np.clip((L - tt) / 0.06, 0, 1) * (0.7 + 0.3 * np.sin(np.pi * u))
        _place(out, x, t0, 1.0 - 0.12 * i)
        t0 += L + rng.uniform(0.18, 0.4)
    out = sos(out, "lowpass", 4200.0, 2)
    st = dsp.pan_stereo(to_stereo(out) * 0.6, rng.uniform(-0.6, 0.6)) + wet(out, "dusk_air", -2.0)[:n]
    return fade(st, 0.0, 0.3)


# ============================================================================ wreck
@_sfx("silt_puff", space=1.0)
def _silt_puff(dur, p, rng):
    """Landing in soft silt: a slow soft thud with no hard edge, the mud's 'fwumph', the silt cloud's
    grainy swirl. size 0..1 (0.6); metal 0..1 (a lead weight's dead clunk)."""
    s = float(np.clip(p.get("size", 0.6), 0, 1))
    n = _N(1.9)
    out = np.zeros(n)
    _place(out, _thump(_N(1.0), 70.0 + 25.0 * s, 38.0 + 6.0 * s, 0.05, 0.3 + 0.4 * s, attack=0.008), 0.0, 1.0)
    body = sos(brown(n, rng), "lowpass", 260.0, 2) * ar_env(n, 0.015, 0.35 + 0.4 * s)
    _place(out, body, 0.0, 0.7 / max(1e-9, np.max(np.abs(body))))
    m = _N(1.4)
    tt = t_axis(m)
    cloud = bandpass(pink(m, rng), 220.0, 1300.0, 2) * np.clip(tt / 0.12, 0, 1) * np.exp(-tt / 0.45) * (1 + 0.5 * smooth_noise(m, 7.0, rng))
    _place(out, _tf(cloud, 0.4), 0.03, (0.16 + 0.1 * s) / max(1e-9, np.max(np.abs(cloud))))
    grit = sos(crackle(m, 120.0, rng), "lowpass", 1500.0, 2) * np.exp(-tt / 0.3)
    _place(out, _tf(grit, 0.4), 0.01, 0.05 / max(1e-9, np.max(np.abs(grit))))
    mt = float(p.get("metal", 0.0))
    if mt > 0:
        _place(out, _modes(rng, np.array([290.0, 640.0, 1080.0]) * rng.uniform(0.95, 1.05), [0.08, 0.06, 0.04], [1.0, 0.6, 0.3]),
               0.0, 0.35 * mt)
    return out, -8.0 * (0.6 - s)


@_sfx("silt_step", space=1.0)
def _silt_step(dur, p, rng):
    """A lead boot planted in silt: a dull heavy thud and the soft suck of the mud releasing."""
    n = _N(1.0)
    out = np.zeros(n)
    _place(out, _thump(_N(0.6), 82.0, 46.0, 0.04, 0.3, attack=0.006), 0.0, 1.0)
    _place(out, _burst(_N(0.3), rng, hi=320, t60=0.12, attack=0.01, color="brown"), 0.0, 0.5)
    m = _N(0.3)
    suck = bandpass(pink(m, rng), 200.0, 900.0, 2) * _env_sin(m, 0.08, 0.05, 0.15)
    _place(out, suck, 0.35, 0.15 / max(1e-9, np.max(np.abs(suck))))
    return out


_PLATES = ((46.0, 16.0, 1.0), (69.0, 18.0, 0.9), (94.0, 20.0, 0.8), (127.0, 22.0, 0.65), (171.0, 24.0, 0.5),
           (229.0, 26.0, 0.38), (306.0, 28.0, 0.27), (410.0, 30.0, 0.18))


@_sfx("hull_groan", space=1.0)
def _hull_groan(dur, p, rng):
    """The wreck's steel settling under thirty years of water: a slow stick-slip moan through the
    hull plates' low modes, a sub groan bending down, a thin metallic creak riding on top.
    params: size 0..1 (0.7), length s (3.8)."""
    L = float(p.get("length", 3.8))
    s = float(np.clip(p.get("size", 0.7), 0, 1))
    n = _N(L + 0.6)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    shape = np.sin(np.pi * u) ** 0.8
    rate = (7.0 + 16.0 * shape) * (1.0 + 0.25 * smooth_noise(n, 0.8, rng))
    sc = 1.0 - 0.15 * s
    moan = dsp.friction(n, rate, rng, jitter=0.4, body=[(f * sc * rng.uniform(0.97, 1.03), q, g) for f, q, g in _PLATES]) * shape
    sub = np.sin(TWO_PI * np.cumsum(36.0 * (1.0 - 0.12 * u)) / SR) * shape ** 1.5
    ov = dsp.friction(n, 120.0 + 150.0 * shape, rng, jitter=0.2,
                      body=[(640.0, 30.0, 1.0), (1060.0, 35.0, 0.7), (1570.0, 40.0, 0.5), (2210.0, 40.0, 0.3)]) * shape ** 2
    gate = onepole_lp((smooth_noise(n, 1.5, rng) > 0.15).astype(float), 5.0)
    m_r = max(1e-9, np.sqrt(np.mean(moan ** 2)))
    out = moan / m_r + 0.55 * s * sub / max(1e-9, np.sqrt(np.mean(sub ** 2))) + 0.22 * ov / max(1e-9, np.sqrt(np.mean(ov ** 2))) * gate
    return fade(out, 0.05, 0.3), -6.0 * (0.7 - s)


@_sfx("metal_creak", space=1.0)
def _metal_creak(dur, p, rng):
    """A shorter steel creak (a hatch, a cable, a bulkhead shifting). pitch (1.0)."""
    pt = float(p.get("pitch", 1.0)) * rng.uniform(0.9, 1.1)
    L = rng.uniform(0.9, 1.5)
    n = _N(L + 0.2)
    t = t_axis(n)
    sw = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 1.1
    rate = (40.0 + 100.0 * sw) * pt * (1.0 + 0.2 * smooth_noise(n, 2.0, rng))
    x = dsp.friction(n, rate, rng, jitter=0.25, body=[(380.0 * pt, 18.0, 1.0), (720.0 * pt, 22.0, 0.8), (1180.0 * pt, 25.0, 0.6),
                                                     (1890.0 * pt, 28.0, 0.4), (2700.0 * pt, 30.0, 0.25)])
    return x * sw


@_sfx("hull_ping", space=1.0)
def _hull_ping(dur, p, rng):
    """A plate somewhere in the hull giving way: a far, soft-edged 'tonk' that rings low and long."""
    n = _N(3.0)
    x = _modes(rng, np.array([97.0, 151.0, 213.0, 296.0, 402.0, 531.0, 694.0]) * rng.uniform(0.9, 1.1),
               [2.2, 1.8, 1.5, 1.2, 1.0, 0.8, 0.6], [1.0, 0.8, 0.7, 0.55, 0.4, 0.3, 0.2], n=n, attack=0.006, beat=0.4)
    x += _thump(n, 70.0, 48.0, 0.03, 0.5, attack=0.006) * 0.6
    return sos(x, "lowpass", 1400.0, 2)


@_sfx("hook_clank", space=1.0)
def _hook_clank(dur, p, rng):
    """The winch hook's iron knocking the hull as it comes down: two knocks, the shackle rattling."""
    n = _N(1.4)
    out = np.zeros(n)
    fr = np.array([310.0, 720.0, 1260.0, 1980.0, 2850.0]) * rng.uniform(0.95, 1.05)
    t60 = [0.45, 0.35, 0.26, 0.18, 0.12]
    _place(out, _modes(rng, fr, t60, n=_N(0.6), attack=0.0003) + _burst(_N(0.6), rng, lo=1500, t60=0.004, attack=0.0001) * 0.4, 0.0, 1.0)
    _place(out, _modes(rng, fr * 1.01, t60, n=_N(0.6), attack=0.0003), 0.21 + rng.uniform(0, 0.05), 0.45)
    for _ in range(4):
        f = rng.uniform(1800.0, 3600.0)
        _place(out, _modes(rng, [f, f * 1.43], [0.06, 0.04], n=_N(0.1), attack=0.0002), 0.05 + rng.uniform(0, 0.4), rng.uniform(0.08, 0.2))
    return out


@_sfx("chair_turn", space=1.0)
def _chair_turn(dur, p, rng):
    """A fallen wooden chair turning slowly in the diver's wake: a long soft creak, a dull bump."""
    n = _N(2.0)
    t = t_axis(n)
    sw = np.sin(np.pi * np.clip(t / 1.6, 0, 1)) ** 1.0
    x = dsp.friction(n, 15.0 + 30.0 * sw, rng, jitter=0.4, body=[(210.0, 6.0, 1.0), (480.0, 8.0, 0.7), (1050.0, 10.0, 0.35)]) * sw
    x /= max(1e-9, np.max(np.abs(x)))
    _place(x, _modes(rng, [230.0, 520.0, 980.0], [0.1, 0.07, 0.05], n=_N(0.2)) + _thump(_N(0.2), 120.0, 80.0, 0.01, 0.08) * 0.5,
           1.25, 0.5)
    return x


@_sfx("glove_metal", space=1.0)
def _glove_metal(dur, p, rng):
    """A gloved fingertip touching a torn steel petal: a dull canvas scrape and a small metal tick."""
    n = _N(0.8)
    out = np.zeros(n)
    m = _N(0.4)
    tt = t_axis(m)
    sc = dsp.friction(m, 250.0 + 250.0 * tt / 0.4, rng, jitter=0.3, body=[(1300.0, 6.0, 1.0), (2400.0, 8.0, 0.5)]) * np.sin(np.pi * tt / 0.4)
    _place(out, sc / max(1e-9, np.max(np.abs(sc))), 0.0, 0.5)
    _place(out, _modes(rng, [2100.0, 3300.0, 4700.0], [0.2, 0.15, 0.1], attack=0.0003), 0.03, 0.8)
    return out


@_sfx("rope_tug", space=1.0, hit=True, trim=-1.0)
def _rope_tug(dur, p, rng):
    """One sharp tug on the lifting line: the jerk (fibre snap), the line kicking - a low twang
    running up the rope - and a dull thump through the glove."""
    n = _N(1.4)
    out = np.zeros(n)
    _place(out, _burst(_N(0.05), rng, 300, 3000, t60=0.02, attack=0.0004), 0.0, 0.7)
    f0 = 52.0 * rng.uniform(0.95, 1.05)
    ks = dsp.karplus_strong(f0, 1.2, t60=0.6, brightness=0.3, rng=rng)
    ks += 0.5 * dsp.karplus_strong(f0 * 2.01, 1.2, t60=0.4, brightness=0.35, rng=rng)
    _place(out, ks * exp_env(len(ks), 0.9), 0.004, 0.8 / max(1e-9, np.max(np.abs(ks))))
    _place(out, _thump(_N(0.3), 120.0, 65.0, 0.02, 0.15), 0.0, 0.7)
    m = _N(0.14)
    fib = dsp.friction(m, 400.0, rng, jitter=0.3, body=[(1100.0, 6.0, 1.0), (2100.0, 8.0, 0.5)]) * np.hanning(m)
    _place(out, fib, 0.01, 0.3 / max(1e-9, np.max(np.abs(fib))))
    return out


@_sfx("rope_tie", space=1.0)
def _rope_tie(dur, p, rng):
    """The lifting line wrapped round something heavy and hitched: three fibrous rubs and the knot
    pulled tight."""
    n = _N(2.2)
    out = np.zeros(n)
    for k, t0 in enumerate((0.0, 0.5, 0.95)):
        L = rng.uniform(0.3, 0.42)
        m = _N(L)
        tt = t_axis(m)
        rub = dsp.friction(m, 300.0 + 400.0 * tt / L, rng, jitter=0.35, body=[(700.0, 5.0, 1.0), (1500.0, 7.0, 0.6), (2700.0, 9.0, 0.3)])
        rub = rub * np.sin(np.pi * tt / L) ** 1.3 + 0.3 * bandpass(white(m, rng), 600.0, 3000.0, 2) * np.sin(np.pi * tt / L) ** 2
        _place(out, rub / max(1e-9, np.max(np.abs(rub))), t0, 0.6)
    m = _N(0.5)
    tt = t_axis(m)
    tight = dsp.friction(m, 120.0 + 500.0 * (tt / 0.5) ** 1.5, rng, jitter=0.2, body=[(900.0, 8.0, 1.0), (1800.0, 10.0, 0.5)])
    tight *= np.clip(tt / 0.1, 0, 1) * np.clip((0.5 - tt) / 0.06, 0, 1)
    _place(out, tight / max(1e-9, np.max(np.abs(tight))), 1.45, 0.8)
    return out


# ============================================================================ the cut and the dial
@_sfx("knife_draw", space=1.0, hit=True, trim=0.0, muffle=False, anchor=0.17)
def _knife_draw(dur, p, rng):
    """The client's knife drawn: leather scraping the steel out of its sheath, then the blade
    clearing it with a bright inharmonic ring (the cue time, 0.17 s in), the arm's swish."""
    n = _N(1.8)
    out = np.zeros(n)
    m = _N(0.19)
    tt = t_axis(m)
    lea = dsp.friction(m, 900.0 + 1600.0 * tt / 0.19, rng, jitter=0.3, body=[(2400.0, 4.0, 1.0), (4100.0, 5.0, 0.6)])
    lea = lea / max(1e-9, np.max(np.abs(lea))) + 0.35 * bandpass(white(m, rng), 2000.0, 7000.0, 2) / 3.0
    lea *= np.clip(tt / 0.15, 0, 1) ** 1.5
    _place(out, lea, 0.0, 0.45)
    ring = _modes(rng, [2950.0, 4380.0, 6120.0, 7790.0, 9640.0, 11300.0], [1.1, 0.9, 0.7, 0.55, 0.4, 0.3],
                  [0.8, 1.0, 0.7, 0.5, 0.35, 0.2], n=_N(1.5), beat=2.2, attack=0.0008)
    _place(out, ring, 0.17, 0.5)
    _place(out, _burst(_N(0.02), rng, lo=3000, t60=0.006, attack=0.0002), 0.168, 0.35)
    m = _N(0.3)
    sw = tv_bandpass(pink(m, rng), lambda x: 500.0 + 2500.0 * x / 0.3, q=1.0, block=64) * np.sin(np.pi * t_axis(m) / 0.3) ** 2
    _place(out, sw, 0.1, 0.12 / max(1e-9, np.max(np.abs(sw))))
    return out


@_sfx("hose_cut", space=1.0, hit=True, trim=2.0, muffle=False, anchor=0.07)
def _hose_cut(dur, p, rng):
    """THE CUT (s12): the knife's swing, the chop through the rubber-and-canvas hose against the rail
    (the cue time, 0.07 s in), the fibres tearing, the pump's air BURSTING from the open end, the
    severed end whipping back across the deck. The continuing hiss is 'air_escape'."""
    n = _N(1.6)
    out = np.zeros(n)
    m = _N(0.08)
    sw = tv_bandpass(white(m, rng), lambda x: 900.0 + 5000.0 * x / 0.08, q=1.2, block=32) * np.linspace(0, 1, m) ** 2
    _place(out, sw, 0.0, 0.25 / max(1e-9, np.max(np.abs(sw))))
    tc = 0.07
    chop = _modes(rng, np.array([260.0, 590.0, 1050.0, 1720.0]) * rng.uniform(0.96, 1.04), [0.12, 0.09, 0.06, 0.04], n=_N(0.3), attack=0.0002)
    chop = chop / max(1e-9, np.max(np.abs(chop))) + _burst(_N(0.3), rng, 120, 900, t60=0.04, attack=0.0004)
    chop += _burst(_N(0.3), rng, lo=1500, t60=0.005, attack=0.0001) * 0.8
    _place(out, chop, tc, 1.0)
    m = _N(0.09)
    tear = bandpass(crackle(m, 6000.0, rng, amp_spread=0.8), 1000.0, 6000.0, 2) * 4.0 + bandpass(white(m, rng), 400.0, 1800.0, 2) * 0.4
    tear *= np.clip(t_axis(m) / 0.005, 0, 1) * np.exp(-t_axis(m) / 0.05)
    _place(out, tear, tc + 0.004, 0.5 / max(1e-9, np.max(np.abs(tear))))
    m = _N(1.4)
    tt = t_axis(m)
    jet = bandpass(white(m, rng), 900.0, 12000.0, 2)
    jet = dsp.biquad(jet, "peak", 4000.0, 0.8, 6.0)
    flut = 1.0 + 0.35 * smooth_noise(m, 18.0, rng)
    whistle = tv_bandpass(white(m, rng), 2600.0 * (1.0 + 0.04 * smooth_noise(m, 6.0, rng)), q=25.0, block=64) * 3.0
    blast = (jet + 0.4 * whistle) * flut * np.clip(tt / 0.006, 0, 1) * (0.35 + 0.65 * np.exp(-tt / 0.35)) * np.clip((1.4 - tt) / 0.3, 0, 1)
    _place(out, blast, tc + 0.012, 0.9 / max(1e-9, np.max(np.abs(blast))))
    pop = _burst(_N(0.08), rng, 180, 2500, t60=0.035, attack=0.0008, color="pink")
    _place(out, pop, tc + 0.01, 0.7 / max(1e-9, np.max(np.abs(pop))))
    for k, t0 in enumerate((0.17, 0.39, 0.66)):
        slap = _burst(_N(0.15), rng, 150, 2500, t60=0.025, attack=0.0005) + _thump(_N(0.15), 130.0, 80.0, 0.01, 0.06) * 0.6
        _place(out, slap, tc + t0 + rng.uniform(-0.02, 0.02), 0.55 * (0.8 ** k))
    return out


@_sfx("air_escape", kind="sustained", norm="max", default_dur=3.5, space=0.8, hit=True, muffle=False)
def _air_escape(dur, p, rng):
    """The pump's air pouring out of the severed hose: a hard jet hiss pulsing with each stroke as
    the flywheel runs down, the open end fluttering. params: rpm (26), decay s (1.3)."""
    n = _N(dur)
    t = t_axis(n)
    rpm = float(p.get("rpm", 26.0))
    dec = float(p.get("decay", 1.6))
    w = (rpm * 2.0 / 60.0) * np.exp(-t / (dec * 1.6))
    ph = np.cumsum(w) / SR
    pulse = (0.5 - 0.5 * np.cos(TWO_PI * ph)) ** 2
    jet = dsp.biquad(bandpass(white(n, rng), 900.0, 11000.0, 2), "peak", 3800.0, 0.8, 5.0)
    env = (0.3 * np.exp(-t / (dec * 0.6)) + 0.7 * pulse * np.exp(-t / dec)) * (1.0 + 0.3 * smooth_noise(n, 16.0, rng))
    x = jet * env
    return fade(_wide(x, rng, 0.4), 0.004, min(0.5, dur * 0.2))


@_sfx("dial_turn", kind="sustained", norm="max", default_dur=0.45, space=0.6, muffle=False)
def _dial_turn(dur, p, rng):
    """The combination dial turned: detent ticks speeding up and slowing with the hand, the dial
    ring's faint grit. params: rate peak ticks/s (22)."""
    n = _N(dur)
    t = t_axis(n)
    u = np.clip(t / dur, 0, 1)
    rate = float(p.get("rate", 22.0)) * np.sin(np.pi * u) ** 0.7 + 2.0
    ph = np.cumsum(rate) / SR
    out = np.zeros(n)
    for k in np.nonzero(np.diff(np.floor(ph)) > 0)[0] + 1:
        tick = _modes(rng, np.array([3200.0, 4700.0, 6900.0]) * rng.uniform(0.97, 1.03), [0.012, 0.009, 0.006], [1.0, 0.6, 0.35],
                      n=_N(0.03), attack=0.0001)
        _place(out, tick, k / SR, 0.5 + 0.5 * rng.uniform())
    grit = bandpass(white(n, rng), 1000.0, 5000.0, 2) * np.sin(np.pi * u) * 0.05 * max(1e-9, np.max(np.abs(out)))
    return out + grit


@_sfx("tumbler_click", space=0.6, hit=True, trim=0.0, muffle=False)
def _tumbler_click(dur, p, rng):
    """A tumbler falling into place: a sharp click, then 12 ms later the wheel pack's gate dropping
    onto the fence - a heavy, low clunk inside the iron box - and a tiny rattle."""
    n = _N(0.9)
    out = np.zeros(n)
    c = _modes(rng, np.array([2600.0, 4100.0, 6300.0]) * rng.uniform(0.97, 1.03), [0.02, 0.015, 0.01], n=_N(0.06), attack=0.0001)
    c += _burst(_N(0.06), rng, 2000, 8000, t60=0.004, attack=0.0001) * 0.6
    _place(out, c, 0.0, 0.7)
    iron = np.array([190.0, 460.0, 810.0, 1270.0, 1850.0, 2600.0]) * rng.uniform(0.97, 1.03)
    clunk = _modes(rng, iron, [0.25, 0.2, 0.15, 0.12, 0.09, 0.07], n=_N(0.6), attack=0.0003)
    clunk += _thump(_N(0.6), 92.0, 60.0, 0.01, 0.12) * 0.8
    _place(out, clunk, 0.012, 1.0)
    for _ in range(2):
        f = rng.uniform(2500.0, 4200.0)
        _place(out, _modes(rng, [f, f * 1.5], [0.02, 0.015], n=_N(0.04), attack=0.0001), 0.04 + rng.uniform(0, 0.05), 0.1)
    return out


@_sfx("safe_open", space=1.0, muffle=True, anchor=0.48)
def _safe_open(dur, p, rng):
    """The safe opening: the heavy handle levered round, two bolts shooting back (ka-CHUNK, the cue
    time), the door unsealing with a gulp of water, the great hinge groaning as it swings."""
    n = _N(3.0)
    out = np.zeros(n)
    m = _N(0.45)
    tt = t_axis(m)
    lever = dsp.friction(m, 40.0 + 50.0 * tt / 0.45, rng, jitter=0.3, body=[(210.0, 8.0, 1.0), (480.0, 10.0, 0.7), (900.0, 12.0, 0.4)])
    lever *= np.sin(np.pi * tt / 0.45) ** 1.2
    _place(out, lever / max(1e-9, np.max(np.abs(lever))), 0.0, 0.35)
    iron = np.array([240.0, 560.0, 990.0, 1600.0])
    for t0, g in ((0.48, 1.0), (0.62, 0.8)):
        b = _modes(rng, iron * rng.uniform(0.95, 1.05), [0.2, 0.15, 0.1, 0.07], n=_N(0.4), attack=0.0003) + _thump(_N(0.4), 100.0, 62.0, 0.01, 0.12)
        _place(out, b, t0, g)
    m = _N(0.6)
    gulp = sos(brown(m, rng), "lowpass", 250.0, 2) * _env_sin(m, 0.03, 0.05, 0.25)
    _place(out, gulp, 0.8, 0.5 / max(1e-9, np.max(np.abs(gulp))))
    bub = np.zeros(m)
    _bubbles(bub, rng, np.sort(rng.uniform(0.0, 0.35, 8)), 140.0, 600.0)
    _place(out, bub, 0.84, 0.3 / max(1e-9, np.max(np.abs(bub))))
    m = _N(1.9)
    tt = t_axis(m)
    sw = np.sin(np.pi * np.clip(tt / 1.8, 0, 1)) ** 0.9
    hinge = dsp.friction(m, 18.0 + 40.0 * sw, rng, jitter=0.35,
                         body=[(110.0, 12.0, 1.0), (260.0, 15.0, 0.8), (480.0, 18.0, 0.6), (900.0, 20.0, 0.4), (1500.0, 22.0, 0.2)]) * sw
    _place(out, hinge / max(1e-9, np.max(np.abs(hinge))), 0.95, 0.6)
    return out


# ============================================================================ water surface
def _slap(rng, size=0.6):
    n = _N(1.0)
    out = np.zeros(n)
    _place(out, _burst(_N(0.1), rng, 90, 1400, t60=0.045, attack=0.003, color="pink"), 0.0, 1.0)
    _place(out, _thump(_N(0.2), 110.0, 70.0, 0.02, 0.09, attack=0.003), 0.0, 0.4 * size)
    m = _N(0.6)
    tt = t_axis(m)
    sl = tv_bandpass(pink(m, rng), lambda x: 450.0 + 900.0 * math.exp(-x / 0.12), q=0.8, block=64)
    sl *= np.clip(tt / 0.02, 0, 1) * np.exp(-tt / 0.16)
    _place(out, _tf(sl, 0.4) / max(1e-9, np.max(np.abs(sl))), 0.005, 0.7)
    _bubbles(out, rng, 0.02 + rng.exponential(0.06, int(4 + 10 * size)), 350.0, 1800.0, amp=(0.05, 0.25))
    for _ in range(int(5 + 10 * size)):
        _place(out, _droplet(rng, rng.uniform(1800.0, 5000.0), rng.uniform(0.003, 0.006)), 0.08 + rng.exponential(0.12),
               rng.uniform(0.03, 0.12))
    return out


@_sfx("water_slap", space=1.0, muffle=False)
def _water_slap(dur, p, rng):
    """A swell slapping the wooden hull: the soft impact, a slosh, a gurgle, droplets. size (0.6)."""
    s = float(p.get("size", 0.6))
    return _slap(rng, s), -6.0 * (0.6 - s)


def swell_track(n, rng, period=5.5, slap_rate=1.0, calm=0.0):
    """The sea against a small boat: a slow rolling wash, low surge, slaps at the swell peaks and
    smaller laps between. calm 0..1 thins it out (night)."""
    t = t_axis(n)
    rate = (1.0 / period) * (1.0 + 0.12 * smooth_noise(n, 0.05, rng))
    ph = np.cumsum(rate) / SR
    sw = 0.5 - 0.5 * np.cos(TWO_PI * ph)
    wash = bandpass(pink(n, rng), 120.0, 1800.0, 2) * (0.35 + 0.65 * sw ** 1.5) * (1.0 + 0.2 * smooth_noise(n, 1.5, rng))
    low = sos(brown(n, rng), "lowpass", 160.0, 2) * sw * 0.8
    out = wash / max(1e-9, np.std(wash)) * 0.5 + low / max(1e-9, np.std(low)) * 0.4
    slaps = np.zeros(n)
    peaks = np.nonzero(np.diff(np.floor(ph + 0.15)) > 0)[0] + 1
    for k in peaks:
        if rng.uniform() < 0.85 * slap_rate:
            _place(slaps, _slap(rng, rng.uniform(0.4, 0.9) * (1.0 - 0.4 * calm)), k / SR + rng.uniform(-0.2, 0.2), rng.uniform(0.6, 1.0))
    for tt in dsp.poisson_times(0.9 * slap_rate * (1.0 - 0.5 * calm), n / SR, rng):
        _place(slaps, _slap(rng, rng.uniform(0.15, 0.4)), tt, rng.uniform(0.15, 0.4))
    out += slaps / max(1e-9, np.max(np.abs(slaps))) * 1.8 if np.any(slaps) else 0.0
    return out


@_sfx("swell_lap", kind="sustained", norm="int", default_dur=8.0, space=0.6, muffle=False)
def _swell_lap(dur, p, rng):
    """The swell lapping at the hull (bed layer). params: period s (5.5), calm 0..1 (0)."""
    n = _N(dur)
    out = np.stack([swell_track(n, rng, float(p.get("period", 5.5)), 1.0, float(p.get("calm", 0.0))) for _ in range(2)], axis=1)
    return fade(out, 0.3, 0.3)


@_sfx("entry_splash", space=0.6, hit=True, trim=2.0, muffle=False, anchor=0.0)
def _entry_splash(dur, p, rng):
    """The diver letting go of the ladder (s03): 200 lb of suit, lead and copper hitting the water -
    the slap, the crown of spray falling back, the cavity collapsing (thoomp), and below the line the
    roar of the bubble cloud from the suit."""
    n = _N(2.6)
    t = t_axis(n)
    out = np.zeros(n)
    _place(out, _burst(_N(0.2), rng, 100, 6000, t60=0.06, attack=0.0005, color="pink"), 0.0, 1.0)
    _place(out, _thump(_N(0.5), 90.0, 45.0, 0.03, 0.25), 0.0, 0.8)
    m = _N(1.2)
    tt = t_axis(m)
    spray = bandpass(white(m, rng), 1000.0, 7000.0, 2) * np.clip(tt / 0.02, 0, 1) * np.exp(-tt / 0.3)
    for _ in range(70):
        _place(spray, _droplet(rng, rng.uniform(1300.0, 5500.0), rng.uniform(0.003, 0.009)), rng.exponential(0.25), rng.uniform(0.2, 1.0))
    _place(out, _tf(spray, 0.4), 0.01, 0.5 / max(1e-9, np.max(np.abs(spray))))
    m = _N(0.6)
    th = sos(brown(m, rng), "lowpass", 180.0, 2) * _env_sin(m, 0.02, 0.0, 0.35)
    _place(th, _bubble(rng, 62.0, 8.0, 0.25), 0.0, 0.5 * _pk(th))
    _place(out, th, 0.12, 0.7 / max(1e-9, np.max(np.abs(th))))
    cloud = np.zeros(n)
    _bubbles(cloud, rng, dsp.poisson_times(lambda x: 120.0 * math.exp(-x / 0.6), 2.0, rng) + 0.05, 70.0, 700.0, amp=(0.3, 1.0), q=(6.0, 14.0))
    cloud += bandpass(brown(n, rng), 50.0, 400.0, 2) * np.clip((t - 0.05) / 0.1, 0, 1) * np.exp(-t / 0.7) * 0.4 * max(1e-9, np.max(np.abs(cloud))) / 3.0
    cloud = _tf(sos(cloud, "lowpass", 1600.0, 2), 0.4)
    _place(out, cloud, 0.0, 0.6 / max(1e-9, np.max(np.abs(cloud))))
    return _wide(out, rng, 0.45)


@_sfx("surfacing", space=0.8, muffle=False)
def _surfacing(dur, p, rng):
    """The helmet breaking the surface (s15): the water sheet parting off the copper (a rising
    'shloop'), a gush pouring off it, then drips."""
    n = _N(2.6)
    out = np.zeros(n)
    m = _N(0.35)
    tt = t_axis(m)
    part = tv_bandpass(pink(m, rng), lambda x: 300.0 + 2200.0 * (x / 0.35) ** 1.3, q=1.2, block=64) * np.sin(np.pi * tt / 0.35) ** 1.5
    _place(out, part / max(1e-9, np.max(np.abs(part))), 0.0, 0.8)
    _place(out, _bubble(rng, 120.0, 7.0, 0.2), 0.02, 0.5)
    m = _N(1.4)
    tt = t_axis(m)
    gush = bandpass(white(m, rng), 700.0, 7000.0, 2) * np.clip(tt / 0.05, 0, 1) * np.exp(-tt / 0.35) * (1 + 0.5 * smooth_noise(m, 20.0, rng))
    for _ in range(50):
        _place(gush, _droplet(rng, rng.uniform(1200.0, 4500.0), rng.uniform(0.003, 0.008)) * 4.0, rng.exponential(0.3), rng.uniform(0.1, 0.6))
    _place(out, _tf(gush, 0.4), 0.15, 0.7 / max(1e-9, np.max(np.abs(gush))))
    for tt0 in np.sort(rng.uniform(0.8, 2.4, 14)):
        _place(out, _droplet(rng, rng.uniform(900.0, 3000.0), rng.uniform(0.004, 0.01)), tt0, rng.uniform(0.05, 0.2))
    return _wide(out, rng, 0.4)


@_sfx("bell_surface", space=0.6, hit=True, trim=2.0, muffle=False, anchor=0.0)
def _bell_surface(dur, p, rng):
    """The bell breaking the surface (s14 'bell'): the deep surge as its mass lifts the water, then a
    curtain of sea pouring off the bronze - a heavy cascade slapping back onto the swell - thinning
    to streams and drips."""
    n = _N(4.5)
    t = t_axis(n)
    out = np.zeros(n)
    m = _N(0.7)
    surge = sos(brown(m, rng), "lowpass", 220.0, 2) * _env_sin(m, 0.18, 0.05, 0.45)
    _place(out, surge / max(1e-9, np.max(np.abs(surge))), 0.0, 0.9)
    m = _N(0.5)
    rush = bandpass(pink(m, rng), 200.0, 3000.0, 2) * _env_sin(m, 0.1, 0.05, 0.3)
    _place(out, rush / max(1e-9, np.max(np.abs(rush))), 0.05, 0.6)
    m = _N(3.6)
    tt = t_axis(m)
    dens = np.clip(tt / 0.15, 0, 1) * np.exp(-tt / 1.1)
    pour = (bandpass(pink(m, rng), 150.0, 9000.0, 2) * 0.6 + bandpass(white(m, rng), 1500.0, 9000.0, 2) * 0.4)
    pour *= dens * (1.0 + 0.45 * smooth_noise(m, 22.0, rng))
    _place(out, _tf(pour, 0.35, 0.8) / max(1e-9, np.max(np.abs(pour))), 0.12, 0.8)
    for tt0 in 0.2 + rng.exponential(0.7, 16):
        if tt0 < 3.4:
            _place(out, _slap(rng, rng.uniform(0.5, 1.0)), tt0, 0.35 * math.exp(-tt0 / 1.5))
    for tt0 in np.sort(rng.uniform(1.0, 4.3, 30)):
        _place(out, _droplet(rng, rng.uniform(900.0, 3500.0), rng.uniform(0.004, 0.01)), tt0, rng.uniform(0.03, 0.12))
    return fade(_wide(out, rng, 0.5), 0.0, 0.4)


@_sfx("cam_plunge", space=0.0, muffle=False)
def _cam_plunge(dur, p, rng):
    """The camera tipping under the waterline: the air closing over in a rush, a gulp of bubbles,
    then the world muffled (a falling low-pass)."""
    n = _N(1.8)
    t = t_axis(n)
    x = pink(n, rng)
    x = tv_lowpass(x, lambda tt: 300.0 + 6000.0 * math.exp(-max(tt - 0.25, 0.0) / 0.12) * min(1.0, tt / 0.25), q=0.9, block=64)
    x *= _env_sin(n, 0.25, 0.1, 1.2)
    b = np.zeros(n)
    _bubbles(b, rng, 0.28 + rng.exponential(0.12, 24), 120.0, 900.0, amp=(0.3, 1.0))
    out = x / max(1e-9, np.max(np.abs(x))) * 0.6 + sos(b, "lowpass", 1500.0, 2) / max(1e-9, np.max(np.abs(b))) * 0.5
    return _wide(out, rng, 0.5)


@_sfx("cam_breach", space=0.0, muffle=False)
def _cam_breach(dur, p, rng):
    """The camera rising up through the surface: muffled bubbles and pressure opening up in a rush
    (a rising low-pass) to the open air, water running off the lens."""
    n = _N(1.8)
    x = pink(n, rng)
    x = tv_lowpass(x, lambda tt: 400.0 + 6500.0 * _smoothstep(np.array((tt - 0.45) / 0.35)).item(), q=0.8, block=64)
    x *= _env_sin(n, 0.5, 0.05, 1.1)
    b = np.zeros(n)
    _bubbles(b, rng, np.sort(rng.uniform(0.0, 0.5, 18)), 150.0, 1000.0)
    run = bandpass(white(n, rng), 1500.0, 6000.0, 2) * np.clip((t_axis(n) - 0.55) / 0.05, 0, 1) * np.exp(-np.maximum(t_axis(n) - 0.55, 0) / 0.4)
    out = (x / max(1e-9, np.max(np.abs(x))) * 0.6 + sos(b, "lowpass", 1400.0, 2) / max(1e-9, np.max(np.abs(b))) * 0.45
           + run / max(1e-9, np.max(np.abs(run))) * 0.2)
    return _wide(out, rng, 0.5)


@_sfx("uw_whoosh", space=0.5)
def _uw_whoosh(dur, p, rng):
    """Water pushed past the camera underwater (whip pans, push-ins, rising): a thick, muffled
    surge. size 0..1 (0.6)."""
    s = float(np.clip(p.get("size", 0.6), 0, 1))
    L = 0.4 + 1.1 * s
    n = _N(L + 0.15)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    c = np.where(u < 0.6, 200.0 + 900.0 * (u / 0.6) ** 1.5, 300.0 + 800.0 * np.exp(-(u - 0.6) / 0.15))
    x = tv_bandpass(pink(n, rng), c, q=0.8, block=64) + 0.6 * sos(brown(n, rng), "lowpass", 220.0, 2)
    x *= np.where(u < 0.6, (u / 0.6) ** 2, np.exp(-(u - 0.6) / 0.12))
    return _pan_sweep(x, -0.6, 0.6), 5.0 * (s - 0.6)


@_sfx("fish_school", space=0.6)
def _fish_school(dur, p, rng):
    """A school of fish sweeping past the diver (s03): hundreds of tail flicks - tiny soft 'fwips' -
    and the water they move, panning across."""
    L = 2.6
    n = _N(L + 0.3)
    t = t_axis(n)
    env = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 1.6
    out = np.zeros(n)
    times = dsp.poisson_times(lambda tt: 160.0 * math.sin(math.pi * min(max(tt / L, 0.0), 1.0)) ** 1.5 + 1e-3, L, rng)
    for tt in times:
        m = _N(0.03)
        f = rng.uniform(250.0, 1400.0)
        fl = tv_bandpass(white(m, rng), f * (1.0 + 0.8 * np.linspace(0, 1, m)), q=2.0, block=16) * np.hanning(m)
        _place(out, fl, tt, rng.uniform(0.2, 1.0))
    sw = tv_bandpass(pink(n, rng), 250.0 + 700.0 * env, q=0.9, block=64) * env
    out = out / max(1e-9, np.max(np.abs(out))) + 0.5 * sw / max(1e-9, np.max(np.abs(sw)))
    return _pan_sweep(out, -0.7, 0.7)


# ============================================================================ Bass graphics (paper)
@_sfx("paper_slice", space=0.5, muffle=False)
def _paper_slice(dur, p, rng):
    """The red line drawing itself across black paper (s01; reversed in s16): a scissor-cut 'zip'
    that decelerates (out-cubic ease) - paper grain and a falling hiss. reverse 0/1, length (1.0)."""
    L = float(p.get("length", 1.0))
    n = _N(L + 0.25)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    speed = 3.0 * (1.0 - u) ** 2
    speed = speed * np.clip(t / 0.01, 0, 1)
    cut = tv_bandpass(white(n, rng), 1300.0 + 4500.0 * np.clip(speed / 3.0, 0, 1), q=1.2, block=64) * np.clip(speed / 3.0, 0, 1) ** 0.7
    ph = np.cumsum(1500.0 * speed / 3.0 + 40.0) / SR
    grain = np.zeros(n)
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0] + 1
    grain[idx] = rng.uniform(0.3, 1.0, len(idx)) * rng.choice([-1.0, 1.0], len(idx))
    grain = bandpass(grain, 2000.0, 8000.0, 2) * np.clip(speed / 3.0, 0, 1) ** 0.5
    out = cut / max(1e-9, np.max(np.abs(cut))) + 0.6 * grain / max(1e-9, np.max(np.abs(grain)))
    out += _burst(n, rng, 150, 900, t60=0.04, attack=0.001) * 0.3
    if int(p.get("reverse", 0)):
        out = out[::-1].copy()
        out = _ramp(out, 5.0)
    return _wide(out, rng, 0.3)


@_sfx("paper_pop", space=0.5, muffle=False)
def _paper_pop(dur, p, rng):
    """A cut-paper shape snapping onto the board: a dry 'pap' and a tiny card thump. pitch (1.0)."""
    pt = float(p.get("pitch", 1.0)) * rng.uniform(0.94, 1.06)
    n = _N(0.25)
    out = np.zeros(n)
    _place(out, _burst(_N(0.08), rng, 500 * pt, 4500 * pt, t60=0.03, attack=0.0006), 0.0, 1.0)
    _place(out, _thump(_N(0.15), 180.0 * pt, 105.0 * pt, 0.008, 0.07, attack=0.0008), 0.0, 1.1)
    _place(out, _burst(_N(0.01), rng, lo=3000, t60=0.002, attack=0.0002), 0.0, 0.25)
    _place(out, _burst(_N(0.12), rng, 1500, 6000, t60=0.06, attack=0.004), 0.012, 0.12)
    return out


@_sfx("paper_slide", space=0.5, muffle=False)
def _paper_slide(dur, p, rng):
    """A cut-out sliding across the board: a quick paper swish. length (0.35)."""
    L = float(p.get("length", 0.35)) * rng.uniform(0.9, 1.1)
    if int(p.get("sides", 1)) >= 2:
        a = render_raw("paper_slide", dict(length=L), rng)
        b = render_raw("paper_slide", dict(length=L * rng.uniform(0.9, 1.1)), rng)
        out = np.zeros((max(len(a), len(b)) + _N(0.03), 2))
        _place(out, dsp.pan_mono(a, -0.7), 0.0)
        _place(out, dsp.pan_mono(b, 0.7), 0.025)
        return out
    n = _N(L + 0.05)
    tt = t_axis(n)
    x = tv_bandpass(white(n, rng), lambda z: 900.0 + 3500.0 * math.sin(math.pi * min(z / L, 1.0)), q=0.9, block=64)
    x += 0.4 * bandpass(crackle(n, 1500.0, rng), 2000.0, 7000.0, 2)
    return x * np.sin(np.pi * np.clip(tt / L, 0, 1)) ** 1.2


def _pop1(rng, pt=1.0, body=1.0):
    n = _N(0.3)
    out = np.zeros(n)
    _place(out, _burst(_N(0.08), rng, 500 * pt, 4500 * pt, t60=0.03, attack=0.0006), 0.0, 1.0)
    _place(out, _thump(_N(0.15), 180.0 * pt, 105.0 * pt, 0.008, 0.07, attack=0.0008), 0.0, 1.1 * body)
    _place(out, _burst(_N(0.01), rng, lo=3000, t60=0.002, attack=0.0002), 0.0, 0.25)
    _place(out, _burst(_N(0.12), rng, 1500, 6000, t60=0.06, attack=0.004), 0.012, 0.12)
    return out


@_sfx("paper_pops", space=0.5, muffle=False)
def _paper_pops(dur, p, rng):
    """A run of cut-outs popping on (s04 lifeboats): count (8) pops every gap s (0.12), stepping
    up in pitch, alternating a little left/right."""
    k = int(p.get("count", 8))
    gap = float(p.get("gap", 0.12))
    n = _N(gap * k + 0.4)
    out = np.zeros((n, 2))
    for i in range(k):
        pop = _pop1(rng, (1.0 + 0.045 * i) * rng.uniform(0.97, 1.03), 0.8)
        _place(out, dsp.pan_mono(pop, 0.25 * (-1) ** i), i * gap, rng.uniform(0.8, 1.0))
    return out


@_sfx("paper_slam", space=0.5, hit=True, muffle=False)
def _paper_slam(dur, p, rng):
    """A big black cut-out slammed down onto the board (s04 storm): a heavy card 'whap', the
    air it pushes, a low thud of the table. size 0..1 (1): smaller = a lighter slap."""
    sz = float(np.clip(p.get("size", 1.0), 0.1, 1.0))
    n = _N(0.9)
    out = np.zeros(n)
    m = _N(0.12)
    air = tv_bandpass(pink(m, rng), lambda x: 400.0 + 2000.0 * x / 0.12, q=0.8, block=32) * np.linspace(0, 1, m) ** 2
    _place(out, air / _pk(air), 0.0, 0.3)
    _place(out, _burst(_N(0.15), rng, 250, 5000, t60=0.05, attack=0.0005), 0.12, 1.0)
    _place(out, _thump(_N(0.5), 120.0 + 60.0 * (1 - sz), 55.0 + 40.0 * (1 - sz), 0.02, 0.1 + 0.15 * sz, attack=0.001), 0.12, 1.4 * sz)
    _place(out, _modes(rng, [190.0, 410.0, 760.0], [0.15, 0.1, 0.07], n=_N(0.3)), 0.12, 0.3)
    return out, -6.0 * (1.0 - sz)


@_sfx("paper_scrape", space=0.5, muffle=False)
def _paper_scrape(dur, p, rng):
    """Jagged card dragged up across the board (s04 reef): a rough, grainy, stuttering scrape."""
    L = 0.5
    n = _N(L + 0.1)
    t = t_axis(n)
    sw = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.8
    rate = 90.0 + 160.0 * sw
    x = dsp.friction(n, rate, rng, jitter=0.6, body=[(900.0, 3.0, 1.0), (2100.0, 4.0, 0.7), (4200.0, 5.0, 0.4)])
    x = x / _pk(x) + 0.25 * bandpass(white(n, rng), 1500.0, 7000.0, 2) * sw
    return x * sw


@_sfx("paper_flutter", space=0.6, muffle=False)
def _paper_flutter(dur, p, rng):
    """Small paper cut-outs fluttering down: a soft cloud of light flaps and ticks. length (1.0)."""
    L = float(p.get("length", dur if dur else 1.0) or 1.0)
    n = _N(L + 0.2)
    t = t_axis(n)
    env = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.7
    out = np.zeros(n)
    for tt in dsp.poisson_times(lambda z: 45.0 * math.sin(math.pi * min(max(z / L, 0.0), 1.0)) + 1e-3, L, rng):
        m = _N(0.025)
        f = rng.uniform(1500.0, 5000.0)
        fl = bandpass(white(m, rng), f * 0.6, min(f * 1.6, 16000.0), 2) * np.hanning(m)
        _place(out, fl, tt, rng.uniform(0.2, 1.0))
    out += 0.15 * bandpass(pink(n, rng), 800.0, 4000.0, 2) * env / 3.0
    return _wide(out, rng, 0.6)


@_sfx("card_flip", space=0.5, muffle=False)
def _card_flip(dur, p, rng):
    """A big card turned over (s04: the field flips to paper): a fast airy 'fwip' and a flat slap."""
    n = _N(0.45)
    out = np.zeros(n)
    m = _N(0.14)
    fw = tv_bandpass(pink(m, rng), lambda x: 600.0 + 4000.0 * (x / 0.14) ** 1.5, q=1.0, block=32)
    fw *= np.sin(np.pi * t_axis(m) / 0.14) ** 2
    _place(out, fw / _pk(fw), 0.0, 0.7)
    _place(out, _pop1(rng, 0.85, 0.8), 0.12, 0.9)
    return out


@_sfx("paper_jab", space=0.5, muffle=False)
def _paper_jab(dur, p, rng):
    """Paper arms jabbing forward: a short sharp swish ending in a tap."""
    n = _N(0.35)
    out = np.zeros(n)
    m = _N(0.09)
    sw = tv_bandpass(white(m, rng), lambda x: 1200.0 + 4000.0 * x / 0.09, q=1.2, block=32) * np.linspace(0, 1, m) ** 1.5
    _place(out, sw / _pk(sw), 0.0, 0.6)
    _place(out, _pop1(rng, 1.2, 0.5), 0.09, 0.8)
    return out


@_sfx("paper_stamp", space=0.5, hit=True, trim=1.0, muffle=False)
def _paper_stamp(dur, p, rng):
    """The red ring snapping shut round the captain: a hard rubber stamp - a heavy dead 'TUNK' of
    the stamp hitting paper on wood, the snap of the ring closing."""
    n = _N(0.8)
    out = np.zeros(n)
    _place(out, _burst(_N(0.03), rng, 1500, 9000, t60=0.008, attack=0.0002), 0.0, 0.6)
    _place(out, _thump(_N(0.5), 160.0, 72.0, 0.012, 0.18, attack=0.0005), 0.0, 1.5)
    _place(out, _modes(rng, [230.0, 540.0, 980.0, 1600.0], [0.12, 0.08, 0.05, 0.035], n=_N(0.3)), 0.0, 0.5)
    _place(out, _burst(_N(0.1), rng, 100, 1200, t60=0.04, attack=0.0005), 0.0, 0.8)
    return out


@_sfx("paper_hole", space=0.6, hit=True, trim=-1.0, muffle=False)
def _paper_hole(dur, p, rng):
    """A black hole opening in the paper (s04 end): a hollow low thud (a drum skin of card) and
    the figure falling away - a soft descending whistle of air into the dark."""
    n = _N(1.6)
    out = np.zeros(n)
    _place(out, _thump(_N(0.8), 95.0, 42.0, 0.04, 0.45, attack=0.002), 0.0, 1.0)
    hol = resonator_bank(_burst(_N(0.6), rng, 60, 900, t60=0.25, attack=0.002), [110.0, 175.0, 260.0], [12.0, 14.0, 16.0], [1.0, 0.7, 0.5])
    _place(out, hol / _pk(hol), 0.0, 0.6)
    m = _N(1.1)
    tt = t_axis(m)
    fall = tv_bandpass(pink(m, rng), lambda x: 1400.0 * math.exp(-x / 0.4) + 180.0, q=4.0, block=64)
    fall *= np.clip(tt / 0.05, 0, 1) * np.exp(-tt / 0.35)
    _place(out, fall / _pk(fall), 0.08, 0.35)
    return out


@_sfx("paper_swishes", space=0.5, muffle=False)
def _paper_swishes(dur, p, rng):
    """Several cut-outs sliding in, staggered (bars, rows of arms): count (3) swishes over
    length s (0.7), alternating sides. sides 2 = from both sides at once."""
    k = int(p.get("count", 3))
    L = float(p.get("length", 0.7))
    both = int(p.get("sides", 1)) >= 2
    n = _N(L + 0.5)
    out = np.zeros((n, 2))
    for i in range(k):
        t0 = (L * i / max(k, 1)) * rng.uniform(0.9, 1.1)
        sl = render_raw("paper_slide", dict(length=rng.uniform(0.22, 0.34)), rng)
        if both:
            _place(out, dsp.pan_mono(sl, -0.7), t0, 0.7)
            _place(out, dsp.pan_mono(render_raw("paper_slide", dict(length=rng.uniform(0.22, 0.34)), rng), 0.7), t0 + 0.02, 0.7)
        else:
            _place(out, _pan_sweep(sl, 0.6 * (-1) ** i, -0.2 * (-1) ** i), t0, rng.uniform(0.7, 1.0))
    return out


@_sfx("paper_ticks", space=0.5, muffle=False)
def _paper_ticks(dur, p, rng):
    """A ripple of tiny card clicks travelling left to right (cut-outs clipped onto a line).
    count (12), length s (0.45)."""
    k = max(1, int(p.get("count", 12)))
    L = float(p.get("length", 0.45 if k > 1 else 0.05))
    n = _N(L + 0.15)
    out = np.zeros((n, 2))
    for i in range(k):
        u = i / max(k - 1, 1)
        tt = L * u * rng.uniform(0.97, 1.03) if k > 1 else 0.0
        m = _N(0.03)
        f = rng.uniform(2200.0, 4200.0)
        tk = _modes(rng, [f, f * 1.47, f * 2.1], [0.012, 0.009, 0.006], [1.0, 0.5, 0.25], n=m, attack=0.0002)
        tk += _burst(m, rng, 1500, 7000, t60=0.004, attack=0.0002) * 0.5
        _place(out, dsp.pan_mono(tk, -0.7 + 1.4 * u), tt, rng.uniform(0.6, 1.0))
    return out


@_sfx("metal_ping", space=0.6, muffle=False)
def _metal_ping(dur, p, rng):
    """A small bright metallic ping (a torch cut closing, a steel edge tapped)."""
    fr = np.array([1480.0, 2390.0, 3730.0, 5210.0, 6890.0]) * rng.uniform(0.95, 1.05)
    x = _modes(rng, fr, [0.9, 0.7, 0.5, 0.35, 0.25], [1.0, 0.7, 0.45, 0.3, 0.2], n=_N(1.2), attack=0.0004, beat=1.5)
    x += _burst(_N(1.2), rng, lo=2500, t60=0.004, attack=0.0001) * 0.3
    return x


@_sfx("low_boom", space=0.6, hit=True, trim=-1.0, muffle=False)
def _low_boom(dur, p, rng):
    """A low, muffled boom (a figure falling into the deep, a bar closing): sub thump bending down,
    a dark noise bloom, no hard edge."""
    n = _N(2.2)
    t = t_axis(n)
    out = _thump(n, 70.0, 34.0, 0.08, 0.9, attack=0.006)
    bl = sos(brown(n, rng), "lowpass", 240.0, 2) * np.clip(t / 0.02, 0, 1) * np.exp(-t / 0.35)
    out += 0.6 * bl / _pk(bl)
    out += 0.25 * _modes(rng, [92.0, 141.0, 208.0], [0.9, 0.7, 0.5], n=n, attack=0.004)
    return sos(out, "lowpass", 900.0, 2)


@_sfx("ship_groan", space=0.8, muffle=False)
def _ship_groan(dur, p, rng):
    """A wooden ship's hull straining as she heels over (s04, the paper ship sinking): a deep,
    slow timber groan - longer and lower than a deck creak."""
    L = float(p.get("length", 1.4))
    n = _N(L + 0.3)
    t = t_axis(n)
    sw = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.9
    rate = (9.0 + 26.0 * sw) * (1.0 + 0.2 * smooth_noise(n, 1.5, rng))
    x = dsp.friction(n, rate, rng, jitter=0.4, body=[(95.0, 6.0, 1.0), (180.0, 7.0, 0.9), (330.0, 8.0, 0.7), (610.0, 9.0, 0.4),
                                                    (1150.0, 10.0, 0.2)])
    sub = np.sin(TWO_PI * np.cumsum(48.0 - 8.0 * t / (n / SR)) / SR) * sw ** 1.5
    return x / _rms(x) * sw + 0.4 * sub / _rms(sub)


@_sfx("torch_cut", space=0.5, muffle=False)
def _torch_cut(dur, p, rng):
    """s07: a cutting torch lighting (pop-whump) and biting through steel from the inside - roar,
    sputtering molten crackle, the valve shut off. length (1.2)."""
    L = float(p.get("length", 1.2))
    n = _N(L + 0.4)
    t = t_axis(n)
    out = np.zeros(n)
    _place(out, _burst(_N(0.15), rng, hi=900, t60=0.06, attack=0.0005), 0.0, 1.0)
    _place(out, _thump(_N(0.3), 90.0, 60.0, 0.02, 0.12), 0.0, 0.6)
    on = np.clip((t - 0.04) / 0.05, 0, 1) * np.clip((L - t) / 0.06, 0, 1)
    roar = bandpass(pink(n, rng), 120.0, 3000.0, 2) * (1.0 + 0.35 * smooth_noise(n, 30.0, rng)) + 0.5 * bandpass(white(n, rng), 3000.0, 10000.0, 2)
    roar = roar / max(1e-9, np.max(np.abs(roar))) * on
    sp = bandpass(crackle(n, 90.0, rng, amp_spread=1.2), 2000.0, 9000.0, 2) * on
    out += 0.6 * roar + 0.8 * sp / max(1e-9, np.max(np.abs(sp)))
    off = _burst(_N(0.2), rng, 800, 6000, t60=0.08, attack=0.002)
    _place(out, off, L, 0.3)
    return _wide(out, rng, 0.35)


@_sfx("plate_fall", space=0.5, muffle=False)
def _plate_fall(dur, p, rng):
    """The cut steel disk falling away (s07): a short rush of air, then a heavy dull clang and a
    spinning, settling rattle."""
    n = _N(2.0)
    out = np.zeros(n)
    m = _N(0.25)
    rush = tv_bandpass(pink(m, rng), lambda x: 300.0 + 1500.0 * x / 0.25, q=0.9, block=64) * np.linspace(0, 1, m) ** 2
    _place(out, rush / max(1e-9, np.max(np.abs(rush))), 0.0, 0.3)
    fr = np.array([180.0, 410.0, 690.0, 1040.0, 1480.0, 2050.0]) * rng.uniform(0.95, 1.05)
    _place(out, _modes(rng, fr, [0.9, 0.7, 0.55, 0.42, 0.3, 0.2], n=_N(1.2), attack=0.0003, beat=0.8) + _thump(_N(1.2), 95.0, 55.0, 0.02, 0.2) * 0.7, 0.25, 1.0)
    tt, gap, a = 0.62, 0.11, 0.35
    while gap > 0.012 and tt < 1.8:
        _place(out, _modes(rng, fr[1:4] * rng.uniform(0.98, 1.02), [0.12, 0.09, 0.07], n=_N(0.15), attack=0.0003), tt, a)
        tt += gap
        gap *= 0.8
        a *= 0.9
    return out


@_sfx("cash_riffle", space=0.5, muffle=False)
def _cash_riffle(dur, p, rng):
    """A fan of banknotes riffled / a stack doubling (s07 'worth'): quick crisp paper flicks."""
    n = _N(0.6)
    out = np.zeros(n)
    tt, gap = 0.0, 0.035
    while tt < 0.42:
        _place(out, _burst(_N(0.03), rng, 1500, 7500, t60=0.01, attack=0.0003), tt, rng.uniform(0.4, 1.0))
        tt += gap * rng.uniform(0.7, 1.3)
        gap *= 0.93
    sw = tv_bandpass(white(n, rng), lambda z: 1200.0 + 3000.0 * min(z / 0.4, 1.0), q=0.8, block=64) * _env_sin(n, 0.1, 0.25, 0.2) * 0.3
    return _wide(out + sw, rng, 0.35)


# ============================================================================ the s13 hits
@_sfx("weights_drop", space=1.0, hit=True, trim=0.0)
def _weights_drop(dur, p, rng):
    """s13: the chest weights unbuckled - a dull lead clunk off the breastplate, the fall, and the
    heavy landing in silt (a deep, slow 'fwumph' with a puff)."""
    n = _N(2.2)
    out = np.zeros(n)
    _place(out, _modes(rng, [300.0, 680.0, 1150.0, 1800.0], [0.1, 0.07, 0.05, 0.035], n=_N(0.2), attack=0.0004) +
           _burst(_N(0.2), rng, lo=1500, t60=0.004, attack=0.0001) * 0.3, 0.0, 0.35)
    land = render_raw("silt_puff", dict(size=1.0, metal=1.0), rng)
    _place(out, land, 0.32, 1.0 / max(1e-9, np.max(np.abs(land))))
    return out


@_sfx("boot_drop", space=1.0, hit=True, trim=-2.0)
def _boot_drop(dur, p, rng):
    """s13: a lead boot kicked off, landing in the silt: a soft drop and a thud."""
    land = render_raw("silt_puff", dict(size=0.75, metal=0.6), rng)
    return land / max(1e-9, np.max(np.abs(land)))


@_sfx("buckle", space=1.0)
def _buckle(dur, p, rng):
    """A weight-belt buckle thrown open underwater: a muffled metal latch and the strap sliding."""
    n = _N(0.7)
    out = np.zeros(n)
    _place(out, _modes(rng, [1900.0, 3100.0, 4600.0], [0.06, 0.045, 0.03], n=_N(0.1), attack=0.0002), 0.0, 1.0)
    _place(out, _modes(rng, [1500.0, 2700.0], [0.08, 0.05], n=_N(0.12), attack=0.0002), 0.06, 0.6)
    m = _N(0.4)
    st = dsp.friction(m, 200.0, rng, jitter=0.3, body=[(900.0, 5.0, 1.0), (1900.0, 7.0, 0.5)]) * np.sin(np.pi * t_axis(m) / 0.4)
    _place(out, st / max(1e-9, np.max(np.abs(st))), 0.1, 0.3)
    return out


def render_raw(name, params, rng):
    """A catalog sound's raw (un-normalised) mono render, using the caller's rng - for composites."""
    res = _REG[name]["fn"](_REG[name]["default_dur"], dict(params), rng)
    x = res[0] if isinstance(res, tuple) else res
    return dsp.mono(np.asarray(x, dtype=np.float64))


# ============================================================================ heartbeat
def lubdub(rng, strength=1.0, period=1.0):
    """One heartbeat heard from inside: lub (low, longer), dub (higher, shorter), low-passed;
    a touch of saturation so phones hear it."""
    n = _N(0.8)
    out = np.zeros(n)
    lub = _thump(_N(0.4), 62.0, 41.0, 0.035, 0.2, attack=0.006)
    lub += 0.35 * _burst(_N(0.4), rng, hi=130, t60=0.06, attack=0.005, color="brown")[:len(lub)] / 3.0
    dub = _thump(_N(0.3), 80.0, 52.0, 0.025, 0.13, attack=0.004) * 0.65
    _place(out, lub, 0.0)
    _place(out, dub, 0.27 * max(period, 0.4) ** 0.5)
    out = sos(out, "lowpass", 170.0, 2)
    out += 0.16 * sos(saturate(out * 3.0, 2.0), "bandpass", (90.0, 380.0), 2)
    return out * strength


def heartbeat_track(times, n, seed=0, strengths=None):
    """Heartbeats at the given times (seconds from the track start)."""
    rng = np.random.default_rng(dsp.stable_seed("salvage-heart", seed))
    out = np.zeros(n)
    times = list(times)
    for i, tt in enumerate(times):
        per = (times[i + 1] - tt) if i + 1 < len(times) else (tt - times[i - 1] if i else 1.0)
        s = 1.0 if strengths is None else strengths[i]
        _place(out, lubdub(rng, s, per), tt)
    return out


def beat_times(t0, t1, bpm0, bpm1=None):
    """Beat times from t0 while t < t1, the rate gliding linearly bpm0 -> bpm1 across the span."""
    bpm1 = bpm0 if bpm1 is None else bpm1
    out = []
    t = t0
    while t < t1:
        out.append(t)
        u = (t - t0) / max(t1 - t0, 1e-6)
        t += 60.0 / (bpm0 + (bpm1 - bpm0) * u)
    return out


@_sfx("heartbeat_deep", kind="sustained", norm="int", default_dur=6.0, space=0.0, muffle=False)
def _heartbeat_deep(dur, p, rng):
    """The diver's heartbeat inside the sealed helmet (s13). params: bpm (62), bpm_end."""
    b0 = float(p.get("bpm", 62.0))
    b1 = float(p.get("bpm_end", b0))
    n = _N(dur)
    return heartbeat_track(beat_times(0.02, dur - 0.3, b0, b1), n, int(rng.integers(1 << 30)))


# ============================================================================ scene-cue resolver
# A scene's Cue(sfx=...) is free text ('helmet clank', 'eight small paper pops, 0.12 s apart').
# Each alias: groups of alternatives (every group must match), the catalog name, default params.
# Ordered specific -> generic. Paper context (the text mentions paper/card, or the scene is a
# Bass graphic scene) uses the paper table first.
PAPER_SCENES = ("s04", "s07")

# sound words first (what the animator says it sounds like), then event words (what happens)
PAPER_SOUND = (
    (("red line|line drawn|line draws|draws itself",), "paper_slice", {}),
    (("ping|tink|ting|metallic",), "metal_ping", {}),
    (("torch",), "torch_cut", {}),
    (("bubble",), "surface_pops", {}),
    (("tear|rip|torn",), "paper_tear", {}),
    (("pops",), "paper_pops", {}),
    (("ticks|clicks",), "paper_ticks", {}),
    (("stamp",), "paper_stamp", {}),
    (("swishes|staggered",), "paper_swishes", {}),
    (("slap|whap|smack",), "paper_slam", {"size": 0.5}),
    (("slam|snap",), "paper_slam", {}),
    (("flip",), "card_flip", {}),
    (("scrape|grind",), "paper_scrape", {}),
    (("flutter",), "paper_flutter", {}),
    (("jab|thrust",), "paper_jab", {}),
    (("groan|creak",), "ship_groan", {}),
    (("muffled|deep whoosh|surge|rush",), "uw_whoosh", {}),
    (("whoosh",), "whoosh", {"size": 0.35}),
    (("clang",), "plate_fall", {}),
    (("riffle",), "cash_riffle", {}),
    (("swish|slide|glide|hiss|swipe",), "paper_slide", {}),
    (("hollow",), "paper_hole", {}),
    (("thud|boom|thump",), "low_boom", {}),
    (("pop",), "paper_pop", {}),
    (("tick|click",), "paper_ticks", {"count": 1}),
)
PAPER_EVENT = (
    (("hole",), "paper_hole", {}),
    (("disk|disc|plate",), "plate_fall", {}),
    (("banknote|notes|cash|money|stack",), "cash_riffle", {}),
    (("bars|rows|wave|columns",), "paper_swishes", {}),
    (("strip",), "paper_slice", {}),
    (("appear|land|drop",), "paper_pop", {}),
    (("float|drift|confetti",), "paper_flutter", {}),
    (("point",), "paper_jab", {}),
    (("tilt",), "ship_groan", {}),
    (("sinks|slides under",), "uw_whoosh", {}),
    (("burn|cutting|weld",), "torch_cut", {}),
)

ALIASES = (
    (("ambience|ambient|room tone|atmos",), "ambience", {}),
    (("free flow|freeflow|helmet hiss",), "helmet_hiss", {}),
    (("diver|helmet", "hiss"), "helmet_hiss", {}),
    (("toll",), "meridian_bell", {}),
    (("bell", "muffl|underwater|dull"), "meridian_bell_uw", {}),
    (("bell", "pour|surface|break|emerge|water"), "bell_surface", {}),
    (("bell",), "meridian_bell", {}),
    (("helmet", "unlock|off|lift|remove|open"), "helmet_unlock", {}),
    (("helmet", "clank|lock|seat|turn"), "helmet_clank", {}),
    (("clank",), "helmet_clank", {}),
    (("lamp|light switch|switch",), "lamp_click", {}),
    (("tumbler",), "tumbler_click", {}),
    (("dial", "click"), "tumbler_click", {}),
    (("dial",), "dial_turn", {}),
    (("safe", "open|door|bolt|swing|hinge"), "safe_open", {}),
    (("knife|blade", "draw|unsheath|pull"), "knife_draw", {}),
    (("glint|gleam|sparkle",), "knife_glint", {}),
    (("slash|sever",), "hose_cut", {}),
    (("cut", "hose|rubber"), "hose_cut", {}),
    (("hiss|escap|jet",), "air_escape", {}),
    (("tug|jerk|yank",), "rope_tug", {}),
    (("tie|ties|tied|knot|hitch",), "rope_tie", {}),
    (("taut|tight|tension|strain",), "winch_strain", {}),
    (("winch|ratchet|crank",), "winch_crank", {}),
    (("pump|flywheel|chuff",), "pump_run", {}),
    (("weight",), "weights_drop", {}),
    (("boot",), "boot_drop", {}),
    (("buckle|unbuckl",), "buckle", {}),
    (("whoosh",), "uw_whoosh", {}),
    (("exhale|bubble|exhaust",), "exhaust_bubbles", {}),
    (("breath|inhale|gasp|sigh",), "breath_single", {}),
    (("heart",), "heartbeat_deep", {}),
    (("whoosh|swish|sweep|rush|surge",), "uw_whoosh", {}),
    (("splash|plunge|lets go|drops in|jumps in",), "entry_splash", {}),
    (("surfac|breach|emerge",), "surfacing", {}),
    (("silt|puff|mud",), "silt_puff", {}),
    (("ladder|rung|climb",), "ladder_step", {}),
    (("deck", "step|footstep|walk"), "deck_step", {}),
    (("step|footstep|walk|stomp|gait",), "silt_step", {}),
    (("wood", "groan|creak"), "deck_creak", {}),
    (("groan|moan",), "hull_groan", {}),
    (("rope|line|hemp|davit", "creak|squeak|rub"), "rope_creak", {}),
    (("creak|squeak",), "metal_creak", {}),
    (("ping|tonk",), "hull_ping", {}),
    (("hook|clang|knock",), "hook_clank", {}),
    (("chair",), "chair_turn", {}),
    (("touch|glove|petal|finger|grip",), "glove_metal", {}),
    (("cigar|ember",), "cigar_draw", {}),
    (("envelope|cash|money|banknote",), "envelope_pass", {}),
    (("slap|lap|wave",), "water_slap", {}),
    (("gull|seagull|bird",), "gull_call", {}),
    (("torch|weld",), "torch_cut", {}),
    (("tear|rip",), "paper_tear", {}),
    (("page|flip",), "page_flip", {}),
    (("photo",), "paper_slide", {"length": 0.6}),
    (("riffle",), "cash_riffle", {}),
    (("pop|stamp",), "paper_pop", {}),
    (("fish|school",), "fish_school", {}),
    (("boom|thud|thump",), "low_boom", {}),
    (("slide|swipe|slip",), "paper_slide", {}),
    (("click",), "lamp_click", {}),
)

# sounds whose 'length' param a cue's dur sets (instead of truncating the one-shot)
LENGTH_PARAM = ("paper_flutter", "paper_swishes", "paper_slide", "ship_groan", "hull_groan", "torch_cut", "meridian_bell",
                "meridian_bell_uw", "breath_single")

_NUMWORDS = dict(one=1, two=2, three=3, four=4, five=5, six=6, seven=7, eight=8, nine=9, ten=10, eleven=11, twelve=12,
                 thirteen=13, fourteen=14, fifteen=15, twenty=20, thirty=30)


def _norm_text(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9. ]", " ", str(s).lower().replace("_", " ").replace("-", " "))).strip()


def _count(s):
    m = re.search(r"\b(\d+)\b(?!\.\d)(?!\s*s\b)", s)
    if m and not re.search(r"\d+\.\d+", m.group(0)):
        return int(m.group(1))
    for w, v in _NUMWORDS.items():
        if re.search(rf"\b{w}\b", s):
            return v
    return None


def _has(s, alt):
    return re.search(r"\b" + re.escape(alt), s) is not None


def _match(table, s):
    for groups, name, params in table:
        if all(any(_has(s, alt) for alt in g.split("|")) for g in groups):
            return name, dict(params)
    return None, {}


def resolve(text, scene=None, dur=None):
    """Free-text cue -> (catalog name, params) or (None, {}) when nothing fits. scene (id) and
    dur (s) refine it: Bass scenes resolve to paper sounds; counts ('eight ... pops'), spacing
    ('0.12 s apart'), 'both sides' and lengths become params."""
    raw = str(text).strip()
    key = raw.lower().replace(" ", "_")
    if key in _REG or libsfx.exists(key):
        return key, {}
    s = _norm_text(raw)
    paper = scene in PAPER_SCENES or any(_has(s, w) for w in ("paper", "card", "cut out", "cutout"))
    name, params = (None, {})
    if paper:
        name, params = _match(PAPER_SOUND, s)
        if name is None:
            name, params = _match(PAPER_EVENT, s)
    if name is None:
        name, params = _match(ALIASES, s)
    if name is None:
        return None, {}
    fast = any(_has(s, w) for w in ("fast", "quick", "rapid"))
    if name in ("paper_pops", "paper_ticks") and "count" not in params:
        c = _count(s) or (6 if name == "paper_pops" else 12)
        params["count"] = c
        g = re.search(r"(\d*\.\d+|\d+)\s*s\b", s)
        if name == "paper_pops":
            if g:
                params["gap"] = float(g.group(1))
            elif dur:
                params["gap"] = float(dur) / c
            elif fast:
                params["gap"] = min(0.12, 1.2 / c)
        elif dur:
            params["length"] = float(dur)
        elif fast or c > 12:
            params["length"] = min(0.6, 0.02 * c)
    if name == "paper_slam" and _has(s, "soft"):
        params["size"] = min(params.get("size", 1.0), 0.4)
    if name == "paper_pop" and _has(s, "heav"):
        params["pitch"] = 0.8
    if name in ("paper_swishes",):
        params["count"] = _count(s) or 3
    if "both sides" in s and name in ("paper_slide", "paper_swishes"):
        params["sides"] = 2
    if name in ("uw_whoosh",) and any(w in s for w in ("deep", "big", "huge", "heavy")):
        params["size"] = 0.9
    if dur and name in LENGTH_PARAM:
        params["length"] = float(dur)
    return name, params


if __name__ == "__main__":
    print(f"{len(_REG)} SALVAGE sounds:")
    for k in names():
        sp = _REG[k]
        print(f"  {k:<18} {sp['kind']:<9} hit={int(sp['hit'])} muffle={int(sp['muffle'])} anchor={sp['anchor']:.2f}  {sp['doc'][:70]}")
