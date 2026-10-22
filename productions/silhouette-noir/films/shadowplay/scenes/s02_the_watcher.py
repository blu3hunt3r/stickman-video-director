"""s02 · THE WATCHER: one continuous camera path, facade -> her window -> street -> facade.

IN   -0.5-0.6  the live facade at exactly the FACADE LOCK (s01's flat end resolves into it),
               lit = NIGHT, window 9 dark, rain falling.
0.6-6.4  the camera drifts (cranes, no tilt) to the three lives across the street:
         [Four] window 4 brightens, the dancer pirouettes alone; [Twelve] the old woman leans
         to her cat on the sill, chats with her hand, the cat answers and flicks its tail on
         [cat]; [Thirty] a woman on the end of her bed, head in her hands, shoulders shaking.
6.4-9.05 dolly back across the street: up, back, through the upper-right pane of HER window
         (the sash slides in round the frame, drops on the glass); she rises into view:
         curled in an armchair at the glass, binoculars in her lap, the steamed lower pane
         wiped clear where she looks.  [watch] she lifts the binoculars (glint).
9.85-10.95 push over her head, through the pane, out into the rain and tilt down to the
         street far below; three umbrellas pass and break in the puddles. Nobody looks up.
[up]     tilt back up (11.95-12.85) and push in as her binocular view; SHADOW / PLAY slide in
         along the facade's grid lines (rows 3 and 5), hold ~1.4 s, slide off (14.75-15.3).
OUT 14.35-15.5  window 9 dark, centred, 200 px wide (zoom 0.78), 3 px handheld drift:
         _lib.END_RIG + bino_shake - s03 renders the same world at t + 15.
"""
import math

from engine.core import smoothstep
from engine.timing import Cue
from films.shadowplay.scenes import _lib_s02_s04 as L

# ----------------------------------------------------------------------------- the camera path
# Phases A-C are pure translations (the camera stays square to the facade, aimed straight
# ahead): (u, v) = fac_xy(X, Y). After 10.15 the aim tilts away from straight ahead.
_C = L.Spline([(-1.0, L.LOCK_C), (0.6, L.LOCK_C, "hold"), (1.45, 8.4375), (2.1, 8.13), (2.6, 9.6), (3.1, 7.34),
               (4.35, 7.10), (4.8, 9.0), (5.25, 7.10), (6.4, 6.95, "hold"), (7.6, 15.0), (8.35, 20.0),
               (9.05, 21.85, "hold"), (9.85, 21.85, "hold"), (10.45, 20.0), (10.9, L.END_C, "hold"),
               (16.0, L.END_C)])
_XY = L.Spline([(-1.0, (0.0, L.LOCK_Y)), (0.6, (0.0, L.LOCK_Y), "hold"), (1.45, (2.9475, 25.575)),
                (2.1, (3.0, 25.46)), (3.1, (-2.925, 20.06)), (4.35, (-3.0, 19.99)), (5.25, (6.0375, 11.06)),
                (6.4, (6.075, 10.99), "hold"), (7.6, (1.6, 18.8)), (8.35, (0.36, 20.92)),
                (9.05, (0.10, 20.32), "hold"), (9.85, (0.10, 20.32), "hold"), (10.45, (L.END_X, L.END_Y)),
                (16.0, (L.END_X, L.END_Y))])
_AHEAD_END = L.fac_xy(L.END_X, L.END_Y)


def _off(p):
    return (p[0] - _AHEAD_END[0], p[1] - _AHEAD_END[1])


STREET_AIM0, STREET_AIM1 = (960.0, 4640.0), (1010.0, 4590.0)     # down on the diner's sidewalk
_AIM = L.Spline([(-1.0, (0.0, 0.0)), (10.15, (0.0, 0.0), "hold"), (10.95, _off(STREET_AIM0)),
                 (11.95, _off(STREET_AIM1), "hold"), (L.BINO_T0, _off(L.TITLE_AIM), "hold")])
_F = L.Spline([(-1.0, 900.0), (10.2, 900.0, "hold"), (10.95, L.END_F), (11.95, L.END_F, "hold"),
               (L.BINO_T0, L._zf_F(L.TITLE_ZF), "hold")])


def rig_at(t):
    if t >= L.BINO_T0:
        return L.bino_rig(t)                   # shared with s03 (t + 15): the seam is exact
    c = _C(t)
    X, Y = _XY(t)
    du, dv = _AIM(t)
    u, v = L.fac_xy(X, Y)
    return L.Rig(_F(t), c, X, Y, u + du, v + dv, L.bino_shake(t))


def street_depth(t):
    return 560.0 + (2800.0 - 560.0) * smoothstep(6.6, 9.5, t)


# ----------------------------------------------------------------------------- words
def _words(T):
    return dict(four=T.at("Four"), alone=T.at("alone"), twelve=T.at("Twelve"), talks=T.at("talks"),
                cat=T.at("cat"), thirty=T.at("Thirty"), cries=T.at("cries"), watch=T.at("watch"),
                nobody=T.at("Nobody"), up=T.at("up"))


WALKERS = (L.Walker(10.6, 865.0, 150.0, -1.0, 1.1, 1),                 # along the diner's window
           L.Walker(10.6, 1376.0, -90.0, 0.08, 1.1, 2, du=0.05),         # crossing in its light
           L.Walker(10.6, 835.0, 120.0, 0.42, 1.1, 3))                   # over the reflections
TITLE_IN, TITLE_OUT = 12.45, 14.4


def _people(f, t, st):
    L.street_pools(f, t, st)
    L.draw_walkers(f, t, st, WALKERS)


def render(f, t, T):
    w = _words(T)
    rig = rig_at(t)
    inter = L.interiors_for((w["four"], w["alone"]), (w["twelve"], w["talks"], w["cat"]),
                            (w["thirty"], w["cries"]))
    people = _people if 9.8 < t < 13.2 else None
    title = None
    if TITLE_IN - 0.1 < t < TITLE_OUT + 1.0:
        title = lambda f_, t_: L.draw_title(f_, t_, TITLE_IN, TITLE_OUT, cx=L.TITLE_AIM[0])
    halo, emit = L.bino_halo_emit(t, rig) if t >= L.BINO_T0 else (None, None)
    L.draw_world(f, t, rig, interiors=inter, flare4=w["four"], street_depth=street_depth(t), people=people,
                 title=title, halo=halo, emit=emit)
    L.draw_room(f, t, rig, watch=w["watch"])


def motion_blur(t, T):
    if 6.9 < t < 8.7 or 9.9 < t < 11.0 or 11.95 < t < 12.6:
        return 3
    if 2.2 < t < 3.0 or 4.4 < t < 5.2 or 0.7 < t < 1.4 or 14.55 < t < 15.05:
        return 2
    return 1


def cues(T):
    w = _words(T)
    return [
        Cue(w["four"], "lamp switch click, warm hum swells (window 4, far)", gain_db=-14, pan=0.3),
        Cue(w["four"] + 0.12, "pirouette: skirt swish, faint music box (far, behind glass)", gain_db=-18, pan=0.3),
        Cue(w["twelve"], "old woman's muffled chatter behind glass", gain_db=-20, pan=-0.35, dur=1.8),
        Cue(w["talks"] + 0.55, "cat meow, muffled by glass", gain_db=-16, pan=-0.4),
        Cue(w["cat"], "cat tail flick: soft swish", gain_db=-22, pan=-0.4),
        Cue(w["cries"], "muffled sobbing, shuddering breaths (far)", gain_db=-20, pan=0.45, dur=1.6),
        Cue(6.5, "camera pulls back across the street: rain swells, low whoosh", gain_db=-10, dur=1.9),
        Cue(8.35, "through the glass: rain on the pane close up, room tone", gain_db=-9),
        Cue(w["watch"] - 0.05, "binoculars lifted: cloth rustle, strap", gain_db=-10, pan=0.15),
        Cue(w["watch"] + 0.36, "glint: tiny glass ting", gain_db=-14, pan=-0.1),
        Cue(10.4, "push through the pane: rain roar opens, wind", gain_db=-8),
        Cue(10.9, "street far below: footsteps on wet pavement, rain on umbrellas", gain_db=-14, dur=1.2),
        Cue(w["up"], "whip tilt up: whoosh", gain_db=-10),
        Cue(12.8, "title SHADOW slides in: paper swish (left)", gain_db=-9, pan=-0.4),
        Cue(12.9, "title PLAY slides in: paper swish (right)", gain_db=-9, pan=0.4),
        Cue(14.4, "binocular focus ring click", gain_db=-13),
        Cue(14.75, "title slides off: paper swish", gain_db=-11),
    ]
