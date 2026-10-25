"""s05 GUARD (62-80): the hall, framed close. The guard's sweep; across in the dark gaps; the clank,
the cat, the can; the guard walks on; the push to the dial.

The hall is bank.corridor DRAWN MIRRORED (frame x' = W - x). s04 ends on the street section with
the crew pressed in the hall's dark corner by the side door (left) and the guard facing them
across the hall (right), so here too the corner is on the left and the guard's post on the
right; the mouth of the way to the vault lies between them, and the crew travel rightward toward
the vault, as the section has it. Every place below is in that mirrored set's px (X = W - x of
the set's own constants, y as the set's); figures are drawn unmirrored at those X.

  0.0-2.0   THE GUARD, close: at his post in the dark, the desk lamp at his back. His flashlight
            clicks on (0.5) and its PAPER cone sweeps the hall, a full swing every 2 s (s04's
            clock).
  2.0-4.0   THE CORNER, close: the crew pressed in file, black on black: their rims, and her two
            PAPER eyes. The light's patch slides along the wall to the corner's edge, a hand's
            breadth from the Knight's nose (3.0), and falls away.
  4.0-9.5   ACROSS: one at a time, each in a dark gap of the sweep, they scurry across the lit
            stretch into the mouth's dark: she (5.5), the Knight (6.5), the Cracker (7.5); the
            Cracker's AMBER heartbeat thuds. The guard turns to his desk (8.0).
  9.5-10.25 THE CRACKER, close: last in, at the mouth's edge, he lets his breath go and bends; his
            stethoscope swings out and CLANKS on the pipe (10.0): the sound's ring.
  10.25-15.5 THE GUARD: the ring reaches him and he spins round (10.25); his PAPER look and cone
            swing toward the noise (10.5) and stop on the crates: a callout, two AMBER eyes in
            the dark (11.5). The cat arches (12.0) and leaps down past him (12.5), its tail
            tipping the tin can, which hits the floor (13.0) as the cat streaks between his feet.
            He breathes out, half a laugh (13.75), lowers his light, turns away and walks off on
            his round (14.25).
  15.5-18.0 THE MOUTH: the crew slip down its dark to the vault door; the camera pushes in on the
            door's dial (16.0-18.0), where her small light finds it (17.0). s06 opens on the dial.
"""
import math
from functools import lru_cache

import cairo

from engine import bass
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import kit as K

k = K.k
W = K.W
INK, PAPER, AMBER, RED, STEEL = K.INK, K.PAPER, K.AMBER, K.RED, K.STEEL
S = Bk.FIG_S

# ---------------------------------------------------------------------------- beats (scene time)
FILM_T0 = 62.0
SWEEP_PHASE = 62.0              # film time the guard's sweep is level, going toward the corner (s04's clock)
SHOTS = ((0.0, "the guard"), (2.0, "the corner"), (4.0, "across"), (9.5, "the Cracker"),
         (10.25, "the guard: the near miss"), (15.5, "the mouth: the push to the dial"))
T_ARM = (0.3, 0.62)             # his light comes up ...
T_CLICK = 0.5                   # ... and clicks on
T_EDGE = 3.0                    # its patch at the corner's edge, then it falls away
T_UP = {"architect": (4.2, 4.7), "cracker": (6.2, 6.7)}       # stepping up to the edge of the dark
CROSS = {"architect": (5.15, 5.85), "knight": (6.15, 6.85), "cracker": (7.15, 7.885)}   # each in a dark gap
T_DESK = (7.9, 8.3)             # the guard turns to his desk: his light off the hall
T_CR_TURN = (8.1, 8.35)         # the Cracker, at the mouth's edge, turns back to the way they came
T_BREATH = 9.5                  # ... lets his breath go and bends
T_CLANK = 10.0                  # the chest-piece swings into the pipe
T_SPIN = (10.25, 10.5)          # the guard spins round
T_AIM = (10.5, 11.5)            # his look and light swing toward the noise and stop on the crates
T_EYES = 11.5                   # two AMBER eyes: the callout
T_ARCH = 12.0                   # the cat arches
T_LEAP = (12.5, 12.8)           # and leaps down past him
T_TIP = (12.55, 12.67)          # its tail tips the can off the crate
T_STARTLE = 12.95               # the cat between his feet: he jumps back
T_CLATTER = 13.0                # the can hits the floor
T_SIGH = 13.75                  # he breathes out, half a laugh
T_LOWER = (13.95, 14.25)        # lowers his light
T_TURN_BACK = (14.25, 14.5)     # turns away ...
T_TURN_MID = 0.5 * (T_TURN_BACK[0] + T_TURN_BACK[1])   # (edge-on: his walk takes over)
T_STRAIGHT = (13.85, 14.35)     # the Cracker straightens up
T_SLIP = {"architect": (15.5, 16.1), "knight": (15.62, 16.22), "cracker": (15.75, 16.5)}   # down the mouth
T_PUSH = (16.0, 18.0)
T_HER_LIGHT = 17.0              # her small light finds the dial

WHO = ("knight", "architect", "cracker")


# ---------------------------------------------------------------------------- places (mirrored set px)
def mx(x):
    """A set x (bank.corridor's own) in this scene's mirrored px."""
    return W - x


MOUTH = (mx(Bk.MOUTH_X[1]), mx(Bk.MOUTH_X[0]))          # (505, 575): the dark mouth of the way to the vault
PIPE_X = mx(Bk.PIPE_X)                                  # 490: the vertical pipe beside it
PIPE_FACE = PIPE_X + 5.0                                # its face toward the mouth
CRATES = tuple((mx(x1), y0, mx(x0), y1) for x0, y0, x1, y1 in Bk.CRATES)    # (X0, bottom, X1, top)
CAT_SEAT = (mx(Bk.CAT_SEAT[0]), Bk.CAT_SEAT[1])         # (678, -124): the top crate, its mouth end
CAN_REST = (mx(Bk.CAN_SEAT[0]), Bk.CAN_SEAT[1] - 9.0)   # (724, -133): the can, its guard end
CAN_FLOOR = 7.0
TOP_EDGE = mx(Bk.CRATES[2][0])                          # 740: the top crate's guard end (the can falls off it)
DESK = (mx(Bk.GUARD_DESK[1]), mx(Bk.GUARD_DESK[0]))    # (804, 884)
GUARD_X = 828.0                                         # his post, in front of the desk
DIAL = Bk.DIAL_C                                        # (540, -160): the far door's dial
FILE = {"cracker": 356.0, "architect": 396.0, "knight": 432.0}   # pressed in file, facing the light
READY = {"architect": 428.0, "cracker": 430.0}          # stepped up to the dark's edge
IN = {"architect": 552.0, "knight": 540.0, "cracker": 524.0}     # in the mouth (the Cracker at its edge)
EDGE_X, NEAR_X, PATCH_Y = 486.0, GUARD_X - 96.0, -96.0  # the patch's reach along the wall
PATCH = (40.0, 32.0)
DESK_SPOT = (mx(218.0), -66.0)                          # his light on the logbook
CRATE_SPOT = (CAT_SEAT[0] + 4.0, CAT_SEAT[1] - 22.0)   # on the cat's eyes
FEET_SPOT = (mx(236.0), -2.0)
FLICK_SPOT = (mx(318.0), -196.0)                        # where his light jerks when the cat streaks past
LOW_SPOT = (760.0, -2.0)                                # lowered, on the floor
LAMP = (mx(Bk.GUARD_LAMP[0]), Bk.GUARD_LAMP[1])         # (868, -84): the desk lamp, the hall's one light
DARK = ((56.0, 0.25), (104.0, 0.3), (165.0, 0.4), (250.0, 0.3))   # the dark: INK beyond each radius of it
RIM_W = 3.4                                             # frame px

# cameras (mirrored set px): (x, y, zoom); keys are (t, (x, y, zoom)), eased in-out between
CAM_A = (800.0, -122.0, 6.8)                            # the guard
CAM_B = (412.0, -122.0, 6.8)                            # the corner
CAM_C = ((4.0, (466.0, -120.0, 4.5)), (9.5, (482.0, -118.0, 4.75)))           # across
CAM_D = (500.0, -116.0, 7.0)                            # the Cracker
CAM_E = ((10.25, (760.0, -150.0, 4.4)), (11.6, (742.0, -150.0, 4.5)), (13.4, (752.0, -146.0, 4.45)),
         (15.5, (766.0, -140.0, 4.35)))                 # the guard, the crates, the cat
CAM_G = (540.0, -126.0, 4.6)                            # the mouth
CAM_END = Bk.Cam(DIAL[0], DIAL[1], 7.0)                 # the dial: s06 opens on this frame
LENS_C, LENS_R = (300.0, 300.0), 200.0                  # the callout's lens (frame px)


def motion_blur(t, T):
    return 1


def _seg(name, s0, s1, at, speed=1.0, **kw):
    return C.Seg(C.clip(name), s0, s1, at=at, speed=speed, **kw)


def _keys(keys, t):
    if t <= keys[0][0]:
        return Bk.Cam(*keys[0][1])
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            return Bk.Cam.lerp(Bk.Cam(*a), Bk.Cam(*b), ease("inout", (t - t0) / (t1 - t0)))
    return Bk.Cam(*keys[-1][1])


def shot(t):
    return [name for t0, name in SHOTS if t >= t0][-1]


def cam_at(t):
    """This scene's camera (mirrored set px) at t: hard cuts on the beat, eased moves within."""
    if t < 2.0:
        return Bk.Cam(*CAM_A)
    if t < 4.0:
        return Bk.Cam(*CAM_B)
    if t < 9.5:
        return _keys(CAM_C, t)
    if t < 10.25:
        return Bk.Cam(*CAM_D)
    if t < 15.5:
        return _keys(CAM_E, t)
    u = ease("inout", clamp((t - T_PUSH[0]) / (T_PUSH[1] - T_PUSH[0])))
    return Bk.Cam.toward(Bk.Cam(*CAM_G), CAM_END, u, DIAL)


def _smooth(x, a, b):
    return ease("inout", clamp((x - a) / (b - a)))


# ---------------------------------------------------------------------------- the sweep
def sweep(t):
    """The guard's light on its clock, -1..1: +1 toward the far wall close to him, 0 along the hall
    to the corner's edge, -1 swung round toward us (a full swing every 2 s, s04's clock)."""
    return math.sin(math.pi * (FILM_T0 + t - SWEEP_PHASE))


def sweep_target(t):
    """(target, alpha) of his light while he sweeps: the patch slides along the far wall, slowing
    to a stop at the corner's edge, and falls away to the floor (fading) as the light swings
    round toward us."""
    a = sweep(t)
    if a >= 0.0:
        return (lerp(EDGE_X, NEAR_X, a * a), PATCH_Y), 1.0
    f = ease("inout", clamp(-a / 0.4))
    return (EDGE_X + 22.0 * f, lerp(PATCH_Y, -4.0, f)), 1.0 - f


def _bez(a, b, q, u):
    return ((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * q[0] + u * u * b[0],
            (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * q[1] + u * u * b[1])


# ============================================================================ performances
def _px(p, t):
    return p(t)[0]["pelvis"][0] * S


def _chain(who, segs, facing, x0, marks):
    """A performance whose pelvis starts at x0 and, for each moving segment i in marks, arrives at
    marks[i] when segment i + 1 begins (that segment's travel scaled to fit); and the x to draw it
    at."""
    segs = list(segs)
    for i in sorted(marks):
        for _ in range(2):
            p = C.perf(who, segs, facing=facing)
            xd = x0 - _px(p, segs[0].at)
            g = segs[i]
            tb = segs[i + 1].at if i + 1 < len(segs) else g.end
            d = _px(p, tb) - _px(p, g.at)
            want = marks[i] - (xd + _px(p, g.at))
            if abs(d) > 1e-6:
                segs[i] = C.Seg(g.clip, g.src0, g.src1, at=g.at, speed=g.speed, blend=g.blend,
                                travel=g.travel * want / d, lean=g.lean)
    p = C.perf(who, segs, facing=facing)
    return p, x0 - _px(p, segs[0].at)


def _stand(who, at, **kw):
    if who == "knight":
        return _seg("17_08", 5.7, 6.0, at, 0.03, travel=0.0, **kw)
    return _seg("104_02", 5.7, 7.3, at, 0.12, travel=0.0, **kw)


@lru_cache(maxsize=None)
def perfs():
    d = {}
    # the crew: pressed in file; stepping up to the dark's edge; the scurry across (17_03, her
    # stealth walk, quick: a tiptoe scurry); standing in the mouth's dark
    a0, a1 = CROSS["architect"]
    d["architect"], d["architect_x"] = _chain("architect", [
        _stand("architect", 0.0, lean=-3.0),
        _seg("17_03", 1.0, 1.8, T_UP["architect"][0], 1.6, blend=0.2),
        _stand("architect", T_UP["architect"][1], lean=6.0, blend=0.2),
        _seg("17_03", 1.0, 3.25, a0, 2.25 / (a1 - a0), blend=0.1),
        _stand("architect", a1, lean=-2.0, blend=0.2)], 1, FILE["architect"],
        {1: READY["architect"], 3: IN["architect"]})
    b0, b1 = CROSS["knight"]
    d["knight"], d["knight_x"] = _chain("knight", [
        _stand("knight", 0.0),
        _seg("17_03", 1.0, 3.25, b0, 2.25 / (b1 - b0), blend=0.1, lean=4.0),
        _stand("knight", b1, blend=0.2)], 1, FILE["knight"], {1: IN["knight"]})
    c0, c1 = CROSS["cracker"]
    d["cracker"], d["cracker_x"] = _chain("cracker", [
        _stand("cracker", 0.0, lean=12.0),
        _seg("17_03", 1.0, 1.8, T_UP["cracker"][0], 1.6, blend=0.2, lean=8.0),
        _stand("cracker", T_UP["cracker"][1], lean=14.0, blend=0.2),
        _seg("17_03", 1.0, 3.25, c0, 2.25 / (c1 - c0), blend=0.1, lean=6.0),
        _stand("cracker", c1, lean=10.0, blend=0.25)], 1, FILE["cracker"],
        {1: READY["cracker"], 3: IN["cracker"]})
    # the guard: wary at his post (77_05, looking round with his flashlight), on at his desk and
    # through the near miss; then away on his round (a walk), as DOUBLE CROSS's guard
    d["guard"] = C.perf("guard", [_seg("77_05", 0.4, 4.2, 0.0, 0.48, travel=0.0),
                                  _seg("77_05", 0.4, 4.2, T_DESK[0], 0.58, travel=0.0, blend=0.4)], facing=1)
    d["guard_x"] = GUARD_X - _px(d["guard"], 0.0)
    d["guard_off"] = C.perf("guard", [_seg("77_05", 2.0, 2.2, 0.0, 0.2, travel=0.0),
                                      _seg("104_02", 1.38, 3.2, T_TURN_MID - 0.05, 1.12, blend=0.15)], facing=1)
    d["guard_off_x"] = GUARD_X - _px(d["guard_off"], T_TURN_MID)
    return d


def _dry(who, st, pose, x, facing):
    surf = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    return C.draw(cairo.Context(surf), who, st, pose, x, 0.0, S, facing, rim=False)


def _aim(who, st, pose, x, target):
    """Point the near arm straight at target (set px, the figure facing +x): the flashlight
    along it."""
    sh = _dry(who, st, pose, x, 1)["shoulder_near"]
    a1 = math.degrees(math.atan2(target[0] - sh[0], target[1] - sh[1]))
    pose.arms["near"] = ("ang", a1 - pose.lean, 0.0)


# ============================================================================ the guard
def _near_target(t, xp):
    """Where his light points after the spin (world, facing left): from in front of him round
    toward the noise, slowing, stopping on the cat's eyes; down after the cat; lowered."""
    front = (2.0 * xp - DESK_SPOT[0], DESK_SPOT[1])
    if t < T_AIM[1]:
        u = ease("out3", clamp((t - T_AIM[0]) / (T_AIM[1] - T_AIM[0])))
        return _bez(front, CRATE_SPOT, (742.0, -214.0), u)
    if t < T_LEAP[0]:
        return CRATE_SPOT
    if t < T_LEAP[0] + 0.5:
        return _bez(CRATE_SPOT, FEET_SPOT, (752.0, -24.0), ease("inout", (t - T_LEAP[0]) / 0.5))
    if t < T_LOWER[0]:
        return FEET_SPOT
    u = ease("inout", clamp((t - T_LOWER[0]) / (T_LOWER[1] - T_LOWER[0])))
    return (lerp(FEET_SPOT[0], LOW_SPOT[0], u), lerp(FEET_SPOT[1], LOW_SPOT[1], u))


def guard_at(t):
    """The guard at t: dict(st, pose, x, sx, lift, target, alpha, on). The pose is on twos (from
    twos(t)); sx is the paper turn (+1 facing right, -1 left); target is where his light lands
    (mirrored set px), alpha its patch's strength."""
    tt = K.twos(t)
    d = perfs()
    on = t >= T_CLICK
    if tt < T_TURN_MID:
        st, pose = d["guard"](tt)
        x = d["guard_x"]
        xp = x + st["pelvis"][0] * S
        lift = 0.0
        alpha = 1.0
        if tt < T_DESK[0]:                                   # sweeping the hall, facing left
            sx = -1.0
            tgt, alpha = sweep_target(tt)
            if tt < T_ARM[1]:
                low = (xp - 30.0, -12.0)
                u = ease("inout", clamp((tt - T_ARM[0]) / (T_ARM[1] - T_ARM[0])))
                tgt = (lerp(low[0], tgt[0], u), lerp(low[1], tgt[1], u))
            base = (2.0 * xp - tgt[0], tgt[1])
        elif tt < T_SPIN[0]:                                 # round to his desk, the light on the logbook
            u = ease("inout", clamp((tt - T_DESK[0]) / (T_DESK[1] - T_DESK[0])))
            sx = -math.cos(math.pi * u)
            t0, a0 = sweep_target(T_DESK[0])
            b0 = (2.0 * xp - t0[0], t0[1])
            base = (lerp(b0[0], DESK_SPOT[0], u), lerp(b0[1], DESK_SPOT[1], u))
            alpha = lerp(a0, 1.0, u)
            pose.lean += 5.0 * u                             # over the desk
        else:
            if tt < T_SPIN[1]:                               # the spin: the light swings round with him
                u = ease("inout", (tt - T_SPIN[0]) / (T_SPIN[1] - T_SPIN[0]))
                sx = math.cos(math.pi * u)
                base = DESK_SPOT
            else:
                sx = -1.0
                if tt >= T_TURN_BACK[0]:                     # turning away: the first half
                    u = ease("inout", (tt - T_TURN_BACK[0]) / (T_TURN_BACK[1] - T_TURN_BACK[0]))
                    sx = -math.cos(math.pi * u)
                tgt = _near_target(min(tt, T_TURN_BACK[0]), xp)
                if tt >= T_STARTLE:                          # the cat between his feet: he jolts, hops back,
                    a = tt - T_STARTLE                       # and his light jerks up the wall ...
                    jolt = ease("out", clamp(a / 0.08)) * (1.0 - _smooth(tt, T_STARTLE + 0.16, T_STARTLE + 0.7))
                    lift = 7.0 * math.sin(math.pi * clamp(a / 0.25))
                    x += 9.0 * ease("out", clamp(a / 0.12)) * (1.0 - _smooth(tt, T_STARTLE + 0.3, T_SIGH + 0.4))
                    pose.lean -= 14.0 * jolt
                    pose.head += 12.0 * jolt
                    tgt = (lerp(tgt[0], FLICK_SPOT[0], jolt), lerp(tgt[1], FLICK_SPOT[1], jolt))
                if tt >= T_SIGH:                             # ... and breathes out: the shoulders drop
                    pose.lean += 6.0 * math.sin(math.pi * clamp((tt - T_SIGH) / 0.5)) - 3.0 * clamp((tt - T_SIGH) / 0.3)
                xp = x + st["pelvis"][0] * S
                base = (2.0 * xp - tgt[0], tgt[1])
        _aim("guard", st, pose, x, (base[0], base[1] + lift))
        lit = (xp + sx * (base[0] - xp), base[1])
        return dict(st=st, pose=pose, x=x, sx=sx, lift=lift, target=lit, alpha=alpha, on=on)
    st, pose = d["guard_off"](tt)                             # away on his round
    x = d["guard_off_x"]
    xp = x + st["pelvis"][0] * S
    u = ease("inout", clamp((tt - T_TURN_BACK[0]) / (T_TURN_BACK[1] - T_TURN_BACK[0])))
    sx = -math.cos(math.pi * u)
    aim = (xp + 150.0, -2.0)
    _aim("guard", st, pose, x, aim)
    return dict(st=st, pose=pose, x=x, sx=sx, lift=0.0, target=(xp + sx * 150.0, -2.0), alpha=1.0, on=on)


def _draw_flipped(c, cam, who, st, pose, x, sx, lift, rim, light, eye=True):
    """Draw a figure (facing +x) paper-turned by sx about its pelvis, in set px; returns its joints
    in frame px."""
    xp = x + st["pelvis"][0] * S
    if abs(sx) < 0.03:
        sx = math.copysign(0.03, sx)
    dev = {}
    with cam.on(c):
        c.save()
        c.translate(xp, -lift)
        c.scale(sx, 1.0)
        c.translate(-xp, 0.0)
        j = C.draw(c, who, st, pose, x, 0.0, S, 1, bg=INK, rim=rim, rim_w=RIM_W / cam.zoom,
                   light=(light[0] * math.copysign(1.0, sx), light[1]), eye=eye)
        dev = {kk: c.user_to_device(*v) for kk, v in j.items()}
        c.restore()
    return {kk: c.device_to_user(*v) for kk, v in dev.items()}


def draw_guard(c, cam, g):
    fl = C.hold_flashlight(on=g["on"])
    g["pose"].hold["near"] = fl
    j = _draw_flipped(c, cam, "guard", g["st"], g["pose"], g["x"], g["sx"], g["lift"], None, (0.6, -0.8))
    lens, _ = C.lens_at(c, fl)
    return j, lens


# ============================================================================ the crew
def _x_of(who, t):
    """A crew member's pelvis x (mirrored set px) at t."""
    d = perfs()
    return d[who + "_x"] + d[who](K.twos(t))[0]["pelvis"][0] * S


def crew_rows(t):
    """[(who, st, pose, x, sx, rim_k, inside)] for the crew at t, back to front."""
    tt = K.twos(t)
    d = perfs()
    rows = []
    for who in ("knight", "architect", "cracker"):          # (she steps up in front of him)
        st, pose = d[who](tt)
        x = d[who + "_x"]
        xp = x + st["pelvis"][0] * S
        sx = 1.0
        inside = who != "cracker" and xp >= MOUTH[0] + 7.0
        rim_k = 1.0
        if xp > MOUTH[0]:
            rim_k = lerp(1.0, 0.5 if who != "cracker" else 0.72, _smooth(xp, MOUTH[0], MOUTH[0] + 20.0))
        a, b = T_SLIP[who]
        rim_k *= 1.0 - _smooth(tt, a + 0.1, b)
        if tt < CROSS[who][0] - 0.05:                         # pressed in the dark: a slow breath
            pose.lean += 0.9 * math.sin(2.0 * math.pi * (tt * 0.45 + 0.3 * len(who)))
        if who == "knight":
            pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)
        if who == "cracker":
            if tt >= T_CR_TURN[0]:
                u = _smooth(tt, T_CR_TURN[0], T_CR_TURN[1])
                sx = math.cos(math.pi * u)                   # round to face the way they came
            if tt >= a:
                sx = -math.cos(math.pi * _smooth(tt, a, a + 0.25))   # and back, to follow them
            bend = _smooth(tt, T_BREATH, T_BREATH + 0.3) * (1.0 - _smooth(tt, T_STRAIGHT[0], T_STRAIGHT[1]))
            pant = 1.4 * math.sin(2.0 * math.pi * 1.7 * tt) * (1.0 - _smooth(tt, T_CLANK - 0.1, T_CLANK + 0.05))
            pose.lean += 7.0 * bend + pant * bend
            pose.head -= 18.0 * bend
            if bend > 0.0:                                   # hands on his knees
                pose.arms["near"] = ("ang", lerp(pose.arms["near"][1], -22.0, bend), lerp(pose.arms["near"][2], 34.0, bend))
                pose.arms["far"] = ("ang", lerp(pose.arms["far"][1], -12.0, bend), lerp(pose.arms["far"][2], 30.0, bend))
        rows.append((who, st, pose, x, sx, rim_k, inside))
    # the deepest in the mouth first; then whoever is out front
    rows.sort(key=lambda r: (not r[6], -(r[3] + r[1]["pelvis"][0] * S) if r[6] else 0.0))
    return rows


def _swing(t):
    """The chest-piece's swing (degrees from hanging, + forward): he bends, it swings out on into
    the pipe (T_CLANK), bounces back and settles."""
    if t < T_BREATH:
        return 0.0
    if t < T_CLANK:
        return 34.0 * ease("in", (t - T_BREATH) / (T_CLANK - T_BREATH))
    kk = t - T_CLANK
    return 34.0 * math.exp(-3.2 * kk) * math.cos(9.0 * kk)


def _stethoscope(c, cam, j, t, facing, rim):
    """Round the Cracker's neck (j: his joints, frame px): the chest-piece swinging on its tube; it
    cannot pass the pipe. Returns the chest-piece (set px)."""
    head, sh = cam.to_set(j["head"]), cam.to_set(j["shoulder_near"])
    neck = (lerp(head[0], sh[0], 0.55) + 2.5 * facing, lerp(head[1], sh[1], 0.7))
    L = 30.0
    a = math.radians(_swing(t)) * facing
    piece = (neck[0] + L * math.sin(a), neck[1] + L * math.cos(a))
    if facing < 0 and piece[0] < PIPE_FACE + 2.5:
        piece = (PIPE_FACE + 2.5, piece[1])
    with cam.on(c):
        Bk.stethoscope(c, (neck[0] - 4.0 * facing, neck[1] - 3.0), piece, 0.42, INK, rim=lerp(INK, rim, 0.75))
    return piece


def draw_crew(c, cam, t, rows, inside):
    out = {}
    for who, st, pose, x, sx, rim_k, ins in rows:
        if ins != inside or rim_k <= 0.01 and (t >= T_SLIP[who][1]):
            continue
        rim = lerp(INK, C.RIM[who], rim_k)
        c.save()
        if ins:
            with cam.on(c):
                c.new_path()
                c.rectangle(MOUTH[0] + 1.0, -Bk.MOUTH_H, MOUTH[1] - MOUTH[0] - 2.0, Bk.MOUTH_H + 6.0)
            c.clip()
        eye = who != "architect" or t >= CROSS["architect"][0] - 0.05
        j = _draw_flipped(c, cam, who, st, pose, x, sx, 0.0, rim, (-0.6, -0.8), eye=eye and rim_k > 0.6)
        if who == "cracker":
            out["piece"] = _stethoscope(c, cam, j, t, 1 if sx >= 0 else -1, rim)
        c.restore()
        out[who] = j
    return out


def her_eyes(c, cam, t, j):
    """Her two PAPER eyes in the dark (she looks out of it), with a blink."""
    if t >= CROSS["architect"][0] - 0.05 or "architect" not in j:
        return
    hx, hy = j["architect"]["head"]
    z = cam.zoom
    lid = 0.2 if (3.42 <= t < 3.5 or 4.46 <= t < 4.54) else 1.0
    for dx in (-2.2, 2.2):
        p = (hx + (dx + 1.4) * z, hy - 0.6 * z)
        bass.fill_polys(c, [bass.orient([(p[0] + 0.85 * z * math.cos(2 * math.pi * i / 12.0),
                                          p[1] + 0.85 * z * lid * math.sin(2 * math.pi * i / 12.0)) for i in range(12)],
                                        True)], PAPER)


# ============================================================================ the cat and the can (mirrored)
def cat_at(t):
    """(p, facing, mode, eyes) of the cat, or None once it has gone."""
    if t < T_EYES:
        return CAT_SEAT, 1, "sit", 0.12
    if t < T_ARCH:
        return CAT_SEAT, 1, "sit", min(1.0, 0.12 + (t - T_EYES) / 0.08)
    if t < T_LEAP[0]:
        return CAT_SEAT, 1, "arch", 1.0
    if t < T_LEAP[1]:
        u = (t - T_LEAP[0]) / (T_LEAP[1] - T_LEAP[0])
        p0, p1 = CAT_SEAT, (780.0, 0.0)
        return (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - 40.0 * math.sin(math.pi * u)), 1, "walk", 1.0
    x = 780.0 + 300.0 * (t - T_LEAP[1])
    if x > 960.0:
        return None
    return (x, 0.0), 1, "walk", 1.0


def can_at(t):
    """(X, y, angle) of the tin can, or None while it stands on its crate."""
    x0, y0 = CAN_REST
    if t < T_TIP[0]:
        return None
    if t < T_TIP[1]:
        u = ease("in", (t - T_TIP[0]) / (T_TIP[1] - T_TIP[0]))
        return (x0 + 4.0 * u, y0 + 2.0 * u, 90.0 * u)
    if t < T_CLATTER:
        u = (t - T_TIP[1]) / (T_CLATTER - T_TIP[1])
        return (lerp(x0 + 4.0, TOP_EDGE + 14.0, u), lerp(y0 + 2.0, -CAN_FLOOR, u * u), 90.0 + 160.0 * u)
    kk = t - T_CLATTER
    hop = 9.0 * max(0.0, math.sin(math.pi * clamp(kk / 0.16))) * (1.0 if kk < 0.16 else 0.0)
    roll = 38.0 * (1.0 - math.exp(-2.2 * kk))
    return (TOP_EDGE + 14.0 + roll, -CAN_FLOOR - hop, 250.0 + math.degrees(roll / 7.0))


# ============================================================================ light
def _patch(c, p, alpha, scale=1.0):
    for f, a in ((1.0, 0.10), (0.72, 0.10), (0.45, 0.12)):
        Bk.ellipse(c, p, PATCH[0] * f * scale, PATCH[1] * f * scale, PAPER, a * alpha)


def _dark(c, cam):
    """The hall at night: INK laid over it in cut steps beyond the desk lamp (no blur), so that
    away from the lamp it is black on black."""
    p = cam.to_frame(LAMP)
    for i, (r, a) in enumerate(DARK):
        bass.hole(c, p, r * cam.zoom, INK, seed=70 + i, rect=(-20.0, -20.0, W + 20.0, K.H + 20.0), n=96, alpha=a)


def _on_wall(c, cam, g):
    """The patch on the far wall (after the dark): not in the mouth."""
    tgt, a = g["target"], g["alpha"] * (1.0 if g["on"] else 0.0)
    if a <= 0.0 or tgt[1] > -24.0:
        return
    with cam.on(c):
        c.save()
        x0, x1 = Bk.CORR_X
        c.new_path()
        c.rectangle(x0, -Bk.CORR_H, x1 - x0, Bk.CORR_H)
        c.rectangle(MOUTH[1], -Bk.MOUTH_H, MOUTH[0] - MOUTH[1], Bk.MOUTH_H)
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.clip()
        c.set_fill_rule(cairo.FILL_RULE_WINDING)
        _patch(c, tgt, a)
        c.restore()


def _front_light(c, cam, g):
    """His light on what stands in front of the wall (the desk top, the crates), or on the floor."""
    tgt, a = g["target"], g["alpha"] * (1.0 if g["on"] else 0.0)
    if a <= 0.0:
        return
    with cam.on(c):
        if tgt[1] > -24.0:
            for f, al in ((1.0, 0.12), (0.6, 0.14)):
                Bk.ellipse(c, (tgt[0], -1.0), 64.0 * f, 7.0 * f, PAPER, al * a)
            return
        c.save()
        c.new_path()
        c.rectangle(DESK[0], -82.0, DESK[1] - DESK[0], 26.0)
        for x0, y0, x1, y1 in CRATES:
            c.rectangle(x0, y1, x1 - x0, y0 - y1)
        c.clip()
        _patch(c, tgt, a, 1.3)
        c.restore()


def _hall_clip(c, cam):
    """Clip to the hall's open air (frame px), less the mouth: the beam does not go down it."""
    x0, y0 = cam.to_frame((Bk.CORR_X[0], -Bk.CORR_H))
    x1, y1 = cam.to_frame((Bk.CORR_X[1], 0.0))
    m0, my = cam.to_frame((MOUTH[0], -Bk.MOUTH_H))
    m1, _ = cam.to_frame((MOUTH[1], 0.0))
    c.new_path()
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    c.rectangle(m1, my, m0 - m1, y1 - my)
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    c.clip()
    c.set_fill_rule(cairo.FILL_RULE_WINDING)


def draw_beam(c, cam, t, lens, g):
    """The beam: flat translucent sectors from the lens to where it lands (frame px); swung round
    toward us it shortens and the lens flares."""
    if lens is None or not g["on"]:
        return
    on = clamp((t - T_CLICK) / 0.06)
    tgt = cam.to_frame(g["target"])
    dd = math.dist(lens, tgt)
    toward = 1.0 - g["alpha"] if g["target"][1] > PATCH_Y + 4.0 and t < T_DESK[1] else 0.0
    if dd > 4.0:
        spread = clamp(math.degrees(math.atan2(PATCH[1] * cam.zoom, dd)), 4.0, 16.0)
        c.save()
        _hall_clip(c, cam)
        K.cone(c, lens, math.degrees(math.atan2(tgt[1] - lens[1], tgt[0] - lens[0])), spread,
               dd * 1.02 * (1.0 - 0.55 * toward), PAPER, alpha=0.12 * on * (1.0 - 0.6 * toward), steps=3)
        c.restore()
    K.dot(c, lens, 2.6 * cam.zoom * 0.5, PAPER, seed=5, alpha=0.9 * on)
    if toward > 0.05:
        bass.fill_polys(c, [bass.ring_pts(lens, 9.0 * cam.zoom * toward, seed=6, n=40)], PAPER, 0.18 * toward)


def _wave(c, cam, p, t, t0, n=3, every=0.12, life=0.9, r1=380.0, width=9.0, color=PAPER, seed=0, alpha=1.0):
    """A sound's ring in the world: radius in set px (so it carries across a cut at another zoom)."""
    f = cam.to_frame(p)
    for i in range(n):
        a = (t - t0 - i * every) / life
        if not 0.0 <= a < 1.0:
            continue
        r = lerp(2.0, r1, ease("out3", a)) * cam.zoom
        w = width * (1.0 - a) + 1.0
        bass.ring(c, f, r, w, color, seed=seed + 7 * i, n=int(clamp(2.0 * math.pi * r / 14.0, 48, 420)),
                  alpha=alpha * (1.0 - 0.5 * a))


# ============================================================================ the callout: the cat's eyes
def _lens_inside(t):
    def fn(c):
        K.fill(c, INK)
        cx, cy = LENS_C
        K.pool(c, (cx + 30.0, cy + 10.0), 210.0, 170.0, PAPER, alpha=0.10, add=False)      # his light on it
        mode = "arch" if t >= T_ARCH else "sit"
        eyes = min(1.0, 0.12 + (t - T_EYES) / 0.08) if t >= T_EYES else 0.12
        if mode == "arch":
            eyes *= 0.8
        s = 3.4
        head = (10.0, -78.0) if mode == "sit" else (50.0, -72.0)
        p = (cx - head[0] * s, cy - head[1] * s + (36.0 if mode == "sit" else 60.0))
        C.cat(c, p, s=s, t=t, facing=1, mode=mode, eyes=eyes, rim=lerp(INK, STEEL, 0.65), seed=3)
    return fn


# ============================================================================ render
def _set_cam(cam):
    """The set's own camera for this scene's (mirrored) one."""
    return Bk.Cam(W - cam.x, cam.y, cam.zoom)


def render(f, t, T):
    K.scene_setup(f, INK)
    with f.screen() as c:
        draw(c, t)


def draw(c, t):
    cam = cam_at(t)
    g = guard_at(t)
    can = can_at(t)
    # the hall, mirrored
    c.save()
    c.translate(W, 0.0)
    c.scale(-1.0, 1.0)
    Bk.corridor(c, _set_cam(cam), t, lamp=1.0, can=None if can is None else (W - can[0], can[1], -can[2]))
    c.restore()
    _dark(c, cam)
    with cam.on(c):                                          # the pipe by the mouth catches a little light
        bass.fill_polys(c, [bass.cut_rect(PIPE_FACE - 1.8, Bk.PIPE_Y[0] + 4.0, PIPE_FACE - 0.4, -3.0, seed=71, amp=0.1)],
                        lerp(STEEL, PAPER, 0.25), 0.55)
    _on_wall(c, cam, g)
    _front_light(c, cam, g)
    sh = shot(t)
    if sh == "the mouth: the push to the dial":
        _her_light(c, cam, t)
    ct = cat_at(t)
    if ct is not None:
        p, fc, mode, eyes = ct
        with cam.on(c):
            C.cat(c, p, 0.27, t, facing=fc, mode=mode, eyes=eyes, rim=lerp(INK, STEEL, 0.6))
    rows = crew_rows(t)
    j = draw_crew(c, cam, t, rows, True)
    gj, lens = draw_guard(c, cam, g)
    j.update(draw_crew(c, cam, t, rows, False))
    draw_beam(c, cam, t, lens, g)
    her_eyes(c, cam, t, j)
    # the Cracker's heart while they cross (on the beat)
    hb = _smooth(t, 5.9, 6.3) * (1.0 - _smooth(t, 8.9, 9.4))
    if hb > 0.0 and "cracker" in j:
        cj = j["cracker"]
        chest = (lerp(cj["pelvis"][0], cj["head"][0], 0.6), lerp(cj["pelvis"][1], cj["head"][1], 0.6))
        K.heartbeat(c, chest, t, color=AMBER, bpm=120.0, r0=10.0, r1=34.0 * cam.zoom, width=7.0, life=0.85,
                    seed=55, alpha=0.85 * hb)
    # the click; the clank and its ring (it carries to him); the clatter
    if T_CLICK <= t < T_CLICK + 0.5 and lens is not None:
        K.ripple(c, lens, t, T_CLICK, PAPER, n=2, every=0.12, life=0.4, r0=6.0, r1=12.0 * cam.zoom, width=3.5,
                 seed=50, alpha=0.8)
    if T_CLANK <= t < T_CLANK + 1.4:
        _wave(c, cam, (PIPE_FACE, -98.0), t, T_CLANK, r1=380.0, seed=51)
    if T_CLATTER <= t < T_CLATTER + 0.9:
        cp = can_at(T_CLATTER)
        _wave(c, cam, (cp[0], -4.0), t, T_CLATTER, n=2, every=0.15, life=0.6, r1=46.0, width=6.0, seed=52,
              alpha=0.85)
    # his look: to the noise, onto the crates, down after the cat
    if T_AIM[0] <= t < T_LEAP[0] + 0.6 and "head" in gj:
        tgt = cam.to_frame(g["target"])
        eye = (gj["head"][0] + 4.0 * cam.zoom * (1 if g["sx"] >= 0 else -1), gj["head"][1] - 1.0 * cam.zoom)
        dd = math.dist(eye, tgt)
        if dd > 1.0:                                         # (it stops short of what it sees)
            tgt = (tgt[0] + (eye[0] - tgt[0]) * 8.0 * cam.zoom / dd, tgt[1] + (eye[1] - tgt[1]) * 8.0 * cam.zoom / dd)
        K.sight_line(c, eye, tgt, t, T_AIM[0], color=PAPER, dur=0.5, off=T_LEAP[0] + 0.28, off_dur=0.2, r=5.0,
                     gap=20.0, head=22.0, seed=57)
    # the callout: two AMBER eyes in the dark
    if T_EYES <= t < T_LEAP[0]:
        u = clamp((t - T_EYES) / 0.25) * (1.0 - clamp((t - (T_LEAP[0] - 0.12)) / 0.12))
        anchor = cam.to_frame((CRATE_SPOT[0] - 1.0, CRATE_SPOT[1] - 12.0))      # just over its head
        K.callout(c, anchor, LENS_C, LENS_R, _lens_inside(t), u=u, color=PAPER, ring_w=9.0, dot_r=8.0, line_w=4.0,
                  seed=58)


def _her_light(c, cam, t):
    """Her small light on the far door at the dial (17.0): the door's face shows in its pool."""
    if t < T_HER_LIGHT:
        return
    u = ease("outback", clamp((t - T_HER_LIGHT) / 0.18))
    r = 30.0 * u                                            # (inside the mouth's edges; s06 opens on it)
    with cam.on(c):
        c.save()
        c.new_path()
        c.rectangle(MOUTH[0] + 2.0, -Bk.MOUTH_H + 2.0, MOUTH[1] - MOUTH[0] - 4.0, Bk.MOUTH_H - 2.0)
        c.clip()
        c.new_path()
        bass.iris_path(c, (DIAL[0] + 2.0, DIAL[1] + 4.0), max(0.5, r), seed=61, n=72)
        c.clip()
        Bk.door_face(c, t, face=lerp(STEEL, INK, 0.45))
        c.restore()
        K.pool(c, (DIAL[0] + 2.0, DIAL[1] + 4.0), r * 1.15, r * 1.15, PAPER, alpha=0.16, steps=4)


# ============================================================================ cues
def _pan(t, p):
    fx = cam_at(t).to_frame(p)[0]
    return round(clamp((fx - 540.0) / 540.0, -1.0, 1.0) * 0.8, 3)


def cues(T):
    d = perfs()
    out = [Cue(0.0, "hall_tone", gain_db=-26, dur=9.5,
               desc="the hall at night: room tone, a far hum of the building; the beat's tick underneath"),
           Cue(T_CLICK, "flashlight_click", gain_db=-14, pan=_pan(T_CLICK, (GUARD_X, -90.0)),
               dc="a flashlight clicks on (a small metal switch)"),
           Cue(1.0, "belt_creak", gain_db=-30, pan=_pan(1.0, (GUARD_X, -90.0)), dur=6.5,
               dc="the faint creak of the guard's leather belt as his light swings (it repeats softly)"),
           Cue(2.9, "held_breath", gain_db=-24, pan=_pan(2.9, (FILE["architect"], -100.0)),
               dc="a breath held in the doorway: his light's patch slides up to its edge")]
    # the scurries: a soft step and a tiptoe pizzicato note on each footfall
    note = {"architect": "her high D", "knight": "his low C#", "cracker": "a middle note"}
    for who in WHO:
        a, b = CROSS[who]
        ups = [T_UP[who]] if who in T_UP else []
        for t0, t1 in ups + [(a, b)]:
            for tf, side, fx in Bk.footfalls(d[who], t0, t1 + 0.1):
                out.append(Cue(tf, "crew_step", gain_db=-27, pan=_pan(tf, (d[who + "_x"] + fx * S, 0.0)),
                               dc="a soft step on stone: one of the crew slips into the dark corridor"))
                if (t0, t1) == (a, b):
                    out.append(Cue(tf, "tiptoe_pizz", gain_db=-18, pan=_pan(tf, (d[who + "_x"] + fx * S, 0.0)),
                                   desc=f"a tiptoe pizzicato: one plucked string note per scurrying step ({note[who]})"))
    out += [Cue(5.9, "heartbeat", gain_db=-14, dur=3.4, pan=_pan(7.5, (IN["cracker"], -100.0)),
                desc="the Cracker's heartbeat, close: lub-dub on the beat (120 bpm), rising, then easing"),
            Cue(T_DESK[0], "coat_rustle", gain_db=-24, pan=_pan(T_DESK[0], (GUARD_X, -90.0)),
                dc="a coat rustles: the guard turns away"),
            Cue(T_BREATH, "wheeze", gain_db=-20, pan=_pan(T_BREATH, (IN["cracker"], -100.0)),
                dc="an old man's wheezing breath, held in"),
            Cue(T_CLANK, "steth_clank", gain_db=-6, pan=_pan(T_CLANK, (PIPE_X, -98.0)),
                dc="CLANK: the stethoscope's steel chest-piece swings into an iron pipe (it rings down the pipe)"),
            Cue(T_SPIN[0], "coat_swish", gain_db=-15, pan=_pan(T_SPIN[0] + 0.01, (GUARD_X, -90.0)),
                dc="a heavy coat swishes: the guard spins round"),
            Cue(T_EYES - 0.05, "held_note", gain_db=-20,
                desc="the score's held breath: one low tremolo string note under the two eyes"),
            Cue(T_ARCH, "cat_hiss", gain_db=-14, pan=_pan(T_ARCH, CAT_SEAT), dc="a cat's hiss"),
            Cue(T_LEAP[0], "cat_claws", gain_db=-17, pan=_pan(T_LEAP[0], CAT_SEAT),
                dc="claws scrabble on wood: the cat leaps off the crates"),
            Cue(T_TIP[0], "can_tink", gain_db=-18, pan=_pan(T_TIP[0], CAN_REST),
                dc="tink: the tin can tips over on the crate"),
            Cue(T_STARTLE, "guard_yelp", gain_db=-14, pan=_pan(T_STARTLE, (GUARD_X, -90.0)),
                dc="the guard yelps and stumbles back as the cat streaks between his feet (a scuff, a gasp)"),
            Cue(T_CLATTER, "can_clatter", gain_db=-8, pan=_pan(T_CLATTER, (TOP_EDGE + 14.0, 0.0)), dur=0.9,
                dc="CLATTER: the tin can hits the stone floor, bounces and rolls"),
            Cue(T_SIGH, "guard_sigh", gain_db=-16, pan=_pan(T_SIGH, (GUARD_X, -90.0)),
                dc="the guard breathes out: a relieved sigh, half a laugh"),
            Cue(T_TURN_BACK[0], "coat_rustle", gain_db=-22, pan=_pan(T_TURN_BACK[0], (GUARD_X, -90.0)),
                dc="a coat rustles: the guard turns away"),
            Cue(T_TURN_MID, "heel_scuff", gain_db=-24, pan=_pan(T_TURN_MID, (GUARD_X, -90.0)),
                dc="a heel scuffs on stone: the guard pivots away")]
    for tf, side, fx in Bk.footfalls(d["guard_off"], T_TURN_MID, T_PUSH[0] + 0.6):
        out.append(Cue(tf, "guard_step", gain_db=-22, pan=_pan(min(tf, 15.49), (d["guard_off_x"] + fx * S, 0.0)),
                       dc="footstep: the guard walks off down the corridor (going away)"))
    for who, (a, b) in T_SLIP.items():
        out.append(Cue(a + 0.1, "crew_step", gain_db=-28, pan=_pan(a + 0.1, (IN[who], 0.0)),
                       dc="a soft step on stone: one of the crew slips into the dark corridor"))
    out += [Cue(T_PUSH[0], "push_whoosh", gain_db=-20, dur=T_PUSH[1] - T_PUSH[0],
                dc="a low rising whoosh: the camera pushes down the black corridor"),
            Cue(T_HER_LIGHT, "flashlight_click", gain_db=-18, pan=0.0,
                desc="her small light clicks on at the dial (the flashlight's switch, softer, close)")]
    return sorted(out, key=lambda q: q["t"])
