"""Shared helpers for SALVAGE s05 (meridian), s06 (outward) and s08 (shaft).

Everything is a pure function of its arguments (plus caches of deterministic data):
  * Sampled / track     cache a function of time on a grid; piecewise eased keys
  * hose_rope/draw_hose the red air hose (physics.Rope, the bible's settings) as one band
  * helmet_valve        where the exhaust bubbles leave the Mark V helmet
  * ray_segment / ray_poly / ray_ground   2D ray hits (the lamp's axis against the silt,
                        the transom, a wall)
  * lamp_beam           atmos.beam aimed at a target, stopped by a surface line
  * transom_lit         the lamp's pool on the Meridian's stern plate at an EXPLICIT hit point
                        (Wreck.draw_lit places its pool at the plate's centroid distance)
  * bell_lit            the bronze bell lit by the lamp (warm body, specular streak, lip)
  * silt_puffs          silt clouds kicked up by boots, lit by the lamp
  * screen_glow/band    soft screen-space light (backlight behind a silhouette)
"""
import functools
import math

import cairo
import numpy as np

from engine import atmos, costume, draw
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.palette import RED, SALVAGE
from engine.physics import Rope

INK = SALVAGE.ink
D2R = math.pi / 180.0


# ----------------------------------------------------------------------------- time
class Sampled:
    """fn(t) -> tuple/float sampled on [t0, t1] at `hz`, linearly interpolated (built lazily,
    once per process)."""

    def __init__(self, fn, t0, t1, hz=60.0):
        self.fn, self.t0, self.t1, self.hz = fn, float(t0), float(t1), float(hz)
        self._tab = None

    def _build(self):
        n = int(math.ceil((self.t1 - self.t0) * self.hz)) + 2
        ts = self.t0 + np.arange(n) / self.hz
        self._tab = np.array([np.atleast_1d(np.asarray(self.fn(float(t)), np.float64)) for t in ts])

    def __call__(self, t):
        if self._tab is None:
            self._build()
        x = (min(max(t, self.t0), self.t1) - self.t0) * self.hz
        i = min(int(x), len(self._tab) - 2)
        u = x - i
        v = self._tab[i] * (1.0 - u) + self._tab[i + 1] * u
        return tuple(float(a) for a in v) if v.size > 1 else float(v[0])


def track(keys, t):
    """Piecewise interpolation through [(t, value, ease_into_key)]; values are floats or
    tuples. ease names are engine.core.ease's ('inout', 'out', 'in', 'linear', ...)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            t0, v0 = keys[i - 1][0], keys[i - 1][1]
            t1, v1 = keys[i][0], keys[i][1]
            e = keys[i][2] if len(keys[i]) > 2 else "inout"
            u = ease(e, (t - t0) / max(t1 - t0, 1e-9))
            if isinstance(v0, tuple):
                return tuple(lerp(a, b, u) for a, b in zip(v0, v1))
            return lerp(v0, v1, u)
    return keys[-1][1]


def bump(t, t0, t1, t2=None, t3=None):
    """0 -> 1 over [t0, t1] (smooth), back to 0 over [t2, t3] (if given)."""
    v = smoothstep(t0, t1, t)
    if t2 is not None:
        v *= 1.0 - smoothstep(t2, t3, t)
    return v


# ----------------------------------------------------------------------------- the red hose
HOSE_W = 10.0           # bible: ~10 px thick at zoom 1


def hose_rope(a, b, length, n=40, t0=-2.0, t1=20.0, current=None, collide=None, release=None,
              length_fn=None, init=None, gravity=(0.0, 60.0), drag=1.8, stiffness=0.3, iters=14):
    """The air hose as physics.Rope with the bible's settings (stiffness 0.3, gravity ~(0, 60),
    drag ~1.8, a current toward +x)."""
    cur = current if current is not None else (lambda t, x, y: (34.0 + 14.0 * math.sin(0.37 * t + y / 900.0), 0.0))
    return Rope(n, length, a, b, t0=t0, t1=t1, gravity=gravity, drag=drag, current=cur, collide=collide,
                release=release, length_fn=length_fn, iters=iters, stiffness=stiffness, init=init)


def draw_hose(ctx, pts, width=HOSE_W, color=RED, alpha=1.0):
    """The hose as one smooth band (a round-capped stroke of a Catmull-Rom curve)."""
    if len(pts) < 2:
        return
    ctx.save()
    ctx.new_path()
    if len(pts) >= 3:
        draw.smooth(ctx, pts, close=False, tension=0.5)
    else:
        draw.poly(ctx, pts, close=False)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*color[:3], alpha)
    ctx.stroke()
    ctx.restore()


def helmet_valve(sk):
    """World point just above the helmet's top valve (where the exhaust bubbles leave)."""
    c, R, vp, vr, inlet = costume.helmet_frame(sk)
    w = sk.side_w
    fwd = 1.0 if math.cos((sk.pose.yaw + sk.pose.head_yaw) * D2R) >= 0 else -1.0
    return (c[0] + fwd * R * 0.35 * (1 - w) - 0.18 * R * w, c[1] - R * 1.05)


# ----------------------------------------------------------------------------- 2D ray hits
def ray_segment(p, d, a, b):
    """Distance s >= 0 along the ray p + s * d (d unit) to segment a-b, or None."""
    ex, ey = b[0] - a[0], b[1] - a[1]
    den = d[0] * ey - d[1] * ex
    if abs(den) < 1e-9:
        return None
    wx, wy = a[0] - p[0], a[1] - p[1]
    s = (wx * ey - wy * ex) / den
    u = (wx * d[1] - wy * d[0]) / den
    if s < 0.0 or u < 0.0 or u > 1.0:
        return None
    return s


def ray_poly(p, d, poly):
    """Nearest hit (s, (x, y), edge index) of the ray with a closed polygon's edges, or None."""
    best = None
    n = len(poly)
    for i in range(n):
        s = ray_segment(p, d, poly[i], poly[(i + 1) % n])
        if s is not None and (best is None or s < best[0]):
            best = (s, (p[0] + d[0] * s, p[1] + d[1] * s), i)
    return best


def ray_ground(p, d, ground, smax=6000.0, step=24.0):
    """First hit (s, (x, y)) of the ray with the height field y = ground(x) (below p), or None."""
    if d[1] <= 1e-4:
        return None
    s0 = 0.0
    f0 = p[1] - ground(p[0])
    s = step
    while s <= smax:
        x, y = p[0] + d[0] * s, p[1] + d[1] * s
        f1 = y - ground(x)
        if f1 >= 0.0 > f0:
            lo, hi = s0, s
            for _ in range(12):
                mid = 0.5 * (lo + hi)
                xm, ym = p[0] + d[0] * mid, p[1] + d[1] * mid
                if ym - ground(xm) >= 0.0:
                    hi = mid
                else:
                    lo = mid
            return hi, (p[0] + d[0] * hi, p[1] + d[1] * hi)
        s0, f0 = s, f1
        s += step
    return None


def unit(dx, dy):
    L = math.hypot(dx, dy) or 1.0
    return dx / L, dy / L


# ----------------------------------------------------------------------------- the lamp
def lamp_beam(f, t, apex, target, stop=None, half=9.0, intensity=0.7, pool=0.8, squash=0.4, dust=0.5,
              glare=0.0, seed=5, reach=None, fog=0.4, core=0.55, falloff=0.75, soft=0.5, occluder=None):
    """atmos.beam from apex toward target. stop: 'perp' (a wall facing the camera: a line
    across the beam at the target), a segment ((x0, y0), (x1, y1)), or None (the beam fades
    out at `reach`). Returns the Cone."""
    dx, dy = target[0] - apex[0], target[1] - apex[1]
    dist = math.hypot(dx, dy) or 1.0
    ang = math.degrees(math.atan2(dy, dx))
    st = stop
    if stop == "perp":
        ux, uy = dx / dist, dy / dist
        st = ((target[0] - uy * 900.0, target[1] + ux * 900.0), (target[0] + uy * 900.0, target[1] - ux * 900.0))
    L = reach if reach is not None else dist + 200.0
    return atmos.beam(f, apex, ang, length=L, half_angle=half, intensity=intensity, falloff=falloff, soft=soft,
                      core=core, fog=fog, stop=st, pool=pool if st is not None else 0.0, pool_squash=squash,
                      dust=dust, glare=glare, t=t, seed=seed, occluder=occluder)


def surface_line(ground, x, half=500.0):
    """The silt's local tangent at x as a stop segment for atmos.beam."""
    return ((x - half, ground(x - half)), (x + half, ground(x + half)))


# ----------------------------------------------------------------------------- the stern plate
def transom_lit(f, view, wreck, hit, r, fall, name=True, blur=1.2):
    """The lamp's warm pool on the Meridian's transom (her stern plate) centred on `hit`
    (action-plane coords) with radius r: plate seams, rivet rows and the raised NAME catch
    the light. A copy of sets_wreck.Wreck.draw_lit with an explicit hit point."""
    if fall <= 0.01 or r <= 1.0:
        return
    W_ = wreck.W
    sec = wreck.section(0.0)
    poly = [view.Pp(W_(0.0, b, h)) for b, h in sec]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    if hit[0] + r < min(xs) or hit[0] - r > max(xs) or hit[1] + r < min(ys) or hit[1] - r > max(ys):
        return
    lit = f.pal.light
    k = view.k(W_(0, 0, 2000)[2])
    h0, _, _ = wreck._shape_params(0.0)
    dh = wreck.deck_h(0.0)

    def surf(b, h):
        return view.Pp(W_(0.0, b, h))

    with f.light(blur=blur) as A:
        draw.poly(A, poly)
        A.clip()
        A.rectangle(hit[0] - r, hit[1] - r, 2 * r, 2 * r)
        A.clip()
        A.push_group()
        draw.radial(A, hit, 0, r, [(0, lit, 0.62 * fall), (0.45, lit, 0.34 * fall), (1, lit, 0.0)])
        A.paint()
        A.set_operator(cairo.OPERATOR_DEST_OUT)
        for bb in (-880.0, -300.0, 300.0, 880.0):
            hs = [lerp(h0, dh, i / 8) for i in range(9)]
            pts = [surf(bb + 25 * math.sin(h / 400.0), h) for h in hs]
            _line(A, pts, max(7 * k, 1.0), (0, 0, 0), 0.75)
        for hh in (lerp(h0, dh, 0.36), lerp(h0, dh, 0.7)):
            pts = [surf(lerp(-1250, 1250, i / 12), hh) for i in range(13)]
            _line(A, pts, max(7 * k, 1.0), (0, 0, 0), 0.75)
        if name:
            wreck._name_path(A, view, offset=(5 * k, 6 * k))
            A.set_source_rgba(0, 0, 0, 0.85)
            A.fill()
        A.set_operator(cairo.OPERATOR_OVER)
        A.pop_group_to_source()
        A.paint()
        src = [(0, lit, 0.95 * fall), (0.5, lit, 0.55 * fall), (1, lit, 0.0)]
        rr = max(7 * k, 0.7)
        for bb in (-880.0, -300.0, 300.0, 880.0):
            for i in range(18):
                h = lerp(h0 + 40, dh - 40, i / 17)
                for side in (-1, 1):
                    p = surf(bb + 25 * math.sin(h / 400.0) + side * 30, h)
                    if abs(p[0] - hit[0]) < r and abs(p[1] - hit[1]) < r:
                        draw.circle(A, p, rr)
        for hh in (lerp(h0, dh, 0.36), lerp(h0, dh, 0.7)):
            for i in range(31):
                p = surf(lerp(-1200, 1200, i / 30), hh + 28)
                if abs(p[0] - hit[0]) < r and abs(p[1] - hit[1]) < r:
                    draw.circle(A, p, rr)
        draw.radial(A, hit, 0, r, src)
        A.fill()
        if name:
            wreck._name_path(A, view)
            draw.radial(A, hit, 0, r * 1.1, [(0, lit, 1.0 * fall), (0.55, lit, 0.6 * fall), (1, lit, 0.0)])
            A.fill()
        A.reset_clip()


def _line(ctx, pts, w, col, a=1.0):
    ctx.new_path()
    draw.poly(ctx, pts, close=False)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*col[:3], a)
    ctx.stroke()


# ----------------------------------------------------------------------------- the bell
def bell_lit(f, b, lamp, power, draw_bell, blur=0.8):
    """The bronze bell (wreck.bell_screen(view, t) dict b) lit by a lamp at `lamp`
    (action-plane coords): a warm body graded toward the lamp, a specular streak down the
    flank that faces it, a hot lip bead and a glint on the crown. power 0..1."""
    if power <= 0.01:
        return
    lit = f.pal.light
    X, Y, s, ang = b["X"], b["Y"], b["s"], b["angle"]
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def L(px, py):          # bell-local -> action plane
        return (X + (px * ca - py * sa) * s, Y + (px * sa + py * ca) * s)

    c = L(0, 90)
    ux, uy = unit(lamp[0] - c[0], lamp[1] - c[1])
    side = 1.0 if (ux * ca + uy * sa) >= 0 else -1.0       # which flank faces the lamp
    with f.light(blur=blur) as A:
        A.push_group()
        draw_bell(A, X, Y, angle=ang, clapper=b["clapper"], s=s, color=(1, 1, 1))
        mask = A.pop_group()
        hot = (c[0] + ux * 40 * s, c[1] + uy * 40 * s)
        g = cairo.RadialGradient(hot[0], hot[1], 0, hot[0], hot[1], 105 * s)
        for o, al in ((0.0, 0.85), (0.45, 0.42), (1.0, 0.10)):
            g.add_color_stop_rgba(o, lit[0], lit[1], lit[2], al * power)
        A.set_source(g)
        A.mask(mask)
        # specular streak down the lit flank (the bronze's curvature)
        A.push_group()
        pts = [L(side * x, y) for x, y in ((24, 34), (30, 60), (33, 96), (40, 120), (50, 136), (38, 136),
                                             (26, 112), (19, 80), (16, 48))]
        draw.smooth(A, pts, close=True, tension=0.4)
        A.set_source_rgba(1, 1, 1, 1)
        A.fill()
        streak = A.pop_group()
        A.set_source_rgba(*_hot(lit), 0.9 * power)
        A.mask(streak)
        # the lip bead and the crown loop catch it
        _line(A, [L(-66 * side, 141), L(0, 143), L(66 * side, 141)], max(4.0 * s, 1.0), _hot(lit), 0.75 * power)
        draw.circle(A, L(side * 6, 9), max(3.5 * s, 0.8))
        draw.fill(A, _hot(lit), 0.8 * power)


def _hot(c, k=0.55):
    return (lerp(c[0], 1.0, k), lerp(c[1], 1.0, k), lerp(c[2], 1.0, k))


# ----------------------------------------------------------------------------- silt
def silt_puffs(f, t, puffs, light_at, color=None, blur=7.0):
    """Silt clouds kicked up by boots: puffs = [(x, y, t0, size, seed)]; each billows up and
    out, slows, sags and fades over ~3 s. light_at(x, y) -> 0..1 (how much lamp light
    reaches them: they only show where lit). Drawn as additive haze."""
    col = color or S_SILT
    live = [p for p in puffs if 0.0 <= t - p[2] < 3.4]
    if not live:
        return
    with f.light(blur=blur) as A:
        for x, y, t0, size, seed in live:
            tau = t - t0
            k = light_at(x, y - 40 * size)
            if k <= 0.01:
                continue
            fade = (1.0 - smoothstep(0.6, 3.4, tau)) * smoothstep(0.0, 0.08, tau)
            for i in range(7):
                h1, h2, h3 = hash01(seed, i, 1), hash01(seed, i, 2), hash01(seed, i, 3)
                sd = (h1 - 0.5) * 2.0
                grow = 1.0 - math.exp(-tau * (2.2 + h2))
                bx = x + size * (sd * 70.0 * grow + 8.0 * tau)
                by = y - size * (6.0 + (22.0 + 40.0 * h3) * grow - 6.0 * smoothstep(1.0, 3.4, tau))
                r = size * (14.0 + 26.0 * h2) * (0.45 + 0.9 * grow)
                draw.glow_disc(A, (bx, by), r, col, 0.26 * fade * k * (0.6 + 0.4 * h3))


S_SILT = (0.62, 0.55, 0.44)


@functools.lru_cache(maxsize=8)
def footfalls(actor_key, t0, t1, hz=60.0):
    """[(t, x, side)] of the moments a foot of ACTORS[actor_key] plants (its heel comes down
    to the ground) between t0 and t1."""
    A, ground = ACTORS[actor_key]
    out = []
    n = int((t1 - t0) * hz) + 1
    prev = {}
    for i in range(n):
        t = t0 + i / hz
        sk = A.skeleton(t)
        for s in ("L", "R"):
            hx, hy = sk.j["heel_" + s]
            bx, by = sk.j["ball_" + s]
            low = max(hy, by)
            g = ground((hx + bx) / 2)
            h = g - low
            was = prev.get(s)
            if was is not None and was > 6.0 >= h:
                out.append((t, (hx + bx) / 2, s))
            prev[s] = h
    return tuple(out)


ACTORS = {}


# ----------------------------------------------------------------------------- screen light
def screen_glow(f, c, r, color, a, par=0.0, blur=30.0, core=0.0):
    """A soft additive pool of light in SCREEN space (a backlight behind a silhouette)."""
    if a <= 0.0:
        return
    with f.light(par=par, blur=blur) as A:
        A.save()
        A.identity_matrix()
        A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
        draw.glow_disc(A, c, r, color, a, core)
        A.restore()


def screen_band(f, y0, y1, color, a0, a1, blur=0.0):
    """Additive vertical gradient band (screen space): a0 at y0 -> a1 at y1."""
    if max(a0, a1) <= 0.0:
        return
    with f.light(par=0.0, blur=blur) as A:
        A.save()
        A.identity_matrix()
        A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
        draw.linear(A, (0, y0), (0, y1), [(0, color, a0), (1, color, a1)])
        A.rectangle(0, min(y0, y1), W, abs(y1 - y0))
        A.fill()
        A.restore()


def far_rays(f, t, intensity, par=0.35, length=1400.0, seed=8, spacing=170.0):
    """Faint far rays at the top of the frame (the light plan for s05-s13): underwater rays
    hanging from a virtual surface just above the view on a far layer (par), fading down."""
    if intensity <= 0.0:
        return
    cam = f.lcam(par)
    x0, y0, x1, y1 = cam.view_rect(0)
    sy = y0 - 150.0 / cam.zoom
    atmos.underwater_rays(f, surface_y=sy, t=t, spacing=spacing, angle=97.0, fan=9.0, length=length / cam.zoom,
                          intensity=intensity, density=0.55, seed=seed, par=par, blur=18)
