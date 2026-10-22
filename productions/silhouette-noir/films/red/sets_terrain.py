"""RED sets: terrain. Walkable snow surfaces with exact ground functions.

World coords, y DOWN, zoom-1 px (adult ~600 px, the girl ~380, the wolf ~330 at the shoulder).

Every terrain answers, for any float x or numpy array of x:

    ground_y(x)   FIRM footing: where feet and paws are planted (IK target)
    snow_y(x)     visible top of the snow (= ground_y - depth(x); equal on packed paths)
    depth(x)      snow depth above the footing (0 on packed paths, ~90 px in the ridge drifts)
    slope(x)      d ground_y / dx  (+ = descending to the right, since y is down)
    angle(x)      surface tilt in degrees (atan of slope), for foot pitch
    normal(x)     unit normal pointing up out of the ground
    point(x, lift=0) -> (x, ground_y(x) - lift)

Draw order on the action plane:  terrain.draw_back(...)  ->  characters  ->  terrain.draw_front(...)
(draw_front is the snow lip in front of the legs: it hides whatever is below snow_y, which is
how the girl wades knee-deep on the ridge and how feet sink a little into fresh snow).

Segments (one coordinate system each):
    PATH      the village street (x < 0) and, through the gate at x = 0, the trail that
              descends through the forest (x > 0, endless). VILLAGE_STREET is the same object.
    RIDGE     S05/S06: leaves the trail at x = 0 and climbs through deep snow to the crest
              at RIDGE.crest_x, then drops away into the valley.
    CLEARING  S07-S09, S11: the cottage door is at x = 0; flat in front of the cottage, the
              approach (the lantern path in S11) climbs from the lower left.
"""
import math

import numpy as np

from engine import draw
from engine.core import clamp, smoothstep, hash01
from .sets_common import (get_mood, mix, INK, SNOW, view, srnd, rnd, plane)


def _sstep(e0, e1, x):
    """Vectorized smoothstep."""
    t = np.clip((np.asarray(x, dtype=float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _scalar_or(x, v):
    return float(v) if np.ndim(x) == 0 else v


class Terrain:
    """Base class. Subclasses define `_slope_raw(x)` (vectorized dy/dx of the large-scale
    profile), `_bumps(x)` / `_dbumps(x)` (small analytic undulations) and `_depth(x)`.
    The large-scale profile is integrated once into a table (cached), so ground_y is exact,
    smooth and cheap for scalars and arrays."""

    name = "terrain"
    y0 = 1500.0          # ground_y at x = x_ref (before bumps)
    x_ref = 0.0
    table = (-6000.0, 60000.0, 4.0)     # x range and step of the integrated profile

    def __init__(self):
        a, b, h = self.table
        xs = np.arange(a, b + h, h, dtype=float)
        s = self._slope_raw(xs)
        y = np.concatenate([[0.0], np.cumsum(0.5 * (s[1:] + s[:-1]) * h)])
        y -= np.interp(self.x_ref, xs, y)
        self._xs, self._y, self._s = xs, y + self.y0, s
        self._h = h

    # ------------------------------------------------------------ profile pieces
    def _slope_raw(self, x):
        return np.zeros_like(np.asarray(x, dtype=float))

    def _bumps(self, x):
        return np.zeros_like(np.asarray(x, dtype=float))

    def _dbumps(self, x):
        return np.zeros_like(np.asarray(x, dtype=float))

    def _depth(self, x):
        return np.zeros_like(np.asarray(x, dtype=float))

    def _profile(self, x):
        x = np.asarray(x, dtype=float)
        xs, y = self._xs, self._y
        out = np.interp(x, xs, y)
        lo, hi = x < xs[0], x > xs[-1]
        if lo.any():
            out = np.where(lo, y[0] + (x - xs[0]) * self._s[0], out)
        if hi.any():
            out = np.where(hi, y[-1] + (x - xs[-1]) * self._s[-1], out)
        return out

    # ------------------------------------------------------------ public
    def ground_y(self, x):
        """Firm footing y at x (plant feet / paws here)."""
        v = self._profile(x) + self._bumps(x)
        return _scalar_or(x, v)

    def depth(self, x):
        """Snow depth above the footing (>= 0)."""
        return _scalar_or(x, np.maximum(self._depth(x), 0.0))

    def snow_y(self, x):
        """Visible top of the snow at x (<= ground_y)."""
        return _scalar_or(x, self._profile(x) + self._bumps(x) - np.maximum(self._depth(x), 0.0))

    def slope(self, x):
        """d ground_y / dx (+ = going down to the right)."""
        xa = np.asarray(x, dtype=float)
        s = np.interp(xa, self._xs, self._s) + self._dbumps(xa)
        return _scalar_or(x, s)

    def angle(self, x):
        """Surface tilt in degrees (positive = descending to the right)."""
        return _scalar_or(x, np.degrees(np.arctan(self.slope(x))))

    def normal(self, x):
        s = float(self.slope(x))
        L = math.hypot(s, 1.0)
        return (s / L, -1.0 / L)

    def point(self, x, lift=0.0):
        """(x, ground_y(x) - lift): a point `lift` px above the footing."""
        return (float(x), float(self.ground_y(x)) - lift)

    def snow_point(self, x, lift=0.0):
        return (float(x), float(self.snow_y(x)) - lift)

    def rest(self, x0, x1, n=9):
        """Resting pose of a rigid object spanning x0..x1 laid on the snow surface:
        returns (cx, cy, angle_deg) of the chord touching the two highest support points."""
        xs = np.linspace(x0, x1, n)
        ys = np.asarray(self.snow_y(xs))
        mid = n // 2
        ia = int(np.argmin(ys[:mid + 1]))
        ib = mid + int(np.argmin(ys[mid:]))
        ax, ay, bx, by = xs[ia], ys[ia], xs[ib], ys[ib]
        if bx - ax < 1e-6:
            return (float((x0 + x1) / 2), float(ys.min()), 0.0)
        ang = math.degrees(math.atan2(by - ay, bx - ax))
        cx = (x0 + x1) / 2
        cy = ay + (by - ay) * (cx - ax) / (bx - ax)
        return (float(cx), float(cy), ang)

    def x_for_y(self, y, x0, x1, n=400):
        """First x in [x0, x1] where ground_y crosses y (or None)."""
        xs = np.linspace(x0, x1, n)
        ys = np.asarray(self.ground_y(xs)) - y
        idx = np.where(np.sign(ys[:-1]) != np.sign(ys[1:]))[0]
        if len(idx) == 0:
            return None
        i = int(idx[0])
        u = ys[i] / (ys[i] - ys[i + 1])
        return float(xs[i] + (xs[i + 1] - xs[i]) * u)

    # ------------------------------------------------------------ drawing
    def surface(self, x0, x1, step=8.0, snow=True):
        xs = np.arange(x0, x1 + step, step, dtype=float)
        ys = self.snow_y(xs) if snow else self.ground_y(xs)
        return xs, np.asarray(ys, dtype=float)

    def draw_back(self, f, mood=None, par=1.0, x0=None, x1=None, groove=True, lip=None):
        """The snow ground on plane `par` (behind characters): surface silhouette from
        snow_y down past the bottom of the view, shaded from lit snow at the top to
        snow_dark below; plus the soft trodden groove of a path."""
        mood = get_mood(mood)
        vx0, vy0, vx1, vy1 = view(f, par, 60)
        x0 = vx0 if x0 is None else max(x0, vx0)
        x1 = vx1 if x1 is None else min(x1, vx1)
        if x1 <= x0:
            return
        step = max(4.0, 6.0 / max(f.lcam(par).zoom, 0.05))
        xs, ys = self.surface(x0, x1, step)
        with plane(f, par) as c:
            _fill_snow_body(c, xs, ys, vy1 + 40, mood.snow, mood.snow_dark, f.lcam(par).zoom)
            if groove:
                self._groove(c, xs, ys, mood)

    def _groove(self, c, xs, ys, mood):
        """Faint trodden band just under the surface line: the path reads as a path."""
        top = mix(mood.snow, mood.snow_dark, 0.55)
        y_mean = float(ys.mean())
        c.move_to(xs[0], ys[0])
        for x, y in zip(xs, ys):
            c.line_to(x, y)
        for x, y in zip(xs[::-1], ys[::-1]):
            c.line_to(x, y + 26)
        c.close_path()
        draw.linear(c, (0, y_mean - 2), (0, y_mean + 30), [(0, top, 0.0), (0.25, top, 0.55), (1, top, 0.0)])
        c.fill()

    def draw_front(self, f, mood=None, par=1.0, x0=None, x1=None, sink=6.0):
        """Snow lip IN FRONT of characters: fills from snow_y + sink (feet sink `sink` px
        into fresh snow; on deep snow the legs vanish below snow_y)."""
        mood = get_mood(mood)
        vx0, vy0, vx1, vy1 = view(f, par, 60)
        x0 = vx0 if x0 is None else max(x0, vx0)
        x1 = vx1 if x1 is None else min(x1, vx1)
        if x1 <= x0:
            return
        step = max(4.0, 6.0 / max(f.lcam(par).zoom, 0.05))
        xs, ys = self.surface(x0, x1, step)
        ys = ys + sink
        with plane(f, par) as c:
            _fill_snow_body(c, xs, ys, vy1 + 40, mood.snow, mood.snow_dark, f.lcam(par).zoom, lip=True)


_BODY_STOPS = (0.0, 0.1, 0.42, 1.0)
_BODY_SPAN = 1200.0


def snow_body_color(mood, dy):
    """Color of the shaded snow body `dy` world px below the top of the visible surface
    (matches Terrain.draw_back), for objects that must blend into it."""
    mood = get_mood(mood)
    deep = mix(mood.snow_dark, INK, 0.22)
    u = clamp(dy / _BODY_SPAN)
    if u <= 0.1:
        return mood.snow
    if u <= 0.42:
        return mix(mood.snow, mood.snow_dark, (u - 0.1) / 0.32)
    return mix(mood.snow_dark, deep, (u - 0.42) / 0.58)


def _fill_snow_body(c, xs, ys, bottom, top_col, low_col, zoom=1.0, lip=False, deep_col=None):
    """Snow body under a surface line: lit at the top, falling into shade toward the bottom
    of the frame (the near bank), so the ground has weight."""
    c.move_to(xs[0], bottom)
    for x, y in zip(xs, ys):
        c.line_to(x, y)
    c.line_to(xs[-1], bottom)
    c.close_path()
    y_top = float(ys.min())
    deep_col = deep_col or mix(low_col, INK, 0.22)
    draw.linear(c, (0, y_top), (0, y_top + 1200.0),
                [(0, top_col, 1.0), (0.1, top_col, 1.0), (0.42, low_col, 1.0), (1, deep_col, 1.0)])
    c.fill()


# ============================================================================ segments
class PathTerrain(Terrain):
    """The village street (x < 0, nearly flat at y ~ 1500) and the trail (x > 0) that leaves
    through the gate at x = 0 and descends into the valley, effectively forever (slope
    eases in over the first ~1500 px, then 0.05..0.32, avg ~0.17, i.e. ~10 degrees).

    Landmarks (x): see PATH_MARKS."""

    name = "path"
    y0 = 1500.0
    x_ref = 0.0
    table = (-8000.0, 160000.0, 4.0)

    def _slope_raw(self, x):
        x = np.asarray(x, dtype=float)
        ramp = _sstep(250.0, 1700.0, x)
        s = (0.170 + 0.085 * np.sin(x / 1270.0 + 1.1) + 0.050 * np.sin(x / 530.0 + 0.3)
             + 0.030 * np.sin(x / 2930.0 + 2.0))
        # a steeper, darker descent through the thicket stretch
        s = s + 0.05 * _sstep(7000.0, 8500.0, x) * (1.0 - _sstep(11500.0, 13000.0, x))
        street = -0.012 * np.sin(x / 640.0 + 0.4) * (x < 0)
        return ramp * np.maximum(s, 0.04) + street * (1 - ramp)

    def _bumps(self, x):
        x = np.asarray(x, dtype=float)
        return 4.0 * np.sin(x / 97.0 + 1.3) + 5.0 * np.sin(x / 233.0 + 0.2) + 3.0 * np.sin(x / 41.0 + 2.6) * 0.5

    def _dbumps(self, x):
        x = np.asarray(x, dtype=float)
        return (4.0 / 97.0) * np.cos(x / 97.0 + 1.3) + (5.0 / 233.0) * np.cos(x / 233.0 + 0.2) \
            + (1.5 / 41.0) * np.cos(x / 41.0 + 2.6)


PATH_MARKS = dict(
    street=(-3400.0, -60.0),     # the village street
    mother_door=-1650.0,          # threshold of the mother's house (village)
    well=-900.0,
    gate=0.0,                     # the village gate; the path starts here
    forest_edge=900.0,            # first trees
    descent=1700.0,               # the slope is fully in
    deep=6000.0,                  # the fog darkens from here
    thicket=(8200.0, 11800.0),    # dark thickets: eyes pacing her (S04)
    wolf_block=11900.0,           # where the wolf steps onto the path
)


class RidgeTerrain(Terrain):
    """S05/S06. x = 0 where she is chased off the path; the slope climbs through deep snow
    (snow depth 20 -> ~90 px, drifts) to the crest at crest_x (wind-swept, shallow), then the
    far side drops steeply toward the valley (a cornice edge at crest_x + ~260)."""

    name = "ridge"
    y0 = 1500.0
    x_ref = 0.0
    crest_x = 2800.0
    table = (-4000.0, 7000.0, 4.0)

    def _slope_raw(self, x):
        x = np.asarray(x, dtype=float)
        c = self.crest_x
        up = (0.36 + 0.10 * np.sin(x / 410.0 + 0.7) + 0.06 * np.sin(x / 170.0 + 2.2))
        rise = -up * _sstep(-200.0, 250.0, x) * (1.0 - _sstep(c - 700.0, c - 40.0, x))
        drop = 1.35 * _sstep(c + 140.0, c + 420.0, x)
        flat = 0.06 * np.sin(x / 300.0) * (x < 0)
        return rise + drop + flat

    def _bumps(self, x):
        x = np.asarray(x, dtype=float)
        return 6.0 * np.sin(x / 151.0 + 0.4) + 3.0 * np.sin(x / 67.0 + 1.9)

    def _dbumps(self, x):
        x = np.asarray(x, dtype=float)
        return (6.0 / 151.0) * np.cos(x / 151.0 + 0.4) + (3.0 / 67.0) * np.cos(x / 67.0 + 1.9)

    def _depth(self, x):
        x = np.asarray(x, dtype=float)
        c = self.crest_x
        deep = _sstep(150.0, 900.0, x) * (1.0 - _sstep(c - 650.0, c - 120.0, x))
        drift = 14.0 * np.sin(x / 233.0 + 1.0) + 8.0 * np.sin(x / 97.0 + 0.3)
        base = 16.0 + 70.0 * deep + drift * (0.3 + 0.7 * deep)
        edge = 1.0 - _sstep(c + 200.0, c + 330.0, x)       # no snow lip on the cliff face
        return np.maximum(base * edge, 0.0)

    @property
    def crest(self):
        """(x, y) of the footing at the crest (where she stands to look over the valley)."""
        return self.point(self.crest_x)


class ClearingTerrain(Terrain):
    """S07-S09, S11. The cottage door is at x = 0 (threshold y ~ 1560). Flat in front of the
    cottage from x ~ -600 to ~1500; to the left the ground falls away (the approach / the
    lantern path climbs ~620 px from x = -3400 up to x = -500); to the right it rises gently
    toward the forest edge. Fresh snow: depth ~10 px."""

    name = "clearing"
    y0 = 1560.0
    x_ref = 0.0
    table = (-8000.0, 8000.0, 4.0)

    def _slope_raw(self, x):
        x = np.asarray(x, dtype=float)
        approach = -0.27 * (1.0 - _sstep(-900.0, -380.0, x)) * _sstep(-4300.0, -3300.0, x)
        right = -0.12 * _sstep(1500.0, 2600.0, x)
        return approach + right + 0.02 * np.sin(x / 300.0 + 0.5)

    def _bumps(self, x):
        x = np.asarray(x, dtype=float)
        return 5.0 * np.sin(x / 181.0 + 2.3) + 2.5 * np.sin(x / 59.0 + 0.8)

    def _dbumps(self, x):
        x = np.asarray(x, dtype=float)
        return (5.0 / 181.0) * np.cos(x / 181.0 + 2.3) + (2.5 / 59.0) * np.cos(x / 59.0 + 0.8)

    def _depth(self, x):
        x = np.asarray(x, dtype=float)
        return 9.0 + 3.0 * np.sin(x / 140.0 + 0.2)


PATH = PathTerrain()
VILLAGE_STREET = PATH
RIDGE = RidgeTerrain()
CLEARING = ClearingTerrain()
TERRAINS = {"path": PATH, "street": PATH, "ridge": RIDGE, "clearing": CLEARING}


# ============================================================================ markers
def stake_shape(base, h=95.0, w=15.0, tilt=0.0, seed=0, snow=7.0, ground=None):
    """A short wooden path stake planted at `base` (x, y on the snow surface), leaning
    `tilt` degrees. ground(x): surface function so the drift mound follows the slope.
    Returns (ink_poly, snow_cap_poly, mound_poly) in world coords."""
    bx, by = base
    a = math.radians(tilt)
    ux, uy = math.sin(a), -math.cos(a)        # up along the stake
    nx, ny = -uy, ux                          # across (to the right when upright)

    def L(lx, ly):
        return (bx + nx * lx + ux * ly, by + ny * lx + uy * ly)

    half = w * 0.5
    cut = (rnd(seed, 3) - 0.5) * w * 0.5      # slanted, split top
    ink = [L(-half * 1.05, -6), L(half * 1.05, -6)]
    if rnd(seed, 5) < 0.5:                    # axe notch: detail in the outline
        nh = h * (0.55 + 0.2 * rnd(seed, 6))
        ink += [L(half, nh), L(half * 0.4, nh + 7), L(half, nh + 15)]
    ink += [L(half * 0.9, h + cut), L(-half * 0.9, h - cut)]
    cap = []
    if snow > 0:
        r = half * 1.2
        n = 9
        top = []
        for i in range(n + 1):
            u = i / n
            lx = -r + 2 * r * u
            ly = h + cut * (2 * u - 1) * 0.9 + snow * math.sin(math.pi * u) ** 0.7 + 1.0
            top.append(L(lx, ly))
        cap = top + [L(half * 0.9, h + cut - 3), L(-half * 0.9, h - cut - 3)]
    mr = w * 1.9
    G = ground if ground is not None else (lambda xx: by)
    ink[0] = (ink[0][0], max(ink[0][1], float(G(ink[0][0])) + 6))
    ink[1] = (ink[1][0], max(ink[1][1], float(G(ink[1][0])) + 6))
    mound = []
    for i in range(9):
        u = i / 8.0
        xx = bx - mr + 2 * mr * u
        mound.append((xx, float(G(xx)) - 9.0 * math.sin(math.pi * u) ** 1.4 * (0.8 + 0.4 * rnd(seed, 9 + i)) + 1.0))
    for i in range(8, -1, -1):
        xx = bx - mr + 2 * mr * i / 8.0
        mound.append((xx, float(G(xx)) + 10))
    return ink, cap, mound


def stone_shape(base, w=64.0, h=36.0, seed=0, snow=9.0):
    """A path stone half-buried in snow; returns (ink_poly, snow_cap_poly)."""
    bx, by = base
    n = 12
    rr = [1.0 + 0.10 * srnd(seed, i) for i in range(n + 1)]

    def P(i, k=1.0):
        th = math.pi * i / n
        return (bx - math.cos(th) * w * 0.5 * rr[i] * k, by + 8 - math.sin(th) * h * rr[i] * k)

    ink = [P(i) for i in range(n + 1)]
    top, bot = [], []
    for i in range(2, n - 1):
        th = math.pi * i / n
        p = P(i)
        s_ = math.sin(th) ** 2
        top.append((p[0], p[1] - snow * s_ - 1.5))
        bot.append((p[0] * 0.98 + bx * 0.02, p[1] + snow * 0.55 * s_ + 1.0))
    cap = top + bot[::-1]
    return ink, cap


class PathMarkers:
    """The stakes (and a few stones) that mark "the path". Deterministic along x, endless.
    Far-side markers sit on the action plane behind characters (draw_back); near-side
    markers are optional, slightly larger and lower, drawn in front (draw_front)."""

    def __init__(self, terrain=PATH, x_start=60.0, spacing=430.0, seed=11, near_every=3, x_end=None,
                 rope=True):
        self.terrain, self.x0, self.dx, self.seed = terrain, x_start, spacing, seed
        self.near_every = near_every
        self.x_end = x_end
        self.rope = rope
        self._cache = {}

    def _item(self, k):
        if k in self._cache:
            return self._cache[k]
        s = self.seed
        x = self.x0 + k * self.dx + srnd(s, k, 1) * self.dx * 0.18
        if x < self.x0 - 1 or (self.x_end is not None and x > self.x_end):
            self._cache[k] = None
            return None
        stone = rnd(s, k, 2) < 0.16
        it = dict(x=x, stone=stone, h=104 + 44 * rnd(s, k, 3), w=16 + 6 * rnd(s, k, 4),
                  tilt=srnd(s, k, 5) * 8.0, seed=s * 1000 + k,
                  rope=(not stone) and rnd(s, k, 6) > 0.12)       # rope to the next stake (some broken)
        self._cache[k] = it
        return it

    def top(self, it, ground=None):
        """Rope tie point near the top of a stake item."""
        g = ground or (lambda xx: float(self.terrain.snow_y(xx)) + 2.0)
        a = math.radians(it["tilt"])
        h = it["h"] * 0.78
        return (it["x"] + math.sin(a) * h, g(it["x"]) - math.cos(a) * h)

    def _rope_path(self, c, items, ground=None, sag=26.0, width=2.6):
        """Sagging rope segments between consecutive stakes (a broken one hangs down)."""
        its = dict(items)
        for k, it in items:
            if not it.get("rope") or it["stone"]:
                continue
            nxt = its.get(k + 1) or self._item(k + 1)
            if nxt is None or nxt["stone"]:
                continue
            p0, p1 = self.top(it, ground), self.top(nxt, ground)
            pts = []
            broken = rnd(self.seed, k, 7) < 0.15
            n = 14
            for i in range(n + 1):
                u = i / n
                x = p0[0] + (p1[0] - p0[0]) * u
                y = p0[1] + (p1[1] - p0[1]) * u + sag * 4 * u * (1 - u)
                pts.append((x, y))
            if broken:                                   # snapped: two dangling ends
                cut = n // 2
                a = pts[:cut]
                a = [(x, y + (i / cut) ** 2 * 40) for i, (x, y) in enumerate(a)]
                b = pts[cut + 2:]
                b = [(x, y + (1 - i / max(len(b) - 1, 1)) ** 2 * 55) for i, (x, y) in enumerate(b)]
                segs = [a, b]
            else:
                segs = [pts]
            for sg in segs:
                if len(sg) >= 2:
                    c.move_to(*sg[0])
                    for q in sg[1:]:
                        c.line_to(*q)
        return width

    def items(self, x0, x1):
        k0 = int(math.floor((x0 - self.x0) / self.dx)) - 1
        k1 = int(math.ceil((x1 - self.x0) / self.dx)) + 1
        out = []
        for k in range(max(k0, 0), k1 + 1):
            it = self._item(k)
            if it is not None and x0 - 100 <= it["x"] <= x1 + 100:
                out.append((k, it))
        return out

    def positions(self, x0, x1):
        """x positions of the far-side markers between x0 and x1."""
        return [it["x"] for _, it in self.items(x0, x1)]

    def _draw(self, c, items, mood, terrain_y, scale=1.0, mound_col=None):
        inks, caps, mounds = [], [], []
        for k, it in items:
            x = it["x"]
            base = (x, terrain_y(x))
            if it["stone"]:
                ink, cap = stone_shape(base, w=60 * scale, h=34 * scale, seed=it["seed"])
                inks.append(ink)
                caps.append(cap)
            else:
                ink, cap, mound = stake_shape(base, h=it["h"] * scale, w=it["w"] * scale,
                                              tilt=it["tilt"], seed=it["seed"], ground=terrain_y)
                inks.append(ink)
                caps.append(cap)
                mounds.append((mound, base[1]))
        for p in inks:
            draw.poly(c, p)
        draw.fill(c, mood.ink)
        for p, by in mounds:
            draw.poly(c, p)
            draw.fill(c, mound_col(by) if mound_col else mood.snow)
        for p in caps:
            if len(p) >= 3:
                draw.smooth(c, p, close=True, tension=0.4)
        draw.fill(c, mood.snow)

    def draw_back(self, f, mood=None):
        mood = get_mood(mood)
        vx0, vy0, vx1, vy1 = view(f, 1.0, 120)
        items = self.items(vx0 - self.dx, vx1 + self.dx)
        with plane(f, 1.0) as c:
            if self.rope:
                w = self._rope_path(c, items)
                draw.stroke(c, mood.ink, w)
            self._draw(c, items, mood, lambda x: float(self.terrain.snow_y(x)) + 2.0)

    def draw_front(self, f, mood=None, par=1.07, drop=46.0, blur=0.0):
        """Near-side markers (every `near_every`-th), on plane `par`, `drop` px lower."""
        if not self.near_every:
            return
        mood = get_mood(mood)
        vx0, vy0, vx1, vy1 = view(f, par, 160)
        items = []
        for k, it in self.items(vx0 - 200, vx1 + 200):
            if k % self.near_every == 1:
                it2 = dict(it)
                it2["x"] = it["x"] + 140.0 + 60 * srnd(self.seed, k, 9)
                it2["stone"] = False
                items.append((k, it2))
        if not items:
            return
        T = self.terrain
        g = lambda x: _plane_ground(T, x, par) + drop
        # the near stakes stand in the shaded snow body: match its tone at their base
        top = float(np.min(T.snow_y(np.linspace(*view(f, 1.0, 60)[0::2], 64))))
        col = lambda y: snow_body_color(mood, (y - top) * f.lcam(par).zoom / max(f.cam.zoom, 1e-3))
        if blur > 0:
            with f.layer(par=par, blur=blur) as c:
                self._draw(c, items, mood, g, scale=1.1, mound_col=col)
        else:
            with plane(f, par) as c:
                self._draw(c, items, mood, g, scale=1.1, mound_col=col)


def _plane_ground(terrain, xl, par, off=0.0):
    """Ground of a parallax plane `par` that mirrors `terrain` (see plane_ground)."""
    xw = 540.0 + (np.asarray(xl, dtype=float) - 540.0) / par
    v = 960.0 + par * (np.asarray(terrain.snow_y(xw), dtype=float) - 960.0) + off
    return _scalar_or(xl, v)


def plane_ground(terrain, par, off=0.0):
    """Ground function for a parallax layer `par` that follows `terrain` coherently: with
    the camera tracking the action plane, the layer's ground sits at
    960 + par * (camera height above ground) + off on screen, so far grounds rise toward the
    horizon and every layer keeps the terrain's slopes. Returns g(xl) in layer coords."""
    return lambda xl: _plane_ground(terrain, xl, par, off)


# ============================================================================ footprints
class Footprints:
    """Prints in the snow. prints: list of dicts or tuples (x, t_made[, side, size, deep]).
    side: -1 = far foot, +1 = near foot (offsets the print across the path); size: print
    length in px (child ~44, adult ~70, wolf paw ~38); deep: 0..1 (deep snow postholes).
    Prints exist from t_made on and slowly fill with falling snow (fill_time seconds)."""

    def __init__(self, prints=None, fill_time=60.0):
        self.prints = []
        self.fill_time = fill_time
        for p in prints or []:
            self.add(*p) if isinstance(p, (tuple, list)) else self.add(**p)

    def add(self, x, t_made=0.0, side=1, size=44.0, deep=0.0):
        self.prints.append(dict(x=float(x), t=float(t_made), side=side, size=float(size), deep=float(deep)))
        return self

    @staticmethod
    def from_walk(x0, x1, t0, speed, stride=70.0, size=44.0, deep=0.0):
        """Alternating prints of a walk from x0 to x1 at `speed` px/s starting at t0."""
        fp = Footprints()
        n = int(abs(x1 - x0) // stride)
        d = 1 if x1 >= x0 else -1
        for i in range(n + 1):
            x = x0 + d * i * stride
            fp.add(x, t0 + abs(x - x0) / max(speed, 1e-3), side=1 if i % 2 else -1, size=size, deep=deep)
        return fp

    def draw(self, f, terrain, t, mood=None, par=1.0):
        mood = get_mood(mood)
        vx0, vy0, vx1, vy1 = view(f, par, 80)
        col = mix(mood.snow_dark, mood.ink, 0.12)
        hi = mood.snow
        with plane(f, par) as c:
            for p in self.prints:
                if p["t"] > t or not (vx0 <= p["x"] <= vx1):
                    continue
                age = t - p["t"]
                a = 0.62 * (1.0 - clamp(age / self.fill_time) * 0.7) * clamp(age / 0.08)
                x = p["x"]
                y = float(terrain.snow_y(x))
                ang = float(terrain.angle(x))
                L = p["size"]
                yo = 4.0 + (3.0 if p["side"] > 0 else 0.5)
                c.save()
                c.translate(x, y + yo)
                c.rotate(math.radians(ang))
                if p["deep"] > 0:
                    dh = 10 + 26 * p["deep"]
                    draw.ellipse(c, (0, 2), L * 0.42, dh * 0.5)
                    draw.fill(c, col, a * 1.1)
                    draw.ellipse(c, (0, dh * 0.5), L * 0.5, 4)
                    draw.fill(c, hi, a)
                else:
                    draw.ellipse(c, (0, 0), L * 0.5, max(2.0, L * 0.11))
                    draw.fill(c, col, a)
                    draw.ellipse(c, (0, L * 0.09), L * 0.46, max(1.0, L * 0.05))
                    draw.fill(c, hi, a * 0.6)
                c.restore()


def snow_mound(c, base_x, ground, w, h, seed=0):
    """Add a drift mound path (snow piled against an object) centered at base_x on a
    ground function `ground(x)`."""
    pts = []
    n = 9
    for i in range(n + 1):
        u = i / n
        x = base_x - w / 2 + w * u
        bump = math.sin(math.pi * u) ** 1.6 * h * (1.0 + 0.15 * srnd(seed, i))
        pts.append((x, float(ground(x)) - bump))
    pts.append((base_x + w / 2, float(ground(base_x + w / 2)) + 8))
    pts.append((base_x - w / 2, float(ground(base_x - w / 2)) + 8))
    draw.smooth(c, pts, close=True, tension=0.45)
