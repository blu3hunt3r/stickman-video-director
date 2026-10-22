"""SALVAGE sets - shared foundation: world layout, parallax projection, colours, cached
shapes, ropes and current sway. Import the public API from `films.salvage.sets`.

ONE WORLD FOR THE WHOLE FILM (continuity comes from moving through it)
    x : right, world px. y : DOWN. An adult is ~600 px tall at zoom 1, so 1 m = M = 333 px.
    y = 0 is mean sea level. The sky is y < 0, the water y > 0 (y = depth below the surface).
    The seabed lies at y ~ SEABED_Y = 9000 (~27 m). The boat floats at y ~ 0 with its stern
    davit right above DIVE_X; the Meridian lies on the seabed below, her bridge under DIVE_X.
    The wreck INTERIOR (shafts, captain's cabin) and the close-ups (hull plating, safe dial) are
    separate little worlds with their own origins (see sets_wreck / sets_interior).

PARALLAX LAYERS
    Frame.layer(par) uses Camera.parallax, whose vanishing point is world (540, 960). To place
    something that truly sits at (x, y) but farther away (depth 1/par times the action plane),
    draw it inside that layer at proj(par, x, y) and scale its size by par. This keeps far
    seabed, rock shelves and the wreck's ghost consistent with the action plane whatever the
    camera does (exact at zoom 1, a close approximation at other zooms).
"""
import math

import cairo

from engine import draw
from engine.core import W, H, clamp, lerp, hash01, noise1, fbm1, smoothstep, inv_lerp
from engine.palette import SALVAGE as PAL, RED, PAPER

# ----------------------------------------------------------------------------- world layout
M = 333.0                  # world px per metre (adult 1.8 m = 600 px)
SEA_Y = 0.0                # mean sea level
SEABED_Y = 9000.0          # mean seabed depth (~27 m)
DIVE_X = 0.0               # x of the shot line: boat davit sheave above, the wreck's bridge below

PAR_O = (W / 2.0, H / 2.0)  # Camera.parallax origin = the vanishing point of par -> 0

INK = PAL.ink


# ----------------------------------------------------------------------------- projection
def proj(par, x, y):
    """Layer coordinates (inside f.layer(par=par)) of a point that truly sits at world (x, y)
    at 1/par times the action-plane distance. Sizes scale by `par` too."""
    return (PAR_O[0] + par * (x - PAR_O[0]), PAR_O[1] + par * (y - PAR_O[1]))


def unproj(par, X, Y):
    """Inverse of proj: true world point of layer coordinates (X, Y) at parallax par."""
    p = max(par, 1e-6)
    return (PAR_O[0] + (X - PAR_O[0]) / p, PAR_O[1] + (Y - PAR_O[1]) / p)


def level_y(par, y_true=SEA_Y):
    """Layer y (at parallax par) of the horizontal plane y_true (sea level by default)."""
    return PAR_O[1] + par * (y_true - PAR_O[1])


def screen_of(cam, p, par=1.0):
    """Screen position (1080x1920 frame px) of world point p seen through layer `par`."""
    c = cam if par == 1.0 else cam.parallax(par)
    return c.to_screen(p)


def view_rect(f, par=1.0, margin=0.0):
    """World rect (x0, y0, x1, y1) visible in layer `par` (in that layer's own coords)."""
    return f.lcam(par).view_rect(margin)


# ----------------------------------------------------------------------------- colours
def mix(a, b, t):
    """Blend two rgb tuples (t clamped to 0..1)."""
    t = clamp(t)
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def scale_rgb(c, k):
    return (c[0] * k, c[1] * k, c[2] * k)


# Water by depth (world y). Bright aqua under the surface -> teal -> ink in the deep.
_WATER_STOPS = [
    (-1e9, PAL.surface),
    (0.0, PAL.surface),
    (140.0, mix(PAL.surface, PAL.mid, 0.30)),
    (520.0, mix(PAL.surface, PAL.mid, 0.66)),
    (1300.0, mix(PAL.surface, PAL.mid, 0.90)),
    (2400.0, PAL.mid),
    (4000.0, mix(PAL.mid, PAL.deep, 0.50)),
    (6000.0, mix(PAL.mid, PAL.deep, 0.86)),
    (7800.0, PAL.deep),
    (9400.0, mix(PAL.deep, PAL.ink, 0.45)),
    (1e9, mix(PAL.deep, PAL.ink, 0.45)),
]


def water_at(y, bright=1.0):
    """Ambient water colour at world depth y (what the open water looks like there).
    bright < 1 = night: the surface skin dims a little and the light dies faster with depth
    (the deep end stays the same), so the split shots keep a glowing surface over a dark
    column."""
    if bright != 1.0:
        b = clamp(bright, 0.05, 1.0)
        y = max(y, 0.0) / (b ** 1.6)
    st = _WATER_STOPS
    c = st[-1][1]
    for (y0, c0), (y1, c1) in zip(st, st[1:]):
        if y <= y1:
            c = mix(c0, c1, (y - y0) / max(y1 - y0, 1e-6))
            break
    if bright != 1.0:
        c = mix(PAL.ink, c, lerp(0.80, 1.0, clamp(bright)))
    return c


def water_stops(y0, y1, n=10, bright=1.0):
    """[(world_y, rgb)] stops for a vertical gradient of the water between y0 and y1."""
    return [(lerp(y0, y1, i / (n - 1)), water_at(lerp(y0, y1, i / (n - 1)), bright)) for i in range(n)]


def depth_light(y):
    """0..1 ambient light reaching depth y (1 at the surface). Use it to fade god rays,
    caustics and surface glints, and to dim far silhouettes' backlight."""
    return clamp(math.exp(-max(y, 0.0) / 2600.0))


def tone(d, bg=None, gamma=None):
    """Fill colour for a silhouette at relative distance d (0 = action plane .. 1 = lost in
    the water) seen against background colour bg (default: the palette fog for d). Same maths
    as f.layer(fog=d, fog_color=bg), but drawn directly (no offscreen layer, no cost)."""
    bg = bg if bg is not None else PAL.fog_at(d)
    g = PAL.haze_gamma if gamma is None else gamma
    return mix(PAL.ink, bg, clamp(d) ** g)


def sky_at(u):
    """Night sky colour, u = 0 at the horizon .. 1 high up."""
    return mix(PAL.sky_bottom, PAL.sky_top, smoothstep(0.0, 1.0, u))


def lit_paper(k=1.0):
    """Pale prop colour (logbook pages, photo, envelope) at light level k (0 = ink)."""
    return mix(PAL.ink, PAL.paper, clamp(k))


# ----------------------------------------------------------------------------- cached shapes
_SCRATCH = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2))
_SHAPES = {}


def shape(key, builder):
    """Build (once) and return a cached cairo.Path. builder(ctx) issues path commands in
    LOCAL coordinates (no fill). Holes: trace them in the opposite direction (winding rule)."""
    p = _SHAPES.get(key)
    if p is None:
        c = _SCRATCH
        c.new_path()
        c.identity_matrix()
        builder(c)
        p = c.copy_path()
        c.new_path()
        _SHAPES[key] = p
    return p


def put(ctx, path, x=0.0, y=0.0, ang=0.0, s=1.0, flip=False, sy=None):
    """Append a cached path to ctx's current path at (x, y), rotated ang degrees, scaled s
    (flip mirrors in x). Fill afterwards (lets several shapes share one fill)."""
    ctx.save()
    ctx.translate(x, y)
    if ang:
        ctx.rotate(math.radians(ang))
    ctx.scale(-s if flip else s, s if sy is None else sy)
    ctx.append_path(path)
    ctx.restore()


def paint(ctx, rgb, a=1.0):
    """Fill the current path with rgb (winding rule)."""
    if len(rgb) == 4:
        ctx.set_source_rgba(*rgb)
    else:
        ctx.set_source_rgba(rgb[0], rgb[1], rgb[2], a)
    ctx.fill()


def rev(pts):
    """Reversed point list (trace a hole against its outer contour)."""
    return list(reversed(pts))


def signed_area(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def oriented(pts, cw=True):
    """pts with a fixed orientation (cw=True: clockwise on screen, y down)."""
    return pts if (signed_area(pts) > 0) == cw else rev(pts)


def hole_circle(ctx, c, r):
    """Circle traced counter-clockwise (screen): a hole inside a clockwise contour."""
    ctx.new_sub_path()
    ctx.arc_negative(c[0], c[1], max(r, 0.01), 0.0, -2 * math.pi)
    ctx.close_path()


def solid_circle(ctx, c, r):
    """Circle traced clockwise (screen), the orientation of solids in this module."""
    ctx.new_sub_path()
    ctx.arc(c[0], c[1], max(r, 0.01), 0.0, 2 * math.pi)
    ctx.close_path()


def ell(ctx, c, rx, ry, ang=0.0, hole=False):
    """Ellipse sub-path (clockwise; hole=True traces it counter-clockwise)."""
    ctx.save()
    ctx.translate(c[0], c[1])
    if ang:
        ctx.rotate(math.radians(ang))
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    if hole:
        ctx.arc_negative(0, 0, 1, 0, -2 * math.pi)
    else:
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.close_path()
    ctx.restore()


def round_rect(ctx, x0, y0, x1, y1, r, hole=False):
    """Rounded rectangle sub-path (clockwise, or counter-clockwise when hole=True)."""
    r = min(r, abs(x1 - x0) / 2, abs(y1 - y0) / 2)
    ctx.new_sub_path()
    if not hole:
        ctx.arc(x1 - r, y0 + r, r, -math.pi / 2, 0)
        ctx.arc(x1 - r, y1 - r, r, 0, math.pi / 2)
        ctx.arc(x0 + r, y1 - r, r, math.pi / 2, math.pi)
        ctx.arc(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi)
    else:
        ctx.arc_negative(x0 + r, y0 + r, r, 1.5 * math.pi, math.pi)
        ctx.arc_negative(x0 + r, y1 - r, r, math.pi, math.pi / 2)
        ctx.arc_negative(x1 - r, y1 - r, r, math.pi / 2, 0)
        ctx.arc_negative(x1 - r, y0 + r, r, 0, -math.pi / 2)
    ctx.close_path()


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def xform(pts, x=0.0, y=0.0, ang=0.0, s=1.0):
    """Rotate (deg) + scale + translate a list of points (pure python, for anchors)."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s) for px, py in pts]


def xf(p, x=0.0, y=0.0, ang=0.0, s=1.0):
    return xform([p], x, y, ang, s)[0]


# ----------------------------------------------------------------------------- lines / ropes
def line(ctx, pts, w, rgb=None, a=1.0, cap=cairo.LINE_CAP_ROUND):
    """A thin physical line (wire, rope, rail) of width w through pts, filled in rgb."""
    if len(pts) < 2:
        return
    ctx.new_path()
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    rgb = rgb or INK
    ctx.set_source_rgba(rgb[0], rgb[1], rgb[2], a)
    ctx.stroke()


def sag_curve(p0, p1, sag, n=24, wobble=0.0, t=0.0, seed=0):
    """Points of a hanging line from p0 to p1 sagging by `sag` px at mid-span (parabolic
    catenary approximation). wobble adds a slow current-driven sideways ripple."""
    out = []
    for i in range(n + 1):
        u = i / n
        x = lerp(p0[0], p1[0], u)
        y = lerp(p0[1], p1[1], u) + sag * 4.0 * u * (1.0 - u)
        if wobble:
            env = math.sin(math.pi * u)
            x += wobble * env * noise1(u * 3.0 + t * 0.35, seed)
            y += 0.4 * wobble * env * noise1(u * 2.0 + t * 0.3, seed + 5)
        out.append((x, y))
    return out


def sway(t, seed=0, amp=1.0, period=5.0):
    """Slow, smooth current sway in [-amp, amp] (deterministic): a sine swell plus a little
    noise so repeated props never move in lockstep."""
    ph = hash01(seed, 3) * 6.283
    return amp * (0.75 * math.sin(2 * math.pi * t / period + ph) + 0.25 * noise1(t * 0.45, seed + 11))


def pendulum(t, seed=0, amp=6.0, period=4.0):
    """(angle, angular_velocity_sign) of something hanging in a current (degrees)."""
    a = sway(t, seed, amp, period)
    a2 = sway(t + 0.05, seed, amp, period)
    return a, (a2 - a) / 0.05


def blade(ctx, base, ang, length, w0, w1=0.0, bend=0.0, n=8):
    """Tapered curved blade (sea grass, petal, flame-like tongue): base point, direction ang
    (deg, 0 = right, -90 = up), length, base width w0 -> tip width w1, bend (deg over the
    length). Appends a closed sub-path (clockwise)."""
    left, right = [], []
    x, y = base
    a = math.radians(ang)
    step = length / n
    pts = [(x, y)]
    for i in range(n):
        a += math.radians(bend) / n
        x += math.cos(a) * step
        y += math.sin(a) * step
        pts.append((x, y))
    for i, p in enumerate(pts):
        u = i / n
        w = lerp(w0, w1, u) * 0.5
        q0 = pts[max(i - 1, 0)]
        q1 = pts[min(i + 1, n)]
        tx, ty = q1[0] - q0[0], q1[1] - q0[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    outline = left + right[::-1]
    draw.poly(ctx, outline)
    return pts[-1]


def jag(pts, seed=0, amp=6.0, step=18.0, close=True):
    """Roughen an outline with small irregular steps (torn steel, rock, broken timber)."""
    out = []
    n = len(pts)
    edges = n if close else n - 1
    k = 0
    for i in range(edges):
        a, b = pts[i], pts[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        m = max(1, int(L / step))
        nx, ny = (-(b[1] - a[1]) / (L or 1), (b[0] - a[0]) / (L or 1))
        for j in range(m):
            u = j / m
            d = (hash01(seed, k) * 2 - 1) * amp if j else 0.0
            out.append((lerp(a[0], b[0], u) + nx * d, lerp(a[1], b[1], u) + ny * d))
            k += 1
    if not close:
        out.append(pts[-1])
    return out


def riveted_edge(pts, pitch=26.0, r=3.2, plate=300.0, step=7.0, close=False, seed=0):
    """Re-trace a hull edge (open polyline, solid on its RIGHT when walking it) with lapped
    plate steps every `plate` px and rivet heads every `pitch` px, so a riveted steel hull
    reads in the silhouette edge. Returns a new point list."""
    out = []
    n = len(pts)
    acc = 0.0
    lap = 0.0
    last_plate = 0
    for i in range(n - 1 if not close else n):
        a, b = pts[i], pts[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-6:
            continue
        tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = ty, -tx        # outward normal (left of walking direction)
        m = max(1, int(L / 2.0))
        for j in range(m):
            u = j / m
            s = acc + u * L
            pk = int(s / plate)
            if pk != last_plate:
                last_plate = pk
                lap = (0.6 + 0.8 * hash01(seed, pk)) * r * 1.4 * (1 if pk % 2 else -0.4)
            ph = (s % pitch) / pitch
            bump = r * math.sqrt(max(0.0, 1.0 - ((ph - 0.5) / 0.22) ** 2)) if abs(ph - 0.5) < 0.22 else 0.0
            off = lap + bump
            if j % 2 == 0 or bump > 0:
                out.append((a[0] + tx * u * L + nx * off, a[1] + ty * u * L + ny * off))
        acc += L
    out.append(pts[-1] if not close else pts[0])
    return out
