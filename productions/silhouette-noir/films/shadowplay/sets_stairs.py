"""SHADOW PLAY - the stairwell (S06) and the landing outside apartment 9 (S09, S10).

Stairwell   straight down a square spiral stair: flights on all four sides of an open well,
            radial balusters, a handrail spiralling into the dark, a dim bulb on every
            landing. The camera can descend (dolly), widen (zoom) and roll: the Vertigo shot.
            .path_point(u) places the small figure on the stairs.
Hallway     the landing outside apartment 9, side view: the door with its number, light
            under the door and through the keyhole, the stair going down with its banister,
            the hallway window where the police light floods in, a bare ceiling bulb.
"""
import math

import cairo

from engine import draw
from engine.core import W, H, clamp, lerp, hash01, noise1, fbm1, siren
from engine.palette import RED

from .sets_base import (PAL, INK, AMBER, HOT, BLUE, PX_M, mix, mul, layer_spec, opened, glow, glow_ellipse,
                        cone, rrect, texture_surface)


# =========================================================================== stairwell
class Stairwell:
    """Straight down a square stairwell (S06).

    Stairwell(center=(540, 960), scale=1.0, floors=7, well=1.0, outer=2.05, floor_h=3.0,
              treads=5, seed=0)
      center   world point of the vanishing point (the bottom of the well)
      well     half-width of the open well (m): the handrail runs round it
      outer    half-width of the shaft (m): the outer walls
      floors   storeys below the camera's landing; flights on all 4 sides of every storey

    Space is metres: x right, y down the screen, z = depth below the top landing. The
    camera hangs over the well, `cam_h` m above the top landing, looking straight down with
    focal `focal` px per metre at 1 m. `roll` (deg) turns the shaft about its axis.

    draw(f, t, cam_h=2.5, focal=520, roll=0, layer=None, bulbs=1.0, bottom=0.0, fade=11.0,
         flicker=0.3, hooks=None)
      bottom   light on the lobby floor at the bottom of the well (0 = into the dark)
      fade     depth (m) over which the shaft falls off into black
      hooks    {floor_index: fn(f, t)} drawn right after that storey (deep to near): put the
               small figure in the right place in the painter's order
    path_point(u, cam_h, focal, roll) -> dict(p, z, ppm, heading, floor): a point on the
         walking line, u = 0 at the top landing .. 1 at the bottom; ppm = world px per metre
         there (a person's shoulders are ~0.45 m); heading = screen angle (deg) of travel.
    vertigo(u, ...) -> (cam_h, focal): a dolly-zoom pair keeping storey `ref` the same size."""

    def __init__(self, center=(540.0, 960.0), scale=1.0, floors=7, well=1.0, outer=2.05, floor_h=3.0, treads=5,
                 seed=0):
        self.c = (float(center[0]), float(center[1]))
        self.s = float(scale)
        self.n = int(floors)
        self.a = float(well)
        self.b = float(outer)
        self.h = float(floor_h)
        self.treads = int(treads)
        self.seed = seed
        self.m = (self.a + self.b) / 2.0

    # ------------------------------------------------------------------ projection
    def project(self, x, y, z, cam_h=2.5, focal=520.0, roll=0.0):
        d = max(cam_h + z, 0.05)
        if roll:
            r = math.radians(roll)
            x, y = x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)
        k = self.s * focal / d
        return (self.c[0] + x * k, self.c[1] + y * k)

    def vertigo(self, u, cam0=4.0, cam1=1.2, ref=2, focal0=520.0):
        """Dolly-zoom: the camera sinks from cam0 to cam1 (u 0..1) while the focal length
        shrinks so storey `ref` keeps its size on screen: the well stretches away."""
        cam = lerp(cam0, cam1, u)
        zr = ref * self.h
        return cam, focal0 * (cam + zr) / (cam0 + zr)

    # ------------------------------------------------------------------ the walking line
    def _segments(self):
        """One storey's walking line: 4 flights (each drops h/4) and 4 flat corner turns."""
        a, m = self.a, self.m
        segs = []
        side = [((-a, -m), (a, -m)), ((m, -a), (m, a)), ((a, m), (-a, m)), ((-m, a), (-m, -a))]
        corner = [((a, -m), (m, -m), (m, -a)), ((m, a), (m, m), (a, m)), ((-a, m), (-m, m), (-m, a)),
                  ((-m, -a), (-m, -m), (-a, -m))]
        for k in range(4):
            segs.append(("flight", side[k][0], side[k][1], None))
            segs.append(("corner", corner[k][0], corner[k][2], corner[k][1]))
        return segs

    def path_point(self, u, cam_h=2.5, focal=520.0, roll=0.0):
        u = clamp(u)
        segs = self._segments()
        lens = []
        for (kind, p0, p1, pc) in segs:
            if kind == "flight":
                lens.append(math.hypot(p1[0] - p0[0], p1[1] - p0[1]))
            else:
                lens.append(math.hypot(pc[0] - p0[0], pc[1] - p0[1]) + math.hypot(p1[0] - pc[0], p1[1] - pc[1]))
        per = sum(lens)
        dist = u * per * self.n
        fl = min(int(dist // per), self.n - 1)
        rem = dist - fl * per
        z = fl * self.h
        x = y = 0.0
        hx, hy = 1.0, 0.0
        for k, ((kind, p0, p1, pc), L) in enumerate(zip(segs, lens)):
            flights_done = (k + 1) // 2
            if rem <= L or k == len(segs) - 1:
                v = clamp(rem / max(L, 1e-6))
                if kind == "flight":
                    x, y = lerp(p0[0], p1[0], v), lerp(p0[1], p1[1], v)
                    z += (flights_done + v) * self.h / 4
                    hx, hy = p1[0] - p0[0], p1[1] - p0[1]
                else:
                    la = math.hypot(pc[0] - p0[0], pc[1] - p0[1])
                    if v * L < la:
                        w = v * L / la
                        x, y = lerp(p0[0], pc[0], w), lerp(p0[1], pc[1], w)
                        hx, hy = pc[0] - p0[0], pc[1] - p0[1]
                    else:
                        w = (v * L - la) / max(L - la, 1e-6)
                        x, y = lerp(pc[0], p1[0], w), lerp(pc[1], p1[1], w)
                        hx, hy = p1[0] - pc[0], p1[1] - pc[1]
                    z += flights_done * self.h / 4
                break
            rem -= L
        p = self.project(x, y, z, cam_h, focal, roll)
        q = self.project(x + hx * 0.01, y + hy * 0.01, z, cam_h, focal, roll)
        ppm = self.s * focal / max(cam_h + z, 0.05)
        return dict(p=p, z=z, ppm=ppm, heading=math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])), floor=fl,
                    xy=(x, y))

    # ------------------------------------------------------------------ lighting
    def _bulbs(self):
        """One dim bulb per landing (on the outer wall at the corner where the storey starts)."""
        out = []
        for i in range(self.n + 1):
            k = i % 4
            sx, sy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[k]
            out.append((sx * (self.b - 0.15), sy * (self.b - 0.15), i * self.h - 2.3, i))
        return out

    def _light(self, x, y, z, t, bulbs, flicker, fade):
        e = 0.0
        for (bx, by, bz, i) in self._bulbs():
            d2 = (x - bx) ** 2 + (y - by) ** 2 + (z - bz) ** 2
            fl = 1.0 - flicker * 0.5 * (1 + noise1(t * 7.0 + i * 3.1, self.seed + 5)) * (hash01(self.seed, i, 3) < 0.35)
            e += 1.6 * fl / (0.6 + d2)
        e *= bulbs
        return e * math.exp(-z / max(fade, 0.1))

    # ------------------------------------------------------------------ drawing
    def draw(self, f, t, cam_h=2.5, focal=520.0, roll=0.0, layer=None, bulbs=1.0, bottom=0.0, fade=11.0,
             flicker=0.3, hooks=None):
        hooks = hooks or {}
        spec = layer_spec(layer)
        P = lambda x, y, z: self.project(x, y, z, cam_h, focal, roll)
        a, b, h = self.a, self.b, self.h
        n = self.n
        wall_c = mix(INK, PAL.fog_at(1.0), 0.16)
        with opened(f, spec) as L:
            # the bottom of the well: lobby floor tiles, lit or lost in the dark
            zb = n * h
            q = [P(-b, -b, zb), P(b, -b, zb), P(b, b, zb), P(-b, b, zb)]
            draw.poly(L, q)
            draw.fill(L, mix(INK, mul(AMBER, 0.5), 0.35 * bottom))
            if bottom > 0.02:
                k = 8
                for i in range(k):
                    for j in range(k):
                        if (i + j) % 2 == 0:
                            x0, y0 = -b + 2 * b * i / k, -b + 2 * b * j / k
                            x1, y1 = x0 + 2 * b / k, y0 + 2 * b / k
                            draw.poly(L, [P(x0, y0, zb), P(x1, y0, zb), P(x1, y1, zb), P(x0, y1, zb)])
                draw.fill(L, INK, 0.55)
        V = (cam_h, focal)
        for i in range(n - 1, -1, -1):
            with opened(f, spec) as L:
                self._storey(L, t, i, P, bulbs, flicker, fade, wall_c, V)
            if i in hooks:
                hooks[i](f, t)
        # the shaft walls above the top landing, rising past the camera to the frame edges
        with opened(f, spec) as L:
            z_top = max(-cam_h + 0.2, -h)
            for k in range(4):
                sx = ((0, -1), (1, 0), (0, 1), (-1, 0))[k]
                if sx[0] == 0:
                    ys = sx[1] * b
                    quad = [P(-b, ys, z_top), P(b, ys, z_top), P(b, ys, 0), P(-b, ys, 0)]
                else:
                    xs = sx[0] * b
                    quad = [P(xs, -b, z_top), P(xs, b, z_top), P(xs, b, 0), P(xs, -b, 0)]
                draw.poly(L, quad)
                e = self._light(sx[0] * b * 0.9, sx[1] * b * 0.9, z_top * 0.5, t, bulbs, flicker, fade)
                draw.linear(L, P(sx[0] * b, sx[1] * b, 0), P(sx[0] * b, sx[1] * b, z_top),
                            [(0, mix(wall_c, mul(AMBER, 0.55), clamp(0.45 * e)), 1), (1, INK, 1)])
                L.fill()
        # bulbs: hot cores and haloes, dimmer with depth
        with f.light(par=spec["par"], blur=6.0) as A:
            for (bx, by, bz, i) in self._bulbs():
                if bz < -cam_h + 0.3:
                    continue
                p = P(bx * 0.97, by * 0.97, bz)
                k = bulbs * math.exp(-max(bz, 0) / max(fade, 0.1))
                ppm = self.s * focal / max(cam_h + bz, 0.05)
                glow(A, p, 1.2 * ppm, AMBER, 0.30 * k)
                glow(A, p, 0.25 * ppm, HOT, 0.8 * k)
            if bottom > 0.02:
                glow(A, P(0, 0, n * h), self.s * focal / (cam_h + n * h) * b * 1.4, AMBER, 0.35 * bottom)
        with f.emit(par=spec["par"]) as G:
            for (bx, by, bz, i) in self._bulbs():
                if bz < -cam_h + 0.3:
                    continue
                p = P(bx * 0.97, by * 0.97, bz)
                ppm = self.s * focal / max(cam_h + bz, 0.05)
                draw.circle(G, p, max(1.0, 0.06 * ppm))
                draw.fill(G, HOT, bulbs * math.exp(-max(bz, 0) / max(fade, 0.1)))

    def _bar(self, L, P, V, a3, b3, width):
        """A round bar between two 3D points, its width true to depth at both ends."""
        cam_h, focal = V
        p0, p1 = P(*a3), P(*b3)
        w0 = 0.5 * width * self.s * focal / max(cam_h + a3[2], 0.05)
        w1 = 0.5 * width * self.s * focal / max(cam_h + b3[2], 0.05)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        d = math.hypot(dx, dy)
        if d < 1e-6:
            draw.circle(L, p0, max(w0, w1))
            return
        nx, ny = -dy / d, dx / d
        L.move_to(p0[0] + nx * w0, p0[1] + ny * w0)
        L.line_to(p1[0] + nx * w1, p1[1] + ny * w1)
        L.line_to(p1[0] - nx * w1, p1[1] - ny * w1)
        L.line_to(p0[0] - nx * w0, p0[1] - ny * w0)
        L.close_path()

    def _storey(self, L, t, i, P, bulbs, flicker, fade, wall_c, V):
        a, b, h, m = self.a, self.b, self.h, self.m
        z0 = i * h
        nt = self.treads
        # outer walls of this storey (seen as the band outside the stairs, darker deep down)
        for k in range(4):
            sx = ((0, -1), (1, 0), (0, 1), (-1, 0))[k]
            # the wall face at x/y = +-b from this storey's floor (z0 + h) up to z0
            if sx[0] == 0:
                ys = sx[1] * b
                quad = [P(-b, ys, z0), P(b, ys, z0), P(b, ys, z0 + h), P(-b, ys, z0 + h)]
            else:
                xs = sx[0] * b
                quad = [P(xs, -b, z0), P(xs, b, z0), P(xs, b, z0 + h), P(xs, -b, z0 + h)]
            e = self._light(sx[0] * b * 0.9, sx[1] * b * 0.9, z0 + h * 0.5, t, bulbs, flicker, fade)
            draw.poly(L, quad)
            draw.fill(L, mix(wall_c, mul(AMBER, 0.55), clamp(0.45 * e)) if e > 0 else wall_c)
            # dado rail line and a door frame on every storey's landing wall
        for k in range(4):
            fx, fy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[k]
            # corner landing (flat), at the level reached after k flights
            zc = z0 + (k + 1) * h / 4
            cx0, cy0 = min(fx * a, fx * b), min(fy * a, fy * b)
            cx1, cy1 = max(fx * a, fx * b), max(fy * a, fy * b)
            e = self._light(fx * m, fy * m, zc, t, bulbs, flicker, fade)
            draw.poly(L, [P(cx0, cy0, zc), P(cx1, cy0, zc), P(cx1, cy1, zc), P(cx0, cy1, zc)])
            draw.fill(L, self._tread_col(e))
        # flights: treads with lit nosings, then the inner stringer face, balusters, rail
        for k in range(4):
            zs = z0 + k * h / 4
            for j in range(nt):
                u0, u1 = j / nt, (j + 1) / nt
                zt = zs + (j + 1) * h / 4 / nt
                quad = self._tread_quad(k, u0, u1)
                e = self._light(*self._flight_xy(k, (u0 + u1) / 2, m), zt, t, bulbs, flicker, fade)
                pts = [P(x, y, zt) for (x, y) in quad]
                draw.poly(L, pts)
                draw.fill(L, self._tread_col(e))
                # nosing: a thin strip at the front edge of the tread catches the light
                nq = self._tread_quad(k, u1 - 0.12 / nt, u1)
                draw.poly(L, [P(x, y, zt) for (x, y) in nq])
                draw.fill(L, self._tread_col(e * 1.8 + 0.02))
        # the inner stringer: the stair's edge seen against the drop
        for k in range(4):
            zs = z0 + k * h / 4
            ze = zs + h / 4
            e0, e1 = self._flight_xy(k, 0.0, a), self._flight_xy(k, 1.0, a)
            pts = [P(e0[0], e0[1], zs), P(e1[0], e1[1], ze), P(e1[0], e1[1], ze + 0.32), P(e0[0], e0[1], zs + 0.32)]
            draw.poly(L, pts)
        draw.fill(L, INK)
        # balusters (radial bars in this view) and the handrail spiralling down
        ar = a - 0.04
        rh = 0.92
        cam_h = V[0]
        for k in range(4):
            zs = z0 + k * h / 4
            nb = int(2 * a / 0.13)
            for j in range(nb + 1):
                u = (j + 0.5) / (nb + 1)
                x, y = self._flight_xy(k, u, ar)
                zt = zs + h / 4 * u
                if zt - rh > -cam_h + 0.15:
                    self._bar(L, P, V, (x, y, zt), (x, y, zt - rh), 0.022)
            cx, cy = self._flight_xy(k, 1.0, ar)          # corner newel
            ze = zs + h / 4
            if ze - rh - 0.08 > -cam_h + 0.15:
                self._bar(L, P, V, (cx, cy, ze), (cx, cy, ze - rh - 0.08), 0.07)
        rail = []
        for k in range(4):
            zs = z0 + k * h / 4
            for u in (0.0, 1.0):
                x, y = self._flight_xy(k, u, ar)
                rail.append((x, y, zs + h / 4 * u - rh))
        nx_, ny_ = self._flight_xy(0, 0.0, ar)
        rail.append((nx_, ny_, z0 + h - rh))
        for p3a, p3b in zip(rail[:-1], rail[1:]):
            if min(p3a[2], p3b[2]) > -cam_h + 0.15:
                self._bar(L, P, V, p3a, p3b, 0.06)
        draw.fill(L, INK)

    def _flight_xy(self, k, u, r):
        """Point on flight k at fraction u, at distance r from the axis on the flight's side."""
        a = self.a
        if k == 0:
            return (lerp(-a, a, u), -r)
        if k == 1:
            return (r, lerp(-a, a, u))
        if k == 2:
            return (lerp(a, -a, u), r)
        return (-r, lerp(a, -a, u))

    def _tread_quad(self, k, u0, u1):
        a, b = self.a, self.b
        p = [self._flight_xy(k, u0, a), self._flight_xy(k, u1, a), self._flight_xy(k, u1, b), self._flight_xy(k, u0, b)]
        return p

    @staticmethod
    def _tread_col(e):
        base = mix(INK, PAL.fog_at(1.0), 0.10)
        return mix(base, mix(mul(AMBER, 0.62), HOT, 0.15), clamp(0.55 * e))


# =========================================================================== hallway
class Hallway:
    """The landing outside apartment 9, seen side-on (S09 from outside, S10): the door
    with a brass 9, light under it and through its keyhole, the banister going down to the
    right, the hallway window on the left (police light floods in), a bare ceiling bulb.

    Hallway(origin=(540, 1640), scale=1.0)    origin = floor point at the door's centre
      .door_rect           world rect of the door leaf
      .knob, .keyhole      world points
      .floor_y             world y of the landing floor
      .stair_point(u)      a point on the stair treads going down (u 0 = landing .. 1)
      .window_rect         world rect of the hallway window
    draw(f, t, layer=None, room=0.0, room_flicker=0.0, bulb=0.35, police=0.0, door_shake=0.0,
         feet=(), number=True)
      room          light inside apartment 9 (leaks under the door, through the keyhole)
      room_flicker  0..1: the lamp crashing inside (the leak stutters and its angle whirls)
      bulb          the hallway's bare bulb (0 = off)
      police        blue/red flood through the window (siren pattern)
      door_shake    0..1: someone hammering from inside (the leaf jumps in its frame)
      feet          x offsets (world px from the door centre) of feet blocking the leak"""

    def __init__(self, origin=(540.0, 1640.0), scale=1.0):
        self.o = (float(origin[0]), float(origin[1]))
        self.s = s = float(scale)
        ox, oy = self.o
        self.floor_y = oy
        dw, dh = 0.92 * PX_M * s, 2.12 * PX_M * s
        self.door_rect = (ox - dw / 2, oy - dh, ox + dw / 2, oy)
        self.knob = (ox + dw / 2 - 40 * s, oy - dh * 0.47)
        self.keyhole = (self.knob[0], self.knob[1] + 34 * s)
        self.window_rect = (ox - 820 * s, oy - 1010 * s, ox - 440 * s, oy - 190 * s)
        self.bulb_p = (ox - 120 * s, oy - 1230 * s)
        self.ceiling_y = oy - 1290 * s

    def stair_point(self, u):
        """Point on the stair nosings going down to the right (u 0 = top .. 1 = 8 steps down)."""
        s = self.s
        x0 = self.o[0] + 330 * s
        return (x0 + u * 8 * 0.27 * PX_M * s, self.floor_y + u * 8 * 0.18 * PX_M * s)

    def draw(self, f, t, layer=None, room=0.0, room_flicker=0.0, bulb=0.35, police=0.0, door_shake=0.0, feet=(),
             number=True):
        spec = layer_spec(layer)
        par = spec["par"]
        s = self.s
        ox, oy = self.o
        dx0, dy0, dx1, dy1 = self.door_rect
        wx0, wy0, wx1, wy1 = self.window_rect
        b, r = siren(t, rate=1.6)
        leak = room * self._room_flicker(t, room_flicker)
        shake = door_shake * (math.sin(t * 61.0) * 0.6 + noise1(t * 23.0, 4) * 0.4)
        with opened(f, spec) as L:
            # wall: dark wallpaper above a wainscot
            wall = mix(INK, PAL.fog_at(1.0), 0.20)
            L.rectangle(ox - 3000 * s, self.ceiling_y, 6000 * s, oy - self.ceiling_y)
            draw.fill(L, wall)
            # wallpaper stripes (tone only)
            x = ox - 3000 * s
            while x < ox + 3000 * s:
                L.rectangle(x, self.ceiling_y, 26 * s, oy - 330 * s - self.ceiling_y)
                x += 74 * s
            draw.fill(L, INK, 0.16)
            L.rectangle(ox - 3000 * s, oy - 330 * s, 6000 * s, 330 * s)
            draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.12))
            draw.rect(L, ox - 3000 * s, oy - 340 * s, ox + 3000 * s, oy - 322 * s)       # dado rail
            draw.rect(L, ox - 3000 * s, oy - 34 * s, ox + 3000 * s, oy)                  # skirting
            draw.rect(L, ox - 3000 * s, self.ceiling_y - 400 * s, ox + 3000 * s, self.ceiling_y + 26 * s)
            draw.fill(L, INK)
            # floor
            L.rectangle(ox - 3000 * s, oy, 6000 * s, 900 * s)
            draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.07))
            # the window: night outside, police light in it
            self._window(L, t, b, r, police)
            # the door, its casing and the number
            cw = 30 * s
            draw.rect(L, dx0 - cw, dy0 - cw, dx1 + cw, oy)
            draw.fill(L, INK)
            L.save()
            L.translate(shake * 3 * s, 0)
            draw.rect(L, dx0, dy0, dx1, dy1)
            draw.fill(L, mix(INK, PAL.fog_at(0.8), 0.24))
            for (u0, u1, v0, v1) in ((0.14, 0.46, 0.06, 0.40), (0.54, 0.86, 0.06, 0.40),
                                     (0.14, 0.46, 0.50, 0.92), (0.54, 0.86, 0.50, 0.92)):
                draw.rect(L, lerp(dx0, dx1, u0), lerp(dy0, dy1, v0), lerp(dx0, dx1, u1), lerp(dy0, dy1, v1))
            draw.fill(L, INK, 0.45)
            kx, ky = self.knob
            draw.circle(L, (kx, ky), 13 * s)
            draw.ellipse(L, (kx, ky + 34 * s), 10 * s, 24 * s)
            draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.45))
            kh = self.keyhole
            draw.circle(L, (kh[0], kh[1] - 5 * s), 4.5 * s)
            draw.poly(L, [(kh[0] - 2.5 * s, kh[1] - 3 * s), (kh[0] + 2.5 * s, kh[1] - 3 * s), (kh[0] + 4 * s, kh[1] + 10 * s),
                          (kh[0] - 4 * s, kh[1] + 10 * s)])
            draw.fill(L, mix(INK, HOT, clamp(leak)))
            if number:
                nc = ((dx0 + dx1) / 2, dy0 + (dy1 - dy0) * 0.22)
                draw.ellipse(L, nc, 34 * s, 46 * s)
                draw.fill(L, mix(INK, AMBER, 0.42))
                # the 9: a ring and a tail, cut out of the brass plate
                L.new_path()
                L.arc(nc[0], nc[1] - 10 * s, 12 * s, 0, 2 * math.pi)
                L.new_sub_path()
                L.arc_negative(nc[0], nc[1] - 10 * s, 6 * s, 2 * math.pi, 0)
                draw.fill(L, INK)
                draw.capsule(L, (nc[0] + 9 * s, nc[1] - 6 * s), (nc[0] + 2 * s, nc[1] + 26 * s), 3.2 * s, 3.2 * s)
                draw.fill(L, INK)
                draw.circle(L, (nc[0], nc[1] - 54 * s), 5 * s)                      # peephole
                draw.fill(L, INK)
            L.restore()
            # banister and stair going down to the right
            self._stairs(L)
            # the bare bulb on its flex
            bp = self.bulb_p
            draw.rect(L, bp[0] - 1.2 * s, self.ceiling_y, bp[0] + 1.2 * s, bp[1] - 18 * s)
            draw.rect(L, bp[0] - 7 * s, bp[1] - 26 * s, bp[0] + 7 * s, bp[1] - 10 * s)
            draw.fill(L, INK)
            draw.ellipse(L, (bp[0], bp[1]), 11 * s, 14 * s)
            draw.fill(L, mix((0.05, 0.05, 0.06), HOT, clamp(bulb)))
        # light
        with f.light(par=par, blur=5.0) as A:
            if leak > 0.01:
                self._leak(A, t, leak, room_flicker, feet)
            if bulb > 0.01:
                glow(A, self.bulb_p, 900 * s, AMBER, 0.16 * bulb)
                glow(A, self.bulb_p, 160 * s, HOT, 0.45 * bulb)
                # pool on the floor under it
                glow_ellipse(A, (self.bulb_p[0], oy + 20 * s), 700 * s, 70 * s, AMBER, 0.20 * bulb)
            if police > 0:
                self._police(A, b, r, police)
        with f.emit(par=par) as G:
            if bulb > 0.01:
                draw.circle(G, self.bulb_p, 12 * s)
                draw.fill(G, HOT, bulb)
            if leak > 0.01:
                draw.circle(G, self.keyhole, 6 * s)
                draw.fill(G, HOT, leak)
                G.rectangle(dx0, oy - 6 * s, dx1 - dx0, 6 * s)
                draw.fill(G, HOT, 0.5 * leak)

    @staticmethod
    def _room_flicker(t, k):
        if k <= 0:
            return 1.0
        v = 0.55 + 0.45 * math.sin(t * 37.0) * noise1(t * 9.0, 11)
        if noise1(t * 5.0, 3) > 0.35:
            v *= 0.15
        return lerp(1.0, clamp(v, 0.0, 1.2), k)

    def _leak(self, A, t, leak, flick, feet):
        s = self.s
        dx0, dy0, dx1, dy1 = self.door_rect
        oy = self.floor_y
        n = 36
        for k in range(n):
            u0, u1 = k / n, (k + 1) / n
            xm = lerp(dx0, dx1, (u0 + u1) / 2) - (dx0 + dx1) / 2
            if any(abs(xm - fx) < 30 * s for fx in feet):
                continue
            A.rectangle(lerp(dx0, dx1, u0), oy - 5 * s, (dx1 - dx0) / n, 5 * s)
        draw.fill(A, HOT, 0.95 * leak)
        # the fan of light on the hallway floor, in slices so feet cut shadows out of it;
        # it whirls when the lamp falls inside
        sk = 60 * s * math.sin(t * 6.0) * flick
        cxd = (dx0 + dx1) / 2
        for k in range(n):
            u0, u1 = k / n, (k + 1) / n
            xa, xb = lerp(dx0 + 6 * s, dx1 - 6 * s, u0), lerp(dx0 + 6 * s, dx1 - 6 * s, u1)
            fa = lerp(dx0 - 90 * s, dx1 + 90 * s, u0) + sk
            fb = lerp(dx0 - 90 * s, dx1 + 90 * s, u1) + sk
            if any(abs((xa + xb) / 2 - cxd - fx) < 30 * s for fx in feet):
                continue
            A.move_to(xa, oy)
            A.line_to(xb, oy)
            A.line_to(fb, oy + 110 * s)
            A.line_to(fa, oy + 110 * s)
            A.close_path()
        draw.linear(A, (0, oy), (0, oy + 110 * s), [(0, AMBER, 0.40 * leak), (1, AMBER, 0.0)])
        A.fill()
        # keyhole beam
        kh = self.keyhole
        glow(A, kh, 26 * s, HOT, 0.8 * leak)

    def _window(self, L, t, b, r, police):
        s = self.s
        x0, y0, x1, y1 = self.window_rect
        draw.linear(L, (0, y0), (0, y1), [(0, mix(PAL.sky_bottom, PAL.fog_at(1.0), 0.4), 1),
                                          (1, mix(INK, PAL.fog_at(1.0), 0.3), 1)])
        L.rectangle(x0, y0, x1 - x0, y1 - y0)
        L.fill()
        if police > 0:
            draw.linear(L, (0, y1), (0, y0), [(0, BLUE, 0.85 * b * police), (1, BLUE, 0.25 * b * police)])
            L.rectangle(x0, y0, x1 - x0, y1 - y0)
            L.fill()
            draw.linear(L, (0, y1), (0, y0), [(0, RED, 0.7 * r * police), (1, RED, 0.2 * r * police)])
            L.rectangle(x0, y0, x1 - x0, y1 - y0)
            L.fill()
        # sash, mullions, sill, the casing
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for (a0, a1, c0, c1) in ((x0 - 26 * s, x1 + 26 * s, y0 - 26 * s, y0), (x0 - 26 * s, x0, y0, y1),
                                 (x1, x1 + 26 * s, y0, y1), (x0 - 40 * s, x1 + 40 * s, y1, y1 + 22 * s),
                                 (x0, x1, cy - 9 * s, cy + 9 * s), (cx - 6 * s, cx + 6 * s, y0, y1)):
            draw.rect(L, a0, c0, a1, c1)
        draw.fill(L, INK)

    def _police(self, A, b, r, k):
        """The window's light falls across the floor and up the door wall as slanted panes."""
        s = self.s
        x0, y0, x1, y1 = self.window_rect
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        oy = self.floor_y
        for col, v in ((BLUE, b), (RED, r)):
            if v <= 0.01:
                continue
            a = 0.32 * v * k
            # glow in the air by the window and a wash over the wall, the door, everything
            glow(A, (cx, cy), 700 * s, col, 0.20 * v * k)
            glow(A, (cx + 300 * s, cy + 200 * s), 1500 * s, col, 0.10 * v * k)
            # the four panes thrown on the floor, sheared away from the window
            for (u0, u1, w0, w1) in ((0, 0.5, 0, 0.5), (0.5, 1, 0, 0.5), (0, 0.5, 0.5, 1), (0.5, 1, 0.5, 1)):
                pts = []
                for (u, w) in ((u0, w0), (u1, w0), (u1, w1), (u0, w1)):
                    wx = lerp(x0, x1, u) + 8 * s * (1 if u < 0.5 else -1)
                    wy = lerp(y0, y1, w)
                    # a high source outside: the pattern lands on the floor, shifted right
                    fx = wx + (oy - wy) * 0.55 + 380 * s
                    fy = oy + (wy - y0) / (y1 - y0) * 160 * s + 10 * s
                    pts.append((fx, fy))
                draw.poly(A, pts)
            draw.fill(A, col, a)

    def _stairs(self, L):
        s = self.s
        ox, oy = self.o
        x0 = ox + 330 * s
        tr, ri = 0.27 * PX_M * s, 0.18 * PX_M * s
        # the treads going down (a sawtooth silhouette against the stairwell's dark)
        pts = [(x0, oy)]
        x, y = x0, oy
        for k in range(8):
            pts += [(x, y + ri), (x + tr, y + ri)]
            x += tr
            y += ri
        pts += [(x + 400 * s, y), (x + 400 * s, oy + 900 * s), (x0, oy + 900 * s)]
        draw.poly(L, pts)
        draw.fill(L, INK)
        # the drop of the stairwell behind the banister: darker than the wall
        L.rectangle(x0, self.ceiling_y, 3000 * s, oy - self.ceiling_y)
        draw.fill(L, INK, 0.45)
        # newel post, handrail, balusters
        rail_h = 0.92 * PX_M * s
        npx = x0 - 10 * s
        draw.rect(L, npx - 16 * s, oy - rail_h - 40 * s, npx + 16 * s, oy)
        draw.circle(L, (npx, oy - rail_h - 52 * s), 20 * s)
        draw.rect(L, npx - 20 * s, oy - rail_h - 40 * s, npx + 20 * s, oy - rail_h - 28 * s)
        a = (npx, oy - rail_h)
        bpt = (x + 0 * s, y - rail_h)
        draw.capsule(L, a, bpt, 7 * s, 7 * s)
        k = 0
        xx = x0 + tr * 0.3
        while xx < x - 4 * s:
            u = (xx - x0) / max(x - x0, 1)
            yr = lerp(oy, y, u)
            step_y = oy + ri * (math.floor((xx - x0) / tr) + 1)
            draw.rect(L, xx - 3.2 * s, lerp(a[1], bpt[1], u), xx + 3.2 * s, step_y)
            xx += tr / 2.0
            k += 1
        draw.fill(L, INK)
