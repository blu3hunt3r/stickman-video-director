"""s10 · CHECKMATE (146-166): the police box him in; every look in the street goes to him; over
his shoulder, across the street, she climbs out, looks back at him, pats her pocket and walks away.

  0-3    SIRENS. The low angle up both facades: his car lurches off the curb (0.3); headlights swing
         in dead ahead, a police car nose to nose (0.8); a second slides in behind (1.5). The light
         bars sweep RED and POLICE across the walls.
  3-5    His face in the car's side window, washed red and blue by turns; his eyes dart; his heart
         (RED rings); one nervous drag on the cigarette (4.35).
  5-10   THE WEB, on the section: from each neighbour at the lit windows a PAPER look flies to him
         in his car (5.25, 5.75, 6.25), then from the city (6.75-7.25), then the police lights'
         (8.0). Under manhole B's lid her two eyes wait; no look goes to her. 9.0: the third ring.
  10-13  THE ARREST, the bank's front: his door shoved open (10.3); out with a sack (10.5-11.0); a
         look at each police car (11.2, 11.5); the sack drops and the gold spills (11.75-11.9);
         hands up in the headlights (12.1-12.5).
  13-17  OVER HIS SHOULDER (the mirror of hers in s02): across the street manhole B's lid slides off
         (13.4); she climbs out (13.7), the Cracker after her (14.1); her look to him (14.5), his to
         her (14.9): they meet (15.2). She pats her pocket, a red glint (15.8), and turns away (16.3).
  17-20  THE PULL BACK: the whole block, every window lit, every look on his small ringed figure
         between the police cars; she and the Cracker walk off left under the lamp, into the dark.
"""
import math
from functools import lru_cache

import cairo

from engine import bass, draw as D, paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import faces as F
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import street as St
from films.double_cross_opposite.scenes import s09_plan_b as S09
from films.opposite_full import kit as OK

k = K.k
W, H = K.W, K.H
INK, PAPER, AMBER, RED, NIGHT, STEEL, DEEP, POLICE, SHUT = (K.INK, K.PAPER, K.AMBER, K.RED, K.NIGHT, K.STEEL, K.DEEP,
                                                            K.POLICE, K.SHUT)
T0 = K.film_start("s10")                  # film time of this scene's t = 0
FS = St.FIG_S

# ---------------------------------------------------------------- beats (scene time)
T_LURCH = (0.3, 0.75)                     # his car lurches off the curb ...
T_A_IN = (0.45, 0.8)                      # ... headlights swing in dead ahead: police car A, nose to nose
T_BRAKE = 0.8                             # both brake
T_B_IN = (1.15, 1.5)                      # police car B slides in behind him
T_FACE = 3.0                              # his face in the side window
T_DARTS = ((3.2, 1.0), (3.55, -1.0), (3.85, 1.0), (4.15, -0.4), (4.6, -1.0))   # (t, look): his eyes dart
T_DRAG = 4.35                             # one nervous drag on the cigarette
T_WEB = 5.0                               # the section: every look goes to him
T_LOOKS_TEN = ((5, 5.25), (3, 5.75), (2, 6.25))    # (storey, t): the neighbours at their windows
T_LOOKS_CITY = (6.75, 7.0, 7.25)          # the city's lit windows
T_LOOKS_POLICE = (8.0,)                   # the police light
T_RING = 9.0                              # THE THIRD RED RING closes round him
T_ARREST = 10.0                           # the bank's front, face on
T_DOOR = (10.3, 10.5)                     # his door shoved open
T_OUT = (10.5, 11.0)                      # he climbs out with a sack
T_LOOK_A, T_LOOK_B = 11.2, 11.5           # a look at each police car
T_DROP = (11.75, 11.9)                    # the sack drops; the gold spills
T_FACE_A = 12.0                           # he turns into the light ...
T_HANDS = (12.1, 12.5)                    # ... and puts his hands up
T_OTS = 13.0                              # over his shoulder
T_LID = (13.4, 13.8)                      # manhole B's lid slides off
T_UP_H = (13.7, 14.15)                    # she climbs out ...
T_STEP_H = (14.15, 14.4)
T_UP_C = (14.1, 14.55)                    # ... and the Cracker after her
T_STEP_C = (14.55, 14.8)
T_HER_LOOK = 14.5
T_HIS_LOOK = 14.9
T_MEET = 15.2                             # the two looks meet
T_PAT = (15.8, 16.1)                      # she pats her pocket: a red glint
T_TURN_H = (16.3, 16.6)                   # she turns away ...
T_TURN_C = (16.45, 16.75)
T_PULL = (17.0, 17.4, 19.8)               # the pull back: cut, the move starts, it lands
T_DARK = 19.0                             # past the lamp, into the dark

STROBE_HZ = 3.0                           # the light bars' halves swap this often (as K.light_bar)


def motion_blur(t, T):
    return 1


def strobe_blue(tf, seed=0.0):
    return (tf * STROBE_HZ + seed) % 1.0 < 0.5


def rim(c, draw_fn, color, off, alpha=1.0):
    S09.rim(c, draw_fn, color, off, alpha)


# ================================================================ cars seen end on (frame or section px)
CAR_BODY = ((-50.0, 0.0), (50.0, 0.0), (52.0, -10.0), (50.0, -40.0), (44.0, -48.0), (34.0, -52.0), (28.0, -78.0),
            (18.0, -88.0), (-18.0, -88.0), (-28.0, -78.0), (-34.0, -52.0), (-44.0, -48.0), (-50.0, -40.0), (-52.0, -10.0))


def bar_pos(cx, gy, s, rock=0.0):
    """Where an end-on police car's light bar sits (St.car_rear's, and police_front's)."""
    a = math.radians(rock)
    lx, ly = 0.0, -88.0
    return (cx + s * (lx * math.cos(a) - ly * math.sin(a)), gy + s * (-14.0 + lx * math.sin(a) + ly * math.cos(a)))


def bar_glow(c, p, tf, s, seed=0, alpha=1.0):
    """The light bar's lit half throws a flat halo (on top of the car)."""
    blue = strobe_blue(tf, hash01(seed, 9))
    off = -11.0 * s if blue else 11.0 * s
    col = POLICE if blue else RED
    K.dot(c, (p[0] + off, p[1] - 4.0 * s), 30.0 * s, col, seed=seed, alpha=0.22 * alpha)
    K.dot(c, (p[0] + off, p[1] - 4.0 * s), 16.0 * s, col, seed=seed + 1, alpha=0.25 * alpha)


def police_front(c, cx, tf, s=1.0, gy=0.0, glare=1.0, dip=0.0, seed=0):
    """A police car end on from the front, centred on cx, wheels on gy: the windscreen, the grille,
    two headlights glaring at us, the light bar on the roof. dip (px): the nose dips (a brake)."""
    c.save()
    c.translate(cx, gy)
    c.scale(s, s)
    for d in (-1, 1):
        bass.fill_polys(c, [St._r(d * 44.0 - 9.0, -26.0, d * 44.0 + 9.0, 0.0, 1700 + d, 0.3)], INK)
    c.save()
    c.translate(0.0, -14.0 + dip / max(s, 0.01))
    bass.fill_polys(c, [bass.orient([(x * 1.04, y * 1.03 - 1.5) for x, y in CAR_BODY], True)], STEEL)
    bass.fill_polys(c, [bass.orient(bass.cut(list(CAR_BODY), seed=1702, amp=0.3, seg=(16.0, 40.0)), True)], INK)
    bass.fill_polys(c, [bass.orient([(-24.0, -56.0), (24.0, -56.0), (17.0, -80.0), (-17.0, -80.0)], True)], St.GLASS)
    bass.fill_polys(c, [St._r(-52.0, -14.0, 52.0, -7.0, 1703, 0.3)], STEEL)                      # the bumper
    bass.fill_polys(c, [St._r(-17.0, -40.0, 17.0, -22.0, 1704, 0.2)], lerp(INK, STEEL, 0.45))    # the grille
    for i in range(5):
        x = -13.0 + 6.5 * i
        bass.fill_polys(c, [St._r(x - 0.9, -38.0, x + 0.9, -24.0, 1705 + i, 0.1)], INK)
    bass.fill_polys(c, [St._r(-50.0, -46.0, 50.0, -43.0, 1711, 0.2)], lerp(PAPER, STEEL, 0.35))  # the stripe
    for d in (-1, 1):
        K.dot(c, (d * 37.0, -33.0), 7.5, lerp(STEEL, PAPER, 0.4 + 0.6 * clamp(glare)), seed=1712 + d)
    K.light_bar(c, (0.0, -88.0), tf, s=1.15, seed=1714 + seed)
    c.restore()
    c.restore()
    if glare > 0.0:                                     # the headlights straight at us: flat halos
        for d in (-1, 1):
            p = (cx + d * 37.0 * s, gy + (-47.0 * s + dip))
            K.dot(c, p, 34.0 * s, PAPER, seed=1716 + d, alpha=0.16 * glare)
            K.dot(c, p, 19.0 * s, PAPER, seed=1718 + d, alpha=0.30 * glare)


# ================================================================ 0-3: sirens, the low angle
def _fz(v, a=1.7):
    """The facades' foreshortening up the frame (OPPOSITE's low angle)."""
    return v * (1.0 + a) / (1.0 + a * v)


def facade(bl, br, tl, tr):
    def P(u, v):
        f = _fz(v)
        x0, y0 = lerp(bl[0], br[0], u), lerp(bl[1], br[1], u)
        x1, y1 = lerp(tl[0], tr[0], u), lerp(tl[1], tr[1], u)
        return (lerp(x0, x1, f), lerp(y0, y1, f))
    return P


def quad(P, u0, v0, u1, v1):
    return bass.orient([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], True)


TEN_F = facade((-330.0, 2080.0), (330.0, 2080.0), (300.0, 236.0), (436.0, 250.0))
BANK_F = facade((736.0, 2080.0), (1440.0, 2080.0), (612.0, 820.0), (944.0, 806.0))
BANK_FACE = lerp(STEEL, NIGHT, 0.52)
LOW_MOON = (556.0, 330.0)
TEN_LIT = (1, 2, 3, 5)                    # the storeys awake (s09); the crew's (4) dark


def bust(c, q, kind=0, color=INK):
    """A watcher at a lit window, head and shoulders at the sill (q: the window's quad, any
    orientation; scaled to it). kind: 0 bald, 1 bun, 2 cap. Returns the head's centre."""
    xs = [p[0] for p in q]
    ys = [p[1] for p in q]
    cx, by = sum(xs) / len(xs), max(ys)
    hgt = by - min(ys)
    s = hgt / 300.0
    c.save()
    c.new_path()
    D.poly(c, q)
    c.clip()
    c.translate(cx, by)
    c.scale(s, s)
    body = [(-120.0, 0.0), (-112.0, -112.0), (-64.0, -160.0), (64.0, -160.0), (112.0, -112.0), (120.0, 0.0)]
    polys = [bass.orient(body, True), bass.orient(D.ellipse_pts((0.0, -218.0), 52.0, 60.0, n=36), True)]
    if kind == 1:
        polys.append(bass.orient(D.ellipse_pts((0.0, -286.0), 30.0, 22.0, n=24), True))
    elif kind == 2:
        polys.append(bass.orient([(-62.0, -246.0), (-50.0, -282.0), (40.0, -286.0), (58.0, -262.0), (96.0, -254.0),
                                  (96.0, -244.0)], True))
    bass.fill_polys(c, polys, color)
    c.restore()
    return (cx, by - 218.0 * s)


def draw_ten_low(c, t, tf):
    """The tenement's front leaning in from the left: five storeys, the crew's dark."""
    P = TEN_F
    nb = 4
    bass.fill_polys(c, [quad(P, 0.0, 0.0, 1.0, 1.0)], INK)
    bass.fill_polys(c, [bass.orient([P(0.0, 1.0), P(1.0, 1.0), (P(1.0, 1.0)[0] + 6.0, P(1.0, 1.0)[1] - 22.0),
                                     (P(0.0, 1.0)[0] - 10.0, P(0.0, 1.0)[1] - 26.0)], True)], INK)   # the parapet
    for n in range(1, 6):
        for j in range(nb):
            if n == 1:
                u0, u1, v0, v1 = j / nb + 0.025, (j + 1) / nb - 0.025, 0.035, 0.15
            else:
                u0, u1 = j / nb + 0.05, (j + 1) / nb - 0.05
                v0, v1 = (n - 1) / 5.0 + 0.055, n / 5.0 - 0.06
            q = quad(P, u0, v0, u1, v1)
            lit = n in TEN_LIT and n > 1
            bass.fill_polys(c, [q], AMBER if lit else SHUT)
            if lit and hash01(n, j, 31) < 0.5:
                bust(c, q, int(hash01(n, j, 32) * 3.0))
            if n > 1:                                       # the glazing bar
                bass.fill_polys(c, [bass.orient([P(lerp(u0, u1, 0.47), v0), P(lerp(u0, u1, 0.53), v0),
                                                 P(lerp(u0, u1, 0.53), v1), P(lerp(u0, u1, 0.47), v1)], True)], INK)
        if n < 5:                                           # the sill line
            v = n / 5.0
            bass.fill_polys(c, [quad(P, 0.0, v - 0.004, 1.0, v + 0.004)], lerp(INK, STEEL, 0.25))


def draw_bank_low(c, t, tf):
    """The bank's stone front leaning in from the right: rusticated, the hall's barred windows lit
    low, pilasters, the side door burst open and the bell over it ringing, the cornice and the
    pediment with its clock."""
    P = BANK_F
    dark = lerp(BANK_FACE, INK, 0.45)
    bass.fill_polys(c, [quad(P, 0.0, 0.0, 1.0, 1.0)], BANK_FACE)
    for i in range(1, 7):                               # the base's rustication
        v = 0.05 * i
        bass.fill_polys(c, [quad(P, 0.2, v - 0.003, 1.0, v + 0.003)], dark)
    bass.fill_polys(c, [quad(P, 0.0, 0.355, 1.0, 0.38)], lerp(BANK_FACE, INK, 0.3))    # the string course
    for u in (0.27, 0.47, 0.67, 0.87):                  # the pilasters
        bass.fill_polys(c, [quad(P, u - 0.025, 0.38, u + 0.025, 0.95)], lerp(BANK_FACE, PAPER, 0.07))
        bass.fill_polys(c, [quad(P, u + 0.018, 0.38, u + 0.025, 0.95)], dark)
    for u0 in (0.32, 0.52, 0.72):                       # the hall's barred windows, the guard's lamp low behind
        u1 = u0 + 0.1
        bass.fill_polys(c, [quad(P, u0, 0.06, u1, 0.24)], St.LOW_LAMP)
        top = [P(lerp(u0, u1, 0.5 - 0.5 * math.cos(math.pi * a / 8.0)), 0.24 + 0.035 * math.sin(math.pi * a / 8.0))
               for a in range(9)]
        bass.fill_polys(c, [bass.orient([P(u0, 0.239)] + top + [P(u1, 0.239)], True)], St.LOW_LAMP)
        for f in (0.33, 0.67):
            uu = lerp(u0, u1, f)
            bass.fill_polys(c, [quad(P, uu - 0.003, 0.06, uu + 0.003, 0.27)], lerp(STEEL, INK, 0.55))
        bass.fill_polys(c, [quad(P, u0, 0.15, u1, 0.157)], lerp(STEEL, INK, 0.55))
    for v0 in (0.45, 0.67):                             # the dark offices between the pilasters
        for u0 in (0.335, 0.535, 0.735):
            bass.fill_polys(c, [quad(P, u0, v0, u0 + 0.07, v0 + 0.14)], SHUT)
    # the side door, burst open, and the alarm bell over it, still ringing
    bass.fill_polys(c, [quad(P, 0.04, 0.0, 0.18, 0.21)], dark)
    bass.fill_polys(c, [quad(P, 0.055, 0.0, 0.165, 0.195)], DEEP)
    bp = P(0.11, 0.27)
    rock = 13.0 * math.sin(tf * 2.0 * math.pi * 9.0)
    K.bell(c, bp, 2.4, RED, seed=1730, ring=rock)
    # the cornice and the pediment, its clock
    a, b = P(0.0, 0.97), P(1.0, 0.97)
    bass.fill_polys(c, [bass.orient([(a[0] - 18.0, a[1] + 8.0), (b[0] + 16.0, b[1] + 8.0), (b[0] + 20.0, b[1] - 22.0),
                                     (a[0] - 22.0, a[1] - 22.0)], True)], lerp(BANK_FACE, INK, 0.3))
    apex = ((a[0] + b[0]) / 2.0 + 4.0, (a[1] + b[1]) / 2.0 - 124.0)
    bass.fill_polys(c, [bass.orient(bass.cut([(a[0] - 14.0, a[1] - 22.0), apex, (b[0] + 14.0, b[1] - 22.0)], seed=1731,
                                             amp=0.4, seg=(20.0, 50.0)), True)], BANK_FACE)
    bass.fill_polys(c, [bass.orient(bass.cut([(a[0] + 20.0, a[1] - 30.0), (apex[0], apex[1] + 18.0), (b[0] - 20.0, b[1] - 30.0)],
                                             seed=1734, amp=0.4, seg=(20.0, 50.0)), True)], lerp(BANK_FACE, INK, 0.18))
    cp = ((a[0] + b[0]) / 2.0 + 3.0, (a[1] + b[1]) / 2.0 - 62.0)
    K.dot(c, cp, 32.0, dark, seed=1732)
    K.clock_face(c, cp, 27.0, 12, 21, seed=1733)


def his_car_low(t):
    """(cx, gy, s, jolt) of his car on the low angle: it lurches off the curb, then brakes hard."""
    u = ease("inout", clamp((t - T_LURCH[0]) / (T_LURCH[1] - T_LURCH[0])))
    cx = lerp(700.0, 642.0, u)
    gy = lerp(2010.0, 1972.0, u)
    s = lerp(4.3, 3.95, u)
    jolt = 0.0
    if t >= T_LURCH[0]:
        jolt -= 7.0 * math.exp(-(t - T_LURCH[0]) / 0.12) * math.sin((t - T_LURCH[0]) * 30.0)
    if t >= T_BRAKE:
        jolt += 12.0 * math.exp(-(t - T_BRAKE) / 0.16) * math.sin((t - T_BRAKE) * 22.0)
    return cx, gy, s, jolt


def police_a_low(t):
    u = ease("out", clamp((t - T_A_IN[0]) / (T_A_IN[1] - T_A_IN[0])))
    cx = lerp(1340.0, 452.0, u)
    gy = lerp(1846.0, 1822.0, u)
    s = lerp(2.3, 2.75, u)
    dip = 0.0
    if t >= T_A_IN[1]:
        dip = 9.0 * math.exp(-(t - T_A_IN[1]) / 0.14) * math.sin((t - T_A_IN[1]) * 25.0)
    return cx, gy, s, dip


def police_b_low(t):
    u = ease("out", clamp((t - T_B_IN[0]) / (T_B_IN[1] - T_B_IN[0])))
    cx = lerp(-520.0, 104.0, u)
    rock = 0.0
    if t >= T_B_IN[1]:
        rock = 2.5 * math.exp(-(t - T_B_IN[1]) / 0.15) * math.sin((t - T_B_IN[1]) * 28.0)
    return cx, 2096.0, 5.4, rock


def draw_sirens(c, t):
    tf = T0 + t
    K.fill(c, NIGHT)
    K.moon(c, LOW_MOON, r=60.0)
    draw_ten_low(c, t, tf)
    draw_bank_low(c, t, tf)
    a_on = t >= T_A_IN[0]
    b_on = t >= T_B_IN[0]
    ax, ay, a_s, a_dip = police_a_low(t)
    bx, by, b_s, b_rock = police_b_low(t)
    # the light bars' beams sweeping the walls (under the cars)
    if a_on:
        K.sweep(c, bar_pos(ax, ay, a_s), tf, length=2600.0, spread=9.0, alpha=0.16 * k(t, T_A_IN[1] - 0.1, 0.3, "out"),
                seed=3, rate=210.0)
    if b_on:
        K.sweep(c, bar_pos(bx, by, b_s, b_rock), tf, length=2600.0, spread=10.0,
                alpha=0.15 * k(t, T_B_IN[1] - 0.1, 0.3, "out"), seed=5, rate=190.0)
    # police car A, dead ahead (beyond his car), facing us
    if a_on:
        police_front(c, ax, tf, s=a_s, gy=ay, glare=1.0, dip=a_dip, seed=1)
        bar_glow(c, bar_pos(ax, ay, a_s), tf, a_s, seed=1714 + 1)
    # his car, from behind: it lurches, it brakes (its tail lights flare)
    cx, gy, s, jolt = his_car_low(t)
    c.save()
    c.translate(0.0, -max(0.0, jolt))
    run = ((tf % 0.35) / 0.35) if t < T_BRAKE else 0.0
    St.car_rear(c, cx, tf, s=s, lights=1.0, cough=run, rock=0.6 * jolt / 12.0, gy=gy)
    c.restore()
    if t >= T_BRAKE:
        fl = 0.55 + 0.45 * math.exp(-(t - T_BRAKE) / 0.5)
        for d in (-1, 1):
            p = (cx + d * 43.0 * s, gy - 52.0 * s - max(0.0, jolt))
            K.dot(c, p, 20.0 * s * fl, RED, seed=1740 + d, alpha=0.20)
            K.dot(c, p, 8.0 * s, RED, seed=1742 + d, alpha=0.8)
    # police car B, close behind him, from behind
    if b_on:
        St.car_rear(c, bx, tf, s=b_s, lights=1.0, rock=b_rock, gy=by, police=True)
        bar_glow(c, bar_pos(bx, by, b_s, b_rock), tf, b_s, seed=913)


# ================================================================ 3-5: his face in the side window
WIN_POLY = ((262.0, 590.0), (1002.0, 576.0), (1014.0, 1430.0), (40.0, 1430.0))
FAR_WIN = ((270.0, 620.0), (996.0, 606.0), (1004.0, 1330.0), (80.0, 1330.0))
FACE_AT = (590.0, 1745.0)
FACE_S = 1.45


def dart_look(t):
    look = 0.0
    for t0, lk in T_DARTS:
        if t >= t0:
            look = lerp(look, lk, ease("out", clamp((t - t0) / 0.07)))
    return look


def draw_face(c, t):
    tf = T0 + t
    blue = strobe_blue(tf)
    col, other = (POLICE, RED) if blue else (RED, POLICE)
    # the night above the roof, the light bars washing it
    K.fill(c, lerp(NIGHT, col, 0.18))
    # inside the window: the car's dark inside, the far window and the night through it
    c.save()
    c.new_path()
    D.poly(c, WIN_POLY)
    c.clip()
    K.fill(c, DEEP)
    bass.fill_polys(c, [bass.orient(list(FAR_WIN), True)], lerp(NIGHT, col, 0.42))
    K.sweep(c, (1150.0, 1500.0), tf, length=1800.0, spread=10.0, alpha=0.16, seed=7, rate=200.0)
    drag = 0.0
    if T_DRAG <= t < T_DRAG + 0.6:
        drag = math.sin(math.pi * clamp((t - T_DRAG) / 0.6))
    F.knight(c, FACE_AT, FACE_S, look=dart_look(t), draw=drag, t=tf, field=DEEP, rim=col, back=other, smoke=1.0)
    # his eye, wide open: bigger than his usual hooded one
    c.save()
    F._place(c, FACE_AT, FACE_S, facing=-1)
    F._eye(c, (468.0, 282.0), 44.0, 13.0, dart_look(t), lid=1.0)
    c.restore()
    # the glass: a faint cold sheen and two streaks
    bass.fill_polys(c, [bass.orient(list(WIN_POLY), True)], STEEL, 0.05)
    for ox, w in ((520.0, 60.0), (700.0, 22.0)):
        bass.fill_polys(c, [bass.orient([(ox, 560.0), (ox + w, 560.0), (ox + w - 420.0, 1440.0), (ox - 420.0, 1440.0)],
                                        True)], PAPER, 0.045)
    c.restore()
    # the car's body round the window: the roof, the pillars, the door
    body = [(-40.0, 470.0), (1120.0, 470.0), (1120.0, 1960.0), (-40.0, 1960.0)]
    c.save()
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    c.new_path()
    D.poly(c, body)
    D.poly(c, WIN_POLY)
    c.set_source_rgb(*INK)
    c.fill()
    c.restore()
    bass.fill_polys(c, [bass.cut_rect(-40.0, 462.0, 1120.0, 476.0, seed=1750, amp=0.4)], lerp(STEEL, col, 0.35))   # the roof's edge
    bass.fill_polys(c, [bass.cut_rect(-40.0, 1426.0, 1120.0, 1444.0, seed=1751, amp=0.4)], lerp(STEEL, col, 0.45))  # the chrome
    bass.fill_polys(c, [bass.cut_rect(820.0, 1520.0, 930.0, 1536.0, seed=1752, amp=0.3)], STEEL)                   # the handle
    bass.fill_polys(c, [bass.cut_rect(1020.0, 1444.0, 1026.0, 1960.0, seed=1753, amp=0.2)], lerp(INK, STEEL, 0.3))  # the door's seam
    # his heart, thudding out through the door
    K.heartbeat(c, (700.0, 1700.0), tf, RED, bpm=144.0, r0=24.0, r1=420.0, width=10.0, life=0.95, seed=1754, alpha=0.85)


# ================================================================ 5-10: the web, on the section
WEB_KEYS = ((T_WEB, (540.0, 1010.0), 0.98), (5.6, (540.0, 1010.0), 0.98), (9.4, (520.0, 1062.0), 1.1))
A_SEC = (St.CAR_C + 50.0, St.GROUND - 12.0, 0.94)        # police car A beyond his car (x, wheels y, scale)
HIS_HEAD_SEC = (St.CAR_C - 2.0, St.GROUND - 75.0)        # his head in the car's rear window


def his_head_sec(tf):
    sway = 2.0 * math.sin(tf * 7.0) * (1.0 if strobe_blue(tf) else -1.0) * 0.5
    return (HIS_HEAD_SEC[0] + sway, HIS_HEAD_SEC[1])


def him_in_car(c, tf):
    """His head and cap in the rear window of his car (section px), from behind."""
    cx, gy = St.CAR_C, St.GROUND
    win = [(cx - 22.0, gy - 70.0), (cx + 22.0, gy - 70.0), (cx + 16.0, gy - 92.0), (cx - 16.0, gy - 92.0)]
    hx, hy = his_head_sec(tf)
    c.save()
    c.new_path()
    D.poly(c, win)
    c.clip()
    polys = [bass.orient(D.ellipse_pts((hx, hy + 3.0), 8.5, 9.5, n=24), True),
             bass.orient(D.ellipse_pts((hx, hy - 4.0), 10.5, 4.6, n=24), True),
             bass.orient([(hx - 22.0, gy - 66.0), (hx - 14.0, hy + 9.0), (hx + 14.0, hy + 9.0), (hx + 22.0, gy - 66.0)], True)]
    bass.fill_polys(c, polys, INK)
    c.restore()


@lru_cache(maxsize=1)
def city_eyes():
    """Lit windows of the far city with a view of the street (section px): two in the gap between
    the fronts, one over the bank's roof."""
    _, wins = OK._skyline()
    gap = [((x0 + x1) / 2.0, (y0 + y1) / 2.0) for x0, y0, x1, y1, h in wins
           if 360.0 < (x0 + x1) / 2.0 < 600.0 and 560.0 < (y0 + y1) / 2.0 < 1150.0]
    roof = [((x0 + x1) / 2.0, (y0 + y1) / 2.0) for x0, y0, x1, y1, h in wins
            if 700.0 < (x0 + x1) / 2.0 < 1000.0 and (y0 + y1) / 2.0 < St.BANK_ROOF - 150.0]
    gap.sort(key=lambda p: p[1])
    roof.sort(key=lambda p: -p[1])
    pts = gap[:1] + gap[-1:] + roof[:1]
    while len(pts) < 3:
        pts.append((470.0 + 60.0 * len(pts), 640.0))
    return tuple(pts)


def web_people(t, tf, heads):
    def people(cc, where, n, rect):
        if where == "ten" and n in (2, 3, 5):
            h = St.neighbour(cc, n, tf, "woken")
            if h is not None:
                heads[n] = h
    return people


def draw_web(c, t):
    tf = T0 + t
    centre, z = S09.cam(WEB_KEYS, t)
    heads = {}
    st = dict(S09.AFTER)
    st.update(lit={("ten", n): AMBER for n in TEN_LIT}, beams=True, sky_lit=1.0)
    c.save()
    St.zoom_on(c, centre, z)
    St.draw_section(c, tf, people=web_people(t, tf, heads), moon_at=St.MOON_S, under=1.0, bell_ring=1.0, car=None, **st)
    K.fill(c, INK, (-400.0, 1930.0, 1600.0, 2600.0))
    S09.hole_and_block(c)
    # the police lights sweeping the street (above the ground only)
    ax, ay, a_s = A_SEC
    abar = bar_pos(ax, ay, a_s)
    c.save()
    c.rectangle(-400.0, -400.0, 2000.0, St.GROUND + 400.0)
    c.clip()
    for p, seed in (((-160.0, 1330.0), 1), ((1240.0, 1330.0), 2), (abar, 3)):
        K.sweep(c, p, tf, length=1600.0, spread=8.0, alpha=0.11, seed=seed, rate=230.0)
    c.restore()
    # police car A beyond his car, nose to nose, glaring; then his car, him in it, the engine idling
    police_front(c, ax, tf, s=a_s, gy=ay, glare=1.0, seed=2)
    bar_glow(c, abar, tf, a_s, seed=1716)
    St.car_rear(c, St.CAR_C, tf, lights=1.0, cough=(tf % 0.35) / 0.35, rock=0.4 * math.sin(tf * 2.0 * math.pi * 12.0))
    him_in_car(c, tf)
    # under manhole B's lid: the two of them on its ladder; her eyes
    hs, hp, hx, hfy, hsx = S09.her_row(S09.T_CLIMB_H[1] + 0.5)
    cs, cp, cx, cfy, csx, _ = S09.cracker_row(S09.T_CLIMB_C[1] + 0.5)
    c.save()
    S09.clip_under(c, vault=False)
    jh = S09.draw_fig(c, "architect", hs, hp, hx, hfy, hsx, bg=St.TUNNEL, rim_w=2.0)
    S09.draw_fig(c, "cracker", cs, cp, cx, cfy, csx, bg=St.TUNNEL, rim_w=2.0)
    c.restore()
    blink = 0.15 if 7.3 <= t < 7.42 else 1.0
    e = (jh["head"][0] - 4.0, jh["head"][1] - 3.0)
    bass.fill_polys(c, [bass.orient(D.ellipse_pts(e, 4.6, 3.6 * blink, n=16), True)], PAPER)
    # the looks: the neighbours', the city's, the police lights'
    target = his_head_sec(tf)
    for i, (n, t0) in enumerate(T_LOOKS_TEN):
        p = heads.get(n)
        if p is not None:
            K.sight_line(c, (p[0] + 3.0, p[1] - 2.0), target, t, t0, PAPER, dur=0.5, r=5.0, gap=19.0, head=20.0, march=24.0,
                         seed=1760 + i)
    for i, (p, t0) in enumerate(zip(city_eyes(), T_LOOKS_CITY)):
        K.sight_line(c, p, target, t, t0, PAPER, dur=0.5, r=4.4, gap=19.0, head=18.0, march=24.0, seed=1770 + i, alpha=0.9)
    K.sight_line(c, (abar[0] + 10.0, abar[1] - 6.0), target, t, T_LOOKS_POLICE[0], POLICE, dur=0.3, r=5.0, gap=15.0, head=16.0,
                 march=20.0, seed=1780)
    # THE THIRD RED RING
    if t >= T_RING:
        K.marker_ring(c, (St.CAR_C + 4.0, St.GROUND - 50.0), 78.0, 66.0, u=k(t, T_RING, 0.42, "out"), color=RED, width=9.0,
                      seed=1790)
    c.restore()


# ================================================================ 10-13: the arrest, the bank's front
CAR_X = St.CAR_FX                                     # his car, nose left (west)
POL_A_X = CAR_X - Bk.CAR_L - 14.0                     # nose to nose, facing right
POL_B_X = CAR_X + Bk.CAR_L + 14.0                     # nose to his tail, facing left
KN_AR = CAR_X - 40.0                                  # where he stands, before his door
AR_CAM0 = Bk.Cam(-84.0, -280.0, 2.22)
AR_CAM1 = Bk.Cam(-70.0, -262.0, 2.45)
AR_CAM2 = Bk.Cam(-35.0, -228.0, 3.0)                  # hands up: the push in (the bell kept in)
SACK_LAND = (KN_AR + 26.0, 0.0)              # under his near hand, facing B
SPILL = ((-34.0, -14.0, 0.0), (-58.0, -22.0, 10.0), (-12.0, 14.0, -8.0), (12.0, 26.0, 14.0), (-80.0, -30.0, -6.0))


def ar_cam(t):
    t1 = T_HANDS[0] - 0.05
    if t < t1:
        u = ease("inout", clamp((t - T_ARREST) / (t1 - T_ARREST)))
        return Bk.Cam.toward(AR_CAM0, AR_CAM1, u, (KN_AR, -60.0))
    u = ease("inout", clamp((t - t1) / 0.85))
    return Bk.Cam.toward(AR_CAM1, AR_CAM2, u, (KN_AR, -90.0))


def knight_ar(t):
    """(st, pose, facing, sx, sack) of him at the car's door, face on (Bk set px, the road y 0);
    or None while he is still in his seat. sx: the paper turn (-1 faces left)."""
    st = C.standing("knight", spread=20.0)
    sack = t < T_DROP[0]
    if t < T_OUT[0]:
        return None
    sx = -1.0
    if t < T_OUT[1]:                                   # unfolding out of the door, sack in hand
        u = ease("out", clamp((t - T_OUT[0]) / (T_OUT[1] - T_OUT[0])))
        pose = pd.Pose(lean=lerp(34.0, 6.0, u), head=lerp(-14.0, -4.0, u), crouch=lerp(170.0, 0.0, u))
    else:
        pose = pd.Pose(lean=5.0, head=2.0)
        if t >= T_FACE_A - 0.1:                         # back round, into A's headlights
            sx = S09._turn(t, T_FACE_A - 0.1, T_FACE_A + 0.04, 1.0)
        elif t >= T_LOOK_B - 0.08:                      # round to B, behind his car
            sx = S09._turn(t, T_LOOK_B - 0.08, T_LOOK_B + 0.06, -1.0)
    pose.arms = {"near": ("ang", 12.0, 18.0), "far": ("ang", 8.0, 16.0)}
    if sack:
        pose.hold["near"] = Bk.hold_sack(1.0, seed=7, floor=0.0)
    else:
        let = k(t, T_DROP[0], 0.12, "out")
        pose.arms["near"] = ("ang", lerp(12.0, 26.0, let) - 14.0 * k(t, T_DROP[0] + 0.12, 0.2, "inout"), 18.0)
    if t >= T_HANDS[0]:
        g = ease("outback", clamp((t - T_HANDS[0]) / (T_HANDS[1] - T_HANDS[0])))
        pose.arms = {"near": ("ang", lerp(12.0, 156.0, g), lerp(18.0, 14.0, g)),
                     "far": ("ang", lerp(8.0, 206.0, g), lerp(16.0, -12.0, g))}
        pose.head = lerp(2.0, 10.0, g)
        pose.lean = lerp(5.0, -2.0, g)
    return st, pose, sx, sack


def sack_fall(t):
    """The dropped sack: (its base, falling) -- from where it hung (its foot 30 px up) to the road,
    then slumped on it."""
    if t < T_DROP[0]:
        return None
    u = clamp((t - T_DROP[0]) / (T_DROP[1] - T_DROP[0]))
    if u < 1.0:
        return (SACK_LAND[0], -30.0 * (1.0 - u * u)), True
    return SACK_LAND, False


def draw_gold_spill(c, t):
    if t < T_DROP[1]:
        return
    for i, (dx, slide, ang) in enumerate(SPILL):
        u = ease("out3", clamp((t - T_DROP[1] - 0.03 * i) / 0.4))
        p = (SACK_LAND[0] + dx * 0.4 + slide * u, 0.0)
        Bk.bar(c, p, 1.0, angle=ang * (1.0 - u), color=AMBER, edge=INK, shine=PAPER)
    tw = clamp((t - (T_DROP[1] + 0.22)) / 0.4)
    if 0.0 < tw < 1.0:
        p = (SACK_LAND[0] + SPILL[1][0] * 0.4 + SPILL[1][1], -6.0)
        K.twinkle(c, p, 18.0, PAPER, u=math.sin(math.pi * tw), rot=15.0)


def his_head_in_window(c):
    """Before he gets out: his cap and head dark in the car's front window (Bk set px)."""
    x0 = CAR_X - Bk.CAR_L / 2.0
    win = bass.orient([(x0 + 98.0, -84.0), (x0 + 116.0, -90.0), (x0 + 150.0, -90.0), (x0 + 150.0, -60.0), (x0 + 84.0, -60.0)],
                      True)
    c.save()
    c.new_path()
    D.poly(c, win)
    c.clip()
    hx = x0 + 128.0
    bass.fill_polys(c, [bass.orient(D.ellipse_pts((hx, -66.0), 13.0, 15.0, n=24), True),
                        bass.orient([(hx - 16.0, -76.0), (hx + 14.0, -84.0), (hx + 2.0, -88.0), (hx - 20.0, -84.0),
                                     (hx - 24.0, -76.0)], True)], INK)
    c.restore()


def draw_arrest(c, t):
    tf = T0 + t
    cam = ar_cam(t)
    door = ease("outback", clamp((t - T_DOOR[0]) / (T_DOOR[1] - T_DOOR[0]))) if t >= T_DOOR[0] else 0.0
    K.fill(c, NIGHT)
    police = (dict(x=POL_A_X, facing=1, headlights=1.0), dict(x=POL_B_X, facing=-1, headlights=1.0))
    St.bank_front(c, cam, tf, clock=(12, 21), bell_ring=1.0, side_door=1.0, low=1.0, guard_x=None, car=True,
                  car_x=CAR_X, car_door=min(door, 1.0), headlights=1.0, police=police, lid=1.0, road="section", moon=True)
    with cam.on(c):
        # the light bars' beams over the bank's wall, the halos on the bars
        c.save()
        c.rectangle(-1200.0, -2000.0, 3000.0, 2000.0)
        c.clip()
        for x, fc, seed in ((POL_A_X, 1, 1), (POL_B_X, -1, 2)):
            K.sweep(c, (x + 6.0 * fc, -96.0), tf, length=900.0, spread=8.0, alpha=0.10, seed=seed, rate=220.0)
        c.restore()
        for x, fc, seed in ((POL_A_X, 1, 1381 + int(POL_A_X) % 7), (POL_B_X, -1, 1381 + int(POL_B_X) % 7)):
            bar_glow(c, (x + 6.0 * fc, -92.0), tf, 1.5, seed=seed)
        if t < T_OUT[0]:
            his_head_in_window(c)
        row = knight_ar(t)
        if row is not None:
            st, pose, sx, sack = row
            # the bars' red on one side of him, A's headlights (PAPER) on the other
            edge = lerp(NIGHT, STEEL, 0.3)
            j = S09.draw_fig(c, "knight", st, pose, KN_AR, 0.0, sx, bg=edge, rim_w=3.0, light=(0.9, -0.4))
            rim(c, _knight_rim(st, pose, sx), PAPER, (-3.0, -1.0), 0.95)
            S09.draw_fig(c, "knight", st, pose, KN_AR, 0.0, sx, bg=edge, rim_w=0.0)
            # his looks: at A, at B
            eye = (j["head"][0] + 5.0 * sx, j["head"][1] - 3.0)
            K.sight_line(c, eye, (POL_A_X + 6.0, -100.0), t, T_LOOK_A, RED, dur=0.18, off=T_LOOK_B - 0.06, off_dur=0.12, r=2.6,
                         gap=9.0, head=10.0, march=12.0, seed=1800)
            K.sight_line(c, eye, (POL_B_X - 6.0, -100.0), t, T_LOOK_B, RED, dur=0.18, off=T_DROP[0], off_dur=0.12, r=2.6,
                         gap=9.0, head=10.0, march=12.0, seed=1801)
        fall = sack_fall(t)
        if fall is not None:
            p, air = fall
            if air:
                Bk.sack(c, p, 0.9, s=1.0, color=INK, rim=RED, seed=7)
            else:
                Bk.sack(c, p, 0.55, s=1.25, color=INK, rim=RED, seed=7)
                if t < T_DROP[1] + 0.4:
                    K.ripple(c, (p[0], -4.0), t, T_DROP[1], PAPER, n=2, every=0.1, life=0.4, r0=4.0, r1=34.0, width=2.0,
                             seed=1802, alpha=0.8)
        draw_gold_spill(c, t)


def _knight_rim(st, pose, sx):
    def fn(cc):
        S09.draw_fig(cc, "knight", st, pose, KN_AR, 0.0, sx, bg=INK, rim_w=0.0, eye=False)
    return fn


# ================================================================ 13-17: over his shoulder
OTS_CAM = Bk.Cam(700.0, -262.0, 1.5)
KN_NAPE = (740.0, 1664.0)                            # him, from behind, at the right of the frame
KN_S = 1.32
TF_LIT = {**{(n, j): AMBER for n in (2, 3, 5) for j in range(5)}}
HER_OUT_X = St.TF_MH_B + 28.0                        # where they stand, out of the hole (tenement front set px)
CR_OUT_X = St.TF_MH_B - 26.0
POCKET = (16.0, -238.0)                              # her coat pocket, figure units from her floor point


def open_hand(wr, d):
    """The back of a raised open hand (local units; d -1 his left, 1 his right, the head at x 0):
    the palm up off the wrist, four fingers fanned, the thumb in toward the head."""
    top = wr[1] - 104.0
    cx = wr[0] - 4.0 * d
    palm = bass.orient([(cx - 36.0, wr[1] + 10.0), (cx + 36.0, wr[1] + 10.0), (cx + 46.0, wr[1] - 40.0), (cx + 42.0, top),
                        (cx - 42.0, top), (cx - 46.0, wr[1] - 40.0)], True)
    out = [palm]
    for off, length, a in ((-30.0, 64.0, -8.0), (-10.0, 74.0, -2.0), (10.0, 68.0, 4.0), (30.0, 54.0, 10.0)):
        base = (cx + d * off, top + 10.0)                  # index (by the thumb) .. little finger
        ang = math.radians(d * a)
        tip = (base[0] + math.sin(ang) * length, base[1] - math.cos(ang) * length)
        out.append(bass.capsule_pts(base, tip, 11.0, 9.0, cap=4))
    tb = (cx - d * 40.0, wr[1] - 30.0)
    ta = math.radians(40.0)
    out.append(bass.capsule_pts(tb, (tb[0] - d * math.sin(ta) * 56.0, tb[1] - math.cos(ta) * 56.0), 13.0, 10.0, cap=4))
    return out


def knight_back_polys():
    """His head and shoulders from behind (local units: the nape at the origin, y down; s 1: the
    head about 200 high): the flat cap, the ears, the coat's collar turned up, the broad
    shoulders, his hands up by his head (the upper arms foreshortened, reaching forward), the
    backs of the hands."""
    def sym(half):
        return half + [(-x, y) for x, y in reversed(half)]

    shoulders = sym([(-60.0, 10.0), (-130.0, 26.0), (-214.0, 54.0), (-280.0, 104.0), (-306.0, 200.0), (-316.0, 420.0),
                     (-322.0, 760.0)])
    collar = [(-118.0, 40.0), (-112.0, -20.0), (-102.0, -74.0), (-50.0, -64.0), (0.0, -50.0), (50.0, -64.0),
              (102.0, -74.0), (112.0, -20.0), (118.0, 40.0)]
    head = [(0.0 + 92.0 * math.cos(math.radians(a)), -166.0 + 100.0 * math.sin(math.radians(a))) for a in range(0, 360, 10)]
    ears = [D.ellipse_pts((d * 94.0, -150.0), 15.0, 26.0, n=16) for d in (-1, 1)]
    cap = [(-122.0, -160.0), (-118.0, -204.0), (-98.0, -248.0), (-50.0, -278.0), (0.0, -284.0), (54.0, -278.0),
           (102.0, -246.0), (122.0, -202.0), (126.0, -158.0), (60.0, -150.0), (0.0, -148.0), (-60.0, -150.0)]
    arms, hands_ = [], []
    for d in (-1, 1):
        sh, el, wr = (d * 236.0, 86.0), (d * 272.0, -10.0), (d * 196.0, -296.0)
        arms.append(bass.capsule_pts(sh, el, 64.0, 54.0, cap=8))
        arms.append(bass.capsule_pts(el, wr, 54.0, 40.0, cap=8))
        hands_ += open_hand(wr, d)
    return [shoulders, collar, head, cap] + ears, arms, hands_


def knight_back(c, base=KN_NAPE, s=KN_S, t=0.0, rim_l=RED, rim_r=PAPER):
    """Draws him from behind (see knight_back_polys), rimmed by the light on each side.
    Returns {'head', 'r'} in frame px."""
    body, arms, hands_ = knight_back_polys()
    br = 1.0 + 0.008 * math.sin(2.0 * math.pi * 0.9 * K.twos(t))      # he breathes hard
    m = cairo.Matrix()
    m.translate(*base)
    m.scale(s, s * br)

    def cut(pts, seed):
        q = [m.transform_point(*p) for p in pts]
        return bass.orient(bass.scissor(q, seed=seed, sag=0.45, amp=0.25, max_len=40.0, corner=40.0), True)

    polys = [cut(p, 1820 + i) for i, p in enumerate(body + arms)]
    polys += [bass.orient(bass.scissor([m.transform_point(*q) for q in p], seed=1830 + i, sag=0.3, amp=0.2, max_len=18.0,
                                       corner=30.0), True) for i, p in enumerate(hands_)]

    def fn(cc):
        bass.fill_polys(cc, polys, INK)
    rim(c, fn, rim_r, (7.0, -3.0))
    rim(c, fn, rim_l, (-7.0, -3.0))
    bass.fill_polys(c, polys, INK)
    # the cap's seam and the strap at its back
    a, b = m.transform_point(-100.0, -168.0), m.transform_point(100.0, -168.0)
    bass.line_band(c, [a, m.transform_point(0.0, -160.0), b], lerp(INK, STEEL, 0.35), width=3.0 * s, seed=1840)
    hx, hy = m.transform_point(0.0, -166.0)
    return {"head": (hx, hy), "r": 92.0 * s}


def climb_out(who, t):
    """(st, pose, x, foot_y, sx) of a figure coming up out of manhole B (tenement front set px):
    rising with the hands on the rim, a step out, standing; or None while still below."""
    up, step = (T_UP_H, T_STEP_H) if who == "architect" else (T_UP_C, T_STEP_C)
    x_out = HER_OUT_X if who == "architect" else CR_OUT_X
    if t < up[0]:
        return None
    st = C.standing(who, spread=14.0)
    x0 = St.TF_MH_B
    if t < up[1]:                                     # up, the hands on the rim pushing down
        u = ease("out", clamp((t - up[0]) / (up[1] - up[0])))
        fy = lerp(170.0, 0.0, u)
        pose = pd.Pose(lean=4.0, head=8.0 * (1.0 - u))
        g = clamp((u - 0.6) / 0.4)                       # past the rim, they let go
        arms = {}
        for side, dx, rest in (("near", 22.0, (34.0, -300.0)), ("far", -20.0, (-14.0, -300.0))):
            rim_pt = (dx / FS, (-1.0 - fy) / FS)
            arms[side] = ("ik", (lerp(rim_pt[0], rest[0], g), lerp(rim_pt[1], rest[1], g)))
        pose.arms = arms
        return st, pose, x0, fy, 1.0
    u = ease("inout", clamp((t - step[0]) / (step[1] - step[0])))
    x = lerp(x0, x_out, u)
    st["feet"]["near"] = (st["feet"]["near"][0] + 40.0 * math.sin(math.pi * u), -60.0 * math.sin(math.pi * u), 0.0)
    pose = pd.Pose(lean=4.0, head=0.0)
    pose.arms = {"near": ("ang", 14.0, 20.0), "far": ("ang", 8.0, 16.0)}
    return st, pose, x, 0.0, 1.0


@lru_cache(maxsize=None)
def walker_off(who):
    t0 = T_TURN_H[1] if who == "architect" else T_TURN_C[1]
    v = 640.0                                          # a long, brisk walk, not a run
    return pd.Walker(C.fig(who), 0.0, speed=((t0, 0.0), (t0 + 0.3, v), (t0 + 6.0, v)), t0=t0 - 1.0, t1=t0 + 7.0,
                     walk=(440.0, 0.62, 36.0), v_walk=640.0, v_run=1100.0)


def her_row(t):
    """(st, pose, x, foot_y, sx) of her across the street (tenement front set px), or None."""
    if t < T_TURN_H[1]:
        row = climb_out("architect", t)
        if row is None or t < T_STEP_H[1]:
            return row
        st = C.standing("architect", spread=14.0)
        pose = pd.Pose(lean=2.0, head=6.0)                   # up at him, across the street
        pose.arms = {"near": ("ang", 12.0, 20.0), "far": ("ang", 8.0, 16.0)}
        if T_PAT[0] - 0.15 <= t < T_PAT[1] + 0.2:          # the pat: the near hand to her pocket, twice
            g = k(t, T_PAT[0] - 0.15, 0.15, "out") * (1.0 - k(t, T_PAT[1], 0.2, "inout"))
            tap = 10.0 * abs(math.sin(math.pi * clamp((t - T_PAT[0]) / (T_PAT[1] - T_PAT[0])) * 2.0))
            tgt = (POCKET[0] + 10.0, POCKET[1] - tap)
            rest = (30.0, -300.0)
            pose.arms["near"] = ("ik", (lerp(rest[0], tgt[0], g), lerp(rest[1], tgt[1], g)))
        sx = S09._turn(t, *T_TURN_H) if t >= T_TURN_H[0] else 1.0
        return st, pose, HER_OUT_X, 0.0, sx
    st = walker_off("architect").state(t)
    pose = pd.Pose(lean=4.0, head=-2.0)
    pose.arms = {"near": ("ang", 14.0, 20.0), "far": ("ang", 8.0, 16.0)}
    return st, pose, HER_OUT_X, 0.0, -1.0


def cracker_row(t):
    if t < T_TURN_C[1]:
        row = climb_out("cracker", t)
        if row is None or t < T_STEP_C[1]:
            return row
        st = C.standing("cracker", spread=14.0)
        look = math.sin(2.0 * math.pi * 0.9 * (t - T_STEP_C[1]))     # glancing round, nervous
        pose = pd.Pose(lean=10.0, head=10.0 * look)
        pose.arms = {"near": ("ang", 6.0, 14.0), "far": ("ang", 2.0, 10.0)}
        sx = S09._turn(t, *T_TURN_C) if t >= T_TURN_C[0] else 1.0
        return st, pose, CR_OUT_X, 0.0, sx
    st = walker_off("cracker").state(t)
    pose = pd.Pose(lean=12.0, head=-4.0)
    pose.arms = {"near": ("ang", 16.0, 26.0), "far": ("ang", 10.0, 22.0)}
    return st, pose, CR_OUT_X, 0.0, -1.0


def lamp_light(x):
    """How much the lamp's light catches a figure at x (tenement front set px): full to 60 px past
    the lamp, gone 170 px past it."""
    return 1.0 - clamp((St.TF_LAMP - x - 60.0) / 110.0) if x < St.TF_LAMP else 1.0


def draw_pair(c, t, marks):
    """Her and the Cracker across the street (set px): clipped to the road's surface while they
    come up out of the hole; their rims fade as they leave the lamp's light. marks gets their
    eyes and her pocket."""
    for who, row_fn, col in (("cracker", cracker_row, AMBER), ("architect", her_row, PAPER)):
        row = row_fn(t)
        if row is None:
            continue
        st, pose, x, fy, sx = row
        px = x + sx * st["pelvis"][0] * FS
        lit = lamp_light(px) if t >= T_TURN_H[1] else 1.0
        rim_col = lerp(INK, col, lit)
        c.save()
        if fy > 0.0:
            c.rectangle(x - 300.0, -900.0, 600.0, 902.0)
            c.clip()
        c.save()
        c.translate(x, 0.0)
        c.scale(sx if abs(sx) > 0.04 else 0.04, 1.0)
        c.translate(-x, 0.0)
        j = C.draw(c, who, st, pose, x, fy, s=FS, facing=1, bg=lerp(INK, lerp(NIGHT, STEEL, 0.3), lit), rim=rim_col,
                   rim_w=2.6, light=(0.8, -0.6), eye=lit > 0.3)
        c.restore()
        c.restore()
        j = S09._flip(j, x, sx)
        marks[who] = j
        if who == "architect":
            fx, fyy = POCKET
            marks["pocket"] = (x + sx * fx * FS, fy + fyy * FS)
    return marks


def look_from_back(mk, target, inset=0.55):
    (hx, hy), r = mk["head"], mk["r"]
    dx, dy = target[0] - hx, target[1] - hy
    d = math.hypot(dx, dy) or 1.0
    return (hx + dx / d * r * inset, hy + dy / d * r * inset)


def tf_watchers(heads, kind_seed=0):
    def at_window(c, n, j, r):
        if hash01(n, j, 41 + kind_seed) < 0.62:
            q = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
            heads[(n, j)] = bust(c, q, int(hash01(n, j, 42) * 3.0))
    return at_window


def draw_ots(c, t):
    tf = T0 + t
    blue = strobe_blue(tf)
    marks = {}
    heads = {}
    lid = ease("inout", clamp((t - T_LID[0]) / (T_LID[1] - T_LID[0])))

    def extra(cc):
        draw_pair(cc, t, marks)

    St.tenement_front(c, OTS_CAM, tf, windows=TF_LIT, at_window=tf_watchers(heads), lid=lid, lamp_on=1.0, sky=NIGHT,
                      moon=True, extra=extra, far_lit=1.0)
    # the police lights wash the tenement's front from the cars at our sides
    for p, seed in (((-260.0, 1760.0), 4), ((1340.0, 1700.0), 6)):
        K.sweep(c, p, tf, length=2600.0, spread=9.0, alpha=0.075, seed=seed, rate=200.0)
    # the lid's grind: a small ripple at the curb
    if T_LID[0] <= t < T_LID[0] + 0.6:
        K.ripple(c, OTS_CAM.to_frame((St.TF_MH_B, -2.0)), t, T_LID[0], PAPER, n=2, every=0.12, life=0.5, r0=6.0, r1=46.0,
                 width=2.4, seed=1850, alpha=0.8)
    # him, from behind; the looks land on top of him
    mk = knight_back(c, t=tf, rim_l=POLICE if blue else RED, rim_r=PAPER)
    her = marks.get("architect")
    if her is not None:
        eye_f = OTS_CAM.to_frame((her["head"][0] + 3.0, her["head"][1] - 2.0))
        his_target = (mk["head"][0] - 20.0, mk["head"][1] - 30.0)
        # her look to him; his look back to her, a little apart; they meet
        K.sight_line(c, eye_f, his_target, t, T_HER_LOOK, PAPER, dur=0.45, off=T_TURN_H[0], off_dur=0.2, r=6.0, gap=22.0,
                     head=24.0, march=26.0, seed=1851)                    # she looks away; his look follows her
        dx, dy = his_target[0] - eye_f[0], his_target[1] - eye_f[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d * 16.0, dx / d * 16.0
        start = look_from_back(mk, eye_f)
        K.sight_line(c, (start[0] + nx, start[1] + ny), (eye_f[0] + nx, eye_f[1] + ny), t, T_HIS_LOOK, RED, dur=0.3, r=6.0,
                     gap=22.0, head=24.0, march=26.0, seed=1852)
        if T_MEET <= t < T_MEET + 0.6:
            mid = ((eye_f[0] + his_target[0]) / 2.0 + nx / 2.0, (eye_f[1] + his_target[1]) / 2.0 + ny / 2.0)
            K.ripple(c, mid, t, T_MEET, PAPER, n=1, life=0.5, r0=6.0, r1=60.0, width=3.0, seed=1853, alpha=0.8)
            K.ripple(c, mid, t, T_MEET + 0.06, RED, n=1, life=0.5, r0=6.0, r1=52.0, width=3.0, seed=1854, alpha=0.8)
        # the pocket: a red glint
        tw = clamp((t - (T_PAT[0] + 0.1)) / 0.5)
        if 0.0 < tw < 1.0 and "pocket" in marks:
            pk = OTS_CAM.to_frame(marks["pocket"])
            K.dot(c, pk, 26.0 * math.sin(math.pi * tw), RED, seed=1855, alpha=0.45)
            K.twinkle(c, pk, 52.0, RED, u=math.sin(math.pi * tw), rot=10.0)


# ================================================================ 17-20: the pull back
PULL_CAM0 = Bk.Cam(590.0, -340.0, 1.02)
PULL_CAM1 = Bk.Cam(560.0, -620.0, 0.6)
NEAR_CURB = 300.0                                    # the bank's curb, this side of the road (set px)
FAR_WALK = 22.0                                      # the far sidewalk, where they walk
KN_PULL = (St.TF_MH_B + 6.0, NEAR_CURB - 30.0)       # him, in the road before his car
CARS_PULL = ((St.TF_MH_B - 252.0, 1, True), (St.TF_MH_B, 1, False), (St.TF_MH_B + 252.0, -1, True))  # (x, facing, police)


def pull_cam(t):
    u = ease("inout3", clamp((t - T_PULL[1]) / (T_PULL[2] - T_PULL[1])))
    return Bk.Cam.lerp(PULL_CAM0, PULL_CAM1, u)


@lru_cache(maxsize=1)
def flank_windows():
    """The houses either side of the tenement, every window lit: [(rect, key)] (set px)."""
    out = []
    for side, x0, x1, top in (("L", -660.0, 30.0, -5.0 * St.FH + 200.0), ("R", 1050.0, 1760.0, -5.0 * St.FH + 100.0)):
        y = top + 50.0
        row = 0
        while y + 110.0 < -40.0:
            col = 0
            x = x0 + 40.0
            while x + 70.0 < x1 - 30.0:
                out.append(((x, y, x + 70.0, y + 110.0), (side, row, col)))
                x += 132.0
                col += 1
            y += 190.0
            row += 1
    return out


def road_above(c, vx0, vx1):
    """The street seen from up the block: the far sidewalk, the road, manhole B's open hole and
    its lid aside, the near curb and sidewalk."""
    Bk.rect(c, (vx0 - 40.0, 0.0, vx1 + 40.0, 3000.0), lerp(NIGHT, INK, 0.30), amp=0.0)             # the near sidewalk
    Bk.rect(c, (vx0 - 40.0, 0.0, vx1 + 40.0, NEAR_CURB), lerp(NIGHT, INK, 0.55), amp=0.0)         # the road
    Bk.rect(c, (vx0 - 40.0, 0.0, vx1 + 40.0, 40.0), lerp(NIGHT, INK, 0.38), amp=0.0)              # the far sidewalk
    Bk.band(c, (vx0 - 40.0, 40.0), (vx1 + 40.0, 40.0), 5.0, lerp(NIGHT, STEEL, 0.3), seed=1860)
    Bk.band(c, (vx0 - 40.0, NEAR_CURB), (vx1 + 40.0, NEAR_CURB), 6.0, lerp(NIGHT, STEEL, 0.3), seed=1861)
    Bk.ellipse(c, (St.TF_MH_B, 74.0), 34.0, 11.0, INK, n=40)                                      # the open hole
    Bk.ellipse(c, (St.TF_MH_B - 84.0, 76.0), 36.0, 12.0, lerp(STEEL, INK, 0.30), n=40)             # its lid, aside
    Bk.ellipse(c, (St.TF_MH_B - 84.0, 76.0), 30.0, 9.0, lerp(STEEL, INK, 0.45), n=40)
    K.pool(c, (St.TF_LAMP + 20.0, 34.0), 240.0, 60.0, AMBER, 0.20)


def knight_back_small(c, foot, s, tf, rim_l):
    """Him from behind, small and whole, hands up (set px): coat, legs, cap, arms."""
    body, arms, hands_ = knight_back_polys()
    legs = [[(-150.0, 700.0), (-40.0, 700.0), (-46.0, 1080.0), (-140.0, 1080.0)],
            [(40.0, 700.0), (150.0, 700.0), (140.0, 1080.0), (46.0, 1080.0)]]
    coat = [[(-322.0, 300.0), (322.0, 300.0), (340.0, 820.0), (-340.0, 820.0)]]
    m = cairo.Matrix()
    m.translate(foot[0], foot[1])
    m.scale(s, s)
    m.translate(0.0, -1100.0)
    polys = [bass.orient([m.transform_point(*p) for p in pts], True) for pts in body + arms + hands_ + legs + coat]

    def fn(cc):
        bass.fill_polys(cc, polys, INK)
    rim(c, fn, PAPER, (2.2, -1.0))
    rim(c, fn, rim_l, (-2.2, -1.0))
    fn(c)
    return m.transform_point(0.0, -166.0)


def draw_pull(c, t):
    tf = T0 + t
    blue = strobe_blue(tf)
    cam = pull_cam(t)
    marks = {}
    heads = {}
    vx0, vy0, vx1, vy1 = cam.view(80.0)

    def extra(cc):
        road_above(cc, vx0, vx1)
        draw_pair(cc, t, marks)

    St.tenement_front(c, cam, tf, windows=TF_LIT, at_window=tf_watchers(heads), lid=1.0, lamp_on=1.0,
                      sky=lerp(NIGHT, INK, 0.45), moon=True, extra=extra, far_lit=1.0)
    with cam.on(c):
        # the houses either side, every window lit, a watcher in many
        for r, key in flank_windows():
            Bk.rect(c, r, AMBER, seed=1870 + key[1] * 11 + key[2], amp=0.4)
            if hash01(key[1], key[2], 43 if key[0] == "L" else 44) < 0.5:
                q = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
                heads[key] = bust(c, q, int(hash01(key[1], key[2], 45) * 3.0))
        # the police light washing the fronts
        c.save()
        c.rectangle(-3000.0, -4000.0, 7000.0, 4000.0 + NEAR_CURB)
        c.clip()
        for x, fc, police in CARS_PULL:
            if police:
                K.sweep(c, (x + 6.0 * fc, NEAR_CURB - 96.0), tf, length=2600.0, spread=8.0, alpha=0.08, seed=int(x) % 5, rate=210.0)
        c.restore()
        # him, in the road before his car, hands up; the cars at the near curb
        head = knight_back_small(c, KN_PULL, 0.1, tf, POLICE if blue else RED)
        for x, fc, police in CARS_PULL:
            St.car_side(c, tf, x, facing=fc, headlights=1.0 if police else 0.6, police=police, gy=NEAR_CURB)
            if police:
                bar_glow(c, (x + 6.0 * fc, NEAR_CURB - 92.0), tf, 1.5, seed=1381 + int(x) % 7)
        # every look in the street on him
        target = (head[0], head[1] + 4.0)
        order = sorted(heads.items(), key=lambda kv: math.hypot(kv[1][0] - target[0], kv[1][1] - target[1]))
        for i, (key, p) in enumerate(order):
            K.sight_line(c, p, target, t, T_PULL[0] + (0.0 if isinstance(key[0], int) else 0.5 + 0.05 * i), PAPER,
                         dur=0.45 if isinstance(key[0], int) else 0.5, r=7.0, gap=26.0, head=24.0, march=28.0,
                         seed=1880 + i, alpha=0.9)
        for i, (x, fc, police) in enumerate(CARS_PULL):
            if police:
                K.sight_line(c, (x + 6.0 * fc, NEAR_CURB - 104.0), target, t, T_PULL[0] + 0.25 * i, POLICE, dur=0.01,
                             r=7.0, gap=26.0, head=24.0, march=30.0, seed=1890 + i)
        # the third ring, round him
        K.marker_ring(c, (target[0] + 2.0, target[1] + 52.0), 66.0, 104.0, u=1.0, color=RED, width=12.0, seed=1790)


# ================================================================ the scene
def render(f, t, T):
    if t < T_FACE:
        K.scene_setup(f, NIGHT)
    elif t < T_WEB:
        K.scene_setup(f, INK)
    else:
        K.scene_setup(f, NIGHT)
    with f.screen() as c:
        if t < T_FACE:
            draw_sirens(c, t)
        elif t < T_WEB:
            draw_face(c, t)
        elif t < T_ARREST:
            draw_web(c, t)
        elif t < T_OTS:
            draw_arrest(c, t)
        elif t < T_PULL[0]:
            draw_ots(c, t)
        else:
            draw_pull(c, t)


def cues(T):
    out = [
        Cue(0.0, "sirens close by and rising: two police cars, their wails braiding", gain_db=-6, dur=5.0),
        Cue(0.0, "under it all the alarm bell keeps ringing, further off now", gain_db=-16, pan=0.3, dur=10.0),
        Cue(T_LURCH[0], "his engine revs hard; tyres scrub off the curb", gain_db=-6, pan=0.1),
        Cue(T_BRAKE - 0.05, "brakes shriek, two cars at once; a siren whoop dead ahead", gain_db=-4),
        Cue(T_B_IN[0], "a second car slides in close behind: tyres on wet stone, a short whoop", gain_db=-5, pan=-0.5),
        Cue(T_FACE, "inside the car: the sirens muffled through the glass", gain_db=-12, dur=2.0),
        Cue(T_FACE, "his heartbeat, fast and heavy", gain_db=-6, dur=2.0),
        Cue(T_DRAG, "a sharp drag on the cigarette: the paper crackles", gain_db=-12, pan=-0.2),
        Cue(T_WEB, "the street: sirens steady, the bell, the engine idling", gain_db=-12, dur=5.0),
        Cue(T_LOOKS_POLICE[0], "the police lights' looks: a low string swell", gain_db=-10, dur=1.0),
        Cue(T_RING, "the red ring: the marker's squeak, and a stab", gain_db=-4),
        Cue(T_ARREST, "close by the cars: the engines idling, the sirens wound down to a wail", gain_db=-12, dur=3.0),
        Cue(T_DOOR[0], "his car door shoved open", gain_db=-6, pan=-0.1),
        Cue(T_OUT[0] + 0.1, "his boots on the road; the sack's gold clinks", gain_db=-10, pan=-0.1),
        Cue(T_LOOK_A, "a quick low string note", gain_db=-12, pan=-0.4),
        Cue(T_LOOK_B, "the same low note, a step lower", gain_db=-12, pan=0.4),
        Cue(T_DROP[0], "the Knight's grunt", gain_db=-8, pan=-0.1),
        Cue(T_DROP[1], "the sack thumps down on the road; the gold spills out, clinking", gain_db=-5, pan=-0.1),
        Cue(T_HANDS[0], "a held low string note: his C#", gain_db=-8, dur=0.9),
        Cue(T_OTS, "over his shoulder: the sirens further off, the street hushed", gain_db=-14, dur=4.0),
        Cue(T_LID[0], "across the street a manhole lid grinds and slides off", gain_db=-10, pan=-0.3),
        Cue(T_UP_H[0], "her gloves on iron; she climbs out", gain_db=-14, pan=-0.3),
        Cue(T_UP_C[0], "his shoes on the rungs, a wheeze: the old man climbs out after her", gain_db=-15, pan=-0.3),
        Cue(T_HER_LOOK, "her look: a high held D", gain_db=-8, dur=1.5),
        Cue(T_HIS_LOOK, "his look back: a low C# under it", gain_db=-8, dur=1.1),
        Cue(T_MEET, "the looks meet: the two notes, a semitone apart, struck together like a chime", gain_db=-6),
        Cue(T_PAT[0], "her glove pats her coat pocket twice, softly", gain_db=-14, pan=-0.3),
        Cue(T_TURN_H[0], "her heels turn on the stone", gain_db=-14, pan=-0.3),
        Cue(T_PULL[0], "the theme upright, resolving into D major as the camera pulls back", gain_db=-6, dur=3.0),
    ]
    # her footsteps and the Cracker's walking away, quieter and further left
    for who, gain in (("architect", -15), ("cracker", -16)):
        wk = walker_off(who)
        t0 = T_TURN_H[1] if who == "architect" else T_TURN_C[1]
        x0 = HER_OUT_X if who == "architect" else CR_OUT_X
        for tt, side, fx in Bk.footfalls(lambda u: (wk.state(u), None), t0, 19.95):
            x = x0 - fx * FS
            fade = lamp_light(x)
            out.append(Cue(float(tt), "a heel on the stone, walking away", gain_db=round(gain - 6.0 * (1.0 - fade), 1),
                           pan=round(clamp((x - 540.0) / 540.0, -1.0, 1.0) * 0.6, 3)))
    for t0 in (T_LOOKS_TEN[0][1], T_LOOKS_TEN[1][1], T_LOOKS_TEN[2][1]) + T_LOOKS_CITY:
        out.append(Cue(t0, "a look flies: one plucked note of her theme", gain_db=-12, pan=-0.5))
    return sorted(out, key=lambda q: q["t"])
