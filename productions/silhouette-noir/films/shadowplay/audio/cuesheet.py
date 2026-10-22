"""SHADOW PLAY cue sheet: every designed sound on the film clock, built from the narration's
word anchors and the storyboard beats (docs/bible.md section 4).

    sync, notes = sync_points(scene_cues)    # named sync moments (film s), after picture retiming
    cues = build_cues(sync)                  # [{t, name, gain_db, pan, dur, params, seed, ...}]
    spans = sfx_spaces()                     # [(t0, t1, room, send_db)] reverb per stretch of film

Film time = scene start + scene-local time. The scenes have not been written yet, so every
picture beat is the storyboard's. When a scene file exports cues(T), its cues (free-text names
such as 'knife stab' or 'door slam') are mapped onto this sheet by keyword: a scene cue with the
same tag within +-1 s of a sync point moves that point to the picture (every SFX and score hit
built on it follows); mappable scene cues with no partner are added; the rest are reported.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from audio import dsp  # noqa: E402
from engine.timing import SceneTiming, timeline  # noqa: E402

FILM = "shadowplay"
RETIME_WINDOW = 1.0

# --------------------------------------------------------------------------- scene-cue mapping
# (pattern on the free-text cue name, tag, this film's sound, default params). First match wins.
KEYWORDS = [
    (r"\bcar door", "car_door", "car_door_close", {}),
    (r"\bcar\b.*(away|pull|leav|driv)|engine", "car", "car_away", {}),
    (r"lamp\s*switch|socket", "lamp_switch", "lamp_switch", {}),
    (r"lamp.*(crash|fall|knock)|crash", "crash", "lamp_crash", {}),
    (r"light.*(out|off)|snaps? out|goes dark", "light_out", "light_out", {}),
    (r"switch|light.*on|click on", "switch", "switch_click", {}),
    (r"bulb|flicker|filament", "bulb", "bulb_on", {}),
    (r"binocular", "binoculars", "binocular_lift", {}),
    (r"coat|flare", "coat", "coat_flare", {}),
    (r"collar|cloth", "cloth", "cloth_snap", {}),
    (r"sheet.*(tear|rip|slash)|(tear|rip).*sheet|fabric", "sheet_rip", "sheet_rip", dict(size=0.7)),
    (r"paper.*tear|tear", "tear", "tear_big", {}),
    (r"slash", "slash", "slash_whoosh", {}),
    (r"stab|knife", "stab", "knife_whoosh", {}),
    (r"pin|joint", "pin", "pin_creak", {}),
    (r"doll|puppet|rod", "doll", "doll_flutter", {}),
    (r"handle|knob", "handle", "handle_turn", {}),
    (r"burst|bursts open|kick", "burst", "door_burst", {}),
    (r"slam", "slam", "door_slam", {}),
    (r"key|lock", "key", "key_lock", {}),
    (r"hammer|pound|bang|fist", "hammer", "door_hammer", {}),
    (r"radio", "radio", "police_radio", {}),
    (r"whoop", "whoop", "siren_whoop", {}),
    (r"siren", "siren", "siren_whoop", {}),
    (r"flashlight|torch|beam", "torch", "flashlight_click", {}),
    (r"stair", "stairs", "wood_step", dict(stair=1)),
    (r"footstep|step|walk", "steps", "wood_step", {}),
    (r"umbrella", "umbrella", "umbrella_pass", {}),
    (r"\brain\b", "rain", "rain_street", {}),                      # the beds own the rain
    (r"whisk|strip", "whisk", "paper_slide", dict(length=0.2, tap=0, shape="out")),
    (r"card|rail", "card", "paper_slide", dict(length=0.24, tap=0, shape="in")),
    (r"count", "count", "count_ticks", {}),
    (r"match", "match", "match_strike", {}),
    (r"flame|blow", "flame", "flame_out", {}),
    (r"curtain|ring", "curtain", "curtain_rings", {}),
    (r"glint|lens", "glint", "glint", {}),
    (r"scream", "scream", "scream_pull", {}),
    (r"red line|line", "red_line", "red_line", {}),
    (r"grid|snap", "grid", "grid_snap", {}),
    (r"pop|land", "pop", "paper_pop", {}),
    (r"tap|typewriter", "pop", "paper_pop", {}),
    (r"flip", "flip", "paper_flip", {}),
    (r"heart|pulse", "heart", "heart_pulse", {}),
    (r"door", "door", "door_open", {}),
]


def classify(text):
    """Free-text scene cue name -> (tag, sound name, default params) or None."""
    from films.shadowplay.audio import sfx_shadowplay as S
    s = str(text).strip().lower()
    exact = s.replace(" ", "_") if S.exists(s.replace(" ", "_")) else None
    for pat, tag, name, params in KEYWORDS:
        if re.search(pat, s):
            return tag, exact or name, ({} if exact else dict(params))
    return (exact, exact, {}) if exact else None


# --------------------------------------------------------------------------- timing helpers
_T = {}


def T(sid):
    if sid not in _T:
        _T[sid] = SceneTiming(FILM, sid)
    return _T[sid]


def word(sid, w, n=0):
    """Film time of the n-th occurrence of a narration word in scene sid."""
    return T(sid).start + T(sid).at(w, n)


def g(sid, t):
    """Film time of scene-local time t."""
    return T(sid).start + t


def trans_window(sid):
    """(t0, t1) film time of the transition out of scene sid (centred on the cut), or None."""
    s = next(x for x in timeline(FILM)["scenes"] if x["id"] == sid)
    tr = s.get("trans_out")
    if not tr:
        return None
    cut = s["start"] + s["duration"]
    d = float(tr["dur"])
    return cut - d / 2, cut + d / 2


# --------------------------------------------------------------------------- sync points
def default_sync():
    """name -> dict(t=film s, tags=(...)) - the moments sound and score hit."""
    S = {}

    def put(name, t, *tags):
        S[name] = dict(t=round(float(t), 4), tags=tuple(tags))

    # s01 forty windows
    put("s01_strips", g("s01", 0.02), "whisk")
    put("s01_pops", g("s01", 0.30), "pop")
    put("s01_card", word("s01", "forty") - 0.24, "card")
    put("s01_grid", word("s01", "forty"), "grid", "pop")
    put("s01_flip", g("s01", 4.40), "flip")
    put("s01_lights", g("s01", 5.02), "lights", "switch", "bulb")
    put("s01_every", word("s01", "every"), "count")
    put("s01_heart", word("s01", "heart"), "heart")
    put("s01_rain", g("s01", 7.7), "rain")
    # s02 the watcher
    put("s02_win4", word("s02", "Four"))
    put("s02_win12", word("s02", "Twelve"))
    put("s02_win30", word("s02", "Thirty"))
    put("s02_through", g("s02", 6.7))
    put("s02_bino", word("s02", "watch"), "binoculars")
    put("s02_down", g("s02", 10.6))
    put("s02_up", g("s02", 12.4))
    put("s02_title_in", g("s02", 12.45), "title")
    put("s02_title_out", g("s02", 14.35), "title")
    put("s02_iris", trans_window("s02")[0], "iris")
    # s03 window nine
    put("s03_light_on", word("s03", "light"), "switch", "bulb")
    put("s03_arm", g("s03", 9.4))
    put("s03_stab1", g("s03", 10.337), "stab")
    put("s03_stab2", g("s03", 10.887), "stab")
    put("s03_stab3", g("s03", 11.437), "stab")
    put("s03_fall", g("s03", 11.9))
    put("s03_light_out", g("s03", 12.3), "light_out")
    put("s03_bino_down", g("s03", 13.6), "binoculars")
    put("s03_every", word("s03", "Every"))
    # s04 nothing
    put("s04_burst", g("s04", 0.03), "burst", "door")
    put("s04_body", word("s04", "body"))
    put("s04_blood", word("s04", "blood"))
    put("s04_woman", word("s04", "woman"))
    put("s04_street", g("s04", 5.5))
    put("s04_cop_torch", g("s04", 6.0), "torch")
    put("s04_dreamed", word("s04", "dreamed"))
    put("s04_car_away", g("s04", 9.4), "car")
    put("s04_bars", trans_window("s04")[0], "bars")
    # s05 again
    put("s05_light_on", word("s05", "Wednesday"), "switch", "bulb")
    put("s05_eleven", word("s05", "eleven"))
    put("s05_again", word("s05", "again"), "stab")
    put("s05_second", word("s05", "second"), "red_line")
    put("s05_arm", word("s05", "arm"), "slide")
    put("s05_scream", word("s05", "scream"), "scream")
    put("s05_pin1", g("s05", 11.8), "pin")
    put("s05_pin2", g("s05", 12.8), "pin")
    put("s05_last_stab", g("s05", 13.65), "stab")
    put("s05_slash", trans_window("s05")[0], "slash")
    # s06 crossing
    put("s06_coat", g("s06", 0.5), "coat")                      # the flare (peak of the swing)
    put("s06_collar", g("s06", 1.4), "cloth")
    put("s06_door", g("s06", 3.05), "door")
    put("s06_stairs", g("s06", 3.8), "stairs", "steps")
    put("s06_street", g("s06", 5.9), "street_door")
    put("s06_crane", g("s06", 7.0))
    put("s06_iris", trans_window("s06")[0], "iris")
    # s07 the show
    put("s07_door", g("s07", 0.15), "door")
    put("s07_match", g("s07", 0.95), "match")
    put("s07_lamp", word("s07", "lamp"))
    put("s07_sheet", word("s07", "sheet"))
    put("s07_dolls", word("s07", "dolls"), "doll")
    put("s07_lamp_on", word("s07", "show") - 0.16, "lamp_switch", "switch", "bulb")
    put("s07_show", word("s07", "show"))
    put("s07_flame_out", g("s07", 10.4), "flame")
    # s08 the other side
    put("s08_someone", word("s08", "Someone"))
    put("s08_glint", g("s08", 7.4), "glint", "binoculars")
    put("s08_wave", g("s08", 7.6))
    put("s08_light_off", word("s08", "watch"), "switch", "light_out")
    # s09 ninety seconds
    put("s09_ninety", word("s09", "ninety"))
    put("s09_lamp", word("s09", "light"), "lamp")
    put("s09_sheet", word("s09", "sheet"), "sheet")
    put("s09_believe", word("s09", "believe"), "doll")
    put("s09_show", word("s09", "show"))
    put("s09_hide", g("s09", 11.5), "cloth")
    put("s09_steps", g("s09", 10.1), "stairs", "steps")
    put("s09_feet_stop", g("s09", 13.35))
    put("s09_handle", g("s09", 13.65), "handle")
    # s10 the trap (wordless)
    put("s10_clack", g("s10", 0.95), "latch")
    put("s10_burst", g("s10", 1.0), "burst", "door")
    put("s10_stab1", g("s10", 2.05), "stab")
    put("s10_stab2", g("s10", 2.55), "stab")
    put("s10_stab3", g("s10", 3.05), "stab")
    put("s10_stab4", g("s10", 3.65), "stab")
    put("s10_doll", g("s10", 3.95), "doll")
    put("s10_slam", g("s10", 4.75), "slam")
    put("s10_key", g("s10", 4.92), "key")
    put("s10_hammer", g("s10", 5.55), "hammer")
    put("s10_crash", g("s10", 6.42), "crash")
    put("s10_dark", g("s10", 6.95), "light_out", "bulb")
    put("s10_sirens", g("s10", 7.5), "siren")
    put("s10_slide", g("s10", 8.1), "cloth")
    put("s10_tear", trans_window("s10")[0], "tear")
    # s11 forty dolls
    put("s11_torch", g("s11", 0.3), "torch")
    put("s11_found", word("s11", "forty"))
    put("s11_window", word("s11", "window"), "grid")
    put("s11_binoculars", word("s11", "binoculars"), "glint", "doll")
    put("s11_dissolve", trans_window("s11")[0])
    # s12 mostly
    put("s12_curtain", g("s12", 1.5), "curtain")
    put("s12_mostly", word("s12", "Mostly"))
    put("s12_part", g("s12", 4.5), "curtain")
    put("s12_new_window", g("s12", 5.1), "switch")
    put("s12_pullout", g("s12", 6.5))
    put("s12_glint", g("s12", 9.9), "glint")
    put("s12_dark", g("s12", 10.0), "lights")
    return S


# sustained cues that cover a stretch: a scene's per-event cues of this tag inside are 'covered'
def covered_spans(S):
    return [("stairs", S["s06_stairs"]["t"], S["s06_stairs"]["t"] + 2.1), ("steps", S["s06_stairs"]["t"] - 1.6, S["s06_stairs"]["t"] + 3.4),
            ("stairs", S["s09_steps"]["t"], S["s09_feet_stop"]["t"]), ("steps", 108.0, S["s09_feet_stop"]["t"]),
            ("steps", S["s04_burst"]["t"], S["s04_burst"]["t"] + 1.6), ("hammer", S["s10_hammer"]["t"] - 0.1, S["s10_sirens"]["t"] + 0.6),
            ("pop", 0.0, 1.6), ("siren", S["s10_sirens"]["t"] - 0.3, S["s11_dissolve"]["t"]),
            ("siren", S["s04_burst"]["t"], S["s04_bars"]["t"]), ("umbrella", S["s02_down"]["t"], S["s02_up"]["t"]),
            ("flame", S["s07_match"]["t"], S["s07_flame_out"]["t"] + 0.5), ("rain", 0.0, 1e9)]


def sync_points(scene_cues=None):
    """Default sync points, retimed to the picture by the scenes' own cues where they exist.
    Returns (sync {name: t}, notes {retimed, added, covered, unmapped})."""
    S = default_sync()
    notes = dict(retimed=[], added=[], covered=[], unmapped=[])
    claimed = set()
    sc = []
    for i, c in enumerate(scene_cues or []):
        k = classify(c.get("sfx", ""))
        sc.append((i, c, k))
    # retime: each sync point takes the nearest same-tag scene cue within the window
    for name, d in sorted(S.items(), key=lambda kv: kv[1]["t"]):
        best = None
        for i, c, k in sc:
            if k is None or i in claimed or k[0] not in d["tags"]:
                continue
            dt = abs(float(c["t"]) - d["t"])
            if dt <= RETIME_WINDOW and (best is None or dt < best[0]):
                best = (dt, i, c)
        if best is not None:
            _, i, c = best
            claimed.add(i)
            if abs(float(c["t"]) - d["t"]) > 1e-3:
                notes["retimed"].append(dict(sync=name, frm=d["t"], to=round(float(c["t"]), 4), cue=c.get("sfx")))
            d["t"] = round(float(c["t"]), 4)
    spans = covered_spans(S)
    extras = []
    for i, c, k in sc:
        if i in claimed:
            continue
        if k is None:
            notes["unmapped"].append(dict(t=c.get("t"), sfx=c.get("sfx"), scene=c.get("scene")))
            continue
        tag, nm, params = k
        if any(tag == st and a - 0.5 <= float(c["t"]) <= b + 0.5 for st, a, b in spans):
            notes["covered"].append(dict(t=c.get("t"), sfx=c.get("sfx"), by=tag))
            continue
        params = dict(params, **(c.get("params") or {}))
        extras.append(dict(t=float(c["t"]), name=nm, gain_db=float(c.get("gain_db", 0.0)) - 6.0, pan=float(c.get("pan", 0.0)),
                           dur=c.get("dur"), params=params, tag=tag, src="scene:" + str(c.get("scene"))))
        notes["added"].append(dict(t=c.get("t"), sfx=c.get("sfx"), as_=nm))
    return {k: v["t"] for k, v in S.items()}, dict(notes, extras=extras)


# s01's picture: window i (1..40, row-major, 5 across) pops in at pops + 0.03 * rank (window 9
# is the one that slides in on [forty]); the nine NIGHT windows switch on in LIGHT_ORDER
S01_LIGHT_ORDER = (4, 12, 30, 2, 19, 26, 7, 23, 37)
S01_COLS = (230.0, 385.0, 540.0, 695.0, 850.0)
S01_V_LINES = (152.5, 307.5, 462.5, 617.5, 772.5, 927.5)


def s01_pan(x):
    return round((x / 1080.0 - 0.5) * 1.6, 3)


def s01_pop_t(S, i):
    """Film time a window's pop is heard (the shape is ~40 % grown 20 ms after its start)."""
    rank = i - 1 - (1 if i > 9 else 0)
    return S["s01_pops"] + 0.03 * rank + 0.012


def s01_light_times(S):
    """(t, pan) of the nine windows switching on (after their slat has flipped)."""
    out = []
    for k, i in enumerate(S01_LIGHT_ORDER):
        r, col = divmod(i - 1, 5)
        out.append((max(S["s01_flip"] + 0.11 * r + 0.38, S["s01_lights"] + 0.075 * k), s01_pan(S01_COLS[col])))
    return sorted(out)


# --------------------------------------------------------------------------- the cue list
def build_cues(sync, extras=()):
    """Every SFX cue: {t, name, gain_db, pan, dur, params, seed, persp, send_db, bus}.
    persp: None | 'behind_door' | 'through_window' | 'hall_door' (applied by the mixer);
    send_db: extra reverb-send trim; bus: None (from the sound's spec) | 'hit' | 'sfx'."""
    S = sync
    cues = []

    def c(t, name, gain=0.0, pan=0.0, dur=None, persp=None, send_db=0.0, bus=None, seed=None, **params):
        cues.append(dict(t=round(float(t), 4), name=name, gain_db=float(gain), pan=float(pan), dur=dur, params=params,
                         persp=persp, send_db=send_db, bus=bus,
                         seed=seed if seed is not None else dsp.stable_seed(name, round(float(t), 3)) % 1000003))

    rng = dsp.rng_for("shadowplay_cues", 1)

    # ---------------------------------------------------------------- s01 forty windows
    # the grid's ink strips whisk in from the edges: verticals from the top (each at its own x),
    # horizontals from alternating sides
    t0 = S["s01_strips"] - 0.02
    for j, x in enumerate(S01_V_LINES):
        c(t0 + 0.02 + 0.05 * j, "paper_slide", -21.0, length=0.2, tap=0, shape="out", pan0=s01_pan(x), pan1=s01_pan(x))
    for j in range(9):
        a, b = (-0.85, 0.85) if j % 2 == 0 else (0.85, -0.85)
        c(t0 + 0.08 + 0.045 * j, "paper_slide", -21.5, length=0.22, tap=0, shape="out", pan0=a, pan1=b)
    # 39 cut-paper windows pop in row by row (0.03 s apart); window 9 shoots in along its row's
    # line from the right and lands on [forty]
    for i in [i for i in range(1, 41) if i != 9]:
        row, col = divmod(i - 1, 5)
        c(s01_pop_t(S, i), "paper_pop", -12.0 + rng.uniform(-2, 1.5), pan=-0.6 + 0.3 * col,
          pitch=round(1.25 - 0.055 * row, 3))
    c(S["s01_card"], "paper_slide", -9.0, length=0.24, tap=0, shape="in", pan0=0.95, pan1=s01_pan(S01_COLS[3]))
    c(S["s01_grid"] - 0.004, "paper_pop", -7.0, pan=s01_pan(S01_COLS[3]), pitch=0.85)
    c(S["s01_grid"] - 0.045, "grid_snap", -1.0)                  # the thock lands on [forty]
    c(S["s01_flip"] - 0.05, "paper_flip", -4.0)
    lt = s01_light_times(S)
    c(lt[0][0], "window_lights", -7.0, times=tuple(round(t - lt[0][0], 4) for t, _ in lt), pans=tuple(p for _, p in lt))
    c(S["s01_every"], "count_ticks", -13.0, n=8, gap=0.09)       # the counting glint, row by row
    c(S["s01_heart"], "heart_pulse", -2.0, gap=0.27)

    # ---------------------------------------------------------------- s02 the watcher
    c(S["s02_win4"] - 0.3, "phonograph_waltz", -13.0, pan=-0.25, dur=2.9)
    c(S["s02_bino"] - 0.57, "binocular_lift", -6.0, pan=0.1)      # eyecups meet the brow on [watch]
    c(S["s02_bino"] + 0.08, "glint", -13.0, pan=0.15)
    for k, (dt, d, p0, p1, gg) in enumerate(((-0.2, 2.4, -0.6, 0.4, -11.0), (0.5, 2.2, 0.7, -0.2, -13.0), (1.2, 2.0, -0.2, 0.6, -14.0))):
        c(S["s02_down"] + dt, "umbrella_pass", gg, dur=d, dist=0.7 + 0.05 * k, pan0=p0, pan1=p1)
    for k, (dt, p0, p1, gg) in enumerate(((0.0, -0.7, -0.1, -9.0), (0.07, 0.7, 0.1, -11.0), (0.15, -0.35, 0.25, -12.0))):
        c(S["s02_title_in"] + dt, "paper_slide", gg, length=0.42, pan0=p0, pan1=p1)
        c(S["s02_title_out"] + dt, "paper_slide", gg - 2.0, length=0.45, pan0=p1, pan1=-p0, tap=0)
    c(S["s02_iris"] + 0.15, "iris_close", -9.0)

    # ---------------------------------------------------------------- s03 window nine
    c(S["s03_light_on"] - 0.05, "switch_click", 6.0, pan=0.05, dist=0.3, bus="hit")
    c(S["s03_light_on"], "bulb_on", 2.0, pan=0.05, dist=0.3, bus="hit")
    c(S["s03_light_on"] + 0.2, "bulb_hum", -30.0, dur=S["s03_light_out"] - S["s03_light_on"] - 0.2, persp="through_window")
    c(S["s03_stab3"] + 0.01, "paper_pop", -10.0, pitch=0.55)       # the red cut-paper splash
    c(S["s03_light_out"], "light_out", 7.0, pan=0.05, dist=0.3, bus="hit")
    c(S["s03_bino_down"], "binocular_lift", -9.0, pan=0.1, lower=1)

    # ---------------------------------------------------------------- s04 nothing
    c(S["s04_burst"], "door_burst", 0.0, pan=-0.1)
    c(S["s04_burst"] + 0.22, "flashlight_click", -9.0, pan=-0.35)
    c(S["s04_burst"] + 0.42, "flashlight_click", -10.0, pan=0.35)
    c(S["s04_burst"] + 0.25, "steps_seq", -9.0, dur=1.4, kind="floor", who="him", weight=0.9, rate=2.8, pan0=-0.2, pan1=0.3, g0=0.0, g1=-4.0)
    c(S["s04_burst"] + 0.55, "siren_whoop", -7.0, pan=0.35, dist=0.65, persp="through_window")
    c(S["s04_burst"] + 0.9, "police_radio", -9.0, pan=0.4, dist=0.5, persp="through_window")
    for k, nm in enumerate(("s04_body", "s04_blood", "s04_woman")):
        c(S[nm] - 0.25, "wood_step", -15.0, pan=(-0.3, 0.1, 0.35)[k], who="him", weight=0.8, creak=0.6, stair=0)
    c(S["s04_street"] + 0.1, "police_radio", -8.0, pan=0.3, dist=0.25)
    c(S["s04_street"] - 0.1, "engine_idle", -19.0, pan=0.2, dur=S["s04_car_away"] - S["s04_street"] + 0.4)
    c(S["s04_cop_torch"], "flashlight_click", -9.0, pan=0.25)
    c(S["s04_dreamed"] - 0.35, "car_door_close", -11.0, pan=0.3)
    c(S["s04_car_away"], "car_away", -11.0, pan=0.2, dur=3.2)
    c(S["s04_car_away"] + 0.5, "siren_whoop", -9.0, pan=0.3, dist=0.55)
    c(S["s04_bars"] + 0.15, "bars_wipe", -8.0)

    # ---------------------------------------------------------------- s05 again (split screen)
    for k, (dt, pan) in enumerate(((0.0, -0.35), (0.012, 0.35))):
        c(S["s05_light_on"] - 0.05 + dt, "switch_click", -3.0, pan=pan, dist=0.45, seed=531 + k)
        c(S["s05_light_on"] + dt, "bulb_on", -6.0, pan=pan, dist=0.45, seed=541 + k)
    c(S["s05_light_on"] + 0.2, "bulb_hum", -32.0, dur=S["s05_slash"] - S["s05_light_on"], persp="through_window")
    for k, pan in enumerate((-0.35, 0.35)):
        c(S["s05_again"] - 0.13 + 0.008 * k, "knife_whoosh", -13.0, pan=pan, seed=551 + k)
    c(S["s05_second"], "red_line", -8.0)
    c(S["s05_arm"], "paper_slide", -6.0, length=0.42, pan0=0.0, pan1=0.0)
    c(S["s05_scream"] + 0.21 - 0.95, "scream_pull", -2.0, length=0.95)      # cut dead 0.21 s after [scream]
    c(S["s05_pin1"], "pin_creak", -7.0, length=0.6)
    c(S["s05_pin2"], "pin_creak", -2.0, length=0.9, seed=77)
    c(S["s05_last_stab"] - 0.13, "knife_whoosh", -7.0)
    c(S["s05_slash"], "slash_whoosh", -2.0)

    # ---------------------------------------------------------------- s06 crossing
    c(S["s06_coat"] - 0.45, "coat_flare", -1.0)
    c(S["s06_collar"] - 0.1, "cloth_snap", -9.0, pan=0.1)
    c(S["s06_door"] - 1.0, "steps_seq", -12.0, dur=0.95, kind="floor", who="her", weight=0.55, rate=3.2, pan0=-0.1, pan1=0.3)
    c(S["s06_door"], "door_open", -9.0, pan=0.35)
    c(S["s06_door"] + 0.6, "door_close", -10.0, pan=0.4)
    c(S["s06_stairs"], "stair_steps", -5.0, dur=2.1, who="her", rate=4.6, d0=0.15, d1=0.8, spin=0.6, creak=0.3)
    c(S["s06_street"] - 0.2, "door_open", -12.0, pan=-0.2)
    c(S["s06_street"], "steps_seq", -8.0, dur=1.3, kind="wet", rate=2.8, weight=0.5, pan0=-0.35, pan1=0.4)
    c(S["s06_iris"] + 0.1, "iris_close", -11.0, rect=1)

    # ---------------------------------------------------------------- s07 the show
    c(S["s07_door"], "door_creak", -8.0, pan=-0.3)
    c(S["s07_door"] + 0.45, "steps_seq", -13.0, dur=1.0, kind="floor", who="her", weight=0.45, rate=1.7, creak=0.5, pan0=-0.3, pan1=0.0)
    c(S["s07_match"], "match_strike", -5.0, pan=0.05)
    c(S["s07_match"] + 0.25, "flame_flicker", -24.0, dur=S["s07_flame_out"] - S["s07_match"] - 0.2)
    c(S["s07_dolls"], "doll_flutter", -16.0, pan=0.2, length=0.5)
    c(S["s07_lamp_on"] - 0.085, "lamp_switch", -3.0, pan=0.1)      # the snap lands on the sync point
    c(S["s07_lamp_on"], "bulb_on", -5.0, pan=0.1)
    c(S["s07_flame_out"], "flame_out", -10.0, pan=0.05)
    c(S["s07_flame_out"] + 0.5, "steps_seq", -13.0, dur=1.2, kind="floor", who="her", weight=0.5, rate=2.0, pan0=0.0, pan1=0.35)

    # ---------------------------------------------------------------- s08 the other side
    c(S["s08_glint"], "glint", -9.0, pan=0.1)
    c(S["s08_light_off"] - 0.006, "switch_click", 6.0, pan=0.1, dist=1.0, bus="hit")

    # ---------------------------------------------------------------- s09 ninety seconds
    c(S["s09_ninety"] + 0.8, "steps_seq", -11.0, dur=2.2, kind="floor", who="her", weight=0.55, rate=3.6, pan0=-0.3, pan1=0.3)
    c(S["s09_lamp"] - 0.3, "lamp_set", -6.0, pan=0.15)                # the tripod lands on [light]
    c(S["s09_sheet"] - 0.27, "sheet_snap", -6.0)                      # taut on [sheet]
    c(S["s09_believe"] - 0.09, "doll_clamp", -6.0, pan=0.1)           # the clamp on [believe]
    c(S["s09_believe"] + 0.25, "rod_tap", -13.0, pan=0.15)
    c(S["s09_hide"], "cloth_rustle", -10.0, pan=-0.4, length=0.8)
    c(S["s09_steps"], "stair_steps", -5.0, dur=S["s09_feet_stop"] - S["s09_steps"], who="him", rate=1.8, d0=0.95, d1=0.2,
      spin=0.25, creak=0.6, persp="hall_door")
    c(S["s09_feet_stop"] - 0.4, "breath", -16.0, pan=-0.4, kind="in", length=0.4)
    c(S["s09_handle"], "handle_turn", 5.0, pan=-0.1, length=S["s10_clack"] - S["s09_handle"])

    # ---------------------------------------------------------------- s10 the trap
    c(S["s10_burst"], "door_burst", 4.0, pan=-0.2)
    for k, dt in enumerate((0.15, 0.45, 0.75)):
        c(S["s10_burst"] + dt, "wood_step", -6.0 - (k % 2), pan=-0.1 + 0.15 * k, who="him", weight=1.0, creak=0.3, stair=0)
    for k, nm in enumerate(("s10_stab1", "s10_stab2", "s10_stab3", "s10_stab4")):
        c(S[nm] - 0.13, "knife_whoosh", -3.0, pan=(0.1, -0.1, 0.15, 0.0)[k])
        c(S[nm], "sheet_rip", 1.5 + 0.4 * k, pan=(0.15, -0.05, 0.2, 0.05)[k], size=(0.35, 0.55, 0.75, 1.0)[k])
    c(S["s10_doll"], "doll_flutter", -8.0, pan=0.2, length=0.6)
    c(S["s10_doll"] + 0.2, "rod_tap", -9.0, pan=0.25)
    c(S["s10_slam"] - 0.11, "door_slam", 4.0, pan=0.0)               # the slab hits on the sync point
    c(S["s10_key"], "key_lock", 3.0, pan=0.1)
    c(S["s10_hammer"], "door_hammer", 2.0, dur=S["s10_crash"] - S["s10_hammer"] + 0.1, rate=3.6)
    c(S["s10_crash"] - 0.17, "lamp_crash", 4.0, pan=0.0, persp="behind_door", pop=0)
    c(S["s10_crash"] + 0.12, "bulb_flicker", -4.0, persp="behind_door")
    c(S["s10_dark"], "bulb_pop", 0.0, persp="behind_door")
    c(S["s10_dark"] + 0.3, "door_hammer", -1.0, dur=0.62, rate=3.2, seed=1010)
    c(S["s10_slide"], "cloth_slide", -7.0, length=1.3)
    c(S["s10_slide"] + 1.45, "keys", -16.0, pan=0.15)
    c(S["s10_slide"] + 1.8, "breath", -11.0, kind="out", length=1.2)
    c(S["s10_tear"], "tear_big", -4.0)

    # ---------------------------------------------------------------- s11 forty dolls
    c(S["s11_torch"], "flashlight_click", -8.0, pan=-0.2)
    c(S["s11_found"] + 1.0, "doll_flutter", -17.0, pan=0.3, length=0.8)
    c(S["s11_window"] - 0.045, "grid_snap", -4.0)
    c(S["s11_binoculars"] + 0.05, "glint", -12.0, pan=0.05)

    # ---------------------------------------------------------------- s12 mostly
    c(S["s12_curtain"], "curtain_rings", -6.0, length=0.95)
    c(S["s12_part"], "curtain_rings", -9.0, part=1)
    c(S["s12_part"] + 0.35, "glint", -15.0, pan=-0.1)
    c(S["s12_new_window"], "switch_click", 3.0, pan=0.3, dist=0.9)
    c(S["s12_glint"], "glint", -7.0, pan=0.0)
    c(S["s12_dark"] + 0.1, "window_lights", -9.0, off=1, n=9, span=1.6)

    for e in extras:
        c(e["t"], e["name"], e["gain_db"], pan=e["pan"], dur=e.get("dur"), **(e.get("params") or {}))
        cues[-1]["src"] = e.get("src")
    return sorted(cues, key=lambda x: x["t"])


# --------------------------------------------------------------------------- SFX rooms by time
def sfx_spaces(sync):
    """[(t0, t1, room kind, send dB)] - the reverb every SFX cue is sent to, by film time."""
    S = sync
    return [
        (0.0, 9.0, "plate", -24.0),                       # s01 Bass graphics: a touch of plate
        (9.0, S["s02_through"] + 0.5, "street", -14.0),   # the facade across the street
        (S["s02_through"] + 0.5, S["s02_down"], "her_room", -16.0),
        (S["s02_down"], S["s02_up"] + 0.2, "street", -13.0),
        (S["s02_up"] + 0.2, 24.5, "plate", -22.0),        # title graphics
        (24.5, 41.0, "her_room", -16.0),                  # s03 her window (across-street sounds carry their own distance)
        (41.0, S["s04_street"], "apt9", -12.0),
        (S["s04_street"], 52.5, "street", -12.0),
        (52.5, 66.5, "her_room", -18.0),                  # s05 split screen through her binoculars
        (66.5, S["s06_stairs"], "her_room", -14.0),
        (S["s06_stairs"], S["s06_street"], "stairwell", -9.0),
        (S["s06_street"], 79.5, "street", -12.0),
        (79.5, S["s10_slam"], "apt9", -12.0),
        (S["s10_slam"], 131.5, "hallway", -11.0),
        (131.5, 141.5, "killer", -15.0),
        (141.5, S["s12_pullout"] + 1.5, "her_room", -15.0),
        (S["s12_pullout"] + 1.5, 153.5, "street", -13.0),
    ]


if __name__ == "__main__":
    import json
    sync, notes = sync_points([])
    cues = build_cues(sync)
    print(json.dumps({k: v for k, v in sorted(sync.items(), key=lambda kv: kv[1])}, indent=0)[:3000])
    print(len(cues), "cues")
