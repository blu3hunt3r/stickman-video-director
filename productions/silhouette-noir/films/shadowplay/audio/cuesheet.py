"""SHADOW PLAY cue sheet: every designed sound on the film clock, hung on the final scenes' own
cues and the narration's word anchors.

    sync, notes = sync_points(scene_cues)    # named sync moments (film s), claimed from the scenes' cues
    cues = build_cues(sync)                  # [{t, name, gain_db, pan, dur, params, seed, ...}]
    spans = sfx_spaces(sync)                 # [(t0, t1, room, send_db)] reverb per stretch of film
    gaps = sfx_silences(sync)                # [(t0, t1, fade_out, fade_in)] where every SFX and bed stops

Film time = scene start + scene-local time. Every scene exports cues(T) (free-text names such as
'the door SLAMS'); each one is claimed by a sync point here - by its own text (SCENE_SYNC_A / _B,
at the scene's time) or, for s01 / s05, by keyword tag - within +-1 s, and the point moves to the
cue's time (every SFX and score hit built on it follows). Scene cues no point claims are covered
by a sustained cue, added by keyword (-6 dB) or reported unmapped; a text claim that finds no cue
is reported missing.
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
    (r"\(score\)|^score:|muted brass stab|string sting|string swell|strings? (lift|swell)", "score", "__score__", {}),
    (r"\bcar door", "car_door", "car_door_close", {}),
    (r"\bcar\b.*(away|pull|leav|driv)|engine", "car", "car_away", {}),
    (r"rewind|projector", "rewind", "rewind", {}),
    (r"match (strike|scrape)|strikes? a match", "match", "match_strike", {}),
    (r"lamp\s*switch|socket", "lamp_switch", "lamp_switch", {}),
    (r"lamp.*(crash|fall|knock)|crash", "crash", "lamp_crash", {}),
    (r"lamp stand|tripod", "lamp", "lamp_set", {}),
    (r"street lamp dies|lamp dies", "lamp_die", "lamp_die", {}),
    (r"light.*\b(out|off)\b|snaps? out|goes dark", "light_out", "light_out", {}),
    (r"flashgun|flash ?bulb fires", "flash", "flashgun", {}),
    (r"flashbulb ejected|bulb ejected", "eject", "bulb_eject", {}),
    (r"flashlight|torch|beam", "torch", "flashlight_click", {}),
    (r"timer light|switch|light.*\bon\b|click on", "switch", "switch_click", {}),
    (r"fuse", "fuse", "fuse_click", {}),
    (r"fizz|stutter", "fizz", "electric_fizz", {}),
    (r"bulb|flicker|filament", "bulb", "bulb_on", {}),
    (r"focus ring", "focus", "focus_click", {}),
    (r"binocular", "binoculars", "binocular_lift", {}),
    (r"footstep|\bsteps?\b|walk|running|heels? (splash|pivot)", "steps", "wood_step", {}),
    (r"door.*(burst|kick)|burst|kicked", "burst", "door_burst", {}),
    (r"\bslams?\b", "slam", "door_slam", {}),
    (r"door creaks|creaks open", "door", "door_creak", {}),
    (r"lobby door|door:|door swings", "door", "door_open", {}),
    (r"coat|flare", "coat", "coat_flare", {}),
    (r"clothes pins pop|pins pop", "pins", "pins_pop", {}),
    (r"pins? rasp|rasp along", "rasp", "pins_rasp", {}),
    (r"dolls rustle|draft", "dolls", "dolls_rustle", {}),
    (r"sheet.*(tear|rip|slash)|(tear|rip).*sheet|cloth rip|knife punches|fabric|drape", "sheet_rip", "sheet_rip", dict(size=0.7)),
    (r"collar|cloth", "cloth", "cloth_snap", {}),
    (r"paper.*tear|tear", "tear", "tear_big", {}),
    (r"slash", "slash", "slash_whoosh", {}),
    (r"stab|knife", "stab", "knife_whoosh", {}),
    (r"splash|splat", "splash", "paper_splash", {}),
    (r"fold|slump", "fold", "body_fold", {}),
    (r"rod creak|arm (rises|cocks)", "creak", "pin_creak", dict(length=0.5)),
    (r"\bpins?\b|joint", "pin", "pin_creak", {}),
    (r"doll|puppet|\brod\b", "doll", "doll_flutter", {}),
    (r"handle|knob|lever", "handle", "handle_turn", {}),
    (r"latch", "latch", "handle_turn", {}),
    (r"key|lock|bolt", "key", "key_lock", {}),
    (r"hammer|pound|bang|fist", "hammer", "door_hammer", {}),
    (r"radio", "radio", "police_radio", {}),
    (r"whoop", "whoop", "siren_whoop", {}),
    (r"siren", "siren", "siren_whoop", {}),
    (r"stair", "stairs", "wood_step", dict(stair=1)),
    (r"umbrella", "umbrella", "umbrella_pass", {}),
    (r"\brain\b", "rain", "rain_street", {}),                      # the beds own the rain
    (r"whisk|strip", "whisk", "paper_slide", dict(length=0.2, tap=0, shape="out")),
    (r"card|rail", "card", "paper_slide", dict(length=0.24, tap=0, shape="in")),
    (r"slide", "slide", "paper_slide", dict(length=0.45)),
    (r"count", "count", "count_ticks", {}),
    (r"match", "match", "match_strike", {}),
    (r"flame|blow", "flame", "flame_out", {}),
    (r"curtain|\brings?\b", "curtain", "curtain_rings", {}),
    (r"glint|lens", "glint", "glint", {}),
    (r"scream", "scream", "scream_pull", {}),
    (r"chatter", "chatter", "chatter", {}),
    (r"meow", "meow", "cat_meow", {}),
    (r"sob", "sobs", "sobbing", {}),
    (r"breath", "breath", "breathing", {}),
    (r"whoosh|swish|whip", "swish", "swish", {}),
    (r"music box", "music_box", "music_box", {}),
    (r"string|swell|\bnotes?\b|chord|music|pizz", "score", "__score__", {}),   # the score's cues
    (r"pencil|red line|line", "red_line", "red_line", {}),
    (r"grid|snap", "grid", "grid_snap", {}),
    (r"pop|land", "pop", "paper_pop", {}),
    (r"\btaps?\b|typewriter", "pop", "paper_pop", {}),
    (r"flip", "flip", "paper_flip", {}),
    (r"heart|pulse", "heart", "heart_pulse", {}),
    (r"thud|knock|bump", "thud", "wall_bump", {}),
    (r"creak", "creak", "board_creak", {}),
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

# --------------------------------------------------------------------------- the final scenes' cues
# (sync name, scene-local time, regex on the scene cue's text that claims it, fallback tags). The
# times are the scenes' own; a scene that moves a cue moves the point (and every sound on it).
SCENE_SYNC_A = (
    ("s02", (
        ("s02_win4", 0.800, r"window 4", ("switch",)),                  # the dancer's lamp, on [Four]
        ("s02_dance", 0.920, r"pirouette", ()),
        ("s02_win12", 2.785, r"chatter", ()),                           # [Twelve]
        ("s02_meow", 3.800, r"meow", ()),
        ("s02_tail", 4.051, r"tail flick", ()),
        ("s02_win30", 5.351, r"sobbing", ()),                           # [cries]
        ("s02_pull", 6.500, r"pulls back", ()),
        ("s02_through", 8.350, r"rain on the pane close up", ()),
        ("s02_bino", 9.131, r"binoculars lifted", ("binoculars",)),
        ("s02_glint", 9.541, r"glint", ("glint",)),
        ("s02_out", 10.400, r"push through the pane", ()),
        ("s02_down", 10.900, r"street far below", ()),
        ("s02_up", 11.993, r"whip tilt", ()),
        ("s02_title_in", 12.450, r"title SHADOW", ()),
        ("s02_title_in2", 12.530, r"title PLAY", ()),
        ("s02_title_out", 14.400, r"focus ring", ()),
    )),
    ("s03", (
        ("s03_hush", 0.600, r"binocular hush", ()),
        ("s03_light_on", 7.157, r"far lamp switch", ("switch", "bulb")),
        ("s03_turn", 8.450, r"doll turning", ("doll",)),
        ("s03_arm", 9.000, r"arm rises", ()),
        ("s03_stab1", 9.850, r"stab 1", ("stab",)),
        ("s03_stab2", 10.250, r"stab 2", ("stab",)),
        ("s03_stab3", 10.650, r"stab 3", ("stab",)),                    # + the RED splash
        ("s03_fall", 10.850, r"she falls", ("fold",)),
        ("s03_light_out", 12.300, r"light snaps out", ("light_out",)),
        ("s03_reverse", 13.000, r"reverse: lens", ()),
        ("s03_bino_down", 14.750, r"binoculars lowered", ("binoculars",)),
        ("s03_every", 15.150, r"stops breathing", ()),                  # [Every]
        ("s03_heart", 16.600, r"heartbeat", ("heart",)),
    )),
    ("s04", (
        ("s04_dark", 0.000, r"dark room", ()),
        ("s04_burst", 0.150, r"door kicked open", ("burst", "door")),
        ("s04_torch1", 0.270, r"^torch clicks on", ()),
        ("s04_torch2", 0.965, r"second torch", ()),
        ("s04_body", 2.704, r"boot stops", ()),                         # [body]
        ("s04_blood", 3.516, r"beam sweeps the wall", ()),              # [blood]
        ("s04_woman", 4.480, r"rain against the bare window", ()),      # [woman]
        ("s04_street", 5.600, r"outside: rain hiss", ()),
        ("s04_raise", 7.200, r"torch raised", ()),
        ("s04_finds", 8.200, r"beam finds her: a sharp string", ()),
        ("s04_dreamed", 8.963, r"she steps back", ()),                  # [dreamed]
        ("s04_car_away", 9.950, r"police car pulls away", ("car",)),
        ("s04_torch_off", 10.200, r"torch clicks off", ()),
        ("s04_walk", 10.700, r"walking away", ()),
    )),
)

SCENE_SYNC_B = (
    ("s06", (
        ("s06_grab", -0.300, r"hook creaks", ()),
        ("s06_coat", 0.620, r"coat FLARES", ("coat",)),
        ("s06_land", 1.300, r"coat lands", ()),
        ("s06_collar", 1.900, r"collar flicked", ("cloth",)),
        ("s06_heels", 2.300, r"three quick heel steps", ()),
        ("s06_door", 2.810, r"door: latch", ("door",)),
        ("s06_stairs", 3.300, r"stairwell: heels", ("stairs",)),
        ("s06_spiral", 3.300, r"Vertigo arpeggio", ()),
        ("s06_street", 4.720, r"drumming on parked cars", ()),
        ("s06_run", 4.850, r"heels splash", ()),
        ("s06_lobby", 6.900, r"lobby door", ()),
        ("s06_crane", 7.200, r"crane up", ()),
    )),
    ("s07", (
        ("s07_room", -0.400, r"room tone: an empty flat", ()),
        ("s07_door", -0.050, r"door creaks open", ("door",)),
        ("s07_steps", 0.620, r"two careful steps", ()),
        ("s07_match", 1.430, r"match strike", ("match",)),
        ("s07_burn", 1.570, r"match burning", ()),
        ("s07_lamp", 3.084, r"glass tick", ()),                         # [lamp]
        ("s07_dolls", 5.627, r"doll stirs", ("doll",)),
        ("s07_flame_out", 7.120, r"match shaken out", ("flame",)),
        ("s07_lamp_on", 9.632, r"lamp switch: a hard click", ("lamp_switch",)),
        ("s07_swell", 9.672, r"low swell under the giant shadow", ()),
        ("s07_to_window", 10.550, r"steps toward the window", ()),
        ("s07_glass", 11.280, r"quick steps to the glass", ()),
    )),
    ("s08", (
        ("s08_steps", 4.350, r"floorboard, barely", ()),
        ("s08_glint", 6.523, r"binocular glint", ("glint",)),
        ("s08_light_off", 13.307, r"switch click, far, across", ("switch",)),
    )),
    ("s09", (
        ("s09_pivot", 0.620, r"heels pivot", ()),
        ("s09_run", 0.950, r"fast footsteps across the room", ()),
        ("s09_lamp_lift", 2.250, r"lamp stand lifted", ()),
        ("s09_doll", 3.100, r"doll yanked", ()),
        ("s09_lamp", 5.904, r"lamp stand set down", ()),                # [light]
        ("s09_rasp", 6.526, r"rasp along the wire", ()),
        ("s09_believe", 9.039, r"spring clamp", ()),                    # [believe]
        ("s09_hide_run", 9.450, r"footsteps round the sheet", ()),
        ("s09_wall", 11.150, r"back meets the wall", ()),
        ("s09_steps", 12.000, r"start up the stairs", ()),
        ("s09_timer", 12.250, r"timer light", ()),
        ("s09_feet_stop", 13.350, r"footsteps stop", ()),
        ("s09_handle", 13.520, r"handle begins to turn", ("handle",)),
    )),
    ("s10", (
        ("s10_creak", 0.000, r"creak continues", ()),
        ("s10_clack", 0.610, r"latch clicks free", ("latch",)),
        ("s10_burst", 1.000, r"door BURSTS", ("burst",)),
        ("s10_brass", 1.020, r"muted brass stab \(score\)", ()),
        ("s10_run", 1.300, r"heavy running footsteps", ()),
        ("s10_stab1", 2.020, r"punches through the sheet: a cloth rip", ()),
        ("s10_stab2", 2.420, r"through the sheet again", ()),
        ("s10_rip", 2.820, r"long tearing rip", ()),
        ("s10_pins", 3.000, r"clothes pins pop", ()),
        ("s10_hum", 3.420, r"bare bulb's hum", ()),
        ("s10_her", 4.200, r"quick soft footsteps", ()),
        ("s10_whip", 5.000, r"whips round: coat swish", ()),
        ("s10_slam", 5.000, r"door SLAMS", ("slam",)),
        ("s10_key", 5.140, r"key turns", ("key",)),
        ("s10_bolt", 5.340, r"deadbolt", ()),
        ("s10_body", 5.380, r"body slams into the door", ()),
        ("s10_hammer", 5.600, r"fists hammering", ("hammer",)),
        ("s10_stride", 6.500, r"stride away", ()),
        ("s10_crash", 6.620, r"lamp CRASHES", ("crash",)),
        ("s10_fizz", 6.700, r"electric fizz", ()),
        ("s10_dark", 7.250, r"fuse goes", ("fuse",)),
        ("s10_sirens", 7.600, r"sirens arriving", ("siren",)),
        ("s10_slide", 7.950, r"coat slides down the door", ()),
        ("s10_breath", 9.500, r"breathing, shaking", ()),
    )),
    ("s11", (
        ("s11_strobe", -0.500, r"police light bar", ()),
        ("s11_dolls", -0.350, r"forty paper dolls rustle", ()),
        ("s11_torch", 0.320, r"torch switch click", ("torch",)),
        ("s11_sweep", 1.000, r"torch beam sweeps", ()),
        ("s11_flash", 3.910, r"flashgun", ("flash",)),
        ("s11_window", 4.030, r"facade print", ()),                     # [window]
        ("s11_eject", 4.280, r"flashbulb ejected", ()),
        ("s11_finds", 5.900, r"beam finds her: paper flutter", ()),
        ("s11_push", 6.000, r"low strings swell under the push", ()),
    )),
    ("s12", (
        ("s12_rain", -0.600, r"radiator ticks", ()),
        ("s12_bino", 1.360, r"binoculars set down", ()),
        ("s12_take", 1.950, r"rings shiver", ()),
        ("s12_curtain", 2.050, r"rings run along the rod", ("curtain",)),
        ("s12_home", 2.920, r"knock home", ()),
        ("s12_part", 4.250, r"drape parted", ()),
        ("s12_new_window", 4.720, r"light switch clicks on, far and small", ()),
        ("s12_lift", 7.200, r"strings lift", ()),
        ("s12_pullout", 7.950, r"wet hush", ()),
        ("s12_glint", 9.255, r"tiny bright glint", ("glint",)),
        ("s12_lamp_dies", 10.000, r"street lamp dies", ()),
        ("s12_end", 11.500, r"glint winks out", ()),
    )),
)
# s12: the last windows going dark, in order: (window, scene-local t, the scene's pan)
S12_DARK = ((37, 10.300, -0.5), (30, 10.415, 1.0), (26, 10.524, -1.0), (23, 10.627, 0.0), (19, 10.725, 0.5),
            (12, 10.816, -0.5), (14, 10.902, 0.5), (2, 10.982, -0.5), (7, 11.055, -0.5), (4, 11.123, 0.5))


# --------------------------------------------------------------------------- sync points
def default_sync():
    """name -> dict(t=film s, tags=(...)) - the moments sound and score hit."""
    S = {}

    def put(name, t, *tags, txt=None):
        S[name] = dict(t=round(float(t), 4), tags=tuple(tags), txt=txt)

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
    # s02 - s04 and s06 - s12: one sync point per final scene cue, claimed by its own text (txt) at
    # the scene's time; the sound design below hangs off these names
    for sid, rows in SCENE_SYNC_A:
        for name, t, txt, tags in rows:
            put(name, g(sid, t), *tags, txt=txt)
    put("s02_iris", trans_window("s02")[0], "iris")
    put("s04_bars", trans_window("s04")[0], "bars")
    # s05 again
    # (the replayed show runs on _lib_shadow_show's clock: show time 0 = [again] - 2.65)
    u0 = word("s05", "again") - 2.65
    put("s05_light_tue", word("s05", "On"), "switch", "bulb")       # Tuesday, the top panel
    put("s05_light_on", word("s05", "Wednesday"), "switch", "bulb")  # Wednesday, the bottom
    put("s05_eleven", word("s05", "eleven"))
    put("s05_turn", u0 + 0.45, "doll")
    put("s05_raise", u0 + 1.00, "creak")
    put("s05_stab1", u0 + 1.85, "stab")
    put("s05_stab2", u0 + 2.25, "stab")
    put("s05_again", u0 + 2.65, "stab")                             # the third stab lands on [again]
    put("s05_splash", u0 + 2.65, "splash")
    put("s05_fall", u0 + 2.85, "fold")
    put("s05_light_out", u0 + 4.30, "light_out")
    put("s05_rewind", word("s05", "Same"), "rewind")
    put("s05_second", word("s05", "second"), "red_line")
    put("s05_captions", word("s05", "arm") - 0.34, "whisk")
    put("s05_arm", word("s05", "arm"), "slide")
    put("s05_slowmo", word("s05", "scream") - 0.31, "stab", "score")
    put("s05_scream", word("s05", "scream"), "scream")
    put("s05_people", word("s05", "People"), "score")
    put("s05_pin1", word("s05", "die"), "pin")
    put("s05_pin2", word("s05", "same", 3), "pin")
    put("s05_pin3", word("s05", "way"), "pin")
    put("s05_pin4", word("s05", "twice"), "pin")
    put("s05_cock", g("s05", 12.80), "creak")
    put("s05_last_stab", g("s05", 13.61), "slash", "stab")
    put("s05_slash", trans_window("s05")[0])
    for sid, rows in SCENE_SYNC_B:
        for name, t, txt, tags in rows:
            put(name, g(sid, t), *tags, txt=txt)
    for k, (win, t, pan) in enumerate(S12_DARK):
        put(f"s12_dark{k}", g("s12", t), txt=rf"window {win} goes dark")
    # narration anchors and transitions (no scene cue of their own)
    put("s06_iris", trans_window("s06")[0], "iris")
    put("s07_sheet", word("s07", "sheet"))
    put("s07_show", word("s07", "show"))
    put("s08_someone", word("s08", "Someone"))
    put("s08_wave", g("s08", 8.0))
    put("s09_ninety", word("s09", "ninety"))
    put("s09_sheet", word("s09", "sheet"))
    put("s09_show", word("s09", "show"))
    put("s10_tear", trans_window("s10")[0], "tear")
    put("s11_found", word("s11", "forty"))
    put("s11_binoculars", word("s11", "binoculars"))
    put("s11_dissolve", trans_window("s11")[0])
    put("s12_mostly", word("s12", "Mostly"))
    return S


# sustained cues that cover a stretch: a scene's per-event cues of this tag inside are 'covered'
# (only reached by a scene cue that no sync point claimed - e.g. one added to a scene later)
def covered_spans(S):
    return [("pop", 0.0, 1.6), ("rain", 0.0, 1e9), ("score", 0.0, 1e9),
            ("umbrella", S["s02_down"]["t"] - 0.3, S["s02_up"]["t"]),
            ("steps", S["s04_torch1"]["t"], S["s04_body"]["t"]), ("siren", S["s04_dark"]["t"], S["s04_bars"]["t"]),
            ("stairs", S["s06_stairs"]["t"], S["s06_street"]["t"]), ("steps", S["s06_stairs"]["t"], S["s06_street"]["t"] + 1.6),
            ("flame", S["s07_match"]["t"], S["s07_flame_out"]["t"] + 0.5),
            ("stairs", S["s09_steps"]["t"], S["s09_feet_stop"]["t"]),
            ("hammer", S["s10_hammer"]["t"] - 0.1, S["s10_stride"]["t"]),
            ("siren", S["s10_sirens"]["t"] - 0.3, S["s11_dissolve"]["t"])]


def sync_points(scene_cues=None):
    """Default sync points, retimed to the picture by the scenes' own cues where they exist.
    A point with a text claim (txt) takes the nearest unclaimed scene cue whose text matches,
    within +-RETIME_WINDOW; the rest take the nearest same-tag cue. Unclaimed scene cues are
    covered by a sustained cue, added (-6 dB, by keyword) or reported unmapped.
    Returns (sync {name: t}, notes {retimed, added, covered, unmapped, missing, extras})."""
    S = default_sync()
    notes = dict(retimed=[], added=[], covered=[], unmapped=[], missing=[])
    claimed = set()
    sc = []
    for i, c in enumerate(scene_cues or []):
        k = classify(c.get("sfx", ""))
        sc.append((i, c, k))

    def take(name, d, ok):
        best = None
        for i, c, k in sc:
            if i in claimed or not ok(c, k):
                continue
            dt = abs(float(c["t"]) - d["t"])
            if dt <= RETIME_WINDOW and (best is None or dt < best[0]):
                best = (dt, i, c)
        if best is None:
            return False
        _, i, c = best
        claimed.add(i)
        if abs(float(c["t"]) - d["t"]) > 1e-3:
            notes["retimed"].append(dict(sync=name, frm=d["t"], to=round(float(c["t"]), 4), cue=c.get("sfx")))
        d["t"] = round(float(c["t"]), 4)
        return True

    order = sorted(S.items(), key=lambda kv: kv[1]["t"])
    done = set()
    for name, d in order:                                     # 1. text claims
        if d.get("txt") and take(name, d, lambda c, k, rx=d["txt"]: re.search(rx, str(c.get("sfx", "")), re.I) is not None):
            done.add(name)
    for name, d in order:                                     # 2. tags
        if name in done or not d["tags"]:
            continue
        if take(name, d, lambda c, k, tg=d["tags"]: k is not None and k[0] in tg):
            done.add(name)
    if sc:
        notes["missing"] = [dict(sync=n, t=d["t"], txt=d["txt"]) for n, d in order if d.get("txt") and n not in done]
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
    # the crane past the facade: three lit windows across the street, each through its glass
    c(S["s02_win4"] - 0.007, "switch_click", 0.0, pan=0.3, dist=0.9)
    c(S["s02_win4"] + 0.04, "bulb_hum", -38.0, pan=0.3, dur=2.0, persp="through_window")
    c(S["s02_dance"] - 0.05, "music_box", -8.0, pan=0.3, dur=round(S["s02_win12"] - S["s02_dance"] + 0.5, 3), dist=0.8)
    c(S["s02_dance"], "swish", -10.0, pan=0.32, length=0.42, f0=900.0, f1=2600.0, peak=0.45, flutter=20.0, weight=0.1, dist=0.75)
    c(S["s02_win12"], "chatter", -8.5, pan=-0.35, dur=1.8, dist=0.75)
    c(S["s02_meow"], "cat_meow", -6.0, pan=-0.4, dist=0.75)
    c(S["s02_tail"] - 0.05, "swish", -12.0, pan=-0.4, length=0.24, f0=1300.0, f1=2800.0, peak=0.4, q=1.2, dist=0.8)
    c(S["s02_win30"], "sobbing", -9.0, pan=0.45, dur=1.6, dist=0.8)
    # the camera pulls back across the street and in through her window; the binoculars come up
    c(S["s02_pull"], "pull_whoosh", -9.0, dur=round(S["s02_through"] - S["s02_pull"] + 0.1, 3))
    c(S["s02_through"] - 0.05, "pane_through", -8.0, dir="in")
    c(S["s02_bino"], "binocular_lift", -7.0, pan=0.12, length=0.32)        # the eyecups meet the brow at +0.30
    c(S["s02_glint"], "glint", -11.0, pan=-0.1)
    c(S["s02_out"] - 0.1, "pane_through", -8.0, dir="out")
    # the street far below: umbrellas going by; the whip tilt back up
    for k, (dt, d, p0, p1, gg) in enumerate(((-0.1, 1.5, -0.6, 0.3, -12.0), (0.15, 1.3, 0.65, -0.1, -14.0))):
        c(S["s02_down"] + dt, "umbrella_pass", gg, dur=d, dist=0.7 + 0.05 * k, pan0=p0, pan1=p1)
    c(S["s02_up"] - 0.05, "swish", -9.0, length=0.34, f0=420.0, f1=3200.0, peak=0.5, q=0.7, weight=0.35)
    # the titles: SHADOW slides in from the left, PLAY from the right (both settle at ~+0.5 s)
    c(S["s02_title_in"], "paper_slide", -9.0, length=0.5, pan0=-0.8, pan1=-0.1)
    c(S["s02_title_in2"], "paper_slide", -10.0, length=0.44, pan0=0.8, pan1=0.1)
    c(S["s02_title_out"] - 0.05, "focus_click", -9.0, pan=0.05)
    c(S["s02_title_out"] + 0.04, "paper_slide", -12.0, length=0.5, tap=0, shape="out", pan0=-0.1, pan1=0.8)   # SHADOW off right
    c(S["s02_title_out"] + 0.08, "paper_slide", -13.0, length=0.48, tap=0, shape="out", pan0=0.1, pan1=-0.8)   # PLAY off left
    c(S["s02_iris"] + 0.1, "iris_close", -12.0)

    # ---------------------------------------------------------------- s03 window nine
    c(S["s03_hush"], "breathing", -23.0, dur=round(S["s03_light_on"] - S["s03_hush"] - 0.4, 3), mode="calm")
    c(S["s03_light_on"] - 0.05, "switch_click", 6.0, pan=0.05, dist=0.3, bus="hit")
    c(S["s03_light_on"], "bulb_on", 2.0, pan=0.05, dist=0.3, bus="hit")
    c(S["s03_light_on"] + 0.2, "bulb_hum", -30.0, dur=S["s03_light_out"] - S["s03_light_on"] - 0.2, persp="through_window")
    c(S["s03_turn"], "doll_flutter", -14.0, pan=0.05, length=0.4, persp="through_window")
    c(S["s03_arm"] + 0.05, "pin_creak", -18.0, pan=0.05, length=0.5, persp="through_window")
    for k, nm in enumerate(("s03_stab1", "s03_stab2", "s03_stab3")):   # (the stabs themselves: the score's strings)
        c(S[nm], "stab_thud", (1.0, 2.0, 3.0)[k], pan=0.05)
    c(S["s03_stab1"] + 0.03, "breath_catch", -14.0)
    c(S["s03_stab3"], "paper_splash", -10.0, tear=1)                  # the red cut-paper splash
    c(S["s03_fall"], "body_fold", -15.0, land=0.42)                   # down at +0.42
    c(S["s03_light_out"], "light_out", 5.0, pan=0.05, dist=0.3, bus="hit")
    c(S["s03_reverse"], "glint", -14.0, pitch=0.62, decay=0.6, attack=0.01)   # the lens, rain loud on her pane
    c(S["s03_bino_down"], "binocular_lift", -12.0, pan=0.1, lower=1)
    c(S["s03_every"], "tinnitus", -27.0, dur=round(S["s03_heart"] - S["s03_every"] + 0.3, 3))
    c(S["s03_heart"], "heart_pulse", -5.0, gap=0.34)

    # ---------------------------------------------------------------- s04 nothing
    c(S["s04_dark"], "beacon_hum", -21.0, pan=0.3, dur=round(S["s04_street"] - S["s04_dark"], 3))
    c(S["s04_burst"], "door_burst", -1.5, pan=-0.45, ti=0.14)           # the leaf hits the wall stop at +0.14
    c(S["s04_torch1"] - 0.03, "flashlight_click", -6.0, pan=-0.5)
    c(S["s04_torch1"] + 0.03, "steps_seq", -10.0, dur=round(S["s04_body"] - S["s04_torch1"] - 0.1, 3), kind="floor", who="him",
      weight=0.9, rate=2.6, creak=0.3, pan0=-0.5, pan1=0.0, g0=0.0, g1=-3.0)
    c(S["s04_torch2"] - 0.03, "flashlight_click", -7.0, pan=-0.7)
    c(S["s04_torch2"] + 0.1, "police_radio", -13.0, pan=-0.75, dist=0.6)
    c(S["s04_body"], "wood_step", -11.0, pan=-0.1, who="him", weight=0.85, creak=0.0)
    c(S["s04_body"] + 0.08, "board_creak", -13.0, pan=-0.1, length=0.5, pitch=0.85)
    c(S["s04_blood"] - 0.1, "cloth_rustle", -18.0, pan=-0.2, length=0.5)
    c(S["s04_street"] + 0.02, "siren_whoop", -9.0, pan=0.3, dist=0.25)
    c(S["s04_street"] - 0.1, "engine_idle", -19.0, pan=0.3, dur=round(S["s04_car_away"] - S["s04_street"] + 0.4, 3))
    c(S["s04_street"] + 0.35, "police_radio", -12.0, pan=0.35, dist=0.25)
    c(S["s04_raise"] - 0.05, "cloth_rustle", -16.0, pan=-0.3, length=0.45)
    c(S["s04_raise"] + 0.05, "grunt", -14.0, pan=-0.3, dist=0.3)
    c(S["s04_dreamed"], "board_creak", -10.0, pan=0.1, length=0.55, pitch=1.1, dist=0.6)
    c(S["s04_car_away"], "car_away", -10.0, pan=0.5, dur=3.2)
    c(S["s04_torch_off"] - 0.03, "flashlight_click", -9.0, pan=-0.6)
    c(S["s04_walk"], "steps_seq", -16.0, dur=1.5, kind="wet", who="him", weight=0.75, rate=1.7, pan0=-0.6, pan1=-0.85, g0=0.0, g1=-6.0)
    c(S["s04_bars"] + 0.2, "bars_wipe", -8.0, t2=0.4, length=0.25)     # top bar home +0.45, bottom +0.85

    # ---------------------------------------------------------------- s05 again (split screen)
    # Tuesday's window (top panel), then Wednesday's (bottom): the same old filament - the same
    # seed, so the two flickers are sample-identical
    for k, nm in enumerate(("s05_light_tue", "s05_light_on")):
        c(S[nm] - 0.05, "switch_click", -3.0, pan=(-0.08, 0.08)[k], dist=0.45, seed=531)
        c(S[nm], "bulb_on", -6.0, pan=(-0.08, 0.08)[k], dist=0.45, seed=541)
    # the replayed murder (the stabs themselves are the score's Psycho strings, as in s03)
    c(S["s05_turn"], "doll_flutter", -16.0, length=0.4)
    c(S["s05_raise"], "pin_creak", -14.0, length=0.55, seed=61)
    c(S["s05_splash"], "paper_splash", -9.0)
    c(S["s05_fall"], "body_fold", -12.0)
    c(S["s05_light_out"], "light_out", 2.0, dist=0.45)
    c(S["s05_rewind"], "rewind", -8.0, length=0.3)                  # the projector restarts
    for a, b in ((S["s05_light_on"] + 0.2, S["s05_light_out"]), (S["s05_rewind"] + 0.35, S["s05_scream"]),
                 (63.0, S["s05_slash"])):
        c(a, "bulb_hum", -32.0, dur=b - a, persp="through_window")
    c(S["s05_second"], "red_line", -8.0)
    c(S["s05_captions"], "paper_slide", -15.0, length=0.3, tap=0, shape="out", pan0=0.0, pan1=-0.7)
    c(S["s05_arm"], "paper_slide", -6.0, length=0.42, pan0=0.0, pan1=0.0)
    c(S["s05_scream"] - 0.95, "scream_pull", -2.0, length=0.95)     # cut dead on [scream]: the silent scream
    for k in range(4):                                               # the pin turns one tick on each word
        c(S[f"s05_pin{k + 1}"], "pin_creak", -9.0 + 1.5 * k, length=0.22 + 0.04 * k, seed=71 + k)
    c(S["s05_cock"], "pin_creak", -3.0, length=0.5, seed=77)         # the arm cocks back
    c(S["s05_last_stab"] - 0.13, "knife_whoosh", -7.0)
    c(S["s05_slash"], "slash_whoosh", -2.0)

    # ---------------------------------------------------------------- s06 crossing
    c(S["s06_grab"], "hook_creak", -11.0, pan=-0.2)
    t0 = S["s06_coat"] - 0.2                                           # the flap at its widest on the cue
    c(t0, "coat_flare", -1.0, flare=0.26, land=round(S["s06_land"] - 0.05 - t0, 3), sleeves=round(S["s06_land"] - t0, 3),
      sleeve_len=0.26, hook=0)
    c(S["s06_collar"] - 0.1, "cloth_snap", -8.0, pan=0.1)
    for k, dt in enumerate((0.04, 0.22, 0.40)):                        # three heel steps to the door
        c(S["s06_heels"] + dt, "wood_step", (-4.0, -5.0, -4.5)[k], pan=0.2 + 0.07 * k, who="her", weight=0.55, creak=0.15)
    c(S["s06_door"] - 0.15, "door_open", -3.0, pan=0.35)               # the latch on the cue, then the swing
    c(S["s06_stairs"], "stair_steps", -5.0, dur=round(S["s06_street"] - S["s06_stairs"], 3), who="her", rate=4.6, d0=0.15, d1=0.8,
      spin=0.6, creak=0.3)
    c(S["s06_run"], "steps_seq", -8.0, dur=1.6, kind="wet", run=1, rate=3.4, weight=0.5, pan0=-0.35, pan1=0.4)
    c(S["s06_lobby"] - 0.15, "door_open", -9.0, pan=0.05, persp="hall_door")
    c(S["s06_lobby"] + 0.25, "door_close", -12.0, pan=0.05, persp="hall_door")
    # the crane up the facade: a radio high up, the crier (window 30), the dancer's music box
    c(S["s06_crane"] + 1.9, "far_radio", -9.0, pan=0.35, dur=1.5)
    c(S["s06_crane"] + 2.45, "sobbing", -9.0, pan=-0.3, dur=1.3, dist=0.85)
    c(S["s06_crane"] + 3.65, "music_box", -12.0, pan=0.25, dur=1.35, dist=0.85, offset=2.0)
    c(S["s06_iris"] + 0.1, "iris_close", -11.0, rect=1)

    # ---------------------------------------------------------------- s07 the show
    c(S["s07_door"], "door_creak", -8.0, pan=-0.55)
    for k, dt in enumerate((0.0, 0.36)):
        c(S["s07_steps"] + dt, "wood_step", (-5.0, -6.0)[k], pan=(-0.5, -0.4)[k], who="her", weight=0.45, creak=0.5)
    c(S["s07_match"] - 0.05, "match_strike", -5.0, pan=-0.15)          # the crack on the cue, the flare just after
    c(S["s07_burn"], "flame_flicker", -24.0, pan=-0.1, dur=round(S["s07_flame_out"] - S["s07_burn"], 3))
    c(S["s07_lamp"], "glass_tick", -18.0, pan=0.1)
    c(S["s07_dolls"], "doll_flutter", -16.0, pan=0.05, length=0.4)
    c(S["s07_flame_out"] - 0.06, "swish", -18.0, pan=0.15, length=0.22, f0=600.0, f1=1700.0, peak=0.4, q=1.0)
    c(S["s07_flame_out"], "flame_out", -12.0, pan=0.15)
    c(S["s07_lamp_on"] - 0.085, "lamp_switch", -3.0, pan=0.15)          # the snap lands on the cue
    c(S["s07_lamp_on"], "bulb_on", -6.0, pan=0.15)
    c(S["s07_to_window"], "steps_seq", -9.0, dur=0.8, kind="floor", who="her", weight=0.5, rate=2.4, pan0=0.35, pan1=0.45)
    c(S["s07_glass"], "steps_seq", -9.0, dur=0.7, kind="floor", who="her", weight=0.5, rate=3.6, pan0=0.0, pan1=0.2)
    # the show lamp's filament from here until it crashes in s10 (louder when everything else stops)
    c(S["s07_lamp_on"] + 0.3, "bulb_hum", -33.0, pan=0.1, dur=round(S["s10_hum"] - S["s07_lamp_on"] - 0.3, 3))

    # ---------------------------------------------------------------- s08 the other side
    # across the street, barely: a floorboard as he walks into her window
    c(S["s08_steps"], "wood_step", -20.0, pan=0.25, who="him", weight=0.6, creak=1.0, stair=0, persp="through_window")
    c(S["s08_steps"] + 0.55, "wood_step", -25.0, pan=0.3, who="him", weight=0.5, creak=0.4, stair=0, persp="through_window")
    c(S["s08_glint"], "glint", -9.0, pan=0.1)
    c(S["s08_light_off"] - 0.05, "pull_chain", 7.0, pan=0.1, dist=1.0, bus="hit")   # her lamp's pull chain: the click on the cue

    # ---------------------------------------------------------------- s09 ninety seconds
    c(S["s09_pivot"], "heel_pivot", -9.0)                               # the heel knocks at +0.10
    c(S["s09_run"], "steps_seq", -10.0, dur=round(S["s09_lamp_lift"] - S["s09_run"] - 0.05, 3), kind="floor", who="her", weight=0.55,
      rate=3.6, pan0=0.0, pan1=0.3)
    c(S["s09_lamp_lift"], "lamp_lift", -8.0, pan=0.25)
    c(S["s09_doll"], "rod_tap", -10.0, pan=0.05)
    c(S["s09_doll"] + 0.03, "doll_flutter", -12.0, pan=0.05, length=0.5)
    c(S["s09_doll"] + 0.45, "steps_seq", -13.0, dur=round(S["s09_lamp"] - S["s09_doll"] - 0.75, 3), kind="floor", who="her",
      weight=0.6, rate=3.0, pan0=0.1, pan1=-0.15)
    c(S["s09_lamp"] - 0.3, "lamp_set", -6.0, pan=-0.15)                # the tripod's feet land on [light]
    c(S["s09_rasp"], "pins_rasp", -8.0, length=1.15, pan0=0.35, pan1=-0.25)
    c(S["s09_believe"] - 0.09, "doll_clamp", -6.0, pan=-0.2)            # the clamp snaps on [believe]
    c(S["s09_hide_run"], "steps_seq", -10.0, dur=round(S["s09_wall"] - S["s09_hide_run"] - 0.15, 3), kind="floor", who="her",
      weight=0.5, rate=3.4, pan0=-0.4, pan1=-0.6)
    c(S["s09_wall"], "wall_bump", -12.0, pan=-0.6)
    c(S["s09_wall"] + 0.1, "breathing", -21.0, pan=-0.55, dur=round(S["s09_feet_stop"] - S["s09_wall"] - 0.1, 3), mode="held")
    c(S["s09_steps"], "stair_steps", -5.0, dur=round(S["s09_feet_stop"] - S["s09_steps"] + 0.05, 3), who="him", rate=1.8, d0=0.95,
      d1=0.2, spin=0.25, creak=0.6, persp="hall_door")
    c(S["s09_timer"], "timer_switch", -10.0, pan=-0.75, persp="hall_door")
    c(S["s09_handle"], "handle_turn", -1.0, pan=-0.6, length=round(S["s10_clack"] - S["s09_handle"], 3))   # clack on 'latch free'

    # ---------------------------------------------------------------- s10 the trap (wordless)
    c(S["s10_burst"], "door_burst", -1.0, pan=-0.45, ti=0.12)           # the leaf off its stop at +0.12
    for k, dt in enumerate((0.0, 0.25, 0.5)):                          # his heavy run to the sheet, coat flapping
        c(S["s10_run"] + dt, "wood_step", (-5.0, -6.0, -5.5)[k], pan=-0.2 + 0.1 * k, who="him", weight=1.0, creak=0.2)
    c(S["s10_run"] + 0.05, "swish", -13.0, pan=-0.1, length=0.55, f0=300.0, f1=1000.0, peak=0.4, q=0.8, flutter=14.0, weight=0.7)
    for k, nm in enumerate(("s10_stab1", "s10_stab2")):
        c(S[nm] - 0.12, "knife_whoosh", -4.0, pan=(0.05, 0.0)[k])
        c(S[nm], "sheet_rip", 1.0 + 0.5 * k, pan=(0.0, 0.05)[k], size=(0.45, 0.55)[k])
    c(S["s10_rip"] - 0.02, "sheet_rip", 2.0, pan=0.05, punch=0, length=round(S["s10_pins"] - S["s10_rip"], 3))
    c(S["s10_pins"], "pins_pop", -1.0, pan=-0.1, slump=round(S["s10_hum"] - S["s10_pins"], 3))
    c(S["s10_hum"], "bulb_hum", -22.0, pan=0.05, dur=round(S["s10_slam"] - S["s10_hum"], 3))
    c(S["s10_her"], "steps_seq", -10.0, dur=0.75, kind="floor", who="her", weight=0.4, rate=3.2, pan0=-0.5, pan1=-0.6)
    c(S["s10_whip"] - 0.1, "swish", -10.0, pan=-0.2, length=0.3, f0=350.0, f1=1200.0, peak=0.35, q=0.8, flutter=16.0, weight=0.6)
    c(S["s10_slam"] - 0.114, "door_slam", 1.0, pan=-0.3)               # the slab hits on the cue
    c(S["s10_key"], "key_lock", 2.0, pan=-0.1, insert=0, bolt_at=round(S["s10_bolt"] - S["s10_key"], 3))
    c(S["s10_body"], "body_hit", -1.0, pan=-0.05)
    c(S["s10_hammer"], "door_hammer", 0.5, dur=round(S["s10_stride"] - S["s10_hammer"] + 0.3, 3), rattle=1.0,
      times=(0.0, 0.2, 0.38, 0.55, 0.7, 0.85))
    c(S["s10_slam"] + 0.05, "bulb_hum", -32.0, dur=round(S["s10_crash"] - S["s10_slam"], 3), persp="behind_door")
    c(S["s10_stride"] - 0.02, "wood_step", -3.0, pan=0.05, who="him", weight=0.95, creak=0.2, persp="behind_door")
    c(S["s10_crash"] - 0.17, "lamp_crash", 0.5, pop=1, dur=round(S["s10_dark"] - S["s10_crash"] + 0.17, 3), persp="behind_door")
    c(S["s10_fizz"], "electric_fizz", -4.0, pan=0.05, length=round(S["s10_dark"] - S["s10_fizz"], 3), persp="behind_door")
    c(S["s10_dark"], "fuse_click", -2.0, pan=0.1)                       # ... then total silence (sfx_silences)
    c(S["s10_sirens"] + 0.8, "car_door_close", -17.0, pan=-0.55, persp="through_window")
    c(S["s10_sirens"] + 1.2, "car_door_close", -19.0, pan=-0.4, persp="through_window")
    c(S["s10_slide"], "cloth_slide", -8.0, length=1.4)
    c(S["s10_breath"], "breathing", -16.0, dur=round(S["s10_tear"] - S["s10_breath"] + 0.5, 3), mode="shaky")
    c(S["s10_tear"], "tear_big", -4.0)

    # ---------------------------------------------------------------- s11 forty dolls
    c(S["s11_strobe"] + 0.3, "police_radio", -17.0, pan=0.6, dist=0.6, persp="through_window")
    c(S["s11_dolls"], "dolls_rustle", -9.0, dur=1.6)
    c(S["s11_torch"] - 0.03, "flashlight_click", -5.0, pan=-0.6)
    c(S["s11_torch"] + 0.02, "bulb_flicker", -22.0, pan=-0.55)
    c(S["s11_sweep"], "cloth_rustle", -18.0, pan=-0.4, length=0.7)
    c(S["s11_sweep"] + 0.1, "swish", -21.0, pan=-0.35, length=0.6, f0=350.0, f1=900.0, peak=0.5, q=0.8, weight=0.3)
    for k, dt in enumerate((0.15, 1.0, 1.85)):
        c(S["s11_sweep"] + dt, "wood_step", (-12.0, -13.0, -13.5)[k], pan=(-0.4, -0.3, -0.2)[k], who="him", weight=0.75, creak=0.5)
    # the shutter on the scene's flashgun cue, the bulb's pop on the facade print (the picture's flash)
    c(S["s11_flash"], "flashgun", -3.0, pan=0.5, pop=round(max(0.0, S["s11_window"] - S["s11_flash"]), 3))
    c(S["s11_eject"], "bulb_eject", -10.0, pan=0.6)
    c(S["s11_finds"], "doll_flutter", -16.0, pan=0.1, length=0.4)
    c(S["s11_finds"] + 0.05, "pin_creak", -14.0, pan=0.1, length=0.3)

    # ---------------------------------------------------------------- s12 mostly
    c(S["s12_bino"], "bino_set", -5.0, pan=0.2)
    c(S["s12_take"], "curtain_rings", -12.0, pan=0.4, part=1)
    c(S["s12_curtain"], "curtain_rings", -2.0, length=0.85, pan0=0.3, pan1=-0.5)
    c(S["s12_home"] - 0.06, "rings_home", -6.0, pan=-0.5)
    c(S["s12_part"], "curtain_rings", -11.0, pan=0.1, part=1, pan0=0.05, pan1=0.15)
    c(S["s12_new_window"], "switch_click", 2.0, dist=1.0)
    c(S["s12_pullout"] - 0.12, "pane_through", -8.0, dir="out")
    c(S["s12_glint"], "glint", -9.0, pan=0.25)
    c(S["s12_lamp_dies"], "lamp_die", -8.0, pan=-0.5)
    for k, (win, t, pan) in enumerate(S12_DARK):                       # the last windows (with the score's muted pizz)
        c(S[f"s12_dark{k}"] - 0.007, "switch_click", -12.0, pan=round(0.75 * pan, 2), dist=1.0, off=1)
    c(S["s12_end"], "glint", -16.0, pan=0.25, decay=0.5, pitch=1.25)

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
        (9.0, S["s02_through"] + 0.3, "street", -14.0),   # the facade across the street
        (S["s02_through"] + 0.3, S["s02_out"], "her_room", -16.0),
        (S["s02_out"], S["s02_title_in"] - 0.2, "street", -13.0),
        (S["s02_title_in"] - 0.2, 24.5, "plate", -22.0),  # title graphics
        (24.5, 41.0, "her_room", -16.0),                  # s03 her window (across-street sounds carry their own distance)
        (41.0, S["s04_street"], "apt9", -12.0),
        (S["s04_street"], 52.5, "street", -12.0),
        (52.5, 66.5, "her_room", -18.0),                  # s05 split screen through her binoculars
        (66.5, S["s06_door"], "her_room", -14.0),
        (S["s06_door"], S["s06_stairs"], "hallway", -12.0),
        (S["s06_stairs"], S["s06_street"], "stairwell", -9.0),
        (S["s06_street"], 79.0, "street", -12.0),
        (79.0, S["s10_slam"], "apt9", -12.0),
        (S["s10_slam"], 131.5, "hallway", -11.0),
        (131.5, 141.5, "killer", -15.0),
        (141.5, S["s12_pullout"], "her_room", -15.0),
        (S["s12_pullout"], 153.5, "street", -13.0),
    ]


def sfx_silences(sync):
    """[(t0, t1, fade_out s, fade_in s)] - stretches where every SFX (and its reverb) is cut dead:
    s10's fuse ('then total silence') until the sirens arrive, and the very end."""
    S = sync
    return [(S["s10_dark"] + 0.06, S["s10_sirens"] - 0.02, 0.012, 0.02),
            (153.3, 153.5 + 1.0, 0.15, 0.0)]


if __name__ == "__main__":
    import json
    sync, notes = sync_points([])
    cues = build_cues(sync)
    print(json.dumps({k: v for k, v in sorted(sync.items(), key=lambda kv: kv[1])}, indent=0)[:3000])
    print(len(cues), "cues")
