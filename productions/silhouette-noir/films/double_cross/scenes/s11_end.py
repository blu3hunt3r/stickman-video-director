"""s11 END (166-174). The X that closes s10 splits the frame open along its own strokes, the four
pieces flying apart, and in the gap, under a street lamp, is her gloved fist: X marks the spot. It
opens on the ruby, which glints (an X of light: the one celesta ping), and she closes her hand on
it. Dawn at the table: her hand brings the white queen in low and takes the red knight with it,
knocking him over; he rolls on the paper. The camera rises to the whole plan, straight down; the
chalk X lifts off the vault and grows into the title, the reverse of the opening (this time the
white strip crosses over the red); DOUBLE and CROSS slide back in, and the ruby lands as the red
dot at the crossing. Black, the dot a breath longer.
"""
import math
from functools import lru_cache

import cairo

from engine import bass, draw
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.double_cross import faces as F
from films.double_cross import kit as K
from films.double_cross import plan as P
from films.double_cross import shots as S
from films.double_cross.scenes import s01_title as S1
from films.double_cross.scenes import s09_plan_b as S9
from films.double_cross.scenes import s10_checkmate as S10

T_SPLIT = (0.0, 0.62)            # s10's last frame splits along its X; the four pieces fly apart
T_OPEN = (0.55, 1.3)             # her fist opens on the ruby, the index finger first
T_PING = 1.5                     # the ruby glints: an X of light (the one celesta ping)
T_FIST = 2.45                    # she closes her hand on it
FIST_DUR = 0.3
T_TABLE = 3.0                    # dawn at the table
T_IN = (3.0, 3.85)               # her hand brings the white queen in, low over the paper ...
T_HIT = 3.85                     # ... its base knocks the knight's (click) ...
T_TIP = 4.0                      # ... and he lands on his side: clack, roll
T_ROLL = (4.0, 4.5)
T_LET = 4.02                     # she lets go of the queen; her hand goes
T_RISE = (4.35, 5.5)             # the camera rises to the whole plan, straight down
T_GROW = (5.5, 6.0)              # the chalk X lifts off the vault and grows into the title X ...
T_TITLE = 6.0                    # ... landing on the last chord
T_DOUBLE = 6.2
T_CROSS = 6.45
T_DOT = 7.0                      # the ruby lands as the red dot at the crossing (the last chalk tap)
T_BLACK = 7.5                    # black; the dot a breath longer
T_DOT_OUT = (7.62, 7.9)

S10_LAST = S10.T_END - 1.0 / 24.0     # s10's last frame: the X
X_C = S10.X_CENTRE               # where the X crossed (frame px)
_DIAG = math.atan2(K.H, K.W)


def motion_blur(t, T):
    return 1


# ============================================================================ the split
@lru_cache(maxsize=1)
def _s10_last():
    """s10's last frame (the board under the X), drawn once."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(K.W), int(K.H))
    S10.board_shot(cairo.Context(surf), S10_LAST)
    surf.flush()
    return surf


# the frame's four triangles between the X's strokes: (corners, which way it flies, how far, spin)
_TRIS = (([(0.0, 0.0), (K.W, 0.0), X_C], (0.0, -1.0), 1150.0, -1.0),
         ([(K.W, 0.0), (K.W, K.H), X_C], (1.0, 0.0), 780.0, 1.0),
         ([(K.W, K.H), (0.0, K.H), X_C], (0.0, 1.0), 1150.0, -1.0),
         ([(0.0, K.H), (0.0, 0.0), X_C], (-1.0, 0.0), 780.0, 1.0))


def _split(c, t):
    """s10's last frame cut along its X: the four pieces crack apart, then fly off, each carrying
    half of the two strokes along its edges."""
    u = clamp((t - T_SPLIT[0]) / (T_SPLIT[1] - T_SPLIT[0]))
    if u >= 1.0:
        return
    surf = _s10_last()
    for tri, d, dist, spin in _TRIS:
        off = 26.0 * ease("out", clamp(u / 0.16)) + dist * ease("in3", u)
        cen = (sum(p[0] for p in tri) / 3.0, sum(p[1] for p in tri) / 3.0)
        c.save()
        c.translate(d[0] * off, d[1] * off)
        c.translate(*cen)
        c.rotate(math.radians(spin * 8.0 * ease("in", u)))
        c.translate(-cen[0], -cen[1])
        c.save()
        c.translate(12.0, 18.0)                           # its shadow on the picture under it
        bass.fill_polys(c, [tri], K.INK, 0.55)
        c.restore()
        c.new_path()
        draw.poly(c, tri)
        c.clip()
        c.set_source_surface(surf, 0.0, 0.0)
        c.paint()
        c.restore()


# ============================================================================ the street under the lamp
# Seen from straight above, like s10's board: the pavement she stands on, its kerb running along
# the red stroke's diagonal, the road beyond it in the top left, a puddle, the lamp's pool.
KERB_O = (200.0, 600.0)          # a point on the kerb's road edge (frame px at the shot's start)
KERB_ANG = math.atan2(-math.sin(_DIAG), math.cos(_DIAG))
FLAG = (236.0, 196.0)            # the paving slabs: along the kerb, across it
POOL_AT = (360.0, 700.0)         # the lamp's pool: the lamp stands at the kerb, up and to the left
PUDDLE_AT = (205.0, 1385.0)
ASPHALT = lerp(K.NAVY, K.INK, 0.4)
JOINT = lerp(K.NAVY, K.INK, 0.45)
SHADOW = lerp(K.NAVY, K.INK, 0.72)


def _kerb_pt(x, y):
    """The kerb's frame (x along it, y across it toward the pavement) to frame px."""
    ca, sa = math.cos(KERB_ANG), math.sin(KERB_ANG)
    return (KERB_O[0] + x * ca - y * sa, KERB_O[1] + x * sa + y * ca)


@lru_cache(maxsize=1)
def _pavement():
    """In the kerb's frame: the slabs [(shade, polygon)], the kerb stones, the slabs' far edges in
    frame px (for the wet sheen), the road's specks."""
    slabs, edges = [], []
    w, h = FLAG
    for r in range(9):
        y0 = 70.0 + r * h
        off = (r % 3) * w / 3.0
        for k in range(-7, 6):
            x0 = k * w + off
            slabs.append((int(hash01(r, k, 511) * 4.0),
                          bass.cut_rect(x0 + 4.0, y0 + 4.0, x0 + w - 4.0, y0 + h - 4.0, seed=r * 31 + k + 950, amp=2.0,
                                        seg=(40.0, 90.0))))
            edges.append((_kerb_pt(x0 + 24.0, y0 + 12.0), _kerb_pt(x0 + w - 40.0, y0 + 12.0)))
    kerb = [bass.cut_rect(k * 280.0 + 43.0, 4.0, k * 280.0 + 317.0, 66.0, seed=980 + k, amp=1.2) for k in range(-6, 5)]
    specks = [(-1400.0 + 2500.0 * hash01(i, 521), -600.0 + 585.0 * hash01(i, 522), 1.5 + 2.5 * hash01(i, 523))
              for i in range(170)]
    puddle = bass.orient(F.spline([(PUDDLE_AT[0] + (150.0 + 40.0 * hash01(i, 531)) * math.cos(2.0 * math.pi * i / 7.0),
                                    PUDDLE_AT[1] + (80.0 + 26.0 * hash01(i, 532)) * math.sin(2.0 * math.pi * i / 7.0))
                                   for i in range(7)], n=6), True)
    return slabs, kerb, edges, specks, puddle


def _street(c, t, gz):
    """The pavement, the kerb and the road from above, the lamp's gold pool on them, a few wet
    slabs and the puddle catching it (gz: the ground's zoom about the frame centre: it is far
    below the hand, so it moves less as the camera pushes in)."""
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
        bass.fill_polys(c, [draw.circle_pts((x, y), r, n=6)], lerp(K.NAVY, K.STEEL, 0.25))
    bass.fill_polys(c, [bass.cut_rect(-1500.0, -18.0, 1200.0, 2.0, seed=990, amp=1.0)], lerp(K.NAVY, K.INK, 0.7))
    bass.fill_polys(c, kerb, lerp(K.NAVY, K.STEEL, 0.55))
    bass.fill_polys(c, [bass.cut_rect(-1500.0, 70.0, 1200.0, 1900.0, seed=991, amp=1.0)], JOINT)
    for b in range(4):
        bass.fill_polys(c, [p for k, p in slabs if k == b], lerp(K.NAVY, K.STEEL, 0.2 + 0.06 * b))
    bass.line_band(c, [(-1500.0, 6.0), (1200.0, 6.0)], K.PAPER, width=3.0, seed=992, alpha=0.3)
    c.restore()
    bass.fill_polys(c, [puddle], lerp(K.NAVY, K.INK, 0.62))
    K.pool(c, POOL_AT, 720.0, 660.0, K.GOLD, 0.15, steps=4)
    for i, (a, b) in enumerate(edges):                        # wet slabs catching the lamp
        d = math.dist(a, POOL_AT)
        if d < 600.0 and hash01(i, 505) < 0.45:
            bass.line_band(c, [a, b], K.GOLD, width=4.0, seed=i, alpha=0.32 * (1.0 - d / 600.0))
    # the lamp in the puddle: a gold smear, white at its heart
    K.pool(c, (PUDDLE_AT[0] + 30.0, PUDDLE_AT[1] - 14.0), 70.0, 26.0, K.GOLD, 0.55, steps=3)
    K.pool(c, (PUDDLE_AT[0] + 30.0, PUDDLE_AT[1] - 14.0), 24.0, 9.0, K.PAPER, 0.5, steps=2)
    c.restore()


# ============================================================================ her hand, palm up
# Hand units: the palm about 1 wide, the wrist at +y, the fingers along -y. Her right hand, palm up
# under the lamp, seen from above (the thumb on the right), turned a little so the forearm comes
# in from the bottom right.
HAND_ROT = math.radians(-12.0)
_PALM = ((-0.40, 0.66), (-0.48, 0.30), (-0.53, -0.10), (-0.50, -0.44), (-0.40, -0.58), (-0.16, -0.66),
         (0.12, -0.68), (0.36, -0.63), (0.50, -0.50), (0.52, -0.22), (0.60, 0.04), (0.62, 0.30), (0.52, 0.52),
         (0.40, 0.66))
# (base, direction when straight (deg; -90 is up the frame), segment lengths, width, delay as the
# hand opens: the index first)
_FINGERS = (((0.33, -0.60), -83.0, (0.40, 0.25, 0.21), 0.215, 0.0),
            ((0.10, -0.65), -91.0, (0.44, 0.28, 0.22), 0.225, 0.08),
            ((-0.14, -0.62), -99.0, (0.40, 0.26, 0.21), 0.215, 0.16),
            ((-0.36, -0.53), -108.0, (0.32, 0.20, 0.18), 0.19, 0.24))
_FLEX = (88.0, 98.0, 72.0)       # each joint's bend in the fist
_THUMB = ((0.50, 0.04), (-36.0, -160.0), (0.36, 0.30), 0.25)     # base, direction (open, shut), lengths, width
_CUFF = ((-0.44, 0.56), (0.44, 0.56), (0.50, 0.92), (-0.50, 0.92))
RUBY_HU = (-0.02, -0.32)         # where the ruby lies: in the hollow below the fingers
RUBY_R = 0.2
SLEEVE = F.HANDS["architect"]["sleeve"]
GLOVE = lerp(lerp(K.INK, K.PAPER, 0.06), K.GOLD, 0.11)   # black leather in the lamp's warm light
_ARM = (0.3, 1.0)                # the forearm's way (hand units), toward her


@lru_cache(maxsize=1)
def _palm_poly():
    return bass.orient(F.spline(_PALM, n=5), True)


def _curl(t, delay):
    """How closed a finger is (1: in the fist): it opens from T_OPEN[0] + delay, and closes on the
    ruby at T_FIST (the little finger last)."""
    o = ease("inout", clamp((t - T_OPEN[0] - delay) / (T_OPEN[1] - T_OPEN[0] - 0.3)))
    k = ease("inout", clamp((t - T_FIST - 0.3 * delay) / FIST_DUR))
    return max(1.0 - o, k)


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
    parts = [(-0.2, bass.orient(list(_CUFF), True), lerp(K.INK, K.GOLD, 0.05)),
             (0.0, _palm_poly(), GLOVE)]
    segs = []
    for base, dirn, lens, w, delay in _FINGERS:
        segs += _finger(base, dirn, lens, w, _curl(t, delay))
    segs += _thumb(_curl(t, 0.1))
    for a, b, ra, rb, z, lit in segs:
        parts.append((z + 0.001, bass.capsule_pts(a, b, ra, rb, cap=4), lerp(K.INK, GLOVE, 0.4 + 0.75 * lit)))
    parts.sort(key=lambda it: it[0])
    return parts


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


def _ruby(c, p, r, rot=0.0, flash=0.0, px=1.0, edge=None):
    """The ruby from above: a cut octagon, its crown facets lit from the top left, the table in the
    middle. px: frame px per unit here (for the hairlines). edge: an outline colour."""
    n = 8
    outer = [(p[0] + r * math.cos(rot + 2.0 * math.pi * i / n), p[1] + r * math.sin(rot + 2.0 * math.pi * i / n))
             for i in range(n)]
    inner = [(p[0] + 0.56 * r * math.cos(rot + 2.0 * math.pi * i / n),
              p[1] + 0.56 * r * math.sin(rot + 2.0 * math.pi * i / n)) for i in range(n)]
    if edge is not None:
        K.edged(c, [bass.orient(outer, True)], K.RED, edge, 7.0 / px)
    light = math.radians(-135.0)
    for i in range(n):
        j = (i + 1) % n
        mid = rot + 2.0 * math.pi * (i + 0.5) / n
        b = 0.5 + 0.5 * math.cos(mid - light)
        col = lerp(lerp(K.RED, K.INK, 0.55), lerp(K.RED, K.PAPER, 0.4), b)
        bass.fill_polys(c, [bass.orient([outer[i], outer[j], inner[j], inner[i]], True)], col)
    bass.fill_polys(c, [bass.orient(inner, True)], lerp(K.RED, K.PAPER, 0.1 + 0.55 * flash))
    hl = (p[0] - 0.3 * r, p[1] - 0.26 * r)
    bass.fill_polys(c, [bass.orient([(hl[0] - 0.16 * r, hl[1] + 0.04 * r), (hl[0] + 0.02 * r, hl[1] - 0.14 * r),
                                     (hl[0] + 0.1 * r, hl[1] - 0.06 * r), (hl[0] - 0.08 * r, hl[1] + 0.12 * r)], True)],
                    K.PAPER, 0.9)
    c.save()                                                # the facets' hairlines
    c.set_source_rgb(*lerp(K.RED, K.INK, 0.6))
    c.set_line_width(1.6 / px)
    for q in outer:
        c.move_to(*q)
        c.line_to(p[0] + (q[0] - p[0]) * 0.56, p[1] + (q[1] - p[1]) * 0.56)
    c.stroke()
    c.restore()


def _hand_xf(t):
    """(origin, scale): the hand placed so the ruby lies where the X crossed, the camera pushing in."""
    S = lerp(330.0, 362.0, ease("inout", clamp(t / T_TABLE)))
    bob = 3.0 * math.sin(2.0 * math.pi * K.twos(t) / 1.7)
    r = (RUBY_HU[0] * S, RUBY_HU[1] * S)
    ca, sa = math.cos(HAND_ROT), math.sin(HAND_ROT)
    return (X_C[0] - (r[0] * ca - r[1] * sa), X_C[1] - (r[0] * sa + r[1] * ca) + bob), S


def _glint(c, p, t):
    """The ruby's glint: an X of light along the frame's diagonals (the title's X, small)."""
    k = t - T_PING
    if not -0.04 <= k < 0.5:
        return 0.0
    g = ease("out3", clamp((k + 0.04) / 0.1)) * (1.0 - ease("in", clamp((k - 0.06) / 0.44)))
    for ang in (_DIAG, math.pi - _DIAG):
        L, w = 250.0 * g, 9.0 * g
        d = (math.cos(ang), math.sin(ang))
        n = (-d[1] * w, d[0] * w)
        bass.fill_polys(c, [bass.orient([(p[0] + d[0] * L, p[1] + d[1] * L), (p[0] + n[0], p[1] + n[1]),
                                         (p[0] - d[0] * L, p[1] - d[1] * L), (p[0] - n[0], p[1] - n[1])], True)],
                        K.PAPER)
    K.dot(c, p, 13.0 * g, K.PAPER, seed=1102)
    return g


def palm_shot(c, t):
    gz = lerp(1.0, 1.035, ease("inout", clamp(t / T_TABLE)))
    _street(c, t, gz)
    o, S = _hand_xf(t)
    parts = _hand_parts(t)
    sleeve, strap, button = _sleeve()
    curls = [_curl(t, f[4]) for f in _FINGERS]
    # the hand's shadow on the street, far below it (down and to the right of the lamp)
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
    # the rim: the glove and sleeve in chalk, a little up and to the left (the lamp's side)
    c.save()
    c.translate(*rim)
    bass.fill_polys(c, [p for _, p, _ in parts] + [sleeve], K.PAPER)
    c.restore()
    for z, poly, col in parts + [(1.0, None, None)]:
        if poly is None or 0.07 < z:                         # the ruby, under whatever has curled over it
            if min(curls) < 0.93:
                K.pool(c, RUBY_HU, 0.5, 0.5, K.RED, 0.34, steps=3)
                _ruby(c, RUBY_HU, RUBY_R, math.radians(22.5 + 3.0 * math.sin(t * 1.3)),
                      flash=clamp(1.0 - abs(t - T_PING) / 0.18), px=S)
            curls = [1.0]
            if poly is None:
                break
        if z < 0.0:                                           # the glove's cuff, then her sleeve over it
            K.edged(c, [poly], col, K.INK, 6.0 / S)
            K.edged(c, [sleeve], SLEEVE, K.INK, 6.0 / S)
            bass.fill_polys(c, [strap], lerp(SLEEVE, K.STEEL, 0.3))
            bass.fill_polys(c, [draw.circle_pts(button, 0.064, n=16)], K.PAPER)
            bass.fill_polys(c, [draw.circle_pts(button, 0.048, n=16)], K.INK)
            continue
        K.edged(c, [poly], col, K.INK, 6.0 / S)
    c.restore()
    # light between the fingers as they close on it, dying away
    k = clamp((t - T_FIST) / (FIST_DUR + 0.35))
    if 0.0 < k < 1.0:
        K.pool(c, X_C, 150.0, 150.0, K.RED, 0.16 * math.sin(math.pi * k), steps=3)
    ca, sa = math.cos(HAND_ROT), math.sin(HAND_ROT)
    hu = (RUBY_HU[0] - 0.3 * RUBY_R, RUBY_HU[1] - 0.26 * RUBY_R)          # the ruby's highlight
    _glint(c, (o[0] + S * (hu[0] * ca - hu[1] * sa), o[1] + S * (hu[0] * sa + hu[1] * ca)), t)


# ============================================================================ the table, at dawn
KNIGHT_AT = P.PIECES_A[3][1]              # his piece, where he set it by the car in s03 (inside the ring)
HIT_AT = (KNIGHT_AT[0] - 64.0, KNIGHT_AT[1])   # where the queen's base meets his
QUEEN_FROM = (KNIGHT_AT[0] - 420.0, KNIGHT_AT[1] + 40.0)
BISHOP_AT = (P.MANHOLE_B[0] - 56.0, P.MANHOLE_B[1])
PIECE_H = 100.0
WINDOW = (-1400.0, -900.0)                # the dawn window, far off the sheet's top left: shadows fall away
CAM_T0 = P.PlanCam(KNIGHT_AT[0] + 20.0, KNIGHT_AT[1] - 150.0, 3.0, 30.0, -8.0)
CAM_T1 = P.PlanCam(KNIGHT_AT[0] + 40.0, KNIGHT_AT[1] - 140.0, 3.25, 30.0, -8.0)
CAM_TOP = S1.CAM1                         # the whole sheet, straight down: where the opening's X landed
S9_DONE = 12.0                            # s09 time by which Plan B is all drawn


def table_cam(t):
    cam = P.PlanCam.lerp(CAM_T0, CAM_T1, ease("out", clamp((t - T_TABLE) / (T_RISE[0] - T_TABLE))))
    cam = P.PlanCam.lerp(cam, CAM_TOP, ease("inout3", clamp((t - T_RISE[0]) / (T_RISE[1] - T_RISE[0]))))
    if T_TIP <= t < T_TIP + 0.25:                           # the clack jolts the table
        a = (1.0 - (t - T_TIP) / 0.25) ** 2
        cam = P.PlanCam(cam.cx + 3.0 * a * math.sin(t * 90.0), cam.cy + 4.0 * a * math.sin(t * 77.0), cam.zoom,
                        cam.phi, cam.yaw)
    return cam


def queen_at(t):
    """The queen's plan point and lift: carried in low from the west, knocking his base at T_HIT
    and pushing on onto his square, set down at T_TIP."""
    if t < T_HIT:
        u = ease("inout", clamp((t - T_IN[0]) / (T_IN[1] - T_IN[0])))
        p = (lerp(QUEEN_FROM[0], HIT_AT[0], u), lerp(QUEEN_FROM[1], HIT_AT[1], u))
        return p, lerp(150.0, 14.0, ease("out", clamp((t - T_IN[0]) / 0.7)))
    u = ease("out", clamp((t - T_HIT) / (T_TIP - T_HIT)))
    return (lerp(HIT_AT[0], KNIGHT_AT[0], u), KNIGHT_AT[1]), 14.0 * (1.0 - u)


def knight_state(t):
    """(phase, base, v): standing; tipping over to the east (v: the tilt), pushed at the base; then
    on his side (v: the roll, 0..1), rolling a little further and lying down flat."""
    if t < T_HIT:
        return "stand", KNIGHT_AT, 0.0
    if t < T_TIP:
        u = (t - T_HIT) / (T_TIP - T_HIT)
        return "tip", (KNIGHT_AT[0] + 30.0 * u, KNIGHT_AT[1]), 90.0 * ease("in", u)
    u = clamp((t - T_ROLL[0]) / (T_ROLL[1] - T_ROLL[0]))
    e = ease("out3", u)
    return "lie", (KNIGHT_AT[0] + 30.0 + 22.0 * e, KNIGHT_AT[1] + 5.0 * e), u


@lru_cache(maxsize=1)
def _knight_pts():
    return list(K._piece_poly("knight", 0))


def _lying_knight(c, cam, base, roll):
    """The knight on his side, fallen east: at roll 0 just as K.piece draws him tipped 90 degrees;
    as he rolls (a rock, then still) his profile lies down on the paper, squashed by the view."""
    v = cam.to_view(base)
    st = max(cam.stand(), cam.flat())
    s = PIECE_H * cam.zoom * st / 112.0
    e = ease("out", roll)
    k = lerp(1.0, lerp(1.0, cam.flat(), 0.5), e)          # lying down (but still reading as a knight)
    piv = 30.0 * s
    rock = math.radians(7.0 * math.sin(roll * 3.0 * math.pi) * (1.0 - roll))
    # his shadow on the paper
    bass.fill_polys(c, [draw.ellipse_pts((v[0] + piv + 54.0 * s, v[1] + 4.0 * s), 62.0 * s, 12.0 * s * cam.flat() + 2.0,
                                         n=32)], K.INK, 0.38)
    pts = [(v[0] + piv - s * py, v[1] - piv * k - s * px * k) for px, py in _knight_pts()]
    c.save()
    c.translate(v[0] + piv, v[1])
    c.rotate(rock)
    c.translate(-v[0] - piv, -v[1])
    K.edged(c, [bass.orient(pts, True)], K.RED, K.INK, 5.0)
    c.restore()


def _hand(c, cam, t):
    """Her gloved hand carrying the queen in (from the left, low), letting go and leaving."""
    if not T_IN[0] <= t < T_LET + 0.62:
        return
    p, lift = queen_at(t)
    v = cam.to_view(p)
    crown = (v[0], v[1] - (lift + PIECE_H * 0.96) * cam.zoom * cam.stand())
    wrist = (crown[0] - 980.0, crown[1] + 420.0)
    open_u = clamp((t - T_LET) / 0.16)
    leave = ease("in3", clamp((t - T_LET - 0.1) / 0.5))
    if leave > 0.0:
        crown = (crown[0] + (wrist[0] - crown[0]) * leave * 0.7, crown[1] - 340.0 * leave)
    F.hand(c, "architect", wrist, crown, 0.65 * cam.zoom * cam.stand(), open_u=open_u)


def _on_plan(t):
    def fn(c):
        P.draw_plan_a(c, x=t < T_GROW[0])
        S9._plan_b(c, S9_DONE + t)                          # her tracing sheet, Plan B all drawn on it
        K.marker_ring(c, P.CAR, 160.0, 126.0, 1.0, K.RED, width=9.0, seed=1105)    # his checkmate, in red
        K.pool(c, (100.0, 300.0), 1500.0, 1350.0, K.STEEL, 0.14, steps=4)        # the dawn, cold, from the window
    return fn


def table_shot(c, t):
    cam = table_cam(t)
    K.fill(c, K.DEEP)
    P.table(c, cam, 0.3, 1.0, 0.0, on_plan=_on_plan(t))
    qp, ql = queen_at(t)
    phase, kb, kv = knight_state(t)
    items = [("queen", qp, K.PAPER, K.INK, 1, ql), ("knight", kb, K.RED, K.INK, -1, 0.0)]
    if t < T_GROW[0] + 0.15:                                # (under the title they would sit on DOUBLE)
        items += [("pawn", P.GUARD_POST, K.INK, K.PAPER, 1, 0.0), ("bishop", BISHOP_AT, K.GOLD, K.INK, -1, 0.0)]
    for kind, p, col, edge, fc, lift in sorted(items, key=lambda it: cam.depth(it[1])):
        if kind == "knight" and phase == "lie":
            _lying_knight(c, cam, p, kv)
        elif kind == "knight":
            P.piece_on(c, cam, kind, p, PIECE_H, col, edge, facing=fc, tilt=kv, light=WINDOW,
                       shadow=0.38 * (1.0 - kv / 90.0))
        else:
            P.piece_on(c, cam, kind, p, PIECE_H, col, edge, facing=fc, lift=lift, light=WINDOW)
    _hand(c, cam, t)
    if T_TIP <= t < T_TIP + 0.5:                            # the clack: chalk dust off the paper
        v = cam.to_view((KNIGHT_AT[0] + 80.0, KNIGHT_AT[1]))
        g = (t - T_TIP) / 0.5
        for i in range(7):
            a = math.radians(-170.0 + 160.0 * i / 6.0)
            d = (30.0 + 120.0 * ease("out3", g)) * cam.zoom / 2.0
            K.dot(c, (v[0] + d * math.cos(a) * 1.5, v[1] + d * math.sin(a) * 0.5), 5.0 * (1.0 - g), K.PAPER,
                  seed=1110 + i, alpha=0.7)


# ============================================================================ the title
def _strips(t, cam):
    """The title strips growing out of the plan's chalk X (s01's landing, run backwards):
    [(a, b, width, colour)], the red one first and the white one over it: she crossed him last."""
    u = clamp((t - T_GROW[0]) / (T_GROW[1] - T_GROW[0]))
    e = ease("in", u)                                       # lifting off slowly, then flying at us ...
    if t > T_GROW[1]:                                       # ... to land on the chord, and settle
        k = t - T_GROW[1]
        e = 1.0 + 0.035 * math.exp(-k * 12.0) * math.sin(k * 34.0)
    h = 28.0
    xv = P.X_VAULT
    targets = ((cam.to_view((xv[0] - h, xv[1] - h)), cam.to_view((xv[0] + h, xv[1] + h))),
               (cam.to_view((xv[0] + h, xv[1] - h)), cam.to_view((xv[0] - h, xv[1] + h))))
    out = []
    for i in (1, 0):
        ang = _DIAG if i == 0 else math.pi - _DIAG
        d = (math.cos(ang), math.sin(ang))
        L = 1350.0
        a = (S1.C0[0] - d[0] * L, S1.C0[1] - d[1] * L)
        b = (S1.C0[0] + d[0] * L, S1.C0[1] + d[1] * L)
        ta, tb = targets[i]
        a = (lerp(ta[0], a[0], e), lerp(ta[1], a[1], e))
        b = (lerp(tb[0], b[0], e), lerp(tb[1], b[1], e))
        col = K.PAPER if i == 0 else lerp(K.PAPER, K.RED, clamp(u / 0.35))
        out.append((a, b, lerp(10.0 * cam.zoom, S1.STRIP_W, e), col, 60 + i))
    return out


def _words(c, t):
    """DOUBLE and CROSS slide back in (from the top and the bottom) where the opening's flew out."""
    for word, t0, y, frm in (("DOUBLE", T_DOUBLE, 286.0, "top"), ("CROSS", T_CROSS, 1648.0, "bottom")):
        u = clamp((t - t0) / 0.42)
        if u <= 0.0:
            continue
        g = bass.title_glyphs(word, width=530.0 if word == "DOUBLE" else 490.0, tracking=0.06, seed=7, rough=0.8,
                              jitter=0.6)
        bass.draw_title(c, g, (540.0, y), K.PAPER, u=u, anim="slide", frm=frm, order="center", overlap=0.6,
                        dist=900.0, ease="out3")


def _dot(c, t):
    """The ruby, landed as the red dot where the strokes cross."""
    g = ease("outback", clamp((t - T_DOT) / 0.2))
    g *= 1.0 - ease("in3", clamp((t - T_DOT_OUT[0]) / (T_DOT_OUT[1] - T_DOT_OUT[0])))
    if g > 0.01:
        _ruby(c, X_C, 46.0 * g, math.radians(22.5), edge=K.INK)
    if T_DOT <= t < T_BLACK:
        K.ripple(c, X_C, t, T_DOT + 0.08, K.RED, n=1, life=0.5, r0=44.0, r1=130.0, width=5.0)


def title(c, t):
    cam = table_cam(t)
    K.fill(c, K.NAVY, alpha=0.62 * ease("inout", clamp((t - T_GROW[0]) / 0.3)))
    for a, b, w, col, seed in _strips(t, cam):
        bass.fill_polys(c, [S1._strip_poly(a, b, w, seed)], col)
    _words(c, t)


# ============================================================================ render
def _hit_frame(t):
    """The knight's middle as he goes over (frame px): the lens rides his fall east, the queen's
    base at the edge of it."""
    phase, kb, v = knight_state(t)
    a = math.radians({"stand": 0.0, "tip": v, "lie": 90.0}[phase])
    h = 0.42 * PIECE_H
    return table_cam(t).to_view((kb[0] + h * math.sin(a), kb[1]), h * math.cos(a))


INSERTS = (S.Punch(T_HIT, 5, _hit_frame, 3.0, seed=111, accent=K.RED),)  # she takes him, close


def render(f, t, T):
    S.play(f, t, T, render_plain, INSERTS)


def render_plain(f, t, T):
    if t < T_TABLE:
        K.scene_setup(f, K.NAVY)
        with f.screen() as c:
            palm_shot(c, t)
            _split(c, t)
        return
    K.scene_setup(f, K.DEEP)
    with f.screen() as c:
        if t < T_BLACK:
            table_shot(c, t)
            if t >= T_GROW[0]:
                title(c, t)
        else:
            K.fill(c, K.INK)
        _dot(c, t)


def cues(T):
    return [
        Cue(T_SPLIT[0], "whoosh: the frame splits open along the X (a paper rip) and the four pieces fly apart; "
                        "the sirens cut off", gain_db=-8, dur=T_SPLIT[1] - T_SPLIT[0]),
        Cue(0.3, "a night street under a lamp: a low electric hum, a far drip", gain_db=-24, dur=T_TABLE - 0.3),
        Cue(T_OPEN[0], "leather creak: her gloved fingers open, one after another", gain_db=-18,
            dur=T_OPEN[1] - T_OPEN[0]),
        Cue(T_PING, "the ruby glints: one celesta ping", gain_db=-10),
        Cue(T_FIST, "her fist closes on it: the glove creaks tight", gain_db=-14, dur=FIST_DUR),
        Cue(T_TABLE, "dawn at the table: quiet room tone, a bird far off", gain_db=-24, dur=T_RISE[0] - T_TABLE),
        Cue(T_IN[0] + 0.2, "cloth rustle: her sleeve brushes the paper as the queen comes in low", gain_db=-22,
            pan=-0.3,
            dur=T_IN[1] - T_IN[0] - 0.2),
        Cue(T_HIT, "click: the queen's base knocks the knight's", gain_db=-12, pan=0.1),
        Cue(T_TIP, "she tips the knight over: clack, roll (he rolls on the paper)", gain_db=-8, pan=0.2,
            dur=T_ROLL[1] - T_ROLL[0]),
        Cue(T_RISE[0], "whoosh, soft and airy: the camera rises off the table", gain_db=-24,
            dur=T_RISE[1] - T_RISE[0]),
        Cue(T_GROW[0], "whoosh: the chalk X lifts off the vault and grows into the title", gain_db=-12,
            dur=T_GROW[1] - T_GROW[0]),
        Cue(T_TITLE, "the title X lands: the last chord", gain_db=-10),
        Cue(T_DOUBLE, "paper whoosh: DOUBLE slides back in from the top", gain_db=-16),
        Cue(T_CROSS, "paper whoosh: CROSS slides back in from the bottom", gain_db=-16),
        Cue(T_DOT, "chalk tap: the red dot lands at the crossing (the film's last tap)", gain_db=-10),
        Cue(T_BLACK, "black", gain_db=-20),
    ]
