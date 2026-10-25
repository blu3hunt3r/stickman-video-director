"""s11 · END (166-174): from straight above, her gloved fist under the street lamp opens on the
ruby; it glints (an X of light along the frame's diagonals: the one celesta ping) and she closes
her hand on it, the red leaking between her fingers and dying. Then the street's elevation as the
title left it: the windows the letters became snap back to paper and fly up into the title,
DOUBLE over CROSS, paper on black (the reverse of the opening), while the street sinks into
black. The paper strip and the red one cross over it again, an X; on the last chord the title is
cut along the red strip and the halves slide apart along it and away; the red strip draws in to
the centre and pops as the red dot, which beats twice like a heart (the ruby) and is gone. Black.
Silence.

  0-2.5    THE PALM, straight down: the fist opens, the index finger first (0.4-1.2); the glint
           (1.5); the hand closes (2.2).
  2.5-5    THE TITLE: the windows fly back (2.52-3.25) and it stamps (3.25); the strips, an X
           (3.5, 3.75); the cut, the halves part and go (4.0-4.95); the red draws in (4.55-5.0).
  5-8      Black: the red dot pops (5.0), beats (5.45, 6.05), is gone by 7.0. Silence from 7.5.
"""
import math
from functools import lru_cache

from engine import bass, draw
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.double_cross_opposite import faces as F
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import street as St
from films.double_cross_opposite.scenes import s01_title as S01

k = K.k
W, H = K.W, K.H
INK, PAPER, AMBER, RED, NIGHT, STEEL, SHUT = K.INK, K.PAPER, K.AMBER, K.RED, K.NIGHT, K.STEEL, K.SHUT
C0 = (W / 2.0, H / 2.0)
_DIAG = math.atan2(H, W)

# ---------------------------------------------------------------- beats (scene time)
T_OPEN = (0.4, 1.2)               # her fist opens on the ruby, the index finger first
T_PING = 1.5                      # the ruby glints: an X of light (the one celesta ping)
T_FIST = 2.2                      # she closes her hand on it
FIST_DUR = 0.2
T_ELEV = 2.5                      # the street's elevation, as the title left it
T_SNAP = 2.52                     # the letters' windows snap back to paper, one after another ...
STAGGER = 0.025
MORPH = 0.16                      # ... each turns back into its letter where it is ...
FLY = 0.36                        # ... and flies up into the title
T_BLACK = (2.78, 0.32)            # the street sinks into black behind them
T_STAMP = 3.25                    # the title lands: DOUBLE over CROSS, paper on black
T_STRIPS = (3.5, 3.75)            # the paper strip, then the red one across it: the X again
STRIP_IN = 0.24
T_CUT = 4.0                       # the last chord: the title is cut along the red strip ...
T_AWAY = 4.45                     # ... the halves slide apart along it, and away
T_DRAW_IN = (4.55, 0.45)          # the red strip draws in to the centre ...
T_POP = 5.0                       # ... and pops as the red dot
BEATS = ((5.45, 1.0), (6.05, 0.7))   # it beats like a heart: lub (dub after it), and how hard
T_GONE = (6.5, 0.45)              # it shrinks away: gone by 7.0
T_SILENCE = 7.5

CLOCK_END = (12, 25)              # the bank's clock now (s10 left it at 12:21)


def motion_blur(t, T):
    return 1


# ================================================================ 0-2.5: the palm, straight down
# The pavement she stands on, from above: its kerb along the frame's diagonal, the road beyond it
# in the top left, a puddle, the lamp's pool. Frame px.
X_C = C0                          # the ruby lies at the frame's centre: its glint is the diagonals' X
KERB_O = (200.0, 600.0)           # a point on the kerb's road edge
KERB_ANG = math.atan2(-math.sin(_DIAG), math.cos(_DIAG))
FLAG = (236.0, 196.0)             # the paving slabs: along the kerb, across it
POOL_AT = (360.0, 700.0)          # the lamp's pool: the lamp stands at the kerb, up and to the left
PUDDLE_AT = (205.0, 1385.0)
ASPHALT = lerp(NIGHT, INK, 0.4)
JOINT = lerp(NIGHT, INK, 0.45)
SHADOW = lerp(NIGHT, INK, 0.72)


def _kerb_pt(x, y):
    """The kerb's frame (x along it, y across it toward the pavement) to frame px."""
    ca, sa = math.cos(KERB_ANG), math.sin(KERB_ANG)
    return (KERB_O[0] + x * ca - y * sa, KERB_O[1] + x * sa + y * ca)


@lru_cache(maxsize=1)
def _pavement():
    """In the kerb's frame: the slabs [(shade, polygon)], the kerb stones, the slabs' far edges in
    frame px (for the wet sheen), the road's specks; the puddle in frame px."""
    slabs, edges = [], []
    w, h = FLAG
    for r in range(9):
        y0 = 70.0 + r * h
        off = (r % 3) * w / 3.0
        for j in range(-7, 6):
            x0 = j * w + off
            slabs.append((int(hash01(r, j, 511) * 4.0),
                          bass.cut_rect(x0 + 4.0, y0 + 4.0, x0 + w - 4.0, y0 + h - 4.0, seed=r * 31 + j + 950, amp=2.0,
                                        seg=(40.0, 90.0))))
            edges.append((_kerb_pt(x0 + 24.0, y0 + 12.0), _kerb_pt(x0 + w - 40.0, y0 + 12.0)))
    kerb = [bass.cut_rect(j * 280.0 + 43.0, 4.0, j * 280.0 + 317.0, 66.0, seed=980 + j, amp=1.2) for j in range(-6, 5)]
    specks = [(-1400.0 + 2500.0 * hash01(i, 521), -600.0 + 585.0 * hash01(i, 522), 1.5 + 2.5 * hash01(i, 523))
              for i in range(170)]
    puddle = bass.orient(F.spline([(PUDDLE_AT[0] + (150.0 + 40.0 * hash01(i, 531)) * math.cos(2.0 * math.pi * i / 7.0),
                                    PUDDLE_AT[1] + (80.0 + 26.0 * hash01(i, 532)) * math.sin(2.0 * math.pi * i / 7.0))
                                   for i in range(7)], n=6), True)
    return slabs, kerb, edges, specks, puddle


def draw_street(c, t, gz):
    """The pavement, the kerb and the road from above, the lamp's pool on them, a few wet slabs and
    the puddle catching it (gz: the ground's zoom about the centre: it is far below the hand, so it
    moves less as the camera pushes in)."""
    slabs, kerb, edges, specks, puddle = _pavement()
    K.fill(c, ASPHALT)
    c.save()
    c.translate(*X_C)
    c.scale(gz, gz)
    c.translate(-X_C[0], -X_C[1])
    c.save()
    c.translate(*KERB_O)
    c.rotate(KERB_ANG)
    for x, y, r in specks:
        bass.fill_polys(c, [draw.circle_pts((x, y), r, n=6)], lerp(NIGHT, STEEL, 0.25))
    bass.fill_polys(c, [bass.cut_rect(-1500.0, -18.0, 1200.0, 2.0, seed=990, amp=1.0)], lerp(NIGHT, INK, 0.7))
    bass.fill_polys(c, kerb, lerp(NIGHT, STEEL, 0.55))
    bass.fill_polys(c, [bass.cut_rect(-1500.0, 70.0, 1200.0, 1900.0, seed=991, amp=1.0)], JOINT)
    for b in range(4):
        bass.fill_polys(c, [p for j, p in slabs if j == b], lerp(NIGHT, STEEL, 0.2 + 0.06 * b))
    bass.line_band(c, [(-1500.0, 6.0), (1200.0, 6.0)], PAPER, width=3.0, seed=992, alpha=0.3)
    c.restore()
    bass.fill_polys(c, [puddle], lerp(NIGHT, INK, 0.62))
    K.pool(c, POOL_AT, 720.0, 660.0, AMBER, 0.15, steps=4)
    for i, (a, b) in enumerate(edges):                        # wet slabs catching the lamp
        d = math.dist(a, POOL_AT)
        if d < 600.0 and hash01(i, 505) < 0.45:
            bass.line_band(c, [a, b], AMBER, width=4.0, seed=i, alpha=0.32 * (1.0 - d / 600.0))
    # the lamp in the puddle: an amber smear, paper at its heart
    K.pool(c, (PUDDLE_AT[0] + 30.0, PUDDLE_AT[1] - 14.0), 70.0, 26.0, AMBER, 0.55, steps=3)
    K.pool(c, (PUDDLE_AT[0] + 30.0, PUDDLE_AT[1] - 14.0), 24.0, 9.0, PAPER, 0.5, steps=2)
    c.restore()


# Hand units: the palm about 1 wide, the wrist at +y, the fingers along -y. Her right hand, palm up
# under the lamp, seen from above (the thumb on the right), turned a little so the forearm comes in
# from the bottom right.
HAND_ROT = math.radians(-12.0)
_PALM = ((-0.40, 0.66), (-0.48, 0.30), (-0.53, -0.10), (-0.50, -0.44), (-0.40, -0.58), (-0.16, -0.66),
         (0.12, -0.68), (0.36, -0.63), (0.50, -0.50), (0.52, -0.22), (0.60, 0.04), (0.62, 0.30), (0.52, 0.52),
         (0.40, 0.66))
# (base, direction when straight (deg; -90 is up the frame), segment lengths, width, delay as the hand
# opens: the index first)
_FINGERS = (((0.33, -0.60), -83.0, (0.40, 0.25, 0.21), 0.215, 0.0),
            ((0.10, -0.65), -91.0, (0.44, 0.28, 0.22), 0.225, 0.08),
            ((-0.14, -0.62), -99.0, (0.40, 0.26, 0.21), 0.215, 0.16),
            ((-0.36, -0.53), -108.0, (0.32, 0.20, 0.18), 0.19, 0.24))
_FLEX = (88.0, 98.0, 72.0)        # each joint's bend in the fist
_THUMB = ((0.50, 0.04), (-36.0, -160.0), (0.36, 0.30), 0.25)     # base, direction (open, shut), lengths, width
_CUFF = ((-0.44, 0.56), (0.44, 0.56), (0.50, 0.92), (-0.50, 0.92))
RUBY_HU = (-0.02, -0.32)          # where the ruby lies: in the hollow below the fingers
RUBY_R = 0.2
SLEEVE = F.HANDS["architect"]["sleeve"]
GLOVE = lerp(lerp(INK, PAPER, 0.06), AMBER, 0.11)     # black leather in the lamp's warm light
_ARM = (0.3, 1.0)                 # the forearm's way (hand units), toward her


@lru_cache(maxsize=1)
def _palm_poly():
    return bass.orient(F.spline(_PALM, n=5), True)


def _curl(t, delay):
    """How closed a finger is (1: in the fist): it opens from T_OPEN[0] + delay, and closes on the
    ruby at T_FIST (the little finger last)."""
    o = ease("inout", clamp((t - T_OPEN[0] - delay) / (T_OPEN[1] - T_OPEN[0] - 0.3)))
    shut = ease("inout", clamp((t - T_FIST - 0.3 * delay) / FIST_DUR))
    return max(1.0 - o, shut)


def _finger(base, dirn, lens, w, curl):
    """A finger's segments [(a, b, ra, rb, z, lit)] at curl (0 straight .. 1 in the fist). Each joint
    bends toward the camera, so a bent segment foreshortens and the last ones fold back over the
    palm; lit: how squarely it faces the lamp (end-on is dark)."""
    d = (math.cos(math.radians(dirn)), math.sin(math.radians(dirn)))
    p, z, phi = base, 0.0, 0.0
    radii = (0.5 * w, 0.47 * w, 0.43 * w, 0.4 * w)
    out = []
    for i, L in enumerate(lens):
        phi += _FLEX[i] * curl
        cs, sn = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        q = (p[0] + d[0] * L * cs, p[1] + d[1] * L * cs)
        z1 = z + L * sn
        out.append((p, q, radii[i], radii[i + 1], 0.5 * (z + z1), abs(cs)))
        p, z = q, z1
    return out


def _thumb(curl):
    base, (a_open, a_shut), lens, w = _THUMB
    a1 = math.radians(lerp(a_open, a_shut, curl))
    a2 = a1 + math.radians(lerp(10.0, 22.0, curl))
    p1 = (base[0] + lens[0] * math.cos(a1), base[1] + lens[0] * math.sin(a1))
    p2 = (p1[0] + lens[1] * math.cos(a2), p1[1] + lens[1] * math.sin(a2))
    z = 0.02 + 0.5 * curl
    return [(base, p1, 0.5 * w, 0.46 * w, z, 1.0), (p1, p2, 0.46 * w, 0.4 * w, z + 0.01, 1.0)]


def _hand_parts(t):
    """The glove at t (hand units): [(z, polygon, colour)], back to front."""
    parts = [(-0.2, bass.orient(list(_CUFF), True), lerp(INK, AMBER, 0.05)),
             (0.0, _palm_poly(), GLOVE)]
    segs = []
    for base, dirn, lens, w, delay in _FINGERS:
        segs += _finger(base, dirn, lens, w, _curl(t, delay))
    segs += _thumb(_curl(t, 0.1))
    for a, b, ra, rb, z, lit in segs:
        parts.append((z + 0.001, bass.capsule_pts(a, b, ra, rb, cap=4), lerp(INK, GLOVE, 0.4 + 0.75 * lit)))
    parts.sort(key=lambda it: it[0])
    return parts


@lru_cache(maxsize=1)
def _sleeve():
    """Her coat sleeve (hand units): from the glove's cuff off the frame toward her, with the
    trench coat's strap and button."""
    L = math.hypot(*_ARM)
    d = (_ARM[0] / L, _ARM[1] / L)
    n = (-d[1], d[0])
    e = (0.03, 0.86)

    def at(s, w):
        return (e[0] + d[0] * s + n[0] * w, e[1] + d[1] * s + n[1] * w)
    sleeve = bass.orient([at(0.0, 0.58), at(-0.05, 0.0), at(0.0, -0.58), at(3.4, -0.74), at(3.4, 0.74)], True)
    strap = bass.orient([at(0.2, 0.6), at(0.2, -0.6), at(0.34, -0.62), at(0.34, 0.62)], True)
    return sleeve, strap, at(0.27, 0.4)


def _ruby(c, p, r, rot=0.0, flash=0.0, px=1.0):
    """The ruby from above: a cut octagon, its crown facets lit from the top left (the lamp), the
    table in the middle. px: frame px per unit here (for the hairlines)."""
    n = 8
    outer = [(p[0] + r * math.cos(rot + 2.0 * math.pi * i / n), p[1] + r * math.sin(rot + 2.0 * math.pi * i / n))
             for i in range(n)]
    inner = [(p[0] + 0.56 * r * math.cos(rot + 2.0 * math.pi * i / n),
              p[1] + 0.56 * r * math.sin(rot + 2.0 * math.pi * i / n)) for i in range(n)]
    light = math.radians(-135.0)
    for i in range(n):
        j = (i + 1) % n
        mid = rot + 2.0 * math.pi * (i + 0.5) / n
        b = 0.5 + 0.5 * math.cos(mid - light)
        col = lerp(lerp(RED, INK, 0.55), lerp(RED, PAPER, 0.4), b)
        bass.fill_polys(c, [bass.orient([outer[i], outer[j], inner[j], inner[i]], True)], col)
    bass.fill_polys(c, [bass.orient(inner, True)], lerp(RED, PAPER, 0.1 + 0.55 * flash))
    hl = (p[0] - 0.3 * r, p[1] - 0.26 * r)
    bass.fill_polys(c, [bass.orient([(hl[0] - 0.16 * r, hl[1] + 0.04 * r), (hl[0] + 0.02 * r, hl[1] - 0.14 * r),
                                     (hl[0] + 0.1 * r, hl[1] - 0.06 * r), (hl[0] - 0.08 * r, hl[1] + 0.12 * r)], True)],
                    PAPER, 0.9)
    c.save()                                                # the facets' hairlines
    c.set_source_rgb(*lerp(RED, INK, 0.6))
    c.set_line_width(1.6 / px)
    for q in outer:
        c.move_to(*q)
        c.line_to(p[0] + (q[0] - p[0]) * 0.56, p[1] + (q[1] - p[1]) * 0.56)
    c.stroke()
    c.restore()


def _hand_xf(t):
    """(origin, scale): the hand placed so the ruby lies at the frame's centre, the camera
    pushing in."""
    S = lerp(330.0, 362.0, ease("inout", clamp(t / T_ELEV)))
    bob = 3.0 * math.sin(2.0 * math.pi * K.twos(t) / 1.7)
    r = (RUBY_HU[0] * S, RUBY_HU[1] * S)
    ca, sa = math.cos(HAND_ROT), math.sin(HAND_ROT)
    return (X_C[0] - (r[0] * ca - r[1] * sa), X_C[1] - (r[0] * sa + r[1] * ca) + bob), S


def draw_glint(c, p, t):
    """The ruby's glint: an X of light along the frame's diagonals (the title's X, small)."""
    dt = t - T_PING
    if not -0.04 <= dt < 0.5:
        return
    g = ease("out3", clamp((dt + 0.04) / 0.1)) * (1.0 - ease("in", clamp((dt - 0.06) / 0.44)))
    for ang in (_DIAG, math.pi - _DIAG):
        L, w = 320.0 * g, 9.0 * g
        d = (math.cos(ang), math.sin(ang))
        n = (-d[1] * w, d[0] * w)
        bass.fill_polys(c, [bass.orient([(p[0] + d[0] * L, p[1] + d[1] * L), (p[0] + n[0], p[1] + n[1]),
                                         (p[0] - d[0] * L, p[1] - d[1] * L), (p[0] - n[0], p[1] - n[1])], True)],
                        PAPER)
    K.dot(c, p, 13.0 * g, PAPER, seed=1102)


def draw_palm(c, t):
    gz = lerp(1.0, 1.035, ease("inout", clamp(t / T_ELEV)))
    draw_street(c, t, gz)
    o, S = _hand_xf(t)
    parts = _hand_parts(t)
    sleeve, strap, button = _sleeve()
    curls = [_curl(t, f[4]) for f in _FINGERS]
    # the hand's shadow on the pavement, far below it (down and to the right of the lamp)
    c.save()
    c.translate(o[0] + 70.0, o[1] + 118.0)
    c.rotate(HAND_ROT)
    c.scale(S * 0.9, S * 0.9)
    bass.fill_polys(c, [sleeve] + [p for _, p, _ in parts], SHADOW)
    c.restore()
    c.save()
    c.translate(*o)
    c.rotate(HAND_ROT)
    c.scale(S, S)
    ca, sa = math.cos(-HAND_ROT), math.sin(-HAND_ROT)
    rim = ((-6.0 * ca + 6.0 * sa) / S, (-6.0 * sa - 6.0 * ca) / S)    # (-6, -6) frame px, in hand units
    # the rim: the glove and sleeve caught in paper, a little up and to the left (the lamp's side)
    c.save()
    c.translate(*rim)
    bass.fill_polys(c, [p for _, p, _ in parts] + [sleeve], PAPER)
    c.restore()
    for z, poly, col in parts + [(1.0, None, None)]:
        if poly is None or 0.07 < z:                         # the ruby, under whatever has curled over it
            if min(curls) < 0.93:
                K.pool(c, RUBY_HU, 0.5, 0.5, RED, 0.34, steps=3)
                _ruby(c, RUBY_HU, RUBY_R, math.radians(22.5 + 3.0 * math.sin(t * 1.3)),
                      flash=clamp(1.0 - abs(t - T_PING) / 0.18), px=S)
            curls = [1.0]
            if poly is None:
                break
        if z < 0.0:                                           # the glove's cuff, then her sleeve over it
            K.edged(c, [poly], col, INK, 6.0 / S)
            K.edged(c, [sleeve], SLEEVE, INK, 6.0 / S)
            bass.fill_polys(c, [strap], lerp(SLEEVE, STEEL, 0.3))
            bass.fill_polys(c, [draw.circle_pts(button, 0.064, n=16)], PAPER)
            bass.fill_polys(c, [draw.circle_pts(button, 0.048, n=16)], INK)
            continue
        K.edged(c, [poly], col, INK, 6.0 / S)
    c.restore()
    # the red between her fingers as they close on it, dying away by the cut
    g = clamp((t - T_FIST) / (FIST_DUR + 0.1))
    if 0.0 < g < 1.0:
        K.pool(c, X_C, 150.0, 150.0, RED, 0.16 * math.sin(math.pi * g), steps=3)
    ca, sa = math.cos(HAND_ROT), math.sin(HAND_ROT)
    hu = (RUBY_HU[0] - 0.3 * RUBY_R, RUBY_HU[1] - 0.26 * RUBY_R)          # the ruby's highlight
    draw_glint(c, (o[0] + S * (hu[0] * ca - hu[1] * sa), o[1] + S * (hu[0] * sa + hu[1] * ca)), t)


# ================================================================ 2.5-5: the title, the reverse of s01's
def _t0(w, i):
    """When letter i of word w's window snaps back to paper."""
    return T_SNAP + STAGGER * i + 0.06 * w


def _shrink(p, s):
    if s <= 0.02:
        return None
    cx = sum(x for x, _ in p) / len(p)
    cy = sum(y for _, y in p) / len(p)
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in p]


def letter_polys(w, i, t):
    """Letter i of word w at t: its window turned back into the letter where it is, then flown
    up to its place in the title: [polygon] (oriented, holes reversed), or None before its
    snap."""
    t0 = _t0(w, i)
    if t < t0:
        return None
    m = k(t, t0 + 0.04, MORPH, "inout")                     # window -> letter
    u = k(t, t0 + 0.04 + MORPH, FLY, "inout3")              # ... then the flight
    g = S01.glyphs(w)[i]
    at = S01.WORDS[w][1]
    centre, dh, outline = S01._dest_geom(S01.destinations()[w][i])
    s = lerp(dh / (g.bbox[3] - g.bbox[1]), 1.0, u)
    pw = (at[0] + g.pivot[0], at[1] + g.pivot[1])
    pos = (lerp(centre[0], pw[0], u), lerp(centre[1], pw[1], u))
    polys = [[(pos[0] + (x - g.pivot[0]) * s, pos[1] + (y - g.pivot[1]) * s) for x, y in cont] for cont in g.polys]
    outer = max(polys, key=lambda p: abs(bass.poly_area(p)))
    if m < 1.0:
        shape = bass.morph_outline(outer, outline, 1.0 - m, n=120)
        holes = [_shrink(p, clamp(m * 2.2 - 1.2)) for p in polys if p is not outer]
        return [bass.orient(shape, True)] + [bass.orient(h, False) for h in holes if h]
    return [bass.orient(outer, True)] + [bass.orient(p, False) for p in polys if p is not outer]


def letter_keys():
    """The windows the letters left from, in s01's order: [(w, i, ("ten"|"bank"|"clock", ...))]."""
    out = []
    for i, (n, j) in enumerate((n, j) for n in (5, 4) for j in range(3)):
        out.append((0, i, ("ten", n, j)))
    bank = [("bank", 3, 0), ("bank", 3, 1), "clock", ("bank", 3, 2), ("bank", 3, 3)]
    for i, key in enumerate(bank):
        out.append((1, i, key))
    return out


ELEV_LIT = {("ten", n, j): AMBER for n in (2, 3, 5) for j in range(3)}     # the street awake; the crew's dark


def draw_elev(c, t):
    """The street's elevation, the night the title left (the street awake now, his car gone, the
    side door open), its letters' windows snapping to paper and emptying as they fly; then the
    black slides over it."""
    win = dict(ELEV_LIT)
    clock = None
    for w, i, key in letter_keys():
        t0 = _t0(w, i)
        state = None if t < t0 else ("paper" if t < t0 + 0.04 else "gone")
        if key == "clock":
            clock = state
            continue
        if state == "paper":
            win[key] = PAPER
        elif state == "gone":
            win[key] = INK
    St.draw_elevation(c, t, city=True, sky_lit=0.35, windows=win, low=0.6, clock=CLOCK_END, side_door=1.0, lid_a=1.0,
                      lid_b=1.0)                              # both manholes open, as the night left them
    if clock is not None:                                     # the clock was CROSS's O
        bass.fill_polys(c, [draw.circle_pts(St.CLOCK_E, 25.0, n=48)], PAPER if clock == "paper" else INK)
    u = k(t, T_BLACK[0], T_BLACK[1], "linear")
    if u > 0.0:
        bass.bars(c, u, n=7, axis="h", colors=(INK,), frm="alt", mode="slide", overlap=0.55, seed=11, bleed=3.0)


def strip_poly(i, L=1350.0, w=None, off=0.0):
    """Strip i (0 paper, along the frame's diagonal; 1 red, across it) through the centre."""
    ang = _DIAG if i == 0 else math.pi - _DIAG
    d = (math.cos(ang), math.sin(ang))
    a = (C0[0] - d[0] * L + d[0] * off, C0[1] - d[1] * L + d[1] * off)
    b = (C0[0] + d[0] * L + d[0] * off, C0[1] + d[1] * L + d[1] * off)
    return S01._strip_poly(a, b, S01.STRIP_W if w is None else w, 70 + i)


def strip_off(i, t):
    """How far strip i still has to come along its axis (it slashes in, landing on its beat with a
    settle); None before it starts."""
    t0 = T_STRIPS[i]
    if t < t0 - STRIP_IN:
        return None
    return -(1.0 - ease("outback", clamp((t - (t0 - STRIP_IN)) / STRIP_IN))) * 2400.0


def draw_title_whole(c, t):
    """The title as it is now: the letters flying in, or landed; the paper strip over it."""
    if t < T_STAMP:
        for w, i, _ in letter_keys():
            polys = letter_polys(w, i, t)
            if polys:
                bass.fill_polys(c, polys, PAPER)
    else:
        for w in (0, 1):
            bass.draw_title(c, S01.glyphs(w), S01.WORDS[w][1], PAPER)
    off = strip_off(0, t)
    if off is not None:
        bass.fill_polys(c, [strip_poly(0, off=off)], PAPER)


def draw_title(c, t):
    """The title; from T_CUT, cut along the red strip, the halves sliding apart along it and away."""
    if t < T_CUT:
        draw_title_whole(c, t)
        return
    ang = math.pi - _DIAG
    d = (math.cos(ang), math.sin(ang))
    n = (-d[1], d[0])
    apart = 36.0 * k(t, T_CUT, 0.4, "out5") + 1600.0 * k(t, T_AWAY, 0.5, "in3")
    if apart > 1500.0:
        return
    for sg in (-1.0, 1.0):
        c.save()
        c.new_path()
        draw.poly(c, [(C0[0] - d[0] * 3000.0, C0[1] - d[1] * 3000.0), (C0[0] + d[0] * 3000.0, C0[1] + d[1] * 3000.0),
                      (C0[0] + d[0] * 3000.0 + n[0] * 3000.0 * sg, C0[1] + d[1] * 3000.0 + n[1] * 3000.0 * sg),
                      (C0[0] - d[0] * 3000.0 + n[0] * 3000.0 * sg, C0[1] - d[1] * 3000.0 + n[1] * 3000.0 * sg)])
        c.clip()
        c.translate(-d[0] * apart * sg, -d[1] * apart * sg)      # DOUBLE's half up and right, CROSS's down and left
        draw_title_whole(c, t)
        c.restore()


def draw_red(c, t):
    """The red strip: it slashes in across the paper one (T_STRIPS[1]); from T_DRAW_IN it draws in
    to the centre, narrowing, and is gone as the dot pops."""
    off = strip_off(1, t)
    if off is None:
        return
    e = k(t, T_DRAW_IN[0], T_DRAW_IN[1], "inout")
    if e >= 1.0:
        return
    bass.fill_polys(c, [strip_poly(1, L=lerp(1350.0, 30.0, e), w=S01.STRIP_W * lerp(1.0, 0.55, e), off=off)], RED)


def shake(t):
    dx = dy = 0.0
    for t0, amp in ((T_STAMP, 7.0), (T_CUT, 5.0)):
        if t >= t0:
            e = amp * math.exp(-14.0 * (t - t0))
            dx += e * math.sin(61.0 * (t - t0))
            dy += e * math.cos(47.0 * (t - t0))
    return dx, dy


# ================================================================ 5-8: the heart
def bump(t, t0, rise=0.06, fall=0.22):
    """0 .. 1 .. 0: a quick swell at t0 and its decay (a beat)."""
    if t < t0:
        return 0.0
    d = t - t0
    return d / rise if d < rise else math.exp(-3.0 * (d - rise) / fall)


def draw_heart(c, t):
    """The red dot at the centre: it pops, beats twice like a heart, the second softer, and
    shrinks away."""
    if t < T_POP:
        return
    r = lerp(28.0, 42.0, ease("outback", clamp((t - T_POP) / 0.14)))      # out of the drawn-in strip
    for tb, a in BEATS:
        r *= 1.0 + a * (0.26 * bump(t, tb) + 0.15 * bump(t, tb + 0.2))
        K.ripple(c, C0, t, tb, RED, n=1, life=0.95, r0=44.0, r1=330.0, width=9.0, seed=31, alpha=0.75 * a)
    r *= 1.0 - k(t, T_GONE[0], T_GONE[1], "in3")
    if r > 0.5:
        K.dot(c, C0, r, RED, seed=5)


# ================================================================ the scene
def render(f, t, T):
    K.scene_setup(f, NIGHT if t < T_BLACK[0] + T_BLACK[1] else INK)
    with f.screen() as c:
        if t < T_ELEV:
            draw_palm(c, t)
            return
        if t < T_BLACK[0] + T_BLACK[1]:
            draw_elev(c, t)
        else:
            K.fill(c, INK)
        dx, dy = shake(t)
        c.save()
        c.translate(dx, dy)
        draw_title(c, t)
        draw_red(c, t)
        c.restore()
        draw_heart(c, t)


def cues(T):
    out = [
        Cue(0.0, "night under the street lamp: the sirens far off and fading, a breath of wind", gain_db=-18, dur=2.5),
        Cue(T_OPEN[0], "her leather glove creaks as the fingers open", gain_db=-13, pan=0.1),
        Cue(0.75, "the ruby's red: a soft high string harmonic", gain_db=-16, dur=0.9),
        Cue(T_PING, "the ruby glints: the one celesta ping", gain_db=-7),
        Cue(T_FIST, "she closes her hand on it: the glove creaks", gain_db=-12, pan=0.1),
        Cue(T_ELEV, "the strings swell on a D major chord as the windows fly up", gain_db=-10, dur=T_STAMP - T_ELEV),
    ]
    out += [Cue(T_SNAP, "the windows lift out: a quick rising run of plucked notes", gain_db=-12, dur=0.3)]
    out += [Cue(T_STAMP, "the title stamps down: a deep paper thud", gain_db=-4),
            Cue(T_STRIPS[0], "the paper strip slashes in: a whoosh and a thud", gain_db=-6),
            Cue(T_STRIPS[1], "the red strip slashes across it: a whoosh and a thud", gain_db=-5),
            Cue(T_CUT, "the last chord: D major with the major seventh, held", gain_db=-3, dur=T_POP - T_CUT),
            Cue(T_AWAY, "the halves slide away: a paper swish", gain_db=-12),
            Cue(T_POP, "the red dot pops", gain_db=-10)]
    out += [Cue(tb, "a heartbeat: lub-dub", gain_db=-6 if a > 0.9 else -10) for tb, a in BEATS]
    out += [Cue(T_SILENCE, "silence", gain_db=-60)]
    return sorted(out, key=lambda q: q["t"])
