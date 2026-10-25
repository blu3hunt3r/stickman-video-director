"""s05 GUARD (62-80). The corridor, the guard's light, the stealth map, the clank and the cat.
The corridor is framed close, the figures half the frame's height and the corridor floor to
ceiling filling it, and the camera moves with the action, because a 9:16 frame cannot hold the
guard and the crew at a size that reads.
  The corridor (0-4): the cross corridor in side elevation, dark, close on the guard. He walks out
    to his post and his flashlight clicks on (0.5); it sweeps the corridor on the plan's clock (a
    full swing every 2 s). The camera pans right along his beam to the dark doorway where the crew
    stand pressed in file, black on black, only their rims showing, as its patch slides up to the
    doorway's edge and falls away. The score drops to the tick.
  The stealth map (4-9.5): the camera tilts up into the plan. The world folds down onto its chalk:
    the crew sink into their pieces and the guard into his pawn, whose cone sweeps the
    intersection between its walls, its timing ring running. In the dark gaps they hop across one
    at a time, landing on the beat (she 5.5, the Knight 6.5, the Cracker 7.5), the route's dots
    brightening under her. The camera tilts back down, close on the doorway.
  The near miss (9.5-15.5), one beat at a time: the Cracker, last in, steps to the mouth (9.5) and
    stops to get his breath (10.0); his stethoscope swings and CLANKS on the pipe (10.5, a
    ripple). The camera whips left to the guard as he spins round (11.0); his light swings toward
    the noise and stops on the crates: two gold eyes (12.0). The cat arches (12.5) and leaps down
    past him (13.0), its tail tipping the tin can, which hits the floor (13.5, clatter) as the cat
    streaks between his feet. He breathes out, half a laugh (14.0), lowers his light, turns away
    and walks off west (14.5); the camera drifts back to the doorway as the crew slip into the
    dark.
  The dial (15.5-18): the camera pushes down the black corridor to the far door: a chalk dot and
    the plan's ring on its dial (step 4, 16.5). s06 opens on that dial.
"""
import math
from functools import lru_cache

import cairo

from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross import bank as Bk
from films.double_cross import cast as C
from films.double_cross import kit as K
from films.double_cross import plan as P
from films.double_cross import shots as S
from films.double_cross.scenes import s03_plan as S3

# ---------------------------------------------------------------------------- beats
FILM_T0 = K.film_start("s05")
SHOTS = ((0.0, "the corridor"), (4.0, "tilt up: the stealth map"), (8.5, "tilt down"), (9.5, "the near miss"),
         (15.5, "down the corridor to the dial"))
SWEEP_PHASE = K.film_start("s03") + S3.SWEEP_T0   # film time his light began to swing in s03: the same clock
SWEEP_AMP = 32.0                # degrees each way, a full swing every 2 s
CONE_SPREAD = 22.0              # its half-angle: the crossing is dark only when |sweep| > CONE_SPREAD
T_CLICK = 0.5                   # the guard's flashlight clicks on
T_TILT_UP = (4.0, 5.0)
T_TILT_DOWN = (8.5, 9.5)
CROSS = {"architect": 5.5, "knight": 6.5, "cracker": 7.5}     # each crossing lands in a dark gap, on the beat
HOP = 0.25
T_STEP = (9.5, 9.8)             # the Cracker, last in, steps to the mouth ...
T_BEND = (10.0, 10.3)           # ... bends to get his breath ...
T_CLANK = 10.5                  # ... and his stethoscope swings into the pipe: CLANK
T_WHIP = (10.62, 10.9)          # the camera whips left to the guard ...
T_SPIN = (11.0, 11.3)           # ... as he spins round (a paper turn)
T_AIM = (11.25, 12.0)           # his light swings toward the noise, slowing, and stops on the crates ...
T_EYES = 12.0                   # ... two gold eyes in the beam
T_ARCH = (12.5, 12.8)           # the cat arches ...
T_LEAP = (13.0, 13.3)           # ... and leaps down past him ...
T_TIP = (13.05, 13.17)          # ... its tail tips the can ...
T_CLATTER = 13.5                # ... which falls off the crate: clatter, and rolls
T_STARTLE = 13.4                # the cat streaks between his feet: he jumps back
T_SIGH = 14.0                   # the guard breathes out, half a laugh
T_LOWER = (14.2, 14.5)          # lowers his light
T_TURN_BACK = (14.5, 14.75)     # turns away ...
T_TURN_MID = 0.5 * (T_TURN_BACK[0] + T_TURN_BACK[1])   # edge-on in that turn: his walk away takes over
T_STRAIGHT = (14.0, 14.6)       # the Cracker straightens up as the guard breathes out
T_SLIP = {"architect": (14.6, 15.0), "knight": (14.8, 15.2), "cracker": (15.0, 15.5)}   # they slip into the dark
T_PUSH = (15.5, 17.0)           # the camera pushes down the corridor to the far door's dial
T_DIAL = 16.5                   # a chalk dot on the dial, the plan's ring round it (step 4)
T_THREE = 9.75                  # step 3, circled on the world: they are across

# ---------------------------------------------------------------------------- places (set px; depths are plan y)
GUARD_X = 250.0                 # his post (the plan's GUARD_POST is at x 240)
GUARD_DEPTH = 900.0
WALL_DEPTH = 860.0              # the far wall (the cross corridor's north wall)
FILE_E1 = {"architect": (520.0, 975.0), "knight": (544.0, 1039.0), "cracker": (566.0, 1090.0)}   # in file, south
FILE_E2 = {"architect": (521.0, 758.0), "knight": (545.0, 800.0), "cracker": (558.0, 856.0)}     # across, north
CR_STEP = 8.0                   # the Cracker's last step east to the mouth
S_SLOTS = ((540.0, 975.0), (540.0, 1039.0), (540.0, 1090.0))     # the pieces wait in the south corridor ...
N_SLOTS = ((540.0, 842.0), (540.0, 800.0), (540.0, 758.0))       # ... and move up the north one
PIECE = {"architect": ("queen", K.PAPER, K.INK, 1), "knight": ("knight", K.RED, K.INK, 1),
         "cracker": ("bishop", K.GOLD, K.INK, -1)}
PATCH = (46.0, 36.0)            # the flashlight's patch on the wall (rx, ry)
PATCH_Y = -92.0
CAT_SEAT = Bk.CAT_SEAT
CAN_REST = (Bk.CAN_SEAT[0], Bk.CAN_SEAT[1] - 9.0)
CAN_FLOOR = 7.0                 # the can lying on the floor: its centre this far up
PIPE_HIT = Bk.PIPE_X - 5.0      # the pipe's west face
STOPWATCH = ((930.0, 190.0), 62.0)

# the set camera in elevation, close: zoom 4.8 puts the corridor floor to ceiling across most of
# the frame and a figure at a third of its height, the floor at the safe area's foot. Keys:
# (t, (x, y, zoom), ease into this key)
Y_C = -112.0
CAM_E1 = ((0.0, (236.0, Y_C, 4.8), None),           # the guard walks out to his post ...
          (1.9, (262.0, Y_C, 4.8), "inout"),
          (3.4, (538.0, Y_C, 4.8), "inout"),         # ... the camera pans along his beam to the crew
          (4.0, (538.0, Y_C, 4.8), "inout"))
CAM_E2 = ((T_TILT_DOWN[1], (552.0, Y_C, 4.8), None),  # the Cracker at the mouth
          (T_WHIP[0], (556.0, Y_C, 4.8), "inout"),
          (T_WHIP[1], (282.0, Y_C, 4.6), "inout5"),  # the whip to the guard
          (T_AIM[0], (288.0, Y_C, 4.5), "out"),
          (T_EYES + 0.15, (352.0, Y_C, 4.25), "inout"),   # with his light to the crates
          (T_TURN_BACK[0] + 0.1, (346.0, Y_C, 4.25), "inout"),
          (T_PUSH[0], (548.0, Y_C, 4.8), "inout"))   # back to the doorway as they slip away
CAM_END = Bk.Cam(Bk.DIAL_C[0], Bk.DIAL_C[1], 7.0)    # the far door's dial: s06 opens on this frame
MAP0 = (540.0, 900.0, 1.25, 78.0, 0.0, 540.0, 1000.0)    # the stealth map
MAP1 = (540.0, 900.0, 1.33, 80.0, 0.0, 540.0, 990.0)
PANS = (((1.9, 3.4), 6), (T_WHIP, 10), ((T_TURN_BACK[0] + 0.1, T_PUSH[0]), 6))   # fast moves: sub-frames to blur


def motion_blur(t, T):
    return next((n for (a, b), n in PANS if a <= t < b), 1)


def _seg(name, s0, s1, at, speed=1.0, **kw):
    return C.Seg(C.clip(name), s0, s1, at=at, speed=speed, **kw)


def sweep(ft):
    """The guard's light on the plan (degrees from east, + toward the south) at film time ft."""
    return SWEEP_AMP * math.sin(math.pi * (ft - SWEEP_PHASE))


def dark(ft):
    """Whether the crossing is out of his light at film time ft."""
    return abs(sweep(ft)) > CONE_SPREAD


# ============================================================================ cameras
def _keyed(keys, t):
    """The set camera along keys [(t, (x, y, zoom), ease into it)]: held outside them, the zoom
    geometric."""
    if t <= keys[0][0]:
        return Bk.Cam(*keys[0][1])
    for (t0, a, _), (t1, b, e) in zip(keys, keys[1:]):
        if t <= t1:
            return Bk.Cam.lerp(Bk.Cam(*a), Bk.Cam(*b), ease(e, (t - t0) / (t1 - t0)))
    return Bk.Cam(*keys[-1][1])


def cam_e(t):
    """The set camera in elevation."""
    if t < T_TILT_UP[0]:
        return _keyed(CAM_E1, t)
    if t < T_PUSH[0]:
        return _keyed(CAM_E2, t)
    return Bk.Cam.toward(Bk.Cam(*CAM_E2[-1][1]), CAM_END, ease("inout", clamp((t - T_PUSH[0]) / (T_PUSH[1] - T_PUSH[0]))),
                         Bk.DIAL_C)


E1_PC = Bk.plan_cam_for(Bk.Cam(*CAM_E1[-1][1]), GUARD_DEPTH)
E2_PC = Bk.plan_cam_for(Bk.Cam(*CAM_E2[0][1]), GUARD_DEPTH)


def _lerp_pc(a, b, u):
    v = [lerp(x, y, u) for x, y in zip(a, b)]
    v[2] = math.exp(lerp(math.log(a[2]), math.log(b[2]), u))
    return P.PlanCam(*v)


def plan_cam(t):
    """The plan camera from the tilt up to the end of the tilt down (None in elevation)."""
    if t < T_TILT_UP[0] or t >= T_TILT_DOWN[1]:
        return None
    if t < T_TILT_UP[1]:
        return _lerp_pc(E1_PC, MAP0, ease("inout", (t - T_TILT_UP[0]) / (T_TILT_UP[1] - T_TILT_UP[0])))
    if t < T_TILT_DOWN[0]:
        return _lerp_pc(MAP0, MAP1, ease("inout", (t - T_TILT_UP[1]) / (T_TILT_DOWN[0] - T_TILT_UP[1])))
    return _lerp_pc(MAP1, E2_PC, ease("inout", (t - T_TILT_DOWN[0]) / (T_TILT_DOWN[1] - T_TILT_DOWN[0])))


def _smooth(x, a, b):
    return ease("inout", clamp((x - a) / (b - a)))


# ============================================================================ performances
@lru_cache(maxsize=None)
def perfs():
    d = {}
    # the guard walks out to his post and stands sweeping (77_05: looking round, wary)
    d["guard_w"] = C.perf("guard", [_seg("104_02", 1.0, 2.3, 0.0, 0.9),
                                    _seg("77_05", 0.6, 4.2, 1.44, 0.75, travel=0.0, blend=0.45)], facing=1)
    d["guard_x"] = GUARD_X - d["guard_w"](1.44)[0]["pelvis"][0] * Bk.FIG_S
    # after the crossing: at his desk, then round to the noise, then away west
    d["guard_d"] = C.perf("guard", [_seg("77_05", 0.4, 4.2, 9.0, 0.62, travel=0.0)], facing=1)
    d["guard_off"] = C.perf("guard", [_seg("77_05", 2.0, 2.2, 0.0, 0.2, travel=0.0),     # (the walk starts as
                                      _seg("104_02", 1.38, 3.2, T_TURN_MID - 0.05, 1.0, blend=0.15)],  # he turns
                            facing=-1)                                                     # edge-on: no skid)
    d["guard_off_x"] = GUARD_X - d["guard_off"](T_TURN_MID)[0]["pelvis"][0] * Bk.FIG_S
    # the crew stand still: standing frames of their walks
    d["architect"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 0.0, 0.12, travel=0.0, lean=-3.0)], facing=-1)
    d["knight"] = C.perf("knight", [_seg("17_08", 5.7, 6.0, 0.0, 0.03, travel=0.0)], facing=-1)
    d["cracker"] = C.perf("cracker", [_seg("104_02", 5.7, 7.3, 0.0, 0.12, travel=0.0, lean=12.0)], facing=-1)
    d["cracker_e"] = C.perf("cracker", [_seg("104_02", 5.7, 7.3, 0.0, 0.12, travel=0.0, lean=10.0)], facing=1)
    return d


def _dry(who, st, pose, x, facing):
    """A figure's joints (set px) without drawing it."""
    surf = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    return C.draw(cairo.Context(surf), who, st, pose, x, 0.0, Bk.FIG_S, facing, rim=False)


def _aim(who, st, pose, x, facing, target):
    """Point the near arm (straight, the flashlight along it) at target (set px)."""
    S = _dry(who, st, pose, x, facing)["shoulder_near"]
    a1 = math.degrees(math.atan2(facing * (target[0] - S[0]), target[1] - S[1]))
    pose.arms["near"] = ("ang", a1 - pose.lean, 0.0)


def _bez(a, b, k, u):
    return ((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * k[0] + u * u * b[0],
            (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * k[1] + u * u * b[1])


# ---------------------------------------------------------------------------- the guard and his light
def _e1_light(t, gx):
    """(target, patch alpha) of his light in the first elevation: the sweep on the plan's clock,
    the patch sliding along the far wall from in front of him to the doorway's edge, and fading
    when the light swings south toward us."""
    a = sweep(FILM_T0 + t)
    edge = Bk.MOUTH_X[0] - PATCH[0] * 0.92
    near = gx + 92.0
    if a <= 0.0:
        return (lerp(edge, near, (-a / SWEEP_AMP) ** 0.8), PATCH_Y), 1.0
    f = _smooth(a, 0.0, 18.0)
    return (edge - 30.0 * f, lerp(PATCH_Y, -6.0, f)), 1.0 - f


DESK_SPOT = (218.0, -66.0)
CRATE_SPOT = (398.0, -134.0)
FEET_SPOT = (236.0, -2.0)
FLICK_SPOT = (318.0, -196.0)      # where his light jerks when the cat streaks between his feet


def _e2_target(t):
    """Where his light points in the near miss (set px): from his desk round toward the noise,
    stopping on the cat's eyes on the crates, then down after the cat as it streaks past him."""
    if t < T_AIM[0]:
        return DESK_SPOT
    if t < T_AIM[1]:
        return _bez(DESK_SPOT, CRATE_SPOT, (300.0, -230.0), ease("out3", (t - T_AIM[0]) / (T_AIM[1] - T_AIM[0])))
    if t < T_LEAP[0]:
        return CRATE_SPOT
    if t < T_LEAP[0] + 0.5:
        return _bez(CRATE_SPOT, FEET_SPOT, (330.0, -20.0), ease("inout", (t - T_LEAP[0]) / 0.5))
    if t < T_LOWER[0]:
        return FEET_SPOT
    if t < T_LOWER[1]:
        u = ease("inout", (t - T_LOWER[0]) / (T_LOWER[1] - T_LOWER[0]))
        return (lerp(FEET_SPOT[0], 330.0, u), -2.0)
    return (330.0, -2.0)


def guard_at(t, tt):
    """The guard: dict(st, pose, x, facing, sx, target, on, patch_a) at time t (pose on twos)."""
    d = perfs()
    if t < T_TILT_DOWN[0]:
        st, pose = d["guard_w"](tt)
        x = d["guard_x"]
        gx = x + st["pelvis"][0] * Bk.FIG_S
        target, pa = _e1_light(t, gx)
        on = t >= T_CLICK
        _aim("guard", st, pose, x, 1, target)
        return dict(st=st, pose=pose, x=x, facing=1, sx=1.0, target=target, on=on, patch_a=pa)
    if t < T_TURN_MID:
        st, pose = d["guard_d"](tt)
        x = GUARD_X - st["pelvis"][0] * Bk.FIG_S
        target = _e2_target(t)
        if t < T_SPIN[0]:
            sx = -1.0
        elif t < T_SPIN[1]:
            sx = -math.cos(math.pi * ease("inout", (t - T_SPIN[0]) / (T_SPIN[1] - T_SPIN[0])))
        elif t < T_TURN_BACK[0]:
            sx = 1.0
        else:
            sx = math.cos(math.pi * ease("inout", (t - T_TURN_BACK[0]) / (T_TURN_BACK[1] - T_TURN_BACK[0])))
        lift = 0.0
        if tt >= T_STARTLE:                               # the cat between his feet: he jolts, hops back,
            a = tt - T_STARTLE                            # and his light jerks up the wall ...
            jolt = ease("out", clamp(a / 0.08)) * (1.0 - _smooth(tt, T_STARTLE + 0.16, T_STARTLE + 0.7))
            lift = 7.0 * math.sin(math.pi * clamp(a / 0.25))
            x -= 9.0 * ease("out", clamp(a / 0.12)) * (1.0 - _smooth(tt, T_STARTLE + 0.3, T_SIGH + 0.4))
            pose.lean -= 14.0 * jolt
            pose.head += 12.0 * jolt
            target = (lerp(target[0], FLICK_SPOT[0], jolt), lerp(target[1], FLICK_SPOT[1], jolt))
        if tt >= T_SIGH:                                  # ... and breathes out: the shoulders drop
            pose.lean += 6.0 * math.sin(math.pi * clamp((tt - T_SIGH) / 0.5)) - 3.0 * clamp((tt - T_SIGH) / 0.3)
        xp = x + st["pelvis"][0] * Bk.FIG_S
        aim = target if sx >= 0.0 else (2.0 * xp - target[0], target[1])
        _aim("guard", st, pose, x, 1, (aim[0], aim[1] + lift))
        lit = (xp + sx * (aim[0] - xp), target[1])                 # the light swings round with him
        return dict(st=st, pose=pose, x=x, facing=1, sx=sx, target=lit, on=True, patch_a=1.0, lift=lift)
    st, pose = d["guard_off"](tt)
    x = d["guard_off_x"]
    xp = x + st["pelvis"][0] * Bk.FIG_S
    sx = 1.0
    if t < T_TURN_BACK[1]:                                         # the second half of his turn
        sx = -math.cos(math.pi * ease("inout", (t - T_TURN_BACK[0]) / (T_TURN_BACK[1] - T_TURN_BACK[0])))
    aim = (xp - 150.0, -2.0)
    _aim("guard", st, pose, x, -1, aim)
    return dict(st=st, pose=pose, x=x, facing=-1, sx=sx, target=(xp + sx * (aim[0] - xp), -2.0), on=True,
                patch_a=1.0)


# ---------------------------------------------------------------------------- the crew
def _hop_slots():
    """{who: [(t_land, slot)]}: the file in the south corridor and how it moves up, one hop a beat."""
    order = ["architect", "knight", "cracker"]
    pos = {w: ("S", i) for i, w in enumerate(order)}
    out = {w: [(-1e9, pos[w])] for w in order}
    for who in order:
        tc = CROSS[who]
        for w in order:
            kind, i = pos[w]
            if w == who:
                pos[w] = ("N", 0)
            elif kind == "N":
                pos[w] = ("N", i + 1)
            elif kind == "S" and i > 0 and order.index(w) > order.index(who):
                pos[w] = ("S", i - 1)
            else:
                continue
            out[w].append((tc, pos[w]))
    return out


HOPS = _hop_slots()


def _slot(s):
    kind, i = s
    return (S_SLOTS if kind == "S" else N_SLOTS)[i]


def piece_at(who, t):
    """(plan point, lift, tilt) of a crew piece on the stealth map."""
    sched = HOPS[who]
    for (_, a), (t1, b) in zip(sched, sched[1:]):
        if t < t1 - HOP:
            return _slot(a), 0.0, 0.0
        if t < t1:
            u = (t - (t1 - HOP)) / HOP
            pa, pb = _slot(a), _slot(b)
            e = ease("inout", u)
            dd = math.dist(pa, pb)
            return (lerp(pa[0], pb[0], e), lerp(pa[1], pb[1], e)), (18.0 + 0.22 * dd) * math.sin(math.pi * u), 0.0
    return _slot(sched[-1][1]), 0.0, 0.0


def _her_s(t):
    """How far along P.ROUTE_IN her piece has come."""
    p, _, _ = piece_at("architect", t)
    return 540.0 + (1150.0 - p[1])


def _her_s_t(s):
    """When the dot at s along the route lit (the dots behind her lit long ago)."""
    for t0, slot in HOPS["architect"]:
        if 540.0 + (1150.0 - _slot(slot)[1]) >= s - 1.0:
            return t0
    return -1e9


def crew_e(t, tt):
    """The crew in elevation: [(who, st, pose, x, facing, depth, rim_k, inside)], back to front.
    inside: behind the far wall's plane (seen through the doorway only)."""
    d = perfs()
    out = []
    if t < T_TILT_DOWN[0]:
        for who in ("architect", "knight", "cracker"):
            st, pose = d[who](tt)
            breathe = 1.2 * math.sin(2.0 * math.pi * (tt * 0.45 + 0.3 * len(who)))
            pose.lean += breathe
            x, depth = FILE_E1[who]
            if who == "knight":
                pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)
            out.append((who, st, pose, x - st["pelvis"][0] * Bk.FIG_S, -1, depth, 1.0, False))
        return out
    for who in ("architect", "knight", "cracker"):
        x, depth = FILE_E2[who]
        a, b = T_SLIP[who]
        rim_k = 1.0 - _smooth(t, a, b)
        if who == "cracker":
            st, pose = d["cracker_e"](tt)
            x += CR_STEP * ease("inout", clamp((t - T_STEP[0]) / (T_STEP[1] - T_STEP[0])))
            x -= 16.0 * _smooth(t, a, a + 0.3)                      # he backs into the doorway
            bend = _smooth(t, T_BEND[0], T_BEND[1]) * (1.0 - _smooth(t, T_STRAIGHT[0], T_STRAIGHT[1]))
            pose.lean += 12.0 * bend + 1.0 * math.sin(2.0 * math.pi * tt * 1.6) * bend
            pose.head -= 10.0 * bend
            out.append((who, st, pose, x - st["pelvis"][0] * Bk.FIG_S, 1, depth, rim_k, t >= a + 0.3))
            continue
        st, pose = d[who](tt)
        pose.lean += 1.0 * math.sin(2.0 * math.pi * (tt * 0.45 + 0.3 * len(who)))
        if who == "knight":
            pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)
        out.append((who, st, pose, x - st["pelvis"][0] * Bk.FIG_S, -1, depth, rim_k, True))
    return out


def _swing(t):
    """The stethoscope's swing (degrees from hanging, + toward the pipe): he stops short, it swings
    on into the pipe (T_CLANK), bounces back and settles."""
    if t < T_BEND[0]:
        return 0.0
    hit = 1.0
    if t < T_CLANK:
        return 21.0 * hit * ease("in", (t - T_BEND[0]) / (T_CLANK - T_BEND[0]))
    k = t - T_CLANK
    return 21.0 * math.exp(-3.2 * k) * math.cos(9.0 * k) * (1.0 if k > 0.0 else 1.0)


def _stethoscope(c, j, t, facing, rim):
    """Round his neck: the chest-piece swinging on its tube; it cannot pass the pipe."""
    neck = (lerp(j["head"][0], j["shoulder_near"][0], 0.55) + 3.0 * facing, lerp(j["head"][1], j["shoulder_near"][1], 0.7))
    L = 34.0
    a = math.radians(_swing(t)) * facing
    piece = (neck[0] + L * math.sin(a), neck[1] + L * math.cos(a))
    if facing > 0 and piece[0] > PIPE_HIT - 3.5:
        piece = (PIPE_HIT - 3.5, piece[1])
    Bk.stethoscope(c, (neck[0] - 6.0 * facing, neck[1] - 4.0), piece, 1.0, K.INK, rim=rim)
    return piece


# ============================================================================ the cat and the can
def cat_at(t):
    """(p, facing, mode, eyes, s) of the cat, or None once it has gone."""
    s = 0.27
    if t < T_EYES:
        return CAT_SEAT, -1, "sit", 0.12, s
    if t < T_ARCH[0]:
        return CAT_SEAT, -1, "sit", 1.0, s
    if t < T_LEAP[0]:
        return CAT_SEAT, -1, "arch", 1.0, s
    if t < T_LEAP[1]:
        u = (t - T_LEAP[0]) / (T_LEAP[1] - T_LEAP[0])
        p0, p1 = CAT_SEAT, (300.0, 0.0)
        return (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - 46.0 * math.sin(math.pi * u)), -1, "walk", 1.0, s
    x = 300.0 - 300.0 * (t - T_LEAP[1])
    if x < 120.0:
        return None
    return (x, 0.0), -1, "walk", 1.0, s


def can_at(t):
    """(x, y, angle) of the tin can, or None while it stands on its crate."""
    x0, y0 = CAN_REST
    edge = Bk.CRATES[2][0]                                # the top crate's west edge: it falls off here
    if t < T_TIP[0]:
        return None
    if t < T_TIP[1]:
        u = ease("in", (t - T_TIP[0]) / (T_TIP[1] - T_TIP[0]))
        return (x0 - 4.0 * u, y0 + 2.0 * u, -90.0 * u)
    if t < T_CLATTER:
        u = (t - T_TIP[1]) / (T_CLATTER - T_TIP[1])
        x = lerp(x0 - 4.0, edge - 14.0, u)
        y = lerp(y0 + 2.0, -CAN_FLOOR, u * u)
        return (x, y, -90.0 - 160.0 * u)
    k = t - T_CLATTER
    hop = 9.0 * max(0.0, math.sin(math.pi * clamp(k / 0.16))) * (1.0 if k < 0.16 else 0.0)
    roll = 38.0 * (1.0 - math.exp(-2.2 * k))
    return (edge - 14.0 - roll, -CAN_FLOOR - hop, -250.0 - math.degrees(roll / 7.0))


# ============================================================================ the light
def _patch_ellipses(c, p, alpha):
    for f, a in ((1.0, 0.10), (0.72, 0.10), (0.45, 0.12)):
        Bk.ellipse(c, p, PATCH[0] * f, PATCH[1] * f, K.PAPER, a * alpha)


def _wall_clip(c):
    """The far wall without the doorway (set px): the light lands on the wall, not down the corridor."""
    x0, x1 = Bk.CORR_X
    c.new_path()
    c.rectangle(x0, -Bk.CORR_H, x1 - x0, Bk.CORR_H)
    m0, m1 = Bk.MOUTH_X
    c.rectangle(m1, -Bk.MOUTH_H, m0 - m1, Bk.MOUTH_H)
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    c.clip()
    c.set_fill_rule(cairo.FILL_RULE_WINDING)


def _on_wall(g):
    target, a = g["target"], g["patch_a"] * (1.0 if g["on"] else 0.0)
    if a <= 0.0 or target[1] > -24.0:
        return None

    def fn(c):
        c.save()
        _wall_clip(c)
        _patch_ellipses(c, target, a)
        c.restore()
    return fn


def _front_light(c, g):
    """His light on what stands in front of the wall (the desk top, the crates) and on the floor."""
    target, a = g["target"], g["patch_a"] * (1.0 if g["on"] else 0.0)
    if a <= 0.0:
        return
    if target[1] > -24.0:                                     # on the floor
        for f, al in ((1.0, 0.12), (0.6, 0.14)):
            Bk.ellipse(c, (target[0], -1.0), 64.0 * f, 7.0 * f, K.PAPER, al * a)
        return
    c.save()
    c.new_path()
    d0, d1 = Bk.GUARD_DESK
    c.rectangle(d0, -82.0, d1 - d0, 26.0)
    for x0, y0, x1, y1 in Bk.CRATES:
        c.rectangle(x0, y1, x1 - x0, y0 - y1)
    c.clip()
    _patch_ellipses(c, target, a * 1.3)
    c.restore()


def _beam(c, cam, lens, ang, g):
    """The beam itself, a flat translucent wedge from the lens to where it lands (frame px)."""
    if lens is None or not g["on"]:
        return
    tgt = cam.to_frame(g["target"])
    d = math.dist(lens, tgt)
    on = clamp((g.get("t", 99.0) - T_CLICK) / 0.06)
    K.cone(c, lens, math.degrees(math.atan2(tgt[1] - lens[1], tgt[0] - lens[0])), 8.5, d * 1.02, K.PAPER,
           alpha=0.11 * on, steps=3)
    K.dot(c, lens, 5.0 * cam.zoom * 0.5, K.PAPER, seed=5, alpha=0.9 * on)


# ============================================================================ drawing: elevation
def _draw_guard(c, g, rim_w, alpha_rim=1.0):
    """The guard in set px (inside a camera); returns the flashlight hold (for its lens)."""
    fl = C.hold_flashlight(on=g["on"])
    pose = g["pose"]
    pose.hold["near"] = fl
    xp = g["x"] + g["st"]["pelvis"][0] * Bk.FIG_S
    sx = g["sx"]
    if abs(sx) < 0.03:
        sx = math.copysign(0.03, sx)
    c.save()
    c.translate(xp, -g.get("lift", 0.0))
    c.scale(sx, 1.0)
    c.translate(-xp, 0.0)
    C.draw(c, "guard", g["st"], pose, g["x"], 0.0, Bk.FIG_S, g["facing"], bg=K.INK, rim_w=rim_w,
           light=(-0.6 * math.copysign(1.0, sx), -0.8))
    c.restore()
    return fl


def _draw_crew(c, rows, t, rim_w, clip_inside=True):
    for who, st, pose, x, facing, depth, rim_k, inside in rows:
        if rim_k <= 0.01:
            continue
        rim = lerp(K.INK, C.RIM[who], rim_k)
        c.save()
        if inside and clip_inside:
            m0, m1 = Bk.MOUTH_X
            c.new_path()
            c.rectangle(m0 + 1.0, -Bk.MOUTH_H, m1 - m0 - 2.0, Bk.MOUTH_H + 4.0)
            c.clip()
        j = C.draw(c, who, st, pose, x, 0.0, Bk.FIG_S, facing, bg=K.INK, rim=rim, rim_w=rim_w)
        if who == "cracker":
            _stethoscope(c, j, t, facing, rim)
        c.restore()


def _elevation(c, t, tt):
    cam = cam_e(t)
    g = guard_at(t, tt)
    g["t"] = t
    can = can_at(t)
    dot = clamp((t - T_DIAL) / 0.2)
    Bk.corridor(c, cam, t, lamp=1.0, can=can, on_wall=_on_wall(g), door_dot=dot)
    rows = crew_e(t, tt)
    with cam.on(c):
        _front_light(c, g)
        ct = cat_at(t)
        if ct is not None:
            p, fc, mode, eyes, s = ct
            C.cat(c, p, s, t, facing=fc, mode=mode, eyes=eyes, rim=lerp(K.INK, K.STEEL, 0.6))
        rim_w = 4.0 / cam.zoom
        _draw_crew(c, [r for r in rows if r[7]], t, rim_w)
        fl = _draw_guard(c, g, rim_w)
        _draw_crew(c, [r for r in rows if not r[7]], t, rim_w)
    lens, ang = C.lens_at(c, fl)
    _beam(c, cam, lens, ang, g)
    # the sounds, seen: the clank on the pipe and the can on the floor
    if T_CLANK <= t < T_CLANK + 1.0:
        K.ripple(c, cam.to_frame((PIPE_HIT, -98.0)), t, T_CLANK, K.PAPER, n=3, every=0.14, life=0.75, r0=10.0,
                 r1=150.0, width=6.0, seed=51)
    if T_CLATTER <= t < T_CLATTER + 0.9:
        cp = can_at(T_CLATTER)
        K.ripple(c, cam.to_frame((cp[0], -4.0)), t, T_CLATTER, K.PAPER, n=2, every=0.15, life=0.6, r0=8.0, r1=90.0,
                 width=4.5, seed=52, alpha=0.8)
    if t >= T_THREE:
        u = clamp((t - T_THREE) / 0.45)
        K.circled(c, "3", cam.to_frame((624.0, -40.0)), 30.0, u, K.PAPER, width=5.0, seed=12, alpha=0.9)
    if t >= T_DIAL:                                           # step 4's mark: the plan's ring on the dial
        u = clamp((t - T_DIAL) / 0.35)
        p = cam.to_frame(Bk.DIAL_C)
        r = (Bk.DIAL_R + 8.0) * cam.zoom
        K.chalk_circle(c, p, r, u, 2.5 * cam.zoom * 0.45, K.PAPER, seed=137, alpha=0.9)
        if u >= 1.0:
            K.chalk_line(c, [p, (p[0] + 0.5 * r * 0.6, p[1] - 0.5 * r * 0.8)], 1.0, 2.5 * cam.zoom * 0.45, K.PAPER,
                         seed=138, alpha=0.9)


# ============================================================================ drawing: the tilt and the map
def _ring_hand(c, ft, a):
    """The timing ring's dot, running round once a swing (plan px), as in s03."""
    amp = abs(sweep(ft)) / SWEEP_AMP
    ang = math.radians(-90.0 + 180.0 * (ft - SWEEP_PHASE))
    p = (P.GUARD_POST[0] + P.RING_R * math.cos(ang), P.GUARD_POST[1] + P.RING_R * math.sin(ang))
    K.dot(c, p, 6.0 + 2.0 * amp, K.PAPER, seed=139, alpha=0.9 * a)


def _map_plan(c, pc, t):
    """The blueprint under the world: Plan A, the guard's cone on its clock, the route lit under her."""
    if pc.flat() < 1e-6:                     # the paper edge-on (the tilt's first frame): nothing to see
        return
    ft = FILM_T0 + t
    plan_k = _smooth(pc.phi, 25.0, 70.0)
    with pc.ground(c):
        P.draw_sheet(c, 1.0)
        P.draw_plan_a(c, 1.0, prog={"in": 0.0, "cone": 0.0})
        Bk.ghost_route(c, P.ROUTE_IN, _her_s(t), gap=22.0, r=6.5, ghost=0.32, seed=3, t=t, lit_t=_her_s_t)
        if plan_k > 0.0:
            c.save()
            x0, y0, x1, y1 = P.CONE_BAND
            c.rectangle(x0, y0, x1 - x0, y1 - y0)
            c.clip()
            K.cone(c, (P.GUARD_POST[0] + 24.0, P.GUARD_POST[1]), sweep(ft), CONE_SPREAD, 320.0, alpha=0.16 * plan_k)
            c.restore()
            _ring_hand(c, ft, plan_k)


def _piece_k(t):
    """How far the world has folded into the plan (0 the figures standing .. 1 the pieces)."""
    if t < T_TILT_DOWN[0]:
        return _smooth(t, T_TILT_UP[0] + 0.1, T_TILT_UP[0] + 0.7)
    return 1.0 - _smooth(t, T_TILT_DOWN[0] + 0.2, T_TILT_DOWN[1] - 0.15)


def _tilt(c, t, tt, pc):
    k = _piece_k(t)
    wall_a = 1.0 - _smooth(pc.phi, 18.0, 58.0)
    _map_plan(c, pc, t)
    g = guard_at(t, tt)
    g["t"] = t
    can = can_at(t)
    # the far wall: a set standing on its chalk line, folding down as the camera rises
    if wall_a > 0.0:
        c.push_group()
        with Bk.TiltSet(pc, WALL_DEPTH).on(c):
            Bk.corridor_px(c, t, lamp=1.0, can=can, on_wall=_on_wall(g), bg=False)
        c.pop_group_to_source()
        c.paint_with_alpha(wall_a)
    # the pieces rise out of the plan as the figures fold into it (back to front)
    items = []
    for who in ("architect", "knight", "cracker"):
        p, lift, tilt = piece_at(who, t)
        items.append((p[1], "piece", who, p, lift))
    items.append((P.GUARD_POST[1], "pawn", "guard", P.GUARD_POST, 0.0))
    rows = {r[0]: r for r in crew_e(t, tt)}
    for depth, kind, who, p, lift in sorted(items, key=lambda it: pc.depth(it[3])):
        if k > 0.0:
            if kind == "pawn":
                P.piece_on(c, pc, "pawn", p, 100.0 * k, K.INK, K.PAPER, facing=1, shadow=0.0)
            else:
                pk, col, edge, fc = PIECE[who]
                P.piece_on(c, pc, pk, p, 100.0 * k, col, edge, facing=fc, lift=lift, shadow=0.0)
        if k < 1.0:
            if kind == "pawn":
                ts = Bk.TiltSet(pc, GUARD_DEPTH, stand=True)
                with ts.on(c):
                    with Bk.popped(c, 0.0, 1.0 - k) as ok:
                        if ok:
                            fl = _draw_guard(c, g, 4.0 / ts.zoom)
                if wall_a > 0.0 and k < 0.6:
                    lens, ang = C.lens_at(c, fl) if ok else (None, 0.0)
                    if lens is not None:
                        tgt = Bk.TiltSet(pc, WALL_DEPTH).to_frame(g["target"])
                        K.cone(c, lens, math.degrees(math.atan2(tgt[1] - lens[1], tgt[0] - lens[0])), 8.5,
                               math.dist(lens, tgt), K.PAPER, alpha=0.11 * wall_a, steps=3)
            else:
                who_, st, pose, x, facing, dep, rim_k, inside = rows[who]
                ts = Bk.TiltSet(pc, dep, stand=True)
                with ts.on(c):
                    with Bk.popped(c, 0.0, 1.0 - k) as ok:
                        if ok:
                            rim = lerp(K.INK, C.RIM[who], rim_k)
                            j = C.draw(c, who, st, pose, x, 0.0, Bk.FIG_S, facing, bg=K.INK, rim=rim,
                                       rim_w=4.0 / ts.zoom)
                            if who == "cracker":
                                _stethoscope(c, j, t, facing, rim)


# ============================================================================ render
def _can_frame(t):
    """The tin can on the frame (frame px)."""
    can = can_at(t) or (CAN_REST[0], CAN_REST[1], 0.0)
    return cam_e(t).to_frame((can[0], can[1]))


INSERTS = (S.Punch(T_CLATTER - 0.01, 5, _can_frame, 6.0, seed=51),)      # the clatter, close


def render(f, t, T):
    S.play(f, t, T, render_plain, INSERTS)


def render_plain(f, t, T):
    K.scene_setup(f, K.DEEP)
    tt = K.twos(t)
    with f.screen() as c:
        pc = plan_cam(t)
        if pc is None:
            _elevation(c, t, tt)
        else:
            _tilt(c, t, tt, pc)
        K.stopwatch(c, STOPWATCH[0], STOPWATCH[1], K.heist_beats(FILM_T0 + t))


# ============================================================================ cues
def _pan(t, x):
    pc = plan_cam(t)
    if pc is None:
        fx = cam_e(t).to_frame((x, 0.0))[0]
    else:
        fx = pc.to_view((x, GUARD_DEPTH))[0]
    return round(clamp((fx - 540.0) / 540.0, -1.0, 1.0), 2)


def cues(T):
    d = perfs()
    out = [Cue(0.0, "the score drops away to the heist clock's tick alone: a dark, held corridor (room tone, a far "
                    "hum of the building)", gain_db=-24, dur=9.5),
           Cue(T_CLICK, "a flashlight clicks on (a small metal switch)", gain_db=-14, pan=_pan(T_CLICK, 200.0))]
    for t0, side, fx in Bk.footfalls(d["guard_w"], 0.0, 1.6):
        out.append(Cue(t0, "footstep: the guard's hard heel on a stone corridor floor (echo)", gain_db=-19,
                       pan=_pan(t0, d["guard_x"] + fx * Bk.FIG_S)))
    out.append(Cue(1.0, "the faint creak of the guard's leather belt as his light swings (it repeats softly)",
                   gain_db=-30, pan=_pan(1.0, GUARD_X), dur=3.0))
    out.append(Cue(2.9, "a breath held in the doorway: his light's patch slides up to its edge", gain_db=-26,
                   pan=_pan(3.0, Bk.MOUTH_X[0])))
    out.append(Cue(T_TILT_UP[0], "a paper fold and a soft whoosh: the corridor folds down into the plan as the "
                                 "camera tilts up", gain_db=-16, dur=1.0))
    for k in range(4, 9):                                   # the plan's clock: a tock at each end of the swing
        t0 = k + 0.5
        if T_TILT_UP[1] - 0.6 <= t0 <= T_TILT_DOWN[0]:
            out.append(Cue(t0, "a low wooden tock: the guard's light at the end of its swing (the plan's timing)",
                           gain_db=-21, pan=-0.45))
    names = {"architect": "the queen", "knight": "the red knight", "cracker": "the gold bishop"}
    for who, t0 in CROSS.items():
        out.append(Cue(t0, f"a wooden piece clack: {names[who]} hops across the corridor in the dark gap",
                       gain_db=-13, pan=0.05))
    out.append(Cue(T_TILT_DOWN[0], "a paper unfold and a soft whoosh: the camera tilts back down; the corridor "
                                   "stands up again", gain_db=-16, dur=1.0))
    out += [Cue(T_STEP[0] + 0.1, "a soft shuffling step: the Cracker reaches the doorway", gain_db=-24, pan=_pan(9.6, 560.0)),
            Cue(T_BEND[0], "an old man's wheezing breath, held in", gain_db=-22, pan=_pan(9.7, 560.0)),
            Cue(T_CLANK, "CLANK: the stethoscope's steel chest-piece swings into an iron pipe (it rings down the "
                         "pipe)", gain_db=-6, pan=_pan(T_CLANK, Bk.PIPE_X)),
            Cue(T_WHIP[0], "a whip whoosh: the camera whips left to the guard", gain_db=-18,
                dur=T_WHIP[1] - T_WHIP[0]),
            Cue(T_SPIN[0], "a heavy coat swishes: the guard spins round", gain_db=-15, pan=_pan(T_SPIN[0], GUARD_X)),
            Cue(T_EYES - 0.05, "the score's held breath: a single low muted-trumpet note", gain_db=-20),
            Cue(T_ARCH[0], "a cat's hiss", gain_db=-14, pan=_pan(T_ARCH[0], CAT_SEAT[0])),
            Cue(T_LEAP[0], "claws scrabble on wood: the cat leaps off the crates", gain_db=-17,
                pan=_pan(T_LEAP[0], CAT_SEAT[0])),
            Cue(T_TIP[0], "tink: the tin can tips over on the crate", gain_db=-18, pan=_pan(T_TIP[0], Bk.CAN_SEAT[0])),
            Cue(T_STARTLE, "the guard yelps and stumbles back as the cat streaks between his feet (a scuff, a "
                           "gasp)", gain_db=-14, pan=_pan(T_STARTLE, GUARD_X)),
            Cue(T_CLATTER, "CLATTER: the tin can hits the stone floor, bounces and rolls", gain_db=-8,
                pan=_pan(T_CLATTER, Bk.CRATES[2][0] - 14.0), dur=0.9),
            Cue(T_SIGH, "the guard breathes out: a relieved sigh, half a laugh", gain_db=-16, pan=_pan(T_SIGH, GUARD_X)),
            Cue(T_TURN_BACK[0], "a coat rustles: the guard turns away", gain_db=-22, pan=_pan(T_TURN_BACK[0], GUARD_X))]
    perf = d["guard_off"]
    x0 = d["guard_off_x"]
    out.append(Cue(T_TURN_MID, "a heel scuffs on stone: the guard pivots away", gain_db=-24, pan=_pan(T_TURN_MID, GUARD_X)))
    for t0, side, fx in Bk.footfalls(perf, T_TURN_MID, T_PUSH[0] + 0.5):
        out.append(Cue(t0, "footstep: the guard walks off down the corridor (going away)", gain_db=-22,
                       pan=_pan(t0, x0 + fx * Bk.FIG_S)))
    for who, (a, b) in T_SLIP.items():
        out.append(Cue(a + 0.1, "a soft step on stone: one of the crew slips into the dark corridor", gain_db=-27,
                       pan=_pan(a, FILE_E2[who][0])))
    out.append(Cue(T_PUSH[0], "a low rising whoosh: the camera pushes down the black corridor", gain_db=-17,
                   dur=T_PUSH[1] - T_PUSH[0]))
    out.append(Cue(T_DIAL, "a chalk tap and a quick chalk circle: the plan's mark on the dial", gain_db=-15))
    return out
