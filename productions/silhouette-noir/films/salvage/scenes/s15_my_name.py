"""s15 · MY NAME: night, high moon. The diver comes up the ladder out of the sea, drops the cut
hose, climbs onto the deck and takes off his helmet in front of the client. He says his name.
The bell tolls (9.0 s).

IN  (hard cut from s14, its toll echo carrying): the s14 framing and states continue.
    (Filled in at the end of the work.)

The bell, the davit, the boat and the swell run on s14's clock: tau = t + LIB.S15_OFFSET.
"""
import bisect
import functools
import math

import numpy as np

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import arm_ik
from engine.timing import Cue
from films.salvage import cast
from films.salvage import sets as S
from films.salvage import sets_boat as SB
from films.salvage import sets_surface as SS
from films.salvage.scenes import _lib_s01_s03_s16 as LIB
from films.salvage.scenes import s14_the_bell as S14

PAL = S.PAL
INK = PAL.ink
D2R = math.pi / 180.0

OFF = LIB.S15_OFFSET                 # tau = t + OFF (s14's clock: bell, boat, swell)
BOAT = S.Boat()
MOON = LIB.NIGHT_MOON
MOON_R = LIB.NIGHT_MOON_R
BRIGHT = LIB.NIGHT_BRIGHT
T_TOLL = LIB.TOLLS[2][0] - OFF       # 6.80: the third toll (the loudest)

T_REL = 2.40                         # the hose coupling comes off the helmet
T_TWIST = (5.30, 5.58)               # the helmet's quarter-turn (unlock)
T_LIFT = (5.62, 6.10)                # lifted off over the head
T_LOWER = (6.10, 6.45)               # lowered to his side
T_HAT = 7.32                         # the gust takes the client's hat


def _tau(t):
    return t + OFF


def _pchip(xs, ys, m0=None, m1=None):
    """Monotone cubic through (xs, ys); at rest at the ends unless end slopes are given."""
    n = len(xs)
    h = [max(xs[i + 1] - xs[i], 1e-9) for i in range(n - 1)]
    dl = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if dl[i - 1] * dl[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])
    if m0 is not None:
        m[0] = m0
    if m1 is not None:
        m[-1] = m1

    def f(x):
        if x <= xs[0]:
            return ys[0] + (x - xs[0]) * m[0]
        if x >= xs[-1]:
            return ys[-1] + (x - xs[-1]) * m[-1]
        i = min(bisect.bisect_right(xs, x) - 1, n - 2)
        u = (x - xs[i]) / h[i]
        u2, u3 = u * u, u * u * u
        return ((2 * u3 - 3 * u2 + 1) * ys[i] + (u3 - 2 * u2 + u) * h[i] * m[i]
                + (-2 * u3 + 3 * u2) * ys[i + 1] + (u3 - u2) * h[i] * m[i + 1])
    return f


def _keys(keys, col):
    return _pchip([k[0] for k in keys], [k[col] for k in keys])


# ============================================================================= camera
_CAM = [  # (t, x, y, zoom)
    (0.0, -165.0, -420.0, 0.86),
    (1.25, -60.0, -265.0, 1.30),
    (1.75, -95.0, -300.0, 1.26),
    (3.35, -330.0, -440.0, 1.06),
    (4.45, -420.0, -452.0, 1.08),
    (5.60, -452.0, -458.0, 1.14),
    (6.80, -480.0, -462.0, 1.20),
    (8.00, -498.0, -470.0, 1.24),
    (10.0, -512.0, -476.0, 1.27),
]
_CX = _keys(_CAM, 1)
_CY = _keys(_CAM, 2)
_CZ = _pchip([k[0] for k in _CAM], [math.log(k[3]) for k in _CAM])


def _shake(t):
    """Shudders on the tolls (s14's two decaying, the third here), <= 4 px."""
    tau = _tau(t)
    a = 0.0
    for tk, s in LIB.TOLLS:
        if tau >= tk:
            a += 3.2 * s * math.exp(-(tau - tk) / 0.25)
    return min(a, 4.0)


def camera(t):
    x, y, z = _CX(t), _CY(t), math.exp(_CZ(t))
    a = _shake(t)
    if a > 0.05:
        k = a / z
        tau = _tau(t)
        return Camera(x + k * noise1(tau * 31.0, 3), y + k * noise1(tau * 29.0, 7), z)
    return Camera(x, y, z)


# ============================================================================= the ladder (boat-local)
_LX0, _LY0 = SB.LADDER["top"]
_LX1, _LY1 = SB.LADDER["bottom"]
_LOX, _LOY = SB.LADDER["off"]
_LLEN = math.hypot(_LX1 - _LX0, _LY1 - _LY0)


def rung(i):
    """Boat-local centre of rung i (1 = the top rung, level with the deck)."""
    u = i * SB.LADDER["pitch"] / _LLEN
    return (lerp(_LX0, _LX1, u) + _LOX / 2, lerp(_LY0, _LY1, u) + _LOY / 2)


def _foot_rung(i):
    """Ankle (local) with the ball of the foot on rung i (facing the hull, -x)."""
    r = rung(i)
    return (r[0] + 52.0, r[1] - 28.0)


def _foot_deck(x):
    return (x, SB.deck_local(x) - 0.043 * cast.DIVER.height)


def _hand_rung(i):
    """Wrist (local) for a fist round rung i."""
    r = rung(i)
    return (r[0] + 26.0, r[1] + 14.0)


H_HOOK = (906.0, -230.0)            # wrist on the ladder's top (the hooks over the gunwale)
H_RAIL = (912.0, -306.0)            # wrist on the end of the stern rail
H_RAIL_IN = (846.0, -306.0)


def _limb(segs, t):
    """A hand's or foot's contact plan. segs: [(t0, t1, a, b, lift), ...] in time order: it
    holds a before the first move, travels a -> b over [t0, t1] on an eased arc (lift = (dx, dy)
    at mid-move) and holds b until the next move. a / b may be callables of t.
    Returns (point, moving 0..1)."""
    def P(q):
        return q(t) if callable(q) else q
    prev = P(segs[0][2])
    for (t0, t1, a, b, lift) in segs:
        if t < t0:
            return prev, 0.0
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            e = ease("inout", u)
            pa, pb = P(a), P(b)
            arc = math.sin(math.pi * u)
            return (lerp(pa[0], pb[0], e) + lift[0] * arc, lerp(pa[1], pb[1], e) + lift[1] * arc), arc
        prev = P(b)
    return prev, 0.0


# ============================================================================= the diver
DV_LOOK = cast.diver(helmet=True, weights=False, boots=False)
DV_BARE = cast.diver(helmet=False, weights=False, boots=False)
DVH = cast.DIVER.height

# pelvis (boat-local) - the s14 rise at the cut, the hang, the climb, over onto the deck
_DV_P = [
    (0.00, 1020.0, 303.0),
    (0.45, 1018.0, 252.0),
    (0.90, 1017.0, 204.0),
    (1.25, 1016.0, 170.0),
    (1.62, 1011.0, 100.0),
    (1.94, 1005.0, 30.0),
    (2.55, 1003.0, 20.0),
    (2.85, 997.0, -60.0),
    (3.15, 989.0, -160.0),
    (3.45, 979.0, -262.0),
    (3.80, 905.0, -410.0),
    (4.10, 818.0, -484.0),
    (4.40, 752.0, -490.0),
    (4.75, 728.0, -488.0),
    (6.45, 728.0, -488.0),
    (6.75, 690.0, -489.0),
    (7.10, 684.0, -488.0),
    (10.0, 684.0, -488.0),
]
_DVX = _pchip([k[0] for k in _DV_P], [k[1] for k in _DV_P], m0=-15.0)
_DVY = _pchip([k[0] for k in _DV_P], [k[2] for k in _DV_P], m0=-120.0)

_DV_YAW = _pchip([0.0, 0.40, 0.80, 1.30, 1.62, 3.45, 3.95, 10.0], [81.4, 102.0, 126.0, 136.0, 176.0, 178.0, 180.0, 180.0])
_DV_HEAD = _pchip([0.0, 0.45, 0.85, 1.35, 1.62, 1.95, 2.10, 2.42, 2.62, 3.40, 3.75, 4.10, 4.50, 10.0],
                  [-42.5, -26.0, -6.0, -8.0, -22.0, -14.0, 16.0, 16.0, -18.0, -10.0, 12.0, 2.0, -3.0, -3.0])
_DV_PITCH = _pchip([0.0, 0.6, 1.25, 1.65, 3.40, 3.65, 3.95, 4.30, 10.0],
                   [-3.0, 2.0, 5.0, 7.0, 7.0, 20.0, 12.0, 3.0, 2.0])

# feet: (t0, t1, from, to, arc lift (dx, dy)) - local ankle targets
_FL = [
    (0.55, 1.05, _foot_rung(10.6), _foot_rung(9), (6.0, -10.0)),
    (1.62, 1.94, _foot_rung(9), _foot_rung(7), (34.0, -20.0)),
    (2.85, 3.15, _foot_rung(7), _foot_rung(4), (36.0, -30.0)),
    (3.45, 3.80, _foot_rung(4), _foot_deck(850.0), (40.0, -150.0)),
    (4.10, 4.40, _foot_deck(850.0), _foot_deck(715.0), (0.0, -34.0)),
    (6.45, 6.72, _foot_deck(715.0), _foot_deck(668.0), (0.0, -26.0)),
]
_FR = [
    (0.65, 1.15, _foot_rung(11.4), _foot_rung(10), (6.0, -10.0)),
    (1.30, 1.62, _foot_rung(10), _foot_rung(8), (34.0, -20.0)),
    (2.55, 2.85, _foot_rung(8), _foot_rung(5), (36.0, -30.0)),
    (3.15, 3.45, _foot_rung(5), _foot_rung(2), (36.0, -30.0)),
    (3.80, 4.10, _foot_rung(2), _foot_deck(785.0), (10.0, -110.0)),
    (4.45, 4.75, _foot_deck(785.0), _foot_deck(740.0), (0.0, -26.0)),
    (6.62, 6.88, _foot_deck(740.0), _foot_deck(700.0), (0.0, -20.0)),
]


def _dv_inlet_local(t):
    """The helmet's air inlet (hose end), local (the arms don't move the head)."""
    p = costume.helmet_inlet(_dv_skel_body(t))
    return BOAT.to_local(p, _tau(t))


# hands: wrist targets (local); weight of the IK = contact
_HL = [
    (0.10, 0.55, None, _hand_rung(2), (30.0, -20.0)),
    (1.45, 1.70, _hand_rung(2), H_HOOK, (20.0, -20.0)),
    (3.50, 3.82, H_HOOK, H_RAIL_IN, (10.0, -40.0)),
]
_HR = [
    (0.55, 0.95, None, _hand_rung(3), (30.0, -20.0)),
    (1.65, 1.92, _hand_rung(3), _hand_rung(1), (24.0, -20.0)),
    (2.02, 2.20, _hand_rung(1), "inlet", (30.0, -20.0)),
    (2.42, 2.66, "inlet", H_RAIL, (30.0, -30.0)),
]


def _ik_w_L(t):
    return smoothstep(0.05, 0.50, t) * (1.0 - smoothstep(3.85, 4.20, t))


def _ik_w_R(t):
    return smoothstep(0.45, 0.85, t) * (1.0 - smoothstep(3.70, 4.05, t))


def _hand_plan(segs, t, start):
    """Resolve 'inlet' and None (= where the hand starts) placeholders."""
    out = []
    for (t0, t1, a, b, lift) in segs:
        def res(q):
            if q is None:
                return start
            if q == "inlet":
                return _inlet_grip
            return q
        out.append((t0, t1, res(a), res(b), lift))
    return _limb(out, t)


def _inlet_grip(t):
    p = _dv_inlet_local(min(t, T_REL))
    return (p[0] + 14.0, p[1] + 16.0)


def _dv_s14(t):
    """s14's diver, continued (valid to t = 1.0)."""
    return S14.DIVER.pose(_tau(min(t, 1.0)))


@functools.lru_cache(maxsize=4)
def _s14_hand_local(side):
    sk = F.solve(_dv_s14(0.0), cast.DIVER)
    p = sk.j["wrist_" + side]
    return BOAT.to_local(p, _tau(0.0))


def _dv_body(t):
    """Base body pose (no arms IK): root, yaw, spine, head, legs."""
    tau = _tau(t)
    pb = BOAT.pose(tau)

    def Wd(q):
        return BOAT.to_world(q, tau, pb)
    x, y = Wd((_DVX(t), _DVY(t)))
    p = F.Pose(x, y, _DV_YAW(t))
    p.pitch = _DV_PITCH(t) + 1.5 * noise1(t * 0.4, 21)
    climb = smoothstep(1.2, 1.6, t) * (1.0 - smoothstep(3.8, 4.3, t))
    p.spine = [1.0 + 1.5 * climb, 1.0 + 1.5 * climb, 0.0]
    p.head = _DV_HEAD(t) + 2.0 * noise1(t * 0.3, 22)
    # breathing (shoulders / chest) once he is out of the water
    br = math.sin(2 * math.pi * t / 2.6) * smoothstep(0.9, 1.4, t)
    p.spine[2] += 1.2 * br
    # legs: on the rungs / the deck (IK), still kicking in the water before he finds them
    fl, ml = _limb(_FL, t)
    fr, mr = _limb(_FR, t)
    for s, f_, m_ in (("L", fl, ml), ("R", fr, mr)):
        a = Wd(f_)
        p.legs[s] = {"ik": a, "pitch": -6.0 * m_, "toe": 0.0, "abd": 4.0}
    p.eyes = dict(open=1.0, glow=1.0, look=0.0)
    kick_w = 1.0 - smoothstep(0.55, 1.05, t)
    if kick_w > 0.0:
        q = p.copy()
        for s, ph in (("L", 0.0), ("R", math.pi)):
            k = math.sin(2 * math.pi * tau / 1.9 + ph)
            q.legs[s] = dict(hip=6.0 + 9.0 * k, abd=4.0, knee=12.0 + 10.0 * max(0.0, k), ankle=-14.0, toe=0.0)
        p = F.blend(q, p, 1.0 - kick_w, cast.DIVER)
    return p


@functools.lru_cache(maxsize=512)
def _dv_skel_body(t):
    """The body alone (arms relaxed), blended out of s14's: for the head / inlet."""
    p = _dv_body(t)
    w = smoothstep(0.0, 0.65, t)
    if w < 1.0:
        p = F.blend(_dv_s14(t), p, w, cast.DIVER)
    return F.solve(p, cast.DIVER)


def _dv_hands(p, t):
    """Arms: relaxed FK, IK onto the holds while climbing; the helmet removal."""
    tau = _tau(t)
    pb = BOAT.pose(tau)
    p.arms["L"] = dict(sh=8.0, abd=12.0, elbow=16.0, wrist=4.0, grip=0.35)
    p.arms["R"] = dict(sh=4.0, abd=12.0, elbow=14.0, wrist=4.0, grip=0.35)
    for side, plan, wfn in (("L", _HL, _ik_w_L), ("R", _HR, _ik_w_R)):
        w = wfn(t)
        if w <= 0.001:
            continue
        start = _s14_hand_local(side)
        tgt, mv = _hand_plan(plan, t, start)
        q = arm_ik(p.copy(), side, BOAT.to_world(tgt, tau, pb), cast.DIVER, elbow_out=False)
        p.arms[side]["sh"] = lerp(p.arms[side]["sh"], q.arms[side]["sh"], w)
        p.arms[side]["elbow"] = lerp(p.arms[side]["elbow"], q.arms[side]["elbow"], w)
        p.arms[side]["wrist"] = lerp(p.arms[side]["wrist"], 20.0, w)
        p.arms[side]["grip"] = lerp(p.arms[side]["grip"], 1.0 - 0.6 * mv, w)
    return p


def _dv_mine(t):
    p = _dv_body(t)
    return _dv_hands(p, t)


@functools.lru_cache(maxsize=512)
def _dv_pose_pre(t):
    """The diver's pose before the helmet business (blended out of s14's at the cut)."""
    p = _dv_mine(t)
    w = smoothstep(0.0, 0.65, t)
    if w < 1.0:
        p = F.blend(_dv_s14(t), p, w, cast.DIVER)
    return p


@functools.lru_cache(maxsize=512)
def _dv_skel_pre(t):
    return F.solve(_dv_pose_pre(t), cast.DIVER)


def dv_skel(t):
    return _dv_skel_pre(t)


# ============================================================================= the client
CLH = cast.CLIENT.height


def _cl_s14(t):
    return S14.CLIENT.pose(_tau(min(t, 2.0)))


# feet (world x on deck): R = near / front, L = far / back
_CFL = [
    (2.00, 2.42, -624.0, -680.0),
    (3.05, 3.45, -680.0, -722.0),
]
_CFR = [
    (2.50, 2.92, -576.0, -632.0),
    (3.55, 3.95, -632.0, -672.0),
]


def _cfoot(plan, t, x0):
    x = x0
    for (t0, t1, a, b) in plan:
        if t < t0:
            return x, 0.0
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return lerp(a, b, ease("inout", u)), math.sin(math.pi * u)
        x = b
    return x, 0.0


def _cl_mine(t):
    tau = _tau(t)
    xl, ml = _cfoot(_CFL, t, -624.0)
    xr, mr = _cfoot(_CFR, t, -576.0)
    x = (xl + xr) / 2.0 - 2.0
    deck = BOAT.deck_y(x, tau)
    p = F.Pose(x, deck - 318.0 + 4.0 * (ml + mr), 0.0)
    p.pitch = 5.0 - 3.0 * smoothstep(1.9, 2.3, t) * (1.0 - smoothstep(3.9, 4.4, t))
    p.spine = [0.0, 0.0, -2.0]
    for s, fx, m_ in (("L", xl, ml), ("R", xr, mr)):
        dy = BOAT.deck_y(fx, tau)
        p.legs[s] = {"ik": (fx, dy - 0.043 * CLH - 16.0 * m_), "pitch": -8.0 * m_, "toe": 0.0, "abd": 3.0}
    knife = smoothstep(1.6, 2.2, t)
    p.arms["L"] = dict(sh=lerp(-6.0, 10.0, knife), abd=6.0, elbow=lerp(16.0, 40.0, knife), wrist=-10.0 * knife,
                       grip=1.0)
    p.arms["R"] = dict(sh=lerp(4.0, -10.0, knife), abd=7.0, elbow=lerp(16.0, 24.0, knife), wrist=0.0, grip=0.5)
    p.head = -2.0
    p.eyes = dict(open=1.0, glow=0.9, look=0.0)
    return p


def _look(p, body, target, amt):
    if amt <= 0.0:
        return p
    sk = F.solve(p, body)
    hx, hy = sk.j["head"]
    d = 1.0 if math.cos(p.yaw * D2R) >= 0 else -1.0
    dx, dy = (target[0] - hx) * d, target[1] - hy
    ang = math.degrees(math.atan2(dy, max(abs(dx), 1.0)))
    need = clamp(ang * 0.75, -40.0, 50.0)
    p.head = lerp(p.head, p.head + (need - sk.head_ang), amt)
    return p


@functools.lru_cache(maxsize=512)
def _cl_pose(t):
    p = _cl_mine(t)
    # he watches the diver: the helmet as it comes up, then the man (not his eyes until the
    # helmet is off)
    dk = dv_skel(t)
    tgt = dk.j["head"]
    lower = 60.0 * (1.0 - smoothstep(5.7, 6.1, t))
    p = _look(p, cast.CLIENT, (tgt[0], tgt[1] + lower), 0.85 * smoothstep(0.5, 1.2, t))
    w = smoothstep(0.0, 0.8, t)
    if w < 1.0:
        p = F.blend(_cl_s14(t), p, w, cast.CLIENT)
    # blinks before the eye contact
    for tb in (1.15, 3.95, 5.30):
        if tb - 0.06 < t < tb + 0.16:
            p.eyes["open"] = min(p.eyes["open"], abs(t - tb - 0.05) / 0.11)
    p.extra["vel"] = (0.0, 0.0)
    p.extra["t"] = t
    return p


@functools.lru_cache(maxsize=512)
def cl_skel(t):
    return F.solve(_cl_pose(t), cast.CLIENT)


def _cl_ember(t):
    base = (0.55 + 0.1 * noise1(_tau(t) * 0.7, 9)) * 0.3
    return base


def _cl_look(t):
    return cast.client(ember=_cl_ember(t), coat_flow=0.15 + 0.08 * noise1(t * 0.5, 4))


def _knife(L, sk):
    w = sk.j["wrist_L"]
    h = sk.j["hand_L"]
    ang = math.degrees(math.atan2(h[1] - w[1], h[0] - w[0])) - 35.0
    S.draw_knife(L, h[0], h[1], angle=ang, s=0.42)


# ============================================================================= the cut hose
_NH = 40
_HDT = 1.0 / 120.0
_HT0, _HT1 = 0.0, 10.05
_SW = np.array(SS.SWELL, float)


def _sea_y_np(x, tau):
    y = np.zeros_like(x)
    for A, Lw, Tw, ph, d in SS.SWELL:
        y += A * np.sin(2 * np.pi * (x / Lw - d * tau / Tw) + ph)
    return SS.SEA_Y + y


class _Hose:
    """The cut red hose from s14's state at the cut. Node 0 is on the helmet's inlet until the
    coupling is unscrewed (T_REL), then free and heavy (brass). Above the surface it falls
    (air), below it drifts and sinks slowly in the current (as s14)."""

    def __init__(self):
        self._F = None
        self.splash = None

    def _sim(self):
        n, dt = _NH, _HDT
        P = np.array(S14.HOSE.points(OFF), np.float64)
        prev = np.array(S14.HOSE.points(OFF - dt), np.float64)
        rest = 2300.0 / (n - 1)
        steps = int(math.ceil((_HT1 - _HT0) / dt)) + 2
        frames = np.empty((steps, n, 2), np.float64)
        inv = np.ones((n, 1))
        inv[0] = 0.35                      # the coupling is heavy
        i_even = [np.arange(par, n - 1, 2) for par in (0, 1)]
        bend = [np.array([i for i in range(n - 2) if i % 4 in grp], dtype=int) for grp in ((0, 1), (2, 3))]
        released = False
        for k in range(steps):
            t = _HT0 + k * dt
            tau = _tau(t)
            vel = (P - prev) / dt
            sea = _sea_y_np(P[:, 0], tau)
            wet = (P[:, 1] > sea)[:, None]
            cx = 26.0 + 10.0 * np.sin(0.37 * tau + P[:, 1] / 700.0)
            cy = -40.0 + 30.0 * np.sin(0.5 * tau + P[:, 1] / 400.0)
            cur = np.stack([cx, cy], axis=1)
            g_w = np.array([0.0, 70.0])
            acc_w = g_w - 1.6 * (vel - cur)
            acc_a = np.array([0.0, 2600.0]) - 0.5 * vel
            acc = np.where(wet, acc_w, acc_a)
            if released:
                acc[0] += np.where(wet[0], np.array([0.0, 520.0]), np.array([0.0, 0.0]))
            new = P + vel * dt + acc * dt * dt
            prev, P = P, new
            pin = t < T_REL
            if pin:
                pa = np.array(BOAT.to_world(_dv_inlet_local(t), tau), np.float64)
            elif not released:
                released = True
            w = inv.copy()
            if pin:
                w[0] = 0.0
            for _ in range(10):
                if pin:
                    P[0] = pa
                for i0 in i_even:
                    d = P[i0 + 1] - P[i0]
                    L = np.linalg.norm(d, axis=1)[:, None] + 1e-9
                    diff = (L - rest) / L
                    wa, wb = w[i0], w[i0 + 1]
                    sw = wa + wb
                    sw[sw == 0] = 1.0
                    P[i0] += d * diff * wa / sw
                    P[i0 + 1] -= d * diff * wb / sw
                for i0 in bend:
                    d = P[i0 + 2] - P[i0]
                    L = np.linalg.norm(d, axis=1)[:, None] + 1e-9
                    diff = np.minimum((L - 2 * rest) / L, 0.0) * 0.3
                    wa, wb = w[i0], w[i0 + 2]
                    sw = wa + wb
                    sw[sw == 0] = 1.0
                    P[i0] += d * diff * wa / sw
                    P[i0 + 2] -= d * diff * wb / sw
            if pin:
                P[0] = pa
            frames[k] = P
            if released and self.splash is None:
                if P[0, 1] > _sea_y_np(P[:1, 0], tau)[0]:
                    self.splash = (t, float(P[0, 0]))
        self._F = frames

    def points(self, t):
        if self._F is None:
            self._sim()
        f = (min(max(t, _HT0), _HT1) - _HT0) / _HDT
        i = min(max(int(math.floor(f)), 0), len(self._F) - 2)
        u = f - i
        P = self._F[i] * (1 - u) + self._F[i + 1] * u
        return [tuple(q) for q in P]

    def splash_at(self):
        if self._F is None:
            self._sim()
        return self.splash


HOSE = _Hose()


def _coupling(L, pts):
    """The brass coupling on the free end (ink, as s16 draws it)."""
    a, b = pts[0], pts[1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    ux, uy = dx / d, dy / d
    draw.capsule(L, (a[0] - 6.0 * ux, a[1] - 6.0 * uy), (a[0] + 16.0 * ux, a[1] + 16.0 * uy), 8.0, 8.0)
    L.set_source_rgb(*INK)
    L.fill()


# ============================================================================= light
def _moon_screen(f):
    return (MOON[0], S.horizon_y(f) - MOON[1])


def _under_light(f, t, sk):
    k = 1.0 - smoothstep(0.6, 2.2, t)
    atmos.underwater_rays(f, surface_y=0.0, t=_tau(t), spacing=190.0, angle=95.0, fan=8.0, length=1800.0,
                          intensity=0.16, density=0.5, seed=14, blur=18, color=S.mix(PAL.moon, PAL.surface, 0.5))
    if k > 0.01:
        ps = f.cam.to_screen(sk.j["chest"])
        LIB.screen_glow(f, (ps[0], ps[1] - 80.0), 640.0 * f.cam.zoom / 0.5, PAL.surface, 0.10 * k)


def _beam(f, t, sk):
    """His helmet lamp: the s14 beam up through the water, gone as the helmet surfaces."""
    p, d, _ = costume.helmet_lamp(sk)
    sea = S.sea_y(p[0], _tau(t))
    k = smoothstep(sea - 10.0, sea + 60.0, p[1])
    if k <= 0.01:
        return
    ang = math.degrees(math.atan2(d[1], d[0]))
    L = max(60.0, (p[1] - sea) / max(0.2, -d[1]) + 40.0)
    atmos.beam(f, p, ang, length=L, half_angle=9.0, intensity=0.42 * k, falloff=0.8, soft=0.5, core=0.5,
               fog=0.4, pool=0.0, dust=0.35, glare=0.0, t=_tau(t), seed=5)


def _lamp_head(f, t, p, k=1.0):
    atmos.lamp(f, p, radius=8.0, intensity=0.9 * k, halo=4.0, core=0.3, t=_tau(t), seed=6)


def _line(L, st):
    P, top = st["pivot"], st["top"]
    LIB.draw_hose(L, [P, top], 5.0, color=LIB.PALE)
    draw.circle(L, (top[0], top[1] + 4.0), 8.0)
    L.set_source_rgb(*INK)
    L.fill()


def _bell(L, f, t, st, md):
    ring = clamp(st["ring"])
    LIB.draw_bell_lit(L, st, md, f.cam.zoom, rim=0.30 + 0.45 * ring, sheen=0.20 + 0.30 * ring)


def _deck_hose(L, t):
    S14._deck_hose(L, _tau(t))


# ============================================================================= render
def render(f, t, T):
    tau = _tau(t)
    cam = camera(t)
    f.set_camera(cam)
    S.sea_world(f, tau, moon=MOON, moon_r=MOON_R, dusk=0.0, veil=0.25)
    ms = _moon_screen(f)
    dk = dv_skel(t)
    ck = cl_skel(t)
    _under_light(f, t, dk)
    st = LIB.bell_state(tau, BOAT)
    md = LIB.moon_dir_world(cam, LIB.bell_point(st, (0.0, 80.0)), ms)
    _beam(f, t, dk)
    with f.layer() as L:
        BOAT.draw(L, tau, pump_angle=150.0 * tau, winch_angle=-2.0 * LIB.crank_deg(LIB.T_STOP), hose=False,
                  hook=False)
        _deck_hose(L, t)
        _knife(L, ck)
        F.draw_figure(f, ck, _cl_look(t), L)
        hp = HOSE.points(t)
        LIB.draw_hose(L, hp, LIB.HOSE_W)
        if t >= T_REL:
            _coupling(L, hp)
        F.draw_figure(f, dk, DV_LOOK, L)
        _line(L, st)
        _bell(L, f, t, st, md)
    S.water_front(f, tau, alpha=0.08, bright=BRIGHT)
    BOAT.draw_lights(f, tau, lantern=1.0, window=0.5, masthead=1.0)
    p, d, _ = costume.helmet_lamp(dk)
    _lamp_head(f, t, p)
    f.post["vignette"] = lerp(f.post["vignette"], 0.38, 0.6)


def motion_blur(t, T):
    return 1


def cues(T):
    return [
        Cue(T_TOLL, "THE BELL TOLLS the third time: the loudest sound in the film (tonic D), ringing on over the "
                    "dip to black", gain_db=0, pan=0.25, dur=6.0),
    ]
