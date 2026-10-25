"""DOUBLE CROSS, the OPPOSITE cut: the kit every scene shares.

  * the palette: OPPOSITE's. INK, PAPER, AMBER lamplight (here also the gold and the match), RED
    for the double-crosser, the teal NIGHT with STEEL distance, DEEP dark rooms, SHUT windows,
    POLICE blue for the end. GOLD and NAVY are aliases (AMBER, NIGHT) so the sets and the cast
    forked from DOUBLE CROSS (`bank.py`, `cast.py`, `faces.py`) draw in this palette unchanged;
  * OPPOSITE's annotation layer, re-exported from `films/opposite_full/kit.py`: dots, sight
    lines, marker rings, arrows, ripples, hand-cut numerals, footstep dots, callouts, the clock,
    the heartbeat, the moon and the far city;
  * DOUBLE CROSS's small devices, in this palette: ruled strokes (`chalk_line` and friends: here
    the plan's ink lines and the cut edges), dashes (what is underground), the alarm bell, the
    flashlight cone, a pool of light, the match and its light, a glint, the police light bar.

All drawing is in frame px (1080 x 1920, y down) as a pure function of time.
"""
import math

import cairo

from engine import bass, draw
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED
from engine.timing import timeline
from films.opposite_bass import world as B
from films.opposite_full import kit as OK

FILM = "double_cross_opposite"
W, H = 1080.0, 1920.0

INK = OK.INK
PAPER = OK.PAPER
AMBER = OK.AMBER                   # lamplight, the gold's glow, the match, the Cracker
RED = RED                          # the Knight and what he does; the rings; the ruby
NIGHT = OK.NIGHT                   # the teal night: every exterior field, the sewer's air
STEEL = OK.STEEL                   # the far city, moonlit stone and iron, the guard's rim
DEEP = OK.DEEP                     # a dark room at night
SHUT = OK.SHUT                     # an unlit window at night
POLICE = OK.POLICE                 # the police light's blue half (s09's end, s10)
UNLIT = OK.UNLIT
DIM = OK.DIM

# the forked DOUBLE CROSS modules' names for the same colours
GOLD = AMBER
NAVY = NIGHT

BPM = 120.0
BEAT = 60.0 / BPM

k = B.k
twos = B.twos
fill = B.fill
clip_rect = B.clip_rect
place = B.place
edged = B.edged

# OPPOSITE's annotation layer
dot = OK.dot
arrowhead = OK.arrowhead
dotted = OK.dotted
sight_line = OK.sight_line
marker_pts = OK.marker_pts
marker_ring = OK.marker_ring
arrow = OK.arrow
ripple = OK.ripple
numeral = OK.numeral
step_dots = OK.step_dots
callout = OK.callout
clock_face = OK.clock_face
heartbeat = OK.heartbeat
path_points = OK.path_points
moon = OK.moon
skyline = OK.skyline


def film_start(sid):
    """Film time (s) of scene sid's first frame, from the timeline."""
    return float(next(s["start"] for s in timeline(FILM)["scenes"] if s["id"] == sid))


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


def scene_setup(f, field=NIGHT):
    """The film's paper (OPPOSITE's settings): a flat field, fibres, ink mottling, grain on twos."""
    bass.bass_scene(f, field=field, paper=0.85, vignette=0.12, mottle=0.035, flicker=0.0)
    f.post["grain_fps"] = 12.0


# ============================================================================ polylines
def poly_len(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def poly_at(pts, s):
    """The point at arc length s along pts, and the unit direction there."""
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        if s <= d or (a, b) == (pts[-2], pts[-1]):
            u = clamp(s / d) if d > 0 else 0.0
            return (lerp(a[0], b[0], u), lerp(a[1], b[1], u)), ((b[0] - a[0]) / (d or 1.0), (b[1] - a[1]) / (d or 1.0))
        s -= d
    a, b = pts[-2], pts[-1]
    d = math.dist(a, b) or 1.0
    return b, ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def poly_cut(pts, s0, s1):
    """The piece of polyline pts between arc lengths s0 and s1."""
    out, acc = [], 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        lo, hi = max(s0, acc), min(s1, acc + d)
        if hi >= lo and d > 0:
            p0 = (lerp(a[0], b[0], (lo - acc) / d), lerp(a[1], b[1], (lo - acc) / d))
            p1 = (lerp(a[0], b[0], (hi - acc) / d), lerp(a[1], b[1], (hi - acc) / d))
            if not out or math.dist(out[-1], p0) > 1e-6:
                out.append(p0)
            out.append(p1)
        acc += d
    return out


def walk(route, step, t0, t1):
    """Footsteps along a polyline: points about `step` apart (the last one on the end) and the
    times they land, evenly from t0 to t1 (OPPOSITE s07's helper)."""
    L = poly_len(route) or 1.0
    n = max(1, round(L / step))
    pts = [poly_at(route, L * i / n)[0] for i in range(n + 1)]
    times = [lerp(t0, t1, i / n) for i in range(n + 1)]
    return pts, times


# ============================================================================ ruled strokes
def band_pts(pts, width, seed=0, taper=(1.0, 1.0), step=14.0, amp=0.6):
    """The outline of a band along pts that keeps every vertex, so corners stay square and small
    circles stay round (bass.line_band resamples at fixed arc steps and rounds them off): each
    segment is resampled at <= step px, corners are mitred, the width wobbles by amp."""
    P = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, P[-1]) > 1e-6:
            P.append(p)
    if len(P) < 2:
        return []
    total = poly_len(P) or 1.0
    out, nrm, arc = [], [], []
    acc = 0.0
    n = (0.0, 1.0)
    for i, (a, b) in enumerate(zip(P, P[1:])):
        d = math.dist(a, b)
        n = (-(b[1] - a[1]) / d, (b[0] - a[0]) / d)
        m = max(1, int(math.ceil(d / step)))
        for j in range(m):
            f = j / m
            out.append((lerp(a[0], b[0], f), lerp(a[1], b[1], f)))
            arc.append(acc + d * f)
            if j == 0 and i > 0:                     # a corner: mitre between the two normals
                p0 = nrm[-1]
                mx, my = p0[0] + n[0], p0[1] + n[1]
                ml = math.hypot(mx, my) or 1.0
                mx, my = mx / ml, my / ml
                kk = 1.0 / max(0.4, mx * n[0] + my * n[1])
                nrm.append((mx * kk, my * kk))
            else:
                nrm.append(n)
        acc += d
    out.append(P[-1])
    arc.append(total)
    nrm.append(n)
    left, right = [], []
    for i, (p, nn, s) in enumerate(zip(out, nrm, arc)):
        w = 0.5 * max(0.4, width * lerp(taper[0], taper[1], s / total) + amp * _sn(seed, i, 5))
        left.append((p[0] + nn[0] * w, p[1] + nn[1] * w))
        right.append((p[0] - nn[0] * w, p[1] - nn[1] * w))
    return bass.orient(left + right[::-1], True)


def band(c, pts, color=PAPER, width=5.0, seed=0, taper=(1.0, 1.0), alpha=1.0):
    poly = band_pts(pts, width, seed, taper)
    if poly:
        bass.fill_polys(c, [poly], color, alpha)


def chalk_line(c, pts, u=1.0, width=5.0, color=PAPER, seed=0, alpha=0.95, taper=(1.0, 1.0)):
    """A ruled stroke along pts, struck on to fraction u of its length (the plan's ink lines; the
    edges of a cut)."""
    if u <= 0.0 or len(pts) < 2:
        return
    L = poly_len(pts)
    part = poly_cut(pts, 0.0, L * clamp(u))
    if len(part) >= 2 and poly_len(part) > 0.5:
        band(c, part, color, width, seed, taper, alpha)


def chalk_rect(c, r, u=1.0, width=5.0, color=PAPER, seed=0, alpha=0.95):
    """A rectangle (x0, y0, x1, y1) outlined, drawn round from its top-left corner."""
    x0, y0, x1, y1 = r
    lap = min(width, (x1 - x0) / 2.0)
    chalk_line(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0), (x0 + lap, y0)], u, width, color, seed, alpha)


def chalk_circle(c, p, r, u=1.0, width=5.0, color=PAPER, seed=0, alpha=0.95, start=-90.0, n=None):
    """A circle drawn round clockwise from `start` degrees."""
    n = n or int(clamp(r * 0.6, 20, 96))
    pts = [(p[0] + r * math.cos(math.radians(start + 360.0 * i / n)),
            p[1] + r * math.sin(math.radians(start + 360.0 * i / n))) for i in range(n + 1)]
    chalk_line(c, pts, u, width, color, seed, alpha)


def dashes(c, pts, color=PAPER, width=4.0, dash=22.0, gap=14.0, u=1.0, seed=0, alpha=0.9):
    """A dashed line (what is underground: the sewer on the plan), drawn on to u."""
    L = poly_len(pts) * clamp(u)
    s, i = 0.0, 0
    while s < L:
        part = poly_cut(pts, s, min(s + dash, L))
        if len(part) >= 2 and poly_len(part) > 1.0:
            bass.line_band(c, part, color, width=width, seed=seed * 97 + i, alpha=alpha)
        s += dash + gap
        i += 1


def route(c, pts, u=1.0, color=PAPER, tail=0.0, r=6.5, gap=22.0, head=26.0, phase=0.0, seed=0, alpha=1.0):
    """A traced way along polyline pts: dots shown between fractions `tail` and `u` of its length,
    led by an arrowhead at the u end. phase (px) marches the dots."""
    L = poly_len(pts)
    s1, s0 = L * clamp(u), L * clamp(tail)
    if s1 - s0 < 2.0:
        return
    stop = s1 - (head * 0.95 + r if head > 0 else 0.0)
    s = s0 + (phase % gap)
    while s <= stop:
        g = min(1.0, (s - s0) / gap * 1.4 + 0.25, (stop - s) / (0.6 * gap) + 0.45)
        p, _ = poly_at(pts, s)
        dot(c, p, r * clamp(g), color, seed=seed * 131 + int(s // gap), alpha=alpha)
        s += gap
    if head > 0 and s1 - s0 > head * 0.8:
        p, d = poly_at(pts, s1)
        arrowhead(c, p, d, min(head, (s1 - s0) * 0.9), color, seed=seed, alpha=alpha)


def bell(c, p, s=1.0, color=PAPER, seed=0, alpha=1.0, ring=0.0):
    """The alarm bell, small (a dome with a clapper), as drawn on the plan. ring rocks it (deg)."""
    c.save()
    c.translate(*p)
    c.rotate(math.radians(ring))
    c.scale(s, s)
    dome = [(-16.0, 6.0), (-14.0, -4.0), (-10.0, -12.0), (0.0, -16.0), (10.0, -12.0), (14.0, -4.0), (16.0, 6.0),
            (20.0, 9.0), (-20.0, 9.0)]
    bass.fill_polys(c, [bass.orient(bass.cut(dome, seed=seed, amp=0.4, seg=(6.0, 12.0)), True)], color, alpha)
    dot(c, (0.0, 14.0), 4.5, color, seed=seed + 1, alpha=alpha)
    c.restore()


# ============================================================================ light
def cone(c, apex, ang, spread, length, color=PAPER, alpha=0.16, steps=3, seed=0):
    """A flashlight beam: flat translucent sectors from apex along `ang` (degrees, 0 = +x),
    half-angle `spread`, nested so the core is brighter (flat tints, no blur)."""
    for i in range(steps):
        f = 1.0 - i / steps
        sp = spread * (0.45 + 0.55 * f)
        L = length * (0.75 + 0.25 * f)
        n = 18
        pts = [apex] + [(apex[0] + L * math.cos(math.radians(ang - sp + 2 * sp * j / n)),
                         apex[1] + L * math.sin(math.radians(ang - sp + 2 * sp * j / n))) for j in range(n + 1)]
        bass.fill_polys(c, [bass.orient(pts, True)], color, alpha * (0.55 if i == 0 else 0.5))


def pool(c, p, rx, ry, color=AMBER, alpha=0.16, steps=4, add=True):
    """A pool of light: nested flat ellipses, brightest in the middle. add: the light adds to what
    it falls on instead of greying it."""
    c.save()
    if add:
        c.set_operator(cairo.OPERATOR_ADD)
    for i in range(steps):
        f = 1.0 - i / steps
        bass.fill_polys(c, [draw.ellipse_pts(p, rx * (0.35 + 0.65 * f), ry * (0.35 + 0.65 * f), n=72)], color,
                        alpha * 0.5)
    c.restore()


def flame(c, p, t, s=1.0, seed=0):
    """A match flame: an AMBER teardrop round a PAPER core, flickering on twos."""
    tt = twos(t)
    fl = 1.0 + 0.12 * math.sin(tt * 23.0 + seed) + 0.08 * _sn(int(tt * 12), seed)
    lean = 4.0 * math.sin(tt * 7.0 + seed)
    for col, sc in ((AMBER, 1.0), (PAPER, 0.5)):
        h, w = 46.0 * s * fl * sc, 15.0 * s * sc
        pts = [(p[0] + lean * sc + w * 0.1, p[1] - h)]
        for i in range(1, 16):
            a = math.pi * i / 16.0
            pts.append((p[0] + w * math.sin(a) * (1.0 if i > 8 else 0.85) + lean * sc * (1 - i / 16.0) * 0.4,
                        p[1] - h * 0.42 + h * 0.42 * (1 - math.cos(a)) * 0.95))
        pts.append((p[0] - w * 0.02, p[1] + h * 0.06))
        for i in range(1, 16):
            a = math.pi * (1 - i / 16.0)
            pts.append((p[0] - w * math.sin(a) + lean * sc * (i / 16.0) * 0.4,
                        p[1] - h * 0.42 + h * 0.42 * (1 - math.cos(a)) * 0.95))
        bass.fill_polys(c, [bass.orient(pts, True)], col)


def match_light(c, p, t, r=520.0, strength=1.0, seed=0):
    """The light of a match on the dark: AMBER rings, brightest close in, breathing with the flame."""
    tt = twos(t)
    fl = 1.0 + 0.05 * math.sin(tt * 17.0 + seed) + 0.03 * _sn(int(tt * 12), seed + 5)
    for i, a in enumerate((0.05, 0.06, 0.07, 0.09)):
        rr = r * fl * (1.0 - 0.21 * i)
        bass.fill_polys(c, [draw.circle_pts(p, rr, n=72)], AMBER, a * strength)


def twinkle(c, p, size, color=PAPER, u=1.0, rot=0.0, alpha=1.0):
    """A four-point glint (spectacles, the gold, the ruby): long and short rays, scaled by u."""
    if u <= 0.0:
        return
    pts = []
    for i in range(8):
        a = math.radians(rot + 45.0 * i)
        rr = size * u * (1.0 if i % 2 == 0 else 0.16)
        pts.append((p[0] + rr * math.cos(a), p[1] + rr * math.sin(a)))
    bass.fill_polys(c, [bass.orient(pts, True)], color, alpha)


def light_bar(c, p, t, s=1.0, seed=0):
    """A police car's light bar seen side on (blue and red halves flashing in turn), centred on p."""
    blue_on = (t * 3.0 + hash01(seed, 9)) % 1.0 < 0.5
    c.save()
    c.translate(*p)
    c.scale(s, s)
    bass.fill_polys(c, [bass.cut_rect(-22.0, -7.0, 0.0, 0.0, seed=seed, amp=0.3)], POLICE, 1.0 if blue_on else 0.45)
    bass.fill_polys(c, [bass.cut_rect(0.0, -7.0, 22.0, 0.0, seed=seed + 1, amp=0.3)], RED, 0.45 if blue_on else 1.0)
    c.restore()


def sweep(c, p, t, length=900.0, spread=16.0, alpha=0.10, seed=0, rate=260.0):
    """The two turning beams of a light bar at p: a flat POLICE sector and a flat RED one opposite,
    rotating (deg/s) about p (the police light washing the walls)."""
    rot = (t * rate + 97.0 * seed) % 360.0
    for col, off in ((POLICE, 0.0), (RED, 180.0)):
        a = rot + off
        pts = [p] + [(p[0] + length * math.cos(math.radians(a - spread + 2 * spread * j / 12)),
                      p[1] + length * math.sin(math.radians(a - spread + 2 * spread * j / 12))) for j in range(13)]
        bass.fill_polys(c, [bass.orient(pts, True)], col, alpha)
