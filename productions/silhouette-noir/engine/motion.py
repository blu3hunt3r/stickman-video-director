"""Motion: footstep-planned gaits (feet never slide), an Actor timeline for performing
characters, keyframe channels, arm IK (reach) and look-at.

    from engine.motion import Actor
    a = Actor(Body.child(), look, x=200, ground=1500)          # ground: y or fn(x) -> y
    a.stand(1.0).walk(to=760).stand(0.6).turn().run(to=-200, speed=2.1)
    a.arm("R", 2.0, 4.5, sh=70, elbow=40)                       # pose overlay with fades
    a.key("head", [(3.0, 0), (3.4, 18, "out3"), (5.0, 18), (5.5, 0)], mode="add")
    a.reach("L", 6.0, 7.5, target=lambda t: rope_point(t))      # arm IK to a world point
    a.draw(f, t, L)                                             # solve + draw the silhouette

All times are scene seconds. Positions are world px. A Gait's lengths are fractions of
body height and its speeds are body heights per second, so one gait suits every body.
"""
import bisect
import math

from . import figure as F
from .core import clamp, lerp, ease, smoothstep, noise1, wrap_angle, Track

D2R = math.pi / 180.0
HEEL_F, BALL_F, SOLE_U = 0.036, 0.104, 0.043      # foot geometry (fractions of height)


# ----------------------------------------------------------------------------- gaits
class Gait:
    FIELDS = dict(
        step=0.40,          # step length (footfall to footfall), fraction of height
        speed=0.62,         # default speed, heights per second
        duty=0.62,          # stance fraction of a stride (2 steps); < 0.5 -> flight phase
        strike=0.5,         # touchdown foot is strike*step ahead of the pelvis
        lift=0.055,         # swing clearance, fraction of height
        bob=0.010,          # pelvis bob amplitude, fraction of height
        bob_phase=0.0,      # where in the step the pelvis is lowest (0 = touchdown)
        crouch=0.012,       # pelvis lowered from full standing height, fraction of height
        lean=3.0,           # trunk pitch forward, degrees
        spine=0.0,          # extra upper-back bend (hunch), degrees
        head_comp=0.6,      # head counter-pitch as a fraction of the lean
        arm_swing=14.0,     # shoulder swing amplitude, degrees
        arm_bias=-2.0,      # mean shoulder angle
        elbow=14.0,         # base elbow flexion
        elbow_swing=12.0,   # extra elbow flexion when the arm swings forward
        abd=5.0,            # arm abduction
        grip=0.3,
        heel=14.0,          # touchdown pitch (toes up), degrees
        toe_off=32.0,       # lift-off pitch (heel up), degrees
        heel_off=0.62,      # fraction of stance when the heel starts to rise
        flat=0.16,          # fraction of stance to roll from heel to flat foot
        knee_lift=0.0,      # extra swing-foot height early in swing (heel kick / high knees)
        swing_lead=0.0,     # 0 = cycloid swing (walk), 1 = linear (the foot leaves the ground fast)
    )
    RAMP = dict(ramp_in=(0.72,), ramp_out=(0.78,))

    def __init__(self, name, ramp_in=None, ramp_out=None, **kw):
        self.name = name
        for k, v in self.FIELDS.items():
            setattr(self, k, kw.pop(k, v))
        if kw:
            raise TypeError("unknown gait fields: %s" % sorted(kw))
        self.ramp_in = tuple(ramp_in) if ramp_in is not None else self.RAMP["ramp_in"]
        self.ramp_out = tuple(ramp_out) if ramp_out is not None else self.RAMP["ramp_out"]

    def but(self, **kw):
        """Copy with some fields changed: GAITS['walk'].but(speed=0.5, lean=8)."""
        g = Gait(self.name, self.ramp_in, self.ramp_out, **{k: getattr(self, k) for k in self.FIELDS})
        for k, v in kw.items():
            setattr(g, k, v)
        return g

    @staticmethod
    def mix(a, b, u):
        if u <= 0:
            return a
        if u >= 1:
            return b
        g = a.but()
        for k in Gait.FIELDS:
            setattr(g, k, lerp(getattr(a, k), getattr(b, k), u))
        return g


GAITS = {
    "walk": Gait("walk"),
    "stroll": Gait("stroll", step=0.33, speed=0.42, arm_swing=11, lean=1.5, bob=0.008, heel=10, toe_off=24),
    "brisk": Gait("brisk", step=0.46, speed=0.88, arm_swing=26, elbow=20, lean=5, bob=0.012, heel=16,
                  toe_off=36),
    "sneak": Gait("sneak", step=0.34, speed=0.30, duty=0.72, crouch=0.075, lean=20, head_comp=0.85,
                  lift=0.07, arm_swing=6, arm_bias=12, elbow=55, elbow_swing=6, heel=4, toe_off=18,
                  heel_off=0.7, bob=0.005, ramp_in=(0.6,), ramp_out=(0.7,)),
    "run": Gait("run", step=0.74, speed=1.9, duty=0.34, strike=0.20, lift=0.10, knee_lift=0.16, swing_lead=0.55,
                bob=0.016, bob_phase=0.35, crouch=0.015, lean=14, head_comp=0.7, arm_swing=42,
                arm_bias=-10, elbow=78, elbow_swing=18, heel=6, toe_off=42, heel_off=0.3, flat=0.2,
                ramp_in=(0.45, 0.68, 0.88), ramp_out=(0.88, 0.66, 0.45)),
    "sprint": Gait("sprint", step=0.90, speed=2.6, duty=0.32, strike=0.15, lift=0.12, knee_lift=0.22, swing_lead=0.6,
                   bob=0.022, bob_phase=0.35, crouch=0.035, lean=16, head_comp=0.7, arm_swing=52,
                   arm_bias=-10, elbow=82, elbow_swing=16, heel=4, toe_off=48, heel_off=0.25, flat=0.2,
                   ramp_in=(0.4, 0.6, 0.8, 0.92), ramp_out=(0.9, 0.7, 0.5, 0.36)),
    "child_walk": Gait("child_walk", step=0.42, speed=0.78, arm_swing=22, bob=0.014, lean=2, heel=12),
    "child_run": Gait("child_run", step=0.78, speed=2.1, duty=0.34, strike=0.2, lift=0.11, knee_lift=0.16, swing_lead=0.55,
                      bob=0.020, bob_phase=0.35, crouch=0.016, lean=12, arm_swing=46, arm_bias=-8, elbow=70,
                      elbow_swing=20, heel=6, toe_off=40, heel_off=0.3, flat=0.2,
                      ramp_in=(0.45, 0.7, 0.9), ramp_out=(0.85, 0.62, 0.42)),
    "old": Gait("old", step=0.27, speed=0.32, lean=12, spine=10, crouch=0.035, arm_swing=6, elbow=26,
                lift=0.03, heel=6, toe_off=14, bob=0.004, head_comp=0.4),
    "heavy": Gait("heavy", step=0.30, speed=0.30, duty=0.68, lift=0.075, knee_lift=0.03, lean=9,
                  crouch=0.028, arm_swing=14, arm_bias=8, elbow=34, elbow_swing=10, bob=0.007, heel=8,
                  toe_off=16, heel_off=0.7),
    "trudge": Gait("trudge", step=0.30, speed=0.40, duty=0.66, lift=0.10, knee_lift=0.08, lean=12,
                   crouch=0.03, arm_swing=22, elbow=30, bob=0.012, heel=4, toe_off=26),
}


def gait(g):
    return GAITS[g] if isinstance(g, str) else g


# ----------------------------------------------------------------------------- helpers
def _ground_fn(ground):
    if callable(ground):
        return ground
    gy = float(ground)
    return lambda x: gy


def _slope(g, x, d, H):
    """Ground pitch (degrees, + = rising in the walking direction d)."""
    e = 0.03 * H
    return math.degrees(math.atan2(-(g(x + d * e) - g(x - d * e)), 2 * e))


def _rot(f, u, th):
    c, s = math.cos(th), math.sin(th)
    return f * c - u * s, f * s + u * c


def foot_ik(xa, theta, contact, d, H, g):
    """Ankle world position + total pitch for a foot whose flat-ankle x is xa, rolled by
    theta (deg; + toes up about the heel, - heel up about the ball) on ground g."""
    ths = _slope(g, xa, d, H) * D2R
    th = theta * D2R
    cy = g(xa)
    if contact == "heel" and theta > 0:
        hf, hu = _rot(-HEEL_F, 0.0, ths)
        cx, cyy = xa + d * hf * H, cy - hu * H
        f_, u_ = _rot(HEEL_F, SOLE_U, ths + th)
    elif contact == "ball" and theta < 0:
        bf, bu = _rot(BALL_F, 0.0, ths)
        cx, cyy = xa + d * bf * H, cy - bu * H
        f_, u_ = _rot(-BALL_F, SOLE_U, ths + th)
    else:
        cx, cyy = xa, cy
        f_, u_ = _rot(0.0, SOLE_U, ths + th)
    return (cx + d * f_ * H, cyy - u_ * H), (ths + th) / D2R


def _pchip(xs, ys):
    """Monotone cubic interpolation through (xs, ys), at rest at both ends."""
    n = len(xs)
    if n == 1:
        return lambda x: ys[0]
    h = [max(xs[i + 1] - xs[i], 1e-9) for i in range(n - 1)]
    dl = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if dl[i - 1] * dl[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = min(bisect.bisect_right(xs, x) - 1, n - 2)
        t = (x - xs[i]) / h[i]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i]
                + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1])
    return f


def _smax(a, b, k):
    """Smooth maximum (k = blend width)."""
    return 0.5 * (a + b + math.sqrt((a - b) ** 2 + k * k))


def _relaxed_arms(p, t=0.0, seed=0, amt=1.0):
    for s, sg in (("L", 1), ("R", -1)):
        a = p.arms[s]
        a["sh"] = 3.0 * sg + 1.5 * noise1(t * 0.3, seed + sg) * amt
        a["abd"] = 5.0
        a["elbow"] = 12.0 + 2.0 * noise1(t * 0.25, seed + 5 + sg) * amt
        a["wrist"] = 4.0
        a["grip"] = 0.3


# ----------------------------------------------------------------------------- segments
class _Seg:
    t0 = 0.0
    t1 = 0.0
    blend = 0.25

    def root(self, t):
        raise NotImplementedError

    def pose(self, t):
        raise NotImplementedError


class _Stand(_Seg):
    """Standing on planted feet with breathing, sway and small weight shifts."""

    def __init__(self, A, t0, t1, x, feet, yaw, idle=1.0, crouch=0.0, blend=0.25):
        self.A, self.t0, self.t1 = A, t0, t1
        self.x, self.feet, self.yaw = x, dict(feet), yaw
        self.idle, self.crouch, self.blend = idle, crouch, blend
        self.end = dict(x=x, feet=dict(feet), yaw=yaw)

    def root(self, t):
        A = self.A
        H = A.H
        sway = 0.006 * H * noise1(t * 0.22, A.seed + 1) * self.idle
        breathe = math.sin(2 * math.pi * t / 3.6 + A.seed) * 0.0022 * H * self.idle
        x = self.x + sway
        gy = 0.5 * (A.g(self.feet["L"]) + A.g(self.feet["R"]))
        y = gy - (A.body.hip - 0.006 - self.crouch) * H + breathe
        return x, y

    def pose(self, t):
        A = self.A
        H = A.H
        x, y = self.root(t)
        p = F.Pose(x, y, self.yaw)
        p.scale = A.scale
        d = 1.0 if math.cos(self.yaw * D2R) >= 0 else -1.0
        for s in ("L", "R"):
            (ax, ay), pitch = foot_ik(self.feet[s], 0.0, "flat", d, H, A.g)
            p.legs[s] = {"ik": (ax, ay), "pitch": pitch, "toe": 0.0, "abd": 3.0}
        br = math.sin(2 * math.pi * t / 3.6 + A.seed)
        p.spine = [0.6 * br * self.idle, 0.0, -0.8 * br * self.idle]
        p.head = 1.5 * noise1(t * 0.18, A.seed + 9) * self.idle
        _relaxed_arms(p, t, A.seed, self.idle)
        return p


class _Walk(_Seg):
    """Footstep-planned locomotion along x through waypoints [(x, gait, speed), ...]."""

    def __init__(self, A, t0, x0, feet0, legs, yaw=None, blend=0.2):
        self.A, self.t0, self.blend = A, t0, blend
        H = A.H
        X = [x0] + [l[0] for l in legs]
        d = 1.0 if X[-1] >= x0 else -1.0
        self.d = d
        self.yaw = (0.0 if d > 0 else 180.0) if yaw is None else yaw
        k = max(abs(math.cos(self.yaw * D2R)), 0.3)
        D = abs(X[-1] - x0)
        # ---- nominal steps with per-step gait
        G = [gait(l[1]) for l in legs]
        S = [l[2] if l[2] is not None else gait(l[1]).speed for l in legs]

        def gait_at(dist):
            acc = 0.0
            for i, (gx, sp) in enumerate(zip(G, S)):
                seg = abs(X[i + 1] - X[i])
                if dist <= acc + seg or i == len(G) - 1:
                    u = clamp((dist - acc) / max(seg, 1e-6))
                    if i + 1 < len(G) and u > 0.85:          # blend into the next leg's gait
                        w = smoothstep(0.85, 1.0, u)
                        return Gait.mix(gx, G[i + 1], w), lerp(sp, S[i + 1], w)
                    return gx, sp
                acc += seg
            return G[-1], S[-1]

        steps = []          # (gait, speed, nominal length)
        cum = 0.0
        while True:
            g_, sp = gait_at(cum + 0.3 * H)
            Ln = g_.step * H * k
            if cum + Ln * 0.5 >= D and steps:
                break
            steps.append([g_, sp, Ln])
            cum += Ln
            if D < 1e-3:
                break
        def ramped(st):
            n = len(st)
            out = [list(x) for x in st]
            for i, v in enumerate(st[0][0].ramp_in):
                if i < n:
                    out[i][2] *= v
            for i, v in enumerate(st[-1][0].ramp_out):
                j = n - 1 - i
                if j >= len(st[0][0].ramp_in) or (j >= 0 and n > 2 * len(st[0][0].ramp_in)):
                    out[j][2] *= v
            return out
        for _ in range(8):                  # add/remove steps until the ramped sum fits D
            r = ramped(steps)
            sc = D / (sum(x[2] for x in r) or 1.0)
            if sc > 1.08:
                steps.append(list(steps[-1]))
            elif sc < 0.92 and len(steps) > 1:
                steps.pop()
            else:
                break
        steps = ramped(steps)
        scale = D / (sum(x[2] for x in steps) or 1.0)
        for x_ in steps:
            x_[2] *= scale
        m = len(steps)
        # ---- footprints and timing
        first = "L" if d * feet0["L"] <= d * feet0["R"] else "R"
        other = "R" if first == "L" else "L"
        side = [first if i % 2 == 0 else other for i in range(m)]
        prints, cum = [], 0.0
        for i in range(m):
            cum += steps[i][2]
            prints.append(x0 + d * cum)
        off = 0.022 * H * k
        prints[-1] += d * off
        T = []
        for g_, sp, L in steps:
            Tn = g_.step / sp                               # nominal step period (s)
            e = L / (g_.step * H * k)                       # this step vs nominal length
            # shorter (ramp) steps keep nearly the same cadence; longer steps keep the speed
            T.append(Tn * ((0.80 + 0.20 * e) if e <= 1.0 else e))
        g0 = steps[0][0]
        prep = 0.10 * T[0]
        land = []
        lift = []
        swing0 = max(2 * T[0] * (1 - g0.duty), 0.5 * T[0])
        lift.append(t0 + prep)
        land.append(lift[0] + swing0)
        for i in range(1, m):
            land.append(land[i - 1] + T[i])
            sw = 2 * T[i] * (1 - steps[i][0].duty)
            lo = land[i] - sw
            if i == 1:
                lo = max(lo, land[0] - 0.02)
            lift.append(max(lo, (land[i - 2] if i >= 2 else t0) + 0.08 * T[i]))
        gm = steps[-1][0]
        lift_c = max(land[-1] + (2 * gm.duty - 1) * T[-1], land[-1] + 0.05)
        land_c = lift_c + max(0.75 * 2 * T[-1] * (1 - gm.duty), 0.32 * T[-1])
        close_side = other if side[-1] == first else first
        close_x = X[-1] - d * off
        # per-foot plant timeline: list of (x, t_land, t_lift_next, gait)
        plants = {s: [(feet0[s], -1e9, None, g0)] for s in ("L", "R")}
        for i in range(m):
            s = side[i]
            plants[s][-1] = plants[s][-1][:2] + (lift[i], plants[s][-1][3])
            plants[s].append((prints[i], land[i], None, steps[i][0]))
        s = close_side
        plants[s][-1] = plants[s][-1][:2] + (lift_c, plants[s][-1][3])
        plants[s].append((close_x, land_c, None, gm))
        for s in ("L", "R"):
            last = plants[s][-1]
            plants[s][-1] = last[:2] + (1e9, last[3])
        self.plants = plants
        self.lands = land + [land_c]
        self.steps = steps
        self.side = side
        settle = 0.30 * T[-1] + 0.08
        self.t1 = land_c + settle
        # ---- pelvis x: anchors at touchdowns
        tx = [t0, lift[0]]
        xx = [x0, x0]
        for i in range(m):
            tx.append(land[i])
            xx.append(prints[i] - d * steps[i][0].strike * steps[i][2] - (d * off if i == m - 1 else 0.0))
        tx += [land_c, self.t1]
        xx += [X[-1] - d * 0.05 * steps[-1][2], X[-1]]
        # make strictly monotone in time and x
        for i in range(1, len(tx)):
            tx[i] = max(tx[i], tx[i - 1] + 1e-3)
            if d * (xx[i] - xx[i - 1]) < 0:
                xx[i] = xx[i - 1]
        self.px = _pchip(tx, xx)
        self.tx = tx
        self.end = dict(x=X[-1], feet={s: plants[s][-1][0] for s in ("L", "R")}, yaw=self.yaw)

    # ---------------------------------------------------------------- evaluation
    def _step_index(self, t):
        return bisect.bisect_right(self.lands, t) - 1      # -1 before the first touchdown

    def gait_at(self, t):
        i = self._step_index(t)
        S = self.steps
        if i < 0:
            g = S[0][0]
            u = 0.0
            return g, clamp((t - self.t0) / max(self.lands[0] - self.t0, 1e-3))
        if i >= len(S) - 1:
            return S[-1][0], 1.0
        a, b = S[i][0], S[i + 1][0]
        u = clamp((t - self.lands[i]) / max(self.lands[i + 1] - self.lands[i], 1e-3))
        return Gait.mix(a, b, u), u

    def _phase(self, t):
        """Continuous step phase: integer at each touchdown."""
        L = self.lands
        if t <= L[0]:
            return clamp((t - self.t0) / max(L[0] - self.t0, 1e-3)) - 1.0
        i = min(bisect.bisect_right(L, t) - 1, len(L) - 2)
        return i + clamp((t - L[i]) / max(L[i + 1] - L[i], 1e-3))

    def _envelope(self, t):
        """0 at rest .. 1 in full stride (for bob/lean/arm amplitudes)."""
        a = smoothstep(self.t0, self.lands[0], t)
        b = 1.0 - smoothstep(self.lands[-2] if len(self.lands) > 1 else self.t0, self.t1, t)
        return min(a, b)

    def foot(self, s, t):
        """(ankle (x, y), pitch, toe) for foot s at time t."""
        A = self.A
        H, d, g = A.H, self.d, A.g
        P = self.plants[s]
        j = 0
        for i in range(len(P)):
            if P[i][1] <= t:
                j = i
        x, tl, tlift, gt = P[j]
        if t <= tlift or j == len(P) - 1:
            # stance on plant j
            nxt_lift = tlift
            stance = (nxt_lift - tl) if (tl > -1e8 and nxt_lift < 1e8) else None
            if tl > -1e8 and t < tl + gt.flat * (stance or 0.5):
                u = (t - tl) / max(gt.flat * (stance or 0.5), 1e-3)
                th = gt.heel * (1.0 - ease("out", u))
                return foot_ik(x, th, "heel", d, H, g) + (0.0, True)
            if nxt_lift < 1e8:
                start = (tl + gt.heel_off * stance) if stance else max(self.t0, nxt_lift - 0.22)
                if t > start:
                    u = (t - start) / max(nxt_lift - start, 1e-3)
                    th = -gt.toe_off * ease("in", u)
                    (a, pitch) = foot_ik(x, th, "ball", d, H, g)
                    return a, pitch, -th, True
            return foot_ik(x, 0.0, "flat", d, H, g) + (0.0, True)
        # swing from plant j to plant j+1
        x1, tl1, _, g1 = P[j + 1]
        u = clamp((t - tlift) / max(tl1 - tlift, 1e-3))
        (a0, p0) = foot_ik(x, -gt.toe_off, "ball", d, H, g)
        (a1, p1) = foot_ik(x1, g1.heel, "heel", d, H, g)
        cyc = u - math.sin(2 * math.pi * u) / (2 * math.pi)
        ax = lerp(a0[0], a1[0], lerp(cyc, u, g1.swing_lead))
        bump = math.sin(math.pi * (u ** 0.78))
        lift = (g1.lift + g1.knee_lift * (1.0 - u)) * H * bump
        dist = abs(x1 - x)
        lift *= clamp(dist / (0.35 * H), 0.25, 1.0)
        ay = lerp(a0[1], a1[1], smoothstep(0.0, 1.0, u)) - lift
        ay = min(ay, g(ax) - (SOLE_U + 0.4 * lift / H) * H)
        rec = smoothstep(0.0, 0.62, u)
        pitch = lerp(p0, p1, rec) + 8.0 * math.sin(math.pi * u) * (1 - u)
        toe = gt.toe_off * (1.0 - smoothstep(0.0, 0.35, u))
        return (ax, ay), pitch, toe, False

    def root(self, t):
        A = self.A
        H = A.H
        x = self.px(t)
        g_, _ = self.gait_at(t)
        env = self._envelope(t)
        ph = self._phase(t)
        bob = g_.bob * H * env * math.cos(2 * math.pi * (ph - g_.bob_phase))
        crouch = lerp(0.006, g_.crouch, env)
        y = A.g(x) - (A.body.hip - crouch) * H + bob
        # never further than the legs can reach to a planted/swinging ankle
        Lmax = (A.body.thigh + A.body.shin) * H * 0.985
        k = max(abs(math.cos(self.yaw * D2R)), 0.3)
        for s in ("L", "R"):
            (ax, ay), _, _, stance = self.foot(s, t)
            if not stance:
                continue
            dx = (ax - x) / k
            if abs(dx) < Lmax:
                y = _smax(y, ay - math.sqrt(Lmax * Lmax - dx * dx), 0.012 * H)
        return x, y

    def pose(self, t):
        A = self.A
        H, d = A.H, self.d
        x, y = self.root(t)
        g_, _ = self.gait_at(t)
        env = self._envelope(t)
        p = F.Pose(x, y, self.yaw)
        p.scale = A.scale
        for s in ("L", "R"):
            (ax, ay), pitch, toe, _ = self.foot(s, t)
            p.legs[s] = {"ik": (ax, ay), "pitch": pitch, "toe": toe, "abd": 3.0}
        # trunk: gait lean + acceleration lean + slope
        v0 = (self.px(t + 0.06) - self.px(t - 0.06)) / 0.12
        v1 = (self.px(t + 0.18) - self.px(t + 0.06)) / 0.12
        acc = d * (v1 - v0) / 0.12 / H
        slope = _slope(A.g, x, d, H)
        lean = g_.lean * env + clamp(acc * 2.2, -6, 8) + 0.35 * slope
        p.pitch = lean
        p.spine = [0.0, g_.spine * 0.4, g_.spine * 0.6]
        p.head = -lean * g_.head_comp - g_.spine * 0.5
        # arms counter-swing to the legs: each arm is back when its own foot touches down
        ph = self._phase(t)
        for s in ("L", "R"):
            i_s = 0 if self.side[0] == s else 1
            psi = ((ph - i_s) % 2.0) / 2.0
            c = -math.cos(2 * math.pi * psi)          # -1 back .. +1 forward
            sw = g_.arm_swing * c * env
            a = p.arms[s]
            a["sh"] = g_.arm_bias * env + sw
            a["elbow"] = lerp(12.0, g_.elbow, env) + g_.elbow_swing * max(c, 0.0) * env
            a["abd"] = g_.abd
            a["wrist"] = 6.0
            a["grip"] = g_.grip
        return p


class _Turn(_Seg):
    """Turn in place (yaw a -> b through `via`), with two small stepping lifts."""

    def __init__(self, A, t0, dur, x, feet, a, b, via=90.0, blend=0.12):
        self.A, self.t0, self.t1, self.blend = A, t0, t0 + dur, blend
        self.x, self.feet = x, dict(feet)
        b_ = a + wrap_angle(b - a)
        mid = a + wrap_angle(via - a)
        # choose the direction that passes through `via`
        if not (min(a, b_) <= mid <= max(a, b_)):
            b_ = b_ - 360.0 if b_ > a else b_ + 360.0
        self.a, self.b = a, b_
        self.end = dict(x=x, feet={"L": x, "R": x}, yaw=wrap_angle(b))

    def root(self, t):
        A = self.A
        H = A.H
        u = clamp((t - self.t0) / (self.t1 - self.t0))
        x = lerp(0.5 * (self.feet["L"] + self.feet["R"]), self.x, ease("inout", u))
        dip = 0.010 * H * math.sin(math.pi * u)
        return x, A.g(x) - (A.body.hip - 0.006) * H + dip

    def pose(self, t):
        A = self.A
        H = A.H
        u = clamp((t - self.t0) / (self.t1 - self.t0))
        x, y = self.root(t)
        yaw = lerp(self.a, self.b, ease("inout", u))
        p = F.Pose(x, y, yaw)
        p.scale = A.scale
        d = 1.0 if math.cos(yaw * D2R) >= 0 else -1.0
        for i, s in enumerate(("L", "R")):
            fx = lerp(self.feet[s], self.x, ease("inout", clamp((u - 0.1 - 0.35 * i) / 0.45)))
            w0, w1 = 0.08 + 0.38 * i, 0.46 + 0.38 * i
            lift = 0.03 * H * math.sin(math.pi * clamp((u - w0) / (w1 - w0)))
            (ax, ay), pitch = foot_ik(fx, 0.0, "flat", d, H, A.g)
            p.legs[s] = {"ik": (ax, ay - lift), "pitch": pitch, "toe": 0.0, "abd": 3.0}
        p.head_yaw = 18.0 * math.sin(math.pi * u) * (1 if self.b > self.a else -1)
        _relaxed_arms(p, t, A.seed, 0.5)
        return p


class _Free(_Seg):
    """Root follows path(t) -> (x, y) with a given base pose function (floating, falling,
    being lifted, swimming). pose_fn(t, u) -> Pose (legs FK); default: relaxed dangle."""

    def __init__(self, A, t0, t1, path, pose_fn, end, blend=0.3):
        self.A, self.t0, self.t1, self.blend = A, t0, t1, blend
        self.path, self.pose_fn = path, pose_fn
        self.end = end
        self.yaw = end["yaw"]

    def root(self, t):
        return self.path(t)

    def pose(self, t):
        u = clamp((t - self.t0) / max(self.t1 - self.t0, 1e-6))
        p = self.pose_fn(t, u) if self.pose_fn else dangle(self.A, t, self.yaw)
        x, y = self.path(t)
        p.x, p.y = x, y
        if self.pose_fn is None or getattr(p, "yaw", None) is None:
            p.yaw = self.yaw
        p.scale = self.A.scale
        return p


def dangle(A, t, yaw=None):
    """A relaxed floating pose (legs hang slightly bent)."""
    p = F.Pose(0, 0, A.state["yaw"] if yaw is None else yaw)
    for s, ph in (("L", 0.0), ("R", 1.7)):
        p.legs[s] = dict(hip=8 + 6 * math.sin(t * 1.3 + ph), abd=4, knee=16 + 8 * math.sin(t * 1.3 + ph + 0.8),
                         ankle=-12, toe=0)
    _relaxed_arms(p, t, A.seed)
    return p


# ----------------------------------------------------------------------------- channels
class _Channel:
    def __init__(self, name, fn, mode, t0, t1, fade_in, fade_out):
        self.name, self.fn, self.mode = name, fn, mode
        self.t0, self.t1, self.fi, self.fo = t0, t1, fade_in, fade_out

    def weight(self, t):
        if self.mode == "add":
            return 1.0
        if t < self.t0 - self.fi or t > self.t1 + self.fo:
            return 0.0
        a = smoothstep(self.t0 - self.fi, self.t0, t) if self.fi > 0 else (1.0 if t >= self.t0 else 0.0)
        b = 1.0 - smoothstep(self.t1, self.t1 + self.fo, t) if self.fo > 0 else (1.0 if t <= self.t1 else 0.0)
        return min(a, b)


def _get(p, name, body):
    parts = name.split(".")
    if parts[0] == "arm":
        return p.arms[parts[1]].get(parts[2], 0.0)
    if parts[0] == "leg":
        leg = p.legs[parts[1]]
        if "ik" in leg:
            leg = F.leg_ik_angles(p, parts[1], body)
            p.legs[parts[1]] = dict(leg)
        return leg.get(parts[2], 0.0)
    if parts[0] == "foot":
        leg = p.legs[parts[1]]
        if "ik" not in leg:
            return 0.0
        return leg["ik"][0 if parts[2] == "x" else 1] if parts[2] in ("x", "y") else leg.get(parts[2], 0.0)
    if parts[0] == "eyes":
        return p.eyes.get(parts[1], 0.0)
    if parts[0] == "extra":
        return p.extra.get(parts[1], 0.0)
    if parts[0] == "spine":
        return p.spine[int(parts[1])] if len(parts) > 1 else sum(p.spine) / 3.0
    return getattr(p, parts[0])


def _set(p, name, v):
    parts = name.split(".")
    if parts[0] == "arm":
        p.arms[parts[1]][parts[2]] = v
    elif parts[0] == "leg":
        p.legs[parts[1]][parts[2]] = v
    elif parts[0] == "foot":
        leg = p.legs[parts[1]]
        if "ik" in leg and parts[2] in ("x", "y"):
            ik = list(leg["ik"])
            ik[0 if parts[2] == "x" else 1] = v
            leg["ik"] = tuple(ik)
        elif "ik" in leg:
            leg[parts[2]] = v
    elif parts[0] == "eyes":
        p.eyes[parts[1]] = v
    elif parts[0] == "extra":
        p.extra[parts[1]] = v
    elif parts[0] == "spine":
        if len(parts) > 1:
            p.spine[int(parts[1])] = v
        else:
            cur = sum(p.spine) / 3.0
            p.spine = [s + (v - cur) for s in p.spine]
    else:
        setattr(p, parts[0], v)


# ----------------------------------------------------------------------------- arm IK
def arm_ik(p, side, target, body, elbow_out=False):
    """Set p.arms[side] (sh, elbow) so the wrist reaches the world target (clamped to reach)."""
    sk = F.solve(p, body)
    S = sk.j["shoulder_" + side]
    H = sk.H
    yaw = p.yaw * D2R
    k = max(abs(math.cos(yaw)), 0.3)
    sgn = 1.0 if math.cos(yaw) >= 0 else -1.0
    f_ = (target[0] - S[0]) / (H * k) * sgn
    u_ = (S[1] - target[1]) / H
    L1, L2 = body.upper_arm, body.forearm
    abd = p.arms[side].get("abd", 5.0) * D2R
    L1c, L2c = L1 * math.cos(abd), L2 * math.cos(abd)
    dd = clamp(math.hypot(f_, u_), abs(L1c - L2c) + 1e-4, (L1c + L2c) * 0.999)
    phi_t = math.atan2(f_, -u_) / D2R
    cb = clamp((L1c * L1c + dd * dd - L2c * L2c) / (2 * L1c * dd), -1, 1)
    beta = math.acos(cb) / D2R
    phi_u = phi_t - beta if not elbow_out else phi_t + beta
    eu = (math.sin(phi_u * D2R) * L1c, -math.cos(phi_u * D2R) * L1c)
    phi_f = math.atan2(f_ - eu[0], -(u_ - eu[1])) / D2R
    chest = sk.spine_angs[-1]
    p.arms[side]["sh"] = phi_u - chest
    p.arms[side]["elbow"] = wrap_angle(phi_f - phi_u)
    return p


# ----------------------------------------------------------------------------- actor
class Actor:
    """A performing character: a timeline of locomotion/standing/free segments plus
    keyframe channels, reaches and look-ats layered on top."""

    def __init__(self, body, look=None, x=0.0, ground=0.0, facing=1, t0=0.0, scale=1.0, seed=0,
                 name=""):
        self.body, self.look = body, look or F.Look()
        self.g = _ground_fn(ground)
        self.scale = scale
        self.H = body.height * scale
        self.seed = seed
        self.name = name
        # facing: +1 right, -1 left, or an explicit yaw in degrees (e.g. 90 = facing camera)
        yaw = (0.0 if facing > 0 else 180.0) if facing in (1, -1) else float(facing)
        o = 0.022 * self.H
        d = 1.0 if math.cos(yaw * D2R) >= 0 else -1.0
        self.state = dict(x=x, feet={"L": x + d * o, "R": x - d * o}, yaw=yaw)
        self.segs = []
        self.channels = []
        self.reaches = []
        self.looks = []
        self.cursor = t0
        self._start = dict(self.state, feet=dict(self.state["feet"]))

    # ---------------------------------------------------------------- building
    def _t(self, at):
        return self.cursor if at is None else at

    def _push(self, seg):
        if self.segs and seg.t0 > self.segs[-1].t1 + 1e-6:
            # fill the gap with a stand
            st = self.state
            self.segs.append(_Stand(self, self.segs[-1].t1, seg.t0, st["x"], st["feet"], st["yaw"]))
        self.segs.append(seg)
        self.state = dict(seg.end, feet=dict(seg.end["feet"]))
        self.cursor = seg.t1
        return self

    def stand(self, dur=None, until=None, at=None, idle=1.0, crouch=0.0, blend=0.25):
        """Stand on the current spot. Give dur (s) or until (absolute time)."""
        t0 = self._t(at)
        t1 = until if until is not None else t0 + (dur if dur is not None else 1.0)
        st = self.state
        return self._push(_Stand(self, t0, t1, st["x"], st["feet"], st["yaw"], idle, crouch, blend))

    def walk(self, to=None, gait="walk", speed=None, path=None, at=None, yaw=None, turn=0.45, blend=0.2):
        """Walk (or any gait) to x=`to`, or along path=[(x, gait, speed|None), ...].
        Turns first if facing the wrong way (turn = turn duration)."""
        legs = path if path is not None else [(to, gait, speed)]
        legs = [(l[0], l[1] if len(l) > 1 else gait, l[2] if len(l) > 2 else None) for l in legs]
        t0 = self._t(at)
        st = self.state
        d = 1.0 if legs[-1][0] >= st["x"] else -1.0
        want = (0.0 if d > 0 else 180.0) if yaw is None else yaw
        if abs(wrap_angle(st["yaw"] - want)) > 60 and turn:
            self.turn(want, dur=turn, at=t0)
            t0 = self.cursor
        if abs(legs[-1][0] - self.state["x"]) < 1.0:
            return self.stand(0.01, at=t0)
        return self._push(_Walk(self, t0, self.state["x"], self.state["feet"], legs, yaw=want, blend=blend))

    def run(self, to=None, speed=None, **kw):
        return self.walk(to, gait=kw.pop("gait", "run"), speed=speed, **kw)

    def sneak(self, to=None, speed=None, **kw):
        return self.walk(to, gait="sneak", speed=speed, **kw)

    def turn(self, yaw=None, dur=0.5, at=None, via=90.0):
        """Turn in place to yaw (default: about-face), passing through `via` (90 = facing
        the camera, -90 = back to camera)."""
        st = self.state
        b = (180.0 - st["yaw"]) if yaw is None else yaw
        t0 = self._t(at)
        return self._push(_Turn(self, t0, dur, st["x"], st["feet"], st["yaw"], b, via))

    def face(self, yaw, at=None):
        """Change facing instantly (e.g. at a cut)."""
        self.state["yaw"] = yaw
        return self

    def free(self, dur, path, pose=None, at=None, end_x=None, blend=0.3):
        """Leave the ground: the pelvis follows path(t) -> (x, y) (absolute time); pose(t, u)
        returns the base Pose (FK legs) or None for a relaxed dangle. After it ends the
        actor stands at end_x (default: path end x) on the ground."""
        t0 = self._t(at)
        t1 = t0 + dur
        ex = path(t1)[0] if end_x is None else end_x
        o = 0.022 * self.H
        end = dict(x=ex, feet={"L": ex + o, "R": ex - o}, yaw=self.state["yaw"])
        return self._push(_Free(self, t0, t1, path, pose, end, blend))

    def jump(self, to, height=None, dur=None, at=None):
        """A two-footed hop/jump to x=to: crouch, launch, tuck, land, absorb."""
        H = self.H
        x0 = self.state["x"]
        height = 0.18 * H if height is None else height
        dur = dur or 0.75
        t0 = self._t(at)
        g = self.g
        base = lambda x: g(x) - (self.body.hip - 0.006) * H
        T = dict(c0=t0, c1=t0 + 0.18, l1=t0 + dur - 0.2, e=t0 + dur)

        def path(t):
            if t < T["c1"]:
                u = (t - T["c0"]) / 0.18
                return x0, base(x0) + 0.08 * H * math.sin(math.pi * 0.5 * u)
            if t < T["l1"]:
                u = (t - T["c1"]) / (T["l1"] - T["c1"])
                x = lerp(x0, to, u)
                return x, lerp(base(x0) + 0.08 * H, base(to) + 0.02 * H, u) - height * 4 * u * (1 - u)
            u = (t - T["l1"]) / 0.2
            return to, base(to) + 0.10 * H * math.sin(math.pi * clamp(u)) * (1 - 0.5 * u)

        yaw0 = self.state["yaw"]

        def pose(t, u):
            p = dangle(self, t, yaw0)
            tuck = math.sin(math.pi * clamp((t - T["c1"]) / (T["l1"] - T["c1"])))
            for s, k in (("L", 1.0), ("R", 0.8)):
                p.legs[s] = dict(hip=10 + 50 * tuck * k, abd=3, knee=12 + 70 * tuck * k, ankle=-10, toe=0)
            for s in ("L", "R"):
                p.arms[s].update(sh=lerp(-30, 60, tuck), elbow=30)
            p.pitch = 10 * tuck
            return p
        return self.free(dur, path, pose, at=t0, end_x=to, blend=0.12)

    # ---------------------------------------------------------------- layered channels
    def key(self, name, keys, mode="set", fade=0.25, fade_out=None):
        """Keyframe a pose channel. keys: [(t, value), (t, value, ease), ...] (absolute t).
        name: 'pitch', 'spine', 'spine.0', 'neck', 'head', 'head_yaw', 'head_roll', 'yaw',
        'x', 'y' (root, use mode='add'), 'scale', 'arm.R.sh|abd|elbow|wrist|grip',
        'leg.L.hip|knee|ankle|toe|abd' (FK), 'foot.L.x|y|pitch|toe' (IK target),
        'eyes.open|glow|look', 'extra.<anything>'.
        mode 'set' overrides the base pose between the first and last key, fading in/out
        over `fade` seconds; mode 'add' adds the track value at all times."""
        tr = Track(keys)
        ts = [k[0] for k in keys]
        self.channels.append(_Channel(name, tr, mode, min(ts), max(ts), fade,
                                      fade if fade_out is None else fade_out))
        return self

    def channel(self, name, fn, t0, t1, mode="set", fade=0.25):
        """A channel driven by fn(t) (absolute time)."""
        self.channels.append(_Channel(name, fn, mode, t0, t1, fade, fade))
        return self

    def arm(self, side, t0, t1, fade=0.3, **vals):
        """Hold an arm pose from t0 to t1: arm('R', 2, 4, sh=80, elbow=20, grip=0.9)."""
        for k, v in vals.items():
            self.channels.append(_Channel("arm.%s.%s" % (side, k), (lambda t, v=v: v), "set", t0, t1, fade, fade))
        return self

    def pose_keys(self, t0, t1, fade=0.3, **vals):
        """Hold body channels: pose_keys(3, 5, pitch=30, head=10, **{'leg.R.knee': 40})."""
        for k, v in vals.items():
            self.channels.append(_Channel(k, (lambda t, v=v: v), "set", t0, t1, fade, fade))
        return self

    def reach(self, side, t0, t1, target, fade=0.3, elbow_out=False, grip=None):
        """Arm IK: the wrist goes to target (x, y) or target(t) between t0 and t1."""
        self.reaches.append((side, t0, t1, target, fade, elbow_out, grip))
        return self

    def look_at(self, t0, t1, target, fade=0.35, amount=1.0):
        """Turn the head (pitch, and yaw toward camera for 'camera') toward a world point
        or callable target(t), or the string 'camera'."""
        self.looks.append((t0, t1, target, fade, amount))
        return self

    def eyes(self, t0, t1, fade=0.15, **vals):
        """eyes(2, 3, open=0) - close the eyes; glow=0.3 dims them; look=-1..1 gaze."""
        for k, v in vals.items():
            self.channels.append(_Channel("eyes." + k, (lambda t, v=v: v), "set", t0, t1, fade, fade))
        return self

    def blink(self, t, dur=0.14):
        self.channels.append(_Channel("eyes.open", (lambda tt: 0.0), "set", t, t + dur * 0.3, dur * 0.35, dur * 0.35))
        return self

    # ---------------------------------------------------------------- evaluation
    @property
    def end(self):
        return self.cursor

    def _seg_at(self, t):
        S = self.segs
        if not S:
            st = self._start
            S.append(_Stand(self, -1e6, 1e6, st["x"], st["feet"], st["yaw"]))
        i = 0
        for k, s in enumerate(S):
            if s.t0 <= t:
                i = k
        return i

    def _base(self, t):
        S = self.segs
        if not S:
            st = self._start
            return _Stand(self, -1e6, 1e6, st["x"], st["feet"], st["yaw"]).pose(t)
        if t <= S[0].t0:
            first = S[0]
            if isinstance(first, (_Stand, _Free)):
                return first.pose(t)
            st = self._start
            return _Stand(self, -1e6, first.t0, st["x"], st["feet"], st["yaw"]).pose(t)
        i = self._seg_at(t)
        seg = S[i]
        if t > seg.t1 and i == len(S) - 1:
            st = self.state
            tail = _Stand(self, seg.t1, 1e9, st["x"], st["feet"], st["yaw"])
            p = tail.pose(t)
            w = smoothstep(seg.t1, seg.t1 + 0.25, t)
            return F.blend(seg.pose(seg.t1), p, w, self.body) if w < 1 else p
        p = seg.pose(min(t, seg.t1))
        if i > 0 and t < seg.t0 + seg.blend:
            prev = S[i - 1]
            w = smoothstep(seg.t0, seg.t0 + seg.blend, t)
            p = F.blend(prev.pose(min(t, prev.t1)), p, w, self.body)
        return p

    def root(self, t):
        S = self.segs
        if not S:
            return self._start["x"], 0.0
        i = self._seg_at(t)
        seg = S[i]
        return seg.root(min(max(t, seg.t0), seg.t1))

    def pose(self, t):
        """The final Pose at time t (base segments + channels + reaches + looks)."""
        p = self._base(t)
        p = p.copy()
        for ch in self.channels:
            w = ch.weight(t)
            if w <= 0:
                continue
            v = ch.fn(t)
            if ch.mode == "add":
                _set(p, ch.name, _get(p, ch.name, self.body) + v)
            else:
                cur = _get(p, ch.name, self.body)
                _set(p, ch.name, lerp(cur, v, w))
        for (side, t0, t1, target, fade, eo, grip) in self.reaches:
            if t < t0 - fade or t > t1 + fade:
                continue
            w = min(smoothstep(t0 - fade, t0, t), 1 - smoothstep(t1, t1 + fade, t))
            tgt = target(t) if callable(target) else target
            q = arm_ik(p.copy(), side, tgt, self.body, eo)
            for k in ("sh", "elbow"):
                p.arms[side][k] = lerp(p.arms[side][k], q.arms[side][k], w)
            if grip is not None:
                p.arms[side]["grip"] = lerp(p.arms[side].get("grip", 0.3), grip, w)
        for (t0, t1, target, fade, amt) in self.looks:
            if t < t0 - fade or t > t1 + fade:
                continue
            w = min(smoothstep(t0 - fade, t0, t), 1 - smoothstep(t1, t1 + fade, t)) * amt
            if target == "camera":
                d = 1.0 if math.cos(p.yaw * D2R) >= 0 else -1.0
                p.head_yaw = lerp(p.head_yaw, 60.0 * d, w)
                continue
            tgt = target(t) if callable(target) else target
            sk = F.solve(p, self.body)
            hx, hy = sk.j["head"]
            d = 1.0 if math.cos(p.yaw * D2R) >= 0 else -1.0
            dx, dy = (tgt[0] - hx) * d, tgt[1] - hy
            ang = math.degrees(math.atan2(dy, max(abs(dx), 1.0)))      # + = target below
            need = clamp(ang * 0.75, -40, 50)          # the eyes do the rest
            p.head = lerp(p.head, p.head + (need - sk.head_ang), w)
            if dx < 0:                    # target behind: turn the head toward the camera
                p.head_yaw = lerp(p.head_yaw, 70.0 * d, w)
        # velocity for cloth / hair flutter
        h = 1.0 / 48.0
        x0, y0 = self.root(t - h)
        x1, y1 = self.root(t + h)
        p.extra["vel"] = ((x1 - x0) / (2 * h), (y1 - y0) / (2 * h))
        p.extra["t"] = t
        return p

    def skeleton(self, t):
        return F.solve(self.pose(t), self.body)

    def joint(self, t, name):
        return self.skeleton(t).j[name]

    def draw(self, f, t, ctx=None, look=None, **kw):
        """Solve and draw at time t. Returns the Skeleton (for attaching props)."""
        sk = self.skeleton(t)
        F.draw_figure(f, sk, look or self.look, ctx, **kw)
        return sk
