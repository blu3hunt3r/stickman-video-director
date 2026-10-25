"""s04 NIGHT (48-62). The dark street; the manhole; the Vertigo shaft; the section: the sewer, the
hatch, up into the hall. OPPOSITE's grammar on DOUBLE CROSS v5's staging.

  The elevation (0-3): the crew's window is dark now and the bank's clock reads 11:59; the guard's
    light moves behind the barred windows. The tenement's street door opens without a light and
    three shapes slip out, the Knight first, then she, then the Cracker, and cross to manhole A,
    footstep dots behind them, each on its own track under the street (RED, PAPER, AMBER). The
    Knight crouches and hooks the lid (2.6) and heaves it up on edge (2.75, the scrape starts).
    The camera glides in on them.
  The low angle (3-5): up from the road, the bank's front leaning back into the night behind them.
    The Knight drags the lid aside and lets it fall flat (3.25, CLANK). They go down one a beat,
    hands on the rim: the Knight (3.5), she (4.0), the Cracker (4.5). The bank's clock reaches
    12:00 on the bar line (4.0, one deep chime: a ripple off its face).
  The shaft (5-7): straight down the manhole from above. The iron rungs recede in a spiral and the
    shaft stretches (the dolly zoom: the rim holds, the depths fall away and turn) while three rims
    sink into the dark and land in the water far below, one a beat (5.5, 6.0, 6.5); drips.
  The section (7-14), dark but for the guard's lamp and the gold. Their dots go right along the
    sewer, each on its own track in the water, under the bank's street wall, to the hatch; the
    Knight climbs its shaft. 9.5-11.0, a callout lens: his hand pushes the hatch up a crack (9.75,
    creak) and the hall's lamplight slices in. He lifts it open (10.9) and they climb up into the
    hall's dark corner, one a beat (11.5, 12.0, 12.5), behind the guard's back while his PAPER cone
    sweeps the far end of the hall. The Cracker lets the hatch down (12.75); they back into the
    corner; the guard clicks his light off (13.5: s05 opens on it dark and clicks it on at 0.5).
    Hold on them, pressed in the dark.
"""
import math
from functools import lru_cache

import cairo

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import faces as F
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import street as St

k = K.k
W, H = K.W, K.H
INK, PAPER, AMBER, RED = K.INK, K.PAPER, K.AMBER, K.RED
NIGHT, STEEL, DEEP = K.NIGHT, K.STEEL, K.DEEP

# ---------------------------------------------------------------------------- beats (scene time)
FILM_T0 = 48.0
SHOTS = ((0.0, "the elevation"), (3.0, "low angle from the road"), (5.0, "the Vertigo shaft"), (7.0, "the section"))
T_LOW, T_SHAFT, T_SECTION = 3.0, 5.0, 7.0
T_DOOR = (0.1, 0.45)            # the tenement's street door opens, no light
OUT = {"knight": 0.35, "architect": 0.8, "cracker": 1.25}     # each slips out of the door
T_DOOR_SHUT = (2.0, 2.4)        # it swings to behind the Cracker
T_BEND = 2.3                    # the Knight crouches at the lid ...
T_HOOK = 2.55                   # ... and hooks its edge (iron tick, a low grunt)
T_LIFT = 2.75                   # he heaves it up on edge and drags it out of the hole (the scrape) ...
T_DROP = 3.15                   # ... lets go ...
T_CLANK = 3.25                  # ... CLANK: it falls flat on the road
T_CHIME = 4.0                   # the bank's clock reaches 12:00 (one deep chime), on the bar line
DOWN = {"knight": 3.5, "architect": 4.0, "cracker": 4.5}      # they go down one a beat
STEP_IN = 0.3                   # s to step in over the hole
CLIMB = 2.0                     # s from the road to the water
LAND = {w: t + CLIMB for w, t in DOWN.items()}                 # each lands in the water: 5.5, 6.0, 6.5
T_STRETCH = (5.0, 7.0)          # the shaft stretches (the dolly zoom)
WADE = {"knight": (5.7, 8.4), "architect": (6.2, 9.0), "cracker": (6.7, 10.4)}   # east along the sewer
T_UP_SHAFT = {"knight": (8.45, 9.55), "architect": (9.6, 10.5), "cracker": (10.45, 11.0)}   # onto the hatch's rungs
T_LENS = (9.5, 11.0)            # the callout: the Knight's hand on the hatch
T_CRACK = 9.75                  # he pushes it up a crack (creak): the lamplight slices in
T_OPEN = (10.9, 11.2)           # he lifts it open
UP = {"knight": 11.5, "architect": 12.0, "cracker": 12.5}     # each comes up into the hall, one a beat
RISE = {"knight": 0.7, "architect": 0.85, "cracker": 0.9}      # s to climb from the rungs to the floor
T_LID_DOWN = (12.65, 12.8, 12.95)  # the Cracker, up in the corner, guides the lid over, lets go: it drops shut
T_THUD = 12.95                  # (a soft thud)
T_PRESS = 13.0                  # they press back into the dark as the light swings near
T_LIGHT_OFF = 13.6              # the guard clicks his light off

# ---------------------------------------------------------------------------- places
WHO = ("knight", "architect", "cracker")
NAME = {"knight": "the Knight", "architect": "she", "cracker": "the Cracker"}
TRACK_COL = {"knight": RED, "architect": PAPER, "cracker": AMBER}
# the elevation (section px): where each stops at manhole A, and the tracks of their dots
E_STOP = {"knight": 401.0, "architect": 346.0, "cracker": 298.0}
E_DOOR_X = 0.5 * (St.TEN_DOOR_E[0] + St.TEN_DOOR_E[2])
TRACK_Y = {"knight": St.GROUND + 30.0, "architect": St.GROUND + 45.0, "cracker": St.GROUND + 60.0}
E_CAM = (((560.0, 820.0), 1.25), ((402.0, 1136.0), 2.8))
# the low angle (Bk set px, the face-on bank front): the crew round manhole A
L_STOP = {"knight": 155.0, "architect": 304.0, "cracker": 372.0}
L_FACING = {"knight": 1, "architect": -1, "cracker": -1}
SHAFT_X = Bk.MANHOLE_X
NEAR = Bk.Cam(272.0, -174.0, 3.9)           # the crew at the hole, close (the road at frame y 1640)
FAR = Bk.Cam(520.0, -467.0, 1.22)           # the bank's front behind them (its road line at frame y 1530)
KEY_A = 3.4e-4                              # the keystone: the front narrows by this per frame px of height
KEY_CX = 560.0                              # ... toward this vertical
# the section (section px)
SEWER_TRACK = {"knight": St.WATER + 6.0, "architect": St.WATER + 12.5, "cracker": St.WATER + 19.0}
LADDER_X = St.HATCH_C - 7.0                  # a climber's pelvis on the hatch's rungs
WADE_FROM = {"knight": St.MH_A + 8.0, "architect": St.MH_A + 2.0, "cracker": St.MH_A - 4.0}
WADE_TO = {"knight": LADDER_X, "architect": St.HATCH_C - 46.0, "cracker": LADDER_X - 4.0}
H_TOP = {"knight": 172.0, "architect": 60.0, "cracker": 10.0}   # how high each waits on the hatch's rungs
H_FLOOR = St.WATER - St.FEET                                     # feet on the hall's floor
HALL_X = {"knight": 732.0, "architect": 704.0, "cracker": 650.0}  # the Knight and she step off east of the
HALL_WALK = {"knight": 0.75, "architect": 0.6, "cracker": 0.0}     # hatch; the Cracker climbs out into the corner
GUARD_X = 836.0                              # the guard by the crates, facing the hall, his light on the floor
LID_LEN = St.HATCH[1] - St.HATCH[0] + 4.0    # the hatch's lid (street.py's), hinged at HATCH[0] - 2
SWEEP_PHASE = 62.0                           # film time of the sweep's zero (s05 shares the clock)
HALL_R = (St.HALL[0], St.bank_level(2) + St.SLAB / 2, St.HALL[1], St.FEET)
SEC_KEYS = ((7.0, (520.0, 1600.0, 3.2), None),
            (8.5, (612.0, 1596.0, 3.2), "inout"),
            (9.35, (690.0, 1500.0, 2.7), "inout"),
            (11.05, (690.0, 1500.0, 2.7), None),
            (12.0, (744.0, 1338.0, 2.7), "inout"),
            (12.9, (744.0, 1338.0, 2.7), None),
            (14.0, (702.0, 1332.0, 3.35), "inout"))
LENS_C = (590.0, 1240.0)                     # the callout lens (section px, rides the camera)
LENS_R = 84.0
# the shaft from above (frame px)
V_C = (540.0, 900.0)                         # the vanishing point
V_R = 470.0                                  # the manhole's rim
V_RINGS = 24


def motion_blur(t, T):
    return 1


def _seg(name, s0, s1, at, speed=1.0, **kw):
    return C.Seg(C.clip(name), s0, s1, at=at, speed=speed, **kw)


def _pan(x):
    return round(clamp((x - 540.0) / 540.0, -1.0, 1.0) * 0.8, 3)


def _hatch_u(ang):
    """street.draw_section's hatch value for a lid raised `ang` degrees: its curve overshoots, so
    invert its rising branch (monotone, 0 .. 104 degrees for u 0 .. ~0.4)."""
    if ang <= 0.05:
        return 0.0
    if ang >= 103.9:
        return 1.0
    lo, hi = 0.0, 0.4
    for _ in range(30):
        m = 0.5 * (lo + hi)
        if 104.0 * ease("outback", m) < ang:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


# ============================================================================ performances
def _fit(who, segs, facing, t0, t1, x0, x1, s=St.FIG_S):
    """A performance whose root travels from x0 at t0 to x1 at t1 (the walking segment's travel
    scaled to fit), and the x to draw it from."""
    p = C.perf(who, segs, facing=facing)
    a, b = p(t0)[0]["pelvis"][0], p(t1)[0]["pelvis"][0]
    if abs(b - a) > 1e-6:
        g = (x1 - x0) / ((b - a) * s)
        segs = [C.Seg(sg.clip, sg.src0, sg.src1, at=sg.at, speed=sg.speed, blend=sg.blend,
                      travel=sg.travel * (g if sg.travel > 0.0 else 1.0), lean=sg.lean) for sg in segs]
        p = C.perf(who, segs, facing=facing)
    return p, x1 - p(t1)[0]["pelvis"][0] * s


@lru_cache(maxsize=None)
def perfs():
    d = {}
    # the elevation: out of the door and across, facing east; each holds at the end
    # the Knight: out and across (a heavy walk, quick), a crouch at the lid (26_10's knees-bent
    # bend, held: not its deep stoop), the heave up from the crouch with the lid
    walk_k = (T_BEND - OUT["knight"]) * 1.5
    d["knight_e"] = C.perf("knight", [_seg("17_08", 1.5, 1.5 + walk_k, OUT["knight"], 1.5),
                                      _seg("26_10", 0.6, 1.3, T_BEND, 2.8, blend=0.15),
                                      _seg("26_10", 1.3, 1.34, T_BEND + 0.25, 0.1, blend=0.05),
                                      _seg("26_10", 3.1, 3.8, T_LIFT - 0.05, 1.5, blend=0.15)], facing=1)
    d["architect_e"] = C.perf("architect", [_seg("104_02", 1.0, 2.4, OUT["architect"], 1.05),
                                            _seg("104_02", 5.7, 7.3, OUT["architect"] + 1.3, 0.3, travel=0.0,
                                                 blend=0.35)], facing=1)
    d["cracker_e"] = C.perf("cracker", [_seg("77_14", 1.5, 2.5, OUT["cracker"], 0.83),
                                        _seg("104_02", 5.7, 7.3, OUT["cracker"] + 1.2, 0.3, travel=0.0, blend=0.4,
                                             lean=14.0)], facing=1)
    stops = {"knight": T_BEND, "architect": OUT["architect"] + 1.3, "cracker": OUT["cracker"] + 1.2}
    for who, t_end in stops.items():
        d[who + "_ex"] = E_STOP[who] - d[who + "_e"](t_end)[0]["pelvis"][0] * St.FIG_S
        d[who + "_eend"] = t_end
    # the low angle: she and the Cracker wait at the far rim, turned to the hole
    d["architect_l"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 0.0, 0.3, travel=0.0)], facing=-1)
    d["cracker_l"] = C.perf("cracker", [_seg("104_02", 5.7, 7.3, 0.0, 0.3, travel=0.0, lean=14.0)], facing=-1)
    # the sewer: east through the water to the hatch
    wade = {"knight": [_seg("17_08", 5.7, 6.0, 0.0, 0.2, travel=0.0),
                       _seg("17_08", 1.5, 5.3, WADE["knight"][0], 1.4, blend=0.3)],
            "architect": [_seg("104_02", 5.7, 5.9, 0.0, 0.2, travel=0.0),
                          _seg("104_02", 1.0, 3.9, WADE["architect"][0], 1.04, blend=0.3)],
            "cracker": [_seg("104_02", 5.7, 5.9, 0.0, 0.2, travel=0.0, lean=10.0),
                        _seg("104_02", 1.0, 3.8, WADE["cracker"][0], 0.76, blend=0.3, lean=10.0)]}
    for who in WHO:
        t0, t1 = WADE[who]
        d[who + "_s"], d[who + "_sx"] = _fit(who, wade[who], 1, t0, t1, WADE_FROM[who], WADE_TO[who])
    # in the hall: a few steps off the hatch into file, then standing, pressed in the dark
    hall = {"knight": [_seg("17_08", 1.5, 1.5 + HALL_WALK["knight"] * 1.4, UP["knight"], 1.4),
                       _seg("17_08", 5.7, 6.0, UP["knight"] + HALL_WALK["knight"], 0.03, travel=0.0, blend=0.25)],
            "architect": [_seg("104_02", 1.0, 1.0 + HALL_WALK["architect"], UP["architect"], 1.0),
                          _seg("104_02", 5.7, 7.3, UP["architect"] + HALL_WALK["architect"], 0.12, travel=0.0,
                               blend=0.3, lean=-3.0)],
            "cracker": [_seg("104_02", 5.7, 7.3, UP["cracker"], 0.12, travel=0.0, lean=12.0)]}
    for who in WHO:
        t0 = UP[who]
        d[who + "_h"], d[who + "_hx"] = _fit(who, hall[who], 1, t0, t0 + HALL_WALK[who], LADDER_X, HALL_X[who])
    # the guard by the crates, facing the hall, wary
    d["guard"] = C.perf("guard", [_seg("77_05", 0.4, 4.2, 6.5, 0.55, travel=0.0)], facing=-1)
    return d


def _dry(who, st, pose, x, floor_y, facing, s=St.FIG_S):
    """A figure's joints without drawing it (px of whatever space x, floor_y are in)."""
    surf = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    return C.draw(cairo.Context(surf), who, st, pose, x, floor_y, s, facing, rim=False)


def _aim(who, st, pose, x, floor_y, facing, target, s=St.FIG_S):
    """Point the near arm straight at target (the flashlight along it)."""
    S = _dry(who, st, pose, x, floor_y, facing, s)["shoulder_near"]
    a1 = math.degrees(math.atan2(facing * (target[0] - S[0]), target[1] - S[1]))
    pose.arms["near"] = ("ang", a1 - pose.lean, 0.0)


def _ik(pose, side, p, x, floor_y, s):
    pose.arms[side] = ("ik", ((p[0] - x) / s, (p[1] - floor_y) / s))


def _sack(pose):
    pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)


# ============================================================================ the elevation (0-3)
def _e_cam(t):
    u = ease("inout", clamp((t - 0.2) / (T_LOW - 0.2)))
    (a, za), (b, zb) = E_CAM
    z = math.exp(lerp(math.log(za), math.log(zb), u))
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u)), z


def _e_lid(t):
    """Manhole A's lid on the elevation (street.py's canned value): levered up on edge from T_LIFT."""
    return 0.35 * k(t, T_LIFT, 0.22, "out")


def _e_row(who, tt):
    """(st, pose, x) of a walker on the elevation at (twos) time tt, or None before they are out."""
    if tt < OUT[who]:
        return None
    d = perfs()
    st, pose = d[who + "_e"](tt)
    x = d[who + "_ex"]
    if who == "knight":
        _sack(pose)
        if tt >= T_HOOK - 0.2:                                  # his near hand to the lid's edge
            g = St.lid_edge(St.MH_A, _e_lid(tt))
            h = _dry(who, st, pose, x, St.FEET, 1)["hand_near"]
            u = ease("inout", clamp((tt - T_HOOK + 0.2) / 0.2))
            _ik(pose, "near", (lerp(h[0], g[0], u), lerp(h[1], g[1], u)), x, St.FEET, St.FIG_S)
    return st, pose, x


@lru_cache(maxsize=None)
def e_steps(who):
    """(points, times) of a walker's footfalls on the elevation, on its track under the street."""
    d = perfs()
    pts, times = [], []
    for t0, side, fx in Bk.footfalls(d[who + "_e"], OUT[who] + 0.05, d[who + "_eend"] + 0.1):
        x = d[who + "_ex"] + fx * St.FIG_S
        if x < E_DOOR_X - 6.0:
            continue
        pts.append((x, TRACK_Y[who]))
        times.append(t0)
    return tuple(pts), tuple(times)


def _guard_x_e(t):
    """The guard's light behind the bank's barred windows on the elevation (x)."""
    return 872.0 + 118.0 * math.sin(2.0 * math.pi * (t + 0.6) / 3.4)


def _elevation(c, t, tt):
    centre, z = _e_cam(t)
    door = k(t, T_DOOR[0], T_DOOR[1] - T_DOOR[0], "out") * (1.0 - k(t, T_DOOR_SHUT[0], T_DOOR_SHUT[1] - T_DOOR_SHUT[0]))
    rows = [(w, _e_row(w, tt)) for w in ("cracker", "architect", "knight")]

    def figures(cc):
        for who, row in rows:
            if row is None:
                continue
            st, pose, x = row
            cc.save()
            if tt < OUT[who] + 0.5:                               # in the doorway: nothing of them behind it
                d0 = St.TEN_DOOR_E
                cc.rectangle(d0[0] + 1.0, d0[1] + 1.0, 2000.0, 400.0)
                cc.clip()
            St.fig(cc, who, st, pose, x, St.FEET, facing=1, lit=None)
            cc.restore()

    c.save()
    St.zoom_on(c, centre, z)
    St.draw_elevation(c, t, windows={}, low=1.0, guard_x=_guard_x_e(t), clock=(11, 59), street_door=door,
                      car=dict(lights=0.0), lid_a=_e_lid(t), figures=figures)
    for who in WHO:
        pts, times = e_steps(who)
        K.step_dots(c, list(pts), list(times), t, TRACK_COL[who], r=4.2, seed=11 + len(who))
    c.restore()


# ============================================================================ the low angle (3-5)
@lru_cache(maxsize=1)
def _knight_x_l():
    """Where the Knight is drawn from on the low angle, so his pelvis stands at L_STOP."""
    st, _ = perfs()["knight_e"](T_HOOK)
    return L_STOP["knight"] - st["pelvis"][0] * Bk.FIG_S


@lru_cache(maxsize=512)
def _knight_hand(tt):
    """The Knight's near hand (Bk set px, on NEAR's road) as the mocap has it while he heaves."""
    st, pose = perfs()["knight_e"](tt)
    return _dry("knight", st, pose, _knight_x_l(), 0.0, 1, Bk.FIG_S)["hand_near"]


def lid_at(tt):
    """(grip, (pivot_x, angle)) of manhole A's lid on the low angle, dragged by his hand (DOUBLE
    CROSS's lid): the grip goes from its edge at rest to his rising hand, the far edge sliding
    along the road behind it; when he lets go it falls flat."""
    rest = Bk.lid_edge(0.0)
    if tt < T_LIFT:
        return rest, (Bk.LID_HOME, 0.0)
    if tt < T_DROP:
        h = _knight_hand(tt)
        u = ease("inout", clamp((tt - T_LIFT) / 0.1))
        g = (lerp(rest[0], h[0], u), lerp(rest[1], h[1], u))
        hh = clamp(rest[1] - g[1], 0.0, 0.9 * Bk.LID_L)
        px = g[0] + math.sqrt(Bk.LID_L ** 2 - hh ** 2)
        return (g[0], rest[1] - hh), (px, math.degrees(math.asin(hh / Bk.LID_L)))   # his hand stays on its edge
    g, (px, ang) = lid_at(T_DROP - 1e-6)
    f = clamp((tt - T_DROP) / (T_CLANK - T_DROP))
    return g, (px - 6.0 * f, ang * (1.0 - f * f))


def _descent(t, who, x0):
    """(x, h) of a climber going down shaft A on the low angle: steps in over the hole, then down."""
    t0 = DOWN[who]
    fc = L_FACING[who]
    kk = clamp((t - t0) / STEP_IN)
    if kk < 1.0:
        h = lerp(Bk.WATER, Bk.WATER - Bk.RUNG_STEP, kk)
    else:
        h = lerp(Bk.WATER - Bk.RUNG_STEP, 0.0, clamp((t - t0 - STEP_IN) / (CLIMB - STEP_IN)))
    return lerp(x0, SHAFT_X - 4.0 * fc, ease("inout", kk)), h


def _low_rows(tt):
    """[(who, st, pose, x, foot_y, facing, down)] on the low angle (Bk set px), back to front."""
    d = perfs()
    out = []
    for who in ("cracker", "architect", "knight"):
        fc = L_FACING[who]
        if who == "knight":
            st, pose = d["knight_e"](tt)
            x = _knight_x_l()
        else:
            st, pose = d[who + "_l"](tt)
            x = L_STOP[who] - st["pelvis"][0] * Bk.FIG_S
            pose.lean += 1.0 * math.sin(2.0 * math.pi * (tt * 0.45 + 0.3 * len(who)))
        if tt < DOWN[who]:
            if who == "knight":
                _sack(pose)
                if tt < T_DROP:                                       # his near hand on the lid's edge
                    g, _ = lid_at(tt)
                    _ik(pose, "near", g, x, 0.0, Bk.FIG_S)
            out.append((who, st, pose, x, 0.0, fc, False))
            continue
        if who == "knight":
            st_d, _ = d["knight_e"](DOWN[who])
            x0 = x + st_d["pelvis"][0] * Bk.FIG_S
        else:
            x0 = L_STOP[who]
        xx, h = _descent(tt, who, x0)
        if h < -40.0:
            continue
        st2, pose2 = Bk.ladder_pose(who, h, facing=fc)
        # both hands on the hole's rim, on the ladder's side, while they can reach it
        for side, dx in (("near", 22.0), ("far", 30.0)):
            _ik(pose2, side, (SHAFT_X + fc * dx, -1.0), xx, Bk.WATER, Bk.FIG_S)
        if who == "knight":
            _sack(pose2)
        out.append((who, st2, pose2, xx, Bk.WATER, fc, True))
    return out


def _keystone(c, scale, draw_src, y_road, a=KEY_A, cx=KEY_CX, step_px=4):
    """Paint draw_src (frame px) leaning back, as a camera tipped up from the road sees it: above
    y_road each row narrows toward cx by (1 - a * height) and the heights foreshorten (a
    homography, painted in thin strips of an offscreen picture, aligned to device pixels)."""
    m_top = 1.0 - a * y_road
    top_h = y_road / m_top                                  # the source height the frame's top shows
    x0 = cx - (cx + 8.0) / m_top
    x1 = cx + (W - cx + 8.0) / m_top
    y0 = y_road - top_h - 8.0
    y1 = H
    wpx, hpx = int(math.ceil((x1 - x0) * scale)), int(math.ceil((y1 - y0) * scale))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, wpx, hpx)
    cc = cairo.Context(surf)
    cc.scale(scale, scale)
    cc.translate(-x0, -y0)
    draw_src(cc)
    pat = cairo.SurfacePattern(surf)
    pat.set_filter(cairo.FILTER_GOOD)
    rows = int(math.ceil(y_road * scale / step_px))
    for i in range(rows):
        ya = i * step_px / scale
        yb = min((i + 1) * step_px / scale, y_road)
        if yb <= ya:
            continue
        ym = 0.5 * (ya + yb)
        hd = y_road - ym
        m = 1.0 - a * hd
        hs = hd / m
        dh = 1.0 / (m * m)                                   # d(source height) / d(frame height)
        ys0 = y_road - hs - dh * (y_road - hd)               # source y = ys0 + dh * y
        pat.set_matrix(cairo.Matrix(scale / m, 0.0, 0.0, scale * dh, scale * (cx - cx / m - x0), scale * (ys0 - y0)))
        c.save()
        c.rectangle(0.0, ya, W, yb - ya)
        c.clip()
        c.set_source(pat)
        c.paint()
        c.restore()


def _key_pt(p, y_road, a=KEY_A, cx=KEY_CX):
    """Where the keystone puts frame point p (as drawn flat) on the leaning front."""
    hs = y_road - p[1]
    if hs <= 0.0:
        return p
    hd = hs / (1.0 + a * hs)
    m = 1.0 - a * hd
    return (cx + (p[0] - cx) * m, y_road - hd)


ROAD_FAR = lerp(NIGHT, INK, 0.6)
LID_FS = 0.27                                # the road's foreshortening on the low angle (the hole's ellipse)


def _lid_dy(tt):
    """The lid falls toward us as he lets it go: it lands on the road in front of his feet."""
    return 13.0 * ease("in", clamp((tt - T_DROP) / (T_CLANK - T_DROP)))


def _lid_disc(c, lid, dy=0.0):
    """Manhole A's lid on the low angle (NEAR's set px): a cast-iron disc foreshortened like the
    hole, tipping up about its east edge as DOUBLE CROSS's (pivot_x, angle) has it."""
    px, ang = lid
    a = math.radians(ang)
    R = Bk.LID_L / 2.0
    u = (-math.cos(a), -math.sin(a))
    pivot = (px, 1.5 + 3.5 * math.cos(a) + dy)
    m = (pivot[0] + R * u[0], pivot[1] + R * u[1])

    def outline(sc, dy=0.0):
        return bass.orient([(m[0] + sc * R * (math.cos(q) * u[0]),
                             m[1] + dy + sc * R * (math.cos(q) * u[1] + math.sin(q) * LID_FS))
                            for q in (2.0 * math.pi * i / 48 for i in range(48))], True)

    face = lerp(Bk.LID, Bk.LID_LIT, clamp(ang / 40.0))
    bass.fill_polys(c, [outline(1.04, 2.6)], INK)
    bass.fill_polys(c, [outline(1.0)], face)
    for sc, w in ((0.74, 0.07), (0.4, 0.08)):
        bass.fill_polys(c, [outline(sc)], lerp(face, INK, 0.45))
        bass.fill_polys(c, [outline(sc - w)], face)


def _low(c, t, tt, scale):
    y_road = FAR.to_frame((0.0, 0.0))[1]
    clock = (11, 59) if t < T_CHIME else (12, 0)
    gx = 365.0 + 175.0 * math.sin(2.0 * math.pi * (t - 3.0 + 0.4) / 3.0)

    def far(cc):
        K.fill(cc, NIGHT)
        St.bank_front(cc, FAR, t, clock=clock, low=1.0, guard_x=gx, car=True, lid=1.0)

    _keystone(c, scale, far, y_road)
    # the road toward us, and the lamp's light on it round the hole
    K.fill(c, ROAD_FAR, (-10.0, y_road, W + 10.0, H + 10.0))
    bass.fill_polys(c, [bass.cut_rect(-10.0, y_road - 1.5, W + 10.0, y_road + 3.0, seed=401, amp=0.3)],
                    lerp(STEEL, NIGHT, 0.35))
    hole_f = NEAR.to_frame((SHAFT_X, 4.0))
    K.pool(c, (hole_f[0] + 10.0, hole_f[1] + 36.0), 520.0, 130.0, AMBER, 0.09)
    # the clock strikes midnight: a ripple off its face
    if T_CHIME <= t < T_CHIME + 1.3:
        cf = _key_pt(FAR.to_frame(Bk.CLOCK_AT), y_road)
        K.ripple(c, cf, t, T_CHIME, PAPER, n=3, every=0.18, life=1.0, r0=34.0, r1=190.0, width=6.0, seed=402, alpha=0.85)
    rows = _low_rows(tt)
    with NEAR.on(c):
        # the hole: an ellipse seen across the road, black inside, its iron rim
        Bk.ellipse(c, (SHAFT_X, 5.0), Bk.MANHOLE_R + 4.0, 9.5, lerp(STEEL, INK, 0.35), n=56)
        Bk.ellipse(c, (SHAFT_X, 5.0), Bk.MANHOLE_R - 1.0, 7.0, INK, n=56)
        g, lid = lid_at(tt)
        _lid_disc(c, lid, _lid_dy(tt))
        if T_CLANK <= t < T_CLANK + 0.6:
            px, _ = lid
            K.ripple(c, (px - Bk.LID_L * 0.5, 2.0 + _lid_dy(tt)), t, T_CLANK, PAPER, n=2, every=0.1, life=0.35,
                     r0=5.0, r1=22.0, width=1.8, seed=403, alpha=0.9)
        for who, st, pose, x, fy, fc, down in rows:
            c.save()
            if down:                                              # into the hole: the road's near lip hides them
                c.new_path()
                c.rectangle(-2000.0, -3000.0, 5000.0, 3000.0)
                pts = [(SHAFT_X + (Bk.MANHOLE_R - 1.0) * math.cos(2 * math.pi * i / 40),
                        5.0 + 7.0 * math.sin(2 * math.pi * i / 40)) for i in range(40)]
                c.move_to(*pts[0])
                for p in pts[1:]:
                    c.line_to(*p)
                c.close_path()
                c.rectangle(SHAFT_X - Bk.MANHOLE_R + 1.0, -10.0, 2.0 * Bk.MANHOLE_R - 2.0, 15.0)
                c.clip()
            C.draw(c, who, st, pose, x, fy, Bk.FIG_S, fc, bg=lerp(NIGHT, STEEL, 0.3), rim_w=5.0 / NEAR.zoom)
            c.restore()


# ============================================================================ the shaft from above (5-7)
def _stretch(t):
    """The depth scale: the shaft stretches away below the rim (the dolly zoom)."""
    return 1.0 + 1.6 * ease("inout", clamp((t - T_STRETCH[0]) / (T_STRETCH[1] - T_STRETCH[0])))


def _v_r(z, t):
    """The radius (frame px) of the shaft's wall at depth z (0 the rim .. 1 the water)."""
    return V_R / (1.0 + 3.0 * z * _stretch(t))


def _v_ang(z, t):
    """The spiral: the angle (deg) of the rungs at depth z, turning as the shaft stretches."""
    return -40.0 + 420.0 * z + 55.0 * (_stretch(t) - 1.0)


def _climber_z(who, t):
    """How far down shaft A a climber looks from the rim (0 the rim .. 1 the water), or None: the
    stretching shaft holds them near the top and drops them away at the end (they land on the
    beat)."""
    t0 = DOWN[who] + STEP_IN
    if t < t0:
        return None
    return clamp((t - t0) / (CLIMB - STEP_IN)) ** 2


def _from_above(c, who, p, s, ang, rim, rim_px):
    """A climber seen from straight above (frame px; s px per unit): shoulders, two arms reaching
    out to the rung (+x), the head (her chignon, the Cracker's bowler, the Knight's cap), rimmed in
    their colour toward the lamp (rim_px)."""
    wide = {"knight": 1.18, "architect": 0.9, "cracker": 0.84}[who]
    sh = bass.draw.ellipse_pts((-6.0, 0.0), 30.0 * wide, 62.0 * wide, n=44)
    arms = [bass.capsule_pts((0.0, -46.0 * wide), (60.0, -30.0), 12.0 * wide, 9.0, cap=4),
            bass.capsule_pts((0.0, 46.0 * wide), (60.0, 30.0), 12.0 * wide, 9.0, cap=4)]
    hands = [bass.draw.circle_pts((62.0, -30.0), 10.0, n=16), bass.draw.circle_pts((62.0, 30.0), 10.0, n=16)]
    if who == "architect":
        head = [bass.draw.ellipse_pts((2.0, 0.0), 25.0, 23.0, n=36), bass.draw.ellipse_pts((-22.0, 0.0), 12.0, 11.0, n=20)]
    elif who == "cracker":
        head = [bass.draw.circle_pts((2.0, 0.0), 37.0, n=48)]
    else:
        head = [bass.draw.ellipse_pts((2.0, 0.0), 29.0, 31.0, n=40),
                bass.orient([(22.0, -24.0), (48.0, -15.0), (48.0, 15.0), (22.0, 24.0)], True)]
    polys = [bass.orient(q, True) for q in [sh] + arms + hands + head]
    for off, col in ((rim_px, rim), ((0.0, 0.0), INK)):
        c.save()
        c.translate(p[0] + off[0], p[1] + off[1])
        c.rotate(math.radians(ang))
        c.scale(s, s)
        bass.fill_polys(c, polys, col)
        c.restore()
    # the head, picked out from the shoulders by a thin line of their colour (the bowler's brim
    # and crown, her chignon, his cap)
    c.save()
    c.translate(*p)
    c.rotate(math.radians(ang))
    c.scale(s, s)
    w = max(2.2, 1.6 / max(s, 0.05)) if s < 1.2 else 2.6
    if who == "cracker":
        bass.ring(c, (2.0, 0.0), 36.0, w, rim, seed=411, n=48)
        bass.ring(c, (2.0, 0.0), 22.0, w * 0.9, lerp(INK, rim, 0.6), seed=412, n=40)
    elif who == "architect":
        bass.fill_polys(c, [bass.orient(bass.draw.ellipse_pts((2.0, 0.0), 25.0 + w, 23.0 + w, n=36), True)], rim)
        bass.fill_polys(c, [bass.orient(bass.draw.ellipse_pts((2.0, 0.0), 25.0, 23.0, n=36), True)], INK)
        bass.fill_polys(c, [bass.orient(bass.draw.ellipse_pts((-22.0, 0.0), 12.0, 11.0, n=20), True)], INK)
    else:
        bass.fill_polys(c, [bass.orient(bass.draw.ellipse_pts((2.0, 0.0), 29.0 + w, 31.0 + w, n=40), True)], rim)
        bass.fill_polys(c, [bass.orient(q, True) for q in head], INK)
    c.restore()


def _v_drips():
    """[(t_hit, angle)] of the drips falling from the rim to the water in the shaft."""
    out = []
    for i in range(5):
        per = 0.8 + 0.5 * hash01(i, 421)
        ph = 0.9 * hash01(i, 422)
        ang = 360.0 * hash01(i, 423)
        j = 0
        while True:
            th = T_SHAFT + ph + j * per + 0.5
            if th > T_SECTION + 0.6:
                break
            out.append((round(th, 4), ang + 47.0 * j))
            j += 1
    return out


V_ROAD = lerp(NIGHT, INK, 0.45)
V_LID = lerp(STEEL, INK, 0.2)
V_WALL = lerp(STEEL, NIGHT, 0.3)             # the shaft's brick at the top, in the lamp's spill
V_IRON = lerp(STEEL, PAPER, 0.3)             # the rungs


def _shaft(c, t, tt):
    # the road round the rim, from above: asphalt, the lamp's pool, the lid laid aside
    K.fill(c, V_ROAD)
    K.pool(c, (V_C[0] - 420.0, V_C[1] + 600.0), 720.0, 560.0, AMBER, 0.08)
    lid_c = (V_C[0] - V_R * 1.5, V_C[1] + V_R * 1.5)
    Bk.disc(c, lid_c, V_R * 0.98, V_LID, seed=430, n=96)
    for i in range(4):
        bass.ring(c, lid_c, V_R * (0.3 + 0.17 * i), 7.0, lerp(V_LID, INK, 0.45), seed=431 + i, n=96)
    for i in range(-3, 4):                                     # its cast grid
        a = math.radians(-35.0)
        o = i * 0.13 * V_R
        p0 = (lid_c[0] + o * math.cos(a + math.pi / 2) - 0.9 * V_R * math.cos(a),
              lid_c[1] + o * math.sin(a + math.pi / 2) - 0.9 * V_R * math.sin(a))
        p1 = (p0[0] + 1.8 * V_R * math.cos(a), p0[1] + 1.8 * V_R * math.sin(a))
        c.save()
        c.new_path()
        bass.iris_path(c, lid_c, V_R * 0.86, seed=434, n=72)
        c.clip()
        bass.line_band(c, [p0, p1], lerp(V_LID, INK, 0.3), width=5.0, seed=435 + i)
        c.restore()
    # the rim: an iron collar
    Bk.disc(c, V_C, V_R + 44.0, lerp(STEEL, PAPER, 0.06), seed=440, n=96)
    Bk.disc(c, V_C, V_R + 16.0, lerp(STEEL, INK, 0.6), seed=441, n=96)
    # the wall: brick courses stepping down into the dark (flat tones), each joint a thin dark ring
    for i in range(V_RINGS):
        z = i / V_RINGS
        r = _v_r(z, t)
        col = lerp(V_WALL, INK, clamp(0.06 + 0.9 * z ** 0.6 + (0.07 if i % 2 else 0.0)))
        Bk.disc(c, V_C, r, col, seed=450 + i, n=96 if i < 10 else 56)
        bass.ring(c, V_C, r, max(0.8, 0.016 * r), lerp(col, INK, 0.6), seed=470 + i, n=96 if i < 10 else 56)
    rw = _v_r(1.0, t)
    water = lerp(NIGHT, INK, 0.25)
    Bk.disc(c, V_C, rw, water, seed=480, n=48)
    Bk.disc(c, V_C, rw * 0.42, lerp(water, STEEL, 0.25), seed=481, n=32)      # the sky's disc, reflected
    # the splashes and the drips' rings on the water
    c.save()
    c.new_path()
    c.arc(V_C[0], V_C[1], rw, 0.0, 2.0 * math.pi)
    c.clip()
    for who in WHO:
        if LAND[who] <= t < LAND[who] + 0.9:
            K.ripple(c, V_C, t, LAND[who], PAPER, n=3, every=0.12, life=0.7, r0=rw * 0.08, r1=rw * 1.05,
                     width=max(2.0, rw * 0.05), seed=520 + len(who), alpha=0.9)
    for th, ang in _v_drips():
        if 0.0 <= t - th < 0.5:
            q = (V_C[0] + rw * 0.55 * math.cos(math.radians(ang)), V_C[1] + rw * 0.55 * math.sin(math.radians(ang)))
            K.ripple(c, q, t, th, PAPER, n=1, life=0.5, r0=1.5, r1=rw * 0.5, width=1.4, seed=531, alpha=0.6)
    c.restore()
    # the rungs: iron staples, one below another, turning down the shaft (the spiral)
    n_r = 15
    for j in range(n_r):
        z = (j + 0.6) / (n_r + 0.3)
        r = _v_r(z, t)
        a = _v_ang(z, t)
        half = 9.0
        ri = 0.92 * r
        pts = [(V_C[0] + r * math.cos(math.radians(a - half)), V_C[1] + r * math.sin(math.radians(a - half)))]
        pts += [(V_C[0] + ri * math.cos(math.radians(a + half * (q / 4.0 - 1.0))),
                 V_C[1] + ri * math.sin(math.radians(a + half * (q / 4.0 - 1.0)))) for q in range(9)]
        pts += [(V_C[0] + r * math.cos(math.radians(a + half)), V_C[1] + r * math.sin(math.radians(a + half)))]
        w = max(1.6, 0.04 * r)
        col = lerp(V_IRON, INK, clamp(0.72 * z ** 1.3))
        shp = [(V_C[0] + (x - V_C[0]) * 0.955, V_C[1] + (y - V_C[1]) * 0.955) for x, y in pts]
        bass.line_band(c, shp, lerp(INK, NIGHT, 0.2), width=w * 1.5, seed=490 + j)
        bass.line_band(c, pts, col, width=w, seed=510 + j)
    # drips from the rim, falling and shrinking toward the water
    for th, ang in _v_drips():
        u = 1.0 - (th - t) / 0.5
        if 0.0 <= u < 1.0:
            z = u * u
            r = lerp(_v_r(z, t) * 0.85, rw * 0.55, z)
            q = (V_C[0] + r * math.cos(math.radians(ang)), V_C[1] + r * math.sin(math.radians(ang)))
            K.dot(c, q, max(1.4, 8.0 * _v_r(z, t) / V_R), lerp(PAPER, STEEL, 0.3), seed=530)
    # the climbers, deepest first, each at its rung on the spiral, hands out to the iron
    rows = []
    for who in WHO:
        z = _climber_z(who, t)
        if z is None or z >= 0.985:
            continue
        rows.append((z, who))
    for z, who in sorted(rows, reverse=True):
        r = _v_r(z, t)
        a = _v_ang(z, t)
        s = 3.1 * r / V_R
        pr = max(0.0, 0.92 * r - 64.0 * s)
        q = (V_C[0] + pr * math.cos(math.radians(a)), V_C[1] + pr * math.sin(math.radians(a)))
        rim = lerp(C.RIM[who], lerp(C.RIM[who], INK, 0.5), clamp((z - 0.55) / 0.45))
        w = 2.5 + 3.5 * s
        _from_above(c, who, q, s, a, rim, (-0.9 * w, -0.45 * w))


# ============================================================================ the section (7-14)
def _sec_cam(t):
    keys = SEC_KEYS
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a, _), (t1, b, e) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease(e, (t - t0) / (t1 - t0)) if e else 0.0
            z = math.exp(lerp(math.log(a[2]), math.log(b[2]), u))
            return (lerp(a[0], b[0], u), lerp(a[1], b[1], u), z)
    return keys[-1][1]


def _climb_h(who, t):
    """How high a climber stands on the hatch's rungs (h above the water), or None (wading)."""
    a, b = T_UP_SHAFT[who]
    if t < a:
        return None
    h = H_TOP[who] * ease("inout", clamp((t - a) / (b - a)))
    if who == "knight":                                      # he pushes up a crack: up a little on his toes
        h += 6.0 * k(t, T_CRACK - 0.15, 0.2, "out") * (1.0 - k(t, T_OPEN[0], 0.2, "inout"))
    tu = UP[who]
    r = RISE[who]
    if t >= tu - r:                                          # up and out into the hall
        h = lerp(h, H_FLOOR, ease("inout", clamp((t - tu + r) / r)))
    return h


def _hatch_ang(t):
    """The hatch's lid (degrees up off the floor)."""
    a = 7.0 * k(t, T_CRACK, 0.22, "out")
    if t >= T_OPEN[0]:
        a = lerp(a, 104.0, k(t, T_OPEN[0], T_OPEN[1] - T_OPEN[0], "outback"))
    g0, g1, g2 = T_LID_DOWN
    if t >= g0:                                              # the Cracker guides it over, then it drops
        a = lerp(104.0, 68.0, ease("inout", clamp((t - g0) / (g1 - g0))))
        a *= 1.0 - ease("in", clamp((t - g1) / (g2 - g1)))
    return a


def _lid_tip(ang):
    """The hatch lid's free edge (section px) at an angle."""
    a = math.radians(ang)
    return (St.HATCH[0] - 2.0 + LID_LEN * math.cos(a), St.FEET + 1.0 - LID_LEN * math.sin(a))


def _sec_rows(t, tt):
    """[(who, st, pose, x, foot_y, facing, where)] in the section: where 'sewer' (wading), 'shaft'
    (on the hatch's rungs, or climbing out), 'hall' (standing on the hall's floor)."""
    d = perfs()
    out = []
    for who in ("cracker", "architect", "knight"):
        h = _climb_h(who, t)
        tu = UP[who]
        if h is None:
            st, pose = d[who + "_s"](tt)
            x = d[who + "_sx"]
            if who == "knight":
                _sack(pose)
            out.append((who, st, pose, x, St.SEWER_FEET, 1, "sewer"))
            continue
        if t < tu:
            fc = 1
            st, pose = Bk.ladder_pose(who, h, facing=fc, rung=St.RUNG_STEP)
            a, _ = T_UP_SHAFT[who]
            x = lerp(WADE_TO[who], LADDER_X, ease("inout", clamp((t - a) / 0.25)))
            if who == "cracker":                              # he climbs out over the corner's edge
                r0 = tu - 0.4 * RISE[who]
                x = lerp(x, HALL_X[who], ease("inout", clamp((t - r0) / (tu - r0))))
            if who == "knight":
                _sack(pose)
                if T_CRACK - 0.25 <= t < T_OPEN[1]:          # his near hand flat up under the lid's free end
                    _ik(pose, "near", (x + 20.0, St.FEET + 9.0), x, St.WATER, St.FIG_S)
            out.append((who, st, pose, x, St.WATER, fc, "shaft"))
            continue
        # in the hall: a few steps off the hatch, then still, pressed back in the dark
        fc, x = 1, d[who + "_hx"]
        st, pose = d[who + "_h"](tt)
        if who == "cracker":                                 # he guides the lid down
            g0, g1, g2 = T_LID_DOWN
            if g0 - 0.1 <= tt < g1 + 0.05:
                _ik(pose, "near", _lid_tip(_hatch_ang(clamp(tt, g0, g1))), x, St.FEET, St.FIG_S)
            pose.lean += 16.0 * k(tt, g0 - 0.05, 0.15, "inout") * (1.0 - k(tt, g1 + 0.05, 0.25, "inout"))
        if tt >= tu + HALL_WALK[who]:
            pose.lean += 0.8 * math.sin(2.0 * math.pi * (tt * 0.45 + 0.3 * len(who)))
        t_press = T_THUD if who == "cracker" else T_PRESS + 0.06 * WHO.index(who)
        pose.lean -= 4.0 * k(tt, t_press, 0.3, "inout")
        if who == "knight":
            _sack(pose)
        out.append((who, st, pose, x, St.FEET, fc, "hall"))
    # back to front: the hall's file drawn from the wall outward
    out.sort(key=lambda r: (r[6] == "hall", r[3] if r[6] == "hall" else 0.0))
    return out


@lru_cache(maxsize=None)
def s_steps(who):
    """(points, times) of a wader's footfalls along the sewer, on its track in the water."""
    d = perfs()
    a, b = WADE[who]
    pts, times = [], []
    for t0, side, fx in Bk.footfalls(d[who + "_s"], a, b + 0.05):
        pts.append((d[who + "_sx"] + fx * St.FIG_S, SEWER_TRACK[who]))
        times.append(t0)
    return tuple(pts), tuple(times)


def _sweep(t):
    """The guard's light (degrees off his aim) at scene time t: a full swing every 2 s (s05's clock)."""
    return 20.0 * math.sin(math.pi * (FILM_T0 + t - SWEEP_PHASE))


def _beam(t):
    """The guard's light: degrees below the horizontal, toward the corner (it sweeps the floor in
    front of the desk and never quite reaches them)."""
    return 64.0 + 0.3 * _sweep(t)


def _guard(c, t, tt, store):
    d = perfs()
    st, pose = d["guard"](tt)
    x = GUARD_X - st["pelvis"][0] * St.FIG_S
    on = t < T_LIGHT_OFF
    fl = C.hold_flashlight(on=on)
    pose.hold["near"] = fl
    a = math.radians(_beam(t) + 22.0 * k(t, T_LIGHT_OFF, 0.4, "inout"))   # off: he lowers it
    target = (GUARD_X - 100.0 * math.cos(a), St.FEET - 84.0 + 100.0 * math.sin(a))
    _aim("guard", st, pose, x, St.FEET, -1, target)
    St.fig(c, "guard", st, pose, x, St.FEET, facing=-1, lit=None)
    lens, ang = C.lens_at(c, fl)
    store["lens"], store["ang"], store["on"] = lens, ang, on


def _glove_polys(r):
    """The Knight's gloved hand pressed flat up under a board, and his sleeve going down from it
    (lens px: origin at the palm's middle on the board's underside, +x along the board toward its
    free end, +y down, r the lens radius)."""
    palm = bass.orient([(-0.24 * r, 0.0), (0.26 * r, 0.0), (0.34 * r, 0.015 * r), (0.37 * r, 0.05 * r),
                        (0.33 * r, 0.09 * r), (0.16 * r, 0.12 * r), (-0.02 * r, 0.15 * r), (-0.12 * r, 0.26 * r),
                        (-0.27 * r, 0.22 * r), (-0.29 * r, 0.08 * r)], True)
    thumb = bass.orient(bass.capsule_pts((-0.06 * r, 0.11 * r), (0.13 * r, 0.2 * r), 0.055 * r, 0.042 * r, cap=4),
                        True)
    sleeve = bass.orient([(-0.36 * r, 0.12 * r), (-0.06 * r, 0.2 * r), (-0.14 * r, 1.5 * r), (-0.56 * r, 1.5 * r)], True)
    cuff = bass.orient([(-0.37 * r, 0.1 * r), (-0.04 * r, 0.19 * r), (-0.06 * r, 0.27 * r), (-0.39 * r, 0.2 * r)], True)
    return [sleeve, cuff, palm, thumb]


def _lens_inside(t):
    """The callout: the hatch's lid in the hall's floor, cut, and the Knight's gloved hand flat up
    under its free end; he pushes it up a crack and the hall's lamplight slices in through the slit,
    down across his knuckles into the shaft (the crack drawn a little wider than life: a lens)."""
    cx, cy = LENS_C
    r = LENS_R

    def inside(c):
        ang = min(1.8 * _hatch_ang(t), 20.0)
        lit = clamp(ang / 10.0)
        y_top, y_bot = cy - 0.36 * r, cy - 0.12 * r          # the floor slab, cut
        x0, x1 = cx - 0.7 * r, cx + 0.48 * r               # the hatch's opening in it
        L = x1 - x0
        a = math.radians(ang)
        # the hall above (dark, warming toward the lamp on the right) and the shaft's lining below
        K.fill(c, lerp(NIGHT, STEEL, 0.16), (cx - r, cy - r, cx + r, cy + r))
        K.fill(c, lerp(INK, NIGHT, 0.4), (cx - r, y_bot, cx - 0.82 * r, cy + r))
        K.fill(c, lerp(INK, NIGHT, 0.4), (cx + 0.62 * r, y_bot, cx + r, cy + r))
        K.fill(c, lerp(DEEP, AMBER, 0.14 + 0.1 * lit), (cx - r, cy - r, cx + r, y_top))
        bass.fill_polys(c, [bass.orient([(cx - 0.1 * r, y_top), (cx + r, cy - r), (cx + r, y_top)], True)],
                        AMBER, 0.1 + 0.08 * lit)
        # the slab either side of the opening
        bass.fill_polys(c, [bass.cut_rect(cx - 1.2 * r, y_top, x0, y_bot, seed=540, amp=0.4),
                            bass.cut_rect(x1, y_top, cx + 1.2 * r, y_bot, seed=541, amp=0.4)], lerp(INK, STEEL, 0.3))
        # the slit at the lid's free end and the slice of light fanning down through it (flat tints)
        thick = y_bot - y_top
        tip_top = (x0 + L * math.cos(a), y_top - L * math.sin(a))
        tip_bot = (tip_top[0] - thick * math.sin(a), tip_top[1] + thick * math.cos(a))
        edge = (x1, y_top + 0.01 * r)
        if lit > 0.0:
            far = 2.6 * r
            d1 = (math.cos(math.radians(118.0)), math.sin(math.radians(118.0)))
            d2 = (math.cos(math.radians(142.0)), math.sin(math.radians(142.0)))
            wedge = [tip_bot, edge, (edge[0] + d1[0] * far, edge[1] + d1[1] * far),
                     (tip_bot[0] + d2[0] * far, tip_bot[1] + d2[1] * far)]
            bass.fill_polys(c, [bass.orient(wedge, True)], AMBER, 0.3 * lit)
            core = [tip_bot, edge, (edge[0] + d1[0] * far, edge[1] + d1[1] * far),
                    (lerp(tip_bot[0], edge[0], 0.5) + 0.5 * (d1[0] + d2[0]) * far,
                     lerp(tip_bot[1], edge[1], 0.5) + 0.5 * (d1[1] + d2[1]) * far)]
            bass.fill_polys(c, [bass.orient(core, True)], AMBER, 0.22 * lit)
        # his hand under the lid's free end, the sleeve down from it, rimmed toward the light
        d = 0.8 * L
        palm = (x0 + d * math.cos(a) - thick * math.sin(a), y_top - d * math.sin(a) + thick * math.cos(a))
        polys = _glove_polys(r)
        for off, col in (((2.8, -1.8), RED), ((0.0, 0.0), INK)):
            c.save()
            c.translate(palm[0] + off[0], palm[1] + off[1])
            c.rotate(-a)
            bass.fill_polys(c, polys, col)
            c.restore()
        if lit > 0.0:                                        # the slice of light across the knuckles
            c.save()
            c.translate(*palm)
            c.rotate(-a)
            c.new_path()
            for q in polys:
                c.move_to(*q[0])
                for pt in q[1:]:
                    c.line_to(*pt)
                c.close_path()
            c.restore()
            c.save()
            c.clip()
            bass.fill_polys(c, [bass.orient(wedge, True)], AMBER, 0.55 * lit)
            c.restore()
        # the lid: a heavy board on its hinge, its free end lifted
        c.save()
        c.translate(x0, y_top)
        c.rotate(-a)
        bass.fill_polys(c, [bass.cut_rect(0.0, 0.0, L - 0.01 * r, thick, seed=542, amp=0.4)], lerp(INK, STEEL, 0.42))
        bass.fill_polys(c, [bass.cut_rect(0.04 * r, 0.035 * r, L - 0.05 * r, 0.065 * r, seed=543, amp=0.2)],
                        lerp(INK, STEEL, 0.56))
        c.restore()
        if lit > 0.0:                                        # the bright line of the slit
            bass.line_band(c, [tip_bot, edge], lerp(AMBER, PAPER, 0.35), width=0.03 * r, seed=545)
        K.dot(c, (x0 + 0.03 * r, y_top + 0.03 * r), 0.05 * r, lerp(STEEL, PAPER, 0.2), seed=544)
    return inside


def _section(c, t, tt):
    cx, cy, z = _sec_cam(t)
    store = {}
    rows = _sec_rows(t, tt)

    def people(cc, where, n, rect):
        if where == "hall":
            _guard(cc, t, tt, store)

    c.save()
    St.zoom_on(c, (cx, cy), z)
    St.draw_section(c, t, lit={}, people=people, hall_lamp=0.55, vault_lit=0.0, gold_glow=1.0, gold=1.0,
                    hatch=_hatch_u(_hatch_ang(t)), lid_a=1.0, car=dict(lights=0.0), clock=(12, 0),
                    bank_clock=(12, 0))
    K.fill(c, INK, (-400.0, 1936.0, 1600.0, 2600.0))
    # the lamplight slicing in at the crack, down the hatch's shaft
    ang = _hatch_ang(t)
    if 0.5 < ang < 60.0 and t < T_OPEN[1] + 0.3:
        c.save()
        c.rectangle(St.HATCH[0], St.FEET - 2.0, St.HATCH[1] - St.HATCH[0], St.CROWN - St.FEET + 2.0)
        c.clip()
        g = clamp(ang / 7.0)
        x1 = St.HATCH[1]
        bass.fill_polys(c, [bass.orient([(x1 - 3.0, St.FEET), (x1, St.FEET), (x1 - 10.0, St.FEET + 130.0),
                                         (x1 - 30.0 * g - 12.0, St.FEET + 130.0)], True)], AMBER, 0.22 * g)
        c.restore()
    # the waders, the climbers: clipped to the tunnel, the shafts and the hall
    for who, st, pose, x, fy, fc, where in rows:
        c.save()
        c.new_path()
        for r in St.open_rects(above=False):
            c.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
        hr = HALL_R
        c.rectangle(hr[0], hr[1], hr[2] - hr[0], hr[3] - hr[1] + 0.5)
        c.rectangle(St.HATCH[0], St.FEET - 2.0, St.HATCH[1] - St.HATCH[0], 20.0)
        c.clip()
        j = St.fig(c, who, st, pose, x, fy, facing=fc, lit=None)
        if who == "architect" and where == "hall":            # her two eyes in the dark
            K.dot(c, (j["head"][0] + 5.0, j["head"][1] - 1.0), 1.0, PAPER, seed=550)
        c.restore()
    St.water_edge(c)
    for who in WHO:
        pts, times = s_steps(who)
        K.step_dots(c, list(pts), list(times), t, TRACK_COL[who], r=2.4, seed=21 + len(who))
        for p, t0 in zip(pts, times):                         # each step's splash
            if t0 <= t < t0 + 0.6:
                St.splash(c, (p[0], St.WATER), t, t0, 0.55)
    # the guard's cone sweeping the far end of the hall (light: a flat tint)
    if store.get("lens") is not None and store.get("on"):
        c.save()
        hr = HALL_R
        c.rectangle(hr[0], hr[1], hr[2] - hr[0], hr[3] - hr[1])
        c.clip()
        K.cone(c, store["lens"], store["ang"], 13.0, 130.0, PAPER, alpha=0.22, steps=3)
        c.restore()
        K.dot(c, store["lens"], 1.8, PAPER, seed=551)
    if T_LIGHT_OFF <= t < T_LIGHT_OFF + 0.45 and store.get("lens") is not None:
        K.ripple(c, store["lens"], t, T_LIGHT_OFF, PAPER, n=1, life=0.4, r0=2.0, r1=16.0, width=1.2, seed=552,
                 alpha=0.7)
    # the callout lens on the hatch
    if T_LENS[0] <= t < T_LENS[1] + 0.3:
        u = k(t, T_LENS[0], 0.3, "out3") * (1.0 - k(t, T_LENS[1], 0.3, "in3"))
        K.callout(c, (St.HATCH[1] - 3.0, St.FEET + 1.0), LENS_C, LENS_R, _lens_inside(t), u=u, color=RED, ring_w=3.0,
                  dot_r=2.2, line_w=1.3, seed=553)
    c.restore()


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, NIGHT)
    tt = K.twos(t)
    with f.screen() as c:
        if t < T_LOW:
            _elevation(c, t, tt)
        elif t < T_SHAFT:
            _low(c, t, tt, f.scale)
        elif t < T_SECTION:
            _shaft(c, t, tt)
        else:
            _section(c, t, tt)


# ============================================================================ sound
def _e_frame_x(x, t):
    centre, z = _e_cam(t)
    return St.to_frame((x, 0.0), centre, z)[0]


def _s_frame(p, t):
    cx, cy, z = _sec_cam(t)
    return St.to_frame(p, (cx, cy), z)


def cues(T):
    dur = float(getattr(T, "duration", 14.0) or 14.0)
    out = [Cue(0.0, "night_air", gain_db=-22, dur=T_SHAFT + 0.3,
               dc="the table lamp clicks off; night air comes up (a distant city, a far siren, wind)")]
    # the elevation: soft steps across to the manhole
    walk = {"knight": ("a heavy shoe on the paving (soft, careful)", -20),
            "architect": ("a soft creeping step (her)", -25),
            "cracker": ("an old man's shuffling step (the Cracker)", -24)}
    for who in WHO:
        text, g = walk[who]
        for p, t0 in zip(*e_steps(who)):
            out.append(Cue(t0, "footstep", gain_db=g, pan=_pan(_e_frame_x(p[0], t0)), who=who, dc="footstep: " + text))
    out.append(Cue(T_HOOK, "iron_tick", gain_db=-17, pan=_pan(_e_frame_x(St.MH_A - 30.0, T_HOOK)),
                   dc="iron tick: his fingers hook the lid's edge; a low grunt"))
    lid_x = NEAR.to_frame((SHAFT_X, 0.0))[0]
    out.append(Cue(T_LIFT, "manhole_scrape", gain_db=-9, pan=_pan(lid_x), dur=T_DROP - T_LIFT,
                   dc="iron scrape: the manhole lid levered up and dragged out of the hole across the road"))
    out.append(Cue(T_CLANK, "manhole_clank", gain_db=-5, pan=_pan(lid_x - 160.0),
                   dc="CLANK: the iron lid falls flat on the road (it rings)"))
    out.append(Cue(T_CHIME, "chime", gain_db=-9, pan=0.3, dur=3.0,
                   desc="the bank's clock strikes midnight: one deep bell chime across the street"))
    for who in WHO:
        t0 = DOWN[who]
        out.append(Cue(t0 + STEP_IN, "rung", gain_db=-14, pan=_pan(lid_x), who=who,
                       dc=f"a shoe on the first iron rung: {NAME[who]} goes down the manhole"))
        out.append(Cue(t0 + STEP_IN + 0.2, "rung_run", gain_db=-22, pan=_pan(lid_x), dur=CLIMB - STEP_IN - 0.3, who=who,
                       dc=f"a quick run of iron rung steps going down (low; {NAME[who]})"))
        out.append(Cue(LAND[who], "splash", gain_db=-13, who=who,
                       dc=f"splash: {NAME[who]} steps off the ladder into the sewer water"))
    # the shaft: its echo, the stretch, drips
    out.append(Cue(T_SHAFT, "sewer_bed", gain_db=-28, dur=dur - T_SHAFT,
                   dc="the sewer: the channel, the air of the pipe (the shaft's echo first)"))
    out.append(Cue(T_SHAFT, "sink_whoosh", gain_db=-20, dur=T_STRETCH[1] - T_STRETCH[0],
                   dc="a low whoosh: the shaft stretches away below them (the dolly zoom)"))
    for th, ang in _v_drips():
        if T_SHAFT <= th < T_SECTION:
            out.append(Cue(th, "drip", gain_db=-26, dc="a drip into still water (echoing in the pipe)"))
    # the section: steps in water, drips in view, the hatch
    for who in WHO:
        for p, t0 in zip(*s_steps(who)):
            if t0 >= T_SECTION - 0.01:
                out.append(Cue(t0, "water_step", gain_db=-21, pan=_pan(_s_frame(p, t0)[0]), who=who,
                               dc="a footstep in shallow water (sewer slosh)"))
    for t0, x in St.drip_times(T_SECTION, dur):
        fx, fy = _s_frame((x, St.WATER), t0)
        if 0.0 <= fx <= W and 0.0 <= fy <= H:
            out.append(Cue(t0, "drip", gain_db=-26, pan=_pan(fx), dc="a drip into still water (echoing in the pipe)"))
    for who in WHO:
        a, b = T_UP_SHAFT[who]
        out.append(Cue(a, "rung_up", gain_db=-23, pan=_pan(_s_frame((St.HATCH_C, 0.0), a)[0]), dur=b - a, who=who,
                       dc="iron rung steps going up, quick and light"))
        tu = UP[who]
        out.append(Cue(tu - RISE[who], "rung_up", gain_db=-24, pan=_pan(_s_frame((St.HATCH_C, 0.0), tu)[0]),
                       dur=RISE[who], who=who, dc="iron rung steps going up, quick and light"))
    out.append(Cue(T_CRACK, "hatch_creak", gain_db=-13, pan=_pan(_s_frame((St.HATCH_C, 0.0), T_CRACK)[0]), dur=0.6,
                   dc="a long hinge creak: he pushes the hatch up (a crack)"))
    out.append(Cue(T_OPEN[0], "hatch_creak", gain_db=-17, pan=_pan(_s_frame((St.HATCH_C, 0.0), T_OPEN[0])[0]),
                   dur=0.4, dc="a hinge creak: he lifts the hatch open (slow, careful)"))
    d = perfs()
    for who in WHO:
        t0 = UP[who]
        for tf, side, fx in Bk.footfalls(d[who + "_h"], t0, t0 + HALL_WALK[who] + 0.2):
            out.append(Cue(tf, "footstep", gain_db=-28, pan=_pan(_s_frame((d[who + "_hx"] + fx * St.FIG_S, 0.0), tf)[0]),
                           who=who, dc="footstep: " + walk[who][0] + " on the hall's stone floor, held back"))
    out.append(Cue(T_LID_DOWN[0], "hatch_creak", gain_db=-24, pan=_pan(_s_frame((St.HATCH_C, 0.0), T_LID_DOWN[0])[0]),
                   dur=0.25, dc="a long hinge creak: she pushes the hatch up"))
    out.append(Cue(T_THUD, "hatch_thud", gain_db=-22, pan=_pan(_s_frame((St.HATCH_C, 0.0), T_THUD)[0]),
                   desc="a soft wooden thud: the hatch's lid drops shut in its frame (muffled; not the DC fall-open)"))
    out.append(Cue(T_LIGHT_OFF, "flashlight_click", gain_db=-20, pan=_pan(_s_frame((GUARD_X, 0.0), T_LIGHT_OFF)[0]),
                   dc="a flashlight clicks off (a small metal switch)"))
    return sorted(out, key=lambda c_: c_["t"])
