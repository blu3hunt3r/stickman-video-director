"""Composited scene-to-scene transitions (Saul Bass cut paper + film grammar).

    out = apply(kind, A, B, u, t=0.0, **params)

A, B: uint8 BGRA arrays (H x W x 4, any scale, same size; B is resized if not), the outgoing
and incoming scene frames. u: progress 0..1, LINEAR in time (each kind eases internally).
t: seconds since the transition started (used by kinds that animate, and to infer the
duration for motion blur when u > 0). Returns a new uint8 BGRA array (alpha 255).

Geometry params are in FRAME px of the 1080x1920 reference (scaled to the array size),
colors are RGB tuples 0..1. Every kind is deterministic and costs <= ~40 ms at 1080x1920.

Kinds (see each _k_* docstring for params):
  cut, dissolve, ink, iris, bars, shape, scroll, flatten, flash, dip, whip, tear, slash
"""
import math

import cairo
import cv2
import numpy as np

from . import bass
from .core import W, H, clamp, ease as _ease, hash01, inv_lerp, lerp, noise1, noise_grid
from .palette import PAPER, RED

INK = (0.012, 0.012, 0.014)
FIBER = (0.97, 0.955, 0.92)          # the white core of torn paper


def _e(name, u):
    if name is None or name == "linear":
        return clamp(u)
    if callable(name):
        return name(clamp(u))
    return _ease(name, u)


def _h(*a):
    return hash01(*a)


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


# ----------------------------------------------------------------------------- array helpers
def _prep(X, like=None):
    X = np.asarray(X)
    if X.dtype != np.uint8:
        X = np.clip(X, 0, 255).astype(np.uint8)
    if X.ndim == 2:
        X = cv2.cvtColor(X, cv2.COLOR_GRAY2BGRA)
    elif X.shape[2] == 3:
        X = cv2.cvtColor(X, cv2.COLOR_BGR2BGRA)
    if like is not None and X.shape[:2] != like.shape[:2]:
        X = cv2.resize(X, (like.shape[1], like.shape[0]), interpolation=cv2.INTER_AREA)
    if not X.flags.c_contiguous or not X.flags.writeable:
        X = np.ascontiguousarray(X).copy()
    return X


_CONST = {}


def _solid(shape, rgb):
    """Cached constant BGRA image."""
    key = (shape[0], shape[1], tuple(round(c, 4) for c in rgb[:3]))
    if key not in _CONST:
        if len(_CONST) > 24:
            _CONST.clear()
        a = np.empty((shape[0], shape[1], 4), np.uint8)
        a[...] = (int(round(rgb[2] * 255)), int(round(rgb[1] * 255)), int(round(rgb[0] * 255)), 255)
        _CONST[key] = a
    return _CONST[key]


def _mix(X, Y, k):
    """Uniform blend X -> Y by k (0..1)."""
    k = clamp(k)
    if k <= 0.0:
        return X.copy()
    if k >= 1.0:
        return Y.copy()
    out = cv2.addWeighted(X, 1.0 - k, Y, k, 0.0)
    out[..., 3] = 255
    return out


def _blend_mask(X, Y, m):
    """Per-pixel blend X -> Y with float32 mask m (H x W, 0..1)."""
    out = cv2.blendLinear(X, Y, (1.0 - m).astype(np.float32), m.astype(np.float32))
    out[..., 3] = 255
    return out


def _surface(arr):
    h, w = arr.shape[:2]
    return cairo.ImageSurface.create_for_data(arr, cairo.FORMAT_ARGB32, w, h, w * 4)


class _Canvas:
    """A copy of `base` wrapped as a cairo surface; ctx draws in frame px (1080x1920 space)."""

    def __init__(self, base):
        self.arr = np.ascontiguousarray(base).copy()
        self.h, self.w = self.arr.shape[:2]
        self.s = self.w / float(W)
        self.surf = _surface(self.arr)
        self.ctx = cairo.Context(self.surf)
        self.ctx.scale(self.s, self.s)
        self._keep = []

    def image(self, X, clip=None, dx=0.0, dy=0.0, rot=0.0, pivot=(W / 2.0, H / 2.0), alpha=1.0):
        """Paint image X (array, same size), moved by (dx, dy) frame px and rotated (deg)
        about pivot, through an optional clip path builder clip(ctx) in frame px (the clip is
        in DESTINATION space)."""
        c = self.ctx
        c.save()
        if clip is not None:
            c.new_path()
            clip(c)
            c.clip()
        src = _surface(X)
        self._keep.append(X)
        c.identity_matrix()
        s = self.s
        if rot:
            c.translate(pivot[0] * s + dx * s, pivot[1] * s + dy * s)
            c.rotate(math.radians(rot))
            c.translate(-pivot[0] * s, -pivot[1] * s)
            c.set_source_surface(src, 0, 0)
            c.get_source().set_filter(cairo.FILTER_BILINEAR)
        else:
            c.set_source_surface(src, round(dx * s), round(dy * s))
            c.get_source().set_filter(cairo.FILTER_FAST)
        if alpha >= 1.0:
            c.paint()
        else:
            c.paint_with_alpha(alpha)
        c.restore()

    def fill(self, build, rgb, alpha=1.0, evenodd=False):
        c = self.ctx
        c.save()
        c.new_path()
        build(c)
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD if evenodd else cairo.FILL_RULE_WINDING)
        c.set_source_rgba(rgb[0], rgb[1], rgb[2], alpha)
        c.fill()
        c.restore()

    def done(self):
        self.surf.flush()
        self.arr[..., 3] = 255
        return self.arr


def _poly(c, pts):
    if pts:
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        c.close_path()


def _dur(t, u, dur):
    if dur:
        return float(dur)
    if t > 0 and u > 0.02:
        return t / u
    return 1.0


def _motion_blur(X, axis, length):
    """Directional blur (two box passes = a triangle kernel ~`length` px long) along axis 0
    (vertical) or 1 (horizontal)."""
    k = int(round(length * 0.6))
    if k < 2:
        return X
    ks = (1, k) if axis == 0 else (k, 1)          # cv2 ksize is (width, height)
    out = cv2.blur(cv2.blur(X, ks), ks)
    out[..., 3] = 255
    return out


# ============================================================================ kinds
def _k_cut(A, B, u, t, at=0.5):
    """Hard cut at u = at."""
    return (B if u >= at else A).copy()


def _k_dissolve(A, B, u, t, ease="sine"):
    """Cross-dissolve."""
    return _mix(A, B, _e(ease, u))


_NOISE = {}


def _noise(w, h, feature, seed, detail=5.0):
    key = (w, h, round(feature, 2), seed, detail)
    if key not in _NOISE:
        if len(_NOISE) > 12:
            _NOISE.clear()
        _NOISE[key] = noise_grid(w, h, feature=feature, seed=seed, beta=1.8, detail=detail)
    return _NOISE[key]


def _k_ink(A, B, u, t, soft=0.045, spread=1.0, grain=1.0, rim=0.5, rim_color=INK, ease="inout",
           seed=11, key="A", seed_frac=0.16, drift=5.0):
    """Ink bleed (luma key): B appears first through A's darkest areas (the silhouettes),
    then the ink spreads outward from them in noisy tendrils (faster through dark areas)
    until it has soaked the frame. The pace is equalized, so the soaked area grows evenly
    with u. Flat areas (an ink field, plain paper) soak in organic blobs. spread: 0 = pure
    luma key (no outward growth) .. 1. grain: tendril noise. rim: dark ink fringe on the
    advancing edge (rim_color), only where A and B differ (no contour lace where paper
    meets paper). key: 'A' (A's darks), 'B' (the new scene's darks soak through first),
    'AB'. seed_frac: share of darkest pixels that bleed first."""
    h, w = A.shape[:2]
    k = _e(ease, u)
    if k <= 0.0:
        return A.copy()
    if k >= 1.0:
        return B.copy()
    lw, lh = min(w, 270), min(h, 480)
    sa = cv2.resize(A, (lw, lh), interpolation=cv2.INTER_AREA)
    sb = cv2.resize(B, (lw, lh), interpolation=cv2.INTER_AREA)
    T = _ink_field(sa if key != "B" else sb, sb if key == "AB" else None, seed, seed_frac, spread, grain, t, drift)
    kk = lerp(-soft, 1.0 + soft, k)
    m = np.clip((kk - T) / (2.0 * soft) + 0.5, 0.0, 1.0)
    m = m * m * (3.0 - 2.0 * m)

    def up(z):
        return cv2.resize(z, (w, h), interpolation=cv2.INTER_LINEAR)

    out = cv2.blendLinear(A, B, up(1.0 - m), up(m))
    if rim > 0:
        q = 4.0 * m * (1.0 - m)
        diff = cv2.GaussianBlur(cv2.absdiff(sa, sb)[..., :3].max(axis=2).astype(np.float32), (0, 0), 2.0)
        rr = np.clip(q * q * rim * np.minimum(diff * (1.0 / 60.0), 1.0), 0.0, 1.0).astype(np.float32)
        out = cv2.blendLinear(out, _solid(A.shape, rim_color), up(1.0 - rr), up(rr))
    out[..., 3] = 255
    return out


def _ink_field(X, Y, seed, seed_frac, spread, grain, t, drift):
    """Arrival time (0..1, equalized) of the ink at each pixel of the low-res BGRA frame X
    (and Y for key 'AB')."""
    lh, lw = X.shape[:2]

    def dark(Z):
        g = cv2.cvtColor(Z, cv2.COLOR_BGRA2GRAY).astype(np.float32)
        return 255.0 - cv2.GaussianBlur(g, (0, 0), 1.6)

    D = dark(X)
    if Y is not None:
        D = np.maximum(D, dark(Y))
    N = _noise(lw, lh, 16.0, seed, detail=3.0)
    if drift and t:
        dx = (t * drift) % lw
        N = cv2.warpAffine(N, np.float32([[1, 0, dx], [0, 1, -0.6 * dx]]), (lw, lh), borderMode=cv2.BORDER_WRAP)
    # darkness rank 0..1. Smooth, static blob noise is added BEFORE ranking so that inside
    # flat areas (a Bass ink field, plain paper) the order comes from large organic blobs,
    # not from film grain (ranking amplifies any noise: grain alone gives salt-and-pepper).
    Nb = _noise(lw, lh, 0.15 * lw, seed + 101, detail=1.6)
    Dn = np.clip(D + 26.0 * (Nb - 0.5), 0, 255).astype(np.uint8)
    r = cv2.equalizeHist(Dn).astype(np.float32) * (1.0 / 255.0)
    seedm = r >= 1.0 - seed_frac
    if spread > 0 and seedm.any():
        dist = cv2.distanceTransform((~seedm).astype(np.uint8), cv2.DIST_L2, 5)
        dn = dist * (1.0 / (float(np.percentile(dist[::2, ::2], 99.5)) + 1e-6))
        T = np.where(seedm, (1.0 - r) * (0.2 / max(seed_frac, 1e-3)),
                     0.2 + 0.8 * np.clip(spread * 0.75 * dn ** 0.8 + (1.0 - spread * 0.75) * (1.0 - r), 0, 1))
    else:
        T = 1.0 - r
    T = T + grain * 0.10 * (N - 0.5) * np.clip(0.35 + 2.5 * T, 0.0, 1.0)
    T = cv2.GaussianBlur(T.astype(np.float32), (0, 0), 0.9)          # no pixel-level islands
    T8 = np.clip(T * 255.0, 0, 255).astype(np.uint8)
    return cv2.equalizeHist(T8).astype(np.float32) * (1.0 / 255.0)


def _iris_poly(c, r, seed, n=88, edge=1.0):
    pts = []
    amp = edge * (2.0 + 0.004 * r)
    for i in range(n):
        th = 2 * math.pi * (i + 0.4 * _sn(seed, i, 1)) / n
        rr = max(0.0, r + amp * _sn(seed, i, 2))
        pts.append((c[0] + rr * math.cos(th), c[1] + rr * math.sin(th)))
    return pts


def _far(c):
    return max(math.hypot(c[0] - x, c[1] - y) for x in (0, W) for y in (0, H))


def _k_iris(A, B, u, t, center=(540.0, 960.0), r0=0.0, r1=None, mode="open", ease="inout3", edge=1.0,
            ring=0.0, ring_color=RED, fill=INK, seed=3, n=88):
    """Iris. mode 'open': B inside a circle growing r0 -> r1 over A. 'close': A inside a
    circle shrinking r1 -> r0, B outside. 'through': A irises down to `fill` by u=.5, then B
    irises open from it. center/r0/r1 in frame px (r1 default: past the far corner).
    edge: scissor-cut edge strength (0 = clean); ring > 0 adds a cut paper ring of that width
    in ring_color around the edge."""
    k = _e(ease, u)
    r1 = r1 if r1 is not None else _far(center) + ring + 12.0
    if mode == "through":
        if u < 0.5:
            inner, outer_img, r = A, None, lerp(r1, r0, _e(ease, u * 2.0))
        else:
            inner, outer_img, r = B, None, lerp(r0, r1, _e(ease, u * 2.0 - 1.0))
        base = _solid(A.shape, fill)
    elif mode == "close":
        inner, base, r = A, B, lerp(r1, r0, k)
    else:
        inner, base, r = B, A, lerp(r0, r1, k)
    cv = _Canvas(base)
    if r > 0.5:
        P = _iris_poly(center, r, seed, n, edge)
        cv.image(inner, clip=lambda c: _poly(c, P))
        if ring > 0:
            Q = _iris_poly(center, r + ring, seed + 1, n, edge * 0.8)
            cv.fill(lambda c: (_poly(c, Q), _poly(c, P[::-1])), ring_color)
    return cv.done()


def _k_bars(A, B, u, t, n=6, axis="v", color=INK, frm="alt", overlap=0.55, ease="inout3", seed=7,
            cut=1.0, sizes=None, travel="through"):
    """Bass bars. axis 'v': vertical bars sliding vertically; 'h': horizontal bars sliding
    sideways. With color (an rgb or a list of rgbs, cycled: e.g. [INK, RED, PAPER]) the bars
    slide in and cover A by u=.5, then slide on (travel='through') or back (travel='back')
    to reveal B. With color=None the bars are strips of B that slide in over A (one move).
    frm: 'alt' (alternate ends), 'start' (top/left), 'end', 'random'. sizes: relative bar
    widths (default slightly irregular)."""
    vertical = axis == "v"
    span = H if vertical else W
    slots = bass.bar_rects((0.0, 0.0, float(W), float(H)), n, "v" if vertical else "h", sizes, 0.0, seed,
                           irregular=0.35)
    rk, steps = bass.ranks(n, "random" if frm == "random" else "ltr", seed)
    ov = 3.0

    def side(i):
        if frm == "alt":
            return -1.0 if i % 2 == 0 else 1.0
        if frm == "end":
            return 1.0
        if frm == "random":
            return -1.0 if _h(seed, i, 5) < 0.5 else 1.0
        return -1.0

    def bar_poly(i):
        x0, y0, x1, y1 = slots[i]
        if vertical:
            r = (x0 - ov, -30.0, x1 + ov, H + 30.0)
        else:
            r = (-30.0, y0 - ov, W + 30.0, y1 + ov)
        return bass.cut_rect(*r, seed=seed * 31 + i, amp=1.8 * cut, seg=(40.0, 120.0)) if cut > 0 else \
            [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]

    travel_px = span + 80.0
    if color is None:
        cv = _Canvas(A)
        for i in range(n):
            p = bass.stagger(u, rk[i], steps, overlap=overlap, ease=ease)
            if p <= 0:
                continue
            off = side(i) * travel_px * (1.0 - p)
            dx, dy = (0.0, off) if vertical else (off, 0.0)
            P = [(x + dx, y + dy) for x, y in bar_poly(i)]
            cv.image(B, clip=lambda c, P=P: _poly(c, P), dx=dx, dy=dy)
        return cv.done()
    cols = color if isinstance(color, (list, tuple)) and isinstance(color[0], (list, tuple)) else [color]
    if u < 0.5:
        cv = _Canvas(A)
        for i in range(n):
            p = bass.stagger(u * 2.0, rk[i], steps, overlap=overlap, ease=ease)
            if p <= 0:
                continue
            off = side(i) * travel_px * (1.0 - p)
            dx, dy = (0.0, off) if vertical else (off, 0.0)
            P = [(x + dx, y + dy) for x, y in bar_poly(i)]
            cv.fill(lambda c, P=P: _poly(c, P), cols[i % len(cols)])
        return cv.done()
    cv = _Canvas(B)
    for i in range(n):
        p = bass.stagger(u * 2.0 - 1.0, rk[i], steps, overlap=overlap, ease=ease)
        if p >= 1:
            continue
        d = -side(i) if travel == "through" else side(i)
        off = d * travel_px * p
        dx, dy = (0.0, off) if vertical else (off, 0.0)
        P = [(x + dx, y + dy) for x, y in bar_poly(i)]
        cv.fill(lambda c, P=P: _poly(c, P), cols[i % len(cols)])
    return cv.done()


def _k_shape(A, B, u, t, path=None, ease="inout3", invert=False, edge=None, edge_width=10.0):
    """B revealed through an arbitrary growing mask: path(ctx, k) adds a cairo path in frame
    px for eased progress k (see shape_* factories: shape_circle, shape_triangle,
    shape_title, shape_spiral, shape_window). invert=True plays the shape backwards as a
    closing mask: A stays inside path(1 - k), which shrinks away over B. edge: optional rgb
    stroked along the path (a paper rim)."""
    if path is None:
        path = shape_circle()
    if u >= 1.0:
        return B.copy()
    if u <= 0.0:
        return A.copy()
    k = _e(ease, u)
    inner, base, kk = (A, B, 1.0 - k) if invert else (B, A, k)
    cv = _Canvas(base)
    cv.image(inner, clip=lambda c: path(c, kk))
    if edge is not None:
        c = cv.ctx
        c.save()
        c.new_path()
        path(c, kk)
        c.set_source_rgb(*edge[:3])
        c.set_line_width(edge_width)
        c.set_line_join(cairo.LINE_JOIN_MITER)
        c.stroke()
        c.restore()
    return cv.done()


def _k_scroll(A, B, u, t, direction="up", ease="inout3", blur=1.0, dur=None, gap=0.0, gap_color=INK):
    """Vertical continuation: the camera keeps travelling, A slides out and B follows as one
    continuous strip (direction 'up' = content moves up, B comes from below, i.e. a descent;
    'down' = an ascent; 'left'/'right' for sideways). gap: a band (frame px) of gap_color
    between the two worlds. blur: motion blur amount (1 = 180-degree shutter; duration from
    dur or t/u)."""
    h, w = A.shape[:2]
    vertical = direction in ("up", "down")
    L = h if vertical else w
    s = w / float(W)
    g = int(round(gap * s))
    k = _e(ease, u)
    off = int(round(k * (L + g)))
    out = np.empty_like(A)
    # strip = [A, gap, B] along the travel; window starts at `off`
    if direction in ("up", "left"):
        segs = [(A, 0), (None, L), (B, L + g)]
    else:
        segs = [(B, 0), (None, L), (A, L + g)]
        off = (L + g) - off
    gc = _solid(A.shape, gap_color)
    for X, s0 in segs:
        n = L if X is not None else g
        a, b = max(off, s0), min(off + L, s0 + n)
        if b <= a:
            continue
        src = X if X is not None else gc
        if vertical:
            out[a - off:b - off] = src[a - s0:b - s0]
        else:
            out[:, a - off:b - off] = src[:, a - s0:b - s0]
    if blur > 0:
        d = _dur(t, u, dur)
        du = 1.0 / (d * 24.0)
        v = abs(_e(ease, min(1.0, u + du / 2)) - _e(ease, max(0.0, u - du / 2))) * (L + g)
        out = _motion_blur(out, 0 if vertical else 1, blur * 0.5 * v)
    out[..., 3] = 255
    return out


_FLAT_LUT = {}


def _flat_lut(tones, thr, soft):
    key = (tuple(tuple(round(c, 4) for c in x[:3]) for x in tones), tuple(int(v) for v in thr), soft)
    if key not in _FLAT_LUT:
        if len(_FLAT_LUT) > 512:
            _FLAT_LUT.clear()
        v = np.arange(256, dtype=np.float32)
        col = np.zeros((256, 3), np.float32)
        col[:] = tones[0][:3]
        for j, th in enumerate(thr):
            s = np.clip((v - (th - soft)) / (2.0 * soft), 0, 1)
            s = s * s * (3 - 2 * s)
            col += s[:, None] * (np.array(tones[j + 1][:3], np.float32) - np.array(tones[j][:3], np.float32))
        lut = np.clip(col[:, ::-1] * 255.0, 0, 255).astype(np.uint8).reshape(256, 1, 3)
        _FLAT_LUT[key] = lut
    return _FLAT_LUT[key]


def otsu_thresholds(hist, classes=3, bins=64):
    """Multi-level Otsu on a 256-bin histogram: the classes-1 thresholds (0..255) that
    maximize the between-class variance."""
    hb = hist.reshape(bins, -1).sum(1).astype(np.float64)
    p = hb / max(hb.sum(), 1e-9)
    i = np.arange(bins, dtype=np.float64)
    P = np.concatenate([[0.0], np.cumsum(p)])
    S = np.concatenate([[0.0], np.cumsum(p * i)])

    def term(a, b):          # class over bins [a, b)
        w = P[b] - P[a]
        m = S[b] - S[a]
        return np.where(w > 1e-9, m * m / np.maximum(w, 1e-9), 0.0)

    step = 256 // bins
    if classes <= 2:
        t = np.arange(1, bins)
        v = term(0, t) + term(t, bins)
        return [int(t[int(np.argmax(v))]) * step]
    t1, t2 = np.meshgrid(np.arange(1, bins - 1), np.arange(2, bins), indexing="ij")
    ok = t2 > t1
    v = term(0, t1) + term(t1, t2) + term(t2, bins)
    v = np.where(ok, v, -1.0)
    a, b = np.unravel_index(int(np.argmax(v)), v.shape)
    return [int(t1[a, b]) * step, int(t2[a, b]) * step]


def flatten_image(X, tones=None, levels=3, thresholds="auto", keep_red=True, soft=5, simplify=2, red=RED):
    """Bass flatten of one frame: luminance -> 2 or 3 flat inks (tones, dark -> light;
    levels=2 uses the darkest and lightest) with smooth simplified cut shapes (median +
    blur at 1/4 res, re-thresholded at full res); saturated reds become flat RED.
    thresholds: 'auto' (multi-level Otsu over the non-red pixels) or 0..255 values.
    Returns uint8 BGRA."""
    tones = list(tones or [INK, (0.45, 0.45, 0.44), PAPER])
    if levels == 2 and len(tones) == 3:
        tones = [tones[0], tones[2]]
    tones = tones[:levels]
    h, w = X.shape[:2]
    q = max(1, int(round(2 * w / float(W))))          # work at ~540 px wide
    lw, lh = max(8, w // q), max(8, h // q)
    sm = cv2.resize(X, (lw, lh), interpolation=cv2.INTER_AREA) if q > 1 else X
    g = cv2.cvtColor(sm, cv2.COLOR_BGRA2GRAY)
    if simplify > 0:
        g = cv2.medianBlur(g, 5)
        g = cv2.GaussianBlur(g, (0, 0), 0.9 * simplify)
    rm = None
    if keep_red:
        b, gg, r = [sm[..., i].astype(np.int16) for i in range(3)]
        rm = (r > 90) & (r > gg * 2.2) & (r > b * 2.2)
        if not rm.any():
            rm = None
    if thresholds == "auto":
        mask = None if rm is None else (~rm).astype(np.uint8)
        hist = cv2.calcHist([g], [0], mask, [256], [0, 256]).ravel()
        thr = otsu_thresholds(hist, len(tones))
        if len(tones) == 3:
            tot = max(hist.sum(), 1.0)
            if hist[thr[0]:thr[1]].sum() / tot < 0.05:      # the mid class is only edges: 2 inks
                tones = [tones[0], tones[2]]
                thr = otsu_thresholds(hist, 2)
    else:
        thr = [int(v) for v in thresholds][:len(tones) - 1]
    up = cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)
    out = cv2.cvtColor(cv2.LUT(cv2.merge([up, up, up]), _flat_lut(tones, thr, soft)), cv2.COLOR_BGR2BGRA)
    if rm is not None:
        rf = cv2.GaussianBlur(rm.astype(np.float32), (0, 0), 0.6)
        rf = np.clip((rf - 0.35) * 3.0, 0, 1)
        RM = cv2.resize(rf, (w, h), interpolation=cv2.INTER_LINEAR)
        out = cv2.blendLinear(out, _solid(X.shape, red), 1.0 - RM, RM)
    out[..., 3] = 255
    return out


def _k_flatten(A, B, u, t, tones=None, pal=None, levels=(3, 2), thresholds="auto", hold=0.1, blend=0.0,
               keep_red=True, soft=5):
    """Flatten: A snaps through posterized stages (levels, e.g. 3 then 2 flat tones: Bass
    cut paper) after holding full tone for `hold`; hard swap at u=.5 to B's flattest
    version, which steps back up through the levels to full tone. tones: 2-3 rgb (dark ->
    light) or pal: a palette (or name) for its Bass poster tones. blend > 0 crossfades
    that fraction of each step (0 = crisp graphic steps)."""
    if tones is None and pal is not None:
        tones, _ = bass.poster_tones(pal)
    X, v = (A, u) if u < 0.5 else (B, 1.0 - u)
    if v < hold:
        return X.copy()
    n = len(levels)
    x = (v - hold) / max(0.5 - hold, 1e-6) * n
    j = min(n - 1, int(x))
    F = flatten_image(X, tones, levels[j], thresholds, keep_red, soft)
    if blend > 0:
        f = x - j
        if f < blend:
            prev = X if j == 0 else flatten_image(X, tones, levels[j - 1], thresholds, keep_red, soft)
            return _mix(prev, F, _e("inout", f / blend))
    return F


def _k_flash(A, B, u, t, color=(1.0, 1.0, 1.0), at=0.5, attack=0.16, decay=0.4, strength=1.0):
    """Flash: a fast build to `color` peaking at u=at (where A swaps to B), then a decay."""
    if u < at:
        X = A
        f = _e("in3", inv_lerp(at - attack, at, u))
    else:
        X = B
        f = 1.0 - _e("out3", inv_lerp(at, at + decay, u))
    return _mix(X, _solid(A.shape, color), strength * f)


def _k_dip(A, B, u, t, color=INK, hold=0.12, ease="inout"):
    """Dip to color and back (hold = fraction of the time spent fully in color)."""
    h0, h1 = 0.5 - hold / 2.0, 0.5 + hold / 2.0
    C = _solid(A.shape, color)
    if u < h0:
        return _mix(A, C, _e(ease, u / h0))
    if u <= h1:
        return C.copy()
    return _mix(C, B, _e(ease, (u - h1) / (1.0 - h1)))


def _k_whip(A, B, u, t, direction="left", ease="inout5", blur=1.0, dur=None):
    """Whip pan: a fast directional move with heavy motion blur that peaks mid-move. A leaves
    toward `direction`, B arrives from the opposite side."""
    m = {"left": "left", "right": "right", "up": "up", "down": "down"}[direction]
    d = _dur(t, u, dur if dur else (0.5 if not (t > 0 and u > 0.02) else None))
    return _k_scroll(A, B, u, t, direction=m, ease=ease, blur=blur * 1.6, dur=d)


def _tear_line(seed, amp, n=72, length=W, rough=1.0):
    """A torn edge as offsets along a line: fractal wiggle + small sharp tears (fixed)."""
    xs, ys = [], []
    x = -60.0
    k = 0
    while x < length + 60:
        xs.append(x)
        y = amp * (0.6 * noise1(x / 260.0, seed) + 0.3 * noise1(x / 80.0, seed + 1)
                   + 0.14 * noise1(x / 24.0, seed + 2) + rough * 0.2 * _sn(seed, k, 3))
        ys.append(y)
        x += (length + 120) / n * (0.5 + _h(seed, k, 4))
        k += 1
    return xs, ys


def _k_tear(A, B, u, t, direction="down", mode="wipe", amp=46.0, fiber=1.0, fiber_color=FIBER,
            shadow=0.35, ease="inout3", seed=5, tilt=7.0):
    """Paper tear. mode 'wipe': a jagged torn edge travels across the frame (direction
    'down' = from the top; 'up', 'left', 'right'); A is torn away behind it showing B, its
    torn edge shows the white paper core (fiber, fiber_color) and casts a soft shadow on B.
    mode 'rip': A rips in two along a vertical tear and the halves are pulled apart."""
    k = _e(ease, u)
    if mode == "rip":
        return _tear_rip(A, B, u, ease, amp, fiber, fiber_color, shadow, seed)
    horiz = direction in ("down", "up")
    length = W if horiz else H
    span = H if horiz else W
    xs, ys = _tear_line(seed, amp, 120 if horiz else 200, length)
    margin = amp * 1.25 + abs(tilt) * length / 200.0 + 40.0
    pos = lerp(-margin, span + margin, k)
    if direction in ("up", "left"):
        pos = span - pos

    def P(i, off=0.0):
        x = xs[i]
        y = pos + ys[i] + tilt * (x - length / 2) / 100.0 + off
        return (x, y) if horiz else (y, x)

    keep_after = direction in ("down", "right")       # A remains on the far side of the edge
    far = (span + 4000.0) if keep_after else -4000.0
    sgn = 1.0 if keep_after else -1.0
    n = len(xs)
    edge = [P(i) for i in range(n)]

    def region(c, off=0.0):
        pts = [P(i, off) for i in range(n)]
        if horiz:
            pts += [(xs[-1], far), (xs[0], far)]
        else:
            pts += [(far, xs[-1]), (far, xs[0])]
        _poly(c, pts)

    cv = _Canvas(B)
    if shadow > 0:
        for j, (off, a) in enumerate(((-26.0, 0.10), (-15.0, 0.14), (-7.0, 0.2))):
            cv.fill(lambda c, off=off: region(c, sgn * off), (0, 0, 0), shadow * a)
    cv.image(A, clip=lambda c: region(c))
    if fiber > 0:
        inner = []
        for i in range(n):
            wfib = fiber * (3.0 + 9.0 * _h(seed, i, 9) ** 2)
            x, y = P(i, sgn * wfib)
            inner.append((x, y))
        cv.fill(lambda c: _poly(c, edge + inner[::-1]), fiber_color)
    return cv.done()


def _tear_rip(A, B, u, ease, amp, fiber, fiber_color, shadow, seed, tear_end=0.3):
    """The rip propagates down the sheet (u 0..tear_end), then the halves are pulled apart."""
    ys, xs = _tear_line(seed, amp * 0.8, 190, H)       # x offsets along y
    n = len(ys)
    front = -40.0 + (H + 80.0) * _e("out3", u / tear_end)
    sep = _e(ease, inv_lerp(tear_end * 0.85, 1.0, u)) * (W / 2.0 + amp + 60.0)

    def edge(off):
        return [(W / 2.0 + xs[i] + off, ys[i]) for i in range(n)]

    if sep <= 0.0:
        cv = _Canvas(A)
        if fiber > 0 and front > -40.0:
            vis = [i for i in range(n) if ys[i] <= front]
            if len(vis) >= 2:
                e1 = [(W / 2.0 + xs[i], ys[i]) for i in vis]
                e2 = [(W / 2.0 + xs[i] + fiber * (2.0 + 5.0 * _h(seed, i, 9) ** 2), ys[i]) for i in vis]
                cv.fill(lambda c: _poly(c, e1 + e2[::-1]), fiber_color)
        return cv.done()
    cv = _Canvas(B)
    for sgn in (-1.0, 1.0):
        dx = sgn * sep
        e = edge(0.0)
        far = -4000.0 if sgn < 0 else W + 4000.0
        reg = e + [(far, ys[-1]), (far, ys[0])]
        moved = [(x + dx, y) for x, y in reg]
        if shadow > 0:
            for off, a in ((22.0, 0.10), (12.0, 0.14), (5.0, 0.2)):
                sh = [(x + dx - sgn * off, y) for x, y in reg]
                cv.fill(lambda c, sh=sh: _poly(c, sh), (0, 0, 0), shadow * a)
        cv.image(A, clip=lambda c, m=moved: _poly(c, m), dx=dx)
        if fiber > 0:
            e1 = [(x + dx, y) for x, y in e]
            e2 = [(x + dx + sgn * fiber * (3.0 + 9.0 * _h(seed, i, 9 + (sgn > 0)) ** 2), y) for i, (x, y) in enumerate(e)]
            cv.fill(lambda c, a=e1, b=e2: _poly(c, a + b[::-1]), fiber_color)
    return cv.done()


def _k_slash(A, B, u, t, angle=-58.0, center=(540.0, 960.0), color=RED, width=14.0, cut_end=0.2,
             crack=0.42, gap=46.0, ease="in3", seed=0):
    """Knife slash: a red sliver cuts diagonally across A (u 0..cut_end), the cut cracks
    open by `gap` px showing B (..crack, with overshoot), then the two halves slide apart
    along the cut and off the frame (ease) to reveal B. The red cut edges stay on the paper
    halves. angle = direction of the cut (deg), through `center`. color=None: no red."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    nrm = (-d[1], d[0])
    Lh = math.hypot(W, H)
    p0 = (center[0] - d[0] * Lh * 0.6, center[1] - d[1] * Lh * 0.6)
    p1 = (center[0] + d[0] * Lh * 0.6, center[1] + d[1] * Lh * 0.6)
    ks = clamp(u / max(cut_end, 1e-6))
    kc = bass.snap(u, cut_end, max(crack - cut_end, 1e-6), 0.0, 1.0, "outback")
    km = _e(ease, inv_lerp(crack, 1.0, u))
    BIG = 6000.0

    def half(sg):
        q0 = (p0[0] - d[0] * BIG, p0[1] - d[1] * BIG)
        q1 = (p1[0] + d[0] * BIG, p1[1] + d[1] * BIG)
        return [q0, q1, (q1[0] + nrm[0] * sg * BIG, q1[1] + nrm[1] * sg * BIG),
                (q0[0] + nrm[0] * sg * BIG, q0[1] + nrm[1] * sg * BIG)]

    if u < cut_end:
        cv = _Canvas(A)
        if color is not None and ks > 0:
            sl = bass.slash_pts(p0, p1, width * 2.4, u=_e("out3", ks), tail=0.0, seed=seed)
            cv.fill(lambda c: _poly(c, sl), color)
        return cv.done()
    cv = _Canvas(B)
    along = km * Lh * 1.1
    for sg in (-1.0, 1.0):
        dx = sg * d[0] * along + nrm[0] * sg * gap * kc * 0.5
        dy = sg * d[1] * along + nrm[1] * sg * gap * kc * 0.5
        hp = [(x + dx, y + dy) for x, y in half(sg)]
        cv.image(A, clip=lambda c, hp=hp: _poly(c, hp), dx=dx, dy=dy)
        if color is not None:
            w = width * 0.5
            band = [(p0[0] - d[0] * BIG + dx, p0[1] - d[1] * BIG + dy), (p1[0] + d[0] * BIG + dx, p1[1] + d[1] * BIG + dy),
                    (p1[0] + d[0] * BIG + dx + nrm[0] * sg * w, p1[1] + d[1] * BIG + dy + nrm[1] * sg * w),
                    (p0[0] - d[0] * BIG + dx + nrm[0] * sg * w, p0[1] - d[1] * BIG + dy + nrm[1] * sg * w)]
            rect = [(dx, dy), (W + dx, dy), (W + dx, H + dy), (dx, H + dy)]
            c = cv.ctx
            c.save()
            c.new_path()
            _poly(c, rect)
            c.clip()
            c.new_path()
            _poly(c, band)
            c.set_source_rgb(*color[:3])
            c.fill()
            c.restore()
    return cv.done()


KINDS = {
    "cut": _k_cut, "dissolve": _k_dissolve, "ink": _k_ink, "iris": _k_iris, "bars": _k_bars,
    "shape": _k_shape, "scroll": _k_scroll, "flatten": _k_flatten, "flash": _k_flash, "dip": _k_dip,
    "whip": _k_whip, "tear": _k_tear, "slash": _k_slash,
}


def apply(kind, A, B, u, t=0.0, **params):
    """Composite the transition `kind` between frames A (outgoing) and B (incoming) at
    progress u (0..1, linear). Returns uint8 BGRA (alpha 255). See the module docstring."""
    if kind not in KINDS:
        raise ValueError("unknown transition %r (have: %s)" % (kind, ", ".join(sorted(KINDS))))
    A = _prep(A)
    B = _prep(B, like=A)
    u = clamp(float(u))
    return KINDS[kind](A, B, u, float(t), **params)


# ============================================================================ shape factories
def shape_circle(center=(540.0, 960.0), r0=0.0, r1=None, seed=3, n=88):
    """Path builder for kind='shape': a cut circle growing r0 -> r1."""
    r1 = r1 if r1 is not None else _far(center) + 10.0

    def build(c, k):
        r = lerp(r0, r1, k)
        if r > 0.5:
            _poly(c, _iris_poly(center, r, seed, n))
    return build


def shape_triangle(center=(540.0, 1000.0), s0=0.0, s1=4200.0, rot=0.0, seed=2):
    """Path builder: RED's hood triangle (apex up) growing from center."""
    def build(c, k):
        s = lerp(s0, s1, k)
        if s > 0.5:
            pts = [(center[0], center[1] - s * 0.62), (center[0] + s * 0.42, center[1] + s * 0.38),
                   (center[0] - s * 0.42, center[1] + s * 0.38)]
            _poly(c, bass.xform(pts, 0, 0, rot * k, 1.0, None, center))
    return build


def title_anchor(T):
    """(anchor, radius): the point deepest inside the Title's letters (title space) and its
    distance to the nearest edge, used to zoom through a letter until it fills the frame.
    Computed once per Title (stored on it)."""
    cached = getattr(T, "_anchor", None)
    if cached is None:
        q = 160.0 / max(T.height, 1.0)
        x0, y0, x1, y1 = T.bbox
        w, h = int((x1 - x0) * q) + 24, int((y1 - y0) * q) + 24
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, w)
        buf = np.zeros((h, stride), np.uint8)
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_A8, w, h, stride)
        c = cairo.Context(surf)
        c.translate(12 - x0 * q, 12 - y0 * q)
        c.scale(q, q)
        for g in T:
            for poly in g.polys:
                _poly(c, poly)
        c.fill()
        surf.flush()
        m = (buf[:, :w] > 127).astype(np.uint8)
        dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)
        iy, ix = np.unravel_index(int(np.argmax(dist)), dist.shape)
        anchor = ((ix - 12) / q + x0, (iy - 12) / q + y0)
        cached = (anchor, float(dist[iy, ix]) / q)
        try:
            T._anchor = cached
        except AttributeError:
            pass
    return cached


def shape_title(T, center=(540.0, 960.0), s1=None, anchor=None, pop=0.22, target=(W / 2.0, H / 2.0)):
    """Path builder: B seen through a Title's letters (placed at `center`). They pop in
    (first `pop` of the move), then zoom exponentially into the thickest stroke (or
    `anchor`, title space) while it drifts to `target`, until the letter fills the frame."""
    a, rin = title_anchor(T)
    if anchor is not None:
        a = anchor
    far = max(math.hypot(target[0] - x, target[1] - y) for x in (0, W) for y in (0, H))
    s1 = s1 if s1 is not None else 1.15 * far / max(rin, 1.0)

    def build(c, k):
        if pop > 0 and k < pop:
            s = max(1e-3, bass.pop(k, 0.0, pop))
            P = (center[0] + a[0], center[1] + a[1])
        else:
            z = (k - pop) / max(1.0 - pop, 1e-6) if pop > 0 else k
            s = s1 ** z
            m = _e("inout3", z)
            P = (lerp(center[0] + a[0], target[0], m), lerp(center[1] + a[1], target[1], m))
        c.save()
        c.translate(P[0], P[1])
        c.scale(s, s)
        c.translate(-a[0], -a[1])
        for g in T:
            for poly in g.polys:
                _poly(c, poly)
        c.restore()
    return build


def shape_spiral(center=(540.0, 960.0), turns=3.0, arms=2, seed=4, spin=-200.0):
    """Path builder: a Vertigo spiral whose bands widen until they cover the frame."""
    R = _far(center) + 40.0

    def build(c, k):
        if k <= 0:
            return
        pitch = R / turns / arms
        w = max(1.0, lerp(0.14, 1.3, k) * pitch)
        bass.spiral_path(c, center, r0=0.0, r1=R, turns=turns, width=w, arms=arms, rot=spin * k,
                         taper=(0.35, 1.0), extent=min(1.0, 0.35 + 1.3 * k), seed=seed)
        if k > 0.82:
            _poly(c, _iris_poly(center, R * (k - 0.82) / 0.18 * 1.1, seed, 64))
    return build


def shape_window(rect0, rect1=(-40.0, -40.0, W + 40.0, H + 40.0), seed=6):
    """Path builder: a cut-paper rectangle (a window) growing from rect0 to rect1."""
    def build(c, k):
        r = tuple(lerp(a, b, k) for a, b in zip(rect0, rect1))
        _poly(c, bass.cut_rect(*r, seed=seed, amp=2.0))
    return build

def shape_binocular(center=(540.0, 960.0), r=300.0, sep=330.0, r_big=None, seed=0):
    """Path builder: a binocular view (bass.binocular_pts) scaled from r_big (k=1, past the
    frame) down to (r, sep) at k=0. Use with kind='shape', invert=True: the outgoing scene
    shrinks into the binocular lenses of the incoming scene's point of view."""
    r_big = r_big if r_big is not None else 2.4 * H

    def build(c, k):
        s = lerp(1.0, r_big / r, k)
        for p in bass.binocular_pts(center, r * s, sep * s, seed):
            _poly(c, p)
    return build
