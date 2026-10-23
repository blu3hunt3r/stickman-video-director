"""DOUBLE CROSS: the kit every scene shares.

  * the palette: cyanotype BLUE paper and PAPER chalk for the plan; NAVY night, STEEL distance
    and DEEP dark rooms for the world; GOLD for gold and lamplight; RED for the double-crosser;
    POLICE blue for the end;
  * the trilogy's annotation devices (dots, sight lines, marker rings, ripples, callouts, hand-cut
    numerals), re-exported from OPPOSITE's kit;
  * the plan's own handwriting: ruled chalk lines, routes (dotted chalk led by an arrowhead),
    circled step numerals, the X, the guard's flashlight cone, the heist stopwatch, chess
    pieces, the alarm bell, cars from above with their police light bars, the match, the
    tracing-paper sheet, the X-split screen and the rewind's marks.

All drawing is in frame px (1080 x 1920, y down) as a pure function of time, unless a function
says it draws in plan px (inside a P.PlanCam's ground transform).
"""
import math
from functools import lru_cache

from engine import bass, draw
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED
from films.opposite_bass import world as B
from films.opposite_full import kit as OK

W, H = 1080.0, 1920.0

INK = (0.018, 0.020, 0.026)
PAPER = B.PAPER                    # chalk
BLUE = (0.12, 0.27, 0.45)          # the blueprint
NAVY = (0.05, 0.09, 0.16)          # the night: sky, street, the sewer, the dark bank
STEEL = (0.16, 0.26, 0.38)         # moonlit planes, distance
DEEP = (0.035, 0.045, 0.065)       # a dark room; the table under the sheet
GOLD = B.AMBER                     # gold, the lamp, the match, the Cracker
POLICE = OK.POLICE                 # the police light's blue half (s10 only)
RED = RED

BPM = 120.0
BEAT = 60.0 / BPM

k = B.k
twos = B.twos
fill = B.fill
clip_rect = B.clip_rect
place = B.place
edged = B.edged

# the trilogy's annotation devices
dot = OK.dot
arrowhead = OK.arrowhead
dotted = OK.dotted
sight_line = OK.sight_line
marker_ring = OK.marker_ring
arrow = OK.arrow
ripple = OK.ripple
numeral = OK.numeral
step_dots = OK.step_dots
callout = OK.callout
heartbeat = OK.heartbeat
path_points = OK.path_points

# film-time beats every scene agrees on
HEIST_T0 = 46.0                    # the stopwatch starts (s04, the sewer)
HEIST_STOP = 93.5                  # it stops dead: he has crossed them (s07)


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


def scene_setup(f, field=NAVY):
    """The film's paper: a flat field (BLUE for plan shots, NAVY at night), fibres, grain on twos."""
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


# ============================================================================ chalk
def chalk_line(c, pts, u=1.0, width=5.0, color=PAPER, seed=0, alpha=0.95, taper=(1.0, 1.0)):
    """A ruled chalk stroke along pts, struck on to fraction u of its length."""
    if u <= 0.0 or len(pts) < 2:
        return
    L = poly_len(pts)
    part = poly_cut(pts, 0.0, L * clamp(u))
    if len(part) >= 2 and poly_len(part) > 0.5:
        bass.line_band(c, part, color, width=width, seed=seed, taper=taper, alpha=alpha)


def chalk_rect(c, r, u=1.0, width=5.0, color=PAPER, seed=0, alpha=0.95):
    """A rectangle (x0, y0, x1, y1) outlined in chalk, drawn round from its top-left corner."""
    x0, y0, x1, y1 = r
    chalk_line(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], u, width, color, seed, alpha)


def chalk_circle(c, p, r, u=1.0, width=5.0, color=PAPER, seed=0, alpha=0.95, start=-90.0, n=None):
    """A chalk circle drawn round clockwise from `start` degrees."""
    n = n or int(clamp(r * 0.6, 20, 96))
    pts = [(p[0] + r * math.cos(math.radians(start + 360.0 * i / n)),
            p[1] + r * math.sin(math.radians(start + 360.0 * i / n))) for i in range(n + 1)]
    chalk_line(c, pts, u, width, color, seed, alpha)


def dashes(c, pts, color=PAPER, width=4.0, dash=22.0, gap=14.0, u=1.0, seed=0, alpha=0.9):
    """A dashed chalk line (what is underground: the sewer), drawn on to u."""
    L = poly_len(pts) * clamp(u)
    s, i = 0.0, 0
    while s < L:
        part = poly_cut(pts, s, min(s + dash, L))
        if len(part) >= 2 and poly_len(part) > 1.0:
            bass.line_band(c, part, color, width=width, seed=seed * 97 + i, alpha=alpha)
        s += dash + gap
        i += 1


def route(c, pts, u=1.0, color=PAPER, tail=0.0, r=6.5, gap=22.0, head=26.0, phase=0.0, seed=0, alpha=1.0,
          solid=False, width=6.0):
    """A planned path along polyline pts: chalk dots (or a solid line) shown between fractions
    `tail` and `u` of its length, led by an arrowhead at the u end. phase (px) marches the dots."""
    L = poly_len(pts)
    s1, s0 = L * clamp(u), L * clamp(tail)
    if s1 - s0 < 2.0:
        return
    stop = s1 - (head * 0.95 + r if head > 0 else 0.0)
    if solid:
        part = poly_cut(pts, s0, max(s0, stop + r))
        if len(part) >= 2:
            bass.line_band(c, part, color, width=width, seed=seed, alpha=alpha)
    else:
        s = s0 + (phase % gap)
        while s <= stop:
            g = min(1.0, (s - s0) / gap * 1.4 + 0.25, (stop - s) / (0.6 * gap) + 0.45)
            p, _ = poly_at(pts, s)
            dot(c, p, r * clamp(g), color, seed=seed * 131 + int(s // gap), alpha=alpha)
            s += gap
    if head > 0 and s1 - s0 > head * 0.8:
        p, d = poly_at(pts, s1)
        arrowhead(c, p, d, min(head, (s1 - s0) * 0.9), color, seed=seed, alpha=alpha)


def circled(c, text, p, r=30.0, u=1.0, color=PAPER, width=5.0, seed=0, alpha=1.0):
    """A circled step numeral (①..⑤): the ring is drawn round, then the figure pops in."""
    chalk_circle(c, p, r, clamp(u / 0.7), width, color, seed, alpha, start=-110.0)
    g = ease("outback", clamp((u - 0.55) / 0.45))
    if g > 0.01:
        numeral(c, text, p, r * 1.15, color, seed=seed + 3, alpha=alpha, scale=g)


def xmark(c, p, size=60.0, u=1.0, color=PAPER, width=10.0, seed=0, alpha=1.0):
    """The X: two strokes, top-left to bottom-right, then top-right to bottom-left."""
    h = size / 2.0
    chalk_line(c, [(p[0] - h, p[1] - h), (p[0] + h, p[1] + h)], clamp(u * 2.0), width, color, seed, alpha,
               taper=(0.6, 1.0))
    chalk_line(c, [(p[0] + h, p[1] - h), (p[0] - h, p[1] + h)], clamp(u * 2.0 - 1.0), width, color, seed + 1,
               alpha, taper=(0.6, 1.0))


def chevron(c, p, size, d=(0.0, 1.0), color=PAPER, width=6.0, seed=0, alpha=1.0):
    """A chalk chevron pointing along d (the 'down here' mark on a manhole)."""
    nx, ny = -d[1], d[0]
    tip = (p[0] + d[0] * size * 0.45, p[1] + d[1] * size * 0.45)
    a = (p[0] - d[0] * size * 0.25 + nx * size * 0.5, p[1] - d[1] * size * 0.25 + ny * size * 0.5)
    b = (p[0] - d[0] * size * 0.25 - nx * size * 0.5, p[1] - d[1] * size * 0.25 - ny * size * 0.5)
    chalk_line(c, [a, tip, b], 1.0, width, color, seed, alpha)


def bell(c, p, s=1.0, color=PAPER, seed=0, alpha=1.0, ring=0.0):
    """The alarm bell (a dome with a clapper), drawn small on the plan. ring rocks it (degrees)."""
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


def pool(c, p, rx, ry, color=GOLD, alpha=0.16, steps=4, seed=0):
    """A pool of light: nested flat ellipses, brightest in the middle."""
    for i in range(steps):
        f = 1.0 - i / steps
        bass.fill_polys(c, [draw.ellipse_pts(p, rx * (0.35 + 0.65 * f), ry * (0.35 + 0.65 * f), n=64)], color,
                        alpha * 0.5)


def flame(c, p, t, s=1.0, seed=0):
    """A match flame: a gold teardrop round a paper core, flickering on twos."""
    tt = twos(t)
    fl = 1.0 + 0.12 * math.sin(tt * 23.0 + seed) + 0.08 * _sn(int(tt * 12), seed)
    lean = 4.0 * math.sin(tt * 7.0 + seed)
    for col, sc in ((GOLD, 1.0), (PAPER, 0.5)):
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
    """The light of a match on the dark: gold rings, brightest close in, breathing with the flame."""
    tt = twos(t)
    fl = 1.0 + 0.05 * math.sin(tt * 17.0 + seed) + 0.03 * _sn(int(tt * 12), seed + 5)
    for i, a in enumerate((0.05, 0.06, 0.07, 0.09)):
        rr = r * fl * (1.0 - 0.21 * i)
        bass.fill_polys(c, [draw.circle_pts(p, rr, n=72)], GOLD, a * strength)


def twinkle(c, p, size, color=PAPER, u=1.0, rot=0.0, alpha=1.0):
    """A four-point glint (a lens, the ruby): long and short rays, scaled by u."""
    if u <= 0.0:
        return
    pts = []
    for i in range(8):
        a = math.radians(rot + 45.0 * i)
        rr = size * u * (1.0 if i % 2 == 0 else 0.16)
        pts.append((p[0] + rr * math.cos(a), p[1] + rr * math.sin(a)))
    bass.fill_polys(c, [bass.orient(pts, True)], color, alpha)


# ============================================================================ the stopwatch
def heist_beats(ft):
    """Beats on the heist clock at film time ft: it starts at HEIST_T0, ticks on every beat (a
    quick snap with a settle) and stops dead at HEIST_STOP."""
    e = min(ft, HEIST_STOP) - HEIST_T0
    if e <= 0.0:
        return 0.0
    n = math.floor(e / BEAT)
    return n + ease("outback", clamp((e - n * BEAT) / 0.09))


def stopwatch(c, p, r, beats, color=PAPER, hand=None, u=1.0, seed=0, alpha=1.0):
    """The heist clock: a chalk ring with a crown, sixty ticks, a sweep hand at `beats` (one
    tick = one beat, a full turn in sixty), and the elapsed arc shaded. hand: the hand's colour
    (RED once he has crossed them). u scales it in."""
    if u <= 0.0:
        return
    rr = r * ease("outback", clamp(u))
    bass.fill_polys(c, [draw.circle_pts(p, rr, n=72)], INK, 0.55 * alpha)
    a = (beats % 60.0) / 60.0
    if a > 0.002:
        n = max(2, int(72 * a))
        pts = [p] + [(p[0] + rr * 0.86 * math.sin(2 * math.pi * a * i / n), p[1] - rr * 0.86 * math.cos(2 * math.pi * a * i / n))
                     for i in range(n + 1)]
        bass.fill_polys(c, [bass.orient(pts, True)], color, 0.16 * alpha)
    bass.ring(c, p, rr, max(3.0, rr * 0.08), color, seed=seed, n=72, alpha=alpha)
    bass.fill_polys(c, [bass.cut_rect(p[0] - rr * 0.12, p[1] - rr * 1.22, p[0] + rr * 0.12, p[1] - rr * 1.05,
                                      seed=seed + 1, amp=0.4)], color, alpha)
    for i in range(12):
        ang = 2 * math.pi * i / 12.0
        r0 = rr * (0.70 if i % 3 == 0 else 0.76)
        bass.line_band(c, [(p[0] + r0 * math.sin(ang), p[1] - r0 * math.cos(ang)),
                           (p[0] + rr * 0.86 * math.sin(ang), p[1] - rr * 0.86 * math.cos(ang))], color,
                       width=max(2.0, rr * (0.06 if i % 3 == 0 else 0.035)), seed=seed + 2 + i, alpha=alpha)
    ang = 2 * math.pi * a
    bass.line_band(c, [(p[0] - rr * 0.14 * math.sin(ang), p[1] + rr * 0.14 * math.cos(ang)),
                       (p[0] + rr * 0.8 * math.sin(ang), p[1] - rr * 0.8 * math.cos(ang))], hand or color,
                   width=max(2.5, rr * 0.07), seed=seed + 20, taper=(1.0, 0.4), alpha=alpha)
    dot(c, p, max(2.5, rr * 0.08), hand or color, seed=seed + 21, alpha=alpha)


# ============================================================================ chess pieces
# Staunton profiles, base at (0, 0), height about 100 units up (y negative), facing +x.
_BASE = [(-36.0, 0.0), (36.0, 0.0), (36.0, -6.0), (31.0, -10.0), (25.0, -13.0)]


def _piece_pts(kind):
    if kind == "pawn":
        right = _BASE + [(14.0, -20.0), (11.0, -36.0), (21.0, -40.0), (21.0, -45.0), (11.0, -48.0)]
        head = [(17.0 * math.sin(math.radians(a)), -66.0 - 17.0 * math.cos(math.radians(a))) for a in range(150, -1, -10)]
        return _mirror(right, head)
    if kind == "bishop":
        right = _BASE + [(14.0, -20.0), (10.0, -52.0), (20.0, -56.0), (20.0, -61.0), (10.0, -64.0), (13.0, -70.0)]
        mitre = [(16.0, -76.0), (18.0, -84.0), (16.0, -92.0), (10.0, -100.0), (4.0, -105.0), (5.0, -109.0),
                 (5.5, -113.0), (3.0, -116.0), (0.0, -117.0)]
        return _mirror(right, mitre)
    if kind == "queen":
        right = _BASE + [(15.0, -20.0), (11.0, -62.0), (23.0, -66.0), (23.0, -72.0), (12.0, -76.0), (16.0, -90.0),
                         (26.0, -102.0)]
        crown = [(21.0, -109.0), (17.0, -103.0), (11.0, -110.0), (7.0, -104.0), (5.0, -110.0), (7.0, -116.0),
                 (5.0, -121.0), (0.0, -123.0)]
        return _mirror(right, crown)
    if kind == "knight":
        return [(-36.0, 0.0), (36.0, 0.0), (36.0, -6.0), (31.0, -10.0), (25.0, -13.0), (22.0, -22.0), (24.0, -30.0),
                (22.0, -36.0),
                # throat, jaw, muzzle, nose, forehead, ear, mane
                (12.0, -44.0), (10.0, -54.0), (16.0, -62.0), (28.0, -66.0), (36.0, -72.0), (35.0, -80.0),
                (24.0, -92.0), (12.0, -100.0), (6.0, -112.0), (0.0, -103.0), (-6.0, -100.0), (-16.0, -92.0),
                (-24.0, -76.0), (-26.0, -60.0), (-24.0, -44.0), (-26.0, -36.0), (-24.0, -30.0), (-22.0, -22.0),
                (-25.0, -13.0), (-31.0, -10.0), (-36.0, -6.0)]
    raise ValueError(kind)


def _mirror(right, top):
    """A symmetric outline from its right half (base up) and the right half of its top."""
    half = right + top
    left = [(-x, y) for x, y in reversed(half[:-1])]
    return half + left[1:] if abs(half[-1][0]) < 1e-6 else half + left


@lru_cache(maxsize=None)
def _piece_poly(kind, seed):
    return bass.orient(bass.cut(_piece_pts(kind), seed=seed, amp=0.25, seg=(5.0, 14.0)), True)


def piece(c, kind, base, h=110.0, color=PAPER, edge=INK, squash=1.0, facing=1, tilt=0.0, seed=0, alpha=1.0,
          ew=5.0):
    """A chess piece standing at `base` (frame px), `h` px tall, squashed vertically by `squash`
    (the camera's elevation: 1 at eye level), tipped by `tilt` degrees about its base edge (it
    falls over). Edged in `edge` so a white piece shows on white and a black one on black."""
    s = h / 112.0
    c.save()
    c.translate(*base)
    if tilt:
        piv = 30.0 * s * (1.0 if tilt > 0 else -1.0)
        c.translate(piv, 0.0)
        c.rotate(math.radians(tilt))
        c.translate(-piv, 0.0)
    c.scale(s * facing, s * squash)
    poly = _piece_poly(kind, seed)
    if edge is not None:
        B.edged(c, [poly], color, edge, ew / max(s, 0.1))
    else:
        bass.fill_polys(c, [poly], color, alpha)
    if kind == "bishop":
        bass.line_band(c, [(-11.0, -84.0), (6.0, -101.0)], edge or INK, width=4.0, seed=seed + 1)
    c.restore()


def piece_disc(c, p, r, color, edge=INK, squash=1.0, seed=0, alpha=1.0):
    """A piece's base seen from above (a disc on the plan, foreshortened by squash)."""
    pts = draw.ellipse_pts(p, r, r * squash, n=40)
    if edge is not None:
        B.edged(c, [pts], color, edge, 4.0)
    else:
        bass.fill_polys(c, [pts], color, alpha)


# ============================================================================ cars from above
def car(c, p, ang, s=1.0, color=INK, edge=PAPER, ew=4.0, glass=None, seed=0, alpha=1.0):
    """A car seen from straight above, centred on p and heading along `ang` degrees (0 = +x):
    a rounded body, the windscreen and the rear window. About 120 x 56 px at s = 1."""
    L, Wd = 60.0, 28.0
    c.save()
    c.translate(*p)
    c.rotate(math.radians(ang))
    c.scale(s, s)
    body = []
    for i in range(10):
        a = math.radians(-90.0 + 180.0 * i / 9.0)
        body.append((L - 14.0 + 14.0 * math.cos(a), Wd * 0.92 * math.sin(a)))
    for i in range(10):
        a = math.radians(90.0 + 180.0 * i / 9.0)
        body.append((-L + 12.0 + 12.0 * math.cos(a), Wd * math.sin(a)))
    body = bass.orient(body, True)
    if edge is not None:
        B.edged(c, [body], color, edge, ew / s)
    else:
        bass.fill_polys(c, [body], color, alpha)
    g = glass or (edge if edge is not None else PAPER)
    bass.fill_polys(c, [bass.orient([(18.0, -21.0), (32.0, -16.0), (32.0, 16.0), (18.0, 21.0)], True)], g, 0.85)
    bass.fill_polys(c, [bass.orient([(-34.0, -19.0), (-26.0, -21.0), (-26.0, 21.0), (-34.0, 19.0)], True)], g, 0.6)
    c.restore()


def police_lights(c, p, ang, t, s=1.0, beams=True, seed=0):
    """A police car's light bar (blue and red halves flashing in turn) and its two turning beams."""
    ph = (t * 3.0 + hash01(seed, 9)) % 1.0
    blue_on = ph < 0.5
    c.save()
    c.translate(*p)
    c.rotate(math.radians(ang))
    c.scale(s, s)
    if beams:
        rot = (t * 260.0 + 97.0 * seed) % 360.0
        for col, off in ((POLICE, 0.0), (RED, 180.0)):
            a = rot + off
            sp = 22.0
            pts = [(0.0, 0.0)] + [(330.0 * math.cos(math.radians(a - sp + 2 * sp * j / 10)),
                                   330.0 * math.sin(math.radians(a - sp + 2 * sp * j / 10))) for j in range(11)]
            bass.fill_polys(c, [bass.orient(pts, True)], col, 0.12)
    bass.fill_polys(c, [bass.cut_rect(-6.0, -20.0, 6.0, 0.0, seed=seed, amp=0.3)], POLICE, 1.0 if blue_on else 0.45)
    bass.fill_polys(c, [bass.cut_rect(-6.0, 0.0, 6.0, 20.0, seed=seed + 1, amp=0.3)], RED, 0.45 if blue_on else 1.0)
    c.restore()


# ============================================================================ the tracing sheet
def tracing_rect(rect, u):
    """Where the tracing sheet is at slide progress u: it comes down from above the frame."""
    x0, y0, x1, y1 = rect
    dy = -(1.0 - ease("out3", clamp(u))) * (y1 + 40.0)
    return (x0, y0 + dy, x1, y1 + dy)


def tracing(c, rect, u=1.0, alpha=0.20, seed=0):
    """The tracing paper: a translucent sheet with a crisp edge and one lifted corner, sliding in
    from the top (u = 1: at rest on `rect`). Returns where it is, for drawing on it."""
    r = tracing_rect(rect, u)
    if u <= 0.0:
        return r
    x0, y0, x1, y1 = r
    sheet = bass.cut([(x0, y0), (x1, y0), (x1, y1 - 70.0), (x1 - 70.0, y1), (x0, y1)], seed=seed, amp=1.2)
    bass.fill_polys(c, [bass.orient(sheet, True)], PAPER, alpha)
    bass.line_band(c, sheet + sheet[:1], PAPER, width=3.0, seed=seed + 1, alpha=0.5)
    curl = [(x1, y1 - 70.0), (x1 - 70.0, y1), (x1 - 52.0, y1 - 52.0)]
    bass.fill_polys(c, [bass.orient(curl, True)], PAPER, alpha * 1.8)
    return r


# ============================================================================ the X-split
def x_split(c, panels, seam=PAPER, seam_w=12.0, seam_u=1.0, centre=(W / 2.0, H / 2.0)):
    """The frame cut on both diagonals into four triangles. panels: {'top', 'right', 'bottom',
    'left'} -> fn(c), each drawing a whole frame that is shown only in its triangle. The seams
    run out from the centre to seam_u."""
    cx, cy = centre
    tri = {"top": [(0.0, 0.0), (W, 0.0), (cx, cy)], "right": [(W, 0.0), (W, H), (cx, cy)],
           "bottom": [(W, H), (0.0, H), (cx, cy)], "left": [(0.0, H), (0.0, 0.0), (cx, cy)]}
    for name, fn in panels.items():
        if fn is None:
            continue
        c.save()
        c.new_path()
        draw.poly(c, tri[name])
        c.clip()
        fn(c)
        c.restore()
    if seam_u > 0.0 and seam is not None:
        for corner in ((0.0, 0.0), (W, 0.0), (W, H), (0.0, H)):
            e = (lerp(cx, corner[0], clamp(seam_u)), lerp(cy, corner[1], clamp(seam_u)))
            bass.line_band(c, [(cx, cy), e], seam, width=seam_w, seed=int(corner[0] + corner[1]))


# ============================================================================ the rewind
def rewind_marks(c, t, alpha=1.0, seed=0):
    """Over replayed frames: chalk streaks that jump every frame (a tape scrubbing back) and a
    double chevron pointing back, top left."""
    f = int(t * 24.0)
    for i in range(5):
        y = H * hash01(f, i, seed)
        h = 3.0 + 10.0 * hash01(f, i, seed + 1)
        bass.fill_polys(c, [bass.cut_rect(-10.0, y, W + 10.0, y + h, seed=f * 7 + i, amp=0.5)], PAPER,
                        alpha * (0.10 + 0.18 * hash01(f, i, seed + 2)))
    for j in range(2):
        tip = (96.0 + 52.0 * j, 150.0)
        pts = [tip, (tip[0] + 50.0, 118.0), (tip[0] + 50.0, 182.0)]
        bass.fill_polys(c, [bass.orient(pts, True)], PAPER, alpha * 0.9)
