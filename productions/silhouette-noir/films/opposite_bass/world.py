"""OPPOSITE, the Bass cut: the same story told the way Saul Bass told stories, in flat cut
paper, graphic metaphor and rhythm instead of a camera looking at rooms.

Every beat is one graphic idea, and each one turns into the next:

   0.0  TITLE    Psycho bars race across the black and strips assemble OPPOSITE; a red cut
                 splits it; OPPO and SITE (upside down: opposite) part; paper floods in round
                 two slabs that stood in the dark under the halves, and each letter becomes a
                 window (type -> architecture, North by Northwest).
   5.0  WINDOWS  two lit windows face each other.
   5.6  SIP      close on her, in profile on her window's amber: she lifts the mug to her lips
                 and drinks, eyes lowered. Back on the street, red zigzags of shouting cross
                 from his window to hers.
   8.5  HER EYE  her eye fills the frame; his window is reflected in it; we fall into the
                 reflection (Vertigo).
  11.0  QUARREL  inside his window: the two of them as Anatomy of a Murder cut-outs, every limb
                 a separate piece of paper; the frame jumps closer on the beat; each shout
                 flies from one mouth into the other's face.
  14.0  KNIFE    the knife goes up; three stabs, and each one cuts the picture of her open on
                 red (Psycho) while he stands whole in front of the tear; she comes apart and
                 falls through the floor; bars close the window.
  16.5  MUG      her profile again, the mug under her chin; she gasps, lets it go and the same
                 hand flies to her mouth; it shatters out of shot, the shards fly up.
  18.5  ARM      his window lights; he stands looking at her; his arm grows out of his shoulder
                 across the street to her window, jagged (The Man with the Golden Arm). It
                 snaps back, and he steps out of the light.
  21.5  OFF      she pulls the cord: the picture flips negative and goes dark.
  22.5  PATH     a diagram in the dark: a red line walks, step by step, down his stairs,
                 across the street, up hers, to her door.
  28.5  DOOR     her door in the dark, light under it and across her floor; his shadow takes
                 it a step at a time; two feet cut into it; the handle turns, twice.
  31.5  HIS EYE  in at the keyhole's light; his face comes to it from the other side, and his
                 eye, the mirror of hers, opens in it; through the keyhole to the whole eye.
  33.4  END      OPPOSITE, cut through in red along the slash. Black.

All drawing is in frame px (1080 x 1920, y down), a pure function of film time t. Figures
are paperdoll cut-outs driven by retargeted CMU motion capture (engine/mocap.py), stepped on
twos (12 fps) like stop-motion paper; graphics and camera moves run on ones.
"""
import math
import zlib
from dataclasses import replace
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
T_FLOOD = 2.9              # paper floods in round the two slabs, already standing in the dark
T_RISE = 3.0               # the flood reaches them: two buildings stand under the halves
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
T_RETRACT = 20.9          # his arm snaps back (0.12 s), then he steps out of his window
T_GONE = 21.25
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
def _victim():
    """The woman in his room: long hair down her back and a full skirt, so she is never
    taken for the woman watching (a bob, a slim dress)."""
    f = pd.woman(RED, 1)
    torso = [(pd._cut([(-24, -258), (30, -258), (42, -200), (32, -110), (36, -50), (92, 150), (-80, 150),
                       (-30, -50), (-28, -110), (-38, -200)], 461), "ink"), f.torso[1]]
    hair = (pd._cut([(-30, -348), (-12, -366), (12, -370), (36, -358), (50, -334), (40, -330), (22, -342),
                     (2, -342), (-12, -328), (-20, -296), (-22, -250), (-20, -196), (-34, -186), (-54, -200),
                     (-56, -252), (-52, -306), (-44, -334)], 462), "ink")
    return replace(f, torso=torso, head=[f.head[0], hair])


@lru_cache(maxsize=1)
def figs():
    return pd.woman(RED, 0), pd.man(RED, 0), _victim()


@lru_cache(maxsize=None)
def win_fig(i):
    """Figure i drawn small in a street window: arms and hands a little thicker, so a hand
    and what it holds still read at a fifth of the size."""
    f = figs()[i]
    return replace(f, arm_w=tuple(w * 1.4 for w in f.arm_w), hand_r=f.hand_r * 1.3)


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


def _toward(arm, sh, el, w, we=None):
    we = w if we is None else we
    return ("ang", arm[1] + mc._wrap(sh - arm[1]) * w, arm[2] + mc._wrap(el - arm[2]) * we)


def her_pose(t):
    st, p = perfs()[0](twos(t))
    if t < T_MUG:
        p.hold["near"] = mug_hold(t)
        # before and after the sip she holds the mug at her chest, forearm level
        w = 1.0 - k(t, 5.2, 0.4) + k(t, T_SIP[1] - 0.45, 0.4)
        if w > 0.0:
            p.arms["near"] = _toward(p.arms["near"], 14.0 - p.lean, 84.0, min(w, 1.0))
    if T_OFF <= t:                                 # up to the cord, and pull
        u = k(t, T_OFF + 0.1, 0.25, "out3")
        pull = k(t, T_PULL, 0.08, "out")
        p.arms["near"] = _toward(p.arms["near"], lerp(172.0, 150.0, pull), lerp(4.0, 20.0, pull), u)
        p.head = lerp(p.head, 14.0, u)
    return st, p


STABS = (T_SLASH[0] - 0.13, T_SLASH[1] - 0.1, T_SLASH[2] - 0.1)     # each stab lands, holds, then its cut


def stab_at(t):
    """0 = the knife raised high, 1 = driven home. Each stab snaps home, held until its cut,
    and after each cut but the last the arm snaps back up high: no in-betweens, so the blade
    never sweeps across her face (the shower in Psycho is cut the same way)."""
    s = 0.0
    for i, t0 in enumerate(STABS):
        if t >= t0 - 0.02:
            s = 1.0
        if i < len(STABS) - 1 and t >= T_SLASH[i] + 0.06:
            s = 0.0
    return s


def man_pose(t):
    t2 = twos(t)
    st, p = perfs()[1](t2)
    S_ = stab_at(t)
    w = k(t, T_RAISE, 0.3, "out3") * (1.0 - k(t, T_SLASH[2] + 0.2, 0.5))
    if w > 0.0:
        # raised: the arm straight up, the fist high over his hat (the elbow straightens first,
        # so the forearm never crosses his eyes); stabbing: down and forward into her
        p.arms["near"] = _toward(p.arms["near"], lerp(186.0, 58.0, S_) - p.lean * (1.0 - S_), lerp(-8.0, -20.0, S_), w,
                                 min(1.0, 2.2 * w))
    if t >= T_RAISE + 0.06:
        # an ice-pick grip, out of his coat on the way up: the blade points forward and down
        # from his fist, at her; driven home, its point ends inside her
        p.hold["near"] = knife_hold(lerp(35.0, 58.0, S_))
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


_HILT = bass.cut([(-8, -9), (16, -9), (16, 9), (-8, 9)], seed=62, amp=0.2)
_BLADE = bass.orient(bass.cut([(14, -13), (128, -5), (172, 6), (14, 13)], seed=63, amp=0.2), True)


def knife_hold(ang):
    """An overhand grip: the hilt in the fist, the blade pointing at world angle `ang` (deg,
    for a figure facing +x: -90 straight up, 90 straight down)."""
    def fn(c, H):
        a = ang if H["facing"] > 0 else 180.0 - ang
        c.save()
        c.translate(*H["hc"])
        c.rotate(math.radians(a))
        edged(c, [_BLADE], PAPER, INK, 7.0)
        bass.fill_polys(c, [_HILT], INK)
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
        c.scale(1.35 * f, 1.35)
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


def draw_cutout(c, fig, st, pose, color, facing=1, gap=0.0, burst=None, far=None, edge=None, hide=(),
                outline=None, ow=7.0):
    """Draw a paperdoll figure as separate pieces of cut paper (Anatomy of a Murder): each
    limb segment, the torso, head, hands and feet are their own shapes with `gap` px of paper
    between them. burst(name, centre) -> (dx, dy, deg) moves a piece (coming apart). edge: the
    colour behind the figure, for the paper edge of held things. hide: arms not to draw.
    outline: the near arm and leg are laid on with an `ow` wide edge of this colour, so a limb
    across the body still shows."""
    P = st["pelvis"]
    P = (P[0], P[1] + pose.crouch)
    lean = pose.lean
    far = far or color

    def Wd(p):
        q = pd._rot((p[0], p[1]), lean)
        return (P[0] + facing * q[0], P[1] + q[1])

    def paint(polys, rgb, ol):
        if ol and outline is not None:
            edged(c, polys, rgb, outline, ow)
        else:
            bass.fill_polys(c, polys, rgb)

    def piece(name, polys, rgb, centre, ol=False):
        if burst is not None:
            dx, dy, deg = burst(name, centre)
            if dx or dy or deg:
                c.save()
                c.translate(centre[0] + dx, centre[1] + dy)
                c.rotate(math.radians(deg))
                c.translate(-centre[0], -centre[1])
                paint(polys, rgb, ol)
                c.restore()
                return
        paint(polys, rgb, ol)

    def seg(name, a, b, ra, rb, rgb, ol=False):
        a2, b2 = _shorten(a, b, gap)
        piece(name, [bass.orient(bass.capsule_pts(a2, b2, ra, rb, cap=8), True)], rgb,
              ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), ol)

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
        ol = side == "near"
        seg("thigh_" + side, hip, knee, w0 / 2, w1 / 2, rgb, ol)
        seg("shin_" + side, knee, ank, w1 / 2, w2 / 2, rgb, ol)
        foot = [(ank[0] + facing * x, ank[1] + y + gap * 0.6) for x, y in _rot_poly(fig.foot, -pitch)]
        piece("foot_" + side, [bass.orient(foot, True)], rgb, ank, ol)

    def draw_arm(side, rgb):
        sh, el, wr = arm(side)
        out["shoulder_" + side] = sh
        if side in hide:
            return
        w0, w1, w2 = fig.arm_w
        d = math.dist(wr, el) or 1.0
        u = ((wr[0] - el[0]) / d, (wr[1] - el[1]) / d)
        ol = side == "near"
        seg("upper_" + side, sh, el, w0 / 2, w1 / 2, rgb, ol)
        seg("fore_" + side, el, wr, w1 / 2, w2 / 2, rgb, ol)
        hold = pose.hold.get(side)
        base = (wr[0] - u[0] * gap * 0.6, wr[1] - u[1] * gap * 0.6)      # the hand just off the cuff
        n1 = (-u[1], u[0])
        sc = n1[0] * facing - 0.6 * n1[1]               # thumb forward and up
        n = n1 if sc >= 0 else (-n1[0], -n1[1])
        poly, L = hand_poly(fig, "fist" if hold is not None else "open", base, u, n, thumb=clamp(abs(sc) * 3.0))
        hc = (base[0] + u[0] * 0.5 * L, base[1] + u[1] * 0.5 * L)
        out["hand_" + side] = hc

        def fn():
            if hold is not None:
                hold(c, dict(hc=hc, wrist=base, u=u, n=n, facing=facing, mouth=out["mouth"], edge=edge))
            paint([poly], rgb, ol)
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


T_LEAD = 0.125             # three frames of black before anything moves
STRIPS = tuple((0.13 + 0.12 * i, 0.42) for i in range(9))      # Psycho's bars: (start, crossing time)


def draw_strips(c, t):
    """Psycho's grey bars: thin strips race right across the black one after another, each
    the full width of the frame as it passes, alternately from the left and the right."""
    for i, (t0, dur) in enumerate(STRIPS):
        u = k(t, t0, dur, "inout")
        if not 0.0 < u < 1.0:
            continue
        L = 1300.0
        lead = lerp(0.0, W + L, u)
        x0, x1 = (lead - L, lead) if i % 2 == 0 else (W - lead, W - lead + L)
        y = 170.0 + 1580.0 * ((i * 4) % 9) / 8.0 + 40.0 * (hash01(i, 1) - 0.5)
        h = 26.0 + 64.0 * hash01(i, 2)
        bass.fill_polys(c, [bass.cut_rect(x0, y - h / 2, x1, y + h / 2, seed=60 + i, amp=1.0)], DIM)


def draw_title_shot(c, t):
    fill(c, INK)
    if t < T_LEAD:
        return
    # the paper floods in (vertical bars, alternately from the top and the bottom) round the
    # two slabs, which have stood in the dark under the halves all along: the letters stay
    # paper on black throughout
    flood = k(t, T_FLOOD, 0.4, "linear")
    if flood > 0:
        bass.bars(c, flood, n=6, axis="v", colors=(PAPER,), frm="alt", mode="slide", overlap=0.5, seed=4, bleed=3.0)
        for j, B in enumerate((LEFT_B, RIGHT_B)):
            bass.fill_polys(c, [bass.cut_rect(*B, seed=20 + j)], INK)
    if t < 1.6:
        draw_strips(c, t)
    morph = k(t, T_MORPH, 0.8, "inout3")
    if t < T_DARK:
        if t < T_PART:
            T = title()
            split = 1.0 - k(t, 0.3, 1.3, "out5")
            bass.draw_title(c, T, (540.0, 960.0), PAPER, anim="split" if split > 0 else None, u=split,
                            strips=6, angle=0.0, dist=1100.0, irregular=0.5, ease="linear", seed=5)
        else:
            for i in range(8):
                polys = _letter_world(i, t)
                if morph > 0:
                    outer = bass.morph_outline(_outer_world(polys), rect_pts(_letter_window(i)), morph, n=120)
                    holes = [_shrink(p, 1.0 - clamp(morph * 2.2)) for p in polys if p is not _outer_world(polys)]
                    bass.fill_polys(c, [bass.orient(outer, True)] + [bass.orient(h, False) for h in holes if h], PAPER)
                else:
                    bass.fill_polys(c, polys, PAPER, evenodd=True)
    else:
        draw_windows(c, t)
    # the red cut between the halves; it is gone as soon as they part
    if T_TITLE_CUT <= t < T_PART + 0.2:
        u = k(t, T_TITLE_CUT, 0.12, "out3")
        tail = k(t, T_PART, 0.15, "in3")
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


def her_light_off(t):
    return t >= T_PULL + 0.04


def window_color(r, t):
    """The letters' paper goes dark, window by window (each one snaps off like a light),
    except hers and his, which snap to AMBER. Hers goes out when she pulls the cord."""
    if r == HER_WIN:
        if her_light_off(t):
            return INK
        return AMBER if t >= T_DARK + 0.1 else PAPER
    if r == HIS_WIN and his_on(t):
        return AMBER if t >= T_DARK + 0.35 else PAPER
    i = (LEFT_WIN + RIGHT_WIN).index(r)
    return UNLIT if t >= T_DARK + 0.06 * ((i * 5) % 8) else PAPER


def draw_street(c, t):
    fill(c, PAPER)
    for j, B in enumerate((LEFT_B, RIGHT_B)):
        bass.fill_polys(c, [bass.cut_rect(*B, seed=20 + j)], INK)
    return draw_windows(c, t)


def red_arm_out(t):
    return T_GROW - 0.08 <= t < T_RETRACT + 0.12


def draw_windows(c, t):
    """The lit windows and the figures in them. Returns device-space anchors: his shoulder,
    for the red arm; her near hand, for the light cord."""
    anchors = {}
    for r in LEFT_WIN + RIGHT_WIN:
        bass.fill_polys(c, [bass.cut_rect(*r, seed=int(r[0] + r[1]))], window_color(r, t))
    if T_WIN - 0.6 <= t and not her_light_off(t):
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
    o = draw_cutout(c, win_fig(0), st, p, INK, facing=1, edge=AMBER, outline=AMBER, ow=10.0)
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
    place(c, HIS_WIN[0] + 92.0 + 260.0 * k(t, T_RETRACT + 0.12, T_GONE - T_RETRACT - 0.14, "in3"), HIS_WIN[3] + 6.0, WIN_FS)
    o = draw_cutout(c, win_fig(1), st, p, INK, facing=-1, edge=AMBER, hide=("near",) if red_arm_out(t) else (),
                    outline=AMBER, ow=10.0)
    sh = c.user_to_device(*o["shoulder_near"])
    c.restore()
    return sh


def draw_room_small(c, t):
    man, vic = win_fig(1), win_fig(2)
    c.save()
    place(c, HIS_WIN[0] + 24.0, HIS_WIN[3] + 6.0, WIN_FS)
    st, p = man_pose(t)
    draw_cutout(c, man, st, p, INK, facing=1, edge=AMBER, outline=AMBER, ow=10.0)
    c.restore()
    c.save()
    place(c, HIS_WIN[0] + 24.0 + 300.0 * WIN_FS, HIS_WIN[3] + 6.0, WIN_FS)
    st, p = vic_pose(t)
    draw_cutout(c, vic, st, p, INK, facing=-1, edge=AMBER, outline=AMBER, ow=10.0)
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


def draw_eye(c, t, open_, look, iris_rgb, reflect=None, mirror=False, pupil=1.0, skin=PAPER):
    """A Bass eye: an ink band across the face (`skin` above and below), an almond cut out of
    it, the iris an ink (or red) disc; `reflect(c, rect)` draws what the eye sees, into a small
    window in the iris."""
    fill(c, skin)
    band = bass.cut_rect(-40.0, EYE_C[1] - 330.0, W + 40.0, EYE_C[1] + 330.0, seed=31, amp=3.0)
    lid = almond(EYE_C, 860.0, 420.0, max(open_, 0.0))
    bass.fill_polys(c, [band], INK)
    if open_ <= 0.02:
        return
    # everything inside the eye is drawn into one layer and laid in through the lid once, so
    # no edge is composited twice (a hairline the dive would magnify)
    c.push_group()
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
    inside = c.pop_group()
    c.save()
    c.new_path()
    bass.draw.poly(c, lid)
    c.clip()
    c.set_source(inside)
    c.paint()
    c.restore()


def reflect_room(t):
    def fn(c, r):
        # the room drawn whole into its own layer, laid into the iris once; the window is a
        # hair bigger than the frame it dives into, so no edge of it is left on screen
        c.push_group()
        s = (r[2] - r[0]) / W
        c.translate(r[0], r[1])
        c.scale(s, s)
        draw_room(c, t)
        room = c.pop_group()
        c.save()
        clip_rect(c, (r[0] - 0.6, r[1] - 0.6, r[2] + 0.6, r[3] + 0.6))
        c.set_source(room)
        c.paint()
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
    steps = [(T_ROOM, 1.0), (12.0, 1.15), (12.5, 1.3), (13.0, 1.45), (13.5, 1.6), (T_RAISE, 1.25)]
    z = steps[0][1]
    for (t0, v0), (t1, v1) in zip(steps, steps[1:]):
        z = lerp(z, v1, k(t, t1, 0.07, "out5"))
    return z


def vic_burst(t):
    """She comes apart: after the third cut every piece flies loose and falls out of frame."""
    t0 = T_SLASH[2] + 0.02
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


def draw_room(c, t, zoom_cam=True, parts="all"):
    """His room: the wall, her, him, the floor and the shouting between them. parts 'torn' is
    what the knife cuts (the wall and her); 'whole' is what stays whole over the tear (him,
    and the floor her pieces fall behind)."""
    torn, whole = parts in ("all", "torn"), parts in ("all", "whole")
    if torn:
        fill(c, AMBER)
    man, vic = figs()[1], figs()[2]
    c.save()
    if zoom_cam:
        z = room_zoom(t)
        c.translate(540.0, 1150.0)
        c.scale(z, z)
        c.translate(-540.0, -1150.0)
    gap = 8.0 + 6.0 * k(t, 12.0, 2.0)
    mouth = {}
    if torn:
        c.save()
        place(c, VIC_X, ROOM_FLOOR, ROOM_FS)
        st, p = vic_pose(t)
        m = draw_cutout(c, vic, st, p, INK, facing=-1, gap=gap, burst=vic_burst(t), edge=AMBER, outline=AMBER)["mouth"]
        mouth["vic"] = (VIC_X + m[0] * ROOM_FS, ROOM_FLOOR + m[1] * ROOM_FS)
        c.restore()
    if whole:
        c.save()
        place(c, MAN_X, ROOM_FLOOR, ROOM_FS)
        st, p = man_pose(t)
        m = draw_cutout(c, man, st, p, INK, facing=1, gap=gap, edge=AMBER, outline=AMBER)["mouth"]
        mouth["man"] = (MAN_X + m[0] * ROOM_FS, ROOM_FLOOR + m[1] * ROOM_FS)
        c.restore()
        bass.fill_polys(c, [bass.cut_rect(-400.0, ROOM_FLOOR, W + 400.0, H + 800.0, seed=51, amp=2.0)], INK)
    # the shouting: from one mouth into the other's face
    if len(mouth) == 2:
        for j, tb in enumerate(BOLTS):
            if tb < T_EYE - 0.3 or tb > T_RAISE:
                continue
            a, b = (mouth["man"], mouth["vic"]) if j % 2 == 0 else (mouth["vic"], mouth["man"])
            d = math.dist(a, b) or 1.0
            e = ((b[0] - a[0]) / d, (b[1] - a[1]) / d)
            bolt(c, (a[0] + e[0] * 14.0, a[1] + e[1] * 14.0), (b[0] - e[0] * 30.0, b[1] - e[1] * 30.0 - 8.0), t, tb,
                 dur=0.38, width=20.0, seed=10 + j, amp=26.0, n=5)
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


# the three cuts, each through her (frame px at the knife shot's zoom)
CUTS = ((T_SLASH[0], (720.0, 1000.0), 62.0), (T_SLASH[1], (740.0, 1080.0), -48.0), (T_SLASH[2], (730.0, 880.0), 12.0))


def draw_knife_shot(c, t):
    """Each stab tears the picture of her (and her wall) open on red; he stands whole in front
    of the tear, on a floor her pieces fall behind."""
    c.push_group()
    draw_room(c, t, parts="torn")
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
    draw_room(c, t, parts="whole")
    # his light goes out: bars close the frame
    if t >= T_BARS:
        bass.bars(c, k(t, T_BARS, 0.5, "linear"), n=9, axis="h", colors=(INK,), frm="alt", mode="slide",
                  overlap=0.6, seed=8, bleed=3.0)


# ----------------------------------------------------------------------------- her close-ups: the sip, the mug
# her face in profile, enormous, cut from one sheet: brow, nose, lips, chin. The hair is its
# own piece laid over it (a Louise Brooks bob: blunt fringe, the sides swept forward to a
# point on the cheek), with a hairline of window light between them. Her close-ups are on
# AMBER: we are inside her lit window.
PROFILE = bass.scissor([
    (300, 1960), (300, 1120), (262, 1010), (236, 880), (232, 720), (262, 560), (330, 450), (430, 392),
    (530, 392), (604, 440), (640, 520), (652, 600), (640, 650), (650, 690), (700, 780), (742, 838),
    (730, 858), (684, 866), (690, 890), (708, 914), (690, 934), (668, 940), (690, 962), (684, 990),
    (650, 1010), (668, 1040), (660, 1090), (610, 1120), (566, 1130), (560, 1250), (640, 1340),
    (900, 1460), (1200, 1542), (1200, 1960)], seed=301, sag=0.8, amp=1.2, max_len=60.0, corner=36.0)
BOB = bass.scissor([
    (232, 1034), (198, 900), (190, 760), (204, 620), (248, 505), (328, 420), (440, 362), (548, 358),
    (626, 398), (666, 468), (678, 548), (664, 566), (560, 566), (494, 574), (462, 606), (450, 700),
    (460, 820), (498, 930), (552, 1008), (470, 1014), (380, 1030), (300, 1042)],
    seed=302, sag=0.8, amp=1.2, max_len=60.0, corner=36.0)
EYE_P = (590.0, 640.0)
LIP = (684.0, 948.0)             # where the mug's rim meets her lower lip
CU_S = 7.0                       # the close-ups: the mug at this scale (mug units -> px)
CU_DX = -110.0                   # the close-ups sit left of centre: room at her lips for the mug in her fist
MUG_HC = (968.0, 1250.0)         # the handle, in her fist: the mug held under her chin, handle out
SIP_TILT = 32.0                  # deg the mug tips toward her lips as she drinks
# her near arm: the shoulder, inside her (the upper arm is never drawn over her), and the elbow
SHOULDER = (520.0, 1500.0)
E_HOLD = (905.0, 2010.0)         # holding the mug under her chin: the elbow below the frame
E_SIP = (870.0, 1640.0)          # drinking: the elbow comes up and forward, into the frame
E_MOUTH = (905.0, 1640.0)        # her hand over her mouth: the elbow down at her chest
A_OPEN = -88.0                   # her hand sprung open off the handle: fingers up
A_MOUTH = -160.0                 # her hand over her mouth: fingers across her cheek, toward her ear
W_MOUTH = (770.0, 994.0)         # ... and her wrist, in front of her chin
MUG_G = 14000.0                  # px/s^2: the mug drops out of the frame well before it lands
T_SIP = (5.6, 7.0)               # the insert: her sip, between the windows


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


def cu_mug_at(hc, tilt, p):
    """Mug units -> frame px for the close-up mug: handle (her fist) at hc, the body toward
    her face, tipped `tilt` deg rim-first toward her."""
    return _xf([(-p[0] * CU_S, p[1] * CU_S)], hc, -tilt)[0]


def cu_mug(c, hc, tilt, rot=0.0):
    """Draw the close-up mug; returns its rim centre."""
    c.save()
    c.translate(*hc)
    c.rotate(math.radians(rot - tilt))
    c.scale(-CU_S, CU_S)
    mug_shape(c, INK, edge=AMBER, edge_w=1.4)
    rim = c.user_to_device(*_MUG_RIM)
    c.restore()
    return c.device_to_user(*rim)


def sip_hc(tilt):
    """Where her fist must be for the rim to meet her lower lip at this tilt."""
    q = cu_mug_at((0.0, 0.0), tilt, (_MUG_BODY[1][0], _MUG_BODY[1][1]))
    return (LIP[0] - q[0], LIP[1] - q[1])


def draw_arm(c, wr, el, hand):
    """Her near forearm, wrist to elbow, swelling toward the elbow, with her hand, edged in
    window light over her; then the upper arm from the elbow into her shoulder, unedged, so
    the arm runs into her where it joins her."""
    edged(c, [_capsule(wr, el, 42.0, 70.0)] + hand, INK, AMBER, 10.0)
    bass.fill_polys(c, [_capsule(el, SHOULDER, 67.0, 90.0)], INK)


# her fist round the handle, in mug units mirrored as on screen (x away from the mug, y down):
# the fingers curled round the handle, their knuckles to the outside (y, radius, x of the
# knuckle), over a block that hides the handle in her grip; the hole of the handle shows
# between her fist and the mug. Her thumb lies along the top of the handle; her wrist below.
_GRIP_FINGERS = ((-13.3, 3.6, 17.0), (-6.3, 3.6, 17.6), (0.7, 3.6, 17.0), (7.4, 3.3, 15.4))
_GRIP_BLOCK = [(-0.5, -14.5), (1.5, -16.8), (8.0, -17.0), (12.0, -15.0), (12.0, 10.4), (4.0, 10.6),
               (0.5, 8.5), (-0.5, 5.0)]
_GRIP_WRIST = (8.0, 12.0)
_GRIP_THUMB = ((12.5, -16.0), (-1.5, -19.6), 3.4, 2.7)


def _grip_pts(hc, tilt, pts):
    return _xf([(x * CU_S, y * CU_S) for x, y in pts], hc, -tilt)


def cu_grip(hc, tilt):
    """Her fist round the mug's handle at hc, tipped with the mug. Returns (polys, the cuts
    between her fingers and under her thumb, her wrist)."""
    polys = [bass.orient(_grip_pts(hc, tilt, _GRIP_BLOCK), True)]
    for y, r, x1 in _GRIP_FINGERS:
        a, b = _grip_pts(hc, tilt, [(3.0, y), (x1 - r, y)])
        polys.append(_capsule(a, b, r * CU_S, r * CU_S))
    a, b, ra, rb = _GRIP_THUMB
    a, b = _grip_pts(hc, tilt, [a, b])
    polys.append(_capsule(a, b, ra * CU_S, rb * CU_S))
    cuts = []
    for (y0, r0, x0), (y1, r1, x1) in zip(_GRIP_FINGERS, _GRIP_FINGERS[1:]):
        ym = (y0 + r0 + y1 - r1) / 2.0
        cuts.append(_grip_pts(hc, tilt, [(min(x0, x1) - 1.0, ym), (min(x0, x1) - 6.5, ym)]))
    cuts.append(_grip_pts(hc, tilt, [(13.4, -16.9), (5.0, -17.2)]))         # the thumb off her fist
    return polys, cuts, _grip_pts(hc, tilt, [_GRIP_WRIST])[0]


def cut_lines(c, lines, width=6.0):
    """The cuts between her fingers: lines of window light through the ink."""
    c.save()
    c.set_source_rgb(*AMBER)
    c.set_line_width(width)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ln in lines:
        c.new_path()
        bass.draw.poly(c, ln, close=False)
        c.stroke()
    c.restore()


def draw_grip(c, hc, tilt, el):
    """The mug in her fist, her arm down to the elbow at el. Returns the rim."""
    rim = cu_mug(c, hc, tilt)
    polys, cuts, wr = cu_grip(hc, tilt)
    draw_arm(c, wr, el, polys)
    cut_lines(c, cuts)
    return rim


def draw_her_profile(c, wide=1.0, lid=1.0, look=0.0):
    """Her face: the profile, the bob, the eye (wide on the gasp, lowered as she drinks)."""
    fill(c, AMBER)
    bass.fill_polys(c, [bass.orient(PROFILE, True)], INK)
    edged(c, [bass.orient(BOB, True)], INK, AMBER, 9.0)
    c0 = (EYE_P[0], EYE_P[1] - 10.0 * (wide - 1.0))
    eye = almond(c0, 84.0, 40.0 * wide, lid)
    bass.fill_polys(c, [eye], PAPER)
    c.save()
    c.new_path()
    bass.draw.poly(c, eye)
    c.clip()
    bass.disc(c, (EYE_P[0] + 20.0 + 8.0 * look, EYE_P[1] - 4.0 + 6.0 * (1.0 - lid)), 11.0 * (2.0 - wide * 0.6), INK, seed=312)
    c.restore()
    # lashes: two flicks off the front of the upper lid, out past the line of her face
    top = eye[: len(eye) // 2 + 1]
    for f, L, a in ((0.86, 54.0, -36.0), (0.94, 52.0, -17.0)):
        b = top[int(f * (len(top) - 1))]
        tip = (b[0] + math.cos(math.radians(a)) * L, b[1] + math.sin(math.radians(a)) * L)
        bass.fill_polys(c, [bass.orient([(b[0] - 8.0, b[1] + 3.0), (b[0] + 8.0, b[1] + 2.0), tip], True)], INK)


def steam_cu(c, rim, t, alpha=1.0):
    steam(c, rim, twos(t), INK, alpha=alpha, scale=CU_S * 0.8)


# --- the sip
def sip_state(t):
    """(handle, elbow, tilt) of her sip: the mug under her chin, up to her lips and tipped,
    held there, and back down."""
    up = k(t, 5.86, 0.36, "inout") * (1.0 - k(t, 6.62, 0.32, "inout"))
    tilt = SIP_TILT * up
    hc = lerp(MUG_HC, sip_hc(SIP_TILT), up)
    return hc, lerp(E_HOLD, E_SIP, up), tilt


def draw_sip_shot(c, t):
    hc, el, tilt = sip_state(t)
    drink = k(t, 6.12, 0.12, "out") * (1.0 - k(t, 6.66, 0.16, "out"))
    c.save()
    c.translate(CU_DX, 0.0)
    draw_her_profile(c, lid=lerp(1.0, 0.38, drink), look=-0.5 * drink)
    rim = draw_grip(c, hc, tilt, el)
    steam_cu(c, rim, t, alpha=1.0 - clamp(tilt / 12.0))
    c.restore()


# --- the mug: she hears it, drops it, her hand goes to her mouth
# her open hand, its back to us (it is her left): px. The palm (wrist to knuckles, width at the
# knuckles, wrist); the fingers, index first (across the knuckles / palm width, length, radius
# at the knuckle and at the tip, deg fanned out when spread); the thumb (along the palm / its
# length, across / its width, length, radii, deg out from the hand closed and open)
_PALM = (170.0, 168.0, 104.0)
_FINGERS = ((0.375, 148.0, 21.5, 17.0, 22.0), (0.125, 166.0, 22.0, 18.0, 7.0),
            (-0.125, 156.0, 21.5, 17.5, -8.0), (-0.375, 124.0, 19.0, 15.5, -24.0))
_THUMB = (0.3, 0.44, 124.0, 25.0, 19.0, 34.0, 40.0)


def cu_hand(wr, ang, spread):
    """Her open hand at wrist `wr`, pointing `ang` deg, the thumb on its clockwise side; fingers
    fanned by `spread` (0 = together, over her mouth; 1 = sprung open). Returns (polys, the cuts
    between her fingers)."""
    a = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    n = (-a[1], a[0])
    L, Wp, Ww = _PALM

    def P(s, q):
        return (wr[0] + a[0] * s + n[0] * q, wr[1] + a[1] * s + n[1] * q)

    def ray(p, deg, length):
        return (p[0] + math.cos(math.radians(ang + deg)) * length, p[1] + math.sin(math.radians(ang + deg)) * length)

    palm = [P(0.0, -Ww / 2), P(0.45 * L, -Wp * 0.51), P(L, -Wp * 0.49), P(L + 10.0, -Wp * 0.2),
            P(L + 10.0, Wp * 0.2), P(L, Wp * 0.5), P(0.5 * L, Wp * 0.52), P(0.0, Ww / 2)]
    polys = [bass.orient(palm, True)]
    tips = []
    for qf, Lf, rb, rt, sp in _FINGERS:
        base = P(L - rb * 0.7, qf * Wp)
        deg = sp * spread + 4.0 * qf
        polys.append(_capsule(base, ray(base, deg, Lf), rb, rt))
        tips.append((base, deg, Lf))
    sf, qf, Lt, rb, rt, d0, d1 = _THUMB
    base = P(sf * L, qf * Wp)
    polys.append(_capsule(base, ray(base, lerp(d0, d1, spread), Lt), rb, rt))
    cuts = []
    if spread < 0.05:
        for (b0, g0, L0), (b1, g1, L1) in zip(tips, tips[1:]):
            m = ((b0[0] + b1[0]) / 2.0, (b0[1] + b1[1]) / 2.0)
            g, Lc = (g0 + g1) / 2.0, min(L0, L1)
            cuts.append([ray(m, g, 0.2 * Lc), ray(m, g, Lc - 24.0)])
    return polys, cuts


def mug_hand_at(t):
    """Where her fist holds the mug: it jumps on the gasp and trembles (on twos) until she
    lets go."""
    jump = 44.0 * (k(t, T_GASP, 0.07, "out") - k(t, T_GASP + 0.12, 0.35, "inout"))
    shake = 4.0 * math.sin(twos(t) * 61.0) * k(t, T_GASP, 0.05)
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
    """Her near hand and its forearm, up from out of the frame: her fist on the mug, sprung open
    as she lets it go (fingers up), then turned over onto her mouth. Returns the rim while she
    holds it."""
    if t < T_DROP:
        hc = mug_hand_at(t)
        return draw_grip(c, hc, 0.0, (E_HOLD[0] + hc[0] - MUG_HC[0], E_HOLD[1] + hc[1] - MUG_HC[1]))
    pop = k(t, T_DROP, 0.05, "outback")
    swing = k(t, T_HAND - 0.14, 0.14, "out")
    w0 = cu_grip(mug_hand_at(T_DROP), 0.0)[2]
    wr = lerp((w0[0] - 6.0, w0[1] - 16.0 * pop), W_MOUTH, swing)
    polys, cuts = cu_hand(wr, lerp(A_OPEN, A_MOUTH, swing), pop * (1.0 - swing))
    draw_arm(c, wr, lerp((E_HOLD[0] - 6.0, E_HOLD[1] - 16.0 * pop), E_MOUTH, swing), polys)
    cut_lines(c, cuts)
    return None


def draw_mug_shot(c, t):
    c.save()
    c.translate(CU_DX, 0.0)
    draw_her_profile(c, wide=1.0 + 0.7 * k(t, T_GASP, 0.1, "outback"))
    # the dropped mug, tipping forward as it falls out of the frame
    if T_DROP <= t < T_SMASH:
        (x, y), rot = mug_fall(twos(t))
        if y < H + 400.0:
            cu_mug(c, (x, y), 0.0, rot=rot)
    rim = draw_mug_hand(c, t)
    # steam: off the rim while she holds it; left hanging in the air a moment when it drops
    if rim is not None:
        steam_cu(c, rim, t)
    elif t < T_DROP + 0.15:
        r0 = cu_mug_at(mug_hand_at(T_DROP), 0.0, _MUG_RIM)
        steam(c, (r0[0], r0[1] - 20.0 * (t - T_DROP) / 0.15), twos(T_DROP), INK,
              alpha=1.0 - k(t, T_DROP, 0.15, "in"), scale=CU_S * 0.8)
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
                      AMBER if ink else INK, 5.0)
    c.restore()


# ----------------------------------------------------------------------------- his arm across the street
def arm_points(shoulder=None):
    """From his shoulder in the window to her window."""
    base = shoulder or (HIS_WIN[0] + 80.0, HIS_WIN[3] + 6.0 - 568.0 * WIN_FS)
    tip = (HER_WIN[2] - 14.0, centre(HER_WIN)[1] - 20.0)
    return base, tip


def draw_arm_shot(c, t):
    # the frame trembles while the arm is out (stepped, on twos), and tilts with its weight
    shake = 3.5 * k(t, T_GROW + 0.6, 0.1) * (1.0 - k(t, T_RETRACT, 0.12))
    tilt = -4.0 * k(t, T_GROW, 0.8, "inout3") * (1.0 - k(t, T_RETRACT + 0.1, 0.4))
    tt = twos(t)
    c.save()
    c.translate(540.0, 960.0)
    c.rotate(math.radians(tilt))
    c.translate(-540.0 + shake * math.sin(tt * 61.0), -960.0 + shake * math.cos(tt * 47.0))
    anchors = draw_street(c, t)
    grow = k(t, T_GROW, 0.7, "out3") * (1.0 - k(t, T_RETRACT, 0.12, "in3"))
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
    # in on her window from the street exactly as the last shot left it (no jump on the cut)
    p = k(t, T_OFF, 0.35, "out5")
    z = lerp(1.0, 3.3, p)
    cc = (centre(HER_WIN)[0], centre(HER_WIN)[1] - 10.0)
    c.save()
    c.translate(lerp(cc[0], 540.0, p), lerp(cc[1], 960.0, p))
    c.scale(z, z)
    c.translate(-cc[0], -cc[1])
    anchors = draw_street(c, t)
    if not her_light_off(t):
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
    lw = 16.0
    lines = []
    for x0, x1 in (LB, RB):
        top = -5 * FLOOR
        lines.append([(x0, 60.0), (x0, top), (x1, top), (x1, 60.0)])
        for f in range(1, 5):
            lines.append([(x0, -f * FLOOR), (x1, -f * FLOOR)])
    lines.append([(-600.0, 0.0), (3300.0, 0.0)])
    reveal = k(t, T_PATH, 0.35, "out3")
    for j, ln in enumerate(lines):
        bass.line_band(c, ln, lerp(DIM, PAPER, 0.3), width=lw, u=reveal, seed=80 + j)
    # the two rooms: his lit, hers dark with her in it
    bass.fill_polys(c, [bass.cut_rect(2250.0, HIS_ROOM_Y - 200.0, 2550.0, HIS_ROOM_Y - 20.0, seed=91)], AMBER)
    bass.fill_polys(c, [bass.cut_rect(80.0, HER_ROOM_Y - 200.0, 260.0, HER_ROOM_Y - 20.0, seed=92)], lerp(UNLIT, AMBER, 0.32))
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
DOOR = (250.0, 262.0, 830.0, BAR_Y)
HALL_STEPS = (T_DOOR + 0.4, T_DOOR + 0.95, T_DOOR + 1.45)     # his steps along her hall, heard not seen
SHADOW_LEAD = (DOOR[2] + 60.0, 760.0, 690.0, 610.0, 470.0)     # where his shadow reaches, step by step
SHADOW_TONE = (0.0, 0.3, 0.45, 0.58, 0.66)
FEET_X = (410.0, 600.0)
KNOB = (745.0, 840.0)
KEYHOLE = (745.0, 960.0)
SPILL = ((0.36, 70.0), (0.22, 150.0), (0.11, 250.0))          # the light under the door on her floor: (tone, depth)
T_FACE = 32.0              # his face comes to the keyhole: the light in it is cut across


def keyhole_pts(c0, s=1.0):
    # fine facets: the push into the keyhole magnifies them 15-20x (a cut's worth, not a polygon)
    circ = bass.draw.circle_pts((c0[0], c0[1] - 18.0 * s), 22.0 * s, n=64)
    leg = [(c0[0] - 13.0 * s, c0[1]), (c0[0] + 13.0 * s, c0[1]), (c0[0] + 20.0 * s, c0[1] + 62.0 * s),
           (c0[0] - 20.0 * s, c0[1] + 62.0 * s)]
    return bass.orient(circ, True), bass.orient(leg, True)


def _spill_x(x, depth):
    """Light through the gap under the door fans out a little as it comes across the floor."""
    return 540.0 + (x - 540.0) * (1.0 + 0.5 * depth / 250.0)


def _floor_band(x0, x1, d0, d1):
    y0, y1 = BAR_Y + 26.0 + d0, BAR_Y + 26.0 + d1
    return bass.orient([(_spill_x(x0, d0), y0), (_spill_x(x1, d0), y0), (_spill_x(x1, d1), y1), (_spill_x(x0, d1), y1)], True)


def draw_light(c, x0, x1, dark=0.0):
    """The bar of light under the door between x0 and x1, and its spill on her floor, darkened
    by `dark` (0..1)."""
    bass.fill_polys(c, [bass.cut_rect(x0, BAR_Y, x1, BAR_Y + 26.0, seed=102, amp=0.8)], lerp(AMBER, INK, dark))
    d0 = 0.0
    for tone, d1 in SPILL:
        bass.fill_polys(c, [_floor_band(x0, x1, d0, d1)], lerp(lerp(INK, AMBER, tone), INK, dark))
        d0 = d1


def draw_door(c, t):
    fill(c, INK)
    # her door in the dark: a dark grey slab in its frame, two panels
    bass.fill_polys(c, [bass.cut_rect(DOOR[0] - 26.0, DOOR[1] - 26.0, DOOR[2] + 26.0, BAR_Y, seed=100, amp=1.2)],
                    (0.075, 0.07, 0.064))
    bass.fill_polys(c, [bass.cut_rect(*DOOR, seed=101, amp=1.2)], (0.13, 0.122, 0.112))
    for j, (y0, y1) in enumerate(((320.0, 760.0), (880.0, 1240.0))):
        bass.fill_polys(c, [bass.cut_rect(DOOR[0] + 56.0, y0, DOOR[2] - 56.0, y1, seed=106 + j, amp=1.0)],
                        (0.105, 0.098, 0.09))
    # the light under it, and on her floor
    draw_light(c, DOOR[0], DOOR[2])
    # his shadow comes along the hall ahead of him: a step at a time it takes more of the light
    n = sum(k(t, ts, 0.08, "out") for ts in HALL_STEPS) + k(t, T_FEET - 0.08, 0.16, "out3")
    if n > 0.0:
        i = min(int(n), 3)
        f = n - i
        lead = lerp(SHADOW_LEAD[i], SHADOW_LEAD[min(i + 1, 4)], f)
        if lead < DOOR[2]:
            draw_light(c, lead, DOOR[2], lerp(SHADOW_TONE[i], SHADOW_TONE[min(i + 1, 4)], f))
    # his feet cut into it, and their shadows run out across her floor
    fu = k(t, T_FEET - 0.08, 0.16, "out3")
    if fu > 0:
        for j, x in enumerate(FEET_X):
            xx = lerp(1200.0 + 190.0 * j, x, fu)
            if xx < DOOR[2]:
                x1 = min(xx + 140.0, DOOR[2])
                bass.fill_polys(c, [bass.cut_rect(xx, BAR_Y - 6.0, x1, BAR_Y + 30.0, seed=103 + j, amp=1.0),
                                    _floor_band(xx, x1, 0.0, SPILL[-1][1])], INK)
    # the handle: tried twice (jerky, on twos)
    tt = twos(t)
    turn = 0.0
    for t0 in T_KNOB:
        turn += -38.0 * (k(tt, t0, 0.12, "out3") - k(tt, t0 + 0.32, 0.12, "in3"))
    turn += 2.5 * math.sin(tt * 70.0) * (k(tt, T_KNOB[0], 0.05) - k(tt, T_KNOB[1] + 0.5, 0.05))
    # (finely cut, like the keyhole: the push into the keyhole passes 15x over them)
    bass.fill_polys(c, [bass.ring_pts(KNOB, 44.0, seed=104, n=96, amp=0.1)], DIM)
    c.save()
    c.translate(*KNOB)
    c.rotate(math.radians(turn))
    bass.fill_polys(c, [bass.capsule_pts((0.0, 0.0), (-190.0, 0.0), 22.0, 19.0, 12)], DIM)
    c.restore()
    # the keyhole: the hall's light comes through it
    bass.fill_polys(c, list(keyhole_pts(KEYHOLE)), AMBER)


def draw_door_shot(c, t):
    draw_door(c, t)


# ----------------------------------------------------------------------------- the keyhole, his eye
def key_zoom(t):
    """(zoom, centring) of the push into the keyhole: in until it fills most of the frame, a
    hold while his eye comes to it and opens, then on through it."""
    p = k(t, T_KEY + 0.05, 0.45, "inout")
    z = math.exp(math.log(15.0) * p + math.log(4.2) * k(t, T_OPEN + 0.25, 0.3, "in3"))
    return z, p


def draw_his_eye(c, t):
    """His eye, the mirror of hers: lit by the hall (amber), the iris red. The band of his face
    slides into the keyhole from the side as he puts his eye to it; shut until he opens it."""
    c.save()
    c.translate(lerp(1150.0, 0.0, k(t, T_FACE, 0.14, "out3")), 0.0)
    open_ = k(t, T_OPEN, 0.1, "outback")
    look = 0.04 * math.sin(5.0 * t) * k(t, T_OPEN + 0.4, 0.3)
    pupil = 1.0 - 0.45 * k(t, T_OPEN + 0.55, 0.12, "outback")
    draw_eye(c, t, open_, look, RED, mirror=True, pupil=pupil, skin=AMBER)
    c.restore()


def draw_key_shot(c, t):
    z, p = key_zoom(t)
    kc = (KEYHOLE[0], KEYHOLE[1] - 18.0)               # the keyhole's round, slid to the eye's place
    c.save()
    c.translate(lerp(kc[0], EYE_C[0], p), lerp(kc[1], EYE_C[1] - 6.0, p))
    c.scale(z, z)
    c.translate(-kc[0], -kc[1])
    draw_door(c, t)
    c.new_path()
    for poly in keyhole_pts(KEYHOLE):
        bass.draw.poly(c, poly)
    c.restore()
    # through the keyhole (the path survives the restore): the light of the hall, and him
    c.save()
    c.clip()
    draw_his_eye(c, t)
    c.restore()


# ----------------------------------------------------------------------------- end card
def draw_end(c, t):
    fill(c, INK)
    T = title()
    s_ = lerp(1.6, 1.0, k(t, T_END, 0.1, "out3"))
    p0, p1 = (60.0, 1110.0), (1020.0, 682.0)
    if t < T_END_SLASH + 0.1:
        bass.draw_title(c, T, (540.0, 960.0), PAPER, scale=s_)
    else:
        # cut along the slash's own line: the halves slide apart along it, under the red
        d = _unit((p1[0] - p0[0], p1[1] - p0[1]))
        n = (-d[1], d[0])
        apart = 40.0 * k(t, T_END_SLASH + 0.1, 0.5, "out5")
        for sg in (-1.0, 1.0):
            c.save()
            c.new_path()
            bass.draw.poly(c, [(p0[0] - d[0] * 3000.0, p0[1] - d[1] * 3000.0), (p0[0] + d[0] * 3000.0, p0[1] + d[1] * 3000.0),
                               (p0[0] + d[0] * 3000.0 + n[0] * 3000.0 * sg, p0[1] + d[1] * 3000.0 + n[1] * 3000.0 * sg),
                               (p0[0] - d[0] * 3000.0 + n[0] * 3000.0 * sg, p0[1] - d[1] * 3000.0 + n[1] * 3000.0 * sg)])
            c.clip()
            c.translate(d[0] * apart * sg, d[1] * apart * sg)
            bass.draw_title(c, T, (540.0, 960.0), PAPER, scale=s_)
            c.restore()
    if t >= T_END_SLASH:
        bass.slash(c, p0, p1, RED, width=40.0, u=k(t, T_END_SLASH, 0.1, "out3"), seed=12)


# ----------------------------------------------------------------------------- the film
SHOTS = [
    (0.0, draw_title_shot),
    (T_WIN, draw_windows_shot),
    (T_SIP[0], draw_sip_shot),
    (T_SIP[1], draw_windows_shot),
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
