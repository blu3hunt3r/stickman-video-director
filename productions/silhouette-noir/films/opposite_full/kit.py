"""OPPOSITE (the full Bass cut): the kit every scene shares.

  * the palette: the Bass cut's ink, paper, amber and red, and the night: a deep teal field
    with steel-blue distance (the colour of the film's exteriors);
  * the annotation layer: the film's own handwriting over the story, the way a detective
    marks up a photograph. Sight lines (dotted, with an arrowhead: hers paper, his red), marker
    rings (a red marker pen circling what matters), footstep dots, arrows, ripples, hand-cut
    numerals, callouts (a lens on a leader line) and a clock;
  * the street, seen two ways: ELEVATION, the two facades of the Bass cut on the night field
    (her window low on the left building, his high on the right), and SECTION, the same two
    buildings cut open like a doll's house (floors, stairs, rooms, her fire escape, the
    street between them), the diagram the chase is drawn on.

All drawing is in frame px (1080 x 1920, y down) as a pure function of time. Scenes import
this module as K and the Bass cut's world (figures, shots) as B.
"""
import math
from functools import lru_cache

import cairo

from engine import bass, draw
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED
from films.opposite_bass import world as B

W, H = 1080.0, 1920.0
INK = B.INK
PAPER = B.PAPER
AMBER = B.AMBER
UNLIT = B.UNLIT
DIM = B.DIM
NIGHT = (0.10, 0.23, 0.27)        # the night: sky, street, every exterior field
STEEL = (0.20, 0.36, 0.40)        # the city behind, moonlit edges
DEEP = (0.055, 0.10, 0.12)        # a dark room at night
SHUT = (0.085, 0.10, 0.11)        # an unlit window at night
POLICE = (0.42, 0.82, 0.95)       # the police light's blue half (the end only)

BPM = 120.0
BEAT = 60.0 / BPM

k = B.k
twos = B.twos
fill = B.fill
clip_rect = B.clip_rect
place = B.place
edged = B.edged


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d, d


def scene_setup(f):
    """The film's paper: the Bass cut's settings (the grain on twos, with the figures)."""
    bass.bass_scene(f, field=INK, paper=0.85, vignette=0.12, mottle=0.035, flicker=0.0)
    f.post["grain_fps"] = 12.0


# ============================================================================ annotation layer
def dot(c, p, r, color, seed=0, alpha=1.0):
    """One cut-paper dot."""
    if r <= 0.3:
        return
    n = int(clamp(round(r * 1.3), 9, 28))
    bass.fill_polys(c, [bass.ring_pts(p, r, seed=seed, n=n, amp=min(0.6, 0.07 * r))], color, alpha)


def arrowhead(c, tip, d, size, color, seed=0, alpha=1.0):
    """A cut-paper arrowhead with its tip at `tip`, pointing along unit vector d."""
    nx, ny = -d[1], d[0]
    bx, by = tip[0] - d[0] * size, tip[1] - d[1] * size
    pts = [tip, (bx + nx * size * 0.52, by + ny * size * 0.52), (bx + d[0] * size * 0.18, by + d[1] * size * 0.18),
           (bx - nx * size * 0.52, by - ny * size * 0.52)]
    pts = [(x + 0.8 * _sn(seed, i, 1), y + 0.8 * _sn(seed, i, 2)) for i, (x, y) in enumerate(pts)]
    bass.fill_polys(c, [bass.orient(pts, True)], color, alpha)


def dotted(c, a, b, color, lead=1.0, tail=0.0, r=7.0, gap=25.0, phase=0.0, head=28.0, seed=0, alpha=1.0):
    """Dots from a toward b, shown between fractions `tail` and `lead` of the way, an arrowhead
    at the lead end (head=0: none). `phase` (px) slides the dots along the line (marching)."""
    dx, dy, L = _unit(a, b)
    s1, s0 = L * clamp(lead), L * clamp(tail)
    if s1 - s0 < 2.0:
        return
    stop = s1 - (head * 0.95 + r if head > 0 else 0.0)
    s = s0 + (phase % gap)
    i = 0
    while s <= stop:
        # dots shrink in at the tail end and against the arrowhead, so marching never pops
        g = min(1.0, (s - s0) / gap * 1.4 + 0.25, (stop - s) / (0.6 * gap) + 0.45)
        dot(c, (a[0] + dx * s, a[1] + dy * s), r * clamp(g), color, seed=seed * 131 + int(s // gap), alpha=alpha)
        s += gap
        i += 1
    if head > 0 and s1 - s0 > head * 0.8:
        sz = min(head, (s1 - s0) * 0.9)
        arrowhead(c, (a[0] + dx * s1, a[1] + dy * s1), (dx, dy), sz, color, seed=seed, alpha=alpha)


def sight_line(c, a, b, t, t0, color=PAPER, dur=0.45, off=None, off_dur=0.3, march=30.0, r=7.0, gap=25.0,
               head=28.0, seed=0, alpha=1.0):
    """A look, drawn as the film draws looks: dots flying from the eye `a` to what it sees `b`
    (from t0, over dur), an arrowhead in front; held, the dots march on toward b; at `off`
    the tail runs after the head and the line is gone."""
    if t < t0:
        return
    lead = k(t, t0, dur, "out3")
    tail = k(t, off, off_dur, "in3") if off is not None else 0.0
    if tail >= 0.999:
        return
    dotted(c, a, b, color, lead=lead, tail=tail, r=r, gap=gap, phase=march * (t - t0), head=head, seed=seed,
           alpha=alpha)


def marker_pts(center, rx, ry, u=1.0, width=14.0, tilt=-8.0, turns=1.16, start=-128.0, seed=0):
    """Outline of a marker-pen ring round `center`: one quick loop and a bit (it overshoots
    where it began, a little wider: a hand did it), thick in the middle of the stroke and
    thin at both ends. u (0..1) draws it on; the shape of the finished ring never changes."""
    total = 360.0 * turns
    shown = total * clamp(u)
    if shown < 4.0:
        return []
    ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    n = int(total / 4.0)
    pts, ws = [], []
    for i in range(n + 1):
        a = total * i / n
        last = a >= shown
        a = min(a, shown)
        f = a / total
        g = 1.0 + 0.085 * f + 0.022 * math.sin(math.radians(2.0 * a) + seed) + 0.004 * _sn(seed, i, 3)
        th = math.radians(start + a)
        x, y = rx * g * math.cos(th), ry * g * math.sin(th)
        pts.append((center[0] + x * ca - y * sa, center[1] + x * sa + y * ca))
        ws.append(width * (0.22 + 0.78 * math.sin(math.pi * f) ** 0.45) + 0.6 * _sn(seed, i, 4))
        if last:
            break
    if len(pts) < 2:
        return []
    return bass.orient(draw.ribbon(pts, ws), True)


def marker_ring(c, center, rx, ry=None, u=1.0, color=RED, width=14.0, tilt=-8.0, turns=1.16, start=-128.0,
                seed=0, alpha=1.0):
    pts = marker_pts(center, rx, rx if ry is None else ry, u, width, tilt, turns, start, seed)
    if pts:
        bass.fill_polys(c, [pts], color, alpha)


def arrow(c, a, b, color, width=16.0, head=40.0, u=1.0, seed=0, alpha=1.0):
    """A straight cut-paper arrow from a to b, drawn on to u."""
    dx, dy, L = _unit(a, b)
    s = L * clamp(u)
    if s < 2.0:
        return
    shaft = max(0.0, s - head * 0.8)
    if shaft > 1.0:
        bass.line_band(c, [a, (a[0] + dx * shaft, a[1] + dy * shaft)], color, width=width, seed=seed, alpha=alpha)
    arrowhead(c, (a[0] + dx * s, a[1] + dy * s), (dx, dy), min(head, s), color, seed=seed, alpha=alpha)


def ripple(c, p, t, t0, color, n=3, every=0.16, life=0.7, r0=10.0, r1=110.0, width=6.0, seed=0, alpha=1.0):
    """Rings spreading out of p (a sound, a listener, a heartbeat): each thins as it grows."""
    for i in range(n):
        a = (t - t0 - i * every) / life
        if not 0.0 <= a < 1.0:
            continue
        r = lerp(r0, r1, ease("out3", a))
        w = width * (1.0 - a) + 0.6
        bass.ring(c, p, r, w, color, seed=seed + 7 * i, alpha=alpha * (1.0 - 0.5 * a))


@lru_cache(maxsize=None)
def _glyphs(text, height, seed):
    return bass.title_glyphs(text, height=height, seed=seed, rough=0.8, jitter=0.5)


def numeral(c, text, p, height, color, seed=0, rot=0.0, alpha=1.0, scale=1.0):
    """Hand-cut figures (floor numbers, the dial): centred on p."""
    bass.draw_title(c, _glyphs(text, float(height), seed), p, color, rot=rot, alpha=alpha, scale=scale)


def step_dots(c, pts, times, t, color, r=10.0, line=None, seed=0, alpha=1.0):
    """Footsteps: dot i lands at times[i] (a little pop) and stays. line: (width, color) of a
    thin thread joining the landed dots, or None."""
    shown = [i for i, ti in enumerate(times) if t >= ti]
    if not shown:
        return
    if line is not None and len(shown) > 1:
        bass.line_band(c, [pts[i] for i in shown], line[1], width=line[0], seed=seed, alpha=alpha)
    for i in shown:
        g = ease("outback", clamp((t - times[i]) / 0.14))
        dot(c, pts[i], r * g, color, seed=seed * 17 + i, alpha=alpha)


def callout(c, anchor, center, r, inside, u=1.0, color=PAPER, ring_w=9.0, dot_r=9.0, line_w=4.0, seed=0):
    """A lens on a leader line: a circular inset at `center` showing `inside(c)` (drawn in
    frame px, clipped to the lens), joined by a thin line to a dot at `anchor`."""
    if u <= 0.0:
        return
    rr = r * ease("outback", clamp(u))
    dx, dy, d = _unit(anchor, center)
    if d > rr + 4.0:
        e = (center[0] - dx * rr, center[1] - dy * rr)
        bass.line_band(c, [anchor, e], color, width=line_w, seed=seed)
    dot(c, anchor, dot_r, color, seed=seed)
    c.save()
    c.new_path()
    bass.iris_path(c, center, rr, seed=seed, n=72)
    c.clip()
    c.translate(*center)
    c.scale(rr / r, rr / r)
    c.translate(-center[0], -center[1])
    inside(c)
    c.restore()
    bass.ring(c, center, rr, ring_w, color, seed=seed, n=72)


def clock_face(c, p, r, hh, mm, face=PAPER, ink=INK, seed=0):
    """A wall clock: a paper disc, twelve dots, two hands."""
    bass.fill_polys(c, [bass.ring_pts(p, r, seed=seed, n=48, amp=0.4)], face)
    for i in range(12):
        a = math.radians(i * 30.0 - 90.0)
        dot(c, (p[0] + 0.8 * r * math.cos(a), p[1] + 0.8 * r * math.sin(a)), r * (0.085 if i % 3 else 0.12), ink,
            seed=seed + i)
    for ang, L, w in ((((hh % 12) + mm / 60.0) * 30.0, 0.5, 0.11), (mm * 6.0, 0.74, 0.07)):
        a = math.radians(ang - 90.0)
        bass.line_band(c, [p, (p[0] + L * r * math.cos(a), p[1] + L * r * math.sin(a))], ink, width=w * r * 2.0,
                       seed=seed)
    dot(c, p, r * 0.1, ink, seed=seed)


def heartbeat(c, p, t, color=RED, bpm=96.0, r0=40.0, r1=520.0, width=18.0, life=1.4, seed=0, alpha=1.0):
    """Her heart: rings thudding out of p (lub-dub), thinning as they go."""
    bass.heartbeat(c, p, t, color=color, bpm=bpm, r0=r0, r1=r1, width=width, life=life, core=False, seed=seed,
                   alpha=alpha)


def path_points(pts, step):
    """Evenly spaced points along a polyline, `step` px apart (footstep positions)."""
    out = [pts[0]]
    carry = 0.0
    for a, b in zip(pts, pts[1:]):
        dx, dy, L = _unit(a, b)
        s = step - carry
        while s <= L:
            out.append((a[0] + dx * s, a[1] + dy * s))
            s += step
        carry = L - (s - step)
    return out


# ============================================================================ the night
MOON_E = (840.0, 230.0)          # the moon over the street, elevation
MOON_S = (540.0, 300.0)          # ... and in the section, over the gap between the roofs


def moon(c, p, r=78.0, color=PAPER):
    bass.fill_polys(c, [bass.ring_pts(p, r, seed=3, n=56, amp=0.5)], color)


@lru_cache(maxsize=1)
def _skyline():
    """The city behind: steel slabs with a few dim windows (static, cut once)."""
    rects = []
    x = -30.0
    i = 0
    while x < W + 30.0:
        w = 120.0 + 150.0 * hash01(i, 71)
        top = 330.0 + 380.0 * hash01(i, 72)
        rects.append((x, top, x + w, H + 20.0, i))
        x += w + 8.0 + 30.0 * hash01(i, 73)
        i += 1
    wins = []
    for x0, y0, x1, y1, j in rects:
        for row in range(14):
            for col in range(3):
                if hash01(j, row, col, 74) < 0.16:
                    wx = x0 + 18.0 + col * (x1 - x0 - 36.0) / 3.0
                    wy = y0 + 30.0 + row * 70.0
                    wins.append((wx, wy, wx + 22.0, wy + 34.0, hash01(j, row, col, 75)))
    return [(bass.cut_rect(x0, y0, x1, y1, seed=500 + j, amp=1.0)) for x0, y0, x1, y1, j in rects], wins


def skyline(c, color=STEEL, lit=0.0, t=0.0):
    """The far city; `lit` (0..1) lights its windows one after another (the end)."""
    slabs, wins = _skyline()
    bass.fill_polys(c, slabs, color)
    dark = lerp(color, INK, 0.45)
    for x0, y0, x1, y1, h in wins:
        on = lit > 0.0 and h < lit
        bass.fill_polys(c, [bass.cut_rect(x0, y0, x1, y1, seed=int(x0 * 7 + y0), amp=0.5)], AMBER if on else dark)


# ============================================================================ ELEVATION
def window_color(r, tb):
    """B.window_color on the night field: the unlit windows go cold."""
    col = B.window_color(r, tb)
    return SHUT if col == B.UNLIT else col


def draw_elevation(c, tb, field=NIGHT, with_moon=True, with_city=True, figures=True):
    """The Bass cut's street (two slabs, her window low on the left, his high on the right) at
    Bass-cut time tb, on the night field. Returns B.draw_windows' anchors."""
    fill(c, field)
    if with_city:
        skyline(c)
    if with_moon:
        moon(c, MOON_E)
    for j, Bk in enumerate((B.LEFT_B, B.RIGHT_B)):
        bass.fill_polys(c, [bass.cut_rect(*Bk, seed=20 + j)], INK)
    if not figures:
        for r in B.LEFT_WIN + B.RIGHT_WIN:
            bass.fill_polys(c, [bass.cut_rect(*r, seed=int(r[0] + r[1]))], window_color(r, tb))
        return {}
    anchors = {}
    for r in B.LEFT_WIN + B.RIGHT_WIN:
        bass.fill_polys(c, [bass.cut_rect(*r, seed=int(r[0] + r[1]))], window_color(r, tb))
    if B.T_WIN - 0.6 <= tb and not B.her_light_off(tb):
        c.save()
        clip_rect(c, B.HER_WIN)
        anchors["her_hand"] = B.draw_her_window(c, tb)
        c.restore()
    if B.his_on(tb):
        c.save()
        clip_rect(c, B.HIS_WIN)
        if tb < B.T_ARM:
            B.draw_room_small(c, tb)
        elif tb < B.T_GONE:
            anchors["his_shoulder"] = B.draw_him_alone(c, tb)
        c.restore()
    return anchors


# ============================================================================ SECTION
GROUND = 1700.0                   # street level
FH = 212.0                        # floor to floor
SLAB = 16.0
WALL = 14.0
STAIR_W = 92.0
HER_FLOOR, HIS_FLOOR = 4, 5       # her room, his room (his is a floor higher: she looks up at it)


def level(n):
    """y of the floor of storey n (1 = the street floor)."""
    return GROUND - (n - 1) * FH


class Building:
    """One of the two buildings in section. side: +1 if the street is on its right (hers),
    -1 if on its left (his). The stairs run up the side away from the street; the rooms face
    the street, each with a window in the street wall and a door into the stairwell."""

    def __init__(self, x0, x1, floors, side, seed):
        self.x0, self.x1, self.floors, self.side, self.seed = x0, x1, floors, side, seed
        self.roof = level(floors + 1)
        if side > 0:
            self.stair = (x0 + WALL, x0 + WALL + STAIR_W)
            self.part = (self.stair[1], self.stair[1] + WALL)
            self.rooms = (self.part[1], x1 - WALL)
            self.street = (x1 - WALL, x1)
        else:
            self.stair = (x1 - WALL - STAIR_W, x1 - WALL)
            self.part = (self.stair[0] - WALL, self.stair[0])
            self.rooms = (x0 + WALL, self.part[0])
            self.street = (x0, x0 + WALL)

    @property
    def face(self):
        """x of the street face."""
        return self.x1 if self.side > 0 else self.x0

    def room(self, n):
        """Inside of storey n's room: (x0, y0, x1, y1)."""
        return (self.rooms[0], level(n + 1) + SLAB / 2, self.rooms[1], level(n) - SLAB / 2)

    def floor_y(self, n):
        """Where feet stand in storey n."""
        return level(n) - SLAB / 2

    def window(self, n):
        """The window opening in the street wall of storey n: (x0, y0, x1, y1)."""
        return (self.street[0], level(n + 1) + 58.0, self.street[1], level(n) - 44.0)

    def door(self, n):
        """The door from storey n's room to the stairwell (an opening in the partition)."""
        return (self.part[0], self.floor_y(n) - 136.0, self.part[1], self.floor_y(n))

    def street_door(self):
        return (self.street[0], GROUND - 150.0, self.street[1], GROUND - SLAB / 2)

    def landing(self, n):
        """(x, y) of the stair landing at storey n's floor, by the door."""
        x = self.stair[1] - 20.0 if self.side > 0 else self.stair[0] + 20.0
        return (x, self.floor_y(n))

    def mid(self, n):
        """(x, y) of the half landing between storey n and n+1, against the outer wall."""
        x = self.stair[0] + 20.0 if self.side > 0 else self.stair[1] - 20.0
        return (x, self.floor_y(n) - FH / 2.0)

    def stair_route(self, n0, n1):
        """Polyline up (or down) the stairs from storey n0's landing to storey n1's, where feet
        go (a little above the flights)."""
        pts = []
        lo, hi = min(n0, n1), max(n0, n1)
        for n in range(lo, hi):
            pts += [self.landing(n), self.mid(n)]
        pts.append(self.landing(hi))
        return pts if n0 <= n1 else pts[::-1]


HER_B = Building(40.0, 380.0, 5, +1, seed=600)
HIS_B = Building(700.0, 1040.0, 6, -1, seed=700)
STREET = (HER_B.x1, HIS_B.x0)     # the gap
CURB = 40.0                       # sidewalk width each side
LAMP = (HIS_B.x0 - 26.0, GROUND)  # the street lamp, on his side
ESCAPE_X = (HER_B.x1, HER_B.x1 + 64.0)     # her fire escape, out over the sidewalk


def her_room():
    return HER_B.room(HER_FLOOR)


def his_room():
    return HIS_B.room(HIS_FLOOR)


def her_window():
    return HER_B.window(HER_FLOOR)


def his_window():
    return HIS_B.window(HIS_FLOOR)


def escape_platform(n):
    """(x0, y, x1) of her fire escape's platform at storey n (2..5)."""
    return (ESCAPE_X[0], level(n), ESCAPE_X[1])


def escape_route(n0=HER_FLOOR, n1=2):
    """Down her fire escape from storey n0's platform to n1's, zig-zagging."""
    pts = []
    for n in range(n0, n1, -1):
        y0, y1 = level(n) - 4.0, level(n - 1) - 4.0
        a, b = (ESCAPE_X[0] + 12.0, y0), (ESCAPE_X[1] - 10.0, y0)
        pts += [a, b] if (n0 - n) % 2 == 0 else [b, a]
    pts.append((pts[-1][0], level(n1) - 4.0))
    return pts


# --- furniture, in room-floor coordinates: x along the floor, y up (negative), unscaled px
def _furn(kind, x, fy, s=1.0):
    def P(pts):
        return bass.orient([(x + px * s, fy + py * s) for px, py in pts], True)
    if kind == "lamp":
        return [P([(-3, 0), (3, 0), (3, -96), (-3, -96)]), P([(-18, -96), (18, -96), (11, -124), (-11, -124)]),
                P([(-14, 0), (14, 0), (10, -6), (-10, -6)])]
    if kind == "table":
        return [P([(-34, -44), (34, -44), (34, -50), (-34, -50)]), P([(-30, 0), (-25, 0), (-25, -44), (-30, -44)]),
                P([(25, 0), (30, 0), (30, -44), (25, -44)])]
    if kind == "chair":
        return [P([(-12, -30), (12, -30), (12, -35), (-12, -35)]), P([(-12, 0), (-8, 0), (-8, -30), (-12, -30)]),
                P([(8, 0), (12, 0), (12, -72), (8, -72)])]
    if kind == "armchair":
        return [P([(-30, 0), (30, 0), (30, -30), (24, -36), (24, -64), (14, -70), (14, -40), (-24, -40),
                   (-24, -50), (-30, -50)])]
    if kind == "bed":
        return [P([(-60, 0), (60, 0), (60, -30), (-60, -30)]), P([(-60, 0), (-54, 0), (-54, -56), (-60, -56)]),
                P([(-50, -30), (-24, -30), (-24, -40), (-50, -40)])]
    if kind == "shelf":
        return [P([(-24, 0), (24, 0), (24, -118), (-24, -118)])]
    if kind == "plant":
        return [P([(-10, 0), (10, 0), (13, -22), (-13, -22)]), P([(0, -22), (-26, -60), (-6, -40), (2, -74),
                                                                    (8, -42), (28, -58), (6, -24)])]
    if kind == "radio":
        return [P([(-16, -44), (16, -44), (16, -66), (-16, -66)])] + _furn("table", x, fy, s)
    if kind == "stove":
        return [P([(-26, 0), (26, 0), (26, -52), (-26, -52)]), P([(-6, -52), (12, -52), (14, -62), (6, -68),
                                                                   (-6, -66), (-14, -60)])]
    if kind == "fridge":
        return [P([(-22, 0), (22, 0), (22, -112), (16, -118), (-16, -118), (-22, -112)])]
    if kind == "tv":
        return [P([(-22, 0), (-18, 0), (-12, -26), (12, -26), (18, 0), (22, 0), (22, -30), (-22, -30)]),
                P([(-24, -30), (24, -30), (24, -66), (-24, -66)]), P([(-2, -66), (2, -66), (-16, -92), (-19, -90)]),
                P([(-2, -66), (2, -66), (17, -94), (14, -96)])]
    if kind == "phone":
        return [P([(-30, -50), (30, -50), (30, -44), (-30, -44)])] + _furn("table", x, fy, s) + [
            P([(-12, -50), (12, -50), (9, -60), (-9, -60)]), P([(-14, -60), (14, -60), (14, -65), (-14, -65)])]
    return []


ROOM_SETS = (("bed", "lamp"), ("armchair", "lamp", "shelf"), ("table", "chair", "plant"), ("radio", "armchair"),
             ("fridge", "table", "chair"), ("tv", "armchair"), ("shelf", "bed"), ("stove", "table"))
HER_SET = (("stove", 26.0), ("phone", 92.0), ("lamp", 150.0))       # x from the room's back wall
HIS_SET = (("table", 150.0), ("lamp", 186.0), ("chair", 112.0))


def furniture(b, n, overturned=False):
    """The cut-paper furniture of storey n's room in building b: [(kind, x, polys)]. His chair
    lies on its back once `overturned`."""
    x0, y0, x1, y1 = b.room(n)
    fy = y1
    if b is HER_B and n == HER_FLOOR:
        items = [(kind, x0 + dx) for kind, dx in HER_SET]
    elif b is HIS_B and n == HIS_FLOOR:
        items = [(kind, x1 - dx) for kind, dx in HIS_SET]
    elif n == 1:
        return []
    else:
        kinds = ROOM_SETS[int(hash01(b.seed, n, 9) * len(ROOM_SETS))]
        span = x1 - x0
        items = [(kind, x0 + span * (0.22 + 0.28 * i) + 10.0 * _sn(b.seed, n, i)) for i, kind in enumerate(kinds)]
    out = []
    for kind, x in items:
        polys = _furn(kind, x, fy, 0.9)
        if overturned and kind == "chair":
            ca, sa = 0.0, 1.0                     # 90 deg about the foot of its back
            px, py = x + 10.0, fy
            polys = [bass.orient([(px + (qx - px) * ca - (qy - py) * sa, py + (qx - px) * sa + (qy - py) * ca - 2.0)
                                  for qx, qy in p], True) for p in polys]
        out.append((kind, x, polys))
    return out


def _stairs(c, b, color):
    """The flights, landings and half landings of b's stairwell, as sawtooth bands."""
    polys = []
    for n in range(1, b.floors + 1):
        top = n < b.floors
        lx, ly = b.landing(n)
        # landing at the floor (the slab runs under it); the half landing against the far wall
        if top:
            mx, my = b.mid(n)
            ex = b.stair[0] if b.side > 0 else b.stair[1]
            polys.append(bass.orient([(ex, my), (mx + 18.0 * b.side, my), (mx + 18.0 * b.side, my + 10.0),
                                      (ex, my + 10.0)], True))
            for (ax, ay), (bx2, by2) in (((lx, ly), (mx, my)), ((mx, my), b.landing(n + 1))):
                steps = 9
                pts = []
                for i in range(steps + 1):
                    f = i / steps
                    x = ax + (bx2 - ax) * f
                    y = ay + (by2 - ay) * f
                    pts.append((x, y))
                    if i < steps:
                        fx = ax + (bx2 - ax) * (i + 1) / steps
                        pts.append((fx, y))
                d = 11.0
                under = [(x, y + d) for x, y in pts[::-1]]
                polys.append(bass.orient(pts + [(pts[-1][0], pts[-1][1] + d)] + under, True))
    bass.fill_polys(c, polys, color)


def _shell(b, open_windows=(), open_doors=(), street_door_open=False):
    """b's walls and floors (with openings) as polygons."""
    polys = []
    top = b.roof
    for n in range(1, b.floors + 2):
        y = level(n)
        polys.append(bass.cut_rect(b.x0, y - SLAB / 2, b.x1, y + SLAB / 2, seed=b.seed + n, amp=0.6))
    # the outer wall away from the street: whole
    ox = (b.x0, b.x0 + WALL) if b.side > 0 else (b.x1 - WALL, b.x1)
    polys.append(bass.cut_rect(ox[0], top, ox[1], GROUND + SLAB / 2, seed=b.seed + 20, amp=0.6))
    # the street wall and the partition: storey by storey, round the openings
    for n in range(1, b.floors + 1):
        y0, y1 = level(n + 1) + SLAB / 2, level(n) - SLAB / 2
        if n == 1:
            sd = b.street_door()
            polys.append(bass.cut_rect(b.street[0], y0, b.street[1], sd[1], seed=b.seed + 40 + n, amp=0.5))
            if not street_door_open:
                polys.append(bass.cut_rect(b.street[0] + 4.0, sd[1], b.street[1] - 4.0, sd[3], seed=b.seed + 45, amp=0.4))
        else:
            wx0, wy0, wx1, wy1 = b.window(n)
            polys.append(bass.cut_rect(b.street[0], y0, b.street[1], wy0, seed=b.seed + 40 + n, amp=0.5))
            polys.append(bass.cut_rect(b.street[0], wy1, b.street[1], y1, seed=b.seed + 60 + n, amp=0.5))
            if n not in open_windows:            # the sash, shut: two thin bars across the opening
                mx = (wx0 + wx1) / 2.0
                polys.append(bass.cut_rect(mx - 2.5, wy0, mx + 2.5, wy1, seed=b.seed + 80 + n, amp=0.3))
        d = b.door(n)
        polys.append(bass.cut_rect(b.part[0], y0, b.part[1], d[1], seed=b.seed + 100 + n, amp=0.5))
        if n not in open_doors and n > 1:
            polys.append(bass.cut_rect(b.part[0] + 4.0, d[1], b.part[1] - 4.0, d[3], seed=b.seed + 120 + n, amp=0.4))
    # parapet
    polys.append(bass.cut_rect(b.x0 - 6.0, top - 26.0, b.x1 + 6.0, top, seed=b.seed + 140, amp=0.6))
    return polys


def _roof(b):
    """Roof furniture: her water tank; his bulkhead and aerial."""
    top = b.roof - 26.0
    if b.side > 0:
        x = b.x0 + 70.0
        return [bass.orient(bass.cut([(x, top), (x + 8, top), (x + 8, top - 60), (x + 82, top - 60), (x + 82, top),
                                      (x + 90, top), (x + 90, top - 64), (x + 96, top - 64), (x + 96, top - 74),
                                      (x + 92, top - 74), (x + 92, top - 150), (x + 76, top - 168), (x + 14, top - 168),
                                      (x - 2, top - 150), (x - 2, top - 74), (x - 6, top - 74), (x - 6, top - 64),
                                      (x, top - 64)], seed=b.seed + 150, amp=0.6), True)]
    x = b.stair[0] - 6.0
    return [bass.cut_rect(x, top - 70.0, b.stair[1] + 6.0, top, seed=b.seed + 151, amp=0.6),
            bass.orient([(x + 30.0, top - 70.0), (x + 34.0, top - 70.0), (x + 34.0, top - 190.0),
                         (x + 30.0, top - 190.0)], True),
            bass.orient([(x + 10.0, top - 160.0), (x + 56.0, top - 160.0), (x + 56.0, top - 155.0),
                         (x + 10.0, top - 155.0)], True)]


def fire_escape(c, color=INK, ladder=0.0):
    """Her fire escape: a platform under each window from storey 2 up, railed, ladders
    zig-zagging between them, and the drop ladder (ladder 0 = up, 1 = down to the street)."""
    polys = []
    x0, x1 = ESCAPE_X
    for n in range(2, HER_B.floors + 1):
        y = level(n)
        polys.append(bass.cut_rect(x0, y - 4.0, x1, y + 4.0, seed=800 + n, amp=0.4))
        polys.append(bass.cut_rect(x1 - 4.0, y - 44.0, x1, y, seed=810 + n, amp=0.3))       # railing post
        polys.append(bass.cut_rect(x0, y - 46.0, x1, y - 41.0, seed=820 + n, amp=0.3))      # top rail
        for j in range(1, 4):
            px = x0 + j * (x1 - x0) / 4.0
            polys.append(bass.orient([(px - 1.2, y - 44.0), (px + 1.2, y - 44.0), (px + 1.2, y), (px - 1.2, y)], True))
    for n in range(HER_B.floors, 2, -1):
        a = (x0 + 10.0, level(n)) if (HER_B.floors - n) % 2 == 0 else (x1 - 10.0, level(n))
        b2 = (x1 - 10.0, level(n - 1) - 4.0) if (HER_B.floors - n) % 2 == 0 else (x0 + 10.0, level(n - 1) - 4.0)
        polys.append(bass.line_pts([a, b2], width=7.0, seed=830 + n))
    # the drop ladder: two rails and rungs under the storey-2 platform
    yd0 = level(2) + 4.0
    yd1 = lerp(level(2) + 120.0, GROUND - 6.0, clamp(ladder))
    for x in (x1 - 30.0, x1 - 8.0):
        polys.append(bass.orient([(x - 2.0, yd0), (x + 2.0, yd0), (x + 2.0, yd1), (x - 2.0, yd1)], True))
    y = yd0 + 16.0
    while y < yd1:
        polys.append(bass.orient([(x1 - 30.0, y), (x1 - 8.0, y), (x1 - 8.0, y + 3.0), (x1 - 30.0, y + 3.0)], True))
        y += 20.0
    bass.fill_polys(c, polys, color)


def beam(c, b, n, color=AMBER, alpha=0.16, reach=None):
    """The light of a lit window, thrown out across the street as a flat wedge."""
    wx0, wy0, wx1, wy1 = b.window(n)
    x = b.face
    reach = reach if reach is not None else (STREET[1] - STREET[0])
    xe = x + b.side * reach
    spread = 0.38 * reach
    pts = [(x, wy0), (xe, wy0 - 0.25 * spread), (xe, wy1 + 0.75 * spread), (x, wy1)]
    bass.fill_polys(c, [bass.orient(pts, True)], color, alpha)


def street(c, t=0.0, lamp=True, lamp_on=True):
    """The street between them in section: the ground, the curbs, the lamp and its light."""
    gx0, gx1 = STREET
    if lamp and lamp_on:
        lx, ly = LAMP
        hx, hy = lx - 70.0, ly - 330.0
        bass.fill_polys(c, [bass.orient([(hx - 10.0, hy + 6.0), (hx + 10.0, hy + 6.0), (hx + 120.0, GROUND),
                                         (hx - 140.0, GROUND)], True)], AMBER, 0.13)
    bass.fill_polys(c, [bass.cut_rect(-20.0, GROUND, W + 20.0, H + 20.0, seed=900, amp=0.8)], INK)
    bass.fill_polys(c, [bass.cut_rect(gx0, GROUND - 10.0, gx0 + CURB, GROUND + 2.0, seed=901, amp=0.5),
                        bass.cut_rect(gx1 - CURB, GROUND - 10.0, gx1, GROUND + 2.0, seed=902, amp=0.5)], INK)
    if lamp:
        lx, ly = LAMP
        hx, hy = lx - 70.0, ly - 330.0
        bass.fill_polys(c, [bass.orient([(lx - 4.0, ly), (lx + 4.0, ly), (lx + 3.0, hy - 12.0), (lx - 3.0, hy - 12.0)],
                                        True),
                            bass.line_pts([(lx, hy - 10.0), (lx - 20.0, hy - 26.0), (hx, hy - 20.0)], width=5.0, seed=903),
                            bass.orient([(hx - 16.0, hy - 6.0), (hx + 16.0, hy - 6.0), (hx + 10.0, hy - 22.0),
                                         (hx - 10.0, hy - 22.0)], True)], INK)
        if lamp_on:
            dot(c, (hx, hy - 2.0), 7.0, AMBER, seed=904)


def floor_numbers(c, b, color, lit=None, size=40.0):
    """1, 2, 3 ... beside each storey on the side away from the street. lit: {storey: rgb}."""
    x = b.x0 - 22.0 if b.side > 0 else b.x1 + 22.0
    for n in range(1, b.floors + 1):
        col = (lit or {}).get(n, color)
        numeral(c, str(n), (x, (level(n) + level(n + 1)) / 2.0), size, col, seed=40 + n + b.seed)


def draw_section(c, t, lit=None, people=None, open_windows=None, open_doors=None, street_doors=(),
                 beams=True, ladder=0.0, numbers=None, room_fill=None, overturned=False, city=True,
                 lamp_on=True, field=NIGHT, sky_lit=0.0, moon_at=MOON_S):
    """The two buildings cut open, at time t.

    lit:   {(building, storey): rgb} rooms whose light is on (default: hers and his, AMBER)
    beams: True (every lit room throws its light across the street), False, or a set of
           (building, storey): only those rooms do
    people(c, b, n, room_rect): draws whoever is in a lit or dark room (called after the
           furniture, before the walls), for every room
    open_windows / open_doors: {building: set(storeys)}; street_doors: buildings whose street
           door stands open
    ladder: her drop ladder, 0 up .. 1 down
    numbers: None, or {building: {storey: rgb}} to show the floor numbers (lit ones coloured)
    sky_lit: how many of the far city's windows are lit (0..1); moon_at: where the moon hangs
    """
    fill(c, field)
    if city:
        skyline(c, lit=sky_lit)
        moon(c, moon_at)
    lit = {(HER_B, HER_FLOOR): AMBER, (HIS_B, HIS_FLOOR): AMBER} if lit is None else lit
    open_windows = open_windows or {}
    open_doors = open_doors or {}
    for b in (HER_B, HIS_B):
        # inside: rooms and stairwell
        bass.fill_polys(c, [bass.cut_rect(b.x0, b.roof, b.x1, GROUND, seed=b.seed + 1, amp=0.5)], DEEP)
        for n in range(1, b.floors + 1):
            col = lit.get((b, n))
            if col is not None:
                bass.fill_polys(c, [bass.cut_rect(*b.room(n), seed=b.seed + 200 + n, amp=0.5)], col)
            for kind, x, polys in furniture(b, n, overturned and b is HIS_B and n == HIS_FLOOR):
                bass.fill_polys(c, polys, INK if col is not None else lerp(DEEP, INK, 0.6))
            if people is not None:
                people(c, b, n, b.room(n))
        _stairs(c, b, INK)
        bass.fill_polys(c, _shell(b, open_windows.get(b, ()), open_doors.get(b, ()), b in street_doors) + _roof(b), INK)
        if numbers is not None and b in numbers:
            floor_numbers(c, b, lerp(NIGHT, PAPER, 0.35), lit=numbers[b])
    if beams:
        c.save()
        clip_rect(c, (STREET[0], 0.0, STREET[1], GROUND))           # the light falls in the street only
        for (b, n), col in lit.items():
            if n > 1 and (beams is True or (b, n) in beams):
                beam(c, b, n, col)
        c.restore()
    fire_escape(c, INK, ladder)
    street(c, t, lamp_on=lamp_on)
