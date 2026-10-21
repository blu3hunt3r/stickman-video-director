"""Atmosphere and graphic effects: rain, splashes, light cones, wet reflections, smoke,
puddles, lightning, chalk outlines and screen-space transitions (eyelid, iris).

All effects are deterministic functions of time + seed so any frame renders independently.
Rain is white line art; light haze uses an accent color at low opacity on the black canvas.
"""
import math

import cairo
import numpy as np
from scipy.ndimage import binary_erosion

from .core import W, H, WHITE, AMBER, BLACK, hash01, fbm1, noise1, clamp, rad
from .frame import Camera, _surface_to_array, _array_to_surface
from . import draw


# ----------------------------------------------------------------------------- rain
RAIN_LAYERS = (
    # depth, alpha, streak length, width, fall speed (px/s at depth 1), drops per cell
    (0.45, 0.22, 26.0, 1.4, 1500.0, 2),
    (0.75, 0.38, 42.0, 1.9, 2100.0, 2),
    (1.15, 0.62, 70.0, 2.6, 2900.0, 1),
)


def _view_bounds(cam, pad=120.0):
    corners = [cam.to_world(p) for p in ((0, 0), (W, 0), (0, H), (W, H))]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def rain(f, t, density=1.0, wind=7.0, seed=11, alpha=1.0, layers=RAIN_LAYERS, color=WHITE,
         speed=1.0, cell=150.0, slowmo=1.0):
    """World-anchored layered rain with parallax. wind: streak slant in degrees.
    slowmo < 1 slows the fall (for slow-motion beats)."""
    base = f.cam
    for li, (depth, a, length, w, v, per) in enumerate(layers):
        # each layer lives in a scaled copy of the world -> parallax when the camera moves
        cam = Camera(base.x * depth, base.y * depth, max(0.2, 1 + (base.zoom - 1) * depth), base.rot)
        x0, y0, x1, y1 = _view_bounds(cam)
        c = cell * (0.8 + 0.4 * depth)
        vy = v * speed * slowmo
        sl = math.tan(rad(wind))
        L = length * (0.35 + 0.65 * slowmo)
        n_per = max(1, int(round(per * density + 0.25)))
        with f.camera(cam):
            ctx = f.ctx
            ctx.new_path()
            i0, i1 = int(math.floor(x0 / c)), int(math.ceil(x1 / c))
            j0, j1 = int(math.floor(y0 / c)), int(math.ceil(y1 / c))
            for i in range(i0, i1):
                for j in range(j0, j1):
                    for k in range(n_per):
                        if hash01(seed, li, i, j, k, 7) > density:
                            continue
                        rx = (i + hash01(seed, li, i, j, k)) * c
                        ph = hash01(seed, li, i, j, k, 3)
                        span = c
                        yy = j * c + ((ph * span + t * vy) % span)
                        xx = rx + sl * (yy - j * c)
                        ctx.move_to(xx, yy)
                        ctx.line_to(xx + sl * L, yy + L)
            ctx.set_line_width(f.lw(w))
            ctx.set_source_rgba(color[0], color[1], color[2], a * alpha)
            ctx.stroke()


def splashes(f, t, ground_y, x0, x1, rate=1.0, seed=5, alpha=0.8, size=1.0):
    """Tiny crown splashes along a ground line between x0 and x1 (world)."""
    n = int(abs(x1 - x0) / 34 * rate)
    ctx = f.ctx
    ctx.new_path()
    for i in range(n):
        per = 0.35 + 0.5 * hash01(seed, i)
        ph = hash01(seed, i, 2)
        cyc = math.floor((t / per) + ph)
        tau = (t / per + ph) - cyc
        if tau > 0.28:
            continue
        x = x0 + (x1 - x0) * hash01(seed, i, int(cyc), 4)
        y = ground_y + 6 * (hash01(seed, i, int(cyc), 5) - 0.5)
        k = tau / 0.28
        r = (5 + 9 * k) * size
        h = 9 * size * math.sin(math.pi * k)
        ctx.move_to(x - r * 0.4, y)
        ctx.line_to(x - r, y - h)
        ctx.move_to(x + r * 0.4, y)
        ctx.line_to(x + r, y - h)
    ctx.set_line_width(f.lw(1.6))
    ctx.set_source_rgba(1, 1, 1, alpha)
    ctx.stroke()


def ripples(f, t, x0, y0, x1, y1, rate=1.0, seed=9, alpha=0.6, squash=0.32):
    """Expanding ripple rings on a wet surface rectangle (world)."""
    area = abs((x1 - x0) * (y1 - y0))
    n = int(area / 9000 * rate)
    for i in range(n):
        per = 0.6 + 0.8 * hash01(seed, i)
        ph = hash01(seed, i, 1)
        cyc = math.floor(t / per + ph)
        tau = (t / per + ph) - cyc
        x = x0 + (x1 - x0) * hash01(seed, i, int(cyc), 2)
        y = y0 + (y1 - y0) * hash01(seed, i, int(cyc), 3)
        r = 4 + 26 * tau
        draw.ellipse(f, (x, y), r, r * squash, 0, 1.5, WHITE, alpha * (1 - tau) ** 1.5)


# ----------------------------------------------------------------------------- light
def light_cone(f, apex, angle, spread, length, color=AMBER, alpha=0.16, glow=0.5):
    """Visible haze of a light beam (accent color, low opacity) - pair with f.lit()."""
    ax, ay = apex
    a0, a1 = rad(angle - spread / 2), rad(angle + spread / 2)
    pts = [apex]
    for i in range(13):
        th = a0 + (a1 - a0) * i / 12
        pts.append((ax + length * math.cos(th), ay + length * math.sin(th)))
    draw.gradient_fill(f, pts, [(0.0, color, alpha), (0.55, color, alpha * 0.45), (1.0, color, 0.0)],
                       apex, None, radial=True, r0=0, r1=length, glow=glow)


def light_pool(f, c, rx, ry, color=AMBER, alpha=0.18, glow=0.6):
    """Elliptical pool of light on the ground."""
    f.ctx.save()
    f.g.save()
    for ctx in (f.ctx, f.g):
        ctx.translate(*c)
        ctx.scale(1.0, ry / max(rx, 1e-3))
    draw.gradient_fill(f, [(-rx, -rx), (rx, -rx), (rx, rx), (-rx, rx)],
                       [(0.0, color, alpha), (1.0, color, 0.0)], (0, 0), None, radial=True,
                       r0=0, r1=rx, glow=glow)
    f.ctx.restore()
    f.g.restore()


def reflection(f, x, y_ground, length=260, width=34, color=AMBER, alpha=0.5, t=0.0, seed=0):
    """Wet-pavement reflection of a light: broken horizontal ripple dashes below it."""
    n = int(length / 10)
    for i in range(n):
        k = i / max(1, n - 1)
        yy = y_ground + 6 + i * 10
        wob = 6 * fbm1(t * 1.3 + i * 0.37, seed)
        ww = width * (1 - 0.55 * k) * (0.6 + 0.4 * hash01(seed, i))
        a = alpha * (1 - k) ** 1.4 * (0.55 + 0.45 * (0.5 + 0.5 * noise1(t * 3 + i, seed + 1)))
        draw.line(f, (x - ww / 2 + wob, yy), (x + ww / 2 + wob, yy), 3.0, color, a, glow=0.9)


# ----------------------------------------------------------------------------- smoke / water
def smoke(f, x, y, t, seed=0, height=140.0, alpha=0.45, strands=2, drift=14.0, w=2.0):
    """Wisps rising from (x, y). Thin white curling lines that fade with height."""
    for s in range(strands):
        pts = []
        n = 18
        for i in range(n):
            k = i / (n - 1)
            yy = y - k * height
            xx = x + drift * k * fbm1(t * 0.9 - k * 2.2, seed + s * 13) * 2.2 + 4 * s
            pts.append((xx, yy))
        for i in range(n - 1):
            k = i / (n - 1)
            draw.line(f, pts[i], pts[i + 1], w * (1 - 0.5 * k), WHITE, alpha * (1 - k) ** 1.3 * (0.7 if s else 1.0))


def puddle(f, c, rx, ry, t, seed=0, alpha=0.7, rings=True):
    draw.ellipse(f, c, rx, ry, 0, 2.2, WHITE, alpha * 0.55)
    if rings:
        for i in range(3):
            per = 0.9 + 0.4 * hash01(seed, i)
            tau = (t / per + hash01(seed, i, 1)) % 1.0
            cx = c[0] + (hash01(seed, i, int(t / per)) - 0.5) * rx * 0.8
            cy = c[1] + (hash01(seed, i, int(t / per), 2) - 0.5) * ry * 0.6
            r = 3 + rx * 0.35 * tau
            draw.ellipse(f, (cx, cy), r, r * ry / rx, 0, 1.4, WHITE, alpha * (1 - tau) ** 2)


def lightning(f, a, b, seed=0, alpha=1.0, w=3.0, branches=2):
    """Jagged white bolt from a to b with a couple of branches (emissive)."""
    def bolt(p, q, depth, s):
        pts = [p, q]
        disp = math.hypot(q[0] - p[0], q[1] - p[1]) * 0.18
        for d in range(depth):
            new = [pts[0]]
            for i in range(len(pts) - 1):
                m = ((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
                off = (hash01(s, d, i) - 0.5) * 2 * disp
                new += [(m[0] + off, m[1] + off * 0.2), pts[i + 1]]
            pts = new
            disp *= 0.55
        return pts
    main = bolt(a, b, 6, seed)
    draw.stroke(f, main, w, WHITE, alpha, glow=1.6, glow_w=w * 5)
    for k in range(branches):
        i = int(len(main) * (0.3 + 0.4 * hash01(seed, k, 9)))
        p = main[i]
        q = (p[0] + (hash01(seed, k, 3) - 0.5) * 300, p[1] + 160 + 140 * hash01(seed, k, 4))
        draw.stroke(f, bolt(p, q, 4, seed + 50 + k), w * 0.6, WHITE, alpha * 0.8, glow=1.0)


# ----------------------------------------------------------------------------- chalk outline
def chalk_outline(f, polylines, head_c, head_r, body_w=46.0, line_px=5.0, alpha=0.95, seed=0,
                  color=WHITE):
    """Crime-scene chalk outline traced AROUND a lying stick figure (world coords).
    Renders a thick silhouette mask, extracts its edge, roughens it like chalk."""
    sw, sh = f.pw, f.ph
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
    c = cairo.Context(surf)
    c.set_matrix(f.cam.matrix(f.scale))
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgba(1, 1, 1, 1)
    c.set_line_width(body_w)
    for pl in polylines:
        c.move_to(*pl[0])
        for p in pl[1:]:
            c.line_to(*p)
        c.stroke()
    c.arc(head_c[0], head_c[1], head_r + body_w * 0.45, 0, 2 * math.pi)
    c.fill()
    m = _surface_to_array(surf)[..., 3] > 127
    k = max(1, int(round(line_px * f.scale * f.cam.zoom ** 0.35)))
    edge = m & ~binary_erosion(m, iterations=k)
    rng = np.random.default_rng(seed)
    grain = rng.random(edge.shape) > 0.18
    a = (edge & grain).astype(np.float32) * 255.0 * alpha
    out = np.zeros((sh, sw, 4), np.float32)
    for ch, v in zip((2, 1, 0), color):
        out[..., ch] = a * v
    out[..., 3] = a
    s = _array_to_surface(out)
    f.ctx.save()
    f.ctx.identity_matrix()
    f.ctx.set_source_surface(s, 0, 0)
    f.ctx.paint()
    f.ctx.restore()


# ----------------------------------------------------------------------------- transitions
def eyelid(f, openness, curve=0.18):
    """Screen-space eyelids closing/opening vertically. openness 1 = fully open (no-op)."""
    o = clamp(openness)
    if o >= 0.999:
        return
    with f.screen():
        ctx = f.ctx
        half = H / 2 * (1 - o)
        bulge = H * curve * o
        ctx.set_source_rgb(*BLACK)
        ctx.move_to(-10, -10)
        ctx.line_to(W + 10, -10)
        ctx.line_to(W + 10, half)
        ctx.curve_to(W * 0.7, half + bulge, W * 0.3, half + bulge, -10, half)
        ctx.close_path()
        ctx.fill()
        ctx.move_to(-10, H + 10)
        ctx.line_to(W + 10, H + 10)
        ctx.line_to(W + 10, H - half)
        ctx.curve_to(W * 0.7, H - half - bulge, W * 0.3, H - half - bulge, -10, H - half)
        ctx.close_path()
        ctx.fill()


def iris(f, cx, cy, r):
    """Screen-space iris: black everywhere outside a circle (cx, cy, r in screen px)."""
    with f.screen():
        ctx = f.ctx
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.rectangle(-10, -10, W + 20, H + 20)
        ctx.new_sub_path()
        ctx.arc(cx, cy, max(0.0, r), 0, 2 * math.pi)
        ctx.set_source_rgb(*BLACK)
        ctx.fill()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def dust(f, t, box, n=90, seed=3, alpha=0.55, size=2.2, drift=(6.0, -4.0)):
    """Floating dust motes in a world-space box (x0, y0, x1, y1). Draw them INSIDE an
    f.lit(...) group so they only sparkle where the light beam falls."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    for i in range(n):
        px = (hash01(seed, i) * w + drift[0] * t * (0.5 + hash01(seed, i, 1)) + 14 * fbm1(t * 0.3, seed + i)) % w
        py = (hash01(seed, i, 2) * h + drift[1] * t * (0.5 + hash01(seed, i, 3)) + 10 * fbm1(t * 0.27, seed + 2 * i)) % h
        tw = 0.45 + 0.55 * (0.5 + 0.5 * noise1(t * 1.7 + i, seed + 5))
        r = size * (0.6 + 0.8 * hash01(seed, i, 4))
        draw.circle(f, (x0 + px, y0 + py), r, 1, WHITE, alpha * tw, fill_it=True)
