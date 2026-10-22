"""RED: the designed SFX cue sheet (bible sections 4-5) + merging of the scenes' cues(T) hints.

    cues(use_scenes=True) -> (cue list on the film clock, report)

A cue: dict(t, sfx, gain_db, pan, dur, params, seed, sid, tag, lock, source)
  t       film time of the sound's SYNC point (mix.py places the render at t - sync)
  lock    'word'  locked to a narration word (common.A): never moves
          'beat'  a picture beat from the bible: snaps to a scene's cue of the same family
          'free'  detail / Foley bed: snaps too, or is replaced by a scene's sequence
  source  'design' (this sheet) | 'scene' (added from a scene's cues(T))

The sheet is primary: the scenes are not written yet. When they are, `cues(T)` hints (free-text
names, see engine.timing.Cue) are mapped to this film's catalog by keyword (KEYWORDS, or the exact
catalog name) and merged:
  * a designed cue of the same family within SNAP s (same scene) moves to the scene's time
    (unless word-locked) and takes its pan;
  * a scene giving >= 3 footsteps (girl or wolf) replaces the designed steps over its span;
  * anything else from a scene is added at the family's default level (+ the scene's gain_db);
  * names that map to nothing are reported (audio_report.json 'unknown_scene_cues').
"""
from __future__ import annotations

import re

import numpy as np

from .common import A, SCENE_IDS, scene_at
from . import sfx_red
from audio import dsp

SNAP = 0.6
SEQ_FAMILIES = ("step_girl", "step_wolf")

# "the footsteps stop": no sound, it ends the scene's walk there (later steps of that walk are dropped)
STOP = r"(foot)?steps? (stop|cease|end)|stops? (walking|running)|comes? to a (halt|stop)|\bhalts?\b"
STOP_MARK = "-stop"

# free text -> catalog sound (first match wins; more specific first)
KEYWORDS = [
    (r"\bpop\b|pops up", "paper_pop"),
    (r"paper.*(thump|slam)|(thump|slam).*paper", "grid_pulse"),
    (r"\bink\b|drawn|draws|\bdraw\b|brush", "ink_draw"),
    (r"page turns|turns over|paper.*whoosh|whoosh.*paper", "paper_swing"),
    (r"thicket", "thicket_grow"),
    (r"lantern.*(smash|break|shatter)|smash|shatter", "lantern_smash"),
    (r"(match|light).*(lantern|wick)|lantern.*(light|lit)|wick|light.*lantern", "lantern_light"),
    (r"lantern", "lantern_roll"),
    (r"shriek|screech|scream", "spider_shriek"),
    (r"(spider|grandmother).*hiss|hiss.*(spider|grandmother)", "spider_hiss"),
    (r"fire.*(whoosh|race|run|spread|catch)|whoosh.*fire|ignite|catch(es)? fire|web.*burn", "fire_whoosh"),
    (r"flare|flash", "fire_flare"),
    (r"ember|smoulder|smolder|sizzle", "embers"),
    (r"fire|burn|blaze|inferno", "fire_roar"),
    (r"flame|flicker", "flame_flutter"),
    (r"clink", "bottle_clink"),
    (r"bottle|wine", "bottle_roll"),
    (r"bread|loaf", "bread_thump"),
    (r"basket.*(handle|give|hand|take)", "basket_handle"),
    (r"basket.*creak|wicker", "basket_creak"),
    (r"basket", "basket_tumble"),
    (r"ribbon|\btie|knot|tied", "ribbon_tie"),
    (r"hood.*(fall|drift|drop|float|land|pat|settle|flutter)", "hood_fall"),
    (r"hood", "hood_up"),
    (r"door|shutter", "door_wood"),
    (r"gate", "gate_creak"),
    (r"\bsign\b", "sign_creak"),
    (r"dog|bark", "dog_bark"),
    (r"crow|caw|raven", "crow_caw"),
    (r"wing|flap", "crow_flap"),
    (r"owl|hoot", "owl_hoot"),
    (r"bird|chirp|song", "bird_chirp"),
    (r"plop|snow.*(slide|fall from|clump|drop)", "snow_plop"),
    (r"branch|tree.*creak|creak.*tree|trunk", "branch_creak"),
    (r"thread|silk|web.*creak|rope", "thread_creak"),
    (r"(spider|grandmother|body).*(drop|land)|drops", "spider_drop"),
    (r"stab|leg.*(hit|strike|touch|plant|land)|legs? touch", "leg_stab"),
    (r"skitter|scuttle|legs? (move|run|charge)|charge", "spider_skitter"),
    (r"hiss", "spider_hiss"),
    (r"chitin|click|mandible", "chitin_click"),
    (r"eye.*(cluster|spider)|spider.*eye", "spider_eyes"),
    (r"eyes?.*(out|close|blink|vanish)|blink", "eyes_out"),
    (r"eyes?|glint|glow", "eyes_glint"),
    (r"bite|jaw|snap shut", "wolf_bite"),
    (r"yelp|whimper|pinned", "wolf_yelp"),
    (r"whine", "wolf_whine"),
    (r"snarl", "wolf_snarl"),
    (r"growl", "wolf_growl"),
    (r"wolf.*pant|pant.*wolf", "wolf_pant"),
    (r"huff|snort|sniff", "wolf_huff"),
    (r"wounded|wheeze", "wolf_wounded"),
    (r"wolf.*breath|breath.*wolf", "wolf_breath"),
    (r"leap|jump|pounce", "wolf_leap"),
    (r"wolf.*(land|step|block|appear)|lands?\b", "wolf_land"),
    (r"\bsits?\b|settle", "wolf_settle"),
    (r"paw|wolf.*(step|run|gallop)|gallop|bound", "wolf_paw"),
    (r"skid|slide.*stop|stop.*slide|stops? (short|dead)", "snow_skid"),
    (r"fall|face.?down|plunge|knocked down", "fall_deep_snow"),
    (r"scramble|crawl", "snow_scramble"),
    (r"wade|deep snow", "snow_wade"),
    (r"kneel", "kneel_snow"),
    (r"gasp|inhale", "girl_gasp"),
    (r"breath|pant", "girl_breath_run"),
    (r"touch|stroke|fur|muzzle|pet", "fur_touch"),
    (r"cloak|cloth|rustle|cape|turn|hug|embrace", "cloth_rustle"),
    (r"run|step|foot|walk", "snow_step"),
    (r"ink|draw|brush", "ink_draw"),
    (r"stake", "stakes_pop"),
    (r"thicket|bloom", "thicket_grow"),
    (r"letter|title", "letter_fall"),
    (r"grid.*pulse|pulse", "grid_pulse"),
    (r"grid|tick|row", "grid_tick"),
    (r"flatten|unflatten|fold", "flatten"),
    (r"swing|tilt", "paper_swing"),
    (r"slide|glide", "paper_slide"),
    (r"pop|snap|paper|triangle", "paper_pop"),
    (r"white|swell|dip", "white_swell"),
    (r"whip", "lib:whip"),
    (r"whoosh|swish|swoosh", "lib:whoosh"),
]

# level (gain_db) for a sound a scene adds that the sheet did not design (+ the scene's gain_db)
FAMILY_GAIN = dict(step_girl=-12.0, step_wolf=-12.0, door=-7.0, cloth=-15.0, graphic=-10.0, breath_girl=-10.0,
                   spider_leg=-6.0, spider_click=-12.0, spider_voice=-6.0, spider_move=-8.0, thread=-8.0,
                   wolf_growl=-8.0, wolf_breath=-12.0, wolf_body=-4.0, fire_whoosh=-4.0, fire_bed=-10.0,
                   embers=-12.0, flame=-16.0, crow=-16.0, dog=-18.0, sign=-16.0, owl=-18.0, bird=-18.0,
                   branch=-16.0, snow_plop=-16.0, hood=-15.0, eyes=-10.0, kneel=-11.0, touch=-10.0)


def resolve(text):
    """Scene cue text -> catalog sound name (or None)."""
    t = str(text).strip()
    if sfx_red.exists(t):
        return t
    tt = t.lower().replace("_", " ")
    if sfx_red.exists(tt.replace(" ", "_")):
        return tt.replace(" ", "_")
    if re.search(STOP, tt):
        return STOP_MARK
    for pat, name in KEYWORDS:
        if re.search(pat, tt):
            if name in ("snow_step", "girl_breath_run") and re.search(r"wolf", tt):
                return "wolf_paw" if name == "snow_step" else "wolf_pant"
            return name
    return None


def family(name):
    return sfx_red.spec(name)["family"]


def scene_gain(h, fam):
    """A scene's gain_db is a placement relative to the library level (0 dB = -16 LUFS momentary);
    0.0 is read as 'not given' (the family default), anything above +3 dB is clamped."""
    g = float(h.get("gain_db", 0.0))
    return FAMILY_GAIN.get(fam, -8.0) if g == 0.0 else min(g, 3.0)


def expand_steps(h, fam):
    """One scene cue describing a run of footsteps (with dur) -> one hint per step."""
    text = h["text"].lower()
    running = re.search(r"\brun|running|sprint|gallop|bound", text)
    slow = re.search(r"\bslow|hesitant|careful|creep|tiptoe", text)
    rate = 3.2 if running else (1.4 if slow else (2.2 if fam == "step_wolf" else 1.9))
    pace = None
    if fam == "step_girl":
        pace = "run" if running else ("slow" if slow else None)
    elif running:
        pace = "gallop"
    n = max(2, int(float(h["dur"]) * rate))
    fade = -8.0 if re.search(r"reced|away|fading|distant", text) else 0.0
    out = []
    for i in range(n):
        e = dict(h)
        e["t"] = h["t"] + i / rate
        e["gain_db"] = (h["gain_db"] or FAMILY_GAIN.get(fam, -12.0)) + fade * i / max(n - 1, 1) - (1.0 if i % 2 else 0.0)
        e["idx"] = h["idx"] * 100 + i
        e["dur"] = None
        e["span_end"] = h["t"] + float(h["dur"])
        if pace and "pace" not in (h.get("params") or {}):
            e["params"] = {**(h.get("params") or {}), "pace": pace}
        out.append(e)
    return out


# ============================================================================ the designed sheet
class Sheet:
    def __init__(self):
        self.cues = []
        self.rng = np.random.default_rng(dsp.stable_seed("red-cuesheet"))

    def add(self, t, sfx, gain_db=0.0, pan=0.0, dur=None, lock="beat", tag=None, **params):
        if not sfx_red.exists(sfx):
            raise KeyError(sfx)
        c = dict(t=round(float(t), 4), sfx=sfx, gain_db=float(gain_db), pan=float(pan), dur=dur, params=params,
                 lock=lock, tag=tag or sfx, sid=scene_at(t), source="design",
                 seed=int(dsp.stable_seed("red-cue", tag or sfx, len(self.cues)) % (1 << 31)))
        self.cues.append(c)
        return c

    def steps(self, t0, t1, rate, sfx="snow_step", gain_db=-12.0, pan=0.0, pan1=None, gain1=None, jitter=0.02,
              tag="steps", **params):
        n = int((t1 - t0) * rate) + 1
        for i in range(n):
            t = t0 + i / rate + float(self.rng.uniform(-jitter, jitter))
            if t > t1:
                break
            u = i / max(n - 1, 1)
            g = gain_db + ((gain1 - gain_db) * u if gain1 is not None else 0.0)
            p = pan + ((pan1 - pan) * u if pan1 is not None else 0.0)
            self.add(t, sfx, g - (1.2 if i % 2 else 0.0), p + (0.04 if i % 2 else -0.04), lock="free", tag=tag, **params)


def designed():
    D = Sheet()
    # ------------------------------------------------------------------ s01 THE RULE (cut paper)
    child, rule, never, leave, path = A(1, "child"), A(1, "rule"), A(2, "Never"), A(2, "leave"), A(2, "path")
    D.add(0.02, "ink_draw", -9.0, dur=1.38, tag="s01 the path line draws itself")
    D.add(child, "paper_pop", -11.0, lock="word", tag="red triangle appears on 'child'")
    D.add(child + 0.1, "paper_slide", -17.0, dur=leave - child - 0.1, tag="triangle glides down the line")
    D.add(rule, "stakes_pop", -8.0, lock="word", tag="stakes pop up on 'rule'", count=10, span=0.7)
    D.add(never, "thicket_grow", -7.0, lock="word", tag="thickets bloom on 'Never'")
    D.add(never + 0.35, "eyes_glint", -11.0, -0.45, tag="eyes open (pair 1)")
    D.add(never + 0.62, "eyes_glint", -13.0, 0.5, tag="eyes open (pair 2)")
    D.add(leave, "paper_pop", -17.0, lock="word", tag="triangle stops on 'leave'")
    D.add(path, "eyes_out", -9.0, -0.45, lock="word", tag="eyes blink out on 'path'")
    D.add(path + 0.05, "eyes_out", -11.0, 0.5, lock="word", tag="eyes blink out on 'path' (2)")
    D.add(7.3, "paper_swing", -8.0, tag="top-down view tilts to the side view")
    D.add(8.38, "ink_draw", -16.0, dur=1.2, tag="ink bleeds into the night village")

    # ------------------------------------------------------------------ s02 THE HOOD (village)
    D.add(9.9, "cloth_rustle", -15.0, -0.1, tag="mother kneels", size=0.6)
    D.add(10.05, "kneel_snow", -14.0, -0.1, tag="mother kneels", weight=0.6)
    D.add(A(3, "tied"), "ribbon_tie", -10.0, lock="word", tag="hands tie the ribbon on 'tied'")
    D.add(A(3, "hood"), "hood_up", -8.0, lock="word", tag="hood pulled up on 'hood'")
    D.add(A(3, "basket"), "basket_handle", -9.0, lock="word", tag="basket handed over on 'basket'")
    D.add(17.25, "cloth_rustle", -15.0, tag="mother stands, turns away", size=0.7)
    D.add(A(4, "didn't", 1), "door_wood", -7.0, -0.6, lock="word", tag="door 1 shuts on 'didn't'", force=0.6)
    D.add(A(4, "know"), "door_wood", -7.0, 0.6, lock="word", tag="door 2 shuts on 'know'", force=0.7)
    D.add(A(4, "yet"), "door_wood", -5.0, -0.25, lock="word", tag="door 3 shuts on 'yet'", force=0.9)
    D.steps(21.15, 24.6, 1.9, gain_db=-11.0, pan=-0.05, pan1=0.25, gain1=-15.0, tag="s02 walk to the gate", weight=0.25)
    for t in (21.4, 22.45, 23.5):
        D.add(t, "basket_creak", -18.0, lock="free", tag="basket on her arm")
    D.add(21.9, "gate_creak", -11.0, 0.35, tag="the village gate")
    D.add(22.5, "cloth_rustle", -19.0, tag="she looks back once", size=0.3)

    # ------------------------------------------------------------------ s03 THE PATH (title, forest)
    D.steps(24.0, 37.6, 1.8, gain_db=-12.0, tag="s03 walk down the path", weight=0.25, depth=0.3)
    for t in np.arange(24.9, 37.0, 1.7):
        D.add(t, "basket_creak", -19.0, lock="free", tag="basket on her arm")
    D.add(24.55, "paper_pop", -19.0, tag="title letters stand")
    for i, (t, p) in enumerate(((27.5, -0.25), (27.82, 0.0), (28.12, 0.25))):
        D.add(t, "letter_fall", -10.0 + (1.0 if i == 2 else 0.0), p, tag=f"title letter {i + 1} falls")

    # ------------------------------------------------------------------ s04 THE WOLF
    wolf, girls = A(6, "wolf"), A(7, "girls")
    D.steps(38.0, 43.3, 1.8, gain_db=-12.0, tag="s04 walk", weight=0.25)
    D.steps(43.3, 44.45, 2.4, gain_db=-11.0, tag="s04 walk faster", weight=0.25)
    D.steps(44.5, 50.15, 3.3, gain_db=-9.0, tag="s04 run", pace="run", weight=0.3)
    D.add(wolf, "eyes_glint", -6.0, -0.6, lock="word", tag="the wolf's eyes open on 'wolf'", low=1)
    D.add(40.1, "wolf_growl", -17.0, -0.6, dur=2.4, tag="low growl in the thicket", f0=60.0)
    D.steps(40.2, 44.3, 1.6, "wolf_paw", -18.0, pan=-0.65, tag="wolf pacing her in the thicket", pace="walk", depth=0.3)
    D.add(41.9, "wolf_breath", -15.0, -0.55, dur=3.5, tag="something huge between the trunks")
    D.add(42.55, "fur_touch", -16.0, -0.6, tag="fur brushing a trunk")
    D.add(43.15, "wolf_huff", -11.0, -0.5, tag="a huff in the dark")
    D.add(girls - 0.12, "girl_gasp", -9.0, lock="word", tag="she gasps and RUNS on 'girls'")
    D.add(44.6, "girl_breath_run", -11.0, dur=5.7, tag="her running breath", rate=2.6, intensity=0.75)
    D.steps(45.0, 49.7, 2.4, "wolf_paw", -14.0, pan=-0.7, tag="the eyes pace her (gallop)", pace="gallop", depth=0.5)
    D.add(45.0, "wolf_pant", -13.0, -0.65, dur=4.8, tag="wolf panting alongside", rate=2.3)
    D.add(49.95, "wolf_land", -4.0, 0.25, tag="the wolf steps onto the path ahead")
    D.add(50.3, "snow_skid", -5.0, 0.0, tag="she skids to a stop", who="girl")
    D.add(50.55, "girl_gasp", -9.0, tag="she gasps")
    D.add(50.75, "wolf_growl", -6.0, 0.25, dur=1.2, tag="head low, growling", f0=58.0)
    D.add(51.75, "lib:whip", -6.0, 0.3, tag="whip transition")

    # ------------------------------------------------------------------ s05 DEEP SNOW
    off, snow, stopped, waited = A(8, "off"), A(8, "snow"), A(8, "stopped"), A(8, "waited")
    D.steps(52.0, 57.0, 2.6, "snow_wade", -12.0, tag="s05 wading uphill", weight=0.3)
    D.add(52.0, "girl_breath_run", -14.0, dur=5.1, tag="her breath, climbing", rate=2.8, intensity=0.85)
    D.steps(52.25, 58.6, 2.2, "wolf_paw", -14.0, pan=-0.35, tag="the wolf bounds after her", pace="gallop", depth=0.8)
    D.add(52.3, "wolf_pant", -16.0, -0.35, dur=6.2, tag="wolf panting behind", rate=2.2)
    D.add(off, "cloth_rustle", -14.0, lock="word", tag="she crosses the stakes on 'off'", size=0.8)
    for t in (52.9, 54.4, 55.9):
        D.add(t, "basket_creak", -17.0, lock="free", tag="basket swinging")
    D.add(snow, "fall_deep_snow", -3.0, lock="word", tag="face-down in the deep snow on 'snow'")
    D.add(snow + 0.55, "snow_scramble", -8.0, tag="she scrambles")
    D.add(snow + 1.4, "girl_breath_run", -13.0, dur=1.8, tag="ragged breath", rate=2.0, intensity=0.6)
    D.add(stopped - 0.28, "snow_skid", -7.0, -0.3, tag="the wolf stops short ('stopped')", who="wolf")
    D.add(stopped + 0.42, "wolf_huff", -11.0, -0.3, tag="the wolf huffs")
    D.add(59.9, "wolf_breath", -15.0, -0.3, dur=6.5, tag="the wolf breathing, waiting", rate=0.45, intensity=0.6)
    D.add(waited, "wolf_settle", -8.0, -0.3, lock="word", tag="it sits on 'waited'")
    D.add(61.5, "cloth_rustle", -14.0, tag="she gets up", size=0.7)
    D.steps(61.8, 64.8, 1.6, gain_db=-12.0, tag="she backs away uphill", pace="back", weight=0.25, depth=0.5)
    D.add(61.6, "girl_breath_run", -17.0, dur=4.0, tag="frightened breath", rate=1.3, intensity=0.4)
    D.add(63.4, "wolf_whine", -14.0, -0.3, tag="the wolf looks past her")
    D.add(65.0, "cloth_rustle", -17.0, tag="she turns to look", size=0.4)

    # ------------------------------------------------------------------ s06 RED HOODS
    D.add(77.6, "flatten", -8.0, tag="hoods flatten into the Bass grid")
    for i in range(6):
        D.add(77.75 + 0.3 * i, "grid_tick", -12.0 - 0.5 * i, 0.15 * (-1) ** i, tag=f"grid row {i + 1}")
    D.add(79.84, "grid_pulse", -6.0, tag="the grid pulses once (with the score)")
    D.add(81.0, "flatten", -9.0, tag="grid becomes live again (flatten reverse)")

    # ------------------------------------------------------------------ s07 GRANDMOTHER
    G, ch7 = A(12, "Grandmother"), A(12, "child")
    D.add(G, "thread_creak", -6.0, 0.2, lock="word", tag="first leg descends on a thread on 'Grandmother'")
    D.add(G + 0.4, "chitin_click", -15.0, 0.1, tag="joint clicks")
    D.add(G + 0.6, "thread_creak", -9.0, -0.35, tag="second leg", pitch=95.0)
    D.add(G + 1.1, "thread_creak", -10.0, 0.5, tag="third leg", pitch=125.0)
    for i, (dt, p, g) in enumerate(((0.0, -0.4, -6.0), (0.17, 0.5, -7.0), (0.33, -0.1, -8.0), (0.5, 0.3, -9.0))):
        D.add(ch7 + dt, "leg_stab", g, p, lock="word" if i == 0 else "beat", tag=f"leg {i + 1} touches the snow ('child')")
    D.add(85.6, "spider_eyes", -6.0, tag="the eye cluster opens")
    D.add(86.2, "chitin_click", -16.0, tag="mandibles", count=2)
    D.add(87.3, "spider_hiss", -6.0, tag="the hiss after 'alone'")
    D.add(87.75, "spider_drop", -2.0, tag="Grandmother drops fully")
    D.add(87.95, "girl_gasp", -9.0, tag="she gasps")
    D.add(88.4, "spider_skitter", -6.0, dur=5.0, tag="the CHARGE", speed=8.0)
    D.steps(88.6, 90.4, 2.2, gain_db=-12.0, tag="she backs away", pace="back", weight=0.3)
    D.add(90.6, "fall_deep_snow", -9.0, tag="she falls backwards")
    for t, p in ((89.2, 0.3), (90.0, -0.4), (91.2, 0.5), (92.4, -0.2)):
        D.add(t, "chitin_click", -11.0, p, lock="free", tag="chitin rattle")
    for t, p, g in ((91.7, 0.4, -9.0), (92.3, -0.3, -8.5), (92.9, 0.2, -7.5)):
        D.add(t, "leg_stab", g, p, tag="charging legs hit the snow")
    D.add(93.6, "wolf_leap", 0.0, tag="the WOLF leaps over her")

    # ------------------------------------------------------------------ s08 FIRE
    D.add(94.15, "leg_stab", -5.5, 0.3, tag="the fight: leg stabs")
    D.add(94.35, "wolf_snarl", -3.0, -0.2, tag="the fight snarl")
    D.add(94.95, "leg_stab", -5.0, -0.4, tag="leg stab")
    D.add(95.3, "wolf_bite", -3.5, 0.1, tag="the wolf bites a leg")
    D.add(95.5, "spider_hiss", -6.0, 0.2, tag="Grandmother hisses")
    D.add(95.9, "leg_stab", -6.0, 0.5, tag="leg stab")
    D.add(96.25, "kneel_snow", -6.0, tag="she is knocked down", weight=1.0)
    D.add(96.3, "girl_gasp", -9.0, tag="knocked down")
    D.add(96.35, "lib:whoosh", -10.0, 0.4, tag="the basket flies", size=0.4)
    D.add(A(13, "basket"), "basket_tumble", -6.0, lock="word", tag="the basket rolls on 'basket'")
    D.add(97.25, "spider_skitter", -14.0, dur=2.5, tag="fight continues (under the voice)")
    D.add(98.7, "wolf_growl", -12.0, dur=2.0, tag="growl under the voice")
    D.add(A(13, "Bread"), "bread_thump", -8.0, lock="word", tag="a loaf tumbles out on 'Bread'")
    D.add(A(13, "Wine"), "bottle_roll", -8.0, lock="word", tag="a bottle rolls out on 'Wine' (+clink)")
    D.add(101.5, "leg_stab", -10.0, 0.4, tag="leg stab between lines")
    D.add(101.65, "wolf_snarl", -11.0, -0.3, tag="snarl between lines")
    L = A(14, "lantern")
    D.add(L, "lantern_roll", -8.0, lock="word", tag="the lantern rolls out on 'lantern'")
    D.add(L + 0.3, "flame_flutter", -16.0, dur=3.6, tag="the lantern glows in the snow", wind=0.3)
    D.add(103.35, "wolf_yelp", -6.0, -0.2, tag="the spider pins the wolf")
    D.add(103.55, "spider_hiss", -9.0, 0.2, tag="hiss over the pinned wolf")
    D.add(104.9, "cloth_rustle", -15.0, tag="she grabs the lantern", size=0.6)
    D.steps(105.05, 106.5, 3.3, gain_db=-12.0, tag="she runs to the web", pace="run", weight=0.3)
    fire = A(15, "fire")
    D.add(fire, "lantern_smash", 0.0, lock="word", tag="SMASH on 'fire'")
    D.add(fire + 0.28, "fire_whoosh", -3.0, tag="fire races along the web (after the word reads)", size=1.0, pan0=-0.5, pan1=0.8)
    D.add(fire + 0.95, "fire_whoosh", -5.0, tag="up the threads into the canopy", size=0.85, pan0=0.4, pan1=-0.6)
    D.add(fire + 1.7, "fire_whoosh", -7.0, tag="down toward the valley", size=0.7, pan0=-0.2, pan1=0.3)
    D.add(108.1, "spider_shriek", -3.0, tag="the spider burns and recoils")
    D.add(108.6, "embers", -12.0, dur=2.4, tag="embers")
    D.add(111.0, "fire_flare", -4.0, tag="fire flares to white (flash crest)")

    # ------------------------------------------------------------------ s09 DAWN
    for i, (t, p, g) in enumerate(((111.25, -0.5, -14.0), (111.75, 0.4, -16.0), (112.3, -0.1, -15.0),
                                   (112.85, 0.6, -18.0), (113.6, -0.6, -19.0))):
        D.add(t, "hood_fall", g, p, lock="free", tag=f"red hood {i + 1} falls")
    D.add(113.0, "wolf_wounded", -12.0, 0.25, dur=12.0, tag="the wolf lies wounded, breathing", rate=0.33)
    D.steps(114.6, 117.3, 1.6, gain_db=-14.0, pan=-0.2, pan1=0.15, tag="she walks to it", weight=0.2)
    D.add(118.0, "cloth_rustle", -16.0, 0.15, tag="she kneels by the wolf", size=0.5)
    D.add(118.05, "kneel_snow", -11.0, 0.15, tag="she kneels by the wolf", weight=0.25)
    nv = A(18, "never")
    D.add(nv, "fur_touch", -8.0, 0.2, lock="word", tag="she touches its muzzle on 'never'")
    D.add(nv + 0.5, "eyes_glint", -18.0, 0.25, tag="its eyes open", low=1)
    D.add(nv + 1.1, "wolf_whine", -14.0, 0.25, tag="a soft whine")

    # ------------------------------------------------------------------ s10 MONSTER
    D.steps(125.6, 131.2, 1.8, gain_db=-12.0, tag="s10 she walks home", weight=0.25)
    D.add(131.05, "door_wood", -8.0, 0.6, tag="a door shuts", force=0.6)
    D.add(A(20, "monster"), "door_wood", -5.0, -0.5, lock="word", tag="doors shut on 'monster'", force=0.9)
    D.add(133.1, "door_wood", -10.0, 0.35, tag="a far door", force=0.5)
    D.add(132.55, "flame_flutter", -17.0, 0.4, dur=2.5, tag="a lantern raised at her", wind=0.4)
    D.steps(133.25, 134.6, 3.0, gain_db=-10.0, pan=-0.35, pan1=-0.05, tag="her mother runs out", pace="run", weight=0.7)
    D.add(134.75, "kneel_snow", -9.0, tag="mother kneels", weight=0.7)
    D.add(134.85, "cloth_rustle", -10.0, tag="holds her tight", size=0.9)
    D.add(135.6, "cloth_rustle", -16.0, tag="the embrace", size=0.5)
    D.add(139.0, "white_swell", -10.0, tag="dip to snow-white (years pass)")

    # ------------------------------------------------------------------ s11 GRANDMOTHER'S HOUSE
    D.add(140.2, "wolf_breath", -19.0, 0.25, dur=9.0, tag="the old wolf by the step", rate=0.3, intensity=0.3)
    D.add(A(22, "one"), "lantern_light", -8.0, -0.15, lock="word", tag="she lights the last lantern on 'one'")
    D.steps(147.0, 151.8, 1.9, gain_db=-18.0, pan=0.45, pan1=0.1, gain1=-13.0, tag="a small child walks up the path",
            weight=0.12)
    D.add(148.4, "cloth_rustle", -20.0, tag="Old Red raises a hand", size=0.3)
    D.add(148.95, "wolf_huff", -18.0, 0.25, tag="the old wolf lifts its head")
    D.add(152.0, "flatten", -8.0, tag="flatten to Bass (end)")
    D.add(152.35, "paper_pop", -14.0, tag="the red triangle at the end of the path")
    return D.cues


# ============================================================================ scene hints
def scene_hints():
    """All scenes' cues(T) on the film clock. Missing scenes are fine (the sheet is primary)."""
    hints, status = [], dict(scenes_with_cues=[], scenes_without_module=[], scenes_without_cues=[], errors=[])
    try:
        from engine.render import scene_path, scene_module
    except Exception as e:  # noqa: BLE001
        status["errors"].append(f"engine.render import: {e!r}"[:300])
        return hints, status
    for sid in SCENE_IDS:
        try:
            if scene_path("red", sid) is None:
                status["scenes_without_module"].append(sid)
                continue
            mod, T = scene_module("red", sid)
        except Exception as e:  # noqa: BLE001
            status["errors"].append(f"{sid}: {e!r}"[:300])
            continue
        if mod is None or not hasattr(mod, "cues"):
            status["scenes_without_cues"].append(sid)
            continue
        try:
            lst = list(mod.cues(T) or [])
        except Exception as e:  # noqa: BLE001
            status["errors"].append(f"{sid}.cues(): {e!r}"[:300])
            continue
        status["scenes_with_cues"].append(sid)
        for i, c in enumerate(lst):
            if not isinstance(c, dict) or "t" not in c or "sfx" not in c:
                status["errors"].append(f"{sid} cue {i}: malformed {c!r}"[:200])
                continue
            hints.append(dict(scene=sid, idx=i, t=float(c["t"]) + T.start, text=str(c["sfx"]),
                              gain_db=float(c.get("gain_db", 0.0)), pan=float(c.get("pan", 0.0)), dur=c.get("dur"),
                              params=dict(c.get("params") or {})))
    return sorted(hints, key=lambda h: h["t"]), status


BED_MIN = 4.0     # sustained cues at least this long are 'beds': a scene bed matches a designed one by overlap


def _bed_overlap(c, h, name):
    """Designed sustained cue c and scene hint h (resolved to `name`) are the same bed: both long and
    overlapping for at least half of the shorter one."""
    if sfx_red.spec(c["sfx"])["kind"] != "sustained" or sfx_red.spec(name)["kind"] != "sustained":
        return False
    dc = float(c["dur"] or sfx_red.spec(c["sfx"])["default_dur"] or 0.0)
    dh = float(h["dur"] or sfx_red.spec(name)["default_dur"] or 0.0)
    if min(dc, dh) < BED_MIN:
        return False
    ov = min(c["t"] + dc, h["t"] + dh) - max(c["t"], h["t"])
    return ov >= 0.5 * min(dc, dh)


def merge(design, hints):
    cues = [dict(c) for c in design]
    rep = dict(snapped=[], kept_word_locked=[], added=[], replaced_sequences=[], unknown=[])
    resolved = []
    stops = {}
    for h in hints:
        if resolve(h["text"]) == STOP_MARK:
            stops.setdefault(h["scene"], []).append(h["t"])
            rep.setdefault("walk_stops", []).append(dict(scene=h["scene"], t=round(h["t"], 3), text=h["text"]))
    for h in hints:
        name = resolve(h["text"])
        if name == STOP_MARK:
            continue
        if name is None:
            rep["unknown"].append(dict(scene=h["scene"], t=round(h["t"], 3), sfx=h["text"]))
            continue
        fam = family(name)
        if fam in SEQ_FAMILIES and h.get("dur") and float(h["dur"]) >= 0.8:
            ends = [x for x in stops.get(h["scene"], []) if x > h["t"]]
            resolved += [(e, name, fam) for e in expand_steps(h, fam) if not ends or e["t"] < min(ends) - 0.05]
            rep.setdefault("expanded_step_cues", []).append(dict(scene=h["scene"], t=round(h["t"], 3), text=h["text"]))
            continue
        resolved.append((h, name, fam))
    # footstep sequences from a scene replace the designed ones over their span
    for sid in sorted(set(h["scene"] for h, _, _ in resolved)):
        for fam in SEQ_FAMILIES:
            seq = [(h, nm) for h, nm, f in resolved if h["scene"] == sid and f == fam]
            if len(seq) < 3:
                continue
            a = min(h["t"] for h, _ in seq) - 0.3
            b = max(max(h["t"], h.get("span_end", h["t"])) for h, _ in seq) + 0.3
            inside = [c for c in cues if c["sid"] == sid and family(c["sfx"]) == fam and a <= c["t"] <= b
                      and c["source"] == "design"]
            # a designed walk the scene's walk overlaps is replaced whole (no stray steps after she stops)
            tags = {c["tag"] for c in inside}
            proto = [c for c in cues if c["sid"] == sid and family(c["sfx"]) == fam and c["source"] == "design"
                     and c["lock"] != "word" and (a <= c["t"] <= b or c["tag"] in tags)]
            gains = [c["gain_db"] for c in proto]
            cues = [c for c in cues if not any(c is q for q in proto)]
            g = float(np.median(gains)) if gains else None
            params = dict(proto[0]["params"]) if proto else {}
            ref = seq[0][0]["gain_db"] or 0.0
            for h, nm in seq:
                # designed level, the scene's own pattern on top (alternate feet, a receding fade)
                cues.append(dict(t=h["t"], sfx=proto[0]["sfx"] if proto else nm,
                                 gain_db=g + ((h["gain_db"] or 0.0) - ref) if g is not None else scene_gain(h, fam),
                                 pan=h["pan"], dur=h["dur"], params={**params, **h["params"]}, lock="free",
                                 tag=f"{sid} scene steps", sid=sid, source="scene",
                                 seed=int(dsp.stable_seed("red-scene-cue", sid, h["idx"]) % (1 << 31))))
            rep["replaced_sequences"].append(dict(scene=sid, family=fam, span=[round(a, 2), round(b, 2)],
                                                  removed=len(proto), added=len(seq)))
            resolved = [(h, nm, f) for h, nm, f in resolved if not (h["scene"] == sid and f == fam)]
    used = set()
    for h, name, fam in resolved:
        cand = [c for c in cues if c["sid"] == h["scene"] and c["source"] == "design" and id(c) not in used
                and family(c["sfx"]) == fam and (fam != "graphic" or c["sfx"] == name)
                and (abs(c["t"] - h["t"]) <= SNAP or _bed_overlap(c, h, name))]
        if cand:
            c = min(cand, key=lambda c: abs(c["t"] - h["t"]))
            used.add(id(c))
            if c["lock"] == "word":
                rep["kept_word_locked"].append(dict(tag=c["tag"], t=c["t"], scene_t=round(h["t"], 3)))
            else:
                rep["snapped"].append(dict(tag=c["tag"], from_t=c["t"], to_t=round(h["t"], 3)))
                c["t"] = round(h["t"], 4)
            if abs(h["pan"]) > 1e-6:
                c["pan"] = h["pan"]
            if h["dur"] is not None and sfx_red.spec(c["sfx"])["kind"] == "sustained":
                c["dur"] = float(h["dur"])
            continue
        g = scene_gain(h, fam)
        cues.append(dict(t=round(h["t"], 4), sfx=name, gain_db=g, pan=h["pan"], dur=h["dur"], params=h["params"],
                         lock="beat", tag=f"{h['scene']}: {h['text']}", sid=h["scene"], source="scene",
                         seed=int(dsp.stable_seed("red-scene-cue", h["scene"], h["idx"]) % (1 << 31)),
                         decay=bool(sfx_red.spec(name)["kind"] == "sustained"
                                    and re.search(r"dying|dies away|die away|fading|fades|dwindl", h["text"].lower()))))
        rep["added"].append(dict(scene=h["scene"], t=round(h["t"], 3), text=h["text"], sfx=name, gain_db=round(g, 1)))
    return sorted(cues, key=lambda c: c["t"]), rep


def cues(use_scenes=True, hints=None):
    design = designed()
    st = dict(scenes_with_cues=[], scenes_without_module=list(SCENE_IDS), scenes_without_cues=[], errors=[])
    if hints is None and use_scenes:
        hints, st = scene_hints()
    out, rep = merge(design, hints or [])
    rep.update(status=st, designed=len(design), total=len(out), hints=len(hints or []))
    return out, rep


if __name__ == "__main__":
    cs, rep = cues()
    for c in cs:
        print(f"{c['t']:8.3f} {c['sid']} {c['sfx']:16s} {c['gain_db']:6.1f} {c['pan']:+.2f} {c['lock']:5s} {c['tag']}")
    print({k: v for k, v in rep.items() if k not in ("status",)}, rep["status"])
