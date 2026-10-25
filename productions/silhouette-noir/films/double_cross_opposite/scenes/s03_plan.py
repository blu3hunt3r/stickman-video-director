"""s03 · PLAN (30-48): straight down on the bank's plan under the lamp. Her gloved finger traces
the way in (manhole A, the sewer, the hatch, across the hall in the dark of the guard's sweep, the
vault door); she taps the bell on the side door (not that way), then the vault twice, and the first
red ring closes round the gold. The looks from above: his to the gold, the Cracker's to the vault
door, hers to his face and then, unseen, down to the sewer under the vault. His golden arm, from
the side; the split mirror, his profile and hers; she pulls the lamp's cord: dark.

Screen direction carries on from s02's table: the Knight on the left, she on the right (the top
shot looks down with the table's far side at the top, the Cracker there)."""
import math

from engine import bass, paperdoll as pd
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import faces as F
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import room as R
from films.double_cross_opposite import street as St
from films.opposite_full import kit as OK

k = K.k
INK, PAPER, AMBER, RED, NIGHT, STEEL, DEEP = K.INK, K.PAPER, K.AMBER, K.RED, K.NIGHT, K.STEEL, K.DEEP
T0 = K.film_start("s03")                  # film time of this scene's t = 0

# ---------------------------------------------------------------- beats (scene time)
T_TRACE = 0.5                             # her hand leaves the table's edge for manhole A
T_MH_A = 0.9                              # manhole A: down
T_HATCH = 1.7                             # along the sewer and up the hatch
T_WAIT = 1.95                             # the hall's dark corner: she waits on the sweep
T_CROSS = (2.45, 3.25)                    # across in its dark to the vault door
T_BELL = 3.75                             # she taps the bell on the side door: not that way
T_TAPS = (4.5, 5.0)                       # she taps the vault, twice
T_RING = (5.0, 0.4)                       # the first red marker ring closes round the gold
T_GLINT = 5.4                             # the gold glints
T_HOME = (5.4, 0.5)                       # her hand goes back to the table's edge
T_LOOK_K, T_LOOK_C, T_LOOK_H = 6.0, 6.5, 7.25    # his look to the gold, the Cracker's to the door, hers to him
T_SLIP = (8.25, 0.45)                     # her look leaves his face for the sewer under the vault
T_ANSWER = 8.75                           # a small ripple answers there
T_ARM = 9.0                               # the golden arm: the table from the side
T_GROW = (9.6, 1.0)                       # his jagged arm grows across the table to the gold
T_CLAW = (10.55, 0.3)                     # its claw closes over it
T_SNAP = (11.0, 0.14)                     # it snaps back
T_MIRROR = 12.0                           # the split mirror
T_HIS_DOTS = 12.15                        # his look runs down out of the frame to the gold
T_HER_DOTS = 12.6                         # hers crosses the split into his eye
T_PRESS = (13.0, 13.5, 14.0, 14.5)        # the halves press in on the beat
T_OUT = 15.5                              # the room, wide
T_REACH = (15.75, 0.5)                    # she reaches up for the lamp's cord
T_PULL = (16.3, 0.2)                      # and pulls it
T_DARK = 16.5                             # dark
T_LEAVE = 16.6                            # three shapes go to the door


def motion_blur(t, T):
    return 1


# ================================================================ 0-9: straight down on the plan
TABLE_F = (100.0, 280.0, 980.0, 1660.0)   # the table's top in the lamp's pool (frame px at zoom 1)
SHEET = (180.0, 380.0, 900.0, 1540.0)     # the plan
TEN_WALL = (180.0, 198.0)                 # the tenement's front wall (cut by the sheet's edge)
TEN_DOOR = (1100.0, 1160.0)               # its street door (y)
CURB_T, CURB_B = 248.0, 404.0             # the two curbs
BANK = (452.0, 520.0, 888.0, 1400.0)      # the bank's outer walls
WALL = 16.0
SIDE_DOOR = (690.0, 752.0)                # the side door's span in the front wall (y)
MAIN_DOOR = (930.0, 1010.0)
BELL_P = (430.0, 672.0)                   # the bell, drawn on the wall over the side door
Y_SEWER = 792.0                           # the sewer's line, the street's width and on under the bank
SEWER_HALF = 13.0
SEWER_END = 826.0                         # it ends under the vault
MH_B = (272.0, Y_SEWER)                   # manhole B, at the tenement's curb
MH_A = (326.0, Y_SEWER)                   # manhole A, in the road
HATCH = (504.0, Y_SEWER)                  # the hatch, in the hall's dark corner by the side door
VAULT = (690.0, 536.0, 872.0, 880.0)      # the vault, in the bank's far corner
VAULT_W = 24.0
VDOOR = (702.0, 700.0)                    # its round door, in the wall to the hall
GOLD_C = (790.0, 612.0)                   # the gold: five bars
BOXES_X = (830.0, 852.0)                  # the deposit boxes on the back wall
DESK = (640.0, 950.0)                     # the guard's desk
GUARD = (640.0, 990.0)                    # the guard at it: his light's apex
CRATES = ((524.0, 1296.0), (562.0, 1326.0))
W_PT = (520.0, 786.0)                     # the dark corner, just out of the sweep's reach
M_PT = (606.0, 746.0)
VD_PT = (676.0, 706.0)                    # at the vault door
ROUTE = (MH_A, HATCH, W_PT, M_PT, VD_PT)
TAP_P = (786.0, 654.0)                    # where she taps the vault
REST = (930.0, 1046.0)                    # her fingertip at rest on the table's edge
CONE_LEN, CONE_SPREAD = 300.0, 13.0

KNIGHT_AT = (80.0, 900.0)                 # heads from above: his cap (left), facing in
CRACKER_AT = (430.0, 214.0)               # the Cracker's bowler (top)
HER_AT = (1010.0, 1184.0)                 # her chignon (right)
EYE_K = (176.0, 902.0)                    # where the looks leave from: under his peak,
EYE_C = (430.0, 308.0)                    # under the Cracker's brim,
EYE_H = (934.0, 1172.0)                   # and her face
FACE_K = (192.0, 906.0)                   # his face, the end of her look
OVER_C = (540.0, 930.0)                   # the top shot's camera: centre, zoom from .. to
OVER_Z = (0.94, 0.985)


def _seglens(pts):
    return [math.dist(a, b) for a, b in zip(pts, pts[1:])]


ROUTE_L = _seglens(ROUTE)
S_HATCH = ROUTE_L[0]
S_WAIT = S_HATCH + ROUTE_L[1]
S_END = sum(ROUTE_L)


def route_at(s):
    for (a, b), L in zip(zip(ROUTE, ROUTE[1:]), ROUTE_L):
        if s <= L:
            u = s / L if L else 0.0
            return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))
        s -= L
    return ROUTE[-1]


def finger(t):
    """Her fingertip: (point, lift 0 pressed .. 1 lifted, route length traced)."""
    def hop(a, b, t0, t1):
        u = clamp((t - t0) / (t1 - t0))
        e = ease("inout", u)
        return (lerp(a[0], b[0], e), lerp(a[1], b[1], e)), math.sin(math.pi * u)

    if t < T_TRACE:
        return REST, 0.0, 0.0
    if t < T_MH_A:
        p, l = hop(REST, MH_A, T_TRACE, T_MH_A)
        return p, l, 0.0
    if t < T_HATCH:
        s = S_HATCH * ease("inout", (t - T_MH_A) / (T_HATCH - T_MH_A))
        return route_at(s), 0.0, s
    if t < T_WAIT:
        s = lerp(S_HATCH, S_WAIT, ease("inout", (t - T_HATCH) / (T_WAIT - T_HATCH)))
        return route_at(s), 0.0, s
    if t < T_CROSS[0]:
        return W_PT, 0.0, S_WAIT
    if t < T_CROSS[1]:
        s = lerp(S_WAIT, S_END, ease("inout", (t - T_CROSS[0]) / (T_CROSS[1] - T_CROSS[0])))
        return route_at(s), 0.0, s
    if t < T_BELL:
        p, l = hop(VD_PT, BELL_P, T_CROSS[1], T_BELL)
        return p, l, S_END
    if t < T_TAPS[0] - 0.3:
        return BELL_P, 0.0, S_END
    if t < T_TAPS[0]:
        p, l = hop(BELL_P, TAP_P, T_TAPS[0] - 0.3, T_TAPS[0])
        return p, l, S_END
    if t < T_TAPS[1]:
        return TAP_P, 0.45 * math.sin(math.pi * (t - T_TAPS[0]) / (T_TAPS[1] - T_TAPS[0])), S_END
    if t < T_HOME[0]:
        return TAP_P, 0.0, S_END
    p, l = hop(TAP_P, REST, T_HOME[0], T_HOME[0] + T_HOME[1])
    return p, l, S_END


def cone_ang(t):
    """The guard's light, swinging at his desk: its centre (deg, frame), left extreme at 2.2."""
    return -78.0 - 26.0 * math.cos(2.0 * math.pi * (t - 2.2) / 1.6)


def lean_in(t):
    """She leans in over the table while she traces (her head and shoulders come in)."""
    return k(t, T_TRACE - 0.1, 0.5, "inout") * (1.0 - k(t, T_HOME[0], 0.6, "inout"))


# ---------------------------------------------------------------- the drawing on the sheet
def _rect(r, seed, amp=0.35):
    return bass.cut_rect(r[0], r[1], r[2], r[3], seed=seed, amp=amp)


def _ell(cx, cy, rx, ry, n=64, seed=0, amp=0.5, a0=0.0, a1=360.0, close=False):
    pts = []
    for i in range(n + (0 if a1 - a0 >= 360.0 else 1)):
        th = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + rx * math.cos(th), cy + ry * math.sin(th)))
    if close:
        pts.append((cx, cy))
    return bass.orient(bass.cut(pts, seed=seed, amp=amp, seg=(8.0, 16.0)), True)


def _line(c, a, b, w=3.5, seed=0, color=INK):
    bass.line_band(c, [a, b], color, width=w, seed=seed)


def draw_sheet(c, t):
    x0, y0, x1, y1 = SHEET
    bass.fill_polys(c, [_rect(SHEET, 3001, 0.6)], PAPER)
    walls = [_rect((TEN_WALL[0], y0, TEN_WALL[1], TEN_DOOR[0]), 3002), _rect((TEN_WALL[0], TEN_DOOR[1], TEN_WALL[1], y1), 3003)]
    bx0, by0, bx1, by1 = BANK
    fw = (bx0, bx0 + WALL)
    walls += [_rect((fw[0], by0, fw[1], SIDE_DOOR[0]), 3004), _rect((fw[0], SIDE_DOOR[1], fw[1], MAIN_DOOR[0]), 3005),
              _rect((fw[0], MAIN_DOOR[1], fw[1], by1), 3006), _rect((bx0, by0, bx1, by0 + WALL), 3007),
              _rect((bx0, by1 - WALL, bx1, by1), 3008), _rect((bx1 - WALL, by0, bx1, by1), 3009)]
    vx0, vy0, vx1, vy1 = VAULT
    walls += [_rect((vx0, vy0, vx0 + VAULT_W, vy1), 3010), _rect((vx0, vy1 - VAULT_W, vx1, vy1), 3011),
              _rect((vx0, vy0, vx1, vy0 + 16.0), 3012), _rect((vx1 - 16.0, vy0, vx1, vy1), 3013)]
    bass.fill_polys(c, walls, INK)
    # the curbs, the tenement's door, the bank's doors and steps
    for i, x in enumerate((CURB_T, CURB_B)):
        _line(c, (x, y0), (x, y1), 4.0, seed=3020 + i)
    _line(c, (TEN_WALL[1] - 2.0, TEN_DOOR[0]), (TEN_WALL[1] + 40.0, TEN_DOOR[0] + 30.0), 3.0, seed=3022)
    _line(c, (fw[1] - 2.0, SIDE_DOOR[0]), (fw[1] + 50.0, SIDE_DOOR[0] + 26.0), 3.0, seed=3023)   # the side door, ajar on the plan
    bass.line_band(c, [(fw[1] + 50.0 * math.cos(math.radians(a)), SIDE_DOOR[0] + 50.0 * math.sin(math.radians(a)) * 1.0)
                       for a in range(28, 92, 8)], INK, width=2.0, seed=3024)
    for i in range(3):
        x = bx0 - 12.0 - 12.0 * i
        _line(c, (x, MAIN_DOOR[0] - 14.0 - 6.0 * i), (x, MAIN_DOOR[1] + 14.0 + 6.0 * i), 3.0, seed=3025 + i)
    _line(c, (fw[0] + 8.0, MAIN_DOOR[0]), (fw[0] + 8.0, MAIN_DOOR[1]), 3.0, seed=3028)
    # the sewer: dashed, the street's width and on under the bank to the vault
    for sgn in (-1.0, 1.0):
        K.dashes(c, [(x0, Y_SEWER + sgn * SEWER_HALF), (SEWER_END, Y_SEWER + sgn * SEWER_HALF)], INK, width=3.5,
                 dash=18.0, gap=12.0, seed=3030 + int(sgn), alpha=1.0)
    K.dashes(c, [(SEWER_END, Y_SEWER - SEWER_HALF), (SEWER_END, Y_SEWER + SEWER_HALF)], INK, width=3.5, dash=10.0,
             gap=6.0, seed=3033, alpha=1.0)
    for i, p in enumerate((MH_B, MH_A)):
        bass.fill_polys(c, [bass.ring_pts(p, 20.0, seed=3040 + i, n=40, amp=0.3)], PAPER)
        bass.ring(c, p, 20.0, 4.0, INK, seed=3042 + i, n=40)
        K.dot(c, p, 5.0, INK, seed=3044 + i)
    hx, hy = HATCH
    hr = (hx - 15.0, hy - 15.0, hx + 15.0, hy + 15.0)
    bass.fill_polys(c, [_rect(hr, 3046)], PAPER)
    for a, b in (((hr[0], hr[1]), (hr[2], hr[1])), ((hr[2], hr[1]), (hr[2], hr[3])), ((hr[2], hr[3]), (hr[0], hr[3])),
                 ((hr[0], hr[3]), (hr[0], hr[1])), ((hr[0], hr[1]), (hr[2], hr[3]))):
        _line(c, a, b, 3.0, seed=3047)
    # the guard's desk, his chair, the crates
    dx, dy = DESK
    for r_, sd in (((dx - 46.0, dy - 22.0, dx + 46.0, dy + 22.0), 3050), ((dx - 16.0, dy + 30.0, dx + 16.0, dy + 62.0), 3051)) + \
            tuple(((p[0] - 18.0, p[1] - 18.0, p[0] + 18.0, p[1] + 18.0), 3052 + i) for i, p in enumerate(CRATES)):
        for a, b in (((r_[0], r_[1]), (r_[2], r_[1])), ((r_[2], r_[1]), (r_[2], r_[3])), ((r_[2], r_[3]), (r_[0], r_[3])),
                     ((r_[0], r_[3]), (r_[0], r_[1]))):
            _line(c, a, b, 3.5, seed=sd)
    # the bank's windows in its front wall, the hall's columns, the stair to the offices
    for i, (ya, yb) in enumerate(((560.0, 640.0), (1070.0, 1140.0), (1230.0, 1300.0))):
        bass.fill_polys(c, [_rect((fw[0] - 1.0, ya, fw[1] + 1.0, yb), 3110 + i, 0.2)], PAPER)
        for xx in (fw[0] + 3.0, fw[1] - 3.0):
            _line(c, (xx, ya), (xx, yb), 2.5, seed=3113 + i)
    bass.fill_polys(c, [_rect((x - 10.0, 1176.0, x + 10.0, 1196.0), 3120 + i, 0.2) for i, x in enumerate((560.0, 680.0, 800.0))],
                    INK)
    st = (764.0, 1236.0, 856.0, 1368.0)
    for a, b in (((st[0], st[1]), (st[0], st[3])), ((st[2], st[1]), (st[2], st[3]))):
        _line(c, a, b, 3.0, seed=3124)
    for i in range(8):
        y = st[1] + (st[3] - st[1]) * i / 7.0
        _line(c, (st[0], y), (st[2], y), 2.0, seed=3125 + i)
    # the deposit boxes on the vault's back wall
    for i in range(7):
        y = 646.0 + 28.0 * i
        bx = (BOXES_X[0], y, BOXES_X[1], y + 22.0)
        for a, b in (((bx[0], bx[1]), (bx[2], bx[1])), ((bx[2], bx[1]), (bx[2], bx[3])), ((bx[2], bx[3]), (bx[0], bx[3])),
                     ((bx[0], bx[3]), (bx[0], bx[1]))):
            _line(c, a, b, 2.5, seed=3060 + i)


def draw_vault_door(c):
    bass.fill_polys(c, [bass.ring_pts(VDOOR, 30.0, seed=3070, n=48, amp=0.3)], PAPER)
    bass.ring(c, VDOOR, 30.0, 6.0, INK, seed=3071, n=48)
    bass.ring(c, VDOOR, 14.0, 3.0, INK, seed=3072, n=32)
    K.dot(c, VDOOR, 4.0, INK, seed=3073)


def draw_gold(c, t):
    gx, gy = GOLD_C
    bars = [(gx + dx - 16.0, gy + 6.0, gx + dx + 16.0, gy + 22.0) for dx in (-36.0, 0.0, 36.0)] + \
           [(gx + dx - 16.0, gy - 12.0, gx + dx + 16.0, gy + 4.0) for dx in (-18.0, 18.0)]
    for i, b in enumerate(bars):
        K.edged(c, [_rect(b, 3080 + i, 0.25)], AMBER, INK, 6.0)


def draw_bell(c, t):
    dt = t - T_BELL
    rock = 16.0 * math.sin(2.0 * math.pi * 7.0 * dt) * math.exp(-dt / 0.25) if dt > 0.0 else 0.0
    _line(c, (BELL_P[0] - 18.0, BELL_P[1] - 24.0), (BELL_P[0] + 18.0, BELL_P[1] - 24.0), 4.0, seed=3090)
    K.bell(c, BELL_P, 0.95, INK, seed=3091, ring=rock)


def draw_cone(c, t):
    a = cone_ang(t)
    n = 16
    pts = [GUARD] + [(GUARD[0] + CONE_LEN * math.cos(math.radians(a - CONE_SPREAD + 2.0 * CONE_SPREAD * i / n)),
                      GUARD[1] + CONE_LEN * math.sin(math.radians(a - CONE_SPREAD + 2.0 * CONE_SPREAD * i / n)))
                     for i in range(n + 1)]
    bass.fill_polys(c, [bass.orient(pts, True)], AMBER, 0.42)
    bass.line_band(c, pts + [GUARD], INK, width=3.0, seed=3095)
    K.dot(c, GUARD, 13.0, INK, seed=3096)                     # the guard at his desk


# ---------------------------------------------------------------- dots and rings on the paper
def edged_dot(c, p, r, color, seed=0, e=3.5):
    K.dot(c, p, r + e, INK, seed=seed)
    K.dot(c, p, r, color, seed=seed)


def edged_ripple(c, p, t, t0, color, **kw):
    w = kw.pop("width", 6.0)
    K.ripple(c, p, t, t0, INK, width=w + 5.0, **kw)
    K.ripple(c, p, t, t0, color, width=w, **kw)


def edged_look(c, a, b, t, t0, color, dur=0.45, off=None, off_dur=0.3, march=30.0, r=7.0, gap=25.0, head=28.0,
               seed=0):
    """K.sight_line with an INK edge round each dot and the arrowhead, for looks laid on the paper."""
    if t < t0:
        return
    lead = k(t, t0, dur, "out3")
    tail = k(t, off, off_dur, "in3") if off is not None else 0.0
    if tail >= 0.999:
        return
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    dx, dy = dx / L, dy / L
    s1, s0 = L * lead, L * tail
    if s1 - s0 < 2.0:
        return
    stop = s1 - (head * 0.95 + r)
    s = s0 + ((march * (t - t0)) % gap)
    while s <= stop:
        g = min(1.0, (s - s0) / gap * 1.4 + 0.25, (stop - s) / (0.6 * gap) + 0.45)
        edged_dot(c, (a[0] + dx * s, a[1] + dy * s), r * clamp(g), color, seed=seed * 131 + int(s // gap))
        s += gap
    if s1 - s0 > head * 0.8:
        sz = min(head, (s1 - s0) * 0.9)
        tip = (a[0] + dx * s1, a[1] + dy * s1)
        OK.arrowhead(c, (tip[0] + dx * 4.0, tip[1] + dy * 4.0), (dx, dy), sz + 10.0, INK, seed=seed)
        OK.arrowhead(c, tip, (dx, dy), sz, color, seed=seed)


def draw_trail(c, s_end):
    """Her way in, dots laid behind her fingertip along the route."""
    gap = 26.0
    s = 0.0
    i = 0
    while s <= s_end - 14.0:
        edged_dot(c, route_at(s), 6.5, PAPER, seed=3100 + i, e=3.0)
        s += gap
        i += 1


# ---------------------------------------------------------------- the three, from above
def _shift(polys, d):
    return [[(x + d[0], y + d[1]) for x, y in p] for p in polys]


def _rimmed(c, polys, rim, d, px=7.0):
    bass.fill_polys(c, _shift(polys, (d[0] * px, d[1] * px)), rim)
    bass.fill_polys(c, polys, INK)


def _fist(x, y, rx, ry, facing, seed, arm_to):
    """A hand resting on the table's edge: the fist, its knuckles toward the table, the forearm off."""
    fx, fy = facing
    hand = _ell(x, y, rx, ry, n=40, seed=seed)
    knuck = [_ell(x + fx * rx * 0.86 + (-fy) * rx * 0.5 * o, y + fy * ry * 0.86 + fx * ry * 0.5 * o, rx * 0.26, ry * 0.26,
                  n=16, seed=seed + 1 + i) for i, o in enumerate((-1.2, -0.4, 0.4, 1.2))]
    ax, ay = arm_to
    wx, wy = -fy, fx                      # across the forearm
    w = 0.78 * (ry if fx else rx)
    arm = bass.orient([(x + wx * w, y + wy * w), (ax + wx * w * 1.25, ay + wy * w * 1.25),
                       (ax - wx * w * 1.25, ay - wy * w * 1.25), (x - wx * w, y - wy * w)], True)
    return [arm, hand] + knuck


def knight_above(c, t):
    x, y = KNIGHT_AT
    d = (1.0, 0.0)
    shoulders = _ell(x - 112.0, y, 132.0, 262.0, seed=3201)
    crown = _ell(x - 6.0, y, 84.0, 76.0, seed=3202)
    peak = _ell(x + 62.0, y, 48.0, 64.0, seed=3203, a0=-90.0, a1=90.0, n=24)
    hands = _fist(x + 92.0, y - 156.0, 46.0, 38.0, (1.0, 0.0), 3210, (-60.0, y - 190.0)) + \
        _fist(x + 92.0, y + 156.0, 46.0, 38.0, (1.0, 0.0), 3220, (-60.0, y + 196.0))
    _rimmed(c, hands, RED, d, 6.0)
    _rimmed(c, [shoulders, crown, peak], RED, d, 7.0)
    # the cigarette under his peak, its ember breathing on twos
    a, b = (x + 100.0, y + 30.0), (x + 132.0, y + 38.0)
    bass.line_band(c, [a, b], PAPER, width=6.0, seed=3230)
    glow = 0.5 + 0.5 * math.sin(2.0 * math.pi * 0.4 * K.twos(T0 + t))
    K.dot(c, b, 16.0 + 5.0 * glow, RED, seed=3231, alpha=0.25)
    K.dot(c, b, 6.5, RED, seed=3232)


def cracker_above(c, t):
    x, y = CRACKER_AT
    d = (0.0, 1.0)
    shoulders = _ell(x, y - 108.0, 206.0, 120.0, seed=3301)
    brim = _ell(x, y, 98.0, 86.0, seed=3302)
    crown = _ell(x, y - 8.0, 62.0, 58.0, seed=3303)
    hands = _fist(x - 86.0, y + 112.0, 26.0, 32.0, (0.0, 1.0), 3310, (x - 120.0, y - 40.0)) + \
        _fist(x + 92.0, y + 112.0, 26.0, 32.0, (0.0, 1.0), 3320, (x + 130.0, y - 40.0))
    _rimmed(c, hands, AMBER, d, 5.0)
    for i, hx in enumerate((x - 86.0, x + 92.0)):            # his shirt cuffs
        bass.fill_polys(c, [_rect((hx - 22.0, y + 70.0, hx + 22.0, y + 80.0), 3330 + i, 0.3)], PAPER)
    _rimmed(c, [shoulders, brim], AMBER, d, 6.0)
    bass.fill_polys(c, _shift([crown], (0.0, 5.0)), AMBER)  # the crown's lit edge on the brim
    bass.fill_polys(c, [crown], INK)


def her_above(c, t, fingertip, lift):
    li = lean_in(t)
    x, y = HER_AT[0] - 46.0 * li, HER_AT[1] - 10.0 * li
    d = (-1.0, 0.0)
    shoulders = _ell(x + 122.0, y, 120.0, 232.0, seed=3401)
    head = _ell(x, y, 70.0, 80.0, seed=3402)
    bun = _ell(x + 64.0, y + 8.0, 40.0, 38.0, seed=3403)
    rest = _fist(x - 74.0, y + 200.0, 30.0, 26.0, (-1.0, 0.0), 3410, (x + 120.0, y + 260.0))
    _rimmed(c, rest, PAPER, d, 5.0)
    _rimmed(c, [shoulders, head, bun], PAPER, d, 6.0)
    # the pencil through the chignon
    a, b = (x + 36.0, y - 34.0), (x + 116.0, y + 50.0)
    bass.line_band(c, [(a[0] - 2.0, a[1] - 2.0), (b[0] + 2.0, b[1] + 2.0)], PAPER, width=11.0, seed=3420)
    bass.line_band(c, [a, b], INK, width=6.0, seed=3421)
    # the right hand, gloved, pointing from her shoulder
    s = 0.78 + 0.07 * lift
    F.hand(c, "architect", (x + 40.0, y - 120.0), fingertip, s=s, point=True)
    return x, y


def draw_people(c, t):
    p, lift, _ = finger(t)
    cracker_above(c, t)
    knight_above(c, t)
    her_above(c, t, p, lift)


def her_eye(t):
    li = lean_in(t)
    return (EYE_H[0] - 46.0 * li, EYE_H[1] - 10.0 * li)


# ---------------------------------------------------------------- the top shot
def draw_overhead(c, t):
    K.fill(c, DEEP)
    z = lerp(OVER_Z[0], OVER_Z[1], k(t, 0.0, T_ARM, "inout"))
    c.save()
    c.translate(K.W / 2.0, K.H / 2.0)
    c.scale(z, z)
    c.translate(-OVER_C[0], -OVER_C[1])
    bass.fill_polys(c, [_rect(TABLE_F, 3500, 0.8)], AMBER)
    draw_sheet(c, t)
    p, lift, s_tr = finger(t)
    draw_cone(c, t)
    draw_trail(c, s_tr)
    for t0, q in ((T_MH_A, MH_A), (T_HATCH, HATCH)):         # down at manhole A, up at the hatch
        edged_ripple(c, q, t, t0, PAPER, n=2, every=0.12, life=0.5, r0=16.0, r1=46.0, width=4.0, seed=int(q[0]))
    draw_vault_door(c)
    draw_gold(c, t)
    draw_bell(c, t)
    edged_ripple(c, BELL_P, t, T_BELL, PAPER, n=2, every=0.13, life=0.6, r0=20.0, r1=80.0, width=5.0, seed=3600)
    for i, t0 in enumerate(T_TAPS):
        edged_ripple(c, TAP_P, t, t0, PAPER, n=1, life=0.4, r0=12.0, r1=48.0, width=4.0, seed=3610 + i)
    u = k(t, T_RING[0], T_RING[1], "inout")
    if u > 0.0:
        K.marker_ring(c, (GOLD_C[0], GOLD_C[1] + 4.0), 84.0, 58.0, u, RED, width=13.0, seed=3620)
    g = clamp((t - T_GLINT) / 0.45)
    if 0.0 < g < 1.0:
        K.twinkle(c, (GOLD_C[0] + 26.0, GOLD_C[1] - 14.0), 54.0 * math.sin(math.pi * g), PAPER)
    draw_people(c, t)
    # the looks, from above
    edged_look(c, EYE_K, (GOLD_C[0] - 30.0, GOLD_C[1] + 22.0), t, T_LOOK_K, RED, dur=0.5, seed=3700)
    edged_look(c, EYE_C, (VDOOR[0] - 22.0, VDOOR[1] - 18.0), t, T_LOOK_C, AMBER, dur=0.5, seed=3701)
    su = k(t, T_SLIP[0], T_SLIP[1], "inout")
    tgt = (lerp(FACE_K[0], SEWER_END - 18.0, su), lerp(FACE_K[1], Y_SEWER, su))
    edged_look(c, her_eye(t), tgt, t, T_LOOK_H, PAPER, dur=0.6, seed=3702)
    edged_ripple(c, (SEWER_END - 18.0, Y_SEWER), t, T_ANSWER, PAPER, n=2, every=0.15, life=0.6, r0=10.0, r1=44.0,
                 width=4.0, seed=3710)
    c.restore()


# ================================================================ 9-12: the golden arm, from the side
ARM_CAM = ((206.0, 676.0), 7.0)
GOLD_X = R.TABLE_X + 18.0                 # where the gold lies on the plan, on the table (section px)
NIGHT_SECTION = dict(sky_lit=0.0, moon_at=St.MOON_S, under=1.0, gold_glow=1.0, car=dict(lights=0.0), lamp_on=1.0)


def _fig(c, who, st, pose, x, fy, facing, bg=AMBER, rim=None, rim_w=1.4, light=(-0.6, -0.8), eye=True):
    return C.draw(c, who, st, pose, x, fy, s=St.FIG_S, facing=facing, bg=bg, rim=rim, rim_w=rim_w, light=light,
                  eye=eye)


def her_at_table(t, x=R.HER_TABLE):
    """Her leaning on the table's end over the plan, as s02 left her."""
    x1 = R.TABLE_X + R.TABLE_HALF
    return pd.Pose(lean=14.0, crouch=10.0, head=-14.0,
                   arms={"near": ("ik", R.on_table(x, R.TABLE_X + 14.0)), "far": ("ik", R.on_table(x, R.TABLE_X + 24.0))})


def arm_crew(t, tf, got):
    def fn(c, rect):
        fy = rect[3]
        # the Knight at the table's end, upright now, his look on the gold
        st = C.standing("knight", spread=18.0)
        pose = pd.Pose(lean=5.0, head=-18.0, arms={"near": ("ang", -2.0, 22.0), "far": ("ang", 4.0, 12.0)})
        out = _fig(c, "knight", st, pose, R.KNIGHT_TABLE, fy, 1)
        C.cigarette(c, out, tf, St.FIG_S, facing=1)
        got["shoulder"] = out["shoulder_near"]
        # the Cracker in his chair; he ducks under the arm
        sh = k(t, T_GROW[0] + 0.05, 0.3, "out3") * (1.0 - k(t, T_SNAP[0] + 0.15, 0.5, "inout"))
        nod = 2.5 * math.sin(2.0 * math.pi * 0.25 * K.twos(tf))
        pose = pd.Pose(lean=22.0 + 12.0 * sh, head=-20.0 - 14.0 * sh + nod * (1.0 - sh), crouch=6.0 * sh,
                       arms={"near": ("ik", R.on_table(R.CRACKER_SEAT, R.TABLE_X - 8.0 + 3.0 * sh)),
                             "far": ("ik", R.on_table(R.CRACKER_SEAT, R.TABLE_X - 16.0 + 3.0 * sh))})
        _fig(c, "cracker", R.seated("cracker"), pose, R.CRACKER_SEAT, fy, 1)
        # her at the far end: she lifts her head to watch him
        w = k(t, T_GROW[0] - 0.2, 0.5, "inout")
        pose = her_at_table(t)
        pose.head = lerp(-14.0, 4.0, w)
        pose.lean = lerp(14.0, 10.0, w)
        _fig(c, "architect", C.standing("architect", spread=16.0), pose, R.HER_TABLE, fy, -1)
    return fn


def draw_arm(c, t):
    tf = T0 + t
    got = {}
    R.draw_stage(c, tf, cam=ARM_CAM, crew=arm_crew(t, tf, got), plan=1.0, neighbours="asleep", **NIGHT_SECTION)
    gold = R.to_frame((GOLD_X, R.TABLE_TOP - 1.5), ARM_CAM)
    g = clamp((t - (T_ARM + 0.25)) / 0.5)
    if 0.0 < g < 1.0:
        K.twinkle(c, (gold[0], gold[1] - 8.0), 96.0 * math.sin(math.pi * g), PAPER)
    grow = k(t, T_GROW[0], T_GROW[1], "inout") * (1.0 - k(t, T_SNAP[0], T_SNAP[1], "in3"))
    if grow > 0.0 and "shoulder" in got:
        base = R.to_frame(got["shoulder"], ARM_CAM)
        claw = lerp(0.25, 1.35, k(t, T_CLAW[0], T_CLAW[1], "outback"))
        tip = (gold[0] - 84.0, gold[1] - 92.0)
        bass.jagged_arm(c, base, tip, RED, width=62.0, grow=grow, jags=4, jag=0.8, claw=claw, seed=3800)


# ================================================================ 12-15.5: the mirror
SPLIT_X = 540.0
EYE_Y = 960.0
EYE_KX, EYE_HX = 340.0, 740.0             # their eyes, level, either side of the red line
FACE_S = 0.8


def press(t):
    return sum(ease("outback", clamp((t - tp) / 0.22)) for tp in T_PRESS)


def knight_mirrored(c, t, eye, s):
    """His profile turned to face right (faces.knight faces left), its eye at `eye`."""
    at = (eye[0] + 80.0 * s, eye[1] + 576.0 * s)
    c.save()
    c.translate(2.0 * eye[0], 0.0)
    c.scale(-1.0, 1.0)
    m = F.knight(c, at, s, look=0.25, draw=0.0, t=T0 + t, field=DEEP, smoke=1.0)
    c.restore()
    return {key: (2.0 * eye[0] - v[0], v[1]) for key, v in m.items()}


def her_mirrored(c, t, eye, s):
    """Her profile turned to face left (faces.her faces right), its eye at `eye`."""
    at = (eye[0] - 80.0 * s, eye[1] + 560.0 * s)
    c.save()
    c.translate(2.0 * eye[0], 0.0)
    c.scale(-1.0, 1.0)
    m = F.her(c, at, s, look=0.7, t=T0 + t, field=AMBER)
    c.restore()
    return {key: (2.0 * eye[0] - v[0], v[1]) for key, v in m.items()}


def draw_mirror(c, t):
    p = press(t)
    s = FACE_S * 1.06 ** p
    sh = 26.0 * p
    ek, eh = (EYE_KX + sh, EYE_Y), (EYE_HX - sh, EYE_Y)
    c.save()
    K.clip_rect(c, (0.0, 0.0, SPLIT_X, K.H))
    K.fill(c, DEEP)
    mk = knight_mirrored(c, t, ek, s)
    K.sight_line(c, mk["eye"], (mk["eye"][0] + 170.0, K.H + 80.0), t, T_HIS_DOTS, RED, dur=0.5, seed=3900)
    c.restore()
    c.save()
    K.clip_rect(c, (SPLIT_X, 0.0, K.W, K.H))
    K.fill(c, AMBER)
    mh = her_mirrored(c, t, eh, s)
    c.restore()
    bass.line_band(c, [(SPLIT_X, -20.0), (SPLIT_X, K.H + 20.0)], RED, width=12.0, seed=3901)
    K.sight_line(c, mh["eye"], (mk["eye"][0] + 18.0, mk["eye"][1]), t, T_HER_DOTS, PAPER, dur=0.45, seed=3902)


# ================================================================ 15.5-18: lights out
def out_crew(t, tf, dark):
    def fn(c, rect):
        fy = rect[3]
        if not dark:
            nod = 2.5 * math.sin(2.0 * math.pi * 0.25 * K.twos(tf))
            st = C.standing("knight", spread=16.0)
            pose = pd.Pose(lean=7.0, head=-20.0, arms={"near": ("ang", -6.0, 16.0), "far": ("ang", 4.0, 12.0)})
            out = _fig(c, "knight", st, pose, R.KNIGHT_TABLE, fy, 1)
            C.cigarette(c, out, tf, St.FIG_S, facing=1)
            pose = pd.Pose(lean=22.0, head=-20.0 + nod,
                           arms={"near": ("ik", R.on_table(R.CRACKER_SEAT, R.TABLE_X - 8.0)),
                                 "far": ("ik", R.on_table(R.CRACKER_SEAT, R.TABLE_X - 16.0))})
            _fig(c, "cracker", R.seated("cracker"), pose, R.CRACKER_SEAT, fy, 1)
            up = k(t, T_OUT, 0.3, "inout")
            reach = k(t, T_REACH[0], T_REACH[1], "inout")
            pull = k(t, T_PULL[0], T_PULL[1], "in3")
            hx = R.HER_TABLE - 6.0 * reach
            _, end = R.lamp_cord(tf, 1.5, pull)
            pose = her_at_table(t, hx)
            pose.lean = lerp(14.0, 2.0, up) - 3.0 * reach
            pose.crouch = lerp(10.0, 0.0, up) + 4.0 * pull
            pose.head = lerp(-14.0, -2.0, up) - 10.0 * reach
            if reach > 0.0:
                cord = ((end[0] - hx) / St.FIG_S, (end[1] + 3.0 - R.FLOOR) / St.FIG_S)
                rest = (3.0 / St.FIG_S, -70.0 / St.FIG_S)
                pose.arms = {"near": ("ik", (lerp(rest[0], cord[0], reach), lerp(rest[1], cord[1], reach))),
                             "far": ("ang", 4.0, 12.0)}
            elif up > 0.0:
                pose.arms = {"near": ("ang", 6.0, 14.0), "far": ("ang", 3.0, 10.0)}
            _fig(c, "architect", C.standing("architect", spread=16.0), pose, hx, fy, -1)
        else:
            # three shapes to the door in the dark, rimmed by the window's night
            lt = (0.85, -0.5)
            heads = {}
            # the Knight: a beat in the dark, then he turns for the door
            u = max(0.0, t - (T_DARK + 0.3))
            x = R.KNIGHT_TABLE - 92.0 * u
            if x > R.DOOR[0] - 20.0:
                ph = 2.6 * u
                st = C.standing("knight", spread=16.0 + 46.0 * abs(math.sin(math.pi * ph)))
                pose = pd.Pose(lean=6.0, head=-6.0, arms={"near": ("ang", 14.0 * math.sin(math.pi * ph), 14.0),
                                                          "far": ("ang", -14.0 * math.sin(math.pi * ph), 12.0)})
                _fig(c, "knight", st, pose, x, fy - abs(math.sin(math.pi * ph)), -1 if u > 0.0 else 1, bg=DEEP, rim=STEEL,
                     rim_w=1.0, light=lt, eye=False)
            # the Cracker: he gets up out of his chair, then follows
            up = k(t, T_DARK + 0.35, 0.4, "inout")
            u = max(0.0, t - (T_DARK + 0.75))
            x = R.CRACKER_SEAT - 80.0 * u
            ph = 2.6 * u
            a, b = R.seated("cracker"), C.standing("cracker", spread=16.0 + 46.0 * abs(math.sin(math.pi * ph)))
            st = dict(b, pelvis=(lerp(a["pelvis"][0], b["pelvis"][0], up), lerp(a["pelvis"][1], b["pelvis"][1], up)),
                      feet={key: tuple(lerp(p0, p1, up) for p0, p1 in zip(a["feet"][key], b["feet"][key])) for key in a["feet"]})
            pose = pd.Pose(lean=lerp(22.0, 16.0, up), head=lerp(-20.0, -6.0, up),
                           arms={"near": ("ang", 14.0 * math.sin(math.pi * ph), 14.0),
                                 "far": ("ang", -14.0 * math.sin(math.pi * ph), 12.0)})
            if up < 1.0:
                pose.arms = {"near": ("ik", R.on_table(R.CRACKER_SEAT, lerp(R.TABLE_X - 8.0, R.TABLE_X - 30.0, up))),
                             "far": ("ang", 4.0, 12.0)}
            _fig(c, "cracker", st, pose, x, fy - abs(math.sin(math.pi * ph)) * (u > 0.0), -1 if u > 0.0 else 1, bg=DEEP,
                 rim=STEEL, rim_w=1.0, light=lt, eye=False)
            # her: the arm comes down off the cord, then she goes last
            u = max(0.0, t - (T_DARK + 0.6))
            x0 = R.HER_TABLE - 6.0
            x = x0 - 96.0 * u
            ph = 2.6 * u
            st = C.standing("architect", spread=16.0 + 46.0 * abs(math.sin(math.pi * ph)))
            down = k(t, T_DARK, 0.3, "inout")
            pose = pd.Pose(lean=4.0, head=-4.0, arms={"near": ("ang", 14.0 * math.sin(math.pi * ph), 14.0),
                                                      "far": ("ang", -14.0 * math.sin(math.pi * ph), 12.0)})
            if down < 1.0:
                _, end = R.lamp_cord(tf, 1.5, 1.0)
                cord = ((end[0] - x0) / St.FIG_S, (end[1] + 3.0 - R.FLOOR) / St.FIG_S)
                rest = (3.0 / St.FIG_S, -70.0 / St.FIG_S)
                pose.arms["near"] = ("ik", (lerp(cord[0], rest[0], down), lerp(cord[1], rest[1], down)))
            out = _fig(c, "architect", st, pose, x, fy - abs(math.sin(math.pi * ph)), -1, bg=DEEP, rim=STEEL, rim_w=1.0,
                       light=lt, eye=False)
            heads["architect"] = out["head"]
            # her two eyes: she looks back once, at the lamp, as she goes
            e = clamp((t - 17.3) / 0.1) * (1.0 - clamp((t - 17.8) / 0.1))
            if e > 0.0 and "architect" in heads:
                hx, hy = heads["architect"]
                lid = 0.25 if abs(t - 17.55) < 0.05 else 1.0
                for dx in (-1.5, 1.5):
                    K.dot(c, (hx + dx, hy - 0.6), 0.85 * e * lid, PAPER, seed=3990)
    return fn


def draw_out(c, t):
    tf = T0 + t
    dark = t >= T_DARK
    pull = k(t, T_PULL[0], T_PULL[1], "in3") * (1.0 - k(t, T_DARK, 0.25, "out3"))
    R.draw_stage(c, tf, cam=R.STAGE, lit=not dark, pull=pull, crew=out_crew(t, tf, dark), plan=1.0,
                 neighbours="asleep", beams={St.CREW_FLOOR} if not dark else False,
                 **dict(NIGHT_SECTION, lamp_on=1.0))


# ================================================================ the scene
def render(f, t, T):
    if t < T_ARM:
        K.scene_setup(f, DEEP)
    elif t < T_MIRROR:
        K.scene_setup(f, NIGHT)
    elif t < T_OUT:
        K.scene_setup(f, AMBER)
    else:
        K.scene_setup(f, NIGHT)
    with f.screen() as c:
        if t < T_ARM:
            draw_overhead(c, t)
        elif t < T_MIRROR:
            draw_arm(c, t)
        elif t < T_OUT:
            draw_mirror(c, t)
        else:
            draw_out(c, t)


def cues(T):
    return [
        Cue(0.0, "her murmur, low and close, no words (the DOUBLE CROSS voice take), as she lays out the way in",
            gain_db=-9, dur=3.4),
        Cue(0.2, "a low cello hum under the murmur: the old man listening", gain_db=-18, dur=3.0),
        Cue(T_MH_A, "a soft tap on paper: her fingertip on manhole A", gain_db=-15, pan=-0.3),
        Cue(T_MH_A + 0.05, "her glove sliding along the paper, the sewer's way", gain_db=-19, pan=-0.1, dur=0.8),
        Cue(T_HATCH, "a soft tap on paper: up through the hatch", gain_db=-15),
        Cue(2.1, "the guard's light sweeping: a faint high string glissando, away and back", gain_db=-18, dur=1.2),
        Cue(T_CROSS[0], "her glove sliding across the paper behind the light", gain_db=-19, pan=0.1, dur=0.8),
        Cue(T_BELL, "one damped tink: the alarm bell's own note, muted, as her finger taps the bell on the plan",
            gain_db=-12, pan=-0.2),
        Cue(T_TAPS[0], "a tap on paper: her finger on the vault", gain_db=-10, pan=0.2),
        Cue(T_TAPS[1], "a second tap on paper, on the vault", gain_db=-10, pan=0.2),
        Cue(T_RING[0], "a sting: a high string harmonic and a marker pen's squeak as the red ring closes round the gold",
            gain_db=-8, pan=0.2),
        Cue(T_GLINT, "a glint on the gold: a soft high shimmer", gain_db=-17, pan=0.25),
        Cue(T_LOOK_K, "his low note: a cello C sharp, held under the looks", gain_db=-10, pan=-0.3, dur=3.0),
        Cue(T_LOOK_C, "the old man's look: a middle pizzicato", gain_db=-14),
        Cue(T_LOOK_H, "her look: a high violin D, held soft", gain_db=-14, pan=0.3, dur=1.0),
        Cue(T_SLIP[0], "a low held note as her look slips down to the sewer, unseen", gain_db=-12, dur=0.75),
        Cue(T_ANSWER, "a tiny drip-like pluck where her look lands", gain_db=-18, pan=0.2),
        Cue(T_ARM, "the room from the side: the wall clock ticking, the lamp's chain creaking", gain_db=-16, dur=3.0),
        Cue(T_GROW[0], "braam: a low brass and string swell as his jagged red arm grows across the table", gain_db=-6,
            pan=-0.2, dur=1.0),
        Cue(T_CLAW[0], "the claw closing: a dry scrape and a string snap", gain_db=-10),
        Cue(T_SNAP[0], "the arm snaps back: a short low thud and a whoosh", gain_db=-8, pan=-0.3),
        Cue(T_MIRROR, "the mirror: the clock louder, a sustained dissonance between her high D and his low C sharp",
            gain_db=-10, dur=3.5),
        Cue(T_HIS_DOTS, "his look sinking: a low descending pizzicato run", gain_db=-14, pan=-0.4),
        Cue(T_HER_DOTS, "her look crosses the line: a thin high string line", gain_db=-14, pan=0.2),
        Cue(T_PRESS[0], "the clock ticks, louder, as the halves press in", gain_db=-8),
        Cue(T_PRESS[1], "the clock ticks, louder", gain_db=-7),
        Cue(T_PRESS[2], "the clock ticks, louder", gain_db=-6),
        Cue(T_PRESS[3], "the clock ticks, loudest", gain_db=-5),
        Cue(T_OUT, "the room: the clock, the lamp's chain creaking", gain_db=-16, dur=1.0),
        Cue(T_PULL[0], "the cord pulled: the lamp's chain rattles", gain_db=-12, pan=0.2),
        Cue(T_DARK, "click: the lamp goes out", gain_db=-6, pan=0.1),
        Cue(T_DARK + 0.3, "in the dark: soft steps to the door, three people, the chair pushed back", gain_db=-16,
            pan=-0.2, dur=1.2),
        Cue(17.85, "the door, closing softly", gain_db=-16, pan=-0.5),
    ]
