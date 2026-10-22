"""Path and fill helpers on a cairo context (world coordinates of the current camera).

Silhouette art is built from FILLED shapes, not strokes: polygons, smooth closed curves
(Catmull-Rom), tapered capsules (limbs, branches, legs), plus Saul Bass "cut paper" edges.
"""
import math

import cairo

from .core import hash01, lerp


# ----------------------------------------------------------------------------- color
def rgba(ctx, rgb, a=1.0):
    if len(rgb) == 4:
        ctx.set_source_rgba(*rgb)
    else:
        ctx.set_source_rgba(rgb[0], rgb[1], rgb[2], a)


def fill(ctx, rgb, a=1.0, preserve=False):
    rgba(ctx, rgb, a)
    ctx.fill_preserve() if preserve else ctx.fill()


def stroke(ctx, rgb, width, a=1.0, cap=cairo.LINE_CAP_ROUND, preserve=False):
    rgba(ctx, rgb, a)
    ctx.set_line_width(width)
    ctx.set_line_cap(cap)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve() if preserve else ctx.stroke()


# ----------------------------------------------------------------------------- paths
def poly(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def smooth(ctx, pts, close=True, tension=0.5):
    """Catmull-Rom curve through pts (as cubic beziers). close=True for a closed outline."""
    n = len(pts)
    if n < 3:
        return poly(ctx, pts, close)
    k = tension / 3.0        # tension 0.5 -> standard Catmull-Rom (control = (p2 - p0) / 6)

    def P(i):
        if close:
            return pts[i % n]
        return pts[min(max(i, 0), n - 1)]

    ctx.move_to(*pts[0])
    last = n if close else n - 1
    for i in range(last):
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if close:
        ctx.close_path()


def circle(ctx, c, r):
    ctx.new_sub_path()
    ctx.arc(c[0], c[1], max(r, 0.01), 0, 2 * math.pi)
    ctx.close_path()


def ellipse(ctx, c, rx, ry, angle=0.0):
    ctx.save()
    ctx.translate(c[0], c[1])
    ctx.rotate(math.radians(angle))
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.close_path()
    ctx.restore()


def rect(ctx, x0, y0, x1, y1):
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)


def capsule(ctx, a, b, ra, rb):
    """Tapered capsule from point a (radius ra) to b (radius rb): the convex hull of two
    circles. The basic shape of every limb, branch, leg and tentacle."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d < 1e-6 or d <= abs(ra - rb):
        if ra >= rb:
            circle(ctx, a, ra)
        else:
            circle(ctx, b, rb)
        return
    ang = math.atan2(dy, dx)
    # angle of the tangent points relative to the axis
    s = (ra - rb) / d
    s = max(-1.0, min(1.0, s))
    phi = math.acos(s)
    ctx.new_sub_path()
    ctx.arc(a[0], a[1], max(ra, 0.01), ang + phi, ang - phi + 2 * math.pi)
    ctx.arc(b[0], b[1], max(rb, 0.01), ang - phi, ang + phi)
    ctx.close_path()


def chain(ctx, pts, radii):
    """Union of capsules along a polyline with per-point radii (tails, tentacles, ropes)."""
    for i in range(len(pts) - 1):
        capsule(ctx, pts[i], pts[i + 1], radii[i], radii[i + 1])


def ribbon(pts, widths):
    """Closed outline (list of points) of a variable-width ribbon along a polyline."""
    n = len(pts)
    left, right = [], []
    for i in range(n):
        p = pts[i]
        q0 = pts[max(i - 1, 0)]
        q1 = pts[min(i + 1, n - 1)]
        tx, ty = q1[0] - q0[0], q1[1] - q0[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        w = widths[i] * 0.5
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    return left + right[::-1]


# ----------------------------------------------------------------------------- shapes as point lists
def circle_pts(c, r, n=48, start=0.0):
    return [(c[0] + r * math.cos(start + 2 * math.pi * i / n), c[1] + r * math.sin(start + 2 * math.pi * i / n))
            for i in range(n)]


def ellipse_pts(c, rx, ry, n=48, angle=0.0):
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    out = []
    for i in range(n):
        th = 2 * math.pi * i / n
        x, y = rx * math.cos(th), ry * math.sin(th)
        out.append((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca))
    return out


def transform_pts(pts, origin=(0, 0), angle=0.0, scale=1.0, offset=(0, 0)):
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    out = []
    for x, y in pts:
        x, y = (x - origin[0]) * scale, (y - origin[1]) * scale
        out.append((origin[0] + offset[0] + x * ca - y * sa, origin[1] + offset[1] + x * sa + y * ca))
    return out


# ----------------------------------------------------------------------------- Saul Bass cut paper
def cut_paper(pts, seed=0, amp=2.2, seg=(26.0, 70.0), close=True):
    """Hand-cut paper edge: re-sample every edge into straight scissor cuts of random length
    and nudge each vertex by up to `amp` px. Edges stay straight between cuts (paper, not
    wobble). Deterministic for a given seed, so a shape keeps its edge from frame to frame."""
    n = len(pts)
    out = []
    edges = n if close else n - 1
    k = 0
    for i in range(edges):
        a, b = pts[i], pts[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        pos = 0.0
        while pos < L:
            u = pos / L if L > 0 else 0.0
            x, y = lerp(a[0], b[0], u), lerp(a[1], b[1], u)
            jx = (hash01(seed, k, 1) * 2 - 1) * amp
            jy = (hash01(seed, k, 2) * 2 - 1) * amp
            out.append((x + jx, y + jy))
            k += 1
            pos += seg[0] + (seg[1] - seg[0]) * hash01(seed, k, 3)
    if not close:
        out.append(pts[-1])
    return out


def cut_circle(c, r, seed=0, amp=None, n=None):
    """A circle cut out of paper with scissors: a slightly irregular polygon."""
    n = n or max(14, int(2 * math.pi * r / 34))
    amp = amp if amp is not None else min(3.0, 0.02 * r + 0.8)
    pts = []
    for i in range(n):
        th = 2 * math.pi * (i + 0.35 * (hash01(seed, i) - 0.5)) / n
        rr = r + (hash01(seed, i, 9) * 2 - 1) * amp
        pts.append((c[0] + rr * math.cos(th), c[1] + rr * math.sin(th)))
    return pts


def flatten_path(ctx):
    """Current cairo path as a list of closed polylines (for roughening text/curves)."""
    out, cur = [], []
    for kind, pts in ctx.copy_path_flat():
        if kind == cairo.PATH_MOVE_TO:
            if cur:
                out.append(cur)
            cur = [pts]
        elif kind == cairo.PATH_LINE_TO:
            cur.append(pts)
        elif kind == cairo.PATH_CLOSE_PATH:
            if cur:
                out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


# ----------------------------------------------------------------------------- gradients
def linear(ctx, p0, p1, stops):
    """Set a linear gradient source. stops: [(offset, rgb, alpha), ...]."""
    g = cairo.LinearGradient(p0[0], p0[1], p1[0], p1[1])
    for o, c, a in stops:
        g.add_color_stop_rgba(o, c[0], c[1], c[2], a)
    ctx.set_source(g)
    return g


def radial(ctx, c, r0, r1, stops, c1=None):
    c1 = c1 or c
    g = cairo.RadialGradient(c[0], c[1], r0, c1[0], c1[1], r1)
    for o, col, a in stops:
        g.add_color_stop_rgba(o, col[0], col[1], col[2], a)
    ctx.set_source(g)
    return g


def glow_disc(ctx, c, r, rgb, a=1.0, core=0.0):
    """Soft radial light blob (use on an additive/emissive context)."""
    radial(ctx, c, r * core, r, [(0, rgb, a), (0.35, rgb, a * 0.45), (1, rgb, 0.0)])
    ctx.arc(c[0], c[1], r, 0, 2 * math.pi)
    ctx.fill()


def resample(pts, n, closed=True):
    """Resample a polyline/polygon to n points evenly spaced by arc length (for morphing
    two outlines that were drawn with different vertex counts)."""
    P = list(pts) + ([pts[0]] if closed else [])
    seg = [math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1)]
    total = sum(seg) or 1.0
    out = []
    step = total / (n if closed else max(n - 1, 1))
    i, acc = 0, 0.0
    for k in range(n):
        target = k * step
        while i < len(seg) - 1 and acc + seg[i] < target:
            acc += seg[i]
            i += 1
        u = (target - acc) / seg[i] if seg[i] > 0 else 0.0
        u = max(0.0, min(1.0, u))
        out.append((P[i][0] + (P[i + 1][0] - P[i][0]) * u, P[i][1] + (P[i + 1][1] - P[i][1]) * u))
    return out


def morph(a, b, t, n=None):
    """Blend two outlines (resampled to the same count)."""
    n = n or max(len(a), len(b))
    if len(a) != n:
        a = resample(a, n)
    if len(b) != n:
        b = resample(b, n)
    return [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) for (x0, y0), (x1, y1) in zip(a, b)]
