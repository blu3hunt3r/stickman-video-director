"""SHADOW PLAY - the street between the two buildings: wet asphalt that mirrors every lit
window as broken vertical streaks, puddles with rain rings, a bishop's-crook streetlamp
with its cone of rain, parked sedans (holes for windows, so the lights show through) and
the POLICE CAR with its blue / RED light bar.

Elevation view: the street is the band below a facade's base line (`ground_y`, which is
also the mirror line). Street(ground_y, depth) spans ground_y .. ground_y + depth*scale.
Reflections are mirrored about ground_y and compressed into the band (the perspective
foreshortening of a street seen from the sidewalk or from a window), so every lit window
leaves its streak, higher windows reflecting nearer the camera.
"""
import math

import cairo
import cv2
import numpy as np

from engine import draw
from engine.core import clamp, lerp, hash01, noise1, fbm1, siren
from engine.frame import surf_array, array_surface
from engine.palette import RED

from .sets_base import (PAL, INK, AMBER, HOT, RAIN, BLUE, mix, mul, layer_spec, opened, view_box,
                        glow, glow_ellipse, cone, rain_glints, add_streaks)


# =========================================================================== street
class Street:
    """Wet street in elevation.

    Street(ground_y, x0=-3000, x1=4200, scale=1.0, depth=900, sidewalk=70, seed=0,
           puddles=None, near_curb=True)
      ground_y   world y of the far sidewalk line (base of the facade) = mirror line
      depth      height of the visible street band (world px / scale)
      puddles    list of (x, depth01, rx) or None for a seeded default set
    Anchors: .curb_y (far curb), .lane_y(u) (u = 0 far curb .. 1 near curb), .near_y.
    """

    def __init__(self, ground_y, x0=-3000.0, x1=4200.0, scale=1.0, depth=900.0, sidewalk=70.0, seed=0,
                 puddles=None, near_curb=True, mirror_height=4400.0):
        self.g = float(ground_y)
        self.x0, self.x1 = float(x0), float(x1)
        self.s = float(scale)
        self.depth = depth * self.s
        self.sw = sidewalk * self.s
        self.seed = seed
        self.curb_y = self.g + self.sw
        self.road_y = self.curb_y + 12 * self.s
        self.near_y = self.g + self.depth
        self.near_curb = near_curb
        self.mirror_h = mirror_height * self.s
        if puddles is None:
            puddles = []
            for k in range(14):
                x = self.x0 + (self.x1 - self.x0) * hash01(seed, k, 1)
                u = 0.15 + 0.8 * hash01(seed, k, 2)
                rx = (90 + 260 * hash01(seed, k, 3)) * (0.5 + u)
                puddles.append((x, u, rx))
        self.puddles = [(x, u, rx * self.s if rx < 2000 else rx) for (x, u, rx) in puddles]

    def lane_y(self, u):
        """World y on the road at depth fraction u (0 = far curb, 1 = near edge)."""
        return lerp(self.road_y, self.near_y, clamp(u))

    def depth_scale(self, u, near_scale=1.6):
        """Relative size of an object standing at depth u (1 at the far curb)."""
        return lerp(1.0, near_scale, clamp(u) ** 1.3)

    def mirror(self, y):
        """Reflection y in the street band of a world point at height y above ground_y."""
        h = self.g - y
        k = (self.near_y - self.road_y) / self.mirror_h
        return self.road_y + max(0.0, h) * k

    def puddle_rect(self, p):
        x, u, rx = p
        y = self.lane_y(u)
        ry = rx * lerp(0.06, 0.16, u)
        return (x, y, rx, ry)

    # ------------------------------------------------------------------ drawing
    def draw(self, f, t, sources=(), layer=None, sky=1.0, rain=1.0, reflections=1.0, lamp_pools=()):
        """Surfaces, puddles, reflections of `sources` (dicts with rect/color/level, e.g.
        Facade.light_sources() + streetlamp/police sources; optional 'ground' = the road y
        under a source standing in the street, where its reflection starts), rain splashes
        and ripples.
        lamp_pools: [(x, level)] warm light pools on the far sidewalk (from streetlamps)."""
        spec = layer_spec(layer)
        par = spec["par"]
        s = self.s
        vb = view_box(f, par, 50)
        x0, x1 = max(self.x0, vb[0]), min(self.x1, vb[2])
        if x1 <= x0 or vb[3] < self.g or vb[1] > self.near_y + 200 * s:
            return
        with opened(f, spec) as L:
            # far sidewalk (wet slabs catching the sky), curb face, asphalt
            draw.linear(L, (0, self.g), (0, self.curb_y), [(0, mix(INK, PAL.fog_at(0.5), 0.30 * sky), 1),
                                                           (1, mix(INK, PAL.fog_at(0.5), 0.45 * sky), 1)])
            L.rectangle(x0, self.g, x1 - x0, self.curb_y - self.g)
            L.fill()
            L.rectangle(x0, self.curb_y, x1 - x0, self.road_y - self.curb_y)
            draw.fill(L, INK)
            yb = self.near_y + (200 * s if not self.near_curb else 0)
            draw.linear(L, (0, self.road_y), (0, yb), [(0, mix(INK, PAL.fog_at(0.6), 0.55 * sky), 1),
                                                      (0.25, mix(INK, PAL.fog_at(0.4), 0.22 * sky), 1),
                                                      (1, mix(INK, PAL.fog_at(0.2), 0.06 * sky), 1)])
            L.rectangle(x0, self.road_y, x1 - x0, yb - self.road_y)
            L.fill()
            if self.near_curb:
                L.rectangle(x0, self.near_y, x1 - x0, 400 * s)
                draw.linear(L, (0, self.near_y), (0, self.near_y + 400 * s),
                            [(0, mix(INK, PAL.fog_at(0.3), 0.25 * sky), 1), (1, INK, 1)])
                L.fill()
                L.rectangle(x0, self.near_y, x1 - x0, 10 * s)
                draw.fill(L, mix(INK, PAL.fog_at(0.5), 0.5 * sky))
            # puddles: deep mirrors of the sky
            for p in self.puddles:
                px, py, rx, ry = self.puddle_rect(p)
                if px + rx < x0 or px - rx > x1:
                    continue
                self._puddle_path(L, p, t)
                draw.linear(L, (0, py - ry), (0, py + ry), [(0, mix(INK, PAL.fog_at(1.0), 0.40 * sky), 1),
                                                            (1, mix(INK, PAL.fog_at(0.6), 0.18 * sky), 1)])
                L.fill()
        if reflections > 0 and sources:
            k = reflections * (1 - 0.7 * spec["fog"])
            z = f.lcam(par).zoom
            add_streaks(f, lambda c: self._streaks(c, t, sources, k, x0, x1, z), par=par, blur_v=7.0, blur_h=1.8, ds=2)
            add_streaks(f, lambda c: self._puddle_reflections(c, t, sources, k, x0, x1, z), par=par, blur_v=2.5,
                        blur_h=1.5, ds=2)
        with f.light(par=par, blur=2.5) as A:
            for (lx, lv) in lamp_pools:
                glow_ellipse(A, (lx, (self.g + self.curb_y) / 2), 420 * s, 52 * s, AMBER, 0.55 * lv)
                glow_ellipse(A, (lx, (self.g + self.curb_y) / 2), 160 * s, 26 * s, HOT, 0.45 * lv)
                glow_ellipse(A, (lx, self.road_y + 60 * s), 640 * s, 150 * s, AMBER, 0.12 * lv)
            # a thin wet sheen along the far curb edge catching the sky
            A.rectangle(x0, self.curb_y - 3 * s, x1 - x0, 4 * s)
            draw.fill(A, PAL.rain, 0.10 * sky)
            if rain > 0:
                self._splashes(A, t, x0, x1, rain)

    def reflect(self, f, t, draw_fn, foot_y, bbox, par=1.0, strength=0.55, ripple=1.0, length=0.8, seed=0):
        """Mirror what draw_fn(ctx) draws (a figure in world coords, feet at foot_y, inside
        world rect bbox) into the wet road: flipped about the feet, darkened, broken into
        wavering rows by the rain and fading over `length` of its height. Her red coat leaves
        a red smear in the street (S06). Call it BEFORE drawing the figure itself."""
        Mx = f.lcam(par).matrix(f.scale)
        bx0, by0, bx1, by1 = bbox
        pts = [Mx.transform_point(x, y) for x, y in ((bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1))]
        fx, fy = Mx.transform_point((bx0 + bx1) / 2, foot_y)
        ix0 = max(0, int(min(p[0] for p in pts)) - 8)
        ix1 = min(f.pw, int(max(p[0] for p in pts)) + 8)
        iy0 = max(0, int(min(p[1] for p in pts)) - 2)
        iy1 = min(f.ph, int(math.ceil(fy)) + 1)
        w, h = ix1 - ix0, iy1 - iy0
        if w < 2 or h < 2:
            return
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        c = cairo.Context(surf)
        c.set_matrix(Mx.multiply(cairo.Matrix(x0=-ix0, y0=-iy0)))
        draw_fn(c)
        src = surf_array(surf).astype(np.float32)
        if not src[..., 3].any():
            return
        n = int(h * length)
        dy0 = int(math.floor(fy))
        rows = min(n, f.ph - dy0)
        if rows <= 1:
            return
        out = np.zeros((rows, w, 4), np.float32)
        kpx = f.scale * f.lcam(par).zoom
        for j in range(rows):
            sr = int(fy - iy0) - j - 1
            if sr < 0:
                break
            amp = ripple * (1.5 + 0.06 * j) * kpx
            sh = int(round(amp * (noise1(j * 0.35 + t * 2.3, seed) + 0.5 * math.sin(j * 1.7 + t * 9.0))))
            row = np.roll(src[sr], sh, axis=0)
            fade = (1.0 - j / max(rows, 1)) ** 1.6
            if (j + int(t * 30)) % 7 == 0:
                fade *= 0.45                                    # rain ripples break the image
            out[j] = row * fade
        out[..., :3] *= strength
        out[..., 3] *= strength
        out = cv2.GaussianBlur(out, (0, 0), sigmaX=max(0.6, 1.2 * kpx), sigmaY=max(0.8, 2.5 * kpx))
        rs = array_surface(out)
        ctx = f.ctx
        ctx.save()
        ctx.identity_matrix()
        ry = Mx.transform_point(0, self.road_y)[1]
        ctx.rectangle(ix0, max(dy0, ry), w, rows)
        ctx.clip()
        ctx.set_source_surface(rs, ix0, dy0)
        ctx.paint()
        ctx.restore()

    def _puddle_path(self, c, p, t):
        px, py, rx, ry = self.puddle_rect(p)
        n = 18
        pts = []
        for k in range(n):
            a = 2 * math.pi * k / n
            r = 1.0 + 0.16 * (hash01(self.seed, int(px), k) - 0.5)
            pts.append((px + rx * r * math.cos(a), py + ry * r * math.sin(a)))
        draw.smooth(c, pts, close=True, tension=0.45)

    def _streaks(self, c, t, sources, k, x0, x1, zoom=1.0):
        """Long broken vertical streaks: each light leaves a bright root on the asphalt and
        a tail of ripple-broken dashes running toward the camera."""
        s = self.s
        top = self.road_y + 2 * s
        bot = self.near_y + (160 * s if not self.near_curb else 0)
        band_h = max(bot - top, 1.0)
        for si, src in enumerate(sources):
            rx0, ry0, rx1, ry1 = src["rect"]
            if rx1 < x0 - 200 or rx0 > x1 + 200:
                continue
            gy = src.get("ground")              # a source standing in the street (a car)
            hrel = clamp(((gy if gy is not None else self.g) - ry1) / self.mirror_h)
            lv = src["level"] * k * src.get("gain", 1.0) * (1.0 - 0.45 * hrel)
            col = src["color"]
            cx = (rx0 + rx1) / 2
            w = rx1 - rx0
            if gy is not None:
                root = gy + (gy - ry1) * (self.near_y - self.road_y) / self.mirror_h
            else:
                root = top + band_h * 0.30 * hrel
            length = band_h * (0.5 + 0.5 * min(lv, 1.0)) * (1.0 - 0.3 * hrel)
            seed = 400 + si
            # ripple dashes sized in SCREEN px so they survive any zoom
            q = max(s, 1.0 / max(zoom, 1e-3))
            dash, pitch = 8.0 * q, 14.0 * q
            yy = root
            while yy < min(bot, root + length):
                u = (yy - root) / length
                env = (1 - u) ** 1.5 * (0.5 + 0.5 * math.exp(-7 * u))
                br = 0.5 + 0.5 * noise1(yy * 0.05 / q - t * 1.6, seed)
                br2 = 0.5 + 0.5 * noise1(yy * 0.13 / q + t * 2.9, seed + 3)
                gate = clamp((br - 0.26) * 2.6) * (0.55 + 0.45 * br2)
                if gate > 0.02:
                    wob = 5 * q * noise1(yy * 0.035 / q + t * 2.1, seed + 7)
                    ww = w * (0.32 + 0.5 * br) * (0.8 + 0.6 * u)
                    c.rectangle(cx - ww / 2 + wob, yy, ww, dash * (0.5 + br))
                    draw.fill(c, col, min(1.0, 0.85 * lv * env * gate))
                yy += pitch
            # the bright root where the light meets the wet ground
            c.rectangle(cx - w * 0.4, root, w * 0.8, 6 * s)
            draw.fill(c, col, min(1.0, 0.6 * lv))

    def _puddle_reflections(self, c, t, sources, k, x0, x1, zoom=1.0):
        """Lights mirrored in the puddles, broken by the rain into horizontal slivers that
        shimmer (sized in screen px so they hold up in close shots)."""
        q = max(self.s, 1.0 / max(zoom, 1e-3))
        for p in self.puddles:
            px, py, rx, ry = self.puddle_rect(p)
            if px + rx < x0 or px - rx > x1:
                continue
            c.save()
            self._puddle_path(c, p, t)
            c.clip()
            for si, src in enumerate(sources):
                rx0, ry0, rx1, ry1 = src["rect"]
                if rx1 < px - rx or rx0 > px + rx:
                    continue
                ya = self.mirror(ry1)
                yb = self.mirror(ry0)
                span = max(yb - ya, 4) * 2.2
                lv = min(1.0, 0.7 * src["level"] * k * src.get("gain", 1.0))
                seed = 900 + si + int(px) % 97
                yy = ya
                pitch = 6.0 * q
                while yy < ya + span:
                    br = 0.5 + 0.5 * noise1(yy * 0.09 / q - t * 2.2, seed)
                    gate = clamp((br - 0.22) * 2.4)
                    if gate > 0.02:
                        wob = 4 * q * noise1(yy * 0.05 / q + t * 3.1, seed + 5)
                        ww = (rx1 - rx0) * (0.75 + 0.35 * br)
                        cx = (rx0 + rx1) / 2 + wob
                        c.rectangle(cx - ww / 2, yy, ww, pitch * (0.35 + 0.45 * br))
                        draw.fill(c, src["color"], lv * gate * (1.0 - 0.6 * (yy - ya) / span))
                    yy += pitch
            c.restore()

    def _splashes(self, A, t, x0, x1, k):
        """Rain hitting the asphalt: tiny crowns and expanding rings in the puddles."""
        s = self.s
        A.set_line_width(max(0.8, 1.2 * s))
        span = x1 - x0
        n = int(span / (16 * s) * k)
        for j in range(n):
            period = 0.35 + 0.5 * hash01(self.seed, j, 1)
            ph = (t / period + hash01(self.seed, j, 2)) % 1.0
            cyc = math.floor(t / period + hash01(self.seed, j, 2))
            x = x0 + span * hash01(self.seed, j, cyc, 3)
            u = hash01(self.seed, j, cyc, 4)
            y = self.lane_y(u)
            sc = self.depth_scale(u)
            if ph < 0.25:
                a = (1 - ph / 0.25) * 0.35 * k
                r = (2 + 10 * ph) * s * sc
                draw.ellipse(A, (x, y), r, r * 0.35)
                draw.rgba(A, RAIN, a)
                A.stroke()
        # rings in puddles
        for p in self.puddles:
            px, py, rx, ry = self.puddle_rect(p)
            if px + rx < x0 or px - rx > x1:
                continue
            for j in range(int(rx / (30 * s)) + 2):
                period = 0.6 + 0.6 * hash01(int(px), j, 1)
                cyc = math.floor(t / period + hash01(int(px), j, 2))
                ph = (t / period + hash01(int(px), j, 2)) % 1.0
                a0 = hash01(int(px), j, cyc, 3) * 2 * math.pi
                rr = math.sqrt(hash01(int(px), j, cyc, 4)) * 0.8
                cx = px + rx * rr * math.cos(a0)
                cy = py + ry * rr * math.sin(a0)
                r = (4 + 34 * ph) * s
                draw.ellipse(A, (cx, cy), r, r * ry / rx)
                draw.rgba(A, RAIN, 0.4 * (1 - ph) * k)
                A.stroke()


# =========================================================================== streetlamp
class Streetlamp:
    """Cast-iron bishop's-crook streetlamp with a hanging lantern.

    Streetlamp(base, height=600, scale=1.0, facing=1)
      base   world point where the post meets the sidewalk
      height post height in world px at scale 1 (600 = 4.5 m at facade scale)
    .lantern -> world point of the glowing lantern (light source)."""

    def __init__(self, base, height=600.0, scale=1.0, facing=1):
        self.base = base
        self.s = scale * height / 600.0
        self.facing = facing
        s, k = self.s, facing
        bx, by = base
        self.top = (bx, by - 560 * s)
        self.lantern = (bx + k * 96 * s, by - 488 * s)

    def _shape(self, c):
        s, k = self.s, self.facing
        bx, by = self.base
        # plinth and fluted base
        draw.poly(c, [(bx - 26 * s, by), (bx + 26 * s, by), (bx + 22 * s, by - 34 * s), (bx + 14 * s, by - 46 * s),
                      (bx + 15 * s, by - 120 * s), (bx + 9 * s, by - 136 * s), (bx - 9 * s, by - 136 * s),
                      (bx - 15 * s, by - 120 * s), (bx - 14 * s, by - 46 * s), (bx - 22 * s, by - 34 * s)])
        # tapering post with collars
        draw.poly(c, [(bx - 7 * s, by - 136 * s), (bx + 7 * s, by - 136 * s), (bx + 4.5 * s, by - 548 * s),
                      (bx - 4.5 * s, by - 548 * s)])
        for yy in (by - 300 * s, by - 420 * s):
            draw.rect(c, bx - 9 * s, yy, bx + 9 * s, yy + 9 * s)
        draw.circle(c, (bx, by - 556 * s), 8 * s)
        # the crook: an arm curving out and down to the lantern
        c.new_sub_path()
        cx, cy = bx + k * 48 * s, by - 528 * s
        r_out, r_in = 52 * s, 45 * s
        if k > 0:
            c.arc(cx, cy, r_out, math.pi, 2 * math.pi)
            c.line_to(cx + r_in, cy)
            c.arc_negative(cx, cy, r_in, 2 * math.pi, math.pi)
        else:
            c.arc_negative(cx, cy, r_out, 0, -math.pi)
            c.line_to(cx - r_in, cy)
            c.arc(cx, cy, r_in, -math.pi, 0)
        c.close_path()
        # scroll brace under the arm
        sx = bx + k * 4 * s
        draw.capsule(c, (sx, by - 470 * s), (sx + k * 34 * s, by - 520 * s), 2.2 * s, 2.2 * s)
        draw.circle(c, (sx + k * 16 * s, by - 478 * s), 7 * s)
        # lantern: cap, glass cage frame, finial drop
        lx, ly = self.lantern
        draw.rect(c, lx - 2.5 * s, by - 528 * s, lx + 2.5 * s, ly - 34 * s)
        draw.poly(c, [(lx - 24 * s, ly - 26 * s), (lx + 24 * s, ly - 26 * s), (lx + 8 * s, ly - 40 * s),
                      (lx - 8 * s, ly - 40 * s)])
        for sgn in (-1, 1):
            draw.poly(c, [(lx + sgn * 20 * s, ly - 26 * s), (lx + sgn * 24 * s, ly - 26 * s),
                          (lx + sgn * 14 * s, ly + 24 * s), (lx + sgn * 10.5 * s, ly + 24 * s)])
        draw.rect(c, lx - 14 * s, ly + 22 * s, lx + 14 * s, ly + 28 * s)
        draw.poly(c, [(lx - 5 * s, ly + 28 * s), (lx + 5 * s, ly + 28 * s), (lx, ly + 40 * s)])

    def draw(self, f, t, layer=None, on=1.0, rain=1.0, cone_k=1.0, flicker=0.0, seed=0, wall=1.0):
        """Post (ink), lantern glass (glowing), halo, cone of light with rain caught in it.
        wall: strength of the warm light the lantern throws on whatever is behind it."""
        spec = layer_spec(layer)
        s = self.s
        lx, ly = self.lantern
        lv = on * (1.0 - flicker * (0.5 + 0.5 * fbm1(t * 9.0, seed)))
        with opened(f, spec) as L:
            draw.poly(L, [(lx - 20 * s, ly - 26 * s), (lx + 20 * s, ly - 26 * s), (lx + 11 * s, ly + 23 * s),
                          (lx - 11 * s, ly + 23 * s)])
            draw.fill(L, mix(mul(AMBER, 0.25), HOT, clamp(lv)))
            self._shape(L)
            draw.fill(L, INK)
        if lv <= 0.01:
            return
        fk = 1 - 0.7 * spec["fog"]
        with f.light(par=spec["par"], blur=6.0) as A:
            glow(A, (lx, ly), 70 * s, HOT, 0.75 * lv * fk)
            glow(A, (lx, ly), 260 * s, AMBER, 0.30 * lv * fk)
            glow(A, (lx, ly + 120 * s), 760 * s, AMBER, 0.13 * lv * wall * fk)
            if cone_k > 0:
                cone(A, (lx, ly + 10 * s), 90, 26, (self.base[1] - ly) * 1.05, AMBER, 0.30 * lv * cone_k * fk, r0=10 * s)
            if rain > 0:
                bx = self.base[1]
                hgt = bx - ly

                def wgt(x, y, lx=lx, ly=ly, hgt=hgt):
                    dy = (y - ly) / hgt
                    if dy < -0.15:
                        return 0.0
                    spread = 0.1 + 0.42 * max(dy, 0.0)
                    dx = abs(x - lx) / (hgt * spread + 1e-6)
                    return math.exp(-dx * dx * 1.5) * math.exp(-max(dy, 0) * 1.0) * (1.3 if dy < 0.25 else 1.0)
                rain_glints(A, t, (lx - hgt * 0.6, ly - 60 * s, lx + hgt * 0.6, self.base[1]), color=mix(HOT, (1, 1, 1), 0.3),
                            alpha=0.85 * lv * rain * fk, density=2.6 / (s * s), seed=77 + seed, speed=1700 * s,
                            length=46 * s, width=max(0.9, 1.7 * s), wind=0.14, weight=wgt)
        with f.emit(par=spec["par"]) as G:
            draw.circle(G, (lx, ly), 22 * s)
            draw.fill(G, HOT, 0.9 * lv)

    def light_source(self, on=1.0):
        s = self.s
        lx, ly = self.lantern
        return dict(rect=(lx - 22 * s, ly - 24 * s, lx + 22 * s, ly + 24 * s), color=HOT, level=1.2 * on, gain=1.4)


# =========================================================================== cars
def _sedan_outline(s, k):
    """Side outline of a 1950s sedan (local, origin = middle of the car on the ground,
    facing +x if k = 1). Returns (body points, window polygons, wheel centres, wheel r)."""
    L = 520.0
    body = [(-260, -30), (-262, -78), (-246, -104), (-196, -116), (-150, -118), (-122, -170), (-92, -188),
            (40, -190), (82, -172), (122, -124), (196, -118), (246, -104), (262, -80), (262, -32),
            (220, -30), (212, -54), (190, -72), (160, -76), (130, -68), (112, -44), (110, -28),
            (-108, -28), (-112, -48), (-132, -70), (-162, -76), (-192, -70), (-210, -50), (-214, -30)]
    win = [[(-112, -164), (-88, -180), (-36, -180), (-36, -126), (-128, -126)],
           [(-26, -180), (36, -180), (72, -164), (106, -126), (-26, -126)]]
    wheels = [(-162, -28), (162, -28)]
    sc = s

    def T(p):
        return (p[0] * k * sc, p[1] * sc)
    return [T(p) for p in body], [[T(p) for p in w] for w in win], [T(p) for p in wheels], 34 * sc


class Car:
    """Parked 1950s sedan in side view: an ink silhouette with see-through windows.

    Car(pos, scale=1.0, facing=1)  pos = world point on the road under the car's middle.
    At scale 1 the car is 524 px long (5.2 m at 100 px/m: the scale of the far curb when
    the facade has scale 1, where a storey is 400 px)."""

    def __init__(self, pos, scale=1.0, facing=1, seed=0):
        self.pos = pos
        self.s = scale * 0.9
        self.k = facing
        self.seed = seed

    def outline(self):
        body, wins, wheels, wr = _sedan_outline(self.s, self.k)
        px, py = self.pos
        mv = lambda pts: [(px + x, py + y) for (x, y) in pts]
        return mv(body), [mv(w) for w in wins], [(px + x, py + y) for (x, y) in wheels], wr

    def draw_on(self, L, color=None, glass=0.35):
        body, wins, wheels, wr = self.outline()
        L.new_path()
        draw.smooth(L, body, close=True, tension=0.18)
        for w in wins:
            draw.poly(L, w)
        L.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        draw.fill(L, color or INK)
        L.set_fill_rule(cairo.FILL_RULE_WINDING)
        if glass > 0:
            for w in wins:
                draw.poly(L, w)
            draw.fill(L, INK, glass)
        for c in wheels:
            draw.circle(L, c, wr)
        draw.fill(L, color or INK)

    def draw(self, f, t, layer=None, headlights=0.0):
        spec = layer_spec(layer)
        with opened(f, spec) as L:
            self.draw_on(L)
        self._headlights(f, spec, headlights)

    def _headlights(self, f, spec, headlights):
        """Warm headlamps (never red tail lights: red belongs to the story)."""
        if headlights <= 0:
            return
        s, k = self.s, self.k
        hx, hy = self.pos[0] + k * 256 * s, self.pos[1] - 70 * s
        with f.light(par=spec["par"], blur=5) as A:
            glow(A, (hx, hy), 40 * s, HOT, 0.8 * headlights)
            cone(A, (hx, hy), 0 if k > 0 else 180, 14, 900 * s, AMBER, 0.12 * headlights, r0=8 * s)
        with f.emit(par=spec["par"]) as G:
            draw.circle(G, (hx, hy), 12 * s)
            draw.fill(G, HOT, 0.8 * headlights)


class PoliceCar(Car):
    """The police sedan: Car + roof light bar (blue half and RED half), a spotlight and a
    whip antenna. The strobe follows engine.core.siren (double flash, alternating).

    PoliceCar(pos, scale=1.0, facing=1)
      .bar()            world points of the (blue, red) lamps on the roof
      .strobe(t)        (blue, red) intensities 0..1
      .light_sources(t) reflections for Street.draw
      .draw(f, t, layer, lights=1.0, wash=1.0) wash = how strongly the strobe floods the set
    """

    def __init__(self, pos, scale=1.0, facing=1, seed=0, rate=1.6, phase=0.0):
        super().__init__(pos, scale, facing, seed)
        self.rate, self.phase = rate, phase

    def bar(self):
        s, k = self.s, self.k
        px, py = self.pos
        y = py - 198 * s
        return ((px + k * (-40) * s, y), (px + k * 32 * s, y))

    def strobe(self, t, on=1.0):
        b, r = siren(t, rate=self.rate, phase=self.phase)
        # soft edges so 24 fps never lands on a hard zero for a whole cycle
        b2, r2 = siren(t - 0.02, rate=self.rate, phase=self.phase)
        return on * (0.75 * b + 0.25 * b2), on * (0.75 * r + 0.25 * r2)

    def draw_on(self, L, color=None, glass=0.35):
        super().draw_on(L, color, glass)
        s, k = self.s, self.k
        px, py = self.pos
        draw.rect(L, px - 70 * s, py - 194 * s, px + 64 * s, py - 188 * s)      # bar rack
        for (bx, by) in self.bar():
            draw.ellipse(L, (bx, by), 30 * s, 11 * s)
        draw.fill(L, color or INK)
        # A-pillar spotlight and whip antenna
        draw.ellipse(L, (px + k * 60 * s, py - 176 * s), 10 * s, 7 * s)
        draw.capsule(L, (px - k * 230 * s, py - 104 * s), (px - k * 290 * s, py - 380 * s), 1.6 * s, 0.6 * s)
        draw.fill(L, color or INK)

    def draw(self, f, t, layer=None, lights=1.0, wash=1.0, headlights=0.0):
        spec = layer_spec(layer)
        s = self.s
        b, r = self.strobe(t, lights)
        (bx, by), (rx, ry) = self.bar()
        fk = 1 - 0.7 * spec["fog"]
        px, py = self.pos
        if wash > 0:
            # the strobe floods the street around the car (the body, drawn after, stays
            # a silhouette against it): a hard pool on the wet asphalt, a wide cold wash
            with f.light(par=spec["par"], blur=30.0) as A:
                for (cx, cy), col, v in (((bx, by), BLUE, b), ((rx, ry), RED, r)):
                    if v > 0.01:
                        glow_ellipse(A, (cx, cy + 200 * s), 2600 * s, 1500 * s, col, 0.10 * v * wash * fk)
                        glow_ellipse(A, (cx, py + 30 * s), 900 * s, 120 * s, col, 0.30 * v * wash * fk)
                        glow(A, (cx, cy), 900 * s, col, 0.20 * v * wash * fk)
        with opened(f, spec) as L:
            self.draw_on(L)
            # the domes light up
            for (cx, cy), col, v in (((bx, by), BLUE, b), ((rx, ry), RED, r)):
                if v > 0.01:
                    draw.ellipse(L, (cx, cy - 2 * s), 24 * s, 8 * s)
                    draw.fill(L, mix(col, (1, 1, 1), 0.35 * v), v)
        with f.light(par=spec["par"], blur=8.0) as A:
            for (cx, cy), col, v in (((bx, by), BLUE, b), ((rx, ry), RED, r)):
                if v <= 0.01:
                    continue
                glow(A, (cx, cy), 120 * s, col, 0.9 * v * fk)
                # the roof and the top of the hood catch the flash; the flank stays dark
                body, _, _, _ = self.outline()
                A.save()
                draw.smooth(A, body, close=True, tension=0.18)
                A.clip()
                glow_ellipse(A, (cx, cy + 20 * s), 300 * s, 46 * s, col, 0.35 * v * fk)
                A.restore()
        with f.emit(par=spec["par"]) as G:
            for (cx, cy), col, v in (((bx, by), BLUE, b), ((rx, ry), RED, r)):
                if v > 0.01:
                    draw.ellipse(G, (cx, cy), 34 * s, 14 * s)
                    draw.fill(G, col, 0.9 * v)
        self._headlights(f, spec, headlights)

    def light_sources(self, t, lights=1.0):
        b, r = self.strobe(t, lights)
        s = self.s
        (bx, by), (rx, ry) = self.bar()
        out = []
        gy = self.pos[1]
        if b > 0.01:
            out.append(dict(rect=(bx - 30 * s, by - 12 * s, bx + 30 * s, by + 12 * s), color=BLUE, level=1.6 * b, gain=1.8,
                            ground=gy))
        if r > 0.01:
            out.append(dict(rect=(rx - 30 * s, ry - 12 * s, rx + 30 * s, ry + 12 * s), color=RED, level=1.4 * r, gain=1.6,
                            ground=gy))
        return out


def strobe_wash(f, t, car, rect, par=1.0, k=1.0):
    """Police strobe light washing over a facade region `rect` (world x0, y0, x1, y1 at
    layer `par`): soft blue and red pools that pulse with the car's strobe."""
    b, r = car.strobe(t)
    x0, y0, x1, y1 = rect
    (bx, by), (rx, ry) = car.bar()
    with f.light(par=par, blur=40.0) as A:
        for (cx, col, v) in ((bx, BLUE, b), (rx, RED, r)):
            if v > 0.01:
                glow_ellipse(A, (cx, (y0 + y1) / 2 + (y1 - y0) * 0.25), (x1 - x0) * 0.45, (y1 - y0) * 0.55, col,
                             0.16 * v * k)
