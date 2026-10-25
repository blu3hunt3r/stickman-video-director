"""s09 · PLAN B (128-146): her way out, the one only she knew.

  0-2    From straight above, by the Cracker's match: kneeling, she lifts the cut block out of the
         vault's floor and lays it aside; below is black, and the top rungs of a ladder.
  2-3    The Cracker's face lit from below by his match: the light crosses his spectacles (2.1)
         and he grins (2.4).
  3-7    The section, close on the shaft she cut: she slides down its ladder into the dark and
         splashes into the sewer (4.2); he follows, the match held up (5.6); they wade off left,
         toward the street.
  7-18   The street in section, wide (OPPOSITE's mirrored race). The bell rings over the side door,
         red ripples on every beat. Above, the Knight flings the sacks into his car and slams its
         door (7.3, 7.6); the engine coughs and coughs; the tenement wakes window by window (9.5-11)
         and then the city (11.5). Below, their footstep dots go left along the sewer. He is out
         again on the gully's grating and kicks the tyre (11.3): she has stopped right under him.
         A lens, her view up through the bars at his boots (11.0-12.55). He gets back in and the
         engine catches (12.0). They go on under the road to manhole B; the match goes out; they
         climb, she first, and she stops under the lid. 16-18: the police lights begin to sweep
         the street (a far siren).
"""
import math
from functools import lru_cache

import cairo

from engine import bass, draw as D, paperdoll as pd
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import faces as F
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import street as St

k = K.k
W, H = K.W, K.H
INK, PAPER, AMBER, RED, NIGHT, STEEL, DEEP, POLICE = K.INK, K.PAPER, K.AMBER, K.RED, K.NIGHT, K.STEEL, K.DEEP, K.POLICE
T0 = K.film_start("s09")                  # film time of this scene's t = 0
FS = St.FIG_S

# ---------------------------------------------------------------- beats (scene time)
T_LIFT = (0.2, 0.5)                       # the block comes up out of the floor, toward us ...
T_ASIDE = (0.5, 0.9)                      # ... and is laid aside, off to the left
T_RIM = (0.9, 1.25)                       # her hands back to the hole's rim
T_LEAN_IN = 1.4                           # his match comes in over the hole
T_FACE = 2.0                              # his face, lit from below
T_GLINT = (2.05, 2.35)                    # the light crosses his spectacles
T_GRIN = 2.4
T_SEC = 3.0                               # the shaft, in section
T_SLIDE_H = (3.2, 4.2)                    # she slides down the ladder ...
T_SPLASH_H = 4.2                          # ... into the water
T_TURN_H = (4.45, 4.65)                   # and turns to face the way out
T_STEP_C = (4.3, 4.5)                     # he steps down into the hole
T_SLIDE_C = (4.5, 5.6)                    # and slides down, the match held up
T_SPLASH_C = 5.6
T_TURN_C = (5.75, 5.95)
T_GO_H, T_GO_C = 5.8, 6.0                 # they wade off left
T_WIDE = 7.0                              # the street in section
T_FLING = 7.3                             # the Knight flings the sacks in ...
T_SLAM = 7.6                              # ... and slams the car's door
T_IN = (7.7, 7.95)                        # he ducks in
T_COUGHS = (8.0, 8.5, 9.1, 9.7)           # the engine coughs
T_WAKE = {5: 9.5, 3: 10.0, 2: 10.5, 1: 11.0}   # the tenement's windows light, storey by storey
T_CITY = 11.5                             # and the city's
T_OUT = (10.2, 10.45)                     # his door flung open: he is out, on the grating
T_LOOKS = (10.45, 10.8, 11.05)            # he looks round: the bank, the windows, the car
T_KICK = 11.3                             # he kicks the tyre
T_BACK_IN = (11.6, 11.85)
T_SLAM2 = 11.9
T_CATCH = 12.0                            # the engine catches
T_UNDER_H = 10.8                          # she has stopped right under him, under the grating
T_UNDER_C = 10.95
T_LENS = (11.0, 12.55)                    # her view up through it
T_ON_H, T_ON_C = 12.6, 12.75              # they go on
T_AT_B_H, T_AT_B_C = 14.9, 15.1           # manhole B
T_DOUSE = 14.95                           # he shakes the match out
T_CLIMB_H = (15.0, 16.1)                  # up its shaft, she first; she stops under the lid
T_CLIMB_C = (15.45, 16.35)
T_SWEEP = 16.0                            # the police lights begin to sweep (a far siren)
BEATS = tuple(T_WIDE + 0.5 * i for i in range(22))      # the bell's strokes, on the beat

AFTER = dict(lit={}, hall_lamp=1.0, vault_lit=0.0, gold_glow=0.0, gold=0.0, ruby_box=1.0, ruby=False, vault_door=0.0,
             side_door=1.0, hatch=0.0, lid_a=1.0, tile=0.0, trap_shaft=True, beams=False, sky_lit=0.0, lamp_on=1.0,
             clock=(12, 20), drips=True)      # the hatch shut and manhole A open, as s04 left them


def motion_blur(t, T):
    return 1


# ================================================================ light
def flicker(t):
    tt = K.twos(T0 + t)
    return 1.0 + 0.05 * math.sin(tt * 17.0) + 0.03 * math.sin(tt * 41.0)


def darkness(c, p, r, steps=((1.0, 0.45), (1.16, 0.75), (1.34, 1.0)), seed=0):
    """The dark beyond the match's light: INK over everything outside radius r of p, in three cut
    steps (no blur)."""
    for kk, a in steps:
        rr = r * kk
        pts = [(p[0] + rr * (1.0 + 0.012 * math.sin(i * 1.7 + seed)) * math.cos(2.0 * math.pi * i / 96.0),
                p[1] + rr * (1.0 + 0.012 * math.sin(i * 1.7 + seed)) * math.sin(2.0 * math.pi * i / 96.0))
               for i in range(96)]
        c.save()
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.new_path()
        c.rectangle(-4000.0, -4000.0, 9000.0, 9000.0)
        D.poly(c, pts)
        c.set_source_rgba(*INK, a)
        c.fill()
        c.restore()


def glow(c, p, r, a):
    K.pool(c, p, r, r, AMBER, a, steps=5)


def rim(c, draw_fn, color, off, alpha=1.0):
    """draw_fn's silhouette laid in `color`, shifted by off: the edge the light catches."""
    c.save()
    c.push_group()
    draw_fn(c)
    m = c.pop_group()
    c.translate(*off)
    c.set_source_rgba(*color, alpha)
    c.mask(m)
    c.restore()


def match_stick(c, p, t, s=1.0, ang=-8.0):
    """A lit match held at its foot (p its head): the stick, the fingertips, the flame."""
    a = math.radians(90.0 + ang)
    base = (p[0] + 92.0 * s * math.cos(a), p[1] + 92.0 * s * math.sin(a))
    bass.line_band(c, [base, p], lerp(PAPER, AMBER, 0.35), width=7.0 * s, seed=901)
    K.dot(c, p, 6.0 * s, INK, seed=902)
    K.dot(c, base, 15.0 * s, INK, seed=903)
    K.flame(c, (p[0], p[1] + 2.0 * s), T0 + t, s=1.15 * s * flicker(t), seed=4)


def tiny_flame(c, p, t, s=0.16):
    """The match in the section: a tiny flame at p (section px)."""
    c.save()
    c.translate(p[0], p[1])
    c.scale(s, s)
    K.flame(c, (0.0, 0.0), T0 + t, s=flicker(t), seed=4)
    c.restore()


# ================================================================ 0-2: the tile, from straight above
OV_T = 400.0                              # a floor tile, frame px
OV_C = (540.0, 900.0)                     # the cut block's middle
OV_FLAME0 = (230.0, 470.0)                # his match, held low over the floor, up and left of the block
OV_STONE = lerp(STEEL, INK, 0.55)
OV_SEAM = lerp(STEEL, INK, 0.85)
OV_SHOULDERS = ((290.0, 1730.0), (790.0, 1730.0))


def ov_flame(t):
    lean = k(t, T_LEAN_IN, 0.5, "inout")
    return (lerp(OV_FLAME0[0], 320.0, lean), lerp(OV_FLAME0[1], 580.0, lean))


def ov_block(t):
    """(centre, scale, up, aside) of the block from above: lifted toward us, laid aside left."""
    up = k(t, T_LIFT[0], T_LIFT[1] - T_LIFT[0], "inout")
    aside = k(t, T_ASIDE[0], T_ASIDE[1] - T_ASIDE[0], "inout")
    s = 1.0 + 0.18 * up - 0.12 * aside
    return (OV_C[0] - 800.0 * aside, OV_C[1] - 24.0 * up + 160.0 * aside), s, up, aside


def ov_hands(t):
    """Her two gloved hands from above: on the block's sides while she lifts it, then back to the
    rim of the hole."""
    bc, s, up, aside = ov_block(t)
    half = OV_T * s / 2.0
    on_block = [(bc[0] - half - 6.0, bc[1] + 30.0), (bc[0] + half + 6.0, bc[1] + 30.0)]
    reach = k(t, 0.0, T_LIFT[0], "out")                     # her hands come in to the block's sides
    rest = [(OV_C[0] - 240.0, OV_C[1] + 470.0), (OV_C[0] + 240.0, OV_C[1] + 470.0)]
    rimp = [(OV_C[0] - OV_T / 2.0 - 10.0, OV_C[1] + 60.0), (OV_C[0] + OV_T / 2.0 + 10.0, OV_C[1] + 60.0)]
    back = k(t, T_RIM[0], T_RIM[1] - T_RIM[0], "inout")
    out = []
    for i in range(2):
        p = (lerp(rest[i][0], on_block[i][0], reach), lerp(rest[i][1], on_block[i][1], reach))
        out.append((lerp(p[0], rimp[i][0], back), lerp(p[1], rimp[i][1], back)))
    return out


def ov_floor(c):
    K.fill(c, OV_SEAM)
    x0 = OV_C[0] - OV_T / 2.0 - 3.0 * OV_T
    y0 = OV_C[1] - OV_T / 2.0 - 4.0 * OV_T
    for i in range(8):
        for j in range(10):
            x, y = x0 + i * OV_T, y0 + j * OV_T
            tone = lerp(OV_STONE, INK, 0.12 * K.hash01(i * 13 + j, 1301))
            bass.fill_polys(c, [bass.cut_rect(x + 5.0, y + 5.0, x + OV_T - 5.0, y + OV_T - 5.0, seed=1310 + i * 10 + j,
                                              amp=1.2)], tone)


def ov_hole(c, t):
    """The hole where the block was: black, the shaft's top rungs going down into it, and far
    below a glint of the match on the water."""
    x0, y0 = OV_C[0] - OV_T / 2.0, OV_C[1] - OV_T / 2.0
    bass.fill_polys(c, [bass.cut_rect(x0, y0, x0 + OV_T, y0 + OV_T, seed=1320, amp=0.8)], INK)
    for i in range(4):
        d = 1.0 + 0.55 * i
        w, y = 0.34 * OV_T / d, OV_C[1] - 0.36 * OV_T / d
        bass.fill_polys(c, [bass.cut_rect(OV_C[0] - w, y - 9.0 / d, OV_C[0] + w, y + 9.0 / d, seed=1321 + i, amp=0.4)],
                        lerp(STEEL, INK, 0.35 + 0.17 * i))
    g = k(t, T_ASIDE[1], 0.3, "out")
    if g > 0.0:
        f = ov_flame(t)
        p = (OV_C[0] + (f[0] - OV_C[0]) * 0.12, OV_C[1] + (f[1] - OV_C[1]) * 0.12 + 40.0)
        K.dot(c, p, 7.0 * flicker(t), AMBER, seed=1325, alpha=0.75 * g)


def ov_block_draw(c, t):
    bc, s, up, aside = ov_block(t)
    half = OV_T * s / 2.0
    if up > 0.0:                                            # its shadow on the floor, away from the match
        sx, sy = bc[0] + 60.0 * up, bc[1] + 74.0 * up
        bass.fill_polys(c, [bass.cut_rect(sx - OV_T / 2.0, sy - OV_T / 2.0, sx + OV_T / 2.0, sy + OV_T / 2.0, seed=1330,
                                          amp=0.8)], INK, 0.55)
    bass.fill_polys(c, [bass.cut_rect(bc[0] - half, bc[1] - half, bc[0] + half, bc[1] + half, seed=1331, amp=1.0)],
                    lerp(OV_STONE, STEEL, 0.12))
    bass.line_band(c, [(bc[0] - half, bc[1] + half - 4.0), (bc[0] - half, bc[1] - half), (bc[0] + half - 4.0, bc[1] - half)],
                   AMBER, width=6.0, seed=1332, alpha=0.75)


def her_from_above(c, t, hands):
    """The top of her head and her shoulders at the foot of the frame, her arms up to her hands."""
    polys = [bass.orient(D.ellipse_pts((540.0, 1800.0), 340.0, 130.0, n=48), True),
             bass.orient(D.ellipse_pts((540.0, 1590.0), 124.0, 146.0, n=40), True),
             bass.orient(D.ellipse_pts((540.0, 1712.0), 70.0, 60.0, n=28), True)]
    bass.fill_polys(c, polys, INK)
    for i, (sh, hp) in enumerate(zip(OV_SHOULDERS, hands)):
        mid = ((sh[0] + hp[0]) / 2.0, (sh[1] + hp[1]) / 2.0)
        n = math.hypot(hp[0] - sh[0], hp[1] - sh[1])
        side = -1.0 if i == 0 else 1.0
        elbow = (mid[0] + side * max(0.0, 560.0 - n) * 0.5, mid[1])           # the elbows out when the hands come close
        bass.line_band(c, [sh, elbow, hp], INK, width=110.0, seed=1340 + i, taper=(1.0, 0.72))
        bass.fill_polys(c, [bass.ring_pts(hp, 50.0, seed=1342 + i, n=24, amp=0.6)], INK)
    # the pencil through her chignon
    bass.line_band(c, [(470.0, 1690.0), (624.0, 1748.0)], lerp(PAPER, AMBER, 0.3), width=9.0, seed=1344)


def cracker_hand_above(c, t):
    f = ov_flame(t)
    hand = (f[0] - 34.0, f[1] - 46.0)
    bass.line_band(c, [(-80.0, 160.0), (f[0] - 150.0, f[1] - 170.0), hand], INK, width=80.0, seed=1350, taper=(1.0, 0.7))
    bass.fill_polys(c, [bass.ring_pts(hand, 34.0, seed=1351, n=20, amp=0.5)], INK)
    bass.line_band(c, [hand, f], lerp(PAPER, AMBER, 0.35), width=7.0, seed=1352)
    fl = flicker(t)
    K.dot(c, f, 40.0 * fl, AMBER, seed=1353)
    K.dot(c, (f[0] + 3.0, f[1] - 3.0), 17.0 * fl, PAPER, seed=1354)


def draw_tile(c, t):
    f = ov_flame(t)
    fl = flicker(t)
    ov_floor(c)
    glow(c, f, 950.0 * fl, 0.12)
    ov_hole(c, t)                                           # the hole stays black: drawn over the light
    _, _, _, aside = ov_block(t)
    if aside < 1.0:
        ov_block_draw(c, t)
    hands = ov_hands(t)
    fn = (lambda cc: her_from_above(cc, t, hands))
    rim(c, fn, lerp(PAPER, AMBER, 0.5), (-7.0, -7.0))
    fn(c)
    rim(c, lambda cc: cracker_hand_above(cc, t), AMBER, (6.0, 6.0), alpha=0.8)
    cracker_hand_above(c, t)
    darkness(c, f, 1080.0 * fl)


# ================================================================ 2-3: his face, lit from below
CR_EYE_G = (500.0, 760.0)
CR_S_G = 1.25
CR_AT_G = (CR_EYE_G[0] - 70.0 * CR_S_G, CR_EYE_G[1] + 560.0 * CR_S_G)
MATCH_G = (800.0, 1380.0)


def face_pt(at, s, p):
    return (at[0] + (p[0] - 400.0) * s, at[1] + (p[1] - 860.0) * s)


def draw_grin(c, t):
    K.fill(c, DEEP)
    fl = flicker(t)
    glow(c, MATCH_G, 900.0 * fl, 0.12)
    K.match_light(c, MATCH_G, T0 + t, r=1000.0 * fl)
    gl = clamp((t - T_GLINT[0]) / (T_GLINT[1] - T_GLINT[0]))
    fn = (lambda cc: F.cracker(cc, CR_AT_G, CR_S_G, look=0.85, glint=gl, t=T0 + t, field=DEEP, edge=AMBER))
    rim(c, fn, AMBER, (5.0, 11.0))                          # the light from below
    marks = fn(c)
    grin = ease("outback", clamp((t - T_GRIN) / 0.3))
    pts = [face_pt(CR_AT_G, CR_S_G, p) for p in ((530.0, 452.0), (512.0, 456.0 - 3.0 * grin), (494.0, 453.0 - 11.0 * grin),
                                                 (476.0, 444.0 - 20.0 * grin))]
    bass.line_band(c, pts, AMBER, width=10.0, seed=1401, taper=(1.0, 0.45), alpha=0.95)
    if grin > 0.0:
        ch = [face_pt(CR_AT_G, CR_S_G, (452.0 + 12.0 * i, 398.0 - 10.0 * grin - 3.0 * math.sin(math.pi * i / 4.0)))
              for i in range(5)]
        bass.line_band(c, ch, AMBER, width=6.0, seed=1402, taper=(0.4, 0.4), alpha=0.5 * clamp(grin))
    if T_GLINT[0] + 0.05 <= t < T_GLINT[1] + 0.1:
        u = math.sin(math.pi * clamp((t - T_GLINT[0] - 0.05) / 0.35))
        K.twinkle(c, marks["lens"], 80.0, PAPER, u=u, rot=12.0)
    match_stick(c, MATCH_G, t, s=1.3)
    darkness(c, MATCH_G, 1150.0 * fl)


# ================================================================ the figures (section px)
def _dry(who, st, pose, x, floor_y):
    """A figure's joints without drawing it."""
    surf = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    return C.draw(cairo.Context(surf), who, st, pose, x, floor_y, FS, 1, rim=False)


def _flip(j, x, sx):
    return {key: (x + sx * (v[0] - x), v[1]) for key, v in j.items()}


def draw_fig(c, who, st, pose, x, floor_y, sx=1.0, bg=None, rim_w=2.4, light=(0.8, -0.6), eye=True):
    """Drawn facing right and scaled by sx about x (-1 faces left; between, the paper turn).
    Returns the joints where they land."""
    if abs(sx) < 0.04:
        return _flip(_dry(who, st, pose, x, floor_y), x, sx)
    c.save()
    c.translate(x, 0.0)
    c.scale(sx, 1.0)
    c.translate(-x, 0.0)
    j = C.draw(c, who, st, pose, x, floor_y, FS, 1, bg=bg if bg is not None else DEEP, rim_w=rim_w,
               light=(light[0] * (1.0 if sx > 0 else -1.0), light[1]), eye=eye)
    c.restore()
    return _flip(j, x, sx)


def _ik_pt(p, x, floor_y):
    """An ik target (figure units) for section point p, for a figure drawn facing right at x on floor_y."""
    return ("ik", ((p[0] - x) / FS, (p[1] - floor_y) / FS))


def _turn(t, a, b, s0=1.0, s1=-1.0):
    u = ease("inout", clamp((t - a) / (b - a)))
    return math.cos(math.pi * u) if s0 > 0 else -math.cos(math.pi * u)


H_TOP = St.WATER - (St.FEET + St.VSLAB + 34.0)       # feet on the top rung under the slab
H0 = 2.0 * St.RUNG_STEP * 0.25                        # the ladder pose they slide in (hands on the rails)
LADDER_X = St.TRAP_C - 3.0
CR_STAND = 972.0                                      # the Cracker over the hole, the match low over it
BLOCK = (900.0, 936.0)                                # the block, laid aside on the vault's floor
SEWER_TRACK = {"architect": St.WATER + 12.5, "cracker": St.WATER + 19.0}
UNDER_X = {"architect": St.GULLY_C + 4.0, "cracker": St.GULLY_C + 48.0}
B_X = {"architect": St.MH_B + 4.0, "cracker": St.MH_B + 40.0}
START_X = {"architect": LADDER_X - 26.0, "cracker": LADDER_X + 2.0}     # she steps aside off the ladder's foot
H_UNDER_LID = {"architect": St.WATER - St.GROUND - 132.0, "cracker": St.WATER - St.GROUND - 262.0}


@lru_cache(maxsize=None)
def walker(who):
    """Wading left along the sewer (figure units, drawn mirrored): from the shaft to the gully,
    a stop right under him, then on to manhole B."""
    if who == "architect":
        a0, a1, b0, b1 = T_GO_H, T_UNDER_H, T_ON_H, T_AT_B_H
    else:
        a0, a1, b0, b1 = T_GO_C, T_UNDER_C, T_ON_C, T_AT_B_C
    da = (START_X[who] - UNDER_X[who]) / FS
    db = (UNDER_X[who] - B_X[who]) / FS
    va = da / (a1 - a0 - 0.3)
    vb = db / (b1 - b0 - 0.3)
    keys = ((a0, 0.0), (a0 + 0.3, va), (a1 - 0.3, va), (a1, 0.0), (b0, 0.0), (b0 + 0.3, vb), (b1 - 0.3, vb), (b1, 0.0))
    return pd.Walker(C.fig(who), 0.0, speed=keys, t0=a0 - 1.0, t1=b1 + 2.0, walk=(380.0, 0.6, 40.0), v_walk=440.0,
                     v_run=900.0)


@lru_cache(maxsize=None)
def steps(who):
    """(points, times) of a wader's footfalls along the sewer, on its track."""
    wk = walker(who)
    a0 = T_GO_H if who == "architect" else T_GO_C
    b1 = T_AT_B_H if who == "architect" else T_AT_B_C
    pts, times = [], []
    for tt, side, fx in Bk.footfalls(lambda u: (wk.state(u), None), a0, b1 + 0.1):
        pts.append((float(START_X[who] - fx * FS), SEWER_TRACK[who]))
        times.append(float(tt))
    return tuple(pts), tuple(times)


def wading(who, t, t_land):
    st = walker(who).state(t)
    land = clamp((t - t_land) / 0.3)
    pose = pd.Pose(lean=6.0, head=-4.0, crouch=50.0 * math.sin(math.pi * land) * (1.0 - 0.5 * land))
    pose.arms = {"near": ("ang", 16.0, 22.0), "far": ("ang", 10.0, 18.0)}
    return st, pose


def her_row(t):
    """(st, pose, x, floor_y, sx) for her, from the top rung of the shaft to the lid of manhole B."""
    if t < T_SLIDE_H[0]:                                   # on the top rung, looking down the shaft
        st, pose = Bk.ladder_pose("architect", H_TOP, facing=1, rung=St.RUNG_STEP, reach=0.6)
        pose.head = -18.0
        return st, pose, LADDER_X, St.WATER, 1.0
    if t < T_SPLASH_H:                                     # the slide (a sailor's, hands on the rails)
        u = clamp((t - T_SLIDE_H[0]) / (T_SLIDE_H[1] - T_SLIDE_H[0]))
        h = H_TOP * (1.0 - u * u)
        st, pose = Bk.ladder_pose("architect", H0, facing=1, rung=St.RUNG_STEP)
        pose.head = -10.0
        return st, pose, LADDER_X, St.WATER - (h - H0), 1.0
    if t < T_GO_H:                                         # in the water, turned, looking up for him
        st = C.standing("architect", spread=18.0)
        land = clamp((t - T_SPLASH_H) / 0.3)
        pose = pd.Pose(lean=2.0, head=22.0 * k(t, T_TURN_H[1], 0.3, "inout"),
                       crouch=70.0 * math.sin(math.pi * land) * (1.0 - 0.5 * land))
        pose.arms = {"near": ("ang", 14.0, 20.0), "far": ("ang", 8.0, 16.0)}
        x = lerp(LADDER_X, START_X["architect"], k(t, T_TURN_H[1] - 0.05, 0.4, "inout"))
        return st, pose, x, St.SEWER_FEET, _turn(t, *T_TURN_H)
    if t < T_CLIMB_H[0]:
        st, pose = wading("architect", t, T_GO_H - 1.0)
        if T_UNDER_H - 0.1 <= t < T_ON_H + 0.2:            # stock still under the grating, looking up
            g = k(t, T_UNDER_H - 0.1, 0.25, "inout") * (1.0 - k(t, T_ON_H - 0.05, 0.25, "inout"))
            pose.head = lerp(pose.head, 30.0, g)
            pose.lean = lerp(pose.lean, -4.0, g)
        return st, pose, START_X["architect"], St.SEWER_FEET, -1.0
    u = ease("inout", clamp((t - T_CLIMB_H[0]) / (T_CLIMB_H[1] - T_CLIMB_H[0])))
    st, pose = Bk.ladder_pose("architect", H_UNDER_LID["architect"] * u, facing=1, rung=St.RUNG_STEP)
    pose.head = 6.0
    return st, pose, B_X["architect"] - 4.0, St.WATER, -1.0


def cracker_row(t):
    """(st, pose, x, floor_y, sx, match) for the Cracker; match: his match's head (section px) or
    None once it is out."""
    if t < T_STEP_C[0]:                                    # bent over the hole, the match low over it
        st = C.standing("cracker", spread=14.0)
        m = (St.TRAP_C - 10.0, St.FEET - 34.0)
        pose = pd.Pose(lean=24.0, head=-30.0)
        pose.arms = {"near": _ik_pt((m[0] - 2.0, m[1] + 9.0), CR_STAND, St.FEET), "far": ("ang", 10.0, 30.0)}
        return st, pose, CR_STAND, St.FEET, 1.0, m
    if t < T_SLIDE_C[0]:                                   # a step down into the hole
        u = ease("inout", clamp((t - T_STEP_C[0]) / (T_STEP_C[1] - T_STEP_C[0])))
        x = lerp(CR_STAND, LADDER_X + 2.0, u)
        fy = lerp(St.FEET, St.WATER - (H_TOP - H0), u * u)
        st = C.standing("cracker", spread=14.0)
        m = (x + 12.0, fy - 150.0 * u - 34.0 * (1.0 - u))
        pose = pd.Pose(lean=lerp(24.0, 4.0, u), head=lerp(-30.0, -12.0, u))
        pose.arms = {"near": _ik_pt((m[0] - 2.0, m[1] + 9.0), x, fy), "far": ("ang", 10.0, 30.0)}
        return st, pose, x, fy, 1.0, m
    x = LADDER_X + 2.0
    if t < T_SPLASH_C:                                     # the slide, slower, one hand up with the match
        u = ease("inout", clamp((t - T_SLIDE_C[0]) / (T_SLIDE_C[1] - T_SLIDE_C[0])))
        h = H_TOP * (1.0 - u)
        fy = St.WATER - (h - H0)
        st, pose = Bk.ladder_pose("cracker", H0, facing=1, rung=St.RUNG_STEP)
        m = (x + 10.0, fy - H0 - 150.0)
        pose.arms["near"] = _ik_pt((m[0] - 2.0, m[1] + 9.0), x, fy)
        pose.head = -14.0
        return st, pose, x, fy, 1.0, m
    if t < T_GO_C:
        st = C.standing("cracker", spread=14.0)
        land = clamp((t - T_SPLASH_C) / 0.3)
        pose = pd.Pose(lean=8.0, head=-6.0, crouch=80.0 * math.sin(math.pi * land) * (1.0 - 0.5 * land))
        sx = _turn(t, *T_TURN_C)
        m = (x + 12.0 * sx, St.SEWER_FEET - 108.0)
        pose.arms = {"near": _ik_pt((x + 12.0, m[1] + 9.0), x, St.SEWER_FEET), "far": ("ang", 8.0, 16.0)}
        return st, pose, x, St.SEWER_FEET, sx, m
    if t < T_CLIMB_C[0]:
        st, pose = wading("cracker", t, T_GO_C - 1.0)
        pose.lean += 6.0
        x0 = START_X["cracker"]
        pel = st["pelvis"][0]
        m = None
        if t < T_DOUSE + 0.15:                            # the match held up and ahead
            hp = (x0 - pel * FS - 12.0, St.SEWER_FEET - 110.0)
            pose.arms["near"] = _ik_pt((x0 + pel * FS + 10.0, hp[1] + 9.0), x0, St.SEWER_FEET)
            if t < T_DOUSE:
                m = hp
            else:                                          # shaken out
                shake = math.sin((t - T_DOUSE) * 60.0)
                pose.arms["near"] = _ik_pt((x0 + pel * FS + 10.0 + 4.0 * shake, hp[1] + 14.0), x0, St.SEWER_FEET)
        return st, pose, x0, St.SEWER_FEET, -1.0, m
    u = ease("inout", clamp((t - T_CLIMB_C[0]) / (T_CLIMB_C[1] - T_CLIMB_C[0])))
    st, pose = Bk.ladder_pose("cracker", H_UNDER_LID["cracker"] * u, facing=1, rung=St.RUNG_STEP)
    return st, pose, B_X["architect"] - 2.0, St.WATER, -1.0, None


def clip_under(c, vault=True):
    """Clip to where a figure below (or coming down from the vault) can be seen."""
    c.new_path()
    for r in St.open_rects(trap_shaft=True, above=False):
        c.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
    if vault:
        c.rectangle(St.VAULT_IN[0], St.VAULT_TOP, St.VAULT_IN[1] - St.VAULT_IN[0], St.FEET - St.VAULT_TOP + 0.5)
        c.rectangle(St.TILE[0], St.FEET - 1.0, St.TILE[1] - St.TILE[0], St.VSLAB + 2.0)
    c.clip()


def hole_and_block(c):
    """The cut block lifted out (laid aside on the vault's floor) and the hole it leaves."""
    bass.fill_polys(c, [St._r(St.TILE[0], St.FEET - 0.5, St.TILE[1], St.FEET + St.VSLAB + 1.0, 1450, 0.2)], St.TUNNEL)
    bass.fill_polys(c, [St._r(BLOCK[0], St.FEET - St.VSLAB, BLOCK[1], St.FEET, 1451, 0.3)], St.HEAVY)
    bass.fill_polys(c, [St._r(BLOCK[0], St.FEET - St.VSLAB, BLOCK[1], St.FEET - St.VSLAB + 1.6, 1452, 0.2)],
                    lerp(STEEL, INK, 0.3))


# ================================================================ 3-7: the shaft, in section
SEC_KEYS = ((T_SEC, (985.0, 1470.0), 4.2), (T_SLIDE_H[0], (985.0, 1470.0), 4.2), (T_SPLASH_H, (982.0, 1560.0), 3.6),
            (T_SPLASH_C, (975.0, 1580.0), 3.4), (T_WIDE, (890.0, 1630.0), 3.05))
SHAFT_DARK = ((1.0, 0.4), (1.16, 0.6), (1.34, 0.72))       # down here the dark keeps the shapes, just


def cam(keys, t):
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, p0, z0), (t1, p1, z1) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease("inout", (t - t0) / (t1 - t0))
            return (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)), math.exp(lerp(math.log(z0), math.log(z1), u))
    return keys[-1][1], keys[-1][2]


def draw_shaft(c, t):
    tf = T0 + t
    centre, z = cam(SEC_KEYS, t)
    hs, hp, hx, hfy, hsx = her_row(t)
    cs, cp, cx, cfy, csx, m = cracker_row(t)
    c.save()
    St.zoom_on(c, centre, z)
    St.draw_section(c, tf, moon_at=St.MOON_S, under=1.0, bell_ring=1.0, car=dict(lights=0.4), **AFTER)
    K.fill(c, INK, (-400.0, 1930.0, 1600.0, 2600.0))
    hole_and_block(c)
    c.save()
    clip_under(c)
    jh = draw_fig(c, "architect", hs, hp, hx, hfy, hsx, bg=St.TUNNEL, rim_w=1.4)
    jc = draw_fig(c, "cracker", cs, cp, cx, cfy, csx, bg=St.TUNNEL, rim_w=1.4)
    c.restore()
    St.water_edge(c)
    fl = flicker(t)
    if m is not None:
        tiny_flame(c, m, t)
        glow(c, m, 120.0 * fl, 0.12)
        K.match_light(c, m, tf, r=140.0 * fl)
        darkness(c, m, 150.0 * fl, steps=SHAFT_DARK)
    for t0, x, s in ((T_SPLASH_H, LADDER_X, 1.0), (T_SPLASH_C, LADDER_X + 2.0, 1.25)):
        St.splash(c, (x, St.WATER), t, t0, s)
    if m is not None and math.hypot(jh["head"][0] - m[0], jh["head"][1] - m[1]) > 120.0:
        K.dot(c, (jh["head"][0] + 4.0 * (1.0 if hsx > 0 else -1.0), jh["head"][1] - 1.0), 1.1, PAPER, seed=1460)
    if t >= T_GO_H:                                         # their dots begin
        for who, col in (("architect", PAPER), ("cracker", AMBER)):
            pts, times = steps(who)
            K.step_dots(c, list(pts), list(times), t, col, r=2.0, seed=1461 + len(who))
    c.restore()


# ================================================================ 7-18: the street in section, wide
WIDE_KEYS = ((T_WIDE, (540.0, 1010.0), 0.98), (13.0, (540.0, 1010.0), 0.98), (14.6, (430.0, 1390.0), 1.6),
             (16.2, (430.0, 1390.0), 1.6), (17.4, (540.0, 1010.0), 0.98))
KN_X = 590.0                              # beside the car, on the gully's grating by the bank's curb
KN_IN = 548.0                             # behind the car: in it
LENS_C = (800.0, 930.0)
LENS_R = 215.0


def knight_row(t):
    """(st, pose, x, facing, behind, sacks) for the Knight, or None while he is in the car."""
    st = C.standing("knight", spread=22.0)
    if t < T_IN[0]:
        pose = pd.Pose(lean=6.0, head=-2.0)
        wind = k(t, T_FLING - 0.12, 0.1, "out")
        fling = k(t, T_FLING, 0.12, "out")
        down = k(t, T_FLING + 0.15, 0.25, "inout")
        sacks = t < T_FLING
        a_near = lerp(10.0, -30.0, wind)                    # back, then over and in
        a_near = lerp(a_near, 120.0, fling)
        a_near = lerp(a_near, 14.0, down)
        pose.arms = {"near": ("ang", a_near, 20.0), "far": ("ang", a_near - 6.0, 24.0)}
        if sacks:
            pose.hold["near"] = Bk.hold_sack(1.0, seed=7, floor=0.0)
            pose.hold["far"] = Bk.hold_sack(1.0, seed=8, floor=0.0)
        slam = k(t, T_SLAM - 0.08, 0.08, "out") * (1.0 - k(t, T_SLAM + 0.05, 0.15, "inout"))
        if slam > 0.0:
            pose.arms["near"] = ("ang", lerp(14.0, 82.0, slam), 10.0)
            pose.lean += 10.0 * slam
        return st, pose, KN_X, -1, False, sacks
    if t < T_IN[1]:
        u = ease("inout", clamp((t - T_IN[0]) / (T_IN[1] - T_IN[0])))
        pose = pd.Pose(lean=lerp(6.0, 30.0, u), head=-10.0, crouch=120.0 * u)
        return st, pose, lerp(KN_X, KN_IN, u), -1, u > 0.35, False
    if t < T_OUT[0]:
        return None
    if t < T_OUT[1]:
        u = ease("out", clamp((t - T_OUT[0]) / (T_OUT[1] - T_OUT[0])))
        pose = pd.Pose(lean=lerp(30.0, 4.0, u), head=-6.0, crouch=120.0 * (1.0 - u))
        return st, pose, lerp(KN_IN, KN_X, u), 1, u < 0.4, False
    if t < T_BACK_IN[0]:
        a, b, c3 = T_LOOKS
        facing = 1 if t < b else -1
        pose = pd.Pose(lean=4.0, head=18.0 if b <= t < c3 else -4.0)    # up at the lit windows
        pose.arms = {"near": ("ang", 26.0, 40.0), "far": ("ang", 18.0, 34.0)}
        kick = 0.0
        if T_KICK - 0.2 <= t < T_KICK + 0.25:
            if t < T_KICK - 0.04:
                kick = -0.6 * ease("out", (t - (T_KICK - 0.2)) / 0.16)
            elif t < T_KICK:
                kick = 1.0 * ease("in3", (t - (T_KICK - 0.04)) / 0.04)
            else:
                kick = 1.0 - ease("inout", (t - T_KICK) / 0.25)
        if kick != 0.0:                                     # the near foot swings at the tyre (to his left)
            f = st["feet"]["near"]
            reach = (St.CAR_C + 44.0 - KN_X) / FS
            st["feet"]["near"] = (lerp(f[0], f[0] + 60.0, -kick) if kick < 0 else lerp(f[0], reach * 0.9, kick),
                                  -90.0 * abs(kick), 10.0 * kick)
            pose.lean -= 8.0 * kick
        return st, pose, KN_X, facing, False, False
    if t < T_BACK_IN[1]:
        u = ease("inout", clamp((t - T_BACK_IN[0]) / (T_BACK_IN[1] - T_BACK_IN[0])))
        pose = pd.Pose(lean=lerp(6.0, 30.0, u), head=-10.0, crouch=120.0 * u)
        return st, pose, lerp(KN_X, KN_IN, u), -1, u > 0.35, False
    return None


def car_state(t):
    rock = 0.0
    for t0, a in ((T_SLAM, 3.2), (T_OUT[0], 1.6), (T_KICK, 1.2), (T_SLAM2, 3.2)):
        if t >= t0:
            rock += a * math.exp(-(t - t0) / 0.18) * math.sin((t - t0) * 30.0)
    cough = 0.0
    for t0 in T_COUGHS:
        if t0 <= t < t0 + 0.7:
            cough = max(cough, (t - t0) / 0.7)
            rock += 0.8 * math.exp(-(t - t0) / 0.15) * math.sin((t - t0) * 40.0)
    if t >= T_CATCH:                                        # running: a puff on every beat, a shiver
        cough = ((t - T_CATCH) % 0.35) / 0.35
        rock += 0.5 * math.sin((t - T_CATCH) * 2.0 * math.pi * 12.0)
    lights = 0.45 if t < T_CATCH else 1.0
    return dict(lights=lights, cough=cough, rock=rock)


def sack_flight(c, t):
    """The two sacks, flung over the car's flank and in (drawn before the car: it hides them)."""
    u = (t - T_FLING) / 0.18
    if not 0.0 <= u < 1.0:
        return
    for i, dx in enumerate((-6.0, 6.0)):
        p0 = (KN_X - 22.0 + dx, St.GROUND - 70.0)
        p1 = (St.CAR_C + 6.0 + dx, St.GROUND - 46.0)
        p = (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - 40.0 * math.sin(math.pi * u))
        bass.fill_polys(c, [bass.orient(D.ellipse_pts((p[0], p[1] + 12.0), 13.0, 16.0, n=20), True),
                            bass.orient([(p[0] - 3.0, p[1] - 6.0), (p[0] + 3.0, p[1] - 6.0), (p[0] + 5.0, p[1]),
                                         (p[0] - 5.0, p[1])], True)], INK)


def lens_inside(t):
    """Her view up through the gully's grating: the lit night beyond the bars, the car's flank and
    its tyre, the RED of its tail light pulsing; his boots on the bars (10.45-11.6), one swinging
    at the tyre (11.3); the slam shakes it all (11.9); the engine catches (12.0), exhaust over the
    bars; a drip falls at her."""
    cx, cy, R = LENS_C[0], LENS_C[1], LENS_R

    def P(x, y):
        return (cx + x * R, cy + y * R)

    def inside(c):
        c.save()
        sh = 0.0
        if t >= T_SLAM2:
            sh += 0.04 * math.exp(-(t - T_SLAM2) / 0.1) * math.sin((t - T_SLAM2) * 70.0)
        if t >= T_CATCH:
            sh += 0.006 * math.sin((t - T_CATCH) * 2.0 * math.pi * 12.0)
        c.translate(sh * R, 0.6 * sh * R)
        K.fill(c, lerp(NIGHT, STEEL, 0.62), (cx - 1.5 * R, cy - 1.5 * R, cx + 1.5 * R, cy + 1.5 * R))
        beat = (t - T_WIDE) % 0.5
        bass.fill_polys(c, [D.circle_pts(P(-0.7, -0.8), 0.75 * R, n=48)], RED, 0.08 + 0.14 * math.exp(-beat / 0.15))
        jolt = 0.0
        if T_KICK <= t:
            jolt = 0.05 * math.exp(-(t - T_KICK) / 0.12) * math.sin((t - T_KICK) * 50.0)
        # the car: its flank and underside over the left of the lens, the tyre at its edge, the tail light
        bass.fill_polys(c, [bass.orient([P(-1.3, -1.3), P(-0.5, -1.3), P(-0.58, -0.4), P(-0.86, 1.3), P(-1.3, 1.3)], True)],
                        INK)
        K.dot(c, P(-0.72, -0.9), 0.13 * R, RED, seed=1510, alpha=0.65 + 0.35 * clamp(car_state(t)["lights"]))
        tyre = [P(-0.6 + jolt, -0.5), P(-0.16 + jolt, -0.5), P(-0.1 + jolt, 0.35), P(-0.18 + jolt, 0.95),
                P(-0.56 + jolt, 0.95), P(-0.64 + jolt, 0.35)]
        bass.fill_polys(c, [bass.orient(bass.cut(tyre, seed=1501, amp=0.4, seg=(10.0, 20.0)), True)],
                        lerp(INK, STEEL, 0.22))
        for i in range(9):                                  # its tread, catching the light along the edge
            y = -0.42 + 0.155 * i
            bass.line_band(c, [P(-0.2 + jolt, y), P(-0.13 + jolt, y + 0.05)], lerp(STEEL, PAPER, 0.2), width=0.035 * R,
                           seed=1502 + i, alpha=0.8)
        # his boots on the bars, soles to us
        on = k(t, T_OUT[1] - 0.05, 0.12, "out") * (1.0 - k(t, T_BACK_IN[0], 0.15, "in"))
        if on > 0.0:
            for i, bx in enumerate((0.16, 0.56)):
                kick = 0.0
                if i == 0 and T_KICK - 0.2 <= t < T_KICK + 0.25:
                    kick = math.sin(math.pi * clamp((t - (T_KICK - 0.2)) / 0.45))
                s = (0.8 + 0.2 * on) * (1.0 - 0.3 * kick)
                ox = bx - 0.5 * kick
                sole = [(0.0, -0.46), (0.12, -0.4), (0.15, -0.12), (0.11, 0.04), (0.1, 0.1), (-0.1, 0.1), (-0.11, 0.04),
                        (-0.15, -0.12), (-0.12, -0.4)]
                heel = [(-0.1, 0.18), (0.1, 0.18), (0.11, 0.44), (0.0, 0.48), (-0.11, 0.44)]
                for shape in (sole, heel):
                    pts = [P(ox + x * s, -0.02 + y * s) for x, y in shape]
                    bass.fill_polys(c, [bass.orient([(x - 4.0, y - 4.0) for x, y in pts], True)], RED)
                    bass.fill_polys(c, [bass.orient(pts, True)], INK)
        # the exhaust, once the engine runs: puffs drifting out over the bars
        if t >= T_CATCH:
            for i in range(4):
                a = ((t - T_CATCH) / 0.35 + i * 0.25) % 1.0
                K.dot(c, P(-0.3 + 0.9 * a, -0.6 + 0.25 * math.sin(i * 2.1)), (0.12 + 0.28 * a) * R,
                      lerp(STEEL, PAPER, 0.5), seed=1530 + i, alpha=0.5 * (1.0 - a))
        # the grating's bars, nearest of all
        for i, bx in enumerate((-0.42, 0.02, 0.44, 0.86)):
            bass.fill_polys(c, [bass.cut_rect(cx + (bx - 0.055) * R, cy - 1.3 * R, cx + (bx + 0.055) * R, cy + 1.3 * R,
                                              seed=1540 + i, amp=0.6)], INK)
            bass.fill_polys(c, [bass.cut_rect(cx + (bx + 0.03) * R, cy - 1.3 * R, cx + (bx + 0.055) * R, cy + 1.3 * R,
                                              seed=1545 + i, amp=0.3)], lerp(STEEL, PAPER, 0.15))
        # a drip off the bars, falling at her
        a = (t - (T_CATCH + 0.25)) / 0.3
        if 0.0 <= a < 1.0:
            K.dot(c, P(0.25, -0.05 + 0.3 * a), (0.02 + 0.09 * a) * R, PAPER, seed=1550, alpha=0.9 * (1.0 - a * a))
        c.restore()
    return inside


def draw_street(c, t):
    tf = T0 + t
    centre, z = cam(WIDE_KEYS, t)
    woke = {n for n, tw in T_WAKE.items() if t >= tw}
    lit = {("ten", n): AMBER for n in woke}

    def people(cc, where, n, rect):
        if where == "ten" and n in (2, 3, 5):
            St.neighbour(cc, n, tf, "woken" if n in woke else "asleep")

    st = dict(AFTER)
    st.update(lit=lit, beams=True, sky_lit=k(t, T_CITY, 0.6, "out"))
    c.save()
    St.zoom_on(c, centre, z)
    St.draw_section(c, tf, people=people, moon_at=St.MOON_S, under=1.0, bell_ring=1.0, car=None, **st)
    K.fill(c, INK, (-400.0, 1930.0, 1600.0, 2600.0))
    hole_and_block(c)
    # the Knight and his car
    row = knight_row(t)
    behind = row is not None and row[4]
    sack_flight(c, t)

    def kn(cc):
        stk, pose, x, facing, _, _ = row
        St.fig(cc, "knight", stk, pose, x, St.GROUND, facing=facing, lit=None)
    if behind:
        kn(c)
    St.car_rear(c, St.CAR_C, tf, **car_state(t))
    if row is not None and not behind:
        kn(c)
    # the bell's strokes rolling out over the street
    for i, tb in enumerate(BEATS):
        if tb <= t:
            K.ripple(c, St.BELL, t, tb, RED, n=2, every=0.12, life=0.9, r0=10.0, r1=170.0, width=3.4, seed=1600 + i,
                     alpha=0.8)
    # below: the two of them
    hs, hp, hx, hfy, hsx = her_row(t)
    cs, cp, cx, cfy, csx, m = cracker_row(t)
    c.save()
    clip_under(c, vault=False)
    jh = draw_fig(c, "architect", hs, hp, hx, hfy, hsx, bg=St.TUNNEL, rim_w=2.0)
    draw_fig(c, "cracker", cs, cp, cx, cfy, csx, bg=St.TUNNEL, rim_w=2.0)
    c.restore()
    St.water_edge(c)
    if m is not None:
        K.pool(c, m, 64.0, 44.0, AMBER, 0.22, steps=4)
        tiny_flame(c, m, t, s=0.2)
    if T_DOUSE <= t < T_DOUSE + 0.5:
        K.ripple(c, (cx - 10.0, cfy - 110.0), t, T_DOUSE, AMBER, n=1, life=0.4, r0=2.0, r1=14.0, width=1.2, seed=1610)
    for who, col in (("architect", PAPER), ("cracker", AMBER)):
        pts, times = steps(who)
        K.step_dots(c, list(pts), list(times), t, col, r=3.4, seed=1611 + len(who))
        for p, t0 in zip(pts, times):
            if t0 <= t < t0 + 0.6:
                St.splash(c, (p[0], St.WATER), t, t0, 0.55)
    # her look up through the grating, at him
    if T_UNDER_H <= t < T_ON_H + 0.1:
        eye = (jh["head"][0] - 4.0, jh["head"][1] - 3.0)
        K.sight_line(c, eye, (St.GULLY_C, St.GROUND + 8.0), t, T_UNDER_H + 0.05, PAPER, dur=0.3, off=T_ON_H - 0.05,
                     off_dur=0.15, r=3.0, gap=10.0, head=10.0, march=14.0, seed=1620)
    if T_LENS[0] <= t < T_LENS[1] + 0.3:
        u = k(t, T_LENS[0], 0.3, "out3") * (1.0 - k(t, T_LENS[1], 0.3, "in3"))
        K.callout(c, (St.GULLY_C, St.GROUND + 6.0), LENS_C, LENS_R, lens_inside(t), u=u, color=PAPER, ring_w=6.0,
                  dot_r=5.0, line_w=2.6, seed=1621)
    # the police lights begin to sweep the street
    sw = k(t, T_SWEEP, 1.6, "inout")
    if sw > 0.0:
        c.save()
        c.rectangle(-400.0, -400.0, 2000.0, St.GROUND + 400.0)
        c.clip()
        for p, seed in (((-160.0, 1330.0), 1), ((1240.0, 1330.0), 2)):
            K.sweep(c, p, tf, length=1600.0, spread=8.0, alpha=0.11 * sw, seed=seed, rate=230.0)
        c.restore()
    c.restore()


# ================================================================ the scene
def render(f, t, T):
    if t < T_FACE:
        K.scene_setup(f, INK)
    elif t < T_SEC:
        K.scene_setup(f, DEEP)
    else:
        K.scene_setup(f, NIGHT)
    with f.screen() as c:
        if t < T_FACE:
            draw_tile(c, t)
        elif t < T_SEC:
            draw_grin(c, t)
        elif t < T_WIDE:
            draw_shaft(c, t)
        else:
            draw_street(c, t)


def cues(T):
    out = [
        Cue(0.0, "the vault by match light: the bell far off through the walls, the match's breath", gain_db=-20, dur=2.0),
        Cue(T_LIFT[0], "her gloves on stone; the cut block grinds up out of the floor", gain_db=-10, dur=0.3),
        Cue(T_ASIDE[1] - 0.05, "the block set down on the floor: a heavy, soft stone thud", gain_db=-10, pan=-0.4),
        Cue(T_ASIDE[1], "a breath of cold air up the shaft: a low hollow wind, drips far below", gain_db=-16, dur=1.1),
        Cue(T_GLINT[0], "a glassy tick as the light crosses his spectacles", gain_db=-14, pan=0.1),
        Cue(T_GRIN, "the old man's dry chuckle, breath only, no words", gain_db=-12),
        Cue(T_SEC, "the shaft: echoing drips, water lapping far below", gain_db=-18, dur=4.0),
        Cue(T_SLIDE_H[0], "her gloves squeal down the ladder's rails, a fast slide", gain_db=-12, pan=0.2, dur=1.0),
        Cue(T_SPLASH_H, "a splash: she lands in the sewer", gain_db=-6, pan=0.2),
        Cue(T_STEP_C[0], "his shoe on the top rung: an iron clank", gain_db=-12, pan=0.2),
        Cue(T_SLIDE_C[0], "his slower slide down the rails, a squeak", gain_db=-14, pan=0.2, dur=1.1),
        Cue(T_SPLASH_C, "a heavier splash: he lands", gain_db=-6, pan=0.2),
        Cue(T_WIDE, "the street: the alarm bell rings and rings, loud and steady", gain_db=-6, pan=0.3, dur=11.0),
        Cue(T_WIDE, "Herrmann strings: a driving ostinato for the race under the street, her high D against "
                    "his low C#", gain_db=-10, dur=9.0),
        Cue(T_FLING, "the two sacks thump into the car, the gold clinks", gain_db=-8, pan=0.05),
        Cue(T_SLAM, "the car door slams", gain_db=-6, pan=0.05),
        Cue(T_OUT[0], "the car door flung open", gain_db=-8, pan=0.05),
        Cue(T_KICK, "his boot kicks the tyre: a thud, and the Knight's grunt", gain_db=-6, pan=0.05),
        Cue(T_BACK_IN[0], "his boots off the grating", gain_db=-12, pan=0.05),
        Cue(T_SLAM2, "the car door slams again, right overhead", gain_db=-5, pan=0.05),
        Cue(T_CATCH, "the engine catches: a roar right over their heads, then a hard idle", gain_db=-5, pan=0.05,
            dur=6.0),
        Cue(T_CATCH + 0.4, "a single drip falls past her face, close", gain_db=-14, pan=0.0),
        Cue(T_CITY, "the far city waking: a soft rising shimmer of strings", gain_db=-16, dur=1.5),
        Cue(T_DOUSE, "the match shaken out: a soft hiss, then dark", gain_db=-14, pan=-0.4),
        Cue(T_CLIMB_H[0], "iron rungs: her climb, hollow clanks up the shaft", gain_db=-12, pan=-0.4, dur=1.1),
        Cue(T_CLIMB_C[0], "iron rungs: his climb behind her", gain_db=-13, pan=-0.4, dur=0.9),
        Cue(T_SWEEP, "far off, the first police siren, rising", gain_db=-14, pan=0.4, dur=2.0),
    ]
    for tc in T_COUGHS:
        out.append(Cue(tc, "the starter whines and the engine coughs and dies", gain_db=-8, pan=0.05))
    for n, tw in sorted(T_WAKE.items(), key=lambda kv: kv[1]):
        out.append(Cue(tw, "a window lights: one plucked note of her theme", gain_db=-12, pan=-0.6))
    for tb in (T_OUT[1], T_LOOKS[1], T_LOOKS[2]):
        out.append(Cue(tb, "his boots on the iron grating, right overhead: a clank", gain_db=-9, pan=0.05))
    for who, gain in (("architect", -16), ("cracker", -17)):
        for p, tt in zip(*steps(who)):
            out.append(Cue(tt, "a wading step: a slosh in the sewer", gain_db=gain, pan=round(clamp((p[0] - 540.0) / 540.0, -1.0, 1.0) * 0.6, 3)))
    return sorted(out, key=lambda q: q["t"])
