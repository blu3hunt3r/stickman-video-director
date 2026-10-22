"""s03 · WINDOW NINE: her binocular view of window 9 (dark for a year; on Tuesday at eleven the
light comes on; the shadow murder on its sheet), then the reverse: her face behind her own
steamed, rain-beaded glass, the binoculars coming down, the eyes wide.

IN   -0.5-13.0 her binocular view, inside bass.binoculars(ctx, (540, 960), 300, 330, ink, seed=0):
          the s02 world, rig and 3 px handheld drift at tw = t + 15 (_lib.bino_rig), so the
          seam with s02's end is exact: window 9 dark (its pale sheet), centred, 200 px wide.
0.6-3.9   [L6] slow push on the dark window (zoom 0.78 -> 0.97).
4.8-8.0   [L7] [light@7.157] the window flickers on: the sheet glows amber with the two
          silhouettes facing each other; 7.35-8.3 the binoculars zoom in (zoom 1.07 -> 1.7).
8.0-12.5  the shadow play (_lib_shadow_show, start 8.0): she turns away, his jagged arm rises,
          three stabs (9.85, 10.25, 10.65), the RED splash, she folds and falls; 12.3 the
          light snaps out. 12.3-13.0 the dark window again.
13.0      hard match inside the lenses: her binoculars' objectives, staring back, in the
          middle of the two circles; the mask opens wide (13.05-13.9) and the camera pulls
          back through her window (13.05-14.7): her, at her dark window, the steamed pane
          wiped clear where she watches, rain on the glass.
14.75-15.3 [L8] the binoculars come down; [Every@15.148] her eyes wide, unblinking; slow push
          on them, the frame closing to dark.
OUT 17.0  (hard cut) her eyes glow at (540, 900) in a dark frame.
"""
import math

import cairo

from engine import bass, draw
from engine.core import W, H, clamp, lerp, smoothstep
from engine.frame import GLOW_DS
from engine.timing import Cue, SceneTiming
from films.shadowplay import sets
from films.shadowplay.scenes import _lib_s02_s04 as L
from films.shadowplay.scenes import _lib_shadow_show as show

T2 = SceneTiming("shadowplay", "s02")
OFF = T2.duration                     # s02 time of this scene's t = 0 (the cut)
SHOW_START = 8.0                      # u = 0 of the shadow play (light out at 12.3)
OPEN_T = 13.0                         # the reverse
LOWER_T = 14.75                       # the binoculars start down
FROZEN_T = 15.15                      # eyes wide, no blink from here
MASK_C, MASK_R, MASK_SEP = (540.0, 960.0), 300.0, 330.0


def _s02_words():
    return dict(four=T2.at("Four"), alone=T2.at("alone"), twelve=T2.at("Twelve"), talks=T2.at("talks"),
                cat=T2.at("cat"), thirty=T2.at("Thirty"), cries=T2.at("cries"))


def nine_level(t, T):
    """Window 9's lamp (s03 time): flickers on at [light], snaps out at 12.3."""
    return 0.85 * sets.switch(t, T.at("light"), kind="flicker", seed=9) * show.lamp_level(t - SHOW_START)


# ----------------------------------------------------------------------------- the binocular view
def mask(f, s=1.0):
    """The binocular mask (exactly the s02 -> s03 transition's shape at s = 1), scaled by s
    about its centre; it also erases the bloom buffer outside the lenses."""
    r, sep = MASK_R * s, MASK_SEP * s
    with f.screen() as S:
        bass.binoculars(S, MASK_C, r, sep, sets.PAL.ink, seed=0)
    G = f.g
    G.save()
    G.set_matrix(cairo.Matrix(xx=f.scale / GLOW_DS, yy=f.scale / GLOW_DS))
    G.new_path()
    G.rectangle(-10, -10, W + 20, H + 20)
    for p in bass.binocular_pts(MASK_C, r, sep, 0):
        draw.poly(G, p)
    G.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    G.set_operator(cairo.OPERATOR_CLEAR)
    G.fill()
    G.restore()


def draw_pov(f, t, T):
    """The world through her binoculars at s02 time tw = t + 15 (same rig, same lives)."""
    tw = t + OFF
    rig = L.bino_rig(tw)
    w = _s02_words()
    inter = L.interiors_for((w["four"], w["alone"]), (w["twelve"], w["talks"], w["cat"]), (w["thirty"], w["cries"]))
    inter[9] = show.interior(lambda tt: tt - OFF - SHOW_START)
    hk, ek = L.bino_halo_emit(tw, rig)
    e = smoothstep(5.5, 7.1, t)                 # the facade's bloom eased off before the show
    L.draw_world(f, tw, rig, lit=L.facade_lit(tw, {9: lambda tt: nine_level(tt - OFF, T)}), interiors=inter,
                 flare4=w["four"], street_depth=2800.0, halo=lerp(hk, 0.3, e), emit=lerp(ek, 0.0, e))


# ----------------------------------------------------------------------------- the reverse
# the close-up camera: F px, D m from her face, (X, Y) the lateral point at the screen centre.
_F = 2600.0
_D0 = _F / (MASK_SEP / (42.0 * L.BINO_SCALE) * L.ROOM_K)     # the objectives sit on the mask's lenses
_D = L.Spline([(OPEN_T, _D0, "hold"), (13.05, _D0, "hold"), (14.7, 3.2, "hold"), (15.25, 3.2, "hold"),
               (17.0, 1.55)])
_XY = L.Spline([(OPEN_T, (0.0, 9.0), "hold"), (13.05, (0.0, 9.0), "hold"), (14.7, (29.5, 42.0), "hold"),
                (15.25, (29.5, 42.0), "hold"), (17.0, (0.0, 60.0 / (_F / (1.55 * L.ROOM_K))))])


def close_rig(t):
    X, Y = _XY(t)
    sh = L.bino_shake(t + OFF)
    k = 1.0 - smoothstep(OPEN_T, OPEN_T + 0.6, t)   # her hands still shake a little at first
    return L.CloseRig(_F, _D(t), X, Y, (sh[0] * k, sh[1] * k))


def mask_open(t):
    """Scale of the binocular mask as it opens (1 = closed on the lenses)."""
    return 1.0 + 3.6 * L.kseg(t, OPEN_T + 0.05, OPEN_T + 0.9, "in3")


def render(f, t, T):
    if t < OPEN_T:
        draw_pov(f, t, T)
        mask(f)
        return
    rig = close_rig(t)
    dark = smoothstep(15.9, 17.0, t)
    L.draw_her_closeup(f, t, rig, lower_t=LOWER_T, frozen=FROZEN_T, wall=1.0 - 0.7 * dark,
                       glass=1.0 - 0.5 * dark, dark=dark)
    s = mask_open(t)
    if s < 4.5:
        mask(f, s)


def motion_blur(t, T):
    if 7.4 < t < 8.2 or 13.2 < t < 14.5:
        return 2
    return 1


def cues(T):
    light = T.at("light")
    st = SHOW_START
    return [
        Cue(0.6, "binocular hush: rain across the street, far traffic, her slow breathing", gain_db=-16, dur=3.0),
        Cue(light, "far lamp switch: a click and the hum of an old filament, flickering", gain_db=-14, pan=0.1),
        Cue(st + show.TURN_T[0], "paper doll turning on its rod (felt, far): a dry flick", gain_db=-24),
        Cue(st + show.RAISE_T[0], "the arm rises: a low string swell", gain_db=-16, dur=0.6),
        Cue(st + show.STAB_TIMES[0], "stab 1: a muffled thud, her breath catches", gain_db=-12),
        Cue(st + show.STAB_TIMES[1], "stab 2: muffled thud", gain_db=-12),
        Cue(st + show.STAB_TIMES[2], "stab 3: muffled thud + wet paper tear (the RED splash)", gain_db=-10),
        Cue(st + show.FALL_T, "she falls: a soft paper slump", gain_db=-20),
        Cue(st + show.LIGHT_OUT_T, "the light snaps out: a tiny click, then silence", gain_db=-12),
        Cue(OPEN_T, "reverse: lens glass ring, rain loud on her pane close by", gain_db=-10),
        Cue(LOWER_T, "binoculars lowered: sleeve rustle, strap", gain_db=-14),
        Cue(FROZEN_T, "she stops breathing: room tone drops out, a thin high tone", gain_db=-18, dur=1.8),
        Cue(16.6, "one slow heartbeat", gain_db=-12),
    ]
