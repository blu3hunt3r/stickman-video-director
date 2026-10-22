"""RED sets: the village (S02 at night, S10 in the morning).

It shares the PATH coordinate system: the street is x < 0 (ground PATH.ground_y ~ 1500),
the village gate stands at x = 0 and the trail leaves through it (sets_forest takes over).

    V = VILLAGE
    V.draw_back(f, NIGHT)       # sky, far hill + church, mid and near rows of houses, smoke
    V.draw_plane(f, NIGHT)      # street snow, the mother's house + doorway, well, fence, gate, lanterns
    ...characters (feet on PATH.ground_y)...
    V.draw_front(f, NIGHT)      # snow lip, blurred foreground fence posts

Anchors (world, action plane): V.threshold (mother's door step), V.door_x, V.well_x,
V.gate_x, V.lanterns (flame positions), MARKS. Real scale: a house is ~1300-1900 px wide and
~1600 px to the ridge, so village shots are typically framed at zoom 0.45-0.7.
"""
import math

import numpy as np

from engine import draw
from engine.core import clamp, lerp, fbm1, smoothstep
from .sets_common import (get_mood, mix, NIGHT, INK, SNOW, view, plane, depth_layer, backdrop, rnd, srnd,
                          soft_layer, glow, light_pool, fogged, flick, mist_band, ground_mist, tinted)
from .sets_terrain import PATH, plane_ground, _plane_ground, PATH_MARKS
from .sets_props import Lantern, Doorway, swing_angle
from .sets_forest import _orient, _fill, _taper_limb, _curve, _make_spruce, _make_tree

MARKS = dict(street=(-4200.0, 300.0), mother_door=PATH_MARKS["mother_door"], well=-760.0, gate=0.0,
             lanterns=(-2650.0, -1080.0, -330.0))


DOOR_SIZE = 1.45          # door scale of a real-size house (the mother's door); rows use DOOR_SIZE * sc


class _LayerGround:
    """Adapter: a layer's ground function as a terrain (for props that ask terrain.ground_y)."""

    def __init__(self, g):
        self.ground_y = g
        self.snow_y = g


# ----------------------------------------------------------------------------- house builder
def _house(x, G, w, wall_h, pitch, seed, sc=1.0, windows=2, lit=0.6, chimney=True, horns=True,
           door=None, icicles=True):
    """A timber house centered at x on ground function G. Returns dict with ink / snow
    polygons, windows [(poly, lit, center)], mullions (ink polys over windows), sills,
    chimney top point and the roof outline. All in the layer's coords."""
    x0, x1 = x - w / 2, x + w / 2
    gy = float(G(x))
    gb = max(float(G(x0)), float(G(x1)), gy) + 60
    eave = gy - wall_h
    ov = 70 * sc
    t = math.tan(math.radians(pitch))
    ridge_y = eave - (w / 2 + ov) * t
    ink, snow, wins, mull, sills = [], [], [], [], []
    # walls with log ends protruding at both corners (outline detail of a log house)
    wall = [(x0, gb)]
    nlog = max(3, int(wall_h / (88 * sc)))
    step = wall_h / nlog
    for i in range(nlog):
        y = gy - i * step
        wall += [(x0, y - step * 0.15), (x0 - 18 * sc, y - step * 0.2), (x0 - 18 * sc, y - step * 0.78), (x0, y - step * 0.85)]
    wall += [(x0, eave), (x1, eave)]
    for i in range(nlog - 1, -1, -1):
        y = gy - i * step
        wall += [(x1, y - step * 0.85), (x1 + 18 * sc, y - step * 0.78), (x1 + 18 * sc, y - step * 0.2), (x1, y - step * 0.15)]
    wall += [(x1, gb)]
    ink.append(_orient(wall))
    # roof (with a little sag), eaves overhang
    ex0, ex1 = x0 - ov, x1 + ov
    roof = [(ex0, eave + 16 * sc), (ex0 - 6 * sc, eave + 4 * sc), (x, ridge_y), (ex1 + 6 * sc, eave + 4 * sc),
            (ex1, eave + 16 * sc)]
    ink.append(_orient(roof))
    if horns:     # crossed gable boards above the ridge
        hl = 70 * sc
        a = math.radians(pitch)
        ink.append(_taper_limb([(x - math.cos(a) * 30 * sc, ridge_y + math.sin(a) * 30 * sc),
                                (x + math.cos(a) * hl, ridge_y - math.sin(a) * hl)], 7 * sc, 5 * sc))
        ink.append(_taper_limb([(x + math.cos(a) * 30 * sc, ridge_y + math.sin(a) * 30 * sc),
                                (x - math.cos(a) * hl, ridge_y - math.sin(a) * hl)], 7 * sc, 5 * sc))
    # chimney on one slope
    ch = None
    if chimney:
        side = -1 if rnd(seed, 3) < 0.5 else 1
        cx = x + side * w * (0.18 + 0.12 * rnd(seed, 4))
        roof_y = ridge_y + abs(cx - x) * t
        cw = 70 * sc
        top = roof_y - (110 + 90 * rnd(seed, 5)) * sc
        ink.append(_orient([(cx - cw / 2, roof_y + 40 * sc), (cx - cw / 2, top), (cx - cw / 2 - 8 * sc, top),
                            (cx - cw / 2 - 8 * sc, top - 16 * sc), (cx + cw / 2 + 8 * sc, top - 16 * sc),
                            (cx + cw / 2 + 8 * sc, top), (cx + cw / 2, top), (cx + cw / 2, roof_y + 40 * sc)]))
        snow.append(_orient([(cx - cw / 2 - 12 * sc, top - 14 * sc), (cx - cw * 0.2, top - 30 * sc),
                             (cx + cw * 0.3, top - 28 * sc), (cx + cw / 2 + 12 * sc, top - 14 * sc),
                             (cx + cw / 2 + 8 * sc, top - 12 * sc), (cx - cw / 2 - 8 * sc, top - 12 * sc)]))
        ch = (cx, top - 20 * sc)
    # the snow cap: thick on both slopes, curling over the eaves
    th = (62 + 40 * rnd(seed, 6)) * sc
    capL, capR = [], []
    n = 9
    for i in range(n + 1):
        u = i / n
        px = lerp(ex0 - 10 * sc, x, u)
        py = lerp(eave + 4 * sc, ridge_y, u)
        lump = th * (0.75 + 0.5 * rnd(seed, 10 + i))
        capL.append((px - 2 * sc, py - lump * (0.5 + 0.5 * math.sin(math.pi * clamp(u * 1.4)))))
    for i in range(n + 1):
        u = i / n
        px = lerp(x, ex1 + 10 * sc, u)
        py = lerp(ridge_y, eave + 4 * sc, u)
        lump = th * (0.75 + 0.5 * rnd(seed, 30 + i))
        capR.append((px + 2 * sc, py - lump * (0.5 + 0.5 * math.sin(math.pi * clamp((1 - u) * 1.4)))))
    under = [(ex1 + 14 * sc, eave + 14 * sc), (ex1 + 4 * sc, eave + 2 * sc), (x, ridge_y + 6 * sc),
             (ex0 - 4 * sc, eave + 2 * sc), (ex0 - 14 * sc, eave + 14 * sc)]
    snow.append(_orient([(ex0 - 16 * sc, eave + 16 * sc)] + capL + capR[1:] + under))
    if icicles:
        for side in (-1, 1):
            exx = ex0 if side < 0 else ex1
            for k in range(int(3 + 4 * rnd(seed, 50 + side))):
                ix = exx - side * (10 + 140 * rnd(seed, 60 + k + side * 7)) * sc
                iy = eave + (14 - side * 0) * sc + (abs(ix - exx)) * 0.0
                L = (18 + 46 * rnd(seed, 70 + k + side * 7)) * sc
                snow.append(_orient([(ix - 4 * sc, iy), (ix + 4 * sc, iy), (ix, iy + L)]))
    # windows (small, mullioned) at ~45% of the wall height
    for i in range(windows):
        u = (i + 1) / (windows + 1)
        wx = lerp(x0, x1, u) + srnd(seed, 80 + i) * w * 0.05
        if door is not None and abs(wx - door) < 220 * sc:
            continue
        ww, wh = (150 + 30 * rnd(seed, 90 + i)) * sc, (180 + 30 * rnd(seed, 95 + i)) * sc
        wy = gy - wall_h * 0.42
        poly = [(wx - ww / 2, wy - wh / 2), (wx + ww / 2, wy - wh / 2), (wx + ww / 2, wy + wh / 2), (wx - ww / 2, wy + wh / 2)]
        is_lit = rnd(seed, 100 + i) < lit
        wins.append((poly, is_lit, (wx, wy), (ww, wh)))
        b = 9 * sc
        mull.append([(wx - b / 2, wy - wh / 2), (wx + b / 2, wy - wh / 2), (wx + b / 2, wy + wh / 2), (wx - b / 2, wy + wh / 2)])
        mull.append([(wx - ww / 2, wy - b / 2), (wx + ww / 2, wy - b / 2), (wx + ww / 2, wy + b / 2), (wx - ww / 2, wy + b / 2)])
        # shutters as outline detail (stick out of the wall silhouette? no: on the wall) -> sill + snow
        sills.append(_orient([(wx - ww / 2 - 16 * sc, wy + wh / 2), (wx + ww / 2 + 16 * sc, wy + wh / 2),
                              (wx + ww / 2 + 14 * sc, wy + wh / 2 - 14 * sc), (wx, wy + wh / 2 - 20 * sc),
                              (wx - ww / 2 - 14 * sc, wy + wh / 2 - 14 * sc)]))
    # snow drifted against the walls
    for side in (-1, 1):
        bx = x0 if side < 0 else x1
        dw = (120 + 120 * rnd(seed, 120 + side)) * sc
        dh = (40 + 50 * rnd(seed, 130 + side)) * sc
        pts = []
        for i in range(9):
            u = i / 8
            xx = bx - side * 30 * sc + side * dw * u
            pts.append((xx, float(G(xx)) - dh * (1 - u) ** 1.6))
        pts += [(bx + side * dw, float(G(bx + side * dw)) + 20), (bx - side * 30 * sc, float(G(bx)) + 20)]
        snow.append(_orient(pts))
    return dict(ink=ink, snow=snow, windows=wins, mullions=mull, sills=sills, chimney=ch, x=x, w=w,
                eave=eave, ridge=ridge_y, gy=gy)


def _church(x, G, sc, seed):
    """Wooden church: steep nave roof and a bell tower with a tall spire."""
    h = _house(x, G, 900 * sc, 620 * sc, 58, seed, sc=sc, windows=2, lit=0.8, chimney=False, horns=False)
    gy = float(G(x))
    tx = x - 520 * sc
    tw = 260 * sc
    top = gy - 1500 * sc
    tower = [(tx - tw / 2, gy + 40), (tx - tw / 2, top), (tx - tw * 0.62, top), (tx - tw * 0.62, top - 40 * sc),
             (tx - tw * 0.25, top - 80 * sc), (tx, top - 900 * sc), (tx + tw * 0.25, top - 80 * sc),
             (tx + tw * 0.62, top - 40 * sc), (tx + tw * 0.62, top), (tx + tw / 2, top), (tx + tw / 2, gy + 40)]
    h["ink"].append(_orient(tower))
    h["ink"].append(_orient([(tx - 6 * sc, top - 880 * sc), (tx + 6 * sc, top - 880 * sc), (tx + 6 * sc, top - 1010 * sc),
                             (tx - 6 * sc, top - 1010 * sc)]))
    h["ink"].append(_orient([(tx - 40 * sc, top - 960 * sc), (tx + 40 * sc, top - 960 * sc), (tx + 40 * sc, top - 948 * sc),
                             (tx - 40 * sc, top - 948 * sc)]))
    # belfry opening: a lit slit
    h["windows"].append(([(tx - 40 * sc, top + 60 * sc), (tx + 40 * sc, top + 60 * sc), (tx + 40 * sc, top + 200 * sc),
                          (tx - 40 * sc, top + 200 * sc)], rnd(seed, 7) < 0.5, (tx, top + 130 * sc), (80 * sc, 140 * sc)))
    h["snow"].append(_orient([(tx - tw * 0.66, top - 36 * sc), (tx - tw * 0.3, top - 90 * sc), (tx - tw * 0.1, top - 300 * sc),
                              (tx - tw * 0.05, top - 280 * sc), (tx - tw * 0.2, top - 80 * sc), (tx - tw * 0.6, top - 30 * sc)]))
    return h


def _bare_tree(x, G, h, seed):
    """A bare orchard tree: short trunk forking into a rounded crown of limbs and twigs,
    snow on the larger limbs. Returns dict(x, limbs, snow)."""
    from .sets_forest import _snow_on_limb, _resample_line
    gy = float(G(x))
    tw = h * 0.055
    limbs, snow = [], []
    fork = h * (0.32 + 0.1 * rnd(seed, 1))
    limbs.append(_taper_limb([(x, gy + 30), (x + srnd(seed, 2) * tw, gy - fork * 0.5), (x, gy - fork)], tw * 0.75, tw * 0.5))
    nb = 4 + int(3 * rnd(seed, 3))
    for b in range(nb):
        ang = -60 + 120 * (b + 0.5) / nb + srnd(seed, 10 + b) * 12
        L = h * (0.45 + 0.25 * rnd(seed, 20 + b)) * (1 - 0.35 * abs(ang) / 60)
        pts = _curve((x, gy - fork), ang, L, -ang * 0.35, n=6)
        r0 = tw * (0.42 + 0.15 * rnd(seed, 30 + b))
        limbs.append(_taper_limb(pts, r0, 1.0))
        dp = _resample_line(pts, 12)
        sn = _snow_on_limb(dp, [lerp(r0, 1.0, i / 11) for i in range(12)], r0 * 0.5, seed + b, u0=0.05, u1=0.7)
        if sn:
            snow.append(sn)
        for k in range(3):
            q = pts[2 + k]
            ta = ang + (35 if k % 2 else -35) + srnd(seed, 40 + b * 5 + k) * 15
            limbs.append(_taper_limb(_curve(q, ta, L * (0.3 + 0.2 * rnd(seed, 50 + b * 5 + k)), -ta * 0.3, n=4),
                                     max(1.0, r0 * 0.45), 0.6))
    return dict(x=x, limbs=limbs, snow=snow)


# ----------------------------------------------------------------------------- village
class Village:
    """The village street at night (or day). See module doc for the draw order."""

    # rows of houses terraced up the hillside behind the street (each row's roofs rise above
    # the row in front); the far row tops the hill with the church
    LAYERS = [
        dict(name="far", par=0.30, depth=0.70, blur=3.5, off=-700.0, sc=0.18, gap=(220.0, 520.0), lit=0.55),
        dict(name="mid", par=0.55, depth=0.46, blur=2.2, off=-560.0, sc=0.30, gap=(170.0, 460.0), lit=0.55),
        dict(name="near", par=0.80, depth=0.22, blur=0.0, off=-250.0, sc=0.45, gap=(220.0, 620.0), lit=0.6, direct=True),
    ]

    def __init__(self, terrain=PATH, seed=21, x_range=MARKS["street"]):
        self.T = terrain
        self.seed = seed
        self.x_range = x_range
        self.door_x = MARKS["mother_door"]
        self.well_x = MARKS["well"]
        self.gate_x = MARKS["gate"]
        self.lantern_x = MARKS["lanterns"]
        self.layers = [dict(L) for L in self.LAYERS]
        for L in self.layers:
            base = plane_ground(terrain, L["par"], L["off"])
            hc = 540.0 + (-1300.0 - 540.0) * L["par"]
            if L["name"] == "far":
                # the hill crest; the church sits on the top
                L["g"] = (lambda b, hc: (lambda xl: b(xl) - 300.0 * np.exp(-((np.asarray(xl, dtype=float) - hc) / 700.0) ** 2)
                                         - 120.0 * np.exp(-((np.asarray(xl, dtype=float) - hc - 1100) / 500.0) ** 2)))(base, hc)
            elif L["name"] == "mid":
                L["g"] = (lambda b, hc: (lambda xl: b(xl) - 160.0 * np.exp(-((np.asarray(xl, dtype=float) - hc) / 1100.0) ** 2)))(base, hc)
            else:
                L["g"] = base
        self._built = {}
        self.door = Doorway(self.door_x, terrain, size=DOOR_SIZE, wall_on=False, seed=seed + 1)
        self.lantern = Lantern(size=2.1)

    # ------------------------------------------------------------ layout
    def _layer_items(self, L):
        key = L["name"]
        if key in self._built:
            return self._built[key]
        par, sc = L["par"], L["sc"]
        a, b = self.x_range
        xa, xb = 540 + (a - 1400 - 540) * par, 540 + (b + 300 - 540) * par
        s = self.seed * 97 + int(par * 100)
        items = []
        x = xa
        k = 0
        church_at = 540 + (-1300.0 - 540) * par if L["name"] == "far" else None
        while x < xb:
            k += 1
            if church_at is not None and x > church_at - 700 * sc * 1.15 - 200:
                # the church on the hill (placed once), clear space around it
                items.append(("house", _church(church_at, L["g"], sc * 1.15, s + 999)))
                x = max(x, church_at + 700 * sc * 1.15 + 260)
                church_at = None
                continue
            w = (1300 + 600 * rnd(s, k, 1)) * sc
            wall = (620 + 160 * rnd(s, k, 2)) * sc
            pitch = 50 + 9 * rnd(s, k, 3)
            door = x + w / 2 + w * 0.28 * srnd(s, k, 11) if L["name"] in ("near", "mid") else None
            items.append(("house", _house(x + w / 2, L["g"], w, wall, pitch, s + k, sc=sc,
                                          windows=1 + int(2.5 * rnd(s, k, 4)), lit=L["lit"], door=door)))
            if door is not None:
                n_doors = sum(1 for kd, it in items if kd == "house" and "door_x" in it)
                items[-1][1]["door_x"] = door
                items[-1][1]["door_id"] = L["name"][0] + str(n_doors)      # "n0", "n1", ... "m0", ...
            x += w + lerp(*L["gap"], rnd(s, k, 5))
            # trees and spruces between houses
            if rnd(s, k, 6) < 0.6:
                tx = x - lerp(*L["gap"], 0.5) * 0.55
                items.append(("spruce", _make_spruce(tx, float(L["g"](tx)), (900 + 700 * rnd(s, k, 7)) * sc, s + k * 3)))
            if rnd(s, k, 8) < 0.55:
                tx = x - lerp(*L["gap"], 0.5) * 0.3
                items.append(("tree", _bare_tree(tx, L["g"], (1300 + 700 * rnd(s, k, 9)) * sc, s + k * 5)))
            if L["name"] == "near" and rnd(s, k, 10) < 0.5:
                items.append(("lamp", dict(x=x - 160 * sc, sc=sc)))
        self._built[key] = items
        return items

    def _plane_items(self):
        if "plane" in self._built:
            return self._built["plane"]
        G = self.T.ground_y
        s = self.seed
        items = []
        # the mother's house (her door at door_x), real scale
        mh = _house(self.door_x - 120, G, 1650, 905, 52, s + 1, sc=1.0, windows=2, lit=1.0, door=self.door_x)
        items.append(("house", mh))
        # two more houses up the street
        items.append(("house", _house(self.door_x - 2350, G, 1500, 860, 54, s + 2, sc=1.0, windows=2, lit=0.7)))
        items.append(("house", _house(-4700, G, 1400, 820, 52, s + 3, sc=1.0, windows=1, lit=0.6)))
        self._built["plane"] = items
        self._mother = mh
        return items

    # ------------------------------------------------------------ drawing pieces
    def _paint_houses(self, f, c, items, mood, tint, par, windows=True):
        ink = fogged(mood, tint) if tint > 0 else mood.ink
        snow_c = fogged(mood, tint, mood.snow) if tint > 0 else mood.snow
        houses = [it for kind, it in items if kind == "house"]
        others = [(kind, it) for kind, it in items if kind not in ("house", "lamp")]
        for kind, it in others:
            if kind == "tree":
                _fill(c, it["limbs"], ink)
                _fill(c, it["snow"], snow_c)
            elif kind == "spruce":
                for a, b in it:
                    _fill(c, a, ink)
                    _fill(c, b, snow_c)
        _fill(c, [p for h in houses for p in h["ink"]], ink)
        lit_on = mood.night > 0.25 and windows
        lamp = mood.lamp
        for h in houses:
            for poly, lit, cen, size in h["windows"]:
                if lit and lit_on:
                    col = mix(mix(INK, lamp, 0.8), mix(lamp, SNOW, 0.18), 0.45 + 0.4 * flick(f.t, int(cen[0]) % 97, rate=2.0, depth=0.2))
                    if tint > 0:
                        col = mix(col, mood.fog_at(tint), tint * 0.55)
                    draw.poly(c, poly)
                    draw.fill(c, col)
            _fill(c, h["mullions"], ink)
        _fill(c, [p for h in houses for p in h["snow"]], snow_c)
        _fill(c, [p for h in houses for p in h["sills"]], snow_c)

    def _window_glow(self, f, items, mood, par, tint):
        """Glow of lit windows. On the action plane it goes to the emissive buffer (bloom);
        rear rows use an additive pass composited right away, so nearer houses occlude it
        (the emissive buffer is added at finish() over everything)."""
        if mood.night <= 0.25:
            return
        gain = mood.lamp_gain * clamp((mood.night - 0.25) / 0.5) * (1.0 - 0.6 * tint)
        if gain <= 0.02:
            return
        wins = [(cen, size) for kind, h in items if kind == "house" for poly, lit, cen, size in h["windows"] if lit]
        if not wins:
            return
        if par >= 1.0:
            with f.emit(par=par) as G:
                for cen, size in wins:
                    glow(G, cen, max(size) * 1.0, mood.lamp, 0.42 * gain)
        else:
            with soft_layer(f, par, k=4, op="add", blur=16.0) as A:
                for cen, size in wins:
                    glow(A, cen, max(size) * 1.6, mood.lamp, 0.30 * gain)
                    glow(A, (cen[0], cen[1] + size[1] * 1.2), max(size) * 1.4, mood.lamp, 0.10 * gain)

    def _smoke(self, f, items, mood, par, tint, wind=34.0):
        """Chimney smoke: soft puffs rising and leaning with the wind (low-res layer)."""
        chims = [h["chimney"] for kind, h in items if kind == "house" and h["chimney"]]
        if not chims:
            return
        vx0, vy0, vx1, vy1 = view(f, par, 600)
        chims = [c for c in chims if vx0 < c[0] < vx1 and c[1] > vy0 - 1600]
        if not chims:
            return
        col = mix(mood.fog_at(1.0), SNOW, 0.25) if mood.night > 0.5 else mix(mood.fog_at(0.7), SNOW, 0.3)
        sc = {0.3: 0.35, 0.55: 0.6, 0.8: 0.85}.get(par, 1.0)
        with soft_layer(f, par, k=4, blur=10.0) as S:
            for j, (cx, cy) in enumerate(chims):
                life = 6.5
                n = 16
                for i in range(n):
                    ph = (f.t / life + i / n + rnd(j, i, 1) * 0.02) % 1.0
                    age = ph * life
                    rise = 105 * sc * age
                    x = cx + wind * sc * age * (0.4 + 0.15 * age) + 16 * sc * math.sin(age * 0.9 + i) * clamp(age / 2)
                    y = cy - rise
                    r = (22 + 17 * age) * sc
                    a = 0.34 * math.sin(math.pi * clamp(ph * 1.15)) ** 0.8 * (1.0 - 0.4 * tint)
                    draw.circle(S, (x, y), r)
                    draw.fill(S, col, a)

    # ------------------------------------------------------------ public draw
    def draw_back(self, f, mood=NIGHT, smoke=True, mist=True, doors=None, door_light=None, t=None,
                  door_figures=None):
        """Sky, the far hill with the church, mid and near rows of houses (lit windows glow
        through the fog), chimney smoke and mist between the rows.

        doors: how far the front doors of the rows across the street stand open (the village
        watching, S02/S10): None/0 = all shut, a float = all, {id: amount}, or a callable
        (id, t) -> amount (see door_schedule). door_light: interior light of an open door
        (default 1 at night, 0.6 by day). doorways() lists ids and where villagers stand.
        door_figures: optional callable(ctx, door, open_amount, t, mood) that draws whoever
        stands in a doorway, in that row's layer coords (door = dict(id, row, x, y, par, sc,
        depth); mood is pre-fogged for the row: draw in mood.ink). It is called for every
        door in view, after the lit interior and before the door leaf, so a door that
        closes hides them."""
        mood = get_mood(mood)
        t = f.t if t is None else t
        backdrop(f, mood, glow=(540.0, 1250.0), glow_r=1300.0, glow_a=0.22)
        for i, L in enumerate(self.layers):
            items = self._layer_items(L)
            par = L["par"]
            lit_doors = []
            vx0, vy0, vx1, vy1 = view(f, par, 1200)
            vis = [(k, it) for k, it in items if vx0 < (it["x"] if k != "spruce" else it[0][0][0][0][0]) < vx1]
            lamps = [it for k, it in vis if k == "lamp"]
            if L.get("direct"):
                with plane(f, par) as c:
                    self._ground(f, c, L, mood, tint=L["depth"])
                    self._paint_houses(f, c, vis, mood, L["depth"], par)
                    lit_doors = self._row_doors(c, L, vis, mood, doors, door_light, t, figures=door_figures)
                    self._fence_row(f, c, L, mood, tint=L["depth"])
            else:
                with depth_layer(f, mood, par, L["depth"], blur=L["blur"]) as c:
                    self._ground(f, c, L, mood)
                    self._paint_houses(f, c, vis, mood, 0.0, par)
                    lit_doors = self._row_doors(c, L, vis, mood, doors, door_light, t, tint=0.0,
                                                figures=door_figures)
                    if mist:
                        xs = np.linspace(vx0 + 900, vx1 - 900, 14)
                        mist_band(c, xs, np.asarray(L["g"](xs), dtype=float), mood.mist, 0.5, up=380.0, down=120.0)
            if lit_doors:
                self._door_wedges(f, L, lit_doors, mood)
            if lamps:
                self._row_lamps(f, L, lamps, mood)
            self._window_glow(f, vis, mood, par, L["depth"])
            if smoke:
                self._smoke(f, vis, mood, par, L["depth"])
            if mist and L.get("direct"):
                ground_mist(f, par, L["g"], mood.mist, 0.35, up=300.0, down=100.0)

    @staticmethod
    def _door_amount(doors, i, t):
        if doors is None:
            return 0.0
        if callable(doors):
            return clamp(float(doors(i, t)))
        if isinstance(doors, dict):
            return clamp(float(doors.get(i, 0.0)))
        return clamp(float(doors))

    def _row_doors(self, c, L, vis, mood, doors, light, t, tint=None, figures=None):
        """Front doors of a row's houses (porch, frame, step); open ones show the lit room.
        Returns [(x, y, w, h, light)] of the open, lit ones (for their glow and wedge).
        figures: draw_back's door_figures hook (people standing in the doorways)."""
        tm = tinted(mood, L["depth"] if tint is None else tint)
        G = _LayerGround(L["g"])
        light = (1.0 if mood.night > 0.3 else 0.6) if light is None else light
        out = []
        for kind, h in vis:
            if kind != "house" or h.get("door_x") is None:
                continue
            o = self._door_amount(doors, h["door_id"], t)
            size = DOOR_SIZE * L["sc"]
            inside = None
            if figures is not None:
                d = dict(id=h["door_id"], row=L["name"], x=h["door_x"], y=float(L["g"](h["door_x"])),
                         par=L["par"], sc=L["sc"], depth=L["depth"])
                inside = (lambda ctx, d=d, o=o: figures(ctx, d, o, t, tm))
            Doorway(h["door_x"], G, size=size, wall_on=False, seed=self.seed + 31 + len(h["door_id"])).draw_back(
                None, c, tm, open_=o, light=light * smoothstep(0.0, 0.35, o), t=t, inside=inside)
            a = light * smoothstep(0.0, 0.35, o)
            if a > 0.01:
                out.append((h["door_x"], float(L["g"](h["door_x"])), 150 * size, 420 * size, a))
        return out

    def _door_wedges(self, f, L, lit, mood):
        """Glow of the open doors and the wedge of light each throws across the snow (an
        additive pass on the row's plane, so nearer houses hide it)."""
        if mood.night <= 0.3:
            return
        g = mood.lamp_gain * clamp((mood.night - 0.3) / 0.4) * (1.0 - 0.5 * L["depth"])
        with soft_layer(f, L["par"], k=4, op="add", blur=10.0) as A:
            for (x, gy, dw, dh, a) in lit:
                glow(A, (x, gy - dh * 0.45), dw * 1.8, mood.lamp, 0.3 * a * g)
                reach = dh * 0.75
                draw.linear(A, (0, gy - 4), (0, gy + reach), [(0, mood.lamp, 0.55 * a * g), (1, mood.lamp, 0.0)])
                draw.poly(A, [(x - dw * 0.5, gy - 4), (x + dw * 0.5, gy - 4), (x + dw * 2.2, gy + reach),
                              (x - dw * 2.2, gy + reach)])
                A.fill()

    def doorways(self, f=None):
        """Front doors of the rows of houses up the slope across the street (near row "n0",
        "n1", ... and the smaller mid row "m0", ...), where villagers stand and watch (S02,
        S10). Each: dict(id, row, x, y, par, sc, world_x[, sx, sy]), sorted by world_x: the
        threshold in that row's layer coords (draw a villager there inside
        f.layer(par=par), scaled by sc relative to the action plane); world_x is the
        action-plane x it lines up with when the camera is at rest; with a frame f, (sx, sy)
        is the threshold on screen (frame px) for f's camera. Open/close: draw_back(doors=...)."""
        out = []
        for L in self.layers:
            if L["name"] not in ("near", "mid"):
                continue
            cam = f.lcam(L["par"]) if f is not None else None
            for kind, h in self._layer_items(L):
                if kind == "house" and h.get("door_x") is not None:
                    x = h["door_x"]
                    d = dict(id=h["door_id"], row=L["name"], x=x, y=float(L["g"](x)), par=L["par"], sc=L["sc"],
                             world_x=540.0 + (x - 540.0) / L["par"])
                    if cam is not None:
                        d["sx"], d["sy"] = cam.to_screen((x, d["y"]))
                        top = cam.to_screen((x, d["y"] - 420.0 * DOOR_SIZE * L["sc"]))[1]
                        d["visible"] = (-60.0 < d["sx"] < 1140.0 and not self._hidden(f, d["sx"], top))
                    out.append(d)
        return sorted(out, key=lambda d: d["world_x"])

    def _hidden(self, f, sx, sy):
        """True if screen point (sx, sy) is behind one of the action-plane houses."""
        for kind, h in self._plane_items():
            x0, y0 = f.cam.to_screen((h["x"] - h["w"] / 2 - 90.0, h["ridge"]))
            x1, y1 = f.cam.to_screen((h["x"] + h["w"] / 2 + 90.0, h["gy"]))
            if x0 < sx < x1 and sy < y1:
                cx = (x0 + x1) / 2
                ey = f.cam.to_screen((h["x"], h["eave"]))[1]
                roof = y0 + (ey - y0) * abs(sx - cx) / max((x1 - x0) / 2, 1e-6)
                if sy > roof:
                    return True
        return False

    def doors_near(self, world_x, n=3, row=None, f=None):
        """Ids of the n doorways closest to action-plane x (e.g. the mother's door V.door_x
        for the S02 two-shot), left to right. With a frame f the match is made on screen for
        f's camera, skipping doors off screen or hidden behind the street's houses (best:
        these are the doors you will actually see)."""
        ds = [d for d in self.doorways(f) if (row is None or d["row"] == row) and d.get("visible", True)]
        if f is not None:
            sx = f.cam.to_screen((world_x, 0.0))[0]
            key = lambda d: abs(d["sx"] - sx)
        else:
            key = lambda d: abs(d["world_x"] - world_x)
        ds = sorted(ds, key=key)[:n]
        return [d["id"] for d in sorted(ds, key=lambda d: d["world_x"])]

    @staticmethod
    def door_schedule(close_at, open_at=None, dur=0.35):
        """doors= callable for draw_back: door id -> open amount over time. close_at
        {id: t} shuts each door at its time (S02: the light wedges vanish on [didn't],
        [know], [yet]); open_at {id: t} opens it (default: open from the start)."""
        open_at = open_at or {}

        def fn(i, t):
            a = 1.0 if i not in open_at else smoothstep(open_at[i], open_at[i] + dur, t)
            if i in close_at:
                a *= 1.0 - smoothstep(close_at[i], close_at[i] + dur, t)
            return a if (i in close_at or i in open_at) else 0.0
        return fn

    def _row_lamps(self, f, L, lamps, mood):
        """Lantern posts in a rear row (pre-fogged), with an occludable additive glow."""
        par, tint = L["par"], L["depth"]
        ink = fogged(mood, tint)
        lit = mood.night > 0.3
        with plane(f, par) as c:
            for it in lamps:
                x, sc = it["x"], it["sc"]
                gy = float(L["g"](x))
                _fill(c, [[(x - 16 * sc, gy + 40), (x - 13 * sc, gy - 860 * sc), (x + 13 * sc, gy - 860 * sc), (x + 16 * sc, gy + 40)],
                          _orient([(x - 13 * sc, gy - 850 * sc), (x + 170 * sc, gy - 850 * sc), (x + 170 * sc, gy - 832 * sc),
                                   (x - 13 * sc, gy - 832 * sc)])], ink)
                it["flame"] = self.lantern.draw(None, c, (x + 150 * sc, gy - 832 * sc), 2.0 * math.sin(f.t + x), lit=1.0 if lit else 0.0,
                                                t=f.t, mood=mood, tint=tint, seed=int(x) % 17)
        if lit:
            with soft_layer(f, par, k=4, op="add", blur=14.0) as A:
                for it in lamps:
                    fx, fy = it["flame"]
                    glow(A, (fx, fy), 300 * it["sc"], mood.lamp, 0.45 * mood.lamp_gain * (1 - 0.5 * tint))
                    light_pool(A, (fx, float(L["g"](fx)) + 20), 380 * it["sc"], 70 * it["sc"], mood.lamp,
                               0.35 * mood.lamp_gain * (1 - 0.5 * tint))

    def _ground(self, f, c, L, mood, tint=0.0):
        vx0, vy0, vx1, vy1 = view(f, L["par"], 100)
        xs = np.linspace(vx0, vx1, 40)
        ys = np.asarray(L["g"](xs), dtype=float)
        c.move_to(xs[0], vy1 + 50)
        for x, y in zip(xs, ys):
            c.line_to(x, y)
        c.line_to(xs[-1], vy1 + 50)
        c.close_path()
        col = fogged(mood, tint, mood.snow) if tint > 0 else mood.snow
        col2 = fogged(mood, tint, mood.snow_dark) if tint > 0 else mood.snow_dark
        draw.linear(c, (0, float(ys.min())), (0, float(ys.min()) + 500), [(0, col, 1), (1, col2, 1)])
        c.fill()

    def _fence_row(self, f, c, L, mood, tint=0.0):
        """A low picket fence along the near row's gardens."""
        vx0, vy0, vx1, vy1 = view(f, L["par"], 200)
        sc = L["sc"]
        sp = 46 * sc
        ink = fogged(mood, tint)
        snow_c = fogged(mood, tint, mood.snow)
        k0, k1 = int(vx0 // sp), int(vx1 // sp) + 1
        polys, caps, rails = [], [], []
        for k in range(k0, k1):
            if (k // 26) % 3 == 2:          # gaps between gardens
                continue
            x = k * sp
            gy = float(L["g"](x)) + 30 * sc
            h = (210 + 20 * rnd(self.seed, k, 2)) * sc
            pw = 15 * sc
            polys.append([(x - pw / 2, gy + 10), (x - pw / 2, gy - h), (x, gy - h - 12 * sc), (x + pw / 2, gy - h), (x + pw / 2, gy + 10)])
            caps.append(_orient([(x - pw * 0.7, gy - h + 2), (x, gy - h - 22 * sc), (x + pw * 0.7, gy - h + 2)]))
        _fill(c, polys, ink)
        _fill(c, caps, snow_c)

    def draw_plane(self, f, mood=NIGHT, door_open=1.0, door_light=None, t=None, ground=True, door_glow=1.0):
        """The street (snow), the mother's house and doorway, the other plane houses, the well,
        the fence, the gate and the lantern posts with their light pools. door_glow scales the
        mother's doorway emissive bloom (lower it while someone stands in the doorway: the
        bloom is added over everything at finish)."""
        mood = get_mood(mood)
        t = f.t if t is None else t
        if door_light is None:
            door_light = 1.0 if mood.night > 0.3 else 0.0
        items = self._plane_items()
        vx0, vy0, vx1, vy1 = view(f, 1.0, 1300)
        vis = [(k, it) for k, it in items if vx0 < it["x"] < vx1]
        with plane(f, 1.0) as c:
            self._paint_houses(f, c, vis, mood, 0.0, 1.0)
            self._fence_plane(c, mood)
            self._gate(f, c, mood, t)
            self._well(c, mood, t)
        self._window_glow(f, vis, mood, 1.0, 0.0)
        self._smoke(f, vis, mood, 1.0, 0.0)
        if ground:
            self.T.draw_back(f, mood, groove=False)
        with plane(f, 1.0) as c:
            if vx0 - 400 < self.door_x < vx1 + 400:
                self.door.draw_back(f, c, mood, open_=door_open, light=door_light, t=t, glow=door_glow)
            for x in self.lantern_x:
                if vx0 - 600 < x < vx1 + 600:
                    self._lantern_post(f, c, x, mood, t)

    def ground_lights(self, f, mood=NIGHT, door_light=None, t=None):
        """Light pools on the snow under the lanterns and the door's spill (additive). Drawn by
        draw_front after the snow lip; call it yourself if you skip draw_front."""
        mood = get_mood(mood)
        t = f.t if t is None else t
        if mood.night <= 0.3:
            return
        if door_light is None:
            door_light = 1.0
        vx0, vy0, vx1, vy1 = view(f, 1.0, 900)
        G = self.T.snow_y
        with soft_layer(f, 1.0, k=6, op="add", blur=30.0) as A:
            for (fx, fy), x in zip(self.lanterns, list(self.lantern_x) + [self.gate_x]):
                if vx0 < fx < vx1:
                    gain = mood.lamp_gain * flick(t, int(x) % 31 + 3)
                    light_pool(A, (fx, float(G(fx)) + 40), 640, 170, mood.lamp, 0.42 * gain)
        if vx0 - 400 < self.door_x < vx1 + 400:
            self.door.draw_spill(f, mood, light=door_light, t=t)

    def draw_front(self, f, mood=NIGHT, lip=True, sink=6.0, occluders=False, door_light=None):
        """Snow lip in front of feet, the ground light pools (+ optional blurred foreground
        fence posts)."""
        mood = get_mood(mood)
        if lip:
            self.T.draw_front(f, mood, sink=sink)
        self.ground_lights(f, mood, door_light=door_light)
        if occluders:
            par = 1.4
            vx0, vy0, vx1, vy1 = view(f, par, 300)
            g = plane_ground(self.T, par, 260.0)
            polys, caps = [], []
            for k in range(int(vx0 // 900) - 1, int(vx1 // 900) + 2):
                if rnd(self.seed, k, 31) < 0.5:
                    continue
                x = k * 900 + 300 * rnd(self.seed, k, 32)
                gy = float(g(x))
                h = 520 + 120 * rnd(self.seed, k, 33)
                polys.append([(x - 26, gy + 200), (x - 24, gy - h), (x + 22, gy - h - 10), (x + 26, gy + 200)])
                caps.append(_orient([(x - 34, gy - h + 6), (x - 10, gy - h - 26), (x + 30, gy - h - 16), (x + 34, gy - h - 4)]))
            if polys:
                with f.layer(par=par, blur=12.0) as c:
                    _fill(c, polys, mood.ink)
                    _fill(c, caps, mood.snow)

    def draw(self, f, mood=NIGHT, **kw):
        self.draw_back(f, mood)
        self.draw_plane(f, mood, **kw)
        self.draw_front(f, mood)

    # ------------------------------------------------------------ plane pieces
    def _fence_plane(self, c, mood):
        """Picket fence along the street, behind characters, with snow on the rails."""
        G = self.T.snow_y
        polys, snow = [], []
        for (a, b) in ((-4100.0, -2950.0), (-930.0 + 240, -190.0)):
            sp = 58.0
            n = int((b - a) / sp)
            for i in range(n + 1):
                x = a + i * sp
                gy = float(G(x)) - 70        # fence stands a little behind the street edge
                h = 300 + 18 * srnd(self.seed, i, 41)
                pw = 22
                polys.append([(x - pw / 2, gy + 90), (x - pw / 2, gy - h), (x, gy - h - 18), (x + pw / 2, gy - h), (x + pw / 2, gy + 90)])
                snow.append(_orient([(x - pw * 0.75, gy - h + 4), (x - 2, gy - h - 26), (x + pw * 0.75, gy - h + 4)]))
            for ry in (110, 230):
                pts = [(a - 10, float(G(a)) - 70 - ry), (b + 10, float(G(b)) - 70 - ry)]
                polys.append(_orient(draw.ribbon(pts, [16, 16])))
                snow.append(_orient(draw.ribbon([(p[0], p[1] - 11) for p in pts], [8, 8])))
        _fill(c, polys, mood.ink)
        _fill(c, snow, mood.snow)

    def _gate(self, f, c, mood, t):
        """The village gate at x = gate_x: two tall posts under a little gabled roof, one leaf
        swung open, a lantern hanging from the beam. The path starts on the far side."""
        x = self.gate_x
        G = self.T.snow_y
        gy = float(G(x))
        half = 330.0
        ink, snow = [], []
        for side in (-1, 1):
            px = x + side * half
            pgy = float(G(px))
            ink.append([(px - 26, pgy + 60), (px - 26, gy - 900), (px + 26, gy - 900), (px + 26, pgy + 60)])
        beam_y = gy - 880
        ink.append(_orient([(x - half - 90, beam_y), (x + half + 90, beam_y), (x + half + 90, beam_y + 34),
                            (x - half - 90, beam_y + 34)]))
        roof = [(x - half - 170, beam_y + 10), (x, beam_y - 240), (x + half + 170, beam_y + 10), (x + half + 150, beam_y + 22),
                (x, beam_y - 214), (x - half - 150, beam_y + 22)]
        ink.append(_orient(roof))
        snow.append(_orient([(x - half - 186, beam_y + 12), (x - half * 0.5, beam_y - 160), (x, beam_y - 280),
                             (x + half * 0.5, beam_y - 160), (x + half + 186, beam_y + 12), (x + half + 160, beam_y + 6),
                             (x, beam_y - 232), (x - half - 160, beam_y + 6)]))
        # open leaf (seen edge-on, swung toward us: a narrow slanted panel with pickets)
        lx = x + half - 30
        leaf = [(lx, gy - 30), (lx, gy - 420), (lx + 170, gy - 380), (lx + 170, gy - 40)]
        ink.append(_orient([(lx, gy - 400), (lx + 170, gy - 362), (lx + 170, gy - 340), (lx, gy - 378)]))
        ink.append(_orient([(lx, gy - 120), (lx + 170, gy - 100), (lx + 170, gy - 78), (lx, gy - 98)]))
        for k in range(5):
            u = k / 4
            px = lx + 170 * u
            ink.append(_orient([(px - 7, gy - 40 + 10 * u), (px - 7, gy - 440 + 40 * u), (px, gy - 456 + 40 * u),
                                (px + 7, gy - 440 + 40 * u), (px + 7, gy - 40 + 10 * u)]))
        _fill(c, ink, mood.ink)
        _fill(c, snow, mood.snow)
        # lantern hanging from the beam
        hook = (x, beam_y + 34)
        ang = swing_angle(t, lambda tt: x, length=120, kick=4.0, seed=7) if False else 3.0 * math.sin(t * 1.1)
        c.move_to(*hook)
        c.line_to(hook[0] - math.sin(math.radians(ang)) * 40, hook[1] + 40)
        draw.stroke(c, mood.ink, 5)
        self.lantern.draw(f, c, (hook[0] - math.sin(math.radians(ang)) * 40, hook[1] + 40), ang,
                          lit=1.0 if mood.night > 0.3 else 0.0, t=t, mood=mood, seed=11)

    def _well(self, c, mood, t):
        """Stone well: drum with a rough stone rim, two posts, a winch and a small roof."""
        x = self.well_x
        G = self.T.snow_y
        gy = float(G(x)) - 30
        w2 = 250.0
        ink, snow = [], []
        rim = [(x - w2, gy + 80), (x - w2, gy - 260)]
        for i in range(12):
            u = (i + 0.5) / 12
            rim.append((x - w2 + 2 * w2 * u, gy - 262 - 14 * rnd(self.seed, i, 51)))
        rim += [(x + w2, gy - 260), (x + w2, gy + 80)]
        ink.append(_orient(rim))
        for side in (-1, 1):
            px = x + side * (w2 - 30)
            ink.append([(px - 18, gy - 200), (px - 18, gy - 760), (px + 18, gy - 760), (px + 18, gy - 200)])
        ink.append(_orient([(x - w2 + 10, gy - 640), (x + w2 - 10, gy - 640), (x + w2 - 10, gy - 618), (x - w2 + 10, gy - 618)]))
        ink.append(_orient(draw.ellipse_pts((x + w2 - 30, gy - 629), 34, 34, n=12)))
        roof = [(x - w2 - 90, gy - 720), (x, gy - 900), (x + w2 + 90, gy - 720), (x + w2 + 70, gy - 708), (x, gy - 878),
                (x - w2 - 70, gy - 708)]
        ink.append(_orient(roof))
        snow.append(_orient([(x - w2 - 104, gy - 718), (x - w2 * 0.4, gy - 840), (x, gy - 930), (x + w2 * 0.4, gy - 842),
                             (x + w2 + 104, gy - 718), (x + w2 + 80, gy - 724), (x, gy - 892), (x - w2 - 80, gy - 724)]))
        snow.append(_orient([(x - w2 - 10, gy - 262), (x - w2 * 0.3, gy - 292), (x + w2 * 0.4, gy - 286), (x + w2 + 10, gy - 262),
                             (x + w2, gy - 252), (x - w2, gy - 252)]))
        # rope and bucket
        sw = 6 * math.sin(t * 0.8)
        ink.append(_orient(draw.ribbon([(x, gy - 629), (x + sw, gy - 400)], [5, 5])))
        ink.append(_orient([(x + sw - 34, gy - 410), (x + sw + 34, gy - 410), (x + sw + 26, gy - 340), (x + sw - 26, gy - 340)]))
        _fill(c, ink, mood.ink)
        _fill(c, snow, mood.snow)

    def _lantern_post(self, f, c, x, mood, t):
        """A lantern post: post, arm, hanging lantern, snow on the arm; light pool on the snow."""
        G = self.T.snow_y
        gy = float(G(x)) - 40
        ink = [[(x - 20, gy + 80), (x - 16, gy - 880), (x + 16, gy - 880), (x + 20, gy + 80)],
               _orient([(x - 16, gy - 860), (x + 190, gy - 860), (x + 190, gy - 838), (x - 16, gy - 838)]),
               _taper_limb([(x + 12, gy - 760), (x + 120, gy - 852)], 7, 5)]
        _fill(c, ink, mood.ink)
        _fill(c, [_orient([(x - 22, gy - 878), (x + 6, gy - 900), (x + 120, gy - 884), (x + 196, gy - 872), (x + 196, gy - 858),
                           (x - 22, gy - 862)])], mood.snow)
        hook = (x + 170, gy - 838)
        ang = 4.0 * math.sin(t * 0.9 + x * 0.01)
        lit = 1.0 if mood.night > 0.3 else 0.0
        flame = self.lantern.draw(f, c, hook, ang, lit=lit, t=t, mood=mood, seed=int(x) % 31)
        if lit > 0:
            gain = mood.lamp_gain * flick(t, int(x) % 31 + 3)
            with soft_layer(f, 1.0, k=6, op="add", blur=30.0) as A:
                glow(A, flame, 640, mood.lamp, 0.16 * gain)

    # ------------------------------------------------------------ anchors
    @property
    def threshold(self):
        """(x, y) of the mother's door step (she stands here; the girl in front of her)."""
        return self.door.threshold

    @property
    def lanterns(self):
        """World positions of the lantern flames on the action plane (posts + gate)."""
        out = []
        for x in self.lantern_x:
            gy = float(self.T.snow_y(x)) - 40
            out.append((x + 170, gy - 838 + 47 * 2.1))
        gy = float(self.T.snow_y(self.gate_x))
        out.append((self.gate_x, gy - 880 + 34 + 40 + 47 * 2.1))
        return out


VILLAGE = Village()
