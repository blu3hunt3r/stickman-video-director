"""DSP primitives for the procedural soundtrack. 48 kHz, stereo arrays are (n, 2) float32.

Everything is vectorised numpy/scipy; the only Python loops run at a decimated control
rate (dynamics) or once per delay-line period (Karplus-Strong), so a full 179 s film
renders in a couple of minutes on one core.

Contents
  util ........ sample/second helpers, deterministic RNG, fades, stereo helpers, mix_into
  osc ......... PolyBLEP saw / square, sine, triangle, FM operator, band-limited pulse train
  noise ....... white, pink, brown, velvet, crackle (sparse impulses)
  env ......... ADSR, exponential decay, breakpoint envelopes, one-pole / attack-release smoothers
  filters ..... RBJ biquads (static + time-varying, block-wise), Butterworth SOS, one-pole
  models ...... Karplus-Strong pluck, modal resonators, resonator bank, friction (stick-slip)
  space ....... synthesized impulse responses (small_room, office, hall, cell, alley, plate, car,
                court, street), FFT convolution reverb, equal-power panning, width, Haas
  dynamics .... saturation, compressor, sidechain ducking, true-peak look-ahead limiter
  metering .... ITU-R BS.1770-4 K-weighting, integrated / short-term / momentary loudness,
                4x oversampled true peak, RMS
  io .......... WAV writer (16/24-bit PCM, 32-bit float) and reader (scipy -> soundfile -> ffmpeg)
"""
from __future__ import annotations

import functools
import math
import os
import struct
import subprocess
import zlib
from fractions import Fraction

import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, minimum_filter1d

SR = 48000
EPS = 1e-12
TWO_PI = 2.0 * np.pi
# Anti-denormal offset (about -480 dBFS) added before every IIR: decaying filter states over long
# silent stretches otherwise fall into subnormal floats, which run ~100x slower.
DENORMAL_GUARD = 1e-24


# ============================================================================ util
def n_of(t, sr=SR):
    """Seconds -> whole samples (>= 0)."""
    return max(0, int(round(float(t) * sr)))


def t_axis(n, sr=SR):
    return np.arange(n, dtype=np.float64) / sr


def db2lin(db):
    return np.power(10.0, np.asarray(db, dtype=np.float64) / 20.0)


def lin2db(x, floor=-200.0):
    return np.maximum(20.0 * np.log10(np.maximum(np.abs(x), EPS)), floor)


def stable_seed(*keys):
    """Process-independent 32-bit seed from arbitrary keys (Python's hash() is salted)."""
    return zlib.crc32("|".join(str(k) for k in keys).encode("utf-8")) & 0xFFFFFFFF


def rng_for(*keys):
    return np.random.default_rng(stable_seed(*keys))


def to_stereo(x):
    x = np.asarray(x)
    if x.ndim == 1:
        return np.stack([x, x], axis=1)
    if x.shape[1] == 1:
        return np.repeat(x, 2, axis=1)
    return x[:, :2]


def mono(x):
    x = np.asarray(x)
    return x if x.ndim == 1 else x.mean(axis=1)


def pad_to(x, n):
    """Zero-pad or truncate along axis 0 to exactly n samples."""
    if len(x) >= n:
        return x[:n]
    pad = [(0, n - len(x))] + [(0, 0)] * (x.ndim - 1)
    return np.pad(x, pad)


def fade(x, fin=0.0, fout=0.0, sr=SR, shape="sine"):
    """Fade the edges (seconds). shape: 'sine' (equal-power quarter sine), 'lin', 'exp'."""
    x = np.array(x, dtype=np.float64, copy=True)
    n = len(x)
    for length, side in ((fin, 0), (fout, 1)):
        k = min(n, n_of(length, sr))
        if k <= 1:
            continue
        r = np.linspace(0.0, 1.0, k)
        if shape == "sine":
            w = np.sin(0.5 * np.pi * r)
        elif shape == "exp":
            w = (np.exp(4 * r) - 1) / (np.exp(4) - 1)
        else:
            w = r
        if side == 1:
            w = w[::-1]
            sl = slice(n - k, n)
        else:
            sl = slice(0, k)
        x[sl] *= w if x.ndim == 1 else w[:, None]
    return x


def declick(x, ms=3.0, sr=SR):
    return fade(x, ms / 1000.0, ms / 1000.0, sr, "sine")


def normalize_peak(x, peak_db=-1.0):
    p = np.max(np.abs(x)) if len(x) else 0.0
    return x if p < EPS else x * (db2lin(peak_db) / p)


def normalize_rms(x, rms_db=-20.0):
    r = np.sqrt(np.mean(np.square(x))) if len(x) else 0.0
    return x if r < EPS else x * (db2lin(rms_db) / r)


def mix_into(dst, src, at, gain=1.0):
    """Add src into dst starting at sample index `at` (may be negative); clips to bounds."""
    n = len(dst)
    a = int(at)
    s0 = max(0, -a)
    d0 = max(0, a)
    k = min(len(src) - s0, n - d0)
    if k <= 0:
        return dst
    seg = src[s0:s0 + k]
    if dst.ndim == 2 and seg.ndim == 1:
        seg = seg[:, None]
    dst[d0:d0 + k] += seg * gain
    return dst


def crossfade_curves(n, shape="sine"):
    r = np.linspace(0.0, 1.0, max(n, 1))
    if shape == "sine":
        return np.cos(0.5 * np.pi * r), np.sin(0.5 * np.pi * r)
    return 1.0 - r, r


def concat_xfade(a, b, xf_samples):
    """Concatenate a and b with an equal-power crossfade of xf_samples."""
    k = min(xf_samples, len(a), len(b))
    if k <= 0:
        return np.concatenate([a, b])
    fo, fi = crossfade_curves(k)
    if a.ndim == 2:
        fo, fi = fo[:, None], fi[:, None]
    mid = a[-k:] * fo + b[:k] * fi
    return np.concatenate([a[:-k], mid, b[k:]])


# ============================================================================ oscillators
def phase_acc(freq, n, sr=SR, phase0=0.0):
    """Phase in cycles [0, 1) for a (possibly time-varying) frequency. Returns (phase, dt)."""
    if np.ndim(freq) == 0:
        dt = np.full(n, float(freq) / sr)
    else:
        dt = np.asarray(freq, dtype=np.float64)[:n] / sr
        if len(dt) < n:
            dt = np.pad(dt, (0, n - len(dt)), mode="edge")
    ph = np.empty(n, dtype=np.float64)
    if n:
        ph[0] = phase0
        np.cumsum(dt[:-1], out=ph[1:])
        ph[1:] += phase0
    ph -= np.floor(ph)
    return ph, dt


def _polyblep(ph, dt):
    out = np.zeros_like(ph)
    dt = np.broadcast_to(dt, ph.shape)
    m = ph < dt
    if m.any():
        t = ph[m] / dt[m]
        out[m] = t + t - t * t - 1.0
    m = ph > 1.0 - dt
    if m.any():
        t = (ph[m] - 1.0) / dt[m]
        out[m] = t * t + t + t + 1.0
    return out


def saw(freq, n, sr=SR, phase0=0.0):
    """Band-limited (PolyBLEP) sawtooth, -1..1."""
    ph, dt = phase_acc(freq, n, sr, phase0)
    return 2.0 * ph - 1.0 - _polyblep(ph, dt)


def square(freq, n, sr=SR, phase0=0.0, pw=0.5):
    """Band-limited (PolyBLEP) pulse/square wave with pulse width pw."""
    ph, dt = phase_acc(freq, n, sr, phase0)
    out = np.where(ph < pw, 1.0, -1.0)
    out += _polyblep(ph, dt)
    out -= _polyblep((ph - pw) % 1.0, dt)
    return out


def triangle(freq, n, sr=SR, phase0=0.0):
    """Band-limited triangle via a leaky-integrated PolyBLEP square."""
    sq = square(freq, n, sr, phase0)
    f = float(np.mean(freq)) if np.ndim(freq) else float(freq)
    leak = 1.0 - 2.0 * np.pi * 2.0 / sr
    tri = signal.lfilter([4.0 * f / sr], [1.0, -leak], sq)
    return tri / max(EPS, np.max(np.abs(tri))) if len(tri) else tri


def sine(freq, n, sr=SR, phase0=0.0):
    ph, _ = phase_acc(freq, n, sr, phase0)
    return np.sin(TWO_PI * ph)


def fm_op(freq, n, ratio=1.0, index=1.0, sr=SR, mod_env=None, feedback=0.0, phase0=0.0):
    """Two-operator FM: sin(2pi fc t + I(t) sin(2pi fc*ratio t)). index may be an array
    (time-varying brightness). feedback adds a little self-modulation on the modulator."""
    phm, _ = phase_acc(np.asarray(freq) * ratio if np.ndim(freq) else freq * ratio, n, sr)
    mod = np.sin(TWO_PI * phm)
    if feedback:
        mod = np.sin(TWO_PI * phm + feedback * mod)
    idx = np.asarray(index, dtype=np.float64)
    if mod_env is not None:
        idx = idx * mod_env
    phc, _ = phase_acc(freq, n, sr, phase0)
    return np.sin(TWO_PI * phc + idx * mod)


def pulse_train(freq, n, sr=SR, jitter=0.0, rng=None, harmonics=None):
    """Band-limited glottal-ish pulse train (sum of harmonics up to Nyquist with 1/k^1.0 rolloff).
    freq may vary; jitter adds random period perturbation."""
    f = np.full(n, float(freq)) if np.ndim(freq) == 0 else np.asarray(freq, dtype=np.float64)[:n]
    if jitter and rng is not None:
        f = f * (1.0 + jitter * smooth_noise(n, 30.0, rng))
    ph, _ = phase_acc(f, n, sr)
    fmax = float(np.max(f)) if n else 100.0
    kmax = harmonics or max(1, int(0.45 * sr / max(fmax, 1.0)))
    kmax = min(kmax, 60)
    out = np.zeros(n)
    for k in range(1, kmax + 1):
        amp = 1.0 / k
        # fade harmonics approaching Nyquist (for time-varying f)
        lim = np.clip((0.45 * sr - k * f) / (0.05 * sr), 0.0, 1.0)
        out += amp * lim * np.sin(TWO_PI * k * ph)
    return out


# ============================================================================ noise
def white(n, rng):
    return rng.standard_normal(n)


_PINK_B = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
_PINK_A = [1.0, -2.494956002, 2.017265875, -0.522189400]


def pink(n, rng):
    """-3 dB/oct noise (Kellet 3-pole IIR), unit RMS."""
    x = signal.lfilter(_PINK_B, _PINK_A, rng.standard_normal(n + 2048))[2048:]
    return x / max(EPS, np.std(x))


def brown(n, rng, sr=SR):
    """-6 dB/oct noise (leaky integrator + 18 Hz HP to remove drift), unit RMS."""
    x = signal.lfilter([1.0], [1.0, -0.997], rng.standard_normal(n + 4096))
    x = sos(x, "highpass", 18.0, order=2, sr=sr)[4096:]
    return x / max(EPS, np.std(x))


def velvet(n, density, rng, sr=SR):
    """Velvet noise: sparse +-1 impulses, `density` per second (great for smooth reverbs)."""
    out = np.zeros(n)
    if n == 0:
        return out
    td = sr / max(density, 1.0)
    m = int(n / td) + 1
    pos = (np.arange(m) * td + rng.uniform(0, td, m)).astype(np.int64)
    pos = pos[pos < n]
    out[pos] = rng.choice([-1.0, 1.0], len(pos))
    return out


def poisson_times(rate, dur, rng, t0=0.0):
    """Event times of a Poisson process (rate per second may be a callable of t)."""
    if callable(rate):
        rmax = max(rate(t) for t in np.linspace(t0, t0 + dur, 64)) + 1e-9
        k = rng.poisson(rmax * dur)
        ts = np.sort(rng.uniform(t0, t0 + dur, k))
        keep = rng.uniform(0, rmax, k) < np.array([rate(t) for t in ts])
        return ts[keep]
    k = rng.poisson(max(rate, 0.0) * dur)
    return np.sort(rng.uniform(t0, t0 + dur, k))


def crackle(n, rate, rng, sr=SR, amp_spread=1.0, polarity=True):
    """Sparse random impulses (Poisson, `rate` per second) with log-normal amplitudes."""
    out = np.zeros(n)
    ts = poisson_times(rate, n / sr, rng)
    idx = (ts * sr).astype(np.int64)
    idx = idx[idx < n]
    amps = np.exp(rng.normal(0.0, amp_spread, len(idx)))
    amps /= max(EPS, np.max(amps)) if len(amps) else 1.0
    if polarity:
        amps *= rng.choice([-1.0, 1.0], len(idx))
    np.add.at(out, idx, amps)
    return out


def smooth_noise(n, rate_hz, rng, sr=SR):
    """Band-limited random signal (-1..1-ish) varying at about rate_hz (cubic-ish interp)."""
    if n == 0:
        return np.zeros(0)
    k = max(4, int(n / sr * rate_hz) + 4)
    pts = rng.uniform(-1.0, 1.0, k)
    xs = np.linspace(0, n - 1, k)
    out = np.interp(np.arange(n), xs, pts)
    # one extra smoothing pass to round corners
    fc = max(0.5, rate_hz)
    return onepole_lp(out, fc, sr) * 1.3


# ============================================================================ envelopes
def exp_env(n, t60, sr=SR):
    """Amplitude decaying by 60 dB over t60 seconds (floored at -600 dB: no subnormals)."""
    return np.power(10.0, np.maximum(-3.0 * t_axis(n, sr) / max(t60, 1e-4), -30.0))


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2, gate=None, sr=SR, curve=3.0):
    """ADSR over n samples; gate (s) = note-on length, release follows. Exponential d/r."""
    gate = (n / sr - r) if gate is None else gate
    t = t_axis(n, sr)
    env = np.zeros(n)
    a = max(a, 1e-4)
    att = t < a
    env[att] = (t[att] / a) ** 0.9
    dec = (t >= a) & (t < gate)
    env[dec] = s + (1.0 - s) * np.exp(-curve * (t[dec] - a) / max(d, 1e-4))
    # level at gate (to start release from)
    if gate <= a:
        lg = (gate / a) ** 0.9 if gate > 0 else 0.0
    else:
        lg = s + (1.0 - s) * math.exp(-curve * (gate - a) / max(d, 1e-4))
    rel = t >= gate
    env[rel] = lg * np.exp(-curve * 2.3 * (t[rel] - gate) / max(r, 1e-4))
    return env


def ar_env(n, attack, release, sr=SR, hold=0.0, curve=1.0):
    """Attack (linear^curve) -> hold -> exponential release to -60 dB at release seconds."""
    t = t_axis(n, sr)
    env = np.ones(n)
    a = max(attack, 1e-4)
    m = t < a
    env[m] = (t[m] / a) ** curve
    m = t > a + hold
    env[m] = np.power(10.0, np.maximum(-3.0 * (t[m] - a - hold) / max(release, 1e-4), -30.0))
    return env


def env_bp(points, n, sr=SR):
    """Piecewise-linear envelope from [(t, value), ...] (seconds); holds the end values."""
    pts = sorted(points)
    ts = np.array([p[0] for p in pts], dtype=np.float64) * sr
    vs = np.array([p[1] for p in pts], dtype=np.float64)
    return np.interp(np.arange(n, dtype=np.float64), ts, vs)


def env_bp_db(points, n, sr=SR):
    """Breakpoints in dB, interpolated in dB, returned as linear gain (-inf allowed as <= -120)."""
    e = env_bp([(t, max(v, -120.0)) for t, v in points], n, sr)
    g = db2lin(e)
    g[e <= -119.9] = 0.0
    return g


def smoothstep_env(n, t0, t1, v0, v1, sr=SR):
    t = t_axis(n, sr)
    k = np.clip((t - t0) / max(t1 - t0, 1e-6), 0.0, 1.0)
    k = k * k * (3 - 2 * k)
    return v0 + (v1 - v0) * k


def follow_ar(x, attack, release, rate):
    """Asymmetric one-pole smoother (attack when rising, release when falling) at `rate` Hz.
    Python loop - use on control-rate signals only."""
    a_up = math.exp(-1.0 / max(attack * rate, 1e-9))
    a_dn = math.exp(-1.0 / max(release * rate, 1e-9))
    out = np.empty(len(x))
    y = float(x[0]) if len(x) else 0.0
    for i, v in enumerate(np.asarray(x, dtype=np.float64)):
        a = a_up if v > y else a_dn
        y = a * y + (1.0 - a) * v
        out[i] = y
    return out


# ============================================================================ filters
def _clamp_f(f, sr):
    return float(min(max(f, 5.0), 0.49 * sr))


def biquad_coeffs(kind, f0, q=0.7071, gain_db=0.0, sr=SR):
    """RBJ Audio-EQ-Cookbook biquad. kind: lowpass highpass bandpass notch allpass peak lowshelf
    highshelf. Returns (b, a) normalised by a0."""
    f0 = _clamp_f(f0, sr)
    w0 = TWO_PI * f0 / sr
    cw, sw = math.cos(w0), math.sin(w0)
    q = max(q, 1e-3)
    alpha = sw / (2.0 * q)
    A = 10.0 ** (gain_db / 40.0)
    if kind == "lowpass":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "highpass":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "bandpass":           # constant 0 dB peak gain
        b = [alpha, 0.0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "notch":
        b = [1.0, -2 * cw, 1.0]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "allpass":
        b = [1 - alpha, -2 * cw, 1 + alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "peak":
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind == "lowshelf":
        sa = 2 * math.sqrt(A) * alpha
        b = [A * ((A + 1) - (A - 1) * cw + sa), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sa)]
        a = [(A + 1) + (A - 1) * cw + sa, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sa]
    elif kind == "highshelf":
        sa = 2 * math.sqrt(A) * alpha
        b = [A * ((A + 1) + (A - 1) * cw + sa), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sa)]
        a = [(A + 1) - (A - 1) * cw + sa, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sa]
    else:
        raise ValueError(kind)
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return b, a


def biquad(x, kind, f0, q=0.7071, gain_db=0.0, sr=SR):
    b, a = biquad_coeffs(kind, f0, q, gain_db, sr)
    return signal.lfilter(b, a, np.asarray(x) + DENORMAL_GUARD, axis=0)


def biquad_chain(x, stages, sr=SR):
    """stages: [(kind, f0, q, gain_db), ...]"""
    for st in stages:
        x = biquad(x, *st, sr=sr) if len(st) > 2 else biquad(x, st[0], st[1], sr=sr)
    return x


@functools.lru_cache(maxsize=256)
def _butter_sos(kind, f, order, sr):
    if isinstance(f, tuple):
        wn = [_clamp_f(v, sr) for v in f]
    else:
        wn = _clamp_f(f, sr)
    return signal.butter(order, wn, btype=kind, fs=sr, output="sos")


def sos(x, kind, f, order=2, sr=SR, zero_phase=False):
    """Butterworth via SOS. kind: lowpass highpass bandpass bandstop; f scalar or (lo, hi)."""
    s = _butter_sos(kind, tuple(f) if isinstance(f, (list, tuple)) else float(f), int(order), int(sr))
    x = np.asarray(x) + DENORMAL_GUARD
    if zero_phase:
        return signal.sosfiltfilt(s, x, axis=0)
    return signal.sosfilt(s, x, axis=0)


def bandpass(x, lo, hi, order=2, sr=SR):
    return sos(x, "bandpass", (lo, hi), order, sr)


def onepole_lp(x, fc, sr=SR):
    a = math.exp(-TWO_PI * max(fc, 1e-3) / sr)
    return signal.lfilter([1.0 - a], [1.0, -a], np.asarray(x) + DENORMAL_GUARD, axis=0)


def onepole_hp(x, fc, sr=SR):
    return x - onepole_lp(x, fc, sr)


def tv_biquad(x, kind, f0, q=0.7071, gain_db=0.0, sr=SR, block=128):
    """Time-varying RBJ biquad: f0 (and q) may be arrays (per sample) or callables of time (s).
    Coefficients update every `block` samples; filter state is carried across blocks."""
    x = np.asarray(x, dtype=np.float64) + DENORMAL_GUARD
    n = len(x)
    if n == 0:
        return x.copy()
    nb = (n + block - 1) // block
    centers = (np.arange(nb) * block + block / 2.0) / sr

    def per_block(v):
        if callable(v):
            return np.array([v(t) for t in centers], dtype=np.float64)
        if np.ndim(v) == 0:
            return np.full(nb, float(v))
        v = np.asarray(v, dtype=np.float64)
        idx = np.minimum((np.arange(nb) * block + block // 2), len(v) - 1)
        return v[idx]

    fb, qb, gb = per_block(f0), per_block(q), per_block(gain_db)
    out = np.empty_like(x)
    zi = np.zeros((2,) + x.shape[1:])
    for i in range(nb):
        s = slice(i * block, min(n, (i + 1) * block))
        b, a = biquad_coeffs(kind, fb[i], qb[i], gb[i], sr)
        out[s], zi = signal.lfilter(b, a, x[s], axis=0, zi=zi)
    return out


def tv_lowpass(x, f0, q=0.7071, sr=SR, block=128):
    return tv_biquad(x, "lowpass", f0, q, 0.0, sr, block)


def tv_bandpass(x, f0, q=1.0, sr=SR, block=128):
    return tv_biquad(x, "bandpass", f0, q, 0.0, sr, block)


def resonator_bank(x, freqs, qs, gains, sr=SR):
    """Parallel constant-peak band-pass resonators (modal filtering of an excitation)."""
    out = np.zeros_like(np.asarray(x, dtype=np.float64))
    for f, q, g in zip(freqs, np.broadcast_to(qs, len(freqs)), np.broadcast_to(gains, len(freqs))):
        if f < 0.48 * sr:
            out += g * biquad(x, "bandpass", f, q, sr=sr)
    return out


# ============================================================================ physical models
def karplus_strong(f0, dur, sr=SR, excitation=None, t60=2.0, brightness=0.5, rng=None,
                   pluck_pos=None):
    """Karplus-Strong plucked string, vectorised one period at a time.
    Loop: y[n] = x[n] + g * sum_k h_k y[n - N - k], h = [1-s, s] * linear fractional delay.
    t60: decay time (s) of the fundamental. brightness s in (0, 1): 0.5 = classic averaging,
    lower = brighter. pluck_pos (0..0.5) adds a comb (pick position) to the excitation."""
    n = n_of(dur, sr)
    P = sr / float(f0)
    s = float(np.clip(brightness, 0.02, 0.98))
    N = int(math.floor(P - s))
    N = max(N, 2)
    frac = (P - s) - N
    h = np.convolve([1.0 - s, s], [1.0 - frac, frac])          # taps at N, N+1, N+2
    g = 10.0 ** (-3.0 / (max(t60, 1e-3) * f0))
    if excitation is None:
        rng = rng or np.random.default_rng(0)
        excitation = rng.uniform(-1.0, 1.0, N)
        excitation -= excitation.mean()
    exc = np.zeros(n)
    k = min(len(excitation), n)
    exc[:k] = excitation[:k]
    if pluck_pos:
        d = max(1, int(round(pluck_pos * P)))
        exc[d:] -= exc[:-d].copy()
    hist = N + 2
    y = np.zeros(n + hist)
    for start in range(0, n, N):
        end = min(start + N, n)
        a, b = hist + start, hist + end
        y[a:b] = exc[start:end] + g * (h[0] * y[a - N:b - N] + h[1] * y[a - N - 1:b - N - 1] + h[2] * y[a - N - 2:b - N - 2])
    return y[hist:]


def modal(freqs, t60s, amps, n, sr=SR, phases=None, attack=0.0005):
    """Sum of exponentially decaying sinusoids (struck-object modal synthesis)."""
    t = t_axis(n, sr)
    out = np.zeros(n)
    phases = np.zeros(len(freqs)) if phases is None else phases
    for f, t60, a, ph in zip(freqs, t60s, amps, phases):
        if f >= 0.48 * sr or a == 0:
            continue
        m = min(n, n_of(t60 * 1.2, sr) + 1)
        out[:m] += a * np.sin(TWO_PI * f * t[:m] + ph) * np.power(10.0, -3.0 * t[:m] / t60)
    if attack > 0:
        k = min(n, n_of(attack, sr))
        if k > 1:
            out[:k] *= np.linspace(0, 1, k)
    return out


def friction(n, rate_hz, rng, sr=SR, jitter=0.15, body=None):
    """Stick-slip friction (creaks, squeaks): an irregular impulse train whose rate follows
    rate_hz (scalar or per-sample array), optionally filtered by a resonant body
    [(f, q, gain), ...]."""
    r = np.full(n, float(rate_hz)) if np.ndim(rate_hz) == 0 else np.asarray(rate_hz, dtype=np.float64)[:n]
    r = r * (1.0 + jitter * smooth_noise(n, 25.0, rng, sr))
    r = np.maximum(r, 0.5)
    ph = np.cumsum(r / sr)
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0] + 1
    out = np.zeros(n)
    amps = np.exp(rng.normal(0.0, 0.5, len(idx)))
    out[idx] = amps
    # each slip is a short smooth asymmetric pulse (~0.4 ms), not a broadband spike
    k = max(3, int(0.0004 * sr))
    pulse = np.hanning(2 * k + 1)[:k + 3]
    pulse = pulse - 0.6 * np.concatenate([[0.0], pulse[:-1]])
    out = np.convolve(out, pulse)[:n]
    if body:
        out = resonator_bank(out, [b[0] for b in body], [b[1] for b in body], [b[2] for b in body], sr)
    return out


# ============================================================================ space
_IR_SPECS = {
    # t60 mid (s), low mult, high mult, predelay (s), ER count, ER span (s), ER gain, density/s,
    # brightness LP (Hz), length (s), flutter (s period of parallel-wall echoes, 0=none)
    "small_room": dict(t60=0.38, lo=1.1, hi=0.55, pre=0.002, er=10, er_span=0.022, er_g=0.55, lp=7000, flutter=0.0),
    "office":     dict(t60=0.55, lo=1.15, hi=0.45, pre=0.004, er=12, er_span=0.035, er_g=0.45, lp=5200, flutter=0.0),
    "hall":       dict(t60=2.7, lo=1.25, hi=0.5, pre=0.024, er=14, er_span=0.09, er_g=0.30, lp=6500, flutter=0.0),
    "cell":       dict(t60=1.15, lo=1.0, hi=0.85, pre=0.003, er=16, er_span=0.05, er_g=0.6, lp=9000, flutter=0.0105),
    "alley":      dict(t60=1.5, lo=0.9, hi=0.4, pre=0.009, er=10, er_span=0.16, er_g=0.5, lp=5000, flutter=0.031),
    "plate":      dict(t60=2.1, lo=0.8, hi=0.85, pre=0.0, er=0, er_span=0.0, er_g=0.0, lp=11000, flutter=0.0),
    "car":        dict(t60=0.11, lo=1.0, hi=0.5, pre=0.001, er=6, er_span=0.006, er_g=0.5, lp=6000, flutter=0.0),
    "court":      dict(t60=1.7, lo=1.2, hi=0.55, pre=0.016, er=14, er_span=0.07, er_g=0.35, lp=6000, flutter=0.0),
    "street":     dict(t60=0.9, lo=0.9, hi=0.45, pre=0.012, er=7, er_span=0.28, er_g=0.35, lp=5500, flutter=0.0),
}
IR_KINDS = tuple(_IR_SPECS)


@functools.lru_cache(maxsize=32)
def make_ir(kind, sr=SR, seed=0):
    """Synthesised stereo impulse response (unit energy per channel), float64 (m, 2).

    Late tail: decorrelated noise split into low / mid / high bands, each with its own decay
    (frequency-dependent T60); early reflections: sparse taps (plus flutter echoes for parallel
    walls: cell, alley), low-passed; a pre-delay; a 2 ms onset ramp."""
    sp = _IR_SPECS[kind]
    rng = np.random.default_rng(stable_seed("ir", kind, seed))
    t60 = sp["t60"]
    length = min(6.0, t60 * 1.25 + sp["pre"] + 0.05)
    n = n_of(length, sr)
    t = t_axis(n, sr)
    ir = np.zeros((n, 2))
    for ch in range(2):
        nz = rng.standard_normal(n)
        lo = sos(nz, "lowpass", 400.0, 2, sr)
        hi = sos(nz, "highpass", 3200.0, 2, sr)
        mid = nz - lo - hi
        tail = (lo * np.power(10.0, -3.0 * t / (t60 * sp["lo"]))
                + mid * np.power(10.0, -3.0 * t / t60)
                + hi * np.power(10.0, -3.0 * t / (t60 * sp["hi"])))
        # tail builds up over the first ~ 1/6 of t60 (diffusion), starting after the ER span
        build = 1.0 - np.exp(-t / max(0.004, 0.06 * t60))
        tail *= build
        tail = onepole_lp(tail, sp["lp"], sr)
        er = np.zeros(n)
        if sp["er"]:
            times = np.sort(rng.uniform(0.0015, sp["er_span"], sp["er"]))
            gains = sp["er_g"] * rng.uniform(0.4, 1.0, sp["er"]) * np.exp(-times / max(sp["er_span"], 1e-3))
            gains *= rng.choice([-1.0, 1.0], sp["er"])
            for tt, gg in zip(times, gains):
                i = n_of(tt, sr)
                if i < n:
                    er[i] += gg
        if sp["flutter"]:
            per = sp["flutter"] * (1.0 + 0.02 * (ch - 0.5))
            k = 1
            while k * per < t60 * 0.6:
                i = n_of(k * per, sr)
                if i < n:
                    er[i] += 0.5 * sp["er_g"] * math.pow(10.0, -3.0 * k * per / (t60 * 0.55)) * (1 if k % 2 else -1)
                k += 1
        er = onepole_lp(er, sp["lp"] * 0.8, sr)
        # scale tail so that its energy relates sensibly to the early reflections
        tail /= max(EPS, np.sqrt(np.sum(tail ** 2)))
        e_er = np.sqrt(np.sum(er ** 2))
        if e_er > 0:
            er /= e_er
            er *= 0.55
        ch_ir = tail + er
        pre = n_of(sp["pre"], sr)
        ch_ir = np.concatenate([np.zeros(pre), ch_ir])[:n]
        ramp = min(n, n_of(0.002, sr))
        ch_ir[:ramp] *= np.linspace(0, 1, ramp)
        ch_ir = fade(ch_ir, 0.0, min(0.25, length * 0.2), sr)
        ir[:, ch] = ch_ir / max(EPS, np.sqrt(np.sum(ch_ir ** 2)))
    return ir


def convolve(x, ir):
    """FFT convolution (overlap-add for long inputs). Mono x with stereo ir -> stereo."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    if ir.ndim == 1:
        ir = ir[:, None]
    if len(x) > 8 * len(ir) and len(x) > 200000:
        return signal.oaconvolve(x, ir, axes=0)
    return signal.fftconvolve(x, ir, axes=0)


def reverb(x, kind="small_room", wet_db=-12.0, dry=1.0, seed=0, sr=SR, keep_len=False, tail=True):
    """Dry + convolution wet. Output is lengthened by the IR tail unless keep_len."""
    x = np.asarray(x, dtype=np.float64)
    ir = make_ir(kind, sr, seed)
    xs = x if x.ndim == 2 else x[:, None]
    src = xs.mean(axis=1) if xs.shape[1] == 2 else xs[:, 0]
    wet = convolve(src, ir) * db2lin(wet_db)
    n = len(x) if keep_len or not tail else len(wet)
    out = np.zeros((n, 2))
    out[:len(x)] += to_stereo(x)[:n] * dry
    out += wet[:n]
    return out


def pan_mono(x, pan):
    """Equal-power pan of a mono signal: pan -1 (L) .. 1 (R). Returns (n, 2)."""
    th = (float(np.clip(pan, -1, 1)) + 1.0) * np.pi / 4.0
    x = np.asarray(x, dtype=np.float64)
    return np.stack([x * math.cos(th), x * math.sin(th)], axis=1)


def pan_stereo(x, pan):
    """Pan a stereo signal: the mid moves with an equal-power law (sqrt2-compensated so pan=0
    is unity), the side narrows as |pan| grows."""
    x = to_stereo(np.asarray(x, dtype=np.float64))
    if abs(pan) < 1e-6:
        return x.copy()
    mid = 0.5 * (x[:, 0] + x[:, 1])
    side = 0.5 * (x[:, 0] - x[:, 1])
    out = pan_mono(mid, pan) * math.sqrt(2.0)
    k = 1.0 - min(1.0, abs(pan))
    out[:, 0] += side * k
    out[:, 1] -= side * k
    return out


def width(x, w=1.0):
    x = to_stereo(np.asarray(x, dtype=np.float64))
    mid = 0.5 * (x[:, 0] + x[:, 1])
    side = 0.5 * (x[:, 0] - x[:, 1]) * w
    return np.stack([mid + side, mid - side], axis=1)


def haas(x, ms=8.0, side=1, sr=SR, mix=0.6):
    """Pseudo-stereo from mono: delayed copy on one side."""
    x = np.asarray(x, dtype=np.float64)
    d = n_of(ms / 1000.0, sr)
    dl = np.concatenate([np.zeros(d), x])[:len(x)]
    a, b = x, x * (1 - mix) + dl * mix
    return np.stack([a, b] if side > 0 else [b, a], axis=1)


def decorrelate(x, rng, sr=SR, amount=0.5):
    """Mono -> stereo via two short random allpass/velvet diffusers (keeps the timbre)."""
    x = np.asarray(x, dtype=np.float64)
    outs = []
    for ch in range(2):
        k = n_of(0.012, sr)
        v = velvet(k, 2500, rng, sr) * np.exp(-np.arange(k) / (0.004 * sr))
        v[0] = 1.0
        v /= np.sqrt(np.sum(v ** 2))
        y = signal.fftconvolve(x, v)[:len(x)]
        outs.append((1 - amount) * x + amount * y)
    return np.stack(outs, axis=1)


# ============================================================================ dynamics
def saturate(x, drive=1.0, kind="tanh", asym=0.0):
    """Soft saturation, roughly level-preserving for small signals."""
    x = np.asarray(x, dtype=np.float64)
    if kind == "tanh":
        y = np.tanh(drive * (x + asym)) - np.tanh(drive * asym)
        return y / max(drive, EPS) if drive < 1 else y / np.tanh(drive) if drive > 0 else y
    if kind == "soft":       # cubic soft clip
        z = np.clip(drive * x, -1.5, 1.5)
        return (z - (4.0 / 27.0) * z ** 3) / max(drive, EPS)
    if kind == "fold":
        return np.sin(drive * x) / max(drive, EPS)
    raise ValueError(kind)


def _block_levels(x, block, mode="peak", rms_ms=15.0, sr=SR):
    if mode == "rms":
        # sliding RMS over rms_ms (stereo: mean power of the channels), sampled per block,
        # sine-calibrated to peak (x sqrt 2)
        p = np.square(x) if x.ndim == 1 else np.mean(np.square(x), axis=1)
        w = max(1, int(rms_ms / 1000.0 * sr))
        c = np.concatenate([[0.0], np.cumsum(p)])
        n = len(p)
        nb = (n + block - 1) // block
        ends = np.minimum(np.arange(nb) * block + block, n)
        starts = np.maximum(ends - w, 0)
        return np.sqrt(np.maximum(c[ends] - c[starts], 0) / np.maximum(ends - starts, 1) * 2.0)
    xs = np.abs(x) if x.ndim == 1 else np.max(np.abs(x), axis=1)
    n = len(xs)
    nb = (n + block - 1) // block
    pad = nb * block - n
    if pad:
        xs = np.concatenate([xs, np.zeros(pad)])
    xs = xs.reshape(nb, block)
    return xs.max(axis=1)


def _expand_blocks(gb, n, block):
    """Block values (at block centres) -> per-sample, linear interpolation."""
    centers = np.arange(len(gb)) * block + block / 2.0
    return np.interp(np.arange(n, dtype=np.float64), centers, gb)


def compressor(x, thresh_db=-18.0, ratio=2.0, attack_ms=20.0, release_ms=250.0, knee_db=6.0,
               makeup_db=0.0, sidechain=None, block=32, sr=SR, mode="rms", return_gain=False):
    """Feed-forward stereo-linked compressor (block-rate detector, smooth gain in dB)."""
    x = np.asarray(x, dtype=np.float64)
    key = x if sidechain is None else np.asarray(sidechain, dtype=np.float64)
    lv = lin2db(_block_levels(key, block, mode))
    over = lv - thresh_db
    gr = np.zeros_like(over)
    hk = knee_db / 2.0
    m = over > hk
    gr[m] = -over[m] * (1.0 - 1.0 / ratio)
    m = (over > -hk) & (over <= hk)
    if knee_db > 0:
        gr[m] = -(1.0 - 1.0 / ratio) * (over[m] + hk) ** 2 / (2.0 * knee_db)
    rate = sr / block
    # gain smoothing: attack = gain going down
    a_att = math.exp(-1.0 / max(attack_ms / 1000.0 * rate, 1e-9))
    a_rel = math.exp(-1.0 / max(release_ms / 1000.0 * rate, 1e-9))
    g = np.empty_like(gr)
    y = 0.0
    for i, v in enumerate(gr):
        a = a_att if v < y else a_rel
        y = a * y + (1.0 - a) * v
        g[i] = y
    gain = db2lin(_expand_blocks(g, len(x), block) + makeup_db)
    out = x * (gain[:, None] if x.ndim == 2 else gain)
    return (out, gain) if return_gain else out


def duck_gain(activity, depth_db, attack, release, rate):
    """Gain curve (linear) from a 0..1 activity signal sampled at `rate` Hz."""
    sm = follow_ar(np.clip(activity, 0, 1), attack, release, rate)
    return db2lin(depth_db * sm)


def sidechain_duck(x, key, depth_db=-9.0, thresh_db=-40.0, attack=0.03, release=0.25, sr=SR, block=48):
    """Duck x by depth_db whenever the key signal is above thresh_db (envelope follower)."""
    lv = lin2db(_block_levels(key, block, "rms"))
    act = np.clip((lv - thresh_db) / 6.0, 0.0, 1.0)
    g = duck_gain(act, depth_db, attack, release, sr / block)
    gain = _expand_blocks(g, len(x), block)
    return x * (gain[:, None] if np.ndim(x) == 2 else gain)


def _forward_min(v, L):
    """m[i] = min(v[i : i+L]) (window clipped at the end)."""
    if L <= 1:
        return v.copy()
    padded = np.concatenate([v, np.full(L - 1, v[-1] if len(v) else 1.0)])
    # minimum_filter1d window for output j covers j - L//2 .. j - L//2 + L - 1 (origin 0)
    m = minimum_filter1d(padded, size=L, mode="nearest", origin=-(L // 2) if L % 2 else -(L // 2) + 0)
    return m[:len(v)]


def _backward_mean(v, L):
    """s[i] = mean(v[i-L+1 : i+1]) with the window clipped at the start."""
    c = np.concatenate([[0.0], np.cumsum(v, dtype=np.float64)])
    i = np.arange(len(v))
    lo = np.maximum(0, i - L + 1)
    return (c[i + 1] - c[lo]) / (i + 1 - lo)


def tp_envelope(x, oversample=4, chunk=1 << 19):
    """Per-sample true-peak envelope: max |x| over the 4x-oversampled sub-samples of each
    sample interval, max over channels. Chunked to bound memory."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    n = len(x)
    env = np.zeros(n)
    pad = 64
    for s in range(0, n, chunk):
        a, b = max(0, s - pad), min(n, s + chunk + pad)
        up = signal.resample_poly(x[a:b], oversample, 1, axis=0)
        up = np.max(np.abs(up), axis=1)
        k = (b - a)
        up = up[:k * oversample].reshape(k, oversample).max(axis=1)
        env[s:min(n, s + chunk)] = up[s - a:s - a + min(chunk, n - s)]
    return np.maximum(env, np.max(np.abs(x), axis=1))


def limiter(x, ceiling_db=-1.0, lookahead_ms=2.5, release_ms=90.0, sr=SR, true_peak=True,
            block=16, return_gain=False):
    """Look-ahead brick-wall limiter (no added latency).

    req[i] = min(1, ceiling / peak[i]) with peak from the 4x-oversampled envelope (true peak);
    m = forward running minimum over the look-ahead window L; release smoothing at block rate
    (gain only rises slowly, never above m); finally a backward moving average over L, which
    guarantees gain[i] <= req[i] at every peak while starting the reduction L samples early."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    pk = tp_envelope(x) if true_peak else (np.max(np.abs(x), axis=1) if x.ndim == 2 else np.abs(x))
    ceil = db2lin(ceiling_db)
    req = np.minimum(1.0, ceil / np.maximum(pk, EPS))
    L = max(2, n_of(lookahead_ms / 1000.0, sr))
    m = _forward_min(req, L)
    nb = (n + block - 1) // block
    padn = nb * block - n
    mb = np.concatenate([m, np.ones(padn)]).reshape(nb, block).min(axis=1)
    a_rel = math.exp(-1.0 / max(release_ms / 1000.0 * sr / block, 1e-9))
    gb = np.empty(nb)
    y = 1.0
    for i, v in enumerate(mb):
        y = v if v < y else a_rel * y + (1.0 - a_rel) * v
        gb[i] = y
    g = np.repeat(gb, block)[:n]
    g = _backward_mean(g, L)
    out = x * (g[:, None] if x.ndim == 2 else g)
    return (out, g) if return_gain else out


# ============================================================================ metering
@functools.lru_cache(maxsize=8)
def k_weighting_coeffs(sr=SR):
    """ITU-R BS.1770-4 K-weighting (pre-filter shelf + RLB high-pass) for any sample rate."""
    f0 = 1681.974450955533
    G = 3.999843853973347
    Q = 0.7071752369554196
    K = math.tan(math.pi * f0 / sr)
    Vh = 10.0 ** (G / 20.0)
    Vb = Vh ** 0.4996667741545416
    a0 = 1.0 + K / Q + K * K
    b1 = np.array([(Vh + Vb * K / Q + K * K) / a0, 2.0 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0])
    a1 = np.array([1.0, 2.0 * (K * K - 1.0) / a0, (1.0 - K / Q + K * K) / a0])
    f0 = 38.13547087602444
    Q = 0.5003270373238773
    K = math.tan(math.pi * f0 / sr)
    d = 1.0 + K / Q + K * K
    b2 = np.array([1.0, -2.0, 1.0])
    a2 = np.array([1.0, 2.0 * (K * K - 1.0) / d, (1.0 - K / Q + K * K) / d])
    return b1, a1, b2, a2


def k_weight(x, sr=SR):
    b1, a1, b2, a2 = k_weighting_coeffs(sr)
    y = signal.lfilter(b1, a1, np.asarray(x, dtype=np.float64), axis=0)
    return signal.lfilter(b2, a2, y, axis=0)


def _block_ms(x, sr, win, hop):
    """Mean square of K-weighted x per channel over windows (win, hop in s) -> (nb, ch)."""
    y = k_weight(x, sr)
    if y.ndim == 1:
        y = y[:, None]
    W = n_of(win, sr)
    H = n_of(hop, sr)
    n = len(y)
    if n < W:
        return np.zeros((0, y.shape[1]))
    c = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(y * y, axis=0)])
    starts = np.arange(0, n - W + 1, H)
    return (c[starts + W] - c[starts]) / W


def loudness_integrated(x, sr=SR):
    """BS.1770-4 integrated loudness (LUFS), 400 ms blocks, 75 % overlap, -70 LUFS absolute
    and -10 LU relative gates. Channel weights 1.0 (L/R)."""
    z = _block_ms(x, sr, 0.4, 0.1)
    if len(z) == 0:
        return -np.inf
    p = z.sum(axis=1)
    lk = -0.691 + 10.0 * np.log10(np.maximum(p, EPS))
    g1 = lk > -70.0
    if not g1.any():
        return -np.inf
    gamma_r = -0.691 + 10.0 * np.log10(np.mean(p[g1])) - 10.0
    g2 = g1 & (lk > gamma_r)
    return float(-0.691 + 10.0 * np.log10(np.mean(p[g2])))


def loudness_curve(x, sr=SR, win=3.0, hop=0.1):
    """Ungated loudness per window (short-term: win=3, momentary: win=0.4). Returns (t, LUFS)
    with t = window centre."""
    z = _block_ms(x, sr, win, hop)
    lk = -0.691 + 10.0 * np.log10(np.maximum(z.sum(axis=1), EPS))
    t = np.arange(len(lk)) * hop + win / 2.0
    return t, lk


def true_peak_db(x, oversample=4):
    """4x-oversampled true-peak estimate in dBTP (BS.1770-4 Annex 2 style)."""
    return float(lin2db(np.max(tp_envelope(x, oversample)))) if len(x) else -np.inf


def sample_peak_db(x):
    return float(lin2db(np.max(np.abs(x)))) if len(x) else -np.inf


def rms_db(x):
    return float(lin2db(np.sqrt(np.mean(np.square(x))))) if len(x) else -np.inf


# ============================================================================ resampling
def resample(x, sr_in, sr_out=SR):
    if int(sr_in) == int(sr_out):
        return np.asarray(x, dtype=np.float64)
    fr = Fraction(int(sr_out), int(sr_in)).limit_denominator(2000)
    return signal.resample_poly(np.asarray(x, dtype=np.float64), fr.numerator, fr.denominator, axis=0)


def upsample2(x):
    return signal.resample_poly(np.asarray(x, dtype=np.float64), 2, 1, axis=0)


# ============================================================================ WAV I/O
def write_wav(path, x, sr=SR, bits=24):
    """Write a WAV file: bits 16 / 24 (PCM, TPDF dither for 16) or 32 (IEEE float)."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    nch = x.shape[1]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if bits == 32:
        data = x.astype("<f4").tobytes()
        fmt_tag, bps = 3, 32
    elif bits == 24:
        xi = np.clip(np.round(x * 8388607.0), -8388608, 8388607).astype("<i4")
        data = xi.reshape(-1).view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
        fmt_tag, bps = 1, 24
    elif bits == 16:
        rng = np.random.default_rng(16)
        d = (rng.uniform(-0.5, 0.5, x.shape) + rng.uniform(-0.5, 0.5, x.shape))
        xi = np.clip(np.round(x * 32767.0 + d), -32768, 32767).astype("<i2")
        data = xi.tobytes()
        fmt_tag, bps = 1, 16
    else:
        raise ValueError(bits)
    block_align = nch * bps // 8
    with open(path, "wb") as fh:
        if fmt_tag == 3:
            fmt = struct.pack("<HHIIHHH", fmt_tag, nch, sr, sr * block_align, block_align, bps, 0)
            fact = b"fact" + struct.pack("<II", 4, len(x))
        else:
            fmt = struct.pack("<HHIIHH", fmt_tag, nch, sr, sr * block_align, block_align, bps)
            fact = b""
        riff_size = 4 + (8 + len(fmt)) + len(fact) + (8 + len(data)) + (len(data) & 1)
        fh.write(b"RIFF" + struct.pack("<I", riff_size) + b"WAVE")
        fh.write(b"fmt " + struct.pack("<I", len(fmt)) + fmt)
        fh.write(fact)
        fh.write(b"data" + struct.pack("<I", len(data)) + data)
        if len(data) & 1:
            fh.write(b"\x00")
    return path


def read_audio(path, sr_out=None):
    """Read any audio file -> (float64 (n, ch), sr). Tries scipy, soundfile, then ffmpeg."""
    err = []
    try:
        from scipy.io import wavfile
        sr, d = wavfile.read(path)
        if d.dtype.kind == "f":
            x = d.astype(np.float64)
        elif d.dtype == np.uint8:
            x = (d.astype(np.float64) - 128.0) / 128.0
        else:
            x = d.astype(np.float64) / float(np.iinfo(d.dtype).max + 1)
        if x.ndim == 1:
            x = x[:, None]
        if sr_out and sr != sr_out:
            x, sr = resample(x, sr, sr_out), sr_out
        return x, sr
    except Exception as e:  # noqa: BLE001
        err.append(f"scipy: {e}")
    try:
        import soundfile as sf
        x, sr = sf.read(path, dtype="float64", always_2d=True)
        if sr_out and sr != sr_out:
            x, sr = resample(x, sr, sr_out), sr_out
        return x, sr
    except Exception as e:  # noqa: BLE001
        err.append(f"soundfile: {e}")
    try:
        sr = sr_out or SR
        out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-acodec", "pcm_f32le",
                              "-ac", "2", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(out, dtype="<f4").astype(np.float64).reshape(-1, 2)
        return x, sr
    except Exception as e:  # noqa: BLE001
        err.append(f"ffmpeg: {e}")
    raise IOError(f"cannot read {path}: " + " | ".join(err))


# ============================================================================ self-test
def _selftest():
    print("K-weighting @48k:", [np.round(c, 8).tolist() for c in k_weighting_coeffs(48000)])
    t = t_axis(SR * 10)
    for amp_db in (-20.0, -23.0):
        s = db2lin(amp_db) * np.sin(TWO_PI * 997.0 * t)
        st = np.stack([s, s], 1)
        print(f"997 Hz stereo sine at {amp_db} dBFS -> {loudness_integrated(st):.2f} LUFS (expect {amp_db:.2f})")
    # true peak of a sine at fs/4 with 45 deg phase: sample peak -3 dB, true peak 0 dB
    x = np.sin(TWO_PI * 12000.0 * t[:48000] + np.pi / 4)
    print(f"fs/4 sine 45deg: sample peak {sample_peak_db(x):.2f} dB, true peak {true_peak_db(x):.2f} dBTP (expect ~0)")
    rng = np.random.default_rng(1)
    v = rng.uniform(0, 1, 5000)
    for L in (2, 5, 8, 33):
        ref = np.array([v[i:i + L].min() for i in range(len(v))])
        assert np.allclose(_forward_min(v, L), ref), L
    nz = rng.standard_normal((SR * 4, 2)) * 0.5
    y = limiter(nz, -1.0)
    print(f"limiter: in TP {true_peak_db(nz):.2f} -> out TP {true_peak_db(y):.2f} dBTP (ceiling -1)")
    ks = karplus_strong(110.0, 1.0)
    f = np.fft.rfft(ks * np.hanning(len(ks)))
    print(f"KS 110 Hz peak bin -> {np.argmax(np.abs(f)) * SR / len(ks):.1f} Hz")


if __name__ == "__main__":
    _selftest()
