"""THIN ICE: the kit every scene shares.

  * the palette (one job per colour, see docs/BIBLE.md): INK figures and trees; NIGHT sky; STEEL
    distance; SNOW the moonlit page; SHADOW footprints and cast shadows; ICE the river's white ice;
    THIN the black band of thin ice; WATER open water; PAPER the moon, the searchlight, breath;
    AMBER the lantern and lit windows; RED the girl's scarf, nothing else;
  * the paper (OPPOSITE's settings, grain on twos);
  * OPPOSITE's annotation layer, re-exported: dots, sight lines, ripples, step dots, the heartbeat;
  * the film's devices, all pure functions of time:
      snow(c, t, ...)               falling cut-paper flakes in three depths; `density(t)` lets it
                                    stop (flakes already falling fall out) and start again
      snow_top(c, t, ...)           the same seen from above (flakes shrink as they fall and land)
      moon(c, p, r) / stars(c)      the moon disc; a few stars
      cloud(c, p, s)                a flat cloud (the moon goes in and out)
      breath(c, mouth, t, ...)      puffs on every out-breath
      beam(...) / lit_patch(...)    the searchlight: a beam in elevation, its lit patch on snow
      lantern(...) / glow(...)      the guard's lantern and its pool of warm light
      print_pts(kind, side)         a footprint outline in metres (heel at 0, toe toward +y)
      crack_tree(...) / crack(...)  jagged branching cracks grown from a point
      whistle(...)                  the whistle's rays

Frame px everywhere (1080 x 1920, y down) unless a function says metres.
"""
import math
from functools import lru_cache

import cairo

from engine import bass, draw
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED
from engine.timing import timeline
from films.opposite_bass import world as B
from films.opposite_full import kit as OK

FILM = "thin_ice"
W, H = 1080.0, 1920.0

INK = (0.020, 0.022, 0.030)
NIGHT = (0.075, 0.115, 0.185)      # the sky; the title's field
STEEL = (0.22, 0.29, 0.38)         # distance: far trees, the far bank, the farmhouse
SNOW = (0.74, 0.78, 0.84)          # moonlit snow: the page
SHADOW = (0.50, 0.57, 0.67)        # footprints, cast shadows on snow
ICE = (0.60, 0.70, 0.78)           # the river's white ice
THIN = (0.22, 0.30, 0.37)          # the thin black band
WATER = (0.035, 0.075, 0.125)      # open water, under the ice: a deep blue, apart from the earth's INK
PAPER = bass.PAPER                 # the moon, the searchlight, breath, the title
AMBER = (0.95, 0.66, 0.24)         # the lantern, the stove, lit windows
RED = RED                          # the girl's scarf
# derived tones (same jobs, other lights)
SNOW_DIM = lerp(SNOW, NIGHT, 0.30)       # the page before the moon comes out
ICE_DIM = lerp(ICE, NIGHT, 0.30)
SHADOW_DIM = lerp(SHADOW, NIGHT, 0.30)
LIT = PAPER                        # snow in the searchlight

BPM = 120.0
BEAT = 60.0 / BPM

k = B.k
twos = B.twos
fill = B.fill
clip_rect = B.clip_rect
edged = B.edged

# OPPOSITE's annotation layer
dot = OK.dot
arrowhead = OK.arrowhead
dotted = OK.dotted
sight_line = OK.sight_line
marker_ring = OK.marker_ring
arrow = OK.arrow
ripple = OK.ripple
step_dots = OK.step_dots
callout = OK.callout
heartbeat = OK.heartbeat


def film_start(sid):
    """Film time (s) of scene sid's first frame, from the timeline."""
    return float(next(s["start"] for s in timeline(FILM)["scenes"] if s["id"] == sid))


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


def scene_setup(f, field=NIGHT):
    """The film's paper (OPPOSITE's settings): a flat field, fibres, ink mottling, grain on twos."""
    bass.bass_scene(f, field=field, paper=0.85, vignette=0.12, mottle=0.035, flicker=0.0)
    f.post["grain_fps"] = 12.0


def poly(c, pts, color, alpha=1.0):
    """Fill one polygon (any winding)."""
    if len(pts) >= 3:
        bass.fill_polys(c, [bass.orient(list(pts), True)], color, alpha)


def polys(c, ps, color, alpha=1.0):
    ps = [bass.orient(list(p), True) for p in ps if len(p) >= 3]
    if ps:
        bass.fill_polys(c, ps, color, alpha)


def disc(c, p, r, color, seed=0, alpha=1.0, n=None):
    if r > 0.3:
        bass.fill_polys(c, [bass.ring_pts(p, r, seed=seed, n=n or int(clamp(r * 0.9, 12, 72)), amp=min(1.2, 0.02 * r))],
                        color, alpha)


def ellipse(c, p, rx, ry, color, angle=0.0, alpha=1.0, n=48):
    if rx > 0.3 and ry > 0.3:
        bass.fill_polys(c, [draw.ellipse_pts(p, rx, ry, n=n, angle=angle)], color, alpha)


def band(c, pts, color, width, seed=0, alpha=1.0, taper=(1.0, 1.0)):
    """A cut stroke along a polyline (wire, a branch, the scarf seen from above)."""
    if len(pts) >= 2:
        bass.line_band(c, pts, color, width=width, seed=seed, alpha=alpha, taper=taper)


# ============================================================================ snow
def _flake_pts(p, r, seed):
    """A small six-pointed cut flake (bigger flakes) or a cut dot (small ones)."""
    if r < 5.0:
        return bass.ring_pts(p, r, seed=seed, n=7, amp=0.25 * r)
    pts = []
    rot = 30.0 * hash01(seed, 3)
    for i in range(12):
        a = math.radians(rot + 30.0 * i)
        rr = r * (1.0 if i % 2 == 0 else 0.55)
        pts.append((p[0] + rr * math.cos(a), p[1] + rr * math.sin(a)))
    return pts


def snow(c, t, density=lambda t: 1.0, n=170, wind=18.0, fall=1.0, rect=(0.0, 0.0, W, H), seed=11, alpha=1.0,
         color=PAPER, layers=(0, 1, 2), size=1.0):
    """Falling snow in three depths (0 far: small and slow, 2 near: big and quicker), screen
    space. density(t) in 0..1 is the snowfall when a flake was born at the top: when it drops to
    0 the flakes already falling keep falling out of the frame, so the snow STOPS rather than
    vanishing; when it rises again new flakes start at the top. fall scales the fall speed
    (0.25 for a straight-down view, where the flakes come toward the camera)."""
    x0, y0, x1, y1 = rect
    hgt = (y1 - y0) + 80.0
    polys_by_layer = {0: [], 1: [], 2: []}
    for i in range(n):
        layer = 0 if i % 3 == 0 else (1 if i % 3 == 1 else 2)
        if layer not in layers:
            continue
        r = (2.6, 4.4, 7.0)[layer] * (0.8 + 0.45 * hash01(seed, i, 1)) * size
        v = (55.0, 85.0, 125.0)[layer] * (0.8 + 0.4 * hash01(seed, i, 2)) * fall
        ph = hash01(seed, i, 3)
        s = ph * hgt + v * t                       # distance fallen since the flake's cycle began
        cyc = math.floor(s / hgt)
        yy = s - cyc * hgt                         # 0 at the top
        born = t - yy / max(v, 1e-6)               # when this cycle of the flake left the top
        if hash01(seed, i, 4, cyc) >= density(born):
            continue
        sway = (10.0 + 14.0 * hash01(seed, i, 5)) * math.sin(t * (0.6 + 0.7 * hash01(seed, i, 6)) + 6.28 * ph)
        xx = x0 + ((hash01(seed, i, 7, cyc) * (x1 - x0 + 120.0) + wind * (0.5 + 0.25 * layer) * t + sway)
                   % (x1 - x0 + 120.0)) - 60.0
        polys_by_layer[layer].append(_flake_pts((xx, y0 - 40.0 + yy), r, seed * 7 + i))
    for layer, a in ((0, 0.55), (1, 0.8), (2, 0.95)):
        if polys_by_layer[layer]:
            bass.fill_polys(c, [bass.orient(q, True) for q in polys_by_layer[layer]], color, alpha * a)


def snow_top(c, t, density=lambda t: 1.0, n=150, wind=(26.0, 10.0), life=(0.8, 1.5), rect=(0.0, 0.0, W, H), seed=17,
             alpha=1.0, color=PAPER, size=1.0):
    """Snow seen from above (the page): each flake appears near the camera, big, and shrinks as it
    falls to the snow, drifting with the wind (px/s), and is gone when it lands. density(t) is
    the snowfall when a flake starts its fall: when it drops to 0 the flakes in the air land
    within `life` seconds, so the snow STOPS (and starts again when it rises)."""
    x0, y0, x1, y1 = rect
    polys = []
    for i in range(n):
        L = lerp(life[0], life[1], hash01(seed, i, 1))
        P = L * (1.25 + 0.5 * hash01(seed, i, 2))
        ph = hash01(seed, i, 3) * P
        cyc = math.floor((t + ph) / P)
        age = (t + ph) - cyc * P
        if age > L:
            continue
        born = t - age
        if hash01(seed, i, 4, cyc) >= density(born):
            continue
        u = age / L
        bx = x0 + hash01(seed, i, 5, cyc) * (x1 - x0 + 80.0) - 40.0
        by = y0 + hash01(seed, i, 6, cyc) * (y1 - y0 + 80.0) - 40.0
        r = (3.0 + 6.0 * hash01(seed, i, 7)) * size * (1.7 - 1.1 * u)
        polys.append((_flake_pts((bx + wind[0] * age, by + wind[1] * age), r, seed * 5 + i), 1.0 - 0.5 * u))
    for a in (0.95, 0.7):
        ps = [bass.orient(q, True) for q, w in polys if (w > 0.75) == (a > 0.8)]
        if ps:
            bass.fill_polys(c, ps, color, alpha * a)


def snowfall(t0, t1, start=None, ramp=0.6):
    """A density function: 1 until t0, easing to 0 by t1 (the snow stops); if start is given it
    rises again from start over `ramp` s (it begins to snow)."""
    def fn(t):
        d = 1.0 - ease("inout", clamp((t - t0) / max(t1 - t0, 1e-6)))
        if start is not None:
            d = max(d, ease("inout", clamp((t - start) / ramp)))
        return d
    return fn


# ============================================================================ sky
def moon(c, p, r=70.0, color=PAPER, seed=3):
    bass.fill_polys(c, [bass.ring_pts(p, r, seed=seed, n=56, amp=0.5)], color)


@lru_cache(maxsize=8)
def _stars(seed, n, y1):
    return [(hash01(seed, i, 1) * W, hash01(seed, i, 2) * y1, 1.4 + 1.8 * hash01(seed, i, 3)) for i in range(n)]


def stars(c, t=0.0, y1=700.0, n=46, seed=5, alpha=0.75, dx=0.0, dy=0.0):
    """A few small stars in the sky above y1 (they twinkle slowly on twos)."""
    tt = twos(t)
    for i, (x, y, r) in enumerate(_stars(seed, n, y1)):
        tw = 0.6 + 0.4 * math.sin(tt * (0.7 + hash01(seed, i, 4)) + 6.28 * hash01(seed, i, 5))
        dot(c, (x + dx, y + dy), r, PAPER, seed=seed + i, alpha=alpha * tw)


@lru_cache(maxsize=16)
def _cloud(seed, w, h):
    """A flat cloud: a row of overlapping cut lobes on a flat bottom (cached at the origin)."""
    lobes = []
    n = 5
    for i in range(n):
        u = i / (n - 1)
        r = h * (0.45 + 0.4 * math.sin(math.pi * u)) * (0.85 + 0.3 * hash01(seed, i))
        cx = -w / 2.0 + w * (0.12 + 0.76 * u)
        lobes.append(bass.cut_ellipse((cx, -r * 0.55), r * 1.15, r, seed=seed * 13 + i))
    base = bass.cut_rect(-w / 2.0 * 0.9, -h * 0.35, w / 2.0 * 0.9, 0.0, seed=seed, amp=0.8)
    return [bass.orient(q, True) for q in lobes + [base]]


def cloud(c, p, w=520.0, h=110.0, color=STEEL, seed=1, alpha=1.0):
    c.save()
    c.translate(*p)
    bass.fill_polys(c, _cloud(seed, float(w), float(h)), color, alpha)
    c.restore()


# ============================================================================ breath
def breath(c, mouth, t, rate=0.5, facing=1, s=1.0, phase=0.0, strength=1.0, color=PAPER, life=1.1, seed=0,
           pant=None):
    """Breath in the cold: a puff on every out-breath (one every 1/rate s, or `pant` for quick
    panting), growing, drifting forward and up and fading. strength 0 = holding the breath. s is
    the scale (1 for a figure about 600 px tall)."""
    if strength <= 0.01:
        return
    period = 1.0 / (pant or rate)
    k0 = math.floor((t - phase) / period)
    for j in (k0, k0 - 1):
        t0 = phase + j * period
        a = (t - t0) / life
        if not 0.0 <= a < 1.0:
            continue
        g = ease("out3", a)
        for lobe in range(3):
            off = (lobe - 1) * 0.35
            r = s * (5.0 + 15.0 * g) * (0.75 + 0.35 * hash01(seed, j, lobe))
            x = mouth[0] + facing * s * (6.0 + 40.0 * g + 9.0 * lobe)
            y = mouth[1] - s * (2.0 + 22.0 * g + 6.0 * off)
            dot(c, (x, y), r, color, seed=seed * 31 + j * 3 + lobe, alpha=strength * 0.42 * (1.0 - a) ** 1.4)


# ============================================================================ light
def beam(c, apex, a, b, color=PAPER, alpha=0.14, steps=3):
    """A searchlight beam: flat translucent wedges from apex to the segment a-b (where it meets the
    snow), nested so the core is brighter."""
    for i in range(steps):
        f = 1.0 - i / steps
        m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        aa = (lerp(m[0], a[0], 0.35 + 0.65 * f), lerp(m[1], a[1], 0.35 + 0.65 * f))
        bb = (lerp(m[0], b[0], 0.35 + 0.65 * f), lerp(m[1], b[1], 0.35 + 0.65 * f))
        poly(c, [apex, aa, bb], color, alpha * (0.6 if i == 0 else 0.5))


def lit_patch(c, p, rx, ry, color=LIT, alpha=0.9, angle=0.0, seed=0):
    """Where the searchlight falls on the snow: a bright flat ellipse with a softer ring round it."""
    ellipse(c, p, rx * 1.18, ry * 1.18, color, angle, alpha * 0.35)
    ellipse(c, p, rx, ry, color, angle, alpha)


def glow(c, p, r, strength=1.0, t=0.0, color=AMBER, ry=None, steps=4, seed=0, add=True):
    """A pool of lamplight: nested flat ellipses, brightest in the middle, breathing a little with
    the flame on twos. add: the light adds to what it falls on."""
    tt = twos(t)
    fl = 1.0 + 0.03 * math.sin(tt * 9.0 + seed) + 0.02 * _sn(int(tt * 12), seed)
    ry = r if ry is None else ry
    c.save()
    if add:
        c.set_operator(cairo.OPERATOR_ADD)
    for i in range(steps):
        f = 1.0 - i / steps
        bass.fill_polys(c, [draw.ellipse_pts(p, r * fl * (0.35 + 0.65 * f), ry * fl * (0.35 + 0.65 * f), n=72)],
                        color, 0.11 * strength)
    c.restore()


def lantern(c, p, s=1.0, lit=1.0, swing=0.0, color=INK, t=0.0, seed=0):
    """The guard's lantern hanging from its bail at p (the top of the bail): a cap, a glass
    chimney with a flame-bright core, a base; swing in degrees. Returns the flame's centre (px)."""
    c.save()
    c.translate(*p)
    c.rotate(math.radians(swing))
    c.scale(s, s)
    parts = [
        bass.capsule_pts((-14.0, 8.0), (14.0, 8.0), 3.0, 3.0, cap=3),                       # the bail's grip
        [(-16.0, 10.0), (-20.0, 34.0), (-17.0, 34.0), (-13.0, 10.0)],                         # the bail's arms
        [(16.0, 10.0), (20.0, 34.0), (17.0, 34.0), (13.0, 10.0)],
        [(-22.0, 34.0), (22.0, 34.0), (16.0, 22.0), (-16.0, 22.0)],                           # the cap
        [(-20.0, 34.0), (20.0, 34.0), (20.0, 40.0), (-20.0, 40.0)],
        [(-24.0, 78.0), (24.0, 78.0), (26.0, 92.0), (-26.0, 92.0)],                           # the base
    ]
    glass = [(-15.0, 40.0), (15.0, 40.0), (19.0, 60.0), (15.0, 78.0), (-15.0, 78.0), (-19.0, 60.0)]
    bass.fill_polys(c, [bass.orient(q, True) for q in parts], color)
    bass.fill_polys(c, [bass.orient(glass, True)], INK if lit <= 0.0 else lerp(INK, AMBER, clamp(lit)))
    # the guards round the glass
    for x in (-17.0, 0.0, 17.0):
        bass.fill_polys(c, [bass.orient([(x - 2.0, 40.0), (x + 2.0, 40.0), (x + 2.0, 78.0), (x - 2.0, 78.0)], True)], color)
    if lit > 0.0:
        tt = twos(t)
        fl = 1.0 + 0.08 * math.sin(tt * 19.0 + seed)
        dot(c, (0.0, 61.0), 7.5 * fl, PAPER, seed=seed, alpha=clamp(lit))
    flame = c.user_to_device(0.0, 61.0)
    c.restore()
    return c.device_to_user(*flame)


# ============================================================================ footprints (metres)
_PRINT = {
    # length, width (m); the shape is a sole: rounded toe, a waist, a heel
    "mother": (0.27, 0.105),
    "girl": (0.185, 0.075),
    "guard": (0.305, 0.12),
}


@lru_cache(maxsize=None)
def print_pts(kind, side=1):
    """A footprint outline in metres: heel at (0, 0), toe toward +y, side = +1 right foot, -1 left
    (the waist bites on the inside)."""
    L, Wd = _PRINT[kind]
    pts = []
    n = 28
    for i in range(n):
        a = 2.0 * math.pi * i / n
        y = L * (0.5 - 0.5 * math.cos(a))            # 0 at the heel, L at the toe
        u = y / L
        half = Wd * 0.5 * (0.78 + 0.22 * math.sin(math.pi * clamp(u * 1.25 - 0.1)))
        if 0.35 < u < 0.62:                          # the waist, on the inner side
            bite = 0.22 * math.sin(math.pi * (u - 0.35) / 0.27)
        else:
            bite = 0.0
        sgn = 1.0 if math.sin(a) >= 0 else -1.0
        inner = sgn == -side
        x = sgn * half * (1.0 - (bite if inner else 0.0))
        if kind == "guard" and u < 0.28:             # a square heel
            x = sgn * Wd * 0.5 * 0.82
        pts.append((x, y))
    return tuple(pts)


def print_world(kind, side, at, heading, scale=1.0):
    """A footprint's outline in map metres: heel at `at`, pointing along heading (degrees, 0 =
    north, 90 = east)."""
    a = math.radians(heading)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in print_pts(kind, side):
        x, y = x * scale, y * scale
        # local +y is the heading direction; local +x is to its right
        out.append((at[0] + x * ca + y * sa, at[1] - x * sa + y * ca))
    return out


# ============================================================================ cracks
@lru_cache(maxsize=256)
def crack_tree(origin, length, seed=0, branches=3, spread=70.0, heading=None, depth=2, jag=0.28, segs=7):
    """A jagged crack grown from origin: a list of (polyline, t0, t1) where t0..t1 is the part of
    the growth (0..1) during which that branch draws on. heading None: several arms out in all
    directions (a star); else one main line along heading (degrees, 0 = +x, 90 = +y) with
    branches off it."""
    out = []

    def grow(p, ang, L, t0, t1, d, s):
        pts = [p]
        seg = L / segs
        a = ang
        for i in range(segs):
            a += math.radians(_sn(s, i, 1) * 26.0)
            q = (pts[-1][0] + seg * math.cos(a), pts[-1][1] + seg * math.sin(a))
            # a jag: a short kink sideways
            if i < segs - 1:
                side = _sn(s, i, 2) * jag * seg
                q = (q[0] - math.sin(a) * side, q[1] + math.cos(a) * side)
            pts.append(q)
        out.append((tuple(pts), t0, t1))
        if d > 0:
            for b in range(2):
                f = 0.3 + 0.45 * hash01(s, b, 3)
                i = int(f * segs)
                bp = pts[i]
                ba = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
                ba += math.radians((1 if b == 0 else -1) * (28.0 + 30.0 * hash01(s, b, 4)))
                grow(bp, ba, L * (0.35 + 0.25 * hash01(s, b, 5)), lerp(t0, t1, f), t1 + (t1 - t0) * 0.3, d - 1,
                     s * 7 + b + 1)

    if heading is None:
        for i in range(branches):
            a = 2.0 * math.pi * (i + 0.5 * _sn(seed, i, 9)) / branches
            grow(origin, a, length * (0.7 + 0.5 * hash01(seed, i, 8)), 0.0, 0.8, depth, seed * 11 + i)
    else:
        grow(origin, math.radians(heading), length, 0.0, 0.85, depth, seed)
    return tuple(out)


def crack(c, tree, u, color=PAPER, width=5.0, seed=0, alpha=1.0, xf=None):
    """Draw a crack_tree grown to u (0..1). xf maps a tree point to frame px (default: identity)."""
    for j, (pts, t0, t1) in enumerate(tree):
        g = clamp((u - t0) / max(t1 - t0, 1e-6))
        if g <= 0.0:
            continue
        P = [xf(p) for p in pts] if xf else list(pts)
        L = sum(math.dist(a, b) for a, b in zip(P, P[1:]))
        part = _cut_at(P, L * g)
        if len(part) >= 2:
            w = width * (1.0 if j == 0 else 0.62)
            bass.line_band(c, part, color, width=w, seed=seed + j, alpha=alpha, taper=(1.0, 0.25))


def _cut_at(P, s):
    out = [P[0]]
    acc = 0.0
    for a, b in zip(P, P[1:]):
        d = math.dist(a, b)
        if acc + d >= s:
            u = (s - acc) / d if d > 0 else 0.0
            out.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u)))
            return out
        out.append(b)
        acc += d
    return out


# ============================================================================ sound made visible
def whistle(c, p, t, t0, color=PAPER, n=7, r0=26.0, r1=96.0, dur=0.35, width=7.0, seed=0, facing=1):
    """The whistle: short cut rays bursting forward from p at t0, gone after dur."""
    a = (t - t0) / dur
    if not 0.0 <= a < 1.0:
        return
    g = ease("out3", a)
    for i in range(n):
        ang = math.radians(-60.0 + 120.0 * i / (n - 1)) if facing > 0 else math.radians(120.0 + 120.0 * i / (n - 1))
        ra = lerp(r0, r1 * 0.75, g)
        rb = lerp(r0 + 18.0, r1, g)
        band(c, [(p[0] + ra * math.cos(ang), p[1] + ra * math.sin(ang)),
                 (p[0] + rb * math.cos(ang), p[1] + rb * math.sin(ang))], color, width * (1.0 - 0.6 * a), seed=seed + i,
             alpha=1.0 - a * a)


def step_pulse(c, p, t, t0, color=PAPER, r0=6.0, r1=34.0, life=0.4, width=4.0, seed=0, alpha=1.0):
    """A small ring out of a print when a foot lands in it (the backtrack: a print reused)."""
    a = (t - t0) / life
    if 0.0 <= a < 1.0:
        bass.ring(c, p, lerp(r0, r1, ease("out3", a)), width * (1.0 - a) + 0.5, color, seed=seed, alpha=alpha * (1.0 - a))
