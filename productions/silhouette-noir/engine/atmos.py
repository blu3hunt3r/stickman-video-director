"""Atmosphere and effects for Silhouette Noir (SALVAGE, SHADOW PLAY, RED).

Light shafts, volumetric beams with occlusion, lamps and flicker, closed-form particles
(snow, rain, splashes, drips, bubbles, marine snow, dust, embers), water (surface from
below, waterline, caustics), weather (lightning, moon, ground mist), fire (flames, burning
fuses / webs) and underwater depth helpers. Everything is a pure function of time + seeds.

Conventions
    * Positions and lengths are WORLD units (frame px at zoom 1, y DOWN) seen through the
      camera of layer `par` (1 = action plane, <1 farther, >1 nearer), exactly as f.layer().
    * Angles are degrees, screen convention: 0 = +x (right), 90 = +y (DOWN). A lamp shining
      straight down is angle=90; light from the upper left falling to the right is ~60.
    * t=None means f.t (seconds). No effect keeps state: any frame renders alone, in any
      order, and t < 0 / t > T (transition handles) keep animating naturally.
    * Colors are RGB 0..1. color=None takes the palette's light (pal.light, pal.moon,
      pal.rain, pal.snow, pal.lightning, pal.surface ...). intensity ~ additive alpha.
    * Effects draw IMMEDIATELY onto the frame, in call order. Call them between layers (not
      inside a `with f.layer()` block) at the depth where they belong. Light is ADDED with
      numpy (cv2.add), 3-5x cheaper than f.light(); `atmos.light(f, ...)` is a faster
      drop-in for f.light() that also accepts a world bbox.
    * Light objects (Cone, Glow, Shaft) returned by beam()/lamp()/window_light() describe
      where light is; pass them as `lit=` to particles so rain, dust and marine snow light
      up inside beams.

    cone = atmos.beam(f, apex=(540, 400), angle=80, length=1100, half_angle=13,
                      stop=((0, 1600), (1080, 1600)), occluder=draw_diver, dust=1.0)
    atmos.rain(f, lit=cone)
"""
import heapq
import math
from contextlib import contextmanager

import cairo
import cv2
import numpy as np

from . import draw
from .core import W, H, clamp, lerp, hash01, noise1, fbm1, noise_grid, pulse
from .frame import surf_array, cached

TAU = 2.0 * math.pi
G_PX = 3300.0                   # gravity, world px/s^2 (an adult ~600 px ~ 1.75 m)
WHITE = (1.0, 1.0, 1.0)
_AA = cv2.LINE_AA
_SH = 4                         # cv2 sub-pixel shift bits
_SK = 16.0                      # 2**_SH

__all__ = [
    "auto_tint",
    "light", "Light", "Cone", "Glow", "Shaft", "lit_sum",
    "god_rays", "underwater_rays", "window_light", "beam", "lamp", "light_pool",
    "lantern_flicker", "candle_flicker", "bulb_flicker", "ember_glow", "fire_light", "flicker_value",
    "wind_at", "snow", "rain", "splashes", "drips", "bubbles", "exhale", "breathing",
    "marine_snow", "dust", "embers",
    "wave_y", "water_path", "water_split", "waterline", "surface_from_below", "caustics", "wet_reflection",
    "bolt_points", "flash_env", "lightning", "moon", "ground_mist",
    "flames", "Fuse", "burn_web", "burning", "burning_line",
    "depth_stops", "depth_color", "depth_light", "abyss",
]


# ============================================================================ helpers
def _now(f, t):
    return f.t if t is None else float(t)


def _rgb(c):
    return (float(c[0]), float(c[1]), float(c[2]))


def _mix(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k)


def _pal(f, name, default):
    v = getattr(f.pal, name, None)
    return _rgb(v) if v is not None else _rgb(default)


def _hot(c, k=0.75):
    """A light color pushed toward white (hot cores)."""
    return _mix(c, WHITE, k)


def _skylight(f):
    """Ambient sky/sun light of the palette (pale aqua under the sea, cool grey in town)."""
    return _mix(f.pal.fog_at(1.0), WHITE, 0.5)


def _ds(f, base):
    return max(1, int(round(base * f.scale)))


def _ss(e0, e1, x):
    """numpy smoothstep."""
    u = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)


def _M(f, par=1.0):
    """world -> output pixel matrix of layer `par`."""
    return f.lcam(par).matrix(f.scale)


def _xf(m, x, y):
    xx, yx, xy, yy, x0, y0 = tuple(m)
    return xx * x + xy * y + x0, yx * x + yy * y + y0


def _inv(m):
    m = cairo.Matrix(*tuple(m))
    m.invert()
    return m


def _world1(f, par, x, y):
    """World coords of layer `par` -> world coords of the action plane (par 1)."""
    if par == 1.0:
        return x, y
    sx, sy = _xf(_M(f, par), x, y)
    return _xf(_inv(_M(f, 1.0)), sx, sy)


def _zoom(f, par=1.0):
    return f.lcam(par).zoom * f.scale


def _pxbox(f, par, bb, pad=0.0, align=1):
    """Output-pixel box (X0, Y0, X1, Y1) covering world bbox bb through layer par, padded,
    clipped to the frame and aligned to `align`. None if off-screen."""
    m = _M(f, par)
    xs, ys = _xf(m, np.array([bb[0], bb[2], bb[0], bb[2]], float),
                 np.array([bb[1], bb[1], bb[3], bb[3]], float))
    X0 = max(0, int(math.floor((xs.min() - pad) / align)) * align)
    Y0 = max(0, int(math.floor((ys.min() - pad) / align)) * align)
    X1 = min(f.pw, int(math.ceil((xs.max() + pad) / align)) * align)
    Y1 = min(f.ph, int(math.ceil((ys.max() + pad) / align)) * align)
    if X1 - X0 < 1 or Y1 - Y0 < 1:
        return None
    return X0, Y0, X1, Y1


def _grid(f, par, box, ds):
    """World coords of the centers of a ds-downsampled pixel grid over `box` (broadcastable)."""
    X0, Y0, X1, Y1 = box
    gw, gh = -(-(X1 - X0) // ds), -(-(Y1 - Y0) // ds)
    px = X0 + (np.arange(gw, dtype=np.float32) + 0.5) * ds
    py = Y0 + (np.arange(gh, dtype=np.float32) + 0.5) * ds
    xx, yx, xy, yy, x0, y0 = tuple(_inv(_M(f, par)))
    if abs(xy) < 1e-9 and abs(yx) < 1e-9:
        wx = (xx * px + x0)[None, :]
        wy = (yy * py + y0)[:, None]
    else:
        wx = xx * px[None, :] + xy * py[:, None] + x0
        wy = yx * px[None, :] + yy * py[:, None] + y0
    return wx.astype(np.float32), wy.astype(np.float32), gw, gh


def _grid_affine(f, par, box, ds):
    """2x3 affine (grid j, i) -> world (x, y)."""
    X0, Y0 = box[0], box[1]
    xx, yx, xy, yy, x0, y0 = tuple(_inv(_M(f, par)))
    # output px X = X0 + (j + 0.5) ds
    ax = np.array([[xx * ds, xy * ds, xx * (X0 + 0.5 * ds) + xy * (Y0 + 0.5 * ds) + x0],
                   [yx * ds, yy * ds, yx * (X0 + 0.5 * ds) + yy * (Y0 + 0.5 * ds) + y0]], np.float64)
    return ax


def _add(f, img, X0=0, Y0=0, ds=1, sigma=0.0):
    """ADD a premultiplied BGRA uint8 image (at 1/ds resolution, top-left at output px X0, Y0)
    into the frame canvas."""
    if sigma > 0.25:
        img = cv2.GaussianBlur(img, (0, 0), float(sigma))
    if ds > 1:
        img = cv2.resize(img, (img.shape[1] * ds, img.shape[0] * ds), interpolation=cv2.INTER_LINEAR)
    h, w = img.shape[:2]
    x0, y0 = max(0, X0), max(0, Y0)
    x1, y1 = min(f.pw, X0 + w), min(f.ph, Y0 + h)
    if x1 <= x0 or y1 <= y0:
        return
    dst = surf_array(f.surf)[y0:y1, x0:x1]
    cv2.add(dst, img[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0], dst=dst)
    f.surf.mark_dirty()


def _bgra(I, rgb, gain=1.0):
    """float intensity field (h, w) * color -> BGRA uint8 (additive light)."""
    I = np.ascontiguousarray(I, dtype=np.float32)
    ch = [cv2.convertScaleAbs(I, alpha=255.0 * gain * c) for c in (rgb[2], rgb[1], rgb[0])]
    ch.append(np.zeros_like(ch[0]))
    return cv2.merge(ch)


def _over(f, img, X0, Y0, ds=1):
    """Composite a premultiplied BGRA uint8 image (1/ds res) OVER the frame (cairo fast path)."""
    img = np.ascontiguousarray(img)
    h, w = img.shape[:2]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    surf_array(surf)[...] = img
    surf.mark_dirty()
    c = f.ctx
    c.save()
    c.identity_matrix()
    pat = cairo.SurfacePattern(surf)
    pat.set_filter(cairo.FILTER_BILINEAR if ds > 1 else cairo.FILTER_FAST)
    pat.set_matrix(cairo.Matrix(xx=1.0 / ds, yy=1.0 / ds, x0=-X0 / ds, y0=-Y0 / ds))
    c.set_source(pat)
    c.rectangle(X0, Y0, w * ds, h * ds)
    c.fill()
    c.restore()


_SCR = {}


def _scratch(h, w):
    """Reusable zeroed BGRA canvas (h, w) for particle drawing."""
    b = _SCR.get((h, w))
    if b is None:
        b = _SCR[(h, w)] = np.zeros((h, w, 4), np.uint8)
    else:
        b.fill(0)
    return b


def _canvas(f, box, ds=1):
    """Zeroed BGRA canvas for an output-pixel box at 1/ds res."""
    X0, Y0, X1, Y1 = box
    h, w = -(-(Y1 - Y0) // ds), -(-(X1 - X0) // ds)
    if X0 == 0 and Y0 == 0 and X1 == f.pw and Y1 == f.ph:
        return _scratch(h, w)
    return np.zeros((h, w, 4), np.uint8)


def _canvas_matrix(f, par, box, ds):
    """world (layer par) -> canvas px matrix, in cv2 pixel-center convention."""
    X0, Y0 = box[0], box[1]
    return _M(f, par).multiply(cairo.Matrix(x0=-X0 - 0.5, y0=-Y0 - 0.5)).multiply(
        cairo.Matrix(xx=1.0 / ds, yy=1.0 / ds))


def _cv(col, b):
    """cv2 BGRA color for an RGB light color at brightness b."""
    return (min(255.0, 255.0 * col[2] * b), min(255.0, 255.0 * col[1] * b), min(255.0, 255.0 * col[0] * b), 0.0)


@contextmanager
def _main(f, par=1.0, op=None):
    """The frame canvas with layer `par`'s camera (and an optional cairo operator)."""
    c = f.ctx
    c.save()
    c.set_matrix(_M(f, par))
    if op is not None:
        c.set_operator(op)
    try:
        yield c
    finally:
        c.restore()


class _Null:
    """Context that swallows drawing (for off-screen light layers)."""

    def __getattr__(self, name):
        return lambda *a, **k: None


@contextmanager
def light(f, par=1.0, blur=6.0, alpha=1.0, ds=None, bbox=None, tint=0.0):
    """Additive light layer: a faster drop-in for f.light() (numpy ADD instead of cairo's slow
    scaled ADD). Draw in world coords of layer `par` with the yielded cairo context (operator
    ADD). blur: softness in screen px. ds: force a downsample factor (default from blur).
    bbox=(x0, y0, x1, y1) world: only that region is allocated and composited (much cheaper
    for small lights). tint 0..1: that fraction of the light is laid OVER as a colored veil
    instead of added (on bright backgrounds added light only bleaches toward white)."""
    blur_px = max(0.0, blur * f.scale)
    if ds:
        k = max(1, int(ds))
    else:
        k = int(clamp(round(blur_px / 2.5), 1, 8)) if blur_px >= 1 else 1
    if bbox is None:
        box = (0, 0, f.pw, f.ph)
    else:
        box = _pxbox(f, par, bbox, pad=3.0 * blur_px + 2 * k, align=k)
    if box is None:
        yield _Null()
        return
    X0, Y0, X1, Y1 = box
    lw, lh = max(1, -(-(X1 - X0) // k)), max(1, -(-(Y1 - Y0) // k))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, lw, lh)
    c = cairo.Context(surf)
    c.set_operator(cairo.OPERATOR_ADD)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_matrix(_M(f, par).multiply(cairo.Matrix(x0=-X0, y0=-Y0)).multiply(cairo.Matrix(xx=1.0 / k, yy=1.0 / k)))
    try:
        yield c
    finally:
        surf.flush()
        arr = surf_array(surf)
        if alpha != 1.0:
            arr = cv2.convertScaleAbs(arr, alpha=float(max(alpha, 0.0)))
        if tint > 0.0:
            if blur_px / k > 0.25:
                arr = cv2.GaussianBlur(arr, (0, 0), blur_px / k)
            _over(f, cv2.convertScaleAbs(arr, alpha=float(TINT_GAIN * min(tint, 1.0))), X0, Y0, k)
            if tint < 1.0:
                _add(f, cv2.convertScaleAbs(arr, alpha=float(1.0 - tint)), X0, Y0, k, 0.0)
        else:
            _add(f, arr, X0, Y0, k, blur_px / k)


TINT_GAIN = 1.4


def auto_tint(f, tint=None):
    """The `tint` an effect uses when given None: ~0.75 on bright palettes (RED's daylight
    fog, where a lantern or fire should color the fog, not bleach it), 0 on dark ones."""
    if tint is not None:
        return clamp(tint)
    fog = _rgb(f.pal.fog_at(0.5))
    lum = 0.3 * fog[0] + 0.59 * fog[1] + 0.11 * fog[2]
    return clamp((lum - 0.3) / 0.25) * 0.75


# ---------------------------------------------------------------------------- randomness
_M32 = np.uint64(0xFFFFFFFF)


def _vhash(*args):
    """Vectorized deterministic hash of integer arrays -> float64 in [0, 1)."""
    h = np.uint64(0x811C9DC5)
    for a in args:
        a = np.asarray(a).astype(np.int64).astype(np.uint64) & _M32
        h = (h ^ a) & _M32
        h = (h * np.uint64(0x01000193)) & _M32
        h = h ^ (h >> np.uint64(13))
        h = (h * np.uint64(0x5BD1E995)) & _M32
        h = h ^ (h >> np.uint64(15))
    return (h & np.uint64(0xFFFFFF)).astype(np.float64) / 16777216.0


def _rand(seed, n, k):
    """(k, n) uniform randoms, fixed for (seed, n, k) - per-particle constants."""
    return cached(("atmos_rand", int(seed), int(n), int(k)),
                  lambda: np.random.default_rng([int(seed) & 0xFFFFFFFF, int(n), int(k), 7]).random((k, n)))


def _vnoise(x, seed=0):
    """Vectorized smooth 1D value noise in [-1, 1]."""
    x = np.asarray(x, np.float64)
    i = np.floor(x)
    fr = x - i
    a = _vhash(seed, i) * 2 - 1
    b = _vhash(seed, i + 1) * 2 - 1
    u = fr * fr * (3 - 2 * fr)
    return a + (b - a) * u


def _tex(seed, size=256, feature=40.0, beta=2.4):
    return cached(("atmos_tex", seed, size, feature, beta),
                  lambda: noise_grid(size, size, feature=feature, seed=seed, beta=beta))


def _sample(T, u, v):
    """Bilinear, wrapped sample of a tileable texture at texel coords (u = col, v = row)."""
    th, tw = T.shape[:2]
    u, v = np.broadcast_arrays(np.mod(u, tw), np.mod(v, th))
    return cv2.remap(T, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_WRAP)


def _fog(wx, wy, t, seed=0, drift=(10.0, -4.0), scale=1.0):
    """Slowly drifting volumetric fog density (0..1, mean ~0.5) at world coords."""
    T1 = _tex(9100 + seed, 256, 34.0)
    T2 = _tex(9200 + seed, 256, 16.0)
    s1, s2 = 3.2 * scale, 1.7 * scale
    n1 = _sample(T1, (wx + drift[0] * t) / s1, (wy + drift[1] * t) / s1)
    n2 = _sample(T2, (wx - 0.7 * drift[0] * t) / s2 + 71.0, (wy + 0.5 * drift[1] * t) / s2 + 13.0)
    return 0.62 * n1 + 0.38 * n2


def _wrap(f, par, x, y, tw, th, margin):
    """Periodic copies (period tw x th world px) of points that fall in the layer's view."""
    vx0, vy0, vx1, vy1 = f.lcam(par).view_rect(margin)
    x = vx0 + np.mod(x - vx0, tw)
    y = vy0 + np.mod(y - vy0, th)
    nx = max(1, int(math.ceil((vx1 - vx0) / tw)))
    ny = max(1, int(math.ceil((vy1 - vy0) / th)))
    idx = np.arange(x.size)
    if nx == 1 and ny == 1:
        keep = (x <= vx1) & (y <= vy1)
        return x[keep], y[keep], idx[keep]
    XS, YS, IS = [], [], []
    for i in range(nx):
        for j in range(ny):
            xx, yy = x + i * tw, y + j * th
            keep = (xx <= vx1) & (yy <= vy1)
            XS.append(xx[keep])
            YS.append(yy[keep])
            IS.append(idx[keep])
    return np.concatenate(XS), np.concatenate(YS), np.concatenate(IS)


# ============================================================================ light regions
class Light:
    """Where light is. lit(x, y) takes ACTION-PLANE world coords (numpy arrays or floats) and
    returns intensity >= 0 (about 0..1). Used as `lit=` by particles. Combine with lit_sum()."""
    color = WHITE
    intensity = 1.0

    def lit(self, x, y):
        return np.zeros(np.broadcast(np.asarray(x), np.asarray(y)).shape)

    def bbox(self):
        return (0.0, 0.0, 0.0, 0.0)

    def __call__(self, x, y):
        return self.lit(x, y)


def lit_sum(*lights):
    """Combine several Light objects / callables into one lit(x, y) (sum)."""
    ls = [l for l in lights if l is not None]

    class _Sum(Light):
        color = ls[0].color if ls and hasattr(ls[0], "color") else WHITE

        def lit(self, x, y):
            out = 0.0
            for l in ls:
                out = out + l(x, y)
            return out

        def bbox(self):
            bbs = [l.bbox() for l in ls if hasattr(l, "bbox")]
            return (min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs))
    return _Sum()


def _litfn(lit, lit_color, f):
    if lit is None:
        return None, None
    if isinstance(lit, (list, tuple)) and lit and not isinstance(lit[0], (int, float)):
        lit = lit_sum(*lit)
    col = _rgb(lit_color) if lit_color is not None else _rgb(getattr(lit, "color", f.pal.light))
    return lit, col


class _Shadow:
    """Polar shadow map around a cone apex (built by beam(occluder=...))."""

    def __init__(self, S, apex, ux, uy, hrad, step):
        self.S, self.ax, self.ay, self.ux, self.uy, self.hrad, self.step = S, apex[0], apex[1], ux, uy, hrad, step
        self.nr, self.nphi = S.shape

    def coords(self, x, y):
        dx, dy = x - self.ax, y - self.ay
        al = dx * self.ux + dy * self.uy
        lat = dy * self.ux - dx * self.uy
        phi = np.arctan2(lat, al)
        ci = (phi + self.hrad) / (2 * self.hrad) * (self.nphi - 1)
        ri = np.hypot(dx, dy) / self.step
        return ci, ri

    def field(self, x, y):
        ci, ri = self.coords(x, y)
        ci, ri = np.broadcast_arrays(ci, ri)
        return cv2.remap(self.S, ci.astype(np.float32), ri.astype(np.float32), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REPLICATE)

    def sample(self, x, y):
        ci, ri = self.coords(np.asarray(x, float), np.asarray(y, float))
        ci = np.clip(np.rint(ci), 0, self.nphi - 1).astype(int)
        ri = np.clip(np.rint(ri), 0, self.nr - 1).astype(int)
        return self.S[ri, ci]


class Cone(Light):
    """A volumetric cone of light (see beam()). World coords of the layer it was drawn in."""

    def __init__(self, apex, angle, length, half_angle, intensity=1.0, falloff=1.0, soft=0.45,
                 color=WHITE, stop=None, par=1.0):
        self.apex = (float(apex[0]), float(apex[1]))
        self.angle = float(angle)
        a = math.radians(angle)
        self.ux, self.uy = math.cos(a), math.sin(a)
        self.length = float(length)
        self.half = float(half_angle)
        self.tanh = math.tan(math.radians(clamp(half_angle, 0.3, 80.0)))
        self.intensity, self.falloff, self.soft = float(intensity), float(falloff), float(soft)
        self.color = _rgb(color)
        self.stop = stop
        self.par = par
        self.shadow = None
        self.hit = None
        if stop is not None:
            (sx0, sy0), (sx1, sy1) = stop
            tx, ty = sx1 - sx0, sy1 - sy0
            L = math.hypot(tx, ty) or 1.0
            tx, ty = tx / L, ty / L
            nx, ny = -ty, tx
            side = (self.apex[0] - sx0) * nx + (self.apex[1] - sy0) * ny
            if side < 0:
                nx, ny, side = -nx, -ny, -side
            self._sn = (sx0, sy0, nx, ny, tx, ty)
            den = self.ux * nx + self.uy * ny
            if den < -1e-4:
                dist = side / -den
                if dist < self.length * 1.05:
                    self.hit = (self.apex[0] + self.ux * dist, self.apex[1] + self.uy * dist, dist, -den)

    def profile(self, x, y):
        """(intensity, along, lateral, r) of the bare cone (no fog, no occlusion)."""
        dx, dy = x - self.apex[0], y - self.apex[1]
        al = dx * self.ux + dy * self.uy
        lat = dy * self.ux - dx * self.uy
        r = np.abs(lat) / (np.maximum(al, 1e-3) * self.tanh)
        s = self.soft
        ang = 1.0 - _ss(1.0 - s, 1.0 + 0.3 * s, r)
        L = self.length
        L0 = 0.22 * L
        alp = np.maximum(al, 0.0)
        lon = (L0 / (L0 + alp)) ** self.falloff
        lon = lon * _ss(0.0, 0.02 * L + 3.0, al) * (1.0 - _ss(0.62 * L, L, al))
        I = self.intensity * ang * lon
        if self.stop is not None:
            sx0, sy0, nx, ny, _, _ = self._sn
            I = I * _ss(-1.0, 5.0, (x - sx0) * nx + (y - sy0) * ny)
        return I, al, lat, r

    def lit(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        I = self.profile(x, y)[0]
        if self.shadow is not None:
            I = I * (1.0 - self.shadow_k * self.shadow.sample(x, y))
        return I

    def bbox(self, pad=0.0):
        h = math.radians(self.half * (1.0 + 0.3 * self.soft) + 1.0)
        a = math.radians(self.angle)
        L = self.length
        xs, ys = [self.apex[0]], [self.apex[1]]
        for k in range(9):
            ang = a - h + 2 * h * k / 8.0
            xs.append(self.apex[0] + L / math.cos(h) * math.cos(ang))
            ys.append(self.apex[1] + L / math.cos(h) * math.sin(ang))
        return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


class Glow(Light):
    """Point light: intensity / (1 + (d / radius)^2), fading out at reach * radius."""

    def __init__(self, c, radius, intensity=1.0, color=WHITE, reach=5.0):
        self.c = (float(c[0]), float(c[1]))
        self.r, self.intensity, self.color, self.reach = float(radius), float(intensity), _rgb(color), float(reach)

    def lit(self, x, y):
        d2 = ((np.asarray(x, float) - self.c[0]) ** 2 + (np.asarray(y, float) - self.c[1]) ** 2) / (self.r * self.r)
        R2 = self.reach * self.reach
        return self.intensity / (1.0 + d2) * (1.0 - _ss(0.3 * R2, R2, d2))

    def bbox(self):
        R = self.r * self.reach
        return (self.c[0] - R, self.c[1] - R, self.c[0] + R, self.c[1] + R)


class Shaft(Light):
    """Light through an opening: the volume between quad `a` (the opening, 4 points) and quad
    `b` (where the light lands, same winding), fading from a to b (see window_light())."""

    def __init__(self, a, b, intensity=1.0, color=WHITE, falloff=1.2, steps=18):
        self.a = np.asarray(a, float)
        self.b = np.asarray(b, float)
        self.intensity, self.color, self.falloff, self.steps = float(intensity), _rgb(color), float(falloff), steps

    def quad(self, s):
        return self.a + (self.b - self.a) * s

    def lit(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        best = np.zeros(np.broadcast(x, y).shape)
        for s in np.linspace(0.0, 1.0, self.steps):
            q = self.quad(s)
            sign = None
            inside = np.ones_like(best, dtype=bool)
            for i in range(4):
                (x0, y0), (x1, y1) = q[i], q[(i + 1) % 4]
                cr = (x - x0) * (y1 - y0) - (y - y0) * (x1 - x0)
                pos = cr >= 0
                sign = pos if sign is None else sign
                inside &= pos == sign
            best = np.maximum(best, inside * (1.0 - s) ** self.falloff)
        return self.intensity * best

    def bbox(self):
        P = np.vstack([self.a, self.b])
        return (P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max())


# ============================================================================ 1. shafts
GOD_PROFILE = ((0.0, 0.0), (0.08, 1.0), (0.3, 0.78), (0.55, 0.42), (0.8, 0.13), (1.0, 0.0))
SEA_PROFILE = ((0.0, 0.0), (0.02, 0.65), (0.1, 0.9), (0.25, 0.68), (0.5, 0.34), (0.78, 0.1), (1.0, 0.0))


def _shaft(ctx, p0, ang, L, w0, w1, col, I, profile=GOD_PROFILE):
    """One soft crepuscular shaft: nested trapezoids (a soft cross profile) with a lengthwise
    gradient `profile` [(offset 0..1, value), ...] (additive ctx)."""
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    nx, ny = -uy, ux
    p1 = (p0[0] + ux * L, p0[1] + uy * L)
    for wk, ak in ((1.0, 0.30), (0.62, 0.32), (0.30, 0.38)):
        g = cairo.LinearGradient(p0[0], p0[1], p1[0], p1[1])
        a = I * ak
        for o, v in profile:
            g.add_color_stop_rgba(o, col[0], col[1], col[2], clamp(a * v))
        ctx.set_source(g)
        a0, a1 = 0.5 * w0 * wk, 0.5 * w1 * wk
        ctx.move_to(p0[0] + nx * a0, p0[1] + ny * a0)
        ctx.line_to(p1[0] + nx * a1, p1[1] + ny * a1)
        ctx.line_to(p1[0] - nx * a1, p1[1] - ny * a1)
        ctx.line_to(p0[0] - nx * a0, p0[1] - ny * a0)
        ctx.close_path()
        ctx.fill()
    return p1


def god_rays(f, src, angle=95.0, length=1500.0, count=7, width=(40.0, 150.0), widen=1.8, spread=0.0,
             color=None, intensity=0.45, var=0.6, drift=40.0, rate=0.12, profile=GOD_PROFILE,
             t=None, seed=0, par=1.0, blur=18.0):
    """Crepuscular shafts (additive). src: a point (x, y) - shafts fan out `spread` degrees
    around `angle` - or a segment ((x0, y0), (x1, y1)) the shafts start along (canopy gap,
    skylight). width (min, max) px at the source, `widen` x at the far end. Intensity breathes
    with slow noise (var 0..1) at `rate` Hz; shafts slide up to `drift` px."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _skylight(f)
    point = not isinstance(src[0], (tuple, list))
    if point:
        a, b = src, src
        segL = 1.0
    else:
        a, b = src
        segL = max(1.0, math.hypot(b[0] - a[0], b[1] - a[1]))
    rays = []
    for i in range(count):
        h = [hash01(seed, i, k) for k in range(7)]
        u = (i + 0.5 + 0.8 * (h[0] - 0.5)) / count
        if not point:
            u += drift / segL * fbm1(t * rate + 13.1 * i, seed + 3)
        p0 = (lerp(a[0], b[0], u), lerp(a[1], b[1], u))
        ang = angle + spread * (u - 0.5) + 3.0 * (h[1] - 0.5) + 1.2 * noise1(t * rate * 0.8 + 7.3 * i, seed + 11)
        if point:
            ang += drift * 0.02 * fbm1(t * rate + 13.1 * i, seed + 3)
        w0 = lerp(width[0], width[1], h[2])
        w1 = w0 * widen * (0.8 + 0.4 * h[3])
        L = length * (0.65 + 0.35 * h[4])
        e = clamp(1.0 - var + var * (0.55 + 0.8 * fbm1(t * rate * 2.1 + 3.7 * i, seed + 23)))
        I = intensity * (0.45 + 0.55 * h[5]) * e
        if I > 0.003:
            rays.append((p0, ang, L, w0, w1, I))
    if not rays:
        return
    xs, ys = [], []
    for p0, ang, L, w0, w1, I in rays:
        xs += [p0[0] - w1, p0[0] + math.cos(math.radians(ang)) * L - w1, p0[0] + w1,
               p0[0] + math.cos(math.radians(ang)) * L + w1]
        ys += [p0[1] - w1, p0[1] + math.sin(math.radians(ang)) * L - w1, p0[1] + w1,
               p0[1] + math.sin(math.radians(ang)) * L + w1]
    with light(f, par=par, blur=blur, bbox=(min(xs), min(ys), max(xs), max(ys))) as A:
        for p0, ang, L, w0, w1, I in rays:
            _shaft(A, p0, ang, L, w0, w1, col, I, profile)


def underwater_rays(f, surface_y=0.0, t=None, spacing=120.0, angle=96.0, fan=12.0, length=2000.0,
                    width=(16.0, 75.0), widen=2.4, intensity=0.75, color=None, shimmer=1.0,
                    density=0.7, seed=0, par=1.0, blur=14.0):
    """Sun shafts hanging from the sea surface (world y = surface_y), fading with depth over
    `length` px. Anchored in world x every ~`spacing` px (so they stay put when the camera
    pans), fanning by `fan` degrees across the frame like perspective. shimmer scales the
    speed of the surface-wave flicker."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _mix(_pal(f, "surface", _skylight(f)), WHITE, 0.45)
    cam = f.lcam(par)
    vx0, vy0, vx1, vy1 = cam.view_rect(300.0)
    if vy0 > surface_y + length or vy1 < surface_y:
        return
    rays = []
    for i in range(int(math.floor(vx0 / spacing)) - 2, int(math.ceil(vx1 / spacing)) + 3):
        h = [hash01(seed, i, k) for k in range(7)]
        if h[6] > density:
            continue
        x = (i + 0.5 + 0.6 * (h[0] - 0.5)) * spacing + 22.0 * noise1(t * 0.22 * shimmer + 3.1 * i, seed)
        ang = angle + fan * (x - cam.x) / W + 2.0 * (h[1] - 0.5) + 0.8 * noise1(t * 0.3 * shimmer + i, seed + 5)
        env = clamp(0.35 + 0.9 * (0.5 + 0.5 * fbm1(t * 0.42 * shimmer + 1.7 * i, seed + 9)))
        env *= 0.88 + 0.12 * math.sin(t * 2.6 * shimmer + TAU * h[4])
        I = intensity * (0.35 + 0.65 * h[2]) * env ** 1.4
        w0 = lerp(width[0], width[1], h[3])
        L = length * (0.6 + 0.4 * h[5])
        if I > 0.004:
            rays.append(((x, surface_y), ang, L, w0, w0 * widen, I))
    if not rays:
        return
    with light(f, par=par, blur=blur, bbox=(vx0, max(vy0, surface_y - 50), vx1, min(vy1, surface_y + length))) as A:
        for p0, ang, L, w0, w1, I in rays:
            _shaft(A, p0, ang, L, w0, w1, col, I, SEA_PROFILE)


def _quad(window):
    if len(window) == 4 and isinstance(window[0], (int, float)):
        x0, y0, x1, y1 = window
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [tuple(map(float, p)) for p in window]


def _pane_quads(q, cols, rows, mullion):
    """Panes of a quad (bilinear in its 4 corners) separated by mullion gaps: list of 4-pt lists."""
    q = np.asarray(q, float)
    P = lambda u, v: (1 - u) * (1 - v) * q[0] + u * (1 - v) * q[1] + u * v * q[2] + (1 - u) * v * q[3]
    out = []
    gu, gv = mullion / max(cols, 1), mullion / max(rows, 1)
    for i in range(cols):
        for j in range(rows):
            u0, u1 = i / cols + (gu if i > 0 else 0), (i + 1) / cols - (gu if i < cols - 1 else 0)
            v0, v1 = j / rows + (gv if j > 0 else 0), (j + 1) / rows - (gv if j < rows - 1 else 0)
            out.append(np.array([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]))
    return out


def window_light(f, window, angle=60.0, length=700.0, to=None, color=None, intensity=0.55, falloff=1.1,
                 panes=(2, 2), mullion=0.07, patch=0.7, dust=0.0, steps=28, flicker=None,
                 t=None, seed=0, par=1.0, blur=8.0):
    """Light pouring through a window/doorway: the opening (rect (x0, y0, x1, y1) or 4 points)
    swept `length` px along `angle` - or morphed into the quad `to` (4 points, same winding:
    where the light lands, e.g. a floor patch in perspective) - as a slanted volume with
    mullion shadows (panes=(cols, rows), mullion = bar width as a fraction), fading with
    distance, a brighter `patch` where it lands and optional dust motes. Returns a Shaft."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _rgb(f.pal.light)
    qa = np.asarray(_quad(window), float)
    if to is not None:
        qb = np.asarray(_quad(to), float)
    else:
        D = np.array([math.cos(math.radians(angle)), math.sin(math.radians(angle))]) * length
        qb = qa + D
    k = intensity * flicker_value(flicker, t, seed)
    shaft = Shaft(qa, qb, k, col, falloff)
    if k <= 0.002:
        return shaft
    cols, rows = panes if panes else (1, 1)
    pa, pb = _pane_quads(qa, cols, rows, mullion), _pane_quads(qb, cols, rows, mullion)
    # how many stacked copies cover a point while the opening slides past it -> normalize
    D = qb.mean(0) - qa.mean(0)
    Ld = float(np.hypot(*D)) or 1.0
    ux, uy = D / Ld
    wv, hv = np.ptp(qa[:, 0]) or 1.0, np.ptp(qa[:, 1]) or 1.0
    chord = min(wv / max(abs(ux), 1e-3), hv / max(abs(uy), 1e-3))
    cover = max(1.0, steps * min(1.0, chord / Ld))
    with light(f, par=par, blur=blur, bbox=shaft.bbox()) as A:
        for s_i in range(steps):
            s = (s_i + 0.5) / steps
            a = k / cover * (1.0 - s) ** falloff * _ss(0.0, 0.06, s)
            if a <= 0.0005:
                continue
            for qa_, qb_ in zip(pa, pb):
                draw.poly(A, (qa_ + (qb_ - qa_) * s).tolist())
            A.set_source_rgba(col[0], col[1], col[2], float(a))
            A.fill()
        if patch > 0:
            for qb_ in pb:
                draw.poly(A, qb_.tolist())
            A.set_source_rgba(col[0], col[1], col[2], float(clamp(patch * k * 0.6)))
            A.fill()
    if dust > 0:
        globals()["dust"](f, shaft, density=dust, t=t, seed=seed + 11, par=par)
    return shaft


# ============================================================================ 2. beam
def _occlusion(f, par, cone, occluder, box, ds, wx, wy, penumbra):
    """Shadow field (0..1) behind silhouettes drawn by occluder(ctx), cast from cone.apex."""
    X0, Y0, X1, Y1 = box
    gw, gh = wx.shape[1] if wx.ndim == 2 else wx.size, wy.shape[0]
    ms = cairo.ImageSurface(cairo.FORMAT_A8, gw, gh)
    mc = cairo.Context(ms)
    m = _M(f, par).multiply(cairo.Matrix(x0=-X0, y0=-Y0)).multiply(cairo.Matrix(xx=1.0 / ds, yy=1.0 / ds))
    mc.set_matrix(m)
    mc.set_source_rgba(0, 0, 0, 1)
    occluder(mc)
    mc.fill()
    ms.flush()
    mask = np.ndarray((gh, ms.get_stride()), np.uint8, buffer=ms.get_data())[:, :gw].astype(np.float32) * (1 / 255.0)
    if not mask.any():
        return None
    hrad = math.radians(cone.half * (1.0 + 0.3 * cone.soft) + 3.0)
    step = ds / _zoom(f, par)
    nphi = int(clamp(2 * hrad / math.radians(0.12), 64, 900))
    rmax = cone.length * 1.08 + 40.0
    nr = int(rmax / step) + 2
    phis = np.linspace(-hrad, hrad, nphi)
    ang = math.radians(cone.angle) + phis
    rhos = np.arange(nr) * step
    PX = cone.apex[0] + rhos[:, None] * np.cos(ang)[None, :]
    PY = cone.apex[1] + rhos[:, None] * np.sin(ang)[None, :]
    gx, gy = _xf(m, PX, PY)
    Mp = cv2.remap(mask, (gx - 0.5).astype(np.float32), (gy - 0.5).astype(np.float32), cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    S = np.maximum.accumulate(Mp, axis=0)
    # splash: where the beam first strikes a silhouette, lighting a thin band of its face
    Hh = np.zeros_like(S)
    Hh[1:] = np.maximum(S[1:] - S[:-1], 0.0)
    band = max(2, int(round(9.0 / step)))
    H2 = Hh.copy()
    for kk in range(1, band + 1):
        H2[kk:] += Hh[:-kk] * math.exp(-kk / (0.45 * band))
    Ip = cone.profile(PX, PY)[0].astype(np.float32)
    splash = cv2.GaussianBlur(H2 * Ip, (0, 0), sigmaX=1.2, sigmaY=0.7)
    S = cv2.GaussianBlur(S, (0, 0), sigmaX=0.8 + penumbra, sigmaY=0.8)
    sh = _Shadow(S, cone.apex, cone.ux, cone.uy, hrad, step)
    sh.splash = _Shadow(splash, cone.apex, cone.ux, cone.uy, hrad, step)
    return sh


def beam(f, apex, angle, length=900.0, half_angle=12.0, color=None, intensity=0.8, falloff=1.0,
         soft=0.45, core=0.5, fog=0.45, stop=None, pool=0.6, pool_squash=0.3, occluder=None,
         shadow=0.94, penumbra=1.5, splash=1.0, dust=0.0, glare=1.0, t=None, seed=0, par=1.0,
         drift=(10.0, -4.0)):
    """Volumetric cone of light: flashlight, helmet lamp, lantern, police torch, projector.

    apex: lamp position; angle: direction (deg, 90 = down); length px; half_angle deg.
    intensity: additive alpha near the lamp; falloff: decay exponent with distance;
    soft: edge softness (0 hard .. 1 very soft); core: brighter axis; fog: drifting
    volumetric texture inside the beam (0..1).
    stop=((x0, y0), (x1, y1)): a surface line (floor, wall, sheet) that ends the beam; a
        light `pool` (0..1, squashed by pool_squash across the line) is drawn where it lands.
    occluder(ctx): draws filled silhouettes in world coords (on a mask); they block the beam
        and cast a dark gap behind them (shadow 0..1, penumbra in polar px). `splash` lights
        the face where the beam strikes them - draw those silhouettes BEFORE beam() to see it.
    dust: density of floating motes lit by the beam (0 = none, 1 = typical).
    glare: hot glow at the lamp head (emit + light).
    Returns a Cone (pass it as lit= to rain/dust/marine_snow)."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _rgb(f.pal.light)
    cone = Cone(apex, angle, length, half_angle, intensity, falloff, soft, col, stop, par)
    cone.shadow_k = shadow
    ds = _ds(f, 3)
    rg = 22.0
    bb = list(cone.bbox())
    bb = [min(bb[0], apex[0] - rg * 4), min(bb[1], apex[1] - rg * 4), max(bb[2], apex[0] + rg * 4), max(bb[3], apex[1] + rg * 4)]
    if cone.hit is not None and pool > 0:
        hx, hy, dist, cosi = cone.hit
        rx = dist * cone.tanh / max(cosi, 0.25) * 1.25
        bb = [min(bb[0], hx - rx), min(bb[1], hy - rx), max(bb[2], hx + rx), max(bb[3], hy + rx)]
    box = _pxbox(f, par, bb, pad=2 * ds, align=ds)
    if box is not None and intensity > 0.001:
        wx, wy, gw, gh = _grid(f, par, box, ds)
        I, al, lat, r = cone.profile(wx, wy)
        if core > 0:
            I = I * ((1.0 - core) + core * 2.1 * np.exp(-(r / 0.4) ** 2))
        if fog > 0:
            N = _fog(wx, wy, t, seed, drift)
            I = I * ((1.0 - fog) + fog * 2.0 * N)
        shf = None
        if occluder is not None:
            cone.shadow = _occlusion(f, par, cone, occluder, box, ds, wx, wy, penumbra)
            if cone.shadow is not None:
                shf = cone.shadow.field(wx, wy)
                I = I * (1.0 - shadow * shf)
                if splash > 0:
                    sp = cone.shadow.splash.field(wx, wy)
                    I = I + splash * (sp * 1.1 + cv2.GaussianBlur(sp, (0, 0), 5.0 * f.scale / ds + 0.5) * 1.6)
        if cone.hit is not None and pool > 0:
            hx, hy, dist, cosi = cone.hit
            sx0, sy0, nx, ny, tx, ty = cone._sn
            rx = dist * cone.tanh / max(cosi, 0.25)
            ry = rx * pool_squash
            du = (wx - hx) * tx + (wy - hy) * ty
            dv = (wx - hx) * nx + (wy - hy) * ny
            q = (du / rx) ** 2 + (dv / ry) ** 2
            lon = (0.5 * length / (0.5 * length + dist)) ** (0.5 * falloff)
            P = pool * intensity * lon * (0.55 * np.exp(-q * 1.6) + 0.35 * (1.0 - _ss(0.5, 1.05, np.sqrt(q))))
            if shf is not None:
                P = P * (1.0 - shadow * shf)
            I = I + P
        if glare > 0:
            d2 = ((wx - apex[0]) ** 2 + (wy - apex[1]) ** 2) / (rg * rg)
            I = I + glare * min(intensity, 1.0) * (0.55 * np.exp(-d2) + 0.18 / (1.0 + d2 * 0.35))
        _add(f, _bgra(I, col), box[0], box[1], ds)
    if glare > 0:
        g = glare * min(intensity, 1.2)
        with f.emit(par) as G:
            draw.glow_disc(G, apex, 30.0, _hot(col, 0.5), clamp(0.8 * g))
        with _main(f, par, cairo.OPERATOR_ADD) as C:
            draw.circle(C, apex, 4.5)
            draw.fill(C, _hot(col, 0.85), clamp(0.9 * g))
    if dust > 0:
        globals()["dust"](f, cone, density=dust, t=t, seed=seed + 7, par=par)
    return cone


# ============================================================================ 3. lamps, flicker
def lantern_flicker(t, seed=0):
    """Oil lantern behind glass: steady with soft breathing and rare gutters. ~0.7..1.05."""
    v = 0.93 + 0.05 * fbm1(t * 4.0, seed) + 0.025 * noise1(t * 11.0, seed + 3)
    g = max(0.0, noise1(t * 0.45, seed + 9)) ** 4
    return clamp(v - 0.25 * g, 0.0, 1.1)


def candle_flicker(t, seed=0):
    """Candle: lively flutter plus slow sway, occasional dips. ~0.6..1.05."""
    v = 0.86 + 0.09 * fbm1(t * 7.5, seed) + 0.05 * noise1(t * 17.0, seed + 1) + 0.04 * noise1(t * 1.1, seed + 2)
    g = max(0.0, noise1(t * 0.8, seed + 5)) ** 3
    return clamp(v - 0.22 * g, 0.0, 1.1)


def bulb_flicker(t, seed=0, dropouts=0.0, hum=0.015):
    """Electric bulb: steady with a faint hum; dropouts (0..1) = a failing bulb that stutters."""
    v = 1.0 - hum * (0.5 + 0.5 * math.sin(t * TAU * 12.0 + seed))
    if dropouts > 0:
        k = math.floor(t * 5.0)
        if hash01(seed + 7, k) < dropouts:
            ph = t * 5.0 - k
            v *= 0.08 + 0.92 * (abs(math.cos(ph * math.pi * 3.0)) > 0.55)
    return v


def ember_glow(t, seed=0, puffs=None, period=6.0):
    """Cigar / cigarette ember: dim breathing glow that flares on each puff. puffs: list of
    puff times (s); default one puff every `period` s. Returns ~0.3..1.0."""
    base = 0.36 + 0.06 * fbm1(t * 0.9, seed)
    if puffs is None:
        k = math.floor(t / period)
        puffs = [(k + j + 0.3 + 0.4 * hash01(seed, k + j)) * period for j in (-1, 0, 1)]
    flare = 0.0
    for tp in puffs:
        dt = t - tp
        if -0.6 < dt < 4.0:
            rise = clamp((dt + 0.6) / 0.6)
            flare = max(flare, (rise * rise * (3 - 2 * rise)) * (math.exp(-max(dt, 0.0) / 1.1)))
    return clamp(base + 0.64 * flare + 0.04 * noise1(t * 9.0, seed + 1), 0.0, 1.0)


def fire_light(t, seed=0, amount=1.0):
    """Firelight flicker multiplier for lighting other things (~0.7..1.08). amount scales the depth."""
    v = 0.86 + 0.09 * fbm1(t * 6.5, seed) + 0.05 * noise1(t * 15.0, seed + 1) + 0.04 * noise1(t * 1.2, seed + 2)
    return 1.0 + (v - 1.0) * amount


FLICKER = {"lantern": lantern_flicker, "candle": candle_flicker, "bulb": bulb_flicker,
           "ember": ember_glow, "fire": fire_light, "steady": lambda t, seed=0: 1.0}


def flicker_value(kind, t, seed=0):
    """kind: None/'steady' (1), a preset name in FLICKER, a float depth (generic flicker), or a
    callable(t) -> multiplier."""
    if kind is None:
        return 1.0
    if callable(kind):
        return float(kind(t))
    if isinstance(kind, (int, float)):
        return clamp(1.0 - kind * (0.5 + 0.5 * fbm1(t * 8.0, seed)), 0.0, 1.2)
    return FLICKER[kind](t, seed)


def lamp(f, c, radius=40.0, color=None, intensity=1.0, flicker=None, halo=5.0, core=0.22, pool=None,
         t=None, seed=0, par=1.0, emit=1.0, tint=None):
    """A lamp halo / point light: soft additive halo (radius * halo px), emissive glow, a crisp
    hot core (core * radius px, 0 = none) and an optional light pool on the ground:
    pool=dict(y=ground_y, rx=..., ry=..., intensity=...). flicker: None, 'lantern', 'candle',
    'bulb', 'ember', 'fire', a float depth or callable. tint: see light() (None = auto_tint).
    Returns a Glow (for lit=)."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _rgb(f.pal.light)
    k = intensity * flicker_value(flicker, t, seed)
    tint = auto_tint(f, tint)
    glow = Glow(c, radius * 1.6, k, col, reach=halo / 1.6)
    if k <= 0.002:
        return glow
    R = radius * halo
    bb = [c[0] - R, c[1] - R, c[0] + R, c[1] + R]
    if pool:
        py = pool.get("y", c[1] + 300)
        prx = pool.get("rx", radius * 6)
        pry = pool.get("ry", prx * 0.22)
        bb = [min(bb[0], c[0] - prx), min(bb[1], py - pry), max(bb[2], c[0] + prx), max(bb[3], py + pry)]
    with light(f, par=par, blur=0, ds=_ds(f, 4), bbox=bb, tint=tint) as A:
        r0 = 1.0 / halo
        g = cairo.RadialGradient(c[0], c[1], 0, c[0], c[1], R)
        for s in (0.0, 0.25 * r0, 0.5 * r0, r0, 1.6 * r0, 2.5 * r0, 4.0 * r0, 0.55, 0.75, 1.0):
            if s > 1.0:
                continue
            v = 1.0 / (1.0 + (s / r0) ** 2) * (1.0 - s) ** 1.6
            g.add_color_stop_rgba(s, col[0], col[1], col[2], clamp(0.62 * k * v))
        A.set_source(g)
        A.arc(c[0], c[1], R, 0, TAU)
        A.fill()
        if pool:
            _pool(A, (c[0], py), prx, pry, col, pool.get("intensity", 0.45) * k)
    if emit > 0:
        with f.emit(par) as G:
            draw.glow_disc(G, c, radius * 1.3, _hot(col, 0.35), clamp(0.75 * k * emit * (1.0 - 0.8 * tint)))
    if core > 0:
        with _main(f, par, cairo.OPERATOR_ADD) as C:
            draw.radial(C, c, 0, radius * core, [(0.0, _hot(col, 0.9), clamp(k)), (0.6, _hot(col, 0.6), clamp(0.8 * k)),
                                                (1.0, col, 0.0)])
            C.arc(c[0], c[1], radius * core, 0, TAU)
            C.fill()
    return glow


def _pool(ctx, c, rx, ry, col, I, angle=0.0):
    ctx.save()
    ctx.translate(c[0], c[1])
    ctx.rotate(math.radians(angle))
    ctx.scale(max(rx, 0.1), max(ry, 0.1))
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1.0)
    for o, v in ((0.0, 1.0), (0.3, 0.75), (0.6, 0.35), (0.85, 0.1), (1.0, 0.0)):
        g.add_color_stop_rgba(o, col[0], col[1], col[2], clamp(I * v))
    ctx.set_source(g)
    ctx.arc(0, 0, 1.0, 0, TAU)
    ctx.fill()
    ctx.restore()


def light_pool(f, c, rx, ry=None, color=None, intensity=0.5, angle=0.0, t=None, par=1.0, tint=None):
    """Soft elliptical pool of light on a surface (ground under a lamp, a spot on a wall).
    rx, ry: radii px (ry default 0.25 rx: a floor seen at a grazing angle)."""
    col = _rgb(color) if color is not None else _rgb(f.pal.light)
    ry = ry if ry is not None else rx * 0.25
    R = max(rx, ry)
    with light(f, par=par, blur=0, ds=_ds(f, 4), bbox=(c[0] - R, c[1] - R, c[0] + R, c[1] + R),
               tint=auto_tint(f, tint)) as A:
        _pool(A, c, rx, ry, col, intensity, angle)


# ============================================================================ 4. particles
def _bump(t, tk, dk):
    if t <= tk or t >= tk + dk:
        return 0.0
    return 0.5 * (1.0 - math.cos(TAU * (t - tk) / dk))


def _bump_int(t, tk, dk):
    if t <= tk:
        return 0.0
    if t >= tk + dk:
        return 0.5 * dk
    u = t - tk
    return 0.5 * u - dk / (4.0 * math.pi) * math.sin(TAU * u / dk)


def wind_at(t, wind=0.0, gust=0.0, seed=0, period=7.0):
    """Horizontal wind (closed form): returns (offset_px, velocity_px_s) at time t for a steady
    `wind` (px/s) plus gusts (raised-cosine bursts of up to ~1.5 * gust px/s, one every
    ~`period` s). offset is the exact integral of velocity since t = 0."""
    off, vel = wind * t, wind
    if gust:
        lo, hi = min(0.0, t), max(0.0, t)
        for k in range(int(math.floor(lo / period)) - 1, int(math.floor(hi / period)) + 2):
            tk = (k + 0.1 + 0.55 * hash01(seed, k, 1)) * period
            dk = period * (0.3 + 0.45 * hash01(seed, k, 2))
            sk = gust * (0.5 + hash01(seed, k, 3))
            off += sk * (_bump_int(t, tk, dk) - _bump_int(0.0, tk, dk))
            vel += sk * _bump(t, tk, dk)
    return off, vel


SNOW_BANDS = (   # far -> near: parallax, flakes per screen, radius, fall px/s, sway px, alpha, blur, wind factor
    dict(par=0.5, n=300, r=(0.7, 1.4), fall=(28.0, 50.0), sway=(5.0, 12.0), a=(0.30, 0.65), blur=0.0, wind=0.5),
    dict(par=1.0, n=130, r=(1.5, 2.8), fall=(60.0, 100.0), sway=(9.0, 22.0), a=(0.55, 0.95), blur=0.0, wind=1.0),
    dict(par=1.75, n=24, r=(5.0, 10.0), fall=(140.0, 230.0), sway=(18.0, 40.0), a=(0.45, 0.8), blur=7.0, wind=1.75),
)


def _arcs(ctx, xs, ys, rs, alphas, col, levels=4):
    """Fill circles grouped into a few alpha buckets (one cairo fill per bucket)."""
    if not len(xs):
        return
    lv = np.minimum((np.clip(alphas, 0, 1) * levels).astype(int), levels - 1)
    for L in range(levels):
        sel = np.flatnonzero(lv == L)
        if not sel.size:
            continue
        for x, y, r in zip(xs[sel].tolist(), ys[sel].tolist(), rs[sel].tolist()):
            ctx.new_sub_path()
            ctx.arc(x, y, r, 0, TAU)
        ctx.set_source_rgba(col[0], col[1], col[2], (L + 0.5) / levels)
        ctx.fill()


def snow(f, density=1.0, wind=25.0, gust=0.0, t=None, seed=0, color=None, size=1.0, speed=1.0,
         alpha=1.0, lit=None, lit_gain=1.2, lit_color=None, bands=None):
    """Falling snow in three depth bands (SNOW_BANDS: far small slow, near big fast blurred),
    with per-flake sway, a steady `wind` (px/s) and `gust` bursts. density scales the counts.
    lit: Light(s) - flakes inside them catch the light (additive tint). Returns flake count."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _pal(f, "snow", (0.95, 0.95, 0.94))
    litf, lcol = _litfn(lit, lit_color, f)
    woff, _ = wind_at(t, wind, gust, seed + 3)
    count = 0
    for bi, B in enumerate(bands or SNOW_BANDS):
        n = int(round(B["n"] * density))
        if n <= 0:
            continue
        par = B["par"]
        m = 2.5 * B["r"][1] * size + B["sway"][1] + 10
        tw, th = W + 2 * m, H + 2 * m
        R = _rand(seed * 31 + bi, n, 8)
        fall = lerp(B["fall"][0], B["fall"][1], R[2]) * speed
        A = lerp(B["sway"][0], B["sway"][1], R[3])
        om = 0.45 + 1.0 * R[4]
        ph = TAU * R[5]
        x = R[0] * tw + B["wind"] * woff + A * np.sin(om * t + ph)
        y = R[1] * th + fall * t + 0.25 * A * np.sin(1.7 * om * t + 2.0 * ph)
        x, y, idx = _wrap(f, par, x, y, tw, th, m)
        if not x.size:
            continue
        r = lerp(B["r"][0], B["r"][1], R[6][idx] ** 1.5) * size
        a = lerp(B["a"][0], B["a"][1], R[7][idx]) * alpha
        count += x.size
        if B.get("blur", 0) > 0:
            with f.layer(par=par, blur=B["blur"]) as L:
                _arcs(L, x, y, r, a, col)
        else:
            with _main(f, par) as C:
                _arcs(C, x, y, r, a, col)
        if litf is not None:
            Lv = litf(*_world1(f, par, x, y)) * lit_gain * a
            sel = np.flatnonzero(Lv > 0.03)
            if sel.size:
                if B.get("blur", 0) > 0:
                    with light(f, par=par, blur=B["blur"]) as Lc:
                        _arcs(Lc, x[sel], y[sel], r[sel] * 1.2, Lv[sel], lcol)
                else:
                    with _main(f, par, cairo.OPERATOR_ADD) as C:
                        _arcs(C, x[sel], y[sel], r[sel] * 1.25, Lv[sel], lcol)
    return count


RAIN_BANDS = (   # parallax, drops per screen, line width px, streak length factor, speed factor, alpha, blur
    dict(par=0.5, n=460, w=1.0, len=0.6, speed=0.55, a=0.13, blur=0.0),
    dict(par=1.0, n=240, w=1.0, len=1.0, speed=1.0, a=0.24, blur=0.0),
    dict(par=1.8, n=34, w=2.0, len=1.7, speed=1.7, a=0.20, blur=2.0),
)


def _bucket_lines(img, sx1, sy1, sx2, sy2, b, bl, col, lcol, thick, nb=5, nl=6):
    """cv2 AA line segments grouped by (brightness, lit) buckets: one polylines call per
    bucket, drawn with the bucket's mean brightness. b, bl: absolute additive brightness."""
    if not len(b):
        return
    bmax = float(b.max()) or 1.0
    qb = np.minimum((b / bmax * nb).astype(int), nb - 1)
    if bl is not None and float(bl.max()) > 0.01:
        lmax = float(bl.max())
        ql = np.minimum((bl / lmax * nl).astype(int), nl - 1)
    else:
        ql = np.zeros_like(qb)
        bl = None
    P = np.stack([np.stack([sx1, sy1], -1), np.stack([sx2, sy2], -1)], 1)
    P = np.rint(P * _SK).astype(np.int32)
    key = qb * nl + ql
    for k in np.unique(key):
        sel = np.flatnonzero(key == k)
        vb = float(b[sel].mean())
        vl = 0.0 if bl is None else float(bl[sel].mean())
        c = tuple(min(255.0, u + w) for u, w in zip(_cv(col, vb), _cv(lcol, vl)))
        cv2.polylines(img, list(P[sel]), False, c, thick, _AA, _SH)


def rain(f, density=1.0, speed=2300.0, angle=7.0, wind=0.0, gust=0.0, t=None, seed=0, color=None,
         alpha=1.0, shutter=0.022, lit=None, lit_gain=3.0, lit_color=None, bands=None):
    """Rain streaks in three depth bands (RAIN_BANDS). speed: fall px/s; angle: lean from
    vertical in degrees (+ = toward +x); wind/gust add a closed-form lateral drift and tilt the
    streaks. shutter: exposure (s) -> streak length. lit: Light(s) (lamp cones, windows) make
    the drops inside them glow in the light's color. Additive. Returns drop count."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _pal(f, "rain", (0.62, 0.66, 0.74))
    litf, lcol = _litfn(lit, lit_color, f)
    woff, wvel = wind_at(t, wind, gust, seed + 5)
    tan_a = math.tan(math.radians(angle))
    count = 0
    for bi, B in enumerate(bands or RAIN_BANDS):
        n = int(round(B["n"] * density))
        if n <= 0:
            continue
        par = B["par"]
        blur = B.get("blur", 0.0)
        ds = _ds(f, 2) if blur > 0 else 1
        vy0 = speed * B["speed"]
        Ls = shutter * B["len"]
        m = vy0 * Ls * 1.3 + 30.0
        tw, th = W + 2 * m, H + 2 * m
        R = _rand(seed * 17 + 101 + bi, n, 4)
        vy = vy0 * (0.85 + 0.3 * R[2])
        x = R[0] * tw + vy * tan_a * t + woff * B["speed"]
        y = R[1] * th + vy * t
        x, y, idx = _wrap(f, par, x, y, tw, th, m)
        if not x.size:
            continue
        count += x.size
        vyi = vy[idx]
        vxi = vyi * tan_a + wvel * B["speed"]
        x2, y2 = x - vxi * Ls, y - vyi * Ls
        b = alpha * B["a"] * (0.55 + 0.45 * R[3][idx])
        bl = None
        if litf is not None:
            bl = litf(*_world1(f, par, 0.5 * (x + x2), 0.5 * (y + y2))) * lit_gain * B["a"] * 2.2 * alpha
        box = (0, 0, f.pw, f.ph)
        img = _canvas(f, box, ds)
        cm = _canvas_matrix(f, par, box, ds)
        sx1, sy1 = _xf(cm, x, y)
        sx2, sy2 = _xf(cm, x2, y2)
        thick = max(1, int(round(B["w"] * f.scale * f.lcam(par).zoom / ds)))
        _bucket_lines(img, sx1, sy1, sx2, sy2, b, bl, col, lcol or col, thick)
        _add(f, img, 0, 0, ds, blur * f.scale / ds)
    return count


def _cells(x0, x1, cell):
    return range(int(math.floor(x0 / cell)), int(math.floor(x1 / cell)) + 1)


def splashes(f, y, x0=None, x1=None, rate=40.0, depth=0.0, t=None, seed=0, color=None, alpha=0.9,
             size=1.0, lit=None, lit_gain=4.0, lit_color=None, par=1.0):
    """Rain splashes on a ground line at world y: a tiny impact flash, 2-4 crown droplets on
    ballistic arcs and a flat expanding ripple. rate: splashes per second per 1000 px of
    ground. depth > 0 spreads them over a band y..y+depth (a street seen from above; lower =
    nearer = bigger). x0/x1 limit the ground (default: the whole view). Additive."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _pal(f, "rain", (0.62, 0.66, 0.74))
    litf, lcol = _litfn(lit, lit_color, f)
    vx0, vy0, vx1, vy1 = f.lcam(par).view_rect(40)
    xa = vx0 if x0 is None else max(vx0, x0)
    xb = vx1 if x1 is None else min(vx1, x1)
    if xb <= xa or y - 80 > vy1 or y + depth + 20 < vy0:
        return 0
    cell = 250.0
    dur = 0.26
    per = 0.5 + 0.9 * 0.5
    slots = max(1, int(round(rate * cell / 1000.0 * per)))
    cs = np.array(list(_cells(xa, xb, cell)))
    C = np.repeat(cs, slots)
    J = np.tile(np.arange(slots), cs.size)
    P = 0.5 + 0.9 * _vhash(seed, C, J, 1)
    ph = P * _vhash(seed, C, J, 2)
    cyc = np.floor((t + ph) / P)
    tau = (t + ph) - cyc * P
    on = tau < dur
    C, J, tau, cyc = C[on], J[on], tau[on], cyc[on]
    if not C.size:
        return 0
    sx = (C + _vhash(seed, C, J, cyc, 3)) * cell
    hz = _vhash(seed, C, J, cyc, 4)
    keep = (sx >= xa) & (sx <= xb)
    if x0 is not None:
        keep &= sx >= x0
    if x1 is not None:
        keep &= sx <= x1
    sx, hz, tau, C, J, cyc = sx[keep], hz[keep], tau[keep], C[keep], J[keep], cyc[keep]
    if not sx.size:
        return 0
    sy = y + depth * hz
    sc = size * (1.0 + 0.9 * hz * (depth > 0))
    u = tau / dur
    fade = (1.0 - u) ** 1.5
    lv = np.zeros_like(sx) if litf is None else litf(*_world1(f, par, sx, sy)) * lit_gain
    bb = (xa, y - 60 * size * 2, xb, y + depth + 20)
    box = _pxbox(f, par, bb, pad=6)
    if box is None:
        return 0
    img = _canvas(f, box, 1)
    cm = _canvas_matrix(f, par, box, 1)
    z = _zoom(f, par)
    for i in range(sx.size):
        b = alpha * fade[i]
        c = _cv(col, b) if lv[i] < 0.02 else tuple(min(255.0, v1 + v2) for v1, v2 in zip(_cv(col, b), _cv(lcol, b * lv[i])))
        X, Y = _xf(cm, sx[i], sy[i])
        k = sc[i] * z
        ta = tau[i]
        if ta < 0.04:      # impact flash: the drop's last streak
            cv2.line(img, (int(X * _SK), int((Y - 18 * k) * _SK)), (int(X * _SK), int(Y * _SK)), c, max(1, int(k)), _AA, _SH)
        # ripple ring (flat ellipse) + a short bright crown sheet in the first instants
        rx = (3.0 + 75.0 * ta) * k
        cv2.ellipse(img, (int(X * _SK), int(Y * _SK)), (int(rx * _SK), max(1, int(rx * 0.22 * _SK))), 0, 0, 360,
                    tuple(v * 0.6 for v in c), 1, _AA, _SH)
        if ta < 0.09:
            cw, chh = (2.5 + 40.0 * ta) * k, (2.0 + 70.0 * ta) * k * (1.0 - ta / 0.09)
            cv2.ellipse(img, (int(X * _SK), int((Y - 0.5 * chh) * _SK)), (int(cw * _SK), max(1, int(0.5 * chh * _SK))),
                        0, 180, 360, tuple(v * 0.8 for v in c), 1, _AA, _SH)
        # crown droplets
        nd = 2 + int(_vhash(seed, C[i], J[i], cyc[i], 5) * 3)
        for d in range(nd):
            hv = _vhash(seed, C[i], J[i], cyc[i], 10 + d)
            vx = (hv - 0.5) * 2 * (60 + 110 * hv)
            vy = 160 + 200 * _vhash(seed, C[i], J[i], cyc[i], 20 + d)
            dy = -vy * ta + 0.5 * G_PX * ta * ta
            if dy > 0:
                continue
            DX, DY = vx * ta * k, dy * k
            cv2.circle(img, (int((X + DX) * _SK), int((Y + DY) * _SK)), max(1, int(1.1 * k * _SK)), c, -1, _AA, _SH)
    _add(f, img, box[0], box[1], 1)
    return int(sx.size)


def drips(f, ledge, count=8, period=(1.2, 2.8), ground=None, t=None, seed=0, color=None, alpha=0.8,
          size=1.0, lit=None, lit_gain=3.0, lit_color=None, par=1.0):
    """Water dripping from a ledge polyline [(x, y), ...]: each drip swells, lets go, falls with
    gravity (a short streak) and, if `ground` (world y) is given, splashes there. Additive."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _pal(f, "rain", (0.62, 0.66, 0.74))
    litf, lcol = _litfn(lit, lit_color, f)
    pts = np.asarray(ledge, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = cum[-1] or 1.0
    vx0, vy0, vx1, vy1 = f.lcam(par).view_rect(30)
    gy = ground if ground is not None else vy1 + 50
    box = _pxbox(f, par, (pts[:, 0].min() - 30, pts[:, 1].min() - 30, pts[:, 0].max() + 30, gy + 10), pad=4)
    if box is None:
        return
    img = _canvas(f, box, 1)
    cm = _canvas_matrix(f, par, box, 1)
    z = _zoom(f, par)
    for j in range(count):
        s = (j + 0.2 + 0.6 * hash01(seed, j, 1)) / count * total
        i = int(np.clip(np.searchsorted(cum, s) - 1, 0, len(seg) - 1))
        u = (s - cum[i]) / (seg[i] or 1.0)
        px, py = pts[i] + (pts[i + 1] - pts[i]) * u
        P = lerp(period[0], period[1], hash01(seed, j, 2))
        tau = (t + P * hash01(seed, j, 3)) % P
        grow = 0.62 * P
        r0 = (1.6 + 1.2 * hash01(seed, j, 4)) * size
        Lv = 0.0 if litf is None else float(litf(*_world1(f, par, px, py + 10))) * lit_gain
        def C(b):
            return tuple(min(255.0, a + c) for a, c in zip(_cv(col, b), _cv(lcol or col, b * Lv)))
        if tau < grow:
            r = r0 * (tau / grow) ** 0.6
            X, Y = _xf(cm, px, py + r * 0.9)
            cv2.ellipse(img, (int(X * _SK), int(Y * _SK)), (max(1, int(r * z * 0.8 * _SK)), max(1, int(r * z * 1.05 * _SK))),
                        0, 0, 360, C(alpha * 0.85), -1, _AA, _SH)
        else:
            tf = tau - grow
            yy = py + r0 + 0.5 * G_PX * tf * tf
            v = G_PX * tf
            if yy < gy:
                X, Y = _xf(cm, px, yy)
                L = max(2.0 * r0, v * 0.022) * z
                cv2.line(img, (int(X * _SK), int((Y - L) * _SK)), (int(X * _SK), int(Y * _SK)), C(alpha), max(1, int(r0 * z * 0.9)), _AA, _SH)
            elif ground is not None:
                tg = math.sqrt(max(0.0, 2.0 * (gy - py - r0) / G_PX))
                ta = tf - tg
                if ta < 0.25:
                    X, Y = _xf(cm, px, gy)
                    rx = (3.0 + 60.0 * ta) * z * size
                    cv2.ellipse(img, (int(X * _SK), int(Y * _SK)), (int(rx * _SK), max(1, int(rx * 0.22 * _SK))), 0, 0, 360,
                                C(alpha * 0.6 * (1 - ta / 0.25)), 1, _AA, _SH)
                    for d in (-1, 1):
                        dx = d * (50 + 40 * hash01(seed, j, d + 9)) * ta
                        dy = -230 * ta + 0.5 * G_PX * ta * ta
                        if dy < 0:
                            X2, Y2 = _xf(cm, px + dx, gy + dy)
                            cv2.circle(img, (int(X2 * _SK), int(Y2 * _SK)), max(1, int(0.9 * z * _SK)), C(alpha * (1 - ta / 0.25)), -1, _AA, _SH)
    _add(f, img, box[0], box[1], 1)


# ---------------------------------------------------------------------------- bubbles
def _bubble_draw(f, par, xs, ys, rs, bs, wob, col, lit=None, lit_gain=2.0, lcol=None):
    """Render bubbles (world xs, ys, radius rs, brightness bs): pale rim, faint body, highlight."""
    if not len(xs):
        return
    pad = float(np.max(rs)) * 2 + 6
    bb = (float(np.min(xs)) - pad, float(np.min(ys)) - pad, float(np.max(xs)) + pad, float(np.max(ys)) + pad)
    box = _pxbox(f, par, bb, pad=4)
    if box is None:
        return
    if lit is not None:
        bs = bs * (1.0 + lit_gain * lit(*_world1(f, par, xs, ys)))
    img = _canvas(f, box, 1)
    cm = _canvas_matrix(f, par, box, 1)
    z = _zoom(f, par)
    X, Y = _xf(cm, xs, ys)
    for i in range(len(xs)):
        r = rs[i] * z
        b = float(bs[i])
        cx, cy = int(X[i] * _SK), int(Y[i] * _SK)
        if r < 2.2:
            cv2.circle(img, (cx, cy), max(1, int(max(r, 0.6) * _SK)), _cv(col, b * 0.9), -1, _AA, _SH)
            continue
        e = wob[i]
        ax = (r * (1.0 + 0.10 * e), r * (1.0 - 0.13 * e)) if r > 5 else (r, r)
        axes = (int(ax[0] * _SK), int(ax[1] * _SK))
        cv2.ellipse(img, (cx, cy), axes, 0, 0, 360, _cv(col, b * 0.16), -1, _AA, _SH)
        cv2.ellipse(img, (cx, cy), axes, 0, 0, 360, _cv(col, b * 0.62), 1 if r < 9 else 2, _AA, _SH)
        hx, hy = cx - int(0.38 * ax[0] * _SK), cy - int(0.42 * ax[1] * _SK)
        cv2.circle(img, (hx, hy), max(1, int(0.24 * r * _SK)), _cv(col, b * 0.95), -1, _AA, _SH)
    _add(f, img, box[0], box[1], 1)


def _rise(tau, v, r0, growth):
    acc = 0.18 * v
    d = v * tau + 0.5 * acc * tau * tau
    return d, r0 * (1.0 + growth * d / 1000.0)


def _rise_time(D, v):
    acc = 0.18 * v
    return (-v + np.sqrt(v * v + 2 * acc * D)) / acc


def bubbles(f, src, rate=6.0, t=None, seed=0, rise=(150.0, 250.0), size=(1.5, 6.0), growth=0.6,
            wobble=1.0, spread=10.0, current=0.0, surface=None, height=1500.0, color=None, alpha=1.0,
            lit=None, lit_gain=2.0, lit_color=None, t_start=None, t_end=None, par=1.0):
    """A rising stream of bubbles from src (x, y): `rate` per second, rising `rise` px/s
    (bigger ones faster, accelerating), wobbling, growing as they rise (growth per 1000 px),
    drifting with `current` px/s, and bursting at world y `surface` (or fading after `height`
    px). t_start/t_end limit emission. Additive pale bubbles. Returns the count drawn."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _mix(_pal(f, "surface", WHITE), WHITE, 0.55)
    litf, _ = _litfn(lit, lit_color, f)
    D = height if surface is None else max(1.0, min(height, src[1] - surface))
    vmin = rise[0] * 0.7
    life = float(_rise_time(D, vmin)) + 0.15
    k0 = int(math.floor((t - life) * rate)) - 1
    k1 = int(math.floor(t * rate)) + 1
    k = np.arange(k0, k1 + 1)
    tk = (k + 0.85 * _vhash(seed, k, 1)) / rate
    tau = t - tk
    ok = tau >= 0
    if t_start is not None:
        ok &= tk >= t_start
    if t_end is not None:
        ok &= tk <= t_end
    k, tau = k[ok], tau[ok]
    if not k.size:
        return 0
    h2 = _vhash(seed, k, 2)
    r0 = lerp(size[0], size[1], h2 * h2)
    v = lerp(rise[0], rise[1], _vhash(seed, k, 3)) * (0.75 + 0.45 * np.minimum(r0 / max(size[1], 1e-3), 1.2))
    return _bubble_set(f, par, src, tau, r0, v, k, seed, growth, wobble, spread, current, surface, D, col, alpha,
                       litf, lit_gain)


def _bubble_set(f, par, src, tau, r0, v, k, seed, growth, wobble, spread, current, surface, D, col, alpha,
                litf, lit_gain, kick=None):
    d, r = _rise(tau, v, r0, growth)
    tD = _rise_time(D, v)
    pop = 0.12
    alive = tau < tD + (pop if surface is not None else 0.0)
    if not alive.any():
        return 0
    d, r, tau, r0, v, k, tD = d[alive], r[alive], tau[alive], r0[alive], v[alive], k[alive], tD[alive]
    if kick is not None:
        kick = (kick[0][alive], kick[1][alive])
    side = (_vhash(seed, k, 4) - 0.5) * 2.0
    om = 9.0 - 0.45 * np.minimum(r, 12.0)
    phw = TAU * _vhash(seed, k, 5)
    x = src[0] + side * spread * (1.0 - np.exp(-tau / 0.5)) + current * tau
    x = x + wobble * (0.4 + 0.28 * r) * np.sin(om * tau + phw)
    y = src[1] - np.minimum(d, D)
    if kick is not None:
        kx, ky = kick
        x = x + kx * (1.0 - np.exp(-tau / 0.28)) * 0.28
        y = y - ky * (1.0 - np.exp(-tau / 0.3)) * 0.3
    b = alpha * _ss(0.0, 0.06, tau)
    wob = np.sin(1.3 * om * tau + 2 * phw)
    if surface is not None:
        burst = tau > tD
        age = np.clip((tau - tD) / pop, 0, 1)
        r = np.where(burst, r * (1.0 + 1.6 * age), r)
        b = np.where(burst, b * (1.0 - age) * 0.9, b)
    else:
        b = b * (1.0 - _ss(0.75 * tD, tD, tau))
    _bubble_draw(f, par, x, y, r, b, wob, col, litf, lit_gain)
    return int(x.size)


def exhale(f, src, t0, n=24, t=None, seed=0, size=(1.5, 11.0), rise=(170.0, 260.0), spread=60.0,
           growth=0.7, wobble=1.2, current=0.0, surface=None, height=1500.0, color=None, alpha=1.0,
           lit=None, lit_gain=2.0, lit_color=None, par=1.0):
    """A diver's exhale at time t0: a burst of n bubbles (a few big wobbly ones) kicked out of
    src, then rising as in bubbles(). Returns the count drawn."""
    t = _now(f, t)
    if t < t0:
        return 0
    col = _rgb(color) if color is not None else _mix(_pal(f, "surface", WHITE), WHITE, 0.55)
    litf, _ = _litfn(lit, lit_color, f)
    D = height if surface is None else max(1.0, min(height, src[1] - surface))
    k = np.arange(n)
    tk = t0 + 0.38 * _vhash(seed, k, 11) ** 1.4
    tau = t - tk
    ok = tau >= 0
    k, tau = k[ok], tau[ok]
    if not k.size:
        return 0
    hs = _vhash(seed, k, 12)
    r0 = lerp(size[0], size[1], hs ** 2.2)
    v = lerp(rise[0], rise[1], _vhash(seed, k, 13)) * (0.8 + 0.35 * np.minimum(r0 / max(size[1], 1e-3), 1.0))
    kx = (_vhash(seed, k, 14) - 0.5) * 2.0 * 260.0
    ky = 150.0 + 200.0 * _vhash(seed, k, 15)
    return _bubble_set(f, par, src, tau, r0, v, k + 1000 * (seed % 97), seed, growth, wobble, spread * 0.3, current,
                       surface, D, col, alpha, litf, lit_gain, kick=(kx, ky))


def breathing(f, src, period=4.0, phase=0.0, n=20, t=None, seed=0, **kw):
    """A diver breathing: an exhale() every `period` s (first at `phase`), each with its own
    seed. Extra keywords go to exhale(). Returns the count drawn."""
    t = _now(f, t)
    life = 8.0
    total = 0
    for c in range(int(math.floor((t - life - phase) / period)), int(math.floor((t - phase) / period)) + 1):
        t0 = phase + c * period + 0.25 * period * (hash01(seed, c) - 0.5)
        if t0 <= t:
            total += exhale(f, src, t0, n=int(n * (0.75 + 0.5 * hash01(seed, c, 2))), t=t, seed=seed * 7919 + c, **kw)
    return total


# ---------------------------------------------------------------------------- floating specks
MARINE_BANDS = (
    dict(par=0.45, n=340, r=(0.5, 0.9), a=(0.10, 0.24), speed=0.5, blur=0.0),
    dict(par=1.0, n=170, r=(0.8, 1.6), a=(0.16, 0.36), speed=1.0, blur=0.0),
    dict(par=1.7, n=16, r=(3.0, 6.5), a=(0.05, 0.12), speed=1.7, blur=4.0),
)


def _specks(f, bands, seed, t, col, alpha, litf, lcol, lit_gain, motion, size=1.0):
    count = 0
    for bi, B in enumerate(bands):
        n = int(round(B["n"]))
        if n <= 0:
            continue
        par = B["par"]
        blur = B.get("blur", 0.0)
        ds = _ds(f, 2) if blur > 0 else 1
        m = 20.0 + B["r"][1] * 3
        tw, th = W + 2 * m, H + 2 * m
        R = _rand(seed * 13 + 7 + bi, n, 9)
        x, y = motion(R, t, B)
        x, y, idx = _wrap(f, par, R[0] * tw + x, R[1] * th + y, tw, th, m)
        if not x.size:
            continue
        count += x.size
        r = lerp(B["r"][0], B["r"][1], R[6][idx] ** 2) * size
        a = lerp(B["a"][0], B["a"][1], R[7][idx]) * alpha
        tw_ = 0.65 + 0.35 * np.sin(t * (1.5 + 3.0 * R[8][idx]) + TAU * R[5][idx])
        a = a * tw_
        Lv = None
        if litf is not None:
            Lv = litf(*_world1(f, par, x, y)) * lit_gain
        box = (0, 0, f.pw, f.ph)
        img = _canvas(f, box, ds)
        cm = _canvas_matrix(f, par, box, ds)
        X, Y = _xf(cm, x, y)
        z = _zoom(f, par) / ds
        for i in range(x.size):
            b = float(a[i])
            c = _cv(col, b)
            if Lv is not None and Lv[i] > 0.01:
                c = tuple(min(255.0, u + w) for u, w in zip(c, _cv(lcol, float(Lv[i]) * (0.25 + b))))
            if max(c) < 2.0:
                continue
            rr = r[i] * z
            if rr < 0.75:
                k = (rr / 0.75) ** 2
                c = tuple(v * k for v in c)
                rr = 0.75
            cv2.circle(img, (int(X[i] * _SK), int(Y[i] * _SK)), int(rr * _SK), c, -1, _AA, _SH)
        _add(f, img, 0, 0, ds, blur * f.scale / ds)
    return count


def marine_snow(f, density=1.0, t=None, seed=0, color=None, alpha=1.0, sink=10.0, current=(5.0, 0.0),
                size=1.0, lit=None, lit_gain=3.5, lit_color=None, bands=None):
    """Marine snow: slow drifting organic specks in three depth bands (near ones big, soft
    and faster). Sinks `sink` px/s, drifts with `current` (px/s). Faint on its own; inside a
    lamp beam (lit=cone) the specks blaze. Additive. Returns the count drawn."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _mix(_pal(f, "surface", _skylight(f)), WHITE, 0.3)
    litf, lcol = _litfn(lit, lit_color, f)
    bands = [dict(B, n=B["n"] * density) for B in (bands or MARINE_BANDS)]

    def motion(R, t, B):
        s = B["speed"]
        A = 6.0 + 14.0 * R[2]
        om = 0.2 + 0.5 * R[3]
        x = current[0] * s * t + A * np.sin(om * t + TAU * R[4])
        y = (sink * (0.6 + 0.8 * R[3]) + current[1]) * s * t + 0.6 * A * np.sin(0.7 * om * t + TAU * R[5])
        return x, y
    return _specks(f, bands, seed, t, col, alpha, litf, lcol, lit_gain, motion, size)


def dust(f, region, density=1.0, t=None, seed=0, color=None, alpha=1.0, size=1.0, drift=1.0,
         ambient=0.0, bokeh=0.06, par=1.0):
    """Dust motes that only show where `region` (a Light: Cone / Glow / Shaft, or a list) is
    lit - floating, slowly turning (they twinkle). density ~ motes per 10,000 px^2 * 1.6;
    ambient adds a base visibility everywhere in the region's bbox. A few big out-of-focus
    bokeh motes (fraction `bokeh`). Additive."""
    t = _now(f, t)
    if isinstance(region, (list, tuple)):
        region = lit_sum(*region)
    col = _rgb(color) if color is not None else _rgb(getattr(region, "color", f.pal.light))
    bb = region.bbox()
    tile = 512.0
    nt = int(round(42 * density))
    if nt <= 0:
        return 0
    R = _rand(seed * 7 + 3, nt, 10)
    A = (5.0 + 12.0 * R[2]) * drift
    om = 0.15 + 0.35 * R[3]
    x = R[0] * tile + A * np.sin(om * t + TAU * R[4]) + 3.0 * drift * t * (R[5] - 0.5)
    y = R[1] * tile + 0.7 * A * np.sin(0.8 * om * t + TAU * R[6]) + 2.5 * drift * t
    x0 = bb[0] + np.mod(x - bb[0], tile)
    y0 = bb[1] + np.mod(y - bb[1], tile)
    XS, YS, IS = [], [], []
    for i in range(max(1, int(math.ceil((bb[2] - bb[0]) / tile)))):
        for j in range(max(1, int(math.ceil((bb[3] - bb[1]) / tile)))):
            xx, yy = x0 + i * tile, y0 + j * tile
            keep = (xx <= bb[2]) & (yy <= bb[3])
            XS.append(xx[keep])
            YS.append(yy[keep])
            IS.append(np.flatnonzero(keep))
    x, y, idx = np.concatenate(XS), np.concatenate(YS), np.concatenate(IS)
    L = region.lit(*_world1(f, par, x, y)) + ambient
    tw = 0.35 + 0.65 * np.sin(t * (0.8 + 2.2 * R[7][idx]) + TAU * R[8][idx]) ** 2
    b = L * tw * alpha * (0.6 + 0.8 * R[9][idx])
    sel = b > 0.015
    if not sel.any():
        return 0
    x, y, b, idx = x[sel], y[sel], b[sel], idx[sel]
    big = R[9][idx] < bokeh
    r = (0.7 + 1.1 * R[2][idx]) * size
    box = _pxbox(f, par, (x.min() - 12, y.min() - 12, x.max() + 12, y.max() + 12), pad=4)
    if box is None:
        return 0
    img = _canvas(f, box, 1)
    cm = _canvas_matrix(f, par, box, 1)
    X, Y = _xf(cm, x, y)
    z = _zoom(f, par)
    for i in range(x.size):
        if big[i]:
            continue
        rr = r[i] * z
        c = _cv(col, float(min(b[i], 1.5)))
        if rr < 0.75:
            c = tuple(v * (rr / 0.75) ** 2 for v in c)
            rr = 0.75
        cv2.circle(img, (int(X[i] * _SK), int(Y[i] * _SK)), int(rr * _SK), c, -1, _AA, _SH)
    _add(f, img, box[0], box[1], 1)
    if big.any():
        with _main(f, par, cairo.OPERATOR_ADD) as C:
            for i in np.flatnonzero(big):
                rr = (5.0 + 6.0 * R[3][idx[i]]) * size
                draw.radial(C, (x[i], y[i]), 0, rr, [(0, col, clamp(0.22 * b[i])), (0.7, col, clamp(0.12 * b[i])), (1, col, 0.0)])
                C.arc(x[i], y[i], rr, 0, TAU)
                C.fill()
    return int(x.size)


# ---------------------------------------------------------------------------- embers
def _src_sampler(src):
    """src -> sampler(u array) -> (x, y). Point, segment ((x0,y0),(x1,y1)) or polyline."""
    if callable(src):
        return src
    if not isinstance(src[0], (tuple, list, np.ndarray)):
        p = (float(src[0]), float(src[1]))
        return lambda tk, u: (np.full(u.shape, p[0]), np.full(u.shape, p[1]), np.ones(u.shape, bool))
    pts = np.asarray(src, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0.0], np.cumsum(seg)])

    def samp(tk, u):
        s = u * cum[-1]
        i = np.clip(np.searchsorted(cum, s) - 1, 0, len(seg) - 1)
        w = (s - cum[i]) / np.maximum(seg[i], 1e-6)
        p = pts[i] + (pts[i + 1] - pts[i]) * w[:, None]
        return p[:, 0], p[:, 1], np.ones(u.shape, bool)
    return samp


def embers(f, src, rate=24.0, life=(1.0, 2.4), rise=(90.0, 200.0), spread=35.0, wind=15.0, gust=0.0,
           turbulence=1.0, size=(1.0, 2.4), color=None, intensity=1.0, t=None, seed=0, par=1.0,
           t_start=None, t_end=None, glow=0.7):
    """Embers / sparks rising from a fire. src: point, segment, polyline, or a callable
    (tk_array, u_array) -> (x, y, valid) giving the birthplace of an ember born at tk. Each
    lives `life` s, rises with decaying buoyancy, swirls (turbulence), drifts with
    wind/gust, cools from white-hot to dim amber and twinkles. Drawn as short motion streaks
    (+ emissive glow for the hot ones). Returns the count drawn."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _rgb(f.pal.light)
    samp = _src_sampler(src)
    lmax = life[1]
    k = np.arange(int(math.floor((t - lmax) * rate)) - 1, int(math.floor(t * rate)) + 2)
    tk = (k + 0.85 * _vhash(seed, k, 1)) / rate
    tau = t - tk
    L = lerp(life[0], life[1], _vhash(seed, k, 2))
    ok = (tau >= 0) & (tau < L)
    if t_start is not None:
        ok &= tk >= t_start
    if t_end is not None:
        ok &= tk <= t_end
    k, tk, tau, L = k[ok], tk[ok], tau[ok], L[ok]
    if not k.size:
        return 0
    sx, sy, valid = samp(tk, _vhash(seed, k, 3))
    k, tk, tau, L, sx, sy = k[valid], tk[valid], tau[valid], L[valid], sx[valid], sy[valid]
    if not k.size:
        return 0
    v0 = lerp(rise[0], rise[1], _vhash(seed, k, 4))
    Td = 0.7
    up = v0 * Td * (1.0 - np.exp(-tau / Td)) + 22.0 * tau
    vup = v0 * np.exp(-tau / Td) + 22.0
    A = (6.0 + 16.0 * _vhash(seed, k, 5)) * turbulence
    om = 2.0 + 3.5 * _vhash(seed, k, 6)
    ph = TAU * _vhash(seed, k, 7)
    side = (_vhash(seed, k, 8) - 0.5) * 2.0 * spread
    ramp = np.minimum(tau, 1.0)
    woff_t, wv = wind_at(t, wind, gust, seed + 1)
    wo = np.array([wind_at(float(a), wind, gust, seed + 1)[0] for a in tk]) if gust else wind * tk
    x = sx + side * (1.0 - np.exp(-tau / 0.6)) + (woff_t - wo) + A * np.sin(om * tau + ph) * ramp
    y = sy - up
    vx = side / 0.6 * np.exp(-tau / 0.6) + wv + A * om * np.cos(om * tau + ph) * ramp
    vy = -vup
    u = tau / L
    tw = 0.6 + 0.4 * np.sin(tau * (10.0 + 14.0 * _vhash(seed, k, 9)) + ph)
    b = intensity * _ss(0.0, 0.06, tau) * (1.0 - u) ** 1.3 * tw
    r = lerp(size[0], size[1], _vhash(seed, k, 10) ** 2) * (1.0 - 0.45 * u)
    pad = 20.0
    box = _pxbox(f, par, (x.min() - pad, y.min() - pad, x.max() + pad, y.max() + pad), pad=4)
    if box is None:
        return 0
    img = _canvas(f, box, 1)
    cm = _canvas_matrix(f, par, box, 1)
    z = _zoom(f, par)
    X, Y = _xf(cm, x, y)
    X2, Y2 = _xf(cm, x - vx / 40.0, y - vy / 40.0)
    hot = _hot(col, 0.85)
    for i in range(k.size):
        c = _mix(hot, col, min(1.0, float(u[i]) * 1.8))
        cc = _cv(c, float(min(b[i], 1.0)) * 1.1)
        th = max(1, int(round(r[i] * z)))
        cv2.line(img, (int(X2[i] * _SK), int(Y2[i] * _SK)), (int(X[i] * _SK), int(Y[i] * _SK)), cc, th, _AA, _SH)
    _add(f, img, box[0], box[1], 1)
    if glow > 0:
        sel = np.flatnonzero(b > 0.35)
        if sel.size:
            with f.emit(par) as G:
                for i in sel:
                    draw.glow_disc(G, (x[i], y[i]), 9.0 + 5.0 * r[i], col, clamp(glow * 0.6 * b[i]))
    return int(k.size)


# ============================================================================ 5. water
def wave_y(x, t, y0=0.0, amp=10.0, wavelength=520.0, speed=1.0, chop=0.5, seed=0):
    """Water surface height (world y, down) at x (float or array) and time t: four Stokes-ish
    wave trains with deep-water dispersion (long waves move faster) and sharpened crests.
    amp px, wavelength px of the main train, speed scales time."""
    x = np.asarray(x, float)
    y = np.zeros_like(x)
    for k, (lf, af) in enumerate(((1.0, 1.0), (0.57, 0.48), (0.31, 0.24), (0.17, 0.11))):
        lam = wavelength * lf * (0.9 + 0.2 * hash01(seed, k))
        kk = TAU / lam
        om = math.sqrt(G_PX * kk) * speed * 0.55
        ph = TAU * hash01(seed, k, 7)
        dirn = 1.0 if hash01(seed, k, 3) > 0.3 else -1.0
        th = kk * x - dirn * om * t + ph
        a = amp * af
        y -= a * np.cos(th) + chop * 0.5 * kk * a * a * np.cos(2.0 * th)
    return y0 + y


def _wave_kw(kw):
    return {k: kw[k] for k in ("amp", "wavelength", "speed", "chop", "seed") if k in kw}


def water_path(ctx, t, y0, x0, x1, side="below", far=6000.0, step=8.0, **wave):
    """Cairo path of the water body (side='below') or the air (side='above') bounded by the
    wave line from x0 to x1 (world). Fill it yourself (e.g. a hull clip or a tint)."""
    n = max(2, int((x1 - x0) / step) + 1)
    xs = np.linspace(x0, x1, n)
    ys = wave_y(xs, t, y0, **_wave_kw(wave))
    ctx.move_to(xs[0], ys[0])
    for x, y in zip(xs[1:].tolist(), ys[1:].tolist()):
        ctx.line_to(x, y)
    yy = y0 + far if side == "below" else y0 - far
    ctx.line_to(x1, yy)
    ctx.line_to(x0, yy)
    ctx.close_path()


def water_split(f, y0, t=None, color=None, deep=None, alpha=0.7, depth=900.0, band=1.0, par=1.0, **wave):
    """Underwater half of a split (above/below) shot: tints everything already drawn below the
    wave line (hull, far silhouettes) from `color` (alpha at the surface) to `deep` (fully
    opaque `depth` px down), and adds the bright rippled underside of the surface (band 0..1).
    Draw it after the far layers and before the action plane; then waterline() on top."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _pal(f, "mid", f.pal.fog_at(0.5))
    deep = _rgb(deep) if deep is not None else _pal(f, "deep", f.pal.ink)
    vx0, vy0, vx1, vy1 = f.lcam(par).view_rect(40)
    if y0 - 60 > vy1:
        return
    with _main(f, par) as C:
        water_path(C, t, y0, vx0, vx1, "below", far=max(depth * 3, vy1 - y0 + 100), **wave)
        g = cairo.LinearGradient(0, y0 - 20, 0, y0 + depth)
        g.add_color_stop_rgba(0.0, col[0], col[1], col[2], clamp(alpha))
        g.add_color_stop_rgba(0.45, lerp(col[0], deep[0], 0.6), lerp(col[1], deep[1], 0.6), lerp(col[2], deep[2], 0.6),
                              clamp(alpha + (1 - alpha) * 0.55))
        g.add_color_stop_rgba(1.0, deep[0], deep[1], deep[2], 1.0)
        C.set_source(g)
        C.fill()
    if band > 0:
        # the bright underside of the surface: a smooth falloff below the wave line (sharp at
        # the meniscus, long soft tail) broken by drifting ripple streaks and glints
        sky = _mix(_pal(f, "moon", _skylight(f)), col, 0.3)
        ds = _ds(f, 2)
        box = _pxbox(f, par, (vx0, y0 - 30, vx1, y0 + 320), pad=2, align=ds)
        if box is not None:
            wx, wy, gw, gh = _grid(f, par, box, ds)
            wl = wave_y(wx, t, y0, **_wave_kw(wave))
            dy = wy - wl
            d = np.maximum(dy, 0.0)
            on = _ss(-1.2, 0.8, dy)
            T = _tex(7700, 256, 10.0)
            rip = _sample(T, wx / 2.5 + 30.0 * t, d / 1.6 + 7.0 + 0.6 * t)
            I = on * ((0.5 * np.exp(-d / 7.0) + 0.2 * np.exp(-d / 28.0) + 0.07 * np.exp(-d / 90.0)) * (0.7 + 0.6 * rip)
                      + 0.35 * _ss(0.62, 0.85, rip) * np.exp(-d / 16.0))
            _add(f, _bgra(I * band, sky), box[0], box[1], ds, 0.6)


def waterline(f, y0, t=None, color=None, intensity=0.8, width=2.2, glitter=1.0, glitter_band=50.0,
              moon_x=None, moon_spread=200.0, par=1.0, seed=0, **wave):
    """The meniscus of a split shot: a bright wavy line with a soft glow, plus surface glitter
    (moonlight glints twinkling in a band above the line, densest under moon_x). Additive.
    Wave keywords (amp, wavelength, speed, chop, seed) must match water_split()."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _hot(_pal(f, "moon", _skylight(f)), 0.3)
    vx0, vy0, vx1, vy1 = f.lcam(par).view_rect(30)
    if y0 + 40 < vy0 or y0 - glitter_band - 40 > vy1:
        return
    n = max(2, int((vx1 - vx0) / 5.0) + 1)
    xs = np.linspace(vx0, vx1, n)
    ys = wave_y(xs, t, y0, **_wave_kw(wave))
    with light(f, par=par, blur=7.0, bbox=(vx0, y0 - 60, vx1, y0 + 60)) as A:
        draw.poly(A, list(zip(xs.tolist(), ys.tolist())), close=False)
        A.set_source_rgba(col[0], col[1], col[2], clamp(0.35 * intensity))
        A.set_line_width(width * 5)
        A.stroke()
    with _main(f, par, cairo.OPERATOR_ADD) as C:
        draw.poly(C, list(zip(xs.tolist(), ys.tolist())), close=False)
        C.set_source_rgba(col[0], col[1], col[2], clamp(0.8 * intensity))
        C.set_line_width(width)
        C.stroke()
    if glitter <= 0:
        return
    cell = 26.0
    cs = np.arange(int(math.floor(vx0 / cell)), int(math.floor(vx1 / cell)) + 1)
    C_ = np.repeat(cs, 2)
    J = np.tile(np.arange(2), cs.size)
    P = 0.3 + 0.6 * _vhash(seed, C_, J, 1)
    cyc = np.floor((t + P * _vhash(seed, C_, J, 2)) / P)
    tau = (t + P * _vhash(seed, C_, J, 2)) - cyc * P
    gx = (C_ + _vhash(seed, C_, J, cyc, 3)) * cell
    dens = 0.18 if moon_x is None else 0.12 + 0.88 * np.exp(-((gx - moon_x) / moon_spread) ** 2)
    on = _vhash(seed, C_, J, cyc, 4) < dens * glitter
    life = 0.6 * P
    on &= tau < life
    if not on.any():
        return
    gx, tau, life, C_, J, cyc = gx[on], tau[on], life[on], C_[on], J[on], cyc[on]
    hy = _vhash(seed, C_, J, cyc, 5)
    gy = wave_y(gx, t, y0, **_wave_kw(wave)) - 3.0 - glitter_band * hy * hy
    env = np.sin(np.pi * tau / life) ** 2
    ln = (3.0 + 10.0 * _vhash(seed, C_, J, cyc, 6)) * (1.0 - 0.6 * hy)
    box = _pxbox(f, par, (vx0, y0 - glitter_band - 30, vx1, y0 + 30), pad=4)
    if box is None:
        return
    img = _canvas(f, box, 1)
    cm = _canvas_matrix(f, par, box, 1)
    z = _zoom(f, par)
    X, Y = _xf(cm, gx, gy)
    for i in range(gx.size):
        c = _cv(_hot(col, 0.5), float(env[i]) * intensity * 1.1)
        L = ln[i] * z * 0.5
        cv2.line(img, (int((X[i] - L) * _SK), int(Y[i] * _SK)), (int((X[i] + L) * _SK), int(Y[i] * _SK)), c, 1, _AA, _SH)
    _add(f, img, box[0], box[1], 1)
    sel = np.flatnonzero(env > 0.8)
    if sel.size:
        with f.emit(par) as G:
            for i in sel[:40]:
                draw.glow_disc(G, (gx[i], gy[i]), 10.0, col, 0.35 * intensity)


def wet_reflection(f, x, ground_y, length=320.0, width=40.0, color=None, intensity=0.5, x_src=None,
                   t=None, seed=0, par=1.0, ripple=1.0):
    """Reflection of a light on a wet street / puddle: a vertical streak hanging below the
    ground line at world x (length px down, `width` px wide, widening with distance), broken
    into shimmering horizontal ripples. Additive."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _rgb(f.pal.light)
    ds = _ds(f, 2)
    box = _pxbox(f, par, (x - width * 3, ground_y - 4, x + width * 3, ground_y + length), align=ds)
    if box is None or intensity <= 0:
        return
    wx, wy, gw, gh = _grid(f, par, box, ds)
    dy = np.clip((wy - ground_y) / length, 0.0, 1.0)
    w = width * (0.6 + 0.9 * dy)
    T = _tex(7600 + seed, 256, 12.0)
    band = _sample(T, wx / 9.0 + 3.0 * t * ripple, wy / 1.6 - 6.0 * t * ripple)
    I = np.exp(-((wx - x) / w) ** 2) * (1.0 - dy) ** 1.6 * (wy >= ground_y) * (0.25 + 1.1 * band ** 2)
    _add(f, _bgra(I * intensity, col), box[0], box[1], ds)


def _fft_noise(size, feature, seed, beta=3.4, detail=1.8):
    """Unclipped, zero-mean, unit-variance tileable FFT noise (smooth height field). Unlike
    core.noise_grid it is not percentile-clipped, so its derivatives have no kinks."""
    rng = np.random.default_rng([int(seed) & 0xFFFFFFFF, int(size), 991])
    spec = np.fft.rfft2(rng.standard_normal((size, size)))
    fy = np.fft.fftfreq(size)[:, None]
    fx = np.fft.rfftfreq(size)[None, :]
    fr = np.sqrt(fx * fx + fy * fy)
    f0 = 1.0 / max(feature, 2.0)
    amp = (f0 * f0 + fr * fr) ** (-beta / 4.0) * np.exp(-(fr / (f0 * detail)) ** 2)
    amp[0, 0] = 0.0
    h = np.fft.irfft2(spec * amp, s=(size, size))
    return (h - h.mean()) / (h.std() + 1e-12)


def _caustic_tex(seed, size=256, feature=22.0):
    """Tileable Hessian (hxx, hyy, hxy) of a smooth FFT-noise height field, unit variance."""
    def make():
        h = _fft_noise(size, feature, seed)
        R = lambda a, s, ax: np.roll(a, s, ax)
        hxx = R(h, -1, 1) - 2 * h + R(h, 1, 1)
        hyy = R(h, -1, 0) - 2 * h + R(h, 1, 0)
        hx = 0.5 * (R(h, -1, 1) - R(h, 1, 1))
        hxy = 0.5 * (R(hx, -1, 0) - R(hx, 1, 0))
        s = np.std(hxx) + 1e-12
        return np.dstack([hxx / s, hyy / s, hxy / s]).astype(np.float32)
    return cached(("atmos_caustic", seed, size, feature), make)


def _caustic_field(f, par, box, ds, t, cell=110.0, squash=1.0, speed=1.0, focus=1.0, seed=0, drift=(0.0, 0.0),
                   persp=None):
    """Caustic brightness (gh, gw) over an output-pixel box: 1/|det J| of the refraction map
    through two drifting wave layers (bright focal lines ~1.5, dark cells ~0).
    persp=(y_far, y_near, p, x_c): floor perspective - cells shrink to (1 - p) at y_far,
    converging toward x_c."""
    gw, gh = -(-(box[2] - box[0]) // ds), -(-(box[3] - box[1]) // ds)
    F = 22.0
    acc = np.zeros((gh, gw, 3), np.float32)
    if persp is None:
        G = _grid_affine(f, par, box, ds)
    else:
        wx, wy, _, _ = _grid(f, par, box, ds)
        yf, yn, pp, xc = persp
        Lr = max(yn - yf, 1.0)
        sy = np.clip((wy - yf) / Lr, -0.45 * (1.0 - pp) / max(pp, 1e-3), 1.5)
        z = (1.0 - pp) + pp * sy
        vint = (Lr / pp * np.log(z) if pp > 1e-3 else (wy - yf)).astype(np.float64)
        ux = ((wx - xc) / z).astype(np.float64)
    for T, sc, vel in ((_caustic_tex(8800 + seed), 1.0, (0.9, 0.55)), (_caustic_tex(8900 + seed), 0.83, (-0.7, 0.8))):
        size = T.shape[0]
        su, sv = F / (cell * sc), F / (cell * sc * squash)
        ou = (vel[0] * speed * F * 0.35 - drift[0] * su) * t
        ov = (vel[1] * speed * F * 0.35 - drift[1] * sv) * t
        if persp is None:
            S = np.array([[su, 0, ou], [0, sv, ov]], np.float64)
            Mx = S[:, :2] @ G[:, :2]
            off = S[:, :2] @ G[:, 2] + S[:, 2]
            A = np.hstack([Mx, np.mod(off, size)[:, None]])
            acc += cv2.warpAffine(T, A, (gw, gh), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                  borderMode=cv2.BORDER_WRAP)
        else:
            mu, mv = np.broadcast_arrays(np.mod(ux * su + ou, size), np.mod(vint * sv + ov, size))
            acc += cv2.remap(T, mu.astype(np.float32), mv.astype(np.float32), cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_WRAP)
    k = 0.53 * focus
    det = (1.0 + k * acc[..., 0]) * (1.0 + k * acc[..., 1]) - (k * acc[..., 2]) ** 2
    return np.clip(1.0 / (0.4 + np.abs(det)) - 0.55, 0.0, 3.0) * 0.8


def surface_from_below(f, y0=0.0, t=None, color=None, intensity=1.0, window_x=None, window_w=480.0,
                       glow=260.0, height=170.0, mirror=None, ripple=1.0, seed=0, par=1.0, **wave):
    """The sea surface seen from below. At world y0 a bright undulating meniscus; above it the
    underside of the surface (`height` px, perspective-compressed): inside Snell's window
    (centred on window_x, default camera x, half-width ~window_w) the bright sky refracted
    into a rippling mosaic; outside it a darker mirror (total internal reflection, color
    `mirror`); below it a glow of scattered light fading over `glow` px. Wave keywords:
    amp, wavelength, speed, chop, seed."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _mix(_pal(f, "surface", _skylight(f)), WHITE, 0.55)
    mir = _rgb(mirror) if mirror is not None else _pal(f, "mid", f.pal.fog_at(0.5))
    cam = f.lcam(par)
    vx0, vy0, vx1, vy1 = cam.view_rect(20)
    if y0 - height - 30 > vy1 or y0 + glow * 3 < vy0:
        return
    wx_c = cam.x if window_x is None else window_x
    ds = _ds(f, 2)
    box = _pxbox(f, par, (vx0, y0 - height - 30, vx1, y0 + glow * 3.0), pad=0, align=ds)
    if box is None:
        return
    wx, wy, gw, gh = _grid(f, par, box, ds)
    wk = dict(dict(amp=7.0, wavelength=300.0, speed=0.8, chop=0.6, seed=seed), **_wave_kw(wave))
    ys = wave_y(wx, t, y0, **wk).astype(np.float32)
    win = np.exp(-((wx - wx_c) / window_w) ** 2)
    dy = wy - ys
    q = np.clip(-dy / height, 0.0, 1.0)
    up = (dy < 0) * (1.0 - _ss(0.75, 1.0, q))
    # 1) the mirror: outside the window the underside reflects the dark water
    A = up * (0.82 - 0.7 * win) * (1.0 - 0.35 * q)
    over = np.empty((gh, gw, 4), np.float32)
    for ch, ci in ((0, 2), (1, 1), (2, 0)):
        over[..., ch] = mir[ci] * A * 255.0
    over[..., 3] = A * 255.0
    _over(f, np.clip(over, 0, 255).astype(np.uint8), box[0], box[1], ds)
    # 2) light: the refracted sky mosaic (squashed caustic network), the meniscus, the glow below
    mos = _caustic_field(f, par, box, ds, t, cell=95.0, squash=0.22, speed=1.4 * ripple, focus=1.25, seed=seed + 3,
                         drift=(25.0, 0.0))
    above = up * (0.18 + 0.82 * win) * (0.22 + 0.5 * np.minimum(mos, 2.0)) * (1.0 - q) ** 0.7
    line = (np.exp(-(dy / 2.4) ** 2) * 0.85 + np.exp(-(dy / 10.0) ** 2) * 0.18) * (0.45 + 0.55 * win)
    dyp = np.maximum(dy, 0.0)
    T3 = _tex(7500 + seed, 256, 30.0)
    dance = _sample(T3, wx / 4.0 + 5.0 * t, wy / 6.0 - 3.0 * t)
    below = (dy >= 0) * (np.exp(-dyp / glow) * 0.4 + np.exp(-dyp / (glow * 0.2)) * 0.16) * (0.6 + 0.8 * dance * ripple)
    below = below * (0.3 + 0.7 * win) * (1.0 - _ss(0.55, 1.0, dyp / (3.0 * glow)))
    I = intensity * (above + line + below)
    _add(f, _bgra(I, col), box[0], box[1], ds)


def caustics(f, y0, y1, x0=None, x1=None, t=None, cell=130.0, speed=1.0, focus=1.0, intensity=0.5,
             color=None, squash=0.5, perspective=0.6, feather=90.0, base=0.12, seed=0, par=1.0, mask=None):
    """Caustics: the moving light network that a wavy surface focuses onto a seabed region
    (world y0..y1, x0..x1, feathered). Physically based: the brightness of light refracted by
    a moving height field (two FFT-noise wave layers drifting apart) is 1/|det J| of the
    refraction map, so bright lines form where the surface focuses. cell: network cell size
    px (at the near edge y1); squash < 1 foreshortens it for a receding floor; perspective
    0..1 shrinks and dims the cells toward the far edge y0 (0 = a flat wall/hull); focus
    sharpens the lines; base adds the even sunlight between the lines. mask(ctx): optional -
    draws the surfaces that receive caustics (rocks, hull). Additive."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _mix(_pal(f, "surface", _skylight(f)), WHITE, 0.5)
    vx0, vy0, vx1, vy1 = f.lcam(par).view_rect(10)
    xa = vx0 if x0 is None else max(vx0, x0 - feather)
    xb = vx1 if x1 is None else min(vx1, x1 + feather)
    ya, yb = max(vy0, y0 - feather), min(vy1, y1 + feather)
    if xb <= xa or yb <= ya or intensity <= 0:
        return
    ds = _ds(f, 2)
    box = _pxbox(f, par, (xa, ya, xb, yb), align=ds)
    if box is None:
        return
    gw, gh = -(-(box[2] - box[0]) // ds), -(-(box[3] - box[1]) // ds)
    pp = clamp(perspective, 0.0, 0.95)
    I = _caustic_field(f, par, box, ds, t, cell, squash, speed, focus, seed,
                       persp=(y0, y1, pp, f.lcam(par).x) if pp > 0 else None) + base
    wx, wy, _, _ = _grid(f, par, box, ds)
    win = _ss(y0 - feather, y0 + feather * 0.25, wy) * (1.0 - _ss(y1 - feather * 0.25, y1 + feather, wy))
    if pp > 0:
        win = win * (1.0 - 0.6 * pp * (1.0 - np.clip((wy - y0) / max(y1 - y0, 1.0), 0.0, 1.0)))
    if x0 is not None:
        win = win * _ss(x0 - feather, x0 + feather * 0.25, wx)
    if x1 is not None:
        win = win * (1.0 - _ss(x1 - feather * 0.25, x1 + feather, wx))
    I = I * win * intensity
    if mask is not None:
        ms = cairo.ImageSurface(cairo.FORMAT_A8, gw, gh)
        mc = cairo.Context(ms)
        mc.set_matrix(_M(f, par).multiply(cairo.Matrix(x0=-box[0], y0=-box[1])).multiply(cairo.Matrix(xx=1.0 / ds, yy=1.0 / ds)))
        mask(mc)
        mc.fill()
        ms.flush()
        mm = np.ndarray((gh, ms.get_stride()), np.uint8, buffer=ms.get_data())[:, :gw].astype(np.float32) / 255.0
        I = I * mm
    _add(f, _bgra(I, col), box[0], box[1], ds)


# ============================================================================ 6. weather & sky
def _displace(pts, seed, jag, detail):
    pts = [tuple(p) for p in pts]
    for lev in range(detail):
        out = [pts[0]]
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            dx, dy = bx - ax, by - ay
            L = math.hypot(dx, dy) or 1.0
            o = (hash01(seed, lev, i) - 0.5) * 2.0 * jag * L
            out.append(((ax + bx) * 0.5 - dy / L * o, (ay + by) * 0.5 + dx / L * o))
            out.append(pts[i + 1])
        pts = out
    return pts


def bolt_points(start, end, seed=0, jag=0.22, detail=7, branches=3, branch_len=(0.15, 0.42)):
    """Lightning geometry by midpoint displacement: [(points, weight), ...] - the main channel
    (weight 1) then forks (weight < 1). Deterministic for a seed."""
    main = _displace([start, end], seed, jag, detail)
    total = math.hypot(end[0] - start[0], end[1] - start[1])
    out = [(main, 1.0)]
    n = len(main)
    for b in range(branches):
        i = int(n * (0.1 + 0.6 * hash01(seed, b, 1)))
        p, q = main[i], main[min(i + 4, n - 1)]
        d = math.atan2(q[1] - p[1], q[0] - p[0])
        d += math.radians((22 + 30 * hash01(seed, b, 2)) * (1 if hash01(seed, b, 3) > 0.5 else -1))
        L = total * lerp(branch_len[0], branch_len[1], hash01(seed, b, 4))
        e = (p[0] + math.cos(d) * L, p[1] + math.sin(d) * L)
        pts = _displace([p, e], seed + 97 * (b + 1), jag * 0.85, max(2, detail - 3))
        wgt = 0.32 + 0.18 * hash01(seed, b, 5)
        out.append((pts, wgt))
        if hash01(seed, b, 6) > 0.4:
            j = int(len(pts) * (0.3 + 0.4 * hash01(seed, b, 7)))
            p2 = pts[j]
            d2 = d + math.radians(30 * (1 if hash01(seed, b, 8) > 0.5 else -1))
            e2 = (p2[0] + math.cos(d2) * L * 0.4, p2[1] + math.sin(d2) * L * 0.4)
            out.append((_displace([p2, e2], seed + 31 * (b + 7), jag * 0.85, max(2, detail - 4)), wgt * 0.55))
    return out


def _strokes(dt, seed, j):
    """Return-stroke pulses of one strike (bolt visibility), dt = t - t_strike."""
    if dt < -0.01 or dt > 1.2:
        return 0.0
    n = 2 + int(hash01(seed, j, 1) * 3)
    tt, v = 0.0, 0.0
    for kk in range(n):
        amp = 1.0 if kk == 0 else 0.45 + 0.5 * hash01(seed, j, kk, 2)
        v = max(v, amp * pulse(dt, tt, attack=0.012, decay=0.055))
        tt += 0.045 + 0.11 * hash01(seed, j, kk, 3)
    return v


def flash_env(t, strikes, seed=0):
    """Lightning flash envelope 0..1 at t for strike times `strikes` (list): 2-4 flickering
    return strokes over ~0.3 s plus a short afterglow."""
    if isinstance(strikes, (int, float)):
        strikes = [strikes]
    v = 0.0
    for j, t0 in enumerate(strikes):
        dt = t - t0
        if dt < -0.01 or dt > 3.0:
            continue
        v = max(v, _strokes(dt, seed, j), 0.22 * pulse(dt, 0.0, attack=0.02, decay=0.4))
    return clamp(v)


def lightning(f, strikes, start, end, t=None, seed=0, color=None, flash=0.3, width=3.0, branches=3,
              jag=0.22, glow=1.0, bolt=True, par=0.3):
    """Lightning: a forked bolt from start to end (world, layer `par`, usually far) visible on
    each return stroke of strikes at times `strikes` (s), plus the flash envelope: sets
    f.post['flash'] (strength `flash` * envelope, color pal.lightning) and returns the
    envelope 0..1 - use it to brighten the sky / rim-light silhouettes."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _pal(f, "lightning", (0.86, 0.9, 1.0))
    if isinstance(strikes, (int, float)):
        strikes = [strikes]
    I = flash_env(t, strikes, seed)
    if I <= 0.002:
        return 0.0
    if flash > 0:
        f.post["flash"] = max(f.post.get("flash", 0.0), flash * I)
        f.post["flash_color"] = col
    if not bolt:
        return I
    for j, t0 in enumerate(strikes):
        v = _strokes(t - t0, seed, j)
        if v < 0.05:
            continue
        geo = bolt_points(start, end, seed + 131 * j, jag, 7, branches)
        xs = [p[0] for pts, _ in geo for p in pts]
        ys = [p[1] for pts, _ in geo for p in pts]
        bb = (min(xs), min(ys), max(xs), max(ys))
        with light(f, par=par, blur=28.0, bbox=bb) as A:
            for pts, wgt in geo:
                draw.poly(A, pts, close=False)
                A.set_source_rgba(col[0], col[1], col[2], clamp(0.5 * v * wgt * glow))
                A.set_line_width(width * 9 * wgt)
                A.stroke()
        with light(f, par=par, blur=5.0, bbox=bb) as A:
            for pts, wgt in geo:
                draw.poly(A, pts, close=False)
                A.set_source_rgba(col[0], col[1], col[2], clamp(0.7 * v * wgt))
                A.set_line_width(width * 3.0 * wgt)
                A.stroke()
        with _main(f, par, cairo.OPERATOR_ADD) as C:
            for pts, wgt in geo:
                draw.poly(C, pts, close=False)
                C.set_source_rgba(*_hot(col, 0.8), clamp(v * (0.6 + 0.4 * wgt)))
                C.set_line_width(max(0.8, width * wgt))
                C.stroke()
    return I


def moon(f, c, r=70.0, t=None, color=None, halo=1.0, clouds=0.0, cloud_speed=12.0, cloud_color=None,
         texture=0.07, seed=0, par=0.05, emit=1.0):
    """Moon: crisp disc (faint maria), soft halo (light + emit) and optional drifting clouds
    (coverage 0..1) that pass in front with moonlit silver edges. Far layer (par 0.05).
    Returns the visible fraction 0..1 (scale moonlight with it)."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _pal(f, "moon", (0.92, 0.94, 0.88))
    cam = f.lcam(par)
    vx0, vy0, vx1, vy1 = cam.view_rect(20)
    vis = 1.0
    cloud = None
    if clouds > 0:
        ds = _ds(f, 3)
        band = (vx0, c[1] - 3.6 * r, vx1, c[1] + 3.6 * r)
        box = _pxbox(f, par, band, align=ds)
        if box is not None:
            wx, wy, gw, gh = _grid(f, par, box, ds)
            T = _tex(6100 + seed, 512, 70.0)
            T2 = _tex(6200 + seed, 256, 18.0)
            n = 0.75 * _sample(T, (wx - cloud_speed * t) / 2.6, wy / 1.1) + \
                0.25 * _sample(T2, (wx - cloud_speed * 1.3 * t) / 1.4, wy / 1.0)
            th = 1.0 - clouds
            A = _ss(th - 0.02, th + 0.22, n)
            A = A * (1.0 - _ss(2.2 * r, 3.6 * r, np.abs(wy - c[1])))
            d = np.sqrt((wx - c[0]) ** 2 + (wy - c[1]) ** 2)
            rim = (1.0 - _ss(th, th + 0.3, n)) * np.exp(-d / (2.2 * r))
            ccol = _rgb(cloud_color) if cloud_color is not None else _mix(_pal(f, "sky_top", (0.05, 0.06, 0.08)), col, 0.12)
            disc = d < r
            if disc.any():
                vis = float(1.0 - np.mean(np.broadcast_to(A, disc.shape)[disc]))
            cloud = (box, ds, A.astype(np.float32), rim.astype(np.float32), ccol)
    k = halo * (0.25 + 0.75 * vis)
    with light(f, par=par, blur=0, ds=_ds(f, 4), bbox=(c[0] - 9 * r, c[1] - 9 * r, c[0] + 9 * r, c[1] + 9 * r)) as L:
        for R, a in ((2.6 * r, 0.32), (9.0 * r, 0.12)):
            g = cairo.RadialGradient(c[0], c[1], r * 0.9, c[0], c[1], R)
            for o, v in ((0.0, 1.0), (0.15, 0.55), (0.4, 0.2), (0.7, 0.05), (1.0, 0.0)):
                g.add_color_stop_rgba(o, col[0], col[1], col[2], clamp(a * k * v))
            L.set_source(g)
            L.arc(c[0], c[1], R, 0, TAU)
            L.fill()
    with _main(f, par) as C:
        draw.circle(C, c, r)
        draw.fill(C, col)
        if texture > 0:
            C.save()
            draw.circle(C, c, r)
            C.clip()
            for i in range(7):
                a = TAU * hash01(seed, i, 1)
                dd = r * 0.7 * hash01(seed, i, 2)
                rr = r * (0.12 + 0.28 * hash01(seed, i, 3))
                draw.circle(C, (c[0] + math.cos(a) * dd, c[1] + math.sin(a) * dd), rr)
                draw.fill(C, _mix(col, (0.5, 0.52, 0.55), 0.5), texture * (0.5 + hash01(seed, i, 4)))
            C.restore()
    if emit > 0:
        with f.emit(par) as G:
            draw.glow_disc(G, c, r * 1.5, col, clamp(0.55 * emit * vis))
    if cloud is not None:
        box, ds, A, rim, ccol = cloud
        lit = np.clip(rim * 1.4, 0, 1)
        img = np.empty(A.shape + (4,), np.float32)
        for ch, ci in ((0, 2), (1, 1), (2, 0)):
            img[..., ch] = (ccol[ci] * (1 - lit) + col[ci] * 0.85 * lit) * A * 255.0
        img[..., 3] = A * 255.0
        _over(f, np.clip(img, 0, 255).astype(np.uint8), box[0], box[1], ds)
    return vis


def ground_mist(f, y, height=320.0, color=None, alpha=0.5, t=None, speed=16.0, layers=3, tex=0.8,
                scale=1.0, seed=0, par=1.0):
    """Rolling ground mist: `layers` drifting, breathing f.haze bands piled on the ground line
    (world y), densest at the ground, fading upward over `height` px. Alternate layers drift
    in opposite directions at `speed` px/s; tex 0..1 breaks it into wisps."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _rgb(f.pal.fog_at(0.55))
    for i in range(layers):
        k = (i + 1) / layers
        top = y - height * (0.25 + 0.85 * k) + 14.0 * math.sin(t * 0.23 + 1.9 * i + seed)
        a = alpha * (1.2 - 0.6 * k) / max(layers, 1) * 1.5
        sp = speed * (0.7 + 0.6 * i) * (-1.0 if i % 2 else 1.0)
        f.haze(col, clamp(a), y0=top, y1=y + height * 0.2, feather=height * 0.7, tex=tex,
               tex_scale=scale * (0.9 + 0.35 * i), scroll=(sp, 0.0), seed=seed * 5 + i, par=par)


# ============================================================================ 7. fire
def _tongue_polys(bx, by, hw, h, lean, wig, ph, n=7):
    """Vectorized flame-tongue outlines. Inputs: arrays (N,) - base point, half-width, height,
    tip lean, wiggle amplitude, wiggle phase. Returns (N, 2n+2, 2) polygons: a rounded base,
    a body swelling a little above the base, a travelling S-wiggle and a sharp tip."""
    bx, by, hw, h, lean, wig, ph = [np.asarray(v, float)[:, None] for v in (bx, by, hw, h, lean, wig, ph)]
    s = np.linspace(0.0, 0.93, n)[None, :]
    w = hw * (1.0 - s) ** 0.85 * (1.0 + 0.6 * s) * np.minimum(1.0, 0.55 + 4.0 * s)
    cx = bx + lean * s * s + wig * np.sin(TAU * 1.3 * s - ph) * s
    y = by - h * s
    tipx = bx + lean + wig * np.sin(TAU * 1.3 - ph)
    tipy = by - h
    bot = np.stack([bx, by + hw * 0.35], -1)
    left = np.stack([cx - w, y], -1)
    right = np.stack([cx + w, y], -1)[:, ::-1]
    tip = np.stack([tipx, tipy], -1)
    return np.concatenate([bot, left, tip, right], axis=1)


FLAME_LAYERS = ((1.0, 1.0, 0.0, 0.9), (0.62, 0.6, 0.45, 0.92), (0.34, 0.3, 0.9, 1.0))   # (w, h, hot, alpha)
BURN_LAYERS = ((1.0, 1.0, 0.0, 0.85), (0.6, 0.62, 0.4, 0.92), (0.3, 0.4, 0.8, 1.0))


def _draw_tongues(f, par, T, col, k=1.0, soft=1.5, layers=FLAME_LAYERS, n=7, emit=0.5, ramp=None, ribbon=None):
    """Composite flame tongues (rows of T = bx, by, hw, h, lean, wig, ph, bright) OVER the frame:
    nested outer/mid/core bands (each overwrites the last, so brightness never piles up), a
    little blur, plus an emissive glow. ramp=(base_y, height): fade toward the tips.
    ribbon=(polylines, alphas, width_px): lines the tongues stand on, drawn in every band (width
    scaled like the band) so a row of tongues reads as one burning strand, plus a hot thread."""
    if not len(T):
        return
    T = np.asarray(T, float)
    pad = float(T[:, 3].max()) * 0.5 + float(T[:, 2].max()) * 2 + 8
    bb = (T[:, 0].min() - pad, (T[:, 1] - T[:, 3]).min() - pad, T[:, 0].max() + pad, T[:, 1].max() + pad)
    box = _pxbox(f, par, bb, pad=4 + 3 * soft)
    if box is None:
        return
    img = _canvas(f, box, 1)
    cm = _canvas_matrix(f, par, box, 1)
    br = T[:, 7] if T.shape[1] > 7 else np.ones(len(T))
    rib = []
    if ribbon is not None:
        polys, ral, rw = ribbon
        ral = np.asarray(ral, float)
        rq = np.minimum((np.clip(ral, 0, 1) * 4).astype(int), 3)
        rib = [(lv, [np.rint(np.stack(_xf(cm, q[:, 0], q[:, 1]), -1) * _SK).astype(np.int32)
                     for q, ok in zip(polys, rq == lv) if ok]) for lv in np.unique(rq)]
    for (sw, sh, hot, a) in layers + (((0.12, 0.0, 0.95, 1.0),) if rib else ()):
        P = _tongue_polys(T[:, 0], T[:, 1], T[:, 2] * sw, T[:, 3] * sh, T[:, 4] * sh, T[:, 5] * sh, T[:, 6], n)
        X, Y = _xf(cm, P[..., 0], P[..., 1])
        P = np.rint(np.stack([X, Y], -1) * _SK).astype(np.int32)
        c = _hot(col, hot)
        q = np.minimum((np.clip(br, 0, 1) * 4).astype(int), 3)
        for lv in np.unique(q):
            sel = np.flatnonzero(q == lv)
            al = clamp(a * k * (lv + 1) / 4.0)
            if sh > 0:
                cv2.fillPoly(img, list(P[sel]), (255 * c[2] * al, 255 * c[1] * al, 255 * c[0] * al, 255 * al), _AA, _SH)
        for lv, Ps in rib:
            al = clamp(a * k * (lv + 1) / 4.0)
            cv2.polylines(img, Ps, False, (255 * c[2] * al, 255 * c[1] * al, 255 * c[0] * al, 255 * al),
                          max(1, int(round(rw * sw * f.scale))), _AA, _SH)
    if ramp is not None:
        by, hh = ramp
        im = _inv(cm)
        rows = np.arange(img.shape[0], dtype=np.float64)
        wy = _xf(im, np.full_like(rows, img.shape[1] * 0.5), rows)[1]
        r = 1.0 - 0.7 * _ss(by - 0.25 * hh, by - 1.05 * hh, wy)
        img = (img * r[:, None, None].astype(np.float32)).astype(np.uint8)
    if soft > 0.3:
        img = cv2.GaussianBlur(img, (0, 0), soft * f.scale)
    _over(f, img, box[0], box[1], 1)
    if emit > 0:
        P = _tongue_polys(T[:, 0], T[:, 1], T[:, 2] * 0.7, T[:, 3] * 0.55, T[:, 4] * 0.55, T[:, 5] * 0.5, T[:, 6], 5)
        with f.emit(par) as G:
            for poly in P[::2]:
                draw.poly(G, poly.tolist())
            G.set_source_rgba(col[0], col[1], col[2], clamp(emit * k))
            G.fill()


def flames(f, base, height=110.0, width=None, t=None, seed=0, intensity=1.0, color=None, tongues=None,
           wind=0.0, par=1.0, glow=1.0, licks=True, soft=2.0, tint=None):
    """Procedural fire: flickering silhouette tongues (amber body, hot near-white core, composited
    OVER so the hue survives on bright fog) along a base point (x, y) or segment
    ((x0, y0), (x1, y1)), detached licks, an emissive glow and a big soft additive light halo.
    height px; wind leans the tongues (+ = right). Returns the fire-light level
    (intensity * fire_light(t)) for lighting the scene."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _rgb(f.pal.light)
    if isinstance(base[0], (tuple, list)):
        (x0, y0), (x1, y1) = base
    else:
        x0 = x1 = float(base[0])
        y0 = y1 = float(base[1])
        width = width if width is not None else height * 0.5
        x0, x1 = x0 - width / 2, x1 + width / 2
    width = max(abs(x1 - x0), 1.0)
    n = tongues or max(4, int(round(width / (height * 0.11))) + 2)
    fl = fire_light(t, seed) * intensity
    T = []
    for i in range(n):
        u = (i + 0.5) / n + 0.35 / n * noise1(t * 0.9 + 3.1 * i, seed + 1)
        prof = math.sin(math.pi * clamp(u, 0.03, 0.97)) ** 0.75
        fk = 0.5 + 0.5 * fbm1(t * 2.8 + 5.3 * i, seed + 2)
        hh = height * prof * (0.4 + 0.6 * fk) * (0.75 + 0.5 * hash01(seed, i))
        hw = max(width / n * 0.8, height * 0.055) * (0.8 + 0.4 * hash01(seed, i, 5)) * (0.7 + 0.3 * prof)
        lean = (wind * 0.004 + 0.16 * noise1(t * 1.7 + 2.2 * i, seed + 3)) * hh
        wig = hh * 0.09 * (0.6 + 0.4 * noise1(t * 3.3 + i, seed + 4))
        ph = t * (7.0 + 3.0 * hash01(seed, i, 2)) + TAU * hash01(seed, i, 3)
        T.append((lerp(x0, x1, u), lerp(y0, y1, u), hw, hh, lean, wig, ph, 1.0))
    if licks:
        for j in range(max(1, n // 3 + 1)):
            P = 0.45 + 0.35 * hash01(seed, j, 11)
            ph0 = P * hash01(seed, j, 12)
            tau = (t + ph0) % P
            cyc = math.floor((t + ph0) / P)
            u = 0.2 + 0.6 * hash01(seed, j, cyc, 13)
            hh = height * (0.65 + 0.35 * hash01(seed, j, cyc, 14))
            sp = tau / P
            if sp < 0.85:
                T.append((lerp(x0, x1, u) + wind * 0.004 * hh * (1 + sp), lerp(y0, y1, u) - hh * (0.62 + 0.55 * sp),
                          height * 0.035 * (1 - sp), height * 0.2 * (1 - sp) ** 0.7, 0.0, height * 0.02, t * 9.0,
                          (1 - sp) ** 0.5))
    Rg = height * 2.4
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1) - height * 0.4
    with light(f, par=par, blur=0, ds=_ds(f, 4), bbox=(cx - Rg - width / 2, cy - Rg, cx + Rg + width / 2, cy + Rg),
               tint=auto_tint(f, tint)) as A:
        A.save()
        A.translate(cx, cy)
        A.scale(1.0 + width / (2 * Rg), 1.0)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, Rg)
        for o, v in ((0.0, 0.26), (0.12, 0.18), (0.3, 0.08), (0.6, 0.025), (1.0, 0.0)):
            g.add_color_stop_rgba(o, col[0], col[1], col[2], clamp(v * fl * glow))
        A.set_source(g)
        A.arc(0, 0, Rg, 0, TAU)
        A.fill()
        A.restore()
    _draw_tongues(f, par, T, col, k=min(fl, 1.0), soft=soft, n=12 if height > 60 else 7,
                  emit=0.3 * (1.0 - 0.8 * auto_tint(f, tint)), ramp=(max(y0, y1), height))
    return fl


class Fuse:
    """A polyline resampled every `step` px with an ignition time per point (s) - something
    that burns: a web strand, a rope, a fuse, a line of oil. Build with Fuse.along() or
    burn_web(); draw with burning()."""

    def __init__(self, pts, times):
        self.pts = np.asarray(pts, float)
        self.times = np.asarray(times, float)

    @staticmethod
    def resample(pts, step=8.0):
        pts = np.asarray(pts, float)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        n = max(2, int(math.ceil(cum[-1] / step)) + 1)
        s = np.linspace(0.0, cum[-1], n)
        return np.stack([np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])], 1), s

    @classmethod
    def along(cls, pts, t0=0.0, speed=400.0, start=0.0, step=8.0):
        """Ignited at t0 at arc-length fraction `start` (0 = first point, 1 = last, 0.5 = middle:
        burns both ways) and travelling at `speed` px/s."""
        P, s = cls.resample(pts, step)
        s0 = clamp(start) * s[-1]
        return cls(P, t0 + np.abs(s - s0) / max(speed, 1e-6))

    def intact(self, t, burn=0.8, keep=0.55):
        """Polylines still standing at t (unburnt, or burning for less than keep*burn s): draw
        these in ink so the strand visibly burns through."""
        ok = (t - self.times) < burn * keep
        out, cur = [], []
        for p, o in zip(self.pts.tolist(), ok.tolist()):
            if o:
                cur.append(tuple(p))
            elif cur:
                if len(cur) > 1:
                    out.append(cur)
                cur = []
        if len(cur) > 1:
            out.append(cur)
        return out


def burn_web(strands, origin, t0=0.0, speed=400.0, step=8.0, snap=7.0):
    """Fire spreading through a network of strands (a spider web, rigging, a hedge of ropes):
    strands are polylines that touch/cross; fire starts at `origin` (x, y) at t0 and travels at
    `speed` px/s along strands, jumping between strands wherever they come within `snap` px
    (shortest-path, Dijkstra). Returns a list of Fuse (one per strand)."""
    res = [Fuse.resample(s, step)[0] for s in strands]
    offs = np.cumsum([0] + [len(p) for p in res])
    allp = np.concatenate(res)
    N = len(allp)
    adj = [[] for _ in range(N)]
    for k, p in enumerate(res):
        o = offs[k]
        d = np.hypot(*np.diff(p, axis=0).T)
        for i in range(len(p) - 1):
            adj[o + i].append((o + i + 1, d[i]))
            adj[o + i + 1].append((o + i, d[i]))
    cell = max(snap, 1.0)
    grid = {}
    owner = np.repeat(np.arange(len(res)), [len(p) for p in res])
    for i, (x, y) in enumerate(allp.tolist()):
        grid.setdefault((int(x // cell), int(y // cell)), []).append(i)
    for i, (x, y) in enumerate(allp.tolist()):
        gx, gy = int(x // cell), int(y // cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx + dx, gy + dy), ()):
                    if j > i and owner[j] != owner[i]:
                        d = math.hypot(allp[j, 0] - x, allp[j, 1] - y)
                        if d <= snap:
                            adj[i].append((j, d))
                            adj[j].append((i, d))
    d0 = np.hypot(allp[:, 0] - origin[0], allp[:, 1] - origin[1])
    start = int(np.argmin(d0))
    dist = np.full(N, np.inf)
    dist[start] = d0[start]
    pq = [(dist[start], start)]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist[i]:
            continue
        for j, w in adj[i]:
            nd = d + w
            if nd < dist[j]:
                dist[j] = nd
                heapq.heappush(pq, (nd, j))
    dist[np.isinf(dist)] = 1e9
    times = t0 + dist / max(speed, 1e-6)
    return [Fuse(res[k], times[offs[k]:offs[k + 1]]) for k in range(len(res))]


def _runs(key):
    """Runs of equal non-negative key over segments: [(level, i0, i1)] - points i0..i1 inclusive."""
    key = np.asarray(key)
    if not key.size:
        return []
    chg = np.flatnonzero(np.diff(key) != 0) + 1
    st = np.concatenate([[0], chg])
    en = np.concatenate([chg, [key.size]])
    return [(int(key[i]), int(i), int(j)) for i, j in zip(st, en) if key[i] >= 0]


CHAR_COLORS = ((0.3, 0.9), (-0.45, 0.8), (-0.8, 0.6), (-1.0, 0.3))   # (heat: + toward white, - toward ink; alpha)


def burning(f, fuses, t=None, burn=0.8, height=30.0, char=1.4, embers_rate=1.0, intensity=1.0, color=None,
            wind=10.0, seed=0, par=1.0, glow=1.0, halo=1.0, tint=None):
    """Draw fire travelling along Fuses at time t: a white-hot spark at each front, a continuous
    ribbon of flame tongues along the burning stretch (each point burns `burn` s: flares up,
    then dies) over a white-hot thread, a char line that cools from amber to ink for `char` s
    and then breaks, a soft light halo and rising embers (embers_rate x). height px is the flame
    height. Batched: pass all strands of a web in one call. Returns [intact polylines per fuse]
    (Fuse.intact) to draw the standing strands in ink."""
    t = _now(f, t)
    col = _rgb(color) if color is not None else _rgb(f.pal.light)
    if isinstance(fuses, Fuse):
        fuses = [fuses]
    fl = fire_light(t, seed) * intensity
    tint = auto_tint(f, tint)
    TT, sparks, segs, threads, th_a, chars = [], [], [[], [], []], [], [], [[], [], [], []]
    hp = []     # (x, y, weight) of burning points for the halo
    for fi, fu in enumerate(fuses):
        age = t - fu.times
        if not (age >= 0).any():
            continue
        step = float(np.median(np.hypot(*np.diff(fu.pts, axis=0).T))) if len(fu.pts) > 1 else 8.0
        on = (age >= 0) & (age < burn)
        a = np.clip(age / burn, 0.0, 1.0)
        env = np.where(on, _ss(0.0, 0.08, a) * (1.0 - a) ** 0.8, 0.0)
        idx = np.flatnonzero(on)
        if idx.size:
            e = env[idx]
            nz = 0.5 + 0.5 * _vnoise(t * 3.1 + idx * 0.37, seed + fi)          # flicker
            tall = 0.5 + 0.5 * _vnoise(t * 1.3 + idx * 0.23, seed + 11 + fi)    # clusters of tall licks
            hh = height * e * (0.45 + 0.3 * nz + 0.65 * tall ** 2)
            keep = (hh > 1.2) & (_vhash(seed + 3, fi, idx) < 0.6)            # irregular spacing
            i2, hh, e2 = idx[keep], hh[keep], e[keep]
            if i2.size:
                lean = (wind * 0.006 + 0.22 * _vnoise(t * 1.5 + 0.3 * i2, seed + 7)) * hh
                hw = max(0.95 * step, 0.2 * height) * (0.5 + 0.5 * e2) * (0.8 + 0.4 * _vhash(seed + 4, fi, i2))
                TT.append(np.stack([fu.pts[i2, 0], fu.pts[i2, 1], hw, hh, lean, hh * 0.11, t * 8.0 + 1.7 * i2 + fi,
                                    0.55 + 0.45 * e2], 1))
                hp.append(np.stack([fu.pts[i2, 0], fu.pts[i2, 1], e2], 1))
            # glow + hot thread: runs of burning segments, bucketed by heat
            se = 0.5 * (env[:-1] + env[1:])
            key = np.where(on[:-1] & on[1:], np.minimum((se * 3).astype(int), 2), -1)
            for lv, i0, i1 in _runs(key):
                segs[lv].append(fu.pts[i0:i1 + 1])
                threads.append(fu.pts[i0:i1 + 1])
                th_a.append(0.55 + 0.15 * lv)
        front = np.flatnonzero((age >= 0) & (age < 0.12))
        for i in front:
            nb = [j for j in (i - 1, i + 1) if 0 <= j < len(age)]
            if len(nb) < 2 or any(age[j] < 0 for j in nb):
                sparks.append((fu.pts[i, 0], fu.pts[i, 1]))
        ch = (age >= burn * 0.5) & (age < burn + char)
        if ch.any():
            cool = np.clip((age - burn * 0.5) / (burn * 0.5 + char), 0.0, 1.0)
            # the char breaks up as it cools: drop pieces by a per-point hash
            brk = _vhash(seed + 31 + fi, np.arange(len(age))) > 1.1 - cool * 1.1
            q = np.minimum((cool * 4).astype(int), 3)
            sc = ch[:-1] & ch[1:] & ~brk[:-1]
            for lv, i0, i1 in _runs(np.where(sc, q[:-1], -1)):
                chars[lv].append(fu.pts[i0:i1 + 1])
    if any(segs):
        P = np.concatenate([p for bucket in segs for p in bucket])
        pad = height * 3
        bb = (P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        with light(f, par=par, blur=height * 0.9, bbox=bb, tint=tint) as A:
            A.set_line_join(cairo.LINE_JOIN_ROUND)
            A.set_line_cap(cairo.LINE_CAP_ROUND)
            for lv, bucket in enumerate(segs):
                if not bucket:
                    continue
                for run in bucket:
                    A.move_to(run[0, 0], run[0, 1] - height * 0.3)
                    for x, y in run[1:]:
                        A.line_to(x, y - height * 0.3)
                A.set_line_width(height * 1.6)
                A.set_source_rgba(col[0], col[1], col[2], clamp(0.055 * (lv + 1) * fl * glow))
                A.stroke()
    if hp and halo > 0:
        H = np.concatenate(hp)
        w = H[:, 2].sum()
        if w > 0:
            cx, cy = (H[:, 0] * H[:, 2]).sum() / w, (H[:, 1] * H[:, 2]).sum() / w - height * 0.5
            sd = math.sqrt(max(((H[:, 0] - cx) ** 2 * H[:, 2]).sum() / w + ((H[:, 1] - cy) ** 2 * H[:, 2]).sum() / w, 1.0))
            R = sd * 1.6 + height * 6
            I = clamp(0.2 * halo * fl * min(1.0, w / 25.0) ** 0.6)
            with light(f, par=par, blur=0, ds=_ds(f, 6), bbox=(cx - R, cy - R, cx + R, cy + R), tint=tint) as A:
                draw.radial(A, (cx, cy), 0, R, [(0, col, I), (0.25, col, I * 0.55), (0.6, col, I * 0.15), (1, col, 0.0)])
                A.arc(cx, cy, R, 0, TAU)
                A.fill()
    if any(chars):
        with _main(f, par) as C:
            C.set_line_width(max(1.0, height * 0.065))
            C.set_line_join(cairo.LINE_JOIN_ROUND)
            for lv, bucket in enumerate(chars):
                if not bucket:
                    continue
                for run in bucket:
                    C.move_to(*run[0])
                    for x, y in run[1:]:
                        C.line_to(x, y)
                heat, al = CHAR_COLORS[lv]
                c = _hot(col, heat) if heat >= 0 else _mix(_mix(col, (0.55, 0.12, 0.04), 0.6), f.pal.ink, -heat)
                C.set_source_rgba(c[0], c[1], c[2], al)
                C.stroke()
    if TT:
        T = np.concatenate(TT)
        _draw_tongues(f, par, T, col, k=min(fl, 1.0), soft=0.9, n=7, emit=0.3 * (1.0 - 0.8 * tint), layers=BURN_LAYERS,
                      ribbon=(threads, th_a, float(np.median(T[:, 2])) * 0.7))
    if sparks:
        with f.emit(par) as G:
            for x, y in sparks:
                draw.glow_disc(G, (x, y), height * 0.8, _hot(col, 0.6), clamp(0.7 * fl * (1.0 - 0.7 * tint)))
        rs = height * 0.25
        with _main(f, par, cairo.OPERATOR_ADD) as C:
            for x, y in sparks:
                draw.radial(C, (x, y), 0, rs, [(0, _hot(col, 0.95), 1.0), (0.5, _hot(col, 0.6), 0.5), (1, col, 0.0)])
                C.arc(x, y, rs, 0, TAU)
                C.fill()
    if embers_rate > 0 and fuses and TT:
        allp = np.concatenate([fu.pts for fu in fuses])
        allt = np.concatenate([fu.times for fu in fuses])
        order = np.argsort(allt)
        allp, allt = allp[order], allt[order]

        def samp(tk, u):
            lo = np.searchsorted(allt, tk - burn)
            hi = np.searchsorted(allt, tk)
            cnt = hi - lo
            i = np.clip(lo + (u * np.maximum(cnt, 1)).astype(int), 0, len(allt) - 1)
            return allp[i, 0], allp[i, 1] - height * 0.3, cnt > 0
        nburn = sum(len(x) for x in TT)
        rate = embers_rate * clamp(nburn / 5.0, 2.0, 70.0)
        embers(f, samp, rate=rate, life=(0.8, 2.0), rise=(60.0, 150.0), spread=25.0, wind=wind, size=(0.9, 2.0),
               color=col, intensity=intensity, t=t, seed=seed + 5, par=par)
    return [fu.intact(t, burn) for fu in fuses]


def burning_line(f, pts, t0=0.0, speed=400.0, start=0.0, t=None, **kw):
    """Convenience: fire travelling along one polyline ignited at t0 at fraction `start`
    (see Fuse.along) at `speed` px/s. Keywords go to burning(). Returns intact polylines."""
    return burning(f, [Fuse.along(pts, t0, speed, start)], t=t, **kw)[0]


# ============================================================================ 8. underwater depth
def depth_stops(surface_y=0.0, scale=1.0, pal=None):
    """Water color stops [(world_y, rgb), ...] from the sunlit surface (aqua) through teal to
    ink-black. scale stretches the depths (1 = black by ~9000 px below the surface)."""
    from .palette import SALVAGE
    p = pal or SALVAGE
    surf = _rgb(getattr(p, "surface", p.fog_at(1.0)))
    mid = _rgb(getattr(p, "mid", p.fog_at(0.5)))
    deep = _rgb(getattr(p, "deep", p.fog_at(0.0)))
    ink = _rgb(p.ink)
    return [(surface_y, surf), (surface_y + 260 * scale, _mix(surf, mid, 0.5)), (surface_y + 1100 * scale, mid),
            (surface_y + 2800 * scale, _mix(mid, deep, 0.6)), (surface_y + 5500 * scale, deep),
            (surface_y + 9000 * scale, ink)]


def depth_color(y, surface_y=0.0, scale=1.0, pal=None):
    """Water color at world depth y (use as fog_color for layers at that depth)."""
    st = depth_stops(surface_y, scale, pal)
    if y <= st[0][0]:
        return st[0][1]
    for (y0, c0), (y1, c1) in zip(st, st[1:]):
        if y <= y1:
            return _mix(c0, c1, (y - y0) / (y1 - y0))
    return st[-1][1]


def depth_light(y, surface_y=0.0, scale=1.0):
    """Ambient daylight left at world depth y: 1 at the surface -> ~0 in the abyss."""
    d = max(0.0, y - surface_y) / max(scale, 1e-6)
    return math.exp(-d / 1500.0)


def abyss(f, surface_y=0.0, scale=1.0, pal=None, t=None, texture=0.35, seed=0):
    """Underwater backdrop for a vertical journey: the depth gradient anchored in world y (it
    scrolls with the camera, so a descent darkens from aqua to ink), plus slow, parallaxed
    light blotches (texture 0..1) that sell the motion."""
    t = _now(f, t)
    st = depth_stops(surface_y, scale, pal or f.pal)
    f.sky_world(st, par=1.0)
    if texture > 0:
        cam = f.cam
        lv = depth_light(cam.y, surface_y, scale)
        if lv > 0.01:
            col = _mix(st[0][1], WHITE, 0.3)
            f.haze(col, clamp(0.10 * texture * (0.3 + 0.7 * lv)), tex=0.95, tex_scale=0.35, scroll=(4.0, -2.0),
                   seed=seed + 40, par=0.6)
        f.haze(_rgb((pal or f.pal).ink), clamp(0.18 * texture), tex=0.9, tex_scale=0.25, scroll=(-3.0, 1.0),
               seed=seed + 41, par=0.4)
