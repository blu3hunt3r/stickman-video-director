"""THIN ICE: the world, in metres, seen two ways.

THE MAP (the page, straight down). x east, n north, metres; north is UP the frame.

    cam = W.Plan(13.0, 4.0, 90.0)          # centre (x, n) on the map, px per metre [, rot deg]
    W.draw_page(c, cam, t, moonlit=1.0, prints=W.prints_before("s07"), holes=("stone",), ...)
    p = cam.px((x, n))                     # map -> frame px; cam.m(p) is the reverse

  draw_page lays, back to front: the snow; cloud shadows; the river's white ice and its banks; the
  black band; holes; the reeds; the trunk; the woods (crowns and long moon shadows); the fence, the
  tower, the guardhouse, the farmhouse; the prints. Scenes add lights (W.lamp_pool, W.search_patch)
  and figures from above (cast.top) after it.

THE STORY VIEWS (dioramas: cut open along a plane, everything behind it in one-point
perspective). u runs along the screen (to the right), z up, d metres behind the cut plane.

    cam = W.Dio(u0, z0, ppm, eye=7.0, D=14.0)   # frame centre (u0, z0) on the cut plane; the eye
                                                # `eye` m above z = 0 and D m in front of the plane
    cam.px(u, z, d=0.0)                         # -> frame px;  cam.scale(d) px per metre at depth d
    W.draw_river(c, cam, t, ...)                # looking WEST, cut through the false trail: u = n
    W.draw_woods(c, cam, t, ...)                # looking WEST, cut through the path: u = n

  On the river, z = 0 is the land's snow and the ice's top is ICE_Z (-0.9). The cut face shows the
  slab: thick and white (ICE_T) either side, thin and black across the band (THIN_T); black water
  under it; the riverbed; earth.

THE FENCE VIEW (s02, s03): looking NORTH through the wire, a composed set in frame px:
    W.draw_fence(c, t, cam=W.FenceCam(...), ...)

THE RECORD OF FOOTPRINTS. Prints are tuples (x, n, heading, kind, side, depth): heading in
degrees from north, clockwise; kind 'mother' | 'girl' | 'guard'; side +1 right, -1 left; depth
0..1 (deep prints are darker and wider). Each stage of the story owns a list:

    W.STAGES                      # stage -> [prints] ("fence", "woods", "river", "trail", ...)
    W.prints_before("s07")        # every print laid before scene s07 begins
    W.FALSE_TRAIL                 # s06's thirteen prints out across the ice, in order
    W.lay(prints, t, times)       # the prints laid by time t (times: one landing time each)
"""
import math
from functools import lru_cache

from engine import bass, draw
from engine.core import clamp, ease, hash01, lerp
from films.thin_ice import kit as K

INK, NIGHT, STEEL, SNOW, SHADOW = K.INK, K.NIGHT, K.STEEL, K.SNOW, K.SHADOW
ICE, THIN, WATER, PAPER, AMBER, RED = K.ICE, K.THIN, K.WATER, K.PAPER, K.AMBER, K.RED

# ============================================================================ the map (metres)
RIVER = (0.0, 25.0)                 # south bank, north bank (n)
BANK = 1.4                          # the banks' slope width (m), land 0.9 m above the ice
BAND = (10.0, 16.0)                 # the black band (n)
BAND_X0 = -22.0                     # ... from here downstream (east); upstream of it, white ice all across
CROSSING_X = -32.0                  # where she crosses at the end
TRAIL_X = 13.2
TRAIL_N = (-1.85, 9.0)              # the false trail: from the bank's slope to a stride short of the band
TRUNK = ((11.6, -2.0), (12.6, 8.6))     # root plate on the bank, tip on the ice
TRUNK_W = (0.52, 0.26)              # its width at the root, at the tip (m)
STUB_N = 7.4                        # the branch stub near the tip (her boot hooks it in s10)
STONE_HOLE = (12.2, 14.4)          # 1 m behind the river view's cut, off the trail's line
STONE_R = 0.35
HOLE = (13.3, 11.05)                # the guard's hole as he breaks through ...
HOLE_R = (0.95, 1.2)
HOLE_BIG = (13.3, 11.3)             # ... and after its edges have broken away (north: the white ice holds)
REEDS = (2.0, 10.6, -4.2, -0.6)     # x0, x1, n0, n1
HIDE = (7.5, -2.5)                  # where she hides in the reeds
WOODS_N = (-118.0, -8.0)
STUMBLE = (21.0, -48.0)             # where the small prints end
FENCE_N = -130.0
FENCE_X = (-70.0, 130.0)
CROSS = (40.0, -130.0)              # where they go under the wire
SCRAP = (40.15, -130.0)
TOWER = (24.0, -125.0)
GUARDHOUSE = (62.0, -126.5)
FARM = (-30.0, 38.0)                # the farmhouse (centre); its door and window face the river
FARM_DOOR = (-28.6, 35.0)
MOON_DIR = (0.0, 1.0)               # the moon is in the north ...
MOON_ALT = 33.0                     # ... and low: shadows fall south, 1.5 x as long as things are tall
SHADOW_K = 1.0 / math.tan(math.radians(MOON_ALT))

# the way they came: from the fence through the woods to the bank
PATH = ((40.0, -128.4), (38.6, -121.0), (35.0, -108.0), (31.0, -94.0), (27.6, -80.0), (23.8, -64.0), STUMBLE,
        (19.0, -36.0), (17.2, -24.0), (15.4, -13.0), (14.2, -5.5), (13.5, -2.6))
GIRL_OFF = 0.55                     # the girl walks this far to the mother's right (east)


# ============================================================================ helpers
def poly_len(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def poly_at(pts, s):
    """(point, unit direction) at arc length s along pts."""
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        if s <= d or (a, b) == (pts[-2], pts[-1]):
            u = clamp(s / d) if d > 0 else 0.0
            return (lerp(a[0], b[0], u), lerp(a[1], b[1], u)), ((b[0] - a[0]) / (d or 1.0), (b[1] - a[1]) / (d or 1.0))
        s -= d
    a, b = pts[-2], pts[-1]
    d = math.dist(a, b) or 1.0
    return b, ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def poly_cut(pts, s0, s1):
    out, acc = [], 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        lo, hi = max(s0, acc), min(s1, acc + d)
        if hi >= lo and d > 0:
            p0 = (lerp(a[0], b[0], (lo - acc) / d), lerp(a[1], b[1], (lo - acc) / d))
            p1 = (lerp(a[0], b[0], (hi - acc) / d), lerp(a[1], b[1], (hi - acc) / d))
            if not out or math.dist(out[-1], p0) > 1e-9:
                out.append(p0)
            out.append(p1)
        acc += d
    return out


def offset_path(pts, off):
    """The polyline pts moved `off` m to its right."""
    out = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dn = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dn) or 1.0
        out.append((p[0] + off * dn / L, p[1] - off * dx / L))
    return out


def heading_of(d):
    """Degrees from north, clockwise, of a map direction (dx, dn)."""
    return math.degrees(math.atan2(d[0], d[1]))


def _wig(x, seed, amp=0.35):
    return amp * (math.sin(x * 0.21 + seed) * 0.6 + math.sin(x * 0.57 + 2.0 * seed) * 0.3 +
                  math.sin(x * 1.31 + 3.0 * seed) * 0.1)


def bend(x):
    """The river's meander (m north): flat near the trail, bending south upstream (west) and a
    little north downstream."""
    return 6.0 * math.tanh((x - TRAIL_X) / 30.0) ** 3


def bank_s(x):
    return RIVER[0] + bend(x) + _wig(x, 1.0)


def bank_n(x):
    return RIVER[1] + bend(x) + _wig(x, 4.0, 0.45)


def band_lo(x):
    return BAND[0] + bend(x) + _wig(x, 7.0, 0.5)


def band_hi(x):
    return BAND[1] + bend(x) + _wig(x, 9.0, 0.5)


def band_taper(x):
    """0 upstream of the band's tip, rising to 1 over its first 7 m (the rounded west end)."""
    u = clamp((x - BAND_X0) / 7.0)
    return math.sqrt(u * (2.0 - u))


def on_band(x, n):
    """True where the ice is thin (n inside the band at x)."""
    if x < BAND_X0:
        return False
    tp = band_taper(x)
    mid = 0.5 * (band_lo(x) + band_hi(x))
    half = 0.5 * (band_hi(x) - band_lo(x)) * tp
    return abs(n - mid) <= half


# ============================================================================ the plan camera
class Plan:
    """A straight-down camera: map (x, n) metres -> frame px. rot turns the map (degrees, counter-
    clockwise on screen)."""

    def __init__(self, x, n, ppm, rot=0.0):
        self.x, self.n, self.ppm, self.rot = float(x), float(n), float(ppm), float(rot)
        a = math.radians(self.rot)
        self._c, self._s = math.cos(a), math.sin(a)

    def px(self, p):
        dx, dn = p[0] - self.x, p[1] - self.n
        X = dx * self._c - dn * self._s
        N = dx * self._s + dn * self._c
        return (540.0 + X * self.ppm, 960.0 - N * self.ppm)

    def pts(self, P):
        return [self.px(p) for p in P]

    def m(self, q):
        X, N = (q[0] - 540.0) / self.ppm, (960.0 - q[1]) / self.ppm
        return (self.x + X * self._c + N * self._s, self.n - X * self._s + N * self._c)

    def bounds(self, margin=2.0):
        cs = [self.m(q) for q in ((0.0, 0.0), (1080.0, 0.0), (0.0, 1920.0), (1080.0, 1920.0))]
        return (min(p[0] for p in cs) - margin, max(p[0] for p in cs) + margin,
                min(p[1] for p in cs) - margin, max(p[1] for p in cs) + margin)

    def dir(self, d):
        """A map direction (dx, dn) as a frame direction (unit)."""
        X = d[0] * self._c - d[1] * self._s
        N = d[0] * self._s + d[1] * self._c
        L = math.hypot(X, N) or 1.0
        return (X / L, -N / L)

    def screen_heading(self, heading):
        """Frame angle (degrees, 0 = +x, 90 = +y) of a map heading (degrees from north)."""
        h = math.radians(heading)
        d = self.dir((math.sin(h), math.cos(h)))
        return math.degrees(math.atan2(d[1], d[0]))


def plan_lerp(a, b, u):
    """A camera between two plans (zoom eased in log space so it doesn't rush)."""
    ppm = math.exp(lerp(math.log(a.ppm), math.log(b.ppm), u))
    return Plan(lerp(a.x, b.x, u), lerp(a.n, b.n, u), ppm, lerp(a.rot, b.rot, u))


# ============================================================================ static geometry (metres)
def _cutm(pts, seed, amp=0.03, max_len=0.6, sag=0.02, corner=40.0):
    """A scissor cut in metres (cached by the caller)."""
    return bass.scissor(pts, seed=seed, sag=sag, amp=amp, max_len=max_len, corner=corner)


@lru_cache(maxsize=1)
def woods():
    """The trees: (x, n, crown radius, height, seed), a jittered grid with the path left clear."""
    out = []
    step = 4.6
    path = PATH
    for gi in range(-16, 30):
        for gj in range(-27, 0):
            x = gi * step + 2.2 * K._sn(gi, gj, 1)
            n = gj * step - 2.0 + 2.0 * K._sn(gi, gj, 2)
            if not (WOODS_N[0] <= n <= WOODS_N[1]) or hash01(gi, gj, 3) > 0.78:
                continue
            # keep the path clear: distance to the path polyline
            dmin = min(_seg_dist((x, n), a, b) for a, b in zip(path, path[1:]))
            if dmin < 3.4:
                continue
            r = 1.5 + 1.2 * hash01(gi, gj, 4)
            h = 9.0 + 7.0 * hash01(gi, gj, 5)
            out.append((x, n, r, h, gi * 131 + gj))
    # thinning toward the river: a few willows at the bank
    for i in range(9):
        x = -20.0 + 4.5 * i + 1.5 * K._sn(i, 77)
        if 1.0 < x < 16.0:
            continue
        out.append((x, -6.5 + 1.2 * K._sn(i, 78), 1.6, 6.0, 9000 + i))
    return tuple(out)


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1.0
    u = clamp(((p[0] - ax) * dx + (p[1] - ay) * dy) / L2)
    return math.hypot(p[0] - (ax + dx * u), p[1] - (ay + dy * u))


@lru_cache(maxsize=None)
def crown(r, seed):
    """A spruce from above: a spiky disc (metres, at the origin)."""
    n = 10 + int(4 * hash01(seed, 1))
    rot = 6.283 * hash01(seed, 2)
    pts = []
    for i in range(2 * n):
        a = rot + math.pi * i / n
        rr = r * (1.0 if i % 2 == 0 else 0.62 + 0.08 * K._sn(seed, i))
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return tuple(_cutm(pts, seed, amp=0.04 * r, max_len=0.8 * r, sag=0.02 * r, corner=30.0))


@lru_cache(maxsize=None)
def crown_shadow(r, h, seed):
    """The tree's moon shadow on the snow: a long spiky wedge toward the south (metres): widest
    near the foot (a spruce's lowest tiers), narrowing to the shadow of its tip."""
    L = h * SHADOW_K
    m = 10
    right = []
    for i in range(m + 1):
        u = i / m
        w = r * (0.22 + 0.78 * (1.0 - u) ** 0.9) * (1.0 if i % 2 == 0 else 0.7) * (0.92 + 0.16 * hash01(seed, i, 3))
        right.append((w, -L * (0.06 + 0.94 * u)))
    left = [(-x * (0.94 + 0.12 * hash01(seed, i, 4)), y) for i, (x, y) in enumerate(right)]
    shape = [(0.2 * r, 0.0)] + right + [(0.0, -L * 1.02)] + left[::-1] + [(-0.2 * r, 0.0)]
    return tuple(_cutm(shape, seed + 5, amp=0.05, max_len=1.2, sag=0.05, corner=25.0))


@lru_cache(maxsize=1)
def reeds():
    """Reed tufts in the bank (x, n, size, seed)."""
    out = []
    x0, x1, n0, n1 = REEDS
    i = 0
    for gx in range(int((x1 - x0) / 0.55) + 1):
        for gn in range(int((n1 - n0) / 0.55) + 1):
            x = x0 + gx * 0.55 + 0.22 * K._sn(gx, gn, 11)
            n = n0 + gn * 0.55 + 0.22 * K._sn(gx, gn, 12)
            edge = min(x - x0, x1 - x, n - n0, n1 - n)
            if hash01(gx, gn, 13) > 0.55 + 0.3 * clamp(edge / 1.2):
                continue
            out.append((x, n, 0.22 + 0.16 * hash01(gx, gn, 14), i))
            i += 1
    # a sparse fringe along the north bank
    for j in range(40):
        x = -40.0 + j * 2.6 + 1.1 * K._sn(j, 15)
        out.append((x, bank_n(x) + 0.9 + 0.5 * hash01(j, 16), 0.2, 5000 + j))
    return tuple(out)


@lru_cache(maxsize=None)
def tuft(size, seed):
    """A reed tuft from above: short spokes (metres)."""
    out = []
    n = 5 + int(3 * hash01(seed, 1))
    for i in range(n):
        a = 6.283 * (i + 0.4 * K._sn(seed, i)) / n
        L = size * (0.6 + 0.5 * hash01(seed, i, 2))
        out.append(((0.0, 0.0), (L * math.cos(a), L * math.sin(a))))
    return tuple(out)


@lru_cache(maxsize=1)
def trunk_poly():
    """The fallen trunk from above (metres): a tapering band, root to tip, with stubs."""
    (x0, n0), (x1, n1) = TRUNK
    L = math.hypot(x1 - x0, n1 - n0)
    ux, un = (x1 - x0) / L, (n1 - n0) / L
    rx, rn = un, -ux
    left, right = [], []
    m = 16
    for i in range(m + 1):
        u = i / m
        w = 0.5 * lerp(TRUNK_W[0], TRUNK_W[1], u) * (1.0 + 0.06 * K._sn(i, 21))
        cx, cn = x0 + ux * L * u, n0 + un * L * u
        left.append((cx - rx * w, cn - rn * w))
        right.append((cx + rx * w, cn + rn * w))
    body = left + right[::-1]
    stubs = []
    for j, (u, side, ln) in enumerate(((0.18, 1, 0.5), (0.34, -1, 0.7), (0.52, 1, 0.42), (0.66, -1, 0.55),
                                       ((STUB_N - n0) / (n1 - n0), 1, 0.38), (0.9, -1, 0.3))):
        cx, cn = x0 + ux * L * u, n0 + un * L * u
        w = 0.5 * lerp(TRUNK_W[0], TRUNK_W[1], u)
        a = (cx + side * rx * w * 0.6, cn + side * rn * w * 0.6)
        b = (a[0] + side * rx * ln + ux * ln * 0.35, a[1] + side * rn * ln + un * ln * 0.35)
        stubs.append((a, b))
    plate = []
    # the root plate stands up across the root end: from above, a ragged thick bar
    for i in range(14):
        u = i / 13.0
        plate.append((x0 - ux * 0.25 + rx * (u - 0.5) * 2.4, n0 - un * 0.25 + rn * (u - 0.5) * 2.4 + 0.12 * K._sn(i, 31)))
    for i in range(14):
        u = 1.0 - i / 13.0
        plate.append((x0 - ux * 0.62 + rx * (u - 0.5) * 2.2, n0 - un * 0.62 + rn * (u - 0.5) * 2.2 + 0.12 * K._sn(i, 32)))
    return tuple(_cutm(body, 41, amp=0.02, max_len=0.5)), tuple(stubs), tuple(_cutm(plate, 42, amp=0.04, max_len=0.5))


def trunk_point(u):
    """A point along the trunk's axis (u 0 root .. 1 tip), map metres."""
    (x0, n0), (x1, n1) = TRUNK
    return (lerp(x0, x1, u), lerp(n0, n1, u))


def trunk_u(n):
    """The trunk's u at map n."""
    return clamp((n - TRUNK[0][1]) / (TRUNK[1][1] - TRUNK[0][1]))


@lru_cache(maxsize=None)
def hole_poly(centre, r, seed):
    """A ragged hole in the ice (metres)."""
    pts = []
    n = 26
    for i in range(n):
        a = 6.283 * i / n
        rr = r * (1.0 + 0.16 * K._sn(seed, i) + 0.07 * K._sn(seed, i, 2))
        pts.append((centre[0] + rr * math.cos(a), centre[1] + rr * math.sin(a)))
    return tuple(_cutm(pts, seed, amp=0.015 * r * 4, max_len=0.35 * r, sag=0.01, corner=20.0))


@lru_cache(maxsize=None)
def hole_shards(centre, r, seed, n=9):
    """Broken plates round a hole (metres): small floating polygons."""
    out = []
    for i in range(n):
        a = 6.283 * (i + 0.5 * K._sn(seed, i)) / n
        rr = r * (0.55 + 0.3 * hash01(seed, i, 3))
        cx, cn = centre[0] + rr * math.cos(a), centre[1] + rr * math.sin(a)
        s = r * (0.13 + 0.12 * hash01(seed, i, 4))
        rot = 6.283 * hash01(seed, i, 5)
        shard = [(cx + s * math.cos(rot + 6.283 * j / 5) * (0.7 + 0.5 * hash01(seed, i, j)),
                  cn + s * math.sin(rot + 6.283 * j / 5) * (0.7 + 0.5 * hash01(seed, i, j))) for j in range(5)]
        out.append(tuple(shard))
    return tuple(out)


HOLES = {"stone": (STONE_HOLE, STONE_R, 61), "guard": (HOLE_BIG, HOLE_R[1], 62), "guard_small": (HOLE, HOLE_R[0], 62)}


# ============================================================================ the page
def draw_page(c, cam, t=0.0, moonlit=1.0, prints=(), cover=0.0, holes=(), clouds=None, woods_on=True,
              farm_light=1.0, guardhouse_light=1.0, door=0.0, reeds_on=True, trunk_on=True, band_cracks=(),
              fence_on=True, scrap=True, grow=None, shadows=1.0, woods_keep=1.0, crown_scale=1.0, woods_mass_a=0.0):
    """The page at plan camera cam. moonlit 0..1 (0: under cloud). prints: print tuples. cover:
    0..1, fresh snow filling the prints (they fade and shrink into the page). holes: names in
    HOLES or (centre, r, seed) tuples. clouds: [(x, n, rx, rn)] map ellipses of cloud shadow.
    door: 0..1 the farmhouse door open (its light falls across the snow). band_cracks: [(tree,
    u)] crack trees in map metres drawn on the band. grow: {element: 0..1} pops the map's elements
    in (s01): 'river', 'band', 'farm', 'woods', 'fence', 'tower', 'guardhouse' (missing = 1).
    shadows 0..1: the moon's shadows (0 under cloud: they melt into the page). woods_keep 0..1:
    the share of the trees drawn (the title's map thins them); crown_scale: their size;
    woods_mass_a 0..1: the far woods' canopy under the crowns (draw_woods_mass)."""
    g = grow or {}
    x0, x1, n0, n1 = cam.bounds(3.0)
    snow_c = lerp(K.SNOW_DIM, SNOW, moonlit)
    ice_c = lerp(K.ICE_DIM, ICE, moonlit)
    shade_c = lerp(lerp(K.SNOW_DIM, SHADOW, 0.55), lerp(SNOW, SHADOW, 0.55), moonlit)
    shade_c = lerp(snow_c, shade_c, clamp(shadows))
    K.fill(c, snow_c)
    gr = g.get("river", 1.0)
    # ---- the river
    if gr > 0.0 and n1 > RIVER[0] - 3 and n0 < RIVER[1] + 3:
        xs = [x0 + (x1 - x0) * i / 60.0 for i in range(61)]
        mid = 0.5 * (RIVER[0] + RIVER[1])
        lo = [(x, lerp(mid, bank_s(x), gr)) for x in xs]
        hi = [(x, lerp(mid, bank_n(x), gr)) for x in xs]
        K.poly(c, cam.pts(lo + hi[::-1]), ice_c)
        # the north bank's slope faces away from the moon: in shade
        if gr >= 1.0:
            slope = [(x, bank_n(x)) for x in xs] + [(x, bank_n(x) + BANK * 0.8 + 0.2 * _wig(x, 5.0)) for x in xs[::-1]]
            K.poly(c, cam.pts(slope), shade_c)
            # the south bank's foot: a thin line of shade where the bank meets the ice
            foot = [(x, bank_s(x)) for x in xs] + [(x, bank_s(x) + 0.16) for x in xs[::-1]]
            K.poly(c, cam.pts(foot), shade_c)
    gb = g.get("band", 1.0)
    if gb > 0.0 and x1 > BAND_X0 and n1 > BAND[0] - 2 and n0 < BAND[1] + 2:
        xa = max(x0, BAND_X0)
        xs = [xa + (x1 - xa) * i / 60.0 for i in range(61)]
        mid = [0.5 * (band_lo(x) + band_hi(x)) for x in xs]
        lo = [(x, m - (m - band_lo(x)) * band_taper(x) * gb) for x, m in zip(xs, mid)]
        hi = [(x, m + (band_hi(x) - m) * band_taper(x) * gb) for x, m in zip(xs, mid)]
        K.poly(c, cam.pts(lo + hi[::-1]), lerp(lerp(THIN, NIGHT, 0.2), THIN, moonlit))
        for tree, u in band_cracks:
            K.crack(c, tree, u, PAPER, width=max(1.6, 0.05 * cam.ppm), xf=cam.px)
    # ---- holes
    for h in holes:
        centre, r, seed = HOLES[h] if isinstance(h, str) else h
        draw_hole(c, cam, centre, r, seed)
    # ---- the reeds and the trunk
    if reeds_on and x1 > REEDS[0] - 1 and x0 < REEDS[1] + 1 and n0 < REEDS[3] + 1 and n1 > REEDS[2] - 1:
        draw_reeds(c, cam, (x0, x1, n0, n1))
    elif reeds_on:
        draw_reeds(c, cam, (x0, x1, n0, n1), north_only=True)
    if trunk_on and x1 > 10 and x0 < 14 and n1 > -4 and n0 < 10:
        draw_trunk_top(c, cam, shade_c)
    # ---- the woods
    if woods_on and n0 < WOODS_N[1] + 2:
        mass = (lambda c_: draw_woods_mass(c_, cam, snow_c, woods_mass_a)) if woods_mass_a > 0.0 else None
        draw_woods_top(c, cam, (x0, x1, n0, n1), shade_c, g.get("woods", 1.0), keep=woods_keep, scale=crown_scale,
                       shadows=shadows > 0.0, under=mass)
    # ---- the fence, tower, guardhouse
    if fence_on and n0 < FENCE_N + 8 and n1 > FENCE_N - 6:
        draw_fence_top(c, cam, t, shade_c, g.get("fence", 1.0), scrap=scrap)
    if n0 < TOWER[1] + 8 and n1 > TOWER[1] - 30:
        draw_tower_top(c, cam, shade_c, g.get("tower", 1.0))
        draw_house_top(c, cam, GUARDHOUSE, (5.0, 4.0), shade_c, g.get("guardhouse", 1.0), light=guardhouse_light,
                       window_side=1, seed=71)
    if n1 > FARM[1] - 12:
        draw_house_top(c, cam, FARM, (9.0, 6.0), shade_c, g.get("farm", 1.0), light=farm_light, window_side=-1,
                       seed=81, door=door)
    # ---- prints
    if prints:
        draw_prints(c, cam, prints, cover=cover, page=snow_c, bounds=(x0, x1, n0, n1))
    # ---- cloud shadows: over everything on the ground
    if clouds:
        for (cx, cn, rx, rn) in clouds:
            K.ellipse(c, cam.px((cx, cn)), rx * cam.ppm, rn * cam.ppm, NIGHT, alpha=0.28, n=64)


def draw_hole(c, cam, centre, r, seed, water=WATER, rim=None):
    shards = hole_shards(centre, r, seed)
    K.poly(c, cam.pts(hole_poly(centre, r, seed)), water)
    for s in shards:
        K.poly(c, cam.pts(s), rim or lerp(THIN, ICE, 0.35))


def draw_reeds(c, cam, b, north_only=False, color=INK):
    x0, x1, n0, n1 = b
    w = max(1.2, 0.035 * cam.ppm)
    for (x, n, s, seed) in reeds():
        if north_only and seed < 5000:
            continue
        if not (x0 <= x <= x1 and n0 <= n <= n1):
            continue
        for a, bb in tuft(s, seed):
            K.band(c, [cam.px((x + a[0], n + a[1])), cam.px((x + bb[0], n + bb[1]))], color, w, seed=seed)


def draw_trunk_top(c, cam, shade_c):
    body, stubs, plate = trunk_poly()
    # the root plate stands ~2 m tall: its shadow falls south
    sh = [(x, n - 2.0 * SHADOW_K * (0.4 + 0.6 * hash01(i, 5))) for i, (x, n) in enumerate(plate)]
    K.poly(c, cam.pts(list(plate) + sh[::-1]), shade_c)
    K.poly(c, cam.pts(body), INK)
    w = max(1.5, 0.12 * cam.ppm)
    for i, (a, b) in enumerate(stubs):
        K.band(c, [cam.px(a), cam.px(b)], INK, w, seed=90 + i, taper=(1.0, 0.4))
    K.poly(c, cam.pts(plate), INK)


def draw_woods_top(c, cam, b, shade_c, grow=1.0, keep=1.0, scale=1.0, shadows=True, under=None):
    """The crowns from above and their moon shadows; under(c), if given, draws between the two."""
    x0, x1, n0, n1 = b
    trees = [tr for tr in woods() if x0 - 4 <= tr[0] <= x1 + 4 and n0 - 4 <= tr[1] <= n1 + 28]
    shp, crs = [], []
    for (x, n, r, h, seed) in trees:
        if keep < 1.0 and hash01(seed, 21) > keep:
            continue
        gz = clamp(grow * 1.6 - 0.6 * hash01(seed, 9))
        if gz <= 0.0:
            continue
        sc = ease("outback", gz) * scale
        shp.append(cam.pts([(x + px_ * sc, n + pn * sc) for px_, pn in crown_shadow(r, h, seed)]))
        crs.append(cam.pts([(x + px_ * sc, n + pn * sc) for px_, pn in crown(r, seed)]))
    if shadows:
        K.polys(c, shp, shade_c)
    if under is not None:
        under(c)
    K.polys(c, crs, INK)


@lru_cache(maxsize=1)
def woods_mass():
    """The woods seen from far off as one cut-paper canopy (map metres): its south and north edges
    follow the edge trees, smoothed, with a jagged fringe of spruce tips."""
    trees = [tr for tr in woods() if tr[1] <= WOODS_N[1]]
    xs = [-80.0 + 0.8 * i for i in range(276)]

    def edge(pick, out_sign, seed):
        raw = []
        for x in xs:
            near = [tn for (tx, tn, r, h, sd) in trees if abs(tx - x) <= 3.0]
            raw.append(pick(near) if near else None)
        last = next(v for v in raw if v is not None)
        for i, v in enumerate(raw):
            raw[i] = last = (v if v is not None else last)
        pts = []
        for i, x in enumerate(xs):
            win = raw[max(0, i - 8): i + 9]
            base = sum(win) / len(win)
            tip = (1.9 if i % 2 == 0 else 0.7) + 0.45 * K._sn(seed, i)
            pts.append((x, base + out_sign * tip))
        return pts

    south = edge(min, -1.0, 5)
    north = edge(max, +1.0, 6)
    return tuple(south + north[::-1])


def draw_woods_mass(c, cam, page_c, alpha=1.0, path_w=5.0):
    """The far woods (s01's map): the canopy in INK with the path through it in the page's colour.
    Draw it under draw_woods_top's crowns."""
    if alpha <= 0.0:
        return
    K.poly(c, cam.pts(woods_mass()), INK, alpha)
    run = [p for p in PATH if p[1] <= WOODS_N[1] + 3.0]
    K.band(c, cam.pts(run), page_c, max(1.5, path_w * cam.ppm), seed=23, alpha=alpha)


def draw_fence_top(c, cam, t, shade_c, grow=1.0, scrap=True):
    if grow <= 0.0:
        return
    xa, xb = FENCE_X
    xm = lerp(CROSS[0], xa, grow), lerp(CROSS[0], xb, grow)
    w = max(1.2, 0.06 * cam.ppm)
    K.band(c, [cam.px((xm[0], FENCE_N)), cam.px((xm[1], FENCE_N))], INK, w, seed=3)
    x = math.ceil(xm[0] / 3.0) * 3.0
    while x <= xm[1]:
        p = cam.px((x, FENCE_N))
        s = max(2.0, 0.22 * cam.ppm)
        # the post and its short moon shadow
        K.band(c, [p, cam.px((x, FENCE_N - 2.2 * SHADOW_K))], shade_c, max(1.2, 0.12 * cam.ppm), seed=int(x))
        K.poly(c, [(p[0] - s / 2, p[1] - s / 2), (p[0] + s / 2, p[1] - s / 2), (p[0] + s / 2, p[1] + s / 2),
                   (p[0] - s / 2, p[1] + s / 2)], INK)
        x += 3.0
    if scrap:
        p = cam.px(SCRAP)
        s = max(2.0, 0.18 * cam.ppm)
        K.poly(c, [(p[0] - s, p[1] - s * 0.4), (p[0] + s * 0.8, p[1] - s * 0.7), (p[0] + s * 0.5, p[1] + s * 0.6)], INK)


def draw_tower_top(c, cam, shade_c, grow=1.0):
    if grow <= 0.0:
        return
    x, n = TOWER
    g = ease("outback", clamp(grow))
    s = 1.7 * g
    hgt = 9.0
    sh = [(x - s, n), (x + s, n), (x + s * 0.7, n - hgt * SHADOW_K), (x - s * 0.7, n - hgt * SHADOW_K)]
    K.poly(c, cam.pts(sh), shade_c)
    K.poly(c, cam.pts(_cutm([(x - s, n - s), (x + s, n - s), (x + s, n + s), (x - s, n + s)], 51, amp=0.03)), INK)


def draw_house_top(c, cam, centre, size, shade_c, grow=1.0, light=1.0, window_side=1, seed=0, door=0.0):
    """A hut from above: its roof (a ridge line in shade), its moon shadow, and the warm light from
    its window falling on the snow (window_side +1: the window faces north; -1: south)."""
    if grow <= 0.0:
        return
    x, n = centre
    g = ease("outback", clamp(grow))
    hw, hn = size[0] / 2.0 * g, size[1] / 2.0 * g
    hgt = 4.5
    sh = [(x - hw, n - hn), (x + hw, n - hn), (x + hw, n - hn - hgt * SHADOW_K), (x - hw, n - hn - hgt * SHADOW_K)]
    K.poly(c, cam.pts(sh), shade_c)
    if light > 0.0:
        side_n = n + window_side * hn
        spill = [(x - 0.7, side_n), (x + 0.7, side_n), (x + 2.4, side_n + window_side * 6.0),
                 (x - 2.4, side_n + window_side * 6.0)]
        K.poly(c, cam.pts(spill), AMBER, alpha=0.22 * light)
    if door > 0.0:
        dx = x + 1.4
        side_n = n - hn
        spill = [(dx - 0.5, side_n), (dx + 0.5, side_n), (dx + 0.5 + 2.6 * door, side_n - 9.0 * door),
                 (dx - 0.5 - 2.6 * door, side_n - 9.0 * door)]
        K.poly(c, cam.pts(spill), AMBER, alpha=0.5 * door)
    roof = _cutm([(x - hw, n - hn), (x + hw, n - hn), (x + hw, n + hn), (x - hw, n + hn)], seed, amp=0.04)
    K.poly(c, cam.pts(roof), INK)
    # the ridge, a thin light line along the roof (moonlit north slope)
    K.band(c, [cam.px((x - hw * 0.9, n + hn * 0.08)), cam.px((x + hw * 0.9, n + hn * 0.08))], lerp(INK, STEEL, 0.6),
           max(1.0, 0.1 * cam.ppm), seed=seed)
    ch = cam.px((x + hw * 0.5, n + hn * 0.4))
    s = max(2.0, 0.45 * cam.ppm)
    K.poly(c, [(ch[0] - s / 2, ch[1] - s / 2), (ch[0] + s / 2, ch[1] - s / 2), (ch[0] + s / 2, ch[1] + s / 2),
               (ch[0] - s / 2, ch[1] + s / 2)], lerp(INK, STEEL, 0.35))


def draw_prints(c, cam, prints, cover=0.0, page=SNOW, bounds=None, alpha=1.0, color=SHADOW):
    if cover >= 0.999:
        return
    x0, x1, n0, n1 = bounds or cam.bounds(1.0)
    groups = {}
    for (x, n, hdg, kind, side, depth) in prints:
        if not (x0 <= x <= x1 and n0 <= n <= n1):
            continue
        col = lerp(lerp(color, THIN, 0.3 * depth), page, ease("inout", cover))
        sc = (1.0 + 0.22 * depth) * (1.0 - 0.35 * cover)
        L = K._PRINT[kind][0] * sc
        hx, hn = x - math.sin(math.radians(hdg)) * L / 2.0, n - math.cos(math.radians(hdg)) * L / 2.0
        groups.setdefault(col, []).append(cam.pts(K.print_world(kind, side, (hx, hn), hdg, sc)))
    for col, ps in groups.items():
        K.polys(c, ps, col, alpha)


def lamp_pool(c, cam, centre, r, strength=1.0, t=0.0, seed=0):
    """The lantern's warm pool on the snow, from above (r in metres)."""
    K.glow(c, cam.px(centre), r * cam.ppm, strength, t, seed=seed)


def search_patch(c, cam, centre, r, alpha=0.85, stretch=1.25, heading=0.0):
    """The searchlight's lit patch on the snow, from above (r in metres; stretched along heading,
    away from the tower)."""
    ang = cam.screen_heading(heading)
    K.lit_patch(c, cam.px(centre), r * stretch * cam.ppm, r * cam.ppm, alpha=alpha, angle=ang)


# ============================================================================ the record of footprints
def walk_prints(route, kind, step, depth=0.25, lateral=0.09, side0=1, seed=0, s0=0.0, s1=None):
    """Prints along a route (map metres): one every `step` m between arc lengths s0 and s1,
    alternating feet `lateral` m either side of the line."""
    L = poly_len(route)
    s1 = L if s1 is None else s1
    out = []
    i = 0
    s = s0
    side = side0
    while s <= s1 + 1e-6:
        p, d = poly_at(route, s)
        h = heading_of(d) + 7.0 * K._sn(seed, i, 1) + side * 5.0
        rx, rn = d[1], -d[0]
        jit = 0.025 * K._sn(seed, i, 2)
        out.append((p[0] + rx * (side * lateral + jit), p[1] + rn * (side * lateral + jit), h, kind, side,
                    clamp(depth + 0.08 * K._sn(seed, i, 3))))
        side = -side
        s += step * (1.0 + 0.05 * K._sn(seed, i, 4))
        i += 1
    return out


def _s_at(route, target):
    """Arc length along route of the vertex nearest target."""
    best, acc, bs = None, 0.0, 0.0
    for a, b in zip(route, route[1:]):
        d = math.dist(a, b)
        for u in (0.0, 0.25, 0.5, 0.75, 1.0):
            p = (lerp(a[0], b[0], u), lerp(a[1], b[1], u))
            e = math.dist(p, target)
            if best is None or e < best:
                best, bs = e, acc + d * u
        acc += d
    return bs


S_STUMBLE = _s_at(PATH, STUMBLE)
GIRL_PATH = tuple(offset_path(list(PATH), GIRL_OFF))
# the fugitives: the crouch, under the wire, then both of them to the stumble
FENCE_PRINTS = (walk_prints([(40.0, -133.0), (40.0, -131.2)], "mother", 0.6, 0.3, seed=1) +
                walk_prints([(40.6, -133.0), (40.6, -131.4)], "girl", 0.42, 0.3, seed=2) +
                walk_prints(PATH, "mother", 0.62, 0.35, seed=3, s1=11.0) +
                walk_prints(GIRL_PATH, "girl", 0.44, 0.35, seed=4, s1=11.0))
WOODS_PRINTS = (walk_prints(PATH, "mother", 0.62, 0.42, seed=5, s0=11.0 + 0.62, s1=S_STUMBLE) +
                walk_prints(GIRL_PATH, "girl", 0.44, 0.5, seed=6, s0=11.0 + 0.44, s1=S_STUMBLE - 0.3) +
                # the fall: a trampled patch, then only her prints, deeper and closer together
                [(STUMBLE[0] + 0.45 + 0.35 * K._sn(i, 71), STUMBLE[1] + 0.2 * K._sn(i, 72), 360.0 * hash01(i, 73),
                  "girl" if i % 3 else "mother", 1 if i % 2 else -1, 0.9) for i in range(9)] +
                walk_prints(PATH, "mother", 0.5, 0.85, seed=7, s0=S_STUMBLE + 0.5))
# at the bank (s05): she sets the girl down by the root plate; the girl stands there
RIVER_PRINTS = tuple(walk_prints([(13.5, -2.6), (12.9, -2.75)], "mother", 0.5, 0.5, seed=8) +
                     [(12.25, -2.95, 200.0, "girl", 1, 0.5), (12.05, -2.85, 175.0, "girl", -1, 0.5)])
# s06: out across the ice to the band, in a straight line (her own prints, carrying the girl)
FALSE_TRAIL = tuple((TRAIL_X + (0.1 if i % 2 == 0 else -0.1) + 0.02 * K._sn(i, 91), TRAIL_N[0] + (TRAIL_N[1] - TRAIL_N[0]) * i / 18.0,
                     5.0 * K._sn(i, 92) + (5.0 if i % 2 == 0 else -5.0), "mother", 1 if i % 2 == 0 else -1,
                     0.75 + 0.06 * K._sn(i, 93)) for i in range(19))
BACKTRACK_TO = 12        # she walks backward in her prints to this one (index), beside the trunk
# the guard: along the fence from his hut, over their prints into the woods, out along the trail
GUARD_FENCE = tuple(walk_prints([(GUARDHOUSE[0] - 1.0, GUARDHOUSE[1] - 2.4), (CROSS[0] + 1.2, FENCE_N + 1.0),
                                 (CROSS[0] + 1.0, FENCE_N + 2.2)], "guard", 0.74, 0.4, seed=10) +
                    walk_prints(offset_path(list(PATH), -0.55), "guard", 0.74, 0.45, seed=11, s1=11.0))
GUARD_WOODS = tuple(walk_prints(offset_path(list(PATH), -0.55), "guard", 0.76, 0.55, seed=12, s0=11.0 + 0.76))
GUARD_ICE = tuple(walk_prints([(13.95, -2.4), (13.62, -1.0), (13.55, TRAIL_N[1] + 0.25)], "guard", 0.74, 0.55,
                              seed=13) + [(13.42, 10.35, 2.0, "guard", 1, 0.6)])
# after the rescue: his drag mark from the hole to the trunk's tip; the trampled bank
DRAG = ((13.2, 10.2), (13.0, 9.5), (12.75, 8.85))
RESCUE_PRINTS = tuple([(12.2 + 0.7 * K._sn(i, 81), -2.6 + 0.5 * K._sn(i, 82), 360.0 * hash01(i, 83),
                        ("guard", "mother", "girl")[i % 3], 1 if i % 2 else -1, 0.7) for i in range(16)])
# s11: the two of them go upstream along the bank; the other guards come down to the river
ESCAPE = ((10.4, -2.7), (6.0, -2.2), (0.0, -1.9), (-10.0, -1.7), (-22.0, -1.6), (CROSSING_X, -1.4))
ESCAPE_PRINTS = tuple(walk_prints(list(ESCAPE), "mother", 0.6, 0.45, seed=14))
GUARDS_PRINTS = tuple(walk_prints([(18.0, -14.0), (15.2, -6.0), (14.2, -2.2)], "guard", 0.74, 0.5, seed=15) +
                      walk_prints([(10.5, -13.0), (12.6, -6.0), (13.2, -2.5)], "guard", 0.74, 0.5, seed=16) +
                      walk_prints([(22.0, -12.0), (17.0, -5.0), (14.9, -2.0)], "guard", 0.74, 0.5, seed=17))
# s12: across the white ice upstream, and up the far bank to the door
CROSSING = ((CROSSING_X, -1.4), (CROSSING_X + 0.3, 12.0), (CROSSING_X + 0.8, RIVER[1] + 0.6), (FARM_DOOR[0], FARM_DOOR[1] - 0.6))
CROSSING_PRINTS = tuple(walk_prints(list(CROSSING), "mother", 0.6, 0.5, seed=18))

STAGES = {
    "fence": tuple(FENCE_PRINTS),                  # s02
    "guard_fence": GUARD_FENCE,                    # s03
    "woods": tuple(WOODS_PRINTS),                  # s04
    "guard_woods": GUARD_WOODS,                    # s04
    "river": RIVER_PRINTS,                         # s05
    "trail": FALSE_TRAIL,                          # s06
    "guard_ice": GUARD_ICE,                        # s07
    "rescue": RESCUE_PRINTS,                       # s10
    "escape": ESCAPE_PRINTS,                       # s11
    "guards": GUARDS_PRINTS,                       # s11
    "crossing": CROSSING_PRINTS,                   # s12
}
_ORDER = (("s02", ()), ("s03", ("fence",)), ("s04", ("guard_fence",)), ("s05", ("woods", "guard_woods")),
          ("s06", ("river",)), ("s07", ("trail",)), ("s08", ("guard_ice",)), ("s09", ()), ("s10", ()),
          ("s11", ("rescue",)), ("s12", ("escape", "guards")))


def prints_before(sid):
    """Every print laid before scene sid begins."""
    out = []
    for s, stages in _ORDER:
        for st in stages:
            out.extend(STAGES[st])
        if s == sid:
            break
    return tuple(out) if sid != "s01" else ()


def lay(prints, t, times):
    """The prints laid by time t, each at its time in `times`."""
    return [p for p, ti in zip(prints, times) if t >= ti]


def holes_before(sid):
    order = ["s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10", "s11", "s12"]
    i = order.index(sid)
    out = []
    if i > order.index("s05"):
        out.append("stone")
    if i > order.index("s08"):
        out.append("guard")
    return tuple(out)


# ============================================================================ the diorama camera
class Dio:
    """A cut-open view: (u, z) on the cut plane, d metres behind it, in one-point perspective
    from an eye `eye` m above z = 0 (the land's snow) and D m in front of the plane."""

    def __init__(self, u0, z0, ppm, eye=7.0, D=14.0):
        self.u0, self.z0, self.ppm, self.eye, self.D = float(u0), float(z0), float(ppm), float(eye), float(D)

    def f(self, d):
        return self.D / (self.D + max(d, -0.9 * self.D))

    def px(self, u, z, d=0.0):
        f = self.f(d)
        up = self.u0 + (u - self.u0) * f
        zp = self.eye + (z - self.eye) * f
        return (540.0 + (up - self.u0) * self.ppm, 960.0 - (zp - self.z0) * self.ppm)

    def scale(self, d=0.0):
        return self.ppm * self.f(d)

    def horizon_y(self):
        return 960.0 - (self.eye - self.z0) * self.ppm

    def u_at(self, x):
        return self.u0 + (x - 540.0) / self.ppm

    def z_at(self, y):
        return self.z0 + (960.0 - y) / self.ppm


def dio_lerp(a, b, u):
    ppm = math.exp(lerp(math.log(a.ppm), math.log(b.ppm), u))
    return Dio(lerp(a.u0, b.u0, u), lerp(a.z0, b.z0, u), ppm, lerp(a.eye, b.eye, u), lerp(a.D, b.D, u))


# ---------------------------------------------------------------------------- the river (looking west)
ICE_Z = -0.9                         # the ice's top
ICE_T = 0.38                         # white ice thickness
THIN_T = 0.09                        # the band's
SNOW_T = 0.05                        # snow on the white ice
LAND_SNOW = 0.45                     # the snow on the land, in the cut
SECTION_X = TRAIL_X                  # the cut plane


def bed_z(n):
    """The riverbed's depth at n (deepest under the current)."""
    if n <= RIVER[0] or n >= RIVER[1]:
        return ICE_Z
    u = (n - RIVER[0]) / (RIVER[1] - RIVER[0])
    return ICE_Z - 0.4 - 2.9 * math.sin(math.pi * u) ** 0.8 - 0.25 * math.sin(n * 1.7)


def land_z(n):
    """The ground's snow surface in the cut (z) at n: the land, the banks' slopes, the ice."""
    if n <= -BANK:
        return 0.0
    if n < RIVER[0]:
        u = (n + BANK) / BANK
        return lerp(0.0, ICE_Z, ease("inout", u))
    if n <= RIVER[1]:
        return ICE_Z + (0.0 if on_band(SECTION_X, n) else SNOW_T)
    if n < RIVER[1] + BANK:
        u = (n - RIVER[1]) / BANK
        return lerp(ICE_Z, 0.0, ease("inout", u))
    return 0.0


def slab_bottom(n):
    return ICE_Z - (THIN_T if on_band(SECTION_X, n) else ICE_T)


def draw_river(c, cam, t=0.0, moonlit=1.0, holes=(), sky=True, moon_at=None, farm_light=1.0, door=0.0,
               search=None, trunk=True, reeds_on=True, broken=None, prints_cut=(), stars_on=True, band_cut=True,
               far_trees=True):
    """The river, cut open through the false trail and seen from downstream (looking west, north to
    the right). holes: names in HOLES (cut into the slab where they cross the cut plane, and seen
    behind it). search: (x, n, r) the searchlight's patch on the ice upstream. broken: a function
    n -> (dz, tilt) for broken plates, or None. Draws everything except figures."""
    hy = cam.horizon_y()
    snow_c = lerp(K.SNOW_DIM, SNOW, moonlit)
    ice_c = lerp(K.ICE_DIM, ICE, moonlit)
    thin_c = lerp(lerp(THIN, NIGHT, 0.2), THIN, moonlit)
    shade_c = lerp(snow_c, SHADOW, 0.55)
    # ---- the sky
    if sky:
        K.fill(c, NIGHT)
        if stars_on:
            K.stars(c, t, y1=min(hy, 1920.0) - 30.0)
        mp = moon_at or (cam.px(RIVER[1] + 9.0, 0.0, 200.0)[0], hy - 0.28 * min(cam.ppm * 6.0, 600.0))
        K.moon(c, mp, r=clamp(cam.ppm * 1.1, 30.0, 90.0))
    # ---- the ground behind the cut, receding to the horizon along the river's banks
    K.poly(c, [(-50.0, hy - 1.0), (1130.0, hy - 1.0), (1130.0, 1970.0), (-50.0, 1970.0)], snow_c)
    ds = _depths()
    xs_ = [SECTION_X - d for d in ds]
    bs = [bank_s(x) for x in xs_]
    bn = [bank_n(x) for x in xs_]
    # the south slope (lit: it faces the moon) with a line of shade at its foot; the ice; the
    # north slope in shade
    foot = [cam.px(b, ICE_Z, d) for b, d in zip(bs, ds)] + [cam.px(b + 0.25, ICE_Z, d) for b, d in zip(bs, ds)][::-1]
    K.poly(c, [cam.px(b, ICE_Z, d) for b, d in zip(bn, ds)][::-1] + [cam.px(b, ICE_Z, d) for b, d in zip(bs, ds)], ice_c)
    K.poly(c, foot, lerp(ice_c, SHADOW, 0.6))
    K.poly(c, [cam.px(b, ICE_Z, d) for b, d in zip(bn, ds)] + [cam.px(b + BANK, 0.0, d) for b, d in zip(bn, ds)][::-1],
           shade_c)
    # the black band recedes upstream to its tip
    pts_l, pts_r = [], []
    for d, x in zip(ds, xs_):
        if x < BAND_X0:
            break
        tp = band_taper(x)
        mid = 0.5 * (band_lo(x) + band_hi(x))
        half = 0.5 * (band_hi(x) - band_lo(x)) * tp
        pts_l.append(cam.px(mid - half, ICE_Z, d))
        pts_r.append(cam.px(mid + half, ICE_Z, d))
    if len(pts_l) > 1:
        K.poly(c, pts_l + pts_r[::-1], thin_c)
    # holes seen behind the cut
    for h in holes:
        centre, r, seed = HOLES[h] if isinstance(h, str) else h
        d = SECTION_X - centre[0]
        if d > r:
            ring = [cam.px(centre[1] + r * math.cos(a) * 1.0, ICE_Z, d + r * math.sin(a))
                    for a in [6.283 * i / 20 for i in range(20)]]
            K.poly(c, ring, WATER)
    if search is not None:
        sx, sn, sr = search
        d = SECTION_X - sx
        ring = [cam.px(sn + sr * 1.3 * math.cos(a), ICE_Z, d + sr * math.sin(a)) for a in [6.283 * i / 28 for i in range(28)]]
        K.poly(c, ring, PAPER, 0.75)
    # far trees along both shores, and the farmhouse on the north side
    if far_trees:
        _far_trees(c, cam, hy, moonlit)
    _farmhouse_far(c, cam, farm_light, door)
    # the reeds, behind the cut on the south bank
    if reeds_on:
        _reeds_side(c, cam, moonlit)
    # ---- the cut face
    _cut_face(c, cam, holes, broken, thin_c, band_cut)
    if trunk:
        draw_trunk_side(c, cam)


@lru_cache(maxsize=1)
def _depths():
    """Depths behind the cut for receding outlines: dense near, sparse far (to 600 m)."""
    return tuple(600.0 * (i / 90.0) ** 2.2 for i in range(91))


def _cut_face(c, cam, holes, broken, thin_c, band_cut=True):
    """The front of the diorama: earth, the snow on the land, the slab, the water."""
    u_l, u_r = cam.u_at(-60.0), cam.u_at(1140.0)
    lo_z = cam.z_at(2000.0)
    ns = [u_l + (u_r - u_l) * i / 220.0 for i in range(221)]
    # earth (everything below the land's snow and the riverbed)
    top = [(n, (land_z(n) - (LAND_SNOW if (n <= -BANK or n >= RIVER[1] + BANK) else 0.0)) if not (RIVER[0] <= n <= RIVER[1])
            else bed_z(n)) for n in ns]
    K.poly(c, [cam.px(n, z) for n, z in top] + [cam.px(u_r, lo_z), cam.px(u_l, lo_z)], INK)
    # the snow layer on the land, in the cut
    for side in ((u_l, -BANK), (RIVER[1] + BANK, u_r)):
        a, b = side
        if b <= a:
            continue
        xs = [a + (b - a) * i / 30.0 for i in range(31)]
        K.poly(c, [cam.px(n, 0.0) for n in xs] + [cam.px(n, -LAND_SNOW) for n in xs[::-1]], SHADOW)
    # the banks' slopes in the cut: snow over earth
    for a, b in ((-BANK, RIVER[0]), (RIVER[1], RIVER[1] + BANK)):
        xs = [a + (b - a) * i / 20.0 for i in range(21)]
        K.poly(c, [cam.px(n, land_z(n)) for n in xs] + [cam.px(n, land_z(n) - 0.3) for n in xs[::-1]], SHADOW)
    # the water under the ice
    xs = [RIVER[0] + (RIVER[1] - RIVER[0]) * i / 120.0 for i in range(121)]
    K.poly(c, [cam.px(n, ICE_Z) for n in xs] + [cam.px(n, bed_z(n)) for n in xs[::-1]], WATER)
    # the slab: white ice either side, the black band thin between (holes cut out of it)
    gaps = []
    for h in holes:
        centre, r, seed = HOLES[h] if isinstance(h, str) else h
        dx = abs(SECTION_X - centre[0])
        if dx < r:
            half = math.sqrt(r * r - dx * dx)
            gaps.append((centre[1] - half, centre[1] + half))
    runs = _runs(RIVER[0], RIVER[1], gaps)
    face_white = lerp(ICE, INK, 0.28)
    for a, b in runs:
        m = max(4, int((b - a) / 0.12))
        xs = [a + (b - a) * i / m for i in range(m + 1)]
        tops, bots, snows = [], [], []
        for n in xs:
            dz, tilt = broken(n) if broken else (0.0, 0.0)
            tops.append((n, ICE_Z + dz))
            bots.append((n, slab_bottom(n) + dz))
        poly_ = [cam.px(n, z) for n, z in tops] + [cam.px(n, z) for n, z in bots[::-1]]
        K.poly(c, poly_, face_white)
        # the band's thin slab, darker
        if band_cut:
            bl = [i for i, n in enumerate(xs) if on_band(SECTION_X, n)]
            if bl:
                i0, i1 = bl[0], bl[-1]
                seg = [cam.px(*tops[i]) for i in range(i0, i1 + 1)] + [cam.px(*bots[i]) for i in range(i1, i0 - 1, -1)]
                K.poly(c, seg, thin_c)
        # the snow on the white ice
        wl = [(n, z) for (n, z) in tops if not on_band(SECTION_X, n)]
        if wl:
            runs2 = []
            cur = [wl[0]]
            for p, q in zip(wl, wl[1:]):
                if q[0] - p[0] > 0.2:
                    runs2.append(cur)
                    cur = [q]
                else:
                    cur.append(q)
            runs2.append(cur)
            for r_ in runs2:
                if len(r_) >= 2:
                    K.poly(c, [cam.px(n, z + SNOW_T) for n, z in r_] + [cam.px(n, z) for n, z in r_[::-1]], SNOW)


def _runs(a, b, gaps):
    out = []
    cur = a
    for g0, g1 in sorted(gaps):
        if g0 > cur:
            out.append((cur, min(g0, b)))
        cur = max(cur, g1)
    if cur < b:
        out.append((cur, b))
    return out


@lru_cache(maxsize=1)
def _far_tree_list():
    out = []
    for i in range(80):
        side = -1 if i % 2 == 0 else 1
        n = (-2.0 - 2.0 - 30.0 * hash01(i, 1)) if side < 0 else (RIVER[1] + 3.0 + 25.0 * hash01(i, 1))
        d = 20.0 + 160.0 * hash01(i, 2) ** 0.7
        h = 8.0 + 8.0 * hash01(i, 3)
        out.append((n, d, h, i))
    return tuple(sorted(out, key=lambda r: -r[1]))


def spruce_side(c, base, h, w, color, seed=0, snow=None, snow_alpha=1.0):
    """A spruce in profile at `base` (px), h px tall, w px wide: stacked drooping tiers on a trunk."""
    tiers = 6
    trunk = [(base[0] - w * 0.05, base[1]), (base[0] + w * 0.05, base[1]), (base[0] + w * 0.03, base[1] - h),
             (base[0] - w * 0.03, base[1] - h)]
    ps = [trunk]
    caps = []
    for i in range(tiers):
        u0 = 0.18 + 0.82 * i / tiers
        u1 = 0.18 + 0.82 * (i + 1.6) / tiers
        y0 = base[1] - h * u0
        y1 = base[1] - h * min(1.0, u1)
        ww = w * 0.5 * (1.0 - 0.8 * i / tiers) * (0.92 + 0.16 * hash01(seed, i))
        tier = [(base[0] - ww, y0 + h * 0.02), (base[0], y1), (base[0] + ww, y0 + h * 0.02),
                (base[0] + ww * 0.55, y0 - h * 0.025), (base[0] - ww * 0.5, y0 - h * 0.02)]
        ps.append(tier)
        if snow is not None:
            caps.append([(base[0] - ww * 0.7, y0 - h * 0.03 + (y1 - y0) * 0.25), (base[0], y1 + h * 0.01),
                         (base[0] + ww * 0.7, y0 - h * 0.03 + (y1 - y0) * 0.25),
                         (base[0] + ww * 0.4, y0 - h * 0.035 + (y1 - y0) * 0.32),
                         (base[0] - ww * 0.4, y0 - h * 0.035 + (y1 - y0) * 0.32)])
    K.polys(c, ps, color)
    if caps:
        K.polys(c, caps, snow, snow_alpha)


def _far_trees(c, cam, hy, moonlit):
    for (n, d, h, i) in _far_tree_list():
        base = cam.px(n, 0.0, d)
        if base[1] < hy - 2 or base[0] < -200 or base[0] > 1280:
            continue
        sc = cam.scale(d)
        col = lerp(lerp(STEEL, INK, 0.5), STEEL, clamp(d / 180.0))
        spruce_side(c, base, h * sc, h * 0.42 * sc, col, seed=i)


def _farmhouse_far(c, cam, light=1.0, door=0.0):
    """The farmhouse across the river, upstream: a small house on the far bank, its window lit."""
    d = SECTION_X - FARM[0]
    n = FARM[1] - 3.0
    base = cam.px(n, 0.0, d)
    sc = cam.scale(d)
    w, h, roof = 9.0 * sc, 3.2 * sc, 2.6 * sc
    x, y = base
    col = lerp(INK, STEEL, 0.25)
    K.poly(c, [(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h), (x - w / 2, y - h)], col)
    K.poly(c, [(x - w / 2 - 0.4 * sc, y - h), (x + w / 2 + 0.4 * sc, y - h), (x + w * 0.12, y - h - roof),
               (x - w * 0.12, y - h - roof)], col)
    K.poly(c, [(x + w * 0.2, y - h - roof * 0.6), (x + w * 0.3, y - h - roof * 0.6), (x + w * 0.3, y - h - roof * 1.25),
               (x + w * 0.2, y - h - roof * 1.25)], col)
    if light > 0.0:
        wx, wy = x - w * 0.22, y - h * 0.55
        ws = 0.55 * sc
        K.poly(c, [(wx - ws, wy - ws), (wx + ws, wy - ws), (wx + ws, wy + ws), (wx - ws, wy + ws)], AMBER, light)
        K.glow(c, (wx, wy), 3.0 * sc, 0.6 * light)
    if door > 0.0:
        dx, dy = x + w * 0.22, y
        dw, dh = 0.55 * sc, 2.1 * sc
        K.poly(c, [(dx - dw, dy), (dx + dw, dy), (dx + dw, dy - dh), (dx - dw, dy - dh)], AMBER, door)


@lru_cache(maxsize=1)
def _reed_side_list():
    out = []
    for i in range(70):
        n = REEDS[2] + (REEDS[3] - REEDS[2]) * hash01(i, 1)
        d = SECTION_X - (REEDS[0] + (REEDS[1] - REEDS[0]) * hash01(i, 2))
        h = 0.9 + 0.7 * hash01(i, 3)
        out.append((n, d, h, i))
    return tuple(sorted(out, key=lambda r: -r[1]))


def _reeds_side(c, cam, moonlit):
    for (n, d, h, i) in _reed_side_list():
        base = cam.px(n, land_z(n), d)
        sc = cam.scale(d)
        top = (base[0] + 0.12 * sc * K._sn(i, 4), base[1] - h * sc)
        col = lerp(INK, STEEL, 0.15 * clamp(d / 10.0))
        K.band(c, [base, top], col, max(1.2, 0.035 * sc), seed=i, taper=(1.0, 0.3))
        if i % 3 == 0:                       # a seed head
            K.ellipse(c, (top[0], top[1] + 0.08 * sc), max(1.0, 0.035 * sc), max(2.0, 0.12 * sc), col)


def trunk_side_pts():
    """The fallen trunk on the cut plane (u = n, z): from the root plate on the bank down the slope
    onto the ice; returns (top polyline, bottom polyline)."""
    (x0, n0), (x1, n1) = TRUNK
    m = 30
    top, bot = [], []
    for i in range(m + 1):
        u = i / m
        n = lerp(n0, n1, u)
        r = 0.5 * lerp(TRUNK_W[0], TRUNK_W[1], u)
        g = max(land_z(n), ICE_Z + SNOW_T) if n > RIVER[0] else land_z(n)
        zc = g + r * 0.85
        top.append((n, zc + r))
        bot.append((n, zc - r))
    return top, bot


def trunk_top_z(n):
    """The height of the trunk's upper surface at n (where a foot or a crawling body rests)."""
    top, _ = trunk_side_pts()
    for (na, za), (nb, zb) in zip(top, top[1:]):
        if na <= n <= nb:
            return lerp(za, zb, (n - na) / (nb - na))
    return top[0][1] if n < top[0][0] else top[-1][1]


def draw_trunk_side(c, cam, color=INK):
    top, bot = trunk_side_pts()
    d = SECTION_X - 0.5 * (TRUNK[0][0] + TRUNK[1][0])
    K.poly(c, [cam.px(n, z, d) for n, z in top] + [cam.px(n, z, d) for n, z in bot[::-1]], color)
    # the root plate: a ragged disc standing up at the root end
    n0 = TRUNK[0][1]
    zc = land_z(n0) + 0.9
    pts = []
    for i in range(22):
        a = 6.283 * i / 22
        rr = 1.15 * (1.0 + 0.18 * K._sn(i, 51))
        pts.append(cam.px(n0 - 0.25 + 0.35 * rr * math.cos(a), zc + rr * math.sin(a), d))
    K.poly(c, pts, color)
    # roots trailing into the snow
    for j in range(5):
        a = math.radians(200.0 + 35.0 * j)
        p0 = cam.px(n0 - 0.25 + 0.3 * math.cos(a), zc + 1.0 * math.sin(a), d)
        p1 = cam.px(n0 - 0.25 + 0.55 * math.cos(a), zc + 1.5 * math.sin(a), d)
        K.band(c, [p0, p1], color, max(1.5, 0.05 * cam.scale(d)), seed=60 + j, taper=(1.0, 0.2))
    # stubs
    for j, (u, ln, ang) in enumerate(((0.2, 0.5, 70.0), (0.36, 0.7, 110.0), (0.55, 0.45, 60.0),
                                      ((STUB_N - TRUNK[0][1]) / (TRUNK[1][1] - TRUNK[0][1]), 0.42, 75.0), (0.88, 0.3, 120.0))):
        n = lerp(TRUNK[0][1], TRUNK[1][1], u)
        z = trunk_top_z(n)
        a = math.radians(ang)
        K.band(c, [cam.px(n, z - 0.05, d), cam.px(n + ln * math.cos(a), z + ln * math.sin(a), d)], color,
               max(1.5, 0.07 * cam.scale(d)), seed=70 + j, taper=(1.0, 0.35))


def stub_point():
    """The tip of the branch stub near the trunk's end (u = n, z): her boot hooks behind it."""
    u = (STUB_N - TRUNK[0][1]) / (TRUNK[1][1] - TRUNK[0][1])
    n = lerp(TRUNK[0][1], TRUNK[1][1], u)
    a = math.radians(75.0)
    return (n + 0.42 * math.cos(a), trunk_top_z(n) + 0.42 * math.sin(a))


# ---------------------------------------------------------------------------- the woods (looking west)
@lru_cache(maxsize=1)
def _wood_trees():
    """Trees behind the cut in the woods view: (u, d, height, seed), u spanning the whole path."""
    out = []
    for i in range(900):
        u = -135.0 + 135.0 * hash01(i, 1)
        d = 1.5 + 70.0 * hash01(i, 2) ** 1.35
        h = 10.0 + 8.0 * hash01(i, 3)
        out.append((u, d, h, i))
    return tuple(sorted(out, key=lambda r: -r[1]))


def snow_depth(n):
    """The snow's depth in the woods' cut at n (deep drifts here and there; a deep one at the
    stumble)."""
    base = 0.5 + 0.12 * math.sin(n * 0.37) + 0.08 * math.sin(n * 1.1 + 1.0)
    drift = 0.45 * math.exp(-((n - STUMBLE[1]) / 2.2) ** 2)
    return base + drift


def draw_woods(c, cam, t=0.0, moonlit=1.0, sky=True, search=None, prints_cut=(), stars_on=True, near=True):
    """The woods, cut open along the path and seen from the east (looking west, north to the
    right): the night sky, far treelines, trunks receding, the snow in the cut. search: a function
    of t giving (u, d, r) for the searchlight's patch, or None."""
    hy = cam.horizon_y()
    snow_c = lerp(K.SNOW_DIM, SNOW, moonlit)
    if sky:
        K.fill(c, NIGHT)
        if stars_on:
            K.stars(c, t, y1=min(hy, 1920.0) - 30.0)
    K.poly(c, [(-50.0, hy - 1.0), (1130.0, hy - 1.0), (1130.0, 1970.0), (-50.0, 1970.0)], snow_c)
    u_l, u_r = cam.u_at(-80.0), cam.u_at(1160.0)
    shade_c = lerp(snow_c, SHADOW, 0.55)
    if search is not None:
        su, sd, sr = search
        ring = [cam.px(su + sr * 1.4 * math.cos(q), 0.0, sd + sr * math.sin(q)) for q in [6.283 * i / 28 for i in range(28)]]
        K.poly(c, ring, PAPER, 0.8)
    # the trees: far ones are STEEL spruces at the horizon, near ones INK trunks; each casts a
    # moon shadow south (to the left) along the ground
    for (u, d, h, i) in _wood_trees():
        base = cam.px(u, 0.0, d)
        sc = cam.scale(d)
        if base[0] < -400 or base[0] > 1480 or base[1] < hy - 4:
            continue
        col = lerp(INK, STEEL, clamp((d - 4.0) / 60.0) * 0.9)
        if d > 18.0:
            spruce_side(c, base, h * sc, h * 0.4 * sc, col, seed=i)
            continue
        w = (0.28 + 0.12 * hash01(i, 4)) * sc
        L = h * SHADOW_K * 0.55
        sh = [cam.px(u - 0.1, 0.0, d - w / sc * 0.5), cam.px(u + 0.1, 0.0, d + w / sc * 0.5),
              cam.px(u - L, 0.0, d + 0.6), cam.px(u - L, 0.0, d - 0.6)]
        K.poly(c, sh, shade_c, 0.8)
    for (u, d, h, i) in _wood_trees():
        base = cam.px(u, 0.0, d)
        sc = cam.scale(d)
        if d > 18.0 or base[0] < -200 or base[0] > 1280 or base[1] < hy - 4:
            continue
        col = lerp(INK, STEEL, clamp((d - 4.0) / 60.0) * 0.9)
        w = (0.28 + 0.12 * hash01(i, 4)) * sc
        lean = 0.025 * K._sn(i, 6) * h * sc
        top = base[1] - h * sc
        K.poly(c, [(base[0] - w / 2, base[1] + 2), (base[0] + w / 2, base[1] + 2), (base[0] + w * 0.35 + lean, top),
                   (base[0] - w * 0.35 + lean, top)], col)
        # snow caught on the trunk's north side (to the right)
        K.poly(c, [(base[0] + w * 0.12, base[1] - 0.3 * sc), (base[0] + w / 2, base[1] - 0.3 * sc),
                   (base[0] + w * 0.38 + lean * 0.4, base[1] - h * sc * 0.45),
                   (base[0] + w * 0.22 + lean * 0.4, base[1] - h * sc * 0.43)], lerp(snow_c, col, 0.35), 0.8)
        # a few drooping dead branches low on the trunk
        for j in range(3):
            by = base[1] - (0.35 + 0.12 * j + 0.05 * hash01(i, j, 7)) * h * sc
            bl = (0.8 + 0.7 * hash01(i, j, 5)) * sc
            sgn = 1 if (i + j) % 2 else -1
            bx = base[0] + lean * (base[1] - by) / max(h * sc, 1.0)
            K.band(c, [(bx, by), (bx + sgn * bl, by + 0.3 * sc), (bx + sgn * bl * 1.2, by + 0.55 * sc)], col,
                   max(1.5, 0.06 * sc), seed=i * 5 + j, taper=(1.0, 0.2))
        # a snow cushion at the foot
        K.ellipse(c, (base[0] + w * 0.3, base[1]), w * 0.9, max(2.0, 0.08 * sc), lerp(snow_c, PAPER, 0.25))
    # the cut: snow over earth
    ns = [u_l + (u_r - u_l) * i / 160.0 for i in range(161)]
    lo_z = cam.z_at(2000.0)
    K.poly(c, [cam.px(n, 0.0) for n in ns] + [cam.px(u_r, lo_z), cam.px(u_l, lo_z)], INK)
    K.poly(c, [cam.px(n, 0.0) for n in ns] + [cam.px(n, -snow_depth(n)) for n in ns[::-1]], SHADOW)


def woods_ground(n):
    """z of the snow surface in the woods' cut (always 0: the cut follows the surface)."""
    return 0.0


# ============================================================================ the fence view (looking north)
class FenceCam:
    """The fence view's camera: a composed set in frame px, pushed in by `zoom` about `focus`
    (frame px) and panned by (dx, dy) px. Layers move with parallax: far 0.2, the zone 0.5, the
    fence 1.0, the drift 1.3."""

    def __init__(self, zoom=1.0, focus=(540.0, 1300.0), dx=0.0, dy=0.0):
        self.zoom, self.focus, self.dx, self.dy = float(zoom), focus, float(dx), float(dy)

    def xf(self, p, par=1.0):
        z = 1.0 + (self.zoom - 1.0) * par
        fx, fy = self.focus
        return (fx + (p[0] - fx) * z + self.dx * par, fy + (p[1] - fy) * z + self.dy * par)

    def s(self, par=1.0):
        return 1.0 + (self.zoom - 1.0) * par


FENCE_Y = 1240.0            # the foot of the fence (frame px at zoom 1)
FENCE_TOP = 640.0           # the posts' tops
WIRES = (690.0, 820.0, 950.0, 1080.0, 1185.0)     # the five strands (the lowest is the one she lifts)
POSTS = (-80.0, 300.0, 780.0, 1160.0)             # post x (the gap is between 300 and 780)
HORIZON_FENCE = 610.0       # the woods' line beyond the zone
TOWER_X = 190.0             # the tower's foot (zone layer)
HUT_X = 900.0               # the guardhouse (zone layer)
MOON_FENCE = (790.0, 300.0)


def wire_y(i, x, lift=0.0, lift_x=540.0):
    """Strand i's y at frame x (zoom 1): a slight sag between posts; lift (px) raises the bottom
    strand near lift_x (her hand)."""
    y = WIRES[i]
    sag = 0.0
    for a, b in zip(POSTS, POSTS[1:]):
        if a <= x <= b:
            u = (x - a) / (b - a)
            sag = 18.0 * math.sin(math.pi * u)
    y += sag
    if i == len(WIRES) - 1 and lift:
        y -= lift * math.exp(-((x - lift_x) / 150.0) ** 2)
    return y


def draw_fence(c, t, cam=None, moonlit=1.0, search=None, lift=0.0, lift_x=540.0, tower_lamp=0.0, hut_light=1.0,
               scrap=None, stars_on=True, drift=True, moon_out=1.0, posts_shadow=None, under=None, mid=None):
    """The fence view. search: (x, y, rx) of the searchlight's lit patch on the zone's snow (frame
    px at zoom 1) or None; tower_lamp: the lamp's beam angle (deg, 0 = straight down the zone).
    lift: the bottom wire lifted (px). scrap: (x, y) the scrap of coat on the barb, or None.
    moon_out 0..1: the cloud slides off the moon. posts_shadow: 0..1 length of the posts' long
    moon shadows toward the camera. under(c) draws on the zone, behind the posts and wires (the
    far side of the fence); mid(c) between the wires and the drift (this side of the fence)."""
    cam = cam or FenceCam()
    snow_c = lerp(K.SNOW_DIM, SNOW, moonlit)
    far_snow = lerp(snow_c, STEEL, 0.25)
    # sky
    K.fill(c, NIGHT)
    if stars_on:
        K.stars(c, t, y1=560.0, dx=cam.dx * 0.1, dy=cam.dy * 0.1)
    mp = cam.xf(MOON_FENCE, 0.05)
    K.moon(c, mp, r=62.0 * cam.s(0.05))
    if moon_out < 1.0:
        K.cloud(c, (mp[0] - 520.0 * ease("inout", moon_out) + 30.0, mp[1] + 32.0 * cam.s(0.05)), 560.0 * cam.s(0.05),
                120.0 * cam.s(0.05), lerp(NIGHT, STEEL, 0.55), seed=4)
    # the zone's snow up to the woods
    hz = cam.xf((0.0, HORIZON_FENCE), 0.2)[1]
    K.poly(c, [(-50.0, hz), (1130.0, hz), (1130.0, 1970.0), (-50.0, 1970.0)], far_snow)
    # the woods' line (far)
    for i in range(46):
        x = -80.0 + 27.0 * i + 10.0 * K._sn(i, 3)
        h = 70.0 + 50.0 * hash01(i, 4)
        b = cam.xf((x, HORIZON_FENCE + 8.0), 0.2)
        spruce_side(c, b, h * cam.s(0.2), h * 0.45 * cam.s(0.2), lerp(STEEL, INK, 0.25), seed=i)
    # the zone's nearer snow, brighter
    zy = cam.xf((0.0, 820.0), 0.5)[1]
    K.poly(c, [(-50.0, zy), (1130.0, zy), (1130.0, 1970.0), (-50.0, 1970.0)], snow_c)
    if search is not None:
        sx, sy, sr = search
        p = cam.xf((sx, sy), 0.5)
        K.lit_patch(c, p, sr * cam.s(0.5), sr * 0.28 * cam.s(0.5))
    # the tower (zone layer)
    _tower_side(c, cam, tower_lamp)
    # the guardhouse
    _hut_side(c, cam, hut_light)
    # long shadows of the posts toward us
    if posts_shadow:
        for x in POSTS:
            a = cam.xf((x, FENCE_Y), 1.0)
            b = cam.xf((x + 40.0, FENCE_Y + 700.0 * posts_shadow), 1.15)
            K.poly(c, [(a[0] - 9 * cam.s(), a[1]), (a[0] + 9 * cam.s(), a[1]), (b[0] + 16 * cam.s(1.15), b[1]),
                       (b[0] - 16 * cam.s(1.15), b[1])], lerp(snow_c, SHADOW, 0.85))
    if under is not None:
        under(c)
    # the fence
    for x in POSTS:
        top = cam.xf((x, FENCE_TOP), 1.0)
        bot = cam.xf((x, FENCE_Y + 10.0), 1.0)
        w = 26.0 * cam.s()
        K.poly(c, [(bot[0] - w / 2, bot[1]), (bot[0] + w / 2, bot[1]), (top[0] + w * 0.4, top[1]),
                   (top[0] - w * 0.4, top[1])], INK)
        # the angled top arm
        K.band(c, [top, cam.xf((x - 40.0, FENCE_TOP - 50.0), 1.0)], INK, 16.0 * cam.s(), seed=int(x))
    for i in range(len(WIRES)):
        xs = [-80.0 + 1240.0 * j / 80.0 for j in range(81)]
        pts = [cam.xf((x, wire_y(i, x, lift, lift_x)), 1.0) for x in xs]
        K.band(c, pts, INK, 4.5 * cam.s(), seed=100 + i)
        # barbs every ~48 px
        for j, x in enumerate(range(-60, 1180, 48)):
            p = cam.xf((x + 12.0 * K._sn(i, j), wire_y(i, x, lift, lift_x)), 1.0)
            s = 9.0 * cam.s()
            K.band(c, [(p[0] - s, p[1] - s), (p[0] + s, p[1] + s)], INK, 3.4 * cam.s(), seed=j)
            K.band(c, [(p[0] - s, p[1] + s), (p[0] + s, p[1] - s)], INK, 3.4 * cam.s(), seed=j + 7)
    if scrap is not None:
        p = cam.xf(scrap, 1.0)
        s = cam.s()
        flut = 6.0 * math.sin(t * 7.0) * s
        K.poly(c, [(p[0] - 6 * s, p[1]), (p[0] + 30 * s, p[1] + 6 * s + flut), (p[0] + 22 * s, p[1] + 34 * s + flut),
                   (p[0] - 2 * s, p[1] + 22 * s)], INK)
    if mid is not None:
        mid(c)
    # the drift in front (where they crouch)
    if drift:
        K.poly(c, drift_poly(cam), lerp(snow_c, PAPER, 0.18))


def drift_y(x):
    """The drift's crest (frame y at zoom 1, drift layer) at frame x."""
    return 1500.0 - 120.0 * math.exp(-((x - 430.0) / 260.0) ** 2) - 30.0 * math.sin(x * 0.01)


def drift_poly(cam):
    pts = [cam.xf((x, drift_y(x)), 1.3) for x in (-60.0 + 1200.0 * j / 40.0 for j in range(41))]
    return pts + [cam.xf((1140.0, 2100.0), 1.3), cam.xf((-60.0, 2100.0), 1.3)]


def tower_lamp_px(cam):
    return cam.xf((TOWER_X + 10.0, 330.0), 0.5)


def _tower_side(c, cam, lamp_ang=0.0):
    col = lerp(INK, STEEL, 0.2)
    s = cam.s(0.5)
    foot = cam.xf((TOWER_X, 840.0), 0.5)
    top = cam.xf((TOWER_X, 380.0), 0.5)
    w0, w1 = 120.0 * s, 70.0 * s
    for sgn in (-1, 1):
        K.band(c, [(foot[0] + sgn * w0 / 2, foot[1]), (top[0] + sgn * w1 / 2, top[1])], col, 9.0 * s, seed=3 + sgn)
    for j in range(4):
        u0, u1 = j / 4.0, (j + 1) / 4.0
        y0, y1 = lerp(foot[1], top[1], u0), lerp(foot[1], top[1], u1)
        wa, wb = lerp(w0, w1, u0), lerp(w0, w1, u1)
        K.band(c, [(foot[0] - wa / 2, y0), (foot[0] + wb / 2, y1)], col, 5.0 * s, seed=10 + j)
        K.band(c, [(foot[0] + wa / 2, y0), (foot[0] - wb / 2, y1)], col, 5.0 * s, seed=20 + j)
    cab = [(top[0] - 62 * s, top[1]), (top[0] + 62 * s, top[1]), (top[0] + 56 * s, top[1] - 70 * s),
           (top[0] - 56 * s, top[1] - 70 * s)]
    K.poly(c, cab, col)
    K.poly(c, [(top[0] - 76 * s, top[1] - 70 * s), (top[0] + 76 * s, top[1] - 70 * s), (top[0] + 30 * s, top[1] - 104 * s),
               (top[0] - 30 * s, top[1] - 104 * s)], col)
    # the lamp on the rail
    lp = tower_lamp_px(cam)
    K.disc(c, lp, 16.0 * s, col)
    K.disc(c, (lp[0] + 6 * s, lp[1] + 4 * s), 9.0 * s, PAPER)


def _hut_side(c, cam, light=1.0):
    col = lerp(INK, STEEL, 0.2)
    s = cam.s(0.5)
    b = cam.xf((HUT_X, 860.0), 0.5)
    w, h, r = 200.0 * s, 110.0 * s, 70.0 * s
    K.poly(c, [(b[0] - w / 2, b[1]), (b[0] + w / 2, b[1]), (b[0] + w / 2, b[1] - h), (b[0] - w / 2, b[1] - h)], col)
    K.poly(c, [(b[0] - w / 2 - 14 * s, b[1] - h), (b[0] + w / 2 + 14 * s, b[1] - h), (b[0], b[1] - h - r)], col)
    K.poly(c, [(b[0] + 40 * s, b[1] - h - 30 * s), (b[0] + 58 * s, b[1] - h - 30 * s), (b[0] + 58 * s, b[1] - h - 80 * s),
               (b[0] + 40 * s, b[1] - h - 80 * s)], col)
    if light > 0.0:
        wx, wy = b[0] - 40 * s, b[1] - h * 0.55
        ws = 22.0 * s
        K.poly(c, [(wx - ws, wy - ws * 0.8), (wx + ws, wy - ws * 0.8), (wx + ws, wy + ws * 0.8), (wx - ws, wy + ws * 0.8)],
               AMBER, light)
        K.glow(c, (wx, wy), 90.0 * s, 0.6 * light)
