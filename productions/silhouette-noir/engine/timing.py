"""Film timelines: scene durations, transitions, narration placement and word times.

Each film has films/<film>/timeline/timeline.json, written by films/<film>/timeline/
build_timeline.py from the narration takes (vo_lines.json + vo_words.txt) and the bible's
storyboard table. Scenes read it through SceneTiming:

    T.duration, T.frames            # this scene's length (its handles are extra)
    T.at('tugs'), T.end('tugs')     # scene-local start/end of a narration word
    T.line(16)                      # (t0, t1) of narration line 16, scene-local
    T.handle_in, T.handle_out       # seconds rendered before 0 / after duration for transitions

Times are seconds. Scene-local time 0 is the scene's first frame; film time 0 is the film's.
"""
import json
import os
import re

from .core import FPS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILMS = ("salvage", "shadowplay", "red", "lantern", "opposite")

_TL = {}


def film_dir(film, *parts):
    return os.path.join(ROOT, "films", film, *parts)


def timeline(film):
    if film not in _TL:
        with open(film_dir(film, "timeline", "timeline.json")) as fh:
            _TL[film] = json.load(fh)
    return _TL[film]


def _norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


class SceneTiming:
    """Scene-relative timing. All times in seconds from the scene's first frame."""

    def __init__(self, film, sid):
        tl = timeline(film)
        d = next(s for s in tl["scenes"] if s["id"] == sid)
        self.d = d
        self.film = film
        self.id = sid
        self.slug = d["slug"]
        self.duration = d["duration"]
        self.frames = d["frames"]
        self.start = d["start"]
        self.lines = d["lines"]            # [{n, t0, t1, text}] overlapping this scene (scene-local)
        self.words = d["words"]            # [{w, t0, t1, n}] scene-local
        self.text = " ".join(l["text"] for l in self.lines)
        self.vo_start = self.lines[0]["t0"] if self.lines else None
        self.vo_end = self.lines[-1]["t1"] if self.lines else None
        self.trans_in = d.get("trans_in")
        self.trans_out = d.get("trans_out")
        self.handle_in = d.get("handle_in", 0.0)
        self.handle_out = d.get("handle_out", 0.0)
        self.prev = d.get("prev")
        self.next = d.get("next")

    def word(self, text, n=0):
        """(t0, t1) of the n-th occurrence of a word in this scene's narration
        (case/punctuation-insensitive)."""
        key = _norm(text)
        hits = [w for w in self.words if _norm(w["w"]) == key]
        if not hits:
            raise KeyError(f"{self.film}/{self.id}: word {text!r} not in narration: {self.text}")
        w = hits[min(n, len(hits) - 1)]
        return w["t0"], w["t1"]

    def at(self, text, n=0):
        return self.word(text, n)[0]

    def end(self, text, n=0):
        return self.word(text, n)[1]

    def line(self, n):
        """(t0, t1) of narration line n (film numbering), scene-local."""
        for l in self.lines:
            if l["n"] == n:
                return l["t0"], l["t1"]
        raise KeyError(f"{self.film}/{self.id}: line {n} is not in this scene")

    def speaking(self, t, pad=0.0):
        """True while the narrator is speaking at scene time t."""
        return any(l["t0"] - pad <= t <= l["t1"] + pad for l in self.lines)

    def __repr__(self):
        return f"<SceneTiming {self.film}/{self.id} {self.duration:.3f}s>"


def Cue(t, sfx, gain_db=0.0, pan=0.0, dur=None, **params):
    """A sound cue at scene-relative time t, exported by a scene's optional cues(T) for the
    sound team (the name is free text describing the sound; see the film's sound plan).
    pan -1 (left) .. 1 (right). dur for sustained sounds."""
    c = {"t": round(float(t), 4), "sfx": sfx, "gain_db": float(gain_db), "pan": float(pan)}
    if dur is not None:
        c["dur"] = float(dur)
    if params:
        c["params"] = params
    return c


# ----------------------------------------------------------------------------- building
def _load_takes(film):
    """Narration lines (t0/t1 in narration_full.wav) with their words attached."""
    tdir = film_dir(film, "timeline")
    with open(os.path.join(tdir, "vo_lines.json")) as fh:
        lines = json.load(fh)
    words = []
    with open(os.path.join(tdir, "vo_words.txt")) as fh:
        for row in fh:
            parts = row.split()
            if len(parts) >= 3:
                words.append((parts[0], float(parts[1]), float(parts[2])))
    for l in lines:
        l["words"] = [w for w in words if l["t0"] - 0.02 <= w[1] < l["t1"] + 0.02]
    return lines


def build(film, scenes, place, src="audio/vo/narration_full.wav"):
    """Write films/<film>/timeline/timeline.json.

    scenes: [(id, slug, duration_s, trans_out)] in film order. trans_out is None (hard cut)
        or dict(kind=..., dur=seconds, align=0.5, **params) for transitions.apply(); the
        transition window is [cut - dur*align, cut + dur*(1-align)].
    place: {line_n: (scene_id, scene_local_start_s)} - where each narration line starts.
    """
    lines = _load_takes(film)
    out_scenes, start = [], 0.0
    for i, (sid, slug, dur, tout) in enumerate(scenes):
        frames = int(round(dur * FPS))
        if abs(frames / FPS - dur) > 1e-6:
            raise ValueError(f"{sid}: duration {dur} is not a whole number of frames")
        out_scenes.append(dict(id=sid, slug=slug, start=round(start, 6), duration=dur, frames=frames,
                               prev=scenes[i - 1][0] if i else None,
                               next=scenes[i + 1][0] if i + 1 < len(scenes) else None,
                               trans_out=tout, trans_in=None, handle_in=0.0, handle_out=0.0))
        start += dur
    total = start
    by_id = {s["id"]: s for s in out_scenes}
    for a, b in zip(out_scenes, out_scenes[1:]):
        tr = a["trans_out"]
        if tr and tr.get("kind", "cut") != "cut" and tr.get("dur", 0) > 0:
            al = tr.get("align", 0.5)
            b["trans_in"] = tr
            a["handle_out"] = round(tr["dur"] * (1 - al), 6)
            b["handle_in"] = round(tr["dur"] * al, 6)
    # narration on the film clock
    vo = []
    for l in lines:
        if l["n"] not in place:
            raise ValueError(f"line {l['n']} has no placement")
        sid, off = place[l["n"]]
        t0 = by_id[sid]["start"] + off
        vo.append(dict(n=l["n"], text=l["text"], start=round(t0, 4), end=round(t0 + l["t1"] - l["t0"], 4),
                       src_t0=l["t0"], src_t1=l["t1"],
                       words=[dict(w=w, t0=round(t0 + a - l["t0"], 4), t1=round(t0 + b - l["t0"], 4))
                              for w, a, b in l["words"]]))
    vo.sort(key=lambda v: v["start"])
    for p, q in zip(vo, vo[1:]):
        if q["start"] < p["end"] + 0.25:
            raise ValueError(f"lines {p['n']} and {q['n']} overlap ({p['end']:.2f} > {q['start']:.2f})")
    if vo and vo[-1]["end"] > total:
        raise ValueError(f"last line ends at {vo[-1]['end']:.2f} after the film ({total:.2f})")
    for s in out_scenes:
        s0, s1 = s["start"] - s["handle_in"], s["start"] + s["duration"] + s["handle_out"]
        s["lines"], s["words"] = [], []
        for v in vo:
            if v["end"] > s0 and v["start"] < s1:
                s["lines"].append(dict(n=v["n"], text=v["text"], t0=round(v["start"] - s["start"], 4),
                                       t1=round(v["end"] - s["start"], 4)))
                s["words"] += [dict(w=w["w"], t0=round(w["t0"] - s["start"], 4),
                                    t1=round(w["t1"] - s["start"], 4), n=v["n"]) for w in v["words"]]
    tl = dict(film=film, fps=FPS, duration=round(total, 6), frames=int(round(total * FPS)),
              vo_src=src, scenes=out_scenes, vo=vo)
    path = film_dir(film, "timeline", "timeline.json")
    with open(path, "w") as fh:
        json.dump(tl, fh, indent=1)
    _TL.pop(film, None)
    return tl


def summary(film):
    """Human-readable storyboard timing table (for the bible and QA)."""
    tl = timeline(film)
    rows = [f"{film}: {tl['duration']:.2f} s, {tl['frames']} frames"]
    for s in tl["scenes"]:
        tr = s["trans_out"]
        trs = "cut" if not tr else f"{tr['kind']} {tr.get('dur', 0):.2f}s"
        ln = " ".join(f"L{l['n']}@{l['t0']:.2f}-{l['t1']:.2f}" for l in s["lines"])
        rows.append(f"  {s['id']} {s['slug']:<22} {s['start']:7.2f} +{s['duration']:5.2f}  -> {trs:<16} {ln}")
    return "\n".join(rows)
