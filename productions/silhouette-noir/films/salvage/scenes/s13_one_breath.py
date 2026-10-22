"""s13 · ONE BREATH: at depth by the wreck, the hose cut, one minute of air (11.0 s).

IN  (scroll 'up' = descent from s12, window -0.5..0.5; s12's bottom edge meets s13's top
    edge): the slack red hose comes in at the top edge at screen x ~531-536 (held there
    through the window), swings down in one loose bend to the back of his helmet and lies in
    a coil round his legs. The diver stands on the silt by the wreck's quarter, lamp-lit, his
    head tipped back, the beam running up the dead hose; no bubbles (the breath stopped at
    the cut). -0.5: pelvis (512, 1731), helmet (452, 1484), zoom 1.12; 0.5: pelvis
    (515, 1423), helmet (451, 1153), zoom 1.22.

Beats (scene-local s; L18 A 1.5 ... calm 6.515-7.305; L19 My 8.2 ... that 9.372-9.848):
  -0.5-1.05        the camera settles onto him; he looks up the hose (a blink 0.92-1.14)
  1.05-2.45        his eyes come down off it, the beam swings level to frame right, and the
                   camera pushes in to the helmet port (it lands on [helmet@2.336])
  2.45-7.05        close on the port (held at screen ~(590, 980)); the push advances a notch
                   on each heartbeat (97 settling to 60 bpm), a small thump on each lub-dub;
                   his eyes dart (2.62-3.25), then
  [one@3.59]       squeeze shut (3.57-3.75), the push going on in the dark of the port
  [calm@6.515]     they open, slowly (6.515-6.965)
  7.05-7.95        pull back; he turns to profile and looks down at his chest weights; both
                   gloves come up to the front weight's hook
  [My@8.2]         two pulls on the hooks (8.02, 8.17); 8.37 the weights fall
  8.37-8.93        the camera goes down with the lead and opens out to hold all of him; the
                   one big bubble release climbs out of the top of frame;
  [taught@8.931]   WEIGHTS DROP: they hit the silt at 8.927 / 8.937 (silt y ~1494), puffs
                   in the lamp pool
  8.55             lighter: his heels leave the silt (a slow rise that quickens)
  9.06, 9.29       he kicks off the lead boots: one lands on [me@9.222] (9.265), the other
                   just after [that@9.372] (9.573)
  9.42-10.05       his head and the beam swing up; from 9.55 the camera catches him up and
                   pulls out (zoom 1.66 -> 1.25 by 10.5); the silt and the coils fall away
                   below, snow streaks down
OUT (scroll 'down' = ascent, window 10.5-11.5; s13's top edge meets s14's bottom edge): he
    rises through screen centre, beam straight up, bubbles above, the hose trailing straight
    down out of frame. 10.5: helmet (480, 825), pelvis (567, 1095), zoom 1.25; 11.0: helmet
    (474, 772), pelvis (566, 1029); 11.5: helmet (473, 705), lamp (450, 653), pelvis
    (565, 945), zoom 1.14.

Sound: silence and a heartbeat; two clicks; ONE big bubble release; the WEIGHTS DROP (the key
sync hit); two boots; the water rush.
"""
import functools
import math

import numpy as np

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor, dangle
from engine.physics import Rope
from engine.timing import Cue
from films.salvage import cast
from films.salvage import sets as S
from films.salvage.scenes import _lib_s10_s13 as LIB

PAL = S.PAL
INK = PAL.ink
LIGHT = PAL.light
ss = smoothstep
mix = LIB.mix

# ----------------------------------------------------------------------------- beats
T_LOWER = 1.05                  # his eyes come down off the coils
T_PUSH0, T_PUSH1 = 1.45, 2.45   # the push in to the port
T_ONE = 3.59                    # [one]: the eyes close
T_CALM = 6.515                  # [calm]: they open
T_PULL0, T_PULL1 = 7.05, 7.95   # pull back; he turns to profile, looks down at his weights
T_BUCKLE = 7.88                 # both gloves on the front weight's hook
T_TUG_A, T_TUG_B = 8.02, 8.17   # two pulls on the hooks
T_DROP = 8.37                   # [My]...: the weights fall (they hit the silt on [taught])
T_LIFT = 8.55                   # lighter: his heels leave the silt
T_KICK = {"R": 9.06, "L": 9.29}  # the lead boots kicked off (land on [me], [that])
T_OUT = 11.5

# ----------------------------------------------------------------------------- the set
WRECK = S.Wreck()
WORLD = S.DeepWorld(wreck=WRECK, reef=False)
MURK = 0.34
LENS = 6000.0
X0 = -560.0                     # where he stands (pelvis x), by her quarter, left of the bell
SEA0 = S.seabed_y(X0)

DIVER = cast.DIVER
LOOK = cast.diver(weights=False, boots=False)   # the weights and boots are props: they come off
FWD = 1.0                                       # he faces frame right


def _rise(t):
    """How far he has risen (world px): slowly at first, then faster."""
    tau = t - T_LIFT
    if tau <= 0.0:
        return 0.0
    Tc = 1.25
    return 700.0 * (tau - Tc * (1.0 - math.exp(-tau / Tc)))


def _float_pose(A):
    def pose(t, u):
        p = dangle(A, t, 10.0)
        for s in ("L", "R"):
            leg = p.legs[s]
            tk = T_KICK[s]
            k = LIB.bump(t, tk - 0.17, tk - 0.03, tk + 0.03, tk + 0.32)      # kick down and forward
            r = LIB.bump(t, tk + 0.03, tk + 0.25, tk + 0.6, tk + 1.6)        # then draw it up, free
            leg["hip"] = lerp(leg["hip"], 30.0, k) + 14.0 * r
            leg["knee"] = lerp(leg["knee"], 3.0, k) + 22.0 * r
            leg["ankle"] = lerp(leg["ankle"], 28.0, k)
        sw = math.sin(1.1 * t)
        p.arms["R"].update(sh=16.0 + 8.0 * sw, abd=14.0, elbow=28.0)
        p.arms["L"].update(sh=-10.0 - 8.0 * sw, abd=12.0, elbow=24.0)
        return p
    return pose


@functools.lru_cache(maxsize=1)
def _diver():
    A = Actor(DIVER, LOOK, x=X0, ground=S.seabed_y, facing=16.0, t0=-4.0, seed=13)
    A.stand(until=T_LIFT, idle=0.25)
    p0 = A.root(T_LIFT - 1e-4)

    def path(t):
        return (p0[0] + 22.0 * ss(T_LIFT, 11.8, t) + 5.0 * math.sin(0.9 * (t - T_LIFT)) * ss(T_LIFT, T_LIFT + 1.0, t),
                p0[1] - _rise(t))
    A.free(12.0 - T_LIFT, path, pose=_float_pose(A), at=T_LIFT, blend=0.35)
    # he turns his helmet toward us for the close-up, back to profile to shed the lead
    A.key("yaw", [(-4.0, 16.0), (T_LOWER, 16.0), (2.1, 22.0, "inout"), (T_PULL0, 22.0), (7.75, 10.0, "inout"),
                  (12.0, 10.0)], fade=0.0)
    # head (+ = nod down): up at the coils, level, down at his chest, the weights, then up
    A.key("head", [(-4.0, -40.0), (0.5, -40.0), (1.7, -4.0, "inout"), (2.4, 2.0, "inout"), (T_PULL0, 2.0),
                   (7.65, 26.0, "inout"), (8.25, 28.0), (8.55, 32.0, "inout"), (8.95, 20.0, "inout"),
                   (9.4, 14.0, "inout"), (10.05, -40.0, "inout"), (12.0, -44.0)], fade=0.0)
    A.key("spine", [(-4.0, -5.0), (0.6, -5.0), (1.8, 2.0, "inout"), (T_PULL0, 2.0), (7.65, 9.0, "inout"),
                    (8.25, 9.0), (8.65, 2.0, "inout"), (9.5, -6.0, "inout"), (12.0, -8.0)], fade=0.0)
    return A


# ----------------------------------------------------------------------------- his hands
def _buckle_targets(t, sk0):
    """Both gloves on the front weight's hook, just proud of the breastplate (so they read in
    profile); two pulls, then they spring open as it goes."""
    lug = _weights_attached(sk0)[1][0]
    jerk = LIB.bump(t, T_TUG_A - 0.04, T_TUG_A, T_TUG_A + 0.02, T_TUG_A + 0.1) + \
        LIB.bump(t, T_TUG_B - 0.04, T_TUG_B, T_TUG_B + 0.02, T_TUG_B + 0.1)
    fall = ss(T_DROP - 0.02, T_DROP + 0.3, t)
    r = (lug[0] + 20.0 + 6.0 * jerk + 40.0 * fall, lug[1] + 10.0 + 8.0 * jerk + 40.0 * fall)
    l = (lug[0] + 6.0 + 4.0 * jerk - 50.0 * fall, lug[1] + 26.0 + 6.0 * jerk + 70.0 * fall)
    return r, l


@functools.lru_cache(maxsize=96)
def _solved(t):
    """The pose with his gloves driven to the weight hooks: the TARGET travels (on an arc up
    the front of the suit) from where the hand hangs, so the hand moves, not the angles."""
    A = _diver()
    p = A.pose(t)
    w = LIB.bump(t, 7.35, T_BUCKLE, T_DROP + 0.12, T_DROP + 0.6)
    if w > 0.0:
        sk0 = F.solve(p, DIVER)
        tr, tl = _buckle_targets(t, sk0)
        we = ease("inout", w)
        for side, tg in (("R", tr), ("L", tl)):
            w0 = sk0.j["wrist_" + side]
            tgt = (lerp(w0[0], tg[0], we), lerp(w0[1], tg[1], we) - 30.0 * math.sin(math.pi * we))
            arm = p.arms[side]
            arm["sh"] = lerp(arm["sh"], 55.0, we)
            arm["elbow"] = lerp(arm["elbow"], 115.0, we)
            arm["abd"] = lerp(arm.get("abd", 5.0), 10.0, we)
            LIB.solve_arm(p, side, tgt, DIVER)
            arm["grip"] = lerp(arm.get("grip", 0.3), 0.85, we * (1.0 - ss(T_DROP, T_DROP + 0.15, t)))
    return F.solve(p, DIVER), p


def _sk(t):
    return _solved(round(t, 5))[0]


# ----------------------------------------------------------------------------- the lead
def _weights_attached(sk):
    """[(lug, k)] for the back (k=-1) and front (k=+1) chest weights while they hang."""
    return LIB.weight_anchors(sk)


@functools.lru_cache(maxsize=1)
def _weight_release():
    sk = _diver().skeleton(T_DROP)
    return LIB.weight_anchors(sk)


def _weights(t, sk):
    """[(lug (x, y), angle, k, landed)] of both weights this frame."""
    out = []
    if t < T_DROP:
        jerk = LIB.bump(t, T_TUG_A - 0.04, T_TUG_A, T_TUG_A + 0.02, T_TUG_A + 0.1) + \
            LIB.bump(t, T_TUG_B - 0.04, T_TUG_B, T_TUG_B + 0.02, T_TUG_B + 0.1)
        for lug, k in _weights_attached(sk):
            out.append(((lug[0], lug[1] + (4.0 * jerk if k > 0 else 0.0)), 6.0 * k * jerk, k, None))
        return out
    for i, (lug, k) in enumerate(_weight_release()):
        floor = S.seabed_y(lug[0] + 80.0 * k) - 118.0 * LIB.WEIGHT_S + 3.0
        x, y, a, landed = LIB.drop(t, T_DROP + 0.02 * i, lug, v0=(250.0 * k, 90.0), floor_y=floor, vt=1400.0,
                                   tau=0.33, spin=16.0 * k, rest=5.0 * k)
        out.append(((x, y), a, k, landed))
    return out


def _weights_landed():
    return [w[3] for w in _weights(T_DROP + 2.0, None)]


@functools.lru_cache(maxsize=1)
def _boot_release():
    out = {}
    for s, tk in T_KICK.items():
        out[s] = LIB.boot_frame(_diver().skeleton(tk), s)
    return out


def _boots(t, sk):
    """{side: (origin, angle, scale, flip, landed or None, attached)}"""
    out = {}
    for s, tk in T_KICK.items():
        if t < tk:
            o, a, sc, fl = LIB.boot_frame(sk, s)
            out[s] = (o, a, sc, fl, None, True)
            continue
        o, a, sc, fl = _boot_release()[s]
        floor = S.seabed_y(o[0] + 30.0) - 4.0 * sc + 3.0
        x, y, ang, landed = LIB.drop(t, tk, o, v0=(190.0 * FWD, 240.0), floor_y=floor, vt=1250.0, tau=0.3,
                                     ang0=a, spin=(22.0 if s == "R" else -14.0), rest=(4.0 if s == "R" else -7.0))
        out[s] = ((x, y), ang, sc, fl, landed, False)
    return out


def _draw_weight(ctx, w):
    (x, y), a, k, landed = w
    S.draw_lead_weight(ctx, x, y, angle=a, s=LIB.WEIGHT_S)


def _draw_boot(ctx, b):
    o, a, sc, fl, landed, att = b
    S.draw_lead_boot(ctx, o[0], o[1], angle=a, s=sc, flip=fl)


# ----------------------------------------------------------------------------- the hose
def _inlet_path(t):
    return costume.helmet_inlet(_diver().skeleton(t))


_INLET = LIB.Sampled(_inlet_path, -3.6, 11.8, hz=60.0)
_SEA_X = np.linspace(-2000.0, 600.0, 521)
_SEA_Y = np.array([S.seabed_y(x) for x in _SEA_X])


def ss_v(a, b, x):
    u = np.clip((x - a) / (b - a), 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)


def _sea(x):
    return float(np.interp(x, _SEA_X, _SEA_Y))


def _far(t):
    """The rest of the cut hose: pinned high above the frame while the camera comes down with
    it, then laid off to the left along the silt (out of the tight frames)."""
    if t < -0.5:
        y = lerp(6250.0, 6550.0, ss(-3.5, -0.5, t))
    elif t < 0.6:
        y = lerp(6550.0, 7120.0, ss(-0.5, 0.6, t))
    else:
        y = lerp(7120.0, 7300.0, ss(0.6, 2.4, t))
    u = ss(2.4, 6.0, t)
    return lerp(X0 + 25.0, X0 - 1300.0, u), lerp(y, _sea(X0 - 1300.0) - 6.0, u)


HOSE_N = 80
HOSE_LEN = 3000.0


@functools.lru_cache(maxsize=1)
def _hose_rope():
    def init(t):
        a = np.array(_INLET(t))
        b = np.array(_far(t))
        d = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([-d[1], d[0]])
        u = np.linspace(0.0, 1.0, HOSE_N)
        base = a[None] * (1 - u[:, None]) + b[None] * u[:, None]
        env = np.sin(math.pi * np.clip(u * 1.1, 0.0, 1.0)) ** 0.5 * (1.0 - 0.86 * ss_v(0.28, 0.5, u))
        ph = 2.0 * math.pi * (3.2 * u + 0.12 * np.sin(u * 6.0)) + 0.9
        shape = np.sin(ph) * env * (0.75 + 0.45 * np.sin(u * 4.1 + 1.0) ** 2)

        def pts(A):
            return base + (A * shape)[:, None] * nrm[None]
        lo, hi = 0.0, 2000.0
        for _ in range(40):
            m = 0.5 * (lo + hi)
            P = pts(m)
            if np.linalg.norm(P[1:] - P[:-1], axis=1).sum() < HOSE_LEN * 0.985:
                lo = m
            else:
                hi = m
        return [tuple(p) for p in pts(lo)]

    def current(t, x, y):
        return (10.0 + 6.0 * math.sin(0.35 * t + 0.002 * y), 0.0)

    def collide(x, y):
        return _sea(x) - 6.0
    return Rope(HOSE_N, HOSE_LEN, _INLET, _far, t0=-3.5, t1=11.8, dt=1.0 / 90.0, gravity=(0.0, 220.0), drag=1.3,
                current=current, collide=collide, iters=12, stiffness=0.3, init=init)


def _hose_pts(t):
    return _hose_rope().points(t)


# ----------------------------------------------------------------------------- heartbeat
def _beats():
    out, b = [], 1.50
    while b < 11.6:
        out.append(round(b, 3))
        b += lerp(0.62, 1.0, ss(1.5, 6.6, b))          # ~97 bpm settling to 60
    return tuple(out)


BEATS = _beats()


def _pulse(t):
    """Lub-dub envelope (0..~1.3) at time t."""
    v = 0.0
    for b in BEATS:
        for dt, g in ((0.0, 1.0), (0.17, 0.55)):
            tau = t - b - dt
            if 0.0 <= tau < 0.7:
                v += g * (1.0 - math.exp(-tau / 0.025)) * math.exp(-tau / 0.11)
    return v


def _steps(t):
    """0..1 staircase: the push-in advances a notch on each beat in the close-up."""
    bs = [b for b in BEATS if T_PUSH1 - 0.2 <= b <= T_PULL0 - 0.2]
    if not bs:
        return 0.0
    return sum(ease("out", clamp((t - b) / 0.45)) for b in bs) / len(bs)


# ----------------------------------------------------------------------------- camera
@functools.lru_cache(maxsize=1)
def _marks():
    A = _diver()
    sk = A.skeleton(2.6)
    port = LIB.port_center(sk)[0]
    hc = costume.helmet_frame(A.skeleton(0.0))[0]
    return dict(port=port, hc=hc, root=A.root(0.0))


Z_CU0, Z_CU1 = 3.0, 4.6


CU_SCREEN = (590.0, 980.0)      # where the port sits on screen through the close-up


@functools.lru_cache(maxsize=1)
def _helm_lift():
    c, R = costume.helmet_frame(_diver().skeleton(T_LIFT))[:2]
    return c[1], R


def _fit(t):
    """(zoom, y) holding the whole man and the silt as the lead goes: his helmet top at y~260
    and the silt line easing from y 1500 (the weights land) to 1650 (the boots land)."""
    hy, R = _helm_lift()
    top = hy - _rise(t) - R
    yb = lerp(1500.0, 1650.0, ss(8.95, 9.6, t))
    z = (yb - 260.0) / (SEA0 - top)
    return z, SEA0 - (yb - H / 2) / z


def camera(t):
    m = _marks()
    hc, port = m["hc"], m["port"]
    tl = min(t, T_DROP)
    z = LIB.track([(-1.0, 1.0), (0.6, 1.22, "out"), (T_PUSH0, 1.25, "inout"), (T_PUSH1, Z_CU0, "inout"),
                   (T_PULL0, Z_CU0), (T_PULL1, 2.4, "inout"), (T_DROP, 2.36)], tl)
    if T_PUSH1 - 0.3 < tl < T_PULL1:
        # the heartbeat push: a notch in on each beat, a small thump on each lub-dub
        k = ss(T_PUSH1 - 0.3, T_PUSH1, tl) * (1.0 - ss(T_PULL0, T_PULL0 + 0.35, tl))
        z *= (Z_CU1 / Z_CU0) ** (_steps(tl) * (1.0 - ss(T_PULL0, T_PULL1, tl))) * (1.0 + 0.012 * k * _pulse(tl))
    xc0 = port[0] - (CU_SCREEN[0] - W / 2) / Z_CU0
    yc0 = port[1] - (CU_SCREEN[1] - H / 2) / Z_CU0
    x = LIB.track([(-1.0, X0 + 30.0), (0.6, X0 + 20.0, "out"), (T_PUSH0, X0 + 18.0), (T_PUSH1, xc0, "inout"),
                   (T_PULL0, xc0), (T_PULL1, X0 + 62.0, "inout"), (T_DROP, X0 + 64.0),
                   (8.95, X0 + 66.0, "inout"), (12.0, X0 + 66.0)], min(t, 9.0))
    y = LIB.track([(-1.0, hc[1] - 820.0), (0.6, hc[1] - 156.0, "out"), (T_PUSH0, hc[1] - 150.0, "inout"),
                   (T_PUSH1, yc0, "inout"), (T_PULL0, yc0), (T_PULL1, 8640.0, "inout"), (T_DROP, 8650.0)], tl)
    # through the close-up the port stays put on screen while the zoom breathes in
    w = ss(T_PUSH1 - 0.5, T_PUSH1, tl) * (1.0 - ss(T_PULL0, T_PULL0 + 0.45, tl))
    if w > 0.0:
        x = lerp(x, port[0] - (CU_SCREEN[0] - W / 2) / z, w)
        y = lerp(y, port[1] - (CU_SCREEN[1] - H / 2) / z, w)
    if t > T_DROP:
        # down with the lead to the silt, opening out as he lifts off it (helmet never cut)
        fz, fy = _fit(t)
        v = ease("inout", clamp((t - T_DROP) / 0.5))
        z = lerp(z, fz, v)
        y = lerp(y, fy, v)
    if t > 9.55:
        # rise with him: catch up, pull out, then let him drift up through the centre
        rx, ry = _diver().root(t)
        u = ease("inout", clamp((t - 9.55) / 0.95))
        drift = 150.0 * ss(10.4, 11.9, t)
        x = lerp(x, rx - 22.0, u)
        y = lerp(y, ry - 110.0 + drift, u)
        z = lerp(z, lerp(1.25, 1.12, ss(10.5, 11.8, t)), u)
    cam = Camera(x, y, z)
    amp = 0.6 + 1.2 * LIB.bump(t, T_DROP - 0.3, T_DROP, 9.4, 9.9)
    return cam.shaken(t, amp=amp, rot_amp=0.04, freq=0.45, seed=13)


def _proj(cam, x, y, z):
    k = LENS / (LENS + z)
    return cam.x + k * (x - cam.x), cam.y + k * (y - cam.y)


# ----------------------------------------------------------------------------- light
def _aim(t):
    """Where the lamp points, relative to the lamp."""
    return LIB.track([(-4.0, (260.0, -800.0)), (0.7, (260.0, -800.0)), (1.8, (800.0, 70.0), "inout"),
                      (T_PULL0, (800.0, 130.0)), (7.7, (300.0, 700.0), "inout"), (8.3, (220.0, 760.0)),
                      (8.9, (170.0, 800.0), "inout"), (9.42, (150.0, 700.0), "inout"),
                      (10.05, (90.0, -900.0), "inout"), (12.0, (60.0, -1000.0))], t)


def _beam(f, t, sk):
    lamp = costume.helmet_lamp(sk)[0]
    ax, ay = _aim(t)
    ang = math.degrees(math.atan2(ay, ax))
    down = ss(150.0, 500.0, ay)
    kw = dict(half_angle=11.0, color=LIGHT, intensity=0.6, falloff=0.8, soft=0.5, core=0.55, fog=0.4, dust=0.45,
              glare=0.0, t=t, seed=7)
    if down > 0.5:
        x0 = lamp[0] + ax * (S.seabed_y(lamp[0]) - lamp[1]) / max(ay, 1.0)
        g0, g1 = x0 - 600.0, x0 + 600.0
        stop = ((g0, S.seabed_y(g0)), (g1, S.seabed_y(g1)))
        return atmos.beam(f, lamp, ang, length=1400.0, stop=stop, pool=0.8, pool_squash=0.4, **kw)
    L = lerp(1300.0, 1700.0, ss(9.4, 10.2, t))
    return atmos.beam(f, lamp, ang, length=L, pool=0.0, **kw)


def _backdrop(f, t, cam, sk):
    hc = cam.to_screen(costume.helmet_frame(sk)[0])
    z = cam.zoom
    r = clamp(300.0 * z, 600.0, 1200.0)
    cu = ss(2.0, 2.8, z)
    up = ss(9.4, 11.0, t)
    S.deep_backdrop(f, t, glow=[(hc[0] - lerp(120.0, 170.0, cu), hc[1] - lerp(40.0, 90.0, cu), r,
                                 lerp(0.55, 0.75, cu) * (1.0 - 0.5 * up)),
                                (760.0, 160.0, 760.0, 0.22 + 0.25 * up)], murk=MURK)


def _shadow(f, t, cam):
    """The dark under her quarter at frame right: the bell (being hauled) is never seen here."""
    if cam.zoom > 2.2:
        return
    a = 0.97 * (1.0 - ss(1.6, 2.2, cam.zoom))
    bp = WRECK.bell_pose(t)["crown"]
    c = cam.to_screen(_proj(cam, bp[0] + 10.0, bp[1] + 160.0, bp[2]))
    LIB.screen_dark(f, c, 360.0 * cam.zoom, a, squash=1.3, color=mix(INK, PAL.deep, 0.5))
    br = WRECK.bracket_point()
    c2 = cam.to_screen(_proj(cam, br[0] + 120.0, br[1] - 120.0, br[2]))
    LIB.screen_dark(f, c2, 520.0 * cam.zoom, a * 0.95, squash=0.8, color=mix(INK, PAL.deep, 0.5))


def _lamp_glare(f, sk, t):
    lp = costume.helmet_lamp(sk)[0]
    with f.emit() as G:
        draw.glow_disc(G, lp, 10.0, LIGHT, 0.34)
    with f.layer() as L:
        draw.circle(L, lp, 2.0)
        L.set_source_rgb(*mix(LIGHT, (1, 1, 1), 0.6))
        L.fill()


# ----------------------------------------------------------------------------- eyes
def _eyes(t):
    look_x = LIB.track([(-4.0, 0.3), (0.7, 0.3), (1.5, 0.25, "inout"), (2.4, 0.1), (2.62, -0.45, "out"),
                        (2.95, 0.45, "inout"), (3.25, -0.2, "inout"), (3.5, 0.0), (T_CALM, -0.1),
                        (7.2, -0.1), (7.6, 0.35, "inout"), (8.5, 0.3), (9.4, 0.3), (9.75, 0.2, "inout"), (10.1, 0.1, "inout")], t)
    look_y = LIB.track([(-4.0, -0.9), (0.7, -0.9), (1.5, 0.15, "inout"), (2.4, 0.1), (2.62, 0.15, "out"),
                        (2.95, -0.05, "inout"), (3.25, 0.25, "inout"), (3.5, 0.3), (T_CALM, 0.05),
                        (7.2, 0.05), (7.6, 0.9, "inout"), (8.5, 1.0), (9.4, 0.8), (9.75, 0.0, "inout"), (10.1, -0.9, "inout")], t)
    shut = LIB.bump(t, T_ONE - 0.02, T_ONE + 0.16, T_CALM, T_CALM + 0.45)
    blink = LIB.bump(t, 0.92, 1.0, 1.04, 1.14)
    return (look_x, look_y), (1.0 - shut) * (1.0 - blink)


# ----------------------------------------------------------------------------- render
def _valve_path(t):
    return LIB.helmet_valve(_diver().skeleton(t))


_VALVE = LIB.Sampled(_valve_path, 7.5, 12.0, hz=24.0)


def render(f, t, T):
    cam = f.set_camera(camera(t))
    sk = _sk(t)
    _backdrop(f, t, cam, sk)
    view = S.View(f, murk=MURK)
    cu = ss(1.4, 2.8, cam.zoom)               # close: a shallow focus, the wreck goes soft
    # no rigging lines: a pale line beside the red hose would read as the lifting line
    WORLD.draw(f, t, view=view, wreck_kw=dict(bell=True, lines=False),
               bins=((9000.0, 7.0 + 16.0 * cu), (3200.0, 4.5 + 15.0 * cu), (900.0, 1.4 + 12.0 * cu),
                     (-1e9, 9.0 * cu)))
    _shadow(f, t, cam)
    up = ss(9.6, 11.4, t)
    if up > 0.0:
        LIB.screen_glow(f, (580.0, -260.0), 1100.0, mix(PAL.moon, PAL.surface, 0.5), 0.16 * up, blur=40)
    weights = _weights(t, sk)
    boots = _boots(t, sk)
    # the hose (behind him), the back weight
    with f.layer() as L:
        LIB.draw_hose(L, _hose_pts(t), LIB.HOSE_W)
        for w in weights:
            if w[2] < 0:
                _draw_weight(L, w)
    cone = _beam(f, t, sk)
    # the diver, his front weight, his boots
    with f.layer() as L:
        F.draw_figure(f, sk, LOOK, L, eyes=False)
        for w in weights:
            if w[2] > 0:
                _draw_weight(L, w)
        for s in ("L", "R"):
            _draw_boot(L, boots[s])
    look, open_ = _eyes(t)
    zc = cam.zoom
    with f.layer() as L:
        LIB.port_eyes(f, L, sk, look, open_=open_, glow=1.0, halo=1.0, halo_r=lerp(4.0, 2.2, ss(1.2, 3.5, zc)))
    LIB.port_glint(f, sk, 0.22 * ss(1.6, 2.8, zc))
    _lamp_glare(f, sk, t)
    # silt thrown up where the lead lands
    silt = mix(mix(PAL.mid, PAL.surface, 0.3), LIGHT, 0.35)
    for i, w in enumerate(weights):
        if w[3] is not None:
            LIB.silt_puff(f, (w[0][0], S.seabed_y(w[0][0]) - 6.0), t, w[3], size=1.0, color=silt, alpha=0.42,
                          seed=40 + i)
    for i, s in enumerate(("R", "L")):
        b = boots[s]
        if b[4] is not None:
            LIB.silt_puff(f, (b[0][0] + 30.0, S.seabed_y(b[0][0]) - 4.0), t, b[4], size=0.7, color=silt, alpha=0.36,
                          seed=50 + i, n=7)
    # the one big release of air as the lead goes
    atmos.exhale(f, _VALVE, T_DROP + 0.05, n=46, t=t, seed=31, size=(2.0, 15.0), rise=(300.0, 460.0), spread=80.0,
                 growth=0.8, wobble=1.4, current=10.0, height=2600.0, alpha=0.9, lit=cone, lit_gain=1.5)
    atmos.marine_snow(f, density=0.45, t=t, seed=13, sink=4.0, current=(8.0, 0.0), alpha=0.55, lit=cone,
                      lit_gain=2.2)
    if t > 9.3:
        vy = (camera(t + 0.02).y - camera(t - 0.02).y) / 0.04
        LIB.streaks(f, t, (0.0, vy), n=90, seed=17, alpha=0.4 * ss(150.0, 450.0, -vy), size=1.2)
    WORLD.draw_front(f, t, view)


def cues(T):
    out = [Cue(b, "heartbeat (lub-dub), no breath", gain_db=-9) for b in BEATS if b < 9.0]
    out += [
        Cue(-0.3, "slack rubber hose settling in coils around him; the air hiss gone", gain_db=-18, dur=1.8),
        Cue(T_TUG_A, "weight hook unclipped: metal click", gain_db=-14),
        Cue(T_TUG_B, "second hook: click", gain_db=-14),
        Cue(T_DROP + 0.05, "ONE BIG BUBBLE RELEASE from the helmet valve", gain_db=-7, dur=2.4),
    ]
    for lt in _weights_landed():
        out.append(Cue(lt, "WEIGHTS DROP: lead thuds into the silt, a soft puff", gain_db=-5))
    for s in ("R", "L"):
        o, a, sc, fl, landed, att = _boots(T_KICK[s] + 1.5, None)[s]
        out.append(Cue(landed, "lead boot drops into the silt", gain_db=-8, pan=0.3))   # they land frame right
    out.append(Cue(9.5, "rising: water rush building", gain_db=-12, dur=2.0))
    return out
