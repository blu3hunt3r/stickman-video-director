"""s09 PLAN B (108-124). The film rewinds to what we missed, and her tracing sheet shows Plan B.
  The rewind: under chalk streaks and a double chevron, the heist clock spinning back, the film
    runs backwards through s08, s07, s06, s05 and s04 into s03 and lands on the plant. Played
    forward: the Knight slams his piece down and her chalk, lifting off the vault, leaves the
    dot. Freeze: a lens snaps round the dot, on the sewer line inside the vault.
  Back again, to s02: his red look at the X, her white look at him. Freeze: a lens on her eye.
  The plan from above. Her tracing sheet unrolls down over it and Plan B is chalked on it in
    solid lines, the camera whipping from one to the next: (1) the trapdoor at the dot; (2) her
    route down through it, north along the branch to manhole B and off the sheet; (3) four
    police cars closing on his car; (4) a red X on the ruby box. Pull back: both plans at once.
  The vault by match light: she lifts the floor tile over the trapdoor; below is black. The
    Cracker stares, then grins. In section they drop through to the sewer and walk north, the
    solid route lighting ahead of her match.
REWIND / FREEZES say which scene the picture shows when (the mix runs the same film's sound
backwards and forwards to match).
"""
import glob
import importlib
import math
import os
from functools import lru_cache

import cairo

from engine import bass
from engine import paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue, SceneTiming
from films.double_cross import bank as Bk
from films.double_cross import cast as C
from films.double_cross import faces as F
from films.double_cross import kit as K
from films.double_cross import plan as P
from films.double_cross.scenes import s02_crew as S2
from films.double_cross.scenes import s03_plan as S3

FILM = "double_cross"

# ============================================================================ the rewind
# (t0, t1, scene, scene t0, scene t1): from t0 to t1 the picture is that scene run from its t0
# to its t1 (backwards when t1 < t0)
REWIND = ((0.15, 0.55, "s08", 12.0, 0.0),
          (0.55, 0.95, "s07", 16.0, 0.0),
          (0.95, 1.35, "s06", 14.0, 0.0),
          (1.35, 1.75, "s05", 14.0, 0.0),
          (1.75, 2.15, "s04", 12.0, 0.0),
          (2.15, 2.45, "s03", 16.0, 12.0),
          (2.45, 2.75, "s03", 12.0, 10.05),
          (2.75, 3.5, "s03", 10.05, 10.8),         # played: his slam, her dot
          (4.2, 4.33, "s03", 10.8, 0.0),
          (4.33, 4.45, "s02", 12.0, 9.3),
          (4.45, 6.15, "s02", 9.3, 11.0))          # played: his look at the X, hers at him
# (t0, t1, scene, scene t): a frame held
FREEZES = ((0.0, 0.15, "s08", 12.0), (3.5, 4.2, "s03", 10.8), (6.15, 6.6, "s02", 11.0))
T_PLAY = 2.75
T_LENS1 = 3.55          # the lens on the dot
T_LENS2 = 6.05          # the lens on her eye

# ============================================================================ Plan B
T_PLAN = 6.6
T_SHEET = (6.6, 7.15)                    # the tracing sheet unrolls down over the plan
T_B1 = (7.4, 7.85)                       # (1) the trapdoor
T_B2 = (7.95, 8.9)                       # (2) her route
T_COPS = (9.15, 9.35, 9.55, 9.75)        # (3) the police cars, on the half beats
T_B4 = (10.12, 10.32)                    # (4) the red X
PLAN_KEYS = ((6.6, (540.0, 960.0, 1.0)), (7.1, (540.0, 960.0, 1.0)), (7.4, (455.0, 620.0, 2.1)),
             (7.95, (455.0, 620.0, 2.1)), (8.9, (300.0, 430.0, 1.85)), (9.1, (905.0, 1385.0, 1.8)),
             (9.95, (905.0, 1385.0, 1.8)), (10.12, (672.0, 534.0, 2.3)), (10.4, (672.0, 534.0, 2.3)),
             (10.9, (540.0, 960.0, 1.04)))
SHEET_B = (40.0, 120.0, 1064.0, 1800.0)  # her tracing sheet (plan px)
COPS = ((-1.0, 0.0, 100.0), (0.0, -1.0, 80.0), (1.0, 0.0, 100.0), (0.0, 1.0, 80.0))   # W, N, E, S of his car

# ============================================================================ the vault
T_VAULT = 10.9
T_TILE = (11.12, 11.8)                   # she lifts the tile and lays it aside: below is black
T_FACE = (11.92, 12.66)                  # the Cracker's face: he stares ...
T_GLINT = (12.0, 12.3)
T_GRIN = 12.28                           # ... and grins
T_SECTION = 12.66                        # back on the vault, the floor cut away under it
T_CUT = (12.7, 13.25)
T_RISE = (12.66, 13.15)                  # she gets up and steps into the hole
T_SLIDE = ((13.15, 13.8), (13.85, 14.45))   # down the ladder: her, him
T_TURN = (13.92, 14.1)                   # in the water she turns north (a cut-paper turn)
T_STEP_HIM = (13.25, 13.8)               # he steps to the hole
T_GO = (14.05, 14.55)                    # they set off north (left): her, him
T_REVEAL = (14.1, 15.7)                  # the cut runs on north ahead of her, to manhole B
T_LIT = (15.15, 15.75)                   # Plan B's line lights up the rest of the way, to the street
HER_U, HIM_U = 556.0, 652.0
TRAP = Bk.TRAP_U
FOOT_W = Bk.BRANCH_WATER + 8.0           # feet in the water
CAM_TILE = Bk.Cam(588.0, -84.0, 5.2)
CAM_SECT = Bk.Cam(560.0, 160.0, 2.25)
CAM_END = Bk.Cam(440.0, 10.0, 1.5)
WALK_V = 430.0                           # figure units / s, wading
ROUTE_Y = Bk.BRANCH_WATER - 14.0         # Plan B in section, at shin height
ROUTE_SEC = [(TRAP, Bk.VSLAB), (TRAP, ROUTE_Y), (Bk.MANHOLE_B_U, ROUTE_Y), (Bk.MANHOLE_B_U, -34.0)]
CUT_N = Bk.VAULT_U[0] - 30.0             # the floor cut's north edge ...
REVEAL_TO = 196.0                        # ... runs on north past manhole B

DIM_GOLD = lerp(K.INK, K.GOLD, 0.45)


def motion_blur(t, T):
    return 1


# ============================================================================ other scenes
_MODS = {}


def _scene(sid):
    """(module or None, SceneTiming) of another scene of the film."""
    if sid not in _MODS:
        here = os.path.dirname(os.path.abspath(__file__))
        paths = sorted(glob.glob(os.path.join(here, f"{sid}_*.py")))
        mod = importlib.import_module(f"films.{FILM}.scenes.{os.path.basename(paths[0])[:-3]}") if paths else None
        _MODS[sid] = (mod, SceneTiming(FILM, sid))
    return _MODS[sid]


def shown(t):
    """(kind, scene, scene t) the picture shows at t in the rewind, or None after it. kind:
    'rew' (running backwards), 'play' (forwards) or 'still'."""
    for a, b, sid, s0, s1 in REWIND:
        if a <= t < b:
            return ("rew" if s1 < s0 else "play"), sid, lerp(s0, s1, (t - a) / (b - a))
    for a, b, sid, st in FREEZES:
        if a <= t < b:
            return "still", sid, st
    return None


def _missing(f, sid):
    """A stand-in for a scene not written yet (never in the cut)."""
    K.scene_setup(f, K.NAVY)
    with f.screen() as c:
        c.set_source_rgba(*K.PAPER, 0.5)
        c.select_font_face("Sans")
        c.set_font_size(140.0)
        c.move_to(380.0, 1000.0)
        c.show_text(sid)


# ============================================================================ the rewind's marks
def _streaks(c, t, a=1.0):
    """Chalk streaks across the picture, new on every other frame: the tape scrubbing back."""
    k = int(K.twos(t) * 24.0 + 0.5)
    for i in range(7):
        y = K.H * hash01(k, i, 2101)
        x0 = K.W * (1.3 * hash01(k, i, 2102) - 0.3)
        L = 160.0 + 760.0 * hash01(k, i, 2103)
        K.chalk_line(c, [(x0, y), (x0 + L, y + 8.0 * (hash01(k, i, 2104) - 0.5))], 1.0, 2.0 + 6.0 * hash01(k, i, 2105),
                     K.PAPER, seed=2106 + i, alpha=a * (0.2 + 0.35 * hash01(k, i, 2107)))


def _chevrons(c, t, a=1.0):
    """The double chevron, pointing back, beating."""
    pulse = 1.0 + 0.1 * max(0.0, math.cos(2.0 * math.pi * t / (K.BEAT / 2.0)))
    for k, dx in enumerate((-50.0, 50.0)):
        K.chevron(c, (540.0 + dx * pulse, 300.0), 66.0 * pulse, (-1.0, 0.0), K.PAPER, width=13.0, seed=2110 + k,
                  alpha=a)


def _clock(c, ft, a=1.0):
    """The heist clock, at the film time the picture shows (so it spins back with it)."""
    K.stopwatch(c, (900.0, 230.0), 84.0, K.heist_beats(ft), K.PAPER, hand=K.RED if ft >= K.HEIST_STOP else None,
                seed=2120, alpha=a)


def _finder(c, a=1.0):
    """Chalk corners round the frame: this is a replay."""
    m, L = 54.0, 120.0
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        x = m if sx > 0 else K.W - m
        y = m if sy > 0 else K.H - m
        K.chalk_line(c, [(x, y + sy * L), (x, y), (x + sx * L, y)], 1.0, 7.0, K.PAPER, seed=2130 + i, alpha=0.8 * a)


def _dot_lens(c, t):
    """Frozen on the plant: a lens joins her dot to the plan, magnified: the dot sits on the
    sewer line inside the vault."""
    anchor = S3.cam_at(10.8).to_view(P.DOT, 0.0)
    centre = (770.0, 420.0)

    def inside(cc):
        lc = P.PlanCam(492.0, 584.0, 1.8, 90.0, 0.0, fx=centre[0], fy=centre[1])
        K.fill(cc, K.DEEP)
        P.table(cc, lc, 1.0, 1.0, 1.0)
        K.ripple(cc, lc.to_view(P.DOT), t, T_LENS1 + 0.12, K.GOLD, n=2, every=0.22, life=0.8, r0=12.0, r1=70.0, width=5.0)
    K.callout(c, anchor, centre, 200.0, inside, u=clamp((t - T_LENS1) / 0.3), color=K.PAPER, ring_w=9.0, dot_r=9.0,
              line_w=4.0, seed=2140)


@lru_cache(maxsize=1)
def _her_eye_s02():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, 8, 8)
    h = S2._people(cairo.Context(s), 11.0)["architect"]["head"]
    return (h[0] + 44.0, h[1] + 78.0)


def _eye_lens(c, t):
    """Frozen on her look: a lens on her eye. She saw him look."""
    anchor = _her_eye_s02()
    centre = (clamp(anchor[0] + 330.0, 240.0, 840.0), clamp(anchor[1] - 420.0, 240.0, 1680.0))

    def inside(cc):
        K.fill(cc, K.DEEP)
        K.pool(cc, (centre[0] + 190.0, centre[1] - 40.0), 300.0, 300.0, K.GOLD, 0.34, steps=4)
        s = 1.5
        eye = (centre[0] - 70.0, centre[1] - 10.0)
        at = (eye[0] - (466.0 - 400.0) * s, eye[1] + (860.0 - 298.0) * s)
        F.her(cc, at, s, look=0.9, t=t, edge=K.GOLD, squint=0.25)
        K.dot(cc, (eye[0] + 12.0 * s, eye[1] + 1.0 * s), 2.6 * s, K.RED, seed=2152)     # his red look, in her eye
        K.dotted(cc, (eye[0] + 30.0 * s, eye[1]), (centre[0] + 200.0, eye[1] - 4.0), K.PAPER, r=7.0, gap=24.0,
                 head=0.0, seed=2151)
    K.callout(c, anchor, centre, 190.0, inside, u=clamp((t - T_LENS2) / 0.3), color=K.PAPER, ring_w=9.0, dot_r=9.0,
              line_w=4.0, seed=2150)


def _rewind_marks(c, t, kind, sid, st, Ts):
    if kind == "rew":
        _streaks(c, t)
        _chevrons(c, t)
        _clock(c, Ts.start + st)
    elif kind == "play":
        _finder(c)
    else:
        if t < REWIND[0][0]:
            a = clamp((t - 0.04) / 0.08)
            _chevrons(c, t, a)
            _clock(c, Ts.start + st, a)
        elif sid == "s03":
            _finder(c)
            _dot_lens(c, t)
        else:
            _finder(c)
            _eye_lens(c, t)


# ============================================================================ Plan B
def plan_cam(t):
    keys = PLAN_KEYS
    v = keys[-1][1] if t >= keys[-1][0] else keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if a <= t < b:
            u = ease("inout3", (t - a) / (b - a))
            v = (lerp(va[0], vb[0], u), lerp(va[1], vb[1], u), math.exp(lerp(math.log(va[2]), math.log(vb[2]), u)))
            break
    return P.PlanCam(v[0], v[1], v[2], 90.0, 0.0)


def _sheet_dy(t):
    return -(SHEET_B[3] + 260.0) * (1.0 - ease("out3", clamp((t - T_SHEET[0]) / (T_SHEET[1] - T_SHEET[0]))))


def _tracing(c, t):
    """Her tracing sheet on the plan (plan px), unrolling down from the top, a roll at its
    foot until it lies flat."""
    x0, y0, x1, y1 = SHEET_B
    dy = _sheet_dy(t)
    top, bot = y0 + min(0.0, dy * 0.15), y1 + dy
    if bot <= top + 2.0:
        return
    q = [(x0, top), (x1, top), (x1, bot), (x0, bot)]
    bass.fill_polys(c, [bass.orient(q, True)], K.PAPER, 0.24)
    for i in range(110):                                   # the fibres in it
        fx = x0 + (x1 - x0) * hash01(i, 2201)
        fy = y0 + (y1 - y0) * hash01(i, 2202)
        if not top < fy < bot:
            continue
        ang = 2.0 * math.pi * hash01(i, 2203)
        L = 14.0 + 22.0 * hash01(i, 2204)
        bass.line_band(c, [(fx, fy), (fx + L * math.cos(ang), fy + L * 0.4 * math.sin(ang))], K.PAPER, width=1.4,
                       seed=2205 + i, alpha=0.18)
    for a, b in ((q[0], q[3]), (q[1], q[2])):
        bass.line_band(c, [a, b], K.PAPER, width=3.0, seed=2210, alpha=0.6)
    if bot < y1 - 1.0:                                     # the roll
        bass.fill_polys(c, [bass.orient(bass.capsule_pts((x0 - 6.0, bot), (x1 + 6.0, bot), 16.0, 16.0, cap=4), True)],
                        K.PAPER)
        bass.line_band(c, [(x0, bot + 7.0), (x1, bot + 7.0)], DIM_GOLD, width=4.0, seed=2211)


def _badge(c, text, p, u, seed):
    """Plan B's step numbers: solid chalk discs (Plan A's are rings)."""
    g = ease("outback", clamp(u))
    if g > 0.01:
        K.dot(c, p, 25.0 * g, K.PAPER, seed=seed)
        K.numeral(c, text, p, 30.0, K.DEEP, seed=seed + 1, scale=g)


def _trapdoor_b(c, t):
    u = clamp((t - T_B1[0]) / (T_B1[1] - T_B1[0]))
    if u <= 0.0:
        return
    x, y = P.TRAPDOOR
    h = 26.0
    K.chalk_rect(c, (x - h, y - h, x + h, y + h), u=ease("inout", clamp(u / 0.7)), width=6.0, color=K.PAPER, seed=2221)
    K.chalk_line(c, [(x - h, y + h), (x + h, y - h)], clamp((u - 0.7) / 0.3), 4.0, K.PAPER, seed=2222)
    _badge(c, "1", (x - 70.0, y - 58.0), (u - 0.55) / 0.45, 2223)


def _route_b(c, t):
    u = ease("inout", clamp((t - T_B2[0]) / (T_B2[1] - T_B2[0])))
    if u <= 0.0:
        return
    pts = P.ROUTE_B
    K.route(c, pts, u, K.PAPER, solid=True, width=7.0, head=30.0, seed=2231)
    at_b = K.poly_len(pts[:3]) / K.poly_len(pts)           # where the route reaches manhole B
    K.chalk_circle(c, P.MANHOLE_B, 24.0, u=clamp((u - at_b) / 0.15), width=5.0, color=K.PAPER, seed=2233)
    _badge(c, "2", (520.0, 420.0), (u - 0.3) / 0.25, 2234)


def _cops_b(c, t):
    """The police, at his car from the four streets: chalk cars sliding in nose first, like
    rooks, their bars flashing."""
    tint = lerp(K.BLUE, K.PAPER, 0.24)
    for i, (dx, dy, d1) in enumerate(COPS):
        k = t - T_COPS[i]
        g = ease("outback", clamp(k / 0.2))
        if k <= 0.0 or g < 1e-3:         # a zero scale is an invalid cairo matrix
            continue
        d = d1 + 90.0 * (1.0 - ease("out3", clamp(k / 0.32)))
        p = (P.CAR[0] + dx * d, P.CAR[1] + dy * d)
        ang = math.degrees(math.atan2(-dy, -dx))
        K.car(c, p, ang, 0.5 * g, tint, K.PAPER, ew=4.0)
        K.police_lights(c, p, ang, t, s=0.5 * g, beams=k > 0.2, seed=2240 + i)
        K.ripple(c, p, t, T_COPS[i] + 0.2, K.POLICE if i % 2 == 0 else K.RED, n=1, life=0.45, r0=16.0, r1=70.0,
                 width=4.0)
    _badge(c, "3", (P.CAR[0] - 150.0, P.CAR[1] - 120.0), (t - T_COPS[0]) / 0.3, 2249)


def _ruby_b(c, t):
    u = clamp((t - T_B4[0]) / (T_B4[1] - T_B4[0]))
    if u <= 0.0:
        return
    K.xmark(c, P.RUBY, 44.0, u, K.RED, width=10.0, seed=2251)
    if t >= T_B4[1]:
        K.ripple(c, P.RUBY, t, T_B4[1], K.RED, n=2, every=0.16, life=0.6, r0=20.0, r1=90.0, width=5.0)
    _badge(c, "4", (P.RUBY[0] + 76.0, P.RUBY[1] - 60.0), (u - 0.4) / 0.6, 2252)


def _plan_b(c, t):
    """On the plan (plan px): her tracing sheet, and Plan B on it."""
    _tracing(c, t)
    if t >= T_SHEET[1]:
        _trapdoor_b(c, t)
        _route_b(c, t)
        _cops_b(c, t)
        _ruby_b(c, t)


def _plan_frame(c, t):
    cam = plan_cam(t)
    K.fill(c, K.DEEP)
    P.table(c, cam, 1.0, 1.0, 1.0, on_plan=lambda cc: _plan_b(cc, t))


def plan_shot(c, t):
    """The plan from above; the camera's whips are smeared over the frame (box-averaged)."""
    a, b = plan_cam(t), plan_cam(t - 1.0 / 24.0)
    moved = math.hypot((a.cx - b.cx) * a.zoom, (a.cy - b.cy) * a.zoom)
    n = 1 if moved < 40.0 else 6
    if n == 1:
        _plan_frame(c, t)
        return
    for i in range(n):
        c.push_group()
        _plan_frame(c, t - i / (24.0 * n))
        c.pop_group_to_source()
        c.paint_with_alpha(1.0 / (i + 1))


# ============================================================================ the vault
def _tile_u(t):
    return ease("inout", clamp((t - T_TILE[0]) / (T_TILE[1] - T_TILE[0])))


def _tile_edge(g):
    """The lifting (north) edge of the floor tile at tile progress g (set px), as Bk._tile
    swings it: up on its south edge, then over and laid down south of the hole."""
    x0, x1 = Bk.TILE_U
    lift = clamp(g / 0.5)
    slide = clamp((g - 0.5) / 0.5)
    ang = math.radians(80.0 * ease("out3", lift) * (1.0 - ease("inout", slide)))
    px = x1 + 44.0 * ease("inout", slide)
    w = x1 - x0
    return (px - w * math.cos(ang), -1.0 - w * math.sin(ang))


def _ik(pt, x, floor, pel=0.0):
    """An IK target (figure units) for set point pt, for a figure drawn at x on floor (facing
    right; pel: the walker's pelvis x, figure units)."""
    return ("ik", ((pt[0] - x) / Bk.FIG_S + pel, (pt[1] - floor) / Bk.FIG_S))


_WALKERS = {}


def _walker(who):
    if who not in _WALKERS:
        t_go = T_GO[0] if who == "architect" else T_GO[1]
        _WALKERS[who] = pd.Walker(C.fig(who), 0.0, speed=((t_go, 0.0), (t_go + 0.3, WALK_V), (17.0, WALK_V)),
                                  t0=t_go - 1.0, t1=17.0)
    return _WALKERS[who]


def steps(who):
    """[(t, set x)]: her (or his) feet coming down in the water."""
    wk = _walker(who)
    t_go = T_GO[0] if who == "architect" else T_GO[1]
    x0 = TRAP + (6.0 if who == "architect" else -6.0)
    return [(tt, x0 - fx * Bk.FIG_S) for tt, side, fx in Bk.footfalls(lambda u: (wk.state(u), None), t_go, 16.0)]


def _wading(who, t, x0, t_land):
    """(state, pose, pelvis x) in the water after the drop: a landing dip, then walking north."""
    wk = _walker(who)
    st = wk.state(t)
    land = clamp((t - t_land) / 0.3)
    pose = pd.Pose(lean=5.0, head=-4.0, crouch=60.0 * math.sin(math.pi * land) * (1.0 - land * 0.5))
    return st, pose, st["pelvis"][0]


def her_state(t):
    """(x, floor y, state, pose, sx, match) for the Architect: sx is her horizontal scale (1 facing
    right, -1 left, between: the paper turn); match: where her match burns (set px)."""
    if t < T_RISE[0]:                                      # kneeling at the tile, the match raised
        g = _tile_u(t)
        st = C.standing("architect")
        pose = pd.Pose(lean=26.0, head=-22.0 + 10.0 * clamp(g / 0.4), crouch=150.0)
        hold = min(g, 0.34)
        e = _tile_edge(hold) if g > 0.0 else (Bk.TILE_U[0] - 2.0, -2.0)
        back = ease("inout", clamp((g - 0.34) / 0.3))
        rest = (HER_U + 22.0, -24.0)
        e = (lerp(e[0], rest[0], back), lerp(e[1], rest[1], back))
        m = (HER_U + 30.0, -62.0)
        pose.arms["near"] = _ik(e, HER_U, 0.0)
        pose.arms["far"] = _ik(m, HER_U, 0.0)
        return HER_U, 0.0, st, pose, 1.0, m
    x_ladder = TRAP - 6.0
    if t < T_SLIDE[0][0]:                                  # up, and into the hole
        u = ease("inout", clamp((t - T_RISE[0]) / (T_SLIDE[0][0] - T_RISE[0])))
        x = lerp(HER_U, x_ladder, u)
        st = C.standing("architect")
        pose = pd.Pose(lean=lerp(26.0, 6.0, u), head=lerp(-12.0, -18.0, u), crouch=150.0 * (1.0 - u))
        m = (lerp(HER_U + 30.0, x + 10.0, u), lerp(-62.0, -128.0, u))
        pose.arms["near"] = ("ang", lerp(30.0, 60.0, u), 20.0)
        pose.arms["far"] = _ik(m, x, 0.0)
        return x, 0.0, st, pose, 1.0, m
    d0, d1 = T_SLIDE[0]
    if t < d1:                                             # down the ladder (a sailor's slide)
        u = clamp((t - d0) / (d1 - d0))
        y = FOOT_W * u * u
        st, pose = Bk.ladder_pose("architect", 0.0, 1)
        m = (x_ladder + 10.0, y - 128.0)
        pose.arms["far"] = _ik(m, x_ladder, y)
        return x_ladder, y, st, pose, 1.0, m
    st, pose, pel = _wading("architect", t, x_ladder, d1)
    turn = ease("inout", clamp((t - T_TURN[0]) / (T_TURN[1] - T_TURN[0])))
    sx = math.cos(math.pi * turn)
    m = (x_ladder + 9.0 * (1.0 if sx >= 0.0 else -1.0) - pel * Bk.FIG_S * (1.0 if sx < 0.0 else 0.0), FOOT_W - 112.0)
    pose.arms["near"] = ("ang", 12.0, 18.0)
    pose.arms["far"] = ("ik", (pel + 45.0, -560.0))
    return x_ladder, FOOT_W, st, pose, sx, m


def him_state(t):
    """(x, floor y, state, pose, sx) for the Cracker (sx -1: facing left, toward her)."""
    if t < T_STEP_HIM[0]:                                  # bent over the hole, watching
        g = _tile_u(t)
        st = C.standing("cracker")
        pose = pd.Pose(lean=lerp(6.0, 20.0, g), head=lerp(-10.0, -30.0, g))
        pose.arms["near"] = ("ang", 14.0, 30.0)
        pose.arms["far"] = ("ang", 8.0, 20.0)
        return HIM_U, 0.0, st, pose, -1.0
    x_ladder = TRAP + 6.0
    if t < T_SLIDE[1][0]:                                  # a few steps to the hole
        u = clamp((t - T_STEP_HIM[0]) / (T_STEP_HIM[1] - T_STEP_HIM[0]))
        x = lerp(HIM_U, x_ladder, ease("inout", u))
        st = C.standing("cracker")
        bob = abs(math.sin(math.pi * 3.0 * u))
        pose = pd.Pose(lean=lerp(20.0, 6.0, u), head=-18.0, crouch=14.0 * bob)
        pose.arms["near"] = ("ang", 10.0 + 14.0 * bob, 14.0)
        pose.arms["far"] = ("ang", 6.0, 12.0)
        return x, 0.0, st, pose, -1.0
    d0, d1 = T_SLIDE[1]
    if t < d1:
        u = clamp((t - d0) / (d1 - d0))
        st, pose = Bk.ladder_pose("cracker", 0.0, 1)
        return x_ladder, FOOT_W * u * u, st, pose, -1.0
    st, pose, pel = _wading("cracker", t, x_ladder, d1)
    pose.arms["near"] = ("ang", 18.0, 22.0)
    pose.arms["far"] = ("ang", 8.0, 16.0)
    return x_ladder, FOOT_W, st, pose, -1.0


def _draw_fig(c, cam, who, x, y, st, pose, sx, match):
    """Drawn facing right and scaled by sx about x (so -1 faces left); rimmed in gold toward the
    match."""
    if abs(sx) < 0.04:
        return
    head = (x + sx * st["pelvis"][0] * Bk.FIG_S, y - 120.0)
    dx, dy = match[0] - head[0], match[1] - head[1]
    n = math.hypot(dx, dy) or 1.0
    with cam.on(c):
        c.translate(x, 0.0)
        c.scale(sx, 1.0)
        c.translate(-x, 0.0)
        C.draw(c, who, st, pose, x, y, Bk.FIG_S, 1, bg=K.INK, rim=K.GOLD, rim_w=4.0 / cam.zoom,
               light=(dx / n * (1.0 if sx > 0 else -1.0), dy / n))


def _reveal_x(t):
    return lerp(CUT_N, REVEAL_TO, ease("inout", clamp((t - T_REVEAL[0]) / (T_REVEAL[1] - T_REVEAL[0]))))


def _her_s(t, x, y, pel):
    """How far along ROUTE_SEC she is (set px)."""
    shaft = ROUTE_Y - Bk.VSLAB
    if t < T_SLIDE[0][1]:
        return clamp(y - Bk.VSLAB, 0.0, shaft)
    return shaft + max(0.0, pel * Bk.FIG_S)


def _route_sec(c, cam, t, s_her):
    """Plan B's solid line in section, lighting ahead of her: down the shaft, north along the
    branch to manhole B and up it to the back street."""
    if t < T_SLIDE[0][0]:
        return
    L = K.poly_len(ROUTE_SEC)
    lit = s_her + 80.0
    lit = lerp(lit, L, ease("inout", clamp((t - T_LIT[0]) / (T_LIT[1] - T_LIT[0]))))
    with cam.on(c):
        K.route(c, ROUTE_SEC, clamp(lit / L), K.PAPER, solid=True, width=3.4, head=13.0, r=3.0, seed=2301)
        if t >= T_LIT[1]:
            K.ripple(c, ROUTE_SEC[-1], t, T_LIT[1], K.PAPER, n=2, every=0.18, life=0.6, r0=6.0, r1=40.0, width=2.0)


def _lit_floor(c, cam, t, match):
    """Her match low over the floor: a gold edge along the floor's top, broken by the hole, and
    along the lifted tile's underside."""
    g = _tile_u(t)
    k = clamp(1.0 - abs(match[1] + 40.0) / 160.0)          # strongest while the match is low
    x0, x1 = Bk.TILE_U
    with cam.on(c):
        for a, b in ((Bk.VAULT_IN[0] + 6.0, x0), (x1 + (52.0 if g >= 1.0 else 0.0), Bk.VAULT_IN[1] - 6.0)):
            K.chalk_line(c, [(a, -1.2), (b, -1.2)], 1.0, 1.4, K.GOLD, seed=2320, alpha=0.55 * k)
        if 0.0 < g < 1.0:
            e = _tile_edge(g)
            px = x1 + 44.0 * ease("inout", clamp((g - 0.5) / 0.5))
            K.chalk_line(c, [(px, -1.0), e], 1.0, 1.6, K.GOLD, seed=2321, alpha=0.9 * k)


def vault_cam(t):
    if t < T_SECTION:
        return CAM_TILE
    cam = Bk.Cam.lerp(CAM_TILE, CAM_SECT, ease("inout", clamp((t - T_SECTION) / 0.95)))
    w = ease("inout", clamp((t - 13.9) / (16.0 - 13.9)))
    return Bk.Cam.lerp(cam, CAM_END, w) if w > 0.0 else cam


def vault_shot(c, t):
    cam = vault_cam(t)
    tf = K.twos(t)                                         # the figures (and what they hold) on twos
    hx, hy, hst, hpose, hsx, match = her_state(tf)
    mx, my, mst, mpose, msx = him_state(tf)
    cut = ease("out3", clamp((t - T_CUT[0]) / (T_CUT[1] - T_CUT[0]))) if t >= T_CUT[0] else 0.0
    r = lerp(170.0, 250.0, ease("inout", clamp((t - T_SECTION) / 1.2)))
    Bk.vault(c, cam, t, light=("match", match, 0.0), door=1.0, box=1.0, tile=_tile_u(tf), floor_cut=cut, gold=0.0)
    if t < T_SLIDE[0][0] + 0.25:                           # the match grazes the floor and the tile's underside
        _lit_floor(c, cam, tf, match)
    rx = _reveal_x(t)
    if rx < CUT_N - 0.5:                                   # the cut runs on north: the branch to manhole B
        f0, f1 = cam.to_frame((rx, 0.0))[0], cam.to_frame((CUT_N + 3.0, 0.0))[0]
        c.save()
        c.rectangle(f0, 0.0, f1 - f0, K.H)
        c.clip()
        Bk.sewer(c, cam, t, view="branch", trapdoor=1.0, above=True)
        c.restore()
        with cam.on(c):
            K.chalk_line(c, [(rx, -700.0), (rx, Bk.BRANCH[1] + 30.0)], 1.0, 2.5, K.PAPER, seed=2310, alpha=0.7)
    pel = _walker("architect").state(tf)["pelvis"][0] if tf >= T_SLIDE[0][1] else 0.0
    _route_sec(c, cam, t, _her_s(tf, hx, hy, pel))
    _draw_fig(c, cam, "cracker", mx, my, mst, mpose, msx, match)
    _draw_fig(c, cam, "architect", hx, hy, hst, hpose, hsx, match)
    for i, (d0, d1) in enumerate(T_SLIDE):                 # the splashes
        Bk.splash(c, cam, (TRAP + (6.0 if i else -6.0), Bk.BRANCH_WATER), t, d1, s=1.6)
    for who in ("architect", "cracker"):
        for tt, x in steps(who):
            Bk.splash(c, cam, (x, Bk.BRANCH_WATER), t, tt, s=0.7)
    if cut > 0.0:
        Bk.water(c, cam, t, view="branch", x0=min(rx, CUT_N), x1=Bk.VAULT_U[1] + 30.0)
    Bk.match_rings(c, cam, match, r, t)
    K.flame(c, cam.to_frame(match), t, s=0.3 + 0.08 * cam.zoom, seed=5)


def face_shot(c, t):
    """The Cracker close, lit from below by her match at the hole: he stares; he grins."""
    K.fill(c, K.INK)
    s = lerp(1.62, 1.76, ease("inout", clamp((t - T_FACE[0]) / (T_FACE[1] - T_FACE[0]))))
    g = ease("out3", clamp((t - T_GRIN) / 0.26))
    glint = clamp((t - T_GLINT[0]) / (T_GLINT[1] - T_GLINT[0]))
    c.save()
    c.translate(K.W, 0.0)                                  # mirrored: he faces left, toward her
    c.scale(-1.0, 1.0)
    K.pool(c, (930.0, 1760.0), 1150.0, 1150.0, K.GOLD, 0.42, steps=5)
    eye = (K.W - 430.0, 800.0)
    at = (eye[0] - (452.0 - 400.0) * s, eye[1] + (860.0 - 298.0) * s)

    def face(cc):
        F.cracker(cc, at, s, look=0.85, glint=glint if glint < 1.0 else 0.0, t=t, edge=DIM_GOLD)
    c.push_group()                                         # the match's rim, toward it (down and left)
    face(c)
    m = c.pop_group()
    c.save()
    c.translate(10.0, 7.0)
    c.set_source_rgba(*K.GOLD, 1.0)
    c.mask(m)
    c.restore()
    face(c)

    def fp(p):
        return (at[0] + (p[0] - 400.0) * s, at[1] + (p[1] - 860.0) * s)
    if g > 0.0:                                            # the grin: teeth under the moustache, the crease
        teeth = [fp(p) for p in ((531.0, 472.0), (515.0, 477.0 - 3.0 * g), (497.0, 469.0 - 8.0 * g),
                                 (488.0, 475.0 - 8.0 * g), (509.0, 488.0), (530.0, 482.0))]
        bass.fill_polys(c, [bass.orient(teeth, True)], K.PAPER, g)
        crease = [fp(p) for p in ((522.0, 396.0), (502.0, 422.0 - 6.0 * g), (486.0, 450.0 - 9.0 * g),
                                  (486.0, 478.0 - 8.0 * g))]
        bass.line_band(c, crease, K.GOLD, width=11.0, seed=2402, taper=(0.3, 1.0), alpha=g)
    c.restore()
    K.match_light(c, (150.0, 1760.0), t, 1300.0, 0.6, seed=7)


# ============================================================================ render
def render(f, t, T):
    sh = shown(t)
    if sh is not None:
        kind, sid, st = sh
        mod, Ts = _scene(sid)
        if mod is None:
            _missing(f, sid)
        else:
            mod.render(f, st, Ts)
        with f.screen() as c:
            _rewind_marks(c, t, kind, sid, st, Ts)
        return
    if t < T_VAULT:
        K.scene_setup(f, K.DEEP)
        with f.screen() as c:
            plan_shot(c, t)
        return
    K.scene_setup(f, K.INK)
    with f.screen() as c:
        if T_FACE[0] <= t < T_FACE[1]:
            face_shot(c, t)
        else:
            vault_shot(c, t)


def cues(T):
    out = [Cue(0.12, "a tape stops and spools backwards: a rising rewind whoosh; the heist clock ticking backwards",
               gain_db=-8, dur=T_PLAY - 0.12),
           Cue(T_PLAY, "the tape catches and plays: a soft click", gain_db=-14),
           Cue(3.5, "freeze: the sound stops dead (a tape pause)", gain_db=-16),
           Cue(T_LENS1, "a ting: the lens opens on the chalk dot", gain_db=-9),
           Cue(4.2, "a short rewind whoosh", gain_db=-11, dur=0.25),
           Cue(6.15, "freeze", gain_db=-18),
           Cue(T_LENS2, "a soft chalk tick: the lens opens on her eye", gain_db=-16),
           Cue(T_SHEET[0], "tracing paper unrolling over the blueprint", gain_db=-11, dur=T_SHEET[1] - T_SHEET[0]),
           Cue(T_B1[0], "chalk: four quick strokes, a square", gain_db=-14, dur=T_B1[1] - T_B1[0]),
           Cue(T_B2[0], "chalk: one long sure stroke", gain_db=-13, dur=T_B2[1] - T_B2[0]),
           Cue(8.9, "a whip whoosh", gain_db=-14, dur=0.2)]
    for i, tc in enumerate(T_COPS):
        out.append(Cue(tc, "a muted trumpet stab: a police car chalked in", gain_db=-10 - i, pan=0.4))
    out += [Cue(9.95, "a whip whoosh", gain_db=-14, dur=0.17),
            Cue(T_B4[0], "two hard chalk slashes and a low stab: the red X on the ruby box", gain_db=-8, pan=0.2),
            Cue(10.4, "the theme returns upright, in the major (vibraphone and walking bass)", gain_db=-11,
                dur=T.duration - 10.4),
            Cue(T_VAULT, "the match's small hiss in the dark vault", gain_db=-22, dur=T.duration - T_VAULT),
            Cue(T_TILE[0], "a stone tile scraped up out of the floor", gain_db=-10, pan=0.1),
            Cue(T_TILE[1] - 0.15, "the tile laid down on the floor: a dull clunk", gain_db=-12, pan=0.25),
            Cue(T_GLINT[0], "a ting: the light crosses his spectacles", gain_db=-14),
            Cue(T_GRIN, "a low dry chuckle", gain_db=-14),
            Cue(T_CUT[0], "paper torn down: the floor cut away into section", gain_db=-14, dur=T_CUT[1] - T_CUT[0]),
            Cue(T_SLIDE[0][0], "gloves and a coat sliding fast down an iron ladder", gain_db=-15,
                dur=T_SLIDE[0][1] - T_SLIDE[0][0]),
            Cue(T_SLIDE[0][1], "a splash in shallow water, echoing in the pipe", gain_db=-9),
            Cue(T_SLIDE[1][0], "a heavier slide down the iron ladder", gain_db=-15, pan=0.15,
                dur=T_SLIDE[1][1] - T_SLIDE[1][0]),
            Cue(T_SLIDE[1][1], "a heavier splash, echoing", gain_db=-8, pan=0.1),
            Cue(T_REVEAL[0], "paper torn on along the pipe", gain_db=-17, pan=-0.3, dur=T_REVEAL[1] - T_REVEAL[0]),
            Cue(T_LIT[0], "a rising chime: Plan B's line lights the way to the street", gain_db=-12,
                dur=T_LIT[1] - T_LIT[0] + 0.3)]
    for who in ("architect", "cracker"):
        for tt, x in steps(who):
            fx = vault_cam(tt).to_frame((x, 0.0))[0]
            out.append(Cue(tt, "a footstep in shallow water", gain_db=-18 if who == "architect" else -17,
                           pan=clamp(fx / K.W * 2.0 - 1.0, -0.8, 0.8)))
    return out
