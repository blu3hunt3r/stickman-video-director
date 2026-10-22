"""RED sets: the Limbo forest. Endless, deterministic, side-scrolling along the trail.

    forest = FOREST                        # shared instance on the PATH terrain (or Forest(...))
    forest.draw_back(f, mood)              # sky, 4 fogged tree layers, mist, light shafts, thickets
    forest.draw_plane(f, mood)             # action-plane trunks, snow ground, the path stakes
    ...characters, feet on PATH.ground_y(x)...
    forest.draw_front(f, mood)             # snow lip, near stakes, blurred foreground trunks

Trees are generated per cell along each layer's x (hash of seed, layer, cell), so the same
tree is always at the same place, and geometry is cached. Every layer has its own ground
(`plane_ground`): the trail's profile seen through that layer's parallax, so the whole forest
descends with the path and far floors rise toward the horizon.

mood=None (or "auto") picks the mood from the camera x along the trail: daylight fog near
the village, darkening toward DEEP in the thicket stretch (PATH_MARKS['thicket']).
"""
import math

import cairo
import numpy as np

from engine import draw
from engine.core import clamp, smoothstep, fbm1, noise1, hash01, lerp
from .sets_common import (get_mood, mood_mix, mix, DAY, DEEP, SNOW, INK, view, plane, depth_layer,
                          ground_mist, backdrop, rnd, srnd, Mood, soft_layer, mist_band, fogged)
from .sets_terrain import PATH, PATH_MARKS, plane_ground, PathMarkers, _plane_ground


# ----------------------------------------------------------------------------- geometry utils
def _area(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a * 0.5


def _orient(pts):
    """Same winding for every polygon so batched non-zero fills union instead of cancel."""
    return pts if _area(pts) >= 0 else pts[::-1]


def _taper_limb(pts, r0, r1):
    """Closed outline of a tapered limb along pts (radius r0 -> r1), pointed tip."""
    n = len(pts)
    widths = [2 * lerp(r0, r1, (i / (n - 1)) ** 0.9) for i in range(n)]
    widths[-1] = max(0.6, r1 * 0.6)
    return _orient(draw.ribbon(pts, widths))


def _curve(p0, ang_deg, length, bend, n=6, droop=0.0):
    """Polyline from p0 heading ang_deg (0 = up, + = clockwise/right), bending by `bend`
    degrees along its length, plus gravity droop (px at the tip)."""
    pts = [p0]
    x, y = p0
    a = ang_deg
    step = length / (n - 1)
    for i in range(1, n):
        a += bend / (n - 1)
        r = math.radians(a)
        x += math.sin(r) * step
        y += -math.cos(r) * step + droop * (2 * i - 1) / ((n - 1) ** 2)
        pts.append((x, y))
    return pts


def _snow_on_limb(pts, radii, thick, seed=0, u0=0.12, u1=0.88):
    """Thin, lumpy snow lying on the upper side of a limb (only where it is not too steep)."""
    out_top, out_bot = [], []
    n = len(pts)
    any_ = False
    for i in range(n):
        u = i / (n - 1)
        p = pts[i]
        q0, q1 = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        tx, ty = q1[0] - q0[0], q1[1] - q0[1]
        L = math.hypot(tx, ty) or 1.0
        tx, ty = tx / L, ty / L
        nx, ny = ty, -tx                       # a normal
        if ny > 0:
            nx, ny = -nx, -ny                  # make it point up (y down)
        flat = clamp((abs(tx) - 0.5) / 0.35)   # steep limbs hold no snow
        env = clamp((u - u0) / 0.15) * clamp((u1 - u) / 0.2)
        lump = 0.55 + 0.9 * rnd(seed, i, 77) ** 2
        th = thick * flat * env * lump
        if th > 0.6:
            any_ = True
        r = radii[i]
        out_bot.append((p[0] + nx * r * 0.35, p[1] + ny * r * 0.35))
        out_top.append((p[0] + nx * (r + th), p[1] + ny * (r + th)))
    if not any_:
        return None
    return _orient(out_top + out_bot[::-1])


def _resample_line(pts, n):
    """Densify a polyline to n points (linear)."""
    out = []
    m = len(pts) - 1
    for i in range(n):
        u = i / (n - 1) * m
        k = min(int(u), m - 1)
        f = u - k
        out.append((pts[k][0] + (pts[k + 1][0] - pts[k][0]) * f, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * f))
    return out


# ----------------------------------------------------------------------------- layer specs
LAYERS = [
    # name     par   fog   blur  cell  trunk width   dens  branch  ground off
    dict(name="ghost", par=0.22, depth=0.92, blur=8.0, cell=95.0, w=(9.0, 22.0), dens=0.9, branch=0.12, off=-60.0),
    dict(name="far", par=0.38, depth=0.78, blur=5.5, cell=140.0, w=(16.0, 36.0), dens=0.85, branch=0.3, off=-35.0),
    dict(name="mid", par=0.56, depth=0.54, blur=4.6, cell=210.0, w=(26.0, 56.0), dens=0.8, branch=0.55, off=-15.0),
    dict(name="near", par=0.76, depth=0.30, blur=0.0, cell=300.0, w=(40.0, 84.0), dens=0.72, branch=0.85, off=0.0,
         direct=True),
]
PLANE = dict(name="plane", par=1.0, depth=0.0, blur=0.0, cell=560.0, w=(58.0, 120.0), dens=0.62, branch=1.0, off=0.0)
FG = dict(name="fg", par=1.6, depth=0.0, blur=18.0, cell=1250.0, w=(110.0, 210.0), dens=0.42, branch=0.7, off=520.0)


class Forest:
    """Endless winter forest along a terrain (default: the PATH trail).

    terrain      ground of the action plane (feet: terrain.ground_y)
    seed         changes every tree
    x_start      no trees before this world x (open fields past the village gate)
    thicket      (x0, x1) world range of the dark thicket band (eyes in the dark), or None
    markers      PathMarkers for the stakes ("the path"), or None
    clear        list of (x0, x1) world ranges kept free of action-plane trunks
    """

    def __init__(self, terrain=PATH, seed=7, x_start=None, thicket=None, markers=True,
                 dark_profile=True, clear=(), layers=None):
        self.terrain = terrain
        self.seed = seed
        self.x_start = PATH_MARKS["forest_edge"] if x_start is None and terrain is PATH else (x_start or -1e9)
        self.thicket = (PATH_MARKS["thicket"] if terrain is PATH else None) if thicket is None else thicket
        self.thicket_par = 0.9
        if markers is True:
            markers = PathMarkers(terrain) if terrain is PATH else None
        self.markers = markers or None
        self.dark_profile = dark_profile and terrain is PATH
        self.clear = list(clear)
        self.layers = [dict(l) for l in (layers or LAYERS)]
        for i, L in enumerate(self.layers):
            L["g"] = plane_ground(terrain, L["par"], L["off"])
            L["i"] = i
        self.plane = dict(PLANE, g=terrain.snow_y, i=10)
        self.fg = dict(FG, g=plane_ground(terrain, FG["par"], FG["off"]), i=11)
        self._cache = {}

    # ------------------------------------------------------------ profiles along the trail
    def density(self, xw):
        """Tree density multiplier at world x (0 before the forest edge)."""
        d = smoothstep(self.x_start, self.x_start + 1600.0, xw)
        if self.thicket:
            a, b = self.thicket
            d *= 1.0 + 0.35 * smoothstep(a - 1500, a, xw) * (1 - smoothstep(b, b + 1500, xw))
        return d

    def darkness(self, xw):
        """0 (daylight fog) .. 1 (DEEP) along the trail."""
        if not self.dark_profile:
            return 0.0
        a, b = self.thicket or (1e9, 1e9)
        return 0.55 * smoothstep(PATH_MARKS["deep"] - 1500, a, xw) + 0.45 * smoothstep(a - 800, a + 900, xw) \
            - 0.25 * smoothstep(b + 300, b + 2500, xw)

    def mood_at(self, xw):
        return mood_mix(DAY, DEEP, self.darkness(xw))

    def _mood(self, f, mood):
        if mood is None or mood == "auto":
            return self.mood_at(f.cam.x)
        return get_mood(mood)

    # ------------------------------------------------------------ tree generation
    def _tree(self, L, k):
        key = (L["i"], k)
        if key in self._cache:
            return self._cache[key]
        s = self.seed * 7919 + L["i"] * 104729
        par = L["par"]
        xl = (k + 0.5 + 0.8 * srnd(s, k, 1) * 0.5) * L["cell"]
        xw = 540.0 + (xl - 540.0) / par
        dens = L["dens"] * self.density(xw)
        tree = None
        clear = any(a <= xw <= b for a, b in self.clear) if L["name"] == "plane" else False
        if rnd(s, k, 2) < dens and not clear:
            w = lerp(L["w"][0], L["w"][1], rnd(s, k, 3) ** 1.3)
            tree = _make_tree(L, xl, float(L["g"](xl)), w, s * 31 + k, ground=L["g"])
        self._cache[key] = tree
        return tree

    def _trees(self, f, L, margin=None):
        par = L["par"]
        m = margin if margin is not None else L["w"][1] * 4 + 500
        vx0, vy0, vx1, vy1 = view(f, par, m)
        k0, k1 = int(math.floor(vx0 / L["cell"])), int(math.ceil(vx1 / L["cell"]))
        out = []
        for k in range(k0, k1 + 1):
            t = self._tree(L, k)
            if t is not None:
                out.append(t)
        return out

    # ------------------------------------------------------------ drawing a layer
    def _paint_layer(self, f, c, L, mood, trees, ground=True, extras=True, tint=0.0):
        """Paint one layer's trees, logs, ground and tufts on c. tint > 0 pre-fogs the colors
        (for layers drawn directly on the canvas instead of in a fogged offscreen)."""
        par = L["par"]
        vx0, vy0, vx1, vy1 = view(f, par, 80)
        if tint > 0:
            m0 = mood
            mood = Mood(m0.name, m0.sky, m0.fog_stops, fogged(m0, tint, m0.snow), fogged(m0, tint, m0.snow_dark),
                        m0.mist, m0.shaft, m0.shaft_a, m0.lamp_gain, ink=fogged(m0, tint), night=m0.night)
        ink = mood.ink
        bodies, limbs, snows = [], [], []
        for t in trees:
            bodies.append(t["body"])
            limbs.extend(t["limbs"])
            snows.extend(t["snow"])
        _fill(c, bodies, ink)
        _fill(c, limbs, ink)
        if extras:
            logs = self._logs(L, vx0, vx1)
            for lg in logs:
                _fill(c, lg["ink"], ink)
        if ground:
            g = L["g"]
            step = max(10.0, 14.0 / max(f.lcam(par).zoom, 0.1))
            xs = np.arange(vx0, vx1 + step, step)
            ys = np.asarray(g(xs), dtype=float)
            c.move_to(xs[0], vy1 + 50)
            for x, y in zip(xs, ys):
                c.line_to(x, y)
            c.line_to(xs[-1], vy1 + 50)
            c.close_path()
            y_top = float(ys.min())
            draw.linear(c, (0, y_top), (0, y_top + 520), [(0, mood.snow, 1), (0.2, mood.snow, 1), (1, mood.snow_dark, 1)])
            c.fill()
        mounds = []
        for t in trees:
            mounds.extend(t["mounds"])
            snows.extend(t["root_snow"])
        if extras:
            for lg in logs:
                snows.extend(lg["snow"])
        _fill(c, mounds, mood.snow)
        _fill(c, snows, mood.snow)
        if extras:
            tufts = self._tufts(L, vx0, vx1)
            _fill(c, tufts, ink)

    def _logs(self, L, x0, x1):
        """Fallen logs (with an upturned root plate) lying on a layer's ground."""
        if L["name"] not in ("mid", "near"):
            return []
        cell = 1700.0 if L["name"] == "near" else 1300.0
        out = []
        s = self.seed * 13 + L["i"] * 977
        for k in range(int(math.floor((x0 - 900) / cell)), int(math.ceil((x1 + 900) / cell)) + 1):
            key = ("log", L["i"], k)
            if key not in self._cache:
                lg = None
                xw = 540.0 + ((k + 0.5) * cell - 540.0) / L["par"]
                if rnd(s, k, 1) < 0.45 * self.density(xw):
                    lg = _make_log(L, (k + 0.3 + 0.4 * rnd(s, k, 2)) * cell, s * 17 + k)
                self._cache[key] = lg
            if self._cache[key]:
                out.append(self._cache[key])
        return out

    def _near_trunk(self, L, x, pad=1.6):
        """True if x is within pad trunk-widths of a trunk of layer L."""
        k = int(math.floor(x / L["cell"]))
        for kk in (k - 1, k, k + 1):
            t = self._tree(L, kk)
            if t is not None and abs(t["x"] - x) < t["w"] * pad + 40:
                return True
        return False

    def _tufts(self, L, x0, x1):
        """Dead grass / bracken poking out of the snow."""
        if L["name"] not in ("near", "plane", "mid"):
            return []
        cell = {"mid": 260.0, "near": 210.0, "plane": 170.0}[L["name"]]
        sc = {"mid": 0.7, "near": 0.85, "plane": 1.0}[L["name"]]
        s = self.seed * 101 + L["i"] * 31
        out = []
        for k in range(int(math.floor(x0 / cell)), int(math.ceil(x1 / cell)) + 1):
            key = ("tuft", L["i"], k)
            if key not in self._cache:
                polys = []
                xw = 540.0 + ((k + 0.5) * cell - 540.0) / L["par"]
                x = (k + rnd(s, k, 2)) * cell
                if rnd(s, k, 1) < 0.55 * clamp(self.density(xw) + 0.3) and not self._near_trunk(L, x):
                    polys = _make_tuft(x, float(L["g"](x)), sc * (0.6 + 0.8 * rnd(s, k, 3)), s * 7 + k)
                self._cache[key] = polys
            out.extend(self._cache[key])
        return out

    # ------------------------------------------------------------ public draw
    def draw_back(self, f, mood=None, glow=(560.0, 820.0), shafts=True, mist=True, haze_tex=True):
        """Everything behind the action plane: backdrop, far->near fogged tree layers with
        mist between them, light shafts, and the thicket band (if in view)."""
        mood = self._mood(f, mood)
        backdrop(f, mood, glow=glow, glow_r=1100.0, glow_a=0.45 if mood.night < 0.5 else 0.15)
        for i, L in enumerate(self.layers):
            trees = self._trees(f, L)
            if L.get("direct"):
                # sharp-ish near layer: pre-fogged colors straight onto the canvas (cheap)
                with plane(f, L["par"]) as c:
                    self._paint_layer(f, c, L, mood, trees, tint=L["depth"])
                if mist:
                    ground_mist(f, L["par"], L["g"], mood.mist, 0.45, up=320.0, down=150.0, step=110.0)
                if i == 3 and shafts and mood.shaft_a > 0:
                    self.draw_shafts(f, mood)
                continue
            with depth_layer(f, mood, L["par"], L["depth"], blur=L["blur"]) as c:
                self._paint_layer(f, c, L, mood, trees, extras=L["name"] != "ghost")
                if mist:
                    # mist lying on this layer's floor, inside the layer (no extra composite)
                    vx0, vy0, vx1, vy1 = view(f, L["par"], 200)
                    xs = np.linspace(vx0, vx1, max(3, int((vx1 - vx0) / 110) + 2))
                    mist_band(c, xs, np.asarray(L["g"](xs), dtype=float), mood.mist,
                              0.62 if i < 2 else 0.45, up=320.0 + 120 * (2 - min(i, 2)), down=150.0)
            if i == 1 and haze_tex:
                f.haze(mood.mist, 0.22, y0=None, y1=None, tex=0.85, tex_scale=0.7, scroll=(9.0, -1.5),
                       seed=self.seed, par=0.4)
            if i == 3 and shafts and mood.shaft_a > 0:
                self.draw_shafts(f, mood)
        if self.thicket:
            self.draw_thicket(f, mood)

    def draw_plane(self, f, mood=None, ground=True, markers=True):
        """The action plane behind characters: trunks, snow ground, tufts, path stakes."""
        mood = self._mood(f, mood)
        L = self.plane
        trees = self._trees(f, L)
        with plane(f, 1.0) as c:
            self._paint_layer(f, c, L, mood, trees, ground=False, extras=False)
        if ground:
            self.terrain.draw_back(f, mood)
        with plane(f, 1.0) as c:
            snows, mounds = [], []
            for t in trees:
                mounds.extend(t["mounds"])
                snows.extend(t["root_snow"])
            _fill(c, mounds, mood.snow)
            _fill(c, snows, mood.snow)
            vx0, vy0, vx1, vy1 = view(f, 1.0, 100)
            _fill(c, self._tufts(L, vx0, vx1), mood.ink)
        if markers and self.markers:
            self.markers.draw_back(f, mood)

    def draw_front(self, f, mood=None, lip=True, sink=6.0, near_markers=True, occluders=True,
                   keep_clear=None):
        """In front of characters: the snow lip (feet sink `sink` px), near-side stakes,
        and the blurred foreground trunks and brambles. keep_clear=(sx0, sx1) screen-x band
        where foreground trunks fade out (keeps the subject readable); None = no fading."""
        mood = self._mood(f, mood)
        if lip:
            self.terrain.draw_front(f, mood, sink=sink)
        if near_markers and self.markers:
            self.markers.draw_front(f, mood)
        if occluders:
            L = self.fg
            # zoomed far out (zoom < ~0.7) the foreground planes shrink to blurry specks
            # at the ground line: fade them away instead
            fade_t = smoothstep(0.3, 0.6, f.lcam(L["par"]).zoom)
            fade_b = smoothstep(0.35, 0.65, f.lcam(self.FGV["par"]).zoom)
            trees = self._trees(f, L) if fade_t > 0.01 else []
            brambles = self._brambles(f) if fade_b > 0.01 else []
            if not trees and not brambles:
                return
            cam = f.lcam(L["par"])
            if brambles:
                with f.layer(par=self.FGV["par"], blur=self.FGV["blur"]) as c:
                    _fill(c, brambles, mood.ink, fade_b)
            if trees:
                with f.layer(par=L["par"], blur=L["blur"]) as c:
                    for t in trees:
                        a = 1.0
                        if keep_clear:
                            sx = (t["x"] - cam.x) * cam.zoom + 540.0
                            hw = t["w"] * cam.zoom * 0.7
                            d = max(keep_clear[0] - (sx + hw), (sx - hw) - keep_clear[1], 0.0)
                            a = smoothstep(0.0, 160.0, d)
                        a *= fade_t
                        if a > 0.01:
                            _fill(c, [t["body"]], mood.ink, a)

    def draw(self, f, mood=None, **kw):
        """Whole set without characters (style frames, establishing shots)."""
        self.draw_back(f, mood)
        self.draw_plane(f, mood)
        self.draw_front(f, mood)

    # ------------------------------------------------------------ light shafts
    def draw_shafts(self, f, mood=None, par=0.6, strength=1.0):
        """Soft additive beams slanting down between the trunks (light from upper left),
        drifting in strength like light through moving cloud."""
        mood = self._mood(f, mood)
        a0 = mood.shaft_a * strength
        if a0 <= 0:
            return
        g = plane_ground(self.terrain, par, -20.0)
        vx0, vy0, vx1, vy1 = view(f, par, 900)
        cell = 430.0
        s = self.seed * 3 + 5
        with soft_layer(f, par, k=6, op="add", blur=22.0) as A:
            for k in range(int(math.floor(vx0 / cell)), int(math.ceil(vx1 / cell)) + 1):
                if rnd(s, k, 1) > 0.55:
                    continue
                x = (k + rnd(s, k, 2)) * cell
                gy = float(g(x))
                top = gy - 2800.0
                slant = 0.30 + 0.05 * srnd(s, k, 3)
                w0 = 40 + 110 * rnd(s, k, 4)
                w1 = w0 * (1.8 + 0.8 * rnd(s, k, 5))
                xt = x - slant * (gy - top)
                inten = a0 * (0.5 + 0.5 * rnd(s, k, 6)) * (0.55 + 0.45 * fbm1(f.t * 0.13 + k * 3.1, s))
                pts = [(xt - w0 / 2, top), (xt + w0 / 2, top), (x + w1 / 2, gy), (x - w1 / 2, gy)]
                draw.linear(A, (xt, top), (x, gy), [(0, mood.shaft, 0), (0.3, mood.shaft, inten),
                                                    (0.75, mood.shaft, inten * 0.75), (1, mood.shaft, 0)])
                draw.poly(A, pts)
                A.fill()

    # ------------------------------------------------------------ thicket (eyes in the dark)
    def thicket_ground(self, xl):
        return _plane_ground(self.terrain, xl, self.thicket_par, -8.0)

    def _thicket_geom(self, k):
        key = ("thicket", k)
        if key in self._cache:
            return self._cache[key]
        a, b = self.thicket
        par = self.thicket_par
        cell = 120.0
        xl = (k + 0.5) * cell
        xw = 540.0 + (xl - 540.0) / par
        geo = None
        if a - 200 <= xw <= b + 200:
            s = self.seed * 41 + 3
            edge = smoothstep(a - 200, a + 500, xw) * (1 - smoothstep(b - 500, b + 200, xw))
            gap = rnd(s, k // 4, 9) < 0.12        # occasional gaps of ~4 cells
            if not gap and edge > 0.02:
                geo = _make_bramble(xl, float(self.thicket_ground(xl)), cell,
                                    (180 + 150 * rnd(s, k, 1)) * (0.4 + 0.6 * edge), s * 13 + k)
        self._cache[key] = geo
        return geo

    def draw_thicket(self, f, mood=None, depth=0.30):
        """The dark undergrowth band behind the path in the thicket stretch (layer par 0.9).
        Glowing eyes can pace along `eye_track(x)` inside it."""
        if not self.thicket:
            return
        mood = self._mood(f, mood)
        par = self.thicket_par
        vx0, vy0, vx1, vy1 = view(f, par, 300)
        a, b = self.thicket
        xa, xb = 540 + (a - 740 - 540) * par, 540 + (b + 740 - 540) * par
        if vx1 < xa or vx0 > xb:
            return
        polys, snow, layered = [], [], []
        for k in range(int(math.floor(vx0 / 120.0)), int(math.ceil(vx1 / 120.0)) + 1):
            g = self._thicket_geom(k)
            if g:
                polys.extend(g["ink"])
                snow.extend(g["snow"])
                layered.extend(g["layered"])
        if not polys:
            return
        ink_c, snow_c = fogged(mood, depth), fogged(mood, depth, mood.snow)
        with plane(f, par) as c:
            _fill(c, polys, ink_c)
            _fill(c, snow, snow_c)
            for ink, sn in layered:
                _fill(c, ink, ink_c)
                _fill(c, sn, snow_c)

    def eye_track(self, xw, height=0.5):
        """Where eyes can glow inside the thicket band at world x: returns (xl, yl, par)
        in the thicket layer's coords (draw them with f.emit(par=par) / f.layer(par=par)).
        height: 0 = ground, 1 = top of the bramble mass. None if no thicket there."""
        if not self.thicket:
            return None
        par = self.thicket_par
        xl = 540.0 + (xw - 540.0) * par
        k = int(math.floor(xl / 120.0))
        g = self._thicket_geom(k)
        if not g:
            return None
        return (xl, float(self.thicket_ground(xl)) - g["h"] * (0.12 + 0.7 * height), par)

    def thicket_has_cover(self, xw):
        """True if the thicket band is dense at world x (eyes hidden in gaps otherwise)."""
        return self.eye_track(xw) is not None

    # ------------------------------------------------------------ foreground vegetation
    FGV = dict(par=1.32, blur=7.0, cell=560.0, off=230.0)

    def _fg_ground(self, xl):
        return _plane_ground(self.terrain, xl, self.FGV["par"], self.FGV["off"])

    def _brambles(self, f):
        """Out-of-focus tall grass and bramble arcs along the bottom of the frame."""
        V = self.FGV
        par = V["par"]
        vx0, vy0, vx1, vy1 = view(f, par, 500)
        cell = V["cell"]
        s = self.seed * 59 + 1
        out = []
        for k in range(int(math.floor(vx0 / cell)), int(math.ceil(vx1 / cell)) + 1):
            key = ("fgv", k)
            if key not in self._cache:
                geo = None
                xl = (k + rnd(s, k, 2)) * cell
                xw = 540.0 + (xl - 540.0) / par
                if rnd(s, k, 1) < 0.6 * clamp(self.density(xw) + 0.5):
                    geo = _make_fg_clump(xl, float(self._fg_ground(xl)), 0.8 + 0.7 * rnd(s, k, 3), s * 5 + k)
                self._cache[key] = geo
            if self._cache[key]:
                out.extend(self._cache[key])
        return out


# ----------------------------------------------------------------------------- builders
def _fill(c, polys, rgb, a=1.0):
    n = 0
    for p in polys:
        if p is not None and len(p) >= 3:
            c.move_to(*p[0])
            for q in p[1:]:
                c.line_to(*q)
            c.close_path()
            n += 1
    if n:
        draw.fill(c, rgb, a)


def _make_tree(L, x, base_y, w, seed, ground=None, height=None):
    """One winter tree: tall straight trunk (root flare, knots, stubs), sparse thin limbs
    with twigs, snow on the limbs and a drift mound at the base. Layer coords.
    height: None = the trunk runs out of frame (5200 px); a number = a whole tree whose
    trunk tapers to a point at that height (seen from afar, e.g. the valley view)."""
    kind = L["name"]
    far = kind in ("ghost", "far")
    H = 5200.0 if height is None else float(height)
    lean = srnd(seed, 1) * (2.5 if not far else 1.5) + (srnd(seed, 2) * 6.0 if rnd(seed, 3) < 0.12 else 0.0)
    tl = math.tan(math.radians(lean))
    snag = rnd(seed, 4) < (0.10 if kind in ("near", "plane", "mid") else 0.05)
    top_h = (900 + 900 * rnd(seed, 5)) * (w / 60.0) ** 0.3 if snag else H
    hs = [0.0, 0.08, 0.2, 0.4, 0.7, 1.1, 1.6]
    hs = [h * w for h in hs] + [w * 2.4 + i * (220.0 if not far else 420.0) for i in range(0, 40)]
    hs = [h for h in hs if h < top_h] + [top_h]

    def center(h):
        return x + tl * h + w * 0.12 * fbm1(h / 700.0, seed + 11) * min(1.0, h / (3 * w))

    def width(h):
        flare = 1.0 + 0.95 * math.exp(-h / (0.55 * w)) + 0.25 * math.exp(-h / (1.6 * w))
        taper = 1.0 - 0.22 * clamp(h / 3000.0)
        if height is not None:
            taper *= max(0.04, 1.0 - (h / H) ** 1.6)
        return w * flare * taper

    left, right = [], []
    for h in hs:
        cx, ww = center(h), width(h)
        jl = 1.0 + 0.05 * srnd(seed, int(h), 7)
        jr = 1.0 + 0.05 * srnd(seed, int(h), 8)
        y = base_y - h
        left.append((cx - ww * 0.5 * jl, y))
        right.append((cx + ww * 0.5 * jr, y))
    # roots: the flare digs under the snow, following the slope on both sides
    G = ground if ground is not None else (lambda xx: base_y)
    lx0, rx0 = left[0][0] - w * 0.35, right[0][0] + w * 0.35
    left[0] = (lx0, float(G(lx0)) + 40)
    right[0] = (rx0, float(G(rx0)) + 40)
    left.insert(1, (left[1][0] - w * 0.05, min(left[1][1], float(G(left[1][0])) + 6)))
    right.insert(1, (right[1][0] + w * 0.05, min(right[1][1], float(G(right[1][0])) + 6)))
    if snag:
        # broken jagged top
        cx, ww = center(top_h), width(top_h)
        jag = [(cx + ww * 0.5, base_y - top_h), (cx + ww * 0.2, base_y - top_h - ww * (0.8 + rnd(seed, 21))),
               (cx, base_y - top_h - ww * 0.3), (cx - ww * 0.25, base_y - top_h - ww * (1.6 + 1.2 * rnd(seed, 22))),
               (cx - ww * 0.5, base_y - top_h - ww * 0.2)]
        body = right + jag + left[::-1]
    else:
        body = right + left[::-1]
    body = _orient(body)

    limbs, snow = [], []
    nb = 0
    if not far or rnd(seed, 30) < L["branch"]:
        nb = int(round((1 + 4 * rnd(seed, 31)) * L["branch"]))
    vis_top = min(top_h - w, 2400.0)
    for b in range(nb):
        hb = 260 + (vis_top - 260) * rnd(seed, 40 + b) ** 0.8
        if hb > top_h - 40:
            continue
        side = -1 if rnd(seed, 50 + b) < 0.5 else 1
        ang = side * (38 + 42 * rnd(seed, 60 + b))
        length = w * (2.2 + 4.5 * rnd(seed, 70 + b)) * (1.0 if not far else 0.6)
        length = min(length, 560.0)
        r0 = width(hb) * (0.16 + 0.14 * rnd(seed, 80 + b))
        p0 = (center(hb) - side * width(hb) * 0.1, base_y - hb)
        droop = length * 0.12 * rnd(seed, 85 + b)
        pts = _curve(p0, ang, length, side * (8 + 18 * rnd(seed, 90 + b)), n=6, droop=droop)
        limbs.append(_taper_limb(pts, r0, 0.8))
        radii = [lerp(r0, 0.8, (i / 5) ** 0.9) for i in range(6)]
        if not far:
            dp = _resample_line(pts, 14)
            dr = [lerp(r0, 0.8, (i / 13) ** 0.9) for i in range(14)]
            sn = None
            if r0 > 4.0 and rnd(seed, 88 + b) < 0.8:
                sn = _snow_on_limb(dp, dr, max(1.6, r0 * 0.3), seed + b, u0=0.1 + 0.25 * rnd(seed, 86 + b),
                                   u1=0.45 + 0.4 * rnd(seed, 87 + b))
            if sn:
                snow.append(sn)
            # twigs
            for tw in range(int(1 + 3 * rnd(seed, 100 + b))):
                u = 0.35 + 0.55 * rnd(seed, 110 + b * 7 + tw)
                i = min(4, int(u * 5))
                q = pts[i]
                tang = ang + side * (-25 + 70 * rnd(seed, 120 + b * 7 + tw)) * (-1 if tw % 2 else 1)
                tl2 = length * (0.18 + 0.3 * rnd(seed, 130 + b * 7 + tw))
                tp = _curve(q, tang, tl2, side * 10, n=4)
                limbs.append(_taper_limb(tp, max(0.8, radii[i] * 0.5), 0.5))
    # broken stubs: outline detail
    for b in range(int(3 * rnd(seed, 200)) if not far else int(2 * rnd(seed, 200))):
        hb = 200 + (vis_top - 200) * rnd(seed, 210 + b)
        if hb > top_h - 60:
            continue
        side = -1 if rnd(seed, 220 + b) < 0.5 else 1
        p0 = (center(hb) + side * width(hb) * 0.3, base_y - hb)
        L2 = width(hb) * (0.35 + 0.5 * rnd(seed, 230 + b))
        ang = side * (55 + 30 * rnd(seed, 240 + b))
        p1 = (p0[0] + math.sin(math.radians(ang)) * L2, p0[1] - math.cos(math.radians(ang)) * L2)
        r = width(hb) * 0.13
        limbs.append(_orient([(p0[0], p0[1] - r * 1.4), (p1[0], p1[1] - r * 0.3), (p1[0] + side * r * 0.3, p1[1] + r * 0.5),
                              (p0[0], p0[1] + r * 1.2)]))
        if not far:
            snow.append(_orient([(p0[0], p0[1] - r * 1.5), (p1[0], p1[1] - r * 0.4), (p1[0], p1[1] - r * 1.4),
                                 (p0[0] + side * r, p0[1] - r * 2.6)]))
    # roots arching out of the snow + snow on them
    root_snow = []
    if kind in ("near", "plane", "mid"):
        for side in (-1, 1):
            if rnd(seed, 300 + side) < 0.65:
                rl = w * (0.55 + 0.5 * rnd(seed, 310 + side))
                x0r = x + side * w * 0.4
                x1r = x0r + side * rl * 0.5
                x2r = x0r + side * rl
                pts = [(x0r, float(G(x0r)) - w * 0.16),
                       (x1r, float(G(x1r)) - w * 0.07 * (0.6 + rnd(seed, 320 + side))),
                       (x2r, float(G(x2r)) + 8)]
                limbs.append(_taper_limb(pts, w * 0.12, w * 0.04))
    mound_w = w * 3.2
    mound = []
    n = 12
    for i in range(n + 1):
        u = i / n
        xx = x - mound_w / 2 + mound_w * u
        hh = math.sin(math.pi * u) ** 1.5 * w * (0.20 + 0.06 * srnd(seed, 400 + i))
        mound.append((xx, float(G(xx)) - hh))
    for i in range(n, -1, -1):
        xx = x - mound_w / 2 + mound_w * i / n
        mound.append((xx, float(G(xx)) + 14))
    return dict(body=body, limbs=limbs, snow=snow, mounds=[_orient(mound)], root_snow=root_snow, x=x, w=w)


def _make_log(L, x, seed):
    """A fallen trunk lying along the layer ground: broken far end, a few snapped branch
    stubs, snow along the top, and the upturned root plate (seen edge-on, roots radiating)."""
    g = L["g"]
    length = 600 + 800 * rnd(seed, 1)
    r = (20 + 22 * rnd(seed, 2)) * (1.35 if L["name"] == "near" else 1.0)
    d = 1 if rnd(seed, 3) < 0.5 else -1
    n = 10
    pts, radii = [], []
    for i in range(n):
        u = i / (n - 1)
        xx = x + d * length * u
        rr = r * (1.0 - 0.4 * u)
        pts.append((xx, float(g(xx)) - rr * 0.72))
        radii.append(rr)
    body = draw.ribbon(pts, [2 * rr for rr in radii])
    # jagged broken far end
    ex, ey = pts[-1]
    re = radii[-1]
    half = len(body) // 2
    jag = [(ex + d * re * 0.6, ey - re * 0.6), (ex + d * re * 0.15, ey - re * 0.1), (ex + d * re * 0.9, ey + re * 0.2),
           (ex + d * re * 0.3, ey + re * 0.7)]
    body = body[:half] + (jag if d > 0 else jag[::-1]) + body[half:]
    ink = [_orient(body)]
    snow = []
    sn = _snow_on_limb(_resample_line(pts, 16), [lerp(radii[0], radii[-1], i / 15) for i in range(16)], r * 0.32, seed,
                       u0=0.05, u1=0.95)
    if sn:
        snow.append(sn)
    # snapped branch stubs on the top side
    for j in range(2 + int(3 * rnd(seed, 4))):
        u = 0.2 + 0.7 * rnd(seed, 5 + j)
        i = int(u * (n - 1))
        p = pts[i]
        rr = radii[i]
        ang = d * (20 + 50 * rnd(seed, 15 + j)) * (1 if rnd(seed, 25 + j) < 0.7 else -1)
        q = _curve((p[0], p[1] - rr * 0.6), ang, rr * (1.2 + 2.2 * rnd(seed, 35 + j)), d * 10, n=3)
        ink.append(_taper_limb(q, rr * 0.28, rr * 0.12))
    # root plate: an edge-on slab of soil and roots, standing at the thick end
    cx, cy = x - d * r * 0.15, float(g(x)) - r * 1.9
    R = r * (2.7 + 0.9 * rnd(seed, 6))
    m = 26
    plate = []
    for i in range(m):
        th = 2 * math.pi * i / m
        spike = (1.25 + 0.6 * rnd(seed, 40 + i)) if i % 2 == 0 else (0.85 + 0.15 * rnd(seed, 70 + i))
        rx, ry = R * 0.34 * spike, R * spike
        plate.append((cx + math.cos(th) * rx, cy + math.sin(th) * ry))
    ink.append(_orient(plate))
    for i in range(7):                                         # long thin roots sticking out
        th = -math.pi * (0.1 + 0.8 * rnd(seed, 90 + i)) if i % 2 else math.pi * (0.2 + 0.6 * rnd(seed, 90 + i))
        p0 = (cx + math.cos(th) * R * 0.25, cy + math.sin(th) * R * 0.7)
        ang = math.degrees(math.atan2(math.cos(th), -math.sin(th))) - d * 30
        q = _curve(p0, ang + srnd(seed, 95 + i) * 25, R * (0.5 + 0.6 * rnd(seed, 99 + i)), srnd(seed, 97 + i) * 50, n=4)
        ink.append(_taper_limb(q, max(1.5, r * 0.10), 0.5))
    top = [(cx - R * 0.30, cy - R * 0.80), (cx - R * 0.05, cy - R * 1.02), (cx + R * 0.22, cy - R * 0.86)]
    snow.append(_orient(top + [(cx + R * 0.15, cy - R * 0.78), (cx - R * 0.2, cy - R * 0.72)]))
    return dict(ink=ink, snow=snow)


def _make_fg_clump(x, gy, sc, seed):
    """Foreground clump (out of focus): tall dry grass, a few broken stems, bramble arcs
    with thorns. Big: blades 140-420 px * sc."""
    polys = []
    n = 9 + int(10 * rnd(seed, 1))
    for i in range(n):
        h = (140 + 280 * rnd(seed, 10 + i) ** 1.5) * sc
        a = srnd(seed, 20 + i) * 28 + (8 if i % 3 == 0 else 0)
        bx = x + srnd(seed, 30 + i) * 90 * sc
        bend = srnd(seed, 40 + i) * 45
        pts = _curve((bx, gy + 20), a, h, bend, n=5)
        if rnd(seed, 45 + i) < 0.18:                     # broken stem: a kink near the top
            kx, ky = pts[3]
            pts[4] = (kx + (14 if i % 2 else -14) * sc * 3, ky + 20 * sc)
        polys.append(_taper_limb(pts, (4.5 + 2.5 * rnd(seed, 50 + i)) * sc, 0.6))
        if rnd(seed, 55 + i) < 0.25:                     # seed head
            hx, hy = pts[-1]
            polys.append(_orient(draw.ellipse_pts((hx, hy - 8 * sc), 5 * sc, 16 * sc, n=10, angle=a)))
    side = 1 if rnd(seed, 66) < 0.5 else -1
    for j in range(1 + int(1.8 * rnd(seed, 60))):        # bramble arcs with thorns, all leaning one way
        p0 = (x + srnd(seed, 61 + j) * 60 * sc, gy + 10)  # (symmetric arcs read as legs)
        L = (200 + 220 * rnd(seed, 62 + j)) * sc
        pts = _curve(p0, side * (8 + 30 * rnd(seed, 63 + j)), L, side * (55 + 55 * rnd(seed, 64 + j)), n=9)
        polys.append(_taper_limb(pts, 5.5 * sc, 2.0 * sc))
        for i in range(1, 8):
            px, py = pts[i]
            qx, qy = pts[i + 1]
            tx, ty = qx - px, qy - py
            Lt = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / Lt, tx / Lt
            if i % 2:
                nx, ny = -nx, -ny
            th = 11 * sc
            polys.append(_orient([(px - tx / Lt * 4 * sc, py - ty / Lt * 4 * sc), (px + tx / Lt * 4 * sc, py + ty / Lt * 4 * sc),
                                  (px + nx * th + tx / Lt * 6 * sc, py + ny * th + ty / Lt * 6 * sc)]))
    return polys


def _make_tuft(x, gy, sc, seed):
    """Dead grass / bracken: thin curved blades out of the snow."""
    polys = []
    n = 4 + int(7 * rnd(seed, 1))
    for i in range(n):
        h = (38 + 60 * rnd(seed, 10 + i)) * sc
        a = srnd(seed, 20 + i) * 34
        bx = x + srnd(seed, 30 + i) * 22 * sc
        pts = _curve((bx, gy + 4), a, h, srnd(seed, 40 + i) * 50, n=4)
        polys.append(_taper_limb(pts, 2.2 * sc, 0.4))
    return polys


def _make_bramble(x, gy, w, h, seed, n=7):
    """A dark bramble / young-spruce mass: overlapping blobs plus a ragged crown of thin
    stems and thorny twigs. Returns dict(ink=[polys], snow=[polys], h=height)."""
    ink, snow = [], []
    # body: a lumpy hill shape
    pts = []
    m = 14
    for i in range(m + 1):
        u = i / m
        xx = x - w * 0.75 + w * 1.5 * u
        hh = h * (math.sin(math.pi * u) ** 0.7) * (0.65 + 0.35 * rnd(seed, i)) * 0.8
        pts.append((xx, gy - hh))
    pts += [(x + w * 0.75, gy + 260), (x - w * 0.75, gy + 260)]
    ink.append(_orient(pts))
    # stems and twigs above the mass
    for i in range(n):
        u = rnd(seed, 50 + i)
        bx = x - w * 0.6 + w * 1.2 * u
        top = h * (0.55 + 0.65 * rnd(seed, 60 + i))
        ang = srnd(seed, 70 + i) * 26
        p = _curve((bx, gy - h * 0.3), ang, top, srnd(seed, 80 + i) * 40, n=5)
        ink.append(_taper_limb(p, 3.2, 0.5))
        for j in range(3):
            q = p[1 + j]
            side = -1 if (i + j) % 2 else 1
            tp = _curve(q, ang + side * (40 + 30 * rnd(seed, 90 + i * 5 + j)), 26 + 40 * rnd(seed, 95 + i * 5 + j), side * 15, n=3)
            ink.append(_taper_limb(tp, 1.6, 0.4))
    # a young spruce now and then: drooping tiers, thin snow on each tier
    layered = []
    if rnd(seed, 120) < 0.4:
        layered = _make_spruce(x + srnd(seed, 121) * w * 0.4, gy, h * (1.3 + 0.8 * rnd(seed, 122)), seed + 7)
    # snow caps on the hummocks
    cap = []
    for i in range(3, m - 2):
        cap.append((pts[i][0], pts[i][1] - 3))
    for i in range(m - 3, 2, -1):
        cap.append((pts[i][0], pts[i][1] + 7 + 5 * rnd(seed, 200 + i)))
    if len(cap) >= 3:
        snow.append(_orient(cap))
    return dict(ink=ink, snow=snow, h=h, layered=layered)


def _make_spruce(x, gy, H, seed, tiers=None):
    """Young spruce: a stem with drooping, ragged tiers and thin snow on top of each tier.
    Returns a list of (ink_polys, snow_polys) in painter's order (lowest tier first)."""
    tiers = tiers or (6 + int(3 * rnd(seed, 1)))
    out = [([_taper_limb([(x, gy + 10), (x, gy - H)], H * 0.025 + 2, 1.0)], [])]
    for k in range(tiers):
        u = k / tiers
        ty = gy - H * (0.12 + 0.86 * u)
        tw = (H * 0.30) * (1 - u) ** 0.9 + 12
        th = H / tiers * 1.25
        droop = tw * 0.35
        ink, snow = [], []
        for side in (-1, 1):
            j = 1.0 + 0.18 * srnd(seed, k, side)
            tip = (x + side * tw * j, ty + droop)
            tier = [(x, ty - th * 0.55), (x + side * tw * 0.45, ty - th * 0.12), tip,
                    (x + side * tw * 0.78, ty + droop * 0.55), (x + side * tw * 0.62, ty + droop * 0.95),
                    (x + side * tw * 0.4, ty + droop * 0.5), (x + side * tw * 0.22, ty + droop * 0.75), (x, ty + th * 0.2)]
            ink.append(_orient(tier))
            if rnd(seed, k, side, 4) < 0.55:
                # a soft clump of snow resting on the outer bough
                e1 = (x + side * tw * 0.45, ty - th * 0.12)
                u0, u1 = 0.1 + 0.2 * rnd(seed, k, side, 5), 0.55 + 0.25 * rnd(seed, k, side, 6)
                hh = (3.0 + 4.0 * rnd(seed, k, side, 3)) * (1 + tw / 160.0)
                clump = []
                for i in range(7):
                    u = u0 + (u1 - u0) * i / 6
                    px, py = e1[0] + (tip[0] - e1[0]) * u, e1[1] + (tip[1] - e1[1]) * u
                    clump.append((px, py - hh * math.sin(math.pi * i / 6) ** 0.8 + 1.0))
                for i in range(6, -1, -1):
                    u = u0 + (u1 - u0) * i / 6
                    px, py = e1[0] + (tip[0] - e1[0]) * u, e1[1] + (tip[1] - e1[1]) * u
                    clump.append((px, py + 2.5 * math.sin(math.pi * i / 6)))
                snow.append(_orient(clump))
        out.append((ink, snow))
    return out


FOREST = Forest()
