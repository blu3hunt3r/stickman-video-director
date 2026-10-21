"""The score: one noir identity (D minor, 72 BPM) from the first frame to the last.

    render_score(tl, cue_scenes=None) -> (main float32 (N, 2), feature float32 (N, 2), info)

`main` is the bed of the score (pad, drone, groove, pulses, strings); `feature` carries the
designed musical moments that must survive under the narration (motif statements, soft hits,
clue stabs, heartbeat) - mix.py ducks it less than `main`.

Instruments (all synthesised):
  felt piano ..... additive, inharmonic partials f_k = k f0 sqrt(1 + B k^2), hammer-position comb,
                   velocity-dependent brightness, two-stage decay, beating unison pairs, felt
                   thump + key noise, damper at note-off; optional pitch bend (the copycat)
  pad ............ detuned PolyBLEP saws (per-channel detune = width), slow time-varying low-pass
  sub drone ...... D1 / D2 / A1 sines, lightly saturated so phones hear it
  strings ........ detuned saw ensemble, delayed vibrato, slow attack, body EQ (S10, S13, S15, S18)
  upright bass ... Karplus-Strong with soft finger excitation, body resonances, finger thump
  brushes/ride ... beat-locked brush swirls, brush taps on 2 & 4, synthesized ride (inharmonic
                   modal cymbal) in a swung 'spang-a-lang', hi-hat foot chick
  tension pulse .. filtered saw/square 8ths (S4, S10-S12, S14)
  chase .......... 108 BPM: 16th bass ostinato, toms, hats, spiccato strings (S11 3.5 s -> 'caught')
  heartbeat ...... sfx 'heartbeat' (S12-S13), yields to a picture-synced heartbeat cue

Motif "No Face" = A3 D4 F4 E4, stated on the words in production-bible section 7.
"""
from __future__ import annotations

import functools
import math

import numpy as np

from . import dsp, sfx
from .dsp import (SR, TWO_PI, db2lin, exp_env, karplus_strong, n_of, onepole_lp, saturate, saw, sos,
                  square, t_axis, tv_lowpass, white, pink)

SR2 = 24000                  # render rate for the dark, band-limited layers (pad, strings, drone)
BPM = 72.0
BEAT = 60.0 / BPM            # 0.8333 s
CHASE_BPM = 108.0
_NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
         "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
MOTIF = ("A3", "D4", "F4", "E4")


def m(name):
    return 12 * (int(name[-1]) + 1) + _NOTE[name[:-1]]


def ms(names):
    return [m(x) for x in names.split()]


def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


# ============================================================================ instruments
@functools.lru_cache(maxsize=512)
def piano_note(midi, vel, dur, bend=None, seed=0):
    """Felt piano note, stereo float32. bend = (start_s, length_s, semitones)."""
    f0 = hz(midi)
    rng = np.random.default_rng(7919 * midi + seed)
    tail = 0.55 if f0 > 200 else 0.9
    n = n_of(dur + tail)
    t = t_axis(n)
    B = 0.00005 * 2.0 ** ((midi - 21) / 16.0)
    x0 = 0.12 + 0.01 * rng.uniform(-1, 1)
    bright = 1.3 + 6.0 * vel ** 1.5
    ratio = None
    if bend:
        b0, bl, bs = bend
        u = np.clip((t - b0) / bl, 0, 1)
        ratio = 2.0 ** (bs * u * u * (3 - 2 * u) / 12.0)
    out = np.zeros((n, 2))
    kmax = int(min(26, 9000.0 / f0))
    for k in range(1, kmax + 1):
        fk = k * f0 * math.sqrt(1 + B * k * k)
        if fk > 9000:
            break
        a = k ** -0.85 * abs(math.sin(math.pi * k * x0)) ** 0.7 * math.exp(-(k - 1) / bright)
        if a < 2e-4:
            continue
        t1 = float(np.clip(5.0 * (261.6 / f0) ** 0.55 / (1 + 0.11 * (k - 1) ** 1.25), 0.15, 14.0))
        t2 = t1 * 3.0
        mm = min(n, n_of(t2 * 1.4))
        env = 0.7 * np.power(10.0, -3.0 * t[:mm] / t1) + 0.3 * np.power(10.0, -3.0 * t[:mm] / t2)
        for ch in (0, 1):
            d = (0.35 + 0.25 * ch) * 5.8e-4 * (1 if k % 2 else -1)      # ~0.6-1 cent unison spread
            p1, p2 = rng.uniform(0, TWO_PI, 2)
            if ratio is None:
                s = np.sin(TWO_PI * fk * (1 + d) * t[:mm] + p1) + np.sin(TWO_PI * fk * (1 - d) * t[:mm] + p2)
            else:
                ph = np.cumsum(fk * ratio[:mm]) / SR
                s = np.sin(TWO_PI * ph * (1 + d) + p1) + np.sin(TWO_PI * ph * (1 - d) + p2)
            out[:mm, ch] += 0.5 * a * env * s
    # damper at note-off
    nd = n_of(dur)
    if nd < n:
        tau = 0.08 + (0.12 if f0 < 150 else 0.0)
        out[nd:] *= np.exp(-(t[nd:] - dur) / tau)[:, None]
        dn = sos(rng.standard_normal(n_of(0.05)), "lowpass", 260, 2) * exp_env(n_of(0.05), 0.04) * 0.004
        k = min(len(dn), n - nd)
        out[nd:nd + k] += dn[:k, None]
    # felt hammer thump + key/mechanics noise
    att = 0.0018 + 0.004 * (1 - vel)
    ka = min(n, n_of(att))
    out[:ka] *= np.linspace(0, 1, ka)[:, None] ** 1.5
    nh = n_of(0.04)
    th = sos(rng.standard_normal(nh), "lowpass", 500 + 2400 * vel, 2) * exp_env(nh, 0.025)
    knock = np.sin(TWO_PI * min(f0 * 2, 180.0) * t_axis(nh)) * exp_env(nh, 0.03)
    out[:nh] += ((0.05 * th + 0.03 * knock) * vel)[:, None]
    pan = float(np.clip((midi - 60) / 48.0, -0.45, 0.45))
    out[:, 0] *= math.cos((pan + 1) * math.pi / 4) * math.sqrt(2)
    out[:, 1] *= math.sin((pan + 1) * math.pi / 4) * math.sqrt(2)
    return (out * (0.32 * vel ** 1.7)).astype(np.float32)


@functools.lru_cache(maxsize=256)
def bass_note(midi, vel, dur, bright=0.6):
    """Upright bass pluck: Karplus-Strong with a soft, period-length finger excitation."""
    f0 = hz(midi)
    rng = np.random.default_rng(3571 * midi + int(vel * 100))
    L = dur + 0.3
    n = n_of(L)
    P = int(SR / f0)
    exc = onepole_lp(rng.uniform(-1, 1, P), 600 + 1700 * vel)
    exc = onepole_lp(exc, 900 + 1500 * vel)
    exc -= exc.mean()
    exc /= max(1e-9, np.max(np.abs(exc)))
    y = karplus_strong(f0, L, excitation=exc, t60=2.6 * (55.0 / f0) ** 0.25, brightness=bright)
    t = t_axis(n)
    nd = n_of(dur)
    y[nd:] *= np.exp(-(t[nd:] - dur) / 0.07)
    th = sos(rng.standard_normal(n_of(0.04)), "lowpass", 320, 2) * exp_env(n_of(0.04), 0.03)
    y[:len(th)] += 0.35 * vel * th
    y = dsp.biquad(y, "peak", 100, 1.2, 4.0)
    y = dsp.biquad(y, "peak", 260, 1.5, 2.0)
    y = sos(y, "lowpass", 2300, 2)
    y = saturate(y * 0.8, 1.4)
    return (dsp.to_stereo(y) * 0.24 * vel ** 1.4).astype(np.float32)


@functools.lru_cache(maxsize=64)
def pulse_note(midi, vel, dur, bright=1.0):
    """Tension-pulse synth: saw + sub square through an enveloped low-pass."""
    f = hz(midi)
    n = n_of(dur + 0.08)
    t = t_axis(n)
    x = 0.6 * saw(f, n) + 0.4 * square(f * 0.5, n)
    cut = 140 + 1300 * bright * vel * np.exp(-t / 0.05)
    x = tv_lowpass(x, cut, q=1.1, block=32)
    x *= np.clip(t / 0.003, 0, 1) * np.exp(-t / max(dur * 0.45, 0.02))
    return (dsp.to_stereo(x) * 0.42 * vel).astype(np.float32)


@functools.lru_cache(maxsize=16)
def ride_hit(seed):
    rng = np.random.default_rng(900 + seed)
    n = n_of(3.0)
    fr = np.exp(rng.uniform(np.log(380), np.log(9500), 24))
    t60 = rng.uniform(1.3, 3.0, 24) * (1000.0 / fr) ** 0.2
    amps = rng.uniform(0.5, 1.0, 24) / np.sqrt(fr / 500.0)
    x = dsp.modal(fr, t60, amps, n, phases=rng.uniform(0, TWO_PI, 24))
    x += dsp.bandpass(rng.standard_normal(n), 3000, 11000, 2) * exp_env(n, 2.0) * 0.12
    x += dsp.modal(np.array([5200.0, 7100.0]), np.array([0.09, 0.07]), np.array([0.5, 0.3]), n)
    x = sos(x, "highpass", 350, 2)
    return (dsp.decorrelate(x, rng, amount=0.4) * 0.04).astype(np.float32)


@functools.lru_cache(maxsize=16)
def brush_tap(seed):
    rng = np.random.default_rng(700 + seed)
    n = n_of(0.4)
    t = t_axis(n)
    x = dsp.bandpass(rng.standard_normal(n), 1500, 6500, 2) * np.clip(t / 0.004, 0, 1) * exp_env(n, 0.17)
    x += 0.5 * np.sin(TWO_PI * 185 * t) * exp_env(n, 0.06)
    x += 0.4 * sos(rng.standard_normal(n), "highpass", 4000, 2) * exp_env(n, 0.22)
    return (dsp.to_stereo(x) * 0.04).astype(np.float32)


@functools.lru_cache(maxsize=8)
def hat_chick(seed):
    rng = np.random.default_rng(800 + seed)
    n = n_of(0.08)
    x = dsp.bandpass(rng.standard_normal(n), 6000, 11000, 2) * exp_env(n, 0.03)
    x += 0.3 * np.sin(TWO_PI * 420 * t_axis(n)) * exp_env(n, 0.01)
    return (dsp.to_stereo(x) * 0.025).astype(np.float32)


@functools.lru_cache(maxsize=16)
def tom(f0, seed=0, decay=0.3):
    rng = np.random.default_rng(600 + seed)
    n = n_of(decay * 2 + 0.1)
    t = t_axis(n)
    f = f0 * (1 + 0.45 * np.exp(-t / 0.03))
    x = np.sin(TWO_PI * np.cumsum(f) / SR) * exp_env(n, decay)
    x += sos(rng.standard_normal(n), "lowpass", 1400, 2) * exp_env(n, 0.03) * 0.5
    return (dsp.to_stereo(saturate(x, 1.5)) * 0.25).astype(np.float32)


def timpani(f0, rng):
    n = n_of(2.6)
    t = t_axis(n)
    f = f0 * (1 + 0.08 * np.exp(-t / 0.05))
    x = np.sin(TWO_PI * np.cumsum(f) / SR) * exp_env(n, 1.5)
    x += 0.4 * np.sin(TWO_PI * np.cumsum(f * 1.5) / SR) * exp_env(n, 0.8)
    x += 0.35 * np.sin(TWO_PI * f0 * 0.5 * t) * exp_env(n, 1.1)
    x += sos(rng.standard_normal(n), "lowpass", 900, 2) * exp_env(n, 0.03) * 0.6
    x[:n_of(0.002)] *= np.linspace(0, 1, n_of(0.002))
    return dsp.to_stereo(x) * 0.22


def strings_note(f0, gate, attack, release, vel, rng, voices=8, detune=10.0, vib=0.0055, bend=None,
                 trem=None, sr=SR2):
    """Section strings voice at `sr`: detuned saws (random spread, slow pitch drift so the
    ensemble does not beat periodically), each with its own delayed vibrato."""
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
    env = np.where(t > gate, np.power(10.0, -3.0 * np.maximum(t - gate, 0.0) / max(release, 0.02)), env)
    if trem:
        rate, depth = trem
        env = env * (1 - depth + depth * (0.5 + 0.5 * np.sin(TWO_PI * rate * t)))
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
    def __init__(self, tl, cue_scenes=None):
        from engine.timing import SceneTiming
        self.tl = tl
        self.N = int(round(tl["total_frames"] * SR / tl["fps"]))
        self.total = self.N / SR
        self.T = {s["id"]: SceneTiming(s["id"]) for s in tl["scenes"]}
        self.cue_scenes = cue_scenes or {}
        self.piano = []         # (t, midi, vel, dur, bus, bend)
        self.bass = []          # (t, midi, vel, dur, bright)
        self.chords = []        # (t0, t1, [midi])          pad
        self.lv = dict(pad=[], drone=[])   # (t, dB) automation
        self.cut = []           # (t, Hz) pad low-pass
        self.strings = []       # (t, gate, [midi], vel, attack, release, kw, bus)
        self.kit = []           # (t, kind, vel, seed)
        self.pulses = []        # (t, midi, vel, dur, bright, bus)
        self.events = []        # (t, fn(rng)->stereo48k, bus)  free-form hits
        self.heart = []         # (t0, t1, bpm0, bpm1, gain_db, lp, sid)
        self.mask = []          # (t0, t1, fade_out_s, fade_in_s): music silent inside
        self.groove_span = None
        self.marks = []         # (t, label) for QA plots

    # timing helpers -------------------------------------------------------
    def g(self, sid, t):
        return self.T[sid].start + t

    def w(self, sid, word, n=0):
        return self.T[sid].start + self.T[sid].at(word, n)

    def end(self, sid):
        return self.T[sid].start + self.T[sid].duration

    # event helpers --------------------------------------------------------
    def pn(self, t, names, vel, dur, bus="main", bend=None):
        for x in (names.split() if isinstance(names, str) else names):
            self.piano.append((t, m(x) if isinstance(x, str) else x, vel, dur, bus, bend))

    def motif(self, times, vels, last_dur, bus="feature", notes=MOTIF, bend=None, durs=None):
        for i, (t, v, nm) in enumerate(zip(times, vels, notes)):
            if i < 3:
                d = durs[i] if durs else max(0.25, (times[i + 1] - t) + 0.25)
                self.pn(t, nm, v, d, bus)
            else:
                self.pn(t, nm, v, last_dur, bus, bend)
        self.marks.append((times[0], "motif"))

    def chord(self, t0, t1, names):
        self.chords.append((t0, t1, ms(names)))

    def level(self, layer, *pts):
        self.lv[layer].extend(pts)

    def silence(self, t0, t1, fade_out=0.01, fade_in=0.05):
        self.mask.append((t0, t1, fade_out, fade_in))
        self.marks.append((t0, "music out"))

    def st(self, t, gate, names, vel, attack=1.0, release=1.2, bus="main", **kw):
        self.strings.append((t, gate, ms(names), vel, attack, release, kw, bus))

    # ======================================================================= composition
    def compose(self):
        g, w, end = self.g, self.w, self.end
        L = self.level
        S = {s["id"]: s for s in self.tl["scenes"]}

        # ------------------------------------------------------------- S01 golden hook
        s = "s01"
        L("drone", (0.0, -80), (g(s, 0.3), -80), (g(s, 2.6), -13), (g(s, 8.5), -11), (w(s, "face", 1), -11),
          (w(s, "face", 1) + 0.25, -15))
        L("pad", (0.0, -80), (g(s, 0.3), -80), (g(s, 3.2), -10), (g(s, 6.0), -9), (w(s, "face", 1) - 0.02, -8),
          (w(s, "face", 1) + 0.07, -80))
        self.cut += [(0.0, 330), (g(s, 5.0), 600), (g(s, 8.4), 900)]
        self.chord(g(s, 0.3), g(s, 6.0), "D2 A2 D3 F3")
        self.chord(g(s, 6.0), w(s, "nobody"), "Bb1 F2 D3 F3")
        self.chord(w(s, "nobody"), w(s, "face", 1) + 0.1, "D2 A2 D3 F3")
        self.pn(w(s, "seven"), "D2 A2", 0.45, 3.0)
        self.pn(w(s, "not"), "D5", 0.27, 1.2)
        self.pn(w(s, "it"), "C#5", 0.24, 1.1)
        self.motif([w(s, "nobody"), w(s, "has"), w(s, "a"), w(s, "face", 1)], [0.5, 0.52, 0.55, 0.64], 1.25)

        # ------------------------------------------------------------- S02 the city
        s = "s02"
        L("pad", (g(s, 0.0), -80), (g(s, 2.4), -10), (g(s, 8.8), -10))
        L("drone", (g(s, 0.0), -13), (end(s), -13))
        self.cut += [(g(s, 0.0), 450), (g(s, 2.8), 1100), (g(s, 3.4), 1300), (g(s, 6.0), 850), (end(s), 700)]
        self.chord(g(s, 0.0), w(s, "under"), "D2 A2 D3 F3 A3")
        self.chord(w(s, "under"), w(s, "i'm"), "Bb1 F2 D3 F3 A3")
        self.chord(w(s, "i'm"), g(s, 8.0), "G2 D3 G3 Bb3")
        self.chord(g(s, 8.0), end(s), "A2 E3 G3 D4")
        self.pn(g(s, 1.95), "D4", 0.34, 1.0)
        self.pn(g(s, 5.30), "F4", 0.32, 0.9)
        self.pn(g(s, 8.45), "E4", 0.34, 1.1)

        # ------------------------------------------------------------- S03 useless evidence
        s = "s03"
        L("pad", (g(s, 0.0), -11), (g(s, 9.0), -10), (g(s, 11.75), -6), (g(s, 11.86), -80))
        L("drone", (g(s, 0.0), -14), (g(s, 11.8), -12))
        self.cut += [(g(s, 0.0), 650), (g(s, 9.0), 800), (g(s, 11.8), 1800)]
        self.chord(g(s, 0.0), g(s, 5.8), "D3 F3 A3")
        self.chord(g(s, 5.8), g(s, 9.08), "G2 D3 G3 Bb3")
        self.chord(g(s, 9.08), end(s), "A2 E3 G3 C#4")
        for word, note in (("faces", 74), ("fingerprints", 77), ("witnesses", 81)):     # pizzicato D5 F5 A5
            self.bass.append((w(s, word), note, 0.55, 0.35, 0.35))
        self.pn(w(s, "circles"), "D4 F4", 0.34, 1.6)
        self.st(g(s, 9.08), end(s) - g(s, 9.08) - 0.05, "A3 E4", 0.5, attack=2.6, release=0.08, trem=(9.0, 0.25))
        self.silence(end(s) - 0.05, end(s) + 0.08, 0.03, 0.05)     # the whip up into black

        # ------------------------------------------------------------- S04 rain murders (tension pulse)
        s = "s04"
        L("pad", (g(s, 0.0), -80), (g(s, 0.4), -12), (g(s, 6.6), -12), (g(s, 7.4), -9), (end(s), -10))
        L("drone", (g(s, 0.0), -10), (end(s), -11))
        self.cut += [(g(s, 0.0), 380), (g(s, 6.8), 420), (g(s, 8.0), 900), (end(s), 1000)]
        self.chord(g(s, 0.0), w(s, "one"), "D2 A2 D3 F3")
        self.chord(w(s, "one"), end(s), "D2 Bb2 D3 F3")
        self._pulse_run(g(s, 0.12), g(s, 8.6), 38, fade_from=g(s, 6.8))
        rng = np.random.default_rng(4)
        for word, k in (("four", 0), ("four", 1), ("one", 0)):
            t = w(s, word, k)
            self.events.append((t, lambda r, f=hz(38): timpani(f, r) * 0.55, "feature"))
            self.pn(t, "D1 A1 D2", 0.42, 1.6, "feature")
            self.marks.append((t, "soft hit"))
        self.pn(w(s, "match"), "A5", 0.25, 1.6)
        self.pn(w(s, "body"), "F5", 0.22, 1.6)

        # ------------------------------------------------------------- S05-S09 investigation groove
        g0 = g("s05", 0.15)
        drop = g("s09", 5.6)
        self.groove_span = (g0, drop)
        bars = [("D3 F3 A3 C#4", [38, None, 33, None]),
                ("D3 F3 A3 C4", [38, 41, 45, 36]),
                ("G2 D3 F3 Bb3", [31, None, 38, None]),
                ("A2 E3 G3 Bb3", [33, 37, 40, 43]),
                ("D3 F3 A3 C#4", [38, None, 45, None]),
                ("Bb2 D3 F3 A3", [34, None, 41, None]),
                ("G2 D3 F3 Bb3", [31, 34, 38, 41]),
                ("A2 E3 G3 Bb3", [33, None, None, None]),       # bar 8: the limp bass (below)
                ("D3 F3 A3 C#4", [38, None, 33, None]),
                ("E3 G3 Bb3 D4", [40, None, 34, None]),
                ("A2 D3 E3 G3", [33, None, 40, 37])]
        L("pad", (g("s05", 0.0), -80), (g0, -14), (drop - 0.05, -13))
        L("drone", (g("s05", 0.0), -15), (drop, -15))
        self.cut += [(g("s05", 0.0), 900), (drop, 900)]
        for b, (ch, line) in enumerate(bars):
            t0 = g0 + 4 * b * BEAT
            if t0 >= drop:
                break
            self.chord(t0, min(drop + 0.02, t0 + 4 * BEAT), ch)
            for k, note in enumerate(line):
                tb = t0 + k * BEAT
                if note is None or tb >= drop:
                    continue
                # length: until the next note (or 2 beats)
                nxt = next((j for j in range(k + 1, 4) if line[j] is not None), 4)
                self.bass.append((tb, note, 0.8 if k == 0 else 0.65, min((nxt - k) * BEAT * 0.92, drop - tb), 0.6))
        # S8 "Short step, long step": the bass limps (short note on Short, long note on long)
        self.bass.append((w("s08", "short"), 40, 0.75, 0.18, 0.6))
        self.bass.append((w("s08", "long"), 45, 0.8, 1.15, 0.6))
        self.bass.append((w("s08", "quarter"), 38, 1.0, 1.4, 0.5))
        self.pn(w("s08", "quarter"), "D2 D3", 0.5, 1.5, "feature")
        # kit: brush swirl every beat (rendered continuously), taps + hat on 2 & 4, ride from bar 3
        nbeats = int((drop - g0) / BEAT) + 1
        for k in range(nbeats):
            tb = g0 + k * BEAT
            if tb >= drop:
                break
            beat_in_bar = k % 4
            if beat_in_bar in (1, 3):
                self.kit.append((tb, "tap", 0.9, k))
                if k >= 4:
                    self.kit.append((tb, "hat", 0.8, k))
            if k >= 8:
                self.kit.append((tb, "ride", 1.0 if beat_in_bar in (1, 3) else 0.75, k % 6))
                if beat_in_bar in (1, 3) and tb + BEAT * 2 / 3 < drop:
                    self.kit.append((tb + BEAT * 2 / 3, "ride", 0.55, (k + 3) % 6))     # swung skip note
        # piano: the motif in the groove (S5 "Nobody can hide their habits"), answers in the gaps
        tm = g("s05", 5.15)
        self.motif([tm, tm + BEAT / 2, tm + BEAT, tm + 1.5 * BEAT], [0.5, 0.48, 0.52, 0.58], 1.4)
        self.pn(g0 + 4 * BEAT, "D3 A3 C#4", 0.3, 2.6)
        self.pn(g("s06", 6.05), "D4", 0.33, 0.45)
        self.pn(g("s06", 6.47), "C#4", 0.31, 0.9)
        for note in (74, 81):                                          # S7 pluck on "half"
            self.bass.append((w("s07", "half"), note, 0.7, 0.5, 0.3))
        self.marks.append((w("s07", "half"), "pluck"))
        self.pn(g("s09", 2.45), "A5", 0.24, 1.4)
        self.silence(drop, w("s09", "red") - 0.01, 0.06, 0.02)        # S9: the music drops out
        # S9 after "red": crimson low cluster (the stinger + sub are SFX)
        s = "s09"
        L("pad", (w(s, "red") - 0.01, -80), (w(s, "red") + 0.35, -13), (end(s), -12))
        self.cut += [(w(s, "red"), 500), (end(s), 700)]
        self.chord(w(s, "red"), end(s) + 0.3, "D2 A2 Eb3")

        # ------------------------------------------------------------- S10 the thread / backstory
        s = "s10"
        L("pad", (g(s, 0.3), -12), (g(s, 6.2), -12), (g(s, 6.9), -22), (end(s), -22))
        L("drone", (g(s, 0.0), -12), (g(s, 6.4), -9), (end(s), -10))
        self.cut += [(g(s, 0.0), 700), (g(s, 4.6), 800), (g(s, 6.4), 600)]
        self.chord(g(s, 0.0), w(s, "all"), "D2 A2 D3 F3")
        self.chord(w(s, "all"), w(s, "freed"), "Bb1 F2 D3 F3")
        self.chord(w(s, "freed"), g(s, 6.6), "G1 D2 G2 Bb2")
        self.chord(g(s, 6.6), end(s) + 0.4, "D2 A2")
        self._pulse_run(g(s, 0.0), w(s, "freed"), 38)
        self._pulse_run(w(s, "freed") + 0.62, g(s, 6.4), 38, fade_from=g(s, 5.8))
        self.pn(w(s, "freed"), "Bb1 F2 Bb2", 0.6, 1.3, "feature")
        fb = g(s, 6.4)
        self.st(fb, 1.6, "D3 F3 A3", 0.6, attack=0.8, release=1.0)
        self.st(w(s, "murdered"), 0.7, "Bb2 D3 F3", 0.66, attack=0.5, release=1.0)
        self.st(w(s, "partner"), end(s) - w(s, "partner") - 0.2, "A2 C#3 E3", 0.7, attack=0.5, release=1.4)
        mt = [fb, w(s, "the", 3), w(s, "murdered"), w(s, "partner")]
        self.motif(mt, [0.55, 0.56, 0.6, 0.62], 1.6, notes=("A2", "D3", "F3", "E3"))
        for i, nm in enumerate(("A2", "D3", "F3", "E3")):                      # cello doubling
            t1 = mt[i + 1] if i < 3 else end(s) - 0.15
            self.st(mt[i], t1 - mt[i], nm, 0.45, attack=0.25, release=0.6, voices=3, detune=5)

        # ------------------------------------------------------------- S11 the chase
        s = "s11"
        caught = w(s, "caught")
        L("pad", (g(s, 0.0), -12), (g(s, 3.4), -11), (caught - 0.02, -8), (caught, -80),
          (w(s, "warm") - 0.05, -80), (w(s, "warm") + 0.9, -17), (end(s), -16))
        L("drone", (g(s, 0.0), -11), (caught, -8), (caught + 0.01, -80), (w(s, "warm"), -80), (end(s), -14))
        self.cut += [(g(s, 0.0), 700), (g(s, 3.5), 900), (caught, 2200), (caught + 0.05, 1400), (end(s), 1400)]
        self.chord(g(s, 0.0), caught + 0.05, "D2 A2 D3 F3")
        self.chord(w(s, "warm") - 0.1, end(s) + 0.8, "A4 D5")                    # amber: the warm match
        self._pulse_run(g(s, 0.0), g(s, 3.45), 38, crescendo=True)
        self._chase(s, caught)
        self.st(g(s, 2.0), caught - g(s, 2.0), "D3 A3", 0.55, attack=4.0, release=0.04, trem=(12.0, 0.45))
        self.silence(caught + 0.16, w(s, "warm") - 0.06, 0.012, 0.25)

        # ------------------------------------------------------------- S12 the trap
        s = "s12"
        cut12 = g(s, 9.7)
        L("pad", (g(s, 0.0), -13), (g(s, 5.2), -12), (cut12 - 0.02, -7))
        L("drone", (g(s, 0.0), -13), (g(s, 5.4), -11), (cut12, -8))
        self.cut += [(g(s, 0.0), 650), (g(s, 5.4), 600), (cut12, 1500)]
        self.chord(g(s, 0.0), w(s, "friday"), "D2 A2 D3 F3")
        self.chord(w(s, "friday"), g(s, 5.4), "D2 Bb2 D3 F3")
        self.chord(g(s, 5.4), w(s, "clock"), "D2 G2 Bb2 D3")
        self.chord(w(s, "clock"), cut12 + 0.05, "D2 A2 C#3 Bb3")
        for k in range(int(5.4 / BEAT)):                                           # slow quarter pulse
            self.pulses.append((g(s, 0.1 + k * BEAT), 38, 0.55, 0.3, 0.6, "main"))
        self._pulse_run(g(s, 5.4), cut12, 38, crescendo=True)
        self.st(g(s, 5.4), cut12 - g(s, 5.4), "D3 Eb3 A3 Bb3", 0.6, attack=4.2, release=0.02, trem=(7.0, 0.35))
        self.heart.append((g(s, 5.4), cut12, 64, 92, -7.0, None, s))
        self.motif([w(s, "three"), w(s, "oh"), w(s, "seven")], [0.5, 0.52, 0.56], 0.9, notes=("A3", "D4", "F4"),
                   durs=[0.4, 0.3, 0.9])                                          # ...and the E never comes
        self.silence(cut12, end(s) + 1.2, 0.004, 0.02)                            # SMASH TO BLACK (into S13)

        # ------------------------------------------------------------- S13 blackout
        s = "s13"
        L("pad", (g(s, 1.15), -80), (g(s, 3.9), -30), (g(s, 10.6), -8), (end(s), -8))
        L("drone", (g(s, 1.15), -80), (g(s, 1.4), -16), (g(s, 3.9), -13), (end(s), -7))
        self.cut += [(g(s, 3.9), 300), (end(s), 1500)]
        self.chord(g(s, 3.0), end(s) + 0.1, "D2 Eb2 A2")
        self.heart.append((g(s, 1.2), g(s, 7.8), 58, 50, -9.0, 120.0, s))
        self.st(g(s, 3.9), end(s) - g(s, 3.9), "D3 Eb3 Ab3 A3 D4 Eb4", 0.75, attack=6.4, release=0.02, trem=(5.5, 0.2))
        self.pn(w(s, "left"), "E4", 0.4, 1.4, "feature")                         # the missing note
        self.marks.append((g(s, 3.9), "dissonant swell"))
        self.silence(end(s) - 0.03, end(s) + 0.05, 0.03, 0.02)                    # the whip

        # ------------------------------------------------------------- S14 the mirror
        s = "s14"
        mirror = w(s, "mirror")
        L("pad", (g(s, 0.0), -14), (g(s, 7.4), -14), (mirror - 0.02, -8))
        L("drone", (g(s, 0.0), -11), (mirror, -8))
        self.cut += [(g(s, 0.0), 600), (g(s, 7.4), 700), (mirror, 2600)]
        self.chord(g(s, 0.0), g(s, 7.4), "D2 A2 D3")
        self.chord(g(s, 7.4), mirror + 0.02, "D2 A2 D3 Eb3")
        self._pulse_run(g(s, 0.05), g(s, 11.5), 38, crescendo=True, gain=0.62)
        clue = [w(s, "rain"), w(s, "three"), w(s, "a", 0), w(s, "a", 1), w(s, "a", 2)]
        for i, t in enumerate(clue):
            big = i == 4
            self.pn(t, "D1 D2" if not big else "D1 D2 Eb3", 0.58 if not big else 0.68, 1.2, "feature")
            self.st(t, 0.14, "D3 A3 D4" if not big else "D3 Eb4 A4", 0.48, attack=0.008, release=0.35, bus="feature")
            self.events.append((t, lambda r: dsp.to_stereo(dsp.mono(tom(62.0, 1, 0.45))) * 1.2, "feature"))
            self.marks.append((t, f"clue {i + 1}"))
        rise = g(s, 7.4)
        self.st(rise, mirror - rise, "D3 A3 D4 Eb4 A4", 0.52, attack=mirror - rise, release=0.01, trem=(9.0, 0.3),
                bend=lambda tt, d=mirror - rise: 2 ** (2.0 * np.clip(tt / d, 0, 1) ** 1.6 / 12))
        self.silence(mirror, end(s) + 0.3, 0.008, 0.2)                            # braam, then silence

        # ------------------------------------------------------------- S15 blue lights (strings)
        s = "s15"
        L("pad", (g(s, 0.0), -80), (g(s, 1.5), -15), (end(s), -15))
        L("drone", (g(s, 0.0), -80), (g(s, 1.0), -11), (end(s), -11))
        self.cut += [(g(s, 0.0), 500), (end(s), 600)]
        self.chord(g(s, 0.3), end(s), "D2 A2 D3")
        self.st(g(s, 0.3), w(s, "my") - g(s, 0.3), "D3 F3 A3 D4", 0.5, attack=1.6, release=1.4)
        self.st(w(s, "my"), w(s, "i") - w(s, "my"), "Bb2 D3 F3 Bb3", 0.56, attack=1.0, release=1.3)
        self.st(w(s, "i"), w(s, "where") - w(s, "i"), "G2 D3 G3 Bb3", 0.62, attack=0.9, release=1.3)
        self.st(w(s, "where"), w(s, "is") - w(s, "where"), "A2 E3 A3 C#4", 0.7, attack=0.9, release=1.2)
        self.st(w(s, "is"), end(s) - w(s, "is") - 0.2, "D3 F3 Bb3 D4", 0.75, attack=0.5, release=1.6)

        # ------------------------------------------------------------- S16 the lineup, again
        s = "s16"
        walk = w(s, "walk")
        L("pad", (g(s, 0.0), -14), (g(s, 2.0), -11), (end(s), -11))
        L("drone", (g(s, 0.0), -11), (end(s), -12))
        self.cut += [(g(s, 0.0), 450), (walk, 750), (end(s), 650)]
        self.chord(g(s, 0.0), walk, "D2 A2 D3 F3")
        self.chord(walk, end(s) + 0.2, "A2 D3 E3 G3")
        self.motif([w(s, "she", 1), w(s, "watched"), w(s, "me", 1), walk], [0.5, 0.52, 0.55, 0.64], 1.8)

        # ------------------------------------------------------------- S17 habits can be learned
        s = "s17"
        copied = w(s, "copied")
        L("pad", (g(s, 0.0), -12), (g(s, 7.4), -12), (end(s), -16))
        L("drone", (g(s, 0.0), -12), (end(s), -14))
        self.cut += [(g(s, 0.0), 600), (copied, 700), (end(s), 450)]
        self.pn(w(s, "case"), "A2 E3 G3 C#4", 0.42, 0.42, "feature")
        self.pn(w(s, "closed"), "D2 A2 D3 F3", 0.46, 1.1, "feature")
        self.chord(g(s, 0.0), w(s, "except"), "D2 A2 D3 F3")
        self.chord(w(s, "except"), copied, "Bb1 F2 D3 A3")
        self.chord(copied, w(s, "and"), "D2 A2 D3 Eb3")
        self.chord(w(s, "and"), end(s), "D2 A2 D3")
        self.motif([w(s, "habits"), w(s, "can"), w(s, "learned"), copied], [0.45, 0.45, 0.5, 0.6], 2.3,
                   bend=(0.18, 0.38, -1.0))
        self.st(copied, 2.0, "E4", 0.35, attack=0.12, release=1.0, voices=3, detune=4,
                bend=lambda tt: 2 ** (-1.0 * np.clip((tt - 0.18) / 0.38, 0, 1) ** 2 / 12), bus="feature")
        self.marks.append((copied, "copycat E->Eb"))

        # ------------------------------------------------------------- S18 your verdict
        s = "s18"
        fin = w(s, "suspect")
        L("pad", (g(s, 0.0), -80), (g(s, 1.0), -15), (fin, -12), (g(s, 12.0), -80))
        L("drone", (g(s, 0.0), -14), (fin, -11), (g(s, 12.0), -80))
        self.cut += [(g(s, 0.0), 500), (fin, 800), (g(s, 12.0), 400)]
        self.chord(g(s, 0.2), w(s, "hardest"), "G2 D3 G3")
        self.chord(w(s, "hardest"), w(s, "so"), "Bb1 F2 D3 A3")
        self.chord(w(s, "so"), fin, "G2 D3 A3 Bb3")
        self.chord(fin, g(s, 12.0), "Bb1 F2 D3")
        self.st(g(s, 0.3), w(s, "hardest") - g(s, 0.3), "G2 D3 G3 Bb3", 0.42, attack=1.8, release=1.3)
        self.st(w(s, "hardest"), w(s, "so") - w(s, "hardest"), "Bb2 F3 A3 D4", 0.48, attack=1.0, release=1.3)
        self.st(w(s, "so"), w(s, "was") - w(s, "so"), "G2 D3 A3 Bb3", 0.5, attack=0.9, release=1.2)
        self.st(w(s, "was"), fin - w(s, "was"), "A2 D3 E3 G3", 0.55, attack=0.9, release=1.0)
        self.st(fin, g(s, 12.0) - fin, "Bb2 F3 D4 A4 E5", 0.62, attack=0.35, release=0.8)
        self.motif([w(s, "city"), w(s, "faces"), w(s, "hardest"), w(s, "own")], [0.42, 0.4, 0.38, 0.36], 2.6)
        self.pn(fin, "Bb1 F2 D3 A3 E4", 0.46, 2.6, "feature")
        self.marks.append((fin, "final chord"))
        self.silence(g(s, 12.0), self.total + 1, 1.6, 0.0)       # fade by 12.0

    # ------------------------------------------------------------------ pulse helpers
    def _pulse_run(self, t0, t1, midi, fade_from=None, crescendo=False, gain=1.0):
        k = 0
        step = BEAT / 2
        while t0 + k * step < t1 - 0.05:
            t = t0 + k * step
            acc = 1.0 if k % 2 == 0 else 0.62
            v = 0.62 * acc * gain
            if crescendo:
                v *= 0.65 + 0.45 * (t - t0) / max(t1 - t0, 1e-3)
            if fade_from is not None and t > fade_from:
                v *= max(0.0, 1 - (t - fade_from) / max(t1 - fade_from, 1e-3))
            if v > 0.02:
                self.pulses.append((t, midi, v, 0.26, 0.9, "main"))
            k += 1

    def _chase(self, s, caught):
        """108 BPM chase pulse, built backwards from 'caught' so the last hit lands on it."""
        sb = 60.0 / CHASE_BPM
        first = caught - 8 * sb
        while first - sb >= self.g(s, 3.5) - 1e-6:
            first -= sb
        n16 = int(round((caught - first) / (sb / 4)))
        pat = [38, 38, 50, 38, 38, 45, 38, 50]
        for i in range(n16):
            t = first + i * sb / 4
            prog = (t - first) / max(caught - first, 1e-3)
            v = (0.5 + 0.45 * prog) * (1.0 if i % 4 == 0 else 0.7)
            self.pulses.append((t, pat[i % 8], v, 0.12, 1.3, "chase"))
            self.kit.append((t, "chh", 0.45 + 0.4 * prog * (1.0 if i % 2 == 0 else 0.6), i % 4))
            if i % 4 == 0:
                self.kit.append((t, "tom_lo", 0.65 + 0.35 * prog, i))
            if i % 16 == 14:
                self.kit.append((t, "tom_hi", 0.6 + 0.3 * prog, i))
            if i % 2 == 0:
                nm = ("D4", "F4", "A4", "F4")[(i // 2) % 4]
                self.st(t, 0.07, nm, 0.32 + 0.3 * prog, attack=0.006, release=0.09, voices=3, detune=6, bus="main")
        # the button: a choked tutti hit exactly on "caught"
        self.pn(caught, "D1 A1 D2 A2", 0.85, 0.16, "feature")
        self.st(caught, 0.1, "D3 A3 D4", 0.8, attack=0.004, release=0.06, bus="feature")
        self.kit.append((caught, "tom_lo", 1.0, 99))
        self.marks.append((caught, "caught"))


# ============================================================================ rendering
# layer balance (from the first measured pass: pad+drone -14, piano -35, strings -26, bass -30,
# kit -28, pulse -33 LUFS integrated) -> pad ~ -28, piano ~ -26, strings ~ -25, bass ~ -28,
# kit ~ -30, pulse ~ -28
PAD_GAIN = db2lin(-14.0)
DRONE_GAIN = db2lin(-3.0)


def _up2(x):
    """2x upsampling, channel by channel on contiguous arrays (much faster than axis=0)."""
    from scipy import signal as _sg
    return np.stack([_sg.resample_poly(np.ascontiguousarray(x[:, c]), 2, 1) for c in range(x.shape[1])], axis=1)


def _bp(points, n, sr, default=-80.0):
    if not points:
        return np.full(n, default)
    pts = sorted(points)
    return np.interp(np.arange(n) / sr, [p[0] for p in pts], [p[1] for p in pts])


def _add(buf, x, t, sr=SR, gain=1.0):
    dsp.mix_into(buf, x, n_of(t, sr), gain)


def _sparse_reverb(x, kind, wet_db, thresh=1e-6, gap=1.5):
    """Convolve only the active regions of a send (FFT per region, tails kept)."""
    ir = dsp.make_ir(kind)
    act = np.max(np.abs(x), axis=1) > thresh
    out = np.zeros_like(x)
    idx = np.nonzero(act)[0]
    if len(idx) == 0:
        return out
    brk = np.nonzero(np.diff(idx) > gap * SR)[0]
    starts = np.concatenate([[idx[0]], idx[brk + 1]])
    ends = np.concatenate([idx[brk], [idx[-1]]])
    for a, b in zip(starts, ends):
        seg = x[a:b + 1].mean(axis=1)
        wet = dsp.convolve(seg, ir) * db2lin(wet_db)
        dsp.mix_into(out, wet, a)
    return out


def render_score(tl, cue_scenes=None, seed=0, return_plan=False, debug=False):
    plan = Plan(tl, cue_scenes)
    plan.compose()
    N, total = plan.N, plan.total
    N2 = int(math.ceil(total * SR2)) + 1
    rng = np.random.default_rng(dsp.stable_seed("score", seed))
    main = np.zeros((N, 2))
    feat = np.zeros((N, 2))
    send_hall = np.zeros((N, 2))
    send_plate = np.zeros((N, 2))
    send_plate_f = np.zeros((N, 2))
    send_hall_f = np.zeros((N, 2))
    send_room = np.zeros((N, 2))
    info = dict(notes=0)
    layers = {}

    # ---- pad (24 kHz): merge contiguous chord notes into long voices
    pad = np.zeros((N2, 2))
    spans = {}
    for t0, t1, notes in sorted(plan.chords):
        for mm in notes:
            lst = spans.setdefault(mm, [])
            if lst and abs(lst[-1][1] - t0) < 0.06:
                lst[-1][1] = max(lst[-1][1], t1)
            else:
                lst.append([t0, t1])
    XF = 0.9
    for mm, lst in spans.items():
        for t0, t1 in lst:
            a = max(0, int((t0 - XF / 2) * SR2))
            b = min(N2, int((t1 + XF) * SR2))
            if b <= a:
                continue
            v = pad_voice(hz(mm), b - a, rng)
            tt = (np.arange(a, b) / SR2)
            env = np.clip((tt - (t0 - XF / 2)) / XF, 0, 1)
            env = np.sin(0.5 * np.pi * env) * np.cos(0.5 * np.pi * np.clip((tt - (t1 - XF / 2)) / XF, 0, 1))
            pad[a:b] += v * env[:, None] * (0.8 if mm < 45 else 0.6)
    cut = np.clip(_bp(plan.cut, N2, SR2, 600.0), 120, 6000)
    for ch in range(2):
        pad[:, ch] = tv_lowpass(pad[:, ch], cut, q=0.75, sr=SR2, block=256)
    pad *= db2lin(_bp(plan.lv["pad"], N2, SR2))[:, None]
    pad *= (1 + 0.06 * dsp.smooth_noise(N2, 0.07, rng, SR2))[:, None]

    # ---- drone (24 kHz)
    t2 = np.arange(N2) / SR2
    dr = (np.sin(TWO_PI * 36.708 * t2) + 0.5 * np.sin(TWO_PI * 73.416 * t2 + 1.0)
          + 0.12 * np.sin(TWO_PI * 55.0 * t2 + 2.0)) * (1 + 0.15 * dsp.smooth_noise(N2, 0.1, rng, SR2))
    dr = dr + 0.25 * sos(saturate(dr * 2.0, 2.0), "highpass", 90, 2, sr=SR2)
    dr *= 0.22 * db2lin(_bp(plan.lv["drone"], N2, SR2))
    drone = np.stack([dr, dr], axis=1)

    # ---- strings (24 kHz)
    strings_m = np.zeros((N2, 2))
    strings_f = np.zeros((N2, 2))
    for (t, gate, notes, vel, att, rel, kw, bus) in plan.strings:
        for mm in notes:
            x = strings_note(hz(mm), gate, att, rel, vel, rng, **kw)
            dsp.mix_into(strings_f if bus == "feature" else strings_m, x, int(t * SR2), 0.25)
    for buf in (strings_m, strings_f):
        for ch in range(2):
            y = sos(buf[:, ch], "highpass", 70, 2, sr=SR2)
            y = sos(y, "lowpass", 3600, 2, sr=SR2)
            y = dsp.biquad(y, "peak", 450, 1.0, 2.0, sr=SR2)
            buf[:, ch] = dsp.biquad(y, "peak", 2600, 1.2, 1.5, sr=SR2)
    lowbus = _up2(pad * PAD_GAIN + drone * DRONE_GAIN)[:N]
    s_m = _up2(strings_m)[:N]
    s_f = _up2(strings_f)[:N]
    lowbus = dsp.pad_to(lowbus, N)
    s_m = dsp.pad_to(s_m, N)
    s_f = dsp.pad_to(s_f, N)
    main += lowbus + s_m
    feat += s_f
    if debug:
        layers["pad+drone"] = lowbus.copy()
        layers["strings"] = s_m + s_f
    send_hall += lowbus * 0.35 + s_m * 0.55
    send_hall_f += s_f * 0.5
    del pad, drone, strings_m, strings_f, lowbus

    # ---- piano
    if debug:
        layers["piano"] = np.zeros((N, 2))
    for (t, midi, vel, dur, bus, bend) in plan.piano:
        x = piano_note(int(midi), round(float(vel), 2), round(float(dur), 2), bend)
        if bus == "feature":
            _add(feat, x, t)
            _add(send_plate_f, x, t, gain=0.45)
        else:
            _add(main, x, t)
            _add(send_plate, x, t, gain=0.45)
        info["notes"] += 1
        if debug:
            _add(layers["piano"], x, t)

    # ---- groove: bass + kit (brush swirl continuous)
    grv = np.zeros((N, 2))
    for (t, midi, vel, dur, bright) in plan.bass:
        x = bass_note(int(midi), round(float(vel), 2), round(float(dur), 2), bright)
        _add(grv, x, t)
    if plan.groove_span:
        g0, drop = plan.groove_span
        a, b = n_of(g0 - BEAT), n_of(drop)
        tt = (np.arange(a, b) / SR - g0) / BEAT
        swell = (0.5 - 0.5 * np.cos(TWO_PI * tt)) ** 1.5
        acc = np.where(np.floor(tt) % 2 == 1, 1.2, 0.85)
        sw = dsp.bandpass(pink(b - a, rng), 2200, 7000, 2) * (0.25 + 0.75 * swell) * acc * 0.012
        sw *= np.clip((np.arange(b - a)) / (BEAT * SR), 0, 1)
        grv[a:b] += dsp.decorrelate(sw, rng, amount=0.5)
    kitbus = np.zeros((N, 2))
    for (t, kind, vel, sd) in plan.kit:
        if kind == "tap":
            x = brush_tap(sd % 5)
        elif kind == "hat":
            x = hat_chick(sd % 3)
        elif kind == "ride":
            x = ride_hit(sd % 6)
        elif kind == "chh":
            x = hat_chick(sd % 3) * 1.4
        elif kind == "tom_lo":
            x = tom(68.0, sd % 4, 0.32)
        elif kind == "tom_hi":
            x = tom(104.0, sd % 4, 0.22)
        else:
            continue
        _add(kitbus, x, t, gain=vel)
    main += grv + kitbus
    if debug:
        layers["bass+swirl"] = grv.copy()
        layers["kit"] = kitbus.copy()
    send_room += grv * 0.25 + kitbus * 0.35
    del grv, kitbus

    # ---- pulses (tension / chase)
    pul = np.zeros((N, 2))
    for (t, midi, vel, dur, bright, bus) in plan.pulses:
        x = pulse_note(int(midi), round(float(vel), 2), round(float(dur), 2), bright)
        _add(pul, x, t)
    main += pul
    send_hall += pul * 0.12
    if debug:
        layers["pulse"] = pul.copy()
    del pul

    # ---- free events (soft hits, clue toms)
    for (t, fn, bus) in plan.events:
        x = fn(rng)
        _add(feat if bus == "feature" else main, x, t)
        _add(send_hall_f if bus == "feature" else send_hall, x, t, gain=0.35)

    # ---- heartbeat (yields to a picture-synced heartbeat cue in the same scene)
    info["heartbeat"] = []
    for (t0, t1, b0, b1, gdb, lp, sid) in plan.heart:
        if sid in plan.cue_scenes.get("heartbeat", set()):
            info["heartbeat"].append(dict(scene=sid, yielded=True))
            continue
        x = sfx.render("heartbeat", dur=t1 - t0, params=dict(bpm=b0, bpm_end=b1), seed=12).astype(np.float64)
        if lp:
            x = sos(x, "lowpass", lp, 2)
            x = dsp.fade(x, 0.4, 2.5)
        _add(feat, x * db2lin(gdb), t0)
        info["heartbeat"].append(dict(scene=sid, t0=t0, t1=t1))

    # ---- reverbs
    main += dsp.pad_to(_sparse_reverb(send_hall, "hall", -5.0), N)
    main += dsp.pad_to(_sparse_reverb(send_plate, "plate", -6.0), N)
    main += dsp.pad_to(_sparse_reverb(send_room, "small_room", -9.0), N)
    feat += dsp.pad_to(_sparse_reverb(send_plate_f, "plate", -6.0), N)
    feat += dsp.pad_to(_sparse_reverb(send_hall_f, "hall", -6.0), N)

    # ---- designed silences (after reverb: they cut the tails too)
    gate = np.ones(N)
    tt = None
    for (t0, t1, fo, fi) in plan.mask:
        a, b = n_of(max(0.0, t0 - fo)), min(N, n_of(t1 + fi))
        if b <= a:
            continue
        seg_t = np.arange(a, b) / SR
        gdn = np.clip((t0 - seg_t) / max(fo, 1e-4), 0, 1)
        gup = np.clip((seg_t - t1) / max(fi, 1e-4), 0, 1)
        gate[a:b] = np.minimum(gate[a:b], np.maximum(gdn, gup))
    main *= gate[:, None]
    feat *= gate[:, None]
    info["marks"] = plan.marks
    info["layers"] = layers
    info["silences"] = [(round(a, 3), round(b, 3)) for a, b, _, _ in plan.mask]
    out = (main.astype(np.float32), feat.astype(np.float32), info)
    return out + (plan,) if return_plan else out


if __name__ == "__main__":
    import os
    import sys
    import time
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from engine.timing import timeline
    t0 = time.time()
    main, feat, info = render_score(timeline())
    print(f"score rendered in {time.time() - t0:.1f}s, {info['notes']} piano notes")
    mix = main + feat
    print("music integrated", round(dsp.loudness_integrated(mix), 2), "TP", round(dsp.true_peak_db(mix), 2))
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dsp.write_wav(os.path.join(root, "out", "score_preview.wav"), mix * 0.5, bits=24)
