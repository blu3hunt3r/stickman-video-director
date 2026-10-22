"""s11 · TWO TUGS: outside, at the bell, in the dark under her quarter (10.0 s).

IN  (hard cut on action from s10): the diver walks right along the silt, the hook in his
    right glove swinging forward (toward frame right), the pale line rising from it out of
    the top of frame, the red hose from the back of his helmet.

Beats (scene-local s; L16 0.84-7.31):
  0.0-1.8          he walks right into the shadow under the wreck's quarter (heavy gait);
                   the lamp rakes the silt ahead
  1.6-2.09         he stops; the beam lifts... and on [something@2.09] ends on an EDGE: a
                   warm sliver of a big curve in the dark (the bell: never seen whole)
  2.1-2.5          he reaches up with the hook; 2.50 it bites under the lip (clink)
  2.6-3.45         both gloves make the line fast at the hook; a hard pull to cinch it
  3.6-4.6          he backs away two steps, the line running through his right glove: the
                   line now comes down from above to his hands and runs on into the dark
  4.7-5.8          hand over hand he takes up the slack
  [two@6.06], [tugs@6.45]   TWO TUGS: both gloves jerk the line; the kinks run up it
  6.6-7.3          he looks up the line; the beam swings up with his eyes
  7.3-10.6         the camera rises along the line and the hose, faster and faster: the hull
                   slides away, the hose crosses over the line, the water greys toward a
                   faint moonlit surface
OUT (scroll 'down' = ascent, window 9.375-10.625): vertical pale line at screen x 470 and
    red hose at x 610 rising toward the light, marine snow streaming down.
"""
import functools
import math

import cairo

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import RED
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
T_STOP = 1.70                   # his last step lands
T_FIND = 2.09                   # [something]: the beam ends on an edge
T_HOOK = 2.50                   # the hook bites under the lip
T_HITCH0, T_HITCH1 = 2.62, 3.45
T_BACK0, T_BACK1 = 3.62, 4.62
T_TAKE0, T_TAKE1 = 4.70, 5.80
T_TUG1, T_TUG2 = 6.06, 6.45
T_LOOK0, T_LOOK1 = 6.60, 7.30
T_RISE = 7.30
T_OUT = 10.625

# ----------------------------------------------------------------------------- the set
WRECK = S.Wreck()
WORLD = S.DeepWorld(wreck=WRECK, reef=False)
LENS = 6000.0
BELL_K = LENS / (LENS + WRECK.bell_pose(0.0)["crown"][2])
BELL_S = BELL_K * WRECK.BELL_SCALE
HOOK_S = 1.3
MURK = 0.32

# ----------------------------------------------------------------------------- the diver
DIVER = cast.DIVER
LOOK = cast.diver()
YAW = 4.0
X_WALK0 = -780.0
X_STOP = -275.0
X_BACK = -395.0


@functools.lru_cache(maxsize=1)
def _diver():
    A = Actor(DIVER, LOOK, x=X_WALK0, ground=S.seabed_y, facing=YAW, t0=-1.2, seed=11)
    A.walk(to=X_STOP, gait="heavy", speed=0.42, at=-1.2, yaw=YAW)
    A.stand(until=T_BACK0, idle=0.6)
    A.walk(to=X_BACK, gait="heavy", speed=0.5, at=T_BACK0, yaw=YAW)
    A.stand(until=12.0, idle=0.5)
    # + nods down: the silt ahead, up to the edge, his hands, the tugs, up the line
    A.key("head", [(-1.0, 12.0), (1.3, 12.0), (2.05, -6.0), (2.6, 0.0), (3.5, 2.0), (4.6, 6.0), (5.9, 4.0),
                   (6.5, 4.0), (7.25, -30.0), (12.0, -30.0)], fade=0.0)
    A.key("spine", [(-1.0, 6.0), (1.6, 6.0), (2.3, -2.0), (3.5, 0.0), (4.6, 4.0), (6.0, 6.0),
                    (6.06, 6.0), (6.12, -3.0, "out"), (6.36, 5.0), (6.45, 5.0), (6.51, -4.0, "out"), (6.8, 3.0),
                    (7.3, -4.0), (12.0, -4.0)], fade=0.0)
    return A


def _root(t):
    return _diver().root(t)


# ----------------------------------------------------------------------------- camera
def _cam_keys(t):
    x = LIB.track([(-1.0, -560.0), (0.0, -520.0), (1.8, -255.0, "inout"), (3.5, -235.0, "inout"),
                   (4.8, -300.0, "inout"), (7.3, -312.0, "inout")], t)
    y = LIB.track([(-1.0, 8440.0), (0.0, 8440.0), (1.8, 8420.0, "inout"), (3.5, 8430.0, "inout"),
                   (4.8, 8440.0, "inout"), (7.3, 8390.0, "inout")], t)
    z = LIB.track([(-1.0, 1.12), (0.0, 1.12), (1.8, 1.10, "inout"), (2.9, 1.24, "inout"), (3.6, 1.24),
                   (4.8, 1.08, "inout"), (6.2, 1.16, "inout"), (7.3, 1.14, "inout")], t)
    return x, y, z


def _rise_u(t):
    return clamp((t - T_RISE) / (T_OUT + 0.4 - T_RISE))


def camera(t):
    x, y, z = _cam_keys(min(t, T_RISE))
    if t > T_RISE:
        u = _rise_u(t)
        z = lerp(z, 0.55, ease("inout", clamp((t - T_RISE) / 2.6)))
        y = y - 5200.0 * u ** 2.2
        x = lerp(x, _line_x_top() + 70.0 / z, ease("inout", clamp((t - T_RISE) / 2.4)))
    cam = Camera(x, y, z)
    amp = 0.8 + 1.6 * LIB.bump(t, T_TUG1 - 0.02, T_TUG1 + 0.03, T_TUG2 + 0.1, T_TUG2 + 0.5)
    return cam.shaken(t, amp=amp, rot_amp=0.05, freq=0.5, seed=11)


def _proj(cam, x, y, z):
    k = LENS / (LENS + z)
    return cam.x + k * (x - cam.x), cam.y + k * (y - cam.y)


# ----------------------------------------------------------------------------- the bell (never seen)
def _bell(t):
    """(X, Y, angle, s, clapper): the bell in action-plane coords this frame."""
    cam = camera(t)
    bp = WRECK.bell_pose(t)
    X, Y = _proj(cam, *bp["crown"])
    return X, Y, bp["angle"], BELL_S, bp["clapper"]


def _bell_pt(b, u, v):
    a = math.radians(b[2])
    return (b[0] + b[3] * (u * math.cos(a) - v * math.sin(a)), b[1] + b[3] * (u * math.sin(a) + v * math.cos(a)))


def _tie(t):
    """(throat, eye, angle) of the hook once it is under the bell's lip (mirrored hook: its
    point inside the mouth, the shank outside the flare)."""
    b = _bell(t)
    th = _bell_pt(b, -63.0, 141.0)
    a = math.radians(b[2])
    d = 66.0 * HOOK_S
    eye = (th[0] + d * math.sin(a), th[1] - d * math.cos(a))
    return th, eye, b[2]


def _bell_shape(ctx, b):
    S.draw_bell(ctx, b[0], b[1], angle=b[2], clapper=b[4], s=b[3])


# ----------------------------------------------------------------------------- the gloves
def _carry(t, sh):
    """Right wrist while walking: the hook carried out in front, the arm still up from the
    swing at the cut and settling (relative to his right shoulder)."""
    e = math.exp(-max(t, 0.0) / 0.5)
    return sh[0] + 128.0 + 34.0 * e + 6.0 * math.sin(3.2 * t), sh[1] + 48.0 - 30.0 * e


def _hands_line(t, pel):
    """Where his two gloves hold the line after backing away: (lower = right, upper = left),
    with the hand-over-hand and the two tugs."""
    base_r = (pel[0] + 110.0, pel[1] - 92.0)
    base_l = (pel[0] + 116.0, pel[1] - 150.0)
    # hand over hand: R pulls down, L reaches up, L pulls, R reaches up (two cycles)
    hh = 0.0
    if T_TAKE0 < t < T_TAKE1:
        u = (t - T_TAKE0) / (T_TAKE1 - T_TAKE0)
        hh = math.sin(2.0 * math.pi * 2.0 * u) * math.sin(math.pi * u)
    r = (base_r[0] - 4.0 * hh, base_r[1] + 22.0 * hh)
    l = (base_l[0] + 4.0 * hh, base_l[1] - 22.0 * hh)
    # the tugs: a hard jerk down and back, a slower recover
    j = 0.0
    for tt in (T_TUG1, T_TUG2):
        tau = t - (tt - 0.05)
        if 0.0 < tau < 0.45:
            j += ss(0.0, 0.07, tau) * (1.0 - ss(0.10, 0.42, tau))
    r = (r[0] - 26.0 * j, r[1] + 34.0 * j)
    l = (l[0] - 26.0 * j, l[1] + 34.0 * j)
    return r, l


def _wrist_targets(t, sk0):
    """World wrist targets (R, L); None keeps the walk's own arm."""
    pel = sk0.j["pelvis"]
    gR, gL = _carry(t, sk0.j["shoulder_R"]), None
    th, eye, ang = _tie(min(max(t, T_HOOK - 0.4), T_HITCH1))
    at_eye_r = (eye[0] - 22.0, eye[1] + 12.0)
    at_eye_l = (eye[0] - 34.0, eye[1] - 6.0)
    if t > 1.45:
        w = ease("inout", clamp((t - 1.45) / (T_HOOK - 1.45)))
        gR = (lerp(gR[0], at_eye_r[0], w), lerp(gR[1], at_eye_r[1], w))
    if t > T_HOOK:
        # the hitch: small turns of both gloves around the eye, then the cinch
        u = clamp((t - T_HITCH0) / (T_HITCH1 - T_HITCH0))
        c = math.sin(2.0 * math.pi * 2.0 * u) * (1.0 - ss(0.8, 1.0, u))
        cin = LIB.bump(t, T_HITCH1 - 0.15, T_HITCH1, T_HITCH1 + 0.05, T_HITCH1 + 0.3)
        c2 = math.cos(2.0 * math.pi * 2.0 * u) * (1.0 - ss(0.8, 1.0, u))
        gR = (at_eye_r[0] + 8.0 * c - 14.0 * cin, at_eye_r[1] + 10.0 * c2 + 22.0 * cin)
    if t > T_HITCH1 + 0.15:
        r, l = _hands_line(t, pel)
        w = ease("inout", clamp((t - (T_HITCH1 + 0.15)) / (T_BACK1 - T_HITCH1 - 0.15)))
        gR = (lerp(gR[0], r[0], w), lerp(gR[1], r[1], w))
    # the left glove comes up for the hitch, drops while he backs away, takes the line
    shL = sk0.j["shoulder_L"]
    hang = (shL[0] + 26.0, shL[1] + 178.0)
    if 1.95 < t < T_BACK1:
        w = LIB.bump(t, 1.95, T_HITCH0, T_HITCH1 + 0.05, T_BACK0 + 0.3)
        c = math.sin(2.0 * math.pi * 2.0 * clamp((t - T_HITCH0) / (T_HITCH1 - T_HITCH0)) + 1.6)
        tgt = (at_eye_l[0] + 7.0 * c, at_eye_l[1] - 8.0 * c)
        gL = (lerp(hang[0], tgt[0], w), lerp(hang[1], tgt[1], w))
    if t >= T_BACK1 - 0.3:
        r, l = _hands_line(t, pel)
        w = ease("inout", clamp((t - (T_BACK1 - 0.3)) / 0.55))
        gL = (lerp(hang[0], l[0], w), lerp(hang[1], l[1], w))
    return gR, gL


@functools.lru_cache(maxsize=96)
def _solved(t):
    A = _diver()
    p = A.pose(t)
    sk0 = F.solve(p, DIVER)
    gR, gL = _wrist_targets(t, sk0)
    if gR is not None:
        p.arms["R"].update(sh=40.0, abd=10.0, elbow=60.0)
        LIB.solve_arm(p, "R", gR, DIVER)
        p.arms["R"]["grip"] = 0.85
    if gL is not None:
        p.arms["L"].update(sh=40.0, abd=8.0, elbow=60.0)
        LIB.solve_arm(p, "L", gL, DIVER)
        p.arms["L"]["grip"] = 0.8
    return F.solve(p, DIVER)


def _hand(sk, side):
    w, f_ = sk.j["wrist_" + side], sk.j["fingers_" + side]
    return w[0] + (f_[0] - w[0]) * 0.45, w[1] + (f_[1] - w[1]) * 0.45


# ----------------------------------------------------------------------------- the hook
def _swing(t):
    """The hook hanging from his glove while he walks, as a draw angle (deg, + = its bowl
    toward -x): still flying out toward frame right at the cut (s10 ends on -40, moving),
    falling back, trailing a little as he walks, settling as he stops."""
    a = LIB.track([(0.0, -36.0), (0.16, -44.0, "out"), (0.62, -6.0, "inout"), (1.05, 10.0, "inout"),
                   (1.55, 2.0, "inout"), (2.0, -4.0, "inout"), (2.4, 0.0, "inout")], t)
    return a + 4.0 * math.sin(5.6 * t + 0.4) * ss(0.4, 0.8, t) * (1.0 - ss(1.4, 1.9, t))


def _hook(t, sk):
    """(eye, angle, flip) of the hook: in his right glove (swinging), then under the lip."""
    if t < T_HOOK:
        eye = _hand(sk, "R")
        a = _swing(t)
        if t > 1.9:                       # he lifts it in front of the edge, turning it over
            w = ss(1.9, T_HOOK - 0.05, t)
            th, e2, ang = _tie(t)
            a = lerp(a, ang, w)
            return eye, a, w > 0.5
        return eye, a, False
    th, eye, ang = _tie(t)
    return eye, ang, True


# ----------------------------------------------------------------------------- the line
def _line_x_top():
    return X_BACK + 118.0


def _line_pts(t, sk, cam):
    """The pale line, top of frame (and beyond) -> his hands -> the hook's eye."""
    top_y = cam.y - (H / 2 + 260.0) / cam.zoom
    xt = _line_x_top() + 10.0 * math.sin(0.35 * t + 0.4) + 6.0 * noise1(t * 0.2, 31)
    hk = _hook(t, sk)[0]
    hits = [(T_TUG1, 1.0), (T_TUG2, 1.1)]
    if t < T_HITCH1 + 0.15:
        # one run from the top to the eye (in his glove, or under the lip)
        bot = hk
        mid = []
        n = 14
        lag = 22.0 * ss(-0.5, 0.2, t) * (1.0 - ss(1.2, 1.9, t))     # trailing as he walks
        for i in range(n + 1):
            u = i / n
            y = lerp(top_y, bot[1], u)
            x = lerp(xt, bot[0], u ** 1.6) - lag * math.sin(math.pi * u)
            mid.append((x, y))
        return mid, []
    r, l = _hand(sk, "R"), _hand(sk, "L")
    hold = ss(T_BACK1 - 0.3, T_BACK1 + 0.2, t)
    upper_from = (lerp(r[0], l[0], hold), lerp(r[1], l[1], hold))
    # upper run: from his top glove straight up, the slack taken up hand over hand
    slack = 26.0 * (1.0 - ss(T_TAKE0, T_TAKE1, t))
    up = []
    n = 26
    L = upper_from[1] - top_y
    for i in range(n + 1):
        u = i / n
        y = lerp(upper_from[1], top_y, u)
        x = lerp(upper_from[0], xt, u ** 0.7) + slack * math.sin(math.pi * min(u * 3.0, 1.0)) * (1.0 - u)
        s = u * L
        off = LIB.pulses_offset(s, t, hits, speed=1600.0, width=75.0, amp=34.0, decay=0.8)
        up.append((x + off, y))
    # lower run: from the eye under the lip to his lower glove (taut after the cinch)
    lo = [hk, (lerp(hk[0], r[0], 0.5), lerp(hk[1], r[1], 0.5) + 6.0 * (1.0 - hold)), r]
    if hold > 0.02:
        lo.append(l)
    return up, lo


# ----------------------------------------------------------------------------- the hose
def _inlet_path(t):
    return costume.helmet_inlet(_diver().skeleton(t))


_INLET = LIB.Sampled(_inlet_path, -4.0, 11.5, hz=30.0)
Y_ANCHOR = 7050.0


def _anchor(t):
    u = ss(-2.0, 6.0, t)
    return lerp(-640.0, -470.0, u) + 14.0 * math.sin(0.3 * t), Y_ANCHOR


def _current(t, x, y):
    return (22.0 + 6.0 * math.sin(0.4 * t), 0.0)


@functools.lru_cache(maxsize=1)
def _hose_rope():
    a0 = _anchor(-4.0)
    b0 = _INLET(-4.0)
    span = math.hypot(b0[0] - a0[0], b0[1] - a0[1])
    n = 34

    def init(t):
        return [(lerp(a0[0], b0[0], i / (n - 1)), lerp(a0[1], b0[1], i / (n - 1))) for i in range(n)]
    return Rope(n, span * 1.015, _anchor, _INLET, t0=-4.0, t1=11.5, dt=1.0 / 90.0, gravity=(0.0, 60.0), drag=1.8,
                current=_current, iters=14, stiffness=0.3, init=init)


def _hose_top_x():
    return _line_x_top() + 255.0


def _hose_pts(t, cam):
    """The hose: simulated near him, then on up (procedural, tangent to the simulated run)
    over the line to its right."""
    pts = _hose_rope().points(t)              # anchor -> inlet
    top_y = cam.y - (H / 2 + 260.0) / cam.zoom
    if top_y > Y_ANCHOR - 20.0:
        return pts
    p0, p1 = pts[0], pts[1]
    d = (p0[0] - p1[0], p0[1] - p1[1])
    dl = math.hypot(*d) or 1.0
    y3 = Y_ANCHOR - 1500.0
    p3 = (_hose_top_x() + 10.0 * math.sin(0.5 * t), y3)
    L = p0[1] - y3
    t0 = (d[0] / dl * L * 0.9, d[1] / dl * L * 0.9)
    t1 = (0.0, -L * 0.9)
    ext = []
    n = 18
    for i in range(1, n + 1):
        u = i / n
        h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        ext.append((h00 * p0[0] + h10 * t0[0] + h01 * p3[0] + h11 * t1[0],
                    h00 * p0[1] + h10 * t0[1] + h01 * p3[1] + h11 * t1[1]))
    if top_y < y3:
        m = 14
        for i in range(1, m + 1):
            y = lerp(y3, top_y, i / m)
            ext.append((p3[0] + 14.0 * math.sin(0.0011 * (y3 - y)) * math.sin(0.4 * t + 1.0), y))
    return list(reversed(ext)) + pts


# ----------------------------------------------------------------------------- light
def _aim(t, sk, lamp):
    """Where the lamp points: the silt ahead, up to the edge, the hitch, up the line."""
    rx, ry = _root(t)
    ahead = (rx + 420.0, S.seabed_y(rx + 420.0))
    th, eye, ang = _tie(t)
    edge = _bell_pt(_bell(t), -44.0, 104.0)
    hk = (eye[0] - 6.0, eye[1] + 30.0)
    upl = (_line_x_top() + 70.0, lamp[1] - 1400.0)
    hands = (_line_x_top() + 30.0, lamp[1] - 160.0)
    a = LIB.track([(-1.0, ahead), (1.45, ahead), (T_FIND, edge, "inout"), (2.6, hk, "inout"),
                   (T_BACK1, hk), (T_LOOK0, hk), (T_LOOK0 + 0.22, hands, "inout"), (T_LOOK1, upl, "inout")], t)
    return a


def _beam(f, t, sk):
    lamp, _, _ = costume.helmet_lamp(sk)
    tgt = _aim(t, sk, lamp)
    dx, dy = tgt[0] - lamp[0], tgt[1] - lamp[1]
    dist = math.hypot(dx, dy) or 1.0
    ang = math.degrees(math.atan2(dy, dx))
    b = _bell(t)
    occ = (lambda ctx, b=b: _bell_shape(ctx, b))
    if t < 1.75:
        g = S.seabed_y(tgt[0])
        stop = ((tgt[0] - 500.0, S.seabed_y(tgt[0] - 500.0)), (tgt[0] + 500.0, S.seabed_y(tgt[0] + 500.0)))
        return atmos.beam(f, lamp, ang, length=dist + 260.0, half_angle=12.0, color=LIGHT, intensity=0.62,
                          falloff=0.75, soft=0.5, core=0.55, fog=0.4, stop=stop, pool=0.9, pool_squash=0.42,
                          dust=0.45, glare=0.0, t=t, seed=5, occluder=occ, splash=0.25)
    fade = 1.0 - ss(0.12, 0.5, _rise_u(t))
    up = ss(T_LOOK0, T_LOOK1, t)
    return atmos.beam(f, lamp, ang, length=lerp(max(dist, 300.0) + 900.0, 1500.0, up), half_angle=12.0,
                      color=LIGHT, intensity=0.62 * lerp(1.0, 0.75, up) * fade, falloff=lerp(0.75, 1.1, up), soft=0.5,
                      core=0.55, fog=0.4, pool=0.0, dust=0.45, glare=0.0, t=t, seed=5, occluder=occ, shadow=0.985,
                      splash=0.30)


_BELL_OUT = [(-30, 30), (-22, 26), (0, 24), (22, 26), (30, 30), (36, 44), (37, 70), (40, 96), (49, 118), (61, 134),
             (66, 142), (60, 146), (0, 141), (-60, 146), (-66, 142), (-61, 134), (-49, 118), (-40, 96), (-37, 70),
             (-36, 44)]


def _bell_outline(ctx, b, off=(0.0, 0.0)):
    """The bell's body outline (no loop, no clapper) as a path."""
    pts = _bell_pt_list(b, _BELL_OUT, off)
    draw.smooth(ctx, pts, close=True, tension=0.42)


def _bell_pt_list(b, uv, off=(0.0, 0.0)):
    a = math.radians(b[2])
    ca, sa = math.cos(a), math.sin(a)
    return [(b[0] + off[0] + b[3] * (u * ca - v * sa), b[1] + off[1] + b[3] * (u * sa + v * ca)) for u, v in uv]


def _edge_rim(f, t, sk):
    """The only thing we see of it: a thin warm crescent along the curve where the beam
    grazes it (its outline nudged toward the lamp, minus its body), fading out of a small
    window around the beam's hit."""
    b = _bell(t)
    lamp = costume.helmet_lamp(sk)[0]
    hit = _bell_pt(b, -42.0, 104.0)
    on = ss(T_FIND - 0.10, T_FIND + 0.06, t) * (1.0 - ss(T_LOOK0, T_LOOK1 - 0.2, t))
    if on <= 0.01:
        return
    d = (lamp[0] - hit[0], lamp[1] - hit[1])
    L = math.hypot(*d) or 1.0
    off = (3.2 * d[0] / L, 3.2 * d[1] / L - 0.8)
    col = mix(LIGHT, (1.0, 1.0, 1.0), 0.2)
    with f.layer() as Lr:
        Lr.save()
        Lr.new_path()
        Lr.rectangle(hit[0] - 600.0, hit[1] - 600.0, 1200.0, 1200.0)
        _bell_outline(Lr, b)
        Lr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        Lr.clip()
        Lr.set_fill_rule(cairo.FILL_RULE_WINDING)
        Lr.new_path()
        _bell_outline(Lr, b, off)
        draw.radial(Lr, hit, 0.0, 78.0, [(0.0, col, 0.95 * on), (0.45, col, 0.7 * on), (1.0, col, 0.0)])
        Lr.fill()
        Lr.restore()


def _backdrop(f, t, cam):
    """The open water behind while he works: the deep haze, with a faint far glow behind
    his shoulders."""
    u = _rise_u(t)
    S.deep_backdrop(f, t, glow=[(300.0, 760.0, 900.0, 0.55 * (1.0 - u)), (760.0, 200.0, 700.0, 0.25)], murk=MURK)


def _night_water(f, t, cam):
    """On the way up the water greys toward a faint moonlit skin (a compressed column: the
    colour runs ahead of the camera); painted OVER the wreck so she sinks into the murk."""
    u = _rise_u(t)
    a = ss(0.08, 0.62, u)
    if a <= 0.0:
        return
    vy = lerp(1750.0, 760.0, ss(0.1, 0.95, u))
    with f.screen() as Sc:
        st = []
        for i in range(9):
            sy = -40 + (H + 80) * i / 8
            y = vy + (sy - H / 2) / H * 950.0
            st.append((i / 8, S.water_at(max(y, 120.0), bright=0.55), a))
        draw.linear(Sc, (0, -40), (0, H + 40), st)
        Sc.paint()
    LIB.screen_glow(f, (600.0, -320.0), 1100.0, mix(PAL.moon, PAL.mid, 0.35), 0.30 * ss(0.5, 1.0, u), blur=40)


def _shadow(f, t, cam):
    """The deep shadow under her quarter that swallows the bell, its chain and bracket."""
    b = _bell(t)
    c = cam.to_screen((b[0] + 10.0, b[1] + 40.0))
    z = cam.zoom
    fade = 1.0 - ss(0.45, 0.75, _rise_u(t))
    LIB.screen_dark(f, c, 330.0 * z, 0.97 * fade, squash=1.35, color=mix(INK, PAL.deep, 0.5))
    # the bracket arm and its brace (from s05) must not show either
    br = WRECK.bracket_point()
    c2 = cam.to_screen(_proj(cam, br[0] + 120.0, br[1] - 120.0, br[2]))
    LIB.screen_dark(f, c2, 520.0 * z, 0.95 * fade, squash=0.8, color=mix(INK, PAL.deep, 0.5))


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    cam = f.set_camera(camera(t))
    sk = _solved(round(t, 5))
    _backdrop(f, t, cam)
    view = S.View(f, murk=MURK)
    WORLD.draw(f, t, view=view, wreck_kw=dict(bell=True))
    _shadow(f, t, cam)
    _night_water(f, t, cam)
    # the hose and the line
    up, lo = _line_pts(t, sk, cam)
    held = bool(lo)
    with f.layer() as L:
        if not held:
            LIB.draw_pale(L, up, LIB.LINE_W)
        LIB.draw_hose(L, _hose_pts(t, cam), LIB.HOSE_W)
    # the beam (ends on the edge of the bell), its rim, the diver
    cone = _beam(f, t, sk)
    _edge_rim(f, t, sk)
    with f.layer() as L:
        F.draw_figure(f, sk, LOOK, L, eyes=False)
        eye, ang, flip = _hook(t, sk)
        LIB.draw_hook_rim(L, eye[0], eye[1], angle=ang, s=HOOK_S, rim=mix(LIGHT, LIB.LINE_C, 0.5), rim_a=0.35,
                          off=(-1.2, -0.8), flip=flip)
        if held:                                   # he holds it in front of him
            LIB.draw_pale(L, up, LIB.LINE_W)
            LIB.stroke(L, lo, LIB.LINE_W, LIB.LINE_C, smooth=False)
            for side in ("R", "L"):                # his fingers close over it
                F._hand(L, sk, side, LOOK, 0.9)
                L.set_source_rgb(*INK)
                L.fill()
    lx = LIB.track([(-1, 0.75), (1.4, 0.75), (2.0, 0.6), (2.6, 0.55), (4.6, 0.5), (6.5, 0.5), (7.2, 0.35)], t)
    ly = LIB.track([(-1, 0.55), (1.4, 0.6), (2.05, -0.3), (2.6, 0.0), (4.6, 0.25), (6.5, 0.2), (7.2, -0.9)], t)
    with f.layer() as L:
        LIB.port_eyes(f, L, sk, (lx, ly), open_=1.0, glow=1.0, halo=1.0, halo_r=4.0)
    # his breath: a burst from the valve every few seconds
    atmos.breathing(f, _VALVE, period=3.4, phase=0.8, n=12, t=t, seed=11, size=(1.2, 5.5), rise=(180.0, 260.0),
                    current=18.0, height=2600.0, alpha=0.7, lit=cone, lit_gain=1.2)
    atmos.marine_snow(f, density=0.45, t=t, seed=11, sink=4.0, current=(10.0, 0.0), alpha=0.55, lit=cone,
                      lit_gain=2.2)
    u = _rise_u(t)
    if u > 0.0:
        # faint moonlight hanging from a surface still far above; the snow smears as we rise
        top = cam.y - (H / 2) / cam.zoom
        atmos.underwater_rays(f, surface_y=top - 250.0, t=t, spacing=170.0, angle=93.0, fan=10.0,
                              length=1900.0 / max(cam.zoom, 0.3), width=(14.0, 60.0), intensity=0.22 * ss(0.5, 1.0, u),
                              color=mix(PAL.moon, PAL.surface, 0.4), density=0.6, seed=11, blur=14.0)
        vy = (camera(t + 0.02).y - camera(t - 0.02).y) / 0.04
        LIB.streaks(f, t, (0.0, vy), n=110, seed=13, alpha=0.45 * ss(0.05, 0.3, u), size=1.3)
    WORLD.draw_front(f, t, view)


def _valve_path(t):
    return LIB.helmet_valve(_diver().skeleton(t))


_VALVE = LIB.Sampled(_valve_path, -10.0, 11.0, hz=24.0)


def cues(T):
    return [
        Cue(0.05, "heavy boots in silt, the hook's chain-rattle swing", gain_db=-14, dur=1.8),
        Cue(T.at("something"), "low groan of metal in the dark (the edge in the beam)", gain_db=-14, dur=1.4),
        Cue(T_HOOK, "iron hook bites under a bronze lip: dull clink", gain_db=-9),
        Cue(T_HITCH1, "rope cinched hard", gain_db=-14),
        Cue(T_BACK0, "two heavy steps back, the line hissing through a glove", gain_db=-16, dur=1.0),
        Cue(T.at("two"), "TUG one: the line snaps taut, a low twang running up", gain_db=-6),
        Cue(T.at("tugs"), "TUG two", gain_db=-6),
        Cue(T_RISE, "rising whoosh up the line toward the surface", gain_db=-10, dur=3.3),
    ]
