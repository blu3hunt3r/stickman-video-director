"""RED sets: the cottage clearing (S07-S09, S11): the old cottage, its giant web, the trees
hung with red hoods, Grandmother's thread, and (years later) the lantern path.

World coords of the CLEARING terrain (sets_terrain): the cottage door is at x = 0, its
threshold at CLEARING.ground_y(0) ~ 1560. The ground is flat from x ~ -600 to ~1500; to the
left it falls away down the approach (the S11 lantern path climbs from the lower left); to
the right it rises toward the forest edge, where tall canopy trees hold the web's anchor
lines and Grandmother's thread. The cottage is ~1640 px long and ~1500 px to the ridge, so
establishing shots sit at zoom ~0.35-0.5; S11 at the door at ~0.8-1.

    C = CLEARING_SET
    burn = C.ignite(t0=12.66)                       # S08: the lantern smashed at C.smash_point
    C.draw_back(f, NIGHT, era="web")                # sky, fog forest, hood trees, dark canopy
    C.draw_plane(f, NIGHT, era="web", burn=burn)    # canopy trees, cottage, web, hoods, snow
    ...characters (feet on CLEARING.ground_y)...
    C.draw_front(f, NIGHT, era="web", burn=burn)    # snow lip, firelight, foreground brambles

Eras: "web" (S07/S08: the old cottage cocooned in silk), "burnt" (S09 dawn: black threads
hanging, smoke, the hoods fall: release=0.0), "later" (S11: mended cottage, warm window and
chimney smoke, the lantern path, no web, no hoods).

Anchors: C.cottage.threshold, C.cottage.anchors(state), C.smash_point, C.spider_top /
C.spider_end (Grandmother's thread), C.web.anchors, C.lanterns.flames(), C.hoods.
"""
import math

import cairo
import numpy as np

from engine import draw
from engine.core import clamp, lerp, smoothstep, fbm1
from .sets_common import (get_mood, mix, INK, SNOW, HOOD_RED, NIGHT, view, plane, depth_layer, backdrop,
                          soft_layer, glow, light_pool, fogged, flick, rnd, srnd, mist_band, ground_mist)
from .sets_terrain import CLEARING
from .sets_forest import (Forest, LAYERS, _orient, _fill, _taper_limb, _curve, _snow_on_limb, _resample_line,
                          _make_tree)
from .sets_props import Lantern, hood_poly, hood_sway
from .sets_web import Web, sag_line, build_orb


# ============================================================================ the cottage
class Cottage:
    """The cottage at the end of the path, long side facing us, door at `door_x`.

    state "old" (S06-S09): swaybacked thatch with a broken ridge (rafters poking out),
    leaning chimney with a broken top, dark doorway with the door hanging open on one hinge,
    broken window (glass shards, a shutter hanging askew), a cart wheel against the corner,
    a collapsed woodpile, a leaning fence.
    state "new" (S11): roof mended, chimney capped and smoking, door shut (warm light at the
    cracks), lit window with open shutters and curtains, neat woodpile and fence.

    The walls are ink lifted a hair toward the fog, so the doorway and window holes (pure
    ink) read as holes. Geometry is cached per state."""

    W = 1640.0          # wall length
    WALL_H = 700.0
    ROOF_H = 740.0
    OV = 130.0          # eave overhang

    def __init__(self, terrain=CLEARING, door_x=0.0, seed=3):
        self.T = terrain
        self.door_x = float(door_x)
        self.seed = seed
        self.x0 = self.door_x - 620.0
        self.x1 = self.x0 + self.W
        self.window_x = self.door_x + 560.0
        self._geo = {}

    @property
    def threshold(self):
        """(x, y) of the door step: where Old Red stands, where the girl would knock."""
        return (self.door_x, float(self.T.ground_y(self.door_x)))

    def anchors(self, state="old"):
        """Named world points: door (x0, y0, x1, y1), window (cx, cy, w, h), chimney (smoke
        point), ridge [pts], eave [pts], eave_l / eave_r, corner_l / corner_r (wall tops),
        lantern_hook (S11: where the last lantern hangs by the door), step."""
        return self.geometry(state)["anchors"]

    def geometry(self, state="old"):
        if state not in self._geo:
            self._geo[state] = self._build(state)
        return self._geo[state]

    # ------------------------------------------------------------ build
    def _build(self, state):
        old = state == "old"
        s = self.seed
        T = self.T

        def G(x):
            return float(T.ground_y(x))

        x0, x1, dx = self.x0, self.x1, self.door_x
        gd = G(dx)
        H = self.WALL_H
        lean = 24.0 if old else 5.0
        sag_e = 30.0 if old else 5.0
        sag_r = 105.0 if old else 12.0
        ov = self.OV

        def lx(x, h):                      # wall x at height h (the old walls lean right)
            return x + lean * h / H

        def eave_y(x):
            u = clamp((x - x0) / (x1 - x0))
            return gd - H + sag_e * math.sin(math.pi * u) + (14.0 * u if old else 0.0)

        body, roof, ink, holes, snow, glass, seams, lit, leaf, curtains = [], [], [], [], [], [], [], [], [], []
        # ---------------------------------------------------------------- walls (log corners)
        gb = max(G(x0), G(x1), gd) + 80
        nlog = 8
        step = H / nlog
        wall = [(x0, gb)]
        for i in range(nlog):
            h = i * step
            y = gd - h
            xl = lx(x0, h)
            ext = 24 + (14 if old else 4) * rnd(s, i, 1)
            wall += [(xl, y - step * 0.12), (xl - ext, y - step * 0.16), (xl - ext, y - step * 0.84), (xl, y - step * 0.88)]
        wall += [(lx(x0, H), eave_y(x0)), (lx(x1, H), eave_y(x1))]
        for i in range(nlog - 1, -1, -1):
            h = i * step
            y = gd - h
            xr = lx(x1, h)
            ext = 24 + (14 if old else 4) * rnd(s, i, 2)
            wall += [(xr, y - step * 0.88), (xr + ext, y - step * 0.84), (xr + ext, y - step * 0.16), (xr, y - step * 0.12)]
        wall += [(x1, gb)]
        body.append(_orient(wall))
        for i in range(1, nlog):
            h = i * step
            pts = []
            for k in range(9):
                u = k / 8
                x = lerp(lx(x0, h), lx(x1, h), u)
                pts.append((x, gd - h + (4.0 * srnd(s, i, k, 3) if old else 0.0)))
            seams.append(pts)
        # ---------------------------------------------------------------- roof (thatch, hipped)
        base = gd - H - self.ROOF_H
        xr0, xr1 = x0 + 300 + lean, x1 - 280 + lean

        def ridge_y(x):
            u = clamp((x - xr0) / (xr1 - xr0))
            y = base + sag_r * math.sin(math.pi * u) ** 1.2
            return y + (10.0 * fbm1(x / 160.0, s + 5) if old else 0.0)

        notch = (lerp(xr0, xr1, 0.30), lerp(xr0, xr1, 0.43)) if old else None
        ridge = []
        n = 28
        for i in range(n + 1):
            x = lerp(xr0, xr1, i / n)
            y = ridge_y(x)
            if notch and notch[0] < x < notch[1]:
                v = (x - notch[0]) / (notch[1] - notch[0])
                y += 125 * math.sin(math.pi * v) ** 0.6 + 16 * srnd(s, i, 9)
            ridge.append((x, y))
        eL = (x0 - ov + lean, eave_y(x0) + (30.0 if old else 22.0))
        eR = (x1 + ov + lean, eave_y(x1) + 22.0)

        def hip(a, b, bulge, m=6):
            out = []
            ddx, ddy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(ddx, ddy) or 1.0
            nx, ny = ddy / L, -ddx / L            # outward for a clockwise outline
            for i in range(1, m):
                u = i / m
                k = bulge * math.sin(math.pi * u) + (6 * srnd(s, i, int(a[0])) if old else 0.0)
                out.append((lerp(a[0], b[0], u) + nx * k, lerp(a[1], b[1], u) + ny * k))
            return out

        hipL = hip(eL, ridge[0], 26.0)
        hipR = hip(ridge[-1], eR, 26.0)
        fringe = []
        m = 30
        for i in range(m + 1):
            x = lerp(eR[0], eL[0], i / m)
            jag = (10 + 26 * rnd(s, i, 11) ** 2) if old else 6 * rnd(s, i, 11)
            fringe.append((x, eave_y(min(max(x - lean, x0), x1)) + 40 + jag))
        roof_poly = [eL] + hipL + ridge + hipR + [eR] + fringe
        roof.append(_orient(roof_poly))
        # thatch streaks (texture lines from the ridge down the roof face)
        for i in range(16):
            u = (i + 0.5) / 16
            xa = lerp(xr0, xr1, u)
            xb = lerp(eL[0] + 60, eR[0] - 60, u)
            ya = ridge_y(xa) + 50
            yb = eave_y(min(max(xb - lean, x0), x1)) + 10
            seams.append([(xa, ya), (lerp(xa, xb, 0.5) + 8 * srnd(s, i, 12), lerp(ya, yb, 0.5)), (xb, yb)])
        # rafters poking out of the broken ridge
        if notch:
            for k in range(4):
                bx = lerp(notch[0], notch[1], (k + 0.5) / 4) + 14 * srnd(s, k, 13)
                by = ridge_y(bx) + 150
                tx = bx + (46 * srnd(s, k, 14))
                ty = ridge_y(bx) - 55 - 75 * rnd(s, k, 15)
                ink.append(_taper_limb([(bx, by), (tx, ty)], 10, 6))
            ink.append(_taper_limb([(notch[0] - 20, ridge_y(notch[0]) + 30), (notch[1] + 10, ridge_y(notch[1]) + 70)], 7, 5))
        # ---------------------------------------------------------------- chimney
        xc = x1 - 470 + lean
        yr = ridge_y(xc)
        cw = 120.0
        top = yr - (230.0 if old else 260.0)
        by = yr + 220
        if old:
            cpts = [(xc - cw / 2, by), (xc - cw / 2, top + 34), (xc - cw / 4, top + 4), (xc - cw * 0.05, top + 30),
                    (xc + cw * 0.18, top - 10), (xc + cw / 2, top + 46), (xc + cw / 2, by)]
            tilt = 5.0
        else:
            cpts = [(xc - cw / 2, by), (xc - cw / 2, top), (xc - cw / 2 - 16, top), (xc - cw / 2 - 16, top - 26),
                    (xc + cw / 2 + 16, top - 26), (xc + cw / 2 + 16, top), (xc + cw / 2, top), (xc + cw / 2, by)]
            tilt = 0.0
        a = math.radians(tilt)

        def rot(p):
            px, py = p[0] - xc, p[1] - by
            return (xc + px * math.cos(a) - py * math.sin(a), by + px * math.sin(a) + py * math.cos(a))

        body.append(_orient([rot(p) for p in cpts]))
        chim_top = rot((xc + (cw * 0.1 if old else 0.0), top - (0 if old else 30)))
        cs = [(xc - cw / 2 - 18, top - (26 if not old else -30)), (xc - 10, top - (52 if not old else 0)),
              (xc + cw / 2 + 18, top - (30 if not old else -40)), (xc + cw / 2 + 12, top - (20 if not old else -46)),
              (xc - cw / 2 - 12, top - (16 if not old else -36))]
        snow.append(_orient([rot(p) for p in cs]))
        # ---------------------------------------------------------------- snow on the roof
        cap_top, cap_bot = [], []
        for i, (x, y) in enumerate(ridge):
            inn = notch and notch[0] - 20 < x < notch[1] + 20
            th = 0.0 if inn else (22 + 40 * rnd(s, i, 20) ** 1.8)
            cap_top.append((x, y - th))
            cap_bot.append((x, y + (0 if inn else 10 + 22 * rnd(s, i, 19) ** 2)))
        if notch:
            k0 = max(i for i, (x, y) in enumerate(ridge) if x < notch[0] - 20)
            k1 = min(i for i, (x, y) in enumerate(ridge) if x > notch[1] + 20)
            snow.append(_orient(cap_top[:k0 + 1] + cap_bot[:k0 + 1][::-1]))
            snow.append(_orient(cap_top[k1:] + cap_bot[k1:][::-1]))
        else:
            snow.append(_orient(cap_top + cap_bot[::-1]))
        for side, hp, end in ((-1, hipL, ridge[0]), (1, hipR, ridge[-1])):
            pts = [end] + (hp[::-1] if side < 0 else hp)
            top_l = [(x + side * (6 + 9 * rnd(s, i, 21)), y - 10 - 16 * rnd(s, i, 22) ** 2) for i, (x, y) in enumerate(pts)]
            bot_l = [(x - side * (10 + 12 * rnd(s, i, 23)), y + 8) for i, (x, y) in enumerate(pts)]
            snow.append(_orient(top_l + bot_l[::-1]))
        # snow lying on the roof face when mended (the old steep thatch has shed its snow)
        if not old:
            sheet = [(x, y + 22) for (x, y) in ridge]
            for (x, y) in hipR[::-1][::-1]:
                sheet.append((x - 34, y + 30))
            ye = lambda x: eave_y(min(max(x - lean, x0), x1))
            for i in range(21):
                x = lerp(eR[0] - 110, eL[0] + 110, i / 20)
                sheet.append((x, ye(x) - 70 - 34 * rnd(s, i, 23) ** 2 + 10 * math.sin(i * 1.7)))
            for (x, y) in hipL[::-1]:
                sheet.append((x + 34, y + 30))
            snow.append(_orient(sheet))
        # the eave lip and icicles
        lip_t, lip_b = [], []
        for i in range(m + 1):
            x = lerp(eL[0] + 10, eR[0] - 10, i / m)
            ye = eave_y(min(max(x - lean, x0), x1))
            lip_t.append((x, ye - 8 - 14 * rnd(s, i, 25) ** 2))
            lip_b.append((x, ye + 22 + 14 * rnd(s, i, 26) ** 3))
        snow.append(_orient(lip_t + lip_b[::-1]))
        for k in range(16 if old else 7):
            x = lerp(eL[0] + 40, eR[0] - 40, rnd(s, k, 27))
            y = eave_y(min(max(x - lean, x0), x1)) + 34
            L = (30 + (110 if old else 50) * rnd(s, k, 28) ** 2)
            snow.append(_orient([(x - 5, y), (x + 5, y), (x + 1, y + L)]))
        # ---------------------------------------------------------------- door
        dw, dh = 300.0, 610.0
        door = (dx - dw / 2, gd, dx + dw / 2, gd - dh)
        body.append(_orient([(dx - dw / 2 - 46, gd - dh - 6), (dx + dw / 2 + 46, gd - dh - 12),
                             (dx + dw / 2 + 46, gd - dh - 44), (dx - dw / 2 - 46, gd - dh - 40)]))     # lintel
        if old:
            holes.append([(door[0], gd + 20), (door[0], door[3]), (door[2], door[3]), (door[2], gd + 20)])
            # the door hangs open outward on its top hinge, its foot dragged in the snow
            hx, hy = door[0], door[3] + 30
            leaf.append(_orient([(hx, hy), (hx - 118, hy + 44), (hx - 142, gd + 6), (hx - 22, gd - 18)]))
            for k in range(1, 4):
                u = k / 4
                seams.append([(lerp(hx, hx - 118, u), lerp(hy, hy + 44, u) + 4), (lerp(hx - 22, hx - 142, u), lerp(gd - 18, gd + 6, u) - 4)])
        else:
            leaf.append([(door[0], gd + 20), (door[0], door[3]), (door[2], door[3]), (door[2], gd + 20)])
            for k in range(1, 5):
                xx = lerp(door[0], door[2], k / 5)
                seams.append([(xx, door[3] + 8), (xx, gd - 4)])
            seams.append([(door[0] + 10, gd - 140), (door[2] - 10, gd - 140)])
            seams.append([(door[0] + 10, door[3] + 130), (door[2] - 10, door[3] + 130)])
        # step stone
        stp = [(dx - 215, gd + 30), (dx - 205, gd - 28), (dx - 60, gd - 36), (dx + 190, gd - 32), (dx + 220, gd + 30)]
        ink.append(_orient(stp))
        snow.append(_orient([(dx - 222, gd - 22), (dx - 120, gd - 46), (dx + 60, gd - 50), (dx + 228, gd - 26),
                             (dx + 190, gd - 20), (dx - 200, gd - 16)]))
        # ---------------------------------------------------------------- window
        wx, wy, ww, wh = self.window_x + lean * 0.55, gd - 390.0, 230.0, 250.0
        win = [(wx - ww / 2, wy - wh / 2), (wx + ww / 2, wy - wh / 2), (wx + ww / 2, wy + wh / 2), (wx - ww / 2, wy + wh / 2)]
        b = 15.0
        if old:
            holes.append(win)
            body.append(_orient([(wx - b / 2, wy - wh / 2), (wx + b / 2, wy - wh / 2), (wx + b / 2, wy + wh / 2), (wx - b / 2, wy + wh / 2)]))
            body.append(_orient([(wx - ww / 2, wy - b / 2), (wx - 24, wy - b / 2 - 4), (wx - 40, wy + b / 2 + 6), (wx - ww / 2, wy + b / 2)]))
            for (cx, cy, sx, sy) in ((-1, -1, 1, 1), (1, -1, -1, 1), (1, 1, -1, -1), (-1, 1, 1, -1)):
                px, py = wx + cx * (ww / 2 - 8), wy + cy * (wh / 2 - 8)
                k1, k2 = 26 + 30 * rnd(s, cx, cy, 30), 30 + 40 * rnd(s, cx, cy, 31)
                glass.append([(px, py), (px + sx * k1, py), (px + sx * k1 * 0.3, py + sy * k2 * 0.35),
                              (px + sx * 6, py + sy * k2 * 0.5), (px, py + sy * k2)])
            # left shutter hangs from its top hinge, swung out of true
            hx, hy = wx - ww / 2 - 6, wy - wh / 2 + 8
            a = math.radians(-24.0)
            sh = [(0, 0), (-112, 0), (-112, 250), (0, 250)]
            shp = [(hx + p[0] * math.cos(a) - p[1] * math.sin(a), hy + p[0] * math.sin(a) + p[1] * math.cos(a)) for p in sh]
            leaf.append(_orient(shp))
            for k in (1, 2):
                q = [(-112 * k / 3, 6), (-112 * k / 3, 244)]
                seams.append([(hx + p[0] * math.cos(a) - p[1] * math.sin(a), hy + p[0] * math.sin(a) + p[1] * math.cos(a)) for p in q])
        else:
            lit.append(win)
            curtains.append(_orient([(wx - ww / 2, wy - wh / 2), (wx - ww / 2 + 62, wy - wh / 2), (wx - ww / 2 + 34, wy + 10),
                                     (wx - ww / 2 + 50, wy + wh / 2), (wx - ww / 2, wy + wh / 2)]))
            curtains.append(_orient([(wx + ww / 2, wy - wh / 2), (wx + ww / 2 - 62, wy - wh / 2), (wx + ww / 2 - 34, wy + 10),
                                     (wx + ww / 2 - 50, wy + wh / 2), (wx + ww / 2, wy + wh / 2)]))
            curtains.append([(wx - b / 2, wy - wh / 2), (wx + b / 2, wy - wh / 2), (wx + b / 2, wy + wh / 2), (wx - b / 2, wy + wh / 2)])
            curtains.append([(wx - ww / 2, wy - b / 2), (wx + ww / 2, wy - b / 2), (wx + ww / 2, wy + b / 2), (wx - ww / 2, wy + b / 2)])
            for side in (-1, 1):
                sx0 = wx + side * (ww / 2 + 8)
                leaf.append(_orient([(sx0, wy - wh / 2), (sx0 + side * 112, wy - wh / 2), (sx0 + side * 112, wy + wh / 2), (sx0, wy + wh / 2)]))
                seams.append([(sx0 + side * 56, wy - wh / 2 + 8), (sx0 + side * 56, wy + wh / 2 - 8)])
        body.append(_orient([(wx - ww / 2 - 22, wy + wh / 2), (wx + ww / 2 + 22, wy + wh / 2), (wx + ww / 2 + 22, wy + wh / 2 + 20),
                             (wx - ww / 2 - 22, wy + wh / 2 + 20)]))
        snow.append(_orient([(wx - ww / 2 - 28, wy + wh / 2 + 2), (wx - 30, wy + wh / 2 - 22), (wx + ww / 2 + 28, wy + wh / 2 - 6),
                             (wx + ww / 2 + 22, wy + wh / 2 + 6), (wx - ww / 2 - 22, wy + wh / 2 + 8)]))
        # ---------------------------------------------------------------- yard: wheel / woodpile / fence
        if old:
            cx, r = x0 - 110, 150.0
            cy = G(cx) - r + 18
            ring = [(cx + math.cos(2 * math.pi * i / 40) * r, cy + math.sin(2 * math.pi * i / 40) * r * 0.97) for i in range(40)]
            inner = [(cx + math.cos(2 * math.pi * i / 40) * (r - 20), cy + math.sin(2 * math.pi * i / 40) * (r - 20)) for i in range(40)]
            ink.append(_orient(ring))
            ink.append(_orient(inner)[::-1])          # opposite winding: the hole in the rim
            wheel_spokes = []
            for k in range(8):
                if k == 3:
                    continue
                th = 2 * math.pi * k / 8 + 0.2
                wheel_spokes.append(_taper_limb([(cx, cy), (cx + math.cos(th) * (r - 12), cy + math.sin(th) * (r - 12))], 6, 5))
            wheel_spokes.append(_orient([(cx + math.cos(t_) * 28, cy + math.sin(t_) * 28) for t_ in np.linspace(0, 6.28, 16)]))
            snow.append(_orient([(cx - 60, cy - r + 6), (cx, cy - r - 14), (cx + 70, cy - r + 8), (cx, cy - r + 14)]))
            logs = []
            for k in range(6):
                lx0 = x1 + 70 + 70 * k + 30 * srnd(s, k, 40)
                ang = 18 * srnd(s, k, 41)
                L = 160 + 60 * rnd(s, k, 42)
                p0 = (lx0, G(lx0) - 18)
                p1 = (lx0 + math.cos(math.radians(ang)) * L, G(lx0) - 18 + math.sin(math.radians(ang)) * L * 0.3)
                logs.append(_taper_limb([p0, p1], 22, 20))
                snow.append(_orient([(p0[0] + 10, p0[1] - 20), (p1[0] - 10, p1[1] - 22), (p1[0] - 14, p1[1] - 14), (p0[0] + 14, p0[1] - 12)]))
            ink.extend(logs)
            fence = []
            for k in range(4):
                fx = x1 + 700 + 210 * k
                tl = (-14 if k % 2 else 10) + 6 * srnd(s, k, 43)
                fy = G(fx)
                top = (fx + math.sin(math.radians(tl)) * 300, fy - math.cos(math.radians(tl)) * 300)
                fence.append(_taper_limb([(fx, fy + 30), top], 13, 11))
                snow.append(_orient([(top[0] - 16, top[1] + 4), (top[0], top[1] - 14), (top[0] + 16, top[1] + 4)]))
            fence.append(_taper_limb([(x1 + 700, G(x1 + 700) - 200), (x1 + 900, G(x1 + 900) - 120)], 9, 8))
            fence.append(_taper_limb([(x1 + 1120, G(x1 + 1120) - 210), (x1 + 1250, G(x1 + 1250) - 60)], 9, 8))
            ink.extend(fence)
        else:
            wheel_spokes = []
            pile = []
            r = 30.0
            for row in range(5):
                for k in range(7 - (row % 2)):
                    px = x1 + 90 + r + k * 2 * r + (r if row % 2 else 0)
                    py = G(x1 + 300) - r - row * 1.75 * r
                    pile.append(_orient([(px + math.cos(2 * math.pi * i / 10) * r, py + math.sin(2 * math.pi * i / 10) * r) for i in range(10)]))
            ink.extend(pile)
            ptop = G(x1 + 300) - 5 * 1.75 * r - 2 * r
            snow.append(_orient([(x1 + 80, ptop + 26), (x1 + 200, ptop - 12), (x1 + 420, ptop - 8), (x1 + 540, ptop + 30),
                                 (x1 + 520, ptop + 40), (x1 + 100, ptop + 40)]))
            bx = x1 + 700
            ink.append(_orient([(bx - 60, G(bx) + 20), (bx - 60, G(bx) - 110), (bx + 60, G(bx) - 116), (bx + 60, G(bx) + 20)]))
            ink.append(_taper_limb([(bx - 10, G(bx) - 110), (bx + 90, G(bx) - 330)], 7, 6))
            ink.append(_orient([(bx + 70, G(bx) - 345), (bx + 128, G(bx) - 318), (bx + 118, G(bx) - 296), (bx + 76, G(bx) - 312)]))
            snow.append(_orient([(bx - 66, G(bx) - 106), (bx, G(bx) - 128), (bx + 66, G(bx) - 112), (bx + 60, G(bx) - 104), (bx - 60, G(bx) - 100)]))
            for k in range(6):
                fx = x1 + 1000 + 190 * k
                fy = G(fx)
                ink.append(_taper_limb([(fx, fy + 30), (fx, fy - 280)], 12, 11))
                snow.append(_orient([(fx - 16, fy - 276), (fx, fy - 296), (fx + 16, fy - 276)]))
            for hh in (110, 220):
                ink.append(_taper_limb([(x1 + 990, G(x1 + 990) - hh), (x1 + 1960, G(x1 + 1960) - hh)], 8, 8))
        # ---------------------------------------------------------------- drifts against the walls
        ground_snow = []
        for side in (-1, 1):
            bx = x0 if side < 0 else x1
            dw = 260 + 120 * rnd(s, 50 + side)
            dh = 70 + 50 * rnd(s, 51 + side)
            pts = []
            for i in range(10):
                u = i / 9
                xx = bx - side * 40 + side * dw * u
                pts.append((xx, G(xx) - dh * (1 - u) ** 1.6 - 6 * math.sin(u * 9 + side)))
            pts += [(bx + side * dw, G(bx + side * dw) + 24), (bx - side * 40, G(bx) + 24)]
            ground_snow.append(_orient(pts))
        front = []
        for i in range(25):
            xx = lerp(x0 - 40, x1 + 40, i / 24)
            if door[0] - 30 < xx < door[2] + 30:
                hgt = 4.0
            else:
                hgt = 30 + 26 * rnd(s, i, 52)
            front.append((xx, G(xx) - hgt))
        front += [(x1 + 40, G(x1) + 24), (x0 - 40, G(x0) + 24)]
        ground_snow.append(_orient(front))

        eave_pts = [(x, eave_y(min(max(x - lean, x0), x1)) + 40) for x in np.linspace(eL[0], eR[0], 14)]
        anchors = dict(
            door=door, window=(wx, wy, ww, wh), chimney=chim_top, ridge=ridge, eave=eave_pts, eave_l=eL, eave_r=eR,
            corner_l=(lx(x0, H), eave_y(x0)), corner_r=(lx(x1, H), eave_y(x1)), hip_l=[eL] + hipL + [ridge[0]],
            hip_r=[ridge[-1]] + hipR + [eR], step=(dx, gd - 34), lantern_hook=(dx - 250, gd - 470),
            notch=notch, lean=lean, base=base, gd=gd,
        )
        return dict(body=body, roof=roof, ink=ink, holes=holes, snow=snow, glass=glass, seams=seams, lit=lit, leaf=leaf,
                    curtains=curtains, wheel_spokes=wheel_spokes, ground_snow=ground_snow,
                    anchors=anchors, outline=self._outline_fn(lx, eave_y, eL, eR, hipL, hipR, ridge, x0, x1, H, gd))

    @staticmethod
    def _outline_fn(lx, eave_y, eL, eR, hipL, hipR, ridge, x0, x1, H, gd):
        """(x_left, x_right) of the house silhouette at height y (for wrapping strands)."""
        hl = [eL] + hipL + [ridge[0]]
        hr = [ridge[-1]] + hipR + [eR]

        def at(y):
            if y >= eave_y(x0) + 30:
                h = clamp(gd - y, 0, H)
                return lx(x0, h) - 10, lx(x1, h) + 10
            yl = np.interp(y, [p[1] for p in hl][::-1], [p[0] for p in hl][::-1])
            yr = np.interp(y, [p[1] for p in hr], [p[0] for p in hr])
            return float(yl), float(yr)
        return at

    # ------------------------------------------------------------ draw
    def colors(self, mood, tint=0.0):
        mood = get_mood(mood)
        lift = 0.19 - 0.05 * mood.night
        ink = fogged(mood, tint) if tint > 0 else mood.ink
        fog = mood.fog_at(0.35)
        return dict(ink=ink, body=mix(ink, fog, lift), roof=mix(ink, fog, lift * 0.75), leaf=mix(ink, fog, lift * 1.7),
                    snow=fogged(mood, tint, mood.snow) if tint > 0 else mood.snow,
                    glass=mix(mood.fog_at(0.1), SNOW, 0.4))

    def draw(self, f, c, mood=None, state="old", t=0.0, window_light=None, door_light=None, tint=0.0, detail=True):
        """Draw the cottage on context c (plane coords). window_light / door_light 0..1 (default:
        lit at dusk/night in the "new" state). Call draw_lights() for the glow and spill."""
        mood = get_mood(mood)
        g = self.geometry(state)
        C = self.colors(mood, tint)
        zoom = f.lcam(1.0).zoom if f is not None else 1.0
        _fill(c, g["ink"][:5] if state == "old" else [], C["ink"])        # rafters behind the roof
        _fill(c, g["roof"], C["roof"])
        _fill(c, g["body"], C["body"])
        if detail and zoom > 0.22:
            for pts in g["seams"]:
                c.move_to(*pts[0])
                for q in pts[1:]:
                    c.line_to(*q)
            draw.stroke(c, C["ink"], max(2.6, 1.1 / max(zoom, 0.1)), a=0.75)
        _fill(c, g["holes"], C["ink"])
        if g["glass"]:
            _fill(c, g["glass"], C["glass"], 0.5)
        wl = self._window_light(mood, state, window_light)
        if g["lit"]:
            if wl > 0.01:
                hot = mix(mix(INK, mood.lamp, 0.85), mix(mood.lamp, SNOW, 0.12), 0.35 + 0.3 * flick(t, 41, rate=2.0, depth=0.2))
                _fill(c, g["lit"], mix(C["ink"], hot, clamp(wl)))
            else:
                _fill(c, g["lit"], mix(C["ink"], mood.fog_at(0.5), 0.12))
        _fill(c, g["curtains"], C["ink"])
        _fill(c, g["leaf"], C["leaf"] if state == "old" else C["body"])
        dl = self._door_light(mood, state, door_light)
        if state == "new" and dl > 0.01:
            d0, gy, d1, d3 = g["anchors"]["door"]
            col = mix(mood.lamp, SNOW, 0.3)
            c.move_to(d0 + 3, d3 + 4)
            c.line_to(d0 + 3, gy - 2)
            c.move_to(d1 - 3, d3 + 4)
            c.line_to(d1 - 3, gy - 2)
            draw.stroke(c, col, 3.0, a=0.8 * dl)
            c.move_to(d0 + 4, gy - 3)
            c.line_to(d1 - 4, gy - 3)
            draw.stroke(c, col, 5.0, a=0.9 * dl)
        _fill(c, g["ink"][5:] if state == "old" else g["ink"], C["ink"])
        if g["wheel_spokes"]:
            _fill(c, g["wheel_spokes"], C["ink"])
        _fill(c, g["snow"], C["snow"])

    def draw_ground_snow(self, c, mood=None, state="old"):
        """Drifts against the walls (after the terrain's draw_back, before characters)."""
        mood = get_mood(mood)
        _fill(c, self.geometry(state)["ground_snow"], mood.snow)

    def _window_light(self, mood, state, wl):
        if wl is not None:
            return wl
        return (0.35 + 0.65 * clamp(mood.night / 0.6)) if state == "new" else 0.0

    def _door_light(self, mood, state, dl):
        if dl is not None:
            return dl
        return clamp(mood.night / 0.6) if state == "new" else 0.0

    def draw_lights(self, f, mood=None, state="new", t=0.0, window_light=None, door_light=None):
        """Window glow (emissive) and the light falling on the snow (call after the snow lip)."""
        mood = get_mood(mood)
        wl = self._window_light(mood, state, window_light)
        dl = self._door_light(mood, state, door_light)
        if wl <= 0.01 and dl <= 0.01:
            return
        A = self.anchors(state)
        wx, wy, ww, wh = A["window"]
        gain = mood.lamp_gain * flick(t, 43, rate=2.0, depth=0.15)
        if wl > 0.01:
            with f.emit() as G:
                glow(G, (wx, wy), 260, mood.lamp, 0.22 * wl * gain)
        with soft_layer(f, 1.0, k=6, op="add", blur=30.0) as L:
            if wl > 0.01:
                glow(L, (wx, wy), 520, mood.lamp, 0.16 * wl * gain)
                light_pool(L, (wx + 40, float(self.T.snow_y(wx)) + 40), 520, 110, mood.lamp, 0.28 * wl * gain)
            if dl > 0.01:
                dx, gy = self.threshold
                light_pool(L, (dx, gy + 20), 260, 50, mood.lamp, 0.35 * dl * gain)

    def smoke(self, f, mood=None, t=0.0, wind=40.0, amount=1.0):
        """Chimney smoke (state "new"): soft puffs rising, leaning with the wind."""
        mood = get_mood(mood)
        cx, cy = self.anchors("new")["chimney"]
        col = mix(mood.fog_at(1.0), SNOW, 0.25) if mood.night > 0.5 else mix(mood.fog_at(0.7), SNOW, 0.3)
        with soft_layer(f, 1.0, k=4, blur=12.0) as S:
            life = 7.0
            for i in range(18):
                ph = (t / life + i / 18 + rnd(7, i, 1) * 0.02) % 1.0
                age = ph * life
                x = cx + wind * age * (0.4 + 0.15 * age) + 18 * math.sin(age * 0.9 + i) * clamp(age / 2)
                y = cy - 110 * age
                r = 26 + 20 * age
                a = 0.32 * amount * math.sin(math.pi * clamp(ph * 1.15)) ** 0.8
                draw.circle(S, (x, y), r)
                draw.fill(S, col, a)


# ============================================================================ trees with crowns
def _crown_tree(x, G, w, seed, crown=(1150.0, 1800.0), reach=950.0, n_limbs=6, sc=1.0, snow=True, levels=2,
                height=None):
    """An old broad tree whose bare crown makes the canopy: a straight forest trunk, limbs from
    the crown base that fork (recursively, `levels` deep) into branches and twigs. Returns the
    forest tree dict plus forks=[(x, y)], tips=[(x, y)] (web anchors) and
    hang=[(x, y, angle)] (points under the branches where hoods hang)."""
    base_y = float(G(x))
    tr = _make_tree(dict(name="plane", branch=0.0), x, base_y, w, seed, ground=G, height=height)
    limbs, snows, forks, tips, hang = [], [], [], [], []

    def branch(p0, ang, length, r0, level, sd):
        pts = _curve(p0, ang, length, srnd(sd, 1) * 16, n=6, droop=length * (0.03 + 0.05 * level))
        limbs.append(_taper_limb(pts, r0, max(0.7, r0 * 0.35)))
        tips.append(pts[-1])
        if 28 < abs(ang) < 120:
            for i in (2, 3, 4):
                hang.append((pts[i][0], pts[i][1] + r0 * 0.5, ang))
        if snow and level < 2 and r0 > 3.5 and rnd(sd, 2) < 0.65:
            dp = _resample_line(pts, 12)
            dr = [lerp(r0, r0 * 0.35, (i / 11) ** 0.9) for i in range(12)]
            sn = _snow_on_limb(dp, dr, max(2.0, r0 * 0.22), sd, u0=0.15 + 0.2 * rnd(sd, 3), u1=0.5 + 0.3 * rnd(sd, 4))
            if sn:
                snows.append(sn)
        if level >= levels:
            for k in range(1 + int(rnd(sd, 5) < 0.5)):
                q = pts[3 + k]
                tang = ang + (-1 if k % 2 else 1) * (25 + 30 * rnd(sd, 6 + k))
                limbs.append(_taper_limb(_curve(q, tang, length * (0.25 + 0.2 * rnd(sd, 8 + k)), srnd(sd, 9) * 10, n=4),
                                         max(0.7, r0 * 0.3), 0.5))
            return
        nk = 2 + int(rnd(sd, 10) < 0.45)
        for k in range(nk):
            u = 0.3 + 0.55 * (k + rnd(sd, 11 + k)) / nk
            q = pts[min(4, int(u * 5))]
            forks.append(q)
            cang = ang + (-1 if (k + level) % 2 else 1) * (16 + 24 * rnd(sd, 20 + k))
            cang = max(-105.0, min(105.0, cang))
            branch(q, cang, length * (0.5 + 0.2 * rnd(sd, 30 + k)), r0 * (0.6 - 0.12 * u), level + 1, sd * 7 + k + 1)

    for b in range(n_limbs):
        hb = lerp(crown[0], crown[1], (b + rnd(seed, 500 + b)) / n_limbs) * sc
        side = -1 if (b + int(2 * rnd(seed, 501))) % 2 else 1
        ang = side * (22 + 36 * rnd(seed, 510 + b))
        length = reach * (0.5 + 0.35 * rnd(seed, 520 + b)) * sc
        r0 = w * (0.22 + 0.07 * rnd(seed, 530 + b))
        p0 = (x + side * w * 0.12, base_y - hb)
        forks.append(p0)
        branch(p0, ang, length, r0, 0, seed * 31 + b)
    tr["limbs"] = tr["limbs"] + limbs
    tr["snow"] = tr["snow"] + snows
    tr.update(forks=forks, tips=tips, hang=hang)
    return tr


# ============================================================================ hoods
_FALL_CACHE = {}


def hood_fall(t, t0, start, ground, size=100.0, seed=0, wind=26.0):
    """A released hood falls like a leaf from `start` (its peak at release time t0) onto
    ground(x) (a snow-surface function). Returns (x, y, angle, crumple) for hood_poly /
    draw_hood: drifting pendulum flutter at a slow terminal speed, then it lands and slumps
    into a heap (crumple 0 -> 1, anchor moving to the heap's center on the snow)."""
    a = t - t0
    if a <= 0:
        return start[0], start[1], 0.0, 0.0
    k = size / 100.0
    vt = (360.0 + 170.0 * rnd(seed, 1)) * k ** 0.5
    tau = 0.45
    fq = 0.55 + 0.35 * rnd(seed, 2)
    A = (40.0 + 60.0 * rnd(seed, 3)) * k
    ph = 6.283 * rnd(seed, 4)
    dr = wind * (0.4 + rnd(seed, 5))

    def pos(tt):
        y = start[1] + vt * (tt - tau * (1.0 - math.exp(-tt / tau)))
        env = 1.0 - math.exp(-tt / 0.7)
        x = start[0] + A * env * math.sin(6.283 * fq * tt + ph) - A * env * math.sin(ph) + dr * tt
        return x, y

    key = (seed, round(t0, 4), round(start[0], 2), round(start[1], 2), id(ground), size)
    land = _FALL_CACHE.get(key)
    if land is None:
        tt, dt = 0.0, 1.0 / 60.0
        land = (1e9, 0.0, 0.0)
        while tt < 30.0:
            x, y = pos(tt)
            if y + 0.62 * size >= float(ground(x)):
                land = (tt, x, y)
                break
            tt += dt
        if len(_FALL_CACHE) > 20000:
            _FALL_CACHE.clear()
        _FALL_CACHE[key] = land
    ta, lx_, ly_ = land
    if a < ta:
        x, y = pos(a)
        env = 1.0 - math.exp(-a / 0.7)
        ang = 22.0 * env * math.cos(6.283 * fq * a + ph)
        return x, y, ang, 0.12 * env
    u = clamp((a - ta) / 0.35)
    u = u * u * (3 - 2 * u)
    gy = float(ground(lx_)) + 3.0
    return lx_, lerp(ly_, gy, u), 0.0, lerp(0.12, 1.0, u)


class Hoods:
    """The red hoods hanging in the trees and from the web. Each hood is a dict:
        id, layer ("plane", "web", or a forest layer name), anchor (x, y) in that layer's
        coords, thread (px), size (peak to hem, px), seed, ground (fn: where it lands),
        strand (web strand id it hangs from, or None).
    pose(h, t, t_rel) -> (x, y, angle, crumple); draw(c, t, group, mood, release, burn)."""

    def __init__(self):
        self.items = []
        self.groups = {}

    def add(self, layer, anchor, thread, size, seed, ground, strand=None, amp=5.0):
        h = dict(id=len(self.items), layer=layer, anchor=anchor, thread=thread, size=size, seed=seed,
                 ground=ground, strand=strand, amp=amp)
        self.items.append(h)
        self.groups.setdefault(layer, []).append(h)
        return h

    def release_time(self, h, release=None, burn=None, spread=2.0):
        """When hood h falls: release may be None (never), a float t0 (all hoods fall over
        [t0, t0 + spread], staggered), a dict id -> t, or a callable(h) -> t | None. With a
        burn, hoods hanging from web threads fall when their thread burns through."""
        if burn is not None and h["strand"] is not None:
            tr = burn.release_time(h["strand"])
            if math.isfinite(tr):
                return tr
        if release is None:
            return None
        if isinstance(release, dict):
            return release.get(h["id"])
        if callable(release):
            return release(h)
        return float(release) + spread * rnd(h["seed"], 77) ** 0.9

    def pose(self, h, t, t_rel=None):
        ax, ay = h["anchor"]
        L = h["thread"]

        def hang(tt):
            a = hood_sway(tt, h["seed"], amp=h["amp"])
            r = math.radians(a)
            return (ax - math.sin(r) * L, ay + math.cos(r) * L), a

        if t_rel is None or t < t_rel:
            p, a = hang(t)
            return p[0], p[1], a, 0.0
        p0, a0 = hang(t_rel)
        return hood_fall(t, t_rel, p0, h["ground"], h["size"], h["seed"])

    def draw(self, c, t, items, mood=None, release=None, burn=None, color=None, ink=None, threads=True, alpha=1.0):
        """Fill a group of hoods (one fill) and stroke their threads."""
        mood = get_mood(mood)
        col = color or HOOD_RED
        ink = ink or mood.ink
        polys = []
        lines = []
        for h in items:
            tr = self.release_time(h, release, burn)
            x, y, ang, cr = self.pose(h, t, tr)
            polys.append(hood_poly((x, y), h["size"], ang, cr, h["seed"]))
            if threads and h["strand"] is None:          # web hoods hang on silk (drawn by the web)
                ax, ay = h["anchor"]
                if tr is None or t < tr:
                    lines.append(((ax, ay), (x, y)))
                else:
                    lines.append(((ax, ay), (ax + 3 * math.sin(t + h["seed"]), ay + h["thread"] * 0.8)))
        if threads and lines:
            for a, b in lines:
                c.move_to(*a)
                c.line_to(*b)
            draw.stroke(c, ink, 2.0, a=0.9 * alpha)
        for p in polys:
            draw.smooth(c, p, close=True, tension=0.35)
        draw.fill(c, col, alpha)

    def positions(self, t, layer=None, release=None, burn=None):
        """[(id, layer, x, y)] of hood peaks at t (layer coords)."""
        out = []
        for h in (self.groups.get(layer, []) if layer else self.items):
            x, y, a, cr = self.pose(h, t, self.release_time(h, release, burn))
            out.append((h["id"], h["layer"], x, y))
        return out


# ============================================================================ the lantern path (S11)
class LanternPath:
    """S11: a new path of lanterns on crooked posts, climbing from the forest to the cottage
    door. Posts on the action plane along the approach (x0 .. x_last, CLEARING), the last one
    by the door; beyond, the line continues as far lights down through the forest layers
    (the "line of light through the dark trees" when the camera cranes up).

    lit: 1.0 (all lit), a float 0..1, a callable(i, t) -> 0..1, or dict(last=t_lit) to have
    the last lantern (by the door) light up at t_lit (Old Red lights it)."""

    def __init__(self, terrain=CLEARING, x0=-4200.0, x_last=-270.0, n=10, seed=5, size=1.9):
        self.T = terrain
        self.seed = seed
        self.lantern = Lantern(size)
        self.posts = []
        for i in range(n):
            u = i / (n - 1)
            x = lerp(x0, x_last, u) + (0 if i == n - 1 else 60 * srnd(seed, i, 1))
            self.posts.append(dict(x=x, h=420.0 + 40 * rnd(seed, i, 2), tilt=3.0 * srnd(seed, i, 3)))
        self.far = {}

    def lit_amount(self, i, t, lit=1.0):
        if callable(lit):
            return clamp(lit(i, t))
        if isinstance(lit, dict):
            if i == len(self.posts) - 1 and "last" in lit:
                return clamp((t - lit["last"]) / 0.35)
            return 1.0
        return clamp(lit)

    def _post(self, p):
        x = p["x"]
        gy = float(self.T.snow_y(x))
        h = p["h"]
        a = math.radians(p["tilt"])
        top = (x + math.sin(a) * h, gy - math.cos(a) * h)
        crook = _curve(top, 25.0, 120.0, 150.0, n=6)
        hook = crook[-1]
        ink = [_taper_limb([(x, gy + 40), top], 12, 9), _taper_limb(crook, 6, 4)]
        snow = [_orient([(top[0] - 13, top[1] + 4), (top[0] - 2, top[1] - 12), (top[0] + 12, top[1] + 2)])]
        return ink, snow, hook

    def flames(self, t=0.0):
        """World positions of the plane lanterns' flames."""
        out = []
        for i, p in enumerate(self.posts):
            ink, snow, hook = self._post(p)
            g = self.lantern.geometry(hook, 3.0 * math.sin(t * 0.8 + i))
            out.append(g["flame"])
        return out

    def draw(self, f, c, mood=None, t=0.0, lit=1.0):
        """Posts and lanterns on the plane (context c). Returns the flame positions."""
        mood = get_mood(mood)
        vx0, vy0, vx1, vy1 = view(f, 1.0, 600)
        out = []
        inks, snows = [], []
        for i, p in enumerate(self.posts):
            if not (vx0 < p["x"] < vx1):
                continue
            ink, snow, hook = self._post(p)
            inks += ink
            snows += snow
            out.append((i, hook))
        _fill(c, inks, mood.ink)
        _fill(c, snows, mood.snow)
        flames = []
        for i, hook in out:
            fl = self.lit_amount(i, t, lit)
            pos = self.lantern.draw(f, c, hook, 3.0 * math.sin(t * 0.8 + i), lit=fl, t=t, mood=mood, seed=i + 3)
            flames.append((i, pos, fl))
        return flames

    def ground_lights(self, f, mood=None, t=0.0, lit=1.0):
        """Warm pools on the snow and a soft room-light around each lantern (after the lip)."""
        mood = get_mood(mood)
        vx0, vy0, vx1, vy1 = view(f, 1.0, 900)
        with soft_layer(f, 1.0, k=6, op="add", blur=30.0) as A:
            for i, p in enumerate(self.posts):
                if not (vx0 < p["x"] < vx1):
                    continue
                fl = self.lit_amount(i, t, lit) * flick(t, i + 11)
                if fl <= 0.01:
                    continue
                ink, snow, hook = self._post(p)
                gain = mood.lamp_gain * fl
                light_pool(A, (hook[0], float(self.T.snow_y(hook[0])) + 30), 460, 120, mood.lamp, 0.48 * gain)
                glow(A, (hook[0], hook[1] + 85), 520, mood.lamp, 0.16 * gain)

    def far_lights(self, f, L, mood=None, t=0.0, tint=None):
        """The path's continuation as small lights in forest layer L (winding away into the
        valley). Lantern silhouettes are drawn in the layer's colors, the glow is additive and
        occludable (composited now, so nearer layers drawn later cover it)."""
        mood = get_mood(mood)
        name = L["name"]
        if name not in ("near", "mid", "far"):
            return
        key = name
        if key not in self.far:
            # the path winds back and forth through the forest behind the clearing and away
            # down the valley: a few lights in each layer, farther layers farther left
            par = L["par"]
            pts = []
            span = {"near": (-2300.0, -300.0, 5), "mid": (-3600.0, -900.0, 6), "far": (-5600.0, -1800.0, 7)}[name]
            for k in range(span[2]):
                xw = lerp(span[0], span[1], k / (span[2] - 1)) + 160 * srnd(self.seed, len(name), k, 9)
                xl = 540.0 + (xw - 540.0) * par
                pts.append((xl, float(L["g"](xl))))
            self.far[key] = pts
        pts = self.far[key]
        par = L["par"]
        sc = {"near": 0.7, "mid": 0.5, "far": 0.34}[name]
        tint = L["depth"] if tint is None else tint
        vx0, vy0, vx1, vy1 = view(f, par, 400)
        vis = [p for p in pts if vx0 < p[0] < vx1]
        if not vis:
            return
        ink = fogged(mood, tint)
        with plane(f, par) as c:
            polys = []
            for (x, gy) in vis:
                polys.append(_taper_limb([(x, gy + 20), (x, gy - 420 * sc)], 9 * sc, 7 * sc))
                polys.append(_taper_limb(_curve((x, gy - 420 * sc), 25.0, 120 * sc, 150.0, n=5), 5 * sc, 3 * sc))
            _fill(c, polys, ink)
            hot = mix(mix(mood.lamp, SNOW, 0.45), mood.fog_at(tint), tint * 0.4)
            for (x, gy) in vis:
                draw.circle(c, (x + 70 * sc, gy - 340 * sc), 13 * sc)
            draw.fill(c, hot)
        with soft_layer(f, par, k=4, op="add", blur=12.0) as A:
            for i, (x, gy) in enumerate(vis):
                g = mood.lamp_gain * flick(t, 50 + i) * (1 - 0.45 * tint)
                glow(A, (x + 70 * sc, gy - 340 * sc), 300 * sc, mood.lamp, 0.55 * g)
                light_pool(A, (x + 60 * sc, gy + 10), 330 * sc, 60 * sc, mood.lamp, 0.35 * g)


# ============================================================================ the clearing
CLEARING_LAYERS = [
    dict(LAYERS[0]),
    dict(LAYERS[1], dens=0.8),
    dict(LAYERS[2], dens=0.66),
    dict(LAYERS[3], dens=0.5),
]

# plane trees: (x, trunk width, crown base, crown top, reach, limbs)
PLANE_TREES = [
    (1990.0, 118.0, 1250.0, 1900.0, 1000.0, 6),
    (2640.0, 140.0, 1150.0, 1850.0, 1150.0, 7),
    (3380.0, 128.0, 1250.0, 1950.0, 1000.0, 6),
    (4150.0, 150.0, 1200.0, 1900.0, 1100.0, 6),
    (-1480.0, 112.0, 1150.0, 1700.0, 900.0, 6),
    (-2460.0, 126.0, 1100.0, 1700.0, 950.0, 6),
    (-3560.0, 118.0, 1150.0, 1750.0, 900.0, 5),
    (-4700.0, 132.0, 1200.0, 1800.0, 950.0, 5),
]

# hood trees in the forest layers: world x positions (converted to layer x)
HOOD_TREES = {
    "near": [-2950.0, -1950.0, 850.0, 1500.0, 2300.0, 3150.0],
    "mid": [-3700.0, -2500.0, -1250.0, 50.0, 1150.0, 2250.0, 3350.0, 4300.0],
    "far": [-4200.0, -2100.0, 0.0, 2000.0, 4100.0, 6100.0],
}


class _ClearingForest(Forest):
    """The forest around the clearing: thinner behind the cottage."""

    def density(self, xw):
        return 1.0 - 0.7 * math.exp(-((xw - 250.0) / 1500.0) ** 2)


class Clearing:
    """The cottage clearing set. See the module docstring for the draw order and eras."""

    def __init__(self, terrain=CLEARING, seed=17):
        self.T = terrain
        self.seed = seed
        self.cottage = Cottage(terrain, door_x=0.0)
        self.forest = _ClearingForest(terrain=terrain, seed=seed, markers=None, layers=CLEARING_LAYERS)
        self.lanterns = LanternPath(terrain)
        self._built = False

    # ------------------------------------------------------------ build (lazy, cached)
    _LAZY = ("trees", "hoods", "hood_trees", "web", "smash_point", "spider_top", "spider_end")

    def __getattr__(self, name):
        # the geometry is built on first use (~0.8 s): asking for any of it builds it
        if name in Clearing._LAZY and not self.__dict__.get("_built", True):
            self._ensure()
            return getattr(self, name)
        raise AttributeError(name)

    def _ensure(self):
        if self._built:
            return
        G = self.T.ground_y
        self.trees = []
        for i, (x, w, c0, c1, reach, nl) in enumerate(PLANE_TREES):
            self.trees.append(_crown_tree(x, G, w, self.seed * 101 + i * 7, crown=(c0, c1), reach=reach, n_limbs=nl))
        self.hoods = Hoods()
        gd = self.cottage.threshold[1]
        # hoods on the plane trees (low limbs, where the camera sees them)
        for ti, tr in enumerate(self.trees):
            pts = [p for p in tr["hang"] if gd - 1950 < p[1] < gd - 950]
            chosen = []
            for j, (hx, hy, ang) in enumerate(pts):
                if len(chosen) >= 8:
                    break
                if rnd(self.seed, ti, j, 1) < 0.5 and all(math.hypot(hx - q[0], hy - q[1]) > 170 for q in chosen):
                    chosen.append((hx, hy))
                    self.hoods.add("plane", (hx, hy), 24 + 70 * rnd(self.seed, ti, j, 2), 100 + 18 * rnd(self.seed, ti, j, 3),
                                   ti * 100 + j, self.T.snow_y)
        # hood trees in the forest layers
        self.hood_trees = {}
        for L in self.forest.layers:
            name = L["name"]
            if name not in HOOD_TREES:
                continue
            par = L["par"]
            sc = {"near": 0.78, "mid": 0.58, "far": 0.4}[name]
            items = []
            for i, xw in enumerate(HOOD_TREES[name]):
                xl = 540.0 + (xw - 540.0) * par
                w = L["w"][1] * (0.9 + 0.3 * rnd(self.seed, i, 5))
                tr = _crown_tree(xl, L["g"], w, self.seed * 13 + i * 31 + len(name), crown=(1100.0, 1750.0),
                                 reach=950.0, n_limbs=6, sc=sc, snow=name != "far", levels=1 if name == "far" else 2)
                items.append(tr)
                gy = float(L["g"](xl))
                pts = [p for p in tr["hang"] if gy - 1900 * sc < p[1] < gy - 800 * sc]
                chosen = []
                cap = {"near": 11, "mid": 12, "far": 10}[name]
                for j, (hx, hy, ang) in enumerate(pts):
                    if len(chosen) >= cap:
                        break
                    if rnd(self.seed, len(name), i, j) < 0.6 and all(math.hypot(hx - q[0], hy - q[1]) > 135 * sc for q in chosen):
                        chosen.append((hx, hy))
                        self.hoods.add(name, (hx, hy), (20 + 60 * rnd(self.seed, i, j, 6)) * sc, 100 * sc * (0.9 + 0.25 * rnd(i, j, 7)),
                                       i * 1000 + j + len(name) * 77, L["g"])
            self.hood_trees[name] = items
        self.web = _build_clearing_web(self.cottage, self.trees, self.T, self.hoods, seed=self.seed + 12)
        A = self.web.anchors
        self.smash_point = A["smash"]
        self.spider_top = A["spider_top"]
        self.spider_end = A["spider_end"]
        self._built = True

    def ignite(self, t0, point=None, **kw):
        """The S08 fire: the lantern smashed on the anchor strands at `point` (default
        self.smash_point) at time t0. Returns a cached Burn (see sets_web)."""
        self._ensure()
        p = point or self.smash_point
        return self.web.ignite([(p[0], p[1], t0)], **kw)

    @staticmethod
    def _state(era):
        return "new" if era == "later" else "old"

    # ------------------------------------------------------------ draw
    def draw_back(self, f, mood=NIGHT, era="web", t=None, canopy=None, mist=True, release=None, lit=1.0,
                  glow_at=(540.0, 760.0), haze_tex=True):
        """Sky, the fogged forest layers around the clearing (with the hood trees: their hoods
        fall when `release` says, see Hoods.release_time), far lantern lights (era "later"),
        and the dark canopy shade over the top of the frame (era "web" by default)."""
        mood = get_mood(mood)
        t = f.t if t is None else t
        self._ensure()
        backdrop(f, mood, glow=glow_at, glow_r=1150.0, glow_a=0.42 if mood.night < 0.5 else 0.16)
        F = self.forest
        hoods_on = era != "later"
        for i, L in enumerate(F.layers):
            trees = F._trees(f, L)
            name = L["name"]
            hts = self.hood_trees.get(name, [])
            par = L["par"]
            vx0, vy0, vx1, vy1 = view(f, par, 1400)
            hts = [h for h in hts if vx0 < h["x"] < vx1]
            if L.get("direct"):
                tint = L["depth"]
                with plane(f, par) as c:
                    F._paint_layer(f, c, L, mood, trees + hts, tint=tint)
                    if hoods_on:
                        red = mix(HOOD_RED, mood.fog_at(tint), tint * 0.8)
                        self.hoods.draw(c, t, self._vis_hoods(name, vx0, vx1), mood, release=release, color=red,
                                        ink=fogged(mood, tint))
                if mist:
                    ground_mist(f, par, L["g"], mood.mist, 0.42, up=320.0, down=150.0, step=110.0)
            else:
                with depth_layer(f, mood, par, L["depth"], blur=L["blur"]) as c:
                    F._paint_layer(f, c, L, mood, trees + hts, extras=name != "ghost")
                    if hoods_on and name in self.hood_trees:
                        self.hoods.draw(c, t, self._vis_hoods(name, vx0, vx1), mood, release=release)
                    if mist:
                        xs = np.linspace(vx0, vx1, max(3, int((vx1 - vx0) / 110) + 2))
                        mist_band(c, xs, np.asarray(L["g"](xs), dtype=float), mood.mist, 0.6 if i < 2 else 0.45,
                                  up=320.0 + 120 * (2 - min(i, 2)), down=150.0)
            if era == "later":
                self.lanterns.far_lights(f, L, mood, t)
            if i == 1 and haze_tex:
                f.haze(mood.mist, 0.2, tex=0.85, tex_scale=0.7, scroll=(9.0, -1.5), seed=self.seed, par=0.4)
        if canopy if canopy is not None else era == "web":
            self.canopy_shade(f, mood)

    def _vis_hoods(self, layer, x0, x1):
        return [h for h in self.hoods.groups.get(layer, []) if x0 - 300 < h["anchor"][0] < x1 + 300]

    def canopy_shade(self, f, mood=None, strength=0.6, depth=0.42):
        """Darkness pressing down from the canopy: an ink gradient over the top of the frame."""
        mood = get_mood(mood)
        with soft_layer(f, k=8, screen=True) as S:
            g = cairo.LinearGradient(0, 0, 0, 1920 * depth)
            g.add_color_stop_rgba(0, *mood.ink, strength)
            g.add_color_stop_rgba(0.55, *mood.ink, strength * 0.35)
            g.add_color_stop_rgba(1, *mood.ink, 0.0)
            S.set_source(g)
            S.paint()

    def draw_plane(self, f, mood=NIGHT, era="web", t=None, burn=None, lights=(), tremble=0.0, release=None,
                   window_light=None, door_light=None, lit=1.0, ground=True, web=True, hoods=True):
        """The action plane behind the characters: the canopy trees, the cottage, the snow
        ground, the web (intact / burning with `burn` / charred remnants in era "burnt"), the
        hoods, and (era "later") the lantern posts. lights: extra light sources the silk
        catches, e.g. [(*lantern_flame, 380, 1.0)]."""
        mood = get_mood(mood)
        t = f.t if t is None else t
        self._ensure()
        state = self._state(era)
        vx0, vy0, vx1, vy1 = view(f, 1.0, 1500)
        trees = [tr for tr in self.trees if vx0 < tr["x"] < vx1]
        with plane(f, 1.0) as c:
            _fill(c, [tr["body"] for tr in trees], mood.ink)
            _fill(c, [p for tr in trees for p in tr["limbs"]], mood.ink)
            _fill(c, [p for tr in trees for p in tr["snow"]], mood.snow)
            if vx0 - 1200 < self.cottage.x1 and self.cottage.x0 < vx1 + 1200:
                self.cottage.draw(f, c, mood, state, t, window_light, door_light)
        if ground:
            self.T.draw_back(f, mood, groove=era == "later")
        with plane(f, 1.0) as c:
            _fill(c, [p for tr in trees for p in tr["mounds"]], mood.snow)
            _fill(c, [p for tr in trees for p in tr["root_snow"]], mood.snow)
            self.cottage.draw_ground_snow(c, mood, state)
            if era == "later":
                self.lanterns.draw(f, c, mood, t, lit)
        if web and era == "web":
            self.web.draw(f, t, mood, burn=burn, lights=lights, tremble=tremble)
        elif web and era == "burnt":
            self.web.draw_remnants(f, t, mood)
        if hoods and era != "later":
            with plane(f, 1.0) as c:
                vis = [h for h in self.hoods.groups.get("plane", []) + self.hoods.groups.get("web", [])
                       if vx0 - 300 < h["anchor"][0] < vx1 + 300]
                self.hoods.draw(c, t, vis, mood, release=release, burn=burn if era == "web" else None)
        if era == "later":
            self.cottage.smoke(f, mood, t)

    def draw_front(self, f, mood=NIGHT, era="web", t=None, burn=None, lip=True, sink=6.0, occluders=True,
                   lit=1.0, window_light=None, door_light=None, smoke=None, fire_strength=1.0):
        """In front of the characters: snow lip, light on the snow (lanterns, window, fire),
        the firelight washing the frame (S08), smoke and low mist (S09), foreground brambles."""
        mood = get_mood(mood)
        t = f.t if t is None else t
        self._ensure()
        if lip:
            self.T.draw_front(f, mood, sink=sink)
        if era == "later":
            self.lanterns.ground_lights(f, mood, t, lit)
            self.cottage.draw_lights(f, mood, "new", t, window_light, door_light)
        if era == "web" and burn is not None:
            self.fire_light(f, burn, t, mood, fire_strength)
        if era == "burnt" or smoke:
            self.smoke(f, mood, t, amount=1.0 if smoke is None else smoke)
        if occluders:
            br = self.forest._brambles(f)
            if br:
                with f.layer(par=self.forest.FGV["par"], blur=self.forest.FGV["blur"]) as c:
                    _fill(c, br, mood.ink)

    def draw(self, f, mood=NIGHT, era="web", **kw):
        """Whole set without characters."""
        self.draw_back(f, mood, era)
        self.draw_plane(f, mood, era, **kw)
        self.draw_front(f, mood, era, burn=kw.get("burn"))

    # ------------------------------------------------------------ light and air
    def fire_light(self, f, burn, t, mood=NIGHT, strength=1.0):
        """Warm light thrown by the burning web on everything (after the characters, additive):
        glows at the fire clusters, pools on the snow under them, and an overall warm wash
        growing with the amount of silk alight. Returns the wash intensity 0..1."""
        mood = get_mood(mood)
        ls = burn.light_sources(t, n=4, radius=1100.0)
        if not ls:
            return 0.0
        I = clamp(burn.heat(t) / 7000.0) * strength
        with soft_layer(f, 1.0, k=6, op="add", blur=40.0) as A:
            for (x, y, r, s) in ls:
                glow(A, (x, y), r * 1.2, mood.lamp, 0.15 * s * strength)
                light_pool(A, (x, float(self.T.snow_y(x)) + 30), r * 1.4, r * 0.2, mood.lamp, 0.26 * s * strength)
        if I > 0.02:
            with soft_layer(f, k=8, op="add", screen=True) as S:
                g = cairo.LinearGradient(0, 0, 0, 1920)
                g.add_color_stop_rgba(0, *mood.lamp, 0.02 * I)
                g.add_color_stop_rgba(1, *mood.lamp, 0.07 * I)
                S.set_source(g)
                S.paint()
        return I

    def smoke(self, f, mood=None, t=0.0, amount=1.0):
        """S09: thin grey smoke rising from the smouldering web and the roof, drifting."""
        mood = get_mood(mood)
        col = mix(mood.fog_at(0.6), mood.ink, 0.25)
        srcs = [(-420.0, 900.0), (260.0, 600.0), (780.0, 420.0), (1500.0, 1300.0), (2050.0, 400.0), (-1300.0, 1100.0)]
        with soft_layer(f, 1.0, k=6, blur=26.0) as S:
            for j, (sx, sy) in enumerate(srcs):
                life = 9.0
                for i in range(12):
                    ph = (t / life + i / 12 + rnd(j, i, 3) * 0.05) % 1.0
                    age = ph * life
                    x = sx + 30 * age * (0.5 + 0.12 * age) + 40 * math.sin(age * 0.7 + i + j)
                    y = sy - 120 * age
                    r = 60 + 46 * age
                    a = 0.22 * amount * math.sin(math.pi * clamp(ph * 1.1)) ** 0.9
                    draw.circle(S, (x, y), r)
                    draw.fill(S, col, a)

    # ------------------------------------------------------------ queries
    def hood_positions(self, t=0.0, release=None, burn=None):
        """[(id, layer, x, y)] of every hood (layer coords) at t."""
        self._ensure()
        return self.hoods.positions(t, release=release, burn=burn)


# ============================================================================ the web around the cottage
def _build_clearing_web(cot, trees, T, hoods, seed=29):
    """Silk over and around the old cottage: girdles and diagonal bindings across the walls
    and roof (the cocoon), veils over the door and window, tangles at the corners, two orb
    webs (right: between the roof and the first canopy tree, its hub under Grandmother's
    thread; left: tattered), guy lines to the ground, long anchor lines up into the canopy
    and down the slope toward the valley, Grandmother's thread with the strands anchoring
    it (where the lantern is smashed), and threads holding a dozen hoods."""
    g = cot.geometry("old")
    A = g["anchors"]
    out = g["outline"]
    W = Web(junction_tol=8.0)

    def S(a, b, sag, kind, w, tag=None):
        return W.add(sag_line(a, b, sag), kind, w, tag)

    def gp(x, lift=0.0):
        return (x, float(T.snow_y(x)) - lift)

    gd = A["gd"]
    x0, x1 = cot.x0, cot.x1
    ridge = A["ridge"]
    R = sorted([tr for tr in trees if tr["x"] > x1], key=lambda tr: tr["x"])
    L = sorted([tr for tr in trees if tr["x"] < x0], key=lambda tr: -tr["x"])

    def fork(tr, y_lo, y_hi, k=0):
        cand = [p for p in tr["forks"] if y_lo < p[1] < y_hi]
        cand.sort(key=lambda p: p[1])
        return cand[k % len(cand)] if cand else (tr["x"], (y_lo + y_hi) / 2)

    def trunk(tr, h):
        side = -1 if tr["x"] > x1 else 1
        return (tr["x"] + side * tr["w"] * 0.42, float(T.ground_y(tr["x"])) - h)

    # 1. girdles: silk bound around the house (ends on the house outline), each a bundle of
    #    two or three nearly parallel strands, pulled down where something heavy once hung
    girdles = []
    hs = sorted(90 + 1280 * rnd(seed, k, 1) for k in range(7))
    for k, h in enumerate(hs):
        ya = gd - h
        yb = ya + 190 * srnd(seed, k, 2)
        xa, _ = out(ya)
        _, xb = out(yb)
        mx = lerp(xa, xb, 0.25 + 0.5 * rnd(seed, k, 3))
        my = lerp(ya, yb, 0.5) + 40 + 80 * rnd(seed, k, 4)
        for j in range(2 + int(rnd(seed, k, 5) < 0.5)):
            off = 9.0 * j
            pts = sag_line((xa, ya + off * 0.5), (mx + 14 * j, my + off), 0.02 + 0.01 * j)
            pts += sag_line((mx + 14 * j, my + off), (xb, yb + off * 0.4), 0.02 + 0.012 * j)[1:]
            st = W.add(pts, "wrap", (2.0 if j == 0 else 1.2) + 0.4 * rnd(seed, k, j, 6))
            if j == 0:
                girdles.append(st)
    # 2. a few long bindings across the front, gently curved
    for k in range(9):
        h1 = 60 + 1300 * rnd(seed, k, 6)
        h2 = 60 + 1300 * rnd(seed, k, 7)
        if abs(h1 - h2) < 360:
            h2 = min(1350, h1 + 480) if h1 < 700 else h1 - 480
        ya, yb = gd - h1, gd - h2
        xa, _ = out(ya)
        _, xb = out(yb)
        a, b = ((xa, ya), (xb, yb)) if k % 2 else ((xb, yb), (xa, ya))
        S(a, b, 0.03 + 0.04 * rnd(seed, k, 8), "wrap", 1.2 + 0.8 * rnd(seed, k, 9))
    # 2b. sheets: translucent fans of silk across the corners (eave to wall, roof to ground)
    eL, eR = A["eave_l"], A["eave_r"]
    sheets = [
        ((eL, (eL[0] + 60, eL[1] - 320)), ((x0 + 10, gd - 120), (x0 + 30, gd - 560))),
        ((eR, (eR[0] - 60, eR[1] - 320)), ((x1 - 10, gd - 120), (x1 - 30, gd - 560))),
        ((A["hip_l"][2], ridge[0]), (gp(x0 - 520), gp(x0 - 160))),
        ((A["hip_r"][-3], ridge[-1]), (gp(x1 + 560), gp(x1 + 180))),
        ((ridge[6], ridge[11]), (A["eave"][3], A["eave"][6])),
    ]
    for si, ((a0, a1), (b0, b1)) in enumerate(sheets):
        n = 9 + int(5 * rnd(seed, si, 40))
        S(a0, a1, 0.02, "wrap", 1.6)
        for i in range(n):
            u = (i + 0.3 + 0.4 * rnd(seed, si, i, 41)) / n
            pa = (lerp(a0[0], a1[0], u), lerp(a0[1], a1[1], u))
            v = clamp(u + 0.12 * srnd(seed, si, i, 42))
            pb = (lerp(b0[0], b1[0], v), lerp(b0[1], b1[1], v))
            S(pa, pb, 0.03 + 0.04 * rnd(seed, si, i, 43), "wrap", 0.9 + 0.6 * rnd(seed, si, i, 44))
        for i in range(3):
            u0, u1 = rnd(seed, si, i, 45), rnd(seed, si, i, 46)
            pa = (lerp(lerp(a0[0], a1[0], u0), lerp(b0[0], b1[0], u0), 0.35), lerp(lerp(a0[1], a1[1], u0), lerp(b0[1], b1[1], u0), 0.35))
            pb = (lerp(lerp(a0[0], a1[0], u1), lerp(b0[0], b1[0], u1), 0.7), lerp(lerp(a0[1], a1[1], u1), lerp(b0[1], b1[1], u1), 0.7))
            S(pa, pb, 0.05, "wrap", 0.9)
    # 2c. short connectors between neighbouring girdles: an irregular mesh, not a grid
    for k in range(16):
        j = int(rnd(seed, k, 10) * (len(girdles) - 1))
        ga, gb = girdles[j], girdles[j + 1]
        x = lerp(x0 - 60, x1 + 60, rnd(seed, k, 11))
        pa = (x, float(np.interp(x, ga.pts[:, 0], ga.pts[:, 1])))
        xb2 = x + 140 * srnd(seed, k, 12)
        pb = (xb2, float(np.interp(xb2, gb.pts[:, 0], gb.pts[:, 1])))
        if abs(pa[1] - pb[1]) > 30:
            S(pa, pb, 0.06, "wrap", 0.9 + 0.5 * rnd(seed, k, 13))
    # 3. roof: from the chimney and the ridge, draped down to the eaves
    ch = A["chimney"]
    for k in range(5):
        e = A["eave"][int(rnd(seed, k, 14) * len(A["eave"]))]
        S(ch, e, 0.03, "wrap", 1.1 + 0.6 * rnd(seed, k, 15))
    for k in range(5):
        r0 = ridge[int(rnd(seed, k, 16) * len(ridge))]
        e = A["eave"][int(rnd(seed, k, 17) * len(A["eave"]))]
        S(r0, e, 0.05, "wrap", 1.0 + 0.6 * rnd(seed, k, 18))
    # 4. veils over the door and the window
    d0, dg, d1, d3 = A["door"]
    for k in range(7):
        y = d3 + 40 + k * 78 + 20 * srnd(seed, k, 10)
        S((d0 - 40, y + 30 * srnd(seed, k, 11)), (d1 + 40, y + 30 * srnd(seed, k, 12)), 0.12 + 0.1 * rnd(seed, k, 13), "veil", 1.6)
    for k in range(3):
        xx = lerp(d0 + 30, d1 - 30, (k + 0.5) / 3)
        S((xx + 40 * srnd(seed, k, 14), d3 - 20), (xx + 50 * srnd(seed, k, 15), dg - 10), 0.03, "veil", 1.4)
    wx, wy, ww, wh = A["window"]
    for k in range(5):
        y = wy - wh / 2 + 30 + k * 50
        S((wx - ww / 2 - 30, y), (wx + ww / 2 + 30, y + 20 * srnd(seed, k, 16)), 0.1, "veil", 1.5)
    # 5. corner tangles
    for k in range(22):
        corner = [(x0, gd - 40), (x0, gd - 650), (x1, gd - 40), (x1, gd - 650), (A["eave_l"][0], A["eave_l"][1]),
                  (A["eave_r"][0], A["eave_r"][1])][k % 6]
        a = (corner[0] + 200 * srnd(seed, k, 17), corner[1] + 160 * srnd(seed, k, 18))
        b = (corner[0] + 220 * srnd(seed, k, 19), corner[1] + 180 * srnd(seed, k, 20))
        S(a, b, 0.06, "tangle", 1.5)
    # 6. guy lines to the ground
    for k in range(10):
        side = -1 if k % 2 == 0 else 1
        src = [A["eave_l"], A["corner_l"], ridge[0], (x0, gd - 300)] if side < 0 else [A["eave_r"], A["corner_r"], ridge[-1], (x1, gd - 300)]
        a = src[k // 2 % 4]
        xg = a[0] + side * (280 + 620 * rnd(seed, k, 21))
        S(a, gp(xg), 0.01, "anchor", 2.2)
    # 7. orb webs
    R1, L1 = R[0], L[0]
    hubA = (x1 + 540.0, gd - 1080.0)
    frameA = [ridge[-1], fork(R1, gd - 2300, gd - 1500), trunk(R1, 420.0), A["eave_r"]]
    build_orb(W, hubA, frameA, n_radials=30, ring0=60.0, ring_dr=42.0, seed=seed + 1, tatter=0.10, width=2.2)
    hubB = (x0 - 470.0, gd - 1010.0)
    frameB = [fork(L1, gd - 2200, gd - 1300), ridge[0], A["eave_l"], trunk(L1, 520.0)]
    build_orb(W, hubB, frameB, n_radials=22, ring0=60.0, ring_dr=48.0, seed=seed + 2, tatter=0.32, width=2.0,
              broken=0.2)
    # 8. into the canopy (right) and the left crowns
    for k in range(10):
        src = [ch, ridge[-1], ridge[-5], A["eave_r"], A["hip_r"][3], hubA][k % 6]
        tr = R[k % min(len(R), 2)]
        dst = fork(tr, gd - 2600, gd - 1200, k)
        S(src, dst, 0.02 + 0.02 * rnd(seed, k, 22), "anchor", 2.0)
    for k in range(6):
        src = [ridge[0], ridge[4], A["hip_l"][2], A["eave_l"], hubB, ridge[8]][k]
        tr = L[k % min(len(L), 2)]
        S(src, fork(tr, gd - 2400, gd - 1100, k), 0.025, "anchor", 2.0)
    for a_tr, b_tr in ((R[0], R[1]), (R[1], R[2]), (L[0], L[1])):
        for k in range(3):
            S(fork(a_tr, gd - 2500, gd - 1300, k), fork(b_tr, gd - 2500, gd - 1300, k + 1), 0.04, "anchor", 1.8)
    # 9. down the slope toward the valley
    for k, (a_tr, xg) in enumerate(((L[0], -2100.0), (L[1], -3100.0), (L[1], -3900.0), (L[2], -4400.0), (L[2], -5200.0))):
        S(fork(a_tr, gd - 2200, gd - 900, k), gp(xg), 0.015, "anchor", 1.9)
    S(A["eave_l"], trunk(L[0], 300.0), 0.03, "anchor", 2.0)
    S(trunk(L[0], 900.0), trunk(L[1], 700.0), 0.05, "anchor", 1.8)
    # 10. Grandmother's thread and the strands anchoring it
    sx = hubA[0] + 110.0
    top = (sx, float(T.ground_y(sx)) - 2900.0)
    end = (sx, float(T.ground_y(sx)) - 780.0)
    W.add([top, end], "thread", 2.6, tag="spider")
    gl = gp(sx - 330.0)
    gr = gp(sx + 290.0)
    left = S(end, gl, 0.01, "anchor", 2.4, tag="spider_anchor")
    S(end, gr, 0.01, "anchor", 2.4, tag="spider_anchor")
    S(end, A["eave_r"], 0.02, "anchor", 2.0, tag="spider_anchor")
    S(end, trunk(R1, 900.0), 0.02, "anchor", 2.0, tag="spider_anchor")
    S(top, fork(R1, gd - 3000, gd - 1800), 0.01, "anchor", 2.0)
    # the smash point: on the left anchor, ~200 px above the snow
    smash = None
    for u in np.linspace(0.5, 1.0, 101):
        p = left.point_at(u)
        if float(T.snow_y(p[0])) - p[1] <= 200.0:
            smash = p
            break
    # 11. hoods hanging on short threads from the outer silk (orb frames, guy lines)
    outer = [st for st in W.strands if st.kind in ("anchor", "frame") and st.tag is None]
    k = 0
    tries = 0
    while k < 7 and tries < 600:
        tries += 1
        s = outer[int(rnd(seed, tries, 30) * len(outer))]
        p = s.point_at(0.15 + 0.7 * rnd(seed, tries, 31))
        h = gd - p[1]
        if not (300 < h < 1500) or (x0 + 80 < p[0] < x1 + 60) or not (x0 - 1300 < p[0] < x1 + 1300):
            continue
        if any(math.hypot(p[0] - q["anchor"][0], p[1] - q["anchor"][1]) < 190 for q in hoods.groups.get("web", [])):
            continue
        Lth = 30 + 70 * rnd(seed, tries, 32)
        th = W.add([p, (p[0], p[1] + Lth)], "thread", 1.4, tag=("hood", k))
        hoods.add("web", p, Lth, 92 + 16 * rnd(seed, tries, 33), 9000 + k, T.snow_y, strand=th.id, amp=3.0)
        k += 1
    W.finalize()
    W.anchors.update(smash=smash, spider_top=top, spider_end=end, hub_right=hubA, hub_left=hubB, chimney=ch)
    return W


CLEARING_SET = Clearing()
