"""s04 NIGHT (50-62). The plan becomes the night street, and the crew go down into the sewer.
  The pop-up (0-3): s03's tilt carries straight on (same speed at the cut) down to eye level. The
    table lamp goes out and the blue paper goes NAVY; the chess pieces sink into it and the walls
    rise out of their chalk lines; the crew rise out of the plan's route one per beat (the
    Knight, her, the Cracker) and set off west along the curb; the car, the portico, the front
    and the pediment pop up in turn. The route stays on the street as a ghost of chalk dots, and
    the dots brighten under the crew as they pass.
  The front street (3-6): at eye level the lamp, the clock, the moon and the neighbours pop up.
    The Knight walks past manhole A and turns to it; she stops at its far rim, the Cracker
    behind her. The camera pushes in. He bends and hooks the lid, heaves it up and drags it out
    of the hole (scrape), and lets it fall flat on the road (CLANK).
  The descent (6-8.5): they go down one per beat, her first (the stopwatch appears and starts:
    film 46.0), the Cracker, the Knight. The camera sinks through the road and the street opens
    into its section: the shaft, the long pipe, the drips. Each lands in the water at the foot of
    the rungs (splash), and the route's dots light down the shaft as she reaches them.
  The sewer (8.5-12): east along the pipe through the water, her first, the dots brightening
    under her. The bank's wing opens in a cutaway round the store room; she climbs the hatch
    shaft, pushes the hatch up (creak) and it falls open (thud): she comes up into the bank.
"""
import math
from functools import lru_cache

import cairo

from engine import bass
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross import bank as Bk
from films.double_cross import cast as C
from films.double_cross import kit as K
from films.double_cross import plan as P

# ---------------------------------------------------------------------------- beats
SHOTS = ((0.0, "tilt down into the street"), (3.0, "the front street"), (5.75, "the descent"), (8.2, "the sewer"))
TILT_T1 = 3.0                   # the tilt reaches eye level
T_NIGHT = (0.2, 2.4)            # the paper goes NAVY
T_LAMP = (0.2, 1.4)             # the table lamp goes out
T_WALLS = (0.3, 2.8)            # the walls rise out of their chalk lines
SINK = {"pawn": 0.15, "queen": 0.25, "bishop": 0.35, "knight": 0.45}     # the pieces sink into the paper
RISE = {"knight": 0.5, "architect": 1.0, "cracker": 1.5}                 # the crew rise from the route
POPS = {"portico": 1.6, "facade": 1.75, "car": 1.9, "pediment": 2.2, "clock": 2.5, "lamp": 3.0, "moon": 3.5,
        "neighbours": 3.5, "alley": 3.65}
POP_DUR = 0.35
T_TURN = 3.5                    # the Knight, past the manhole, turns to it ...
T_HOOK = 4.6                    # ... bends and hooks the lid
T_LIFT = 4.9                    # scrape: he heaves it up and drags it out of the hole
T_DROP = 5.35                   # he lets it go ...
T_CLANK = 5.5                   # ... CLANK: it falls flat on the road
DOWN = {"architect": 6.0, "cracker": 6.5, "knight": 7.0}                 # they go down one per beat
CLIMB = 1.5                     # s from the road to the water
PIPE_GO = {"cracker": 8.4, "knight": 9.0}                                # they set off along the pipe after her
T_CUT = (5.75, 7.1)             # the street opens into its section
T_CLOCK = 6.0                   # the stopwatch appears and starts (film 46.0 = K.HEIST_T0)
T_WINDOW = (9.8, 10.6)          # a cutaway window opens in the wing round the store room
T_UP = 10.4                     # she climbs the hatch shaft ...
T_CREAK = 11.2                  # ... pushes the hatch up (creak) ...
T_THUD = 11.5                   # ... and it falls open (thud)
STEP_MARKS = (("1", (184.0, 84.0), T_CLANK), ("2", (392.0, 84.0), T_UP))   # the plan's steps, on the section

# ---------------------------------------------------------------------------- places
ROUTE_Y = 1368.0                # Plan A's way along the street (plan y): the crew walk on it
FACADE_Y = 1300.0               # the bank's front (plan y)
CAR_Y = 1400.0
KN_STOP = 155.0                 # the Knight stops past the manhole (pelvis, set px) and turns back
HER_STOP = 300.0                # she stops at its east rim
CR_STOP = 360.0                 # the Cracker behind her
SHAFT_X = float(Bk.MANHOLE_X)
HATCH_X = float(Bk.HATCH_X)
STOPWATCH = ((930.0, 190.0), 62.0)

# the tilt: s03's camera carries on from P.HANDOFF_34 at s03's end rates, down to eye level
TILT_FROM = P.HANDOFF_34.tuple()                            # (cx, cy, zoom, phi, yaw, fx, fy)
TILT_RATE = (2.0, 30.0, 0.055, -15.0, 0.0, 0.0, 0.0)        # s03's END_RATE; fx, fy were fixed
TILT_TO = (545.0, 1300.0, 1.15, 0.0, 0.0, 540.0, 1480.0)
EYE = Bk.eye_cam(P.PlanCam(*TILT_TO))                       # the same view as a set camera

# the camera on the street and below it: (t, (x, y, zoom), ease into this key)
CAM_KEYS = ((TILT_T1, EYE.tuple(), None),
            (3.55, EYE.tuple(), None),
            (4.5, (262.0, -150.0, 1.9), "inout"),           # he turns to the manhole: push in, landing on the beat
            (5.75, (262.0, -150.0, 1.9), None),
            (7.75, (300.0, 215.0, 2.0), "inout"),           # sink through the road with them
            (8.2, (300.0, 215.0, 2.0), None),
            (10.5, (425.0, 215.0, 2.0), "inout"),           # east along the pipe
            (11.8, (450.0, -40.0, 2.0), "inout"),           # up the hatch shaft into the bank
            (12.0, (450.0, -40.0, 2.0), None))


def motion_blur(t, T):
    return 1


# ============================================================================ cameras
def tilt_cam(t):
    """The plan camera during the tilt: each of (cx, cy, zoom, phi, yaw, fx, fy) on a cubic from
    P.HANDOFF_34 (leaving at s03's end rates) to eye level (arriving at rest)."""
    if t >= TILT_T1:
        return P.PlanCam(*TILT_TO)
    T = TILT_T1
    u = max(0.0, t) / T
    h00, h10, h01 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2
    return P.PlanCam(*(h00 * a + h10 * T * m + h01 * b for a, m, b in zip(TILT_FROM, TILT_RATE, TILT_TO)))


TiltSet = Bk.TiltSet


def cam_at(t):
    """The set camera from TILT_T1 on (Bk.Cam)."""
    t = clamp(t, CAM_KEYS[0][0], CAM_KEYS[-1][0])
    for (t0, a, _), (t1, b, e) in zip(CAM_KEYS, CAM_KEYS[1:]):
        if t <= t1:
            u = clamp((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return Bk.Cam.lerp(Bk.Cam(*a), Bk.Cam(*b), ease(e, u) if e else u)
    return Bk.Cam(*CAM_KEYS[-1][1])


# ============================================================================ the crew
def _seg(name, s0, s1, at, speed=1.0, **kw):
    return C.Seg(C.clip(name), s0, s1, at=at, speed=speed, **kw)


@lru_cache(maxsize=None)
def perfs():
    """Every performance in the scene, and where each walk is drawn from (set px)."""
    d = {}
    # the walk in along the curb, west (facing -1); each holds a waiting pose at the end
    d["knight_w"] = C.perf("knight", [_seg("17_08", 1.5, 5.0, 0.65, 1.25)], facing=-1)
    d["architect_w"] = C.perf("architect", [_seg("17_03", 1.0, 3.6, 1.15, 1.0),
                                            _seg("104_02", 5.7, 7.3, 3.75, 0.55, travel=0.0, blend=0.4)], facing=-1)
    # the Cracker creeps in hunched, straightens (an old man's stoop) to wait, and walks up to the
    # rim as she goes down
    cr_end = 1.65 + 2.5 / 0.95
    up_end = DOWN["architect"] - 0.15 + 0.8 / 1.6
    d["cracker_w"] = C.perf("cracker", [_seg("77_14", 1.5, 4.0, 1.65, 0.95),
                                        _seg("104_02", 5.7, 7.3, cr_end, 0.55, travel=0.0, blend=0.5, lean=16.0),
                                        _seg("104_02", 1.0, 1.8, DOWN["architect"] - 0.15, 1.6, blend=0.25),
                                        _seg("104_02", 5.7, 5.9, up_end, 0.2, travel=0.0, blend=0.15, lean=10.0)],
                            facing=-1)
    # the Knight turned back to the manhole (facing +1): the bend and the heave, then two steps to the rim
    d["knight_e"] = C.perf("knight", [_seg("26_10", 0.6, 2.4, T_TURN, 1.6),
                                      _seg("26_10", 2.4, 3.8, T_LIFT - 0.05, 1.6, blend=0.05),
                                      _seg("17_08", 1.5, 3.4, 5.75, 1.3, blend=0.3)], facing=1)
    # east along the pipe, in the water: she sets off at once; the others stand a moment where they
    # land (spacing the file out), then follow
    d["architect_p"] = C.perf("architect", [_seg("104_02", 1.0, 4.0, DOWN["architect"] + CLIMB + 0.1, 1.2)], facing=1)
    d["cracker_p"] = C.perf("cracker", [_seg("104_02", 5.7, 5.9, DOWN["cracker"] + CLIMB, 0.2, travel=0.0, blend=0.0, lean=8.0),
                                        _seg("104_02", 1.0, 3.75, PIPE_GO["cracker"], 1.15, blend=0.3)], facing=1)
    d["knight_p"] = C.perf("knight", [_seg("17_08", 5.7, 6.0, DOWN["knight"] + CLIMB, 0.2, travel=0.0, blend=0.0),
                                      _seg("17_08", 1.5, 4.0, PIPE_GO["knight"], 1.45, blend=0.3)], facing=1)
    # where the walks in are drawn from: each stops on its mark
    stops = {"knight": (KN_STOP, 0.65 + 3.5 / 1.25), "architect": (HER_STOP, 3.75), "cracker": (CR_STOP, cr_end)}
    for who, (x, t_end) in stops.items():
        d[who + "_x"] = x - d[who + "_w"](t_end)[0]["pelvis"][0] * Bk.FIG_S
    return d


def _px(who, kind, t):
    """A walker's pelvis (set px) at t."""
    d = perfs()
    return d[who + "_x"] + d[who + "_" + kind](t)[0]["pelvis"][0] * Bk.FIG_S


def _step_back(t):
    """The Knight shuffles back as he heaves the lid out (set px)."""
    return -20.0 * ease("inout", clamp((t - T_LIFT - 0.05) / 0.45))


@lru_cache(maxsize=512)
def _knight_hand(tt):
    """The Knight's near hand (set px) as the mocap has it, while he is turned to the lid."""
    st, pose = perfs()["knight_e"](tt)
    surf = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    out = C.draw(cairo.Context(surf), "knight", st, pose, KN_STOP + _step_back(tt), 0.0, Bk.FIG_S, 1, rim=False)
    return out["hand_near"]


def lid_at(tt):
    """(grip, (pivot_x, angle)): where his hand holds the lid's raised edge, and the lid. It is
    dragged by his hand: the grip goes from the edge at rest to his rising hand, the lid's far
    edge sliding along the road behind it; when he lets go it falls flat."""
    rest = Bk.lid_edge(0.0)
    if tt < T_LIFT:
        return rest, (Bk.LID_HOME, 0.0)
    if tt < T_DROP:
        h = _knight_hand(tt)
        k = ease("inout", clamp((tt - T_LIFT) / 0.25))
        g = (lerp(rest[0], h[0], k), lerp(rest[1], h[1], k))
        hh = clamp(rest[1] - g[1], 0.0, 0.9 * Bk.LID_L)
        return g, (g[0] + math.sqrt(Bk.LID_L ** 2 - hh ** 2), math.degrees(math.asin(hh / Bk.LID_L)))
    g, (px, ang) = lid_at(T_DROP - 1e-6)
    f = clamp((tt - T_DROP) / (T_CLANK - T_DROP))
    return g, (px - 6.0 * f, ang * (1.0 - f * f))


def _descent(t, who, x0, facing):
    """(x, h) of a climber going down shaft A: steps in over the hole from x0, then down the rungs."""
    t0 = DOWN[who]
    k = clamp((t - t0) / 0.15)
    h = lerp(Bk.WATER, Bk.WATER - Bk.RUNG_STEP, k) if k < 1.0 else \
        lerp(Bk.WATER - Bk.RUNG_STEP, 0.0, clamp((t - t0 - 0.15) / (CLIMB - 0.15)))
    return lerp(x0, SHAFT_X + 2.0 * facing, ease("inout", k)), h


def _up(t):
    """How far up the hatch shaft she has climbed (h above the water)."""
    return lerp(0.0, Bk.WATER + 4.0, clamp((t - T_UP) / 1.5))


def crew(tt):
    """[(who, st, pose, x, foot_y, facing, where)] at (twos) time tt, back to front. where:
    'street', 'shaft' (going down shaft A), 'pipe' (in the water) or 'hatch' (up the hatch)."""
    d = perfs()
    out = []
    for who in ("cracker", "architect", "knight"):
        down = DOWN[who]
        if tt < RISE[who]:
            continue
        if who == "knight" and T_TURN <= tt < down:
            st, pose = d["knight_e"](tt)
            x = KN_STOP + _step_back(tt)
            if T_HOOK - 0.2 <= tt < T_DROP:                     # his near hand on the lid's edge
                g, _ = lid_at(tt)
                if tt < T_HOOK:
                    h = _knight_hand(tt)
                    k = ease("inout", (tt - T_HOOK + 0.2) / 0.2)
                    g = (lerp(h[0], g[0], k), lerp(h[1], g[1], k))
                pose.arms["near"] = ("ik", ((g[0] - x) / Bk.FIG_S, g[1] / Bk.FIG_S))
            pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)
            out.append((who, st, pose, x, 0.0, 1, "street"))
            continue
        if tt < down:
            st, pose = d[who + "_w"](tt)
            if who == "knight":
                pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)
            out.append((who, st, pose, d[who + "_x"], 0.0, -1, "street"))
            continue
        if tt < down + CLIMB:
            facing = 1 if who == "knight" else -1
            if who == "knight":
                x0 = KN_STOP + _step_back(down) + d["knight_e"](down)[0]["pelvis"][0] * Bk.FIG_S
            else:
                x0 = d[who + "_x"] + d[who + "_w"](down)[0]["pelvis"][0] * Bk.FIG_S
            x, h = _descent(tt, who, x0, facing)
            st, pose = Bk.ladder_pose(who, h, facing=facing)
            if who == "knight":
                pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)
            out.append((who, st, pose, x, Bk.WATER, facing, "shaft"))
            continue
        if who == "architect" and tt >= T_UP:
            st, pose = Bk.ladder_pose(who, _up(tt), facing=1)
            out.append((who, st, pose, HATCH_X - 6.0, Bk.WATER, 1, "hatch"))
            continue
        st, pose = d[who + "_p"](tt)
        if who == "knight":
            pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)
        out.append((who, st, pose, SHAFT_X, Bk.WATER + 8.0, 1, "pipe"))
    order = {"street": 0, "shaft": 1, "pipe": 1, "hatch": 1}
    return sorted(out, key=lambda r: order[r[6]])


def _rise(who, t):
    return clamp((t - RISE[who]) / 0.3)


# ============================================================================ the ghost route
STREET_PTS = Bk.ROUTE_STREET                         # along the curb from the car to manhole A (set px)
STREET_GAP = 22.0
IN_GAP = 22.0


@lru_cache(maxsize=1)
def _street_lit():
    """{dot x: the time it lit}: a dot lights when one of the crew first walks over it."""
    xs = []
    s = STREET_GAP * 0.5
    L = STREET_PTS[0][0] - STREET_PTS[1][0]
    while s < L - 4.0:
        xs.append(STREET_PTS[0][0] - s)
        s += STREET_GAP
    lit = {}
    for who in ("knight", "architect", "cracker"):
        x_rise = _px(who, "w", RISE[who])
        t = RISE[who]
        while t < DOWN[who]:
            x = _px(who, "w", t) if who != "knight" or t < T_TURN else KN_STOP
            for dx in xs:
                if x <= dx <= x_rise + 6.0 and dx not in lit:
                    lit[dx] = t
            t += 1.0 / 24.0
    return lit


def _street_dot_t(s):
    x = STREET_PTS[0][0] - s
    best = None
    for dx, t in _street_lit().items():
        if abs(dx - x) < 1.0:
            best = t
    return 1e9 if best is None else best


@lru_cache(maxsize=1)
def _her_way():
    """[(t, s)]: how far along Bk.ROUTE_IN_E she has come (set px of the route), sampled."""
    pts = Bk.ROUTE_IN_E
    seg = [K.poly_len(pts[:i + 1]) for i in range(len(pts))]
    out = []
    t = DOWN["architect"]
    while t <= 12.05:
        tt = K.twos(t)
        rows = {r[0]: r for r in crew(tt)}
        who, st, pose, x, fy, fc, where = rows["architect"]
        if where == "shaft":
            _, h = _descent(t, "architect", 0.0, -1)
            s = clamp(Bk.WATER - h + 8.0, 0.0, seg[1])
        elif where == "pipe":
            px = x + st["pelvis"][0] * Bk.FIG_S
            s = seg[1] + clamp(px - SHAFT_X, 0.0, HATCH_X - SHAFT_X)
        else:
            s = seg[2] + clamp(_up(t) - 14.0, 0.0, seg[3] - seg[2])
        out.append((t, max(s, out[-1][1] if out else 0.0)))
        t += 1.0 / 24.0
    return out


def _her_s(t):
    way = _her_way()
    if t <= way[0][0]:
        return 0.0
    for (t0, s0), (t1, s1) in zip(way, way[1:]):
        if t <= t1:
            return lerp(s0, s1, (t - t0) / (t1 - t0))
    return way[-1][1]


def _her_s_t(s):
    for t, si in _her_way():
        if si >= s:
            return t
    return 1e9


# ============================================================================ the tilt (0-3)
WALL_RISE = {"ext": Bk.FACADE_H, "vault": Bk.VAULT_H + 30.0, "int": Bk.ROOM_H}


def _edged(c, pts, color, edge, ew, ea):
    if ea > 0.0:
        c.save()
        c.new_path()
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        c.close_path()
        c.set_source_rgba(*edge, ea)
        c.set_line_width(ew)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.stroke()
        c.restore()
    bass.fill_polys(c, [pts], color)


def _walls(c, pc, t):
    """The plan's walls rising out of their chalk lines into the bank (frame px): the outer walls
    to the cornice, the rooms and the vault to the ceiling; chalk-white as they leave the paper,
    stone as they rise, edged in chalk that fades."""
    g = ease("inout", clamp((t - T_WALLS[0]) / (T_WALLS[1] - T_WALLS[0])))
    if g <= 0.0:
        return
    a = math.radians(pc.yaw)
    V = pc.to_view
    st = clamp(g * 4.0)
    cols = {"ext": (Bk.STONE, Bk.STONE_SH), "vault": (lerp(K.STEEL, K.INK, 0.35), lerp(K.STEEL, K.INK, 0.55)),
            "int": (lerp(K.NAVY, K.STEEL, 0.3), lerp(K.NAVY, K.STEEL, 0.15))}
    top = lerp(K.PAPER, Bk.STONE_DK, g)
    ea = 0.85 * (1.0 - g) + 0.12
    boxes = sorted(P.WALLS, key=lambda b: pc.depth(((b[0][0] + b[0][2]) / 2.0, (b[0][1] + b[0][3]) / 2.0)))
    for (x0, y0, x1, y1), kd in boxes:
        z = WALL_RISE[kd] * g
        face, side = (lerp(K.PAPER, col, st) for col in cols[kd])
        faces = []
        if math.cos(a) > 0:
            faces.append(([V((x0, y1)), V((x1, y1)), V((x1, y1), z), V((x0, y1), z)], face))
        if math.sin(a) > 1e-3:
            faces.append(([V((x1, y1)), V((x1, y0)), V((x1, y0), z), V((x1, y1), z)], side))
        elif math.sin(a) < -1e-3:
            faces.append(([V((x0, y0)), V((x0, y1)), V((x0, y1), z), V((x0, y0), z)], side))
        faces.append(([V((x0, y0), z), V((x1, y0), z), V((x1, y1), z), V((x0, y1), z)], top))
        for pts, col in faces:
            _edged(c, bass.orient(pts, True), col, K.PAPER, 2.0, ea)


def _pops(t):
    return {k: clamp((t - t0) / POP_DUR) for k, t0 in POPS.items()}


def _street_dots(c, t, to_frame, alpha=1.0):
    """The ghost of the route along the curb (dots stay on the world; frame-px size)."""
    lit = _street_lit()

    def on(s):
        x = STREET_PTS[0][0] - s
        for dx, t0 in lit.items():
            if abs(dx - x) < 1.0:
                return 1.0 if t >= t0 else 0.0
        return 0.0

    Bk.ghost_route(c, STREET_PTS, on, gap=STREET_GAP, r=5.5, ghost=0.3, seed=41, t=t, lit_t=_street_dot_t,
                   xf=to_frame, alpha=alpha)


def _tilt(c, t, tt):
    pc = tilt_cam(t)
    un = ease("inout", clamp((t - T_NIGHT[0]) / (T_NIGHT[1] - T_NIGHT[0])))
    lamp_a = 1.0 - ease("inout", clamp((t - T_LAMP[0]) / (T_LAMP[1] - T_LAMP[0])))
    on_plan = None
    if un > 0.0:
        def on_plan(c):                                  # night falls on the paper; the routes stay, a ghost
            x0, y0, x1, y1 = P.SHEET
            bass.fill_polys(c, [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], K.NAVY, 0.84 * un)
            K.route(c, P.ROUTE_IN, 1.0, K.PAPER, seed=3, alpha=0.42 * un)
            K.route(c, P.ROUTE_OUT[6:], 1.0, K.PAPER, seed=4, alpha=0.42 * un)
    P.table(c, pc, lamp_a, 1.0, 1.0, on_plan=on_plan)
    ea = ease("inout", clamp((t - 1.2) / 1.4))           # the earth under the street comes up black
    if ea > 0.0:
        a, b = pc.to_view((-3000.0, P.SHEET[3])), pc.to_view((4000.0, P.SHEET[3]))
        bass.fill_polys(c, [bass.orient([a, b, (b[0], 4000.0), (a[0], 4000.0)], True)], Bk.EARTH, ea)
    # the pieces sink into the paper (the knight, in the street, after the walls)
    pieces = sorted(P.PIECES_A, key=lambda it: pc.depth(it[1]))
    for kind, p, col, edge, fc in pieces:
        if kind != "knight":
            _sunk_piece(c, pc, kind, p, col, edge, fc, t)
    _walls(c, pc, t)
    pops = _pops(t)
    with TiltSet(pc, FACADE_Y).on(c):
        Bk.facade(c, t, pops, chalk=_chalk(t))
    if t > 2.5:                                          # the road line and the shut lid come up last
        with TiltSet(pc, ROUTE_Y).on(c):
            u = clamp((t - 2.5) / 0.5)
            Bk.band(c, (-400.0, 1.0), (1500.0, 1.0), 4.0, lerp(K.STEEL, K.NAVY, 0.25), seed=711, alpha=u)
        with TiltSet(pc, P.MANHOLE_A[1]).on(c):
            Bk.manhole_lid(c, 0.0)
    for kind, p, col, edge, fc in pieces:
        if kind == "knight":
            _sunk_piece(c, pc, kind, p, col, edge, fc, t)
    ga = clamp((t - 0.3) / 0.5)                          # the route along the curb, a ghost on the world
    if ga > 0.0:
        _street_dots(c, t, lambda q: pc.to_view((q[0], ROUTE_Y), -q[1]), ga)
    ts = TiltSet(pc, ROUTE_Y, stand=True)
    with ts.on(c):
        _figures(c, tt, t, ts.zoom, tilt=True)
    with TiltSet(pc, CAR_Y).on(c):
        Bk.car(c, t, 0.0, pops["car"])


def _chalk(t):
    return clamp((t - 2.0) / 0.3) * (1.0 - clamp((t - 2.7) / 0.6))


def _sunk_piece(c, pc, kind, p, col, edge, fc, t):
    k = 1.0 - ease("in", clamp((t - SINK[kind]) / 0.35))
    if k * 100.0 >= 1.0:
        P.piece_on(c, pc, kind, p, 100.0 * k, col, edge, facing=fc, shadow=0.38 * k)


# ============================================================================ the figures
def _figures(c, tt, t, zoom, tilt=False, cut=1.0, window=0.0):
    """The crew, drawn in set px (inside the camera)."""
    for who, st, pose, x, fy, facing, where in crew(tt):
        if tilt and where != "street":
            continue
        rise = _rise(who, t)
        c.save()
        if where in ("shaft", "pipe"):
            rects = Bk.open_rects(cut)
        elif where == "hatch":
            rects = [r for r in Bk.open_rects(1.0, above=False)] + [Bk.window_rect(window)]
        else:
            rects = None
        if rects:
            c.new_path()
            for x0, y0, x1, y1 in rects:
                c.rectangle(x0, y0, x1 - x0, y1 - y0)
            c.clip()
        with Bk.popped(c, fy, rise) as ok:
            if ok:
                C.draw(c, who, st, pose, x, fy, Bk.FIG_S, facing, bg=K.NAVY, rim_w=4.0 / zoom)
        c.restore()


def _splashes(c, cam, t):
    for who, t0 in DOWN.items():
        tb = t0 + CLIMB
        if tb <= t < tb + 0.7:
            Bk.splash(c, cam, (SHAFT_X, Bk.WATER), t, tb, 1.3)
    for t0, x in water_steps():
        if t0 <= t < t0 + 0.6:
            Bk.splash(c, cam, (x, Bk.WATER), t, t0, 0.7)


@lru_cache(maxsize=1)
def water_steps():
    """[(t, x)]: every footstep in the water along the pipe."""
    out = []
    d = perfs()
    for who in ("architect", "cracker", "knight"):
        perf = d[who + "_p"]
        for t, side, fx in Bk.footfalls(perf, perf.segs[0].at, perf.segs[-1].end):
            if who == "architect" and t >= T_UP:
                continue
            out.append((t, SHAFT_X + fx * Bk.FIG_S))
    return sorted(out)


# ============================================================================ the street and the sewer (3-12)
def _cut(t):
    return ease("inout", clamp((t - T_CUT[0]) / (T_CUT[1] - T_CUT[0])))


def _window(t):
    return clamp((t - T_WINDOW[0]) / (T_WINDOW[1] - T_WINDOW[0]))


def _hatch(t):
    return clamp((t - T_CREAK) / (T_THUD - T_CREAK))


def _marks(c, cam, t):
    """The plan's own marks on the world: its 'down here' chevron over the open manhole while they
    go down, and the circled steps (1) at the manhole and (2) at the hatch as they reach them
    (the same hand as on the plan: s03's seeds)."""
    u = clamp((t - T_CLANK + 0.05) / 0.3)
    fade = 1.0 - clamp((t - DOWN["knight"] - 0.3) / 0.4)
    if u > 0.0 and fade > 0.0:
        g = ease("outback", u) if u < 1.0 else 1.0
        K.chevron(c, cam.to_frame((SHAFT_X, -38.0)), 46.0 * g, (0.0, 1.0), K.PAPER, width=6.0, seed=131, alpha=0.95 * fade)
    for txt, p, t0 in STEP_MARKS:
        u = clamp((t - t0) / 0.45)
        if u > 0.0:
            K.circled(c, txt, cam.to_frame(p), 30.0, u, K.PAPER, width=5.0, seed=9 + int(txt), alpha=0.9)


def _street(c, t, tt):
    cam = cam_at(t)
    cut, window = _cut(t), _window(t)
    _, lid = lid_at(tt)
    Bk.front_street(c, cam, t, pop=_pops(t), lid=lid, cut=cut, chalk=_chalk(t), window=window, hatch=_hatch(t))
    _street_dots(c, t, cam.to_frame)
    _marks(c, cam, t)
    if t >= DOWN["architect"]:                           # down the shaft, along the pipe, up the hatch
        s = _her_s(t)
        Bk.ghost_route(c, Bk.ROUTE_IN_E, lambda q: 1.0 if q <= s else 0.0, gap=IN_GAP, r=5.5, ghost=0.3, seed=43,
                       t=t, lit_t=_her_s_t, xf=cam.to_frame, alpha=clamp((t - DOWN["architect"]) / 0.4))
    with cam.on(c):
        _figures(c, tt, t, cam.zoom, cut=cut, window=window)
    if t >= DOWN["architect"] + CLIMB - 0.2:
        Bk.water(c, cam, t)
    _splashes(c, cam, t)


# ============================================================================ render
def render(f, t, T):
    un = ease("inout", clamp((t - T_NIGHT[0]) / (T_NIGHT[1] - T_NIGHT[0])))
    K.scene_setup(f, lerp(K.DEEP, K.NAVY, un))
    tt = K.twos(t)
    with f.screen() as c:
        if t < TILT_T1:
            _tilt(c, t, tt)
        else:
            _street(c, t, tt)
        u = clamp((t - T_CLOCK) / 0.4)
        if u > 0.0:
            K.stopwatch(c, STOPWATCH[0], STOPWATCH[1], K.heist_beats(T.start + t), u=u)


# ============================================================================ cues
def _pan_x(t, x, plan_y=ROUTE_Y):
    """Where set x is across the frame at t (-1 left .. 1 right)."""
    if t < TILT_T1:
        fx = TiltSet(tilt_cam(t), plan_y).to_frame((x, 0.0))[0]
    else:
        fx = cam_at(t).to_frame((x, 0.0))[0]
    return round(clamp((fx - 540.0) / 540.0, -1.0, 1.0), 2)


def _first(fn, t0, t1, step=1.0 / 24.0):
    t = t0
    while t <= t1:
        if fn(t):
            return round(t, 4)
        t += step
    return None


def cues(T):
    d = perfs()
    out = [Cue(0.0, "the tilt carries on from the plan: a rising paper whoosh as the walls rise out of the chalk",
               gain_db=-12, dur=2.8),
           Cue(T_LAMP[0], "the table lamp clicks off; night air comes up (a distant city, a far siren, wind)", gain_db=-20,
               dur=T.duration - T_LAMP[0]),
           Cue(min(SINK.values()), "the four chess pieces sink into the paper (soft paper slides)", gain_db=-20, dur=0.7)]
    for who, t0 in RISE.items():
        out.append(Cue(t0, f"a paper pop-up snap: the {'Knight' if who == 'knight' else 'Architect' if who == 'architect' else 'Cracker'} "
                           "rises out of the plan", gain_db=-15, pan=_pan_x(t0, _px(who, "w", t0))))
    xs = {"car": Bk.CAR_X, "portico": 735.0, "facade": 365.0, "pediment": 735.0, "clock": Bk.CLOCK_AT[0],
          "lamp": Bk.LAMP_X, "moon": Bk.MOON_AT[0], "neighbours": 540.0, "alley": Bk.ALLEY_X[0]}
    for k, t0 in sorted(POPS.items(), key=lambda kv: kv[1]):
        out.append(Cue(t0, f"a card pop-up snap: the {k} stands up", gain_db=-17 if k in ("car", "facade", "portico") else -21,
                       pan=_pan_x(t0, xs[k], FACADE_Y)))
    # footsteps on the street
    walks = (("knight", "knight_w", "a heavy shoe on the paving (he walks west)", -15),
             ("architect", "architect_w", "a soft creeping step (her)", -24),
             ("cracker", "cracker_w", "an old man's shuffling step (the Cracker)", -23))
    for who, key, text, g in walks:
        perf = d[key]
        t_end = T_TURN if who == "knight" else DOWN[who]
        for t0, side, fx in Bk.footfalls(perf, RISE[who] + 0.3, t_end):
            out.append(Cue(t0, "footstep: " + text, gain_db=g, pan=_pan_x(t0, d[who + "_x"] + fx * Bk.FIG_S)))
    for t0, side, fx in Bk.footfalls(d["knight_e"], 5.75, DOWN["knight"] - 0.05):
        out.append(Cue(t0, "footstep: the Knight steps back to the manhole's rim (heavy)", gain_db=-16,
                       pan=_pan_x(t0, KN_STOP - 20.0 + fx * Bk.FIG_S)))
    out.append(Cue(T_TURN, "a heavy coat rustles: the Knight turns back to the manhole", gain_db=-22, pan=_pan_x(T_TURN, KN_STOP)))
    out.append(Cue(T_HOOK, "iron tick: his fingers hook the lid's edge; a low grunt", gain_db=-16, pan=_pan_x(T_HOOK, 215.0)))
    t_scr = _first(lambda t: lid_at(K.twos(t))[1][1] > 1.0, T_LIFT, T_DROP) or T_LIFT
    out.append(Cue(t_scr, "iron scrape: the manhole lid levered up and dragged out of the hole across the road", gain_db=-9,
                   pan=_pan_x(t_scr, 240.0), dur=T_DROP - t_scr))
    out.append(Cue(T_CLANK, "CLANK: the iron lid falls flat on the road (it rings)", gain_db=-5, pan=_pan_x(T_CLANK, 180.0)))
    # the descent
    out.append(Cue(T_CUT[0], "a low whoosh: the camera sinks through the road; the street opens into the sewer below",
                   gain_db=-14, dur=2.0))
    out.append(Cue(T_CLOCK, "the heist clock starts: a dry woodblock tick on every beat (it runs into s07)", gain_db=-14,
                   pan=0.72))
    for who, t0 in DOWN.items():
        name = {"knight": "the Knight", "architect": "she", "cracker": "the Cracker"}[who]
        out.append(Cue(t0, f"a shoe on the first iron rung: {name} goes down the manhole", gain_db=-14, pan=_pan_x(t0, SHAFT_X)))
        out.append(Cue(t0 + 0.2, f"a quick run of iron rung steps going down (low; {name})", gain_db=-22,
                       pan=_pan_x(t0, SHAFT_X), dur=CLIMB - 0.25))
        out.append(Cue(t0 + CLIMB, f"splash: {name} steps off the ladder into the sewer water", gain_db=-12,
                       pan=_pan_x(t0 + CLIMB, SHAFT_X)))
    for t0, x in water_steps():
        out.append(Cue(t0, "a footstep in shallow water (sewer slosh)", gain_db=-21, pan=_pan_x(t0, x)))
    for t0, x in Bk.drip_times(T_CUT[0] + 0.6, T.duration, "main"):
        cam = cam_at(t0)
        x0, y0, x1, y1 = cam.view(0.0)
        if x0 <= x <= x1 and y0 <= Bk.WATER <= y1:
            out.append(Cue(t0, "a drip into still water (echoing in the pipe)", gain_db=-26, pan=_pan_x(t0, x)))
    out.append(Cue(T_WINDOW[0], "a soft chalk scratch: a cutaway window opens in the bank's wall", gain_db=-20,
                   pan=_pan_x(T_WINDOW[0], 340.0)))
    out.append(Cue(T_UP, "iron rung steps going up, quick and light (her)", gain_db=-22, pan=_pan_x(T_UP, HATCH_X),
                   dur=T.duration - T_UP))
    out.append(Cue(T_CREAK, "a long hinge creak: she pushes the hatch up", gain_db=-11, pan=_pan_x(T_CREAK, HATCH_X)))
    out.append(Cue(T_THUD, "thud: the hatch falls open on the store room floor", gain_db=-12, pan=_pan_x(T_THUD, HATCH_X - 30.0)))
    return out
