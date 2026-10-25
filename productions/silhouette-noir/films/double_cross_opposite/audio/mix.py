"""DOUBLE CROSS, the OPPOSITE cut: the complete score and sound, locked to the scene modules.

    cd productions/silhouette-noir
    python3 films/double_cross_opposite/audio/mix.py                  # -> films/double_cross_opposite/out/audio_master.wav
    python3 films/double_cross_opposite/audio/mix.py --qa DIR         # ... and measure it (DIR/qa.json, DIR/overview.png)
    python3 films/double_cross_opposite/audio/mix.py --only s05,s07   # just these sections (a quick listen: out/audio_only.wav)
    python3 films/double_cross_opposite/audio/mix.py --stems DIR      # ... and the stems, at the master's gain
    python3 films/double_cross_opposite/audio/mix.py --without s06    # treat s06 as missing (it is played from the bible)
    python3 films/double_cross_opposite/audio/mix.py --skip-missing   # leave missing scenes silent instead

48 kHz stereo 24-bit PCM, exactly the timeline's 174 s, integrated -16 LUFS, true peak at most
-1.3 dBTP, and digital silence from s11's T_SILENCE (7.5 s: film 173.5) to the end.

Every beat a section uses is read from the scene's module on every run: its constant by name, else
its own cue whose words match (nearest the bible's time), else the bible's time. A missing module
(s07 until it lands), one that does not import, or one whose cues() gives nothing yet is played from
the bible (a stand-in: BIBLE_CUES). Every cue no section answered within a frame is realised from
its words (realize) and reported. Nothing is fetched and nothing is generated: the strings, harp,
bells and the one celesta are synthesised here with the OPPOSITE cuts' instruments
(films/opposite_full/audio/mix.py), the foley is DOUBLE CROSS's synths (films/double_cross/audio/
mix.py) and OPPOSITE's recordings (films/opposite/audio/gen: breaths, gasps, steps), and the only
voices are DOUBLE CROSS's own takes (the briefing's murmur, its syllables shuffled so it never says
a word; the Knight's grunts; her breath of a laugh). The police are cars: sirens, engines, brakes,
doors. Deterministic: the same scenes give the same file.

THE SCORE: Herrmann strings at 120 bpm (a beat 0.5 s, a bar 2 s; every scene starts on a bar line),
in D minor on the Psycho chord (D F A C#: minor with a major seventh). Two notes for two people: hers
is D, high (D6 bowed or as a harmonic, D5 plucked); his is C#, low (C#2), a semitone and octaves
under her. THE THEME (her plan; DOUBLE CROSS's tune, its eighths straight here), plucked:

    | D4 . A4 . . G4 F4 . | E4 F4 G4 . E4 . C4 . | D4 . C5 . . B4 A4 . | G4 E4 C#4 . D4 . . . |
      D minor (major 7)     B-flat (Lydian)         G                      A7         D minor

  in mirror inversion about D4 at the betrayal (low, dark: cellos and basses, an octave down):
    | D4 . G3 . . A3 B3 . | C4 B3 A3 . C4 . E4 . | D4 . E3 . . F3 G3 . | A3 C4 Eb4 . D4 . . . |
  the inversion inverted (upright again) from the dive into her eye; and in D MAJOR at the end:
    | D4 . A4 . . G4 F#4 . | E4 F#4 G4 . E4 . C#4 . | D4 . C#5 . . B4 A4 . | G4 E4 C#4 . D4 . . . |
      D                      E minor   A7              G major 7    D/A      A7         D major 7

  s01  OPPOSITE's title: three soft dot notes (D F A) with a dry tick each; a run of string stabs
       under the racing strips; a stab as each strip lands; a soft ostinato into the night; a low
       gong on D; a pizzicato descent down the Psycho chord; the moon's bell; D minor held under the
       cutaway, a click and a harp note up the chord per storey, a pulse a beat; a harp note down
       per light going out; the crew's 4: one high pizzicato D; a tremolo rising i-iv-V into the room.
  s02  the wall clock on every beat (s02 to s03's lamp, its level by shot); the cameos plucked:
       her D, the old man's A, the Knight's low C#; THE THEME on the harp from bar 10 (6.0), and
       again, pizzicato over the strings' harmony, under the murmur from 14.0 ...
  s03  ... landing on D as the red ring closes (5.0, the sting); his C# held, her D held; a braam
       under the golden arm; the mirror: her D6 against his C#2, the clock pressing in; the click,
       then silence.
  s04  sparse: the bank's clock strikes midnight (a deep bell on D); the shaft (a faint tremolo, a
       glide down to his C#); from the hall (60.0) the beat's tick ...
  s05  ... under the guard's sweep; a tiptoe pizzicato per crossing (her D, his C#, the old man's A);
       his heart on the picture's rings; one low tremolo under the cat's eyes; a swell on the push.
  s06  the dial: a pizzicato answer on each gate (D, F, A), the chord on the fence; the tick stops
       as the door swings (91.0); a string swell in D minor rising onto the gold; the looks plucked.
  s07  the gold (B-flat major); the ruby: a held low D, a harmonic rising as she lifts it, a glassy
       string shimmer on its flare (no celesta); his look: his C# as a cello pedal under THE
       INVERSION (6.0), its last D held into the BOOM on the bar line (14.0); the red dial; the
       squeak and a low stab on the ring; an ostinato under his run; BANG, and the bell, loud,
       swelling on every beat.
  s08  black, breath, the match; his heart on its rings; the Dutch-tilt string; three BOOMs; the far
       bell; her laugh; from the dive (8.0) THE THEME upright, plucked, through the night before ...
  s09  ... landing on D (s09 1.0); the race under the street (7.0): an ostinato on the Psycho chord,
       her D6 against his C#2; a plucked theme note per waking window (D A G F); down to the pedals
       for the near miss; back as the engine catches, the theme's head on the violins; a siren far.
  s10  the sirens braiding (tuned D-A) over a Psycho tremolo; his heart; the web: the theme's next
       notes plucked, a look each (E F G E C D); a low swell, the squeak and a stab on the ring; E,
       D, C#: his low notes going down; her D6, his C#2, then the two struck together in a chime;
       from 17.0 THE THEME in D MAJOR, violins and harp ...
  s11  ... the ONE celesta note of the film on the ruby's glint (1.5: film 167.5); D/A swelling as
       the windows fly up, a rising harp run; A7 under the stamp and the strips; on the theme's last
       D (4.0) the last chord, D major with the major seventh; the dot; two heartbeats; silence.
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
from functools import lru_cache

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np  # noqa: E402

from audio import dsp, sfx  # noqa: E402
from audio.dsp import SR, db2lin, n_of  # noqa: E402
from engine.timing import SceneTiming  # noqa: E402
import films.double_cross.audio.mix as DC  # noqa: E402   (its foley synths and voice takes; import is side-effect free)
import films.opposite_full.audio.mix as OF  # noqa: E402  (the OPPOSITE cuts' strings, harp, bells, celesta)
from films.opposite.audio.mix import mono  # noqa: E402

FILM = "double_cross_opposite"
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

# scene trims (dB, every bus but the clocks): the film's arc, set by meter (see --qa's per-scene table)
TRIM = dict(s01=0.0, s02=0.0, s03=-3.0, s04=1.0, s05=0.0, s06=0.0, s07=0.0, s08=0.0, s09=-1.5, s10=-1.5, s11=-1.5)
CUE_TRIM = -2.0              # a cue's gain_db, as the scenes write it, to this mix's levels

ARGS = argparse.Namespace(stand_ins=True, only=None, qa=None, without=set())
WARN = []
STATUS = {}                  # sid -> how the scene was played (module / stand-in and why)


def warn(msg):
    WARN.append(msg)
    print("WARNING:", msg, flush=True)


# ============================================================================ music theory
hz, midi, nm = DC.hz, DC.midi, DC.nm
HER, HER_P, HIS, MID = 86, 74, 37, 57        # her D6 (bowed, a harmonic) and D5 (plucked); his C#2; the old man's A3
PSY = (50, 53, 57, 61)                       # D3 F3 A3 C#4: the Psycho chord in D
THEME, INVERSION, THEME_MAJOR = DC.THEME, DC.INVERSION, DC.THEME_MAJOR
UPRIGHT = DC.inverted(INVERSION)             # the inversion inverted: upright again (the theme itself)

# the harmony, in the strings' voicing: (beats, (midi, ...)); the lowest note the basses'
PROG = ((4, (38, 50, 53, 57, 61)),           # D minor with the major seventh
        (4, (34, 50, 53, 58)),               # B-flat (the tune's E: Lydian)
        (4, (31, 50, 55, 59)),               # G (Dorian's B)
        (2, (33, 52, 55, 61)),               # A7
        (2, (38, 50, 53, 57)))               # D minor
PROG_INV = ((4, (38, 45)), (4, (33, 40)), (4, (31, 38)), (2, (33, 39)), (2, (38, 45)))   # low: D, A, G, A half-dim, D
INV_TREM = ((4, 53), (4, 48), (4, 46), (2, 48), (2, 53))                                 # violas: the thirds, trembling
PROG_MAJ = ((4, (38, 50, 54, 57)),           # D
            (2, (40, 52, 55, 59)),           # E minor
            (2, (33, 52, 55, 61)),           # A7
            (3, (31, 50, 54, 59)),           # G major 7 (the tune's C#: Lydian)
            (1.5, (33, 50, 54, 57)),         # D/A: the swell
            (1.5, (33, 52, 55, 61)),         # A7
            (2, (38, 50, 54, 57, 61)))       # D major with the major seventh: the last chord


def notes_in(notes, start=0.0, stop=None):
    return [(b, d, p) for b, d, p in notes if b >= start - 1e-9 and (stop is None or b < stop - 1e-9)]


def chords_in(prog, start=0.0, stop=None):
    """[(beat, beats, notes)] of a progression, clipped to [start, stop) beats."""
    out, b = [], 0.0
    for nb, ch in prog:
        a, e = max(b, start), min(b + nb, 16.0 if stop is None else stop)
        if e > a + 1e-9:
            out.append((a, e - a, ch))
        b += nb
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
    """The cues as the mix reads them; each gets its words ('text': the sfx, a tag's underscores as
    spaces, and its params' dc/desc) and who it is about ('who')."""
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
BUSES = ("music", "hall", "efx", "amb", "vox", "feet", "tick")
BUS_TRIM = dict(feet=1.0)
HALL_SEND = -14.0            # the music's send to the plate


class Mix:
    """The film's buses. put() takes scene time; placements are staged and committed when the
    section ends (a section that fails part-way is dropped and played again from the bible).
    Every labelled placement is logged as an event (the beat it is for, and where its sound
    actually starts) for the sync check and for spotting: a cue counts as realised when an event
    of its scene lands within a frame of it."""

    def __init__(self):
        self.b = {k: np.zeros((N, 2), np.float32) for k in BUSES}
        self.key = np.zeros(N, np.float32)          # breath and voices duck the music a little
        self.ev, self.edges, self.starts, self.spans, self.report = [], [], [], [], []
        self.ticks, self.celesta = [], []           # film times of every clock tick; of the celesta's note
        self.src = {}
        self.sid, self.t0, self.trim, self.cues, self.covered, self.claimed = None, 0.0, 0.0, [], set(), set()
        self.stage, self.S, self.len = [], None, 10.0

    def begin(self, S, sid, t0):
        self.S, self.sid, self.t0, self.trim = S, sid, t0, TRIM.get(sid, 0.0)
        self.cues = cue_list(S, sid)
        self.covered, self.claimed = set(), set()
        self.len = LENGTH.get(sid, 10.0)
        self.stage = []
        self.n_ev = len(self.ev)
        self.n_misc = (len(self.edges), len(self.starts), len(self.spans), len(self.ticks), len(self.report),
                       len(self.celesta))

    def abort(self):
        self.stage = []
        if not hasattr(self, "n_ev"):
            return
        del self.ev[self.n_ev:]
        e, s, sp, tk, rp, ce = self.n_misc
        del self.edges[e:], self.starts[s:], self.spans[sp:], self.ticks[tk:], self.report[rp:], self.celesta[ce:]

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
        """Several beats: the module's sequence `name`; else every cue with any of `words` around the
        bible's times (for a module, anywhere in the scene after that); else the bible's."""
        S = self.S
        defaults = tuple(float(x) for x in defaults)
        if self._module() and name:
            v = getattr(S, name, None)
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
            if words and not any(w in c["text"] for w in words):
                continue
            d = abs(c["t"] - t)
            if d <= win and (best is None or d < best[0]):
                best = (d, c)
        return None if best is None else best[1]

    def music_at(self, t, pad=0.25):
        tf = self.t0 + t
        return any(bus == "music" and a - pad <= tf <= b for bus, a, b, *_ in self.spans[self.n_misc[2]:])

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
        trim = 0.0 if bus == "tick" else self.trim
        x = (x * db2lin(gain + trim + BUS_TRIM.get(bus, 0.0))).astype(np.float32)
        if hall == "auto":
            hall = HALL_SEND if bus == "music" else None
        self.stage.append((bus, i, x, None if hall is None else db2lin(hall), bool(key)))
        self.starts.append(self.t0 + at)
        self.spans.append((bus, self.t0 + at, self.t0 + at + len(x) / SR, label or "", sys._getframe(1).f_lineno,
                           float(np.sqrt(np.mean(np.square(x[: n_of(1.0)], dtype=np.float64))))))
        if bus == "tick":
            self.ticks.append(self.t0 + at)
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

    def cover(self, *words):
        for i, c in enumerate(self.cues):
            if any(w in c["text"] for w in words):
                self.covered.add(i)

    def cover_span(self, a, b, *words):
        for i, c in enumerate(self.cues):
            if a - FRAME <= c["t"] <= b + FRAME and any(w in c["text"] for w in words):
                self.covered.add(i)

    def end(self):
        """Spotting: realise every cue of this scene no event answered; commit the section."""
        if FROM_BIBLE.get(self.sid):
            warn(f"{self.sid}: not in the module yet, taken from the bible: "
                 f"{', '.join(dict.fromkeys(FROM_BIBLE[self.sid]))}")
        mine = [e["t"] - self.t0 for e in self.ev if e["sid"] == self.sid]
        for i, c in enumerate(self.cues):
            if i in self.covered or any(abs(t - c["t"]) <= FRAME + 1e-6 for t in mine):
                self.report.append((self.sid, c, "section"))
                continue
            how = realize(self, c)
            self.report.append((self.sid, c, how))
            if how.startswith("auto"):
                print(f"  {self.sid} {c['t']:6.3f}  auto: {c['text'][:70]!r} -> {how[6:]}")
            elif not how.startswith("silence"):
                warn(f"{self.sid} {c['t']:.3f}: cue {c['text']!r} not realised ({how})")
        self.commit()


# ============================================================================ helpers
norm, tax, cut, onset_at, pitch = OF.norm, OF.tax, OF.cut, OF.onset_at, OF.pitch
fx = OF.fx
STEP_PRE = DC.STEP_PRE


def rng(*keys):
    return dsp.rng_for("double-cross-opposite", *keys)


ROOMS = {        # scene -> [(from scene time, reverb, wet dB)]: where its foley sounds
    "s01": [(0.0, "small_room", -24.0), (5.5, "street", -16.0), (11.5, "small_room", -20.0)],
    "s02": [(0.0, "small_room", -18.0)],
    "s03": [(0.0, "small_room", -20.0)],
    "s04": [(0.0, "street", -14.0), (5.0, "cell", -7.0), (7.0, "cell", -10.0), (11.3, "court", -12.0)],
    "s05": [(0.0, "court", -12.0)],
    "s06": [(0.0, "hall", -15.0)],
    "s07": [(0.0, "cell", -12.0), (11.5, "hall", -12.0), (14.0, "small_room", -20.0), (15.0, "hall", -14.0),
            (17.0, "street", -12.0)],
    "s08": [(0.0, "cell", -10.0), (8.5, "cell", -7.0), (12.0, "cell", -10.0)],
    "s09": [(0.0, "cell", -10.0), (3.0, "cell", -8.0)],
    "s10": [(0.0, "street", -12.0), (3.0, "car", -14.0), (5.0, "street", -12.0), (13.0, "street", -15.0)],
    "s11": [(0.0, "street", -16.0), (2.6, "small_room", -24.0)],
}


def room(m, t):
    kind, wet = "small_room", -20.0
    for t0, k, w in ROOMS.get(m.sid, ()):
        if t >= t0 - 1e-6:
            kind, wet = k, w
    return kind, wet


def roomed(m, x, t, seed=0, wet=None, kind=None):
    """x in the room of this scene at scene time t (or in `kind`)."""
    k, w = room(m, t)
    return dsp.reverb(x if np.ndim(x) == 2 else dsp.fade(mono(x), 0.0005, 0.003, shape="lin"), kind or k,
                      wet_db=w if wet is None else wet, seed=seed % 5)


def head(c):
    """A cue's lead words: its tag (underscores as spaces), or its text up to the first colon."""
    return c["sfx"].replace("_", " ").split(":")[0].strip().lower()


def cues_with(m, *words):
    """This scene's cues with any of words: [(t, dur, cue)], in time order."""
    return [(c["t"], float(c.get("dur") or 0.0), c) for c in m.cues if any(w in c["text"] for w in words)]


def cgain(m, t, *words, default=-14.0, win=0.12):
    c = m.cue_near(t, *words, win=win)
    return default if c is None else c["gain_db"] + CUE_TRIM


def cpan(m, t, *words, default=0.0, win=0.12):
    c = m.cue_near(t, *words, win=win)
    return default if c is None else c["pan"]


def bed(name, dur, seed=0, lp=None, fin=0.3, fout=0.4, **p):
    """A catalog bed (room tone, the city, wind, an engine idling) with real fades."""
    x = fx(name, dur=round(max(0.3, dur), 2), seed=seed, **p)
    if lp:
        x = dsp.sos(x, "lowpass", lp, 2)
    return dsp.fade(x, min(fin, dur / 3), min(fout, dur / 3))


def env(x, pts):
    """x shaped by a breakpoint envelope [(s, gain)]."""
    x = np.asarray(x, np.float64)
    e = dsp.env_bp(pts, len(x))
    return x * (e[:, None] if x.ndim == 2 else e)


def beat_pulse(n, t0, depth=0.3, every=BEAT):
    """A swell on every beat (scene time t0 at sample 0): the bell's red ripples."""
    ph = ((tax(n) + t0) % every) / every
    return (1.0 - depth) + depth * np.exp(-ph / 0.22)


# ============================================================================ the strings (OPPOSITE's), in midi
def pz(p, vel=0.8, seed=0):
    return OF.pizz(hz(p), vel, seed)


def hp(p, vel=0.8, seed=0):
    return OF.harp(hz(p), vel, seed)


def harm(p, dur, vel=0.7, seed=0, **kw):
    return OF.harmonic(hz(p), dur, vel, seed, **kw)


def bow(pts, dur, vel=0.7, seed=0, **kw):
    """A bowed section line through [(s, midi)] (glides between points)."""
    return OF.bowed_line([(t, p - 46) for t, p in pts], dur, vel, seed, **kw)


def held(notes, dur, vel=0.7, seed=0, octaves=(0,), attack=0.2, release=0.6, env_=None, bright=4500.0):
    return OF.strings([p - 46 for p in notes], dur, vel, seed, octaves=octaves, attack=attack, release=release,
                      env=env_, bright=bright)


def stacc(notes, dur, vel=0.8, seed=0, spread=(0, 12)):
    return OF.chord([p - 46 for p in notes], dur, vel, seed, 0, True, spread)


def trem(notes, dur, vel=0.6, seed=0, rate=13.0):
    return OF.tremolo([p - 46 for p in notes], dur, vel, seed, octave=0, rate=rate)


def stab(notes=PSY, seed=0, low=False):
    """A string stab, hard, with its hall (low: an octave down, and the octave under that)."""
    sh = -12 if low else 0
    return OF.rev(OF.chord([p - 46 + sh for p in notes], 0.45, 1.0, 40 + seed, 0, spread=(0, 12, -12)), -8.0, seed)


@lru_cache(maxsize=None)
def shimmer(dur=0.8, seed=0, top=93):
    """A glassy string shimmer: harmonics high over each other, each trembling at its own rate
    (strings, not a celesta: the celesta is the ruby's alone)."""
    r = rng("shimmer", seed, round(dur, 3), top)
    out = None
    for k, p in enumerate((top, top + 5, top + 7, top - 5)):
        x = OF.harmonic(hz(p), dur, 1.0, seed + 7 * k, attack=0.05 + 0.04 * k, release=0.5, vib=0.004)
        t = tax(len(x))
        x = x * (0.55 + 0.45 * np.sin(2 * np.pi * r.uniform(6.0, 11.0) * t + r.uniform(0, 6.3)) ** 2) * 0.75 ** k
        out = x if out is None else out[:len(x)] + x[:len(out)]
    return norm(dsp.sos(out, "highpass", 900.0, 2))


def ostinato(m, t0, t1, notes=PSY, step=E8, vel=(0.4, 0.9), accent=(0, 3), gain=-14.0, seed=0, spread=(0, 12),
             pan=0.0, gate=0.6, label=None):
    """Herrmann's ostinato: staccato chords from t0 to t1 (scene time), crescendo vel[0] -> vel[1],
    accents on the given steps of the film's bar; notes may be a function of t (None: a rest)."""
    per_bar = int(round(BAR / step))
    i, t = 0, t0
    while t < t1 - 1e-6:
        u = (t - t0) / max(t1 - t0, 1e-6)
        v = vel[0] + (vel[1] - vel[0]) * u
        if int(round((m.t0 + t) / step)) % per_bar in accent:
            v *= 1.3
        ch = notes(t) if callable(notes) else notes
        if ch:
            m.put("music", stacc(ch, step * gate, 1.0, seed + i % 4, spread) * min(v, 1.2), t, gain, pan=pan,
                  label=label if i == 0 else None)
        t += step
        i += 1


def pluck_line(m, t0, notes, inst="harp", gain=-12.0, pan=0.0, vel=0.8, octave=0, seed=0, label=None, start=0.0,
               stop=None, skip=(), t_min=-1e9, t_max=1e9):
    """The tune plucked (harp or pizzicato), its beat 0 at scene time t0; beats [start, stop)."""
    k = 0
    for j, (b, d, p) in enumerate(notes_in(notes, start, stop)):
        t = t0 + b * BEAT
        if b in skip or not t_min - 1e-9 <= t < t_max:
            continue
        acc = 1.0 if b % 4 == 0 else 0.88
        x = (hp if inst == "harp" else pz)(p + 12 * octave, vel * acc, seed + j)
        m.put("music", x, t, gain, pan=pan, label=label if k == 0 else None)
        k += 1


def bowed_tune(m, t0, notes, gain=-12.0, pan=0.0, vel=0.8, octave=0, seed=0, label=None, start=0.0, stop=None,
               octaves=(0,), bright=5500.0, attack=0.08, release=0.6, hold=None, shape=None):
    """The tune bowed legato (one bow line, a 30 ms slide from note to note, each note leant on a
    little), its beat 0 at scene time t0; beats [start, stop); hold: the last note's length (s)."""
    sel = notes_in(notes, start, stop)
    if not sel:
        return
    b0 = sel[0][0]
    pts, envp = [], [(0.0, 1.0)]
    for i, (b, d, p) in enumerate(sel):
        ts = (b - b0) * BEAT
        q = p + 12 * octave
        pts.append((ts, q))
        if i + 1 < len(sel):
            te = (sel[i + 1][0] - b0) * BEAT
            pts.append((te - 0.03, q))
            envp += [(max(ts, te - 0.05), 1.0), (te, 0.78), (te + 0.07, 1.0)]
        else:
            te = ts + (d * BEAT if hold is None else hold)
            pts.append((te, q))
    dur = pts[-1][0]
    envp.append((dur, 1.0))
    x = OF.bowed_line([(t, p - 46) for t, p in pts], dur, vel, seed, octaves=octaves, attack=attack, release=release,
                      bright=bright, env=envp)
    if shape:
        x = env(x, shape)
    m.put("music", x, t0 + b0 * BEAT, gain, pan=pan, label=label, align=None)


def pad(m, t0, prog, gain=-20.0, seed=0, start=0.0, stop=None, octaves=(0,), attack=0.25, release=0.7, vel=0.7,
        bright=4000.0, label=None, swell=False):
    """The progression held (beat 0 at scene time t0), chord by chord, clipped to beats [start, stop)."""
    for i, (b, nb, ch) in enumerate(chords_in(prog, start, stop)):
        d = nb * BEAT
        e = [(0.0, 0.55), (d, 1.0), (d + release, 1.0)] if swell else None
        x = held(ch, d + 0.04, vel, seed + i, octaves=octaves, attack=attack, release=release, env_=e, bright=bright)
        m.put("music", x, t0 + b * BEAT, gain, label=label if i == 0 else None, align=None)


def stealth(m, t0, t1, seed, gain=-18.5, fin=1.0, fout=0.6):
    """The hush's floor under the stealth: violas and cellos sul tasto on an open fifth (D-A) and a
    faint high harmonic A over them, equal-power fades. Never an event: it only keeps a hush
    audible on a phone speaker (the short-term loudness about -29 LUFS, not a drop-out)."""
    d = max(0.5, t1 - t0)
    lo = dsp.fade(held((50, 57), d, 0.5, seed, octaves=(0,), attack=0.05, release=0.05, bright=2500.0), fin, fout)
    hi = dsp.fade(harm(81, d, 0.35, seed + 1, attack=0.05, release=0.05, vib=0.002), fin * 1.5, fout)
    m.put("music", lo, t0, gain, align=None)
    m.put("music", hi, t0, gain - 14.0, pan=0.15, align=None)


def the_celesta(m, t, gain, pan=0.0, label=None):
    """THE celesta: one note in the whole film, the ruby's glint. A second is refused."""
    if m.celesta:
        warn(f"{m.sid} {t:.3f}: a second celesta note refused (the celesta is the ruby's glint alone)")
        return False
    m.celesta.append(m.t0 + t)
    m.put("music", OF.celesta(hz(HER + 12), 0.9, 1), t, gain, pan=pan, label=label, hall=-12.0)
    return True


# ============================================================================ foley and voices this film adds
VOX_TRIM = -10.0             # the voices' takes (RMS -20 dBFS) under the scene's cue gain


def say(m, who, k, t, gain, fit=None, seed=0, label=None):
    """Line k of this voice, its syllables shuffled (DOUBLE CROSS's murmur: it never says a word),
    low-passed further, in the scene's room; where it ends."""
    x = DC.murmur(who, k, None if fit is None else round(fit, 3), seed)
    x = dsp.sos(x, "lowpass", 0.8 * DC.VOICE[who][0], 2)
    m.put("vox", roomed(m, x, t, seed), t, gain, pan=DC.VOICE[who][1], label=label, align=None, key=True)
    return t + len(x) / SR


GRUNTS = ((5.06, 5.76, 0.168), (0.10, 1.64, 0.257), (0.28, 0.95, 0.10))   # (a, b, onset) in grunt_knight


def grunt(m, t, gain, k=0, pan=0.0, label=None, wet=None):
    """The Knight's grunt, his own take: 0 short, 1 strained and held, 2 a shorter strain."""
    a, b, on = GRUNTS[k % 3]
    x = dsp.sos(DC.take_cut("grunt_knight", a, b, 0.03, 0.25 if k == 1 else 0.12, rms=db2lin(-11.2)), "lowpass",
                9000.0, 2)
    m.put("vox", roomed(m, x, t, k, wet=wet), t - on, gain, pan=pan, label=label, sync=t, align=None, key=True)


def laugh(m, t, gain, pan=0.0, label=None):
    """Her breath of a laugh, her own take."""
    x = DC.take_cut("laugh_her", 2.25, 2.72, 0.01, 0.06, rms=db2lin(-11.2))
    m.put("vox", roomed(m, x, t), t - 0.06, gain, pan=pan, label=label, sync=t, align=None, key=True)


def breath(m, kind, t, gain, pan=0.0, label=None, dur=None, semis=0.0, key=True):
    """A breath cut from the OPPOSITE recordings (DC's breath: ragged, out, in, draw, gasp, held)."""
    x = mono(DC.breath(kind))
    if semis:
        x = pitch(x, semis)
    if dur:
        x = dsp.fade(x[:n_of(dur + 0.25)], 0.02, 0.2)
    m.put("vox", roomed(m, x, t), t, gain, pan=pan, label=label, align=None, key=key)


@lru_cache(maxsize=None)
def chuckle_breath(seed=0):
    """A dry chuckle with no voice in it: his exhale (the recording) broken into three huffs."""
    x = pitch(mono(DC.breath("out")), -2.0)[: n_of(0.75)]
    t = tax(len(x))
    am = np.clip(np.sin(2 * np.pi * 6.2 * t + 0.3), 0, None) ** 1.4 * np.exp(-t / 0.45)
    return norm(dsp.fade(dsp.bandpass(x * am, 250.0, 3500.0, 2), 0.005, 0.08))


@lru_cache(maxsize=None)
def wheeze(seed=0):
    """An old man's breath held in: an intake, lower, a whistle in it."""
    x = pitch(mono(DC.breath("in")), -3.0)
    x = dsp.biquad(x, "peak", 1700.0, 6.0, 9.0)
    return norm(dsp.fade(x, 0.01, 0.12))


def _pop(r, a=1.0):
    p = sfx._thump(n_of(0.2), 85.0, 48.0, 0.01, 0.08)
    q = np.zeros(len(p))
    q[:n_of(0.1)] = 0.6 * sfx._burst(n_of(0.1), r, 90.0, 900.0, t60=0.03)
    return a * norm(p + q)


@lru_cache(maxsize=None)
def cough_die(seed=0):
    """The getaway car won't start: the starter whining, a cough, a sputter dying."""
    r = rng("cough", seed)
    st = 0.26 + 0.06 * r.uniform()
    n = n_of(st + 0.6)
    y = np.zeros(n)
    tm = tax(n_of(st))
    whine = dsp.bandpass(dsp.saw(112.0 * (1 + 0.05 * np.sin(2 * np.pi * 6.2 * tm)), len(tm)), 150.0, 2200.0, 2)
    comp = 0.45 + 0.55 * (0.5 + 0.5 * np.cos(2 * np.pi * 6.2 * tm)) ** 3
    dsp.mix_into(y, 0.5 * norm(whine * comp) * np.clip(tm / 0.02, 0, 1) * np.clip((st - tm) / 0.04, 0, 1), 0)
    for tt, a in ((st, 1.0), (st + 0.14, 0.55)):
        dsp.mix_into(y, _pop(r, a), n_of(tt))
    k = n_of(st + 0.05)
    te = tax(n - k)
    eng = norm(sfx._engine(n - k, r, 60.0 + 650.0 * np.exp(-te / 0.12), 0.5)) * np.exp(-te / 0.12)
    dsp.mix_into(y, 0.5 * eng, k)
    return norm(dsp.fade(y, 0.002, 0.05))


@lru_cache(maxsize=None)
def engine_catch(dur=6.0, seed=0):
    """The engine catches: a roar (the revs flung up), settling to a hard, lumpy idle."""
    r = rng("catch", seed, round(dur, 2))
    n = n_of(dur)
    t = tax(n)
    y = np.zeros(n)
    dsp.mix_into(y, _pop(r, 1.1), 0)
    rpm = 900.0 + 2700.0 * np.clip(t / 0.35, 0, 1) ** 0.7 * np.exp(-np.clip(t - 0.7, 0, None) / 0.8)
    rpm = np.maximum(rpm, 1050.0 + 200.0 * np.exp(-t / 3.0))
    y += 0.95 * norm(sfx._engine(n, r, rpm, 0.5)) * np.clip(t / 0.03, 0, 1)
    return norm(dsp.fade(y, 0.002, 0.3))


@lru_cache(maxsize=None)
def rev_hard(dur=0.9, seed=0):
    """His engine revved hard off the curb: the revs climbing, the tyres scrubbing."""
    r = rng("rev", seed)
    n = n_of(dur)
    t = tax(n)
    rpm = 1300.0 + 2600.0 * np.clip(t / 0.4, 0, 1) ** 0.6
    y = norm(sfx._engine(n, r, rpm, 0.9)) * np.clip(t / 0.03, 0, 1)
    sq = DC.tyre_squeal(round(min(0.45, dur), 2), seed, 1700.0, 0.1)
    dsp.mix_into(y, 0.6 * norm(sq), n_of(0.05))
    return norm(dsp.fade(y, 0.003, 0.15))


@lru_cache(maxsize=None)
def car_door_open(seed=0):
    """A car door flung open: the latch, the hinge."""
    r = rng("cdoor", seed)
    y = np.zeros(n_of(0.6))
    dsp.mix_into(y, norm(sfx._hit(r, [900.0, 1700.0, 2600.0], [0.03, 0.02, 0.015], click=0.8, n=n_of(0.12))), 0)
    dsp.mix_into(y, 0.5 * norm(OF.creak(0.35, seed % 4, iron=True)), n_of(0.04))
    dsp.mix_into(y, 0.4 * norm(sfx._thump(n_of(0.15), 140.0, 90.0, 0.01, 0.05)), 0)
    return norm(dsp.fade(y, 0.001, 0.08))


@lru_cache(maxsize=None)
def grating_clank(seed=0):
    """A boot on the gully's iron grating, heard from under it: a heavy, dull iron clank."""
    x = pitch(DC.rung(seed % 6), -5.0)
    y = np.zeros(max(len(x), n_of(0.5)))
    y[:len(x)] += norm(x)
    c = cut(DC.manhole_clank(seed % 3), 0.45, 0.2)
    y[:len(c)] += 0.7 * norm(c)
    y[:n_of(0.2)] += 0.6 * norm(sfx._thump(n_of(0.2), 120.0, 70.0, 0.01, 0.06))
    return norm(dsp.sos(y, "lowpass", 2600.0, 2))


@lru_cache(maxsize=None)
def tyre_kick(seed=0):
    """A boot into a tyre: a dull rubber thud."""
    r = rng("kick", seed)
    y = 1.0 * sfx._thump(n_of(0.35), 110.0, 58.0, 0.012, 0.09)
    y[:n_of(0.06)] += 0.5 * sfx._burst(n_of(0.06), r, 120.0, 1200.0, t60=0.02)
    return norm(dsp.fade(y, 0.0, 0.05))


@lru_cache(maxsize=None)
def gold_spill(seed=0, n=6, dur=0.7):
    """A sack dropped: its thump, the gold bars spilling out and clinking on the road."""
    r = rng("spill", seed)
    y = np.zeros(n_of(dur + 0.6))
    dsp.mix_into(y, 1.2 * norm(DC.gold_bag(seed % 5)), 0)
    dsp.mix_into(y, 0.8 * norm(sfx._thump(n_of(0.3), 120.0, 60.0, 0.012, 0.1)), 0)
    for k in range(n):
        tt = 0.05 + dur * (k / n) ** 1.3 + r.uniform(0, 0.03)
        dsp.mix_into(y, 0.7 * (0.85 ** k) * DC.gold_clink((seed + k) % 5, 0.2), n_of(tt))
    return norm(y)


@lru_cache(maxsize=None)
def chain_rattle(seed=0):
    """The lamp's chain pulled: a short rattle of links."""
    r = rng("rattle", seed)
    y = np.zeros(n_of(0.45))
    for k in range(5):
        dsp.mix_into(y, (0.9 - 0.12 * k) * norm(OF.link_tink(seed * 5 + k)), n_of(0.025 * k + r.uniform(0, 0.012)))
    return norm(dsp.fade(y, 0.0, 0.1))


@lru_cache(maxsize=None)
def soft_door(seed=0):
    """A door closed softly: the wood meeting its frame, the latch."""
    y = np.zeros(n_of(0.6))
    dsp.mix_into(y, dsp.sos(DC.wood_thunk(seed % 3, 0.7), "lowpass", 1200.0, 2), 0)
    dsp.mix_into(y, 0.35 * norm(DC.knob_tick(seed % 3)), n_of(0.03))
    return norm(dsp.fade(y, 0.0005, 0.1))


@lru_cache(maxsize=None)
def torch_pop(seed=0):
    """A blowtorch lit: a soft pop and its hiss."""
    r = rng("tpop", seed)
    y = np.zeros(n_of(0.5))
    dsp.mix_into(y, 0.8 * norm(sfx._thump(n_of(0.15), 260.0, 120.0, 0.006, 0.04)), 0)
    dsp.mix_into(y, 0.5 * norm(sfx._burst(n_of(0.08), r, 500.0, 6000.0, t60=0.03)), 0)
    dsp.mix_into(y, 0.45 * norm(DC.flame_bed(0.45, seed % 3)), n_of(0.03))
    return norm(dsp.fade(y, 0.0, 0.1))


@lru_cache(maxsize=None)
def match_out(seed=0):
    """A match shaken out: a flick of air and the flame's hiss gone."""
    y = np.zeros(n_of(0.4))
    f = DC.flame_bed(0.4, seed % 3)
    dsp.mix_into(y, 0.6 * norm(f) * np.exp(-tax(len(f)) / 0.06), 0)
    dsp.mix_into(y, 0.5 * norm(mono(DC.whip_down(0.2, seed % 3))), 0)
    return norm(dsp.fade(y, 0.002, 0.08))


@lru_cache(maxsize=None)
def pat(seed=0):
    """A gloved pat on a coat pocket."""
    r = rng("pat", seed)
    y = np.zeros(n_of(0.2))
    dsp.mix_into(y, 0.7 * norm(sfx._thump(n_of(0.1), 180.0, 110.0, 0.006, 0.03)), 0)
    dsp.mix_into(y, 0.5 * norm(DC.cloth(0.12, seed % 5, 1.0)), 0)
    dsp.mix_into(y, 0.2 * norm(sfx._burst(n_of(0.04), r, 600.0, 3000.0, t60=0.015)), 0)
    return norm(dsp.fade(y, 0.0005, 0.04))


@lru_cache(maxsize=None)
def string_snap(seed=0):
    """A string snapped against the fingerboard (Bartok's pizzicato), low."""
    r = rng("snap", seed)
    y = np.zeros(n_of(0.9))
    dsp.mix_into(y, norm(OF.pizz(hz(38), 1.0, seed)), 0)
    dsp.mix_into(y, 0.7 * norm(sfx._hit(r, [1800.0, 2900.0], [0.01, 0.008], click=1.0, n=n_of(0.03))), 0)
    return norm(y)


def far(x, lp=1800.0):
    """Through walls: the top gone."""
    return dsp.sos(np.asarray(x, np.float64), "lowpass", lp, 2)


def alarm(dur, t0=0.0, seed=0, depth=0.3):
    """The alarm bell (DC's: D6, her note), a swell on every beat (its red ripples)."""
    x = DC.alarm_bell(round(dur, 2), seed)
    return x * beat_pulse(len(x), t0, depth)


def night_bed(dur, seed=0, lp=5000.0, wind=0.6):
    """The night street: the far city and a breath of wind (no siren in it: the police come later)."""
    c = bed("city_far", dur, seed, lp=lp)
    w = bed("wind_gust", dur, seed + 1, lp=min(lp, 2500.0))
    k = min(len(c), len(w))
    return c[:k] + wind * w[:k]


def heart_rings(m, t0, t1, bpm, film=True, gain=-8.0, pan=0.0, label="heartbeat", shape=None, dub=0.26):
    """A heartbeat on the picture's rings (kit.heartbeat: a lub every 60/bpm s of the film's clock,
    or of the scene's when film=False) from t0 to t1 (scene time); shape(u) -> dB over the span."""
    per = 60.0 / bpm
    base = m.t0 if film else 0.0
    k = math.ceil((base + t0 - 1e-6) / per)
    j = 0
    while (k * per - base) < t1 - 1e-6:
        t = k * per - base
        u = (t - t0) / max(t1 - t0, 1e-6)
        m.put("music", OF.heart(dub, seed=j % 3), t, gain + (shape(u) if shape else 0.0), pan=pan, label=label, hall=-24.0)
        k += 1
        j += 1


def wall_clock(m, t0, t1, level, pan=0.2):
    """The crew's wall clock: a tick on every beat (tick, tock), its level level(t) dB (None: no
    tick), in the room. The press beats take their cue's gain."""
    k = math.ceil((m.t0 + t0) / BEAT - 1e-9)
    while True:
        tf = k * BEAT
        t = tf - m.t0
        if t >= t1 - 1e-6:
            break
        lv = level(t)
        c = m.cue_near(t, "clock tick", "ticks", win=0.02)
        if c is not None:
            lv = c["gain_db"] - 8.0
        if lv is not None:
            x = roomed(m, mono(OF.tick(k % 2)), t, k, wet=-22.0)
            m.put("tick", x, t, lv, pan=pan, label="the wall clock" if c is not None else None, hall=None)
        k += 1


BANK_TICK = (60.0, 91.0)     # film: the hall's clock heard from s04 12.0 to the door's swing (s06 11.0)


def bank_clock(m, gain=-21.0):
    """The beat's tick in the bank (the hall's clock): every beat inside BANK_TICK and this scene."""
    a, b = max(BANK_TICK[0], m.t0), min(BANK_TICK[1], m.t0 + m.len)
    k = math.ceil(a / BEAT - 1e-9)
    while k * BEAT < b - 1e-6:
        t = k * BEAT - m.t0
        x = dsp.sos(pitch(mono(OF.tick(k % 2)), -4.0), "lowpass", 3000.0, 2)
        m.put("tick", roomed(m, x, t, k, wet=-12.0), t, gain + (1.0 if k % 2 == 0 else 0.0), pan=-0.15, hall=None)
        k += 1


SECTIONS = []


def section(sid):
    def deco(fn):
        SECTIONS.append((sid, fn))
        return fn
    return deco


# ============================================================================ s01 TITLE (0-14)
@section("s01")
def s01(m, S):
    T_DOT = m.ats("T_DOT", (0.25, 0.5, 0.75), "red dot ticks", "dot tick")
    T_LEAD = m.at("T_LEAD", 1.125, "strips race", "string stabs")
    words = g(S, "T_WORDS", ((1.3, 1.0), (1.55, 1.0)))
    T_STRIPS = m.ats("T_STRIPS", (2.75, 3.0))
    STRIP_IN = g(S, "STRIP_IN", 0.24)
    T_PART = m.at("T_PART", 3.4, "halves part", "tear")
    T_FLOOD = m.at("T_FLOOD", 4.1, "floods", "rush")
    T_MORPH = m.at("T_MORPH", 4.3, "become windows")
    MORPH_DUR = g(S, "MORPH_DUR", 0.55)
    T_NIGHT = m.at("T_NIGHT", 5.5, "night falls", "gong")
    T_CITY = m.at("T_CITY", 5.75, "city rises", "pizzicato descent")
    T_MOON = m.at("T_MOON", 6.0, "moon", "soft bell")
    T_CUT = m.at("T_CUT", 6.5)
    T_STOREY = m.ats("T_STOREY", (6.75, 7.0, 7.25, 7.5, 7.75), "storey", n=5)
    t_lamp = m.at("", 7.3, "street lamp", "low hum")
    u0, u1 = m.span("T_UNDER", (8.0, 9.0), "road opens", "stone sliding")
    T_VAULT = m.at("T_VAULT", 8.5, "vault and its gold", "cello note")
    T_OUT = m.ats("T_OUT", (9.0, 9.5, 10.0), "light out")
    OUT_ORDER = g(S, "OUT_ORDER", (5, 2, 3))
    T_CITY_OUT = m.at("T_CITY_OUT", 10.5, "far city goes dark", "last low pluck")
    T_FOUR = m.at("T_FOUR", 10.75, "crew's 4", "high pizzicato")
    p0, p1 = m.span("T_PUSH", (11.5, 14.0), "rising tremolo")
    p1 = min(p1, m.len)

    # 0-1: the red dot: three soft felt notes up the chord (D F A), each with a dry tick
    for i, t in enumerate(T_DOT):
        m.put("music", OF.soft_hit(hz((62, 65, 69)[i % 3]), i), t, -16.0 + 1.0 * i, label="the red dot")
        m.put("efx", OF.tick(i), t, cgain(m, t, "tick", default=-10.0) - 12.0)

    # 1.125: the strips race: a run of fast string stabs on the Psycho chord, in sixteenths
    sl0 = T_STRIPS[0] - STRIP_IN
    ostinato(m, T_LEAD, sl0, notes=tuple(p - 12 for p in PSY), step=E16, vel=(0.5, 0.95), accent=(0, 4, 8, 12),
             gain=cgain(m, T_LEAD, "stabs", default=-12.0) - 2.0, seed=1, label="the strips race: string stabs")
    # the words assemble from cut strips: a rustle, the strips snapping together (CROSS lower)
    for w, (t, d) in enumerate(words[:2]):
        ru = cut(mono(fx("paper_rustle", seed=11 + w)), 0.55, 0.2)
        m.put("efx", pitch(ru, -3.0 * w), t, cgain(m, t, "assembles", default=-14.0) - 2.0, pan=(-0.25, 0.25)[w],
              label="a word assembles", align=None)
        for j in range(3):
            m.put("efx", pitch(OF.paper_snap(20 + 3 * w + j), -3.0 * w), t + 0.16 + 0.13 * j, -26.0 - 2.0 * w,
                  pan=(-0.3, 0.3)[w])
    # the X: each strip slashes in (a whoosh) and lands (a thud, a string stab)
    for i, land in enumerate(T_STRIPS[:2]):
        s0 = land - STRIP_IN
        m.put("efx", DC.whoosh_thud(round(STRIP_IN, 3), 3 + i, 0.6 * i), s0,
              cgain(m, s0, "whoosh", default=-8.0) - 2.0, pan=(-0.2, 0.2)[i], label="a strip slashes in", align=None)
        m.put("music", stab(PSY, i, low=bool(i)), land, -12.0 + 1.5 * i, label="the strip lands: a stab")
    m.put("music", OF.rev(held(tuple(p - 12 for p in PSY), 0.5, 0.8, 21, octaves=(0, 1), attack=0.01, release=0.4),
                          -10.0, 2), T_STRIPS[-1], -16.0)
    # 3.4: the X lifts off, the halves part: a paper tear, a swish either way
    x = fx("paper_tear", seed=4, size=0.6)
    m.put("efx", x, T_PART - onset_at(x), cgain(m, T_PART, "tear", default=-11.0), label="the halves part: a tear",
          sync=T_PART)
    for j in range(2):
        m.put("efx", DC.paper_whoosh(0.5, j), T_PART + 0.03 + 0.05 * j, -18.0, pan=(-0.5, 0.5)[j], align=None)
    # into the night: a soft ostinato, growing to the gong
    ostinato(m, T_STRIPS[-1] + 0.5, T_NIGHT, notes=PSY, step=E8, vel=(0.3, 0.6), accent=(0, 3), gain=-16.0, seed=5)
    m.put("efx", OF.rush(0.9, 3), T_FLOOD, cgain(m, T_FLOOD, "rush", default=-16.0), label="the paper floods in",
          align=None)
    # the letters become windows: a small paper snap as each lands
    letters = [len(w[0]) for w in g(S, "WORDS", (("DOUBLE", None, None), ("CROSS", None, None)))
               if isinstance(w, (tuple, list)) and w and isinstance(w[0], str)] or [6, 5]
    m.mark(T_MORPH, "the letters become windows (a snap each)")
    for w, nl in enumerate(letters):
        for i in range(nl):
            ts = T_MORPH + 0.04 * i + 0.1 * w + 0.85 * MORPH_DUR
            m.put("efx", OF.paper_snap(30 + 6 * w + i), ts, -27.0, pan=-0.4 + 0.08 * i + 0.3 * w)

    # 5.5: night falls: a low gong on D, D minor low under it; the city rises: a pizzicato descent
    m.put("music", OF.gong(hz(38), 1), T_NIGHT, -13.0, label="night falls: the gong")
    m.put("music", OF.rev(held((38, 45, 50, 53), 2.5, 0.5, 31, octaves=(0,), attack=0.4, release=1.0), -10.0, 3),
          T_NIGHT, -21.0)
    for j, p in enumerate((73, 69, 65, 62, 61, 57, 53, 50)):
        m.put("music", pz(p, 0.85 - 0.04 * j, j), T_CITY + E16 * j, cgain(m, T_CITY, "pizzicato", default=-12.0),
              pan=0.4 - 0.1 * j, label="the city rises: a pizzicato descent" if j == 0 else None)
    m.put("music", OF.bell(hz(81), 1), T_MOON, -18.0, pan=0.35, label="the moon: a soft bell")
    city = night_bed(m.len - T_CITY, 11, lp=4000.0, wind=0.3)
    m.put("amb", env(city, [(0.0, 0.0), (0.8, 1.0), (p0 - T_CITY, 1.0), (len(city) / SR, 0.25)]), T_CITY, -32.0)

    # 6.5: the cutaway: a whoosh; D minor held under it; a click and a harp note up the chord per
    # storey; a soft pulse a beat (the city's life); the radio through the wall; the street lamp
    m.put("efx", fx("whoosh", seed=70, size=0.55), T_CUT - 0.22, -21.0, align=None)
    m.put("music", held((50, 53, 57), p0 - T_CUT, 0.6, 3, octaves=(-1, 0), attack=0.6, release=1.0,
                        env_=[(0.0, 0.6), (1.5, 1.0), (p0 - T_CUT, 0.8)]), T_CUT, -23.0)
    for i, t in enumerate(T_STOREY):
        m.put("efx", OF.paper_snap(i), t, cgain(m, t, "storey", default=-14.0) - 10.0, pan=(-0.3, 0.3)[i % 2])
        m.put("music", hp((62, 65, 69, 73, 74, 77)[i % 6], 0.7, i), t, -14.0, pan=(-0.25, 0.25)[i % 2],
              label=f"storey {i + 1} opens")
    t, k = math.ceil((T_STOREY[0] + 1e-6) / BEAT) * BEAT, 0
    while t < p0 - 1e-6:
        m.put("music", pz(38 if k % 2 == 0 else 33, 0.55, 20 + k), t, -19.0)
        t, k = t + BEAT, k + 1
    rad = cues_with(m, "radio")
    r0 = rad[0][0] if rad else (T_STOREY[1] if len(T_STOREY) > 1 else 7.0)
    r1 = T_OUT[list(OUT_ORDER).index(2)] if 2 in OUT_ORDER and len(T_OUT) == len(OUT_ORDER) else r0 + (
        rad[0][1] if rad and rad[0][1] else 2.5)
    x = far(OF.radio(max(0.5, r1 - r0), 1), 1500.0)
    m.put("amb", dsp.fade(x, 0.15, 0.05), r0, cgain(m, r0, "radio", default=-26.0) - 6.0, pan=-0.45,
          label="the radio through the wall", align=None)
    m.put("efx", OF.switch(4), r1 - 0.005, -30.0, pan=-0.45)
    m.put("efx", DC.lamp_on(2, 2.0), t_lamp, cgain(m, t_lamp, "lamp", default=-20.0) - 2.0, pan=0.3,
          label="the street lamp comes on")
    # 8.0: the road opens down: stone sliding, a hollow drip far below; 8.5 the vault's gold
    m.put("efx", roomed(m, DC.tile_scrape(2), u0, wet=-12.0), u0, cgain(m, u0, "stone", default=-14.0) - 2.0,
          label="the road opens: stone sliding", align=None)
    m.put("amb", DC.far_drip(1), u0 + 0.62, -24.0, pan=-0.2)
    m.put("music", bow([(0.0, 38)], 1.9, 0.9, 9, octaves=(0, 1), attack=0.25, release=1.0), T_VAULT,
          cgain(m, T_VAULT, "cello", default=-10.0) - 2.0, label="the vault: a deep cello note", align=None)
    m.put("music", shimmer(1.4, 1, 93), T_VAULT + 0.1, -24.0, pan=0.2)
    # 9.0: the city goes to bed: a harp note down the chord per light, a switch each
    for j, t in enumerate(T_OUT):
        side = -0.35 if j % 2 == 0 else 0.35
        m.put("music", hp((81, 77, 74, 69)[min(j, 3)], 0.75, 10 + j), t, cgain(m, t, "light out", default=-12.0) - 1.0,
              pan=side, label="a light goes out")
        m.put("efx", OF.switch(10 + j), t - 0.01, -31.0, pan=side)
    m.put("music", hp(50, 0.8, 4), T_CITY_OUT, cgain(m, T_CITY_OUT, "pluck", default=-14.0), pan=0.1,
          label="the far city goes dark: a low pluck")
    m.put("music", pz(HER, 0.8, 5), T_FOUR, cgain(m, T_FOUR, "pizzicato", default=-12.0) - 1.0, pan=-0.2,
          label="the crew's 4: one high pizzicato")
    # 11.5: a tremolo rising into the crew's room, a chord a beat (i iv i6/4 V V7), to the cut
    steps = ((50, 53, 57), (55, 58, 62), (57, 62, 65), (57, 61, 64), (55, 57, 61, 64))
    k = 0
    while p0 + k * BEAT < p1 - 1e-6:
        t = p0 + k * BEAT
        d = min(BEAT + 0.04, p1 - t)
        x = trem(steps[min(k, len(steps) - 1)], d + 0.02, 0.8, seed=7 + k)[: n_of(d)]
        m.put("music", dsp.fade(x, 0.004, 0.02), t, -20.0 + 2.5 * k, label="a tremolo into the room" if k == 0 else None,
              align=None)
        k += 1
    m.put("music", fx("reverse_swell", dur=round(p1 - p0, 2), seed=8), p0, -23.0)
    m.put("music", bow([(0.0, 33)], p1 - p0, 0.7, 12, octaves=(0, 1), attack=1.5, release=0.05), p0, -21.0)


# ============================================================================ s02 CREW (14-30)
def clock_level_s02(t):
    return -18.0 if t < 2.0 else -21.0 if t < 6.5 else -26.0 if t < 11.5 else -21.0


@section("s02")
def s02(m, S):
    T_HER = m.at("T_HER", 2.0, "her cameo")
    T_CR = m.at("T_CRACKER", 3.5, "cracker's cameo")
    T_KN = m.at("T_KNIGHT", 5.0, "knight's cameo")
    T_GLINT = m.at("T_GLINT", 4.25, "glint", "spectacles")
    T_DRAW = m.at("", 5.4, "draws on it", "cigarette crackles")
    T_OTS = m.at("T_OTS", 6.5, "over her shoulder", "night street")
    T_TINK = m.at("T_TINK", 8.6, "tink")
    T_BEGIN = m.at("T_BEGIN", 14.0, "murmur", "low voice")
    L = m.len

    # the room: the wall clock on every beat, the lamp's chain, the room's own tone
    wall_clock(m, 0.0, L, clock_level_s02)
    m.put("efx", roomed(m, DC.chain_creak(2.0, 1), 0.0), 0.0, cgain(m, 0.0, "chain", default=-16.0) - 4.0, pan=0.1,
          label="the lamp's chain", align=None)
    m.put("efx", roomed(m, DC.chain_creak(2.4, 2), 11.6), 11.6, -27.0, pan=0.1)
    m.put("amb", bed("room_tone", L, 21, lp=2500.0), 0.0, -30.0)
    tc = m.at("", 0.6, "cigarette", "faint crackle")
    m.put("efx", cut(fx("ember_sizzle", seed=2), 0.9, 0.3), tc, cgain(m, tc, "crackle", default=-22.0) - 2.0, pan=0.35,
          label="the cigarette's crackle", align=None)

    # the three cameos, plucked: her D high, the old man's A, the Knight's low C#
    m.put("music", pz(HER_P, 0.85, 1), T_HER, cgain(m, T_HER, "cameo", default=-11.0) - 2.0, pan=-0.2,
          label="her cameo: D")
    m.put("music", pz(MID, 0.85, 2), T_CR, cgain(m, T_CR, "cameo", default=-11.0) - 2.0, pan=0.1,
          label="the old man's cameo: A")
    m.put("music", harm(93, 0.16, 0.8, 3, attack=0.01, release=0.3, sfz=True), T_GLINT,
          cgain(m, T_GLINT, "harmonic", default=-18.0) - 2.0, pan=0.25, label="a glint: a harmonic flick", align=None)
    m.put("music", pz(HIS, 0.95, 3), T_KN, cgain(m, T_KN, "cameo", default=-10.0) - 1.0, pan=0.3,
          label="the Knight's cameo: low C#")
    m.put("music", bow([(0.0, HIS)], 1.0, 0.5, 4, octaves=(0,), attack=0.05, release=0.6), T_KN, -24.0, pan=0.3)
    m.put("efx", cut(fx("ember_sizzle", seed=5), 0.8, 0.3), T_DRAW, cgain(m, T_DRAW, "crackle", default=-16.0) - 2.0,
          pan=0.3, label="he draws on the cigarette", align=None)
    breath(m, "draw", T_DRAW + 0.05, -26.0, pan=0.3)

    # over her shoulder: the night street through the glass; the guard's far steps; the bell's tink
    ob = cues_with(m, "night street", "far wind")
    d_ots = ob[0][1] if ob and ob[0][1] else 5.0
    x = night_bed(d_ots, 23, lp=1400.0, wind=0.8)
    m.put("amb", x, T_OTS, cgain(m, T_OTS, "night street", default=-22.0) - 6.0, label="the night street, through the glass",
          align=None)
    for j, (t, _, c) in enumerate(cues_with(m, "far footstep")):
        x = far(DC.footstep("guard", 3 + j, None), 1300.0)
        m.put("feet", dsp.reverb(x, "street", wet_db=-6.0, seed=j), t - STEP_PRE, c["gain_db"] + CUE_TRIM - 4.0,
              pan=c["pan"], label="the guard's far step", sync=t)
    m.put("efx", roomed(m, DC.bell_tink(1), T_TINK), T_TINK, cgain(m, T_TINK, "tink", default=-14.0),
          pan=cpan(m, T_TINK, "tink", default=-0.3), label="the damped tink")

    # THE THEME, first time: the harp alone, from bar 10, over the window and the table; the harp's
    # bass a note a bar; then (14.0) the second time, pizzicato over the strings, under her murmur
    t_a = 6.0
    pluck_line(m, t_a, THEME, "harp", -13.0, pan=-0.15, vel=0.8, seed=40, label="THE THEME (harp)")
    for i, (b, nb, ch) in enumerate(chords_in(PROG)):
        m.put("music", hp(ch[0] + 12 if ch[0] < 36 else ch[0], 0.6, 50 + i), t_a + b * BEAT, -19.0, pan=0.1)
    t_b = T_BEGIN
    pluck_line(m, t_b, THEME, "pizz", -12.0, pan=-0.1, vel=0.85, seed=60, stop=4, label="THE THEME again (pizzicato)")
    pad(m, t_b, PROG, -25.0, seed=70, stop=4, octaves=(0,), attack=0.5)
    m.put("music", pz(38, 0.7, 6), t_b, -17.0, pan=0.05)

    # the window and the table: her turn, her heels, the plan spread; the Knight off the wall; the
    # chair; she begins: her murmur, low and close, no words
    tt = m.at("T_TURN", 10.75, "coat", "rustle")
    m.put("efx", roomed(m, DC.cloth(0.5, 1, 1.0), tt), tt, cgain(m, tt, "rustle", default=-18.0), pan=-0.2,
          label="she turns: a coat's rustle", align=None)
    th = m.at("", 11.6, "her heels")
    for j in range(2):
        m.put("feet", DC.footstep("her", j, "small_room", j), th + 0.38 * j - STEP_PRE,
              cgain(m, th, "heels", default=-16.0) - 1.5 * j, pan=cpan(m, th, "heels", default=0.2) - 0.1 * j,
              label="her heels" if j == 0 else None, sync=th + 0.38 * j)
    tp = m.at("T_SPREAD", 12.0, "unrolled", "paper")
    m.put("efx", roomed(m, DC.paper_unroll(0.75, 1), tp), tp, cgain(m, tp, "paper", default=-12.0) - 1.0,
          label="the plan spread", align=None)
    m.put("efx", roomed(m, cut(mono(fx("paper_rustle", seed=7)), 0.5, 0.2), tp + 0.55), tp + 0.55, -22.0)
    tk = m.at("", 12.35, "heavy steps")
    for j in range(2):
        m.put("feet", DC.footstep("knight", j, "small_room", j), tk + 0.45 * j - STEP_PRE,
              cgain(m, tk, "heavy steps", default=-15.0) - 2.0 * j, pan=cpan(m, tk, "heavy steps", default=-0.3),
              label="the Knight's steps" if j == 0 else None, sync=tk + 0.45 * j)
    tch = m.at("", 12.6, "chair")
    m.put("efx", roomed(m, OF.creak(0.45, 3), tch), tch, cgain(m, tch, "chair", default=-18.0), pan=-0.2,
          label="the chair creaks", align=None)
    say(m, "her", 0, T_BEGIN, cgain(m, T_BEGIN, "murmur", default=-10.0) + VOX_TRIM, fit=max(0.5, L - T_BEGIN - 0.05),
        label="her murmur (no words)")


# ============================================================================ s03 PLAN (30-48)
def clock_level_s03(t):
    return (-22.0 if t < 9.0 else -19.0 if t < 12.0 else -16.0 if t < 15.5 else -19.0)


@section("s03")
def s03(m, S):
    T_RING = m.at("T_RING", 5.0, "sting", "red ring")
    T_GLINT = m.at("T_GLINT", 5.4, "glint", "shimmer")
    T_LK = m.at("T_LOOK_K", 6.0, "his low note", "cello c sharp")
    T_LC = m.at("T_LOOK_C", 6.5, "old man's look", "middle pizzicato")
    T_LH = m.at("T_LOOK_H", 7.25, "her look", "violin d")
    T_SLIP = m.at("T_SLIP", 8.25, "low held note", "slips")
    T_ANS = m.at("T_ANSWER", 8.75, "drip-like pluck", "pluck")
    g0, g1 = m.span("T_GROW", (9.6, 10.6), "braam")
    T_CLAW = m.at("T_CLAW", 10.55, "claw", "string snap")
    T_SNAP = m.at("T_SNAP", 11.0, "snaps back", "low thud")
    T_MIRROR = m.at("T_MIRROR", 12.0, "mirror", "dissonance")
    T_HIS_DOTS = m.at("T_HIS_DOTS", 12.15, "his look sinking", "descending")
    T_HER_DOTS = m.at("T_HER_DOTS", 12.6, "crosses the line", "thin high string")
    T_OUT = m.at("T_OUT", 15.5)
    T_PULL = m.at("T_PULL", 16.3, "cord pulled", "rattles")
    T_DARK = m.at("T_DARK", 16.5, "click", "goes out")
    L = m.len

    # the clock, by shot, louder as the halves press in; it stops at the click: silence
    wall_clock(m, 0.0, T_DARK, clock_level_s03)
    m.put("amb", bed("room_tone", T_DARK + 0.2, 31, lp=2500.0, fout=0.05), 0.0, -38.0)
    # the briefing: her murmur (no words); the old man listening: a low cello hum
    mu = cues_with(m, "murmur")
    if mu:
        t, d, c = mu[0]
        say(m, "her", 1, t, c["gain_db"] + CUE_TRIM + VOX_TRIM, fit=max(0.5, (d or 3.4) - 0.05),
            label="her murmur (no words)")
    for t, d, c in cues_with(m, "cello hum"):
        m.put("music", bow([(0.0, 45)], d or 3.0, 0.6, 31, octaves=(0,), attack=0.6, release=0.8), t,
              c["gain_db"] + CUE_TRIM - 4.0, pan=0.1, label="the old man listening: a cello hum", align=None)
    # her finger on the plan: taps, the glove sliding; the guard's light: a faint high glissando
    for j, (t, d, c) in enumerate(cues_with(m, "tap on paper", "second tap")):
        m.put("efx", roomed(m, DC.finger_tap(j, 0.45 if c["gain_db"] < -12 else 0.8), t), t,
              c["gain_db"] + CUE_TRIM, pan=c["pan"], label="a tap on the plan")
    for j, (t, d, c) in enumerate(cues_with(m, "glove sliding")):
        x = OF.rustle(round(d or 0.8, 2), 5 + j, 900.0, 5000.0)
        x = x * np.sin(np.pi * np.clip(tax(len(x)) / max(len(x) / SR, 1e-3), 0, 1)) ** 0.8
        m.put("efx", roomed(m, x, t), t, c["gain_db"] + CUE_TRIM - 2.0, pan=c["pan"], label="her glove slides",
              align=None)
    for t, d, c in cues_with(m, "glissando"):
        dd = d or 1.2
        x = harm(88, dd, 0.7, 6, attack=0.2, release=0.4, bend=lambda u, dd=dd: 5.0 * np.sin(np.pi * np.clip(u / dd, 0, 1)))
        m.put("music", x, t, c["gain_db"] + CUE_TRIM - 3.0, pan=0.3, label="the guard's light: a glissando", align=None)
    for t, d, c in cues_with(m, "tink"):
        m.put("efx", roomed(m, DC.bell_tink(2), t), t, c["gain_db"] + CUE_TRIM, pan=c["pan"], label="the damped tink")

    # THE THEME, the second time, from s02's 14.0: bars 2-4 here, landing on D as the ring closes
    t_b = -2.0
    pluck_line(m, t_b, THEME, "pizz", -12.0, pan=-0.1, vel=0.85, seed=60, start=4, label="THE THEME (pizzicato)")
    pad(m, t_b, PROG, -25.0, seed=70, start=4, octaves=(0,), attack=0.5)
    for i, (b, nb, ch) in enumerate(chords_in(PROG, 4)):
        m.put("music", pz(ch[0] if ch[0] >= 36 else ch[0] + 12, 0.7, 7 + i), t_b + b * BEAT, -17.0, pan=0.05)
    # 5.0: the sting: a high harmonic, sforzando, and the marker's squeak round the gold; a shimmer
    m.put("music", harm(93, 0.9, 0.9, 8, attack=0.01, release=0.8, sfz=True), T_RING,
          cgain(m, T_RING, "sting", default=-10.0) - 4.0, pan=0.2, label="the sting: a harmonic")
    m.put("efx", roomed(m, OF.squeak(0.4, 3), T_RING), T_RING, cgain(m, T_RING, "sting", default=-10.0) - 3.0, pan=0.2,
          label="the marker's squeak", align=None)
    m.put("music", shimmer(0.9, 2, 93), T_GLINT, cgain(m, T_GLINT, "shimmer", default=-17.0) - 4.0, pan=0.25,
          label="a glint on the gold: a shimmer", align=None)

    # 6.0-9.0 the looks: his C# held (a cello); the old man's A plucked; her D, high, held soft;
    # her look slips to the sewer: a low held D; a drip-like pluck where it lands
    d_k = (m.cue_near(T_LK, "c sharp", win=0.2) or {}).get("dur") or 3.0
    m.put("music", bow([(0.0, HIS)], d_k, 0.9, 11, octaves=(0, 1), attack=0.3, release=0.9), T_LK,
          cgain(m, T_LK, "c sharp", default=-12.0) - 3.0, pan=-0.3, label="his low note: C#", align=None)
    m.put("music", pz(MID, 0.8, 12), T_LC, cgain(m, T_LC, "pizzicato", default=-14.0) - 1.0, pan=0.1,
          label="the old man's look: A")
    d_h = (m.cue_near(T_LH, "violin", win=0.2) or {}).get("dur") or 1.0
    m.put("music", bow([(0.0, HER)], d_h, 0.7, 13, octaves=(0,), attack=0.3, release=0.8, vib=0.005, bright=7000.0),
          T_LH, cgain(m, T_LH, "violin", default=-14.0) - 6.0, pan=0.3, label="her look: D, high", align=None)
    d_s = (m.cue_near(T_SLIP, "held", win=0.2) or {}).get("dur") or 0.75
    m.put("music", bow([(0.0, 38)], d_s, 0.8, 14, octaves=(0, 1), attack=0.15, release=0.7), T_SLIP,
          cgain(m, T_SLIP, "held", default=-12.0) - 3.0, label="a low held note", align=None)
    m.put("music", OF.pluck(hz(HER), 0.7, 3, damp=0.06), T_ANS, cgain(m, T_ANS, "pluck", default=-18.0) - 1.0, pan=0.2,
          label="a drip-like pluck")
    # 9.0: the room from the side: the chain; 9.6 the golden arm: braam; the claw; the snap back
    for t, d, c in cues_with(m, "chain creaking", "chain"):
        if "rattle" in c["text"]:
            continue
        m.put("efx", roomed(m, DC.chain_creak(round(max(0.8, d or 2.0), 2), int(t)), t), t,
              c["gain_db"] + CUE_TRIM - 8.0, pan=0.1, label="the lamp's chain", align=None)
    m.put("music", fx("braam", seed=3), g0, cgain(m, g0, "braam", default=-8.0) - 2.0, label="braam: his golden arm",
          align=None)
    m.put("music", bow([(0.0, 26), (g1 - g0, 26)], g1 - g0 + 0.2, 0.9, 15, octaves=(0, 1), attack=g1 - g0,
                       release=0.25), g0, -14.0)
    m.put("efx", roomed(m, OF.scrape(0.25, 2), T_CLAW), T_CLAW, cgain(m, T_CLAW, "scrape", default=-10.0) - 2.0,
          label="the claw: a dry scrape", align=None)
    m.put("music", string_snap(1), T_CLAW + 0.12, -12.0, pan=-0.1)
    m.put("efx", DC.strip_thud(2), T_SNAP, cgain(m, T_SNAP, "thud", default=-8.0) - 2.0, pan=-0.3,
          label="the arm snaps back: a thud")
    m.put("efx", fx("whip", seed=6), T_SNAP - 0.12, -18.0, pan=-0.3)

    # 12.0 the mirror: her D6 against his C#2, sustained, the halves pressing in; his look sinks (a
    # low pizzicato run); hers crosses the line (a thin high line, rising)
    d_m = (m.cue_near(T_MIRROR, "mirror", win=0.2) or {}).get("dur") or 3.5
    envm = [(0.0, 0.5), (1.0, 0.7), (d_m - 0.6, 1.0), (d_m, 0.8)]
    m.put("music", harm(HER, d_m, 0.8, 16, attack=0.4, release=0.6, vib=0.003), T_MIRROR,
          cgain(m, T_MIRROR, "mirror", default=-10.0) - 6.0, pan=0.25, label="the mirror: her D against his C#",
          align=None)
    m.put("music", bow([(0.0, HIS)], d_m, 0.9, 17, octaves=(0, 1), attack=0.5, release=0.6, env=envm), T_MIRROR,
          cgain(m, T_MIRROR, "mirror", default=-10.0) - 3.0, pan=-0.25)
    m.put("music", trem((73, 74), d_m, 0.5, 18), T_MIRROR + 0.5, -27.0)
    for j, p in enumerate((49, 45, 41, 38, 37)):
        m.put("music", pz(p, 0.8 - 0.05 * j, 20 + j), T_HIS_DOTS + E16 * j, cgain(m, T_HIS_DOTS, "pizz", default=-14.0),
              pan=-0.4, label="his look sinks: a pizzicato run" if j == 0 else None)
    m.put("music", harm(HER, 0.9, 0.6, 19, attack=0.05, release=0.5, bend=lambda u: 7.0 * np.clip(u / 0.6, 0, 1)),
          T_HER_DOTS, cgain(m, T_HER_DOTS, "string line", default=-14.0) - 6.0, pan=0.2,
          label="her look crosses: a thin high line", align=None)

    # 15.5 lights out: the chain's rattle as she pulls the cord; click; silence; three of them leave
    m.put("efx", roomed(m, chain_rattle(1), T_PULL), T_PULL, cgain(m, T_PULL, "rattle", default=-12.0) - 2.0, pan=0.2,
          label="the chain rattles")
    m.put("efx", roomed(m, DC.switch_click(3, 0.8), T_DARK), T_DARK, cgain(m, T_DARK, "click", default=-6.0) - 2.0,
          pan=0.1, label="click: the lamp goes out")
    for t, d, c in cues_with(m, "soft steps", "three people"):
        gg = c["gain_db"] + CUE_TRIM
        m.put("efx", roomed(m, OF.scrape(0.3, 5), t), t, gg - 6.0, pan=-0.1, label="the chair pushed back", align=None)
        for j, (who, dt) in enumerate((("her", 0.12), ("cracker", 0.32), ("knight", 0.5))):
            for s in range(2):
                ts = t + dt + 0.5 * s
                m.put("feet", DC.footstep(who, 3 + j + s, "small_room", j), ts - STEP_PRE, gg - 3.0 - 1.5 * s,
                      pan=-0.2 - 0.1 * s)
    for t, d, c in cues_with(m, "door, closing", "door closing"):
        m.put("efx", roomed(m, soft_door(1), t), t, c["gain_db"] + CUE_TRIM, pan=c["pan"], label="the door, softly")


# ============================================================================ s04 NIGHT (48-62)
@section("s04")
def s04(m, S):
    T_HOOK = m.at("T_HOOK", 2.55, "iron tick", "hook")
    T_CHIME = m.at("T_CHIME", 4.0, "chime", "midnight")
    T_SHAFT = m.at("T_SHAFT", 5.0, "sink whoosh", "shaft")
    T_SECTION = m.at("T_SECTION", 7.0)
    L = m.len

    # the night street (no lamp click: it went out in s03; no siren: the police come later)
    for t, d, c in cues_with(m, "night air"):
        dd = d or 5.3
        x = night_bed(dd + 0.8, 41, lp=5000.0, wind=0.7)
        m.put("amb", env(x, [(0.0, 0.0), (0.6, 1.0), (dd, 1.0), (dd + 0.8, 0.0)]), t, c["gain_db"] + CUE_TRIM - 6.0,
              label="the night air", align=None)
    # his fingers hook the lid: an iron tick, his grunt (low, short)
    m.put("efx", roomed(m, DC.metal_tap(1), T_HOOK), T_HOOK, cgain(m, T_HOOK, "iron tick", default=-17.0),
          pan=cpan(m, T_HOOK, "iron tick"), label="an iron tick")
    grunt(m, T_HOOK + 0.06, cgain(m, T_HOOK, "iron tick", default=-17.0) - 9.0, 2, pan=cpan(m, T_HOOK, "iron tick"))
    # midnight: the bank's clock strikes once, a deep bell on D across the street
    x = dsp.reverb(OF.bell(hz(50), 3, tail=4.0), "street", wet_db=-6.0, seed=2)
    m.put("music", x, T_CHIME, cgain(m, T_CHIME, "chime", default=-11.0) - 4.0, pan=cpan(m, T_CHIME, "chime", default=0.3),
          label="midnight: one deep chime", hall=None)
    # the shaft: a faint tremolo high on the Psycho chord, a slow glide down to his C#
    d_s = max(0.5, T_SECTION - T_SHAFT)
    x = trem((74, 77, 81, 85), d_s + 0.3, 0.6, 4)
    m.put("music", env(x, [(0.0, 0.0), (0.8, 0.8), (d_s - 0.4, 1.0), (d_s + 0.3, 0.0)]), T_SHAFT, -29.0, align=None)
    m.put("music", bow([(0.0, 38), (d_s, HIS)], d_s, 0.8, 5, octaves=(0, 1), attack=0.6, release=0.6), T_SHAFT, -25.0)
    # the section: a low pulse as they wade (pizzicato D, a bar), hushed as they come up
    t = math.ceil((T_SECTION + 0.5) / BAR) * BAR
    while t < 11.0:
        m.put("music", pz(38, 0.6, int(t)), t, -24.0)
        t += BAR
    # the hall: its clock, the beat's tick; the hold in the corner keeps a floor (over the cut)
    bank_clock(m)
    stealth(m, 12.5, L + 0.35, 40, fin=1.0, fout=0.35)


# ============================================================================ s05 GUARD (62-80)
TIPTOE = (("high d", HER_P), ("low c", HIS), ("middle", MID))


def tiptoe_note(text, k):
    for w, p in TIPTOE:
        if w in text:
            return p if w != "middle" or k % 2 == 0 else 53
    return (HER_P, HIS, MID, 53)[k % 4]


@section("s05")
def s05(m, S):
    T_EDGE = m.at("T_EDGE", 3.0, "held breath", "breath held")
    T_BREATH = m.at("T_BREATH", 9.5, "wheez")
    T_CLANK = m.at("T_CLANK", 10.0, "clank", "stethoscope")
    T_SPIN = m.at("T_SPIN", 10.25, "coat swish", "spins round")
    T_EYES = m.at("", 11.45, "held breath: one low", "tremolo string note", "held note")
    T_STARTLE = m.at("T_STARTLE", 12.95, "yelp", "stumbles")
    T_SIGH = m.at("T_SIGH", 13.75, "sigh", "breathes out")
    q0, q1 = m.span("T_PUSH", (16.0, 18.0), "push", "rising whoosh")
    L = m.len

    bank_clock(m)
    # the hall at night: its room tone and the building's hum (on D)
    for t, d, c in cues_with(m, "hall tone", "room tone"):
        x = bed("room_tone", L - t, 51, lp=1800.0)
        hum = 0.25 * np.sin(2 * np.pi * hz(26) * tax(len(x))) + 0.1 * np.sin(2 * np.pi * hz(38) * tax(len(x)))
        x = x + dsp.fade(hum, 0.5, 0.5)[:, None]
        m.put("amb", x, t, c["gain_db"] + CUE_TRIM - 2.0, label="the hall at night", align=None)
        break
    stealth(m, 0.0, T_CLANK - 0.15, 41, fin=0.35, fout=0.7)          # the floor under the crossings: the CLANK breaks it
    # his belt creaks as the light swings, softly, every swing
    for t, d, c in cues_with(m, "belt"):
        k = 0
        while t + 2.0 * k < t + (d or 6.5) - 0.2:
            m.put("efx", roomed(m, DC.glove_creak(k % 3, 0.35), t + 2.0 * k), t + 2.0 * k,
                  c["gain_db"] + CUE_TRIM - 1.5 * (k % 2), pan=c["pan"], label="his belt creaks" if k == 0 else None,
                  align=None)
            k += 1
    breath(m, "held", T_EDGE - 0.1, cgain(m, T_EDGE, "breath", default=-24.0) - 2.0, pan=cpan(m, T_EDGE, "breath"),
           label="a breath held")
    m.mark(T_EDGE, "a breath held")
    # a tiptoe pizzicato per crossing: her D, his C#, the old man's A (the notes the cues name)
    for k, (t, d, c) in enumerate(cues_with(m, "tiptoe")):
        p = tiptoe_note(c["text"], k)
        m.put("music", pz(p, 0.8, 30 + k), t, c["gain_db"] + CUE_TRIM + 2.0, pan=c["pan"], label=f"tiptoe: {nm(p)}")
    # his heart, on the picture's rings (120 bpm, the scene's clock), rising, then easing
    for t, d, c in cues_with(m, "heartbeat"):
        dd = d or 3.4
        m.mark(t, "his heart (on its rings)")
        heart_rings(m, t, t + dd, 120.0, film=False, gain=c["gain_db"] + CUE_TRIM + 2.0, pan=c["pan"],
                    shape=lambda u: -8.0 + 10.0 * min(1.0, u / 0.55) - 9.0 * max(0.0, (u - 0.6) / 0.4))
    # the near miss: his wheeze held in; CLANK on the pipe, ringing down it; the guard spins round
    m.put("vox", roomed(m, wheeze(1), T_BREATH), T_BREATH, cgain(m, T_BREATH, "wheez", default=-20.0) - 2.0,
          pan=cpan(m, T_BREATH, "wheez", default=0.25), label="his wheeze", align=None, key=True)
    m.put("efx", roomed(m, DC.steth_clank(1), T_CLANK), T_CLANK, cgain(m, T_CLANK, "clank", default=-6.0) - 2.5,
          pan=cpan(m, T_CLANK, "clank"), label="CLANK on the pipe")
    m.put("efx", roomed(m, DC.ripple(1, 92.0, 1.3), T_CLANK), T_CLANK + 0.02, -14.0)
    m.put("efx", roomed(m, DC.cloth(0.45, 2, 1.0), T_SPIN), T_SPIN, cgain(m, T_SPIN, "swish", default=-15.0),
          pan=cpan(m, T_SPIN, "swish", default=0.44), label="he spins round", align=None)
    m.put("efx", fx("whip", seed=9), T_SPIN + 0.05, -22.0, pan=0.3, align=None)
    # the score holds its breath: one low tremolo under the cat's eyes (his C#), to the hiss
    d_e = max(0.4, m.at("T_ARCH", 12.0, "hiss") - T_EYES)
    m.put("music", env(trem((HIS, HIS + 12), d_e + 0.15, 0.8, 7), [(0.0, 0.3), (d_e, 1.0), (d_e + 0.15, 0.0)]),
          T_EYES, cgain(m, T_EYES, "tremolo", default=-20.0), label="one low tremolo note", align=None)
    # the cat; the can; he yelps without a voice (a scuff, a gasp); he breathes out
    m.put("feet", roomed(m, DC.heel_scuff(1, "guard"), T_STARTLE), T_STARTLE - STEP_PRE,
          cgain(m, T_STARTLE, "yelp", default=-14.0), pan=cpan(m, T_STARTLE, "yelp", default=0.5),
          label="the guard stumbles back (a scuff)", sync=T_STARTLE)
    breath(m, "gasp", T_STARTLE + 0.02, cgain(m, T_STARTLE, "yelp", default=-14.0) - 2.0, pan=0.5, semis=-4.0)
    breath(m, "out", T_SIGH, cgain(m, T_SIGH, "sigh", default=-16.0), pan=cpan(m, T_SIGH, "sigh", default=0.5),
           semis=-2.0, label="he breathes out")
    # the push to the dial: a low swell on the Psycho chord, into s06
    dq = max(0.5, q1 - q0)
    m.put("music", held((38, 50, 53, 61), dq, 0.7, 8, octaves=(0,), attack=dq * 0.9, release=0.2), q0, -20.0,
          align=None)


# ============================================================================ s06 SAFE (80-94)
@section("s06")
def s06(m, S):
    GATES = m.ats("GATES", (6.0, 7.5, 9.0), "gate click", n=3)
    T_FENCE = m.at("T_FENCE", 9.5, "fence", "clunk")
    s0, s1 = m.span("T_SWING", (11.1, 12.9), "hinge groan")
    sw0 = m.at("", 11.2, "string swell", "swell")
    L = m.len

    bank_clock(m)
    for t, d, c in cues_with(m, "vault tone", "hush"):
        x = bed("room_tone", L - t, 61, lp=1500.0)
        x = env(x, [(0.0, 1.0), (max(0.1, s0 - t), 1.0), (max(0.2, s0 - t + 1.0), 0.5), (len(x) / SR, 0.5)])
        m.put("amb", x, t, c["gain_db"] + CUE_TRIM, label="the hush at the vault door", align=None)
        break
    stealth(m, 0.0, T_FENCE - 0.05, 42, fin=0.5, fout=0.5)           # the floor under the dial: the CLUNK ends it
    # the dial: each gate's click (pitched D, F, A), a pizzicato answer on the off-beat; the fence:
    # the chord together
    for k, t in enumerate(GATES[:3]):
        c = m.cue_near(t, "gate", win=0.15)
        lvl = (c["gain_db"] if c else -9.0) + CUE_TRIM
        kk = 0 if c is None or "low" in c["text"] else 2 if "high" in c["text"] else 1 if "mid" in c["text"] else k
        m.put("efx", roomed(m, DC.gate_click(kk, k), t, wet=-18.0), t, lvl, label=f"gate click {('low', 'mid', 'high')[kk]}")
        m.put("music", pz((50, 53, 57)[kk], 0.6, 40 + k), t + BEAT / 2, -22.0, pan=0.15)
    m.put("efx", roomed(m, DC.fence_clunk(1), T_FENCE), T_FENCE, cgain(m, T_FENCE, "clunk", default=-5.0) - 2.5,
          label="CLUNK: the fence")
    for j, p in enumerate((38, 50, 53, 57, 61)):
        m.put("music", pz(p, 0.75, 50 + j), T_FENCE + 0.004 * j, -17.0, pan=-0.2 + 0.1 * j)
    # the swell: D minor, rising, as the gold's light floods out
    d_w = max(1.0, L - sw0)
    e = [(0.0, 0.25), (min(1.7, d_w * 0.6), 1.0), (d_w, 0.9)]
    m.put("music", held((38, 50, 57, 62, 65), d_w, 0.85, 60, octaves=(0, 1), attack=0.6, release=0.8, env_=e), sw0,
          cgain(m, sw0, "swell", default=-8.0) - 6.0, label="a string swell: D minor, rising", align=None)
    m.put("music", bow([(0.0, 69), (1.4, 74), (d_w, 77)], d_w, 0.6, 61, octaves=(0,), attack=1.2, release=0.8,
                       bright=7000.0), sw0 + 0.3, -20.0)
    # three looks go in, plucked: his C#, the old man's A, her D
    for k, (t, d, c) in enumerate(cues_with(m, "look goes in", "look note")):
        p = HIS if "c#" in c["text"] else MID if "middle" in c["text"] or "viola" in c["text"] else HER_P
        m.put("music", pz(p, 0.85, 70 + k), t, c["gain_db"] + CUE_TRIM, pan=c["pan"], label=f"a look: {nm(p)}")


# ============================================================================ s07 CROSS (94-114)
INV_BOOM = tuple(INVERSION[:-2]) + ((13, 3, 63), (16, 2, 62))       # its E-flat hangs; the last D lands on the BOOM
PROG_INV_B = ((4, (38, 45)), (4, (33, 40)), (4, (31, 38)), (4, (33, 39)))
INV_TREM_B = ((4, 53), (4, 48), (4, 46), (4, 48))


@section("s07")
def s07(m, S):
    """The betrayal. The music on the bible's beats (read from the module where it has them); the
    foley on its cues, the module's or (a stand-in) the bible's, which use the same words."""
    T_RUBY = m.at("T_RUBY", 1.5, "ruby close")
    T_POCKET = m.at("T_POCKET", 4.0, "pocket")
    T_LOOK = m.at("T_LOOK", 6.0, "his note", "his look")
    T_INV = m.at("T_INVERSION", 6.0, "theme inverted", "inversion")
    T_BOOM = m.at("T_BOOM", 14.0, "boom")
    T_RING = m.at("T_RING", 15.3, "marker squeak")
    r0, r1 = m.span("T_RUN", (15.5, 16.75))
    T_BANG = m.at("T_BANG", 17.0, "bang")
    q0, q1 = m.span("T_BELL_PUSH", (17.7, 20.0), "bell push")
    L = m.len

    def each(*words):            # the cues whose lead words (the tag) say it
        return [(t, d, c) for t, d, c in cues_with(m, *words) if any(w in head(c) for w in words)]

    def cg(c, extra=0.0):
        return c["gain_db"] + CUE_TRIM + extra

    # ---- the music
    # the gold's warmth (B-flat major 7, D minor's sixth) until the ruby; it comes back with a soft
    # pizzicato and turns to A7 on the half bar before his look
    m.put("music", held((34, 50, 53, 57, 62), T_RUBY + 0.2, 0.7, 1, octaves=(0, 1), attack=0.4, release=0.7), 0.0,
          -22.0, label="the gold (B-flat major)", align=None)
    m.put("music", held((34, 50, 53, 57), 1.0, 0.6, 2, octaves=(0, 1), attack=0.3, release=0.4), T_POCKET, -23.0,
          align=None)
    m.put("music", held((33, 49, 52, 55), max(0.5, T_LOOK - T_POCKET - 1.0), 0.6, 3, octaves=(0, 1), attack=0.25,
                        release=0.35), T_POCKET + 1.0, -23.0, align=None)
    ostinato(m, T_POCKET, T_LOOK, notes=lambda t: (46, 50, 53, 57) if t < T_POCKET + 1.0 else (45, 49, 52, 55),
             step=E8, vel=(0.3, 0.6), accent=(0, 3), gain=-22.0, seed=9, spread=(0,))
    # the ruby, close: the score drops to a held low D
    for t, d, c in each("ruby close") or [(T_RUBY, 0.0, None)]:
        m.put("music", bow([(0.0, 38)], T_POCKET - t + 0.5, 0.75, 2, octaves=(0, 1), attack=0.35, release=1.0), t,
              -19.0, label="the ruby: a held low D", align=None)
    for t, d, c in each("ruby glint"):          # a faint high ting: the harp's top (not the celesta)
        m.put("music", hp(98, 0.5, 3), t, cg(c, -1.0), pan=c["pan"], label="a red glint: a high harp ting", hall=-10.0)
    for t, d, c in each("string harmonic"):     # she lifts it: a harmonic rising
        dl = max(0.3, d or 0.6)
        m.put("music", harm(86, dl + 0.4, 0.8, 3, attack=0.12, release=0.8,
                            bend=lambda u, dl=dl: 7.0 * np.clip(u / dl, 0, 1)), t, cg(c, 5.0), pan=c["pan"],
              label="she lifts it: a harmonic rising", align=None)
    for t, d, c in each("ruby shimmer"):        # it flares: a glassy string shimmer
        m.put("music", shimmer(1.1, 4, 98), t, cg(c, 2.0), pan=c["pan"], label="it flares: a glassy shimmer", align=None)
    # 6.0 HIS LOOK: his C#, a cello pedal; THE INVERSION, low and dark (cellos, the basses an octave
    # under), its E-flat hanging over the last bar and its D landing on the BOOM
    for t, d, c in each("his note") or [(T_LOOK, 3.0, {"gain_db": -14.0, "pan": 0.2})]:
        m.put("music", bow([(0.0, HIS)], d or 3.0, 0.9, 5, octaves=(0, 1), attack=0.45, release=1.0), t, cg(c, -2.0),
              pan=c["pan"], label="his look: his C#, a cello pedal", align=None)
    gi = next((cg(c) for t, d, c in each("theme inverted")), -14.0)
    bowed_tune(m, T_INV, INV_BOOM, gi - 1.0, pan=-0.1, vel=0.85, octave=-1, seed=6, label="THE INVERSION (cellos, basses)",
               octaves=(0, -1), bright=2600.0, attack=0.12, release=0.9, hold=1.3)
    pad(m, T_INV, PROG_INV_B, gi - 9.0, seed=7, octaves=(0,), attack=0.6, bright=1800.0)
    for i, (b, nb, p) in enumerate(chords_in(tuple((nb, (p,)) for nb, p in INV_TREM_B))):
        m.put("music", trem(p, nb * BEAT + 0.05, 0.5, 8 + i), T_INV + b * BEAT, gi - 13.0, pan=0.3, align=None)
    for k, (t, d, c) in enumerate(each("look tick")):     # each look: a dry tick, a plucked low C#
        m.put("efx", OF.tick(k), t, cg(c, -3.0), pan=c["pan"], label="his look: a dry tick")
        m.put("music", pz(HIS + 12, 0.8, 50 + k), t, cg(c, 5.0), pan=0.5 * c["pan"])
        m.put("music", pz(HIS, 0.7, 60 + k), t, cg(c, 3.0), pan=0.5 * c["pan"])
    # the POV (the last bar): A half-diminished pressing, her D against an E-flat over it, louder
    # and louder into the slot of gold; the BOOM, the low stab, the inversion's D left ringing
    t_p = T_INV + 12 * BEAT
    dp = max(0.5, T_BOOM - t_p)
    m.put("music", held((45, 48, 51, 55), dp + 0.05, 0.75, 9, octaves=(0, 1), attack=0.3, release=0.05,
                        env_=[(0.0, 0.35), (dp, 1.0)]), t_p, gi - 5.0, align=None, fades=False)
    m.put("music", env(trem((74, 75), dp + 0.05, 0.6, 10), [(0.0, 0.15), (dp - 0.02, 1.0), (dp + 0.05, 0.0)]), t_p,
          gi - 9.0, pan=0.2, align=None, fades=False)
    m.put("music", stab(PSY, 2, low=True), T_BOOM, -11.0, label="BOOM: a low stab")
    m.put("music", bow([(0.0, 26)], 1.4, 0.8, 11, octaves=(0, 1), attack=0.01, release=1.2), T_BOOM, -18.0, align=None)
    # the section: the ring's low stab; an ostinato under his run, sixteenths, into the BANG
    for t, d, c in each("low stab"):
        m.put("music", stab(PSY, 3, low=True), t, cg(c, 1.0), label="the ring: a low stab")
    ostinato(m, r0 - 0.25, T_BANG, notes=tuple(p - 12 for p in PSY), step=E16, vel=(0.45, 1.0), accent=(0, 4, 8, 12),
             gain=-16.0, seed=10, label="his run: the ostinato")
    # 17.0 BANG: the bell, loud, swelling on every beat; the strings' tremolo on the Psycho chord
    # under it, rising as the camera pushes in; cut dead at the cut
    m.put("music", stab(PSY, 4), T_BANG, -12.0)
    db = L - T_BANG
    m.put("music", env(trem(PSY, db + 0.05, 0.7, 11), [(0.0, 0.45), (db - 0.03, 1.0), (db, 0.0)]), T_BANG, -19.0,
          align=None, fades=False)
    m.put("music", env(bow([(0.0, 26)], db + 0.05, 0.8, 12, octaves=(0, 1), attack=0.05, release=0.05),
                       [(0.0, 0.8), (db - 0.03, 1.0), (db, 0.0)]), T_BANG, -17.0, align=None, fades=False)

    # ---- the rooms: the vault's hush (cut by the BOOM), the hall in the section
    m.put("amb", env(bed("room_tone", T_BOOM + 0.1, 8, lp=1500.0), [(0.0, 1.0), (T_BOOM - 0.02, 1.0), (T_BOOM, 0.0)]),
          0.0, -40.0, align=None, fades=False)
    m.put("amb", bed("room_tone", T_BANG - 15.0 + 0.1, 9, lp=1800.0), 15.0, -38.0, align=None)
    # ---- the foley, cue by cue
    for k, (t, d, c) in enumerate(each("gold clink", "gold drop")):
        drop = "drop" in c["sfx"]
        close = T_RUBY - 0.05 <= t < T_POCKET
        x = DC.gold_bag(k % 5) if drop else DC.gold_clink(k % 5, 0.4 if close else 0.0)
        m.put("efx", roomed(m, far(x, 1300.0) if close else x, t, k), t, cg(c), pan=c["pan"],
              label="a bar into the sack" if drop else "a bar off the stack")
    for t, d, c in each("box open"):
        m.put("efx", roomed(m, DC.deposit_box(1), t), t, cg(c, 3.0), pan=c["pan"], label="her box opens")
    for k, (t, d, c) in enumerate(each("glove creak", "knob creak", "collar creak")):
        x = DC.glove_creak(k % 3, 0.3 if "collar" in c["sfx"] else 0.4)
        m.put("efx", roomed(m, x, t, k), t, cg(c, 3.0), pan=c["pan"], label="leather creaks", align=None)
    for t, d, c in each("ruby tick"):
        m.put("efx", dsp.sos(DC.finger_tap(2, 0.3), "lowpass", 3500.0, 2), t, cg(c, 2.0), pan=c["pan"],
              label="a tiny tick of stone on leather")
    for k, (t, d, c) in enumerate(each("cloth swish", "inside swish", "pocket rustle", "knee up")):
        s, inside = c["sfx"], "inside" in c["sfx"]
        x = (OF.rustle(0.45, 3 + k) if "rustle" in s else DC.cloth(0.5 if "knee" in s else 0.3, k % 5, 1.0 if inside else 0.3))
        if inside:
            x = far(x, 900.0)
        m.put("efx", roomed(m, x, t, k), t, cg(c, 3.0), pan=c["pan"], label="cloth", align=None)
        if "knee" in s:
            m.put("efx", roomed(m, far(OF.creak(0.3, 4), 2500.0), t + 0.12), t + 0.12, cg(c, -3.0), pan=c["pan"])
    for k, (t, d, c) in enumerate(each("crew step", "knight step", "lunge step", "step back", "inside step")):
        s = c["sfx"]
        inside = "inside" in s
        who = "cracker" if inside or "crew" in s else "knight"
        x = DC.steel_step(who, k, room(m, t)[0], k)
        m.put("feet", far(x, 700.0) if inside else x, t - STEP_PRE, cg(c, 2.0 if "lunge" in s else 0.0), pan=c["pan"],
              label=f"a step on steel ({who})", sync=t)
        if "bags" in c["text"]:
            m.put("efx", roomed(m, DC.gold_clink(40 + k, 0.6), t + 0.05), t + 0.05, cg(c, -9.0), pan=c["pan"])
    for t, d, c in each("sack cinch"):
        dd = max(0.2, d or 0.4)
        m.put("efx", roomed(m, DC.cloth(round(dd, 2), 4, 1.0), t), t, cg(c, 2.0), pan=c["pan"],
              label="the sack's neck pulled shut", align=None)
        m.put("efx", roomed(m, far(pitch(OF.zip_(0.22, 2), -9.0), 2500.0), t + 0.05), t + 0.05, cg(c, -6.0), pan=c["pan"])
        m.put("efx", roomed(m, DC.gold_clink(7, 0.7), t + 0.15), t + 0.15, cg(c, -6.0), pan=c["pan"])
    for t, d, c in each("knight breath"):
        breath(m, "out", t, cg(c, 3.0), pan=c["pan"], label="he straightens: a slow breath out", semis=-1.0)
    for t, d, c in each("grunt"):
        cutp = (c.get("params") or {}).get("cut")
        k = 1 if ((isinstance(cutp, (tuple, list)) and len(cutp) and float(cutp[0]) < 1.0)
                  or "weight" in c["text"] or "held" in c["text"]) else 0
        grunt(m, t, cg(c, -2.0), k, pan=c["pan"], label="his grunt" + (", held" if k == 1 else ""))
        if "bags" in c["text"] or "sacks" in c["text"] or "gold" in c["text"]:
            for j in range(3):
                m.put("efx", roomed(m, DC.gold_clink(10 + j, 0.8), t + 0.06 + 0.07 * j), t + 0.06 + 0.07 * j,
                      cg(c, -8.0 - 2.0 * j), pan=c["pan"])
    for k, (t, d, c) in enumerate(each("heel scuff")):
        m.put("feet", roomed(m, DC.heel_scuff(k % 4, "knight"), t), t - STEP_PRE, cg(c, 1.0), pan=c["pan"],
              label="he turns on his heel", sync=t)
    for t, d, c in each("glove slap"):
        m.put("efx", roomed(m, OF.slap(2), t), t, cg(c, 1.0), pan=c["pan"], label="his palms slap the door's edge")
        m.put("efx", roomed(m, pitch(DC.metal_tap(1), -7.0), t + 0.005), t + 0.005, cg(c, -6.0), pan=c["pan"])
    for t, d, c in each("hinge groan"):
        dd = round(max(0.6, d or 2.4), 2)
        m.put("efx", roomed(m, DC.vault_groan(dd, 2), t), t, cg(c), pan=c["pan"], label="the great door's hinge groans",
              align=None)
    for t, d, c in each("inside gasp"):
        x = far(mono(DC.breath("gasp")), 900.0)
        m.put("vox", roomed(m, x, t), t, cg(c, 2.0), pan=c["pan"], label="inside: his gasp (muffled)", align=None,
              key=True)
    for t, d, c in each("boom") or [(T_BOOM, 0.0, {"gain_db": -2.0, "pan": 0.0})]:
        # its sub-bass (half its energy under 40 Hz, inaudible on most speakers) only drives the limiter
        m.put("efx", dsp.sos(DC.vault_boom(1), "highpass", 42.0, 2), t, cg(c, -5.0), pan=c["pan"],
              label="BOOM: the door shut")
    for k, (t, d, c) in enumerate(each("bolt clack")):
        m.put("efx", roomed(m, DC.bolt_one(k % 12), t), t - DC.BOLT_PRE, cg(c, -1.0), pan=c["pan"],
              label="a bolt shoots home", sync=t, align="peak")
    for t, d, c in each("clank"):
        m.put("efx", roomed(m, DC.fence_clunk(1), t), t, cg(c, -7.0), pan=c["pan"], label="CLANK: the lock's bolt home")
        m.put("efx", roomed(m, DC.bolt_one(5), t), t - DC.BOLT_PRE, cg(c, -8.0), pan=c["pan"])
    for t, d, c in each("dial spin"):
        dd = round(max(0.3, d or 0.5), 2)
        m.put("efx", roomed(m, DC.dial_spin(dd, 2, 40.0, 14.0), t), t, cg(c, 1.0), pan=c["pan"],
              label="the red dial spun", align=None)
    for t, d, c in each("marker squeak"):
        m.put("efx", roomed(m, OF.squeak(round(max(0.2, d or 0.4), 2), 5), t), t, cg(c), pan=c["pan"],
              label="the second ring: the squeak", align=None)
    for k, (t, d, c) in enumerate(each("run step")):
        rm = room(m, t)[0]
        m.put("feet", DC.footstep("knight", k, rm, k % 5), t - STEP_PRE, cg(c, 1.0), pan=c["pan"], label="his run",
              sync=t)
    for k, (t, d, c) in enumerate(each("bags swing")):
        dd = max(0.4, d or 1.0)
        for j, dt in enumerate(np.arange(0.0, dd, 0.27)):
            m.put("efx", roomed(m, DC.gold_clink(60 + 7 * k + j, 0.6), t + dt), t + dt, cg(c, -1.5 * (j % 2)),
                  pan=c["pan"], label="the bags swing, the gold clinking" if j == 0 else None)
    for t, d, c in each("bang") or [(T_BANG, 0.0, {"gain_db": -4.0, "pan": 0.05})]:
        m.put("efx", fx("impact", seed=12), t, cg(c, -5.0), pan=c["pan"], label="BANG: the side door")
        m.put("efx", roomed(m, DC.door_thud(1), t), t, cg(c, -6.0), pan=c["pan"])
    bell = next(((t, d, c) for t, d, c in each("alarm bell")), (T_BANG, L - T_BANG, {"gain_db": -6.0, "pan": 0.05}))
    t, d, c = bell
    db = max(0.5, L - t)
    pu = max(0.1, q0 - t)
    x = alarm(db + 0.05, t, 1, depth=0.35)
    x = dsp.reverb(x, "street", wet_db=-10.0, seed=3)[: n_of(db + 0.05)]
    x = env(x, [(0.0, 0.78), (pu, 0.8), (db - 0.03, 1.0), (db, 0.0)])
    m.put("efx", x, t, cg(c, -4.0), pan=c["pan"], label="the alarm bell, loud", align=None, fades=False)
    m.mark(q0, "the push in on the bell (the bell nearer)")


# ============================================================================ s08 LOCKED (114-128)
@section("s08")
def s08(m, S):
    T_SCRATCH = m.at("T_SCRATCH", 1.2, "scratches")
    T_STRIKE = m.at("T_STRIKE", 1.6, "flares")
    T_PANIC = m.at("T_PANIC", 2.0, "heartbeat")
    T_LEVEL = m.at("T_LEVEL", 6.0, "far off", "alarm bell")
    T_BLOWS = m.ats("T_BLOWS", (3.5, 4.0, 4.5), "boom", n=3)
    T_SMILE = m.at("T_SMILE", 6.9, "laugh")
    T_EYE = m.at("T_EYE", 7.25, "low held note")
    T_DIVE = m.at("T_DIVE", 8.0, "rising whoosh", "into her eye")
    T_SET = m.at("T_SET", 11.2, "set back", "settling")
    T_EYE_OUT = m.at("T_EYE_OUT", 11.75, "reverse whoosh", "out of her eye")
    T_BACK = m.at("T_BACK", 12.0, "the vault: the bell")
    T_TAP = m.at("T_TAP", 12.4, "heel taps", "click")
    T_KNOCK = m.at("T_KNOCK", 12.75, "hollow knock")
    T_TURN = m.at("T_TURN", 13.25, "intake")
    cuts = g(S, "T_CUTS", ((9.0, 9.6), (9.75, 10.35)))
    p0, p1 = m.span("T_PUSH", (10.5, 10.9), "stone grinding")
    L = m.len

    # black: his ragged breath; the match scratched, it flares; its flame breathes on (match light)
    for t, d, c in cues_with(m, "ragged"):
        x = DC.ragged(round(max(0.5, d or 1.6), 2), 1)
        m.put("vox", roomed(m, x, t), t, c["gain_db"] + CUE_TRIM - 2.0, label="his ragged breath", align=None, key=True)
    x = DC.match_scratch(1)
    m.put("efx", roomed(m, x, T_SCRATCH), T_SCRATCH - onset_at(x), cgain(m, T_SCRATCH, "scratch", default=-8.0) - 2.0,
          pan=0.3, label="the match scratches", sync=T_SCRATCH)
    st = fx("match_flare", seed=2)
    m.put("efx", roomed(m, st, T_STRIKE), T_STRIKE - onset_at(st), cgain(m, T_STRIKE, "flare", default=-8.0), pan=0.3,
          label="the match flares", sync=T_STRIKE)
    for t, d, c in cues_with(m, "flame's soft breath", "flame"):
        m.put("amb", DC.flame_bed(1.2, 1), t, c["gain_db"] + CUE_TRIM - 2.0, pan=0.3, label="the flame's breath",
              align=None)
        break
    m.put("amb", env(DC.flame_bed(round(T_DIVE - T_STRIKE, 2), 2), [(0.0, 0.0), (0.4, 1.0), (T_DIVE - T_STRIKE, 0.0)]),
          T_STRIKE + 0.3, -36.0, pan=0.3)
    # the panic: his heart on the picture's rings (150 bpm, the film's clock); a high string rising
    # (the Dutch tilt), his C# a semitone under her D up there
    for t, d, c in cues_with(m, "heartbeat"):
        heart_rings(m, t, t + (d or 4.0), 150.0, film=True, gain=c["gain_db"] + CUE_TRIM - 7.0,
                    shape=lambda u: -3.0 + 3.0 * min(1.0, u / 0.4))
        m.mark(t, "his heart")
        break
    for t, d, c in cues_with(m, "high held string"):
        dd = d or 4.0
        m.put("music", harm(HER, dd, 0.8, 4, attack=0.6, release=0.8, bend=lambda u, dd=dd: 4.0 * np.clip(u / dd, 0, 1)),
              t, c["gain_db"] + CUE_TRIM - 6.0, pan=0.15, label="a high string, rising", align=None)
        m.put("music", harm(HER + 1, dd, 0.5, 5, attack=1.4, release=0.8, bend=lambda u, dd=dd: 4.0 * np.clip(u / dd, 0, 1)),
              t + 0.5, c["gain_db"] + CUE_TRIM - 12.0, pan=-0.15)
    # his fists: three muffled BOOMs; he sags (a breath, his coat on the steel)
    for k, t in enumerate(T_BLOWS[:3]):
        m.put("efx", DC.pound(k), t, cgain(m, t, "boom", default=-4.0) - 7.0, pan=cpan(m, t, "boom", default=-0.4),
              label="a fist on the door: BOOM")
    ts = m.at("", 5.0, "sags")
    breath(m, "out", ts, cgain(m, ts, "sags", default=-16.0), pan=-0.4, semis=-2.0, label="he sags")
    m.put("efx", roomed(m, DC.cloth(0.6, 4, 1.0), ts + 0.05), ts + 0.05, -20.0, pan=-0.4)
    # far off, the bell; her eye; her breath of a laugh; a low note for her calm
    for t, d, c in cues_with(m, "alarm bell", "the bell faint"):
        dd = d or 2.0
        x = far(alarm(dd + 0.3, t, 2 + int(t), 0.25), 750.0)
        x = env(x, [(0.0, 0.0), (0.5, 1.0), (dd - 0.2, 1.0), (dd + 0.3, 0.0)])
        m.put("amb", dsp.reverb(x, "cell", wet_db=-6.0, seed=1), t, c["gain_db"] + CUE_TRIM - 3.0, pan=c["pan"],
              label="the bell, far off through the walls", align=None)
    laugh(m, T_SMILE, cgain(m, T_SMILE, "laugh", default=-10.0) - 8.0, pan=-0.1, label="her breath of a laugh")
    d_e = (m.cue_near(T_EYE, "held", win=0.2) or {}).get("dur") or 0.75
    m.put("music", bow([(0.0, 38)], d_e + 0.3, 0.8, 6, octaves=(0, 1), attack=0.2, release=0.8), T_EYE,
          cgain(m, T_EYE, "held", default=-16.0) - 3.0, label="a low held note: her calm", align=None)
    m.put("music", harm(81, d_e + 0.3, 0.5, 7, attack=0.3, release=0.8), T_EYE + 0.1, -26.0, pan=-0.2)
    # 8.0 the dive into her eye: a deep rising whoosh; THE THEME upright (the inversion turned
    # upright again), plucked, through the night before, its last D on s09's 1.0
    dd = (m.cue_near(T_DIVE, "whoosh", win=0.2) or {}).get("dur") or 0.5
    x = pitch(DC.rise_whoosh(round(dd + 0.4, 2), 1), -5.0)
    m.put("efx", x, T_DIVE - 0.1, cgain(m, T_DIVE, "whoosh", default=-8.0) - 2.0, label="into her eye: a deep whoosh",
          sync=T_DIVE, align=None)
    t_u = T_DIVE
    pluck_line(m, t_u, UPRIGHT, "harp", -14.0, pan=-0.15, vel=0.8, octave=1, seed=80, stop=14,
               label="THE THEME upright (harp)", t_max=L)
    pad(m, t_u, PROG, -27.0, seed=81, stop=14, octaves=(1,), attack=0.8, bright=6000.0)
    for i, (b, nb, ch) in enumerate(chords_in(PROG, 0, 14)):
        if t_u + b * BEAT < L:
            m.put("music", pz(ch[0] if ch[0] >= 36 else ch[0] + 12, 0.7, 82 + i), t_u + b * BEAT, -19.0, pan=0.05)
    # the night before: drips in the shaft; the torch lit (a pop, its hiss), its two cuts roaring;
    # the block lifted a crack (stone grinding, a shimmer on the gold), set back (a soft knock)
    for t, d, c in cues_with(m, "drips in a hollow shaft", "drips"):
        dd = d or 3.25
        for k, dt in enumerate(np.arange(0.0, dd, 0.62)):
            m.put("amb", DC.far_drip(k % 4) if k % 2 else DC.drip(k % 5), t + dt + 0.07 * (k % 3),
                  c["gain_db"] + CUE_TRIM - 4.0 - 2.0 * (k % 2), pan=(-0.3, 0.2, 0.4)[k % 3],
                  label="drips in the shaft" if k == 0 else None)
        break
    tp = m.at("", 8.7, "torch lights", "pop and a hiss")
    m.put("efx", roomed(m, torch_pop(1), tp), tp, cgain(m, tp, "torch", default=-12.0), pan=0.1, label="the torch lights")
    for k, (a, b) in enumerate(cuts[:2]):
        x = DC.torch_cut(round(max(0.3, b - a), 2), k)
        m.put("efx", roomed(m, x, a), a, cgain(m, a, "torch", default=-9.0) - 2.0, pan=0.1 + 0.05 * k,
              label="the torch cuts", align=None)
    m.put("efx", roomed(m, DC.tile_scrape(3), p0), p0, cgain(m, p0, "stone", default=-12.0), label="stone grinding",
          align=None)
    m.put("music", shimmer(0.8, 5, 93), p0 + 0.15, -22.0, pan=0.2)
    m.put("efx", roomed(m, DC.tile_set(2), T_SET), T_SET, cgain(m, T_SET, "set back", default=-12.0),
          label="the block set back")
    m.put("efx", roomed(m, dsp.sos(DC.wood_thunk(2, 0.7), "lowpass", 900.0, 2), T_SET + 0.05), T_SET + 0.05, -20.0)
    de = (m.cue_near(T_EYE_OUT, "reverse", win=0.2) or {}).get("dur") or 0.25
    x = DC.rise_whoosh(round(de + 0.35, 2), 2)[::-1]
    m.put("efx", x, T_EYE_OUT - 0.1, cgain(m, T_EYE_OUT, "reverse", default=-10.0) - 3.0,
          label="out of her eye: a reverse whoosh", sync=T_EYE_OUT, align=None)
    # back in the vault: the match's breath; her heel: a click, then the HOLLOW knock; his intake
    m.put("amb", env(DC.flame_bed(round(L - T_BACK, 2), 3), [(0.0, 0.0), (0.3, 1.0), (L - T_BACK - 0.3, 1.0),
                                                             (L - T_BACK, 0.0)]), T_BACK, -34.0, pan=0.3)
    m.put("efx", roomed(m, DC.heel_tap(1), T_TAP), T_TAP, cgain(m, T_TAP, "click", default=-10.0) - 1.0,
          pan=cpan(m, T_TAP, "click", default=0.2), label="her heel: a click")
    m.put("efx", DC.hollow_knock(1), T_KNOCK, cgain(m, T_KNOCK, "knock", default=-4.0) - 3.0,
          pan=cpan(m, T_KNOCK, "knock", default=0.2), label="a HOLLOW knock")
    m.put("efx", DC.ripple(2, 62.0, 1.4), T_KNOCK + 0.03, -12.0)
    breath(m, "in", T_TURN - 0.25, cgain(m, T_TURN, "intake", default=-14.0), pan=-0.3, label="his sharp intake")
    m.mark(T_TURN, "his sharp intake")


# ============================================================================ s09 PLAN B (128-146)
@section("s09")
def s09(m, S):
    T_LIFT = m.at("T_LIFT", 0.2, "grinds up", "gloves on stone")
    T_SETDOWN = m.at("", 0.85, "set down")
    T_AIR = m.at("", 0.9, "cold air")
    T_GLINT = m.at("T_GLINT", 2.05, "glassy tick")
    T_GRIN = m.at("T_GRIN", 2.4, "chuckle")
    T_WIDE = m.at("T_WIDE", 7.0, "ostinato", "alarm bell")
    T_FLING = m.at("T_FLING", 7.3, "sacks thump")
    T_SLAM = m.at("T_SLAM", 7.6, "door slams")
    T_COUGHS = m.ats("T_COUGHS", (8.0, 8.5, 9.1, 9.7), "coughs", n=4)
    wake = g(S, "T_WAKE", {5: 9.5, 3: 10.0, 2: 10.5, 1: 11.0})
    T_WAKE = tuple(sorted(float(v) for v in wake.values())) if isinstance(wake, dict) else (9.5, 10.0, 10.5, 11.0)
    o0, o1 = m.span("T_OUT", (10.2, 10.45), "flung open")
    T_LOOKS = m.ats("T_LOOKS", (10.45, 10.8, 11.05), "grating", n=3)
    T_KICK = m.at("T_KICK", 11.3, "kicks the tyre")
    T_CITY = m.at("T_CITY", 11.5, "far city", "shimmer of strings")
    T_BACK_IN = m.at("T_BACK_IN", 11.6, "off the grating")
    T_SLAM2 = m.at("T_SLAM2", 11.9, "slams again")
    T_CATCH = m.at("T_CATCH", 12.0, "engine catches")
    T_DOUSE = m.at("T_DOUSE", 14.95, "shaken out")
    T_SWEEP = m.at("T_SWEEP", 16.0, "siren")
    L = m.len

    def street(x, wet=-8.0, seed=0, lp=None):
        x = x if lp is None else far(x, lp)
        return dsp.reverb(x if np.ndim(x) == 2 else mono(x), "street", wet_db=wet, seed=seed)

    # the vault by match light: the bell far off, the flame's breath
    for t, d, c in cues_with(m, "by match light"):
        dd = d or 2.0
        x = far(alarm(dd + 0.6, t, 9, 0.25), 750.0)
        m.put("amb", env(dsp.reverb(x, "cell", wet_db=-6.0, seed=2), [(0.0, 1.0), (dd, 1.0), (dd + 0.6, 0.0)]), t,
              c["gain_db"] + CUE_TRIM - 4.0, pan=-0.5, label="the bell far off; the match's breath", align=None)
        break
    m.put("amb", env(DC.flame_bed(round(T_DOUSE + 0.05, 2), 4), [(0.0, 1.0), (T_DOUSE, 1.0), (T_DOUSE + 0.05, 0.0)]),
          0.0, -36.0, pan=0.2)
    # THE THEME upright lands on D (beat 14 of s08's statement)
    t_u = -6.0
    pluck_line(m, t_u, UPRIGHT, "harp", -14.0, pan=-0.15, vel=0.8, octave=1, seed=80, start=12, stop=16,
               label="THE THEME upright lands", t_min=0.0)
    pad(m, t_u, PROG, -27.0, seed=81, start=14, octaves=(1,), attack=0.5, bright=6000.0)
    m.put("music", pz(38, 0.7, 90), t_u + 14 * BEAT, -19.0, pan=0.05)
    # the block: gloves on stone, it grinds up; set down; cold air up the shaft
    m.put("efx", roomed(m, DC.tile_scrape(4), T_LIFT), T_LIFT, cgain(m, T_LIFT, "grinds", default=-10.0) - 2.0,
          label="the block grinds up", align=None)
    m.put("efx", roomed(m, DC.glove_creak(1, 0.3), T_LIFT), T_LIFT, -22.0)
    m.put("efx", roomed(m, DC.tile_set(4), T_SETDOWN), T_SETDOWN, cgain(m, T_SETDOWN, "set down", default=-10.0),
          pan=-0.4, label="the block set down")
    m.put("efx", roomed(m, dsp.sos(DC.wood_thunk(1, 1.0), "lowpass", 600.0, 2), T_SETDOWN), T_SETDOWN, -14.0, pan=-0.4)
    da = (m.cue_near(T_AIR, "cold air", win=0.2) or {}).get("dur") or 1.1
    x = bed("wind_gust", da + 0.5, 3, lp=420.0)
    m.put("amb", dsp.reverb(x, "cell", wet_db=-6.0, seed=3), T_AIR, cgain(m, T_AIR, "cold air", default=-16.0) + 2.0,
          label="a breath of cold air up the shaft", align=None)
    m.put("amb", DC.far_drip(2), T_AIR + 0.4, -26.0, pan=0.3)
    # his face by the match: a glassy tick across his spectacles; his dry chuckle (breath only)
    m.put("efx", OF.glass_tick(2), T_GLINT, cgain(m, T_GLINT, "glassy", default=-14.0) - 2.0, pan=0.1,
          label="a glassy tick")
    m.put("vox", roomed(m, chuckle_breath(1), T_GRIN), T_GRIN, cgain(m, T_GRIN, "chuckle", default=-12.0) - 2.0,
          pan=0.1, label="his dry chuckle (breath only)", align=None, key=True)
    # down the shaft: the slides, the splashes; drips, the water lapping; their wading steps
    for t, d, c in cues_with(m, "the shaft: echoing", "lapping"):
        dd = d or 4.0
        m.put("amb", DC.sewer_bed(round(dd + 0.5, 2), 2), t, c["gain_db"] + CUE_TRIM - 6.0,
              label="the shaft: drips, lapping", align=None)
        for k, dt in enumerate((0.3, 1.25, 2.1, 3.2)):
            if dt < dd:
                m.put("amb", DC.drip(k + 1), t + dt, c["gain_db"] + CUE_TRIM - 4.0, pan=(-0.4, 0.3, -0.1, 0.5)[k])
        break
    for k, (t, d, c) in enumerate(cues_with(m, "slide", "squeal down", "squeak")):
        heavy = 0.8 if "slower" in c["text"] or "his" in c["text"] else 0.4
        m.put("efx", roomed(m, DC.ladder_slide(round(max(0.3, d or 1.0), 2), k, heavy), t), t,
              c["gain_db"] + CUE_TRIM - 1.5, pan=c["pan"], label="a slide down the rails", align=None)
    for k, (t, d, c) in enumerate(cues_with(m, "splash")):
        m.put("efx", DC.splash_drop(k), t, c["gain_db"] + CUE_TRIM - 2.0, pan=c["pan"], label="a splash")
        if "heavier" in c["text"]:
            m.put("efx", roomed(m, sfx._thump(n_of(0.3), 110.0, 55.0, 0.012, 0.12), t), t, -14.0, pan=c["pan"])
    for t, d, c in cues_with(m, "top rung"):
        m.put("efx", roomed(m, DC.rung(2), t), t, c["gain_db"] + CUE_TRIM, pan=c["pan"], label="his shoe on the rung")
    for k, (t, d, c) in enumerate(cues_with(m, "wading step", "slosh")):
        m.put("feet", DC.water_step((k * 3) % 8, (0.5, 0.65, 0.55)[k % 3]), t, c["gain_db"] + CUE_TRIM - 1.0,
              pan=c["pan"], label="a wading step")
    # 7.0 THE STREET: the bell rolls out over it (loud, a swell on every beat); the Herrmann
    # ostinato drives the race, her D6 high against his C#2 low; it drops to the pedals for the near
    # miss and comes back as the engine catches, the theme's head on the violins over it
    bc = m.cue_near(T_WIDE, "alarm bell", win=0.2)
    db = (bc or {}).get("dur") or 11.0
    db = min(db, L - T_WIDE + 0.5)
    x = street(alarm(db, T_WIDE, 5, 0.35), -10.0, 4)[: n_of(db)]
    m.put("efx", env(x, [(0.0, 0.0), (0.04, 1.0), (db - 0.6, 1.0), (db, 0.6)]), T_WIDE,
          (bc["gain_db"] if bc else -6.0) + CUE_TRIM - 6.0, pan=(bc or {}).get("pan", 0.3),
          label="the street: the alarm bell", align=None)
    oc = m.cue_near(T_WIDE, "ostinato", win=0.2)
    d_o = (oc or {}).get("dur") or 9.0
    o_end = T_WIDE + d_o
    g_o = ((oc or {}).get("gain_db", -10.0)) + CUE_TRIM - 4.0
    m.mark(T_WIDE, "the ostinato for the race")
    ostinato(m, T_WIDE, o0, notes=PSY, step=E8, vel=(0.55, 0.85), accent=(0, 3), gain=g_o, seed=20)
    ostinato(m, T_CATCH, o_end, notes=PSY, step=E8, vel=(0.75, 1.0), accent=(0, 3), gain=g_o + 1.0, seed=24)
    m.put("music", harm(HER, o_end - T_WIDE, 0.7, 21, attack=0.8, release=1.0), T_WIDE, g_o - 9.0, pan=-0.3)
    m.put("music", bow([(0.0, HIS)], o_end - T_WIDE, 0.85, 22, octaves=(0, 1), attack=0.6, release=1.0,
                       env=[(0.0, 0.8), (o0 - T_WIDE, 1.0), (T_CATCH - T_WIDE, 1.15), (o_end - T_WIDE, 1.0)]), T_WIDE,
          g_o - 2.0, pan=0.3)
    dn = max(0.5, T_CATCH - o0)
    m.put("music", env(trem((HIS + 36, HER - 12), dn, 0.6, 23), [(0.0, 0.3), (dn - 0.2, 1.0), (dn, 0.2)]), o0,
          g_o - 6.0, align=None)
    bowed_tune(m, T_CATCH, UPRIGHT, g_o - 1.0, pan=-0.1, vel=0.85, octave=1, seed=25, stop=8,
               label="the theme's head (violins)", octaves=(0, 1), bright=6500.0, hold=0.5)
    # the Knight up above: the sacks, the slam, the starter coughing and dying, four times
    m.put("efx", street(DC.gold_bag(1), -9.0, 1), T_FLING, cgain(m, T_FLING, "sacks", default=-8.0) - 2.0, pan=0.05,
          label="the sacks thump into the car")
    m.put("efx", street(DC.gold_bag(2), -9.0, 2), T_FLING + 0.06, cgain(m, T_FLING, "sacks", default=-8.0) - 4.0, pan=0.1)
    for j in range(3):
        m.put("efx", street(DC.gold_clink(30 + j, 0.4), -10.0, j), T_FLING + 0.08 + 0.07 * j, -20.0 - 2.0 * j, pan=0.05)
    for t, lab in ((T_SLAM, "the car door slams"), (T_SLAM2, "the car door slams again, right overhead")):
        m.put("efx", street(fx("car_door_close", seed=int(t * 10) % 5), -10.0, 3), t,
              cgain(m, t, "slam", default=-6.0) - 1.0, pan=0.05, label=lab)
    for k, t in enumerate(T_COUGHS[:4]):
        m.put("efx", street(cough_die(k), -10.0, k), t, cgain(m, t, "cough", default=-8.0) - 3.0, pan=0.05,
              label="the starter whines, the engine coughs and dies", align=None)
    # the street wakes: a plucked theme note per window (D A G F); the far city: strings rising
    for j, t in enumerate(T_WAKE[:4]):
        m.put("music", hp((74, 81, 79, 77)[j], 0.85, 100 + j), t, cgain(m, t, "window", default=-12.0) - 1.0,
              pan=cpan(m, t, "window", default=-0.6) + 0.15 * j, label="a window lights: a theme note")
    dc_ = (m.cue_near(T_CITY, "shimmer", win=0.2) or {}).get("dur") or 1.5
    x = env(trem((81, 86, 89), dc_ + 0.4, 0.6, 27), [(0.0, 0.15), (dc_, 1.0), (dc_ + 0.4, 0.0)])
    m.put("music", x, T_CITY, cgain(m, T_CITY, "shimmer", default=-16.0) - 4.0, pan=-0.3,
          label="the far city wakes: strings rising", align=None)
    m.put("music", shimmer(dc_, 6, 98), T_CITY + 0.3, -24.0, pan=-0.4)
    # the near miss: his door flung open; his boots on the grating, right over her head; the kick
    # and his grunt; off the grating; the slam; the engine catches over their heads
    m.put("efx", street(car_door_open(1), -10.0, 1), o0, cgain(m, o0, "flung", default=-8.0) - 1.0, pan=0.05,
          label="the car door flung open")
    for k, t in enumerate(T_LOOKS[:3]):
        m.put("efx", roomed(m, grating_clank(k), t), t, cgain(m, t, "grating", default=-9.0) - 2.0, pan=0.05,
              label="his boots on the grating, overhead")
    m.put("efx", roomed(m, tyre_kick(1), T_KICK), T_KICK, cgain(m, T_KICK, "kick", default=-6.0) - 2.0, pan=0.05,
          label="he kicks the tyre")
    grunt(m, T_KICK + 0.05, cgain(m, T_KICK, "kick", default=-6.0) - 8.0, 0, pan=0.05, wet=-10.0)
    for j in range(2):
        m.put("efx", roomed(m, far(grating_clank(5 + j), 2000.0), T_BACK_IN + 0.18 * j), T_BACK_IN + 0.18 * j,
              cgain(m, T_BACK_IN, "grating", default=-12.0) - 2.0 * j, pan=0.05,
              label="his boots off the grating" if j == 0 else None)
    ec = m.cue_near(T_CATCH, "engine", win=0.2)
    de = min((ec or {}).get("dur") or 6.0, L - T_CATCH)
    x = street(engine_catch(round(de, 2), 1), -12.0, 5)[: n_of(de)]
    m.put("efx", env(x, [(0.0, 1.0), (de - 1.0, 0.8), (de, 0.0)]), T_CATCH, cgain(m, T_CATCH, "engine", default=-5.0) - 4.0,
          pan=0.05, label="the engine catches: a roar overhead")
    td = m.at("", 12.4, "single drip")
    m.put("efx", DC.drip(3), td, cgain(m, td, "drip", default=-14.0), pan=-0.1, label="a drip past her face")
    m.put("efx", roomed(m, match_out(1), T_DOUSE), T_DOUSE, cgain(m, T_DOUSE, "shaken", default=-14.0), pan=-0.4,
          label="the match shaken out")
    # up manhole B's shaft: her climb, his behind her (hollow rungs)
    for j, (t, d, c) in enumerate(cues_with(m, "iron rungs")):
        dd = d or 1.0
        n_ = max(2, int(round(dd / 0.28)))
        for k in range(n_):
            ts = t + dd * k / n_
            m.put("efx", roomed(m, DC.rung((3 * j + k) % 6), ts), ts, c["gain_db"] + CUE_TRIM - 1.5 * (k % 2),
                  pan=c["pan"], label="iron rungs" if k == 0 else None)
    # 16.0: far off, the first police siren, rising (a car)
    for t, d, c in cues_with(m, "siren"):
        dd = max(0.5, L - t)
        x = far(DC.siren(dd + 0.3, hz(69), hz(74), 2.0, 7, 0.75), 1600.0)
        x = env(x, [(0.0, 0.0), (dd, 1.0), (dd + 0.3, 1.0)])[: n_of(dd)]
        m.put("efx", dsp.fade(street(x, -4.0, 6)[: n_of(dd)], 0.0, 0.012), t, c["gain_db"] + CUE_TRIM - 3.0,
              pan=c["pan"], label="the first siren, far", align=None, fades=False)    # cut on the cut (no click)
        m.put("music", dsp.fade(held(PSY, dd, 0.6, 28, octaves=(0, 1), attack=dd * 0.9, release=0.05), 0.0, 0.012), t,
              -20.0, align=None, fades=False)
        break


# ============================================================================ s10 CHECKMATE (146-166)
THEME_RUBY = tuple((b, d, 74 if b == 9 else p) for b, d, p in THEME_MAJOR)   # its C# taken up to her D (the celesta's)
WEB = (76, 77, 79, 76, 72, 74)      # the looks: the theme's second bar (E F G E C) and home (D), a note a look


@section("s10")
def s10(m, S):
    T_BRAKE = m.at("", 0.75, "brakes shriek")               # the cue: a frame before the cars stop (T_BRAKE 0.8)
    T_FACE = m.at("T_FACE", 3.0, "inside the car", "muffled")
    T_WEB = m.at("T_WEB", 5.0, "sirens steady")
    T_RING = m.at("T_RING", 9.0, "red ring")
    T_ARREST = m.at("T_ARREST", 10.0, "close by the cars", "wound down")
    T_LOOK_A = m.at("T_LOOK_A", 11.2, "quick low string note")
    T_LOOK_B = m.at("T_LOOK_B", 11.5, "a step lower")
    T_HANDS = m.at("T_HANDS", 12.1, "held low string note")
    T_OTS = m.at("T_OTS", 13.0, "over his shoulder")
    T_HER = m.at("T_HER_LOOK", 14.5, "high held d")
    T_HIS = m.at("T_HIS_LOOK", 14.9, "low c# under")
    T_MEET = m.at("T_MEET", 15.2, "looks meet")
    T_PULL = m.at("T_PULL", 17.0, "theme upright", "d major")
    L = m.len

    def cg(c, extra=0.0):
        return c["gain_db"] + CUE_TRIM + extra

    def one(words, t, d=0.0, gain=-12.0, pan=0.0):
        return cues_with(m, *words) or [(t, d, {"gain_db": gain, "pan": pan, "text": "", "sfx": ""})]

    # ---- the sirens: two cars, their wails braiding (tuned D5-A5 and A4-D5, a bar each, half a bar
    # apart), one track through the scene: close and rising; muffled through his window; steady on the
    # street; wound down to a slower, lower wail by the cars; further off over his shoulder; gone
    sir = DC.sirens(L + 0.5, 21)
    wail = (dsp.pan_mono(DC.siren(L - 9.5, hz(57), hz(69), 3.6, 31, 0.0), -0.3)
            + dsp.pan_mono(DC.siren(L - 9.5, hz(62), hz(69), 4.2, 32, 0.5), 0.3))

    def seg(x, x0, a, b, gain, lp=None, label=None, sync=None, fin=0.12, fout=0.12):
        y = np.asarray(x[n_of(max(0.0, a - x0)):n_of(max(0.0, b - x0))], np.float64)
        if lp:
            y = dsp.sos(y, "lowpass", lp, 2)
        y = dsp.fade(y, fin, fout, shape="lin")
        m.put("efx", y, max(0.0, a), gain, label=label, sync=sync, align=None, fades=False)

    t0_, d0_, c0 = one(("sirens close by",), 0.0, 5.0, -6.0)[0]
    tm_, dm_, cm = one(("muffled",), T_FACE, 2.0, -12.0)[0]
    ts_, ds_, cs = one(("sirens steady",), T_WEB, 5.0, -12.0)[0]
    tw_, dw_, cw = one(("wound down",), T_ARREST, 3.0, -12.0)[0]
    tf_, df_, cf = one(("sirens further off",), T_OTS, 4.0, -14.0)[0]
    rise = env(sir, [(0.0, 0.35), (0.7, 1.0)])
    seg(rise, 0.0, t0_, tm_ + 0.06, cg(c0, -14.0), label="the sirens close by, rising", sync=t0_, fin=0.02)
    seg(sir, 0.0, tm_ - 0.06, ts_ + 0.06, cg(cm, -5.0), lp=650.0, label="inside the car: the sirens through the glass",
        sync=tm_)
    seg(sir, 0.0, ts_ - 0.06, tw_ + 0.3, cg(cs, -9.0), label="the street: the sirens steady", sync=ts_, fout=0.4)
    seg(wail, tw_ - 0.1, tw_ - 0.1, tf_ + 0.1, cg(cw, -9.0), label="by the cars: the sirens wound down to a wail",
        sync=tw_, fin=0.4)
    far_w = env(dsp.sos(np.asarray(wail, np.float64), "lowpass", 2200.0, 2),
                [(0.0, 1.0), (T_PULL - tf_, 0.8), (L - tf_, 0.0)])
    seg(far_w, tw_ - 0.1, tf_ - 0.1, L, cg(cf, -9.0), label="over his shoulder: the sirens further off", sync=tf_,
        fout=0.05)
    # the bell, further off now, under everything (nearer at the bank's front, far over his shoulder)
    for t, d, c in one(("alarm bell keeps ringing", "keeps ringing"), 0.0, 10.0, -16.0)[:1]:
        db = max(1.0, T_PULL + 2.5 - t)
        x = far(alarm(db, t, 7, 0.25), 3000.0)
        x = dsp.reverb(x, "street", wet_db=-6.0, seed=2)[: n_of(db)]
        x = env(x, [(0.0, 0.0), (0.3, 1.0), (T_ARREST - t, 1.0), (T_ARREST - t + 0.5, 1.4), (T_OTS - t, 1.4),
                    (T_OTS - t + 0.5, 0.8), (T_PULL - t, 0.7), (db, 0.0)])
        m.put("efx", x, t, cg(c, -2.0), pan=0.3, label="the alarm bell, further off now", align=None, fades=False)
    # the engines: his revved off the curb, then idling with the police cars'
    for t, d, c in one(("revs hard",), 0.3, 0.0, -6.0):
        m.put("efx", roomed(m, rev_hard(0.9, 1), t), t, cg(c, -8.0), pan=c["pan"], label="his engine revs hard")
    di = L - 1.0
    x = bed("engine_idle", di, 4, lp=1800.0, rpm=760)
    x = env(x, [(0.0, 0.0), (0.4, 0.5), (T_FACE - 1.0, 0.5), (T_WEB - 1.0, 0.7), (T_ARREST - 1.0, 1.0), (T_OTS - 1.0, 1.0),
                (T_OTS - 0.5, 0.35), (T_PULL - 1.0, 0.25), (di, 0.0)])
    m.put("amb", roomed(m, x, 1.0, 1), 1.0, -21.0, pan=0.1, align=None)
    m.mark(T_WEB, "the street: the engines idling")
    m.mark(T_ARREST, "close by the cars: the engines idling")
    # the brakes, two cars at once, and a whoop dead ahead; the second car slides in behind
    for t, d, c in cues_with(m, "brakes"):
        for j, pn in enumerate((-0.2, 0.25)):
            m.put("efx", roomed(m, DC.tyre_squeal(0.55, 3 + j, 2300.0, 0.25), t + 0.03 * j), t + 0.03 * j,
                  cg(c, -9.0 - 2.0 * j), pan=pn, label="brakes shriek" if j == 0 else None)
        m.put("efx", roomed(m, DC.police_whoop(1, 880.0), t + 0.12), t + 0.12, cg(c, -11.0), pan=0.05)
    for t, d, c in cues_with(m, "slides in close behind", "second car"):
        m.put("efx", roomed(m, DC.car_slide(2, 0.45), t - 0.1), t - 0.1, cg(c, -7.0), pan=c["pan"],
              label="the second car slides in behind", sync=t, align=None)
        m.put("efx", roomed(m, DC.police_whoop(3, 830.0), t + 0.25), t + 0.25, cg(c, -13.0), pan=c["pan"])
    # 0-3 the score: the Psycho chord trembling, rising, his C# under it; a stab on the brakes
    m.put("music", env(trem(PSY, T_FACE + 0.15, 0.7, 1), [(0.0, 0.35), (T_FACE - 0.1, 1.0), (T_FACE + 0.15, 0.0)]), 0.0,
          -21.0, align=None, fades=False)
    m.put("music", bow([(0.0, HIS)], T_FACE + 0.1, 0.85, 2, octaves=(0, 1), attack=0.3, release=0.2), 0.0, -18.0,
          pan=0.2, label="his C#, under the sirens", align=None)
    m.put("music", stab(PSY, 5), T_BRAKE, -13.0, label="the brakes: a stab")
    # 3-5 his face in the window: his heart on its rings (144 bpm, the film's clock); her D and his
    # C# grinding very quietly; a drag on the cigarette
    for t, d, c in cues_with(m, "heartbeat"):
        heart_rings(m, t, t + (d or 2.0), 144.0, film=True, gain=cg(c, 1.0), shape=lambda u: 2.0 * u)
        m.mark(t, "his heart (on its rings)")
    m.put("music", env(trem((61, 62), 2.1, 0.45, 3), [(0.0, 0.0), (0.5, 1.0), (1.8, 1.0), (2.1, 0.0)]), T_FACE, -29.0,
          align=None)
    m.put("music", bow([(0.0, HIS)], 2.0, 0.7, 4, octaves=(0,), attack=0.2, release=0.4), T_FACE, -22.0, align=None)
    for t, d, c in cues_with(m, "drag"):
        breath(m, "draw", t, cg(c, 2.0), pan=c["pan"], label="a sharp drag on the cigarette", dur=0.45)
        m.put("efx", cut(fx("ember_sizzle", seed=7), 0.6, 0.25), t + 0.03, cg(c, -3.0), pan=c["pan"], align=None)
    # 5-9 THE WEB: one plucked note of her theme per look, over B-flat; the police look: a low swell
    lk = cues_with(m, "a look flies") or [(t, 0.0, {"gain_db": -12.0, "pan": -0.5}) for t in (5.25, 5.75, 6.25, 6.75,
                                                                                              7.0, 7.25)]
    for k, (t, d, c) in enumerate(lk):
        p = WEB[min(k, len(WEB) - 1)]
        m.put("music", hp(p, 0.85, 110 + k), t, cg(c, 2.0), pan=0.6 * c["pan"], label=f"a look: {nm(p)} (her theme)")
    t_sw = m.at("", 8.0, "low string swell")
    m.put("music", held((34, 50, 53, 58), max(0.5, t_sw - T_WEB) + 0.2, 0.55, 4, octaves=(0, 1), attack=0.8, release=0.4),
          T_WEB, -25.0, align=None)
    for t, d, c in cues_with(m, "low string swell"):
        dd = max(0.4, d or 1.0)
        m.put("music", held((38, 45, 49, 50), dd + 0.05, 0.75, 5, octaves=(0, -1), attack=0.05, release=0.05,
                            env_=[(0.0, 0.25), (dd, 1.0)]), t, cg(c, -1.0), label="the police look: a low swell",
              align=None, fades=False)
    # 9.0 the ring: the squeak, a stab, the chord trembling away
    for t, d, c in cues_with(m, "red ring"):
        m.put("efx", roomed(m, OF.squeak(0.4, 7), t), t, cg(c, -6.0), pan=0.1, label="the ring: the squeak", align=None)
        m.put("music", stab(PSY, 6), t, cg(c, -6.0), label="the ring: a stab")
        m.put("music", env(trem(PSY, 1.3, 0.5, 6), [(0.0, 1.0), (1.3, 0.0)]), t + 0.05, cg(c, -15.0), align=None)
    # 10-13 THE ARREST: the door, his boots, the sack; his low notes going down: E, D, his C# held
    for t, d, c in cues_with(m, "door shoved open"):
        m.put("efx", roomed(m, car_door_open(2), t), t, cg(c, -6.0), pan=c["pan"], label="his car door shoved open")
    for t, d, c in cues_with(m, "boots on the road"):
        for j in range(2):
            m.put("feet", DC.footstep("knight", 3 + j, "street", j), t + 0.32 * j - STEP_PRE, cg(c, -1.0 * j),
                  pan=c["pan"], label="his boots on the road" if j == 0 else None, sync=t + 0.32 * j)
        m.put("efx", roomed(m, DC.gold_clink(80, 0.5), t + 0.06), t + 0.06, cg(c, -5.0), pan=c["pan"])
    for t, p, lab in ((T_LOOK_A, 40, "a quick low note: E"), (T_LOOK_B, 38, "a step lower: D")):
        c = m.cue_near(t, "low", win=0.06) or {"gain_db": -12.0, "pan": 0.0}
        m.put("music", bow([(0.0, p)], 0.28, 0.85, 7 + p, octaves=(0, 1), attack=0.02, release=0.3), t, cg(c, 2.0),
              pan=0.5 * c["pan"], label=lab, align=None)
    for t, d, c in cues_with(m, "grunt"):
        grunt(m, t, cg(c, -4.0), 2, pan=c["pan"], label="his grunt")
    for t, d, c in cues_with(m, "spills", "sack thumps"):
        m.put("efx", roomed(m, gold_spill(1, 7, 0.8), t), t, cg(c, -7.0), pan=c["pan"],
              label="the sack thumps down, the gold spills")
    ch = m.cue_near(T_HANDS, "held low", win=0.1) or {"gain_db": -8.0, "pan": 0.0}
    dh = ch.get("dur") or 0.9
    m.put("music", bow([(0.0, HIS)], dh + 0.5, 0.85, 9, octaves=(0, 1), attack=0.08, release=0.9), T_HANDS, cg(ch, -2.0),
          label="his hands up: his C#, held", align=None)
    # 13-17 OVER HIS SHOULDER: the street hushed; the lid, her climb, the old man's; her D, his C#,
    # and the two struck together as their looks meet; her pats, her turn
    for t, d, c in one(("street hushed",), T_OTS, 4.0, -14.0)[:1]:
        x = night_bed(L - t + 0.5, 9, lp=3000.0, wind=0.7)
        m.put("amb", env(x, [(0.0, 0.0), (0.8, 1.0), (L - t, 1.0), (L - t + 0.5, 0.0)]), t, cg(c, -8.0),
              label="the street hushed", align=None)
    for t, d, c in cues_with(m, "manhole lid"):
        m.put("efx", roomed(m, far(DC.manhole_scrape(0.4, 2), 2600.0), t), t, cg(c, -2.0), pan=c["pan"],
              label="across the street the lid grinds off", align=None)
    for t, d, c in cues_with(m, "she climbs out"):
        m.put("efx", roomed(m, DC.glove_creak(2, 0.3), t), t, cg(c, 1.0), pan=c["pan"], label="her gloves on iron",
              align=None)
        m.put("efx", roomed(m, far(DC.rung(3), 3000.0), t + 0.12), t + 0.12, cg(c, -2.0), pan=c["pan"])
    for t, d, c in cues_with(m, "climbs out after"):
        for j in range(2):
            m.put("efx", roomed(m, far(DC.rung(4 + j), 3000.0), t + 0.22 * j), t + 0.22 * j, cg(c, -1.0 * j),
                  pan=c["pan"], label="his shoes on the rungs" if j == 0 else None)
        m.put("vox", roomed(m, far(wheeze(1), 3500.0), t + 0.3), t + 0.3, cg(c, -2.0), pan=c["pan"], align=None,
              key=True)
    dh_ = (m.cue_near(T_HER, "high held", win=0.1) or {}).get("dur") or 1.5
    m.put("music", harm(HER, dh_ + 0.3, 0.75, 10, attack=0.25, release=1.0), T_HER,
          cgain(m, T_HER, "high held", default=-10.0) - 6.0, label="her look: her D, high", align=None)
    dc2 = (m.cue_near(T_HIS, "low c#", win=0.1) or {}).get("dur") or 1.1
    m.put("music", bow([(0.0, HIS)], dc2 + 0.3, 0.8, 11, octaves=(0, 1), attack=0.2, release=1.0), T_HIS,
          cgain(m, T_HIS, "low c#", default=-10.0) - 6.0, label="his look: his C#, low", align=None)
    gm_ = cgain(m, T_MEET, "looks meet", default=-8.0)
    m.put("music", OF.chime(hz(HER), 3, 4.0) + 0.8 * OF.chime(hz(HER - 1), 4, 4.0), T_MEET, gm_ - 7.0,
          label="the looks meet: her D and his C#, struck together", hall=-10.0)
    m.put("music", pz(HIS, 0.8, 12), T_MEET, gm_ - 6.0)
    for t, d, c in cues_with(m, "pats"):
        p0, p1 = m.span("T_PAT", (t, t + 0.3))
        for j, tp in enumerate((t, t + 0.5 * (p1 - p0) if p1 - p0 > 0.1 else t + 0.15)):
            m.put("efx", roomed(m, pat(j), tp), tp, cg(c, 2.0 - 2.0 * j), pan=c["pan"],
                  label="her glove pats her pocket" if j == 0 else None)
    for t, d, c in cues_with(m, "heels turn"):
        m.put("feet", roomed(m, DC.heel_scuff(2, "her"), t), t - STEP_PRE, cg(c, 1.0), pan=c["pan"],
              label="her heels turn on the stone", sync=t)
    # 17.0 THE PULL BACK: THE THEME upright, in D MAJOR, violins an octave up and harp over the
    # strings' harmony (beats 0-6 here, the rest in s11, its last D on s11's 4.0); their heels going
    t_m = T_PULL
    gt = cgain(m, T_PULL, "theme", default=-8.0)
    bowed_tune(m, t_m, THEME_RUBY, gt - 6.0, pan=-0.1, vel=0.8, octave=1, seed=120, stop=6,
               label="THE THEME in D major (violins)", octaves=(0, 1), bright=6500.0, attack=0.25)
    pluck_line(m, t_m, THEME_RUBY, "harp", gt - 8.0, pan=0.15, vel=0.75, octave=0, seed=121, stop=6)
    pad(m, t_m, PROG_MAJ, gt - 13.0, seed=122, stop=6, octaves=(0, 1), attack=0.7, bright=5000.0)
    for k, (t, d, c) in enumerate(cues_with(m, "heel on the stone", "walking away")):
        who = "her" if k % 2 == 0 else "cracker"
        m.put("feet", DC.footstep(who, k, "street", k % 5), t - STEP_PRE, cg(c, 3.0), pan=c["pan"],
              label="a heel, walking away", sync=t)
        if who == "her":
            m.put("feet", roomed(m, DC.heel_tap(k % 3), t), t, cg(c, -9.0), pan=c["pan"])


# ============================================================================ s11 END (166-174)
@section("s11")
def s11(m, S):
    T_PING = m.at("T_PING", 1.5, "celesta")
    T_ELEV = m.at("T_ELEV", 2.5, "strings swell")
    T_SNAP = m.at("T_SNAP", 2.52, "rising run")
    STAG = g(S, "STAGGER", 0.025)
    T_STAMP = m.at("T_STAMP", 3.25, "stamps down")
    T_STRIPS = m.ats("T_STRIPS", (3.5, 3.75), "slashes", n=2)
    STRIP_IN = g(S, "STRIP_IN", 0.24)
    T_CUT = m.at("T_CUT", 4.0, "last chord")
    T_AWAY = m.at("T_AWAY", 4.45, "swish")
    T_POP = m.at("T_POP", 5.0, "pops")
    beats = g(S, "BEATS", ((5.45, 1.0), (6.05, 0.7)))
    T_SIL = m.at("T_SILENCE", 7.5, "silence")
    L = m.len

    def cg(c, extra=0.0):
        return c["gain_db"] + CUE_TRIM + extra

    # night under the lamp: the sirens far off and fading, a breath of wind, the lamp's hum
    for t, d, c in cues_with(m, "night under the street lamp", "sirens far off") or [(0.0, 2.5, {"gain_db": -18.0})]:
        dd = max(0.5, d or 2.5)
        x = far(DC.sirens(dd + 0.6, 41), 1500.0)
        m.put("efx", env(x, [(0.0, 0.7), (dd, 0.15), (dd + 0.6, 0.0)]), t, cg(c, -4.0),
              label="the sirens far off, fading", align=None)
        m.put("amb", env(bed("wind_gust", dd + 1.0, 5, lp=1600.0), [(0.0, 0.6), (dd, 1.0), (dd + 1.0, 0.0)]), t,
              cg(c, -2.0), align=None)
        hum = DC.lamp_hum(m.t0 + t, dd + 0.3, 1.0)
        m.put("amb", dsp.fade(hum, 0.3, 0.3), t, cg(c, -22.0), align=None)
        break
    for k, (t, d, c) in enumerate(cues_with(m, "glove creaks")):
        m.put("efx", roomed(m, DC.glove_creak(k % 3, 0.45), t), t, cg(c, 3.0), pan=c["pan"], label="her glove creaks",
              align=None)
    for t, d, c in cues_with(m, "ruby's red", "soft high string harmonic"):
        m.put("music", harm(93, (d or 0.9) + 0.4, 0.6, 3, attack=0.3, release=0.8), t, cg(c, 1.0),
              label="the ruby's red: a high harmonic", align=None)
    # 1.5 THE CELESTA: the one note of it in the whole film, her D, high, on the ruby's glint
    the_celesta(m, T_PING, cgain(m, T_PING, "celesta", default=-9.0) - 1.0, label="the ruby glints: THE celesta")
    # THE THEME in D major goes on from s10 (beats 6-14; its last D on T_CUT); the violins pp under
    # her fist, up with the windows; the harp leaves the glint to the celesta
    t_m = T_CUT - 14 * BEAT
    bowed_tune(m, t_m, THEME_RUBY, -14.0, pan=-0.1, vel=0.8, octave=1, seed=130, start=6, stop=15,
               label="THE THEME in D major (violins), to its last D", octaves=(0, 1), bright=6500.0, attack=0.2,
               hold=1.8, shape=[(0.0, 0.5), (T_ELEV - (t_m + 3.0), 0.55), (T_CUT - (t_m + 3.0), 1.0)])
    pluck_line(m, t_m, THEME_RUBY, "harp", -17.0, pan=0.15, vel=0.75, octave=0, seed=131, start=6, stop=15, skip=(9,))
    pad(m, t_m, PROG_MAJ, -24.0, seed=132, start=6, stop=11, octaves=(0, 1), attack=0.5, bright=4500.0)
    # 2.5 the windows fly up: the strings swell on D/A, a rising run of plucks; A7 under the stamp and
    # the strips; on the theme's last D the last chord, D major with the major seventh, held
    for t, d, c in cues_with(m, "strings swell") or [(T_ELEV, 0.75, {"gain_db": -10.0})]:
        dd = max(0.4, d or 0.75)
        m.put("music", held((33, 50, 54, 57, 62), dd + 0.05, 0.8, 4, octaves=(0, 1), attack=0.05, release=0.08,
                            env_=[(0.0, 0.35), (dd, 1.0)]), t, cg(c, -2.0), label="the windows fly up: D/A, swelling",
              align=None, fades=False)
    for t, d, c in cues_with(m, "rising run") or [(T_SNAP, 0.3, {"gain_db": -12.0})]:
        run = (62, 66, 69, 74, 78, 81, 86, 90, 93, 98, 102, 105)
        for j, p in enumerate(run):
            m.put("music", hp(p, 0.8 - 0.02 * j, 140 + j), t + STAG * j, cg(c, 1.0), pan=-0.4 + 0.07 * j,
                  label="the windows lift out: a rising run" if j == 0 else None)
    m.put("music", held((33, 49, 55, 57, 61), T_CUT - T_STAMP + 0.05, 0.85, 5, octaves=(0, 1), attack=0.01, release=0.08),
          T_STAMP, -17.0, label="A7 under the stamp", fades=False)
    for t, d, c in cues_with(m, "stamps down") or [(T_STAMP, 0.0, {"gain_db": -4.0})]:
        m.put("efx", DC.stamp(1), t, cg(c, -2.0), label="the title stamps down")
        m.put("efx", sfx._thump(n_of(0.4), 90.0, 45.0, 0.01, 0.15), t, cg(c, -6.0))
    for i, t in enumerate(T_STRIPS[:2]):
        c = m.cue_near(t, "strip", win=0.05) or {"gain_db": -6.0 + i}
        m.put("efx", DC.whoosh_thud(STRIP_IN, 3 + i, 0.6 * i), t - STRIP_IN, cg(c), pan=(-0.25, 0.25)[i],
              label="a strip slashes in: whoosh and thud", sync=t, align=None)
    gl = cgain(m, T_CUT, "last chord", default=-5.0)
    m.put("music", held((38, 50, 54, 57, 61, 66), 2.2, 0.85, 6, octaves=(0, 1), attack=0.03, release=1.6), T_CUT, gl - 8.0,
          label="the last chord: D major with the major seventh", align=None)
    m.put("music", bow([(0.0, 26)], 2.2, 0.8, 7, octaves=(0, 1), attack=0.03, release=1.6), T_CUT, gl - 10.0,
          align=None)
    m.put("music", stab((50, 54, 57, 61), 7), T_CUT, gl - 12.0)
    # the halves away, the dot, its two heartbeats; then silence
    for k, pn in enumerate((-0.5, 0.5)):
        m.put("efx", DC.paper_whoosh(0.5, 2 + k), T_AWAY + 0.03 * k, cgain(m, T_AWAY, "swish", default=-12.0) - 2.0,
              pan=pn, label="the halves slide away" if k == 0 else None, align=None)
    m.put("music", OF.soft_hit(hz(62), 2), T_POP, cgain(m, T_POP, "pops", default=-10.0) + 1.0, label="the red dot pops")
    for t, strength in beats:
        g_ = cgain(m, float(t), "heartbeat", default=-8.0)
        m.put("music", OF.heart(0.26, seed=int(t * 10) % 3), float(t), g_ + 2.0 + 4.0 * (float(strength) - 1.0),
              label="the dot beats like a heart", hall=-24.0)
    m.mark(T_SIL, "silence")


# ============================================================================ the bible's cues (stand-ins)
def _bc(t, text, gain=-12.0, dur=None, pan=0.0):
    c = {"t": float(t), "sfx": text, "gain_db": float(gain), "pan": float(pan)}
    if dur is not None:
        c["dur"] = float(dur)
    return c


def _gold(pairs):
    out = []
    for a, b in pairs:
        out += [_bc(a, "gold clink: a bar lifted off the stack", -17), _bc(b, "gold drop: a bar drops into the sack", -16)]
    return out


BIBLE_CUES = {       # the bible's sound beats (scene times): what a scene played as a stand-in is spotted from
    "s01": [_bc(t, "the red dot ticks: a dry clock tick", -8) for t in (0.25, 0.5, 0.75)]
           + [_bc(1.125, "the title's strips race across the black: a run of fast string stabs", -10, 1.4),
              _bc(1.3, "DOUBLE assembles: a paper rustle snapping together", -12),
              _bc(1.55, "CROSS assembles: a paper rustle snapping together, lower", -12),
              _bc(2.51, "the paper strip slashes across: whoosh-thud", -6, pan=-0.2),
              _bc(2.76, "the red strip crosses it: whoosh-thud, lower and harder", -5, pan=0.2),
              _bc(3.4, "the halves part: a paper tear and a swish", -9),
              _bc(4.1, "paper floods in round the buildings: a soft rush", -14),
              _bc(4.3, "the letters become windows: small paper snaps", -14, 0.9),
              _bc(5.5, "night falls: a low gong", -8), _bc(5.75, "the city rises: a pizzicato descent", -10),
              _bc(6.0, "the moon drops: a soft bell", -12)]
           + [_bc(t, "the cutaway: a click as a storey opens", -12) for t in (6.75, 7.0, 7.25, 7.5, 7.75)]
           + [_bc(8.0, "the road opens down: stone sliding, a hollow drip far below", -12),
              _bc(8.5, "the vault and its gold: a deep cello note and a soft string shimmer", -8, 1.5)]
           + [_bc(t, "light out: a plucked note, descending", -10) for t in (9.0, 9.5, 10.0)]
           + [_bc(10.5, "the far city goes dark: a last low pluck", -12),
              _bc(10.75, "the crew's 4: one high pizzicato note", -10),
              _bc(11.5, "a rising tremolo into the crew's room, to the cut", -8, 2.5)],
    "s02": [_bc(0.0, "the crew's room: the wall clock ticking on the beat, the lamp's chain creaking", -14, 2.0),
            _bc(2.0, "her cameo: a pizzicato note, high (D)", -9), _bc(3.5, "the Cracker's cameo: a pizzicato note, middle", -9),
            _bc(4.25, "a glint across his spectacles: a soft high string harmonic flick", -16),
            _bc(5.0, "the Knight's cameo: a pizzicato note, low (C sharp)", -8),
            _bc(5.6, "the cigarette crackles as he draws on it", -14),
            _bc(6.5, "over her shoulder: the night street through the glass, a far wind", -20, 5.0),
            _bc(7.0, "a far footstep: the guard on his round inside the bank", -22, pan=0.2),
            _bc(8.25, "one damped tink: the alarm bell's own note, muted", -12, pan=-0.3),
            _bc(10.75, "she turns from the window: a coat's rustle", -16),
            _bc(12.0, "paper: the plan unrolled and smoothed flat on the table", -10),
            _bc(14.0, "her murmur, low and close, no words", -8, 2.0)],
    "s03": [_bc(0.0, "her murmur, low and close, no words, as she lays out the way in", -9, 3.4),
            _bc(0.5, "a low cello hum under the murmur: the old man listening", -18, 3.0),
            _bc(3.75, "one damped tink: the alarm bell's own note, muted", -12, pan=-0.2),
            _bc(4.5, "a tap on paper: her finger on the vault", -10, pan=0.2),
            _bc(5.0, "a second tap on paper, on the vault", -10, pan=0.2),
            _bc(5.0, "a sting: a high string harmonic and a marker pen's squeak as the red ring closes", -8),
            _bc(5.4, "a glint on the gold: a soft high shimmer", -17),
            _bc(6.0, "his low note: a cello C sharp, held under the looks", -10, 3.0),
            _bc(7.25, "her look: a high violin D, held soft", -14, 1.0),
            _bc(8.25, "a low held note as her look slips down to the sewer, unseen", -12, 0.75),
            _bc(9.6, "braam: a low swell as his jagged red arm grows across the table", -6, 1.0),
            _bc(11.0, "the arm snaps back: a short low thud and a whoosh", -8),
            _bc(12.0, "the mirror: the clock louder, a sustained dissonance between her high D and his low C sharp", -10, 3.5)]
           + [_bc(t, "the clock ticks, louder, as the halves press in", g) for t, g in ((13.0, -8), (13.5, -7), (14.0, -6),
                                                                                        (14.5, -5))]
           + [_bc(16.5, "click: the lamp goes out", -6)],
    "s04": [_bc(0.0, "night air: the street at night, a distant city, wind", -22, 5.3)]
           + [_bc(t, f"footstep: a soft step crossing the road ({w})", -22) for t, w in ((0.8, "knight"), (1.5, "her"),
                                                                                         (2.1, "cracker"))]
           + [_bc(2.55, "iron tick: his fingers hook the lid's edge", -17),
              _bc(2.75, "manhole scrape: the lid levered up and dragged aside", -9, 0.4),
              _bc(3.25, "manhole clank: the iron lid falls flat on the road", -5),
              _bc(4.0, "chime: the bank's clock strikes midnight, one deep bell chime", -9, 3.0)]
           + [_bc(t, "rung: a shoe on the first iron rung, going down", -14) for t in (3.5, 4.0, 4.5)]
           + [_bc(5.0, "sink whoosh: the shaft stretches away below them", -20, 2.0),
              _bc(5.0, "sewer bed: the shaft's echo, the sewer", -28, 9.0),
              _bc(5.6, "drip: a drip into still water", -26), _bc(6.3, "drip: a drip into still water", -26)]
           + [_bc(t, "water step: a footstep in shallow water", -21) for t in (7.5, 8.0, 8.5, 9.0)]
           + [_bc(9.5, "hatch creak: the hatch pushed up a crack", -13, 0.6)]
           + [_bc(t, "footstep: a soft step up into the hall's dark corner", -26) for t in (11.5, 12.0, 12.5)],
    "s05": [_bc(0.0, "hall tone: the hall at night, room tone", -26, 9.5),
            _bc(0.5, "flashlight click: his flashlight clicks on", -14, pan=0.3),
            _bc(3.0, "held breath: a breath held in the corner", -24),
            _bc(5.5, "tiptoe pizz: her high D", -18), _bc(6.5, "tiptoe pizz: his low C#", -18),
            _bc(7.5, "tiptoe pizz: a middle note", -18),
            _bc(5.9, "heartbeat: the Cracker's heart on the beat (120 bpm)", -14, 3.4),
            _bc(9.5, "wheeze: an old man's wheezing breath, held in", -20),
            _bc(10.0, "steth clank: CLANK, the stethoscope swings into a pipe", -6),
            _bc(10.25, "coat swish: the guard spins round", -15),
            _bc(11.5, "held note: one low tremolo string note under the two eyes", -20),
            _bc(12.0, "cat hiss: a cat's hiss", -14), _bc(12.5, "cat claws: claws scrabble on wood", -17),
            _bc(13.0, "can clatter: CLATTER, the tin can hits the floor", -8, 0.9),
            _bc(13.75, "guard sigh: the guard breathes out, half a laugh", -16)]
           + [_bc(t, "guard step: footstep, the guard walks off", -22) for t in (14.25, 14.75, 15.25)]
           + [_bc(16.0, "push whoosh: a low rising whoosh, the push in on the dial", -20, 2.0)],
    "s06": [_bc(0.0, "vault tone: the hush at the vault door", -28, 11.0),
            _bc(1.5, "knee down: the old man goes down on one knee", -27),
            _bc(3.5, "steth tick: through the stethoscope, a soft tick", -22)]
           + [_bc(t, "dial spin: the dial spins, fine ticks slowing to a creep", -20, 1.25) for t in (4.75, 6.25, 7.75)]
           + [_bc(6.0, "gate click: pitched LOW", -9), _bc(7.5, "gate click: pitched MID", -9),
              _bc(9.0, "gate click: pitched HIGH", -9), _bc(9.5, "fence clunk: CLUNK, the fence drops", -5),
              _bc(10.0, "bolt run: the bolts withdraw round the rim (a rolling metallic run)", -13),
              _bc(10.45, "wheel ratchet: he hauls on the wheel", -11, 0.55),
              _bc(11.1, "hinge groan: the door swings open", -9, 1.8),
              _bc(11.2, "string swell: D minor rising, gold light floods out", -8, 2.8),
              _bc(12.5, "look note: a look goes in to the gold, his low C#", -16),
              _bc(13.0, "look note: a middle note", -16), _bc(13.5, "look note: her high D", -16)],
    "s07": _gold(((0.25, 0.55), (1.05, 1.35), (2.55, 2.85), (3.35, 3.65)))
           + [_bc(0.95, "box open: her deposit box's little door opens", -19, 0.55),
              _bc(1.5, "ruby close: the ruby, close", -24), _bc(1.7, "ruby glint: a faint high ting", -20),
              _bc(2.0, "glove creak: her gloved hand comes in", -26),
              _bc(2.6, "ruby tick: finger and thumb close on it", -24),
              _bc(2.7, "string harmonic: she lifts it into the light, a soft rising string harmonic", -22, 0.6),
              _bc(3.0, "ruby shimmer: it flares, a glassy shimmer (not the celesta)", -18),
              _bc(3.65, "cloth swish: her hand takes it away", -24),
              _bc(4.4, "pocket rustle: into her coat pocket", -26),
              _bc(6.0, "his note: his look, his low note, C# on the cellos, held as a pedal", -14, 3.0),
              _bc(6.0, "theme inverted: THE THEME in mirror inversion, low and dark, four bars", -12, 8.0)]
           + [_bc(t, "look tick: his red look flies, a soft dry tick, a plucked low C#", -22) for t in (6.4, 7.1, 7.6)]
           + [_bc(9.2, "grunt: he heaves up both sacks, a strained grunt, the gold shifting", -17)]
           + [_bc(t, "knight step: footstep, his heavy step on the steel floor, two full bags swinging", -21)
              for t in (10.0, 10.7, 11.4)]
           + [_bc(11.6, "hinge groan: the great door swings shut, faster and faster", -9, 2.4),
              _bc(11.7, "grunt: he throws his weight against the door, a strained grunt, held", -15),
              _bc(14.0, "boom: BOOM, the vault door slams shut; black", -2),
              _bc(14.4, "dial spin: the red dial spun, the lock run backwards (clicks)", -15, 0.5),
              _bc(15.3, "marker squeak: THE SECOND RED MARKER RING, the squeak", -11, 0.4),
              _bc(15.3, "low stab: a low string stab under the ring", -10)]
           + [_bc(15.5 + 0.25 * i, "run step: footstep, his heavy run across the hall (a red dot)", -15 - i % 2)
              for i in range(6)]
           + [_bc(15.6, "bags swing: the gold clinking", -21, 1.25), _bc(17.0, "bang: BANG, the side door bursts open", -4),
              _bc(17.0, "alarm bell: the bell rings and rings, loud, a red ripple on every beat", -6, 3.0),
              _bc(17.7, "bell push: the camera pushes in on the ringing bell", -10, 2.3)],
    "s08": [_bc(0.0, "black: the old man's ragged breath, close", -12, 1.6),
            _bc(1.2, "a match scratches on its box (sparks)", -8, pan=0.3), _bc(1.6, "the match flares", -8, pan=0.3),
            _bc(2.0, "his heartbeat, fast and loud", -6, 4.0), _bc(2.0, "a high held string, rising", -12, 4.0)]
           + [_bc(t, "a fist on the steel door: a muffled BOOM", -4, pan=-0.4) for t in (3.5, 4.0, 4.5)]
           + [_bc(5.0, "he sags against the door: a breath, cloth on steel", -16),
              _bc(6.0, "far off through the walls, the alarm bell, faint", -18, 2.0),
              _bc(6.9, "her breath of a laugh", -10), _bc(7.25, "a low held note under her eye", -16, 0.75),
              _bc(8.0, "into her eye: a deep rising whoosh", -8, 0.5),
              _bc(8.5, "the night before: drips in a hollow shaft", -18, 3.25),
              _bc(9.0, "the torch's roar and hiss as it cuts up through stone", -9, 0.6),
              _bc(9.75, "the torch's roar and hiss as it cuts again", -9, 0.6),
              _bc(10.5, "stone grinding as the block lifts a crack; a shimmer on the gold", -12, 0.4),
              _bc(11.2, "the block set back: stone settling, a soft knock", -12),
              _bc(11.75, "out of her eye: a reverse whoosh", -10, 0.25),
              _bc(12.0, "the vault: the bell faint through the walls, the match's breath", -20, 2.0),
              _bc(12.4, "her heel taps the floor: a click", -10), _bc(12.75, "a hollow knock", -4),
              _bc(13.25, "the old man turns: a sharp intake of breath", -14)],
    "s09": [_bc(0.0, "the vault by match light: the bell far off, the match's breath", -20, 2.0),
            _bc(0.2, "her gloves on stone; the cut block grinds up", -10, 0.3),
            _bc(0.85, "the block set down: a heavy soft stone thud", -10, pan=-0.4),
            _bc(0.9, "a breath of cold air up the shaft", -16, 1.1),
            _bc(2.1, "a glassy tick as the light crosses his spectacles", -14),
            _bc(2.4, "the old man's dry chuckle, breath only", -12),
            _bc(3.0, "the shaft: echoing drips, water lapping far below", -18, 4.0),
            _bc(3.2, "her gloves squeal down the ladder's rails, a fast slide", -12, 1.0),
            _bc(4.2, "a splash: she lands in the sewer", -6), _bc(4.5, "his slower slide down the rails", -14, 1.1),
            _bc(5.6, "a heavier splash: he lands", -6)]
           + [_bc(t, "a wading step: a slosh in the sewer", -16) for t in (5.8, 6.3, 6.8, 7.3, 7.8)]
           + [_bc(7.0, "the street: the alarm bell rings and rings, loud", -6, 11.0),
              _bc(7.0, "a driving ostinato for the race, her high D against his low C#", -10, 9.0),
              _bc(7.3, "the two sacks thump into the car", -8), _bc(7.6, "the car door slams", -6)]
           + [_bc(t, "the starter whines and the engine coughs and dies", -8) for t in (8.0, 8.5, 9.1, 9.7)]
           + [_bc(t, "a window lights: one plucked note of her theme", -12, pan=-0.6) for t in (9.5, 10.0, 10.5, 11.0)]
           + [_bc(10.2, "the car door flung open", -8)]
           + [_bc(t, "his boots on the iron grating, right overhead", -9) for t in (10.45, 10.8, 11.05)]
           + [_bc(11.3, "his boot kicks the tyre: a thud, and his grunt", -6),
              _bc(11.5, "the far city waking: a soft rising shimmer of strings", -16, 1.5),
              _bc(11.6, "his boots off the grating", -12), _bc(11.9, "the car door slams again, right overhead", -5),
              _bc(12.0, "the engine catches: a roar right over their heads", -5, 6.0),
              _bc(14.95, "the match shaken out", -14, pan=-0.4), _bc(15.0, "iron rungs: her climb", -12, 1.1, -0.4),
              _bc(15.45, "iron rungs: his climb behind her", -13, 0.9, -0.4),
              _bc(16.0, "far off, the first police siren, rising", -14, 2.0, 0.4)],
    "s10": [_bc(0.0, "sirens close by and rising: two police cars, braiding", -6, 5.0),
            _bc(0.0, "under it all the alarm bell keeps ringing, further off", -16, 10.0, 0.3),
            _bc(0.3, "his engine revs hard", -6), _bc(0.75, "brakes shriek; a siren whoop dead ahead", -4),
            _bc(1.15, "a second car slides in close behind, a short whoop", -5, pan=-0.5),
            _bc(3.0, "inside the car: the sirens muffled through the glass", -12, 2.0),
            _bc(3.0, "his heartbeat, fast and heavy", -6, 2.0), _bc(4.35, "a sharp drag on the cigarette", -12),
            _bc(5.0, "the street: sirens steady, the bell, the engine idling", -12, 5.0)]
           + [_bc(t, "a look flies: one plucked note of her theme", -12, pan=-0.5) for t in (5.25, 5.75, 6.25, 6.75, 7.0,
                                                                                             7.25)]
           + [_bc(8.0, "the police lights' looks: a low string swell", -10, 1.0),
              _bc(9.0, "the red ring: the marker's squeak, and a stab", -4),
              _bc(10.0, "close by the cars: the engines idling, the sirens wound down to a wail", -12, 3.0),
              _bc(10.3, "his car door shoved open", -6), _bc(10.6, "his boots on the road; the sack's gold clinks", -10),
              _bc(11.2, "a quick low string note", -12), _bc(11.5, "the same low note, a step lower", -12),
              _bc(11.75, "the Knight's grunt", -8), _bc(11.9, "the sack thumps down on the road; the gold spills out", -5),
              _bc(12.1, "a held low string note: his C#", -8, 0.9),
              _bc(13.0, "over his shoulder: the sirens further off, the street hushed", -14, 4.0),
              _bc(13.4, "across the street a manhole lid grinds and slides off", -10, pan=-0.3),
              _bc(13.7, "her gloves on iron; she climbs out", -14, pan=-0.3),
              _bc(14.1, "his shoes on the rungs, a wheeze: the old man climbs out after her", -15, pan=-0.3),
              _bc(14.5, "her look: a high held D", -8, 1.5), _bc(14.9, "his look back: a low C# under it", -8, 1.1),
              _bc(15.2, "the looks meet: the two notes, a semitone apart, struck together like a chime", -6),
              _bc(15.8, "her glove pats her coat pocket twice, softly", -14, pan=-0.3),
              _bc(16.3, "her heels turn on the stone", -14, pan=-0.3),
              _bc(17.0, "the theme upright, resolving into D major as the camera pulls back", -6, 3.0)]
           + [_bc(17.1 + 0.17 * k, "a heel on the stone, walking away", -15 - k % 2 - 0.4 * max(0, k - 10),
                  pan=-0.05 - 0.025 * k) for k in range(17)],
    "s11": [_bc(0.0, "night under the street lamp: the sirens far off and fading, a breath of wind", -18, 2.5),
            _bc(0.4, "her leather glove creaks as the fingers open", -13, pan=0.1),
            _bc(0.75, "the ruby's red: a soft high string harmonic", -16, 0.9),
            _bc(1.5, "the ruby glints: the one celesta ping", -7),
            _bc(2.2, "she closes her hand on it: the glove creaks", -12, pan=0.1),
            _bc(2.5, "the strings swell on a D major chord as the windows fly up", -10, 0.75),
            _bc(2.52, "the windows lift out: a quick rising run of plucked notes", -12, 0.3),
            _bc(3.25, "the title stamps down: a deep paper thud", -4),
            _bc(3.5, "the paper strip slashes in: a whoosh and a thud", -6),
            _bc(3.75, "the red strip slashes across it: a whoosh and a thud", -5),
            _bc(4.0, "the last chord: D major with the major seventh, held", -3, 1.0),
            _bc(4.45, "the halves slide away: a paper swish", -12), _bc(5.0, "the red dot pops", -10),
            _bc(5.45, "a heartbeat: lub-dub", -6), _bc(6.05, "a heartbeat: lub-dub", -10), _bc(7.5, "silence", -60)],
}


def silence_from():
    """Film time the sound must be gone: s11's T_SILENCE (scene time; the bible's 7.5)."""
    S = scene("s11") if "s11" in START else None
    ts = g(S, "T_SILENCE", 7.5) if S is not None else 7.5
    return float(min(DUR, START.get("s11", DUR - 8.0) + float(np.clip(ts, 0.5, LENGTH.get("s11", 8.0)))))


# ============================================================================ spotting: a cue no section answered
WHO = {"architect": "her", "her": "her", "she": "her", "knight": "knight", "cracker": "cracker", "guard": "guard"}


def realize(m, c):
    """Realise a cue no section answered, from its words (its tag or lead words first), at its time, in
    its scene's room. Returns how ('auto: ...'), or why nothing was added ('silence ...', 'the clock
    ...'), or why it could not be ('not realised: ...')."""
    s, h, t = c["text"], head(c), float(c["t"])
    g0, pan, d = c["gain_db"] + CUE_TRIM, c["pan"], (float(c["dur"]) if c.get("dur") else None)
    seed = int(round(t * 100)) % 997
    lab = "auto: " + h[:40]
    words = set(re.findall(r"[a-z#]+", s))

    def has(*w):
        return any(x in s for x in w)

    def word(*w):
        return any(x in words for x in w)

    def hd(*w):
        return any(x in h for x in w)

    def put(x, gain=0.0, bus="efx", at=None, align="onset", sync=None, room_=True, wet=None, label=True, key=False,
            hall="auto", pan_=None):
        tt = t if at is None else at
        y = roomed(m, x, tt, seed, wet) if room_ else x
        m.put(bus, y, tt, g0 + gain, pan=pan if pan_ is None else pan_, label=lab if label else None, align=align,
              sync=sync, key=key, hall=hall)

    def who():
        if c.get("who") in WHO:
            return WHO[c["who"]]
        return ("guard" if has("guard") else "knight" if has("knight", "heavy") else
                "cracker" if has("cracker", "old man", "shuffl") else "her")

    def step(w, k=0, at=None, gain=0.0, steel=False, lp=None, label=True):
        tt = t if at is None else at
        x = (DC.steel_step(w, (seed + k) % 7, room(m, tt)[0], seed) if steel else
             DC.footstep(w, (seed + k) % 7, room(m, tt)[0], (seed + k) % 5))
        m.put("feet", far(x, lp) if lp else x, tt - STEP_PRE, g0 + gain, pan=pan, label=lab if label else None, sync=tt)

    # ---- nothing to add
    if hd("silence") or s.strip(" .") == "black":
        m.mark(t, lab)
        return "silence (nothing to add)"
    if has("room tone", "hall tone", "vault tone", "hush at", "dead hush"):
        dd = max(1.0, d or 3.0)
        put(bed("room_tone", dd, seed % 5, lp=1800.0), gain=-8.0, bus="amb", room_=False, align=None)
        return "auto: room tone"
    if has("clock tick", "clock ticking", "clock ticks", "wall clock", "the beat's tick") and not has("chime", "strikes"):
        m.mark(t, lab)
        return "the clock (on the tick bus)"
    # ---- the voices (their takes only) and breath
    if has("murmur"):
        say(m, "her", seed % 2, t, g0 + VOX_TRIM, fit=d, seed=seed, label=lab)
        return "auto: her murmur (no words)"
    if word("sigh", "sighs") or has("breathes out"):
        breath(m, "out", t, g0 + 2.0, pan=pan, label=lab, semis=-1.0)
        return "auto: a breath out"
    if has("laugh"):
        laugh(m, t, g0 - 6.0, pan=pan, label=lab)
        return "auto: her breath of a laugh (her take)"
    if has("chuckle"):
        put(chuckle_breath(seed % 3), bus="vox", align=None, key=True)
        return "auto: a dry chuckle (breath only)"
    if has("grunt"):
        grunt(m, t, g0 + 1.0, 1 if has("held", "weight", "strain") else 0, pan=pan, label=lab)
        if has("iron tick"):
            put(DC.metal_tap(seed % 3), label=False)
        return "auto: his grunt (his take)"
    if has("yelp"):
        breath(m, "gasp", t, g0 + 2.0, pan=pan, label=lab, semis=-4.0)
        m.put("feet", roomed(m, DC.heel_scuff(seed % 4, "guard"), t), t - STEP_PRE, g0, pan=pan)
        return "auto: a gasp and a scuff (no voice for the yelp)"
    if has("wheez"):
        put(wheeze(seed % 3), bus="vox", align=None, key=True, gain=2.0)
        return "auto: a wheeze"
    if hd("held breath") or has("breath held"):
        breath(m, "held", t, g0, pan=pan, label=lab)
        return "auto: a breath held"
    if (word("ragged", "gasp", "gasps", "intake", "inhale", "breath", "breathes", "panting")
            and not has("flame", "match's breath", "cold air", "fist")):
        kind = ("ragged" if word("ragged", "panting") else "gasp" if word("gasp", "gasps") else
                "in" if word("intake", "inhale", "sharp") else "out")
        breath(m, kind, t, g0 + 2.0, pan=pan, label=lab, semis=-2.0 if has("strained", "heave") else 0.0)
        return f"auto: breath ({kind})"
    # ---- the celesta is the ruby's glint's alone
    if has("celesta") and not has("not the celesta"):
        if m.sid == "s11" and has("glint", "ruby", "ping") and the_celesta(m, t, g0 + 2.0, pan, lab):
            return "auto: THE celesta (the ruby's glint)"
        put(hp(98, 0.6, seed), bus="music", room_=False)
        return "auto: a high harp note (the celesta is the ruby's alone)"
    if has("heartbeat"):
        dd = d or 0.6
        for k in range(max(1, int(round(dd / BEAT)))):
            m.put("music", OF.heart(0.26, k % 3), t + k * BEAT, g0, label=lab if k == 0 else None, hall=-24.0)
        return "auto: a heartbeat"
    # ---- beds
    if has("night air", "night street", "far wind", "a breath of wind"):
        dd = max(1.0, d or 3.0)
        put(night_bed(dd, seed % 3), gain=-6.0, bus="amb", room_=False, align=None)
        return "auto: the night air (no siren in it)"
    if hd("sewer bed") or has("water lapping", "the shaft's echo", "echoing drips"):
        put(DC.sewer_bed(round(max(1.0, d or 4.0), 2), seed % 3), gain=-6.0, bus="amb", room_=False, align=None)
        return "auto: the sewer"
    # ---- the foley the scenes name by tag, then by their words
    if hd("iron tick"):
        put(DC.metal_tap(seed % 3))
        return "auto: an iron tick"
    if hd("manhole scrape") or (word("manhole", "lid") and has("scrape", "grind", "slides off", "levered", "dragged")):
        put(DC.manhole_scrape(round(max(0.3, d or 0.6), 2), seed % 3), align=None, gain=-4.0 if has("across") else 0.0)
        return "auto: the manhole lid scraped"
    if hd("manhole clank") or (word("lid") and word("clank", "clanks")):
        put(DC.manhole_clank(seed % 3), gain=-3.0)
        return "auto: the manhole lid's clank"
    if hd("rung run", "rung up") or has("iron rungs", "rung steps"):
        dd = max(0.3, d or 1.0)
        gap = 0.22 if hd("rung up") or has("light") else 0.2 if hd("rung run") else 0.28
        n = max(2, int(round(dd / gap)))
        low = has("low", "going down")
        for k in range(n):
            x = DC.rung((seed + k) % 6)
            put(dsp.sos(x, "lowpass", 2500.0, 2) if low else x, at=t + k * gap, gain=-(0.8 * k if low else 1.5 * (k % 2)),
                label=k == 0)
        return "auto: iron rungs"
    if hd("rung") or has("first iron rung", "shoe on the top rung"):
        put(DC.rung(seed % 6))
        step(who(), at=t + 0.02, gain=-8.0, label=False)
        return "auto: a shoe on a rung"
    if hd("splash") or has("splash"):
        if has("steps off", "step off", "steps into"):
            m.put("feet", DC.water_step(seed % 8, 0.95), t, g0, pan=pan, label=lab)
            return "auto: a heavy step into the water"
        put(DC.splash_drop(seed % 3), room_=False)
        return "auto: a splash"
    if hd("water step") or has("slosh", "shallow water", "wading"):
        wt = {"knight": 0.75, "cracker": 0.55}.get(who(), 0.45)
        m.put("feet", DC.water_step(seed % 8, wt), t, g0, pan=pan, label=lab)
        return "auto: a step in water"
    if hd("drip") or has("drip"):
        put(DC.drip(seed % 5), room_=False)
        return "auto: a drip"
    if hd("hatch creak") or (has("hatch") and has("creak")):
        put(DC.hatch_creak(round(max(0.2, d or 0.8), 2), seed % 3), align=None)
        return "auto: the hatch creaks"
    if hd("hatch thud") or (has("hatch") and has("thud")):
        put(dsp.sos(DC.wood_thunk(seed % 3, 0.8), "lowpass", 1200.0, 2))
        return "auto: the hatch drops shut (muffled)"
    if hd("flashlight click") or has("flashlight", "small light clicks"):
        put(DC.flashlight_click(seed % 3), gain=-3.0 if has("softer") else 0.0)
        return "auto: a flashlight click"
    if hd("sink whoosh"):
        put(DC.sink_whoosh(round(max(0.4, d or 2.0), 2), seed % 3), room_=False, align=None)
        return "auto: a low whoosh, sinking"
    if hd("push whoosh") or has("low rising whoosh"):
        put(pitch(DC.rise_whoosh(round(max(0.4, d or 1.0), 2), seed % 3), -3.0), room_=False, align=None)
        return "auto: a low whoosh, rising"
    if hd("cat hiss") or has("cat's hiss"):
        put(DC.cat_hiss(seed % 3), align=None)
        return "auto: a cat's hiss"
    if hd("claws") or has("claws"):
        put(DC.claws(seed % 3), align=None)
        return "auto: claws scrabble"
    if hd("clatter") or has("clatter"):
        put(cut(DC.can_clatter(seed % 3), round(max(0.6, (d or 0.9) + 0.8), 2), 0.5))
        return "auto: the can clatters"
    if hd("tink") or has("tink"):
        if has("alarm", "bell"):
            put(DC.bell_tink(seed % 3, 0.22))
            return "auto: the bell's damped tink"
        put(DC.tin_tink(seed % 3))
        return "auto: a tin tink"
    if hd("heel scuff") or has("heel scuffs", "scuff"):
        m.put("feet", roomed(m, DC.heel_scuff(seed % 4, who()), t), t - STEP_PRE, g0, pan=pan, label=lab, sync=t)
        return "auto: a heel scuffs"
    if hd("knee"):
        put(DC.cloth(0.45, seed % 5, 0.6), align=None)
        put(sfx._thump(n_of(0.15), 160.0, 95.0, 0.008, 0.05), gain=-6.0, label=False)
        return "auto: a knee on the floor (a soft knock, cloth)"
    if hd("steth tock"):
        put(DC.metal_tap(seed % 3))
        return "auto: a tiny metallic tock"
    if hd("steth tick"):
        put(dsp.sos(DC.knob_tick(seed % 3), "lowpass", 2500.0, 2), gain=2.0)
        return "auto: a tick in the lock (through the stethoscope)"
    if hd("knob tick") or has("knurled"):
        put(DC.knob_tick(seed % 3))
        return "auto: a faint tick on the knob"
    if hd("dial spin") or (has("dial") and has("spin")):
        dd = round(min(max(d or 1.0, 0.3), 3.0), 2)
        fast = has("fast run") and not has("slowing", "creep")
        put(DC.dial_spin(dd, seed % 3, 40.0 if fast else 34.0, 14.0 if fast else 5.0), align=None)
        return "auto: the dial spun"
    if hd("gate click"):
        put(DC.gate_click(0 if has("low") else 2 if has("high") else 1, seed % 3))
        return "auto: a gate click"
    if hd("fence") or has("fence drops"):
        put(DC.fence_clunk(seed % 2))
        return "auto: the fence clunks"
    if hd("bolt run") or has("rolling metallic run", "bolts withdraw"):
        put(DC.bolt_run(10, 0.9, seed % 3), align=None)
        return "auto: the bolts run round the rim"
    if hd("bolt clack") or has("one clack"):
        put(DC.bolt_one(seed % 12), at=t - DC.BOLT_PRE, sync=t, align="peak")
        return "auto: one bolt (a clack)"
    if hd("lock bolt") or has("bolt draws back"):
        put(DC.bolt_slide(round(min(max(d or 0.35, 0.15), 0.8), 2), seed % 3), align=None)
        return "auto: the lock's bolt slides back"
    if hd("piece drop") or has("chest-piece drops"):
        put(DC.coat_tap(seed % 3))
        return "auto: the chest-piece taps his coat"
    if hd("wheel ratchet") or (has("wheel") and has("ratchet")):
        put(pitch(DC.dial_ratchet(round(min(max(d or 0.7, 0.3), 2.0), 2), seed % 3, 9.0), -12.0), align=None)
        return "auto: the great wheel's ratchet"
    if hd("hinge groan") or has("hinge groans"):
        put(DC.vault_groan(round(max(0.6, d or 2.0), 2), seed % 3), align=None)
        return "auto: the great hinge groans"
    if hd("door thud") or has("settles against its stop"):
        put(DC.door_thud(seed % 2))
        return "auto: the door settles (a deep thud)"
    if hd("steth clank") or (has("stethoscope") and has("clank")):
        put(DC.steth_clank(seed % 3))
        put(DC.ripple(seed % 3, 90.0, 0.9), at=t + 0.02, gain=-12.0, room_=False, label=False)
        return "auto: the stethoscope's clank"
    if hd("glove slap"):
        put(OF.slap(seed % 3))
        return "auto: gloved palms slap"
    if hd("belt creak"):
        dd = d or 0.4
        for k in range(max(1, int(dd // 2.0) + 1)):
            put(DC.glove_creak((seed + k) % 3, 0.35), at=t + 2.0 * k, gain=-1.5 * k, align=None, label=k == 0)
        return "auto: leather creaks"
    if hd("glove creak", "knob creak", "collar creak") or has("glove creaks", "leather creak", "gloves on iron"):
        put(DC.glove_creak(seed % 3, 0.4), align=None, gain=3.0)
        return "auto: leather creaks"
    if hd("coat", "cloth", "swish", "rustle", "pocket") or has("coat rustles", "coat's rustle", "coat swish", "cloth"):
        if has("paper"):
            put(cut(mono(fx("paper_rustle", seed=seed % 5)), round(min(max(d or 0.6, 0.3), 0.9), 2), 0.12), align=None)
            return "auto: paper rustle"
        put(DC.cloth(round(min(max(d or 0.45, 0.2), 1.0), 2), seed % 5, 1.0 if has("heavy", "coat") else 0.3),
            align=None, gain=2.0)
        return "auto: cloth"
    if (hd("footstep", "step", "heel") or has("a footstep", "a soft step", "heel on the stone", "heels:", "steps off the wall")
            or (has("boots") and not has("grating"))):
        if has("water", "slosh"):
            m.put("feet", DC.water_step(seed % 8, 0.6), t, g0, pan=pan, label=lab)
            return "auto: a step in water"
        w = ("her", "cracker", "knight")[seed % 3] if hd("crew") else who()
        steel = has("steel")
        lp = 1500.0 if has("far footstep", "inside the bank", "muffled") else None
        step(w, steel=steel, lp=lp)
        if has("two steps", ": two", "steps off the wall"):
            step(w, k=1, at=t + 0.42, gain=-1.0, steel=steel, lp=lp, label=False)
        return f"auto: a footstep ({w}{', steel' if steel else ''})"
    # ---- the street and the cars (the police are cars: sirens, engines, brakes, doors)
    if has("grating"):
        put(grating_clank(seed % 6))
        return "auto: boots on the iron grating"
    if has("kicks the tyre", "tyre"):
        put(tyre_kick(seed % 3))
        return "auto: a boot into a tyre"
    if has("car door"):
        if has("open", "flung", "shoved"):
            put(car_door_open(seed % 3))
            return "auto: a car door opened"
        put(fx("car_door_close", seed=seed % 5), wet=-10.0)
        return "auto: a car door slams"
    if has("engine", "starter"):
        if has("cough", "dies", "starter"):
            put(cough_die(seed % 4), align=None)
            return "auto: the starter, a cough, it dies"
        if has("catches", "roar"):
            put(engine_catch(round(max(1.0, d or 4.0), 2), seed % 3))
            return "auto: the engine catches"
        if has("revs"):
            put(rev_hard(0.9, seed % 3))
            return "auto: the engine revs"
        put(bed("engine_idle", max(1.0, d or 3.0), seed % 3, lp=1800.0, rpm=760), bus="amb", gain=-8.0, align=None)
        return "auto: an engine idling"
    if has("brakes", "shriek", "squeal"):
        put(DC.tyre_squeal(0.55, seed % 3, 2300.0, 0.25), align=None)
        return "auto: tyres squeal"
    if has("whoop"):
        put(DC.police_whoop(seed % 3, 880.0), align=None)
        return "auto: a siren whoop"
    if has("siren"):
        dd = max(1.0, d or 3.0)
        put(env(far(DC.sirens(dd, seed % 7), 1800.0), [(0.0, 0.0), (dd * 0.6, 1.0), (dd, 1.0)]), gain=-4.0, room_=False,
            align=None)
        return "auto: sirens, far (cars)"
    if has("alarm bell", "the bell"):
        dd = max(0.5, d or 2.0)
        x = alarm(dd, t, seed % 5, 0.3)
        if has("far", "faint", "through the walls"):
            x = far(x, 800.0)
        put(dsp.fade(x, 0.05, 0.3), room_=True, align=None, gain=-2.0)
        return "auto: the alarm bell"
    if word("sack", "sacks", "gold"):
        if has("spill"):
            put(gold_spill(seed % 5, 6, 0.7))
            return "auto: a sack dropped, the gold spilling"
        for k in range(2 if has("sacks", "two", "both") else 1):
            put(DC.gold_bag((seed + k) % 5), at=t + 0.04 * k, gain=-2.0 * k, label=k == 0)
        return "auto: sacks of gold"
    if word("match", "matches"):
        if has("shaken out"):
            put(match_out(seed % 3))
            return "auto: the match shaken out"
        if has("scratch"):
            x = DC.match_scratch(seed % 3)
            put(x, at=t - onset_at(x), sync=t)
            return "auto: a match scratched"
        if has("flare", "strike"):
            x = fx("match_flare", seed=seed % 3)
            put(x, at=t - onset_at(x), sync=t)
            return "auto: the match flares"
        put(DC.flame_bed(round(max(0.5, d or 2.0), 2), seed % 3), bus="amb", gain=-8.0, room_=False, align=None)
        return "auto: the match's breath"
    if has("torch"):
        if has("lights", "pop"):
            put(torch_pop(seed % 3))
            return "auto: the torch lit"
        put(DC.torch_cut(round(max(0.3, d or 0.6), 2), seed % 3), align=None)
        return "auto: the torch cuts"
    if word("stone", "block", "tile", "slab"):
        if has("set", "settl", "thud", "down"):
            put(DC.tile_set(seed % 3))
            return "auto: the stone set down"
        put(DC.tile_scrape(seed % 3), align=None)
        return "auto: stone grinding"
    if word("knock", "knocks"):
        put(DC.hollow_knock(seed % 2))
        return "auto: a hollow knock"
    if has("heel") and has("tap", "click"):
        put(DC.heel_tap(seed % 3))
        return "auto: a heel tap"
    if has("boom"):
        put(DC.pound(seed % 3) if has("fist", "muffled") else DC.vault_boom(seed % 2), room_=False)
        return "auto: BOOM"
    if has("bang"):
        put(fx("impact", seed=seed % 5), room_=False)
        return "auto: BANG"
    if has("glassy tick", "spectacles"):
        put(OF.glass_tick(seed % 3), room_=False)
        return "auto: a glassy tick"
    # ---- the table, the title, the paper
    if has("pencil"):
        put(dsp.sos(DC.chalk_scratch(round(max(0.3, d or 0.6), 2), seed % 7, circle=has("circle"), press=0.5), "lowpass",
                    6000.0, 2), align=None)
        return "auto: a soft pencil scratch"
    if has("whoosh-thud", "whoosh and a thud"):
        put(DC.whoosh_thud(0.24, seed % 3, 0.6 if has("harder", "red") else 0.0), room_=False, align=None)
        return "auto: whoosh-thud"
    if has("stamp"):
        put(DC.stamp(seed % 2), room_=False)
        return "auto: stamp"
    if has("paper", "plan unrolled", "unroll"):
        if has("unroll", "spread"):
            put(DC.paper_unroll(round(max(0.5, d or 1.0), 2), seed % 3), align=None, room_=False)
            return "auto: paper unrolled"
        if has("tear", "torn"):
            put(DC.paper_torn(0.55, seed % 5), align=None, room_=False)
            return "auto: paper torn"
        if has("snap"):
            put(OF.paper_snap(seed % 5), room_=False)
            return "auto: a paper snap"
        if has("whoosh", "swish", "slide"):
            put(DC.paper_whoosh(round(max(0.3, d or 0.5), 2), seed % 5), align=None, room_=False)
            return "auto: a paper swish"
        put(cut(mono(fx("paper_rustle", seed=seed % 5)), round(min(max(d or 0.6, 0.3), 0.9), 2), 0.12), align=None)
        return "auto: paper rustle"
    if has("squeak"):
        put(OF.squeak(round(min(max(d or 0.4, 0.2), 0.8), 2), seed % 3), align=None)
        return "auto: a marker's squeak"
    if has("pops", " pop"):
        put(OF.soft_hit(hz(62), seed % 3), bus="music", room_=False)
        return "auto: a soft pop"
    if word("cigarette", "crackle", "crackles", "ember"):
        put(cut(fx("ember_sizzle", seed=seed % 5), round(max(0.4, d or 0.8), 2), 0.3), align=None)
        return "auto: the cigarette's crackle"
    if has("radio"):
        put(far(OF.radio(round(max(1.0, d or 2.0), 2), seed % 3), 1500.0), bus="amb", align=None, gain=-4.0)
        return "auto: a radio through the wall"
    if word("lamp", "lamps"):
        if has("goes out", "off", "click"):
            put(OF.switch(seed % 3))
            return "auto: a lamp's click"
        put(DC.lamp_on(seed % 3, round(max(0.5, d or 1.5), 2)), align=None)
        return "auto: a lamp comes on (a tick, a hum)"
    if word("chain", "chains"):
        if has("rattle"):
            put(chain_rattle(seed % 3))
            return "auto: the chain rattles"
        put(DC.chain_creak(round(max(0.5, d or 2.0), 2), seed % 3), align=None)
        return "auto: the chain creaks"
    if has("door") and has("clos", "soft"):
        put(soft_door(seed % 3))
        return "auto: a door closed softly"
    if has("chair"):
        put(OF.creak(0.4, seed % 4), align=None)
        return "auto: a chair creaks"
    if word("pats"):
        for k in range(2):
            put(pat(k), at=t + 0.16 * k, gain=-2.0 * k, label=k == 0)
        return "auto: two pats"
    if has("whoosh"):
        dd = round(max(0.3, min(d or 0.5, 1.5)), 2)
        x = DC.rise_whoosh(dd, seed % 3)
        put(x[::-1] if has("reverse") else x, room_=False, align=None)
        return "auto: a whoosh"
    if has("creak"):
        put(OF.creak(0.35, seed % 4), align=None)
        return "auto: a creak"
    if has("click"):
        put(OF.switch(seed % 3))
        return "auto: a click"
    if has("thud"):
        put(DC.strip_thud(seed % 4))
        return "auto: a thud"
    if has("clank"):
        put(DC.manhole_clank(seed % 3))
        return "auto: a clank"
    if word("wind", "winds"):
        put(bed("wind_gust", max(1.0, d or 2.0), seed % 3, lp=2000.0), bus="amb", gain=-4.0, room_=False, align=None)
        return "auto: wind"
    if has("city"):
        put(night_bed(max(1.0, d or 2.0), seed % 3), bus="amb", gain=-4.0, room_=False, align=None)
        return "auto: the far city"
    # ---- the score
    if has("theme", "ostinato", "inversion", "inverted", "upright", "phrase"):
        if m.music_at(t):
            m.mark(t, lab)
            return "auto: the score plays here"
        notes = INVERSION if has("invers", "inverted") else THEME_MAJOR if has("major") else THEME
        pluck_line(m, t, notes, "harp", g0, pan=pan, stop=4, label=lab, seed=seed)
        return "auto: the theme's head (harp)"
    if has("pizzicato", "plucked", "pluck"):
        if has("descend", "descent", "run"):
            for k, p in enumerate((73, 69, 65, 62, 61, 57)):
                put(pz(p, 0.8, seed + k), bus="music", at=t + E16 * k, room_=False, label=k == 0)
            return "auto: a pizzicato run, descending"
        p = (HIS + 12 if has("low", "c#", "c sharp", "his") else MID if has("middle", "viola") else HER_P)
        put(pz(p, 0.85, seed), bus="music", room_=False)
        return f"auto: a pizzicato {nm(p)}"
    if has("braam"):
        put(fx("braam", seed=seed % 3), bus="music", room_=False, align=None)
        return "auto: a braam"
    if word("sting", "stab", "stabs"):
        put(stab(PSY, seed % 5, low=has("low")), bus="music", room_=False)
        return "auto: a string stab"
    if has("tremolo"):
        dd = max(0.5, d or 2.0)
        put(env(trem(PSY, dd, 0.6, seed), [(0.0, 0.4), (dd, 1.0)]), bus="music", room_=False, align=None)
        return "auto: a tremolo"
    if has("swell"):
        dd = max(0.5, d or 1.5)
        put(held(PSY, dd, 0.7, seed, octaves=(0, 1), attack=dd * 0.8, release=0.4), bus="music", room_=False, align=None)
        return "auto: a string swell"
    if has("glissando"):
        dd = max(0.4, d or 1.0)
        put(harm(93, dd, 0.6, seed, bend=lambda u, dd=dd: -5.0 * np.sin(np.pi * np.clip(u / dd, 0, 1))), bus="music",
            room_=False, align=None)
        return "auto: a harmonic glissando"
    if has("harmonic"):
        put(harm(93, max(0.3, d or 0.8), 0.6, seed, attack=0.05), bus="music", room_=False, align=None)
        return "auto: a string harmonic"
    if has("shimmer"):
        put(shimmer(max(0.4, d or 0.8), seed % 5, 93), bus="music", room_=False, align=None)
        return "auto: a string shimmer"
    if has("chime"):
        if has("deep", "midnight", "clock"):
            put(OF.bell(hz(50), seed % 3, 4.0), bus="music", room_=False)
            return "auto: a deep bell chime"
        put(OF.chime(hz(86), seed % 3, 4.0), bus="music", room_=False)
        return "auto: a chime"
    if has("gong"):
        put(OF.gong(hz(38), seed % 3), bus="music", room_=False)
        return "auto: a low gong"
    if has("soft bell"):
        put(OF.bell(hz(81), seed % 3), bus="music", room_=False)
        return "auto: a soft bell"
    if has("held note", "low note", "low held", "pedal", "cello", "low string"):
        p = HIS if has("c#", "c sharp", "his") else 38
        dd = max(0.4, d or 1.5)
        put(bow([(0.0, p)], dd, 0.8, seed, octaves=(0, 1), attack=0.15, release=0.6), bus="music", room_=False, align=None)
        return f"auto: a low held {nm(p)}"
    if has("violin", "high held", "high string"):
        dd = max(0.4, d or 1.0)
        put(harm(HER, dd, 0.7, seed, attack=0.2), bus="music", room_=False, align=None)
        return "auto: her D, high"
    if has("chord"):
        dd = max(0.5, d or 2.0)
        put(held((38, 50, 54, 57, 61) if has("major") else PROG[0][1], dd, 0.7, seed, octaves=(0, 1), attack=0.1,
                 release=1.0), bus="music", room_=False, align=None)
        return "auto: a held chord"
    if word("note", "notes"):
        put(pz(HER_P, 0.8, seed), bus="music", room_=False)
        return "auto: a plucked note"
    if word("tick", "ticks"):
        put(OF.tick(seed % 2), gain=-4.0)
        return "auto: a dry tick"
    return "not realised: no rule for its words"


# ============================================================================ the mix
def mixdown(m):
    """The buses to one mix: the music's plate (the hall bus), the music ducked a little under the
    voices and breath; the stems kept (QA, --stems)."""
    def duck(x, depth):
        return dsp.sidechain_duck(x, m.key, depth_db=depth, thresh_db=-44.0, attack=0.03, release=0.35)
    music = duck(m.b["music"].astype(np.float64), -4.0)
    plate = duck(dsp.reverb(m.b["hall"].astype(np.float64), "plate", wet_db=0.0, dry=0.0, seed=7)[:N], -4.0)
    stems = {"music": music + plate}
    for k in ("amb", "efx", "vox", "feet", "tick"):
        stems[k] = m.b[k].astype(np.float64)
    mix = sum(stems.values())
    m.stems = {k: v.astype(np.float32) for k, v in stems.items()}
    return mix


def master(mix, t_silence, target=-16.0, ceiling=-1.4):     # 0.1 dB under the -1.3 dBTP spec: meters differ
    """High-pass; a short fade into digital silence at t_silence; loudness to target; a true-peak
    limiter (iterated: it takes a little loudness back)."""
    mix = dsp.sos(np.asarray(mix, np.float64), "highpass", 30.0, 2)
    a = int(round(t_silence * SR))
    fl = n_of(0.35)
    if 0 < a <= len(mix):
        k = min(fl, a)
        mix[a - k:a] *= (np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, k)) ** 2)[:, None]
        mix[a:] = 0.0
    gain = target - dsp.loudness_integrated(mix)
    out, gr = mix, np.ones(1)
    for _ in range(6):
        out, gr = dsp.limiter(mix * db2lin(gain), ceiling_db=ceiling, return_gain=True)
        out[a:] = 0.0
        lufs = dsp.loudness_integrated(out)
        if abs(lufs - target) < 0.03:
            break
        gain += target - lufs
    out[a:] = 0.0
    out = dsp.fade(out, 0.004, 0.0)
    master.gain = gain
    master.gr = float(dsp.lin2db(max(float(np.min(gr)), 1e-9)))
    if len(out) < N:
        out = np.concatenate([out, np.zeros((N - len(out), 2))])
    return out[:N]


# ============================================================================ QA
find_clicks, onsets = DC.find_clicks, DC.onsets
CLOCKS = (("the wall clock (s02-s03)", 14.0, 46.5), ("the bank's clock (s04-s06)", BANK_TICK[0], BANK_TICK[1]))


def grid_off(t):
    """Seconds from film time t to the nearest straight eighth note."""
    return t - round(t / E8) * E8


def qa(m, t_sil, outdir, path):
    import soundfile as sf
    os.makedirs(outdir, exist_ok=True)
    info = sf.info(path)
    y, sr = sf.read(path, dtype="float64", always_2d=True)
    gm = db2lin(getattr(master, "gain", 0.0))
    R = {"file": dict(path=os.path.relpath(path, ROOT), sr=sr, channels=y.shape[1], subtype=info.subtype,
                      samples=len(y), seconds=len(y) / sr)}
    print("\n================ QA:", path)
    R["lufs"], R["tp"], R["peak"] = dsp.loudness_integrated(y), dsp.true_peak_db(y), dsp.sample_peak_db(y)
    print(f"  file: {sr} Hz, {y.shape[1]} ch, {info.subtype}, {len(y)} samples = {len(y) / sr:.4f} s (the film: {DUR:.4f} s)")
    print(f"  integrated {R['lufs']:.2f} LUFS (-16 +-0.1)   true peak {R['tp']:.2f} dBTP (<= -1.3)   sample peak "
          f"{R['peak']:.2f} dBFS   master gain {master.gain:+.1f} dB, limiter at most {master.gr:.1f} dB")
    a = int(round(t_sil * SR))
    R["silent_from"], R["silent_tail"] = t_sil, bool(np.all(y[a:] == 0.0))
    nz = np.nonzero(np.any(y != 0.0, axis=1))[0]
    R["last_sound"] = float((nz[-1] + 1) / SR) if len(nz) else 0.0
    print(f"  digital silence from {t_sil:.3f} s to the end: {R['silent_tail']} (last non-zero sample at "
          f"{R['last_sound']:.4f} s)")
    keys = list(m.stems)
    print("  per scene:  LUFS  short-max  peak | per bus, LUFS at the master's gain: " + " ".join(f"{k:>5s}" for k in keys))
    R["scenes"] = {}
    for sid, s0, d in SCENES:
        i0, i1 = int(round(s0 * SR)), int(round((s0 + d) * SR))
        seg = y[i0:i1]
        lu = dsp.loudness_integrated(seg) if np.any(seg) else -99.0
        _, st = dsp.loudness_curve(seg, win=3.0, hop=0.25) if len(seg) > 3 * SR else (None, np.array([lu]))
        parts = []
        for k in keys:
            s_ = m.stems[k][i0:i1].astype(np.float64) * gm
            parts.append(dsp.loudness_integrated(s_) if np.any(s_) else -99.0)
        R["scenes"][sid] = dict(lufs=lu, short_max=float(np.max(st)), peak=dsp.sample_peak_db(seg),
                                tp=dsp.true_peak_db(seg), buses=dict(zip(keys, parts)), status=STATUS.get(sid))
        print(f"   {sid} {s0:5.0f}  {lu:6.1f}  {np.max(st):6.1f}  {dsp.sample_peak_db(seg):6.1f} | "
              + " ".join(f"{p:5.0f}" for p in parts) + f"   {STATUS.get(sid, '?')}")
    print("  whole film, per bus (LUFS / peak dBFS at the master's gain): " + ", ".join(
        f"{k} {dsp.loudness_integrated(m.stems[k].astype(np.float64) * gm) if np.any(m.stems[k]) else -99:.1f}/"
        f"{dsp.sample_peak_db(m.stems[k].astype(np.float64) * gm):.1f}" for k in keys))
    # the clocks (the tick bus): a tick on every beat of their stretch, nothing outside them
    tk = m.stems["tick"].astype(np.float64)
    on = onsets(tk, 0.12, 0.3)
    R["clocks"] = []
    inside = np.zeros(len(on), bool)
    for name, c0, c1 in CLOCKS:
        want = [k * BEAT for k in range(int(math.ceil(c0 / BEAT - 1e-9)), int(math.ceil(c1 / BEAT - 1e-9)))]
        sel = (on >= c0 - 0.05) & (on < c1 + 0.05)
        inside |= sel
        got = on[sel]
        off = [min(abs(o - w) for w in want) for o in got] if len(got) and want else []
        placed = [x for x in m.ticks if c0 - 1e-6 <= x < c1 - 1e-6]
        R["clocks"].append(dict(name=name, want=len(want), placed=len(placed), measured=int(len(got)),
                                worst_ms=1000 * max(off) if off else None))
        print(f"  {name}: {len(placed)} ticks placed, {len(got)} measured (want {len(want)}, a beat from {c0:.1f} to "
              f"{c1:.1f} s); worst offset from the beat {1000 * max(off) if off else 0:.1f} ms")
    R["ticks_outside"] = int(np.sum(~inside))
    print(f"  ticks measured outside the clocks' stretches: {R['ticks_outside']}")
    # the celesta: one note, the ruby's glint
    R["celesta"] = dict(n=len(m.celesta), at=[round(x, 3) for x in m.celesta])
    ok = len(m.celesta) == 1 and abs(m.celesta[0] - (START.get("s11", 166.0) + 1.5)) < 1e-6
    print(f"  THE CELESTA: {len(m.celesta)} note(s), at {R['celesta']['at']} ({'the ruby glint only: OK' if ok else 'CHECK'})")
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
        st_ = sorted(((k, 20 * np.log10(np.abs(m.stems[k][i]).max() * gm + 1e-12)) for k in keys), key=lambda kv: -kv[1])[:3]
        top = sorted((sp for sp in m.spans if sp[1] <= tt <= sp[2] and sp[0] != "tick"), key=lambda sp: -sp[5])[:3]
        R["peaks"].append(dict(t=tt, db=float(20 * np.log10(pe[i] + 1e-12)), stems=st_))
        print(f"   {tt:8.3f} {20 * np.log10(pe[i] + 1e-12):+5.1f} | " + " ".join(f"{k} {v:+.1f}" for k, v in st_)
              + " | " + "; ".join(f"{sp[0]}:{sp[3] or '-'}@{sp[4]}" for sp in top))
    # silences: 50 ms windows under -60 dBFS for more than half a second, before the black
    w = n_of(0.05)
    nb = a // w
    rms = 20 * np.log10(np.sqrt(np.mean(np.square(y[:nb * w]).reshape(nb, w, 2), axis=(1, 2))) + 1e-12)
    runs, s_ = [], None
    for k, q in enumerate(list(rms < -60.0) + [False]):
        if q and s_ is None:
            s_ = k
        elif not q and s_ is not None:
            if (k - s_) * 0.05 > 0.5:
                runs.append((s_ * 0.05, k * 0.05))
            s_ = None
    R["silences"] = runs
    print(f"  silences under -60 dBFS longer than 0.5 s before {t_sil:.2f} s: "
          + (", ".join(f"{p:.2f}-{q:.2f}" for p, q in runs) or "none"))
    # clicks
    clicks = find_clicks(y, max_report=400)
    hits = np.array(sorted(m.starts))
    sus = [(t, sc) for t, sc in clicks if not len(hits) or not np.any((t - hits > -0.003) & (t - hits < 0.08))]
    by = {}
    stem_clicks = {k: np.array([t for t, _ in find_clicks(m.stems[k].astype(np.float64) * gm, max_report=4000)])
                   for k in keys}
    for t, sc in sus:
        src_ = [k for k in keys if len(stem_clicks[k]) and np.min(np.abs(stem_clicks[k] - t)) < 0.003]
        by.setdefault("+".join(src_) or "the mix only", []).append((t, sc))
    R["clicks"] = {k: len(v) for k, v in by.items()}
    print(f"  click detector: {len(clicks)} transients, {len(sus)} not at the start of a placed sound; by stem: "
          + ", ".join(f"{k} {len(v)}" for k, v in sorted(by.items(), key=lambda kv: -len(kv[1]))))
    for k, v in sorted(by.items()):
        if k not in ("efx", "feet", "efx+feet"):
            print(f"    {k}: " + ", ".join(f"{t:.3f}({sc:.0f})" for t, sc in v[:12]))
    ends = [e for e in m.edges if e[4] > 0.1]
    R["cut_off"] = len(ends)
    print(f"  placements cut off loud at their end (no real fade): {len(ends)}"
          + "".join(f"\n    {sid} {t:8.3f} {bus:5s} end {e1:4.2f}  {lab}" for sid, t, lab, e0, e1, bus in ends[:12]))
    cuts = []
    for sid, s0, _ in SCENES[1:]:
        i0 = int(round(s0 * SR))
        ww = y[i0 - n_of(0.004): i0 + n_of(0.004)]
        cuts.append(f"{s0:.0f}:{float(np.max(np.abs(np.diff(ww, axis=0)))) if len(ww) > 1 else 0:.3f}")
    print("  largest sample step within 4 ms of each cut:", " ".join(cuts))
    # the cues
    n_sec = sum(1 for r in m.report if r[2] == "section")
    n_auto = sum(1 for r in m.report if r[2].startswith("auto"))
    n_sil = sum(1 for r in m.report if r[2].startswith(("silence", "the clock")))
    miss = [r for r in m.report if not (r[2] == "section" or r[2].startswith(("auto", "silence", "the clock")))]
    per = {}
    for sid, c, how in m.report:
        p = per.setdefault(sid, dict(cues=0, sections=0, auto=0, nothing=0, missed=0))
        p["cues"] += 1
        key = ("sections" if how == "section" else "auto" if how.startswith("auto") else
               "nothing" if how.startswith(("silence", "the clock")) else "missed")
        p[key] += 1
    R["cues"] = dict(total=len(m.report), sections=n_sec, auto=n_auto, silence=n_sil, missed=len(miss), per_scene=per,
                     not_realised=[dict(sid=sid, t=c["t"], cue=c["sfx"], why=how) for sid, c, how in miss],
                     auto_list=[dict(sid=sid, t=c["t"], cue=c["text"][:90], how=how) for sid, c, how in m.report
                                if how.startswith("auto")])
    print(f"  cues: {len(m.report)}: realised by the sections {n_sec}, auto-spotted from their words {n_auto}, "
          f"silence or the clock {n_sil}, NOT REALISED {len(miss)}")
    print("    per scene: " + "; ".join(f"{sid} {p['cues']} ({p['sections']}/{p['auto']}/{p['nothing']}/{p['missed']})"
                                       for sid, p in per.items()))
    for sid, c, how in miss:
        print(f"    MISSED {sid} {c['t']:.3f} {c['sfx']!r}: {how}")
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
    ms = [sp for sp in m.spans if sp[0] == "music"]
    offs = [grid_off(sp[1]) for sp in ms]
    on_grid = sum(1 for o in offs if abs(o) <= 0.015)
    R["music_grid"] = dict(n=len(ms), on=on_grid)
    print(f"  music on the straight-eighth grid: {on_grid} of {len(ms)} note starts within 15 ms "
          f"({100.0 * on_grid / max(1, len(ms)):.0f} %); off it (picture hits): "
          + ", ".join(sorted({f'{sp[1]:.2f}' + (f' {sp[3]}' if sp[3] else '') for sp, o in zip(ms, offs)
                              if abs(o) > 0.015 and sp[3]})[:14]))
    R["status"], R["warnings"] = dict(STATUS), list(WARN)
    R["from_bible"] = {k: sorted(set(v)) for k, v in FROM_BIBLE.items()}
    with open(os.path.join(outdir, "qa.json"), "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    overview(y, m, outdir, t_sil)
    return R


def overview(y, m, outdir, t_sil):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import signal
    x = y.mean(axis=1)
    fig, ax = plt.subplots(5, 1, figsize=(26, 15), dpi=70, sharex=True,
                           gridspec_kw=dict(height_ratios=[1.0, 2.0, 1.1, 1.1, 0.5]))
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
    ax[2].plot(tm, lm, color="#999", lw=0.6, label="momentary")
    ax[2].plot(ts, ls, color="#c60", lw=1.6, label="short-term")
    ax[2].axhline(-16, color="#060", lw=0.8, ls="--")
    ax[2].set_ylim(-50, -5)
    ax[2].set_ylabel("LUFS")
    ax[2].legend(loc="lower right", fontsize=9)
    gm = db2lin(getattr(master, "gain", 0.0))
    cols = dict(music="#1f5fa8", efx="#c0392b", amb="#7f8c8d", vox="#8e44ad", feet="#a0522d", tick="#000000")
    for k_, st in m.stems.items():
        if not np.any(st):
            continue
        tb, lb = dsp.loudness_curve(st.astype(np.float64) * gm, win=1.0, hop=0.1)
        ax[3].plot(tb, lb, color=cols.get(k_, "#333"), lw=1.0, label=k_)
    ax[3].set_ylim(-60, -5)
    ax[3].set_ylabel("per bus (1 s)")
    ax[3].legend(loc="lower right", ncol=6, fontsize=9)
    for e in m.ev:
        ax[4].plot([e["t"], e["t"]], [0, 1], color="#c00" if e["bus"] == "music" else "#036", lw=0.5)
    for tk in m.ticks:
        ax[4].plot([tk, tk], [0, 0.3], color="#000", lw=0.4)
    for tc in m.celesta:
        ax[4].plot([tc, tc], [0, 1], color="#f0a", lw=2.0)
    ax[4].set_yticks([])
    ax[4].set_ylabel("events")
    for a in ax:
        for sid, s0, d in SCENES:
            a.axvline(s0, color="#0a0", lw=1.0)
        a.axvline(t_sil, color="#e00", lw=0.8, ls=":")
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
    mix = mixdown(m)
    t_sil = silence_from()
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
    out = master(mix, t_sil)
    path = os.path.join(out_dir, "audio_master.wav")
    sf.write(path, out, SR, subtype="PCM_24")
    y, _ = sf.read(path, dtype="float64", always_2d=True)
    print(f"{path}: {len(y) / SR:.3f} s, {dsp.loudness_integrated(y):.2f} LUFS, TP {dsp.true_peak_db(y):.2f} dBTP; "
          f"{time.time() - w0:.0f} s wall, {time.process_time() - c0:.0f} s CPU")
    n_auto = sum(1 for r in m.report if r[2].startswith("auto"))
    miss = [r for r in m.report if not (r[2] == "section" or r[2].startswith(("auto", "silence", "the clock")))]
    print(f"cues: {len(m.report)} ({len(m.report) - n_auto - len(miss)} by the sections, {n_auto} auto-spotted, "
          f"{len(miss)} not realised)")
    print("scenes: " + "; ".join(f"{sid} {STATUS.get(sid, '?')}" for sid, _, _ in SCENES))
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
    if a.qa:
        qa(m, t_sil, a.qa, path)
    print(f"done: {time.time() - w0:.0f} s wall, {time.process_time() - c0:.0f} s CPU")


if __name__ == "__main__":
    main()
