"""Drawing primitives. All coordinates are world units under the frame's camera.

Every helper takes the Frame `f` first. Widths `w` are on-screen pixels at zoom 1.
`glow` (0..n) additionally paints the shape into the emissive glow layer, which is
blurred and added at finish() - use it for light sources and accent props only.
"""
import math

import cairo

from .core import WHITE


def _src(ctx, color, alpha):
    ctx.set_source_rgba(color[0], color[1], color[2], alpha)


def _path(ctx, pts, closed=False):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if closed:
        ctx.close_path()


def _both(f, glow):
    return [(f.ctx, 1.0)] + ([(f.g, glow)] if glow > 0 else [])


def stroke(f, pts, w=4.0, color=WHITE, alpha=1.0, closed=False, glow=0.0, dash=None, glow_w=None):
    """Polyline / polygon outline."""
    if len(pts) < 2 or alpha <= 0:
        return
    for ctx, k in _both(f, glow):
        _path(ctx, pts, closed)
        ww = f.lw(w if ctx is f.ctx else (glow_w or w * 2.2))
        ctx.set_line_width(ww)
        if dash and ctx is f.ctx:
            ctx.set_dash([d * ww / max(w, 1e-6) * 1.0 for d in dash])
        _src(ctx, color, min(1.0, alpha * k))
        ctx.stroke()
        if dash and ctx is f.ctx:
            ctx.set_dash([])


def line(f, a, b, w=4.0, color=WHITE, alpha=1.0, glow=0.0, dash=None):
    stroke(f, [a, b], w, color, alpha, glow=glow, dash=dash)


def fill(f, pts, color=WHITE, alpha=1.0, glow=0.0):
    """Filled polygon (use for accent props: red umbrella canopy, flame, lit window)."""
    if len(pts) < 3 or alpha <= 0:
        return
    for ctx, k in _both(f, glow):
        _path(ctx, pts, True)
        _src(ctx, color, min(1.0, alpha * k))
        ctx.fill()


def circle(f, c, r, w=4.0, color=WHITE, alpha=1.0, fill_it=False, glow=0.0):
    if r <= 0 or alpha <= 0:
        return
    for ctx, k in _both(f, glow):
        ctx.new_sub_path()
        ctx.arc(c[0], c[1], r, 0, 2 * math.pi)
        _src(ctx, color, min(1.0, alpha * k))
        if fill_it:
            ctx.fill()
        else:
            ctx.set_line_width(f.lw(w if ctx is f.ctx else w * 2.2))
            ctx.stroke()


def arc(f, c, r, a0, a1, w=4.0, color=WHITE, alpha=1.0, glow=0.0):
    """Arc from a0 to a1 degrees (0 = +x, 90 = down)."""
    if alpha <= 0:
        return
    for ctx, k in _both(f, glow):
        ctx.new_sub_path()
        ctx.arc(c[0], c[1], r, math.radians(a0), math.radians(a1))
        ctx.set_line_width(f.lw(w if ctx is f.ctx else w * 2.2))
        _src(ctx, color, min(1.0, alpha * k))
        ctx.stroke()


def ellipse(f, c, rx, ry, angle=0.0, w=4.0, color=WHITE, alpha=1.0, fill_it=False, glow=0.0):
    if rx <= 0 or ry <= 0 or alpha <= 0:
        return
    for ctx, k in _both(f, glow):
        ctx.save()
        ctx.translate(*c)
        ctx.rotate(math.radians(angle))
        ctx.scale(rx, ry)
        ctx.new_sub_path()
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        _src(ctx, color, min(1.0, alpha * k))
        if fill_it:
            ctx.fill()
        else:
            ctx.set_line_width(f.lw(w if ctx is f.ctx else w * 2.2))
            ctx.stroke()


def rect(f, x, y, w_, h_, w=4.0, color=WHITE, alpha=1.0, fill_it=False, radius=0.0, glow=0.0, angle=0.0):
    """Axis-aligned (or rotated about its center) rectangle, optional rounded corners."""
    if alpha <= 0:
        return
    for ctx, k in _both(f, glow):
        ctx.save()
        if angle:
            ctx.translate(x + w_ / 2, y + h_ / 2)
            ctx.rotate(math.radians(angle))
            ctx.translate(-(x + w_ / 2), -(y + h_ / 2))
        if radius > 0:
            r = min(radius, w_ / 2, h_ / 2)
            ctx.new_sub_path()
            ctx.arc(x + w_ - r, y + r, r, -math.pi / 2, 0)
            ctx.arc(x + w_ - r, y + h_ - r, r, 0, math.pi / 2)
            ctx.arc(x + r, y + h_ - r, r, math.pi / 2, math.pi)
            ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
            ctx.close_path()
        else:
            ctx.rectangle(x, y, w_, h_)
        ctx.restore()
        _src(ctx, color, min(1.0, alpha * k))
        if fill_it:
            ctx.fill()
        else:
            ctx.set_line_width(f.lw(w if ctx is f.ctx else w * 2.2))
            ctx.stroke()


def bezier(f, p0, p1, p2, p3, w=4.0, color=WHITE, alpha=1.0, glow=0.0):
    if alpha <= 0:
        return
    for ctx, k in _both(f, glow):
        ctx.move_to(*p0)
        ctx.curve_to(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
        ctx.set_line_width(f.lw(w if ctx is f.ctx else w * 2.2))
        _src(ctx, color, min(1.0, alpha * k))
        ctx.stroke()


def bezier_pts(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        out.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                    mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def glow_dot(f, c, r, color, alpha=1.0, core=True):
    """Emissive point light: radial-falloff halo in the glow layer (+ small bright core).
    r is the visible halo radius in world units."""
    g = cairo.RadialGradient(c[0], c[1], 0, c[0], c[1], r)
    g.add_color_stop_rgba(0.0, color[0], color[1], color[2], min(1.0, alpha))
    g.add_color_stop_rgba(0.18, color[0], color[1], color[2], min(1.0, alpha * 0.55))
    g.add_color_stop_rgba(0.5, color[0], color[1], color[2], min(1.0, alpha * 0.16))
    g.add_color_stop_rgba(1.0, color[0], color[1], color[2], 0.0)
    f.g.new_sub_path()
    f.g.arc(c[0], c[1], r, 0, 2 * math.pi)
    f.g.set_source(g)
    f.g.fill()
    if core:
        f.ctx.new_sub_path()
        f.ctx.arc(c[0], c[1], max(1.5, r * 0.06), 0, 2 * math.pi)
        _src(f.ctx, color, min(1.0, alpha))
        f.ctx.fill()


def gradient_fill(f, pts, stops, p0, p1, radial=False, r0=0.0, r1=1.0, glow=0.0):
    """Fill polygon with a linear (p0->p1) or radial (center p0, radii r0..r1) gradient.
    stops: [(offset, color, alpha), ...]. For light cones / haze of accent light only."""
    for ctx, k in _both(f, glow):
        if radial:
            g = cairo.RadialGradient(p0[0], p0[1], r0, p0[0], p0[1], r1)
        else:
            g = cairo.LinearGradient(p0[0], p0[1], p1[0], p1[1])
        for off, col, a in stops:
            g.add_color_stop_rgba(off, col[0], col[1], col[2], min(1.0, a * k))
        _path(ctx, pts, True)
        ctx.set_source(g)
        ctx.fill()
