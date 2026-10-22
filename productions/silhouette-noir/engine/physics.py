"""Deterministic secondary motion: verlet ropes/hoses/chains and driven pendulums.

Simulations run once per process at a fixed step from t_start, are cached, and are then
sampled at any time (linear interpolation between steps), so frames rendered in parallel
processes agree exactly and any frame can be rendered alone.

    hose = Rope(n=48, length=2600, a=lambda t: boat.hose_exit(t), b=lambda t: helmet_inlet(t),
                t0=-1.0, t1=16.0, gravity=(0, 60), drag=1.8, current=lambda t, x, y: (25, 0))
    pts = hose.points(t)                      # list of (x, y), a -> b
    draw.chain(L, pts, [9] * len(pts))       # or draw.ribbon(pts, widths)

    lamp = Pendulum(pivot=lambda t: hand(t), length=60, t0=0, t1=12, damping=1.5)
    ang = lamp.angle(t)                       # radians from straight down (+ = swung to +x)
"""
import math

import numpy as np


class Rope:
    """A rope of n nodes and total `length` (px), pinned at a(t) and optionally b(t).

    gravity: (gx, gy) px/s^2 (underwater: small). drag: velocity damping per second
    (0 = none, ~2 = thick water). current(t, x, y) -> (vx, vy): flow velocity the rope is
    dragged toward (wind, sea current). collide(x, y) -> y_max or None: nodes are kept
    above a floor (e.g. the seabed or deck). length_fn(t): rope length over time (paying
    out / reeling in). release(t) -> bool: when True, end b is let go (a cut hose).
    stiffness: 0..1 bending resistance (0 = string, 0.3 = hose)."""

    def __init__(self, n, length, a, b=None, t0=0.0, t1=10.0, dt=1.0 / 120.0, gravity=(0.0, 900.0),
                 drag=0.3, current=None, collide=None, length_fn=None, release=None, iters=14,
                 stiffness=0.0, init=None):
        self.n, self.length = n, float(length)
        self.a, self.b = a, b
        self.t0, self.t1, self.dt = t0, t1, dt
        self.gravity = np.array(gravity, np.float64)
        self.drag = drag
        self.current, self.collide = current, collide
        self.length_fn, self.release = length_fn, release
        self.iters, self.stiffness = iters, stiffness
        self.init = init
        self._frames = None

    def _rest(self, t):
        L = self.length_fn(t) if self.length_fn else self.length
        return L / (self.n - 1)

    def _simulate(self):
        n, dt = self.n, self.dt
        steps = int(math.ceil((self.t1 - self.t0) / dt)) + 2
        a0 = np.array(self.a(self.t0), np.float64)
        if self.init is not None:
            P = np.array(self.init(self.t0), np.float64)
        elif self.b is not None:
            b0 = np.array(self.b(self.t0), np.float64)
            # start as a sagging catenary-ish curve between the ends
            u = np.linspace(0, 1, n)[:, None]
            P = a0 * (1 - u) + b0 * u
            span = np.linalg.norm(b0 - a0)
            sag = max(0.0, (self.length - span)) * 0.5
            P[:, 1] += np.sin(np.pi * u[:, 0]) * sag * (1 if self.gravity[1] >= 0 else -1)
        else:
            g = self.gravity / (np.linalg.norm(self.gravity) + 1e-9)
            P = a0 + np.outer(np.arange(n) * self._rest(self.t0), g if g.any() else np.array([0, 1.0]))
        prev = P.copy()
        frames = np.empty((steps, n, 2), np.float64)
        released = False
        for k in range(steps):
            t = self.t0 + k * dt
            # verlet with drag toward the local current
            vel = (P - prev) / dt
            if self.current is not None:
                cur = np.array([self.current(t, x, y) for x, y in P])
            else:
                cur = 0.0
            acc = self.gravity - self.drag * (vel - cur)
            new = P + (vel * dt) + acc * dt * dt
            prev, P = P, new
            rest = self._rest(t)
            pa = np.array(self.a(t), np.float64)
            pin_b = self.b is not None and not released
            if pin_b and self.release is not None and self.release(t):
                released = True
                pin_b = False
            pb = np.array(self.b(t), np.float64) if pin_b else None
            inv = np.ones((n, 1))
            inv[0] = 0.0
            if pin_b:
                inv[-1] = 0.0
            for _ in range(self.iters):
                P[0] = pa
                if pin_b:
                    P[-1] = pb
                for parity in (0, 1):            # red-black Gauss-Seidel on the segments
                    i0 = np.arange(parity, n - 1, 2)
                    d = P[i0 + 1] - P[i0]
                    L = np.linalg.norm(d, axis=1)[:, None] + 1e-9
                    diff = (L - rest) / L
                    wa, wb = inv[i0], inv[i0 + 1]
                    sw = wa + wb
                    sw[sw == 0] = 1.0
                    P[i0] += d * diff * wa / sw
                    P[i0 + 1] -= d * diff * wb / sw
                if self.stiffness > 0 and n > 2:
                    # bending: weak "skip" constraints between nodes i and i+2 that only push
                    # apart (resist folding), 4-colored so no two pairs share a node
                    for grp in ((0, 1), (2, 3)):
                        i0 = np.array([i for i in range(n - 2) if i % 4 in grp], dtype=int)
                        if len(i0) == 0:
                            continue
                        d = P[i0 + 2] - P[i0]
                        L = np.linalg.norm(d, axis=1)[:, None] + 1e-9
                        diff = np.minimum((L - 2 * rest) / L, 0.0) * self.stiffness
                        wa, wb = inv[i0], inv[i0 + 2]
                        sw = wa + wb
                        sw[sw == 0] = 1.0
                        P[i0] += d * diff * wa / sw
                        P[i0 + 2] -= d * diff * wb / sw
                if self.collide is not None:
                    for i in range(n):
                        ym = self.collide(P[i, 0], P[i, 1])
                        if ym is not None and P[i, 1] > ym:
                            P[i, 1] = ym
                            prev[i, 0] = P[i, 0] - (P[i, 0] - prev[i, 0]) * 0.6   # friction
            P[0] = pa
            if pin_b:
                P[-1] = pb
            frames[k] = P
        self._frames = frames

    def points(self, t):
        """Node positions at time t (list of (x, y)), from end a to end b."""
        if self._frames is None:
            self._simulate()
        f = (min(max(t, self.t0), self.t1) - self.t0) / self.dt
        i = int(math.floor(f))
        i = min(max(i, 0), len(self._frames) - 2)
        u = f - i
        P = self._frames[i] * (1 - u) + self._frames[i + 1] * u
        return [tuple(p) for p in P]

    def tension(self, t):
        """Stretch ratio (current length / rest length): > 1.0 means taut."""
        pts = np.array(self.points(t))
        L = np.linalg.norm(pts[1:] - pts[:-1], axis=1).sum()
        return L / (self._rest(t) * (self.n - 1))


class Pendulum:
    """A pendulum hanging from pivot(t) (a hand, a hook, a boat): swings from the pivot's
    accelerations. angle(t) in radians from straight down (+ swings toward +x)."""

    def __init__(self, pivot, length, t0=0.0, t1=10.0, damping=1.2, gravity=900.0, theta0=0.0,
                 dt=1.0 / 240.0, kick=None):
        self.pivot, self.length = pivot, float(length)
        self.t0, self.t1, self.dt = t0, t1, dt
        self.damping, self.g = damping, gravity
        self.theta0 = theta0
        self.kick = kick              # kick(t) -> extra angular acceleration (rad/s^2)
        self._th = None

    def _simulate(self):
        dt = self.dt
        n = int(math.ceil((self.t1 - self.t0) / dt)) + 2
        th, om = self.theta0, 0.0
        out = np.empty(n)
        h = dt

        def pv(t):
            return np.array(self.pivot(t), np.float64)
        for k in range(n):
            t = self.t0 + k * dt
            acc = (pv(t + h) - 2 * pv(t) + pv(t - h)) / (h * h)       # pivot acceleration
            # angular acceleration from gravity and the pivot's acceleration
            alpha = -(self.g * math.sin(th) + acc[0] * math.cos(th) - acc[1] * math.sin(th)) / self.length
            alpha -= self.damping * om
            if self.kick is not None:
                alpha += self.kick(t)
            om += alpha * dt
            th += om * dt
            out[k] = th
        self._th = out

    def angle(self, t):
        if self._th is None:
            self._simulate()
        f = (min(max(t, self.t0), self.t1) - self.t0) / self.dt
        i = min(max(int(f), 0), len(self._th) - 2)
        u = f - i
        return self._th[i] * (1 - u) + self._th[i + 1] * u

    def bob(self, t):
        """World position of the pendulum's end."""
        th = self.angle(t)
        px, py = self.pivot(t)
        return px + math.sin(th) * self.length, py + math.cos(th) * self.length
