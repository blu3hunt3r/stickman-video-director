"""SHADOW PLAY sets: shared internals (palette shortcuts, layer specs, recorded paths,
light switches, shadow screens, rain glints, anisotropic streak lights).

Animators import the public names from `films.shadowplay.sets`; this module is the toolbox
the set modules are built on. Everything is a pure function of its arguments (and t).
"""
import math
from contextlib import contextmanager

import cairo
import cv2
import numpy as np

from engine import draw
from engine.core import W, H, clamp, hash01, fbm1, smoothstep
from engine.frame import Camera, surf_array, array_surface, cached
from engine.palette import SHADOWPLAY

PAL = SHADOWPLAY
INK = PAL.ink
AMBER = PAL.light            # window / lamp light
HOT = PAL.lamp_hot           # bulb core, hottest part of a lit window
RAIN = PAL.rain
BLUE = PAL.police
LIGHTNING = PAL.lightning

#: world px per metre on the action plane (an adult of 1.75 m is 600 px at zoom 1)
PX_M = 600.0 / 1.75


# ----------------------------------------------------------------------------- colour helpers
def mix(a, b, t):
    """Blend two rgb tuples."""
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def mul(c, k):
    """Scale an rgb tuple by k (light intensity)."""
    return (c[0] * k, c[1] * k, c[2] * k)


def tone(k):
    """A dark set tone: ink lifted toward the near fog by k (0 = pure ink, 1 = fog_at(0.35)).
    Use for the few surfaces that must separate from pure ink (walls vs. frames)."""
    return mix(INK, PAL.fog_at(0.35), k)


# ----------------------------------------------------------------------------- layer specs
def layer_spec(layer=None, **over):
    """Normalize a layer spec. Accepts None (action plane), a dict with any of
    par/blur/fog/alpha, a tuple (par, blur, fog[, alpha]), or a cairo.Context the caller
    already opened (kept as spec['ctx']; drawn into as an action-plane layer)."""
    if isinstance(layer, cairo.Context):
        d = {"ctx": layer}
    elif layer is None:
        d = {}
    elif isinstance(layer, dict):
        d = dict(layer)
    elif isinstance(layer, (tuple, list)):
        d = dict(zip(("par", "blur", "fog", "alpha"), layer))
    else:
        raise TypeError("layer must be None, a dict, a tuple or a cairo.Context")
    d.setdefault("par", 1.0)
    d.setdefault("blur", 0.0)
    d.setdefault("fog", 0.0)
    d.setdefault("alpha", 1.0)
    d.update(over)
    return d


@contextmanager
def opened(f, layer):
    """Yield a context for `layer`: a cairo.Context is used as is; a spec opens f.layer()."""
    if isinstance(layer, cairo.Context):
        yield layer
        return
    s = layer_spec(layer)
    if s.get("ctx") is not None:
        yield s["ctx"]
        return
    with f.layer(par=s["par"], blur=s["blur"], fog=s["fog"], alpha=s["alpha"]) as L:
        yield L


def view_box(f, par=1.0, margin=0.0):
    """World rect (x0, y0, x1, y1) seen by the layer camera with parallax `par`."""
    return f.lcam(par).view_rect(margin)


def boxes_overlap(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


# ----------------------------------------------------------------------------- recorded paths
_SCRATCH = []


def _scratch():
    if not _SCRATCH:
        _SCRATCH.append(cairo.Context(cairo.ImageSurface(cairo.FORMAT_A8, 8, 8)))
    return _SCRATCH[0]


def record(fn):
    """Run fn(ctx) on a scratch context and return the built path (cairo.Path, local units).
    Static geometry is recorded once and replayed every frame with put()."""
    c = _scratch()
    c.new_path()
    c.identity_matrix()
    fn(c)
    p = c.copy_path()
    c.new_path()
    return p


def put(ctx, path, M=None):
    """Append a recorded path to ctx, mapped through the local->world matrix M."""
    if M is None:
        ctx.append_path(path)
        return
    ctx.save()
    ctx.transform(M)
    ctx.append_path(path)
    ctx.restore()


def fill_path(ctx, path, rgb, alpha=1.0, M=None, even_odd=False):
    ctx.new_path()
    put(ctx, path, M)
    if even_odd:
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    draw.fill(ctx, rgb, alpha)
    if even_odd:
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def local_matrix(origin, scale, anchor=(0.0, 0.0)):
    """Matrix mapping local design units to world: local `anchor` lands on `origin`."""
    s = float(scale)
    return cairo.Matrix(xx=s, yy=s, x0=origin[0] - s * anchor[0], y0=origin[1] - s * anchor[1])


def rrect(ctx, x0, y0, x1, y1, r):
    """Rounded rectangle path."""
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    ctx.new_sub_path()
    ctx.arc(x1 - r, y0 + r, r, -math.pi / 2, 0)
    ctx.arc(x1 - r, y1 - r, r, 0, math.pi / 2)
    ctx.arc(x0 + r, y1 - r, r, math.pi / 2, math.pi)
    ctx.arc(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


# ----------------------------------------------------------------------------- light switches
def switch(t, t_on=None, t_off=None, kind="bulb", seed=0, level=1.0):
    """Level (0..level) of a light switched on at t_on and off at t_off (None = never).

    kind:
      'bulb'    two-frame rise with a small filament overshoot (a lamp, a window light);
      'flicker' stutters on/off for ~0.7 s, then holds (old wiring, a fluorescent tube);
      'fade'    1.2 s dimmer;   'instant' hard cut.
    Switching off decays like a filament (about 0.1 s). Deterministic for a seed."""
    v = 1.0
    if t_on is not None:
        dt = t - t_on
        if dt < 0:
            v = 0.0
        elif kind == "instant":
            v = 1.0
        elif kind == "fade":
            v = smoothstep(0.0, 1.2, dt)
        elif kind == "flicker":
            if dt < 0.72:
                # choreographed stutter: on, off, on-on, off, on ... jittered by the seed
                k = int(dt * 24.0)
                pattern = (1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1)
                on = pattern[k % len(pattern)]
                if hash01(seed, k, 31) < 0.18:
                    on = 1 - on
                v = (0.08 + 0.92 * on) * (0.75 + 0.25 * hash01(seed, k, 5))
            else:
                v = 1.0 - 0.06 * math.exp(-(dt - 0.72) * 3.0) * (0.5 + 0.5 * math.sin(dt * 60.0))
        else:                                   # bulb
            v = min(1.0, dt / 0.07)
            v *= 1.0 + 0.10 * math.exp(-dt * 7.0) * (dt > 0.07)
    if t_off is not None and t >= t_off:
        v *= math.exp(-(t - t_off) / 0.05)
    return clamp(v, 0.0, 1.15) * level


def level_of(v, t):
    """A light level given as a number or as a callable of t."""
    if v is None:
        return 0.0
    if callable(v):
        return float(v(t))
    return float(v)


# ----------------------------------------------------------------------------- shadow screens
def shadow_screen(ctx, casters, region=None, bbox=None, soft=4.0, density=0.9, mag=1.0,
                  center=None, gel=1.0):
    """Cast the shapes drawn by `casters(c)` as shadows on whatever is already painted on ctx.

    The casters are drawn (in the same world coordinates as ctx) into an offscreen buffer,
    optionally magnified by `mag` about `center` (the lamp's point on the screen: a caster
    near the lamp throws a big shadow), blurred by `soft` world px (penumbra: casters far
    from the screen are soft), then MULTIPLIED onto ctx inside `region` (a callable that
    builds a world path, or a cairo.Path in world coords). Translucent colours act as gels:
    a RED shape tints the light red instead of blocking it (the paper blood).

    density: how dark a full shadow is (1 = black, 0.9 leaves some room light).
    bbox: world rect bounding the screen (required). The screen must already be opaque."""
    Mx = ctx.get_matrix()
    x0, y0, x1, y1 = bbox
    pts = [Mx.transform_point(x, y) for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
    tgt = ctx.get_target()
    tw, th = tgt.get_width(), tgt.get_height()
    kpx = math.sqrt(abs(Mx.xx * Mx.yy - Mx.xy * Mx.yx)) or 1.0
    sig = soft * kpx
    pad = int(3 * sig) + 2
    ix0 = max(0, int(math.floor(min(p[0] for p in pts))) - pad)
    iy0 = max(0, int(math.floor(min(p[1] for p in pts))) - pad)
    ix1 = min(tw, int(math.ceil(max(p[0] for p in pts))) + pad)
    iy1 = min(th, int(math.ceil(max(p[1] for p in pts))) + pad)
    w, h = ix1 - ix0, iy1 - iy0
    if w <= 1 or h <= 1:
        return
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(surf)
    c.set_matrix(Mx.multiply(cairo.Matrix(x0=-ix0, y0=-iy0)))
    if mag != 1.0 and center is not None:
        c.translate(center[0], center[1])
        c.scale(mag, mag)
        c.translate(-center[0], -center[1])
    casters(c)
    arr = surf_array(surf).astype(np.float32) * (1.0 / 255.0)
    if not arr[..., 3].any():
        return
    if sig > 0.3:
        arr = cv2.GaussianBlur(arr, (0, 0), sigmaX=sig, sigmaY=sig, borderType=cv2.BORDER_REPLICATE)
    a = arr[..., 3:4]
    T = 1.0 - density * a + density * gel * arr[..., :3]
    out = np.empty((h, w, 4), np.uint8)
    out[..., :3] = np.clip(T * 255.0, 0, 255)
    out[..., 3] = 255
    msurf = array_surface(out)
    ctx.save()
    if region is not None:
        ctx.new_path()
        if isinstance(region, cairo.Path):
            ctx.append_path(region)
        else:
            region(ctx)
        ctx.clip()
    ctx.identity_matrix()
    ctx.rectangle(ix0, iy0, w, h)
    ctx.clip()
    ctx.set_operator(cairo.OPERATOR_MULTIPLY)
    ctx.set_source_surface(msurf, ix0, iy0)
    ctx.paint()
    ctx.restore()


# ----------------------------------------------------------------------------- rain glints
def rain_glints(ctx, t, box, color=HOT, alpha=0.5, density=1.0, seed=0, speed=1300.0,
                length=40.0, width=1.4, wind=0.16, weight=None):
    """Falling rain streaks caught in a light, inside world `box` (x0, y0, x1, y1).
    Draw on an additive context (f.light()). Each streak keeps its identity between frames.
    density: streaks per 10 000 world px^2; weight(x, y) -> 0..1 shapes the brightness."""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    if bw <= 0 or bh <= 0 or alpha <= 0.003:
        return
    n = int(bw * bh * density / 10000.0)
    span = bh + length
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(n):
        u = hash01(seed, k, 1)
        sp = speed * (0.8 + 0.4 * hash01(seed, k, 2))
        y = y0 - length + (hash01(seed, k, 3) * span + sp * t) % span
        x = x0 + u * bw + wind * (y - y0)
        if x > x1:
            x -= bw * math.ceil((x - x1) / bw)
        L = length * (0.6 + 0.8 * hash01(seed, k, 4))
        a = alpha * (0.35 + 0.65 * hash01(seed, k, 5))
        if weight is not None:
            a *= weight(x, y)
        if a < 0.01:
            continue
        ctx.move_to(x, y)
        ctx.line_to(x + wind * L, y + L)
        draw.rgba(ctx, color, a)
        ctx.stroke()


# ----------------------------------------------------------------------------- streak lights
def add_streaks(f, draw_fn, par=1.0, blur_v=18.0, blur_h=3.0, ds=4, gain=1.0):
    """Anisotropic additive light: draw_fn(ctx) paints light shapes in world coords (layer
    `par`) at 1/ds resolution; the result is blurred vertically (blur_v, blur_h in frame px
    at scale 1) and ADDED to the frame. Used for wet-street reflections and long glints."""
    cam = f.lcam(par)
    w, h = max(1, f.pw // ds), max(1, f.ph // ds)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(surf)
    c.set_operator(cairo.OPERATOR_ADD)
    c.set_matrix(cam.matrix(f.scale * w / f.pw))
    draw_fn(c)
    arr = surf_array(surf)
    if not arr.any():
        return
    sx = max(0.0, blur_h * f.scale / ds)
    sy = max(0.0, blur_v * f.scale / ds)
    fa = arr.astype(np.float32)
    if sx > 0.2 or sy > 0.2:
        fa = cv2.GaussianBlur(fa, (0, 0), sigmaX=max(sx, 0.01), sigmaY=max(sy, 0.01),
                              borderType=cv2.BORDER_REPLICATE)
    if gain != 1.0:
        fa *= gain
    arr[...] = np.clip(fa, 0, 255).astype(np.uint8)
    surf.mark_dirty()
    with f.screen() as S:
        S.set_operator(cairo.OPERATOR_ADD)
        pat = cairo.SurfacePattern(surf)
        pat.set_filter(cairo.FILTER_BILINEAR)
        pat.set_matrix(cairo.Matrix(xx=w / float(W), yy=h / float(H)))
        S.set_source(pat)
        S.paint()


def occlude_emit(f, par, path_fn, even_odd=False):
    """Erase the emissive (bloom) buffer under an occluder. f.emit glows are added at
    finish(), after every layer, so a wall drawn in front of lit windows cannot hide their
    bloom by itself: call this with the occluder's outline (path_fn(ctx) builds it in world
    coords; even_odd for a wall with holes)."""
    with f.emit(par=par) as G:
        G.save()
        G.new_path()
        path_fn(G)
        if even_odd:
            G.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        G.set_operator(cairo.OPERATOR_CLEAR)
        G.fill()
        G.restore()


# ----------------------------------------------------------------------------- glows
def glow(ctx, c, r, rgb, a=1.0, core=0.0):
    """Soft radial light (additive contexts)."""
    if a <= 0.002 or r <= 0.5:
        return
    draw.radial(ctx, c, r * core, r, [(0, rgb, a), (0.3, rgb, a * 0.42), (0.65, rgb, a * 0.12), (1, rgb, 0.0)])
    ctx.new_path()
    ctx.arc(c[0], c[1], r, 0, 2 * math.pi)
    ctx.fill()


def glow_ellipse(ctx, c, rx, ry, rgb, a=1.0, angle=0.0):
    """Elliptical soft light (a light pool on a floor or a wall)."""
    if a <= 0.002:
        return
    ctx.save()
    ctx.translate(c[0], c[1])
    ctx.rotate(math.radians(angle))
    ctx.scale(max(rx, 0.1), max(ry, 0.1))
    draw.radial(ctx, (0, 0), 0, 1, [(0, rgb, a), (0.4, rgb, a * 0.45), (1, rgb, 0.0)])
    ctx.new_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def cone(ctx, apex, angle, spread, length, rgb, a=0.3, r0=0.0, falloff=0.85, soft_edge=0.35):
    """Additive light cone from apex toward `angle` (deg, 0 = +x, 90 = down) with half-angle
    `spread`. Brightness falls off along the cone and is softened at its edges."""
    if a <= 0.002:
        return
    ang = math.radians(angle)
    sp = math.radians(spread)
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    tip_w = r0
    far_w = length * math.tan(sp)
    p0 = (apex[0] + nx * tip_w, apex[1] + ny * tip_w)
    p1 = (apex[0] - nx * tip_w, apex[1] - ny * tip_w)
    q = (apex[0] + ux * length, apex[1] + uy * length)
    p2 = (q[0] - nx * far_w, q[1] - ny * far_w)
    p3 = (q[0] + nx * far_w, q[1] + ny * far_w)
    # along-axis falloff
    draw.linear(ctx, apex, q, [(0, rgb, a), (0.35, rgb, a * 0.55), (falloff, rgb, a * 0.12), (1, rgb, 0.0)])
    ctx.new_path()
    draw.poly(ctx, [p0, p3, p2, p1])
    ctx.fill()
    # brighter core
    core_w = far_w * (1 - soft_edge)
    p2c = (q[0] - nx * core_w, q[1] - ny * core_w)
    p3c = (q[0] + nx * core_w, q[1] + ny * core_w)
    draw.linear(ctx, apex, q, [(0, rgb, a * 0.8), (0.5, rgb, a * 0.25), (1, rgb, 0.0)])
    ctx.new_path()
    draw.poly(ctx, [apex, p3c, p2c])
    ctx.fill()


# ----------------------------------------------------------------------------- misc
def sway(t, seed=0, amp=1.0, rate=0.35):
    """Slow breeze-like sway value in [-amp, amp]."""
    return amp * fbm1(t * rate, seed)


def static_texture(key, w, h, feature, seed, beta=2.2):
    """Cached tileable noise texture (float32 0..1)."""
    from engine.core import noise_grid
    return cached(("sp_tex", key, w, h, feature, seed, beta),
                  lambda: noise_grid(w, h, feature=feature, seed=seed, beta=beta))


def texture_surface(key, w, h, feature, seed, rgb, a_lo, a_hi, beta=2.2, streak=0.0):
    """Cached premultiplied ARGB surface: rgb with alpha varying a_lo..a_hi by noise.
    streak > 0 stretches the noise vertically (rain stains running down a wall)."""
    def build():
        T = static_texture(key, w, h, feature, seed, beta)
        if streak > 0:
            T = cv2.GaussianBlur(T, (0, 0), sigmaX=0.6, sigmaY=max(0.6, streak))
            T = (T - T.min()) / max(1e-6, T.max() - T.min())
        a = a_lo + (a_hi - a_lo) * T
        arr = np.empty((h, w, 4), np.float32)
        arr[..., 0] = rgb[2] * a * 255
        arr[..., 1] = rgb[1] * a * 255
        arr[..., 2] = rgb[0] * a * 255
        arr[..., 3] = a * 255
        return array_surface(arr)
    return cached(("sp_texsurf", key, w, h, feature, seed, rgb, a_lo, a_hi, beta, streak), build)


def camera_for(point, zoom=1.0, par=1.0, rot=0.0, origin=(W / 2, H / 2)):
    """Main Camera that centres world `point` of a layer with parallax `par` on screen with
    that layer appearing at `zoom` (inverts Camera.parallax)."""
    ox, oy = origin
    p = max(par, 1e-6)
    cx = ox + (point[0] - ox) / p
    cy = oy + (point[1] - oy) / p
    z = 1.0 + (zoom - 1.0) / p
    return Camera(cx, cy, max(z, 1e-3), rot)
