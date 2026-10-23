"""OPPOSITE (full version): the complete score and sound, locked to the scene modules.

    cd productions/silhouette-noir
    python3 films/opposite_full/audio/mix.py                  # -> films/opposite_full/out/audio_master.wav
    python3 films/opposite_full/audio/mix.py --qa DIR         # ... and measure it, overview PNG in DIR
    python3 films/opposite_full/audio/mix.py --stand-ins      # missing scenes played from the bible's sound plan
    python3 films/opposite_full/audio/mix.py --only s05,s07   # just these sections (a quick listen; not mastered
                                                              #   to the film's loudness, written to out/audio_only.wav)
    python3 films/opposite_full/audio/mix.py --stems DIR      # ... and the five stems, at the master's gain
    python3 films/opposite_full/audio/mix.py --without s06    # treat s06 as missing (add --stand-ins to hear the bible's)

48 kHz stereo, exactly the timeline's 144 s, integrated -16 LUFS, true peak under -1 dBTP, and
digital silence from the moment the red dot is gone (s11) to the end.

THE SCORE is one continuous piece at 120 bpm, the tempo the picture is cut to (every scene starts
on a bar line; picture beats sit on 0.5 s steps). It is in B-flat minor on the Psycho chord of
the Bass cut (Bb Db F A, minor with a major seventh), and has two notes for its two people: hers
is B-flat, high; his is A, low, the chord's major seventh, a semitone (and three octaves) under
her. The strings, chords, pizzicato, tremolo, ostinato and the sip are the Bass cut's
(films/opposite_bass/audio/mix.py), the voices and real foley the first cut's recordings
(films/opposite/audio/gen); everything else is synthesised here, deterministically.

    s01  the dot pops three soft notes; the Bass title as the Bass cut scored it; night falls on a
         low gong; the city rises on a pizzicato descent; the storeys open up an arpeggio; a note
         per light going out; her four and his five; a tremolo rising into her room.
    s02  her theme, a celesta tune over pizzicato; the clock ticks on the beat; the kettle sings
         on the picture's own whistle curve.
    s03  the quarrel close, the strings driving in sixteenths; his low A under his look; the slap.
    s04  the Bass cut's knife: the shrieks; the mug; then her heartbeat alone (90 to 140 bpm).
    s05  braams and dissonance; the halves pressing on her heart.
    s06  sparse: her breath; her heart, 72 bpm rising to 112 (the scene's cue); four floors down,
         his door and his steps, his low A as he looks up; the chain slid home; the sash sticks,
         grinds up, bangs home; the night wind; out onto the iron.
    s07  the race as a plucked canon: his steps low, rising a semitone a landing; hers high,
         mirrored, falling; the two notes cross at the X.
    s08  sparse: his steps, his breath, the handle, the chain, the wind through the keyhole.
    s09  sparse: the door creaks, her breath catches; the fingers close (a faint breath, one
         pulse); the dial, 9, 1, 1, as the picture winds it, a relay click on each tally dot;
         it rings twice; the click.
    s10  the burst; the empty room; her high B-flat and his low A clash in a chime; sirens; her
         theme plucked one note per window; the city's looks swell; the ring; the strings resolve
         onto B-flat major.
    s11  the major rings on; the windows rise up the major scale; the stamp; the slash and the
         last chord (B-flat major seventh: the Psycho chord turned major); the dot; two
         heartbeats; silence.

Each scene's section (s01 ... s11) imports its scene module and reads its beats, sync helpers
(footfalls, paths, wind, the chain's links) and cues; no picture time is typed in here. A missing
scene module is skipped with a warning (or, with --stand-ins, played from the bible's beats); one
that does not import is played from the bible. Every cue a section has not realised is realised
from its words (and reported), so a re-run after the scenes change still covers every cue.
"""
from __future__ import annotations

import argparse
import glob
import importlib
import json
import math
import os
import re
import sys
import time
from fractions import Fraction
from functools import lru_cache

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np  # noqa: E402
from scipy import signal  # noqa: E402

from audio import dsp, sfx  # noqa: E402
from audio.dsp import SR, db2lin, n_of  # noqa: E402
from engine.timing import SceneTiming  # noqa: E402
from films.opposite.audio.mix import _gen, gen, glass, knife_ring, mono, piano, shrieks, step_bank  # noqa: E402
from films.opposite_bass import world as BW  # noqa: E402
from films.opposite_bass.audio import mix as OB  # noqa: E402

FILM = "opposite_full"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "timeline", "timeline.json")) as fh:
    TL = json.load(fh)
DUR = float(TL["duration"])
N = int(round(DUR * SR))
FPS = float(TL.get("fps", 24))
FRAME = 1.0 / FPS
SCENES = [(s["id"], float(s["start"]), float(s["duration"])) for s in TL["scenes"]]
START = {sid: a for sid, a, _ in SCENES}
LENGTH = {sid: d for sid, _, d in SCENES}

BEAT, E8, E16 = 0.5, 0.25, 0.125             # 120 bpm
BB2, SEMI = OB.BB2, OB.SEMI
note = OB.note                               # semitones over B-flat 2 -> Hz
PSYCHO = (0, 3, 7, 11)                       # Bb Db F A
MINOR = (0, 3, 7, 12)
MAJOR = (0, 4, 7, 12)
MAJ7 = (0, 4, 7, 11)                         # the Psycho chord turned major: the last chord
HER = 36                                     # B-flat 5: her note
HIS = -13                                    # A 1: his note

# scene trims (dB, every bus): the film's arc. Set by ear-by-meter (see --qa's per-scene table).
TRIM = dict(s01=0.0, s02=-2.0, s03=0.0, s04=0.0, s05=0.0, s06=0.0, s07=-3.0, s08=0.0, s09=0.0, s10=0.0, s11=0.0)

ARGS = argparse.Namespace(stand_ins=False, only=None, qa=None, without=None)
WARN = []


def warn(msg):
    WARN.append(msg)
    print("WARNING:", msg, flush=True)


# ============================================================================ the scene modules
class Stub:
    """A scene whose module is missing (--stand-ins) or broken: every beat falls back to the
    bible's (the defaults the section passes to g), its cues to BIBLE_CUES."""

    def __init__(self, sid, why):
        self.sid, self.why = sid, why


def scene(sid):
    """The scene's module; a Stub when it is broken (or missing, with --stand-ins); None when it
    is missing (the section is skipped)."""
    paths = sorted(glob.glob(os.path.join(ROOT, "scenes", f"{sid}_*.py")))
    if sid in (ARGS.without or ()):
        paths = []
    if not paths:
        if ARGS.stand_ins:
            warn(f"{sid}: no scene module (scenes/{sid}_*.py): played from the bible (--stand-ins)")
            return Stub(sid, "missing")
        warn(f"{sid}: no scene module (scenes/{sid}_*.py): section skipped")
        return None
    name = os.path.basename(paths[0])[:-3]
    try:
        return importlib.import_module(f"films.{FILM}.scenes.{name}")
    except Exception as e:  # mid-edit: play it from the bible
        warn(f"{sid}: {name} does not import ({type(e).__name__}: {e}): played from the bible")
        return Stub(sid, "broken")


FROM_BIBLE = {}          # sid -> beats a (mid-edit) module does not have yet, taken from the bible
_FAILED = set()


def _sid(S):
    return S.sid if isinstance(S, Stub) else os.path.basename(getattr(S, "__name__", "?")).split(".")[-1].split("_")[0]


def g(S, name, default):
    """A beat of scene module S (the bible's value when S is a Stub or lacks it)."""
    if isinstance(S, Stub):
        return default
    v = getattr(S, name, None)
    if v is None:
        FROM_BIBLE.setdefault(_sid(S), []).append(name)
        return default
    return v


def call(S, name, *a, default=None):
    """A sync helper of scene module S, or default when it is missing or fails."""
    fn = None if isinstance(S, Stub) else getattr(S, name, None)
    if fn is None:
        return default
    try:
        return fn(*a)
    except Exception as e:
        if (_sid(S), name) not in _FAILED:
            _FAILED.add((_sid(S), name))
            warn(f"{_sid(S)}: {name}() fails ({type(e).__name__}: {e}): using the bible's")
        return default


def cue_list(S, sid):
    if isinstance(S, Stub):
        return [dict(c) for c in BIBLE_CUES.get(sid, [])]
    if not hasattr(S, "cues"):
        warn(f"{sid}: no cues(): spotting from its beats only")
        return []
    T = SceneTiming(FILM, sid)
    err = None
    for arg in (T, T.duration):
        try:
            out = [dict(c) for c in S.cues(arg)]
            if err is not None:
                warn(f"{sid}: cues(T) raised {err}; read with cues(T.duration) instead")
            return out
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
    warn(f"{sid}: cues() fails ({err}): spotting from its beats only")
    return []


def mocap_footfalls(perf, t0, t1, thr=-6.0, rate=48.0):
    """Times a foot comes down in a mocap performance (as s02.footfalls finds them)."""
    out, prev = [], {}
    for i in range(int((t1 - t0) * rate) + 1):
        t = t0 + i / rate
        st = perf(t)[0]
        for side in ("near", "far"):
            up = st["feet"][side][1] < thr
            if prev.get(side) and not up:
                out.append(round(t, 3))
            prev[side] = up
    return out


# ============================================================================ the buses
BUSES = ("music", "hall", "efx", "amb", "vox", "feet")


class Mix:
    """The film's buses. put() takes scene time; every labelled placement is logged as an
    event (the beat it is for, and where its sound actually starts or peaks) for the sync check
    and for spotting: a cue counts as realised when an event of its scene lands within a frame."""

    def __init__(self):
        self.b = {k: np.zeros((N, 2), np.float32) for k in BUSES}
        self.key = np.zeros(N, np.float32)          # the voices that duck the music
        self.ev = []
        self.edges = []                             # (sid, t, label, start/peak, end/peak, bus)
        self.starts = []                            # film time of every placement
        self.spans = []                             # (bus, start, end, label, line) of every placement
        self.report = []                            # (sid, cue, how)
        self.sid, self.t0, self.trim, self.cues, self.covered = None, 0.0, 0.0, [], set()

    def begin(self, S, sid, t0):
        self.sid, self.t0, self.trim = sid, t0, TRIM.get(sid, 0.0)
        self.cues = cue_list(S, sid)
        self.covered = set()
        self.len = LENGTH.get(sid, 10.0)

    def put(self, bus, x, at, gain=0.0, pan=0.0, label=None, sync=None, align="onset", key=False, hall="auto"):
        x = np.asarray(x, np.float64)
        if x.ndim == 1:
            x = dsp.pan_mono(x, pan)
        elif pan:
            x = dsp.pan_stereo(x, pan)
        i = int(round((self.t0 + at) * SR))
        env = np.abs(x).max(axis=1)
        pk = float(env.max()) if len(env) else 0.0
        if pk > 0 and len(x) > n_of(0.01):
            e0, e1 = float(env[0]) / pk, float(env[-1]) / pk
            if e0 > 0.2 or e1 > 0.1:                 # cut off loud: it wants a real fade, not the 3 ms one
                self.edges.append((self.sid, self.t0 + at, label or "", e0, e1, bus))
        if len(x) > n_of(0.008):                     # no sound starts or stops on a step (a click)
            x = dsp.fade(x, 0.001, 0.003, shape="lin")
        x = (x * db2lin(gain + self.trim)).astype(np.float32)
        dsp.mix_into(self.b[bus], x, i)
        self.starts.append(self.t0 + at)
        self.spans.append((bus, self.t0 + at, self.t0 + at + len(x) / SR, label or "", sys._getframe(1).f_lineno,
                           float(np.sqrt(np.mean(np.square(x[: n_of(1.0)], dtype=np.float64)))) if len(x) else 0.0))
        env = np.abs(x).max(axis=1)
        pk = float(env.max()) if len(env) else 0.0
        if hall == "auto":
            hall = -13.0 if bus == "music" else None
        if hall is not None:
            dsp.mix_into(self.b["hall"], x * np.float32(db2lin(hall)), i)
        if key:
            dsp.mix_into(self.key, x.mean(axis=1), i)
        if label:
            if align == "peak" and pk > 0:
                sm = np.convolve(env, np.ones(n_of(0.01)) / n_of(0.01), "same")
                meas = at + int(np.argmax(sm)) / SR
            elif align == "onset" and pk > 0:
                i20, i90 = int(np.argmax(env >= 0.2 * pk)), int(np.argmax(env >= 0.9 * pk))
                # a hit is checked at its onset; a sound that swells in (strings, a creak, a
                # rustle) is placed at its start, and its onset is no sync point
                meas = at + i20 / SR if (i90 - i20) / SR < 0.05 else None
            else:
                meas = None
            self.ev.append(dict(sid=self.sid, t=self.t0 + (at if sync is None else sync), label=label,
                                meas=None if meas is None else self.t0 + meas, bus=bus))

    def mark(self, t, label):
        """An event with no sound of its own (a cue realised by a phrase, a bed, a silence)."""
        self.ev.append(dict(sid=self.sid, t=self.t0 + t, label=label, meas=None, bus=None))

    def cover(self, *words):
        """Cues of this scene whose text has any of words are realised (elsewhere in time)."""
        for i, c in enumerate(self.cues):
            if any(w in c["sfx"].lower() for w in words):
                self.covered.add(i)

    def end(self):
        """Spotting: realise every cue of this scene no event answered."""
        if FROM_BIBLE.get(self.sid):
            warn(f"{self.sid}: not in the module yet, taken from the bible: {', '.join(dict.fromkeys(FROM_BIBLE[self.sid]))}")
        mine = [e["t"] - self.t0 for e in self.ev if e["sid"] == self.sid]
        for i, c in enumerate(self.cues):
            hit = i in self.covered or any(abs(t - c["t"]) <= FRAME + 1e-6 for t in mine)
            if hit:
                self.report.append((self.sid, c, "section"))
                continue
            how = realize(self, c)
            self.report.append((self.sid, c, how))
            if how.startswith("auto"):
                print(f"  {self.sid} {c['t']:6.3f}  auto-realised: {c['sfx']!r} -> {how}")
            else:
                warn(f"{self.sid} {c['t']:.3f}: cue {c['sfx']!r} not realised ({how})")


# ============================================================================ instruments
def norm(x, peak=1.0):
    x = np.asarray(x, np.float64)
    p = float(np.max(np.abs(x))) if x.size else 0.0
    return x * (peak / p) if p > 1e-12 else x


def tax(n):
    return np.arange(n) / SR


def rng(*keys):
    return dsp.rng_for("opposite-full", *keys)


def rev(x, wet=-10.0, seed=0, kind="hall"):
    x = mono(x)
    if len(x) > n_of(0.008):  # a dry sound cut short inside the reverb would click, and echo the click
        x = dsp.fade(x, 0.001, 0.003, shape="lin")
    return dsp.reverb(x, kind, wet_db=wet, seed=seed)


def pitch(x, semis):
    """Resample by 2**(semis/12): pitch and speed together."""
    fr = Fraction(2.0 ** (-semis / 12.0)).limit_denominator(64)
    return signal.resample_poly(np.asarray(x, np.float64), fr.numerator, fr.denominator, axis=0)


@lru_cache(maxsize=None)
def _chord1(semis, dur, seed, octave, stacc, spread):
    return OB.chord(list(semis), dur, 1.0, seed, octave, stacc, spread)


def chord(semis, dur, vel=0.7, seed=0, octave=0, stacc=True, spread=(0, 12)):
    """The Bass cut's string chord (it is linear in vel: rendered once at 1, cached)."""
    return vel * _chord1(tuple(int(s) for s in semis), round(float(dur), 4), int(seed), int(octave), bool(stacc),
                         tuple(int(s) for s in spread))


def tremolo(semis, dur, vel=0.6, seed=0, octave=2, rate=13.0):
    x = chord(semis, dur, vel, seed, octave, stacc=False, spread=(0,))
    return x * (0.55 + 0.45 * np.abs(np.sin(np.pi * rate * tax(len(x)))))


def ostinato(m, t0, t1, step=E8, semis=PSYCHO, octave=0, vel=(0.4, 0.9), accent=(0, 3), lift=None, seed=0,
             gain=-14.0, spread=(0, 12), pan=0.0):
    """The Bass cut's ostinato: staccato chords t0..t1 (scene time), crescendo vel[0]->vel[1],
    accents on the given steps of each bar; lift(t) -> semitones; semis may be a function of t."""
    i, t = 0, t0
    per_bar = int(round(2.0 / step))
    while t < t1 - 1e-6:
        u = (t - t0) / max(t1 - t0, 1e-6)
        v = vel[0] + (vel[1] - vel[0]) * u
        if i % per_bar in accent:
            v *= 1.35
        sh = lift(t) if lift else 0
        ch = semis(t) if callable(semis) else semis
        m.put("music", chord([s + sh for s in ch], step * 0.6, v, seed + i % 4, octave, spread=spread), t, gain, pan=pan)
        t += step
        i += 1


@lru_cache(maxsize=None)
def _pizz1(f0, seed):
    return OB.pizz(f0, 1.0, seed)


def pizz(f0, vel=0.8, seed=0):
    return vel * _pizz1(round(float(f0), 3), int(seed) % 8)


@lru_cache(maxsize=None)
def _harp1(f0, seed):
    r = rng("harp", seed, int(f0))
    t60 = float(np.clip(2.2 * (220.0 / f0) ** 0.45, 0.5, 3.0))
    exc = dsp.sos(r.uniform(-1.0, 1.0, int(SR / f0) + 2), "lowpass", min(7000.0, 9.0 * f0), 2)
    y = dsp.karplus_strong(f0, min(3.5, t60 * 1.2), t60=t60, brightness=0.35, excitation=exc, pluck_pos=0.17)
    t = tax(len(y))
    y = norm(y) + 0.25 * np.sin(2 * np.pi * f0 * t) * np.power(10.0, -3.0 * t / (t60 * 1.3))
    return norm(dsp.fade(y, 0.0005, 0.08))


def harp(f0, vel=0.8, seed=0):
    return vel * _harp1(round(float(f0), 3), int(seed) % 6)


def pluck(f0, vel=0.8, seed=0, damp=0.09):
    """A harp string stopped by the hand right after it is plucked: a short, dry note."""
    x = harp(f0, vel, seed)[: n_of(6.0 * damp)]
    return dsp.fade(x * np.exp(-tax(len(x)) / damp), 0.0, damp)


@lru_cache(maxsize=None)
def _celesta1(f0, seed):
    r = rng("cel", seed, int(f0))
    t60 = float(np.clip(2.4 * (523.0 / f0) ** 0.6, 0.6, 4.0))
    n = n_of(min(4.0, t60 * 1.1))
    t = tax(n)
    y = np.zeros(n)
    for ratio, amp, k in ((1.0, 1.0, 1.0), (2.0, 0.06, 0.45), (3.0, 0.03, 0.3), (4.0, 0.16, 0.16),
                          (2.76, 0.04, 0.1), (5.4, 0.03, 0.06)):
        if f0 * ratio < 16000.0:
            y += amp * np.sin(2 * np.pi * f0 * ratio * t + r.uniform(0, 2 * np.pi)) * np.power(10.0, -3.0 * t / (t60 * k))
    a = n_of(0.0015)
    y[:a] *= np.linspace(0.0, 1.0, a)
    knock = dsp.bandpass(r.standard_normal(n_of(0.02)), 800.0, 5000.0, 2) * np.exp(-tax(n_of(0.02)) / 0.004)
    y[:len(knock)] += 0.05 * knock
    return norm(dsp.fade(y, 0.0, 0.1))


def celesta(f0, vel=0.7, seed=0):
    return vel * _celesta1(round(float(f0), 3), int(seed) % 4)


@lru_cache(maxsize=None)
def bell(f0, seed=0, tail=3.0):
    """A small soft bell (the moon)."""
    r = rng("bell", seed, int(f0))
    n = n_of(tail)
    t = tax(n)
    y = np.zeros(n)
    for ratio, amp, k in ((0.5, 0.3, 1.0), (1.0, 1.0, 0.85), (1.2, 0.4, 0.6), (1.5, 0.22, 0.5), (2.0, 0.45, 0.45),
                          (2.52, 0.16, 0.3), (3.0, 0.15, 0.25), (4.07, 0.08, 0.18)):
        for det in (-0.4, 0.4):
            y += 0.5 * amp * np.sin(2 * np.pi * (f0 * ratio + det) * t + r.uniform(0, 2 * np.pi)) * \
                np.power(10.0, -3.0 * t / (tail * k))
    a = n_of(0.002)
    y[:a] *= np.linspace(0.0, 1.0, a)
    return norm(dsp.fade(y, 0.0, 0.4))


@lru_cache(maxsize=None)
def gong(f0, seed=0, dur=6.0):
    """A low tam-tam: a mallet thud, partials blooming a moment after the stroke, a shimmer."""
    r = rng("gong", seed)
    n = n_of(dur)
    t = tax(n)
    y = np.zeros(n)
    for ratio, amp, t60, bloom in ((1.0, 1.0, 5.5, 0.01), (1.48, 0.55, 4.2, 0.05), (2.03, 0.5, 3.6, 0.08),
                                   (2.52, 0.4, 3.0, 0.12), (3.07, 0.35, 2.6, 0.18), (3.62, 0.3, 2.2, 0.22),
                                   (4.29, 0.25, 1.9, 0.28), (5.11, 0.2, 1.6, 0.32), (6.05, 0.16, 1.3, 0.36),
                                   (7.2, 0.12, 1.1, 0.4), (8.6, 0.08, 0.9, 0.45)):
        f = f0 * ratio * (1.0 + 0.004 * np.exp(-t / 0.3))
        ph = 2 * np.pi * np.cumsum(f) / SR + r.uniform(0, 2 * np.pi)
        y += amp * np.sin(ph) * (1.0 - np.exp(-t / bloom)) * np.power(10.0, -3.0 * t / t60)
    y += 0.04 * dsp.bandpass(r.standard_normal(n), 1200.0, 5000.0, 2) * (1.0 - np.exp(-t / 0.25)) * \
        np.power(10.0, -3.0 * t / 2.0)
    m = sfx._thump(n_of(0.5), 2.0 * f0, f0, 0.03, 0.4)
    y[:len(m)] += 0.6 * m
    return norm(dsp.fade(y, 0.0, 0.5))


@lru_cache(maxsize=None)
def chime(f0, seed=0, tail=4.0):
    """A struck chime (a free bar's partials, each a slow beating pair)."""
    r = rng("chime", seed, int(f0))
    n = n_of(tail)
    t = tax(n)
    y = np.zeros(n)
    for ratio, amp, k in ((1.0, 1.0, 1.0), (2.756, 0.45, 0.45), (5.404, 0.22, 0.28), (8.933, 0.1, 0.16),
                          (13.34, 0.04, 0.1)):
        for det in (-0.3, 0.3):
            f = f0 * ratio + det
            if f < 18000.0:
                y += 0.5 * amp * np.sin(2 * np.pi * f * t + r.uniform(0, 2 * np.pi)) * np.power(10.0, -3.0 * t / (tail * k))
    c = sfx._click(r, 3000.0, 0.003)
    y[:len(c)] += 0.25 * norm(c)
    return norm(dsp.fade(y, 0.0, 0.5))


def harmonic(f0, dur, vel=0.7, seed=0, attack=0.12, release=0.5, vib=0.002, sfz=False, bend=None):
    """A string harmonic: almost a sine, a breath of bow; bend(t) -> semitones (a swirl)."""
    r = rng("harm", seed, int(f0))
    n = n_of(dur + release)
    t = tax(n)
    f = f0 * (1.0 + vib * np.sin(2 * np.pi * 5.2 * t + r.uniform(0, 2 * np.pi)) * np.clip((t - 0.2) / 0.3, 0, 1))
    if bend is not None:
        f = f * 2.0 ** (bend(t) / 12.0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.08 * np.sin(2 * ph) + 0.03 * np.sin(3 * ph)
    y += 0.05 * norm(dsp.bandpass(r.standard_normal(n), f0 * 0.8, min(f0 * 3.0, 16000.0), 2))
    env = dsp.env_bp([(0.0, 0.0), (attack, 1.0), (dur, 0.9), (dur + release, 0.0)], n)
    if sfz:
        env = env * (1.0 + 1.5 * np.exp(-t / 0.08))
    return vel * norm(y * env)


def bowed_line(pts, dur, vel=0.7, seed=0, octaves=(0,), attack=0.08, release=0.35, vib=0.004, bright=5500.0,
               env=None):
    """A sustained section note following pts [(t, semitones over Bb2)] (glides between them),
    doubled at the given octaves. env: optional [(t, gain)] over the note."""
    r = rng("line", seed, len(pts))
    n = n_of(dur + release)
    t = tax(n)
    semis = np.interp(t, [p[0] for p in pts], [float(p[1]) for p in pts])
    f = BB2 * 2.0 ** (semis / 12.0)
    f = f * (1.0 + vib * np.sin(2 * np.pi * 5.4 * t + r.uniform(0, 2 * np.pi)) * np.clip((t - 0.15) / 0.3, 0, 1))
    x = np.zeros(n)
    for j, o in enumerate(octaves):
        for d in (1.0, 1.0035, 0.9968, 1.0071):
            x += (1.0 if j == 0 else 0.55) * dsp.saw(f * d * 2.0 ** o, n, phase0=r.uniform())
    lo = max(float(np.min(f)) * 0.9 * 2.0 ** min(octaves), 28.0)
    x = dsp.bandpass(x, lo, bright, 2)
    x = dsp.biquad(dsp.biquad(x, "peak", 1100.0, 1.2, 4.0), "peak", 2700.0, 1.5, 3.0)
    x += 0.04 * dsp.bandpass(r.standard_normal(n), 2200.0, 7000.0, 2) * np.max(np.abs(x))
    e = dsp.env_bp([(0.0, 0.0), (attack, 1.0), (dur, 0.92), (dur + release, 0.0)], n)
    if env is not None:
        e = e * dsp.env_bp(env, n)
    return vel * norm(x * e)


def strings(semis, dur, vel=0.7, seed=0, octaves=(0, 1), attack=0.15, release=0.6, env=None, bright=5000.0):
    """A held section chord (one bowed line per note)."""
    out = None
    for i, s in enumerate(semis):
        y = bowed_line([(0.0, s)], dur, 1.0, seed + 11 * i, octaves, attack, release, bright=bright, env=env)
        out = y if out is None else out + y
    return vel * norm(out)


@lru_cache(maxsize=None)
def braam(seed=0):
    """The catalog's braam (a D minor cluster) taken down a major third: B-flat minor."""
    return pitch(fx_("braam", seed=seed), -4).astype(np.float32)


@lru_cache(maxsize=None)
def stinger(seed=0, semis=-4):
    """The catalog's stinger (D Eb A) down a major third: Bb B F."""
    return pitch(fx_("stinger", seed=seed), semis).astype(np.float32)


def fx_(name, dur=None, seed=0, **p):
    return sfx.render(name, dur=dur, params=p, seed=seed)


fx = fx_


def bed(name, dur, seed=0, fin=0.05, fout=0.05):
    """A sustained catalog sound (room tone, the city, wind) with short fades: beds start and
    end at cuts, and an edge with no fade is a click."""
    return dsp.fade(fx(name, dur=dur, seed=seed), fin, fout)


def cut(x, dur, fout=0.1):
    """The first dur seconds of x, faded out over its last fout."""
    return dsp.fade(np.asarray(x, np.float64)[: n_of(dur)], 0.0, fout)


def onset_at(x, frac=0.2):
    """Seconds into x where it first reaches frac of its peak."""
    e = np.abs(np.asarray(x, np.float64))
    e = e.max(axis=1) if e.ndim == 2 else e
    return int(np.argmax(e >= frac * e.max())) / SR if e.size and e.max() > 0 else 0.0


def peak_at(x, win=0.01):
    """Seconds into x of its loudest 10 ms."""
    e = np.abs(np.asarray(x, np.float64))
    e = e.max(axis=1) if e.ndim == 2 else e
    if not e.size:
        return 0.0
    w = max(1, n_of(win))
    return int(np.argmax(np.convolve(e, np.ones(w) / w, "same"))) / SR


def stab(seed=0, octave=0, semis=PSYCHO):
    """A string stab: the chord, hard, with its hall."""
    return rev(chord(semis, 0.45, 1.0, 40 + seed, octave, spread=(0, 12, -12)), -8.0, seed)


@lru_cache(maxsize=None)
def heart(dub=0.26, seed=0, dub_amp=0.62):
    """One heartbeat as the catalog's heartbeat makes it: lub, and dub `dub` s later."""
    r = rng("heart", seed)
    n = n_of(dub + 0.45)
    out = np.zeros(n)
    lub = sfx._thump(n_of(0.3), 70.0, 46.0, 0.03, 0.16)
    lub[:n_of(0.08)] += 0.4 * sfx._burst(n_of(0.08), r, hi=140.0, t60=0.05, attack=0.004)
    dsp.mix_into(out, lub, 0)
    dsp.mix_into(out, sfx._thump(n_of(0.25), 88.0, 58.0, 0.02, 0.11) * dub_amp, n_of(dub))
    out = dsp.sos(out, "lowpass", 190.0, 2)
    out += 0.18 * dsp.sos(dsp.saturate(out * 3.0, 2.0), "bandpass", (90.0, 400.0), 2)
    return norm(out)


@lru_cache(maxsize=None)
def soft_hit(f0, seed=0):
    """The red dot popping: a felt mallet on a soft drum and a felt note, a small round pop."""
    r = rng("dot", seed)
    n = n_of(1.8)
    y = 0.8 * norm(sfx._felt_piano_note(f0, n, vel=0.5, rng=r))
    th = sfx._thump(n_of(0.3), 2.5 * f0, f0, 0.02, 0.18)
    y[:len(th)] += 0.7 * th
    pop = sfx._drop(r, 520.0 + 30.0 * seed, 0.006, chirp=0.8)
    y[:len(pop)] += 0.25 * norm(pop)
    return norm(dsp.fade(y, 0.0, 0.3))


# ============================================================================ voices and recordings
@lru_cache(maxsize=None)
def bank(name, thr=-18.0, length=0.26):
    """Single footfalls cut from a recording (each starts 15 ms before its onset)."""
    return tuple(step_bank(name, thr_db=thr, length=length))


STEP_PRE = 0.015

# the quarrel recording's shouts, by voice (s): his lower (f0 140-240 Hz), hers higher
Q_UNITS = {"man": ((3.56, 3.80), (3.86, 4.16), (1.19, 1.40)),
           "vic": ((1.58, 1.76), (1.82, 2.05), (2.08, 2.27), (4.17, 4.47), (5.19, 5.60))}


def shout(who, k):
    """The k-th shout of a voice: its units in turn, each round a little higher or lower."""
    units = Q_UNITS[who]
    a, b = units[k % len(units)]
    x = gen("quarrel", a - 0.012, b + 0.05, fade=0.012)
    sh = (0.0, -1.0, 1.0, -2.0, 0.5)[(k // len(units)) % 5]
    return pitch(x, sh) if sh else x


def near(x, seed=2):
    """In the room with them: a little low cut, a little of the room."""
    return dsp.reverb(dsp.sos(mono(x), "highpass", 120.0, 2), "small_room", wet_db=-14.0, seed=seed)


# ============================================================================ foley
def tick(k=0):
    """Her wall clock: tick, tock."""
    return fx("clock_tick", seed=k % 2, tock=bool(k % 2))


@lru_cache(maxsize=None)
def switch(seed=0):
    r = rng("switch", seed)
    y = sfx._hit(r, [2300.0, 3600.0, 5200.0], [0.025, 0.02, 0.012], click=1.0, n=n_of(0.08))
    th = sfx._thump(n_of(0.06), 320.0, 180.0, 0.004, 0.02)
    y[:len(th)] += 0.5 * th
    return norm(y)


@lru_cache(maxsize=None)
def glass_tick(seed=0):
    r = rng("gtick", seed)
    return norm(sfx._hit(r, [3100.0, 4650.0, 7900.0], [0.12, 0.08, 0.05], click=0.5, n=n_of(0.2)))


@lru_cache(maxsize=None)
def clink(seed=0, f=2600.0):
    r = rng("clink", seed)
    return norm(sfx._hit(r, [f, f * 1.52, f * 2.43], [0.08, 0.06, 0.04], click=0.5))


@lru_cache(maxsize=None)
def clunk(seed=0):
    """A kettle set down on an iron burner."""
    r = rng("clunk", seed)
    y = sfx._hit(r, [210.0, 470.0, 820.0, 1330.0, 2100.0], [0.2, 0.15, 0.1, 0.08, 0.05], spread=0.03, click=0.4)
    th = sfx._thump(n_of(0.15), 140.0, 80.0, 0.01, 0.07)
    y[:len(th)] += 0.7 * th
    return norm(y)


def kettle(amp, seed=0):
    """Her kettle's whistle (two pipes, F6 and A6) on the picture's whistle curve (per sample)."""
    r = rng("kettle", seed)
    a = np.clip(np.asarray(amp, np.float64), 0.0, 1.5)
    n = len(a)
    f1 = 1396.9 * (0.94 + 0.06 * a) * (1.0 + 0.004 * dsp.smooth_noise(n, 3.0, r))
    f2 = 1760.0 * (0.94 + 0.06 * a) * (1.0 + 0.003 * dsp.smooth_noise(n, 2.0, r))
    tone = np.sin(2 * np.pi * np.cumsum(f1) / SR) + 0.6 * np.sin(2 * np.pi * np.cumsum(f2) / SR)
    breath = dsp.tv_bandpass(r.standard_normal(n), f1, q=6.0, block=128)
    hiss = dsp.bandpass(r.standard_normal(n), 2500.0, 9000.0, 2)
    y = (tone + 0.5 * norm(breath)) * a ** 1.6 + 0.12 * norm(hiss) * np.clip(a, 0, 1) ** 0.5
    return norm(dsp.fade(y, 0.02, 0.05))


def gas_bed(dur, seed=0):
    r = rng("gas", seed)
    n = n_of(dur)
    x = dsp.bandpass(r.standard_normal(n), 180.0, 1800.0, 2) * (1.0 + 0.3 * dsp.smooth_noise(n, 9.0, r))
    x += 0.3 * dsp.bandpass(r.standard_normal(n), 2500.0, 7000.0, 2)
    return norm(dsp.fade(x, 0.3, 0.06))


@lru_cache(maxsize=None)
def gas_off(seed=0):
    """The gas knob: a click, the flame's last breath."""
    r = rng("gasoff", seed)
    y = np.zeros(n_of(0.3))
    c = sfx._hit(r, [1900.0, 3300.0, 4800.0], [0.02, 0.015, 0.01], click=1.0, n=n_of(0.05))
    y[:len(c)] += c
    puff = dsp.bandpass(r.standard_normal(n_of(0.15)), 150.0, 900.0, 2) * np.exp(-tax(n_of(0.15)) / 0.04)
    y[n_of(0.01):n_of(0.01) + len(puff)] += 0.4 * norm(puff)
    return norm(y)


def pour(dur, seed=0):
    """Hot water into the mug: the stream, the mug's note rising as it fills, bubbles, drips."""
    r = rng("pour", seed)
    n = n_of(dur + 0.5)
    t = tax(n)
    u = np.clip(t / dur, 0.0, 1.0)
    on = np.clip(t / 0.04, 0, 1) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.05))
    stream = dsp.bandpass(r.standard_normal(n), 500.0, 6000.0, 2) * (0.6 + 0.4 * np.abs(dsp.smooth_noise(n, 25.0, r)))
    fres = 380.0 * 3.4 ** u
    body = dsp.tv_bandpass(r.standard_normal(n), fres, q=7.0, block=64)
    y = (0.5 * norm(stream) + norm(body)) * on
    for tt in dsp.poisson_times(28.0, dur, r):
        d = sfx._drop(r, float(np.interp(tt, t, fres)) * r.uniform(1.4, 2.4), r.uniform(0.004, 0.01))
        dsp.mix_into(y, 0.3 * norm(d), n_of(tt))
    for j, dt in enumerate((0.12, 0.23, 0.37)):
        d = sfx._drop(r, r.uniform(900.0, 1300.0), 0.012, chirp=0.9)
        dsp.mix_into(y, (0.35 - 0.08 * j) * norm(d), n_of(dur + dt))
    return norm(y)


@lru_cache(maxsize=None)
def slap(seed=0):
    r = rng("slap", seed)
    y = np.zeros(n_of(0.3))
    y[:n_of(0.05)] += sfx._burst(n_of(0.05), r, 900.0, 9000.0, t60=0.016, attack=0.0002)
    y[:n_of(0.09)] += 0.6 * sfx._burst(n_of(0.09), r, 150.0, 1400.0, t60=0.035, attack=0.0005)
    y[:n_of(0.15)] += 0.35 * sfx._thump(n_of(0.15), 190.0, 95.0, 0.008, 0.05)
    return norm(dsp.reverb(y, "small_room", wet_db=-12.0, seed=seed))


@lru_cache(maxsize=None)
def squeak(dur=0.4, seed=0):
    """A felt marker drawing a ring: a rubbery squeak that follows the stroke's speed."""
    r = rng("squeak", seed)
    n = n_of(dur)
    t = tax(n)
    speed = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.5
    rate = 650.0 + 800.0 * speed + 90.0 * np.sin(2 * np.pi * 11.0 * t)
    y = dsp.friction(n, rate, r, jitter=0.06, body=[(1850.0, 8, 1.0), (3050.0, 10, 0.5), (5200.0, 12, 0.2)])
    y = norm(y) + 0.25 * np.sin(2 * np.pi * np.cumsum(2.0 * rate) / SR) * speed
    return norm(dsp.fade(y * speed, 0.008, 0.03))


@lru_cache(maxsize=None)
def zip_(dur=0.3, seed=0):
    """A look zipping across: a fast rising swish, left to right."""
    r = rng("zip", seed)
    n = n_of(dur + 0.05)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    fc = 600.0 * 10.0 ** u
    x = norm(dsp.tv_bandpass(r.standard_normal(n), fc, q=3.0, block=32)) + 0.35 * np.sin(2 * np.pi * np.cumsum(0.5 * fc) / SR)
    x *= u ** 1.5 * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.012))
    th = (np.clip(-0.8 + 1.6 * u, -1, 1) + 1) * np.pi / 4
    return norm(np.stack([x * np.cos(th), x * np.sin(th)], axis=1))


def rush(dur, seed=0, peak=0.9):
    """Flying along a look: air rising to a peak at peak*dur, then gone."""
    r = rng("rush", seed)
    n = n_of(dur + 0.2)
    t = tax(n)
    u = np.clip(t / dur, 0, 1.2)
    up = np.clip(u / peak, 0, 1)
    fc = 300.0 + 2400.0 * up ** 1.5
    x = dsp.tv_bandpass(dsp.pink(n, r), fc, q=0.9, block=64)
    x += 0.5 * dsp.sos(dsp.tv_bandpass(dsp.pink(n, r), 0.4 * fc, q=0.7, block=64), "lowpass", 800.0, 2)
    env = np.where(u < peak, up ** 2.2, np.exp(-(t - peak * dur) / 0.05))
    return norm(dsp.fade(dsp.decorrelate(x * env, r, amount=0.5), 0.0, 0.05))


@lru_cache(maxsize=None)
def rustle(dur=0.35, seed=0, lo=500.0, hi=5000.0):
    r = rng("rustle", seed)
    n = n_of(dur)
    t = tax(n)
    x = dsp.bandpass(r.standard_normal(n), lo, hi, 2) * (0.5 + 0.5 * np.abs(dsp.smooth_noise(n, 30.0, r)))
    x += 0.4 * dsp.sos(dsp.crackle(n, 300.0, r), "highpass", 2000.0, 2)
    return norm(x * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5)


@lru_cache(maxsize=None)
def creak(dur=0.35, seed=0, iron=False):
    """Wood in a fist (or iron taking weight): stick-slip through the material's resonances."""
    r = rng("creak", seed, iron)
    n = n_of(dur)
    sw = np.sin(np.pi * np.clip(tax(n) / dur, 0, 1)) ** 0.8
    if iron:
        body, rate = [(310.0, 9, 1.0), (520.0, 11, 0.8), (870.0, 13, 0.5), (1450.0, 15, 0.3)], 25.0 + 45.0 * sw
    else:
        body, rate = [(650.0, 7, 1.0), (1400.0, 9, 0.6), (2600.0, 12, 0.3)], 70.0 + 120.0 * sw
    return norm(dsp.friction(n, rate, r, jitter=0.25, body=body) * sw)


@lru_cache(maxsize=None)
def scrape(dur=0.22, seed=0):
    """A knife lifted off a wooden counter: steel dragging on wood."""
    r = rng("scrape", seed)
    n = n_of(dur)
    sw = np.sin(np.pi * np.clip(tax(n) / dur, 0, 1)) ** 0.6
    y = dsp.friction(n, 900.0 + 600.0 * sw, r, jitter=0.2, body=[(2900.0, 14, 1.0), (4300.0, 16, 0.7), (6100.0, 18, 0.4)])
    y = norm(y) + 0.3 * norm(dsp.bandpass(r.standard_normal(n), 2500.0, 9000.0, 2))
    return norm(y * sw)


@lru_cache(maxsize=None)
def paper_snap(seed=0):
    r = rng("psnap", seed)
    y = np.zeros(n_of(0.2))
    y[:n_of(0.03)] += sfx._burst(n_of(0.03), r, 1200.0, 9000.0, t60=0.01, attack=0.0002)
    t = mono(fx("paper_tear", seed=seed))[:n_of(0.12)]
    y[:len(t)] += 0.5 * norm(t) * np.exp(-tax(len(t)) / 0.04)
    return norm(y)


@lru_cache(maxsize=None)
def iron_step(seed=0):
    r = rng("iron", seed)
    k = r.uniform(0.9, 1.12)
    y = sfx._hit(r, np.array([340.0, 560.0, 830.0, 1210.0, 1740.0, 2480.0]) * k, [0.22, 0.18, 0.14, 0.11, 0.09, 0.07],
                 spread=0.03, click=0.7)
    th = sfx._thump(n_of(0.1), 150.0, 85.0, 0.008, 0.05)
    y[:len(th)] += 0.8 * th
    return norm(y)


@lru_cache(maxsize=None)
def rung(seed=0):
    r = rng("rung", seed)
    return norm(sfx._hit(r, np.array([820.0, 1390.0, 2210.0, 3180.0]) * r.uniform(0.95, 1.08), [0.35, 0.25, 0.18, 0.12],
                         spread=0.02, click=0.6))


@lru_cache(maxsize=None)
def door_thud(seed=0, size=1.0):
    r = rng("dthud", seed)
    y = np.zeros(n_of(0.6))
    y[:n_of(0.35)] += sfx._thump(n_of(0.35), 130.0, 62.0, 0.015, 0.16 + 0.1 * size)
    y[:n_of(0.08)] += 0.8 * sfx._burst(n_of(0.08), r, 60.0, 1300.0, t60=0.04, attack=0.0006)
    knock = sfx._hit(r, [480.0, 760.0, 1180.0, 1700.0], [0.06, 0.05, 0.04, 0.03], click=0.6)
    y[:len(knock)] += 0.5 * knock
    return norm(dsp.reverb(y, "small_room", wet_db=-14.0, seed=seed))


@lru_cache(maxsize=None)
def chain_taut(seed=0, hard=1.0):
    """A door chain snapping taut: its links rattle, the slide clacks, the door jolts."""
    r = rng("chain", seed)
    y = np.zeros(n_of(0.45))
    for _ in range(int(5 + 5 * hard)):
        f = r.uniform(2200.0, 5200.0)
        h = sfx._hit(r, [f, f * 1.43, f * 2.2], [0.05, 0.04, 0.025], click=0.5, n=n_of(0.08))
        dsp.mix_into(y, h, n_of(abs(r.normal(0.0, 0.012))), r.uniform(0.2, 0.6))
    dsp.mix_into(y, sfx._hit(r, [1250.0, 2050.0, 3300.0, 5000.0], [0.09, 0.07, 0.05, 0.03], click=1.0), 0)
    dsp.mix_into(y, sfx._thump(n_of(0.2), 120.0, 70.0, 0.012, 0.08 + 0.05 * hard), 0, 0.6 * hard)
    return norm(dsp.reverb(y, "small_room", wet_db=-16.0, seed=seed))


@lru_cache(maxsize=None)
def chain_snap(seed=0):
    """The chain torn out of the jamb: a bright snap and the links let go."""
    r = rng("csnap", seed)
    y = np.zeros(n_of(0.5))
    dsp.mix_into(y, sfx._hit(r, [1900.0, 3100.0, 4700.0, 6900.0], [0.25, 0.18, 0.12, 0.08], spread=0.02, click=1.0), 0)
    for _ in range(9):
        f = r.uniform(2400.0, 5600.0)
        h = sfx._hit(r, [f, f * 1.47], [0.05, 0.03], click=0.4, n=n_of(0.07))
        dsp.mix_into(y, h, n_of(0.005 + abs(r.normal(0.0, 0.035))), r.uniform(0.15, 0.5))
    return norm(y)


@lru_cache(maxsize=None)
def link_tink(seed=0):
    """One link of chain landing on a wooden floor."""
    r = rng("link", seed)
    f = r.uniform(2600.0, 4800.0)
    y = sfx._hit(r, [f, f * 1.47, f * 2.31, f * 3.2], [0.06, 0.045, 0.03, 0.02], spread=0.02, click=0.8, n=n_of(0.12))
    th = sfx._thump(n_of(0.05), 420.0, 260.0, 0.005, 0.02)
    y[:len(th)] += 0.3 * th
    return norm(y)


@lru_cache(maxsize=None)
def skitter(dur=0.3, seed=0):
    r = rng("skitter", seed)
    n = n_of(dur)
    y = dsp.sos(dsp.crackle(n, 220.0, r), "highpass", 2500.0, 2) * np.exp(-tax(n) / (dur / 3.0))
    return norm(y)


@lru_cache(maxsize=None)
def splinter(seed=0):
    r = rng("splinter", seed)
    n = n_of(0.5)
    y = dsp.bandpass(dsp.crackle(n, 900.0, r), 300.0, 6000.0, 2) * np.exp(-tax(n) / 0.08)
    y[:n_of(0.06)] += 0.8 * norm(sfx._burst(n_of(0.06), r, 200.0, 5000.0, t60=0.03, attack=0.0003)) * np.max(np.abs(y))
    return norm(y)


@lru_cache(maxsize=None)
def bead(seed=0):
    """Her lamp's pull-cord bead touching the glass."""
    r = rng("bead", seed)
    return norm(sfx._hit(r, [3300.0, 5200.0, 7600.0], [0.02, 0.014, 0.01], click=0.7, n=n_of(0.05)))


@lru_cache(maxsize=None)
def cord_rattle(seed=0):
    """A phone's coiled cord, the handset lowered."""
    r = rng("cord", seed)
    y = np.zeros(n_of(0.5))
    for _ in range(10):
        f = r.uniform(1800.0, 4200.0)
        h = sfx._hit(r, [f, f * 1.7], [0.02, 0.015], click=0.6, n=n_of(0.03))
        dsp.mix_into(y, h, n_of(0.02 + abs(r.normal(0.12, 0.08))), r.uniform(0.2, 0.7))
    return norm(y)


@lru_cache(maxsize=None)
def receiver(seed=0):
    """A handset taken off (or put back on) its cradle: a plastic clack, the hook's click."""
    r = rng("recv", seed)
    y = np.zeros(n_of(0.3))
    dsp.mix_into(y, sfx._hit(r, [900.0, 1700.0, 2900.0], [0.04, 0.03, 0.02], click=0.8), 0)
    dsp.mix_into(y, sfx._hit(r, [2500.0, 4100.0], [0.015, 0.01], click=1.0, n=n_of(0.03)), n_of(0.06), 0.6)
    return norm(y)


def dial_wind(digit):
    """How long her finger takes to turn a digit round to the stop."""
    return 0.12 + 0.05 * (digit if digit else 10)


def dial(digit, seed=0):
    """A rotary dial wound round to the stop and let go: the ratchet under her finger, the
    stop, then one relay click per unit (ten a second) as it spins back. The sound starts as
    her finger starts to turn; she lets go at dial_wind(digit)."""
    r = rng("dial", seed, digit)
    units = digit if digit else 10
    wind = dial_wind(digit)
    n = n_of(wind + 0.06 + 0.1 * units + 0.3)
    y = np.zeros(n)
    tt = 0.02
    while tt < wind:
        dsp.mix_into(y, sfx._hit(r, [3800.0, 5600.0], [0.006, 0.004], click=0.6, n=n_of(0.012)), n_of(tt), 0.1)
        tt += 0.024
    dsp.mix_into(y, sfx._hit(r, [1300.0, 2300.0, 3500.0], [0.03, 0.02, 0.015], click=1.0, n=n_of(0.06)), n_of(wind), 0.5)
    pulses = [wind + 0.06 + 0.1 * j for j in range(units)]
    for tp in pulses:
        dsp.mix_into(y, sfx._hit(r, [1700.0, 2900.0, 4400.0], [0.02, 0.015, 0.01], click=1.0, n=n_of(0.04)), n_of(tp), 0.8)
    a = n_of(wind)
    whirr = dsp.bandpass(r.standard_normal(n - a), 600.0, 2400.0, 2) * 0.06
    y[a:] += whirr * np.clip((pulses[-1] + 0.06 - tax(n - a) - wind) / 0.03, 0, 1)
    return norm(dsp.fade(y, 0.002, 0.05))


def dial_turn(digit, t_in, t0, t1, t_rel, pulses, rate=300.0, seed=0):
    """One digit dialled as the picture times it (scene s; the sound starts at t_in): her
    fingertip into the hole, the ratchet as she winds it round (t0 .. t1), the finger stop, and
    after she lets go (t_rel) the governor's whirr and one relay click per pulse (at `pulses`,
    where the picture's tally lands its dots) until the wheel is home."""
    r = rng("dturn", seed, digit)
    units = digit if digit else 10
    home = t_rel + 30.0 * (units + 1) / rate
    n = n_of(home - t_in + 0.3)
    y = np.zeros(n)

    def at(t):
        return n_of(max(t - t_in, 0.0))
    dsp.mix_into(y, sfx._hit(r, [2100.0, 3300.0], [0.01, 0.008], click=0.5, n=n_of(0.02)), at(t_in), 0.12)
    tt = t0 + 0.012
    while tt < t1 - 0.01:
        dsp.mix_into(y, sfx._hit(r, [3800.0, 5600.0], [0.006, 0.004], click=0.6, n=n_of(0.012)), at(tt), 0.1)
        tt += 0.024
    dsp.mix_into(y, sfx._hit(r, [1300.0, 2300.0, 3500.0], [0.03, 0.02, 0.015], click=1.0, n=n_of(0.06)), at(t1), 0.5)
    for tp in pulses:
        dsp.mix_into(y, sfx._hit(r, [1700.0, 2900.0, 4400.0], [0.02, 0.015, 0.01], click=1.0, n=n_of(0.04)), at(tp), 0.8)
    dsp.mix_into(y, sfx._hit(r, [900.0, 1500.0], [0.03, 0.02], click=0.4, n=n_of(0.05)), at(home), 0.25)
    a, b = at(t_rel), at(home)
    tw = tax(b - a)
    whirr = dsp.bandpass(r.standard_normal(b - a), 600.0, 2400.0, 2) * 0.06 * (0.75 + 0.25 * np.cos(2 * np.pi * 10.0 * tw))
    y[a:b] += whirr * np.clip(tw / 0.01, 0, 1) * np.clip((home - t_rel - tw) / 0.03, 0, 1)
    return norm(dsp.fade(y, 0.002, 0.05))


def ringback(rings=2, on=0.9, off=0.5, seed=0):
    """The ringing in the receiver (440 + 480 Hz, the line's narrow band), rings x (on, off)."""
    n = n_of(rings * (on + off))
    t = tax(n)
    x = np.sin(2 * np.pi * 440.0 * t) + np.sin(2 * np.pi * 480.0 * t)
    ph = t % (on + off)
    gate = np.clip(ph / 0.015, 0, 1) * np.clip((on - ph) / 0.015, 0, 1)
    return norm(dsp.bandpass(x * gate, 300.0, 3400.0, 2))


@lru_cache(maxsize=None)
def sash(dur=0.55, seed=0, stop=True):
    """A sash window shoved up: wood dragging in its runners, a rattle, the stop at dur."""
    r = rng("sash", seed)
    n = n_of(dur + 0.4)
    t = tax(n)
    sw = np.clip(t / dur, 0, 1)
    drag = dsp.friction(n, 60.0 + 140.0 * np.sin(np.pi * sw), r, jitter=0.3,
                        body=[(240.0, 6, 1.0), (520.0, 8, 0.7), (1200.0, 10, 0.4)])
    drag = norm(drag) * np.clip((dur + 0.01 - t) / 0.02, 0, 1) * np.clip(t / 0.03, 0, 1)
    rattle = dsp.bandpass(dsp.crackle(n, 60.0, r), 1500.0, 6000.0, 2) * (t < dur)
    y = 0.7 * drag + 0.15 * norm(rattle)
    if stop:
        dsp.mix_into(y, door_thud(seed + 7, 0.4).mean(axis=1), n_of(dur - 0.004), 0.6)
    return norm(y)


@lru_cache(maxsize=None)
def horn_far(seed=0):
    """A car horn far off, on F and A."""
    n = n_of(0.6)
    t = tax(n)
    h = dsp.saw(349.2, n) + dsp.saw(440.0, n)
    h = dsp.sos(h, "lowpass", 900.0, 2) * np.clip(t / 0.03, 0, 1) * np.clip((0.55 - t) / 0.08, 0, 1)
    return norm(dsp.reverb(h, "street", wet_db=0.0, dry=0.4, seed=seed))


@lru_cache(maxsize=None)
def ladder(seed=0):
    """A drop ladder let go: it slides down its guides and lands (the clang at 0.2 s)."""
    r = rng("ladder", seed)
    y = np.zeros(n_of(1.6))
    k = n_of(0.22)
    slide = dsp.friction(k, 300.0 + 900.0 * np.linspace(0, 1, k), r, jitter=0.2,
                         body=[(900.0, 10, 1.0), (1500.0, 12, 0.6), (2600.0, 14, 0.3)])
    y[:k] += 0.5 * norm(slide) * np.linspace(0.3, 1.0, k)
    dsp.mix_into(y, norm(mono(fx("metal_clang", seed=seed))), n_of(0.2))
    return norm(y)


@lru_cache(maxsize=None)
def fridge(seed=0):
    r = rng("fridge", seed)
    y = np.zeros(n_of(0.6))
    y[:n_of(0.3)] += sfx._thump(n_of(0.3), 110.0, 55.0, 0.02, 0.12)
    y[:n_of(0.05)] += 0.4 * sfx._burst(n_of(0.05), r, 80.0, 900.0, t60=0.03)
    for j, f in enumerate((2400.0, 3100.0)):
        dsp.mix_into(y, sfx._hit(r, [f, f * 1.6, f * 2.7], [0.12, 0.09, 0.05], click=0.3, n=n_of(0.2)), n_of(0.03 + 0.05 * j), 0.2)
    return norm(y)


@lru_cache(maxsize=None)
def tv_off(seed=0):
    r = rng("tvoff", seed)
    n = n_of(0.25)
    t = tax(n)
    y = 0.3 * np.sin(2 * np.pi * np.cumsum(9000.0 * np.exp(-t / 0.05) + 300.0) / SR) * np.exp(-t / 0.06)
    c = sfx._click(r, 2500.0, 0.004)
    y[:len(c)] += norm(c)
    y[:24] *= np.linspace(0.0, 1.0, 24)
    return norm(y)


def radio(dur, seed=0):
    """A dance band through a little radio in the next room (F, swung, 120 bpm)."""
    r = rng("radio", seed)
    n = n_of(dur)
    y = np.zeros(n)
    walk = (-17, -13, -10, -8, -5, -8, -10, -13)
    k, tt = 0, 0.0
    while tt < dur:
        dsp.mix_into(y, pizz(note(walk[k % len(walk)] + 12), 0.7, seed=k)[:n_of(0.45)], n_of(tt))
        if k % 2:
            b = dsp.bandpass(r.standard_normal(n_of(0.12)), 2000.0, 8000.0, 2) * np.exp(-tax(n_of(0.12)) / 0.04)
            dsp.mix_into(y, 0.25 * b, n_of(tt))
        else:
            st = sum(dsp.saw(note(s), n_of(0.14)) for s in (7, 11, 14, 17))
            st = dsp.sos(st, "lowpass", 1400.0, 2) * np.exp(-tax(n_of(0.14)) / 0.06)
            dsp.mix_into(y, 0.12 * st, n_of(tt + 1.0 / 3.0))
        tt += BEAT
        k += 1
    y = norm(dsp.bandpass(y, 350.0, 2800.0, 2)) + 0.05 * norm(dsp.sos(dsp.crackle(n, 40.0, r), "highpass", 1500.0, 2))
    return norm(dsp.fade(y, 0.05, 0.03))


def murmur(dur, seed=0, f0=125.0, lo=400.0, hi=3200.0):
    """Voices with no words (a television, a radio play)."""
    r = rng("murmur", seed)
    m = int(np.ceil(dur * 16000))
    v = sfx._formant_voice(m, r, 16000, f0=f0, syl_rate=4.6)
    v = dsp.pad_to(dsp.resample(v, 16000, SR), n_of(dur))
    return norm(dsp.fade(dsp.bandpass(v, lo, hi, 2), 0.05, 0.05))


def wind_bed(amp, seed=0):
    """Wind at an open window, following amp (per sample)."""
    r = rng("wind", seed)
    a = np.clip(np.asarray(amp, np.float64), 0.0, 2.0)
    n = len(a)
    out = np.zeros((n, 2))
    for ch in range(2):
        x = dsp.tv_bandpass(dsp.pink(n, r), 260.0 + 650.0 * a, q=0.8, block=256)
        x += 0.45 * dsp.sos(dsp.brown(n, r), "lowpass", 260.0, 2)
        out[:, ch] = x * a * (1.0 + 0.2 * dsp.smooth_noise(n, 6.0, r))
    out += (dsp.tv_bandpass(r.standard_normal(n), 900.0 + 700.0 * a, q=14.0, block=256) * a ** 2 * 0.35)[:, None]
    return norm(dsp.fade(out, 0.2, 0.2))


def curtain(amp, seed=0):
    """A curtain fluttering in it (faster as the wind rises)."""
    r = rng("curtain", seed)
    a = np.clip(np.asarray(amp, np.float64), 0.0, 2.0)
    n = len(a)
    ph = np.cumsum(5.0 + 9.0 * np.clip(a, 0, 1)) / SR
    flut = dsp.onepole_lp(0.5 + 0.5 * np.sign(np.sin(2 * np.pi * ph + 0.6 * np.sin(2 * np.pi * 0.37 * ph))), 70.0)
    x = dsp.bandpass(r.standard_normal(n), 180.0, 2600.0, 2) * (0.3 + 0.7 * flut) * a
    x += 0.4 * norm(dsp.sos(dsp.pink(n, r), "lowpass", 600.0, 2)) * np.std(x) * 3.0 * a
    return norm(dsp.fade(x, 0.2, 0.2))


def siren(dur, seed=0, period=3.8, lo=640.0, hi=1420.0):
    r = rng("siren", seed)
    n = n_of(dur)
    x = sfx._siren_tone(sfx._siren_wail(n, r, period, lo, hi), n)
    return norm(dsp.bandpass(x, 350.0, 5000.0, 2))


def sample_fn(fn, t0, t1, step=0.01):
    """fn(t) sampled every step from t0 to t1, interpolated to samples."""
    ts = np.arange(t0, t1 + step, step)
    vs = np.array([float(fn(t)) for t in ts])
    return np.interp(t0 + tax(n_of(t1 - t0)), ts, vs)


def window_switches(tb0, tb1, step=1.0 / 480.0):
    """[(Bass time, window index, colour)] each time one of the Bass windows changes colour."""
    wins = BW.LEFT_WIN + BW.RIGHT_WIN
    prev = [BW.window_color(r, tb0) for r in wins]
    out = []
    for tb in np.arange(tb0, tb1, step):
        for i, r in enumerate(wins):
            c = BW.window_color(r, tb)
            if c != prev[i]:
                out.append((round(float(tb), 4), i, c))
                prev[i] = c
    return out


def bass_sip_tb():
    """Bass time the mug is up at her lips in the Bass sip (where the Bass cut put its sip)."""
    tbs = np.arange(BW.T_SIP[0], BW.T_SIP[1], 1.0 / 240.0)
    tilt = np.array([BW.sip_state(tb)[2] for tb in tbs])
    return float(tbs[int(np.argmax(tilt >= 0.999 * tilt.max()))])


# ============================================================================ s01 TITLE
def s01(m, t0):
    S = scene("s01")
    if S is None:
        return
    m.begin(S, "s01", t0)
    T_DOT = g(S, "T_DOT", (0.25, 0.5, 0.75))
    T_TITLE = g(S, "T_TITLE", 1.0)
    T_NIGHT = g(S, "T_NIGHT", 5.4)
    T_BARS = g(S, "T_BARS", 5.5)
    T_CITY = g(S, "T_CITY", 5.75)
    T_MOON = g(S, "T_MOON", 6.0)
    T_CUT = g(S, "T_CUT", 6.5)
    T_STOREY = g(S, "T_STOREY", tuple(7.0 + 0.25 * i for i in range(6)))
    T_OUT = g(S, "T_OUT", tuple(8.5 + 0.25 * i for i in range(7)))
    LIGHTS = g(S, "LIGHTS_OUT", None)
    HER_B = g(S, "HER_B", None)
    T_FRIDGE = g(S, "T_FRIDGE", 8.8)
    T_TV_OFF = g(S, "T_TV_OFF", 10.0)
    T_NUMS = g(S, "T_NUMS", 10.25)
    T_PUSH = g(S, "T_PUSH", (10.5, 12.0))

    # 0-1: the red dot pops three times: soft felt notes, B-flat, D-flat, F (the chord's first three)
    for i, t in enumerate(T_DOT):
        m.put("music", soft_hit(note((12, 15, 19)[i % 3]), i), t, -15 + 1.0 * i, label="red dot pop")
        m.put("efx", tick(i), t, -32)

    # 1-5.4: the Bass title as the Bass cut scored it (Bass time tb = t - T_TITLE)
    def tb(x):
        return T_TITLE + x
    m.mark(T_TITLE, "the Bass title")
    ostinato(m, T_TITLE, tb(BW.T_TITLE_CUT), vel=(0.45, 0.85), octave=-1, seed=1, gain=-4)
    for i, (s, _) in enumerate(BW.STRIPS):
        m.put("efx", fx("brush_swish", seed=10 + i), tb(s) + 0.08, -21, pan=0.6 if i % 2 else -0.6)
    tc = tb(BW.T_TITLE_CUT)
    m.put("music", rev(chord(PSYCHO, 0.5, 1.0, 21, octave=1)), tc, -9, label="title: the red cut")
    m.put("music", shrieks(n_stabs=1, seed=2), tc, -15)
    m.put("efx", fx("whip", seed=3), tc - 0.02, -15)
    m.put("efx", fx("whoosh", seed=4, size=0.4), tb(BW.T_PART), -17, pan=-0.4, label="title: halves part", align=None)
    m.put("efx", fx("whoosh", seed=5, size=0.4), tb(BW.T_PART) + 0.1, -17, pan=0.4)
    for j in range(6):
        m.put("efx", fx("brush_swish", seed=30 + j), tb(BW.T_FLOOD) + 0.06 * j, -21, pan=-0.7 + 0.28 * j)
    for j in range(2):
        m.put("efx", cut(fx("impact", seed=40 + j, size=0.25), 1.2, 0.3), tb(BW.T_RISE) + 0.12 * j + 0.32, -13, pan=-0.5 + j)
    m.put("music", rev(chord(PSYCHO, 1.1, 0.8, 23, octave=-1, stacc=False, spread=(0, -12))), tb(BW.T_RISE) + 0.3, -15)
    ostinato(m, tb(BW.T_MORPH), T_NIGHT, vel=(0.35, 0.55), octave=0, seed=5, gain=-9)

    # 5.4: night falls: the letters are windows; the others snap off (dry ticks), hers lights (her
    # note), then his (his note: the city's pizzicato descent starts on it)
    wins = BW.LEFT_WIN + BW.RIGHT_WIN
    her_i, his_i = wins.index(BW.HER_WIN), wins.index(BW.HIS_WIN)
    for tbs, i, col in window_switches(T_NIGHT - T_TITLE - 0.02, T_CUT - T_TITLE):
        t = T_TITLE + tbs
        side = -0.5 if i < len(BW.LEFT_WIN) else 0.5
        if col == BW.UNLIT:
            m.put("efx", fx("clock_tick", seed=50 + i), t, -27, pan=side)
        elif i == her_i:
            m.put("music", piano(note(24), vel=0.6, seed=1), t, -13, pan=-0.3, label="her light")
        elif i == his_i:
            m.put("music", piano(note(HIS + 12), vel=0.7, seed=2), t, -13, pan=0.3, label="his light")
    m.put("music", gong(note(-12)), T_BARS, -14, label="night falls: gong")
    m.put("music", rev(chord(MINOR, 2.5, 0.5, 31, octave=-1, stacc=False, spread=(0, 12))), T_BARS, -20)
    for j in range(7):
        m.put("efx", fx("brush_swish", seed=60 + j), T_BARS + 0.07 * j, -25, pan=-0.6 if j % 2 else 0.6)
    for j, s in enumerate((23, 19, 15, 12, 11, 7, 3, 0)):     # A4 F4 Db4 Bb3 A3 F3 Db3 Bb2: the city rises
        m.put("music", pizz(note(s), 0.85 - 0.04 * j, seed=j), T_CITY + E16 * j, -10, pan=0.4 - 0.1 * j,
              label="city rises: pizzicato" if j == 0 else None)
    m.put("music", bell(note(31), 1), T_MOON, -17, pan=0.35, label="moon: soft bell")
    city = bed("city_far", 12.0 - T_CITY, 11)
    m.put("amb", city * dsp.env_bp_db([(0.0, -40), (0.8, 0), (len(city) / SR, 0)], len(city))[:, None], T_CITY, -30)

    # 6.5: the cutaway: the slabs open; storey by storey the section snaps in (a paper click and a
    # harp note rising up the chord), the city lives a moment, then goes to bed light by light
    m.put("efx", fx("whoosh", seed=70, size=0.55), T_CUT - 0.15, -19, label="the cutaway", sync=T_CUT, align=None)
    m.put("music", strings((0, 3, 7), T_PUSH[0] - T_CUT, 0.6, seed=3, octaves=(-1, 0), attack=0.6, release=1.0,
                           env=[(0.0, 0.6), (1.5, 1.0), (T_PUSH[0] - T_CUT, 0.8)]), T_CUT, -21)
    for i, t in enumerate(T_STOREY):
        m.put("efx", paper_snap(i), t, -24, pan=(-0.3, 0.3)[i % 2])
        m.put("music", harp(note((12, 15, 19, 23, 24, 27)[i % 6]), 0.7, seed=i), t, -13, pan=(-0.25, 0.25)[i % 2],
              label=f"storey {i + 1} opens")
    for k in range(int(round((T_PUSH[0] - T_STOREY[0]) / BEAT))):        # a soft pulse: the city's life
        t = T_STOREY[0] + k * BEAT
        m.put("music", pizz(note(-12 if k % 2 == 0 else -19), 0.55, seed=20 + k), t, -18)
    rad_on, rad_off = T_STOREY[1], T_OUT[3] if len(T_OUT) > 3 else T_STOREY[1] + 2.0
    m.put("amb", radio(rad_off - rad_on), rad_on, -31, pan=-0.45, label="radio", align=None)
    m.put("efx", switch(4), rad_off, -30, pan=-0.45)
    tv_on = T_STOREY[2]
    m.put("amb", murmur(T_TV_OFF - tv_on, seed=3), tv_on, -32, pan=-0.45, label="tv murmur", align=None)
    m.put("efx", tv_off(), T_TV_OFF, -28, pan=-0.45)
    m.put("efx", fridge(), T_FRIDGE, -20, pan=0.45, label="fridge")
    out_notes = (31, 29, 27, 26, 24, 23, 19)                             # F5 Eb5 Db5 C5 Bb4 A4 F4
    for j, t in enumerate(T_OUT):
        her_side = LIGHTS is not None and HER_B is not None and j < len(LIGHTS) and LIGHTS[j][0] is HER_B
        side = -0.4 if (her_side if LIGHTS is not None else j % 2) else 0.4
        m.put("music", harp(note(out_notes[min(j, len(out_notes) - 1)]), 0.75, seed=10 + j), t, -12, pan=side,
              label="light out")
        m.put("efx", switch(10 + j), t - 0.01, -31, pan=side)
    # 10.25: her 4 turns paper, his 5 red: her note, high; his, low
    m.put("music", celesta(note(HER), 0.8, 1), T_NUMS, -11, pan=-0.3, label="her 4")
    m.put("music", piano(note(HIS), dur=2.4, vel=0.8, seed=4), T_NUMS, -10, pan=0.3)
    m.put("music", pizz(note(HIS + 12), 0.8, seed=5), T_NUMS, -14, pan=0.3)
    # 10.5-12: a tremolo rising into her room, a chord a beat (B-flat minor, E-flat minor, F: the
    # dominant, which s02's first bar resolves), cut on the bar
    a, b = T_PUSH
    steps = ((0, 3, 7), (3, 6, 10), (5, 9, 12), (5, 9, 12))
    k = 0
    while a + k * BEAT < b - 1e-6:
        t = a + k * BEAT
        d = min(BEAT + 0.04, b - t)
        x = tremolo(steps[min(k, len(steps) - 1)], d + 0.02, 0.8, seed=7 + k, octave=1)[: n_of(d)]
        m.put("music", dsp.fade(x, 0.004, 0.02), t, -19 + 3.0 * k, label="push in: tremolo" if k == 0 else None)
        k += 1
    m.put("music", fx("reverse_swell", dur=b - a, seed=8), a, -22)
    m.end()


# ============================================================================ s02 AMBER
S02_HARM = {   # a bar of oom-pah pizzicato: (beat 1 bass, beat 3 bass, the double-stops on 2 and 4)
    "Bbm": (-12, -19, (3, 7), (3, 7)),
    "EbF": (-7, -5, (8, 12), (-1, 5)),
    "Gb": (-16, -9, (3, 7), (3, 7)),
    "A": (-13, -13, (2, 5), (2, 5)),
}
S02_PLAN = ("Bbm", "Bbm", "EbF", "Gb", "Bbm", "Bbm")
# her theme (celesta): (beat in the phrase, semitones over Bb2, beats)
HER_THEME = ((0, 31, 2), (2, 27, 1), (3, 26, 1), (4, 27, 2), (6, 24, 1), (7, 23, 1),
             (8, 24, 1), (9, 27, 1), (10, 31, 1), (11, 36, 1), (12, 35, 2), (14, 31, 1), (15, 27, 1),
             (16, 26, 2), (18, 27, 1), (19, 24, 1))


def s02(m, t0):
    S = scene("s02")
    if S is None:
        return
    m.begin(S, "s02", t0)
    L = m.len
    T_STEAM = g(S, "T_STEAM", 0.3)
    T_RIPPLES = g(S, "T_RIPPLES", (0.5, 1.0, 1.5))
    T_LIFT = g(S, "T_LIFT", 2.0)
    T_GAS = g(S, "T_GAS", 2.25)
    T_POUR = g(S, "T_POUR", 3.22)
    T_POUR_END = g(S, "T_POUR_END", 4.42)
    T_DOWN = g(S, "T_DOWN", 4.76)
    T_MUG_UP = g(S, "T_MUG_UP", 4.86)
    T_WIDE = g(S, "T_WIDE", 5.0)
    T_SIP = g(S, "T_SIP", 8.0)
    SIP_TB = g(S, "SIP_TB", 5.6)
    T_OTS = g(S, "T_OTS", 10.0)
    T_SIGHT = g(S, "T_SIGHT", 10.6)
    T_BOLT = g(S, "T_BOLT", (12.6, 13.5))
    CLOCK_IN = g(S, "CLOCK_IN", 0.45)

    # her wall clock jumps on every beat (rooms.clock_time): dry and close, until we are at the glass
    i = 0
    while i * BEAT < T_OTS + 1.0:
        t = i * BEAT
        m.put("efx", tick(i), t, -19 - max(0.0, t - T_OTS + BEAT) * 10.0, pan=0.15,
              label="clock tick" if i == 0 else None)
        i += 1
    m.put("efx", glass_tick(), CLOCK_IN, -24, pan=0.15, label="clock lens")
    m.put("amb", bed("room_tone", L, 21), 0.0, -30)

    # the kettle sings on the picture's own curve (whistle_amt), its rings on the beat
    end = T_LIFT + 0.6
    amp = sample_fn(lambda t: call(S, "whistle_amt", t, default=float(np.clip((t - T_STEAM) / 0.7, 0, 1))
                                   * (1.0 if t < T_LIFT else max(0.0, 1.0 - (t - T_LIFT) / 0.25))), 0.0, end)
    tt = tax(len(amp))
    for tr in T_RIPPLES:
        amp = amp * (1.0 + 0.25 * np.where(tt >= tr, np.exp(-(tt - tr) / 0.12), 0.0))
    m.put("efx", kettle(amp), 0.0, -17, pan=-0.15, label="kettle sings", sync=T_STEAM, align=None)
    m.put("efx", gas_bed(T_GAS + 0.03), 0.0, -31, pan=-0.15)
    m.put("efx", gas_off(), T_GAS, -21, pan=-0.15, label="gas off")
    m.put("efx", clink(1, 1800.0), T_LIFT, -27, pan=-0.15, label="kettle lifted")
    m.put("efx", pour(T_POUR_END - T_POUR), T_POUR, -15, label="pour")
    m.put("efx", clunk(), T_DOWN, -19, pan=-0.1, label="kettle down")
    m.put("efx", clink(3, 2900.0), T_MUG_UP, -30)
    steps = call(S, "footfalls", default=None) or (T_WIDE + 0.17, T_WIDE + 0.69, T_WIDE + 1.58)
    her = bank("her_steps", -28.0)
    for j, ft in enumerate(steps):
        m.put("feet", dsp.sos(her[j % len(her)], "lowpass", 2400.0, 2), ft - STEP_PRE, -21, pan=-0.1 + 0.1 * j,
              label="her step", sync=ft)
    t_sip = T_SIP + (bass_sip_tb() - SIP_TB)          # the mug at her lips in the Bass sip it cuts to
    m.put("vox", dsp.reverb(OB.sip(1), "small_room", wet_db=-18.0, seed=3).mean(axis=1), t_sip, -11, label="the sip")
    m.put("efx", fx("brush_swish", seed=21), T_SIP - 0.03, -27)
    m.cover("the sip")
    m.put("efx", fx("whoosh", seed=22, size=0.3), T_SIGHT - 0.05, -21, pan=0.3, label="her look flies", sync=T_SIGHT, align=None)

    # across the street, through the glass: the couple's quarrel, then two shouts (his)
    q0 = T_OTS + 0.3
    q = gen("quarrel", 0.4, 0.4 + (L - q0) + 0.3, fade=0.3)
    far = glass(q, lp=1300.0, seed=4)
    far = far * dsp.env_bp_db([(0.0, -40), (0.8, -10), (L - q0 - 0.4, 0), (len(far) / SR, -40)], len(far))
    m.put("vox", far, q0, -26, pan=0.35)
    for j, t in enumerate(T_BOLT):
        xb = glass(shout("man", (1, 0)[j % 2]), lp=1700.0, seed=5 + j)
        m.put("vox", xb, t - onset_at(xb), -9 - 2 * j, pan=0.35, label="muffled shout", sync=t, key=True)

    # the music: pizzicato, her theme on the celesta from the lift; the shouts darken the last bar
    nbar = int(round(L / 2.0))
    bolt_bar = int(T_BOLT[0] // 2.0) if T_BOLT else nbar
    m.mark(0.0, "celesta over pizzicato")
    for b in range(nbar):
        h = S02_HARM["A"] if b >= bolt_bar else S02_HARM[S02_PLAN[min(b, len(S02_PLAN) - 1)]]
        for k in range(4):
            t = 2.0 * b + k * BEAT
            if k % 2 == 0:
                m.put("music", pizz(note(h[k // 2]), 0.75, seed=b * 4 + k), t, -13)
            else:
                for s in h[2 + k // 2]:
                    m.put("music", pizz(note(s), 0.45, seed=b * 4 + k + s), t, -18, pan=0.15)
    start = 2.0 * math.floor(T_LIFT / 2.0 + 1e-6)
    for beat, s, ln in HER_THEME:
        t = start + beat * BEAT
        if t >= 2.0 * bolt_bar - 1e-6:
            break
        m.put("music", celesta(note(s), 0.75, seed=beat), t, -12, pan=-0.1)
    a = 2.0 * bolt_bar
    if a < L:
        x = tremolo((-13, -10, -7), L - a + 0.05, 0.7, seed=9, octave=0)[: n_of(L - a)]
        m.put("music", dsp.fade(x * np.linspace(0.3, 1.0, len(x)), 0.0, 0.02), a, -18)
    m.end()


# ============================================================================ s03 QUARREL
def s03(m, t0):
    S = scene("s03")
    if S is None:
        return
    m.begin(S, "s03", t0)
    L = m.len
    T_LAND = g(S, "T_LAND", 1.5)
    SHOUTS = g(S, "SHOUTS", ((1.625, "man"), (2.125, "vic"), (2.375, "man"), (2.875, "vic"), (3.125, "man"),
                             (3.875, "vic"), (4.125, "man"), (4.375, "vic"), (4.875, "man"), (5.125, "vic"),
                             (5.875, "vic"), (6.125, "vic")))
    T_RING = g(S, "T_RING", 3.5)
    T_LOOK = g(S, "T_LOOK", 5.5)
    T_WIND = g(S, "T_WIND", 6.17)
    T_SLAP = g(S, "T_SLAP", 6.5)
    T_TURN = g(S, "T_TURN", 6.85)
    T_LOOK_AGAIN = g(S, "T_LOOK_AGAIN", 7.4)
    T_EYE = g(S, "T_EYE", 8.0)
    T_BLINK = g(S, "T_BLINK", 9.12)
    T_DIVE = g(S, "T_DIVE", 9.5)
    T_INSERT = g(S, "T_INSERT", 10.0)
    T_EXIT = g(S, "T_EXIT", 10.45)
    T_HAND = g(S, "T_HAND", 11.5)
    T_GRIP = g(S, "T_GRIP", 11.75)
    T_CLOSE = g(S, "T_CLOSE", 11.95)
    T_LIFT = g(S, "T_LIFT", 12.2)
    T_SHE_TURNS = g(S, "T_SHE_TURNS", 13.3)
    JUMPS = g(S, "JUMPS", ())

    # 0-1.5: along her look, into his window: air, and the shouting bar's tension climbing
    m.put("efx", rush(T_LAND, seed=1), 0.0, -13, label="into his window", sync=0.0, align=None)
    ostinato(m, 0.0, T_LAND, step=E8, semis=(-1, 2, 5), vel=(0.3, 0.75), accent=(0, 4), seed=11, gain=-10)
    m.put("amb", bed("room_tone", L - T_LAND, 31), T_LAND, -29)

    # 1.5-5.5: the quarrel close; the strings drive in sixteenths (a semitone up from the ring),
    # a low B-flat chugging in eighths; the frame jumps in on the beat, a thud each
    m.mark(T_LAND, "the quarrel, sixteenths")
    ostinato(m, T_LAND, T_LOOK, step=E16, vel=(0.5, 0.95), accent=(0, 3, 6, 8, 11, 14), seed=13, gain=-12,
             lift=lambda t: 1 if t >= T_RING else 0)
    ostinato(m, T_LAND, T_LOOK, step=E8, semis=(0,), octave=-1, spread=(0,), vel=(0.6, 0.9), accent=(0, 4), seed=17,
             gain=-12, lift=lambda t: 1 if t >= T_RING else 0)
    for j in JUMPS:
        if T_LAND < j[0] < T_EYE and abs(j[0] - T_SLAP) > 0.05:
            m.put("efx", cut(fx("impact", seed=int(j[0] * 10), size=0.08), 0.5, 0.15), j[0], -22)
    kk = {"man": 0, "vic": 0}
    for t, who in SHOUTS:
        k = kk.setdefault(who, 0)
        kk[who] += 1
        x = shout(who if who in Q_UNITS else "man", k)
        dropped = t >= T_LOOK
        if dropped:                                          # the quarrel drops away under his look
            x = dsp.sos(x, "lowpass", 1100.0, 2)
        x = dsp.pan_stereo(near(x, seed=k), -0.2 if who == "man" else 0.25)
        m.put("vox", x, t - onset_at(x), (-6.5 if who == "man" else -7.5) - (9 if dropped else 0),
              label=f"shout ({who})", sync=t, key=True)
    m.put("efx", squeak(0.4, 1), T_RING, -13, pan=0.1, label="the ring: squeak")
    m.put("music", harmonic(note(HIS + 60), 0.35, 0.8, seed=1, attack=0.01, release=0.6, sfz=True), T_RING, -15)

    # 5.5: his look locks on the knife: his low A; the drive sinks under it
    m.put("music", bowed_line([(0.0, HIS)], T_SLAP - T_LOOK + 0.1, 0.9, seed=2, octaves=(0, 1), attack=0.12, release=0.25),
          T_LOOK, -9, pan=-0.15, label="his look: low A")
    ostinato(m, T_LOOK, T_SLAP, step=E16, vel=(0.25, 0.4), accent=(), seed=19, gain=-18, octave=1, lift=lambda t: 1)
    breath = gen("her_breath", 3.0, 3.32, fade=0.02)
    m.put("vox", near(breath, 5), T_WIND - 0.04, -12, pan=0.25, label="her breath in", sync=T_WIND)
    m.put("efx", slap(), T_SLAP, -3, pan=-0.1, label="slap")
    m.put("music", stab(1), T_SLAP, -9)
    m.put("efx", rustle(0.3, 2, 300.0, 3500.0), T_TURN, -19, pan=0.25, label="she turns")
    her = bank("her_steps", -28.0)
    for j, dt in enumerate((0.1, 0.32)):
        m.put("feet", her[(j + 2) % len(her)], T_TURN + dt - STEP_PRE, -21, pan=0.3)
    m.put("music", bowed_line([(0.0, HIS)], 0.6, 0.7, seed=3, octaves=(0, 1), attack=0.1, release=0.4), T_LOOK_AGAIN,
          -15, pan=-0.15, label="his look again")

    # 8-10: her eye: the Bass cut's high tremolo; the blink; into the reflection
    m.put("music", cut(tremolo((10, 11, 12), T_INSERT - T_EYE + 0.15, 0.7, seed=3), T_INSERT - T_EYE + 0.15, 0.12), T_EYE,
          -11, label="her eye: tremolo")
    m.put("efx", fx("clock_tick", seed=7), T_BLINK, -22, label="blink")
    m.put("efx", rush(T_INSERT - T_DIVE, seed=2, peak=0.95), T_DIVE, -14, label="into the reflection", align=None)

    # 10-14: the insert: near silence and his low A; he goes; his hand; the knife
    m.put("music", bowed_line([(0.0, HIS)], L - T_INSERT, 0.8, seed=4, octaves=(0,), attack=0.5, release=0.3,
                              env=[(0.0, 0.7), (L - T_INSERT - 1.5, 0.6), (L - T_INSERT, 1.0)]), T_INSERT, -15,
          label="the insert: low A")
    walk = None
    if not isinstance(S, Stub) and hasattr(S, "_perfs"):
        try:
            walk = [t for t in mocap_footfalls(S._perfs()[3], T_EXIT + 0.08, T_HAND) if t > T_EXIT + 0.1]
        except Exception as e:
            warn(f"s03: his exit footfalls ({e}): spaced from T_EXIT")
    walk = walk or [T_EXIT + 0.2 + 0.27 * j for j in range(3)]
    up = bank("stairs_up")
    for j, ft in enumerate(walk[:4]):
        m.put("feet", dsp.sos(up[(j + 3) % len(up)], "lowpass", 2200.0 - 300.0 * j, 2), ft - STEP_PRE, -15 - 3.0 * j,
              pan=-0.2 - 0.15 * j, label="his steps, going" if j == 0 else None, sync=ft)
    m.cover("his steps")
    m.put("efx", rustle(0.35, 3, 250.0, 3000.0), T_HAND, -17, pan=-0.2, label="sleeve")
    m.put("efx", clink(5, 1500.0), T_GRIP, -30, label="hand on the handle")
    m.put("efx", creak(0.3, 4), T_CLOSE, -15, label="grip creak")
    m.put("efx", scrape(0.2, 5), T_LIFT, -9, label="knife off the counter")
    m.put("efx", sfx._thump(n_of(0.3), 120.0, 60.0, 0.015, 0.15), T_LIFT + 0.02, -10)
    m.put("efx", knife_ring(6), T_LIFT + 0.05, -20, pan=0.2)
    m.put("efx", paper_snap(7), T_LIFT + 0.02, -12, label="the ring snaps")
    m.put("vox", dsp.sos(gen("gasp_a", 0.0, 0.5, fade=0.01), "lowpass", 3000.0, 2), T_SHE_TURNS, -16, pan=0.3,
          label="her breath catches", key=True)
    m.end()


# ============================================================================ s04 KNIFE
def s04(m, t0):
    S = scene("s04")
    if S is None:
        return
    m.begin(S, "s04", t0)
    L = m.len
    TB = g(S, "TB_KNIFE", 14.0)
    T_STABS = g(S, "T_STABS", tuple(round(s - TB, 3) for s in BW.STABS))
    T_CUTS = g(S, "T_CUTS", tuple(round(s - TB, 3) for s in BW.T_SLASH))
    T_FALL = g(S, "T_FALL", round(BW.T_SLASH[2] + 0.02 - TB, 3))
    T_BARS = g(S, "T_BARS", round(BW.T_BARS - TB, 3))
    T_GASP = g(S, "T_GASP", 2.55)
    T_DROP = g(S, "T_DROP", 2.95)
    T_HAND = g(S, "T_HAND", 3.17)
    T_SMASH = g(S, "T_SMASH", 3.6)
    T_HORROR = g(S, "T_HORROR", 4.5)
    T_STREET = g(S, "T_STREET", 9.0)
    T_HIS_LIGHT = g(S, "T_HIS_LIGHT", 9.5)
    DUB = g(S, "DUB", 0.24)
    HEART_BPM = g(S, "HEART_BPM", (90.0, 140.0))

    def cut_off(x, at):
        """The strings cut off at the bars (scene time; x starts at `at`)."""
        k = n_of(max(0.0, T_BARS - at))
        x = np.array(x[: k + n_of(0.02)], np.float64)
        if len(x) > k:
            x[k:] *= np.linspace(1.0, 0.0, len(x) - k)[:, None] if x.ndim == 2 else np.linspace(1.0, 0.0, len(x) - k)
        return x

    # the knife goes up: the Bass cut's tightening string, the high tremolo, the shrieks begin
    # (kd: the knife and the mug sit under s10's climax)
    kd = -4.0
    m.put("music", cut(fx("string_tighten", seed=4), 1.0, 0.2), -0.3, -13 + kd)
    m.put("music", cut_off(tremolo((11, 12, 13), T_CUTS[0] + 0.3, 0.9, seed=5), 0.0), 0.0, -15 + kd)
    m.put("music", shrieks(n_stabs=3, every=0.13, f0=1318.5, seed=9), 0.0, -14 + kd, label="the shrieks begin")
    for j, ts in enumerate(T_STABS):
        m.put("music", shrieks(n_stabs=2, every=0.09, f0=1318.5 * SEMI ** j, seed=10 + j), ts - 0.01, -12 + kd, label=f"stab {j + 1}",
              sync=ts)
    for j, tc in enumerate(T_CUTS):
        m.put("efx", cut(fx("impact", seed=75 + j, size=0.1), 0.4, 0.12), tc, -9 + kd, pan=0.1, label=f"tear {j + 1}")
        m.put("efx", cut(mono(fx("paper_tear", seed=80 + j)), 0.35, 0.1), tc, -13 + kd, pan=(-0.4, 0.4, 0.0)[j % 3])
        m.put("efx", fx("whip", seed=70 + j), tc - 0.18, -13 + kd, pan=(-0.4, 0.4, 0.0)[j % 3])
    m.put("music", stinger(6), T_CUTS[0], -16 + kd)
    sc = dsp.reverb(gen("scream_a", 0.08, 0.08 + 0.9 + 0.35, fade=0.06), "small_room", wet_db=-12.0, seed=4).mean(axis=1)
    m.put("vox", sc, T_CUTS[0] - onset_at(sc), -18, label="her scream", sync=T_CUTS[0], key=True)
    bf = gen("body_fall", 0.0, 1.3, fade=0.004)
    on = int(np.argmax(np.abs(bf) >= 0.2 * np.max(np.abs(bf)))) / SR
    m.put("efx", bf, T_FALL - on, -11 + kd, pan=0.2, label="body fall", sync=T_FALL)
    for j in range(9):                                       # the bars close: his light goes out
        m.put("efx", fx("brush_swish", seed=80 + j), T_BARS + 0.05 * j, -19 + kd, pan=-0.6 if j % 2 else 0.6)
    m.mark(T_BARS, "the bars close: strings cut off")
    m.put("music", rev(chord(PSYCHO, 0.4, 1.0, 31, octave=-1, spread=(0, -12))), T_BARS + 0.45, -11 + kd)
    m.put("music", fx("sub_drop", seed=1), T_BARS + 0.45, -10 + kd)

    # the mug: her gasp, it drops, her hand over her mouth, the smash
    m.put("vox", gen("gasp_b", 0.0, 0.9, fade=0.005), T_GASP, -5 + kd, label="her gasp", key=True)
    m.put("efx", fx("whoosh", seed=91, size=0.25), T_DROP, -22 + kd, pan=0.4, label="mug drops", align=None)
    m.put("vox", dsp.sos(gen("stifled", 0.0, 1.5, fade=0.06), "lowpass", 2200.0, 2), T_HAND + 0.02, -19,
          label="stifled cry", sync=T_HAND, key=True)
    sm = gen("mug_smash", 0.0, 1.4, fade=0.003)
    on = int(np.argmax(np.abs(sm) >= 0.2 * np.max(np.abs(sm)))) / SR
    m.put("efx", sm, T_SMASH - on, -4 + kd, pan=0.35, label="mug smash", sync=T_SMASH)

    # her horror: her heart alone, 90 rising to 140 bpm; over it one high string, swirling with
    # the Vertigo spiral (its pitch bends with the spiral's turn)
    beats = call(S, "heart_beats", default=None)
    if not beats:
        beats, t = [], T_HORROR + 0.08
        while t < T_STREET:
            beats.append(t)
            u = (t - T_HORROR) / (T_STREET - T_HORROR)
            t += 60.0 / (HEART_BPM[0] + (HEART_BPM[1] - HEART_BPM[0]) * u ** 0.8)
    for j, tb in enumerate(beats):
        u = (tb - T_HORROR) / max(T_STREET - T_HORROR, 1e-6)
        m.put("music", heart(round(DUB, 3), seed=j % 3), tb, -5 + 3.0 * u, label="heartbeat", hall=-22)

    def swirl(t):
        turn = np.array([float(call(S, "spiral_turn", T_HORROR + float(x), default=0.0)) for x in t[:: n_of(0.02)]])
        return np.interp(t, t[:: n_of(0.02)], 0.35 * np.sin(turn))
    hd = T_STREET - T_HORROR
    m.put("music", harmonic(note(HER + 12), hd, 0.7, seed=3, attack=1.0, release=0.4, bend=swirl), T_HORROR, -27,
          pan=0.2, label="vertigo: high string")
    m.put("music", harmonic(note(HER + 19), hd, 0.5, seed=4, attack=1.5, release=0.4, bend=swirl), T_HORROR, -33, pan=-0.2)

    # the silent street; his light; his breath, slow and close (it carries over into s05)
    city = bed("city_far", L - T_STREET + 2.0, 4)
    m.put("amb", city * dsp.env_bp_db([(0.0, -40), (0.5, 0), (len(city) / SR, 0)], len(city))[:, None], T_STREET, -36,
          label="silent street", align=None)
    m.put("efx", switch(1), T_HIS_LIGHT, -15, pan=0.35, label="his light switch")
    hb = gen("his_breath", 1.0, 4.0, fade=0.05)
    m.put("vox", dsp.sos(hb, "highpass", 90.0, 2), T_HIS_LIGHT + 0.3, -9, pan=0.1, label="his breath",
          sync=T_HIS_LIGHT + 0.3, align=None)
    m.end()


# ============================================================================ s05 SEEN
def s05(m, t0):
    S = scene("s05")
    if S is None:
        return
    m.begin(S, "s05", t0)
    L = m.len
    TB = g(S, "TB", 10.5)
    T_LISTEN = g(S, "T_LISTEN", 4 / 12.0)
    T_HEAD = g(S, "T_HEAD", 11 / 12.0)
    T_TURN = g(S, "T_TURN", 14 / 12.0)
    T_OPEN = g(S, "T_OPEN", 2.15)
    T_PUPIL = g(S, "T_PUPIL", 2.75)
    T_LOOK = g(S, "T_LOOK", 3.6)
    T_RING = g(S, "T_RING", 3.95)
    T_FLINCH = g(S, "T_FLINCH", 4.35)
    T_MIRROR = g(S, "T_MIRROR", 5.5)
    T_PANELS = g(S, "T_PANELS", 5.62)
    T_DOTS = g(S, "T_DOTS", 6.05)
    T_SEEN = g(S, "T_SEEN", T_DOTS + 0.45)
    T_PRESS = g(S, "T_PRESS", (6.0, 6.5, 7.0, 7.5))
    T_ARM = g(S, "T_ARM", 8.0)
    T_GROW = g(S, "T_GROW", BW.T_GROW - TB)
    T_GRAB = g(S, "T_GRAB", 9.5)
    T_RETRACT = g(S, "T_RETRACT", BW.T_RETRACT - TB)
    T_GONE = g(S, "T_GONE", BW.T_GONE - TB)
    T_PULL = g(S, "T_PULL", BW.T_PULL - TB)
    T_HEART = g(S, "T_HEART", 11.7)
    HEART_BPM = g(S, "HEART_BPM", 132.0)

    # his back, listening: a low string swell under his breath; his head comes round, then he does
    m.put("music", strings((HIS, HIS + 1), 2.2, 0.8, seed=5, octaves=(0, 1), attack=0.8, release=0.6,
                           env=[(0.0, 0.4), (1.3, 1.0), (2.2, 0.5)]), 0.0, -17, label="low string swell")
    m.put("music", harmonic(note(HER + 12), 1.2, 0.6, seed=6, attack=0.3, release=0.6), T_LISTEN, -27, pan=0.3,
          label="he listens: harmonic")
    m.put("efx", rustle(0.3, 11, 250.0, 2500.0), T_HEAD, -19, label="collar")
    m.put("music", bowed_line([(0.0, 3), (0.35, -1), (0.8, -1)], 0.8, 0.8, seed=7, octaves=(-1,), attack=0.06, release=0.4),
          T_TURN, -12, label="cello slide")
    m.put("efx", cut(fx("impact", seed=51, size=0.06), 0.4, 0.12), g(S, "T_JUMP", 1.5), -24)
    m.put("efx", fx("clock_tick", seed=13), T_OPEN, -16, label="eye opens: tick")
    m.put("music", stinger(9), T_PUPIL, -8, label="pupil: stinger")
    m.put("music", shrieks(n_stabs=1, f0=1396.9, seed=20), T_PUPIL, -18)

    # the wide street: his look zips across; the ring round her window; the braam; her flinch
    m.put("efx", zip_(0.3, 1), T_LOOK, -11, label="his look: zip")
    m.put("efx", squeak(0.4, 2), T_RING, -12, pan=-0.3, label="ring: squeak")
    m.put("music", cut(braam(1), 1.4, 0.4), T_RING + 0.05, -8, label="braam")
    gs = dsp.sos(gen("gasp_a", 0.0, 0.6, fade=0.005), "lowpass", 1500.0, 2)
    m.put("vox", gs, T_FLINCH, -15, pan=-0.35, label="her gasp, stifled", key=True)
    m.put("amb", bed("city_far", T_MIRROR - 3.5 + 0.5, 5), 3.5, -33)

    # the mirror: the red split, the halves slam in, then press in on her heart, four times,
    # under a held dissonance (the chord with his A against her B-flat, and B natural)
    rs = fx("brush_swish", seed=52)
    m.put("efx", rs, T_MIRROR - onset_at(rs), -15, label="red split", sync=T_MIRROR)
    m.put("efx", paper_snap(3), T_MIRROR, -16)
    m.put("efx", fx("whip", seed=53), T_MIRROR - 0.18, -18)
    m.put("efx", cut(fx("impact", seed=54, size=0.3), 1.2, 0.3), T_PANELS, -10, label="halves slam")
    m.put("efx", door_thud(5, 1.2), T_PANELS, -14)
    for j, t in enumerate(T_PRESS):
        m.put("music", heart(0.16, seed=j % 3), t, -5, label="press: heartbeat", hall=-22)
    dis = strings((-1, 0, 1, 11, 12), T_ARM - T_PRESS[0] + 0.3, 0.8, seed=8, octaves=(0, 1), attack=0.4, release=0.5,
                  env=[(0.0, 0.5), (T_ARM - T_PRESS[0], 1.0)])
    m.put("music", dis, T_PRESS[0], -17, label="sustained dissonance")
    m.put("music", tremolo((23, 24), T_ARM - T_PRESS[0], 0.5, seed=9, octave=1), T_PRESS[0], -26)
    m.put("music", harmonic(note(24), T_SEEN - T_DOTS + 0.2, 0.7, seed=10, attack=0.1, release=0.3,
                            bend=lambda t: 12.0 * np.clip(t / max(T_SEEN - T_DOTS, 0.05), 0, 1)), T_DOTS, -18,
          label="dots: rising glass")
    m.put("efx", glass_tick(2), T_SEEN, -24)

    # the Bass arm (Bass time = t + TB): his light again; the arm grows (braam); the claw; it snaps back
    t_on = BW.T_HIS_ON - TB
    m.put("amb", bed("city_far", T_PULL - T_ARM + 0.3, 6), T_ARM, -30)
    m.put("efx", fx("clock_tick", seed=4), t_on, -16, pan=0.4)
    m.put("music", rev(chord((0, 1), T_GROW - t_on + 0.6, 0.6, 41, octave=-1, stacc=False, spread=(0, -12)), -8.0), t_on, -19)
    m.put("music", cut(braam(2), T_PULL - T_GROW, 0.04), T_GROW, -8, label="arm grows: braam")
    m.put("efx", fx("whoosh", seed=93, size=0.6), T_GROW - 0.05, -14, pan=-0.2)
    m.put("music", stab(2, octave=1), T_GRAB, -8, label="claw: string stab")
    m.put("music", shrieks(n_stabs=1, f0=1244.5, seed=22), T_GRAB, -17)
    m.put("efx", fx("whip", seed=94), T_RETRACT - 0.18, -11, pan=0.4, label="snaps back: whip", sync=T_RETRACT, align=None)
    runs = bank("street_run", -14.0, 0.2)
    for j, dt in enumerate((0.12, 0.3, 0.47)):
        m.put("feet", glass(runs[j], lp=1500.0, seed=20 + j), T_RETRACT + dt - STEP_PRE, -16, pan=0.5)
    m.put("efx", glass(fx("door_close", seed=6), lp=1300.0, seed=5), T_GONE + 0.4, -13, pan=0.6)

    # the Bass off: her hand to the cord: all dark; her heart alone in the dark
    m.put("efx", dsp.sos(cut(mono(fx("keys", seed=7)), 0.3, 0.08), "highpass", 2500.0, 2), T_PULL - 0.2, -27)
    m.put("efx", fx("clock_tick", seed=6), T_PULL, -8, label="light cord: click")
    m.put("music", fx("sub_drop", seed=3), T_PULL + 0.05, -14)
    beat = 60.0 / HEART_BPM
    k = 0
    while T_HEART + k * beat < L - 0.05:
        m.put("music", heart(0.16, seed=k % 3), T_HEART + k * beat, -7, label="heartbeat in the dark" if k == 0 else None,
              hall=-22)
        k += 1
    m.end()


# ============================================================================ s06 DARK
def chain_slide(dur, catch=None, seed=0):
    """A door chain's knob slid along its slotted track: steel dragging in the slot, the links
    shivering with her hand, a hitch where it catches (catch: s from the start)."""
    r = rng("cslide", seed)
    n = n_of(dur + 0.1)
    t = tax(n)
    on = np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.02, 0, 1)
    sp = 0.6 + 0.4 * np.sin(np.pi * np.clip(t / dur, 0, 1))
    y = dsp.friction(n, 380.0 + 500.0 * sp, r, jitter=0.35, body=[(2400.0, 12, 1.0), (3700.0, 14, 0.7), (5600.0, 16, 0.4)])
    y = norm(y) * on * sp
    for tt in dsp.poisson_times(14.0, dur, r):
        f = r.uniform(2600.0, 5200.0)
        dsp.mix_into(y, sfx._hit(r, [f, f * 1.45], [0.03, 0.02], click=0.4, n=n_of(0.05)), n_of(tt), r.uniform(0.1, 0.3))
    if catch is not None:
        dsp.mix_into(y, sfx._hit(r, [1900.0, 3100.0, 4700.0], [0.03, 0.02, 0.015], click=1.0, n=n_of(0.06)), n_of(catch), 0.6)
    return norm(y)


def chain_shiver(dur, seed=0):
    """A door chain hanging from trembling fingers: its links ticking against each other."""
    r = rng("cshiver", seed)
    y = np.zeros(n_of(dur + 0.1))
    for tt in dsp.poisson_times(22.0, dur, r):
        f = r.uniform(2800.0, 5600.0)
        dsp.mix_into(y, sfx._hit(r, [f, f * 1.5], [0.025, 0.015], click=0.5, n=n_of(0.04)), n_of(tt), r.uniform(0.15, 0.6))
    return norm(dsp.fade(y, 0.02, 0.05))


@lru_cache(maxsize=None)
def chain_seat(seed=0):
    """The chain's knob seating at the end of its slot: a small hard click."""
    r = rng("cseat", seed)
    y = sfx._hit(r, [1500.0, 2600.0, 4100.0, 6100.0], [0.05, 0.035, 0.02, 0.012], click=1.0)
    th = sfx._thump(n_of(0.06), 400.0, 220.0, 0.004, 0.02)
    y[:len(th)] += 0.4 * th
    return norm(y)


def s06(m, t0):
    S = scene("s06")
    if S is None:
        return
    m.begin(S, "s06", t0)
    L = m.len
    T_BREATH = g(S, "T_BREATH", (0.1, 1.05))
    T_TURN = g(S, "T_TURN", 1.12)
    T_RISE = g(S, "T_RISE", (1.2, 1.9))
    T_DOWN = g(S, "T_DOWN", 2.0)
    T_DOOR = g(S, "T_DOOR", 2.5)
    T_OUT = g(S, "T_OUT", 2.72)
    T_STEPS = g(S, "T_STEPS", (3.0, 3.5, 4.0))
    T_STOP = g(S, "T_STOP", 4.22)
    T_LOOK = g(S, "T_LOOK", 4.5)
    T_SHUT = g(S, "T_SHUT", 3.3)
    T_CHAIN = g(S, "T_CHAIN", 5.0)
    T_SLIDE = g(S, "T_SLIDE", (5.32, 6.02))
    T_HOME = g(S, "T_HOME", 6.02)
    T_WINDOW = g(S, "T_WINDOW", 6.5)
    T_LIFT = g(S, "T_LIFT", (6.68, 7.2))
    T_WIND = g(S, "T_WIND", 7.12)
    T_DUCK = g(S, "T_DUCK", 7.35)
    T_KNEE = g(S, "T_KNEE", 7.96)
    T_LOW = g(S, "T_LOW", 8.5)
    T_STEP_OUT = g(S, "T_STEP_OUT", 8.62)
    T_PLANT = g(S, "T_PLANT", (8.90, 9.22, 9.40))
    T_LOOK_DOWN = g(S, "T_LOOK_DOWN", 9.5)
    feet = call(S, "footfalls_b", default=None)
    feet = sorted(f[1] for f in feet) if feet else [T_OUT + 0.12] + list(T_STEPS) + [T_STOP]

    # her heart all scene long (the score's pulse now), at the tempo the scene's heart cue asks
    # (72 bpm, rising to 112 by the time the chain seats; on the beat if it names none): close
    # in her shots, far under his; it carries over into s07
    def hgain(t):
        return -12.0 if t < T_DOWN else -23.0 if t < T_CHAIN else -10.0 if t < T_WINDOW else -14.0 if t < T_LOW else -17.0
    hc = next((c for c in m.cues if "heart" in c["sfx"].lower() and "bpm0" in c.get("params", {})), None)
    hp = hc["params"] if hc else {}
    bpm0 = float(hp.get("bpm0", 60.0 / BEAT))
    bpm1 = float(hp.get("bpm1", bpm0))
    r0, r1 = (float(v) for v in hp.get("rise", (0.0, T_HOME)))

    def bpm(t):
        return bpm0 + (bpm1 - bpm0) * min(max((t - r0) / max(r1 - r0, 1e-3), 0.0), 1.0)
    t, k = (float(hc["t"]) if hc else 0.0), 0
    while t < L - 0.05:
        dub = round(0.3 - 0.06 * min(max((bpm(t) - 72.0) / 40.0, 0.0), 1.0), 2)
        m.put("music", heart(dub, seed=k % 3), t, hgain(t), label="her heart" if k == 0 else None, hall=-22)
        dt = 60.0 / bpm(t)
        t += 60.0 / bpm(t + 0.5 * dt)
        k += 1

    # A: from the floor, in the dark: her breath, quick; she turns to the window and rises to peek
    m.put("amb", bed("room_tone", T_DOWN, 61), 0.0, -32)
    b = gen("her_breath", 0.32, 0.32 + T_BREATH[1] - T_BREATH[0] + 0.2, fade=0.04)
    m.put("vox", near(dsp.sos(b, "lowpass", 5000.0, 2), 6), T_BREATH[0] - 0.03, -12, label="her breath",
          sync=T_BREATH[0], align=None)
    m.put("efx", rustle(0.4, 61, 250.0, 3000.0), T_TURN, -23, label="she turns")
    m.put("efx", rustle(T_RISE[1] - T_RISE[0], 62, 200.0, 2500.0), T_RISE[0], -25, label="she rises to the sill")
    m.put("efx", creak(0.3, 63), T_RISE[0] + 0.25, -31)
    m.put("music", harmonic(note(HER + 12), T_DOWN - T_RISE[0] + 0.05, 0.5, seed=61, attack=0.5, release=0.2), T_RISE[0],
          -31, pan=-0.1)

    # B: straight down, through her glass, four floors: his door, his steps, his door to; he
    # looks up (his low A)
    def down(x, lp=1400.0, s=0):
        return glass(dsp.reverb(mono(x), "street", wet_db=-5.0, seed=s).mean(axis=1), lp=lp, wet_db=-14.0, seed=s)
    m.put("amb", bed("city_far", L - T_DOWN, 62), T_DOWN, -37)
    do = down(cut(fx("door_open", seed=64), 0.7, 0.15), 1500.0, 1)
    m.put("efx", do, T_DOOR - onset_at(do), -17, pan=0.25, label="his door opens", sync=T_DOOR)
    hinge = down(creak(0.4, 64), 1600.0, 4)
    m.put("efx", hinge, T_SHUT - onset_at(hinge), -26, pan=0.25, label="his door swings to", sync=T_SHUT)
    dc = down(fx("door_close", seed=65), 1300.0, 2)
    m.put("efx", dc, T_SHUT + 0.45 - peak_at(dc), -21, pan=0.25, label="his door shuts: a soft far thud",
          sync=T_SHUT + 0.45, align="peak")
    db_ = bank("stairs_down")
    for j, ft in enumerate(feet):
        x = down(db_[(2 * j + 1) % len(db_)], 1700.0, 3 + j)
        m.put("feet", x, ft - STEP_PRE, -18 + 0.8 * j - (5.0 if j == len(feet) - 1 else 0.0), pan=0.2 - 0.08 * j,
              label="his step", sync=ft)
    m.put("efx", glass_tick(5), T_LOOK + 0.05, -34, pan=0.15)
    gp = near(dsp.sos(gen("gasp_a", 0.0, 0.62, fade=0.01), "lowpass", 4000.0, 2), 8)
    m.put("vox", gp, T_LOOK - onset_at(gp), -19, pan=-0.05, label="her breath catches", sync=T_LOOK)
    m.put("music", bowed_line([(0.0, HIS)], T_CHAIN - T_LOOK + 0.3, 0.8, seed=64, octaves=(0, 1), attack=0.25,
                              release=0.5), T_LOOK, -15, pan=0.15, label="he looks up: his low A")

    # C: the chain, close: it shivers in her fingers, slides along its track (a hitch), seats
    m.put("amb", bed("room_tone", T_WINDOW - T_CHAIN, 66), T_CHAIN, -31)
    t_shiv = T_SLIDE[0] - 0.12
    cs = chain_shiver(max(t_shiv - T_CHAIN, 0.05), 66)
    m.put("efx", cs, T_CHAIN - onset_at(cs), -28, label="the chain in her hand", sync=T_CHAIN)
    cs = chain_shiver(0.16, 69)
    m.put("efx", cs, t_shiv - onset_at(cs), -20, label="the links shiver as the knob comes up", sync=t_shiv)
    m.put("efx", clink(5, 3600.0), T_SLIDE[0], -24, label="the knob finds the slot")
    m.put("efx", chain_slide(T_HOME - T_SLIDE[0] - 0.04, catch=0.24, seed=67), T_SLIDE[0] + 0.04, -15,
          label="the chain slides along its track")
    m.put("efx", chain_seat(68), T_HOME, -12, label="the chain seats")
    m.put("vox", near(dsp.sos(gen("her_breath", 1.35, 1.66, fade=0.03), "lowpass", 4500.0, 2), 7), T_HOME + 0.18, -19)

    # D: the window: the sash goes up, the night comes in (wind, the curtain); she ducks out
    m.put("efx", sash(0.1, 1), T_LIFT[0], -14, label="the sash sticks: a wooden knock")
    m.put("efx", sash(round(T_LIFT[1] - T_LIFT[0] - 0.16, 3), 2, stop=False), T_LIFT[0] + 0.16, -13,
          label="the sash grinds up")
    m.put("efx", dsp.sos(door_thud(75, 0.6).mean(axis=1), "lowpass", 1100.0, 2), T_LIFT[1], -13,
          label="the sash goes home at the top")
    tt = np.arange(n_of(L - T_WINDOW)) / SR + T_WINDOW
    amp = np.interp(tt, [T_WINDOW, T_WIND - 0.06, T_WIND + 0.35, T_LOW, T_LOW + 0.05, L], [0.0, 0.03, 0.75, 0.55, 0.8, 0.9])
    inside = (tt < T_LOW).astype(np.float64)
    m.put("amb", wind_bed(amp, 61), T_WINDOW, -16, label="the night comes in: wind", sync=T_WIND, align=None)
    m.put("amb", curtain(amp * inside, 62), T_WINDOW, -22)
    m.put("efx", rustle(0.5, 69, 200.0, 2800.0), T_DUCK, -21, label="she ducks into the opening")
    m.put("efx", dsp.sos(door_thud(70, 0.3).mean(axis=1), "lowpass", 900.0, 2), T_KNEE - 0.04, -25,
          label="her knee on the sill: a soft knock")
    m.put("vox", near(dsp.sos(gen("her_breath", 1.35, 1.66, fade=0.03), "lowpass", 4500.0, 2), 9), T_KNEE + 0.08, -18)

    # E: the low angle from the street: her leg over the sill, her weight onto the iron grating
    # (it creaks; it rings under her other foot), a careful step to the rail; she looks down,
    # holding her breath
    m.put("efx", rustle(0.3, 71, 250.0, 2600.0), T_STEP_OUT, -24, label="her leg over the sill")
    m.put("feet", iron_step(71), T_PLANT[0], -17, label="her weight onto the grating")
    m.put("efx", creak(0.6, 72, iron=True), T_PLANT[0] + 0.03, -18)
    m.put("feet", iron_step(73), T_PLANT[1], -24, label="the grating rings under her other foot")
    m.put("efx", rung(74), T_PLANT[1] + 0.01, -31)
    m.put("feet", iron_step(76), T_PLANT[2], -27, label="a careful step to the rail")
    br = dsp.sos(gen("her_breath", 4.0, 4.26, fade=0.02), "lowpass", 4500.0, 2)
    m.put("vox", br, T_LOOK_DOWN - 0.04, -19, label="she holds her breath", sync=T_LOOK_DOWN, align=None)
    m.put("efx", creak(0.5, 74, iron=True), T_LOOK_DOWN + 0.12, -28)
    m.put("music", harmonic(note(HER + 12), L - T_LOW + 0.2, 0.5, seed=62, attack=0.8, release=0.4), T_LOW, -30, pan=0.2)
    m.end()


# ============================================================================ s07 CROSSING
def s07(m, t0):
    S = scene("s07")
    if S is None:
        return
    m.begin(S, "s07", t0)
    L = m.len
    T_STOP = g(S, "T_STOP", 1.9)
    T_LISTEN = g(S, "T_LISTEN", 2.1)
    T_HORN = g(S, "T_HORN", 3.6)
    T_IN = g(S, "T_IN", 4.0)
    T_LADDER = g(S, "T_LADDER", 4.5)
    T_LENS2 = g(S, "T_LENS2", (7.8, 9.8))
    T_X = g(S, "T_X", 12.0)
    T_RINGS = g(S, "T_RINGS", 12.4)
    PAVE = g(S, "PAVE", None)
    P = call(S, "paths", default=None)
    if P is None:
        warn("s07: no paths(): footsteps spaced from the bible")
        P = {"his": (None, [0.1 + 0.257 * i for i in range(8)] + [T_IN + 0.1 * i for i in range(10)] +
                     [5.0 + 0.2625 * i for i in range(25)], {1: 5.0, 2: 7.1, 3: 9.2, 4: 11.3}),
             "hers": (None, [0.1 + 0.106 * i for i in range(18)] + [5.5 + 0.125 * i for i in range(9)] +
                      [7.2 + 0.134 * i for i in range(31)], {1: 7.2, 2: 8.24, 3: 9.28, 4: 10.31, 5: 11.35})}
    m.put("amb", bed("city_far", L, 7), 0.0, -36)
    race0 = T_LADDER + 0.4
    hpts, htimes, hland = P["his"]
    rpts, rtimes, rland = P["hers"]

    def landings(land, t):
        return sum(1 for v in land.values() if t >= v - 1e-6)

    # his steps: the red dots, slow, heavy, careful (the street, her lobby, up her stairs)
    down, up = bank("stairs_down"), bank("stairs_up")
    i_race = 0
    for i, t in enumerate(htimes):
        on_pave = hpts is not None and PAVE is not None and abs(hpts[i][1] - PAVE) < 0.5
        s = down[i % len(down)] if on_pave or t < T_IN else up[(i * 3) % len(up)]
        m.put("feet", dsp.sos(s, "lowpass", 1700.0, 2), t - STEP_PRE, -14, pan=-0.3, label="his step", sync=t)
        if t >= race0 - 0.15:                   # the canon: his voice, low, a semitone up each landing
            semis = HIS + landings(hland, t) + PSYCHO[i_race % 4]
            m.put("music", pizz(note(semis), 0.95, seed=i), t, -10, pan=-0.35, hall=-19)
            i_race += 1
    # her steps: the paper dots, quick and light: iron on the fire escape and the ladder, the
    # street running, his stairs
    first_pave = None
    if rpts is not None and PAVE is not None:
        first_pave = next((rtimes[i] for i, p in enumerate(rpts) if abs(p[1] - PAVE) < 0.5), None)
    her, runs = bank("her_steps", -28.0), bank("street_run", -14.0, 0.2)
    j_race = 0
    for j, t in enumerate(rtimes):
        iron = t < (first_pave if first_pave is not None else T_LADDER + 0.95) - 1e-6
        if iron and t > T_LADDER:
            m.put("feet", rung(j), t, -21, pan=0.3, label="her step", sync=t)
        elif iron:
            m.put("feet", iron_step(j), t, -21, pan=0.3, label="her step", sync=t)
            m.put("feet", her[j % len(her)], t - STEP_PRE, -27, pan=0.3)
        elif t < (rland.get(1, 99.0) - 0.15):
            m.put("feet", runs[j % len(runs)] if t < T_LADDER + 2.0 else her[j % len(her)], t - STEP_PRE, -21, pan=0.3,
                  label="her step", sync=t)
        else:
            m.put("feet", dsp.sos(up[(j * 5) % len(up)], "highpass", 300.0, 2), t - STEP_PRE, -23, pan=0.3,
                  label="her step", sync=t)
        if race0 - 0.15 <= t <= T_X - 0.3:       # the canon: her voice, high, mirrored: falling
            semis = HER - 12 - landings(rland, t) + (11, 7, 3, 0)[j_race % 4]
            m.put("music", pluck(note(semis), 0.7, seed=j, damp=0.08), t, -15, pan=0.35, hall=-21)
            j_race += 1
    m.mark(race0, "the race: a plucked canon")

    # the near miss: both stop; she holds her breath; he listens (her heart in the rings he
    # listens with); a far horn lets them go
    m.put("vox", dsp.sos(gen("her_breath", 4.0, 4.26, fade=0.02), "lowpass", 5000.0, 2), T_STOP, -15, pan=0.3,
          label="held breath")
    rings = [T_LISTEN + 0.55 * j for j in range(3) if T_LISTEN + 0.55 * j < T_HORN]
    for k, t in enumerate(rings):
        m.put("music", heart(0.26, seed=k), t, -11, label="heartbeat (her)" if k == 0 else None, hall=-22)
    m.put("music", strings((HIS,), T_HORN - T_STOP + 0.3, 0.6, seed=12, octaves=(0, 1), attack=0.8, release=0.5), T_STOP,
          -24)
    m.put("efx", horn_far(1), T_HORN, -20, pan=0.8, label="far horn")
    m.put("vox", dsp.sos(gen("her_breath", 1.4, 1.65, fade=0.03), "lowpass", 4000.0, 2), T_HORN + 0.15, -20, pan=0.3)
    sd = dsp.sos(cut(fx("door_open", seed=9), 0.6, 0.15), "lowpass", 2000.0, 2)
    m.put("efx", sd, T_IN - onset_at(sd), -18, pan=-0.35, label="street door", sync=T_IN)
    m.put("efx", dsp.sos(fx("door_close", seed=10), "lowpass", 1800.0, 2), T_IN + 0.85, -19, pan=-0.35)
    m.put("efx", ladder(1), T_LADDER, -12, pan=0.25, label="drop ladder")

    # Vertigo under the stairwell callout: two string lines swirling in contrary motion
    a, b = T_LENS2
    up_line = (12, 15, 19, 23, 24, 23, 19, 15)
    k = 0
    m.mark(a, "Vertigo swirl")
    while a + k / 6.0 < b - 0.05:
        t = a + k / 6.0
        sw = math.sin(math.pi * (t - a) / (b - a))
        for v, s in enumerate((up_line[k % 8], 36 - up_line[k % 8])):
            m.put("music", chord((s,), 0.3, 0.55 * sw + 0.1, seed=k % 4 + v, octave=0, stacc=False, spread=(0,)), t,
                  -20, pan=(-0.3, 0.3)[v])
        k += 1

    # the X: her note falls to his, his rises to hers; then a ring round each, her heart
    m.put("music", bowed_line([(0.0, 24), (0.45, HIS + 12), (1.0, HIS + 12)], 0.9, 0.8, seed=13, octaves=(0,), attack=0.03),
          T_X, -11, pan=0.3, label="the X: hers falls")
    m.put("music", bowed_line([(0.0, HIS + 12), (0.45, 24), (1.0, 24)], 0.9, 0.8, seed=14, octaves=(0,), attack=0.03),
          T_X, -11, pan=-0.3)
    m.put("music", strings((0, 3, 7, 11), L - T_RINGS + 0.2, 0.7, seed=15, octaves=(-1, 0), attack=0.3, release=0.8),
          T_RINGS, -17, label="the rings: held chord")
    beat = 60.0 / 132.0
    k = int(math.ceil(T_RINGS / beat - 1e-6))
    while k * beat < L - 0.05:
        m.put("music", heart(0.26, seed=k % 3), k * beat, -11, hall=-22)
        k += 1
    m.end()


# ============================================================================ s08 DOOR
def s08(m, t0):
    S = scene("s08")
    if S is None:
        return
    m.begin(S, "s08", t0)
    L = m.len
    T_STEPS = g(S, "T_STEPS", (0.8, 1.6, 2.4))
    T_FEET = g(S, "T_FEET", 3.2)
    T_KNOB = g(S, "T_KNOB", (4.0, 5.0))
    SNAPS = g(S, "SNAPS", (T_KNOB[0] + 2 / 12.0, T_KNOB[1] + 2 / 12.0, T_KNOB[1] + 5 / 12.0, T_KNOB[1] + 7 / 12.0))
    T_KEY = g(S, "T_KEY", 6.0)
    T_FACE = g(S, "T_FACE", 6.95)
    T_OPEN = g(S, "T_OPEN", 7.35)
    T_DIVE = g(S, "T_DIVE", 8.45)
    T_POV = g(S, "T_POV", 9.0)
    T_GUST = g(S, "T_GUST", 11.5)
    T_BACK = g(S, "T_BACK", 12.5)
    T_NARROW = g(S, "T_NARROW", 12.75)

    def wind_at(t):
        w = call(S, "wind", t, default=None)
        return w[0] if w is not None else 0.32 + 0.09 * math.sin(t * 1.7) + 0.1 * math.sin(t * 0.63 + 1.0)
    amp = sample_fn(wind_at, 0.0, L)
    tt = tax(len(amp))
    # her empty room, dark, the window open: wind and the curtain; through the keyhole it is
    # closer (the POV), then back outside his eye
    near_g = np.where((tt >= T_POV) & (tt < T_BACK), 1.0, 0.45)
    near_g = dsp.onepole_lp(near_g, 3.0)
    m.put("amb", wind_bed(amp * near_g, 8), 0.0, -17, label="wind at her window", align=None)
    m.put("amb", curtain(amp * near_g, 8), 0.0, -24)
    m.put("amb", bed("room_tone", L, 81), 0.0, -32)
    # the lamp's pull cord, swinging in the wind: its bead ticks the glass at the end of each swing
    sw_ts = np.arange(T_POV, T_BACK, 1.0 / 240.0)
    sw = []
    for t in sw_ts:
        w = call(S, "wind", math.floor(t * 12.0) / 12.0, default=(wind_at(t), 0.0))
        tw = math.floor(t * 12.0) / 12.0
        sw.append(w[0] * (0.6 * math.sin(tw * 3.1) + 0.4 * math.sin(tw * 5.3 + 1.0)) + w[1] * 0.8 * math.sin(tw * 6.4))
    sw = np.array(sw)
    k = 0
    for i in range(1, len(sw) - 1):
        if abs(sw[i]) > 0.3 and abs(sw[i]) >= abs(sw[i - 1]) and abs(sw[i]) > abs(sw[i + 1]) and sw[i] != sw[i - 1]:
            m.put("efx", bead(k), float(sw_ts[i]), -27, pan=0.1 * np.sign(sw[i]), label="cord ticks" if k == 0 else None)
            k += 1
    if k == 0:
        m.mark(T_POV, "inside")

    # his steps on the landing, nearer each time; he stops at her door; his breath
    up = bank("stairs_up")
    for j, t in enumerate(T_STEPS):
        m.put("feet", dsp.sos(up[(j + 4) % len(up)], "lowpass", 1100.0 + 500.0 * j, 2), t - STEP_PRE, -15 + 2.5 * j,
              label="his step", sync=t)
    for j in range(2):
        m.put("feet", dsp.sos(up[(j + 1) % len(up)], "lowpass", 2600.0, 2), T_FEET + 0.14 * j - STEP_PRE, -9 - 3.0 * j,
              label="he stops" if j == 0 else None, sync=T_FEET + 0.14 * j)
    hv = gen("his_breath", 0.9, 0.9 + T_KNOB[0] - (T_FEET + 0.3), fade=0.08)
    m.put("vox", dsp.sos(hv, "lowpass", 1500.0, 2), T_FEET + 0.3, -10)
    for j in range(3):
        m.put("music", heart(0.26, seed=j), T_FEET + 0.15 + 0.55 * j, -19, hall=-22)
    # the handle tried, twice; the door jolts open on the chain, slammed against it twice more
    for (a0, b0), t in zip([(0.06, 0.9), (1.8, 2.55)], T_KNOB):
        hx = gen("handle", a0, b0, fade=0.01, norm=-1.0)
        m.put("efx", hx, t - onset_at(hx), -8, label="the handle", sync=t)
    for j, t in enumerate(SNAPS):
        m.put("efx", chain_taut(j, 1.0 if j else 0.7), t, -7 if j else -9, pan=0.2, label="chain taut")
    # into the keyhole: a low swell; his face at it: the light goes, his breath; his eye opens
    m.put("music", strings((HIS, HIS + 1, HIS + 13), T_POV - T_KEY, 0.8, seed=21, octaves=(0, 1), attack=2.2, release=0.5),
          T_KEY, -17, label="keyhole: low swell")
    m.put("music", fx("reverse_swell", dur=T_POV - T_KEY, seed=22), T_KEY, -22)
    m.put("efx", switch(8), T_FACE, -28, label="his face: the light goes")
    hv = gen("his_breath", 1.2, 2.9, fade=0.08)
    m.put("vox", dsp.sos(hv, "lowpass", 2500.0, 2), T_FACE + 0.05, -11)
    m.put("efx", fx("clock_tick", seed=17), T_OPEN, -16, label="eye opens: tick")
    m.put("efx", rush(T_POV - T_DIVE, seed=3, peak=0.95), T_DIVE, -14, label="into his eye", align=None)
    # inside: a gust, the curtain cracks
    m.put("amb", fx("laundry_flap", seed=4), T_GUST - 0.25, -14, pan=-0.2, label="gust: curtain cracks", sync=T_GUST,
          align=None)
    m.put("amb", bed("wind_gust", 1.6, 5), T_GUST - 0.2, -19)
    # back on his eye: a low stinger; it narrows: a held low cluster
    m.put("music", stinger(11, semis=-16), T_BACK, -10, label="low stinger")
    m.put("music", strings((HIS, HIS + 1, -12), L - T_NARROW + 0.3, 0.8, seed=23, octaves=(0,), attack=0.3, release=0.8),
          T_NARROW, -17, label="held low cluster")
    m.end()


# ============================================================================ s09 CALL
def s09(m, t0):
    S = scene("s09")
    if S is None:
        return
    m.begin(S, "s09", t0)
    L = m.len
    T_DOOR = g(S, "T_DOOR", 0.35)
    T_OPEN = g(S, "T_OPEN", 1.1)
    T_SEE = g(S, "T_SEE", 1.15)
    T_HANDS = g(S, "T_HANDS", 2.0)
    T_DIAL = g(S, "T_DIAL", 5.0)
    T_EAR = g(S, "T_EAR", 10.0)
    T_REACH = g(S, "T_REACH", T_HANDS + 0.25)
    T_TOUCH = g(S, "T_TOUCH", T_HANDS + 1.0)
    T_TWITCH = g(S, "T_TWITCH", T_HANDS + 1.5)
    T_CLOSE = g(S, "T_CLOSE", T_HANDS + 1.9)
    T_PULSE = g(S, "T_PULSE", T_HANDS + 2.25)
    # the dial: the module's (digit, finger in, wind from, at the stop, let go) and its pulses;
    # until it has them, the bible's 9-1-1 let go on the beat
    DIGITS = g(S, "DIGITS", None)
    if DIGITS and not isinstance(DIGITS[0], (int, str)):
        DIGITS = [(int(d[0]) % 10, *(float(v) for v in d[1:5])) for d in DIGITS]
    else:
        T_RELEASE = g(S, "T_RELEASE", (T_DIAL + 1.0, T_DIAL + 2.5, T_DIAL + 3.5))     # she lets go of 9, of 1, of 1
        DIGITS = [(int(d) % 10, rel - dial_wind(int(d)) - 0.2, rel - dial_wind(int(d)), rel - 0.06, rel)
                  for d, rel in zip(DIGITS or (9, 1, 1), T_RELEASE)]
    D_RATE = g(S, "D_RATE", 300.0)
    PULSES = call(S, "pulse_times", default=None)
    if not PULSES or len(PULSES) != len(DIGITS):
        PULSES = [[d[4] + (15.0 + 30.0 * i) / D_RATE for i in range(d[0] or 10)] for d in DIGITS]
    T_WITHDRAW = g(S, "T_WITHDRAW", DIGITS[-1][4] + 0.08)
    # the bible's beats the draft has not set yet (placed on the beat)
    T_RINGS = g(S, "T_RINGS", (T_EAR + 0.25, T_EAR + 1.0))
    T_ANSWER = g(S, "T_ANSWER", T_EAR + 1.5)

    # his room, amber; the door creaks open on the landing's light
    m.put("amb", bed("room_tone", L, 91), 0.0, -30)
    cr = fx("door_creak", seed=91)
    cr = dsp.fade(cr[: n_of(T_OPEN - T_DOOR + 0.25)], 0.01, 0.15)
    m.put("efx", cr, T_DOOR - 0.06, -12, pan=-0.35, label="his door creaks open", sync=T_DOOR)
    sway = [t for t in np.arange(T_OPEN, T_HANDS, 1.0 / 48.0)
            if abs(call(S, "lamp_sway", t, default=0.0)) > 0.0
            and abs(call(S, "lamp_sway", t, default=0.0)) >= abs(call(S, "lamp_sway", t - 1 / 48.0, default=0.0))
            and abs(call(S, "lamp_sway", t, default=0.0)) > abs(call(S, "lamp_sway", t + 1 / 48.0, default=0.0))]
    for j, t in enumerate(sway):
        m.put("efx", creak(0.25, 92 + j, iron=True), float(t) - 0.1, -34, pan=0.1)
    m.put("vox", gen("gasp_a", 0.0, 0.62, fade=0.01), T_SEE, -11, pan=-0.3, label="her breath catches", key=True)
    m.put("music", strings((HIS, HIS + 1), T_EAR - T_SEE, 0.7, seed=91, octaves=(0, 1), attack=1.2, release=0.6,
                           env=[(0.0, 0.5), (T_DIAL - T_SEE, 0.8), (T_EAR - T_SEE, 1.0)]), T_SEE + 0.1, -21)

    # the hands: hers reaches in; the victim's fingers twitch, close on hers: alive (one faint ring
    # from the wrist, a faint breath); her heart, on the beat, from here to the ringing
    k = 0
    while T_HANDS + k * BEAT < L - 0.05:
        t = T_HANDS + k * BEAT
        m.put("music", heart(0.24, seed=k % 3), t, -17 if t < T_EAR else -14, hall=-22,
              label="her heart" if k == 0 else None)
        k += 1
    m.put("efx", rustle(0.45, 93, 250.0, 2500.0), T_REACH, -26, label="her hand comes in")
    m.put("efx", rustle(0.2, 94, 400.0, 3000.0), T_TOUCH, -31)
    m.put("efx", rustle(0.18, 95, 300.0, 2500.0), T_TWITCH, -27, label="the victim's fingers twitch")
    m.put("efx", rustle(0.25, 96, 250.0, 2200.0), T_CLOSE, -25, label="they close on hers")
    m.put("music", harp(note(HER), 0.5, seed=5), T_CLOSE, -24, pan=-0.2)
    m.put("vox", dsp.sos(gen("her_breath", 1.35, 1.7, fade=0.04), "lowpass", 2000.0, 2), T_PULSE - 0.05, -27,
          label="a faint breath", sync=T_PULSE, align=None)
    m.put("music", heart(0.24, seed=3, dub_amp=0.4) * 0.5, T_PULSE, -16, hall=-20, pan=0.2)
    m.put("music", harmonic(note(HER + 12), 1.2, 0.5, seed=92, attack=0.05, release=0.8), T_PULSE, -27, pan=-0.2)

    # the dial, from above, close: 9, then 1, then 1, each wound round and let go; a relay click
    # for each dot the tally lands
    m.put("efx", receiver(1), T_DIAL - 0.35, -20, pan=-0.1)
    for j, ((d, t_in, w0, w1, rel), ps) in enumerate(zip(DIGITS, PULSES)):
        x = dial_turn(d, t_in, w0, w1, rel, tuple(float(v) for v in ps), rate=D_RATE, seed=j)
        m.put("efx", x, t_in, -10, pan=-0.05, label=f"dial {d}: let go", sync=rel, align=None)
        for tp in ps:
            m.mark(float(tp), f"dial {d}: pulse")
    m.put("efx", rustle(0.3, 97, 250.0, 2400.0), T_WITHDRAW, -29, label="her hand goes")
    last = max(float(PULSES[-1][-1]), DIGITS[-1][4] + 0.15)
    m.put("efx", receiver(3) * 0.4, last + 0.45, -26, label="the line connects")

    # the receiver at her ear: it rings twice in the earpiece; the ringing stops: a click
    for j, t in enumerate(T_RINGS):
        d = min(0.55, (T_RINGS[j + 1] - t - 0.15) if j + 1 < len(T_RINGS) else (T_ANSWER - t - 0.05))
        x = ringback(1, on=d, off=0.0)
        m.put("efx", dsp.reverb(x, "car", wet_db=-14.0, seed=j).mean(axis=1), t, -15, pan=-0.2, label="ringback")
    m.put("efx", receiver(4), T_ANSWER, -15, pan=-0.2, label="the ringing stops: click")
    m.put("music", fx("reverse_swell", dur=L - T_ANSWER + 0.1, seed=94), T_ANSWER, -24)
    m.end()


# ============================================================================ s10 OPPOSITE
NEIGHBOURS = (31, 27, 26, 27, 24, 23, 24)           # her theme's first notes: one per window


def s10(m, t0):
    S = scene("s10")
    if S is None:
        return
    m.begin(S, "s10", t0)
    L = m.len
    T_KICK = g(S, "T_KICK", 0.1)
    T_BURST = g(S, "T_BURST", 0.5)
    T_ROOM = g(S, "T_ROOM", 2.5)
    T_AT_WIN = g(S, "T_AT_WIN", 5.3)
    T_OTS = g(S, "T_OTS", 5.5)
    T_HER_LOOK = g(S, "T_HER_LOOK", 6.0)
    T_HIS_LOOK = g(S, "T_HIS_LOOK", 6.4)
    T_MEET = g(S, "T_MEET", 6.82)
    T_LOWER = g(S, "T_LOWER", 8.15)
    T_SWEEP = g(S, "T_SWEEP", 8.85)
    T_SIREN = g(S, "T_SIREN", 9.5)
    T_WAKE = g(S, "T_WAKE", 12.5)
    T_LIGHTS = g(S, "T_LIGHTS", tuple(12.75 + 0.25 * i for i in range(7)))
    WAKE = g(S, "WAKE_ORDER", None)
    HER_B = g(S, "HER_B", None)
    T_CITY = g(S, "T_CITY", (13.0, 15.0))
    T_CITY_LOOKS = g(S, "T_CITY_LOOKS", 14.4)
    T_RING = g(S, "T_RING", 16.0)
    T_PULL = g(S, "T_PULL", (16.5, 19.5))
    THRESH = g(S, "THRESH", 1250.0)

    # the kick: the door jumps on its chain; the burst: the chain snaps, its links fly and skitter
    m.put("efx", door_thud(1, 0.8), T_KICK, -7, label="kick")
    m.put("efx", chain_taut(5, 1.0), T_KICK + 0.005, -11)
    m.put("efx", fx("impact", seed=12, size=0.85), T_BURST, -3, label="door burst")
    m.put("efx", door_thud(2, 1.4), T_BURST, -8)
    m.put("efx", splinter(3), T_BURST, -10)
    m.put("efx", chain_snap(4), T_BURST + 0.004, -8, pan=0.35)
    m.put("efx", door_thud(6, 0.6), T_BURST + 0.3, -17, pan=-0.4)
    for i in range(9):
        lk = call(S, "_link", i, default=None)
        if lk is None:
            t_land, x_land, near_k = 0.75 + 0.02 * i, 300.0 + 60.0 * i, 0.5
        else:
            x0, y0, vx, vy, floor_y, t_land = lk
            x_land = x0 + vx * t_land
            near_k = float(np.clip((floor_y - THRESH) / (1820.0 - THRESH), 0, 1))
        pan = float(np.clip((x_land - 540.0) / 600.0, -0.8, 0.8))
        for k in range(4):
            t = T_BURST + t_land + 0.16 * k
            m.put("efx", link_tink(10 * i + k), t, -21 + 6.0 * near_k - 8.3 * k, pan=pan,
                  label="link lands" if k == 0 else None)
        m.put("efx", skitter(0.3, i), T_BURST + t_land + 0.02, -31 + 6.0 * near_k, pan=pan)

    # the empty room: wind and the curtain (her open window); his steps in, a stop, to the window
    def wind_at(t):
        rm = call(S, "room_at", t, default=None)
        return getattr(rm, "wind", 0.85 + 0.15 * math.sin(2.0 * math.pi * 0.4 * t))
    amp = sample_fn(wind_at, 0.0, T_OTS + 0.6, step=0.02)
    tt = tax(len(amp))
    amp = amp * np.interp(tt, [0.0, T_BURST, T_BURST + 0.4, T_OTS - 0.2, T_OTS + 0.6], [0.25, 0.25, 0.55, 0.55, 0.0])
    m.put("amb", wind_bed(amp, 10), 0.0, -14, label="the empty room: wind", sync=T_ROOM, align=None)
    m.put("amb", curtain(amp, 10), 0.0, -20)
    walk = None
    try:
        if not isinstance(S, Stub) and hasattr(S, "his_walk"):
            walk = [t for t in mocap_footfalls(S.his_walk(), T_ROOM - 0.1, T_AT_WIN + 0.3) if t >= T_ROOM - 0.05]
    except Exception as e:
        warn(f"s10: his footfalls ({e}): spaced from T_ROOM")
    walk = walk or [T_ROOM + 0.1 + 0.5 * j for j in range(5)]
    up = bank("stairs_up")
    for j, ft in enumerate(walk):
        m.put("feet", dsp.sos(up[(j * 3 + 1) % len(up)], "lowpass", 2400.0, 2), ft - STEP_PRE, -14, pan=-0.2 + 0.1 * j,
              label="his step", sync=ft)

    # over his shoulder: the street. Her look: a high B-flat; his: a low A; they clash in a chime
    city = bed("city_far", L - T_OTS + 1.0, 10)
    m.put("amb", city * dsp.env_bp_db([(0.0, -40), (0.6, 0), (len(city) / SR, 0)], len(city))[:, None], T_OTS, -32)
    hl = T_SIREN - T_HER_LOOK
    m.put("music", harmonic(note(HER), hl, 0.85, seed=21, attack=0.3, release=1.2, vib=0.003), T_HER_LOOK, -20, pan=-0.2,
          label="her look: high B-flat")
    m.put("music", harmonic(note(HER - 12), hl, 0.5, seed=22, attack=0.5, release=1.2), T_HER_LOOK, -26, pan=-0.2)
    sl = T_SIREN - T_HIS_LOOK
    m.put("music", bowed_line([(0.0, HIS)], sl, 0.9, seed=23, octaves=(0, 1), attack=0.25, release=1.0,
                              env=[(0.0, 0.6), (max(T_MEET - T_HIS_LOOK, 0.1), 1.0), (sl, 0.85)]), T_HIS_LOOK, -16,
          pan=0.2, label="his look: low A")
    clash = chime(note(HER)) + 0.8 * chime(note(HER - 1), 1)
    m.put("music", clash, T_MEET, -15, label="the looks meet: chime")
    m.put("music", piano(note(HIS), dur=3.0, vel=0.9, seed=7), T_MEET, -17)
    m.put("efx", cord_rattle(1), T_LOWER, -21, pan=-0.2, label="receiver cord")

    # the sirens: one far off, rising; then two cars, nearer and nearer (they fade far in s11)
    far = siren(T_SIREN - T_SWEEP + 1.0, seed=1, period=4.4)
    far = dsp.sos(far, "lowpass", 1800.0, 2) * dsp.env_bp_db([(0.0, -30), (T_SIREN - T_SWEEP, -6), (len(far) / SR, -40)],
                                                              len(far))
    m.put("efx", rev(far, -2.0, 1, "street"), T_SWEEP, -21, pan=0.5, label="far siren", align=None)
    for v, (period, lo, hi, pan, dt) in enumerate(((3.6, 640.0, 1420.0, 0.45, 0.0), (4.3, 600.0, 1330.0, -0.4, 0.9))):
        d = L - T_SIREN - dt + 0.3
        x = siren(d, seed=2 + v, period=period, lo=lo, hi=hi)
        tt = tax(len(x))
        x = dsp.tv_lowpass(x, 1200.0 + 4000.0 * np.clip((tt) / max(T_RING - T_SIREN, 1.0), 0, 1), q=0.7, block=64)
        x = x * dsp.env_bp_db([(0.0, -40), (0.4, -16), (T_WAKE - T_SIREN - dt, -4), (T_RING - T_SIREN - dt, -4),
                               (T_PULL[0] - T_SIREN - dt, -10), (d - 0.3, -12), (d, -40)], len(x))
        m.put("efx", rev(x, -6.0, 2 + v, "street"), T_SIREN + dt, -20, pan=pan, label="sirens" if v == 0 else None,
              align=None)
    # under them, up both facades: the Psycho chord trembling, growing to the neighbours' lights
    tw = T_LIGHTS[0] - T_SIREN
    tr = tremolo(PSYCHO, tw + 0.2, 0.7, seed=38, octave=1)
    m.put("music", tr * dsp.env_bp([(0.0, 0.25), (tw, 1.0), (tw + 0.2, 0.0)], len(tr)), T_SIREN, -20,
          label="sirens: tremolo", align=None)
    m.put("music", bowed_line([(0.0, HIS)], tw, 0.7, seed=39, octaves=(0, 1), attack=0.8, release=0.3), T_SIREN, -22)

    # the section: the neighbours wake: her theme plucked, one note per window
    for j, t in enumerate(T_LIGHTS):
        side = 0.0
        if WAKE is not None and HER_B is not None and j < len(WAKE):
            side = -0.45 if WAKE[j][0] is HER_B else 0.45
        m.put("music", harp(note(NEIGHBOURS[j % len(NEIGHBOURS)]), 0.8, seed=30 + j), t, -9, pan=side,
              label="window lights")
        m.put("efx", switch(20 + j), t - 0.01, -31, pan=side)
    r = rng("city-lights")
    for j in range(10):                                       # the far city lights up: a shimmer
        t = T_CITY[0] + (T_CITY[1] - T_CITY[0]) * j / 10.0 + r.uniform(0, 0.1)
        m.put("music", celesta(note(int(r.choice((36, 39, 43, 46, 48)))), 0.4, seed=j), t, -25, pan=r.uniform(-0.7, 0.7))
    # the city's looks fly: a rising swell into the ring
    sw = T_RING - T_CITY_LOOKS
    m.put("music", bowed_line([(0.0, 12), (sw, 23)], sw, 0.8, seed=31, octaves=(0, 1), attack=sw * 0.8, release=0.05),
          T_CITY_LOOKS, -15, label="the city's looks: swell")
    m.put("music", bowed_line([(0.0, 0), (sw, 11)], sw, 0.8, seed=32, octaves=(-1, 0), attack=sw * 0.8, release=0.05),
          T_CITY_LOOKS, -17)
    m.put("music", fx("reverse_swell", dur=sw, seed=33), T_CITY_LOOKS, -15)
    # the red ring: the marker squeak, a stab (the last minor)
    m.put("efx", squeak(0.4, 9), T_RING, -11, pan=0.3, label="red ring: squeak")
    m.put("music", stab(3, octave=0), T_RING, -5, label="stab")
    m.put("music", shrieks(n_stabs=1, f0=1318.5, seed=34), T_RING, -16)
    m.put("music", tremolo((0, 3, 7), T_PULL[0] - T_RING + 0.15, 0.6, seed=35, octave=1), T_RING + 0.1, -16)
    # the pull back: the strings resolve. D-flat rises to D, his A to B-flat: B-flat major
    d = L - T_PULL[0]
    env = [(0.0, 0.55), (T_PULL[1] - T_PULL[0], 1.0), (d, 1.0)]
    m.put("music", strings((-12, 0, 4, 7, 12, 16), d, 0.9, seed=36, octaves=(0, 1), attack=0.35, release=0.8, env=env),
          T_PULL[0], -7, label="resolution: B-flat major")
    m.put("music", bowed_line([(0.0, HIS), (0.25, -12), (d, -12)], d, 0.9, seed=37, octaves=(0,), attack=0.05, release=0.8,
                              env=env), T_PULL[0] - 0.05, -10)
    m.put("music", celesta(note(HER), 0.6, 2), T_PULL[0], -17, pan=-0.2)
    m.end()


# ============================================================================ s11 END
def s11(m, t0):
    S = scene("s11")
    if S is None:
        return
    m.begin(S, "s11", t0)
    T_WEB_OFF = g(S, "T_WEB_OFF", 0.15)
    T_RING_IN = g(S, "T_RING_IN", (0.3, 0.18))
    T_LIFT = g(S, "T_LIFT", 0.55)
    STAG = g(S, "LIFT_STAGGER", 0.085)
    n_win = len(g(S, "LETTER_ROOMS", (None,) * 8))
    T_STAMP = g(S, "T_STAMP", 1.95)
    T_SLASH = g(S, "T_SLASH", 3.0)
    T_AWAY = g(S, "T_AWAY", 4.45)
    T_POP = g(S, "T_POP", 5.2)
    BEATS = g(S, "BEATS", ((5.55, 1.0), (6.2, 0.7)))
    T_GONE = g(S, "T_GONE", (6.5, 0.45))
    lift = [call(S, "t_lift", i, default=T_LIFT + STAG * i) for i in range(n_win)]
    ring = 1.6

    # the major rings on (s10's chord), the sirens far off and fading
    env = [(0.0, 1.0), (ring, 0.0)]
    m.put("music", strings((-12, 0, 4, 7, 12, 16), ring, 0.9, seed=36, octaves=(0, 1), attack=0.6, release=0.3, env=env),
          0.0, -12, label="the major rings on", align=None)
    for v, (period, pan) in enumerate(((3.6, 0.45), (4.3, -0.4))):
        x = dsp.sos(siren(ring + 0.4, seed=40 + v, period=period), "lowpass", 1500.0, 2)
        x = x * dsp.env_bp_db([(0.0, -30), (0.25, -14), (ring, -40)], len(x))  # crossfades with s10's tail
        m.put("efx", rev(x, 0.0, 40 + v, "street"), 0.0, -14, pan=pan)
    # the looks run home: a reversed shimmer; the ring draws tight
    sh = celesta(note(HER), 0.7, 3)[: n_of(0.6)] + celesta(note(HER + 7), 0.5, 2)[: n_of(0.6)]
    m.put("music", rev(sh[::-1], -6.0, 5), T_WEB_OFF - 0.3, -19, label="looks run home", sync=T_WEB_OFF, align=None)
    m.put("efx", squeak(max(0.12, T_RING_IN[1]), 12), T_RING_IN[0], -15, label="ring draws tight")
    # each window lifts out: one plucked note, up the major scale
    scale = (24, 26, 28, 29, 31, 33, 35, 36)
    for i, t in enumerate(lift):
        m.put("music", harp(note(scale[min(i, len(scale) - 1)]), 0.8, seed=50 + i), t, -11, pan=-0.5 + i / max(n_win - 1, 1),
              label="window lifts")
    # the title stamps; the red slash: a whip and the last chord (the Psycho chord turned major)
    m.put("efx", fx("impact", seed=60, size=0.55), T_STAMP + 0.02, -6, label="title stamps", sync=T_STAMP)
    m.put("efx", dsp.sos(door_thud(61, 1.5).mean(axis=1), "lowpass", 400.0, 2), T_STAMP + 0.02, -8)
    m.put("efx", fx("brush_swish", seed=62), T_STAMP - 0.05, -20)
    m.put("efx", fx("whip", seed=63), T_SLASH - 0.15, -6, pan=0.2, label="red slash: whip", sync=T_SLASH, align=None)
    last = T_POP - T_SLASH
    m.put("music", rev(strings((-12, 0, 4, 7, 11, 16), last, 1.0, seed=64, octaves=(0, 1), attack=0.02, release=0.5,
                               env=[(0.0, 1.0), (0.4, 0.8), (last, 0.35)]), -12.0, 6), T_SLASH, -11, label="the last chord",
          hall=-20)
    m.put("music", piano(note(-12), dur=last + 0.4, vel=0.9, seed=8), T_SLASH, -14, hall=-20)
    m.put("music", celesta(note(HIS + 48), 0.5, 1), T_SLASH, -20, pan=0.3)
    m.put("efx", fx("brush_swish", seed=65), T_AWAY, -15, pan=-0.5, label="halves slide away")
    m.put("efx", fx("brush_swish", seed=66), T_AWAY + 0.05, -15, pan=0.5)
    # the dot pops; two heartbeats, the second softer; gone
    m.put("music", soft_hit(note(12), 0), T_POP, -12, label="dot pops")
    for j, (tb, a) in enumerate(BEATS):
        m.put("music", heart(0.2, seed=j), tb, -6 + 20.0 * math.log10(max(a, 0.05)), label="heartbeat", hall=-24)
    m.mark(T_GONE[0] + T_GONE[1], "gone")
    m.cover("silence")
    m.end()


SECTIONS = (("s01", s01), ("s02", s02), ("s03", s03), ("s04", s04), ("s05", s05), ("s06", s06), ("s07", s07),
            ("s08", s08), ("s09", s09), ("s10", s10), ("s11", s11))


def silence_from():
    """Film time the sound must be gone: the red dot's end in s11, on the next quarter beat."""
    S = scene("s11") if "s11" in START else None
    gone = g(S, "T_GONE", (6.5, 0.45)) if S is not None else (6.5, 0.45)
    t = math.ceil((gone[0] + gone[1]) / E8 - 1e-6) * E8
    return START.get("s11", DUR - 8.0) + t


# ============================================================================ the bible, for missing scenes
def _bc(t, text, gain=-12.0, dur=None):
    c = {"t": float(t), "sfx": text, "gain_db": float(gain), "pan": 0.0}
    if dur is not None:
        c["dur"] = float(dur)
    return c


BIBLE_CUES = {       # the bible's sound notes for s06 and s09, on the beats the sections default to
    "s06": [_bc(0.1, "her breath (in the dark)", -14), _bc(2.5, "his door opens: a slab of light", -16),
            _bc(2.84, "his steps on the street", -18, 1.4), _bc(4.5, "he looks up: two red glints", -14),
            _bc(5.32, "the chain slides into its slot", -12), _bc(6.68, "the sash goes up", -12),
            _bc(7.12, "wind", -18, 2.9), _bc(8.62, "iron creak: she steps out onto the fire escape", -14)],
    "s09": [_bc(0.35, "his door creaks open", -8, 0.75), _bc(1.15, "her breath catches", -6),
            _bc(4.25, "the victim's fingers close: a faint breath", -22),
            _bc(6.0, "dial 9: real dial pulses", -10), _bc(7.5, "dial 1", -10), _bc(8.5, "dial 1", -10),
            _bc(10.25, "ringback in the receiver", -15), _bc(11.0, "ringback in the receiver", -15),
            _bc(11.5, "the ringing stops: click", -15)],
}


# ============================================================================ spotting fallback
def realize(m, c):
    """Realise a cue no section answered, from its words. Returns how (or why not)."""
    s = c["sfx"].lower()
    t = float(c["t"])
    gdb = float(c.get("gain_db", -12.0)) - 4.0
    pan = float(c.get("pan", 0.0))
    dur = c.get("dur")
    lab = "auto: " + c["sfx"]

    def has(*w):
        return any(x in s for x in w)

    if has("silence"):
        return "silence (nothing to add)"
    if has("heart"):
        k, n = 0, max(1, int((dur or 0.5) / 0.6))
        for k in range(n):
            m.put("music", heart(0.26, seed=k % 3), t + 0.6 * k, gdb, label=lab if k == 0 else None, hall=-22)
        return "auto: heartbeat"
    if has("breath"):
        x = gen("his_breath", 1.2, 1.2 + min(dur or 1.6, 1.6)) if has("his") else gen("her_breath", 3.0, 3.0 + min(dur or 1.5, 2.5))
        m.put("vox", dsp.sos(x, "lowpass", 3000.0, 2), t, gdb, pan=pan, label=lab, align=None)
        return "auto: breath"
    if has("gasp"):
        m.put("vox", gen("gasp_a", 0.0, 0.6), t, gdb, pan=pan, label=lab, key=True)
        return "auto: gasp"
    if has("scream"):
        m.put("vox", gen("scream_b", 0.0, min(dur or 1.0, 2.5)), t, gdb, pan=pan, label=lab, key=True)
        return "auto: scream"
    if has("step", "feet", "footfall"):
        bk = bank("her_steps", -28.0) if has("her", "she") else bank("stairs_up")
        n = max(1, int((dur or 0.0) / 0.4) + 1)
        for k in range(n):
            m.put("feet", bk[k % len(bk)], t + 0.4 * k - STEP_PRE, gdb, pan=pan, label=lab if k == 0 else None,
                  sync=t + 0.4 * k)
        return "auto: footsteps"
    if has("dial"):
        d = re.findall(r"\d", s)
        x, _ = dial(int(d[0]) if d else 1)
        m.put("efx", x, t, gdb, pan=pan, label=lab)
        return "auto: rotary dial"
    if has("ringback", "ringing", "phone ring", "rings twice"):
        m.put("efx", ringback(2), t, gdb, pan=pan, label=lab)
        return "auto: ringback"
    if has("receiver", "handset", "hang"):
        m.put("efx", receiver(int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: receiver"
    if has("door"):
        name = "door_creak" if has("creak") else "door_close" if has("close", "shut", "slam") else "door_open"
        m.put("efx", fx(name, seed=int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: " + name
    if has("chain"):
        m.put("efx", chain_taut(int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: chain"
    if has("sash"):
        m.put("efx", sash(0.55, int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: sash"
    if has("grating", "rung", "iron ring", "rings faintly"):
        m.put("efx", rung(int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: iron ring"
    if has("creak"):
        m.put("efx", creak(0.5, int(t * 10), iron=has("iron", "escape")), t, gdb, pan=pan, label=lab)
        return "auto: creak"
    if has("wind", "gust"):
        d = dur or 2.0
        m.put("amb", wind_bed(np.full(n_of(d), 0.4)), t, gdb, pan=pan, label=lab, align=None)
        return "auto: wind"
    if has("siren"):
        m.put("efx", rev(siren(dur or 3.0, seed=int(t)), -4.0, 1, "street"), t, gdb, pan=pan, label=lab, align=None)
        return "auto: siren"
    if has("horn"):
        m.put("efx", horn_far(int(t)), t, gdb, pan=pan, label=lab)
        return "auto: horn"
    if has("click", "tick", "switch"):
        m.put("efx", fx("clock_tick", seed=int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: click"
    if has("whoosh", "rush"):
        m.put("efx", fx("whoosh", seed=int(t * 10), size=0.5), t, gdb, pan=pan, label=lab, align=None)
        return "auto: whoosh"
    if has("whip", "slash"):
        m.put("efx", fx("whip", seed=int(t * 10)), t - 0.18, gdb, pan=pan, label=lab, sync=t, align=None)
        return "auto: whip"
    if has("zip"):
        m.put("efx", zip_(0.3, int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: zip"
    if has("squeak", "marker"):
        m.put("efx", squeak(0.4, int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: marker squeak"
    if has("braam"):
        m.put("music", braam(int(t) % 3), t, gdb, pan=pan, label=lab)
        return "auto: braam"
    if has("sting"):
        m.put("music", stinger(int(t) % 3), t, gdb, pan=pan, label=lab)
        return "auto: stinger"
    if has("stab"):
        m.put("music", stab(int(t) % 3), t, gdb, pan=pan, label=lab)
        return "auto: string stab"
    if has("swell", "riser"):
        m.put("music", fx("reverse_swell", dur=dur or 1.5, seed=int(t)), t, gdb, pan=pan, label=lab, align=None)
        return "auto: swell"
    if has("chime"):
        m.put("music", chime(note(HER)), t, gdb, pan=pan, label=lab)
        return "auto: chime"
    if has("bell"):
        m.put("music", bell(note(31)), t, gdb, pan=pan, label=lab)
        return "auto: bell"
    if has("gong"):
        m.put("music", gong(note(-12)), t, gdb, pan=pan, label=lab)
        return "auto: gong"
    if has("thud", "impact", "slam", "burst", "kick", "stamp", "hit"):
        m.put("efx", cut(fx("impact", seed=int(t * 10), size=0.3), 1.2, 0.3), t, gdb, pan=pan, label=lab)
        return "auto: impact"
    if has("rustle", "cloth", "skirt", "collar", "sleeve"):
        m.put("efx", rustle(0.35, int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: rustle"
    if has("slap"):
        m.put("efx", slap(int(t)), t, gdb, pan=pan, label=lab)
        return "auto: slap"
    if has("paper", "rip", "tear", "swish"):
        m.put("efx", fx("brush_swish", seed=int(t * 10)), t, gdb, pan=pan, label=lab)
        return "auto: paper"
    if has("smash", "shatter", "glass"):
        m.put("efx", gen("mug_smash", 0.0, 1.4), t, gdb, pan=pan, label=lab)
        return "auto: smash"
    if has("fall"):
        m.put("efx", gen("body_fall", 0.0, 1.3), t, gdb, pan=pan, label=lab)
        return "auto: body fall"
    if has("pizz"):
        m.put("music", pizz(note(0)), t, gdb, pan=pan, label=lab)
        return "auto: pizzicato"
    if has("pluck", "note", "melody"):
        m.put("music", harp(note(24)), t, gdb, pan=pan, label=lab)
        return "auto: plucked note"
    if has("tremolo", "string", "chord", "cluster", "drone"):
        m.put("music", strings((0, 3, 7), dur or 1.5, 0.7, seed=int(t), attack=0.3), t, gdb, pan=pan, label=lab, align=None)
        return "auto: strings"
    return "no sound for these words"


# ============================================================================ mixdown and master
def mixdown(m):
    key = m.key
    duck = lambda x, depth: dsp.sidechain_duck(x, key, depth_db=depth, thresh_db=-42.0, attack=0.03, release=0.3)  # noqa: E731
    music = duck(m.b["music"].astype(np.float64), -7.0)
    hall = dsp.reverb(m.b["hall"].astype(np.float64), "hall", wet_db=0.0, dry=0.0, seed=7)[:N]
    hall = duck(hall, -7.0)
    amb = duck(m.b["amb"].astype(np.float64), -3.0)
    m.stems = {"music": (music + hall).astype(np.float32), "amb": amb.astype(np.float32), "efx": m.b["efx"],
               "vox": m.b["vox"], "feet": m.b["feet"]}
    return music + hall + amb + m.b["efx"] + m.b["vox"] + m.b["feet"]


def master(mix, t_silence, target=-16.0, ceiling=-1.2):
    """High-pass, loudness to target, true-peak limit (iterated: the limiter takes a little
    loudness), and digital silence from t_silence (with a fade into it)."""
    mix = dsp.sos(mix, "highpass", 30.0, 2)
    a = int(round(t_silence * SR))
    fl = n_of(0.35)
    if 0 < a <= len(mix):
        mix[max(0, a - fl):a] *= np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, min(fl, a)))[:, None] ** 2
        mix[a:] = 0.0
    gain = target - dsp.loudness_integrated(mix)
    for it in range(4):
        out = dsp.limiter(mix * db2lin(gain), ceiling_db=ceiling)
        lufs = dsp.loudness_integrated(out)
        if abs(lufs - target) < 0.05:
            break
        gain += target - lufs
    out[a:] = 0.0
    out = dsp.fade(out, 0.005, 0.0)
    master.gain = gain
    return out[:N]


# ============================================================================ QA
def find_clicks(x, thresh=8.0, max_report=40):
    """audio/reference/qa.py's detector: 2nd difference of the 7 kHz high-passed signal against
    its local 20 ms RMS."""
    hp = dsp.sos(np.asarray(x, np.float64), "highpass", 7000.0, 4)
    d2 = np.abs(np.diff(hp, n=2, axis=0)).max(axis=1)
    w = n_of(0.02)
    c = np.concatenate([[0.0], np.cumsum(d2 ** 2)])
    i = np.arange(len(d2))
    lo, hi = np.maximum(0, i - w), np.minimum(len(d2), i + w)
    local = np.sqrt((c[hi] - c[lo]) / np.maximum(hi - lo, 1))
    score = d2 / (local + 1e-6)
    cand = np.nonzero((score > thresh) & (d2 > 10 ** (-50 / 20)))[0]
    events, last = [], -10 ** 9
    for k in cand:
        if k - last > SR * 0.05:
            events.append(k)
        last = k
    events = sorted(events, key=lambda k: -score[k])[:max_report]
    return [((k + 1) / SR, float(score[k])) for k in sorted(events)]


def qa(out, m, t_silence, outdir, path):
    import soundfile as sf
    os.makedirs(outdir, exist_ok=True)
    y, sr = sf.read(path, dtype="float64", always_2d=True)
    print("\n================ QA:", path)
    print(f"  file: {sr} Hz, {y.shape[1]} ch, {len(y)} samples = {len(y) / sr:.4f} s")
    print(f"  integrated {dsp.loudness_integrated(y):.2f} LUFS   true peak {dsp.true_peak_db(y):.2f} dBTP   "
          f"sample peak {dsp.sample_peak_db(y):.2f} dBFS   samples >= -0.1 dBFS: {int(np.sum(np.abs(y) >= db2lin(-0.1)))}")
    a = int(round(t_silence * SR))
    print(f"  silence from {t_silence:.2f} s: all zero = {bool(np.all(y[a:] == 0.0))}; last second all zero = "
          f"{bool(np.all(y[-SR:] == 0.0))}")
    print("  per scene:   RMS dBFS   LUFS(int)   peak dBFS   (loudest 3 s)")
    for sid, s0, d in SCENES:
        seg = y[int(s0 * SR): int((s0 + d) * SR)]
        rms = dsp.rms_db(seg) if np.any(seg) else -np.inf
        lu = dsp.loudness_integrated(seg) if np.any(seg) else -np.inf
        _, st = dsp.loudness_curve(seg, win=3.0, hop=0.25) if np.any(seg) else (None, np.array([-np.inf]))
        print(f"   {sid} {s0:6.1f}  {rms:8.1f}   {lu:8.1f}   {dsp.sample_peak_db(seg):8.1f}   {np.max(st):7.1f}")
    # the loudest moments: which stem makes them (each stem at the master's gain), and what is there
    tw, lw = dsp.loudness_curve(y, win=1.0, hop=0.5)
    order = [int(i) for i in np.argsort(-lw)]
    picked = []
    for i in order:
        if all(abs(tw[i] - tw[j]) > 2.0 for j in picked):
            picked.append(i)
        if len(picked) == 10:
            break
    gm = db2lin(getattr(master, "gain", 0.0))
    print("  loudest 1 s windows (LUFS): mix | " + " ".join(f"{k:>5s}" for k in m.stems))
    for i in sorted(picked, key=lambda j: tw[j]):
        a, b = int((tw[i] - 0.5) * SR), int((tw[i] + 0.5) * SR)
        parts = []
        for k, st in m.stems.items():
            seg = st[a:b].astype(np.float64) * gm
            parts.append(f"{dsp.loudness_integrated(seg) if np.any(seg) else -99:5.0f}")
        top = sorted((sp for sp in m.spans if sp[1] < b / SR and sp[2] > a / SR), key=lambda sp: -sp[5])[:5]
        print(f"   {tw[i]:6.1f}  {lw[i]:5.1f} | " + " ".join(parts) + "   "
              + "; ".join(f"{sp[3] or '-'}@{sp[4]}({20 * math.log10(max(sp[5], 1e-9)) + 20 * math.log10(gm):.0f})" for sp in top))
    # clicks: anything not on a placed transient is suspect; scene cuts checked on their own
    clicks = find_clicks(y, max_report=400)
    hits = np.array(sorted(m.starts))
    sus = [(t, s) for t, s in clicks if not len(hits) or not np.any((t - hits > -0.003) & (t - hits < 0.08))]
    print(f"  click detector: {len(clicks)} transients flagged, {len(sus)} not at the start of a placed sound: "
          + ", ".join(f"{t:.3f}s({s:.0f})" for t, s in sus[:30]))
    gm = db2lin(getattr(master, "gain", 0.0))
    for t, sc in sus:
        a, b = int((t - 0.003) * SR), int((t + 0.003) * SR)
        hf = {}
        for k, st in m.stems.items():
            seg = dsp.sos(st[max(0, a - 2000): b + 2000].astype(np.float64) * gm, "highpass", 7000.0, 4)[2000: 2000 + b - a]
            hf[k] = float(np.max(np.abs(np.diff(seg, n=2, axis=0)))) if len(seg) > 2 else 0.0
        k = max(hf, key=hf.get)
        over = [f"{lab or '-'}@{ln}" for bus, s0, s1, lab, ln, _ in m.spans if bus == k and s0 <= t <= s1]
        print(f"    {t:8.3f}: {k} ({hf[k]:.4f}); under it: {', '.join(over[:6])}")
    print(f"  placements starting or ending on a step: {len(m.edges)}")
    for sid, t, lab, e0, e1, bus in m.edges[:40]:
        print(f"    {sid} {t:8.3f} {bus:5s} start {e0:5.2f} end {e1:5.2f}  {lab}")
    cuts = []
    for sid, s0, _ in SCENES[1:]:
        i0 = int(s0 * SR)
        w = y[i0 - n_of(0.004): i0 + n_of(0.004)]
        cuts.append(f"{s0:.0f}:{float(np.max(np.abs(np.diff(w, axis=0)))) if len(w) > 1 else 0:.3f}")
    print("  largest sample step within 4 ms of each cut:", " ".join(cuts))
    # sync: every cue against the nearest event of its scene; and each event's measured onset
    worst, late = 0.0, []
    for sid, c, how in m.report:
        mine = [e for e in m.ev if e["sid"] == sid]
        if not mine or how.startswith("silence") or how.startswith("no sound"):
            continue
        tf = START[sid] + c["t"]
        d = min(abs(e["t"] - tf) for e in mine)
        if how == "section" and d > FRAME + 1e-6:
            continue                                  # realised by a section elsewhere (cover)
        worst = max(worst, d)
        if d > FRAME + 1e-6:
            late.append((sid, c["t"], c["sfx"], d))
    print(f"  cues: {len(m.report)}  realised by sections {sum(1 for r in m.report if r[2] == 'section')}, "
          f"auto {sum(1 for r in m.report if r[2].startswith('auto'))}, "
          f"not realised {sum(1 for r in m.report if not (r[2] == 'section' or r[2].startswith('auto') or r[2].startswith('silence')))}; "
          f"worst cue-to-event offset {worst * 1000:.1f} ms")
    off = [(e["sid"], e["label"], e["meas"] - e["t"]) for e in m.ev if e["meas"] is not None]
    bad = [o for o in off if abs(o[2]) > FRAME]
    print(f"  measured onsets of {len(off)} hits: worst {max((abs(o[2]) for o in off), default=0) * 1000:.1f} ms; "
          f"{len(bad)} beyond a frame")
    for s_, lab, d in bad[:80]:
        print(f"    {s_} {lab}: {d * 1000:+.0f} ms")
    for sid, t, txt, d in late:
        print(f"    late: {sid} {t:.3f} {txt!r} ({d * 1000:.0f} ms)")
    overview(y, m, outdir)


def overview(y, m, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = y.mean(axis=1)
    fig, ax = plt.subplots(4, 1, figsize=(26, 13), dpi=70, sharex=True,
                           gridspec_kw=dict(height_ratios=[1.1, 2.0, 1.1, 0.6]))
    fig.patch.set_facecolor("white")
    px = 3000
    k = len(x) // px
    mn, mx = x[: k * px].reshape(px, k).min(axis=1), x[: k * px].reshape(px, k).max(axis=1)
    tt = np.arange(px) * k / SR
    ax[0].fill_between(tt, mn, mx, color="#234", lw=0)
    ax[0].set_ylim(-1, 1)
    ax[0].set_ylabel("waveform")
    f, t, Z = signal.spectrogram(x[::2], fs=SR / 2, nperseg=1024, noverlap=512)
    Z = 10 * np.log10(Z + 1e-12)
    ax[1].pcolormesh(t, f, Z, vmin=Z.max() - 90, vmax=Z.max(), shading="auto", cmap="magma")
    ax[1].set_yscale("symlog", linthresh=200)
    ax[1].set_ylim(30, 12000)
    ax[1].set_ylabel("Hz")
    tm, lm = dsp.loudness_curve(y, win=0.4, hop=0.05)
    ts, ls = dsp.loudness_curve(y, win=3.0, hop=0.1)
    ax[2].plot(tm, lm, color="#999", lw=0.6)
    ax[2].plot(ts, ls, color="#c60", lw=1.6)
    ax[2].axhline(-16, color="#060", lw=0.8, ls="--")
    ax[2].set_ylim(-50, -5)
    ax[2].set_ylabel("LUFS (0.4 s / 3 s)")
    for e in m.ev:
        ax[3].plot([e["t"], e["t"]], [0, 1], color="#c00" if e["bus"] == "music" else "#036", lw=0.5)
    ax[3].set_yticks([])
    ax[3].set_ylabel("events")
    for a in ax:
        for sid, s0, d in SCENES:
            a.axvline(s0, color="#0a0", lw=1.0)
        a.set_xlim(0, DUR)
    for sid, s0, d in SCENES:
        ax[0].text(s0 + 0.2, 0.85, sid, color="#070", fontsize=12)
    ax[3].set_xlabel("film time (s)")
    fig.tight_layout()
    p = os.path.join(outdir, "overview.png")
    fig.savefig(p)
    plt.close(fig)
    print("  overview:", p)


# ============================================================================ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--qa", metavar="DIR", help="measure the master and draw DIR/overview.png")
    ap.add_argument("--stand-ins", action="store_true", help="play missing scenes from the bible's beats")
    ap.add_argument("--only", help="comma list of sections to render (not mastered to the film)")
    ap.add_argument("--stems", metavar="DIR", help="also write the stems (music, amb, efx, vox, feet) at the master's gain")
    ap.add_argument("--without", help="comma list of scenes to treat as missing (to hear the skip or the stand-ins)")
    a = ap.parse_args(argv)
    ARGS.stand_ins, ARGS.only, ARGS.qa = a.stand_ins, set(a.only.split(",")) if a.only else None, a.qa
    ARGS.without = set(a.without.split(",")) if a.without else set()
    t_start = time.process_time()
    w0 = time.time()
    m = Mix()
    for sid, fn in SECTIONS:
        if sid not in START or (ARGS.only and sid not in ARGS.only):
            continue
        ts = time.time()
        try:
            fn(m, START[sid])
        except Exception as e:  # a scene changed under the section: keep the rest of the film
            import traceback
            traceback.print_exc()
            warn(f"{sid}: section failed ({type(e).__name__}: {e}): what it placed before failing is kept")
        print(f"{sid}: {time.time() - ts:5.1f} s", flush=True)
    mix = mixdown(m)
    t_sil = silence_from()
    import soundfile as sf
    out_dir = os.path.join(ROOT, "out")
    os.makedirs(out_dir, exist_ok=True)
    if ARGS.only:
        path = os.path.join(out_dir, "audio_only.wav")
        mix = dsp.sos(mix, "highpass", 30.0, 2)
        mix = dsp.limiter(mix * db2lin(-16.0 - dsp.loudness_integrated(mix)), ceiling_db=-1.2)
        sf.write(path, mix[:N].astype(np.float32), SR, subtype="PCM_24")
        print(path)
        return
    out = master(mix, t_sil)
    path = os.path.join(out_dir, "audio_master.wav")
    sf.write(path, out.astype(np.float32), SR, subtype="PCM_24")
    print(f"{path}: {len(out) / SR:.3f} s, {dsp.loudness_integrated(out):.2f} LUFS, TP {dsp.true_peak_db(out):.2f} dBTP; "
          f"render {time.time() - w0:.0f} s wall, {time.process_time() - t_start:.0f} s CPU")
    if WARN:
        print(f"{len(WARN)} warnings:")
        for w in WARN:
            print("  -", w)
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        gm = db2lin(master.gain)
        for k, st in m.stems.items():
            sf.write(os.path.join(a.stems, f"stem_{k}.wav"), (st * gm).astype(np.float32), SR, subtype="FLOAT")
        print("stems:", a.stems)
    if ARGS.qa:
        qa(out, m, t_sil, ARGS.qa, path)


if __name__ == "__main__":
    main()
