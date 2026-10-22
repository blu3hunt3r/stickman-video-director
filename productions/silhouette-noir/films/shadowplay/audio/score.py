"""SHADOW PLAY score: one Herrmann-ish nocturne in A minor, built on the minor-major seventh
(A C E G#) - the Hitchcock chord - from the first paper window to the last 'Mostly.'

    render_score(sync, N) -> (main float32 (N, 2), hits float32 (N, 2), info)

`main` is the score's body (con sordino strings, harmonics, the pizzicato clock, harp and
celesta spirals, soft brass swells); `hits` carries the designed moments that must land on the
picture and survive the narration (string stabs on the knife blows, muted-brass stabs, the
hour strikes, the trap's hits, the last pizzicato) - mix.py ducks it far less.

Instruments (all synthesised):
  pizzicato ...... Karplus-Strong with a rounded finger excitation, violin / cello / bass body
                   resonances, a finger 'thup'; the clock motif is pizz E5 (tick) / B4 (tock)
  strings ........ detuned saw sections (per-voice drift + delayed vibrato) at 24 kHz, con
                   sordino EQ; tremolo, glissando (pitch-bend callables), divisi clusters
  harmonics ...... flautando string harmonics: near-sine trio with bow noise
  muted brass .... 3-player saw stacks with an attack scoop, brightness that follows the dynamic,
                   stopped-horn (nasal, buzzy) or straight-mute EQ; sfz stabs and slow swells
  harp ........... Karplus-Strong, warm gut tone, long ring
  celesta ........ steel-bar partials (1, 2.76, 4.0, 5.4) with a felt hammer
  hour bell ...... minor-third bell partials over a low A thump and a harp harmonic
  timpani ........ pitched membrane + overtone + stick noise; rolls
  string stab .... sfx_shadowplay 'string_stab' (the shrill Psycho-echo blow, our own)

Every hit is placed on a sync point from cuesheet.sync_points (narration word anchors /
storyboard beats), so the score and the SFX follow the picture together.
"""
from __future__ import annotations

import functools
import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

from audio import dsp  # noqa: E402
from audio.dsp import (SR, TWO_PI, db2lin, exp_env, karplus_strong, n_of, onepole_lp, saturate, saw, sos,  # noqa: E402
                       t_axis, tv_lowpass)
from films.shadowplay.audio import sfx_shadowplay as SP  # noqa: E402

SR2 = 24000
_NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
         "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

# the harmony (voicings, low to high)
AMM7 = "A2 E3 A3 C4 E4 G#4"            # A minor-major 7: the Hitchcock chord
FMA7S11 = "F2 C3 A3 E4 B4"             # F maj7 #11
DM9 = "D2 A2 F3 C4 E4"
E7B9 = "E2 B2 G#3 D4 F4"
BB = "Bb1 F2 D3 F3 Bb3"
TICK, TOCK = "E5", "B4"


def m(name):
    return 12 * (int(name[-1]) + 1) + _NOTE[name[:-1]]


def ms(names):
    return [m(x) for x in names.split()] if isinstance(names, str) else list(names)


def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def _norm(x, peak=1.0):
    p = float(np.max(np.abs(x))) if len(x) else 0.0
    return x if p < 1e-12 else x * (peak / p)


def _pan(x, pan):
    th = (float(np.clip(pan, -1, 1)) + 1.0) * math.pi / 4.0
    return np.stack([x * math.cos(th), x * math.sin(th)], axis=1) * math.sqrt(2.0)


# ============================================================================ instruments (48 kHz)
@functools.lru_cache(maxsize=512)
def pizz(midi, vel, var=0, pan=None):
    """Orchestral pizzicato: KS string with a rounded finger excitation, body resonances by
    register (violin / cello / bass), a finger 'thup'. float32 stereo."""
    f0 = hz(midi)
    rng = np.random.default_rng(1009 * midi + 17 * var)
    t60 = float(np.clip(0.75 * (330.0 / f0) ** 0.6, 0.2, 2.4))
    L = min(3.2, t60 * 1.1 + 0.1)
    n = n_of(L)
    P = max(4, int(SR / f0))
    k = max(4, P // 2)
    exc = np.sin(np.pi * np.arange(k) / k) + 0.25 * rng.uniform(-1, 1, k)
    exc = onepole_lp(exc, 1500 + 3500 * vel)
    exc = exc - exc.mean()
    y = karplus_strong(f0 * (1 + rng.normal(0, 0.0007)), L, excitation=exc, t60=t60, brightness=0.55 - 0.2 * vel,
                       pluck_pos=0.17)
    if f0 > 250:
        body = ([280, 460, 1050, 2700], [4, 5, 5, 4], [0.8, 0.9, 0.6, 0.4])
    elif f0 > 100:
        body = ([200, 330, 700, 1600], [4, 5, 5, 4], [0.9, 0.8, 0.5, 0.3])
    else:
        body = ([95, 180, 420], [4, 5, 5], [1.0, 0.8, 0.4])
    y = 0.6 * y + 0.8 * dsp.resonator_bank(y, *body)
    y = _norm(y)
    nt = n_of(0.03)
    th = sos(rng.standard_normal(nt), "lowpass", 700 + 900 * vel, 2) * exp_env(nt, 0.02)
    y[:nt] += 0.1 * vel * _norm(th)
    t = t_axis(n)
    y *= np.exp(-t / max(0.15, t60 * 0.7))
    y = dsp.fade(y, 0.0018, 0.06, shape="sine")
    p = float(np.clip((midi - 62) / 30.0, -0.5, 0.5)) if pan is None else pan
    return (_pan(y, p) * 0.3 * vel ** 1.4).astype(np.float32)


@functools.lru_cache(maxsize=512)
def harp(midi, vel, var=0, pan=0.0):
    """Concert harp: gut-string KS, warm, long ring, soundboard warmth."""
    f0 = hz(midi)
    rng = np.random.default_rng(2003 * midi + 31 * var)
    t60 = float(np.clip(3.2 * (220.0 / f0) ** 0.5, 0.8, 6.0))
    L = min(4.0, t60 * 0.8)
    P = max(4, int(SR / f0))
    exc = onepole_lp(rng.uniform(-1, 1, P), 2500 + 3500 * vel)
    exc -= exc.mean()
    y = karplus_strong(f0, L, excitation=exc, t60=t60, brightness=0.45, pluck_pos=0.28)
    y = 0.8 * y + 0.35 * dsp.resonator_bank(y, [180, 420, 900], [3, 4, 4], [1.0, 0.6, 0.3])
    y = _norm(y)
    y = dsp.fade(y, 0.0005, 0.4)
    return (_pan(y, pan) * 0.22 * vel ** 1.3).astype(np.float32)


@functools.lru_cache(maxsize=512)
def celesta(midi, vel, var=0, pan=0.0):
    """Celesta: steel bars over wooden resonators - a pure, bell-like fundamental with a quick
    inharmonic shimmer, felt-hammer onset."""
    f0 = hz(midi)
    rng = np.random.default_rng(3001 * midi + 7 * var)
    n = n_of(2.4)
    t = t_axis(n)
    out = np.zeros((n, 2))
    tl = float(np.clip(1.5 * (1047.0 / f0) ** 0.35, 0.6, 2.2))
    for ratio, a, t60 in ((1.0, 1.0, tl), (2.76, 0.22, 0.22), (4.0, 0.1, 0.45), (5.4, 0.08, 0.07)):
        if f0 * ratio > 17000:
            continue
        for ch in range(2):
            d = 1 + (0.0008 if ch else -0.0008) * (1 if ratio == 1.0 else 0)
            out[:, ch] += a * np.sin(TWO_PI * f0 * ratio * d * t + rng.uniform(0, TWO_PI)) * np.power(10.0, np.maximum(-3 * t / t60, -30))
    k = n_of(0.003)
    out[:k] *= np.linspace(0, 1, k)[:, None] ** 1.5
    nh = n_of(0.02)
    out[:nh] += (sos(rng.standard_normal(nh), "bandpass", (800, 3000), 2) * exp_env(nh, 0.01) * 0.04)[:, None]
    out = _norm(out)
    th = (float(np.clip(pan, -1, 1)) + 1) * math.pi / 4
    out[:, 0] *= math.cos(th) * math.sqrt(2)
    out[:, 1] *= math.sin(th) * math.sqrt(2)
    return (out * 0.16 * vel ** 1.3).astype(np.float32)


def harmonic(midi, dur, vel, rng, attack=0.25, release=0.8, bend=None):
    """Flautando string harmonics: three players on a near-sine with a breath of bow noise."""
    f0 = hz(midi)
    n = n_of(dur + release)
    t = t_axis(n)
    out = np.zeros((n, 2))
    for k, (cents, pan) in enumerate(((-3.0, -0.4), (0.5, 0.1), (3.5, 0.45))):
        vib = 1 + 0.0018 * np.sin(TWO_PI * rng.uniform(4.8, 5.8) * t + rng.uniform(0, 6)) * np.clip((t - 0.3) / 0.6, 0, 1)
        f = f0 * 2 ** (cents / 1200) * vib * (1 + 0.0006 * dsp.smooth_noise(n, 0.7, rng))
        if bend is not None:
            f = f * bend(t)
        ph = np.cumsum(f) / SR + rng.uniform()
        x = np.sin(TWO_PI * ph) + 0.05 * np.sin(2 * TWO_PI * ph) + 0.015 * np.sin(3 * TWO_PI * ph)
        out += _pan(x, pan) / 3.0
    bow = sos(rng.standard_normal(n), "bandpass", (f0 * 0.8, min(f0 * 1.6, 20000)), 2) * 0.05
    out += np.stack([bow, bow[::-1]], axis=1) * 0.5
    a = max(attack, 0.01)
    env = np.where(t < a, np.sin(0.5 * np.pi * np.clip(t / a, 0, 1)) ** 2, 1.0)
    env = np.where(t > dur, np.power(10.0, np.maximum(-3.0 * (t - dur) / max(release, 0.02), -30)), env)
    return out * (env * 0.09 * vel)[:, None]


@functools.lru_cache(maxsize=8)
def hour_bell(var=0):
    """The clock at eleven: one deep strike on A - minor-third bell partials over a low A
    thump, a harp harmonic on top."""
    rng = np.random.default_rng(1100 + var)
    n = n_of(6.0)
    t = t_axis(n)
    f = 220.0
    ratios = np.array([0.5, 1.0, 1.19, 1.5, 2.0, 2.52, 3.0, 4.07, 5.2])
    amps = np.array([0.55, 0.8, 0.5, 0.25, 0.45, 0.22, 0.14, 0.08, 0.05])
    t60s = np.array([5.5, 4.2, 3.2, 2.4, 2.0, 1.3, 0.9, 0.55, 0.35])
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = dsp.modal(f * ratios * (1 + (0.0007 if ch else -0.0007)), t60s, amps, n, phases=rng.uniform(0, TWO_PI, len(ratios)))
    strike = sos(rng.standard_normal(n_of(0.05)), "bandpass", (600, 5000), 2) * exp_env(n_of(0.05), 0.03)
    out[:len(strike)] += 0.25 * strike[:, None]
    fd = 55.0 * (1 + 0.15 * np.exp(-t / 0.03))
    low = np.sin(TWO_PI * np.cumsum(fd) / SR) * np.power(10.0, np.maximum(-3 * t / 2.6, -30)) + 0.5 * np.sin(TWO_PI * 110 * t) * np.power(10.0, np.maximum(-3 * t / 2.0, -30))
    out += 0.6 * low[:, None]
    dsp.mix_into(out, np.asarray(harp(m("A5"), 0.5, var), dtype=np.float64) * 2.0, 0)
    out[:n_of(0.002)] *= np.linspace(0, 1, n_of(0.002))[:, None]
    out = dsp.fade(out, 0.0, 1.5)
    return (_norm(out) * 0.42).astype(np.float32)


def timpani(f0, rng, vel=1.0):
    n = n_of(2.6)
    t = t_axis(n)
    f = f0 * (1 + 0.06 * np.exp(-t / 0.05))
    x = np.sin(TWO_PI * np.cumsum(f) / SR) * exp_env(n, 1.6)
    x += 0.4 * np.sin(TWO_PI * np.cumsum(f * 1.51) / SR) * exp_env(n, 0.8)
    x += 0.25 * np.sin(TWO_PI * np.cumsum(f * 1.99) / SR) * exp_env(n, 0.5)
    x += sos(rng.standard_normal(n), "lowpass", 700 + 900 * vel, 2) * exp_env(n, 0.03) * 0.6
    x[:n_of(0.002)] *= np.linspace(0, 1, n_of(0.002))
    return dsp.to_stereo(x) * 0.22 * vel


def timp_roll(f0, dur, rng, v0=0.2, v1=1.0, rate=14.0):
    n = n_of(dur + 2.6)
    out = np.zeros((n, 2))
    k = 0
    tt = 0.0
    while tt < dur:
        u = tt / max(dur, 1e-3)
        v = (v0 + (v1 - v0) * u ** 1.5) * rng.uniform(0.85, 1.0)
        x = timpani(f0, rng, v) * (0.55 if k % 2 else 0.5)
        dsp.mix_into(out, x, n_of(tt))
        tt += (1.0 / rate) * rng.uniform(0.9, 1.1)
        k += 1
    return out


# ============================================================================ instruments (24 kHz)
def strings_note(f0, gate, attack, release, vel, rng, voices=6, detune=9.0, vib=0.005, bend=None, trem=None, sr=SR2):
    """Section strings voice: detuned saws with slow drift and delayed vibrato."""
    n = int((gate + release) * sr) + 1
    t = np.arange(n) / sr
    out = np.zeros((n, 2))
    for v in range(voices):
        sp = (2.0 * v / max(voices - 1, 1) - 1.0)
        cents = detune * 0.6 * rng.normal(0, 1.0) + 2.0 * sp
        drift = 1 + 0.0012 * dsp.smooth_noise(n, 0.6, rng, sr)
        depth = vib * np.clip((t - 0.35) / 0.9, 0, 1)
        f = f0 * drift * 2 ** (cents / 1200) * (1 + depth * np.sin(TWO_PI * rng.uniform(4.7, 5.9) * t + rng.uniform(0, TWO_PI)))
        if bend is not None:
            f = f * bend(t)
        s = saw(f, n, sr, phase0=rng.uniform())
        th = (0.7 * sp + 1) * math.pi / 4
        out[:, 0] += math.cos(th) * s
        out[:, 1] += math.sin(th) * s
    a = max(attack, 0.005)
    env = np.where(t < a, np.sin(0.5 * math.pi * np.clip(t / a, 0, 1)) ** 2, 1.0)
    env = np.where(t > gate, np.power(10.0, np.maximum(-3.0 * np.maximum(t - gate, 0.0) / max(release, 0.02), -30)), env)
    if trem:
        rate, depth = trem
        env = env * (1 - depth + depth * (0.5 + 0.5 * np.sin(TWO_PI * rate * t)) ** 2)
    return out * (env * vel / voices)[:, None]


def brass_note(f0, dur, vel, rng, attack=0.04, release=0.3, sfz=False, swell=None, sr=SR2):
    """Muted brass voice (3 players): saw stack with an attack scoop; brightness follows the
    dynamic. sfz: hard attack falling to a held piano; swell: (t_peak, exp) crescendo."""
    n = int((dur + release) * sr) + 1
    t = np.arange(n) / sr
    a = max(attack, 0.005)
    env = np.where(t < a, np.sin(0.5 * np.pi * np.clip(t / a, 0, 1)) ** 1.5, 1.0)
    if sfz:
        env = env * (0.32 + 0.68 * np.exp(-np.maximum(t - a, 0) / 0.09))
    if swell is not None:
        tp, ex = swell
        env = env * (0.08 + 0.92 * np.clip(t / max(tp, 1e-3), 0, 1) ** ex)
    env = np.where(t > dur, env * np.power(10.0, np.maximum(-3.0 * (t - dur) / max(release, 0.02), -30)), env)
    out = np.zeros((n, 2))
    for v, pan in enumerate((-0.35, 0.05, 0.4)):
        cents = rng.normal(0, 4.0)
        f = f0 * 2 ** (cents / 1200) * (1 - 0.028 * np.exp(-t / 0.035)) * (1 + 0.0012 * dsp.smooth_noise(n, 1.5, rng, sr))
        s = saw(f, n, sr, phase0=rng.uniform())
        cut = np.clip(f0 * (1.2 + 7.0 * vel * env), 150, 0.45 * sr)
        s = tv_lowpass(s, cut, q=0.8, sr=sr, block=64)
        th = (pan + 1) * math.pi / 4
        out[:, 0] += math.cos(th) * s
        out[:, 1] += math.sin(th) * s
    return out * (env * vel / 3.0)[:, None]


def _mute_eq(x, sr=SR2):
    """Stopped / straight-muted horn colour: thin low end, a nasal buzz around 1.8-2.4 kHz."""
    y = sos(x, "highpass", 140, 2, sr=sr)
    y = dsp.biquad(y, "peak", 2100, 1.6, 7.0, sr=sr)
    y = dsp.biquad(y, "peak", 650, 1.0, -3.0, sr=sr)
    y = sos(y, "lowpass", 5200, 2, sr=sr)
    return saturate(y * 1.3, 1.6) / 1.3


def _sordino(x, sr=SR2):
    """Con sordino section colour: soft top, a little nasal mid, no fizz."""
    y = sos(x, "highpass", 60, 2, sr=sr)
    y = sos(y, "lowpass", 3000, 2, sr=sr)
    y = dsp.biquad(y, "peak", 1100, 1.0, 2.0, sr=sr)
    return dsp.biquad(y, "peak", 350, 1.0, 1.5, sr=sr)


# ============================================================================ the plan
class Plan:
    def __init__(self, S, N):
        self.S = S
        self.N = N
        self.total = N / SR
        self.strings = []   # (t, gate, [midi], vel, attack, release, kw, layer)
        self.brass = []     # (t, dur, [midi], vel, kw, layer)
        self.notes = []     # (t, kind, midi, vel, layer, kw)
        self.events = []    # (t, fn(rng) -> stereo 48 kHz, layer, send)
        self.masks = []     # (t0, t1, fade_out, fade_in, layers)
        self.marks = []     # (t, label, layer)

    # ---- helpers ----------------------------------------------------------
    def st(self, t, gate, names, vel, attack=1.0, release=1.2, layer="main", **kw):
        self.strings.append((t, gate, ms(names), vel, attack, release, kw, layer))

    def br(self, t, dur, names, vel, layer="main", **kw):
        self.brass.append((t, dur, ms(names), vel, kw, layer))

    def nt(self, t, kind, names, vel, layer="main", strum=0.0, **kw):
        for i, mm in enumerate(ms(names)):
            self.notes.append((t + i * strum, kind, mm, vel, layer, kw))

    def ev(self, t, fn, layer="hits", send=0.3):
        self.events.append((t, fn, layer, send))

    def mark(self, t, label, layer="hits"):
        self.marks.append((round(float(t), 3), label, layer))

    def silence(self, t0, t1, fo=0.02, fi=0.05, layers=("main", "hits", "tick")):
        self.masks.append((t0, t1, fo, fi, tuple(layers)))
        self.mark(t0, "silence", "mask")

    def ticks(self, t0, t1, period=1.0, vel=0.42, first_tick=True, accel_to=None, bass_every=0, vel_end=None):
        """The pizzicato clock: tick (E5) / tock (B4) from t0 while t < t1 - eps. accel_to: period
        reached at t1 (linear in time). bass_every: an A1 pizz under every k-th tick."""
        t, k = t0, 0
        out = []
        while t < t1 - 1e-6:
            u = (t - t0) / max(t1 - t0, 1e-6)
            v = vel if vel_end is None else vel + (vel_end - vel) * u
            nm = TICK if (k % 2 == 0) == first_tick else TOCK
            self.nt(t, "pizz", nm, v * (1.0 if nm == TICK else 0.9), "tick", var=k % 3, pan=0.12 if nm == TICK else -0.12)
            if bass_every and k % bass_every == 0:
                self.nt(t, "pizz", "A1", min(1.0, v * 1.25), "tick", var=k % 2, pan=0.0)
            out.append(t)
            p = period if accel_to is None else period + (accel_to - period) * u
            t += p
            k += 1
        return out

    def stab(self, t, step, size=0.8, pan=0.0, gain=1.0, label="stab"):
        def fn(rng, step=step, size=size, pan=pan, gain=gain):
            x = SP.render("string_stab", params=dict(step=step, size=size), seed=int(rng.integers(1 << 20))).astype(np.float64)
            return dsp.pan_stereo(x, pan) * gain
        self.ev(t, fn, "hits", send=0.15)
        self.mark(t, label)

    # ---- the composition ---------------------------------------------------
    def compose(self):
        S = self.S
        from films.shadowplay.audio.cuesheet import word, g
        w = word

        # ============================================================ s01 forty windows
        from films.shadowplay.audio.cuesheet import s01_pop_t
        rows = [s01_pop_t(S, 5 * r + 1) for r in range(8)]                 # each row's first window
        for r, (t, nm) in enumerate(zip(rows, "A3 C4 E4 G#4 A4 C5 E5 G#5".split())):
            self.nt(t, "pizz", nm, 0.42 + 0.03 * r, "main", var=r)
        self.nt(S["s01_grid"], "pizz", AMM7, 0.75, "hits", strum=0.008)            # the grid snaps tight
        self.nt(S["s01_grid"], "pizz", "A1", 0.9, "hits")
        self.mark(S["s01_grid"], "pizz chord [forty]")
        self.st(g("s01", 4.4), 4.8, AMM7, 0.32, attack=1.6, release=1.4)          # night: the chord enters
        for k, (dt, nm) in enumerate(((0.0, "G#6"), (0.11, "E6"), (0.19, "C6"), (0.33, "A5"), (0.46, "E6"))):
            self.nt(S["s01_lights"] + dt, "celesta", nm, 0.45, "main", var=k, pan=(-0.4, 0.3, -0.1, 0.45, 0.1)[k])
        self.nt(S["s01_heart"], "pizz", "A1 A2", 0.85, "hits")                      # lub
        self.nt(S["s01_heart"] + 0.27, "pizz", "E2", 0.7, "hits")                   # dub (the second pulse)
        self.mark(S["s01_heart"], "heart pizz")
        # T1: the clock, phase-locked so the hour falls on [eleven] (s03)
        eleven3 = w("s03", "eleven")
        t1_start = eleven3 - math.floor(eleven3 - (S["s01_heart"] + 0.9))
        self.ticks(t1_start, eleven3 - 0.5, vel=0.4)
        self.mark(t1_start, "tick T1 starts", "main")

        # ============================================================ s02 the watcher
        self.st(9.0, w("s02", "Twelve") - 9.0 + 3.9, AMM7, 0.3, attack=0.8, release=1.6)
        self.st(15.7, 3.9, FMA7S11, 0.3, attack=1.4, release=1.4)
        self.st(19.6, 1.9, DM9, 0.3, attack=1.0, release=1.0)
        self.nt(S["s02_win4"], "harp", "E5", 0.55, pan=-0.3)
        self.nt(S["s02_win12"], "harp", "C5", 0.55, pan=0.25)
        self.nt(S["s02_win30"], "harp", "A4", 0.55, pan=-0.1)
        self.nt(S["s02_bino"] + 0.07, "celesta", "G#6", 0.5, pan=0.2)
        self.nt(S["s02_bino"] + 0.07, "celesta", "E7", 0.3, pan=0.25)
        title = S["s02_title_in"] + 0.45                                           # the letters stop
        self.br(title, 0.5, "A3 C4 E4 G#4", 0.85, "hits", sfz=True, attack=0.012, release=0.5)
        self.st(title, 0.35, "A4 C5 E5 G#5", 0.55, attack=0.01, release=0.6, layer="hits")
        self.nt(title, "pizz", "A1 A2", 0.85, "hits")
        self.mark(title, "title stab")
        self.st(title + 0.6, S["s02_iris"] + 1.2 - title - 0.6, E7B9, 0.26, attack=1.2, release=1.2)

        # ============================================================ s03 window nine
        self.st(w("s03", "Window"), 28.8 - w("s03", "Window"), AMM7, 0.3, attack=0.8, release=0.8)
        self.st(28.8, eleven3 - 28.8 + 0.05, BB, 0.32, attack=0.8, release=0.6)
        self.ev(eleven3, lambda r: np.asarray(hour_bell(0), dtype=np.float64), "hits", send=0.35)
        self.mark(eleven3, "hour strike [eleven]")
        light = S["s03_light_on"]
        self.notes.append((eleven3 + 0.2, "harm", m("E6"), 0.6, "main", dict(dur=light - eleven3 - 0.1)))
        self.st(light, S["s03_light_out"] - light, "A1", 0.55, attack=0.4, release=0.1, voices=4, detune=5)
        self.notes.append((light, "harm", m("E7"), 0.45, "main", dict(dur=S["s03_stab1"] - light - 0.3)))
        self.br(light + 0.45, S["s03_arm"] - light - 0.4, "E3 G#3 C4", 0.45, "main", swell=(S["s03_arm"] - light - 0.45, 1.6),
                attack=0.5, release=0.3)
        self.nt(light + 1.65, "pizz", "E3", 0.55)
        arm = S["s03_arm"]
        self.st(arm, S["s03_stab1"] - arm, "A3 E4 A4", 0.5, attack=S["s03_stab1"] - arm, release=0.02, trem=(13.0, 0.5),
                bend=lambda tt, d=S["s03_stab1"] - arm: 2 ** (2.0 * np.clip(tt / d, 0, 1) ** 1.4 / 12))
        self.br(arm, S["s03_stab1"] - arm, "A2 Bb2 E3", 0.5, "main", swell=(S["s03_stab1"] - arm, 2.0), attack=0.3, release=0.02)
        for k, nm in enumerate(("s03_stab1", "s03_stab2", "s03_stab3")):
            self.stab(S[nm], k, size=0.6 + 0.15 * k, label=f"stab {k + 1}")
        self.br(S["s03_stab3"], 0.45, "A3 Bb3 E4 G#4", 0.95, "hits", sfz=True, attack=0.01, release=0.35)
        self.ev(S["s03_stab3"], lambda r: timpani(55.0, r, 1.0), "hits", send=0.3)
        fall = S["s03_stab3"] + 0.12
        dfall = S["s03_light_out"] - fall
        self.st(fall, dfall, "A3", 0.45, attack=0.05, release=0.1, voices=4, detune=6,
                bend=lambda tt, d=dfall: 2 ** (-12.0 * np.clip(tt / d, 0, 1) ** 1.3 / 12))
        self.silence(S["s03_light_out"], S["s03_light_out"] + 1.1, fo=0.01, fi=0.4)
        self.mark(S["s03_light_out"], "light out: silence")
        self.st(S["s03_light_out"] + 1.1, 41.0 - S["s03_light_out"] - 1.1, "A1 E2", 0.35, attack=1.6, release=1.0, voices=4)
        self.notes.append((w("s03", "Every"), "harm", m("G#6"), 0.5, "main", dict(dur=40.6 - w("s03", "Every"))))
        # T2: phase-locked to s05's [eleven]
        eleven5 = w("s05", "eleven")
        t2_start = eleven5 - math.floor(eleven5 - w("s03", "second"))
        self.ticks(t2_start, eleven5 - 0.5, vel=0.38)
        self.mark(t2_start, "tick T2 starts", "main")

        # ============================================================ s04 nothing
        self.br(S["s04_burst"], 0.6, "A2 Bb2 E3", 0.75, "hits", sfz=True, attack=0.015, release=0.5)
        self.ev(S["s04_burst"], lambda r: timpani(55.0, r, 0.8), "hits", send=0.3)
        self.mark(S["s04_burst"], "door burst stinger")
        for k, (nm, note) in enumerate((("s04_body", "E4"), ("s04_blood", "C4"), ("s04_woman", "A3"))):
            self.br(S[nm], 0.32, note, 0.42, "hits", sfz=True, attack=0.02, release=0.35)
            self.mark(S[nm], f"nothing dot {k + 1}")
        self.st(41.8, 46.2 - 41.8, "D2 A2 F3 A3", 0.28, attack=1.0, release=1.0)
        self.st(46.2, S["s04_dreamed"] - 46.2 + 0.2, FMA7S11, 0.28, attack=0.9, release=0.8)
        dre = S["s04_dreamed"]
        self.notes.append((dre, "harm", m("G#5"), 0.55, "main", dict(dur=1.4, bend=lambda tt: 2 ** (-1.0 * np.clip((tt - 0.5) / 0.6, 0, 1) / 12))))
        self.mark(dre, "G#->G [dreamed]", "main")
        self.st(dre + 0.6, S["s04_bars"] + 1.0 - dre - 0.6, E7B9, 0.3, attack=1.2, release=0.6)

        # ============================================================ s05 again
        l5 = S["s05_light_on"]
        self.st(l5, eleven5 - l5 + 0.3, AMM7, 0.33, attack=0.5, release=0.8)
        self.ev(eleven5, lambda r: np.asarray(hour_bell(1), dtype=np.float64), "hits", send=0.35)
        self.mark(eleven5, "hour strike [eleven] (rhyme)")
        again = S["s05_again"]
        b0 = eleven5 + 0.6
        self.st(b0, again - b0, "A3 E4 A4", 0.48, attack=again - b0, release=0.02, trem=(13.0, 0.5),
                bend=lambda tt, d=again - b0: 2 ** (2.0 * np.clip(tt / d, 0, 1) ** 1.4 / 12))
        self.br(b0, again - b0, "A2 Bb2 E3", 0.48, "main", swell=(again - b0, 2.0), attack=0.3, release=0.02)
        self.stab(again, 1, size=0.85, pan=-0.35, gain=0.8, label="stab [again] (top)")
        self.stab(again + 0.011, 1, size=0.85, pan=0.35, gain=0.8, label="stab [again] (bottom)")
        self.silence(again + 0.2, S["s05_second"] - 0.45, fo=0.25, fi=0.3, layers=("main",))
        sec = S["s05_second"]
        self.ticks(sec, 65.3, vel=0.45)                                            # T3: same second
        self.mark(sec, "tick T3 [second]", "main")
        self.nt(sec, "harp", "E6", 0.5, pan=0.0)
        self.nt(S["s05_arm"], "pizz", "A3 A4", 0.75, "hits")
        self.mark(S["s05_arm"], "unison pizz [arm]")
        cut = S["s05_scream"] + 0.21
        self.st(S["s05_arm"] + 0.45, cut - S["s05_arm"] - 0.45, "A4 Bb4 B4 C5", 0.42, attack=cut - S["s05_arm"] - 0.45, release=0.01,
                trem=(15.0, 0.45))
        self.silence(cut, 63.0, fo=0.006, fi=0.6, layers=("main",))
        self.mark(cut, "scream cut", "main")
        self.st(63.0, 66.0 - 63.0, "D2 A2 F3", 0.3, attack=1.0, release=0.4)
        self.stab(S["s05_last_stab"], 3, size=1.0, label="last stab -> slash")

        # ============================================================ s06 crossing
        red = S["s06_coat"] - 0.2
        self.br(red, 1.3, "E4", 0.6, "main", attack=0.08, release=0.8)
        self.br(red + 0.35, 1.0, "A4", 0.62, "main", attack=0.06, release=0.9)
        self.st(red, 2.2, FMA7S11, 0.32, attack=0.4, release=1.5)
        self.mark(red, "red: horn call", "main")
        self._spiral(67.3, S["s06_stairs"], step=0.19, vel=0.36, spin=0.35, mode="contrary", chords=(AMM7, FMA7S11))
        st0, st1 = S["s06_stairs"], S["s06_street"]
        self._spiral(st0, st1, step=0.12, vel=0.48, spin=0.9, mode="down", chords=(AMM7, E7B9))
        self.st(st0, st1 - st0, "E6", 0.42, attack=0.2, release=0.3, voices=4, detune=6, trem=(11.0, 0.3),
                bend=lambda tt, d=st1 - st0: 2 ** (-7.0 * np.clip(tt / d, 0, 1) ** 1.2 / 12))
        self.ev(st0, lambda r, d=st1 - st0: timp_roll(55.0, d, r, 0.15, 0.7), "main", send=0.3)
        self.mark(st0, "Vertigo spiral down", "main")
        dr0, dr1 = st1, S["s06_crane"]
        k = 0
        tt = dr0
        while tt < dr1 - 0.05:
            self.nt(tt, "pizz", "A2" if k % 2 == 0 else "E3", 0.6, var=k % 3)
            tt += 0.18
            k += 1
        self.ev(dr0, lambda r: timpani(55.0, r, 0.9), "hits", send=0.3)
        self._spiral(S["s06_crane"], 78.6, step=0.15, vel=0.47, spin=0.25, mode="up", chords=(DM9, E7B9))
        cr0 = S["s06_crane"]
        self.st(cr0, 78.5 - cr0, DM9, 0.38, attack=78.5 - cr0, release=0.6)
        self.br(76.2, 78.5 - 76.2, "D3 A3 C4 E4", 0.4, "main", swell=(78.5 - 76.2, 1.8), attack=0.4, release=0.3)
        self.ev(77.3, lambda r: timp_roll(41.2, 1.2, r, 0.1, 0.6), "main", send=0.3)
        self.st(78.5, 1.6, E7B9, 0.34, attack=0.15, release=0.9)
        self.br(78.5, 1.0, "E3 G#3 D4", 0.42, "main", attack=0.05, release=0.8)
        self.mark(S["s06_crane"], "spiral up (crane)", "main")

        # ============================================================ s07 the show
        self.st(79.5, 86.0 - 79.5, "A1 Bb1", 0.3, attack=1.5, release=0.6, voices=4, detune=5)
        for k, (nm, note) in enumerate((("s07_lamp", "C6"), ("s07_sheet", "E6"), ("s07_dolls", "G#6"))):
            self.nt(S[nm], "celesta", note, 0.5, pan=(-0.2, 0.15, 0.3)[k], var=k)
            self.mark(S[nm], f"celesta [{nm[4:]}]", "main")
        self.st(86.0, 87.1 - 86.0, DM9, 0.28, attack=0.8, release=0.5)
        self.st(87.1, S["s07_show"] - 87.1, BB, 0.32, attack=0.6, release=0.1)
        show = S["s07_show"]
        self.br(show, 0.7, "A3 C4 E4 G#4", 0.85, "hits", sfz=True, attack=0.012, release=0.6)
        self.st(show, 0.4, AMM7, 0.5, attack=0.01, release=0.8, layer="hits")
        self.ev(show, lambda r: timpani(55.0, r, 0.7), "hits", send=0.3)
        self.mark(show, "show stab")
        self.st(show + 0.3, 92.0 - show - 0.3, AMM7, 0.24, attack=0.8, release=0.8)

        # ============================================================ s08 the other side
        self.st(92.0, S["s08_someone"] - 92.0 + 0.4, "A2 Bb2 E3", 0.24, attack=1.5, release=0.8)
        self.ticks(92.5, 97.6, vel=0.3, first_tick=False)                          # the clock seen from the other side
        self.br(S["s08_someone"], S["s08_glint"] - S["s08_someone"], "E3 G#3 B3", 0.45, "main",
                swell=(S["s08_glint"] - S["s08_someone"], 1.5), attack=0.4, release=0.5)
        self.notes.append((S["s08_glint"], "harm", m("E7"), 0.45, "main", dict(dur=1.4)))
        for k, nm in enumerate(("G#5", "E5", "C5")):
            self.nt(S["s08_wave"] + 0.55 * k, "celesta", nm, 0.45, pan=0.25 - 0.2 * k, var=k)
        self.mark(S["s08_wave"], "the wave", "main")
        b0 = 101.0
        b1 = S["s08_light_off"] - 0.06
        self.st(b0, b1 - b0, "A3 Bb3 E4 F4", 0.42, attack=b1 - b0, release=0.01, trem=(9.0, 0.4))
        self.st(b0, b1 - b0, "A1 E2", 0.35, attack=2.0, release=0.01, voices=4)
        self.silence(b1, w("s09", "ninety") - 0.01, fo=0.005, fi=0.02)
        self.mark(b1, "cut to silence (her light)", "mask")

        # ============================================================ s09 ninety seconds
        n0 = w("s09", "ninety")
        stop = S["s09_feet_stop"]
        self.ticks(n0, stop, period=0.5, accel_to=0.3, vel=0.42, vel_end=0.62, bass_every=4)
        self.mark(n0, "fast clock [ninety]", "main")
        self.st(110.0, stop - 110.0, "A2 E3 A3", 0.42, attack=stop - 110.0, release=0.01, trem=(12.0, 0.45))
        for k, nm in enumerate(("s09_lamp", "s09_sheet", "s09_believe")):
            self.nt(S[nm], "pizz", ("A2 E3 A3", "C3 G#3 C4", "E3 A3 E4")[k], 0.8, "hits", strum=0.006)
            self.mark(S[nm], f"pizz accent [{nm[4:]}]")
        bel = S["s09_believe"]
        for nm in ("A5", "C6", "E6", "G#6"):
            self.notes.append((bel, "harm", m(nm), 0.4, "main", dict(dur=S["s09_show"] - bel - 0.1)))
        self.br(S["s09_show"], 0.5, "A3 C4 E4 G#4", 0.55, "hits", sfz=True, attack=0.015, release=0.45)
        self.mark(S["s09_show"], "brass echo [show]")
        self.silence(stop, S["s10_burst"] - 0.005, fo=0.008, fi=0.005)
        self.mark(stop, "dead stop", "mask")

        # ============================================================ s10 the trap (wordless)
        bu = S["s10_burst"]
        self.br(bu, 0.55, "A2 Bb2 E3 Bb3 E4", 1.0, "hits", sfz=True, attack=0.008, release=0.4)
        self.st(bu, 0.25, "A2 E3 A3", 0.7, attack=0.006, release=0.3, layer="hits")
        self.ev(bu, lambda r: timpani(55.0, r, 1.0), "hits", send=0.3)
        self.mark(bu, "tutti hit (burst)")
        for k, nm in enumerate(("s10_stab1", "s10_stab2", "s10_stab3", "s10_stab4")):
            self.stab(S[nm], k, size=0.7 + 0.1 * k, gain=1.0 + 0.06 * k, label=f"trap stab {k + 1}")
        self.silence(S["s10_stab4"] + 0.5, S["s10_slam"] - 0.01, fo=0.15, fi=0.005, layers=("main", "hits", "tick"))
        sl = S["s10_slam"]
        self.br(sl, 0.4, "A1 A2 E3", 0.9, "hits", sfz=True, attack=0.008, release=0.4)
        self.ev(sl, lambda r: timpani(55.0, r, 1.0), "hits", send=0.3)
        self.mark(sl, "slam hit")
        bolt = S["s10_key"] + 0.52
        self.nt(bolt, "pizz", "A1 E2", 0.9, "hits")
        self.mark(bolt, "bolt pizz")
        cr = S["s10_crash"]
        self.br(cr, 0.5, "Bb2 E3 Bb3 E4", 0.85, "hits", sfz=True, attack=0.01, release=0.4)
        self.st(cr, 0.3, "A4 Bb4 E5", 0.6, attack=0.006, release=0.4, layer="hits", trem=(16.0, 0.5))
        self.ev(cr, lambda r: timpani(58.27, r, 0.9), "hits", send=0.3)
        self.mark(cr, "crash hit")
        self.silence(S["s10_dark"], S["s10_slide"], fo=0.05, fi=1.2)
        self.st(S["s10_slide"], 141.5 - S["s10_slide"], "A1 E2", 0.36, attack=2.5, release=1.0, voices=4)
        self.notes.append((S["s10_slide"] + 0.8, "harm", m("E6"), 0.4, "main", dict(dur=S["s10_tear"] - S["s10_slide"] - 0.3)))

        # ============================================================ s11 forty dolls
        self.nt(S["s11_found"], "pizz", TICK, 0.5, "hits", pan=0.12)
        self.mark(S["s11_found"], "one tick [forty]")
        wn = S["s11_window"]
        self.nt(wn, "pizz", AMM7, 0.7, "hits", strum=0.008)
        self.nt(wn + 0.03, "celesta", "A5 C6 E6 G#6", 0.45, "main", strum=0.05)
        self.mark(wn, "grid chord [window]")
        self.notes.append((S["s11_binoculars"], "harm", m("G#6"), 0.45, "main", dict(dur=2.5)))
        self.nt(S["s11_binoculars"], "celesta", "G#6", 0.45, pan=0.1)
        self.st(139.0, 142.9 - 139.0, "F2 C3 A3 E4", 0.26, attack=1.5, release=1.2)

        # ============================================================ s12 mostly
        self.st(142.9, S["s12_mostly"] - 142.9 + 0.5, "F2 C3 A3 E4", 0.26, attack=0.8, release=1.0)
        mo = S["s12_mostly"]
        self.nt(mo, "pizz", TICK, 0.6, "hits", pan=0.12, var=7)
        self.mark(mo, "last pizz [Mostly]")
        self.st(mo + 0.7, 153.4 - mo - 0.7, "A1 A2 E3 C4 G#4", 0.22, attack=2.0, release=0.4)
        self.notes.append((mo + 3.0, "harm", m("E6"), 0.35, "main", dict(dur=152.6 - mo - 3.0)))
        self.nt(S["s12_glint"], "celesta", "G#6", 0.45, pan=0.0)
        self.mark(S["s12_glint"], "glint", "main")
        self.silence(153.42, self.total + 1.0, fo=1.0, fi=0.0)

    def _spiral(self, t0, t1, step, vel, spin, mode, chords):
        """Vertigo arpeggios: harp (low layer) + celesta (high layer) running through the chord
        tones over four octaves with a Shepard-like level bell, so the spiral never arrives; the
        pan circles. mode 'up' / 'down' / 'contrary' (two lines in contrary motion)."""
        def tones(names):
            pcs = sorted(set(x % 12 for x in ms(names)))
            return [o * 12 + pc for o in range(3, 8) for pc in pcs]
        k = 0
        t = t0
        while t < t1 - 0.02:
            ch = tones(chords[(k // 8) % len(chords)])
            lines = [1] if mode == "up" else [-1] if mode == "down" else [1, -1]
            for li, d in enumerate(lines):
                L = len(ch)
                idx = (k * d + (0 if d > 0 else L - 1) + 3 * li) % L
                mm = ch[idx]
                wgt = math.exp(-0.5 * ((mm - 74) / 10.0) ** 2)
                pan = 0.65 * math.sin(TWO_PI * spin * (t - t0) + li * math.pi)
                if wgt < 0.05:
                    continue
                kind = "celesta" if mm >= 79 else "harp"
                self.notes.append((t, kind, mm, vel * wgt * (0.9 if li else 1.0), "main", dict(var=k % 4, pan=round(pan, 2))))
            t += step
            k += 1


# ============================================================================ rendering
def _up2(x):
    from scipy import signal as _sg
    return np.stack([_sg.resample_poly(np.ascontiguousarray(x[:, c]), 2, 1) for c in range(x.shape[1])], axis=1)


def _sparse_reverb(x, ir, wet_db, thresh=1e-6, gap=1.5):
    """Convolve only the active regions of a send (tails kept)."""
    out = np.zeros_like(x)
    act = np.max(np.abs(x), axis=1) > thresh
    idx = np.nonzero(act)[0]
    if len(idx) == 0:
        return out
    brk = np.nonzero(np.diff(idx) > gap * SR)[0]
    starts = np.concatenate([[idx[0]], idx[brk + 1]])
    ends = np.concatenate([idx[brk], [idx[-1]]])
    for a, b in zip(starts, ends):
        wet = dsp.convolve(x[a:b + 1].mean(axis=1), ir) * db2lin(wet_db)
        dsp.mix_into(out, wet, a)
    return out


LAYER_GAIN = dict(strings=db2lin(-3.0), brass=db2lin(-2.0), notes=1.0)


def render_score(S, N, seed=0):
    plan = Plan(S, N)
    plan.compose()
    rng = np.random.default_rng(dsp.stable_seed("sp_score", seed))
    N2 = int(math.ceil(N / SR * SR2)) + 2
    bus = {k: np.zeros((N, 2)) for k in ("main", "hits", "tick")}
    send = {k: np.zeros((N, 2)) for k in ("main", "hits", "tick")}
    info = dict(notes=0, strings=0, brass=0)

    # ---- strings + brass at 24 kHz
    lo = {k: np.zeros((N2, 2)) for k in ("main", "hits")}
    br = {k: np.zeros((N2, 2)) for k in ("main", "hits")}
    for (t, gate, notes, vel, att, rel, kw, layer) in plan.strings:
        for mm in notes:
            x = strings_note(hz(mm), max(gate, 0.02), att, rel, vel, rng, **kw)
            dsp.mix_into(lo["hits" if layer == "hits" else "main"], x, int(t * SR2), 0.3)
            info["strings"] += 1
    for (t, dur, notes, vel, kw, layer) in plan.brass:
        for mm in notes:
            x = brass_note(hz(mm), max(dur, 0.02), vel, rng, **kw)
            dsp.mix_into(br["hits" if layer == "hits" else "main"], x, int(t * SR2), 0.3)
            info["brass"] += 1
    for k in ("main", "hits"):
        y = _sordino(lo[k]) * LAYER_GAIN["strings"] + _mute_eq(br[k]) * LAYER_GAIN["brass"]
        y48 = dsp.pad_to(_up2(y), N)
        bus[k] += y48
        send[k] += y48 * (0.55 if k == "main" else 0.4)
    del lo, br

    # ---- notes at 48 kHz
    for (t, kind, mm, vel, layer, kw) in plan.notes:
        kw = dict(kw)
        if kind == "pizz":
            x = pizz(int(mm), round(float(vel), 2), int(kw.get("var", 0)), kw.get("pan"))
            sg = 0.25
        elif kind == "harp":
            x = harp(int(mm), round(float(vel), 2), int(kw.get("var", 0)), float(kw.get("pan", 0.0)))
            sg = 0.45
        elif kind == "celesta":
            x = celesta(int(mm), round(float(vel), 2), int(kw.get("var", 0)), float(kw.get("pan", 0.0)))
            sg = 0.5
        elif kind == "harm":
            x = harmonic(int(mm), float(kw.get("dur", 1.0)), float(vel), rng, bend=kw.get("bend"))
            sg = 0.5
        else:
            continue
        dsp.mix_into(bus[layer], np.asarray(x, dtype=np.float64), n_of(t))
        dsp.mix_into(send[layer], np.asarray(x, dtype=np.float64), n_of(t), sg)
        info["notes"] += 1
    for (t, fn, layer, sg) in plan.events:
        x = fn(rng)
        dsp.mix_into(bus[layer], x, n_of(t))
        dsp.mix_into(send[layer], x, n_of(t), sg)

    # ---- reverbs (the score lives in a dark hall; the clock is closer, in a room)
    hall = dsp.make_ir("hall")
    for k in ("main", "hits"):
        bus[k] += _sparse_reverb(send[k], hall, -4.0)
    bus["tick"] += _sparse_reverb(send["tick"], SP.ir("her_room"), -6.0) + _sparse_reverb(send["tick"], hall, -12.0)
    del send

    # ---- designed silences (after the reverbs: they cut the tails too)
    for k in bus:
        gate = np.ones(N)
        for (t0, t1, fo, fi, layers) in plan.masks:
            if k not in layers:
                continue
            a, b = n_of(max(0.0, t0 - fo)), min(N, n_of(t1 + fi))
            if b <= a:
                continue
            st = np.arange(a, b) / SR
            gdn = np.clip((t0 - st) / max(fo, 1e-4), 0, 1)
            gup = np.clip((st - t1) / max(fi, 1e-4), 0, 1)
            gate[a:b] = np.minimum(gate[a:b], np.maximum(gdn, gup))
        bus[k] *= gate[:, None]
    main = bus["main"] + bus["tick"]
    hits = bus["hits"]
    info["marks"] = sorted(plan.marks)
    ons = [(t, kind) for (t, kind, mm, vel, layer, kw) in plan.notes] + [(t, "hit") for (t, fn, layer, sg) in plan.events]
    ons += [(t, "strings") for (t, gate, nts, vel, att, rel, kw, layer) in plan.strings if att <= 0.03]
    ons += [(t, "brass") for (t, dur, nts, vel, kw, layer) in plan.brass if kw.get("attack", 0.04) <= 0.06]
    ons += [(t0, "mask") for (t0, t1, fo, fi, ls) in plan.masks] + [(t1, "mask") for (t0, t1, fo, fi, ls) in plan.masks]
    info["onsets"] = sorted((round(float(t), 4), k) for t, k in ons)
    info["silences"] = [(round(a, 3), round(b, 3), list(ls)) for a, b, _, _, ls in plan.masks]
    return main.astype(np.float32), hits.astype(np.float32), info


if __name__ == "__main__":
    import time
    from engine.timing import timeline
    from films.shadowplay.audio import cuesheet
    tl = timeline("shadowplay")
    N = int(round(tl["duration"] * SR))
    sync, _ = cuesheet.sync_points([])
    t0 = time.time()
    main, hits, info = render_score(sync, N)
    print(f"score in {time.time() - t0:.1f}s: {info['notes']} notes, {info['strings']} string voices, {info['brass']} brass")
    mix = main.astype(np.float64) + hits
    print("music integrated", round(dsp.loudness_integrated(mix), 2), "TP", round(dsp.true_peak_db(mix), 2),
          "main", round(dsp.loudness_integrated(main), 2), "hits", round(dsp.loudness_integrated(hits), 2))
    out = os.path.join(_ROOT, "films", "shadowplay", "out")
    os.makedirs(out, exist_ok=True)
    dsp.write_wav(os.path.join(out, "score_preview.wav"), mix * 0.5, bits=24)
