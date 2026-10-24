"""DOUBLE CROSS: the complete score and sound, locked to the scene modules.

    cd productions/silhouette-noir
    python3 films/double_cross/audio/mix.py                   # -> films/double_cross/out/audio_master.wav
    python3 films/double_cross/audio/mix.py --qa DIR          # ... and measure it (report, overview PNG in DIR)
    python3 films/double_cross/audio/mix.py --only s05,s07    # just these sections (a quick listen; not mastered
                                                              #   to the film, written to out/audio_only.wav)
    python3 films/double_cross/audio/mix.py --stems DIR       # ... and the stems, at the master's gain
    python3 films/double_cross/audio/mix.py --without s06     # treat s06 as missing (it is played from the bible)
    python3 films/double_cross/audio/mix.py --skip-missing    # leave missing scenes silent instead

48 kHz stereo, exactly the timeline's 144 s, integrated -16 LUFS, true peak under -1 dBTP, and
digital silence once the picture is black (s11, 143.5 s) to the end.

A missing scene module is played from the bible (its beats and cues as the bible gives them: a
"stand-in"); a module that does not import, or whose cues() gives no cues yet (a draft), is
played from the bible too, and one whose cues() fails is spotted from the bible's cues;
a module's beat that is missing or of the wrong kind is taken from the bible. Every beat a
section uses is looked up in this order: the module's constant (by name), else the module's own
cue whose words match (nearest the bible's time), else the bible's time. Every cue no section
answered within a frame is realised from its words (and reported), so a re-run after the scenes
change still covers every cue. Nothing is fetched; everything is synthesised here (or cut from
films/opposite/audio/gen, and from the voices' own takes in audio/gen: the briefing's murmur, the
Knight's grunts, her breath of a laugh), deterministically: the same scenes give the same file, bit
for bit.

THE SCORE is heist jazz at 120 bpm in D minor, one piece from the first chalk tap to the last
chord: a beat is 0.5 s, a bar 2 s, and every scene starts on a bar line (bar b starts at 2b s).
The band: a walking upright bass (pizzicato; arco for the held notes), brushes on a snare (the
left hand's sweep, the right hand's taps, the bass drum feathered, the hi-hat's foot on 2 and 4),
vibraphone (its motor's tremolo one global clock), muted trumpets (Harmon), a cup-muted trombone
for the low brass, a low felt piano. The eighths swing (the off-beat at 64 % of the beat).

THE THEME (vibraphone; beats in the 16-beat phrase; D Dorian with C# as the leading tone):

    | D4 . A4 . . G4 F4 . | E4 F4 G4 . E4 . C4 . | D4 . C5 . . B4 A4 . | G4 E4 C#4 . D4 . . . |
        Dm6                   Bb7(#11)               G13                    A7(b9)    Dm9

  its exact mirror inversion about D4 (every interval turned upside down: low, and still minor,
  with E-flat for C-sharp: a Phrygian close):

    | D4 . G3 . . A3 B3 . | C4 B3 A3 . C4 . E4 . | D4 . E3 . . F3 G3 . | A3 C4 Eb4 . D4 . . . |
        Dm6                   Am9                    Gm9                    Am7b5     Dm9

  and the inversion inverted (upright again) in D major:

    | D4 . A4 . . G4 F#4 . | E4 F#4 G4 . E4 . C#4 . | D4 . C#5 . . B4 A4 . | G4 E4 C#4 . D4 . . . |
        D6/9                   Em9    A13               Gmaj9                  A13       D6/9

    bars   film s    scene  the score
    0- 5     0- 12   s01    four chalk taps count it in on the bank at night; the bass walks in as the
                            street folds flat (card snaps) and the camera tilts up to the blueprint;
                            a vibraphone note per ruled line, up the D minor-major chord; the strips
                            and the stamps hit with the band (the spy chord, D minor-major 7); the X
                            lands; the bass walks down into the lamp.
    6-11    12- 24   s02    a bar of vamp, then THE THEME, plainly, vibraphone; the knight's slam on
                            its third bar; bar 11: the band stops on a low held D: she knows.
   12-19    24- 40   s03    THE THEME twice more: vibraphone with a muted trumpet in unison as she
                            chalks the route (pieces clack on the beat), then vibraphone alone; it
                            thins out for the plant (the dot); a swell into the tilt.
   20-25    40- 52   s04    the pop-up: a rising piano run; the heist groove (trumpet calls the
                            theme's head, vibraphone answers); from 46.0 THE CLOCK, a dry woodblock
                            on every beat.
   26-32    52- 66   s05    the score drops away to the tick (the corridor's room tone, the building
                            humming on D); the stealth map: a tiptoe bass under the plan's tocks, a
                            vibe note (D, F, A) per piece hopping the gap; the CLANK ends it; the
                            score holds its breath (one low muted G#, an arco D under it); the cat,
                            the can; bar 32: the band creeps back for the push to the dial.
   33-39    66- 80   s06    the vault door: low piano, an arco D; the dial: a tiptoe pizzicato, the
                            dial spun under the clock, the gates click D, F, A on their beats and the
                            vibraphone answers on the off-beat; the fence: CLUNK, the chord together;
                            the bolts round the rim: a brush roll; the door swings: a brass swell on
                            B-flat major, onto gold, rising into s07.
   40-47    80- 96   s07    gold: a hot groove; the glint; his look; bars 42-45 THE INVERSION, low
                            and minor (vibraphone, trombone, piano octaves), peaking from 86 as the
                            frame splits; its Phrygian close lands, and the vault door BOOMs on the
                            bar line (92); bars 46-47 the inversion's head again, exposed over the
                            alarm; the clock stops dead at 93.5.
   48-53    96-108   s08    sparse: black, ragged breath; the match; muffled pounding; one low note
                            for her calm; the hollow knock; the tracing paper; a swell into s09.
   54-61   108-124   s09    the rewind: the film's own mix (back through s08..s02 as s09's REWIND rows
                            say), reversed and sped up under a tape scrub and the clock ticking
                            backwards; it catches and plays his slam and her dot; freezes stop it
                            dead; Plan B chalked over D major (the police: muted stabs rising a
                            semitone a car; the red X on a low A); from its cue (on the next beat)
                            THE THEME upright in D MAJOR, under the vault, the ladder, the cut
                            running on along the pipe and Plan B's line lighting (rising tings).
   62-67   124-136   s10    his getaway: the band drives under his run and stops dead on the door's
                            slam; the starter coughs in the clear; it catches on bar 63 and the
                            trumpets come in hot on the theme's head; bar 64 a muted stab per police
                            car, rising a semitone each, the sirens (tuned D-A) braiding over them;
                            bar 65 CHECKMATE (a hard low stab, a choked cymbal, his heart); bar 66
                            the back street (rungs, the lid, soft steps) under the theme in D major,
                            soft, as they walk away; bar 67 the X swells on a
                            held A13 and the theme's last phrase resolves onto s11's D.
   68-71   136-144   s11    the frame torn open (a paper rip; the sirens cut off) onto D major; ONE
                            celesta ping on the ruby; dawn: the theme's last two bars in D major,
                            plainly, the knight tipped over on bar 70; its C# held over A13 as the
                            camera rises; it resolves as the title lands (the last chord, D6/9); the
                            red dot's chalk tap with the bass's button; digital silence from 143.5.
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
from fractions import Fraction
from functools import lru_cache

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np  # noqa: E402
from scipy import signal  # noqa: E402

from audio import dsp, sfx  # noqa: E402
from audio.dsp import SR, db2lin, n_of  # noqa: E402
from engine.timing import SceneTiming  # noqa: E402
from films.opposite.audio.mix import gen, mono, step_bank  # noqa: E402

FILM = "double_cross"
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
TWO_PI = 2.0 * np.pi

BPM = 120.0
BEAT = 60.0 / BPM            # 0.5 s
BAR = 4 * BEAT               # 2.0 s
SWING = 0.64                 # the off-beat eighth at 64 % of the beat


def _kit_beat(name, default):
    """A film-time beat every scene agrees on, from the kit (the bible's value if it will not load)."""
    try:
        from films.double_cross import kit as K
        v = float(getattr(K, name))
        return v
    except Exception:
        return default


HEIST_T0 = _kit_beat("HEIST_T0", 46.0)       # the stopwatch starts (s04): the first tick
HEIST_STOP = _kit_beat("HEIST_STOP", 93.5)   # it stops dead (s07): no tick from here on

# scene trims (dB, every bus): the film's arc, set by meter (see --qa's per-scene table)
TRIM = dict(s01=-1.4, s02=-2.3, s03=-1.5, s04=-0.6, s05=3.0, s06=1.0, s07=0.4, s08=0.0, s09=-2.0, s10=-1.5, s11=-1.2)

ARGS = argparse.Namespace(stand_ins=True, only=None, qa=None, without=set())
WARN = []
STATUS = {}                  # sid -> how the scene was played (module / stand-in and why)


def warn(msg):
    WARN.append(msg)
    print("WARNING:", msg, flush=True)


# ============================================================================ music theory
NAMES = "C C# D Eb E F F# G Ab A Bb B".split()
_PC = {n: i for i, n in enumerate(NAMES)}
_PC.update({"Db": 1, "D#": 3, "Gb": 6, "G#": 8, "A#": 10, "Cb": 11, "E#": 5, "Fb": 4, "B#": 0})


def nm(m):
    return f"{NAMES[int(m) % 12]}{int(m) // 12 - 1}"


def midi(name):
    """'D4' -> 62, 'Bb2' -> 46, 'C#3' -> 49."""
    mt = re.fullmatch(r"([A-G][#b]?)(-?\d)", name.strip())
    if not mt:
        raise ValueError(f"not a note: {name!r}")
    return 12 * (int(mt.group(2)) + 1) + _PC[mt.group(1)]


def hz(m):
    return 440.0 * 2.0 ** ((float(m) - 69.0) / 12.0)


def sw(b):
    """Beat position b (beats from a bar line) -> seconds, the off-beat eighths swung."""
    k = math.floor(b + 1e-9)
    f = b - k
    f = f / 0.5 * SWING if f <= 0.5 else SWING + (f - 0.5) / 0.5 * (1.0 - SWING)
    return (k + f) * BEAT


# THE THEME: (beat in the phrase, beats, midi). D Dorian, C# the leading tone.
THEME = ((0, 1, 62), (1, 1.5, 69), (2.5, 0.5, 67), (3, 1, 65),
         (4, 0.5, 64), (4.5, 0.5, 65), (5, 1, 67), (6, 1, 64), (7, 1, 60),
         (8, 1, 62), (9, 1.5, 72), (10.5, 0.5, 71), (11, 1, 69),
         (12, 0.5, 67), (12.5, 0.5, 64), (13, 1, 61), (14, 2, 62))
AXIS = 62                    # D4: the mirror


def inverted(notes, axis=AXIS):
    """Exact mirror inversion: every interval turned upside down about the axis."""
    return tuple((b, d, 2 * axis - p) for b, d, p in notes)


def to_major(notes):
    """The same tune, degree for degree, in D major (F -> F#, C -> C#)."""
    return tuple((b, d, p + 1 if p % 12 in (0, 5) else p) for b, d, p in notes)


INVERSION = inverted(THEME)
THEME_MAJOR = to_major(inverted(INVERSION))      # the inversion inverted, in the major

# chords: (the bass's root, the piano's rootless voicing)
CHORDS = {
    "Dm6": (38, (53, 57, 59, 64)),       # F3 A3 B3 E4: D minor 6/9, the heist chord
    "Dm9": (38, (53, 57, 60, 64)),       # F3 A3 C4 E4
    "DmM7": (38, (53, 57, 61, 64)),      # F3 A3 C#4 E4: the spy chord (minor, major seventh)
    "Bb7": (34, (50, 52, 56, 60)),       # D3 E3 Ab3 C4: B-flat 9 #11
    "G7": (43, (53, 57, 59, 64)),        # F3 A3 B3 E4: G 13
    "A7b9": (33, (55, 58, 61, 65)),      # G3 Bb3 C#4 F4: A 7 b9 b13
    "Am9": (33, (48, 52, 55, 59)),       # C3 E3 G3 B3
    "Gm9": (43, (46, 50, 53, 57)),       # Bb2 D3 F3 A3
    "Am7b5": (33, (43, 48, 51, 55)),     # G2 C3 Eb3 G3
    "Eb": (39, (43, 46, 50, 55)),        # G2 Bb2 D3 G3: E-flat major 7 (the Phrygian step)
    "D69": (38, (54, 59, 64, 69)),       # F#3 B3 E4 A4
    "Dmaj9": (38, (54, 57, 61, 64)),     # F#3 A3 C#4 E4
    "Em9": (40, (55, 59, 62, 66)),       # G3 B3 D4 F#4
    "A13": (33, (55, 59, 61, 66)),       # G3 B3 C#4 F#4
    "Gmaj9": (43, (54, 57, 59, 62)),     # F#3 A3 B3 D4
    "Bbmaj7": (34, (50, 52, 57, 60)),    # D3 E3 A3 C4: B-flat major 9 #11 (gold)
    "Bb7alt": (34, (50, 56, 59, 62)),    # D3 Ab3 B3 D4
    "B7": (35, (51, 57, 60, 63)),        # D#3 A3 C4 D#4
    "C7": (36, (52, 58, 61, 64)),        # E3 Bb3 C#4 E4
    "C#7": (37, (53, 59, 62, 65)),       # F3 B3 D4 F4
    "A7": (33, (55, 61, 64, 67)),        # G3 C#4 E4 G4
}
PROG_MINOR = (("Dm6", 4), ("Bb7", 4), ("G7", 4), ("A7b9", 2), ("Dm9", 2))
PROG_INV = (("Dm6", 4), ("Am9", 4), ("Gm9", 4), ("Am7b5", 2), ("Dm9", 2))
PROG_MAJOR = (("D69", 4), ("Em9", 2), ("A13", 2), ("Gmaj9", 4), ("A13", 2), ("D69", 2))

# the walking bass, by hand ('.' a rest, '|' a bar line, '~' ties the previous note over)
WALK = {
    "minor_a": "D2 E2 F2 A2 | Bb2 D2 F2 Ab2 | G2 B2 D3 Bb2 | A2 E2 D2 C#2",
    "minor_b": "D2 C3 A2 F2 | Bb1 D2 F2 F#2 | G2 F2 D2 Bb1 | A1 C#2 D2 A1",
    "inv": "D2 C2 B1 Bb1 | A1 E2 C2 Ab1 | G1 Bb1 D2 Bb1 | A1 Eb2 D2 A1",
    "major": "D2 F#2 A2 D#2 | E2 G2 A2 F#2 | G2 B2 A2 G#2 | A2 E2 D2 A1",
    "vamp": "D2 F2 A2 B2 | C3 B2 A2 F2",
    "vamp2": "D2 A1 B1 C#2 | D2 F2 G2 G#2",
}


def parse_line(s):
    """'D2 E2 . F2 | ...' -> [(beat, midi or None, beats)]: one token a beat."""
    out = []                 # one slot a beat: (beat, midi or None, beats), or None for a tied beat
    last = None
    for tok in s.replace("|", " ").split():
        if tok == "~" and last is not None:
            b, m, d = out[last]
            out[last] = (b, m, d + 1)
            out.append(None)
            continue
        out.append((len(out), None if tok == "." else midi(tok), 1))
        last = len(out) - 1
    return [o for o in out if o is not None]


# ============================================================================ the scene modules
class Stub:
    """A scene played from the bible: missing, or its module broken. Every beat falls back to
    the bible's (the defaults the section passes), its cues to BIBLE_CUES."""

    def __init__(self, sid, why):
        self.sid, self.why = sid, why


_LOADED = {}


def scene(sid):
    """The scene's module; a Stub when it is missing (unless --skip-missing) or broken; None
    when it is missing and missing scenes are skipped. Loaded once a run."""
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
        warn(f"{sid}: no scene module (scenes/{sid}_*.py): section skipped (--skip-missing)")
        return None
    name = os.path.basename(paths[0])[:-3]
    try:
        mod = importlib.import_module(f"films.{FILM}.scenes.{name}")
    except Exception as e:  # mid-edit: play it from the bible
        STATUS[sid] = f"stand-in (module does not import: {type(e).__name__})"
        warn(f"{sid}: {name} does not import ({type(e).__name__}: {e}): played from the bible")
        return Stub(sid, "broken")
    if _draft(mod, sid):            # cues() gives nothing yet: the bible's sound plan, whole
        STATUS[sid] = f"stand-in (module {name} has no cues yet)"
        warn(f"{sid}: {name}.cues() gives no cues yet (a draft?): played from the bible until it does")
        return Stub(sid, "draft")
    STATUS[sid] = f"module {name}"
    return mod


def _draft(mod, sid):
    """True when the module's cues() runs and gives no cues at all. (A module without cues(), or
    whose cues() fails, keeps its beats and is spotted from the bible's cues: see cue_list.)"""
    if not hasattr(mod, "cues"):
        return False
    try:
        T = SceneTiming(FILM, sid)
        args = (T, T.duration)
    except Exception:
        return False
    for arg in args:
        try:
            return len(list(mod.cues(arg))) == 0
        except Exception:
            continue
    return False


FROM_BIBLE = {}          # sid -> beats a module does not have yet, taken from the bible
_FAILED = set()


def _sid(S):
    return S.sid if isinstance(S, Stub) else os.path.basename(getattr(S, "__name__", "?")).split(".")[-1].split("_")[0]


def _num(v):
    return isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool) and math.isfinite(float(v))


def _same_kind(v, d):
    """Does a module's value v have the shape of the bible's default d?"""
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
    return True


def g(S, name, default):
    """A constant of scene module S (the bible's value when S is a Stub, lacks it, or it is of
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


def call(S, name, *a, default=None):
    """A sync helper of scene module S, or default when it is missing or fails."""
    fn = None if isinstance(S, Stub) or S is None else getattr(S, name, None)
    if fn is None or not callable(fn):
        return default
    try:
        return fn(*a)
    except Exception as e:
        if (_sid(S), name) not in _FAILED:
            _FAILED.add((_sid(S), name))
            warn(f"{_sid(S)}: {name}() fails ({type(e).__name__}: {e}): using the bible's")
        return default


def _clean_cues(raw, sid):
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
    err = None
    try:
        T = SceneTiming(FILM, sid)
        args = (T, T.duration)
    except Exception as e:
        args, err = (), f"SceneTiming: {e}"
    for arg in args:
        try:
            out = _clean_cues(S.cues(arg), sid)
            if err is not None:
                warn(f"{sid}: cues(T) raised {err}; read with cues(T.duration) instead")
            return out
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
    warn(f"{sid}: cues() fails ({err}): spotting from the bible's cues")
    return _clean_cues(BIBLE_CUES.get(sid, []), sid)


# ============================================================================ the buses
BUSES = ("music", "hall", "efx", "amb", "vox", "feet", "tick", "rew")
BUS_TRIM = dict(feet=2.0)    # dB on everything a bus is given
HALL_SEND = -14.0            # the music's send to the plate


class Mix:
    """The film's buses. put() takes scene time; placements are staged and committed when the
    section ends (a section that fails part-way is dropped and played again from the bible).
    Every labelled placement is logged as an event (the beat it is for, and where its sound
    actually starts or peaks) for the sync check and for spotting: a cue counts as realised when
    an event of its scene lands within a frame."""

    def __init__(self):
        self.b = {k: np.zeros((N, 2), np.float32) for k in BUSES}
        self.key = np.zeros(N, np.float32)          # breath and voices duck the music a little
        self.ev, self.edges, self.starts, self.spans, self.report = [], [], [], [], []
        self.ticks = []                             # film time of every clock tick
        self.rewind = []                            # (film t0, t1, src film t0, t1) of the rewind
        self.src = {}                               # (sid, beat) -> where it came from
        self.sid, self.t0, self.trim, self.cues, self.covered = None, 0.0, 0.0, [], set()
        self.stage = []
        self.S = None

    # ---------------------------------------------------------------- a section
    def begin(self, S, sid, t0):
        self.S, self.sid, self.t0, self.trim = S, sid, t0, TRIM.get(sid, 0.0)
        self.cues = cue_list(S, sid)
        self.covered, self.claimed = set(), set()
        self.len = LENGTH.get(sid, 10.0)
        self.stage = []
        self.n_ev = len(self.ev)
        self.n_misc = (len(self.edges), len(self.starts), len(self.spans), len(self.ticks), len(self.rewind),
                       len(self.report))

    def abort(self):
        """Drop what the section staged (it failed part-way)."""
        self.stage = []
        if not hasattr(self, "n_ev"):
            return
        del self.ev[self.n_ev:]
        e, s, sp, tk, rw, rp = self.n_misc
        del self.edges[e:], self.starts[s:], self.spans[sp:], self.ticks[tk:], self.rewind[rw:], self.report[rp:]

    def commit(self):
        for bus, i, x, hall, key in self.stage:
            dsp.mix_into(self.b[bus], x, i)
            if hall is not None:
                dsp.mix_into(self.b["hall"], x * np.float32(hall), i)
            if key:
                dsp.mix_into(self.key, x.mean(axis=1), i)
        self.stage = []

    # ---------------------------------------------------------------- beats
    def _match(self, words, default, win, exclude=()):
        best = None
        for i, c in enumerate(self.cues):
            if i in self.claimed or i in exclude:
                continue
            s = c["sfx"].lower()
            if not any(w in s for w in words):
                continue
            d = abs(c["t"] - default)
            if d <= win and (best is None or d < best[0]):
                best = (d, i)
        return None if best is None else best[1]

    def _module(self):
        return not isinstance(self.S, Stub) and self.S is not None

    def at(self, name, default, *words, win=1.5, opt=False):
        """A beat of this scene (scene time): the module's constant `name`; else the time of
        its cue whose text has any of `words`, nearest the bible's time (within win; for a
        module, anywhere in the scene after that); else the bible's time (opt: for a module,
        None: the module has no such beat)."""
        S = self.S
        if not isinstance(S, Stub) and S is not None and name:
            v = getattr(S, name, None)
            if v is not None and _num(v):
                self.src[(self.sid, name)] = "module"
                return float(v)
            if isinstance(v, (tuple, list)) and len(v) and _num(v[0]):      # a span: its start
                self.src[(self.sid, name)] = "module (a span's start)"
                return float(v[0])
            if v is not None:
                warn(f"{self.sid}: {name} = {v!r} is not a time: looking for its cue")
        if words:
            i = self._match(words, default, win) if default is not None else self._first(words)
            if i is None and default is not None and self._module():
                i = self._match(words, default, self.len + 1.0)
            if i is not None:
                self.claimed.add(i)
                self.src[(self.sid, name)] = f"cue {self.cues[i]['sfx']!r}"
                return float(self.cues[i]["t"])
        if opt and self._module():
            self.src[(self.sid, name)] = "not in the module"
            return None
        self.src[(self.sid, name)] = "bible"
        if default is None:
            return None
        if not isinstance(S, Stub) and S is not None and name:
            FROM_BIBLE.setdefault(self.sid, []).append(name)
        return float(default)

    def ats(self, name, defaults, *words, win=1.5, n=None, opt=False):
        """Several beats: the module's sequence `name`; else every cue matching `words` from just
        before the first of the bible's times to just after the last (for a module, anywhere in
        the scene after that); else the bible's (opt: for a module, none)."""
        S = self.S
        defaults = tuple(float(x) for x in defaults)
        if not isinstance(S, Stub) and S is not None and name:
            v = getattr(S, name, None)
            if v is not None and isinstance(v, (tuple, list, np.ndarray)) and len(v) and all(_num(x) for x in v):
                self.src[(self.sid, name)] = "module"
                return tuple(float(x) for x in v)
            if v is not None:
                warn(f"{self.sid}: {name} = {v!r} is not a list of times: looking for its cues")
        if words and defaults:
            lo, hi = min(defaults) - win, max(defaults) + win
            hits = [i for i, c in enumerate(self.cues) if i not in self.claimed and lo <= c["t"] <= hi
                    and any(w in c["sfx"].lower() for w in words)]
            if not hits and self._module():
                hits = [i for i, c in enumerate(self.cues) if i not in self.claimed
                        and any(w in c["sfx"].lower() for w in words)]
            if hits:
                if n is not None and len(hits) > n:     # the n nearest the bible's times
                    pick = []
                    for d in defaults[:n]:
                        j = min((h for h in hits if h not in pick), key=lambda h: abs(self.cues[h]["t"] - d))
                        pick.append(j)
                    hits = sorted(pick)
                self.claimed.update(hits)
                self.src[(self.sid, name)] = f"{len(hits)} cues {self.cues[hits[0]]['sfx']!r}..."
                return tuple(sorted(float(self.cues[i]["t"]) for i in hits))
        if opt and self._module():
            self.src[(self.sid, name)] = "not in the module"
            return ()
        self.src[(self.sid, name)] = "bible"
        if not isinstance(S, Stub) and S is not None and name:
            FROM_BIBLE.setdefault(self.sid, []).append(name)
        return defaults

    def _first(self, words):
        for i, c in enumerate(self.cues):
            if i not in self.claimed and any(w in c["sfx"].lower() for w in words):
                return i
        return None

    def cue_of(self, *words, default=None):
        """The first cue of this scene with any of words (or default)."""
        for c in self.cues:
            if any(w in c["sfx"].lower() for w in words):
                return c
        return default

    def cue_near(self, t, *words, win=FRAME + 1e-6):
        """This scene's cue at t (within win) with any of words (any cue, if no words)."""
        best = None
        for c in self.cues:
            if words and not any(w in c["sfx"].lower() for w in words):
                continue
            d = abs(c["t"] - t)
            if d <= win and (best is None or d < best[0]):
                best = (d, c)
        return None if best is None else best[1]

    def music_at(self, t, pad=0.25):
        """Is this section's music sounding at scene time t?"""
        tf = self.t0 + t
        return any(bus == "music" and a - pad <= tf <= b for bus, a, b, *_ in self.spans[self.n_misc[2]:])

    # ---------------------------------------------------------------- placing
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
            if e0 > 0.2 or e1 > 0.1:                 # cut off loud: it wants a real fade, not the 3 ms one
                self.edges.append((self.sid, self.t0 + at, label or "", e0, e1, bus))
        if fades and len(x) > n_of(0.008):           # no sound starts or stops on a step (a click)
            x = dsp.fade(x, 0.001, 0.003, shape="lin")
        trim = 0.0 if bus == "tick" else self.trim     # the clock: one level from 46.0 to 93.5
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
            if align == "peak" and pk > 0:
                w = n_of(0.01)
                sm = np.convolve(env, np.ones(w) / w, "same")
                meas = at + int(np.argmax(sm)) / SR
            elif align == "onset" and pk > 0:
                i20, i90 = int(np.argmax(env >= 0.2 * pk)), int(np.argmax(env >= 0.9 * pk))
                # a hit is checked at its onset; a sound that swells in (a creak, a swell, a
                # slide) is placed at its start, and its onset is no sync point
                meas = at + i20 / SR if (i90 - i20) / SR < 0.05 else None
            else:
                meas = None
            self.ev.append(dict(sid=self.sid, t=self.t0 + (at if sync is None else sync), label=label,
                                meas=None if meas is None else self.t0 + meas, bus=bus))

    def mark(self, t, label):
        """An event with no sound of its own (a cue realised by a phrase, a bed, a silence)."""
        self.ev.append(dict(sid=self.sid, t=self.t0 + t, label=label, meas=None, bus=None))

    def cover(self, *words):
        """Cues of this scene whose text has any of words are realised (by the score, elsewhere
        in time)."""
        for i, c in enumerate(self.cues):
            if any(w in c["sfx"].lower() for w in words):
                self.covered.add(i)

    def cover_span(self, a, b, *words):
        """Cues with any of words between scene times a and b are realised by the score playing
        there (a theme statement, a held chord)."""
        for i, c in enumerate(self.cues):
            if a - FRAME <= c["t"] <= b + FRAME and any(w in c["sfx"].lower() for w in words):
                self.covered.add(i)

    def end(self):
        """Spotting: realise every cue of this scene no event answered; commit the section."""
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
        self.commit()


# ============================================================================ helpers
def norm(x, peak=1.0):
    x = np.asarray(x, np.float64)
    p = float(np.max(np.abs(x))) if x.size else 0.0
    return x * (peak / p) if p > 1e-12 else x


def tax(n):
    return np.arange(n) / SR


def rng(*keys):
    return dsp.rng_for("double-cross", *keys)


def rev(x, wet=-10.0, seed=0, kind="hall"):
    x = mono(x)
    if len(x) > n_of(0.008):  # a dry sound cut short inside the reverb would click, and echo the click
        x = dsp.fade(x, 0.001, 0.003, shape="lin")
    return dsp.reverb(x, kind, wet_db=wet, seed=seed)


def pitch(x, semis):
    """Resample by 2**(semis/12): pitch and speed together."""
    fr = Fraction(2.0 ** (-semis / 12.0)).limit_denominator(64)
    return signal.resample_poly(np.asarray(x, np.float64), fr.numerator, fr.denominator, axis=0)


def fx(name, dur=None, seed=0, **p):
    return sfx.render(name, dur=dur, params=p, seed=seed)


def bed(name, dur, seed=0, fin=0.05, fout=0.05, **p):
    """A sustained catalog sound with short fades (beds start and end at cuts)."""
    return dsp.fade(fx(name, dur=dur, seed=seed, **p), fin, fout)


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


def space(x, kind, wet, seed=0, lp=None, hp=None):
    """A sound in a room: optional band limits, then the room (stereo)."""
    y = mono(x)
    if hp:
        y = dsp.sos(y, "highpass", hp, 2)
    if lp:
        y = dsp.sos(y, "lowpass", lp, 2)
    return dsp.reverb(dsp.fade(y, 0.0005, 0.003, shape="lin"), kind, wet_db=wet, seed=seed)


def humanize(key, amount=0.006):
    """A small deterministic timing offset (s) for a played note."""
    return float(rng("hum", *key).uniform(-amount, amount))


# ============================================================================ instruments
VIB_MODES = ((1.0, 0.32, 1.0), (3.984, 0.20, 0.30), (9.92, 0.05, 0.12))   # (ratio, amp, t60 factor)
VIB_RATE = 6.0               # the motor: triplet eighths at 120 bpm


@lru_cache(maxsize=None)
def _vibe_parts(m, ring, hard, seed):
    """One vibraphone bar struck with yarn mallets: (bar, res), mono. bar: the aluminium bar's
    partials (1 : 4 : 10); res: the resonator tube's bloom at the fundamental (what the motor's
    discs modulate). The damper comes down `ring` s after the stroke."""
    f0 = hz(m)
    r = rng("vibe", m, seed)
    t60 = float(np.clip(7.0 * (262.0 / f0) ** 0.65, 1.0, 10.0))
    L = min(ring + 0.35, t60 * 1.1)
    n = n_of(L)
    t = tax(n)
    bar = np.zeros(n)
    for ratio, amp, k in VIB_MODES:
        f = f0 * ratio
        if f > 16000.0:
            continue
        a = amp * (1.0 if ratio == 1.0 else (0.45 + 1.1 * hard) ** (1.0 + 0.25 * ratio))
        bar += a * np.sin(TWO_PI * f * t + r.uniform(0, TWO_PI)) * np.power(10.0, -3.0 * t / (t60 * k))
    res = np.sin(TWO_PI * (f0 + r.uniform(-0.3, 0.3)) * t + r.uniform(0, TWO_PI)) * (1.0 - np.exp(-t / 0.010)) * \
        np.power(10.0, -3.0 * t / (t60 * 1.1))
    k = n_of(0.02)
    knock = dsp.sos(r.standard_normal(k), "lowpass", 900.0 + 2600.0 * hard, 2) * np.exp(-tax(k) / 0.0025)
    bar[:k] += 0.05 * (0.5 + hard) * knock / (np.max(np.abs(knock)) + 1e-9)
    a = n_of(0.0012)
    bar[:a] *= np.linspace(0.0, 1.0, a)
    if ring < L - 0.02:
        d = n_of(ring)
        dmp = np.ones(n)
        dmp[d:] = np.exp(-(t[d:] - ring) / 0.075)
        bar, res = bar * dmp, res * dmp
    return bar, res


def vibe(m, ring, vel=0.7, t_abs=0.0, motor=VIB_RATE, depth=0.45, hard=0.55, seed=0):
    """A vibraphone note; its tremolo follows the motor's one clock (t_abs: film time of the stroke)."""
    bar, res = _vibe_parts(int(m), round(float(max(ring, 0.05)), 3), round(float(hard), 2), int(seed) % 3)
    if motor and depth:
        tt = t_abs + tax(len(res))
        res = res * (1.0 - depth * (0.5 - 0.5 * np.cos(TWO_PI * motor * tt)))
    return vel * (bar + res) / 1.25


@lru_cache(maxsize=None)
def _bass1(m, gate, vel_q, seed):
    vel = vel_q / 10.0
    f0 = hz(m)
    r = rng("bass", m, seed)
    L = gate + 0.25
    n = n_of(L)
    t = tax(n)
    P = int(SR / f0)
    exc = r.uniform(-1, 1, P)
    for fc in (260.0 + 500.0 * vel, 320.0 + 600.0 * vel):
        exc = dsp.onepole_lp(exc, fc)
    exc -= exc.mean()
    exc /= max(1e-9, np.max(np.abs(exc)))
    t60 = 2.2 * (55.0 / f0) ** 0.2
    y = norm(dsp.karplus_strong(f0, L, excitation=exc, t60=t60, brightness=0.5, pluck_pos=0.11))
    body = np.sin(TWO_PI * f0 * t * (1.0 + 0.004 * np.exp(-t / 0.03))) * (1.0 - np.exp(-t / 0.004)) * \
        np.power(10.0, -3.0 * t / (t60 * 0.8))
    y = y + 0.55 * body
    d = n_of(gate)
    y[d:] *= np.exp(-(t[d:] - gate) / 0.045)
    k = n_of(0.04)
    y[:k] += 0.35 * vel * sfx._thump(k, 2.2 * f0, 1.4 * f0, 0.01, 0.025)
    snap = dsp.bandpass(r.standard_normal(n_of(0.015)), 900.0, 3000.0, 2) * np.exp(-tax(n_of(0.015)) / 0.003)
    y[:len(snap)] += 0.05 * vel * snap / (np.max(np.abs(snap)) + 1e-9)
    y = dsp.biquad(y, "peak", 90.0, 1.0, 3.0)
    y = dsp.biquad(y, "peak", 230.0, 1.4, 1.5)
    y = dsp.sos(y, "lowpass", 1700.0 + 600.0 * vel, 2)
    y = dsp.saturate(norm(y) * 0.9, 1.0)
    return norm(dsp.fade(y, 0.0008, 0.02)) * vel


def bass(m, gate, vel=0.8, seed=0):
    """The upright bass, plucked: a dark string (a soft fingertip near the end of the
    fingerboard), its fundamental carried by the body, a finger thump; damped at gate."""
    return _bass1(int(m), round(float(gate), 3), int(round(np.clip(vel, 0.1, 1.0) * 10)), int(seed) % 3)


def arco(m, dur, vel=0.7, seed=0, attack=0.25, release=0.5, vib=0.003, env=None, bright=1800.0):
    """The bass bowed: a held low note (saws through the body), rosin, a slow bow."""
    r = rng("arco", m, seed)
    n = n_of(dur + release)
    t = tax(n)
    f0 = hz(m)
    f = f0 * (1.0 + vib * np.sin(TWO_PI * 4.8 * t + r.uniform(0, 6)) * np.clip((t - 0.3) / 0.4, 0, 1))
    x = np.zeros(n)
    for d in (1.0, 1.003, 0.9975):
        x += dsp.saw(f * d, n, phase0=r.uniform())
    x = dsp.bandpass(x, max(25.0, f0 * 0.8), bright, 2)
    x = dsp.biquad(dsp.biquad(x, "peak", 110.0, 1.2, 4.0), "peak", 420.0, 1.5, 2.0)
    x += 0.03 * dsp.bandpass(r.standard_normal(n), 1500.0, 5000.0, 2) * np.max(np.abs(x))
    e = dsp.env_bp([(0.0, 0.0), (attack, 1.0), (dur, 0.9), (dur + release, 0.0)], n)
    if env is not None:
        e = e * dsp.env_bp(env, n)
    return vel * norm(x * e)


@lru_cache(maxsize=None)
def _piano1(m, vel_q, dur, seed):
    vel = vel_q / 10.0
    f0 = hz(m)
    r = np.random.default_rng(dsp.stable_seed("dx-piano", m, seed))
    tail = 0.55 if f0 > 200 else 0.9
    n = n_of(dur + tail)
    t = tax(n)
    B = 0.00005 * 2.0 ** ((m - 21) / 16.0)
    x0 = 0.12 + 0.01 * r.uniform(-1, 1)
    bright = 1.3 + 6.0 * vel ** 1.5
    out = np.zeros(n)
    for k in range(1, int(min(26, 9000.0 / f0)) + 1):
        fk = k * f0 * math.sqrt(1 + B * k * k)
        if fk > 9000:
            break
        a = k ** -0.85 * abs(math.sin(math.pi * k * x0)) ** 0.7 * math.exp(-(k - 1) / bright)
        if a < 2e-4:
            continue
        t1 = float(np.clip(5.0 * (261.6 / f0) ** 0.55 / (1 + 0.11 * (k - 1) ** 1.25), 0.15, 14.0))
        mm = min(n, n_of(t1 * 4.2))
        env = 0.7 * np.power(10.0, -3.0 * t[:mm] / t1) + 0.3 * np.power(10.0, -3.0 * t[:mm] / (3.0 * t1))
        d = 2.3e-4 * (1 if k % 2 else -1)
        p1, p2 = r.uniform(0, TWO_PI, 2)
        out[:mm] += 0.5 * a * env * (np.sin(TWO_PI * fk * (1 + d) * t[:mm] + p1) + np.sin(TWO_PI * fk * (1 - d) * t[:mm] + p2))
    nd = n_of(dur)
    if nd < n:
        out[nd:] *= np.exp(-(t[nd:] - dur) / (0.08 + (0.12 if f0 < 150 else 0.0)))
    ka = min(n, n_of(0.0018 + 0.004 * (1 - vel)))
    out[:ka] *= np.linspace(0, 1, ka) ** 1.5
    nh = n_of(0.04)
    out[:nh] += 0.05 * vel * dsp.sos(r.standard_normal(nh), "lowpass", 500 + 2400 * vel, 2) * np.exp(-tax(nh) / 0.008)
    return norm(out) * vel ** 1.2


def piano(m, dur=1.0, vel=0.6, seed=0):
    """The low felt piano (inharmonic partials, a hammer's comb, two-stage decay, the damper)."""
    return _piano1(int(m), int(round(np.clip(vel, 0.1, 1.0) * 10)), round(float(dur), 2), int(seed) % 3)


@lru_cache(maxsize=None)
def brush_tap(seed=0, slap=0.0):
    """A brush on the snare: the wire bristles' splash, the head's short note, the snare wires."""
    r = rng("btap", seed, slap)
    n = n_of(0.35)
    t = tax(n)
    x = dsp.bandpass(r.standard_normal(n), 1100.0, 5200.0, 2) * np.clip(t / 0.003, 0, 1) * np.exp(-t / (0.03 + 0.03 * slap))
    head = np.sin(TWO_PI * (190.0 + 15 * slap) * t) * np.exp(-t / 0.03)
    wires = dsp.bandpass(r.standard_normal(n), 2200.0, 6500.0, 2) * np.clip(t / 0.004, 0, 1) * np.exp(-t / (0.05 + 0.08 * slap))
    y = norm(x) + (0.3 + 0.3 * slap) * head + (0.3 + 0.5 * slap) * norm(wires)
    return norm(dsp.fade(dsp.sos(y, "lowpass", 7500.0, 2), 0.0005, 0.05))


@lru_cache(maxsize=None)
def brush_sweep(seed=0, beats=4):
    """The left hand's circular sweep over `beats`: a soft swish leaning into 2 and 4."""
    r = rng("bsweep", seed, beats)
    L = beats * BEAT
    n = n_of(L + 0.1)
    t = tax(n)
    fc = 2600.0 + 900.0 * np.sin(TWO_PI * t / 1.0 + r.uniform(0, 6))
    nz = dsp.tv_bandpass(r.standard_normal(n), fc, q=0.8, block=64)
    grain = 1.0 + 0.35 * dsp.bandpass(dsp.crackle(n, 1800.0, r, amp_spread=0.6), 2000.0, 6000.0, 2)
    ph = (t / BEAT) % 1.0
    lean = np.where(np.floor(t / BEAT).astype(int) % 2 == 1, 1.0, 0.72)
    env = (0.4 + 0.6 * np.sin(np.pi * ph) ** 1.5) * lean
    env *= np.clip(t / 0.03, 0, 1) * np.clip((L + 0.1 - t) / 0.08, 0, 1)
    y = dsp.sos(nz * grain, "lowpass", 7000.0, 2) * env
    th = (0.25 * np.sin(TWO_PI * t / 1.0) + 1) * np.pi / 4
    return np.stack([y * np.cos(th), y * np.sin(th)], 1) / (np.max(np.abs(y)) + 1e-9)


@lru_cache(maxsize=None)
def brush_roll(dur, seed=0):
    """A brush roll (buzzed taps) swelling over dur into the next downbeat."""
    r = rng("broll", seed)
    n = n_of(dur + 0.2)
    t = tax(n)
    y = np.zeros(n)
    tt = 0.0
    while tt < dur:
        u = tt / dur
        dsp.mix_into(y, brush_tap(int(r.integers(0, 8)), 0.3 * u) * (0.25 + 0.75 * u ** 1.5), n_of(tt))
        tt += 1.0 / (14.0 + 10.0 * u)
    y += 0.3 * dsp.bandpass(r.standard_normal(n), 1500.0, 6000.0, 2) * np.clip(t / dur, 0, 1) ** 2 * (t < dur)
    return norm(dsp.fade(y, 0.002, 0.05))


@lru_cache(maxsize=None)
def kick(seed=0, hard=0.3):
    """The bass drum: feathered (soft) or a dropped bomb (hard)."""
    r = rng("kick", seed, hard)
    n = n_of(0.45)
    y = sfx._thump(n, 75.0 + 40 * hard, 46.0, 0.02, 0.12 + 0.15 * hard)
    y[:n_of(0.02)] += 0.15 * hard * dsp.sos(r.standard_normal(n_of(0.02)), "lowpass", 1500.0, 2)
    return norm(y)


@lru_cache(maxsize=None)
def hat_foot(seed=0):
    """The hi-hat closed with the foot, on 2 and 4."""
    r = rng("hat", seed)
    n = n_of(0.08)
    t = tax(n)
    x = dsp.bandpass(r.standard_normal(n), 5500.0, 11000.0, 2) * np.exp(-t / 0.018)
    x += 0.3 * np.sin(TWO_PI * 430.0 * t) * np.exp(-t / 0.008)
    return norm(dsp.fade(x, 0.0005, 0.01))


@lru_cache(maxsize=None)
def ride(seed=0, bell=0.0):
    """A ride cymbal struck (inharmonic modes, a wash)."""
    r = rng("ride", seed)
    n = n_of(2.2)
    fr = np.exp(r.uniform(np.log(380), np.log(9500), 24))
    t60 = r.uniform(1.0, 2.4, 24) * (1000.0 / fr) ** 0.2
    amps = r.uniform(0.5, 1.0, 24) / np.sqrt(fr / 500.0)
    x = dsp.modal(fr, t60, amps, n, phases=r.uniform(0, TWO_PI, 24))
    x += dsp.bandpass(r.standard_normal(n), 3000, 11000, 2) * np.exp(-tax(n) / 0.5) * 0.12
    x += (0.5 + bell) * dsp.modal(np.array([5200.0, 7100.0]), np.array([0.09, 0.07]), np.array([0.5, 0.3]), n)
    if bell:
        x += bell * dsp.modal(np.array([2350.0, 3120.0]), np.array([0.8, 0.6]), np.array([0.6, 0.4]), n)
    return norm(dsp.fade(dsp.sos(x, "highpass", 350, 2), 0.0, 0.3))


@lru_cache(maxsize=None)
def crash(seed=0, dur=2.6):
    """A crash cymbal: a burst of bright modes and noise, a long wash."""
    r = rng("crash", seed)
    n = n_of(dur)
    t = tax(n)
    fr = np.exp(r.uniform(np.log(300), np.log(11000), 40))
    x = dsp.modal(fr, r.uniform(0.6, 2.0, 40), r.uniform(0.3, 1.0, 40) / np.sqrt(fr / 400.0), n,
                  phases=r.uniform(0, TWO_PI, 40))
    x = norm(x) + 0.8 * dsp.bandpass(r.standard_normal(n), 2500, 12000, 2) * np.exp(-t / 0.9)
    return norm(dsp.fade(dsp.decorrelate(dsp.sos(x, "highpass", 300, 2), r, amount=0.5), 0.001, 0.5))


def cym_swell(dur, seed=0):
    """A cymbal rolled with soft mallets, swelling into the next downbeat (cut at dur)."""
    r = rng("cswell", seed)
    n = n_of(dur + 0.05)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    x = np.zeros((n, 2))
    for ch in range(2):
        nz = dsp.tv_bandpass(r.standard_normal(n), 2500.0 + 4000.0 * u, q=0.7, block=128)
        x[:, ch] = nz * (0.03 + u ** 2.5) * (1.0 + 0.2 * dsp.smooth_noise(n, 9.0, r))
    x *= np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.01))[:, None]
    return norm(x)


def brass(m, dur, vel=0.8, seed=0, mute="harmon", scoop=True, vib=True, fall=0.0, attack=0.012):
    """A brass note: a harmonic series that brightens as it gets louder; muted (Harmon: the
    trumpet's nasal buzz; cup: the trombone's dark nasal) or open; a lip scoop into the note,
    a delayed vibrato, an optional fall off the end (in semitones)."""
    f0 = hz(m)
    r = rng("brass", m, seed, mute)
    rel = 0.07
    n = n_of(dur + rel + 0.05 + 0.4 * (fall > 0))
    t = tax(n)
    cents = 3.0 * dsp.smooth_noise(n, 6.0, r)
    if scoop:
        cents -= 45.0 * np.exp(-t / 0.018)
    if vib and dur > 0.35:
        cents += 14.0 * np.sin(TWO_PI * 5.4 * t + r.uniform(0, 6)) * np.clip((t - 0.25) / 0.25, 0, 1)
    if fall:
        cents -= fall * 100.0 * np.clip((t - dur * 0.5) / (dur * 0.5 + 0.35), 0, 1) ** 2
    f = f0 * 2.0 ** (cents / 1200.0)
    ph = TWO_PI * np.cumsum(f) / SR
    env = np.clip(t / attack, 0, 1) ** 1.5 * (1.0 + 0.35 * np.exp(-np.maximum(t - attack, 0) / 0.04))
    end = dur + (0.35 if fall else 0.0)
    env *= np.where(t < end, 1.0, np.exp(-(t - end) / (rel / 3)))
    env *= 0.92 + 0.08 * dsp.smooth_noise(n, 4.0, r)
    b = 1.2 + 6.5 * vel * np.clip(env, 0, 1.4)
    y = np.zeros(n)
    for k in range(1, int(min(28, 10000.0 / f0)) + 1):
        y += np.exp(-(k - 1) / b) * np.sin(k * ph) / k ** 0.3
    y = y * env + 0.02 * dsp.bandpass(r.standard_normal(n), 1000.0, 5000.0, 2) * env
    if mute == "harmon":
        y = dsp.sos(y, "highpass", 650.0, 2)
        y = dsp.biquad(dsp.biquad(y, "peak", 1650.0, 3.0, 9.0), "peak", 3300.0, 4.0, 5.0)
        y = dsp.sos(y, "lowpass", 6500.0, 2)
    elif mute == "cup":
        y = dsp.sos(y, "highpass", 90.0, 2)
        y = dsp.biquad(dsp.biquad(y, "peak", 950.0, 2.0, 6.0), "peak", 2100.0, 3.0, 2.0)
        y = dsp.sos(y, "lowpass", 3400.0, 2)
    else:
        y = dsp.sos(dsp.biquad(y, "peak", 1200.0, 1.2, 3.0), "lowpass", 8000.0, 2)
    return norm(dsp.fade(y, 0.0005, 0.02)) * vel


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
            y += amp * np.sin(TWO_PI * f0 * ratio * t + r.uniform(0, TWO_PI)) * np.power(10.0, -3.0 * t / (t60 * k))
    a = n_of(0.0015)
    y[:a] *= np.linspace(0.0, 1.0, a)
    knock = dsp.bandpass(r.standard_normal(n_of(0.02)), 800.0, 5000.0, 2) * np.exp(-tax(n_of(0.02)) / 0.004)
    y[:len(knock)] += 0.05 * knock
    return norm(dsp.fade(y, 0.0, 0.1))


def celesta(m, vel=0.7, seed=0):
    return vel * _celesta1(round(hz(m), 3), int(seed) % 4)


@lru_cache(maxsize=None)
def woodblock(seed=0, f=1174.66):
    """THE CLOCK: a small woodblock, dry, tuned to D6 (a hard stick: a click, the block's knock)."""
    r = rng("wood", seed)
    n = n_of(0.12)
    t = tax(n)
    y = np.zeros(n)
    for ratio, amp, t60 in ((1.0, 1.0, 0.07), (1.57, 0.35, 0.045), (2.63, 0.18, 0.03), (3.9, 0.08, 0.02)):
        y += amp * np.sin(TWO_PI * f * ratio * t + r.uniform(0, 1)) * np.power(10.0, -3 * t / t60)
    c = dsp.sos(r.standard_normal(n_of(0.004)), "highpass", 3000.0, 2) * np.exp(-tax(n_of(0.004)) / 0.0008)
    y[:len(c)] += 0.5 * c / (np.max(np.abs(c)) + 1e-9)
    y[:n_of(0.0006)] *= np.linspace(0, 1, n_of(0.0006))
    return norm(dsp.fade(y, 0.0, 0.02))


@lru_cache(maxsize=None)
def chime(f0, seed=0, tail=3.0):
    """A struck chime (a small bell: a free bar's partials, each a slow beating pair)."""
    r = rng("chime", seed, int(f0))
    n = n_of(tail)
    t = tax(n)
    y = np.zeros(n)
    for ratio, amp, k in ((1.0, 1.0, 1.0), (2.756, 0.45, 0.45), (5.404, 0.22, 0.28), (8.933, 0.1, 0.16)):
        for det in (-0.3, 0.3):
            f = f0 * ratio + det
            if f < 18000.0:
                y += 0.5 * amp * np.sin(TWO_PI * f * t + r.uniform(0, TWO_PI)) * np.power(10.0, -3.0 * t / (tail * k))
    c = sfx._click(r, 3000.0, 0.003)
    y[:len(c)] += 0.25 * norm(c)
    return norm(dsp.fade(y, 0.0, 0.5))


# ============================================================================ the band
def bassline(m, t, line, gain=-9.0, vel=0.8, gate=0.94, seed=0, label=None, pan=-0.1, stacc=None, swell=None):
    """A walking line from scene time t (one token a beat; see WALK). stacc: the note's length
    (s) for a tiptoe. swell: (v0, v1) velocity across the line."""
    notes = parse_line(WALK.get(line, line))
    last = max((b + d for b, _, d in notes), default=1)
    for j, (b, p, d) in enumerate(notes):
        if p is None:
            continue
        u = b / max(last, 1)
        v = vel * (1.0 if b % 4 in (1, 3) else 0.93) * (1.0 if swell is None else swell[0] + (swell[1] - swell[0]) * u)
        tt = t + b * BEAT + humanize(("bass", m.sid, t, b), 0.004)
        dur = stacc if stacc else d * BEAT * gate
        m.put("music", bass(p, dur, v, seed + j), tt, gain, pan=pan, hall=-24.0,
              label=label if j == 0 else None)


def comp(m, t, prog, gain=-19.0, vel=0.5, seed=0, pattern="charleston", octave=0, pan=0.12):
    """The low piano comping a progression from scene time t (rootless voicings)."""
    pats = {"charleston": {4: ((0, 0.9, 1.0), (1.5, 0.35, 0.8)), 2: ((0, 0.8, 1.0),)},
            "push": {4: ((0, 0.4, 0.9), (1.5, 0.3, 0.75), (3.5, 0.45, 0.85)), 2: ((0, 0.4, 0.9), (1.5, 0.3, 0.7))},
            "whole": {4: ((0, 1.9, 1.0),), 2: ((0, 0.95, 1.0),)},
            "sparse": {4: ((0, 1.6, 1.0),), 2: ((0, 0.9, 0.9),)}}[pattern]
    b = 0
    for k, (sym, nb) in enumerate(prog):
        _, voicing = CHORDS[sym]
        for hb, hd, hv in pats.get(nb, pats[4] if nb > 2 else pats[2]):
            tt = t + sw(b + hb) + humanize(("comp", m.sid, t, b, hb), 0.006)
            for i, p in enumerate(voicing):
                m.put("music", piano(p + 12 * octave, hd * BEAT * 2, vel * hv * (0.85 + 0.05 * i), seed + k + i),
                      tt + 0.006 * i, gain, pan=pan)
        b += nb


def drums(m, t, bars, level=0.0, seed=0, sweep=True, taps=True, kick_=True, hat=True, ride_=False, slap=0.0,
          label=None, until=None):
    """Brushes over `bars` bars from scene time t: the sweep, the swing on the snare (accents on
    2 and 4), the bass drum feathered, the hi-hat's foot; optionally the ride's spang-a-lang.
    until: no stroke from this scene time on (a bar cut short by the picture)."""
    if until is not None:
        m0, m_put = m, m.put

        class _Until:
            def __getattr__(self, k):
                return getattr(m0, k)

            def put(self, bus, x, at, *a, **kw):
                if at < until - 1e-6:
                    m_put(bus, x if at + len(x) / SR <= until + 0.4 else dsp.fade(np.asarray(x)[:n_of(until + 0.4 - at)],
                                                                                    0.0, 0.1), at, *a, **kw)
        m = _Until()
    for k in range(int(bars)):
        tb = t + k * BAR
        if sweep:
            m.put("music", brush_sweep(seed + k % 4), tb, -31 + level, hall=-24.0,
                  label=label if k == 0 else None, align=None)
        if taps:
            for pos, v in ((0, 0.45), (1, 0.8), (1.5, 0.35), (2, 0.5), (3, 0.85), (3.5, 0.4)):
                s = slap if pos in (1, 3) else 0.0
                m.put("music", brush_tap((seed + 7 * k + int(pos * 2)) % 9, round(s, 2)) * v,
                      tb + sw(pos) + humanize(("tap", m.sid, tb, pos), 0.004), -27 + level, pan=0.15, hall=-22.0)
        if kick_:
            for pos in range(4):
                m.put("music", kick((seed + k + pos) % 3, 0.2), tb + pos * BEAT, -30 + level, hall=None)
        if hat:
            for pos in (1, 3):
                m.put("music", hat_foot((seed + k + pos) % 4), tb + pos * BEAT, -31 + level, pan=0.25, hall=-26.0)
        if ride_:
            for pos, v in ((0, 0.8), (1, 1.0), (1.5, 0.55), (2, 0.8), (3, 1.0), (3.5, 0.55)):
                m.put("music", ride((seed + k + int(pos * 2)) % 6) * v, tb + sw(pos), -30 + level, pan=0.3, hall=-22.0)


def melody(m, t, notes, inst="vibe", gain=-12.0, pan=0.0, vel=0.75, octave=0, motor=VIB_RATE, depth=0.45,
           hard=0.55, ring=0.22, label=None, seed=0, accent=None, legato=0.92, mute="harmon", fall_last=0.0,
           start=None, stop=None, labels=None):
    """A tune from scene time t: notes (beat, beats, midi); the eighths swung. inst: vibe, tpt,
    tbn (trombone, cup mute), piano. start/stop: only the notes from/before these beats."""
    sel = [nt for nt in notes if (start is None or nt[0] >= start - 1e-9) and (stop is None or nt[0] < stop - 1e-9)]
    for j, (b, d, p) in enumerate(sel):
        p = int(p) + 12 * octave
        tt = t + sw(b) + humanize((inst, m.sid, t, b), 0.005)
        dur = sw(b + d) - sw(b)
        v = vel * (1.08 if d >= 1.5 else 1.0) * (0.92 if (b % 1) else 1.0)
        if accent:
            v *= accent(b)
        lab = label if j == 0 else None
        if labels and b in labels:
            lab = labels[b]
        if inst == "vibe":
            x = vibe(p, dur + ring, v, t_abs=m.t0 + tt, motor=motor, depth=depth, hard=hard, seed=seed + j)
        elif inst in ("tpt", "tbn"):
            fall = fall_last if j == len(sel) - 1 else 0.0
            x = brass(p, max(0.08, dur * legato), v, seed=seed + j, mute=mute if inst == "tpt" else "cup",
                      scoop=d >= 1 or j == 0, vib=d >= 1.5, fall=fall)
        elif inst == "piano":
            x = piano(p, dur * legato + 0.05, v, seed + j)
        elif inst == "celesta":
            x = celesta(p, v, seed + j)
        else:
            raise ValueError(inst)
        pn = pan if not callable(pan) else pan(p)
        m.put("music", x, tt, gain, pan=pn, label=lab)


def stab(m, t, sym, gain=-11.0, dur=0.2, vel=0.9, seed=0, label=None, octave=12, fall=0.0, pan=0.0, low=True,
         sync=None):
    """The muted trumpets hit a chord (the voicing's top three, an octave up), with the low piano
    and the bass on its root; a little spread, like players."""
    root, voicing = CHORDS[sym] if isinstance(sym, str) else sym
    top = sorted(voicing)[-3:]
    for i, p in enumerate(top):
        dt = 0.004 * i + humanize(("stab", m.sid, t, i), 0.004)
        x = brass(p + octave, dur, vel * (0.9 + 0.05 * i), seed=seed + i, mute="harmon", scoop=False, vib=False, fall=fall)
        m.put("music", x, t + dt, gain - 2.0, pan=pan + (-0.25, 0.0, 0.25)[i], label=label if i == 0 else None,
              sync=sync)
    if low:
        m.put("music", piano(root, 0.6, 0.85, seed), t, gain - 3.0, pan=-0.1)
        m.put("music", piano(root + 12, 0.6, 0.7, seed + 1), t, gain - 6.0, pan=-0.1)
        m.put("music", bass(root, 0.4, 0.95, seed), t, gain - 2.0, pan=-0.1, hall=-24.0)


def vibe_chord(m, t, notes, dur, gain=-16.0, vel=0.6, roll=0.025, motor=VIB_RATE, depth=0.45, hard=0.4, seed=0,
               label=None, pan=0.0):
    """The vibraphone rolls a chord (low to high), pedal down for dur."""
    for i, p in enumerate(sorted(notes)):
        tt = t + roll * i
        m.put("music", vibe(p, dur - roll * i, vel, t_abs=m.t0 + tt, motor=motor, depth=depth, hard=hard, seed=seed + i),
              tt, gain, pan=pan + 0.08 * (i - len(notes) / 2), label=label if i == 0 else None)


# ============================================================================ foley: the table, the chalk
@lru_cache(maxsize=None)
def chalk_tap(seed=0, hard=0.7):
    """Chalk tapped onto the blueprint: the tip's click, the table's dull knock, a few crumbs."""
    r = rng("ctap", seed, hard)
    n = n_of(0.14)
    t = tax(n)
    y = sfx._burst(n, r, 1800.0, 9000.0, t60=0.004 + 0.003 * hard, attack=0.0002)
    y = norm(y) + 0.6 * hard * sfx._thump(n, 520.0, 300.0, 0.004, 0.02)
    y += 0.35 * norm(sfx._hit(r, [900.0 * r.uniform(0.9, 1.1), 1650.0, 2700.0], [0.03, 0.02, 0.012], click=0.0, n=n))
    cr = dsp.bandpass(dsp.crackle(n, 3000.0, r), 2500.0, 8000.0, 2) * np.exp(-t / 0.012)
    y += 0.25 * norm(cr)
    return norm(dsp.fade(y, 0.0003, 0.03))


def chalk_scratch(dur, seed=0, circle=False, press=1.0):
    """Chalk drawn along paper on a table: grit, a dry chatter of the stick, the stroke's
    pressure (a ruler stroke is even; a circle's pressure turns with the hand)."""
    r = rng("cscr", seed, round(dur, 3), circle)
    n = n_of(dur + 0.04)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    pr = np.sin(np.pi * u) ** 0.35 * (0.8 + 0.2 * dsp.smooth_noise(n, 9.0, r)) * press
    if circle:
        pr *= 0.72 + 0.28 * np.cos(TWO_PI * t / max(dur, 0.1))
    grain = dsp.bandpass(dsp.crackle(n, 5000.0, r, amp_spread=1.0), 1500.0, 8000.0, 2)
    hiss = dsp.bandpass(r.standard_normal(n), 2000.0, 7000.0, 2)
    stick = dsp.friction(n, 170.0 + 140.0 * pr, r, jitter=0.4, body=[(1400.0, 6, 1.0), (2900.0, 8, 0.6), (4800.0, 10, 0.3)])
    y = (norm(grain) + 0.3 * norm(hiss) + 0.45 * norm(stick)) * pr * (t < dur)
    y[:n_of(0.012)] += 0.35 * chalk_tap(seed, 0.4)[:n_of(0.012)]          # the stick touching down
    return norm(dsp.fade(y, 0.003, 0.02))


def chalk_dots(count, dur, seed=0, hard=0.45):
    """A dotted chalk route: one dab per dot, evenly over dur."""
    n = n_of(dur + 0.2)
    y = np.zeros(n)
    for k in range(int(count)):
        tt = dur * k / max(count, 1) + humanize(("dots", seed, k), 0.006)
        dsp.mix_into(y, chalk_tap(seed + k, hard * (0.85 + 0.15 * ((k * 7) % 3) / 2)), n_of(max(tt, 0.0)),
                     0.75 + 0.25 * ((k * 5) % 3) / 2)
    return norm(y)


def paper_unroll(dur=2.0, seed=0):
    """A big sheet unrolled across a table: the roll's soft tumble (faster as it thins), the paper
    flexing, its air, and the sheet landing flat at dur."""
    r = rng("unroll", seed)
    n = n_of(dur + 0.5)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    speed = np.sin(np.pi * np.clip(0.12 + 0.88 * u, 0, 1)) ** 0.7 * (t < dur + 0.02)
    rot = np.cumsum(2.5 + 6.0 * u) / SR
    bump = (0.5 + 0.5 * np.cos(TWO_PI * rot)) ** 6
    rumble = dsp.sos(dsp.brown(n, r), "lowpass", 260.0, 2) * speed * (0.55 + 0.45 * bump)
    crk = dsp.bandpass(dsp.crackle(n, 900.0, r, amp_spread=1.1), 1500.0, 7000.0, 2) * speed
    air = dsp.tv_bandpass(dsp.pink(n, r), 700.0 + 1600.0 * speed, q=0.9, block=64) * speed
    y = 0.55 * norm(rumble) + 0.6 * norm(crk) + 0.35 * norm(air)
    k = n_of(0.3)
    flap = sfx._burst(k, r, 180.0, 2200.0, t60=0.05, attack=0.002) + 0.8 * sfx._thump(k, 150.0, 85.0, 0.01, 0.07)
    dsp.mix_into(y, 0.9 * norm(flap), n_of(dur))
    st = dsp.decorrelate(y, r, amount=0.35)
    return norm(dsp.fade(st, 0.01, 0.1))


@lru_cache(maxsize=None)
def piece_clack(seed=0, weight=0.5):
    """A wooden chess piece set down on the plan: the piece's knock, the table's thump."""
    r = rng("clack", seed, weight)
    k = r.uniform(0.92, 1.08) * (1.15 - 0.3 * weight)
    y = sfx._hit(r, np.array([1250.0, 2350.0, 3700.0, 5100.0]) * k, [0.05, 0.035, 0.022, 0.015], spread=0.03, click=0.8,
                 n=n_of(0.3))
    th = sfx._thump(n_of(0.15), 210.0 - 60.0 * weight, 120.0, 0.006, 0.035 + 0.03 * weight)
    y[:len(th)] += (0.5 + 0.6 * weight) * norm(th) * np.max(np.abs(y))
    y[:n_of(0.03)] += 0.12 * sfx._burst(n_of(0.03), r, 2000.0, 7000.0, t60=0.008) * np.max(np.abs(y))
    return norm(dsp.reverb(norm(y), "small_room", wet_db=-18.0, seed=seed))


@lru_cache(maxsize=None)
def piece_slam(seed=0):
    """A heavy hand slams a piece down: the thump through the table; the other pieces jump and land."""
    r = rng("slam", seed)
    n = n_of(0.7)
    y = np.zeros(n)
    dsp.mix_into(y, 1.2 * sfx._thump(n_of(0.4), 135.0, 68.0, 0.012, 0.13), 0)
    dsp.mix_into(y, 0.5 * norm(sfx._burst(n_of(0.08), r, 80.0, 1600.0, t60=0.03, attack=0.0005)), 0)
    dsp.mix_into(y, 0.7 * norm(sfx._hit(r, [760.0, 1640.0, 2700.0, 3900.0], [0.06, 0.04, 0.03, 0.02], click=0.9)), 0)
    for j, dt in enumerate((0.055, 0.085, 0.12, 0.15)):
        c = piece_clack(40 + j, 0.2).mean(axis=1)
        dsp.mix_into(y, c * (0.35 - 0.05 * j), n_of(dt + r.uniform(0, 0.01)))
    return norm(dsp.reverb(norm(y), "small_room", wet_db=-16.0, seed=seed))


@lru_cache(maxsize=None)
def piece_tip(seed=0):
    """A wooden piece tipped over: it falls on its side, rocks and rolls a little, and lies still."""
    r = rng("tip", seed)
    n = n_of(1.3)
    y = np.zeros(n)
    dsp.mix_into(y, piece_clack(60, 0.6).mean(axis=1), 0)
    tt, gap, a = 0.13, 0.11, 0.42
    while gap > 0.018 and tt < 1.0:
        dsp.mix_into(y, piece_clack(61 + int(tt * 100), 0.15).mean(axis=1) * a, n_of(tt))
        tt += gap
        gap *= 0.74
        a *= 0.72
    m = n_of(0.75)
    roll = dsp.bandpass(r.standard_normal(m), 500.0, 3000.0, 2) * (0.5 + 0.5 * np.cos(TWO_PI * np.cumsum(np.linspace(9, 3, m)) / SR)) ** 4
    dsp.mix_into(y, 0.12 * norm(roll) * np.exp(-tax(m) / 0.3), n_of(0.15))
    return norm(dsp.fade(y, 0.0005, 0.1))


@lru_cache(maxsize=None)
def stamp(seed=0):
    """A title word stamped onto the paper: a firm rubber-and-wood knock, the paper under it."""
    r = rng("stamp", seed)
    n = n_of(0.5)
    y = 1.2 * sfx._thump(n, 170.0, 100.0, 0.008, 0.07)
    y[:n_of(0.06)] += 0.9 * norm(sfx._burst(n_of(0.06), r, 150.0, 1800.0, t60=0.025, attack=0.0004))
    y[:n_of(0.05)] += 0.25 * norm(dsp.bandpass(dsp.crackle(n_of(0.05), 2000.0, r), 2000.0, 7000.0, 2))
    return norm(dsp.reverb(norm(y), "small_room", wet_db=-14.0, seed=seed))


@lru_cache(maxsize=None)
def strip_thud(seed=0):
    """A paper strip slapped down across the sheet."""
    r = rng("strip", seed)
    n = n_of(0.45)
    y = 0.9 * norm(sfx._burst(n, r, 300.0, 4000.0, t60=0.02, attack=0.0004)) + 1.0 * sfx._thump(n, 140.0, 80.0, 0.01, 0.08)
    return norm(dsp.reverb(norm(y), "small_room", wet_db=-14.0, seed=seed))


@lru_cache(maxsize=None)
def popup(seed=0):
    """A paper wall folding up out of the plan (a pop-up book): a card's snap and its air."""
    r = rng("popup", seed)
    n = n_of(0.4)
    t = tax(n)
    y = norm(sfx._burst(n, r, 300.0, 3500.0, t60=0.025, attack=0.001)) + 0.7 * sfx._thump(n, 170.0, 105.0, 0.008, 0.05)
    air = dsp.tv_bandpass(dsp.pink(n, r), 600.0 + 1500.0 * np.exp(-t / 0.08), q=0.8, block=64) * np.exp(-t / 0.09)
    y += 0.35 * norm(air)
    y[:n_of(0.03)] += 0.25 * norm(dsp.bandpass(dsp.crackle(n_of(0.03), 1500.0, r), 2000.0, 7000.0, 2))
    return norm(dsp.fade(y, 0.0005, 0.05))


def tracing_slide(dur, seed=0):
    """A sheet of tracing paper drawn out and slid over the plan: crisp glassy crinkle, a smooth
    slide, a stiff pop or two, a soft flap as it settles."""
    r = rng("tracing", seed, round(dur, 2))
    n = n_of(dur + 0.4)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    mot = np.sin(np.pi * u) ** 0.8 * (t < dur)
    crk = dsp.bandpass(dsp.crackle(n, 1500.0, r, amp_spread=1.2), 2500.0, 9000.0, 2) * mot
    slide = dsp.tv_bandpass(r.standard_normal(n), 2500.0 + 2500.0 * mot, q=0.9, block=64) * mot
    y = 0.7 * norm(crk) + 0.6 * norm(slide)
    for k in range(4):
        tt = dur * r.uniform(0.15, 0.85)
        dsp.mix_into(y, 0.4 * norm(sfx._burst(n_of(0.04), r, 1500.0, 7000.0, t60=0.01, attack=0.0003)), n_of(tt))
    dsp.mix_into(y, 0.5 * norm(sfx._burst(n_of(0.15), r, 300.0, 3000.0, t60=0.04, attack=0.003)), n_of(dur))
    y = dsp.sos(y, "lowpass", 7000.0, 2)
    return norm(dsp.fade(dsp.decorrelate(y, r, amount=0.4), 0.02, 0.15))


# ============================================================================ foley: street, sewer, bank
@lru_cache(maxsize=None)
def manhole_scrape(dur=0.6, seed=0):
    """A cast-iron manhole lid dragged off its seat: iron grinding on stone, grit, effort."""
    r = rng("mscrape", seed)
    n = n_of(dur + 0.1)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    eff = np.sin(np.pi * u) ** 0.6 * (0.8 + 0.2 * dsp.smooth_noise(n, 5.0, r)) * (t < dur)
    iron = dsp.friction(n, 35.0 + 55.0 * eff, r, jitter=0.5,
                        body=[(210.0, 9, 1.0), (470.0, 11, 0.8), (820.0, 13, 0.6), (1350.0, 15, 0.45), (2150.0, 17, 0.3),
                              (3300.0, 18, 0.15)])
    grit = dsp.bandpass(dsp.crackle(n, 600.0, r), 800.0, 5000.0, 2)
    rumble = dsp.sos(dsp.brown(n, r), "lowpass", 180.0, 2)
    y = (norm(iron) + 0.4 * norm(grit) + 0.35 * norm(rumble)) * eff
    return norm(dsp.fade(y, 0.01, 0.05))


@lru_cache(maxsize=None)
def manhole_clank(seed=0):
    """The lid set down on the road: a heavy iron clank, then it wobbles and settles, faster and
    faster, to a stop."""
    r = rng("mclank", seed)
    n = n_of(2.6)
    k = r.uniform(0.95, 1.05)
    modes = np.array([92, 215, 368, 552, 781, 1063, 1402, 1810, 2310, 2900], float) * k
    t60 = np.array([1.6, 1.4, 1.2, 1.0, 0.85, 0.7, 0.55, 0.45, 0.35, 0.28])
    y = np.zeros(n)
    dsp.mix_into(y, sfx._hit(r, modes, t60, spread=0.02, click=0.7, n=n_of(2.0)), 0)
    dsp.mix_into(y, 1.4 * sfx._thump(n_of(0.4), 110.0, 52.0, 0.012, 0.25) * np.max(np.abs(y[:n_of(0.05)])), 0)
    dsp.mix_into(y, 0.6 * sfx._burst(n_of(0.08), r, 100.0, 2500.0, t60=0.03) * np.max(np.abs(y[:n_of(0.05)])), 0)
    tt, gap, a = 0.16, 0.11, 0.32
    while gap > 0.012:
        h = sfx._hit(r, modes[2:8], t60[2:8] * 0.25, spread=0.03, click=0.5, n=n_of(0.3))
        dsp.mix_into(y, a * norm(h) * np.max(np.abs(y[:n_of(0.05)])), n_of(tt))
        tt += gap
        gap *= 0.84
        a *= 0.9
    dsp.mix_into(y, 0.4 * norm(sfx._hit(r, modes[1:6], t60[1:6] * 0.3, click=0.6, n=n_of(0.5))) * np.max(np.abs(y[:n_of(0.05)])),
                 n_of(tt + 0.02))
    return norm(dsp.fade(y, 0.0, 0.3))


def sewer_bed(dur, seed=0):
    """The sewer: low tunnel air, the channel's trickle (many small drops in the flow), in the pipe."""
    r = rng("sewer", seed)
    n = n_of(dur)
    t = tax(n)
    air = dsp.sos(dsp.brown(n, r), "lowpass", 150.0, 2) * (1.0 + 0.3 * dsp.smooth_noise(n, 0.4, r))
    flow = dsp.bandpass(r.standard_normal(n), 350.0, 2400.0, 2) * (0.6 + 0.4 * np.abs(dsp.smooth_noise(n, 14.0, r)))
    drops = np.zeros(n)
    for tt in dsp.poisson_times(45.0, dur, r):
        d = sfx._drop(r, r.uniform(500.0, 1900.0), r.uniform(0.003, 0.008), chirp=0.7)
        dsp.mix_into(drops, d * r.uniform(0.2, 1.0), n_of(tt))
    y = 0.6 * norm(air) + 0.25 * norm(flow) + 0.35 * norm(drops)
    y = dsp.reverb(y, "cell", wet_db=-6.0, seed=seed)[:n]
    return norm(dsp.fade(y, 0.3, 0.3))


@lru_cache(maxsize=None)
def drip(seed=0):
    """A drip from the tunnel's roof into the channel, its echo along the pipe."""
    x = mono(fx("drip", seed=seed))
    return norm(dsp.reverb(x, "cell", wet_db=-3.0, seed=seed))


@lru_cache(maxsize=None)
def water_step(seed=0, weight=0.6):
    """A step in the sewer's channel: the splash, the slosh of a foot through the water, in the pipe."""
    r = rng("wstep", seed, weight)
    x = mono(fx("footstep", seed=seed, weight=weight, wet=1))
    n = max(len(x), n_of(0.4))
    y = np.zeros(n)
    y[:len(x)] += norm(x)
    m = n_of(0.3)
    slosh = dsp.bandpass(r.standard_normal(m), 150.0, 900.0, 2) * np.clip(tax(m) / 0.015, 0, 1) * np.exp(-tax(m) / 0.11)
    dsp.mix_into(y, (0.3 + 0.4 * weight) * norm(slosh), n_of(0.008))
    return norm(dsp.reverb(norm(y), "cell", wet_db=-8.0, seed=seed))


@lru_cache(maxsize=None)
def rung(seed=0):
    """An iron rung under a shoe or a hand."""
    r = rng("rung", seed)
    y = sfx._hit(r, np.array([820.0, 1390.0, 2210.0, 3180.0]) * r.uniform(0.95, 1.08), [0.35, 0.25, 0.18, 0.12],
                 spread=0.02, click=0.6)
    th = sfx._thump(n_of(0.08), 160.0, 95.0, 0.006, 0.04)
    y[:len(th)] += 0.5 * norm(th) * np.max(np.abs(y))
    return norm(y)


def hatch_creak(dur=0.8, seed=0):
    """A wooden hatch pushed up from below: wood creaking through its grain, the iron hinge."""
    r = rng("hatch", seed)
    n = n_of(dur)
    sw_ = np.sin(np.pi * np.clip(tax(n) / dur, 0, 1)) ** 0.8
    wood = dsp.friction(n, 40.0 + 80.0 * sw_, r, jitter=0.3, body=[(240.0, 7, 1.0), (520.0, 9, 0.8), (1150.0, 12, 0.45)])
    hinge = dsp.friction(n, 320.0 + 350.0 * sw_, r, jitter=0.12, body=[(1700.0, 16, 1.0), (2600.0, 18, 0.4)])
    return norm((norm(wood) + 0.25 * norm(hinge)) * sw_)


@lru_cache(maxsize=None)
def wood_thunk(seed=0, size=1.0):
    """A wooden lid or door laid down: a thump, the board's knock."""
    r = rng("wthunk", seed, size)
    n = n_of(0.5)
    y = sfx._thump(n, 140.0, 75.0, 0.012, 0.12 + 0.06 * size)
    y[:n_of(0.08)] += 0.8 * norm(sfx._burst(n_of(0.08), r, 70.0, 1300.0, t60=0.035, attack=0.0006))
    knock = sfx._hit(r, [420.0, 690.0, 1120.0, 1700.0], [0.06, 0.05, 0.04, 0.03], click=0.5)
    y[:len(knock)] += 0.4 * norm(knock)
    return norm(y)


@lru_cache(maxsize=None)
def flashlight_click(seed=0):
    """A flashlight's slide switch: click-click, the tin barrel."""
    r = rng("flash", seed)
    n = n_of(0.12)
    y = np.zeros(n)
    dsp.mix_into(y, sfx._hit(r, [2900.0, 4600.0, 6900.0], [0.012, 0.009, 0.006], click=1.0, n=n_of(0.05)), 0)
    dsp.mix_into(y, 0.55 * sfx._hit(r, [2400.0, 3900.0], [0.01, 0.007], click=1.0, n=n_of(0.04)), n_of(0.019))
    dsp.mix_into(y, 0.3 * sfx._thump(n_of(0.03), 900.0, 600.0, 0.003, 0.01), 0)
    return norm(dsp.fade(y, 0.0002, 0.02))


@lru_cache(maxsize=None)
def steth_clank(seed=0):
    """The stethoscope's steel chest piece swinging into a pipe: the pipe rings out (and it
    bounces once)."""
    r = rng("steth", seed)
    n = n_of(1.6)
    pipe = np.array([612.0, 1480.0, 2690.0, 4120.0, 5800.0]) * r.uniform(0.97, 1.03)
    y = np.zeros(n)
    dsp.mix_into(y, sfx._hit(r, pipe, [1.1, 0.8, 0.6, 0.45, 0.3], spread=0.01, click=0.8, n=n_of(1.4)), 0)
    dsp.mix_into(y, 0.5 * sfx._hit(r, [3900.0, 6100.0, 8800.0], [0.08, 0.06, 0.04], click=0.6), 0)
    dsp.mix_into(y, 0.35 * sfx._hit(r, pipe[:4], [0.5, 0.4, 0.3, 0.2], click=0.6, n=n_of(0.7)), n_of(0.075))
    return norm(dsp.fade(y, 0.0, 0.2))


def cat_yowl(seed=0, dur=0.55):
    """A startled cat: mrrAOW (a voice gliding up and down through i-a-u), breath in it."""
    r = rng("cat", seed)
    sr2 = 24000
    n2 = int(dur * sr2)
    u = np.linspace(0, 1, n2)
    f0 = np.interp(u, [0, 0.12, 0.35, 0.7, 1.0], [380.0, 620.0, 830.0, 690.0, 470.0])
    f0 = f0 * (1.0 + 0.012 * np.sin(TWO_PI * 9.0 * u * dur))
    src = dsp.pulse_train(f0, n2, sr2, jitter=0.02, rng=r, harmonics=12)
    f1 = np.interp(u, [0, 0.2, 0.5, 0.8, 1.0], [650.0, 1150.0, 1350.0, 950.0, 600.0])
    f2 = np.interp(u, [0, 0.2, 0.5, 0.8, 1.0], [2100.0, 1800.0, 1600.0, 1250.0, 1000.0])
    y = np.zeros(n2)
    for fc, q, gn in ((f1, 5.0, 1.0), (f2, 7.0, 0.6), (np.full(n2, 3300.0), 8.0, 0.25)):
        y += gn * dsp.tv_bandpass(src, fc, q=q, sr=sr2, block=32)
    y = norm(y) + 0.12 * norm(dsp.bandpass(r.standard_normal(n2), 1500.0, 6000.0, 2, sr=sr2))
    env = np.clip(u / 0.06, 0, 1) * np.clip((1.0 - u) / 0.25, 0, 1) ** 1.2
    y = dsp.resample(y * env, sr2, SR)
    return norm(dsp.fade(y, 0.003, 0.03))


@lru_cache(maxsize=None)
def paws(seed=0):
    """A cat landing: two soft pads, a scrabble of claws."""
    r = rng("paws", seed)
    n = n_of(0.35)
    y = np.zeros(n)
    for j, dt in enumerate((0.0, 0.05)):
        dsp.mix_into(y, sfx._thump(n_of(0.08), 260.0, 160.0, 0.005, 0.025) * (1.0 - 0.3 * j), n_of(dt))
    dsp.mix_into(y, 0.3 * norm(dsp.sos(dsp.crackle(n_of(0.2), 400.0, r), "highpass", 2500.0, 2)) * np.exp(-tax(n_of(0.2)) / 0.06),
                 n_of(0.03))
    return norm(y)


@lru_cache(maxsize=None)
def can_clatter(seed=0):
    """A tin can knocked off a crate: it hits, bounces, and rolls away along the floor, slowing."""
    r = rng("can", seed)
    n = n_of(2.2)
    y = np.zeros(n)
    modes = np.array([1180.0, 2650.0, 4300.0, 6050.0, 7900.0]) * r.uniform(0.95, 1.05)
    t60 = np.array([0.18, 0.12, 0.09, 0.06, 0.04])
    for tt, a in ((0.0, 1.0), (0.16, 0.6), (0.27, 0.42), (0.35, 0.3), (0.41, 0.22), (0.455, 0.15)):
        dsp.mix_into(y, a * norm(sfx._hit(r, modes, t60 * r.uniform(0.7, 1.2), spread=0.04, click=0.7, n=n_of(0.3))), n_of(tt))
    m = n_of(1.4)
    tm = tax(m)
    rot = np.cumsum(np.linspace(7.0, 1.8, m)) / SR
    roll = dsp.bandpass(r.standard_normal(m), 900.0, 4500.0, 2) * (0.35 + 0.65 * (0.5 + 0.5 * np.cos(TWO_PI * rot)) ** 3)
    roll *= np.exp(-tm / 0.7) * np.clip(tm / 0.05, 0, 1)
    dsp.mix_into(y, 0.18 * norm(roll), n_of(0.48))
    seams = np.nonzero(np.diff(np.floor(rot)) > 0)[0]
    for i in seams:
        dsp.mix_into(y, 0.12 * np.exp(-tm[i] / 0.6) * norm(sfx._hit(r, modes[:3], t60[:3] * 0.4, click=0.5, n=n_of(0.12))),
                     n_of(0.48) + i)
    return norm(dsp.fade(y, 0.0, 0.2))


@lru_cache(maxsize=None)
def dial_ratchet(dur=1.5, seed=0, rate=16.0):
    """The combination dial turned: one detent click a number, the spindle's faint grind."""
    r = rng("ratchet", seed, dur, rate)
    n = n_of(dur + 0.05)
    t = tax(n)
    y = np.zeros(n)
    sp = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.5
    ph = np.cumsum(rate * (0.35 + 0.65 * sp)) / SR
    for i in np.nonzero(np.diff(np.floor(ph)) > 0)[0]:
        dsp.mix_into(y, sfx._hit(r, [3800.0 * r.uniform(0.97, 1.03), 5900.0], [0.006, 0.004], click=0.8, n=n_of(0.015))
                     * r.uniform(0.5, 0.8), i)
    grind = dsp.friction(n, 70.0, r, jitter=0.3, body=[(420.0, 6, 1.0), (950.0, 8, 0.6)]) * sp * (t < dur)
    y = dsp.sos(norm(y) + 0.12 * norm(grind), "lowpass", 7000.0, 2)
    return norm(dsp.fade(y, 0.005, 0.03))


GATE_PITCH = (74, 77, 81)     # D5, F5, A5: the gates click low, mid, high (the D minor chord)


@lru_cache(maxsize=None)
def gate_click(k, seed=0):
    """A wheel's gate arriving under the fence: a hard small click with a pitched ring (low, mid,
    high), and its ripple up the stethoscope into his ear (a tube's dull echo)."""
    r = rng("gate", k, seed)
    f = hz(GATE_PITCH[k % 3])
    n = n_of(0.9)
    y = np.zeros(n)
    dsp.mix_into(y, norm(sfx._hit(r, [f, 2.76 * f, 5.4 * f], [0.45, 0.14, 0.05], amps=[1.0, 0.3, 0.1], click=0.15,
                                  n=n_of(0.6))), 0)
    dsp.mix_into(y, 0.35 * norm(sfx._hit(r, [3100.0, 5300.0], [0.01, 0.007], click=0.6, n=n_of(0.03))), 0)
    tube = dsp.sos(dsp.biquad(y[:n_of(0.5)].copy(), "peak", 450.0, 3.0, 9.0), "lowpass", 1400.0, 2)
    dsp.mix_into(y, 0.45 * norm(tube), n_of(0.035))
    return norm(dsp.fade(y, 0.0, 0.2))


@lru_cache(maxsize=None)
def fence_clunk(seed=0):
    """The fence drops into the lined-up gates: a heavy clunk deep inside the door."""
    r = rng("fence", seed)
    n = n_of(0.8)
    y = 1.3 * sfx._thump(n, 150.0, 85.0, 0.01, 0.09)
    y[:n_of(0.5)] += 0.6 * norm(sfx._hit(r, [420.0, 760.0, 1250.0, 1900.0], [0.18, 0.14, 0.1, 0.07], click=0.6, n=n_of(0.5)))
    for j in range(3):
        dsp.mix_into(y, 0.12 * norm(sfx._hit(r, [1500.0 + 600 * j, 2600.0], [0.03, 0.02], click=0.5, n=n_of(0.05))),
                     n_of(0.03 + 0.025 * j))
    return norm(dsp.sos(y, "lowpass", 2600.0, 2))


def bolt_run(nb=10, dur=0.9, seed=0, home=False):
    """The vault door's radial bolts: withdrawn round the rim one after another (a rolling
    metallic run under the wheel's grind), or shot home (hard, fast, accelerating)."""
    r = rng("bolts", seed, nb, home)
    n = n_of(dur + 0.6)
    out = np.zeros((n, 2))
    gaps = np.linspace(1.0, 0.65 if home else 0.85, nb)
    times = np.cumsum(gaps) / np.sum(gaps) * dur - gaps[0] / np.sum(gaps) * dur
    for j, tt in enumerate(times):
        pan = float(np.cos(TWO_PI * j / nb + 0.3)) * 0.7
        if not home:
            m = n_of(0.07)
            sl = dsp.friction(m, 900.0, r, jitter=0.2, body=[(2400.0, 10, 1.0), (3800.0, 12, 0.5)]) * np.hanning(m)
            dsp.mix_into(out, dsp.pan_mono(0.3 * norm(sl), pan), n_of(tt))
        h = sfx._hit(r, np.array([310.0, 640.0, 1150.0, 1900.0, 2900.0]) * r.uniform(0.93, 1.07),
                     [0.12, 0.09, 0.07, 0.05, 0.03], spread=0.03, click=0.9, n=n_of(0.3))
        th = sfx._thump(n_of(0.1), 180.0, 110.0, 0.006, 0.04 + 0.03 * home)
        h[:len(th)] += (0.6 + 0.6 * home) * norm(th) * np.max(np.abs(h))
        dsp.mix_into(out, dsp.pan_mono(norm(h) * (0.75 + 0.25 * r.uniform()), pan), n_of(tt + (0.0 if home else 0.065)))
    if not home:
        g = dsp.friction(n, 45.0, r, jitter=0.4, body=[(180.0, 6, 1.0), (430.0, 8, 0.6), (900.0, 10, 0.3)])
        out += 0.25 * norm(g * np.clip((dur + 0.1 - tax(n)) / 0.1, 0, 1) * np.clip(tax(n) / 0.05, 0, 1))[:, None]
    return norm(dsp.fade(out, 0.002, 0.2))


def dial_spin(dur=1.0, seed=0, r0=34.0, r1=5.0):
    """The combination dial spun: a fast run of fine detent ticks slowing to a creep, heard close
    through the stethoscope (the tube's dull body under the ticks)."""
    r = rng("dspin", seed, round(dur, 2))
    n = n_of(dur + 0.05)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    ph = np.cumsum(r1 + (r0 - r1) * (1.0 - u) ** 2) / SR
    y = np.zeros(n)
    for i in np.nonzero(np.diff(np.floor(ph)) > 0)[0]:
        dsp.mix_into(y, sfx._hit(r, [3600.0 * r.uniform(0.97, 1.03), 5600.0], [0.006, 0.004], click=0.8, n=n_of(0.015))
                     * r.uniform(0.55, 0.85), i)
    grind = dsp.friction(n, 40.0 + 60.0 * (1.0 - u), r, jitter=0.3, body=[(420.0, 6, 1.0), (950.0, 8, 0.6)])
    y = norm(y) + 0.1 * norm(grind * np.sqrt(1.0 - u) * (t < dur))
    tube = dsp.sos(dsp.biquad(y.copy(), "peak", 450.0, 3.0, 9.0), "lowpass", 1800.0, 2)
    return norm(dsp.fade(dsp.sos(0.6 * norm(y) + 0.6 * norm(tube), "lowpass", 7000.0, 2), 0.005, 0.03))


@lru_cache(maxsize=None)
def knob_tick(seed=0):
    """Fingers settling on the dial's knurled knob: a faint tick and a whisper of knurl."""
    r = rng("knob", seed)
    n = n_of(0.12)
    y = np.zeros(n)
    dsp.mix_into(y, norm(sfx._hit(r, [4200.0, 6100.0], [0.008, 0.005], click=0.9, n=n_of(0.04))), 0)
    q = n_of(0.07)
    dsp.mix_into(y, 0.25 * norm(dsp.friction(q, 260.0, r, jitter=0.4, body=[(3000.0, 6, 1.0)]) * np.hanning(q)), n_of(0.01))
    return norm(dsp.fade(y, 0.0005, 0.02))


def bolt_slide(dur=0.35, seed=0):
    """The lock's bolt drawn back: a short heavy steel slide, stopping home with a knock."""
    r = rng("bslide", seed, round(dur, 2))
    n = n_of(dur + 0.4)
    t = tax(n)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.6 * (t < dur)
    y = norm(dsp.friction(n, 300.0 + 300.0 * env, r, jitter=0.25, body=[(700.0, 8, 1.0), (1600.0, 10, 0.6),
                                                                          (2800.0, 12, 0.3)]) * env)
    dsp.mix_into(y, 0.8 * norm(sfx._thump(n_of(0.2), 160.0, 90.0, 0.008, 0.06)), n_of(dur))
    dsp.mix_into(y, 0.6 * norm(sfx._hit(r, [520.0, 980.0, 1700.0], [0.1, 0.07, 0.05], click=0.8, n=n_of(0.25))), n_of(dur))
    return norm(dsp.fade(y, 0.005, 0.1))


BOLT_PRE = 0.065             # a radial bolt's slide before its clack


@lru_cache(maxsize=None)
def bolt_one(seed=0):
    """One of the door's radial bolts drawn out of the frame: a short steel slide, then its clack
    (BOLT_PRE in)."""
    r = rng("bolt1", seed)
    n = n_of(0.45)
    y = np.zeros(n)
    q = n_of(0.07)
    dsp.mix_into(y, 0.3 * norm(dsp.friction(q, 900.0, r, jitter=0.2, body=[(2400.0, 10, 1.0), (3800.0, 12, 0.5)])
                               * np.hanning(q)), 0)
    h = sfx._hit(r, np.array([310.0, 640.0, 1150.0, 1900.0, 2900.0]) * r.uniform(0.93, 1.07),
                 [0.12, 0.09, 0.07, 0.05, 0.03], spread=0.03, click=0.9, n=n_of(0.3))
    th = sfx._thump(n_of(0.1), 180.0, 110.0, 0.006, 0.04)
    h[:len(th)] += 0.6 * norm(th) * np.max(np.abs(h))
    dsp.mix_into(y, norm(h), n_of(BOLT_PRE))
    return norm(dsp.fade(y, 0.001, 0.15))


@lru_cache(maxsize=None)
def door_thud(seed=0):
    """The open vault door settling against its stop: a deep, soft thud through the floor."""
    r = rng("dthud", seed)
    n = n_of(1.2)
    y = 1.2 * sfx._thump(n, 85.0, 42.0, 0.02, 0.3)
    y[:n_of(0.4)] += 0.25 * norm(sfx._hit(r, [180.0, 330.0, 520.0], [0.2, 0.15, 0.1], click=0.2, n=n_of(0.4)))
    return norm(dsp.sos(y, "lowpass", 900.0, 2))


@lru_cache(maxsize=None)
def coat_tap(seed=0):
    """The chest-piece dropping on its tube against his coat: a muffled metal tap in cloth."""
    y = np.zeros(n_of(0.3))
    dsp.mix_into(y, dsp.sos(metal_tap(seed), "lowpass", 1500.0, 2), 0)
    dsp.mix_into(y, 0.5 * cloth(0.15, seed + 4), n_of(0.005))
    return norm(y)


def steel_step(who, k, room_="hall", seed=0):
    """A soft step on the vault's steel-plated floor: the shoe, and the plate's faint ring."""
    r = rng("steel", who, k)
    x = mono(footstep(who, k, None))
    y = np.zeros(max(len(x), n_of(0.25)))
    dsp.mix_into(y, x, 0)
    ring = sfx._hit(r, [900.0 * r.uniform(0.95, 1.05), 2300.0, 3700.0], [0.05, 0.03, 0.02], click=0.2, n=n_of(0.15))
    dsp.mix_into(y, 0.15 * norm(ring) * np.max(np.abs(x)), n_of(STEP_PRE))
    return dsp.reverb(y, room_, wet_db=-12.0, seed=seed % 5)


def vault_groan(dur=2.5, seed=0):
    """Tons of steel turning on its hinge: a slow, very low groan, the hinge's thin complaint."""
    r = rng("groan", seed, round(dur, 2))
    n = n_of(dur + 0.2)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    sw_ = np.sin(np.pi * u) ** 0.7 * (t < dur)
    rate = 14.0 + 26.0 * sw_ + 6.0 * dsp.smooth_noise(n, 1.5, r)
    body = dsp.friction(n, rate, r, jitter=0.45, body=[(58.0, 6, 1.0), (96.0, 7, 0.9), (148.0, 8, 0.7), (232.0, 9, 0.5),
                                                       (370.0, 11, 0.35), (610.0, 13, 0.2)])
    hinge = dsp.friction(n, 180.0 + 120.0 * sw_, r, jitter=0.15, body=[(1100.0, 14, 1.0), (1750.0, 16, 0.5)])
    y = (norm(body) + 0.12 * norm(hinge)) * sw_
    return norm(dsp.fade(y, 0.05, 0.1))


@lru_cache(maxsize=None)
def vault_boom(seed=0):
    """The vault door slammed shut: a huge low impact, the steel's ring, the bolts' latch, the
    bank's marble answering."""
    r = rng("boom", seed)
    n = n_of(4.5)
    y = np.zeros(n)
    dsp.mix_into(y, 1.4 * sfx._thump(n_of(1.4), 82.0, 30.0, 0.045, 0.9), 0)
    steel = dsp.modal(np.array([46.0, 71.0, 104.0, 151.0, 219.0, 317.0, 455.0, 650.0, 920.0]),
                      np.array([3.0, 2.6, 2.2, 1.8, 1.5, 1.2, 0.9, 0.7, 0.5]),
                      np.array([0.5, 0.45, 0.4, 0.32, 0.25, 0.2, 0.15, 0.1, 0.07]), n_of(3.5),
                      phases=r.uniform(0, TWO_PI, 9))
    dsp.mix_into(y, 0.5 * steel, 0)
    dsp.mix_into(y, 0.9 * norm(sfx._burst(n_of(0.12), r, 60.0, 2500.0, t60=0.06, attack=0.0004)), 0)
    dsp.mix_into(y, 0.8 * norm(mono(fx("impact", seed=seed + 3, size=1.0))), 0)
    dsp.mix_into(y, 0.35 * norm(sfx._hit(r, [900.0, 1500.0, 2600.0], [0.08, 0.06, 0.04], click=0.9)), n_of(0.17))
    y = dsp.saturate(norm(y) * 1.4, 1.5)
    return norm(dsp.fade(dsp.reverb(y, "hall", wet_db=-5.0, seed=seed)[:n_of(5.5)], 0.0, 0.8))


@lru_cache(maxsize=None)
def gold_clink(seed=0, soft=0.0):
    """Gold bars knocked together: a heavy, soft-metal clink (duller than steel)."""
    r = rng("gold", seed, soft)
    k = r.uniform(0.9, 1.1)
    y = sfx._hit(r, np.array([2200.0, 3480.0, 5100.0, 6900.0]) * k, [0.35, 0.25, 0.18, 0.12], spread=0.03, click=0.6,
                 n=n_of(0.6))
    th = sfx._thump(n_of(0.1), 320.0, 200.0, 0.006, 0.03)
    y[:len(th)] += 0.4 * norm(th) * np.max(np.abs(y))
    if soft:
        y = dsp.sos(y, "lowpass", 4000.0 - 2500.0 * soft, 2)
    return norm(y)


@lru_cache(maxsize=None)
def gold_bag(seed=0):
    """A bar dropped into a canvas bag: the canvas, a muffled clink inside, its weight."""
    r = rng("gbag", seed)
    n = n_of(0.5)
    y = 0.9 * sfx._thump(n, 180.0, 100.0, 0.01, 0.06)
    y[:n_of(0.12)] += 0.6 * norm(sfx._burst(n_of(0.12), r, 300.0, 2500.0, t60=0.04, attack=0.002))
    y[:n_of(0.6)] += 0.35 * gold_clink(seed, 0.8)[:n]
    return norm(y)


def alarm_bell(dur, seed=0, f=1174.66):
    """An electric alarm bell on the wall outside: a hammer striking a gong (tuned to D6, the
    drawn bell's ting in s03) twenty times a second; the coil's buzz."""
    r = rng("alarm", seed)
    n = n_of(dur)
    imp = np.zeros(n)
    tt = 0.0
    while tt < dur - 0.01:
        imp[n_of(tt)] = r.uniform(0.8, 1.0)
        tt += 1.0 / 19.0 * r.uniform(0.97, 1.03)
    m = n_of(1.4)
    tm = tax(m)
    ir = np.zeros(m)
    for ratio, a, t60 in ((1.0, 1.0, 1.1), (2.36, 0.5, 0.7), (3.9, 0.3, 0.45), (5.5, 0.15, 0.3), (0.5, 0.15, 0.6)):
        ir += a * np.sin(TWO_PI * f * ratio * tm + r.uniform(0, 6)) * np.power(10.0, -3.0 * tm / t60)
    ring = signal.fftconvolve(imp, ir)[:n]
    clack = signal.fftconvolve(imp, dsp.sos(r.standard_normal(n_of(0.006)), "highpass", 2500.0, 2))[:n]
    buzz = dsp.bandpass(dsp.saw(60.0, n), 100.0, 1500.0, 2)
    y = norm(ring) + 0.3 * norm(clack) + 0.04 * norm(buzz)
    return norm(dsp.fade(y, 0.01, 0.05))


@lru_cache(maxsize=None)
def hollow_knock(seed=0):
    """A heel struck on the vault floor, and it sounds hollow: the slab's knock and, under it,
    the void ringing (a cavity's low notes), the pipe below answering."""
    r = rng("hollow", seed)
    n = n_of(1.4)
    y = np.zeros(n)
    dsp.mix_into(y, sfx._hit(r, [780.0, 1350.0, 2300.0], [0.02, 0.015, 0.01], click=0.9, n=n_of(0.06)), 0)
    dsp.mix_into(y, 0.6 * norm(sfx._burst(n_of(0.04), r, 200.0, 3000.0, t60=0.012, attack=0.0003)), 0)
    cav = dsp.modal(np.array([96.0, 141.0, 226.0, 330.0]), np.array([0.55, 0.42, 0.3, 0.2]),
                    np.array([1.0, 0.6, 0.35, 0.2]), n_of(1.0), phases=r.uniform(0, TWO_PI, 4))
    dsp.mix_into(y, 1.3 * norm(cav), n_of(0.002))
    dsp.mix_into(y, 0.8 * sfx._thump(n_of(0.3), 150.0, 95.0, 0.01, 0.2), 0)
    dsp.mix_into(y, 0.25 * norm(dsp.sos(cav, "lowpass", 400.0, 2)), n_of(0.09))        # the pipe below
    return norm(dsp.reverb(norm(y), "cell", wet_db=-9.0, seed=seed))


@lru_cache(maxsize=None)
def pound(seed=0):
    """A fist on the vault door, from inside: a huge, muffled steel boom (the slab of steel
    rings low; the fist is soft; nothing bright gets out)."""
    r = rng("pound", seed)
    n = n_of(1.6)
    y = np.zeros(n)
    dsp.mix_into(y, 1.2 * sfx._thump(n_of(0.6), 88.0 * r.uniform(0.96, 1.04), 44.0, 0.014, 0.22), 0)
    dsp.mix_into(y, 0.5 * norm(sfx._burst(n_of(0.07), r, 90.0, 900.0, t60=0.025, attack=0.0008)), 0)
    steel = dsp.modal(np.array([57.0, 93.0, 141.0, 212.0, 327.0, 486.0, 702.0]) * r.uniform(0.98, 1.02),
                      np.array([1.3, 1.1, 0.9, 0.7, 0.5, 0.38, 0.28]),
                      np.array([0.6, 0.55, 0.45, 0.32, 0.22, 0.14, 0.08]), n_of(1.5), phases=r.uniform(0, TWO_PI, 7))
    dsp.mix_into(y, 0.7 * norm(steel), 0)
    y = dsp.sos(dsp.saturate(norm(y) * 1.3, 1.2), "lowpass", 1600.0, 2)
    return norm(dsp.reverb(norm(dsp.fade(y, 0.0, 0.3)), "cell", wet_db=-9.0, seed=seed))


@lru_cache(maxsize=None)
def tile_lift(seed=0):
    """A floor tile prised up: stone grinding on stone, the lift, a breath of air from below,
    the tile set down aside."""
    r = rng("tile", seed)
    n = n_of(1.4)
    t = tax(n)
    y = np.zeros(n)
    m = n_of(0.5)
    sw_ = np.sin(np.pi * tax(m) / 0.5) ** 0.7
    grind = dsp.friction(m, 60.0 + 50 * sw_, r, jitter=0.5, body=[(330.0, 6, 1.0), (720.0, 8, 0.7), (1500.0, 10, 0.4)])
    grind += 0.5 * norm(dsp.bandpass(dsp.crackle(m, 900.0, r), 1000.0, 6000.0, 2))
    dsp.mix_into(y, norm(grind) * sw_, 0)
    air = dsp.sos(dsp.brown(n, r), "lowpass", 200.0, 2) * np.clip((t - 0.45) / 0.2, 0, 1) * np.exp(-np.maximum(t - 0.65, 0) / 0.4)
    dsp.mix_into(y, 0.4 * norm(air), 0)
    clonk = sfx._hit(r, [380.0, 820.0, 1500.0], [0.08, 0.06, 0.04], click=0.6, n=n_of(0.3))
    clonk[:n_of(0.15)] += 0.8 * norm(sfx._thump(n_of(0.15), 170.0, 110.0, 0.008, 0.05)) * np.max(np.abs(clonk))
    dsp.mix_into(y, 0.7 * norm(clonk), n_of(0.95))
    return norm(dsp.fade(y, 0.005, 0.1))


@lru_cache(maxsize=None)
def splash_drop(seed=0):
    """Someone drops through the floor into the sewer's channel: a heavy splash in the pipe."""
    r = rng("drop", seed)
    n = n_of(1.0)
    y = sfx._splash(n, r, size=1.0)
    y += 1.0 * sfx._thump(n, 120.0, 60.0, 0.015, 0.12) * np.max(np.abs(y))
    return norm(dsp.reverb(norm(y), "cell", wet_db=-6.0, seed=seed))


@lru_cache(maxsize=None)
def glove_creak(seed=0, dur=0.4):
    """A leather glove closing into a fist."""
    r = rng("glove", seed)
    n = n_of(dur)
    sw_ = np.sin(np.pi * np.clip(tax(n) / dur, 0, 1)) ** 0.9
    y = dsp.friction(n, 30.0 + 50.0 * sw_, r, jitter=0.35, body=[(700.0, 6, 1.0), (1500.0, 8, 0.6), (2600.0, 10, 0.3)])
    return norm(norm(y) * sw_)


@lru_cache(maxsize=None)
def deposit_box(seed=0):
    """A small deposit box opened: its little latch (the handle recording, made small), the
    drawer sliding out."""
    x = gen("handle", 0.06, 0.62, fade=0.01)
    x = dsp.sos(pitch(x, 5.0), "lowpass", 6000.0, 2)
    r = rng("dbox", seed)
    m = n_of(0.35)
    sl = dsp.friction(m, 400.0, r, jitter=0.25, body=[(1800.0, 9, 1.0), (3100.0, 11, 0.6)]) * np.hanning(m)
    y = np.zeros(len(x) + m)
    y[:len(x)] += norm(x)
    dsp.mix_into(y, 0.35 * norm(sl), len(x) - n_of(0.05))
    return norm(dsp.fade(y, 0.003, 0.05))


# ============================================================================ foley: cars, sirens, the rewind
def engine_start(seed=0, idle=2.0):
    """The getaway car: the starter grinding, two coughs, it catches and idles (rpm rising)."""
    r = rng("start", seed)
    st = 0.75
    n = n_of(st + 0.6 + idle)
    t = tax(n)
    y = np.zeros(n)
    m = n_of(st)
    tm = tax(m)
    whine = dsp.bandpass(dsp.saw(115.0 * (1 + 0.05 * np.sin(TWO_PI * 6.0 * tm)), m), 150.0, 2200.0, 2)
    comp = (0.45 + 0.55 * (0.5 + 0.5 * np.cos(TWO_PI * 6.0 * tm)) ** 3)
    dsp.mix_into(y, 0.5 * norm(whine * comp) * np.clip(tm / 0.03, 0, 1), 0)
    for tt, a in ((st + 0.02, 1.0), (st + 0.2, 0.8), (st + 0.33, 0.9)):
        pop = sfx._thump(n_of(0.2), 85.0, 48.0, 0.01, 0.08)
        pop[:n_of(0.1)] += 0.6 * sfx._burst(n_of(0.1), r, 90.0, 900.0, t60=0.03)
        dsp.mix_into(y, a * norm(pop), n_of(tt))
    k = n_of(st + 0.4)
    eng = mono(fx("engine_idle", dur=(n - k) / SR, seed=seed, rpm=780))
    dsp.mix_into(y, 0.8 * norm(eng) * np.clip(tax(len(eng)) / 0.15, 0, 1), k)
    return norm(dsp.fade(y, 0.002, 0.2))


def siren(dur, lo, hi, period=3.2, seed=0, phase=0.0):
    """A police siren whose wail is tuned: it rises from lo to hi (Hz) and falls, every period s."""
    n = n_of(dur)
    t = tax(n)
    ph = (t / period + phase) % 1.0
    up = 0.42
    u = np.where(ph < up, ph / up, 1 - (ph - up) / (1 - up))
    f = lo + (hi - lo) * np.sin(0.5 * np.pi * u) ** 1.25
    x = sfx._siren_tone(f, n)
    return norm(dsp.bandpass(x, 350.0, 5000.0, 2))


def rewind_scrub(dur, seed=0):
    """Tape rewinding under the picture's scrub: a whir climbing, the tape chattering past the head."""
    r = rng("scrub", seed, round(dur, 2))
    n = n_of(dur + 0.05)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    f = 160.0 * (1.0 + 7.0 * u ** 1.3)
    whir = np.sin(TWO_PI * np.cumsum(f) / SR) + 0.4 * np.sin(TWO_PI * np.cumsum(2.01 * f) / SR)
    chat = 0.55 + 0.45 * np.sign(np.sin(TWO_PI * np.cumsum(38.0 + 60.0 * u) / SR))
    chat = dsp.onepole_lp(chat, 300.0)
    nz = dsp.tv_bandpass(dsp.pink(n, r), 600.0 + 5000.0 * u, q=1.1, block=64)
    y = (0.35 * norm(whir) + norm(nz)) * chat
    env = np.clip(t / 0.06, 0, 1) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.008))
    st = dsp.decorrelate(y * env, r, amount=0.5)
    return norm(st)


@lru_cache(maxsize=None)
def ting(seed=0, m=93):
    """A small bright bell: the callout lens snapping round."""
    return norm(chime(round(hz(m), 2), seed, 1.6))


@lru_cache(maxsize=None)
def lamp_on(seed=0, dur=2.0):
    """A street lamp comes on: a relay's clunk and the ballast's hum swelling in."""
    r = rng("lamp", seed)
    n = n_of(dur)
    t = tax(n)
    y = np.zeros(n)
    dsp.mix_into(y, sfx._hit(r, [700.0, 1500.0, 2500.0], [0.04, 0.03, 0.02], click=0.8, n=n_of(0.08)), 0)
    hum = sum(a * np.sin(TWO_PI * f * t) for f, a in ((120.0, 1.0), (240.0, 0.5), (360.0, 0.3), (480.0, 0.15)))
    hum = hum * np.clip(t / 0.5, 0, 1) + 0.15 * dsp.bandpass(r.standard_normal(n), 2000.0, 6000.0, 2) * np.clip(t / 0.5, 0, 1)
    dsp.mix_into(y, 0.2 * norm(hum), n_of(0.02))
    return norm(dsp.fade(y, 0.0005, 0.3))


# ============================================================================ the recordings
@lru_cache(maxsize=None)
def bank(name, thr=-18.0, length=0.26):
    """Single footfalls cut from a recording (each starts 15 ms before its onset)."""
    return tuple(step_bank(name, thr_db=thr, length=length))


STEP_PRE = 0.015


def footstep(who, k, room="court", seed=0):
    """One step: hers stealthy and light; the Cracker's a careful creep; the Knight's heavy; the
    guard's slow and hard. Mono, in its room."""
    if who == "her":
        x = dsp.sos(bank("her_steps", -28.0)[k % 5], "lowpass", 3500.0, 2) * 0.55
    elif who == "cracker":
        x = pitch(dsp.sos(bank("her_steps", -28.0)[(k + 2) % 5], "lowpass", 2400.0, 2), -3.0) * 0.45
    elif who == "knight":
        x = dsp.sos(bank("stairs_down")[(2 * k + 1) % 11], "lowpass", 2200.0, 2)
    elif who == "guard":
        x = dsp.sos(bank("stairs_up")[(3 * k + 1) % 11], "lowpass", 3000.0, 2)
    else:
        x = bank("street_run", -14.0, 0.2)[k % 14]
    return dsp.reverb(mono(x), room, wet_db=-11.0, seed=seed) if room else dsp.to_stereo(mono(x))


def breath(kind, seed=0):
    """Breaths cut from the recordings: 'ragged' (the Cracker's panting: her quick breaths taken
    down three semitones), 'out' (a long exhale), 'in' (a sharp intake), 'held'."""
    if kind == "ragged":
        return dsp.sos(pitch(gen("her_breath", 0.0, 2.6, fade=0.05), -3.0), "lowpass", 3800.0, 2)
    if kind == "out":
        return dsp.sos(gen("his_breath", 1.92, 2.9, fade=0.08), "highpass", 120.0, 2)
    if kind == "in":
        return dsp.sos(gen("his_breath", 1.25, 1.85, fade=0.05), "highpass", 120.0, 2)
    if kind == "draw":                       # a draw on a cigarette
        return dsp.sos(gen("his_breath", 1.3, 1.75, fade=0.06), "bandpass", (500.0, 4000.0), 2)
    if kind == "gasp":
        return dsp.sos(pitch(gen("gasp_a", 0.0, 0.55, fade=0.01), -2.0), "lowpass", 4000.0, 2)
    return dsp.sos(gen("her_breath", 4.0, 4.26, fade=0.02), "lowpass", 4500.0, 2)


# ============================================================================ the voices
# The voices' own takes (generated once, in audio/gen): the briefing's lines in three voices,
# each (start, end) s in its take, with what it says for the record (it is never heard as words:
# see murmur); the Knight's grunts; her breath of a laugh.
VOX = os.path.join(ROOT, "audio", "gen")
LINES = {
    "her": ("murmur_her", ((0.21, 2.48),          # We go in under the street, here.
                           (2.56, 6.52),          # Down the manhole, along the sewer, up through the hatch.
                           (6.61, 9.12),          # The guard turns every two seconds ...
                           (9.17, 11.36),         # ... we cross in the dark, one at a time.
                           (11.49, 15.6))),       # Right, left, right, and the door's open.
    "cracker": ("murmur_cracker", ((0.27, 2.16),      # Under the street ...
                                   (2.24, 2.8),       # Hm.
                                   (2.98, 4.64),      # How long in the corridor?
                                   (4.8, 5.92),       # Two seconds.
                                   (6.0, 7.2),        # That's not long.
                                   (7.34, 9.68),      # And the dial, three turns?
                                   (10.0, 11.28),     # I've opened worse.
                                   (11.49, 12.96))),  # Much worse.
    "knight": ("murmur_knight", ((0.2, 1.28),         # And then the gold.
                                 (1.55, 4.52),        # In my car, out the front.
                                 (4.61, 6.32),        # Nobody carries it but me.
                                 (6.56, 7.52))),      # Got it?
}
VOICE = {"her": (1300.0, -0.25), "cracker": (1050.0, 0.25), "knight": (900.0, 0.4)}    # low-pass (Hz), pan


@lru_cache(maxsize=None)
def take(name):
    """A voice take (audio/gen/<name>.mp3), mono at SR."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", os.path.join(VOX, name + ".mp3"), "-f", "f32le",
                          "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def take_cut(name, a, b, fin=0.02, fout=0.08, rms=None):
    """[a, b) s of a take, its edges faded; rms: its loudest 0.3 s brought to this RMS."""
    x = dsp.fade(take(name)[n_of(a):n_of(b)], fin, fout)
    if rms is not None:
        w = n_of(0.3)
        top = float(np.sqrt(np.max(np.convolve(x ** 2, np.ones(w) / w, "valid"))))
        x = x * (rms / (top + 1e-12))
    return x


def seams(x, dip=5.0, gap=0.12, shortest=0.07):
    """Where a line breaks into syllables: the dips in its level (dip dB deep and gap s apart at
    the least), its ends included; no piece shorter than shortest."""
    hop, w = n_of(0.005), n_of(0.025)
    db = 20.0 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(w) / w, "same")[::hop]) + 1e-9)
    cuts = [0]
    for p in signal.find_peaks(-db, prominence=dip, distance=max(1, int(round(gap / 0.005))))[0]:
        i = int(p) * hop
        if i - cuts[-1] >= n_of(shortest) and len(x) - i >= n_of(shortest):
            cuts.append(i)
    return cuts + [len(x)]


@lru_cache(maxsize=None)
def murmur(who, k, fit=None, seed=0):
    """Line k of the briefing in this voice with its words scrambled: the syllables between its
    first and its last shuffled (no two neighbours still side by side, where that can be), so it
    keeps its voice, its pace and its cadence and says nothing; fit (s): syllables dropped from
    its middle until it fits. Low-passed (across the table, under the score); its RMS -20 dBFS."""
    name, lines = LINES[who]
    a, b = lines[k]
    x = take(name)[n_of(a):n_of(b)]
    cuts = seams(x)
    parts = [x[i:j] for i, j in zip(cuts[:-1], cuts[1:])]
    r = rng("murmur", who, k, seed)
    if len(parts) > 3:
        mid, best = list(range(1, len(parts) - 1)), None
        for _ in range(64):
            order = [0] + [int(i) for i in r.permutation(mid)] + [len(parts) - 1]
            bad = sum(1 for u, v in zip(order, order[1:]) if v == u + 1)
            if best is None or bad < best[0]:
                best = (bad, order)
            if not bad:
                break
        parts = [parts[i] for i in best[1]]
    xf = n_of(0.006)
    while fit is not None and len(parts) > 2 and sum(map(len, parts)) - xf * (len(parts) - 1) > n_of(fit):
        parts.pop(1 + int(r.integers(len(parts) - 2)))
    y = np.zeros(sum(map(len, parts)))
    i = 0
    for p in parts:
        y[i:i + len(p)] += dsp.fade(p, 0.006, 0.006)
        i += len(p) - xf
    y = y[:i + xf]
    if fit is not None and len(y) > n_of(fit):
        y = dsp.fade(y[:n_of(fit)], 0.0, 0.08)
    y = dsp.sos(dsp.sos(y, "highpass", 110.0, 2), "lowpass", VOICE[who][0], 2)
    return y * (0.1 / (np.sqrt(np.mean(y ** 2)) + 1e-12))


def say(m, who, k, t, gain, fit=None, seed=0, label=None):
    """Line k of this voice (murmured) at scene time t, in the scene's room; where it ends."""
    x = murmur(who, k, None if fit is None else round(fit, 3), seed)
    m.put("vox", roomed(m, x, t, seed), t, gain, pan=VOICE[who][1], label=label, align=None)
    return t + len(x) / SR


# ============================================================================ foley the sections share
@lru_cache(maxsize=None)
def cloth(dur=0.35, seed=0, heavy=0.0):
    """A sleeve or a coat moving: fabric noise in one swell (a heavy coat lower and rougher)."""
    r = rng("cloth", seed, dur, heavy)
    n = n_of(dur + 0.05)
    t = tax(n)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.2 * (t < dur)
    lo, hi = (220.0, 2600.0) if heavy else (600.0, 5000.0)
    x = dsp.bandpass(dsp.pink(n, r), lo, hi, 2) * (1.0 + 0.6 * np.abs(dsp.smooth_noise(n, 18.0, r)))
    cr = dsp.bandpass(dsp.crackle(n, 260.0, r), 1500.0, 6000.0, 2)
    return norm(dsp.fade((norm(x) + 0.25 * norm(cr)) * env, 0.005, 0.03))


def chain_creak(dur, seed=0, period=1.6):
    """The lamp's chain as the lamp swings: a small metal squeak at each end of the swing."""
    r = rng("chain", seed, round(dur, 2))
    n = n_of(dur + 0.4)
    y = np.zeros(n)
    tt = 0.15
    while tt < dur:
        k = n_of(0.24)
        sq = dsp.friction(k, 230.0 + 60.0 * r.uniform(), r, jitter=0.25,
                          body=[(2300.0, 14, 1.0), (3700.0, 16, 0.5), (5200.0, 18, 0.25)])
        sq = norm(sq) * np.sin(np.pi * tax(k) / 0.24) ** 1.5
        dsp.mix_into(y, sq * r.uniform(0.6, 1.0), n_of(tt))
        tt += 0.5 * period * r.uniform(0.95, 1.05)
    return norm(dsp.fade(y, 0.01, 0.1))


@lru_cache(maxsize=None)
def whoosh_thud(pre=0.24, seed=0, heavy=0.0):
    """A paper strip slashing across the frame and slapping down: the air rises into the slap
    at `pre` (kept under a fifth of the slap, so the slap is the sync point)."""
    r = rng("wthud", seed, pre, heavy)
    n = n_of(pre + 1.0)
    t = tax(n)
    u = np.clip(t / pre, 0, 1)
    air = dsp.tv_bandpass(dsp.pink(n, r), 500.0 + 3500.0 * u ** 2, q=0.9, block=64) * u ** 2.2 * (t < pre + 0.01)
    th = strip_thud(seed).mean(axis=1)
    if heavy:
        th = norm(th)
        th[:n_of(0.5)] += heavy * 0.9 * sfx._thump(n_of(0.5), 95.0, 46.0, 0.015, 0.2)
    y = 0.16 * norm(air)
    dsp.mix_into(y, norm(th), n_of(pre))
    return norm(y)


@lru_cache(maxsize=None)
def paper_whoosh(dur=0.6, seed=0):
    """Paper lifting away: a soft swish up and down."""
    r = rng("pwhoosh", seed, dur)
    n = n_of(dur + 0.1)
    u = np.clip(tax(n) / dur, 0, 1)
    env = np.sin(np.pi * u) ** 1.5
    x = dsp.tv_bandpass(dsp.pink(n, r), 600.0 + 2400.0 * np.sin(np.pi * u), q=0.8, block=64) * env
    cr = dsp.bandpass(dsp.crackle(n, 400.0, r), 2000.0, 7000.0, 2) * env
    return norm(dsp.fade(dsp.decorrelate(norm(x) + 0.3 * norm(cr), r, amount=0.4), 0.01, 0.05))


@lru_cache(maxsize=None)
def switch_click(seed=0, f=1.0):
    """A switch or a relay: a hard small click and the housing's knock."""
    r = rng("switch", seed, f)
    y = sfx._hit(r, np.array([2300.0, 3600.0, 5200.0]) * f, [0.025, 0.02, 0.012], click=1.0, n=n_of(0.12))
    y[:n_of(0.05)] += 0.5 * norm(sfx._thump(n_of(0.05), 320.0 * f, 180.0 * f, 0.004, 0.015)) * np.max(np.abs(y))
    return norm(dsp.sos(y, "lowpass", 8000.0, 2))


def lamp_hum(t0, dur, level=1.0):
    """A lamp's warm mains hum, phase-locked to film time (t0: the film time it starts), so
    the pieces the sections place join without a seam."""
    t = t0 + tax(n_of(dur))
    y = (np.sin(TWO_PI * 120.0 * t) + 0.45 * np.sin(TWO_PI * 240.0 * t + 0.4) + 0.2 * np.sin(TWO_PI * 360.0 * t + 1.1)
         + 0.08 * np.sin(TWO_PI * 480.0 * t + 2.0))
    return level * y / 1.73


def flame_bed(dur, seed=0):
    """A match's flame held up: a soft roar that flickers."""
    r = rng("flame", seed, round(dur, 2))
    n = n_of(dur)
    x = dsp.bandpass(dsp.pink(n, r), 150.0, 1800.0, 2) * (0.7 + 0.3 * dsp.smooth_noise(n, 7.0, r))
    cr = dsp.bandpass(dsp.crackle(n, 5.0, r), 1500.0, 6000.0, 2)
    return norm(dsp.fade(norm(x) + 0.3 * norm(cr), 0.25, 0.4))


@lru_cache(maxsize=None)
def ripple(seed=0, f0=70.0, dur=1.2):
    """A sound's ripple through the floor or across the plan: a soft sub swell that sinks."""
    n = n_of(dur)
    t = tax(n)
    f = f0 * (1.0 - 0.3 * t / dur)
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * np.clip(t / 0.04, 0, 1) * np.exp(-t / (dur / 3.5))
    return norm(dsp.fade(y, 0.0, 0.1))


@lru_cache(maxsize=None)
def metal_tap(seed=0):
    """The stethoscope's chest piece set against the steel door: a small dull metal tap."""
    r = rng("mtap", seed)
    y = sfx._hit(r, [1250.0, 2900.0, 4700.0], [0.05, 0.035, 0.02], click=0.5, n=n_of(0.2))
    y[:n_of(0.05)] += 0.5 * norm(sfx._thump(n_of(0.05), 400.0, 250.0, 0.003, 0.015)) * np.max(np.abs(y))
    return norm(dsp.sos(y, "lowpass", 5000.0, 2))


@lru_cache(maxsize=None)
def tock(seed=0, f=293.66):
    """A low wooden tock (a temple block, D4): the guard's light at the end of its swing."""
    r = rng("tock", seed, f)
    n = n_of(0.25)
    t = tax(n)
    y = np.zeros(n)
    for ratio, amp, t60 in ((1.0, 1.0, 0.16), (2.31, 0.3, 0.07), (3.7, 0.12, 0.04)):
        y += amp * np.sin(TWO_PI * f * ratio * t + r.uniform(0, 1)) * np.power(10.0, -3 * t / t60)
    c = dsp.sos(r.standard_normal(n_of(0.006)), "bandpass", (800.0, 3000.0), 2) * np.exp(-tax(n_of(0.006)) / 0.0012)
    y[:len(c)] += 0.3 * c / (np.max(np.abs(c)) + 1e-9)
    y[:n_of(0.0008)] *= np.linspace(0, 1, n_of(0.0008))
    return norm(dsp.fade(y, 0.0, 0.04))


@lru_cache(maxsize=None)
def piece_scrape(seed=0, dur=0.3):
    """A wooden piece snatched up off the paper: its felt base dragged a little, a knock."""
    r = rng("pscrape", seed, dur)
    n = n_of(dur + 0.05)
    sw_ = np.sin(np.pi * np.clip(tax(n) / dur, 0, 1)) ** 0.7
    y = dsp.friction(n, 90.0 + 140.0 * sw_, r, jitter=0.4, body=[(900.0, 5, 1.0), (2100.0, 7, 0.5)]) * sw_
    y = norm(y) + 0.3 * norm(dsp.bandpass(r.standard_normal(n), 1500.0, 6000.0, 2) * sw_ ** 2)
    k = sfx._hit(r, [1250.0, 2350.0, 3700.0], [0.04, 0.03, 0.02], click=0.6, n=n_of(0.12))
    y[:len(k)] += 0.5 * norm(k)
    return norm(dsp.fade(y, 0.002, 0.03))


@lru_cache(maxsize=None)
def heel_tap(seed=0):
    """A heel struck on the vault's steel floor: a hard click, the plate's short ring."""
    r = rng("heel", seed)
    n = n_of(0.5)
    y = np.zeros(n)
    dsp.mix_into(y, sfx._hit(r, [1900.0, 3100.0, 4600.0], [0.04, 0.03, 0.02], click=1.0, n=n_of(0.15)), 0)
    dsp.mix_into(y, 0.5 * norm(sfx._hit(r, [420.0, 980.0, 1650.0], [0.25, 0.18, 0.12], click=0.3, n=n_of(0.45))), 0)
    dsp.mix_into(y, 0.5 * norm(sfx._thump(n_of(0.08), 260.0, 150.0, 0.005, 0.025)), 0)
    return norm(dsp.fade(dsp.sos(y, "lowpass", 5000.0, 2), 0.0, 0.08))


@lru_cache(maxsize=None)
def match_scratch(seed=0):
    """A match scratched on its box: the scratch and sparks, no flame (the strike's first part)."""
    x = mono(fx("match_strike", seed=307))
    e = np.abs(x)
    k = int(np.argmax(e >= 0.2 * e.max()))
    y = x[: k + n_of(0.22)]
    return norm(dsp.fade(dsp.sos(dsp.sos(y, "highpass", 600.0, 2), "lowpass", 8000.0, 2), 0.0, 0.06))


def paper_rise(dur=1.6, seed=0):
    """A rising paper whoosh carrying the cut: air through a sheet, climbing in pitch and level."""
    r = rng("prise", seed, round(dur, 2))
    n = n_of(dur)
    u = np.clip(tax(n) / dur, 0, 1)
    x = dsp.tv_bandpass(dsp.pink(n, r), 350.0 + 3800.0 * u ** 1.6, q=0.9, block=64) * (0.08 + u ** 2.0)
    cr = dsp.bandpass(dsp.crackle(n, 250.0 + 700.0 * float(np.mean(u)), r), 1800.0, 7000.0, 2) * u ** 2.5
    y = norm(x) + 0.25 * norm(cr)
    return norm(dsp.fade(dsp.decorrelate(y, r, amount=0.45), 0.05, 0.03))


def night_air(dur, seed=0):
    """The street at night, from the plan's table gone dark: a distant city, a far siren (tuned to
    the D and the A it will wail on in s10, very far), the wind between the buildings."""
    r = rng("night", seed, round(dur, 2))
    n = n_of(dur)
    city = dsp.to_stereo(fx("city_far", dur=dur, seed=seed))[:n]
    far = siren(dur, hz(74), hz(81), period=4.0, seed=seed + 7, phase=0.3)[:n]
    far = dsp.reverb(dsp.bandpass(far, 500.0, 2200.0, 2) * 0.5, "alley", wet_db=0.0, dry=0.25, seed=seed)[:n]
    far = far * (np.clip((tax(n) - 1.5) / 2.0, 0, 1) * 0.5)[:, None]
    wind = dsp.to_stereo(fx("wind_gust", dur=dur, seed=seed + 3))[:n]
    wind = dsp.sos(wind, "lowpass", 1800.0, 2)
    y = norm(city) + 0.3 * norm(far) + 0.25 * norm(wind)
    return norm(dsp.fade(y, 0.4, 0.3)) * (0.9 + 0.1 * r.uniform())


def paper_carry(dur=2.8, seed=0):
    """The paper whoosh carrying on from the tilt (s03's rise) as the walls stand up: it starts
    where that one ended, swells once more, and settles."""
    r = rng("pcarry", seed, round(dur, 2))
    n = n_of(dur)
    u = np.clip(tax(n) / dur, 0, 1)
    env = (0.55 + 0.45 * np.sin(np.pi * np.clip(u / 0.8, 0, 1))) * np.clip((1.0 - u) / 0.25, 0, 1) ** 1.5
    x = dsp.tv_bandpass(dsp.pink(n, r), 2600.0 - 1400.0 * u, q=0.9, block=64)
    cr = dsp.bandpass(dsp.crackle(n, 500.0, r), 1800.0, 7000.0, 2)
    y = (norm(x) + 0.3 * norm(cr)) * env
    return norm(dsp.fade(dsp.decorrelate(y, r, amount=0.45), 0.0, 0.05))


@lru_cache(maxsize=None)
def grunt(seed=0):
    """A low grunt of effort: a short voiced 'hnn' through the nose and a push of breath."""
    r = rng("grunt", seed)
    n = n_of(0.32)
    u = tax(n) / 0.32
    f0 = 98.0 * (1.0 + 0.05 * np.sin(np.pi * u)) * r.uniform(0.96, 1.04)
    v = dsp.resonator_bank(dsp.saw(f0, n), [320.0, 900.0, 2300.0], [5.0, 7.0, 9.0], [1.0, 0.35, 0.12])
    env = np.sin(np.pi * np.clip(u / 0.9, 0, 1)) ** 0.8
    b = dsp.bandpass(r.standard_normal(n), 300.0, 2500.0, 2) * env ** 2
    return norm(dsp.fade(dsp.sos((norm(v) + 0.3 * norm(b)) * env, "lowpass", 2500.0, 2), 0.01, 0.05))


@lru_cache(maxsize=None)
def chuckle(seed=0):
    """The Cracker's low dry chuckle: four breathy 'heh's through a grin, each a little lower and
    softer, close."""
    r = rng("chuckle", seed)
    src_ = mono(breath("out"))
    n = n_of(0.8)
    y = np.zeros(n)
    t0 = 0.0
    for k in range(4):
        d = 0.085 + 0.025 * r.uniform()
        m_ = n_of(d)
        a = n_of(0.12 + 0.11 * k)
        seg = src_[a:a + m_]
        if len(seg) < m_:
            seg = np.concatenate([seg, np.zeros(m_ - len(seg))])
        env = np.sin(np.pi * np.arange(m_) / m_) ** 1.4
        f0 = (112.0 - 5.0 * k) * (1.0 - 0.07 * np.arange(m_) / m_)
        voice = dsp.resonator_bank(dsp.saw(f0, m_), [500.0, 1300.0, 2400.0], [6.0, 8.0, 10.0], [1.0, 0.45, 0.2])
        dsp.mix_into(y, (0.75 * norm(seg) + 0.35 * norm(voice)) * env * (1.0 - 0.16 * k), n_of(t0))
        t0 += d + 0.06 + 0.02 * r.uniform()
    y = dsp.sos(dsp.sos(y, "highpass", 90.0, 2), "lowpass", 3500.0, 2)
    return norm(dsp.fade(y, 0.005, 0.05))


def tile_scrape(seed=0):
    """The floor tile prised up: stone grinding on stone, the breath of air from below."""
    return cut(tile_lift(seed), 0.8, 0.2)


def tile_set(seed=0):
    """The tile laid down aside: a dull stone clunk."""
    x = np.asarray(tile_lift(seed), np.float64)[n_of(0.93):]
    return norm(dsp.fade(x, 0.002, 0.08))


def sink_whoosh(dur=2.0, seed=0):
    """A low whoosh as the camera sinks through the road into the sewer."""
    return norm(dsp.sos(whip_down(round(dur, 3), seed + 11), "lowpass", 1600.0, 2))


def paper_torn(dur=0.55, seed=0):
    """Paper torn down: the floor cut away into its section."""
    x = dsp.to_stereo(fx("paper_tear", seed=seed, size=float(np.clip((dur - 0.12) / 0.45, 0.2, 1.0))))
    return norm(dsp.sos(x, "lowpass", 8000.0, 2))


def paper_tear_run(dur=1.6, seed=0):
    """A tear that runs on and on (the cut running north along the pipe): tears overlapped end to
    end, each a little further off, the last let go."""
    n = n_of(dur + 0.3)
    y = np.zeros((n, 2))
    t, k = 0.0, 0
    while t < dur - 0.1:
        x = dsp.to_stereo(fx("paper_tear", seed=seed * 7 + k, size=0.9))
        x = norm(x)[:n_of(0.56)] * (0.92 ** k)
        x = dsp.fade(x, 0.02, 0.06)
        i = n_of(t)
        m = min(len(x), n - i)
        y[i:i + m] += x[:m]
        t += 0.42
        k += 1
    y = dsp.fade(y[:n_of(dur + 0.15)], 0.0, 0.25)
    return norm(dsp.sos(y, "lowpass", 7000.0, 2))


@lru_cache(maxsize=None)
def ladder_slide(dur=0.6, seed=0, heavy=0.5):
    """Gloves and a coat sliding fast down an iron ladder: leather hissing on the rails (stick-slip
    through the iron's ring), the coat, a boot knocking a rung, the brake at the foot."""
    r = rng("lslide", seed, round(dur, 3), heavy)
    n = n_of(dur + 0.12)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    env = np.clip(t / 0.05, 0, 1) * (0.75 + 0.25 * u + 0.5 * np.clip((u - 0.72) / 0.28, 0, 1) ** 2) * (t < dur)
    lo = 1.0 - 0.18 * heavy
    rails = dsp.friction(n, 110.0 + 70.0 * u, r, jitter=0.6,
                         body=[(640.0 * lo, 10, 0.7), (1150.0 * lo, 12, 1.0), (1880.0 * lo, 14, 0.7),
                               (2900.0 * lo, 16, 0.35)])
    hiss = dsp.bandpass(dsp.pink(n, r), 1400.0 * lo, 5500.0, 2) * (1.0 + 0.4 * np.abs(dsp.smooth_noise(n, 25.0, r)))
    y = (0.8 * norm(rails) + 0.6 * norm(hiss)) * env
    dsp.mix_into(y, 0.55 * cloth(round(dur * 0.9, 3), seed + 3, heavy=0.6 + 0.4 * heavy), 0)
    for j, uj in enumerate((0.3, 0.62)):
        kn = dsp.sos(rung(11 + seed + j), "lowpass", 2400.0, 2) * (0.35 + 0.15 * heavy)
        dsp.mix_into(y, kn, n_of(uj * dur + r.uniform(-0.03, 0.03)))
    return norm(dsp.fade(y, 0.004, 0.03))


@lru_cache(maxsize=None)
def skid_stop(seed=0, dur=0.32):
    """Shoes skidding to a stop on the cobbles: leather scraping over stone, grit, the heel planted."""
    r = rng("skid", seed, round(dur, 3))
    n = n_of(dur + 0.15)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    env = np.clip(t / 0.012, 0, 1) * (1.0 - u) ** 0.7 * (t < dur)
    scr = dsp.friction(n, 90.0 + 160.0 * (1.0 - u), r, jitter=0.5,
                       body=[(950.0, 6, 1.0), (1900.0, 8, 0.6), (3200.0, 10, 0.3)])
    grit = dsp.bandpass(dsp.crackle(n, 700.0, r), 1500.0, 7000.0, 2)
    hiss = dsp.bandpass(dsp.pink(n, r), 600.0, 4000.0, 2)
    y = (0.8 * norm(scr) + 0.45 * norm(grit) + 0.4 * norm(hiss)) * env
    th = sfx._thump(n_of(0.12), 130.0, 70.0, 0.01, 0.06)
    dsp.mix_into(y, 0.7 * norm(th) * float(np.max(np.abs(y))), n_of(dur * 0.85))
    return norm(dsp.fade(y, 0.002, 0.04))


@lru_cache(maxsize=None)
def getaway_start(seed=0, coughs=(0.0, 0.24), catch=0.4, lurch=0.88, dur=1.32):
    """The getaway car, close on its nose: the starter grinding, two coughs, it catches and roars
    (the revs climbing), the clutch biting as it lurches off; cut off by the picture at dur."""
    r = rng("getaway", seed)
    n = n_of(dur + 0.1)
    y = np.zeros(n)
    m = n_of(catch + 0.03)
    tm = tax(m)
    whine = dsp.bandpass(dsp.saw(118.0 * (1 + 0.05 * np.sin(TWO_PI * 6.5 * tm)), m), 150.0, 2400.0, 2)
    comp = 0.45 + 0.55 * (0.5 + 0.5 * np.cos(TWO_PI * 6.5 * tm)) ** 3
    dsp.mix_into(y, 0.5 * norm(whine * comp) * np.clip(tm / 0.02, 0, 1) * np.clip((catch + 0.03 - tm) / 0.05, 0, 1), 0)
    for tt, a in [(c, 0.9) for c in coughs] + [(catch, 1.1)]:
        pop = sfx._thump(n_of(0.2), 85.0, 48.0, 0.01, 0.08)
        pop[:n_of(0.1)] += 0.6 * sfx._burst(n_of(0.1), r, 90.0, 900.0, t60=0.03)
        dsp.mix_into(y, a * norm(pop), n_of(tt))
    k = n_of(catch)
    te = tax(n - k)
    rpm = 900.0 + 2600.0 * np.clip(te / 0.45, 0, 1) ** 0.7
    bite = te - (lurch - catch)
    rpm = np.where(bite > 0, rpm - 700.0 * np.exp(-np.clip(bite, 0, None) / 0.12), rpm)
    eng = norm(sfx._engine(n - k, r, rpm, 0.8)) * np.clip(te / 0.04, 0, 1)
    dsp.mix_into(y, 0.95 * eng, k)
    return norm(dsp.fade(y, 0.002, 0.08))


@lru_cache(maxsize=None)
def tyre_squeal(dur=0.45, seed=0, f0=1900.0, fall=0.15):
    """Tyres squealing (a wheelspin, or brakes locked): rubber's wavering tone and its hiss."""
    r = rng("squeal", seed, round(dur, 3), f0)
    n = n_of(dur + 0.1)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    env = np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.12, 0, 1)
    f = f0 * (1.0 - fall * u) * (1 + 0.02 * dsp.smooth_noise(n, 18.0, r))
    ph = np.cumsum(f) / SR
    tone = np.sin(TWO_PI * ph) + 0.35 * np.sin(TWO_PI * 2 * ph) + 0.12 * np.sin(TWO_PI * 3 * ph)
    tone = tone * (0.65 + 0.35 * np.abs(dsp.smooth_noise(n, 22.0, r)))
    hiss = dsp.bandpass(dsp.pink(n, r), 700.0, 6000.0, 2)
    return norm((0.55 * norm(tone) + 0.6 * norm(hiss)) * env)


@lru_cache(maxsize=None)
def light_swell(dur=0.6, seed=0):
    """A headlight flaring on: a bright airy swell (the light's white), up fast and away."""
    r = rng("lswell", seed, round(dur, 3))
    n = n_of(dur)
    t = tax(n)
    env = np.clip(t / 0.22, 0, 1) ** 2 * np.exp(-np.clip(t - 0.22, 0, None) / 0.18)
    x = dsp.tv_bandpass(dsp.pink(n, r), 2500.0 + 5000.0 * np.clip(t / 0.22, 0, 1), q=0.9, block=64)
    return norm(dsp.decorrelate(norm(x) * env, r, amount=0.5))


@lru_cache(maxsize=None)
def cat_hiss(seed=0, dur=0.45):
    """A cat's hiss: a sharp breathy spit through bared teeth, a rasp in it."""
    r = rng("hiss", seed, round(dur, 3))
    n = n_of(dur)
    t = tax(n)
    env = np.clip(t / 0.015, 0, 1) * np.exp(-t / (dur * 0.45))
    x = dsp.bandpass(r.standard_normal(n), 2200.0, 9000.0, 2)
    rasp = 1.0 + 0.5 * np.sin(TWO_PI * 38.0 * t + r.uniform(0, 6))
    y = norm(x) * env * rasp
    spit = sfx._burst(n_of(0.03), r, 1500.0, 9000.0, t60=0.01, attack=0.0005)
    y[:len(spit)] += 0.7 * norm(spit)
    return norm(dsp.fade(y, 0.001, 0.05))


@lru_cache(maxsize=None)
def claws(seed=0, dur=0.3):
    """Claws scrabbling on wood: quick scratchy clicks, a scrape, the crate's knock as it pushes off."""
    r = rng("claws", seed, round(dur, 3))
    n = n_of(dur + 0.15)
    y = np.zeros(n)
    tt = 0.0
    while tt < dur:
        c = sfx._burst(n_of(0.012), r, r.uniform(2000.0, 3500.0), 9000.0, t60=0.004, attack=0.0002)
        dsp.mix_into(y, r.uniform(0.4, 1.0) * norm(c), n_of(tt))
        tt += r.uniform(0.018, 0.045)
    sc = dsp.bandpass(dsp.crackle(n, 300.0, r), 1500.0, 6000.0, 2) * np.exp(-tax(n) / 0.15)
    y += 0.4 * norm(sc)
    kn = sfx._hit(r, [180.0, 420.0, 760.0], [0.05, 0.04, 0.03], click=0.3, n=n_of(0.15))
    dsp.mix_into(y, 0.6 * norm(kn), n_of(dur * 0.6))
    return norm(dsp.fade(y, 0.001, 0.04))


@lru_cache(maxsize=None)
def tin_tink(seed=0):
    """A tin can tipping over on a crate: one small bright tink."""
    r = rng("tink", seed)
    y = sfx._hit(r, np.array([1850.0, 3120.0, 4630.0, 6900.0]) * r.uniform(0.95, 1.05), [0.18, 0.12, 0.08, 0.05],
                 spread=0.02, click=0.5, n=n_of(0.3))
    return norm(dsp.fade(y, 0.0, 0.05))


def rise_whoosh(dur=1.0, seed=0):
    """A low whoosh rising (the camera pushing in): the sinking whoosh run backwards."""
    x = np.ascontiguousarray(np.asarray(sink_whoosh(round(dur, 2), seed), np.float64)[::-1])
    return norm(dsp.fade(x, 0.05, 0.08))


@lru_cache(maxsize=None)
def far_drip(seed=0):
    """A drip into the puddle under the lamp, a little way down the street."""
    x = dsp.sos(mono(fx("drip", seed=seed)), "lowpass", 5000.0, 2)
    return norm(rev(x, -3.0, seed % 5, "alley"))


@lru_cache(maxsize=None)
def bird_far(seed=0):
    """A bird far off at dawn: two short 'tsip's and a falling, trilled 'tseee', thin and high,
    a street away."""
    r = rng("bird", seed)
    n = n_of(0.9)
    y = np.zeros(n)
    t0 = 0.0
    for k, (d, f0, f1, a) in enumerate(((0.045, 5200.0, 4300.0, 0.7), (0.045, 5350.0, 4400.0, 0.8),
                                        (0.22, 4800.0, 3500.0, 1.0))):
        q = n_of(d)
        tq = tax(q)
        u = tq / d
        f = f0 + (f1 - f0) * u + (170.0 * np.sin(TWO_PI * 36.0 * tq) if k == 2 else 0.0)
        ph = TWO_PI * np.cumsum(f) / SR
        dsp.mix_into(y, a * np.sin(np.pi * np.clip(u, 0, 1)) ** 2 * (np.sin(ph) + 0.12 * np.sin(2.0 * ph)), n_of(t0))
        t0 += d + 0.09 + 0.03 * r.uniform()
    y = dsp.sos(y, "lowpass", 6500.0, 2)
    return norm(rev(y, -3.0, seed % 5, "street"))


def air_swell(dur=1.15, seed=0):
    """Air opening upward as the camera rises off the table: a soft band of breath, swelling
    toward the top of the rise and gone at its end."""
    r = rng("airswell", seed, round(dur, 2))
    n = n_of(dur + 0.05)
    u = np.clip(tax(n) / dur, 0, 1)
    env = u ** 1.6 * np.clip((1.0 - u) / 0.22, 0, 1)
    x = dsp.tv_bandpass(dsp.pink(n, r), 350.0 + 2300.0 * u ** 1.3, q=0.6, block=64) * env
    return norm(dsp.fade(dsp.decorrelate(norm(x), r, amount=0.6), 0.03, 0.05))


def choked(x, dur=0.2):
    """A cymbal grabbed: cut at dur, a 60 ms damp."""
    x = np.asarray(x, np.float64)[:n_of(dur + 0.06)]
    return dsp.fade(x, 0.0, 0.06)


def whip_down(dur=0.25, seed=0):
    """A fast whoosh down (the camera whips after a look): air falling in pitch, then stopping."""
    r = rng("whipdn", seed, round(dur, 3))
    n = n_of(dur + 0.08)
    u = np.clip(tax(n) / dur, 0, 1)
    x = dsp.tv_bandpass(dsp.pink(n, r), 4200.0 * 0.15 ** u, q=1.1, block=32)
    x = norm(x) + 0.5 * norm(dsp.sos(dsp.tv_bandpass(dsp.pink(n, r), 1500.0 * 0.2 ** u, q=0.8, block=32), "lowpass",
                                     1500.0, 2))
    env = np.where(u < 0.7, (u / 0.7) ** 2.0, np.exp(-(u - 0.7) / 0.06))
    return norm(dsp.fade(dsp.decorrelate(x * env, r, amount=0.4), 0.0, 0.03))


def ragged(dur, seed=0):
    """His ragged breathing for dur seconds: the ragged breath looped, crossfaded."""
    x = mono(breath("ragged"))
    if seed:
        x = np.roll(x, n_of(0.9 * seed))
    out = x
    while len(out) < n_of(dur):
        out = dsp.concat_xfade(out, x, n_of(0.25))
    return out[:n_of(dur)]


@lru_cache(maxsize=None)
def shuffle(seed=0):
    """Someone turning round on the spot: coat cloth, two short scuffs of shoe on stone."""
    r = rng("shuffle", seed)
    n = n_of(0.6)
    y = np.zeros(n)
    dsp.mix_into(y, cloth(0.45, seed + 3, heavy=0.5), 0)
    for k, dt in enumerate((0.08, 0.3)):
        m_ = n_of(0.12)
        sc = dsp.bandpass(r.standard_normal(m_), 300.0, 3500.0, 2) * np.sin(np.pi * tax(m_) / 0.12) ** 2
        dsp.mix_into(y, 0.6 * norm(sc), n_of(dt))
    return norm(y)


@lru_cache(maxsize=None)
def heel_scuff(seed=0, who="guard"):
    """A hard heel pivoting on stone: the heel's knock, then the sole's short grind round on it."""
    r = rng("hscuff", seed, who)
    n = n_of(0.4)
    y = np.zeros(n)
    x = mono(footstep(who, 5 + seed, None))
    dsp.mix_into(y, 0.7 * x[:n], 0)
    q = n_of(0.16)
    env = np.sin(np.pi * tax(q) / 0.16) ** 1.5
    sc = dsp.friction(q, 55.0 + 45.0 * env, r, jitter=0.5, body=[(900.0, 4, 1.0), (2400.0, 6, 0.5)])
    dsp.mix_into(y, 0.5 * norm(sc) * env, n_of(0.03))
    return norm(dsp.fade(y, 0.0005, 0.05))


@lru_cache(maxsize=None)
def police_whoop(seed=0, f=880.0):
    """A police car's short siren whoop as it slides in."""
    n = n_of(0.5)
    t = tax(n)
    fr = f * (0.7 + 0.3 * np.sin(np.pi * np.clip(t / 0.3, 0, 1)))
    x = sfx._siren_tone(fr, n) * np.clip(t / 0.02, 0, 1) * np.clip((0.5 - t) / 0.12, 0, 1)
    return norm(dsp.bandpass(x, 350.0, 5000.0, 2))


@lru_cache(maxsize=None)
def car_slide(seed=0, dur=0.5):
    """A car seen from above sliding in fast and stopping: the engine past, the tyres."""
    r = rng("cslide", seed)
    n = n_of(dur + 0.25)
    t = tax(n)
    u = np.clip(t / dur, 0, 1)
    env = np.sin(np.pi * np.clip(u * 0.9, 0, 1)) ** 1.1 * np.clip((dur + 0.25 - t) / 0.25, 0, 1)
    eng = sfx._engine(n, r, 2600.0 - 1200.0 * u, 0.7)
    tyre = dsp.tv_bandpass(dsp.pink(n, r), 900.0 + 900.0 * env, q=0.7, block=64)
    skid = dsp.friction(n, 140.0, r, jitter=0.2, body=[(1300.0, 9, 1.0), (2600.0, 11, 0.5)]) * np.clip((u - 0.6) / 0.4, 0, 1)
    return norm((0.6 * norm(eng) + 0.5 * norm(tyre) + 0.2 * norm(skid)) * env)


def sirens(dur, seed=0):
    """Two police sirens tuned to the theme's first fifth: one wails D5 to A5, the other A4 to
    D5, a bar each, half a bar apart: they braid. Stereo, each its own side."""
    a = siren(dur, hz(74), hz(81), period=2.0, seed=seed, phase=0.0)
    b = siren(dur, hz(69), hz(74), period=2.0, seed=seed + 1, phase=0.5)
    return dsp.pan_mono(a, -0.45) + dsp.pan_mono(b, 0.45)


def steps(m, who, t0, t1, every=0.5, gain=-18.0, pan=0.0, room_="court", label=None, k0=0, spread=0.0):
    """A walk from scene time t0 to t1, one step per `every` (on the beat), in its room."""
    k = 0
    t = t0
    while t < t1 - 1e-6:
        x = footstep(who, k0 + k, room_, seed=k0 + k)
        m.put("feet", x, t - STEP_PRE, gain - (1.5 if k % 2 else 0.0), pan=pan + spread * (-1) ** k,
              label=label if k == 0 else None, sync=t)
        k += 1
        t += every
    return k


def water_steps(m, t0, t1, every=0.5, gain=-19.0, pan=0.0, label=None, k0=0):
    k = 0
    t = t0
    while t < t1 - 1e-6:
        m.put("feet", water_step((k0 + k) % 8, (0.45, 0.6, 0.75)[k % 3]), t, gain - 1.5 * (k % 3 == 1),
              pan=pan - 0.3 + 0.3 * (k % 3), label=label if k == 0 else None)
        k += 1
        t += every
    return k


# ============================================================================ the clock and the rooms
TICK_GAIN = -13.5


def clock(m, gain=TICK_GAIN):
    """THE CLOCK: a dry woodblock on every beat from HEIST_T0 up to (never at) HEIST_STOP, the
    part of it inside this scene, on its own bus (dry). Unlabelled: a tick answers no cue."""
    a, b = START[m.sid], START[m.sid] + m.len
    k = max(0, math.ceil((a - HEIST_T0) / BEAT - 1e-9))
    while True:
        tf = HEIST_T0 + k * BEAT
        if tf >= b - 1e-9 or tf >= HEIST_STOP - 1e-6:
            break
        acc = 1.0 if k % 4 == 0 else 0.84
        m.put("tick", woodblock(k % 4) * acc, tf - m.t0, gain, pan=0.3, hall=None)
        k += 1


ROOMS = {        # scene -> [(from scene time, reverb, wet dB)]: where its foley sounds
    "s01": [(0.0, "small_room", -22.0)],
    "s02": [(0.0, "small_room", -18.0)],
    "s03": [(0.0, "small_room", -20.0)],
    "s04": [(0.0, "street", -14.0), (6.0, "cell", -8.0)],
    "s05": [(0.0, "court", -12.0)],
    "s06": [(0.0, "hall", -14.0)],
    "s07": [(0.0, "hall", -12.0), (13.0, "small_room", -20.0)],
    "s08": [(0.0, "cell", -10.0)],
    "s09": [(0.0, "small_room", -20.0), (10.9, "cell", -10.0), (12.8, "cell", -7.0)],
    "s10": [(0.0, "street", -12.0), (3.0, "street", -16.0), (7.0, "street", -10.0)],
    "s11": [(0.0, "street", -16.0), (3.0, "small_room", -18.0)],
}


def room(m, t):
    kind, wet = "small_room", -20.0
    for t0, k, w in ROOMS.get(m.sid, ()):
        if t >= t0 - 1e-6:
            kind, wet = k, w
    return kind, wet


def roomed(m, x, t, seed=0, wet=None):
    """x in the room of this scene at scene time t."""
    kind, w = room(m, t)
    return dsp.reverb(x if np.ndim(x) == 2 else dsp.fade(mono(x), 0.0005, 0.003, shape="lin"), kind,
                      wet_db=w if wet is None else wet, seed=seed % 5)


def FB(m, b):
    """Scene time of film bar b (a bar is 2 s; every scene starts on a bar line)."""
    return b * BAR - m.t0


def span(m, name, default, *words, win=1.5, opt=False):
    """(start, end) of a stretch of this scene: the module's pair `name`; else its cue with any of
    words (nearest the bible's start; its dur); else the bible's (None if the bible has none)."""
    S = m.S
    if name and not isinstance(S, Stub) and S is not None:
        v = getattr(S, name, None)
        if isinstance(v, (tuple, list)) and len(v) == 2 and all(_num(x) for x in v) and float(v[1]) > float(v[0]):
            m.src[(m.sid, name)] = "module"
            return float(v[0]), float(v[1])
        if v is not None:
            warn(f"{m.sid}: {name} = {v!r} is not a (start, end): looking for its cue")
    if words:
        i = m._match(words, default[0], win) if default is not None else m._first(words)
        if i is None and default is not None and m._module():
            i = m._match(words, default[0], m.len + 1.0)
        if i is not None:
            m.claimed.add(i)
            c = m.cues[i]
            d = c.get("dur") or ((default[1] - default[0]) if default is not None else 1.0)
            m.src[(m.sid, name)] = f"cue {c['sfx']!r}"
            return float(c["t"]), float(c["t"]) + float(d)
    if opt and m._module():
        m.src[(m.sid, name)] = "not in the module"
        return None
    m.src[(m.sid, name)] = "bible"
    if default is None:
        return None
    if name and not isinstance(S, Stub) and S is not None:
        FROM_BIBLE.setdefault(m.sid, []).append(name)
    return float(default[0]), float(default[1])


def cues_with(m, *words):
    """This scene's cues whose text has any of words: [(t, dur, cue)], in time order."""
    out = [(float(c["t"]), float(c.get("dur") or 0.0), c) for c in m.cues if any(w in c["sfx"].lower() for w in words)]
    return sorted(out, key=lambda x: x[0])


def chord_at(t, t0, prog):
    """The chord of progression prog (begun at t0) sounding at t."""
    b = (t - t0) / BEAT
    acc = 0.0
    for sym, nb in prog:
        if b < acc + nb - 1e-9:
            return sym
        acc += nb
    return prog[-1][0]


def hit(m, t, root, hard=0.6, gain=-10.0, label=None, sync=None):
    """A low band hit on a picture beat: the bass drum, the piano's low octave, the bass's root."""
    lo = root - 12 if root - 12 >= 21 else root
    m.put("music", kick(1, round(hard, 1)), t, gain - 8.5 + 5.0 * hard, hall=-22.0, label=label, sync=sync)
    m.put("music", piano(lo, 1.0, 0.55 + 0.35 * hard, 1), t, gain - 4.5, pan=-0.1)
    m.put("music", piano(root, 0.8, 0.5 + 0.3 * hard, 2), t, gain - 7.5, pan=-0.1)
    m.put("music", bass(root if root < 48 else root - 12, 0.5, 0.95, 1), t, gain - 2.5, pan=-0.1, hall=-24.0)


def brass_swell(m, t, sym, dur, gain=-14.0, seed=0, label=None):
    """The brass swell on a chord over dur, pianissimo to forte: open trumpets on the voicing's
    top three, the trombone (cup) on the root."""
    root, voicing = CHORDS[sym]
    n = n_of(dur + 0.6)
    env = 0.12 + 0.88 * np.clip(tax(n) / dur, 0, 1) ** 2.2
    for i, p in enumerate(sorted(voicing)[-3:]):
        x = brass(p + 12, dur, 0.95, seed=seed + i, mute="open", scoop=False, vib=True, attack=0.25)[:n]
        m.put("music", x * env[:len(x)], t + 0.012 * i, gain - 2.0, pan=(-0.3, 0.0, 0.3)[i],
              label=label if i == 0 else None, align=None)
    x = brass(root + 12, dur, 0.9, seed=seed + 5, mute="cup", scoop=False, vib=True, attack=0.25)[:n]
    m.put("music", x * env[:len(x)], t, gain, pan=-0.15)


SECTIONS = []


def section(sid):
    def deco(fn):
        SECTIONS.append((sid, fn))
        return fn
    return deco


# ============================================================================ s01 TITLE (0-12): bars 0-5
@section("s01")
def s01(m, S):
    L = m.len
    # four chalk taps count it in (the corners); the 4th is the bar line the bass walks in on
    dots = m.ats("T_DOTS", (0.0, 0.5, 1.0, 1.5), "chalk tap", "corner", n=4)
    for k, t in enumerate(dots):
        c = m.cue_near(t, "chalk tap", "corner")
        pan = c["pan"] if c else (-0.6, 0.6, 0.6, -0.6)[k % 4]
        m.put("efx", roomed(m, chalk_tap(k, 0.8), t, k), t, -11.0, pan=pan, label="chalk tap (the count-in)")
    jn = span(m, "T_JOIN", None, "dotted lines", "dry run", "chalk ticks")
    if jn:
        m.put("efx", roomed(m, chalk_dots(8, jn[1] - jn[0], 11, 0.35), jn[0]), jn[0], -22.0, label="a dry run of chalk ticks")
    # the bank at night: the street's air under the count-in, going as the street folds flat
    up0, up1 = span(m, "T_UP", (2.75, 4.0), "tilts up", "straight down")
    na = night_air(round(up1 + 0.3, 2), 2)
    env = np.clip((up1 + 0.3 - tax(len(na))) / (up1 - up0 + 0.3), 0, 1)
    m.put("amb", na * env[:, None], 0.0, -23.0, label="night on the street: a distant city, the wind", align=None)
    # the street folds flat, back to front (s04's pop-up snaps); the camera tilts up over it to the plan
    for k, (t, _, c) in enumerate(cues_with(m, "folds flat")):
        m.put("efx", roomed(m, popup(k % 6 + 1), t, k, wet=-20.0), t, c["gain_db"] + CUE_TRIM - 2.0, pan=c["pan"],
              label="a card folds flat (the street folds away)")
    m.put("efx", paper_rise(round(up1 - up0, 2), 2), up0, -18.0, label="the camera tilts up over the street to the plan",
          align=None)
    ls = m.cue_of("lies down")
    if ls:
        t = float(ls["t"])
        m.put("efx", roomed(m, paper_whoosh(0.3, 9), t), t - 0.15, -29.0, label="the chalk outline lies down on the plan",
              align=None, sync=t)
    # the bank rules itself in: a chalk stroke a beat, and the vibraphone climbs the spy chord
    gr = g(S, "T_GROUPS", ())
    if gr and all(isinstance(x, (tuple, list)) and len(x) == 2 and _num(x[1]) for x in gr):
        gts = [float(x[1]) for x in gr]
        m.src[(m.sid, "T_GROUPS")] = "module"
    else:
        gts = list(m.ats(None, (3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5), "ruled", "chalk scratch"))
    gd = g(S, "GROUP_DUR", 0.42)
    t_dim = m.at("T_DIM", 7.75, "drops", "breath before")
    arp = (62, 65, 69, 73, 74, 77, 81)               # D4 F4 A4 C#5 D5 F5 A5
    for k, t in enumerate(gts):
        m.put("efx", roomed(m, chalk_scratch(round(gd, 2), 20 + k, press=0.9), t, k), t, -16.0,
              pan=0.25 * math.sin(1.7 * k), label="chalk scratch: a part of the bank ruled in")
        ring = float(np.clip(t_dim - 0.1 - t, 0.15, 1.4))
        m.put("music", vibe(arp[k % 7], ring, 0.5 + 0.05 * k, t_abs=m.t0 + t, depth=0.35, hard=0.5, seed=k), t, -15.0,
              pan=-0.3 + 0.1 * k)
    bassline(m, FB(m, 1), "D2 F2 A2 C#3 | D3 C#3 C3 B2 | Bb2 A2 G2 .", gain=-10.0, vel=0.78, gate=0.9,
             label="the bass walks in")
    drums(m, FB(m, 2), 1, level=-3.0, kick_=False, seed=3)
    m.put("music", brush_sweep(5, 3), FB(m, 3), -34.0, hall=-24.0, align=None)
    for pos, v in ((0, 0.45), (1, 0.8), (1.5, 0.35), (2, 0.55)):
        m.put("music", brush_tap(int(pos * 2) % 9, 0.0) * v, FB(m, 3) + sw(pos), -30.0, pan=0.15, hall=-22.0)
    m.mark(t_dim, "the music drops: a breath before the title")
    # the title: two strips slash in and cross (D, then the tritone); the stamps on the spy chord
    pre = float(np.clip(g(S, "STRIP_IN", 0.24), 0.08, 0.6))
    tw = m.at("T_STRIP_W", 8.0, "white strip", "first strip", "whoosh-thud")
    tr = m.at("T_STRIP_R", 8.5, "red strip", "second strip", "heavier")
    m.put("efx", roomed(m, whoosh_thud(round(pre, 3), 1, 0.0), tw), tw - pre, -10.0, pan=0.3,
          label="whoosh-thud: the white strip", sync=tw)
    m.put("efx", roomed(m, whoosh_thud(round(pre, 3), 2, 0.8), tr), tr - pre, -9.0, pan=-0.3,
          label="whoosh-thud: the red strip, heavier", sync=tr)
    hit(m, tw, 38, 0.55, gain=-11.0)
    hit(m, tr, 44, 0.85, gain=-11.0)
    td = m.at("T_DOUBLE", 9.0, "double")
    tc = m.at("T_CROSS", 9.5, "stamp: cross", "cross")
    for k, (t, lab) in enumerate(((td, "stamp: DOUBLE"), (tc, "stamp: CROSS"))):
        m.put("efx", roomed(m, stamp(k), t), t, -9.0, label=lab)
        stab(m, t, "DmM7", gain=-12.0, dur=0.22 if k == 0 else 0.55, vel=0.85 + 0.08 * k, seed=10 + k,
             fall=0.0 if k == 0 else 1.0)
    # the words lift away; the lamp; the X lands on the vault; the bass walks down into s02
    tl = m.at("T_LIFT", 10.0, "lift away", "lift")
    m.put("efx", paper_whoosh(0.7, 3), tl, -17.0, label="the words lift away", align=None)
    vibe_chord(m, tl, (65, 69, 72, 76), max(1.0, L - tl), gain=-18.0, vel=0.55, roll=0.04, depth=0.5, seed=4)
    m.put("music", bass(33, 0.9, 0.7, 2), FB(m, 5), -11.0, pan=-0.1, hall=-24.0)
    tlamp = m.at("T_LAMP", 10.5, "lamp")
    m.put("efx", roomed(m, switch_click(1, 0.8), tlamp), tlamp, -25.0, label="the table lamp clicks on")
    d = L - tlamp
    m.put("amb", lamp_hum(START[m.sid] + tlamp, d) * np.clip(tax(n_of(d)) / 0.6, 0, 1), tlamp, -44.0, fades=False)
    tland = m.at("T_LAND", 11.0, "x lands", "lands", "thud")
    m.put("efx", roomed(m, strip_thud(5), tland), tland, -12.0, label="thud: the X lands on the vault")
    m.put("efx", chalk_tap(9, 0.9), tland, -19.0)
    hit(m, tland, 38, 0.45, gain=-12.0)
    m.put("music", bass(37, 0.4, 0.75, 1), FB(m, 5) + 1.5, -11.0, pan=-0.1, hall=-24.0)     # C#2 -> D (s02)
    # the gold lens off the X: a celesta's fifths (in the vibraphone's A), a faint clink, a glint
    tg = m.at("T_GOLD", 11.1, "gold shimmer", "lens opens")
    for k, (p, dt) in enumerate(((81, 0.0), (88, 0.09), (93, 0.18))):          # A5 E6 A6
        m.put("music", celesta(p, 0.55 - 0.08 * k, 20 + k), tg + dt, -21.0, pan=0.45, hall=-16.0,
              label="the gold lens opens (celesta)" if k == 0 else None)
    m.put("efx", roomed(m, gold_clink(6, 0.6), tg + 0.05), tg + 0.05, -28.0, pan=0.45, label="a faint clink of gold")
    tgl = m.at("T_GLINT", 11.45, "glint")
    m.put("music", ting(6, 93) * 0.6, tgl, -27.0, pan=0.5, hall=-16.0, label="a glint off the gold")


# ============================================================================ s02 CREW (12-24): bars 6-11
@section("s02")
def s02(m, S):
    L = m.len
    m.put("amb", lamp_hum(START[m.sid], L), 0.0, -44.0, fades=False)
    t7 = FB(m, 7)
    # bar 6 a vamp; bars 7-10 THE THEME, plainly, on the vibraphone; bar 11 the band stops
    bassline(m, FB(m, 6), "D2 A1 C2 C#2", gain=-10.0, vel=0.72)
    drums(m, FB(m, 6), 1, level=-5.0, taps=False, kick_=False, seed=1)
    melody(m, t7 - BEAT, ((0, 1, 57),), gain=-13.0, vel=0.6, seed=7, label="the theme's pickup (her profile)")
    melody(m, t7, THEME, gain=-12.0, vel=0.78, seed=1, label="THE THEME, plainly (vibraphone)",
           labels={5: "the theme's second phrase lands (the Cracker)"})
    bassline(m, t7, "minor_a", gain=-10.0, vel=0.8)
    comp(m, t7, PROG_MINOR, gain=-21.0, vel=0.45, pattern="charleston", seed=1)
    drums(m, t7, 4, level=-2.0, seed=2)
    m.cover_span(t7 - BEAT, t7 + 16 * BEAT, "theme", "phrase")
    # the three pieces, the three faces
    q = m.at("T_QUEEN", 1.0, "queen")
    tsl = m.at("", q - 0.6, "sleeve comes", "cloth")
    m.put("efx", roomed(m, cloth(0.45, 1), tsl), tsl, -25.0, pan=-0.6, label="cloth: her sleeve", align=None)
    m.put("efx", piece_clack(1, 0.45), q, -10.0, pan=-0.3, label="clack: the white queen")
    tb = m.at("T_BISHOP", 3.5, "bishop")
    m.put("efx", roomed(m, cloth(0.35, 2), tb), tb - 0.5, -28.0, pan=0.4, align=None)
    m.put("efx", piece_clack(2, 0.3), tb, -11.0, pan=0.2, label="clack: the gold bishop")
    for name, dflt, words in (("T_HER_CALL", 2.0, ("lens opens on her",)), ("T_CR_CALL", 5.0, ("lens opens on his",))):
        tt = m.at(name, dflt, *words, win=1.0)
        m.put("efx", chalk_tap(30 + int(dflt), 0.3), tt, -25.0, label="a soft chalk tick: the lens opens")
    tg = m.at("T_GLINT", 4.8, "glint", "spectacles")
    m.put("music", ting(1, 93) * 0.8, tg, -22.0, pan=0.3, label="ting: the glint on his spectacles", hall=-16.0)
    tk = m.at("T_KNIGHT", 6.0, "knight slammed", "slammed", "thud")
    tsw = m.at("", tk - 0.3, "heavy sleeve", "swings in")
    m.put("efx", roomed(m, cloth(0.3, 3, heavy=1.0), tsw), tsw, -19.0, pan=0.6, label="a heavy sleeve swings in", align=None)
    m.put("efx", piece_slam(0), tk, -10.0, pan=0.2, label="THUD: the red knight slammed down")
    hit(m, tk, CHORDS[chord_at(tk, t7, PROG_MINOR)][0], 0.8, gain=-11.0)
    tcall = m.at("", 6.5, "knight in the dark", "low muted trumpet")
    m.put("music", brass(57, 0.85, 0.6, seed=3, mute="harmon", scoop=True, vib=True), tcall, -17.0, pan=0.25,
          label="a low muted trumpet note (the Knight)")
    tdraw = m.at("T_DRAW", 7.0, "draws", "cigarette", "ember")
    m.put("efx", cut(fx("ember_sizzle", seed=2), 0.9, 0.3), tdraw, -25.0, pan=-0.2, label="the cigarette crackles", align=None)
    m.put("vox", breath("draw"), tdraw - 0.05, -24.0, pan=-0.2, align=None)
    tex = m.at("T_EXHALE", 7.8, "smoke out", "breathes", "exhale")
    m.put("vox", breath("out"), tex, -22.0, pan=-0.1, label="he breathes the smoke out", align=None, key=True)
    ch = span(m, "", (8.5, 11.5), "chain", "creaks")
    m.put("efx", roomed(m, chain_creak(round(ch[1] - ch[0], 2), 1), ch[0]), ch[0], -28.0, pan=0.1,
          label="the lamp's chain creaks", align=None)
    thl = m.at("T_HIS_LOOK", 9.0, "his look", "semitone")
    m.put("music", brass(63, 0.7, 0.55, seed=5, mute="harmon", scoop=False, vib=False, fall=0.5), thl, -17.5, pan=0.2,
          label="his look: a muted note a semitone off")
    the = m.at("T_HER_LOOK", 10.0, "her look", "she knows", "low held")
    hold = max(0.8, L - the)
    m.put("music", arco(38, hold, 0.75, seed=1, attack=0.35, release=0.5), the, -13.0, pan=-0.05,
          label="a low held note: she knows", align=None)
    m.put("music", piano(26, hold, 0.45, 1), the, -18.0, pan=-0.1)
    m.put("music", piano(38, hold, 0.4, 2), the, -20.0, pan=-0.1)
    # her chalk taps the X, twice (the target); then lifts and glides off toward manhole A (s03 lands it)
    for k, (t, _, _) in enumerate(cues_with(m, "chalk tap on the x")):
        m.put("efx", roomed(m, chalk_tap(40 + k, 0.5 - 0.1 * k), t), t, -18.0 - 1.5 * k, pan=-0.05,
              label="chalk tap on the X")
    tgo = m.at("", 11.0, "glides over the plan", win=1.0)
    m.put("efx", roomed(m, cloth(0.55, 4), tgo), tgo, -27.0, pan=-0.3, label="her sleeve: the chalk glides off the X",
          align=None)
    # her low voice under the X: the briefing begins (a murmur, no words), until her look
    mu0, mu1 = span(m, "T_MURMUR", (9.05, 10.45), "her low voice", "briefing")
    say(m, "her", 0, mu0, -21.0, fit=min(mu1, the - 0.05) - mu0,
        label="her low voice under the X: the briefing begins (a murmur, no words)")


# ============================================================================ s03 PLAN (24-40): bars 12-19
def _s03_bible(m, S):
    """s03 from the bible (its stand-in): the theme twice, the drawn bell, the plant, a swell into
    the tilt."""
    L = m.len
    m.put("amb", lamp_hum(START[m.sid], L), 0.0, -44.0, fades=False)
    t0 = FB(m, 12)
    # THE THEME: vibraphone and a muted trumpet in unison as she chalks the route
    melody(m, t0, THEME, gain=-12.5, vel=0.75, seed=2, label="THE THEME: vibraphone and muted trumpet")
    melody(m, t0, THEME, inst="tpt", gain=-17.5, vel=0.62, seed=2, legato=0.9)
    bassline(m, t0, "minor_b", gain=-10.0, vel=0.8)
    comp(m, t0, PROG_MINOR, gain=-21.0, vel=0.45, pattern="push", seed=3)
    drums(m, t0, 4, level=-2.0, seed=4)
    # ... and again on the vibraphone alone, thinning out for the plant
    t1 = FB(m, 16)
    melody(m, t1, THEME, gain=-12.5, vel=0.72, seed=3, label="THE THEME: the vibraphone alone")
    bassline(m, t1, "D2 E2 F2 A2 | Bb2 D2 F2 Ab2 | G2 ~ D2 ~ | A1 ~ ~ ~", gain=-10.5, vel=0.75)
    comp(m, t1, PROG_MINOR[:3], gain=-22.0, vel=0.4, pattern="sparse", seed=4)
    drums(m, t1, 2, level=-4.0, kick_=False, seed=5)
    drums(m, t1 + 2 * BAR, 1, level=-8.0, taps=False, kick_=False, seed=6)
    m.cover_span(t0, t1 + 16 * BEAT, "theme", "phrase")
    # the drawn bell (it will ring in s07): a chalk loop and the faintest ting, on its pitch
    tbell = m.at("T_BELL", 12.8, "bell", win=2.5)
    m.put("efx", roomed(m, chalk_scratch(0.3, 78, circle=True, press=0.6), tbell), tbell, -24.0,
          label="a small bell drawn on the side door")
    m.put("music", ting(5, 86), tbell + 0.25, -34.0, pan=0.5, hall=-18.0)
    # the plant: as her hand lifts away, a soft tap: a dot on the sewer line under the vault
    tp = m.at("T_PLANT", 14.0, "plant", "soft tap", "small dot", "dot on the sewer", win=2.5)
    m.put("efx", roomed(m, chalk_tap(77, 0.35), tp), tp, -20.0, label="the plant: a soft tap (the dot)")
    # the tilt begins: a cymbal swells into s04's pop-up
    sw0, _ = span(m, "T_TILT", (15.0, 16.0), "tilt")
    sw0 = min(sw0, L - 0.4)
    m.put("music", cym_swell(L - sw0, 2), sw0, -25.0, label="a swell into the tilt", align=None)


@section("s03")
def s03(m, S):
    """Bars 12-15: THE THEME carries on, light and quick (vibraphone and a muted trumpet, pizzicato
    bass, brushes) while her chalk draws the route and the pieces hop along it on the beat; the
    guard's light ticks the timing (a low wooden tock). Bar 16: a vamp; the door clunks open and
    a bright accent as the arrow lands on the X. Bar 17: the band stops for the Knight's slam, and
    the low brass foreshadows the inversion: D down to G. Bars 18-19: the theme's last bar lands on
    a held D minor 9 as the plan is done; a paper whoosh rises into the tilt (s04)."""
    if isinstance(S, Stub):
        return _s03_bible(m, S)
    L = m.len
    m.put("amb", lamp_hum(START[m.sid], L), 0.0, -44.0, fades=False)
    # bars 12-15: the theme
    t12 = FB(m, 12)
    melody(m, t12, THEME, gain=-12.5, vel=0.75, seed=2,
           label="THE THEME carries on, light and quick (vibraphone, muted trumpet)")
    melody(m, t12, THEME, inst="tpt", gain=-18.5, vel=0.6, seed=2, legato=0.9)
    bassline(m, t12, "minor_b", gain=-10.0, vel=0.8)
    comp(m, t12, PROG_MINOR, gain=-21.5, vel=0.42, pattern="push", seed=3)
    drums(m, t12, 4, level=-3.0, seed=4)
    m.cover_span(t12, t12, "theme carries on", "light and quick")
    # her chalk: the chevron, the circled steps, the dotted route
    tch = m.at("T_CHEVRON", 0.5, "chevron")
    m.put("efx", roomed(m, chalk_tap(51, 0.75), tch), tch, -12.5, pan=-0.4, label="chalk tap: the chevron on manhole A")
    # the lenses on (1) and (3): a soft tick each; the lid's lets in a breath of the street
    for k, (t, _, c) in enumerate(cues_with(m, "lens opens on manhole", "lens opens on the guard")):
        lid = "manhole" in c["sfx"].lower()
        m.put("efx", roomed(m, chalk_tap(68 + k, 0.3), t), t, -22.0, pan=0.3 if lid else -0.4,
              label="a soft chalk tick: a step's lens opens")
        if lid:
            m.put("amb", night_air(1.4, 5), t + 0.05, -33.0, pan=0.3, align=None)
    for k, (t, _, _) in enumerate(cues_with(m, "circled step", "pops in")):
        m.put("efx", roomed(m, chalk_tap(60 + k, 0.3), t), t, -22.0, pan=0.15 * math.sin(1.3 * k + 0.5),
              label="a soft chalk tick: a circled step pops in")
    for k, (t, d, _) in enumerate(cues_with(m, "chalk dotting", "dry run of taps")):
        d = d or 0.8
        m.put("efx", roomed(m, chalk_dots(max(3, int(round(d * 8))), round(d, 2), 30 + k, 0.4), t), t, -20.5,
              pan=0.2 * math.sin(0.9 * k), label="chalk dotting along the route", align=None)
    # the pieces hop along it, landing on the beat (one clack a piece)
    for k, (t, _, c) in enumerate(cues_with(m, "chess piece")):
        mm = re.search(r"(\d+)\s+chess piece", c["sfx"])
        n = int(mm.group(1)) if mm else 1
        for j in range(min(n, 3)):
            dt = (0.0, 0.012, -0.009)[j]
            m.put("efx", roomed(m, piece_clack(70 + 3 * k + j, 0.3 + 0.12 * j), t + dt), t + dt,
                  -17.5 + (1.0 if n > 1 else 0.0) - 2.5 * j, pan=(-0.25, 0.1, 0.3)[j] + 0.1 * math.sin(k),
                  label="wooden clack: the pieces hop on the beat" if j == 0 else None)
    # the guard: the Cracker's old hand sets the pawn; her swish; the timing ring; the tocks
    tpw = m.at("T_PAWN", 4.5, "black pawn", "guard post")
    tsl = m.at("", tpw - 0.6, "sleeve and cuff", "old man")
    m.put("efx", roomed(m, cloth(0.4, 5), tsl), tsl, -25.0, pan=0.3, label="an old man's sleeve and cuff come in",
          align=None)
    m.put("efx", roomed(m, piece_clack(44, 0.7), tpw), tpw, -11.5, pan=-0.3, label="clack: the Cracker sets the black pawn")
    c0, c1 = span(m, "T_CONE", (5.0, 5.3), "soft swish", "sweeps")
    m.put("efx", roomed(m, paper_whoosh(round(max(0.25, c1 - c0 + 0.1), 2), 4), c0), c0, -22.0, pan=-0.2,
          label="a soft swish: she sweeps the guard's light out", align=None)
    r0, r1 = span(m, "T_RING", (5.2, 6.0), "timing ring", "circling")
    m.put("efx", roomed(m, chalk_scratch(round(r1 - r0, 2), 79, circle=True, press=0.6), r0), r0, -22.0, pan=-0.3,
          label="chalk circling the pawn: the timing ring", align=None)
    for j in range(4):
        m.put("efx", chalk_tap(85 + j, 0.25), r0 + (r1 - r0) * (j + 0.5) / 4, -27.0, pan=-0.3)
    for k, (t, _, _) in enumerate(cues_with(m, "wooden tock")):
        m.put("efx", roomed(m, tock(k % 3), t, wet=-16.0), t, -21.0, pan=-0.3,
              label="a low wooden tock: the guard's light at the end of its swing")
    # the vault: the lens on the dial, right, left, right; CLUNK, the door swings open
    tl0 = m.at("", g(S, "T_LENS", (7.0, 8.06))[0], "lens opens on the vault dial", "lens opens")
    m.put("efx", roomed(m, chalk_tap(66, 0.3), tl0), tl0, -21.0, pan=0.4, label="a soft chalk tick: the lens on the dial")
    turns = g(S, "TURNS", ())
    tts = [float(x[0]) for x in turns if isinstance(x, (tuple, list)) and x and _num(x[0])]
    if not tts:
        tts = [t for t, _, _ in cues_with(m, "ratchet", "safe dial")]
    for k, t in enumerate(tts):
        m.put("efx", roomed(m, dial_ratchet(0.24, 5 + k, 40.0), t), t, -15.0, pan=0.4,
              label="a safe dial's ratchet (fine clicks)", align=None)
    tck = m.at("T_CLICK", 8.0, "clunk", "bolt draws back")
    m.put("efx", roomed(m, fence_clunk(1), tck), tck, -10.5, label="CLUNK: the bolt draws back")
    m.put("efx", roomed(m, vault_groan(1.3, 4), tck + 0.08), tck + 0.08, -24.0, pan=0.2, align=None)
    # bar 16: the vamp; the arrow lands on the X: a bright accent
    t16 = FB(m, 16)
    bassline(m, t16, "D2 F2 A2 C3", gain=-10.5, vel=0.78)
    comp(m, t16, (("Dm9", 4),), gain=-22.0, vel=0.4, pattern="push", seed=8)
    drums(m, t16, 1, level=-4.0, seed=5)
    tx = m.at("T_X", 8.4, "lands on the x", "arrow lands")
    m.put("efx", roomed(m, chalk_tap(68, 0.85), tx), tx, -12.5, label="chalk tap: the arrow lands on the X")
    vibe_chord(m, tx, (81, 86, 88), 1.4, gain=-15.5, vel=0.7, roll=0.0, hard=0.85, depth=0.3, seed=21,
               label="a bright accent in the score (vibraphone, ride bell)")
    m.put("music", ride(2, bell=1.0), tx, -21.0, pan=0.3, hall=-20.0)
    # bar 17: the Knight's red hand: the band stops; THUD; the low brass, D down to G
    tgr = m.at("T_GRAB", 10.2, "snatched")
    tsw = m.at("", tgr - 0.35, "heavy sleeve", "swings in")
    m.put("efx", roomed(m, cloth(0.3, 7, heavy=1.0), tsw), tsw, -18.0, pan=0.6, label="a heavy sleeve swings in fast",
          align=None)
    m.put("efx", roomed(m, piece_scrape(3, 0.3), tgr), tgr, -16.0, pan=0.2,
          label="the red knight snatched up (a wooden scrape)", align=None)
    tth = m.at("T_THUD", 10.75, "slammed down", "thud")
    m.put("efx", piece_slam(1), tth, -8.5, pan=0.3, label="THUD: the red knight slammed down by the street")
    for j, dt in enumerate((0.04, 0.075, 0.12, 0.19)):              # the pieces rattle
        m.put("efx", roomed(m, piece_clack(90 + j, 0.25), tth + dt), tth + dt, -21.0 - 2.0 * j, pan=-0.3 + 0.2 * j)
    m.put("efx", roomed(m, strip_thud(7), tth + 0.03), tth + 0.03, -20.0, pan=-0.1)    # the drawn door claps shut
    hit(m, tth, 46, 0.8, gain=-11.0)
    # the briefing, murmured over the plan (no words, under the score): her low voice leads down the
    # route; the Cracker hums, then asks as he sets the guard; she answers through the light's sweep,
    # and right, left, right at the dial; he has opened worse; the Knight cuts in, and his slam ends it
    mu0, mu1 = span(m, "T_MURMUR", (0.1, 10.7), "briefing", "murmured")
    say(m, "her", 1, mu0, -21.0, fit=tpw - 0.55 - mu0, label="the briefing, murmured over the plan (no words)")
    say(m, "cracker", 1, mu0 + 2.25, -24.0)
    say(m, "cracker", 2, tpw - 0.5, -22.0, fit=c0 + 0.45 - (tpw - 0.5))
    say(m, "her", 2, c0 + 0.45, -21.5, fit=tl0 - 0.05 - (c0 + 0.45))
    say(m, "her", 4, tl0, -21.5, fit=tck - 0.05 - tl0)
    e = say(m, "cracker", 6, tck + 0.15, -22.0)
    k0 = max(e - 0.25, tgr - 1.2)
    say(m, "knight", 2, k0, -20.0, fit=min(mu1, tth - 0.04) - k0)
    tdot = m.at("T_DOT", tth, "the dot", "buried")
    m.put("efx", chalk_tap(77, 0.3), tdot, -30.0, pan=-0.2, label="the dot: a soft chalk tap, buried under the thud")
    melody(m, tth, ((0, 1, 62), (1, 1.5, 55)), inst="tbn", gain=-15.0, vel=0.75, seed=12,
           label="the low brass: D down to G, the inversion's first step (a foreshadowing)")
    m.put("music", arco(31, 0.85, 0.6, seed=12, attack=0.08, release=0.3), tth + BEAT, -17.0, pan=-0.05, align=None)
    # bar 18: the way out, the car, the bell; the theme's last bar lands on a held chord
    t18 = FB(m, 18)
    cp = m.cue_of("held chord", "plan is done")
    tl = t18 + round(((float(cp["t"]) if cp else 13.5) - t18) / BEAT) * BEAT      # on the beat nearest the cue
    tl = float(np.clip(tl, t18 + 3 * BEAT, L - 1.0))
    melody(m, tl - sw(14), THEME, gain=-12.5, vel=0.72, seed=6, start=12, stop=14)
    bassline(m, tl - 3 * BEAT, "A1 E2 C#2", gain=-10.5, vel=0.75)
    comp(m, tl - 3 * BEAT, (("A7b9", 2),), gain=-22.0, vel=0.38, pattern="sparse", seed=9)
    drums(m, t18, 1, level=-8.0, kick_=False, seed=6)
    hold = L - tl + 0.3
    m.put("music", vibe(62, hold, 0.72, t_abs=m.t0 + tl, depth=0.5, hard=0.5, seed=31), tl, -12.5,
          label="the plan is done: the theme lands on a held chord")
    vibe_chord(m, tl + 0.03, (53, 57, 60, 64), hold, gain=-18.5, vel=0.5, roll=0.03, depth=0.5, seed=32)
    m.put("music", bass(38, 0.5, 0.8, 4), tl, -11.0, pan=-0.1, hall=-24.0)
    m.put("music", arco(38, hold, 0.6, seed=8, attack=0.2, release=0.6), tl, -15.5, pan=-0.05, align=None)
    m.put("music", arco(45, hold, 0.45, seed=9, attack=0.3, release=0.6), tl, -20.0, pan=0.1, align=None)
    m.cover_span(tl - 0.2, tl + 0.2, "held chord", "plan is done")
    tcar = m.at("T_CAR", 12.45, "the car drawn", "chalk 'tock'")
    m.put("efx", roomed(m, pitch(chalk_tap(81, 0.95), -4), tcar), tcar, -14.5, pan=0.5,
          label="a chalk 'tock': the car drawn by the street")
    tbell = m.at("T_BELL", 13.0, "bell on the side door", "bell")
    m.put("efx", roomed(m, chalk_scratch(0.22, 78, circle=True, press=0.5), tbell), tbell, -23.0, pan=0.5,
          label="a tiny chalk scratch: a bell on the side door (no ring)", align=None)
    # bar 19: the tilt: a paper whoosh rises, a cymbal swells into s04's pop-up
    tv = g(S, "T_TILT", 14.0) if _num(getattr(S, "T_TILT", None)) else g(S, "T_TILT", (14.0, 16.0))[0]
    cw = m.cue_of("rising paper whoosh", "tilts down")
    w0 = float(cw["t"]) if cw else tv + 0.4
    wd = float(np.clip(float(cw.get("dur") or 0.0) if cw else L - w0, 0.4, max(0.4, L - w0 + 0.2)))
    m.put("efx", paper_rise(round(wd, 2), 2), w0, -16.0, label="a rising paper whoosh: the camera tilts down", align=None)
    m.put("music", cym_swell(round(max(0.5, L - tv), 2), 2), tv, -26.0, align=None)


# ============================================================================ s04 NIGHT (40-52): bars 20-25
def _s04_bible(m, S):
    """s04 from the bible (its stand-in)."""
    L = m.len
    clock(m)
    # the pop-up: a piano run up the spy chord as the walls fold up out of the plan
    p0, p1 = span(m, "T_POPUP", (0.0, 3.0), "pop-up", "fold up", "walls rise", "extrude")
    pops = []
    t = p0
    while t < p1 - 1e-6:
        pops.append(t)
        t += 0.5
    for k, t in enumerate(pops):
        m.put("efx", roomed(m, popup(k % 6), t, k, wet=-20.0), t, -15.0 - 2.0 * (k % 2), pan=0.5 * math.sin(2.3 * k),
              label="paper pops: the walls fold up" if k == 0 else None)
    run = (38, 41, 45, 49, 50, 53, 57, 61, 62, 65, 69, 73)
    for k, p in enumerate(run):
        m.put("music", piano(p, 0.35, 0.45 + 0.03 * k, k), FB(m, 20) + k * BEAT * 2 / 6.0, -15.0, pan=-0.25 + 0.04 * k,
              label="a rising piano run (the pop-up)" if k == 0 else None)
    tmoon = m.at("T_MOON", 1.5, "moon")
    vibe_chord(m, tmoon, (81, 86), 1.6, gain=-19.0, vel=0.5, roll=0.06, depth=0.55, seed=9, label="the moon pops up")
    tlamps = m.at("T_LAMPS", 2.5, "street lamp", "lamps")
    for k in range(2):
        m.put("efx", roomed(m, switch_click(4 + k, 0.7), tlamps + 0.25 * k), tlamps + 0.25 * k, -24.0, pan=(-0.5, 0.5)[k],
              label="the street lamps come on" if k == 0 else None)
    # the heist groove: the trumpet calls the theme's head, the vibraphone answers
    t21 = FB(m, 21)
    m.put("music", piano(74, 1.2, 0.6, 3), t21, -15.0, pan=0.2)
    bassline(m, t21, "vamp", gain=-10.0, vel=0.8)
    drums(m, t21, 2, level=-2.0, seed=7)
    comp(m, t21, (("Dm6", 4), ("Dm6", 4)), gain=-22.0, vel=0.42, pattern="push", seed=5)
    melody(m, t21, THEME, inst="tpt", gain=-14.5, vel=0.75, seed=4, stop=4, label="the trumpet calls the theme's head")
    melody(m, t21, THEME, gain=-14.0, vel=0.65, start=4, stop=9, seed=5)
    curb = span(m, "T_CURB", (3.0, 4.5), "curb", "arrive", "steps along")
    steps(m, "her", curb[0], curb[1], 0.5, gain=-22.0, pan=-0.3, room_="street", label="their steps along the curb")
    steps(m, "knight", curb[0] + 0.25, curb[1], 0.5, gain=-21.0, pan=0.2, room_="street", k0=3)
    tsc = m.at("T_SCRAPE", 3.8, "scrape", "lifts manhole")
    m.put("efx", rev(manhole_scrape(0.6, 1), -14.0, 1, "street"), tsc, -11.0, pan=-0.2,
          label="iron scrape: he lifts manhole A", align=None)
    tcl = m.at("T_CLANK", 4.5, "clank", "lid")
    m.put("efx", rev(manhole_clank(1), -12.0, 2, "street"), tcl, -9.5, pan=-0.3, label="clank: the lid set down")
    for k, t in enumerate(m.ats("T_DOWN", (5.0, 5.5, 6.0), "goes down", "one goes down", "down the rungs", n=3)):
        m.put("efx", rev(rung(k), -10.0, k, "cell"), t, -17.0, pan=-0.1, label="a rung: one goes down")
        m.put("feet", footstep(("her", "cracker", "knight")[k % 3], k, "cell"), t + 0.18 - STEP_PRE, -22.0)
    # the sewer: the groove goes dark; the clock starts (46.0)
    t23 = FB(m, 23)
    bassline(m, t23, "vamp2", gain=-11.0, vel=0.72)
    bassline(m, t23 + 2 * BAR, "A1 ~ E2 .", gain=-11.0, vel=0.7)
    drums(m, t23, 3, level=-6.0, kick_=False, seed=8)
    vibe_chord(m, t23, (53, 57, 59, 64), 3.8, gain=-20.0, vel=0.5, depth=0.55, seed=6)
    vibe_chord(m, t23 + 2 * BAR, (55, 58, 61, 65), 1.8, gain=-20.0, vel=0.5, depth=0.55, seed=7)
    melody(m, t23 + 2 * BAR, ((0, 1, 69), (1, 1, 67), (2, 1, 65), (3, 0.5, 64)), inst="tpt", gain=-16.5, vel=0.6, seed=9)
    if 0.0 <= HEIST_T0 - m.t0 < L:
        m.mark(HEIST_T0 - m.t0, "the stopwatch starts: the clock")
    m.cover("stopwatch", "the clock", "ticks")
    s0 = m.at("T_SEWER", 6.0, "sewer", "tunnel", "drips", win=2.0)
    m.put("amb", sewer_bed(round(L - s0 + 0.3, 2), 1), s0, -31.0, label="the sewer: drips, the channel", align=None)
    for k, t in enumerate((6.62, 7.93, 9.21, 10.37, 11.46)):
        if t > s0 + 0.2:
            m.put("efx", drip(k), t, -25.0, pan=0.5 * math.sin(2.1 * k))
    w0, w1 = span(m, "T_WATER", (7.0, 10.0), "water", "wade")
    water_steps(m, w0, w1, 0.5, gain=-20.0, label="their steps in water")
    for k, t in enumerate(m.ats("T_UP", (10.0, 10.5), "up the", "climb", "rungs up")):
        m.put("efx", rev(rung(5 + k), -9.0, k, "cell"), t, -18.0, pan=0.15, label="up the rungs")
    th = m.at("T_HATCH", 11.0, "hatch", "creak")
    m.put("efx", rev(hatch_creak(0.8, 1), -10.0, 3, "cell"), th, -14.0, label="creak: the hatch opens", align=None)


def cgain(m, t, *words, default=-14.0, win=0.1):
    """The gain of this scene's cue at t (with any of words), at this mix's level, or default."""
    c = m.cue_near(t, *words, win=win)
    return float(c["gain_db"]) + CUE_TRIM if c else default


def cpan(m, t, *words, default=0.0):
    """The pan of this scene's cue at t (with any of words), or default."""
    c = m.cue_near(t, *words, win=0.06)
    return float(c["pan"]) if c else default


@section("s04")
def s04(m, S):
    """Bar 20, the pop-up: the lamp goes out and the night comes up; a piano run climbs the spy
    chord as the walls rise, the crew pop up out of the plan a beat apart and the street's cards
    snap up. Bars 21-22, the street: the heist groove, the trumpet calls the theme's head; the band
    stops for the manhole (the vibraphone answers alone over the hook and the scrape) and hits
    the CLANK on beat 4. Bar 23: the clock starts on the bar line (46.0), one down the rungs a
    beat; the groove goes dark. Bars 24-25, the sewer: water, drips, the climb, the hatch."""
    if isinstance(S, Stub):
        return _s04_bible(m, S)
    L = m.len
    clock(m)
    if 0.0 <= HEIST_T0 - m.t0 < L:
        m.mark(HEIST_T0 - m.t0, "the heist clock starts")
    m.cover("heist clock", "woodblock tick", "stopwatch")
    # the lamp goes out (its hum runs on from s03 to the click); the night comes up
    tl0 = float(g(S, "T_LAMP", (0.2, 1.4))[0])
    h = lamp_hum(START[m.sid], tl0 + 0.04)
    m.put("amb", h * np.clip((tl0 + 0.04 - tax(len(h))) / 0.04, 0, 1), 0.0, -44.0, fades=False)
    m.put("efx", roomed(m, switch_click(3, 0.7), tl0), tl0, -27.0, label="the table lamp clicks off")
    c0, c1 = g(S, "T_CUT", (5.75, 7.1))
    na = night_air(round(c1 - tl0 + 0.4, 2), 1)
    u = tax(len(na))
    env = np.clip(u / 1.2, 0, 1) * np.clip((c1 + 0.4 - tl0 - u) / max(0.5, c1 - c0), 0, 1)
    m.put("amb", na * env[:, None], tl0, -29.0, label="night air comes up: a distant city, a far siren, wind", align=None)
    # bar 20: the walls rise (the paper carries on from s03's whoosh); the pieces sink; the pops
    cw = m.cue_of("rising paper whoosh", "walls rise")
    w0, wd = (float(cw["t"]), float(cw.get("dur") or 2.8)) if cw else (0.0, 2.8)
    m.put("efx", paper_carry(round(wd, 2), 3), w0, -17.0, label="the walls rise: the paper whoosh carries on", align=None)
    sinks = sorted(float(v) for v in dict(g(S, "SINK", {})).values() if _num(v))
    for k, t in enumerate(sinks):
        m.put("efx", roomed(m, paper_whoosh(0.3, 12 + k), t), t, -27.0 - 0.5 * k, pan=-0.3 + 0.2 * k,
              label="the chess pieces sink into the paper (soft slides)" if k == 0 else None, align=None)
    for k, (t, _, c) in enumerate(cues_with(m, "pop-up snap")):
        m.put("efx", roomed(m, popup(k % 6), t, k, wet=-20.0), t, c["gain_db"] + CUE_TRIM - 2.0, pan=c["pan"],
              label="a paper pop-up snap")
    run = (38, 41, 45, 49, 50, 53, 57, 61, 62, 65, 69, 73)
    for k, p in enumerate(run):
        m.put("music", piano(p, 0.35, 0.45 + 0.03 * k, k), FB(m, 20) + k * BEAT * 2 / 6.0, -15.0, pan=-0.25 + 0.04 * k,
              label="a rising piano run (the pop-up)" if k == 0 else None)
    pops = dict(g(S, "POPS", {}))
    tmoon = float(pops["moon"]) if _num(pops.get("moon")) else 3.5
    vibe_chord(m, tmoon, (81, 86), 1.6, gain=-19.0, vel=0.5, roll=0.06, depth=0.55, seed=9,
               label="the moon pops up (vibraphone)")
    # the crew walk west along the curb: each footfall the picture has
    for k, (t, _, c) in enumerate(cues_with(m, "footstep:")):
        s = c["sfx"].lower()
        if "water" in s:
            continue
        who = ("knight" if ("heavy" in s or "knight" in s) else
               "cracker" if ("cracker" in s or "shuffl" in s or "old man" in s) else "her")
        m.put("feet", footstep(who, k, "street", seed=k % 5), t - STEP_PRE, c["gain_db"] + CUE_TRIM, pan=c["pan"],
              label=f"footstep ({who})", sync=t)
    # bars 21-22: the groove; the trumpet calls the theme's head; stop-time for the manhole
    t21, t22 = FB(m, 21), FB(m, 22)
    m.put("music", piano(74, 1.2, 0.6, 3), t21, -15.0, pan=0.2)
    bassline(m, t21, "D2 F2 A2 B2 | C3 B2", gain=-10.0, vel=0.8)
    drums(m, t21, 1, level=-2.0, seed=7)
    for pos, v in ((0, 0.5), (1, 0.85)):
        m.put("music", brush_tap((pos + 3) % 9, 0.3 if pos else 0.0) * v, t22 + pos * BEAT, -29.0, pan=0.15, hall=-22.0)
    m.put("music", kick(1, 0.25), t22, -31.0, hall=None)
    comp(m, t21, (("Dm6", 4),), gain=-22.0, vel=0.42, pattern="push", seed=5)
    comp(m, t22, (("Dm6", 2),), gain=-22.0, vel=0.4, pattern="sparse", seed=6)
    melody(m, t21, THEME, inst="tpt", gain=-14.5, vel=0.75, seed=4, stop=4, label="the trumpet calls the theme's head")
    melody(m, t21, THEME, gain=-14.5, vel=0.62, start=4, stop=8, seed=5)
    tturn = m.at("T_TURN", 3.5, "coat rustles", "turns back")
    m.put("efx", roomed(m, cloth(0.45, 6, heavy=1.0), tturn), tturn, -24.0, pan=cpan(m, tturn, "coat"),
          label="a heavy coat rustles: the Knight turns back", align=None)
    thk = m.at("T_HOOK", 4.6, "hook the lid", "iron tick")
    m.put("efx", roomed(m, metal_tap(2), thk), thk, -18.0, pan=cpan(m, thk, "iron tick"),
          label="iron tick: his fingers hook the lid's edge")
    m.put("vox", roomed(m, grunt(1), thk + 0.05), thk + 0.05, -23.0, pan=cpan(m, thk, "iron tick"), align=None, key=True)
    cs = m.cue_of("iron scrape", "levered up")
    s0, sd = (float(cs["t"]), float(cs.get("dur") or 0.45)) if cs else (float(g(S, "T_LIFT", 4.9)), 0.45)
    m.put("efx", rev(manhole_scrape(round(max(0.3, sd + 0.1), 2), 1), -14.0, 1, "street"), s0, -11.0,
          pan=cpan(m, s0, "scrape"), label="iron scrape: the lid dragged out of the hole", align=None)
    tcl = m.at("T_CLANK", 5.5, "clank", "falls flat")
    m.put("efx", rev(manhole_clank(1), -12.0, 2, "street"), tcl, -11.0, pan=cpan(m, tcl, "clank"),
          label="CLANK: the iron lid falls flat on the road")
    hit(m, tcl, 45, 0.6, gain=-14.5)
    # bar 23, the descent: the camera sinks; one down the rungs a beat, a splash each at the foot
    cwh = m.cue_of("low whoosh", "camera sinks")
    k0, kd = (float(cwh["t"]), float(cwh.get("dur") or 2.0)) if cwh else (c0, 2.0)
    m.put("efx", sink_whoosh(round(kd, 2), 2), k0, -19.0, label="a low whoosh: the camera sinks into the sewer", align=None)
    down = dict(g(S, "DOWN", {}))
    climb = float(g(S, "CLIMB", 1.5))
    for k, (who, t) in enumerate(sorted(((w, float(t)) for w, t in down.items() if _num(t)), key=lambda kv: kv[1])):
        name = {"architect": "her", "cracker": "cracker", "knight": "knight"}.get(who, "her")
        pn = cpan(m, t, "rung")
        m.put("efx", rev(rung(k), -10.0, k, "cell"), t, -17.0, pan=pn, label=f"a shoe on the first rung: {who} goes down")
        m.put("feet", footstep(name, k, "cell", seed=k), t + 0.02 - STEP_PRE, -25.0, pan=pn)
        for j in range(4):
            tj = t + 0.2 + j * (climb - 0.35) / 4
            m.put("efx", rev(dsp.sos(rung(3 + k + j), "lowpass", 2500.0, 2), -8.0, j, "cell"), tj, -25.0 - j, pan=pn,
                  label="a quick run of rung steps going down" if j == 0 else None)
        m.put("feet", water_step(k + 2, 0.9), t + climb, -15.0, pan=cpan(m, t + climb, "splash", default=pn),
              label=f"splash: {who} steps off the ladder into the water")
    for k, (t, _, c) in enumerate(cues_with(m, "footstep in shallow water", "sewer slosh")):
        m.put("feet", water_step((k + 3) % 8, (0.45, 0.6, 0.75)[k % 3]), t, c["gain_db"] + CUE_TRIM + 1.0, pan=c["pan"],
              label="a footstep in shallow water")
    for k, (t, _, c) in enumerate(cues_with(m, "a drip")):
        m.put("efx", drip(k % 5), t, c["gain_db"] + CUE_TRIM, pan=c["pan"], label="a drip (the pipe)")
    s0_ = c0 + 0.4
    m.put("amb", dsp.fade(sewer_bed(round(L - s0_ + 0.3, 2), 1), 1.0, 0.0), s0_, -31.0,
          label="the sewer: the channel, the air of the pipe", align=None)
    t23 = FB(m, 23)
    bassline(m, t23, "vamp2", gain=-11.0, vel=0.72)
    bassline(m, t23 + 2 * BAR, "A1 ~ E2 .", gain=-11.0, vel=0.7)
    drums(m, t23, 3, level=-6.0, kick_=False, seed=8)
    vibe_chord(m, t23, (53, 57, 59, 64), 3.8, gain=-20.0, vel=0.5, depth=0.55, seed=6)
    vibe_chord(m, t23 + 2 * BAR, (55, 58, 61, 65), 1.8, gain=-20.0, vel=0.5, depth=0.55, seed=7)
    melody(m, t23 + 2 * BAR, ((0, 1, 69), (1, 1, 67), (2, 1, 65), (3, 0.5, 64)), inst="tpt", gain=-16.5, vel=0.6, seed=9)
    # bars 24-25: the window in the bank's wall; she climbs; the hatch
    win0 = float(g(S, "T_WINDOW", (9.8, 10.6))[0])
    m.put("efx", roomed(m, chalk_scratch(0.4, 61, press=0.6), win0), win0, -22.0, pan=cpan(m, win0, "window"),
          label="a soft chalk scratch: the cutaway window", align=None)
    tup = m.at("T_UP", 10.4, "rung steps going up", "going up")
    cu = m.cue_near(tup, "going up", win=0.1)
    ud = float(cu.get("dur") or 0.8) if cu else 0.8
    tcr = m.at("T_CREAK", 11.2, "hinge creak", "pushes the hatch")
    nup = max(2, int((min(tup + ud, tcr) - tup) / 0.22))
    for j in range(nup):
        tj = tup + 0.22 * j
        m.put("efx", rev(rung(9 + j), -10.0, j, "cell"), tj, -24.0, pan=cpan(m, tup, "going up"),
              label="rung steps going up, quick and light (her)" if j == 0 else None)
    m.put("efx", rev(hatch_creak(0.9, 1), -10.0, 3, "cell"), tcr, -14.0, pan=cpan(m, tcr, "creak"),
          label="a long hinge creak: she pushes the hatch up", align=None)
    tth = m.at("T_THUD", 11.5, "hatch falls open", "thud")
    m.put("efx", roomed(m, wood_thunk(2, 0.8), tth), tth, -14.0, pan=cpan(m, tth, "thud"),
          label="thud: the hatch falls open on the store room floor")


# ============================================================================ s05 GUARD (52-66): bars 26-32
@section("s05")
def s05(m, S):
    """Bars 26-27, the corridor: the score drops away to the clock's tick alone, a dark held
    corridor (its room tone, the building humming low on D); his light clicks on, his hard heels,
    his belt creaking as the light swings. Bars 28-30, the stealth map: the corridor folds down
    into the plan; a tiptoe bass under the plan's timing (a low tock at each end of the swing);
    each piece hops the gap on the beat with a vibraphone note (D, F, A rising); it unfolds. Bars
    30-31, the near miss: the tiptoe ends on the CLANK; the score holds its breath (one low muted
    note on a D pedal); the cat, the can. Bar 32: he breathes out and walks off; the band creeps
    back as they slip into the dark and the camera pushes down to the dial (step 4)."""
    if isinstance(S, Stub):
        return _s05_bible(m, S)
    L = m.len
    clock(m)
    t28, t32 = FB(m, 28), FB(m, 32)
    # the corridor: the score drops away to the tick; the room tone; the building hums, low, on D
    cd = m.cue_of("score drops away", "drops away to the heist clock")
    td = float(cd["t"]) if cd else 0.0
    dd = float(cd.get("dur") or 9.5) if cd else 9.5
    m.mark(td, "the score drops away to the tick")
    rt = bed("room_tone", round(L + 0.2, 2), 5, 0.3, 0.3)
    m.put("amb", rt, 0.0, -30.0, label="the corridor: its room tone, the building's hum", align=None)
    hum = (np.sin(TWO_PI * hz(38) * tax(n_of(dd))) + 0.4 * np.sin(TWO_PI * hz(50) * tax(n_of(dd)) + 0.7))
    m.put("amb", dsp.fade(hum, 1.0, 1.5), td, -50.0, align=None)
    tcl = m.at("T_CLICK", 0.35, "flashlight clicks on")
    m.put("efx", roomed(m, flashlight_click(1), tcl), tcl, cgain(m, tcl, "flashlight", default=-16.0) - 4.0,
          pan=cpan(m, tcl, "flashlight", default=-0.4), label="a flashlight clicks on")
    for k, (t, _, c) in enumerate(cues_with(m, "guard's hard heel")):
        m.put("feet", footstep("guard", k, "court", seed=k % 5), t - STEP_PRE, c["gain_db"] + CUE_TRIM + 1.0,
              pan=c["pan"], label="footstep: the guard's hard heel", sync=t)
    cb = m.cue_of("leather belt")
    if cb:
        b0, b1 = float(cb["t"]), float(cb["t"]) + float(cb.get("dur") or 3.0)
        k = 0
        while b0 + k < b1 - 0.2:
            m.put("efx", roomed(m, glove_creak(k % 3, 0.35), b0 + k), b0 + k, cb["gain_db"] + CUE_TRIM - 2.0 - 2.0 * k,
                  pan=float(cb["pan"]), label="the guard's leather belt creaks as his light swings" if k == 0 else None,
                  align=None)
            k += 1
    # bar 28: the corridor folds down into the plan (paper); the plan's timing; the pieces hop the gap
    tu0, tu1 = g(S, "T_TILT_UP", (4.0, 5.0))
    m.put("efx", paper_whoosh(round(tu1 - tu0, 2), 21), tu0, cgain(m, tu0, "paper fold", default=-18.0) - 6.0,
          label="a paper fold and a soft whoosh: the corridor folds down into the plan", align=None)
    m.put("efx", roomed(m, cut(mono(fx("page_flip", seed=3)), 0.4, 0.1), tu0 + 0.1), tu0 + 0.1, -30.0, align=None)
    for k, (t, _, c) in enumerate(cues_with(m, "low wooden tock")):
        m.put("efx", tock(k % 3), t, c["gain_db"] + CUE_TRIM - 1.0, pan=c["pan"], label="a low wooden tock (the plan's timing)")
    bassline(m, t28, "D2 . A1 . | D2 . A1 . | F2 . A1 .", gain=-12.5, vel=0.7, stacc=0.13, label="the tiptoe bass")
    drums(m, t28, 3, level=-11.0, taps=False, kick_=False, hat=True, seed=9)
    notes = (74, 77, 81)
    for k, (t, _, c) in enumerate(cues_with(m, "piece clack")):
        m.put("efx", piece_clack(50 + k, 0.35), t, c["gain_db"] + CUE_TRIM - 4.0, pan=c["pan"],
              label="a wooden piece clack: a piece hops the gap", align="onset")
        m.put("music", vibe(notes[k % 3], 0.9, 0.6, t_abs=m.t0 + t, seed=k), t, -16.0, pan=(-0.3, 0.0, 0.3)[k % 3])
    td0, td1 = g(S, "T_TILT_DOWN", (8.5, 9.5))
    m.put("efx", paper_whoosh(round(td1 - td0, 2), 22), td0, cgain(m, td0, "paper unfold", default=-18.0) - 6.0,
          label="a paper unfold and a soft whoosh: the corridor stands up again", align=None)
    m.put("efx", roomed(m, popup(4), td1 - 0.12, wet=-20.0), td1 - 0.12, -27.0)
    # the near miss: the Cracker at the mouth; the CLANK; the score holds its breath; the cat; the can
    tst = m.at("", float(g(S, "T_STEP", (9.5, 9.75))[0]) + 0.1, "shuffling step")
    m.put("feet", footstep("cracker", 7, "court", seed=2), tst - STEP_PRE, cgain(m, tst, "shuffling", default=-26.0),
          pan=cpan(m, tst, "shuffling"), label="a soft shuffling step: the Cracker reaches the doorway", sync=tst)
    tbe = m.at("", float(g(S, "T_BEND", (9.7, 9.9))[0]), "wheezing breath")
    wz = dsp.sos(pitch(breath("in"), -3.0), "lowpass", 3200.0, 2)
    m.put("vox", roomed(m, wz, tbe), tbe, cgain(m, tbe, "wheezing", default=-24.0) - 2.0, pan=cpan(m, tbe, "wheezing"),
          label="an old man's wheezing breath, held in", align=None, key=True)
    tck = m.at("T_CLANK", 10.0, "stethoscope", "clank")
    m.put("efx", roomed(m, steth_clank(1), tck), tck, -13.5, pan=cpan(m, tck, "clank", default=0.2),
          label="CLANK: the stethoscope's chest-piece on the iron pipe")
    m.put("efx", ripple(1, 90.0, 0.9), tck + 0.02, -23.0)
    tsp = m.at("", float(g(S, "T_SPIN", (10.15, 10.4))[0]), "coat swishes", "spins round")
    m.put("efx", roomed(m, cloth(0.3, 5, heavy=1.0), tsp), tsp, cgain(m, tsp, "coat swishes", default=-17.0) - 4.0,
          pan=cpan(m, tsp, "coat"), label="a heavy coat swishes: the guard spins round", align=None)
    m.put("feet", footstep("guard", 9, "court"), tsp + 0.14 - STEP_PRE, -19.0, pan=cpan(m, tsp, "coat"))
    the = m.at("", float(g(S, "T_EYES", 10.72)) - 0.05, "held breath", "single low muted")
    m.put("music", brass(56, 1.15, 0.5, seed=7, mute="harmon", scoop=False, vib=False), the, -18.0, pan=0.1,
          label="the score's held breath: a single low muted note (G#)")
    m.put("music", arco(38, round(float(g(S, "T_SIGH", 11.9)) - the + 0.2, 2), 0.45, seed=6, attack=0.3, release=0.4),
          the, -21.0, align=None)
    tar = m.at("", float(g(S, "T_ARCH", (10.8, 11.0))[0]), "cat's hiss")
    m.put("vox", roomed(m, cat_hiss(1), tar), tar, cgain(m, tar, "hiss", default=-16.0) - 4.0,
          pan=cpan(m, tar, "hiss", default=0.45), label="a cat's hiss", align=None)
    tle = m.at("", float(g(S, "T_LEAP", (11.0, 11.35))[0]), "claws scrabble")
    m.put("efx", roomed(m, claws(1), tle), tle, cgain(m, tle, "claws", default=-19.0) - 3.0,
          pan=cpan(m, tle, "claws", default=0.45), label="claws scrabble on wood: the cat leaps", align=None)
    m.put("efx", roomed(m, paws(1), tle + 0.35), tle + 0.35, -26.0, pan=cpan(m, tle, "claws", default=0.45) + 0.1)
    tti = m.at("", float(g(S, "T_TIP", (11.1, 11.2))[0]), "tink", "tips over")
    m.put("efx", roomed(m, tin_tink(1), tti), tti, cgain(m, tti, "tink", default=-20.0) - 3.0,
          pan=cpan(m, tti, "tink", default=0.5), label="tink: the tin can tips over")
    cy = m.cue_of("yelps", "stumbles back")
    if cy:                                   # the cat between his feet: a yelp, a scuff, a gasp
        ty, pn = float(cy["t"]), float(cy["pan"])
        m.put("vox", space(cut(pitch(grunt(3), 4.0), 0.22, 0.06), "court", -14.0), ty, cy["gain_db"] + CUE_TRIM - 8.0,
              pan=pn, label="the guard yelps and stumbles back (a scuff, a gasp)", align=None, key=True)
        m.put("feet", footstep("guard", 17, "court", seed=3), ty + 0.05 - STEP_PRE, -21.0, pan=pn)
        m.put("feet", roomed(m, skid_stop(2, 0.18), ty + 0.08), ty + 0.08, -25.0, pan=pn, align=None)
        m.put("vox", space(breath("in"), "court", -14.0), ty + 0.2, -23.0, pan=pn, align=None, key=True)
    tca = m.at("T_CLATTER", 11.4, "clatter")
    m.put("efx", roomed(m, cut(can_clatter(1), 1.7, 0.5), tca), tca, -13.0, pan=cpan(m, tca, "clatter", default=0.55),
          label="CLATTER: the tin can hits the floor and rolls away")
    # he breathes out, half a laugh; turns away and walks off; the crew slip into the dark
    tsi = m.at("T_SIGH", 11.9, "breathes out", "sigh")
    m.put("vox", space(breath("out"), "court", -14.0, lp=3000.0), tsi, cgain(m, tsi, "breathes out", default=-18.0) - 3.0,
          pan=cpan(m, tsi, "breathes out", default=-0.3), label="the guard breathes out: a relieved sigh", align=None,
          key=True)
    m.put("vox", space(cut(chuckle(2), 0.3, 0.1), "court", -14.0), tsi + 0.45, -27.0, pan=cpan(m, tsi, "breathes out"),
          align=None)
    ttb = m.at("", float(g(S, "T_TURN_BACK", (12.3, 12.55))[0]), "coat rustles", "turns away")
    m.put("efx", roomed(m, cloth(0.35, 7, heavy=1.0), ttb), ttb, cgain(m, ttb, "coat rustles", default=-24.0) - 3.0,
          pan=cpan(m, ttb, "coat"), label="a coat rustles: the guard turns away", align=None)
    tpv = m.at("T_TURN_MID", ttb + 0.125, "heel scuffs", "pivots away", opt=True)
    if tpv is not None:
        m.put("feet", roomed(m, heel_scuff(1), tpv), tpv - STEP_PRE, cgain(m, tpv, "heel scuffs", default=-26.0) - 1.0,
              pan=cpan(m, tpv, "heel scuffs"), label="a heel scuffs on stone: the guard pivots away", sync=tpv)
    for k, (t, _, c) in enumerate(cues_with(m, "walks off down the corridor")):
        m.put("feet", footstep("guard", 12 + k, "court", seed=k % 5), t - STEP_PRE, c["gain_db"] + CUE_TRIM - 1.5 * k,
              pan=c["pan"], label="footstep: the guard walks off", sync=t)
    who = ("her", "knight", "cracker")
    for k, (t, _, c) in enumerate(cues_with(m, "soft step on stone")):
        m.put("feet", dsp.sos(footstep(who[k % 3], 20 + k, "court", seed=k % 5), "lowpass", 2500.0, 2), t - STEP_PRE,
              c["gain_db"] + CUE_TRIM, pan=c["pan"], label="a soft step: one of the crew slips into the dark", sync=t)
    p0, p1 = g(S, "T_PUSH", (12.8, 13.75))
    m.put("efx", rise_whoosh(round(p1 - p0, 2), 3), p0, cgain(m, p0, "rising whoosh", default=-19.0) - 5.0,
          label="a low rising whoosh: the camera pushes down the corridor", align=None)
    tdi = m.at("T_DIAL", 13.35, "chalk tap", "quick chalk circle")
    m.put("efx", roomed(m, chalk_tap(41, 0.7), tdi), tdi, cgain(m, tdi, "chalk tap", default=-17.0) - 3.0,
          label="a chalk tap and a quick chalk circle: the plan's mark on the dial")
    m.put("efx", roomed(m, chalk_scratch(0.3, 42, circle=True), tdi + 0.12), tdi + 0.12, -24.0, align=None)
    m.put("music", ting(3, 86) * 0.7, tdi, -22.0, hall=-16.0)
    # bar 32: the band creeps back in (a walk up the minor seventh into the dial)
    bassline(m, t32, "D2 F2 A2 C3", gain=-11.5, vel=0.68, label="the band creeps back")
    drums(m, t32, 1, level=-8.0, kick_=False, seed=10)
    melody(m, t32, ((1.5, 0.5, 62), (2, 0.5, 65), (2.5, 0.5, 69), (3, 1, 72)), gain=-17.0, vel=0.52, seed=11)


def _s05_bible(m, S):
    """s05 from the bible (its stand-in)."""
    L = m.len
    clock(m)
    # the corridor: the score drops to the tick
    m.mark(m.at("", 0.0, "drops to the tick", "score drops"), "the score drops to the tick")
    tfl = m.at("T_FLASH", 0.25, "flashlight", "torch")
    m.put("efx", roomed(m, flashlight_click(1), tfl), tfl, -21.0, pan=-0.4, label="the guard's flashlight clicks on")
    gw = span(m, "T_GUARD_WALK", (0.5, 4.0), "guard's slow steps", "guard walks", "his steps")
    steps(m, "guard", gw[0], gw[1], 1.0, gain=-16.0, pan=-0.45, room_="court", label="the guard's slow steps")
    m.put("vox", breath("held"), 2.75, -27.0, pan=0.2, align=None)
    # the stealth map: a tiptoe bass; a vibraphone note for each piece that crosses
    t28 = FB(m, 28)
    bassline(m, t28, "D2 . A1 . | D2 . A1 . | F2 . A1 .", gain=-12.0, vel=0.7, stacc=0.13, label="the tiptoe bass")
    drums(m, t28, 3, level=-10.0, taps=False, kick_=False, seed=9)
    for k, t in enumerate(m.ats("T_CROSSING", (6.0, 6.5, 7.0), "crosses", "cross", "gap", n=3)):
        m.put("efx", piece_clack(50 + k, 0.15), t, -24.0, pan=(-0.3, 0.0, 0.3)[k % 3], label="a piece crosses the gap")
        m.put("music", vibe((74, 77, 81)[k % 3], 0.8, 0.6, t_abs=m.t0 + t, seed=k), t, -15.0, pan=(-0.3, 0.0, 0.3)[k % 3])
    # the clank: a muted stab, then nothing
    tcl = m.at("T_CLANK", 9.5, "stethoscope", "clank", "pipe")
    m.put("efx", roomed(m, steth_clank(1), tcl), tcl, -11.0, pan=0.2, label="clank: the stethoscope on a pipe")
    m.put("efx", ripple(1, 90.0, 0.9), tcl + 0.02, -23.0)
    stab(m, tcl, "Bb7alt", gain=-16.0, dur=0.16, vel=0.7, seed=20, low=False)
    tsp = m.at("T_SPIN", 10.0, "spins", "swings at them", "turns")
    m.put("efx", roomed(m, cloth(0.3, 5, heavy=0.6), tsp), tsp, -20.0, pan=-0.3, label="the guard spins", align=None)
    m.put("feet", footstep("guard", 9, "court"), tsp + 0.12 - STEP_PRE, -17.0, pan=-0.3)
    m.put("vox", breath("gasp"), tsp + 0.06, -23.0, pan=0.2, key=True, align=None)
    tcat = m.at("T_CAT", 11.0, "cat", "leaps")
    m.put("vox", roomed(m, cat_yowl(1), tcat), tcat, -17.0, pan=0.45, label="a cat leaps from a crate", align=None)
    m.put("efx", roomed(m, paws(1), tcat + 0.45), tcat + 0.45, -22.0, pan=0.5)
    m.put("music", brass(69, 0.55, 0.55, seed=7, mute="harmon", scoop=True, vib=False, fall=4.0), tcat + 0.1, -19.0,
          pan=0.3)
    tcan = m.at("T_CAN", 11.25, "can", "clatter")
    m.put("efx", roomed(m, can_clatter(1), tcan), tcan, -12.0, pan=0.55, label="a can rolls: clatter")
    tbo = m.at("T_EXHALE", 12.0, "breathes out", "exhale")
    m.put("vox", space(breath("out"), "court", -14.0, lp=3000.0), tbo, -19.0, pan=-0.3,
          label="the guard breathes out", align=None, key=True)
    ws = span(m, "T_WALK_ON", (12.5, 14.0), "walks on", "slips through")
    steps(m, "guard", ws[0], ws[1], 1.0, gain=-21.0, pan=-0.6, room_="court", label="the guard walks on", k0=11)
    steps(m, "her", ws[0] + 0.5, ws[1], 0.5, gain=-26.0, pan=0.2, room_="court", k0=2)
    # the band comes back
    t32 = FB(m, 32)
    bassline(m, t32, "D2 F2 A2 C3", gain=-11.0, vel=0.72, label="the band comes back")
    drums(m, t32, 1, level=-6.0, kick_=False, seed=10)
    melody(m, t32, ((1.5, 0.5, 62), (2, 0.5, 65), (2.5, 0.5, 69), (3, 1, 72)), gain=-16.0, vel=0.55, seed=11)


# ============================================================================ s06 SAFE (66-80): bars 33-39
@section("s06")
def s06(m, S):
    """Bar 33, the door: low piano and an arco D under the clock; the Cracker's soft steps on the
    steel floor, the chest-piece on the steel, his fingers on the knob. Bars 34-37, the lock: a
    tiptoe pizzicato on 1 and 3; the cutaway (a paper cut, quick chalk); the dial spun right, left,
    right (heard through the stethoscope); each gate clicks on its beat (D, F, A; a ripple up the
    tube) and the vibraphone answers on the swung off-beat; the chalk line, step 4; CLUNK on the
    fence with the chord together (D minor, the low piano). Bar 38, the door: the wheel and the
    twelve bolts round the rim (a brush roll); his heave; the hinge groans and the brass swells on
    B-flat (onto gold), rising into s07's downbeat; bar 39, the door settles."""
    if isinstance(S, Stub):
        return _s06_bible(m, S)
    L = m.len
    clock(m)
    t33, t34, t37 = FB(m, 33), FB(m, 34), FB(m, 37)
    # bar 33: the door; low piano, the vibraphone's D minor 9, an arco D under it all
    m.put("music", piano(38, 3.6, 0.55, 1), t33, -14.0, pan=-0.1, label="the vault door: low piano")
    m.put("music", piano(26, 3.6, 0.5, 2), t33, -16.0, pan=-0.1)
    vibe_chord(m, t33, (53, 57, 60, 64), 3.0, gain=-20.0, vel=0.5, motor=0.0, seed=8)
    tfe = float(g(S, "T_FENCE", 9.5))
    m.put("music", arco(26, round(max(1.0, tfe - t33 - 0.4), 2), 0.5, seed=2, attack=1.2, release=0.8), t33 + 0.5, -19.0,
          align=None)
    # his steps in on the steel floor; the chest-piece to the steel; his fingers on the knob
    for k, (t, _, c) in enumerate(cues_with(m, "soft step", "steel-plated floor", "step on the steel")):
        tx = c["sfx"].lower()
        who = "her" if "architect" in tx or " her " in tx else "knight" if "knight" in tx else "cracker"
        m.put("feet", steel_step(who, 3 + k, "hall", k), t - STEP_PRE, c["gain_db"] + CUE_TRIM - 1.0, pan=c["pan"],
              label=f"a soft step on the steel floor ({'the Architect' if who == 'her' else 'the ' + who.title()})",
              sync=t)
    tpc = m.at("", float(g(S, "T_PIECE", (1.5, 2.1))[1]), "chest-piece touches", "metallic tock")
    m.put("efx", roomed(m, metal_tap(1), tpc), tpc, cgain(m, tpc, "chest-piece", "tock", default=-22.0) - 2.0,
          pan=cpan(m, tpc, "chest-piece", "tock"), label="the chest-piece touches the steel door: a tiny metallic tock")
    tkb = m.at("", float(g(S, "T_KNOB", (1.9, 2.5))[1]), "knurled knob", "faint tick")
    m.put("efx", roomed(m, knob_tick(1), tkb), tkb, cgain(m, tkb, "knob", "faint tick", default=-28.0) - 2.0,
          pan=cpan(m, tkb, "knob", "faint tick"), label="fingers settle on the dial's knob: a faint tick")
    # bars 34-37: the lock; a tiptoe pizzicato on 1 and 3 under the clock
    bassline(m, t34, "D2 . A1 . | D2 . A1 . | F2 . A1 . | D2 . . .", gain=-14.0, vel=0.62, stacc=0.13,
             label="the tiptoe bass (the lock)")
    tcu = m.at("", float(g(S, "T_CU", 3.0)), "paper cut", "chalk sketch", "cut away")
    m.put("efx", roomed(m, paper_torn(0.3, 3), tcu), tcu, cgain(m, tcu, "paper cut", "chalk sketch", default=-20.0) - 2.0,
          label="a paper cut and a chalk sketch: the lock drawn in", align=None)
    c0, c1 = g(S, "T_CHALK", (3.05, 3.65))
    for k in range(4):
        tk = c0 + (c1 - c0) * k / 4.0
        m.put("efx", roomed(m, chalk_scratch(0.12, 30 + k, press=0.8), tk), tk, -26.0, pan=-0.15 + 0.1 * k, align=None)
    turns = g(S, "TURNS", ((3.5, 4.5), (4.8, 6.5), (6.8, 8.5)))
    for k, tt in enumerate(turns):
        a, b = float(tt[0]), float(tt[1])
        c = m.cue_near(a, "dial spins", win=0.1)
        m.put("efx", dial_spin(round(max(0.3, b - a), 2), k, 34.0, 5.0), a,
              (c["gain_db"] + CUE_TRIM if c else -22.0) - 3.0, pan=c["pan"] if c else -0.26,
              label="the dial spins (ticks slowing to a creep, through the stethoscope)", align=None)
    gates = g(S, "GATES", (4.5, 6.5, 8.5))
    tube = float(g(S, "T_TUBE", 0.2))
    for k, t in enumerate(gates):
        t = float(t)
        c = m.cue_near(t, "gate", win=0.1)
        m.put("efx", gate_click(k % 3), t, (c["gain_db"] + CUE_TRIM if c else -11.0) - 2.0 - 1.0 * (k % 3),
              pan=c["pan"] if c else 0.15, label=f"a gate falls under the fence: a lock click ({('low', 'mid', 'high')[k % 3]})")
        m.put("efx", ripple(k, 90.0, 0.6), t + tube, -27.0, pan=0.3)
        m.put("music", vibe((62, 65, 69)[k % 3], 1.6, 0.6, t_abs=m.t0 + t + sw(0.5), motor=0.0, seed=k), t + sw(0.5),
              -15.0, pan=-0.2 + 0.2 * k)
    tln = m.at("", float(g(S, "T_LINE", (8.85, 9.3))[0]), "three dots joined", "chalk stroke")
    m.put("efx", roomed(m, chalk_scratch(0.3, 36, press=0.9), tln), tln, cgain(m, tln, "chalk stroke", default=-20.0) - 3.0,
          label="a quick chalk stroke: the three dots joined", align=None)
    tfo = m.at("", float(g(S, "T_FOUR", 9.0)), "chalk circle", "step 4")
    m.put("efx", roomed(m, chalk_scratch(0.3, 37, circle=True), tfo), tfo, cgain(m, tfo, "chalk circle", default=-22.0) - 3.0,
          pan=cpan(m, tfo, "chalk circle", default=0.7), label="a chalk circle: step 4", align=None)
    # CLUNK: the fence drops; the chord together; his spectacles glint; the bolt draws back
    m.put("efx", roomed(m, fence_clunk(1), tfe), tfe, -11.5, label="CLUNK: the fence drops into the lined-up gates")
    vibe_chord(m, tfe, (62, 65, 69, 74), 1.4, gain=-16.0, vel=0.65, roll=0.0, motor=0.0, seed=10)
    m.put("music", piano(26, 1.2, 0.6, 3), tfe, -15.0)
    m.put("music", piano(38, 1.2, 0.55, 4), tfe, -17.0)
    tgl = m.at("", float(g(S, "T_GLINT", (9.5, 9.9))[0]) + 0.05, "glint on his spectacles", "bright ting")
    m.put("music", ting(2, 93) * 0.7, tgl, -24.0, pan=cpan(m, tgl, "glint", default=0.7),
          label="a glint on his spectacles: a tiny bright ting", hall=-16.0)
    b0, b1 = g(S, "T_BOLT", (9.6, 9.95))
    m.put("efx", roomed(m, bolt_slide(round(max(0.15, b1 - b0), 2), 1), b0), b0, cgain(m, b0, "bolt draws back", default=-15.0) - 2.0,
          pan=cpan(m, b0, "bolt draws back", default=0.6), label="the lock's bolt draws back: a short heavy slide", align=None)
    # bar 38, the door: the chest-piece let go; the wheel; the twelve bolts round the rim; his heave
    tlg = m.at("", float(g(S, "T_LET_GO", (10.0, 10.3))[0]) + 0.15, "chest-piece drops", "taps his coat")
    m.put("efx", roomed(m, coat_tap(2), tlg), tlg, cgain(m, tlg, "chest-piece drops", "coat", default=-28.0) - 2.0,
          pan=cpan(m, tlg, "chest-piece drops", "coat"), label="the chest-piece drops on its tube and taps his coat")
    w0, w1 = g(S, "T_WHEEL", (10.2, 10.9))
    m.put("efx", roomed(m, pitch(dial_ratchet(round(w1 - w0, 2), 9, 9.0), -12.0), w0), w0,
          cgain(m, w0, "great wheel", default=-13.0) - 3.0, pan=cpan(m, w0, "great wheel"),
          label="the great wheel turns: a slow heavy iron ratchet", align=None)
    m.put("music", brush_roll(round(w1 - w0, 2), 3), w0, -25.0, pan=0.15, align=None)
    for k, (t, _, c) in enumerate(cues_with(m, "bolt withdraws", "rolling run round the rim")):
        m.put("efx", roomed(m, bolt_one(k % 12), t), t - BOLT_PRE, c["gain_db"] + CUE_TRIM - 3.0, pan=c["pan"],
              label="a heavy steel bolt withdraws from the frame (the rolling run)", sync=t, align="peak")
    th = m.at("", float(g(S, "T_HEAVE", (10.9, 11.15))[0]), "heaves", "strained breath")
    m.put("vox", roomed(m, dsp.sos(pitch(breath("in"), -4.0), "lowpass", 3000.0, 2), th), th,
          cgain(m, th, "heaves", "strained", default=-22.0) - 4.0, pan=cpan(m, th, "heaves"),
          label="the old man heaves on the wheel: a strained breath", align=None, key=True)
    m.put("vox", roomed(m, cut(pitch(grunt(4), -2.0), 0.25, 0.08), th + 0.05), th + 0.05, -31.0, pan=cpan(m, th, "heaves"),
          align=None, key=True)
    # the door swings: the hinge's groan, and the brass swells on B-flat (gold) into s07's downbeat
    d0, d1 = g(S, "T_SWING", (11.0, 13.0))
    m.put("efx", roomed(m, vault_groan(round(d1 - d0, 2), 1), d0, wet=-10.0), d0,
          cgain(m, d0, "hinge groans", "groans", default=-11.0) - 2.0, pan=cpan(m, d0, "hinge", "groans"),
          label="the vault door's great hinge groans as it swings open", align=None)
    tsw = m.at("", d0 + 0.1, "brass swell", "gold light floods")
    brass_swell(m, tsw, "Bbmaj7", max(1.0, L - tsw - 0.05), gain=-13.0, seed=40, label="a brass swell: gold light floods out")
    m.put("music", bass(34, max(1.0, L - d0 - 0.1), 0.85, 2), d0, -11.0, pan=-0.1, hall=-24.0)
    m.put("music", cym_swell(max(1.0, L - d0), 5), d0, -24.0, align=None)
    trs = m.at("", float(g(S, "T_REST", 13.0)), "settles against its stop", "deep soft thud")
    m.put("efx", roomed(m, door_thud(1), trs), trs, cgain(m, trs, "settles", "thud", default=-16.0) - 2.0,
          pan=cpan(m, trs, "settles", "thud"), label="the open door settles against its stop: a deep soft thud")


def _s06_bible(m, S):
    """s06 from the bible (its stand-in)."""
    L = m.len
    clock(m)
    t33 = FB(m, 33)
    m.put("music", piano(38, 3.6, 0.55, 1), t33, -14.0, pan=-0.1, label="the vault door: low piano")
    m.put("music", piano(26, 3.6, 0.5, 2), t33, -16.0, pan=-0.1)
    vibe_chord(m, t33, (53, 57, 60, 64), 3.0, gain=-19.0, vel=0.5, motor=0.0, seed=8)
    m.put("music", arco(26, 9.0, 0.5, seed=2, attack=1.2, release=0.8), t33 + 0.5, -19.0, align=None)
    tkn = m.at("T_KNEEL", 0.5, "kneels", "kneel", opt=True)
    if tkn is not None:
        m.put("efx", roomed(m, cloth(0.4, 6, heavy=0.4), tkn), tkn, -22.0, label="the Cracker kneels", align=None)
    ts = m.at("T_STETH", 2.0, "stethoscope", "set to the door", opt=True)
    if ts is not None:
        m.put("efx", roomed(m, metal_tap(1), ts), ts, -18.0, label="the stethoscope set to the door")
    # the dial: right, left, right; the gates click D, F, A, and the vibraphone answers each
    turns = []
    for k, (d0, w) in enumerate(((3.0, ("turns right", "right")), (5.0, ("turns left", "left")), (7.0, ("turns right", "right")))):
        turns.append(span(m, "", (d0, d0 + 1.8), *w, "dial turns", "dial", win=0.9, opt=True))
    for k, (a, b) in enumerate(tt for tt in turns if tt is not None):
        m.put("efx", roomed(m, dial_ratchet(round(min(b - a, 3.0), 2), k, 14.0 + 3 * k), a), a, -17.0, pan=0.1,
              label="the dial turns", align=None)
    gates = m.ats("T_GATES", (5.0, 7.0, 9.0), "gate", n=3, opt=True)
    for k, t in enumerate(gates):
        m.put("efx", roomed(m, gate_click(k), t), t, -12.0 - 1.0 * (k % 3), pan=0.05,
              label=f"gate click {('low', 'mid', 'high')[k % 3]}")
        m.put("efx", roomed(m, chalk_tap(60 + k, 0.4), t + 0.08), t + 0.08, -26.0)
        m.put("music", vibe((62, 65, 69)[k % 3], 1.6, 0.6, t_abs=m.t0 + t, motor=0.0, seed=k), t + 0.12, -15.0, pan=-0.2 + 0.2 * k)
    tf = m.at("T_FENCE", 9.5, "fence", "clunk", opt=True)
    if tf is not None:
        m.put("efx", roomed(m, fence_clunk(1), tf), tf, -11.5, label="clunk: the fence drops")
        m.put("efx", roomed(m, chalk_scratch(0.3, 66, press=0.7), tf), tf + 0.05, -24.0)
        vibe_chord(m, tf, (62, 65, 69, 74), 1.4, gain=-16.0, vel=0.65, roll=0.0, motor=0.0, seed=10)
        m.put("music", piano(26, 1.2, 0.6, 3), tf, -15.0)
        m.put("music", piano(38, 1.2, 0.55, 4), tf, -17.0)
    # the bolts: a brush roll; the door swings: a groan, and the brass swells onto gold
    bb = span(m, "T_BOLTS", (10.0, 11.0), "bolts", "bolt", opt=True)
    if bb is not None:
        b0, b1 = bb
        m.put("efx", roomed(m, bolt_run(10, round(min(b1 - b0, 1.6), 2), 1), b0), b0, -10.0,
              label="the bolts withdraw round the rim", align=None)
        m.put("music", brush_roll(round(b1 - b0, 2), 3), b0, -25.0, pan=0.15, align=None)
    ds = span(m, "T_SWING", (11.0, 14.0), "door swings", "swings", "groan", opt=True)
    d0, d1 = ds if ds is not None else (11.0, 14.0)
    if ds is not None:
        m.put("efx", roomed(m, vault_groan(round(d1 - d0, 2), 1), d0, wet=-10.0), d0, -11.0,
              label="the door swings: a groan", align=None)
    brass_swell(m, d0, "Bbmaj7", max(1.0, L - d0 - 0.05), gain=-13.0, seed=40, label="a brass swell: gold")
    m.put("music", bass(34, max(1.0, L - d0 - 0.1), 0.85, 2), d0, -11.0, pan=-0.1, hall=-24.0)
    m.put("music", cym_swell(max(1.0, L - d0), 5), d0, -24.0, align=None)
    m.cover_span(d0, L, "brass", "swell", "gold light")


# ============================================================================ s07 CROSS (80-96): bars 40-47
@section("s07")
def s07(m, S):
    L = m.len
    clock(m)
    for t, d, c in (cues_with(m, "room tone") if m._module() else ()):      # a bed the module names
        m.put("amb", bed("room_tone", round(max(1.0, d or 4.0), 2), 6, fin=0.05, fout=0.3), t,
              c["gain_db"] + CUE_TRIM - 9.0, label="the vault's room tone", align=None)
    t40 = FB(m, 40)
    # gold: a hot groove (the ride, trumpet stabs on the off-beats)
    m.put("music", crash(3, 2.6), t40, -24.0, pan=0.3, hall=-20.0, label="gold: the groove")
    bassline(m, t40, "D2 E2 F2 A2 | Bb2 D2 F2 Ab2", gain=-9.5, vel=0.85)
    drums(m, t40, 2, level=0.0, ride_=True, sweep=False, seed=11)
    comp(m, t40, (("Dm6", 4), ("Bb7", 4)), gain=-20.0, vel=0.5, pattern="push", seed=6)
    for k, (b, sym) in enumerate(((1.5, "Dm6"), (3.5, "Dm6"), (5.5, "Bb7"), (7.5, "Bb7"))):
        stab(m, t40 + sw(b), sym, gain=-17.0, dur=0.14, vel=0.75, seed=30 + k, low=False)
    if m._module() and getattr(S, "T_GOLD", None) is None:       # the module's own clinks and bags
        gold = tuple(t for t, _, c in cues_with(m, "clink", "gold bar", "bars", "into a bag", "into the bag", "stacks")
                     if not any(w in c["sfx"].lower() for w in ("look", "light", "tone", "hum", "glint", "sight")))
    else:
        gold = m.ats("T_GOLD", (0.5, 1.0, 1.75, 3.0, 3.5), "gold", "clink", "bag", "bars", opt=True)
    for k, t in enumerate(gold):
        c = m.cue_near(t)
        bagged = bool(c and "bag" in c["sfx"].lower())
        x = gold_bag(k) if bagged else gold_clink(k, 0.0)
        m.put("efx", roomed(m, x, t, k), t, -15.0 - 2.0 * (k % 2), pan=(-0.35, 0.3)[k % 2], label="gold: bars and bags")
    tbox = m.at("T_BOX", 2.0, "deposit", "box", opt=True)
    if tbox is not None:
        m.put("efx", roomed(m, deposit_box(1), tbox), tbox, -17.0, pan=0.45, label="her deposit box opens")
    tgl = m.at("T_GLINT", 2.5, "glint", opt=True)
    if tgl is not None:
        m.put("music", vibe(81, 0.9, 0.35, t_abs=m.t0 + tgl, depth=0.6, hard=0.2, seed=2), tgl, -21.0, pan=0.45,
              label="a tiny red glint", hall=-14.0)
    # bars 42-45: THE THEME INVERTED, low and minor, from his look; it peaks from the X-split
    t42 = FB(m, 42)
    tlook = m.at("T_LOOK", 4.0, "his red look", "sight line", "look", opt=True)
    melody(m, t42, INVERSION, inst="tbn", gain=-12.5, vel=0.72, seed=12, legato=0.96,
           label="THE THEME INVERTED (trombone, low): his look")
    if tlook is not None and abs(tlook - t42) > FRAME:
        m.put("music", brass(51, 0.6, 0.5, seed=13, mute="cup", scoop=False), tlook, -19.0, pan=0.2, label="his look")
    melody(m, t42, INVERSION, inst="piano", gain=-17.0, vel=0.5, seed=13, octave=-1)
    melody(m, t42, INVERSION, inst="piano", gain=-19.5, vel=0.42, seed=14)
    tx = m.at("T_SPLIT", 6.0, "x-split", "split", "diagonals", opt=True)
    melody(m, t42, INVERSION, gain=-14.5, vel=0.7, octave=1, motor=0.0, hard=0.4, start=4, seed=15)
    bassline(m, t42, "inv", gain=-9.5, vel=0.82, swell=(0.7, 1.0))
    comp(m, t42 + BAR, PROG_INV[1:], gain=-21.0, vel=0.48, pattern="whole", seed=7)
    drums(m, t42 + BAR, 3, level=-1.0, seed=12, slap=0.4)
    m.cover_span(t42, t42 + 16 * BEAT, "theme", "invert", "inversion")
    for k in range(2 if tx is not None else 0):
        w = fx("whip", seed=40 + k)
        m.put("efx", w, tx + 0.12 * k - peak_at(w), -14.0 + 2 * k, pan=(-0.4, 0.4)[k], sync=tx + 0.12 * k, align="peak",
              label="the X-split: the frame cut on both diagonals" if k == 0 else None)
    tred = m.at("T_RED", 8.0, "seams turn red", "he moves", opt=True)
    if tred is not None:
        m.put("music", brass(63, 0.9, 0.55, seed=16, mute="harmon", scoop=False, vib=False, fall=1.0), tred, -18.0,
              pan=0.3, label="he moves: the seams turn red (the semitone)")
    # the Knight's strained grunts, his own voice: the bags heaved up (the gold shifts inside them);
    # his weight thrown against the vault door, held as it swings
    for k, (dflt, words, cut_, lab) in enumerate((
            (6.4, ("heaves up the two heavy bags",), (5.06, 5.76, 0.168),
             "he heaves up the two heavy bags: a strained grunt (his voice); the gold shifts inside them"),
            (10.12, ("throws his weight",), (0.10, 1.64, 0.257),
             "he throws his weight against the vault door: a strained grunt (his voice)"))):
        tg_ = m.at("", dflt, *words, win=0.3)
        a, b, on = cut_
        x = dsp.sos(take_cut("grunt_knight", a, b, 0.03, 0.25 if k else 0.12, rms=db2lin(-11.2)), "lowpass", 9000.0, 2)
        m.put("vox", roomed(m, x, tg_, k), tg_ - on, cgain(m, tg_, "grunt", default=-17.0) + (1.0 if k else -1.0),
              pan=cpan(m, tg_, "grunt"), label=lab, sync=tg_, align=None, key=True)
        if not k:
            for j in range(2):
                m.put("efx", roomed(m, dsp.sos(gold_clink(60 + j, 1.0), "lowpass", 1600.0, 2), tg_ + 0.06 + 0.07 * j),
                      tg_ + 0.06 + 0.07 * j, -25.0 - 2.0 * j, pan=(-0.15, 0.15)[j], align=None)
    # the door shut: the groan; BOOM on the bar line; the dial spins red; the bolts shoot home
    ss = span(m, "T_SHUT", (10.0, 12.0), "door shut", "swings the door", "groan", "shut", opt=True)
    if ss is not None:
        s0, s1 = ss
        m.put("efx", roomed(m, vault_groan(round(s1 - s0, 2), 2), s0, wet=-10.0), s0, -10.0,
              label="he swings the door shut", align=None)
    tb = m.at("T_BOOM", 12.0, "boom", "slams")
    m.put("efx", vault_boom(1), tb, -8.0, label="BOOM: the vault door slams")
    hit(m, tb, 38, 1.0, gain=-12.0)
    tds = m.at("T_DIAL_RED", 12.25, "dial spins", "spins", opt=True)
    if tds is not None:
        m.put("efx", roomed(m, dial_ratchet(0.45, 7, 40.0), tds), tds, -15.0, label="the dial spins in red", align=None)
    homes = [(t, c) for t, _, c in cues_with(m, "shoots home", "shoot home", "shot home", "bolt home", "bolts home")]
    if m._module() and len(homes) >= 3:                 # the module gives each bolt: a clack each
        for k, (t, c) in enumerate(homes):
            m.put("efx", roomed(m, bolt_one(k % 12), t), t - BOLT_PRE, c["gain_db"] + CUE_TRIM - 3.0, pan=c["pan"],
                  label="a bolt shoots home (the rolling run)", sync=t, align="peak")
        tbh = homes[0][0]
    else:
        tbh = m.at("T_BOLTS_HOME", 12.6, "shoot home", "bolts", opt=True)
        if tbh is not None:
            m.put("efx", roomed(m, bolt_run(10, 0.4, 3, home=True), tbh), tbh, -10.0, label="the bolts shoot home")
        else:
            tbh = tb + 0.6
    # bars 46-47: the inversion's head again, exposed, over the alarm; the clock stops dead (93.5)
    t46 = FB(m, 46) + 2 * BEAT          # after the BOOM's black: it creeps in on the half bar (93.0)
    melody(m, t46, INVERSION, inst="tbn", gain=-13.5, vel=0.66, stop=6, seed=17, label="the inversion's head, exposed")
    melody(m, t46, INVERSION, gain=-16.5, vel=0.55, stop=6, octave=1, motor=0.0, hard=0.35, seed=18)
    m.put("music", arco(26, max(0.5, L - tbh - 0.3), 0.6, seed=3, attack=0.5, release=0.3), tbh, -16.0, align=None)
    m.cover_span(t46, L, "theme", "invert", "inversion")
    if 0.0 <= HEIST_STOP - m.t0 < L:
        m.mark(HEIST_STOP - m.t0, "the clock stops dead")
    m.cover("stopwatch")
    rl = span(m, "T_ROUTE_L", (13.0, 14.0), "red route", "in an l", "leaves the chalk route", opt=True)
    r0, r1 = rl if rl is not None else (0.0, 0.0)
    for k in range(2 if rl is not None else 0):
        a = r0 + k * (r1 - r0) / 2
        m.put("efx", roomed(m, chalk_scratch(round((r1 - r0) / 2 - 0.05, 2), 70 + k, press=1.0), a), a, -19.0,
              pan=0.2 * k, label="his red route: an L" if k == 0 else None)
    for k, t in enumerate(m.ats("T_HOPS", (13.5, 14.0, 14.5), "knight hops", "hops", n=3, opt=True)):
        m.put("efx", piece_clack(80 + k, 0.8), t, -14.0, pan=0.3 + 0.1 * k, label="the red knight hops")
    a0 = m.at("T_ALARM", 14.5, "alarm")
    al = roomed(m, alarm_bell(max(0.3, L - a0), 1), a0, wet=-16.0)[:n_of(L - a0)]
    m.put("efx", dsp.fade(al, 0.0, 0.03), a0, -17.0, pan=0.35, label="alarm bell")


# ============================================================================ s08 LOCKED (96-108): bars 48-53
@section("s08")
def s08(m, S):
    """Sparse. Black: his ragged breathing, close, the alarm muffled away beyond the steel; a match
    scratches (sparks), then strikes; he pounds the door: huge muffled booms. A single low piano
    note; her calm: the theme's first two notes, upright, on the vibraphone. Her heel: a tap, then
    the hollow knock booming down into the void (a low bowed D comes in under it), the dot's ting.
    The roll of tracing paper; the score gathers: a rising chord (D minor, major seventh) held
    into the rewind."""
    L = m.len
    mod = not isinstance(S, Stub)
    tst = m.at("T_STRIKE", 1.4, "strikes", "flare")
    tsp = m.at("T_SPARK", tst - 0.55, "sparks, no flame", "scratched")
    # black: the alarm, outside, muffled away through the steel; his ragged breath, close
    ad = 1.6
    al = dsp.sos(alarm_bell(ad + 0.2, 2), "lowpass", 600.0, 2)[:n_of(ad)] * np.linspace(1.0, 0.0, n_of(ad)) ** 1.6
    m.put("amb", al, 0.0, -27.0, pan=0.3, align=None)
    x = dsp.fade(ragged(round(max(1.2, tst + 0.7), 2)), 0.02, 0.4)
    m.put("vox", space(x, "cell", -12.0), 0.0, -15.0, label="black: the Cracker's ragged breathing, close", align=None,
          key=True)
    # the match: a scratch, sparks, no flame; then it strikes and flares; the flame's hiss
    sc = match_scratch(1)
    m.put("efx", roomed(m, sc, tsp), tsp - onset_at(sc), -12.0, pan=0.3, label="a match scratched: sparks, no flame",
          sync=tsp)
    st = fx("match_strike", seed=307)
    m.put("efx", roomed(m, st, tst), tst - onset_at(st), -9.5, pan=0.3, label="the match strikes and flares", sync=tst)
    m.put("efx", roomed(m, fx("match_flare", seed=1), tst + 0.08), tst + 0.08, -14.0, pan=0.3, align=None)
    m.put("efx", 0.5 * sfx._thump(n_of(0.25), 110.0, 70.0, 0.02, 0.12), tst + 0.06, -20.0, pan=0.3)   # the soft whump
    fc = m.cue_of("steady hiss", "flame's")
    tfl = float(fc["t"]) if fc else tst + 0.2
    m.put("amb", flame_bed(round(L - tfl + 0.2, 2), 1), tfl, -33.0, pan=0.3, label="the flame's small steady hiss",
          align=None)
    # he rears back and pounds the door: three huge muffled booms
    if mod:
        tw = m.at("T_WIND", 2.4, "breath catches", "rears back")
        m.put("vox", space(breath("gasp"), "cell", -12.0), tw, -20.0, pan=0.35, label="his breath catches", align=None,
              key=True)
        m.put("efx", roomed(m, cloth(0.45, 9, heavy=0.8), tw), tw + 0.05, -22.0, pan=0.4, align=None)
    thuds = m.ats("THUDS", (2.85, 3.3, 3.75), "fist on the vault door", "steel boom", "muffled", "pound")
    for k, t in enumerate(thuds):
        c = m.cue_near(t, "fist", "boom", "muffled", "pound", "thud")
        gk = (float(c["gain_db"]) + CUE_TRIM - 2.0) if c else -8.0 - 1.5 * k
        m.put("efx", pound(k % 4), t, gk, pan=0.1, label="a fist on the vault door: a huge muffled steel BOOM")
    tturn = span(m, "T_TURN", (8.3, 8.8), "turns round", "shuffle")[0]
    if mod and thuds and tturn - (thuds[-1] + 0.45) > 0.8:          # he pants after it, until he turns
        hb0 = thuds[-1] + 0.45
        x = dsp.fade(ragged(round(tturn - hb0 + 0.12, 2), 1), 0.3, 0.12)
        m.put("vox", space(x, "cell", -12.0), hb0, -25.0, pan=0.35, align=None, key=True)
    # her eye: a single low piano note; her look drops; her calm: D and A, upright
    tpn = m.at("", 3.9, "low piano note", "piano note")
    m.put("music", piano(38, 4.0, 0.55, 5), tpn, -14.0, pan=-0.1, label="a single low piano note under the flame's hiss")
    if mod:
        tgl = m.at("", g(S, "T_GLANCE", 4.3) + 0.1, "her look drops", "look drops")
        m.put("efx", roomed(m, chalk_tap(71, 0.3), tgl), tgl, -22.5, label="a soft chalk tick: her look drops to the floor")
    tla = m.at("T_LAUGH", 4.59, "breathes a laugh", "laugh", opt=True)
    if tla is not None:                    # her breath of a laugh (her own voice), as the corner of her mouth lifts
        x = take_cut("laugh_her", 2.32, 2.70, 0.01, 0.06, rms=db2lin(-11.2))
        m.put("vox", space(x, "cell", -14.0), tla - 0.2, -23.0, pan=cpan(m, tla, "laugh", default=-0.2),
              label="she breathes a laugh through her nose (her voice)", sync=tla, align=None)
    tsm = m.at("T_SMILE", 4.65, "mouth lifts", "calm note", "smile")
    for j, (b, d, p) in enumerate(THEME[:2]):
        tt = tsm + b * BEAT
        m.put("music", vibe(p, d * BEAT + (1.8 if j else 0.1), 0.55, t_abs=m.t0 + tt, depth=0.5, hard=0.3, seed=40 + j),
              tt, -15.5, pan=-0.2, label="her calm: the theme's first two notes, upright (vibraphone)" if j == 0 else None)
    # the whip down to the floor; the ring; her heel: a tap, then the hollow knock; the floor opens
    if mod:
        wh0, wh1 = span(m, "WHIP", (5.1, 5.35), "fast whoosh down", "whoosh down")
        m.put("efx", whip_down(round(max(0.15, wh1 - wh0), 3), 1), wh0, -19.0, label="a fast whoosh down", align=None)
        trg = m.at("", wh1, "ring drawn on the floor", "ring drawn")
        m.put("efx", roomed(m, chalk_scratch(0.3, 83, circle=True, press=0.6), trg), trg, -22.0, pan=-0.1,
              label="chalk: the ring drawn on the floor", align=None)
    taps = g(S, "TAPS", ())
    if len(taps) >= 2 and all(_num(x) for x in taps[:2]):
        th_, tk = float(taps[0]), float(taps[1])
    else:
        tk = m.at("T_KNOCK", 6.25, "hollow knock", "hollow")
        th_ = tk - 0.5
    m.put("efx", roomed(m, heel_tap(1), th_), th_, -11.0, pan=-0.1, label="her heel taps the floor: a hard click on steel")
    m.put("efx", hollow_knock(1), tk, -7.0, pan=-0.1, label="the second tap: a hollow knock, booming down into a void")
    m.put("efx", ripple(2, 62.0, 1.6), tk + 0.03, -16.0)
    m.put("music", arco(38, L - tk + 0.2, 0.55, seed=6, attack=0.8, release=0.4), tk, -19.0, pan=-0.05, align=None)
    if mod:
        o0, o1 = span(m, "T_OPEN", (6.25, 6.85), "drawn down fast", "floor opens")
        m.put("efx", paper_whoosh(round(max(0.3, o1 - o0), 2), 6), o0, -19.0, pan=-0.05,
              label="paper drawn down fast: the floor opens into the section", align=None)
    tdot = m.at("T_DOT", 6.95, "dot glows", "glows")
    m.put("music", ting(4, 86), tdot, -15.0, pan=-0.1, label="a ting: the chalk dot glows under her heel", hall=-14.0)
    if mod:
        tln = m.at("T_LENS", 7.25, "lens opens on the plan", "lens opens")
        m.put("efx", roomed(m, chalk_tap(73, 0.3), tln), tln, -21.0, pan=0.3, label="a soft chalk tick: the lens opens on the dot")
        # the tracing paper: her coat, his turn, the roll drawn out
        r0, _ = span(m, "T_ROLL", (8.2, 8.85), "reaches into her coat", "her coat")
        m.put("efx", roomed(m, cloth(0.5, 11, heavy=0.4), r0), r0, -21.0, pan=-0.3, label="cloth: she reaches into her coat",
              align=None)
        m.put("efx", roomed(m, shuffle(2), tturn), tturn, -21.0, pan=0.3, label="the Cracker turns round (a shuffle)",
              align=None)
        ra0, ra1 = span(m, "T_RAISE", (8.85, 9.4), "roll of paper", "drawn out")
        x = cut(mono(fx("paper_rustle", seed=4)), round(min(0.9, max(0.3, ra1 - ra0 + 0.15)), 2), 0.12)
        m.put("efx", roomed(m, x, ra0), ra0, -21.0, pan=-0.2, label="a roll of paper drawn out", align=None)
    f0, f1 = span(m, "T_FALL", (9.45, 9.95), "unrolling as it drops", "crisp rustle", "tracing")
    m.put("efx", tracing_slide(round(f1 - f0 + 0.2, 2), 1), f0, -15.0, pan=-0.1, label="tracing paper unrolling as it drops",
          align=None)
    li = span(m, "T_LIFT", None, "lifted toward us", "slow paper swish") if mod else None
    if li:
        m.put("efx", paper_whoosh(round(li[1] - li[0], 2), 8), li[0], -20.0, label="the sheet lifted toward us: a slow swish",
              align=None)
    # the score gathers: a rising chord over the low D (A, F, C sharp, E, A), held into the rewind
    tg0 = m.at("", f0, "score gathers", "rising chord")
    for j, p in enumerate((45, 53, 61, 64, 69)):
        tj = tg0 + 0.3 * j
        m.put("music", arco(p, L - tj + 0.3, 0.5 + 0.06 * j, seed=50 + j, attack=0.6, release=0.3, bright=3200.0,
                            env=[(0.0, 0.4), (L - tj, 1.0)]),
              tj, -21.0 + 0.5 * j, pan=-0.3 + 0.15 * j, align=None,
              label="the score gathers: a rising chord held into the rewind" if j == 0 else None)
    vibe_chord(m, tg0, (62, 65, 69, 73, 76), L - tg0 + 0.3, gain=-22.0, vel=0.45, roll=0.12, depth=0.6, seed=55)
    m.put("music", cym_swell(round(L - tg0, 2), 5), tg0, -24.0, align=None)


# ============================================================================ s09 PLAN B (108-124): bars 54-61
REWIND_BIBLE = ((0.0, 0.4, "s07", 13.0, 11.8), (0.4, 0.8, "s06", 12.0, 10.8), (0.8, 1.2, "s05", 11.0, 9.8),
                (1.2, 1.6, "s04", 5.0, 3.8), (1.6, 2.0, "s03", 15.6, 14.4), (2.0, 3.0, "s03", 13.6, 14.6))


def rewind_schedule(S):
    """s09's REWIND rows (t0, t1, src scene, src t0, src t1), scene times; the bible's when it has
    none. A row that does not read, or does not point back into the film, is skipped."""
    raw = g(S, "REWIND", REWIND_BIBLE)
    out = []
    for row in raw:
        try:
            a, b, sid, s0, s1 = row
            a, b, s0, s1, sid = float(a), float(b), float(s0), float(s1), str(sid)
            if sid not in START or b <= a or abs(s1 - s0) < 0.02:
                raise ValueError("empty or unknown scene")
            if min(s0, s1) < 0.0 or max(s0, s1) > LENGTH[sid] + 1e-6 or START[sid] + max(s0, s1) > START["s09"] + a + 1e-6:
                raise ValueError("does not point back into the film")
            out.append((a, b, sid, s0, s1))
        except Exception as e:
            warn(f"s09: REWIND row {row!r} cannot be used ({e}): skipped")
    if not out:
        out = list(REWIND_BIBLE)
    return out


def _s09_bible(m, S):
    """s09 from the bible (its stand-in)."""
    L = m.len
    # the rewind: the mix itself, cut where the picture rewinds to (post-pass), under a tape scrub
    sched = rewind_schedule(S)
    for a, b, sid, s0, s1 in sched:
        m.rewind.append((m.t0 + a, m.t0 + b, START[sid] + s0, START[sid] + s1, sid))
    r0, r1 = min(r[0] for r in sched), max(r[1] for r in sched)
    m.put("efx", rewind_scrub(round(r1 - r0, 2), 1), r0, -17.0, label="the rewind: tape whoosh", align=None)
    m.cover_span(r0, r1, "rewind", "stopwatch", "spins back", "scrub")
    tt = m.at("T_TING", min(r1 - 0.5, 2.5), "ting", "lens snaps", "callout lens", win=1.0)
    m.put("music", ting(2, 93), tt, -17.0, pan=0.1, label="a ting: the callout snaps round the dot", hall=-16.0)
    # s02 again: his look (the semitone), her look (the low held D); a callout on her eye
    tl = m.at("T_LOOKS", 3.0, "elevation", "his red look", "her white look")
    m.put("music", brass(63, 0.6, 0.5, seed=8, mute="harmon", scoop=False, vib=False, fall=0.5), tl, -19.0, pan=0.2,
          label="his look again (the semitone)")
    m.put("music", arco(38, 2.2, 0.7, seed=4, attack=0.3, release=0.5), tl + 0.5, -14.0, align=None)
    m.put("music", piano(26, 2.0, 0.4, 3), tl + 0.5, -19.0, pan=-0.1)
    teye = m.at("T_EYE", 4.0, "her eye", "callout on her")
    m.put("music", ting(3, 98), teye, -19.0, pan=-0.15, label="a ting: the callout on her eye", hall=-16.0)
    # the overlay: Plan B drawn in solid chalk over a rising vamp in D MAJOR
    s0, s1 = span(m, "T_SLIDE", (5.0, 6.5), "tracing", "slides", "overlay")
    m.put("efx", tracing_slide(round(s1 - s0, 2), 2), s0, -15.0, label="the tracing sheet slides over the plan", align=None)
    t57 = FB(m, 57)
    bassline(m, t57, "D2 F#2 A2 B2", gain=-11.0, vel=0.7, swell=(0.6, 0.9))
    vibe_chord(m, t57, (54, 59, 64, 69), 1.9, gain=-18.0, vel=0.55, depth=0.5, seed=13, label="D major: the vamp")
    m.put("music", brush_sweep(7, 4), t57, -33.0, hall=-24.0, align=None)
    m.put("music", cym_swell(1.95, 8), t57, -27.0, align=None)
    # bars 58-61: THE THEME upright, in D major (the inversion inverted)
    t58 = FB(m, 58)
    melody(m, t58, THEME_MAJOR, gain=-12.0, vel=0.78, seed=19, label="THE THEME upright, in D major")
    melody(m, t58, THEME_MAJOR, inst="tpt", gain=-17.0, vel=0.6, seed=19, mute="open", legato=0.92)
    bassline(m, t58, "major", gain=-10.0, vel=0.8)
    comp(m, t58, PROG_MAJOR, gain=-21.0, vel=0.45, pattern="charleston", seed=8)
    drums(m, t58, 2, level=-3.0, seed=13)
    drums(m, t58 + 2 * BAR, 2, level=-2.0, ride_=True, sweep=False, seed=14)
    m.cover_span(t57, L, "theme", "major", "upright")
    # the vault by match light: a tile lifted; they drop through and walk north in the water
    tfl = m.at("T_MATCHLIGHT", 10.0, "flame", "match light", win=1.0)
    m.put("amb", flame_bed(3.4, 2), tfl, -38.0, pan=-0.2, align=None, label="the vault by the flame's light")
    ttile = m.at("T_TILE", 11.0, "tile")
    m.put("efx", roomed(m, tile_lift(1), ttile), ttile, -13.0, label="she lifts a floor tile")
    m.put("amb", dsp.sos(sewer_bed(2.6, 3), "lowpass", 900.0, 2), ttile + 0.5, -36.0, align=None)
    for k, t in enumerate(m.ats("T_DROP", (13.5,), "drop", "splash")):
        m.put("efx", splash_drop(k), t, -10.0, pan=-0.1, label="they drop through: splash")
        m.put("efx", splash_drop(k + 2), t + 0.5, -13.0, pan=0.15)
    w0, w1 = span(m, "T_WADE", (14.0, 16.0), "walk north", "water", "wade")
    water_steps(m, w0, w1, 0.5, gain=-21.0, label="they walk north through the water", k0=3)
    # Plan B's chalk (the trapdoor, her route, the police, the red X) is spotted from its cues


@section("s09")
def s09(m, S):
    """The rewind (0-6.6): the film's own sound, cut where the picture rewinds to (a post-pass),
    under the tape's whoosh and the heist clock ticking backwards; the tape catches and plays his
    slam and her dot; freezes stop the sound dead (a ting on the dot); s02's looks played again.
    Plan B (6.6-10.4): D major under the chalk; the police chalked in with muted stabs rising a
    semitone a car; the red X on a low A. Then THE THEME, upright, in D major, from its cue (on
    its own beat), under the vault by match light, the tile, his chuckle, the floor torn away in
    section, the slides down the iron ladder (a splash each), the cut tearing on along the pipe,
    and Plan B's line lighting the way out (rising tings)."""
    if isinstance(S, Stub):
        return _s09_bible(m, S)
    L = m.len
    sched = rewind_schedule(S)
    for a, b, sid, s0, s1 in sched:
        m.rewind.append((m.t0 + a, m.t0 + b, START[sid] + s0, START[sid] + s1, sid))
    # the tape: a whoosh over each run it spools back, the heist clock ticking backwards in the first
    runs = []
    for a, b, sid, s0, s1 in sorted(sched):
        if played(a, b, s0, s1):
            continue
        if runs and a - runs[-1][1] < 0.05:
            runs[-1][1] = b
        else:
            runs.append([a, b])
    for k, (a, b) in enumerate(runs):
        c = m.cue_near(a, "rewind", "spools", win=0.2)
        a0 = min(a, float(c["t"])) if c else a
        dd = max(0.2, b - a0)
        m.put("efx", rewind_scrub(round(dd, 2), 1 + k), a0, -15.0 if k == 0 else -18.0,
              label="the tape spools back: a rising rewind whoosh" if k == 0 else "a short rewind whoosh", align=None)
        if dd > 1.0:
            wb = np.asarray(woodblock(0), np.float64)
            tt, j = a0 + 0.12, 0
            while tt < b - 0.12:
                u = (tt - a0) / dd
                x = np.asarray(woodblock(j % 4), np.float64)[::-1]
                m.put("rew", x * (0.6 + 0.4 * math.sin(math.pi * u)), tt - len(wb) / SR, -21.0, pan=0.3, hall=None)
                tt += 0.06 + 0.16 * (1.0 - math.sin(math.pi * u))
                j += 1
    m.cover("ticking backwards")
    # the catch, the freezes (the sound stops dead), the lenses
    tpl = m.at("T_PLAY", 2.75, "tape catches", "catches and plays")
    m.put("efx", switch_click(2, 0.5), tpl, -24.0, label="the tape catches and plays: a soft click")
    for k, fr in enumerate(g(S, "FREEZES", ())):
        try:
            a = float(fr[0])
        except Exception:
            continue
        if a < 0.1:
            continue
        m.put("efx", switch_click(5 + k, 1.3), a, -22.0, label="freeze: a tape pause, the sound stops dead")
    tl1 = m.at("T_LENS1", 3.55, "lens opens on the chalk dot", "ting")
    m.put("music", ting(4, 86), tl1, -13.0, pan=-0.1, label="a ting: the lens opens on the chalk dot", hall=-14.0)
    tl2 = m.at("T_LENS2", 6.05, "lens opens on her eye")
    m.put("efx", roomed(m, chalk_tap(74, 0.3), tl2), tl2, -21.0, label="a soft chalk tick: the lens opens on her eye")
    # Plan B: the tracing sheet; the trapdoor; her route; the police; the red X
    sl0, sl1 = span(m, "T_SHEET", (6.6, 7.15), "tracing paper unrolling", "unrolling over")
    m.put("efx", tracing_slide(round(sl1 - sl0 + 0.25, 2), 2), sl0, -15.0, label="tracing paper unrolling over the plan",
          align=None)
    b10, b11 = span(m, "T_B1", (7.4, 7.85), "four quick strokes", "a square")
    for j in range(4):
        tj = b10 + j * (b11 - b10) / 4
        m.put("efx", roomed(m, chalk_scratch(round(0.8 * (b11 - b10) / 4, 2), 100 + j, press=0.9), tj), tj, -18.0,
              pan=0.15 * (-1) ** j, label="chalk: four quick strokes, a square" if j == 0 else None, align=None)
    b20, b21 = span(m, "T_B2", (7.95, 8.9), "one long sure stroke", "long sure stroke")
    m.put("efx", roomed(m, chalk_scratch(round(b21 - b20, 2), 104, press=1.0), b20), b20, -17.0,
          label="chalk: one long sure stroke", align=None)
    for k, (t, _, c) in enumerate(cues_with(m, "whip whoosh")):
        m.put("efx", fx("whip", seed=60 + k), t, -19.0, pan=c["pan"], label="a whip whoosh", align=None)
    cops = m.ats("T_COPS", (9.15, 9.35, 9.55, 9.75), "police car chalked", "muted trumpet stab")
    for k, t in enumerate(cops):
        c = m.cue_near(t, "police", "stab")
        sym = ("Bb7", "B7", "C7", "C#7")[k % 4]
        stab(m, t, sym, gain=(c["gain_db"] + CUE_TRIM - 4.0) if c else -16.0 - k, dur=0.16, vel=0.75, seed=70 + k,
             label=f"a muted trumpet stab: a police car chalked in ({sym})", low=False, pan=0.3)
        m.put("music", bass(CHORDS[sym][0], 0.18, 0.8, 70 + k), t, -12.0, pan=-0.1, hall=-24.0)
        m.put("efx", roomed(m, chalk_tap(110 + k, 0.5), t), t, -25.0, pan=0.4)
    xb = g(S, "T_B4", (10.12, 10.32))
    tx = m.at("", float(xb[0]), "red x on the ruby", "two hard chalk slashes")
    for j, tj in enumerate((tx, tx + max(0.08, (float(xb[1]) - tx) / 2))):
        m.put("efx", roomed(m, chalk_scratch(0.09, 120 + j, press=1.0), tj), tj, -15.0, pan=0.2 * (1 - 2 * j),
              label="two hard chalk slashes: the red X" if j == 0 else None, align=None)
    hit(m, tx, 45, 0.7, gain=-12.0, label="a low stab (A): the red X on the ruby box")
    # the music under Plan B, on the theme's beat: D major, a walk up, G major 9 into the police
    tcue = m.at("", 10.4, "theme returns upright", "in the major")
    tth = math.ceil((m.t0 + tcue - FRAME) / BEAT - 1e-9) * BEAT - m.t0      # the theme keeps the film's beat
    if tth - tcue > FRAME:                     # on the cue itself: a grace note (C#) into its first D
        m.put("music", vibe(61, 0.14, 0.55, t_abs=m.t0 + tcue, depth=0.45, hard=0.5, seed=18), tcue, -15.0,
              label="the theme returns upright, in the major: a grace note into it")
        m.put("music", brass(61, 0.12, 0.45, seed=18, mute="open", scoop=False, vib=False), tcue, -21.0)
    gb = tth - 8 * BEAT
    vibe_chord(m, max(sl0, gb), (54, 59, 64, 69), 1.8, gain=-19.0, vel=0.5, roll=0.05, depth=0.5, seed=13,
               label="Plan B: D major")
    bassline(m, gb + BEAT, "D2 F#2 A2 B2 A2", gain=-11.5, vel=0.7, swell=(0.6, 0.9))
    vibe_chord(m, gb + 4 * BEAT, (54, 57, 59, 62), 1.4, gain=-20.0, vel=0.48, roll=0.04, depth=0.5, seed=14)
    drums(m, gb, 2, level=-9.0, kick_=False, seed=13, until=tth)
    m.put("music", cym_swell(round(max(0.5, tx - (gb + 4 * BEAT)), 2), 8), gb + 4 * BEAT, -27.0, align=None)
    # THE THEME, upright, in D major (the inversion inverted), from its cue to the cut
    stop = max(4, int(math.floor(((L - 0.45 - tth) / BEAT) * 2) / 2) - 1)
    melody(m, tth, THEME_MAJOR, gain=-12.0, vel=0.78, seed=19, stop=stop + 0.5,
           label="THE THEME returns upright, in D major (vibraphone, walking bass)")
    melody(m, tth, THEME_MAJOR, inst="tpt", gain=-17.5, vel=0.6, seed=19, mute="open", legato=0.92, stop=stop + 0.5)
    line = "D2 F#2 A2 D#2 E2 G2 A2 F#2 G2 B2 A2 G#2".split()[:max(1, int((L - 0.3 - tth) / BEAT) + 1)]
    bassline(m, tth, " ".join(line), gain=-10.0, vel=0.8)
    comp(m, tth, PROG_MAJOR[:4], gain=-21.0, vel=0.45, pattern="charleston", seed=8)
    drums(m, tth, 3, level=-3.0, seed=15, until=L - 0.1)
    m.cover_span(tth - FRAME, L, "theme returns", "in the major")
    # the vault by match light: the tile, his glint and chuckle; the floor cut away; the drop
    tv = m.at("T_VAULT", 10.9, "match's small hiss", "dark vault")
    m.put("amb", flame_bed(round(L - tv + 0.2, 2), 2), tv, -34.0, pan=-0.2, label="the match's small hiss in the dark vault",
          align=None)
    ti0, ti1 = g(S, "T_TILE", (11.2, 11.95))
    m.put("efx", roomed(m, tile_scrape(1), ti0), ti0, -13.0, pan=cpan(m, ti0, "tile", default=0.1),
          label="a stone tile scraped up out of the floor", align=None)
    tset = m.at("", float(ti1) - 0.15, "tile laid down", "dull clunk")
    m.put("efx", roomed(m, tile_set(1), tset), tset, -15.0, pan=cpan(m, tset, "clunk", default=0.25),
          label="the tile laid down: a dull clunk")
    tgl = m.at("", float(g(S, "T_GLINT", (12.15, 12.45))[0]), "light crosses his spectacles", "spectacles")
    m.put("music", ting(1, 93) * 0.8, tgl, -20.0, pan=0.3, label="a ting: the light crosses his spectacles", hall=-16.0)
    tgr = m.at("T_GRIN", 12.42, "chuckle")
    m.put("vox", roomed(m, chuckle(1), tgr), tgr, -19.0, pan=0.25, label="a low dry chuckle", align=None, key=True)
    ct0, ct1 = g(S, "T_CUT", (12.8, 13.35))
    m.put("efx", paper_torn(round(float(ct1) - float(ct0), 2), 1), ct0, -17.0,
          label="paper torn down: the floor cut away into section", align=None)
    m.put("amb", dsp.fade(dsp.sos(sewer_bed(round(L - float(ct0) + 0.3, 2), 3), "lowpass", 1200.0, 2), 0.6, 0.1), ct0,
          -34.0, align=None)
    # she gets up and steps into the hole; he steps to it
    r0 = float(g(S, "T_RISE", (12.66, 13.15))[0])
    m.put("efx", roomed(m, cloth(0.4, 23, heavy=0.4), r0), r0, -28.0, pan=-0.05, align=None)
    sh0 = float(g(S, "T_STEP_HIM", (13.25, 13.8))[0])
    m.put("feet", footstep("cracker", 3, "cell", seed=3), sh0 - STEP_PRE, -25.0, pan=0.15, sync=sh0)
    # down the iron ladder, her then him: gloves and a coat on the rails, a splash at the foot
    slides = g(S, "T_SLIDE", ((13.15, 13.8), (13.85, 14.45)))
    for k, pr in enumerate(slides):
        try:
            d0, d1 = float(pr[0]), float(pr[1])
        except Exception:
            continue
        cd = m.cue_near(d0, "slid", "ladder", win=0.1)
        m.put("efx", roomed(m, ladder_slide(round(d1 - d0, 2), 30 + k, 0.4 + 0.5 * k), d0), d0,
              ((cd["gain_db"] + CUE_TRIM) if cd else -17.0) - 2.0, pan=float(cd["pan"]) if cd else 0.0,
              label=("gloves and a coat sliding fast down the iron ladder" if k == 0 else
                     "a heavier slide down the iron ladder"), align=None)
        cs_ = m.cue_near(d1, "splash", win=0.15)
        ts = float(cs_["t"]) if cs_ else d1
        m.put("efx", splash_drop(k), ts, ((cs_["gain_db"] + CUE_TRIM) if cs_ else -11.0) - 1.0,
              pan=float(cs_["pan"]) if cs_ else 0.0,
              label="a splash in shallow water, echoing in the pipe" if k == 0 else "a heavier splash, echoing")
    tu0 = float(g(S, "T_TURN", (13.92, 14.1))[0])
    m.put("efx", roomed(m, paper_whoosh(0.18, 31), tu0), tu0, -31.0, pan=-0.1, align=None)
    # the cut runs on north along the pipe, ahead of her; Plan B's line lights the way (rising tings)
    rv0, rv1 = span(m, "T_REVEAL", (14.1, 15.7), "torn on along the pipe")
    cr_ = m.cue_near(rv0, "torn on", win=0.1)
    m.put("efx", paper_tear_run(round(rv1 - rv0, 2), 2), rv0, ((cr_["gain_db"] + CUE_TRIM) if cr_ else -19.0) - 1.0,
          pan=float(cr_["pan"]) if cr_ else -0.3, label="paper torn on along the pipe", align=None)
    li0, li1 = span(m, "T_LIT", (15.15, 15.75), "rising chime", "lights the way")
    for j, p in enumerate((86, 90, 93, 98)):
        tj = li0 + j * (li1 - li0) / 4
        m.put("music", ting(5 + j, p) * (0.95 - 0.1 * j), tj, -19.0 - 0.5 * j, pan=-0.3 + 0.12 * j, hall=-14.0,
              label="a rising chime: Plan B's line lights the way to the street" if j == 0 else None)
    for k, (t, _, c) in enumerate(cues_with(m, "footstep in shallow water")):
        m.put("feet", water_step((k + 5) % 8, (0.5, 0.65, 0.8)[k % 3]), t, c["gain_db"] + CUE_TRIM, pan=c["pan"],
              label="a footstep in shallow water")


# ============================================================================ s10 CHECKMATE (124-136): bars 62-67
@section("s10")
def s10(m, S):
    """Bar 62, the getaway: the alarm bell hard and high; he bursts round the car, the band driving
    under him; the band stops on the door's slam and the starter grinds and coughs in the clear.
    Bar 63: the engine catches on the bar line and the band comes in hot (the trumpets on the
    theme's head an octave up); the tyres, the headlight's white, the board. Bar 64: four police
    cars slide in, one a beat, a muted stab each rising a semitone (Plan B's chalk come true); the
    sirens, tuned to the theme's fifth, braid over them. Bar 65: CHECKMATE on the bar line, a hard
    low stab and a choked cymbal; his heart. Bars 66-67, behind the bank: the back street's night
    air, a drip down the shaft, a boot on each rung, manhole B's lid knocked up and dragged aside,
    and two pairs of soft steps away west on the beat, under the theme in D major (the sirens
    braided into it, receding); the routes swell into the X on a held A13; the theme's last phrase
    resolves into s11's D."""
    L = m.len
    t62, t63, t64, t65, t66, t67 = (FB(m, b) for b in range(62, 68))
    tn = float(g(S, "T_NOSE", 1.46))
    tbd = float(g(S, "T_BOARD", 2.92))
    # the street: the alarm bell hard and high in the alley (further off on the car's nose); night air
    ab = alarm_bell(round(tbd + 0.3, 2), 2)
    u = tax(len(ab))
    env = (1.0 - 0.65 * np.clip((u - tn) / 0.01, 0, 1)) * np.clip((tbd + 0.3 - u) / 0.3, 0, 1)
    m.put("amb", rev(ab * env, -12.0, 3, "street"), 0.0, -17.0, pan=cpan(m, 0.0, "alarm", default=0.5),
          label="the alarm bell ringing hard, high in the alley", align=None)
    na = night_air(round(tbd + 0.3, 2), 2)
    m.put("amb", na * np.clip((tbd + 0.3 - tax(len(na))) / 0.3, 0, 1)[:, None], 0.0, -31.0, align=None)
    # he bursts round the car's tail and runs (the footfalls the picture has), skids, heaves, slams
    tr = float(g(S, "T_RUN", 0.2))
    cr = m.cue_near(tr, "running", win=0.1)
    r1 = tr + (float(cr.get("dur") or 0.75) if cr else 0.75)
    falls = []
    try:
        p, _ = S._run()
        falls = [float(f[0]) for f in S.Bk.footfalls(lambda u_: p(u_), tr, tr + 1.75)]
    except Exception as e:
        if not isinstance(S, Stub):
            warn(f"s10: the run's footfalls cannot be read ({type(e).__name__}: {e}): steps on a 0.25 s cadence")
    if not falls:
        falls = [float(x) for x in np.arange(tr + 0.25, r1 + 1e-6, 0.25)]
    gr = cgain(m, tr, "running", default=-12.0)
    for k, tf in enumerate([tr] + [f for f in falls if f > tr + 0.12]):
        x = pitch(dsp.sos(footstep("run", k + 3, "street", seed=k % 5), "lowpass", 3800.0, 2), -1.5)
        m.put("feet", x, tf - STEP_PRE, gr - 2.0 - (6.0 if tf > r1 + 0.1 else 0.0), pan=max(0.3, 0.6 - 0.1 * k),
              label="heavy running footsteps on cobbles" if k == 0 else None, sync=tf)
    tsk = m.at("", tr + 0.85, "skidding stop")
    m.put("feet", roomed(m, skid_stop(1), tsk), tsk, cgain(m, tsk, "skid", default=-14.0) - 3.0,
          pan=cpan(m, tsk, "skid", default=0.4), label="a skidding stop", align=None)
    th0 = float(g(S, "T_HEAVE", (0.95, 1.12))[0])
    m.put("vox", roomed(m, grunt(2), th0), th0, cgain(m, th0, "grunt", default=-16.0) - 6.0,
          pan=cpan(m, th0, "grunt", default=0.4), label="a grunt of effort", align=None, key=True)
    tsa = float(g(S, "T_THROW", (1.12, 1.26))[1])
    for k in range(2):
        m.put("efx", roomed(m, gold_bag(5 + k), tsa + 0.03 * k), tsa + 0.03 * k,
              cgain(m, tsa, "sacks", default=-10.0) - 2.0 - 2.0 * k, pan=cpan(m, tsa, "sacks", default=0.35),
              label="two heavy sacks of gold thumped into the back seat" if k == 0 else None)
    tsl = float(g(S, "T_SLAM", (1.32, 1.42))[0])
    m.put("efx", roomed(m, fx("car_door_close", seed=1), tsl), tsl, cgain(m, tsl, "car door", default=-8.0) - 3.0,
          pan=cpan(m, tsl, "car door", default=0.3), label="a car door slammed hard")
    # bar 62: the band drives under the run and stops on the slam
    bassline(m, t62, "D2 D2 A1", gain=-10.0, vel=0.9, gate=0.7, label="his getaway: the drive")
    for k in range(3):
        m.put("music", kick(k % 3, 0.5), t62 + k * BEAT, -25.0, hall=None)
    drums(m, t62, 1, level=0.0, ride_=True, sweep=False, kick_=False, seed=15, slap=0.6, until=tsl - 0.02)
    melody(m, t62, THEME, inst="tpt", gain=-13.5, vel=0.9, octave=1, mute="open", stop=2, seed=21,
           label="the trumpets, hot: the theme's first notes")
    stab(m, tsl, "DmM7", gain=-13.0, dur=0.25, vel=0.95, seed=55, sync=tsl)
    m.put("music", kick(2, 0.8), tsl, -21.0, hall=None)
    # the starter grinds in the clear: two coughs; it catches; the headlight flares; the tyres
    c0, c1 = g(S, "T_COUGH", (1.62, 1.86))
    tli = float(g(S, "T_LIGHTS", 2.02))
    tlu = float(g(S, "T_LURCH", (2.5, 2.9))[0])
    eng = getaway_start(1, (0.0, round(c1 - c0, 3)), round(tli - c0, 3), round(tlu - c0, 3), round(tbd - c0, 3))
    m.put("efx", roomed(m, eng, c0, wet=-16.0), c0, cgain(m, c0, "starter", default=-11.0) - 1.0, pan=0.1,
          label="a starter motor grinding, the engine coughing twice", align=None)
    m.put("efx", roomed(m, switch_click(7, 0.6), tli), tli, -20.0, pan=0.1,
          label="the headlight clicks on; the engine catches and roars")
    m.put("efx", light_swell(0.6, 1), tli, -26.0, align=None)
    m.put("efx", roomed(m, tyre_squeal(0.42, 1, 1900.0, 0.12), tlu), tlu, cgain(m, tlu, "tyres", default=-10.0) - 6.0,
          pan=cpan(m, tlu, "tyres", default=-0.4), label="tyres squealing as the car lurches off", align=None)
    tfl = float(g(S, "T_FLASH", (2.68, 2.92))[0])
    wh = dsp.sos(fx("whoosh", seed=3, size=0.5), "highpass", 1200.0, 2)
    m.put("efx", wh, tfl, cgain(m, tfl, "white whoosh", default=-14.0) - 6.0, label="a white whoosh", align=None)
    # bar 63: the engine catches on the bar line, the band in, hot
    hit(m, t63, 38, 0.9, gain=-12.0, label="the band comes in hot (the engine catches)")
    m.put("music", crash(3, 2.4), t63, -21.0, pan=0.2, hall=-18.0)
    bassline(m, t63, "D2 D2 A1 C2", gain=-10.0, vel=0.9, gate=0.7)
    for k in range(4):
        m.put("music", kick(k % 3, 0.5), t63 + k * BEAT, -25.0, hall=None)
    drums(m, t63, 1, level=0.0, ride_=True, sweep=False, kick_=False, seed=16, slap=0.6)
    melody(m, t63, THEME, inst="tpt", gain=-12.5, vel=0.9, octave=1, mute="open", stop=4, seed=22, fall_last=2.0,
           label="the trumpets, hot, on the theme's head")
    melody(m, t63, THEME, inst="tpt", gain=-16.5, vel=0.75, stop=4, seed=23)
    sp0 = float(g(S, "T_SPEED", (3.15, 3.55))[0])
    cw = m.cue_near(sp0, "racing away", win=0.1)
    m.put("efx", dsp.sos(fx("car_away", dur=max(1.2, float(cw.get("dur") or 0.8) + 0.8) if cw else 1.6, seed=2),
                         "lowpass", 5000.0, 2), sp0, cgain(m, sp0, "racing away", default=-16.0) - 5.0, pan=0.1,
          label="the engine racing away", align=None)
    # bar 64: the police slide in, one a beat: a muted stab each, rising a semitone (Plan B's chalk)
    cops = [float(x) for x in g(S, "T_COPS", (4.0, 4.5, 5.0, 5.5))]
    for k, tc in enumerate(cops):
        c = m.cue_near(tc - 0.2, "police car", win=0.25)
        tw = float(c["t"]) if c else tc - 0.2
        pn = float(c["pan"]) if c else (-0.7, 0.0, 0.7, 0.0)[k % 4]
        m.put("efx", car_slide(k, 0.36), tc - 0.36, -21.0, pan=pn, align=None)
        m.put("efx", police_whoop(k, hz(81) if k % 2 else hz(74)), tw, (c["gain_db"] + CUE_TRIM - 12.0) if c else -21.0,
              pan=pn, label="a police car sliding in: a siren whoop")
        sym = ("Bb7", "B7", "C7", "C#7")[k % 4]
        stab(m, tc, sym, gain=-12.0 + 0.5 * k, dur=0.22, vel=0.9, seed=50 + k, pan=0.6 * pn,
             label=f"a police car arrives: a muted stab ({sym})")
        m.put("music", kick(k % 3, 0.6), tc, -23.0, hall=None)
    m.put("music", brush_roll(round(t65 - cops[0], 2), 4), cops[0], -26.0, pan=0.15, hall=-22.0, align=None)
    tbr = m.at("", cops[0] + 0.05, "brakes screeching")
    m.put("efx", roomed(m, tyre_squeal(0.5, 2, 2300.0, 0.25), tbr), tbr, cgain(m, tbr, "brakes", default=-13.0) - 6.0,
          pan=cpan(m, tbr, "brakes", default=-0.2), label="brakes screeching", align=None)
    # the sirens, tuned D-A (the theme's first fifth), braiding: rising to checkmate, then receding
    tx0, tx1 = g(S, "T_X", (10.0, 11.2))
    tbk = float(g(S, "T_BACK", 7.2))
    sd = max(1.0, L - cops[0])
    sir = sirens(round(sd, 2), 3)
    v = tax(len(sir)) + cops[0]
    env = (np.clip((v - cops[0]) / max(0.5, t65 - cops[0]), 0, 1) ** 0.7 *
           db2lin(-9.0 * np.clip((v - tbk) / 1.8, 0, 1) - 6.0 * np.clip((v - tx0) / max(0.3, tx1 - tx0), 0, 1)) *
           np.clip((L - v) / 0.012, 0, 1))          # far off to the last frame: s11's rip cuts them off
    m.put("efx", roomed(m, sir * env[:, None], cops[0], wet=-14.0), cops[0], cgain(m, cops[0], "sirens", default=-15.0) - 6.0,
          label="sirens braiding together, rising (tuned D-A)", align=None)
    # bar 65: CHECKMATE: a hard low stab and a choked cymbal; the held spy chord; his heart, his breath
    tm_ = m.at("T_MATE", 6.0, "checkmate")
    stab(m, tm_, "DmM7", gain=-11.5, dur=0.5, vel=1.0, seed=60, label="checkmate: a hard low stab")
    hit(m, tm_, 38, 0.95, gain=-13.5)
    m.put("music", choked(crash(7, 1.0), 0.2), tm_, -15.0, pan=0.2, hall=-18.0)
    vibe_chord(m, tm_ + 0.02, CHORDS["DmM7"][1], 1.6, gain=-20.0, vel=0.55, depth=0.6, seed=14)
    m.put("music", arco(38, 1.4, 0.6, seed=7, attack=0.1, release=0.4), tm_, -17.0, align=None)
    f0, f1 = g(S, "T_FACE", (6.42, 7.2))
    hb = fx("heartbeat", dur=round(f1 - f0 + 0.2, 2), seed=1, bpm=118)
    m.put("efx", hb, f0, cgain(m, f0, "heartbeat", default=-12.0) + 2.0, label="a heartbeat thump", align=None)
    m.put("vox", breath("in"), f0 + 0.08, -19.0, pan=0.05, align=None, key=True)
    # behind the bank, the back street (full frame): night air, a drip down the shaft; manhole B's lid
    # knocked up off its seat and dragged aside; a boot on each rung; then their soft steps away west
    tbk0 = m.at("", tbk, "cut to the back street", win=0.5)
    esc1 = float(g(S, "T_ESC", (7.2, 9.5))[1])
    m.put("amb", night_air(round(esc1 - tbk0 + 0.6, 2), 9), tbk0, -29.0, label="night air in the back street",
          align=None)
    m.put("efx", drip(4), tbk0 + 0.32, -27.0, pan=0.2, align=None)
    tkn = m.at("", 7.47, "knocked up off its seat", win=0.6)
    m.put("efx", rev(pitch(dsp.sos(rung(30), "lowpass", 1800.0, 2), -5.0), -9.0, 5, "street"), tkn, -15.0, pan=0.25,
          label="an iron clunk: the lid knocked up off its seat")
    tlid = float(g(S, "T_LID", (7.6, 7.88))[0])
    m.put("efx", rev(manhole_scrape(0.35, 2), -8.0, 4, "street"), tlid, cgain(m, tlid, "manhole", default=-14.0) - 8.0,
          pan=cpan(m, tlid, "manhole", default=0.3), label="an iron manhole cover dragged aside", align=None)
    for k, (t, _, c) in enumerate(cues_with(m, "iron rung")):
        m.put("efx", rev(rung(20 + k), -10.0, k, "cell"), t, -24.0, pan=c["pan"], label="a boot on an iron rung")
    for k, (t, _, c) in enumerate(cues_with(m, "soft footstep on the cobbles")):
        who = "her" if "hers" in c["sfx"] else "cracker"
        m.put("feet", footstep(who, 4 + k, "street", seed=4 + k), t - STEP_PRE, -25.0 if who == "her" else -26.5,
              pan=c["pan"], label="a soft footstep on the cobbles", sync=t)
    # bar 66: the theme in D major, soft, braided with the receding sirens (D-A)
    melody(m, t66, THEME_MAJOR, gain=-15.0, vel=0.6, stop=4, seed=23, label="the theme in D major, soft (they walk)")
    bassline(m, t66, "D2 ~ A1 ~", gain=-12.0, vel=0.65)
    comp(m, t66, (("D69", 4),), gain=-23.0, vel=0.4, pattern="whole", seed=10)
    drums(m, t66, 1, level=-10.0, taps=False, kick_=False, seed=16)
    # bar 67: the routes straighten into the X: two long strokes swelling into a held A13 ...
    for j, pn in enumerate((-0.3, 0.3)):
        m.put("efx", roomed(m, chalk_scratch(round(tx1 - tx0, 2), 92 + j, press=0.8), tx0), tx0, -21.0, pan=pn,
              label="two long strokes of chalk swelling into a held chord" if j == 0 else None, align=None)
    brass_swell(m, tx0, "A13", round(tx1 - tx0, 2), gain=-17.0, seed=12)
    vibe_chord(m, tx0, CHORDS["A13"][1], round(tx1 - tx0 + 0.25, 2), gain=-20.0, vel=0.5, depth=0.5, seed=17)
    m.put("music", arco(33, round(tx1 - tx0 + 0.3, 2), 0.6, seed=9, attack=0.4, release=0.3), tx0, -17.0, align=None)
    m.put("music", bass(33, 0.6, 0.7, 3), tx0, -13.0, hall=-24.0)
    m.put("music", cym_swell(round(tx1 - tx0, 2), 9), tx0, -28.0, align=None)
    # ... and the theme's last phrase, out of time off the held chord, resolving on s11's downbeat
    tlp = m.at("", float(tx1), "last phrase", "resolving")
    last = ((tlp, 67, 0.3), (tlp + (L - tlp) * 0.31, 64, 0.3), (tlp + (L - tlp) * 0.62, 61, 0.36), (L, 62, 1.6))
    for j, (tj, p, d) in enumerate(last):
        m.put("music", vibe(p, d, 0.62 if j < 3 else 0.7, t_abs=m.t0 + tj, motor=VIB_RATE, depth=0.45, hard=0.5, seed=30 + j),
              tj, -14.5, label="the theme's last phrase, resolving" if j == 0 else None)
        m.put("music", brass(p, d * 0.9, 0.5, seed=30 + j, mute="harmon", scoop=False, vib=j == 3), tj, -21.0, pan=0.15)
    m.put("music", bass(33, 0.5, 0.7, 4), tlp, -13.0, hall=-24.0)
    m.cover_span(t66, L, "theme", "major", "last phrase")


# ============================================================================ s11 END (136-144): bars 68-71
@section("s11")
def s11(m, S):
    """Bar 68, the street under the lamp: s10's X tears the frame open (a paper rip; the sirens cut
    off) onto D major, s10's last phrase resolved on its downbeat; her glove opens one finger after
    another, and the ruby's glint is the ONE celesta ping (A6); the glove creaks shut on it. Bars
    69-70, dawn at the table: the theme's last two bars in D major, plainly, on the vibraphone; the
    queen's base clicks the knight's and he goes over on bar 70's downbeat (clack, roll); its C# is
    held over A13 as the camera rises and the chalk X lifts off. Bar 71: it resolves on D as the
    title X lands (the last chord, D6/9); DOUBLE and CROSS slide back in; the red dot's chalk tap,
    the film's last, with the bass's button on D; black, and digital silence from 143.5."""
    t68, t69, t70, t71 = (FB(m, b) for b in range(68, 72))
    tend = silence_from() - m.t0
    ttab = float(g(S, "T_TABLE", 3.0))
    # the split: the frame torn open along s10's X, the four pieces whooshing apart (s10's sirens
    # were cut on this frame)
    sp0, sp1 = span(m, "T_SPLIT", (0.0, 0.62), "paper rip", "tears open")
    m.put("efx", roomed(m, paper_torn(0.42, 7), sp0), sp0, cgain(m, sp0, "rip", "tear", "split", default=-10.0) - 3.0,
          label="a paper rip: the frame tears open along the X (the sirens cut off)", align=None)
    for k, (pn, dt) in enumerate(((-0.6, 0.05), (0.6, 0.08), (-0.2, 0.12), (0.25, 0.15))):
        d = round(max(0.3, sp1 - sp0 - dt + 0.05), 2)
        m.put("efx", paper_whoosh(d, 30 + k), sp0 + dt, -22.0 - 1.0 * k, pan=pn,
              label="the four pieces whoosh apart" if k == 0 else None, align=None)
    # bar 68: D major under s10's resolution (its D4 on this downbeat): the vibraphone's D6/9, the
    # bass's D, the arco under it
    vibe_chord(m, t68, CHORDS["D69"][1], 2.1, gain=-21.0, vel=0.5, depth=0.5, seed=15, label="D major (D6/9)")
    m.put("music", bass(38, 0.9, 0.62, 5), t68, -14.0, pan=-0.1, hall=-24.0)
    m.put("music", arco(38, 2.3, 0.55, seed=5, attack=0.4, release=0.6), t68, -18.0, align=None)
    # the street under the lamp: its low electric hum, the city far off, a far drip
    cst = m.cue_of("night street", "electric hum")
    s0 = float(cst["t"]) if cst else 0.3
    s1 = max(s0 + 0.5, ttab)
    sd = round(s1 - s0, 2)
    m.put("amb", dsp.sos(bed("bulb_hum", sd, 3, fin=0.5, fout=0.04), "lowpass", 900.0, 2), s0,
          cgain(m, s0, "night street", default=-26.0) - 15.0,
          label="a night street under a lamp: a low electric hum, a far drip", align=None)
    m.put("amb", bed("city_far", sd, 5, fin=0.6, fout=0.04), s0, -40.0, align=None)
    for k, td in enumerate((s0 + 0.62, s0 + 1.85)):
        if td < s1 - 0.25:
            m.put("amb", far_drip(21 + k), td, -31.0 - 3.0 * k, pan=-0.45 + 0.25 * k)
    # her gloved fingers open, one after another (the index first); the ruby's glint: the ONE
    # celesta ping; her fist closes on it, tight
    o0, o1 = span(m, "T_OPEN", (0.55, 1.3), "leather creak", "fingers open")
    og = cgain(m, o0, "leather creak", default=-20.0)
    sc = (o1 - o0) / 0.75
    od = round(max(0.25, o1 - o0 - 0.3), 2)
    for k, dl in enumerate((0.0, 0.08, 0.16, 0.24)):
        t = o0 + dl * sc
        m.put("efx", roomed(m, glove_creak(3 + k, od), t), t, og - 5.0 - 1.0 * k, pan=0.12 - 0.05 * k,
              label="leather creak: her gloved fingers open, one after another" if k == 0 else None, align=None)
    tping = m.at("T_PING", 1.5, "celesta", "ping", "glints")
    m.put("music", celesta(93, 0.8, 1), tping, -10.5, pan=0.1, label="the ruby glints: ONE celesta ping", hall=-12.0)
    tf = m.at("T_FIST", 2.45, "fist closes", "creaks tight")
    fd = float(np.clip(g(S, "FIST_DUR", 0.3), 0.15, 0.8))
    m.put("efx", roomed(m, glove_creak(9, round(fd + 0.08, 2)), tf), tf, cgain(m, tf, "fist", default=-16.0) - 4.0,
          pan=0.1, label="her fist closes on it: the glove creaks tight", align=None)
    # dawn at the table: a quiet room, a bird far off; her sleeve brushes the paper as the queen
    # comes in low; the click of its base on his; he goes over (clack, roll)
    cdw = m.cue_of("dawn at the table", "bird far off")
    d0 = float(cdw["t"]) if cdw else ttab
    r0, r1 = span(m, "T_RISE", (4.35, 5.5), "camera rises", "airy swell")
    rt = np.asarray(bed("room_tone", round(tend - d0, 2), 4, fin=0.03, fout=0.1), np.float64)
    rt = rt * db2lin(-6.0 * np.clip((tax(len(rt)) + d0 - r0) / max(0.3, r1 - r0), 0, 1))[:, None]
    m.put("amb", rt, d0, cgain(m, d0, "dawn", default=-26.0) - 9.0,
          label="dawn at the table: quiet room tone, a bird far off", align=None)
    m.put("amb", bird_far(2), d0 + 0.14, -33.0, pan=0.55, align=None)
    csl = m.cue_of("sleeve brushes", "sleeve")
    ti0, ti1 = g(S, "T_IN", (3.0, 3.85))
    sl0 = float(csl["t"]) if csl else float(ti0) + 0.2
    sld = round(max(0.25, float(csl["dur"]) if csl and csl.get("dur") else float(ti1) - sl0), 2)
    m.put("efx", roomed(m, cloth(sld, 12, heavy=0.0), sl0), sl0, cgain(m, sl0, "sleeve", "cloth", default=-24.0) - 4.0,
          pan=cpan(m, sl0, "sleeve", default=-0.3), label="her sleeve brushes the paper as the queen comes in low",
          align=None)
    m.put("efx", roomed(m, tracing_slide(sld, 5), sl0), sl0 + 0.05, -34.0, pan=-0.3, align=None)
    th = m.at("T_HIT", 3.85, "click", "base knocks")
    m.put("efx", roomed(m, piece_clack(14, 0.25), th), th, cgain(m, th, "click", default=-14.0) - 2.0,
          pan=cpan(m, th, "click", default=0.1), label="click: the queen's base knocks the knight's")
    ttip = m.at("T_TIP", 4.0, "tips the knight", "clack, roll")
    m.put("efx", roomed(m, piece_tip(1), ttip), ttip, cgain(m, ttip, "tips", default=-10.0) - 1.0,
          pan=cpan(m, ttip, "tips", default=0.2), label="she tips the knight over: clack, roll")
    # bars 69-70: the theme's last two bars in D major, plainly (the vibraphone), over Gmaj9 and
    # A13; its C# held over the A13 as the camera rises, into the title
    melody(m, t69 - 8 * BEAT, THEME_MAJOR, gain=-13.0, vel=0.66, start=8, stop=13, seed=24,
           label="the theme's last bars, in D major")
    bassline(m, t69, "G2 ~ B1 ~", gain=-12.0, vel=0.66)
    comp(m, t69, (("Gmaj9", 4),), gain=-22.0, vel=0.42, pattern="sparse", seed=9)
    drums(m, t69, 1, level=-12.0, taps=False, kick_=False, hat=False, seed=17)
    ttl = m.at("T_TITLE", 6.0, "title x lands", "last chord")
    tcs = t69 - 8 * BEAT + sw(13)
    tres = float(np.clip(ttl, tcs + 0.4, tend - 0.6))           # it resolves as the title lands
    hold = round(tres - tcs, 3)
    m.put("music", vibe(61, hold + 0.1, 0.62, t_abs=m.t0 + tcs, depth=0.5, hard=0.5, seed=40), tcs, -13.5,
          label="its C#, held over A13")
    m.put("music", brass(61, hold, 0.5, seed=40, mute="harmon", scoop=False, vib=True, attack=0.12), tcs, -23.0, pan=0.15)
    m.put("music", bass(33, 0.9, 0.7, 6), t70, -12.5, pan=-0.1, hall=-24.0)
    m.put("music", arco(33, round(tres - t70 + 0.1, 2), 0.55, seed=6, attack=0.3, release=0.25), t70, -18.0, align=None)
    vibe_chord(m, t70, (55, 59, 66), round(tres - t70 + 0.15, 2), gain=-21.0, vel=0.45, depth=0.55, seed=19)
    m.put("music", piano(45, 1.6, 0.42, 7), t70, -23.0, pan=-0.1)
    m.put("music", cym_swell(round(max(0.5, tres - r0), 2), 11), r0, -30.0, align=None)
    # the camera rises: an airy swell; the chalk X lifts off the vault and grows into the title
    m.put("efx", air_swell(round(max(0.4, r1 - r0), 2), 3), r0, cgain(m, r0, "airy", "camera rises", default=-22.0) - 6.0,
          label="the camera rises off the table: an airy swell", align=None)
    g0, g1 = span(m, "T_GROW", (5.5, 6.0), "chalk x lifts", "grows into the title")
    wg = cgain(m, g0, "whoosh", "chalk x", "grows", default=-14.0)
    m.put("efx", paper_whoosh(round(max(0.3, g1 - g0 + 0.05), 2), 41), g0, wg - 6.0,
          label="whoosh: the chalk X lifts off the vault and grows into the title", align=None)
    m.put("efx", fx("whoosh", seed=42, size=0.2), g0 - 0.05, wg - 11.0, align=None)
    # bar 71: the title X lands: the last chord, D6/9, and the theme's D
    ring = max(0.3, tend - tres)
    vibe_chord(m, tres, (54, 59, 64, 69, 76), ring, gain=-16.0, vel=0.62, roll=0.03, depth=0.45, seed=16,
               label="the title X lands: the last chord (D6/9)")
    m.put("music", vibe(62, ring, 0.66, t_abs=m.t0 + tres, depth=0.45, hard=0.5, seed=44), tres, -14.5)
    m.put("music", brass(62, max(0.2, ring - 0.1), 0.5, seed=44, mute="harmon", scoop=False, vib=True), tres, -22.0,
          pan=0.15)
    m.put("music", piano(26, ring, 0.5, 5), tres, -17.0)
    m.put("music", piano(38, ring, 0.45, 6), tres, -18.0)
    m.put("music", bass(38, ring, 0.75, 1), tres, -13.0, hall=-24.0)
    m.put("music", arco(38, ring, 0.5, seed=8, attack=0.2, release=0.3), tres, -18.0, align=None)
    m.put("efx", roomed(m, strip_thud(8), tres), tres, -23.0)
    if abs(ttl - tres) > FRAME:
        m.mark(ttl, "the title X lands (under the last chord)")
    # DOUBLE and CROSS slide back in where the opening's flew out
    for k, (cname, tdef, w, lab) in enumerate((("T_DOUBLE", 6.2, "double slides", "DOUBLE slides back in from the top"),
                                               ("T_CROSS", 6.45, "cross slides", "CROSS slides back in from the bottom"))):
        tw = m.at(cname, tdef, w)
        m.put("efx", paper_whoosh(0.42, 45 + k), tw, cgain(m, tw, "paper whoosh", default=-18.0) - 6.0,
              label=f"paper whoosh: {lab}", align=None)
    # the ruby lands as the red dot at the crossing: the film's last chalk tap, and the bass's button
    tdot = m.at("T_DOT", 7.0, "red dot lands", "last tap")
    m.put("efx", roomed(m, chalk_tap(13, 0.8), tdot), tdot, cgain(m, tdot, "chalk tap", default=-12.0) - 2.0,
          label="chalk tap: the red dot lands at the crossing (the film's last tap)")
    m.put("music", bass(38, 0.22, 0.7, 7), tdot, -14.0, pan=-0.1, hall=-22.0)
    m.put("music", piano(26, 0.3, 0.45, 8), tdot, -21.0, pan=-0.1)
    m.mark(tend, "black: digital silence")
    m.cover("black")


# ============================================================================ the bible, for missing scenes
def _bc(t, text, gain=-12.0, dur=None, pan=0.0):
    c = {"t": float(t), "sfx": text, "gain_db": float(gain), "pan": float(pan)}
    if dur is not None:
        c["dur"] = float(dur)
    return c


BIBLE_CUES = {       # the bible's sound beats, scene times (what a stand-in is spotted from)
    "s01": [_bc(0.0, "chalk tap: a dot at a corner of the bank's front", -10, pan=-0.6),
            _bc(0.5, "chalk tap: a dot at a corner of the bank's front", -10, pan=0.6),
            _bc(1.0, "chalk tap: a dot at a corner of the bank's front", -10, pan=0.6),
            _bc(1.5, "chalk tap: a dot at a corner of the bank's front", -10, pan=-0.6),
            _bc(2.25, "a paper whoosh: the camera tilts up over the street to the plan", -14, 1.25)]
           + [_bc(3.5 + 0.5 * k, f"chalk scratch: the {w} ruled in", -12, 0.42)
              for k, w in enumerate(("bank", "vault", "corridor", "streets", "manholes", "sewer", "side door"))]
           + [_bc(8.0, "whoosh-thud: the first strip slashes across", -6, pan=0.3),
              _bc(8.5, "whoosh-thud, heavier: the second strip crosses it", -5, pan=-0.3),
              _bc(9.0, "stamp: DOUBLE", -6), _bc(9.5, "stamp: CROSS", -6),
              _bc(10.0, "the letters lift away (paper whoosh)", -12),
              _bc(10.5, "the lamp's gold pool fades up: a low warm hum", -14, 1.5),
              _bc(11.0, "thud: the X lands on the vault", -8)],
    "s02": [_bc(1.0, "clack: the white queen set on manhole A", -8, pan=-0.3),
            _bc(3.5, "clack: the gold bishop set", -9, pan=0.2),
            _bc(4.8, "ting: a glint crosses his spectacles", -12, pan=0.3),
            _bc(6.0, "THUD: the red knight slammed down; the other pieces jump", -4, pan=0.2),
            _bc(7.0, "the ember brightens as he draws on the cigarette", -16, pan=-0.2),
            _bc(7.8, "he breathes the smoke out", -20),
            _bc(8.5, "the lamp's chain creaks as it swings", -22, 3.0),
            _bc(10.0, "her look to him: a low held note (she knows)", -12, 2.0),
            _bc(11.0, "she picks up the chalk", -16, pan=-0.6)],
    "s03": [_bc(0.5, "chalk: route 1, manhole A down into the sewer, east, north to the hatch (dotted)", -16, 2.5),
            _bc(1.5, "clack: the pieces hop along it", -15), _bc(2.5, "clack: the pieces hop along it", -15),
            _bc(3.0, "chalk: route 2 through the store room into the corridor (dotted)", -16, 1.0),
            _bc(4.0, "clack: she sets a black pawn on the guard post", -10),
            _bc(4.5, "chalk scratch: the guard's cone", -14, 0.6),
            _bc(5.0, "chalk circle: a timing ring round the pawn", -14, 0.8),
            _bc(7.0, "clack: a piece hops across in a dark gap", -13), _bc(7.5, "clack: a piece hops across", -13),
            _bc(8.0, "clack: a piece hops across", -13),
            _bc(9.0, "chalk: route 4 north to the vault door (dotted)", -16, 0.8),
            _bc(9.5, "chalk circle: a small dial drawn at the door", -15, 0.4),
            _bc(10.0, "clack: the bishop steps to the dial", -13),
            _bc(10.5, "chalk arc: the door's arc swings open onto the X", -15, 0.5),
            _bc(11.0, "chalk: route 5, the exit back to manhole A and along the street (dotted)", -16, 1.2),
            _bc(12.0, "chalk scratch: a chalk car", -15, 0.4),
            _bc(12.5, "clack: the knight set at the car", -11),
            _bc(12.8, "chalk: a small bell drawn on the side door", -20, 0.3),
            _bc(14.0, "the plant: a soft tap, a small dot on the sewer line under the vault", -14),
            _bc(15.0, "the camera begins to tilt toward the bank (a swell)", -18, 1.0)],
    "s04": [_bc(0.0, "the pop-up: the walls fold up out of the plan (paper)", -12, 3.0),
            _bc(1.5, "the moon pops up", -14),
            _bc(2.5, "the street lamps come on", -18),
            _bc(3.0, "their steps along the curb", -18, 1.5),
            _bc(3.8, "iron scrape: he lifts manhole A", -8, 0.6),
            _bc(4.5, "clank: the lid set down on the road", -8),
            _bc(5.0, "iron rung: one goes down", -14), _bc(5.5, "iron rung: one goes down", -14),
            _bc(6.0, "iron rung: one goes down", -14),
            _bc(6.0, "the stopwatch starts: a tick on every beat", -14),
            _bc(6.0, "the sewer: drips, the channel trickling", -20, 6.0),
            _bc(7.0, "their steps in water", -16, 3.0),
            _bc(10.0, "up the iron rungs", -14, 0.8),
            _bc(11.0, "creak: the hatch opens", -10, 0.8)],
    "s05": [_bc(0.0, "the score drops to the tick", -14),
            _bc(0.25, "the guard's flashlight clicks on", -16),
            _bc(0.5, "the guard's slow steps along the corridor", -14, 3.5),
            _bc(6.0, "a piece crosses in the cone's shadow gap", -16), _bc(6.5, "a piece crosses the gap", -16),
            _bc(7.0, "a piece crosses the gap", -16),
            _bc(9.5, "clank: the stethoscope swings into a pipe (a ripple)", -6),
            _bc(10.0, "the guard spins; the cone swings at them", -12),
            _bc(11.0, "a cat leaps from a crate", -10),
            _bc(11.25, "a can rolls: clatter", -8),
            _bc(12.0, "the guard breathes out", -16),
            _bc(12.5, "the guard walks on; the crew slips through", -18, 1.5)],
    "s06": [_bc(0.5, "the Cracker kneels", -20),
            _bc(2.0, "the stethoscope set to the door (a soft metal tap)", -14),
            _bc(3.0, "the dial turns right (detent clicks)", -14, 1.8),
            _bc(5.0, "gate click, low; a ripple into his ear", -10),
            _bc(5.0, "the dial turns left", -14, 1.8),
            _bc(7.0, "gate click, mid; a ripple into his ear", -10),
            _bc(7.0, "the dial turns right", -14, 1.8),
            _bc(9.0, "gate click, high; a ripple into his ear", -10),
            _bc(9.5, "clunk: the fence drops", -8),
            _bc(10.0, "the bolts withdraw round the rim (a rolling metallic run)", -8, 1.0),
            _bc(11.0, "the door swings: a slow groan", -10, 3.0),
            _bc(11.0, "a brass swell; gold light floods out", -10, 3.0)],
    "s07": [_bc(0.5, "gold clinks: bars stacked", -14), _bc(1.0, "a bar into a bag", -14),
            _bc(1.75, "gold clinks: bars stacked", -14),
            _bc(2.0, "her deposit box opened (a small latch)", -14),
            _bc(2.5, "a tiny red glint", -16),
            _bc(3.0, "a bar into a bag", -14), _bc(3.5, "gold clinks", -14),
            _bc(4.0, "his red look from the bags to the open door", -14),
            _bc(6.0, "the X-split: the frame cut on both diagonals", -10),
            _bc(8.0, "he moves: the seams turn red", -14),
            _bc(10.0, "he swings the door shut: the groan", -8, 2.0),
            _bc(12.0, "BOOM: the vault door slams; black", -2),
            _bc(12.25, "the dial spins in red", -12, 0.4),
            _bc(12.6, "the bolts shoot home", -8),
            _bc(13.0, "his red route leaves the chalk route in an L", -14, 1.0),
            _bc(13.0, "the theme, inverted", -12),
            _bc(13.5, "the red knight hops along the L", -12), _bc(14.0, "the red knight hops", -12),
            _bc(14.5, "the red knight hops", -12),
            _bc(13.5, "the stopwatch stops dead", -14),
            _bc(14.5, "alarm bell: red ripples over the plan", -6, 1.5)],
    "s08": [_bc(0.0, "black: the Cracker's ragged breath", -14, 2.0),
            _bc(1.0, "a match strikes: spark, flare", -8),
            _bc(2.0, "he pounds the door: muffled thuds", -10), _bc(2.5, "a muffled thud", -10),
            _bc(3.0, "a muffled thud", -10), _bc(4.0, "a muffled thud", -11),
            _bc(4.5, "the corner of her mouth lifts (a calm note)", -18),
            _bc(6.0, "a hollow knock: her heel on the floor; a ripple through it", -6),
            _bc(6.5, "the chalk dot glows", -18),
            _bc(8.0, "she unrolls a translucent sheet: tracing paper", -10, 3.0)],
    "s09": [_bc(0.0, "the rewind: a tape-rewind whoosh, the stopwatch spinning back", -8, 3.0),
            _bc(2.5, "a ting: the callout lens snaps round the chalk dot", -10),
            _bc(3.0, "s02's elevation: his red look and her white look (the low held note)", -14, 2.0),
            _bc(4.0, "a ting: the callout on her eye", -12),
            _bc(5.0, "the tracing sheet slides over the plan", -10, 1.5),
            _bc(6.5, "chalk: the trapdoor square drawn", -12, 0.5),
            _bc(7.0, "chalk: her route north along the branch to manhole B (dotted)", -14, 1.5),
            _bc(8.5, "chalk: four police cars drawn round his car", -14, 1.0),
            _bc(9.5, "chalk: a red X on the ruby box", -10, 0.5),
            _bc(10.0, "the theme returns upright, in the major", -12),
            _bc(10.0, "the vault by the flame's light", -20, 2.0),
            _bc(11.0, "she lifts a floor tile (stone scrape)", -10),
            _bc(13.5, "they drop through to the sewer: splash", -8),
            _bc(14.0, "they walk north through the water", -16, 2.0)],
    "s10": [_bc(0.0, "the alarm bell ringing hard, high in the alley", -10, 1.46, 0.5),
            _bc(0.2, "heavy running footsteps on cobbles, coming in fast from the right", -10, 0.75, 0.5),
            _bc(0.95, "a grunt of effort", -14, pan=0.4),
            _bc(1.05, "a skidding stop", -12, pan=0.4),
            _bc(1.26, "two heavy sacks of gold thumped into the back seat: a dull clank", -8, pan=0.35),
            _bc(1.32, "a car door slammed hard", -6, pan=0.3),
            _bc(1.62, "a starter motor grinding, the engine coughing twice", -9, 0.4),
            _bc(2.02, "the headlight clicks on with a bright swell; the engine catches and roars", -7, 0.88),
            _bc(2.5, "tyres squealing as the car lurches off", -8),
            _bc(2.68, "a white whoosh", -12),
            _bc(3.15, "the engine racing away", -14, 0.8)]
           + [_bc(tc - 0.2, "a police car sliding in: a muted trumpet stab and a siren whoop", -7, pan=pn)
              for tc, pn in ((4.0, -0.5), (4.5, 0.5), (5.0, 0.3), (5.5, -0.3))]
           + [_bc(4.0, "sirens braiding together, rising", -13, 8.0),
              _bc(6.0, "checkmate: a hard low stab and a choked cymbal", -5),
              _bc(6.42, "a heartbeat thump; his breath catching", -10, 0.78),
              _bc(7.95, "an iron manhole cover dragged aside", -12, pan=-0.2),
              _bc(8.5, "two pairs of soft footsteps walking away on the cobbles", -17, 1.8, -0.3),
              _bc(10.0, "two long strokes of chalk swelling into a held chord", -10, 1.2),
              _bc(11.2, "the theme's last phrase, resolving", -12, 0.8)],
    "s11": [_bc(0.0, "whoosh: the frame splits open along the X (a paper rip) and the four pieces fly apart; "
                     "the sirens cut off", -8, 0.62),
            _bc(0.3, "a night street under a lamp: a low electric hum, a far drip", -24, 2.7),
            _bc(0.55, "leather creak: her gloved fingers open, one after another", -18, 0.75),
            _bc(1.5, "the ruby glints: one celesta ping", -10),
            _bc(2.45, "her fist closes on it: the glove creaks tight", -14, 0.3),
            _bc(3.0, "dawn at the table: quiet room tone, a bird far off", -24, 1.35),
            _bc(3.2, "cloth rustle: her sleeve brushes the paper as the queen comes in low", -22, 0.65, -0.3),
            _bc(3.85, "click: the queen's base knocks the knight's", -12, pan=0.1),
            _bc(4.0, "she tips the knight over: clack, roll (he rolls on the paper)", -8, 0.5, 0.2),
            _bc(4.35, "whoosh, soft and airy: the camera rises off the table", -24, 1.15),
            _bc(5.5, "whoosh: the chalk X lifts off the vault and grows into the title", -12, 0.5),
            _bc(6.0, "the title X lands: the last chord", -10),
            _bc(6.2, "paper whoosh: DOUBLE slides back in from the top", -16),
            _bc(6.45, "paper whoosh: CROSS slides back in from the bottom", -16),
            _bc(7.0, "chalk tap: the red dot lands at the crossing (the film's last tap)", -10),
            _bc(7.5, "black", -20)],
}


def silence_from():
    """Film time the sound must be gone: s11's black (its T_BLACK, scene time; the bible's 7.5)."""
    S = scene("s11") if "s11" in START else None
    tb = g(S, "T_BLACK", 7.5) if S is not None else 7.5
    return float(min(DUR, START.get("s11", DUR - 8.0) + float(np.clip(tb, 0.5, LENGTH.get("s11", 8.0)))))


# ============================================================================ spotting: a cue no section answered
CUE_TRIM = -2.0              # a cue's gain_db, as the scenes write it, to this mix's levels


FOLEY_HEAD = {"chalk", "tap", "taps", "tick", "ticks", "tock", "clack", "thud", "clunk", "whoosh", "knock", "scratch",
              "scratched", "boom", "click", "clicks", "ting", "swish", "stamp", "slam", "creak", "clank", "splash",
              "iron", "gate", "alarm", "cloth", "rustle"}
PIECES = ("knight", "piece", "pawn", "queen", "bishop", "rook")


def realize(m, c):
    """Realise a cue no section answered, from its words, at its time, in its scene's room. A cue
    leads with its sound ('chalk tap: the arrow lands on the X'): the words before the colon are
    read first. Returns how (or why not)."""
    s = c["sfx"].lower()
    t = float(c["t"])
    g0 = float(c.get("gain_db", -12.0)) + CUE_TRIM
    pan = float(c.get("pan", 0.0))
    d = float(c["dur"]) if c.get("dur") else None
    lab = "auto: " + c["sfx"]
    seed = int(round(t * 100)) % 997
    words = set(re.findall(r"[a-z]+", s))
    hw = set(re.findall(r"[a-z]+", s.split(":")[0]))

    def has(*w):
        return any(x in s for x in w)

    def word(*w):
        return any(x in words for x in w)

    def put(x, gain=0.0, bus="efx", at=None, align="onset", sync=None, room_=True, key=False, wet=None, label=True):
        tt = t if at is None else at
        y = roomed(m, x, tt, seed, wet) if room_ else x
        m.put(bus, y, tt, g0 + gain, pan=pan, label=lab if label else None, align=align, sync=sync, key=key)

    # silences and the clock: nothing to add
    if has("silence", "drops to the tick", "music drops", "score drops", "music stops") or s.strip(" .") == "black":
        m.mark(t, lab)
        return "silence (nothing to add)"
    if (has("stopwatch", "the clock", "heist clock", "woodblock tick") and not word("rewind", "rewinds", "back")
            and not has("pop-up", "stands up")):
        m.mark(t, lab)
        return "the clock (on the tick bus)"
    head = s.split(":")[0] if ":" in s else ""
    hd = set(re.findall(r"[a-z]+", head))

    def who_of():
        return ("guard" if has("guard") else "her" if word("her", "she", "architect") else
                "knight" if has("knight", "heavy") else "cracker" if has("cracker", "old man", "shuffl", "creep") else
                "her")

    # sounds the scenes name in so many words (ahead of the broader rules below)
    if (word("rip", "rips", "ripped", "tear", "tears", "torn", "tearing") and word("frame", "paper")
            and not word("tape", "chalk")):
        dd = d or 0.6
        put(paper_torn(round(min(max(dd, 0.3), 0.6), 2), seed % 5), align=None)
        if word("whoosh", "whooshes", "fly", "flies", "flying", "apart"):
            for k, pn in enumerate((-0.5, 0.5)):
                m.put("efx", paper_whoosh(round(max(0.3, dd), 2), seed % 5 + k), t + 0.05 + 0.04 * k, g0 - 8.0, pan=pn,
                      align=None)
            return "auto: a paper rip (the pieces whoosh apart)"
        return "auto: a paper rip"
    if has("room tone", "quiet room") or word("bird", "birds", "birdsong"):
        dd = round(max(1.0, d or 2.0), 2)
        tone = has("room tone", "quiet room")
        if tone:
            m.put("amb", bed("room_tone", dd, seed % 5, fin=0.05, fout=0.2), t, g0 - 9.0, label=lab, align=None)
        if word("bird", "birds", "birdsong"):
            m.put("amb", bird_far(seed % 4), t + 0.15, g0 - 9.0, pan=0.5, label=None if tone else lab, align=None)
            return "auto: room tone, a bird far off" if tone else "auto: a bird far off"
        return "auto: room tone"
    if has("paper fold", "paper unfold") or (word("fold", "folds", "unfold", "unfolds") and word("whoosh")):
        put(paper_whoosh(round(max(0.3, d or 1.0), 2), seed % 5), align=None, room_=False)
        if has("stands up", "stand up"):
            put(popup(seed % 6), at=t + max(0.2, (d or 1.0) - 0.12), gain=-10.0, label=False, wet=-20.0)
        return "auto: a paper fold (a soft whoosh)"
    if has("chest-piece", "chest piece") and not word("clank", "swings", "pipe"):
        if word("coat", "drops", "dropped", "falls"):
            put(coat_tap(seed % 3))
            return "auto: the chest-piece taps his coat"
        put(metal_tap(seed % 3))
        return "auto: the chest-piece on the steel (a tiny tock)"
    if word("knob", "knurled") and not word("spins", "spin", "turns"):
        put(knob_tick(seed % 3))
        return "auto: a faint tick on the knob"
    if word("dial") and word("spins", "spin", "spun", "turns", "turned", "ratchet") and not word("red"):
        dd = round(min(max(d or 1.0, 0.3), 3.0), 2)
        if has("slowing", "creep", "fast run", "spins"):
            put(dial_spin(dd, seed % 3), align=None)
            return "auto: the dial spun (ticks slowing)"
        put(dial_ratchet(dd, seed % 3, 40.0 if word("fine") else 32.0 if has("spin") else 16.0), align=None)
        return "auto: the dial turns"
    if word("stethoscope"):
        if has("set to", "against the door", "on the door", "to the door", "touches", "steel door"):
            put(metal_tap(seed % 3))
            return "auto: the stethoscope against the door"
        put(steth_clank(seed % 3))
        put(ripple(seed % 3, 90.0, 0.9), at=t + 0.02, gain=-12.0, room_=False, label=False)
        return "auto: the stethoscope's clank"
    if word("fence") and (word("drops", "drop", "dropped") or hd & {"clunk"}):
        put(fence_clunk(seed % 2))
        return "auto: the fence clunks"
    if word("bolt", "bolts") and not hd & {"clunk"}:
        if has("one clack", "a heavy steel bolt", "withdraws from"):
            put(bolt_one(seed % 12), at=t - BOLT_PRE, sync=t, align="peak")
            return "auto: one bolt (a clack)"
        if has("draws back", "slide", "slides") and not word("home", "shoot", "shot"):
            put(bolt_slide(round(min(max(d or 0.35, 0.15), 0.8), 2), seed % 3), align=None)
            return "auto: the bolt slides back"
    if word("wheel") and word("ratchet", "turns", "turned"):
        dd = round(min(max(d or 0.7, 0.3), 2.0), 2)
        put(pitch(dial_ratchet(dd, seed % 3, 9.0), -12.0), align=None)
        return "auto: the great wheel's ratchet"
    if has("door settles", "settles against", "against its stop"):
        put(door_thud(seed % 2))
        return "auto: the door settles (a deep thud)"
    if word("tin") or hd & {"clatter", "tink"}:
        if word("tink", "tips", "tip") and not word("clatter"):
            put(tin_tink(seed % 3))
            return "auto: a tin tink"
        put(cut(can_clatter(seed % 3), 1.7, 0.5))
        return "auto: a can clatters"
    if word("hiss") and word("cat", "cats"):
        put(cat_hiss(seed % 3), bus="vox", align=None)
        return "auto: a cat's hiss"
    if word("claws", "scrabble", "scrabbles"):
        put(claws(seed % 3), align=None)
        return "auto: claws scrabble"
    if word("leather", "belt") and word("creak", "creaks"):
        dd = d or 0.4
        for k in range(max(1, int(round(dd))) if has("repeats") else 1):
            put(glove_creak((seed + k) % 3, 0.35), at=t + k, gain=-2.0 * k, align=None, label=k == 0)
        return "auto: leather creaks"
    if has("pop-up snap", "pops up", "stands up") and not has("chalk"):
        put(popup(seed % 6), wet=-20.0)
        return "auto: a paper pop-up snap"
    if (head.strip(" .") in ("footstep", "a footstep", "step", "a step") or head.strip(" .").endswith(" step")
            or has("a footstep in", "a single step", "a soft step", "a step on", "one step")):
        if has("water", "slosh", "puddle", "wade"):
            put(water_step(seed % 8, 0.75 if has("heav") else 0.55), bus="feet", room_=False)
            return "auto: a footstep in water"
        who = who_of()
        if word("steel", "plated", "plate"):
            m.put("feet", steel_step(who, seed % 7, room(m, t)[0], seed), t - STEP_PRE, g0, pan=pan, label=lab, sync=t)
            return f"auto: a step on steel ({who})"
        m.put("feet", footstep(who, seed % 7, room(m, t)[0], seed=seed % 5), t - STEP_PRE, g0, pan=pan, label=lab,
              sync=t)
        return f"auto: a footstep ({who})"
    if (hd & {"scuff", "scuffs", "scuffed", "scuffing"} or (word("heel", "heels") and word("pivots", "pivot", "swivels"))
            or (word("scuffs", "scuffing") and not word("yelp", "yelps", "gasp", "stumbles"))):
        who = who_of()
        m.put("feet", roomed(m, heel_scuff(seed % 4, who), t, seed), t - STEP_PRE, g0, pan=pan, label=lab, sync=t)
        return f"auto: a heel scuffs ({who})"
    if word("ladder") and has("slid", "sliding", "slides"):
        dd = round(min(max(d or 0.6, 0.3), 1.5), 2)
        put(ladder_slide(dd, seed % 5, 0.9 if has("heav") else 0.4), align=None)
        return "auto: a slide down the iron ladder"
    if word("rung", "rungs"):
        if has("first", "a shoe on", "a foot on") and not d:
            put(rung(seed % 6))
            m.put("feet", footstep(who_of(), seed % 7, room(m, t)[0], seed=seed % 5), t + 0.02 - STEP_PRE, g0 - 8.0,
                  pan=pan)
            return "auto: a shoe on a rung"
        gap = 0.25 if has("quick", "fast", "light") else 0.5
        lo = word("low")
        for k in range(max(1, int(round((d or 0.5) / gap)))):
            x = rung((seed + k) % 6)
            put(dsp.sos(x, "lowpass", 2500.0, 2) if lo else x, at=t + gap * k, gain=-6.0 if lo else -2.0, label=k == 0)
        return "auto: iron rungs"
    if word("iron", "steel") and word("tick", "ticks"):
        put(metal_tap(seed % 3))
        if word("grunt", "grunts"):
            put(grunt(seed % 3), bus="vox", at=t + 0.05, gain=-5.0, align=None, label=False, key=True)
        return "auto: an iron tick"
    if word("chuckle", "chuckles", "laugh", "laughs", "snigger") and not word("breath", "breathes", "sigh"):
        put(chuckle(seed % 3), bus="vox", align=None, key=True)
        return "auto: a low chuckle"
    if word("grunt", "grunts"):
        put(grunt(seed % 3), bus="vox", align=None, key=True)
        return "auto: a grunt"
    if hd & {"coat", "cloth", "sleeve"} or ((hd & {"rustle", "rustles"} or has("coat rustles", "coat flaps"))
                                            and not has("paper")):
        put(cloth(round(d or 0.45, 2), seed % 5, heavy=1.0 if has("heavy", "coat") else 0.0), align=None)
        return "auto: cloth"
    if hd & {"whoosh"} and word("low", "sinks", "sink", "sinking", "descends"):
        if word("rising", "rises", "pushes", "push"):
            put(rise_whoosh(round(max(0.4, d or 1.0), 2), seed % 3), align=None, room_=False)
            return "auto: a low whoosh (rising)"
        put(sink_whoosh(round(max(0.4, d or 1.2), 2), seed % 3), align=None, room_=False)
        return "auto: a low whoosh (sinking)"
    if hd & {"whoosh", "whooshes"} and not has("whoosh-thud", "whoosh thud", "tape", "paper whoosh"):
        dd = round(max(0.3, min(d or 0.5, 1.5)), 2)
        if word("soft", "airy", "air", "rises", "rising", "camera"):
            put(air_swell(dd, seed % 5), align=None, room_=False)
            return "auto: an airy whoosh"
        put(paper_whoosh(dd, seed % 5), align=None, room_=False)
        return "auto: a whoosh (paper)"
    if has("paper whoosh"):
        dd = d or 1.0
        if has("rising", "rises", "tilts") and not has("carries on", "carries into"):
            put(paper_rise(round(d or 1.6, 2), seed % 3), align=None, room_=False)
            return "auto: a rising paper whoosh"
        put(paper_carry(round(dd, 2), seed % 3) if dd > 1.2 else paper_whoosh(round(max(0.3, dd), 2), seed % 5),
            align=None, room_=False)
        return "auto: a paper whoosh"
    if has(*PIECES) and has("sink", "soft paper slides", "slide into"):
        n = 4 if has("four") else 3 if has("three") else 2 if has("two") else 1
        for k in range(n):
            put(paper_whoosh(0.3, (seed + k) % 5), at=t + 0.1 * k, gain=-4.0 - 0.5 * k, align=None, label=k == 0)
        return "auto: pieces sink into the paper (soft slides)"
    if word("lamp", "lamps") and has("clicks off", "click off", "goes out", "switched off", "turns off", "lamp off"):
        put(switch_click(seed % 5, 0.7))
        if has("night air", "city", "wind"):
            dd = d or 4.0
            na = night_air(round(dd, 2), seed % 3)
            u = tax(len(na))
            put(na * (np.clip(u / 1.2, 0, 1) * np.clip((dd - u) / 1.0, 0, 1))[:, None], bus="amb", gain=-10.0,
                room_=False, align=None, label=False)
        return "auto: a lamp clicks off (night air)"
    if word("freeze", "freezes") or has("tape pause"):
        put(switch_click(5, 1.3), gain=-4.0)
        return "auto: a tape pause (a click)"
    if word("click", "clicks") and word("tape") and has("catches", "plays") and not has("rewind", "spools"):
        put(switch_click(2, 0.5))
        return "auto: the tape catches (a click)"
    if has("chalk slash"):
        for j in range(2):
            put(chalk_scratch(0.09, (seed + j) % 7, press=1.0), at=t + 0.1 * j, align=None, label=j == 0)
        if has("low stab", "a stab"):
            hit(m, t, 45, 0.7, gain=g0 - 4.0)
        return "auto: chalk slashes (and a low stab)"
    if word("skid", "skids", "skidding"):
        put(skid_stop(seed % 3), bus="feet", align=None)
        return "auto: a skidding stop"
    if word("sack", "sacks") or (word("bag", "bags") and word("gold", "heavy", "two")):
        for k in range(2 if has("two", "both", "sacks", "bags") else 1):
            put(gold_bag((seed + k) % 5), at=t + 0.03 * k, gain=-2.0 * k, label=k == 0)
        return "auto: sacks of gold"
    if word("heartbeat", "heart"):
        put(fx("heartbeat", dur=round(max(0.6, d or 1.0), 2), seed=seed % 3, bpm=118), room_=False, align=None)
        if word("breath"):
            put(breath("in"), bus="vox", at=t + 0.08, gain=-6.0, align=None, label=False, key=True)
        return "auto: a heartbeat"
    if has("racing away", "drives off", "speeds away", "pulls away", "roars away", "drives away"):
        put(fx("car_away", dur=max(1.2, (d or 1.0) + 0.8), seed=seed % 3), align=None, wet=-16.0)
        return "auto: a car racing away"
    if word("squeal", "squealing", "screech", "screeching", "screeches"):
        brake = word("brakes", "brake", "stop", "stops")
        put(tyre_squeal(round(max(0.3, min(d or 0.45, 1.0)), 2), seed % 3, 2300.0 if brake else 1900.0,
                        0.25 if brake else 0.12), align=None)
        return "auto: tyres squeal"
    if word("headlight", "headlights") and has("click", "flare", "flares", "on"):
        put(switch_click(seed % 5, 0.6))
        put(light_swell(0.6, seed % 3), gain=-6.0, align=None, room_=False, label=False)
        if word("engine") and has("catches", "roars"):
            put(getaway_start(seed % 3, (), 0.0, 0.5, 0.9), at=t, gain=-2.0, align=None, label=False)
        return "auto: a headlight flares (the engine catches)"
    if word("chime", "chimes"):
        notes = (86, 90, 93, 98) if has("rising", "rises", "climb") else (93,)
        dd = d or 0.6
        for j, p in enumerate(notes):
            put(ting((seed + j) % 4, p) * (0.95 - 0.1 * j), bus="music", at=t + j * dd / len(notes), gain=-2.0 - 0.5 * j,
                room_=False, label=j == 0)
        return "auto: a rising chime (tings)" if len(notes) > 1 else "auto: a chime"
    # the score (unless the cue leads with a sound of its own: 'chalk tap: ... an accent in the score')
    if not hw & FOLEY_HEAD and has("theme", "phrase", "the score", "music", "inverted", "inversion", "in the major",
                                    "upright", "chord", "calm note"):
        if m.music_at(t):
            m.mark(t, lab)
            return "auto: the score plays here"
        if has("rising chord", "gathers", "held chord", "last chord", "lands on", "resolves"):
            sym = "D69" if has("major", "last chord", "resolves") else "Dm9"
            vibe_chord(m, t, CHORDS[sym][1], d or 2.0, gain=g0 - 2.0, vel=0.55, seed=seed, label=lab)
            put(arco(38, d or 2.0, 0.6, seed=seed), bus="music", gain=-4.0, room_=False, align=None, label=False)
            return f"auto: a held chord ({sym})"
        if has("single", "one low", "a note") and not has("theme"):
            p = 56 if has("low") else 63
            put(brass(p, 1.1, 0.5, seed=seed, mute="harmon", scoop=False, vib=False), bus="music", room_=False,
                align=None)
            return "auto: a single muted note"
        notes = INVERSION if has("invert") else THEME_MAJOR if has("major", "upright", "resolv") else THEME
        if has("last phrase", "resolving", "resolves", "last bar"):
            melody(m, t - sw(12), notes, gain=g0 - 1.0, start=12, label=lab, seed=seed)
            return "auto: the theme's last phrase (vibraphone)"
        melody(m, t, notes, gain=g0 - 1.0, stop=2 if has("two notes", "calm note") else 4, label=lab, seed=seed)
        return "auto: the theme's head (vibraphone)"
    if word("celesta"):
        put(celesta(93, 0.8, seed), bus="music", room_=False)
        return "auto: celesta"
    if word("checkmate") and word("stab", "stabs", "cymbal"):
        stab(m, t, "DmM7", gain=g0, dur=0.5, vel=1.0, seed=seed, label=lab)
        hit(m, t, 38, 0.9, gain=g0 - 2.0)
        m.put("music", choked(crash(seed % 5, 1.0), 0.2) if has("choked") else crash(seed % 5, 2.4), t, g0 - 8.0,
              hall=-18.0)
        return "auto: checkmate (a low stab, a cymbal)"
    if word("stab", "stabs") and (hd & {"stab", "stabs"} or not word("police", "rook")):
        muted = word("muted")
        stab(m, t, "C7" if word("police") else "DmM7", gain=g0, dur=0.18 if muted else 0.22, seed=seed, label=lab,
             low=not muted)
        return "auto: trumpet stab"
    if word("swell", "riser") and word("brass"):
        brass_swell(m, t, "Bbmaj7", d or 3.0, gain=g0, seed=seed, label=lab)
        return "auto: a brass swell"
    if word("swell", "riser"):
        put(cym_swell(round(d or 1.5, 2), seed), bus="music", room_=False, align=None)
        return "auto: cymbal swell"
    if has("held note", "low note", "low held", "drone", "pedal note"):
        put(arco(38, d or 2.0, 0.7, seed=seed), bus="music", room_=False, align=None)
        return "auto: a low held D (arco)"
    if word("piano") and word("note", "notes", "chord"):
        put(piano(38, d or 3.0, 0.55, seed % 5), bus="music", room_=False)
        return "auto: a low piano note"
    if (word("trumpet") or has("muted note", "semitone")) and not word("police", "rook"):
        put(brass(63 if has("semitone") else 57, 0.8, 0.6, seed=seed, mute="harmon"), bus="music", room_=False)
        return "auto: a muted trumpet note"
    if word("ting", "glint", "glints", "spectacles", "callout") or (word("glows", "glow") and word("dot")):
        put(ting(seed % 4, 86 if word("dot") else 93), bus="music", room_=False)
        return "auto: ting"
    # small sounds named outright
    if word("tock", "tocks"):
        if word("chalk"):
            put(pitch(chalk_tap(seed % 7, 0.95), -4))
            return "auto: a chalk tock"
        put(tock(seed % 3), wet=-16.0)
        return "auto: a low wooden tock"
    if word("heel") and word("tap", "taps", "click", "clicks"):
        put(heel_tap(seed % 3))
        return "auto: a heel tap on steel"
    if word("shuffle", "shuffles"):
        put(shuffle(seed % 3), align=None)
        return "auto: a shuffle"
    if hw & {"thud", "thuds", "thump"} and not hw & {"chalk", "tap", "whoosh"} and not has("fist", "muffled"):
        if has(*PIECES):
            put(piece_slam(seed % 3), room_=False)
            return "auto: a piece slammed down"
        if has("hatch", "trapdoor", "lid", "door", "crate"):
            put(wood_thunk(seed % 3, 0.8))
            return "auto: a wooden thud"
        put(strip_thud(seed % 4))
        return "auto: a thud"
    if has("breath", "breathes", "exhale", "pant", "gasp", "sigh", "inhale") and not word("fist", "pound", "boom", "hinge",
                                                                                             "clunk"):
        kind = ("ragged" if has("ragged", "pant") else "gasp" if has("gasp", "catches", "catch") else
                "out" if has(" out", "exhale", "sigh") else "in" if has("inhale", "sharp") else "held")
        x = breath(kind)
        if d:
            x = dsp.fade(mono(x)[:n_of(d + 0.3)], 0.02, 0.2)
        put(x, bus="vox", align=None, key=True)
        if word("alarm"):
            ad = (d or 1.4) + 0.2
            al = dsp.sos(alarm_bell(round(ad + 0.2, 2), seed % 3), "lowpass", 600.0, 2)[:n_of(ad)]
            put(al * np.linspace(1.0, 0.0, n_of(ad)) ** 1.6, bus="amb", gain=-12.0, room_=False, align=None, label=False)
        if word("cloth"):
            put(cloth(0.45, seed % 5, heavy=0.8), at=t + 0.05, gain=-4.0, align=None, label=False)
        return f"auto: breath ({kind})"
    if word("chain"):
        put(chain_creak(round(d or 2.0, 2), seed % 3), align=None)
        return "auto: a chain creaks"
    if word("lamp", "lamps"):
        dd = d or 1.5
        on = has("clicks on", "click", "switch", "comes on", "come on", "lights up", "lit")
        if on:
            put(switch_click(seed % 5, 0.8))
        m.put("amb", lamp_hum(START[m.sid] + t, dd) * np.clip(tax(n_of(dd)) / 0.4, 0, 1), t, -44.0,
              label=None if on else lab, align=None)
        if word("drip", "drips"):
            m.put("amb", far_drip(seed % 4), t + min(0.6, dd / 3.0), g0 - 10.0, pan=-0.4)
        return "auto: a lamp clicks on (a hum)" if on else "auto: a lamp's hum"
    if word("match", "strike", "strikes"):
        if has("hiss") and not word("strike", "strikes", "struck", "scratch", "scratched"):
            put(flame_bed(round(d or 2.0, 2), seed % 3), bus="amb", gain=-8.0, room_=False, align=None)
            return "auto: the match's hiss (a flame)"
        if has("no flame", "sparks") and not word("flare", "flares"):
            x = match_scratch(seed % 3)
            put(x, at=t - onset_at(x), sync=t)
            return "auto: a match scratched (sparks)"
        st = fx("match_strike", seed=307)
        put(st, at=t - onset_at(st), sync=t)
        put(fx("match_flare", seed=seed % 3), at=t + 0.08, gain=-5.0, align=None, label=False)
        return "auto: a match strikes"
    # the title, the table, the paper
    if has("whoosh-thud", "whoosh thud") or word("strip", "strips"):
        put(whoosh_thud(0.24, seed % 3, 0.6 if has("heav") else 0.0), at=t - 0.24, sync=t)
        return "auto: whoosh-thud"
    if word("stamp", "stamps", "stamped"):
        put(stamp(seed % 2))
        return "auto: stamp"
    if word("tracing"):
        put(tracing_slide(round(d or 2.0, 2), seed % 3), align=None, room_=False)
        return "auto: tracing paper"
    if has("unroll", "blueprint"):
        put(paper_unroll(round(d or 2.0, 2), seed % 3), align=None, room_=False)
        return "auto: paper unrolls"
    if has("pop-up", "pops", "fold") or word("pop", "popup"):
        if not has("chalk"):
            for k in range(max(1, int(round((d or 0.5) / 0.5)))):
                put(popup((seed + k) % 6), at=t + 0.5 * k, label=k == 0)
            return "auto: paper pops"
    if word("paper", "sheet", "roll", "scroll") and not has("chalk", *PIECES):
        if word("torn", "tear", "tears", "tearing", "rip", "rips", "ripped"):
            dd = d or 0.55
            put(paper_tear_run(round(dd, 2), seed % 5) if dd > 0.9 else paper_torn(round(dd, 2), seed % 5), align=None,
                room_=False)
            return "auto: paper torn"
        if has("rising", "rises", "tilt"):
            put(paper_rise(round(d or 1.6, 2), seed % 3), align=None, room_=False)
            return "auto: a rising paper whoosh"
        if has("drawn down", "down fast", "whoosh", "swish", "lifted", "lifts", "lift"):
            put(paper_whoosh(round(max(0.3, d or 0.6), 2), seed % 5), align=None)
            return "auto: a paper swish"
        put(cut(mono(fx("paper_rustle", seed=seed % 5)), round(min(max(d or 0.6, 0.3), 0.9), 2), 0.12), align=None)
        return "auto: paper rustle"
    # the chalk
    if has("chalk", "ruled", "sketch") or word("route", "routes") or (word("dot") and word("tap", "tick")) or (
            word("drawn", "draws", "draw") and not word("cigarette", "breath", "paper", "match", "smoke", "sword", "bolt",
                                                           "bolts", "back", "curtain", "gun")):
        dd = d or 0.4
        if has("dry run") or word("dots", "dotting", "dotted"):
            dd = d or 1.0
            put(chalk_dots(max(3, int(round(dd * 8))), round(dd, 2), seed % 5, 0.4), align=None)
            return "auto: chalk dots (a route)"
        if hw & {"tap", "taps", "tick", "ticks", "dab"} or word("tap", "taps", "tick", "dab"):
            soft = has("soft", "tiny", "buried")
            put(chalk_tap(seed % 7, 0.3 if soft else 0.7), gain=-2.0 if soft else 0.0)
            if word("circle"):
                put(chalk_scratch(0.3, (seed + 1) % 7, circle=True), at=t + 0.12, gain=-4.0, align=None, label=False)
            if has("accent in the score", "bright accent"):
                vibe_chord(m, t, (81, 86, 88), 1.2, gain=g0 - 3.0, vel=0.7, roll=0.0, hard=0.85, depth=0.3, seed=seed)
            return "auto: chalk tap"
        if word("circle", "circles", "circling", "ring", "arc", "wheel", "loop", "round", "bell") or (
                word("dial") and not word("lens")):
            put(chalk_scratch(round(dd, 2), seed % 7, circle=True), align=None)
            if word("ticks"):
                for k in range(4):
                    put(chalk_tap((seed + k) % 7, 0.25), at=t + dd * (k + 0.5) / 4, gain=-6.0, label=False)
            return "auto: chalk circle"
        if has("held chord", "swelling into", "swells into"):
            dd = d or 1.2
            for j in range(2 if has("two") else 1):
                put(chalk_scratch(round(dd, 2), (seed + j) % 7, press=0.8), align=None, label=j == 0)
            vibe_chord(m, t, CHORDS["A13"][1], dd + 0.25, gain=g0 - 6.0, vel=0.5, seed=seed)
            put(arco(33, round(dd + 0.3, 2), 0.6, seed=seed, attack=0.4, release=0.3), bus="music", gain=-6.0,
                room_=False, align=None, label=False)
            return "auto: chalk strokes swelling into a held chord"
        if word("route", "routes", "path", "line", "lines", "branch") and not word("x"):
            dd = d or 1.0
            put(chalk_dots(max(3, int(round(dd * 8))), round(dd, 2), seed % 5, 0.4), align=None)
            return "auto: chalk dots (a route)"
        if word("tap", "dab", "tick", "dot"):
            put(chalk_tap(seed % 7, 0.6))
            return "auto: chalk tap"
        if word("x"):
            put(chalk_scratch(round(dd / 2, 2), seed % 7), align=None)
            put(chalk_scratch(round(dd / 2, 2), seed % 7 + 1), at=t + dd / 2, label=False, align=None)
            return "auto: a chalk X"
        put(chalk_scratch(round(dd, 2), seed % 7), align=None)
        return "auto: chalk scratch"
    # the pieces
    if word("slam", "slams", "slammed") and has(*PIECES):
        put(piece_slam(seed % 3), room_=False)
        return "auto: a piece slammed down"
    if word("snatched", "snatches", "snatch", "scrape", "scrapes", "scraped") and has(*PIECES):
        put(piece_scrape(seed % 3, round(min(d or 0.3, 0.8), 2)), align=None)
        return "auto: a piece scraped up"
    if has("tip", "topple") and has(*PIECES):
        put(piece_tip(seed % 3))
        return "auto: a piece tipped over"
    if word("clack", "hop", "hops", "hopping", "queen", "bishop", "pawn", "piece", "pieces") or has("knight set"):
        heavy = 0.8 if has("knight", "pawn") else 0.4
        mm = re.search(r"(\d+)\s+(?:chess )?pieces?", s)
        n = int(mm.group(1)) if mm else (3 if word("pieces") else 1)
        for k in range(min(n, 3)):
            put(piece_clack((seed + k) % 9, heavy), at=t + (0.0, 0.012, -0.009)[k], room_=False, label=k == 0,
                gain=-4.0 - 2.5 * k)
        return "auto: piece clack"
    # street, sewer, bank
    if word("manhole", "lid", "cover") and not word("pot", "book"):
        far = -8.0 if has("far", "blocks") else 0.0
        if has("scrape", "lift", "slide", "open", "dragged", "drag", "aside", "levered"):
            put(manhole_scrape(round(max(0.3, d or 0.6), 2), seed % 3), gain=far, align=None)
            if not m.cue_near(t + 0.6, "clank", win=0.8) and not has("dragged", "aside", "slides off"):
                put(manhole_clank(seed % 3), at=t + 0.7, gain=far - 1.0, label=False)
                return "auto: a manhole lifted (scrape, clank)"
            return "auto: a manhole lid scraped (no clank of its own)"
        put(manhole_clank(seed % 3), gain=far)
        return "auto: a manhole clank"
    if word("tile") or (word("stone", "slab") and has("lifted", "prised", "levered", "out of the floor")):
        if has("laid", "set down", "put down", "clunk"):
            put(tile_set(seed % 3))
            return "auto: a stone tile laid down"
        if has("scraped up", "scrapes up", "prised"):
            put(tile_scrape(seed % 3), align=None)
            return "auto: a stone tile scraped up"
        put(tile_lift(seed % 3))
        return "auto: a stone tile lifted"
    if word("scrape") and word("iron"):
        put(manhole_scrape(0.6, seed % 3), align=None)
        return "auto: iron scrape"
    if word("drip", "drips", "dripping") and not has("sewer", "tunnel", "channel"):
        put(drip(seed % 5), room_=False)
        return "auto: drip"
    if word("splash", "splashes") or has("drop through", "drops through", "drop into"):
        if has("steps off", "step off", "steps into", "steps down into"):
            put(water_step(seed % 8, 0.95), bus="feet", room_=False)
            return "auto: a heavy step into the water"
        put(splash_drop(seed % 3), room_=False)
        return "auto: splash"
    if word("water", "wade", "wading", "puddle"):
        water_steps(m, t, t + (d or 1.0), 0.5, gain=g0 - 2.0, label=lab, k0=seed % 5)
        return "auto: steps in water"
    if word("sewer", "tunnel", "channel") or has("trickl"):
        put(sewer_bed(round(d or 4.0, 2), seed % 3), bus="amb", gain=-16.0, room_=False, align=None)
        return "auto: the sewer (a bed)"
    if word("rung", "rungs", "ladder"):
        for k in range(max(1, int(round((d or 0.5) / 0.5)))):
            put(rung((seed + k) % 6), at=t + 0.5 * k, label=k == 0)
        return "auto: iron rungs"
    if word("hatch", "trapdoor"):
        put(hatch_creak(round(d or 0.8, 2), seed % 3), align=None)
        return "auto: the hatch creaks"
    if word("flashlight", "torch"):
        put(flashlight_click(seed % 3))
        return "auto: flashlight click"
    if word("stethoscope"):
        if has("door", "set to", "against"):
            put(metal_tap(seed % 3))
            return "auto: the stethoscope against the door"
        put(steth_clank(seed % 3))
        return "auto: the stethoscope's clank"
    if word("pipe", "pipes") or (word("clank") and not has("lid", "manhole")):
        put(steth_clank(seed % 3))
        return "auto: a clank on a pipe"
    if word("cat", "cats", "yowl", "meow"):
        put(cat_yowl(seed % 3), bus="vox", align=None)
        put(paws(seed % 3), at=t + 0.45, gain=-6.0, label=False)
        return "auto: a cat"
    if word("can", "clatter", "clatters"):
        put(can_clatter(seed % 3))
        return "auto: a can clatters"
    if word("gate", "gates"):
        k = 0 if has("low") else 2 if has("high") else 1
        put(gate_click(k, seed % 2))
        return f"auto: gate click ({('low', 'mid', 'high')[k]})"
    if word("dial", "ratchet") or (has("spins", "turns right", "turns left") and has("dial")):
        rate = 40.0 if word("fine") else 32.0 if has("spin") else 16.0
        put(dial_ratchet(round(min(d or 1.2, 3.0), 2), seed % 3, rate), align=None)
        return "auto: the dial turns"
    if word("fence", "clunk"):
        put(fence_clunk(seed % 2))
        if has("door", "swing", "hinge"):
            put(vault_groan(1.2, seed % 3), at=t + 0.08, gain=-12.0, align=None, label=False)
        return "auto: the fence clunks"
    if word("bolt", "bolts"):
        home = has("home", "shoot", "shot", "back")
        put(bolt_run(10, round(min(d or (0.4 if home else 0.9), 1.6), 2), seed % 3, home=home),
            align="onset" if home else None)
        return "auto: the bolts"
    if (word("fist", "fists") and has("door", "boom")) or word("pound", "pounds", "pounding", "bangs") or (
            word("muffled") and word("thud", "thuds", "boom", "booms")):
        for k in range(max(1, int(round((d or 0.5) / 0.5)))):
            put(pound((seed + k) % 4), at=t + 0.5 * k, room_=False, label=k == 0)
        return "auto: muffled pounding"
    if word("boom") or (has("slams shut", "door slams") and not word("car")):
        put(vault_boom(seed % 2), room_=False)
        return "auto: BOOM"
    if word("groan", "groans") or has("vault door", "door swings", "swings shut", "door shut"):
        put(vault_groan(round(d or 2.5, 2), seed % 3), align=None)
        return "auto: the vault door groans"
    if word("deposit", "box", "latch"):
        put(deposit_box(seed % 2))
        return "auto: a small latch"
    if word("bag", "bags") and not word("look"):
        put(gold_bag(seed % 5))
        return "auto: a bar into a bag"
    if word("gold", "bar", "bars", "clink", "clinks", "ingot"):
        put(gold_clink(seed % 5))
        return "auto: gold clink"
    if word("alarm"):
        put(alarm_bell(round(d or 1.5, 2), seed % 3))
        return "auto: alarm bell"
    if word("flame", "flare", "flares", "candle") and not word("headlights", "headlight"):
        put(flame_bed(round(d or 2.0, 2), seed % 3), bus="amb", gain=-8.0, room_=False, align=None)
        return "auto: a flame"
    if word("hollow", "knock", "knocks"):
        put(hollow_knock(seed % 2), room_=False)
        put(ripple(seed % 3, 62.0, 1.4), at=t + 0.03, gain=-10.0, room_=False, label=False)
        return "auto: a hollow knock"
    if word("rewind", "tape"):
        put(rewind_scrub(round(d or 2.0, 2), seed % 2), align=None, room_=False)
        return "auto: tape rewind"
    if word("glove", "fist"):
        put(glove_creak(seed % 3, 0.4), align=None)
        return "auto: a glove creaks"
    # the cars, the police
    if word("engine", "ignition", "coughs", "cough"):
        put(engine_start(seed % 3, round(max(1.0, d or 2.0), 2)), at=t - 0.77, sync=t, align=None, wet=-16.0)
        return "auto: the engine starts"
    if has("car door") or (word("door") and word("car")):
        put(fx("car_door_close", seed=seed % 3))
        return "auto: a car door"
    if word("headlights", "headlight"):
        put(switch_click(seed % 5, 0.6))
        return "auto: headlights"
    if word("siren", "sirens") and not word("whoop", "police"):
        dd = d or 4.0
        put(sirens(dd, seed % 3) * np.clip((dd - tax(n_of(dd))) / 1.0, 0, 1)[:, None], align=None, wet=-14.0)
        return "auto: sirens (tuned)"
    if word("police", "rook", "rooks"):
        stab(m, t, "C7", gain=g0, dur=0.22, seed=seed, label=lab, low=not word("muted"))
        put(car_slide(seed % 4, 0.45), at=t - 0.4, gain=-8.0, align=None, label=False)
        if word("whoop", "siren"):
            put(police_whoop(seed % 4, hz(74)), at=t + 0.02, gain=-12.0, label=False)
        return "auto: a police car (a stab)"
    if word("checkmate") or has("ring closes", "marker ring"):
        stab(m, t, "DmM7", gain=g0, dur=0.8, seed=seed, label=lab)
        m.put("music", crash(seed % 5, 2.4), t, g0 - 8.0, hall=-18.0)
        return "auto: checkmate (a stab, a crash)"
    if word("car", "cars", "drives", "tyres", "tires"):
        put(fx("car_away", dur=max(1.5, d or 3.0), seed=seed % 3), align=None, wet=-16.0)
        return "auto: a car drives off"
    # the room: the chain, the lamp, cloth, smoke, steps
    if word("hum", "buzz"):
        dd = d or 2.0
        m.put("amb", lamp_hum(START[m.sid] + t, dd), t, -44.0, label=lab, align=None)
        return "auto: a hum"
    if word("creak", "creaks"):
        put(hatch_creak(round(d or 0.6, 2), seed % 3), align=None)
        return "auto: a creak"
    if word("cloth", "sleeve", "coat", "kneels", "kneel", "rustle"):
        put(cloth(round(d or 0.4, 2), seed % 5, heavy=0.6 if has("heavy", "coat") else 0.0), align=None)
        return "auto: cloth"
    if word("cigarette", "ember", "crackle", "crackles", "sizzle"):
        put(cut(fx("ember_sizzle", seed=seed % 3), d or 0.9, 0.3), align=None, room_=False)
        return "auto: the ember crackles"
    if word("run", "running", "runs", "burst", "bursts"):
        for k in range(max(2, int(round((d or 1.0) / 0.25)))):
            m.put("feet", footstep("run", seed + k, room(m, t)[0]), t + 0.25 * k - STEP_PRE, g0 - 2.0, pan=pan,
                  label=lab if k == 0 else None, sync=t + 0.25 * k)
        return "auto: running steps"
    if has("two pairs", "two figures", "both of them") and word("step", "steps", "footsteps", "walk", "walking"):
        for j, who in enumerate(("her", "cracker")):
            steps(m, who, t + 0.25 * j, t + max(0.5, d or 1.5), 0.5, gain=g0 - 2.0 - 2.0 * j, pan=pan,
                  room_=room(m, t)[0], label=lab if j == 0 else None, k0=seed % 7 + 2 * j)
        return "auto: two walk away"
    if word("step", "steps", "walk", "walks", "feet", "footsteps", "tiptoe", "creep", "creeps", "slips"):
        who = ("guard" if has("guard") else "knight" if has("knight", "heavy") else
               "cracker" if has("cracker", "creep") else "her")
        steps(m, who, t, t + max(0.5, d or 1.0), 1.0 if who == "guard" else 0.5, gain=g0 - 2.0, pan=pan,
              room_=room(m, t)[0], label=lab, k0=seed % 7)
        return f"auto: steps ({who})"
    if word("ripple", "ripples"):
        put(ripple(seed % 3, 70.0, 1.2), room_=False)
        return "auto: a ripple (sub)"
    if word("swish", "swishes"):
        put(paper_whoosh(round(max(0.3, d or 0.5), 2), seed % 5), align=None)
        return "auto: a soft swish"
    if word("whoosh", "whip", "slash", "slashes", "swings", "lift", "lifts", "split", "diagonal", "diagonals"):
        if word("down"):
            put(whip_down(round(max(0.15, min(d or 0.25, 0.6)), 3), seed % 3), align=None)
            return "auto: a whoosh down"
        x = fx("whoosh", seed=seed % 5, size=0.3)
        put(x, at=t - onset_at(x), align=None)
        return "auto: whoosh"
    if word("thud", "thump", "impact", "lands", "land", "bang"):
        put(strip_thud(seed % 4))
        return "auto: a thud"
    if word("tap", "taps", "click", "clicks", "tick", "ticks"):
        put(switch_click(seed % 5) if word("click", "clicks", "switch") else chalk_tap(seed % 7, 0.5))
        return "auto: a tap"
    return "no sound for these words"


# ============================================================================ the rewind, mixdown and master
REW_GAIN = -5.0
REW_RMS = -24.0              # each rewound snippet to this RMS (dBFS, before the master; at most +12 dB)


def played(a, b, s0, s1):
    """A rewind row the picture plays forward at speed (the tape caught and playing)."""
    return s1 > s0 and 0.8 <= (s1 - s0) / max(b - a, 1e-6) <= 1.25


def rewind_pass(m, mix):
    """s09's rewind: the film's own mix (before the master), cut where the picture rewinds to and
    played into the rewind's place: each row from its source start to its source end (backwards
    when the end is earlier), resampled (band-limited) to the time the picture gives it."""
    rew = np.zeros((N, 2))
    for a, b, s0, s1, sid in m.rewind:
        n_out = n_of(b - a)
        i0, i1 = sorted((int(round(s0 * SR)), int(round(s1 * SR))))
        seg = np.asarray(mix[max(0, i0):i1], np.float64)
        if len(seg) < 64 or n_out < 64:
            continue
        if s1 < s0:
            seg = seg[::-1]
        fr = Fraction(n_out, len(seg)).limit_denominator(2000)
        y = signal.resample_poly(seg, fr.numerator, fr.denominator, axis=0)[:n_out]
        if len(y) < n_out:
            y = np.concatenate([y, np.zeros((n_out - len(y), 2))])
        if played(a, b, s0, s1):          # the tape caught: the film itself, as it was
            dsp.mix_into(rew, dsp.fade(y, 0.007, 0.007), int(round(a * SR)))
            continue
        y = dsp.fade(dsp.sos(y, "lowpass", 9000.0, 2), 0.007, 0.007)
        r = float(np.sqrt(np.mean(np.square(y))))
        if r > 1e-7:
            y = y * min(db2lin(REW_RMS) / r, db2lin(12.0))
        dsp.mix_into(rew, y * db2lin(REW_GAIN), int(round(a * SR)))
    return rew


def mixdown(m):
    """The buses to one mix: the music's plate (the hall bus), the music ducked a little under
    breath, the rewind cut from the mix itself; the stems kept (QA, --stems)."""
    key = m.key
    def duck(x, depth):
        return dsp.sidechain_duck(x, key, depth_db=depth, thresh_db=-44.0, attack=0.03, release=0.35)
    music = duck(m.b["music"].astype(np.float64), -4.0)
    plate = duck(dsp.reverb(m.b["hall"].astype(np.float64), "plate", wet_db=0.0, dry=0.0, seed=7)[:N], -4.0)
    stems = {"music": music + plate}
    for k in ("amb", "efx", "vox", "feet", "tick"):
        stems[k] = m.b[k].astype(np.float64)
    mix = sum(stems.values())
    stems["rew"] = rewind_pass(m, mix) + m.b["rew"].astype(np.float64)
    m.stems = {k: v.astype(np.float32) for k, v in stems.items()}
    return mix + stems["rew"]


def master(mix, t_silence, target=-16.0, ceiling=-1.3):
    """High-pass; digital silence from t_silence (a fade into it); loudness to target; a
    true-peak limiter (iterated: it takes a little loudness)."""
    mix = dsp.sos(mix, "highpass", 30.0, 2)
    a = int(round(t_silence * SR))
    fl = n_of(0.35)
    if 0 < a <= len(mix):
        k = min(fl, a)
        mix[a - k:a] *= np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, k))[:, None] ** 2
        mix[a:] = 0.0
    gain = target - dsp.loudness_integrated(mix)
    out = mix
    for _ in range(5):
        out = dsp.limiter(mix * db2lin(gain), ceiling_db=ceiling)
        lufs = dsp.loudness_integrated(out)
        if abs(lufs - target) < 0.05:
            break
        gain += target - lufs
    out[a:] = 0.0
    out = dsp.fade(out, 0.004, 0.0)
    master.gain = gain
    master.gr = float(np.min(dsp.lin2db(np.maximum(np.abs(out).max(axis=1), 1e-9)
                                        / np.maximum(np.abs(mix * db2lin(gain)).max(axis=1), 1e-9))))
    return out[:N]


# ============================================================================ QA
def find_clicks(x, thresh=8.0, max_report=40):
    """The 2nd difference of the 7 kHz high-passed signal against its local 20 ms RMS."""
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


def onsets(x, rel=0.3, gap=0.2):
    """Times a signal rises through rel of its own peak (at least gap s apart)."""
    e = np.abs(np.asarray(x, np.float64))
    e = e.max(axis=1) if e.ndim == 2 else e
    if not e.size or e.max() <= 0:
        return np.zeros(0)
    thr = rel * e.max()
    idx = np.nonzero((e[1:] >= thr) & (e[:-1] < thr))[0] + 1
    out = []
    for i in idx:
        if not out or i - out[-1] > n_of(gap):
            out.append(i)
    return np.array(out) / SR


def grid_off(t):
    """Seconds from film time t to the nearest point of the swung eighth-note grid."""
    k = math.floor(t / BEAT)
    pts = [(k + f) * BEAT for f in (0.0, SWING, 1.0)]
    return min((t - p for p in pts), key=abs)


def qa(m, t_sil, outdir, path):
    import soundfile as sf
    os.makedirs(outdir, exist_ok=True)
    y, sr = sf.read(path, dtype="float64", always_2d=True)
    gm = db2lin(getattr(master, "gain", 0.0))
    R = {}
    print("\n================ QA:", path)
    R["lufs"], R["tp"], R["peak"] = dsp.loudness_integrated(y), dsp.true_peak_db(y), dsp.sample_peak_db(y)
    R["clipped"] = int(np.sum(np.abs(y) >= db2lin(-0.1)))
    print(f"  file: {sr} Hz, {y.shape[1]} ch, {len(y)} samples = {len(y) / sr:.4f} s (the film: {DUR:.4f} s)")
    print(f"  integrated {R['lufs']:.2f} LUFS (-16 +-0.5)   true peak {R['tp']:.2f} dBTP (<= -1)   sample peak "
          f"{R['peak']:.2f} dBFS   samples at or over -0.1 dBFS: {R['clipped']}   master gain {master.gain:+.1f} dB, "
          f"limiter at most {master.gr:.1f} dB")
    a = int(round(t_sil * SR))
    R["silent_tail"] = bool(np.all(y[a:] == 0.0))
    print(f"  digital silence from {t_sil:.3f} s to the end: {R['silent_tail']}")
    # per scene, per bus
    keys = list(m.stems)
    print("  per scene:  LUFS  short-max  peak | per bus, LUFS at the master's gain: " + " ".join(f"{k:>5s}" for k in keys))
    R["scenes"] = {}
    for sid, s0, d in SCENES:
        i0, i1 = int(s0 * SR), int((s0 + d) * SR)
        seg = y[i0:i1]
        lu = dsp.loudness_integrated(seg) if np.any(seg) else -99.0
        _, st = dsp.loudness_curve(seg, win=3.0, hop=0.25) if len(seg) > 3 * SR else (None, np.array([lu]))
        parts = []
        for k in keys:
            s_ = m.stems[k][i0:i1].astype(np.float64) * gm
            parts.append(dsp.loudness_integrated(s_) if np.any(s_) else -99.0)
        R["scenes"][sid] = dict(lufs=lu, peak=dsp.sample_peak_db(seg), buses=dict(zip(keys, parts)), status=STATUS.get(sid))
        print(f"   {sid} {s0:5.0f}  {lu:6.1f}  {np.max(st):6.1f}  {dsp.sample_peak_db(seg):6.1f} | "
              + " ".join(f"{p:5.0f}" for p in parts) + f"   {STATUS.get(sid, '?')}")
    print("  whole film, per bus (LUFS / peak dBFS at the master's gain): " + ", ".join(
        f"{k} {dsp.loudness_integrated(m.stems[k].astype(np.float64) * gm) if np.any(m.stems[k]) else -99:.1f}/"
        f"{dsp.sample_peak_db(m.stems[k].astype(np.float64) * gm):.1f}" for k in keys))
    # THE CLOCK
    tk = m.stems["tick"].astype(np.float64)
    on = onsets(tk, 0.3, 0.25)
    want = [HEIST_T0 + k * BEAT for k in range(int(math.ceil((HEIST_STOP - HEIST_T0) / BEAT - 1e-9)))]
    off = [min(abs(o - w) for w in want) for o in on] if len(on) and want else []
    after = float(np.max(np.abs(tk[int(round(HEIST_STOP * SR)):]))) if len(tk) else 0.0
    R["ticks"] = dict(n=len(on), want=len(want), first=float(on[0]) if len(on) else None,
                      last=float(on[-1]) if len(on) else None, worst_ms=1000 * max(off) if off else None,
                      after_stop=after)
    print(f"  THE CLOCK: {len(on)} ticks measured on the tick bus (want {len(want)}), first {R['ticks']['first']}, "
          f"last {R['ticks']['last']}; worst offset from the beat {R['ticks']['worst_ms'] or 0:.1f} ms; "
          f"tick bus after {HEIST_STOP:.2f} s: max {after:.1e} ({'silent' if after == 0.0 else 'NOT SILENT'}); "
          f"placed: {len(m.ticks)}, last placed {max(m.ticks) if m.ticks else None}")
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
    # what drives the limiter: the biggest peaks before it, and the stems and placements there
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
    quiet, runs, s_ = rms < -60.0, [], None
    for k, q in enumerate(list(quiet) + [False]):
        if q and s_ is None:
            s_ = k
        elif not q and s_ is not None:
            if (k - s_) * 0.05 > 0.5:
                runs.append((s_ * 0.05, k * 0.05))
            s_ = None
    R["silences"] = runs
    first_event = min(m.starts) if m.starts else 0.0
    print(f"  silences under -60 dBFS longer than 0.5 s before {t_sil:.2f} s: "
          + (", ".join(f"{p:.2f}-{q:.2f}" + (" (the head: before the first sound)" if q <= first_event + 0.06 else "")
                       for p, q in runs) or "none"))
    # clicks
    clicks = find_clicks(y, max_report=400)
    hits = np.array(sorted(m.starts))
    sus = [(t, s) for t, s in clicks if not len(hits) or not np.any((t - hits > -0.003) & (t - hits < 0.08))]
    by = {}
    stem_clicks = {k: np.array([t for t, _ in find_clicks(m.stems[k].astype(np.float64) * gm, max_report=4000)])
                   for k in keys}
    for t, s in sus:
        src_ = [k for k in keys if len(stem_clicks[k]) and np.min(np.abs(stem_clicks[k] - t)) < 0.003]
        by.setdefault("+".join(src_) or "the mix only", []).append((t, s))
    R["clicks"] = {k: len(v) for k, v in by.items()}
    print(f"  click detector: {len(clicks)} transients, {len(sus)} not at the start of a placed sound; by the stem "
          "they are in (efx and feet: grain in chalk, paper, gravel by design): "
          + ", ".join(f"{k} {len(v)}" for k, v in sorted(by.items(), key=lambda kv: -len(kv[1]))))
    for k, v in sorted(by.items()):
        if k not in ("efx", "feet", "efx+feet"):
            print(f"    {k}: " + ", ".join(f"{t:.3f}({s:.0f})" for t, s in v[:12]))
    ends = [e for e in m.edges if e[4] > 0.1]
    R["cut_off"] = len(ends)
    print(f"  placements cut off loud at their end (no real fade): {len(ends)}"
          + ("".join(f"\n    {sid} {t:8.3f} {bus:5s} end {e1:4.2f}  {lab}" for sid, t, lab, e0, e1, bus in ends[:12])))
    cuts = []
    for sid, s0, _ in SCENES[1:]:
        i0 = int(s0 * SR)
        ww = y[i0 - n_of(0.004): i0 + n_of(0.004)]
        cuts.append(f"{s0:.0f}:{float(np.max(np.abs(np.diff(ww, axis=0)))) if len(ww) > 1 else 0:.3f}")
    print("  largest sample step within 4 ms of each cut:", " ".join(cuts))
    # cues
    n_sec = sum(1 for r in m.report if r[2] == "section")
    n_auto = sum(1 for r in m.report if r[2].startswith("auto"))
    n_sil = sum(1 for r in m.report if r[2].startswith(("silence", "the clock")))
    miss = [r for r in m.report if not (r[2] == "section" or r[2].startswith(("auto", "silence", "the clock")))]
    R["cues"] = dict(total=len(m.report), sections=n_sec, auto=n_auto, silence=n_sil, missed=len(miss))
    print(f"  cues: {len(m.report)}: realised by the sections {n_sec}, auto-spotted from their words {n_auto}, "
          f"silence or the clock {n_sil}, NOT REALISED {len(miss)}")
    for sid, c, how in miss:
        print(f"    MISSED {sid} {c['t']:.3f} {c['sfx']!r}: {how}")
    worst = 0.0
    for sid, c, how in m.report:
        if how != "section" or c["t"] < 0:
            continue
        mine = [e for e in m.ev if e["sid"] == sid]
        if mine:
            dd = min(abs(e["t"] - (START[sid] + c["t"])) for e in mine)
            if dd <= FRAME + 1e-6:
                worst = max(worst, dd)
    off_ = [(e["sid"], e["label"], e["meas"] - e["t"]) for e in m.ev if e["meas"] is not None]
    bad = [o for o in off_ if abs(o[2]) > FRAME]
    R["onsets"] = dict(n=len(off_), worst_ms=1000 * max((abs(o[2]) for o in off_), default=0.0), beyond_frame=len(bad))
    print(f"  sync: worst cue-to-event offset {worst * 1000:.1f} ms; measured onsets of {len(off_)} labelled hits: "
          f"worst {R['onsets']['worst_ms']:.1f} ms, {len(bad)} beyond a frame")
    for s_, lab, dd in bad[:30]:
        print(f"    {s_} {lab}: {dd * 1000:+.0f} ms")
    # the music on its grid (swung eighths); the picture's own hits are off it by design
    ms = [sp for sp in m.spans if sp[0] == "music"]
    offs = [grid_off(sp[1]) for sp in ms]
    on_grid = sum(1 for o in offs if abs(o) <= 0.015)
    R["music_grid"] = dict(n=len(ms), on=on_grid)
    print(f"  music on the swung grid: {on_grid} of {len(ms)} note starts within 15 ms "
          f"({100.0 * on_grid / max(1, len(ms)):.0f} %); off it (picture hits): "
          + ", ".join(sorted({f'{sp[1]:.2f}' + (f' {sp[3]}' if sp[3] else '') for sp, o in zip(ms, offs) if abs(o) > 0.015 and sp[3]})[:12]))
    print("  rewind rows (film): " + "; ".join(f"{a_:.2f}-{b_:.2f} <- {sid} {s0:.2f}->{s1:.2f}" for a_, b_, s0, s1, sid in m.rewind))
    if m.rewind:
        js = sorted({round(t_, 4) for a_, b_, *_ in m.rewind for t_ in (a_, b_)})
        rw = m.stems["rew"].astype(np.float64) * gm
        print("  the rewind's joins, largest sample step within 2 ms (rew stem / the mix): " + " ".join(
            f"{t_:.2f}:{np.max(np.abs(np.diff(rw[int(t_ * SR) - n_of(0.002):int(t_ * SR) + n_of(0.002)], axis=0))):.3f}/"
            f"{np.max(np.abs(np.diff(y[int(t_ * SR) - n_of(0.002):int(t_ * SR) + n_of(0.002)], axis=0))):.3f}" for t_ in js))
    with open(os.path.join(outdir, "qa.json"), "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    overview(y, m, outdir)
    return R


def overview(y, m, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
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
    cols = dict(music="#1f5fa8", efx="#c0392b", amb="#7f8c8d", vox="#8e44ad", feet="#a0522d", tick="#000000", rew="#16a085")
    for k_, st in m.stems.items():
        if not np.any(st):
            continue
        tb, lb = dsp.loudness_curve(st.astype(np.float64) * gm, win=1.0, hop=0.1)
        ax[3].plot(tb, lb, color=cols.get(k_, "#333"), lw=1.0, label=k_)
    ax[3].set_ylim(-60, -5)
    ax[3].set_ylabel("per bus (1 s)")
    ax[3].legend(loc="lower right", ncol=7, fontsize=9)
    for e in m.ev:
        ax[4].plot([e["t"], e["t"]], [0, 1], color="#c00" if e["bus"] == "music" else "#036", lw=0.5)
    for tk in m.ticks:
        ax[4].plot([tk, tk], [0, 0.3], color="#000", lw=0.4)
    ax[4].set_yticks([])
    ax[4].set_ylabel("events")
    for a in ax:
        for sid, s0, d in SCENES:
            a.axvline(s0, color="#0a0", lw=1.0)
        a.axvline(HEIST_STOP, color="#e00", lw=0.8, ls=":")
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
    """One section; if it fails with the scene's module, it is played again from the bible; if it
    fails from the bible too, it is left out (and said so). Never raises."""
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
    ap.add_argument("--qa", metavar="DIR", help="measure the master; report and DIR/overview.png")
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
        mix = dsp.limiter(mix * db2lin(-16.0 - lu if np.isfinite(lu) else 0.0), ceiling_db=-1.3)
        sf.write(path, mix[:N].astype(np.float32), SR, subtype="PCM_24")
        print(path)
        return
    out = master(mix, t_sil)
    path = os.path.join(out_dir, "audio_master.wav")
    sf.write(path, out.astype(np.float32), SR, subtype="PCM_24")
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
    if ARGS.qa:
        qa(m, t_sil, ARGS.qa, path)


if __name__ == "__main__":
    main()
