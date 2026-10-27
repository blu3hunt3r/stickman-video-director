"""THIN ICE: the complete score and sound, locked to the scene modules.

    cd productions/silhouette-noir
    python3 films/thin_ice/audio/mix.py                  # -> films/thin_ice/out/audio_master.wav
    python3 films/thin_ice/audio/mix.py --qa DIR         # ... and measure it (DIR/qa.json, DIR/overview.png)
    python3 films/thin_ice/audio/mix.py --only s08,s09   # just these sections (a quick listen: out/audio_only.wav)
    python3 films/thin_ice/audio/mix.py --stems DIR      # ... and the stems, at the master's gain
    python3 films/thin_ice/audio/mix.py --without s06    # treat s06 as missing (it is played from the bible)
    python3 films/thin_ice/audio/mix.py --skip-missing   # leave missing scenes silent instead

48 kHz stereo 24-bit PCM, exactly the timeline's 188 s, integrated -16 LUFS, true peak at most -1.3 dBTP;
exact digital zeros from s12's T_BLACK (15.75 s: film 187.75) to the end, and through s08's half
second of dead silence after the crack (its T_SILENCE).

Every beat a section uses is read from the scene's module on every run: its constant by name, else
its own cue whose words match (nearest the bible's time), else the bible's time; every cue is read
from the module's cues() on every run, and the foley is spotted from them (a handler per tag: the
mother's felt boots, the girl's, the guard's hobnails, the ice, the lantern, the wool ...). A missing
module, one that does not import, or one whose cues() gives nothing is played from the bible (a
stand-in: BIBLE_CUES). Every cue no section answered within a frame is realised from its words
(realize) and reported. Nothing is fetched and nothing is generated: the only recordings are
OPPOSITE's breaths, gasps and body fall (films/opposite/audio/gen) and DOUBLE CROSS's grunt
(grunt_knight); everything else is synthesised here (numpy/scipy), with the OPPOSITE cuts' strings
(films/opposite_full/audio/mix.py) and DOUBLE CROSS's foley helpers. No voices but breath, gasps
and the grunt. Deterministic: the same scenes give the same file.

THE SCORE: strings and a music box, 120 bpm (a beat 0.5 s, a bar 2 s; every scene starts on a bar
line), A minor, ending in A major. THE LULLABY (the music box): E5 C5 | D5 B4 | C5 A4 | B4 E4 |
A4 C5 | B4 G#4 | A4. Its first three notes in s02 before the lid is slapped shut; its first note
alone in s09 (where the heartbeat was) and, far off, on s11's match cut; the whole tune once, in A
major, in s12 (its notes and their times read from s12's NOTES and NOTE_NAMES), the strings under
it from T_STRINGS (A, D, E, A), the last chord held under the title and the thread, all of it
stopped dead at T_BLACK. The thread is a string harmonic, E6 (s01, again under s12's last chord);
the moon an A6 harmonic. THE HUNT (s03-s07): low sustained strings in A minor (an F aching in them
when it closes in), a soft low pulse on the film's grid that quickens with the chase (a bar, a beat,
an eighth), high harmonics for the ice; the lullaby's head low and slow in the cellos under the
false trail. s08: the crack, half a second of nothing, the break; under the ice a murky low drone
and his huge slow heart; it surfaces with him. s09: her heart alone at 96 bpm with one trembling
E6, both stopped dead as she takes the scarf. s10: an A pedal swelling under the throws, cut dead
on the hook (one low stab), the strings rising again under the slide and releasing when he is out.
s11: quiet; the watch never ticks; A minor under the watch, A minor with an aching F under the lie,
a glass shimmer as the first snow falls. A heartbeat is never on the score's grid (s02's two cued
beats are hers at 96 bpm, as in s09).

THE ICE (synthesised): deep groans (stick-slip through the sheet's low modes, a bending tone), booms
(a deep thud, a long low chirp, rumble rolling away), the dispersive 'pew' (high notes arrive first:
a falling whistle in 0.1-0.4 s, echoed off the far edges), cracks (a broadband snap, micro-fractures,
a glassy ring, a pew), the break, the plunge, the edge's small crunches, the stone's crack and plop.
THE SNOW: three crunches - the mother's felt boots soft and quick, the girl's smaller and quicker,
the guard's heavy and slow with hobnails' grit; deep snow (a drag before the crunch), thin snow over
ice (a hollow ring under it), bare ice (a ringing click). The wind always there: louder in the open,
high in the pines, through the hut's walls, falling away when the snow stops, quiet in the lee of the
farmhouse.
"""
from __future__ import annotations

import argparse
import glob
import importlib
import json
import math
import os
import re
import subprocess
import sys
import time
from functools import lru_cache

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np  # noqa: E402

from audio import dsp, sfx  # noqa: E402
from audio.dsp import SR, db2lin, n_of  # noqa: E402
from engine.timing import SceneTiming  # noqa: E402
import films.double_cross.audio.mix as DC  # noqa: E402   (its foley helpers and the grunt's take; side-effect free)
import films.opposite_full.audio.mix as OF  # noqa: E402  (the OPPOSITE cuts' strings, harp, pizzicato)
import films.opposite.audio.mix as OPP  # noqa: E402      (the breath recordings: films/opposite/audio/gen)
from films.opposite.audio.mix import mono  # noqa: E402

FILM = "thin_ice"
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
BEAT, BAR, E8, E16 = 0.5, 2.0, 0.25, 0.125      # 120 bpm

# scene trims (dB, every bus): the film's arc, set by meter (see --qa's per-scene table)
TRIM = dict(s01=0.0, s02=0.0, s03=0.0, s04=2.0, s05=1.5, s06=2.0, s07=2.0, s08=-1.0, s09=-0.5, s10=-2.5, s11=-1.5,
            s12=-2.0)
CUE_TRIM = -2.0              # a cue's gain_db, as the scenes write it, to this mix's levels
MUSIC_LIFT = 5.0             # the held score (strings, harmonics; the pulse 2 dB less) over its cues' gains
BED_LIFT = 2.0               # the beds (wind, river, the motor, the stove) over their cue gains: the film's floor
BOX_TRIM = -2.5              # the box's loud notes (s02's three, s12's tune) under their cues: a small box
REF = -16.0                  # every synthesised sound comes in at the catalog's level (sfx.REF_LUFS)

ARGS = argparse.Namespace(stand_ins=True, only=None, qa=None, without=set())
WARN = []
STATUS = {}                  # sid -> how the scene was played (module / stand-in and why)


def warn(msg):
    WARN.append(msg)
    print("WARNING:", msg, flush=True)


# ============================================================================ music theory
hz, midi, nm = DC.hz, DC.midi, DC.nm
LULLABY = ("E5", "C5", "D5", "B4", "C5", "A4", "B4", "E4", "A4", "C5", "B4", "G#4", "A4")   # the bible's, A minor
LULLABY_MAJOR = ("E5", "C#5", "D5", "B4", "C#5", "A4", "B4", "E4", "A4", "C#5", "B4", "G#4", "A4")
THREAD, MOON, ICE_HI = 88, 93, (88, 93, 100)   # E6 (the red thread), A6 (the moon); the ice's harmonics
AM = (45, 52, 57, 60)                          # A2 E3 A3 C4: A minor, the strings' voicing
AM_F = (45, 52, 60, 65)                        # A minor with the aching F (over the E an octave and a half down)


def notes_of(names, fallback):
    """Note names -> midi (a name that does not parse falls back to the bible's)."""
    out = []
    for i, nmx in enumerate(names):
        try:
            out.append(midi(str(nmx)))
        except Exception:
            out.append(midi(fallback[i % len(fallback)]))
    return out


# ============================================================================ the scene modules
class Stub:
    """A scene played from the bible: missing, or its module broken. Every beat falls back to the
    bible's (the defaults the section passes), its cues to BIBLE_CUES."""

    def __init__(self, sid, why):
        self.sid, self.why = sid, why


_LOADED = {}


def scene(sid):
    if sid not in _LOADED:
        _LOADED[sid] = _load(sid)
    return _LOADED[sid]


def _load(sid):
    paths = sorted(glob.glob(os.path.join(ROOT, "scenes", f"{sid}_*.py")))
    if sid in (ARGS.without or ()):
        paths = []
    if not paths:
        if ARGS.stand_ins:
            STATUS[sid] = "stand-in (no module)"
            warn(f"{sid}: no scene module (scenes/{sid}_*.py): played from the bible")
            return Stub(sid, "missing")
        STATUS[sid] = "skipped (no module)"
        warn(f"{sid}: no scene module: section skipped (--skip-missing)")
        return None
    name = os.path.basename(paths[0])[:-3]
    try:
        mod = importlib.import_module(f"films.{FILM}.scenes.{name}")
    except Exception as e:
        STATUS[sid] = f"stand-in (module does not import: {type(e).__name__})"
        warn(f"{sid}: {name} does not import ({type(e).__name__}: {e}): played from the bible")
        return Stub(sid, "broken")
    if _draft(mod, sid):
        STATUS[sid] = f"stand-in (module {name} has no cues yet)"
        warn(f"{sid}: {name}.cues() gives no cues yet: played from the bible until it does")
        return Stub(sid, "draft")
    STATUS[sid] = f"module {name}"
    return mod


def _cue_args(sid):
    try:
        T = SceneTiming(FILM, sid)
        return (T, T.duration), None
    except Exception as e:
        return (), f"SceneTiming: {e}"


def _draft(mod, sid):
    if not hasattr(mod, "cues"):
        return False
    for arg in _cue_args(sid)[0]:
        try:
            return len(list(mod.cues(arg))) == 0
        except Exception:
            continue
    return False


FROM_BIBLE = {}
_FAILED = set()


def _num(v):
    return isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool) and math.isfinite(float(v))


def _sid(S):
    return S.sid if isinstance(S, Stub) else os.path.basename(getattr(S, "__name__", "?")).split(".")[-1].split("_")[0]


def _same_kind(v, d):
    if _num(d):
        return _num(v)
    if isinstance(d, (tuple, list)):
        if not isinstance(v, (tuple, list, np.ndarray)) or len(v) == 0:
            return False
        if d and all(_num(x) for x in d):
            return all(_num(x) for x in v)
        if d and all(isinstance(x, str) for x in d):
            return all(isinstance(x, str) for x in v)
        if d and all(isinstance(x, (tuple, list)) for x in d):
            return all(isinstance(x, (tuple, list)) for x in v)
        return True
    if isinstance(d, dict):
        return isinstance(v, dict)
    return True


def g(S, name, default):
    """A constant of scene module S (the bible's value when S is a stand-in, lacks it, or it is of
    the wrong kind)."""
    if isinstance(S, Stub) or S is None:
        return default
    v = getattr(S, name, None)
    if v is None:
        FROM_BIBLE.setdefault(_sid(S), []).append(name)
        return default
    if not _same_kind(v, default):
        if (_sid(S), name) not in _FAILED:
            _FAILED.add((_sid(S), name))
            warn(f"{_sid(S)}: {name} = {v!r} is not what the mix reads ({default!r}): using the bible's")
        return default
    if _num(default):
        return float(v)
    if isinstance(default, (tuple, list)) and default and all(_num(x) for x in default):
        return tuple(float(x) for x in v)
    return v


def _clean_cues(raw, sid):
    """The cues as the mix reads them; each gets its words ('text': the sfx, its underscores as
    spaces, and its params' dc/desc), its note (params' note) and who it is about ('who')."""
    out = []
    for c in raw:
        try:
            c = dict(c)
            c["t"] = float(c["t"])
            c["sfx"] = str(c.get("sfx", ""))
            c["gain_db"] = float(c.get("gain_db", -12.0) or 0.0)
            c["pan"] = float(np.clip(float(c.get("pan", 0.0) or 0.0), -1.0, 1.0))
            if c.get("dur") is not None:
                c["dur"] = max(0.0, float(c["dur"]))
            if not math.isfinite(c["t"]):
                raise ValueError("t is not finite")
            p = c.get("params") or {}
            words = [c["sfx"].replace("_", " ")]
            for k in ("dc", "desc"):
                if p.get(k):
                    words.append(str(p[k]))
            c["text"] = ": ".join(words).lower()
            c["who"] = str(p.get("who", "") or "").lower()
            c["note"] = p.get("note")
            out.append(c)
        except Exception as e:
            warn(f"{sid}: a cue the mix cannot read ({c!r}: {e}): skipped")
    return sorted(out, key=lambda c: c["t"])


def cue_list(S, sid):
    if isinstance(S, Stub):
        return _clean_cues(BIBLE_CUES.get(sid, []), sid)
    if not hasattr(S, "cues"):
        warn(f"{sid}: no cues(): spotting from the bible's cues")
        return _clean_cues(BIBLE_CUES.get(sid, []), sid)
    args, err = _cue_args(sid)
    for arg in args:
        try:
            return _clean_cues(S.cues(arg), sid)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
    warn(f"{sid}: cues() fails ({err}): spotting from the bible's cues")
    return _clean_cues(BIBLE_CUES.get(sid, []), sid)


# ============================================================================ the buses
BUSES = ("music", "hall", "efx", "amb", "vox", "feet")
BUS_TRIM = dict()
HALL_SEND = -14.0            # the music's send to the plate


class Mix:
    """The film's buses. put() takes scene time; placements are staged and committed when the
    section ends (a section that fails part-way is dropped and played again from the bible).
    Every labelled placement is logged as an event (the beat it is for, and where its sound
    actually starts) for the sync check and for spotting: a cue counts as realised when a section
    answered it (done/covered) or an event of its scene lands within a frame of it."""

    def __init__(self):
        self.b = {k: np.zeros((N, 2), np.float32) for k in BUSES}
        self.key = np.zeros(N, np.float32)          # breath and voices duck the music a little
        self.ev, self.edges, self.starts, self.spans, self.report = [], [], [], [], []
        self.box, self.hearts, self.notes, self.silences = [], [], [], []
        self.src = {}
        self.sid, self.t0, self.trim, self.cues = None, 0.0, 0.0, []
        self.covered, self.claimed, self.done = set(), set(), set()
        self.stage, self.S, self.len = [], None, 10.0

    def begin(self, S, sid, t0):
        self.S, self.sid, self.t0, self.trim = S, sid, t0, TRIM.get(sid, 0.0)
        self.cues = cue_list(S, sid)
        self.covered, self.claimed, self.done = set(), set(), set()
        self.len = LENGTH.get(sid, 10.0)
        self.stage = []
        self.n_ev = len(self.ev)
        self.n_misc = (len(self.edges), len(self.starts), len(self.spans), len(self.report), len(self.box),
                       len(self.hearts), len(self.notes), len(self.silences))

    def abort(self):
        self.stage = []
        if not hasattr(self, "n_ev"):
            return
        del self.ev[self.n_ev:]
        e, s, sp, rp, bx, hb, nt, si = self.n_misc
        del self.edges[e:], self.starts[s:], self.spans[sp:], self.report[rp:], self.box[bx:]
        del self.hearts[hb:], self.notes[nt:], self.silences[si:]

    def commit(self):
        for bus, i, x, hall, key in self.stage:
            dsp.mix_into(self.b[bus], x, i)
            if hall is not None:
                dsp.mix_into(self.b["hall"], x * np.float32(hall), i)
            if key:
                dsp.mix_into(self.key, x.mean(axis=1), i)
        self.stage = []

    def _module(self):
        return not isinstance(self.S, Stub) and self.S is not None

    def _match(self, words, default, win):
        best = None
        for i, c in enumerate(self.cues):
            if i in self.claimed or not any(w in c["text"] for w in words):
                continue
            d = abs(c["t"] - default)
            if d <= win and (best is None or d < best[0]):
                best = (d, i)
        return None if best is None else best[1]

    def at(self, name, default, *words, win=1.5, opt=False):
        """A beat of this scene (scene time): the module's constant `name` (a span's start); else
        the time of its cue with any of `words`, nearest the bible's time (within win; for a module,
        anywhere in the scene after that); else the bible's time (opt: for a module, None)."""
        S = self.S
        if self._module() and name:
            v = getattr(S, name, None)
            if v is not None and _num(v):
                self.src[(self.sid, name)] = "module"
                return float(v)
            if isinstance(v, (tuple, list)) and len(v) and _num(v[0]):
                self.src[(self.sid, name)] = "module (a span's start)"
                return float(v[0])
            if v is not None:
                warn(f"{self.sid}: {name} = {v!r} is not a time: looking for its cue")
        if words and default is not None:
            i = self._match(words, default, win)
            if i is None and self._module():
                i = self._match(words, default, self.len + 1.0)
            if i is not None:
                self.claimed.add(i)
                self.src[(self.sid, name)] = f"cue {self.cues[i]['text'][:40]!r}"
                return float(self.cues[i]["t"])
        if opt and self._module():
            self.src[(self.sid, name)] = "not in the module"
            return None
        self.src[(self.sid, name)] = "bible"
        if self._module() and name:
            FROM_BIBLE.setdefault(self.sid, []).append(name)
        return None if default is None else float(default)

    def ats(self, name, defaults, *words, win=1.5, n=None, opt=False):
        """Several beats: the module's sequence `name` (a dict's values); else every cue with any of
        `words` around the bible's times (for a module, anywhere in the scene after that); else the
        bible's."""
        S = self.S
        defaults = tuple(float(x) for x in defaults)
        if self._module() and name:
            v = getattr(S, name, None)
            if isinstance(v, dict):
                v = [v[k] for k in sorted(v)]
            if isinstance(v, (tuple, list, np.ndarray)) and len(v) and all(_num(x) for x in v):
                self.src[(self.sid, name)] = "module"
                return tuple(float(x) for x in v)
            if v is not None:
                warn(f"{self.sid}: {name} = {v!r} is not a list of times: looking for its cues")
        if words and defaults:
            lo, hi = min(defaults) - win, max(defaults) + win
            hits = [i for i, c in enumerate(self.cues) if i not in self.claimed and lo <= c["t"] <= hi
                    and any(w in c["text"] for w in words)]
            if not hits and self._module():
                hits = [i for i, c in enumerate(self.cues) if i not in self.claimed and any(w in c["text"] for w in words)]
            if hits:
                if n is not None and len(hits) > n:
                    pick = []
                    for d in defaults[:n]:
                        pick.append(min((h for h in hits if h not in pick), key=lambda h: abs(self.cues[h]["t"] - d)))
                    hits = sorted(pick)
                self.claimed.update(hits)
                self.src[(self.sid, name)] = f"{len(hits)} cues"
                return tuple(sorted(float(self.cues[i]["t"]) for i in hits))
        if opt and self._module():
            return ()
        self.src[(self.sid, name)] = "bible"
        if self._module() and name:
            FROM_BIBLE.setdefault(self.sid, []).append(name)
        return defaults

    def span(self, name, default, *words, win=1.5):
        """(start, end) of a stretch: the module's `name` read as (start, dur) when its second
        number is no later than its first, else as (start, end); else its cue (t, t + dur); else
        the bible's (start, end)."""
        S = self.S
        if self._module() and name:
            v = getattr(S, name, None)
            if isinstance(v, (tuple, list)) and len(v) >= 2 and _num(v[0]) and _num(v[1]):
                a, b = float(v[0]), float(v[-1])
                self.src[(self.sid, name)] = "module"
                return (a, b) if b > a else (a, a + b)
        if words:
            i = self._match(words, default[0], win)
            if i is not None:
                self.claimed.add(i)
                c = self.cues[i]
                return float(c["t"]), float(c["t"]) + float(c.get("dur") or (default[1] - default[0]))
        if self._module() and name:
            FROM_BIBLE.setdefault(self.sid, []).append(name)
        return float(default[0]), float(default[1])

    def cue_near(self, t, *words, win=FRAME + 1e-6):
        best = None
        for c in self.cues:
            if words and not any(w in c["text"] or w == c["sfx"] for w in words):
                continue
            d = abs(c["t"] - t)
            if d <= win and (best is None or d < best[0]):
                best = (d, c)
        return None if best is None else best[1]

    def put(self, bus, x, at, gain=0.0, pan=0.0, label=None, sync=None, align="onset", key=False, hall="auto",
            fades=True):
        x = np.asarray(x, np.float64)
        if x.ndim == 1:
            x = dsp.pan_mono(x, pan)
        elif pan:
            x = dsp.pan_stereo(x, pan)
        if not len(x) or not np.all(np.isfinite(x)):
            if len(x):
                warn(f"{self.sid} {at:.3f}: a sound that is not finite ({label}): dropped")
            return
        i = int(round((self.t0 + at) * SR))
        env = np.abs(x).max(axis=1)
        pk = float(env.max())
        if fades and pk > 0 and len(x) > n_of(0.01):
            e0, e1 = float(env[0]) / pk, float(env[-1]) / pk
            if e0 > 0.2 or e1 > 0.1:
                self.edges.append((self.sid, self.t0 + at, label or "", e0, e1, bus))
        if fades and len(x) > n_of(0.008):
            x = dsp.fade(x, 0.001, 0.003, shape="lin")
        x = (x * db2lin(gain + self.trim + BUS_TRIM.get(bus, 0.0))).astype(np.float32)
        if hall == "auto":
            hall = HALL_SEND if bus == "music" else None
        self.stage.append((bus, i, x, None if hall is None else db2lin(hall), bool(key)))
        self.starts.append(self.t0 + at)
        self.spans.append((bus, self.t0 + at, self.t0 + at + len(x) / SR, label or "", sys._getframe(1).f_lineno,
                           float(np.sqrt(np.mean(np.square(x[: n_of(1.0)], dtype=np.float64))))))
        if label:
            env = np.abs(x).max(axis=1)
            pk = float(env.max())
            meas = None
            if align == "peak" and pk > 0:
                w = n_of(0.01)
                meas = at + int(np.argmax(np.convolve(env, np.ones(w) / w, "same"))) / SR
            elif align == "onset" and pk > 0:
                i20, i90 = int(np.argmax(env >= 0.2 * pk)), int(np.argmax(env >= 0.9 * pk))
                meas = at + i20 / SR if (i90 - i20) / SR < 0.05 else None
            self.ev.append(dict(sid=self.sid, t=self.t0 + (at if sync is None else sync), label=label,
                                meas=None if meas is None else self.t0 + meas, bus=bus))

    def mark(self, t, label):
        """An event with no sound of its own (a cue answered by a phrase, a series, a silence)."""
        self.ev.append(dict(sid=self.sid, t=self.t0 + t, label=label, meas=None, bus=None))

    def note(self, c, text):
        """A cue realised only in part, or by an approximation: for the report."""
        self.notes.append((self.sid, float(c["t"]) if isinstance(c, dict) else float(c),
                           c["sfx"] if isinstance(c, dict) else "", text))

    def cover(self, *words):
        for i, c in enumerate(self.cues):
            if any(w in c["text"] or w == c["sfx"] for w in words):
                self.covered.add(i)

    def cover_span(self, a, b, *words):
        for i, c in enumerate(self.cues):
            if a - FRAME <= c["t"] <= b + FRAME and any(w in c["text"] or w == c["sfx"] for w in words):
                self.covered.add(i)

    def end(self):
        """Spotting: the foley handlers for every cue the section left (rest), then realise every
        cue of this scene nothing answered; commit the section."""
        rest(self)
        if FROM_BIBLE.get(self.sid):
            warn(f"{self.sid}: not in the module yet, taken from the bible: "
                 f"{', '.join(dict.fromkeys(FROM_BIBLE[self.sid]))}")
        mine = [e["t"] - self.t0 for e in self.ev if e["sid"] == self.sid]
        for i, c in enumerate(self.cues):
            if i in self.covered or i in self.done or any(abs(t - c["t"]) <= FRAME + 1e-6 for t in mine):
                self.report.append((self.sid, c, "section"))
                continue
            how = realize(self, c)
            self.report.append((self.sid, c, how))
            if how.startswith("auto"):
                print(f"  {self.sid} {c['t']:6.3f}  auto: {c['text'][:70]!r} -> {how[6:]}")
            elif not how.startswith("silence"):
                warn(f"{self.sid} {c['t']:.3f}: cue {c['text']!r} not realised ({how})")
        self.commit()


SECTIONS = []


def section(sid):
    def deco(fn):
        SECTIONS.append((sid, fn))
        return fn
    return deco


# ============================================================================ helpers
norm, tax, cut, onset_at, pitch = OF.norm, OF.tax, OF.cut, OF.onset_at, OF.pitch
fx = OF.fx
TWO_PI = 2.0 * np.pi


def rng(*keys):
    return dsp.rng_for("thin-ice", *keys)


def lvl(x, target=REF, cap=-4.0, bed=False):
    """x at the catalog's level: its loudest 400 ms (a bed: its integrated loudness) at target LUFS,
    its peak never over cap dBFS (so a cue's gain_db means what it means for a catalog sound)."""
    x = np.asarray(x, np.float64)
    if x.size == 0 or not np.any(x):
        return x
    if bed and len(x) >= n_of(0.8):
        lv = dsp.loudness_integrated(x)
    else:
        y = x if len(x) >= n_of(0.4) else dsp.pad_to(x, n_of(0.4))
        _, lk = dsp.loudness_curve(y, win=0.4, hop=0.05)
        lv = float(np.max(lk)) if len(lk) else -70.0
    if not np.isfinite(lv) or lv < -100.0:
        return x
    x = x * db2lin(target - lv)
    pk = float(np.max(np.abs(x)))
    if cap is not None and pk > db2lin(cap):
        x = x * (db2lin(cap) / pk)
    return x


def env(x, pts):
    """x shaped by a breakpoint envelope [(s, gain)]."""
    x = np.asarray(x, np.float64)
    e = dsp.env_bp(pts, len(x))
    return x * (e[:, None] if x.ndim == 2 else e)


def env_db(x, pts):
    """x shaped by a breakpoint envelope in dB [(s, dB)] (-120: nothing)."""
    x = np.asarray(x, np.float64)
    e = dsp.env_bp_db(pts, len(x))
    return x * (e[:, None] if x.ndim == 2 else e)


def mix_at(y, x, t, gain=1.0):
    """x added into y at t seconds (mono into mono, anything into stereo)."""
    dsp.mix_into(y, np.asarray(x, np.float64) * gain, n_of(t))
    return y


def lp(x, f, order=2):
    return dsp.sos(np.asarray(x, np.float64), "lowpass", f, order)


def hpf(x, f, order=2):
    return dsp.sos(np.asarray(x, np.float64), "highpass", f, order)


def bp(x, lo, hi, order=2):
    return dsp.bandpass(np.asarray(x, np.float64), lo, hi, order)


def swell(n, dur):
    """A sine swell over dur seconds (n samples)."""
    return np.sin(np.pi * np.clip(tax(n) / max(dur, 1e-6), 0.0, 1.0))


ROOMS = {        # scene -> [(from scene time, reverb, wet dB)]: where its foley sounds
    "s01": [(0.0, "street", -26.0)],
    "s02": [(0.0, "street", -25.0)],
    "s03": [(0.0, "small_room", -15.0), (6.25, "street", -22.0), (14.0, "court", -23.0)],
    "s04": [(0.0, "court", -24.0), (14.0, "street", -26.0)],
    "s05": [(0.0, "street", -25.0)],
    "s06": [(0.0, "street", -25.0)],
    "s07": [(0.0, "street", -24.0)],
    "s08": [(0.0, "street", -22.0), (1.9, "cell", -14.0), (7.0, "street", -22.0)],
    "s09": [(0.0, "street", -25.0)],
    "s10": [(0.0, "street", -25.0)],
    "s11": [(0.0, "street", -25.0)],
    "s12": [(0.0, "street", -25.0), (5.9, "small_room", -17.0)],
}


def room(m, t):
    kind, wet = "street", -24.0
    for t0, k, w in ROOMS.get(m.sid, ()):
        if t >= t0 - 1e-6:
            kind, wet = k, w
    return kind, wet


def cg(c, extra=0.0):
    """A cue's gain in this mix: the loudest cues (over -10 dB) brought in a little (0.6 dB a dB), so
    the hits keep their order without leaning on the limiter."""
    g0 = float(c["gain_db"])
    if g0 > -10.0:
        g0 = -10.0 + 0.6 * (g0 + 10.0)
    return g0 + CUE_TRIM + extra


def bedg(c, extra=0.0):
    """A bed's gain (wind, river, the motor): its cue's, lifted to the film's floor."""
    return c["gain_db"] + CUE_TRIM + BED_LIFT + extra


def each(m, *tags, words=None, t0=None, t1=None):
    """This scene's cues with one of these tags (or words), marked answered: [(t, dur, cue)]."""
    out = []
    for i, c in enumerate(m.cues):
        if c["sfx"] in tags or (words and any(w in c["text"] for w in words)):
            if (t0 is not None and c["t"] < t0 - 1e-6) or (t1 is not None and c["t"] > t1 + 1e-6):
                continue
            m.done.add(i)
            out.append((c["t"], float(c.get("dur") or 0.0), c))
    return out


def peek(m, *tags):
    """This scene's cues with one of these tags, not marked: [(t, dur, cue)]."""
    return [(c["t"], float(c.get("dur") or 0.0), c) for c in m.cues if c["sfx"] in tags]


def fol(m, x, t, gain, pan=0.0, label=None, bus="efx", wet=None, kind=None, room_=True, align="onset", sync=None,
        key=False, lpf=None, hall="auto"):
    """A sound x (mono or stereo) at scene time t: low-passed (lpf), panned, in the scene's room
    (kind/wet override), on bus."""
    x = np.asarray(x, np.float64)
    if not x.size:
        return
    if float(np.max(np.abs(x))) > 0.7:     # a peak-normalised sound: to the catalog's level first
        x = lvl(x)
    if lpf:
        x = lp(x, lpf)
    y = dsp.pan_mono(x, pan) if x.ndim == 1 else (dsp.pan_stereo(x, pan) if pan else x)
    if room_:
        k, w = room(m, t)
        if len(y) > n_of(0.01):
            y = dsp.fade(y, 0.0005, 0.003, shape="lin")
        y = dsp.reverb(y, kind or k, wet_db=w if wet is None else wet, seed=int(abs(t) * 10) % 5)
    m.put(bus, y, t, gain, pan=0.0, label=label, align=align, sync=sync, key=key, hall=hall)


# ============================================================================ the recordings (breath, gasps, the fall, the grunt)
@lru_cache(maxsize=None)
def rec(name, a=0.0, b=None, semis=0.0, lpf=None, hpf_=None, fin=0.02, fout=0.08, trem=0.0, rate=7.0):
    """A cut [a, b) s of a recording (OPPOSITE's gen/, or grunt_knight's take), its edges faded;
    semis: resampled (pitch and speed together); trem: a shake (amplitude, at rate Hz); at REF."""
    if name == "grunt_knight":
        x = DC.take(name)
        x = x[n_of(a): (n_of(b) if b is not None else len(x))].copy()
    else:
        x = OPP.gen(name, a, b, fade=0.0)
    x = dsp.fade(x, fin, fout)
    if semis:
        x = pitch(x, semis)
    if hpf_:
        x = hpf(x, hpf_)
    if lpf:
        x = lp(x, lpf)
    if trem:
        t = tax(len(x))
        x = x * (1.0 - trem * (0.5 + 0.5 * np.sin(TWO_PI * rate * t)))
    return lvl(x)


@lru_cache(maxsize=None)
def rec_loop(name, dur, a=0.0, b=None, semis=0.0, lpf=None, offset=0.0, xf=0.18, trem=0.0):
    """A recording looped to dur seconds (from offset s into it), crossfaded at the joins; at REF."""
    x = np.asarray(rec(name, a, b, semis, lpf, None, 0.02, 0.02, trem), np.float64)
    out = x[n_of(offset):] if n_of(offset) < len(x) - n_of(0.5) else x
    while len(out) < n_of(dur):
        out = dsp.concat_xfade(out, x, n_of(xf))
    return lvl(dsp.fade(out[:n_of(dur)], 0.04, 0.12), bed=True)


# her_breath: quick frightened breathing (6 s); his_breath: one big breath (in 1.25-1.9, out 1.9-2.9);
# gasp_a, gasp_b: gasps (a woman's: down 5 semitones for the guard, up 3 for the girl)
def b_her(dur, offset=0.0, semis=0.0, lpf=5000.0, trem=0.0):
    return rec_loop("her_breath", round(dur, 3), 0.0, 5.95, semis, lpf, round(offset, 3), 0.18, trem)


def b_girl(dur, offset=1.7):
    return rec_loop("her_breath", round(dur, 3), 0.0, 5.95, 3.0, 6000.0, round(offset, 3), 0.12, 0.0)


def b_guard(dur, offset=0.0, quick=False):
    """The guard's heavy breathing: his big breath (in, out) again and again, a little lower;
    slower than theirs (quick: hurrying, through his moustache)."""
    x = rec("his_breath", 1.2, 2.95, -2.0 if not quick else -1.0, 2600.0 if quick else 3800.0, 80.0, 0.04, 0.12)
    gap = 0.15 if quick else 0.45
    unit = np.concatenate([np.asarray(x), np.zeros(n_of(gap))])
    reps = int(dur / (len(unit) / SR)) + 2
    out = np.tile(unit, reps)
    k = n_of(offset) % len(unit)
    out = out[k:k + n_of(dur)]
    return lvl(dsp.fade(out, 0.05, 0.15), bed=True)


def b_man_pant(dur, offset=0.0, far_=False):
    """His ragged panting in the cold: her quick breaths taken down five semitones (a big man)."""
    return rec_loop("her_breath", round(dur, 3), 0.0, 5.95, -5.0, 2400.0 if far_ else 3400.0, round(offset, 3), 0.15)


def gasp_man(seed=0, choke=False):
    x = rec("gasp_a" if seed % 2 == 0 else "gasp_b", 0.0, 0.62, -5.0, 3600.0, 90.0, 0.005, 0.12)
    return dsp.fade(np.asarray(x)[:n_of(0.32)], 0.0, 0.08) if choke else x


GRUNTS = ((5.06, 5.76, 0.168), (0.10, 1.64, 0.257), (0.28, 0.95, 0.10))   # (a, b, onset) in grunt_knight


def grunt(m, t, gain, k=0, pan=0.0, label=None):
    """His grunt, the recorded take: 0 short, 1 strained and held, 2 a shorter strain."""
    a, b, on = GRUNTS[k % 3]
    x = lp(rec("grunt_knight", a, b, 0.0, None, 80.0, 0.03, 0.25 if k == 1 else 0.12), 7000.0)
    fol(m, x, t - on, gain, pan, label, bus="vox", key=True, align=None, sync=t)


def breathe(m, x, t, gain, pan=0.0, label=None, lpf=None, wet=None, kind=None):
    fol(m, x, t, gain, pan, label, bus="vox", key=True, align=None, lpf=lpf, wet=wet, kind=kind)


# ============================================================================ the ice (the film's signature)
def _chirp(n, f_hi, f_lo, tau, r):
    """A dispersive sweep: f(t) = f_lo + (f_hi - f_lo) (tau / (tau + t))^2 (high notes first)."""
    t = tax(n)
    return np.sin(TWO_PI * (f_lo * t + (f_hi - f_lo) * tau * t / (tau + t)) + r.uniform(0, TWO_PI))


@lru_cache(maxsize=None)
def pew(dur=0.3, f_hi=7000.0, f_lo=320.0, seed=0, echoes=2):
    """Lake ice's dispersive chirp: a crack's impulse runs through the sheet as a flexural wave whose
    speed goes with the root of its frequency, so the high notes arrive first: a falling whistle,
    'pew'; again, fainter and longer, off the far edges (echoes)."""
    r = rng("pew", round(dur, 3), int(f_hi), int(f_lo), seed, echoes)
    n = n_of(dur * (1.0 + 1.2 * echoes) + 0.3)
    y = np.zeros(n)
    at = 0.0
    for k in range(echoes + 1):
        d = dur * (1.0 + 0.55 * k)
        m_ = n_of(d + 0.06)
        t = tax(m_)
        tau = d / 6.5
        fh = f_hi * (0.82 ** k)
        x = _chirp(m_, fh, f_lo * (0.93 ** k), tau, r) + 0.3 * _chirp(m_, fh * 1.004, f_lo * 1.02, tau * 1.05, r)
        e = np.clip(t / 0.0015, 0, 1) * np.exp(-t / (0.4 * d)) * np.clip((d + 0.06 - t) / 0.06, 0, 1)
        e *= 1.0 + 0.6 * np.exp(-((t - 0.55 * d) / (0.25 * d)) ** 2)        # the low 'oo' leans out a little
        dsp.mix_into(y, x * e * (0.5 ** k), n_of(at))
        at += 0.03 + 0.025 * r.uniform() + 0.35 * d
    c = sfx._click(r, 2500.0, 0.0015)
    y[:len(c)] += 0.35 * c / (np.max(np.abs(c)) + 1e-9)
    return norm(dsp.fade(hpf(y, 110.0), 0.0, 0.05))


@lru_cache(maxsize=None)
def ice_crack(size=1.0, seed=0, ring=1.0, pews=1, pew_len=0.0):
    """A crack in lake ice: the split (a hard broadband snap, its micro-fractures crackling for a few
    tens of ms), the sheet ringing (a glassy inharmonic ring), a thump under a big one, and the
    dispersive 'pew' running away from it."""
    r = rng("crack", round(size, 3), seed, round(ring, 3), pews, round(pew_len, 3))
    n = n_of(1.4 + 0.9 * size)
    y = np.zeros(n)
    snap = sfx._burst(n_of(0.05), r, 900.0, 15000.0, t60=0.012 * (1.0 + size), attack=0.0001)
    y[:len(snap)] += norm(snap)
    c = sfx._click(r, 2000.0, 0.002)
    y[:len(c)] += 1.2 * c / (np.max(np.abs(c)) + 1e-9)
    m_ = n_of(0.03 + 0.1 * size)
    cr = bp(dsp.crackle(m_, 2500.0 + 2500.0 * size, r), 1200.0, 10000.0) * np.exp(-tax(m_) / (0.02 + 0.035 * size))
    y[:m_] += 0.8 * norm(cr)
    rg = sfx._hit(r, np.array([640.0, 1310.0, 2210.0, 3380.0, 4870.0]) * r.uniform(0.9, 1.1),
                  np.array([0.35, 0.25, 0.16, 0.1, 0.06]) * ring * (0.6 + 0.4 * size), spread=0.03, click=0.0)
    y[:len(rg)] += 0.32 * norm(rg)
    if size >= 0.6:
        th = sfx._thump(n_of(0.6), 110.0, 40.0, 0.02, 0.18 + 0.14 * size)
        y[:len(th)] += 0.55 * min(size, 1.4) * th
    for k in range(pews):
        d = round((pew_len or (0.2 + 0.12 * size)) * (1.0 + 0.35 * k), 3)
        p = pew(d, 7800.0 - 1300.0 * k, 300.0 + 70.0 * k, seed + 7 * k, 1 + int(size > 0.9))
        dsp.mix_into(y, (0.62 - 0.14 * k) * p, n_of(0.006 + 0.05 * k))
    return norm(dsp.fade(y, 0.0, 0.2))


@lru_cache(maxsize=None)
def ice_groan(dur=2.0, seed=0, deep=1.0):
    """The ice groaning: a slow stick-slip through the sheet's low resonances (a long wooden moan),
    a low tone bending under it, a few faint chirps; it swells and dies away."""
    r = rng("groan", round(dur, 2), seed, round(deep, 2))
    n = n_of(dur)
    t = tax(n)
    sw = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.2
    rate = np.maximum((13.0 + 24.0 * sw + 7.0 * dsp.smooth_noise(n, 1.5, r)) / deep, 3.0)
    body = [(64.0 / deep, 5, 1.0), (121.0 / deep, 6, 0.8), (210.0 / deep, 7, 0.55), (395.0 / deep, 9, 0.3),
            (730.0, 11, 0.12)]
    fr = dsp.friction(n, rate, r, jitter=0.35, body=body)
    f = (56.0 + 15.0 * np.sin(np.pi * np.clip(t / dur, 0, 1)) + 4.0 * dsp.smooth_noise(n, 0.8, r)) / deep
    tone = lp(dsp.saw(f, n), 360.0) * (0.5 + 0.5 * np.abs(dsp.smooth_noise(n, 3.0, r)))
    y = norm(fr) + 0.45 * norm(tone)
    for k in range(1 + int(dur)):
        p = pew(round(r.uniform(0.18, 0.32), 3), r.uniform(2800.0, 5200.0), r.uniform(240.0, 420.0), seed + 31 * k, 1)
        dsp.mix_into(y, 0.12 * p, n_of(r.uniform(0.15, 0.8) * dur))
    return norm(dsp.fade(hpf(y * sw, 32.0), 0.05, 0.2))


@lru_cache(maxsize=None)
def ice_boom(dur=2.2, seed=0):
    """The sheet booming: a deep thud, a long low chirp running away under the ice, its rumble
    rolling off into the distance."""
    r = rng("boom", round(dur, 2), seed)
    n = n_of(dur + 0.3)
    t = tax(n)
    y = np.zeros(n)
    th = sfx._thump(n_of(1.0), 96.0, 33.0, 0.05, 0.7)
    y[:len(th)] += th
    m_ = n_of(min(1.3, dur * 0.6))
    tm = tax(m_)
    ch = _chirp(m_, 1100.0, 58.0, (m_ / SR) / 5.0, r) * np.clip(tm / 0.008, 0, 1) * np.exp(-tm / (0.45 * m_ / SR))
    y[:m_] += 0.55 * ch
    rb = norm(lp(dsp.brown(n, r), 190.0)) * np.exp(-t / (0.45 * dur)) * np.clip(t / 0.05, 0, 1)
    y += 0.6 * rb
    fr = dsp.friction(n, 18.0 + 12.0 * np.exp(-t / 0.8), r, jitter=0.4, body=[(68.0, 5, 1.0), (128.0, 6, 0.7),
                                                                            (236.0, 8, 0.4)])
    y += 0.35 * norm(fr) * np.exp(-t / (0.35 * dur))
    for k in range(3):
        p = pew(round(0.36 + 0.16 * k, 3), 4200.0 - 800.0 * k, 190.0, seed + 13 * k, 1)
        dsp.mix_into(y, 0.2 * p * (0.7 ** k), n_of(0.04 + 0.32 * k + r.uniform(0, 0.08)))
    return norm(dsp.fade(hpf(y, 26.0), 0.0, 0.3))


@lru_cache(maxsize=None)
def ice_break(seed=0, dur=1.1):
    """The slab giving way: cracks running into each other, the sheet shattering and crunching (a
    dense crackle of fragments, chunks knocking together), the collapse's low thud."""
    r = rng("break", seed, dur)
    n = n_of(dur + 1.2)
    y = np.zeros(n)
    for k, (tt, s) in enumerate(((0.0, 1.1), (0.07, 0.8), (0.17, 0.9), (0.28, 0.6), (0.42, 0.5))):
        dsp.mix_into(y, (1.0 - 0.12 * k) * ice_crack(s, seed * 7 + k, 0.6, 1), n_of(tt))
    m_ = n_of(dur)
    tm = tax(m_)
    cr = norm(bp(dsp.crackle(m_, 1500.0, r, amp_spread=1.2), 450.0, 7500.0)) * np.clip(tm / 0.03, 0, 1) * \
        np.exp(-tm / (0.35 * dur))
    y[:m_] += 0.65 * cr
    for k in range(10):
        tt = 0.06 + r.exponential(0.28)
        if tt < dur:
            h = sfx._hit(r, np.array([380.0, 820.0, 1500.0, 2400.0]) * r.uniform(0.8, 1.25), [0.08, 0.06, 0.04, 0.03],
                         click=0.4)
            dsp.mix_into(y, 0.3 * r.uniform(0.4, 1.0) * norm(h), n_of(tt))
    th = sfx._thump(n_of(0.7), 86.0, 36.0, 0.03, 0.4)
    dsp.mix_into(y, 0.85 * th, n_of(0.05))
    return norm(dsp.fade(y, 0.0, 0.25))


@lru_cache(maxsize=None)
def ice_crumble(seed=0, size=0.5):
    """A piece of the edge cracking and breaking away: a small crack, crumbs, the piece knocking."""
    r = rng("crumble", seed, size)
    y = np.zeros(n_of(1.4))
    dsp.mix_into(y, ice_crack(round(0.35 + 0.4 * size, 3), seed, 0.7, 1), 0)
    m_ = n_of(0.25)
    cr = norm(bp(dsp.crackle(m_, 900.0, r), 900.0, 7000.0)) * np.exp(-tax(m_) / 0.08)
    dsp.mix_into(y, 0.35 * cr, n_of(0.02))
    h = sfx._hit(r, np.array([520.0, 1150.0, 2100.0]) * r.uniform(0.85, 1.2), [0.06, 0.04, 0.03], click=0.5)
    dsp.mix_into(y, 0.3 * norm(h), n_of(0.09))
    return norm(y)


@lru_cache(maxsize=None)
def ice_tick(seed=0):
    """Weight settling on the band: a tiny dry tick in the ice, a breath of a chirp."""
    r = rng("itick", seed)
    y = np.zeros(n_of(0.4))
    h = sfx._hit(r, [2600.0, 4100.0, 6300.0], [0.012, 0.009, 0.006], click=1.0, n=n_of(0.05))
    y[:len(h)] += norm(h)
    dsp.mix_into(y, 0.18 * pew(0.1, 5000.0, 900.0, seed, 0), n_of(0.004))
    return norm(y)


@lru_cache(maxsize=None)
def ice_sing(dur=1.3, seed=0):
    """The ice singing: one long dispersive 'pew', a falling metallic whistle running out through the
    thin slab and away under the river, echoing off the far edges."""
    r = rng("sing", round(dur, 2), seed)
    n = n_of(dur + 0.6)
    y = np.zeros(n)
    dsp.mix_into(y, pew(round(0.42 * dur, 3), 8200.0, 210.0, seed, 3), 0)
    m_ = n_of(dur)
    t = tax(m_)
    long_ = _chirp(m_, 5200.0, 160.0, dur / 9.0, r) * np.clip(t / 0.004, 0, 1) * np.exp(-t / (0.5 * dur))
    long_ *= 1.0 + 0.25 * np.sin(TWO_PI * 9.0 * t)
    y[:m_] += 0.35 * long_
    return norm(dsp.fade(hpf(y, 120.0), 0.0, 0.2))


@lru_cache(maxsize=None)
def floe_grind(dur=0.75, seed=0):
    """Two floes grinding apart: ice dragging on ice (a coarse stick-slip, crunching), water lapping."""
    r = rng("floe", round(dur, 2), seed)
    n = n_of(dur + 0.6)
    m_ = n_of(dur)
    t = tax(m_)
    sw = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.8
    fr = dsp.friction(m_, 45.0 + 70.0 * sw, r, jitter=0.4, body=[(240.0, 5, 1.0), (560.0, 7, 0.7), (1300.0, 9, 0.4),
                                                                 (2900.0, 12, 0.2)])
    cr = bp(dsp.crackle(m_, 300.0, r), 1000.0, 6000.0)
    y = np.zeros(n)
    y[:m_] += (norm(fr) + 0.4 * norm(cr)) * sw
    dsp.mix_into(y, 0.5 * water_lap(round(dur + 0.3, 2), seed, 3.0, 0.35), n_of(0.15))
    return norm(dsp.fade(y, 0.01, 0.1))


# ============================================================================ water
@lru_cache(maxsize=None)
def splash(size=0.6, seed=0):
    """Water slapping up: the smack, the spray, the body of water thudding."""
    r = rng("splash", round(size, 2), seed)
    n = n_of(0.7 + 0.8 * size)
    y = sfx._splash(n, r, size=min(1.0, size))
    th = sfx._thump(n_of(0.35), 130.0 - 35.0 * size, 55.0, 0.015, 0.1 + 0.12 * size)
    y[:len(th)] += (0.3 + 0.5 * size) * th * np.max(np.abs(y))
    return norm(dsp.fade(y, 0.0, 0.1))


@lru_cache(maxsize=None)
def bubbles(dur=0.6, seed=0, muffle=0.0, rate=45.0):
    """A rush of bubbles (rising-pitch drops, thinning out); muffle: heard under water."""
    r = rng("bubbles", round(dur, 2), seed, round(muffle, 2), rate)
    n = n_of(dur + 0.3)
    y = np.zeros(n)
    for tt in dsp.poisson_times(lambda t: rate * math.exp(-t / (0.5 * dur)), dur, r):
        f0 = math.exp(r.uniform(math.log(320.0), math.log(1500.0)))
        d = sfx._drop(r, f0, r.uniform(0.006, 0.02), chirp=r.uniform(0.3, 0.9))
        dsp.mix_into(y, r.uniform(0.3, 1.0) * d, n_of(tt))
    if muffle:
        y = lp(y, 900.0 + 2600.0 * (1.0 - muffle))
    return norm(dsp.fade(y, 0.0, 0.1))


@lru_cache(maxsize=None)
def plunge(seed=0):
    """A heavy body into black water: the smack, the deep 'whoomp', the water closing over, bubbles."""
    r = rng("plunge", seed)
    n = n_of(2.2)
    y = np.zeros(n)
    sp = sfx._splash(n_of(1.2), r, size=1.0)
    y[:len(sp)] += norm(sp)
    th = sfx._thump(n_of(0.9), 78.0, 34.0, 0.04, 0.5)
    y[:len(th)] += 0.95 * th
    m_ = n_of(1.4)
    tm = tax(m_)
    rush = bp(dsp.pink(m_, r), 110.0, 1500.0) * np.clip(tm / 0.05, 0, 1) * np.exp(-tm / 0.35)
    dsp.mix_into(y, 0.5 * norm(rush), n_of(0.1))
    dsp.mix_into(y, 0.25 * bubbles(1.2, seed, 0.6), n_of(0.25))
    return norm(dsp.fade(y, 0.0, 0.3))


@lru_cache(maxsize=None)
def pour(dur=0.7, seed=0, size=1.0):
    """Water pouring off a body: a falling sheet of water, then drops."""
    r = rng("pour", round(dur, 2), seed, size)
    n = n_of(dur + 0.4)
    t = tax(n)
    x = bp(dsp.pink(n, r), 300.0, 5000.0) * np.clip(t / 0.03, 0, 1) * np.exp(-t / (0.4 * dur))
    d = np.zeros(n)
    for tt in dsp.poisson_times(lambda u: 60.0 * math.exp(-u / (0.6 * dur)), dur + 0.3, r):
        dd = sfx._drop(r, r.uniform(900.0, 3000.0), r.uniform(0.004, 0.01), chirp=0.5)
        dsp.mix_into(d, r.uniform(0.2, 1.0) * dd, n_of(tt))
    return norm(dsp.fade(norm(x) + 0.5 * size * norm(d), 0.005, 0.1))


@lru_cache(maxsize=None)
def surface_burst(seed=0, size=1.0):
    """Bursting up through the surface: water crashing off him, the splash, the pour."""
    y = np.zeros(n_of(1.6))
    dsp.mix_into(y, splash(round(0.9 * size, 2), seed), 0)
    dsp.mix_into(y, 0.8 * pour(0.9, seed, size), n_of(0.06))
    return norm(y)


@lru_cache(maxsize=None)
def water_lap(dur=1.0, seed=0, rate=2.5, size=0.5):
    """Small ripples lapping at an edge: soft slaps of water, a drop or two."""
    r = rng("lap", round(dur, 2), seed, rate, size)
    n = n_of(dur + 0.4)
    y = np.zeros(n)
    tt = r.uniform(0.0, 0.12)
    while tt < dur:
        m_ = n_of(0.2 + 0.1 * size)
        tm = tax(m_)
        x = bp(r.standard_normal(m_), 160.0 + 120.0 * r.uniform(), 900.0 + 700.0 * size) * \
            np.clip(tm / 0.018, 0, 1) * np.exp(-tm / (0.05 + 0.04 * size))
        dsp.mix_into(y, r.uniform(0.5, 1.0) * norm(x), n_of(tt))
        if r.uniform() < 0.6:
            dsp.mix_into(y, 0.3 * sfx._drop(r, r.uniform(500.0, 1300.0), 0.012, 0.5), n_of(tt + r.uniform(0.02, 0.1)))
        tt += (0.6 + 0.8 * r.uniform()) / rate
    return norm(dsp.fade(y, 0.01, 0.1))


@lru_cache(maxsize=None)
def welling(dur=0.8, seed=0):
    """Black water welling up through a hole: a soft gurgle and slosh, bubbles rising."""
    r = rng("well", round(dur, 2), seed)
    n = n_of(dur + 0.3)
    y = np.zeros(n)
    for tt in dsp.poisson_times(12.0, dur, r):
        dsp.mix_into(y, r.uniform(0.4, 1.0) * sfx._drop(r, r.uniform(140.0, 380.0), r.uniform(0.02, 0.05), 0.7),
                     n_of(tt))
    sl = bp(dsp.pink(n, r), 150.0, 1200.0) * swell(n, dur)
    y = norm(y) + 0.45 * norm(sl)
    dsp.mix_into(y, 0.25 * bubbles(round(dur, 2), seed + 1, 0.3, 25.0), n_of(0.1))
    return norm(dsp.fade(y, 0.02, 0.1))


@lru_cache(maxsize=None)
def trickle(dur=1.2, seed=0):
    """Water trickling out of a watch case onto snow: a thin run of tiny drops."""
    r = rng("trickle", round(dur, 2), seed)
    n = n_of(dur + 0.2)
    y = np.zeros(n)
    for tt in dsp.poisson_times(lambda u: 38.0 * math.exp(-u / (0.7 * dur)), dur, r):
        dsp.mix_into(y, r.uniform(0.3, 1.0) * sfx._drop(r, r.uniform(1300.0, 3200.0), r.uniform(0.003, 0.008), 0.4),
                     n_of(tt))
    th = bp(r.standard_normal(n), 1200.0, 4500.0) * np.exp(-tax(n) / (0.5 * dur)) * 0.15
    return norm(dsp.fade(lp(norm(y) + th, 6000.0), 0.01, 0.1))


@lru_cache(maxsize=None)
def drips(dur=2.6, seed=0, rate=2.8):
    """Water dripping off a coat onto snow: soft taps, now and then a tiny plink."""
    r = rng("drips", round(dur, 2), seed, rate)
    n = n_of(dur + 0.2)
    y = np.zeros(n)
    tt = r.uniform(0.02, 0.2)
    while tt < dur:
        tap = sfx._burst(n_of(0.02), r, 400.0, 2400.0, t60=0.008, attack=0.0003)
        dsp.mix_into(y, r.uniform(0.4, 1.0) * norm(tap), n_of(tt))
        if r.uniform() < 0.35:
            dsp.mix_into(y, 0.25 * sfx._drop(r, r.uniform(1500.0, 2600.0), 0.004, 0.4), n_of(tt + 0.002))
        tt += r.uniform(0.18, 0.55) * 2.8 / rate
    return norm(dsp.fade(y, 0.0, 0.05))


def river_bed(dur, seed=0):
    """The river under the ice: deep water's steady muffled rush, slow surges, a gurgle now and then."""
    r = rng("river", round(dur, 2), seed)
    n = n_of(dur)
    out = np.zeros((n, 2))
    sm = 1.0 + 0.22 * dsp.smooth_noise(n, 0.35, r)
    for ch in range(2):
        b = lp(dsp.brown(n, r), 260.0)
        p = bp(dsp.pink(n, r), 120.0, 650.0)
        out[:, ch] = (norm(b) + 0.4 * norm(p)) * sm
    gur = np.zeros(n)
    for tt in dsp.poisson_times(1.3, dur, r):
        dsp.mix_into(gur, r.uniform(0.3, 1.0) * sfx._drop(r, r.uniform(110.0, 260.0), r.uniform(0.03, 0.07), 0.8),
                     n_of(tt))
    if np.any(gur):
        out += 0.22 * norm(lp(gur, 700.0))[:, None]
    return out


def underwater(dur, seed=0):
    """Under the ice: the current's heavy muffled roar, surging; a slow churn in it."""
    r = rng("under", round(dur, 2), seed)
    n = n_of(dur)
    out = np.zeros((n, 2))
    surge = 1.0 + 0.35 * dsp.smooth_noise(n, 0.6, r)
    for ch in range(2):
        b = lp(dsp.brown(n, r), 210.0)
        p = lp(dsp.pink(n, r), 430.0)
        out[:, ch] = (norm(b) + 0.55 * norm(p)) * surge
    churn = dsp.tv_bandpass(dsp.pink(n, r), 170.0 + 130.0 * (0.5 + 0.5 * dsp.smooth_noise(n, 0.4, r)), q=1.4,
                            block=256)
    out += 0.3 * norm(churn)[:, None]
    return out


# ============================================================================ the snow underfoot
STEPS = {        # crunch(): the boot in the snow, by who and where
    "mother":       dict(dur=0.15, lo=750.0, hi=5200.0, rate=2400.0, thud=(120.0, 75.0, 0.25), roll=0.06, squeak=0.2),
    "mother_run":   dict(dur=0.12, lo=700.0, hi=5200.0, rate=2600.0, thud=(115.0, 72.0, 0.35), roll=0.04),
    "mother_deep":  dict(dur=0.24, lo=550.0, hi=4200.0, rate=2200.0, thud=(105.0, 65.0, 0.4), roll=0.08, drag=0.12,
                         squeak=0.1),
    "mother_heavy": dict(dur=0.28, lo=480.0, hi=3800.0, rate=2400.0, thud=(95.0, 58.0, 0.55), roll=0.09, drag=0.08),
    "mother_ice":   dict(dur=0.1, lo=900.0, hi=6000.0, rate=2600.0, thud=(150.0, 95.0, 0.2), roll=0.05, ring=0.18,
                         pewf=0.06),
    "mother_far":   dict(dur=0.14, lo=700.0, hi=4200.0, rate=2200.0, thud=(120.0, 75.0, 0.2), roll=0.06, soft=0.35),
    "backtrack":    dict(dur=0.2, lo=600.0, hi=3500.0, rate=1800.0, thud=(110.0, 70.0, 0.25), roll=0.08, soft=0.5),
    "soft":         dict(dur=0.24, lo=550.0, hi=3000.0, rate=1500.0, thud=(105.0, 68.0, 0.25), roll=0.1, soft=0.6),
    "girl":         dict(dur=0.085, lo=1300.0, hi=7200.0, rate=2800.0, thud=(170.0, 110.0, 0.12), roll=0.0,
                         squeak=0.15),
    "girl_run":     dict(dur=0.075, lo=1300.0, hi=7200.0, rate=3000.0, thud=(170.0, 110.0, 0.15), roll=0.0),
    "girl_deep":    dict(dur=0.12, lo=1100.0, hi=6500.0, rate=2600.0, thud=(150.0, 100.0, 0.18), roll=0.04,
                         drag=0.05),
    "girl_land":    dict(dur=0.09, lo=1100.0, hi=6500.0, rate=2600.0, thud=(160.0, 100.0, 0.3), roll=0.0),
    "guard":        dict(dur=0.3, lo=380.0, hi=3300.0, rate=3000.0, thud=(92.0, 52.0, 0.85), roll=0.11, grit=4,
                         squeak=0.1),
    "guard_run":    dict(dur=0.22, lo=400.0, hi=3500.0, rate=3200.0, thud=(95.0, 54.0, 0.85), roll=0.07, grit=3),
    "guard_ice":    dict(dur=0.14, lo=650.0, hi=5200.0, rate=2800.0, thud=(120.0, 70.0, 0.6), roll=0.05, grit=3,
                         ring=0.4, pewf=0.12),
    "kneel":        dict(dur=0.3, lo=300.0, hi=2500.0, rate=1600.0, thud=(95.0, 55.0, 0.5), roll=0.0, soft=0.3),
}
STEP_DRAG = {k: v.get("drag", 0.0) for k, v in STEPS.items()}


@lru_cache(maxsize=None)
def crunch(dur=0.16, lo=700.0, hi=5000.0, rate=2200.0, thud=(110.0, 70.0, 0.3), roll=0.07, drag=0.0, squeak=0.0,
           grit=0, ring=0.0, pewf=0.0, soft=0.0, seed=0):
    """A boot in snow: the snow's crystals giving way (a dense crackle through the boot's band, heel
    then toe, roll s apart), the weight's thud under it; a drag before it (wading through deep snow);
    a dry squeak (cold snow); hobnails' iron grit; the hollow ring of ice under thin snow and its
    faint chirp; soft: muffled (careful, or far)."""
    r = rng("crunch", dur, lo, hi, rate, thud, roll, drag, squeak, grit, ring, pewf, soft, seed)
    pre = n_of(drag)
    n = pre + n_of(dur + 0.3)
    y = np.zeros(n)
    m_ = n_of(dur)
    t = tax(m_)
    e = np.clip(t / 0.006, 0, 1) * np.exp(-t / (0.35 * dur))
    if roll:
        e = e + 0.7 * np.clip((t - roll) / 0.008, 0, 1) * np.exp(-np.clip(t - roll, 0, None) / (0.3 * dur))
    e *= np.clip((dur - t) / 0.02, 0, 1)
    gr = bp(dsp.crackle(m_, rate, r, amp_spread=0.8), lo, hi)
    nz = bp(r.standard_normal(m_), lo * 0.8, hi * 0.8)
    y[pre:pre + m_] += norm((norm(gr) + 0.35 * norm(nz)) * e)
    if thud[2] > 0:
        th = sfx._thump(n_of(0.22), thud[0], thud[1], 0.01, 0.06 + 0.1 * thud[2])
        y[pre:pre + len(th)] += thud[2] * th
    if drag > 0 and pre > 8:
        d = tax(pre)
        dg = bp(dsp.pink(pre, r), 300.0, 2500.0) * (d / drag) ** 1.5
        dg = norm(dg) + 0.5 * norm(bp(dsp.crackle(pre, 600.0, r), 800.0, 4000.0)) * (d / drag) ** 2
        y[:pre] += 0.3 * norm(dg)
    if squeak > 0:
        sq_n = n_of(0.05 + 0.05 * r.uniform())
        sq = dsp.friction(sq_n, 700.0 + 400.0 * r.uniform(), r, jitter=0.1,
                          body=[(1500.0 * r.uniform(0.85, 1.2), 9, 1.0), (2700.0, 11, 0.4)])
        sq = norm(sq) * swell(sq_n, sq_n / SR)
        dsp.mix_into(y, squeak * sq, pre + n_of(roll * 0.5))
    for k in range(grit):
        h = sfx._hit(r, np.array([3200.0, 4700.0, 6800.0]) * r.uniform(0.85, 1.15), [0.012, 0.009, 0.006], click=0.6,
                     n=n_of(0.03))
        dsp.mix_into(y, 0.18 * r.uniform(0.5, 1.0) * norm(h), pre + n_of(r.uniform(0.0, 0.04)))
    if ring > 0:
        rg = sfx._hit(r, np.array([210.0, 480.0, 860.0, 1400.0]) * r.uniform(0.9, 1.1), [0.16, 0.12, 0.08, 0.05],
                      click=0.0)
        dsp.mix_into(y, ring * norm(rg), pre + n_of(0.004))
    if pewf > 0:
        dsp.mix_into(y, pewf * pew(0.12, 4500.0, 600.0, seed % 5, 0), pre + n_of(0.01))
    if soft > 0:
        y = lp(y, 5000.0 * (1.0 - soft) + 900.0)
    return lvl(dsp.fade(y, 0.002, 0.05))


def foot(kind, seed=0):
    return crunch(**STEPS[kind], seed=int(seed) % 8)


def step(m, kind, t, gain, pan=0.0, label=None, seed=None, lpf=None, wet=None):
    """One step of kind at scene time t (its crunch, not its drag, on t)."""
    sd = int(round(t * 1000)) if seed is None else seed
    pre = STEP_DRAG.get(kind, 0.0)
    fol(m, foot(kind, sd), t - pre, gain, pan, label, bus="feet", sync=t, lpf=lpf, wet=wet,
        align="onset" if not pre else None)


@lru_cache(maxsize=None)
def bare_ice_step(seed=0, knock=0.5):
    """A hobnailed boot set down on bare black ice: a hard ringing click, the sheet's ring and its
    chirp, the knock of the heel; a faint tick after."""
    r = rng("bare", seed, knock)
    y = np.zeros(n_of(0.9))
    h = sfx._hit(r, np.array([1150.0, 2350.0, 3700.0, 5600.0]) * r.uniform(0.95, 1.05), [0.3, 0.2, 0.12, 0.07],
                 click=1.0)
    y[:len(h)] += norm(h)
    th = sfx._thump(n_of(0.15), 180.0, 100.0, 0.008, 0.05)
    y[:len(th)] += knock * th
    dsp.mix_into(y, 0.25 * pew(0.18, 6000.0, 700.0, seed, 1), n_of(0.005))
    tk = sfx._hit(r, [2900.0, 4600.0], [0.02, 0.012], click=0.8, n=n_of(0.04))
    dsp.mix_into(y, 0.22 * norm(tk), n_of(0.33))
    return lvl(dsp.fade(y, 0.0, 0.1))


@lru_cache(maxsize=None)
def snow_whump(seed=0, size=1.0):
    """A body falling into deep powder: a soft heavy whump, the snow hissing as it settles."""
    r = rng("whump", seed, size)
    n = n_of(1.4)
    t = tax(n)
    y = np.zeros(n)
    th = sfx._thump(n_of(0.45), 82.0, 44.0, 0.02, 0.22)
    y[:len(th)] += th
    m_ = n_of(0.35)
    b = bp(dsp.pink(m_, r), 200.0, 1800.0) * np.clip(tax(m_) / 0.01, 0, 1) * np.exp(-tax(m_) / 0.09)
    y[:m_] += 0.8 * norm(b)
    hs = (norm(hpf(bp(dsp.crackle(n, 700.0, r), 1800.0, 8000.0), 1500.0)) + 0.5 * norm(bp(dsp.pink(n, r), 2000.0, 8000.0)))
    y += 0.22 * size * hs * np.clip((t - 0.05) / 0.1, 0, 1) * np.exp(-np.clip(t - 0.05, 0, None) / 0.35)
    return lvl(dsp.fade(y, 0.001, 0.1))


@lru_cache(maxsize=None)
def snow_dig(seed=0):
    """A mitten digging into crusted snow; a stone scraped loose from the frozen ground."""
    r = rng("dig", seed)
    y = np.zeros(n_of(0.7))
    dsp.mix_into(y, foot("kneel", seed), 0)
    m_ = n_of(0.26)
    sc = dsp.friction(m_, 260.0 + 200.0 * swell(m_, 0.26), r, jitter=0.3, body=[(1200.0, 6, 1.0), (2600.0, 8, 0.6),
                                                                              (4200.0, 10, 0.3)])
    dsp.mix_into(y, 0.6 * norm(sc) * swell(m_, 0.26), n_of(0.14))
    return lvl(y)


@lru_cache(maxsize=None)
def crawl(dur=1.3, seed=0, every=0.28, heavy=0.3, bark=False):
    """Crawling: elbow and knee, elbow and knee - snow pressed and shuffled (or coat on bark), cloth."""
    r = rng("crawl", round(dur, 2), seed, every, heavy, bark)
    n = n_of(dur + 0.4)
    y = np.zeros(n)
    tt, k = 0.02, 0
    while tt < dur:
        if bark:
            m_ = n_of(0.16)
            x = bp(r.standard_normal(m_), 350.0, 3200.0) * swell(m_, 0.16) * (0.6 + 0.4 * np.abs(dsp.smooth_noise(m_, 60.0, r)))
            dsp.mix_into(y, (0.8 + 0.2 * r.uniform()) * norm(x), n_of(tt))
        else:
            dsp.mix_into(y, (0.7 if k % 2 else 1.0) * np.asarray(foot("soft" if heavy > 0.5 else "girl_deep", seed + k)),
                         n_of(tt))
        dsp.mix_into(y, 0.4 * DC.cloth(0.2, (seed + k) % 5, heavy), n_of(tt + 0.02))
        tt += every * (0.85 + 0.3 * r.uniform())
        k += 1
    return lvl(dsp.fade(y, 0.005, 0.08))


# ============================================================================ wind, snow, the river, the motor (beds)
@lru_cache(maxsize=None)
def branch_snow(seed=0):
    """Snow sliding off a branch: a soft 'fffsh', the clump landing."""
    r = rng("bsnow", seed)
    n = n_of(0.9)
    t = tax(n)
    x = norm(bp(dsp.pink(n, r), 400.0, 4000.0) * np.clip(t / 0.08, 0, 1) * np.exp(-t / 0.25))
    x += 0.5 * norm(bp(dsp.crackle(n, 500.0, r), 1500.0, 6000.0) * np.exp(-t / 0.2))
    th = sfx._thump(n_of(0.2), 110.0, 70.0, 0.02, 0.1)
    dsp.mix_into(x, 0.4 * th, n_of(0.32))
    return norm(dsp.fade(x, 0.01, 0.1))


def snow_hiss_bed(n, r):
    """Falling snow: the faintest high hiss, flakes ticking on snow."""
    out = np.zeros((n, 2))
    for ch in range(2):
        h = hpf(dsp.pink(n, r), 3500.0)
        gr = hpf(dsp.crackle(n, 900.0, r, amp_spread=0.6), 5000.0)
        out[:, ch] = norm(h) + 0.3 * norm(gr)
    return out


def _bed_curve(t0, t1, pts, xf):
    a, b = t0 - xf, t1 + xf
    n = n_of(b - a)
    pts = sorted((float(t), float(v)) for t, v in pts)
    ext = [(a, pts[0][1])] + pts + [(b, pts[-1][1])]
    db = dsp.env_bp([(t - a, max(v, -120.0)) for t, v in ext], n)
    top = float(np.max(db))
    amp = db2lin(db - top)
    amp[db <= -119.0] = 0.0
    return a, n, amp, top


def wind_layer(m, t0, t1, pts, kind="open", seed=0, label=None, xf=0.3, gain=0.0):
    """The wind from t0 to t1 (scene time; a crossfade's worth past either end, so the scenes join),
    its level following pts [(t, cue dB)] (-120: none); kind 'open' (over the snow, the river),
    'pines' (high in the trees: a hiss of needles, snow sliding off a branch now and then), 'muffled'
    (through the hut's walls), 'lee' (the farmhouse's shelter), 'snow' (falling snow's hiss in it)."""
    if not pts or t1 <= t0:
        return
    a, n, amp, top = _bed_curve(t0, t1, pts, xf)
    r = rng("wind", m.sid, seed, kind)
    w = OF.wind_bed(np.clip(amp, 0.0, 1.0) * 0.85, seed=int(r.integers(1 << 20)))[:n]
    w = hpf(w, 150.0 if kind == "pines" else 90.0)
    if kind == "pines":
        sm = 0.6 + 0.4 * dsp.smooth_noise(n, 0.25, r)
        hs = np.stack([bp(dsp.pink(n, r), 1400.0, 6500.0) * sm for _ in range(2)], axis=1)
        w = norm(w) + 0.5 * norm(hs) * amp[:, None]
        for tt in dsp.poisson_times(0.16, n / SR, r):
            dsp.mix_into(w, dsp.pan_mono(0.35 * branch_snow(int(r.integers(6))), r.uniform(-0.7, 0.7)) * amp[min(n - 1, n_of(tt))],
                         n_of(tt))
    elif kind == "muffled":
        w = lp(lp(w, 520.0), 520.0)
    elif kind == "lee":
        w = lp(w, 1700.0)
    if kind in ("snow", "lee"):
        w = norm(w) + 0.22 * norm(snow_hiss_bed(n, r)) * amp[:, None]
    w = dsp.fade(lvl(w, bed=True), xf, xf)
    m.put("amb", w, a, top + CUE_TRIM + BED_LIFT + gain, label=label, align=None)


def river_layer(m, t0, t1, pts, seed=0, label=None, xf=0.3, gain=0.0):
    """The river under the ice from t0 to t1, its level following pts [(t, cue dB)]."""
    if not pts or t1 <= t0:
        return
    a, n, amp, top = _bed_curve(t0, t1, pts, xf)
    x = dsp.pad_to(river_bed(round(n / SR, 3), seed), n) * amp[:, None]
    m.put("amb", dsp.fade(lvl(x, bed=True), xf, xf), a, top + CUE_TRIM + BED_LIFT + gain, label=label, align=None)


SEARCH = dict(P=24.0, T_EAST=22.0, A=20.0, X0=None, CROSS=None)


def beam_near(ft):
    """How near the searchlight's patch is to the crossing at film time ft (1: on it), from the
    scenes' clock (_lib_dir: SWEEP_P, SWEEP_T_EAST, SWEEP_A, search_x)."""
    if SEARCH["X0"] is None:
        try:
            L = importlib.import_module(f"films.{FILM}.scenes._lib_dir")
            SEARCH.update(P=float(L.SWEEP_P), T_EAST=float(L.SWEEP_T_EAST), A=float(L.SWEEP_A),
                          X0=float(L.SWEEP_X0), CROSS=float(L.W.CROSS[0]), fn=L.search_x)
        except Exception as e:
            warn(f"the searchlight's clock (_lib_dir) does not load ({type(e).__name__}: {e}): using its constants")
            SEARCH.update(X0=0.0, CROSS=SEARCH["A"] * math.cos(TWO_PI * 3.0 / 24.0))
    if "fn" in SEARCH:
        x = SEARCH["fn"](ft)
    else:
        x = SEARCH["X0"] + SEARCH["A"] * math.cos(TWO_PI * (ft - SEARCH["T_EAST"]) / SEARCH["P"])
    return math.exp(-((x - SEARCH["CROSS"]) / 8.0) ** 2)


def motor_hum(n, seed=0, speed=None):
    """The searchlight's motor: mains hum and its harmonics, the motor's whine, the gearbox's faint
    grind; speed: a per-sample factor (it revs as it swings)."""
    r = rng("motor", seed, n)
    sp = np.ones(n) if speed is None else np.asarray(speed, np.float64)
    f = 50.0 * sp * (1.0 + 0.002 * dsp.smooth_noise(n, 0.5, r))
    ph = TWO_PI * np.cumsum(f) / SR
    y = 0.25 * np.sin(ph) + 0.6 * np.sin(2 * ph) + 0.45 * np.sin(3 * ph) + 0.25 * np.sin(4 * ph) + 0.15 * np.sin(6 * ph)
    wh = 0.12 * np.sin(TWO_PI * np.cumsum(f * 9.2) / SR)
    grd = bp(r.standard_normal(n), 250.0, 1200.0) * (0.5 + 0.5 * np.sin(0.5 * ph)) ** 4 * 0.15
    return 0.5 * (y + wh) + grd


def hum_layer(m, t0, t1, pts, seed=0, label=None, xf=0.3, gain=0.0, pan=0.0, beam=False, wet=-8.0, pan_end=None):
    """The searchlight's motor, far, from t0 to t1, its level following pts [(t, cue dB)]; beam: it
    swells as the beam's patch passes over the crossing (the scenes' searchlight clock)."""
    if not pts or t1 <= t0:
        return
    a, n, amp, top = _bed_curve(t0, t1, pts, xf)
    if beam:
        tt = np.arange(0, n, n_of(0.05))
        near = np.array([beam_near(m.t0 + a + i / SR) for i in tt])
        amp = amp * np.interp(np.arange(n), tt, 0.3 + 0.7 * near)
    x = lp(motor_hum(n, seed), 1400.0) * amp
    if pan_end is None:
        y = dsp.pan_mono(x, pan)
    else:                                   # sweeping across (equal power, as pan_mono)
        th = (np.clip(np.linspace(pan, pan_end, n), -1, 1) + 1.0) * np.pi / 4.0
        y = np.stack([x * np.cos(th), x * np.sin(th)], axis=1)
    x = dsp.reverb(y, "court", wet_db=wet, seed=seed % 5)[:n]
    m.put("amb", dsp.fade(lvl(x, bed=True), xf, xf), a, top + CUE_TRIM + BED_LIFT + gain, label=label, align=None)


@lru_cache(maxsize=None)
def motor_rev(dur=1.5, seed=0):
    """The searchlight's motor revving as it swings: its pitch and its whine climbing, then easing."""
    n = n_of(dur + 0.3)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    sp = 1.0 + 0.45 * np.sin(np.pi * u) ** 0.7
    x = motor_hum(n, seed + 3, sp) * (0.6 + 0.4 * np.sin(np.pi * u))
    return lvl(dsp.fade(lp(x, 2000.0), 0.08, 0.25))


@lru_cache(maxsize=None)
def sizzle(dur=1.2, seed=0):
    """The arc lamp's faint electric sizzle as the beam passes: a crackly hiss and a buzz."""
    r = rng("sizzle", round(dur, 2), seed)
    n = n_of(dur)
    t = tax(n)
    hs = bp(r.standard_normal(n), 2500.0, 9000.0) * (0.6 + 0.4 * np.abs(dsp.smooth_noise(n, 12.0, r)))
    cr = bp(dsp.crackle(n, 70.0, r), 2000.0, 8000.0)
    bz = (np.sin(TWO_PI * 100.0 * t) + 0.5 * np.sin(TWO_PI * 300.0 * t)) * 0.2
    return lvl(dsp.fade((norm(hs) + 0.6 * norm(cr) + bz) * swell(n, dur), 0.05, 0.1))


@lru_cache(maxsize=None)
def yoke_clank(seed=0):
    """The searchlight's iron yoke clanking round at the end of its swing: a heavy metal clank."""
    r = rng("yoke", seed)
    y = np.zeros(n_of(1.2))
    h = sfx._hit(r, np.array([190.0, 430.0, 770.0, 1240.0, 1890.0, 2750.0]) * r.uniform(0.92, 1.08),
                 [0.55, 0.42, 0.3, 0.2, 0.12, 0.08], spread=0.03, click=0.5)
    y[:len(h)] += norm(h)
    th = sfx._thump(n_of(0.25), 120.0, 70.0, 0.015, 0.1)
    y[:len(th)] += 0.6 * th
    h2 = sfx._hit(r, np.array([260.0, 610.0, 1050.0]), [0.2, 0.15, 0.1], click=0.3)
    dsp.mix_into(y, 0.35 * norm(h2), n_of(0.07))
    return lvl(y)


def far_clank(m, t, gain, pan=0.0, label=None, seed=0):
    """The yoke's clank far off, echoing (the whole valley in it)."""
    x = lp(yoke_clank(seed), 2200.0)
    y = dsp.reverb(dsp.pan_mono(x, pan), "alley", wet_db=-3.0, seed=seed % 5)
    m.put("efx", y, t, gain, label=label)


# ============================================================================ the hut, the lantern, the watch, the whistle
def stove(dur, seed=0):
    """A wood stove: the draught's low roar in the flue, the fire's crackle and pops."""
    r = rng("stove", round(dur, 2), seed)
    n = n_of(dur)
    roar = norm(lp(dsp.pink(n, r), 380.0) * (0.8 + 0.2 * dsp.smooth_noise(n, 2.0, r)))
    pops = np.zeros(n)
    for tt in dsp.poisson_times(9.0, dur, r):
        m_ = n_of(r.uniform(0.004, 0.02))
        dsp.mix_into(pops, r.lognormal(0.0, 0.7) * sfx._burst(m_, r, 800.0, 6000.0, t60=m_ / SR * 0.6, attack=0.0002),
                     n_of(tt))
    for tt in dsp.poisson_times(0.8, dur, r):
        dsp.mix_into(pops, 3.0 * sfx._burst(n_of(0.05), r, 400.0, 4000.0, t60=0.03, attack=0.0002), n_of(tt))
    return 0.6 * roar + 0.5 * norm(pops)


@lru_cache(maxsize=None)
def lantern_creak(seed=0, dur=0.22, glass=0.3):
    """A hurricane lantern swinging on its wire bail: the bail squeaking in its ears (iron stick-
    slip), the glass chimney rattling faintly in its cage."""
    r = rng("lantern", seed, dur, glass)
    y = np.zeros(n_of(dur + 0.15))
    m_ = n_of(dur)
    sw = swell(m_, dur) ** 0.7
    sq = dsp.friction(m_, 160.0 + 260.0 * sw, r, jitter=0.2, body=[(1250.0 * r.uniform(0.9, 1.1), 14, 1.0),
                                                                   (2300.0, 16, 0.6), (3900.0, 18, 0.3)])
    y[:m_] += norm(sq) * sw
    for k in range(int(2 + 3 * glass * r.uniform())):
        h = sfx._hit(r, np.array([2900.0, 4300.0, 6100.0]) * r.uniform(0.9, 1.1), [0.03, 0.02, 0.015], click=0.3,
                     n=n_of(0.05))
        dsp.mix_into(y, glass * 0.5 * r.uniform(0.4, 1.0) * norm(h), n_of(r.uniform(0.0, dur)))
    return lvl(dsp.fade(y, 0.003, 0.05))


@lru_cache(maxsize=None)
def lantern_clink(seed=0, hard=0.5):
    """The lantern set down or swung: its bail clinking, a tinny knock of its base."""
    r = rng("lclink", seed, hard)
    y = np.zeros(n_of(0.5))
    dsp.mix_into(y, norm(OF.clink(seed % 3, 3100.0 * r.uniform(0.9, 1.1))), 0)
    h = sfx._hit(r, np.array([620.0, 1340.0, 2250.0]) * r.uniform(0.9, 1.1), [0.05, 0.04, 0.03], click=0.6)
    dsp.mix_into(y, hard * norm(h), n_of(0.01))
    return lvl(y)


@lru_cache(maxsize=None)
def flame_gutter(seed=0, dur=0.5):
    """The lantern's flame guttering: a flutter of its hiss and roar."""
    r = rng("gutter", seed, dur)
    n = n_of(dur)
    t = tax(n)
    x = DC.flame_bed(round(dur, 2), seed % 3)[:n]
    x = x * (0.5 + 0.5 * np.abs(np.sin(TWO_PI * (7.0 + 5.0 * r.uniform()) * t))) * np.exp(-t / (0.5 * dur))
    return lvl(dsp.fade(x, 0.01, 0.1))


def lantern_hiss(dur, seed=0):
    """A kerosene lantern's flame hissing, close."""
    r = rng("lhiss", round(dur, 2), seed)
    n = n_of(dur)
    h = bp(r.standard_normal(n), 2200.0, 7500.0) * (0.85 + 0.15 * dsp.smooth_noise(n, 6.0, r))
    f = lp(dsp.pink(n, r), 600.0) * (0.8 + 0.2 * dsp.smooth_noise(n, 4.0, r))
    return lvl(dsp.fade(norm(h) + 0.5 * norm(f), 0.15, 0.25), bed=True)


@lru_cache(maxsize=None)
def watch_click(seed=0, hard=1.0):
    """A pocket watch's hunter lid springing open, or snapped shut: a small crisp click, the lid's
    tiny ring."""
    r = rng("wclick", seed, hard)
    y = np.zeros(n_of(0.15))
    h = sfx._hit(r, np.array([3600.0, 5300.0, 7400.0]) * r.uniform(0.95, 1.05), [0.02, 0.014, 0.01], click=1.0,
                 n=n_of(0.12))
    y[:len(h)] += norm(h)
    th = sfx._thump(n_of(0.03), 900.0, 500.0, 0.002, 0.008)
    y[:len(th)] += 0.3 * hard * th
    sp = sfx._hit(r, [2100.0, 4200.0], [0.06, 0.04], click=0.0, n=n_of(0.12))
    dsp.mix_into(y, 0.25 * norm(sp), n_of(0.004))
    return lvl(y)


@lru_cache(maxsize=None)
def watch_ticks(dur=2.0, seed=0, per=0.2):
    """A pocket watch ticking, very close: five beats a second, tick and tock."""
    r = rng("wticks", round(dur, 2), seed, per)
    n = n_of(dur + 0.05)
    y = np.zeros(n)
    k = 0
    while k * per < dur - 1e-6:
        f = 1.0 if k % 2 == 0 else 0.88
        h = sfx._hit(r, np.array([4200.0, 6100.0, 8300.0]) * f, [0.008, 0.006, 0.004], click=1.0, n=n_of(0.025))
        dsp.mix_into(y, (1.0 if k % 2 == 0 else 0.8) * norm(h), n_of(k * per))
        k += 1
    return lvl(y)


@lru_cache(maxsize=None)
def whistle(dur=0.7, seed=0, f0=2900.0, blasts=1, gap=0.1):
    """A police whistle (a pea whistle): a shrill tone near 3 kHz warbled by the pea, the breath's hiss
    in it; blasts of dur each, gap apart."""
    r = rng("whistle", dur, seed, f0, blasts, gap)
    n = n_of(blasts * dur + (blasts - 1) * gap + 0.1)
    y = np.zeros(n)
    for b in range(blasts):
        m_ = n_of(dur)
        t = tax(m_)
        ra = 26.0 + 5.0 * r.uniform()
        f = f0 * r.uniform(0.985, 1.015) * (1.0 + 0.012 * np.sin(TWO_PI * ra * t) + 0.004 * dsp.smooth_noise(m_, 40.0, r))
        f = f * (1.0 + 0.025 * np.exp(-t / 0.03))
        ph = TWO_PI * np.cumsum(f) / SR
        am = 1.0 - 0.5 * (0.5 + 0.5 * np.sin(TWO_PI * ra * t + 1.0)) ** 2
        x = (np.sin(ph) + 0.15 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)) * am
        x += 0.25 * bp(r.standard_normal(m_), 2000.0, 7000.0) * am
        e = np.clip(t / 0.012, 0, 1) * np.clip((dur - t) / 0.03, 0, 1) * (1.0 + 0.15 * np.exp(-t / 0.05))
        dsp.mix_into(y, x * e, n_of(b * (dur + gap)))
    return lvl(dsp.fade(y, 0.002, 0.03))


def far_whistle(m, t, gain, pan=0.0, label=None, seed=0, dur=0.45, blasts=1, gap=0.1, dist=1.0):
    """A whistle among the trees, far: its top gone, the woods' echo round it (dist 0..1)."""
    x = lp(whistle(dur, seed, 2750.0 + 260.0 * (seed % 3), blasts, gap), 5200.0 - 2600.0 * dist)
    y = dsp.reverb(dsp.pan_mono(x, pan), "court", wet_db=-9.0 + 6.0 * dist, seed=seed % 5)
    m.put("efx", y, t, gain, label=label)


@lru_cache(maxsize=None)
def far_bark(seed=0):
    """A dog barking twice, very far across the river (an approximation: a voiced, falling burst
    through a dog's formants, its top lost in the distance)."""
    r = rng("bark", seed)
    y = np.zeros(n_of(1.0))
    for k, tt in enumerate((0.0, 0.33)):
        m_ = n_of(0.13)
        t = tax(m_)
        f0 = (520.0 - 120.0 * k) * (1.0 - 0.35 * t / 0.13)
        src = dsp.saw(f0, m_) + 0.3 * r.standard_normal(m_)
        x = sum(dsp.biquad(src, "bandpass", f, q, 0.0) * a for f, q, a in ((750.0, 4.0, 1.0), (1400.0, 5.0, 0.6),
                                                                           (2500.0, 6.0, 0.25)))
        x = x * np.clip(t / 0.01, 0, 1) * np.exp(-t / 0.05)
        dsp.mix_into(y, (1.0 - 0.15 * k) * norm(x), n_of(tt))
    return lvl(lp(y, 1500.0))


# ============================================================================ doors, wood, the farmhouse
@lru_cache(maxsize=None)
def door_flung(seed=0):
    """The hut's door: the latch lifted, the wind throwing the door open (a fast creak) and slamming
    it against the wall (a wooden bang, the frame rattling)."""
    r = rng("dflung", seed)
    y = np.zeros(n_of(1.3))
    latch = sfx._hit(r, [850.0, 1700.0, 2650.0, 3900.0], [0.05, 0.04, 0.03, 0.02], click=0.8)
    y[:len(latch)] += 0.5 * norm(latch)
    cr = dsp.fade(pitch(mono(fx("door_creak", seed=seed % 3))[:n_of(0.4)], 3.0), 0.01, 0.05)
    dsp.mix_into(y, 0.45 * norm(cr), n_of(0.05))
    dsp.mix_into(y, norm(DC.wood_thunk(seed % 3, 1.4)), n_of(0.32))
    for k in range(3):
        h = sfx._hit(r, np.array([480.0, 900.0, 1500.0]) * r.uniform(0.9, 1.1), [0.03, 0.025, 0.02], click=0.3)
        dsp.mix_into(y, 0.18 * norm(h), n_of(0.36 + 0.035 * k))
    return lvl(y)


@lru_cache(maxsize=None)
def door_latch(seed=0):
    """A farmhouse door's iron latch lifting: a cold clack, a rattle."""
    r = rng("latch", seed)
    y = np.zeros(n_of(0.4))
    h = sfx._hit(r, np.array([780.0, 1650.0, 2900.0, 4300.0]) * r.uniform(0.95, 1.05), [0.08, 0.06, 0.04, 0.03],
                 click=0.9)
    y[:len(h)] += norm(h)
    h2 = sfx._hit(r, np.array([1100.0, 2300.0]), [0.03, 0.02], click=0.4)
    dsp.mix_into(y, 0.3 * norm(h2), n_of(0.05))
    return lvl(y)


@lru_cache(maxsize=None)
def door_creak(dur=0.55, seed=0):
    """A door swinging in on stiff hinges: a creak."""
    x = mono(fx("door_creak", seed=seed % 3))
    x = x[:n_of(min(len(x) / SR, dur + 0.1))]
    return lvl(dsp.fade(x, 0.02, 0.1))


@lru_cache(maxsize=None)
def door_shut(seed=0):
    """A door shut: a soft wooden thud, the latch dropping."""
    y = np.zeros(n_of(0.6))
    dsp.mix_into(y, lp(DC.wood_thunk(seed % 3, 0.9), 2600.0), 0)
    dsp.mix_into(y, 0.45 * door_latch(seed + 1), n_of(0.035))
    return lvl(y)


@lru_cache(maxsize=None)
def board_step(seed=0):
    """A boot on the boards inside the door: a knock, the floor answering."""
    y = np.zeros(n_of(0.5))
    dsp.mix_into(y, DC.wood_thunk(seed % 3, 0.5), 0)
    dsp.mix_into(y, 0.15 * OF.creak(0.16, seed % 4), n_of(0.03))
    return lvl(y)


@lru_cache(maxsize=None)
def bark_knock(seed=0, hard=0.4, creak=0.4):
    """A felt boot on frozen bark: a dull knock, the trunk creaking a little."""
    r = rng("bark", seed, hard, creak)
    y = np.zeros(n_of(0.6))
    h = sfx._hit(r, np.array([175.0, 410.0, 760.0, 1180.0]) * r.uniform(0.9, 1.1), [0.06, 0.05, 0.035, 0.025],
                 click=0.3)
    y[:len(h)] += norm(h)
    th = sfx._thump(n_of(0.12), 160.0, 95.0, 0.008, 0.04)
    y[:len(th)] += hard * th
    y = lp(y, 2500.0)
    if creak:
        dsp.mix_into(y, creak * norm(wood_creak(0.35, seed)), n_of(0.04))
    return lvl(y)


@lru_cache(maxsize=None)
def wood_creak(dur=0.8, seed=0, low=1.0):
    """Frozen wood taking weight: a slow, low creak through the grain; snow sifting off it."""
    r = rng("wcreak", round(dur, 2), seed, low)
    n = n_of(dur + 0.2)
    m_ = n_of(dur)
    sw = swell(m_, dur) ** 0.8
    fr = dsp.friction(m_, (28.0 + 60.0 * sw) / low, r, jitter=0.3,
                      body=[(180.0 / low, 6, 1.0), (340.0 / low, 8, 0.8), (640.0, 10, 0.45), (1150.0, 12, 0.2)])
    y = np.zeros(n)
    y[:m_] += norm(fr) * sw
    sift = bp(dsp.crackle(n, 400.0, r), 1500.0, 7000.0) * np.exp(-tax(n) / (0.5 * dur))
    y += 0.12 * norm(sift)
    return lvl(dsp.fade(y, 0.01, 0.08))


@lru_cache(maxsize=None)
def wood_knock(seed=0):
    """A boot hitting the branch stub: a hard knock of frozen wood."""
    r = rng("wknock", seed)
    y = np.zeros(n_of(0.6))
    h = sfx._hit(r, np.array([220.0, 510.0, 940.0, 1500.0, 2300.0]) * r.uniform(0.95, 1.05), [0.09, 0.07, 0.05, 0.04, 0.03],
                 click=0.7)
    y[:len(h)] += norm(h)
    th = sfx._thump(n_of(0.2), 150.0, 80.0, 0.01, 0.07)
    y[:len(th)] += 0.8 * th
    return lvl(y)


def room_warm(dur, seed=0):
    """The warm room through the open door: a stove's soft crackle and a room's low air, muffled."""
    s = stove(dur, seed + 5)
    rt = mono(fx("room_tone", dur=round(dur, 2), seed=seed % 3))[:len(s)]
    x = lp(norm(s) + 0.6 * norm(rt), 2200.0)
    return lvl(x, bed=True)


# ============================================================================ cloth, wool, reeds, hands
@lru_cache(maxsize=None)
def wool(dur=0.35, seed=0, heavy=0.3, soft=0.5):
    """Wool moving (a mitten, a scarf, a shawl): soft fabric noise in one swell, little crackle."""
    x = DC.cloth(round(max(0.08, dur), 3), seed % 7, heavy)
    return lvl(lp(x, 5500.0 - 3000.0 * soft))


@lru_cache(maxsize=None)
def coat(dur=0.4, seed=0):
    """A long greatcoat moving: heavy cloth, lower and rougher."""
    return lvl(DC.cloth(round(max(0.08, dur), 3), seed % 7, 1.0))


@lru_cache(maxsize=None)
def wool_whoosh(seed=0, hard=0.5):
    """The scarf thrown: a soft whoosh of wool through the air, its flutter."""
    r = rng("wwhoosh", seed, hard)
    d = 0.32 + 0.1 * hard
    n = n_of(d + 0.1)
    t = tax(n)
    x = lp(mono(DC.whip_down(round(d, 3), seed % 3)), 3500.0)
    fl = bp(r.standard_normal(n), 300.0, 2500.0) * (0.5 + 0.5 * np.sin(TWO_PI * 24.0 * t) ** 2) * swell(n, d)
    return lvl(dsp.fade(norm(dsp.pad_to(x, n)) + 0.4 * norm(fl), 0.01, 0.05))


@lru_cache(maxsize=None)
def cloth_slap(seed=0, snow=True):
    """The scarf slapping down (on snow, or across an arm): a soft thud, wool, a breath of snow."""
    y = np.zeros(n_of(0.4))
    th = sfx._thump(n_of(0.12), 170.0, 95.0, 0.006, 0.04)
    y[:len(th)] += th
    dsp.mix_into(y, 0.5 * DC.cloth(0.12, seed % 5, 0.3), 0)
    if snow:
        dsp.mix_into(y, 0.4 * foot("girl_land", seed), 0)
    return lvl(y)


@lru_cache(maxsize=None)
def stretch(seed=0, hard=0.5):
    """Wool pulled taut: a quick creak of the knit, a 'thwip' of tension."""
    r = rng("stretch", seed, hard)
    m_ = n_of(0.14)
    fr = dsp.friction(m_, 60.0 + 80.0 * hard, r, jitter=0.3, body=[(600.0, 5, 1.0), (1300.0, 7, 0.5)])
    t = tax(m_)
    th = dsp.tv_bandpass(r.standard_normal(m_), 500.0 + 2500.0 * t / 0.14, q=1.2, block=32) * np.exp(-t / 0.05)
    y = norm(fr) * swell(m_, 0.14) + 0.4 * hard * norm(th)
    return lvl(dsp.fade(y, 0.003, 0.03))


@lru_cache(maxsize=None)
def rip(seed=0, dur=0.16):
    """A short, sharp cloth rip: fibres tearing one after another, fast."""
    r = rng("rip", seed, dur)
    n = n_of(dur + 0.05)
    t = tax(n)
    cr = bp(dsp.crackle(n, 1800.0, r, amp_spread=0.6), 700.0, 6000.0)
    nz = bp(r.standard_normal(n), 900.0, 5000.0)
    e = np.clip(t / 0.01, 0, 1) * np.clip((dur - t) / 0.02, 0, 1) * (0.7 + 0.3 * np.abs(dsp.smooth_noise(n, 80.0, r)))
    return lvl(dsp.fade((norm(cr) + 0.5 * norm(nz)) * e, 0.001, 0.02))


@lru_cache(maxsize=None)
def wire_creak(dur=1.5, seed=0, taut=1.0):
    """Barbed wire lifted: a taut metallic creak (stick-slip through the wire's thin ringing modes),
    the staples ticking."""
    r = rng("wire", round(dur, 2), seed, taut)
    m_ = n_of(dur)
    sw = swell(m_, dur) ** 0.6
    fr = dsp.friction(m_, (40.0 + 90.0 * sw) * taut, r, jitter=0.35,
                      body=[(820.0, 22, 1.0), (1710.0, 26, 0.7), (3100.0, 30, 0.45), (4600.0, 30, 0.2)])
    y = norm(fr) * sw
    for k in range(int(2 + dur * 2)):
        h = sfx._hit(r, np.array([2400.0, 3900.0]) * r.uniform(0.9, 1.1), [0.02, 0.015], click=0.5, n=n_of(0.04))
        dsp.mix_into(y, 0.25 * norm(h), n_of(r.uniform(0.0, dur)))
    return lvl(dsp.fade(y, 0.01, 0.08))


@lru_cache(maxsize=None)
def wire_twang(seed=0, ring=0.5, f0=190.0):
    """The wire jerked: a plucked steel wire's 'boing', quivering as it settles."""
    r = rng("twang", seed, ring, f0)
    n = n_of(0.3 + 1.2 * ring)
    y = sfx._twang_tone(n, f0 * r.uniform(0.92, 1.08), r, bend=0.05, t60=0.25 + 1.0 * ring, bright=1.0)
    y = norm(y) * (1.0 + 0.25 * np.sin(TWO_PI * 6.5 * tax(n)))
    h = sfx._hit(r, np.array([1900.0, 3300.0]), [0.02, 0.015], click=0.6, n=n_of(0.04))
    y[:len(h)] += 0.3 * norm(h)
    return lvl(dsp.fade(y, 0.0, 0.08))


@lru_cache(maxsize=None)
def reeds(dur=0.6, seed=0, density=1.0):
    """Dry frozen reeds brushing and rattling against a coat: stalks ticking on stalks, a rustle."""
    r = rng("reeds", round(dur, 2), seed, density)
    n = n_of(dur + 0.2)
    m_ = n_of(dur)
    sw = swell(m_, dur) ** 0.6
    y = np.zeros(n)
    ru = bp(r.standard_normal(m_), 900.0, 6500.0) * (0.5 + 0.5 * np.abs(dsp.smooth_noise(m_, 25.0, r)))
    y[:m_] += 0.5 * norm(ru) * sw
    for tt in dsp.poisson_times(45.0 * density, dur, r):
        h = sfx._hit(r, np.array([2300.0, 3700.0, 5600.0]) * r.uniform(0.8, 1.25), [0.012, 0.009, 0.006], click=0.5,
                     n=n_of(0.025))
        dsp.mix_into(y, r.uniform(0.2, 1.0) * norm(h) * sw[min(m_ - 1, n_of(tt))], n_of(tt))
    return lvl(dsp.fade(y, 0.01, 0.08))


@lru_cache(maxsize=None)
def reed_tick(seed=0):
    """A dry reed ticking against another in the wind."""
    r = rng("rtick", seed)
    y = np.zeros(n_of(0.2))
    for k in range(2):
        h = sfx._hit(r, np.array([2600.0, 4100.0]) * r.uniform(0.9, 1.1), [0.015, 0.01], click=0.5, n=n_of(0.03))
        dsp.mix_into(y, (1.0 - 0.4 * k) * norm(h), n_of(0.05 * k))
    return lvl(y)


@lru_cache(maxsize=None)
def hands_rub(dur=0.8, seed=0):
    """Gloved hands rubbed together over the stove: three strokes of leather and wool."""
    y = np.zeros(n_of(dur + 0.2))
    k, tt = 0, 0.0
    while tt < dur - 0.1:
        dsp.mix_into(y, (0.8 + 0.2 * (k % 2)) * DC.cloth(0.24, (seed + k) % 5, 0.6), n_of(tt))
        tt += 0.27
        k += 1
    return lvl(y)


@lru_cache(maxsize=None)
def scrape_ice(dur=0.4, seed=0, n_=3):
    """Gloved fingers clawing at ice: scrapes (stick-slip on the hard surface), crumbs of ice."""
    r = rng("iscrape", round(dur, 2), seed, n_)
    y = np.zeros(n_of(dur + 0.3))
    for k in range(n_):
        tt = k * dur / max(n_, 1) + r.uniform(0.0, 0.04)
        m_ = n_of(0.12 + 0.08 * r.uniform())
        fr = dsp.friction(m_, 300.0 + 400.0 * r.uniform(), r, jitter=0.35,
                          body=[(1500.0 * r.uniform(0.8, 1.2), 7, 1.0), (3200.0, 9, 0.6), (5200.0, 11, 0.3)])
        x = norm(fr) * swell(m_, m_ / SR) + 0.4 * norm(bp(r.standard_normal(m_), 2000.0, 8000.0)) * swell(m_, m_ / SR)
        dsp.mix_into(y, r.uniform(0.6, 1.0) * x, n_of(tt))
        cr = bp(dsp.crackle(n_of(0.08), 600.0, r), 2000.0, 8000.0)
        dsp.mix_into(y, 0.25 * norm(cr), n_of(tt + 0.05))
    return lvl(dsp.fade(y, 0.003, 0.05))


@lru_cache(maxsize=None)
def glove_slap(seed=0, wet=1.0):
    """Wet gloves slapping onto ice: a flat smack, water flicking off."""
    r = rng("gslap", seed, wet)
    y = np.zeros(n_of(0.4))
    th = sfx._thump(n_of(0.1), 240.0, 130.0, 0.005, 0.03)
    y[:len(th)] += th
    b = sfx._burst(n_of(0.04), r, 300.0, 3500.0, t60=0.02, attack=0.0003)
    y[:len(b)] += 0.9 * norm(b)
    for k in range(int(3 + 5 * wet)):
        dsp.mix_into(y, 0.15 * sfx._drop(r, r.uniform(900.0, 2600.0), 0.006, 0.5), n_of(r.uniform(0.005, 0.12)))
    return lvl(y)


@lru_cache(maxsize=None)
def glove_slip(seed=0, dur=0.22):
    """A wet glove sliding on ice: a squeal of wet leather, water smearing."""
    r = rng("gslip", seed, dur)
    m_ = n_of(dur)
    fr = dsp.friction(m_, 350.0 + 250.0 * swell(m_, dur), r, jitter=0.25, body=[(1100.0, 8, 1.0), (2300.0, 10, 0.5)])
    wt = bp(r.standard_normal(m_), 400.0, 3000.0)
    return lvl(dsp.fade((norm(fr) + 0.4 * norm(wt)) * swell(m_, dur) ** 0.5, 0.005, 0.04))


@lru_cache(maxsize=None)
def squeeze(seed=0, wet=1.0):
    """A wet glove closing on wool: a squelch, the knit creaking."""
    r = rng("squeeze", seed, wet)
    y = np.zeros(n_of(0.32))
    m_ = n_of(0.18)
    y[:m_] += norm(bp(r.standard_normal(m_), 200.0, 1300.0) * swell(m_, 0.18))
    dsp.mix_into(y, 0.5 * wet * norm(sfx._drop(r, 320.0, 0.03, 0.6)), n_of(0.01))
    dsp.mix_into(y, 0.4 * norm(stretch(seed, 0.3)), n_of(0.02))
    return lvl(dsp.fade(y, 0.003, 0.03))


@lru_cache(maxsize=None)
def body_slide(dur=0.5, seed=0, wet=0.0, bark=True):
    """A body sliding fast: a coat along bark (or wet on snow and ice, long), a swish with grit."""
    r = rng("bslide", round(dur, 2), seed, wet, bark)
    n = n_of(dur + 0.2)
    m_ = n_of(dur)
    sw = swell(m_, dur) ** 0.5
    x = bp(dsp.pink(m_, r), 250.0 if bark else 180.0, 3000.0 if bark else 2600.0) * sw
    fr = dsp.friction(m_, 80.0 + 60.0 * sw, r, jitter=0.4, body=[(300.0, 5, 1.0), (700.0, 7, 0.6)]) * sw
    y = np.zeros(n)
    y[:m_] += norm(x) + 0.35 * norm(fr)
    if wet:
        for tt in dsp.poisson_times(14.0 * wet, dur, r):
            dsp.mix_into(y, 0.2 * sfx._drop(r, r.uniform(700.0, 2200.0), 0.008, 0.5), n_of(tt))
        sq = dsp.friction(m_, 500.0 + 300.0 * sw, r, jitter=0.3, body=[(1400.0, 9, 1.0)]) * sw
        y[:m_] += 0.2 * wet * norm(sq)
    return lvl(dsp.fade(y, 0.02, 0.1))


@lru_cache(maxsize=None)
def chatter(dur=2.5, seed=0):
    """Teeth chattering, small and fast: tiny clicks in bursts, irregular."""
    r = rng("chatter", round(dur, 2), seed)
    n = n_of(dur + 0.1)
    y = np.zeros(n)
    tt = 0.02
    while tt < dur:
        burst = int(3 + r.integers(6))
        for k in range(burst):
            h = sfx._hit(r, np.array([2400.0, 3600.0, 5200.0]) * r.uniform(0.85, 1.15), [0.006, 0.005, 0.004], click=0.7,
                         n=n_of(0.012))
            dsp.mix_into(y, r.uniform(0.4, 1.0) * norm(h), n_of(tt + k * (1.0 / (13.0 + 4.0 * r.uniform()))))
        tt += burst / 14.0 + r.uniform(0.08, 0.3)
    return lvl(lp(y, 6500.0))


@lru_cache(maxsize=None)
def strokes(dur=1.5, seed=0, n_=3):
    """Heavy strokes through water, heard under it: slow muffled surges, bubbles off his sleeves."""
    r = rng("strokes", round(dur, 2), seed, n_)
    n = n_of(dur + 0.6)
    y = np.zeros(n)
    for k in range(n_):
        m_ = n_of(0.5)
        x = lp(dsp.pink(m_, r), 500.0) * swell(m_, 0.5) ** 1.5
        dsp.mix_into(y, norm(x), n_of(k * dur / n_))
        dsp.mix_into(y, 0.25 * bubbles(0.4, seed + k, 0.7, 30.0), n_of(k * dur / n_ + 0.15))
    return lvl(dsp.fade(y, 0.02, 0.1))


@lru_cache(maxsize=None)
def stone_plop(seed=0):
    """A stone dropping through the hole into the black water under the ice: a deep hollow plop."""
    r = rng("plop", seed)
    y = np.zeros(n_of(1.0))
    d = sfx._drop(r, 210.0, 0.035, chirp=1.4)
    y[:len(d)] += norm(d)
    th = sfx._thump(n_of(0.3), 160.0, 80.0, 0.02, 0.12)
    y[:len(th)] += 0.5 * th
    sp = sfx._splash(n_of(0.5), r, size=0.3)
    y[:len(sp)] += 0.25 * norm(sp)
    y = dsp.biquad(y, "peak", 320.0, 2.0, 6.0)
    return lvl(dsp.reverb(norm(y), "cell", wet_db=-14.0, seed=seed).mean(axis=1))


@lru_cache(maxsize=None)
def stone_whir(dur=0.6, seed=0):
    """A stone whirring through the cold air: a short whoosh, tumbling."""
    r = rng("whir", round(dur, 2), seed)
    n = n_of(dur + 0.1)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    x = dsp.tv_bandpass(dsp.pink(n, r), 1800.0 - 900.0 * u, q=1.6, block=64)
    x = x * (0.55 + 0.45 * np.sin(TWO_PI * 23.0 * t) ** 2) * np.sin(np.pi * u) ** 1.2
    return lvl(dsp.fade(x, 0.01, 0.05))


@lru_cache(maxsize=None)
def paper_sound(kind="flood", dur=0.8, seed=0):
    """The paper world: 'flood' a soft whoosh as the page spreads; 'slide' the frame splitting;
    'settle' the letters settling, one after another."""
    r = rng("paper", kind, round(dur, 2), seed)
    if kind == "settle":
        y = np.zeros(n_of(dur + 0.3))
        k = 0
        while k * 0.06 < dur:
            dsp.mix_into(y, 0.6 * OF.paper_snap((seed + k) % 5) * r.uniform(0.3, 0.8), n_of(k * 0.06 + r.uniform(0, 0.02)))
            k += 1
        dsp.mix_into(y, 0.3 * DC.paper_whoosh(round(dur, 2), seed % 5).mean(axis=1), 0)
        return lvl(lp(y, 7000.0))
    x = DC.paper_whoosh(round(max(0.2, dur), 2), seed % 5).mean(axis=1)
    if kind == "slide":
        x = hpf(x, 500.0)
    return lvl(x)


# ============================================================================ the music: strings (OPPOSITE's), the music box
def pz(p, vel=0.8, seed=0):
    return OF.pizz(hz(p), vel, seed)


def harm(p, dur, vel=0.7, seed=0, **kw):
    return OF.harmonic(hz(p), dur, vel, seed, **kw)


def held(notes, dur, vel=0.7, seed=0, octaves=(0,), attack=0.2, release=0.6, env_=None, bright=4500.0):
    return OF.strings([p - 46 for p in notes], dur, vel, seed, octaves=octaves, attack=attack, release=release,
                      env=env_, bright=bright)


def stacc(notes, dur, vel=0.8, seed=0, spread=(0, 12)):
    return OF.chord([p - 46 for p in notes], dur, vel, seed, 0, True, spread)


def trem(notes, dur, vel=0.6, seed=0, rate=13.0):
    return OF.tremolo([p - 46 for p in notes], dur, vel, seed, octave=0, rate=rate)


def strings_at(m, t, notes, dur, gain, seed=0, attack=0.4, release=1.0, octaves=(0,), bright=3200.0, env_=None,
               label=None, vel=0.7, pan=0.0, hall="auto", shape=None, lpf=None):
    """A held section chord at scene time t (shape: a dB breakpoint envelope over it; lpf: muffled)."""
    x = lvl(held(tuple(int(p) for p in notes), dur, vel, seed, octaves, attack, release, env_, bright))
    if shape:
        x = env_db(x, shape)
    if lpf:
        x = lp(x, lpf)
    m.put("music", x, t, gain, pan=pan, label=label, align=None, hall=hall)
    return x


def line_at(m, t0, notes, step, gain, seed=0, label=None, octaves=(0,), bright=1800.0, attack=0.3, release=0.8,
            last=None, vel=0.8, lpf=None, glide=0.06):
    """A line bowed legato (a slide of glide s into each note), a note every step s from t0; last:
    the last note's length."""
    notes = [int(p) for p in notes]
    if not notes:
        return
    pts, envp = [], [(0.0, 1.0)]
    for i, p in enumerate(notes):
        ts = i * step
        pts.append((ts, p))
        if i + 1 < len(notes):
            te = (i + 1) * step
            pts.append((te - glide, p))
            envp += [(max(ts, te - 0.08), 1.0), (te, 0.8), (te + 0.1, 1.0)]
    dur = len(notes) * step if last is None else (len(notes) - 1) * step + last
    pts.append((dur, notes[-1]))
    envp.append((dur, 1.0))
    x = lvl(OF.bowed_line([(t, p - 46) for t, p in pts], dur, vel, seed, octaves=octaves, attack=attack,
                          release=release, bright=bright, env=envp))
    if lpf:
        x = lp(x, lpf)
    m.put("music", x, t0, gain, label=label, align=None)


@lru_cache(maxsize=None)
def shimmer(dur=0.8, seed=0, top=88, n_=4):
    """High string harmonics over each other, each trembling at its own rate: the ice."""
    r = rng("shimmer", seed, round(dur, 3), top, n_)
    out = None
    for k, p in enumerate((top, top + 5, top + 7, top - 5)[:n_]):
        x = OF.harmonic(hz(p), dur, 1.0, seed + 7 * k, attack=0.3 + 0.1 * k, release=0.6, vib=0.004)
        t = tax(len(x))
        x = x * (0.55 + 0.45 * np.sin(TWO_PI * r.uniform(5.0, 9.0) * t + r.uniform(0, 6.3)) ** 2) * 0.75 ** k
        out = x if out is None else out[:len(x)] + x[:len(out)]
    return lvl(hpf(out, 900.0))


@lru_cache(maxsize=None)
def pulse_note(p, seed=0):
    """One beat of the hunt's pulse: the basses' pizzicato on p and the octave under it, a soft short
    bowed note on p (cellos)."""
    a = OF.pizz(hz(p - 12), 1.0, seed)
    b = OF.pizz(hz(p), 1.0, seed + 1)
    c = OF.chord([p - 46], 0.22, 1.0, seed, 0, True, (0,))
    y = np.zeros(max(len(a), len(b), len(c)))
    y[:len(a)] += 0.9 * norm(a)
    y[:len(b)] += 0.5 * norm(b)
    y[:len(c)] += 0.35 * norm(c)
    return lvl(lp(y, 2600.0))


def pulse(m, t0, t1, step=BEAT, gain=-22.0, root=45, vel=(0.7, 1.0), seed=0, label=None, notes=None):
    """The hunt's soft low pulse on the film's grid, every step s from t0 to t1 (scene time); vel ramps
    across it; a bar's first beat a little stronger; notes(t) -> the note at t (None: a rest)."""
    k = math.ceil((m.t0 + t0) / step - 1e-9)
    j = 0
    while True:
        tf = k * step
        t = tf - m.t0
        if t >= t1 - 1e-6:
            break
        u = (t - t0) / max(t1 - t0, 1e-6)
        v = (vel[0] + (vel[1] - vel[0]) * u) * (1.15 if abs(tf / BAR - round(tf / BAR)) < 1e-6 else 1.0)
        p = notes(t) if notes else root
        if p:
            m.put("music", pulse_note(int(p), (seed + j) % 4) * v, t, gain + MUSIC_LIFT - 2.0,
                  label=label if j == 0 else None, hall=-20.0)
        k += 1
        j += 1


@lru_cache(maxsize=None)
def box_note(p, seed=0):
    """One note of the music box: a steel comb's tine plucked by a pin (its click), the tine's
    fundamental and its inharmonic upper modes, a second tine a hair sharp (the shimmer), the little
    wooden box's resonance."""
    r = rng("box", p, seed)
    f0 = hz(p)
    t60 = float(np.clip(3.4 * (523.25 / f0) ** 0.7, 1.4, 4.8))
    n = n_of(t60 * 1.05 + 0.05)
    t = tax(n)
    y = np.zeros(n)
    for ratio, amp, k in ((1.0, 1.0, 1.0), (1.0016, 0.32, 0.85), (2.0, 0.05, 0.3), (6.267, 0.2, 0.12),
                          (17.55, 0.05, 0.03)):
        f = f0 * ratio
        if f < 18000.0:
            y += amp * np.sin(TWO_PI * f * t + r.uniform(0, TWO_PI)) * np.power(10.0, -3.0 * t / (t60 * k))
    a = n_of(0.0008)
    y[:a] *= np.linspace(0.0, 1.0, a)
    c = sfx._click(r, 3500.0, 0.0015)
    y[:len(c)] += 0.22 * c / (np.max(np.abs(c)) + 1e-9)
    y = dsp.biquad(dsp.biquad(y, "peak", 520.0, 1.4, 4.0), "peak", 1250.0, 1.8, 2.5)
    return lvl(dsp.fade(y, 0.0, 0.15))


@lru_cache(maxsize=None)
def box_whirr(dur=2.0, seed=0):
    """The music box's governor whirring while it plays: its little fan beating the air, the gears."""
    r = rng("whirr", round(dur, 2), seed)
    n = n_of(dur)
    t = tax(n)
    fan = 38.0 * (1.0 + 0.03 * np.sin(TWO_PI * 0.7 * t))
    ph = np.cumsum(fan) / SR
    beat = dsp.onepole_lp(0.5 + 0.5 * np.sign(np.sin(TWO_PI * ph)), 300.0)
    x = bp(r.standard_normal(n), 900.0, 4500.0) * beat + 0.3 * bp(dsp.saw(fan * 7.0, n), 300.0, 2500.0)
    return lvl(dsp.fade(x, 0.02, 0.1))


@lru_cache(maxsize=None)
def box_lid(seed=0):
    """The music box's lid springing open: a small wooden click, the spring's buzz (the governor
    starting up)."""
    r = rng("lid", seed)
    y = np.zeros(n_of(0.6))
    h = sfx._hit(r, [1800.0, 3100.0, 4700.0], [0.02, 0.015, 0.01], click=0.8, n=n_of(0.06))
    y[:len(h)] += norm(h)
    th = sfx._thump(n_of(0.05), 320.0, 180.0, 0.003, 0.015)
    y[:len(th)] += 0.4 * th
    bz = np.asarray(box_whirr(0.45, seed + 1))
    bz = norm(bz) * np.exp(-tax(len(bz)) / 0.15) * (1.0 + 0.6 * np.exp(-tax(len(bz)) / 0.04))
    dsp.mix_into(y, 0.45 * bz, n_of(0.01))
    return lvl(y)


@lru_cache(maxsize=None)
def box_snap(seed=0):
    """A mitten slapping the music box's lid shut: a muffled wooden snap, the mitten's pat."""
    r = rng("bsnap", seed)
    y = np.zeros(n_of(0.5))
    dsp.mix_into(y, lp(DC.wood_thunk(seed % 3, 0.35), 2600.0), 0)
    h = sfx._hit(r, [1400.0, 2500.0], [0.02, 0.015], click=0.6, n=n_of(0.05))
    dsp.mix_into(y, 0.5 * norm(h), 0)
    dsp.mix_into(y, 0.35 * DC.cloth(0.1, seed % 5, 0.2), 0)
    return lvl(y)


def music_box(m, t, p, gain, label=None, pan=0.0, choke=None, wet=None, kind=None, far_=False, name=None):
    """A note of the music box at scene time t (choke: the lid shuts on it after choke s)."""
    x = np.asarray(box_note(int(p), int(round(t * 4)) % 3))
    if choke is not None and choke < len(x) / SR:
        x = dsp.fade(x[:n_of(choke + 0.025)], 0.0, 0.025)
    if far_:
        x = lp(x, 2400.0)
    fol(m, x, t, gain, pan, label, bus="music", wet=wet, kind=kind, hall=-22.0)
    m.box.append((round(m.t0 + t, 4), name or nm(int(p))))


@lru_cache(maxsize=None)
def glass_tink(p, seed=0):
    """A crisp glassy tink: a small glass struck (its few high partials, a quick decay), tuned to p."""
    r = rng("gtink", p, seed)
    f = hz(p)
    n = n_of(1.2)
    t = tax(n)
    y = np.zeros(n)
    for ratio, a, t60 in ((1.0, 1.0, 0.9), (2.32, 0.4, 0.5), (3.98, 0.22, 0.3), (6.1, 0.1, 0.15)):
        if f * ratio < 18000.0:
            y += a * np.sin(TWO_PI * f * ratio * t + r.uniform(0, TWO_PI)) * np.power(10.0, -3.0 * t / t60)
    a = n_of(0.001)
    y[:a] *= np.linspace(0.0, 1.0, a)
    c = sfx._click(r, 4000.0, 0.0015)
    y[:len(c)] += 0.4 * c / (np.max(np.abs(c)) + 1e-9)
    return lvl(dsp.fade(y, 0.0, 0.2))


@lru_cache(maxsize=None)
def glass_shimmer(dur=1.7, seed=0, tail=0.8):
    """The first snowflakes: glass harmonics, very soft - high sines beating slowly (A6 E7 D7 A7),
    a sparkle of tiny glass ticks; it fades in and rings on past dur."""
    r = rng("gshim", round(dur, 2), seed, tail)
    n = n_of(dur + tail)
    t = tax(n)
    y = np.zeros((n, 2))
    for k, p in enumerate((93, 100, 98, 105)):
        f = hz(p)
        lfo = 0.6 + 0.4 * np.sin(TWO_PI * r.uniform(0.3, 0.9) * t + r.uniform(0, 6.3))
        for ch in range(2):
            det = (0.6 + 0.5 * ch) * (1 if k % 2 else -1)
            y[:, ch] += (0.75 ** k) * np.sin(TWO_PI * (f + det) * t + r.uniform(0, TWO_PI)) * lfo
    e = np.clip(t / max(0.5 * dur, 0.2), 0, 1) ** 1.5 * np.clip((dur + tail - t) / tail, 0, 1)
    sp = np.zeros(n)
    for tt in dsp.poisson_times(14.0, dur + 0.5 * tail, r):
        h = sfx._hit(r, np.array([5200.0, 7600.0]) * r.uniform(0.9, 1.15), [0.04, 0.03], click=0.2, n=n_of(0.06))
        dsp.mix_into(sp, r.uniform(0.2, 1.0) * norm(h), n_of(tt))
    y = norm(y) * e[:, None] + 0.12 * (norm(sp) * e)[:, None]
    return lvl(y)


def thread_note(dur, seed=0, ping=True, p=THREAD):
    """The red thread: one high string harmonic (E6), held; ping: it snaps taut (a sharp start)."""
    x = OF.harmonic(hz(p), dur, 1.0, seed, attack=0.006 if ping else 0.35, release=0.45, vib=0.0015, sfz=ping)
    if ping:
        x = x.copy()
        tk = glass_tink(p, seed)
        k = min(len(x), len(tk))
        x[:k] += 0.35 * norm(np.asarray(tk))[:k] * np.exp(-tax(k) / 0.08)
    return lvl(x)


@lru_cache(maxsize=None)
def _heart(dub, seed):
    x = np.asarray(OF.heart(dub, seed), np.float64)
    knock = bp(np.tanh(4.0 * x), 110.0, 650.0)
    return lvl(norm(x) + 0.45 * norm(knock))


def heartbeat(m, t, gain, dub=0.24, seed=0, label=None, low=0.0, pan=0.0, cut_at=None, hall=-26.0, lpf=None):
    """One heartbeat (lub, and the dub dub s later) at scene time t; low: semitones down (bigger,
    slower: under water); cut_at: stopped dead there (scene time)."""
    x = np.asarray(_heart(round(dub, 3), seed % 3))
    if low:
        x = pitch(x, -low)
    if lpf:
        x = lp(x, lpf)
    if cut_at is not None and cut_at - t < len(x) / SR:
        k = max(n_of(0.004), n_of(cut_at - t))
        x = dsp.fade(x[:k], 0.0, min(0.01, k / SR / 2))
    m.put("music", x, t, gain, pan=pan, label=label, hall=hall)
    m.hearts.append(round(m.t0 + t, 4))


# ============================================================================ the foley, by tag
STEP_TAGS = {"step_girl_deep": "girl_deep", "step_mother_deep": "mother_deep", "step_mother_heavy": "mother_heavy",
             "step_guard_hobnail": "guard", "step_mother": "mother", "step_mother_ice": "mother_ice",
             "step_backtrack": "backtrack", "crunch_soft": "soft", "step_down_snow": "mother_heavy",
             "snow_step_mother": "mother", "step_guard_ice": "guard_ice", "snow_step": "mother"}


def _sd(c, k=0):
    return (int(round(c["t"] * 100)) + 7 * k) % 997


def h_step(m, c):
    kind = STEP_TAGS.get(c["sfx"], "mother")
    txt = c["text"]
    if kind == "guard" and "hurrying" in txt:
        kind = "guard_run"
    if kind == "mother" and "far off" in txt:
        kind = "mother_far"
    if c["sfx"] == "step_down_snow":
        fol(m, crunch(0.22, 480.0, 3800.0, 2400.0, (95.0, 58.0, 0.5), 0.06, 0.0, 0.0, 0, 0.0, 0.0, 0.0, _sd(c) % 8),
            c["t"], cg(c), c["pan"], c["sfx"], bus="feet")
        return
    step(m, kind, c["t"], cg(c), c["pan"], label=c["sfx"])


def h_girl_land(m, c):
    for k in range(2):
        step(m, "girl_land", c["t"] + 0.09 * k, cg(c) - 2.0 * k, c["pan"] + 0.05 * k, label=c["sfx"] if k == 0 else None,
             seed=_sd(c, k))


def h_scuff(m, c):
    for k in range(2):
        step(m, "girl_run", c["t"] + 0.11 * k, cg(c) - 1.5 * k, c["pan"], label=c["sfx"] if k == 0 else None,
             seed=_sd(c, k))
    fol(m, wool(0.2, _sd(c), 0.2), c["t"], cg(c) - 8.0, c["pan"])


def steps_run(m, kind, t0, dur, every, gain, pan=0.0, label=None, fade_db=0.0, lpf_end=None, pan_end=None, k0=0,
              rise_db=0.0):
    """A run of steps every `every` s over dur (gain fading by fade_db, or rising by rise_db; low-passed
    toward lpf_end; panning toward pan_end)."""
    k = 0
    while k * every < dur - 1e-6:
        u = k * every / max(dur, 1e-6)
        g_ = gain - fade_db * u + rise_db * (u - 1.0)
        pn = pan if pan_end is None else pan + (pan_end - pan) * u
        lpf = None if lpf_end is None else 7000.0 * (lpf_end / 7000.0) ** u
        step(m, kind, t0 + k * every, g_, pn, label=label if k == 0 else None, seed=k0 + k, lpf=lpf)
        k += 1


def h_steps_group(m, c):
    """Several men's boots, or a run of hers / the girl's."""
    s, txt, t, d = c["sfx"], c["text"], c["t"], c.get("dur") or 1.0
    if s == "snow_steps_guards":
        if "run" in txt:
            for j, (ev, pn) in enumerate(((0.33, -0.15), (0.36, 0.2), (0.31, 0.05))):
                steps_run(m, "guard_run", t + 0.07 * j, d, ev, cg(c) - 2.0 * j, c["pan"] + pn, c["sfx"] if j == 0 else None,
                          k0=10 * j)
        else:
            for j, (ev, pn) in enumerate(((0.64, -0.1), (0.71, 0.15), (0.67, -0.25))):
                a = t + 0.21 * j
                # coming closer, then stopping, searching: the last third sparse
                steps_run(m, "guard", a, d * 0.62, ev, cg(c) - 3.0 - 2.0 * j, c["pan"] + pn, c["sfx"] if j == 0 else None,
                          rise_db=4.0, lpf_end=None, k0=10 * j)
                for q in range(2):
                    step(m, "guard", a + d * 0.62 + (0.9 + 0.7 * q) * (1 + 0.2 * j), cg(c) - 2.0 - 2.0 * j,
                         c["pan"] + pn, seed=40 + 10 * j + q)
    elif s == "snow_steps_girl":
        steps_run(m, "girl_run", t, d, 0.2, cg(c), c["pan"], s)
    elif s == "snow_steps_mother":
        steps_run(m, "mother_run", t, d, 0.28, cg(c), c["pan"], s, pan_end=c["pan"] - 0.2)
    elif s in ("far_steps", "far_steps_hobnail"):
        if "nearer" in txt or "coming" in txt:
            steps_run(m, "guard", t, d, 0.6, cg(c), c["pan"], s, rise_db=6.0, lpf_end=None)
        else:
            steps_run(m, "guard", t, d, 0.62, cg(c), c["pan"], s, lpf_end=1600.0)
    elif s == "boots_snow":
        if "away" in txt or "receding" in txt:
            steps_run(m, "guard_run", t, d, 0.4, cg(c), c["pan"], s, fade_db=10.0, lpf_end=1500.0, pan_end=c["pan"] - 0.3)
        else:
            steps_run(m, "guard", t, d, 0.55, cg(c), c["pan"], s, pan_end=c["pan"] * 0.3)
    else:
        steps_run(m, "mother", t, d, 0.33, cg(c), c["pan"], s)


def h_boots_stop(m, c):
    step(m, "guard", c["t"], cg(c), c["pan"], label=c["sfx"])
    r = rng("bstop", c["t"])
    m_ = n_of(0.2)
    sc = dsp.friction(m_, 220.0, r, jitter=0.3, body=[(1300.0, 7, 1.0), (2800.0, 9, 0.6), (4400.0, 11, 0.3)])
    fol(m, lvl(norm(sc) * swell(m_, 0.2)), c["t"] + 0.05, cg(c) - 4.0, c["pan"], bus="feet")


def h_bare_ice(m, c):
    fol(m, bare_ice_step(_sd(c) % 5, 0.9 if "knock" in c["text"] else 0.5), c["t"], cg(c), c["pan"], c["sfx"], bus="feet")


def h_bark(m, c):
    s = c["sfx"]
    hard = 0.7 if s == "trunk_step_up" else 0.45
    fol(m, bark_knock(_sd(c) % 5, hard, 0.25 if s == "trunk_step_up" else 0.4), c["t"], cg(c), c["pan"], s, bus="feet")


def h_wood_creak(m, c):
    txt = c["text"]
    d = 0.3 if ("short" in txt or "sharp" in txt) else 1.3 if "long thin" in txt else 1.0 if "long" in txt else 0.7
    low = 0.8 if "thin" in txt else 1.0
    fol(m, wood_creak(d, _sd(c) % 7, low), c["t"], cg(c), c["pan"], c["sfx"], align=None)


def h_wood_knock(m, c):
    fol(m, wood_knock(_sd(c) % 3), c["t"], cg(c), c["pan"], c["sfx"])


def h_crawl(m, c):
    s, d = c["sfx"], c.get("dur") or 0.8
    bark = s == "crawl_scrape"
    heavy = 0.6 if ("under the wire" in c["text"] or bark) else 0.25
    fol(m, crawl(round(d, 2), _sd(c) % 5, 0.25 if bark else 0.28, heavy, bark), c["t"], cg(c), c["pan"], s, align=None)


def h_slide(m, c):
    s, d = c["sfx"], c.get("dur") or 0.5
    if s == "ice_slide":
        fol(m, body_slide(round(d, 2), _sd(c) % 3, 1.0, False), c["t"], cg(c), c["pan"], s, align=None)
    elif s == "cloth_scrape":
        fol(m, body_slide(0.3, _sd(c) % 3, 0.0, True), c["t"], cg(c), c["pan"], s, align=None)
    else:
        fol(m, body_slide(round(d, 2), _sd(c) % 3, 0.0, True), c["t"], cg(c), c["pan"], s, align=None)


def h_body_fall(m, c):
    x = lp(rec("body_fall", 0.0, 1.3, 0.0, None, 60.0, 0.002, 0.2), 3500.0)
    fol(m, x, c["t"], cg(c), c["pan"], c["sfx"], bus="feet")
    fol(m, snow_whump(_sd(c) % 3, 0.8), c["t"] + 0.02, cg(c) - 4.0, c["pan"], bus="feet")


def h_whump(m, c):
    s = c["sfx"]
    if s == "snow_thump":
        fol(m, snow_whump(1, 1.0), c["t"], cg(c), c["pan"], s, bus="feet")
        fol(m, snow_whump(2, 0.6), c["t"] + 0.1, cg(c) - 4.0, c["pan"] + 0.1, bus="feet")
    else:
        fol(m, snow_whump(_sd(c) % 3, 1.0), c["t"], cg(c), c["pan"], s, bus="feet")


def h_kneel(m, c):
    step(m, "kneel", c["t"], cg(c), c["pan"], label=c["sfx"])
    fol(m, wool(0.3, _sd(c), 0.4, 0.4), c["t"] + 0.12, cg(c) - 6.0, c["pan"])
    r = rng("brush", c["t"])
    m_ = n_of(0.3)
    br = bp(dsp.crackle(m_, 800.0, r), 1500.0, 6000.0) * swell(m_, 0.3)
    fol(m, lvl(br), c["t"] + 0.3, cg(c) - 8.0, c["pan"])


def h_boot_lift(m, c):
    r = rng("lift", c["t"])
    m_ = n_of(0.14)
    sq = dsp.friction(m_, 650.0 + 500.0 * tax(m_) / 0.14, r, jitter=0.15, body=[(1250.0, 9, 1.0), (2400.0, 11, 0.4)])
    fol(m, lvl(norm(sq) * swell(m_, 0.14)), c["t"], cg(c), c["pan"], c["sfx"], bus="feet", align=None)


def h_dig(m, c):
    fol(m, snow_dig(_sd(c) % 3), c["t"], cg(c), c["pan"], c["sfx"], bus="feet")


# ---- breath (OPPOSITE's recordings), gasps, the grunt
def h_breath(m, c):
    s, txt, t, d = c["sfx"], c["text"], c["t"], c.get("dur") or 0.0
    g_, pn = cg(c), c["pan"]
    if s in ("her_breath",):
        if "holding" in txt and "shaking" in txt:
            breathe(m, rec("her_breath", 1.38, 2.0, -1.0, 4500.0, None, 0.01, 0.15, 0.55, 7.5), t, g_, pn, s)
        elif "intake" in txt:
            breathe(m, rec("gasp_b", 0.0, 0.3, -1.0, 4000.0, None, 0.004, 0.08), t, g_ - 2.0, pn, s)
        elif "straining" in txt:
            breathe(m, b_her(max(d, 1.0), 1.3, -1.0, 4500.0), t, g_, pn, s)
        elif "tired" in txt:
            breathe(m, b_her(max(d, 1.0), 2.6, -2.0, 4000.0), t, g_, pn, s)
        elif "receding" in txt:
            x = env_db(b_her(max(d, 1.0), 0.4, 0.0, 5000.0), [(0.0, 0.0), (max(d, 1.0), -14.0)])
            breathe(m, x, t, g_, pn, s, lpf=3000.0)
        elif d >= 0.8:
            breathe(m, b_her(d, 0.0, 0.0, 3800.0), t, g_, pn, s)
        else:
            breathe(m, rec("her_breath", 1.38, 1.95, 0.0, 4800.0, None, 0.01, 0.1), t, g_, pn, s)
    elif s == "girl_breath":
        if d >= 0.8:
            breathe(m, b_girl(d), t, g_, pn, s)
        else:
            breathe(m, rec("her_breath", 3.0, 3.4, 3.0, 6000.0, None, 0.01, 0.08), t, g_, pn, s)
    elif s in ("panting", "panting_carry"):
        far_ = "far" in txt
        dd = max(d, 1.0)
        if s == "panting_carry":
            breathe(m, b_her(dd, 0.9, -1.0, 1800.0), t, g_, pn, s)
        else:
            breathe(m, b_her(dd, 0.0, 0.0, 2600.0 if far_ else 4600.0), t, g_, pn, s)
            breathe(m, b_girl(dd, 2.1), t + 0.17, g_ - 4.0, pn - 0.1, lpf=3000.0 if far_ else None)
    elif s in ("held_breath", "breath_catch"):
        breathe(m, dsp.fade(np.asarray(rec("gasp_a", 0.0, 0.3, -1.0, 3200.0, None, 0.004, 0.04))[:n_of(0.2)], 0.0, 0.05),
                t, g_, pn, s)
    elif s == "girl_gasp":
        breathe(m, rec("gasp_a", 0.0, 0.32, 3.0, 6000.0, None, 0.003, 0.08), t, g_, pn, s)
    elif s == "girl_whimper_breath":
        breathe(m, rec_loop("her_breath", round(max(d, 0.6), 3), 0.0, 5.95, 3.0, 6000.0, 0.5, 0.12, 0.35), t, g_, pn, s)
    elif s == "haul_effort":
        breathe(m, rec("her_breath", 1.38, 1.95, -1.0, 4000.0, None, 0.01, 0.12), t, g_, pn, s)
        r = rng("pourS", t)
        m_ = n_of(0.5)
        sn = bp(dsp.crackle(m_, 1200.0, r), 1200.0, 7000.0) * np.exp(-tax(m_) / 0.15)
        fol(m, lvl(sn), t + 0.1, g_ - 4.0, pn, bus="feet")
    elif s in ("stop_breath", "breath_stop", "rise_breath"):
        semis = -2.0 if s == "rise_breath" else -1.0
        breathe(m, rec("her_breath", 1.38, 2.0, semis, 4200.0, None, 0.01, 0.2), t, g_, pn, s)
        if "girl" in txt:
            breathe(m, rec("her_breath", 3.0, 3.4, 3.0, 6000.0, None, 0.01, 0.08), t + 0.45, g_ - 5.0, pn + 0.1)
    elif s in ("breath_slows", "held_breath_carry"):
        breathe(m, b_her(max(d, 0.6), 3.2, -3.0, 2200.0), t, g_, pn, s)
    elif s == "throw_effort":
        breathe(m, rec("gasp_b", 0.0, 0.26, -2.0, 3600.0, None, 0.003, 0.08), t, g_, pn, s)
    elif s == "girl_flinch":
        breathe(m, rec("gasp_a", 0.0, 0.22, 3.0, 6000.0, None, 0.003, 0.06), t, g_, pn, s)
        fol(m, wool(0.25, _sd(c), 0.3), t + 0.05, g_ - 4.0, pn)
    elif s == "idea_breath":
        breathe(m, rec("gasp_a", 0.0, 0.16, 1.0, 2000.0, None, 0.003, 0.05), t, g_, pn, s)
    elif s == "breath_held":
        breathe(m, dsp.fade(np.asarray(rec("gasp_a", 0.0, 0.2, -2.0, 2500.0, None, 0.004, 0.03))[:n_of(0.12)], 0.0, 0.04),
                t, g_ - 3.0, pn, s)
        fol(m, reed_tick(_sd(c) % 4), t + 0.3, g_ - 2.0, pn + 0.3)
    elif s in ("guard_breath", "guard_breath_heavy"):
        x = b_guard(max(d, 1.0), 0.0, s == "guard_breath_heavy")
        if "slowing" in txt:
            x = b_guard(max(d, 1.0), 0.3, False)
        breathe(m, x, t, g_, pn, s)
    elif s == "guard_breath_stop":
        breathe(m, lp(rec("his_breath", 1.95, 2.9, -1.5, None, 80.0, 0.05, 0.2), 1500.0), t + 0.6, g_, pn, s)
        m.mark(t, s)
    elif s == "guard_sniff":
        breathe(m, lp(rec("his_breath", 1.3, 1.62, 1.0, None, 120.0, 0.01, 0.06), 2500.0), t, g_, pn, s)
    elif s == "gasp_stifled":
        x = np.asarray(rec("gasp_b", 0.02, 0.32, 0.0, 4000.0, None, 0.003, 0.03))
        k = n_of(0.13)
        y = np.concatenate([x[:k], lp(x[k:k + n_of(0.12)], 700.0) * np.linspace(1.0, 0.0, len(x[k:k + n_of(0.12)]))])
        breathe(m, dsp.fade(y, 0.0, 0.03), t, g_, pn, s)
        fol(m, wool(0.15, _sd(c), 0.3), t + 0.1, g_ - 6.0, pn)
    elif s == "gasp_man":
        choke = "choked" in txt
        x = gasp_man(_sd(c), choke)
        breathe(m, x, t, g_, pn, s, lpf=2200.0 if "further" in txt else None)
    elif s == "gasp_b":
        breathe(m, rec("gasp_b", 0.0, 0.55, 0.0, 6000.0, None, 0.003, 0.1), t, g_, pn, s)
    elif s == "panting_man":
        far_ = "far" in txt or "smaller" in txt
        breathe(m, b_man_pant(max(d, 0.8), _sd(c) % 5 * 0.7, far_), t, g_, pn, s)
    elif s == "his_breath":
        if "slowed" in txt or "shaking" in txt:
            x = rec_loop("his_breath", round(max(d, 1.0), 3), 1.2, 2.95, -2.5, 3600.0, 0.0, 0.2, 0.45)
        else:
            x = b_guard(max(d, 1.0), 0.0, "gasping" in txt) if d > 1.4 else rec("his_breath", 1.2, 2.95, -0.5, 4500.0,
                                                                                  80.0, 0.03, 0.15)
        breathe(m, x, t, g_, pn, s)
    else:
        breathe(m, rec("her_breath", 1.38, 1.95, 0.0, 4800.0, None, 0.01, 0.1), t, g_, pn, s)


def h_grunt(m, c):
    txt = c["text"]
    k = 1 if ("heave" in txt) else 2 if ("pushes" in txt or "knee" in txt) else 0
    grunt(m, c["t"], cg(c), k, c["pan"], c["sfx"])


def h_chatter(m, c):
    fol(m, chatter(round(c.get("dur") or 2.0, 2), _sd(c) % 3), c["t"], cg(c), c["pan"], c["sfx"], bus="vox", align=None)


# ---- cloth, wool, hands
def h_cloth(m, c):
    s, txt, t, d = c["sfx"], c["text"], c["t"], c.get("dur") or 0.0
    g_, pn, sd = cg(c), c["pan"], _sd(c)
    heavy_ = any(w in txt for w in ("greatcoat", "coat", "sleeve", "hat"))
    if s in ("cloth_rustle", "mitten_rustle", "hitch_far", "girl_turn", "coat_wrap", "wool_slide", "scarf_unwind",
             "lift_swing"):
        dd = d if d else (0.6 if s in ("coat_wrap",) else 0.35)
        if s == "scarf_unwind" or s == "coat_wrap":
            x = wool(round(max(dd, 0.3), 2), sd, 0.5, 0.5)
        elif heavy_ and s == "cloth_rustle" and "shawl" not in txt:
            x = coat(round(min(max(dd, 0.25), 1.4), 2), sd)
        else:
            x = wool(round(min(max(dd, 0.2), 1.4), 2), sd, 0.3, 0.55)
        fol(m, x, t, g_, pn, s, align=None, lpf=2200.0 if "far" in txt else None)
        if s == "lift_swing":
            fol(m, coat(0.45, sd + 1), t + 0.1, g_ - 2.0, pn)
    elif s in ("coat_swish", "coat_turn", "cloth_whip"):
        fol(m, coat(0.32, sd), t, g_, pn, s, align=None)
        if s == "cloth_whip":
            fol(m, lp(mono(DC.whip_down(0.28, sd % 3)), 2500.0), t, g_ - 6.0, pn)
        if s == "coat_turn":
            step(m, "mother", t + 0.12, g_ - 2.0, pn, seed=sd)
    elif s in ("crouch", "crouch_rustle"):
        fol(m, coat(0.45, sd), t, g_, pn, s, align=None)
        step(m, "kneel", t + 0.18, g_ - 2.0, pn, seed=sd)
        if s == "crouch":
            fol(m, DC.glove_creak(sd % 3, 0.35), t + 0.05, g_ - 6.0, pn)
    elif s == "rise":
        fol(m, coat(0.5, sd), t, g_, pn, s, align=None)
        fol(m, DC.glove_creak(sd % 3, 0.4), t + 0.1, g_ - 5.0, pn)
        fol(m, lantern_clink(sd % 3, 0.2), t + 0.25, g_ - 10.0, pn)
    elif s == "girl_slide_off":
        fol(m, wool(0.35, sd, 0.6, 0.5), t, g_, pn, s, align=None)
        th = sfx._thump(n_of(0.12), 140.0, 85.0, 0.008, 0.05)
        fol(m, lvl(th), t + 0.3, g_ - 4.0, pn)
    elif s == "hitch":
        fol(m, lvl(sfx._thump(n_of(0.14), 130.0, 80.0, 0.008, 0.05)), t, g_, pn, s)
        fol(m, wool(0.3, sd, 0.6), t, g_ - 3.0, pn)
        breathe(m, rec("her_breath", 3.0, 3.45, -1.0, 4000.0, None, 0.01, 0.1), t + 0.05, g_ - 2.0, pn)
    elif s == "cloth_tug":
        fol(m, wool(0.18, sd, 0.4), t, g_, pn, s, align=None)
        fol(m, wire_twang(sd % 3, 0.15, 260.0), t + 0.08, g_ - 8.0, pn)
    elif s == "cloth_stretch":
        fol(m, stretch(sd % 5, 0.8 if "snaps" in txt else 0.5), t, g_, pn, s)
        if "boot digs" in txt:
            step(m, "mother", t + 0.04, g_ - 3.0, pn, seed=sd)
    elif s == "cloth_pull":
        if d >= 1.0:
            k = 0
            while k * 0.45 < d - 0.05:
                fol(m, wool(0.22, sd + k, 0.4, 0.4), t + k * 0.45, g_ - (1.0 if k % 2 else 0.0), pn, s if k == 0 else None,
                    align=None)
                fol(m, stretch((sd + k) % 5, 0.4), t + k * 0.45 + 0.12, g_ - 6.0, pn)
                k += 1
        else:
            fol(m, wool(round(max(d, 0.2), 2), sd, 0.4, 0.4), t, g_, pn, s, align=None)
    elif s == "cloth_whoosh":
        fol(m, wool_whoosh(sd % 3, 0.8 if "harder" in txt else 0.5), t, g_, pn, s, align=None)
    elif s == "cloth_slap":
        fol(m, cloth_slap(sd % 3, "snow" in txt), t, g_, pn, s)
    elif s == "cloth_slide":
        fol(m, wool(round(max(d, 0.25), 2), sd, 0.3, 0.3), t, g_, pn, s, align=None)
        fol(m, crawl(round(max(d, 0.25), 2), sd % 5, 0.19, 0.2), t, g_ - 6.0, pn)
    elif s in ("cloth_grab", "glove_grab"):
        fol(m, squeeze(sd % 3, 1.0), t, g_, pn, s)
        fol(m, wool(0.12, sd, 0.6), t, g_ - 5.0, pn)
    elif s == "wool_wind":
        dd = max(d, 0.25)
        k = 0
        while k * 0.17 < dd - 0.05:
            fol(m, wool(0.16, sd + k, 0.3, 0.5), t + k * 0.17, g_ - 1.0 * (k % 2), pn, s if k == 0 else None, align=None)
            k += 1
    elif s == "mitten_grab":
        fol(m, wool(0.12, sd, 0.4, 0.5), t, g_, pn, s, align=None)
        fol(m, lvl(sfx._thump(n_of(0.08), 180.0, 110.0, 0.005, 0.02)), t, g_ - 6.0, pn)
    elif s == "hands_rub":
        fol(m, hands_rub(round(max(d, 0.4), 2), sd % 3), t, g_, pn, s, align=None)
    else:
        fol(m, wool(0.3, sd), t, g_, pn, s, align=None)


# ---- the ice and the water
def h_ice(m, c):
    s, txt, t, d = c["sfx"], c["text"], c["t"], c.get("dur") or 0.0
    g_, pn, sd = cg(c), c["pan"], _sd(c)
    far_ = "far" in txt or "downstream" in txt
    if s == "ice_groan":
        x = ice_groan(round(max(d, 1.2) if d else 1.6, 2), sd % 5, 1.2 if "deep" in txt else 1.0)
        fol(m, x, t, g_, pn, s, align=None, lpf=1100.0 if far_ else None, kind="hall" if far_ else None,
            wet=-8.0 if far_ else None)
    elif s == "ice_boom":
        fol(m, ice_boom(round(max(d, 1.5), 2), sd % 3), t, g_, pn, s, kind="hall", wet=-14.0)
    elif s == "ice_crack":
        size = 1.0 if ("the crack" in txt or "huge" in txt) else 0.8
        fol(m, ice_crack(size, sd % 5, 1.0, 1), t, g_, pn, s, kind="hall", wet=-18.0)
    elif s == "ice_crack_clean":
        x = np.asarray(ice_crack(0.7, sd % 5, 1.8, 1)).copy()
        gl = glass_tink(93, 1)
        k = min(len(x), len(gl))
        x[n_of(0.01):k] += 0.25 * norm(np.asarray(gl))[:k - n_of(0.01)]
        fol(m, x, t, g_, pn, s, kind="hall", wet=-18.0)
    elif s in ("ice_crack_small", "ice_snap"):
        fol(m, ice_crumble(sd % 5, 0.7 if s == "ice_snap" else 0.5), t, g_, pn, s)
    elif s == "ice_pew":
        fol(m, pew(round(max(d, 0.15), 3) if d else 0.3, 7600.0, 300.0, sd % 5, 2), t, g_, pn, s, room_=False)
    elif s == "ice_tick":
        fol(m, ice_tick(sd % 5), t, g_, pn, s, room_=False)
    elif s == "ice_sing":
        fol(m, ice_sing(round(max(d, 0.8), 2), sd % 3), t, g_, pn, s, room_=False)
    elif s == "floe_grind":
        fol(m, floe_grind(round(max(d, 0.4), 2), sd % 3), t, g_, pn, s, align=None)
    elif s == "ice_break":
        fol(m, ice_break(sd % 3), t, g_ - 2.0, pn, s, kind="hall", wet=-16.0)
    elif s == "ice_scrape":
        dd = d if d else 0.35
        fol(m, scrape_ice(round(dd, 2), sd % 5, max(2, int(round(dd / 0.3)))), t, g_, pn, s, align=None)
    elif s == "glove_ice":
        fol(m, glove_slap(sd % 5), t, g_, pn, s)
    elif s == "glove_slip":
        fol(m, glove_slip(sd % 5), t, g_, pn, s, align=None)


def h_water(m, c):
    s, t, d = c["sfx"], c["t"], c.get("dur") or 0.0
    g_, pn, sd = cg(c), c["pan"], _sd(c)
    if s in ("splash", "splash_small", "splash_big"):
        size = 0.35 if s == "splash_small" else 1.0 if s == "splash_big" else 0.7
        fol(m, splash(size, sd % 5), t, g_, pn, s)
    elif s == "plunge":
        fol(m, plunge(sd % 3), t, g_ - 2.0, pn, s)
    elif s == "surface_burst":
        fol(m, surface_burst(sd % 3, 1.0), t, g_, pn, s)
    elif s == "water_heave":
        fol(m, pour(0.7, sd % 3, 1.0), t, g_, pn, s, align=None)
        fol(m, splash(0.4, sd % 5), t, g_ - 6.0, pn)
    elif s == "bubbles":
        fol(m, bubbles(round(max(d, 0.3), 2), sd % 5, 0.7), t, g_, pn, s, room_=False, align=None)
    elif s == "water_lap":
        fol(m, water_lap(round(max(d, 0.5), 2), sd % 5, 2.2, 0.45), t, g_, pn, s, align=None)
    elif s == "water_welling":
        fol(m, welling(round(max(d, 0.4), 2), sd % 3), t, g_, pn, s, align=None)
    elif s == "stone_plop":
        fol(m, stone_plop(sd % 3), t, g_, pn, s, room_=False)
    elif s == "water_trickle":
        fol(m, trickle(round(max(d, 0.5), 2), sd % 3), t, g_, pn, s, align=None)
    elif s == "water_drip":
        fol(m, drips(round(max(d, 0.5), 2), sd % 3), t, g_, pn, s, align=None)
    elif s == "clunk_under":
        r = rng("clunk", t)
        h = sfx._hit(r, np.array([210.0, 470.0, 900.0]) * r.uniform(0.9, 1.1), [0.12, 0.09, 0.06], click=0.3)
        x = lp(norm(h) + 0.6 * sfx._thump(len(h), 120.0, 70.0, 0.01, 0.08), 650.0)
        fol(m, lvl(x), t, g_, pn, s, kind="cell", wet=-8.0)
    elif s == "swim_strokes":
        fol(m, strokes(round(max(d, 0.8), 2), sd % 3), t, g_, pn, s, room_=False, align=None)


# ---- the guard's world: lantern, watch, whistles, the searchlight, the hut
def h_lantern(m, c):
    s, txt, t, d = c["sfx"], c["text"], c["t"], c.get("dur") or 0.0
    g_, pn, sd = cg(c), c["pan"], _sd(c)
    far_ = "far" in s or "far" in txt
    kw = dict(lpf=2400.0, kind="court", wet=-10.0) if far_ else {}
    if s in ("lantern_creak", "lantern_creak_far", "lantern_squeak"):
        every = 0.55 if s == "lantern_squeak" else 0.62
        many = "lanterns" in txt
        n_ = max(1, int(round(d / every))) if d else 1
        for k in range(n_):
            fol(m, lantern_creak((sd + k) % 7, 0.18 + 0.05 * (k % 2), 0.35), t + k * every, g_ - 1.5 * (k % 2), pn,
                s if k == 0 else None, align=None, **kw)
            if many:
                fol(m, lantern_creak((sd + k + 3) % 7, 0.2, 0.3), t + k * every + 0.27, g_ - 3.0, pn + 0.25, align=None,
                    **kw)
    elif s == "lantern_lowered":
        fol(m, lantern_clink(sd % 3, 0.4), t, g_, pn, s)
    elif s == "lantern_swing_down":
        fol(m, lantern_clink(sd % 3, 0.9), t, g_, pn, s)
        fol(m, flame_gutter(sd % 3, 0.5), t + 0.04, g_ - 6.0, pn)
    elif s == "lantern_raise":
        fol(m, lantern_creak(sd % 7, 0.28, 0.6), t, g_, pn, s, align=None)
        fol(m, glass_tink(91, sd % 3), t + 0.18, g_ - 8.0, pn)
    elif s == "lantern_hiss":
        fol(m, lantern_hiss(round(max(d, 0.5), 2), sd % 3), t, g_ + 4.0, pn, s, align=None)
    elif s == "lantern_sink":
        r = rng("sink", t)
        y = np.zeros(n_of(max(d, 0.5) + 0.3))
        tt, k = 0.0, 0
        while tt < max(d, 0.5):
            dsp.mix_into(y, OF.glass_tick(k % 3) * r.uniform(0.4, 1.0) * (1.0 - 0.6 * tt / max(d, 0.5)), n_of(tt))
            tt += 0.12 + 0.25 * r.uniform() * (1.0 + tt)
            k += 1
        fol(m, lvl(lp(y, 1200.0)), t, g_, pn, s, kind="cell", wet=-10.0, align=None)


def h_watch(m, c):
    s, t, d = c["sfx"], c["t"], c.get("dur") or 2.0
    if s == "watch_tick":
        fol(m, watch_ticks(round(d, 2), 0), t, cg(c), c["pan"], s, room_=False)
    else:
        fol(m, watch_click(_sd(c) % 3, 1.0), t, cg(c), c["pan"], s, wet=-26.0)


def h_whistle(m, c):
    s, txt, t = c["sfx"], c["text"], c["t"]
    g_, pn, sd = cg(c), c["pan"], _sd(c)
    if s == "far_whistle":
        far_whistle(m, t, g_, pn, s, sd % 5, 0.42, dist=0.8)
    elif s == "far_lantern_wake":
        far_whistle(m, t, g_, pn, s, sd % 5, 0.3, dist=1.0)
        y = dsp.reverb(dsp.pan_mono(lp(lantern_clink(sd % 3, 0.2), 2000.0), pn), "court", wet_db=-6.0, seed=sd % 5)
        m.put("efx", y, t + 0.35, g_ - 8.0)
        m.note(c, "the far whistle and a lantern's clink; no voice for the 'voice-less call'")
    else:
        if "two short" in txt:
            x = whistle(0.15, sd % 5, 2950.0, 2, 0.09)
        elif "long" in txt:
            x = whistle(0.85, sd % 5, 2950.0, 1, 0.1)
        else:
            x = whistle(0.42, sd % 5, 2800.0 + 150.0 * (sd % 3), 1, 0.1)
        far_ = "further" in txt or "third" in txt
        fol(m, x, t, g_ - 7.0, pn, s, kind="court", wet=-12.0 if not far_ else -6.0, lpf=4000.0 if far_ else None)


def h_search(m, c):
    s, t, d = c["sfx"], c["t"], c.get("dur") or 1.5
    g_, pn, sd = cg(c), c["pan"], _sd(c)
    if s in ("searchlight_clank", "motor_clank"):
        far_clank(m, t, g_, pn, s, sd % 4)
    elif s == "searchlight_swing":
        fol(m, motor_rev(round(d, 2), sd % 3), t, g_ + BED_LIFT * 0.5, pn, s, kind="court", wet=-8.0, align=None)
    elif s == "beam_pass":
        fol(m, sizzle(round(d, 2), sd % 3), t, g_ - 4.0, pn, s, kind="court", wet=-12.0, align=None)
    elif s == "searchlight_hum":
        hum_layer(m, t, t + d, [(t, c["gain_db"]), (t + d, c["gain_db"])], sd, s, 0.3, 0.0, pn)


def h_hut(m, c):
    s, t, d = c["sfx"], c["t"], c.get("dur") or 1.0
    g_, pn, sd = cg(c), c["pan"], _sd(c)
    if s == "door_open":
        fol(m, door_flung(sd % 3), t, g_, pn, s)
    elif s == "door_latch":
        fol(m, door_latch(sd % 3), t, g_, pn, s)
    elif s == "door_creak":
        fol(m, door_creak(round(max(d, 0.3), 2), sd % 3), t, g_, pn, s, align=None)
    elif s == "door_shut":
        fol(m, door_shut(sd % 3), t, g_, pn, s)
    elif s == "boot_wood":
        fol(m, board_step(sd % 3), t, g_, pn, s, bus="feet")
    elif s == "stove_crackle":
        fol(m, dsp.fade(lvl(stove(round(d, 2), sd % 3), bed=True), 0.2, 0.3), t, bedg(c), pn, s, align=None)
    elif s == "room_tone_warm":
        fol(m, dsp.fade(room_warm(round(d, 2), sd % 3), 0.35, 0.03), t, bedg(c), pn, s, align=None)


def h_wire(m, c):
    s, txt, t, d = c["sfx"], c["text"], c["t"], c.get("dur") or 0.0
    g_, pn, sd = cg(c), c["pan"], _sd(c)
    if s == "wire_creak":
        fol(m, wire_creak(round(max(d, 0.25), 2), sd % 3, 0.7 if "gently" in txt else 1.0), t, g_, pn, s, align=None)
    elif s == "wire_twang":
        ring = 0.9 if (d >= 0.8 or "quivers" in txt) else 0.3
        fol(m, wire_twang(sd % 5, ring), t, g_, pn, s)
    elif s == "wire_snag":
        fol(m, wool(0.12, sd, 0.2, 0.2), t, g_, pn, s, align=None)
        fol(m, wire_twang(sd % 5, 0.2, 230.0), t + 0.02, g_ - 4.0, pn)
    elif s == "rip":
        fol(m, rip(sd % 3, 0.16), t, g_, pn, s)


def h_reeds(m, c):
    s, t, d = c["sfx"], c["t"], c.get("dur") or 0.5
    if s == "reed_tick":
        fol(m, reed_tick(_sd(c) % 4), t, cg(c), c["pan"], s)
    else:
        fol(m, reeds(round(max(d, 0.3), 2), _sd(c) % 5, 1.0), t, cg(c), c["pan"], s, align=None)


def h_misc(m, c):
    s, t, d = c["sfx"], c["t"], c.get("dur") or 0.0
    g_, pn, sd = cg(c), c["pan"], _sd(c)
    if s == "far_dog":
        y = dsp.reverb(dsp.pan_mono(far_bark(sd % 3), pn), "court", wet_db=-4.0, seed=sd % 5)
        m.put("efx", y, t, g_, label=s)
        m.note(c, "a synthesised bark (an approximation: no recording of a dog)")
    elif s == "wind_gust":
        x = fx("wind_gust", dur=round(max(d, 0.6), 2), seed=sd % 5)
        fol(m, x, t, bedg(c), pn, s, room_=False, align=None)
        fol(m, wool(0.5, sd, 0.1, 0.1), t + 0.2, g_ - 10.0, pn)
    elif s == "snap":
        fol(m, box_snap(sd % 3), t, g_, pn, s)
    elif s == "music_box_lid":
        fol(m, box_lid(sd % 3), t, g_, pn, s)
    elif s in ("paper_flood", "paper_slide", "paper_settle"):
        kind = {"paper_flood": "flood", "paper_slide": "slide", "paper_settle": "settle"}[s]
        fol(m, paper_sound(kind, round(max(d, 0.3), 2), sd % 5), t, g_, pn, s, room_=False, align=None)
    elif s == "stone_whoosh":
        fol(m, stone_whir(round(max(d, 0.3), 2), sd % 3), t, g_, pn, s, room_=False, align=None)
    elif s == "snow_shimmer":
        m.put("music", glass_shimmer(round(max(d, 0.8), 2), sd % 3), t, g_, pan=pn, label=s, align=None, hall=-18.0)
    elif s in ("snow_hiss", "snow_settle"):
        dd = max(d, 0.5)
        r = rng("hiss", m.sid, t)
        x = snow_hiss_bed(n_of(dd + 0.6), r)
        x = env(x, [(0.0, 0.0), (0.3, 1.0), (dd * 0.5, 0.8), (dd + 0.6, 0.0)] if s == "snow_hiss" else
                [(0.0, 1.0), (dd * 0.3, 0.7), (dd + 0.3, 0.0)])
        m.put("amb", lvl(x, bed=True), t, bedg(c), label=s, align=None)
    elif s == "teeth_chatter":
        h_chatter(m, c)


FOLEY = {}
for _tag in STEP_TAGS:
    FOLEY[_tag] = h_step
FOLEY.update({
    "girl_boots_land": h_girl_land, "snow_scuff": h_scuff, "snow_scuff_girl": h_scuff,
    "snow_steps_guards": h_steps_group, "snow_steps_girl": h_steps_group, "snow_steps_mother": h_steps_group,
    "far_steps": h_steps_group, "far_steps_hobnail": h_steps_group, "boots_snow": h_steps_group,
    "boots_stop": h_boots_stop, "step_bare_ice": h_bare_ice, "boot_ice": h_bare_ice,
    "trunk_step_up": h_bark, "step_on_bark": h_bark, "trunk_creak": h_wood_creak, "wood_creak": h_wood_creak,
    "wood_knock": h_wood_knock, "crawl_scrape": h_crawl, "snow_crawl": h_crawl,
    "body_slide_wood": h_slide, "ice_slide": h_slide, "cloth_scrape": h_slide, "body_fall": h_body_fall,
    "snow_thump": h_whump, "muffled_fall": h_whump, "snow_kneel": h_kneel, "boot_lift_snow": h_boot_lift,
    "dig_stone": h_dig, "grunt": h_grunt, "grunt_knight": h_grunt, "teeth_chatter": h_chatter,
    "ice_groan": h_ice, "ice_boom": h_ice, "ice_crack": h_ice, "ice_crack_clean": h_ice, "ice_crack_small": h_ice,
    "ice_snap": h_ice, "ice_pew": h_ice, "ice_tick": h_ice, "ice_sing": h_ice, "floe_grind": h_ice, "ice_break": h_ice,
    "ice_scrape": h_ice, "glove_ice": h_ice, "glove_slip": h_ice,
    "splash": h_water, "splash_small": h_water, "splash_big": h_water, "plunge": h_water, "surface_burst": h_water,
    "water_heave": h_water, "bubbles": h_water, "water_lap": h_water, "water_welling": h_water, "stone_plop": h_water,
    "water_trickle": h_water, "water_drip": h_water, "clunk_under": h_water, "swim_strokes": h_water,
    "lantern_creak": h_lantern, "lantern_creak_far": h_lantern, "lantern_squeak": h_lantern,
    "lantern_lowered": h_lantern, "lantern_swing_down": h_lantern, "lantern_raise": h_lantern,
    "lantern_hiss": h_lantern, "lantern_sink": h_lantern,
    "watch_click": h_watch, "watch_tick": h_watch, "whistle": h_whistle, "far_whistle": h_whistle,
    "far_lantern_wake": h_whistle, "searchlight_clank": h_search, "motor_clank": h_search,
    "searchlight_swing": h_search, "beam_pass": h_search, "searchlight_hum": h_search,
    "door_open": h_hut, "door_latch": h_hut, "door_creak": h_hut, "door_shut": h_hut, "boot_wood": h_hut,
    "stove_crackle": h_hut, "room_tone_warm": h_hut,
    "wire_creak": h_wire, "wire_twang": h_wire, "wire_snag": h_wire, "rip": h_wire,
    "reeds_rustle": h_reeds, "reed_tick": h_reeds,
    "far_dog": h_misc, "wind_gust": h_misc, "snap": h_misc, "music_box_lid": h_misc, "paper_flood": h_misc,
    "paper_slide": h_misc, "paper_settle": h_misc, "stone_whoosh": h_misc, "snow_shimmer": h_misc,
    "snow_hiss": h_misc, "snow_settle": h_misc,
})
for _tag in ("her_breath", "girl_breath", "panting", "panting_carry", "held_breath", "breath_catch", "girl_gasp",
             "girl_whimper_breath", "haul_effort", "stop_breath", "breath_stop", "rise_breath", "breath_slows",
             "held_breath_carry", "throw_effort", "girl_flinch", "idea_breath", "breath_held", "guard_breath",
             "guard_breath_heavy", "guard_breath_stop", "guard_sniff", "gasp_stifled", "gasp_man", "gasp_b",
             "panting_man", "his_breath"):
    FOLEY[_tag] = h_breath
for _tag in ("cloth_rustle", "mitten_rustle", "hitch_far", "girl_turn", "coat_wrap", "wool_slide", "scarf_unwind",
             "lift_swing", "coat_swish", "coat_turn", "cloth_whip", "crouch", "crouch_rustle", "rise", "girl_slide_off",
             "hitch", "cloth_tug", "cloth_stretch", "cloth_pull", "cloth_whoosh", "cloth_slap", "cloth_slide",
             "cloth_grab", "glove_grab", "wool_wind", "mitten_grab", "hands_rub"):
    FOLEY[_tag] = h_cloth


def rest(m):
    """The foley handlers for every cue of this scene the section has not answered."""
    for i, c in enumerate(m.cues):
        if i in m.done or i in m.covered:
            continue
        h = FOLEY.get(c["sfx"])
        if h is None:
            continue
        h(m, c)
        m.done.add(i)


# ============================================================================ the sections
def take1(m, tag, near=None):
    """This scene's cue with tag (the one nearest `near`, else the first), marked answered; None when
    it has none."""
    best = None
    for i, c in enumerate(m.cues):
        if c["sfx"] != tag or i in m.done:
            continue
        d = 0.0 if near is None else abs(c["t"] - near)
        if best is None or d < best[0] - 1e-9:
            best = (d, i)
    if best is None:
        return None
    m.done.add(best[1])
    return m.cues[best[1]]


def gg(c, default):
    """A cue's gain as the scene writes it (default when there is no such cue)."""
    return float(c["gain_db"]) if c else float(default)


def _idx(c, k):
    return int(c["note"]) if _num(c.get("note")) else k


def cut_dead(x, at, f=0.006):
    """x stopped dead `at` s in (a few ms' fade, no click)."""
    x = np.asarray(x, np.float64)
    k = n_of(max(at, 0.0))
    if k >= len(x):
        return x
    return dsp.fade(x[:max(k, 2)], 0.0, min(f, at / 2.0) if at > 0 else 0.0)


def harms(notes, dur, seed=0, attack=0.4, release=0.5, vib=0.002, amps=None):
    """String harmonics held together (at the catalog's level)."""
    out = None
    for k, p in enumerate(notes):
        a = 1.0 if amps is None else amps[k]
        x = a * OF.harmonic(hz(p), dur, 1.0, seed + 5 * k, attack=attack, release=release, vib=vib)
        out = x if out is None else out + x
    return lvl(out)


@lru_cache(maxsize=None)
def air_tone(dur, seed=0):
    """A still, cold quiet: the faintest high air tone (a high harmonic's breath, the air's hiss)."""
    r = rng("air", round(dur, 2), seed)
    n = n_of(dur)
    t = tax(n)
    h = dsp.pad_to(OF.harmonic(hz(93), max(dur - 0.6, 0.5), 1.0, seed, attack=1.4, release=0.6, vib=0.0015), n)
    nz = np.stack([hpf(bp(dsp.pink(n, r), 3000.0, 9000.0), 2500.0) for _ in range(2)], axis=1)
    e = np.clip(t / 1.2, 0, 1) * np.clip((dur - t) / 0.6, 0, 1)
    y = 0.4 * norm(h)[:, None] * np.array([1.0, 0.85]) + 0.6 * norm(nz) * e[:, None]
    return lvl(y, bed=True)


def hiss_layer(m, t0, t1, pts, seed=0, label=None, xf=0.3, gain=0.0):
    """Falling snow's hiss from t0 to t1, its level following pts [(t, cue dB)]."""
    if not pts or t1 <= t0:
        return
    a, n, amp, top = _bed_curve(t0, t1, pts, xf)
    x = snow_hiss_bed(n, rng("hiss", m.sid, seed)) * amp[:, None]
    m.put("amb", dsp.fade(lvl(x, bed=True), xf, xf), a, top + CUE_TRIM + BED_LIFT + gain, label=label, align=None)


def wind_pts(cues, t_end, default=-26.0, ramp=0.4):
    """A level curve from a scene's wind cues (each holds its level until the next)."""
    pts = []
    for i, (t, d, c) in enumerate(cues):
        pts.append((t + (0.0 if i == 0 else ramp), c["gain_db"]))
        nxt = cues[i + 1][0] if i + 1 < len(cues) else t_end
        pts.append((max(t + 0.01, nxt), c["gain_db"]))
    return pts or [(0.0, default), (t_end, default)]


# ---------------------------------------------------------------------------- s01 THE TITLE
@section("s01")
def s01(m, S):
    L = m.len
    m.ats("T_LAND", tuple(0.75 + 0.25 * i for i in range(7)), "glass tink", n=7)
    m.at("T_CRACK", 4.0, "the crack")
    T_OUT = m.span("T_THREAD_OUT", (7.5, 8.0))
    T_FLOOD = m.span("T_FLOOD", (5.5, 6.3))
    T_SNOW = m.span("T_SNOW_STOP", (9.7, 10.0))
    T_PUSH = m.span("T_PUSH", (11.0, 14.0))
    # the wind, the snow's hiss in it; both fall away when the snow stops
    wg = gg(take1(m, "wind_low"), -24.0)
    hs = take1(m, "hush")
    t_hush = hs["t"] if hs else T_SNOW[1]
    wind_layer(m, 0.0, L, [(0.0, wg - 9.0), (0.9, wg), (T_SNOW[0], wg), (T_SNOW[1] + 0.8, wg - 8.0), (L, wg - 7.0)],
               "open", 1, "wind (s01)")
    hiss_layer(m, 0.0, T_SNOW[1] + 0.2, [(0.0, wg - 12.0), (0.9, wg - 3.0), (T_SNOW[0], wg - 3.0),
                                        (T_SNOW[1] + 0.2, -120.0)], 1, "the snow's hiss")
    m.put("music", air_tone(round(L - t_hush + 0.8, 2), 1), t_hush, gg(hs, -22.0) + CUE_TRIM, label="hush",
          align=None, hall=-16.0)
    # the letters land: a rising run of glass tinks, A harmonic minor
    run = (81, 83, 84, 86, 88, 89, 92)
    for k, (t, d, c) in enumerate(each(m, "glass_tink")):
        i = _idx(c, k)
        fol(m, glass_tink(run[i % 7], i % 3), t, cg(c), c["pan"], "glass_tink", bus="music", kind="hall", wet=-16.0)
    # the thread snaps taut: E6, held to the thread's going
    for t, d, c in each(m, "thread_ping"):
        dd = max(d, T_OUT[1] - t - 0.45)
        m.put("music", thread_note(round(dd, 3), 1, True), t, cg(c) + MUSIC_LIFT - 3.0, label="thread_ping",
              hall=-12.0)
    # THE CRACK: the title's signature, full size - but under s08's crack, the film's
    for t, d, c in each(m, "ice_crack"):
        fol(m, ice_crack(1.0, _sd(c) % 5, 1.0, 1), t, cg(c, -3.5), c["pan"], "ice_crack", kind="hall", wet=-18.0)
    # the map: plucks rising (A3 C4 E4 A4 C5) as the places pop on; an open A under the page
    pl = (57, 60, 64, 69, 72)
    for k, (t, d, c) in enumerate(each(m, "pluck")):
        i = _idx(c, k)
        m.put("music", lvl(pz(pl[i % 5], 0.9, i)), t, cg(c), pan=c["pan"], label="pluck")
    a = T_FLOOD[0]
    strings_at(m, a, (45, 52), T_PUSH[0] - a + 0.4, -33.0 + MUSIC_LIFT, seed=3, attack=1.6, release=1.0, bright=1500.0,
               shape=[(0.0, -6.0), (2.0, 0.0), (T_PUSH[0] - a, -2.0)])
    # the push in: a slow low swell in A minor, into the fence
    ps = take1(m, "push_swell")
    a, b = (ps["t"], ps["t"] + (ps.get("dur") or 3.0)) if ps else T_PUSH
    strings_at(m, a, AM, b - a, gg(ps, -22.0) + CUE_TRIM + MUSIC_LIFT, seed=4, attack=0.5, release=1.3, bright=2400.0,
               label="push_swell", shape=[(0.0, -14.0), (b - a, 0.0)])
    # the searchlight's motor, far
    for t, d, c in each(m, "searchlight_hum"):
        hum_layer(m, t, L, [(t, c["gain_db"] - 10.0), (t + 1.2, c["gain_db"]), (L, c["gain_db"])], 2,
                  "searchlight hum (far)", pan=c["pan"], xf=0.3)


# ---------------------------------------------------------------------------- s02 THE FENCE
@section("s02")
def s02(m, S):
    L = m.len
    m.span("T_MOON", (3.0, 3.5))
    T_SLAP = m.at("T_SLAP", 9.0, "snap")
    wg = gg(take1(m, "wind_low"), -28.0)
    wind_layer(m, 0.0, L, [(0.0, wg), (L, wg)], "open", 2, "wind (s02)")
    hc = take1(m, "searchlight_hum")
    hg = gg(hc, -26.0)
    hum_layer(m, 0.0, L, [(0.0, hg), (13.0, hg), (16.0, hg - 8.0), (L, hg - 10.0)], 3, "searchlight hum",
              beam=True, pan=0.1)
    # the moon: a cold high harmonic, A6
    for t, d, c in each(m, "moon_reveal"):
        m.put("music", harms((MOON,), max(d, 1.5), 2, attack=0.5, release=1.6, vib=0.003), t, cg(c) + MUSIC_LIFT,
              label="moon_reveal", hall=-10.0)
    # the music box: the lullaby's first three notes, the governor whirring; the lid slapped shut
    box = each(m, "music_box")
    if box:
        a = box[0][0]
        if T_SLAP > a:
            m.put("music", dsp.fade(box_whirr(round(T_SLAP - a + 0.04, 2), 1), 0.02, 0.015), a - 0.02,
                  cg(box[0][2], BOX_TRIM) - 15.0, align=None, hall=-24.0)
    for k, (t, d, c) in enumerate(box):
        i = _idx(c, k)
        music_box(m, t, midi(LULLABY[i % len(LULLABY)]), cg(c, BOX_TRIM), "music_box", pan=c["pan"],
                  choke=(T_SLAP - t) if T_SLAP > t else None, name=LULLABY[i % len(LULLABY)])
    # the heartbeat (where the scene puts it)
    for k, (t, d, c) in enumerate(each(m, "heartbeat")):
        heartbeat(m, t, cg(c), 0.24, k, label="heartbeat")
    # running in snow, two rhythms, receding
    for t, d, c in each(m, "run_steps"):
        dd = max(d, 1.0)
        steps_run(m, "mother_run", t, dd, 0.33, cg(c), c["pan"] - 0.05, "run_steps", fade_db=12.0, lpf_end=1600.0)
        steps_run(m, "girl_run", t + 0.07, dd, 0.24, cg(c) - 3.0, c["pan"] + 0.05, None, fade_db=12.0, lpf_end=1600.0,
                  k0=40)
    # the page: a still, cold tone (an open fifth in harmonics, A5 E6)
    for t, d, c in each(m, "page_tone"):
        m.put("music", harms((81, THREAD), max(d, 1.0), 5, attack=0.7, release=0.3, amps=(0.6, 1.0)), t,
              cg(c) + MUSIC_LIFT, label="page_tone", hall=-12.0)


# ---------------------------------------------------------------------------- s03 THE GUARD
@section("s03")
def s03(m, S):
    L = m.len
    T_DOOR = m.at("T_DOOR", 6.2, "door")
    T_OUT = m.span("T_OUT", (6.35, 7.0))
    T_TOUCH = m.at("T_TOUCH", 11.45, "knee")
    T_WHISTLE = m.ats("T_WHISTLE", (12.0, 12.4))
    T_WOODS = m.at("T_WOODS", 14.0)
    tw = T_WHISTLE[0]
    # the wind: through the hut's walls; howling in at the door; outside; then in the pines
    g0 = gg(take1(m, "wind_outside"), -24.0)
    wind_layer(m, 0.0, T_DOOR, [(0.0, g0), (T_DOOR, g0)], "muffled", 3, "wind outside the hut", xf=0.08)
    wb = take1(m, "wind_burst")
    gb = gg(wb, -12.0)
    wind_layer(m, T_DOOR, T_WOODS + 0.4, [(T_DOOR, gb - 8.0), (T_DOOR + 0.25, gb - 3.0), (T_DOOR + 1.3, g0 + 2.0),
                                          (T_WOODS, g0 + 1.0), (T_WOODS + 0.4, g0 - 6.0)],
               "snow", 4, "wind_burst", xf=0.03)
    gl = gg(take1(m, "wind_low"), -26.0)
    wind_layer(m, T_WOODS, L, [(T_WOODS, gl), (L, gl)], "pines", 5, "wind in the pines")
    # the photograph: one low note (A, cellos and basses)
    for t, d, c in each(m, "string_low"):
        dd = max(d, 1.5)
        line_at(m, t, [45], dd, cg(c) + MUSIC_LIFT, seed=7, label="string_low", octaves=(0, -1), bright=1400.0,
                attack=0.6, release=1.2, last=dd)
    # outside, on the trail: a low A and E barely moving; an F (aching) when he finds the child's print
    a = T_OUT[0] + 0.3
    if tw > a + 1.0:
        strings_at(m, a, (45, 52), tw - a, -31.0 + MUSIC_LIFT, seed=8, attack=2.0, release=0.5, bright=1500.0,
                   shape=[(0.0, -6.0), (tw - a, 0.0)])
    if tw > T_TOUCH + 0.2:
        m.put("music", harms((65,), tw - T_TOUCH, 9, attack=0.4, release=0.4), T_TOUCH, -31.0 + MUSIC_LIFT, align=None,
              hall=-14.0)
    # the whistle: the hunt's pulse begins, a note every half bar, under A minor
    pulse(m, tw, L, 1.0, -20.0, 45, (0.75, 1.0), 1, "the hunt's pulse (s03)")
    strings_at(m, tw, AM, L - tw, -27.0 + MUSIC_LIFT, seed=10, attack=0.3, release=0.5, bright=2000.0,
               shape=[(0.0, -6.0), (L - tw, 0.0)])


# ---------------------------------------------------------------------------- s04 THE TRACKS
@section("s04")
def s04(m, S):
    L = m.len
    T_STUMBLE = m.at("T_STUMBLE", 3.25, "gasp")
    T_HITCH = m.span("T_HITCH", (4.8, 5.0))
    T_EXIT = m.at("T_EXIT", 7.1)
    T_HEAD_UP = m.span("T_HEAD_UP", (10.05, 10.3))
    T_LOOK = m.at("T_LOOK", 10.35)
    T_RISE = m.span("T_RISE", (11.0, 11.45))
    rv = take1(m, "river_under_ice")
    t_bank = rv["t"] if rv else 14.0
    # the wind high in the pines (its cues' levels), dropping away at the open bank; the river
    pts = wind_pts(each(m, "wind_pines"), t_bank, -25.0)
    pts += [(t_bank, pts[-1][1]), (t_bank + 0.8, pts[-1][1] - 10.0)]
    wind_layer(m, 0.0, t_bank + 0.8, pts, "pines", 6, "wind in the pines")
    wind_layer(m, t_bank - 0.3, L, [(t_bank - 0.3, -42.0), (t_bank + 0.7, -31.0), (L, -30.0)], "open", 7,
               "wind over the bank")
    if rv:
        river_layer(m, t_bank, L, [(t_bank, rv["gain_db"] - 8.0), (t_bank + 0.7, rv["gain_db"]), (L, rv["gain_db"])],
                    4, "river_under_ice")
        fol(m, ice_groan(2.0, 3, 1.1), t_bank + 0.6, rv["gain_db"] + CUE_TRIM - 4.0, min(1.0, rv["pan"] + 0.2), None,
            lpf=900.0, kind="hall", wet=-6.0, align=None)
    # the searchlight's motor sweeping across, far
    for t, d, c in each(m, "searchlight_hum"):
        hum_layer(m, t, t + d, [(t, c["gain_db"] - 6.0), (t + 0.6, c["gain_db"]), (t + d - 0.6, c["gain_db"]),
                                (t + d, c["gain_db"] - 8.0)], 4, "searchlight_hum", xf=0.4, pan=c["pan"],
                  pan_end=-0.6 * c["pan"])
    # the guard's breathing: it stops as he understands (the stop's own cue), then goes on
    st = peek(m, "guard_breath_stop")
    t_stop = st[0][0] if st else T_HEAD_UP[0]
    for t, d, c in each(m, "guard_breath"):
        e = t + max(d, 1.0)
        if t < t_stop < e - 1.5:
            breathe(m, b_guard(t_stop - t + 0.1, 0.0), t, cg(c), c["pan"], "guard_breath")
            r0 = t_stop + 1.4
            breathe(m, b_guard(e - r0, 0.9), r0, cg(c) - 1.0, c["pan"])
        else:
            breathe(m, b_guard(max(d, 1.0)), t, cg(c), c["pan"], "guard_breath")
    # the score: the pulse on the beat; at the fall it stops and a chord hangs (the F in it);
    # carrying her, a heavier pulse; the guard: a low tense sustain that swells on his look; after them
    pulse(m, 0.0, T_STUMBLE, BEAT, -20.0, 45, (0.8, 1.0), 2, "the hunt's pulse (s04)")
    strings_at(m, 0.0, AM, T_STUMBLE + 0.15, -27.0 + MUSIC_LIFT, seed=11, attack=0.2, release=0.35, bright=2200.0)
    d = T_HITCH[1] - T_STUMBLE
    strings_at(m, T_STUMBLE, AM_F, d, -25.0 + MUSIC_LIFT, seed=12, attack=0.12, release=0.9, bright=2600.0,
               label="the fall: a chord hangs", shape=[(0.0, 0.0), (0.6, -3.0), (d, -7.0)])
    if T_EXIT > T_HITCH[1] + 0.5:
        pulse(m, T_HITCH[1], T_EXIT, 1.0, -21.0, 45, (0.95, 0.75), 3)
    a = T_EXIT + 0.9
    if T_RISE[0] > a + 0.5:
        strings_at(m, a, (45, 52, 53), T_RISE[0] - a, -31.0 + MUSIC_LIFT, seed=13, attack=1.5, release=0.5,
                   bright=1500.0, shape=[(0.0, -5.0), (max(0.1, T_LOOK - a), -3.0), (T_RISE[0] - a, 2.0)])
    if t_bank > T_RISE[0] + 0.5:
        pulse(m, T_RISE[0], t_bank, BEAT, -20.0, 45, (0.8, 1.0), 4, "the hunt's pulse (after them)")
        d = t_bank - T_RISE[0]
        strings_at(m, T_RISE[0], AM_F, d + 1.2, -26.0 + MUSIC_LIFT, seed=14, attack=0.3, release=1.0, bright=2200.0,
                   shape=[(0.0, -3.0), (d, 0.0), (d + 1.2, -12.0)])


# ---------------------------------------------------------------------------- s05 THE RIVER
@section("s05")
def s05(m, S):
    L = m.len
    T_LOOK = m.span("T_LOOK", (4.35, 4.9))
    T_HIT = m.at("T_HIT", 6.0, "punches")
    T_GROAN = m.at("T_GROAN", 7.45, "booming")
    rg = gg(take1(m, "river_under_ice"), -20.0)
    river_layer(m, 0.0, L, [(0.0, rg), (L, rg)], 5, "river_under_ice")
    wo = each(m, "wind_open")
    wg = wo[0][2]["gain_db"] if wo else -28.0
    hs = take1(m, "held_silence")
    t_hs = hs["t"] if hs else 12.0
    wind_layer(m, 0.0, L, [(0.0, wg), (10.0, wg), (t_hs, wg - 3.0), (L, wg - 2.0)], "open", 8, "wind over the river")
    if hs:
        m.mark(t_hs, "held_silence")
    for t, d, c in each(m, "searchlight_hum"):
        hum_layer(m, t, t + d, [(t, c["gain_db"] - 6.0), (t + 0.6, c["gain_db"]), (t + d - 0.6, c["gain_db"]),
                                (t + d, c["gain_db"] - 8.0)], 5, "searchlight_hum", xf=0.4, pan=c["pan"])
    # the ice's harmonics over her look across it, cut dead by the stone's crack
    a = T_LOOK[0]
    if T_HIT > a + 0.3:
        x = cut_dead(shimmer(round(T_HIT - a + 0.5, 3), 1, 88, 3), T_HIT - a, 0.004)
        m.put("music", x, a, -31.0 + MUSIC_LIFT, label="ice harmonics", align=None, hall=None)
    # the ice booms: a low tremolo under it, dying
    tr = env_db(lvl(trem((33, 45), 2.4, 0.7, 2, 9.0)), [(0.0, -10.0), (0.3, 0.0), (2.4, -16.0)])
    m.put("music", tr, T_GROAN + 0.1, -28.0 + MUSIC_LIFT, hall=-18.0)
    # the guard coming: the pulse and A minor with its F, dropping out for the held silence
    gb = peek(m, "guard_breath")
    t_g = gb[0][0] if gb else 10.0
    if t_hs > t_g + 0.5:
        pulse(m, t_g, t_hs, BEAT, -21.0, 45, (0.7, 1.0), 5, "the hunt's pulse (s05)")
        strings_at(m, t_g, AM_F, t_hs - t_g, -27.0 + MUSIC_LIFT, seed=15, attack=0.6, release=0.25, bright=2000.0,
                   shape=[(0.0, -6.0), (t_hs - t_g, 0.0)])


# ---------------------------------------------------------------------------- s06 THE FALSE TRAIL
@section("s06")
def s06(m, S):
    L = m.len
    T_STOP = m.at("T_STOP", 3.55, "she stops")
    T_SIDE_L = m.span("T_SIDE_L", (9.5, 9.75))
    T_HUSH = m.at("T_HUSH", 12.45, "held")
    rg = gg(take1(m, "river_under_ice"), -22.0)
    river_layer(m, 0.0, L, [(0.0, rg), (L, rg)], 6, "river_under_ice")
    wo = each(m, "wind_open")
    g1 = wo[0][2]["gain_db"] if wo else -27.0
    g2, t2 = (wo[1][2]["gain_db"], wo[1][0]) if len(wo) > 1 else (-28.0, 13.0)
    cq = take1(m, "close_quiet")
    tq = cq["t"] if cq else 4.0
    wind_layer(m, 0.0, L, [(0.0, g1), (tq - 0.3, g1), (tq + 0.8, g1 - 9.0), (t2 - 0.6, g1 - 8.0), (t2 + 0.5, g2),
                           (L, g2)], "open", 9, "wind over the river")
    if cq:
        m.mark(tq, "close_quiet")
    # onto the ice: the pulse on the beat
    pulse(m, 0.0, T_STOP, BEAT, -21.0, 45, (0.8, 1.0), 6, "the hunt's pulse (s06)")
    strings_at(m, 0.0, AM, T_STOP + 0.25, -28.0 + MUSIC_LIFT, seed=16, attack=0.2, release=0.45, bright=2000.0)
    # the false trail: the lullaby's head low and slow in the cellos (E C D B C A), a faint E6 over it
    a = max(4.0, T_STOP + 0.3)
    head = [52, 48, 50, 47, 48, 45]
    step_ = 1.0
    last = max(0.6, T_SIDE_L[0] - (a + step_ * (len(head) - 1)) + 0.3)
    line_at(m, a, head, step_, -27.0 + MUSIC_LIFT, seed=17, label="the lullaby's head (cellos)", octaves=(0,),
            bright=1500.0, attack=0.45, release=1.0, last=last, glide=0.12)
    m.put("music", harms((THREAD,), T_SIDE_L[0] - a, 18, attack=1.5, release=1.0), a, -36.0 + MUSIC_LIFT, align=None,
          hall=-12.0)
    # along the trunk: a pedal A (cellos, basses), to the hush
    if T_HUSH > T_SIDE_L[0] + 0.5:
        strings_at(m, T_SIDE_L[0], (33, 45), T_HUSH - T_SIDE_L[0], -30.0 + MUSIC_LIFT, seed=19, attack=0.8,
                   release=0.35, bright=1200.0)
    # the lantern coming through the trees: the pulse again, slow
    fs = peek(m, "far_steps_hobnail")
    t_far = fs[0][0] if fs else 13.6
    pulse(m, t_far, L, 1.0, -22.0, 45, (0.6, 0.9), 7, "the hunt's pulse (the lantern coming)")


# ---------------------------------------------------------------------------- s07 THE HUNTER
@section("s07")
def s07(m, S):
    L = m.len
    T_HEART = m.span("T_HEART", (5.05, 7.0))
    T_STOP = m.at("T_STOP", 8.65, "he stops")
    T_DOWN = m.span("T_DOWN", (10.25, 10.55))
    T_CRACK = m.span("T_CRACK", (12.85, 13.6))
    rg = gg(take1(m, "river_under_ice"), -24.0)
    river_layer(m, 0.0, L, [(0.0, rg), (L, rg)], 7, "river_under_ice")
    wg = gg(take1(m, "wind_open"), -27.0)
    sw = take1(m, "silence_wind")
    sg, ts = gg(sw, -30.0), (sw["t"] if sw else T_STOP + 0.2)
    wind_layer(m, 0.0, L, [(0.0, wg), (3.0, wg), (ts - 0.5, wg - 1.0), (ts + 0.3, sg), (L, sg)], "open", 10,
               "wind at the woods' edge")
    if sw:
        m.mark(ts, "silence_wind")
    for k_, tt in enumerate((0.6, 2.2)):              # branches creak above
        fol(m, wood_creak(0.9, 3 + k_, 0.8), tt, wg + CUE_TRIM - 5.0, -0.5 + 0.9 * k_, None, lpf=2500.0, align=None)
    # his steps passing on the ice, a few metres away, left to right (at the cadence of the cued ones)
    sp = take1(m, "steps_passing")
    if sp:
        t0, d = sp["t"], sp.get("dur") or 2.0
        ice = sorted(c["t"] for c in m.cues if c["sfx"] == "step_guard_ice")
        before = [x for x in ice if x <= t0 + 1e-6]
        after = [x for x in ice if x >= t0 + d - 1e-6]
        gaps = np.diff(before[-6:]) if len(before) > 2 else np.array([0.379])
        per = float(np.median(gaps)) if len(gaps) else 0.379
        tt = before[-1] + per if before else t0
        end = (after[0] - 0.5 * per) if after else t0 + d
        k = 0
        while tt < end:
            u = (tt - t0) / max(d, 1e-6)
            step(m, "guard_ice", tt, cg(sp), float(np.clip(sp["pan"] + 0.8 * u, -1, 1)),
                 label="steps_passing" if k == 0 else None, seed=60 + k)
            tt += per
            k += 1
        m.mark(t0, "steps_passing")
        for j, tc in enumerate((t0 + 0.42, t0 + 1.33)):
            fol(m, lantern_creak(4 + j, 0.2, 0.35), tc, cg(sp) - 3.0, float(np.clip(sp["pan"] + 0.4 * (j + 1), -1, 1)),
                None, align=None)
    # her heartbeat (one beat per cue), the pulse dropping out for it
    hb = each(m, "heartbeat")
    for k, (t, d, c) in enumerate(hb):
        heartbeat(m, t, cg(c, -2.0), 0.24, k, label="heartbeat")     # (s07's trim lifts the scene; not its heart)
    t_h = hb[0][0] if hb else T_HEART[0]
    pulse(m, 0.0, t_h, E8, -21.0, 45, (0.7, 1.0), 8, "the hunt's pulse (s07, eighths)")
    strings_at(m, 0.0, AM_F, t_h, -28.0 + MUSIC_LIFT, seed=20, attack=0.3, release=0.08, bright=2400.0,
               shape=[(0.0, -6.0), (t_h, 2.0)])
    # the ice's harmonics: from his look down at the black ice, swelling to the ice's song
    sg_ = peek(m, "ice_sing")
    t_sing = sg_[0][0] if sg_ else T_CRACK[0]
    a = T_DOWN[0]
    if t_sing > a + 0.5:
        dd = t_sing - a + 0.9
        x = env_db(shimmer(round(dd, 3), 2, 88, 4), [(0.0, -12.0), (t_sing - a, 0.0), (dd, -12.0)])
        m.put("music", x, a, -28.0 + MUSIC_LIFT, label="ice harmonics (s07)", align=None, hall=-14.0)


# ---------------------------------------------------------------------------- s08 THE ICE
@section("s08")
def s08(m, S):
    L = m.len
    T_SIL = m.span("T_SILENCE", (0.5, 1.0))
    T_UNDER_HEAD = m.at("T_UNDER_HEAD", 1.8)
    T_UNDER = m.at("T_UNDER", 2.0)
    T_LOOK = m.at("T_LOOK", 5.0)
    T_BURST = m.at("T_BURST", 7.0, "bursts up")
    T_PAGE = m.at("T_PAGE", 11.0)
    # the world before the crack (the river, the wind): cut by the silence
    river_layer(m, 0.0, T_SIL[0], [(0.0, -24.0), (T_SIL[0], -24.0)], 8, None, xf=0.3)
    wind_layer(m, 0.0, T_SIL[0], [(0.0, -30.0), (T_SIL[0], -30.0)], "open", 16, None, xf=0.3)
    # the crack: huge, ringing, its pews running away under the sheet; then half a second of nothing
    for t, d, c in each(m, "ice_crack"):
        fol(m, ice_crack(1.0, 7, 1.5, 3, 0.4), t, cg(c) - 1.0, c["pan"], "ice_crack", kind="hall", wet=-14.0)
    take1(m, "silence")
    m.silences.append((round(m.t0 + T_SIL[0], 6), round(m.t0 + T_SIL[1], 6)))
    m.mark(T_SIL[0], "silence")
    # under the ice: the current's muffled roar; his heart, slow and huge; a murky drone
    ur = take1(m, "underwater_roar")
    t_u = min(ur["t"] if ur else T_UNDER, T_UNDER)
    a = max(T_SIL[1] + 0.05, T_UNDER_HEAD)
    d_u = T_BURST - a
    x = dsp.pad_to(underwater(round(d_u + 0.4, 3), 3), n_of(d_u + 0.4))
    x = env_db(lvl(x, bed=True), [(0.0, -18.0), (t_u - a, 0.0), (d_u - 0.06, 1.0), (d_u + 0.03, -60.0),
                                  (d_u + 0.4, -120.0)])
    m.put("amb", x, a, gg(ur, -10.0) + CUE_TRIM, label="underwater_roar", align=None)
    hs = take1(m, "heartbeat_slow")
    if hs:
        t, e = hs["t"], hs["t"] + (hs.get("dur") or 5.0)
        per = 1.2                                     # 50 bpm
        k = 0
        while t + k * per < e - 0.3:
            heartbeat(m, t + k * per, cg(hs), 0.3, k, label="heartbeat_slow" if k == 0 else None, low=4.0,
                      lpf=700.0, cut_at=e, hall=None)
            k += 1
    a = T_UNDER_HEAD + 0.1
    strings_at(m, a, (33, 40), T_BURST - a, -26.0 + MUSIC_LIFT, seed=22, attack=0.8, release=0.05, bright=700.0,
               lpf=380.0, shape=[(0.0, -8.0), (max(0.1, T_LOOK - a), 0.0), (T_BURST - a, 2.0)], hall=None)
    for t, d, c in each(m, "string_rise"):          # one note rising (E to A) as he sees the hole
        dd = max(d, 1.0)
        x = lvl(OF.bowed_line([(0.0, 6), (0.3, 6), (dd * 0.8, 11), (dd, 11)], dd, 0.8, 21, octaves=(0, -1),
                              attack=0.45, release=0.4, bright=1400.0))
        m.put("music", lp(x, 900.0), t, cg(c) + MUSIC_LIFT, label="string_rise", align=None, hall=None)
    # up through the hole: the strings surface with him (a tremolo, A minor with its F), a low A after
    tr = env_db(lvl(trem(AM_F, 2.6, 0.8, 3, 11.0)), [(0.0, 0.0), (0.4, -2.0), (2.6, -16.0)])
    m.put("music", tr, T_BURST, -25.0 + MUSIC_LIFT, label="the strings surface", hall=-16.0)
    if T_PAGE > T_BURST + 1.5:
        strings_at(m, T_BURST + 0.4, (33, 45, 52), T_PAGE - T_BURST - 0.4, -30.0 + MUSIC_LIFT, seed=23, attack=1.2,
                   release=1.0, bright=1400.0, shape=[(0.0, -4.0), (T_PAGE - T_BURST - 0.4, -8.0)])
    # the river and the night wind again
    river_layer(m, T_BURST, L, [(T_BURST, -27.0), (L, -26.0)], 9, None, xf=0.05)
    wl = take1(m, "wind_low")
    t_w, g_w = (wl["t"], wl["gain_db"]) if wl else (T_PAGE, -24.0)
    wind_layer(m, T_BURST, L, [(T_BURST, -32.0), (t_w, g_w - 2.0), (t_w + 0.8, g_w), (L, g_w)], "open", 17,
               "wind_low", xf=0.05)
    # her heart, waking: quickening into s09's (its next beat is s09's first)
    for t, d, c in each(m, "heartbeat"):
        e = t + (d or 1.6)
        n_ = max(1, int(round((e - t) / 0.8)))
        per = (e - t) / n_
        for k in range(n_):
            heartbeat(m, t + k * per, cg(c) - 2.0 * (n_ - 1 - k), 0.24, k, label="heartbeat" if k == 0 else None,
                      hall=None)


# ---------------------------------------------------------------------------- s09 THE CHOICE
@section("s09")
def s09(m, S):
    L = m.len
    bpm = g(S, "HEART_BPM", 96.0)
    t_stop = m.at("HEART_STOP", 13.45, "takes it")
    hc = take1(m, "heartbeat")
    t0 = hc["t"] if hc else 0.0
    per = 60.0 / max(bpm, 30.0)
    beats = []
    while t0 + len(beats) * per < t_stop - 1e-6:
        beats.append(t0 + len(beats) * per)
    # her heart, one array, stopped dead (no reverb tail) as she takes the scarf
    y = np.zeros(n_of(t_stop - t0))
    for j, tb in enumerate(beats):
        dsp.mix_into(y, np.asarray(_heart(0.24, j % 3)), n_of(tb - t0))
    m.put("music", dsp.fade(y, 0.0, 0.004), t0, gg(hc, -6.0) + CUE_TRIM - 3.0, label="heartbeat", hall=None,
          fades=False)
    m.hearts.extend(round(m.t0 + tb, 4) for tb in beats)
    # one high E, trembling, stopped with it
    sh = take1(m, "string_high")
    if sh:
        d = t_stop - sh["t"]
        x = OF.harmonic(hz(THREAD), d + 0.3, 1.0, 24, attack=1.2, release=0.2, vib=0.006)
        x = lvl(x * (0.72 + 0.28 * np.sin(TWO_PI * 5.5 * tax(len(x)))))
        m.put("music", cut_dead(x, d, 0.004), sh["t"], cg(sh) + MUSIC_LIFT, label="string_high", hall=None,
              fades=False)
    wg = gg(take1(m, "wind_low"), -22.0)
    wind_layer(m, 0.0, L, [(0.0, wg), (t_stop - 0.1, wg), (t_stop + 0.25, wg - 4.0), (L, wg - 3.0)], "open", 11,
               "wind over the river")
    river_layer(m, 0.0, L, [(0.0, -31.0), (L, -31.0)], 10, None)
    for t, d, c in each(m, "searchlight_hum"):
        hum_layer(m, t, t + d, [(t, c["gain_db"] - 6.0), (t + 0.8, c["gain_db"]), (t + d - 0.8, c["gain_db"]),
                                (t + d, c["gain_db"] - 8.0)], 9, "searchlight_hum", xf=0.5, pan=c["pan"])
    # where the heartbeat was: the lullaby's first note, alone
    for t, d, c in each(m, "music_box_note"):
        music_box(m, t, midi(LULLABY[0]), cg(c), "music_box_note", pan=c["pan"])


# ---------------------------------------------------------------------------- s10 THE SCARF
@section("s10")
def s10(m, S):
    L = m.len
    T_TIP = m.at("T_TIP", 5.0)
    T_REL2 = m.at("T_REL2", 8.0, "second throw")
    T_HEAVE = m.at("T_HEAVE", 9.72, "heaves")
    T_HOOK = m.at("T_HOOK", 10.38, "stub")
    T_SLIDE = m.span("T_SLIDE", (12.1, 13.5))
    T_ONTO = m.span("T_ONTO", (14.05, 14.8))
    T_BACK = m.span("T_BACK", (14.85, 15.4))
    T_ROLL = m.span("T_ROLL", (15.9, 16.45))
    wg = gg(take1(m, "wind_low"), -22.0)
    wind_layer(m, 0.0, L, [(0.0, wg), (L, wg)], "open", 12, "wind over the river")
    river_layer(m, 0.0, L, [(0.0, -31.0), (L, -31.0)], 11, None)
    # the pedal: A (basses, cellos) swelling toward the hook, the violas over it E, F, G#; all cut dead
    sl = take1(m, "string_low")
    t0 = sl["t"] if sl else 0.0
    gl = gg(sl, -20.0) + CUE_TRIM + MUSIC_LIFT
    d = T_HOOK - t0
    if d > 1.0:
        ped = env_db(lvl(held((33, 45), d + 0.2, 0.8, 25, (0,), 1.5, 0.05, None, 1500.0)), [(0.0, -12.0), (d, 0.0)])
        m.put("music", cut_dead(ped, d, 0.005), t0, gl, label="string_low (the pedal)", hall=None, fades=False)
    if T_HOOK > T_TIP + 1.0:
        e1, e2, e3 = T_REL2 - T_TIP, T_HEAVE - T_TIP, T_HOOK - T_TIP
        pts = [(0.0, 6), (max(0.1, e1 - 0.08), 6), (e1, 7), (max(e1 + 0.1, e2 - 0.08), 7), (e2, 10), (e3 + 0.2, 10)]
        va = env_db(lvl(OF.bowed_line(pts, e3 + 0.2, 0.8, 26, octaves=(0,), attack=1.2, release=0.05, bright=2200.0)),
                    [(0.0, -9.0), (e3, 0.0)])
        m.put("music", cut_dead(va, e3, 0.005), T_TIP, gl - 3.0, hall=None, fades=False)
    # the hook: one short low stab, then a silence
    for t, d_, c in each(m, "string_hit"):
        m.put("music", lvl(stacc((33, 45, 52, 57, 60), 0.35, 1.0, 27, (0, 12))), t, cg(c) + MUSIC_LIFT,
              label="string_hit", hall=-18.0)
    # the slide: the strings rise again (A minor, F, D minor, E) and release on an open A when he is out
    for t, d_, c in each(m, "string_rise"):
        prog = [(t, (45, 52, 57, 60)), (T_SLIDE[1], (41, 53, 57, 60)), (T_ONTO[0], (38, 50, 57, 62)),
                (T_BACK[0], (40, 52, 56, 59, 64)), (T_ROLL[0], (33, 45, 52, 57, 64))]
        prog = [p for i, p in enumerate(prog) if i == 0 or p[0] > prog[i - 1][0] + 0.2]
        for j, (ta, ch) in enumerate(prog):
            last = j == len(prog) - 1
            tb = ta + 1.6 if last else prog[j + 1][0]
            strings_at(m, ta, ch, tb - ta + (0.0 if last else 0.15), cg(c) + MUSIC_LIFT + 0.5 * j, seed=28 + j,
                       attack=1.0 if j == 0 else 0.35, release=1.6 if last else 0.45, bright=2400.0,
                       label="string_rise" if j == 0 else None,
                       shape=[(0.0, -8.0), (tb - ta, 0.0)] if j == 0 else None)
    # what now: one high held note, uneasy (B over the A)
    for t, d_, c in each(m, "string_high"):
        m.put("music", harms((83,), max(d_, 1.0), 29, attack=0.5, release=0.6, vib=0.004), t, cg(c) + MUSIC_LIFT,
              label="string_high", hall=-12.0)


# ---------------------------------------------------------------------------- s11 MERCY
@section("s11")
def s11(m, S):
    L = m.len
    T_RIVER = m.at("T_RIVER", 7.7)
    T_SNOW = m.at("T_SNOW", 16.3, "snowflakes")
    wg = gg(take1(m, "wind_low"), -22.0)
    wind_layer(m, 0.0, L, [(0.0, wg), (T_RIVER, wg), (T_RIVER + 1.0, wg - 2.0), (T_SNOW, wg - 2.0), (L, wg - 1.0)],
               "open", 13, "wind over the river")
    if L > T_SNOW + 0.2:
        hiss_layer(m, T_SNOW - 0.2, L, [(T_SNOW - 0.2, -60.0), (L, wg - 5.0)], 13, "the first snow")
    river_layer(m, 0.0, L, [(0.0, -32.0), (L, -32.0)], 12, None)
    for t, d, c in each(m, "searchlight_hum"):
        hum_layer(m, t, t + d, [(t, c["gain_db"] - 6.0), (t + 0.8, c["gain_db"]), (t + d - 0.8, c["gain_db"]),
                                (t + d, c["gain_db"] - 6.0)], 11, "searchlight_hum", xf=0.5, pan=c["pan"],
                  pan_end=0.3)
    # the low chords: A minor under the watch, no movement; under the lie, A minor with the F aching
    # in it, swelling, the F falling to E at the end
    for j, (t, d, c) in enumerate(each(m, "string_low")):
        dd = max(d, 1.5)
        if "sixth" in c["text"] or "aching" in c["text"] or "(f)" in c["text"]:
            strings_at(m, t, (45, 52, 60), dd, cg(c) + MUSIC_LIFT, seed=31, attack=1.2, release=1.6, bright=1700.0,
                       label="string_low (A minor, its F aching)", shape=[(0.0, -9.0), (dd, 0.0)])
            line_at(m, t, [65, 64], dd * 0.75, cg(c) + MUSIC_LIFT - 2.0, seed=32, octaves=(0,), bright=2000.0,
                    attack=1.2, release=1.6, last=dd * 0.25, glide=0.3)
        else:
            strings_at(m, t, AM, dd, cg(c) + MUSIC_LIFT, seed=30, attack=1.5, release=1.0, bright=1600.0,
                       label="string_low (A minor)", shape=[(0.0, -4.0), (dd * 0.5, 0.0), (dd, -2.0)])
    # the match cut: the lullaby's first note, far away
    for t, d, c in each(m, "music_box_note"):
        music_box(m, t, midi(LULLABY[0]), cg(c), "music_box_note", pan=c["pan"], far_=True, kind="hall", wet=-8.0)


# ---------------------------------------------------------------------------- s12 THE OTHER SIDE
@section("s12")
def s12(m, S):
    T_FARM = m.at("T_FARM", 4.0)
    T_SHUT = m.span("T_SHUT", (6.6, 6.95))
    T_WINDOW = m.at("T_WINDOW", 7.0)
    NOTES = m.ats("NOTES", (7.25, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0), "music box")
    names = g(S, "NOTE_NAMES", LULLABY_MAJOR)
    T_STRINGS = m.at("T_STRINGS", 9.5, "strings come in")
    T_PAGE = m.at("T_PAGE", 9.5)
    T_TITLE = m.at("T_TITLE", 12.5)
    T_BLACK = m.at("T_BLACK", 15.75, "black")
    # the wind: in the falling snow on the river; in the lee of the house; outside the window
    ws = each(m, "wind_low")
    g1 = ws[0][2]["gain_db"] if ws else -20.0
    g2 = ws[1][2]["gain_db"] if len(ws) > 1 else -24.0
    g3 = ws[2][2]["gain_db"] if len(ws) > 2 else -28.0
    wind_layer(m, 0.0, T_FARM + 0.3, [(0.0, g1), (T_FARM, g1)], "snow", 14, "wind in the falling snow")
    wind_layer(m, T_FARM, T_BLACK, [(T_FARM, g2), (T_SHUT[1], g2), (T_WINDOW, g3), (T_PAGE, g3), (T_TITLE, g3 - 5.0),
                                    (T_BLACK, g3 - 7.0)], "lee", 15, "wind in the lee of the house", xf=0.3)
    for t, d, c in each(m, "searchlight_hum"):
        dd = d if d else T_FARM - t
        hum_layer(m, t, t + dd, [(t, c["gain_db"]), (t + dd - 0.8, c["gain_db"]), (t + dd, c["gain_db"] - 10.0)], 12,
                  "searchlight_hum", xf=0.3, pan=c["pan"])
    # the music box: the whole tune, in A major (its notes and times read from the scene); the governor
    box = each(m, "music_box")
    nm_ = notes_of(list(names), LULLABY_MAJOR)
    for k, (t, d, c) in enumerate(box):
        i = _idx(c, k)
        music_box(m, t, nm_[i % len(nm_)], cg(c, BOX_TRIM), "music_box", pan=c["pan"],
                  name=str(names[i % len(names)]))
    if box:
        a, b = box[0][0] - 0.1, min(T_BLACK, box[-1][0] + 0.4)
        m.put("music", dsp.fade(box_whirr(round(b - a, 2), 2), 0.05, 0.2), a, cg(box[0][2], BOX_TRIM) - 18.0,
              align=None, hall=-26.0)
    # the strings under it: A, D, E, A (the last chord landing with the last note, held, stopped dead)
    sr = take1(m, "strings_resolve")
    if sr:
        gs = cg(sr) + MUSIC_LIFT - 3.0

        def nt(i, dflt):
            return NOTES[i] if len(NOTES) > i else dflt
        prog = [(T_STRINGS, (33, 45, 52, 57, 61, 64)), (nt(8, 11.0), (38, 50, 57, 62, 66, 69)),
                (nt(10, 12.0), (40, 52, 56, 59, 64, 68)), (nt(12, 13.0), (33, 45, 52, 57, 61, 64, 69))]
        prog = [p for i, p in enumerate(prog) if i == 0 or p[0] > prog[i - 1][0] + 0.2]
        for j, (ta, ch) in enumerate(prog):
            last = j == len(prog) - 1
            tb = T_BLACK if last else prog[j + 1][0]
            x = held(ch, tb - ta + (0.05 if last else 0.25), 0.8, 40 + j, (0,), 1.4 if j == 0 else 0.45,
                     0.02 if last else 0.6, None, 2600.0)
            x = lvl(x)
            if j == 0:
                x = env_db(x, [(0.0, -6.0), (tb - ta, 0.0)])
            if last:
                x = cut_dead(x, T_BLACK - ta, 0.01)
            m.put("music", x, ta, gs + 0.5 * j, label="strings_resolve" if j == 0 else None, align=None,
                  hall=-12.0, fades=not last)
    # the thread: s01's harmonic, soft, under the last chord; stopped at the black
    for t, d, c in each(m, "thread_ping"):
        x = cut_dead(thread_note(round(T_BLACK - t + 0.2, 3), 3, True), T_BLACK - t, 0.01)
        m.put("music", x, t, cg(c) + MUSIC_LIFT, label="thread_ping", hall=-14.0, fades=False)
    for t, d, c in each(m, "cut_to_silence"):
        m.mark(t, "cut_to_silence")


# ============================================================================ the bible's cues (a scene played as a stand-in)
def _bc(t, sfx_, gain=-12.0, dur=None, pan=0.0, dc="", note=None):
    c = {"t": float(t), "sfx": sfx_, "gain_db": float(gain), "pan": float(pan), "params": {}}
    if dur is not None:
        c["dur"] = float(dur)
    if dc:
        c["params"]["dc"] = dc
    if note is not None:
        c["params"]["note"] = int(note)
    return c


def _series(sfx_, t0, t1, every, gain, pan=0.0, dc="", pan1=None):
    out, k = [], 0
    while t0 + k * every < t1 - 1e-6:
        u = k * every / max(t1 - t0, 1e-6)
        out.append(_bc(round(t0 + k * every, 3), sfx_, gain, None, pan if pan1 is None else pan + (pan1 - pan) * u, dc))
        k += 1
    return out


def _rows(rows):
    return [_bc(*r) for r in rows]


BIBLE_CUES = {       # the bible's sound beats (scene times): what a scene played as a stand-in is spotted from
    "s01": _rows([(0.0, "wind_low", -24, 10.8, 0.0, "a low winter wind, snow hiss (it drops at 10.0)"),
                  (2.5, "ice_groan", -14, 1.5, 0.0, "a deep ice groan under the title"),
                  (4.0, "ice_crack", -4, None, 0.0, "the crack: a sharp split, then a dispersive pew"),
                  (4.05, "ice_pew", -10, 0.4), (4.25, "floe_grind", -20, 0.75),
                  (5.0, "thread_ping", -12, 2.5, 0.0, "a single high harmonic, held: the red thread"),
                  (5.5, "paper_flood", -20, 0.8), (7.0, "searchlight_hum", -30, 7.0, 0.0, "far"),
                  (10.0, "hush", -22, 4.0, 0.0, "the snow stops: a still, cold quiet"),
                  (11.0, "push_swell", -22, 3.0, 0.0, "a slow low string swell")])
    + [_bc(0.75 + 0.25 * i, "glass_tink", -16, None, (-0.38, -0.12, 0.12, 0.38)[i % 4], "a crisp glassy tink", i)
       for i in range(7)]
    + [_bc(t, "pluck", -15, None, 0.0, "a plucked string note, rising", i)
       for i, t in enumerate((6.5, 6.75, 7.0, 7.5, 8.0))],
    "s02": _rows([(0.0, "wind_low", -28, 18.0), (0.0, "searchlight_hum", -26, 18.0),
                  (0.0, "her_breath", -26, 3.3, 0.0, "the mother's quiet, frightened breathing"),
                  (0.0, "girl_breath", -30, 4.4), (2.0, "mitten_rustle", -24, 0.6),
                  (3.0, "moon_reveal", -20, 2.0), (3.3, "held_breath", -18), (4.3, "snow_thump", -16),
                  (4.7, "beam_pass", -18, 1.2), (6.1, "wire_creak", -16, 1.5), (6.35, "snow_crawl", -22, 1.35),
                  (7.7, "wire_creak", -22, 0.3, 0.0, "the wire let down gently"),
                  (8.0, "motor_clank", -12, None, 0.5), (9.0, "snap", -8), (10.75, "heartbeat", -10),
                  (11.375, "heartbeat", -10), (12.0, "snow_crawl", -20, 0.4, 0.0, "crawling under the wire"),
                  (12.4, "wire_snag", -14), (12.5, "wire_twang", -16), (12.62, "wire_twang", -15), (12.75, "rip", -6),
                  (12.78, "wire_twang", -12, 1.0, 0.0, "the wire springs back and quivers"),
                  (13.0, "wind_gust", -22, 1.0), (14.0, "run_steps", -14, 2.0),
                  (14.0, "her_breath", -24, 2.0, 0.0, "her running breath, receding"), (16.0, "page_tone", -22, 2.0)])
    + [_bc(t, "music_box", -10, None, 0.0, "a music box note", i) for i, t in enumerate((8.25, 8.5, 8.75))],
    "s03": _rows([(0.0, "stove_crackle", -18, 7.0), (0.0, "wind_outside", -24, 6.2), (0.6, "hands_rub", -22, 0.8),
                  (2.0, "cloth_rustle", -24, None, 0.0, "he draws the watch from his greatcoat"),
                  (2.5, "watch_click", -10), (2.5, "watch_tick", -20, 2.0), (2.7, "string_low", -20, 2.0),
                  (4.5, "watch_click", -12), (5.3, "lantern_creak", -20), (6.2, "door_open", -10),
                  (6.2, "wind_burst", -12, 0.8), (7.0, "boots_snow", -14, 1.7, 0.4, "hobnailed boots, every 0.55 s"),
                  (7.0, "lantern_squeak", -24, 1.7), (9.4, "cloth_tug", -16), (10.0, "lantern_hiss", -24, 2.0),
                  (11.45, "snow_kneel", -18), (12.0, "whistle", -4, None, 0.0, "one long shrill blast"),
                  (12.4, "whistle", -4, None, 0.0, "a second shrill blast"), (12.9, "searchlight_swing", -18, 1.5),
                  (13.0, "far_whistle", -22, None, -0.6), (13.25, "far_whistle", -24, None, 0.7),
                  (13.5, "far_whistle", -23, None, -0.3),
                  (14.0, "boots_snow", -16, 2.0, 0.0, "his boots jogging away into the woods, receding"),
                  (14.0, "wind_low", -26, 2.0, 0.0, "the wind in the pines")]),
    "s04": _rows([(0.0, "wind_pines", -24, 5.0), (0.0, "panting", -22, 3.5, -0.1),
                  (0.4, "searchlight_clank", -22, None, -0.6), (0.4, "searchlight_hum", -28, 2.6, -0.4),
                  (3.25, "girl_gasp", -20, None, -0.24), (3.5, "muffled_fall", -12, None, -0.24),
                  (3.55, "coat_swish", -24), (3.76, "girl_whimper_breath", -24, 1.2, -0.24),
                  (3.97, "step_mother_deep", -20, None, -0.24), (4.05, "haul_effort", -17), (4.5, "lift_swing", -18),
                  (4.9, "hitch", -22), (5.0, "wind_pines", -26, 3.0), (8.0, "wind_pines", -25, 6.0),
                  (8.0, "guard_breath", -24, 6.0, -0.2), (8.15, "lantern_creak", -24, None, -0.69),
                  (8.77, "lantern_creak", -24, None, -0.45), (9.39, "lantern_creak", -24, None, -0.21),
                  (9.6, "crouch", -20, None, -0.29), (9.9, "lantern_lowered", -24, None, -0.19),
                  (10.05, "guard_breath_stop", -22, None, -0.29), (11.0, "rise", -20, None, -0.29),
                  (11.3, "far_whistle", -26, None, -0.7), (11.5, "far_lantern_wake", -28, None, -0.6),
                  (12.0, "far_lantern_wake", -30, None, -0.45), (12.5, "far_lantern_wake", -32, None, -0.3),
                  (14.0, "river_under_ice", -22, 2.0, 0.4), (15.25, "stop_breath", -22, None, -0.1)])
    + _series("step_girl_deep", 0.083, 3.2, 0.44, -25, -0.34) + _series("step_mother_deep", 0.104, 3.3, 0.62, -20, -0.14)
    + _series("step_mother_heavy", 5.013, 7.0, 0.47, -24) + _series("step_guard_hobnail", 8.008, 9.7, 0.525, -17, -0.8,
                                                                     pan1=-0.29)
    + _series("step_guard_hobnail", 11.763, 14.0, 0.433, -14, -0.3) + _series("lantern_creak", 11.87, 14.0, 0.62, -24,
                                                                              -0.23)
    + _series("step_mother", 14.042, 15.4, 0.37, -20, -0.2),
    "s05": _rows([(0.0, "river_under_ice", -20, 14.0, 0.2), (0.0, "wind_open", -28, 10.0),
                  (0.2, "panting", -30, 3.0, -0.6, "tiny and far off on the bank"),
                  (1.2, "ice_groan", -24, 2.0, 0.5, "far downstream the river ice groans"),
                  (1.8, "hitch_far", -30, None, -0.65, "small and far off"), (3.1, "crouch_rustle", -22),
                  (3.55, "girl_slide_off", -22), (3.75, "girl_boots_land", -24), (3.95, "rise_breath", -24),
                  (4.35, "breath_slows", -28, 0.6), (5.0, "dig_stone", -20), (5.27, "throw_effort", -22),
                  (5.4, "stone_whoosh", -24, 0.6, 0.3), (6.0, "ice_crack_clean", -10, None, 0.18),
                  (6.04, "stone_plop", -14, None, 0.18), (6.1, "water_welling", -22, 0.8, 0.18),
                  (6.5, "water_lap", -26, 1.0), (7.45, "ice_boom", -14, 2.2), (7.5, "girl_flinch", -20),
                  (8.0, "searchlight_hum", -30, 2.0, -0.6), (8.4, "far_steps", -32, 1.6, 0.4),
                  (8.6, "searchlight_clank", -32, None, -0.6), (10.0, "guard_breath", -26, 1.0),
                  (10.15, "lantern_creak", -22), (10.3, "step_guard_hobnail", -18), (10.65, "lantern_creak", -22),
                  (10.94, "step_guard_hobnail", -18), (11.0, "lantern_creak_far", -30, None, -0.8),
                  (11.05, "girl_turn", -26), (11.25, "coat_turn", -24), (11.5, "breath_catch", -22),
                  (12.0, "held_silence", -34, 1.5), (13.55, "idea_breath", -20)]),
    "s06": _rows([(0.0, "river_under_ice", -22, 16.0), (0.0, "wind_open", -27, 4.0), (0.2, "panting_carry", -28, 3.4),
                  (3.6, "breath_stop", -24), (4.0, "close_quiet", -34, 2.0), (4.3, "boot_lift_snow", -26),
                  (5.55, "crunch_soft", -17), (6.2, "held_breath_carry", -32, 3.4), (9.71, "trunk_step_up", -20),
                  (9.93, "trunk_creak", -22), (10.046, "step_on_bark", -22),
                  (10.3, "trunk_creak", -26, None, 0.1, "a long thin creak"), (10.612, "step_on_bark", -22),
                  (11.28, "step_on_bark", -22), (11.58, "step_down_snow", -19), (11.85, "step_down_snow", -21),
                  (11.85, "reeds_rustle", -20, 0.6), (12.05, "crouch_rustle", -22), (12.3, "girl_slide_off", -23),
                  (12.45, "breath_held", -30, 0.6), (12.5, "coat_wrap", -22), (12.55, "girl_boots_land", -25),
                  (13.0, "wind_open", -28, 3.0), (13.6, "far_steps_hobnail", -30, 2.4, 0.1, "far off, coming nearer"),
                  (14.35, "lantern_creak_far", -30, None, 0.15), (15.2, "lantern_creak_far", -28, None, 0.15)])
    + [_bc(t, "step_mother_ice", -21) for t in (0.28, 0.73, 1.18, 1.63, 2.08, 2.53, 3.0, 3.55)]
    + [_bc(t, "step_backtrack", -23) for t in (6.95, 7.75, 8.55, 9.35)],
    "s07": _rows([(0.0, "river_under_ice", -24, 14.0), (0.0, "wind_open", -27, 3.0),
                  (0.0, "guard_breath_heavy", -20, 3.0, -0.2), (0.15, "lantern_creak", -18),
                  (1.0, "lantern_swing_down", -19), (1.35, "guard_sniff", -24), (2.0, "lantern_creak", -20),
                  (3.6, "lantern_creak", -22), (4.5, "lantern_creak", -23),
                  (5.0, "steps_passing", -24, 2.0, -0.4), (5.0, "reed_tick", -34, None, 0.3),
                  (8.65, "boots_stop", -20), (8.7, "lantern_creak", -20), (8.85, "silence_wind", -30, 2.6),
                  (9.0, "guard_breath", -24, 2.5, -0.35, "the guard's breath slowing"), (9.1, "lantern_raise", -19),
                  (9.6, "far_dog", -36, None, 0.6), (11.4, "step_bare_ice", -16), (11.6, "reeds_rustle", -20),
                  (11.72, "gasp_stifled", -18), (12.75, "ice_tick", -26), (12.85, "ice_sing", -12, 1.3)])
    + [_bc(t, "step_guard_hobnail", -15) for t in (0.017, 0.5, 0.9, 1.7, 2.275, 2.65)]
    + _series("step_guard_ice", 3.029, 5.0, 0.379, -20, 0.51)
    + [_bc(5.05 + 0.577 * k, "heartbeat", -8) for k in range(4)]
    + [_bc(t, "step_guard_ice", -21) for t in (7.192, 7.571, 7.95, 8.671)],
    "s08": _rows([(0.05, "boot_ice", -14), (0.25, "ice_crack", -1, None, 0.0, "a huge, ringing crack"),
                  (0.5, "silence", -60, 0.5), (1.08, "ice_break", -2), (1.3, "plunge", -3), (1.42, "splash", -8),
                  (2.0, "underwater_roar", -10, 5.0), (2.0, "heartbeat_slow", -8, 5.0), (2.0, "bubbles", -12, 0.6),
                  (2.55, "lantern_sink", -20, 2.0), (4.75, "clunk_under", -16), (5.05, "clunk_under", -18),
                  (5.1, "bubbles", -10, 0.5), (5.2, "string_rise", -16, 1.8), (5.5, "swim_strokes", -16, 1.5),
                  (7.0, "surface_burst", -4), (7.08, "gasp_man", -4), (7.45, "glove_ice", -12), (7.62, "ice_snap", -5),
                  (7.67, "splash", -6), (8.2, "surface_burst", -6), (8.3, "gasp_man", -5), (8.45, "glove_ice", -10),
                  (9.0, "panting_man", -8, 2.0), (9.0, "ice_scrape", -14, 2.0), (10.2, "ice_crack_small", -9),
                  (11.0, "water_lap", -18, 3.0), (11.0, "wind_low", -24, 3.0),
                  (11.4, "panting_man", -20, 2.6, 0.0, "his gasps, smaller, far off"), (12.4, "heartbeat", -12, 1.6)]),
    "s09": _rows([(0.0, "heartbeat", -6, 13.45, 0.0, "her heartbeat at 96 bpm; it stops dead"),
                  (0.0, "string_high", -20, 13.45), (0.0, "wind_low", -22, 14.0),
                  (1.3, "her_breath", -12, None, 0.0, "the breath she was holding, let out shaking"),
                  (2.0, "paper_slide", -20), (2.2, "searchlight_hum", -24, 3.8, -0.3),
                  (3.75, "panting_man", -16, 1.4, 0.2), (4.35, "glove_slip", -10), (4.37, "ice_scrape", -14),
                  (4.77, "glove_ice", -14), (6.12, "reeds_rustle", -12), (6.5, "mitten_grab", -16),
                  (7.1, "snow_step_mother", -12, None, -0.3), (7.58, "snow_step_mother", -12, None, -0.4),
                  (7.88, "cloth_stretch", -14), (7.9, "snow_scuff_girl", -14, None, 0.1),
                  (8.86, "glove_slip", -8, None, 0.3), (9.18, "splash_small", -8, None, 0.3),
                  (9.26, "gasp_man", -12, None, 0.3, "a choked gasp, further away"), (9.88, "scarf_unwind", -12, 0.98),
                  (13.45, "mitten_grab", -12), (13.5, "music_box_note", -14)]),
    "s10": _rows([(0.0, "wind_low", -22, 18.0), (0.0, "string_low", -20, 10.38), (0.1, "her_breath", -14),
                  (0.42, "cloth_rustle", -18), (0.9, "girl_breath", -18, None, 0.3), (1.3, "cloth_rustle", -16),
                  (1.96, "snow_step_mother", -12), (2.15, "wood_creak", -10, None, 0.0, "a long creak"),
                  (2.52, "cloth_scrape", -14), (2.82, "crawl_scrape", -14, 1.0), (3.3, "crawl_scrape", -14, 1.7),
                  (3.7, "panting_man", -14, 1.6, 0.15), (4.1, "ice_groan", -12), (5.0, "cloth_pull", -16, 0.22),
                  (5.22, "wool_wind", -16, 0.3), (5.7, "cloth_whoosh", -10), (6.39, "cloth_slap", -12, None, 0.2),
                  (6.42, "grunt", -10, None, 0.3, "his grunt as he lunges for it"), (6.74, "ice_crack_small", -8),
                  (6.79, "splash_small", -10), (6.84, "gasp_man", -12), (7.12, "cloth_slide", -16, 0.38),
                  (7.5, "wood_creak", -12), (7.9, "cloth_whoosh", -8, None, 0.0, "the second throw, harder"),
                  (8.48, "cloth_slap", -10), (8.86, "glove_grab", -8), (9.06, "cloth_stretch", -12),
                  (9.42, "wool_wind", -14, 0.26), (9.72, "grunt", -8, None, 0.2, "his grunt as he heaves"),
                  (9.74, "cloth_stretch", -10, None, 0.0, "the scarf snaps taut"), (9.77, "body_slide_wood", -10, 0.5),
                  (9.82, "gasp_b", -12), (10.38, "wood_knock", -4), (10.38, "string_hit", -10),
                  (10.4, "wood_creak", -8, None, 0.0, "a short sharp creak"),
                  (10.9, "cloth_pull", -12, 2.6, 0.0, "pulls every 0.45 s"), (11.1, "water_heave", -10),
                  (11.2, "her_breath", -12, 2.0, 0.0, "her breath straining"), (11.75, "ice_crack", -6),
                  (11.8, "splash_big", -8), (12.0, "grunt", -8, None, 0.0, "his grunt as he pushes on"),
                  (12.1, "ice_slide", -10, 1.4), (12.1, "string_rise", -16, 3.2), (13.62, "cloth_grab", -10),
                  (14.25, "wood_creak", -10), (14.35, "his_breath", -10, 1.2), (14.85, "crawl_scrape", -14, 0.55),
                  (15.5, "snow_step_mother", -12), (15.8, "body_fall", -10),
                  (16.2, "his_breath", -8, 2.2, 0.0, "his gasping on his back"), (16.3, "snow_step_mother", -12),
                  (16.95, "cloth_rustle", -14), (17.15, "string_high", -20, 1.8)]),
    "s11": _rows([(0.0, "wind_low", -22, 7.7), (0.0, "his_breath", -13, 3.0, 0.3, "ragged, shaking (slowed)"),
                  (0.1, "teeth_chatter", -21, 2.5, 0.3), (0.35, "snow_step", -16, None, -0.3),
                  (1.65, "cloth_rustle", -14, 1.0, 0.3, "a wet glove fumbling inside a greatcoat"),
                  (1.85, "her_breath", -12, None, -0.3, "her sharp intake of breath"),
                  (1.88, "snow_scuff", -16, None, -0.4), (3.0, "string_low", -22, 4.7, 0.0, "a low chord, A minor"),
                  (3.42, "watch_click", -10), (3.6, "water_trickle", -16, 1.2), (5.6, "music_box_note", -18),
                  (7.3, "watch_click", -8),
                  (7.7, "snow_steps_guards", -15, 5.7, -0.6, "several men, coming closer, then stopping, searching"),
                  (7.7, "lantern_creak", -20, 1.6, -0.6, "lanterns creaking"),
                  (7.8, "whistle", -8, None, -0.6, "two short blasts"), (8.0, "cloth_whip", -14, None, -0.2),
                  (8.1, "snow_scuff", -17, None, -0.2), (8.2, "whistle", -11, None, -0.75, "a little further"),
                  (8.62, "whistle", -13, None, -0.85, "a third, further"),
                  (9.3, "grunt_knight", -15, None, 0.2, "up on one knee"),
                  (9.85, "cloth_rustle", -18, None, 0.2, "his wet sleeve"), (9.95, "wool_slide", -16, None, -0.2),
                  (10.15, "snow_steps_girl", -17, 0.5), (10.65, "wool_slide", -15, None, 0.1),
                  (10.9, "wool_wind", -14, 0.65), (11.6, "snow_step", -14),
                  (12.45, "cloth_rustle", -18, None, 0.2, "his wet greatcoat"),
                  (12.55, "snow_steps_mother", -16, 0.85, -0.1), (12.8, "searchlight_hum", -22, 4.0, -0.4),
                  (12.85, "reeds_rustle", -17, 1.0, -0.2),
                  (13.4, "snow_steps_guards", -10, 1.4, 0.1, "the guards arrive at a run"),
                  (14.9, "searchlight_clank", -24, None, -0.2),
                  (15.4, "string_low", -18, 2.6, 0.0, "a low chord, A minor with the sixth (F) aching in it"),
                  (15.4, "water_drip", -22, 2.6), (16.3, "lantern_creak", -18, None, 0.2),
                  (16.3, "snow_shimmer", -20, 1.7), (16.6, "cloth_rustle", -20, None, 0.15, "a fur hat taken off")]),
    "s12": _rows([(0.0, "wind_low", -20, 4.0, 0.0, "in falling snow"), (0.0, "searchlight_hum", -26, 4.0, -0.6),
                  (0.4, "lantern_creak", -28, 2.5, -0.65, "the lanterns creak, small and far"),
                  (4.0, "wind_low", -24, 3.0, 0.0, "in the lee of the house"),
                  (4.1, "her_breath", -22, 1.8, -0.3, "her breath, tired"), (4.25, "door_latch", -14, None, 0.3),
                  (4.3, "door_creak", -16, 0.45, 0.3), (4.3, "room_tone_warm", -20, 2.65, 0.3),
                  (4.6, "cloth_rustle", -24, 1.35, 0.3, "the farm woman's shawl"), (5.967, "boot_wood", -20, None, 0.4),
                  (6.375, "boot_wood", -20, None, 0.55), (6.93, "door_shut", -12, None, 0.3),
                  (7.0, "wind_low", -28, 2.5, 0.0, "outside the window"), (7.1, "music_box_lid", -14),
                  (9.5, "strings_resolve", -16, 6.25), (9.5, "snow_hiss", -26, 3.0), (11.4, "paper_flood", -24, 0.95),
                  (12.5, "paper_settle", -24, 0.35), (12.62, "thread_ping", -18, 3.13), (13.7, "snow_settle", -30, 0.8),
                  (15.75, "cut_to_silence", -120)])
    + _series("snow_step_mother", 0.004, 3.6, 0.5, -26, -0.07, "far off", pan1=0.5)
    + [_bc(t, "snow_step_mother", -16) for t in (4.338, 4.742, 5.15, 5.558)]
    + [_bc(t, "music_box", -10, 1.0, 0.0, "the lullaby on the music box in A major", i)
       for i, t in enumerate((7.25, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0))],
}


def silence_from():
    """Film time the sound must be gone: s12's T_BLACK (scene time; the bible's 15.75)."""
    S = scene("s12") if "s12" in START else None
    tb = g(S, "T_BLACK", 15.75) if S is not None else 15.75
    return float(min(DUR, START.get("s12", DUR - 16.0) + float(np.clip(tb, 0.5, LENGTH.get("s12", 16.0)))))


# ============================================================================ spotting: a cue nothing answered
def realize(m, c):
    """Realise a cue no section and no foley handler answered, from its words, at its time. Returns
    how ('auto: ...'), or why nothing was added ('silence ...'), or why it could not be ('not realised:
    ...')."""
    s, t, tag = c["text"], float(c["t"]), c["sfx"]
    g0, pan = cg(c), c["pan"]
    d = float(c["dur"]) if c.get("dur") else None
    seed = int(round(t * 100)) % 997
    lab = "auto: " + tag

    def has(*w):
        return any(x in s for x in w)

    def as_(sfx_, **kw):
        c2 = dict(c, sfx=sfx_, **kw)
        FOLEY[sfx_](m, c2)

    if has("silence", "black", "stops dead", "every sound stops") or c["gain_db"] <= -90.0:
        m.mark(t, lab)
        return "silence (nothing to add)"
    if has("quiet", "hush", "still") and not has("breath", "step", "crunch") and c["gain_db"] <= -30.0:
        m.mark(t, lab)
        return "silence (the beds carry it)"
    if has("heartbeat", "heart"):
        heartbeat(m, t, g0, 0.24, seed, label=lab)
        return "auto: a heartbeat"
    if has("music box", "music-box", "lullaby"):
        k = _idx(c, 0)
        music_box(m, t, midi(LULLABY[k % len(LULLABY)]), g0, lab, pan=pan)
        return f"auto: a music-box note ({LULLABY[k % len(LULLABY)]})"
    if has("thread", "harmonic", "string high", "high string", "high held"):
        m.put("music", harms((THREAD,), max(d or 1.5, 0.5), seed, attack=0.4, release=0.6), t, g0 + MUSIC_LIFT,
              label=lab, align=None)
        return "auto: a high harmonic (E6)"
    if has("pluck"):
        m.put("music", lvl(pz(57 + 3 * (_idx(c, 0) % 5), 0.9, seed)), t, g0, pan=pan, label=lab)
        return "auto: a plucked note"
    if has("tink", "glass"):
        fol(m, glass_tink(81 + 2 * (_idx(c, 0) % 6), seed % 3), t, g0, pan, lab, bus="music")
        return "auto: a glass tink"
    if has("string", "chord", "swell", "pedal", "cello", "tone"):
        dd = max(d or 2.0, 0.6)
        strings_at(m, t, AM_F if has("aching", "sixth", " f)") else AM, dd, g0 + MUSIC_LIFT, seed=seed % 7, attack=0.6,
                   release=0.8, bright=2000.0, label=lab)
        return "auto: a held A minor chord"
    if has("wind"):
        dd = max(d or 2.0, 0.6)
        wind_layer(m, t, t + dd, [(t, c["gain_db"]), (t + dd, c["gain_db"])], "pines" if has("pine") else "open",
                   seed, lab)
        return "auto: wind"
    if has("river", "current", "under the ice"):
        dd = max(d or 2.0, 0.6)
        river_layer(m, t, t + dd, [(t, c["gain_db"]), (t + dd, c["gain_db"])], seed, lab)
        return "auto: the river under the ice"
    if has("hum", "motor", "searchlight"):
        if has("clank"):
            far_clank(m, t, g0, pan, lab, seed % 4)
            return "auto: the yoke's far clank"
        dd = max(d or 2.0, 0.6)
        hum_layer(m, t, t + dd, [(t, c["gain_db"]), (t + dd, c["gain_db"])], seed, lab, pan=pan)
        return "auto: the searchlight's motor"
    if has("hobnail", "guard's boot", "his boot", "boots"):
        step(m, "guard", t, g0, pan, lab)
        return "auto: a hobnailed step"
    if has("girl's", "small boot", "little boot"):
        step(m, "girl", t, g0, pan, lab)
        return "auto: the girl's step"
    if has("step", "boot", "crunch", "foot"):
        step(m, "mother", t, g0, pan, lab)
        return "auto: her step"
    if has("gasp"):
        as_("gasp_man" if has("his", "man") else "girl_gasp" if has("girl") else "gasp_b")
        return "auto: a gasp"
    if has("breath", "pant"):
        as_("guard_breath" if has("guard", "his") else "girl_breath" if has("girl") else "her_breath")
        return "auto: breath"
    if has("grunt", "effort"):
        grunt(m, t, g0, 0, pan, lab)
        return "auto: his grunt"
    if has("crack", "snap"):
        fol(m, ice_crumble(seed % 5, 0.6), t, g0, pan, lab)
        return "auto: an ice crack"
    if has("groan", "boom"):
        fol(m, ice_groan(max(d or 1.5, 0.6), seed % 5), t, g0, pan, lab, align=None)
        return "auto: an ice groan"
    if has("splash", "water", "drip"):
        fol(m, splash(0.4, seed % 5), t, g0, pan, lab)
        return "auto: a splash"
    if has("whistle"):
        fol(m, whistle(0.42, seed % 5), t, g0, pan, lab, kind="court", wet=-10.0)
        return "auto: a whistle"
    if has("creak"):
        fol(m, wood_creak(0.6, seed % 7), t, g0, pan, lab, align=None)
        return "auto: a creak"
    if has("click", "latch", "lid"):
        fol(m, watch_click(seed % 3), t, g0, pan, lab)
        return "auto: a click"
    if has("door"):
        fol(m, door_shut(seed % 3), t, g0, pan, lab)
        return "auto: a door"
    if has("paper", "page"):
        fol(m, paper_sound("slide", max(d or 0.5, 0.3), seed % 5), t, g0, pan, lab, room_=False, align=None)
        return "auto: paper"
    if has("rustle", "cloth", "coat", "wool", "scarf", "mitten", "glove", "sleeve"):
        fol(m, wool(round(max(d or 0.35, 0.2), 2), seed), t, g0, pan, lab, align=None)
        return "auto: a wool rustle"
    if has("snow", "hiss"):
        dd = max(d or 1.0, 0.5)
        hiss_layer(m, t, t + dd, [(t, c["gain_db"]), (t + dd, c["gain_db"])], seed, lab)
        return "auto: snow's hiss"
    if has("reed"):
        fol(m, reeds(0.6, seed % 5), t, g0, pan, lab, align=None)
        return "auto: reeds"
    return "not realised: no rule for its words"


# ============================================================================ the mix
def zero_windows(x, windows, fade=0.008):
    """Digital zeros through each (start, end) film-time window, a short fade into it (and out of it
    when it ends before the film does)."""
    k = max(2, n_of(fade))
    up = np.sin(0.5 * np.pi * np.linspace(0.0, 1.0, k)) ** 2
    n = len(x)
    for a, b in windows:
        i0, i1 = int(round(a * SR)), int(round(b * SR))
        if i0 >= n:
            continue
        j0 = max(0, i0 - k)
        if i0 > j0:
            w = up[::-1][k - (i0 - j0):]
            x[j0:i0] *= w[:, None] if x.ndim == 2 else w
        x[i0:min(i1, n)] = 0.0
        if i1 < n:
            l1 = min(k, n - i1)
            x[i1:i1 + l1] *= up[:l1, None] if x.ndim == 2 else up[:l1]
    return x


def mixdown(m, windows):
    """The buses to one mix: the music's plate (the hall bus), the music ducked a little under the
    breath; the designed silences (s08's half second, the end) zeroed in every stem; the stems kept
    (QA, --stems), float32."""
    def duck(x, depth):
        return dsp.sidechain_duck(x, m.key, depth_db=depth, thresh_db=-44.0, attack=0.03, release=0.35)
    music = duck(m.b.pop("music").astype(np.float64), -3.0)
    plate = dsp.reverb(m.b.pop("hall").astype(np.float64), "plate", wet_db=0.0, dry=0.0, seed=7)[:N]
    music += duck(dsp.pad_to(plate, N), -3.0)
    del plate
    music = zero_windows(music, windows)
    mix = music.copy()
    m.stems = {"music": music.astype(np.float32)}
    del music
    for k in ("amb", "efx", "vox", "feet"):
        x = zero_windows(m.b.pop(k).astype(np.float64), windows)
        mix += x
        m.stems[k] = x.astype(np.float32)
        del x
    m.key = None
    return mix


def master(mix, windows, target=-16.0, ceiling=-1.4):     # 0.1 dB under the -1.3 dBTP spec: meters differ
    """High-pass; the designed silences zeroed (a short fade into each); loudness to target; a
    true-peak limiter (iterated: it takes a little loudness back); the silences zeroed again."""
    mix = dsp.sos(np.asarray(mix, np.float64), "highpass", 30.0, 2)
    mix = zero_windows(mix, windows)
    gain = target - dsp.loudness_integrated(mix)
    out, gr = mix, np.ones(1)
    for _ in range(8):
        out, gr = dsp.limiter(mix * db2lin(gain), ceiling_db=ceiling, return_gain=True)
        for a, b in windows:
            out[int(round(a * SR)):min(len(out), int(round(b * SR)))] = 0.0
        lufs = dsp.loudness_integrated(out)
        if abs(lufs - target) < 0.02:
            break
        gain += target - lufs
    out = dsp.fade(out, 0.004, 0.0)
    for a, b in windows:
        out[int(round(a * SR)):min(len(out), int(round(b * SR)))] = 0.0
    master.gain = gain
    master.gr = float(dsp.lin2db(max(float(np.min(gr)), 1e-9)))
    if len(out) < N:
        out = np.concatenate([out, np.zeros((N - len(out), 2))])
    return out[:N]


# ============================================================================ QA
find_clicks, onsets = DC.find_clicks, DC.onsets
ST_FLOOR = -29.0             # the short-term floor (designed silences excepted)


def _ebur128(path):
    """ffmpeg's ebur128 meter on the file (a second opinion): integrated LUFS, true peak dBTP, LRA."""
    try:
        p = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null",
                            "-"], capture_output=True, text=True, timeout=600)
    except Exception as e:
        return dict(error=f"{type(e).__name__}: {e}")
    txt = p.stderr[p.stderr.rfind("Summary:"):] if "Summary:" in p.stderr else p.stderr[-2000:]
    out = {}
    for key, pat in (("I", r"I:\s+(-?[\d.]+|-inf) LUFS"), ("LRA", r"LRA:\s+(-?[\d.]+) LU"),
                     ("TP", r"Peak:\s+(-?[\d.]+|-inf) dBFS")):
        mm = re.search(pat, txt)
        if mm:
            out[key] = float(mm.group(1))
    return out


def qa(m, windows, outdir, path):
    import soundfile as sf
    os.makedirs(outdir, exist_ok=True)
    t_sil = windows[-1][0]
    info = sf.info(path)
    y, sr = sf.read(path, dtype="float64", always_2d=True)
    gm = db2lin(getattr(master, "gain", 0.0))
    R = {"file": dict(path=os.path.relpath(path, ROOT), sr=sr, channels=y.shape[1], subtype=info.subtype,
                      samples=len(y), seconds=len(y) / sr)}
    print("\n================ QA:", path)
    R["lufs"], R["tp"], R["peak"] = dsp.loudness_integrated(y), dsp.true_peak_db(y), dsp.sample_peak_db(y)
    print(f"  file: {sr} Hz, {y.shape[1]} ch, {info.subtype}, {len(y)} samples = {len(y) / sr:.4f} s (the film: "
          f"{DUR:.4f} s)")
    print(f"  integrated {R['lufs']:.2f} LUFS (-16)   true peak {R['tp']:.2f} dBTP (<= -1.3)   sample peak "
          f"{R['peak']:.2f} dBFS   master gain {master.gain:+.1f} dB, limiter at most {master.gr:.1f} dB")
    R["ffmpeg"] = _ebur128(path)
    print(f"  ffmpeg ebur128: {R['ffmpeg']}")
    # the designed silences: exact zeros
    R["silences_designed"] = []
    for a, b in windows:
        i0, i1 = int(round(a * SR)), min(len(y), int(round(b * SR)))
        ok = bool(np.all(y[i0:i1] == 0.0))
        R["silences_designed"].append(dict(start=a, end=b, zeros=ok))
        print(f"  digital silence {a:.3f}-{b:.3f} s: {'exact zeros' if ok else 'NOT ZERO'}")
    nz = np.nonzero(np.any(y != 0.0, axis=1))[0]
    R["last_sound"] = float((nz[-1] + 1) / SR) if len(nz) else 0.0
    print(f"  last non-zero sample at {R['last_sound']:.4f} s (zeros from {t_sil:.3f} s)")
    # short-term loudness (3 s) and its floor, the designed silences excepted
    ts, ls = dsp.loudness_curve(y, win=3.0, hop=0.1)

    def clear(tc):
        return all(tc + 1.5 <= a - 1e-6 or tc - 1.5 >= b + 1e-6 for a, b in windows)
    ok_ = np.array([clear(tc) for tc in ts])
    i_min = int(np.argmin(np.where(ok_, ls, 99.0)))
    low = []
    s_ = None
    for i, (tc, lv) in enumerate(zip(ts, ls)):
        bad = ok_[i] and lv < ST_FLOOR
        if bad and s_ is None:
            s_ = i
        if (not bad or i == len(ts) - 1) and s_ is not None:
            low.append((round(float(ts[s_]), 1), round(float(tc), 1), round(float(np.min(ls[s_:i + 1])), 1)))
            s_ = None
    R["short_term"] = dict(min=float(ls[i_min]), at=float(ts[i_min]), max=float(np.max(ls)), below_floor=low,
                           min_all=float(np.min(ls)), at_all=float(ts[int(np.argmin(ls))]))
    print(f"  short-term (3 s): min {ls[i_min]:.1f} LUFS at {ts[i_min]:.1f} s (window centre; designed silences "
          f"excepted), max {np.max(ls):.1f}; below {ST_FLOOR:.0f}: " + (", ".join(f"{a}-{b} ({v})" for a, b, v in low)
                                                                         or "nowhere"))
    keys = list(m.stems)
    print("  per scene:  LUFS  short-min  short-max  peak | per bus, LUFS at the master's gain: "
          + " ".join(f"{k:>5s}" for k in keys))
    R["scenes"] = {}
    for sid, s0, d in SCENES:
        i0, i1 = int(round(s0 * SR)), int(round((s0 + d) * SR))
        seg = y[i0:i1]
        lu = dsp.loudness_integrated(seg) if np.any(seg) else -99.0
        sel = (ts >= s0) & (ts < s0 + d)
        smin = float(np.min(np.where(ok_[sel], ls[sel], 99.0))) if np.any(sel) else -99.0
        smax = float(np.max(ls[sel])) if np.any(sel) else -99.0
        parts = []
        for k in keys:
            s2 = m.stems[k][i0:i1].astype(np.float64) * gm
            parts.append(dsp.loudness_integrated(s2) if np.any(s2) else -99.0)
        R["scenes"][sid] = dict(lufs=lu, short_min=smin, short_max=smax, peak=dsp.sample_peak_db(seg),
                                buses=dict(zip(keys, parts)), status=STATUS.get(sid))
        print(f"   {sid} {s0:5.0f}  {lu:6.1f}  {smin:7.1f}  {smax:7.1f}  {dsp.sample_peak_db(seg):6.1f} | "
              + " ".join(f"{p:5.0f}" for p in parts) + f"   {STATUS.get(sid, '?')}")
    print("  whole film, per bus (LUFS / peak dBFS at the master's gain): " + ", ".join(
        f"{k} {dsp.loudness_integrated(m.stems[k].astype(np.float64) * gm) if np.any(m.stems[k]) else -99:.1f}/"
        f"{dsp.sample_peak_db(m.stems[k].astype(np.float64) * gm):.1f}" for k in keys))
    # the heartbeats: their spacing (never the score's 120 bpm)
    hearts = sorted(m.hearts)
    R["hearts"] = {}
    for sid, s0, d in SCENES:
        hb = [h for h in hearts if s0 - 1e-6 <= h < s0 + d - 1e-6]
        if not hb:
            continue
        iv = np.diff(hb)
        R["hearts"][sid] = dict(n=len(hb), first=hb[0] - s0, last=hb[-1] - s0,
                                intervals=sorted({round(float(v), 3) for v in iv}))
        print(f"  heartbeats {sid}: {len(hb)} from {hb[0] - s0:.3f} to {hb[-1] - s0:.3f} s, intervals "
              f"{sorted({round(float(v), 3) for v in iv})}"
              + ("  (0.5 s = the score's 120 bpm)" if np.any(np.abs(iv - 0.5) < 1e-3) else ""))
    # the music box
    R["music_box"] = dict(n=len(m.box), notes=[(round(t, 3), n_) for t, n_ in m.box])
    print(f"  THE MUSIC BOX: {len(m.box)} notes (want 3 + 1 + 1 + 13 = 18): "
          + ", ".join(f"{t:.2f} {n_}" for t, n_ in m.box))
    # the loudest moments
    tw, lw = dsp.loudness_curve(y, win=1.0, hop=0.5)
    picked = []
    for i in [int(i) for i in np.argsort(-lw)]:
        if all(abs(tw[i] - tw[j]) > 2.0 for j in picked):
            picked.append(i)
        if len(picked) == 6:
            break
    print("  loudest 1 s windows: t  LUFS | the loudest placements there")
    for i in sorted(picked, key=lambda j: tw[j]):
        a_, b_ = tw[i] - 0.5, tw[i] + 0.5
        top = sorted((sp for sp in m.spans if sp[1] < b_ and sp[2] > a_), key=lambda sp: -sp[5])[:4]
        print(f"   {tw[i]:6.1f}  {lw[i]:5.1f} | " + "; ".join(f"{sp[0]}:{sp[3] or '-'}@{sp[4]}" for sp in top))
    # what drives the limiter
    pre = sum(m.stems[k].astype(np.float64) for k in keys) * gm
    pe = np.abs(pre).max(axis=1)
    del pre
    order, top_pk = np.argsort(-pe), []
    for i in order[:200000]:
        if all(abs(int(i) - j) > SR for j in top_pk):
            top_pk.append(int(i))
        if len(top_pk) == 8:
            break
    print("  biggest peaks into the limiter: t  dBFS | stems there (dBFS) | the loudest placements")
    R["peaks"] = []
    for i in sorted(top_pk):
        tt = i / SR
        st_ = sorted(((k, 20 * np.log10(np.abs(m.stems[k][i]).max() * gm + 1e-12)) for k in keys),
                     key=lambda kv: -kv[1])[:3]
        top = sorted((sp for sp in m.spans if sp[1] <= tt <= sp[2]), key=lambda sp: -sp[5])[:3]
        R["peaks"].append(dict(t=tt, db=float(20 * np.log10(pe[i] + 1e-12)), stems=st_))
        print(f"   {tt:8.3f} {20 * np.log10(pe[i] + 1e-12):+5.1f} | " + " ".join(f"{k} {v:+.1f}" for k, v in st_)
              + " | " + "; ".join(f"{sp[0]}:{sp[3] or '-'}@{sp[4]}" for sp in top))
    del pe, order
    # silences: 50 ms windows under -60 dBFS for more than half a second, before the black
    a = int(round(t_sil * SR))
    w = n_of(0.05)
    nb = a // w
    rms = 20 * np.log10(np.sqrt(np.mean(np.square(y[:nb * w]).reshape(nb, w, 2), axis=(1, 2))) + 1e-12)
    runs, s_ = [], None
    for k, q in enumerate(list(rms < -60.0) + [False]):
        if q and s_ is None:
            s_ = k
        elif not q and s_ is not None:
            if (k - s_) * 0.05 > 0.45:
                runs.append((round(s_ * 0.05, 2), round(k * 0.05, 2)))
            s_ = None
    R["silences"] = runs
    print(f"  silences under -60 dBFS longer than 0.45 s before {t_sil:.2f} s: "
          + (", ".join(f"{p:.2f}-{q:.2f}" for p, q in runs) or "none"))
    # clicks
    clicks = find_clicks(y, max_report=400)
    hits = np.array(sorted(m.starts))
    edges = [t for a_, b_ in windows for t in (a_, b_)]
    sus = [(t, sc) for t, sc in clicks if (not len(hits) or not np.any((t - hits > -0.003) & (t - hits < 0.08)))
           and not any(abs(t - e) < 0.012 for e in edges)]
    by = {}
    stem_clicks = {k: np.array([t for t, _ in find_clicks(m.stems[k].astype(np.float64) * gm, max_report=4000)])
                   for k in keys}
    for t, sc in sus:
        src_ = [k for k in keys if len(stem_clicks[k]) and np.min(np.abs(stem_clicks[k] - t)) < 0.003]
        by.setdefault("+".join(src_) or "the mix only", []).append((t, sc))
    R["clicks"] = {k: len(v) for k, v in by.items()}
    print(f"  click detector: {len(clicks)} transients, {len(sus)} not at the start of a placed sound or a designed "
          f"silence's edge; by stem: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(by.items(), key=lambda kv: -len(kv[1]))))
    for k, v in sorted(by.items()):
        print(f"    {k}: " + ", ".join(f"{t:.3f}({sc:.0f})" for t, sc in v[:14]))
    ends = [e for e in m.edges if e[4] > 0.1]
    R["cut_off"] = len(ends)
    print(f"  placements cut off loud at their end (no real fade): {len(ends)}"
          + "".join(f"\n    {sid} {t:8.3f} {bus:5s} end {e1:4.2f}  {lab}" for sid, t, lab, e0, e1, bus in ends[:14]))
    cuts = []
    for sid, s0, _ in SCENES[1:]:
        i0 = int(round(s0 * SR))
        ww = y[i0 - n_of(0.004): i0 + n_of(0.004)]
        cuts.append(f"{s0:.0f}:{float(np.max(np.abs(np.diff(ww, axis=0)))) if len(ww) > 1 else 0:.3f}")
    print("  largest sample step within 4 ms of each cut:", " ".join(cuts))
    # the cues
    n_sec = sum(1 for r in m.report if r[2] == "section")
    n_auto = sum(1 for r in m.report if r[2].startswith("auto"))
    n_sil = sum(1 for r in m.report if r[2].startswith("silence"))
    miss = [r for r in m.report if not (r[2] == "section" or r[2].startswith(("auto", "silence")))]
    per = {}
    for sid, c, how in m.report:
        p = per.setdefault(sid, dict(cues=0, sections=0, auto=0, nothing=0, missed=0))
        p["cues"] += 1
        key = ("sections" if how == "section" else "auto" if how.startswith("auto") else
               "nothing" if how.startswith("silence") else "missed")
        p[key] += 1
    R["cues"] = dict(total=len(m.report), sections=n_sec, auto=n_auto, silence=n_sil, missed=len(miss), per_scene=per,
                     not_realised=[dict(sid=sid, t=c["t"], cue=c["sfx"], why=how) for sid, c, how in miss],
                     auto_list=[dict(sid=sid, t=c["t"], cue=c["text"][:90], how=how) for sid, c, how in m.report
                                if how.startswith(("auto", "silence"))])
    print(f"  cues: {len(m.report)}: realised by the sections and their foley {n_sec}, auto-spotted from their words "
          f"{n_auto}, silence {n_sil}, NOT REALISED {len(miss)}")
    print("    per scene: " + "; ".join(f"{sid} {p['cues']} ({p['sections']}/{p['auto']}/{p['nothing']}/{p['missed']})"
                                       for sid, p in per.items()))
    for sid, c, how in m.report:
        if how.startswith(("auto", "silence")):
            print(f"    {how[:9]:9s} {sid} {c['t']:6.3f} {c['sfx']!r}: {how}")
    for sid, c, how in miss:
        print(f"    MISSED {sid} {c['t']:.3f} {c['sfx']!r}: {how}")
    R["approximations"] = [dict(sid=s_, t=t, cue=cue, how=txt) for s_, t, cue, txt in m.notes]
    for s_, t, cue, txt in m.notes:
        print(f"    approximated: {s_} {t:.3f} {cue}: {txt}")
    worst = 0.0
    for sid, c, how in m.report:
        if how != "section":
            continue
        mine = [e for e in m.ev if e["sid"] == sid]
        if mine:
            dd = min(abs(e["t"] - (START[sid] + c["t"])) for e in mine)
            if dd <= FRAME + 1e-6:
                worst = max(worst, dd)
    off_ = [(e["sid"], e["label"], e["meas"] - e["t"]) for e in m.ev if e["meas"] is not None]
    bad = [o for o in off_ if abs(o[2]) > FRAME]
    R["sync"] = dict(worst_cue_ms=1000 * worst, onsets=len(off_),
                     worst_onset_ms=1000 * max((abs(o[2]) for o in off_), default=0.0), beyond_frame=len(bad),
                     beyond=[dict(sid=s_, label=lab, ms=round(1000 * dd, 1)) for s_, lab, dd in bad[:40]])
    print(f"  sync: worst cue-to-event offset {worst * 1000:.1f} ms; measured onsets of {len(off_)} labelled hits: "
          f"worst {R['sync']['worst_onset_ms']:.1f} ms, {len(bad)} beyond a frame")
    for s_, lab, dd in bad[:30]:
        print(f"    {s_} {lab}: {dd * 1000:+.0f} ms")
    R["status"], R["warnings"] = dict(STATUS), list(WARN)
    R["from_bible"] = {k: sorted(set(v)) for k, v in FROM_BIBLE.items()}
    R["trims"] = dict(TRIM)
    with open(os.path.join(outdir, "qa.json"), "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    overview(y, m, outdir, windows, (ts, ls), R["scenes"])
    return R


def overview(y, m, outdir, windows, st, scenes=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import signal
    x = y.mean(axis=1)
    fig, ax = plt.subplots(5, 1, figsize=(26, 15), dpi=70, sharex=True,
                           gridspec_kw=dict(height_ratios=[1.0, 2.0, 1.2, 1.1, 0.5]))
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
    ts, ls = st
    ax[2].plot(tm, lm, color="#999", lw=0.6, label="momentary")
    ax[2].plot(ts, ls, color="#c60", lw=1.6, label="short-term")
    ax[2].axhline(-16, color="#060", lw=0.8, ls="--")
    ax[2].axhline(ST_FLOOR, color="#c00", lw=0.8, ls=":")
    # the per-scene loudness table: each scene's integrated level (a bar across it), its short-term range
    for sid, s0, d in SCENES:
        q = (scenes or {}).get(sid)
        if not q:
            continue
        ax[2].plot([s0 + 0.3, s0 + d - 0.3], [q["lufs"], q["lufs"]], color="#123", lw=2.2)
        ax[2].text(s0 + 0.4, -31.0, f"{sid}  {q['lufs']:.1f} LUFS\nshort {q['short_min']:.1f} .. {q['short_max']:.1f}"
                   f"\npeak {q['peak']:.1f} dBFS", fontsize=9, color="#123", va="top", family="monospace")
    ax[2].set_ylim(-50, -5)
    ax[2].set_ylabel("LUFS")
    ax[2].legend(loc="lower right", fontsize=9)
    gm = db2lin(getattr(master, "gain", 0.0))
    cols = dict(music="#1f5fa8", efx="#c0392b", amb="#7f8c8d", vox="#8e44ad", feet="#a0522d")
    for k_, s2 in m.stems.items():
        if not np.any(s2):
            continue
        tb, lb = dsp.loudness_curve(s2.astype(np.float64) * gm, win=1.0, hop=0.1)
        ax[3].plot(tb, lb, color=cols.get(k_, "#333"), lw=1.0, label=k_)
    ax[3].set_ylim(-60, -5)
    ax[3].set_ylabel("per bus (1 s)")
    ax[3].legend(loc="lower right", ncol=6, fontsize=9)
    for e in m.ev:
        ax[4].plot([e["t"], e["t"]], [0, 0.6], color="#c00" if e["bus"] == "music" else "#036", lw=0.4)
    for h in m.hearts:
        ax[4].plot([h, h], [0, 0.35], color="#000", lw=0.8)
    for tb_, _ in m.box:
        ax[4].plot([tb_, tb_], [0, 1], color="#f0a", lw=2.0)
    ax[4].set_yticks([])
    ax[4].set_ylabel("events")
    for a in ax:
        for sid, s0, d in SCENES:
            a.axvline(s0, color="#0a0", lw=1.0)
        for a0, b0 in windows:
            a.axvspan(a0, b0, color="#e00", alpha=0.12, lw=0)
        a.set_xlim(0, DUR)
    for sid, s0, d in SCENES:
        ax[0].text(s0 + 0.2, 0.82, sid + ("" if str(STATUS.get(sid, "")).startswith("module") else " (bible)"),
                   color="#070", fontsize=12)
    ax[4].set_xlabel("film time (s)")
    fig.tight_layout()
    p = os.path.join(outdir, "overview.png")
    fig.savefig(p)
    plt.close(fig)
    print("  overview:", p)


# ============================================================================ main
def play(m, sid, fn):
    """One section; if it fails with the scene's module it is played again from the bible; if it fails
    from the bible too, it is left out (and said so). Never raises."""
    import traceback
    S = scene(sid)
    if S is None:
        return
    for attempt in (0, 1):
        try:
            m.begin(S, sid, START[sid])
            fn(m, S)
            m.end()
            return
        except Exception as e:
            traceback.print_exc()
            m.abort()
            if isinstance(S, Stub) or attempt == 1:
                warn(f"{sid}: the section fails even from the bible ({type(e).__name__}: {e}): left out")
                STATUS[sid] = f"{STATUS.get(sid, '')}; SECTION FAILED".strip("; ")
                return
            warn(f"{sid}: the section fails with the module ({type(e).__name__}: {e}): played again from the bible")
            STATUS[sid] = f"stand-in (the section failed with the module: {type(e).__name__})"
            S = Stub(sid, "section failed")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--qa", metavar="DIR", help="measure the master: DIR/qa.json and DIR/overview.png")
    ap.add_argument("--only", help="comma list of sections (a quick listen: out/audio_only.wav, not the master)")
    ap.add_argument("--stems", metavar="DIR", help="also write the stems at the master's gain")
    ap.add_argument("--without", help="comma list of scenes to treat as missing (played from the bible)")
    ap.add_argument("--skip-missing", action="store_true", help="leave missing scenes silent (no stand-ins)")
    ap.add_argument("--stand-ins", action="store_true", help="play missing scenes from the bible (the default)")
    a = ap.parse_args(argv)
    ARGS.stand_ins = not a.skip_missing
    ARGS.only = set(a.only.split(",")) if a.only else None
    ARGS.qa = a.qa
    ARGS.without = set(a.without.split(",")) if a.without else set()
    w0, c0 = time.time(), time.process_time()
    for sid, s0, _ in SCENES:
        if abs(s0 / BAR - round(s0 / BAR)) > 1e-6:
            warn(f"{sid} starts at {s0} s, not on a bar line: its music is off the film's grid")
    m = Mix()
    for sid, fn in SECTIONS:
        if sid not in START or (ARGS.only and sid not in ARGS.only):
            continue
        ts = time.time()
        play(m, sid, fn)
        print(f"{sid}: {time.time() - ts:5.1f} s  [{STATUS.get(sid, '?')}]", flush=True)
    t_sil = silence_from()
    windows = sorted(set(m.silences)) + [(t_sil, DUR)]
    report, notes = list(m.report), list(m.notes)
    mix = mixdown(m, windows)
    import soundfile as sf
    out_dir = os.path.join(ROOT, "out")
    os.makedirs(out_dir, exist_ok=True)
    if ARGS.only:
        path = os.path.join(out_dir, "audio_only.wav")
        mix = dsp.sos(mix, "highpass", 30.0, 2)
        lu = dsp.loudness_integrated(mix)
        mix = dsp.limiter(mix * db2lin(-16.0 - lu if np.isfinite(lu) else 0.0), ceiling_db=-1.4)
        sf.write(path, mix[:N].astype(np.float32), SR, subtype="PCM_24")
        print(path)
        return
    out = master(mix, windows)
    del mix
    path = os.path.join(out_dir, "audio_master.wav")
    sf.write(path, out, SR, subtype="PCM_24")
    del out
    y, _ = sf.read(path, dtype="float64", always_2d=True)
    print(f"{path}: {len(y) / SR:.3f} s, {dsp.loudness_integrated(y):.2f} LUFS, TP {dsp.true_peak_db(y):.2f} dBTP; "
          f"{time.time() - w0:.0f} s wall, {time.process_time() - c0:.0f} s CPU")
    del y
    n_auto = sum(1 for r in report if r[2].startswith("auto"))
    miss = [r for r in report if not (r[2] == "section" or r[2].startswith(("auto", "silence")))]
    print(f"cues: {len(report)} ({len(report) - n_auto - len(miss)} by the sections and the foley, {n_auto} "
          f"auto-spotted, {len(miss)} not realised); {len(notes)} approximated")
    print("scenes: " + "; ".join(f"{sid} {STATUS.get(sid, '?')}" for sid, _, _ in SCENES))
    if WARN:
        print(f"{len(WARN)} warnings:")
        for w in WARN:
            print("  -", w)
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        gm = db2lin(master.gain)
        for k, s2 in m.stems.items():
            sf.write(os.path.join(a.stems, f"stem_{k}.wav"), (s2 * gm).astype(np.float32), SR, subtype="FLOAT")
        print("stems:", a.stems)
    if a.qa:
        qa(m, windows, a.qa, path)
    print(f"done: {time.time() - w0:.0f} s wall, {time.process_time() - c0:.0f} s CPU")


if __name__ == "__main__":
    main()
