"""OPPOSITE, the Bass cut: the same story told the way Saul Bass told stories, in flat cut
paper, graphic metaphor and rhythm instead of a camera looking at rooms.

Every beat is one graphic idea, and each one turns into the next:

   0.0  TITLE    Psycho strips assemble OPPOSITE; a red cut splits it; OPPO and SITE (upside
                 down: opposite) part; the ground floods paper, two slabs rise under the halves
                 and each letter becomes a window (type -> architecture, North by Northwest).
   5.0  WINDOWS  two lit windows face each other; she sips; red zigzags of shouting cross the
                 street from his window to hers.
   8.5  HER EYE  her eye fills the frame; his window is reflected in it; we fall into the
                 reflection (Vertigo).
  11.0  QUARREL  inside his window: the two of them as Anatomy of a Murder cut-outs, every limb
                 a separate piece of paper; the frame jumps closer on the beat.
  14.0  KNIFE    the blade goes up; three cuts slice the frame itself open on red (Psycho); she
                 comes apart and falls out of the picture; bars close the window.
  16.5  MUG      her head in profile, her hand to her mouth; the mug falls and shatters.
  18.5  ARM      his window lights; he stands looking at her; his arm grows across the street
                 to her window, jagged (The Man with the Golden Arm). He is gone.
  21.5  OFF      she pulls the cord: the picture flips negative and goes dark.
  22.5  PATH     a diagram in the dark: a red line walks, step by step, down his stairs,
                 across the street, up hers, to her door.
  28.5  DOOR     the bar of light under her door; two feet cut into it; the handle turns, twice.
  31.5  HIS EYE  into the keyhole: his eye, the mirror of hers, opens.
  33.4  END      OPPOSITE, cut through in red. Black.

All drawing is in frame px (1080 x 1920, y down), a pure function of film time t. Figures
are paperdoll cut-outs driven by retargeted CMU motion capture (engine/mocap.py), stepped on
twos (12 fps) like stop-motion paper; graphics and camera moves run on ones.
"""
import math
import zlib
from functools import lru_cache

import cairo

from engine import bass, mocap as mc, paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED

W, H = 1080.0, 1920.0
INK = (0.020, 0.018, 0.016)
PAPER = bass.PAPER
FIELD = (0.80, 0.765, 0.70)
AMBER = (0.95, 0.66, 0.24)
UNLIT = (0.20, 0.185, 0.17)
DIM = (0.33, 0.31, 0.29)

BPM = 120.0
BEAT = 60.0 / BPM

# ----------------------------------------------------------------------------- beats (film s)
T_TITLE_CUT = 2.0          # the red cut between OPPO and SITE
T_PART = 2.15              # the halves part
T_FLOOD = 2.9              # paper floods the ground
T_RISE = 3.0               # the slabs rise
T_MORPH = 3.6              # letters become windows
T_DARK = 4.4               # the windows go out, two stay lit
T_WIN = 5.0
T_EYE = 8.5
T_ROOM = 11.0
T_RAISE = 14.0
T_SLASH = (14.6, 14.85, 15.1)
T_BARS = 15.9
T_MUG = 16.5
T_GASP = 16.55
T_HAND = 16.85
T_DROP = 16.95
T_SMASH = 17.6
T_ARM = 18.5
T_HIS_ON = 18.7
T_GROW = 19.3
T_RETRACT = 20.9
T_GONE = 21.05
T_OFF = 21.5
T_PULL = 21.85
T_PATH = 22.5
T_DOOR = 28.5
T_FEET = 30.35
T_KNOB = (30.85, 31.35)
T_KEY = 31.5
T_OPEN = 32.3
T_END = 33.4
T_END_SLASH = 33.9
T_BLACK = 35.0
DURATION = 36.0

# shouting: one red zigzag per voice onset in the quarrel recording (mix.py places it to match)
QUARREL_AT = 5.9           # film time of the recording's start
QUARREL_LOOP = (11.95, 3.5)   # (film time, source s) where its last part is played again
_Q_ONSETS = (1.23, 1.62, 2.13, 3.62, 4.19, 4.76, 5.32)
BOLTS = tuple(sorted([QUARREL_AT + o for o in _Q_ONSETS if QUARREL_AT + o < 11.9] +
                     [QUARREL_LOOP[0] + o - QUARREL_LOOP[1] for o in _Q_ONSETS if o >= QUARREL_LOOP[1]]))


def k(t, t0, dur, e="inout"):
    return ease(e, clamp((t - t0) / dur)) if dur > 0 else (1.0 if t >= t0 else 0.0)


def twos(t):
    return bass.on_twos(t, 12.0)


# ----------------------------------------------------------------------------- figures
@lru_cache(maxsize=1)
def figs():
    return pd.woman(RED, 0), pd.man(RED, 0), pd.woman(RED, 1)


@lru_cache(maxsize=1)
def perfs():
    C = mc.Clip.load
    her, man, vic = figs()
    her_p = mc.Performance(her, [
        mc.Seg(C("137_26"), 0.3, 2.3, at=3.0, speed=0.6),
        mc.Seg(C("137_26"), 7.0, 9.9, at=5.25),                                    # a sip
        mc.Seg(C("137_26"), 9.9, 10.4, at=8.15, speed=0.4),
        mc.Seg(C("79_73"), 3.6, 5.3, at=T_ARM - 0.2, blend=0.3),                  # frozen at the glass
        mc.Seg(C("79_73"), 5.3, 5.4, at=T_ARM + 1.5, speed=0.05, blend=0.4),
    ], facing=1, near="Right")
    man_p = mc.Performance(man, [
        mc.Seg(C("80_48"), 1.0, 7.75, at=6.4, speed=6.75 / (T_RAISE - 0.75 - 6.4)),
        mc.Seg(C("86_04"), 42.3, 43.05, at=T_RAISE - 0.75, speed=0.6, near="Right", blend=0.3),
        mc.Seg(C("86_04"), 43.05, 44.4, at=T_SLASH[0] - 0.1, near="Right", blend=0.04),
    ], facing=1, near="Left")
    alone = mc.Performance(man, [
        mc.Seg(C("80_48"), 8.6, 9.4, at=T_HIS_ON - 0.4, speed=0.5),
        mc.Seg(C("80_48"), 5.7, 6.05, at=T_GROW - 0.25),
        mc.Seg(C("80_48"), 6.05, 6.15, at=T_GROW + 0.1, speed=0.12, blend=0.1),
        mc.Seg(C("80_48"), 8.6, 8.8, at=T_RETRACT, blend=0.2),
    ], facing=-1, near="Left")
    vic_p = mc.Performance(vic, [
        mc.Seg(C("80_48"), 0.4, 7.9, at=6.4, speed=7.5 / (T_RAISE + 0.05 - 6.4)),
        mc.Seg(C("79_73"), 0.45, 1.6, at=T_RAISE + 0.05, lean=-12.0),             # hands up to her face
        mc.Seg(C("90_18"), 0.55, 1.6, at=T_SLASH[0] + 0.05, blend=0.12),           # going over
    ], facing=-1, near="Left")
    return her_p, man_p, alone, vic_p


def _toward(arm, sh, el, w):
    return ("ang", arm[1] + mc._wrap(sh - arm[1]) * w, arm[2] + mc._wrap(el - arm[2]) * w)


def her_pose(t):
    st, p = perfs()[0](twos(t))
    if t < T_MUG:
        p.hold["near"] = lambda c, hc, deg: draw_mug(c, hc, deg, t, scale=1.0)
    if T_OFF <= t:                                 # up to the cord, and pull
        u = k(t, T_OFF + 0.1, 0.25, "out3")
        pull = k(t, T_PULL, 0.08, "out")
        p.arms["near"] = _toward(p.arms["near"], lerp(172.0, 150.0, pull), lerp(4.0, 20.0, pull), u)
        p.head = lerp(p.head, 14.0, u)
    return st, p


def man_pose(t):
    t2 = twos(t)
    st, p = perfs()[1](t2)
    S_ = k(t, T_SLASH[0] - 0.07, 0.1, "out")
    w = k(t, T_RAISE, 0.32, "out3") * (1.0 - k(t, T_SLASH[0] + 0.5, 0.5))
    if w > 0.0:                                    # the knife high over his head, then down
        p.arms["near"] = _toward(p.arms["near"], lerp(170.0, 30.0, S_) - p.lean * (1.0 - S_), lerp(30.0, 0.0, S_), w)
    if t >= T_RAISE - 0.2:
        off = lerp(150.0, 70.0, S_)
        p.hold["near"] = lambda c, hc, deg: draw_knife(c, hc, deg + off)
    return st, p


def alone_pose(t):
    st, p = perfs()[2](twos(t))
    w = k(t, T_GROW - 0.15, 0.2, "out3") * (1.0 - k(t, T_RETRACT, 0.2))
    if w > 0.0:
        p.arms["near"] = _toward(p.arms["near"], 98.0 - p.lean, -8.0, w)
    return st, p


def vic_pose(t):
    st, p = perfs()[3](twos(t))
    w = k(t, T_RAISE + 0.1, 0.25, "out3") * (1.0 - k(t, T_SLASH[0] + 0.05, 0.12))
    if w > 0.0:
        p.arms["near"] = _toward(p.arms["near"], 150.0, 95.0, w)
        p.arms["far"] = _toward(p.arms["far"], 128.0, 105.0, w)
    return st, p


_HILT = bass.cut([(-6, -7), (16, -7), (16, 7), (-6, 7)], seed=62, amp=0.2)
_BLADE = bass.cut([(16, -10), (120, -3), (150, 5), (16, 10)], seed=63, amp=0.2)


def draw_knife(c, hc, deg):
    c.save()
    c.translate(*hc)
    c.rotate(math.radians(deg))
    bass.fill_polys(c, [_HILT], INK)
    bass.fill_polys(c, [_BLADE], PAPER)
    c.restore()


_MUG = bass.cut([(-14, -28), (16, -28), (15, 12), (-13, 12)], seed=61, amp=0.2)


def mug_shape(c, color, steam_t=None):
    """A coffee mug (handle at the back, steam rising); origin at the hand, mug units."""
    bass.fill_polys(c, [_MUG], color)
    c.save()
    c.new_path()
    c.arc(-17.0, -6.0, 10.0, math.radians(90), math.radians(270))
    c.set_line_width(5.5)
    c.set_source_rgb(*color)
    c.stroke()
    if steam_t is not None:
        c.set_line_width(3.2)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for j, x0 in enumerate((-4.0, 6.0)):
            c.new_path()
            for i in range(14):
                u = i / 13.0
                x = x0 + 5.0 * math.sin(2 * math.pi * (u * 1.2 - steam_t * 0.9) + j * 2.0) * u
                y = -34.0 - 34.0 * u
                c.line_to(x, y) if i else c.move_to(x, y)
            c.set_source_rgba(*color, 0.8)
            c.stroke()
    c.restore()


def draw_mug(c, hc, deg, t, scale=1.0):
    c.save()
    c.translate(hc[0], hc[1] + 4.0)
    c.rotate(math.radians(clamp(-deg - 55.0, 0.0, 75.0)))
    c.scale(scale, scale)
    mug_shape(c, INK, steam_t=twos(t))
    c.restore()


# ----------------------------------------------------------------------------- exploded cut-outs
def _shorten(a, b, g):
    d = math.dist(a, b) or 1.0
    g = min(g, d * 0.3)
    ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
    return (a[0] + ux * g, a[1] + uy * g), (b[0] - ux * g, b[1] - uy * g)


def draw_cutout(c, fig, st, pose, color, facing=1, gap=0.0, burst=None, far=None):
    """Draw a paperdoll figure as separate pieces of cut paper (Anatomy of a Murder): each
    limb segment, the torso, head, hands and feet are their own shapes with `gap` px of paper
    between them. burst(name, centre) -> (dx, dy, deg) moves a piece (coming apart)."""
    P = st["pelvis"]
    P = (P[0], P[1] + pose.crouch)
    lean = pose.lean
    far = far or color

    def Wd(p):
        q = pd._rot((p[0], p[1]), lean)
        return (P[0] + facing * q[0], P[1] + q[1])

    def piece(name, polys, rgb, centre):
        if burst is not None:
            dx, dy, deg = burst(name, centre)
            if dx or dy or deg:
                c.save()
                c.translate(centre[0] + dx, centre[1] + dy)
                c.rotate(math.radians(deg))
                c.translate(-centre[0], -centre[1])
                bass.fill_polys(c, polys, rgb)
                c.restore()
                return
        bass.fill_polys(c, polys, rgb)

    def seg(name, a, b, ra, rb, rgb):
        a2, b2 = _shorten(a, b, gap)
        piece(name, [bass.capsule_pts(a2, b2, ra, rb, cap=8)], rgb, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))

    out = {}
    legs = {}
    for side in ("far", "near"):
        foot = st["feet"][side]
        hip = Wd((0.0, -4.0))
        knee, ank = pd.ik2(hip, (foot[0], foot[1] - fig.ankle), fig.thigh, fig.shin, forward=facing)
        legs[side] = (hip, knee, ank, foot[2])

    def arm(side):
        spec = pose.arms.get(side, ("ang", 0.0, 0.0))
        sh = Wd(fig.shoulder)
        if spec[0] == "ik":
            el, wr = pd.ik2(sh, spec[1], fig.upper, fig.fore, forward=-facing)
        else:
            a1 = spec[1] + lean
            a2 = a1 + spec[2]
            el = (sh[0] + facing * math.sin(math.radians(a1)) * fig.upper, sh[1] + math.cos(math.radians(a1)) * fig.upper)
            wr = (el[0] + facing * math.sin(math.radians(a2)) * fig.fore, el[1] + math.cos(math.radians(a2)) * fig.fore)
        return sh, el, wr

    def draw_leg(side, rgb):
        hip, knee, ank, pitch = legs[side]
        w0, w1, w2 = fig.leg_w
        seg("thigh_" + side, hip, knee, w0 / 2, w1 / 2, rgb)
        seg("shin_" + side, knee, ank, w1 / 2, w2 / 2, rgb)
        foot = [(ank[0] + facing * x, ank[1] + y + gap * 0.6) for x, y in _rot_poly(fig.foot, -pitch)]
        piece("foot_" + side, [bass.orient(foot, True)], rgb, ank)

    def draw_arm(side, rgb):
        sh, el, wr = arm(side)
        w0, w1, w2 = fig.arm_w
        d = math.dist(wr, el) or 1.0
        hc = (wr[0] + (wr[0] - el[0]) / d * (fig.hand_r * 0.55 + gap * 0.7), wr[1] + (wr[1] - el[1]) / d * (fig.hand_r * 0.55 + gap * 0.7))
        seg("upper_" + side, sh, el, w0 / 2, w1 / 2, rgb)
        seg("fore_" + side, el, wr, w1 / 2, w2 / 2, rgb)
        piece("hand_" + side, [bass.draw.circle_pts(hc, fig.hand_r, n=20)], rgb, hc)
        out["hand_" + side] = hc
        hold = pose.hold.get(side)
        if hold is not None:
            dx, dy, deg = burst("hand_" + side, hc) if burst is not None else (0.0, 0.0, 0.0)
            hold(c, (hc[0] + dx, hc[1] + dy), math.degrees(math.atan2(wr[1] - el[1], wr[0] - el[0])) + deg)

    draw_arm("far", far)
    draw_leg("far", far)
    draw_leg("near", color)
    # torso and head, in the pelvis frame
    torso_c = Wd((0.0, -130.0))
    head_c = Wd(fig.neck)

    def framed(name, centre, fn):
        dx, dy, deg = burst(name, centre) if burst is not None else (0.0, 0.0, 0.0)
        c.save()
        c.translate(centre[0] + dx, centre[1] + dy)
        c.rotate(math.radians(deg))
        c.translate(-centre[0], -centre[1])
        c.translate(*P)
        c.scale(facing, 1.0)
        c.rotate(math.radians(lean))
        fn()
        c.restore()

    framed("torso", torso_c, lambda: [bass.fill_polys(c, [poly], color) for poly, _ in fig.torso])

    def head():
        c.translate(0.0, -gap * 1.2)
        c.translate(*fig.neck)
        c.rotate(math.radians(-pose.head))
        c.translate(-fig.neck[0], -fig.neck[1])
        for poly, _ in fig.head:
            bass.fill_polys(c, [poly], color)
        if fig.eye is not None and pose.eye > 0.02:
            (ex, ey), rx, ry = fig.eye
            bass.fill_polys(c, [bass.draw.ellipse_pts((ex, ey), rx * 1.2, ry * 1.2 * pose.eye, n=20)], PAPER)

    framed("head", head_c, head)
    draw_arm("near", color)
    out["head"] = Wd((fig.neck[0] + 10.0, fig.neck[1] - 60.0))
    out["mouth"] = Wd((fig.neck[0] + 40.0, fig.neck[1] - 35.0))
    out["pelvis"] = P
    return out


def _rot_poly(pts, deg):
    return [pd._rot(p, deg) for p in pts]


def place(c, x, floor_y, s):
    c.translate(x, floor_y)
    c.scale(s, s)


# ----------------------------------------------------------------------------- shapes
def rect_pts(r):
    return [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]


def fill(c, rgb, r=None, alpha=1.0):
    c.save()
    c.new_path()
    if r is None:
        c.rectangle(-4000, -4000, 9000, 9000)
    else:
        c.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
    c.set_source_rgba(*rgb, alpha)
    c.fill()
    c.restore()


def clip_rect(c, r):
    c.new_path()
    c.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
    c.clip()


def zigzag(a, b, n=6, amp=34.0, seed=0):
    """Points of a jagged shout bolt from a to b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    pts = [a]
    for i in range(1, n):
        f = i / n
        s = amp * (1 if i % 2 else -1) * (0.7 + 0.6 * hash01(seed, i))
        pts.append((a[0] + dx * f + nx * s, a[1] + dy * f + ny * s))
    pts.append(b)
    return pts


def bolt(c, a, b, t, t0, dur=0.32, width=16.0, seed=0, amp=34.0, n=6):
    """A red zigzag shout from a to b: it shoots out, then its tail chases its head."""
    u = k(t, t0, dur * 0.45, "out3")
    tail = k(t, t0 + dur * 0.45, dur * 0.55, "in3")
    if u <= 0 or tail >= 1:
        return
    pts = zigzag(a, b, n, amp, seed)
    band = bass.line_pts(pts, width, u, seed=seed, taper=(0.4, 1.0))
    if not band:
        return
    if tail > 0:
        c.save()
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        ox, oy = a[0] + dx * tail, a[1] + dy * tail
        # keep only what lies ahead of the tail
        nx, ny = dx / L, dy / L
        c.new_path()
        c.move_to(ox - ny * 4000, oy + nx * 4000)
        c.line_to(ox + ny * 4000, oy - nx * 4000)
        c.line_to(ox + ny * 4000 + nx * 4000, oy - nx * 4000 + ny * 4000)
        c.line_to(ox - ny * 4000 + nx * 4000, oy + nx * 4000 + ny * 4000)
        c.close_path()
        c.clip()
        bass.fill_polys(c, [band], RED)
        c.restore()
    else:
        bass.fill_polys(c, [band], RED)


# ----------------------------------------------------------------------------- the street (title, windows, arm)
LEFT_B = (70.0, 640.0, 450.0, 1960.0)       # her building
RIGHT_B = (630.0, 380.0, 1010.0, 1960.0)    # his building
LEFT_WIN = [(110.0, 760.0, 240.0, 940.0), (280.0, 760.0, 410.0, 940.0),
            (110.0, 1020.0, 240.0, 1200.0), (280.0, 1020.0, 410.0, 1200.0)]
RIGHT_WIN = [(670.0, 500.0, 800.0, 680.0), (840.0, 500.0, 970.0, 680.0),
             (670.0, 760.0, 800.0, 940.0), (840.0, 760.0, 970.0, 940.0)]
HER_WIN = LEFT_WIN[3]
HIS_WIN = RIGHT_WIN[0]
WIN_FS = 0.205                               # figures in the street windows


def centre(r):
    return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)


@lru_cache(maxsize=1)
def title():
    return bass.title_glyphs("OPPOSITE", width=900.0, seed=7, rough=1.0, jitter=0.8)


def _outer(g):
    return max(g.polys, key=lambda p: abs(bass.poly_area(p)))


def _half_xf(t):
    """Placement of OPPO (0) and SITE (1): (dx, dy, rot, scale) about each half's own centre,
    from the title's rest place to the facades."""
    u = k(t, T_PART, 0.75, "inout3")
    r = k(t, T_PART + 0.25, 0.6, "inout5")
    T = title()
    out = []
    for h, (target, rot) in enumerate((((260.0, 980.0), 0.0), ((820.0, 720.0), 180.0))):
        gl = T[:4] if h == 0 else T[4:]
        bb = bass.bbox([p for g in gl for p in g.polys])
        hc = ((bb[0] + bb[2]) / 2 + 540.0, (bb[1] + bb[3]) / 2 + 960.0)
        out.append((hc, lerp(hc, target, u), rot * r, lerp(1.0, 0.82, u)))
    return out


def _letter_world(i, t):
    """Contours of letter i in world px (title placed at its half's transform)."""
    T = title()
    hc, pos, rot, s = _half_xf(t)[0 if i < 4 else 1]
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for p in T[i].polys:
        q = []
        for x, y in p:
            x, y = (x + 540.0 - hc[0]) * s, (y + 960.0 - hc[1]) * s
            q.append((pos[0] + x * ca - y * sa, pos[1] + x * sa + y * ca))
        out.append(q)
    return out


def _letter_window(i):
    # O P P O -> her facade's windows (reading order); E T I S (upside down) -> his
    return LEFT_WIN[i] if i < 4 else RIGHT_WIN[(7 - i)]


def draw_title_shot(c, t):
    fill(c, INK)
    # the paper ground floods in behind the halves (vertical bars, alternately from the top
    # and the bottom), then the two slabs rise
    flood = k(t, T_FLOOD, 0.4, "linear")
    if flood > 0:
        bass.bars(c, flood, n=6, axis="v", colors=(PAPER,), frm="alt", mode="slide", overlap=0.5, seed=4, bleed=3.0)
    for j, B in enumerate((LEFT_B, RIGHT_B)):
        rise = k(t, T_RISE + 0.12 * j, 0.55, "outback")
        if rise > 0:
            c.save()
            c.translate(0.0, (1.0 - rise) * 1500.0)
            bass.fill_polys(c, [bass.cut_rect(*B, seed=20 + j)], INK)
            c.restore()
    # Psycho strips through the black at the start
    if t < 1.6:
        bass.bars(c, k(t, 0.0, 1.5, "linear"), n=9, axis="h", colors=(DIM,), frm="alt", mode="inout",
                  lengths="random", overlap=0.55, seed=3)
    morph = k(t, T_MORPH, 0.8, "inout3")
    dark = t >= T_DARK
    if not dark:
        # the letters: PAPER drawn as a difference, so they read on black and on paper alike
        c.save()
        c.set_operator(cairo.OPERATOR_DIFFERENCE)
        if t < T_PART:
            T = title()
            split = 1.0 - k(t, 0.25, 1.35, "out5")
            bass.draw_title(c, T, (540.0, 960.0), PAPER, anim="split" if split > 0 else None, u=split,
                            strips=6, angle=0.0, dist=900.0, irregular=0.5, ease="linear", seed=5)
        else:
            for i in range(8):
                polys = _letter_world(i, t)
                if morph > 0:
                    outer = bass.morph_outline(_outer_world(polys), rect_pts(_letter_window(i)), morph, n=120)
                    holes = [_shrink(p, 1.0 - morph) for p in polys if p is not _outer_world(polys)]
                    bass.fill_polys(c, [bass.orient(outer, True)] + [bass.orient(h, False) for h in holes if h], PAPER)
                else:
                    bass.fill_polys(c, polys, PAPER, evenodd=True)
        c.restore()
    else:
        draw_windows(c, t)
    # the red cut between the halves
    if T_TITLE_CUT <= t < T_PART + 0.5:
        u = k(t, T_TITLE_CUT, 0.12, "out3")
        tail = k(t, T_PART + 0.1, 0.3, "in3")
        T = title()
        x = 540.0 + (T[3].bbox[2] + T[4].bbox[0]) / 2
        bass.slash(c, (x + 8.0, 780.0), (x - 8.0, 1140.0), RED, width=30.0, u=u, tail=tail, seed=9)


def _outer_world(polys):
    return max(polys, key=lambda p: abs(bass.poly_area(p)))


def _shrink(p, s):
    cx = sum(x for x, _ in p) / len(p)
    cy = sum(y for _, y in p) / len(p)
    if s <= 0.02:
        return None
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in p]


def his_on(t):
    return T_DARK + 0.35 <= t < T_SLASH[2] + 0.6 or t >= T_HIS_ON


def window_color(r, t):
    """The letters' paper goes dark, window by window, except hers and his (AMBER)."""
    if r == HER_WIN:
        return lerp(PAPER, AMBER, k(t, T_DARK + 0.1, 0.12, "out"))
    if r == HIS_WIN and his_on(t):
        return lerp(PAPER, AMBER, k(t, T_DARK + 0.35, 0.12, "out"))
    i = (LEFT_WIN + RIGHT_WIN).index(r)
    return lerp(PAPER, UNLIT, k(t, T_DARK + 0.06 * ((i * 5) % 8), 0.1, "out"))


def draw_street(c, t):
    fill(c, PAPER)
    for j, B in enumerate((LEFT_B, RIGHT_B)):
        bass.fill_polys(c, [bass.cut_rect(*B, seed=20 + j)], INK)
    draw_windows(c, t)


def draw_windows(c, t):
    for r in LEFT_WIN + RIGHT_WIN:
        bass.fill_polys(c, [bass.cut_rect(*r, seed=int(r[0] + r[1]))], window_color(r, t))
    if t >= T_WIN - 0.6:
        c.save()
        clip_rect(c, HER_WIN)
        her = figs()[0]
        st, p = her_pose(t)
        c.save()
        place(c, HER_WIN[0] + 32.0, HER_WIN[3] + 6.0, WIN_FS)
        draw_cutout(c, her, st, p, INK, facing=1)
        c.restore()
        c.restore()
    if his_on(t):
        c.save()
        clip_rect(c, HIS_WIN)
        if t < T_ARM:
            draw_room_small(c, t)
        else:
            st, p = alone_pose(t)
            if t < T_GONE:
                c.save()
                place(c, HIS_WIN[0] + 92.0 + 260.0 * k(t, T_RETRACT + 0.05, 0.2, "in3"), HIS_WIN[3] + 6.0, WIN_FS)
                draw_cutout(c, figs()[1], st, p, INK, facing=-1)
                c.restore()
        c.restore()


def draw_room_small(c, t):
    man, vic = figs()[1], figs()[2]
    c.save()
    place(c, HIS_WIN[0] + 24.0, HIS_WIN[3] + 6.0, WIN_FS)
    st, p = man_pose(t)
    draw_cutout(c, man, st, p, INK, facing=1)
    c.restore()
    c.save()
    place(c, HIS_WIN[0] + 24.0 + 300.0 * WIN_FS, HIS_WIN[3] + 6.0, WIN_FS)
    st, p = vic_pose(t)
    draw_cutout(c, vic, st, p, INK, facing=-1)
    c.restore()


def draw_windows_shot(c, t):
    """Two windows facing each other; the camera eases in on the street between them while
    the shouting crosses it."""
    z = lerp(1.0, 1.45, k(t, T_WIN, 3.5, "inout"))
    cx, cy = lerp(540.0, 545.0, k(t, T_WIN, 3.5)), lerp(960.0, 860.0, k(t, T_WIN, 3.5))
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-cx, -cy)
    draw_street(c, t)
    a = (HIS_WIN[0] - 4.0, centre(HIS_WIN)[1] - 20.0)
    b = (HER_WIN[2] + 6.0, centre(HER_WIN)[1] - 30.0)
    for j, tb in enumerate(BOLTS):
        if tb > T_EYE:
            break
        bolt(c, (a[0], a[1] + 14.0 * (j % 3 - 1)), (b[0], b[1] + 20.0 * ((j + 1) % 3 - 1)), t, tb, dur=0.42,
             width=13.0, seed=j, amp=24.0, n=7)
    c.restore()


# ----------------------------------------------------------------------------- her eye / his eye
EYE_C = (540.0, 900.0)


def almond(c0, w, h, open_=1.0, n=48):
    """Eye opening: upper and lower lid arcs; open_ squeezes it shut toward the lower lid."""
    top, bot = [], []
    for i in range(n + 1):
        u = i / n
        x = c0[0] - w / 2 + w * u
        s = math.sin(math.pi * u) ** 0.85
        top.append((x, c0[1] + h * 0.18 - h * 0.68 * s * open_))
        bot.append((x, c0[1] + h * 0.18 + h * 0.32 * s))
    return top + bot[::-1][1:-1]


def draw_eye(c, t, open_, look, iris_rgb, reflect=None, mirror=False, pupil=1.0):
    """A Bass eye: an ink band across the face, an almond cut out of it, the iris an ink (or
    red) disc; `reflect(c, rect)` draws what the eye sees, into a small window in the iris."""
    fill(c, PAPER)
    band = bass.cut_rect(-40.0, EYE_C[1] - 330.0, W + 40.0, EYE_C[1] + 330.0, seed=31, amp=3.0)
    lid = almond(EYE_C, 860.0, 420.0, max(open_, 0.0))
    bass.fill_polys(c, [band], INK)
    if open_ <= 0.02:
        return
    c.save()
    c.new_path()
    bass.draw.poly(c, lid)
    c.clip()
    fill(c, PAPER)
    ic = (EYE_C[0] + look * 150.0 * (-1 if mirror else 1), EYE_C[1] - 6.0)
    bass.disc(c, ic, 168.0, iris_rgb, seed=33)
    if reflect is not None:
        rr = (ic[0] - 52.0, ic[1] - 92.4, ic[0] + 52.0, ic[1] + 92.4)
        c.save()
        bass.iris_path(c, ic, 150.0, seed=34)
        c.clip()
        reflect(c, rr)
        c.restore()
    else:
        bass.disc(c, ic, 70.0 * pupil, INK, seed=35)
    bass.disc(c, (ic[0] + 70.0, ic[1] - 72.0), 20.0, PAPER, seed=36)
    c.restore()


def reflect_room(t):
    def fn(c, r):
        bass.fill_polys(c, [bass.cut_rect(*r, seed=41, amp=1.0)], AMBER)
        c.save()
        clip_rect(c, r)
        s = (r[2] - r[0]) / W
        c.translate(r[0], r[1])
        c.scale(s, s)
        draw_room(c, t, zoom_cam=False)
        c.restore()
    return fn


def draw_her_eye_shot(c, t):
    look = lerp(-0.25, 0.42, k(t, T_EYE + 0.35, 0.16, "outback")) + 0.03 * math.sin(7.0 * t)
    blink = 1.0 - (k(t, 9.62, 0.06, "in") - k(t, 9.74, 0.08, "out"))
    open_ = min(k(t, T_EYE - 0.05, 0.18, "out3"), blink)
    # into the reflection: the frame rides into the little window in her iris
    z = math.exp(math.log(W / 104.0) * k(t, 10.25, 0.75, "in3"))
    ic = (EYE_C[0] + look * 150.0, EYE_C[1] - 6.0)
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-lerp(540.0, ic[0], k(t, 10.25, 0.4, "out")), -lerp(960.0, ic[1], k(t, 10.25, 0.4, "out")))
    draw_eye(c, t, open_, look, INK, reflect=reflect_room(t))
    c.restore()


# ----------------------------------------------------------------------------- his room (the quarrel, the knife)
ROOM_FS = 1.18
ROOM_FLOOR = 1560.0
MAN_X, VIC_X = 345.0, 345.0 + 300.0 * ROOM_FS


def room_zoom(t):
    """The frame jumps closer on the beat as the quarrel rises (cut-in jumps, not a move)."""
    steps = [(T_ROOM, 1.0), (12.0, 1.07), (12.5, 1.14), (13.0, 1.22), (13.5, 1.3), (T_RAISE, 1.18)]
    z = steps[0][1]
    for (t0, v0), (t1, v1) in zip(steps, steps[1:]):
        z = lerp(z, v1, k(t, t1, 0.07, "out5"))
    return z


def vic_burst(t):
    """She comes apart: from the first cut every piece flies loose and falls out of frame."""
    t0 = T_SLASH[0] + 0.02
    if t < t0:
        return None
    d = t - t0

    def fn(name, centre):
        h = zlib.crc32(name.encode()) % 997
        vx = (hash01(h, 1) - 0.35) * 520.0
        vy = -260.0 - 380.0 * hash01(h, 2)
        w = (hash01(h, 3) - 0.5) * 540.0
        return (vx * d, vy * d + 0.5 * 2600.0 * d * d, w * d)
    return fn


def draw_room(c, t, zoom_cam=True):
    fill(c, AMBER)
    bass.fill_polys(c, [bass.cut_rect(-40.0, ROOM_FLOOR, W + 40.0, H + 40.0, seed=51, amp=2.0)], INK)
    man, vic = figs()[1], figs()[2]
    c.save()
    if zoom_cam:
        z = room_zoom(t)
        c.translate(540.0, 1150.0)
        c.scale(z, z)
        c.translate(-540.0, -1150.0)
    gap = 13.0 + 9.0 * k(t, 12.0, 2.0)
    c.save()
    place(c, VIC_X, ROOM_FLOOR, ROOM_FS)
    st, p = vic_pose(t)
    jv = draw_cutout(c, vic, st, p, INK, facing=-1, gap=gap, burst=vic_burst(t))
    c.restore()
    c.save()
    place(c, MAN_X, ROOM_FLOOR, ROOM_FS)
    st, p = man_pose(t)
    jm = draw_cutout(c, man, st, p, INK, facing=1, gap=gap)
    c.restore()
    # shouting between their mouths
    mm = (MAN_X + jm["mouth"][0] * ROOM_FS, ROOM_FLOOR + jm["mouth"][1] * ROOM_FS)
    mv = (VIC_X + jv["mouth"][0] * ROOM_FS, ROOM_FLOOR + jv["mouth"][1] * ROOM_FS)
    for j, tb in enumerate(BOLTS):
        if tb < T_EYE - 0.3 or tb > T_RAISE:
            continue
        a, b = (mm, mv) if j % 2 == 0 else (mv, mm)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 40.0)
        bolt(c, a, (mid[0] + (b[0] - a[0]) * 0.35, mid[1] - 60.0 - 40.0 * (j % 3)), t, tb, dur=0.38,
             width=22.0, seed=10 + j, amp=30.0, n=5)
    c.restore()


def draw_room_shot(c, t):
    draw_room(c, t)


def _split(c, src, t, t0, p, ang, seed):
    """Paint pattern `src` cut along the line through p at angle ang (deg): the two halves
    slide apart along the cut and open on red."""
    u = k(t, t0, 0.09, "out3")
    if u <= 0:
        c.set_source(src)
        c.paint()
        return
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])
    gap = 34.0 * u + 10.0 * k(t, t0 + 0.09, 0.6, "out")
    slide = 70.0 * u
    fill(c, RED)
    BIG = 5000.0
    for s in (-1.0, 1.0):
        c.save()
        c.translate(n[0] * gap * 0.5 * s + d[0] * slide * s, n[1] * gap * 0.5 * s + d[1] * slide * s)
        c.new_path()
        p0 = (p[0] - d[0] * BIG, p[1] - d[1] * BIG)
        p1 = (p[0] + d[0] * BIG, p[1] + d[1] * BIG)
        c.move_to(*p0)
        c.line_to(*p1)
        c.line_to(p1[0] + n[0] * BIG * s, p1[1] + n[1] * BIG * s)
        c.line_to(p0[0] + n[0] * BIG * s, p0[1] + n[1] * BIG * s)
        c.close_path()
        c.clip()
        c.set_source(src)
        c.paint()
        c.restore()


CUTS = ((T_SLASH[0], (560.0, 980.0), 62.0), (T_SLASH[1], (520.0, 1080.0), -48.0), (T_SLASH[2], (540.0, 900.0), 12.0))


def draw_knife_shot(c, t):
    c.push_group()
    draw_room(c, t)
    src = c.pop_group()
    for j, (t0, p, ang) in enumerate(CUTS):
        if t < t0:
            break
        c.push_group()
        _split(c, src, t, t0, p, ang, j)
        src = c.pop_group()
    c.set_source(src)
    c.paint()
    # the knife's flash on each cut: a white sliver along the line, there and gone
    for t0, p, ang in CUTS:
        if t0 <= t < t0 + 0.12:
            a = math.radians(ang)
            u = k(t, t0, 0.06, "out3")
            tail = k(t, t0 + 0.05, 0.07, "in")
            bass.slash(c, (p[0] - math.cos(a) * 1200, p[1] - math.sin(a) * 1200),
                       (p[0] + math.cos(a) * 1200, p[1] + math.sin(a) * 1200), PAPER, width=26.0, u=u, tail=tail)
    # his light goes out: bars close the frame
    if t >= T_BARS:
        bass.bars(c, k(t, T_BARS, 0.5, "linear"), n=9, axis="h", colors=(INK,), frm="alt", mode="slide",
                  overlap=0.6, seed=8, bleed=3.0)


# ----------------------------------------------------------------------------- her: the mug
# her face in profile, enormous, cut from one sheet: brow, nose, lips, chin, the bob behind
PROFILE = bass.scissor([
    (300, 1960), (300, 1120), (262, 1010), (236, 880), (232, 720), (262, 560), (330, 450), (430, 392),
    (530, 392), (604, 440), (640, 520), (652, 600), (640, 650), (650, 690), (700, 780), (742, 838),
    (730, 858), (684, 866), (690, 890), (708, 914), (690, 934), (668, 940), (690, 962), (684, 990),
    (650, 1010), (668, 1040), (660, 1090), (610, 1120), (566, 1130), (560, 1250), (640, 1340),
    (900, 1460), (1120, 1520), (1120, 1960)], seed=301, sag=0.8, amp=1.2, max_len=60.0, corner=36.0)
BOB = bass.scissor([
    (210, 1010), (190, 820), (205, 640), (262, 500), (360, 400), (470, 360), (580, 380), (650, 450),
    (676, 540), (640, 560), (560, 520), (470, 540), (430, 600), (410, 760), (420, 960), (380, 1040),
    (290, 1050)], seed=302, sag=0.8, amp=1.2, max_len=60.0, corner=36.0)
EYE_P = (590.0, 640.0)
HAND_AT = (720.0, 935.0)
MUG_X = 880.0


def mug_pos(t):
    """Falling past her face, turning; it hits the floor at T_SMASH."""
    u = clamp((t - T_DROP) / (T_SMASH - T_DROP))
    return (lerp(900.0, MUG_X, u), lerp(420.0, 1480.0, u * u)), -170.0 * u


def shards():
    out = []
    for i in range(16):
        a = math.radians(-170.0 + 160.0 * hash01(i, 1))
        v = 380.0 + 620.0 * hash01(i, 2)
        size = 26.0 + 60.0 * hash01(i, 3)
        out.append((math.cos(a) * v, math.sin(a) * v, (hash01(i, 4) - 0.5) * 900.0, size, i))
    return out


def hand_parts():
    """Her hand clamped over her mouth, fingers along her cheek toward her ear: cut strips
    (origin at the palm)."""
    parts = [bass.cut([(-30, -70), (70, -60), (80, 70), (-40, 80)], seed=311, amp=1.0)]
    for j, (y0, ang, L) in enumerate(((-52.0, 192.0, 150.0), (-18.0, 184.0, 178.0), (16.0, 178.0, 170.0),
                                      (50.0, 170.0, 136.0))):
        a = math.radians(ang)
        parts.append(bass.capsule_pts((-20.0, y0), (-20.0 + math.cos(a) * L, y0 + math.sin(a) * L), 17.0, 15.0, 5))
    parts.append(bass.capsule_pts((10.0, -60.0), (-70.0, -150.0), 19.0, 16.0, 5))           # thumb, up the nose
    parts.append(bass.capsule_pts((40.0, 60.0), (130.0, 640.0), 50.0, 60.0, 6))             # wrist, forearm
    return [bass.orient(p, True) for p in parts]


def draw_mug_shot(c, t):
    fill(c, PAPER)
    floor = 1560.0
    bass.fill_polys(c, [bass.cut_rect(-40.0, floor, W + 40.0, H + 40.0, seed=61, amp=2.0)], INK)
    bass.fill_polys(c, [bass.orient(PROFILE, True), bass.orient(BOB, True)], INK)
    # the eye: a paper almond, wide on the gasp
    wide = 1.0 + 0.7 * k(t, T_GASP, 0.1, "outback")
    eye = almond((EYE_P[0], EYE_P[1] - 10.0 * (wide - 1.0)), 84.0, 40.0 * wide)
    bass.fill_polys(c, [eye], PAPER)
    bass.disc(c, (EYE_P[0] + 20.0, EYE_P[1] - 4.0), 11.0 * (2.0 - wide * 0.6), INK, seed=312)
    # her hand flies up over her mouth: a paper edge keeps it apart from her face
    hu = k(t, T_HAND, 0.14, "outback")
    if hu > 0:
        c.save()
        c.translate(HAND_AT[0] + (1.0 - hu) * 200.0, HAND_AT[1] + (1.0 - hu) * 1000.0)
        parts = hand_parts()
        c.new_path()
        for p in parts:
            bass.draw.poly(c, p)
        c.set_source_rgb(*PAPER)
        c.set_line_width(12.0)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.stroke()
        bass.fill_polys(c, parts, INK)
        c.restore()
    # the mug
    if T_DROP <= t < T_SMASH:
        (x, y), rot = mug_pos(twos(t))
        c.save()
        c.translate(x, y)
        c.rotate(math.radians(rot))
        c.scale(5.0, 5.0)
        mug_shape(c, INK)
        c.restore()
    elif T_MUG <= t < T_DROP:
        c.save()
        c.translate(900.0, 420.0 + 30.0 * k(t, T_MUG, 0.3))
        c.scale(5.0, 5.0)
        mug_shape(c, INK, steam_t=t)
        c.restore()
    if t >= T_SMASH:
        d = twos(t) - T_SMASH
        for vx, vy, w, size, i in shards():
            x = MUG_X + vx * d * 0.7
            y = min(floor + 4.0, floor - 40.0 + vy * d + 0.5 * 3200.0 * d * d)
            rot = w * min(d, 0.6)
            bass.fill_polys(c, [bass.triangle_pts((x, y), size, rot, seed=70 + i)], INK)


# ----------------------------------------------------------------------------- his arm across the street
def arm_points(t):
    """From his shoulder in the window to her window."""
    base = (HIS_WIN[0] + 80.0, HIS_WIN[3] + 6.0 - 568.0 * WIN_FS)
    tip = (HER_WIN[2] - 14.0, centre(HER_WIN)[1] - 20.0)
    return base, tip


def draw_arm_shot(c, t):
    shake = 6.0 * k(t, T_GROW + 0.6, 0.1) * (1.0 - k(t, T_RETRACT, 0.2))
    tilt = -4.0 * k(t, T_GROW, 0.8, "inout3") * (1.0 - k(t, T_RETRACT + 0.2, 0.4))
    c.save()
    c.translate(540.0, 960.0)
    c.rotate(math.radians(tilt))
    c.translate(-540.0 + shake * math.sin(t * 61.0), -960.0 + shake * math.cos(t * 47.0))
    draw_street(c, t)
    grow = k(t, T_GROW, 0.7, "out3") * (1.0 - k(t, T_RETRACT, 0.18, "in3"))
    if grow > 0:
        base, tip = arm_points(t)
        bass.jagged_arm(c, base, tip, RED, width=38.0, grow=grow, jags=5, jag=1.0, claw=0.7, seed=4)
    c.restore()


# ----------------------------------------------------------------------------- her light off
def draw_off_shot(c, t):
    z = lerp(1.0, 3.3, k(t, T_OFF, 0.35, "out5"))
    cc = centre(HER_WIN)
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-cc[0], -cc[1] + 10.0)
    off = t >= T_PULL + 0.04
    draw_street(c, t)
    if off:
        bass.fill_polys(c, [bass.cut_rect(*HER_WIN, seed=int(HER_WIN[0] + HER_WIN[1]))], INK)
    else:
        # the cord, from the top of her window
        cx = HER_WIN[0] + 92.0
        pull = 12.0 * k(t, T_PULL, 0.05)
        c.save()
        c.set_source_rgb(*INK)
        c.set_line_width(2.0)
        c.move_to(cx, HER_WIN[1])
        c.line_to(cx, HER_WIN[1] + 42.0 + pull)
        c.stroke()
        c.restore()
    c.restore()
    # the flip: two frames negative, then the dark
    if T_PULL <= t < T_PULL + 2.0 / 24.0:
        c.save()
        c.set_operator(cairo.OPERATOR_DIFFERENCE)
        fill(c, (1.0, 1.0, 1.0))
        c.set_operator(cairo.OPERATOR_HSL_SATURATION)
        fill(c, (0.5, 0.5, 0.5))
        c.restore()
    if t >= T_PULL + 2.0 / 24.0:
        fill(c, INK, alpha=k(t, T_PULL + 2.0 / 24.0, 0.25, "out"))


# ----------------------------------------------------------------------------- the path in the dark
FLOOR = 300.0
LB = (0.0, 1100.0)          # her building x range (diagram world)
RB = (1600.0, 2700.0)       # his building
STREET = (1100.0, 1600.0)
HER_ROOM_Y = -3 * FLOOR     # her floor (3)
HIS_ROOM_Y = -4 * FLOOR     # his floor (4)


def _stairs(x0, x1, y_from, y_to):
    """Zigzag flights between y_from and y_to, switching back between x0 and x1 each floor."""
    pts = []
    n = int(round(abs(y_to - y_from) / FLOOR))
    sgn = 1 if y_to > y_from else -1
    for i in range(n + 1):
        y = y_from + sgn * FLOOR * i
        pts.append((x0 if i % 2 == 0 else x1, y))
    return pts


@lru_cache(maxsize=1)
def path_pts():
    p = [(2300.0, HIS_ROOM_Y - 40.0), (2050.0, HIS_ROOM_Y)]
    p += _stairs(1850.0, 2100.0, HIS_ROOM_Y, 0.0)
    p += [(1600.0, 0.0), (1100.0, 0.0)]
    p += _stairs(850.0, 600.0, 0.0, HER_ROOM_Y)
    p += [(380.0, HER_ROOM_Y), (300.0, HER_ROOM_Y - 40.0)]
    return p


def _plen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


@lru_cache(maxsize=1)
def path_steps():
    """Footfall times on the path and how far along (0..1) each one puts him: down his
    stairs, across at a run, up hers, along to her door."""
    pts = path_pts()
    L = _plen(pts)
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    i_out = pts.index((1600.0, 0.0))
    i_in = pts.index((1100.0, 0.0))
    s_cross0, s_cross1 = cum[i_out] / L, cum[i_in] / L
    times, fr = [], []
    t = T_PATH + 0.15
    for i in range(10):                                # down his stairs
        t += 0.15
        times.append(t)
        fr.append(s_cross0 * (i + 1) / 10)
    for i in range(5):                                 # across the street at a run
        t += 0.2
        times.append(t)
        fr.append(lerp(s_cross0, s_cross1, (i + 1) / 5))
    for i in range(12):                                # up hers, faster and faster
        t += lerp(0.17, 0.12, i / 11)
        times.append(t)
        fr.append(lerp(s_cross1, 0.93, (i + 1) / 12))
    for i in range(3):                                 # along to her door
        t += 0.26
        times.append(t)
        fr.append(lerp(0.93, 1.0, (i + 1) / 3))
    return list(zip(times, fr))


def path_u(t):
    """How far along the path (0..1): each footfall jumps it on, crisply."""
    u = prev = 0.0
    for t0, f in path_steps():
        if t < t0 - 0.05:
            break
        u = lerp(prev, f, k(t, t0 - 0.05, 0.08, "out3"))
        prev = f
    return u


def _point_at(pts, u):
    L = _plen(pts) * clamp(u)
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        if L <= d:
            f = L / (d or 1.0)
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        L -= d
    return pts[-1]


def draw_path_shot(c, t):
    fill(c, INK)
    u = path_u(t)
    head = _point_at(path_pts(), u)
    # the camera follows the head of the line, lagging (a slow glide over each jump)
    lag = 0.35
    hp = _point_at(path_pts(), path_u(t - lag * 0.5))
    z = 0.82
    cx = clamp(lerp(hp[0], head[0], 0.5), 560.0, 2140.0)
    cy = lerp(hp[1], head[1], 0.5) - 120.0
    intro = k(t, T_PATH, 0.5, "out3")
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z * lerp(1.6, 1.0, intro), z * lerp(1.6, 1.0, intro))
    c.translate(-cx, -cy)
    lw = 10.0
    lines = []
    for x0, x1 in (LB, RB):
        top = -5 * FLOOR
        lines.append([(x0, 60.0), (x0, top), (x1, top), (x1, 60.0)])
        for f in range(1, 5):
            lines.append([(x0, -f * FLOOR), (x1, -f * FLOOR)])
    lines.append([(-600.0, 0.0), (3300.0, 0.0)])
    reveal = k(t, T_PATH, 0.7, "out3")
    for j, ln in enumerate(lines):
        bass.line_band(c, ln, DIM, width=lw, u=reveal, seed=80 + j)
    # the two rooms: his lit, hers dark with her in it
    bass.fill_polys(c, [bass.cut_rect(2250.0, HIS_ROOM_Y - 200.0, 2550.0, HIS_ROOM_Y - 20.0, seed=91)], AMBER)
    bass.fill_polys(c, [bass.cut_rect(80.0, HER_ROOM_Y - 200.0, 260.0, HER_ROOM_Y - 20.0, seed=92)], UNLIT)
    her = figs()[0]
    st, p = pd.standing(her), pd.Pose(lean=-4.0)
    c.save()
    place(c, 150.0, HER_ROOM_Y - 22.0, 0.26)
    draw_cutout(c, her, st, p, INK, facing=1)
    c.restore()
    # the red line, drawn on step by step, with a dot for his head
    bass.line_band(c, path_pts(), RED, width=22.0, u=u, seed=95)
    if u > 0.001:
        bass.disc(c, head, 22.0, RED, seed=96)
    # her door at the end
    door = (330.0, HER_ROOM_Y - 230.0, 352.0, HER_ROOM_Y)
    bass.fill_polys(c, [bass.cut_rect(*door, seed=97, amp=0.8)], AMBER if u < 0.999 else RED)
    c.restore()


# ----------------------------------------------------------------------------- her door
BAR_Y = 1300.0
KNOB = (745.0, 840.0)
KEYHOLE = (745.0, 960.0)


def keyhole_pts(c0, s=1.0):
    circ = bass.draw.circle_pts((c0[0], c0[1] - 18.0 * s), 22.0 * s, n=28)
    leg = [(c0[0] - 13.0 * s, c0[1]), (c0[0] + 13.0 * s, c0[1]), (c0[0] + 20.0 * s, c0[1] + 62.0 * s),
           (c0[0] - 20.0 * s, c0[1] + 62.0 * s)]
    return circ, leg


def draw_door(c, t):
    fill(c, INK)
    # the door, just: a slightly lighter slab and a frame
    bass.fill_polys(c, [bass.cut_rect(250.0, 260.0, 830.0, BAR_Y - 2.0, seed=101, amp=1.5)], (0.045, 0.042, 0.038))
    # the bar of light under it
    bar = bass.cut_rect(-40.0, BAR_Y, W + 40.0, BAR_Y + 26.0, seed=102, amp=1.2)
    flick = 1.0 - 0.25 * k(t, 29.0, 1.2) * (0.5 + 0.5 * math.sin(t * 9.0))
    bass.fill_polys(c, [bar], lerp(INK, AMBER, flick))
    # his feet cut into it
    fu = k(t, T_FEET - 0.08, 0.16, "out3")
    if fu > 0:
        for j, x in enumerate((410.0, 600.0)):
            xx = lerp(1200.0 + 190.0 * j, x, fu)
            bass.fill_polys(c, [bass.cut_rect(xx, BAR_Y - 6.0, xx + 140.0, BAR_Y + 32.0, seed=103 + j, amp=1.0)], INK)
    # the handle: tried twice (jerky, on twos)
    tt = twos(t)
    turn = 0.0
    for t0 in T_KNOB:
        turn += -38.0 * (k(tt, t0, 0.12, "out3") - k(tt, t0 + 0.32, 0.12, "in3"))
    turn += 2.5 * math.sin(tt * 70.0) * (k(tt, T_KNOB[0], 0.05) - k(tt, T_KNOB[1] + 0.5, 0.05))
    bass.disc(c, KNOB, 44.0, DIM, seed=104)
    c.save()
    c.translate(*KNOB)
    c.rotate(math.radians(turn))
    bass.fill_polys(c, [bass.capsule_pts((0.0, 0.0), (-190.0, 0.0), 22.0, 19.0, 5)], DIM)
    c.restore()
    circ, leg = keyhole_pts(KEYHOLE)
    bass.fill_polys(c, [bass.orient(circ, True), bass.orient(leg, True)], lerp(INK, AMBER, 0.55))


def draw_door_shot(c, t):
    draw_door(c, t)


# ----------------------------------------------------------------------------- the keyhole, his eye
def draw_key_shot(c, t):
    z = math.exp(math.log(30.0) * k(t, T_KEY + 0.1, 0.65, "in3"))
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-KEYHOLE[0], -(KEYHOLE[1] - 4.0))
    draw_door(c, t)
    c.restore()
    if t >= T_KEY + 0.75:
        # through the keyhole: his eye, opposite hers (mirrored, red), shut until he opens it
        c.save()
        s = 1.0
        c.translate(540.0, 960.0)
        c.scale(s, s)
        c.translate(-540.0, -960.0)
        open_ = k(t, T_OPEN, 0.1, "outback")
        look = 0.0 + 0.04 * math.sin(5.0 * t) * k(t, T_OPEN + 0.4, 0.3)
        pupil = 1.0 - 0.45 * k(t, T_OPEN + 0.55, 0.12, "outback")
        draw_eye(c, t, open_, look, RED, mirror=True, pupil=pupil)
        c.restore()
        # the keyhole's edge stays round the picture for a moment, then lets go
        edge = 1.0 - k(t, T_OPEN - 0.1, 0.4, "out3")
        if edge > 0:
            m = lerp(90.0, 30.0, edge)
            circ, leg = keyhole_pts((540.0, 960.0 + 4.0 * m), m)
            c.push_group()
            fill(c, INK)
            c.set_operator(cairo.OPERATOR_CLEAR)
            for poly in (circ, leg):
                c.new_path()
                bass.draw.poly(c, poly)
                c.fill()
            c.pop_group_to_source()
            c.paint()


# ----------------------------------------------------------------------------- end card
def draw_end(c, t):
    fill(c, INK)
    T = title()
    stamp = k(t, T_END, 0.1, "out3")
    s = lerp(1.6, 1.0, stamp)
    apart = 0.0 if t < T_END_SLASH + 0.1 else k(t, T_END_SLASH + 0.1, 0.5, "out5") * 0.08
    bass.draw_title(c, T, (540.0, 960.0), PAPER, anim="split" if apart > 0 else None, u=apart, scale=s,
                    strips=2, angle=-24.0, dist=500.0, ease="linear", irregular=0.0, seed=2)
    if t >= T_END_SLASH:
        u = k(t, T_END_SLASH, 0.1, "out3")
        bass.slash(c, (60.0, 1110.0), (1020.0, 682.0), RED, width=40.0, u=u, seed=12)


# ----------------------------------------------------------------------------- the film
SHOTS = [
    (0.0, draw_title_shot),
    (T_WIN, draw_windows_shot),
    (T_EYE, draw_her_eye_shot),
    (T_ROOM, draw_room_shot),
    (T_RAISE, draw_knife_shot),
    (T_MUG, draw_mug_shot),
    (T_ARM, draw_arm_shot),
    (T_OFF, draw_off_shot),
    (T_PATH, draw_path_shot),
    (T_DOOR, draw_door_shot),
    (T_KEY, draw_key_shot),
    (T_END, draw_end),
]


def shot_at(t):
    fn = SHOTS[0][1]
    for t0, f in SHOTS:
        if t >= t0:
            fn = f
    return fn


def draw(f, t):
    with f.screen() as c:
        if t >= T_BLACK:
            fill(c, (0.0, 0.0, 0.0))
            return
        shot_at(t)(c, t)


def motion_blur_at(t):
    if T_EYE + 1.7 < t < T_ROOM or T_KEY + 0.1 < t < T_KEY + 0.75:
        return 3
    return 1
