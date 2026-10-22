"""RED sets: shared moods, colors and small drawing helpers.

Every color here is derived from `engine.palette.RED_FILM` (ink, fog stops, snow, amber
light, dawn, RED). Night and dusk are the same greys pulled toward ink; dawn leans toward
`pal.dawn`. No new hues.

A `Mood` is the lighting of one moment (day fog, the dark forest, dusk, night, dawn, the
years-later evening). Every set's draw functions take `mood=`; blend two with `mood_mix`.
"""
import math
from contextlib import contextmanager

import cairo
import cv2
import numpy as np

from engine import draw
from engine.core import clamp, lerp, hash01, fbm1
from engine.palette import RED_FILM, RED

PAL = RED_FILM
INK = PAL.ink
SNOW = PAL.snow
AMBER = PAL.light
DAWN = PAL.dawn
HOOD_RED = RED


def mix(a, b, t):
    t = clamp(t)
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def grey(v):
    return (v, v, v)


def toward_ink(c, k):
    """Color c darkened toward the film's ink by k (0 = c, 1 = ink)."""
    return mix(c, INK, k)


# ----------------------------------------------------------------------------- moods
def sample_stops(stops, u):
    """Color at u from [(pos, rgb), ...] stops (clamped)."""
    u = clamp(u)
    for (u0, c0), (u1, c1) in zip(stops, stops[1:]):
        if u <= u1:
            return mix(c0, c1, (u - u0) / max(u1 - u0, 1e-6))
    return stops[-1][1]


class Mood:
    """Lighting of a moment. Fields (all rgb 0..1, derived from RED_FILM):

    sky        [(pos01, rgb), ...] screen-space vertical gradient (0 = top of frame)
    fog_stops  [(depth01, rgb), ...] atmospheric color by depth (0 near .. 1 far)
    snow       lit snow surface;  snow_dark: snow in shade (low in the near field)
    mist       color of drifting mist bands
    shaft      light-shaft color, shaft_a: its strength (0 = no shafts)
    lamp       lantern / window / fire color (amber), lamp_gain: emissive multiplier
    ink        silhouette ink
    """

    def __init__(self, name, sky, fog_stops, snow, snow_dark, mist, shaft, shaft_a,
                 lamp_gain=1.0, ink=INK, lamp=AMBER, night=0.0):
        self.name = name
        self.sky = sky
        self.fog_stops = fog_stops
        self.snow, self.snow_dark, self.mist = snow, snow_dark, mist
        self.shaft, self.shaft_a = shaft, shaft_a
        self.lamp_gain = lamp_gain
        self.ink, self.lamp = ink, lamp
        self.night = night          # 0 = day .. 1 = full night (drives window/lamp visibility)

    def fog_at(self, d):
        """Atmospheric color at depth d (0 near .. 1 far)."""
        return sample_stops(self.fog_stops, d)

    def shade(self, d):
        """Flat fill for a silhouette at depth d drawn WITHOUT a fog layer (ink -> fog)."""
        return mix(self.ink, self.fog_at(d), clamp(d) ** 0.85)

    def sky_at(self, u):
        """Sky color at screen height u (0 = top of frame, 1 = bottom)."""
        return sample_stops(self.sky, u)

    def __repr__(self):
        return f"Mood({self.name})"


def _fog_scaled(k, toward=None, amt=0.0):
    out = []
    for d, c in PAL.fog_stops:
        c2 = mix(INK, c, k)
        if toward is not None:
            c2 = mix(c2, toward, amt * d)
        out.append((d, c2))
    return out


_FOG = PAL.fog_stops

DAY = Mood(
    "day",
    sky=[(0.0, PAL.sky_top), (0.52, PAL.sky_bottom), (0.78, mix(PAL.sky_bottom, SNOW, 0.35)),
         (1.0, PAL.sky_bottom)],
    fog_stops=_FOG, snow=SNOW, snow_dark=mix(SNOW, _FOG[1][1], 0.38),
    mist=mix(_FOG[2][1], SNOW, 0.4), shaft=SNOW, shaft_a=0.24, lamp_gain=0.8, night=0.0)

# deeper in the forest: the fog thickens and darkens ("the quieter the world became")
DEEP = Mood(
    "deep",
    sky=[(0.0, mix(INK, PAL.sky_top, 0.55)), (0.55, mix(INK, PAL.sky_bottom, 0.74)),
         (1.0, mix(INK, PAL.sky_bottom, 0.62))],
    fog_stops=_fog_scaled(0.70), snow=mix(INK, SNOW, 0.78), snow_dark=mix(INK, SNOW, 0.58),
    mist=mix(INK, _FOG[2][1], 0.72), shaft=SNOW, shaft_a=0.22, lamp_gain=1.0, night=0.25)

DUSK = Mood(
    "dusk",
    sky=[(0.0, mix(INK, PAL.sky_top, 0.30)), (0.6, mix(INK, PAL.sky_bottom, 0.50)),
         (1.0, mix(INK, PAL.sky_bottom, 0.40))],
    fog_stops=_fog_scaled(0.46), snow=mix(INK, SNOW, 0.60), snow_dark=mix(INK, SNOW, 0.40),
    mist=mix(INK, _FOG[2][1], 0.46), shaft=SNOW, shaft_a=0.0, lamp_gain=1.25, night=0.6)

NIGHT = Mood(
    "night",
    sky=[(0.0, mix(INK, PAL.sky_top, 0.07)), (0.62, mix(INK, PAL.sky_bottom, 0.24)),
         (1.0, mix(INK, PAL.sky_bottom, 0.17))],
    fog_stops=_fog_scaled(0.27), snow=mix(INK, SNOW, 0.44), snow_dark=mix(INK, SNOW, 0.24),
    mist=mix(INK, _FOG[2][1], 0.30), shaft=SNOW, shaft_a=0.0, lamp_gain=1.6, night=1.0)

DAWN_M = Mood(
    "dawn",
    sky=[(0.0, mix(PAL.sky_top, DAWN, 0.25)), (0.55, DAWN), (0.8, mix(DAWN, SNOW, 0.45)),
         (1.0, mix(DAWN, PAL.sky_bottom, 0.5))],
    fog_stops=[(d, mix(c, DAWN, 0.55 * d)) for d, c in _FOG],
    snow=mix(SNOW, DAWN, 0.22), snow_dark=mix(mix(SNOW, DAWN, 0.3), _FOG[1][1], 0.4),
    mist=mix(DAWN, SNOW, 0.35), shaft=mix(DAWN, SNOW, 0.5), shaft_a=0.26, lamp_gain=0.7, night=0.0)

# years later: an evening of falling snow, warm lantern path
LATER = Mood(
    "later",
    sky=[(0.0, mix(INK, PAL.sky_top, 0.16)), (0.6, mix(INK, PAL.sky_bottom, 0.36)),
         (1.0, mix(INK, PAL.sky_bottom, 0.28))],
    fog_stops=_fog_scaled(0.37), snow=mix(INK, SNOW, 0.54), snow_dark=mix(INK, SNOW, 0.33),
    mist=mix(INK, _FOG[2][1], 0.40), shaft=SNOW, shaft_a=0.0, lamp_gain=1.45, night=0.8)

# s10: the grey morning after the fire: flat, cold, no shafts, lamps barely matter
MORNING = Mood(
    "morning",
    sky=[(0.0, mix(INK, PAL.sky_top, 0.74)), (0.6, mix(INK, PAL.sky_bottom, 0.84)),
         (1.0, mix(INK, PAL.sky_bottom, 0.8))],
    fog_stops=_fog_scaled(0.84), snow=mix(INK, SNOW, 0.88), snow_dark=mix(INK, SNOW, 0.68),
    mist=mix(INK, _FOG[2][1], 0.84), shaft=SNOW, shaft_a=0.0, lamp_gain=0.75, night=0.1)

MOODS = {"day": DAY, "deep": DEEP, "dusk": DUSK, "night": NIGHT, "dawn": DAWN_M, "later": LATER,
         "morning": MORNING}


def get_mood(m):
    if isinstance(m, Mood):
        return m
    return MOODS[m or "day"]


def mood_mix(a, b, t):
    """Blend two moods (for dusk falling, dawn rising)."""
    a, b = get_mood(a), get_mood(b)
    t = clamp(t)
    if t <= 0:
        return a
    if t >= 1:
        return b

    def stops(sa, sb):
        keys = sorted(set([p for p, _ in sa] + [p for p, _ in sb]))
        return [(k, mix(sample_stops(sa, k), sample_stops(sb, k), t)) for k in keys]

    return Mood(f"{a.name}>{b.name}", sky=stops(a.sky, b.sky), fog_stops=stops(a.fog_stops, b.fog_stops),
                snow=mix(a.snow, b.snow, t), snow_dark=mix(a.snow_dark, b.snow_dark, t),
                mist=mix(a.mist, b.mist, t), shaft=mix(a.shaft, b.shaft, t),
                shaft_a=lerp(a.shaft_a, b.shaft_a, t), lamp_gain=lerp(a.lamp_gain, b.lamp_gain, t),
                night=lerp(a.night, b.night, t))


# ----------------------------------------------------------------------------- frame helpers
def _arr(surf):
    """Writable (h, w, 4) uint8 view of an ARGB32 cairo surface (premultiplied BGRA)."""
    w, h, st = surf.get_width(), surf.get_height(), surf.get_stride()
    return np.ndarray(shape=(h, st // 4, 4), dtype=np.uint8, buffer=surf.get_data())[:, :w, :]


def fogged(mood, d, col=None):
    """Color `col` (default ink) as seen through fog at depth d: identical to drawing it in
    ink inside f.layer(fog=d, fog_color=mood.fog_at(d)), but with no offscreen pass."""
    mood = get_mood(mood)
    col = mood.ink if col is None else col
    return mix(col, mood.fog_at(d), clamp(d))


def tinted(mood, d):
    """A copy of mood with every surface color pre-fogged to depth d (for props and sets
    painted straight onto a far plane without an offscreen fog pass)."""
    mood = get_mood(mood)
    return Mood(mood.name, mood.sky, mood.fog_stops, fogged(mood, d, mood.snow), fogged(mood, d, mood.snow_dark),
                mood.mist, mood.shaft, mood.shaft_a, mood.lamp_gain, ink=fogged(mood, d), lamp=mood.lamp,
                night=mood.night)


def backdrop(f, mood, glow=None, glow_r=900.0, glow_a=0.35):
    """Sky gradient (screen space) + optional bright hot-spot behind the subject
    (glow = screen (x, y)): Limbo's backlight. Draws on the main canvas."""
    mood = get_mood(mood)
    c = f.ctx
    c.save()
    c.identity_matrix()
    s = f.scale
    g = cairo.LinearGradient(0, 0, 0, 1920 * s)
    for u, col in mood.sky:
        g.add_color_stop_rgb(u, *col)
    c.set_source(g)
    c.paint()
    c.restore()
    if glow is not None and glow_a > 0:
        base = mood.sky_at(0.6)
        hot = mix(base, mood.shaft, 0.75) if mood.night < 0.5 else mix(base, mood.fog_at(1.0), 0.8)
        with soft_layer(f, k=4, screen=True) as L:
            rg = cairo.RadialGradient(glow[0], glow[1], 0, glow[0], glow[1], glow_r)
            rg.add_color_stop_rgba(0, hot[0], hot[1], hot[2], glow_a)
            rg.add_color_stop_rgba(0.45, hot[0], hot[1], hot[2], glow_a * 0.4)
            rg.add_color_stop_rgba(1, hot[0], hot[1], hot[2], 0)
            L.set_source(rg)
            L.paint()


@contextmanager
def depth_layer(f, mood, par, depth, blur=None, alpha=1.0):
    """A fogged depth layer: content drawn in ink, tinted toward mood.fog_at(depth) by
    `depth` and blurred (default blur grows with distance from the action plane)."""
    mood = get_mood(mood)
    if blur is None:
        blur = 9.0 * abs(1.0 - par) + 1.0 if par < 1 else 14.0 * (par - 1.0)
    fog = clamp(depth)
    with f.layer(par=par, blur=blur, fog=fog, fog_color=mood.fog_at(depth) if fog > 0 else None,
                 alpha=alpha) as L:
        yield L


@contextmanager
def soft_layer(f, par=1.0, k=4, op=None, screen=False, blur=0.0, alpha=1.0):
    """Low-resolution offscreen for SOFT content (mist, glows, beams): drawn at 1/k
    resolution through the camera of `par` (or in screen space), optionally blurred
    (`blur` in screen px), then composited with bilinear upscaling (op: cairo operator,
    e.g. cairo.OPERATOR_ADD for light). Much cheaper than full-res gradients."""
    pw, ph = f.pw, f.ph
    lw, lh = max(1, pw // k), max(1, ph // k)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, lw, lh)
    c = cairo.Context(surf)
    if screen:
        c.set_matrix(cairo.Matrix(xx=f.scale * lw / pw, yy=f.scale * lh / ph))
    else:
        c.set_matrix(f.lcam(par).matrix(f.scale * lw / pw))
    try:
        yield c
    finally:
        surf.flush()
        sig = blur * f.scale * lw / pw
        if sig > 0.3:
            arr = _arr(surf)
            arr[...] = cv2.GaussianBlur(arr, (0, 0), sigmaX=sig, sigmaY=sig, borderType=cv2.BORDER_REPLICATE)
            surf.mark_dirty()
        if op == "add" or op == cairo.OPERATOR_ADD:
            # numpy additive composite: ~4x faster than pixman's bilinear OPERATOR_ADD
            small = _arr(surf)
            if alpha < 0.999:
                small = (small.astype(np.float32) * clamp(alpha)).astype(np.uint8)
            up = cv2.resize(small, (pw, ph), interpolation=cv2.INTER_LINEAR)
            f.surf.flush()
            main = _arr(f.surf)
            cv2.add(main, up, dst=main)
            f.surf.mark_dirty()
            return
        m = f.ctx
        m.save()
        m.identity_matrix()
        pat = cairo.SurfacePattern(surf)
        pat.set_filter(cairo.FILTER_BILINEAR)
        pat.set_extend(cairo.EXTEND_PAD)
        pat.set_matrix(cairo.Matrix(xx=lw / pw, yy=lh / ph))
        if op is not None:
            m.set_operator(op)
        m.set_source(pat)
        m.paint_with_alpha(clamp(alpha))
        m.restore()


@contextmanager
def plane(f, par=1.0):
    """Draw directly on the main canvas through the parallax camera of `par` (no fog,
    no blur, no offscreen surface): cheap, for gradients and mist."""
    c = f.ctx
    c.save()
    c.set_matrix(f.lcam(par).matrix(f.scale))
    try:
        yield c
    finally:
        c.restore()


def view(f, par=1.0, margin=0.0):
    """World-space view rect (x0, y0, x1, y1) of the camera of layer `par`."""
    return f.lcam(par).view_rect(margin)


def mist_band(c, xs, ys, color, alpha, up=260.0, down=120.0):
    """Draw a soft mist band following the polyline (xs, ys) onto context c (any coords):
    densest on the line, fading `up` above and `down` below (cairo mesh gradient)."""
    r, g, b = color
    mesh = cairo.MeshPattern()
    n = len(xs)
    for i in range(n - 1):
        xa, xb, ya, yb = float(xs[i]), float(xs[i + 1]), float(ys[i]), float(ys[i + 1])
        for (o0, a0, o1, a1) in ((-up, 0.0, 0.0, alpha), (0.0, alpha, down, 0.0)):
            mesh.begin_patch()
            mesh.move_to(xa, ya + o0)
            mesh.line_to(xb, yb + o0)
            mesh.line_to(xb, yb + o1)
            mesh.line_to(xa, ya + o1)
            mesh.set_corner_color_rgba(0, r, g, b, a0)
            mesh.set_corner_color_rgba(1, r, g, b, a0)
            mesh.set_corner_color_rgba(2, r, g, b, a1)
            mesh.set_corner_color_rgba(3, r, g, b, a1)
            mesh.end_patch()
    c.set_source(mesh)
    c.move_to(float(xs[0]), float(ys[0]) - up)
    for x, y in zip(xs, ys):
        c.line_to(float(x), float(y) - up)
    for x, y in zip(xs[::-1], ys[::-1]):
        c.line_to(float(x), float(y) + down)
    c.close_path()
    c.fill()


def ground_mist(f, par, gfn, color, alpha, up=260.0, down=120.0, step=90.0, margin=200.0, x0=None, x1=None):
    """Mist lying on a sloped ground: a soft band that follows gfn(x) (layer coords of
    `par`), densest on the ground line, fading `up` above and `down` below. Painted over
    everything drawn so far (cheap cairo mesh gradient, no offscreen)."""
    if alpha <= 0.003:
        return
    vx0, vy0, vx1, vy1 = view(f, par, margin)
    if x0 is not None:
        vx0 = max(vx0, x0)
    if x1 is not None:
        vx1 = min(vx1, x1)
    if vx1 <= vx0:
        return
    n = max(2, int((vx1 - vx0) / step) + 2)
    xs = np.linspace(vx0, vx1, n)
    ys = np.asarray(gfn(xs), dtype=float)
    r, g, b = color
    with soft_layer(f, par, k=4) as c:
        mesh = cairo.MeshPattern()
        for i in range(n - 1):
            xa, xb, ya, yb = float(xs[i]), float(xs[i + 1]), float(ys[i]), float(ys[i + 1])
            # (top edge offset, top alpha, bottom edge offset, bottom alpha)
            for (o0, a0, o1, a1) in ((-up, 0.0, 0.0, alpha), (0.0, alpha, down, 0.0)):
                mesh.begin_patch()
                mesh.move_to(xa, ya + o0)
                mesh.line_to(xb, yb + o0)
                mesh.line_to(xb, yb + o1)
                mesh.line_to(xa, ya + o1)
                mesh.set_corner_color_rgba(0, r, g, b, a0)
                mesh.set_corner_color_rgba(1, r, g, b, a0)
                mesh.set_corner_color_rgba(2, r, g, b, a1)
                mesh.set_corner_color_rgba(3, r, g, b, a1)
                mesh.end_patch()
        c.set_source(mesh)
        c.move_to(float(xs[0]), float(ys[0]) - up)
        for x, y in zip(xs, ys):
            c.line_to(float(x), float(y) - up)
        for x, y in zip(xs[::-1], ys[::-1]):
            c.line_to(float(x), float(y) + down)
        c.close_path()
        c.fill()


def glow(ctx, c, r, rgb, a=1.0, core=0.0):
    """Soft radial glow (for f.emit / f.light contexts)."""
    if a <= 0.002 or r <= 0.1:
        return
    draw.radial(ctx, c, r * core, r, [(0, rgb, a), (0.3, rgb, a * 0.5), (1, rgb, 0.0)])
    ctx.arc(c[0], c[1], r, 0, 2 * math.pi)
    ctx.fill()


def light_pool(ctx, c, rx, ry, rgb, a):
    """Elliptical pool of light on the snow (for an f.light context)."""
    if a <= 0.002:
        return
    ctx.save()
    ctx.translate(c[0], c[1])
    ctx.scale(max(rx, 0.1), max(ry, 0.1))
    draw.radial(ctx, (0, 0), 0, 1, [(0, rgb, a), (0.4, rgb, a * 0.55), (1, rgb, 0.0)])
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def min_width(f, par, px):
    """World width that renders at least `px` screen pixels for layer `par`."""
    z = f.lcam(par).zoom
    return px / max(z, 1e-3)


def flick(t, seed, rate=7.0, depth=0.22):
    """Flame flicker multiplier around 1."""
    return 1.0 - depth * (0.5 + 0.5 * fbm1(t * rate, seed)) + 0.06 * fbm1(t * 23.0, seed + 5)


def rnd(*seed):
    return hash01(*seed)


def srnd(*seed):
    return hash01(*seed) * 2.0 - 1.0


def lerp_pts(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


def poly_path(ctx, pts):
    """Append a closed polygon (list of (x, y)) to the current path."""
    if len(pts) < 3:
        return
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def fill_polys(ctx, polys, rgb, a=1.0):
    """Fill many polygons as one path (fast)."""
    any_ = False
    for p in polys:
        if len(p) >= 3:
            poly_path(ctx, p)
            any_ = True
    if any_:
        draw.fill(ctx, rgb, a)
