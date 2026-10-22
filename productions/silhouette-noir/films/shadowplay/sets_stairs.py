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
from engine.core import clamp, lerp, hash01, noise1, siren
from engine.palette import RED

from .sets_base import (PAL, INK, AMBER, HOT, BLUE, RAIN, PX_M, mix, mul, layer_spec, opened, glow, glow_ellipse)


# =========================================================================== stairwell
class Stairwell:
    """Straight down a square stairwell (S06).

    Stairwell(center=(540, 960), scale=1.0, floors=7, well=1.0, outer=2.05, floor_h=3.0,
              treads=5, seed=0, stretch=0.0)
      center   world point of the vanishing point (the bottom of the well)
      well     half-width of the open well (m): the handrail runs round it
      outer    half-width of the shaft (m): the outer walls
      stretch  m added to the well's half-length in y (the flights along y get longer):
               ~1.2 makes the shaft fill a 9:16 frame
      floors   storeys below the camera's landing; flights on all 4 sides of every storey

    Space is metres: x right, y down the screen, z = depth below the top landing. The
    camera hangs over the well, `cam_h` m above the top landing, looking straight down with
    focal `focal` px per metre at 1 m. `roll` (deg) turns the shaft about its axis.

    draw(f, t, cam_h=2.5, focal=520, roll=0, layer=None, bulbs=1.0, bottom=0.0, fade=11.0,
         flicker=0.3, hooks=None, windows=1.0, police=0.0)
      bottom   light on the lobby floor at the bottom of the well (0 = into the dark)
      windows  the tall stair windows on the long wall (night outside, rain-blue)
      police   0..1 the siren reaching the windows (blue/red)
      fade     depth (m) over which the shaft falls off into black
      hooks    {floor_index: fn(f, t)} drawn right after that storey (deep to near): put the
               small figure in the right place in the painter's order
    path_point(u, cam_h, focal, roll) -> dict(p, z, ppm, heading, floor): a point on the
         walking line, u = 0 at the top landing .. 1 at the bottom; ppm = world px per metre
         there (a person's shoulders are ~0.45 m); heading = screen angle (deg) of travel.
    vertigo(u, ...) -> (cam_h, focal): a dolly-zoom pair keeping storey `ref` the same size."""

    def __init__(self, center=(540.0, 960.0), scale=1.0, floors=7, well=1.0, outer=2.05, floor_h=3.0, treads=5,
                 seed=0, stretch=0.0):
        self.c = (float(center[0]), float(center[1]))
        self.s = float(scale)
        self.n = int(floors)
        self.a = float(well)
        self.b = float(outer)
        self.h = float(floor_h)
        self.treads = int(treads)
        self.seed = seed
        self.m = (self.a + self.b) / 2.0
        self.dy = max(0.0, float(stretch))

    # ------------------------------------------------------------------ projection
    def _ymap(self, y):
        """The stretch: a translation outside the well, a uniform scale across it."""
        d, a = self.dy, self.a
        if d == 0.0:
            return y
        if y >= a:
            return y + d
        if y <= -a:
            return y - d
        return y * (a + d) / a

    def project(self, x, y, z, cam_h=2.5, focal=520.0, roll=0.0):
        d = max(cam_h + z, 0.05)
        y = self._ymap(y)
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
        Y = self._ymap
        for (kind, p0, p1, pc) in segs:
            if kind == "flight":
                lens.append(math.hypot(p1[0] - p0[0], Y(p1[1]) - Y(p0[1])))
            else:
                lens.append(math.hypot(pc[0] - p0[0], Y(pc[1]) - Y(p0[1])) + math.hypot(p1[0] - pc[0], Y(p1[1]) - Y(pc[1])))
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
                    la = math.hypot(pc[0] - p0[0], Y(pc[1]) - Y(p0[1]))
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

    def _flick(self, t, i, flicker):
        return 1.0 - flicker * 0.5 * (1 + noise1(t * 7.0 + i * 3.1, self.seed + 5)) * (hash01(self.seed, i, 3) < 0.35)

    def _lamps(self, t, flicker):
        """(x, stretched y, z, flicker level) of every bulb at time t (cached per t)."""
        key = (t, flicker)
        if getattr(self, "_lamps_key", None) != key:
            self._lamps_key = key
            self._lamps_val = [(bx, self._ymap(by), bz, self._flick(t, i, flicker)) for (bx, by, bz, i) in self._bulbs()]
        return self._lamps_val

    def _light(self, x, y, z, t, bulbs, flicker, fade):
        e = 0.0
        y = self._ymap(y)
        for (bx, by, bz, fl) in self._lamps(t, flicker):
            d2 = (x - bx) ** 2 + (y - by) ** 2 + (z - bz) ** 2
            e += 1.9 * fl / (0.32 + d2)
        e *= bulbs
        return e * math.exp(-z / max(fade, 0.1))

    # ------------------------------------------------------------------ drawing
    def draw(self, f, t, cam_h=2.5, focal=520.0, roll=0.0, layer=None, bulbs=1.0, bottom=0.0, fade=11.0,
             flicker=0.3, hooks=None, windows=1.0, police=0.0):
        hooks = hooks or {}
        self._win = (windows, police, t)
        spec = layer_spec(layer)
        P = lambda x, y, z: self.project(x, y, z, cam_h, focal, roll)
        a, b, h = self.a, self.b, self.h
        n = self.n
        wall_c = mix(INK, mix(PAL.fog_at(1.0), AMBER, 0.22), 0.12)
        with opened(f, spec) as L:
            # the bottom of the well: lobby floor tiles, lit or lost in the dark
            zb = n * h
            q = [P(-b, -b, zb), P(b, -b, zb), P(b, b, zb), P(-b, b, zb)]
            draw.poly(L, q)
            draw.fill(L, mix(INK, mix(AMBER, HOT, 0.2), 0.5 * bottom))
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
        # all the walls in one soft, half-res pass (smooth plaster; it halves the cost), the
        # shaft walls above the top landing rising past the camera to the frame edges
        wspec = dict(spec)
        wspec["blur"] = max(spec.get("blur", 0.0), 4.5)
        with opened(f, wspec) as L:
            for i in range(n - 1, -1, -1):
                self._storey_walls(L, t, i, P, bulbs, flicker, fade, wall_c, V)
            z_top = max(-cam_h + 0.2, -h)
            self._wall_mesh(L, P, z_top, 0.0, t, bulbs, flicker, fade, wall_c, nu=6, nv=2, dark_near=0.85)
        for i in range(n - 1, -1, -1):
            with opened(f, spec) as L:
                self._storey(L, t, i, P, bulbs, flicker, fade, V)
            if i in hooks:
                hooks[i](f, t)
        # bulbs: hot cores and haloes, dimmer with depth
        with f.light(par=spec["par"], blur=6.0) as A:
            for (bx, by, bz, i) in self._bulbs():
                if bz < -cam_h + 0.3:
                    continue
                p = P(bx * 0.97, by * 0.97, bz)
                k = bulbs * math.exp(-max(bz, 0) / max(fade, 0.1))
                ppm = self.s * focal / max(cam_h + bz, 0.05)
                glow(A, p, 2.4 * ppm, AMBER, 0.10 * k)          # the dusty air round it
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

    def _wall_light(self, x, y, z, nx, ny, t, bulbs, flicker, fade):
        """Light on a wall point (unstretched coords) with the wall's inward normal."""
        e = 0.0
        ym = self._ymap(y)
        for (bx, by, bz, fl) in self._lamps(t, flicker):
            dx, dy, dz = bx - x, by - ym, bz - z
            d2 = dx * dx + dy * dy + dz * dz
            lam = max(0.0, (dx * nx + dy * ny) / math.sqrt(d2 + 1e-6))
            e += 2.6 * fl * (0.25 + 0.75 * lam) / (0.32 + d2)
        return bulbs * e * math.exp(-max(z, 0.0) / max(fade, 0.1))

    def _wall_mesh(self, L, P, za, zb, t, bulbs, flicker, fade, wall_c, nu=6, nv=3, dark_near=0.0):
        """The four shaft walls between depths za and zb, shaded per vertex by every bulb
        (a Coons-patch mesh): pools of light, dark between, falling off with depth."""
        b = self.b
        lit = mix(mul(AMBER, 0.72), HOT, 0.12)
        mesh = cairo.MeshPattern()
        sides = (((-b, -b), (b, -b), (0, 1)), ((b, -b), (b, b), (-1, 0)), ((b, b), (-b, b), (0, -1)),
                 ((-b, b), (-b, -b), (1, 0)))
        for (c0, c1, (nx, ny)) in sides:
            grid = []
            for vj in range(nv + 1):
                z = lerp(za, zb, vj / nv)
                row = []
                for ui in range(nu + 1):
                    x, y = lerp(c0[0], c1[0], ui / nu), lerp(c0[1], c1[1], ui / nu)
                    e = self._wall_light(x, y, z, nx, ny, t, bulbs, flicker, fade)
                    col = mix(wall_c, lit, clamp(0.8 * e) ** 1.2)
                    if dark_near > 0:
                        # walls right by the lens: out of the light's reach and out of focus
                        col = mix(col, INK, dark_near * (1.0 - vj / nv))
                    row.append((P(x, y, z), col))
                grid.append(row)
            for vj in range(nv):
                for ui in range(nu):
                    q = (grid[vj][ui], grid[vj][ui + 1], grid[vj + 1][ui + 1], grid[vj + 1][ui])
                    mesh.begin_patch()
                    mesh.move_to(*q[0][0])
                    for (p, _) in q[1:]:
                        mesh.line_to(*p)
                    for ci, (_, col) in enumerate(q):
                        mesh.set_corner_color_rgb(ci, *col[:3])
                    mesh.end_patch()
            L.move_to(*P(c0[0], c0[1], za))
            L.line_to(*P(c1[0], c1[1], za))
            L.line_to(*P(c1[0], c1[1], zb))
            L.line_to(*P(c0[0], c0[1], zb))
            L.close_path()
        L.set_source(mesh)
        L.fill()

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

    def _storey_walls(self, L, t, i, P, bulbs, flicker, fade, wall_c, V):
        """Storey i's four walls: plaster lit by the bulbs, the stair window, the doors.
        They never overlap a deeper storey on screen, so all walls go down first."""
        a, b, h, m = self.a, self.b, self.h, self.m
        z0 = i * h
        wall_c = mix(INK, wall_c, 0.35 + 0.65 * math.exp(-z0 / max(0.7 * fade, 0.1)))     # the shaft darkens down
        cam_h, focal = V
        # outer walls: dark plaster with a pool of light round each bulb that reaches them
        faces = []
        for k in range(4):
            sx = ((0, -1), (1, 0), (0, 1), (-1, 0))[k]
            if sx[0] == 0:
                ys = sx[1] * b
                faces.append([P(-b, ys, z0), P(b, ys, z0), P(b, ys, z0 + h), P(-b, ys, z0 + h)])
            else:
                xs = sx[0] * b
                faces.append([P(xs, -b, z0), P(xs, b, z0), P(xs, b, z0 + h), P(xs, -b, z0 + h)])
        self._wall_mesh(L, P, z0, z0 + h, t, bulbs, flicker, fade, wall_c, nu=(6, 4, 3)[min(i, 2)],
                        nv=(3, 2, 1)[min(i, 2)])
        for (bx, by, bz, j) in self._bulbs():
            if not (z0 - 0.2 <= bz <= z0 + h) or bz < -cam_h + 0.3:
                continue
            e = bulbs * self._flick(t, j, flicker) * math.exp(-max(bz, 0.0) / max(fade, 0.1))
            if e <= 0.01:
                continue
            c = P(bx, by, bz)
            r = 1.7 * self.s * focal / max(cam_h + bz + 0.8, 0.05)
            for q in faces:
                draw.poly(L, q)
            draw.radial(L, c, 0, r, [(0, mix(AMBER, HOT, 0.4), 0.55 * clamp(e)), (0.35, AMBER, 0.12 * clamp(e)),
                                     (1, AMBER, 0)])
            L.fill()
        # a tall window on the long wall: rain-blue night, mullions, a cold pool round it
        wk, pol, tw = getattr(self, "_win", (1.0, 0.0, t))
        if wk > 0.01:
            dz = math.exp(-z0 / max(fade, 0.1))
            col = mix(PAL.fog_at(1.0), RAIN, 0.35)
            if pol > 0:
                bb, rr = siren(tw + i * 0.13, rate=1.6)
                col = mix(col, mix(BLUE, RED, rr / max(bb + rr, 1e-3)), clamp(pol * max(bb, rr)))
            zt_, zb_ = z0 + 0.55, z0 + 2.35
            c = P(0.0, b, z0 + 1.45)
            r = 1.9 * self.s * focal / max(cam_h + z0 + 1.45, 0.05)
            for q in faces:
                draw.poly(L, q)
            draw.radial(L, c, 0, r, [(0, mix(wall_c, col, 0.35 * wk * dz), 1), (1, wall_c, 0)])
            L.fill()
            wq = [P(-0.45, b, zt_), P(0.45, b, zt_), P(0.45, b, zb_), P(-0.45, b, zb_)]
            draw.poly(L, wq)
            draw.linear(L, P(0.0, b, zt_), P(0.0, b, zb_), [(0, mix(INK, col, clamp(0.55 * wk * dz)), 1),
                                                            (1, mix(INK, col, clamp(0.22 * wk * dz)), 1)])
            L.fill()
            # rain running down the glass
            for j in range(7):
                xr = -0.40 + 0.80 * hash01(self.seed + i, j, 61)
                zr = lerp(zt_, zb_, 0.15 + 0.6 * hash01(self.seed + i, j, 62))
                draw.poly(L, [P(xr - 0.008, b, zr), P(xr + 0.008, b, zr), P(xr + 0.008, b, zr + 0.35), P(xr - 0.008, b, zr + 0.35)])
            draw.fill(L, col, 0.35 * wk * dz)
            for (xa, xb, za, zb2) in ((-0.03, 0.03, zt_, zb_), (-0.45, 0.45, z0 + 1.15, z0 + 1.2),
                                      (-0.45, 0.45, z0 + 1.75, z0 + 1.8)):
                draw.poly(L, [P(xa, b, za), P(xb, b, za), P(xb, b, zb2), P(xa, b, zb2)])
            draw.fill(L, INK, 0.9)
        # the floor landing's two apartment doors (corner -1,-1 at the bottom of this storey),
        # some with light under them
        zc = z0 + h
        for side in (0, 1):
            if side == 0:
                q = [P(-b + 0.14, -b, zc - 2.05), P(-a - 0.08, -b, zc - 2.05), P(-a - 0.08, -b, zc), P(-b + 0.14, -b, zc)]
                g = [P(-b + 0.14, -b, zc - 0.03), P(-a - 0.08, -b, zc - 0.03), P(-a - 0.08, -b, zc), P(-b + 0.14, -b, zc)]
            else:
                q = [P(-b, -b + 0.14, zc - 2.05), P(-b, -a - 0.08, zc - 2.05), P(-b, -a - 0.08, zc), P(-b, -b + 0.14, zc)]
                g = [P(-b, -b + 0.14, zc - 0.03), P(-b, -a - 0.08, zc - 0.03), P(-b, -a - 0.08, zc), P(-b, -b + 0.14, zc)]
            draw.poly(L, q)
            draw.fill(L, INK, 0.45)
            if hash01(self.seed, i, 40 + side) < 0.5:
                draw.poly(L, g)
                draw.fill(L, mix(AMBER, HOT, 0.3), 0.8 * math.exp(-zc / max(fade, 0.1)))

    def _storey(self, L, t, i, P, bulbs, flicker, fade, V):
        a, b, h, m = self.a, self.b, self.h, self.m
        z0 = i * h
        cam_h, focal = V
        nt = self.treads
        if i == 0:
            e = self._light(-m, -m, 0.0, t, bulbs, flicker, fade)
            draw.poly(L, [P(-b, -b, 0.0), P(-a, -b, 0.0), P(-a, -a, 0.0), P(-b, -a, 0.0)])
            draw.fill(L, self._tread_col(e))
        # corner landings (flat), each at the level its flight arrives at
        for k in range(4):
            fx, fy = ((1, -1), (1, 1), (-1, 1), (-1, -1))[k]
            zc = z0 + (k + 1) * h / 4
            cx0, cy0 = min(fx * a, fx * b), min(fy * a, fy * b)
            cx1, cy1 = max(fx * a, fx * b), max(fy * a, fy * b)
            e = self._light(fx * m, fy * m, zc, t, bulbs, flicker, fade)
            draw.poly(L, [P(cx0, cy0, zc), P(cx1, cy0, zc), P(cx1, cy1, zc), P(cx0, cy1, zc)])
            draw.fill(L, self._tread_col(e))
        # flights: treads with lit nosings (more treads on the long sides of a stretched well)
        for k in range(4):
            zs = z0 + k * h / 4
            nk = nt if k % 2 == 0 else max(nt, int(round(nt * (a + self.dy) / a)))
            for j in range(nk):
                u0, u1 = j / nk, (j + 1) / nk
                zt = zs + (j + 1) * h / 4 / nk
                quad = self._tread_quad(k, u0, u1)
                e = self._light(*self._flight_xy(k, (u0 + u1) / 2, m), zt, t, bulbs, flicker, fade)
                draw.poly(L, [P(x, y, zt) for (x, y) in quad])
                draw.fill(L, self._tread_col(e))
                if i < 4:
                    # nosing: a thin strip at the front edge of the tread catches the light
                    nq = self._tread_quad(k, u1 - 0.12 / nk, u1)
                    draw.poly(L, [P(x, y, zt) for (x, y) in nq])
                    draw.fill(L, self._tread_col(e * 1.8 + 0.02))
        # the risers below the nosings fall into shadow
        for k in range(4):
            zs = z0 + k * h / 4
            nk = nt if k % 2 == 0 else max(nt, int(round(nt * (a + self.dy) / a)))
            for j in range(nk):
                u1 = (j + 1) / nk
                zt = zs + (j + 1) * h / 4 / nk
                rq = self._tread_quad(k, u1, min(1.0, u1 + 0.10 / nk))
                draw.poly(L, [P(x, y, zt + 0.02) for (x, y) in rq])
        draw.fill(L, INK, 0.5)
        # the wall stringers (the flights' outer edges against the walls)
        for k in range(4):
            zs = z0 + k * h / 4
            ze = zs + h / 4
            e0, e1 = self._flight_xy(k, 0.0, b), self._flight_xy(k, 1.0, b)
            draw.poly(L, [P(e0[0], e0[1], zs - 0.22), P(e1[0], e1[1], ze - 0.22), P(e1[0], e1[1], ze), P(e0[0], e0[1], zs)])
        draw.fill(L, INK, 0.75)
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
        for k in range(4):
            zs = z0 + k * h / 4
            nb = int(2 * (a if k % 2 == 0 else a + self.dy) / 0.13)
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
