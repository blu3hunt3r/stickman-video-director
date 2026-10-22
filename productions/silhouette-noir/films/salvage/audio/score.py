"""SALVAGE score: one D-minor score from the red line to the red line.

    render_score(C, heart=None, seed=0) -> (main float32 (N, 2), feature float32 (N, 2), info)

`main` is the bed (drones, pads, strings, ostinatos) and is ducked hard under the narration;
`feature` carries the designed moments that must survive it (motif statements, hits on words,
the heartbeat) and is ducked less.

The bell is the key: the Meridian's bell is a minor-third bell on D (hum D2, prime D3, tierce F3,
quint A3), so the score's tonic is the bell's strike note and its motif is the bell's partials
falling: A-F-E-D ("the bell motif"); rising D-E-F-A is the father's.

    depth     low drones whose sub pressure grows with depth (the cue sheet's depth curve), and a
              slow pulse like a ship's engine under the deep scenes
    paper     the Bass interludes (s04, s07, s09's spiral) get a dry pizzicato / col legno / bongo
              ostinato, Bernstein-noir; their tempi are fitted so the words land on the grid:
              s04 at 125.5 BPM (storm, reef, lifeboat, inquiry, captain within 9 ms of a 16th),
              s07 at 125.25 BPM (twice, worth, Thirty-one, part, price within 20 ms), the
              spiral at 85.7 BPM (a beat per tumbler click, 0.7 s)
    silence   the knife's cut stops the music dead (s12 6.03); the heartbeat takes over (s13)
    the bell  from s14 the bell is the tonal centre: brief silence before each toll, D-minor
              support blooming after it, its hum as a pedal in s15, its echo in s16

Instruments (all synthesised): pizzicato bass and violins (Karplus-Strong), col legno (wood click
+ pitched tick), bongos and rim (modal membranes), muted brass stabs (saw stack through an
enveloped low-pass), glass / celesta (inharmonic modal partials), timpani, harp (bright KS),
felt piano (inharmonic additive), string sections (detuned saw ensembles with delayed vibrato,
tremolo, harmonics), pads, the D drone with sub, a sub-pulse "engine", the heartbeat.
"""
from __future__ import annotations

import functools
import math

import numpy as np
from scipy import signal as _sg

from audio import dsp
from audio.dsp import (SR, TWO_PI, db2lin, exp_env, karplus_strong, n_of, onepole_lp, saturate, saw, sos, t_axis,
                       tv_lowpass)

from . import cuesheet as CS
from . import sfx_salvage as S

SR2 = 24000
_NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
         "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def m(name):
    return 12 * (int(name[-1]) + 1) + _NOTE[name[:-1]]


def ms(names):
    return [m(x) for x in names.split()]


def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def _st(x):
    return dsp.to_stereo(np.asarray(x, dtype=np.float64))


def _pan(x, p):
    return dsp.pan_stereo(_st(x), p)


# ============================================================================ instruments (48 kHz, short)
@functools.lru_cache(maxsize=512)
def pizz(midi, vel, dur=0.6, bright=0.5, seed=0):
    """Pizzicato (bass or violins): KS with a soft finger excitation, body formants, finger thump."""
    f0 = hz(midi)
    rng = np.random.default_rng(3571 * midi + int(vel * 100) + 17 * seed)
    L = dur + 0.25
    P = max(2, int(SR / f0))
    exc = onepole_lp(rng.uniform(-1, 1, P), 700 + 2600 * vel * bright)
    exc -= exc.mean()
    exc /= max(1e-9, np.max(np.abs(exc)))
    t60 = (1.6 if f0 < 150 else 0.9) * (110.0 / f0) ** 0.15
    y = karplus_strong(f0, L, excitation=exc, t60=t60, brightness=0.55 - 0.25 * bright, pluck_pos=0.18)
    n = len(y)
    t = t_axis(n)
    nd = n_of(dur)
    if nd < n:
        y[nd:] *= np.exp(-(t[nd:] - dur) / 0.06)
    th = sos(rng.standard_normal(n_of(0.03)), "lowpass", 400 if f0 < 200 else 1200, 2) * exp_env(n_of(0.03), 0.02)
    y[:len(th)] += 0.3 * vel * th
    body = (100, 260, 520) if f0 < 200 else (280, 520, 1100, 2600)
    for b in body:
        y = dsp.biquad(y, "peak", b, 1.4, 2.5)
    y = sos(y, "lowpass", 2400 if f0 < 200 else 5500, 2)
    y = y / max(1e-9, np.max(np.abs(y)))
    return (y * 0.3 * vel ** 1.3).astype(np.float32)


@functools.lru_cache(maxsize=256)
def col_legno(midi, vel, seed=0):
    """Col legno: the wood of the bow striking the string - a dry click and a short pitched tick."""
    f0 = hz(midi)
    rng = np.random.default_rng(911 * midi + seed)
    n = n_of(0.22)
    t = t_axis(n)
    click = dsp.bandpass(rng.standard_normal(n), 1400, 6000, 2) * exp_env(n, 0.012)
    tone = sum(a * np.sin(TWO_PI * f0 * k * t + rng.uniform(0, TWO_PI)) * exp_env(n, 0.09 / k)
               for k, a in ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15)))
    wood = dsp.modal([820.0, 1650.0, 2730.0], [0.03, 0.025, 0.02], [0.6, 0.4, 0.2], n, phases=rng.uniform(0, TWO_PI, 3))
    y = 0.5 * click + 0.6 * tone + 0.4 * wood
    y[:n_of(0.0008)] *= np.linspace(0, 1, n_of(0.0008))
    return (y / max(1e-9, np.max(np.abs(y))) * 0.16 * vel).astype(np.float32)


@functools.lru_cache(maxsize=64)
def bongo(high, vel, seed=0):
    rng = np.random.default_rng(321 + 7 * seed + (1 if high else 0))
    f0 = (395.0 if high else 270.0) * rng.uniform(0.98, 1.02)
    n = n_of(0.45)
    t = t_axis(n)
    f = f0 * (1 + 0.12 * np.exp(-t / 0.012))
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * exp_env(n, 0.16)
    y += 0.45 * np.sin(TWO_PI * np.cumsum(f * 1.59) / SR) * exp_env(n, 0.07)
    y += 0.25 * np.sin(TWO_PI * np.cumsum(f * 2.14) / SR) * exp_env(n, 0.05)
    y += dsp.bandpass(rng.standard_normal(n), 900, 5000, 2) * exp_env(n, 0.008) * 0.6
    y[:n_of(0.0006)] *= np.linspace(0, 1, n_of(0.0006))
    return (y / max(1e-9, np.max(np.abs(y))) * 0.2 * vel).astype(np.float32)


@functools.lru_cache(maxsize=16)
def rim(vel, seed=0):
    rng = np.random.default_rng(77 + seed)
    n = n_of(0.2)
    y = dsp.modal([780.0, 1930.0, 3150.0], [0.05, 0.035, 0.02], [1.0, 0.6, 0.3], n, phases=rng.uniform(0, TWO_PI, 3))
    y += dsp.bandpass(rng.standard_normal(n), 2000, 9000, 2) * exp_env(n, 0.006) * 0.8
    y[:n_of(0.0004)] *= np.linspace(0, 1, n_of(0.0004))
    return (y / max(1e-9, np.max(np.abs(y))) * 0.12 * vel).astype(np.float32)


@functools.lru_cache(maxsize=128)
def glass(midi, vel, dur=2.5, seed=0):
    """Glass / celesta: inharmonic partials, the uppers dying fast; a soft mallet."""
    f0 = hz(midi)
    rng = np.random.default_rng(5003 * midi + seed)
    n = n_of(dur + 0.3)
    parts = ((1.0, 1.0, 2.6), (2.0, 0.35, 1.3), (3.01, 0.18, 0.7), (4.16, 0.12, 0.45), (5.43, 0.06, 0.3), (6.79, 0.04, 0.2))
    fr = [f0 * r for r, _, _ in parts if f0 * r < 15000]
    k = len(fr)
    y = dsp.modal(fr, [t * (440.0 / f0) ** 0.2 for _, _, t in parts[:k]], [a for _, a, _ in parts[:k]], n,
                  phases=rng.uniform(0, TWO_PI, k), attack=0.0015)
    y += dsp.modal([f + 0.8 for f in fr[:2]], [2.4, 1.2], [0.3, 0.1], n, phases=rng.uniform(0, TWO_PI, 2), attack=0.0015)
    y = dsp.fade(y, 0.0, 0.3)
    return (y / max(1e-9, np.max(np.abs(y))) * 0.14 * vel).astype(np.float32)


@functools.lru_cache(maxsize=32)
def timp(midi, vel, seed=0):
    f0 = hz(midi)
    rng = np.random.default_rng(1009 * midi + seed)
    n = n_of(3.0)
    t = t_axis(n)
    f = f0 * (1 + 0.06 * np.exp(-t / 0.05))
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * exp_env(n, 2.0)
    y += 0.45 * np.sin(TWO_PI * np.cumsum(f * 1.504) / SR) * exp_env(n, 1.1)
    y += 0.25 * np.sin(TWO_PI * np.cumsum(f * 1.742) / SR) * exp_env(n, 0.7)
    y += 0.3 * np.sin(TWO_PI * f0 * 0.5 * t) * exp_env(n, 1.4)
    y += sos(rng.standard_normal(n), "lowpass", 700 + 900 * vel, 2) * exp_env(n, 0.035) * 0.5
    y[:n_of(0.002)] *= np.linspace(0, 1, n_of(0.002))
    return (y / max(1e-9, np.max(np.abs(y))) * 0.32 * vel).astype(np.float32)


@functools.lru_cache(maxsize=64)
def harp(midi, vel, seed=0):
    f0 = hz(midi)
    rng = np.random.default_rng(2207 * midi + seed)
    P = max(2, int(SR / f0))
    exc = onepole_lp(rng.uniform(-1, 1, P), 3500.0)
    exc -= exc.mean()
    y = karplus_strong(f0, 2.6, excitation=exc / max(1e-9, np.max(np.abs(exc))), t60=2.2 * (220.0 / f0) ** 0.3,
                       brightness=0.25, pluck_pos=0.3)
    y = sos(y, "lowpass", 6000, 2)
    y = dsp.fade(y, 0.0, 0.4)
    return (y / max(1e-9, np.max(np.abs(y))) * 0.13 * vel).astype(np.float32)


@functools.lru_cache(maxsize=256)
def piano(midi, vel, dur, seed=0):
    """Felt piano: inharmonic additive partials, hammer comb, two-stage decay, felt thump."""
    f0 = hz(midi)
    rng = np.random.default_rng(7919 * midi + seed)
    n = n_of(dur + (0.6 if f0 > 200 else 0.9))
    t = t_axis(n)
    B = 0.00005 * 2.0 ** ((midi - 21) / 16.0)
    x0 = 0.12 + 0.01 * rng.uniform(-1, 1)
    bright = 1.2 + 5.0 * vel ** 1.5
    out = np.zeros((n, 2))
    for k in range(1, int(min(22, 8000.0 / f0)) + 1):
        fk = k * f0 * math.sqrt(1 + B * k * k)
        a = k ** -0.85 * abs(math.sin(math.pi * k * x0)) ** 0.7 * math.exp(-(k - 1) / bright)
        if a < 2e-4:
            continue
        t1 = float(np.clip(5.0 * (261.6 / f0) ** 0.55 / (1 + 0.11 * (k - 1) ** 1.25), 0.15, 14.0))
        mm = min(n, n_of(t1 * 4.2))
        env = 0.7 * np.power(10.0, -3.0 * t[:mm] / t1) + 0.3 * np.power(10.0, -3.0 * t[:mm] / (3 * t1))
        for ch in (0, 1):
            d = (0.35 + 0.25 * ch) * 5.8e-4 * (1 if k % 2 else -1)
            p1, p2 = rng.uniform(0, TWO_PI, 2)
            out[:mm, ch] += 0.5 * a * env * (np.sin(TWO_PI * fk * (1 + d) * t[:mm] + p1) + np.sin(TWO_PI * fk * (1 - d) * t[:mm] + p2))
    nd = n_of(dur)
    if nd < n:
        out[nd:] *= np.exp(-(t[nd:] - dur) / (0.1 if f0 > 150 else 0.2))[:, None]
    ka = n_of(0.002 + 0.004 * (1 - vel))
    out[:ka] *= np.linspace(0, 1, ka)[:, None] ** 1.5
    nh = n_of(0.04)
    th = sos(rng.standard_normal(nh), "lowpass", 500 + 2400 * vel, 2) * exp_env(nh, 0.025)
    out[:nh] += (0.05 * th * vel)[:, None]
    return (out * 0.3 * vel ** 1.6).astype(np.float32)


def brass(midis, dur, vel, seed=0, bright=1.0):
    """Muted brass stab / chord (48 kHz): saw stacks through an enveloped low-pass, a buzz of
    growl, tongue attack."""
    rng = np.random.default_rng(4111 + seed)
    n = n_of(dur + 0.35)
    t = t_axis(n)
    out = np.zeros((n, 2))
    for i, mi in enumerate(midis):
        f = hz(mi)
        for ch in range(2):
            det = 1.0 + rng.uniform(-0.003, 0.003)
            vib = 1.0 + 0.003 * np.sin(TWO_PI * 5.2 * t + rng.uniform(0, TWO_PI)) * np.clip((t - 0.25) / 0.4, 0, 1)
            out[:, ch] += saw(f * det * vib, n, phase0=rng.uniform())
    att = 0.012
    env = np.clip(t / att, 0, 1) ** 1.2 * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.09))
    env *= 0.8 + 0.2 * np.exp(-t / 0.15)
    cut = 250.0 + (1800.0 * bright * vel) * (0.35 + 0.65 * np.exp(-t / 0.12))
    for ch in range(2):
        out[:, ch] = tv_lowpass(out[:, ch], cut, q=1.3, block=64)
    out = dsp.biquad(out, "peak", 1250.0, 2.0, 5.0)              # the mute's nasal formant
    out *= env[:, None] * (1.0 + 0.08 * np.sin(TWO_PI * 31.0 * t))[:, None]
    out = saturate(out * 0.6, 1.6)
    return (out / max(1e-9, np.max(np.abs(out))) * 0.2 * vel).astype(np.float32)


def sub_hit(f0=55.0, f1=32.0, dur=2.0, vel=1.0):
    n = n_of(dur)
    t = t_axis(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.15)
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * exp_env(n, dur * 0.8)
    y[:n_of(0.004)] *= np.linspace(0, 1, n_of(0.004))
    y = y + 0.15 * sos(saturate(y * 2.5, 2.0), "bandpass", (70.0, 300.0), 2)
    return (_st(y) * 0.35 * vel).astype(np.float32)


def noise_swell(dur, vel=1.0, seed=0, lo=1500.0, hi=9000.0):
    """Reverse-cymbal-like swell ending on its last sample (place it to END on a hit)."""
    rng = np.random.default_rng(6101 + seed)
    n = n_of(dur)
    t = t_axis(n)
    x = dsp.bandpass(rng.standard_normal(n), lo, hi, 2)
    x = dsp.tv_lowpass(x, lambda tt: 1200.0 + 9000.0 * (tt / dur) ** 2, q=0.8, block=128)
    env = (t / dur) ** 3
    y = dsp.decorrelate(x * env, rng, amount=0.6)
    return (y / max(1e-9, np.max(np.abs(y))) * 0.12 * vel).astype(np.float32)


# ============================================================================ sustained layers (24 kHz)
def strings_note(f0, gate, attack, release, vel, rng, voices=7, detune=9.0, vib=0.0055, trem=None, harmonic=False,
                 bend=None, sr=SR2):
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
        if harmonic:
            s = 0.25 * s + np.sin(TWO_PI * np.cumsum(f) / sr + rng.uniform(0, TWO_PI))
        th = (0.7 * sp + 1) * math.pi / 4
        out[:, 0] += math.cos(th) * s
        out[:, 1] += math.sin(th) * s
    a = max(attack, 0.005)
    env = np.where(t < a, np.sin(0.5 * math.pi * np.clip(t / a, 0, 1)) ** 2, 1.0)
    env = np.where(t > gate, np.power(10.0, -3.0 * np.maximum(t - gate, 0.0) / max(release, 0.02)), env)
    if trem:
        rate, dep = trem
        env = env * (1 - dep + dep * (0.5 + 0.5 * np.sin(TWO_PI * rate * t + rng.uniform(0, TWO_PI)))) ** 1.5
    return out * (env * vel / voices)[:, None]


def pad_voice(f, n, rng, sr=SR2):
    det = ((-9, -2, 7), (-6, 3, 10))
    out = np.zeros((n, 2))
    for ch in range(2):
        for d in det[ch]:
            out[:, ch] += saw(f * 2 ** (d / 1200), n, sr, phase0=rng.uniform()) / 3.0
        out[:, ch] += 0.5 * np.sin(TWO_PI * f * np.arange(n) / sr + rng.uniform(0, TWO_PI))
    return out


# ============================================================================ the plan
class Plan:
    def __init__(self, C, heart=None):
        self.C = C
        self.N = n_of(C.duration)
        self.total = C.duration
        self.ev = []              # (t, fn, bus, send) one-shot renders (48 kHz stereo)
        self.strings = []         # (t, gate, [midi], vel, attack, release, kw, bus, send)
        self.chords = []          # (t0, t1, [midi]) pad
        self.lv = dict(pad=[], drone=[], pulse=[])
        self.cut = []             # pad low-pass (t, Hz)
        self.mask = []            # (t0, t1, fade_out, fade_in)
        self.marks = []           # (t, label)
        self.pulse_bpm = []       # (t, bpm) for the sub-pulse "engine"
        self.heart_times = heart

    def g(self, sid, t=0.0):
        return self.C.g(sid, t)

    def w(self, sid, word, n=0):
        return self.C.w(sid, word, n)

    def we(self, sid, word, n=0):
        return self.C.we(sid, word, n)

    # one-shot helpers -------------------------------------------------------------
    def add(self, t, x, bus="main", send="hall", gain=1.0, pan=0.0):
        self.ev.append((t, x, bus, send, gain, pan))

    def pz(self, t, names, vel=0.7, dur=0.5, bus="main", send="room", bright=0.5, pan=0.0):
        for k, nm in enumerate(names.split() if isinstance(names, str) else names):
            mi = m(nm) if isinstance(nm, str) else nm
            self.add(t, lambda mi=mi, k=k: pizz(mi, round(vel, 2), round(dur, 2), bright, k), bus, send, pan=pan)

    def cl(self, t, name, vel=0.6, bus="main", seed=0, pan=0.0):
        mi = m(name)
        self.add(t, lambda: col_legno(mi, round(vel, 2), seed % 4), bus, "room", pan=pan)

    def bg(self, t, high, vel=0.6, bus="main", seed=0, pan=0.0):
        self.add(t, lambda: bongo(bool(high), round(vel, 2), seed % 4), bus, "room", pan=pan)

    def rm(self, t, vel=0.6, bus="main", seed=0):
        self.add(t, lambda: rim(round(vel, 2), seed % 4), bus, "room", pan=0.15)

    def gl(self, t, names, vel=0.6, dur=2.5, bus="feature", seed=0, pan=0.0):
        for k, nm in enumerate(names.split()):
            mi = m(nm)
            self.add(t, lambda mi=mi, k=k: glass(mi, round(vel, 2), dur, seed + k), bus, "hall", pan=pan)

    def tp(self, t, name, vel=0.7, bus="feature"):
        mi = m(name)
        self.add(t, lambda: timp(mi, round(vel, 2)), bus, "hall")

    def hp(self, t, name, vel=0.5, bus="main", seed=0, pan=0.0):
        mi = m(name)
        self.add(t, lambda: harp(mi, round(vel, 2), seed % 3), bus, "hall", pan=pan)

    def pn(self, t, names, vel=0.5, dur=1.5, bus="feature"):
        for nm in names.split():
            mi = m(nm)
            self.add(t, lambda mi=mi: piano(mi, round(vel, 2), round(dur, 2)), bus, "hall", pan=float(np.clip((mi - 60) / 50.0, -0.4, 0.4)))

    def br(self, t, names, dur=0.3, vel=0.7, bus="feature", seed=0, bright=1.0):
        mids = tuple(ms(names))
        self.add(t, lambda: brass(mids, dur, vel, seed, bright), bus, "hall")

    def sub(self, t, f0=55.0, f1=32.0, dur=2.0, vel=1.0, bus="feature"):
        self.add(t, lambda: sub_hit(f0, f1, dur, vel), bus, None)

    def swell_to(self, t_hit, dur, vel=1.0, bus="main", seed=0):
        self.add(t_hit - dur, lambda: noise_swell(dur, vel, seed), bus, "hall")

    def st(self, t, gate, names, vel, attack=1.0, release=1.2, bus="main", send="hall", **kw):
        self.strings.append((t, gate, ms(names), vel, attack, release, kw, bus, send))

    def chord(self, t0, t1, names):
        self.chords.append((t0, t1, ms(names)))

    def level(self, layer, *pts):
        self.lv[layer].extend(pts)

    def silence(self, t0, t1, fade_out=0.005, fade_in=0.05, label="music out"):
        self.mask.append((t0, t1, fade_out, fade_in))
        self.marks.append((t0, label))

    def mark(self, t, label):
        self.marks.append((t, label))

    # ======================================================================= composition
    def compose(self):
        C = self.C
        g, w, we = self.g, self.w, self.we
        L = self.level
        tr = C.trans

        # ------------------------------------------------------------------ s01 the line
        # silence for the red line; a low D enters with the first word; the 31 figures fall as a
        # pizzicato cascade, the last on "Meridian"; the bell motif A-F-E-D on "later / I / down / home"
        L("drone", (0.0, -80), (w("s01", "thirtyone") - 0.1, -80), (w("s01", "thirtyone") + 2.2, -16), (g("s01", 4.2), -15),
          (g("s01", 6.0), -11), (g("s01", 8.6), -11), (g("s02", 0.6), -17))
        L("pad", (0.0, -80), (g("s01", 4.3), -80), (g("s01", 6.4), -13), (g("s01", 9.3), -13), (g("s02", 1.2), -18))
        self.cut += [(0.0, 300), (g("s01", 6.0), 420), (g("s01", 9.0), 700), (g("s02", 1.0), 900)]
        self.chord(g("s01", 4.3), g("s01", 7.6), "D2 A2 D3 F3")
        self.chord(g("s01", 7.6), g("s01", 9.2), "Bb1 F2 D3 F3")
        self.chord(g("s01", 9.2), g("s02", 1.5), "D2 A2 D3 F3 A3")
        self.gl(w("s01", "men"), "D6", 0.35, 1.6, bus="main")
        a, b = w("s01", "down"), w("s01", "meridian")
        casc = "D5 C5 A4 G4 F4 E4 D4 C4 A3".split()
        for k, nm in enumerate(casc):
            tt = a + (b - a) * k / len(casc)
            self.pz(tt, nm, 0.5 - 0.02 * k, 0.35, bus="feature", bright=0.7, pan=-0.5 + 0.11 * k)
        self.pz(b, "D2", 0.85, 1.4, bus="feature", bright=0.4)
        self.tp(b, "D2", 0.45)
        self.mark(b, "last figure falls")
        self.st(g("s01", 4.25), 1.9, "D5 A5", 0.22, attack=1.6, release=0.6, harmonic=True, voices=4, detune=4)
        for word, nm, v in (("later", "A4", 0.5), ("i", "F4", 0.46), ("down", "E4", 0.48), ("home", "D4", 0.58)):
            t = w("s01", word, 1 if word == "down" else 0)
            self.gl(t, nm, v, 2.6 if word == "home" else 1.8)
            self.st(t, 1.1 if word != "home" else 2.0, nm[:-1] + "3", 0.28, attack=0.25, release=1.0, bus="feature", voices=5)
        self.mark(w("s01", "later"), "bell motif A-F-E-D")

        # ------------------------------------------------------------------ s02 cash (dusk, the deal)
        s = "s02"
        self.st(g(s, 0.0), 1.4, "A5", 0.18, attack=0.6, release=1.2, harmonic=True, voices=3, detune=3)
        L("pad", (g(s, 1.5), -18), (g(s, 3.0), -15), (g(s, 9.5), -15), (g(s, 11.0), -13), (g(s, 14.0), -12),
          (w(s, "it"), -12), (w(s, "it") + 0.05, -80))
        L("drone", (g(s, 1.5), -19), (g(s, 10.0), -17), (w(s, "it") - 0.05, -15), (w(s, "it") + 0.3, -80))
        self.cut += [(g(s, 2.0), 650), (g(s, 10.0), 520), (w(s, "it"), 900)]
        self.chord(g(s, 1.5), w(s, "name"), "D2 A2 F3")
        self.chord(w(s, "name"), w(s, "men"), "Bb1 F2 D3")
        self.chord(w(s, "men"), w(s, "plan"), "G1 D2 Bb2 D3")
        self.chord(w(s, "plan"), w(s, "it") + 0.05, "A1 E2 G2 Bb2")
        self.pz(w(s, "paid"), "D2", 0.55, 0.9, bright=0.35)
        self.pz(w(s, "cash"), "D2", 0.7, 0.6, bus="feature", bright=0.4)
        self.gl(w(s, "cash") + 0.02, "A5", 0.32, 1.4, bus="feature")
        self.pz(w(s, "name"), "Bb1", 0.55, 1.2, bright=0.3)
        self.st(w(s, "men") + 0.6, w(s, "it") - w(s, "men") - 0.6, "A2 Eb3", 0.42, attack=3.0, release=0.05,
                trem=(11.0, 0.55), bus="main")
        self.gl(w(s, "using"), "D7", 0.22, 1.5, bus="feature")
        t = w(s, "it")
        self.tp(t, "D2", 0.8)
        self.sub(t, 60.0, 36.0, 1.6, 0.8)
        self.br(t, "D2 A2 D3", 0.22, 0.75, seed=1, bright=0.8)
        self.pz(t, "D1", 0.9, 1.0, bus="feature", bright=0.3)
        self.mark(t, "CLANK")

        # ------------------------------------------------------------------ s03 title, the long way down
        s = "s03"
        t_title = g(s, 1.55)
        L("drone", (g(s, 0.6), -80), (g(s, 1.4), -15), (g(s, 5.0), -12), (g(s, 13.5), -9), (tr(s)[1] - 0.3, -80))
        L("pad", (g(s, 1.3), -80), (t_title, -11), (g(s, 4.8), -13), (g(s, 6.0), -14), (g(s, 11.3), -13), (tr(s)[0], -13),
          (tr(s)[1] - 0.3, -80))
        self.cut += [(g(s, 1.0), 800), (g(s, 4.5), 1100), (g(s, 6.0), 650), (g(s, 11.0), 380), (g(s, 11.3), 700)]
        self.chord(t_title, g(s, 5.0), "D2 A2 D3 F3 A3")
        self.st(t_title, 3.0, "D3 A3 D4 F4", 0.5, attack=0.18, release=2.2, bus="feature")
        self.br(t_title, "D3 F3 A3", 1.8, 0.48, seed=3, bright=0.6)
        self.tp(t_title, "D2", 0.55)
        for k, nm in enumerate("D3 F3 A3 D4 F4 A4 D5".split()):
            self.hp(t_title + 0.19 * k, nm, 0.45 + 0.03 * k, seed=k, pan=-0.45 + 0.15 * k)
        self.mark(t_title, "title")
        # the lament bass under the descent, the bell motif high, the lamp's A-major warmth
        lam = [(g(s, 5.0), "D2"), (g(s, 7.2), "C2"), (g(s, 9.0), "Bb1")]
        for k, (t0, nm) in enumerate(lam):
            t1 = lam[k + 1][0] if k + 1 < len(lam) else g(s, 11.3)
            self.st(t0, t1 - t0 + 0.2, nm + " " + nm[:-1] + str(int(nm[-1]) + 1), 0.4, attack=1.0, release=0.9)
        self.chord(g(s, 5.0), g(s, 7.2), "D2 A2 F3")
        self.chord(g(s, 7.2), g(s, 9.0), "C2 G2 Eb3")
        self.chord(g(s, 9.0), g(s, 11.3), "Bb1 F2 D3")
        for t0, nm, v in ((g(s, 5.9), "A4", 0.42), (g(s, 7.3), "F4", 0.4), (g(s, 8.7), "E4", 0.4), (g(s, 10.0), "D4", 0.45)):
            self.gl(t0, nm, v, 2.0, bus="main")
        self.st(g(s, 8.15), 0.9, "D5 A5", 0.16, attack=0.4, release=1.1, harmonic=True, voices=3, detune=3)   # fish
        t = g(s, 11.3)
        self.chord(t, tr(s)[1], "A1 E2 C#3 E3")
        self.st(t, tr(s)[0] - t + 0.3, "A2 E3 C#4", 0.38, attack=0.5, release=0.8)
        self.gl(t + 0.03, "C#5", 0.32, 2.4)
        self.mark(t, "lamp: A major")

        # ------------------------------------------------------------------ s04 calm night (ostinato 125.5)
        self._s04()

        # ------------------------------------------------------------------ s05 the meridian
        s = "s05"
        deep = w(s, "deep")
        conv = w(s, "convenient")
        L("drone", (tr("s04")[0] + 0.2, -80), (tr("s04")[1] + 0.3, -11), (g(s, 3.0), -10), (deep, -7), (deep + 2.5, -10),
          (g(s, 9.6), -13), (conv, -12), (C.end(s), -11))
        L("pad", (tr("s04")[1], -80), (g(s, 1.5), -17), (g(s, 3.5), -14), (deep, -8), (deep + 2.0, -13), (g(s, 9.5), -18),
          (conv, -18), (conv + 1.0, -14), (C.end(s), -14))
        self.cut += [(g(s, 0.0), 350), (g(s, 3.0), 450), (deep, 1500), (deep + 3.0, 500), (conv, 420), (C.end(s), 500)]
        self.chord(g(s, 0.5), g(s, 3.4), "D2 A2 D3")
        self.chord(g(s, 3.4), deep + 2.5, "D2 A2 D3 Eb3 F3")
        self.chord(deep + 2.5, conv, "D2 A2 F3")
        self.chord(conv, C.end("s06"), "D2 A2 D3 F3 A3")
        self.st(g(s, 3.4), deep - g(s, 3.4), "D3 A3 Eb4 F4", 0.42, attack=2.6, release=0.15)
        self.swell_to(deep, 2.4, 0.9, seed=5)
        self.tp(deep - 0.55, "D2", 0.35)
        self.tp(deep - 0.28, "D2", 0.45)
        self.tp(deep, "D2", 0.95)
        self.sub(deep, 55.0, 34.0, 3.0, 1.0)
        self.br(deep, "D2 A2 D3 F3 Bb3", 1.6, 0.8, seed=5, bright=0.7)
        self.st(deep, 3.6, "D2 A2 D3 F3 A4", 0.62, attack=0.06, release=2.4, bus="feature")
        self.st(deep, 4.8, "A5", 0.2, attack=0.8, release=1.5, harmonic=True, voices=3, detune=3)
        self.mark(deep, "the wreck: deep")
        self.st(conv + 0.25, 4.2, "D3 F3 A3", 0.32, attack=1.2, release=1.5, bus="feature")     # the bell's own chord
        self.pz(conv, "D2", 0.45, 1.5, bright=0.3)
        self.mark(conv, "muffled bell")

        # ------------------------------------------------------------------ s06 outward
        s = "s06"
        ins = w(s, "inside")
        L("drone", (g(s, 0.0), -11), (ins, -10), (C.end(s) - 0.02, -7), (C.end(s), -80))
        L("pad", (g(s, 0.0), -15), (ins, -14), (C.end(s) - 0.02, -12), (C.end(s), -80))
        self.cut += [(g(s, 0.0), 450), (ins, 380), (C.end(s), 900)]
        self.chord(C.end("s05"), ins, "D2 A2 Eb3")
        self.chord(ins, C.end(s), "D2 Ab2 Eb3")
        self.st(g(s, 0.2), ins - g(s, 0.2), "D2 Eb2", 0.4, attack=1.5, release=0.5, trem=(7.0, 0.5))
        self.pz(w(s, "holes"), "D1", 0.75, 1.2, bus="feature", bright=0.25)
        self.bg(w(s, "holes"), False, 0.5, bus="feature")
        self.st(w(s, "cut"), 1.6, "C#6 D6", 0.12, attack=0.5, release=1.2, harmonic=True, voices=3, detune=2, bus="feature")
        self.st(ins, C.end(s) - ins, "D3 Eb3 Ab3 D4", 0.5, attack=C.end(s) - ins, release=0.01, trem=(13.0, 0.5))
        self.swell_to(C.end(s), 3.2, 1.0, seed=6)
        self.silence(C.end(s), C.end(s) + 0.9, 0.004, 0.02, label="hard cut to black")

        # ------------------------------------------------------------------ s07 the price (ostinato 125.25)
        self._s07()

        # ------------------------------------------------------------------ s08 the shaft
        s = "s08"
        safe = w(s, "safe")
        L("drone", (tr("s07")[0] + 0.3, -80), (tr("s07")[1], -10), (safe, -10), (C.end(s), -9), (g("s09", 1.0), -13))
        L("pad", (tr("s07")[1], -80), (g(s, 1.5), -16), (safe, -14), (C.end(s), -12), (w("s09", "didn't"), -22))
        self.cut += [(g(s, 0.0), 380), (safe, 600), (C.end(s), 500)]
        self.chord(g(s, 0.0), safe, "D2 A2 Ab2")
        self.chord(safe, w("s09", "didn't"), "D2 A2 F3 C#4")
        self.st(g(s, 0.6), safe - g(s, 0.6), "G#3", 0.14, attack=2.0, release=0.8, trem=(15.0, 0.4), voices=4)
        self.pz(w(s, "captain's"), "A1", 0.6, 1.0, bus="feature", bright=0.3)
        self.st(safe, w("s09", "didn't") - safe, "D3 F3 A3 C#4", 0.38, attack=0.7, release=0.6, bus="feature")
        self.gl(safe + 0.02, "C#5", 0.3, 2.6, bus="feature")
        self.mark(safe, "the safe: Dm(maj7)")

        # ------------------------------------------------------------------ s09 birthday / the spiral
        self._s09()

        # ------------------------------------------------------------------ s10 his own hand
        s = "s10"
        fa, od, hd = w(s, "father's"), w(s, "orders"), w(s, "hand")
        L("drone", (g(s, 0.0), -16), (fa, -18), (od - 0.05, -18), (od, -10), (hd, -9), (C.end(s), -9))
        L("pad", (g(s, 0.0), -18), (fa, -12), (od - 0.1, -12), (od + 0.1, -16), (C.end(s), -14))
        self.cut += [(g(s, 0.0), 500), (fa, 900), (od, 400), (C.end(s), 450)]
        prog = [(fa, "Bb1 F2 D3 F3"), (fa + 1.15, "A1 F2 C3 F3"), (fa + 2.3, "G1 D2 Bb2 D3"), (fa + 3.2, "D2 A2 D3 G3")]
        for k, (t0, ch) in enumerate(prog):
            t1 = prog[k + 1][0] if k + 1 < len(prog) else od
            self.chord(t0, t1, ch)
        self.pn(fa, "Bb2 F3 D4", 0.42, 1.2)
        self.pn(fa + 1.15, "A2 F3 C4", 0.38, 1.1)
        self.pn(fa + 2.3, "G2 D3 Bb3", 0.38, 0.9)
        self.pn(fa + 3.2, "D3 G3 A3", 0.36, 0.7)
        self.st(fa, od - fa, "D4 F4", 0.26, attack=1.0, release=0.5, bus="feature", voices=5)
        self.mark(fa, "father (warm)")
        self.chord(od, C.end(s), "D1 Eb2 A2")
        self.st(od, C.end(s) - od, "D2 Eb2 A2", 0.45, attack=0.08, release=0.3)
        self.pz(od, "D1", 0.8, 1.5, bus="feature", bright=0.25)
        self.br(hd, "Eb3 G3 Bb3", 0.25, 0.6, seed=10, bright=0.7)
        self.br(hd, "D2 A2", 0.25, 0.6, seed=11, bright=0.6)
        self.mark(hd, "his own hand")
        self._pulse_run(g(s, 7.0), C.end(s), "D2", 112.0, 0.35, 0.65)

        # ------------------------------------------------------------------ s11 two tugs
        s = "s11"
        L("drone", (g(s, 0.0), -10), (g(s, 7.3), -11), (C.end(s), -14))
        L("pad", (g(s, 0.0), -15), (g(s, 7.3), -12), (C.end(s), -10))
        self.cut += [(g(s, 0.0), 420), (g(s, 7.3), 500), (C.end(s), 1600)]
        self.chord(g(s, 0.0), g(s, 7.3), "D2 A2 Eb3")
        self.chord(g(s, 7.3), tr(s)[1], "D2 A2 D3 E3 A3")
        self._pulse_run(g(s, 0.0), w(s, "two") - 0.3, "D2", 112.0, 0.3, 0.3)
        self.pz(w(s, "something"), "Bb1", 0.6, 1.4, bright=0.3)
        for word, nm in (("two", "D2"), ("tugs", "D2")):
            t = w(s, word)
            self.pz(t, nm, 0.95, 0.5, bus="feature", bright=0.45)
            self.pz(t, "D3", 0.5, 0.35, bus="feature", bright=0.6)
            self.bg(t, False, 0.65, bus="feature")
            self.mark(t, word)
        self.st(g(s, 7.3), C.end(s) - g(s, 7.3) + 0.6, "D3 A3 E4", 0.36, attack=2.4, release=0.8)
        self.st(g(s, 8.0), C.end(s) - g(s, 8.0) + 0.6, "D5 A5", 0.15, attack=1.6, release=0.8, harmonic=True, voices=3)

        # ------------------------------------------------------------------ s12 the cut
        s = "s12"
        tight, then, cut = w(s, "tight"), w(s, "then"), w(s, "cut")
        L("drone", (g(s, 0.0), -12), (tight, -10), (cut - 0.01, -7), (cut, -80))
        L("pad", (g(s, 0.0), -14), (tight, -14), (cut - 0.01, -10), (cut, -80))
        self.cut += [(g(s, 0.0), 500), (tight, 500), (cut, 1400)]
        self.chord(g(s, 0.0), tight, "D2 A2 F3")
        self.chord(tight, cut + 0.1, "D2 A2 Eb3 G3")
        # the waiting: a slow pizz pulse that quickens from the line going tight to the knife
        t = g(s, 0.6)
        k = 0
        while t < cut - 0.05:
            prog = (t - g(s, 0.6)) / (cut - g(s, 0.6))
            bpm = 78.0 + 70.0 * max(0.0, (t - tight) / (cut - tight)) ** 1.3 if t > tight else 78.0
            self.pz(t, "D2" if k % 2 == 0 else "A1", 0.45 + 0.4 * prog, 0.3, bright=0.35)
            t += 60.0 / bpm / (2.0 if t > tight else 1.0)
            k += 1
        self.st(tight, cut - tight, "D3 Eb3", 0.32, attack=0.3, release=0.01, trem=(12.0, 0.6),
                bend=lambda tt, d=cut - tight: 2 ** (3.0 * np.clip(tt / d, 0, 1) ** 2 / 12))
        self.st(tight + 0.5, cut - tight - 0.5, "A4 Bb4", 0.16, attack=cut - tight - 0.6, release=0.01, trem=(14.0, 0.5),
                bend=lambda tt, d=cut - tight - 0.5: 2 ** (2.0 * np.clip(tt / d, 0, 1) ** 2 / 12))
        self.st(then, cut - then, "A6", 0.12, attack=0.25, release=0.01, harmonic=True, voices=3, detune=3, bus="feature")
        self.swell_to(cut, 2.2, 0.8, seed=12)
        self.silence(cut, C.end("s13") + 0.5, 0.004, 0.0, label="THE CUT: silence")
        self.mark(tight, "tight")
        self.mark(then, "knife")

        # ------------------------------------------------------------------ s13 one breath (heartbeat, silence)
        s = "s13"
        calm = w(s, "calm")
        self.mask[-1] = (cut, calm - 0.02, 0.004, 0.25)          # silence (the heartbeat sits outside the mask)
        L("drone", (calm, -80), (w(s, "my"), -80), (g(s, 9.5), -16), (C.end(s), -13))
        L("pad", (calm, -80), (w(s, "my"), -80), (g(s, 9.0), -16), (C.end(s), -13))
        self.cut += [(calm, 600), (C.end(s), 900)]
        self.st(calm, 3.0, "D6", 0.1, attack=0.6, release=1.8, harmonic=True, voices=3, detune=2, bus="feature")
        self.mark(calm, "calm")
        for word, nm, v in (("my", "D4", 0.42), ("father", "E4", 0.42), ("taught", "F4", 0.44), ("that", "A4", 0.5)):
            t = w(s, word)
            self.pn(t, nm, v, 1.6 if word == "that" else 0.9)
        self.mark(w(s, "my"), "father motif rising")
        self.chord(w(s, "my"), C.end(s), "D2 A2 D3")
        self.st(g(s, 9.0), C.end(s) - g(s, 9.0) + 0.5, "D3 A3", 0.3, attack=1.6, release=0.6)

        # ------------------------------------------------------------------ s14 the bell
        s = "s14"
        bell = w(s, "bell")
        toll = bell + 0.82
        L("drone", (C.start(s), -13), (g(s, 6.4), -11), (bell - 0.05, -10), (bell, -80), (toll + 0.35, -80), (toll + 2.5, -13),
          (C.end(s), -12))
        L("pad", (C.start(s), -13), (bell - 0.05, -11), (bell, -80), (toll + 0.4, -80), (toll + 2.0, -12), (C.end(s), -11))
        self.cut += [(C.start(s), 700), (bell, 1100), (toll, 500), (C.end(s), 500)]
        rise = [(C.start(s), "D3"), (g(s, 2.4), "E3"), (g(s, 4.6), "F3"), (g(s, 6.4), "A3")]
        for k, (t0, nm) in enumerate(rise):
            t1 = rise[k + 1][0] if k + 1 < len(rise) else bell
            self.st(t0, t1 - t0 + 0.15, nm, 0.3 + 0.04 * k, attack=0.9, release=0.2, voices=6)
            self.st(t0 + 0.3, t1 - t0, nm[:-1] + "2", 0.24, attack=1.0, release=0.2, voices=5)
        self.chord(C.start(s), g(s, 6.4), "D2 A2 D3")
        self.chord(g(s, 6.4), bell, "Bb1 F2 D3 A3")
        self._pulse_run(g(s, 0.5), bell - 0.1, "D2", 100.0, 0.3, 0.6)
        self.silence(bell + 0.01, toll + 0.3, 0.06, 0.4, label="breath before the toll")
        self.chord(toll + 0.3, C.end("s15"), "D2 A2 D3")
        self.st(toll + 0.35, C.end(s) - toll + 1.5, "D2 A2 D3 F3", 0.34, attack=1.6, release=1.6, bus="feature")
        self.mark(toll, "TOLL 1")

        # ------------------------------------------------------------------ s15 my name
        s = "s15"
        toll2 = g(s, 6.8)
        L("drone", (C.start(s), -12), (g(s, 4.5), -11), (toll2 - 0.45, -9), (toll2 - 0.3, -80), (toll2 + 0.15, -80),
          (toll2 + 1.2, -9), (tr(s)[1], -14))
        L("pad", (C.start(s), -12), (toll2 - 0.45, -10), (toll2 - 0.3, -80), (toll2 + 0.2, -80), (toll2 + 1.0, -8), (tr(s)[1] + 0.5, -15))
        self.cut += [(C.start(s), 500), (toll2 - 0.3, 900), (toll2 + 0.6, 1300), (tr(s)[1], 600)]
        self.st(C.start(s), 4.0, "D2 A2", 0.3, attack=1.2, release=1.5)
        self.st(g(s, 3.4), toll2 - 0.35 - g(s, 3.4), "D3 A3 Bb3", 0.34, attack=2.5, release=0.12, trem=(9.0, 0.35))
        self.silence(toll2 - 0.3, toll2 - 0.01, 0.25, 0.01, label="silence before the toll")
        self.chord(toll2 + 0.15, tr(s)[1] + 2.0, "D1 D2 A2 D3 F3 A3")
        self.st(toll2 + 0.12, 2.2, "D2 A2 D3 F3 A3 D4", 0.72, attack=0.7, release=3.2, bus="feature")
        self.br(toll2 + 0.15, "D2 A2 D3 F3", 2.0, 0.65, seed=15, bright=0.55)
        self.tp(toll2, "D2", 0.9)
        self.sub(toll2, 50.0, 36.7, 3.5, 0.9)
        self.mark(toll2, "TOLL 2")

        # ------------------------------------------------------------------ s16 the sea keeps
        s = "s16"
        L("drone", (C.start(s), -14), (w(s, "back"), -10), (w(s, "back") + 3.0, -13), (w(s, "me") - 0.3, -16), (g(s, 15.2), -80))
        L("pad", (C.start(s), -15), (g(s, 2.0), -13), (w(s, "justice"), -12), (w(s, "you"), -14), (g(s, 15.2), -80))
        self.cut += [(C.start(s), 500), (w(s, "back"), 650), (w(s, "justice"), 800), (w(s, "you"), 500)]
        self.chord(tr("s15")[1], w(s, "back"), "D2 A2 D3 F3")
        self.chord(w(s, "back"), w(s, "justice"), "D2 A2 C3 F3")
        self.chord(w(s, "justice"), w(s, "revenge"), "Bb1 F2 D3 F3")
        self.chord(w(s, "revenge"), w(s, "you"), "A1 E2 Bb2 D3")
        self.chord(w(s, "you"), g(s, 15.2), "D2 A2 D3")
        for word, nm, v in (("sea", "A4", 0.44), ("keeps", "F4", 0.42), ("everything", "E4", 0.42), ("until", "D4", 0.46)):
            self.gl(w(s, word), nm, v, 2.4, bus="feature")
            self.pn(w(s, word), nm[:-1] + "3", 0.28, 1.2)
        self.mark(w(s, "sea"), "bell motif (sea keeps)")
        self.st(w(s, "back") - 0.3, 3.4, "D2 A2", 0.4, attack=1.5, release=2.0)
        self.tp(w(s, "back"), "D2", 0.35)
        self.st(w(s, "justice"), w(s, "revenge") - w(s, "justice") + 0.3, "Bb2 F3 D4", 0.3, attack=0.8, release=0.8, bus="feature")
        self.st(w(s, "revenge"), w(s, "you") - w(s, "revenge") + 0.2, "A2 Bb3 E4", 0.26, attack=0.6, release=0.7, bus="feature")
        self.st(w(s, "you"), g(s, 14.9) - w(s, "you"), "D3 A3 D4", 0.3, attack=0.5, release=1.0, bus="feature")
        self.mark(w(s, "you"), "open fifth")
        self.pz(w(s, "me"), "D2", 0.6, 1.2, bus="feature", bright=0.35)
        self.gl(w(s, "me") + 0.01, "D5", 0.3, 1.8)
        self.silence(g(s, 15.2), self.total + 1.0, 1.2, 0.0, label="end")

        # the engine: a slow sub pulse under the deep scenes
        self.pulse_bpm = [(g("s03", 7.0), 50.0), (C.end("s03"), 52.0), (C.start("s05"), 52.0), (C.end("s06"), 54.0),
                          (C.start("s08"), 52.0), (g("s09", 1.0), 52.0), (C.start("s10"), 50.0), (C.end("s11"), 56.0)]
        L("pulse", (g("s03", 6.5), -80), (g("s03", 9.0), -6), (tr("s03")[0], -4), (tr("s03")[1], -80),
          (tr("s04")[1], -80), (g("s05", 2.0), -4), (C.end("s06") - 0.02, -2), (C.end("s06"), -80),
          (tr("s07")[1], -80), (g("s08", 1.5), -4), (w("s09", "didn't"), -6), (w("s09", "didn't") + 0.4, -80),
          (g("s10", 6.6), -80), (g("s10", 7.5), -6), (g("s11", 7.0), -4), (C.end("s11"), -80))

    # ------------------------------------------------------------------ ostinatos
    def _ostinato(self, origin, sixteenth, bars, harmony, accents, end_t, bus="main", vel=1.0, seed=0, bongos=True):
        """Bass-noir ostinato: pizz bass 'D . . D . . F . D . . C . . A .', col legno on the
        off-16ths, bongos (low on 1 and 3, high on the syncopations), rim on 2 and 4.
        harmony: per-bar list of (root, fifth, low7, low6) note names."""
        pat_b = {0: 0, 3: 0, 6: 2, 8: 0, 11: 3, 14: 4}
        for b in range(bars):
            h = harmony[min(b, len(harmony) - 1)]
            for k in range(16):
                t = origin + (16 * b + k) * sixteenth
                if t >= end_t - 1e-3 or t < origin - 1e-6:
                    continue
                if k in pat_b:
                    nm = (h[0], h[0], h[1], h[0], h[2], h[3])[list(pat_b).index(k)]
                    self.pz(t, nm, (0.82 if k in (0, 8) else 0.66) * vel, 0.32, bus=bus, bright=0.45)
                if k in (2, 6, 10, 14) and k not in pat_b:
                    self.cl(t, h[4] if len(h) > 4 else "A4", 0.5 * vel, bus=bus, seed=k + b, pan=0.35)
                if k in (2, 10) or (k == 6 and b % 2 == 1):
                    self.cl(t, h[5] if len(h) > 5 else "D5", 0.42 * vel, bus=bus, seed=k + b + 2, pan=-0.35)
                if bongos:
                    if k in (0, 8):
                        self.bg(t, False, 0.55 * vel, bus=bus, seed=k + b, pan=-0.2)
                    elif k in (3, 6, 11, 14):
                        self.bg(t, True, (0.42 + 0.08 * (k == 14)) * vel, bus=bus, seed=k + b, pan=0.25)
                if k in (4, 12):
                    self.rm(t, 0.45 * vel, bus=bus, seed=k + b)

    def _s04(self):
        C, w, g = self.C, self.w, self.g
        s = "s04"
        six = 60.0 / 125.5 / 4.0
        storm = w(s, "storm")
        origin = storm - 8 * six
        end_t = g(s, 13.3)
        harmony = [("D2", "A1", "C2", "A1", "A4", "D5"), ("D2", "A1", "C2", "A1", "A4", "D5"),
                   ("Bb1", "F2", "A1", "F1", "F4", "D5"), ("A1", "E2", "G1", "E1", "E4", "C#5"),
                   ("D2", "A1", "Eb2", "A1", "A4", "Eb5"), ("D2", "A1", "Eb2", "A1", "A4", "Eb5"),
                   ("A1", "E2", "Bb1", "E1", "E4", "C#5"), ("D2", "A1", "C2", "A1", "A4", "D5")]
        self._ostinato(origin, six, 8, harmony, None, end_t, bus="main", vel=1.0, seed=4)
        L = self.level
        L("drone", (C.trans("s03")[0], -9), (C.trans("s03")[1], -80), (end_t - 0.4, -80), (end_t, -14), (C.trans(s)[1], -12))
        L("pad", (C.trans("s03")[1], -80), (g(s, 0.3), -22), (end_t - 0.5, -20), (end_t, -80))
        self.chord(g(s, 0.3), end_t, "D2 A2 F3")
        # stabs on the words (the scene's paper hits)
        rf, lb, inq, cap = w(s, "reef"), w(s, "lifeboat"), w(s, "inquiry"), w(s, "captain")
        self.br(storm, "D3 F3 Ab3", 0.18, 0.75, seed=41, bright=1.0)
        self.tp(storm, "D2", 0.6)
        self.br(self.we(s, "storm"), "D4", 0.08, 0.5, seed=42, bright=1.2)          # the tear
        self.br(rf, "C3 Eb3 Gb3", 0.22, 0.7, seed=43, bright=0.9)
        self.bg(rf, False, 0.8)
        for k in range(8):                                   # the lifeboats pop on: rising pizz violins
            t = lb + k * 0.12
            self.pz(t, ("D4 F4 A4 D5 F5 A5 D6 F6".split())[k], 0.4 + 0.03 * k, 0.2, bus="feature", bright=0.7, pan=-0.4 + 0.11 * k)
        sink0, sink1 = g(s, 6.7), g(s, 7.8)
        self.st(sink0, sink1 - sink0, "A3 E4", 0.4, attack=0.1, release=0.6, bus="main",
                bend=lambda tt, d=sink1 - sink0: 2 ** (-7.0 * np.clip(tt / d, 0, 1) ** 1.5 / 12))
        self.br(sink0, "A2 E3 G3", sink1 - sink0, 0.55, seed=44, bright=0.6)
        self.tp(sink1, "A1", 0.5)
        self.br(inq, "D3 F3 Bb3 Eb4", 0.16, 0.85, seed=45, bright=1.1)
        self.add(inq, lambda: rim(0.9, 1), "feature", "room")
        self.br(w(s, "someone"), "A3", 0.1, 0.5, seed=46)
        self.br(w(s, "blame"), "Eb3 A3", 0.14, 0.7, seed=47, bright=1.0)
        self.br(w(s, "chose") - 0.1, "Eb3 Bb3", 0.12, 0.6, seed=48)
        self.swell_to(cap, 1.0, 0.7, seed=4)
        self.br(cap, "D2 A2 D3 F3 Bb3", 0.5, 1.0, seed=49, bright=1.0)
        self.tp(cap, "D2", 0.95)
        self.sub(cap, 58.0, 36.7, 1.4, 0.7)
        self.mark(storm, "s04 ostinato 125.5")
        self.mark(cap, "captain: target")
        # the hole: a falling low glissando into s05's dark
        hole = g(s, 13.3)
        self.st(hole, 1.2, "D3 A3", 0.4, attack=0.03, release=0.9, bend=lambda tt: 2 ** (-12.0 * np.clip(tt / 1.2, 0, 1) ** 1.2 / 12))
        self.sub(hole, 48.0, 30.0, 2.0, 0.8)
        self.silence(hole + 0.02, C.trans(s)[0] + 0.4, 0.05, 0.6, label="into the hole")

    def _s07(self):
        C, w, g = self.C, self.w, self.g
        s = "s07"
        six = 60.0 / 125.25 / 4.0
        twice = w(s, "twice")
        origin = twice - 16 * six
        price = w(s, "price")
        end_t = price + 2 * six
        harmony = [("D2", "A1", "C2", "A1", "A4", "D5"), ("D2", "A1", "C2", "A1", "A4", "D5"),
                   ("G1", "D2", "F1", "D1", "Bb4", "D5"), ("A1", "E2", "G1", "E1", "C#5", "E5"),
                   ("D2", "A1", "C2", "A1", "A4", "D5")]
        self._ostinato(origin, six, 5, harmony, None, end_t, bus="main", vel=1.0, seed=7)
        # the torch: a low drone and a tense high tremolo while the circle is cut
        self.st(g(s, 0.0), 1.15, "D2 Ab2", 0.36, attack=0.15, release=0.5, trem=(16.0, 0.45))
        self.st(g(s, 0.0), 1.15, "A5 Bb5", 0.08, attack=0.4, release=0.4, harmonic=True, voices=3, detune=2)
        self.tp(origin, "D2", 0.7)
        self.br(twice, "D3 F3 A3", 0.14, 0.7, seed=71, bright=1.0)
        self.br(twice + 2 * six, "D4 F4 A4", 0.14, 0.6, seed=72, bright=1.1)      # x2: the octave echo
        self.br(w(s, "worth"), "Bb2 D3 F3 Ab3", 0.3, 0.85, seed=73, bright=1.0)
        self.bg(w(s, "worth"), False, 0.8)
        t31 = w(s, "thirtyone")
        for k in range(8):                                   # the crew: a soft military rim roll in 32nds
            self.rm(t31 + k * six / 2, 0.25 + 0.04 * k, seed=k)
        self.br(t31, "D3 A3", 0.25, 0.55, seed=74)
        self.chord(t31, w(s, "part"), "D2 A2 F3")
        part = w(s, "part")
        for k, nm in enumerate(("A2 D3", "G2 C3", "F2 Bb2", "E2 A2")):     # bars rise: falling steps
            self.br(part + k * 2 * six, nm, 0.2, 0.6 + 0.05 * k, seed=75 + k, bright=0.6)
        self.br(price, "D2 A2 D3", 0.6, 0.95, seed=79, bright=0.8)
        self.tp(price, "D2", 0.9)
        self.sub(price, 55.0, 34.0, 1.6, 0.8)
        self.mark(twice, "s07 ostinato 125.25")
        self.mark(price, "price")
        L = self.level
        L("drone", (g(s, 0.0), -14), (end_t, -14), (end_t + 0.3, -80))
        L("pad", (g(s, 0.0), -80), (end_t, -80))

    def _s09(self):
        C, w, g = self.C, self.w, self.g
        s = "s09"
        didnt, bday = w(s, "didn't"), w(s, "birthday")
        clicks = [g(s, 3.9), g(s, 4.6), g(s, 5.3)]
        collapse = g(s, 7.2)
        L = self.level
        L("drone", (g(s, 0.5), -13), (didnt, -18), (bday, -15), (clicks[0], -14), (collapse, -9), (collapse + 0.05, -16),
          (C.end(s), -15))
        L("pad", (didnt, -22), (didnt + 0.4, -80), (collapse + 0.5, -80), (g(s, 8.5), -16), (C.end(s), -14))
        self.cut += [(didnt, 600), (collapse + 0.5, 700), (C.end(s), 800)]
        self.st(didnt, bday - didnt + 0.3, "C#6", 0.1, attack=0.3, release=0.6, harmonic=True, voices=3, detune=2, bus="feature")
        self.mark(didnt, "hush")
        # Vertigo: Dm(maj7) arpeggios in contrary motion, a beat per tumbler click (0.7 s), the
        # direction flipping on each click; accelerating into the collapse
        up = ms("D3 F3 A3 C#4 D4 F4 A4 C#5")
        dn = ms("C#5 A4 F4 D4 C#4 A3 F3 D3")
        beat = 0.7
        t = clicks[0]
        i = 0
        seg = 0
        while t < collapse - 0.04:
            seg_now = sum(1 for c in clicks if t >= c - 1e-6) - 1
            if seg_now != seg:
                seg, i = seg_now, 0
            a, b = (up, dn) if seg % 2 == 0 else (dn, up)
            self.hp(t, _nm(a[i % 8]), 0.5, seed=i, pan=-0.45)
            self.hp(t, _nm(b[i % 8]), 0.42, seed=i + 1, pan=0.45)
            if i % 2 == 0:
                self.cl(t, _nm(a[i % 8] + 12), 0.25, bus="main", seed=i)
            step = beat / 4.0
            if t >= clicks[-1]:
                step *= 1.0 - 0.5 * (t - clicks[-1]) / (collapse - clicks[-1])
            nxt = [c for c in clicks if c > t + 1e-6]
            t_next = t + step
            if nxt and t_next > nxt[0] - 0.02:
                t_next = nxt[0]
            t = t_next
            i += 1
        self.chord(clicks[0], collapse, "D2 A2 F3 C#4")
        self.st(clicks[0], collapse - clicks[0], "D3 F3 A3 C#4", 0.3, attack=1.5, release=0.1, trem=(8.0, 0.25))
        for c in clicks:
            self.pz(c, "D2", 0.75, 0.6, bus="feature", bright=0.35)
            self.gl(c, "C#6", 0.22, 1.0, bus="feature")
        self.swell_to(collapse, 1.6, 0.8, seed=9)
        self.br(collapse, "D2 A2 D3 Eb3", 0.4, 0.8, seed=91, bright=0.7)
        self.tp(collapse, "D2", 0.8)
        self.silence(collapse + 0.06, collapse + 0.75, 0.25, 0.6, label="spiral collapses")
        self.chord(collapse + 0.6, C.end(s) + 1.0, "Bb1 F2 D3 F3")
        self.st(g(s, 8.4), C.end(s) - g(s, 8.4) + 1.0, "F3 Bb3 D4", 0.3, attack=1.0, release=1.2, bus="main")
        self.gl(g(s, 8.5), "F5", 0.25, 2.2, bus="main")
        self.mark(clicks[0], "Vertigo arpeggios 85.7")
        self.mark(g(s, 8.5), "the book")

    def _pulse_run(self, t0, t1, name, bpm, v0, v1):
        """Low pizz eighth-notes from t0 to t1 crescendo v0 -> v1."""
        step = 60.0 / bpm / 2.0
        t = t0
        k = 0
        while t < t1 - 0.05:
            u = (t - t0) / max(t1 - t0, 1e-3)
            self.pz(t, name if k % 2 == 0 else name, (v0 + (v1 - v0) * u) * (1.0 if k % 2 == 0 else 0.7), 0.22, bright=0.3)
            t += step
            k += 1


def _nm(midi):
    names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    return f"{names[midi % 12]}{midi // 12 - 1}"


# ============================================================================ rendering
def _up2(x):
    return np.stack([_sg.resample_poly(np.ascontiguousarray(x[:, c]), 2, 1) for c in range(x.shape[1])], axis=1)


def _bp(points, n, sr, default=-80.0):
    if not points:
        return np.full(n, default)
    pts = sorted(points)
    return np.interp(np.arange(n) / sr, [p[0] for p in pts], [p[1] for p in pts])


def _sparse_wet(x, ir, wet_db, gap=1.5):
    act = np.max(np.abs(x), axis=1) > 1e-7
    out = np.zeros((len(x) + len(ir), 2))
    idx = np.nonzero(act)[0]
    if len(idx) == 0:
        return out[:len(x)]
    brk = np.nonzero(np.diff(idx) > gap * SR)[0]
    starts = np.concatenate([[idx[0]], idx[brk + 1]])
    ends = np.concatenate([idx[brk], [idx[-1]]])
    for a, b in zip(starts, ends):
        dsp.mix_into(out, dsp.convolve(x[a:b + 1].mean(axis=1), ir) * db2lin(wet_db), a)
    return out[:len(x)]


PAD_GAIN = db2lin(-12.0)
DRONE_GAIN = db2lin(-2.0)


def render_score(C=None, heart=None, seed=0, debug=False):
    """heart: (beat_times, strengths) for the s12-s14 heartbeat (cuesheet.heartbeat_plan)."""
    C = C or CS.Clock()
    plan = Plan(C)
    plan.compose()
    N = plan.N
    N2 = int(math.ceil(plan.total * SR2)) + 1
    rng = np.random.default_rng(dsp.stable_seed("salvage-score", seed))
    main = np.zeros((N, 2))
    feat = np.zeros((N, 2))
    send_hall = np.zeros((N, 2))
    send_room = np.zeros((N, 2))
    info = dict(events=len(plan.ev), strings=len(plan.strings))
    layers = {}

    # ---- depth -> drone sub & filter
    dpts = CS.depth_points(C)
    t2 = np.arange(N2) / SR2
    depth = np.interp(t2, [p[0] for p in dpts], [p[1] for p in dpts])

    # ---- pad (24 kHz)
    pad = np.zeros((N2, 2))
    spans = {}
    for t0, t1, notes in sorted(plan.chords):
        for mm in notes:
            lst = spans.setdefault(mm, [])
            if lst and abs(lst[-1][1] - t0) < 0.06:
                lst[-1][1] = max(lst[-1][1], t1)
            else:
                lst.append([t0, t1])
    XF = 0.8
    for mm, lst in spans.items():
        for t0, t1 in lst:
            a = max(0, int((t0 - XF / 2) * SR2))
            b = min(N2, int((t1 + XF) * SR2))
            if b <= a:
                continue
            v = pad_voice(hz(mm), b - a, rng)
            tt = np.arange(a, b) / SR2
            env = np.sin(0.5 * np.pi * np.clip((tt - (t0 - XF / 2)) / XF, 0, 1))
            env = env * np.cos(0.5 * np.pi * np.clip((tt - (t1 - XF / 2)) / XF, 0, 1))
            pad[a:b] += v * env[:, None] * (0.8 if mm < 45 else 0.6)
    cut = np.clip(_bp(plan.cut, N2, SR2, 600.0), 120, 6000) * (1.0 - 0.35 * depth)
    for ch in range(2):
        pad[:, ch] = tv_lowpass(pad[:, ch], cut, q=0.75, sr=SR2, block=256)
    pad *= db2lin(_bp(plan.lv["pad"], N2, SR2))[:, None]

    # ---- drone (24 kHz): D1 / D2 / A2 with a sub that grows with depth, a slow engine pulse
    f = 36.708
    dr = (0.5 * np.sin(TWO_PI * 2 * f * t2) + 0.25 * np.sin(TWO_PI * 3 * f * t2 + 1.0)) * (1 + 0.12 * dsp.smooth_noise(N2, 0.1, rng, SR2))
    sv = saw(2 * f * (1 + 0.002 * dsp.smooth_noise(N2, 0.2, rng, SR2)), N2, SR2) + saw(2 * f * 1.004, N2, SR2, 0.3)
    sv = tv_lowpass(sv, 140.0 + 260.0 * (1 - depth), q=0.9, sr=SR2, block=256) * 0.22
    sub = np.sin(TWO_PI * f * t2) * (0.25 + 0.95 * depth ** 1.5)
    bpm = np.interp(t2, [p[0] for p in plan.pulse_bpm], [p[1] for p in plan.pulse_bpm]) if plan.pulse_bpm else np.full(N2, 52.0)
    ph = np.cumsum(bpm / 60.0) / SR2
    throb = np.clip(1.0 - (ph % 1.0) / 0.35, 0, 1) ** 2 + 0.6 * np.clip(1.0 - ((ph - 0.28) % 1.0) / 0.3, 0, 1) ** 2
    pulse = np.sin(TWO_PI * 0.75 * f * t2) * throb * db2lin(_bp(plan.lv["pulse"], N2, SR2)) * (0.3 + 0.7 * depth)
    drn = dr + sv + sub
    drn = drn + 0.2 * sos(saturate(drn * 2.0, 2.0), "highpass", 90, 2, sr=SR2)
    drn *= 0.22 * db2lin(_bp(plan.lv["drone"], N2, SR2))
    pulse = 0.2 * (pulse + 0.25 * sos(saturate(pulse * 3.0, 2.0), "bandpass", (80.0, 260.0), 2, sr=SR2))
    low = np.stack([drn, drn], axis=1) * DRONE_GAIN + pad * PAD_GAIN
    low[:, 0] += pulse
    low[:, 1] += pulse

    # ---- strings (24 kHz)
    s_main = np.zeros((N2, 2))
    s_feat = np.zeros((N2, 2))
    s_send = np.zeros((N2, 2))
    for (t, gate, notes, vel, att, rel, kw, bus, send) in plan.strings:
        for mm in notes:
            x = strings_note(hz(mm), gate, att, rel, vel, rng, **kw)
            dsp.mix_into(s_feat if bus == "feature" else s_main, x, int(t * SR2), 0.25)
            if send:
                dsp.mix_into(s_send, x, int(t * SR2), 0.25 * 0.6)
    for buf in (s_main, s_feat, s_send):
        for ch in range(2):
            y = sos(buf[:, ch], "highpass", 60, 2, sr=SR2)
            y = sos(y, "lowpass", 4200, 2, sr=SR2)
            y = dsp.biquad(y, "peak", 420, 1.0, 2.0, sr=SR2)
            buf[:, ch] = dsp.biquad(y, "peak", 2600, 1.2, 1.5, sr=SR2)
    lowbus = dsp.pad_to(_up2(low), N)
    main += lowbus + dsp.pad_to(_up2(s_main), N)
    feat += dsp.pad_to(_up2(s_feat), N)
    send_hall += lowbus * 0.3 + dsp.pad_to(_up2(s_send), N)
    if debug:
        layers["drone+pad"] = lowbus.astype(np.float32)
    del pad, low, s_main, s_feat, s_send, lowbus, drn, sv, sub, dr, pulse, throb, depth

    # ---- one-shots (48 kHz)
    for (t, fn, bus, send, gain, pan) in plan.ev:
        x = np.asarray(fn(), dtype=np.float64)
        x = _st(x) if x.ndim == 1 else x
        if pan:
            x = dsp.pan_stereo(x, pan)
        dsp.mix_into(feat if bus == "feature" else main, x, n_of(t), gain)
        if send == "hall":
            dsp.mix_into(send_hall, x, n_of(t), gain * 0.5)
        elif send == "room":
            dsp.mix_into(send_room, x, n_of(t), gain * 0.6)

    # ---- the heartbeat (s12 end - s14): feature bus, outside the silence mask
    hb = np.zeros(N)
    if heart:
        beats, strengths = heart
        hb = S.heartbeat_track(beats, N, seed=12, strengths=strengths)
        hb = sos(hb, "lowpass", 220.0, 2)

    # ---- reverbs
    main += _sparse_wet(send_hall, S.space_ir("score_hall"), -7.0)
    main += _sparse_wet(send_room, dsp.make_ir("small_room"), -14.0)
    del send_hall, send_room

    # ---- designed silences (after the reverb: they cut the tails too)
    gate = np.ones(N)
    for (t0, t1, fo, fi) in plan.mask:
        a, b = n_of(max(0.0, t0 - fo)), min(N, n_of(t1 + fi))
        if b <= a:
            continue
        seg = np.arange(a, b) / SR
        gdn = np.clip((t0 - seg) / max(fo, 1e-4), 0, 1)
        gup = np.clip((seg - t1) / max(fi, 1e-4), 0, 1)
        gate[a:b] = np.minimum(gate[a:b], np.maximum(gdn, gup))
    main *= gate[:, None]
    feat *= gate[:, None]
    feat += _st(hb) * 0.63                     # felt more than heard: the silence leads
    info["marks"] = sorted(plan.marks)
    info["silences"] = [(round(a, 3), round(b, 3)) for a, b, _, _ in plan.mask]
    if debug:
        info["layers"] = layers
    return main.astype(np.float32), feat.astype(np.float32), info


if __name__ == "__main__":
    import os
    import time
    t0 = time.time()
    C = CS.Clock()
    main, feat, info = render_score(C, heart=CS.heartbeat_plan(C))
    print(f"score rendered in {time.time() - t0:.1f}s, {info['events']} one-shots, {info['strings']} string notes")
    mix = main + feat
    print("music integrated", round(dsp.loudness_integrated(mix), 2), "TP", round(dsp.true_peak_db(mix), 2))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
    os.makedirs(out, exist_ok=True)
    dsp.write_wav(os.path.join(out, "score_preview.wav"), mix * 0.5, bits=24)
