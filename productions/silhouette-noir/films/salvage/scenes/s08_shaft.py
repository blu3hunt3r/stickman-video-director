"""s08 · THE SHAFT: down the capsized passage into the captain's cabin; the safe (10.0 s).

IN  (bars from s07, 1.0 s): seven ink columns rise and travel on, uncovering the shaft from
    the bottom up (scene t 0.0-0.5). Dark: his lamp's cone reaching down the shaft onto the
    bulkhead past a fallen chair, his silhouette against the lamp's own spill, the door on
    its side above him.
Beats (scene-local s):
  0.0-4.7     he goes down the pipe on the left wall hand under hand (a new grip every
              0.5 s, rust and silt shaken off it); the beam sweeps the shaft: the chair
              turning in his wake (its shadow on the bulkhead), the ports, the cables up the
              right wall, then down into the dark; the door on its side swings in his wake;
              the red hose snakes up behind him; silt snows down
  4.7         the pipe ends: he hangs at arm's length over the dark
  [captain's@4.88]  he lets go and drops into the captain's cabin (lying on its side),
              turning toward the camera as he sinks; the beam sweeps the desk bolted to her
              old floor (now the right wall) ...
  [safe@5.70]  ... and lands on the SAFE: its face comes up warm, the dial readable
  6.4         he lands in a crouch, silt billows; the beam jolts and settles on the dial
  6.4-8.5     he straightens, leans in; the lamp holds the dial (L13 runs to 9.47)
  8.5-9.25    the camera pushes in on the dial
  9.05-9.40   the cabin dissolves into the close-up of the dial (rot -90: the safe lies on
              its side); the camera rolls upright as it keeps pushing in (9.15-10.0)
OUT (match cut into s09): at 10.0 exactly DialCloseup.camera(r_screen=260, rot=0) with
    dc.draw(dial_angle=dial_angle_for(0), lamp=(-0.62, -0.78), power=1.0, door=0.0) and
    light marine snow: the dial centred at (540, 960), r 260, lit from the upper left.
"""
import math

import cairo

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor
from engine.timing import Cue
from films.salvage import cast
from films.salvage import sets as S
from films.salvage.scenes import _lib_s05_s06_s08 as LIB

PAL = S.PAL
INK = PAL.ink
ss = smoothstep
D2R = math.pi / 180.0

INN = S.Interior()
DC = S.DialCloseup()
LENS = 6000.0                                   # InteriorView's default lens


def _beats(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:
            return d
    return dict(captain=at("captain's", 4.879), safe=at("safe.", 5.703), combination=at("combination", 7.398),
                down=at("down", 8.501), him=at("him.", 9.012))


# ============================================================================= times
T_M0 = -1.9            # the first hand move (before the scene: he is already on his way)
DT_M = 0.45            # between grips (hands alternate)
D_MOVE = 0.30          # one hand's move
T_SLOW = 3.95          # he slows ...
T_HANG = 4.62          # ... and hangs at arm's length over the dark mouth
T_REL = 4.76           # he lets go
T_CUT = 4.879          # [captain's]: hard cut on action into the cabin as he drops in
T_DROP = T_CUT
T_SAFE = 5.703         # [safe]: the beam on the safe
T_PUSH = 8.5
T_X0, T_X1 = 9.05, 9.40          # the dissolve into the close-up
T_ROLL0 = 9.12                    # the camera rolls the safe upright (-90 -> 0)
T_PURE = 9.85                     # from here on only the close-up (exact end state)
T_END = 10.0

# ============================================================================= geometry
X_PIPE, Z_PIPE = -S.SHAFT_HW + 58.0, -140.0     # the pipe on the left wall (the hand holds)
K_PIPE = LENS / (LENS + Z_PIPE)
Y_PIPE_END = S.SHAFT_BOT - 90.0
DIAL_W, _ = INN.safe_dial(None), None            # world (x, y, z) of the safe's dial
R_AP = 34.0 * INN.SAFE_S * LENS / (LENS + DIAL_W[2])    # the cabin dial's radius (action plane)
M_DIAL = 1.15          # cabin dial disc radius = M_DIAL x the close-up's ring radius (silhouettes match)

# ============================================================================= the diver
X_HANG = -150.0
SH = 170.0             # pelvis -> shoulder
G_HIGH = 188.0         # a grip released this far above the shoulder (arm long)
G_LOW = -22.0          # a new grip this far below the shoulder (< 0: above it; he hangs from his hands)
V_DESC = 300.0
Y_GRIP_END = 2836.0                         # his last grips (the dark mouth is below his boots)
YP_HANG = Y_GRIP_END + G_HIGH + SH
Y_STAND = S.CABIN_BOT - (cast.DIVER.hip - 0.006) * 620.0
VT, TAU0 = 1300.0, 0.34                    # the drop: terminal speed, time constant
YAW_HANG, YAW_CABIN = 172.0, 28.0


def _drop_d(tau):
    return VT * (tau - TAU0 * (1.0 - math.exp(-tau / TAU0)))


def _solve_land():
    lo, hi = 0.0, 4.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if YP_HANG + _drop_d(mid) < Y_STAND:
            lo = mid
        else:
            hi = mid
    return T_REL + hi


T_LAND = _solve_land()
X_LAND = -215.0                  # left of the safe: clear of it when the close-up plate takes over


def _yp_desc(t):
    """Pelvis height going down the pipe: steady, slowing to a hang at the pipe's end; a
    little drop after each new grip."""
    D = T_HANG - T_SLOW
    if t <= T_SLOW:
        y = YP_HANG - V_DESC * D / 2.0 - V_DESC * (T_SLOW - t)
    elif t <= T_HANG:
        u = (t - T_SLOW) / D
        y = YP_HANG - V_DESC * D / 2.0 * (1.0 - u) ** 2
    else:
        y = YP_HANG + 7.0 * math.sin(4.0 * (t - T_HANG)) * math.exp(-3.0 * (t - T_HANG))
    y += 10.0 * math.sin(2.0 * math.pi * (t - T_M0 - D_MOVE) / DT_M) * (1.0 - ss(T_SLOW - 0.3, T_HANG, t))
    return y


def _path(t):
    if t <= T_REL:
        x = X_HANG + 6.0 * noise1(t * 0.4, 3)
        return x, _yp_desc(t)
    tau = t - T_REL
    x0 = X_HANG + 6.0 * noise1(T_REL * 0.4, 3)
    return lerp(x0, X_LAND, ease("inout", clamp(tau / (T_LAND - T_REL)))), min(YP_HANG + _drop_d(tau), Y_STAND)


def _yaw(t):
    return lerp(YAW_HANG, YAW_CABIN, ease("inout", clamp((t - (T_CUT - 0.02)) / 0.7)))


def _pose(t, u):
    p = F.Pose(0.0, 0.0, _yaw(t))
    if t <= T_REL:
        # hanging: the legs climb down an imaginary ladder in the rhythm of the hands
        ph = 2.0 * math.pi * (t - T_M0) / (2.0 * DT_M)
        calm = ss(T_SLOW, T_HANG + 0.1, t)
        for s, o in (("L", 0.0), ("R", math.pi)):
            lift = (0.5 + 0.5 * math.sin(ph + o)) * (1.0 - 0.7 * calm)
            p.legs[s] = dict(hip=12.0 + 26.0 * lift + 4.0 * math.sin(t * 1.1 + o), abd=5.0,
                             knee=16.0 + 40.0 * lift + 5.0 * math.sin(t * 1.3 + o), ankle=-14.0, toe=0.0)
        p.pitch = 7.0 + 2.0 * math.sin(2.0 * math.pi * (t - T_M0) / DT_M)
        p.spine = [2.0, 2.0, 1.0]
    else:
        # the drop: arms float up off the pipe, knees come up to meet the floor
        k = ss(T_REL, T_REL + 0.4, t)
        brace = ss(T_LAND - 0.55, T_LAND - 0.05, t)
        for s, o in (("L", 0.0), ("R", 1.3)):
            p.legs[s] = dict(hip=lerp(14.0, 34.0, brace) + 4.0 * math.sin(t * 2.0 + o), abd=5.0,
                             knee=lerp(18.0, 50.0, brace) + 6.0 * math.sin(t * 2.3 + o), ankle=-6.0, toe=0.0)
        for s, sg in (("L", 1.0), ("R", -1.0)):
            p.arms[s] = dict(sh=lerp(150.0, 46.0, ss(T_REL + 0.3, T_LAND, t)) + 10.0 * sg, abd=lerp(20.0, 30.0, k),
                             elbow=lerp(20.0, 40.0, k), wrist=8.0, grip=0.3)
        p.pitch = lerp(7.0, 10.0, brace)
        p.spine = [2.0, 1.0, 0.0]
    p.head = 10.0
    p.eyes = dict(open=1.0, glow=1.0, look=0.2)
    return p


# ---------------------------------------------------------------- the grips
def _ys(t):
    return _path(t)[1] - SH


def _schedule():
    """[(t0, t1, side, y_from, y_to)] per hand: the hand moves from one grip on the pipe
    (world y) to the next, below the other hand."""
    moves = {"R": [], "L": []}
    cur = {}
    k = 0
    while True:
        side = "R" if k % 2 == 0 else "L"
        t0 = T_M0 + k * DT_M
        t1 = t0 + D_MOVE
        if t1 > T_HANG - 0.02:
            break
        y_from = cur.get(side, _ys(t0) - G_HIGH)
        y_to = min(_ys(t1) + G_LOW, Y_GRIP_END - (0.0 if side == "R" else 46.0))
        if y_to <= y_from + 20.0:
            k += 1
            continue
        moves[side].append((t0, t1, y_from, y_to))
        cur[side] = y_to
        k += 1
    first = {s: (moves[s][0][2] if moves[s] else Y_GRIP_END) for s in "RL"}
    return moves, first


MOVES, FIRST = _schedule()


def _grip(side, t):
    """(world y on the pipe, off 0..1 = how far the hand is off the pipe, moving 0..1)."""
    y = FIRST[side]
    for t0, t1, ya, yb in MOVES[side]:
        if t < t0:
            return y, 0.0, 0.0
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return lerp(ya, yb, ease("inout", u)), math.sin(math.pi * u), 1.0
        y = yb
    return y, 0.0, 0.0


def _proj(x, y, z, cam_xy):
    k = LENS / (LENS + z)
    return cam_xy[0] + k * (x - cam_xy[0]), cam_xy[1] + k * (y - cam_xy[1])


def _hand_target(side):
    def fn(t):
        y, off, mv = _grip(side, t)
        c = _cam_center(t)
        X, Y = _proj(X_PIPE, y, Z_PIPE, c)
        # the wrist sits below and to the right of the gripping fist; off the pipe the hand
        # swings out toward the camera side and a little right
        return (X + 20.0 + 60.0 * off, Y + 24.0 + 10.0 * off)
    return fn


LOOK = cast.diver()


def _make_diver():
    A = Actor(cast.DIVER, LOOK, x=X_HANG, ground=S.CABIN_BOT, facing=YAW_HANG, seed=8, name="diver")
    A.face(YAW_CABIN)
    A.free(T_LAND - (-3.0), _path, _pose, at=-3.0)
    A.stand(until=16.0, idle=0.6)
    for side in ("R", "L"):
        A.reach(side, -3.0, T_REL - 0.02, _hand_target(side), fade=0.1, elbow_out=False)
        # the fist closes on the pipe, opens to move
        A.channel("arm.%s.grip" % side, (lambda t, s=side: 1.0 - 0.75 * _grip(s, t)[2]), -3.0, T_REL - 0.02, fade=0.08)
    # the landing: knees absorb deep, the body folds forward, recovers; a lean toward the safe
    A.key("y", [(T_LAND - 0.02, 0.0), (T_LAND + 0.24, 92.0, "out"), (T_LAND + 0.75, 30.0, "inout"),
                (T_LAND + 1.5, 0.0, "inout")], mode="add")
    A.key("pitch", [(T_LAND - 0.02, 0.0), (T_LAND + 0.26, 22.0, "out"), (T_LAND + 1.4, 6.0, "inout"),
                    (8.6, 7.0, "inout"), (9.6, 8.0)], mode="add")
    A.key("arm.L.sh", [(T_LAND - 0.05, 0.0), (T_LAND + 0.25, 30.0, "out"), (T_LAND + 1.2, 0.0, "inout")], mode="add")
    A.key("arm.R.sh", [(T_LAND - 0.05, 0.0), (T_LAND + 0.25, 22.0, "out"), (T_LAND + 1.2, 0.0, "inout")], mode="add")
    return A


# ============================================================================= camera
def _cam_follow(t):
    """The shaft: the camera hangs at his chest, a beat behind him, and leans a little the
    way his lamp looks (up to the door, down into the mouth)."""
    y = sum(_path(t - 0.06 * i)[1] for i in range(6)) / 6.0
    lx, ly = _lamp_est(t)
    ax, ay = _aim_shaft(t - 0.12)
    return (-50.0 + 0.10 * (ax - lx), y - 70.0 + 0.24 * (ay - ly), math.log(0.86))


CABIN0 = (35.0, 4400.0, math.log(0.80))      # just after the cut: the mouth at the top of frame
CABIN = (50.0, 4510.0, math.log(0.81))
NEAR_SAFE = (75.0, 4700.0, math.log(0.94))


def _cam_base(t):
    """(x, y, ln zoom) before the push-in: following him down the shaft; after the cut the
    cabin, settling with his fall, then easing toward the safe."""
    if t < T_CUT:
        return _cam_follow(t)
    u = ease("inout", clamp((t - T_CUT) / 1.7))
    c = tuple(lerp(p, q, u) for p, q in zip(CABIN0, CABIN))
    if t < 6.7:
        return c
    v = ease("inout", clamp((t - 6.7) / 1.8))
    return tuple(lerp(p, q, v) for p, q in zip(CABIN, NEAR_SAFE))


L_PUSH0 = math.log(math.exp(NEAR_SAFE[2]) * R_AP / M_DIAL)     # the close-up radius equivalent at 8.5
L_PUSH1 = math.log(260.0)
V_PUSH0, V_PUSH1 = 0.10, 0.30                                    # d ln(r)/dt at 8.5 and 10.0


def _push_ln_r(t):
    """ln of the close-up ring radius equivalent during the push (cubic Hermite in log)."""
    D = T_END - T_PUSH
    u = clamp((t - T_PUSH) / D)
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1
    h10 = u ** 3 - 2 * u ** 2 + u
    h01 = -2 * u ** 3 + 3 * u ** 2
    h11 = u ** 3 - u ** 2
    return h00 * L_PUSH0 + h10 * D * V_PUSH0 + h01 * L_PUSH1 + h11 * D * V_PUSH1


def _r_eq(t):
    return math.exp(_push_ln_r(t))


def _roll(t):
    """Close-up roll (deg): -90 (the safe on its side) -> 0, zero speed at both ends."""
    u = clamp((t - T_ROLL0) / (T_END - T_ROLL0))
    return -90.0 + 90.0 * (u * u * u * (u * (6 * u - 15) + 10))


def _cam_center(t):
    """World (x, y) of the camera centre (no shake): also the vanishing point."""
    if t < T_PUSH:
        c = _cam_base(t)
        return c[0], c[1]
    u = ease("inout", clamp((t - T_PUSH) / 0.62))
    a = _cam_base(T_PUSH)
    return lerp(a[0], DIAL_W[0], u), lerp(a[1], DIAL_W[1], u)


def _cabin_cam(t):
    if t < T_PUSH:
        x, y, lz = _cam_base(t)
        cam = Camera(x, y, math.exp(lz))
        land = math.exp(-((t - T_LAND - 0.12) / 0.16) ** 2)
        if t < 8.2:
            cam = cam.shaken(t, amp=2.2 + 7.0 * land, rot_amp=0.10 + 0.25 * land, freq=0.9 + 2.0 * land, seed=11)
        return cam
    x, y = _cam_center(t)
    z = _r_eq(t) * M_DIAL / R_AP
    rot = _roll(t) + 90.0
    return Camera(x, y, z, rot=rot)


# ============================================================================= the lamp
AIM_KEYS = [(-1.0, 80.0), (0.55, 72.0), (1.25, -58.0, "inout"), (1.85, -64.0, "inout"),  # the chair; up: the door creaks
            (2.45, 6.0, "inout"), (2.85, 0.0, "inout"),                                     # the ports
            (3.3, -36.0, "inout"), (3.65, -40.0, "inout"),                                  # the cables, the hose
            (4.15, 70.0, "inout"), (4.5, 92.0, "inout"), (4.9, 96.0, "inout")]              # down: the black mouth
DESK = (300.0, 3960.0)


def _lamp_est(t):
    """Where his helmet lamp is, from the root path alone (for aiming; no skeleton)."""
    x, y = _path(t)
    side = math.cos(_yaw(t) * D2R)
    return x + 24.0 * side, y - 282.0


def _aim_shaft(t):
    lamp = _lamp_est(t)
    a = LIB.track(AIM_KEYS, t) + 6.0 * noise1(t * 0.8, 21)
    d = 980.0
    return (lamp[0] + math.cos(a * D2R) * d, lamp[1] + math.sin(a * D2R) * d)


def _aim(t):
    """World (x, y) the lamp points at."""
    if t < T_CUT:
        return _aim_shaft(t)
    dial = (DIAL_W[0], DIAL_W[1])
    pts = [(T_CUT, (-60.0, 4900.0)), (5.16, DESK), (5.42, (240.0, 4470.0)), (T_SAFE, dial)]
    if t < T_SAFE:
        for i in range(1, len(pts)):
            if t <= pts[i][0]:
                u = ease("inout", (t - pts[i - 1][0]) / (pts[i][0] - pts[i - 1][0]))
                return (lerp(pts[i - 1][1][0], pts[i][1][0], u), lerp(pts[i - 1][1][1], pts[i][1][1], u))
    jolt = math.exp(-((t - T_LAND - 0.1) / 0.22) ** 2)
    return (dial[0] + 10.0 * noise1(t * 0.9, 5) - 40.0 * jolt, dial[1] + 8.0 * noise1(t * 0.8, 6) + 120.0 * jolt)


DIVER = _make_diver()


DIVER.look_at(-3.0, 16.0, _aim, fade=0.05)
_LAMP = LIB.Sampled(lambda t: costume.helmet_lamp(DIVER.skeleton(t))[0], -1.0, 10.5, 60)
_INLET = LIB.Sampled(lambda t: costume.helmet_inlet(DIVER.skeleton(t)), -3.0, 10.5, 120)
_VALVE = LIB.Sampled(lambda t: LIB.helmet_valve(DIVER.skeleton(t)), -1.0, 10.5, 60)
_CHEST = LIB.Sampled(lambda t: DIVER.skeleton(t).j["chest"], -1.0, 10.5, 60)
LIB.ACTORS["s08"] = (DIVER, lambda x: S.CABIN_BOT)


def _power(t):
    return 1.0 - 0.12 * math.exp(-((t - T_LAND - 0.03) / 0.07) ** 2) + 0.025 * noise1(t * 7.0, 98)


# ============================================================================= the set's moving parts
def _door_wake(t):
    """The door on its side swings toward the camera as he passes below it."""
    return 0.85 * ss(-1.6, 0.2, t) * (1.0 - ss(0.8, 4.2, t))


def _chair_wake(t):
    return ss(0.1, 2.6, t)


def _chair(t):
    x, y, z, a = INN.chair_pose(t)
    w = _chair_wake(t)
    return x + 34.0 * w, y + 50.0 * w, z, a + 52.0 * w


CHAIR_PTS = [(-110, -14), (110, -14), (110, 14), (108, -230), (80, -230), (-96, 190), (-80, 190), (84, 190),
             (100, 190), (-110, 14)]


def _chair_outline(view, t):
    x, y, z, a = _chair(t)
    k = view.k(z)
    ca, sa = math.cos(a * D2R), math.sin(a * D2R)
    pts = []
    for px, py in CHAIR_PTS:
        wx, wy = x + px * ca - py * sa, y + px * sa + py * ca
        pts.append((view.vx + k * (wx - view.vx), view.vy + k * (wy - view.vy)))
    return S.convex_hull(pts)


def _draw_chair(f, view, t):
    """The fallen chair turning in his wake (sets_interior's chair, posed here)."""
    x, y, z, ang = _chair(t)
    with f.layer() as c:
        with S.at_depth(c, view, z):
            c.save()
            c.translate(x, y)
            c.rotate(math.radians(ang))
            S.round_rect(c, -110, -14, 110, 14, 5)
            S.round_rect(c, 80, -230, 108, -10, 5)
            for yy in (-200, -150, -100):
                S.round_rect(c, 70, yy, 112, yy + 18, 3)
            for xx in (-96, 84):
                S.round_rect(c, xx, 10, xx + 16, 190, 4)
            S.round_rect(c, -90, 120, 90, 134, 3)
            c.restore()
            c.set_source_rgb(*INK)
            c.fill()


# ============================================================================= the hose
ENTRY = INN.entry()


def _hose_top(t):
    return (ENTRY[0], ENTRY[1])


def _hose_len(t):
    a = _hose_top(t)
    b = _INLET(t)
    return math.hypot(b[0] - a[0], b[1] - a[1]) + 160.0


def _hose_current(t, x, y):
    # it snakes: the water pushes it toward a slowly travelling S down the shaft (keeps it off
    # the walls), stronger above; in the cabin it hangs toward him
    xc = -40.0 + 90.0 * math.sin(y / 560.0 + 0.55 * t) * (1.0 - ss(3300.0, 3800.0, y))
    if y > 3500.0:
        xc = lerp(xc, -120.0, ss(3500.0, 4200.0, y))
    return (1.1 * (xc - x) + 14.0 * math.sin(0.4 * t + y / 700.0), 0.0)


def _hose_init(t):
    a, b = _hose_top(t), _INLET(t)
    n = 64
    out = []
    for i in range(n):
        u = i / (n - 1)
        out.append((lerp(a[0], b[0], u) + 60.0 * math.sin(math.pi * u) * math.sin(5.0 * u), lerp(a[1], b[1], u)))
    return out


HOSE = LIB.hose_rope(_hose_top, _INLET, _hose_len(-3.0), n=64, t0=-3.0, t1=10.2, length_fn=_hose_len,
                     current=_hose_current, gravity=(0.0, 50.0), drag=1.8, iters=12, init=_hose_init,
                     collide=lambda x, y: S.CABIN_BOT - 6.0)


# ============================================================================= silt
def _puffs():
    out = []
    i = 0
    for side in ("R", "L"):
        for t0, t1, ya, yb in MOVES[side]:
            if t1 < -1.0 or t1 > T_REL:
                continue
            c = _cam_center(t1)
            X, Y = _proj(X_PIPE, yb, Z_PIPE, c)
            out.append((X + 10.0, Y + 20.0, t1, 0.55, 300 + i))
            i += 1
    out.append((X_LAND - 40.0, S.CABIN_BOT, T_LAND + 0.02, 2.4, 11))
    out.append((X_LAND + 50.0, S.CABIN_BOT, T_LAND + 0.05, 2.0, 12))
    return out


_PUFFS = None


def _light_at_fn(t, lamp, hit):
    def fn(x, y):
        k = 0.45 * math.exp(-((x - lamp[0]) ** 2 + (y - lamp[1]) ** 2) / (520.0 ** 2))
        if hit is not None:
            k += 0.8 * math.exp(-((x - hit[0]) ** 2 + (y - hit[1]) ** 2) / (480.0 ** 2))
        return min(k, 1.0)
    return fn


# ============================================================================= render
def _cabin_pass(f, t, cam, beam_alpha=1.0):
    """Shaft / cabin: the set, the lamp, the diver, the water. Returns the beam's cone."""
    global _PUFFS
    f.fill(S.INT_BG)
    f.set_camera(cam)
    view = S.InteriorView(f)
    shaft = t < T_CUT
    INN.draw(f, t, view, cold=1.0)
    # the cold light of the hole far above, falling down the shaft
    LIB.screen_band(f, 0.0, 900.0, S.COLD, 0.075 if shaft else 0.03, 0.0)
    lamp = _LAMP(t)
    aim = _aim(t)
    reach = math.hypot(aim[0] - lamp[0], aim[1] - lamp[1])
    pw = _power(t)
    d = LIB.unit(aim[0] - lamp[0], aim[1] - lamp[1])
    shadows = [] if shaft else None
    # the pool weakens with distance; aimed down into the black mouth it lands far below, dim
    pool_pw = pw * clamp(820.0 / max(reach, 1.0)) ** 0.7
    if shaft:
        pool_pw *= 1.0 - 0.7 * ss(S.SHAFT_BOT - 300.0, S.SHAFT_BOT + 200.0, aim[1])
    hit = INN.draw_lit(f, t, view, lamp, d, spread=14.0 if shaft else 13.0, reach=reach, power=pool_pw,
                       shadows=shadows, throw=0.35)
    safe_lit = 0.88 * ss(T_SAFE - 0.12, T_SAFE + 0.25, t)
    INN.draw_mid(f, t, view, door=INN.door_angle(t, wake=_door_wake(t)), chair=False, safe_lit=safe_lit,
                 dial_angle=0.0)
    if shaft:
        # the mouth below him is a black drop: the cabin is only found after the cut
        f.darken(0.93, y0=S.SHAFT_BOT - 60.0, feather=240.0)
    # the lamp's warm spill in the water around him (his silhouette reads against it)
    with f.light(blur=40) as A:
        draw.glow_disc(A, (lamp[0] + 30.0 * d[0], lamp[1] + 30.0 * d[1]), 420.0, PAL.light, 0.07 * pw)
        draw.glow_disc(A, (lamp[0] + 10.0 * d[0], lamp[1] + 10.0 * d[1]), 160.0, PAL.light, 0.09 * pw)
    # a cold glow from above behind his helmet and shoulders
    ch = cam.to_screen(_CHEST(t))
    LIB.screen_glow(f, (ch[0], ch[1] - 170.0 * cam.zoom), 380.0 * cam.zoom, S.COLD, 0.06 if shaft else 0.03)
    with f.layer() as L:
        LIB.draw_hose(L, HOSE.points(t), LIB.HOSE_W)
        sk = DIVER.draw(f, t, L)
    if shaft:
        # the cold light from the hole far above catches his helmet, shoulders and raised arms
        LIB.rim_light(f, lambda c: F.draw_figure(None, sk, LOOK, c, color=(1, 1, 1), eyes=False), (0.25, -0.97),
                      4.5, S.COLD, 0.75, blur=2.5)
    tgt = hit if hit is not None else aim
    into_dark = ss(S.SHAFT_BOT - 350.0, S.SHAFT_BOT + 150.0, tgt[1]) if shaft else 0.0
    if into_dark > 0.5:
        # down into the black mouth: no surface to stop it, the beam just thins into the dark
        cone = LIB.lamp_beam(f, t, lamp, tgt, stop=None, half=11.0, intensity=0.55 * pw * beam_alpha, reach=1300.0,
                             dust=0.5, seed=8, fog=0.5, core=0.4, falloff=1.2)
    else:
        cone = LIB.lamp_beam(f, t, lamp, tgt, stop="perp", half=11.0, intensity=0.55 * pw * beam_alpha, pool=0.0,
                             dust=0.5, seed=8, fog=0.5, core=0.4)
    if shaft:
        _draw_chair(f, view, t)
    if _PUFFS is None:
        _PUFFS = _puffs()
    LIB.silt_puffs(f, t, _PUFFS, _light_at_fn(t, lamp, hit))
    atmos.lamp(f, lamp, radius=8.0, intensity=0.95 * pw, halo=4.5, core=0.3, t=t, seed=6)
    atmos.breathing(f, _VALVE, period=4.0, phase=-0.6, n=14, t=t, seed=41, size=(1.6, 9.0), rise=(280.0, 440.0),
                    spread=40.0, current=10.0, height=2400.0, alpha=0.6, lit=cone)
    atmos.bubbles(f, _VALVE, rate=2.0, t=t, seed=43, rise=(260.0, 400.0), size=(1.4, 4.5), spread=8.0,
                  current=10.0, height=1800.0, alpha=0.5, lit=cone)
    atmos.marine_snow(f, density=1.0, t=t, seed=18, sink=22.0, current=(4.0, 0.0), alpha=0.75, lit=cone)
    INN.draw_front(f, t, view)
    return cone


def _closeup_light(t):
    """The lamp's direction for DialCloseup (plate coords): the light stays put on the screen
    (upper left, like his helmet lamp riding with the camera) while the plate rolls under it."""
    a0 = math.atan2(-0.66, -0.75)                      # the cabin's light on the dial (screen)
    a1 = math.atan2(-0.78, -0.62)                      # the contract (screen, rot 0)
    a = lerp(a0, a1, ease("inout", clamp((t - T_X0) / (T_END - T_X0))))
    s = (math.cos(a), math.sin(a))
    r = -_roll(t) * D2R                                # screen -> plate: rotate by -rot
    p = (s[0] * math.cos(r) - s[1] * math.sin(r), s[0] * math.sin(r) + s[1] * math.cos(r))
    if t >= T_END - 1e-6:
        return (-0.62, -0.78)
    return p


def _closeup(f, t, alpha, feather):
    """DialCloseup at this frame's radius and roll; alpha (the dissolve) and a feathered
    plate edge (sides and bottom: the cabin's safe shows round it) while both are drawn."""
    R = 260.0 if t >= T_END else _r_eq(t)
    rot = 0.0 if t >= T_END else _roll(t)
    cam = DC.camera(r_screen=R, rot=rot)
    f.set_camera(cam)
    kw = dict(dial_angle=S.dial_angle_for(0), lamp=_closeup_light(t), power=1.0, door=0.0)
    if alpha >= 1.0 and feather <= 0.0:
        DC.draw(f, t, **kw)
        return cam
    c = f.ctx
    c.push_group()
    DC.draw(f, t, **kw)
    if feather > 0.0:
        c.save()
        c.set_matrix(cam.matrix(f.scale))
        c.set_operator(cairo.OPERATOR_DEST_IN)
        x0, y0, x1, y1 = DC.PLATE
        for ax, ay, bx, by in ((x0, 0.0, x0 + feather, 0.0), (x1, 0.0, x1 - feather, 0.0),
                               (0.0, y1, 0.0, y1 - feather)):
            g = cairo.LinearGradient(ax, ay, bx, by)
            g.add_color_stop_rgba(0.0, 0, 0, 0, 0.0)
            g.add_color_stop_rgba(1.0, 0, 0, 0, 1.0)
            c.set_source(g)
            c.paint()
        c.restore()
    c.pop_group_to_source()
    c.paint_with_alpha(alpha)
    return cam


def render(f, t, T):
    if t >= T_PURE:
        _closeup(f, t, 1.0, 0.0)
        atmos.marine_snow(f, density=0.45, t=t, seed=19, sink=9.0, current=(6.0, 0.0), alpha=0.6, size=1.4)
        return
    cam = _cabin_cam(t)
    cone = _cabin_pass(f, t, cam, beam_alpha=1.0)
    if t >= T_X0:
        a = ease("inout", clamp((t - T_X0) / (T_X1 - T_X0)))
        fw = 150.0 * (1.0 - ss(9.55, T_PURE, t))
        _closeup(f, t, a, fw)
        # the beam's haze and the snow ride on over it, fading as the dial fills the frame
        f.set_camera(cam)
        k = 1.0 - ss(9.3, T_PURE - 0.02, t)
        lamp = _LAMP(t)
        aim = _aim(t)
        LIB.lamp_beam(f, t, lamp, aim, stop="perp", half=11.0, intensity=0.4 * k * a, pool=0.0, dust=0.3, seed=8,
                      fog=0.5, core=0.2)
        f.set_camera(DC.camera(r_screen=_r_eq(t), rot=_roll(t)))
        atmos.marine_snow(f, density=0.45 * a, t=t, seed=19, sink=9.0, current=(6.0, 0.0), alpha=0.6, size=1.4)
    f.post["vignette"] = lerp(f.post["vignette"], 0.55, 0.8 * (1.0 - ss(9.3, T_PURE, t)))


def motion_blur(t, T):
    if T_X0 - 0.1 < t < T_END:
        return 2
    return 1


def cues(T):
    b = _beats(T)
    out = [Cue(-0.4, "inside the hull: close, boxed-in drone; the free-flow hiss of his helmet", gain_db=-14,
               dur=4.0)]
    for side in ("R", "L"):
        for t0, t1, ya, yb in MOVES[side]:
            if -0.2 <= t1 <= T_HANG:
                out.append(Cue(t1, "glove grips an iron pipe: a dull clank, rust grit", gain_db=-17 + 2.0 * hash01(int(t1 * 100), 3),
                               pan=-0.4, dur=0.3))
    out += [
        Cue(0.4, "a door on its side creaks open in the current", gain_db=-15, pan=0.1, dur=2.2),
        Cue(1.2, "the chair knocks softly against steel as it turns", gain_db=-19, pan=0.35, dur=0.6),
        Cue(b["captain"], "he lets go: the hose pays out, a falling rush of water", gain_db=-10, dur=1.4),
        Cue(b["safe"], "the beam finds the safe: a low resonant swell, iron", gain_db=-9, dur=2.2),
        Cue(T_LAND, "boots hit the deck plating through silt: a heavy muffled thud", gain_db=-6, dur=0.6),
        Cue(T_PUSH, "the push in: the room tone narrows, a faint high ring", gain_db=-12, dur=1.5),
        Cue(T_X0 + 0.1, "the dial: a low metallic hum swells into s09", gain_db=-10, dur=1.0),
    ]
    return out
