"""THE LANTERN sets: the Limbo forest (sepia-grey fog, black trunks, roots, moss, ferns).

    FOREST.draw_back(f)        sky, far trunk layers in fog, mist bands, soft light shafts
    FOREST.draw_plane(f)       action-plane trunks, roots and the ground (draw characters after)
    FOREST.draw_front(f)       blurred foreground grass, ferns and near trunks framing the shot
    ground_y(x)                the action plane's ground height (world y, down = +)

World: the forest floor runs along x (she walks right). Ground is around y = 0; trunks rise
to y = -4000 and beyond. Everything is generated per cell from hashes, so it is stable for any
camera and any t (pure function of position). Geometry is cached per cell.

Design rules for this film (see docs/STYLE_LANTERN.md):
  * mid-grey fog, never murky: the far layers carry the light, the action plane is pure ink;
  * trunks are TALL and straight-ish, few branches, flared roots, hanging moss strands;
  * the ground is a soft rolling line with grass blades and fern fronds breaking the edge.
"""
import math
from functools import lru_cache

from engine import draw
from engine.core import clamp, hash01, lerp, noise1, fbm1

INK = (0.020, 0.018, 0.016)


# ----------------------------------------------------------------------------- terrain
def ground_y(x, par=1.0, seed=0):
    """Rolling forest floor (world y). Gentle, readable; a few humps of roots."""
    return (38.0 * math.sin(x / 910.0 + 0.6 + seed) + 22.0 * math.sin(x / 377.0 + 1.9 + seed * 2)
            + 26.0 * fbm1(x / 520.0, seed=11 + seed, octaves=3) - 10.0)


def _rnd(*k):
    return hash01(*k)


def _srnd(*k):
    return hash01(*k) * 2.0 - 1.0


# ----------------------------------------------------------------------------- shapes
def _tapered(pts, w0, w1):
    n = len(pts)
    widths = [lerp(w0, w1, (i / (n - 1)) ** 0.85) for i in range(n)]
    widths[-1] = max(0.8, w1 * 0.5)
    return draw.ribbon(pts, widths)


def _bough(x, y, ang, length, bend, n=7, droop=0.0):
    pts = [(x, y)]
    a = ang
    step = length / (n - 1)
    for i in range(1, n):
        a += bend / (n - 1)
        r = math.radians(a)
        x += math.sin(r) * step
        y += -math.cos(r) * step + droop * (2 * i - 1) / ((n - 1) ** 2)
        pts.append((x, y))
    return pts


@lru_cache(maxsize=4096)
def _tree(layer, cell, xc, base, w, height, seed):
    """One tree as a list of polygons: trunk with root flare, a few dead boughs, moss strands."""
    polys = []
    lean = _srnd(seed, 1) * 0.035
    top = base - height
    n = 16
    left, right = [], []
    for i in range(n + 1):
        u = i / n                                      # 0 = base, 1 = top
        y = lerp(base + 12, top, u)
        cx = xc + lean * (base - y) + 14.0 * noise1(u * 3.0, seed=seed) * (w / 60.0)
        hw = w * 0.5 * (1.0 - 0.30 * u)
        flare = w * 0.55 * math.exp(-u * height / (w * 0.9)) ** 1.6   # root flare at the base
        wl = 0.05 * w * noise1(u * 14.0 + 3, seed=seed + 2)          # bark irregularity
        wr = 0.05 * w * noise1(u * 14.0 + 9, seed=seed + 5)
        left.append((cx - hw - flare + wl, y))
        right.append((cx + hw + flare * 0.9 + wr, y))
    polys.append(left + right[::-1])
    # roots: tapered ribbons sliding into the ground on both sides
    nr = 2 + int(_rnd(seed, 3) * 3)
    for k in range(nr):
        side = -1 if k % 2 == 0 else 1
        L = w * (1.2 + 1.4 * _rnd(seed, 4, k))
        sx = xc + side * w * (0.35 + 0.2 * _rnd(seed, 5, k))
        pts = [(sx, base - w * 0.5), (sx + side * L * 0.45, base - w * 0.12), (sx + side * L, base + 14)]
        pts = draw.resample(pts, 6, closed=False)
        polys.append(_tapered(pts, w * 0.32, 3.0))
    # dead boughs, mostly high up
    nb = 1 + int(_rnd(seed, 6) * 5)
    for k in range(nb):
        u = 0.35 + 0.55 * _rnd(seed, 7, k)
        y = lerp(base, top, u)
        side = -1 if _rnd(seed, 8, k) < 0.5 else 1
        cx = xc + lean * (base - y)
        ang = side * (45 + 40 * _rnd(seed, 9, k))
        L = w * (2.5 + 4.0 * _rnd(seed, 10, k))
        pts = _bough(cx + side * w * 0.3, y, ang, L, side * (15 + 25 * _rnd(seed, 11, k)), droop=L * 0.15)
        polys.append(_tapered(pts, w * 0.16, 1.2))
        if _rnd(seed, 12, k) < 0.6:           # a twig off the bough
            m = pts[3]
            tw = _bough(m[0], m[1], ang - side * 50, L * 0.35, side * 10)
            polys.append(_tapered(tw, w * 0.07, 0.8))
    return polys


@lru_cache(maxsize=4096)
def _moss(xc, y0, length, seed):
    """A hanging strand of moss: a thin wavy ribbon that widens into ragged clumps."""
    pts = []
    n = 14
    for i in range(n):
        u = i / (n - 1)
        pts.append((xc + 10 * math.sin(u * 5 + seed) * u, y0 + u * length))
    widths = [lerp(3.0, 10.0, u) * (0.6 + 0.8 * _rnd(seed, i)) for i, u in enumerate(x / (n - 1) for x in range(n))]
    return [draw.ribbon(pts, widths)]


@lru_cache(maxsize=8192)
def _grass(x0, gy, h, seed, n=7, lean=0.0):
    """A clump of grass blades (each a thin curved triangle)."""
    polys = []
    for k in range(n):
        bx = x0 + (k - n / 2) * 7 + 6 * _srnd(seed, k)
        hh = h * (0.5 + 0.6 * _rnd(seed, k, 1))
        a = math.radians(lean + 22 * _srnd(seed, k, 2))
        tip = (bx + math.sin(a) * hh, gy - math.cos(a) * hh)
        mid = (bx + math.sin(a) * hh * 0.55 - 6 * _srnd(seed, k, 3), gy - math.cos(a) * hh * 0.55)
        w = 2.5 + 3.0 * _rnd(seed, k, 4)
        polys.append([(bx - w, gy + 4), (mid[0] - w * 0.5, mid[1]), tip, (mid[0] + w * 0.5, mid[1]), (bx + w, gy + 4)])
    return polys


@lru_cache(maxsize=4096)
def _fern(x0, gy, size, seed, flip=1):
    """A fern: a few arching fronds with leaflets (silhouette)."""
    polys = []
    nf = 3 + int(_rnd(seed) * 3)
    for k in range(nf):
        ang = flip * (-60 + 120 * (k + 0.5) / nf + 12 * _srnd(seed, k))
        L = size * (0.6 + 0.5 * _rnd(seed, k, 1))
        pts = _bough(x0, gy, ang, L, flip * 40 * (1 if ang > 0 else -1) * 0.8, n=9, droop=L * 0.35)
        polys.append(_tapered(pts, 4.0, 1.0))
        for j in range(1, 8):                          # leaflets along the frond
            p, q = pts[j], pts[j + 1]
            dx, dy = q[0] - p[0], q[1] - p[1]
            d = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / d, dx / d
            ll = L * 0.13 * (1 - j / 9.0)
            for s in (-1, 1):
                tip = (p[0] + nx * s * ll + dx * 0.4, p[1] + ny * s * ll + dy * 0.4)
                polys.append([p, (p[0] + dx * 0.5, p[1] + dy * 0.5), tip])
    return polys


def _fill(c, polys, rgb, a=1.0):
    c.new_path()
    for p in polys:
        if len(p) >= 3:
            c.move_to(*p[0])
            for q in p[1:]:
                c.line_to(*q)
            c.close_path()
    c.set_source_rgba(rgb[0], rgb[1], rgb[2], a)
    c.fill()


# ----------------------------------------------------------------------------- the forest
class Forest:
    # far layers: (par, fog, blur, cell width, trunk width range, density, seed)
    LAYERS = [
        (0.22, 0.86, 6.0, 150.0, (14, 30), 0.90, 31),
        (0.38, 0.70, 4.0, 200.0, (20, 42), 0.85, 37),
        (0.58, 0.50, 2.5, 280.0, (30, 58), 0.75, 41),
        (0.78, 0.30, 1.2, 420.0, (40, 75), 0.60, 43),
    ]

    def __init__(self, seed=0, darkness=None):
        self.seed = seed
        self.darkness = darkness or (lambda x: 0.0)     # 0 = forest edge .. 1 = deep wood

    # -- geometry per layer cell
    def _cells(self, f, par, cell, margin=500.0):
        cam = f.lcam(par)
        x0, y0, x1, y1 = cam.view_rect(margin)
        return range(int(math.floor(x0 / cell)) - 1, int(math.floor(x1 / cell)) + 2), (y0, y1)

    def _layer_ground(self, x, par):
        """A far layer's floor: the action ground seen through parallax, flattened."""
        return ground_y(x / max(par, 0.2), seed=par) * par

    def _layer_trees(self, f, li):
        par, fog, blur, cell, (wa, wb), dens, seed = self.LAYERS[li]
        cells, _ = self._cells(f, par, cell)
        out = []
        for k in cells:
            if _rnd(seed, k) > dens:
                continue
            xc = (k + 0.15 + 0.7 * _rnd(seed, k, 1)) * cell
            w = lerp(wa, wb, _rnd(seed, k, 2))
            base = self._layer_ground(xc, par) + 30
            out.append((k, xc, base, w))
        return out

    def draw_back(self, f, light_x=None, shafts=1.0):
        """Sky, fogged far layers with mist between them, and soft shafts."""
        pal = f.pal
        f.sky(pal.sky_top, pal.sky_bottom, mid=lerp(pal.sky_top, pal.sky_bottom, 0.55), mid_at=0.55)
        for li, (par, fog, blur, cell, wr, dens, seed) in enumerate(self.LAYERS):
            gy = self._layer_ground(0, par)
            with f.layer(par=par, blur=blur, fog=fog) as L:
                polys = []
                for k, xc, base, w in self._layer_trees(f, li):
                    polys += _tree(li, k, round(xc, 1), round(base, 1), round(w, 1), 5200.0, seed * 1000 + k)
                    if _rnd(seed, k, 9) < 0.35:
                        polys += _moss(round(xc + w * 0.2, 1), round(base - 1400 - 900 * _rnd(seed, k, 8), 1),
                                       300.0 + 500 * _rnd(seed, k, 7), seed + k)
                # the layer's floor: a band down past the frame bottom
                cam = f.lcam(par)
                x0, y0, x1, y1 = cam.view_rect(300)
                n = 40
                floor = [(lerp(x0, x1, i / n), self._layer_ground(lerp(x0, x1, i / n), par) + 20) for i in range(n + 1)]
                polys.append(floor + [(x1, y1 + 2000), (x0, y1 + 2000)])
                _fill(L, polys, INK)
            # mist settling on each layer's floor (world y through the layer's parallax)
            f.haze(pal.fog_at(fog * 0.9), 0.55, gy - 300, gy + 80, feather=260, tex=0.5,
                   tex_scale=1.4, scroll=(6.0, 0.0), seed=li + 5, par=par)
        if shafts > 0:
            with f.light(par=0.45, blur=26.0, alpha=0.20 * shafts) as A:
                cam = f.lcam(0.45)
                x0, y0, x1, y1 = cam.view_rect(400)
                for k in range(int(x0 // 700) - 1, int(x1 // 700) + 2):
                    if _rnd(77, k) < 0.45:
                        continue
                    x = k * 700 + 300 * _rnd(78, k)
                    w = 60 + 120 * _rnd(79, k)
                    pulse = 0.65 + 0.35 * math.sin(f.t * 0.4 + k)
                    A.move_to(x, y0 - 200)
                    A.line_to(x + w, y0 - 200)
                    A.line_to(x + w + 900, y1 + 200)
                    A.line_to(x + 900 - w * 0.2, y1 + 200)
                    A.close_path()
                    A.set_source_rgba(0.95, 0.92, 0.82, 0.55 * pulse)
                    A.fill()

    def plane_trees(self, f, cell=900.0, seed=53):
        cells, _ = self._cells(f, 1.0, cell)
        out = []
        for k in cells:
            if _rnd(seed, k) < 0.30:
                continue
            xc = (k + 0.2 + 0.6 * _rnd(seed, k, 1)) * cell
            w = 90 + 80 * _rnd(seed, k, 2)
            out.append((k, xc, ground_y(xc), w))
        return out

    def draw_plane(self, f):
        """Action plane: big trunks, the ground and its grass edge (pure ink, sharp)."""
        with f.layer() as L:
            polys = []
            for k, xc, base, w in self.plane_trees(f):
                polys += _tree(9, k, round(xc, 1), round(base, 1), round(w, 1), 6000.0, 9000 + k)
                if _rnd(91, k) < 0.6:
                    for j in range(2):
                        polys += _moss(round(xc + _srnd(92, k, j) * w * 0.6, 1),
                                       round(base - 1500 - 600 * _rnd(93, k, j), 1), 420.0 + 380 * _rnd(94, k, j), 95 + k * 3 + j)
            cam = f.lcam(1.0)
            x0, y0, x1, y1 = cam.view_rect(200)
            n = 90
            xs = [lerp(x0, x1, i / n) for i in range(n + 1)]
            floor = [(x, ground_y(x)) for x in xs]
            polys.append(floor + [(x1, y1 + 3000), (x0, y1 + 3000)])
            # grass and ferns along the edge (deterministic per 60 px cell)
            for k in range(int(x0 // 60), int(x1 // 60) + 1):
                x = k * 60 + 30 * _rnd(61, k)
                gy = ground_y(x) + 6
                r = _rnd(62, k)
                if r < 0.55:
                    polys += _grass(round(x, 1), round(gy, 1), 34 + 40 * _rnd(63, k), 600 + k, n=5 + int(4 * _rnd(64, k)),
                                    lean=8 * _srnd(65, k))
                elif r < 0.66:
                    polys += _fern(round(x, 1), round(gy, 1), 110 + 70 * _rnd(66, k), 700 + k, flip=1 if _rnd(67, k) < 0.5 else -1)
            _fill(L, polys, INK)

    def draw_canopy(self, f, par=1.25, blur=6.0):
        """Moss and vines hanging from out of frame top: frames the tall 9:16 shot."""
        with f.layer(par=par, blur=blur) as L:
            cam = f.lcam(par)
            x0, y0, x1, y1 = cam.view_rect(300)
            polys = []
            for k in range(int(x0 // 230), int(x1 // 230) + 1):
                if _rnd(101, k) < 0.45:
                    continue
                x = k * 230 + 120 * _rnd(102, k)
                L_ = 300 + 650 * _rnd(103, k)
                sway = 6.0 * math.sin(f.t * 0.7 + k)
                polys += _moss(round(x + sway, 0), round(y0 - 50, 0), round(L_, 0), 110 + k)
            _fill(L, polys, INK)

    def draw_front(self, f, strength=1.0):
        """Foreground: blurred black grass and fern masses along the bottom, an occasional
        near trunk at the frame edge (par 1.6)."""
        par = 1.6
        with f.layer(par=par, blur=16.0) as L:
            cam = f.lcam(par)
            x0, y0, x1, y1 = cam.view_rect(400)
            polys = []
            for k in range(int(x0 // 140), int(x1 // 140) + 1):
                x = k * 140 + 70 * _rnd(71, k)
                gy = ground_y(x * 0.7, seed=3) * 0.6 + 330
                r = _rnd(72, k)
                if r < 0.5:
                    polys += _grass(round(x, 1), round(gy, 1), 120 + 150 * _rnd(73, k), 800 + k, n=8, lean=10 * _srnd(74, k))
                elif r < 0.62:
                    polys += _fern(round(x, 1), round(gy, 1), 260 + 120 * _rnd(75, k), 900 + k, flip=1 if r < 0.56 else -1)
            # a thin ground mass along the very bottom (the grass grows out of it)
            n = 30
            floor = [(lerp(x0, x1, i / n), 330 + 25 * math.sin(lerp(x0, x1, i / n) / 300.0)) for i in range(n + 1)]
            polys.append(floor + [(x1, y1 + 3000), (x0, y1 + 3000)])
            for k in range(int(x0 // 3400), int(x1 // 3400) + 1):     # a rare near trunk
                if _rnd(81, k) < 0.55:
                    continue
                xc = k * 3400 + 1200 * _rnd(82, k)
                w = 200 + 100 * _rnd(83, k)
                polys.append([(xc - w / 2, 500), (xc + w / 2, 500), (xc + w * 0.47, -6000), (xc - w * 0.47, -6000)])
            _fill(L, polys, INK, a=strength)
FOREST = Forest()
