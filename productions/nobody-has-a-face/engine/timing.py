"""Timeline access for scenes: durations, narration word times, SFX cues."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMELINE_PATH = os.path.join(ROOT, "timeline", "timeline.json")

_TL = None


def timeline():
    global _TL
    if _TL is None:
        with open(TIMELINE_PATH) as fh:
            _TL = json.load(fh)
    return _TL


def _norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


class SceneTiming:
    """Scene-relative timing. All times in seconds from the scene's first frame."""

    def __init__(self, sid):
        d = next(s for s in timeline()["scenes"] if s["id"] == sid)
        self.d = d
        self.id = sid
        self.slug = d["slug"]
        self.duration = d["duration"]
        self.frames = d["frames"]
        self.start = d["start"]
        self.vo_start = d["vo_start"]
        self.vo_end = d["vo_end"]
        self.words = d["words"]
        self.text = d["text"]

    def word(self, text, n=0):
        """(t0, t1) of the n-th occurrence of a word (case/punctuation-insensitive).
        Hyphenated TTS tokens are matched piecewise: 'three-' / 'oh-' / 'seven.'."""
        key = _norm(text)
        hits = [w for w in self.words if _norm(w["w"]) == key]
        if not hits:
            raise KeyError(f"{self.id}: word {text!r} not in narration: {self.text}")
        w = hits[min(n, len(hits) - 1)]
        return w["t0"], w["t1"]

    def at(self, text, n=0):
        return self.word(text, n)[0]

    def end(self, text, n=0):
        return self.word(text, n)[1]

    def __repr__(self):
        return f"<SceneTiming {self.id} {self.duration:.3f}s vo {self.vo_start:.2f}-{self.vo_end:.2f}>"


def Cue(t, sfx, gain_db=0.0, pan=0.0, dur=None, **params):
    """A sound-effect cue at scene-relative time t. `sfx` must be a name from the SFX
    catalog (see engine/API.md). pan -1 (left) .. 1 (right). dur for sustained sounds."""
    c = {"t": round(float(t), 4), "sfx": sfx, "gain_db": float(gain_db), "pan": float(pan)}
    if dur is not None:
        c["dur"] = float(dur)
    if params:
        c["params"] = params
    return c
