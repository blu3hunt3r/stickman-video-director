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
  16.5  MUG      her head in profile, the mug held up under her chin; she gasps, lets it go and
                 the same hand flies to her mouth; it shatters out of shot, the shards fly up.
  18.5  ARM      his window lights; he stands looking at her; his arm grows out of his shoulder
                 across the street to her window, jagged (The Man with the Golden Arm). He is gone.
  21.5  OFF      she pulls the cord: the picture flips negative and goes dark.
  22.5  PATH     a diagram in the dark: a red line walks, step by step, down his stairs,
                 across the street, up hers, to her door.
  28.5  DOOR     the bar of light under her door; his shadow takes it a step at a time; two feet
                 cut into it; the handle turns, twice.
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
T_HAND = 17.17            # the hand that dropped it lands over her mouth
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
        p.hold["near"] = mug_hold(t)
        # before and after the sip she holds the mug at her chest, forearm level
        w = 1.0 - k(t, 5.2, 0.4) + k(t, 8.05, 0.45)
        if w > 0.0:
            p.arms["near"] = _toward(p.arms["near"], 14.0 - p.lean, 84.0, min(w, 1.0))
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
    if t >= T_RAISE + 0.06:
        # out of his coat on the way up; raised: the blade points up and back over his head;
        # plunging: it points down
        p.hold["near"] = knife_hold(lerp(-112.0, 78.0, S_))
    return st, p


def alone_pose(t):
    return perfs()[2](twos(t))


def vic_pose(t):
    st, p = perfs()[3](twos(t))
    w = k(t, T_RAISE + 0.1, 0.25, "out3") * (1.0 - k(t, T_SLASH[0] + 0.05, 0.12))
    if w > 0.0:
        p.arms["near"] = _toward(p.arms["near"], 58.0 - p.lean, 108.0, w)
        p.arms["far"] = _toward(p.arms["far"], 40.0 - p.lean, 128.0, w)
    return st, p


_HILT = bass.cut([(-6, -7), (16, -7), (16, 7), (-6, 7)], seed=62, amp=0.2)
_BLADE = bass.cut([(16, -10), (120, -3), (150, 5), (16, 10)], seed=63, amp=0.2)


def knife_hold(ang):
    """An overhand grip: the hilt in the fist, the blade pointing at world angle `ang` (deg,
    for a figure facing +x: -90 straight up, 90 straight down)."""
    def fn(c, H):
        a = ang if H["facing"] > 0 else 180.0 - ang
        c.save()
        c.translate(*H["hc"])
        c.rotate(math.radians(a))
        bass.fill_polys(c, [_HILT], INK)
        bass.fill_polys(c, [_BLADE], PAPER)
        c.restore()
    return fn


# a mug held by its handle (origin in the fist), the body forward of the hand
_MUG_BODY = [(5.0, -26.0), (35.0, -26.0), (34.0, 12.0), (6.0, 12.0)]
_MUG_RIM = (20.0, -26.0)


def _mug_handle(c):
    c.new_path()
    c.arc_negative(5.0, -7.0, 9.5, math.radians(-80.0), math.radians(80.0))


def mug_shape(c, color, edge=None, edge_w=6.0):
    """The mug in mug units (handle centre at the origin), with an optional paper edge so it
    reads against a body of the same ink."""
    if edge is not None:
        c.save()
        c.set_source_rgb(*edge)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.new_path()
        bass.draw.poly(c, _MUG_BODY)
        c.set_line_width(edge_w)
        c.stroke()
        _mug_handle(c)
        c.set_line_width(5.0 + edge_w)
        c.stroke()
        c.restore()
    bass.fill_polys(c, [bass.orient(_MUG_BODY, True)], color)
    c.save()
    _mug_handle(c)
    c.set_line_width(5.0)
    c.set_source_rgb(*color)
    c.stroke()
    c.restore()


def steam(c, at, t, color, alpha=1.0, scale=1.0):
    """Two curls of steam rising straight up from `at` (world), whatever the mug is doing."""
    if alpha <= 0.02:
        return
    c.save()
    c.translate(*at)
    c.scale(scale, scale)
    c.set_line_width(3.0)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for j, x0 in enumerate((-6.0, 5.0)):
        c.new_path()
        for i in range(14):
            u = i / 13.0
            x = x0 + 5.0 * math.sin(2 * math.pi * (u * 1.2 - t * 0.9) + j * 2.0) * u
            y = -6.0 - 34.0 * u
            c.line_to(x, y) if i else c.move_to(x, y)
        c.set_source_rgba(*color, 0.8 * alpha)
        c.stroke()
    c.restore()


def mug_hold(t):
    """Her mug, gripped by the handle: upright until the hand nears her mouth, then tipped
    rim-first toward her lips; the steam rises straight up and stops while she drinks."""
    def fn(c, H):
        hc, f = H["hc"], H["facing"]
        dm = math.dist(hc, H["mouth"])
        tilt = 74.0 * ease("inout", clamp((125.0 - dm) / 80.0))
        c.save()
        c.translate(*hc)
        c.scale(f, 1.0)
        c.rotate(math.radians(-tilt))
        mug_shape(c, INK, edge=H.get("edge"))
        rim = c.user_to_device(*_MUG_RIM)
        c.restore()
        rim = c.device_to_user(*rim)
        steam(c, rim, twos(t), INK, alpha=1.0 - clamp(tilt / 30.0))
    return fn


# ----------------------------------------------------------------------------- exploded cut-outs
def _hand_local(fig, kind):
    """Hand outline in the hand's own frame: x along the forearm from the wrist, y toward the
    thumb. Returns (palm polygon, thumb polygon or None, length)."""
    r, a = fig.hand_r, fig.arm_w[2] / 2.0
    if kind == "fist":
        L, b = 1.75 * r, 0.95 * r
        palm = [(0.0, -a), (0.3 * L, -b), (0.78 * L, -1.02 * b), (L, -0.55 * b), (1.04 * L, 0.0), (L, 0.55 * b),
                (0.78 * L, 0.98 * b), (0.42 * L, 1.08 * b), (0.12 * L, 0.85 * b), (0.0, a)]
        return palm, None, L
    L, b = 2.3 * r, 0.8 * r
    palm = [(0.0, -a), (0.35 * L, -b), (0.74 * L, -0.95 * b), (0.92 * L, -0.66 * b), (L, -0.15 * b),
            (0.97 * L, 0.3 * b), (0.86 * L, 0.6 * b), (0.6 * L, 0.72 * b), (0.25 * L, 0.85 * b), (0.0, a)]
    thumb = [(0.2 * L, 0.6 * b), (0.46 * L, 0.95 * b), (0.57 * L, 1.38 * b), (0.5 * L, 1.6 * b), (0.4 * L, 1.42 * b),
             (0.29 * L, 1.0 * b)]
    return palm, thumb, L


def hand_poly(fig, kind, base, u, n, thumb=1.0):
    """World outline of a hand at wrist `base`, forearm direction u, thumb side n; thumb (0..1)
    scales the thumb out of the palm (it shrinks away where the side flips)."""
    palm, th, L = _hand_local(fig, kind)
    pts = list(palm)
    if th is not None and thumb > 0.05:
        y0 = 0.6 * fig.hand_r * 0.8
        tp = [(x, y0 + (y - y0) * thumb) for x, y in th[1:]]
        pts = palm[:8] + tp + palm[8:]              # the thumb lobe sits between knuckles and wrist
    w = [(base[0] + u[0] * x + n[0] * y, base[1] + u[1] * x + n[1] * y) for x, y in pts]
    return bass.orient(w, True), L


def _shorten(a, b, g):
    d = math.dist(a, b) or 1.0
    g = min(g, d * 0.3)
    ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
    return (a[0] + ux * g, a[1] + uy * g), (b[0] - ux * g, b[1] - uy * g)


def draw_cutout(c, fig, st, pose, color, facing=1, gap=0.0, burst=None, far=None, edge=None, hide=()):
    """Draw a paperdoll figure as separate pieces of cut paper (Anatomy of a Murder): each
    limb segment, the torso, head, hands and feet are their own shapes with `gap` px of paper
    between them. burst(name, centre) -> (dx, dy, deg) moves a piece (coming apart). edge: the
    colour behind the figure, for the paper edge of held things. hide: arms not to draw."""
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

    def moved(name, centre, fn):
        dx, dy, deg = burst(name, centre) if burst is not None else (0.0, 0.0, 0.0)
        c.save()
        c.translate(centre[0] + dx, centre[1] + dy)
        c.rotate(math.radians(deg))
        c.translate(-centre[0], -centre[1])
        fn()
        c.restore()

    out = {}
    # the mouth (for the mug): on the face, turned with the head
    m = pd._rot((36.0, -32.0), -pose.head)
    out["mouth"] = Wd((fig.neck[0] + m[0], fig.neck[1] - gap * 1.2 + m[1]))
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
        out["shoulder_" + side] = sh
        if side in hide:
            return
        w0, w1, w2 = fig.arm_w
        d = math.dist(wr, el) or 1.0
        u = ((wr[0] - el[0]) / d, (wr[1] - el[1]) / d)
        seg("upper_" + side, sh, el, w0 / 2, w1 / 2, rgb)
        seg("fore_" + side, el, wr, w1 / 2, w2 / 2, rgb)
        hold = pose.hold.get(side)
        base = (wr[0] + u[0] * gap * 0.7, wr[1] + u[1] * gap * 0.7)
        n1 = (-u[1], u[0])
        sc = n1[0] * facing - 0.6 * n1[1]               # thumb forward and up
        n = n1 if sc >= 0 else (-n1[0], -n1[1])
        poly, L = hand_poly(fig, "fist" if hold is not None else "open", base, u, n, thumb=clamp(abs(sc) * 3.0))
        hc = (base[0] + u[0] * 0.5 * L, base[1] + u[1] * 0.5 * L)
        out["hand_" + side] = hc

        def fn():
            if hold is not None:
                hold(c, dict(hc=hc, wrist=base, u=u, n=n, facing=facing, mouth=out["mouth"], edge=edge))
            bass.fill_polys(c, [poly], rgb)
        moved("hand_" + side, hc, fn)

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
        out.append((hc, lerp(hc, target, u), rot * r, lerp(1.0, 0.64, u)))
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
            # footing below the frame, so the overshoot never lifts the slab off the ground
            bass.fill_polys(c, [bass.orient(rect_pts((B[0] + 3.0, B[3] - 40.0, B[2] - 3.0, B[3] + 400.0)), True)], INK)
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
                    holes = [_shrink(p, 1.0 - clamp(morph * 2.2)) for p in polys if p is not _outer_world(polys)]
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
    return draw_windows(c, t)


def red_arm_out(t):
    return T_GROW - 0.08 <= t < T_RETRACT + 0.2


def draw_windows(c, t):
    """The lit windows and the figures in them. Returns device-space anchors: his shoulder,
    for the red arm; her near hand, for the light cord."""
    anchors = {}
    for r in LEFT_WIN + RIGHT_WIN:
        bass.fill_polys(c, [bass.cut_rect(*r, seed=int(r[0] + r[1]))], window_color(r, t))
    if t >= T_WIN - 0.6:
        c.save()
        clip_rect(c, HER_WIN)
        anchors["her_hand"] = draw_her_window(c, t)
        c.restore()
    if his_on(t):
        c.save()
        clip_rect(c, HIS_WIN)
        if t < T_ARM:
            draw_room_small(c, t)
        elif t < T_GONE:
            anchors["his_shoulder"] = draw_him_alone(c, t)
        c.restore()
    return anchors


def draw_her_window(c, t):
    """Her, in her window. Returns her near hand in device space."""
    st, p = her_pose(t)
    c.save()
    place(c, HER_WIN[0] + 32.0, HER_WIN[3] + 6.0, WIN_FS)
    o = draw_cutout(c, figs()[0], st, p, INK, facing=1, edge=AMBER)
    hand = c.user_to_device(*o["hand_near"])
    c.restore()
    return hand


@lru_cache(maxsize=1)
def cord_end():
    """The light cord hangs from the top of her window to where her hand will take it."""
    surf = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, None)
    return draw_her_window(cairo.Context(surf), T_PULL - 0.06)


def draw_him_alone(c, t):
    """Him alone at his window, after: while the red arm is out it is his arm, and the real
    one is not drawn. Returns his near shoulder in device space."""
    st, p = alone_pose(t)
    c.save()
    place(c, HIS_WIN[0] + 92.0 + 260.0 * k(t, T_RETRACT + 0.05, 0.2, "in3"), HIS_WIN[3] + 6.0, WIN_FS)
    o = draw_cutout(c, figs()[1], st, p, INK, facing=-1, edge=AMBER, hide=("near",) if red_arm_out(t) else ())
    sh = c.user_to_device(*o["shoulder_near"])
    c.restore()
    return sh


def draw_room_small(c, t):
    man, vic = figs()[1], figs()[2]
    c.save()
    place(c, HIS_WIN[0] + 24.0, HIS_WIN[3] + 6.0, WIN_FS)
    st, p = man_pose(t)
    draw_cutout(c, man, st, p, INK, facing=1, edge=AMBER)
    c.restore()
    c.save()
    place(c, HIS_WIN[0] + 24.0 + 300.0 * WIN_FS, HIS_WIN[3] + 6.0, WIN_FS)
    st, p = vic_pose(t)
    draw_cutout(c, vic, st, p, INK, facing=-1, edge=AMBER)
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
    bass.disc(c, (ic[0] + 92.0, ic[1] - 80.0), 18.0, PAPER, seed=36)      # the glint: clear of the reflection
    c.restore()


def reflect_room(t):
    def fn(c, r):
        c.save()
        clip_rect(c, r)                     # everything inside: the dive magnifies any stray edge
        bass.fill_polys(c, [bass.cut_rect(*r, seed=41, amp=1.0)], AMBER)
        s = (r[2] - r[0]) / W
        c.translate(r[0], r[1])
        c.scale(s, s)
        draw_room(c, t)
        c.restore()
    return fn


def draw_her_eye_shot(c, t):
    look = lerp(-0.25, 0.42, k(t, T_EYE + 0.35, 0.16, "outback")) + 0.03 * math.sin(7.0 * t) * (1.0 - k(t, 10.0, 0.2))
    blink = 1.0 - (k(t, 9.62, 0.06, "in") - k(t, 9.74, 0.08, "out"))
    open_ = min(k(t, T_EYE - 0.05, 0.18, "out3"), blink)
    # into the reflection: the frame rides into the little window in her iris
    z = math.exp(math.log(W / 104.0) * k(t, 10.2, 0.72, "in3"))
    ic = (EYE_C[0] + look * 150.0, EYE_C[1] - 6.0)
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-lerp(540.0, ic[0], k(t, 10.2, 0.4, "out")), -lerp(960.0, ic[1], k(t, 10.2, 0.4, "out")))
    draw_eye(c, t, open_, look, INK, reflect=reflect_room(t))
    c.restore()


# ----------------------------------------------------------------------------- his room (the quarrel, the knife)
ROOM_FS = 1.18
ROOM_FLOOR = 1560.0
MAN_X, VIC_X = 345.0, 345.0 + 300.0 * ROOM_FS


def room_zoom(t):
    """The frame jumps closer on the beat as the quarrel rises (cut-in jumps, not a move)."""
    steps = [(T_ROOM, 1.12), (12.0, 1.19), (12.5, 1.26), (13.0, 1.33), (13.5, 1.4), (T_RAISE, 1.25)]
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
    jv = draw_cutout(c, vic, st, p, INK, facing=-1, gap=gap, burst=vic_burst(t), edge=AMBER)
    c.restore()
    c.save()
    place(c, MAN_X, ROOM_FLOOR, ROOM_FS)
    st, p = man_pose(t)
    jm = draw_cutout(c, man, st, p, INK, facing=1, gap=gap, edge=AMBER)
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
CU_S = 7.0                       # the close-up: her hand and the mug at this scale (figure units -> px)
MUG_HC = (745.0, 1262.0)         # her fist on the handle, the mug held up under her chin
MUG_U = (0.34, -0.94)            # her forearm rises from below the frame to the fist
MOUTH_HC = (738.0, 930.0)        # the same hand, clamped over her mouth
MUG_G = 14000.0                  # px/s^2: the mug drops out of the frame well before it lands


def _unit(v):
    d = math.hypot(*v) or 1.0
    return (v[0] / d, v[1] / d)


def _capsule(a, b, r0, r1):
    return bass.orient(bass.capsule_pts(a, b, r0, r1, 6), True)


def edged(c, polys, color, edge, width):
    """Fill polys in `color` over a stroke of `edge`, so a cut piece laid on paper of its own
    colour still shows its edge."""
    c.save()
    c.new_path()
    for p in polys:
        bass.draw.poly(c, p)
    c.set_source_rgb(*edge)
    c.set_line_width(width)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.stroke()
    c.restore()
    bass.fill_polys(c, polys, color)


def _xf(pts, at, ang):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(at[0] + x * ca - y * sa, at[1] + x * sa + y * ca) for x, y in pts]


def cu_open_hand(at, u, spread):
    """Her hand springing open off the handle: palm at `at`, fingers fanned along u."""
    a0 = math.degrees(math.atan2(u[1], u[0]))
    palm = _xf(bass.cut([(-62, -66), (52, -60), (64, 0), (52, 62), (-62, 66)], seed=321, amp=0.6), at, a0)
    polys = [bass.orient(palm, True)]
    tips = []
    for j, (off, da, L, r) in enumerate(((-45.0, -30.0, 118.0, 18.0), (-15.0, -10.0, 138.0, 19.0),
                                         (15.0, 10.0, 130.0, 18.0), (44.0, 28.0, 102.0, 16.0))):
        ang = a0 + da * spread
        base = _xf([(48.0, off)], at, a0)[0]
        tip = (base[0] + math.cos(math.radians(ang)) * L, base[1] + math.sin(math.radians(ang)) * L)
        polys.append(_capsule(base, tip, r, r * 0.85))
        tips.append(tip)
    th0 = _xf([(-6.0, -50.0)], at, a0)[0]                     # the thumb, out to the side
    ang = a0 - 22.0 - 38.0 * spread
    polys.append(_capsule(th0, (th0[0] + math.cos(math.radians(ang)) * 84.0,
                                th0[1] + math.sin(math.radians(ang)) * 84.0), 21.0, 17.0))
    return polys


def cu_mouth_hand():
    """Her hand clamped over her mouth (palm centre at the origin): fingers together across
    her cheek toward her ear, the thumb up beside her nose. Returns (polys, finger cut lines)."""
    polys = [bass.orient(bass.cut([(-40, -70), (44, -78), (58, -10), (40, 80), (-34, 74)], seed=331, amp=0.8),
                         True)]
    cuts = []
    for j, (y0, ang, L, r) in enumerate(((-52.0, 194.0, 168.0, 18.0), (-17.0, 189.0, 186.0, 18.5),
                                         (18.0, 184.0, 176.0, 17.5), (51.0, 178.0, 146.0, 16.0))):
        a = math.radians(ang)
        b0 = (-26.0, y0)
        tip = (b0[0] + math.cos(a) * L, b0[1] + math.sin(a) * L)
        polys.append(_capsule(b0, tip, r, r * 0.88))
        if j:                                                 # the cut between this finger and the last
            pa = math.radians((ang + prev[0]) / 2.0)
            m0 = (b0[0] - 4.0, (y0 + prev[1]) / 2.0)
            Lc = min(L, prev[2]) - 14.0
            cuts.append([(m0[0] + math.cos(pa) * 40.0, m0[1] + math.sin(pa) * 40.0),
                         (m0[0] + math.cos(pa) * Lc, m0[1] + math.sin(pa) * Lc)])
        prev = (ang, y0, L)
    polys.append(_capsule((26.0, -62.0), (-24.0, -136.0), 19.0, 16.0))      # thumb, beside her nose
    return polys, cuts


def mug_hand_at(t):
    """Where her fist holds the mug: it jumps on the gasp and trembles until she lets go."""
    jump = 44.0 * (k(t, T_GASP, 0.07, "out") - k(t, T_GASP + 0.12, 0.35, "inout"))
    shake = 4.0 * math.sin(t * 61.0) * k(t, T_GASP, 0.05)
    return (MUG_HC[0] + shake, MUG_HC[1] - jump)


def mug_fall(t):
    """(handle centre, rotation deg) of the dropped mug: it tips forward and falls out of
    the bottom of the frame long before it lands."""
    x0, y0 = mug_hand_at(T_DROP)
    d = max(0.0, t - T_DROP)
    return (x0 + 90.0 * d, y0 + 0.5 * MUG_G * d * d), 140.0 * min(d / 0.35, 1.0) ** 1.4


def shards():
    out = []
    for i in range(15):
        vx = (hash01(i, 1) - 0.5) * 900.0
        vy = -1500.0 - 750.0 * hash01(i, 2)
        size = 28.0 + 52.0 * hash01(i, 3)
        out.append((vx, vy, (hash01(i, 4) - 0.5) * 1100.0, size, i))
    return out


def draw_mug_hand(c, t):
    """Her near hand and its forearm, rising from the bottom of the frame: on the mug, sprung
    open as she lets it go, then clamped over her mouth."""
    fig = figs()[0]
    swing = k(t, T_HAND - 0.14, 0.14, "out")
    if t < T_HAND - 0.14:
        hc = mug_hand_at(t)
        if t >= T_DROP:
            hc = (hc[0] - 6.0, hc[1] - 16.0 * k(t, T_DROP, 0.05, "out"))
        u = MUG_U
    else:
        h0 = mug_hand_at(T_DROP)
        hc = (lerp(h0[0] - 6.0, MOUTH_HC[0], swing), lerp(h0[1] - 16.0, MOUTH_HC[1], swing))
        u = _unit((lerp(MUG_U[0], 0.05, swing), lerp(MUG_U[1], -1.0, swing)))
    # forearm: from below the frame to the wrist
    wrist = (hc[0] - u[0] * 70.0, hc[1] - u[1] * 70.0) if swing < 1.0 else (MOUTH_HC[0] + 8.0, MOUTH_HC[1] + 70.0)
    elbow = (wrist[0] - u[0] * 1100.0, wrist[1] - u[1] * 1100.0)
    arm = _capsule(wrist, elbow, 54.0, 64.0)
    if t < T_DROP:
        n = (u[1], -u[0])
        c.save()
        c.translate(*hc)
        c.scale(CU_S, CU_S)
        mug_shape(c, INK, edge=PAPER, edge_w=1.4)
        rim = c.user_to_device(*_MUG_RIM)
        c.restore()
        fist, L = hand_poly(fig, "fist", (0.0, 0.0), u, n)
        fist = [(hc[0] + (x - u[0] * 0.5 * L) * CU_S, hc[1] + (y - u[1] * 0.5 * L) * CU_S) for x, y in fist]
        edged(c, [arm, bass.orient(fist, True)], INK, PAPER, 10.0)
        return c.device_to_user(*rim)
    if t < T_HAND - 0.14:
        edged(c, [arm] + cu_open_hand(hc, u, k(t, T_DROP, 0.05, "outback")), INK, PAPER, 10.0)
        return None
    polys, cuts = cu_mouth_hand()
    ang = 100.0 * (1.0 - swing)                          # fingers up off the mug, over onto her cheek
    edged(c, [arm] + [_xf(p, hc, ang) for p in polys], INK, PAPER, 12.0)
    c.save()
    c.set_source_rgb(*PAPER)
    c.set_line_width(6.0)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ln in cuts:
        c.new_path()
        bass.draw.poly(c, _xf(ln, hc, ang), close=False)
        c.stroke()
    c.restore()
    return None


def draw_mug_shot(c, t):
    fill(c, PAPER)
    bass.fill_polys(c, [bass.orient(PROFILE, True), bass.orient(BOB, True)], INK)
    # the eye: a paper almond, wide on the gasp
    wide = 1.0 + 0.7 * k(t, T_GASP, 0.1, "outback")
    eye = almond((EYE_P[0], EYE_P[1] - 10.0 * (wide - 1.0)), 84.0, 40.0 * wide)
    bass.fill_polys(c, [eye], PAPER)
    bass.disc(c, (EYE_P[0] + 20.0, EYE_P[1] - 4.0), 11.0 * (2.0 - wide * 0.6), INK, seed=312)
    # the dropped mug, tipping forward as it falls out of the frame
    if T_DROP <= t < T_SMASH:
        (x, y), rot = mug_fall(twos(t))
        if y < H + 400.0:
            c.save()
            c.translate(x, y)
            c.rotate(math.radians(rot))
            c.scale(CU_S, CU_S)
            mug_shape(c, INK, edge=PAPER, edge_w=1.4)
            c.restore()
    rim = draw_mug_hand(c, t)
    # steam: off the rim while she holds it; left hanging in the air when the mug drops
    if rim is not None:
        steam(c, rim, twos(t), INK, alpha=1.0, scale=CU_S * 0.8)
    elif t < T_DROP + 0.4:
        c.save()
        c.translate(MUG_HC[0], MUG_HC[1])
        c.scale(CU_S, CU_S)
        rim0 = c.user_to_device(*_MUG_RIM)
        c.restore()
        r0 = c.device_to_user(*rim0)
        steam(c, (r0[0], r0[1] - 44.0 * (t - T_DROP) / 0.4), twos(T_DROP), INK,
              alpha=1.0 - k(t, T_DROP, 0.4, "in"), scale=CU_S * 0.8)
    # the smash below the frame: shards burst up into it and fall away
    if t >= T_SMASH:
        (x0, _), _ = mug_fall(T_SMASH)
        d = twos(t) - T_SMASH
        for vx, vy, w, size, i in shards():
            x = x0 + vx * d
            y = H + 30.0 + vy * d + 0.5 * 5200.0 * d * d
            if y < H + 80.0:                                  # china: glaze black outside, white within
                ink = i % 3 != 0
                edged(c, [bass.triangle_pts((x, y), size, w * d, seed=70 + i)], INK if ink else PAPER,
                      PAPER if ink else INK, 5.0)


# ----------------------------------------------------------------------------- his arm across the street
def arm_points(shoulder=None):
    """From his shoulder in the window to her window."""
    base = shoulder or (HIS_WIN[0] + 80.0, HIS_WIN[3] + 6.0 - 568.0 * WIN_FS)
    tip = (HER_WIN[2] - 14.0, centre(HER_WIN)[1] - 20.0)
    return base, tip


def draw_arm_shot(c, t):
    shake = 6.0 * k(t, T_GROW + 0.6, 0.1) * (1.0 - k(t, T_RETRACT, 0.2))
    tilt = -4.0 * k(t, T_GROW, 0.8, "inout3") * (1.0 - k(t, T_RETRACT + 0.2, 0.4))
    c.save()
    c.translate(540.0, 960.0)
    c.rotate(math.radians(tilt))
    c.translate(-540.0 + shake * math.sin(t * 61.0), -960.0 + shake * math.cos(t * 47.0))
    anchors = draw_street(c, t)
    grow = k(t, T_GROW, 0.7, "out3") * (1.0 - k(t, T_RETRACT, 0.18, "in3"))
    if grow > 0:
        sh = anchors.get("his_shoulder")
        base, tip = arm_points(c.device_to_user(*sh) if sh else None)
        c.save()
        if sh:                                      # the root stops at his back
            c.rectangle(-4000.0, -4000.0, base[0] + 1.0 + 4000.0, 8000.0)
            c.clip()
        bass.jagged_arm(c, base, tip, RED, width=38.0, grow=grow, jags=5, jag=1.0, claw=0.7, seed=4)
        c.restore()
        if sh and T_ARM <= t < T_GONE:              # his body over the root of the arm
            c.save()
            clip_rect(c, HIS_WIN)
            draw_him_alone(c, t)
            c.restore()
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
    anchors = draw_street(c, t)
    if off:
        bass.fill_polys(c, [bass.cut_rect(*HER_WIN, seed=int(HER_WIN[0] + HER_WIN[1]))], INK)
    else:
        # the cord, from the top of her window down to her hand: hanging until she takes it,
        # then in her fist as she pulls
        x0, y0 = cord_end()
        hand = anchors.get("her_hand")
        end = c.device_to_user(*hand) if t >= T_PULL - 0.06 and hand else (x0, y0)
        c.save()
        c.set_source_rgb(*INK)
        c.set_line_width(2.0)
        c.move_to(x0, HER_WIN[1])
        c.line_to(*end)
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
    p += [(404.0, HER_ROOM_Y), (378.0, HER_ROOM_Y - 40.0)]      # he stops outside her door (x 330-352)
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
HALL_STEPS = (T_DOOR + 0.4, T_DOOR + 0.95, T_DOOR + 1.45)     # his steps along her hall, heard not seen
SHADOW_LEAD = (W + 60.0, 960.0, 840.0, 730.0, 540.0)            # where his shadow reaches, step by step
SHADOW_TONE = (0.0, 0.3, 0.45, 0.58, 0.66)
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
    bass.fill_polys(c, [bar], AMBER)
    # his shadow comes along the hall ahead of him: a step at a time it takes more of the light
    n = sum(k(t, ts, 0.08, "out") for ts in HALL_STEPS) + k(t, T_FEET - 0.08, 0.16, "out3")
    if n > 0.0:
        i = min(int(n), 3)
        f = n - i
        lead = lerp(SHADOW_LEAD[i], SHADOW_LEAD[min(i + 1, 4)], f)
        tone = lerp(SHADOW_TONE[i], SHADOW_TONE[min(i + 1, 4)], f)
        bass.fill_polys(c, [bass.cut_rect(lead, BAR_Y - 1.0, W + 40.0, BAR_Y + 27.0, seed=105, amp=1.0)],
                        lerp(AMBER, INK, tone))
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
    p = k(t, T_KEY + 0.1, 0.65, "inout")           # the keyhole slides to the centre as we push in
    c.save()
    c.translate(lerp(KEYHOLE[0], 540.0, p), lerp(KEYHOLE[1] - 4.0, 960.0, p))
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
    """No motion blur: cut paper moves crisply (sub-frame blur only left stepped ghosts)."""
    return 1
