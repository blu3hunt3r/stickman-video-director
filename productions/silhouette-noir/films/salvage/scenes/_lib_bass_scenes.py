"""SALVAGE: shared Saul Bass cut-paper pieces for s04 (CALM NIGHT) and s07 (THE PRICE).

Both scenes keep the default camera, so world = screen px (1080x1920). Fields are flat Bass
print tones of the film: ink, deep teal, mid teal, PAPER, and RED where the bible allows it
(flashback graphics). Every shape is cut once (cached) and only moved per frame, so the
scissor edges never boil.

    MERIDIAN: meridian_polys(), lifeboat_polys(), draw_meridian(ctx, (x, y), length, ...)
    banknote_polys(), fist_polys(): the hand holding the fan of notes (s07)
    storm_polys(), rock_polys(): the storm that wasn't and the reef that wasn't (s04)
"""
import math
from functools import lru_cache

from engine import bass
from engine.core import W, H, clamp, ease, hash01
from engine.palette import PAPER, SALVAGE

INK = SALVAGE.ink
TEAL = SALVAGE.mid                       # (0.07, 0.25, 0.29) the Bass print mid tone
DEEP = SALVAGE.fog_at(0.0)               # (0.03, 0.10, 0.12) near water: "black water"
SEA_HI = (0.052, 0.180, 0.212)           # sea bands between TEAL and DEEP (flat steps)
SEA_LO = (0.020, 0.068, 0.084)
FIBER = (0.97, 0.955, 0.92)              # the white core of torn paper
_D2R = math.pi / 180.0


# ----------------------------------------------------------------------------- timing
def k(t, t0, dur, e="out3"):
    """Eased progress 0..1 of a move that starts at t0 and lasts dur seconds."""
    if t <= t0:
        return 0.0                      # exact zero (outback leaves ~1e-16 at x = 0)
    if dur <= 0 or t >= t0 + dur:
        return 1.0
    return ease(e, (t - t0) / dur)


def sn(*a):
    return hash01(*a) * 2.0 - 1.0


def put(ctx, polys, color, at=(0.0, 0.0), rot=0.0, scale=1.0, sy=None, alpha=1.0, pivot=(0.0, 0.0)):
    """Fill cached local polygons moved to `at` (rotated/scaled about local `pivot`)."""
    ctx.save()
    ctx.translate(at[0], at[1])
    if rot:
        ctx.rotate(rot * _D2R)
    ctx.scale(scale, scale if sy is None else sy)
    ctx.translate(-pivot[0], -pivot[1])
    bass.fill_polys(ctx, polys, color, alpha)
    ctx.restore()


# ----------------------------------------------------------------------------- the MERIDIAN
# A 1920s steamer in profile, bow to the right, cut at a nominal length of 700 px.
# Local units: origin on the waterline at midships, y up = negative.
_L0 = 700.0
_HULL = [(-352, -56), (-360, -44), (-357, -28), (-345, -12), (-330, 0), (-316, 14), (-290, 32),
         (-252, 44), (296, 44), (330, 32), (352, 12), (362, 0), (371, -30), (379, -68), (334, -66),
         (318, -65), (312, -54), (180, -47), (0, -45), (-200, -47), (-252, -50), (-262, -60), (-300, -60)]
_HOUSE = [(-150, -44), (112, -44), (112, -86), (-150, -86)]
_UPPER = [(-124, -84), (64, -84), (64, -112), (-124, -112)]
_BRIDGE = [(36, -108), (122, -108), (122, -114), (132, -114), (132, -120), (118, -120), (118, -140),
           (44, -140), (44, -120), (24, -120), (24, -114), (36, -114)]
_POOP_HOUSE = [(-300, -58), (-232, -58), (-232, -78), (-300, -78)]


def _funnel(x0, x1, base, top, rake):
    return [(x0, base), (x1, base), (x1 + rake, top + 3), (x1 + rake + 2, top), (x0 + rake - 2, top),
            (x0 + rake, top + 3)]


def _bar(a, b, w):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    return [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]


def _raw_parts():
    parts = [_HULL, _HOUSE, _UPPER, _BRIDGE, _POOP_HOUSE,
             _funnel(-42, -6, -110, -206, -16), _funnel(-112, -76, -110, -200, -16),
             _bar((236, -64), (228, -262), 6.0), _bar((214, -232), (246, -232), 4.0),      # foremast
             _bar((-228, -58), (-236, -250), 6.0), _bar((-252, -222), (-220, -222), 4.0),  # mainmast
             _bar((230, -250), (376, -70), 2.4), _bar((-234, -240), (-352, -60), 2.4),     # stays
             _bar((-6, -204), (226, -254), 2.0), _bar((-112, -198), (-230, -244), 2.0),    # aerial
             _bar((236, -150), (300, -70), 3.0), _bar((-228, -150), (-292, -64), 3.0),     # derricks
             _bar((60, -112), (58, -128), 7.0), _bar((-150, -86), (-152, -100), 7.0)]      # cowls
    return parts


@lru_cache(maxsize=8)
def meridian_polys(seed=0):
    """The Meridian's cut-paper parts (local units, nominal length 700)."""
    out = []
    for q, p in enumerate(_raw_parts()):
        if len(p) <= 4 and max(abs(p[0][0] - p[2][0]), abs(p[0][1] - p[2][1])) < 30 and q >= 7:
            out.append(bass.orient(p, True))          # thin spars: crisp, uncut
        else:
            out.append(bass.orient(bass.cut(p, seed=seed * 53 + q, amp=1.1, seg=(18.0, 48.0)), True))
    return out


#: the 8 lifeboats hang along the boat deck, in front of the deckhouse
BOAT_X = (-139.0, -107.0, -75.0, -43.0, -11.0, 21.0, 53.0, 85.0)
BOAT_Y = -92.0


@lru_cache(maxsize=8)
def lifeboat_polys(seed=0):
    """Eight small lifeboats, each [poly] centered on (0, 0) in local units."""
    out = []
    for i in range(8):
        hull = [(-13.0, -4.0), (13.0, -4.0), (11.5, 0.5), (7.0, 4.2), (-7.0, 4.2), (-11.5, 0.5)]
        out.append([bass.orient(bass.cut(hull, seed=seed * 17 + i, amp=0.35, seg=(5.0, 12.0)), True)])
    return out


def draw_meridian(ctx, at, length, color, rot=0.0, boats=None, boat_color=PAPER, seed=0, alpha=1.0):
    """The ship with its waterline midpoint at `at`; boats: 8 pop values 0..1 (None = none)."""
    s = length / _L0
    put(ctx, meridian_polys(seed), color, at, rot, s, alpha=alpha)
    if boats is None:
        return
    bp = lifeboat_polys(seed)
    ca, sa = math.cos(rot * _D2R), math.sin(rot * _D2R)
    for i, p in enumerate(boats):
        if p <= 0:
            continue
        lx, ly = BOAT_X[i] * s, BOAT_Y * s
        x, y = at[0] + lx * ca - ly * sa, at[1] + lx * sa + ly * ca
        put(ctx, bp[i], boat_color, (x, y), rot, s * p, alpha=alpha)


# ----------------------------------------------------------------------------- storm + reef (s04)
@lru_cache(maxsize=4)
def storm_polys(seed=0, tear_x=560.0):
    """(cloud, tear): the storm cloud spanning the top of the frame (jagged lower edge
    around y 430..640) and a jagged vertical tear line through it at x ~ tear_x (top to
    bottom). Draw each half clipped by tear_region()."""
    bottom = []
    x, i = W + 80.0, 0
    while x > -80:
        y = 455.0 + 60.0 * math.sin(x / 160.0 + 0.6) + 40.0 * sn(seed, i, 1)
        bottom.append((x, y))
        if i % 2 == 1:                                   # jagged teeth hanging down
            bottom.append((x - 16.0, y + 50.0 + 70.0 * hash01(seed, i, 3)))
        x -= 46.0 + 52.0 * hash01(seed, i, 2)
        i += 1
    bottom.append((-80.0, 470.0))
    cloud = [(-80.0, -120.0), (W + 80.0, -120.0)] + bottom
    cloud = bass.orient(bass.cut(cloud, seed=seed * 7 + 1, amp=1.5, seg=(24.0, 60.0)), True)
    tear = []
    y = -140.0
    j = 0
    while y < 760:
        tear.append((tear_x + 24.0 * sn(seed, j, 4) + 10.0 * math.sin(y / 37.0), y))
        y += 22.0 + 26.0 * hash01(seed, j, 5)
        j += 1
    return cloud, tear


def tear_region(tear, left):
    """Polygon of everything left (or right) of a vertical tear line."""
    far = -2000.0 if left else W + 2000.0
    return [(far, tear[0][1] - 400.0)] + list(tear) + [(far, tear[-1][1] + 400.0)]


@lru_cache(maxsize=4)
def rock_polys(seed=0):
    """Jagged reef rocks rising from the bottom edge (list of polys; bases at y = H + 40)."""
    rocks = []
    spec = [(150, 230, 790), (330, 170, 980), (520, 210, 900), (720, 160, 1010), (900, 240, 800)]
    for i, (cx, half, h) in enumerate(spec):
        base = H + 40.0
        pts = [(cx - half, base)]
        n = 7
        for j in range(1, n):
            f = j / n
            x = cx - half + 2 * half * f
            peak = 1.0 - abs(f - 0.5) * 2.0
            y = base - h * (0.35 + 0.65 * peak) * (0.86 + 0.28 * hash01(seed, i, j))
            if j % 2:
                y += 60.0 * hash01(seed, i, j, 7)
            pts.append((x, y))
        pts.append((cx + half, base))
        rocks.append(bass.orient(bass.cut(pts, seed=seed * 13 + i, amp=1.6, seg=(20.0, 54.0)), True))
    return rocks


def fiber(ctx, edge, side, seed=0, width=6.0, color=FIBER):
    """The white core of torn paper along a tear (edge points), `side` = +1/-1 in x."""
    inner = [(x + side * width * (0.4 + 1.1 * hash01(seed, i, 9) ** 2), y) for i, (x, y) in enumerate(edge)]
    bass.fill_polys(ctx, [bass.orient(list(edge) + inner[::-1], True)], color)


# ----------------------------------------------------------------------------- money (s07)
@lru_cache(maxsize=4)
def banknote_polys(seed=0):
    """(note, window): a banknote 170 x 76 with its bottom-centre at (0, 0), pointing up
    (y negative); window = the oval portrait window cut out of it."""
    note = bass.cut([(-38.0, 0.0), (38.0, 0.0), (38.0, -170.0), (-38.0, -170.0)], seed=seed, amp=0.8,
                    seg=(20.0, 50.0))
    win = bass.ring_pts((0.0, -100.0), 15.0, seed=seed + 3, n=22, amp=0.5)
    win = [(x, -100.0 + (y + 100.0) * 1.35) for x, y in win]
    return bass.orient(note, True), bass.orient(win, True)


@lru_cache(maxsize=4)
def banknote_frame(seed=0):
    """The printed inner border of a banknote (a thin cut frame, two contours: fill nonzero)."""
    outer = [(-31.0, -8.0), (31.0, -8.0), (31.0, -162.0), (-31.0, -162.0)]
    inner = [(-28.0, -11.0), (28.0, -11.0), (28.0, -159.0), (-28.0, -159.0)]
    return [bass.orient(outer, True), bass.orient(inner, False)]


@lru_cache(maxsize=4)
def fist_polys(seed=0):
    """A cut-paper fist holding something at its grip point (0, 0), seen from the side,
    knuckles to the LEFT (the arm comes in from the right). Includes a long sleeve."""
    parts = [
        [(-6.0, -16.0), (52.0, -22.0), (78.0, -14.0), (82.0, 30.0), (54.0, 44.0), (-4.0, 48.0)],   # back
        bass.capsule_pts((-14.0, -6.0), (14.0, -6.0), 11.0, 11.0, 4),                           # fingers
        bass.capsule_pts((-18.0, 15.0), (14.0, 15.0), 11.5, 11.5, 4),
        bass.capsule_pts((-16.0, 35.0), (14.0, 35.0), 10.5, 10.5, 4),
        bass.capsule_pts((-10.0, 52.0), (14.0, 52.0), 8.5, 8.5, 4),
        bass.capsule_pts((40.0, -22.0), (2.0, -30.0), 10.0, 8.5, 4),                            # thumb
        [(76.0, -20.0), (110.0, -26.0), (112.0, 50.0), (78.0, 44.0)],                           # cuff
        [(104.0, -18.0), (1500.0, -40.0), (1500.0, 66.0), (104.0, 44.0)],                       # sleeve
    ]
    out = []
    for q, p in enumerate(parts):
        if len(p) > 8:
            pts = bass.scissor(p, seed=seed * 19 + q, sag=0.8, amp=0.5, max_len=22.0)
        else:
            pts = bass.cut(p, seed=seed * 19 + q, amp=0.9, seg=(16.0, 40.0))
        out.append(bass.orient(pts, True))
    return out


# ----------------------------------------------------------------------------- the cut (s07)
def torch_pts(c, r, seed=0, n=240):
    """The jagged torch cut: n points around a circle (clockwise from the top), zig-zagging."""
    out = []
    for i in range(n + 1):
        a = -math.pi / 2 + 2 * math.pi * i / n
        rr = r + (4.5 if i % 2 else -4.5) * (0.6 + 0.8 * hash01(seed, i % n, 1)) + 3.0 * math.sin(7 * a + seed)
        out.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return out


def torch_band(pts, u, width=8.0, seed=0):
    """Ribbon polygon of the torch cut drawn on to u (0..1); also returns the head point."""
    from engine import draw
    n = len(pts) - 1
    m = n * clamp(u)
    i = int(m)
    if m <= 0.5:
        return None, pts[0]
    sub = list(pts[: i + 1])
    if i < n:
        f = m - i
        a, b = pts[i], pts[i + 1]
        sub.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    widths = [width * (0.75 + 0.5 * hash01(seed, j, 2)) for j in range(len(sub))]
    return bass.orient(draw.ribbon(sub, widths), True), sub[-1]


@lru_cache(maxsize=4)
def petal_hole(seed=0, n=11):
    """The hole the torch left, for a unit radius: a circle with n steel petals bent outward
    (toward us), seen as dark curved teeth pointing into the opening. Scale it by the radius."""
    pet = []
    for i in range(n):
        a0 = 2 * math.pi * (i + 0.2 * sn(seed, i, 1)) / n
        half = (math.pi / n) * (0.24 + 0.26 * hash01(seed, i, 2))
        L = 0.13 + 0.25 * hash01(seed, i, 3) ** 1.3
        skew = (0.8 + 0.7 * hash01(seed, i, 6)) * (1.0 if hash01(seed, i, 4) < 0.5 else -1.0) * half
        pet.append((a0, half, L, skew))
    pts = []
    for i, (a0, half, L, skew) in enumerate(pet):
        pa0, phalf = pet[i - 1][0], pet[i - 1][1]
        if i == 0:
            pa0 -= 2 * math.pi
        g0, g1 = pa0 + phalf, a0 - half              # the rim arc between two petals
        for j in range(1, 6):
            a = g0 + (g1 - g0) * j / 6.0
            rr = 1.0 + 0.005 * sn(seed, i, j, 5)
            pts.append((rr * math.cos(a), rr * math.sin(a)))
        # a petal: a curved tooth (convex flanks), its tip bent a little to one side
        for q in range(0, 9):
            v = q / 8.0                               # 0 = left root, 0.5 = tip, 1 = right root
            depth = L * (1.0 - abs(2.0 * v - 1.0)) ** 0.8
            a = a0 - half + 2.0 * half * v + skew * (1.0 - abs(2.0 * v - 1.0))
            rr = 1.0 - depth
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    return bass.orient(pts, True)
