"""Animated creature silhouettes (Silhouette Noir: Saul Bass x Limbo x Inside).

    Wolf        the huge black wolf of RED (quadruped rig, IK legs, walk/trot/gallop, acting)
    Spider      "Grandmother" (eight 3-segment IK legs, descend, walk, stab, recoil, die)
    FishSchool  a swirling, closed-form school that parts around obstacles (SALVAGE)
    Crow / CrowFlock   perched crows, take-off, flapping flocks (RED)
    Cat         window cat: sit with tail swish, walk the sill, head turn (SHADOW PLAY)
    Moths       erratic moths around a lamp (lit when close)

Conventions (same as engine.figure):
  * World units are frame px at zoom 1, y DOWN. Draw on a layer context: `draw(f, t, ctx)`.
  * Rigs are pseudo-3D: a body-local frame (forward f, up u, left l) projected with a yaw
    (0 = facing screen right, 180 = facing left, 90 = facing the camera, -90 = back to it).
    Sagittal limb angles are measured from straight DOWN toward FORWARD.
  * Everything is a pure function of t, the timeline you build and integer seeds.
  * Limbo eyes: two small bright dots on the silhouette plus a soft halo on f.emit().

Actor timelines (Wolf, Spider, Cat): chain actions; each starts when the previous ends.
`.at(t)` makes the next action start at absolute time t (the current one holds until then).
Consecutive locomotion calls (walk/trot/gallop/stalk) form one run with continuous speed,
gait blending and planted paws. Non-locomotion actions crossfade in (~0.25 s). Head acts
(snarl, howl, look, growl) layer over the last body action (stand, sit, crouch...).
`overlay(name, t0, dur, ...)` adds a head act at an absolute time over anything (also runs).
`timeline()` lists the resolved (t0, t1, kind) of every action; `.end` is the end time.
"""
import bisect
import math

import numpy as np

from . import draw
from .core import clamp, lerp, lerp_angle, hash01, noise1, fbm1

D2R = math.pi / 180.0
_INF = float("inf")


# ============================================================================= small math
def _ss(e0, e1, x):
    """smoothstep of x from e0 to e1 (works for e1 < e0 too)."""
    if e1 == e0:
        return 1.0 if x >= e1 else 0.0
    t = (x - e0) / (e1 - e0)
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return t * t * (3.0 - 2.0 * t)


def _s01(t):
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return t * t * (3.0 - 2.0 * t)


def _down(a):
    """Sagittal unit vector (forward, up) for an angle in degrees from straight DOWN toward FORWARD."""
    r = a * D2R
    return math.sin(r), -math.cos(r)


def _ang_down(v):
    """Angle of the (forward, up) vector v from straight down toward forward, degrees."""
    return math.atan2(v[0], -v[1]) / D2R


def _ik2(a, b, L1, L2, side):
    """2-bone IK in a plane: root a, target b, bone lengths L1, L2. side=+1 puts the middle
    joint to the LEFT of a->b (that is FORWARD for a leg hanging down in (forward, up)
    coordinates), side=-1 to the right. Returns (mid, end): end is b when reachable, otherwise
    the leg straightens toward b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d < 1e-9:
        dx, dy, d = 0.0, -1.0, 1.0
    reach = L1 + L2
    if d >= reach * 0.9999:
        ux, uy = dx / d, dy / d
        # keep a hint of bend so the joint never pops
        k = 0.9999
        ca = (L1 * L1 + (reach * k) ** 2 - L2 * L2) / (2 * L1 * reach * k)
        A = math.acos(clamp(ca, -1.0, 1.0))
        base = math.atan2(uy, ux) + side * A
        mid = (a[0] + L1 * math.cos(base), a[1] + L1 * math.sin(base))
        return mid, (a[0] + ux * reach * k, a[1] + uy * reach * k)
    lo = abs(L1 - L2) + 1e-6
    dd = d if d > lo else lo
    ca = (L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd)
    A = math.acos(clamp(ca, -1.0, 1.0))
    base = math.atan2(dy, dx) + side * A
    mid = (a[0] + L1 * math.cos(base), a[1] + L1 * math.sin(base))
    if d < lo:
        ex, ey = b[0] - mid[0], b[1] - mid[1]
        e = math.hypot(ex, ey) or 1.0
        return mid, (mid[0] + ex / e * L2, mid[1] + ey / e * L2)
    return mid, b



def _reach_distal(G, J, d, alpha, R):
    """Wrist/hock position for a distal bone of length d hanging from it to the paw joint J
    (bone direction _down(alpha) from wrist to J). If the girdle joint G cannot reach it with
    a 2-bone chain of total length R, rotate the distal bone about J (the paw stays planted,
    the heel lifts) just enough. Returns (wrist, alpha_used)."""
    dx, dy = _down(alpha)
    W = (J[0] - dx * d, J[1] - dy * d)
    Rm = R * 0.995
    gx, gy = G[0] - W[0], G[1] - W[1]
    if gx * gx + gy * gy <= Rm * Rm:
        return W, alpha
    vx, vy = G[0] - J[0], G[1] - J[1]
    D = math.hypot(vx, vy) or 1e-6
    base = math.atan2(vy, vx)
    if D >= Rm + d:
        th = base
    else:
        c = clamp((D * D + d * d - Rm * Rm) / (2 * d * D), -1.0, 1.0)
        A = math.acos(c)
        th0 = math.atan2(-dy, -dx)          # current direction J -> W
        c1, c2 = base + A, base - A
        e1 = abs((c1 - th0 + math.pi) % (2 * math.pi) - math.pi)
        e2 = abs((c2 - th0 + math.pi) % (2 * math.pi) - math.pi)
        th = c1 if e1 < e2 else c2
    W = (J[0] + math.cos(th) * d, J[1] + math.sin(th) * d)
    return W, _ang_down((J[0] - W[0], J[1] - W[1]))


def _rot(p, c, s):
    """Rotate (x, y) by an angle given as (cos, sin) - counter-clockwise in a y-UP frame."""
    return p[0] * c - p[1] * s, p[0] * s + p[1] * c


def _area2(pts):
    s = 0.0
    x0, y0 = pts[-1]
    for x1, y1 in pts:
        s += x0 * y1 - x1 * y0
        x0, y0 = x1, y1
    return s


def _poly(ctx, pts):
    """Closed polygon sub-path, oriented like cairo arcs so many shapes can share one
    non-zero fill without cancelling each other."""
    if len(pts) < 3:
        return
    if _area2(pts) < 0:
        pts = pts[::-1]
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def _smooth(ctx, pts, tension=0.5):
    """Closed Catmull-Rom outline, oriented for a shared non-zero fill."""
    if len(pts) < 3:
        return
    if _area2(pts) < 0:
        pts = pts[::-1]
    draw.smooth(ctx, pts, close=True, tension=tension)


def _bez2(p0, p1, p2, s):
    a = (1 - s) * (1 - s)
    b = 2 * s * (1 - s)
    c = s * s
    return (a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1])


def _seg_dist2(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    L = vx * vx + vy * vy
    u = clamp((wx * vx + wy * vy) / L, 0.0, 1.0) if L > 0 else 0.0
    dx, dy = wx - vx * u, wy - vy * u
    return dx * dx + dy * dy


def _tufts(pts, n, seed, length, width, rake, t=0.0, wob=0.12, side=1.0, jag=0.45,
           u0=0.0, u1=None, lens=None):
    """Jagged fur tufts along a LOCAL (forward, up) polyline. Each tuft is a triangle whose
    base sits on the line and whose tip leans out (side=+1: left of the line direction,
    which is 'up' for a line running forward) and along it (rake > 0 = toward the end of
    the line). Deterministic per (seed, i); tips wobble gently with t.
    length/width may be callables of the normalized position v in 0..1."""
    m = len(pts) - 1
    if m < 1 or n <= 0:
        return []
    u1 = m if u1 is None else u1
    out = []
    for i in range(n):
        h1, h2, h3 = hash01(seed, i, 1), hash01(seed, i, 2), hash01(seed, i, 3)
        v = (i + 0.2 + 0.6 * h1) / n
        u = u0 + (u1 - u0) * v
        k = min(int(u), m - 1)
        fr = u - k
        a, b = pts[k], pts[k + 1]
        px, py = a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1.0
        tx, ty = tx / tl, ty / tl
        nx, ny = -ty * side, tx * side
        L = (length(v) if callable(length) else length) * (1.0 - jag + 2 * jag * h2)
        if lens is not None:
            L *= lens
        wdt = (width(v) if callable(width) else width) * (0.7 + 0.6 * h3)
        rk = rake + wob * noise1(t * 1.3 + i * 0.71, seed + 17)
        ex, ey = px + nx * L + tx * rk * L, py + ny * L + ty * rk * L
        out.append(((px - tx * wdt * 0.5, py - ty * wdt * 0.5), (ex, ey),
                    (px + tx * wdt * 0.5, py + ty * wdt * 0.5)))
    return out


def _polyline_resample(pts, n):
    """Resample an open polyline to n points evenly by arc length."""
    return draw.resample(pts, n, closed=False)


# ============================================================================= generic actor
class _Clip:
    """One action on an actor timeline. Subclasses implement pose(t) and set t0, t1, fade,
    end_state. `overlay` clips modify the pose of the body clip they sit on."""
    overlay = False
    kind = "clip"

    def __init__(self, A, t0, state, dur=1.0, fade=0.25, base=None, **kw):
        self.A = A
        self.t0 = float(t0)
        self.dur = max(0.0, float(dur if dur is not None else 1.0))
        self.t1 = self.t0 + self.dur
        self.fade = fade
        self.start = state
        self.base = base
        self.kw = kw
        self.end_state = state

    def pose(self, t):
        raise NotImplementedError


class _Actor:
    """Timeline machinery shared by Wolf, Cat and Spider: chained actions, absolute .at(),
    per-action crossfades and absolute-time overlays."""

    CLIPS = {}            # kind -> clip class (filled by subclasses)
    LOCO = ()             # kinds that merge into one locomotion run

    def __init__(self):
        self._specs = []
        self._overlays = []
        self._plan = None

    # ----------------------------------------------------------- building
    def _add(self, kind, **kw):
        self._specs.append((kind, kw))
        self._plan = None
        return self

    def at(self, t):
        """Start the next action at absolute time t (the current action holds until then)."""
        self._specs.append(("@", dict(t=float(t))))
        self._plan = None
        return self

    def overlay(self, name, t0, dur=1.0, **kw):
        """Layer a head/limb act (snarl, howl, look, growl, blink... or a stab for the spider)
        over whatever the body is doing, at absolute time t0."""
        self._overlays.append((name, float(t0), float(dur), kw))
        self._plan = None
        return self

    def do(self, name, dur=None, **kw):
        """Generic chained action by name, e.g. w.do('snarl', 2.0)."""
        fn = getattr(self, name, None)
        if fn is None or name.startswith("_"):
            raise ValueError("unknown action %r" % name)
        if dur is not None:
            kw["dur"] = dur
        return fn(**kw)

    def _initial_state(self):
        raise NotImplementedError

    def _make_run(self, t0, state, segs):
        raise NotImplementedError

    def _build(self):
        clips = []
        state = self._initial_state()
        t = 0.0
        pend = None
        last_body = None
        specs = self._specs
        i = 0
        while i < len(specs):
            kind, kw = specs[i]
            if kind == "@":
                pend = kw["t"]
                i += 1
                continue
            t0 = t if pend is None else max(t, pend)
            pend = None
            if kind in self.LOCO:
                segs = [dict(kw, kind=kind)]
                j = i + 1
                while j < len(specs) and specs[j][0] in self.LOCO:
                    segs.append(dict(specs[j][1], kind=specs[j][0]))
                    j += 1
                pre = self._pre_run(t0, state, segs, last_body)
                for c in pre:
                    clips.append(c)
                    last_body = c
                    state = c.end_state
                    t0 = c.t1
                c = self._make_run(t0, state, segs)
                i = j
            else:
                cls = self.CLIPS[kind]
                c = cls(self, t0, state, base=last_body, **kw)
                i += 1
            clips.append(c)
            if not c.overlay:
                last_body = c
            state = c.end_state
            t = c.t1
        if not clips:
            c = self.CLIPS["stand"](self, 0.0, state, dur=0.0)
            clips.append(c)
        ovs = []
        for name, t0, dur, kw in self._overlays:
            cls = self.CLIPS[name]
            ovs.append(cls(self, t0, None, dur=dur, base=None, **kw))
        self._plan = (clips, [c.t0 for c in clips], ovs)

    def _pre_run(self, t0, state, segs, last_body):
        return []

    def _get_plan(self):
        if self._plan is None:
            self._build()
        return self._plan

    def timeline(self):
        """[(t0, t1, kind), ...] of the resolved actions (overlays not included)."""
        clips = self._get_plan()[0]
        return [(c.t0, c.t1, c.kind) for c in clips]

    @property
    def end(self):
        clips = self._get_plan()[0]
        return clips[-1].t1 if clips else 0.0

    def state(self, t):
        """The blended pose (a dict) at time t."""
        clips, starts, ovs = self._get_plan()
        k = bisect.bisect_right(starts, t) - 1
        if k < 0:
            k = 0
        c = clips[k]
        P = c.pose(t)
        if k > 0 and c.fade > 0 and t < c.t0 + c.fade:
            Pp = clips[k - 1].pose(t)
            w = _s01((t - c.t0) / c.fade)
            P = self._blend(Pp, P, w)
        for ov in ovs:
            if ov.t0 - ov.fade_in <= t <= ov.t1 + ov.fade_out:
                P = ov.apply(P, t)
        return P

    def _blend(self, a, b, w):
        raise NotImplementedError


def _env(t, t0, t1, fin, fout):
    """0..1 envelope: eases in over fin after t0, out over fout before t1."""
    if t <= t0 or t >= t1:
        return 0.0
    a = _s01((t - t0) / fin) if fin > 0 else 1.0
    b = _s01((t1 - t) / fout) if fout > 0 else 1.0
    return min(a, b)


# ============================================================================= quadruped engine
LEGS = ("LH", "LF", "RH", "RF")
_FRONT = {"LF": True, "RF": True, "LH": False, "RH": False}
_LEFT = {"LF": 1.0, "LH": 1.0, "RF": -1.0, "RH": -1.0}

# touchdown phases (fraction of a stride) per leg, in LEGS order. Values are unwrapped so
# blending walk -> trot -> gallop shifts each foot continuously.
_TAU = {
    "walk": (0.0, 0.25, 0.5, 0.75),          # lateral sequence: LH LF RH RF
    "trot": (0.0, 0.5, 0.5, 1.0),            # diagonal pairs: LH+RF, RH+LF
    "gallop": (0.0, 0.55, 0.09, 1.44),       # rotary: LH RH RF LF, two suspensions
}

_GAIT_NUM = ("v", "L", "duty", "lift_f", "lift_h", "bob", "flex", "nod", "cmin", "tsway",
             "swk_f", "swk_h", "over", "lp_f", "lp_h", "brake_L")

_POSE_KEYS = ("hf", "hh", "chord", "arch", "neck", "head", "hturn", "jaw", "snarl", "ears",
              "ruff", "tail", "tcurve", "tsway", "tlift", "wind", "eopen", "eglow", "bend",
              "sit", "lie", "breath", "speed", "fold_f", "fold_h", "grey", "headnod",
              "tremble", "puff", "roll")


def _blend_pose(a, b, w, S):
    """Blend two quadruped poses. Planted paws that must move take a quick stepped arc
    (staggered hind -> fore) instead of sliding."""
    if w <= 0.0:
        return a
    if w >= 1.0:
        return b
    P = {}
    for k in _POSE_KEYS:
        va, vb = a.get(k, 0.0), b.get(k, 0.0)
        P[k] = va + (vb - va) * w
    P["x"] = a["x"] + (b["x"] - a["x"]) * w
    P["yaw"] = lerp_angle(a["yaw"], b["yaw"], w)
    P["t"] = b["t"]
    P["phase"] = b.get("phase", 0.0)
    legs = {}
    for i, k in enumerate(LEGS):
        la, lb = a["legs"][k], b["legs"][k]
        d = math.hypot(lb[0] - la[0], lb[1] - la[1]) + abs(lb[2] - la[2]) * 0.5
        if d > 0.025 * S and la[6] > 0.5 and lb[6] > 0.5:
            dl = (0.0, 0.18, 0.08, 0.28)[i]
            u = _s01((w - dl) / 0.62)
            lift = min(0.07 * S, 0.45 * d) * math.sin(math.pi * u)
            legs[k] = [la[0] + (lb[0] - la[0]) * u, la[1] + (lb[1] - la[1]) * u - lift,
                       la[2] + (lb[2] - la[2]) * u,
                       la[3] + (lb[3] - la[3]) * u + 25.0 * math.sin(math.pi * u),
                       la[4] + (lb[4] - la[4]) * u + 0.35 * math.sin(math.pi * u),
                       la[5] + (lb[5] - la[5]) * u, 1.0 if u in (0.0, 1.0) else 0.0]
        else:
            legs[k] = [x + (y - x) * w for x, y in zip(la, lb)]
    P["legs"] = legs
    return P


def _fac(yaw):
    return 1.0 if math.cos(yaw * D2R) >= 0 else -1.0


def _step_leg(la, lb, u, S, lift=0.07):
    """A paw stepping from la to lb as u goes 0..1: a quick arc, the paw peeling off."""
    if u <= 0.0:
        out = list(la)
        out[6] = 1.0
        return out
    if u >= 1.0:
        out = list(lb)
        out[6] = 1.0
        return out
    us = u * u * (3 - 2 * u)
    d = math.hypot(lb[0] - la[0], lb[1] - la[1])
    if d < 0.02 * S:            # nothing to step over: just re-angle the paw in place
        return [la[0] + (lb[0] - la[0]) * us, la[1] + (lb[1] - la[1]) * us,
                la[2] + (lb[2] - la[2]) * us, la[3] + (lb[3] - la[3]) * us,
                la[4] + (lb[4] - la[4]) * us, la[5] + (lb[5] - la[5]) * us, 1.0]
    sp = math.sin(math.pi * u)
    h = min(lift * S, 0.5 * d + 0.015 * S) * sp
    return [la[0] + (lb[0] - la[0]) * us, la[1] + (lb[1] - la[1]) * us - h,
            la[2] + (lb[2] - la[2]) * us,
            la[3] + (lb[3] - la[3]) * us + 28.0 * sp,
            la[4] + (lb[4] - la[4]) * us + 0.3 * sp,
            la[5] + (lb[5] - la[5]) * us, 0.0]


def _girdles(A, P):
    """World (x, y) of the withers and of the sacrum for a pose (arch ignored)."""
    S = A.S
    half = 0.5 * P["chord"] * A.PR["chord"] * S
    c = math.cos(P["yaw"] * D2R)
    xw, xs = P["x"] + c * half, P["x"] - c * half
    return (xw, A.ground(xw) - P["hf"] * S), (xs, A.ground(xs) - P["hh"] * S)


def _keyframes(t, frames, key, default):
    """Smoothstep interpolation of one key through [(t, {key: value}), ...] (sorted)."""
    prev_t, prev_v = None, None
    for tk, d in frames:
        v = d.get(key, default)
        if t <= tk:
            if prev_t is None:
                return v
            return prev_v + (v - prev_v) * _s01((t - prev_t) / max(tk - prev_t, 1e-6))
        prev_t, prev_v = tk, v
    return prev_v


class _QPosture(_Clip):
    """Body postures (stand, sit, lie, crouch): an eased transition from the start pose into
    the posture over t_in, with paws that step where they must, then a living hold."""
    kind = "posture"
    POSTURE = "stand"
    T_IN = 0.8
    BREATH_AMP = 1.0
    BREATH_PER = None

    def __init__(self, A, t0, state, dur=1.0, fade=0.25, base=None, **kw):
        _Clip.__init__(self, A, t0, state, dur, fade, base, **kw)
        self.yaw = state["yaw"]
        self.fac = _fac(self.yaw)
        self.x0 = state["x"]
        self.p0 = dict(A.STAND)
        self.p0.update(state.get("pose") or {})
        self.legs0 = {k: list(v) for k, v in state["legs"].items()}
        self.post0 = state.get("posture", "stand")
        self.t_in = min(self._t_in(), max(0.2, self.dur))
        K, x1, legs1, sched, stage = self._targets()
        self.T = dict(A.STAND)
        self.T.update(K)
        self.x1, self.legs1, self.sched, self.stage = x1, legs1, sched, stage
        self.end_state = dict(x=x1, yaw=self.yaw, legs={k: list(v) for k, v in legs1.items()},
                              pose=dict(self.T), posture=self.POSTURE)

    def _t_in(self):
        return self.T_IN

    def _targets(self):
        raise NotImplementedError

    def _live(self, P, t, u):
        pass

    STEP_LIFT = 0.07

    def pose(self, t):
        A, S = self.A, self.A.S
        u = clamp((t - self.t0) / self.t_in) if self.t_in > 0 else 1.0
        sx = self.stage.get("x", (0.1, 0.9))
        x = self.x0 + (self.x1 - self.x0) * _ss(sx[0], sx[1], u)
        P = A._base_params(x, self.yaw, t)
        p0, T, stage = self.p0, self.T, self.stage
        for key in _POSE_KEYS:
            a, b = p0.get(key, 0.0), T.get(key, 0.0)
            if a == b:
                P[key] = b
            else:
                s0, s1 = stage.get(key, (0.0, 1.0))
                P[key] = a + (b - a) * _ss(s0, s1, u)
        self._live(P, t, u)
        A._idle(P, t, self.t0, amp=self.BREATH_AMP, period=self.BREATH_PER)
        legs = {}
        for k in LEGS:
            s0, s1 = self.sched.get(k, (0.0, 1.0))
            legs[k] = _step_leg(self.legs0[k], self.legs1[k], (u - s0) / max(s1 - s0, 1e-6), S,
                                self.STEP_LIFT)
        P["legs"] = legs
        return P

    def _front_x(self):
        return 0.5 * (self.legs0["LF"][0] + self.legs0["RF"][0])

    def _hind_x(self):
        return 0.5 * (self.legs0["LH"][0] + self.legs0["RH"][0])


class _QStand(_QPosture):
    """Idle stand: breathing, tail sway, small head drift, ear flicks. Paws stay planted
    (after a sit / lie / crouch the wolf first gets up, stepping the hind paws back)."""
    kind = "stand"
    POSTURE = "stand"

    def __init__(self, A, t0, state, dur=1.0, fade=0.25, base=None, look=0.0, head=None,
                 neck=None, tail=None, ears=None, low=0.0, **kw):
        self.look, self.head_o, self.neck_o, self.tail_o, self.ears_o = look, head, neck, tail, ears
        self.low = low
        _QPosture.__init__(self, A, t0, state, dur, fade, base, **kw)

    def _t_in(self):
        return {"crouch": 0.4, "sit": 0.8, "lie": 1.1}.get(self.post0, 0.5)

    def _targets(self):
        A, S, fac = self.A, self.A.S, self.fac
        st = A.STAND
        K = dict(hturn=self.look)
        for key, v in (("head", self.head_o), ("neck", self.neck_o), ("tail", self.tail_o),
                       ("ears", self.ears_o)):
            if v is not None:
                K[key] = v
        if self.low:
            K["hf"] = st["hf"] - 0.12 * self.low
            K["hh"] = st["hh"] - 0.08 * self.low
            K["neck"] = K.get("neck", st["neck"]) - 20 * self.low
        if self.post0 == "stand":
            legs1 = {k: list(v) for k, v in self.legs0.items()}
            for v in legs1.values():
                v[3] = v[4] = v[5] = 0.0
            return K, self.x0, legs1, {}, {"x": (0.0, 1.0)}
        # getting up: front paws stay, the body rises over them, the hind paws step back
        PR = A.PR
        x1 = self._front_x() - fac * (0.5 * PR["chord"] + PR["toe_f"] + 0.012) * S
        legs1 = A._stand_legs(x1, self.yaw)
        for k in ("LF", "RF"):
            legs1[k] = [self.legs0[k][0], self.legs0[k][1], legs1[k][2], 0.0, 0.0, 0.0, 1.0]
        sched = {"LH": (0.12, 0.6), "RH": (0.28, 0.76), "LF": (0.0, 0.5), "RF": (0.0, 0.5)}
        stage = {"x": (0.0, 0.75), "hh": (0.0, 0.7), "hf": (0.0, 0.55), "chord": (0.0, 0.7),
                 "neck": (0.0, 0.6), "head": (0.0, 0.6), "tail": (0.2, 1.0)}
        if self.post0 == "lie":
            sched = {"LH": (0.3, 0.7), "RH": (0.42, 0.82), "LF": (0.0, 0.3), "RF": (0.0, 0.3)}
            stage.update({"hf": (0.0, 0.5), "hh": (0.25, 0.85), "x": (0.0, 0.8)})
        return K, x1, legs1, sched, stage


class _QSit(_QPosture):
    """Sit: the rump drops onto the folded hind legs (hocks on the ground), chest upright,
    forelegs straight under the withers, tail along the ground."""
    kind = "sit"
    POSTURE = "sit"
    T_IN = 0.95
    STEP_LIFT = 0.025

    def __init__(self, A, t0, state, dur=2.0, fade=0.25, base=None, look=0.0, **kw):
        self.look = look
        _QPosture.__init__(self, A, t0, state, dur, fade, base, **kw)

    def _targets(self):
        A, S, fac, PR = self.A, self.A.S, self.fac, self.A.PR
        K = dict(hf=0.90, hh=0.32, chord=0.64, arch=-0.012, neck=46.0, head=-18.0, tail=-100.0,
                 tcurve=0.5, ears=0.45, tsway=0.35, sit=1.0, hturn=self.look)
        xf = self._front_x()
        if self.post0 == "lie":     # sitting up from lying: the front paws come back
            xf = self._hind_x() + fac * 0.47 * S
        x1 = xf - fac * (0.5 * 0.64 * PR["chord"] + 0.05) * S
        legs1 = {}
        for k in LEGS:
            l0 = self.legs0[k]
            if _FRONT[k]:
                xx = xf + fac * (0.012 if k == "LF" else -0.012) * S
                legs1[k] = [xx, A.ground(xx), l0[2], 0.0, 0.0, 0.0, 1.0]
            else:
                xx = xf - fac * (0.44 + (0.02 if k == "LH" else -0.02)) * S
                legs1[k] = [xx, A.ground(xx), l0[2] * 1.3, 0.0, 0.0, 80.0, 1.0]
        sched = {"LH": (0.22, 0.66), "RH": (0.32, 0.76), "LF": (0.0, 0.5), "RF": (0.05, 0.55)}
        stage = {"x": (0.1, 0.85), "hh": (0.12, 0.95), "chord": (0.12, 0.9), "hf": (0.2, 0.95),
                 "neck": (0.0, 0.7), "head": (0.0, 0.7), "tail": (0.35, 1.0)}
        return K, x1, legs1, sched, stage

    def _live(self, P, t, u):
        P["hh"] -= 0.025 * math.sin(math.pi * _ss(0.72, 1.0, u))       # settle onto the haunches


class _QLie(_QPosture):
    """Lie down (sphinx): hind legs folded, forelegs flat forward. head_down 0..1 lowers the
    chin to the snow; eyes 0..1 opens the eyes; breath > 1 gives the heavy, fast breathing
    of a wounded animal."""
    kind = "lie"
    POSTURE = "lie"
    T_IN = 1.3
    STEP_LIFT = 0.035

    def __init__(self, A, t0, state, dur=2.0, fade=0.25, base=None, head_down=0.0, eyes=1.0,
                 breath=1.0, **kw):
        self.hd, self.eyes = clamp(head_down), clamp(eyes)
        self.BREATH_AMP = float(breath)
        self.BREATH_PER = A.BREATH / (1.0 + 0.45 * max(0.0, breath - 1.0))
        _QPosture.__init__(self, A, t0, state, dur, fade, base, **kw)

    def _targets(self):
        A, S, fac, PR = self.A, self.A.S, self.fac, self.A.PR
        hd = self.hd
        K = dict(hf=0.46 - 0.03 * hd, hh=0.36, chord=0.96, arch=0.03, neck=30.0 - 58.0 * hd,
                 head=-14.0 + 10.0 * hd, tail=-100.0, tcurve=0.5, ears=0.35 - 0.5 * hd,
                 tsway=0.25, lie=1.0, eopen=self.eyes)
        chord = 0.96 * PR["chord"]
        xh = self._hind_x()
        if self.post0 == "sit":
            xh += fac * 0.06 * S
        x1 = xh + fac * (0.5 * chord - 0.08) * S
        legs1 = {}
        for k in LEGS:
            l0 = self.legs0[k]
            if _FRONT[k]:
                xx = x1 + fac * (0.5 * chord + 0.60 + (0.03 if k == "LF" else -0.02)) * S
                legs1[k] = [xx, A.ground(xx), l0[2], 0.0, 0.0, 78.0, 1.0]
            else:
                xx = xh + fac * (0.02 if k == "LH" else -0.02) * S
                legs1[k] = [xx, A.ground(xx), l0[2] * 1.25, 0.0, 0.0, 80.0, 1.0]
        if self.post0 == "sit":
            sched = {"LH": (0.0, 0.3), "RH": (0.05, 0.35), "LF": (0.1, 0.55), "RF": (0.3, 0.75)}
            stage = {"hh": (0.0, 0.4), "hf": (0.1, 0.9), "chord": (0.1, 0.8), "x": (0.05, 0.9),
                     "neck": (0.4, 1.0), "head": (0.4, 1.0), "eopen": (0.6, 1.0)}
        else:
            sched = {"LH": (0.02, 0.40), "RH": (0.10, 0.48), "LF": (0.38, 0.75), "RF": (0.50, 0.87)}
            stage = {"hh": (0.0, 0.55), "hf": (0.3, 1.0), "chord": (0.2, 0.9), "x": (0.15, 0.95),
                     "neck": (0.4, 1.0), "head": (0.4, 1.0), "eopen": (0.6, 1.0)}
        return K, x1, legs1, sched, stage


class _QCrouch(_QPosture):
    """Crouch: low on loaded haunches, head low and forward, ears pricked, hackles up, a fine
    tremble - the anticipation before a lunge."""
    kind = "crouch"
    POSTURE = "crouch"
    T_IN = 0.45

    def _targets(self):
        A, S, fac = self.A, self.A.S, self.fac
        K = dict(hf=0.63, hh=0.70, chord=0.93, arch=0.05, neck=-12.0, head=-8.0, ears=0.9,
                 ruff=0.7, tail=-16.0, tcurve=2.0, tsway=0.15, snarl=0.25, tremble=0.35)
        legs1 = {k: list(v) for k, v in self.legs0.items()}
        for k in ("LH", "RH"):
            xx = self.legs0[k][0] + fac * 0.10 * S
            legs1[k] = [xx, A.ground(xx), self.legs0[k][2], 0.0, 0.0, 0.0, 1.0]
        for k in ("LF", "RF"):
            legs1[k][3] = legs1[k][4] = legs1[k][5] = 0.0
        sched = {"LH": (0.05, 0.6), "RH": (0.18, 0.75), "LF": (0.0, 0.5), "RF": (0.0, 0.5)}
        stage = {"hf": (0.0, 0.8), "hh": (0.1, 1.0), "x": (0.0, 1.0)}
        return K, self.x0 - fac * 0.03 * S, legs1, sched, stage

    def _live(self, P, t, u):
        sink = _s01((t - self.t0 - self.t_in) / max(0.6, self.dur))
        P["hh"] -= 0.015 * sink
        P["hf"] -= 0.01 * sink


class _QTurn(_Clip):
    """Turn around in place (yaw +-180): the head leads, the forequarters swing first, then
    the hindquarters; every paw steps twice around the root."""
    kind = "turn"

    def __init__(self, A, t0, state, dur=0.9, fade=0.2, base=None, via="front", **kw):
        _Clip.__init__(self, A, t0, state, max(0.4, dur), fade, base)
        y0 = state["yaw"]
        f0 = _fac(y0)
        self.y0 = y0
        self.dy = 180.0 * (f0 if via == "front" else -f0)
        y1 = y0 + self.dy
        y1 = (y1 + 180.0) % 360.0 - 180.0
        if y1 == -180.0:
            y1 = 180.0
        self.y1 = y1
        self.x0 = state["x"]
        self.p0 = dict(A.STAND)
        self.p0.update(state.get("pose") or {})
        self.legs0 = {k: list(v) for k, v in state["legs"].items()}
        self.legs1 = A._stand_legs(self.x0, y1)
        sch = {"LF": ((0.04, 0.34), (0.40, 0.70)), "RF": ((0.12, 0.42), (0.48, 0.78)),
               "LH": ((0.26, 0.56), (0.60, 0.90)), "RH": ((0.33, 0.63), (0.68, 0.98))}
        self.sch = sch
        self.mid = {}
        for k, (a, b) in sch.items():
            yF, yH = self._yaws(a[1])
            self.mid[k] = self._ideal(k, yF if _FRONT[k] else yH)
        self.end_state = dict(x=self.x0, yaw=y1, legs={k: list(v) for k, v in self.legs1.items()},
                              pose=dict(A.STAND), posture="stand")

    def _yaws(self, u):
        wF = _s01(u / 0.72)
        wH = _s01((u - 0.24) / 0.76)
        return self.y0 + self.dy * wF, self.y0 + self.dy * wH

    def _ideal(self, k, yaw):
        A, S = self.A, self.A.S
        f = A._neutral_f(k)
        l = _LEFT[k] * A.PR["lw_f" if _FRONT[k] else "lw_h"]
        c, s = math.cos(yaw * D2R), math.sin(yaw * D2R)
        x = self.x0 + (f * c + l * s) * S
        return [x, A.ground(x), (f * s - l * c) * S, 0.0, 0.0, 0.0, 1.0]

    def pose(self, t):
        A, S = self.A, self.A.S
        u = clamp((t - self.t0) / self.dur)
        yF, yH = self._yaws(u)
        P = A._base_params(self.x0, 0.5 * (yF + yH), t)
        P["bend"] = 0.5 * (yF - yH)
        w = _s01(u / 0.5)
        for key in _POSE_KEYS:
            a, b = self.p0.get(key, 0.0), A.STAND.get(key, 0.0)
            if a != b:
                P[key] = a + (b - a) * w
        sp = math.sin(math.pi * u)
        lead = 38.0 * math.sin(math.pi * min(1.0, u / 0.85)) * (1.0 if self.dy > 0 else -1.0)
        P["hturn"] += lead * (1.0 if math.cos(yF * D2R) >= 0 else -1.0)
        P["hf"] -= 0.035 * sp
        P["hh"] -= 0.02 * sp
        P["neck"] -= 8.0 * sp
        P["tsway"] = 0.4
        A._idle(P, t, self.t0)
        legs = {}
        for k in LEGS:
            (a0, a1), (b0, b1) = self.sch[k]
            if u < b0:
                legs[k] = _step_leg(self.legs0[k], self.mid[k], (u - a0) / (a1 - a0), S, 0.09)
            else:
                legs[k] = _step_leg(self.mid[k], self.legs1[k], (u - b0) / (b1 - b0), S, 0.09)
        P["legs"] = legs
        return P


class _QRecoil(_Clip):
    """Flinch backward: the forequarters rear, head jerks back, ears pin, a quick hop back,
    then a low defensive snarl (held until the next action)."""
    kind = "recoil"

    def __init__(self, A, t0, state, dur=0.9, fade=0.08, base=None, dist=None, **kw):
        _Clip.__init__(self, A, t0, state, max(0.5, dur), fade, base)
        S = A.S
        self.yaw = state["yaw"]
        self.fac = fac = _fac(self.yaw)
        self.x0 = state["x"]
        self.dist = 0.45 * S if dist is None else float(dist)
        self.x1 = self.x0 - fac * self.dist
        self.p0 = dict(A.STAND)
        self.p0.update(state.get("pose") or {})
        self.legs0 = {k: list(v) for k, v in state["legs"].items()}
        legs1 = A._stand_legs(self.x1, self.yaw)
        for k in ("LF", "RF"):
            legs1[k][0] += fac * 0.06 * S
            legs1[k][1] = A.ground(legs1[k][0])
        self.legs1 = legs1
        pd = dict(A.STAND)
        pd.update(hf=0.80, hh=0.82, neck=4.0, head=-20.0, ears=-0.8, ruff=1.0, snarl=0.9,
                  jaw=0.22, tail=-64.0, tcurve=3.0, tsway=0.2, tremble=0.4)
        self.pd = pd
        self.end_state = dict(x=self.x1, yaw=self.yaw, legs={k: list(v) for k, v in legs1.items()},
                              pose=dict(pd), posture="stand")

    def pose(self, t):
        A, S = self.A, self.A.S
        tau = max(0.0, t - self.t0)
        st = _ss(0.0, 0.07, tau) * (1.0 - _ss(0.22, 0.5, tau))      # the startle
        settle = _ss(0.18, 0.55, tau)
        x = self.x0 + (self.x1 - self.x0) * _ss(0.03, 0.36, tau)
        P = A._base_params(x, self.yaw, t)
        for key in _POSE_KEYS:
            a, b = self.p0.get(key, 0.0), self.pd.get(key, 0.0)
            P[key] = a + (b - a) * settle
        P["hf"] += 0.11 * st
        P["hh"] -= 0.03 * st
        P["neck"] += 30.0 * st
        P["head"] += 24.0 * st
        P["ears"] = P["ears"] * (1 - st) - 0.95 * st
        P["jaw"] += 0.4 * st
        P["snarl"] = max(P["snarl"], 0.7 * st)
        P["tail"] -= 20.0 * st
        A._idle(P, t, self.t0)
        legs = {}
        for k in LEGS:
            a, b = {"LF": (0.02, 0.30), "RF": (0.04, 0.32), "LH": (0.07, 0.34), "RH": (0.11, 0.38)}[k]
            legs[k] = _step_leg(self.legs0[k], self.legs1[k], (tau - a) / (b - a), S,
                                0.24 if _FRONT[k] else 0.08)
        P["legs"] = legs
        return P


class _QLunge(_Clip):
    """Lunge / leap to root x `to`: load on the haunches, drive (forequarters rise first),
    a ballistic flight (body follows its path: nose up, level, nose down), land fore then
    hind, absorb, recover with a step. bite=True snaps the jaws at the landing."""
    kind = "lunge"

    def __init__(self, A, t0, state, dur=None, fade=0.15, base=None, to=None, height=None,
                 big=False, bite=False, **kw):
        _Clip.__init__(self, A, t0, state, 1.0, fade, base)
        S = A.S
        self.yaw = state["yaw"]
        self.fac = fac = _fac(self.yaw)
        self.x0 = x0 = state["x"]
        self.p0 = dict(A.STAND)
        self.p0.update(state.get("pose") or {})
        self.legs0 = {k: list(v) for k, v in state["legs"].items()}
        post0 = state.get("posture", "stand")
        self.big, self.bite = bool(big), bool(bite)
        to = x0 + fac * (3.0 if big else 1.6) * S if to is None else float(to)
        dist = max(0.5 * S, (to - x0) * fac)
        g = self.g = 3600.0 * S / 330.0
        H = height if height is not None else (0.85 * S if big else 0.30 * S)
        l_lo, l_td = 0.12 * S, 0.02 * S
        H = max(H, l_lo + 0.05 * S)
        T_up = math.sqrt(2 * (H - l_lo) / g)
        T_dn = math.sqrt(2 * (H - l_td) / g)
        T_fl = T_up + T_dn
        self.l_lo, self.l_td, self.v_up, self.v_dn = l_lo, l_td, g * T_up, g * T_dn
        self.T_load = 0.12 if post0 == "crouch" else 0.26
        self.T_push = 0.20
        self.lift_load = (-0.03 if post0 == "crouch" else -0.11) * S
        T_abs = 0.4
        for _ in range(8):
            v = (dist + 0.04 * S) / (0.5 * self.T_push + T_fl + 0.5 * T_abs)
            T_abs = clamp(1.6 * S / v, 0.28, 0.6)
        self.v, self.T_abs, self.T_fl = v, T_abs, T_fl
        self.ta = t0 + self.T_load
        self.t_lo = self.ta + self.T_push
        self.t_td = self.t_lo + T_fl
        self.t_ab = self.t_td + T_abs
        self.x_a = x0 - fac * 0.04 * S
        self.x_lo = self.x_a + fac * 0.5 * v * self.T_push
        self.x_td = self.x_lo + fac * v * T_fl
        self.x1 = self.x_td + fac * 0.5 * v * T_abs
        t_end = self.t_ab + 0.6
        if dur:
            t_end = max(t_end, self.t0 + dur)
        self.t1 = t_end
        self.dur = t_end - self.t0
        st = A.STAND
        nk = 16.0 if big else 6.0
        self.frames = [
            (self.t0, self.p0),
            (self.ta, dict(st, neck=-14.0, head=-6.0, ears=0.9, ruff=0.5, tail=-16.0, chord=0.93,
                           arch=0.05, tsway=0.1, snarl=0.3 if bite else 0.0)),
            (self.t_lo, dict(st, neck=nk - 4, head=-4.0, ears=-0.3, chord=1.07, arch=-0.03,
                             tail=-6.0, wind=0.6, tsway=0.1, snarl=0.5 if bite else 0.0)),
            (self.t_lo + 0.45 * T_fl, dict(st, neck=nk, head=-8.0, ears=-0.5, chord=1.10,
                                           arch=-0.045, tail=0.0, wind=1.0, tsway=0.1,
                                           snarl=0.9 if bite else 0.0)),
            (self.t_td, dict(st, neck=20.0, head=-22.0, ears=0.1, chord=0.95, arch=0.05,
                             tail=-18.0, wind=0.8, tsway=0.2, snarl=0.9 if bite else 0.0)),
            (self.t_td + 0.6 * T_abs, dict(st, neck=12.0, head=-24.0, chord=0.97, arch=0.03,
                                           tail=-30.0, wind=0.3, snarl=0.5 if bite else 0.0)),
            (self.t_ab + 0.45, dict(st)),
        ]
        legs_end = A._stand_legs(self.x1, self.yaw)
        self.legs_end = legs_end
        land = {}
        for k in LEGS:
            if _FRONT[k]:
                tl = self.t_td + (0.0 if k == "LF" else 0.035)
                Pl = self._body(tl)
                (xw, _), _s = _girdles(A, Pl)
                xl = xw + fac * (0.38 + (0.04 if k == "LF" else -0.02)) * S
            else:
                tl = self.t_td + 0.10 + (0.0 if k == "LH" else 0.03)
                Pl = self._body(tl)
                _w, (xs, _) = _girdles(A, Pl)
                xl = xs + fac * (0.30 + (0.03 if k == "LH" else -0.02)) * S
            lnd = [xl, A.ground(xl), legs_end[k][2], 0.0, 0.0, 0.0, 1.0]
            # one recovery step onto the final stance if the landing is far from it
            rec = None
            if abs(legs_end[k][0] - xl) > 0.06 * S:
                r0 = self.t_td + 0.55 * T_abs + {"LF": 0.0, "RF": 0.08, "LH": 0.16, "RH": 0.24}[k]
                rec = (r0, r0 + 0.24)
            land[k] = (tl, lnd, rec)
        self.land = land
        self.end_state = dict(x=self.x1, yaw=self.yaw, legs={k: list(v) for k, v in legs_end.items()},
                              pose=dict(st), posture="stand")

    # root path --------------------------------------------------------------
    def _x(self, t):
        fac, v = self.fac, self.v
        if t <= self.ta:
            return self.x0 + (self.x_a - self.x0) * _ss(self.t0, self.ta, t)
        if t <= self.t_lo:
            tau = t - self.ta
            return self.x_a + fac * 0.5 * v * tau * tau / self.T_push
        if t <= self.t_td:
            return self.x_lo + fac * v * (t - self.t_lo)
        if t <= self.t_ab:
            tau = t - self.t_td
            return self.x_td + fac * (v * tau - 0.5 * v * tau * tau / self.T_abs)
        return self.x1

    def _lift(self, t):
        S = self.A.S
        if t <= self.ta:
            return self.lift_load * _ss(self.t0, self.ta, t)
        if t <= self.t_lo:          # Hermite: from rest at the load depth to the take-off velocity
            u = (t - self.ta) / self.T_push
            p0, p1, m1 = self.lift_load, self.l_lo, self.v_up * self.T_push
            h01 = u * u * (3 - 2 * u)
            h11 = u * u * (u - 1)
            return p0 + (p1 - p0) * h01 + m1 * h11
        if t <= self.t_td:
            tau = t - self.t_lo
            return self.l_lo + self.v_up * tau - 0.5 * self.g * tau * tau
        tau = t - self.t_td
        T1 = 0.17
        dip = -0.10 * S * (1.6 if self.big else 1.0)
        if tau <= T1:
            u = tau / T1
            m0 = -self.v_dn * T1
            h00 = 2 * u ** 3 - 3 * u * u + 1
            h10 = u ** 3 - 2 * u * u + u
            h01 = -2 * u ** 3 + 3 * u * u
            return self.l_td * h00 + m0 * h10 + dip * h01
        return dip * (1.0 - _ss(T1, T1 + self.T_abs + 0.25, tau))

    def _pitch(self, t):
        if t <= self.ta:
            return -5.0 * _ss(self.t0, self.ta, t)
        if t <= self.t_lo:
            return -5.0 + 25.0 * _s01((t - self.ta) / self.T_push)
        if t <= self.t_td:
            vy = self.v_up - self.g * (t - self.t_lo)
            path = 0.55 * math.degrees(math.atan2(vy, self.v))
            return 20.0 + (path - 20.0) * _ss(0.0, 0.12, t - self.t_lo)
        tau = t - self.t_td
        vy = -self.v_dn
        p_td = 0.55 * math.degrees(math.atan2(vy, self.v))
        return p_td * (1.0 - _ss(0.0, 0.2, tau)) - 6.0 * math.sin(math.pi * _ss(0.0, 0.35, tau))

    def _body(self, t):
        A, S = self.A, self.A.S
        P = A._base_params(self._x(t), self.yaw, t)
        for key in _POSE_KEYS:
            if key in ("hf", "hh"):
                continue
            P[key] = _keyframes(t, self.frames, key, A.STAND.get(key, 0.0))
        lift = self._lift(t) / S
        sp = math.sin(self._pitch(t) * D2R)
        base_f = _keyframes(t, self.frames, "hf", A.STAND["hf"])
        base_h = _keyframes(t, self.frames, "hh", A.STAND["hh"])
        P["hf"] = base_f + lift + 0.42 * sp
        P["hh"] = base_h + lift - 0.42 * sp
        if self.bite:
            # jaws open through the flight and snap shut on the landing
            P["jaw"] = 0.75 * _ss(self.t_lo + 0.2 * self.T_fl, self.t_lo + 0.6 * self.T_fl, t) * \
                (1.0 - _ss(self.t_td - 0.03, self.t_td + 0.05, t))
        return P

    def _air(self, k, t, P):
        """Airborne paw target (body-relative keys) at time t."""
        A, S, fac = self.A, self.A.S, self.fac
        (xw, yw), (xs, ys) = _girdles(A, P)
        T_fl = self.T_fl
        if _FRONT[k]:
            u = (t - self.t_lo) / T_fl
            w = _ss(0.25, 0.75, u)
            reach = (0.50, -0.80) if self.big else (0.42, -0.76)
            fx = 0.12 + (reach[0] - 0.12) * w
            fy = -0.50 + (reach[1] + 0.50) * w
            fold = 0.8 * (1 - w)
            pa = 95.0 * (1 - w) + 35.0 * w
            gx, gy = xw, yw
        else:
            u = (t - self.t_lo) / T_fl
            w = _ss(0.3, 0.95, u)
            fx = -0.48 + 0.66 * w
            fy = -0.70 + 0.12 * w
            fold = 0.55 * w
            pa = 70.0 - 10.0 * w
            gx, gy = xs, ys
        return [gx + fac * fx * S, gy - fy * S, self.legs_end[k][2], pa, fold, 0.0, 0.0]

    def pose(self, t):
        A, S = self.A, self.A.S
        t = max(t, self.t0)
        P = self._body(t)
        A._idle(P, t, self.t0, moving=1.0 if self.ta < t < self.t_ab else 0.0)
        legs = {}
        for k in LEGS:
            l0 = self.legs0[k]
            tl, lnd, rec = self.land[k]
            front = _FRONT[k]
            t_off = (self.ta + 0.04) if front else self.t_lo
            if t <= t_off:
                lg = list(l0)
                lg[6] = 1.0
                if not front:      # the hind paws peel as the legs extend
                    lg[3] = 50.0 * _ss(self.ta, self.t_lo, t)
                legs[k] = lg
            elif t < tl:
                air = self._air(k, t, P)
                w0 = _ss(t_off, t_off + 0.12, t)          # leaving the ground
                if w0 < 1.0:
                    air = [a + (b - a) * w0 for a, b in zip(l0, air)]
                    air[6] = 0.0
                w1 = _ss(tl - 0.30 * self.T_fl, tl, t)    # reaching for the landing spot
                if w1 > 0.0:
                    air = [a + (b - a) * w1 for a, b in zip(air, lnd)]
                    air[1] -= 0.05 * S * math.sin(math.pi * w1) * (1 - w1)
                    air[6] = 0.0
                legs[k] = air
            elif rec is None or t <= rec[0]:
                legs[k] = list(lnd)
            else:
                legs[k] = _step_leg(lnd, self.legs_end[k], (t - rec[0]) / (rec[1] - rec[0]), S, 0.08)
        P["legs"] = legs
        return P


class _QHead(_Clip):
    """Head acts layered over the body action (chained) or at absolute times (overlay)."""
    overlay = True
    kind = "head"
    FIN, FOUT = 0.3, 0.4

    def __init__(self, A, t0, state, dur=2.0, fade=0.0, base=None, **kw):
        _Clip.__init__(self, A, t0, state, dur, 0.0, base, **kw)
        self.inside = state is not None
        if self.inside and base is None:
            base = A.CLIPS["stand"](A, t0, state, dur=max(dur, 0.1))
        self.base = base
        self.fade_in, self.fade_out = self.FIN, self.FOUT
        self.end_state = state if base is None else base.end_state

    def pose(self, t):
        return self.apply(self.base.pose(t), t)

    def env(self, t):
        if self.inside:
            return _env(t, self.t0, self.t1, self.fade_in, self.fade_out)
        return _env(t, self.t0 - self.fade_in, self.t1 + self.fade_out, self.fade_in, self.fade_out)

    def apply(self, P, t):
        e = self.env(t)
        if e <= 0.0:
            return P
        P = dict(P)
        self._act(P, t, e)
        return P

    def _act(self, P, t, e):
        raise NotImplementedError


class _QSnarl(_QHead):
    """Snarl / growl: head low, lips back over the teeth, hackles up, a growl tremor."""
    kind = "snarl"
    FIN, FOUT = 0.25, 0.45

    def _act(self, P, t, e):
        a = clamp(self.kw.get("amount", 1.0))
        ears = self.kw.get("ears", 0.9)
        sd = self.A.seed
        q = math.sin(2 * math.pi * 11.0 * t) * (0.6 + 0.4 * noise1(t * 3.0, sd + 61))
        P["neck"] += e * (-14.0 - 4.0 * a)
        P["head"] += e * (-6.0 + 0.8 * q)
        P["hf"] -= e * 0.035
        P["snarl"] = max(P["snarl"], e * a)
        P["jaw"] = max(P["jaw"], e * (0.30 * a * a + 0.035 * q * a))
        P["ruff"] = max(P["ruff"], e * a)
        P["ears"] += (ears - P["ears"]) * e
        P["tail"] += (-14.0 - P["tail"]) * e * 0.6


class _QHowl(_QHead):
    """Howl: the head rises to the sky, the mouth opens round, a long sustain with vibrato."""
    kind = "howl"
    FIN, FOUT = 0.8, 0.7

    def _act(self, P, t, e):
        tau = t - self.t0
        dur = max(self.dur, 0.5)
        m = _ss(0.35, 0.8, tau) * (1.0 - _ss(dur - 0.25, dur + 0.25, tau))
        arc = math.sin(math.pi * clamp(tau / dur))
        vib = math.sin(2 * math.pi * 5.5 * t) * 0.6
        P["neck"] += (74.0 - P["neck"]) * e
        P["head"] += (50.0 + 4.0 * arc + vib - P["head"]) * e
        P["hf"] += 0.008 * e
        P["jaw"] = max(P["jaw"], m * e * (0.30 + 0.06 * arc + 0.02 * vib))
        P["ears"] += (0.0 - P["ears"]) * e
        P["eopen"] *= 1.0 - 0.45 * e
        P["tail"] += (-50.0 - P["tail"]) * e * 0.5
        P["puff"] = max(P.get("puff", 0.0), m * e)


class _QLook(_QHead):
    """Look: turn the head toward the camera by `turn` deg (negative: away)."""
    kind = "look"
    FIN, FOUT = 0.35, 0.35

    def _act(self, P, t, e):
        P["hturn"] += (self.kw.get("turn", 55.0) - P["hturn"]) * e
        if self.kw.get("head") is not None:
            P["head"] += (self.kw["head"] - P["head"]) * e
        if self.kw.get("neck") is not None:
            P["neck"] += (self.kw["neck"] - P["neck"]) * e


class _QBite(_QHead):
    """Bite: n fast snaps (head darts forward, jaws open wide and slam shut)."""
    kind = "bite"
    FIN, FOUT = 0.06, 0.12

    def _act(self, P, t, e):
        n = max(1, int(self.kw.get("n", 1)))
        per = max(self.dur, 0.2) / n
        ph = ((t - self.t0) / per) % 1.0 if t >= self.t0 else 0.0
        op = _ss(0.0, 0.55, ph) * (1.0 - _ss(0.62, 0.78, ph))
        dart = math.sin(math.pi * _ss(0.2, 0.85, ph))
        P["jaw"] = max(P["jaw"], e * 0.95 * op)
        P["snarl"] = max(P["snarl"], e * 0.9)
        P["neck"] += e * (-12.0 * dart)
        P["head"] += e * (-6.0 * dart + 10.0 * op)
        P["ears"] += (-0.6 - P["ears"]) * e
        P["ruff"] = max(P["ruff"], e)


class _QEyes(_QHead):
    """Eyes: open (or close) the eyes to `open` 0..1 over the fade."""
    kind = "eyes"
    FIN, FOUT = 0.6, 0.4

    def _act(self, P, t, e):
        P["eopen"] += (self.kw.get("open", 1.0) - P["eopen"]) * e


class _QRun(_Clip):
    """A locomotion run: consecutive walk/stalk/trot/gallop segments with continuous speed,
    distance-driven gait phase and event-planned paw plants (no sliding in stance)."""
    kind = "run"

    def __init__(self, A, t0, state, segs):
        S = A.S
        self.A = A
        self.base = None
        self.start = state
        self.t0 = float(t0)
        self.fade = 0.3
        x0, yaw0 = state["x"], state["yaw"]
        self.facing = fac = 1.0 if math.cos(yaw0 * D2R) >= 0 else -1.0
        self.yaw = yaw0
        G = A.GAIT
        # ------------------------------------------------ speed profile (piecewise ramps)
        pieces = []          # (ta, T, da, va, vb) distances along the facing direction
        tcur, dcur, vprev = self.t0, 0.0, 0.0
        gkeys = []           # (t, g, k) gait keys at segment starts (end of their ramp)
        segl = []
        xprev = x0
        for i, sg in enumerate(segs):
            gp = G[sg["kind"]]
            dist = max(0.0, (sg["to"] - xprev) * fac) / S
            xprev = sg["to"]
            v = sg.get("speed")
            v = (v / S) if v else gp["v"] * A.pace
            last = i == len(segs) - 1
            segl.append([dist, v, gp, last, sg.get("dur")])
        for i, (dist, v, gp, last, dur) in enumerate(segl):
            acc = gp["acc"] * A.pace
            dec = gp["dec"] * A.pace
            if dur:
                # solve the cruise speed so the segment lasts about dur seconds
                lo, hi = 0.02, 40.0
                for _ in range(40):
                    vm = 0.5 * (lo + hi)
                    T_in = max(0.25, abs(vm - vprev) / acc)
                    T_out = max(0.45, vm / dec) if last else 0.0
                    dr = 0.5 * (vprev + vm) * T_in + 0.5 * vm * T_out
                    if dist < dr:
                        hi = vm
                    elif T_in + T_out + (dist - dr) / vm > dur:
                        lo = vm
                    else:
                        hi = vm
                v = 0.5 * (lo + hi)
            # shrink the target speed until the ramps fit inside the segment
            for _ in range(60):
                T_in = max(0.25, abs(v - vprev) / acc)
                T_out = max(0.45, v / dec) if last else 0.0
                dr = 0.5 * (vprev + v) * T_in + 0.5 * v * T_out
                if dr <= dist or v < 0.03:
                    break
                v *= 0.9
            cruise = max(0.0, dist - dr) / max(v, 1e-6)
            pieces.append((tcur, T_in, dcur, vprev, v))
            gkeys.append((tcur, tcur + T_in, gp["g"], gp.get("k", 0.0)))
            dcur += 0.5 * (vprev + v) * T_in
            tcur += T_in
            if cruise > 0:
                pieces.append((tcur, cruise, dcur, v, v))
                dcur += v * cruise
                tcur += cruise
            if last:
                pieces.append((tcur, T_out, dcur, v, 0.0))
                dcur += 0.5 * v * T_out
                tcur += T_out
            vprev = v
        self.pieces = pieces
        self.gkeys = gkeys
        self.t_stop = tcur
        self.d_total = dcur
        self.x_end = x0 + fac * dcur * S
        self.x0 = x0
        # ------------------------------------------------ integrate phase on a grid
        dt = 1.0 / 240.0
        nmax = int((self.t_stop - self.t0 + 3.0) / dt) + 2
        T = self.t0 + dt * np.arange(nmax)
        D = np.empty(nmax)
        V = np.empty(nmax)
        for j in range(nmax):
            D[j], V[j] = self._dv(T[j])
        Gs = np.empty(nmax)
        Ks = np.empty(nmax)
        for j in range(nmax):
            Gs[j], Ks[j] = self._gk(T[j], V[j])
        # gait-blended parameters along the grid
        duty = np.empty(nmax)
        cad = np.empty(nmax)
        Lst = np.empty(nmax)
        taus = np.empty((nmax, 4))
        for j in range(nmax):
            gp = A._gait_mix(Gs[j], Ks[j])
            v = V[j]
            L = gp["L"] * (max(v, 1e-4) / gp["v"]) ** 0.55
            acc_j = self._dva(T[j])[2] / A.pace
            if acc_j < 0:
                L *= 1.0 / (1.0 + gp["brake_L"] * (-acc_j))
            c = v / max(L, 1e-6)
            # quick short steps while accelerating hard keep the feet under the body
            c = max(c, (gp["cmin"] + 0.28 * max(0.0, acc_j)) * A.pace)
            m = _ss(0.0, 0.45, v)
            duty[j] = 0.965 + (gp["duty"] - 0.965) * m
            cad[j] = c
            Lst[j] = v / c
            taus[j] = gp["tau"]
        # phase: start so every foot is planted and LH is next to lift
        phi = np.empty(nmax)
        phi[0] = 0.92
        for j in range(1, nmax):
            phi[j] = phi[j - 1] + cad[j - 1] * dt
        self.T, self.D, self.V, self.Gs, self.Ks = T, D, V, Gs, Ks
        self.duty, self.cad, self.Lst, self.taus, self.phi = duty, cad, Lst, taus, phi
        self.dt = dt
        # ------------------------------------------------ foot events
        self.feet = {}
        jstop = int(math.ceil((self.t_stop - self.t0) / dt))
        for i, k in enumerate(LEGS):
            st = state["legs"][k]
            recs = [[-_INF, _INF, st[0], st[1], st[2]]]      # [t_td, t_lo, x, y, z]
            swing = False
            prev_cyc = math.floor(phi[0] - taus[0][i])
            for j in range(1, nmax):
                psi = phi[j] - taus[j][i]
                cyc = math.floor(psi)
                fr = psi - cyc
                tj = T[j]
                if not swing:
                    # lift off when the phase passes the duty factor (never after the stop)
                    if j < jstop and cyc == prev_cyc and fr >= duty[j]:
                        recs[-1][1] = tj
                        swing = True
                elif cyc > prev_cyc:
                    x, y, z = self._plant(k, tj, j)
                    recs.append([tj, _INF, x, y, z])
                    swing = False
                prev_cyc = cyc
                if j > jstop and not swing:
                    break
            if swing:   # never landed inside the grid: land at the end
                x, y, z = self._plant(k, T[-1], nmax - 1)
                recs.append([T[-1], _INF, x, y, z])
            self.feet[k] = recs
        self.t_settle = max(r[-1][0] for r in self.feet.values())
        self.t1 = max(self.t_stop, self.t_settle) + 0.05
        legs = {}
        for k in LEGS:
            r = self.feet[k][-1]
            legs[k] = [r[2], r[3], r[4], 0.0, 0.0, 0.0, 1.0]
        self.end_state = dict(x=self.x_end, yaw=self.yaw, legs=legs)
        self.tds = {k: [r[0] for r in self.feet[k]] for k in LEGS}

    # speed profile ------------------------------------------------------------
    def _dv(self, t):
        """(distance along facing in S units, speed in S/s) at time t."""
        d, v, _ = self._dva(t)
        return d, v

    def _dva(self, t):
        """(distance in S, speed in S/s, acceleration in S/s^2) at time t."""
        ps = self.pieces
        if not ps or t <= ps[0][0]:
            return 0.0, 0.0, 0.0
        for ta, Tp, da, va, vb in ps:
            if t <= ta + Tp:
                tau = (t - ta) / Tp if Tp > 0 else 1.0
                d = da + Tp * (va * tau + (vb - va) * (tau ** 3 - 0.5 * tau ** 4))
                v = va + (vb - va) * tau * tau * (3 - 2 * tau)
                a = (vb - va) * 6.0 * tau * (1.0 - tau) / Tp if Tp > 0 else 0.0
                return d, v, a
        return self.d_total, 0.0, 0.0

    def _gk(self, t, v):
        g, k = self.gkeys[0][2], self.gkeys[0][3]
        gprev, kprev = 0.0, 0.0
        for i, (ta, tb, gg, kk) in enumerate(self.gkeys):
            if t < ta:
                break
            u = _s01((t - ta) / max(tb - ta, 1e-6))
            g = gprev + (gg - gprev) * u
            k = kprev + (kk - kprev) * u
            gprev, kprev = gg, kk
        gn = _ss(1.05, 1.5, v / self.A.pace) + _ss(2.7, 3.5, v / self.A.pace)
        return min(g, gn), k

    def _grid(self, t):
        j = (t - self.t0) / self.dt
        if j <= 0:
            return 0, 0.0
        n = len(self.T) - 1
        if j >= n:
            return n - 1, 1.0
        i = int(j)
        return i, j - i

    def _girdle_x(self, k, t, j):
        A = self.A
        S = A.S
        d = self.D[j]
        x = self.x0 + self.facing * d * S
        off = A._neutral_f(k)
        return x + self.facing * off * S

    def _plant(self, k, t, j):
        A, S = self.A, self.A.S
        xg = self._girdle_x(k, t, j)
        reach = 0.5 * self.duty[j] * self.Lst[j]
        if _FRONT[k]:
            acc = self._dva(t)[2] / A.pace
            reach += 0.035 * max(0.0, -acc)
        x = xg + self.facing * reach * S
        y = A.ground(x)
        z = -_LEFT[k] * A.PR["lw_f" if _FRONT[k] else "lw_h"] * S * math.cos(self.yaw * D2R)
        return x, y, z

    # pose ---------------------------------------------------------------------
    def pose(self, t):
        A, S = self.A, self.A.S
        if t <= self.t0:
            t = self.t0
        j, fr = self._grid(t)
        j1 = min(j + 1, len(self.T) - 1)

        def g(arr):
            return arr[j] + (arr[j1] - arr[j]) * fr

        if t >= self.t_stop:
            d, v, acc = self.d_total, 0.0, 0.0
        else:
            d, v, acc = self._dva(t)
        gg, kk = g(self.Gs), g(self.Ks)
        phi = g(self.phi)
        x = self.x0 + self.facing * d * S
        P = A._base_params(x, self.yaw, t)
        m = _ss(0.0, 0.5, v)
        gp = A._gait_mix(gg, kk)
        for key, val in gp["pose"].items():
            P[key] = P[key] + (val - P[key]) * m
        P["speed"] = v
        P["phase"] = phi
        A._idle(P, t, self.t0, moving=m)
        # legs ------------------------------------------------------------------
        legs = {}
        bob = {True: 0.0, False: 0.0}
        lift_f = gp["lift_f"]
        lift_h = gp["lift_h"]
        for i, k in enumerate(LEGS):
            recs = self.feet[k]
            idx = bisect.bisect_right(self.tds[k], t) - 1
            r = recs[max(idx, 0)]
            front = _FRONT[k]
            if t <= r[1]:            # stance
                if r[1] < _INF and r[0] > -_INF:
                    sp = (t - r[0]) / max(r[1] - r[0], 1e-6)
                    heel = _ss(0.55, 1.0, sp)
                    bob[front] += math.sin(math.pi * sp) * (0.6 + 0.4 * m)
                elif r[1] < _INF:     # initial stance ending in a lift
                    sp = 1.0 - min(1.0, (r[1] - t) / 0.35)
                    heel = _ss(0.3, 1.0, sp)
                else:
                    heel = 0.0
                legs[k] = [r[2], r[3], r[4], A.HEEL * heel, 0.0, 0.0, 1.0]
            else:                     # swing toward the next record
                nx = recs[idx + 1] if idx + 1 < len(recs) else r
                u = (t - r[1]) / max(nx[0] - r[1], 1e-6)
                u = clamp(u, 0.0, 1.0)
                dist = abs(nx[2] - r[2])
                lift = (lift_f if front else lift_h) * S
                lift = min(lift, 0.18 * S + 0.35 * dist) * (0.35 + 0.65 * min(1.0, dist / (0.35 * S)))
                ss_ = u * u * (3 - 2 * u)
                sw = ss_ + (u - ss_) * (gp["swk_f"] if front else gp["swk_h"])
                xx = r[2] + (nx[2] - r[2]) * sw
                yy = r[3] + (nx[3] - r[3]) * sw
                if front:     # reach out past the plant, then paw back onto it
                    xx += self.facing * gp["over"] * min(dist, 1.2 * S) * math.sin(math.pi * u ** 3.1) ** 2
                lp = gp["lp_f"] if front else gp["lp_h"]
                yy -= lift * math.sin(math.pi * min(1.0, u ** lp * 1.04)) ** 0.85
                fold = _ss(0.0, 0.25, u) * (1.0 - _ss(0.42, 0.86, u))
                pa = A.HEEL * (1.0 - _ss(0.0, 0.3, u)) * (1 - fold) + A.HANG[front] * fold
                legs[k] = [xx, yy, r[4] + (nx[4] - r[4]) * u, pa, fold, 0.0, 0.0]
        P["legs"] = legs
        # body bob / pitch / flex from the gait -------------------------------------
        b = gp["bob"] * m
        P["hf"] += b * bob[True]
        P["hh"] += b * bob[False]
        fl = gp["flex"] * m
        if fl:
            c = math.cos(2 * math.pi * (phi + 0.05))
            P["chord"] *= 1.0 - fl * c
            P["arch"] += fl * 0.75 * c
            P["neck"] += 6.0 * fl / 0.1 * math.cos(2 * math.pi * (phi - 0.30))
            P["tail"] += 9.0 * fl / 0.1 * math.cos(2 * math.pi * (phi - 0.15))
        nod = gp["nod"] * m
        if nod:
            P["head"] += nod * math.cos(4 * math.pi * (phi - 0.30))
            P["neck"] += 0.5 * nod * math.cos(4 * math.pi * (phi - 0.25))
        P["tsway"] = P["tsway"] * (1 - m) + gp["tsway"] * m
        # inertia: braking braces the forelegs and sits the hindquarters down, the head
        # comes up; accelerating drops the head and front end
        acc = acc / A.pace
        brake = max(0.0, -acc)
        push = max(0.0, acc)
        P["hf"] += 0.010 * brake - 0.008 * push
        P["hh"] -= 0.016 * brake
        P["head"] += 3.5 * brake - 2.0 * push
        P["neck"] += 3.0 * brake - 2.5 * push
        A._limp(P, phi, m)
        P["wind"] = max(P["wind"], _ss(0.6, 4.5, v))
        return P


class Quadruped(_Actor):
    """Shared quadruped engine (Wolf, Cat). Sizes are in units of the shoulder height S.

    Pose dict keys (all floats unless noted): x (root = body center, world px), yaw (deg),
    hf / hh (withers / sacrum height above the ground, in S), chord (withers-sacrum, in S),
    arch, neck (deg above horizontal), head (muzzle deg above horizontal), hturn (head turn
    toward the camera, deg), jaw (0..1), snarl, ears (-1 pinned .. 1 pricked), ruff
    (hackles), tail (deg above the horizontal-backward), tcurve, tsway, wind, eopen, eglow,
    legs = {LH, LF, RH, RF: [toe_x, toe_y, toe_z, paw_angle, fold, distal_offset, contact]}.
    """

    LOCO = ("walk", "trot", "gallop", "stalk")
    PR = {}
    GAIT = {}
    STAND = {}
    HEEL = 32.0                       # paw angle at toe-off (deg)
    HANG = {True: 105.0, False: 80.0}  # paw angle when folded in the swing (fore, hind)
    ALPHA = {True: (12.0, 0.75, -100.0), False: (10.0, 0.9, -48.0)}   # distal (stance, heel k, fold)

    def __init__(self, x, ground, facing=1, size=330.0, seed=0):
        _Actor.__init__(self)
        self.S = float(size)
        if callable(ground):
            self.ground = ground
        else:
            gy = float(ground)
            self.ground = lambda _x, _g=gy: _g
        self.x0 = float(x)
        self.yaw0 = 0.0 if facing >= 0 else 180.0
        self.seed = int(seed)
        self.pace = 1.0

    # ----------------------------------------------------------- actions
    def stand(self, dur=1.0, look=0.0, **kw):
        """Idle stand: breathing, tail sway, small head drift. look: head turn toward camera (deg)."""
        return self._add("stand", dur=dur, look=look, **kw)

    wait = stand

    def walk(self, to, speed=None, dur=None):
        """Lateral-sequence walk to root x `to` (speed px/s or dur s)."""
        return self._add("walk", to=float(to), speed=speed, dur=dur)

    def stalk(self, to, speed=None, dur=None):
        """Creeping walk: body and head low, slow deliberate placement."""
        return self._add("stalk", to=float(to), speed=speed, dur=dur)

    def trot(self, to, speed=None, dur=None):
        """Diagonal-pair trot."""
        return self._add("trot", to=float(to), speed=speed, dur=dur)

    def gallop(self, to, speed=None, dur=None):
        """Rotary gallop with flexing spine and suspension (accelerates through walk/trot)."""
        return self._add("gallop", to=float(to), speed=speed, dur=dur)

    def turn(self, dur=0.6, via="front"):
        """Quick turn in place (yaw +180). via='front' swings the face past the camera."""
        return self._add("turn", dur=dur, via=via)

    # ----------------------------------------------------------- plumbing
    def _initial_state(self):
        legs = self._stand_legs(self.x0, self.yaw0)
        return dict(x=self.x0, yaw=self.yaw0, legs=legs)

    def _neutral_f(self, k):
        """Neutral toe position along the body (in S) relative to the root."""
        PR = self.PR
        if _FRONT[k]:
            return PR["chord"] * 0.5 + PR["toe_f"]
        return -PR["chord"] * 0.5 + PR["toe_h"]

    def _stand_legs(self, x, yaw, stagger=True):
        S = self.S
        c, s = math.cos(yaw * D2R), math.sin(yaw * D2R)
        legs = {}
        for k in LEGS:
            f = self._neutral_f(k)
            if stagger:
                f += {"LF": 0.035, "RF": -0.01, "LH": 0.015, "RH": -0.03}[k]
            l = _LEFT[k] * self.PR["lw_f" if _FRONT[k] else "lw_h"]
            xx = x + (f * c + l * s) * S
            zz = (f * s - l * c) * S
            legs[k] = [xx, self.ground(xx), zz, 0.0, 0.0, 0.0, 1.0]
        return legs

    def _pre_run(self, t0, state, segs, last_body):
        """Get up first if sitting / lying / crouching; turn first if the run heads behind."""
        out = []
        post = state.get("posture", "stand")
        if post != "stand":
            c = self.CLIPS["stand"](self, t0, state, base=last_body,
                                    dur={"crouch": 0.3, "sit": 0.75, "lie": 1.05}.get(post, 0.5))
            out.append(c)
            state, t0 = c.end_state, c.t1
        fac = 1.0 if math.cos(state["yaw"] * D2R) >= 0 else -1.0
        if (segs[0]["to"] - state["x"]) * fac < -1e-6:
            out.append(self.CLIPS["turn"](self, t0, state, dur=0.8, base=last_body))
        return out

    def _make_run(self, t0, state, segs):
        return _QRun(self, t0, state, segs)

    def _blend(self, a, b, w):
        return _blend_pose(a, b, w, self.S)

    def _gait_mix(self, g, k):
        """Gait parameters for continuous gait g (0 walk, 1 trot, 2 gallop) and stalk k."""
        G = self.GAIT
        if g <= 1.0:
            ws = {"walk": (1 - g) * (1 - k), "stalk": (1 - g) * k, "trot": g}
        else:
            ws = {"trot": 2 - g, "gallop": g - 1}
        out = {}
        tau = [0.0, 0.0, 0.0, 0.0]
        pose = {}
        keys = set()
        for name, wgt in ws.items():
            if wgt > 0:
                keys.update(G[name]["pose"])
        for name, wgt in ws.items():
            if wgt <= 0:
                continue
            gp = G[name]
            for key in _GAIT_NUM:
                out[key] = out.get(key, 0.0) + gp[key] * wgt
            tt = _TAU[gp["tau"]]
            for i in range(4):
                tau[i] += tt[i] * wgt
            gpose = gp["pose"]
            for key in keys:     # a key a gait does not set keeps the stand value
                pose[key] = pose.get(key, 0.0) + gpose.get(key, self.STAND[key]) * wgt
        out["tau"] = tau
        out["pose"] = pose
        return out

    def _base_params(self, x, yaw, t):
        P = dict(self.STAND)
        P["x"] = x
        P["yaw"] = yaw
        P["t"] = t
        P["phase"] = 0.0
        return P

    def _idle(self, P, t, t0, moving=0.0, amp=1.0, period=None):
        """Breathing, tail sway, head drift, ear flicks (fade out while moving); tremble."""
        sd = self.seed
        still = 1.0 - moving
        br = math.sin(2 * math.pi * (t / (period or self.BREATH) + hash01(sd, 3)))
        P["breath"] = br * amp
        P["hf"] += 0.006 * br * still * amp
        hk = still * (1.0 - 0.85 * clamp(P.get("lie", 0.0)) * clamp(-P["neck"] / 25.0))
        P["head"] += hk * (3.0 * fbm1(t * 0.23, sd + 5) + 1.2 * br)
        P["neck"] += hk * 2.5 * fbm1(t * 0.17, sd + 9)
        P["ears"] += still * 0.25 * max(0.0, noise1(t * 0.9, sd + 11)) ** 3 * 4
        tr = P.get("tremble", 0.0)
        if tr:
            q = math.sin(2 * math.pi * 12.0 * t + 1.3 * math.sin(2 * math.pi * 3.1 * t))
            P["head"] += 1.6 * tr * q
            P["neck"] += 0.8 * tr * q
            P["hf"] += 0.004 * tr * q

    def _limp(self, P, phi, m):
        pass

    # ----------------------------------------------------------- queries
    def paws(self, t):
        """World toe positions {leg: (x, y, z, contact)} at time t."""
        P = self.state(t)
        return {k: (v[0], v[1], v[2], v[6]) for k, v in P["legs"].items()}

    def footprints(self, t0=-_INF, t1=_INF):
        """Every paw plant of the locomotion runs in [t0, t1]: [(t, leg, x, y, z), ...] -
        handy for prints in the snow."""
        clips = self._get_plan()[0]
        out = []
        for c in clips:
            if isinstance(c, _QRun):
                for k, recs in c.feet.items():
                    for r in recs[1:]:
                        if t0 <= r[0] <= t1:
                            out.append((r[0], k, r[2], r[3], r[4]))
        out.sort()
        return out


# ============================================================================= wolf
_WOLF_PR = dict(
    chord=0.88,
    lw_f=0.085, lw_h=0.095,
    scap_piv=(0.0, -0.06), scap=0.30, scap0=26.0, scap_k=0.40,
    hum=0.20, rad=0.31, mc=0.10,
    hipj=(-0.075, -0.205), fem=0.285, tib=0.31, mt=0.19,
    paw=0.125,
    toe_f=0.07, toe_h=-0.06,
    neck=0.37, neck_base=(1.07, -0.105),
    head=0.48,
    tail=0.74,
)

_WOLF_STAND = dict(
    hf=0.885, hh=0.865, chord=1.0, arch=0.012, neck=27.0, head=-26.0, hturn=0.0, jaw=0.0,
    snarl=0.0, ears=0.3, ruff=0.0, tail=-36.0, tcurve=4.6, tsway=1.0, tlift=0.0, wind=0.0,
    eopen=1.0, eglow=1.0, bend=0.0, sit=0.0, lie=0.0, breath=0.0, speed=0.0, fold_f=0.0,
    fold_h=0.0, grey=0.0, headnod=0.0, tremble=0.0, puff=0.0, roll=0.0,
)

_WOLF_GAIT = {
    "walk": dict(g=0.0, v=0.85, L=1.05, duty=0.65, lift_f=0.10, lift_h=0.075, bob=0.010,
                 flex=0.0, nod=2.5, cmin=0.55, acc=1.6, dec=1.8, swk_f=0.1, swk_h=0.05, over=0.04, lp_f=0.9, lp_h=1.0, brake_L=0.15, tsway=1.2, tau="walk",
                 pose=dict(hf=0.875, hh=0.855, neck=27.0, head=-27.0, tail=-33.0, ears=0.35)),
    "stalk": dict(g=0.0, k=1.0, v=0.30, L=0.80, duty=0.80, lift_f=0.085, lift_h=0.05,
                  bob=0.004, flex=0.0, nod=1.0, cmin=0.30, acc=0.8, dec=0.9, swk_f=0.0, swk_h=0.0, over=0.03, lp_f=0.9, lp_h=1.0, brake_L=0.1, tsway=0.4, tau="walk",
                  pose=dict(hf=0.70, hh=0.745, neck=-6.0, head=-10.0, tail=-26.0, ears=0.9,
                            ruff=0.35, arch=0.03)),
    "trot": dict(g=1.0, v=2.2, L=1.75, duty=0.40, lift_f=0.17, lift_h=0.13, bob=-0.020,
                 flex=0.0, nod=0.0, cmin=0.9, acc=3.0, dec=2.6, swk_f=0.35, swk_h=0.25, over=0.06, lp_f=0.8, lp_h=1.1, brake_L=0.18, tsway=0.6, tau="trot",
                 pose=dict(hf=0.865, hh=0.85, neck=16.0, head=-22.0, tail=-22.0, ears=0.15)),
    "gallop": dict(g=2.0, v=5.0, L=2.8, duty=0.27, lift_f=0.25, lift_h=0.21, bob=-0.050,
                   flex=0.14, nod=0.0, cmin=1.2, acc=4.2, dec=3.3, swk_f=0.55, swk_h=-0.35, over=0.14, lp_f=0.7, lp_h=1.5, brake_L=0.18, tsway=0.3, tau="gallop",
                   pose=dict(hf=0.80, hh=0.80, neck=8.0, head=-10.0, tail=-8.0, ears=-0.35,
                             chord=1.0)),
}


class Wolf(Quadruped):
    """The huge black wolf of RED.

        w = Wolf(x=200, ground=1500, facing=+1, size=330, seed=1)   # size = shoulder height px
        w.stand(1.0).walk(to=600).gallop(to=2400).snarl(2.0).howl(3.0)
        w.draw(f, t, ctx)

    ground: a constant y or a function ground(x) -> y (slopes). old=True gives the epilogue
    wolf: grey muzzle, ragged sparse fur, sway back, lower head, slower gait with a limp.
    """

    PR = _WOLF_PR
    STAND = _WOLF_STAND
    GAIT = _WOLF_GAIT
    BREATH = 3.4

    def __init__(self, x, ground, facing=1, size=330.0, seed=1, old=False):
        Quadruped.__init__(self, x, ground, facing, size, seed)
        self.old = 1.0 if old is True else float(old or 0.0)
        if self.old:
            self.pace = 1.0 - 0.32 * self.old
            st = dict(_WOLF_STAND)
            o = self.old
            st.update(hf=st["hf"] - 0.03 * o, hh=st["hh"] - 0.045 * o, neck=st["neck"] - 14 * o,
                      head=st["head"] - 6 * o, tail=st["tail"] - 8 * o, arch=st["arch"] - 0.045 * o,
                      ears=st["ears"] - 0.25 * o, eglow=1.0 - 0.3 * o, grey=o)
            self.STAND = st
            gait = {}
            for name, gp in _WOLF_GAIT.items():
                g2 = dict(gp)
                pz = dict(gp["pose"])
                for key in ("hf", "hh"):
                    if key in pz:
                        pz[key] -= 0.035 * o
                for key, dv in (("neck", -14.0), ("head", -5.0), ("tail", -8.0)):
                    if key in pz:
                        pz[key] += dv * o
                g2["pose"] = pz
                g2["lift_f"] *= 1 - 0.3 * o
                g2["lift_h"] *= 1 - 0.3 * o
                g2["nod"] = gp["nod"] + 2.0 * o
                gait[name] = g2
            self.GAIT = gait

    # ----------------------------------------------------------- acting
    def sit(self, dur=2.0, look=0.0):
        """Sit: rump drops onto the hocks, chest upright, front legs straight."""
        return self._add("sit", dur=dur, look=look)

    def lie(self, dur=2.0, head_down=0.0, eyes=1.0, breath=1.0):
        """Lie down (sphinx): forelegs flat forward, hind legs folded. head_down 0..1 rests the
        chin on the snow; eyes 0..1; breath > 1 = heavy fast breathing (wounded, e.g. 2.5)."""
        return self._add("lie", dur=dur, head_down=head_down, eyes=eyes, breath=breath)

    def crouch(self, dur=1.0):
        """Crouch low on loaded haunches, head low and forward: the lunge anticipation."""
        return self._add("crouch", dur=dur)

    def lunge(self, to, dur=None, height=None, bite=False):
        """Spring forward to root x `to`: load, drive, flight, land fore-then-hind, absorb,
        recovery step. height: apex rise in px (default 0.3 S). bite=True snaps on landing.
        Lunges from a crouch skip most of the load."""
        return self._add("lunge", to=float(to), dur=dur, height=height, bite=bite)

    def leap(self, to, height=None, dur=None):
        """A big leap (default apex 0.85 S, stretched flight) - e.g. over the girl."""
        return self._add("lunge", to=float(to), dur=dur, height=height, big=True)

    def bite(self, dur=0.5, n=1):
        """n fast snaps of the jaws (head act, layers over the body action)."""
        return self._add("bite", dur=dur, n=n)

    def eyes(self, dur=1.0, open=1.0):
        """Open (open=1) or close (open=0) the eyes (head act; lie(eyes=0) starts closed)."""
        return self._add("eyes", dur=dur, open=open)

    def snarl(self, dur=2.0, ears=0.9):
        """Head low, jaw open with teeth, lips back, hackles up, growl tremor."""
        return self._add("snarl", dur=dur, ears=ears)

    def growl(self, dur=2.0):
        """A closed-mouth growl: head low, lips slightly back, hackles up, tremor."""
        return self._add("snarl", dur=dur, ears=0.5, amount=0.45)

    def howl(self, dur=3.0):
        """Head up to the sky, mouth rounded open, sustained with vibrato."""
        return self._add("howl", dur=dur)

    def look(self, dur=1.5, turn=55.0, head=None):
        """Turn the head toward the camera by `turn` deg (both eyes show past ~30)."""
        return self._add("look", dur=dur, turn=turn, head=head)

    def recoil(self, dur=0.9, dist=None):
        """Flinch backward: front end rises, head pulls back, ears flat, quick hop back."""
        return self._add("recoil", dur=dur, dist=dist)

    def _limp(self, P, phi, m):
        if not self.old:
            return
        # a front-leg limp: the head rises when the sore RF leg lands
        o = self.old * m
        c = math.cos(2 * math.pi * (phi - 0.80))
        P["head"] += 7.0 * o * c
        P["neck"] += 5.0 * o * c
        P["hf"] -= 0.012 * o * max(0.0, -c)

    # ----------------------------------------------------------- drawing
    def draw(self, f, t, ctx=None, color=None, eyes=True, far_shade=0.0, breath=False):
        """Draw the wolf at time t on ctx (a layer context; default f.ctx). color overrides
        the ink. far_shade (0..1) lifts the far-side legs toward the fog for readability.
        breath=True adds pale exhale puffs (for dark backgrounds)."""
        P = self.state(t)
        return draw_wolf(f, P, self, ctx, color=color, eyes=eyes, far_shade=far_shade, breath=breath)


# ----------------------------------------------------------------------------- wolf drawing
# Shapes in units of S (paw: relative to the toe tip, x forward, y up) and of the head
# length Lh (head: x along the muzzle from the head joint, y up).
_PAW = [(0.004, 0.004), (0.0, 0.020), (-0.012, 0.036), (-0.030, 0.044), (-0.040, 0.040),
        (-0.052, 0.050), (-0.072, 0.054), (-0.094, 0.050), (-0.108, 0.032), (-0.104, 0.010),
        (-0.082, -0.001), (-0.030, -0.002)]
_PAW_J = (-0.080, 0.047)

_HEAD_UP = [
    (1.000, 0.020), (0.986, 0.068), (0.930, 0.088), (0.78, 0.105), (0.64, 0.128),
    (0.54, 0.165), (0.44, 0.215), (0.30, 0.250), (0.14, 0.248), (0.02, 0.205),
    (-0.06, 0.11), (-0.07, -0.01), (0.03, -0.12), (0.20, -0.152), (0.33, -0.10),
    (0.45, -0.050), (0.70, -0.040), (0.90, -0.035), (0.985, -0.012),
]
_UP_LIP = 15                 # index of the mouth corner on the upper lip edge
_JAW = [(0.33, -0.030), (0.45, -0.026), (0.70, -0.022), (0.885, -0.024), (0.925, -0.052),
        (0.900, -0.090), (0.74, -0.106), (0.50, -0.122), (0.30, -0.122)]
_JAW_HINGE = (0.34, -0.06)
_EAR = [(0.29, 0.235), (0.235, 0.42), (0.150, 0.585), (0.115, 0.43), (0.075, 0.232)]
_EAR_PIV = (0.18, 0.24)
_EYE = (0.425, 0.152)

# torso outline: (s along the spine 0 = sacrum .. 1 = withers, offset along the up-normal in S)
_TORSO = [
    (-0.136, 0.035), (0.023, 0.070), (0.27, 0.055), (0.55, 0.050), (0.78, 0.070),
    (0.977, 0.100), (1.09, 0.085),                                   # 0-6 top line
    (1.20, -0.085), (1.25, -0.255), (1.18, -0.385),                  # 7-9 chest front
    (1.01, -0.425), (0.78, -0.43), (0.55, -0.39), (0.386, -0.335),
    (0.25, -0.29), (0.125, -0.295),                                  # 10-15 underline
    (-0.0125, -0.335), (-0.16, -0.245), (-0.193, -0.125), (-0.165, -0.015),   # 16-19 rump
]


def _locks(pts, n, seed, length, width, rake, t=0.0, side=1.0, jag=0.45, u0=0.0, u1=None,
           wob=0.10, skip=0.0):
    """Fur locks along a LOCAL (forward, up) polyline: curved flames whose base sits on the
    line and whose tip leans out (side=+1: left of the line direction) and along it
    (rake > 0 toward the end of the line). Deterministic per (seed, i), tips sway with t.
    length / width may be callables of the position v (0..1) along the run of locks.
    skip > 0 drops that fraction of locks (ragged old fur)."""
    m = len(pts) - 1
    if m < 1 or n <= 0:
        return []
    u1 = m if u1 is None else u1
    out = []
    for i in range(n):
        h1, h2, h3 = hash01(seed, i, 1), hash01(seed, i, 2), hash01(seed, i, 3)
        if skip and hash01(seed, i, 4) < skip:
            continue
        v = (i + 0.15 + 0.7 * h1) / n
        u = u0 + (u1 - u0) * v
        k = min(int(u), m - 1)
        fr = u - k
        a, b = pts[k], pts[k + 1]
        px, py = a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1.0
        tx, ty = tx / tl, ty / tl
        nx, ny = -ty * side, tx * side
        L = (length(v) if callable(length) else length) * (1.0 - jag + 2 * jag * h2)
        wd = (width(v) if callable(width) else width) * (0.75 + 0.5 * h3)
        rk = rake + wob * noise1(t * 1.1 + i * 0.73, seed + 17)
        ex, ey = px + (nx + tx * rk) * L, py + (ny + ty * rk) * L
        ins = 0.22 * L + 0.1 * wd        # sink the base into the body: no seam at the outline
        b0 = (px - tx * wd * 0.5 - nx * ins, py - ty * wd * 0.5 - ny * ins)
        b1 = (px + tx * wd * 0.5 - nx * ins, py + ty * wd * 0.5 - ny * ins)
        # convex leading edge: the side the tip leans away from
        lead = b1 if rk < 0 else b0
        trail = b0 if rk < 0 else b1
        cx = (lead[0] + ex) * 0.5 + nx * L * 0.16
        cy = (lead[1] + ey) * 0.5 + ny * L * 0.16
        out.append((trail, lead, (cx, cy), (ex, ey)))
    return out


def solve_quadruped(A, P):
    """Pose dict -> rig dict with LOCAL (forward, up) joints and a projector. Shared by the
    wolf and the cat drawers."""
    S, PR = A.S, A.PR
    rx = P["x"]
    ry = A.ground(rx)
    yaw = P["yaw"]
    bend = P.get("bend", 0.0)
    yF, yH = (yaw + bend) * D2R, (yaw - bend) * D2R
    cF, sF, cH, sH = math.cos(yF), math.sin(yF), math.cos(yH), math.sin(yH)
    chord = P["chord"] * PR["chord"] * S
    fW, fP = 0.5 * chord, -0.5 * chord
    xW, xP = rx + fW * cF, rx + fP * cH
    uW = ry - A.ground(xW) + P["hf"] * S
    uP = ry - A.ground(xP) + P["hh"] * S
    Wp, Pp = (fW, uW), (fP, uP)
    dx, dy = fW - fP, uW - uP
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    Cp = (0.5 * (fW + fP) + nx * P["arch"] * S, 0.5 * (uW + uP) + ny * P["arch"] * S)
    d0 = (2 * (Cp[0] - Pp[0]), 2 * (Cp[1] - Pp[1]))
    d1 = (2 * (Wp[0] - Cp[0]), 2 * (Wp[1] - Cp[1]))

    def spine(s):
        if s <= 0.0:
            return (Pp[0] + d0[0] * s, Pp[1] + d0[1] * s), d0
        if s >= 1.0:
            return (Wp[0] + d1[0] * (s - 1), Wp[1] + d1[1] * (s - 1)), d1
        return _bez2(Pp, Cp, Wp, s), (d0[0] + (d1[0] - d0[0]) * s, d0[1] + (d1[1] - d0[1]) * s)

    def body(s, off):
        p, d = spine(s)
        l = math.hypot(d[0], d[1]) or 1.0
        return (p[0] - d[1] / l * off * S, p[1] + d[0] / l * off * S)

    def frame(at, a, b):
        p, d = spine(at)
        l = math.hypot(d[0], d[1]) or 1.0
        tx, ty = d[0] / l, d[1] / l
        return (p[0] + (tx * a - ty * b) * S, p[1] + (ty * a + tx * b) * S)

    R = dict(S=S, rx=rx, ry=ry, cF=cF, sF=sF, cH=cH, sH=sH, W=Wp, P=Pp, spine=spine, body=body,
             frame=frame, fW=fW, fP=fP)
    # ---------------------------------------------------------------- legs
    legs = {}
    for k in LEGS:
        lg = P["legs"][k]
        front = _FRONT[k]
        c, s_ = (cF, sF) if front else (cH, sH)
        dxw = lg[0] - rx
        f_t = dxw * c + lg[2] * s_
        l_t = dxw * s_ - lg[2] * c
        u_t = ry - lg[1]
        pa, fold, aov = lg[3], lg[4], lg[5]
        ca, sa = math.cos(pa * D2R), math.sin(pa * D2R)
        ps = PR["paw"] / 0.115
        jx, jy = _PAW_J[0] * S * ps, _PAW_J[1] * S * ps
        J = (f_t + jx * ca + jy * sa, u_t - jx * sa + jy * ca)
        a0, kh, af = A.ALPHA[front]
        alpha = a0 + kh * min(pa, A.HEEL) * (1.0 - fold) + (af - a0) * fold + aov
        lg_ = _LEFT[k] * PR["lw_f" if front else "lw_h"] * S
        if front:
            piv = frame(1.0, PR["scap_piv"][0], PR["scap_piv"][1])
            dmc = _down(alpha)
            wr = (J[0] - dmc[0] * PR["mc"] * S, J[1] - dmc[1] * PR["mc"] * S)
            th = _ang_down((wr[0] - piv[0], wr[1] - piv[1]))
            ths = PR["scap0"] + PR["scap_k"] * th
            dsc = _down(ths)
            sh = (piv[0] + dsc[0] * PR["scap"] * S, piv[1] + dsc[1] * PR["scap"] * S)
            wr, alpha = _reach_distal(sh, J, PR["mc"] * S, alpha, (PR["hum"] + PR["rad"]) * S)
            el, wr2 = _ik2(sh, wr, PR["hum"] * S, PR["rad"] * S, -1)
            ox, oy = wr2[0] - wr[0], wr2[1] - wr[1]
            J2 = (J[0] + ox, J[1] + oy)
            toe = (f_t + ox, u_t + oy)
            legs[k] = dict(front=True, j=[piv, sh, el, wr2, J2, toe], pa=pa, lt=l_t, lg=lg_,
                           c=c, s=s_, alpha=alpha)
        else:
            hip = frame(0.0, PR["hipj"][0], PR["hipj"][1])
            hk, alpha = _reach_distal(hip, J, PR["mt"] * S, alpha, (PR["fem"] + PR["tib"]) * S)
            st, hk2 = _ik2(hip, hk, PR["fem"] * S, PR["tib"] * S, +1)
            ox, oy = hk2[0] - hk[0], hk2[1] - hk[1]
            J2 = (J[0] + ox, J[1] + oy)
            toe = (f_t + ox, u_t + oy)
            legs[k] = dict(front=False, j=[hip, st, hk2, J2, toe], pa=pa, lt=l_t, lg=lg_,
                           c=c, s=s_, alpha=alpha)
    R["legs"] = legs
    # ---------------------------------------------------------------- neck / head
    nb = body(*PR["neck_base"])
    th = P["neck"] * D2R
    Ln = PR["neck"] * S
    H0 = (nb[0] + math.cos(th) * Ln, nb[1] + math.sin(th) * Ln)
    R["neck0"], R["H0"] = nb, H0
    sgn = 1.0 if cF >= 0 else -1.0
    yh = yF + sgn * P.get("hturn", 0.0) * D2R
    R["ch"], R["sh"] = math.cos(yh), math.sin(yh)
    hp = P["head"] * D2R
    R["hc"], R["hs"] = math.cos(hp), math.sin(hp)
    return R


def _proj_fn(R, yaw_mode):
    rx, ry = R["rx"], R["ry"]
    if yaw_mode == "F":
        c, s = R["cF"], R["sF"]
    elif yaw_mode == "H":
        c, s = R["cH"], R["sH"]
    else:
        fP, fW = R["fP"], R["fW"]
        cF, sF, cH, sH = R["cF"], R["sF"], R["cH"], R["sH"]
        span = (fW - fP) or 1.0

        def pr(p, l=0.0):
            w = clamp((p[0] - fP) / span)
            c_ = cH + (cF - cH) * w
            s_ = sH + (sF - sH) * w
            return (rx + p[0] * c_ + l * s_, ry - p[1])
        return pr

    def pr(p, l=0.0):
        return (rx + p[0] * c + l * s, ry - p[1])
    return pr


def _head_pts(R, pts, Lh, ox=0.0, oy=0.0, rot=None, hl=0.0):
    """Head-local points (Lh units, x along the muzzle, y up) -> world, through the head
    pitch and head yaw. rot=(cx, cy, c, s) rotates the points first about (cx, cy)."""
    H0 = R["H0"]
    hc, hs = R["hc"], R["hs"]
    ch, sh = R["ch"], R["sh"]
    rx, ry = R["rx"], R["ry"]
    # project the head joint with the front yaw
    hx0 = rx + H0[0] * R["cF"]
    hy0 = ry - H0[1]
    out = []
    for x, y in pts:
        x += ox
        y += oy
        if rot is not None:
            cx, cy, c, s = rot
            x, y = cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c
        f = (x * hc - y * hs) * Lh
        u = (x * hs + y * hc) * Lh
        out.append((hx0 + f * ch + hl * Lh * sh, hy0 - u))
    return out


def _leg_pts(R, L, prF, prH):
    pr = prF if L["front"] else prH
    js = L["j"]
    lg, lt = L["lg"], L["lt"]
    n = len(js)
    return [pr(p, lg + (lt - lg) * (i / (n - 1)) ** 2) for i, p in enumerate(js)], pr


def _paw_shape(toe, pa, S, ps, pr, lt):
    ca, sa = math.cos(pa * D2R), math.sin(pa * D2R)
    out = []
    for a_, b_ in _PAW:
        a_ *= S * ps
        b_ *= S * ps
        out.append(pr((toe[0] + a_ * ca + b_ * sa, toe[1] - a_ * sa + b_ * ca), lt))
    return out


def _limb_outline(js, specs, S, k=1.0):
    """Outline of a limb chain in LOCAL (forward, up) coords. specs: [(seg, t, front_w,
    back_w), ...] from the top down (widths in S). 'Front' is the left normal of the chain
    direction, which is the anatomical front of a leg hanging down (and stays anatomical
    when a segment folds). At joints (t = 0 / 1) the normal bisects the two bones."""
    dirs = []
    for i in range(len(js) - 1):
        a, b = js[i], js[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy) or 1.0
        dirs.append((dx / l, dy / l))
    F, B = [], []
    nseg = len(dirs)
    for seg, tt, fw, bw in specs:
        a, b = js[seg], js[seg + 1]
        p = (a[0] + (b[0] - a[0]) * tt, a[1] + (b[1] - a[1]) * tt)
        d = dirs[seg]
        if tt <= 0.0 and seg > 0:
            q = dirs[seg - 1]
            d = (d[0] + q[0], d[1] + q[1])
        elif tt >= 1.0 and seg + 1 < nseg:
            q = dirs[seg + 1]
            d = (d[0] + q[0], d[1] + q[1])
        l = math.hypot(d[0], d[1]) or 1.0
        nx, ny = -d[1] / l, d[0] / l
        F.append((p[0] + nx * fw * S * k, p[1] + ny * fw * S * k))
        B.append((p[0] - nx * bw * S * k, p[1] - ny * bw * S * k))
    return F + B[::-1]


# (segment, t, front half-width, back half-width) in S, top -> bottom
_FORE_SPEC = [(1, 0.0, 0.09, 0.08), (1, 0.55, 0.075, 0.08), (2, 0.0, 0.052, 0.080),
              (2, 0.14, 0.049, 0.056), (2, 0.5, 0.040, 0.037), (2, 0.88, 0.032, 0.031),
              (3, 0.0, 0.033, 0.041), (3, 0.35, 0.029, 0.028), (3, 1.0, 0.028, 0.026)]
_HIND_SPEC = [(0, -0.15, 0.09, 0.12), (0, 0.30, 0.122, 0.15), (0, 0.72, 0.095, 0.13),
              (1, 0.0, 0.054, 0.112), (1, 0.30, 0.048, 0.084), (1, 0.66, 0.038, 0.052),
              (1, 0.93, 0.032, 0.058), (2, 0.0, 0.030, 0.033), (2, 0.25, 0.028, 0.028),
              (2, 1.0, 0.027, 0.026)]


_LEG_R = {True: (0.0, 0.07, 0.042, 0.03, 0.03), False: (0.10, 0.055, 0.03, 0.03)}


def _wolf_leg(ctx, R, L, S, PR, thin, pr_fn, paws, caps=None):
    """Add one leg's outline as its own sub-path; the paw goes to `paws`. When the girdle is
    yawed, capsules giving the leg its lateral thickness go to `caps`."""
    js = L["j"]
    lg, lt = L["lg"], L["lt"]
    n = len(js)
    spec = _FORE_SPEC if L["front"] else _HIND_SPEC
    loc = _limb_outline(js, spec, S, thin)
    # lateral position along the outline: interpolate girdle -> paw by height
    u0, u1 = js[0][1], js[-1][1]
    span = (u0 - u1) or 1.0
    out = []
    for p in loc:
        w = clamp((u0 - p[1]) / span)
        out.append(pr_fn(p, lg + (lt - lg) * w * w))
    _smooth(ctx, out, 0.5)
    ps = PR["paw"] / 0.115
    paws.append(_paw_shape(js[-1], L["pa"], S, ps, pr_fn, lt))
    sa = abs(L["s"])
    if caps is not None and sa > 0.04:
        rr = _LEG_R[L["front"]]
        w = [pr_fn(p, lg + (lt - lg) * clamp((u0 - p[1]) / span) ** 2) for p in js]
        for i in range(len(js) - 1):
            r = rr[i] * S * thin * sa
            if r > 0.5:
                caps.append((w[i], w[i + 1], r * 1.1, r))


def draw_wolf(f, P, A, ctx=None, color=None, eyes=True, far_shade=0.0, breath=False):
    """Draw a wolf pose dict P (from Wolf.state) on ctx. Returns the solved rig."""
    ctx = ctx if ctx is not None else f.ctx
    pal = f.pal if f is not None else None
    ink = color or (pal.ink if pal is not None else (0.0, 0.0, 0.0))
    R = solve_quadruped(A, P)
    S, PR = A.S, A.PR
    t = P["t"]
    old = A.old
    thin = 1.0 - 0.10 * old
    prM = _proj_fn(R, "M")
    prF = _proj_fn(R, "F")
    prH = _proj_fn(R, "H")
    body = R["body"]
    wind = P.get("wind", 0.0)
    ruff = P.get("ruff", 0.0)
    rag = 1.0 + 0.5 * old
    skip = 0.3 * old
    side_w = max(abs(R["sF"]), abs(R["sH"]))        # 0 in profile .. 1 facing the camera
    seed = A.seed * 131
    locks = []          # local-space fur, projected with the mid projector
    # depth order of the legs: z = -l*cos(yaw); far legs first
    order = sorted(LEGS, key=lambda k: P["legs"][k][2])
    far_col = lerp(ink, pal.fog_at(0.5), clamp(far_shade)) if (far_shade > 0 and pal is not None) else ink
    for i, k in enumerate(order):
        L = R["legs"][k]
        paws = []
        caps = []
        _wolf_leg(ctx, R, L, S, PR, thin, prF if L["front"] else prH, paws, caps)
        draw.fill(ctx, far_col if i < 2 else ink)
        for pw in paws:
            _poly(ctx, pw)
        draw.fill(ctx, far_col if i < 2 else ink)
        for a_, b_, ra_, rb_ in caps:
            draw.capsule(ctx, a_, b_, ra_, rb_)
            draw.fill(ctx, far_col if i < 2 else ink)
        # feathering behind the forearm / hock
        js = L["j"]
        if L["front"]:
            q = _locks([js[2], (js[2][0] * 0.55 + js[3][0] * 0.45, js[2][1] * 0.55 + js[3][1] * 0.45)], 2,
                       seed + 50 + i, 0.045 * S * rag, 0.045 * S, 1.2, t, side=-1.0, u0=0.1, u1=0.9)
            for tri in q:
                _poly(ctx, [(prF if L["front"] else prH)(pp) for pp in tri])
            draw.fill(ctx, far_col if i < 2 else ink)
    # ---------------------------------------------------------------- torso
    tor = []
    bk = 1.0 + 0.014 * P.get("breath", 0.0)
    for i, (s_, off) in enumerate(_TORSO):
        if 8 <= i <= 12:
            off *= bk * (1.0 - 0.04 * old)
        elif 13 <= i <= 15:
            off *= 1.0 - 0.10 * old
        tor.append(body(s_, off))
    if old:
        tor[1] = body(0.023, 0.070 + 0.02 * old)      # bony hip point
        tor[2] = body(0.27, 0.055 - 0.016 * old)      # sunken loin
    _smooth(ctx, [prM(p) for p in tor], 0.5)
    draw.fill(ctx, ink)
    if side_w > 0.03:          # lateral mass while turning (shaggy edged)
        for j_, (s_, up, dn, wd, sy) in enumerate(((1.0, 0.09, -0.45, 0.21, "F"), (0.6, 0.06, -0.43, 0.20, "F"),
                                                   (0.25, 0.06, -0.30, 0.15, "H"), (-0.05, 0.07, -0.30, 0.18, "H"))):
            pa_, pb_ = body(s_, up), body(s_, dn)
            ctr = prM(((pa_[0] + pb_[0]) * 0.5, (pa_[1] + pb_[1]) * 0.5))
            rx_, ry_ = wd * S * abs(R["s" + sy]) + 1.0, abs(pa_[1] - pb_[1]) * 0.5
            draw.ellipse(ctx, ctr, rx_ * 0.92, ry_ * 0.95)
            draw.fill(ctx, ink)
            if rx_ > 0.04 * S:
                ring = [(ctr[0] + rx_ * 0.9 * math.cos(a_), ctr[1] + ry_ * 0.92 * math.sin(a_))
                        for a_ in [-2 * math.pi * q / 14 for q in range(15)]]
                for q in _locks(ring, 12, seed + 70 + j_, 0.07 * S * min(1.0, rx_ / (0.12 * S)), 0.09 * S,
                                0.6, t, side=1.0):
                    _poly(ctx, q)
                draw.fill(ctx, ink)
    # ---------------------------------------------------------------- neck
    nb, H0 = R["neck0"], R["H0"]
    vx, vy = H0[0] - nb[0], H0[1] - nb[1]
    vl = math.hypot(vx, vy) or 1.0
    nnx, nny = -vy / vl, vx / vl
    if nny < 0:
        nnx, nny = -nnx, -nny
    ctrl = ((nb[0] + H0[0]) * 0.5 + nnx * 0.04 * S, (nb[1] + H0[1]) * 0.5 + nny * 0.04 * S)
    ntop, nbot, naxis = [], [], []
    nflat = clamp(-P["neck"] / 35.0)
    for i in range(6):
        v = i / 5.0
        p = _bez2(nb, ctrl, H0, v)
        naxis.append(p)
        wt = (0.225 - 0.13 * v + 0.02 * math.sin(math.pi * v) + 0.06 * nflat * (1 - v)) * S
        wb = (0.215 - 0.10 * v) * S
        ntop.append((p[0] + nnx * wt, p[1] + nny * wt))
        nbot.append((p[0] - nnx * wb, p[1] - nny * wb))
    draw.fill(ctx, ink)
    ext = (H0[0] + vx / vl * 0.07 * S, H0[1] + vy / vl * 0.07 * S)
    _smooth(ctx, [prF(p) for p in ntop + [ext] + nbot[::-1]], 0.5)
    draw.fill(ctx, ink)
    if side_w > 0.03:
        for i in (1, 3, 5):
            draw.ellipse(ctx, prF(naxis[i]), (0.18 - 0.08 * i / 5) * S * abs(R["sF"]) + 1,
                         (0.20 - 0.09 * i / 5) * S)
    # ---------------------------------------------------------------- head
    Lh = PR["head"] * S
    jaw = clamp(P.get("jaw", 0.0))
    snarl = clamp(P.get("snarl", 0.0))
    up = list(_HEAD_UP)
    tk = 0.8 + 0.4 * snarl
    if snarl > 0.01:          # wrinkled muzzle bridge
        up[3] = (0.80, 0.105 + 0.024 * snarl)
        up.insert(4, (0.735, 0.110 - 0.006 * snarl))
        up.insert(5, (0.70, 0.124 + 0.016 * snarl))
    draw.fill(ctx, ink)
    _smooth(ctx, _head_pts(R, up, Lh), 0.42)
    draw.fill(ctx, ink)
    ja = -jaw * 40.0 * D2R
    jrot = (_JAW_HINGE[0], _JAW_HINGE[1], math.cos(ja), math.sin(ja))
    _smooth(ctx, _head_pts(R, _JAW, Lh, rot=jrot), 0.4)
    draw.fill(ctx, ink)
    if jaw > 0.02:
        # teeth: upper ones hang from the lip, lower ones stand on the jaw (separate triangles)
        for x0, x1, h in ((0.50, 0.56, 0.05), (0.58, 0.645, 0.055), (0.80, 0.865, 0.085 + 0.03 * snarl),
                          (0.875, 0.915, 0.04)):
            xm = (x0 + x1) * 0.5
            _poly(ctx, _head_pts(R, [(x0, -0.03), (xm, -0.035 - h * tk), (x1, -0.03)], Lh))
        for x0, x1, h in ((0.56, 0.62, 0.04), (0.79, 0.85, 0.07 + 0.02 * snarl), (0.86, 0.90, 0.035)):
            xm = (x0 + x1) * 0.5
            _poly(ctx, _head_pts(R, [(x0, -0.06), (xm, -0.048 + h * tk), (x1, -0.06)], Lh, rot=jrot))
        draw.fill(ctx, ink)
    ears = P.get("ears", 0.3)
    er = (ears - 0.3) * 22.0 if ears >= 0.0 else -6.6 + ears * 60.0
    for ei, (dx_, dl_) in enumerate(((0.045, 0.10), (0.0, -0.10))):
        ang = (er + (5.0 if ei == 0 else 0.0)) * D2R
        rot = (_EAR_PIV[0], _EAR_PIV[1], math.cos(-ang), math.sin(-ang))
        _poly(ctx, _head_pts(R, _EAR, Lh, ox=dx_, rot=rot, hl=dl_))
    draw.fill(ctx, ink)
    if abs(R["sh"]) > 0.03:
        for (hx, hy, w_, h_) in ((0.15, 0.07, 0.21, 0.18), (0.40, 0.09, 0.16, 0.13),
                                 (0.65, 0.05, 0.09, 0.085), (0.86, 0.03, 0.07, 0.07)):
            ctr = _head_pts(R, [(hx, hy)], Lh)[0]
            draw.ellipse(ctx, ctr, w_ * Lh * abs(R["sh"]) + 1.0, h_ * Lh)
    # ---------------------------------------------------------------- tail
    tb = body(-0.15, 0.0)
    _, dsp = R["spine"](0.0)
    base_ang = math.atan2(-dsp[1], -dsp[0])
    dba = (base_ang - math.pi + math.pi) % (2 * math.pi) - math.pi
    a = math.pi - P["tail"] * D2R + dba * 0.4       # (f, u) angle: pi = straight back
    nseg = 8
    Lt = PR["tail"] * S * (1 - 0.1 * old)
    seg = Lt / nseg
    pts = [tb]
    sw = P.get("tsway", 1.0)
    droop = (1.0 - wind) * (P.get("tcurve", 5.0) * 10.0 + 4.0) * D2R
    ph = hash01(A.seed, 41)
    for i in range(nseg):
        v = (i + 0.5) / nseg
        # gravity bends the free part toward hanging; wind streams it out behind
        a_i = min(a + droop * v ** 1.15, 1.5 * math.pi + 0.08)
        wav = sw * 5.0 * D2R * math.sin(2 * math.pi * (t * 0.37 + ph) - 1.3 * v) * v
        wav += wind * 6.0 * D2R * math.sin(2 * math.pi * (t * 2.2 + ph) - 2.6 * v) * v
        p = pts[-1]
        q = (p[0] + math.cos(a_i + wav) * seg, p[1] + math.sin(a_i + wav) * seg)
        ug = R["ry"] - A.ground(R["rx"] + q[0] * R["cH"]) + 0.035 * S
        if q[1] < ug:        # resting on the snow: the rest of the tail lies along it
            q = (p[0] - 0.985 * seg * (1.0 if R["cH"] * R["cH"] > 0.0 else 1.0), max(ug, p[1] - 0.17 * seg))
        pts.append(q)
    wid = []
    for i in range(len(pts)):
        v = i / (len(pts) - 1)
        w_ = (0.030 + 0.060 * math.sin(math.pi * min(1.0, v * 0.95) ** 0.7)) * S * (1 - 0.3 * old)
        if v > 0.8:
            w_ *= 1.0 - (v - 0.8) / 0.2 * 0.85
        wid.append(2 * w_)
    rib = draw.ribbon(pts, wid)
    draw.fill(ctx, ink)
    _smooth(ctx, [prH(p) for p in rib], 0.5)
    draw.fill(ctx, ink)
    n_ = len(pts)
    left_e, right_e = rib[:n_], rib[n_:][::-1]
    tl_ = []
    tl_ += _locks(left_e, 7, seed + 8, lambda v: (0.03 + 0.03 * math.sin(math.pi * v)) * S * rag,
                  0.08 * S, 1.6, t, side=1.0, u0=0.6, u1=n_ - 1.6, skip=skip)
    tl_ += _locks(right_e, 7, seed + 9, lambda v: (0.03 + 0.03 * math.sin(math.pi * v)) * S * rag,
                  0.08 * S, 1.6, t, side=-1.0, u0=0.6, u1=n_ - 1.4, skip=skip)
    for q in tl_:
        _poly(ctx, [prH(p) for p in q])
    # ---------------------------------------------------------------- fur
    hk = 1.0 + 0.8 * ruff
    flat = clamp(-P["neck"] / 35.0)          # neck down (lying, stalking): the mane lies flat
    mk = (1 + 0.25 * ruff) * (1.0 - 0.8 * flat) * (1.0 - 0.15 * wind)
    locks += _locks(ntop, 8, seed + 1,
                    lambda v: (0.065 + 0.05 * math.sin(math.pi * min(1.0, v * 1.1))) * S * rag * mk,
                    0.15 * S, -1.8 - 1.3 * wind + 0.45 * ruff - 0.6 * flat, t, side=1.0, u0=0.2, u1=4.6,
                    skip=skip)
    locks += _locks(nbot, 6, seed + 2, lambda v: (0.05 + 0.05 * (1 - v)) * S * rag * (1 + 0.1 * ruff),
                    0.12 * S, -1.5 - 0.3 * wind, t, side=-1.0, u0=0.5, u1=4.8, skip=skip)
    top = tor[0:6]
    locks += _locks(top, 7, seed + 3,
                    lambda v: (0.018 + 0.016 * v + 0.04 * ruff * _ss(0.45, 0.95, v)) * S * rag,
                    0.10 * S, -2.2 - 0.5 * wind + 0.6 * ruff, t, side=1.0, u0=0.4, u1=5.0, skip=skip)
    locks += _locks(tor[9:16], 6, seed + 4, lambda v: (0.045 - 0.02 * v) * S * rag, 0.10 * S,
                    1.7 + 0.4 * wind, t, side=1.0, u0=0.6, u1=5.4, skip=skip)
    locks += _locks(tor[7:10], 3, seed + 5, 0.05 * S * rag, 0.10 * S, 1.2, t, side=1.0, skip=skip)
    locks += _locks(tor[16:20], 3, seed + 6, 0.045 * S * rag, 0.09 * S, 1.2, t, side=1.0, u0=0.5,
                    u1=2.5, skip=skip)
    cheek = [(0.00, 0.20), (-0.07, 0.10), (-0.075, -0.02), (0.03, -0.125), (0.19, -0.155)]
    chk = []
    hc, hs = R["hc"], R["hs"]
    for x_, y_ in cheek:
        chk.append((H0[0] + (x_ * hc - y_ * hs) * Lh, H0[1] + (x_ * hs + y_ * hc) * Lh))
    locks += _locks(chk, 6, seed + 7,
                    lambda v: (0.05 + 0.045 * math.sin(math.pi * v)) * S * rag * (1 + 0.15 * ruff),
                    0.09 * S, 1.1, t, side=-1.0, u0=0.3, u1=3.9, skip=skip)
    for q in locks:
        _poly(ctx, [prM(p) for p in q])
    draw.fill(ctx, ink)
    # ---------------------------------------------------------------- grey muzzle (old)
    if old > 0.01 and pal is not None:
        grey = lerp(ink, pal.fog_at(0.6), 0.32 * old)
        _smooth(ctx, _head_pts(R, [(0.52, 0.17), (0.78, 0.105), (0.99, 0.066), (1.0, 0.02),
                                   (0.95, -0.03), (0.70, -0.04), (0.50, -0.05), (0.46, 0.06)], Lh), 0.5)
        _smooth(ctx, _head_pts(R, [(0.60, -0.046), (0.885, -0.044), (0.925, -0.06), (0.74, -0.104),
                                   (0.56, -0.115)], Lh, rot=jrot), 0.5)
        g0 = _head_pts(R, [(0.48, 0.0)], Lh)[0]
        g1 = _head_pts(R, [(0.95, 0.0)], Lh)[0]
        draw.linear(ctx, g0, g1, [(0.0, ink, 1.0), (0.6, grey, 1.0), (1.0, grey, 1.0)])
        ctx.fill()
    if eyes:
        _wolf_eyes(f, R, P, A, ctx, Lh)
    if breath and pal is not None:
        _breath_puffs(f, R, P, A, ctx, Lh)
    return R


def _wolf_eyes(f, R, P, A, ctx, Lh, col=(1.0, 1.0, 0.97)):
    front = R["sh"]
    if front < -0.35:
        return
    op = clamp(P.get("eopen", 1.0))
    # blink: quick lid closures at hashed moments
    t = P["t"]
    k = math.floor(t / 2.7)
    tb = k * 2.7 + 2.7 * hash01(A.seed, k, 77)
    if hash01(A.seed, k, 78) < 0.6 and 0.0 <= t - tb < 0.16:
        op *= abs(math.cos((t - tb) / 0.16 * math.pi))
    glow = clamp(P.get("eglow", 1.0)) * (clamp((front + 0.35) / 0.35) if front < 0 else 1.0)
    if op <= 0.02 or glow <= 0.01:
        return
    r = 0.030 * Lh
    ex, ey = _EYE
    snarl = P.get("snarl", 0.0)
    near = _head_pts(R, [(ex, ey)], Lh, hl=-0.085 if R["cF"] >= 0 else 0.085)[0]
    farp = _head_pts(R, [(ex, ey)], Lh, hl=0.085 if R["cF"] >= 0 else -0.085)[0]
    vis_far = _ss(0.22, 0.5, front)
    ang = math.degrees(math.atan2(-(R["hs"]), R["hc"] * (1 if R["cF"] >= 0 else -1)))
    es = [(near, 1.0)]
    if vis_far > 0.01:
        es.append((farp, vis_far))
    sq = 1.0 - 0.35 * snarl
    for e, v in es:
        draw.ellipse(ctx, e, r * 1.15, r * op * sq * 0.85, ang - 8 * (1 if R["cF"] >= 0 else -1))
        draw.fill(ctx, col, glow * v)
    if f is not None:
        with f.emit() as G:
            for e, v in es:
                draw.glow_disc(G, e, r * 6.0, col, 0.55 * glow * op * v)


def _breath_puffs(f, R, P, A, ctx, Lh):
    """Pale exhale puffs from the nose (only reads on darker backgrounds)."""
    t = P["t"]
    per = A.BREATH * (0.45 if P.get("speed", 0.0) > 0.5 else 1.0)
    ph = (t / per + hash01(A.seed, 3)) % 1.0
    if ph > 0.55:
        return
    nose = _head_pts(R, [(1.04, -0.02)], Lh)[0]
    dirx = 1.0 if R["cF"] >= 0 else -1.0
    col = f.pal.fog_at(1.0)
    for i in range(3):
        u = ph / 0.55
        a = (1.0 - u) * 0.22 * (1.0 - 0.25 * i)
        rr = (0.03 + 0.10 * u + 0.03 * i) * A.S
        c = (nose[0] + dirx * (0.05 + 0.25 * u + 0.05 * i) * A.S, nose[1] + (0.02 + 0.06 * u - 0.03 * i) * A.S)
        draw.radial(ctx, c, 0, rr, [(0, col, a), (1, col, 0.0)])
        ctx.arc(c[0], c[1], rr, 0, 2 * math.pi)
        ctx.fill()


Wolf.CLIPS = {"stand": _QStand, "sit": _QSit, "lie": _QLie, "crouch": _QCrouch, "turn": _QTurn,
              "recoil": _QRecoil, "lunge": _QLunge, "snarl": _QSnarl, "howl": _QHowl,
              "look": _QLook, "bite": _QBite, "eyes": _QEyes}
