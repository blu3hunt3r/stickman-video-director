"""SHADOW PLAY s11 / s12 helpers (owner: the s11-s12 animator).

THE FORTY DOLLS (s11). His wall of paper dolls, one for every window of the facade across
the street (cells 1..40 row-major, the facade numbering). Each doll is a single piece of
PAPER cut with scissors from the figure rig + props, pinned through the head:

    1 newspaper man     2 umbrella woman    3 old man, cane      4 THE DANCER        5 violinist
    6 girl, balloon     7 handbag, scarf    8 man, suitcase      9 HER (RED, binoc.) 10 man + dog
   11 mother + baby    12 THE CAT LADY     13 pram              14 the bowler man   15 boy, kite
   16 waiter, tray     17 broom            18 fat man, cigar    19 skipping rope    20 painter, easel
   21 brushing hair    22 boxer            23 shopping bags     24 telephone        25 fan, opera
   26 strongman        27 child + teddy    28 fisherman + fish  29 birdcage         30 THE CRIER
   31 trumpet          32 hand mirror      33 ladder            34 paper-doll chain 35 sailor, duffel
   36 wheelchair       37 hatbox           38 scooter           39 watering can     40 sleepwalker

Doll 9 sits where window 9 is (the killer's own window) and it is HER: front view, a RED
paper trench coat, ink paper binoculars raised to the eyes, the pin through the bridge.

    shapes = dolls()                  # cached; {i: Doll}
    d = shapes[i]
    d.draw(ctx, pin, k, angle)       # world pin point, scale (world px per ref px), deg
    d.path_paper / path_red / path_ink: cairo Paths in REF px around the pin (head centre)

Built once per process (~1 s): each figure is rasterized at REF scale (an adult is ~600 px),
traced with holes (cv2 RETR_CCOMP), simplified and re-cut with bass.scissor.
"""
import math
from functools import lru_cache

import cairo
import cv2
import numpy as np

from engine import bass, draw
from engine import figure as FG
from engine.core import clamp, hash01, lerp
from engine.figure import Body, Look, Pose
from engine.frame import surf_array
from engine.palette import PAPER, RED, SHADOWPLAY

INK = SHADOWPLAY.ink
WHITE = (1.0, 1.0, 1.0)
CRED = (1.0, 0.0, 0.0)          # class colours in the build raster
CINK = (0.0, 0.0, 1.0)

RS = 1200                        # build raster size
PIN = (600.0, 430.0)             # where the head centre lands in the build raster
DISPLAY_H = 108.0                # world px of a 600 px reference figure on the wall
K_DOLL = DISPLAY_H / 600.0


# ============================================================================ geometry helpers
def _add(a, d, k=1.0):
    return (a[0] + d[0] * k, a[1] + d[1] * k)


def _lerp2(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def _dirv(deg):
    r = math.radians(deg)
    return (math.cos(r), math.sin(r))


def _xf(pts, at, ang=0.0, s=1.0, flip=1.0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(at[0] + (x * flip * ca - y * sa) * s, at[1] + (x * flip * sa + y * ca) * s) for x, y in pts]


class _Pen:
    """Filled shapes on the build raster in one class colour."""

    def __init__(self, c, col=WHITE):
        self.c = c
        self.col = col

    def _f(self):
        self.c.set_source_rgb(*self.col)
        self.c.set_fill_rule(cairo.FILL_RULE_WINDING)
        self.c.fill()

    def cap(self, a, b, r, r2=None):
        draw.capsule(self.c, a, b, r, r if r2 is None else r2)
        self._f()

    def line(self, a, b, w):
        self.cap(a, b, w * 0.5)

    def poly(self, pts):
        draw.poly(self.c, pts)
        self._f()

    def smooth(self, pts, tension=0.5):
        draw.smooth(self.c, pts, close=True, tension=tension)
        self._f()

    def circ(self, p, r):
        draw.circle(self.c, p, r)
        self._f()

    def ell(self, p, rx, ry, ang=0.0):
        draw.ellipse(self.c, p, rx, ry, ang)
        self._f()

    def ring(self, p, ro, ri, a0=0.0, a1=360.0):
        c = self.c
        c.new_sub_path()
        if a1 - a0 >= 359.9:
            c.arc(p[0], p[1], ro, 0, 2 * math.pi)
            c.close_path()
            c.new_sub_path()
            c.arc_negative(p[0], p[1], ri, 2 * math.pi, 0)
            c.close_path()
        else:
            r0, r1 = math.radians(a0), math.radians(a1)
            c.arc(p[0], p[1], ro, r0, r1)
            c.arc_negative(p[0], p[1], ri, r1, r0)
            c.close_path()
        self._f()

    def wheel(self, p, r, rim, spokes=6, hub=None, rot=0.0):
        self.ring(p, r, r - rim)
        self.circ(p, hub or rim * 1.4)
        for k in range(spokes):
            a = math.radians(rot + 360.0 * k / spokes)
            self.line(p, (p[0] + math.cos(a) * (r - rim * 0.5), p[1] + math.sin(a) * (r - rim * 0.5)), rim * 0.45)

    def path_line(self, pts, w, w2=None):
        """A strip along a polyline (constant or tapering width)."""
        n = len(pts)
        ws = [lerp(w, w if w2 is None else w2, i / max(n - 1, 1)) for i in range(n)]
        draw.poly(self.c, draw.ribbon(pts, ws))
        self._f()
        for p, ww in zip(pts, ws):
            draw.circle(self.c, p, ww * 0.5)
            self._f()


def _curve(p0, p1, p2, n=16):
    """Quadratic bezier points."""
    out = []
    for i in range(n + 1):
        u = i / n
        a = _lerp2(p0, p1, u)
        b = _lerp2(p1, p2, u)
        out.append(_lerp2(a, b, u))
    return out


# ============================================================================ pose helper
def _pose(yaw=0.0, pitch=0.0, spine=(0.0, 0.0, 0.0), neck=0.0, head=0.0, head_yaw=0.0, head_roll=0.0,
          L=None, R=None, lL=None, lR=None):
    p = Pose(0.0, 0.0, yaw)
    p.pitch = pitch
    p.spine = list(spine)
    p.neck, p.head, p.head_yaw, p.head_roll = neck, head, head_yaw, head_roll
    if L:
        p.arms["L"].update(L)
    if R:
        p.arms["R"].update(R)
    base = dict(hip=0.0, abd=3.0, knee=2.0, ankle=0.0, toe=0.0)
    if lL is not None:
        p.legs["L"] = dict(base, **lL)
    if lR is not None:
        p.legs["R"] = dict(base, **lR)
    p.eyes = dict(open=0.0, glow=0.0, look=0.0)
    return p


def _ground(sk):
    J = sk.j
    return max(J["heel_L"][1], J["heel_R"][1], J["ball_L"][1], J["ball_R"][1]) + 0.012 * sk.H


def _walk(front=18.0, back=-16.0, bend=24.0):
    """Stride legs (near leg forward)."""
    return dict(hip=front, knee=6.0, ankle=-4.0), dict(hip=back, knee=bend, ankle=-14.0)


def _sit(knee=88.0, hip=88.0):
    return dict(hip=hip, knee=knee, ankle=0.0), dict(hip=hip - 4.0, knee=knee + 4.0, ankle=0.0, abd=4.0)


# ============================================================================ props
def _cat_sitting(P, at, h, fac=1.0):
    """A sitting cat, `h` tall, paws at `at`, facing fac (+1 right)."""
    pts = [(0.00, 0.00), (0.10, 0.00), (0.14, -0.06), (0.13, -0.30), (0.17, -0.52), (0.22, -0.66),
           (0.20, -0.74), (0.23, -0.86), (0.21, -0.98), (0.16, -0.90), (0.10, -0.95), (0.03, -1.0),
           (0.05, -0.88), (0.0, -0.74), (0.04, -0.62), (-0.06, -0.48), (-0.20, -0.30), (-0.26, -0.12),
           (-0.22, 0.0)]
    P.smooth(_xf(pts, at, 0.0, h, fac), 0.35)
    # the tail curls along the floor round the paws
    tail = [(-0.20, -0.02), (-0.34, -0.03), (-0.44, -0.08), (-0.47, -0.17), (-0.42, -0.24)]
    P.path_line(_xf(tail, at, 0.0, h, fac), 0.07 * h, 0.05 * h)


def _dog(P, at, h, fac=1.0):
    """A small terrier standing, `h` = shoulder height, feet on at[1], chest at at[0]."""
    body = [(-0.55, -0.62), (0.05, -0.68), (0.18, -0.95), (0.30, -1.08), (0.38, -1.30), (0.33, -1.42),
            (0.40, -1.38), (0.47, -1.22), (0.62, -1.16), (0.66, -1.06), (0.50, -0.98), (0.36, -0.92),
            (0.22, -0.55), (0.10, -0.40), (-0.50, -0.40), (-0.62, -0.50)]
    P.smooth(_xf(body, at, 0.0, h, fac), 0.3)
    for x0, x1 in ((0.10, 0.14), (0.0, 0.02), (-0.45, -0.42), (-0.55, -0.58)):
        P.line(_xf([(x0, -0.45)], at, 0, h, fac)[0], _xf([(x1, 0.0)], at, 0, h, fac)[0], 0.09 * h)
    P.path_line(_xf([(-0.58, -0.58), (-0.72, -0.82), (-0.70, -1.0)], at, 0, h, fac), 0.08 * h, 0.04 * h)


def _fish(P, at, L, ang=90.0):
    pts = [(0.0, 0.0), (0.2, -0.17), (0.55, -0.16), (0.78, -0.04), (0.98, -0.2), (0.95, 0.0), (0.98, 0.2),
           (0.78, 0.04), (0.55, 0.16), (0.2, 0.17)]
    P.smooth(_xf(pts, at, ang, L), 0.25)


def _umbrella(P, top, w, h, n=6):
    """Open umbrella canopy: apex `top`, rim width w, depth h, scalloped between ribs."""
    pts = []
    for k in range(25):
        a = math.pi * (1 - k / 24.0)
        pts.append((top[0] + math.cos(a) * w * 0.5, top[1] + h - math.sin(a) * h))
    rim = []
    for k in range(n, -1, -1):
        x = top[0] - w * 0.5 + w * k / n
        rim.append((x, top[1] + h))
        if k > 0:
            xm = top[0] - w * 0.5 + w * (k - 0.5) / n
            rim.append((xm, top[1] + h * 0.80))
    P.poly(pts + rim[1:-1])
    P.line((top[0], top[1] + 0.2 * h), (top[0], top[1] - 0.25 * h), w * 0.03)


# ============================================================================ the forty specs
# each returns dict(body, look, pose, props=fn(P, sk, H, fwd, gy) | None, extra figures)
def _s1():
    b = Body.adult_m(620)
    lk = Look(hat="fedora", coat="trench")
    p = _pose(0, head=6, R=dict(sh=52, abd=8, elbow=74), L=dict(sh=48, abd=12, elbow=80),
              lL=dict(hip=4, knee=3), lR=dict(hip=-4, knee=4))

    def props(P, sk, H, fwd, gy):
        x0 = sk.j["head"][0] + 0.05 * H
        x1 = x0 + 0.20 * H
        xm = (x0 + x1) * 0.5
        y0 = sk.j["crown"][1] - 0.05 * H
        y1 = sk.j["chest"][1] + 0.06 * H
        P.poly([(x0, y0 + 0.010 * H), (xm, y0 + 0.035 * H), (x1, y0), (x1 + 0.01 * H, y1 - 0.02 * H),
                (xm, y1 + 0.012 * H), (x0 - 0.005 * H, y1)])
    return dict(body=b, look=lk, pose=p, props=props)


def _s2():
    b = Body.adult_f(590)
    lk = Look(hair="bob", coat="long", shoes="heel")
    lf, lb = _walk(16, -14, 22)
    p = _pose(180, L=dict(sh=50, abd=10, elbow=80, grip=0.9), R=dict(sh=-12, abd=8, elbow=14),
              lL=lf, lR=lb, head=-4)

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_L"]
        top = (h[0] - 0.01 * H * fwd, sk.j["crown"][1] - 0.13 * H)
        P.line((h[0], h[1] + 0.03 * H), top, 0.016 * H)
        P.path_line([(h[0], h[1] + 0.03 * H), (h[0], h[1] + 0.065 * H), (h[0] - 0.03 * H * fwd, h[1] + 0.07 * H)],
                    0.016 * H)
        _umbrella(P, top, 0.66 * H, 0.16 * H, n=6)
    return dict(body=b, look=lk, pose=p, props=props)


def _s3():
    b = Body.adult_m(600)
    lk = Look(hat="flatcap", coat="long")
    p = _pose(0, pitch=14, spine=(8, 10, 14), neck=-14, head=-12, R=dict(sh=32, abd=6, elbow=-2, grip=0.9),
              L=dict(sh=-10, abd=8, elbow=30), lL=dict(hip=10, knee=16), lR=dict(hip=-8, knee=14, ankle=-6))

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_R"]
        foot = (h[0] + 0.05 * H * fwd, gy)
        P.line(h, foot, 0.018 * H)
        P.path_line([(h[0] - 0.004 * H * fwd, h[1] + 0.01 * H), (h[0] - 0.01 * H * fwd, h[1] - 0.02 * H),
                     (h[0] - 0.045 * H * fwd, h[1] - 0.03 * H), (h[0] - 0.07 * H * fwd, h[1] - 0.005 * H)],
                    0.018 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s4():
    b = Body.adult_f(580)
    lk = Look(hair="ponytail", dress="knee")
    p = _pose(0, pitch=24, spine=(0, -6, -10), neck=-14, head=-14,
              R=dict(sh=118, abd=12, elbow=8, wrist=10), L=dict(sh=-50, abd=45, elbow=8),
              lL=dict(hip=0, knee=0, ankle=35, toe=10), lR=dict(hip=-96, knee=4, ankle=55, abd=4))
    return dict(body=b, look=lk, pose=p, props=None)


def _s5():
    b = Body.adult_m(620)
    lk = Look(hair="slick", coat="jacket")
    p = _pose(0, head=14, head_roll=-6, neck=6, L=dict(sh=74, abd=26, elbow=22, wrist=-15, grip=0.8),
              R=dict(sh=30, abd=14, elbow=58, grip=0.9), lL=dict(hip=6, knee=3), lR=dict(hip=-6, knee=5))

    def props(P, sk, H, fwd, gy):
        chin = _add(sk.j["head_base"], (0.03 * H * fwd, 0.035 * H))
        hand = sk.j["hand_L"]
        ax = (hand[0] - chin[0], hand[1] - chin[1])
        L = math.hypot(*ax)
        ang = math.degrees(math.atan2(ax[1], ax[0]))
        body = [(0.0, 0.0), (0.02, -0.22), (0.12, -0.30), (0.30, -0.28), (0.42, -0.18), (0.55, -0.20),
                (0.72, -0.27), (0.88, -0.24), (1.0, -0.10), (1.0, 0.10), (0.88, 0.24), (0.72, 0.27),
                (0.55, 0.20), (0.42, 0.18), (0.30, 0.28), (0.12, 0.30), (0.02, 0.22)]
        P.smooth(_xf(body, _add(chin, _dirv(ang), -0.02 * H), ang, 0.21 * H), 0.4)
        P.line(_add(chin, _dirv(ang), 0.18 * H), hand, 0.022 * H)
        P.circ(_add(hand, _dirv(ang), 0.02 * H), 0.018 * H)
        hb = sk.j["hand_R"]
        a2 = ang - 62.0 * fwd
        P.line(_add(hb, _dirv(a2), -0.06 * H), _add(hb, _dirv(a2), 0.30 * H), 0.010 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s6():
    b = Body.child(380)
    lk = Look(hair="bob", dress="knee")
    p = _pose(0, head=-14, R=dict(sh=66, abd=10, elbow=12, grip=0.9), L=dict(sh=-8, abd=8, elbow=12),
              lL=dict(hip=5, knee=3), lR=dict(hip=-5, knee=6))

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_R"]
        bc = (h[0] + 0.16 * H * fwd, sk.j["head"][1] - 0.20 * H)
        P.path_line([h, (h[0] + 0.10 * H * fwd, h[1] - 0.15 * H), (bc[0] - 0.01 * H * fwd, bc[1] + 0.15 * H)],
                    0.014 * H)
        P.ell(bc, 0.13 * H, 0.155 * H)
        P.poly([(bc[0], bc[1] + 0.145 * H), (bc[0] - 0.025 * H, bc[1] + 0.19 * H), (bc[0] + 0.025 * H, bc[1] + 0.19 * H)])
    return dict(body=b, look=lk, pose=p, props=props)


def _s7():
    b = Body.adult_f(590)
    lk = Look(hat="kerchief", dress="mid", shoes="heel")
    p = _pose(180, L=dict(sh=8, abd=10, elbow=96, wrist=-10, grip=0.6), R=dict(sh=-8, abd=8, elbow=12),
              lL=dict(hip=6, knee=4), lR=dict(hip=-6, knee=6, ankle=-4), head=-3)

    def props(P, sk, H, fwd, gy):
        e, w = sk.j["elbow_L"], sk.j["wrist_L"]
        m = _lerp2(e, w, 0.45)
        rc = (m[0], m[1] + 0.045 * H)
        P.ring(rc, 0.05 * H, 0.036 * H, 0.0, 180.0)
        P.ring(rc, 0.05 * H, 0.036 * H, 180.0, 360.0)
        top = rc[1] + 0.04 * H
        P.smooth([(rc[0] - 0.06 * H, top), (rc[0] + 0.06 * H, top), (rc[0] + 0.075 * H, top + 0.10 * H),
                  (rc[0] - 0.075 * H, top + 0.10 * H)], 0.12)
    return dict(body=b, look=lk, pose=p, props=props)


def _s8():
    b = Body.adult_m(620)
    lk = Look(hat="watch", coat="jacket")
    lf, lb = _walk(18, -16, 24)
    p = _pose(180, pitch=4, L=dict(sh=4, abd=10, elbow=4, grip=1.0), R=dict(sh=22, abd=8, elbow=18),
              lL=lf, lR=lb)

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_L"]
        y0 = h[1] + 0.035 * H
        w, hh = 0.30 * H, 0.19 * H
        P.ring((h[0], y0 - 0.005 * H), 0.035 * H, 0.020 * H, 180.0, 360.0)
        x0 = h[0] - w * 0.5
        draw.poly(P.c, [(x0 + 0.01 * H, y0), (x0 + w - 0.01 * H, y0), (x0 + w, y0 + 0.012 * H), (x0 + w, y0 + hh),
                        (x0, y0 + hh), (x0, y0 + 0.012 * H)])
        P._f()
    return dict(body=b, look=lk, pose=p, props=props)


def _s10():
    b = Body.adult_m(620)
    lk = Look(hat="flatcap", coat="jacket")
    lf, lb = _walk(18, -16, 22)
    p = _pose(0, R=dict(sh=34, abd=8, elbow=12, grip=1.0), L=dict(sh=-16, abd=8, elbow=16), lL=lb, lR=lf)

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_R"]
        dh = 0.17 * H
        at = (h[0] + 0.24 * H * fwd, gy)
        _dog(P, at, dh, fwd)
        collar = _xf([(0.30, -1.0)], at, 0, dh, fwd)[0]
        P.path_line(_curve(h, ((h[0] + collar[0]) * 0.5, max(h[1], collar[1]) + 0.07 * H), collar, 12), 0.010 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s11():
    b = Body.adult_f(590)
    lk = Look(hair="bun", dress="mid")
    p = _pose(0, head=24, neck=6, R=dict(sh=38, abd=10, elbow=84, grip=0.6), L=dict(sh=30, abd=14, elbow=92),
              lL=dict(hip=4, knee=3), lR=dict(hip=-4, knee=4))

    def props(P, sk, H, fwd, gy):
        a, c = sk.j["hand_R"], sk.j["elbow_R"]
        m = _lerp2(c, a, 0.6)
        ctr = (m[0] + 0.0 * H * fwd, m[1] - 0.035 * H)
        P.ell(ctr, 0.10 * H, 0.045 * H, -14 * fwd)
        P.circ((ctr[0] - 0.085 * H * fwd, ctr[1] - 0.03 * H), 0.04 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s12():
    b = Body.old_f(540)
    lk = Look(hair="bun", dress="mid")
    lL, lR = _sit(86, 86)
    p = _pose(0, spine=(8, 12, 16), neck=4, head=18, R=dict(sh=34, abd=10, elbow=8, wrist=-10, grip=0.2),
              L=dict(sh=22, abd=12, elbow=58), lL=lL, lR=lR)

    def props(P, sk, H, fwd, gy):
        pel = sk.j["pelvis"]
        seat = pel[1] + 0.035 * H
        bx = pel[0] - 0.13 * H * fwd
        fx = pel[0] + 0.15 * H * fwd
        P.poly([(bx - 0.02 * H * fwd, seat), (fx, seat), (fx, seat + 0.03 * H), (bx - 0.02 * H * fwd, seat + 0.03 * H)])
        P.line((bx, seat + 0.01 * H), (bx - 0.025 * H * fwd, seat - 0.36 * H), 0.03 * H)
        P.line((bx - 0.025 * H * fwd, seat - 0.36 * H), (bx + 0.03 * H * fwd, seat - 0.37 * H), 0.03 * H)
        P.line((bx, seat + 0.02 * H), (bx - 0.02 * H * fwd, gy), 0.024 * H)
        P.line((fx - 0.01 * H * fwd, seat + 0.02 * H), (fx, gy), 0.024 * H)
        ft = sk.j["ball_R"]
        cat_at = (ft[0] + 0.20 * H * fwd, gy)
        _cat_sitting(P, cat_at, 0.30 * H, -fwd)
        P.line((bx - 0.02 * H * fwd, gy - 0.006 * H), (cat_at[0] + 0.02 * H * fwd, gy - 0.006 * H), 0.012 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s13():
    b = Body.adult_f(590)
    lk = Look(hair="bob", coat="long")
    lf, lb = _walk(10, -18, 18)
    p = _pose(0, pitch=10, R=dict(sh=58, abd=8, elbow=14, grip=1.0), L=dict(sh=52, abd=12, elbow=18, grip=1.0),
              lL=lb, lR=lf)

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_R"]
        wr = 0.085 * H
        x_near = h[0] + 0.04 * H * fwd
        x_far = h[0] + 0.40 * H * fwd
        ytop = gy - 0.36 * H
        ybot = gy - 0.17 * H
        body = [(x_near, ytop), (x_far, ytop), (x_far + 0.01 * H * fwd, ytop + 0.06 * H),
                ((x_near + x_far) * 0.5 + 0.12 * H * fwd, ybot), ((x_near + x_far) * 0.5 - 0.06 * H * fwd, ybot),
                (x_near - 0.02 * H * fwd, ytop + 0.07 * H)]
        P.smooth(body, 0.2)
        hood = []
        for k in range(13):
            a = math.radians(180.0 - 90.0 * k / 12.0)
            hood.append((x_near + 0.13 * H * fwd + math.cos(a) * 0.13 * H * fwd, ytop - math.sin(a) * 0.13 * H))
        hood.append((x_near + 0.13 * H * fwd, ytop + 0.01 * H))
        P.poly(hood)
        P.line(h, (x_near + 0.01 * H * fwd, ytop + 0.02 * H), 0.02 * H)
        P.line((h[0] - 0.02 * H * fwd, h[1]), (h[0] + 0.02 * H * fwd, h[1]), 0.03 * H)
        for x in (x_near + 0.07 * H * fwd, x_far - 0.06 * H * fwd):
            P.wheel((x, gy - wr), wr, 0.016 * H, spokes=6, rot=15)
            P.line((x, gy - wr), ((x_near + x_far) * 0.5, ybot - 0.01 * H), 0.012 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s14():
    b = Body.adult_m(650, shoulder_w=0.102)
    lk = Look(hat="bowler", coat="long")
    p = _pose(90, L=dict(sh=0, abd=7, elbow=3), R=dict(sh=0, abd=7, elbow=3),
              lL=dict(hip=0, abd=3, knee=0), lR=dict(hip=0, abd=3, knee=0))
    return dict(body=b, look=lk, pose=p, props=None)


def _s15():
    b = Body.child(370)
    lk = Look(hair="short")
    lf, lb = _walk(26, -26, 40)
    p = _pose(0, pitch=6, head=-18, R=dict(sh=104, abd=10, elbow=10, grip=1.0), L=dict(sh=-30, abd=10, elbow=40),
              lL=lb, lR=lf)

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_R"]
        kc = (h[0] + 0.30 * H * fwd, h[1] - 0.24 * H)
        kite = [(0.0, -1.0), (0.62, -0.25), (0.0, 1.0), (-0.62, -0.25)]
        pts = _xf(kite, kc, 18 * fwd, 0.17 * H)
        P.poly(pts)
        P.line(h, pts[2], 0.010 * H)
        tail = [pts[2]]
        for k in range(1, 7):
            tail.append((pts[2][0] - 0.03 * H * fwd * k + 0.025 * H * math.sin(k * 1.9),
                         pts[2][1] + 0.055 * H * k))
        P.path_line(tail, 0.012 * H)
        for k in (2, 4, 6):
            q = tail[k]
            P.poly([(q[0] - 0.03 * H, q[1] - 0.018 * H), (q[0] + 0.03 * H, q[1] + 0.018 * H),
                    (q[0] + 0.03 * H, q[1] - 0.018 * H), (q[0] - 0.03 * H, q[1] + 0.018 * H)])
    return dict(body=b, look=lk, pose=p, props=props)


def _s16():
    b = Body.adult_m(620)
    lk = Look(hair="slick", coat="jacket")
    p = _pose(180, head=-4, L=dict(sh=92, abd=10, elbow=92, wrist=-80, grip=0.2), R=dict(sh=4, abd=8, elbow=88),
              lL=dict(hip=3, knee=2), lR=dict(hip=-3, knee=3))

    def props(P, sk, H, fwd, gy):
        h = sk.j["fingers_L"]
        ty = min(h[1], sk.j["wrist_L"][1]) - 0.015 * H
        tx = h[0] - 0.01 * H * fwd
        P.ell((tx, ty), 0.12 * H, 0.012 * H)
        bx = tx - 0.05 * H
        P.smooth([(bx - 0.018 * H, ty), (bx + 0.018 * H, ty), (bx + 0.02 * H, ty - 0.07 * H), (bx + 0.008 * H, ty - 0.09 * H),
                  (bx + 0.008 * H, ty - 0.13 * H), (bx - 0.008 * H, ty - 0.13 * H), (bx - 0.008 * H, ty - 0.09 * H),
                  (bx - 0.02 * H, ty - 0.07 * H)], 0.15)
        gx = tx + 0.05 * H
        P.poly([(gx - 0.025 * H, ty), (gx + 0.025 * H, ty), (gx + 0.025 * H, ty - 0.006 * H), (gx + 0.004 * H, ty - 0.01 * H),
                (gx + 0.004 * H, ty - 0.045 * H), (gx + 0.03 * H, ty - 0.085 * H), (gx - 0.03 * H, ty - 0.085 * H),
                (gx - 0.004 * H, ty - 0.045 * H), (gx - 0.004 * H, ty - 0.01 * H), (gx - 0.025 * H, ty - 0.006 * H)])
        e, w = sk.j["elbow_R"], sk.j["wrist_R"]
        m = _lerp2(e, w, 0.5)
        P.poly([(m[0] - 0.03 * H, m[1] - 0.01 * H), (m[0] + 0.03 * H, m[1] - 0.01 * H), (m[0] + 0.035 * H, m[1] + 0.13 * H),
                (m[0] - 0.025 * H, m[1] + 0.12 * H)])
    return dict(body=b, look=lk, pose=p, props=props)


def _s17():
    b = Body.adult_f(590)
    lk = Look(hat="kerchief", dress="mid")
    p = _pose(0, pitch=16, spine=(4, 6, 6), head=10, R=dict(sh=30, abd=10, elbow=22, grip=1.0),
              L=dict(sh=58, abd=14, elbow=34, grip=1.0), lL=dict(hip=-10, knee=8), lR=dict(hip=14, knee=10))

    def props(P, sk, H, fwd, gy):
        a, c = sk.j["hand_L"], sk.j["hand_R"]
        d = (c[0] - a[0], c[1] - a[1])
        if d[1] <= 1:
            d = (d[0], abs(d[1]) + 1.0)
        u = (gy - 0.07 * H - a[1]) / d[1]
        foot = (a[0] + d[0] * u, gy - 0.07 * H)
        top = (a[0] - d[0] * 0.25, a[1] - d[1] * 0.25)
        P.line(top, foot, 0.016 * H)
        bx, by = foot
        pts = [(bx - 0.03 * H, by - 0.01 * H), (bx + 0.03 * H, by - 0.01 * H), (bx + 0.07 * H, by + 0.065 * H)]
        for k in range(9):
            x = bx + 0.07 * H - 0.14 * H * (k + 0.5) / 9
            pts.append((x, by + (0.075 if k % 2 == 0 else 0.055) * H))
        pts.append((bx - 0.07 * H, by + 0.065 * H))
        P.poly(pts)
    return dict(body=b, look=lk, pose=p, props=props)


def _s18():
    b = Body.heavy_m(630)
    lk = Look(hat="fedora", coat="jacket", belly=0.035)
    p = _pose(0, pitch=-4, R=dict(sh=52, abd=12, elbow=116, grip=0.8), L=dict(sh=-6, abd=14, elbow=24),
              lL=dict(hip=5, knee=3, abd=6), lR=dict(hip=-5, knee=4, abd=6))

    def props(P, sk, H, fwd, gy):
        m = _add(sk.j["head"], (0.07 * H * fwd, 0.035 * H))
        tip = _add(m, (0.075 * H * fwd, -0.01 * H))
        P.line(m, tip, 0.018 * H)
        sm = [(tip[0] + 0.01 * H * fwd + 0.02 * H * math.sin(k * 1.3), tip[1] - 0.03 * H * k) for k in range(1, 8)]
        P.path_line(sm, 0.016 * H, 0.006 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s19():
    b = Body.child(370)
    lk = Look(hair="ponytail", dress="knee")
    p = _pose(90, L=dict(sh=10, abd=58, elbow=6, grip=1.0), R=dict(sh=10, abd=58, elbow=6, grip=1.0),
              lL=dict(hip=0, abd=4, knee=60, ankle=20), lR=dict(hip=0, abd=4, knee=50, ankle=20))

    def props(P, sk, H, fwd, gy):
        a, c = sk.j["hand_L"], sk.j["hand_R"]
        cx = (a[0] + c[0]) * 0.5
        top = sk.j["crown"][1] - 0.15 * H
        pts = []
        for k in range(31):
            u = k / 30.0
            x = lerp(a[0], c[0], u)
            y = lerp(a[1], c[1], u) - (math.sin(math.pi * u) ** 0.8) * (lerp(a[1], c[1], u) - top)
            pts.append((x, y))
        P.path_line(pts, 0.013 * H)
        for q in (a, c):
            P.cap((q[0], q[1] - 0.01 * H), (q[0], q[1] + 0.05 * H), 0.012 * H)
        del cx
    return dict(body=b, look=lk, pose=p, props=props)


def _s20():
    b = Body.adult_m(620)
    lk = Look(hair="curly", beard=True, coat="long")
    p = _pose(0, head=4, R=dict(sh=62, abd=10, elbow=44, grip=0.9), L=dict(sh=22, abd=18, elbow=72, grip=0.5),
              lL=dict(hip=-6, knee=4), lR=dict(hip=8, knee=3))

    def props(P, sk, H, fwd, gy):
        h = sk.j["fingers_R"]
        P.line(h, (h[0] + 0.07 * H * fwd, h[1] - 0.03 * H), 0.010 * H)
        pl = sk.j["hand_L"]
        pal = (pl[0] - 0.01 * H * fwd, pl[1] - 0.01 * H)
        P.ell(pal, 0.075 * H, 0.03 * H, -10 * fwd)
        ex = h[0] + 0.13 * H * fwd
        top = gy - 0.70 * H
        P.line((ex, top), (ex - 0.10 * H * fwd, gy), 0.016 * H)
        P.line((ex, top), (ex + 0.12 * H * fwd, gy), 0.016 * H)
        P.line((ex + 0.01 * H * fwd, top + 0.05 * H), (ex + 0.03 * H * fwd, gy), 0.012 * H)
        cv = [(-0.12, -0.30), (0.10, -0.30), (0.13, 0.0), (-0.09, 0.0)]
        P.poly(_xf(cv, (ex, gy - 0.30 * H), 0.0, H, fwd))
        P.line((ex - 0.12 * H * fwd, gy - 0.29 * H), (ex + 0.14 * H * fwd, gy - 0.29 * H), 0.014 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s21():
    b = Body.adult_f(590)
    lk = Look(hair="long", dress="floor")
    p = _pose(180, head=-6, head_roll=10, L=dict(sh=158, abd=24, elbow=78, grip=1.0), R=dict(sh=6, abd=10, elbow=26),
              lL=dict(hip=3, knee=3), lR=dict(hip=-3, knee=4))

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_L"]
        d = _dirv(-90 - 35 * fwd)
        hd = _add(h, d, 0.05 * H)
        P.line(h, hd, 0.016 * H)
        P.ell(_add(hd, d, 0.03 * H), 0.024 * H, 0.04 * H, math.degrees(math.atan2(d[1], d[0])) + 90)
    return dict(body=b, look=lk, pose=p, props=props)


def _s22():
    b = Body.adult_m(620)
    lk = Look(hair="short")
    p = _pose(0, pitch=10, head=12, neck=4, R=dict(sh=56, abd=14, elbow=124, grip=1.0),
              L=dict(sh=78, abd=16, elbow=66, grip=1.0), lL=dict(hip=18, knee=18, abd=6),
              lR=dict(hip=-22, knee=20, ankle=-18, abd=6))

    def props(P, sk, H, fwd, gy):
        for s in ("L", "R"):
            P.circ(sk.j["hand_" + s], 0.045 * H)
        pel, wst = sk.j["pelvis"], sk.j["waist"]
        P.poly([(wst[0] - 0.085 * H, wst[1] + 0.01 * H), (wst[0] + 0.07 * H, wst[1] + 0.01 * H),
                (pel[0] + 0.10 * H, pel[1] + 0.11 * H), (pel[0] - 0.11 * H, pel[1] + 0.11 * H)])
    return dict(body=b, look=lk, pose=p, props=props)


def _s23():
    b = Body.old_f(540)
    lk = Look(hat="kerchief", dress="mid", coat="long")
    p = _pose(180, pitch=10, spine=(4, 10, 14), neck=-8, head=-4, L=dict(sh=-4, abd=10, elbow=8, grip=1.0),
              R=dict(sh=10, abd=14, elbow=10, grip=1.0), lL=dict(hip=6, knee=10), lR=dict(hip=-6, knee=12))

    def props(P, sk, H, fwd, gy):
        for s, w in (("L", 0.15), ("R", 0.13)):
            h = sk.j["hand_" + s]
            P.ring((h[0], h[1] + 0.03 * H), 0.04 * H, 0.026 * H, 180.0, 360.0)
            y0 = h[1] + 0.03 * H
            P.poly([(h[0] - w * 0.45 * H, y0), (h[0] + w * 0.45 * H, y0), (h[0] + w * 0.55 * H, y0 + 0.17 * H),
                    (h[0] - w * 0.55 * H, y0 + 0.17 * H)])
        h = sk.j["hand_L"]
        a = (h[0] + 0.03 * H * fwd, h[1] + 0.06 * H)
        b_ = (h[0] - 0.08 * H * fwd, h[1] - 0.16 * H)
        P.line(a, b_, 0.024 * H)
        for k in (-1, 0, 1):
            P.poly([b_, _add(b_, (-0.03 * H * fwd + 0.025 * H * k, -0.09 * H)),
                    _add(b_, (-0.01 * H * fwd + 0.025 * H * k, -0.085 * H))])
    return dict(body=b, look=lk, pose=p, props=props)


def _s24():
    b = Body.adult_m(620)
    lk = Look(hair="slick", coat="jacket")
    p = _pose(0, R=dict(sh=72, abd=14, elbow=146, wrist=10, grip=0.8), L=dict(sh=30, abd=16, elbow=82, grip=1.0),
              lL=dict(hip=4, knee=3), lR=dict(hip=-4, knee=4))

    def props(P, sk, H, fwd, gy):
        hd = sk.j["head"]
        ear = (hd[0] - 0.005 * H * fwd, hd[1] - 0.005 * H)
        mouth = (hd[0] + 0.055 * H * fwd, hd[1] + 0.065 * H)
        P.line(ear, mouth, 0.016 * H)
        P.ell(ear, 0.018 * H, 0.026 * H)
        P.ell(mouth, 0.018 * H, 0.024 * H)
        h = sk.j["hand_L"]
        P.line((h[0], h[1] - 0.10 * H), (h[0], h[1] + 0.08 * H), 0.016 * H)
        top = (h[0], h[1] - 0.10 * H)
        P.poly([top, (top[0] + 0.035 * H * fwd, top[1] - 0.025 * H), (top[0] + 0.04 * H * fwd, top[1] + 0.005 * H)])
        P.ell((h[0], h[1] + 0.085 * H), 0.045 * H, 0.016 * H)
        P.path_line(_curve((h[0], h[1] + 0.08 * H), (h[0] - 0.12 * H * fwd, h[1] + 0.02 * H), mouth, 14), 0.007 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s25():
    b = Body.adult_f(590)
    lk = Look(hair="bun", dress="floor", shoes="heel")
    p = _pose(0, head=-4, R=dict(sh=58, abd=12, elbow=96, wrist=-10, grip=0.8), L=dict(sh=-14, abd=18, elbow=24),
              lL=dict(hip=3, knee=3), lR=dict(hip=-3, knee=4))

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_R"]
        r = 0.13 * H
        pts = [h]
        for k in range(17):
            a = math.radians(-160.0 + 130.0 * k / 16.0)
            rr = r * (1.0 if k % 2 == 0 else 0.93)
            pts.append((h[0] + math.cos(a) * rr * fwd, h[1] + math.sin(a) * rr))
        P.poly(pts)
    return dict(body=b, look=lk, pose=p, props=props)


def _s26():
    b = Body.heavy_m(630)
    lk = Look(hair="short", beard=True)
    p = _pose(90, L=dict(sh=0, abd=158, elbow=6, grip=1.0), R=dict(sh=0, abd=158, elbow=6, grip=1.0),
              lL=dict(hip=0, abd=12, knee=4), lR=dict(hip=0, abd=12, knee=4))

    def props(P, sk, H, fwd, gy):
        a, c = sk.j["hand_L"], sk.j["hand_R"]
        y = (a[1] + c[1]) * 0.5
        x0, x1 = min(a[0], c[0]), max(a[0], c[0])
        cx = (x0 + x1) * 0.5
        P.line((cx - 0.34 * H, y), (cx + 0.34 * H, y), 0.018 * H)
        P.circ((cx - 0.35 * H, y), 0.08 * H)
        P.circ((cx + 0.35 * H, y), 0.08 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s27():
    b = Body.child(360)
    lk = Look(hair="bob", dress="knee")
    p = _pose(0, head=10, R=dict(sh=10, abd=10, elbow=10, grip=1.0), L=dict(sh=-6, abd=8, elbow=14),
              lL=dict(hip=3, knee=3), lR=dict(hip=-4, knee=4))

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_R"]
        hc = (h[0] + 0.03 * H * fwd, h[1] + 0.11 * H)
        P.line(h, (hc[0] - 0.02 * H * fwd, hc[1] - 0.03 * H), 0.03 * H)
        P.circ(hc, 0.065 * H)
        P.circ((hc[0] - 0.05 * H, hc[1] - 0.05 * H), 0.025 * H)
        P.circ((hc[0] + 0.05 * H, hc[1] - 0.05 * H), 0.025 * H)
        bc = (hc[0], hc[1] + 0.12 * H)
        P.ell(bc, 0.06 * H, 0.075 * H)
        P.cap((bc[0] - 0.035 * H, bc[1] + 0.05 * H), (bc[0] - 0.04 * H, bc[1] + 0.11 * H), 0.024 * H)
        P.cap((bc[0] + 0.035 * H, bc[1] + 0.05 * H), (bc[0] + 0.045 * H, bc[1] + 0.10 * H), 0.024 * H)
        P.cap((bc[0] + 0.05 * H * fwd, bc[1] - 0.03 * H), (bc[0] + 0.085 * H * fwd, bc[1] + 0.03 * H), 0.02 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s28():
    b = Body.adult_m(620)
    lk = Look(hat="watch", coat="jacket", beard=True)
    p = _pose(0, pitch=-4, head=-6, R=dict(sh=36, abd=10, elbow=52, grip=1.0), L=dict(sh=62, abd=14, elbow=44, grip=1.0),
              lL=dict(hip=-8, knee=4), lR=dict(hip=10, knee=6))

    def props(P, sk, H, fwd, gy):
        a, c = sk.j["hand_R"], sk.j["hand_L"]
        d = (c[0] - a[0], c[1] - a[1])
        L = math.hypot(*d) or 1.0
        u = (d[0] / L, d[1] / L)
        if u[0] * fwd < 0.3:
            u = (0.75 * fwd, -0.66)
        butt = _add(a, u, -0.06 * H)
        pts = []
        for k in range(13):
            s = k / 12.0
            pts.append((butt[0] + u[0] * 0.80 * H * s, butt[1] + u[1] * 0.80 * H * s + 0.10 * H * s * s))
        P.path_line(pts, 0.020 * H, 0.008 * H)
        tip = pts[-1]
        end = (tip[0], tip[1] + 0.34 * H)
        P.line(tip, end, 0.007 * H)
        _fish(P, end, 0.13 * H, 90.0)
    return dict(body=b, look=lk, pose=p, props=props)


def _s29():
    b = Body.adult_f(590)
    lk = Look(hair="bob", coat="long")
    p = _pose(180, L=dict(sh=58, abd=10, elbow=32, grip=1.0), R=dict(sh=-8, abd=8, elbow=16),
              lL=dict(hip=5, knee=3), lR=dict(hip=-5, knee=5))

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_L"]
        P.ring((h[0], h[1] + 0.012 * H), 0.02 * H, 0.011 * H)
        top = h[1] + 0.03 * H
        w, hh = 0.15 * H, 0.18 * H
        cx = h[0]
        dome = []
        for k in range(13):
            a = math.radians(180 - 180 * k / 12.0)
            dome.append((cx + math.cos(a) * w * 0.5, top + 0.06 * H - math.sin(a) * 0.05 * H))
        P.path_line(dome, 0.012 * H)
        P.line((cx, top - 0.005 * H), (cx, top + 0.012 * H), 0.012 * H)
        for k in range(6):
            x = cx - w * 0.5 + w * k / 5.0
            P.line((x, top + 0.06 * H), (x, top + hh), 0.007 * H)
        P.line((cx - w * 0.55, top + hh), (cx + w * 0.55, top + hh), 0.026 * H)
        P.line((cx - w * 0.5, top + 0.065 * H), (cx + w * 0.5, top + 0.065 * H), 0.008 * H)
        P.line((cx - w * 0.3, top + 0.125 * H), (cx + w * 0.3, top + 0.125 * H), 0.006 * H)
        bd = (cx + 0.005 * H * fwd, top + 0.105 * H)
        P.ell(bd, 0.026 * H, 0.016 * H, -20 * fwd)
        P.circ((bd[0] + 0.022 * H * fwd, bd[1] - 0.014 * H), 0.011 * H)
        P.poly([(bd[0] - 0.02 * H * fwd, bd[1]), (bd[0] - 0.05 * H * fwd, bd[1] + 0.02 * H), (bd[0] - 0.02 * H * fwd, bd[1] + 0.012 * H)])
    return dict(body=b, look=lk, pose=p, props=props)


def _s30():
    b = Body.adult_f(585)
    lk = Look(hair="long")
    lL, lR = _sit(84, 84)
    p = _pose(0, spine=(10, 16, 20), neck=10, head=34, R=dict(sh=-6, abd=12, elbow=128, grip=0.3),
              L=dict(sh=0, abd=16, elbow=124, grip=0.3), lL=lL, lR=lR)

    def props(P, sk, H, fwd, gy):
        pel = sk.j["pelvis"]
        seat = pel[1] + 0.035 * H
        P.ell((pel[0] - 0.01 * H * fwd, seat + 0.012 * H), 0.10 * H, 0.018 * H)
        for dx, ex in ((-0.07, -0.10), (0.06, 0.09)):
            P.line((pel[0] + dx * H * fwd, seat + 0.02 * H), (pel[0] + ex * H * fwd, gy), 0.02 * H)
        P.line((pel[0] - 0.085 * H * fwd, seat + 0.16 * H), (pel[0] + 0.075 * H * fwd, seat + 0.16 * H), 0.014 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s31():
    b = Body.adult_m(620)
    lk = Look(hair="short", coat="jacket")
    p = _pose(0, pitch=-12, spine=(0, -4, -6), head=-16, R=dict(sh=80, abd=10, elbow=52, grip=0.9),
              L=dict(sh=72, abd=14, elbow=60, grip=0.9), lL=dict(hip=-6, knee=8), lR=dict(hip=10, knee=8))

    def props(P, sk, H, fwd, gy):
        hd = sk.j["head"]
        m = _add(hd, (0.07 * H * fwd, 0.03 * H))
        ang = -28.0 if fwd > 0 else -152.0
        d = _dirv(ang)
        end = _add(m, d, 0.24 * H)
        P.line(m, end, 0.018 * H)
        n = (-d[1], d[0])
        bell = [_add(end, n, 0.010 * H), _add(_add(end, d, 0.08 * H), n, 0.05 * H),
                _add(_add(end, d, 0.085 * H), n, -0.05 * H), _add(end, n, -0.010 * H)]
        P.poly(bell)
        a0 = _add(m, d, 0.06 * H)
        a1 = _add(m, d, 0.18 * H)
        P.ring(((a0[0] + a1[0]) * 0.5 - n[0] * 0.03 * H, (a0[1] + a1[1]) * 0.5 - n[1] * 0.03 * H), 0.045 * H, 0.031 * H,
               math.degrees(math.atan2(-n[1], -n[0])) - 90, math.degrees(math.atan2(-n[1], -n[0])) + 90)
        for k in range(3):
            v = _add(m, d, (0.09 + 0.025 * k) * H)
            P.line(v, _add(v, n, 0.035 * H), 0.011 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s32():
    b = Body.adult_f(590)
    lk = Look(hair="curly", dress="knee")
    p = _pose(0, head=-4, R=dict(sh=70, abd=12, elbow=64, grip=1.0), L=dict(sh=150, abd=26, elbow=104),
              lL=dict(hip=3, knee=3), lR=dict(hip=-3, knee=4))

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_R"]
        top = (h[0] + 0.01 * H * fwd, h[1] - 0.09 * H)
        P.line(h, top, 0.016 * H)
        P.ell((top[0], top[1] - 0.04 * H), 0.04 * H, 0.055 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s33():
    b = Body.adult_m(620)
    lk = Look(hat="flatcap", coat="jacket")
    lf, lb = _walk(16, -16, 22)
    p = _pose(180, L=dict(sh=142, abd=10, elbow=58, grip=1.0), R=dict(sh=18, abd=10, elbow=16), lL=lf, lR=lb)

    def props(P, sk, H, fwd, gy):
        sh = sk.j["shoulder_L"]
        ang = 180.0 + 14.0 if fwd < 0 else -14.0
        d = _dirv(ang)
        n = (-d[1], d[0])
        c0 = _add(sh, (0.0, -0.035 * H))
        a = _add(c0, d, -0.42 * H)
        b_ = _add(c0, d, 0.40 * H)
        gap = 0.075 * H
        P.line(a, b_, 0.016 * H)
        P.line(_add(a, n, -gap), _add(b_, n, -gap), 0.016 * H)
        k = 0
        while k * 0.08 * H < 0.82 * H:
            q = _add(a, d, 0.02 * H + k * 0.08 * H)
            P.line(q, _add(q, n, -gap), 0.011 * H)
            k += 1
    return dict(body=b, look=lk, pose=p, props=props)


def _s34():
    b = Body.child(300)
    lk = Look(hair="bob", dress="knee")
    p = _pose(90, L=dict(sh=0, abd=40, elbow=4, grip=0.2), R=dict(sh=0, abd=40, elbow=4, grip=0.2),
              lL=dict(hip=0, abd=9, knee=0), lR=dict(hip=0, abd=9, knee=0))
    return dict(body=b, look=lk, pose=p, props=None, chain=3)


def _s35():
    b = Body.adult_m(620)
    lk = Look(hat="watch")
    lf, lb = _walk(16, -14, 22)
    p = _pose(180, pitch=6, L=dict(sh=138, abd=12, elbow=128, grip=1.0), R=dict(sh=20, abd=8, elbow=20),
              lL=lf, lR=lb)

    def props(P, sk, H, fwd, gy):
        sh = sk.j["shoulder_L"]
        a = _add(sh, (0.02 * H * fwd, -0.04 * H))
        bb = _add(a, (-0.17 * H * fwd, 0.25 * H))
        P.cap(a, bb, 0.07 * H, 0.075 * H)
        P.poly([_add(a, (0.0, -0.06 * H)), _add(a, (0.05 * H * fwd, -0.10 * H)), _add(a, (0.04 * H * fwd, -0.03 * H))])
    return dict(body=b, look=lk, pose=p, props=props)


def _s36():
    b = Body.adult_m(600)
    lk = Look(hair="short", coat="jacket")
    lL, lR = _sit(84, 90)
    p = _pose(0, spine=(4, 6, 6), head=6, R=dict(sh=24, abd=14, elbow=34, grip=1.0), L=dict(sh=30, abd=16, elbow=50),
              lL=lL, lR=lR)

    def props(P, sk, H, fwd, gy):
        pel = sk.j["pelvis"]
        seat = pel[1] + 0.035 * H
        wr = 0.21 * H
        wc = (pel[0] - 0.02 * H * fwd, gy - wr)
        P.wheel(wc, wr, 0.016 * H, spokes=8, rot=10)
        P.line((pel[0] - 0.10 * H * fwd, seat), (pel[0] + 0.16 * H * fwd, seat), 0.026 * H)
        bx = pel[0] - 0.11 * H * fwd
        P.line((bx, seat), (bx - 0.03 * H * fwd, seat - 0.36 * H), 0.022 * H)
        P.line((bx - 0.03 * H * fwd, seat - 0.36 * H), (bx - 0.10 * H * fwd, seat - 0.35 * H), 0.02 * H)
        ft = sk.j["ankle_R"]
        P.line((pel[0] + 0.15 * H * fwd, seat), (ft[0] + 0.02 * H * fwd, gy - 0.07 * H), 0.018 * H)
        P.line((ft[0] - 0.04 * H * fwd, gy - 0.07 * H), (ft[0] + 0.07 * H * fwd, gy - 0.07 * H), 0.016 * H)
        P.wheel((ft[0] + 0.02 * H * fwd, gy - 0.035 * H), 0.035 * H, 0.012 * H, spokes=3)
    return dict(body=b, look=lk, pose=p, props=props)


def _s37():
    b = Body.adult_f(590)
    lk = Look(hair="bob", dress="mid", shoes="heel")
    p = _pose(0, R=dict(sh=10, abd=12, elbow=10, grip=1.0), L=dict(sh=-10, abd=10, elbow=20),
              lL=dict(hip=4, knee=3), lR=dict(hip=-4, knee=4))

    def props(P, sk, H, fwd, gy):
        cr = sk.j["crown"]
        c = (cr[0] + 0.01 * H * fwd, cr[1] + 0.01 * H)
        P.ell(c, 0.15 * H, 0.018 * H, -8 * fwd)
        P.smooth([(c[0] - 0.06 * H, c[1]), (c[0] - 0.055 * H, c[1] - 0.05 * H), (c[0], c[1] - 0.065 * H),
                  (c[0] + 0.055 * H, c[1] - 0.05 * H), (c[0] + 0.06 * H, c[1])], 0.4)
        P.circ((c[0] - 0.05 * H * fwd, c[1] - 0.05 * H), 0.022 * H)
        h = sk.j["hand_R"]
        P.poly([(h[0] - 0.005 * H, h[1]), (h[0] - 0.07 * H, h[1] + 0.05 * H), (h[0] - 0.06 * H, h[1] + 0.055 * H),
                (h[0], h[1] + 0.016 * H), (h[0] + 0.06 * H, h[1] + 0.055 * H), (h[0] + 0.07 * H, h[1] + 0.05 * H),
                (h[0] + 0.005 * H, h[1])])
        y0 = h[1] + 0.05 * H
        P.smooth([(h[0] - 0.09 * H, y0), (h[0], y0 - 0.012 * H), (h[0] + 0.09 * H, y0), (h[0] + 0.09 * H, y0 + 0.13 * H),
                  (h[0], y0 + 0.142 * H), (h[0] - 0.09 * H, y0 + 0.13 * H)], 0.1)
    return dict(body=b, look=lk, pose=p, props=props)


def _s38():
    b = Body.child(370)
    lk = Look(hair="short")
    p = _pose(0, pitch=8, R=dict(sh=58, abd=10, elbow=22, grip=1.0), L=dict(sh=54, abd=14, elbow=26, grip=1.0),
              lL=dict(hip=6, knee=14, ankle=-6), lR=dict(hip=-34, knee=26, ankle=-20))

    def props(P, sk, H, fwd, gy):
        st = sk.j["heel_L"]
        dy = max(st[1], sk.j["ball_L"][1]) + 0.012 * H
        x_b = st[0] - 0.10 * H * fwd
        x_f = st[0] + 0.32 * H * fwd
        P.line((x_b, dy + 0.012 * H), (x_f, dy + 0.012 * H), 0.024 * H)
        wr = 0.05 * H
        P.wheel((x_b, dy + 0.012 * H + wr), wr, 0.014 * H, spokes=4)
        P.wheel((x_f + 0.03 * H * fwd, dy + 0.012 * H + wr), wr, 0.014 * H, spokes=4)
        h = sk.j["hand_R"]
        P.line((x_f + 0.03 * H * fwd, dy + 0.012 * H + wr), (h[0] + 0.01 * H * fwd, h[1]), 0.018 * H)
        P.line((h[0] - 0.035 * H, h[1] - 0.005 * H), (h[0] + 0.035 * H, h[1] + 0.005 * H), 0.018 * H)
    return dict(body=b, look=lk, pose=p, props=props, ground_from="deck")


def _s39():
    b = Body.adult_f(590)
    lk = Look(hair="bun", dress="knee")
    p = _pose(0, pitch=6, head=12, R=dict(sh=52, abd=10, elbow=10, grip=1.0), L=dict(sh=-6, abd=10, elbow=20),
              lL=dict(hip=4, knee=3), lR=dict(hip=-4, knee=4))

    def props(P, sk, H, fwd, gy):
        h = sk.j["hand_R"]
        c = (h[0] + 0.07 * H * fwd, h[1] + 0.05 * H)
        P.ring((h[0] + 0.03 * H * fwd, h[1] + 0.01 * H), 0.04 * H, 0.026 * H, -160 if fwd > 0 else -20, 20 if fwd > 0 else 200)
        P.poly(_xf([(-0.05, -0.04), (0.05, -0.04), (0.055, 0.05), (-0.055, 0.05)], c, 18 * fwd, H, fwd))
        sp0 = _xf([(0.04, 0.02)], c, 18 * fwd, H, fwd)[0]
        sp1 = _add(sp0, (0.12 * H * fwd, -0.02 * H))
        P.line(sp0, sp1, 0.012 * H)
        P.ell(sp1, 0.012 * H, 0.022 * H, 30 * fwd)
        px = sp1[0] + 0.01 * H * fwd
        P.poly([(px - 0.04 * H, gy - 0.075 * H), (px + 0.04 * H, gy - 0.075 * H), (px + 0.03 * H, gy), (px - 0.03 * H, gy)])
        for k, a in enumerate((-60, -90, -120, -75, -105)):
            ln = (0.11 if k < 3 else 0.075) * H
            d = _dirv(a)
            q = (px + d[0] * ln * 0.5, gy - 0.075 * H + d[1] * ln * 0.5)
            P.ell(q, ln * 0.5, 0.016 * H, a)
        P.line((sk.j["ball_R"][0] - 0.02 * H * fwd, gy - 0.006 * H), (px, gy - 0.006 * H), 0.016 * H)
    return dict(body=b, look=lk, pose=p, props=props)


def _s40():
    b = Body.adult_m(620)
    lk = Look(hair="short", dress="knee")
    p = _pose(180, head=-6, L=dict(sh=86, abd=8, elbow=2, wrist=4, grip=0.2), R=dict(sh=82, abd=12, elbow=4, grip=0.2),
              lL=dict(hip=12, knee=4), lR=dict(hip=-8, knee=10, ankle=-8))

    def props(P, sk, H, fwd, gy):
        cr = sk.j["crown"]
        hb = sk.j["head"]
        base = [(hb[0] - 0.07 * H, cr[1] + 0.035 * H), (hb[0] + 0.07 * H, cr[1] + 0.035 * H)]
        tip = (hb[0] - 0.16 * H * fwd, cr[1] + 0.07 * H)
        P.smooth([base[0], (hb[0] - 0.03 * H * fwd, cr[1] - 0.03 * H), (hb[0] - 0.10 * H * fwd, cr[1] - 0.01 * H), tip,
                  (hb[0] - 0.08 * H * fwd, cr[1] + 0.03 * H), base[1]], 0.35)
        P.circ(tip, 0.022 * H)
    return dict(body=b, look=lk, pose=p, props=props)


_SPECS = {1: _s1, 2: _s2, 3: _s3, 4: _s4, 5: _s5, 6: _s6, 7: _s7, 8: _s8, 10: _s10, 11: _s11, 12: _s12,
          13: _s13, 14: _s14, 15: _s15, 16: _s16, 17: _s17, 18: _s18, 19: _s19, 20: _s20, 21: _s21, 22: _s22,
          23: _s23, 24: _s24, 25: _s25, 26: _s26, 27: _s27, 28: _s28, 29: _s29, 30: _s30, 31: _s31, 32: _s32,
          33: _s33, 34: _s34, 35: _s35, 36: _s36, 37: _s37, 38: _s38, 39: _s39, 40: _s40}


# ============================================================================ doll 9: her
def _her_doll(c):
    """HER as a paper doll: front view, bob, RED trench (collar up) with RED sleeves down to the
    wrists (one red shape, as cast.her(coat=True)), her paper hands holding INK binoculars at
    the eyes, elbows out. Draws class colours on c; returns the skeleton."""
    body = Body.adult_f(590, upper_arm=0.002, forearm=0.002, hand=0.002, hand_scale=0.02)
    lk = Look(hair="bob", coat="trench", shoes="heel", colors={"coat": CRED}, opts={"collar": True})
    p = _pose(90, L=dict(sh=0, abd=4, elbow=0), R=dict(sh=0, abd=4, elbow=0),
              lL=dict(hip=0, abd=4.5, knee=0), lR=dict(hip=0, abd=4.5, knee=0))
    sk = FG.solve(p, body)
    hx, hy = sk.j["head"]
    c.translate(PIN[0] - hx, PIN[1] - hy)
    FG.draw_figure(None, sk, lk, c, color=WHITE, eyes=False)
    H = sk.H
    hc = sk.j["head"]
    eye_y = hc[1] - 0.012 * H
    Pr, Pi, Pw = _Pen(c, CRED), _Pen(c, CINK), _Pen(c, WHITE)
    BR, BX = 0.050 * H, 0.046 * H            # binocular objective radius, half separation
    for s, sx in (("R", -1.0), ("L", 1.0)):
        sh = sk.j["shoulder_" + s]
        el = (hc[0] + sx * 0.215 * H, sh[1] + 0.105 * H)
        hand = (hc[0] + sx * (BX + BR + 0.006 * H), eye_y + 0.012 * H)
        wr = (hand[0] + sx * 0.018 * H, hand[1] + 0.05 * H)
        Pr.cap(sh, el, 0.036 * H, 0.031 * H)
        Pr.cap(el, wr, 0.031 * H, 0.025 * H)
        Pr.cap((wr[0] + sx * 0.004 * H, wr[1] + 0.012 * H), (wr[0] - sx * 0.002 * H, wr[1] - 0.004 * H), 0.03 * H)
    for sx in (-1.0, 1.0):
        Pi.circ((hc[0] + sx * BX, eye_y), BR)
    Pi.poly([(hc[0] - 0.03 * H, eye_y - 0.022 * H), (hc[0] + 0.03 * H, eye_y - 0.022 * H),
             (hc[0] + 0.03 * H, eye_y + 0.020 * H), (hc[0] - 0.03 * H, eye_y + 0.020 * H)])
    for sx in (-1.0, 1.0):
        hand = (hc[0] + sx * (BX + BR + 0.006 * H), eye_y + 0.012 * H)
        Pw.ell(hand, 0.024 * H, 0.042 * H, -sx * 10)
        for k in range(3):
            fy = hand[1] - 0.030 * H + k * 0.019 * H
            Pw.cap((hand[0], fy), (hand[0] - sx * 0.030 * H, fy - 0.004 * H), 0.0085 * H)
    return sk


# ============================================================================ build
def _trace(mask, seed, sag, amp, max_len, eps=1.2, min_area=40.0, scale=1.0):
    """Mask -> list of polygons (outer contours and holes) in build-raster px, scissor cut."""
    cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    if hier is None:
        return polys
    for k, cn in enumerate(cnts):
        if abs(cv2.contourArea(cn)) < min_area:
            continue
        ap = cv2.approxPolyDP(cn, eps, True).reshape(-1, 2).astype(float)
        if len(ap) < 3:
            continue
        pts = [(float(x) + 0.5, float(y) + 0.5) for x, y in ap]
        cut = bass.scissor(pts, seed=seed * 31 + k, sag=sag, amp=amp, max_len=max_len, corner=34.0)
        if len(cut) >= 3:
            polys.append(cut)
    return polys


def _to_path(polys, origin):
    s = cairo.ImageSurface(cairo.FORMAT_A8, 4, 4)
    c = cairo.Context(s)
    for poly in polys:
        c.move_to(poly[0][0] - origin[0], poly[0][1] - origin[1])
        for x, y in poly[1:]:
            c.line_to(x - origin[0], y - origin[1])
        c.close_path()
    return c.copy_path()


class Doll:
    """One cut-paper doll: paths in REF px around its pin (the head centre)."""

    def __init__(self, i, paper, red=None, ink=None, com=(0.0, 0.0), bbox=None, tone=1.0):
        self.i = i
        self.path_paper, self.path_red, self.path_ink = paper, red, ink
        self.com = com
        self.bbox = bbox
        self.tone = tone
        # a doll pinned through the head hangs with its centre of mass under the pin
        # (the pin is tight: only part of the way)
        self.hang = clamp(-math.degrees(math.atan2(com[0], max(com[1], 1.0))) * 0.4, -6.0, 6.0)

    def place(self, ctx, pin, k, angle):
        ctx.translate(pin[0], pin[1])
        ctx.rotate(math.radians(angle))
        ctx.scale(k, k)

    def draw(self, ctx, pin, k=K_DOLL, angle=0.0, paper=None, red=RED, ink=INK, alpha=1.0, solid=None):
        """solid: draw every part in one colour (shadows / casters)."""
        ctx.save()
        self.place(ctx, pin, k, angle)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        col = solid if solid is not None else (paper or PAPER)
        ctx.new_path()
        ctx.append_path(self.path_paper)
        ctx.set_source_rgba(col[0], col[1], col[2], alpha)
        ctx.fill()
        if solid is None:
            for pth, cc in ((self.path_red, red), (self.path_ink, ink)):
                if pth is not None:
                    ctx.append_path(pth)
                    ctx.set_source_rgba(cc[0], cc[1], cc[2], alpha)
                    ctx.fill()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        ctx.restore()


def _raster(fn):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, RS, RS)
    c = cairo.Context(surf)
    c.set_antialias(cairo.ANTIALIAS_GRAY)
    fn(c)
    surf.flush()
    return surf_array(surf).copy()


def _build(i):
    if i == 9:
        arr = _raster(_her_doll)
    else:
        spec = _SPECS[i]()

        def paint(c):
            body, lk, pose = spec["body"], spec["look"], spec["pose"]
            sk = FG.solve(pose, body)
            hx, hy = sk.j["head"]
            c.translate(PIN[0] - hx, PIN[1] - hy)
            n = spec.get("chain", 1)
            if n > 1:
                span = abs(sk.j["hand_L"][0] - sk.j["hand_R"][0]) * 0.98
                for k in range(n):
                    c.save()
                    c.translate((k - (n - 1) * 0.5) * span, 0.0)
                    FG.draw_figure(None, sk, lk, c, color=WHITE, eyes=False)
                    c.restore()
            else:
                FG.draw_figure(None, sk, lk, c, color=WHITE, eyes=False)
            if spec.get("props"):
                fwd = 1.0 if math.cos(math.radians(pose.yaw)) >= 0 else -1.0
                spec["props"](_Pen(c), sk, sk.H, fwd, _ground(sk))
        arr = _raster(paint)
    # BGRA premultiplied
    a = arr[..., 3]
    mask = (a > 110).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(mask)
    bbox = (xs.min() - PIN[0], ys.min() - PIN[1], xs.max() - PIN[0], ys.max() - PIN[1]) if len(xs) else None
    com = (float(xs.mean() - PIN[0]), float(ys.mean() - PIN[1])) if len(xs) else (0.0, 1.0)
    paper = _trace(mask, i, sag=2.2, amp=1.1, max_len=46.0)
    red = ink = None
    if i == 9:
        b, g, r = arr[..., 0].astype(int), arr[..., 1].astype(int), arr[..., 2].astype(int)
        mred = ((r > 150) & (g < 90) & (b < 90) & (a > 110)).astype(np.uint8) * 255
        mink = ((b > 150) & (r < 90) & (g < 90) & (a > 110)).astype(np.uint8) * 255
        red = _to_path(_trace(mred, 900, sag=1.8, amp=0.9, max_len=40.0), PIN)
        ink = _to_path(_trace(mink, 901, sag=1.2, amp=0.7, max_len=30.0, eps=0.9), PIN)
    tone = 0.90 + 0.10 * hash01(i, 77)
    return Doll(i, _to_path(paper, PIN), red, ink, com, bbox, tone)


@lru_cache(maxsize=1)
def dolls():
    return {i: _build(i) for i in range(1, 41)}
