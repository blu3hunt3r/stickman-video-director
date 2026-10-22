"""SALVAGE sets - C/D. the deep: descent column, backdrop by depth, seabed, reef walls,
debris - and the small 2.5D projector the wreck uses.

WHY A PROJECTOR. Things behind the action plane are placed at TRUE world positions
(x, y) plus a distance z behind the action plane (z = 0 is the action plane, z < 0 is
in front of it). View.P() maps them into action-plane coordinates with exactly the maths
of Frame.layer(par) (par = LENS / (LENS + z)), so a seabed strip at z = 4000 is the
same as a par-0.6 layer - but a ship 60 m long can recede into the murk, the seabed is a
real ground plane, and everything stays consistent through any camera move (descents,
cranes, pushes). Items are painted far to near; fog grows with z toward the backdrop
colour behind them; far bins are blurred (depth of field).

    view = View(f)                                  # this frame's camera
    deep_backdrop(f, t)                             # water by depth + glow
    world = DeepWorld()                             # seabed + reef + debris (+ wreck)
    world.draw(f, t, view)                          # everything with z >= 0
    with f.layer() as L: ... diver at seabed_y(x) ...
    world.draw_front(f, t, view)                    # foreground occluders (z < 0)
"""
import math

from engine import draw
from engine.core import W, H, clamp, lerp, hash01, noise1, fbm1, smoothstep

from .sets_common import (PAL, INK, SEABED_Y, DIVE_X, M, mix, water_at, depth_light, oriented,
                          jag, sway, line, blade, ell)

LENS = 6000.0       # distance of the action plane from the lens (world px): sets the perspective
FOG_LEN = 5200.0    # underwater visibility: fog(z) = 1 - exp(-z / FOG_LEN)
BG_SPAN = 0.22      # backdrop: screen px per world px of depth seen in the far haze


# ----------------------------------------------------------------------------- depth helpers
def haze_at(y):
    """Colour of the far water haze looking horizontally at depth y. A touch brighter than
    water_at() in the deep so silhouettes always have something to stand against."""
    c = water_at(y)
    return mix(c, PAL.mid, 0.42 * smoothstep(1500.0, 8500.0, y))


def depth_info(y):
    """What you see at depth y (world px below the surface), for scenes and other modules:
    dict(light = ambient 0..1, water = open-water rgb, haze = far-haze rgb,
         rays = god-ray strength 0..1 (gone by ~10 m), snow = marine-snow density 0..1,
         lamp = how much the helmet lamp is needed 0..1, metres = depth in metres)."""
    return dict(light=depth_light(y), water=water_at(y), haze=haze_at(y),
                rays=clamp(1.0 - smoothstep(300.0, 3600.0, y)),
                snow=clamp(0.25 + 0.75 * smoothstep(800.0, 6000.0, y)),
                lamp=smoothstep(2200.0, 5200.0, y), metres=max(y, 0.0) / M)


# ----------------------------------------------------------------------------- the projector
class View:
    """Per-frame projector: true world (x, y) at distance z behind the action plane ->
    action-plane coordinates (draw them in f.layer() / the main ctx)."""

    def __init__(self, f, lens=LENS, fog_len=FOG_LEN, fog_gamma=0.85, fog_max=0.97):
        cam = f.cam
        self.f = f
        self.cx, self.cy, self.zoom = cam.x, cam.y, cam.zoom
        self.lens, self.fog_len, self.fog_gamma, self.fog_max = lens, fog_len, fog_gamma, fog_max
        self.rect = cam.view_rect(60)

    def par(self, z):
        return self.lens / max(self.lens + z, 1e-3)

    def k(self, z):
        p = self.par(z)
        return p * (1.0 + (self.zoom - 1.0) * p) / self.zoom

    def P(self, x, y, z):
        k = self.k(z)
        return (self.cx + k * (x - self.cx), self.cy + k * (y - self.cy))

    def Pp(self, p3):
        return self.P(p3[0], p3[1], p3[2])

    def unP(self, X, Y, z):
        """True world (x, y) at distance z of action-plane point (X, Y)."""
        k = self.k(z)
        return (self.cx + (X - self.cx) / k, self.cy + (Y - self.cy) / k)

    def x_range(self, z, margin=200.0):
        x0, y0, x1, y1 = self.rect
        a = self.unP(x0, 0, z)[0]
        b = self.unP(x1, 0, z)[0]
        return a - margin, b + margin

    def visible(self, X0, Y0, X1, Y1):
        x0, y0, x1, y1 = self.rect
        return not (X1 < x0 or X0 > x1 or Y1 < y0 or Y0 > y1)

    def fog(self, z):
        return min(self.fog_max, 1.0 - math.exp(-max(z, 0.0) / self.fog_len))

    def bg(self, Y):
        """Backdrop colour behind action-plane height Y."""
        sy = H / 2 + self.zoom * (Y - self.cy)
        return haze_at(self.cy + (sy - H / 2) / BG_SPAN)

    def tone(self, z, Y=None):
        """Silhouette colour of an object at distance z seen in front of the backdrop."""
        fz = self.fog(z)
        if fz <= 0.0:
            return INK
        return mix(INK, self.bg(self.cy if Y is None else Y), fz ** self.fog_gamma)


def deep_backdrop(f, t, glow=None, bright=1.0):
    """The open water seen far away, screen space, by the camera's depth: brighter upward
    (toward the light), darker downward. glow = (screen x, screen y, radius, strength): a
    soft pool of light far behind - put it behind the subject (backlight)."""
    cy = f.cam.y
    n = 9
    stops = []
    for i in range(n):
        sy = -40 + (H + 80) * i / (n - 1)
        c = haze_at(cy + (sy - H / 2) / BG_SPAN)
        stops.append((i / (n - 1), mix(INK, c, bright), 1.0))
    with f.screen() as S:
        draw.linear(S, (0, -40), (0, H + 40), stops)
        S.paint()
    if glow is not None:
        gx, gy, gr, gs = glow
        col = haze_at(max(cy - 2500.0, 0.0))
        with f.light(par=0.0, blur=30) as A:
            A.save()
            A.identity_matrix()
            A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
            draw.glow_disc(A, (gx, gy), gr, col, 0.5 * gs)
            draw.glow_disc(A, (gx, gy), gr * 0.45, col, 0.35 * gs)
            A.restore()


# ----------------------------------------------------------------------------- painter
class Painter:
    """Collects depth-sorted drawing items; renders far to near in blur bins."""

    def __init__(self):
        self.items = []
        self._n = 0

    def add(self, z, fn):
        """fn(ctx, view) draws (and fills) itself in action-plane coords."""
        self._n += 1
        self.items.append((z, self._n, fn))

    def render(self, f, view, zmin=0.0, zmax=1e9, bins=((9000.0, 7.0), (3200.0, 3.5), (900.0, 1.4), (-1e9, 0.0))):
        """Draw the items with zmin <= z < zmax. bins: [(z_from, blur_px)], far to near: items
        with z >= z_from (and below the previous bin) go into a layer blurred by blur_px."""
        its = sorted([it for it in self.items if zmin <= it[0] < zmax], key=lambda it: (-it[0], it[1]))
        if not its:
            return
        hi = 1e18
        for zf, blur in bins:
            group = [it for it in its if zf <= it[0] < hi]
            hi = zf
            if not group:
                continue
            with f.layer(blur=blur) as L:
                for z, _, fn in group:
                    fn(L, view)


def convex_hull(pts):
    """Andrew's monotone chain; returns the hull clockwise on screen (y down)."""
    P = sorted(set((round(p[0], 3), round(p[1], 3)) for p in pts))
    if len(P) < 3:
        return P

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in P:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(P):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return oriented(lower[:-1] + upper[:-1])


def fill_grad(ctx, a, b, ca, cb):
    """Fill the current path with a linear gradient from colour ca at point a to cb at b."""
    if math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0:
        ctx.set_source_rgb(*ca)
    else:
        draw.linear(ctx, a, b, [(0, ca, 1.0), (1, cb, 1.0)])
    ctx.fill()


def rod3(ctx, view, a, b, r0, r1, tone=True, col=None):
    """A tapered rod between 3D points a, b (x, y, z), radii in world px; filled with the
    fog tone of each end (gradient) unless col is given."""
    A, B = view.Pp(a), view.Pp(b)
    ka, kb = view.k(a[2]), view.k(b[2])
    draw.capsule(ctx, A, B, max(r0 * ka, 0.35), max(r1 * kb, 0.35))
    if col is not None:
        ctx.set_source_rgb(*col)
        ctx.fill()
    else:
        fill_grad(ctx, A, B, view.tone(a[2], A[1]), view.tone(b[2], B[1]))


def prism3(ctx, view, near, far, col=None):
    """Silhouette of a straight extrusion between two 3D outlines (lists of (x, y, z)) of a
    CONVEX section: the convex hull of both projections, shaded near -> far."""
    pn = [view.Pp(p) for p in near]
    pf = [view.Pp(p) for p in far]
    hull = convex_hull(pn + pf)
    if len(hull) < 3:
        return
    draw.poly(ctx, hull)
    if col is not None:
        ctx.set_source_rgb(*col)
        ctx.fill()
        return
    zn = sum(p[2] for p in near) / len(near)
    zf = sum(p[2] for p in far) / len(far)
    cn = (sum(p[0] for p in pn) / len(pn), sum(p[1] for p in pn) / len(pn))
    cf = (sum(p[0] for p in pf) / len(pf), sum(p[1] for p in pf) / len(pf))
    fill_grad(ctx, cn, cf, view.tone(zn, cn[1]), view.tone(zf, cf[1]))


def card(ctx, view, pts, z, col=None):
    """A flat silhouette (world x, y points) standing at distance z."""
    pp = [view.P(x, y, z) for x, y in pts]
    draw.poly(ctx, pp)
    if col is None:
        ys = [p[1] for p in pp]
        col = view.tone(z, (min(ys) + max(ys)) / 2)
    ctx.set_source_rgb(*col)
    ctx.fill()


# ----------------------------------------------------------------------------- seabed
STRIPS = (0.0, 420.0, 1100.0, 2200.0, 3800.0, 6200.0, 9800.0, 15000.0, 23000.0)


def seabed_y(x, z=0.0):
    """World y of the seabed (silt) at world x and distance z (z = 0: where feet go)."""
    return (SEABED_Y + 58.0 * fbm1(x / 1500.0 + z * 0.00031, 71) + 18.0 * fbm1(x / 330.0 + z * 0.0009, 72)
            + 120.0 * fbm1(z / 5200.0 + 3.3, 73))


def _rock_pts(seed, w, h):
    """A boulder silhouette (base on y = 0) of width w, height h."""
    n = 14
    pts = []
    for i in range(n + 1):
        u = i / n
        a = math.pi * (1 - u)
        r = 1.0 + 0.16 * noise1(u * 5.0, seed) + 0.08 * noise1(u * 13.0, seed + 1)
        pts.append((math.cos(a) * w * 0.5 * r, -math.sin(a) ** 0.8 * h * r))
    pts.append((w * 0.55, 20.0))
    pts.append((-w * 0.55, 20.0))
    return jag(pts, seed=seed, amp=w * 0.012, step=max(w / 18, 8))


def _strip_item(z, seed_base=0, grass=True, rocks=True):
    def fn(ctx, view):
        x0, x1 = view.x_range(z, 600)
        n = 80
        top = []
        for i in range(n + 1):
            x = lerp(x0, x1, i / n)
            top.append(view.P(x, seabed_y(x, z), z))
        Yb = view.rect[3] + 400
        pts = top + [(top[-1][0], Yb), (top[0][0], Yb)]
        draw.poly(ctx, pts)
        ymid = sum(p[1] for p in top) / len(top)
        col = view.tone(z, ymid)
        k = view.k(z)
        # rocks on this strip
        if rocks:
            cell = 1300.0
            i0, i1 = int(math.floor(x0 / cell)), int(math.ceil(x1 / cell))
            for i in range(i0, i1 + 1):
                hsh = hash01(seed_base, i, int(z))
                if hsh > 0.42:
                    continue
                xr = (i + hash01(seed_base, i, 5)) * cell
                wr = 220 + 620 * hash01(seed_base, i, 6) ** 2
                hr = wr * (0.32 + 0.35 * hash01(seed_base, i, 7))
                base = view.P(xr, seabed_y(xr, z) + 30, z)
                rp = [(base[0] + px * k, base[1] + py * k) for px, py in _rock_pts(int(hsh * 1000) + i, wr, hr)]
                ctx.new_sub_path()
                draw.poly(ctx, rp)
        ctx.set_source_rgb(*col)
        ctx.fill()
        if grass and z < 7000:
            _grass(ctx, view, z, x0, x1, col, seed_base)
    return fn


def _grass(ctx, view, z, x0, x1, col, seed=0, t=None):
    t = view.f.t if t is None else t
    k = view.k(z)
    cell = 520.0
    i0, i1 = int(math.floor(x0 / cell)), int(math.ceil(x1 / cell))
    for i in range(i0, i1 + 1):
        if hash01(seed + 3, i, int(z)) > 0.55:
            continue
        xb = (i + hash01(seed + 3, i, 1)) * cell
        yb = seabed_y(xb, z) + 6
        nb = 4 + int(5 * hash01(seed + 3, i, 2))
        hgt = 140 + 260 * hash01(seed + 3, i, 3)
        for j in range(nb):
            u = (j + 0.5) / nb - 0.5
            bx = xb + u * 70
            sw = sway(t + j * 0.3, seed=i * 7 + j, amp=14.0, period=4.5 + j * 0.3)
            ang = -90 + u * 40 + sw * 0.7
            L = hgt * (0.55 + 0.45 * hash01(i, j, 9))
            b = view.P(bx, yb, z)
            blade(ctx, b, ang, L * k, 9 * k, 0.8 * k, bend=u * 50 + sw * 1.6, n=6)
    ctx.set_source_rgb(*col)
    ctx.fill()


# ----------------------------------------------------------------------------- reef walls (descent column)
def _wall_pts(seed, x_edge, y_top, y_bot, side=-1, depth=2400.0, ledges=5):
    """A jagged reef/cliff silhouette: the open edge runs at ~x_edge from y_top down to y_bot
    with ledges sticking out; the mass extends `depth` px away (side -1 = mass to the left)."""
    pts = []
    n = 46
    for i in range(n + 1):
        u = i / n
        y = lerp(y_top, y_bot, u)
        e = (260 * fbm1(u * 6.0, seed) + 120 * noise1(u * 19.0, seed + 1)
             + 420 * max(0.0, math.sin(u * math.pi * ledges + hash01(seed, 4) * 6)) ** 6)
        x = x_edge - side * e - side * 900 * smoothstep(0.75, 1.0, u)
        pts.append((x, y))
    # the cap (rounded top) and the far mass
    far = x_edge + side * depth
    top = [(lerp(far, x_edge, v), y_top - 260 * math.sin(math.pi * v) ** 0.5 - 80 * noise1(v * 7, seed + 2))
           for v in (0.0, 0.25, 0.5, 0.75)]
    body = top + pts + [(far, y_bot + 400)]
    return jag(body, seed=seed + 9, amp=26.0, step=60.0)


REEF = (   # (seed, x_edge, y_top, y_bot, side, z) - the walls of the descent column
    (11, -2300.0, 1400.0, 9600.0, -1, 2600.0),
    (12, -3700.0, 600.0, 9600.0, -1, 7600.0),
    (13, 3900.0, 2900.0, 9600.0, 1, 5200.0),
    (14, 6200.0, 900.0, 9600.0, 1, 13000.0),
)


def _reef_item(seed, x_edge, y_top, y_bot, side, z):
    key = ("reef", seed)
    cache = _REEF_CACHE.get(key)
    if cache is None:
        cache = _wall_pts(seed, x_edge, y_top, y_bot, side)
        _REEF_CACHE[key] = cache

    def fn(ctx, view):
        pp = [view.P(x, y, z) for x, y in cache]
        xs, ys = [p[0] for p in pp], [p[1] for p in pp]
        if not view.visible(min(xs), min(ys), max(xs), max(ys)):
            return
        draw.poly(ctx, pp)
        Ym = view.cy
        top_c = view.tone(z, min(ys) + 300 * view.k(z))
        bot_c = view.tone(z, max(ys))
        mid = (sum(xs) / len(xs), view.cy)
        fill_grad(ctx, (mid[0], max(min(ys), view.rect[1])), (mid[0], min(max(ys), view.rect[3])), top_c, bot_c)
        # kelp on the ledges
        k = view.k(z)
        col = view.tone(z, Ym)
        t = view.f.t
        for j in range(0, len(cache) - 6, 5):
            x, y = cache[j]
            if y < y_top + 200 or y > y_bot - 300 or hash01(seed, j) > 0.5:
                continue
            b = view.P(x, y, z)
            hgt = 260 + 500 * hash01(seed, j, 2)
            for m in range(3):
                sw = sway(t + m, seed=seed * 31 + j * 3 + m, amp=10, period=5.5)
                blade(ctx, (b[0] + (m - 1) * 14 * k, b[1]), -90 + (m - 1) * 10 + sw, hgt * k * (0.7 + 0.3 * m / 2),
                      10 * k, 1 * k, bend=sw * 2.2 + (m - 1) * 12, n=7)
        ctx.set_source_rgb(*col)
        ctx.fill()
    return fn


_REEF_CACHE = {}


# ----------------------------------------------------------------------------- debris
def _crate_pts(w, h, tilt, sink):
    pts = [(-w / 2, 0), (w / 2, 0), (w / 2, -h), (-w / 2, -h)]
    a = math.radians(tilt)
    out = [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a) + sink) for x, y in pts]
    return out


def _drum_pts(r, L, tilt):
    """Oil drum lying on its side, seen end-on-ish (a rounded rectangle)."""
    pts = []
    for i in range(10):
        a = -math.pi / 2 + math.pi * i / 9
        pts.append((L / 2 + math.cos(a) * r * 0.35, -r + math.sin(a) * r))
    for i in range(10):
        a = math.pi / 2 + math.pi * i / 9
        pts.append((-L / 2 + math.cos(a) * r * 0.35, -r + math.sin(a) * r))
    a = math.radians(tilt)
    return [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for x, y in pts]


def chain_items(painter, pts3, link=64.0, seed=0):
    """Anchor chain lying along a 3D polyline: alternating face-on rings and edge-on bars.
    Adds one item per link to the painter."""
    segs = []
    for i in range(len(pts3) - 1):
        a, b = pts3[i], pts3[i + 1]
        L = math.dist(a, b)
        n = max(1, int(L / (link * 0.78)))
        for j in range(n):
            u0, u1 = j / n, (j + 1) / n
            segs.append((tuple(lerp(a[q], b[q], u0) for q in range(3)), tuple(lerp(a[q], b[q], u1) for q in range(3))))
    for idx, (a, b) in enumerate(segs):
        def fn(ctx, view, a=a, b=b, idx=idx):
            A, B = view.Pp(a), view.Pp(b)
            k = view.k(a[2])
            c = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
            ang = math.degrees(math.atan2(B[1] - A[1], B[0] - A[0]))
            Lp = math.hypot(B[0] - A[0], B[1] - A[1]) * 0.64 + link * 0.2 * k
            col = view.tone(a[2], c[1])
            if idx % 2 == 0:       # standing link, face on: a ring you can see through
                ell(ctx, c, Lp, link * 0.36 * k, ang)
                ell(ctx, c, Lp * 0.62, link * 0.16 * k, ang, hole=True)
            else:                  # lying link, edge on: a bar
                ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                draw.capsule(ctx, (c[0] - ca * Lp, c[1] - sa * Lp), (c[0] + ca * Lp, c[1] + sa * Lp),
                             link * 0.11 * k, link * 0.11 * k)
            ctx.set_source_rgb(*col)
            ctx.fill()
        painter.add(a[2] - 1.0, fn)


# ----------------------------------------------------------------------------- the world
class DeepWorld:
    """The underwater world below the boat: seabed strips (with rocks and swaying sea grass),
    the reef walls of the descent column and the debris field, plus any extra items (the wreck
    adds itself with world.wreck = Wreck()). Coordinates: see module doc."""

    def __init__(self, wreck=None, reef=True, debris=True, seed=0):
        self.wreck = wreck
        self.reef = reef
        self.debris = debris
        self.seed = seed

    def painter(self, f, t, view, wreck_kw=None):
        P = Painter()
        for z in STRIPS:
            P.add(z, _strip_item(z, self.seed, grass=True, rocks=z > 300))
        if self.reef:
            for r in REEF:
                P.add(r[5], _reef_item(*r))
        if self.debris:
            self._debris(P, t)
        if self.wreck is not None:
            self.wreck.add_items(P, t, **(wreck_kw or {}))
        return P

    def _debris(self, P, t):
        # crates and drums spilled near the stern (z from 300 to 2600)
        for i, (x, z, w, h, tilt) in enumerate(((DIVE_X - 1400, 700.0, 300, 240, 11), (DIVE_X - 2350, 1500.0, 380, 260, -7),
                                                (DIVE_X + 2300, 520.0, 260, 200, 24), (DIVE_X - 3600, 2600.0, 340, 300, 4))):
            pts = _crate_pts(w, h, tilt, 60)

            def fn(ctx, view, x=x, z=z, pts=pts):
                yb = seabed_y(x, z)
                card(ctx, view, [(x + px, yb + py) for px, py in pts], z)
            P.add(z - 2, fn)
        for i, (x, z, r, L, tilt) in enumerate(((DIVE_X - 1700, 420.0, 95, 300, 6), (DIVE_X + 1900, 1800.0, 95, 300, -12))):
            pts = _drum_pts(r, L, tilt)

            def fn(ctx, view, x=x, z=z, pts=pts):
                yb = seabed_y(x, z) + 22
                card(ctx, view, [(x + px, yb + py) for px, py in pts], z)
            P.add(z - 2, fn)
        # a broken spar (the main topmast) half buried in the silt
        a3 = (DIVE_X - 3100, seabed_y(DIVE_X - 3100, 1300) + 40, 1300.0)
        b3 = (DIVE_X - 900, seabed_y(DIVE_X - 900, 1900) - 300, 1900.0)
        P.add(1600.0, lambda ctx, view: (rod3(ctx, view, a3, b3, 46, 30),
                                         rod3(ctx, view, (b3[0] - 260, b3[1] + 40, b3[2] - 40),
                                              (b3[0] - 520, b3[1] - 520, b3[2] - 80), 22, 16)))
        # the anchor chain snaking over the silt toward the camera
        pts = []
        for i in range(9):
            u = i / 8
            x = DIVE_X - 2600 + 2400 * u + 260 * math.sin(u * 5.0)
            z = 1500.0 - 1350.0 * u
            pts.append((x, seabed_y(x, z) + 8, z))
        chain_items(P, pts, link=70.0)

    def draw(self, f, t, view=None, wreck_kw=None, bins=None):
        """Paint everything at z >= 0 (behind the action plane), far to near."""
        view = view or View(f)
        P = self.painter(f, t, view, wreck_kw)
        if bins:
            P.render(f, view, 0.0, 1e9, bins)
        else:
            P.render(f, view, 0.0, 1e9)
        return view

    def draw_front(self, f, t, view=None, wreck_kw=None, blur=14.0):
        """Paint items in front of the action plane (z < 0) as soft occluders."""
        view = view or View(f)
        P = self.painter(f, t, view, wreck_kw)
        P.render(f, view, -1e9, 0.0, bins=((-1e9, blur),))
        return view
