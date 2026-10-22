"""SHADOW PLAY - props. All are filled ink silhouettes on a cairo context in WORLD coords
(action-plane scale: an adult is 600 px, 1 m = 343 px), plus their light where they have
one (call the light helpers on f.light() / f.emit() contexts, or use the *_light functions
that open those layers for you).

    binoculars(ctx, at, angle, scale, view='side'|'front', ...)   her binoculars
    binocular_view(f, center, r, ...)                               the S03 binocular mask
    BareLamp(base, height, scale)  .draw(f, t, layer, on, tilt)     bulb on a tripod stand
    Sheet(top_left, top_right, height)                              hanging cloth / shadow screen
    flashlight(ctx, hand, angle, scale), flashlight_beam(f, ...)     police torch + beam
    Door(hinge, width, height, ...)  .draw(f, t, ctx, open, ...)    opens, slams, locks
    door_swing(t, keys) / slam(t, t0, ...)                          door angle helpers
    lock_closeup(ctx, f, center, scale, bolt, key_turn)             the lock, close
    red_coat(ctx, hook, scale, sway)                                her coat on its hook (RED)
    match_flame(f, t, tip, level, scale)                            the match she strikes (S07)
    paper_blood(ctx, center, scale, seed, grow)                     red cut-paper splash
"""
import math

import cairo
import cv2
import numpy as np

from engine import draw
from engine.core import W, H, clamp, lerp, hash01, noise1, fbm1, ease
from engine.frame import cached, array_surface
from engine.palette import RED

from .sets_base import (PAL, INK, AMBER, HOT, mix, mul, layer_spec, opened,
                        glow, glow_ellipse, cone, shadow_screen)


def _xf(pts, at, angle, s, flip=1):
    """Transform local points (x along the prop axis, y down) to world."""
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    out = []
    for x, y in pts:
        y *= flip
        out.append((at[0] + (x * ca - y * sa) * s, at[1] + (x * sa + y * ca) * s))
    return out


# =========================================================================== binoculars
def binoculars(ctx, at, angle=0.0, scale=1.0, view="side", flip=1, strap=0.0, color=None, t=0.0):
    """Her 7x50 Porro-prism binoculars (18 cm long = 62 px at scale 1).

    view='side'  profile; `at` is the grip point (middle of the body, where the hand holds
                 them), `angle` the direction they look (deg, 0 = +x, eyepieces at the back).
                 flip=-1 mirrors the prism hump below the axis. strap 0..1 draws the neck
                 strap hanging from the eyepiece end (1 = full loop, e.g. lying on the sill).
    view='front' seen from where they point (the man in her window, S08): two objective
                 lenses and the hinge; `at` = centre of the hinge. Lens glints: use
                 binocular_glints(f, at, scale) on top.
    view='pair'  both barrels seen square-on to the hinge (the iconic shape: eyepieces close,
                 objectives wide); angle=90 stands them on their objectives (on her sill).
    Returns the world point of the eyepieces (side, pair) or the two lens centres (front)."""
    col = color or INK
    s = scale
    if view == "pair":
        for sgn in (-1, 1):
            def P(pts):
                q = _xf([(x, sgn * y) for (x, y) in pts], at, angle, s, 1)
                return q if sgn > 0 else q[::-1]          # keep one winding: no holes where parts overlap
            draw.poly(ctx, P([(-33, 6.5), (-32, 5.0), (-27, 5.0), (-27, 17.0), (-32, 17.0), (-33, 15.5)]))   # eyecup
            draw.poly(ctx, P([(-28, 6.0), (-19, 6.5), (-19, 16.5), (-28, 16.0)]))                 # eyepiece
            draw.smooth(ctx, P([(-21, 3.0), (-6, 3.0), (3, 9.0), (4, 31.0), (-7, 32.0), (-21, 20.0)]), close=True,
                        tension=0.12)                                                           # prism housing
            draw.poly(ctx, P([(1, 10.0), (25, 10.5), (31, 9.5), (31, 31.0), (25, 30.0), (1, 30.5)]))    # objective
        draw.poly(ctx, _xf([(-24, -5.5), (2, -5.5), (2, 5.5), (-24, 5.5)], at, angle, s))             # hinge
        draw.poly(ctx, _xf([(-21, -7.5), (-13, -7.5), (-13, 7.5), (-21, 7.5)], at, angle, s))        # focus wheel
        draw.fill(ctx, col)
        return _xf([(-33, 0)], at, angle, s)[0]
    if view == "front":
        cx, cy = at
        ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        lens = []
        for sgn in (-1, 1):
            p = (cx + sgn * 21 * s * ca, cy + sgn * 21 * s * sa)
            lens.append(p)
            # prism housing behind the lens, then the lens bell
            draw.ellipse(ctx, (p[0], p[1] - 3 * s), 15 * s, 18 * s, angle=angle)
            draw.circle(ctx, p, 13.5 * s)
        draw.rect(ctx, cx - 8 * s, cy - 6 * s, cx + 8 * s, cy + 4 * s)          # hinge bridge
        draw.circle(ctx, (cx, cy - 12 * s), 5 * s)                               # focus wheel
        draw.fill(ctx, col)
        return lens
    # profile, local coords: x from eyepiece (-31) to objective (+31), y down
    pts = [(-31, -6), (-24, -6.5), (-22, -9), (-12, -10), (-12, -16), (6, -16), (9, -12), (16, -11.5),
           (27, -12.5), (31, -13.5), (31, 13.5), (27, 12.5), (16, 11.5), (9, 10), (-6, 10), (-12, 8),
           (-22, 7), (-24, 6.5), (-31, 6)]
    W_ = _xf(pts, at, angle, s, flip)
    draw.poly(ctx, W_)
    # focus wheel on top of the hinge
    fw = _xf([(-14, -16)], at, angle, s, flip)[0]
    draw.circle(ctx, fw, 5 * s)
    # eyecup
    ec = _xf([(-33, 0)], at, angle, s, flip)[0]
    draw.ellipse(ctx, ec, 4 * s, 7 * s, angle=angle)
    if strap > 0:
        a = _xf([(-27, 5)], at, angle, s, flip)[0]
        b = _xf([(-20, 5)], at, angle, s, flip)[0]
        sag = 70 * s * strap
        sw = 6 * s * math.sin(t * 1.3)
        pts2 = [a, (a[0] - 20 * s + sw, a[1] + sag * 0.7), (a[0] + 4 * s + sw, a[1] + sag),
                (b[0] + 18 * s + sw * 0.5, b[1] + sag * 0.8), b]
        draw.chain(ctx, pts2, [1.6 * s] * len(pts2))
    draw.fill(ctx, col)
    return _xf([(-31, 0)], at, angle, s, flip)[0]


def binocular_glints(f, lenses, scale=1.0, level=1.0, par=1.0):
    """Two tiny cold glints on the objective lenses (the man in her window, S08)."""
    if level <= 0:
        return
    with f.emit(par=par) as G:
        for p in lenses:
            draw.circle(G, (p[0] - 3 * scale, p[1] - 3 * scale), 4 * scale)
            draw.fill(G, PAL.lightning, 0.9 * level)
    with f.light(par=par, blur=2) as A:
        for p in lenses:
            glow(A, (p[0] - 3 * scale, p[1] - 3 * scale), 12 * scale, PAL.lightning, 0.6 * level)


def binocular_view(f, center=(W / 2, H / 2), r=330.0, sep=0.56, soft=18.0, alpha=1.0, ring=0.6):
    """The binocular POV mask (S03): everything outside two overlapping circles goes to
    black, with a soft optical edge and a faint dark ring. Screen space (frame px).
    center: middle of the pair; r: circle radius; sep: centre distance / (2r)."""
    if alpha <= 0:
        return
    ds = 4
    w, h = max(1, f.pw // ds), max(1, f.ph // ds)
    k = f.scale / ds
    key = ("sp_bino", w, h, round(center[0], 1), round(center[1], 1), round(r, 1), round(sep, 3), round(soft, 1),
           round(ring, 2))

    def build():
        m = np.zeros((h, w), np.float32)
        d = sep * r
        for sgn in (-1, 1):
            cv2.circle(m, (int(round((center[0] + sgn * d) * k * 16)), int(round(center[1] * k * 16))),
                       int(round(r * k * 16)), 1.0, -1, lineType=cv2.LINE_AA, shift=4)
        m = cv2.GaussianBlur(m, (0, 0), max(0.5, soft * k))
        a = 1.0 - np.clip(m, 0, 1)
        if ring > 0:
            # dark band just inside the rim (lens barrel vignette)
            a = np.maximum(a, ring * np.clip(1.0 - np.abs(m - 0.5) * 2.2, 0, 1) * 0.6)
        out = np.zeros((h, w, 4), np.float32)
        out[..., 3] = a * 255
        return array_surface(out)
    surf = cached(key, build)
    with f.screen() as S:
        pat = cairo.SurfacePattern(surf)
        pat.set_filter(cairo.FILTER_BILINEAR)
        pat.set_matrix(cairo.Matrix(xx=w / float(W), yy=h / float(H)))
        S.set_source(pat)
        S.paint_with_alpha(clamp(alpha))


# =========================================================================== the bare lamp
class BareLamp:
    """A bare bulb on a tripod light stand (apartment 9's show lamp).

    BareLamp(base, height=520, scale=1.0)
      base    world point on the floor under the stand (the tilt pivot)
      height  floor to bulb, world px at scale 1 (520 = 1.5 m)
    .bulb(tilt)   world centre of the bulb (the light source; use it for shadows)
    .draw(f, t, layer, on=0..1, tilt=deg, broken=False, cord_to=None, glow=1.0)
    Turn it on with sets.switch(t, t_on, kind='flicker'|'bulb')."""

    def __init__(self, base, height=520.0, scale=1.0):
        self.base = base
        self.h = height * scale
        self.s = scale

    def _pt(self, x, y, tilt):
        """Local (x right, y up from the base) -> world, rotated by tilt about the base."""
        a = math.radians(tilt)
        ca, sa = math.cos(a), math.sin(a)
        return (self.base[0] + x * ca + y * sa, self.base[1] + x * sa - y * ca)

    def bulb(self, tilt=0.0):
        return self._pt(0, self.h + 22 * self.s, tilt)

    def draw(self, f, t, layer=None, on=0.0, tilt=0.0, broken=False, cord_to=None, glow_k=1.0):
        spec = layer_spec(layer)
        s = self.s
        P = lambda x, y: self._pt(x, y, tilt)
        b = self.bulb(tilt)
        with opened(f, spec) as L:
            # bulb glass (behind the socket)
            if not broken:
                pts = [P(math.sin(a) * (17 if a < math.pi * 0.62 or a > math.pi * 1.38 else 11) * s,
                         self.h + 22 * s + math.cos(a) * 21 * s) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
                draw.smooth(L, pts, close=True, tension=0.5)
                draw.fill(L, mix((0.05, 0.05, 0.06), HOT, clamp(on)))
            # tripod legs, pole, collar, socket
            for sx in (-1, 0, 1):
                foot = P(sx * 120 * s, 0) if sx else P(16 * s, 0)
                draw.capsule(L, P(0, 150 * s), foot, 4 * s, 3 * s)
            draw.capsule(L, P(0, 40 * s), P(0, self.h - 8 * s), 4.5 * s, 3.5 * s)
            draw.capsule(L, P(0, 150 * s), P(0, 175 * s), 8 * s, 8 * s)
            draw.capsule(L, P(0, self.h * 0.62), P(0, self.h * 0.62 + 14 * s), 7 * s, 7 * s)
            draw.poly(L, [P(-9 * s, self.h - 10 * s), P(9 * s, self.h - 10 * s), P(8 * s, self.h + 8 * s),
                          P(-8 * s, self.h + 8 * s)])
            if broken:
                # jagged glass left in the socket
                jag = [(-8, 8), (-10, 16), (-5, 13), (-2, 22), (2, 14), (6, 19), (9, 10), (8, 8)]
                draw.poly(L, [P(x * s, self.h + y * s) for x, y in jag])
            # the cord: down the pole and away along the floor
            c0 = P(-5 * s, self.h * 0.55)
            c1 = P(-5 * s, 40 * s)
            end = cord_to or (self.base[0] - 260 * s, self.base[1])
            draw.chain(L, [c0, c1, (lerp(c1[0], end[0], 0.3), self.base[1] - 2 * s),
                           (lerp(c1[0], end[0], 0.7), self.base[1] - 1 * s), end], [1.8 * s] * 5)
            draw.fill(L, INK)
        if on > 0.01 and not broken:
            lamp_light(f, b, on, scale=s, par=spec["par"], k=glow_k * (1 - 0.7 * spec["fog"]))
        return b


def lamp_light(f, p, level=1.0, scale=1.0, par=1.0, k=1.0, radius=900.0):
    """The glow of a bare bulb at world point p: hot core (emissive) + halo + room fill."""
    if level <= 0.01:
        return
    s = scale
    with f.light(par=par, blur=6.0) as A:
        glow(A, p, 46 * s, HOT, 0.9 * level * k)
        glow(A, p, 220 * s, HOT, 0.30 * level * k)
        glow(A, p, radius * s, AMBER, 0.10 * level * k)
    with f.emit(par=par) as G:
        draw.circle(G, p, 22 * s)
        draw.fill(G, HOT, min(1.0, level))


# =========================================================================== the sheet
class Sheet:
    """A bedsheet hung from a wire with clothes-pins: the shadow screen.

    Sheet(top_left, top_right, height, pins=5, seed=0)  (world; height in world px)
    .outline(t, ...)  list of world points (closed)  -> use as a clip / shadow region
    .draw(f, t, ctx, light=None, level=1.0, back=True, ...)   the cloth itself
    .shadow(ctx, t, casters, lamp, mag, soft, density)          shadows / gels on it
    .tear(x, y, length, angle) entries in `tears` cut slits that leak light.

    Motion: `sway` (breeze), `hit` = (t0, x, y, strength) a stab or a push that ripples out,
    `fall` 0..1 the left pins letting go (the sheet slumps toward the right pin)."""

    def __init__(self, top_left, top_right, height, pins=5, seed=0):
        self.a = top_left
        self.b = top_right
        self.h = float(height)
        self.pins = pins
        self.seed = seed

    def pin_points(self, fall=0.0):
        out = []
        for k in range(self.pins):
            u = k / (self.pins - 1)
            x = lerp(self.a[0], self.b[0], u)
            y = lerp(self.a[1], self.b[1], u)
            out.append((x, y))
        return out

    def outline(self, t, sway=1.0, hit=None, fall=0.0, n_side=8, n_hem=14):
        a, b = self.a, self.b
        Wd = b[0] - a[0]
        sd = self.seed
        brz = sway * (0.010 * Wd * fbm1(t * 0.45, sd) + 0.004 * Wd * math.sin(t * 1.7 + sd))

        def push(x, y):
            if not hit:
                return 0.0, 0.0
            t0, hx, hy, st = hit
            dt = t - t0
            if dt < 0:
                return 0.0, 0.0
            d = math.hypot(x - hx, y - hy) / (Wd * 0.5)
            env = st * math.exp(-dt * 2.2) * math.exp(-d * d * 1.5)
            wave = math.sin(dt * 14.0 - d * 5.0)
            return 0.02 * Wd * env * wave, 0.012 * Wd * env * wave * 0.5

        pts = []
        # top edge: pinned points with sag between them
        pp = self.pin_points()
        for k, p in enumerate(pp):
            if fall > 0 and k < self.pins - 1:
                # pins pop from the left: the cloth peels down and swings toward the right pin
                u = k / (self.pins - 1)
                drop = clamp(fall * 1.6 - u * 0.9)
                p = (lerp(p[0], lerp(p[0], b[0], 0.35), drop), p[1] + self.h * 0.85 * drop * (1 - u))
            pts.append(p)
            if k < self.pins - 1:
                q = pp[k + 1]
                pts.append(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.035 * Wd / max(self.pins - 1, 1) * 1.6))
        # right side down
        yt, yb = b[1], b[1] + self.h
        for k in range(1, n_side + 1):
            u = k / n_side
            x = b[0] + brz * u * u + 0.006 * Wd * math.sin(u * 3 + t * 0.8 + sd)
            dx, dy = push(x, lerp(yt, yb, u))
            pts.append((x + dx, lerp(yt, yb, u) + dy))
        # hem, right to left
        for k in range(1, n_hem):
            u = k / n_hem
            x = lerp(b[0], a[0], u) + brz
            y = lerp(b[1], a[1], u) + self.h + 0.012 * Wd * math.sin(u * 9.0 + t * 1.1 + sd) \
                + 0.006 * Wd * math.sin(u * 23.0 - t * 0.7)
            dx, dy = push(x, y)
            if fall > 0:
                y += -self.h * 0.5 * clamp(fall * 1.6 - (1 - u) * 0.9) * (1 - u)
            pts.append((x + dx, y + dy))
        # left side up
        for k in range(n_side, -1, -1):
            u = k / n_side
            x = a[0] + brz * u * u + 0.006 * Wd * math.sin(u * 3 + t * 0.8 + sd + 1.0)
            y = lerp(a[1], a[1] + self.h, u)
            if fall > 0:
                y -= self.h * 0.5 * clamp(fall * 1.6 - 0.1) * u
                x += (b[0] - a[0]) * 0.35 * clamp(fall * 1.6) * (1 - u)
            dx, dy = push(x, y)
            pts.append((x + dx, y + dy))
        return pts

    def path(self, ctx, t, **kw):
        draw.smooth(ctx, self.outline(t, **kw), close=True, tension=0.35)

    def draw(self, f, t, ctx, light=None, level=1.0, back=True, base=None, sway=1.0, hit=None, fall=0.0,
             tears=(), folds=1.0, wire=True, pins=True):
        """The cloth. light = world point of the lamp (hot spot), level its brightness.
        back=True: lit from BEHIND (translucent glow, transmission); False: lit from the
        camera side (diffuse reflection; flatter, folds show as light and shade).
        base: colour of the unlit cloth (default: a pale ghost in the dark)."""
        kw = dict(sway=sway, hit=hit, fall=fall)
        a, b = self.a, self.b
        Wd = b[0] - a[0]
        cx, cy = (a[0] + b[0]) / 2, a[1] + self.h * 0.5
        lp = light or (cx, cy)
        unlit = base or mix(INK, PAL.fog_at(1.0), 0.55)
        lk = clamp(level)
        hot = mix(unlit, HOT if back else mix(HOT, AMBER, 0.3), lk)
        mid = mix(unlit, mix(AMBER, HOT, 0.45) if back else mul(AMBER, 0.85), lk)
        far = mix(unlit, mul(AMBER, 0.42 if back else 0.5), lk)
        ctx.save()
        self.path(ctx, t, **kw)
        ctx.clip_preserve()
        r = math.hypot(Wd, self.h) * (0.62 if back else 0.75)
        draw.radial(ctx, lp, 0, r, [(0, hot, 1), (0.28 if back else 0.4, mid, 1), (1, far, 1)])
        ctx.fill()
        # folds: soft vertical bands of more and less cloth (darker = gathered folds)
        if folds > 0:
            n = 9
            stops = []
            for k in range(n + 1):
                u = k / n
                v = 0.5 + 0.5 * math.sin(u * 2 * math.pi * 3.3 + self.seed + 0.6 * math.sin(t * 0.4))
                stops.append((u, INK, folds * (0.10 + 0.16 * v) * (0.6 + 0.4 * lk)))
            draw.linear(ctx, (a[0], 0), (b[0], 0), stops)
            ctx.paint()
        # hem shading: the bottom edge is a double layer
        draw.linear(ctx, (0, a[1] + self.h * 0.88), (0, a[1] + self.h * 1.02), [(0, INK, 0), (1, INK, 0.25 * folds)])
        ctx.paint()
        ctx.restore()
        # tears: slits that let the light through (bright when lit from behind)
        for (tx, ty, tl, ta) in tears:
            ca, sa = math.cos(math.radians(ta)), math.sin(math.radians(ta))
            p0 = (tx - ca * tl / 2, ty - sa * tl / 2)
            p1 = (tx + ca * tl / 2, ty + sa * tl / 2)
            wdt = tl * 0.09
            nx, ny = -sa * wdt, ca * wdt
            draw.smooth(ctx, [p0, (tx + nx, ty + ny), p1, (tx - nx, ty - ny)], close=True, tension=0.4)
            draw.fill(ctx, mix(HOT, (1, 1, 1), 0.2) if back and lk > 0.05 else INK, 1.0)
        if wire or pins:
            if wire:
                ext = Wd * 0.18
                draw.capsule(ctx, (a[0] - ext, a[1] - 2), (b[0] + ext, b[1] - 2), 1.6, 1.6)
            if pins:
                for p in self.pin_points():
                    draw.poly(ctx, [(p[0] - 4, p[1] - 8), (p[0] + 4, p[1] - 8), (p[0] + 3, p[1] + 16),
                                    (p[0] - 3, p[1] + 16)])
            draw.fill(ctx, INK)

    def shadow(self, ctx, t, casters, lamp=None, mag=1.0, soft=5.0, density=0.9, sway=1.0, hit=None, fall=0.0):
        """Multiply the shapes drawn by casters(c) onto the cloth as shadows (RED shapes act
        as gels). mag/lamp: magnify about the lamp's point (a caster near the lamp throws a
        giant shadow); soft: penumbra in world px."""
        kw = dict(sway=sway, hit=hit, fall=fall)
        pts = self.outline(t, **kw)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]

        def region(c):
            draw.smooth(c, pts, close=True, tension=0.35)
        shadow_screen(ctx, casters, region=region, bbox=(min(xs), min(ys), max(xs), max(ys)), soft=soft,
                      density=density, mag=mag, center=lamp)

    def light(self, f, t, light, level=1.0, par=1.0, k=1.0, back=True):
        """Glow of the lit sheet into the room (additive) + bloom."""
        if level <= 0.01:
            return
        a, b = self.a, self.b
        cx, cy = (a[0] + b[0]) / 2, a[1] + self.h * 0.5
        Wd = b[0] - a[0]
        with f.light(par=par, blur=30.0) as A:
            glow_ellipse(A, (cx, cy), Wd * 0.9, self.h * 0.75, AMBER, 0.16 * level * k)
        with f.emit(par=par) as G:
            p = light or (cx, cy)
            glow(G, p, Wd * 0.45, HOT, 0.35 * level * k)


# =========================================================================== flashlight
def flashlight(ctx, hand, angle=0.0, scale=1.0, color=None):
    """Police torch (a long 4-cell steel torch, 36 cm = 124 px). hand = grip point;
    angle = beam direction. Returns the lens centre (beam origin)."""
    s = scale
    pts = [(-46, -6), (34, -6), (40, -10.5), (52, -12.5), (58, -12.5), (58, 12.5), (52, 12.5), (40, 10.5),
           (34, 6), (-46, 6), (-50, 3), (-50, -3)]
    draw.poly(ctx, _xf(pts, hand, angle, s))
    draw.fill(ctx, color or INK)
    return _xf([(59, 0)], hand, angle, s)[0]


def flashlight_beam(f, origin, angle, length=1100.0, spread=10.0, level=1.0, par=1.0, hit=True, t=0.0,
                    dust=1.0, scale=1.0, color=None, seed=0):
    """A torch beam in a dark room: a soft cone (additive), the hot spot where it lands
    (an ellipse at the end of the beam, if hit), dust motes drifting through it."""
    if level <= 0.01:
        return
    col = color or mix(HOT, (1, 1, 1), 0.15)
    s = scale
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    end = (origin[0] + ux * length, origin[1] + uy * length)
    with f.light(par=par, blur=10.0) as A:
        cone(A, origin, angle, spread, length, col, 0.30 * level, r0=10 * s, falloff=0.95, soft_edge=0.45)
        glow(A, origin, 60 * s, col, 0.6 * level)
        if hit:
            rx = length * math.tan(math.radians(spread)) * 1.15
            glow_ellipse(A, end, rx, rx * 1.15, col, 0.55 * level, angle=angle)
            glow_ellipse(A, end, rx * 0.45, rx * 0.5, col, 0.45 * level, angle=angle)
    if dust > 0:
        with f.light(par=par, blur=1.5) as A:
            n = int(46 * dust)
            for k in range(n):
                u = hash01(seed, k, 1)
                d = length * (0.08 + 0.9 * u)
                half = d * math.tan(math.radians(spread)) * 0.9
                off = (hash01(seed, k, 2) * 2 - 1) * half
                dx = 18 * s * noise1(t * 0.3 + k, seed + 3)
                dy = 18 * s * noise1(t * 0.25 + k * 1.7, seed + 5) + 10 * s * t % 40
                px = origin[0] + ux * d - uy * off + dx
                py = origin[1] + uy * d + ux * off + dy
                tw = 0.5 + 0.5 * math.sin(t * 3.0 + k)
                draw.circle(A, (px, py), (1.2 + 1.4 * hash01(seed, k, 4)) * s)
                draw.fill(A, col, 0.5 * level * tw * (1 - 0.6 * u))
    with f.emit(par=par) as G:
        draw.circle(G, origin, 9 * s)
        draw.fill(G, col, 0.9 * level)


# =========================================================================== door
def door_swing(t, keys):
    """Door opening 0..1 from keys [(t, open, ease), ...] (ease of the segment ending at
    that key: 'inout', 'out3', 'slam', 'creak'). 'slam' arrives fast and bounces off the
    frame; 'creak' is a slow, stepping open."""
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        t0, v0 = keys[i - 1][0], keys[i - 1][1]
        t1, v1 = keys[i][0], keys[i][1]
        e = keys[i][2] if len(keys[i]) > 2 else "inout"
        if t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-6)
            if e == "slam":
                return lerp(v0, v1, u ** 2.2)
            if e == "creak":
                st = u + 0.06 * math.sin(u * math.pi * 5)
                return lerp(v0, v1, clamp(ease("inout", clamp(st))))
            return lerp(v0, v1, ease(e, u))
    # after the last key: a slam bounces
    tl, vl = keys[-1][0], keys[-1][1]
    if len(keys[-1]) > 2 and keys[-1][2] == "slam":
        dt = t - tl
        return clamp(vl + 0.06 * math.exp(-dt * 9) * abs(math.sin(dt * 22)))
    return vl


def slam(t, t0, dur=0.22, from_open=0.8):
    """Door opening value for a slam starting at t0 (fast close + bounce)."""
    return door_swing(t, [(t0, from_open), (t0 + dur, 0.0, "slam")])


class Door:
    """An apartment door (2.1 m x 0.9 m) with frame, panels read through light, a knob, a
    keyhole and a deadbolt; light leaks around and under it from the hallway.

    Door(hinge, width=310, height=720, swing=1, project=None)
      hinge   world point of the hinge-side bottom corner (on the floor line)
      swing   +1: the free edge is to the right of the hinge (opens toward the camera)
      project optional callable (u, n, v) -> world point, for a door set in a receding wall:
              u along the wall from the hinge (px), n out of the wall into the room, v up.
              Default: a front-on wall with mild perspective on the swinging leaf.
    .draw(f, t, ctx, open=0..1, hall=0..1 hallway light, locked=0..1, key=False,
          feet=() x offsets of feet blocking the light under the door)
    .light(f, t, open, hall) the slab of hallway light thrown into the room (call after)."""

    def __init__(self, hinge, width=310.0, height=720.0, swing=1, project=None):
        self.hinge = hinge
        self.w = width
        self.h = height
        self.swing = swing
        self.project = project or self._front

    def _front(self, u, n, v):
        x0, y0 = self.hinge
        k = 1.0 + n * 0.00035                 # nearer = slightly bigger
        return (x0 + self.swing * u * k, y0 - v * k + n * 0.06)

    def leaf_quad(self, open_):
        ang = math.radians(100 * clamp(open_))
        P = self.project
        u, n = self.w * math.cos(ang), self.w * math.sin(ang)
        return [P(0, 0, 0), P(u, n, 0), P(u, n, self.h), P(0, 0, self.h)]

    def opening_quad(self):
        P = self.project
        return [P(0, 0, 0), P(self.w, 0, 0), P(self.w, 0, self.h), P(0, 0, self.h)]

    def knob(self, open_=0.0):
        ang = math.radians(100 * clamp(open_))
        u = (self.w - 34) * math.cos(ang)
        n = (self.w - 34) * math.sin(ang) + 10
        return self.project(u, n, self.h * 0.46)

    def draw(self, f, t, ctx, open=0.0, hall=0.0, locked=0.0, key=False, feet=(), hall_fn=None):
        P = self.project
        op = clamp(open)
        # the hallway seen through the opening (lit), or nothing
        quad = self.opening_quad()
        if op > 0.005:
            draw.poly(ctx, quad)
            top = min(p[1] for p in quad)
            bot = max(p[1] for p in quad)
            draw.linear(ctx, (0, top), (0, bot), [(0, mix(INK, mul(AMBER, 0.55), hall), 1),
                                                  (1, mix(INK, mul(AMBER, 0.9), hall), 1)])
            ctx.fill()
            if hall_fn is not None:
                ctx.save()
                draw.poly(ctx, quad)
                ctx.clip()
                hall_fn(ctx)
                ctx.restore()
        # frame / casing
        cw = 26.0
        frame = [P(-cw, 0, 0), P(-cw, 0, self.h + cw), P(self.w + cw, 0, self.h + cw), P(self.w + cw, 0, 0),
                 P(self.w, 0, 0), P(self.w, 0, self.h), P(0, 0, self.h), P(0, 0, 0)]
        draw.poly(ctx, frame)
        draw.fill(ctx, INK)
        # the leaf
        leaf = self.leaf_quad(op)
        draw.poly(ctx, leaf)
        draw.fill(ctx, mix(INK, PAL.fog_at(0.8), 0.18))
        # panels: four recessed panels catch a little light (read as tone, not line)
        ang = math.radians(100 * op)
        cu, sn = math.cos(ang), math.sin(ang)

        def L(u, v, n0=0.0):
            return P(u * cu, u * sn + n0, v)
        for (u0, u1, v0, v1) in ((0.16, 0.46, 0.08, 0.42), (0.54, 0.84, 0.08, 0.42),
                                 (0.16, 0.46, 0.52, 0.9), (0.54, 0.84, 0.52, 0.9)):
            draw.poly(ctx, [L(u0 * self.w, v0 * self.h), L(u1 * self.w, v0 * self.h), L(u1 * self.w, v1 * self.h),
                            L(u0 * self.w, v1 * self.h)])
        draw.fill(ctx, INK, 0.55)
        # knob, keyhole escutcheon, deadbolt thumb-turn
        kb = self.knob(op)
        draw.circle(ctx, kb, 11)
        esc = L(self.w - 34, self.h * 0.40)
        draw.poly(ctx, [(esc[0] - 6, esc[1] - 14), (esc[0] + 6, esc[1] - 14), (esc[0] + 6, esc[1] + 14),
                        (esc[0] - 6, esc[1] + 14)])
        bolt = L(self.w - 34, self.h * 0.56)
        draw.circle(ctx, bolt, 12)
        draw.fill(ctx, INK)
        # thumb turn: a bar that rotates when it locks
        ta = math.radians(90 * clamp(locked))
        draw.capsule(ctx, (bolt[0] - 9 * math.cos(ta), bolt[1] - 9 * math.sin(ta)),
                     (bolt[0] + 9 * math.cos(ta), bolt[1] + 9 * math.sin(ta)), 3.2, 3.2)
        draw.fill(ctx, mix(INK, PAL.fog_at(1.0), 0.6))
        if key:
            kh = (esc[0], esc[1] + 4)
            ka = math.radians(90 * clamp(locked))
            draw.capsule(ctx, kh, (kh[0], kh[1] + 30), 2.5, 2.5)
            draw.ellipse(ctx, (kh[0] + 12 * math.sin(ka) * 0, kh[1] + 38), 10 * abs(math.cos(ka)) + 2, 10)
            draw.fill(ctx, INK)

    def light(self, f, t, open=0.0, hall=1.0, feet=(), par=1.0, spill=1.0, floor_fn=None):
        """Hallway light: a thin line under the closed door (broken by `feet`), light round
        the edges as it opens, and a slab of light thrown across the floor."""
        if hall <= 0.01:
            return
        P = self.project
        op = clamp(open)
        with f.light(par=par, blur=3.0) as A:
            if op < 0.02:
                # the gap under the door (in the door's own perspective), broken by the feet
                n = 40
                open_ = []
                for k in range(n):
                    u0, u1 = k / n * self.w, (k + 1) / n * self.w
                    if not any(abs((u0 + u1) / 2 - fx) < 34 for fx in feet):
                        open_.append((u0, u1))
                for (u0, u1) in open_:
                    draw.poly(A, [P(u0, 0, 0), P(u1, 0, 0), P(u1, 0, 6), P(u0, 0, 6)])
                draw.fill(A, HOT, 0.9 * hall)
                # and its fan on the floor inside, with the same gaps
                for (u0, u1) in open_:
                    draw.poly(A, [P(u0, 0, 0), P(u1, 0, 0), P(u1 + 6, 80, 0), P(u0 - 6, 80, 0)])
                draw.linear(A, P(self.w / 2, 0, 0), P(self.w / 2, 80, 0), [(0, AMBER, 0.32 * hall), (1, AMBER, 0.0)])
                A.fill()
            else:
                q = self.opening_quad()
                draw.poly(A, q)
                draw.fill(A, AMBER, 0.12 * hall * min(1.0, op * 4))
        if op > 0.02 and spill > 0:
            with f.light(par=par, blur=14.0) as A:
                q = self.opening_quad()
                ang = math.radians(100 * op)
                # the slab of light on the floor, widening into the room
                fl = floor_fn or (lambda u, n: self.project(u, n, 0))
                depth = 900.0 * op
                pts = [fl(0 + self.w * (1 - math.cos(ang)) * 0.0, 0), fl(self.w, 0),
                       fl(self.w * 1.35, depth), fl(self.w * 0.05 + self.w * math.cos(ang) * 0.6, depth * 0.95)]
                draw.linear(A, pts[0], pts[2], [(0, AMBER, 0.45 * hall * spill), (1, AMBER, 0.0)])
                draw.poly(A, pts)
                A.fill()


def lock_closeup(ctx, f, center, scale=1.0, bolt=0.0, key_turn=0.0, light=1.0, t=0.0):
    """Close-up of the door edge and its lock (S10): the door's edge, the deadbolt sliding
    out into the strike plate (bolt 0..1) and the key turning (key_turn 0..1).
    center = middle of the lock; scale 1 -> the escutcheon is ~200 px tall.
    Light from the hallway rims the gap between the door and the frame."""
    s = scale
    cx, cy = center
    # door face (left) and frame (right), with the gap between
    gap_x = cx + 150 * s
    draw.rect(ctx, cx - 900 * s, cy - 1400 * s, gap_x, cy + 1400 * s)
    draw.fill(ctx, mix(INK, PAL.fog_at(0.8), 0.22))
    draw.rect(ctx, gap_x + 10 * s, cy - 1400 * s, cx + 900 * s, cy + 1400 * s)
    draw.fill(ctx, INK)
    # strike plate and the bolt
    draw.rect(ctx, gap_x + 10 * s, cy - 60 * s, gap_x + 70 * s, cy + 60 * s)
    draw.fill(ctx, mix(INK, PAL.fog_at(1.0), 0.35))
    bl = 90 * s * clamp(bolt)
    draw.rect(ctx, gap_x - 20 * s, cy - 22 * s, gap_x + bl, cy + 22 * s)
    draw.fill(ctx, INK)
    # escutcheon with keyhole (a hole you can see light through)
    draw.ellipse(ctx, (cx, cy), 46 * s, 100 * s)
    draw.fill(ctx, mix(INK, PAL.fog_at(1.0), 0.3))
    kh = [(cx - 10 * s, cy - 10 * s), (cx + 10 * s, cy - 10 * s), (cx + 6 * s, cy + 40 * s), (cx - 6 * s, cy + 40 * s)]
    draw.circle(ctx, (cx, cy - 18 * s), 15 * s)
    draw.poly(ctx, kh)
    draw.fill(ctx, mix(INK, AMBER, 0.5 * light))
    # the key: blade in the hole, bow outside, turning
    a = math.radians(-90 + 90 * clamp(key_turn))
    ca, sa = math.cos(a), math.sin(a)

    def K(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)
    bow = [K(40 * s, -46 * s), K(150 * s, -60 * s), K(170 * s, 0), K(150 * s, 60 * s), K(40 * s, 46 * s)]
    draw.capsule(ctx, K(0, 0), K(60 * s, 0), 14 * s, 14 * s)
    draw.smooth(ctx, bow, close=True, tension=0.4)
    draw.fill(ctx, INK)
    draw.circle(ctx, K(125 * s, 0), 18 * s)
    draw.fill(ctx, mix(INK, AMBER, 0.6 * light))
    with f.light(blur=4.0) as A:
        A.rectangle(gap_x, cy - 1400 * s, 10 * s, 2800 * s)
        draw.fill(A, HOT, 0.7 * light)
        glow(A, (gap_x + 5 * s, cy), 300 * s, AMBER, 0.12 * light)


# =========================================================================== red coat
def coat_hook(ctx, hook, scale=1.0, color=None):
    """A cast-iron wall hook; `hook` is the point where things hang."""
    s = scale
    x, y = hook
    draw.rect(ctx, x - 9 * s, y - 52 * s, x + 9 * s, y - 20 * s)
    ctx.new_sub_path()
    ctx.arc(x + 9 * s, y - 6 * s, 15 * s, math.pi * 0.95, math.pi * 2.2)
    ctx.arc_negative(x + 9 * s, y - 6 * s, 9 * s, math.pi * 2.2, math.pi * 0.95)
    ctx.close_path()
    draw.circle(ctx, (x + 23 * s, y - 14 * s), 5 * s)
    draw.fill(ctx, color or INK)


def red_coat(ctx, hook, scale=1.0, sway=0.0, t=0.0, color=None, hook_too=True):
    """Her red trench coat hanging from a hook by its collar loop (1.05 m = 360 px at
    scale 1): collar, sloping shoulders, sleeves hanging free of the body, a belt, the front
    edge and the folds as darker reds (no lines). sway: degrees of swing (after she brushes
    it). RED is a story colour: nothing else may use it."""
    s = scale
    col = color or RED
    x, y = hook[0] + 6 * s, hook[1] + 4 * s
    a = math.radians(sway + 0.8 * math.sin(t * 0.9))
    ca, sa = math.cos(a), math.sin(a)

    def P(px, py):
        return (x + px * ca * s - py * sa * s, y + px * sa * s + py * ca * s)

    def poly(pts, smooth=0.0):
        q = [P(px, py) for px, py in pts]
        if smooth:
            draw.smooth(ctx, q, close=True, tension=smooth)
        else:
            draw.poly(ctx, q)
    # body: collar loop, shoulders, a straight hang flaring to the hem
    poly([(-5, 0), (5, 0), (4, 14), (-4, 14)])
    body = [(-18, 10), (18, 10), (44, 22), (64, 40), (68, 70), (70, 150), (78, 250), (88, 330), (92, 362),
            (50, 368), (6, 364), (-40, 369), (-92, 362), (-88, 330), (-78, 250), (-70, 150), (-68, 70),
            (-64, 40), (-44, 22)]
    poly(body, 0.22)
    draw.fill(ctx, col)
    # folds: long darker bands down the skirt, the shadowed side away from the light
    for (fx, w0, w1) in ((-46, 6, 14), (-12, 4, 10), (30, 5, 13), (62, 4, 9)):
        poly([(fx - w0, 200), (fx + w0, 200), (fx + w1 + 3, 364), (fx - w1 + 3, 366)], 0.3)
    poly([(-92, 362), (-88, 330), (-78, 250), (-70, 150), (-68, 70), (-56, 70), (-60, 160), (-66, 260),
          (-72, 340), (-74, 364)], 0.25)
    draw.fill(ctx, mix(col, INK, 0.30))
    # front edge (overlapping placket) and the belt with its buckle
    poly([(4, 30), (14, 30), (16, 364), (6, 364)])
    poly([(-70, 178), (70, 178), (71, 196), (-71, 196)])
    draw.fill(ctx, mix(col, INK, 0.45))
    poly([(-12, 174), (12, 174), (12, 200), (-12, 200)])
    draw.fill(ctx, mix(col, INK, 0.65))
    poly([(-6, 180), (6, 180), (6, 194), (-6, 194)])
    draw.fill(ctx, col)
    # sleeves hang in front of the sides, a little apart from the body
    for sgn in (-1, 1):
        sl = [(sgn * 56, 40), (sgn * 72, 64), (sgn * 82, 160), (sgn * 86, 238), (sgn * 64, 246), (sgn * 58, 150),
              (sgn * 50, 70)]
        poly(sl, 0.3)
        draw.fill(ctx, mix(col, INK, 0.22 if sgn > 0 else 0.42))
        poly([(sgn * 66, 226), (sgn * 87, 222), (sgn * 88, 246), (sgn * 64, 250)])
        draw.fill(ctx, mix(col, INK, 0.5))
    # collar and lapels: the darkest red (turned up under the hook)
    for sgn in (-1, 1):
        poly([(sgn * 4, 10), (sgn * 30, 22), (sgn * 26, 56), (sgn * 12, 80), (sgn * 6, 40)])
    draw.fill(ctx, mix(col, INK, 0.55))
    if hook_too:
        coat_hook(ctx, hook, s)


# =========================================================================== match
def match_flame(f, t, tip, level=1.0, scale=1.0, par=1.0, seed=0, stick_angle=-60.0, stick=True):
    """A struck match (S07): the stick from her fingers to `tip` (world), a flickering
    teardrop flame with a hot core, and its small warm halo. level 0..1 (flare -> steady ->
    out). For the room's light use Apartment9.match_light at the same point."""
    if level <= 0.01:
        return
    s = scale
    fl = 0.85 + 0.15 * noise1(t * 11.0, seed) + 0.06 * math.sin(t * 37.0 + seed)
    lean = 6.0 * noise1(t * 3.0, seed + 2)
    hgt = (34 + 6 * noise1(t * 8.0, seed + 4)) * s * level
    x, y = tip
    with f.layer(par=par) as L:
        if stick:
            a = math.radians(stick_angle)
            draw.capsule(L, (x - math.cos(a) * 140 * s, y - math.sin(a) * 140 * s), (x, y), 2.4 * s, 3.2 * s)
            draw.fill(L, INK)
        pts = [(x - 7 * s, y), (x - 6 * s, y - hgt * 0.45), (x + lean * s * 0.6, y - hgt), (x + 6 * s, y - hgt * 0.45),
               (x + 7 * s, y)]
        draw.smooth(L, pts, close=True, tension=0.45)
        draw.fill(L, mix(AMBER, HOT, 0.6), min(1.0, level))
        draw.ellipse(L, (x, y - hgt * 0.28), 3.2 * s, hgt * 0.22)
        draw.fill(L, (1.0, 0.97, 0.9), min(1.0, level))
    with f.light(par=par, blur=4.0) as A:
        glow(A, (x, y - hgt * 0.4), 60 * s, HOT, 0.55 * level * fl)
        glow(A, (x, y - hgt * 0.4), 300 * s, AMBER, 0.16 * level * fl)
    with f.emit(par=par) as G:
        draw.circle(G, (x, y - hgt * 0.4), 9 * s)
        draw.fill(G, HOT, level * fl)


# =========================================================================== paper blood
def paper_blood(ctx, center, scale=1.0, seed=0, grow=1.0, angle=0.0, color=None):
    """A Saul Bass splash of RED cut paper: a jagged star body with a few flung drops.
    grow 0..1 lets it burst open (staggered)."""
    if grow <= 0:
        return
    s = scale * grow
    cx, cy = center
    n = 13
    pts = []
    for k in range(n * 2):
        a = math.radians(angle) + 2 * math.pi * k / (n * 2)
        if k % 2 == 0:
            r = (60 + 70 * hash01(seed, k, 1)) * s
        else:
            r = (26 + 14 * hash01(seed, k, 2)) * s
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.poly(ctx, draw.cut_paper(pts, seed=seed, amp=2.0 * s + 0.4, seg=(14.0 * s + 4, 30.0 * s + 6)))
    for k in range(6):
        g = clamp(grow * 1.4 - 0.4 - 0.08 * k)
        if g <= 0:
            continue
        a = math.radians(angle) + 2 * math.pi * hash01(seed, k, 5)
        d = (130 + 90 * hash01(seed, k, 6)) * scale * g
        r = (6 + 12 * hash01(seed, k, 7)) * scale
        draw.poly(ctx, draw.cut_circle((cx + d * math.cos(a), cy + d * math.sin(a)), r, seed=seed + k))
    draw.fill(ctx, color or RED)
