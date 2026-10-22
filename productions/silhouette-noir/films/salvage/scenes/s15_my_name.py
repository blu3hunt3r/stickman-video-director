"""s15 · MY NAME: night, high moon. The diver comes up the ladder out of the sea, lets the cut
hose go, climbs onto the deck and takes his helmet off in front of the client. He tells him his
name. The bell tolls (9.0 s).

(Beats, handoff states and cues: see the report; filled in below once final.)

The bell, the davit, the boat and the swell run on s14's clock: tau = t + LIB.S15_OFFSET.
"""
import bisect
import functools
import math

import cairo
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

# L22 "He never asked my name." 1.60-3.62 (name 2.97); L23 "So I told him." 5.20-6.49
# (I 5.50, told 5.68, him 6.06)
T_REL = 2.40                         # the hose coupling comes off the helmet
T_TOSS = 2.54                        # ... and he throws it out behind him, into the sea
TOSS = (55.0, 16.0)                  # how far his hand carries it (boat-local)
V_TOSS = (230.0, 20.0)               # its speed as he lets go (px/s)
T_TWIST = (5.30, 5.58)               # the helmet's quarter-turn (unlock)
T_LIFT = (5.62, 6.00)                # lifted off over his head
T_LOWER = (6.00, 6.55)               # brought forward and down to his side
T_HAT = 7.15                         # the gust gets under the client's hat
T_FLY = 7.24                         # ... and takes it


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


def _keys(keys, col, **kw):
    return _pchip([k[0] for k in keys], [k[col] for k in keys], **kw)


def _rot(v, ang):
    a = ang * D2R
    ca, sa = math.cos(a), math.sin(a)
    return (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca)


# ============================================================================= camera
_CAM = [  # (t, x, y, zoom)
    (0.0, -165.0, -420.0, 0.86),
    (1.25, -60.0, -215.0, 1.35),
    (1.75, -90.0, -245.0, 1.31),
    (2.75, -180.0, -340.0, 1.18),
    (3.35, -320.0, -430.0, 1.08),
    (4.45, -410.0, -462.0, 1.10),
    (5.60, -432.0, -472.0, 1.15),
    (6.80, -450.0, -480.0, 1.20),
    (8.00, -462.0, -486.0, 1.24),
    (10.0, -472.0, -490.0, 1.27),
]
_CX = _keys(_CAM, 1)
_CY = _keys(_CAM, 2)
_CZ = _pchip([k[0] for k in _CAM], [math.log(k[3]) for k in _CAM])


def _shake(t):
    """Shudders on the tolls (s14's two, decaying; the third here), <= 4 px."""
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

# pelvis (boat-local): s14's rise at the cut, the hang, the climb, over onto the deck
_DV_P = [
    (0.00, 1020.0, 303.0),
    (0.45, 1018.0, 248.0),
    (0.90, 1017.0, 202.0),
    (1.20, 1016.0, 196.0),
    (1.62, 1011.0, 141.0),
    (1.94, 1005.0, 4.0),
    (2.55, 1003.0, 0.0),
    (2.85, 997.0, -82.0),
    (3.15, 989.0, -195.0),
    (3.45, 979.0, -282.0),
    (3.80, 905.0, -412.0),
    (4.10, 818.0, -484.0),
    (4.40, 752.0, -490.0),
    (4.75, 728.0, -488.0),
    (6.55, 728.0, -488.0),
    (6.85, 690.0, -489.0),
    (7.15, 684.0, -488.0),
    (10.0, 684.0, -488.0),
]
_DVX = _keys(_DV_P, 1, m0=-12.0)
_DVY = _keys(_DV_P, 2, m0=-120.0)
_DV_YAW = _pchip([0.0, 0.40, 0.85, 1.30, 1.62, 3.45, 3.95, 10.0], [81.4, 104.0, 122.0, 132.0, 172.0, 178.0, 180.0, 180.0])
_DV_HEAD = _pchip([0.0, 0.45, 0.85, 1.35, 1.62, 1.95, 2.08, 2.40, 2.62, 3.40, 3.72, 4.10, 4.50, 5.20, 5.60, 6.10, 6.45,
                   10.0],
                  [-42.5, -24.0, -6.0, -8.0, -20.0, -12.0, 14.0, 16.0, -16.0, -10.0, 10.0, 2.0, -3.0, -3.0, 2.0, -4.0,
                   -3.0, -3.0])
_DV_PITCH = _pchip([0.0, 0.6, 1.25, 1.65, 3.40, 3.65, 3.95, 4.30, 5.20, 5.55, 5.95, 6.45, 10.0],
                   [-3.0, 1.0, 4.0, 6.0, 6.0, 18.0, 12.0, 3.0, 2.0, 3.0, -2.0, 2.0, 2.0])

# feet: (t0, t1, from, to, arc lift (dx, dy)) - local ankle targets
_FL = [
    (0.50, 1.00, (1060.0, 560.0), _foot_rung(10), (10.0, -20.0)),
    (1.62, 1.94, _foot_rung(10), _foot_rung(7), (36.0, -24.0)),
    (2.85, 3.15, _foot_rung(7), _foot_rung(4), (36.0, -30.0)),
    (3.45, 3.80, _foot_rung(4), _foot_deck(850.0), (40.0, -150.0)),
    (4.10, 4.40, _foot_deck(850.0), _foot_deck(715.0), (0.0, -34.0)),
    (6.55, 6.80, _foot_deck(715.0), _foot_deck(668.0), (0.0, -26.0)),
]
_FR = [
    (0.60, 1.10, (985.0, 580.0), _foot_rung(11), (10.0, -20.0)),
    (1.30, 1.62, _foot_rung(11), _foot_rung(8), (36.0, -24.0)),
    (2.55, 2.85, _foot_rung(8), _foot_rung(5), (36.0, -30.0)),
    (3.15, 3.45, _foot_rung(5), _foot_rung(2), (36.0, -30.0)),
    (3.80, 4.10, _foot_rung(2), _foot_deck(785.0), (10.0, -110.0)),
    (4.45, 4.75, _foot_deck(785.0), _foot_deck(740.0), (0.0, -26.0)),
    (6.70, 6.95, _foot_deck(740.0), _foot_deck(700.0), (0.0, -20.0)),
]


def _dv_s14(t):
    """s14's diver, continued (valid to t = 1.0)."""
    return S14.DIVER.pose(_tau(min(t, 1.0)))


def _twist(t):
    """head_yaw of the helmet's quarter-turn (the head is hidden inside it)."""
    k = smoothstep(T_TWIST[0], T_TWIST[1], t) * (1.0 - smoothstep(T_LIFT[0], T_LIFT[0] + 0.2, t))
    return -40.0 * k


def _speak(t):
    """The unheard words: two small dips of the head (his name)."""
    return 3.5 * LIB.bump(t, 6.52, 6.57, 6.58, 6.65) + 3.0 * LIB.bump(t, 6.66, 6.71, 6.72, 6.80)


def _dv_body(t):
    """Base body pose: root, yaw, spine, head, legs (arms relaxed)."""
    tau = _tau(t)
    pb = BOAT.pose(tau)

    def Wd(q):
        return BOAT.to_world(q, tau, pb)
    x, y = Wd((_DVX(t), _DVY(t)))
    p = F.Pose(x, y, _DV_YAW(t))
    p.pitch = _DV_PITCH(t) + 1.2 * noise1(t * 0.4, 21)
    climb = smoothstep(1.2, 1.6, t) * (1.0 - smoothstep(3.8, 4.3, t))
    p.spine = [1.0 + 1.5 * climb, 1.0 + 1.5 * climb, 0.0]
    p.head = _DV_HEAD(t) + 1.5 * noise1(t * 0.3, 22) + _speak(t)
    p.head_yaw = _twist(t)
    br = math.sin(2 * math.pi * t / 2.6) * smoothstep(0.9, 1.4, t)       # breathing
    p.spine[2] += 1.2 * br
    fl, ml = _limb(_FL, t)
    fr, mr = _limb(_FR, t)
    for s, f_, m_ in (("L", fl, ml), ("R", fr, mr)):
        p.legs[s] = {"ik": Wd(f_), "pitch": -6.0 * m_, "toe": 0.0, "abd": 4.0}
    glow = 1.0 - 0.65 * _moon_k(t) + 0.35 * LIB.bump(t, T_TOLL - 0.02, T_TOLL + 0.05, T_TOLL + 0.2, T_TOLL + 1.2)
    p.eyes = dict(open=1.0, glow=glow, look=0.0)
    for tb in (4.62,):
        if tb - 0.06 < t < tb + 0.16:
            p.eyes["open"] = min(1.0, abs(t - tb - 0.05) / 0.11)
    kick_w = 1.0 - smoothstep(0.55, 1.05, t)
    if kick_w > 0.0:          # still kicking (s14) before the feet find the rungs
        q = p.copy()
        for s, ph in (("L", 0.0), ("R", math.pi)):
            k = math.sin(2 * math.pi * tau / 1.9 + ph)
            q.legs[s] = dict(hip=6.0 + 9.0 * k, abd=4.0, knee=12.0 + 10.0 * max(0.0, k), ankle=-14.0, toe=0.0)
        p = F.blend(q, p, 1.0 - kick_w, cast.DIVER)
    return p


@functools.lru_cache(maxsize=1024)
def _dv_body_pose(t):
    p = _dv_body(t)
    w = smoothstep(0.0, 0.65, t)
    if w < 1.0:
        p = F.blend(_dv_s14(t), p, w, cast.DIVER)
    return p


@functools.lru_cache(maxsize=1024)
def _dv_skel_body(t):
    """The body alone (arms don't move the head): for the helmet, its inlet and lamp."""
    return F.solve(_dv_body_pose(t), cast.DIVER)


def _inlet_world(t):
    """Where the hose is fixed on the helmet. costume puts the inlet at the helmet's side in a
    front view, mirrored as the yaw crosses 90 deg (a jump); slide it across instead."""
    p = _dv_body_pose(t)
    if 84.0 < p.yaw < 112.0:
        a = p.copy()
        a.yaw = 84.0
        b = p.copy()
        b.yaw = 112.0
        ia = costume.helmet_inlet(F.solve(a, cast.DIVER))
        ib = costume.helmet_inlet(F.solve(b, cast.DIVER))
        u = smoothstep(84.0, 112.0, p.yaw)
        return (lerp(ia[0], ib[0], u), lerp(ia[1], ib[1], u))
    return costume.helmet_inlet(_dv_skel_body(t))


# ---------------------------------------------------------------- the helmet comes off
@functools.lru_cache(maxsize=1)
def _helm_ref():
    """The worn helmet at the moment it lifts: skeleton, centre (world + boat-local),
    the pieces of the helmet proper (not the corselet) and its lamp."""
    sk = _dv_skel_body(T_LIFT[0])
    c, R, vp, vr, inlet = costume.helmet_frame(sk)
    pcs = costume.pieces(sk, DV_LOOK)["head"][2:]
    lamp = costume.helmet_lamp(sk)
    return dict(sk=sk, c=c, R=R, cl=BOAT.to_local(c, _tau(T_LIFT[0])), pieces=pcs, lamp=lamp)


_GRIP_L = (16.0, 34.0)               # near hand on the helmet (from its centre): low on the back
_GRIP_R = (-16.0, 30.0)              # far hand: low on the front (hidden behind it)
_CARRY = (-30.0, 22.0)               # near wrist from the pelvis while he carries it (boat-local)


def _carry_rot(t):
    return -4.0 + 2.0 * math.sin(2 * math.pi * (t - T_LOWER[1]) / 1.7) * smoothstep(T_LOWER[1], T_LOWER[1] + 0.4, t)


def _carry_wrist_local(t):
    sw = 3.0 * math.sin(2 * math.pi * (t - T_LOWER[1]) / 1.7) * smoothstep(T_LOWER[1], T_LOWER[1] + 0.4, t)
    return (_DVX(t) + _CARRY[0] + sw, _DVY(t) + _CARRY[1] + 0.4 * sw)


def _carry_c_local(t):
    w = _carry_wrist_local(t)
    g = _rot(_GRIP_L, _carry_rot(t))
    return (w[0] - g[0], w[1] - g[1])


@functools.lru_cache(maxsize=1)
def _helm_path():
    """Up off his head, forward (clear of his face) and down to his side: boat-local offsets
    from the worn centre, and the tilt."""
    cl = _helm_ref()["cl"]
    cc = _carry_c_local(T_LOWER[1])
    k = [
        (T_LIFT[0], 0.0, 0.0, 0.0),
        (5.70, 0.0, -12.0, 0.0),
        (5.92, -5.0, -118.0, -5.0),
        (T_LIFT[1], -14.0, -146.0, -8.0),
        (6.24, -120.0, -62.0, -16.0),
        (T_LOWER[1], cc[0] - cl[0], cc[1] - cl[1], _carry_rot(T_LOWER[1])),
    ]
    return _keys(k, 1), _keys(k, 2), _keys(k, 3)


def _helm_xform(t):
    """(centre world, rotation deg) of the helmet once it is off his head (t >= T_LIFT[0])."""
    tau = _tau(t)
    if t < T_LOWER[1]:
        cl = _helm_ref()["cl"]
        fx, fy, fr = _helm_path()
        c = (cl[0] + fx(t), cl[1] + fy(t))
        rot = fr(t)
    else:
        c = _carry_c_local(t)
        rot = _carry_rot(t)
    return BOAT.to_world(c, tau), rot


def _helm_now(t):
    """(centre world, rotation) of the helmet, worn or not."""
    if t < T_LIFT[0]:
        return costume.helmet_frame(_dv_skel_body(t))[0], 0.0
    return _helm_xform(t)


def _helm_center(t):
    return _helm_now(t)[0]


# ---------------------------------------------------------------- hands
_ARM_REST_L = dict(sh=10.0, abd=12.0, elbow=18.0, wrist=4.0, grip=0.35)
_ARM_REST_R = dict(sh=5.0, abd=12.0, elbow=14.0, wrist=4.0, grip=0.35)
_ARM_UP_L = dict(sh=148.0, abd=14.0, elbow=28.0, wrist=6.0, grip=0.4)     # s14: reaching up

_HL = [
    (0.30, 0.62, "start", _hand_rung(2), (30.0, -20.0)),
    (1.45, 1.70, _hand_rung(2), H_HOOK, (20.0, -20.0)),
    (3.50, 3.82, H_HOOK, H_RAIL_IN, (10.0, -40.0)),
]
_HR = [
    (0.55, 0.95, "start", _hand_rung(3), (30.0, -20.0)),
    (1.65, 1.92, _hand_rung(3), _hand_rung(1), (24.0, -20.0)),
    (2.00, 2.18, _hand_rung(1), "inlet", (30.0, -20.0)),
    (2.60, 2.88, "inlet", H_RAIL, (30.0, -30.0)),
]


@functools.lru_cache(maxsize=4)
def _s14_wrist_local(side):
    sk = F.solve(_dv_s14(0.3), cast.DIVER)
    return BOAT.to_local(sk.j["wrist_" + side], _tau(0.3))


def _coupling_local(t):
    """Boat-local position of the hose's coupling while he has it: on the helmet's inlet until
    T_REL, then in his far hand as he throws it out behind him (lets go at T_TOSS)."""
    tc = min(t, T_REL)
    p0 = BOAT.to_local(_inlet_world(tc), _tau(tc))
    if t <= T_REL:
        return p0
    u = clamp((t - T_REL) / (T_TOSS - T_REL))
    d = T_TOSS - T_REL
    h01 = 3.0 * u * u - 2.0 * u * u * u
    h11 = u * u * u - u * u
    return (p0[0] + h01 * TOSS[0] + h11 * d * V_TOSS[0], p0[1] + h01 * TOSS[1] + h11 * d * V_TOSS[1])


def _inlet_grip_local(t):
    """The far hand on the hose coupling (twisting it loose, then throwing it), local."""
    p = _coupling_local(min(t, T_TOSS))
    tc = min(t, T_REL)
    tw = 4.0 * math.sin(2 * math.pi * (tc - 2.18) / 0.11) * LIB.bump(tc, 2.16, 2.20, 2.34, 2.39)
    return (p[0] + 12.0 + tw, p[1] + 14.0)


def _resolve(segs, side):
    out = []
    for (t0, t1, a, b, lift) in segs:
        def r(q):
            if q == "start":
                return _s14_wrist_local(side)
            if q == "inlet":
                return _inlet_grip_local
            return q
        out.append((t0, t1, r(a), r(b), lift))
    return out


_HL_R = _resolve(_HL, "L")
_HR_R = _resolve(_HR, "R")


def _hand_targets(t, rest=None):
    """{side: (world wrist target, weight, grip)}. rest: where the wrists hang (world)."""
    tau = _tau(t)
    pb = BOAT.pose(tau)
    out = {}
    # climbing
    wl = smoothstep(0.25, 0.55, t) * (1.0 - smoothstep(3.85, 4.20, t))
    wr = smoothstep(0.45, 0.85, t) * (1.0 - smoothstep(3.70, 4.05, t))
    if wl > 0.0:
        q, mv = _limb(_HL_R, t)
        out["L"] = (BOAT.to_world(q, tau, pb), wl, 1.0 - 0.6 * mv)
    if wr > 0.0:
        q, mv = _limb(_HR_R, t)
        out["R"] = (BOAT.to_world(q, tau, pb), wr, 1.0 - 0.6 * mv)
    # the helmet: both hands up to it (from where they hang), the turn, the lift; the far
    # hand lets go on the way down, the near one carries it
    if rest is not None and t >= _HELM_HANDS["L"][0]:
        c, rot = _helm_now(t)
        tw = _twist(t)
        for side, (a0, a1, r0, r1, g) in _HELM_HANDS.items():
            if t < a0 or (r1 is not None and t >= r1 + 0.05):
                continue
            gx, gy = _rot(g, rot)
            grip = (c[0] + gx + 0.25 * tw, c[1] + gy)          # round with the quarter-turn
            if t < a1:
                tgt = _arc(rest[side], grip, (t - a0) / (a1 - a0), (-26.0, 0.0))
            elif r0 is not None and t > r0:
                tgt = _arc(grip, rest[side], (t - r0) / (r1 - r0), (-8.0, 6.0))
            else:
                tgt = grip
            w = smoothstep(a0, a0 + 0.05, t)
            if r1 is not None:
                w *= 1.0 - smoothstep(r1, r1 + 0.05, t)
            out[side] = (tgt, w, 1.0)
    return out


_HELM_HANDS = {  # side: (rise from, on the helmet by, let go from, back at the side by, grip)
    "L": (5.00, 5.28, None, None, _GRIP_L),
    "R": (5.06, 5.32, 6.30, 6.56, _GRIP_R),
}


def _arc(a, b, u, lift):
    u = clamp(u)
    e = ease("inout", u)
    k = math.sin(math.pi * u)
    return (lerp(a[0], b[0], e) + lift[0] * k, lerp(a[1], b[1], e) + lift[1] * k)


def _dv_arms(p, t):
    up = 1.0 - smoothstep(0.35, 0.8, t)
    p.arms["L"] = {k: lerp(_ARM_REST_L[k], _ARM_UP_L[k], up) for k in _ARM_REST_L}
    p.arms["R"] = dict(_ARM_REST_R)
    rest = None
    if t >= _HELM_HANDS["L"][0]:
        skr = F.solve(p, cast.DIVER)
        rest = {s: skr.j["wrist_" + s] for s in ("L", "R")}
    for side, (tgt, w, grip) in _hand_targets(t, rest).items():
        q = arm_ik(p.copy(), side, tgt, cast.DIVER, elbow_out=False)
        a = p.arms[side]
        a["sh"] = lerp(a["sh"], q.arms[side]["sh"], w)
        a["elbow"] = lerp(a["elbow"], q.arms[side]["elbow"], w)
        a["wrist"] = lerp(a["wrist"], 20.0, w)
        a["grip"] = lerp(a["grip"], grip, w)
    return p


@functools.lru_cache(maxsize=1024)
def dv_skel(t):
    p = _dv_body_pose(t).copy()
    p = _dv_arms(p, t)
    if t < 0.65:          # the arms too come out of s14's
        w = smoothstep(0.0, 0.65, t)
        s14 = _dv_s14(t)
        for s in ("L", "R"):
            p.arms[s] = {k: lerp(s14.arms[s].get(k, 0.0), p.arms[s].get(k, 0.0), w) for k in p.arms[s]}
    return F.solve(p, cast.DIVER)


def _eyes_vis(t, sk):
    """The bare head's eyes once the lifted helmet has cleared them."""
    if t < T_LIFT[0]:
        return 0.0
    if t >= T_LIFT[1]:
        return 1.0
    c, rot = _helm_xform(t)
    R = _helm_ref()["R"]
    e1, e2, r, w, front = F.eye_points(sk, DV_BARE)
    ey = min(e1[1], e2[1])
    return smoothstep(2.0, 20.0, ey - (c[1] + R * 0.95))


def _paint(ctx, pcs, color=None):
    for fn, col, eo in pcs:
        if eo:
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.new_path()
        fn(ctx)
        c = color or col or INK
        ctx.set_source_rgb(*c[:3])
        ctx.fill()
        if eo:
            ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def _draw_helmet_off(L, t, color=None):
    ref = _helm_ref()
    c, rot = _helm_xform(t)
    L.save()
    L.translate(c[0], c[1])
    L.rotate(rot * D2R)
    L.translate(-ref["c"][0], -ref["c"][1])
    _paint(L, ref["pieces"], color)
    L.restore()


def _lamp_point(t, sk):
    """The helmet lamp: (position, intensity)."""
    if t < T_LIFT[0]:
        return costume.helmet_lamp(sk)[0], 1.0
    ref = _helm_ref()
    c, rot = _helm_xform(t)
    p0 = ref["lamp"][0]
    d = _rot((p0[0] - ref["c"][0], p0[1] - ref["c"][1]), rot)
    return (c[0] + d[0], c[1] + d[1]), 0.6


def draw_diver(f, L, t, sk=None):
    sk = sk or dv_skel(t)
    bare = t >= T_LIFT[0]
    look = DV_BARE if bare else DV_LOOK
    # he stands in front of the lantern: keep its bloom off his silhouette
    with f.emit() as G:
        G.save()
        G.set_operator(cairo.OPERATOR_CLEAR)
        F.draw_figure(None, sk, look, G, color=(0, 0, 0), eyes=False)
        if bare:
            _paint(G, costume.pieces(sk, DV_LOOK)["head"][:2], (0, 0, 0))
            _draw_helmet_off(G, t, (0, 0, 0))
        G.restore()
    if not bare:
        F.draw_figure(f, sk, DV_LOOK, L)
        return sk
    F.draw_figure(f, sk, DV_BARE, L, eyes=False)
    _paint(L, costume.pieces(sk, DV_LOOK)["head"][:2])          # the corselet stays on
    vis = _eyes_vis(t, sk)
    if vis > 0.01:
        F.draw_eyes(f, sk, DV_BARE, L, alpha=vis)
    _draw_helmet_off(L, t)
    return sk


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


def _start(t):
    """His start at the toll."""
    return LIB.bump(t, T_TOLL, T_TOLL + 0.07, T_TOLL + 0.16, T_TOLL + 0.9)


def _cl_mine(t):
    tau = _tau(t)
    xl, ml = _cfoot(_CFL, t, -624.0)
    xr, mr = _cfoot(_CFR, t, -576.0)
    x = (xl + xr) / 2.0 - 2.0
    deck = BOAT.deck_y(x, tau)
    st = _start(t)
    p = F.Pose(x, deck - 318.0 + 4.0 * (ml + mr) - 3.0 * st, 0.0)
    p.pitch = 5.0 - 3.0 * smoothstep(1.9, 2.3, t) * (1.0 - smoothstep(3.9, 4.4, t)) - 5.0 * st
    p.spine = [0.0, 0.0, -2.0 - 3.0 * st]
    for s, fx, m_ in (("L", xl, ml), ("R", xr, mr)):
        dy = BOAT.deck_y(fx, tau)
        p.legs[s] = {"ik": (fx, dy - 0.043 * CLH - 16.0 * m_), "pitch": -8.0 * m_, "toe": 0.0, "abd": 3.0}
    knife = smoothstep(1.6, 2.2, t)
    p.arms["L"] = dict(sh=lerp(-6.0, 10.0, knife) + 6.0 * st, abd=6.0, elbow=lerp(16.0, 40.0, knife) + 8.0 * st,
                       wrist=-10.0 * knife, grip=1.0)
    p.arms["R"] = dict(sh=lerp(4.0, -10.0, knife) + 8.0 * st, abd=7.0, elbow=lerp(16.0, 24.0, knife) + 10.0 * st,
                       wrist=0.0, grip=0.5 + 0.3 * st)
    p.head = -2.0 - 9.0 * st
    p.eyes = dict(open=1.0, glow=0.9 + 0.15 * smoothstep(T_TOLL, T_TOLL + 0.1, t), look=0.0)
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


@functools.lru_cache(maxsize=1024)
def _cl_pose(t):
    p = _cl_mine(t)
    # he watches the diver come: the helmet, the man - not his eyes, until the helmet is off
    tgt = _dv_skel_body(t).j["head"]
    lower = 70.0 * (1.0 - smoothstep(5.75, 6.05, t))
    p = _look(p, cast.CLIENT, (tgt[0], tgt[1] + lower), 0.85 * smoothstep(0.5, 1.2, t))
    w = smoothstep(0.0, 0.8, t)
    if w < 1.0:
        p = F.blend(_cl_s14(t), p, w, cast.CLIENT)
    for tb in (1.15, 3.95, 5.30):          # blinks; none once he has seen the eyes
        if tb - 0.06 < t < tb + 0.16:
            p.eyes["open"] = min(p.eyes["open"], abs(t - tb - 0.05) / 0.11)
    p.extra["vel"] = (0.0, 0.0)
    p.extra["t"] = t
    return p


@functools.lru_cache(maxsize=1024)
def cl_skel(t):
    return F.solve(_cl_pose(t), cast.CLIENT)


def _cl_gasp(t):
    return LIB.bump(t, T_TOLL + 0.02, T_TOLL + 0.12, T_TOLL + 0.22, T_TOLL + 1.1)


def _cl_ember(t):
    return (0.55 + 0.1 * noise1(_tau(t) * 0.7, 9)) * 0.3 + 1.1 * _cl_gasp(t)


def _cl_look(t):
    lk = cast.client(ember=_cl_ember(t), coat_flow=0.12 + 0.06 * noise1(t * 0.5, 4))
    lk.eye_size = 1.0 + 0.4 * smoothstep(T_TOLL + 0.01, T_TOLL + 0.12, t)
    if t >= T_HAT:
        lk.hat = None
        lk.hair = "slick"
    return lk


def _knife(L, sk):
    w = sk.j["wrist_L"]
    h = sk.j["hand_L"]
    ang = math.degrees(math.atan2(h[1] - w[1], h[0] - w[0])) - 35.0
    S.draw_knife(L, h[0], h[1], angle=ang, s=0.42)


def _ember_halo(f, t, sk):
    """The cigar's own ember is a few px: on the gasp a warm halo blooms round it (as s14)."""
    k = 0.85 * _cl_gasp(t)
    if k <= 0.01 or sk.side_w > 0.85:
        return
    p = F.head_point(sk, 0.86, 0.22, front_x=0.16, front_y=0.20)
    atmos.lamp(f, p, radius=5.0, intensity=k, halo=7.0, core=0.0, flicker="ember", t=t, seed=21)


def draw_client(f, L, t, sk=None):
    sk = sk or cl_skel(t)
    _knife(L, sk)
    F.draw_figure(f, sk, _cl_look(t), L)
    return sk


# ============================================================================= the hat
@functools.lru_cache(maxsize=1)
def _hat_ref():
    pts = LIB.hat_on_head(cl_skel(T_HAT))
    return pts, LIB.centroid(pts)


def _hat_keys():
    c0 = _hat_ref()[1]
    k = [  # (t, x, y, rot): up off his head, across the moon, high over the diver, down into the
        # sea by the stern (during the dip)
        (T_HAT, c0[0], c0[1], 0.0),
        (T_FLY, c0[0] + 4.0, c0[1] - 8.0, 6.0),
        (7.40, c0[0] + 50.0, c0[1] - 110.0, 18.0),
        (7.60, -550.0, -945.0, 30.0),
        (7.80, -440.0, -935.0, 110.0),
        (7.95, -320.0, -900.0, 190.0),
        (8.10, -245.0, -770.0, 250.0),
        (8.27, -190.0, -560.0, 300.0),
        (8.44, -148.0, -330.0, 335.0),
        (8.58, -122.0, -120.0, 352.0),
        (8.66, -110.0, -20.0, 358.0),
    ]
    return k


_HK = None


def _hat_fn():
    global _HK
    if _HK is None:
        k = _hat_keys()
        _HK = (_keys(k, 1, m1=260.0), _keys(k, 2, m1=2300.0), _keys(k, 3, m1=100.0), k[-1][0])
    return _HK


def _hat_splash():
    fx, fy, fr, t_end = _hat_fn()
    # first time the hat's centre reaches the surface after the flight
    for i in range(400):
        tt = T_FLY + i * 0.005
        x, y = fx(tt), fy(tt)
        if y >= S.sea_y(x, _tau(tt)) - 6.0:
            return tt, x
    return t_end, fx(t_end)


@functools.lru_cache(maxsize=1)
def _hat_splash_c():
    return _hat_splash()


def _hat_pose(t):
    """(outline world pts, centre) of the hat once the gust has it."""
    pts0, c0 = _hat_ref()
    fx, fy, fr, t_end = _hat_fn()
    ts, xs = _hat_splash_c()
    if t <= ts:
        c = (fx(t), fy(t))
        rot = fr(t)
    else:
        a = t - ts
        c = (xs + 30.0 * a, S.sea_y(xs, _tau(t)) - 4.0 + 160.0 * a * a / (1.0 + a))
        rot = fr(ts) + 8.0 * (1.0 - math.exp(-a / 0.4)) + 3.0 * math.sin(2.0 * a)
    return LIB.rigid(pts0, c0, c, rot), c


def _smear(L, polys, rgb, alpha=1.0):
    """Fill several copies of a shape as one motion-blurred shape (their average coverage)."""
    n = len(polys)
    L.push_group()
    L.set_operator(cairo.OPERATOR_ADD)
    for pts in polys:
        L.new_path()
        draw.poly(L, pts)
        L.set_source_rgba(rgb[0], rgb[1], rgb[2], 1.0 / n)
        L.fill()
    L.pop_group_to_source()
    L.paint_with_alpha(alpha)


_HAT_SHUTTER = 0.5 / 24.0
_HAT_SAMPLES = 9


def _draw_hat(L, f, t, ms):
    """The fedora once the gust has it: drawn with its own motion blur (it is the only fast
    thing in the frame), a moonlit rim on the side toward the moon, and a silhouette against
    the moon's glow when it crosses it."""
    pts, c = _hat_pose(t)
    n = _HAT_SAMPLES
    polys = [_hat_pose(t + _HAT_SHUTTER * (i / (n - 1.0) - 0.5))[0] for i in range(n)]
    sc = f.cam.to_screen(c)
    if math.hypot(sc[0] - ms[0], sc[1] - ms[1]) < MOON_R + 160.0:
        _occlude_emit(f, lambda G: draw.poly(G, pts))
    md = LIB.moon_dir_world(f.cam, c, ms)
    off = 3.0 / f.cam.zoom
    _smear(L, [[(x + md[0] * off, y + md[1] * off) for x, y in q] for q in polys], LIB.MOONLIT, 0.55)
    _smear(L, polys, INK)


# ============================================================================= the cut hose
_NH = 40
_HDT = 1.0 / 120.0
_HT0, _HT1 = 0.0, 10.05


def _sea_y_np(x, tau):
    y = np.zeros_like(x)
    for A, Lw, Tw, ph, d in SS.SWELL:
        y += A * np.sin(2 * np.pi * (x / Lw - d * tau / Tw) + ph)
    return SS.SEA_Y + y


class _Hose:
    """The cut red hose from s14's state at the cut. Node 0 is fixed on the helmet's inlet
    until he unscrews the coupling (T_REL), in his hand as he throws it out behind him, then
    (T_TOSS) free and heavy (brass). Above the surface it
    falls (air); below, it drifts and sinks slowly in the current (as s14)."""

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
        pairs = [np.arange(par, n - 1, 2) for par in (0, 1)]
        bend = [np.array([i for i in range(n - 2) if i % 4 in grp], dtype=int) for grp in ((0, 1), (2, 3))]
        g_w = np.array([0.0, 70.0])
        g_a = np.array([0.0, 2600.0])
        for k in range(steps):
            t = _HT0 + k * dt
            tau = _tau(t)
            vel = (P - prev) / dt
            sea = _sea_y_np(P[:, 0], tau)
            wet = (P[:, 1] > sea)[:, None]
            cur = np.stack([26.0 + 10.0 * np.sin(0.37 * tau + P[:, 1] / 700.0),
                            -40.0 + 30.0 * np.sin(0.5 * tau + P[:, 1] / 400.0)], axis=1)
            acc = np.where(wet, g_w - 1.6 * (vel - cur), g_a - 0.5 * vel)
            pin = t < T_TOSS
            if not pin and wet[0, 0]:
                acc[0, 1] += 420.0                 # brass sinks
            new = P + vel * dt + acc * dt * dt
            prev, P = P, new
            w = inv.copy()
            if pin:
                pa = np.array(BOAT.to_world(_coupling_local(t), tau), np.float64)
                w[0] = 0.0
            for _ in range(10):
                if pin:
                    P[0] = pa
                for i0 in pairs:
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
            if not pin and self.splash is None and P[0, 1] > _sea_y_np(P[:1, 0], tau)[0]:
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


# ============================================================================= water
@functools.lru_cache(maxsize=1)
def _t_surface():
    """When the helmet's crown breaks the surface (and its x)."""
    for i in range(300):
        t = i * 0.004
        sk = _dv_skel_body(t)
        c, R = costume.helmet_frame(sk)[:2]
        if c[1] - R <= S.sea_y(c[0], _tau(t)):
            return t, c[0]
    return 0.3, -55.0


def _runoff(f, t, sk):
    """Water off the helmet and the suit as he comes out: sheets on the dome, then drips from
    the corselet's rim, the elbows and the boots, falling back into the sea."""
    ts, xs = _t_surface()
    if t < ts or t > 5.0:
        return
    tau = _tau(t)
    c = f.ctx
    col = LIB.SPRAY
    # sheets running down the dome: short pale streaks sliding off it
    k = smoothstep(ts, ts + 0.12, t) * (1.0 - smoothstep(ts + 0.5, ts + 1.4, t))
    if k > 0.01:
        hc, R = costume.helmet_frame(sk)[:2]
        c.save()
        c.new_path()
        draw.circle(c, hc, R * 0.97)
        c.clip()
        for j in range(6):
            u = (hash01(61, j, 0) * 2.0 - 1.0) * 0.85
            sp = 0.7 + 0.6 * hash01(61, j, 1)
            ph = hash01(61, j, 2)
            pos = (ph + sp * (t - ts)) % 1.0
            pts = []
            for i in range(6):
                v = max(0.0, pos - 0.3) + (pos - max(0.0, pos - 0.3)) * i / 5.0
                yy = hc[1] - R + v * 2.0 * R
                half = math.sqrt(max(0.0, R * R - (yy - hc[1]) ** 2))
                pts.append((hc[0] + u * half + 1.2 * math.sin(yy / 6.0 + ph * 6.0 + 7.0 * t), yy))
            LIB.draw_hose(c, pts, 1.5 / f.cam.zoom, color=LIB.MOONLIT, alpha=0.4 * k * (1.0 - pos) ** 0.5)
        c.restore()
    # drips: emitted from points on the suit, then ballistic (g = 2600)
    g = 2600.0
    hz = 30.0
    big = []
    k1 = int(t * hz)
    for kk in range(max(int(ts * hz), k1 - 18), k1 + 1):
        te = kk / hz
        if te > t:
            continue
        age_e = te - ts
        rate = math.exp(-max(0.0, age_e) / 1.6)
        ske = dv_skel(te)
        srcs = (ske.j["elbow_L"], ske.j["elbow_R"], ske.j["hand_L"], ske.j["heel_L"], ske.j["heel_R"],
                costume.helmet_frame(ske)[0])
        for i, src in enumerate(srcs):
            if hash01(62, kk, i) > rate * 0.55:
                continue
            ox = (hash01(63, kk, i) - 0.5) * 30.0
            oy = 50.0 if i == 5 else 0.0
            x0, y0 = src[0] + ox, src[1] + oy
            if y0 > S.sea_y(x0, _tau(te)):
                continue
            dt = t - te
            x = x0 + 10.0 * (hash01(64, kk, i) - 0.5) * dt
            y = y0 + 0.5 * g * dt * dt
            if y > S.sea_y(x, tau) + 4.0:
                continue
            r = 1.4 + 1.8 * hash01(65, kk, i)
            big.append((x, y, r, r * (1.0 + min(g * dt / 300.0, 4.0))))
    if big:
        c.new_path()
        for x, y, r, Ln in big:
            c.save()
            c.translate(x, y)
            c.rotate(math.pi / 2)
            c.scale(Ln, r)
            c.new_sub_path()
            c.arc(0, 0, 1.0, 0, 2 * math.pi)
            c.restore()
        c.set_source_rgba(col[0], col[1], col[2], 0.7)
        c.fill()


def _splashes(f, t):
    tau = _tau(t)
    ts, xs = _t_surface()
    LIB.foam(f, tau, xs, ts + OFF - 0.02, 120.0, 41, k=0.8, life=2.6)
    LIB.splash(f, tau, xs, ts + OFF, 26, 0.35, 42)
    hs = HOSE.splash_at()
    if hs:
        LIB.splash(f, tau, hs[1], hs[0] + OFF, 22, 0.32, 43)
        LIB.foam(f, tau, hs[1], hs[0] + OFF, 70.0, 44, k=0.6, life=2.0)
    th, xh = _hat_splash_c()
    LIB.splash(f, tau, xh, th + OFF, 24, 0.3, 45)
    LIB.foam(f, tau, xh, th + OFF, 80.0, 46, k=0.7, life=2.2)


# ============================================================================= light
def _moon_screen(f):
    return (MOON[0], S.horizon_y(f) - MOON[1])


def _occlude_emit(f, path_fn):
    """Cut a silhouette out of the glow layer (it is added over everything at the end): the
    moon's and the lantern's glow must not shine through things in front of them."""
    with f.emit() as G:
        G.save()
        G.set_operator(cairo.OPERATOR_CLEAR)
        G.new_path()
        path_fn(G)
        G.fill()
        G.restore()


def _boat_over_moon(f, tau, ms):
    """The davit's arm can cross the moon as the camera follows him up: cut the boat's
    silhouette out of the moon's glow when it does."""
    top = f.cam.to_screen(BOAT.to_world((800.0, -700.0), tau))[1]
    if top > ms[1] + MOON_R + 40.0:
        return
    with f.emit() as G:
        G.save()
        G.set_operator(cairo.OPERATOR_CLEAR)
        BOAT.draw(G, tau, pump_angle=150.0 * tau, winch_angle=-2.0 * LIB.crank_deg(LIB.T_STOP), hose=False,
                  hook=False)
        G.restore()


def _moon_k(t):
    """How strongly the moon shows in his port (as it clears the water, facing us)."""
    return LIB.bump(t, 0.80, 0.98, 1.35, 1.62)


def _moon_in_port(f, t, sk):
    k = _moon_k(t)
    if k <= 0.01:
        return
    c, R, vp, vr, inlet = costume.helmet_frame(sk)
    fwd = 1.0 if math.cos((sk.pose.yaw + sk.pose.head_yaw) * D2R) >= 0 else -1.0
    w = sk.side_w
    port_c = lerp((c[0] + fwd * R * 0.98, vp[1]), vp, w)
    g = lerp(vp, port_c, 0.5)
    if g[1] > S.sea_y(g[0], _tau(t)) - vr * 0.6:
        return
    ms = _moon_screen(f)
    sp = f.cam.to_screen(g)
    dx, dy = ms[0] - sp[0], ms[1] - sp[1]
    d = math.hypot(dx, dy) or 1.0
    m = (g[0] + dx / d * vr * 0.34, g[1] + dy / d * vr * 0.34)
    rr = vr * 0.36
    cc = f.ctx
    cc.save()
    cc.new_path()
    draw.circle(cc, g, vr)
    cc.clip()
    draw.circle(cc, m, rr)
    cc.set_source_rgba(*PAL.moon, 0.92 * k)
    cc.fill()
    cc.restore()
    with f.emit() as G:
        draw.glow_disc(G, m, rr * 3.0, PAL.moon, 0.55 * k)


def _under_light(f, t, sk):
    k = 1.0 - smoothstep(0.6, 2.2, t)
    atmos.underwater_rays(f, surface_y=0.0, t=_tau(t), spacing=190.0, angle=95.0, fan=8.0, length=1800.0,
                          intensity=0.16, density=0.5, seed=14, blur=18, color=S.mix(PAL.moon, PAL.surface, 0.5))
    if k > 0.01:
        ps = f.cam.to_screen(sk.j["chest"])
        LIB.screen_glow(f, (ps[0], ps[1] - 80.0), 640.0 * f.cam.zoom / 0.5, PAL.surface, 0.10 * k)


def _beam(f, t, sk):
    """His lamp's beam up through the water (s14), gone as the helmet surfaces."""
    if t > 1.0:
        return
    p, d, _ = costume.helmet_lamp(sk)
    sea = S.sea_y(p[0], _tau(t))
    k = smoothstep(sea - 10.0, sea + 70.0, p[1])
    if k <= 0.01:
        return
    ang = math.degrees(math.atan2(d[1], d[0]))
    L = max(60.0, (p[1] - sea) / max(0.2, -d[1]) + 40.0)
    atmos.beam(f, p, ang, length=L, half_angle=9.0, intensity=0.42 * k, falloff=0.8, soft=0.5, core=0.5,
               fog=0.4, pool=0.0, dust=0.35, glare=0.0, t=_tau(t), seed=5)


def _lamp(f, t, sk):
    p, k = _lamp_point(t, sk)
    atmos.lamp(f, p, radius=8.0, intensity=0.9 * k, halo=4.0, core=0.3, t=_tau(t), seed=6)


def _bubbles(f, t):
    """s14's exhaust bubbles: the last of them, until the valve leaves the water."""
    ts = _t_surface()[0]
    atmos.bubbles(f, S14._VALVE, rate=2.6, t=_tau(t), seed=33, rise=(240.0, 380.0), size=(1.5, 5.5), spread=8.0,
                  current=12.0, surface=6.0, height=2400.0, alpha=0.8, t_end=ts + OFF - 0.1)


def _line(L, st):
    P, top = st["pivot"], st["top"]
    LIB.draw_hose(L, [P, top], 5.0, color=LIB.PALE)
    draw.circle(L, (top[0], top[1] + 4.0), 8.0)
    L.set_source_rgb(*INK)
    L.fill()


def _bell(L, f, t, st, md):
    tau = _tau(t)
    wet = 1.0 - smoothstep(S14.T_CLEAR, S14.T_CLEAR + 3.0, tau)
    ring = clamp(st["ring"])
    LIB.draw_bell_lit(L, st, md, f.cam.zoom, rim=0.30 + 0.25 * wet + 0.45 * ring,
                      sheen=0.18 + 0.28 * wet + 0.30 * ring)


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
        S14._deck_hose(L, tau)
    _boat_over_moon(f, tau, ms)
    BOAT.draw_lights(f, tau, lantern=1.0, window=0.5, masthead=1.0)
    with f.layer() as L:
        draw_client(f, L, t, ck)
        hp = HOSE.points(t)
        LIB.draw_hose(L, hp, LIB.HOSE_W)
        if t >= T_REL:
            _coupling(L, hp)
        _line(L, st)
        _bell(L, f, t, st, md)
        draw_diver(f, L, t, dk)
        if t >= T_HAT:
            _draw_hat(L, f, t, ms)
    S.water_front(f, tau, alpha=0.08, bright=BRIGHT)
    _ember_halo(f, t, ck)
    if tau > S14.T_BREAK - 0.1:
        LIB.bell_pour(f, tau, BOAT, S14.T_CLEAR, rate=1.0, seed=5)
    _runoff(f, t, dk)
    _bubbles(f, t)
    _splashes(f, t)
    _moon_in_port(f, t, dk)
    _lamp(f, t, dk)
    # the toll: a breath of light off the bell
    fl = st["ring"] if tau >= LIB.TOLLS[2][0] else 0.0
    f.post["flash"] = max(f.post.get("flash", 0.0), 0.05 * clamp(fl) * math.exp(-(tau - LIB.TOLLS[2][0]) / 0.12))
    f.post["flash_color"] = PAL.moon
    f.post["vignette"] = lerp(f.post["vignette"], 0.38, 0.6)


def motion_blur(t, T):
    if T_REL - 0.02 < t < T_REL + 0.35:          # the hose drops away
        return 3
    if T_TOLL - 0.02 < t < T_TOLL + 0.25:        # the shudder of the toll
        return 3
    return 1                                     # (the hat blurs itself: see _draw_hat)


def cues(T):
    ts = _t_surface()[0]
    hs = HOSE.splash_at()
    th = _hat_splash_c()[0]
    return [
        Cue(ts, "the helmet breaks the surface: water sheets off the brass dome, air gasps through the exhaust "
                "valve", gain_db=-8, pan=0.15, dur=1.2),
        Cue(0.62, "a gloved hand slaps onto an iron ladder rung", gain_db=-12, pan=0.15),
        Cue(0.95, "the other hand clanks onto a rung; boots find the rungs under water (muffled)", gain_db=-14,
            pan=0.15),
        Cue(1.30, "water streaming off the suit as he hauls himself up the ladder", gain_db=-13, pan=0.15, dur=2.2),
        Cue(1.62, "a heavy wet boot on an iron rung", gain_db=-11, pan=0.15),
        Cue(1.94, "boot on a rung", gain_db=-12, pan=0.1),
        Cue(2.20, "the hose coupling unscrewed from the helmet: a gritty brass thread turning", gain_db=-14,
            pan=0.1, dur=0.2),
        Cue(T_REL, "the coupling comes free: a last squeal of thread, a hiss of air", gain_db=-13, pan=0.1),
        Cue(2.42, "the client's shoe steps back on the wet deck (slow, careful)", gain_db=-16, pan=-0.4),
        Cue(T_TOSS - 0.06, "he throws the hose out behind him: the rubber whips off the ladder and slithers down "
                           "the hull", gain_db=-11, pan=0.2, dur=0.5),
        Cue(2.85, "boot on a rung", gain_db=-12, pan=0.05),
        Cue(2.92, "a second step back", gain_db=-16, pan=-0.4),
        Cue(hs[0] if hs else 3.05, "the brass coupling plops into the sea; the hose follows it in", gain_db=-13,
            pan=0.45),
        Cue(3.15, "boot on a rung", gain_db=-12, pan=0.05),
        Cue(3.45, "boot on the top rung; a third step back from the client", gain_db=-12, pan=0.0),
        Cue(3.80, "a heavy wet boot comes down on the deck", gain_db=-9, pan=0.0),
        Cue(3.95, "the client's heel finds the pump frame behind him: a soft knock", gain_db=-15, pan=-0.45),
        Cue(4.10, "the second boot on deck; water drips off the suit", gain_db=-10, pan=-0.05),
        Cue(4.40, "a step forward on the boards, the bell swishing past behind him, the davit creaking",
            gain_db=-12, pan=0.2, dur=0.6),
        Cue(4.75, "he plants his feet; the drip of water on the boards", gain_db=-14, pan=0.0),
        Cue(T_TWIST[1] - 0.03, "the helmet unlocks: a quarter-turn clunk of the interrupted thread", gain_db=-8,
            pan=0.0),
        Cue(5.72, "the seal pops; water spills out of the helmet and the breastplate", gain_db=-9, pan=0.0,
            dur=0.7),
        Cue(6.05, "his first breath of night air (a long, slow inhale)", gain_db=-14, pan=0.0, dur=0.6),
        Cue(6.52, "(optional) his voice, very low and unintelligible: he says his name; it must not be heard",
            gain_db=-26, pan=0.0, dur=0.3),
        Cue(T_LOWER[1], "the helmet settles against his hip; a step toward the client (the boot lands at 6.80, "
                        "under the toll)", gain_db=-13, pan=-0.05),
        Cue(T_TOLL, "THE BELL TOLLS (tonic D) the third time, right over them: the loudest sound in the film; "
                    "let it ring on over the dip to black and into s16", gain_db=0, pan=0.2, dur=6.0),
        Cue(T_TOLL + 0.05, "the client's sharp intake of breath; the cigar crackles", gain_db=-16, pan=-0.3),
        Cue(T_HAT - 0.08, "a gust off the sea takes the client's hat", gain_db=-12, pan=-0.2, dur=1.2),
        Cue(th, "the fedora slaps onto the water by the stern", gain_db=-14, pan=0.35),
    ]
