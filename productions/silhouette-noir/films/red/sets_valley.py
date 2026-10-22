"""RED sets: the ridge (S05) and the valley view from its crest (S06).

RIDGE_SET (S05) is a side-scrolling set on the RIDGE terrain: the trail with its stakes ends
at x ~ 60 (she leaves the path there), then the slope climbs through deep snow (draw_front
hides her legs) past thinning, wind-bent trees to the crest at RIDGE.crest_x, beyond which
the ground drops away into the foggy valley.

    R = RIDGE_SET
    R.draw_back(f, mood)    ->  characters (feet on RIDGE.ground_y)  ->  R.draw_front(f, mood)
    R.draw_plane(f, mood)   (between the two: trunks, snow, stakes)

VALLEY_VIEW (S06) is her POV from the crest: a 2.5D matte painting in its own space (at rest
the camera Camera(540, 960, 1) shows the whole valley). Bands of fogged ridges, the valley
forest, the clearing with the cottage wrapped in web (the real CLEARING_SET cottage, web,
trees and hoods, miniaturized), trees around it hung with hoods, the path's stakes winding up
the frame from the crest at the bottom to the clearing. Every band has its own parallax, so
tilts, cranes and push-ins have depth.

    V = VALLEY_VIEW
    f.set_camera(V.camera("start"))          # or V.camera_on(V.cottage_point(), zoom=4.0)
    V.draw(f, mood, t, hoods=1.0)            # hoods: 0..1 fraction shown (reveal on [hoods])
    V.hood_screen_positions(f, t)            # [(x, y, size)] screen px: for the Bass grid
"""
import math

import numpy as np

from engine import draw
from engine.core import clamp, lerp, smoothstep, fbm1
from engine.frame import Camera
from .sets_common import (get_mood, mix, SNOW, HOOD_RED, DAY, view, plane, backdrop, soft_layer, glow,
                          fogged, rnd, srnd, mist_band, ground_mist, tinted)
from .sets_terrain import RIDGE, PathMarkers, stake_shape
from .sets_forest import Forest, LAYERS, _orient, _fill, _taper_limb, _make_tree, _make_spruce
from .sets_cottage import CLEARING_SET, Hoods, _crown_tree
from .sets_props import hood_poly


# ============================================================================ S05: the ridge
class RidgeForest(Forest):
    """Forest along the RIDGE terrain: full forest along the trail (x < 0), thinning up the
    slope to a bare, wind-swept crest. Beyond the crest the trees are whole spruces growing on
    the falling slope, their tops just below the crest line: the drop reads."""

    def density(self, xw):
        c = RIDGE.crest_x
        if xw < 0:
            return 1.0
        if xw < c + 300:
            return lerp(1.0, 0.12, smoothstep(0.0, c - 300.0, xw))
        return lerp(0.12, 0.8, smoothstep(c + 300.0, c + 1500.0, xw))

    def _tree(self, L, k):
        key = (L["i"], k)
        if key in self._cache:
            return self._cache[key]
        tree = Forest._tree(self, L, k)
        if tree is not None:
            par = L["par"]
            c = RIDGE.crest_x
            xw = 540.0 + (tree["x"] - 540.0) / par
            if xw > c + 200.0:
                x0 = tree["x"]
                tree = None
                if L["name"] != "fg":            # open air beyond the crest: no occluders
                    s = self.seed * 7919 + L["i"] * 104729 + k * 13
                    gc = float(L["g"](540.0 + (c - 540.0) * par))
                    gy = float(L["g"](x0))
                    top = gc + (40.0 + 380.0 * rnd(s, 7)) * par
                    tree = _spruce_tree(x0, gy, gy - top, s) if gy - top > 140.0 * par else None
                self._cache[key] = tree
        return tree


def _spruce_tree(x, gy, H, seed):
    """A whole spruce in the tree-dict format the Forest layers paint (no snow: the lee)."""
    tiers = _make_spruce(x, gy, H, seed)
    return dict(body=tiers[0][0][0], limbs=[p for ink, snow in tiers[1:] for p in ink], snow=[], mounds=[],
                root_snow=[], x=x, w=H * 0.05)


class Ridge:
    """S05 set. Delegates to a RidgeForest with the trail's stakes ending at x ~ 60, adds
    spindrift blowing off the crest."""

    def __init__(self, seed=23):
        self.T = RIDGE
        self.markers = PathMarkers(RIDGE, x_start=-4400.0, x_end=80.0, seed=seed)
        self.forest = RidgeForest(terrain=RIDGE, seed=seed, markers=self.markers, clear=[(RIDGE.crest_x - 500, RIDGE.crest_x + 300)])
        self.crest = RIDGE.crest

    def draw_back(self, f, mood=None, **kw):
        self.forest.draw_back(f, get_mood(mood or DAY), **kw)

    def draw_plane(self, f, mood=None, **kw):
        self.forest.draw_plane(f, get_mood(mood or DAY), **kw)

    def draw_front(self, f, mood=None, t=None, spindrift=1.0, **kw):
        """Deep-snow lip (legs vanish below RIDGE.snow_y), the lee face of the crest in
        shadow with its cornice, near stakes, foreground, and spindrift: snow smoking off the
        crest in the wind. kw: Forest.draw_front options (sink, occluders, keep_clear, ...)."""
        mood = get_mood(mood or DAY)
        occ = kw.pop("occluders", True)
        self.forest.draw_front(f, mood, occluders=False, **kw)
        self._lee(f, mood, kw.get("sink", 6.0))
        if occ:
            self.forest.draw_front(f, mood, lip=False, near_markers=False, occluders=True,
                                   keep_clear=kw.get("keep_clear"))
        if spindrift > 0:
            self.spindrift(f, mood, f.t if t is None else t, spindrift)

    def _lee(self, f, mood, sink=6.0):
        """Beyond the crest the face drops away in shadow (light from the upper left), under a
        bright overhanging cornice lip."""
        c = RIDGE.crest_x
        vx0, vy0, vx1, vy1 = view(f, 1.0, 60)
        x0, x1 = max(vx0, c + 40.0), vx1
        if x1 <= x0:
            return
        xs, ys = RIDGE.surface(x0, x1, 6.0)
        ys = ys + sink
        shade = mix(mood.snow_dark, mood.ink, 0.2)
        with plane(f, 1.0) as cc:
            cc.move_to(xs[0], vy1 + 40)
            for x, y in zip(xs, ys):
                cc.line_to(x, y)
            cc.line_to(xs[-1], vy1 + 40)
            cc.close_path()
            draw.linear(cc, (c + 120.0, 0), (c + 520.0, 0), [(0, shade, 0.0), (0.6, shade, 0.55), (1, shade, 0.7)])
            cc.fill()
            # cornice: a lit lip curling over the edge, thinning out down the face
            xa, xb = c + 60.0, min(c + 360.0, x1)
            if xb > max(xa, x0):
                us = np.linspace(0.0, 1.0, 40)
                lx = xa + (xb - xa) * us
                ly = np.asarray(RIDGE.snow_y(lx), dtype=float) + sink
                th = 16.0 * np.sin(np.pi * np.clip(us * 1.15, 0, 1)) ** 0.7 + 2.0
                cc.move_to(lx[0], ly[0])
                for x, y in zip(lx, ly):
                    cc.line_to(x, y - 2.0)
                for x, y, h in zip(lx[::-1], ly[::-1], th[::-1]):
                    cc.line_to(x - 0.35 * h, y + h)
                cc.close_path()
                draw.fill(cc, mix(mood.snow, SNOW, 0.6), 0.95)

    def draw(self, f, mood=None, **kw):
        self.draw_back(f, mood)
        self.draw_plane(f, mood)
        self.draw_front(f, mood)

    def spindrift(self, f, mood=None, t=0.0, amount=1.0, wind=260.0):
        """Snow blown off the crest and the drift tops: soft streaming veils (low-res)."""
        mood = get_mood(mood)
        vx0, vy0, vx1, vy1 = view(f, 1.0, 600)
        cx = RIDGE.crest_x
        srcs = [cx - 120.0, cx + 80.0, cx - 900.0, cx - 1700.0]
        srcs = [x for x in srcs if vx0 < x < vx1 + 800]
        if not srcs:
            return
        col = mix(mood.snow, SNOW, 0.5)
        with soft_layer(f, 1.0, k=5, blur=16.0) as S:
            for j, sx in enumerate(srcs):
                gy = float(RIDGE.snow_y(sx))
                gust = 0.55 + 0.45 * fbm1(t * 0.4 + j * 3.7, 9)
                for i in range(16):
                    ph = (t * 0.55 + i / 16 + rnd(j, i, 1) * 0.05) % 1.0
                    x = sx + wind * ph * 2.2
                    y = gy - 20 - 160 * ph ** 0.7 + 30 * math.sin(i + t)
                    r = 30 + 120 * ph
                    draw.circle(S, (x, y), r)
                    draw.fill(S, col, 0.22 * amount * gust * math.sin(math.pi * ph))


# ============================================================================ S06: the valley view
def _path_curve(n=200):
    """The path from the crest (s = 0, bottom of frame) to the clearing (s = 1), in rest-screen
    coords, with the depth d(s) and size scale k(s) of each point."""
    s = np.linspace(0.0, 1.0, n)
    y = lerp(1990.0, 1046.0, 1.0 - (1.0 - s) ** 1.35)
    amp = lerp(300.0, 20.0, s ** 0.8)
    x = 548.0 + amp * np.sin(s * 9.5 + 0.6) * (1.0 - 0.15 * s)
    d = lerp(0.04, 0.44, s ** 0.9)
    k = lerp(0.8, 0.12, s ** 0.62)
    return s, x, y, d, k


class ValleyView:
    """S06: the valley seen from the crest. See the module docstring.

    Bands (rest-screen y of their ground, depth, parallax):
        sky                           backdrop (screen space)
        far ridges   y ~ 600..760     depth 0.9..0.68, par 0.12..0.28
        valley floor y ~ 880          depth 0.56, par 0.36
        CLEARING     y ~ 1040         depth 0.42, par 0.44: cottage, web, hood trees
        slope rows   y ~ 1180..1700   depth 0.32..0.1, par 0.55..0.9 (trees left and right of
                                      the path's corridor)
        crest        y > 1750         depth 0, par 1: the near snow, the cornice lip
    """

    GROUP_PAR = 0.44
    GROUP_D = 0.42
    GROUP_SCALE = 0.112
    GROUP_AT = (556.0, 1044.0)      # where the cottage door's footing lands (layer coords)

    CAMS = dict(
        start=(540.0, 1480.0, 1.25),     # looking down the near slope: the first stakes
        path=(548.0, 1220.0, 1.55),      # following the path down
        house=None,                      # computed: push in on the cottage (zoom 4.2)
        hoods=None,                      # computed: the hood trees around it (zoom 2.6)
        wide=(540.0, 960.0, 1.0),        # pull back: the whole valley, every hood
    )

    def __init__(self, clearing=CLEARING_SET, seed=31):
        self.C = clearing
        self.seed = seed
        self._built = False

    # ------------------------------------------------------------ coordinates
    def to_group(self, p):
        """Clearing-world point -> valley layer coords (layer par GROUP_PAR)."""
        gx, gy = self.GROUP_AT
        k = self.GROUP_SCALE
        y0 = self.C.cottage.threshold[1]
        return (gx + (p[0] - self.C.cottage.door_x) * k, gy + (p[1] - y0) * k)

    def cottage_point(self):
        """(layer point, par) of the cottage's center."""
        cot = self.C.cottage
        return self.to_group(((cot.x0 + cot.x1) / 2, cot.threshold[1] - 700.0)), self.GROUP_PAR

    @staticmethod
    def camera_on(point, par, zoom):
        """Camera that puts `point` of a layer with parallax `par` at the frame center."""
        return Camera(x=540.0 + (point[0] - 540.0) / par, y=960.0 + (point[1] - 960.0) / par, zoom=zoom)

    def camera(self, name):
        """Preset cameras for S06: start, path, house, hoods, wide. Blend with cam_lerp."""
        if name == "house":
            p, par = self.cottage_point()
            return self.camera_on(p, par, 4.2)
        if name == "hoods":
            p, par = self.cottage_point()
            return self.camera_on((p[0] + 10.0, p[1] - 20.0), par, 2.6)
        x, y, z = self.CAMS[name]
        return Camera(x=x, y=y, zoom=z)

    @staticmethod
    def cam_lerp(a, b, u):
        """Eased blend of two cameras (zoom interpolated geometrically)."""
        u = clamp(u)
        u = u * u * (3 - 2 * u)
        return Camera(x=lerp(a.x, b.x, u), y=lerp(a.y, b.y, u), zoom=a.zoom * (b.zoom / a.zoom) ** u)

    # ------------------------------------------------------------ build
    def _build(self):
        if self._built:
            return
        C = self.C
        C._ensure()
        sd = self.seed
        # far bands: ridge lines with a fringe of tiny trees (clumped: groves and open snow)
        self.bands = []
        for i, (y, d, par, amp, tree_h, step) in enumerate(((515.0, 0.91, 0.07, 85.0, 15.0, 8.0),
                                                            (610.0, 0.84, 0.12, 60.0, 22.0, 9.0),
                                                            (690.0, 0.74, 0.2, 70.0, 34.0, 15.0),
                                                            (775.0, 0.62, 0.28, 55.0, 52.0, 21.0),
                                                            (880.0, 0.52, 0.36, 26.0, 80.0, 27.0))):
            xs = np.linspace(-1600.0, 2700.0, 240)
            ys = y + amp * np.array([fbm1(x / 520.0 + i * 7.1, sd + i) for x in xs]) - 0.18 * amp * np.cos((xs - 540) / 900)
            ticks = []
            for k in range(int(4300 / step)):
                x = -1600.0 + (k + rnd(sd, i, k)) * step
                dens = smoothstep(-0.3, 0.35, fbm1(x / 330.0 + i * 3.3, sd + 40 + i))
                if rnd(sd, i, k, 4) > 0.18 + 0.72 * dens:
                    continue
                gy = float(np.interp(x, xs, ys))
                h = tree_h * (0.45 + 0.45 * dens + 0.5 * rnd(sd, i, k, 2))
                w = 0.6 + 0.4 * i + 0.8 * rnd(sd, i, k, 3)
                ticks += _band_tree(x, gy, h, w, sd * 131 + i * 7919 + k)
            self.bands.append(dict(xs=xs, ys=ys, d=d, par=par, ticks=ticks))
        # the path
        self.path = _path_curve()
        # slope rows: trees beside the path's corridor
        self.rows = []
        s, px, py, pd, pk = self.path
        for j, (y, d, par, w) in enumerate(((1170.0, 0.33, 0.55, 9.0), (1320.0, 0.24, 0.66, 15.0), (1520.0, 0.15, 0.8, 24.0),
                                            (1780.0, 0.07, 0.94, 40.0))):
            cx = float(np.interp(y, py[::-1], px[::-1]))
            corridor = lerp(150.0, 520.0, (y - 1100.0) / 700.0)
            trees = []
            x = -1500.0 + 40 * rnd(sd, j, 0)
            k = 0
            Hs = (190.0, 300.0, 480.0, 760.0)[j]
            while x < 2600.0:
                k += 1
                ww = w * (0.7 + 0.6 * rnd(sd, j, k, 1))
                gy = y + 30 * fbm1(x / 400.0, sd + j)
                if abs(x - cx) > corridor + Hs * 0.3 and rnd(sd, j, k, 2) < 0.85:
                    if rnd(sd, j, k, 4) < 0.8:
                        trees.append(dict(kind="spruce", tiers=_make_spruce(x, gy, Hs * (0.6 + 0.8 * rnd(sd, j, k, 5)),
                                                                            sd * 97 + j * 1000 + k)))
                    else:
                        h = Hs * (0.9 + 0.7 * rnd(sd, j, k, 6))
                        tw = ww * 0.9
                        trees.append(dict(kind="snag", ink=[_orient([(x - tw, gy + 8), (x - tw * 0.7, gy - h * 0.8),
                                                                      (x - tw * 0.2, gy - h), (x + tw * 0.1, gy - h * 0.9),
                                                                      (x + tw * 0.7, gy - h * 0.75), (x + tw, gy + 8)])]))
                x += Hs * (0.16 + 0.3 * rnd(sd, j, k, 3)) + ww
            xs = np.linspace(-1600.0, 2700.0, 120)
            ys = y + 30 * np.array([fbm1(x / 400.0, sd + j) for x in xs])
            self.rows.append(dict(y=y, d=d, par=par, trees=trees, xs=xs, ys=ys))
        # the stakes along the path (alternating sides), each with its depth
        self.stakes = []
        n = 34
        for i in range(n):
            u = (i + 0.5) / n
            si = int(u * (len(s) - 1))
            side = -1 if i % 2 else 1
            k_ = pk[si]
            x = px[si] + side * 38.0 * k_
            y = py[si]
            self.stakes.append(dict(x=x, y=y, k=k_, d=pd[si], par=lerp(1.0, self.GROUP_PAR, u ** 0.9), u=u, seed=i))
        # hood trees around the clearing (clearing-world coords): two rows
        self.group_trees = []
        T = C.T
        self.hoods = Hoods()
        for row, (x0, x1, step, dsc, dd) in enumerate(((-7800.0, 9000.0, 560.0, 0.92, 0.06), (-6200.0, 8200.0, 780.0, 1.08, -0.05))):
            x = x0
            k = 0
            while x < x1:
                k += 1
                xx = x + 200 * srnd(sd, row, k)
                x += step * (0.7 + 0.6 * rnd(sd, row, k, 1))
                if -1300 < xx < 2400 and row == 1:
                    continue                      # keep the front row off the cottage
                if -900 < xx < 1700:
                    continue
                w = 90 + 50 * rnd(sd, row, k, 2)
                tr = _crown_tree(xx, T.ground_y, w, sd * 7 + row * 300 + k, crown=(1000.0, 1700.0), reach=900.0,
                                 n_limbs=6, levels=1, snow=False, height=2300.0 + 1500.0 * rnd(sd, row, k, 5))
                tr["row"] = row
                tr["dsc"], tr["dd"] = dsc, dd
                self.group_trees.append(tr)
                chosen = []
                for j, (hx, hy, ang) in enumerate(tr["hang"]):
                    gy = float(T.ground_y(xx))
                    if len(chosen) >= 9 or not (gy - 1900 < hy < gy - 900):
                        continue
                    if rnd(sd, row, k, j) < 0.55 and all(math.hypot(hx - q[0], hy - q[1]) > 160 for q in chosen):
                        chosen.append((hx, hy))
                        self.hoods.add(("row", row), (hx, hy), 30 + 60 * rnd(sd, k, j, 3), 105.0, row * 10000 + k * 50 + j,
                                       T.snow_y, amp=6.0)
        # the clearing's own canopy trees, as whole trees seen from afar
        from .sets_cottage import PLANE_TREES
        self.near_trees = []
        for i, (x, w, c0, c1, reach, nl) in enumerate(PLANE_TREES):
            self.near_trees.append(_crown_tree(x, T.ground_y, w, C.seed * 101 + i * 7, crown=(c0, c1), reach=reach,
                                               n_limbs=nl, height=c1 + 900.0 + 600.0 * rnd(sd, i, 9)))
        for h in C.hoods.groups.get("plane", []) + C.hoods.groups.get("web", []):
            self.hoods.add(("row", 0), h["anchor"], h["thread"], h["size"], h["seed"] + 77, T.snow_y, amp=h["amp"])
        self._built = True

    # ------------------------------------------------------------ draw
    def draw(self, f, mood=None, t=None, hoods=1.0, web_light=1.0, mist=True):
        """The whole view. hoods: fraction of hoods shown (0..1, nearest the cottage first:
        the reveal on [hoods]); web_light: how much the silk catches the light."""
        mood = get_mood(mood or DAY)
        t = f.t if t is None else t
        self._build()
        backdrop(f, mood, glow=(540.0, 760.0), glow_r=1300.0, glow_a=0.5 if mood.night < 0.5 else 0.15)
        for b in self.bands:
            self._draw_band(f, b, mood)
            if mist:
                _flat_mist(f, b["par"], float(np.median(b["ys"])) + 20.0, mood.mist, 0.55, up=120.0, down=60.0)
        self._draw_group(f, mood, t, hoods, web_light)
        if mist:
            _flat_mist(f, self.GROUP_PAR, self.GROUP_AT[1] + 40.0, mood.mist, 0.5, up=90.0, down=120.0)
        for j, r in enumerate(self.rows):
            self._draw_stakes(f, mood, t, lo=self._row_u(j), hi=self._row_u(j - 1) if j else 1.01)
            self._draw_row(f, r, mood)
            if mist and j < 3:
                _flat_mist(f, r["par"], float(np.median(r["ys"])) + 10.0, mood.mist, 0.42, up=160.0, down=90.0)
        self._draw_stakes(f, mood, t, lo=-0.01, hi=self._row_u(len(self.rows) - 1))
        self._draw_crest(f, mood)

    def _row_u(self, j):
        """Path parameter where row j's ground is (stakes beyond it are drawn before it)."""
        if j < 0:
            return 1.01
        s, px, py, pd, pk = self.path
        return float(np.interp(self.rows[j]["y"], py[::-1], s[::-1]))

    def _draw_band(self, f, b, mood):
        col = fogged(mood, b["d"])
        snow_c = fogged(mood, b["d"] * 0.85, mood.snow)
        vx0, vy0, vx1, vy1 = view(f, b["par"], 100)
        with plane(f, b["par"]) as c:
            xs, ys = b["xs"], b["ys"]
            c.move_to(xs[0], vy1 + 2000)
            for x, y in zip(xs, ys):
                c.line_to(x, y)
            c.line_to(xs[-1], vy1 + 2000)
            c.close_path()
            hill = mix(snow_c, col, 0.42)
            draw.linear(c, (0, float(ys.min())), (0, float(ys.min()) + 240), [(0, hill, 1), (1, mix(snow_c, col, 0.12), 1)])
            c.fill()
            _fill(c, b["ticks"], col)

    def _draw_group(self, f, mood, t, hoods, web_light):
        """The clearing in miniature: back hood trees, the plane trees, the cottage and web,
        the ground, front hood trees, hoods."""
        C = self.C
        par, d, k = self.GROUP_PAR, self.GROUP_D, self.GROUP_SCALE
        gx, gy = self.GROUP_AT
        y0 = C.cottage.threshold[1]
        T = C.T
        vx0, vy0, vx1, vy1 = view(f, par, 100)
        # visible clearing-world x range
        wx0 = C.cottage.door_x + (vx0 - gx) / k
        wx1 = C.cottage.door_x + (vx1 - gx) / k
        with plane(f, par) as c:
            c.translate(gx, gy)
            c.scale(k, k)
            c.translate(-C.cottage.door_x, -y0)
            for row in (0,):
                trs = [tr for tr in self.group_trees if tr["row"] == row and wx0 - 1500 < tr["x"] < wx1 + 1500]
                ink = fogged(mood, d + 0.08)
                _fill(c, [tr["body"] for tr in trs], ink)
                _fill(c, [p for tr in trs for p in tr["limbs"]], ink)
            trs = [tr for tr in self.near_trees if wx0 - 1500 < tr["x"] < wx1 + 1500]
            ink = fogged(mood, d)
            _fill(c, [tr["body"] for tr in trs], ink)
            _fill(c, [p for tr in trs for p in tr["limbs"]], ink)
            _fill(c, [p for tr in trs for p in tr["snow"]], fogged(mood, d * 0.8, mood.snow))
            C.cottage.draw(f, c, mood, "old", t, tint=d * 0.85, detail=False)
            # the ground of the clearing: a snow band fading into the mist below
            xs = np.linspace(wx0 - 400, wx1 + 400, 60)
            ys = np.asarray(T.snow_y(xs), dtype=float)
            c.move_to(xs[0], ys[0])
            for x, y in zip(xs, ys):
                c.line_to(x, y)
            c.line_to(xs[-1], ys[-1] + 1800)
            c.line_to(xs[0], ys[0] + 1800)
            c.close_path()
            sc = fogged(mood, d * 0.7, mood.snow)
            draw.linear(c, (0, y0 - 40), (0, y0 + 1800), [(0, sc, 1), (0.6, sc, 1), (1, sc, 0)])
            c.fill()
            C.cottage.draw_ground_snow(c, mood if d <= 0 else _tinted(mood, d * 0.7), "old")
            # the web: white strands catching the light, dead still
            light = [(C.cottage.door_x + 500, y0 - 1600, 5200.0, 0.55 * web_light)] if web_light > 0 else []
            C.web.draw(f, t, mood, ctx=c, par=par, scale=k, tint=0.0, lights=light, min_px=0.75,
                       alpha=0.95, glints=SNOW)
            trs = [tr for tr in self.group_trees if tr["row"] == 1 and wx0 - 1500 < tr["x"] < wx1 + 1500]
            ink = fogged(mood, d - 0.05)
            _fill(c, [tr["body"] for tr in trs], ink)
            _fill(c, [p for tr in trs for p in tr["limbs"]], ink)
            if hoods > 0:
                items = [h for h in self.hoods.items if wx0 - 300 < h["anchor"][0] < wx1 + 300]
                if hoods < 1:
                    cx = C.cottage.door_x + 400
                    items.sort(key=lambda h: abs(h["anchor"][0] - cx) + 0.5 * abs(h["anchor"][1] - y0 + 1300))
                    items = items[:int(round(len(self.hoods.items) * hoods))]
                red = mix(HOOD_RED, mood.fog_at(d), d * 0.35)
                self.hoods.draw(c, t, items, mood, color=red, ink=fogged(mood, d), threads=True)

    def _crown_fog(self, f, mood):
        """The tall trunks around the clearing vanish upward into the fog."""
        gx, gy = self.GROUP_AT
        with plane(f, self.GROUP_PAR) as c:
            vx0, vy0, vx1, vy1 = view(f, self.GROUP_PAR, 50)
            top = gy - 640.0
            fog = mood.fog_at(0.9)
            draw.linear(c, (0, gy - 230.0), (0, top), [(0, fog, 0.0), (0.55, fog, 0.55), (1, fog, 0.95)])
            c.rectangle(vx0, min(vy0, top) - 2000, vx1 - vx0, gy - 230.0 - (min(vy0, top) - 2000))
            c.fill()

    def _draw_row(self, f, r, mood):
        """A row of young spruces and snags on the slope; its snow covers what lies below."""
        col = fogged(mood, r["d"])
        snow_c = fogged(mood, r["d"] * 0.8, mood.snow)
        with plane(f, r["par"]) as c:
            for tr in r["trees"]:
                if tr["kind"] == "snag":
                    _fill(c, tr["ink"], col)
            for tier in range(12):
                inks, snows = [], []
                for tr in r["trees"]:
                    if tr["kind"] == "spruce" and tier < len(tr["tiers"]):
                        inks += tr["tiers"][tier][0]
                        snows += tr["tiers"][tier][1]
                _fill(c, inks, col)
                _fill(c, snows, snow_c)
            xs, ys = r["xs"], r["ys"]
            c.move_to(xs[0], ys[0] + 6)
            for x, y in zip(xs, ys):
                c.line_to(x, y + 6)
            vx0, vy0, vx1, vy1 = view(f, r["par"], 100)
            c.line_to(xs[-1], vy1 + 2400)
            c.line_to(xs[0], vy1 + 2400)
            c.close_path()
            draw.linear(c, (0, r["y"]), (0, r["y"] + 420), [(0, snow_c, 1.0), (1, mix(snow_c, mood.snow_dark, 0.3), 1.0)])
            c.fill()

    def _draw_stakes(self, f, mood, t, lo, hi):
        """The path between lo <= u < hi: a trodden groove and the stakes with their rope."""
        s, px, py, pd, pk = self.path
        sel = (s >= lo) & (s < hi)
        if sel.sum() >= 2:
            idx = np.where(sel)[0]
            # groove (drawn at the parallax of its middle)
            um = float(s[idx].mean())
            par = lerp(1.0, self.GROUP_PAR, um ** 0.9)
            with plane(f, par) as c:
                for i in idx[:-1]:
                    c.move_to(px[i], py[i])
                    c.line_to(px[i + 1], py[i + 1])
                    draw.stroke(c, mix(mood.snow_dark, mood.ink, 0.12), max(1.2, 30.0 * pk[i]), a=0.45)
        st = [p for p in self.stakes if lo <= p["u"] < hi]
        for side in (0, 1):
            run = [p for p in st if p["seed"] % 2 == side]
            for a, b in zip(run[:-1], run[1:]):
                with plane(f, 0.5 * (a["par"] + b["par"])) as c:
                    ha, hb = 70.0 * a["k"], 70.0 * b["k"]
                    pa, pb = (a["x"], a["y"] - ha), (b["x"], b["y"] - hb)
                    mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2 + 10 * a["k"])
                    c.move_to(*pa)
                    c.curve_to(mid[0], mid[1], mid[0], mid[1], *pb)
                    draw.stroke(c, fogged(mood, a["d"]), max(0.8, 2.4 * a["k"]), a=0.8)
        for p in st:
            with plane(f, p["par"]) as c:
                k = p["k"]
                h, w = 95.0 * k, 15.0 * k
                ink = fogged(mood, p["d"])
                ink_p, cap, mound = stake_shape((p["x"], p["y"] + 4 * k), h=h, w=max(w, 1.4),
                                                tilt=6.0 * srnd(self.seed, p["seed"]), seed=p["seed"], snow=7.0 * k)
                _fill(c, [ink_p], ink)
                if cap:
                    _fill(c, [cap], fogged(mood, p["d"], mood.snow))

    def crest_y(self, x):
        """y (layer par 1, rest-screen coords) of the crest's snow surface at x: where she
        stands, back to camera, for the S05 OUT / S06 IN framing (camera "start" puts
        crest_y(540) at screen y ~ 1360)."""
        return 1800.0 + 40 * fbm1(x / 300.0, self.seed + 5) + 0.00012 * (x - 540) ** 2

    def _draw_crest(self, f, mood):
        """The near snow at the bottom: the crest she stands on (a lit cornice edge with the
        drop's shadow beyond it)."""
        with plane(f, 1.0) as c:
            xs = np.linspace(-900.0, 1980.0, 80)
            ys = np.array([self.crest_y(x) for x in xs])
            # the drop beyond the edge, in shadow
            sh = mix(mood.snow_dark, mood.ink, 0.12)
            c.move_to(xs[0], ys[0] - 90.0)
            for x, y in zip(xs, ys):
                c.line_to(x, y - 90.0)
            for x, y in zip(xs[::-1], ys[::-1]):
                c.line_to(x, y + 2.0)
            c.close_path()
            y_m = float(ys.min())
            draw.linear(c, (0, y_m - 90.0), (0, y_m + 2.0), [(0, sh, 0.0), (1, sh, 0.42)])
            c.fill()
            # the crest
            c.move_to(xs[0], 4000)
            for x, y in zip(xs, ys):
                c.line_to(x, y)
            c.line_to(xs[-1], 4000)
            c.close_path()
            lit = mix(mood.snow, SNOW, 0.5)
            draw.linear(c, (0, y_m), (0, y_m + 520), [(0, lit, 1), (0.05, mood.snow, 1), (1, mood.snow_dark, 1)])
            c.fill()

    # ------------------------------------------------------------ queries
    def hood_screen_positions(self, f, t=None, hoods=1.0):
        """[(x, y, size)] in screen px (frame coords, 1080x1920) of the hood centers: to
        flatten them into the Bass grid of S06."""
        self._build()
        t = f.t if t is None else t
        cam = f.lcam(self.GROUP_PAR)
        out = []
        for h in self.hoods.items:
            x, y, a, cr = self.hoods.pose(h, t, None)
            lp = self.to_group((x, y + h["size"] * 0.4))
            sx, sy = cam.to_screen(lp)
            out.append((sx, sy, h["size"] * self.GROUP_SCALE * cam.zoom))
        return out


def _flat_mist(f, par, y, color, alpha, up, down):
    """Valley fog lying level at y on plane `par` (densest at y): a cheap linear gradient."""
    vx0, vy0, vx1, vy1 = view(f, par, 50)
    with plane(f, par) as c:
        draw.linear(c, (0, y - up), (0, y + down), [(0, color, 0.0), (up / (up + down), color, alpha), (1, color, 0.0)])
        c.rectangle(vx0, y - up, vx1 - vx0, up + down)
        c.fill()


def _band_tree(x, gy, h, w, seed):
    """A tiny far tree for the valley bands: a ragged spire (spruce) or a bare forked trunk.
    Oriented polygons, layer coords."""
    if rnd(seed, 1) < 0.64:
        W = h * (0.1 + 0.07 * rnd(seed, 2))
        n = 5 + int(2 * rnd(seed, 8))
        left = [(x - w * 0.6, gy + 6.0)]
        for k in range(n):
            u = k / n
            ty = gy - h * (0.1 + 0.84 * u)
            tw = W * (1 - u) ** 0.8 * (0.75 + 0.5 * rnd(seed, k, 9)) + w * 0.5
            left.append((x - tw, ty + h * 0.03))
            left.append((x - tw * 0.45 - w * 0.25, ty - h * 0.84 / n * 0.5))
        left.append((x, gy - h))
        right = []
        for k, (px, py) in enumerate(left[::-1][1:]):
            j = 1.0 + 0.2 * srnd(seed, k, 3)
            right.append((x + (x - px) * j, py))
        return [_orient(left + right)]
    hh = h * (0.8 + 0.3 * rnd(seed, 3))
    polys = [_orient([(x - w, gy + 6.0), (x - w * 0.3, gy - hh), (x + w * 0.3, gy - hh), (x + w, gy + 6.0)])]
    for side in (-1, 1):
        if rnd(seed, side, 7) < 0.85:
            y0 = gy - hh * (0.42 + 0.22 * rnd(seed, side, 4))
            tip = (x + side * hh * (0.14 + 0.12 * rnd(seed, side, 5)), y0 - hh * (0.3 + 0.18 * rnd(seed, side, 6)))
            polys.append(_orient([(x - w * 0.35, y0 + w * 1.5), (x + w * 0.35, y0 - w * 0.5), tip]))
    return polys


def _tinted(mood, d):
    return tinted(mood, d)


RIDGE_SET = Ridge()
VALLEY_VIEW = ValleyView()
