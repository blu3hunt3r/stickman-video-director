"""s11 · END (136-144): the lit windows fly out of the block and come back together as the
title, OPPOSITE, paper on black (the reverse of the opening, where the title's letters became
the windows: S, I, T and E turn upright again on the way). The red ring round him draws tight
into a red dot, which waits at the start of the cut; the red slash cuts the title, the halves
slide apart along it and away; the slash draws in to the centre, the red dot beats twice like
a heart and is gone. Black. Silence."""
import math
from functools import lru_cache

from engine import bass
from engine.core import clamp, ease, lerp
from engine.palette import RED
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import kit as K
from films.opposite_full.scenes import s10_opposite as S10

k = K.k
HER_B, HIS_B = K.HER_B, K.HIS_B
S10_END = 20.0                    # s10's length: s11 picks up its last frame

# ---------------------------------------------------------------- beats (scene time)
T_WEB_OFF = 0.15                  # the looks run home into him
T_RING_IN = (0.3, 0.18)           # the red ring draws tight round him: a red dot
T_LIFT = 0.55                     # the first window lifts out of the block ...
LIFT_STAGGER = 0.085              # ... the others after it, in reading order
T_FLY = 0.9                       # each one's flight
T_DARK = (0.8, 1.0)               # the block goes black behind them
T_DOT_MOVE = (0.95, 0.6)          # the dot slips away to the start of the cut
T_STAMP = 1.95                    # the title stamps down
T_SLASH = 3.0                     # the red slash
T_PART = 3.1                      # the halves slide apart along it ...
T_AWAY = 4.45                     # ... and away, out of the frame
T_DRAW_IN = 4.95                  # the slash draws in to the centre
T_POP = 5.2                       # the red dot pops
BEATS = ((5.55, 1.0), (6.2, 0.7))   # lub (dub after it), and how hard
T_GONE = (6.5, 0.45)              # it shrinks away: gone by 7.0

HOVER = 1.1                       # the title's scale while the letters hang over the page
LIFT = 170.0                      # how high a window rises as it flies
LETTER_ROOMS = ((HER_B, 5), (HER_B, 3), (HER_B, 2), (HIS_B, 6), (HIS_B, 5), (HIS_B, 4), (HIS_B, 3), (HIS_B, 2))
P0, P1 = (60.0, 1174.0), (1020.0, 746.0)     # the cut: the Bass end card's, through the frame's centre
CENTRE = (540.0, 960.0)


# ---------------------------------------------------------------- geometry
def sec_to_frame(p):
    """Section px -> frame px, at s10's last frame (the pull back done)."""
    z, cy = S10.pull(S10_END)
    return (540.0 + (p[0] - 540.0) * z, 960.0 + (p[1] - cy) * z)


@lru_cache(maxsize=None)
def room_frame(i):
    """Letter i's room in frame px: (x0, y0, x1, y1)."""
    b, n = LETTER_ROOMS[i]
    x0, y0, x1, y1 = b.room(n)
    a, z = sec_to_frame((x0, y0)), sec_to_frame((x1, y1))
    return (a[0], a[1], z[0], z[1])


@lru_cache(maxsize=None)
def letter(i):
    """Letter i of the title: (centre offset from the title's centre, outer contour, holes),
    the contours about the letter's own centre."""
    g = B.title()[i]
    bb = g.bbox
    lc = ((bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0)
    outer = max(g.polys, key=lambda p: abs(bass.poly_area(p)))
    local = lambda p: [(x - lc[0], y - lc[1]) for x, y in p]
    return lc, local(outer), [local(p) for p in g.polys if p is not outer]


def t_lift(i):
    return T_LIFT + LIFT_STAGGER * i


def _xf(pts, pos, s, rot):
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    return [(pos[0] + s * (x * ca - y * sa), pos[1] + s * (x * sa + y * ca)) for x, y in pts]


def _shrink(p, s):
    cx = sum(x for x, _ in p) / len(p)
    cy = sum(y for _, y in p) / len(p)
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in p]


def flying_letter(c, i, t):
    """Window i on its way to its letter: lifting, arcing over, growing and shrinking a little,
    its rectangle turning into the letter and its amber into paper."""
    u = k(t, t_lift(i), T_FLY, "inout3")
    m = k(t, t_lift(i) + 0.12, T_FLY - 0.12, "inout")
    x0, y0, x1, y1 = room_frame(i)
    w, h = x1 - x0, y1 - y0
    lc, outer, holes = letter(i)
    a = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
    b = (CENTRE[0] + HOVER * lc[0], CENTRE[1] + HOVER * lc[1])
    pos = (lerp(a[0], b[0], u), lerp(a[1], b[1], u) - LIFT * math.sin(math.pi * u))
    s = 1.0 + 0.22 * math.sin(math.pi * u)
    # S, I, T and E hung upside down on his facade at the start: they turn upright now
    rot = 180.0 * (1.0 - ease("inout", u)) if i >= 4 else (9.0 if i % 2 else -9.0) * math.sin(math.pi * u)
    rect = B.rect_pts((-w / 2.0, -h / 2.0, w / 2.0, h / 2.0))
    shape = bass.morph_outline(rect, [(x * HOVER, y * HOVER) for x, y in outer], m, n=120)
    polys = [bass.orient(_xf(shape, pos, s, rot), True)]
    hs = clamp((m - 0.45) / 0.55)
    if hs > 0.02:
        polys += [bass.orient(_xf(_shrink([(x * HOVER, y * HOVER) for x, y in hp], hs), pos, s, rot), False)
                  for hp in holes]
    bass.fill_polys(c, polys, lerp(K.AMBER, K.PAPER, m))


# ---------------------------------------------------------------- the red: ring, dot, cut
def ring_dot(c, t, head):
    """The red ring round him, drawing tight into a dot, which slips away to the cut's start
    and waits there; it beats once with the stamp, and goes into the slash."""
    z, cy = S10.pull(S10_END)
    c0 = (head[0] - 6.0 * z, head[1] + 48.0 * z)
    e = k(t, T_RING_IN[0], T_RING_IN[1], "in3")
    if e < 1.0:
        # in the section's own space, as s10 drew it, so the cut does not jump
        c.save()
        c.translate(540.0, 960.0)
        c.scale(z, z)
        c.translate(-540.0, -cy)
        cs = (540.0 + (c0[0] - 540.0) / z, cy + (c0[1] - 960.0) / z)
        K.marker_ring(c, cs, lerp(48.0, 9.0 / z, e), lerp(92.0, 9.0 / z, e), u=1.0, color=RED, width=12.0, seed=7)
        c.restore()
        return
    v = k(t, T_DOT_MOVE[0], T_DOT_MOVE[1], "inout")
    p = (lerp(c0[0], P0[0], v), lerp(c0[1], P0[1], v) + 90.0 * math.sin(math.pi * v))
    r = 17.0 * ease("outback", clamp((t - T_RING_IN[0] - T_RING_IN[1]) / 0.12))
    r *= 1.0 + 0.3 * bump(t, T_STAMP, 0.05, 0.2)
    r *= 1.0 - k(t, T_SLASH, 0.08, "in")
    if r > 0.5:
        K.dot(c, p, r, RED, seed=5)


def bump(t, t0, rise=0.06, fall=0.22):
    """0 .. 1 .. 0: a quick swell at t0 and its decay (a beat)."""
    if t < t0:
        return 0.0
    d = t - t0
    return d / rise if d < rise else math.exp(-3.0 * (d - rise) / fall)


def draw_cut_title(c, t):
    """The title, cut along the slash: the halves slide apart along it, then away."""
    T = B.title()
    dx, dy = P1[0] - P0[0], P1[1] - P0[1]
    L = math.hypot(dx, dy)
    d = (dx / L, dy / L)
    n = (-d[1], d[0])
    apart = 40.0 * k(t, T_PART, 0.5, "out5") + 1500.0 * k(t, T_AWAY, 0.5, "in3")
    if t < T_PART:
        bass.draw_title(c, T, CENTRE, K.PAPER)
        return
    for sg in (-1.0, 1.0):
        c.save()
        c.new_path()
        bass.draw.poly(c, [(P0[0] - d[0] * 3000.0, P0[1] - d[1] * 3000.0), (P0[0] + d[0] * 3000.0, P0[1] + d[1] * 3000.0),
                           (P0[0] + d[0] * 3000.0 + n[0] * 3000.0 * sg, P0[1] + d[1] * 3000.0 + n[1] * 3000.0 * sg),
                           (P0[0] - d[0] * 3000.0 + n[0] * 3000.0 * sg, P0[1] - d[1] * 3000.0 + n[1] * 3000.0 * sg)])
        c.clip()
        c.translate(d[0] * apart * sg, d[1] * apart * sg)
        bass.draw_title(c, T, CENTRE, K.PAPER)
        c.restore()


def draw_slash(c, t):
    if t < T_SLASH:
        return
    cu = k(t, T_DRAW_IN, T_POP - T_DRAW_IN, "inout")
    if cu >= 0.999:
        return
    bass.slash(c, P0, P1, RED, width=40.0, u=min(k(t, T_SLASH, 0.12, "out3"), 1.0 - 0.5 * cu), tail=0.5 * cu, seed=12)


def draw_heart(c, t):
    """The red dot at the centre: it pops, beats twice like a heart, the second softer, and
    shrinks away."""
    if t < T_POP:
        return
    r = 42.0 * ease("outback", clamp((t - T_POP) / 0.14))
    for tb, a in BEATS:
        r *= 1.0 + a * (0.26 * bump(t, tb) + 0.15 * bump(t, tb + 0.2))
        K.ripple(c, CENTRE, t, tb, RED, n=1, life=0.95, r0=44.0, r1=330.0, width=9.0, seed=31, alpha=0.75 * a)
    r *= 1.0 - k(t, T_GONE[0], T_GONE[1], "in3")
    if r > 0.5:
        K.dot(c, CENTRE, r, RED, seed=5)


def shake(t):
    dx = dy = 0.0
    for t0, amp in ((T_STAMP, 7.0), (T_SLASH, 5.0)):
        if t >= t0:
            e = amp * math.exp(-14.0 * (t - t0))
            dx += e * math.sin(61.0 * (t - t0))
            dy += e * math.cos(47.0 * (t - t0))
    return dx, dy


# ---------------------------------------------------------------- the scene
def draw_block(c, t):
    """s10's last frame running on: the looks run home, the lit rooms go dark as their
    windows leave, the block sinks into black."""
    dark = k(t, T_DARK[0], T_DARK[1], "inout")
    head = None
    if dark < 0.999:
        head = S10.draw_watched(c, S10_END + t, lines_off=S10_END + T_WEB_OFF, ring=False)
        for i in range(8):
            if t >= t_lift(i):
                x0, y0, x1, y1 = room_frame(i)
                bass.fill_polys(c, [bass.cut_rect(x0 - 1.0, y0 - 1.0, x1 + 1.0, y1 + 1.0, seed=40 + i, amp=0.3)], K.DEEP)
    if dark > 0.0:
        bass.fill_polys(c, [bass.cut_rect(-60.0, -60.0, 1140.0, 1980.0, seed=39, amp=0.0)], K.INK, dark)
    return head


@lru_cache(maxsize=1)
def his_head():
    """Where s10 leaves him (frame px): the ring's anchor."""
    import cairo
    c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4))
    return S10.draw_watched(c, S10_END, ring=False) or (420.0, 880.0)


def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        if t < T_STAMP + 0.2:
            draw_block(c, t)
            head = his_head()
            dx, dy = shake(t)
            c.save()
            c.translate(dx, dy)
            if t < T_STAMP:
                for i in range(8):
                    if t >= t_lift(i):
                        flying_letter(c, i, t)
            else:
                bass.draw_title(c, B.title(), CENTRE, K.PAPER, scale=lerp(HOVER, 1.0, k(t, T_STAMP, 0.09, "out3")))
            c.restore()
            ring_dot(c, t, head)
            return
        K.fill(c, K.INK)
        dx, dy = shake(t)
        c.save()
        c.translate(dx, dy)
        if t < T_AWAY + 0.55:
            draw_cut_title(c, t)
        ring_dot(c, t, P0)
        draw_slash(c, t)
        c.restore()
        draw_heart(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    out = [Cue(0.0, "the strings' major chord rings on; the sirens far off, fading", gain_db=-10, dur=1.6),
           Cue(T_WEB_OFF, "the looks run home: a soft reversed shimmer", gain_db=-14),
           Cue(T_RING_IN[0], "the ring draws tight: the marker squeak", gain_db=-12)]
    out += [Cue(t_lift(i), "a window lifts out: one plucked note, rising up the scale", gain_db=-11) for i in range(8)]
    out += [Cue(T_STAMP, "the title stamps down: a deep paper thud", gain_db=-4),
            Cue(T_SLASH, "the red slash: a whip, and the last chord", gain_db=-3, dur=T_POP - T_SLASH),
            Cue(T_AWAY, "the halves slide away: a paper swish", gain_db=-12),
            Cue(T_POP, "the red dot pops", gain_db=-10)]
    out += [Cue(tb, "a heartbeat: lub-dub", gain_db=-6 if a > 0.9 else -10) for tb, a in BEATS]
    out += [Cue(8.0, "silence", gain_db=-60)]
    return out
