"""s08 · DOOR (90-104): her door from inside; his shadow, his feet, the handle twice, the
chain; the keyhole; his eye; his view through the keyhole: an empty room.

  0.00  HER DOOR from inside her dark room: the Bass door shot, re-timed and re-lit for the
        night (a dark teal wall; the moon through her open window lies on the floor at our feet,
        the curtain's shadow blowing in it). The landing light lies under the door.
  0.80  His steps, heard not seen (a paper ripple each): his shadow takes the light a step at a
        time (0.8, 1.6, 2.4).
  3.20  His feet, cut into the light under the door. He stands there.
  4.00  The handle is tried: it turns down (a red arrow shows the turn), the door jolts open a
        crack and her chain snaps taut across the gap: through it, the landing light and a slice
        of him. It falls back shut.
  5.00  Again, harder: the door slams against the chain, and again. Shut.
  6.00  THE KEYHOLE (the Bass key shot, re-timed): the frame pushes into it; the landing light
        fills it; his face comes to it (6.95) and the light goes out; his eye opens (7.35), red
        iris; it searches the dark; the pupil opens wide for the dark (7.9) and in it, small,
        is what he sees: a keyhole of teal light.
  8.45  The frame dives into his pupil, and lands exactly on
  9.00  HIS VIEW THROUGH THE KEYHOLE: a keyhole of light in the black. Her dark room, from
        her door at keyhole height: A's window view (rooms.draw_window_view, the window, sashes,
        casing, rod and street of s02 / s06 / s10) pulled back across the room, her wall re-lit
        to read in the keyhole. The window wide open (the lower sash up), the curtain billowing
        in on the teal light, her lamp's pull cord swinging, her fire escape's railing outside;
        across the street his own window, lit, one floor up. On her floor the moonlight, the
        curtain's shadow blowing in it, and her mug where it broke in s04. Nobody there. His
        eye searches (the view drifts, near things more than far ones). 11.5: a gust; the
        curtain blows in at him.
 12.50  Back on his eye at the keyhole, the empty room small in his pupil: it narrows (12.75).
"""
import math

import cairo
import numpy as np

from engine import bass
from engine.core import clamp, lerp
from engine.palette import RED
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import gaze as G
from films.opposite_full import kit as K
from films.opposite_full import rooms as R

INK, PAPER, AMBER = K.INK, K.PAPER, K.AMBER
NIGHT, STEEL, DEEP, SHUT = K.NIGHT, K.STEEL, K.DEEP, K.SHUT
W, H = K.W, K.H
k = K.k
twos = K.twos

# ----------------------------------------------------------------------------- beats (scene s)
T_STEPS = (0.8, 1.6, 2.4)  # his steps on the landing: his shadow takes the light a step at a time
T_FEET = 3.2               # his feet at her door
T_KNOB = (4.0, 5.0)        # the handle tried twice: the door jolts open on the chain (on twos)
T_KEY = 6.0                # the push into the keyhole (0.6 s)
T_FACE = 6.95              # his face comes to the keyhole: the light in it goes out
T_OPEN = 7.35              # his eye opens
T_WIDEN = 7.9              # the pupil opens wide for the dark: what he sees is in it
T_DIVE = 8.45              # into his pupil ...
T_POV = 9.0                # ... his view through the keyhole
T_GUST = 11.5              # a gust: the curtain blows in at him
T_BACK = 12.5              # back on his eye
T_NARROW = 12.75           # it narrows

# ============================================================================ 1. her door
DOOR = B.DOOR                                  # (250, 262, 830, 1300): the Bass door, face on
BAR_Y = B.BAR_Y
HINGE, LATCH = DOOR[0], DOOR[2]
LEAF_W = LATCH - HINGE
WALL_C = lerp(DEEP, INK, 0.55)
FRAME_C = lerp(DEEP, STEEL, 0.1)
LEAF_C = lerp(DEEP, STEEL, 0.27)
PANEL_C = lerp(DEEP, STEEL, 0.18)
FLOOR_C = lerp(DEEP, INK, 0.6)
METAL = lerp(B.DIM, STEEL, 0.45)               # the handle and the chain's plates
LINK_C = lerp(STEEL, PAPER, 0.45)              # the chain's links, catching the moon

CHAIN_Y = 700.0
CHAIN_A = (846.0, CHAIN_Y)                     # its anchor, on the jamb
SLIDE_X = 782.0                                # its slide, in the track on the leaf (leaf px)
TRACK = (676.0, 806.0)
CHAIN_L = 136.0                                # its length (px)
G_MAX = LEAF_W * (1.0 - (CHAIN_A[0] - CHAIN_L - HINGE) / (SLIDE_X - HINGE))     # the gap it allows
SNAPS = (T_KNOB[0] + 2 / 12.0, T_KNOB[1] + 2 / 12.0, T_KNOB[1] + 5 / 12.0, T_KNOB[1] + 7 / 12.0)


def door_x(x, g):
    """Leaf px -> frame px with the leaf turned open by a gap of g px at the latch."""
    return HINGE + (x - HINGE) * (LEAF_W - g) / LEAF_W


def door_gap(t):
    """The crack at the latch (px), on twos: a jolt out to the chain, held, back shut; the
    second time it is slammed against the chain twice more."""
    tt = twos(t)
    t0, t1 = T_KNOB
    g = G_MAX * (k(tt, t0 + 1 / 12.0, 0.08, "out3") - k(tt, t0 + 0.5, 0.12, "in3"))
    a = k(tt, t1 + 1 / 12.0, 0.08, "out3") - k(tt, t1 + 0.75, 0.12, "in3")
    back = 0.0
    for tb in (t1 + 3 / 12.0, t1 + 5 / 12.0):           # pulled back a little, slammed again
        back = max(back, k(tt, tb, 0.04) - k(tt, tb + 1 / 12.0, 0.04))
    return max(g, G_MAX * a * (1.0 - 0.5 * back))


def handle_turn(t):
    """The lever's angle (deg; down is negative), on twos, with his hand's tremble."""
    tt = twos(t)
    turn = 0.0
    for t0, hold in ((T_KNOB[0], 0.55), (T_KNOB[1], 0.8)):
        turn += -38.0 * (k(tt, t0, 0.1, "out3") - k(tt, t0 + hold, 0.1, "in3"))
    turn += 2.5 * math.sin(tt * 70.0) * (k(tt, T_KNOB[0], 0.05) - k(tt, T_KNOB[1] + 0.9, 0.05))
    return turn


def draw_light(c, x0, x1, dark=0.0):
    """B.draw_light on her floor: the bar of landing light under the door between x0 and x1
    and its spill, darkened by `dark`."""
    bass.fill_polys(c, [bass.cut_rect(x0, BAR_Y, x1, BAR_Y + 26.0, seed=102, amp=0.8)], lerp(AMBER, INK, dark))
    d0 = 0.0
    for tone, d1 in B.SPILL:
        bass.fill_polys(c, [B._floor_band(x0, x1, d0, d1)], lerp(lerp(FLOOR_C, AMBER, tone), FLOOR_C, dark))
        d0 = d1


def wind(t):
    """(wind 0..1, gust 0..1) at her open window."""
    gust = k(t, T_GUST, 0.22, "out3") - k(t, T_GUST + 0.55, 0.75, "inout")
    return 0.32 + 0.09 * math.sin(t * 1.7) + 0.1 * math.sin(t * 0.63 + 1.0) + 0.6 * gust, gust


def moon_floor(c, t):
    """The moon through her open window (behind us) lies on the floor at our feet: one flat
    patch of cold light, the sash rails' shadow across it and the curtain's shadow blowing in
    it from the left (on twos)."""
    tt = twos(t)
    w, _ = wind(tt)
    far, near = 1655.0, 1960.0
    patch = [(150.0, far), (610.0, far - 40.0), (700.0, near), (-60.0, near)]
    holes = []
    # the rails: a band across the patch
    holes.append(bass.orient([(40.0, 1768.0), (660.0, 1742.0), (668.0, 1772.0), (32.0, 1800.0)], True))
    # the curtain (at the right of her window as she faces it: on our left, our back to it):
    # its shadow comes in from the left, its edge wavering with the wind
    edge = []
    n = 14
    for i in range(n + 1):
        v = i / n
        y = lerp(far - 50.0, near + 10.0, v)
        x = lerp(160.0, -20.0, v) + w * (150.0 + 90.0 * v) + 18.0 * math.sin(tt * 6.0 - v * 7.0) * w
        edge.append((x, y))
    holes.append(bass.orient(edge + [(-600.0, near + 10.0), (-600.0, far - 50.0)], True))
    c.save()
    for hp in holes:                                 # (each hole its own clip: where they overlap stays dark)
        c.new_path()
        c.rectangle(-100.0, -100.0, W + 200.0, H + 200.0)
        bass.draw.poly(c, hp)
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.clip()
    c.set_fill_rule(cairo.FILL_RULE_WINDING)
    bass.fill_polys(c, [bass.orient(patch, True)], STEEL, 0.2)
    c.restore()


def chain_links(g, t, n=9):
    """[(centre, angle)] of her chain's links, from its slide on the leaf to its anchor on the
    jamb: slack it hangs in a loop; at the full gap it is a straight line, quivering on each
    snap (on twos)."""
    s = (door_x(SLIDE_X, g), CHAIN_Y)
    a = CHAIN_A
    span = a[0] - s[0]
    d = math.sqrt(max(0.0, 3.0 * span * (CHAIN_L - span) / 8.0))
    tt = twos(t)
    q = 0.0
    for t0 in SNAPS:
        if tt >= t0 - 1e-6:
            q = max(q, math.exp(-(tt - t0) * 9.0))
    pts = []
    m = 48
    for i in range(m + 1):
        u = i / m
        wob = q * 5.0 * math.sin(u * math.pi) * math.sin(tt * 97.0 + u * 3.0)
        pts.append((lerp(s[0], a[0], u), CHAIN_Y + 4.0 * d * u * (1.0 - u) + wob))
    acc = [0.0]
    for p0, p1 in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.dist(p0, p1))
    out = []
    j = 0
    for i in range(n):
        target = acc[-1] * (i + 0.5) / n
        while j < len(acc) - 2 and acc[j + 1] < target:
            j += 1
        f = (target - acc[j]) / max(acc[j + 1] - acc[j], 1e-6)
        p = (lerp(pts[j][0], pts[j + 1][0], f), lerp(pts[j][1], pts[j + 1][1], f))
        ang = math.atan2(pts[j + 1][1] - pts[j][1], pts[j + 1][0] - pts[j][0])
        out.append((p, ang))
    return out


def link_polys(p, ang, ring):
    """One link: a ring seen flat (an oval with a hole) or a link seen edge on (a bar)."""
    ca, sa = math.cos(ang), math.sin(ang)

    def tr(x, y):
        return (p[0] + x * ca - y * sa, p[1] + x * sa + y * ca)
    if ring:
        outer = [tr(13.0 * math.cos(a), 8.0 * math.sin(a)) for a in [i * math.pi / 12.0 for i in range(24)]]
        inner = [tr(7.4 * math.cos(a), 3.1 * math.sin(a)) for a in [i * math.pi / 12.0 for i in range(24)]]
        return [bass.orient(outer, True), bass.orient(inner, False)]
    return [bass.orient([tr(-11.0, -3.2), tr(11.0, -3.2), tr(13.0, 0.0), tr(11.0, 3.2), tr(-11.0, 3.2),
                         tr(-13.0, 0.0)], True)]


def draw_chain(c, g, t):
    """The chain and its plates; over the lit gap its links are black against the light."""
    # the anchor plate on the jamb
    bass.fill_polys(c, [bass.cut_rect(CHAIN_A[0] - 8.0, CHAIN_Y - 22.0, CHAIN_A[0] + 8.0, CHAIN_Y + 22.0, seed=120,
                                      amp=0.2)], METAL)
    links = chain_links(g, t)
    polys = []
    for i, (p, ang) in enumerate(links):
        polys += link_polys(p, ang, i % 2 == 0)
    bass.fill_polys(c, polys, LINK_C)
    if g > 0.5:
        # where the landing light is behind them (past his shoulder), they are black on it
        c.save()
        c.new_path()
        c.rectangle(LATCH - 0.3 * g, DOOR[1], 0.3 * g, BAR_Y - DOOR[1])
        c.clip()
        bass.fill_polys(c, polys, INK)
        c.restore()
    K.dot(c, CHAIN_A, 6.5, METAL, seed=121)


def handle_arrow(c, t, pivot):
    """A red arc arrow round the handle's pivot while it is turned down (his hand on it)."""
    tt = twos(t)
    for i, (t0, hold) in enumerate(((T_KNOB[0], 0.55), (T_KNOB[1], 0.8))):
        if not t0 <= tt < t0 + hold:
            continue
        u = k(t, t0, 0.14, "out3")
        c.save()
        c.translate(*pivot)
        c.scale(1.0, -1.0)                 # (bass.loop_pts sweeps clockwise; the lever goes down
        wd = 15.0 if i == 0 else 19.0      #  anticlockwise)
        pts = bass.loop_pts((0.0, 0.0), 232.0, width=wd, u=u, start=172.0, sweep=44.0, head=2.2, seed=130 + i)
        if pts:
            bass.fill_polys(c, [pts], RED)
        c.restore()


def draw_door(c, t, gap=None):
    """Her door from inside her dark room at scene time t (frame px)."""
    g = door_gap(t) if gap is None else gap
    K.fill(c, WALL_C)
    bass.fill_polys(c, [bass.cut_rect(-40.0, BAR_Y + 26.0, W + 40.0, H + 40.0, seed=99, amp=1.0)], FLOOR_C)
    moon_floor(c, t)
    # the frame, and the doorway behind the leaf: the landing light through the crack
    bass.fill_polys(c, [bass.cut_rect(DOOR[0] - 26.0, DOOR[1] - 26.0, DOOR[2] + 26.0, BAR_Y, seed=100, amp=1.2)],
                    FRAME_C)
    if g > 0.5:
        x0 = LATCH - g
        bass.fill_polys(c, [bass.orient([(x0, DOOR[1]), (LATCH, DOOR[1]), (LATCH, BAR_Y), (x0, BAR_Y)], True)], AMBER)
        # a slice of him close behind it: his dark coat, the light past his shoulder
        bass.fill_polys(c, [bass.orient([(x0 - 2.0, 356.0), (x0 + 0.5 * g, 341.0), (LATCH - 0.3 * g, 392.0),
                                         (LATCH - 0.3 * g, BAR_Y), (x0 - 2.0, BAR_Y)], True)], INK)
        # the crack's light across her floor
        bass.fill_polys(c, [bass.orient([(LATCH - 0.3 * g, BAR_Y + 26.0), (LATCH, BAR_Y + 26.0),
                                         (LATCH + 360.0, H + 20.0), (LATCH + 70.0, H + 20.0)], True)], AMBER, 0.2)
    # the leaf, turned by the gap
    c.save()
    c.translate(HINGE, 0.0)
    c.scale((LEAF_W - g) / LEAF_W, 1.0)
    c.translate(-HINGE, 0.0)
    bass.fill_polys(c, [bass.cut_rect(*DOOR, seed=101, amp=1.2)], LEAF_C)
    for j, (y0, y1) in enumerate(((320.0, 760.0), (880.0, 1240.0))):
        bass.fill_polys(c, [bass.cut_rect(DOOR[0] + 56.0, y0, DOOR[2] - 56.0, y1, seed=106 + j, amp=1.0)], PANEL_C)
    # the chain's track on the leaf
    bass.fill_polys(c, [bass.cut_rect(TRACK[0], CHAIN_Y - 12.0, TRACK[1], CHAIN_Y + 12.0, seed=122, amp=0.2)], METAL)
    bass.fill_polys(c, [bass.cut_rect(TRACK[0] + 10.0, CHAIN_Y - 3.0, TRACK[1] - 8.0, CHAIN_Y + 3.0, seed=123,
                                      amp=0.1)], INK)
    # the handle (finely cut: the push into the keyhole passes 15x over it) and the keyhole
    turn = handle_turn(t)
    bass.fill_polys(c, [bass.ring_pts(B.KNOB, 44.0, seed=104, n=96, amp=0.1)], METAL)
    c.save()
    c.translate(*B.KNOB)
    c.rotate(math.radians(turn))
    bass.fill_polys(c, [bass.capsule_pts((0.0, 0.0), (-190.0, 0.0), 22.0, 19.0, 12)], METAL)
    c.restore()
    bass.fill_polys(c, list(B.keyhole_pts(B.KEYHOLE)), AMBER)
    pivot = c.user_to_device(*B.KNOB)
    c.restore()
    draw_chain(c, g, t)
    # the landing light under the door; his shadow takes it a step at a time, then his feet
    draw_light(c, DOOR[0], DOOR[2])
    n = sum(k(t, ts, 0.08, "out") for ts in T_STEPS) + k(t, T_FEET - 0.08, 0.16, "out3")
    lead = None
    if n > 0.0:
        i = min(int(n), 3)
        f = n - i
        lead = lerp(B.SHADOW_LEAD[i], B.SHADOW_LEAD[min(i + 1, 4)], f)
        if lead < DOOR[2]:
            draw_light(c, lead, DOOR[2], lerp(B.SHADOW_TONE[i], B.SHADOW_TONE[min(i + 1, 4)], f))
    fu = k(t, T_FEET - 0.08, 0.16, "out3")
    if fu > 0:
        for j, x in enumerate(B.FEET_X):
            xx = lerp(1200.0 + 190.0 * j, x, fu)
            if xx < DOOR[2]:
                x1 = min(xx + 140.0, DOOR[2])
                bass.fill_polys(c, [bass.cut_rect(xx, BAR_Y - 6.0, x1, BAR_Y + 30.0, seed=103 + j, amp=1.0),
                                    B._floor_band(xx, x1, 0.0, B.SPILL[-1][1])], INK)
    return c.device_to_user(*pivot)


def draw_door_shot(c, t):
    pivot = draw_door(c, t)
    # his steps, heard: a paper ripple from the edge of his shadow on each
    for i, ts in enumerate(T_STEPS):
        x = B.SHADOW_LEAD[i + 1]
        K.ripple(c, (x, BAR_Y + 13.0), t, ts, PAPER, n=2, every=0.1, life=0.55, r0=12.0, r1=150.0, width=5.0,
                 seed=140 + i, alpha=0.85)
    handle_arrow(c, t, pivot)
    # the chain snaps taut: a rattle
    g = door_gap(t)
    links = chain_links(g, t)
    mid = links[len(links) // 2][0]
    for i, ts in enumerate(SNAPS):
        K.ripple(c, mid, t, ts, PAPER, n=2, every=0.08, life=0.4, r0=18.0, r1=104.0, width=3.2, seed=150 + i,
                 alpha=0.7)


# ============================================================================ 3. his view through the keyhole
KH = dict(cx=540.0, cy=560.0, r=299.0, top=805.0, bot=1648.0, hw0=177.0, hw1=272.0)     # B's keyhole x 13.6


def keyhole_outline(cx, cy, r, top, bot, hw0, hw1, n=120):
    """The keyhole as one cut: the round and the leg in a single outline (the Bass keyhole's
    proportions). The leg's sides meet the round where they cross it."""
    def side_x(y):
        return hw0 + (y - top) * (hw1 - hw0) / (bot - top)
    # where the leg's right side crosses the circle (bisect between the centre and the leg top)
    lo, hi = cy, top + 40.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if side_x(mid) ** 2 + (mid - cy) ** 2 < r * r:
            lo = mid
        else:
            hi = mid
    yi = lo
    xi = side_x(yi)
    a0 = math.atan2(yi - cy, xi)                    # (below the centre: a positive angle)
    # the round: from the right crossing, anticlockwise on screen over the top, to the left one
    span = math.pi + 2.0 * a0
    pts = []
    for i in range(n + 1):
        a = a0 - span * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts += [(cx - side_x(bot), bot), (cx + side_x(bot), bot)]
    return bass.orient(pts, True)


KEYHOLE_V = keyhole_outline(**KH)
WALL_V = lerp(DEEP, STEEL, 0.28)               # her wall, through the keyhole (A's DEEP, re-lit)
FLOOR_VC = lerp(DEEP, STEEL, 0.13)             # her floor
MOON_C = lerp(STEEL, PAPER, 0.15)              # the moonlight on it

# Her room from her door: A's window view (rooms.draw_window_view: the window, sashes, casing,
# rod and the street of s02 / s06 / s10) pulled back to the door, in A's stage geometry.
# Near layer = A's view px (her wall); things nearer than the wall are placed by their depth.
EYE_ST = (40.0, 1288.0)                        # his eye at the keyhole (stage px: the leaf, under the knob)
D_WALL = R.WINDOW[0] - EYE_ST[0]               # 953: from his eye to her window wall
GL = R.WV_GLASS                                # (276, 340, 804, 1380): the opening, view px
VS = (GL[3] - GL[1]) / (R.WINDOW[3] - R.WINDOW[1])      # 2.15 view px per stage px on the wall
WCX = 0.5 * (GL[0] + GL[2])                    # the window's middle (540)
FLOOR_WV = GL[3] + (R.FLOOR - R.WINDOW[3]) * VS         # 1720: the floor meets the wall
EYE_WV = GL[1] + (EYE_ST[1] - R.WINDOW[1]) * VS         # 1136: his eye line on the wall
ZN = 0.62                                      # her wall through the keyhole: view px -> frame px
PUSH_C = (540.0, 720.0)                        # the slow push's centre (frame px)
VA = (WCX, GL[1] + (PUSH_C[1] - 420.0) / ZN)            # the wall point at PUSH_C: the glass's top at y 420
HISW_F = (598.0, 647.0)                        # his window's centre in the frame: clear of the curtain and the rails
_ZF0 = 1.0 + (ZN - 1.0) * R.FAR_PAR            # A's far camera's zoom for ZN
FA = (R.FAR_AT[0] - (HISW_F[0] - PUSH_C[0]) / _ZF0, R.FAR_AT[1] - (HISW_F[1] - PUSH_C[1]) / _ZF0)
FAR_K = 0.45                                   # the street slides 0.45 x as much as her wall
RAIL_L = D_WALL + 282.0                        # her fire escape's railing, out over the street (the section's)
LAMP_L = R.X_LAMP - EYE_ST[0]                  # her pendant lamp: 707 from his eye
LAMP_DX = 0.0                                  # ... over the window's middle (its pull cord over the glass)
LIGHT = (0.12, 0.84)                           # the moonlight: across and into the room per unit of drop
MUG_AT = (26.0, 162.0)                         # where her mug broke in s04, at her feet at the glass (A's stage x ~ 830)


def view_pan(t):
    """His eye at the keyhole searching the room: (dx, dy, push) of the view, frame px; near
    things slide more than far ones (the street FAR_K x, her lamp more than her wall)."""
    a, b_, c_ = k(t, 9.55, 1.0, "inout"), k(t, 10.55, 0.95, "inout"), k(t, 11.45, 0.9, "inout")
    x = -58.0 * a + 108.0 * b_ - 50.0 * c_
    y = 8.0 * a - 18.0 * b_ + 10.0 * c_
    z = 1.0 + 0.07 * k(t, 11.45, 1.0, "inout")
    return x, y, z


def view_cam(t):
    """(A's Cam for her wall, the frame shift to make before it, (P, zn)): her wall framed in
    the keyhole (VA at PUSH_C + the search P, zoom ZN x the push), and the street, which A's
    far camera draws at its own zoom (FAR_PAR), placed so that it slides FAR_K x P."""
    px, py, zp = view_pan(t)
    zn = ZN * zp
    zf = 1.0 + (zn - 1.0) * R.FAR_PAR
    d = zf - zn
    X = ((1.0 - FAR_K) * px - VA[0] * zn + FA[0] * zf) / d
    Y = ((1.0 - FAR_K) * py - VA[1] * zn + FA[1] * zf) / d
    tx = PUSH_C[0] - 540.0 + px - VA[0] * zn + X * zn
    ty = PUSH_C[1] - 960.0 + py - VA[1] * zn + Y * zn
    return R.Cam(X, Y, zn), (tx, ty), ((px, py), zn)


def at_depth(X, y, L, P, zn):
    """A point in her room -> view px: X stage px across from the window's middle, y its
    stage height (y down), L its distance from his eye; nearer than the wall it is bigger
    and slides more with his eye's search (the street, at infinity, FAR_K x)."""
    s = D_WALL / L
    e = (1.0 - FAR_K) * (s - 1.0) / zn
    return (WCX + X * VS * s + e * P[0], EYE_WV + (y - EYE_ST[1]) * VS * s + e * P[1])


def floor_pt(X, d, P, zn):
    """A point on her floor, d stage px out from the window wall toward the door."""
    return at_depth(X, R.FLOOR, D_WALL - d, P, zn)


def lit_pt(p):
    """Where the moonlight through the window at wall point p (view px) lands on her floor:
    (X, d) in floor coordinates."""
    h = (FLOOR_WV - p[1]) / VS
    return ((p[0] - WCX) / VS + LIGHT[0] * h, LIGHT[1] * h)


_PX = {}


def _pixel(col):
    """The ARGB32 word cairo writes for an opaque `col`."""
    if col not in _PX:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        q = cairo.Context(s)
        q.set_source_rgb(*col)
        q.paint()
        s.flush()
        _PX[col] = int(np.frombuffer(s.get_data(), dtype=np.uint32)[0])
    return _PX[col]


def draw_her_window(c, t, room, cam, shift):
    """A's window view, drawn off the frame (the size of the current clip) and pasted in with
    her dark wall re-lit: A's wall is DEEP, and through a keyhole it must read against the
    black of the door."""
    x0, y0, x1, y1 = c.clip_extents()
    m = c.get_matrix()
    corners = [m.transform_point(x, y) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    tgt = c.get_target()
    bx0 = max(0, int(math.floor(min(p[0] for p in corners))))
    by0 = max(0, int(math.floor(min(p[1] for p in corners))))
    bx1 = min(tgt.get_width(), int(math.ceil(max(p[0] for p in corners))))
    by1 = min(tgt.get_height(), int(math.ceil(max(p[1] for p in corners))))
    if bx1 <= bx0 or by1 <= by0:
        return
    w, h = bx1 - bx0, by1 - by0
    img = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    q = cairo.Context(img)
    q.set_matrix(m * cairo.Matrix(x0=-bx0, y0=-by0))
    q.translate(*shift)
    R.draw_window_view(q, t, room, cam=cam, curtain=False, moon=False)
    img.flush()
    a = np.ndarray((h, img.get_stride() // 4), dtype=np.uint32, buffer=img.get_data())[:, :w]
    a[a == _pixel(R.room_bg(room))] = _pixel(WALL_V)
    img.mark_dirty()
    c.save()
    c.identity_matrix()
    c.set_source_surface(img, bx0, by0)
    c.paint()
    c.restore()


def draw_railing(c, P, zn):
    """Her fire escape just outside, seen through the open lower half: the top rail and its
    bars (the section's railing, face on), clipped to the opening."""
    x0, y0, x1, y1 = GL
    c.save()
    K.clip_rect(c, (x0, y1 - R.WV_LIFT, x1, y1))
    top, bot = R.PLATFORM_Y - 202.0, R.PLATFORM_Y - 188.0          # the rail (stage y)
    a, b = at_depth(-200.0, top, RAIL_L, P, zn), at_depth(200.0, bot, RAIL_L, P, zn)
    polys = [bass.cut_rect(a[0], a[1], b[0], b[1], seed=190, amp=0.3)]
    for i in range(-6, 7):
        X = i * 30.0
        p, q = at_depth(X - 2.6, bot - 2.0, RAIL_L, P, zn), at_depth(X + 2.6, R.PLATFORM_Y, RAIL_L, P, zn)
        polys.append(bass.cut_rect(p[0], p[1], q[0], q[1], seed=191 + i, amp=0.15))
    bass.fill_polys(c, [bass.orient(p, True) for p in polys], INK)
    c.restore()


def curtain_v(t, P, zn):
    """The curtain face on from the door: A's curtain (one panel gathered at the right of the
    window, three folds, a cold rim), but to the floor; the wind swings its free edge in across
    the glass and lifts its hem, and with the gust it comes in toward the door, the lower the
    more (it spreads from his eye's point), fluttering on twos. Returns (outline, folds, the
    free edge on the wall: for its shadow), view px."""
    tt = twos(t)
    b, gust = wind(tt)
    b = clamp(b)
    x1 = GL[2]
    top, hem = R.WV_ROD_Y + 10.0, FLOOR_WV - 10.0
    n = 36
    inner, outer, wall_edge, folds = [], [], [], [[], [], []]
    for i in range(n + 1):
        u = i / n
        fl = b * u * (26.0 * math.sin(2.0 * math.pi * (1.2 * tt - 1.5 * u))
                      + 12.0 * math.sin(2.0 * math.pi * (2.7 * tt - 3.0 * u) + 0.7))
        swing = b * 330.0 * u ** 1.4 + gust * 90.0 * u ** 1.2 + fl
        y = lerp(top, hem, u) - (b * 300.0 + gust * 60.0) * u ** 2.0
        xi = x1 - 40.0 + 10.0 * math.sin(u * 7.0) * (1.0 - b) - swing - 22.0 * u
        xo = x1 + 116.0 + 16.0 * u - b * 120.0 * u ** 1.8 + 0.4 * fl
        wall_edge.append((xi, y))
        L = D_WALL * (1.0 - (0.06 * b + 0.48 * gust) * u ** 1.5)       # how near the door it has come
        def near(x, yy):
            return at_depth((x - WCX) / VS, EYE_ST[1] + (yy - EYE_WV) / VS, L, P, zn)
        inner.append(near(xi, y))
        outer.append(near(xo, y))
        for j, f in enumerate((0.26, 0.5, 0.74)):
            folds[j].append(near(lerp(xi, xo, f + 0.04 * math.sin(u * 5.0 + j)), y))
    wave = []
    for u in (0.2, 0.4, 0.6, 0.8):
        a, c_ = outer[-1], inner[-1]
        wave.append((lerp(a[0], c_[0], u), lerp(a[1], c_[1], u) + (8.0 + 10.0 * b) * math.sin(math.pi * 3.0 * u + 4.0 * tt * b)))
    outline = bass.orient([inner[0], outer[0]] + outer + wave + inner[::-1], True)
    return outline, [f[2:-2] for f in folds], wall_edge


def draw_floor(c, t, P, zn, wall_edge):
    """Her floor, from the wall to the keyhole's foot: the skirting, the boards, the moonlight
    through the window lying on it (the sash rails' shadow across it, the curtain's shadow
    blowing in it from the right) and her broken mug in the light."""
    bass.fill_polys(c, [bass.cut_rect(-2000.0, FLOOR_WV, 3000.0, 4000.0, seed=160, amp=0.8)], FLOOR_VC)
    bass.fill_polys(c, [bass.cut_rect(-2000.0, FLOOR_WV - 30.0, 3000.0, FLOOR_WV, seed=161, amp=0.4)], INK)
    fp = lambda X, d: floor_pt(X, d, P, zn)
    # the boards, running out from the wall to the door
    c.save()
    c.set_source_rgba(*INK, 0.45)
    c.set_line_width(3.0)
    for i in range(-7, 8):
        X = i * 58.0 + 17.0
        c.new_path()
        bass.draw.poly(c, [fp(X, 0.0), fp(X, 640.0)], close=False)
        c.stroke()
    c.restore()
    # the moonlight: the open half, and the glass half above the rails (dimmer)
    x0, y0, x1, y1 = GL
    lift_y = y1 - R.WV_LIFT
    meet = R.WV_MEET - R.MEET_RAIL / 2.0
    zones = (([(x0, y1), (x1, y1), (x1, lift_y), (x0, lift_y)], 0.42),
             ([(x0 + R.STILE, meet), (x1 - R.STILE, meet), (x1 - R.STILE, y0 + R.TOP_RAIL), (x0 + R.STILE, y0 + R.TOP_RAIL)], 0.3))
    edge = [lit_pt(p) for p in wall_edge]
    edge.append((edge[-1][0], 0.0))                  # (its wave hem: no sliver of light under it)
    shadow = [fp(X, d) for X, d in edge] + [fp(900.0, 0.0), fp(900.0, edge[0][1])]
    for zone, alpha in zones:
        c.save()
        c.new_path()
        bass.draw.poly(c, [fp(*lit_pt(p)) for p in zone])
        c.clip()
        c.new_path()
        c.rectangle(-3000.0, -3000.0, 7000.0, 9000.0)
        bass.draw.poly(c, bass.orient(shadow, True))
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.clip()
        c.set_fill_rule(cairo.FILL_RULE_WINDING)
        bass.fill_polys(c, [bass.cut_rect(-3000.0, -3000.0, 4000.0, 6000.0, seed=162, amp=0.3)], MOON_C, alpha)
        c.restore()
    draw_mug_shards(c, P, zn)


def draw_mug_shards(c, P, zn):
    """Her mug, dropped at the window in s04, where it broke: the dark spill on her floor, the
    base still standing with its broken rim, the handle snapped off whole, and chips; their
    edges catch the moonlight."""
    X0, d0 = MUG_AT
    fp = lambda X, d: floor_pt(X, d, P, zn)

    def up(X, d, pts):                               # an upright piece: local (across, up) stage px
        s = D_WALL / (D_WALL - d)
        bx, by = fp(X, d)
        return bass.orient([(bx + x * VS * s, by - y * VS * s) for x, y in pts], True)
    def blob(cx, cd, rx, rd, n, ph, lobes=0.08):
        pts = []
        for i in range(n):
            a = 2.0 * math.pi * i / n
            r = 1.0 + lobes * math.sin(3.0 * a + ph) + 0.6 * lobes * math.sin(5.0 * a + 2.0 * ph)
            pts.append(fp(cx + rx * r * math.cos(a), cd + rd * r * math.sin(a)))
        return bass.orient(pts, True)
    pool = [blob(X0 - 14.0, d0 + 4.0, 48.0, 32.0, 28, 0.5),
            blob(X0 - 70.0, d0 + 22.0, 9.0, 7.0, 12, 1.3, 0.05),        # drops thrown off it
            blob(X0 + 46.0, d0 + 26.0, 12.0, 8.0, 12, 2.1, 0.05),
            blob(X0 + 64.0, d0 + 12.0, 5.0, 4.0, 10, 0.2, 0.0)]
    bass.fill_polys(c, pool, lerp(INK, FLOOR_VC, 0.25))
    sheen = [fp(X0 - 44.0 + 56.0 * u, d0 - 20.0 - 5.0 * math.sin(math.pi * u)) for u in (0.0, 0.25, 0.5, 0.75, 1.0)]
    bass.line_band(c, sheen, MOON_C, width=3.0, seed=241, alpha=0.55)
    base = up(X0 - 22.0, d0 + 4.0, [(-16.0, 0.0), (16.0, 0.0), (16.6, 6.0), (13.5, 12.0), (10.0, 7.5), (5.5, 23.0),
                                     (1.5, 14.0), (-3.5, 17.0), (-8.5, 8.0), (-12.5, 11.5), (-16.6, 6.5)])
    hc = (0.0, 12.0)
    handle = []
    for i in range(15):
        a = math.radians(lerp(-110.0, 160.0, i / 14.0))
        handle.append((hc[0] + 11.5 * math.cos(a), hc[1] + 12.5 * math.sin(a)))
    for i in range(15):
        a = math.radians(lerp(160.0, -110.0, i / 14.0))
        handle.append((hc[0] + 6.5 * math.cos(a), hc[1] + 7.5 * math.sin(a)))
    handle = up(X0 + 46.0, d0 - 16.0, handle)
    chips = [bass.orient([fp(X0 - 78.0, d0 - 22.0), fp(X0 - 62.0, d0 - 30.0), fp(X0 - 64.0, d0 - 12.0)], True),
             bass.orient([fp(X0 + 84.0, d0 + 20.0), fp(X0 + 98.0, d0 + 30.0), fp(X0 + 80.0, d0 + 38.0)], True),
             bass.orient([fp(X0 + 8.0, d0 + 48.0), fp(X0 + 26.0, d0 + 44.0), fp(X0 + 20.0, d0 + 58.0)], True),
             bass.orient([fp(X0 - 30.0, d0 - 40.0), fp(X0 - 18.0, d0 - 46.0), fp(X0 - 14.0, d0 - 36.0), fp(X0 - 26.0, d0 - 32.0)], True)]
    pieces = [base, handle] + chips
    c.save()
    c.translate(-2.0, -3.0)
    bass.fill_polys(c, pieces, MOON_C)
    c.restore()
    bass.fill_polys(c, pieces, INK)


def draw_curtain(c, outline, folds):
    """A's dark curtain: ink, its free edge caught cold by the window, the folds faint."""
    c.save()
    c.translate(-4.0, 0.0)
    bass.fill_polys(c, [outline], STEEL)
    c.restore()
    bass.fill_polys(c, [outline], INK)
    c.save()
    c.set_source_rgb(*lerp(STEEL, INK, 0.5))
    c.set_line_width(3.0)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ln in folds:
        c.new_path()
        bass.draw.poly(c, ln, close=False)
        c.stroke()
    c.restore()
    rod = getattr(R, "_wv_rod_polys", None)          # the rod and its brackets back over the cloth
    if rod is not None:
        bass.fill_polys(c, rod(), INK)


def draw_lamp(c, t, P, zn):
    """Her pendant lamp (A's coolie shade), nearer than the wall: off; only its rim, the bulb
    and the pull cord hang into the keyhole, the cord's bead swinging in the wind (on twos)."""
    tt = twos(t)
    wnd, gust = wind(tt)
    def lp(x, y):
        return at_depth(LAMP_DX + (x - R.X_LAMP), y, LAMP_L, P, zn)
    polys = [bass.orient([lp(x, y) for x, y in poly], True) for poly in R.lamp_polys()]
    bulb_c = lp(R.X_LAMP, R.LAMP_BULB[1] + 4.0)
    bass.fill_polys(c, polys, INK)
    s = D_WALL / LAMP_L * VS
    K.dot(c, bulb_c, 12.0 * s, lerp(INK, STEEL, 0.3), seed=231)
    K.dot(c, (bulb_c[0] - 4.5 * s, bulb_c[1] + 3.5 * s), 2.6 * s, lerp(STEEL, PAPER, 0.25), seed=235)   # its glass, cold
    sw = wnd * (0.6 * math.sin(tt * 3.1) + 0.4 * math.sin(tt * 5.3 + 1.0)) + gust * 0.8 * math.sin(tt * 6.4)
    a = math.radians(9.0 * sw)
    top = lp(*R.CORD_TOP)
    cl = 0.94 * R.CORD_LEN * s                       # (its bead clear of the sash rails behind it)
    end = (top[0] + cl * math.sin(a), top[1] + cl * math.cos(a))
    bass.line_band(c, [top, end], INK, width=2.6 * s, seed=232)
    K.dot(c, end, 7.0 * s, INK, seed=233)
    K.dot(c, (end[0] + 1.6 * s, end[1] - 2.2 * s), 2.2 * s, lerp(STEEL, PAPER, 0.3), seed=234)


ROOM_V = R.Room(lit=False, window=1.0, wind=0.0, chain="on", door=0.0, mug=False)


def draw_view(c, t):
    """Her dark room from her door, at keyhole height: A's window view, her floor, the
    curtain, the lamp (view px through A's camera), drifting as his eye searches."""
    cam, shift, (P, zn) = view_cam(t)
    draw_her_window(c, t, ROOM_V, cam, shift)
    outline, folds, wall_edge = curtain_v(t, P, zn)
    c.save()
    c.translate(*shift)
    cam.apply(c)
    draw_railing(c, P, zn)
    draw_floor(c, t, P, zn, wall_edge)
    draw_curtain(c, outline, folds)
    draw_lamp(c, t, P, zn)
    c.restore()


def draw_pov(c, t):
    """The whole POV frame: black, and the keyhole of light with her room in it."""
    K.fill(c, INK)
    c.save()
    c.new_path()
    bass.draw.poly(c, KEYHOLE_V)
    c.clip()
    draw_view(c, t)
    # the inside of the keyhole: the hole's own edge, faintly lit
    c.new_path()
    bass.draw.poly(c, KEYHOLE_V)
    c.set_line_width(16.0)
    c.set_source_rgb(*lerp(INK, STEEL, 0.22))
    c.stroke()
    c.restore()


# ============================================================================ 2. the keyhole, his eye
S_R = 0.085                     # the POV, small in his pupil
Z_DIVE = 1.0 / S_R              # the dive lands exactly on the POV
PUPIL_C = (G.EYE_C[0], G.EYE_C[1] - 6.0)


def reflect_pov(t):
    def fn(c, ic, pr):
        c.save()
        c.translate(ic[0], ic[1])
        c.scale(S_R, S_R)
        c.translate(-540.0, -960.0)
        draw_pov(c, t)
        c.restore()
    return fn


def eye_state(t):
    """(slide, open, look, pupil, low) of his eye at the keyhole."""
    slide = lerp(1150.0, 0.0, k(t, T_FACE, 0.14, "out3"))
    if t >= T_BACK:
        n = k(t, T_NARROW, 0.4, "inout")
        look = -0.06 * k(t, T_BACK, 0.3, "inout")
        return 0.0, lerp(1.0, 0.46, n), look, lerp(1.45, 1.15, n), n
    open_ = k(t, T_OPEN, 0.1, "outback")
    look = 0.17 * (k(t, T_OPEN + 0.15, 0.25, "inout") - 2.0 * k(t, T_OPEN + 0.55, 0.32, "inout")
                   + k(t, T_DIVE - 0.28, 0.22, "inout"))
    pupil = lerp(1.0, 1.45, k(t, T_WIDEN, 0.25, "outback"))
    return slide, open_, look, pupil, 0.0


def dive_xf(c, t):
    """Into his pupil: a zoom on its centre that lands, at T_POV, exactly on the POV frame."""
    u = k(t, T_DIVE, T_POV - T_DIVE, "inout3")
    if u <= 0.0:
        return
    z = math.exp(math.log(Z_DIVE) * u)
    c.translate(lerp(PUPIL_C[0], 540.0, u), lerp(PUPIL_C[1], 960.0, u))
    c.scale(z, z)
    c.translate(-PUPIL_C[0], -PUPIL_C[1])


def draw_key_shot(c, t, back=False):
    """The Bass key shot, re-timed: in to the keyhole, his eye in it (and, back=True, the hold
    on it at the end)."""
    p = 1.0 if back else k(t, T_KEY, 0.6, "inout")
    z = math.exp(math.log(15.0) * p)
    if back:
        z *= 1.0 + 0.05 * k(t, T_BACK, 1.5, "inout")
    kc = (B.KEYHOLE[0], B.KEYHOLE[1] - 18.0)
    c.save()
    if not back:
        dive_xf(c, t)
    c.save()
    c.translate(lerp(kc[0], G.EYE_C[0], p), lerp(kc[1], G.EYE_C[1] - 6.0, p))
    c.scale(z, z)
    c.translate(-kc[0], -kc[1])
    draw_door(c, t, gap=0.0)
    c.new_path()
    for poly in B.keyhole_pts(B.KEYHOLE):
        bass.draw.poly(c, poly)
    c.restore()
    c.clip()                                   # (the path survives the restore)
    slide, open_, look, pupil, low = eye_state(t)
    c.translate(slide, 0.0)
    G.his_eye(c, open_, look, pupil=pupil, iris=RED, skin=AMBER, low=low, reflect=reflect_pov(t), glint=True,
              mirror=True, fine=3.0)
    c.restore()


# ============================================================================ the scene
def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        if t < T_KEY:
            draw_door_shot(c, t)
        elif t < T_POV:
            draw_key_shot(c, t)
        elif t < T_BACK:
            draw_pov(c, t)
        else:
            draw_key_shot(c, t, back=True)


def motion_blur(t, T):
    return 1


def cues(T):
    return [
        Cue(0.0, "her empty dark room: wind at the open window, the curtain stirring", gain_db=-18, dur=T_KEY),
        Cue(T_STEPS[0], "his step on the landing", gain_db=-10),
        Cue(T_STEPS[1], "his step on the landing", gain_db=-9),
        Cue(T_STEPS[2], "his step on the landing", gain_db=-8),
        Cue(T_FEET, "he stops at her door; a held breath", gain_db=-12),
        Cue(T_KNOB[0], "the handle tried", gain_db=-8),
        Cue(SNAPS[0], "the door jolts open on the chain: chain snaps taut", gain_db=-6),
        Cue(T_KNOB[1], "the handle again, harder", gain_db=-7),
        Cue(SNAPS[1], "the chain snaps taut", gain_db=-5),
        Cue(SNAPS[2], "slammed against the chain", gain_db=-5),
        Cue(SNAPS[3], "slammed against the chain", gain_db=-5),
        Cue(T_KEY, "into the keyhole: a low swell", gain_db=-12, dur=T_POV - T_KEY),
        Cue(T_FACE, "his face at the keyhole: the light goes out, his breath", gain_db=-10),
        Cue(T_OPEN, "his eye opens: a dry tick", gain_db=-12),
        Cue(T_DIVE, "into his eye: a rising whoosh", gain_db=-10),
        Cue(T_POV, "inside: wind, the curtain flapping, the lamp cord ticking", gain_db=-12, dur=T_BACK - T_POV),
        Cue(T_GUST, "a gust: the curtain cracks", gain_db=-8),
        Cue(T_BACK, "back on his eye: a low stinger", gain_db=-6),
        Cue(T_NARROW, "it narrows: a held low cluster", gain_db=-10, dur=14.0 - T_NARROW),
    ]
