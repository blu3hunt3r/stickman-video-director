"""THIN ICE: what the director's scenes share (s01-s03, s08-s12): the title and its crack, the
searchlight's clock, the guard's lantern hold, small helpers.

The searchlight sweeps the zone between the fence and the woods on one clock for the whole film
(film time): its lit patch passes over the crossing at film 19 (going east) and 25 (going west),
s02's two near misses. Before that it passes them at film 9 on s01's map (going west), and it is
at the far west end of its swing (x -7) as s01 ends.
"""
import math
from functools import lru_cache

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from films.thin_ice import kit as K, world as W

# ============================================================================ the searchlight's clock
SWEEP_P = 16.0          # s per full swing (there and back)
SWEEP_T_EAST = 22.0     # film time it reaches the east end of its swing
SWEEP_X0 = 27.0         # the middle of the swing (m) ...
SWEEP_A = 34.0          # ... and half its width: x -7 .. 61; over the crossing (x 40) at film 9, 19, 25, 35, 41 ...


def search_x(ft):
    """The searchlight patch's map x at film time ft."""
    return SWEEP_X0 + SWEEP_A * math.cos(2.0 * math.pi * (ft - SWEEP_T_EAST) / SWEEP_P)


def search_n(ft):
    """Its map n: 3 m inside the wire at the crossing (its edge slides over the drift there, a
    stride short of where they crouch), curving away from the wire toward the ends."""
    u = (search_x(ft) - W.CROSS[0]) / SWEEP_A
    return W.FENCE_N + 3.0 + 1.0 * u * u


def search_heading(ft):
    """Map heading (degrees from north) from the tower to the patch."""
    x, n = search_x(ft), search_n(ft)
    return math.degrees(math.atan2(x - W.TOWER[0], n - W.TOWER[1]))


# ============================================================================ the title
@lru_cache(maxsize=None)
def title_glyphs():
    return bass.title_glyphs("THIN\nICE", width=840.0, tracking=0.06, seed=11, rough=0.8, jitter=0.45, leading=1.12)


TITLE_C = (540.0, 880.0)


@lru_cache(maxsize=None)
def crack_line():
    """The title's crack: a jagged line across the whole frame, upper left to lower right,
    through the title (frame px)."""
    a, b = (-30.0, 600.0), (1110.0, 1170.0)
    n = 26
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    nx, ny = dy / L, -dx / L
    pts = []
    for i in range(n + 1):
        u = i / n
        j = 0.0 if i in (0, n) else 22.0 * K._sn(i, 401) + 9.0 * K._sn(i, 402)
        pts.append((a[0] + dx * u + nx * j, a[1] + dy * u + ny * j))
    return tuple(pts)


def crack_normal():
    a, b = crack_line()[0], crack_line()[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dy / L, -dx / L)          # pointing up and to the right (the upper floe's side)


@lru_cache(maxsize=None)
def crack_branches():
    """Short side cracks off the main one: (start index, polyline)."""
    out = []
    pts = crack_line()
    for k, i in enumerate((5, 9, 13, 17, 21)):
        p = pts[i]
        side = 1 if k % 2 == 0 else -1
        ang = math.radians(-26.6 + side * (50.0 + 20.0 * K._sn(k, 411)))
        L = 70.0 + 50.0 * hash01(k, 412)
        q = [p]
        for j in range(1, 4):
            u = j / 3.0
            q.append((p[0] + math.cos(ang) * L * u + 8.0 * K._sn(k, j, 413), p[1] + math.sin(ang) * L * u + 8.0 * K._sn(k, j, 414)))
        out.append((i, tuple(q)))
    return tuple(out)


def floe_regions(off, rot):
    """The two halves' clip polygons (upper/right, lower/left) for an opening `off` px each side
    and a rotation `rot` degrees each (upper turns -rot, lower +rot) about the title's centre."""
    pts = crack_line()
    n = crack_normal()
    up = [xf((p[0] + n[0] * 0.0, p[1] + n[1] * 0.0), off, -rot, +1) for p in pts]
    lo = [xf(p, off, rot, -1) for p in pts]
    upper = up + [xf((1400.0, -400.0), off, -rot, +1), xf((-400.0, -400.0), off, -rot, +1)]
    lower = lo + [xf((1400.0, 2400.0), off, rot, -1), xf((-400.0, 2400.0), off, rot, -1)]
    return upper, lower


def xf(p, off, rot, side):
    """A point of one floe, opened `off` px along the crack's normal (side +1 upper, -1 lower) and
    turned `rot` degrees about the title's centre."""
    n = crack_normal()
    cx, cy = TITLE_C
    a = math.radians(rot)
    x, y = p[0] - cx, p[1] - cy
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return (cx + x + n[0] * off * side, cy + y + n[1] * off * side)


def draw_title_floes(c, color, off=0.0, rot=0.0, alpha=1.0, letters=None):
    """The title's letters on their two floes (each clipped to its side of the crack, opened and
    turned). letters(i) -> (dx, dy, rot, alpha) per letter or None (hidden), for the assembly."""
    T = title_glyphs()
    upper, lower = floe_regions(off, rot)
    for region, side, r in ((upper, +1, -rot), (lower, -1, rot)):
        c.save()
        c.new_path()
        bass.draw.poly(c, region)
        c.clip()
        n = crack_normal()
        cx, cy = TITLE_C
        c.translate(cx + n[0] * off * side, cy + n[1] * off * side)
        c.rotate(math.radians(r))
        for i, g in enumerate(T):
            tr = letters(i) if letters is not None else (0.0, 0.0, 0.0, 1.0)
            if tr is None:
                continue
            dx, dy, gr, a = tr
            c.new_path()
            g.path(c, (0.0, 0.0), dx, dy, gr, 1.0, 1.0)
            bass._set(c, color, alpha * a)
            c.fill()
        c.restore()


def title_path(c, off=0.0, rot=0.0):
    """The title's outlines as the current path (both floes, opened): for the page's flood."""
    T = title_glyphs()
    n = crack_normal()
    cx, cy = TITLE_C
    c.new_path()
    for side, r in ((+1, -rot), (-1, rot)):
        c.save()
        c.translate(cx + n[0] * off * side, cy + n[1] * off * side)
        c.rotate(math.radians(r))
        for g in T:
            bass.path_polys(c, g.polys)
        c.restore()


# ============================================================================ small helpers
def pan_of(x):
    """A sound's pan from a frame x."""
    return round(clamp((x - 540.0) / 540.0, -1.0, 1.0) * 0.8, 3)


def beat(t, t0, dur=0.25, e="out3"):
    return ease(e, clamp((t - t0) / dur))
