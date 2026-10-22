"""RED: the score. An A-minor folk lullaby, synthesized (numpy/scipy only).

    render_score(seed=0) -> (buses, info)
        buses: dict(main=, feat=, hits=) float32 (N, 2) at 48 kHz on the film clock
        info:  dict(marks=[(t, label)], counts=..., seconds=...)

Buses (mix.py ducks them differently under the narration):
  main ... the bed of the score: strings, choir, brass, percussion, ostinati
  feat ... the melodic voices that must survive under the narration: music box, solo violin
  hits ... designed musical hits locked to words or picture beats: booms, stabs, tam-tam, the
           fire downbeat. Lightly ducked.

The lullaby (3/4, A minor; one bar = | |):
  A   | A E- | D C B | C A- | E-- |        Am  G   Am  E
  A'  | A E- | F E D | C B G# | A-- |      Am  Dm  F-E Am
  B   | C D E | G- F | E D C | D-- |       C   G7  Am  E7
Its opening rising fifth (A-E) is the call; the wolf's horns answer it falling (E-A).

Instruments (all synthesized here):
  music box ... cantilever-tine modes (1, 6.27, 17.55 x f0) with a beating partner, pin tick,
                damper 'jam' with a mechanical clack; key-wind ratchet; wow + detune for the
                ghost/winding-down box; body EQ of a small wooden box
  solo violin . one bowed string: PolyBLEP saw on a control-rate pitch track (portamento, delayed
                vibrato, jitter), bow-pressure brightness, rosin noise, 11-mode body
  strings ..... detuned saw sections (24 kHz): tasto (dark), normale, sul ponticello tremolo,
                harmonics (flautando sines)
  choir ....... male voices (24 kHz): saw sources with vibrato/jitter, vowel formant banks
                (oo/oh/ah) that morph, breath
  brass ....... saw sections with a lip scoop, dynamics-driven brightness (horn, trombone,
                stopped horn)
  percussion .. modal timpani (principal + overtones, pitch glide, mallet), gran cassa, crash,
                suspended-cymbal swell, tam-tam bloom, sub boom, breath hits ('hah'), riser
  pizz ........ Karplus-Strong contrabass; spiccato low strings for the chases

Every hit sits on a narration word (common.A) or a picture beat named in the bible; see
compose() and the 'marks' list (the hit list in audio_report.json).
"""
from __future__ import annotations

import functools
import math

import numpy as np
from scipy import signal

from .common import A, N, make_space_ir, sparse_convolve
from .common import S as ST
from audio import dsp
from audio.dsp import (SR, TWO_PI, bandpass, db2lin, karplus_strong, n_of, onepole_lp, pink, resonator_bank,
                       saw, smooth_noise, sos, t_axis, tv_bandpass, tv_lowpass, white)

SR2 = 24000                          # render rate of the section strings and the choir
N2 = (N + 1) // 2 + 2
CUTS = (66.5,)                       # hard cuts: everything sounding before is cut there (8 ms)
SCORE_LUFS = -19.0                   # integrated loudness of main+feat+hits (pre-duck, pre-master)
BUS_PLR = dict(main=13.0, feat=11.0, hits=13.0)   # bus limiter ceilings (dBTP) relative to SCORE_LUFS

_NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
         "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def m(name):
    if not isinstance(name, str):
        return int(name)
    return 12 * (int(name[-1]) + 1) + _NOTE[name[:-1]]


def hz(mm):
    return 440.0 * 2.0 ** ((m(mm) - 69) / 12.0)


# ============================================================================ the tune
LULL = [  # (beat, beats, note) - 3 beats per bar, home octave
    (0, 1, "A4"), (1, 2, "E5"), (3, 1, "D5"), (4, 1, "C5"), (5, 1, "B4"), (6, 1, "C5"), (7, 2, "A4"), (9, 3, "E4"),
    (12, 1, "A4"), (13, 2, "E5"), (15, 1, "F5"), (16, 1, "E5"), (17, 1, "D5"), (18, 1, "C5"), (19, 1, "B4"),
    (20, 1, "G#4"), (21, 3, "A4"),
    (24, 1, "C5"), (25, 1, "D5"), (26, 1, "E5"), (27, 2, "G5"), (29, 1, "F5"), (30, 1, "E5"), (31, 1, "D5"),
    (32, 1, "C5"), (33, 3, "D5"),
]
CHORDS = ["Am", "G", "Am", "E", "Am", "Dm", "F|E", "Am", "C", "G7", "Am", "E7"]
TONES = {"Am": "A C E", "G": "G B D", "E": "E G# B", "E7": "E G# D", "Dm": "D F A", "F": "F A C", "C": "C E G",
         "G7": "G B F", "A": "A C# E", "Fmaj7": "F A E", "Bb": "Bb D F"}
VOICING = {"Am": ("A2", "A3 C4 E4"), "G": ("G2", "G3 B3 D4"), "E": ("E2", "E3 G#3 B3"), "E7": ("E2", "D3 G#3 B3"),
           "Dm": ("D2", "D3 F3 A3"), "F": ("F2", "F3 A3 C4"), "C": ("C2", "C3 E3 G3"), "G7": ("G2", "F3 B3 D4"),
           "A": ("A2", "A3 C#4 E4"), "Fmaj7": ("F2", "F3 A3 E4")}


def chord_at(bar, beat=0):
    c = CHORDS[bar % len(CHORDS)]
    if "|" in c:
        a, b = c.split("|")
        return a if beat < 1 else b
    return c


def in_range(mm, lo, hi):
    while mm < lo:
        mm += 12
    while mm > hi:
        mm -= 12
    return mm


def tones(ch, lo, hi):
    return [in_range(_NOTE[p], lo, hi) for p in TONES[ch].split()]


class TempoMap:
    """beat -> film time, piecewise-linear through [(beat, t)] anchors (extrapolated at the ends)."""

    def __init__(self, pts):
        pts = sorted(pts)
        self.b = np.array([p[0] for p in pts], dtype=np.float64)
        self.t = np.array([p[1] for p in pts], dtype=np.float64)

    def __call__(self, beat):
        b, t = self.b, self.t
        if beat <= b[0]:
            return float(t[0] + (beat - b[0]) * (t[1] - t[0]) / (b[1] - b[0]))
        if beat >= b[-1]:
            return float(t[-1] + (beat - b[-1]) * (t[-1] - t[-2]) / (b[-1] - b[-2]))
        return float(np.interp(beat, b, t))


def melody(tm, b0, b1, table=LULL):
    """[(t, dur, midi, beat)] of the tune's notes with b0 <= beat < b1."""
    return [(tm(b), tm(b + L) - tm(b), m(nm), b) for (b, L, nm) in table if b0 <= b < b1]


def accel_times(t_a, t_b, bpm0, bpm1):
    """Beat times from t_a with the tempo ramping bpm0 -> bpm1, scaled so that the beat after the
    last returned one falls exactly on t_b (the downbeat that follows)."""
    span = t_b - t_a
    ts, t = [], 0.0
    while True:
        ts.append(t)
        if t >= span:
            break
        t += 60.0 / (bpm0 + (bpm1 - bpm0) * min(1.0, t / span))
    scale = span / ts[-1]
    return [t_a + x * scale for x in ts[:-1]]


def _names(names):
    if isinstance(names, str):
        return names.split()
    if isinstance(names, (int, np.integer)):
        return [int(names)]
    return list(names)


def _interp(pts, tt, default):
    if not pts:
        return np.full(len(tt), float(default))
    p = sorted(pts)
    return np.interp(tt, [a for a, _ in p], [b for _, b in p])


# ============================================================================ music box
def mbox_note(midi, vel, rng, cents=0.0, wow=0.0, damp=None, bright=1.0):
    f0 = hz(midi) * 2.0 ** (cents / 1200.0)
    t60 = float(np.clip(2.9 - (m(midi) - 76) * 0.07, 1.0, 3.8))
    dur = t60 * 1.1 if damp is None else min(t60 * 1.1, damp + 0.3)
    n = n_of(dur)
    t = t_axis(n)
    if wow:
        f = f0 * 2.0 ** (wow * np.sin(TWO_PI * rng.uniform(0.35, 0.7) * t + rng.uniform(0, TWO_PI)) / 1200.0)
        ph = np.cumsum(f) / SR
    else:
        ph = f0 * t
    x = np.sin(TWO_PI * ph + rng.uniform(0, TWO_PI)) * np.power(10.0, -3.0 * t / t60)
    x += 0.16 * np.sin(TWO_PI * (ph + 0.6 * t) + 1.3) * np.power(10.0, -3.0 * t / (0.7 * t60))
    if f0 * 6.267 < 18000:
        x += (0.32 * bright * math.sqrt(vel)) * np.sin(TWO_PI * 6.267 * ph + rng.uniform(0, TWO_PI)) \
            * np.power(10.0, -3.0 * t / max(0.06, 0.11 * t60))
    if f0 * 17.55 < 18000:
        x += (0.12 * bright * vel) * np.sin(TWO_PI * 17.55 * ph + rng.uniform(0, TWO_PI)) \
            * np.power(10.0, -3.0 * t / max(0.025, 0.035 * t60))
    k = min(n, n_of(0.005))
    tick = bandpass(rng.standard_normal(k), 2500.0, 11000.0, 2) * np.linspace(1.0, 0.0, k) ** 3
    x[:k] += 0.3 * bright * vel * tick / max(1e-9, np.max(np.abs(tick)))
    a = min(n, n_of(0.0006))
    x[:a] *= np.linspace(0.0, 1.0, a)
    if damp is not None:
        d = n_of(damp)
        if d < n:
            x[d:] *= np.power(10.0, -3.0 * (t[d:] - damp) / 0.045)
            kk = min(n - d, n_of(0.012))
            cl = bandpass(rng.standard_normal(kk), 500.0, 3800.0, 2) * np.exp(-np.arange(kk) / (0.0025 * SR))
            x[d:d + kk] += 0.35 * vel * cl / max(1e-9, np.max(np.abs(cl)))
    return dsp.fade(x, 0.0, 0.02) * (0.55 * vel)


def windup_clicks(count, rng, spacing=0.13):
    """The music box's key being wound: ratchet clicks over a faint spring creak."""
    n = n_of(count * spacing + 0.15)
    x = np.zeros(n)
    for i in range(count):
        k = n_of(0.012)
        c = bandpass(rng.standard_normal(k), 1500.0, 7000.0, 2) * np.exp(-np.arange(k) / (0.0012 * SR))
        c = c + 0.6 * resonator_bank(c, [2350.0, 3900.0], [25.0, 30.0], [1.0, 0.6])
        dsp.mix_into(x, c * rng.uniform(0.6, 1.0), n_of(i * spacing * rng.uniform(0.92, 1.08)))
    cr = dsp.friction(n, 38.0, rng, body=[(900, 8, 1.0), (1900, 10, 0.5)]) * 0.05
    x = x / max(1e-9, np.max(np.abs(x))) + cr * np.hanning(n)
    return dsp.fade(x, 0.002, 0.03)


# ============================================================================ solo violin
VIOLIN_BODY = ([280, 410, 470, 550, 700, 980, 1300, 2150, 2700, 3300, 4500],
               [10, 14, 12, 11, 8, 7, 6, 4, 4, 4, 3],
               [1.0, 0.45, 0.8, 0.9, 0.45, 0.4, 0.35, 0.55, 0.7, 0.5, 0.25])


def violin_phrase(notes, rng, cents_pts=(), vib_pts=(), rate_pts=(), bright=1.0):
    """notes: [(t, dur, midi, vel)] on the film clock; notes closer than 60 ms are slurred.
    Returns (stereo float64, t_start)."""
    notes = sorted(notes)
    t_start = notes[0][0] - 0.03
    t_end = max(t + d for t, d, _, _ in notes) + 0.6
    rate = 1000
    nc = int((t_end - t_start) * rate) + 2
    tc = t_start + np.arange(nc) / rate
    lf = np.full(nc, np.nan)
    target = np.zeros(nc)
    since = np.zeros(nc)
    for i, (t0, d, mm, v) in enumerate(notes):
        nxt = notes[i + 1][0] if i + 1 < len(notes) else None
        slur = nxt is not None and nxt - (t0 + d) < 0.06
        a = int((t0 - t_start) * rate)
        b = max(a + 1, int(((nxt if slur else t0 + d) - t_start) * rate))
        u = np.arange(b - a) / rate
        lf[a:b] = math.log2(hz(mm))
        since[a:b] = u
        target[a:b] = v * (1.0 + 0.10 * np.sin(np.pi * np.clip(u / max(d, 0.1), 0, 1)))
        if slur:
            k = min(int(0.05 * rate), b - a)
            target[b - k:b] *= np.linspace(1.0, 0.8, k)
        else:
            e = min(nc, b + int(0.45 * rate))
            hole = np.isnan(lf[b:e])
            lf[b:e][hole] = math.log2(hz(mm))
            since[b:e] = (np.arange(e - b) + (b - a)) / rate
    idx = np.nonzero(~np.isnan(lf))[0]
    lf = np.interp(np.arange(nc), idx, lf[idx])
    P = math.exp(-1.0 / (0.022 * rate))
    lf = lf[0] + signal.lfilter([1.0 - P], [1.0, -P], lf - lf[0])
    amp = dsp.follow_ar(target, 0.085, 0.075, rate)
    vib_c = _interp(vib_pts, tc, 20.0) * np.clip((since - 0.15) / 0.45, 0.0, 1.0)
    vrate = _interp(rate_pts, tc, 5.6)
    cents = _interp(cents_pts, tc, 0.0)
    n = n_of(t_end - t_start)
    ta = np.arange(n) / SR
    tcr = np.arange(nc) / rate

    def up(v):
        return np.interp(ta, tcr, v)

    vph = np.cumsum(up(vrate) * (1.0 + 0.05 * smooth_noise(n, 0.7, rng))) / SR
    f = 2.0 ** (up(lf) + (up(cents) + up(vib_c) * np.sin(TWO_PI * vph) + 2.5 * smooth_noise(n, 4.0, rng)) / 1200.0)
    a = up(amp)
    src = saw(f, n, phase0=rng.uniform())
    cut = np.clip((1500.0 + 6000.0 * np.clip(a, 0.0, 1.2) ** 1.3) * bright, 600.0, 12000.0)
    x = tv_lowpass(src * a, cut, q=0.6, block=128)
    x = x + bandpass(white(n, rng), 2000.0, 9000.0, 2) * a * (0.03 + 0.02 * np.abs(smooth_noise(n, 9.0, rng)))
    y = sos(0.3 * x + resonator_bank(x, *VIOLIN_BODY), "highpass", 190.0, 2)
    y = dsp.fade(y, 0.002, 0.08)
    return dsp.decorrelate(y, rng, amount=0.25), t_start


# ============================================================================ sections (24 kHz)
def section_tone(f0, n, rng, voices=5, detune=7.0, vib=0.0045, vib_rate=5.3, kind="saw", trem=0.0, sr=SR2):
    t = np.arange(n) / sr
    out = np.zeros((n, 2))
    for v in range(voices):
        sp = 2.0 * v / max(voices - 1, 1) - 1.0
        cents = detune * rng.normal(0.0, 0.6) + 1.5 * sp
        drift = 1.0 + 0.001 * smooth_noise(n, 0.5, rng, sr)
        depth = vib * np.clip((t - 0.3) / 0.8, 0.0, 1.0)
        f = f0 * drift * 2.0 ** (cents / 1200.0) * (1.0 + depth * np.sin(
            TWO_PI * rng.uniform(vib_rate - 0.5, vib_rate + 0.5) * t + rng.uniform(0, TWO_PI)))
        if kind == "saw":
            s = saw(f, n, sr, phase0=rng.uniform())
        else:
            s = np.sin(TWO_PI * np.cumsum(f) / sr + rng.uniform(0, TWO_PI))
        if trem > 0:
            r = rng.uniform(11.0, 15.5)
            s = s * (1.0 - trem * 0.5 * (1.0 - np.cos(TWO_PI * r * t + rng.uniform(0, TWO_PI))))
        th = (0.75 * sp + 1.0) * math.pi / 4.0
        out[:, 0] += math.cos(th) * s
        out[:, 1] += math.sin(th) * s
    return out / voices


def choir_tone(f0, n, rng, voices=4, sr=SR2):
    t = np.arange(n) / sr
    out = np.zeros((n, 2))
    for v in range(voices):
        sp = 2.0 * v / max(voices - 1, 1) - 1.0
        cents = rng.normal(0.0, 6.0)
        depth = 0.0035 * np.clip((t - 0.25) / 0.7, 0.0, 1.0) * rng.uniform(0.7, 1.2)
        f = f0 * 2.0 ** (cents / 1200.0) * (1.0 + 0.0015 * smooth_noise(n, 6.0, rng, sr)) * (1.0 + depth * np.sin(
            TWO_PI * rng.uniform(4.6, 5.6) * t + rng.uniform(0, TWO_PI)))
        s = saw(f, n, sr, phase0=rng.uniform())
        th = (0.8 * sp + 1.0) * math.pi / 4.0
        out[:, 0] += math.cos(th) * s
        out[:, 1] += math.sin(th) * s
    return out / voices


VOWELS = {  # (formant Hz, bandwidth Hz, gain) - male voices
    "u": [(325, 70, 1.0), (700, 90, 0.32), (2530, 130, 0.10)],
    "o": [(450, 80, 1.0), (800, 90, 0.55), (2830, 130, 0.14)],
    "a": [(730, 90, 1.0), (1090, 110, 0.70), (2440, 130, 0.30), (3400, 160, 0.14)],
    "m": [(250, 60, 1.0), (1700, 220, 0.04)],
}


def formant(x, vowel, sr=SR2):
    fs = VOWELS[vowel]
    return resonator_bank(x, [f for f, _, _ in fs], [f / bw for f, bw, _ in fs], [g for _, _, g in fs], sr)


# ============================================================================ brass and percussion (48 kHz)
def brass_note(midi, dur, vel, rng, voices=3, att=0.06, rel=0.25, bright=1.0, dyn=(), stopped=False):
    f0 = hz(midi)
    n = n_of(dur + rel * 1.6 + 0.02)
    t = t_axis(n)
    env = np.where(t < att, np.sin(0.5 * np.pi * np.clip(t / max(att, 1e-3), 0, 1)) ** 2, 1.0)
    env = np.where(t > dur, np.power(10.0, -3.0 * (t - dur) / max(rel, 0.02)), env)
    if dyn:
        env = env * db2lin(_interp(dyn, t, 0.0))
    scoop = 1.0 - 0.012 * np.exp(-t / 0.035)
    x = np.zeros(n)
    for v in range(voices):
        det = 2.0 ** (rng.normal(0.0, 5.0) / 1200.0)
        vib = 1.0 + 0.002 * np.clip((t - 0.3) / 0.5, 0, 1) * np.sin(TWO_PI * rng.uniform(4.8, 5.6) * t + rng.uniform(0, 6))
        x += saw(f0 * det * scoop * vib, n, phase0=rng.uniform())
    x /= voices
    lv = np.clip(env * vel, 0.0, 1.5)
    cut = np.clip(f0 * (1.4 + 9.0 * lv ** 1.6) * bright, 220.0, 9000.0)
    y = tv_lowpass(x, cut, q=0.9, block=128) * lv
    if stopped:      # hand-stopped horn: nasal, buzzy, thin
        y = dsp.saturate(y * 2.0, 1.0) * 0.5
        y = sos(y, "highpass", 300.0, 2) + 0.6 * resonator_bank(y, [1200.0, 2600.0], [5.0, 6.0], [1.0, 0.5])
    return dsp.fade(y, 0.0005, 0.02)


TIMP_MODES = [(0.62, 0.45, 0.22), (1.0, 1.0, 2.6), (1.504, 0.55, 1.7), (1.742, 0.40, 1.3), (2.0, 0.30, 1.1),
              (2.245, 0.22, 0.9), (2.494, 0.15, 0.75), (2.8, 0.10, 0.6), (2.98, 0.08, 0.5)]


@functools.lru_cache(maxsize=256)
def timp_hit(midi, velq, seed, soft=False):
    vel = velq / 100.0
    rng = np.random.default_rng(seed)
    f0 = hz(midi)
    dur = 2.4 if vel > 0.4 else 1.6
    n = n_of(dur)
    t = t_axis(n)
    ph = np.cumsum(f0 * (1.0 + 0.03 * vel * np.exp(-t / 0.07))) / SR
    x = np.zeros(n)
    for r, a, t60 in TIMP_MODES:
        aa = a * (max(vel, 0.05) ** (0.35 * max(r - 1.0, 0.0)))
        x += aa * np.sin(TWO_PI * r * ph + rng.uniform(0, TWO_PI)) * np.power(10.0, -3.0 * t / t60)
    k = n_of(0.06)
    nz = sos(rng.standard_normal(k), "lowpass", (300.0 if soft else 500.0) + 1500.0 * vel, 2) * np.exp(-np.arange(k) / (0.012 * SR))
    x[:k] += (0.4 if soft else 0.8) * vel * nz / max(1e-9, np.max(np.abs(nz)))
    a = n_of(0.001)
    x[:a] *= np.linspace(0, 1, a)
    return (dsp.fade(x, 0.0, 0.05) * vel * 0.5).astype(np.float32)


def bass_drum(vel, rng):
    n = n_of(2.4)
    t = t_axis(n)
    f = 46.0 * (1.0 + 0.3 * np.exp(-t / 0.05))
    ph = np.cumsum(f) / SR
    x = np.sin(TWO_PI * ph) * np.power(10.0, -3.0 * t / 1.5) + 0.4 * np.sin(TWO_PI * 1.6 * ph) * np.power(10.0, -3.0 * t / 0.5)
    k = n_of(0.08)
    skin = sos(rng.standard_normal(k), "lowpass", 700.0, 2) * np.exp(-np.arange(k) / (0.02 * SR))
    x[:k] += 0.6 * skin / max(1e-9, np.max(np.abs(skin)))
    x[:n_of(0.002)] *= np.linspace(0, 1, n_of(0.002))
    return dsp.fade(x, 0.0, 0.05) * vel * 0.6


def crash(vel, rng, dur=4.5):
    n = n_of(dur)
    t = t_axis(n)
    out = np.zeros((n, 2))
    fr = [420, 690, 1050, 1580, 2290, 3170, 4400, 5900, 7600]
    for ch in range(2):
        nz = rng.standard_normal(n)
        hi = sos(nz, "highpass", 3000.0, 2) * np.power(10.0, -3.0 * t / 2.6)
        mid = bandpass(nz, 600.0, 3000.0, 2) * np.power(10.0, -3.0 * t / 1.1)
        md = resonator_bank(nz * np.exp(-t / 0.05), [f * rng.uniform(0.97, 1.03) for f in fr], 35.0,
                            [0.5, 0.5, 0.6, 0.6, 0.5, 0.45, 0.4, 0.3, 0.25])
        out[:, ch] = 0.6 * hi + 0.3 * mid + 0.6 * md
    out[:n_of(0.0015)] *= np.linspace(0, 1, n_of(0.0015))[:, None]
    out = out / max(1e-9, np.max(np.abs(out)))
    return dsp.fade(out, 0.0, 0.3) * vel * 0.45


def cym_swell(dur, vel, rng):
    """Suspended cymbal roll (soft mallets) swelling into a hit."""
    n = n_of(dur)
    t = t_axis(n)
    u = t / dur
    out = np.zeros((n, 2))
    for ch in range(2):
        nz = bandpass(rng.standard_normal(n), 1800.0, 12000.0, 2)
        nz = nz + 0.5 * resonator_bank(nz, [690, 1580, 3170, 5900], 25.0, [0.4, 0.5, 0.4, 0.3])
        roll = 1.0 - 0.25 * (0.5 + 0.5 * np.sin(TWO_PI * 16.0 * t + rng.uniform(0, 6)))
        out[:, ch] = nz * roll * u ** 2.6
    out = out / max(1e-9, np.max(np.abs(out)))
    return dsp.fade(out, 0.01, 0.012) * vel * 0.35


def tamtam(vel, rng, dur=7.0):
    n = n_of(dur)
    t = t_axis(n)
    fr = [62, 91, 127, 168, 214, 270, 335, 410, 497, 600, 715, 850, 1130, 1480]
    out = np.zeros((n, 2))
    for ch in range(2):
        x = np.zeros(n)
        for i, f in enumerate(fr):
            f = f * rng.uniform(0.98, 1.02)
            tau = 0.05 + 0.12 * i
            t60 = 6.0 - 0.25 * i
            x += (1.0 / (1 + 0.25 * i)) * np.sin(TWO_PI * f * t + rng.uniform(0, 6)) * (1 - np.exp(-t / tau)) * np.power(10.0, -3 * t / t60)
        sh = bandpass(rng.standard_normal(n), 600.0, 4000.0, 2) * (1 - np.exp(-t / 0.6)) * np.power(10.0, -3 * t / 4.5) * 0.25
        out[:, ch] = x + sh
    out[:n_of(0.004)] *= np.linspace(0, 1, n_of(0.004))[:, None]
    out = out / max(1e-9, np.max(np.abs(out)))
    return dsp.fade(out, 0.0, 0.8) * vel * 0.5


def boom(vel, rng, f0=58.0, f1=33.0, dur=2.6):
    n = n_of(dur)
    t = t_axis(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.25)
    x = np.sin(TWO_PI * np.cumsum(f) / SR) * np.power(10.0, -3.0 * t / 1.8)
    x = np.tanh(2.0 * x) / math.tanh(2.0)
    k = n_of(0.04)
    th = sos(rng.standard_normal(k), "lowpass", 400.0, 2) * np.exp(-np.arange(k) / (0.01 * SR))
    x[:k] += 0.3 * th / max(1e-9, np.max(np.abs(th)))
    x[:n_of(0.004)] *= np.linspace(0, 1, n_of(0.004))
    return dsp.fade(sos(x, "highpass", 24.0, 2), 0.0, 0.2) * vel * 0.7


def breath_hit(vel, rng, dur=0.32):
    """A rhythmic exhaled 'hah' (the chase's breathing percussion)."""
    n = n_of(dur)
    t = t_axis(n)
    env = (1.0 - np.exp(-t / 0.012)) * np.exp(-t / 0.09)
    src = pink(n, rng)
    y = resonator_bank(src, [750, 1150, 2500, 3500], [6.0, 7.0, 8.0, 8.0], [1.0, 0.7, 0.35, 0.2]) \
        + 0.25 * bandpass(white(n, rng), 3000.0, 9000.0, 2)
    y = y * env
    return dsp.fade(y / max(1e-9, np.max(np.abs(y))), 0.0, 0.02) * vel * 0.45


def riser(dur, vel, rng):
    n = n_of(dur)
    t = t_axis(n)
    u = t / dur
    fc = 250.0 * 40.0 ** u
    nz = tv_bandpass(white(n, rng), fc, q=2.0, block=256) * u ** 2.2
    tone = np.sin(TWO_PI * np.cumsum(110.0 * 2.0 ** (2.0 * u)) / SR) * u ** 2.0 * 0.3
    y = nz / max(1e-9, np.max(np.abs(nz))) + tone
    return dsp.fade(y, 0.01, 0.01) * vel * 0.4


def pizz_note(midi, vel, rng):
    f0 = hz(midi)
    x = karplus_strong(f0, 1.8, t60=1.1, brightness=0.35, rng=rng)
    x = sos(x, "lowpass", 1400.0, 2)
    x = x / max(1e-9, np.max(np.abs(x)))
    k = n_of(0.03)
    th = sos(rng.standard_normal(k), "lowpass", 300.0, 2) * np.exp(-np.arange(k) / (0.006 * SR))
    x[:k] += 0.3 * th / max(1e-9, np.max(np.abs(th)))
    return dsp.fade(x, 0.0005, 0.1) * vel * 0.5


def spiccato(midi, vel, rng, dur=0.16):
    f0 = hz(midi)
    n = n_of(dur + 0.25)
    t = t_axis(n)
    env = (1.0 - np.exp(-t / 0.004)) * np.where(t < dur, np.exp(-t / 0.12), np.exp(-dur / 0.12) * np.exp(-(t - dur) / 0.04))
    x = np.zeros(n)
    for _ in range(3):
        x += saw(f0 * 2.0 ** (rng.normal(0, 6) / 1200.0), n, phase0=rng.uniform())
    x = sos(x / 3.0, "lowpass", 1800.0 + 2000.0 * vel, 2) * env
    k = n_of(0.015)
    x[:k] += 0.15 * bandpass(rng.standard_normal(k), 1000.0, 5000.0, 2) * np.linspace(1, 0, k)
    return dsp.fade(x, 0.0, 0.02) * vel


# ============================================================================ the score buffer
class Score:
    def __init__(self, seed=0):
        self.rng = np.random.default_rng(dsp.stable_seed("red-score", seed))
        self.b = {k: np.zeros((N, 2), np.float32) for k in ("main", "feat", "hits")}
        self.hall = np.zeros(N, np.float32)            # reverb send (mono)
        self.s24 = {}
        self.marks = []
        self.counts = {}

    # ---------------------------------------------------------------- placement
    @staticmethod
    def _cut(x, t, sr):
        for c in CUTS:
            if t < c - 1e-6:
                k = int(round((c - t) * sr))
                if k >= len(x):
                    return x
                if k <= 0:
                    return x[:0]
                y = np.array(x[:k], dtype=np.float64)
                f = min(k, int(0.008 * sr))
                w = np.linspace(1.0, 0.0, f)
                y[-f:] *= w[:, None] if y.ndim == 2 else w
                return y
        return x

    def put(self, x, t, bus="main", gain_db=0.0, pan=0.0, send=0.3):
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = dsp.pan_mono(x, pan) * math.sqrt(2.0) if pan else dsp.to_stereo(x)
        elif pan:
            x = dsp.pan_stereo(x, pan)
        x = self._cut(x, t, SR)
        if len(x) == 0:
            return
        g = db2lin(gain_db)
        at = n_of(t)
        dsp.mix_into(self.b[bus], (x * g).astype(np.float32), at)
        if send > 0:
            dsp.mix_into(self.hall, (x.mean(axis=1) * g * send).astype(np.float32), at)

    def put24(self, key, x, t, gain_db=0.0):
        x = self._cut(np.asarray(x, dtype=np.float64), t, SR2)
        if len(x) == 0:
            return
        if key not in self.s24:
            self.s24[key] = np.zeros((N2, 2), np.float32)
        dsp.mix_into(self.s24[key], (x * db2lin(gain_db)).astype(np.float32), int(round(t * SR2)))

    def mark(self, t, label):
        self.marks.append((round(float(t), 3), label))

    def _count(self, k, v=1):
        self.counts[k] = self.counts.get(k, 0) + v

    # ---------------------------------------------------------------- instruments
    def mbox(self, t, midi, vel=0.6, cents=0.0, wow=0.0, damp=None, bright=1.0, gain_db=0.0, send=0.35, pan=None):
        x = mbox_note(m(midi), vel, self.rng, cents, wow, damp, bright)
        p = float(np.clip((m(midi) - 76) / 30.0, -0.35, 0.35)) if pan is None else pan
        self.put(x, t, "feat", gain_db, p, send)
        self._count("music box notes")

    def windup(self, t, count, gain_db=-12.0):
        self.put(windup_clicks(count, self.rng), t, "feat", gain_db, 0.15, 0.1)

    def violin(self, notes, cents=(), vib=(), rate=(), bright=1.0, gain_db=0.0, send=0.45, lufs=-21.0):
        y, t0 = violin_phrase(notes, self.rng, cents, vib, rate, bright)
        lv = dsp.loudness_integrated(y)
        if np.isfinite(lv):
            y = y * db2lin(lufs - lv)
        self.put(y, t0, "feat", gain_db, -0.08, send)
        self._count("violin notes", len(notes))

    def strings(self, t0, t1, names, vel=0.5, att=0.6, rel=0.8, style="norm", dyn=(), gain_db=0.0, voices=None):
        names = _names(names)
        for nm in names:
            f0 = hz(nm)
            n = int((t1 - t0 + rel * 1.6 + 0.05) * SR2) + 1
            tt = np.arange(n) / SR2
            if style == "harm":
                x = section_tone(f0, n, self.rng, voices or 3, 3.0, 0.002, 5.0, kind="sine")
            elif style == "pont":
                x = section_tone(f0, n, self.rng, voices or 5, 9.0, 0.003, 5.5, trem=0.85)
            elif style == "trem":
                x = section_tone(f0, n, self.rng, voices or 5, 7.0, 0.003, 5.5, trem=0.7)
            else:
                x = section_tone(f0, n, self.rng, voices or 5, 7.0, 0.0045, 5.3)
            gate = t1 - t0
            a = max(att, 0.01)
            env = np.where(tt < a, np.sin(0.5 * np.pi * np.clip(tt / a, 0, 1)) ** 2, 1.0)
            env = np.where(tt > gate, np.power(10.0, -3.0 * np.maximum(tt - gate, 0) / max(rel, 0.02)), env)
            if dyn:
                env = env * db2lin(_interp(dyn, t0 + tt, 0.0))
            key = "norm" if style == "trem" else style
            self.put24(key, x * (env * vel)[:, None], t0, gain_db)
            self._count(f"strings ({style}) notes")

    def choir(self, t0, t1, names, vowel="u", vel=0.5, att=1.0, rel=1.2, dyn=(), gain_db=0.0, voices=4):
        """vowel: 'u' | 'o' | 'a' | 'm' or [(t, vowel)] morph points (film time)."""
        names = _names(names)
        n = int((t1 - t0 + rel * 1.6 + 0.05) * SR2) + 1
        tt = np.arange(n) / SR2
        src = np.zeros((n, 2))
        for nm in names:
            src += choir_tone(hz(nm), n, self.rng, voices)
        for ch in range(2):
            src[:, ch] = onepole_lp(src[:, ch], 900.0, SR2) * 2.0 + 0.05 * pink(n, self.rng)
        pts = [(t0, vowel)] if isinstance(vowel, str) else sorted(vowel)
        vs = sorted(set(v for _, v in pts))
        y = np.zeros((n, 2))
        if len(vs) == 1:
            for ch in range(2):
                y[:, ch] = formant(src[:, ch], vs[0])
        else:
            for v in vs:
                w = _interp([(t, 1.0 if vv == v else 0.0) for t, vv in pts], t0 + tt, 0.0)
                for ch in range(2):
                    y[:, ch] += formant(src[:, ch], v) * w
        gate = t1 - t0
        a = max(att, 0.02)
        env = np.where(tt < a, np.sin(0.5 * np.pi * np.clip(tt / a, 0, 1)) ** 2, 1.0)
        env = np.where(tt > gate, np.power(10.0, -3.0 * np.maximum(tt - gate, 0) / max(rel, 0.02)), env)
        if dyn:
            env = env * db2lin(_interp(dyn, t0 + tt, 0.0))
        self.put24("choir", y * (env * vel)[:, None], t0, gain_db)
        self._count("choir chords")

    def brass(self, t, dur, names, vel=0.6, style="horn", dyn=(), gain_db=0.0, bus="main", att=None, rel=None):
        names = _names(names)
        for i, nm in enumerate(names):
            mm = m(nm)
            if style == "stopped":
                y = brass_note(mm, dur, vel, self.rng, 2, att or 0.05, rel or 0.2, 0.8, dyn, stopped=True)
            elif style == "trombone":
                y = brass_note(mm, dur, vel, self.rng, 3, att or 0.07, rel or 0.3, 0.8, dyn)
            else:
                y = brass_note(mm, dur, vel, self.rng, 3, att or 0.06, rel or 0.25, 1.0, dyn)
            pan = 0.25 * (1 if i % 2 else -1) * (0.5 + 0.5 * (len(names) > 1))
            self.put(y, t + self.rng.uniform(0, 0.008), bus, gain_db, pan, 0.4)
            self._count("brass notes")

    def timp(self, t, note, vel, bus="main", gain_db=0.0, soft=False, send=0.3):
        x = timp_hit(m(note), int(round(np.clip(vel, 0.02, 1.2) * 100)), int(self.rng.integers(0, 6)), soft)
        self.put(x, t, bus, gain_db, -0.15, send)
        self._count("timpani strokes")

    def roll(self, t0, t1, note, v0, v1, bus="main", gain_db=0.0, rate=16.0):
        t = t0
        while t < t1:
            u = (t - t0) / max(t1 - t0, 1e-6)
            v = v0 * (v1 / max(v0, 1e-3)) ** u
            self.timp(t + self.rng.uniform(-0.006, 0.006), note, v * self.rng.uniform(0.9, 1.05), bus, gain_db - 4.0, send=0.35)
            t += 1.0 / rate

    def drum(self, t, vel, bus="main", gain_db=0.0):
        self.put(bass_drum(vel, self.rng), t, bus, gain_db, 0.0, 0.3)
        self._count("gran cassa")

    def crash(self, t, vel, bus="hits", gain_db=0.0, dur=4.5):
        self.put(crash(vel, self.rng, dur), t, bus, gain_db, 0.2, 0.35)
        self._count("cymbals")

    def swell(self, t0, t1, vel, gain_db=0.0):
        self.put(cym_swell(t1 - t0, vel, self.rng), t0, "main", gain_db, 0.2, 0.35)

    def tamtam(self, t, vel, bus="hits", gain_db=0.0):
        self.put(tamtam(vel, self.rng), t, bus, gain_db, -0.2, 0.4)
        self._count("tam-tam")

    def boom(self, t, vel, bus="hits", gain_db=0.0):
        self.put(boom(vel, self.rng), t, bus, gain_db, 0.0, 0.1)
        self._count("booms")

    def breath(self, t, vel, pan=0.0, gain_db=0.0):
        self.put(breath_hit(vel, self.rng), t, "main", gain_db, pan, 0.25)
        self._count("breath hits")

    def riser(self, t0, t1, vel, gain_db=0.0):
        self.put(riser(t1 - t0, vel, self.rng), t0, "main", gain_db, 0.0, 0.3)

    def pizz(self, t, note, vel, bus="main", gain_db=0.0):
        self.put(pizz_note(m(note), vel, self.rng), t, bus, gain_db, -0.2, 0.35)
        self._count("pizzicati")

    def spic(self, t, note, vel, gain_db=0.0):
        self.put(spiccato(m(note), vel, self.rng), t + self.rng.uniform(-0.004, 0.004), "main", gain_db, -0.2, 0.2)
        self._count("spiccati")

    def stab(self, t, names, vel=1.0, gain_db=0.0):
        """Tutti hit: short brass chord + timpani + gran cassa + crash + boom (hits bus)."""
        self.brass(t, 0.35, names, vel, "horn", gain_db=gain_db - 2.0, bus="hits", att=0.012, rel=0.4)
        self.timp(t, "A2", vel, "hits", gain_db - 1.0)
        self.drum(t + 0.006, vel, "hits", gain_db - 3.0)
        self.crash(t + 0.003, 0.8 * vel, "hits", gain_db - 3.0, dur=2.5)
        self.boom(t + 0.012, 0.6 * vel, "hits", gain_db - 6.0)

    # ---------------------------------------------------------------- mixdown
    def finish(self):
        """24 kHz sections -> EQ -> 2x up -> main (+ hall send); hall reverb per segment; calibrate."""
        eq = {"dark": [("highpass", 40.0), ("lowpass", 1500.0)],
              "norm": [("highpass", 50.0), ("lowpass", 5000.0)],
              "pont": [("highpass", 700.0), ("lowpass", 9000.0)],
              "harm": [("highpass", 200.0), ("lowpass", 8000.0)],
              "choir": [("highpass", 60.0), ("lowpass", 6000.0)]}
        sends = {"dark": 0.45, "norm": 0.45, "pont": 0.5, "harm": 0.6, "choir": 0.6}
        for key, x in self.s24.items():
            y = np.asarray(x, dtype=np.float64)
            for kind, f in eq[key]:
                y = sos(y, kind, f, 2, sr=SR2)
            if key == "norm":
                y = y + 0.35 * np.stack([resonator_bank(y[:, c], [290.0, 520.0, 1150.0, 2600.0], 2.5,
                                                        [1.0, 0.7, 0.5, 0.4], SR2) for c in range(2)], 1)
            if key == "pont":
                y = y + 0.5 * np.stack([resonator_bank(y[:, c], [3200.0, 4800.0], 3.0, [1.0, 0.6], SR2) for c in range(2)], 1)
            up = np.stack([signal.resample_poly(np.ascontiguousarray(y[:, c]), 2, 1) for c in range(2)], 1)[:N]
            up = dsp.pad_to(up, N)
            self.b["main"] += up.astype(np.float32)
            self.hall += (up.mean(axis=1) * sends[key]).astype(np.float32)
            self.s24[key] = None
        # hall reverb, one segment per hard cut (a cut silences the tails too)
        ir = make_space_ir("hall")
        edges = [0] + [n_of(c) for c in CUTS] + [N]
        for a, b in zip(edges[:-1], edges[1:]):
            seg = np.asarray(self.hall[a:b], dtype=np.float64)
            if not np.any(seg):
                continue
            wet = sparse_convolve(seg, ir, wet_db=-4.0)
            if b < N:
                f = n_of(0.008)
                wet[-f:] *= np.linspace(1.0, 0.0, f)[:, None]
            self.b["main"][a:b] += wet.astype(np.float32)
        self.hall = None
        tot = self.b["main"].astype(np.float64) + self.b["feat"] + self.b["hits"]
        lv = dsp.loudness_integrated(tot)
        g = db2lin(SCORE_LUFS - lv) if np.isfinite(lv) else 1.0
        tail = n_of(0.6)
        w = np.ones(N)
        w[-tail:] = np.linspace(1.0, 0.0, tail) ** 2
        gr = {}
        for k in self.b:
            y = self.b[k].astype(np.float64) * (g * w)[:, None]
            # bus peak control: transients may sit at most BUS_PLR dB over the score's loudness
            y, lg = dsp.limiter(y, SCORE_LUFS + BUS_PLR[k], lookahead_ms=3.0, release_ms=120.0, return_gain=True)
            gr[k] = round(float(-dsp.lin2db(np.min(lg))), 2)
            hop = n_of(0.25)
            blk = -dsp.lin2db(lg[: (N // hop) * hop].reshape(-1, hop).min(axis=1))
            top = np.argsort(blk)[::-1][:6]
            gr[k + "_detail"] = dict(over_1db_s=round(float(np.sum(lg < db2lin(-1.0)) / SR), 2),
                                     over_3db_s=round(float(np.sum(lg < db2lin(-3.0)) / SR), 2),
                                     worst=[(round(i * 0.25, 2), round(float(blk[i]), 1)) for i in sorted(top) if blk[i] > 0.5])
            self.b[k] = y.astype(np.float32)
        return dict(raw_lufs=round(float(lv), 2), gain_db=round(float(dsp.lin2db(g)), 2), bus_limiter_gr_db=gr)


# ============================================================================ the composition
def box_accomp(S, tm, bar, style="waltz", vel=0.4, cents=0.0, wow=0.0, bright=1.0, beats=(0, 1, 2)):
    for bt in beats:
        ch = chord_at(bar, bt)
        root, third, fifth = tones(ch, 57, 68)[0], *tones(ch, 64, 76)[1:]
        t = tm(bar * 3 + bt)
        if bt == 0:
            S.mbox(t, root, vel, cents, wow, bright=bright)
        elif style == "waltz":
            S.mbox(t, third, vel * 0.7, cents, wow, bright=bright)
            S.mbox(t, fifth, vel * 0.6, cents, wow, bright=bright)
        else:
            S.mbox(t, fifth if bt == 1 else third, vel * 0.75, cents, wow, bright=bright)


def pad_bars(S, tm, bars, t_end=None, vel=0.35, style="dark", gain_db=-14.0, att=0.9, rel=1.2, chords=None, lo_bass=True):
    """Sustained string chords following the tune's harmony, bar by bar (chord changes inside bars too)."""
    segs = []
    for bar in bars:
        for bt in (0, 1):
            ch = (chords or {}).get(bar) if chords else None
            ch = ch or chord_at(bar, bt)
            if bt == 1 and ch == (segs[-1][1] if segs else None):
                continue
            segs.append((tm(bar * 3 + bt), ch))
    for i, (t0, ch) in enumerate(segs):
        t1 = segs[i + 1][0] if i + 1 < len(segs) else (t_end if t_end is not None else t0 + 1.5)
        bass, upper = VOICING[ch]
        S.strings(t0, t1 + 0.12, upper, vel, att, rel, style, gain_db=gain_db)
        if lo_bass:
            S.strings(t0, t1 + 0.12, [bass], vel * 0.9, att, rel, "dark", gain_db=gain_db - 1.0)


def compose(S):
    R = S.rng
    # ------------------------------------------------------------------ s01 THE RULE (paper)
    child, never, path = A(1, "child"), A(2, "Never"), A(2, "path")
    q = (never - child) / 5.0
    tm = TempoMap([(0, child - q), (6, never)])
    S.windup(0.18, 6)
    S.mark(0.18, "s01 music box wound (key ratchet)")
    S.strings(0.05, never + 0.25, "A2 E3", 0.5, 1.6, 0.5, "dark", gain_db=-12.0)
    for t0, d, mm, b in melody(tm, 0, 7):
        S.mbox(t0, mm + 12, 0.8 if b == 1 else 0.66, damp=0.075 if b == 6 else None)
    for bar in range(3):
        ch = chord_at(bar)
        S.mbox(tm(bar * 3), tones(ch, 57, 68)[0], 0.4, damp=0.075 if bar == 2 else None)
    S.mark(child, "box E6 on 'child'")
    S.boom(never, 0.85)
    S.strings(never, path, "A1 Bb1 E2", 0.6, 0.25, 0.18, "pont", dyn=[(never, -10.0), (path, 0.0)], gain_db=-8.0)
    S.strings(never, path, "A1 Bb1", 0.6, 0.12, 0.2, "dark", gain_db=-6.0)
    S.mark(never, "the box JAMS on 'Never': sub boom, low cluster")
    S.mark(path, "cluster cut on 'path' (eyes out)")

    # ------------------------------------------------------------------ s02 THE HOOD (the box carries the village)
    gm = A(4, "grandmother")
    tm2 = TempoMap([(0, 7.6), (15, gm), (16, gm + 0.74), (17, gm + 1.52), (18, gm + 2.42), (19, gm + 3.45)])
    S.windup(7.0, 4, gain_db=-15.0)
    sour = {15: -45.0, 16: -22.0, 17: -38.0, 18: -58.0, 19: -85.0}
    for t0, d, mm, b in melody(tm2, 0, 20):
        v = 0.6 if b < 15 else [0.66, 0.5, 0.45, 0.38, 0.3][b - 15]
        S.mbox(t0, mm + 12, v + (0.08 if b in (1, 13) else 0.0), sour.get(b, 0.0), 0.0 if b < 15 else 6.0 + 4.0 * (b - 15))
    for bar in range(5):
        box_accomp(S, tm2, bar, "waltz", 0.36)
    box_accomp(S, tm2, 5, "waltz", 0.3, cents=-30.0, wow=8.0, beats=(0,))
    S.mark(A(3, "hood"), "box under 'tied ... red hood'")
    S.mark(gm, "box F goes sour on 'grandmother' (-45 cents)")
    S.mark(gm + 3.45, "the box runs down and stops")
    pad_bars(S, tm2, range(5), t_end=gm + 0.4, vel=0.32, gain_db=-16.0)
    S.strings(gm, 21.8, "A1 Bb1", 0.4, 1.5, 0.8, "dark", dyn=[(gm, -10.0), (20.5, -2.0), (21.8, -6.0)], gain_db=-10.0)

    # ------------------------------------------------------------------ s02-s03 the solo violin takes the tune into the forest
    valley, deeper, quieter = A(5, "valley"), A(5, "deeper"), A(5, "quieter")
    tm3 = TempoMap([(0, 24.6), (6, 29.4), (7, 30.35), (9, valley)])
    notes = [(22.2, 2.3, m("A4"), 0.42)]
    for t0, d, mm, b in melody(tm3, 0, 9):
        notes.append((t0, d * 0.97, mm, 0.62 if b == 1 else 0.55))
    notes.append((valley, quieter + 0.6 - valley, m("E4"), 0.5))
    S.violin(notes, cents=[(30.3, 0.0), (valley, -15.0), (quieter + 0.1, -42.0)],
             vib=[(22.0, 18.0), (deeper, 22.0), (quieter, 40.0)], rate=[(22.0, 5.6), (deeper, 5.3), (quieter, 4.3)],
             gain_db=5.0)
    S.mark(22.2, "solo violin takes the tune (A) out of the gate")
    S.mark(A(5, "down"), "violin slows and sags in pitch: 'down into the valley'")
    pad_bars(S, tm3, range(3), t_end=valley, vel=0.3, gain_db=-17.0)
    S.strings(valley, quieter + 0.8, "E2 B2", 0.3, 0.8, 0.6, "dark", gain_db=-17.0)
    S.strings(deeper, quieter + 0.8, "A1 Bb1 E2", 0.5, 0.7, 0.4, "dark", dyn=[(deeper, -12.0), (quieter, 0.0)], gain_db=-8.0)
    S.choir(deeper, quieter + 0.8, "A1 E2", "u", 0.5, 0.9, 0.5, dyn=[(deeper, -14.0), (quieter, -4.0)], gain_db=-10.0)
    S.mbox(deeper + 0.25, "A5", 0.34, -50.0, 14.0, send=0.9)
    S.mbox(deeper + 0.95, "E6", 0.3, -70.0, 16.0, send=0.9)
    S.mark(deeper, "dark cluster + ghost box (detuned) on 'deeper'")
    S.mark(quieter, "THE SILENCE on 'quieter' (mix gate)")

    # ------------------------------------------------------------------ s04 THE WOLF
    wolf, girls = A(6, "wolf"), A(7, "girls")
    S.brass(wolf, 0.5, "E3", 0.55, "stopped", gain_db=-3.0)
    S.brass(wolf + 0.5, 1.9, "A2", 0.6, "stopped", dyn=[(0.0, 0.0), (1.9, -9.0)], gain_db=-3.0)
    S.timp(wolf, "A2", 0.6, "hits")
    S.boom(wolf, 0.45)
    S.mark(wolf, "'wolf': stopped horns E-A (the call, inverted), timpani, boom")
    S.strings(wolf, girls + 0.05, "A1 E2", 0.5, 0.4, 0.3, "pont", dyn=[(wolf, -14.0), (girls, 0.0)], gain_db=-9.0)
    for i, tb in enumerate(accel_times(wolf + 0.9, girls, 64.0, 128.0)):
        u = (tb - wolf) / (girls - wolf)
        S.timp(tb, "A2", 0.3 + 0.35 * u, soft=True, gain_db=2.0)
        S.timp(tb + 0.15 * (1 - 0.4 * u), "A2", (0.3 + 0.35 * u) * 0.65, soft=True, gain_db=2.0)
    S.mark(wolf + 0.9, "heartbeat timpani accelerating to 'girls'")
    skid = ST("s04", 12.3)
    q4 = (skid - girls) / 14.0
    pat = ["A2", "A2", "A3", "A2", "C3", "A2", "E3", "A2"]
    for k in range(14):
        tb = girls + k * q4
        bb = k % 4
        S.timp(tb, "A2" if bb != 3 else "E2", [1.0, 0.6, 0.85, 0.65][bb], "hits" if k == 0 else "main")
        if bb in (0, 2):
            S.drum(tb, 0.9 if bb == 0 else 0.65, "hits" if k == 0 else "main")
        if bb in (1, 3):
            S.breath(tb, 0.55 + 0.15 * k / 14, -0.35 if bb == 1 else 0.35)
        for e in range(2):
            idx = bb * 2 + e
            S.spic(tb + e * q4 / 2, pat[idx], 0.95 if idx in (0, 3, 6) else 0.6)
    S.crash(girls, 0.6, gain_db=-9.0)   # broadband: kept under the word
    S.mark(girls, "the chase: timpani, gran cassa, spiccato, breaths (142 bpm)")
    S.strings(girls, skid, "A4 C5 E5", 0.55, 0.05, 0.12, "pont", dyn=[(girls, -8.0), (skid, 0.0)], gain_db=-8.0)
    S.strings(girls, skid, "A2 E3", 0.6, 0.05, 0.12, "trem", gain_db=-10.0)
    for b, L, nm in [(4, 1, "A3"), (5, 3, "E4"), (8, 1, "D4"), (9, 1, "C4"), (10, 2, "B3"), (12, 1, "C4"), (13, 1, "A3")]:
        S.brass(girls + b * q4, L * q4 * 0.95, nm, 0.8, "horn", gain_db=-4.0)
        S.brass(girls + b * q4, L * q4 * 0.95, m(nm) - 12, 0.7, "trombone", gain_db=-7.0)
    S.stab(skid, ["A2", "E3", "Bb3", "E4"], 1.0)
    S.mark(skid, "skid: tutti stab (picture beat s04 12.3)")
    S.strings(skid + 0.12, 51.95, "A1 Bb1", 0.45, 0.3, 0.2, "pont", gain_db=-11.0)
    S.riser(51.15, 52.0, 0.7)
    S.mark(51.75, "whip: riser into s05")

    # ------------------------------------------------------------------ s05 DEEP SNOW
    off, ridge, snow, stopped, waited = A(8, "off"), A(8, "ridge"), A(8, "snow"), A(8, "stopped"), A(8, "waited")
    tm5 = TempoMap([(0, 52.0), (4, off), (8, ridge), (12, snow), (16, stopped)])
    for k in range(12):
        tb = tm5(k)
        qk = tm5(k + 1) - tb
        bb = k % 4
        up = 1 if k >= 8 else 0
        S.timp(tb, m("A2") + up, [1.0, 0.62, 0.85, 0.7][bb], "hits" if (bb == 0 and k in (0, 4, 8)) else "main")
        if bb in (0, 2):
            S.drum(tb, 0.9 if bb == 0 else 0.7, "hits" if (bb == 0 and k in (0, 4, 8)) else "main")
        if bb == 3:
            S.drum(tb + qk / 2, 0.55)
        if bb in (1, 3):
            S.breath(tb, 0.65, -0.35 if bb == 1 else 0.35)
        for e in range(2):
            idx = bb * 2 + e
            S.spic(tb + e * qk / 2, m(pat[idx]) + up, 0.95 if idx in (0, 3, 6) else 0.62)
    S.crash(52.0, 0.7, gain_db=-3.0)
    S.stab(off, ["A2", "E3", "A3", "C4"], 0.9, gain_db=-4.0)       # under the line: hit, but "the path" reads
    S.stab(ridge, ["Bb2", "F3", "Bb3", "D4"], 0.95, gain_db=-4.0)
    S.mark(52.0, "s05 downbeat after the whip")
    S.mark(off, "'off' (the path): stab")
    S.mark(ridge, "'ridge': stab, the climb a semitone up (Bb)")
    S.strings(52.0, ridge, "A4 C5 E5", 0.55, 0.05, 0.1, "pont", dyn=[(52.0, -6.0), (ridge, 0.0)], gain_db=-8.0)
    S.strings(ridge, snow, "Bb4 D5 F5", 0.6, 0.05, 0.1, "pont", dyn=[(ridge, -3.0), (snow, 0.0)], gain_db=-8.0)
    S.strings(52.0, snow, "A1 E2", 0.6, 0.1, 0.15, "trem", gain_db=-9.0)
    S.brass(52.0, ridge - 52.0, "A3 E4", 0.6, "horn", dyn=[(0.0, -8.0), (ridge - 52.0, 0.0)], gain_db=-6.0)
    S.brass(ridge, snow - ridge, "Bb3 F4", 0.7, "horn", dyn=[(0.0, -4.0), (snow - ridge, 0.0)], gain_db=-6.0)
    S.brass(52.0, snow - 52.0, "A1 E2", 0.55, "trombone", dyn=[(0.0, -8.0), (snow - 52.0, 0.0)], gain_db=-9.0)
    # the fall: big hit, then the music stumbles in half time until 'stopped'
    S.stab(snow, ["A1", "E2", "A2", "E3"], 1.0, gain_db=-3.0)
    S.boom(snow, 0.7)
    S.mark(snow, "'snow': the fall - big hit, half time")
    q5 = (stopped - snow) / 4.0
    for k, (dt, v) in enumerate([(0.0, 0.0), (1.5, 0.5), (2.0, 0.6), (3.5, 0.45)]):
        if v:
            S.timp(snow + dt * q5, "A2", v, soft=True)
    S.strings(snow + 0.2, stopped, "A1 Bb1", 0.45, 0.2, 0.06, "pont", gain_db=-11.0)
    S.mark(stopped, "'stopped': the orchestra stops dead (tails ring)")
    S.choir(waited, 66.5, "A1 E2 A2", [(waited, "u"), (63.5, "u"), (65.2, "a")], 0.6, 1.4, 0.2,
            dyn=[(waited, -20.0), (63.0, -13.0), (65.5, -3.0), (66.5, 0.0)], gain_db=-6.0)
    S.strings(62.0, 66.5, "A3 Bb3 E4 F4", 0.5, 1.5, 0.1, "pont", dyn=[(62.0, -22.0), (66.4, 0.0)], gain_db=-8.0)
    S.strings(63.0, 66.5, "A1 E2", 0.6, 1.2, 0.1, "trem", dyn=[(63.0, -16.0), (66.4, 0.0)], gain_db=-8.0)
    S.brass(64.0, 2.5, "A1 E2 Bb2", 0.8, "trombone", dyn=[(0.0, -18.0), (2.5, 0.0)], gain_db=-6.0, att=0.6)
    S.roll(64.0, 66.46, "A2", 0.12, 1.0)
    S.swell(64.6, 66.5, 0.9)
    S.riser(65.2, 66.5, 0.8)
    S.mark(waited, "'waited': the low choir breathes in; long build")
    S.mark(66.5, "HARD CUT to the valley: subito pp, wide")

    # ------------------------------------------------------------------ s06 RED HOODS
    cut = 66.5
    house, gm2, hoods, winter = A(10, "house"), A(10, "grandmother"), A(11, "hoods"), A(11, "winter")
    S.strings(cut, 81.4, "A5 E6 B6", 0.4, 0.08, 1.5, "harm",
              dyn=[(cut, -2.0), (70.0, -6.0), (winter, -3.0), (80.5, -9.0)], gain_db=-8.0)
    S.strings(cut, 82.2, "A1", 0.5, 0.1, 1.0, "dark", gain_db=-7.0)
    S.choir(house, 78.0, "A2 E3", "u", 0.5, 1.2, 1.5, dyn=[(house, -12.0), (house + 1.3, -4.0), (77.0, -6.0)], gain_db=-7.0)
    S.choir(gm2, gm2 + 3.0, "Bb2", "u", 0.45, 0.4, 1.2, gain_db=-10.0)
    S.tamtam(gm2, 0.45)
    S.brass(gm2, 1.4, "F3", 0.45, "stopped", gain_db=-8.0)
    S.brass(gm2 + 1.4, 2.6, "E3", 0.4, "stopped", dyn=[(0.0, 0.0), (2.6, -10.0)], gain_db=-8.0)
    S.mark(house, "choir enters on 'house'")
    S.mark(gm2, "'grandmother': F-E motif, tam-tam, cluster")
    tmh = TempoMap([(0, hoods), (3, winter)])
    for t0, d, mm, b in melody(tmh, 0, 10):
        S.mbox(t0, mm + 12, 0.5 - 0.012 * b, -30.0, 10.0, send=1.1)
    pulse = tmh(9)
    S.boom(pulse, 0.5)
    S.timp(pulse, "A2", 0.45, "hits")
    S.strings(winter - 0.2, pulse + 1.0, "A3 C4 E4 B4", 0.5, 1.2, 1.2, "dark",
              dyn=[(winter, -10.0), (78.5, -4.0), (pulse, -12.0)], gain_db=-11.0)
    S.mark(hoods, "ghost music box (the children) on 'hoods', one bar per winter")
    S.mark(pulse, "grid pulse (picture beat s06 13.34): boom + box E")

    # ------------------------------------------------------------------ s07 GRANDMOTHER
    G, ch7, alone = A(12, "Grandmother"), A(12, "child"), A(12, "alone")
    eyes, leap = ST("s07", 4.6), ST("s07", 12.6)
    S.choir(81.0, G + 0.3, "A1 E2", "u", 0.5, 1.5, 0.8, dyn=[(81.0, -14.0), (G, -10.0)], gain_db=-4.0)
    S.choir(G, 87.5, "A1 E2 F2", [(G, "u"), (G + 1.5, "a")], 0.55, 0.6, 0.6,
            dyn=[(G, -12.0), (G + 1.8, -4.0), (alone, -4.0), (87.3, -7.0)], gain_db=-4.0)
    S.tamtam(G, 0.55)
    S.brass(G, 87.3 - G, "A1 E2", 0.5, "trombone", dyn=[(0.0, -14.0), (2.0, -6.0), (4.4, -8.0)], gain_db=-6.0, att=0.8)
    S.timp(ch7, "A2", 0.55, "hits")
    S.drum(ch7, 0.5, "hits")
    S.pizz(ch7, "A1", 0.8, "hits")
    S.strings(eyes, leap, "E6 F6 B6", 0.4, 0.8, 0.2, "pont", dyn=[(eyes, -16.0), (alone, -8.0), (leap - 0.1, 0.0)], gain_db=-12.0)
    S.mark(G, "'Grandmother': choir swell (oo->ah), tam-tam, trombones")
    S.mark(ch7, "'child': the legs touch down (timpani, drum, pizz)")
    S.mark(eyes, "the eye cluster: glass harmonics (picture beat s07 4.6)")
    steps = [(87.3, "A1 E2 F2 Bb2"), (88.9, "A1 F2 F#2 B2"), (90.4, "A1 F#2 G2 C3"), (91.9, "A1 G2 Ab2 C#3")]
    for i, (t0, chord) in enumerate(steps):
        t1 = steps[i + 1][0] if i + 1 < len(steps) else leap
        S.choir(t0, t1 + 0.08, chord, "a", 0.6, 0.25, 0.2, dyn=[(t0, -8.0 + 2.5 * i), (t1, -5.0 + 2.5 * i)], gain_db=-5.0)
    S.brass(87.3, leap - 87.3, "A1 E2 Bb2", 0.85, "trombone", dyn=[(0.0, -16.0), (leap - 87.3, 0.0)], gain_db=-7.0, att=0.4)
    S.strings(87.3, leap, "A2 Bb2 E3", 0.6, 0.4, 0.15, "trem", dyn=[(87.3, -14.0), (leap, 0.0)], gain_db=-8.0)
    S.roll(87.6, leap - 0.04, "A2", 0.12, 1.0)
    S.swell(92.1, leap, 0.85)
    S.stab(leap, ["A2", "E3", "A3", "C4", "E4"], 1.0)
    S.mark(87.3, "the charge: rising choir cluster, timpani roll")
    S.mark(leap, "the wolf's leap (picture beat s07 12.6): tutti hit")

    # ------------------------------------------------------------------ s08 FIRE
    t8, q8 = 94.0, 0.4
    for k in range(16):
        te = t8 + k * q8 / 2
        pos = k % 8
        acc = pos in (0, 3, 6)
        S.spic(te, "C3" if pos == 3 else "A2", 0.95 if acc else 0.55)
        if acc:
            S.timp(te, "E2" if pos == 6 else "A2", 0.95 - 0.25 * k / 16)
            S.drum(te, 0.8 - 0.2 * k / 16)
    for tt, ch, v in [(94.0, "A2 E3 Bb3", 0.9), (95.2, "A2 F3 B3", 0.8), (96.4, "A2 E3 Bb3", 0.65)]:
        S.brass(tt, 0.3, ch, v, "horn", gain_db=-4.0, att=0.015, rel=0.3)
    S.strings(94.0, 97.3, "A4 Bb4 E5", 0.55, 0.05, 0.6, "pont", dyn=[(94.0, 0.0), (97.3, -10.0)], gain_db=-9.0)
    S.mark(94.0, "s08 the fight: 3+3+2 percussion, brass stabs")
    for tb in np.arange(97.4, 101.9, 0.82):
        S.timp(tb, "A2", 0.42, soft=True, gain_db=2.0)
        S.timp(tb + 0.15, "A2", 0.28, soft=True, gain_db=2.0)
    S.strings(97.0, 102.6, "A1 E2", 0.4, 0.6, 0.6, "pont", dyn=[(97.0, -8.0), (102.4, -14.0)], gain_db=-8.0)
    S.mark(97.4, "heartbeat under 'basket ... Bread ... Wine'")
    L = A(14, "lantern")
    S.mbox(L, "A5", 0.72, bright=0.8, send=0.5)
    S.mbox(L, "A4", 0.38, bright=0.8)
    S.mbox(L + 0.62, "E6", 0.7, bright=0.8, send=0.5)
    S.mbox(L + 0.62, "C5", 0.3, bright=0.8)
    S.strings(L, 104.4, "F3 A3 C4 E4", 0.5, 0.9, 0.6, "dark", dyn=[(L, -12.0), (103.4, -5.0), (104.4, -8.0)], gain_db=-9.0)
    S.mark(L, "the music box on 'lantern' (the mother's gift)")
    fire = A(15, "fire")
    for t0, t1, ch in [(104.2, 105.0, "A3 C4 E4 A4"), (105.0, 105.8, "F3 A3 C4 F4"), (105.8, fire, "E3 G#3 B3 E4")]:
        S.strings(t0, t1 + 0.06, ch, 0.6, 0.15, 0.12, "trem", dyn=[(104.2, -14.0), (fire, 0.0)], gain_db=-8.0)
    S.roll(105.3, fire - 0.04, "E2", 0.15, 0.9)
    S.swell(105.0, fire, 0.9)
    S.riser(105.4, fire, 0.6)
    # the lullaby as a full orchestral statement (bars 5-8 of the tune)
    tmf = TempoMap([(12, fire), (18, fire + 6 * 0.45), (19, fire + 6 * 0.45 + 0.47), (20, fire + 6 * 0.45 + 0.95),
                    (21, fire + 6 * 0.45 + 1.44)])
    final = tmf(21)
    tut = -1.5            # the tutti's level (the film's loudest moment)
    for t0, d, mm, b in melody(tmf, 12, 21):
        S.strings(t0, t0 + d * 0.98, [mm + 12], 0.85, 0.04, 0.2, "norm", gain_db=tut - 3.0, voices=6)
        S.strings(t0, t0 + d * 0.98, [mm], 0.7, 0.04, 0.2, "norm", gain_db=tut - 6.0)
        S.brass(t0, d * 0.96, [mm - 12], 0.95, "horn", gain_db=tut - 1.0)
        S.brass(t0, d * 0.96, [mm], 0.8, "horn", gain_db=tut - 5.0)
    S.brass(final, 1.3, "A3 A4", 1.0, "horn", dyn=[(0.0, 0.0), (1.3, -4.0)], gain_db=tut - 1.0, rel=0.6)
    S.strings(final, final + 1.2, "A5 C6 E6", 0.85, 0.04, 0.9, "norm", gain_db=tut - 4.0, voices=6)
    harm = [(12, "Am"), (15, "Dm"), (18, "F"), (19, "E"), (21, "Am")]
    for i, (b, ch) in enumerate(harm):
        t0 = tmf(b)
        t1 = tmf(harm[i + 1][0]) if i + 1 < len(harm) else final + 1.2
        bass, upper = VOICING[ch]
        S.strings(t0, t1 + 0.05, upper, 0.75, 0.05, 0.6 if i == len(harm) - 1 else 0.2, "norm", gain_db=tut - 7.0)
        S.strings(t0, t1 + 0.05, [bass, m(bass) - 12], 0.8, 0.05, 0.6, "norm", gain_db=tut - 6.0)
        S.brass(t0, t1 - t0 + (0.6 if i == len(harm) - 1 else 0.0), [bass, m(bass) + 7], 0.9, "trombone", gain_db=tut - 5.0)
        S.choir(t0, t1 + 0.1, [bass] + upper.split()[:3], "a", 0.8, 0.12, 0.6 if i == len(harm) - 1 else 0.25, gain_db=tut - 5.0)
        S.drum(t0, 0.95 if i in (0, len(harm) - 1) else 0.75, gain_db=tut)
        S.timp(t0, "E2" if ch == "E" else "A2", 1.0, "main", gain_db=tut)
    S.roll(fire + 0.15, tmf(15) - 0.05, "A2", 0.5, 0.8)
    S.roll(final + 0.12, final + 1.3, "A2", 0.8, 0.3)
    S.crash(fire, 1.0)
    S.crash(final, 0.9)
    S.mark(fire, "'fire': the lullaby, full orchestra (brass, strings, choir, timpani, cymbals)")
    S.mark(final, "final A minor chord into the flash")

    # ------------------------------------------------------------------ s09 DAWN (solo violin)
    nv = A(18, "never")
    tm9 = TempoMap([(0, 111.96), (15, nv)])
    notes = [(t0, d * 0.96, mm, 0.4 + 0.2 * b / 15) for t0, d, mm, b in melody(tm9, 0, 15)]
    tail = [(nv, 1.75, "F5", 0.7), (nv + 1.78, 0.72, "E5", 0.55), (nv + 2.56, 0.78, "D5", 0.5),
            (nv + 3.4, 0.82, "C5", 0.48), (nv + 4.28, 0.86, "B4", 0.45), (nv + 5.2, 1.0, "G#4", 0.42),
            (nv + 6.25, 2.6, "A4", 0.4)]
    notes += [(t0, d, m(nm), v) for t0, d, nm, v in tail]
    S.violin(notes, vib=[(111.0, 16.0), (nv, 24.0), (nv + 6.0, 18.0)], rate=[(111.0, 5.4)], bright=0.9, gain_db=3.0)
    S.mark(111.96, "dawn: the solo violin, the whole tune")
    S.mark(nv, "violin's high F held on 'never'")
    pad_bars(S, tm9, range(5), t_end=nv, vel=0.3, gain_db=-17.0)
    for t0, t1, ch in [(nv, nv + 1.76, "Dm"), (nv + 1.76, nv + 3.38, "Dm"), (nv + 3.38, nv + 4.26, "F"),
                       (nv + 4.26, nv + 6.2, "E"), (nv + 6.2, nv + 8.6, "Am")]:
        bass, upper = VOICING[ch]
        S.strings(t0, t1 + 0.1, upper, 0.3, 0.8, 1.4, "dark", gain_db=-17.0)
        S.strings(t0, t1 + 0.1, [bass], 0.27, 0.8, 1.4, "dark", gain_db=-18.0)
    S.strings(nv, nv + 2.8, "E6 A6", 0.3, 0.9, 1.6, "harm", gain_db=-15.0)

    # ------------------------------------------------------------------ s10 MONSTER
    S.strings(126.0, 133.4, "A2 E3", 0.4, 2.0, 1.2, "dark", gain_db=-14.0)
    S.strings(129.0, 133.0, "E6", 0.25, 1.5, 1.0, "harm", gain_db=-19.0)
    mon = A(20, "monster")
    S.pizz(mon, "A1", 0.8, "hits")
    S.strings(mon, mon + 1.6, "A1 Bb1", 0.4, 0.05, 0.8, "pont", dyn=[(mon, 0.0), (mon + 1.6, -10.0)], gain_db=-13.0)
    S.mark(mon, "'monster': low pizz + cold cluster")
    t10 = 133.2
    tm10 = TempoMap([(27, t10), (36, 139.4)])
    notes = [(t0, d * 0.97, mm, 0.6 if b == 27 else 0.5) for t0, d, mm, b in melody(tm10, 27, 36)]
    S.violin(notes, vib=[(133.0, 22.0)], bright=0.95, gain_db=2.5)
    for b0, b1, ch in [(27, 30, "C"), (30, 33, "Fmaj7"), (33, 36, "E7")]:
        t0, t1 = tm10(b0), tm10(b1)
        bass, upper = VOICING[ch]
        S.strings(t0, t1 + 0.15, upper, 0.4, 0.9, 1.4, "dark", gain_db=-12.0)
        S.strings(t0, t1 + 0.15, [bass], 0.42, 0.9, 1.4, "norm", gain_db=-14.0)
    S.mark(t10, "the mother: the warm middle phrase (violin + strings)")
    for i, nm in enumerate(["E6", "A6", "C7"]):
        S.mbox(138.45 + 0.17 * i, nm, 0.26 - 0.03 * i, send=0.8)
    S.mark(138.45, "music-box twinkle into the white (years pass)")

    # ------------------------------------------------------------------ s11 GRANDMOTHER'S HOUSE (the box, warm)
    tm11 = TempoMap([(0, 139.4), (21, 152.0)])
    for t0, d, mm, b in melody(tm11, 0, 21):
        S.mbox(t0, mm + 12, 0.6 + (0.06 if b in (1, 13) else 0.0), bright=0.75, send=0.45)
    for bar in range(7):
        box_accomp(S, tm11, bar, "arp", 0.36, bright=0.7)
    pad_bars(S, tm11, range(7), t_end=152.0, vel=0.32, gain_db=-15.0)
    S.mark(139.4, "s11: the music box, warm, with strings")
    end = 152.0
    for i, nm in enumerate(["A3", "E4", "C#5", "A5"]):
        S.mbox(end + 0.03 * i, nm, 0.62 if nm == "A5" else 0.4, bright=0.75, send=0.5)
    S.mbox(end + 0.9, "A6", 0.3, bright=0.7, send=0.6)
    S.strings(end, 153.3, "A2 E3 A3 C#4 E4", 0.35, 0.3, 0.3, "dark", gain_db=-14.0)
    S.mark(end, "bar 8 on the flatten: A MAJOR (Picardy); one last high A")


def render_score(seed=0):
    S = Score(seed)
    compose(S)
    cal = S.finish()
    info = dict(marks=sorted(S.marks), counts=S.counts, calibration=cal)
    return S.b, info


if __name__ == "__main__":
    import os
    import time
    from .common import OUT
    t0 = time.time()
    buses, info = render_score()
    print(f"score rendered in {time.time() - t0:.1f}s", info["calibration"], info["counts"])
    tot = buses["main"].astype(np.float64) + buses["feat"] + buses["hits"]
    print("integrated", round(dsp.loudness_integrated(tot), 2), "TP", round(dsp.true_peak_db(tot), 2))
    os.makedirs(OUT, exist_ok=True)
    dsp.write_wav(os.path.join(OUT, "score_preview.wav"), tot, bits=24)
