"""SALVAGE cue sheet: designed sound events on the film clock, the continuous layers' schedules,
the acoustic map (which space each moment sounds in) and the merge with the scenes' cues.

All times are film seconds, computed from the locked timeline: a word anchor is the scene's
start + the word's scene-local time (SceneTiming.at), so the hits land exactly on the words.

Cue kinds:
    story     the bible's key sync hits (helmet clank, lamp click, tumblers, tugs, knife, cut,
              weights, the bell): always played; retimed to a scene's matching cue if one exists
    sync      designed picture-sync sounds: retimed to a matching scene cue when one exists
    fallback  picture detail the animator is better placed to time (footsteps, paper pops):
              dropped when the scene module supplies cues of its own
"""
from __future__ import annotations

import math

import numpy as np

from engine.timing import SceneTiming, timeline

from . import sfx_salvage as S

FILM = "salvage"

# continuous-layer sounds: a scene cue that resolves to one of these is covered by the layer
LAYER_SOUNDS = ("helmet_breath", "helmet_hiss", "pump_run", "winch_crank", "swell_lap", "bubble_stream", "ambience")
MATCH_TOL = dict(story=1.0, sync=0.75, fallback=0.5)


class Clock:
    """Film-clock helpers over the locked timeline."""

    def __init__(self):
        self.tl = timeline(FILM)
        self.scenes = self.tl["scenes"]
        self.T = {s["id"]: SceneTiming(FILM, s["id"]) for s in self.scenes}
        self.duration = float(self.tl["duration"])
        self.frames = int(self.tl["frames"])
        self.fps = float(self.tl["fps"])

    def g(self, sid, t=0.0):
        return self.T[sid].start + t

    def w(self, sid, word, n=0):
        return self.T[sid].start + self.T[sid].at(word, n)

    def we(self, sid, word, n=0):
        return self.T[sid].start + self.T[sid].end(word, n)

    def start(self, sid):
        return self.T[sid].start

    def end(self, sid):
        return self.T[sid].start + self.T[sid].duration

    def scene_at(self, t):
        for s in self.scenes:
            if s["start"] <= t < s["start"] + s["duration"]:
                return s["id"]
        return self.scenes[-1]["id"]

    def trans(self, sid):
        """(t0, t1) film window of the transition out of scene sid (None for a hard cut)."""
        d = next(s for s in self.scenes if s["id"] == sid)
        tr = d.get("trans_out") or {}
        if not tr or tr.get("kind", "cut") == "cut" or not tr.get("dur"):
            return None
        cut = d["start"] + d["duration"]
        al = tr.get("align", 0.5)
        return cut - tr["dur"] * al, cut + tr["dur"] * (1 - al)


_SEQ = [0]


def cue(t, name, gain=0.0, kind="sync", pan=0.0, params=None, dur=None, space=None, label=None, seed=None, bus=None,
        group=None, **extra):
    sp = S.spec(name)
    _SEQ[0] += 1
    c = dict(t=round(float(t), 4), name=name, gain_db=float(gain), kind=kind, pan=float(pan), params=dict(params or {}),
             dur=dur, space=space, label=label or name, seed=_SEQ[0] if seed is None else seed,
             bus=bus or ("hits" if sp.get("hit") else "sfx"), group=group or name, src="designed")
    c.update(extra)
    return c


# ============================================================================ the designed cue sheet
def designed(C):
    _SEQ[0] = 0
    g, w, we = C.g, C.w, C.we
    cs = []
    add = cs.append

    # ---------------------------------------------------------------- s01 the line (paper -> live)
    add(cue(g("s01", 0.0), "paper_slice", -5, "story", params=dict(length=1.0), label="red line draws"))
    add(cue(w("s01", "men"), "paper_pops", -15, "fallback", params=dict(count=7, gap=0.035), label="figures hang"))
    add(cue(w("s01", "down"), "paper_flutter", -13, "fallback", params=dict(length=0.85), label="figures drop"))
    add(cue(g("s01", 4.2), "paper_slide", -14, "fallback", params=dict(length=0.9), label="line curls to ring"))
    add(cue(g("s01", 4.25), "reverse_swell", -17, "fallback", dur=1.5, bus="sfx", label="iris opens on water"))
    add(cue(g("s01", 6.0), "uw_whoosh", -17, "fallback", params=dict(size=0.5), label="pull back"))

    # ---------------------------------------------------------------- s02 cash (dusk deck)
    add(cue(g("s02", 0.55), "surface_pops", -9, "sync", label="bubbles burst at waterline"))
    add(cue(g("s02", 0.75), "cam_breach", -8, "sync", label="camera breaks the surface"))
    add(cue(w("s02", "paid") - 0.05, "envelope_pass", -12, "sync", label="envelope held out"))
    add(cue(w("s02", "cash") - 0.62, "envelope_pass", -10, "sync", label="diver takes the cash"))
    add(cue(w("s02", "cash") + 1.25, "paper_rustle", -20, "fallback", dur=0.8, label="tucks it in the suit"))
    add(cue(w("s02", "name") - 0.45, "cigar_draw", -13, "sync", label="ember flares"))
    add(cue(w("s02", "men") - 0.25, "wind_gust", -16, "sync", dur=3.2, label="wind lifts the coat"))
    add(cue(w("s02", "using") - 0.03, "knife_glint", -11, "story", label="knife glint 1"))
    add(cue(w("s02", "it"), "helmet_clank", -1, "story", label="CLANK"))
    add(cue(g("s02", 14.45), "ladder_step", -11, "fallback", params=dict(wet=0), label="onto the ladder"))
    add(cue(g("s02", 14.85), "ladder_step", -13, "fallback", params=dict(wet=0), label="ladder"))

    # ---------------------------------------------------------------- s03 salvage (title, descent)
    add(cue(g("s03", 0.9), "entry_splash", -3, "story", label="drops in"))
    for k in range(7):                                    # S A L V A G E land on the waterline
        add(cue(g("s03", 1.55 + 0.19 * k), "paper_pop", -17 - (k % 2), "fallback", params=dict(pitch=1.12 - 0.035 * k),
                label="title letter" if k == 0 else None, group="title"))
    add(cue(g("s03", 5.0), "paper_slide", -16, "fallback", params=dict(length=0.8), label="title slides out"))
    add(cue(g("s03", 5.25), "cam_plunge", -10, "sync", label="camera goes under"))
    add(cue(g("s03", 8.05), "fish_school", -11, "sync", label="fish school"))
    add(cue(g("s03", 11.3), "lamp_click", -4, "story", label="lamp click"))

    # ---------------------------------------------------------------- s04 calm night (paper) - fallbacks
    add(cue(w("s04", "storm"), "paper_slam", -4, "fallback", label="storm slams"))
    add(cue(we("s04", "storm"), "paper_tear", -5, "fallback", label="storm torn away"))
    add(cue(w("s04", "reef"), "paper_scrape", -7, "fallback", label="reef"))
    add(cue(w("s04", "lifeboat"), "paper_pops", -7, "fallback", params=dict(count=8, gap=0.12), label="8 lifeboats"))
    add(cue(g("s04", 6.7), "ship_groan", -6, "fallback", label="ship tilts"))
    add(cue(g("s04", 6.95), "uw_whoosh", -6, "fallback", params=dict(size=0.9), label="ship sinks"))
    add(cue(w("s04", "inquiry") - 0.1, "card_flip", -5, "fallback", label="field flips"))
    add(cue(w("s04", "inquiry"), "paper_slide", -8, "fallback", params=dict(sides=2, length=0.5), label="hands slide in"))
    add(cue(w("s04", "captain"), "paper_stamp", -2, "fallback", label="red ring"))
    add(cue(g("s04", 13.3), "paper_hole", -4, "fallback", label="hole opens"))

    # ---------------------------------------------------------------- s05 the meridian
    add(cue(g("s05", 0.75), "silt_puff", -8, "sync", params=dict(size=0.8), label="lands in silt"))
    for k, tt in enumerate((2.0, 3.15, 4.3, 5.45)):
        add(cue(g("s05", tt), "silt_step", -14 - k * 0.5, "fallback", label="heavy gait" if k == 0 else None, group="gait"))
    add(cue(g("s05", 4.9), "hull_ping", -15, "fallback", label="beam hits the hull"))
    add(cue(w("s05", "deep") - 1.45, "hull_groan", -7, "sync", params=dict(size=1.0, length=4.6), label="the wreck groans"))
    add(cue(w("s05", "convenient") - 0.08, "meridian_bell_uw", -5, "story", params=dict(length=9.0), label="muffled bell"))
    add(cue(g("s05", 12.95), "uw_whoosh", -9, "sync", params=dict(size=0.35), label="whip left"))

    # ---------------------------------------------------------------- s06 outward
    add(cue(w("s06", "holes") + 0.05, "metal_creak", -15, "fallback", params=dict(pitch=0.8), label="more holes"))
    add(cue(w("s06", "holes") + 0.7, "hull_ping", -18, "fallback"))
    add(cue(w("s06", "cut"), "glove_metal", -9, "sync", label="glove on petal"))
    add(cue(w("s06", "inside") - 0.05, "uw_whoosh", -11, "sync", params=dict(size=0.75), label="push into the hole"))
    add(cue(w("s06", "inside") + 1.6, "hull_groan", -16, "fallback", params=dict(size=0.5, length=3.0), space="wreck"))

    # ---------------------------------------------------------------- s07 the price (paper)
    add(cue(g("s07", 0.0), "torch_cut", -7, "sync", params=dict(length=1.15), label="torch cuts from inside"))
    add(cue(g("s07", 0.95), "plate_fall", -7, "sync", label="disk falls away"))
    add(cue(w("s07", "twice") - 0.08, "paper_slide", -10, "fallback", params=dict(length=0.4), label="second ship"))
    add(cue(w("s07", "worth") - 0.1, "paper_slide", -11, "fallback", params=dict(length=0.35), label="hand with notes"))
    add(cue(w("s07", "worth") + 0.25, "cash_riffle", -9, "fallback", label="stacks double"))
    add(cue(w("s07", "thirtyone"), "paper_pops", -12, "fallback", params=dict(count=4, gap=0.16), label="31 crew stagger in"))
    add(cue(w("s07", "part") - 0.05, "paper_swishes", -11, "fallback", params=dict(count=4, length=0.85), label="water bars rise"))
    add(cue(w("s07", "part"), "uw_whoosh", -15, "fallback", params=dict(size=0.5)))
    add(cue(w("s07", "price"), "paper_hole", -8, "fallback", label="captain swallowed"))
    add(cue(C.trans("s07")[0], "paper_swishes", -14, "fallback", params=dict(count=7, length=0.75), label="ink columns"))

    # ---------------------------------------------------------------- s08 the shaft (wreck)
    for k, tt in enumerate((0.6, 1.5, 2.4, 3.3)):
        add(cue(g("s08", tt), "glove_metal", -15 - 0.5 * k, "fallback", label="hand over hand" if k == 0 else None, group="hands"))
    add(cue(g("s08", 1.8), "chair_turn", -13, "fallback", label="chair turns"))
    add(cue(w("s08", "captain's") + 0.05, "silt_puff", -11, "sync", params=dict(size=0.5), label="drops into the cabin"))
    add(cue(w("s08", "safe") + 0.15, "hull_ping", -17, "fallback", label="the safe"))
    add(cue(g("s08", 8.5), "uw_whoosh", -17, "fallback", params=dict(size=0.3), label="push in to dial"))

    # ---------------------------------------------------------------- s09 birthday (the dial)
    add(cue(g("s09", 0.55), "glove_metal", -14, "fallback", label="fingers grip the knob"))
    clicks = [g("s09", 3.9), g("s09", 4.6), g("s09", 5.3)]
    add(cue(w("s09", "birthday"), "dial_turn", -9, "sync", dur=clicks[0] - w("s09", "birthday") + 0.02, label="dial turn R"))
    add(cue(clicks[0] + 0.07, "dial_turn", -10, "sync", dur=0.55, label="dial turn L"))
    add(cue(clicks[1] + 0.07, "dial_turn", -10, "sync", dur=0.55, label="dial turn R"))
    for k, tt in enumerate(clicks):
        add(cue(tt, "tumbler_click", -2 + 0.5 * k, "story", label=f"tumbler {k + 1}", group="tumbler"))
    add(cue(g("s09", 7.45), "safe_open", -4, "sync", label="safe door opens"))

    # ---------------------------------------------------------------- s10 his own hand
    add(cue(w("s10", "father's") - 0.1, "page_flip", -16, "sync", label="photo slips out"))
    add(cue(w("s10", "father's") + 0.15, "paper_slide", -19, "fallback", params=dict(length=0.6)))
    add(cue(w("s10", "orders") - 0.08, "page_flip", -10, "sync", label="page turns"))
    add(cue(g("s10", 7.2), "rope_creak", -17, "fallback", label="winch line descends"))
    add(cue(g("s10", 8.6), "hook_clank", -11, "sync", label="hook knocks the hull"))

    # ---------------------------------------------------------------- s11 two tugs
    add(cue(g("s11", 0.45), "silt_step", -15, "fallback", group="gait"))
    add(cue(g("s11", 1.3), "silt_step", -15.5, "fallback", group="gait"))
    add(cue(w("s11", "something") - 0.05, "rope_tie", -8, "sync", label="ties the line"))
    add(cue(g("s11", 4.2), "silt_step", -16, "fallback", group="gait"))
    add(cue(g("s11", 5.0), "silt_step", -16.5, "fallback", group="gait"))
    add(cue(w("s11", "two"), "rope_tug", 0, "story", label="tug 1", group="tug"))
    add(cue(w("s11", "tugs"), "rope_tug", 1, "story", label="tug 2", group="tug"))
    add(cue(g("s11", 7.35), "uw_whoosh", -15, "fallback", params=dict(size=0.6), label="up the line"))
    add(cue(C.trans("s11")[0] + 0.35, "cam_breach", -7, "sync", label="breaks the surface (night)"))

    # ---------------------------------------------------------------- s12 the cut (night deck)
    add(cue(w("s12", "tight"), "winch_strain", -2, "story", label="line goes tight"))
    add(cue(w("s12", "tight") + 0.3, "rope_creak", -13, "sync"))
    add(cue(g("s12", 4.35), "deck_step", -22, "fallback", params=dict(weight=0.2), label="cigar set down"))
    add(cue(w("s12", "then"), "knife_draw", -3, "story", label="knife drawn"))
    add(cue(w("s12", "then") + 0.2, "knife_glint", -13, "sync", label="knife glint 2"))
    add(cue(w("s12", "cut"), "hose_cut", 1, "story", label="SLASH"))
    add(cue(w("s12", "cut") + 0.06, "air_escape", -5, "story", dur=3.6, label="air hisses"))
    add(cue(g("s12", 8.0), "cam_plunge", -9, "sync", label="camera tilts under"))
    add(cue(g("s12", 8.5), "hose_bubbles", -10, "sync", space="underwater", label="severed hose sinks"))

    # ---------------------------------------------------------------- s13 one breath
    add(cue(we("s13", "air") + 0.05, "breath_single", -12, "sync", params=dict(phase="in", length=0.85), label="one breath in"))
    add(cue(we("s13", "calm") + 0.12, "breath_single", -14, "sync", params=dict(phase="out", length=1.3), label="breath out"))
    add(cue(g("s13", 8.25), "buckle", -9, "sync", label="unbuckles"))
    add(cue(g("s13", 8.55), "weights_drop", -2, "story", label="weights drop"))
    add(cue(g("s13", 8.8), "bubble_release", -4, "story", label="big bubble release"))
    add(cue(g("s13", 9.3), "boot_drop", -5, "story", label="boot 1", group="boots"))
    add(cue(g("s13", 9.72), "boot_drop", -6, "story", label="boot 2", group="boots"))
    add(cue(g("s13", 9.9), "uw_whoosh", -16, "fallback", params=dict(size=0.5), label="begins to rise"))

    # ---------------------------------------------------------------- s14 the bell (split level)
    add(cue(g("s14", 1.6), "exhaust_bubbles", -15, "fallback", params=dict(size=0.6), space="underwater", label="rising: air vents"))
    add(cue(w("s14", "safe") - 0.2, "cigar_draw", -15, "sync", label="ember flares (pleased)"))
    add(cue(g("s14", 4.7), "exhaust_bubbles", -14, "fallback", params=dict(size=0.7), space="underwater"))
    add(cue(g("s14", 7.4), "exhaust_bubbles", -14, "fallback", params=dict(size=0.8), space="underwater"))
    add(cue(w("s14", "bell"), "bell_surface", -2, "story", label="the bell breaks the surface"))
    add(cue(w("s14", "bell") + 0.82, "meridian_bell", -1, "story", params=dict(strike=0.85, length=16.0), label="TOLL 1"))
    add(cue(g("s14", 10.2), "rope_creak", -14, "fallback", label="davit creaks"))

    # ---------------------------------------------------------------- s15 my name
    add(cue(g("s15", 0.45), "surfacing", -7, "sync", label="helmet breaks surface"))
    add(cue(g("s15", 0.75), "rope_creak", -17, "fallback", label="davit"))
    for k, tt in enumerate((1.85, 2.55, 3.25)):
        add(cue(g("s15", tt), "ladder_step", -10 - 0.5 * k, "fallback", label="climbs the ladder" if k == 0 else None, group="ladder"))
    add(cue(g("s15", 2.9), "deck_step", -17, "fallback", params=dict(weight=0.35), label="client backs away", group="client"))
    add(cue(g("s15", 3.6), "deck_step", -18, "fallback", params=dict(weight=0.35), group="client"))
    add(cue(g("s15", 4.05), "deck_step", -9, "fallback", params=dict(wet=1), label="onto the deck"))
    add(cue(w("s15", "told") - 0.35, "helmet_unlock", -6, "sync", label="helmet off"))
    add(cue(g("s15", 6.25), "deck_step", -11, "fallback", params=dict(wet=1), label="steps toward him"))
    add(cue(g("s15", 6.8), "meridian_bell", 3, "story", params=dict(strike=1.0, length=24.0), label="TOLL 2 (loudest)",
            xwater=(C.g("s16", -0.9), 2.8)))

    # ---------------------------------------------------------------- s16 the sea keeps
    add(cue(w("s16", "back") - 0.4, "hull_groan", -13, "sync", params=dict(size=0.9, length=4.4), label="the wreck below"))
    add(cue(g("s16", 11.3), "silt_puff", -18, "fallback", params=dict(size=0.25), label="hat lands"))
    add(cue(w("s16", "me"), "paper_slice", -7, "story", params=dict(length=1.0, reverse=1), label="red line slides out",
            space="paper"))
    return sorted(cs, key=lambda c: c["t"])


# ============================================================================ continuous layers
def bubble_time(e):
    """Film time at which an event's exhaust bubbles burst out (None if it has none)."""
    t = e["t"] + (e.get("inhale", 0) + e.get("hold", 0.25) if e.get("inhale", 0) > 0 else 0.0)
    if e.get("bub", 1.0) <= 0 or not (e.get("exhale", 0) > 0 or e.get("bub_len")):
        return None
    ex = float(e.get("exhale", 0) or 1.0)
    return t + float(e.get("bub_delay", 0.35 * ex))


def sync_breaths(ev, sync, tol=2.2):
    """Move the breath whose bubbles are nearest each picture-synced bubble burst so they land on
    it (a scene's 'exhale: bubble burst' cue); add an exhale where none is near."""
    ev = [dict(e) for e in ev]
    moved = []
    for ts in sorted(sync):
        best, bd = None, tol
        for i, e in enumerate(ev):
            bt = bubble_time(e)
            if bt is None or i in moved:
                continue
            if abs(bt - ts) < bd:
                best, bd = i, abs(bt - ts)
        if best is None:
            ev.append(dict(t=ts - 0.5, inhale=0.0, exhale=1.6, size=1.0, bub=1.0, bub_delay=0.5, bub_len=1.2))
            moved.append(len(ev) - 1)
        else:
            ev[best]["t"] += ts - bubble_time(ev[best])
            moved.append(best)
    for i in moved:
        ev[i]["_moved"] = True
    ev.sort(key=lambda e: e["t"])
    # keep a moved breath from overlapping its neighbours: shorten the neighbour's inhale
    for a, b in zip(ev, ev[1:]):
        if not (a.get("_moved") or b.get("_moved")):
            continue
        end_a = a["t"] + a.get("inhale", 0) + a.get("hold", 0.25) + a.get("exhale", 0)
        if b["t"] < end_a - 0.3 and b.get("inhale", 0) > 0:
            cut = (end_a - 0.3) - b["t"]
            if cut < b["inhale"] - 0.4:
                b["inhale"] -= cut
                b["t"] += cut
            else:
                b["inhale"] = 0.0
    for e in ev:
        e.pop("_moved", None)
    return ev


def breath_events(C, rng=None, sync=()):
    """The diver's free-flow breathing: (events for sfx_salvage.breathing_track, gain automation).
    sync: film times of picture-synced bubble bursts from the scenes."""
    rng = rng or np.random.default_rng(31)
    g, w = C.g, C.w
    ev = []

    def run(t0, t1, period, size=1.0, bub=1.0, inhale=1.45, exhale=1.95):
        ev.extend(S.periodic_breaths(t0, t1, period, rng, 0.07, inhale, exhale, size, bub))

    # s01: the diver sinking (present day), two breaths, the bubbles the camera follows
    ev.append(dict(t=g("s01", 6.05), inhale=1.35, hold=0.2, exhale=2.1, size=0.85, bub=1.0, bub_len=1.8))
    ev.append(dict(t=g("s01", 9.9), inhale=1.3, hold=0.25, exhale=0.0, size=0.8))
    # s02: the helmet goes on: first breath, then the splash and the descent
    ev.append(dict(t=w("s02", "it") + 0.3, inhale=0.95, hold=0.4, exhale=0.0, size=1.05))    # breathes in, drops in
    ev.append(dict(t=g("s03", 1.35), inhale=0.0, exhale=2.2, size=1.1, bub=1.0, bub_len=1.6))  # exhale under
    run(g("s03", 4.1), g("s03", 13.6), 4.7)
    # s05-s06 (s04 is paper: muted)
    run(g("s05", 0.2), C.end("s06") - 0.4, 4.5)
    # s08-s09 up to the dial
    run(g("s08", 0.0), g("s09", 2.6), 4.4)
    # the held breath through the spiral, released when the door opens
    ev.append(dict(t=g("s09", 2.75), inhale=1.25, hold=0.0, exhale=0.0, size=1.0))
    ev.append(dict(t=g("s09", 7.35), inhale=0.0, exhale=2.3, size=1.15, bub=1.2, bub_len=1.9, bub_size=1.2))
    # s10: a sigh at the photo, then calm again
    ev.append(dict(t=w("s10", "father's") + 0.45, inhale=1.1, hold=0.3, exhale=2.6, size=0.95, bub=1.0, bub_len=2.0))
    run(g("s10", 6.0), g("s11", 3.6), 4.6)
    # s11: quicker around the tugs (no breath on the tugs themselves)
    ev.append(dict(t=g("s11", 3.75), inhale=1.0, hold=0.1, exhale=1.3, size=1.05, bub=1.0))
    ev.append(dict(t=g("s11", 6.6), inhale=0.95, hold=0.1, exhale=1.35, size=1.1, bub=1.0))
    ev.append(dict(t=g("s11", 9.3), inhale=1.0, hold=0.1, exhale=1.4, size=0.9, bub=1.0))
    gain = [(0.0, -9.0), (g("s01", 10.0), -9.0), (g("s02", 0.9), -60.0),                     # s01 faint, gone at the surface
            (w("s02", "it"), -60.0), (w("s02", "it") + 0.05, 0.0),
            (C.trans("s03")[0], 0.0), (C.trans("s03")[1] - 0.2, -60.0),                       # flatten into paper
            (C.trans("s04")[0] + 0.3, -60.0), (C.trans("s04")[1], 0.0),                       # back over the ink
            (C.end("s06") - 0.015, 0.0), (C.end("s06"), -60.0),                               # hard cut to black
            (C.trans("s07")[0] + 0.2, -60.0), (C.trans("s07")[1], 0.0),
            (g("s09", 4.0), 0.0), (g("s09", 4.4), -9.0), (g("s09", 7.1), -9.0), (g("s09", 7.4), 0.0),   # spiral
            (g("s11", 7.4), 0.0), (g("s11", 9.0), -60.0)]                                     # the camera leaves him
    if sync:
        ev = sync_breaths(ev, sync)
    return ev, gain


def breath_gain_at(gain, t):
    return float(np.interp(t, [p[0] for p in gain], [p[1] for p in gain]))


def hose_breath_events(C, rng=None):
    """s12: his breathing heard up the hose on deck until the knife - it STOPS at the cut."""
    rng = rng or np.random.default_rng(32)
    ev = S.periodic_breaths(C.g("s12", 0.25), C.w("s12", "cut") + 2.0, 4.0, rng, 0.06, 1.3, 1.7, 1.0, 0.0)
    return ev, C.w("s12", "cut")


def layers(C):
    g, w = C.g, C.w
    cut = w("s12", "cut")
    return dict(
        hiss=[dict(t0=g("s01", 5.2), t1=g("s02", 0.6), fin=0.9, fout=0.6, gain=-9.0),
              dict(t0=w("s02", "it") + 0.02, t1=C.trans("s03")[1], fin=0.25, fout=0.8, gain=-3.0),
              dict(t0=C.trans("s04")[0] + 0.3, t1=C.end("s06"), fin=0.9, fout=0.015, gain=0.0),
              dict(t0=C.trans("s07")[0] + 0.2, t1=g("s11", 9.0), fin=0.8, fout=1.6, gain=0.0)],
        hiss_duck=[(g("s09", 4.0), g("s09", 7.3), -9.0)],
        pump=[dict(t0=w("s02", "it") - 0.6, t1=g("s03", 6.5), spinup=1.6, rundown_at=None, gain=-9.0, fin=0.3, fout=1.5,
                   space="dusk_air"),
              dict(t0=g("s12", -0.2), t1=g("s12", 8.6), spinup=0.0, rundown_at=cut, rundown=3.0, open_after=cut, gain=-7.0,
                   fin=0.6, fout=0.9, space="night_air")],
        winch=[dict(t0=w("s12", "mine"), t1=g("s12", 9.4), rate=0.36, load=0.55, gain=-8.0, fin=0.15, fout=1.2,
                    space="night_air"),
               dict(t0=g("s14", -0.2), t1=w("s14", "bell") + 0.35, rate=0.47, load=0.85, gain=-10.0, fin=0.5, fout=0.08,
                    space="night_air")],
        bubbles=[dict(t0=g("s01", 7.8), t1=g("s02", 0.9), density=24.0, gain=-11.0, fin=0.8, fout=0.5),
                 dict(t0=g("s11", 7.2), t1=g("s11", 10.0), density=16.0, gain=-15.0, fin=1.0, fout=0.6)],
    )


def heartbeat_plan(C):
    """Beat times of the diver's heart after the cut (s12 end -> s14 start) and their strengths."""
    t0 = C.w("s12", "cut") + 0.9
    calm = C.w("s13", "calm")
    rise = C.g("s13", 9.0)
    end = C.g("s14", 0.6)
    beats = []
    t = t0
    while t < end:
        if t < calm:
            bpm = 76.0 - 22.0 * (t - t0) / (calm - t0)          # 76 -> 54 as he calms himself
        elif t < rise:
            bpm = 54.0 - 2.0 * (t - calm) / (rise - calm)
        else:
            bpm = 52.0 + 10.0 * (t - rise) / (end - rise)        # quickens as he rises
        beats.append(t)
        t += 60.0 / bpm
    st = []
    for b in beats:
        a = min(1.0, max(0.0, (b - t0) / 1.6)) ** 1.5           # emerges from under the air escape
        f = min(1.0, max(0.0, (end - b) / 1.2))
        st.append(0.35 + 0.65 * a * f if a > 0 else 0.0)
    return beats, st


# ============================================================================ acoustic map
UNDERWATER = ("underwater", "wreck")


def space_at(C, t):
    g = C.g
    pts = [(0.0, "paper"), (g("s01", 4.2), "underwater"), (g("s02", 0.9), "dusk_air"), (g("s03", 5.3), "underwater"),
           (C.trans("s03")[0] + 0.5, "paper"), (C.trans("s04")[0] + 0.6, "underwater"), (C.w("s06", "inside"), "wreck"),
           (C.end("s06"), "paper"), (C.trans("s07")[0] + 0.5, "wreck"), (C.start("s11"), "underwater"),
           (C.trans("s11")[0] + 0.7, "night_air"), (g("s12", 8.1), "underwater"), (C.start("s14"), "night_air"),
           (C.start("s16") - 0.5, "underwater"), (C.w("s16", "me") - 0.3, "paper")]
    sp = pts[0][1]
    for t0, name in pts:
        if t >= t0:
            sp = name
    return sp


DEPTH_PTS = None


def depth_points(C):
    """Depth 0 (surface) .. 1 (the wreck) for the beds, the score's sub and the muffle filter."""
    g = C.g
    return [(0.0, 0.0), (g("s01", 4.2), 0.45), (g("s01", 8.4), 0.4), (g("s02", 0.0), 0.15), (g("s02", 0.9), 0.0),
            (g("s03", 5.0), 0.0), (g("s03", 6.0), 0.15), (C.end("s03"), 0.72), (C.start("s05"), 0.95), (C.end("s06"), 1.0),
            (C.end("s10"), 1.0), (g("s11", 7.3), 0.95), (C.end("s11"), 0.2), (g("s12", 0.3), 0.0), (g("s12", 8.0), 0.0),
            (g("s12", 9.0), 0.3), (C.start("s13"), 0.95), (g("s13", 9.0), 1.0), (C.start("s14"), 0.55), (g("s14", 10.0), 0.1),
            (C.start("s15"), 0.0), (C.start("s16"), 0.25), (C.w("s16", "back"), 0.75), (C.end("s16"), 0.9)]


def depth_at(C, t):
    pts = depth_points(C)
    return float(np.interp(t, [p[0] for p in pts], [p[1] for p in pts]))


def muffle_fc(depth):
    """Low-pass cutoff for sounds heard through water and the helmet at a given depth."""
    return 2600.0 * math.pow(0.5, float(np.clip(depth, 0, 1)) * 0.85)


# ============================================================================ scene cues + merge
def scene_cues(C, log):
    """Cues exported by the scene modules (film clock), resolved to catalog names. Scenes that
    fail to import or whose cues() raise are logged and skipped."""
    from engine.render import scene_module
    out, have = [], set()
    for s in C.scenes:
        sid = s["id"]
        try:
            mod, T = scene_module(FILM, sid)
        except Exception as e:                        # noqa: BLE001 - a broken scene must not stop the mix
            log.append(dict(scene=sid, event="import_failed", error=f"{type(e).__name__}: {e}"[:200]))
            continue
        if mod is None or not hasattr(mod, "cues"):
            continue
        try:
            cl = list(mod.cues(T) or [])
        except Exception as e:                        # noqa: BLE001
            log.append(dict(scene=sid, event="cues_failed", error=f"{type(e).__name__}: {e}"[:200]))
            continue
        if cl:
            have.add(sid)
        for c in cl:
            try:
                text = c["sfx"]
                t = T.start + float(c["t"])
                name, params = S.resolve(text, sid, c.get("dur"))
                params.update(c.get("params") or {})
                out.append(dict(t=round(t, 4), text=text, name=name, params=params, gain_db=float(c.get("gain_db", 0.0)),
                                pan=float(c.get("pan", 0.0)), dur=c.get("dur"), scene=sid))
            except Exception as e:                    # noqa: BLE001
                log.append(dict(scene=sid, event="bad_cue", cue=str(c)[:120], error=str(e)[:120]))
    return out, have


def merge(C, mine, theirs, have, log, breath_sync=None, heart=None):
    """Designed cues + scene cues -> final cue list (see module doc). Scene bubble bursts while
    the breathing layer plays become breath sync points; scene heartbeats in s13 replace the
    designed beat times."""
    _, bgain = breath_events(C)
    final = [dict(c) for c in mine]
    for c in final:
        c["scene"] = C.scene_at(c["t"])
    # scenes with their own cues take over the picture-detail fallbacks
    kept = []
    for c in final:
        if c["kind"] == "fallback" and c["scene"] in have:
            log.append(dict(scene=c["scene"], event="fallback_dropped", t=c["t"], name=c["name"], label=c["label"]))
            continue
        kept.append(c)
    final = kept
    used = set()
    for sc in sorted(theirs, key=lambda x: x["t"]):
        if sc["name"] is None:
            log.append(dict(scene=sc["scene"], event="unresolved", t=sc["t"], text=sc["text"]))
            continue
        if sc["name"] in LAYER_SOUNDS:
            log.append(dict(scene=sc["scene"], event="covered_by_layer", t=sc["t"], text=sc["text"], name=sc["name"]))
            continue
        if sc["name"] == "exhaust_bubbles" and breath_sync is not None and breath_gain_at(bgain, sc["t"]) > -45.0:
            breath_sync.append(sc["t"])
            log.append(dict(scene=sc["scene"], event="breath_sync", t=sc["t"], text=sc["text"]))
            continue
        if sc["name"] == "heartbeat_deep" and heart is not None and sc["scene"] in ("s12", "s13", "s14"):
            heart.append(sc["t"])
            log.append(dict(scene=sc["scene"], event="heartbeat_sync", t=sc["t"], text=sc["text"]))
            continue
        best, bd = None, 1e9
        for i, c in enumerate(final):
            if i in used or c["src"] != "designed" or c["name"] != sc["name"] or c["scene"] != sc["scene"]:
                continue
            d = abs(c["t"] - sc["t"])
            if d <= MATCH_TOL.get(c["kind"], 0.5) and d < bd:
                best, bd = i, d
        if best is not None:
            c = final[best]
            used.add(best)
            if abs(c["t"] - sc["t"]) > 1e-3:
                log.append(dict(scene=sc["scene"], event="retimed", name=c["name"], label=c["label"], from_t=c["t"], to_t=sc["t"],
                                shift=round(sc["t"] - c["t"], 3), text=sc["text"]))
            c["t"] = sc["t"]
            c["matched"] = sc["text"]
            continue
        sp = S.spec(sc["name"])
        params = dict(sc["params"])
        dur = sc["dur"] if (sp.get("kind") == "sustained" and sc["name"] not in S.LENGTH_PARAM) else None
        nc = dict(t=sc["t"], name=sc["name"], gain_db=float(np.clip(sc["gain_db"], -24.0, 3.0)) - 1.0, kind="scene",
                  pan=float(np.clip(sc["pan"], -1, 1)), params=params, dur=dur, space=None, label=sc["text"][:40],
                  seed=1000 + len(final), bus="hits" if sp.get("hit") else "sfx", group=sc["name"], src="scene",
                  scene=sc["scene"])
        final.append(nc)
        log.append(dict(scene=sc["scene"], event="added", t=sc["t"], name=sc["name"], text=sc["text"]))
    return sorted(final, key=lambda c: c["t"])


def build(C=None, use_scenes=True):
    """-> dict(cues, log, have, breath_sync, heart)"""
    C = C or Clock()
    log = []
    mine = designed(C)
    theirs, have = (scene_cues(C, log) if use_scenes else ([], set()))
    bsync, heart = [], []
    cues = merge(C, mine, theirs, have, log, bsync, heart)
    return dict(cues=cues, log=log, have=sorted(have), breath_sync=sorted(bsync), heart=sorted(heart))
