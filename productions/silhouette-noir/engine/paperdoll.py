"""Fluid cut-paper figures for the Saul Bass films: precise flat silhouettes animated on ones.

A Figure is a set of flat shapes (torso, head, hair, accessories) cut once, plus limb
proportions; limbs are drawn each frame as smooth tapered capsules between solved joints.
A Walker turns a speed curve into planted footfalls (feet never slide), swing arcs, pelvis
bob and stride phase, all precomputed at 240 Hz so any frame is a pure lookup. Springs give
hair, scarves and coat tails overlapping action from the body's motion.

World units are px, ground y = 0, y down, figures face +x (flip with facing=-1 when drawing).

    W = Walker(fig, x0=0, speed=[(t, px/s), ...], stride=300)
    st = W.state(t)                         # pelvis, feet, phase, speed
    pose = Pose(lean=4, arms={"near": ("ang", 30, 40)}, springs={"pony": W.spring("pony", t)})
    hand = fig.draw(ctx, st, pose, colors)  # returns joint positions (hands, head, ...)
"""
import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from . import bass
from .core import clamp, lerp

HZ = 240.0


def _smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def ik2(a, target, l1, l2, forward=1.0):
    """Two-bone IK from a to target: returns (mid joint, end). The bend points `forward`
    (+1: the middle joint goes toward +x, e.g. knees; -1: elbows behind)."""
    dx, dy = target[0] - a[0], target[1] - a[1]
    d = math.hypot(dx, dy)
    d = clamp(d, abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    ang = math.atan2(dy, dx)
    cb = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1.0, 1.0)
    best = None
    for s in (-1.0, 1.0):
        k = (a[0] + math.cos(ang + s * math.acos(cb)) * l1, a[1] + math.sin(ang + s * math.acos(cb)) * l1)
        # signed distance of the joint from the line a->target, toward `forward`
        score = (k[0] - lerp(a[0], target[0], 0.5)) * forward
        if best is None or score > best[0]:
            best = (score, k)
    end = (a[0] + math.cos(ang) * d, a[1] + math.sin(ang) * d)
    return best[1], end


def _rot(p, deg, o=(0.0, 0.0)):
    a = math.radians(deg)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * math.cos(a) - y * math.sin(a), o[1] + x * math.sin(a) + y * math.cos(a))


def _cut(pts, seed, amp=0.35, max_len=34.0):
    """A precise cut: long straight snips, barely any wobble."""
    return bass.scissor(pts, seed=seed, sag=0.6, amp=amp, max_len=max_len, corner=40.0)


def _ellipse(c, rx, ry, seed, n=56, angle=0.0):
    return _cut(bass.draw.ellipse_pts(c, rx, ry, n=n, angle=angle), seed, max_len=22.0)


# ----------------------------------------------------------------------------- figures
@dataclass
class Figure:
    """Proportions (px) and flat parts of one character. Local frame of the upper body:
    origin at the pelvis, y up is negative, facing +x."""
    name: str
    thigh: float
    shin: float
    ankle: float                 # ankle height above the sole
    upper: float
    fore: float
    leg_w: tuple                 # (hip, knee, ankle) widths
    arm_w: tuple                 # (shoulder, elbow, wrist) widths
    hand_r: float
    shoulder: tuple              # pin, pelvis frame
    neck: tuple                  # head pivot, pelvis frame
    torso: list                  # [(polygon, color key)], pelvis frame, drawn between the limbs
    head: list                   # [(polygon, color key)], pelvis frame, turn with the head
    hair: list = field(default_factory=list)      # [(polygon, color, pin, spring name)], pelvis frame
    front: list = field(default_factory=list)     # drawn over the near arm (scarf wrap, ...)
    foot: list = None            # boot polygon, ankle at (0, 0), toe toward +x, sole at y = ankle
    eye: tuple = None            # (centre, rx, ry), pelvis frame (in the head)

    @property
    def leg(self):
        return self.thigh + self.shin + self.ankle

    def draw(self, ctx, st, pose, colors, facing=1):
        """Draw at walker state st (pelvis, feet) in world px. Returns joint positions."""
        P = st["pelvis"]
        crouch = pose.crouch
        P = (P[0], P[1] + crouch)
        lean = pose.lean
        ink = colors["ink"]
        out = {}

        def W(p):            # pelvis frame -> world (lean about the pelvis, facing flip)
            q = _rot((p[0], p[1]), lean)
            return (P[0] + facing * q[0], P[1] + q[1])

        def place(c):
            c.translate(*P)
            c.scale(facing, 1.0)
            c.rotate(math.radians(lean))

        # legs (far first), drawn in world space with IK from the hip pins to the ankles
        legs = {}
        for side in ("far", "near"):
            foot = st["feet"][side]
            hip = W((0.0, -4.0))
            ank = (foot[0], foot[1] - self.ankle)
            knee, ank = ik2(hip, ank, self.thigh, self.shin, forward=facing)
            legs[side] = (hip, knee, ank, foot[2])
        far_tone = colors.get("far", ink)

        def draw_leg(side, rgb):
            hip, knee, ank, pitch = legs[side]
            w0, w1, w2 = self.leg_w
            bass.fill_polys(ctx, [bass.capsule_pts(hip, knee, w0 / 2, w1 / 2, cap=10), bass.capsule_pts(knee, ank, w1 / 2, w2 / 2, cap=10)], rgb)
            ctx.save()
            ctx.translate(*ank)
            ctx.scale(facing, 1.0)
            ctx.rotate(math.radians(-pitch))
            bass.fill_polys(ctx, [self.foot], rgb)
            ctx.restore()
            out["knee_" + side] = knee
            out["ankle_" + side] = ank

        def arm_joints(side):
            spec = pose.arms.get(side, ("ang", 0.0, 0.0))
            sh = W(self.shoulder)
            if spec[0] == "ik":
                el, wr = ik2(sh, spec[1], self.upper, self.fore, forward=-facing)
            else:
                a1 = spec[1] + lean
                a2 = a1 + spec[2]
                el = (sh[0] + facing * math.sin(math.radians(a1)) * self.upper, sh[1] + math.cos(math.radians(a1)) * self.upper)
                wr = (el[0] + facing * math.sin(math.radians(a2)) * self.fore, el[1] + math.cos(math.radians(a2)) * self.fore)
            return sh, el, wr

        def draw_arm(side, rgb):
            sh, el, wr = arm_joints(side)
            w0, w1, w2 = self.arm_w
            d = math.hypot(wr[0] - el[0], wr[1] - el[1]) or 1.0
            hc = (wr[0] + (wr[0] - el[0]) / d * self.hand_r * 0.55, wr[1] + (wr[1] - el[1]) / d * self.hand_r * 0.55)
            bass.fill_polys(ctx, [bass.capsule_pts(sh, el, w0 / 2, w1 / 2, cap=10), bass.capsule_pts(el, wr, w1 / 2, w2 / 2, cap=10),
                                  bass.draw.circle_pts(hc, self.hand_r, n=24)], rgb)
            out["hand_" + side] = hc
            out["elbow_" + side] = el
            hold = pose.hold.get(side)
            if hold is not None:
                hold(ctx, hc, math.degrees(math.atan2(wr[1] - el[1], wr[0] - el[0])))

        draw_arm("far", far_tone)
        draw_leg("far", far_tone)
        draw_leg("near", ink)
        # torso, head, hair
        ctx.save()
        place(ctx)
        for poly, key in self.torso:
            bass.fill_polys(ctx, [poly], colors[key])
        ctx.save()
        ctx.translate(*self.neck)
        ctx.rotate(math.radians(-pose.head))
        ctx.translate(-self.neck[0], -self.neck[1])
        for poly, color, pin, spring in self.hair:
            ctx.save()
            ctx.translate(*pin)
            ctx.rotate(math.radians(pose.springs.get(spring, 0.0)))
            ctx.translate(-pin[0], -pin[1])
            bass.fill_polys(ctx, [poly], colors[color])
            ctx.restore()
        for poly, key in self.head:
            bass.fill_polys(ctx, [poly], colors[key])
        if self.eye is not None and pose.eye > 0.02:
            (ex, ey), rx, ry = self.eye
            bass.fill_polys(ctx, [bass.draw.ellipse_pts((ex + pose.gaze * rx * 0.5, ey), rx, ry * pose.eye, n=20)],
                            colors.get("eye", bass.PAPER))
        ctx.restore()
        for poly, color, pin, spring in [h for h in self.front]:
            ctx.save()
            ctx.translate(*pin)
            ctx.rotate(math.radians(pose.springs.get(spring, 0.0)))
            ctx.translate(-pin[0], -pin[1])
            bass.fill_polys(ctx, [poly], colors[color])
            ctx.restore()
        ctx.restore()
        draw_arm("near", ink)
        out["head"] = W((self.neck[0] + 10.0, self.neck[1] - 60.0))
        out["pelvis"] = P
        return out


@dataclass
class Pose:
    lean: float = 0.0
    head: float = 0.0            # + tilts the face up
    crouch: float = 0.0          # px the pelvis sinks (knees bend to keep the feet planted)
    arms: dict = field(default_factory=dict)      # side -> ("ang", sh, el) | ("ik", (x, y))
    hold: dict = field(default_factory=dict)      # side -> fn(ctx, hand_xy, forearm_deg)
    springs: dict = field(default_factory=dict)   # name -> degrees
    eye: float = 1.0             # 0 = closed
    gaze: float = 0.0            # -1..1 along x


def girl(red, seed=0):
    """THE LANTERN's girl, about nine: big round head, ponytail with a bow, A-line dress,
    red scarf. About 640 px tall."""
    s = seed * 100
    torso = [
        (_cut([(-30, -246), (34, -246), (48, -190), (66, -60), (96, 104), (-92, 104), (-62, -60), (-42, -190)], s + 1), "ink"),
        (_cut([(-11, -262), (15, -262), (15, -240), (-11, -240)], s + 2), "ink"),
    ]
    head = [(_ellipse((10, -322), 60, 66, s + 3), "ink")]
    hair = [
        (_cut([(-44, -352), (-62, -340), (-96, -298), (-110, -246), (-98, -214), (-86, -248), (-66, -296), (-44, -324)],
              s + 4), "ink", (-46, -346), "pony"),
        (_cut([(-50, -366), (-30, -378), (-32, -348), (-50, -352), (-68, -340), (-66, -370)], s + 5), "red", (-46, -346), "pony"),
    ]
    front = [
        (_cut([(-40, -270), (48, -270), (50, -240), (-42, -238)], s + 6), "red", (0, 0), None),
        (_cut([(-30, -262), (-92, -270), (-162, -256), (-186, -238), (-146, -238), (-170, -214), (-100, -226),
               (-30, -236)], s + 7), "red", (-30, -250), "scarf"),
    ]
    foot = _cut([(-14, -10), (12, -10), (18, 6), (40, 10), (42, 22), (-16, 22)], s + 8)
    return Figure("girl", thigh=128.0, shin=120.0, ankle=22.0, upper=104.0, fore=96.0,
                  leg_w=(34.0, 27.0, 22.0), arm_w=(25.0, 21.0, 17.0), hand_r=15.0,
                  shoulder=(2.0, -232.0), neck=(6.0, -256.0), torso=torso, head=head, hair=hair, front=front,
                  foot=foot, eye=((44.0, -330.0), 8.0, 10.0))


# ----------------------------------------------------------------------------- walking
class Walker:
    """Footfalls from a speed curve. speed: [(t, px/s), ...] (linear between keys).
    stride(v) / duty(v) / lift(v) blend walk -> run by speed."""

    def __init__(self, fig, x0=0.0, speed=((0.0, 0.0),), t0=-2.0, t1=40.0, walk=(300.0, 0.62, 30.0),
                 run=(560.0, 0.36, 70.0), v_walk=230.0, v_run=620.0, hip_drop=0.035):
        self.fig = fig
        self.keys = list(speed)
        self.t0, self.t1 = t0, t1
        self.walk, self.run = walk, run
        self.v_walk, self.v_run = v_walk, v_run
        self.hip_drop = hip_drop
        self.x0 = x0
        self._sim()

    def speed(self, t):
        K = self.keys
        if t <= K[0][0]:
            return K[0][1]
        for (a, va), (b, vb) in zip(K, K[1:]):
            if t <= b:
                return lerp(va, vb, (t - a) / max(b - a, 1e-6))
        return K[-1][1]

    def _gait(self, v):
        r = _smooth((v - self.v_walk) / (self.v_run - self.v_walk))
        return tuple(lerp(a, b, r) for a, b in zip(self.walk, self.run)), r

    def _sim(self):
        n = int((self.t1 - self.t0) * HZ) + 2
        dt = 1.0 / HZ
        x = self.x0
        ph = 0.0
        X = np.zeros(n)
        PH = np.zeros(n)
        V = np.zeros(n)
        R = np.zeros(n)
        for i in range(n):
            t = self.t0 + i * dt
            v = self.speed(t)
            (stride, duty, lift), r = self._gait(v)
            X[i], PH[i], V[i], R[i] = x, ph, v, r
            rate = v / stride
            # finishing a step when stopping: a foot in the air always lands
            q = ph % 1.0
            in_swing = any(((q + o) % 1.0) >= duty for o in (0.0, 0.5))
            if v < 25.0 and in_swing:
                rate = max(rate, 1.6)
            x += v * dt
            ph += rate * dt
        self.X, self.PH, self.V, self.R = X, PH, V, R
        # footfalls: each foot plants when its phase enters stance; it lands half a stance
        # ahead of the pelvis (scaled by speed, so a stopping step lands beside the other)
        self.plants = {}
        for side, off in (("near", 0.0), ("far", 0.5)):
            ev = []
            prev = None
            for i in range(n):
                q = (PH[i] + off) % 1.0
                (stride, duty, lift), r = self._gait(V[i])
                st = q < duty
                if prev is None or (st and not prev):
                    k = clamp(V[i] / self.v_walk, 0.0, 1.0)
                    fx = X[i] + stride * duty * 0.5 * k + (8.0 if side == "near" else -8.0) * (1 - k)
                    ev.append((i, fx))
                prev = st
            self.plants[side] = ev

    def _i(self, t):
        return clamp((t - self.t0) * HZ, 0.0, len(self.X) - 1.001)

    def _at(self, arr, t):
        f = self._i(t)
        a = int(f)
        return lerp(arr[a], arr[a + 1], f - a)

    def x(self, t):
        return self._at(self.X, t)

    def phase(self, t):
        return self._at(self.PH, t)

    def foot(self, side, t):
        """(x, y, pitch deg) of the sole: planted, or swinging between two plants."""
        ev = self.plants[side]
        f = self._i(t)
        # the last plant at or before f, and the next one
        lo, hi = 0, len(ev) - 1
        while lo < hi:
            m = (lo + hi + 1) // 2
            if ev[m][0] <= f:
                lo = m
            else:
                hi = m - 1
        i0, x0 = ev[lo]
        off = 0.0 if side == "near" else 0.5
        v = self._at(self.V, t)
        (stride, duty, lift), r = self._gait(v)
        q = (self._at(self.PH, t) + off) % 1.0
        if q < duty or lo + 1 >= len(ev) or self._at(self.V, t) < 1.0 and q < duty:
            return (x0, 0.0, 0.0)
        i1, x1 = ev[lo + 1]
        s = clamp((q - duty) / (1.0 - duty))
        e = _smooth(s)
        k = clamp(v / self.v_walk, 0.25, 1.6)
        y = -lift * k * math.sin(math.pi * s) ** 0.9
        pitch = 28.0 * math.sin(math.pi * clamp(s * 1.6)) * (1 - s) - 12.0 * clamp((s - 0.75) / 0.25) * k
        return (lerp(x0, x1, e), y, pitch)

    def state(self, t):
        v = self._at(self.V, t)
        (stride, duty, lift), r = self._gait(v)
        ph = self._at(self.PH, t)
        k = clamp(v / self.v_walk, 0.0, 1.5)
        # pelvis: lowest at double support, highest at mid stance (walk); highest in flight (run)
        bob_w = -9.0 * k * math.cos(4 * math.pi * (ph - duty * 0.5)) * (1 - r)
        bob_r = -16.0 * math.cos(4 * math.pi * (ph - 0.15)) * r
        L = self.fig.leg
        y = -L * (1.0 - self.hip_drop) + bob_w + bob_r - 6.0 * r
        feet = {s: self.foot(s, t) for s in ("near", "far")}
        return dict(pelvis=(self.x(t), y), feet=feet, phase=ph, speed=v, run=r, stride=stride)


class Spring:
    """A damped angular spring (deg) driven by a point's motion: lags behind when the point
    accelerates (hair, scarf, coat tail). drive(t) -> (x, y); rest(t) -> deg."""

    def __init__(self, drive, rest=lambda t: 0.0, t0=-2.0, t1=40.0, freq=2.2, damping=0.35, gain=0.05,
                 vel_gain=0.0, lo=-80.0, hi=80.0):
        n = int((t1 - t0) * HZ) + 2
        dt = 1.0 / HZ
        w = 2 * math.pi * freq
        th, om = rest(t0), 0.0
        out = np.zeros(n)
        prev = [drive(t0 - 2 * dt), drive(t0 - dt)]
        for i in range(n):
            t = t0 + i * dt
            p = drive(t)
            vx = (p[0] - prev[1][0]) / dt
            ax = (p[0] - 2 * prev[1][0] + prev[0][0]) / (dt * dt)
            target = rest(t) + vel_gain * vx
            alpha = -w * w * (th - target) - 2 * damping * w * om + gain * ax
            om += alpha * dt
            th += om * dt
            th = clamp(th, lo, hi)
            out[i] = th
            prev = [prev[1], p]
        self.t0, self.out = t0, out

    def __call__(self, t):
        f = clamp((t - self.t0) * HZ, 0.0, len(self.out) - 1.001)
        a = int(f)
        return lerp(self.out[a], self.out[a + 1], f - a)
