"""s07 CROSS (80-96). The gold, the ruby, his look, the X-split, the door, the dial in red, his L.
  The vault (0-6), one take inside on gold (east-looking section): the Knight crouched at the
    gold dropping bars into a sack while the Cracker, kneeling, hands them over; behind them the
    Architect at the deposit wall. The camera eases in on her: she opens one small box, something
    RED glints, she takes it and pockets it with her back to them. No one sees. The camera eases
    over to him: he pulls the sack shut and stands over the two full bags. His RED look goes to
    the bags; he turns (a cut-paper turn), and it goes to the open door, carrying the camera.
  The X (6-10): the four panels cut in round the clock and the frame is split on both
    diagonals: top, him heaving up the two bags; right, the Cracker kneeling, turning a bar in
    the light; bottom, the door's edge from the corridor, the gold beyond; left, her shutting the
    little box and patting her pocket (a red glint). He moves off toward the door (8.5): the seams
    turn RED, and his shadow comes out of the gold in the bottom panel.
  The door (10-12): the panels fly off and the bottom one is the frame. Outside, north-looking, he
    drives the great door shut with a lunge, lets go and steps back to watch it swing; the
    ellipse widens back to a circle, the gold narrowing to a sliver; through the gap the two
    inside turn too late. BOOM on the bar line (12.0): black; in the dark the rim's bolts shoot
    home.
  The dial (12.2-13): s06's close-up in RED with s06's lock run backwards: his gloved hand on the
    knob, the lock's bolt shoots home (a red ripple), the fence lifts, the gates' line is rubbed
    out and the dial spins the gates away; he lets go.
  His L (13-16): matched on the dial: the plan, top-down, comes up round the red close-up, which
    shrinks to a lens and closes onto the plan's chalk dial (same place); the camera then glides
    after him. The red knight drops onto the vault door and hops along his
    RED route: down the chalk route, then off it in an L (east, then down the alley) to the car.
    The stopwatch stops dead as he turns off the route (13.5) and its hand turns RED. Landing at
    the side door he sets off the bell: red ripples over the plan, on every beat to the end.

Pure in t (s09 rewinds this scene).
"""
import math
from functools import lru_cache

import cairo

from engine import bass
from engine import draw as D
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross import bank as Bk
from films.double_cross import cast as C
from films.double_cross import faces as F
from films.double_cross import kit as K
from films.double_cross import plan as P
from films.double_cross.scenes import s06_safe as S6

FILM_T0 = 80.0
STOPWATCH = ((930.0, 190.0), 62.0)
FS = Bk.FIG_S
FV = S6.FIG_V                      # the cast at the vault door (s06's cheat)
W, H = 1080.0, 1920.0

# ---------------------------------------------------------------------------- beats: the vault (0-6)
T_SCOOPS = ((0.1, 0.8), (0.9, 1.6), (1.7, 2.4), (2.5, 3.2))   # a bar from his hands into the sack
T_REACH = (0.35, 0.95)             # her hand to the little box's handle
T_BOX = (0.95, 1.5)                # it opens
T_PUSH_HER = (1.0, 2.2)            # the camera eases in on her
T_GLINT = (1.5, 1.95)              # something RED glints in it
T_TAKE = (2.0, 2.35)               # she takes it ...
T_POCKET = (2.35, 3.0)             # ... into her coat pocket, her back to them
T_TO_HIM = (3.15, 4.1)             # the camera eases over to him
T_CINCH = (3.3, 3.75)              # he pulls the sack's neck shut
T_RISE = (3.75, 4.35)              # and stands over the two bags
T_LOOK_BAGS = (4.4, 4.82)          # his RED look at the bags (on, off) ...
T_TURN = (4.9, 5.1)                # ... he turns (a cut-paper turn) ...
T_LOOK_DOOR = 5.1                  # ... and looks at the open door, held
T_X = 6.0                          # cut: the X-split

# ---------------------------------------------------------------------------- beats: the X (6-10)
X_IN = (6.0, 3.0 / 24.0, 0.22)     # the panels cut in round the clock: first, the stagger, the slide
X_ORDER = ("top", "right", "bottom", "left")
T_LIFT = (6.35, 7.2)               # top: he heaves the two bags up
T_SHUT_BOX = (6.45, 6.95)          # left: she shuts the little box ...
T_PAT = (7.3, 7.65)                # ... and pats her pocket (a red glint)
T_GLEAM = (7.35, 7.8)              # right: the Cracker turns a bar in the light: it gleams
T_MOVES = 8.5                      # he moves off toward the door: the seams turn RED
T_SHADOW = (9.2, 10.0)             # bottom: his shadow comes out of the gold onto the corridor floor
T_X_OUT = (10.0, 10.26)            # the panels fly off: the bottom one is the frame

# ---------------------------------------------------------------------------- beats: the door (10-12)
T_PUSH = 10.0                      # his hands on the door: it begins to swing
T_SHOVE = (10.0, 10.6)             # he drives it with a lunge ...
T_STEP_BACK = (10.7, 11.1)         # ... lets go and steps back to watch it swing
T_TURN_IN = {"cracker": (10.55, 10.73), "architect": (10.9, 11.08)}   # the two inside turn: too late
T_SLAM = 12.0                      # BOOM on the bar line: black

# ---------------------------------------------------------------------------- beats: the dial (12.2-13)
T_DIAL = 12.2
S6_KEYS = ((12.2, 10.0), (12.25, 10.0), (12.33, 9.55), (12.42, 8.85), (12.9, 3.4))   # s07 t -> s06 t
T_CLANK = 12.32                    # the lock's bolt shoots home (s06's T_BOLT[0], run backwards)
T_HAND_ON = (12.2, 12.26)          # his hand onto the knob ...
T_HAND_OFF = (12.88, 13.0)         # ... and off it
CU_PUSH = 1.05                     # the close-up's slow push (its last frame is the plan's first)

# ---------------------------------------------------------------------------- beats: his L (13-16)
T_PLAN = 13.0
T_LENS = (13.0, 13.32)             # cut to the plan: the dial in a RED lens shrinks into the plan's chalk dial
T_GLIDE = (13.3, 15.5)             # the camera glides after him
HOPS = ((13.2, 0.0), (13.35, 200.0), (13.5, 400.0), (13.75, 492.5), (14.0, 585.0), (14.25, 677.5),
        (14.5, 770.0), (14.75, 877.0), (15.0, 984.0), (15.25, 1092.0))   # (lands, arc length along his route)
T_BELL = 14.5                      # he lands at the side door: the alarm bell, rung on every beat
T_END = 16.0

# ---------------------------------------------------------------------------- places (east-looking set px)
ARCH_AT = 552.0                    # the Architect at the deposit wall behind the gold, facing north (left)
CRACK_AT = 478.0                   # the Cracker kneeling at the gold's north end, facing south
KNIGHT_AT = 640.0                  # the Knight stooped at his sack, facing north
SACK_A = (612.0, 0.0)              # the sack he is filling ...
SACK_B = (658.0, 0.0)              # ... and the full one behind him
HAND_OVER = (550.0, -60.0)         # where a bar passes from the Cracker's hand to his
RUBY_C = ((Bk.RUBY_BOX[0] + Bk.RUBY_BOX[2]) / 2.0, (Bk.RUBY_BOX[1] + Bk.RUBY_BOX[3]) / 2.0)
POCKET = (546.0, -64.0)            # her coat pocket
DOOR_GAP = (690.0, -112.0)         # the open door, seen from inside (the gap in the south wall)
BAGS_AT = (612.0, -22.0)           # his look at the bags ...
DOOR_AT = (790.0, -112.0)          # ... and at the great door, open outside

CAM_V0 = Bk.Cam(566.0, -112.0, 4.6)        # the vault: the three of them at the gold
CAM_HER = Bk.Cam(548.0, -114.0, 6.6)       # in on her at the box
CAM_HIM = Bk.Cam(634.0, -100.0, 5.4)       # over to him, the bags and the door
CAM_LOOK = Bk.Cam(698.0, -108.0, 5.0)      # his look carries the camera to the door

# the gold he bags (taken off the top of the stacks, in this order) and the light on it
GOLD_N = 16
TAKEN = (15, 13, 12, 14)           # indices into Bk._gold_layout(): the bars he bags
_, _, _, _, GOLD_C, GOLD_EDGE, GOLD_SHINE = Bk._palette(None)

# ---------------------------------------------------------------------------- the X's panels
KX_TOP = 600.0                     # top: the Knight between the bags, facing the door
CAM_XT = Bk.Cam(628.0, 58.0, 4.6)
CAM_XL = Bk.Cam(620.0, -68.0, 4.7)         # left: her at the box wall
CR_XR = 520.0                      # right: the Cracker kneeling, facing north, a bar to his eye
CAM_XR = Bk.Cam(445.0, -46.0, 5.4)
CAM_XB = Bk.Cam(590.0, -262.0, 3.6)        # bottom: the door's edge from the corridor (north-looking)
X_TRI = {"top": ((0.0, 0.0), (W, 0.0)), "right": ((W, 0.0), (W, H)), "bottom": ((W, H), (0.0, H)),
         "left": ((0.0, H), (0.0, 0.0))}
X_DIR = {"top": (0.0, -1.0), "right": (1.0, 0.0), "bottom": (0.0, 1.0), "left": (-1.0, 0.0)}
X_DIST = {"top": 990.0, "right": 570.0, "bottom": 990.0, "left": 570.0}

# ---------------------------------------------------------------------------- the door (north-looking set px)
CAM_D1 = Bk.Cam(586.0, -122.0, 3.15)       # the door, him, the opening
CAM_D2 = Bk.Cam(556.0, -116.0, 3.6)        # in on the closing gap
IN_S = FV * 0.72                   # the two inside, beyond the door
IN_FEET = -26.0
IN_X = {"architect": 462.0, "cracker": 548.0}
PUSH_Y = -62.0                     # his hands on the door's face
S6_DIAL_END = 20.0                 # the dial as s06 left it

# ---------------------------------------------------------------------------- the plan
ROUTE = P.ROUTE_KNIGHT
ROUTE_L = P.route_len(ROUTE)
PLAN_P2 = P.PlanCam(738.0, 1050.0, 1.7)
PIECE_H = 100.0
KNIGHT_R = 0.33 * PIECE_H          # the knight's crown on the plan (plan px)
DIAL_CU = (540.0 + (S6.CU_DIAL[0] - 540.0) * CU_PUSH, 960.0 + (S6.CU_DIAL[1] - 960.0) * CU_PUSH)
DIAL_CU_R = Bk.DIAL_R * S6.CU_ZOOM * CU_PUSH
PLAN_P0 = P.PlanCam(P.DIAL_AT[0] - (DIAL_CU[0] - 540.0) / 1.6, P.DIAL_AT[1] - (DIAL_CU[1] - 960.0) / 1.6, 1.6)


def motion_blur(t, T):
    return 1


def _seg(name, s0, s1, at, speed=1.0, **kw):
    return C.Seg(C.clip(name), s0, s1, at=at, speed=speed, **kw)


def _u(t, span):
    return clamp((t - span[0]) / (span[1] - span[0]))


def _ik(p, x, s=FS):
    return ("ik", ((p[0] - x) / s, p[1] / s))


def _dry(who, st, pose, x, facing, s=FS):
    surf = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    return C.draw(cairo.Context(surf), who, st, pose, x, 0.0, s, facing, rim=False)


def _lerp2(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))


def _arc2(a, b, u, h):
    """a to b along a little arc lifted h px."""
    p = _lerp2(a, b, u)
    return (p[0], p[1] - h * math.sin(math.pi * clamp(u)))


def _paper_turn(u):
    """(sx, flipped) of a cut-paper turn u 0..1: squashed through edge-on, flipped past the middle."""
    e = ease("inout", clamp(u))
    return max(0.04, abs(math.cos(math.pi * e))), e >= 0.5


def _turned(c, px, sx, fn):
    """Draw fn(c) squashed to sx about set x px (a paper turn)."""
    if sx >= 0.999:
        return fn(c)
    c.save()
    c.translate(px, 0.0)
    c.scale(sx, 1.0)
    c.translate(-px, 0.0)
    out = fn(c)
    c.restore()
    return out


# ============================================================================ the vault: performances
@lru_cache(maxsize=None)
def perfs():
    d = {}
    d["architect"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 0.0, 0.1, travel=0.0)], facing=-1)
    d["cracker"] = C.perf("cracker", [_seg("23_03", 3.7, 4.0, 0.0, 0.07, travel=0.0)], facing=1)
    d["knight"] = C.perf("knight", [_seg("26_10", 1.1, 1.2, 0.0, 0.02, travel=0.0),
                                    _seg("26_10", 3.2, 3.6, T_RISE[0], 0.4 / (T_RISE[1] - T_RISE[0]), travel=0.0,
                                         blend=0.25)], facing=-1)
    return d


def bars_left(t):
    """The bars still on the stacks at t (indices into Bk._gold_layout())."""
    gone = {TAKEN[k] for k, (t0, t1) in enumerate(T_SCOOPS) if t >= t0 + 0.22}
    return [i for i in range(GOLD_N) if i not in gone]


def sack_fill(t):
    """Sack A fills a bar at a time (half full when we come in)."""
    n = sum(1 for (t0, t1) in T_SCOOPS if t >= t0 + 0.62)
    return 0.5 + 0.11 * n + 0.06 * ease("inout", _u(t, T_CINCH))


def _scoop(t):
    """(phase, k) of the scoop at t: phase 0..1 through scoop k, or (None, None)."""
    for k, (t0, t1) in enumerate(T_SCOOPS):
        if t0 <= t < t1:
            return (t - t0) / (t1 - t0), k
    return None, None


def _bar_pos(i):
    x, y = Bk._gold_layout()[i]
    return (x, y - 4.5)


def cracker_vault(t, tt):
    """(st, pose, bar): kneeling, he lifts each bar off the stack and hands it over."""
    st, pose = perfs()["cracker"](tt)
    j = _dry("cracker", st, pose, CRACK_AT, 1)
    rest = (j["hand_near"][0] + 2.0, j["hand_near"][1] + 8.0)
    ph, k = _scoop(tt)
    bar = None
    if ph is not None:
        src = _bar_pos(TAKEN[k])
        if ph < 0.22:
            tgt = _lerp2(rest, src, ease("inout", ph / 0.22))
        elif ph < 0.45:
            tgt = _arc2(src, HAND_OVER, ease("inout", (ph - 0.22) / 0.23), 10.0)
            bar = tgt
        elif ph < 0.52:
            tgt = HAND_OVER
            bar = tgt
        else:
            tgt = _lerp2(HAND_OVER, rest, ease("inout", (ph - 0.52) / 0.48))
        pose.arms["near"] = _ik(tgt, CRACK_AT)
        dip = math.sin(math.pi * clamp(ph / 0.5))
        pose.lean += 9.0 * dip
        pose.head -= 6.0 * dip
    pose.arms["far"] = _ik((j["hand_far"][0] + 2.0, -32.0), CRACK_AT)
    return st, pose, bar


def knight_turn(tt):
    """(sx, facing): his paper turn from the bags to the door."""
    sx, flipped = _paper_turn(_u(tt, T_TURN))
    return sx, (1 if flipped else -1)


def knight_vault(t, tt):
    """(st, pose, x, facing, bar, sx): crouched at the sack, taking each bar and dropping it in;
    he pulls the sack shut and stands; looks down at the bags; turns to the door."""
    st, pose = perfs()["knight"](tt)
    x = KNIGHT_AT
    mouth = (SACK_A[0], -40.0)
    bar = None
    if tt < T_RISE[0]:
        ph, k = _scoop(tt)
        far = (mouth[0] + 8.0, mouth[1] - 2.0)
        if ph is not None:
            if ph < 0.4:
                tgt = _lerp2(mouth, HAND_OVER, ease("inout", ph / 0.4))
            elif ph < 0.52:
                tgt = HAND_OVER
            else:
                tgt = _arc2(HAND_OVER, mouth, ease("inout", (ph - 0.52) / 0.12), 8.0) if ph < 0.64 else mouth
                if ph < 0.64:
                    bar = tgt
        else:
            tgt = mouth
        cu = _u(tt, T_CINCH)
        if cu > 0.0:                                   # both hands up the sack's neck: pulled shut
            tgt = (mouth[0] - 2.0, mouth[1] - 10.0 * ease("inout", cu))
            far = (mouth[0] + 4.0, mouth[1] - 12.0 * ease("inout", cu))
        pose.arms["near"] = _ik(tgt, x)
        pose.arms["far"] = _ik(far, x)
        pose.lean += 8.0 * math.sin(math.pi * clamp((ph or 0.0) / 0.6))
    else:
        bow = ease("inout", clamp((tt - T_LOOK_BAGS[0] + 0.15) / 0.3)) * (1.0 - ease("inout", _u(tt, (T_LOOK_BAGS[1], T_TURN[0] + 0.05))))
        pose.head -= 14.0 * bow                        # his face down to the bags
        pose.lean += 4.0 * bow
    sx, fc = knight_turn(tt)
    return st, pose, x, fc, bar, sx


def architect_vault(t, tt):
    """(st, pose, ruby): at the box wall, the little box, the ruby into her pocket."""
    st, pose = perfs()["architect"](tt)
    x = ARCH_AT
    j = _dry("architect", st, pose, x, -1)
    rest = j["hand_near"]
    x0, y0, x1, y1 = Bk.RUBY_BOX
    handle = (x1 - 3.0, (y0 + y1) / 2.0)
    ruby = None
    if tt < T_REACH[0]:
        tgt = rest
    elif tt < T_BOX[0]:
        tgt = _lerp2(rest, handle, ease("inout", _u(tt, T_REACH)))
    elif tt < T_BOX[1] + 0.15:
        g = clamp((tt - T_BOX[0]) / (T_BOX[1] - T_BOX[0]))
        edge = x0 + 1.5 + (x1 - x0 - 3.0) * math.cos(math.radians(100.0 * ease("inout", g)))
        tgt = (max(edge, x0 + 8.0), handle[1])
    elif tt < T_TAKE[0]:
        tgt = (x0 + 8.0, handle[1])
    elif tt < T_TAKE[1]:
        tgt = _lerp2((x0 + 8.0, handle[1]), RUBY_C, ease("inout", _u(tt, T_TAKE)))
    elif tt < T_POCKET[1]:
        tgt = _arc2(RUBY_C, POCKET, ease("inout", _u(tt, T_POCKET)), -6.0)
        ruby = tgt
    else:
        tgt = _lerp2(POCKET, rest, ease("inout", clamp((tt - T_POCKET[1]) / 0.5)))
    if tt >= T_TAKE[1] - 0.05 and tt < T_POCKET[1]:
        ruby = tgt
    pose.arms["near"] = _ik(tgt, x)
    reach = clamp((tt - T_REACH[0]) / 0.4) * (1.0 - clamp((tt - T_POCKET[0]) / 0.4))
    pose.lean += 7.0 * ease("inout", reach)
    pose.head += 5.0 * ease("inout", reach)
    return st, pose, ruby


def box_open(t):
    return ease("inout", _u(t, T_BOX))


def glint_at(t):
    """The ruby's glint in the open box: up, held, gone when she takes it."""
    return ease("out", _u(t, T_GLINT)) * (1.0 - clamp((t - T_TAKE[1] + 0.05) / 0.08))


def cam_vault(t):
    if t < T_TO_HIM[0]:
        return Bk.Cam.toward(CAM_V0, CAM_HER, ease("inout", _u(t, T_PUSH_HER)), RUBY_C)
    if t < T_LOOK_DOOR:
        return Bk.Cam.lerp(CAM_HER, CAM_HIM, ease("inout", _u(t, T_TO_HIM)))
    return Bk.Cam.toward(CAM_HIM, CAM_LOOK, ease("inout", clamp((t - T_LOOK_DOOR) / 0.85)), DOOR_AT)


# ============================================================================ the vault: drawing
def _draw_gold(c, idx):
    lay = Bk._gold_layout()
    for i in idx:
        Bk.bar(c, lay[i], 1.0, color=GOLD_C, edge=GOLD_EDGE, shine=GOLD_SHINE)


def _bar_in_hand(c, p, ang=0.0, s=0.9):
    Bk.bar(c, (p[0], p[1] + 4.5 * s / 0.9), s, angle=ang, color=GOLD_C, edge=K.INK, shine=GOLD_SHINE)


def _ruby(c, p, t, size=1.0):
    K.dot(c, p, 2.6 * size, K.RED, seed=711)
    K.twinkle(c, p, 9.0 * size, K.RED, u=1.0, rot=15.0 + 30.0 * K.twos(t), alpha=0.9)


def shot_vault(c, t):
    tt = K.twos(t)
    cam = cam_vault(t)
    Bk.vault(c, cam, t, light=None, door=0.0, box=box_open(t), glint=glint_at(t), gold=0.0)
    rim_w = 4.0 / cam.zoom
    bg = Bk.GOLD_BOX
    with cam.on(c):
        # behind the gold: her, at the box wall
        st, pose, ruby = architect_vault(t, tt)
        C.draw(c, "architect", st, pose, ARCH_AT, 0.0, FS, -1, bg=bg, rim_w=rim_w)
        if ruby is not None:
            _ruby(c, ruby, t, 0.8)
        _draw_gold(c, bars_left(tt))
        Bk.sack(c, SACK_B, 1.0, 1.0, K.INK, rim=K.RED, seed=42)
        Bk.sack(c, SACK_A, sack_fill(tt), 1.0, K.INK, rim=K.RED, seed=41)
        # the Knight
        st, pose, x, fc, bar, sx = knight_vault(t, tt)
        j = _turned(c, x, sx, lambda cc: C.draw(cc, "knight", st, pose, x, 0.0, FS, fc, bg=bg, rim_w=rim_w))
        if bar is not None:
            _bar_in_hand(c, bar, -10.0)
        # the Cracker, kneeling in front of the stacks
        cst, cpose, cbar = cracker_vault(t, tt)
        C.draw(c, "cracker", cst, cpose, CRACK_AT, 0.0, FS, 1, bg=bg, rim_w=rim_w)
        if cbar is not None:
            _bar_in_hand(c, cbar, 8.0)
    # his looks: the bags, then (turned) the door
    if t >= T_LOOK_BAGS[0] and sx >= 0.999:
        eye = cam.to_frame((x + (j["head"][0] - x) * sx + fc * 3.0, j["head"][1] - 1.0))
        if t < T_TURN[0]:
            K.sight_line(c, eye, cam.to_frame(BAGS_AT), t, T_LOOK_BAGS[0], K.RED, dur=0.3, off=T_LOOK_BAGS[1],
                         off_dur=0.12, march=24.0, r=6.5, gap=23.0, head=26.0, seed=71)
        elif t >= T_LOOK_DOOR:
            K.sight_line(c, eye, cam.to_frame(DOOR_AT), t, T_LOOK_DOOR + 0.02, K.RED, dur=0.4, march=30.0, r=7.0,
                         gap=25.0, head=30.0, seed=72)


# ============================================================================ the X (6-10)
@lru_cache(maxsize=None)
def x_perfs():
    d = {}
    d["knight"] = C.perf("knight", [_seg("26_10", 3.0, 3.06, X_IN[0], 0.06 / (T_LIFT[0] - X_IN[0]), travel=0.0),
                                    _seg("26_10", 3.06, 3.6, T_LIFT[0], 0.54 / (T_LIFT[1] - T_LIFT[0]), travel=0.0,
                                         blend=0.1),
                                    _seg("17_08", 5.7, 6.0, T_LIFT[1] + 0.1, 0.2, travel=0.0, blend=0.4),
                                    _seg("17_08", 1.5, 4.0, T_MOVES, 1.15, blend=0.3)], facing=1)
    d["architect"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 4.0, 0.12, travel=0.0)], facing=-1)
    d["cracker"] = C.perf("cracker", [_seg("22_03", 2.6, 3.6, 5.0, 0.12, travel=0.0)], facing=-1)
    return d


def x_knight(tt):
    """(st, pose, x): top: between the two bags, he takes their necks, heaves them up and goes."""
    st, pose = x_perfs()["knight"](tt)
    x = KX_TOP
    j = _dry("knight", st, pose, x, 1)
    px = x + st["pelvis"][0] * FS
    lift = ease("inout", _u(tt, T_LIFT))
    # the bags' necks: low at his sides while he is bent; held at his sides once up
    low_n, low_f = (j["hand_near"][0] - 2.0, j["hand_near"][1] + 6.0), (j["hand_far"][0] - 26.0, j["hand_far"][1] + 8.0)
    walk = clamp((tt - T_MOVES) / 0.3)
    sw = 3.0 * math.sin(2.0 * math.pi * (tt - T_MOVES) * 1.1) * walk
    up_n, up_f = (px + 15.0 + sw, -58.0), (px - 11.0 - sw, -60.0)
    pose.arms["near"] = _ik(_lerp2(low_n, up_n, lift), x)
    pose.arms["far"] = _ik(_lerp2(low_f, up_f, lift), x)
    pose.hold["near"] = Bk.hold_sack(1.0, seed=41, floor=0.0)
    pose.hold["far"] = Bk.hold_sack(1.0, seed=42, floor=0.0)
    pose.lean += 6.0 * lift * (1.0 - walk) + 8.0 * walk         # heavy: he leans into the walk
    return st, pose, x


def x_architect(tt):
    """(st, pose, box): left: she shuts the little box and pats her pocket."""
    st, pose = x_perfs()["architect"](tt)
    x = ARCH_AT
    j = _dry("architect", st, pose, x, -1)
    rest = j["hand_near"]
    x0, y0, x1, y1 = Bk.RUBY_BOX
    g = 1.0 - ease("inout", _u(tt, T_SHUT_BOX))
    edge = (x0 + 1.5 + (x1 - x0 - 3.0) * math.cos(math.radians(100.0 * g)), (y0 + y1) / 2.0)
    if tt < T_SHUT_BOX[0]:
        tgt = _lerp2(rest, edge, ease("inout", clamp((tt - X_IN[0]) / (T_SHUT_BOX[0] - X_IN[0]))))
    elif tt < T_SHUT_BOX[1] + 0.05:
        tgt = edge
    elif tt < T_PAT[0]:
        tgt = _lerp2(edge, POCKET, ease("inout", clamp((tt - T_SHUT_BOX[1] - 0.05) / (T_PAT[0] - T_SHUT_BOX[1] - 0.05))))
    elif tt < T_PAT[1]:
        tgt = (POCKET[0], POCKET[1] + 2.5 * math.sin(2.0 * math.pi * 2.0 * _u(tt, T_PAT)))
    else:
        tgt = _lerp2(POCKET, rest, ease("inout", clamp((tt - T_PAT[1]) / 0.5)))
    pose.arms["near"] = _ik(tgt, x)
    reach = 1.0 - ease("inout", clamp((tt - T_SHUT_BOX[1]) / 0.4))
    pose.lean += 6.0 * reach
    pose.head += 3.0 * reach - 6.0 * ease("inout", clamp((tt - T_PAT[0] + 0.1) / 0.3)) * (1.0 - ease("inout", clamp((tt - T_PAT[1]) / 0.4)))
    return st, pose, g


def x_cracker(tt):
    """(st, pose, bar, ang): right: kneeling, a bar up before his eye, turned in the light."""
    st, pose = x_perfs()["cracker"](tt)
    x = CR_XR
    j = _dry("cracker", st, pose, x, -1)
    lift = ease("inout", clamp((tt - X_IN[0]) / 0.6))
    hold = (j["head"][0] - 15.0, j["head"][1] + 7.0)
    rest = (j["hand_near"][0] - 2.0, j["hand_near"][1] + 4.0)
    bar = _lerp2(rest, hold, lift)
    ang = -8.0 + 16.0 * math.sin(2.0 * math.pi * (tt - X_IN[0]) / 2.4) + 10.0 * ease("inout", _u(tt, T_GLEAM))
    pose.arms["near"] = _ik((bar[0] + 4.0, bar[1] + 1.0), x)
    pose.arms["far"] = _ik((bar[0] - 4.0, bar[1] + 2.0), x)
    pose.head += 6.0 * lift
    return st, pose, bar, ang


def panel_top(c, t):
    tt = K.twos(t)
    cam = CAM_XT
    Bk.vault(c, cam, t, light=None, door=0.0, box=1.0 - ease("inout", _u(t, T_SHUT_BOX)), gold=0.0)
    with cam.on(c):
        _draw_gold(c, bars_left(T_X))
        st, pose, x = x_knight(tt)
        C.draw(c, "knight", st, pose, x, 0.0, FS, 1, bg=Bk.GOLD_BOX, rim_w=4.0 / cam.zoom)


def panel_left(c, t):
    tt = K.twos(t)
    cam = CAM_XL
    st, pose, box = x_architect(tt)
    Bk.vault(c, cam, t, light=None, door=0.0, box=box, gold=0.0)
    with cam.on(c):
        C.draw(c, "architect", st, pose, ARCH_AT, 0.0, FS, -1, bg=Bk.GOLD_BOX, rim_w=4.0 / cam.zoom)
        _draw_gold(c, bars_left(T_X))
        g = math.sin(math.pi * _u(t, (T_PAT[0] + 0.05, T_PAT[0] + 0.4)))
        if g > 0.0:                                  # the ruby in her pocket: a wink of red
            K.twinkle(c, (POCKET[0] - 1.0, POCKET[1] + 2.0), 7.0, K.RED, u=g, rot=20.0, alpha=0.95)


def panel_right(c, t):
    tt = K.twos(t)
    cam = CAM_XR
    Bk.vault(c, cam, t, light=None, door=0.0, box=0.0, gold=0.0)
    with cam.on(c):
        _draw_gold(c, bars_left(T_X))
        st, pose, bar, ang = x_cracker(tt)
        j = C.draw(c, "cracker", st, pose, CR_XR, 0.0, FS, -1, bg=Bk.GOLD_BOX, rim_w=4.0 / cam.zoom)
        _bar_in_hand(c, bar, ang, 1.0)
        g = math.sin(math.pi * _u(t, T_GLEAM))
        if g > 0.0:                                  # the gold catches the light, and his lens
            K.twinkle(c, (bar[0] - 6.0, bar[1] - 4.0), 14.0, K.PAPER, u=g, rot=10.0 + 20.0 * tt, alpha=0.95)
            K.twinkle(c, (j["head"][0] - 2.5, j["head"][1] - 0.5), 6.0, K.GOLD, u=g, rot=40.0, alpha=0.9)


def panel_bottom(c, t):
    shot_door(c, t, CAM_XB)


def _x_card(c, name, fn, off, seam, seam_w):
    """One of the X's four triangles (its picture and its two seams) slid by off (frame px)."""
    a, b = X_TRI[name]
    dx, dy = off
    tri = [(a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy), (540.0 + dx, 960.0 + dy)]
    c.save()
    c.new_path()
    D.poly(c, tri)
    c.clip()
    c.save()
    c.translate(dx, dy)
    fn(c)
    c.restore()
    c.restore()
    if seam is not None:
        for corner, end in ((a, tri[0]), (b, tri[1])):
            bass.line_band(c, [tri[2], end], seam, width=seam_w, seed=int(corner[0] + corner[1]) + 3)


def x_seam(t):
    """(colour, width) of the X's seams: chalk, then RED (with a flare) when he moves."""
    r = ease("out", clamp((t - T_MOVES) / 0.12))
    flare = math.sin(math.pi * clamp((t - T_MOVES) / 0.3))
    return lerp(K.PAPER, K.RED, r), 12.0 + 10.0 * flare


def shot_x(c, t, under=None):
    """The X-split. Before the panels are all in, `under` (the vault shot) shows where they are not."""
    panels = {"top": lambda cc: panel_top(cc, t), "right": lambda cc: panel_right(cc, t),
              "bottom": lambda cc: panel_bottom(cc, t), "left": lambda cc: panel_left(cc, t)}
    seam, sw = x_seam(t)
    t0, step, slide = X_IN
    if under is not None:
        under(c)
    for k, name in enumerate(X_ORDER):
        u = (t - t0 - k * step) / slide
        if u <= 0.0:
            continue
        g = 1.0 - ease("outback", clamp(u)) if u < 1.0 else 0.0
        d = X_DIR[name]
        off = (d[0] * X_DIST[name] * g, d[1] * X_DIST[name] * g)
        _x_card(c, name, panels[name], off, seam, sw)


def x_out(c, t):
    """The panels fly off (top up, right right, left left); the bottom one is the frame."""
    u = ease("in3", _u(t, T_X_OUT))
    seam, sw = x_seam(t)
    for name, fn in (("top", panel_top), ("right", panel_right), ("left", panel_left)):
        d = X_DIR[name]
        off = (d[0] * X_DIST[name] * 1.05 * u, d[1] * X_DIST[name] * 1.05 * u)
        _x_card(c, name, lambda cc, fn=fn: fn(cc, t), off, seam, sw)


# ============================================================================ the door (north-looking)
def door_open_at(t):
    """The great door (1 open, as s06 left it .. 0 shut): it swings faster and faster to the slam."""
    u = clamp((t - T_PUSH) / (T_SLAM - T_PUSH))
    return 1.0 - u ** 1.6


def _face_x(g, k=0.75):
    """A point across the door's face (set px x; k 0 its hinge side .. 1 its free edge)."""
    th = math.radians(88.0 * clamp(g))
    fc = Bk.HINGE_X + (Bk.VDOOR_C[0] - Bk.HINGE_X) * math.cos(th)
    return fc - k * Bk.VDOOR_R * math.cos(th)


@lru_cache(maxsize=None)
def door_perfs():
    d = {}
    d["knight"] = C.perf("knight", [_seg("81_05", 6.0, 6.08, 9.0, 0.08, travel=0.0),
                                    _seg("81_05", 6.08, 7.1, T_SHOVE[0], 1.02 / (T_SHOVE[1] - T_SHOVE[0]),
                                         travel=0.0, blend=0.08),
                                    _seg("17_08", 5.7, 6.0, T_SHOVE[1] + 0.05, 0.25, travel=0.0, blend=0.3)],
                         facing=-1)
    d["architect"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 8.0, 0.12, travel=0.0)], facing=-1)
    d["cracker"] = C.perf("cracker", [_seg("22_03", 2.6, 3.6, 8.0, 0.12, travel=0.0)], facing=-1)
    return d


@lru_cache(maxsize=1)
def _push_reach():
    """How far ahead of him his hands are in the push (set px at FV)."""
    st, pose = door_perfs()["knight"](9.5)
    j = _dry("knight", st, pose, 0.0, -1, FV)
    return -0.5 * (j["hand_near"][0] + j["hand_far"][0])


def door_knight(t, tt):
    """(st, pose, x): his hands on the door's face, the lunge with it, let go, the step back."""
    st, pose = door_perfs()["knight"](tt)
    g_go = door_open_at(T_SHOVE[1])
    if tt < T_SHOVE[1]:
        hx = _face_x(door_open_at(tt))
        x = hx + _push_reach()
        pose.arms["near"] = _ik((hx, PUSH_Y), x, FV)
        pose.arms["far"] = _ik((hx + 3.0, PUSH_Y - 6.0), x, FV)
    else:
        x = _face_x(g_go) + _push_reach()
        st = S6._stepped(st, _u(tt, T_STEP_BACK), -26.0 / FV, -1)
        let = ease("inout", clamp((tt - T_SHOVE[1]) / 0.2))
        if let < 1.0:
            hx = _face_x(door_open_at(T_SHOVE[1]))
            j = _dry("knight", st, pose, x, -1, FV)
            pose.arms["near"] = _ik(_lerp2((hx, PUSH_Y), j["hand_near"], let), x, FV)
            pose.arms["far"] = _ik(_lerp2((hx + 3.0, PUSH_Y - 6.0), j["hand_far"], let), x, FV)
    return st, pose, x


def inside_rows(t, tt):
    """[(who, st, pose, x, facing, sx, bar)]: the two inside, small beyond the door."""
    rows = []
    for who in ("architect", "cracker"):
        st, pose = door_perfs()[who](tt)
        x = IN_X[who]
        a, b = T_TURN_IN[who]
        sx, flipped = _paper_turn(_u(tt, (a, b)))
        fc = 1 if flipped else -1
        st = S6._stepped(st, _u(tt, (b, b + 0.3)), 12.0 / IN_S, 1, lift=14.0)
        bar = None
        if who == "cracker":
            j = _dry(who, st, pose, x, fc, IN_S)
            bar = (j["head"][0] + fc * 15.0 * IN_S / FS, j["head"][1] + 7.0 * IN_S / FS)
            pose.arms["near"] = _ik((bar[0] - fc * 4.0, bar[1] + 1.0), x, IN_S)
            pose.arms["far"] = _ik((bar[0] + fc * 4.0, bar[1] + 2.0), x, IN_S)
        rows.append((who, st, pose, x, fc, sx, bar))
    return rows


def _inside(c, t, tt):
    """Inside the vault through the door: the gold, and the two of them."""
    Bk.vault_through(c, t, gold=0.6)
    c.save()
    c.translate(0.0, IN_FEET)
    for who, st, pose, x, fc, sx, bar in inside_rows(t, tt):
        _turned(c, x, sx, lambda cc: C.draw(cc, who, st, pose, x, 0.0, IN_S, fc, bg=Bk.GOLD_BOX, rim=K.GOLD,
                                            rim_w=1.2))
        if bar is not None and sx >= 0.999:
            Bk.bar(c, (bar[0], bar[1] + 3.0), 0.6, color=GOLD_C, edge=K.INK, shine=GOLD_SHINE)
    c.restore()


def cam_door(t):
    if t < T_X_OUT[0]:
        return CAM_XB
    u = ease("inout", clamp((t - T_X_OUT[0]) / 0.5))
    a = Bk.Cam.lerp(CAM_XB, CAM_D1, u)
    return Bk.Cam.toward(a, CAM_D2, ease("inout", clamp((t - 10.5) / (T_SLAM - 10.5))), S6.OPENING)


def _his_shadow(c, t):
    """Bottom panel: his shadow, cast out of the vault by the gold, crossing the floor's pool."""
    u = _u(t, T_SHADOW)
    if u <= 0.0:
        return
    a = math.sin(math.pi * u) ** 0.7
    x = lerp(470.0, 640.0, ease("inout", u))
    Bk.spill_shadow(c, x, 0.85 * a, half=10.0)


def shot_door(c, t, cam=None):
    """The great door from the corridor: s06's last shot, the door swung shut by him."""
    tt = K.twos(t)
    cam = cam or cam_door(t)
    g = door_open_at(t)
    Bk.vault_door(c, cam, t, open=g, bolts=1.0, wheel=S6.WHEEL_TURN, dial=S6_DIAL_END, light="gold",
                  inside=lambda cc: _inside(cc, t, tt))
    with cam.on(c):
        if t < T_X_OUT[0]:
            _his_shadow(c, t)
        if t >= T_X_OUT[0]:
            st, pose, x = door_knight(t, tt)
            px = x + st["pelvis"][0] * FV
            Bk.spill_shadow(c, px, g)
            rim = lerp(C.RIM["knight"], K.GOLD, 0.85 * ease("inout", clamp(g * 1.6)))
            C.draw(c, "knight", st, pose, x, 0.0, FV, -1, bg=K.INK, rim=rim, rim_w=4.0 / cam.zoom * (1.0 + 0.6 * g),
                   light=(lerp(-0.6, 0.0, g), lerp(-0.8, -1.0, g)))


# ============================================================================ the dial (12.2-13)
def s6_time(t):
    """The s06 time whose lock this frame shows: s06's lock run backwards."""
    for (a, sa), (b, sb) in zip(S6_KEYS, S6_KEYS[1:]):
        if t < b:
            return lerp(sa, sb, clamp((t - a) / (b - a)))
    return S6_KEYS[-1][1]


def T_DIAL_SPIN(t6):
    """The s07 time at which the close-up shows s06 time t6 (s06's lock run backwards)."""
    for (a, sa), (b, sb) in zip(S6_KEYS, S6_KEYS[1:]):
        if sb < sa and sb <= t6 <= sa:
            return a + (b - a) * (sa - t6) / (sa - sb)
    return S6_KEYS[-1][0]


def _cu_zoom(t):
    return lerp(1.0, CU_PUSH, ease("inout", _u(t, (T_DIAL, T_PLAN))))


def _knob_hand(c, t, dial, zoom):
    """His gloved hand on the knob, from the right, twisting with it."""
    on = ease("out", _u(t, T_HAND_ON))
    off = ease("in", _u(t, T_HAND_OFF))
    if on <= 0.0 or off >= 1.0:
        return
    p = (540.0 + (S6.CU_DIAL[0] - 540.0) * zoom, 960.0 + (S6.CU_DIAL[1] - 960.0) * zoom)
    rk = Bk.DIAL_R * S6.CU_ZOOM * zoom * 0.36
    tw = math.radians(clamp(0.3 * (dial - S6_DIAL_END), -40.0, 50.0))
    a = tw - 0.12
    grip = (p[0] + rk * math.cos(a), p[1] + rk * math.sin(a))
    back = 520.0 * (1.0 - on) + 360.0 * off
    wa = tw - 0.18
    wrist = (p[0] + (rk + 700.0) * math.cos(wa) + back, p[1] + (rk + 700.0) * math.sin(wa) + 40.0)
    grip = (grip[0] + back, grip[1])
    F.hand(c, "knight", wrist, grip, 0.78 * zoom, open_u=clamp(1.0 - on * 3.0 + off * 2.0))


def shot_dial(c, t):
    t6 = s6_time(t)
    lk = S6.lock_state(t6)
    zoom = _cu_zoom(t)
    S6.closeup(c, t6, lock=lk, color=K.RED, profile=False, face=lerp(Bk.IRON, K.INK, 0.35), cut=1.0, chalk=1.0,
               zoom=zoom, clicks=(None, None, None), glint=0.0, four=0.0)
    s = S6.LOCK_S
    tip = (S6.LOCK_AT[0] + 370.0 * s, S6.LOCK_AT[1])
    tip = (540.0 + (tip[0] - 540.0) * zoom, 960.0 + (tip[1] - 960.0) * zoom)
    K.ripple(c, tip, t, T_CLANK, K.RED, n=3, every=0.1, life=0.55, r0=14.0, r1=170.0, width=7.0, seed=731, alpha=0.95)
    _knob_hand(c, t, lk["dial"], zoom)


# ============================================================================ his L (13-16)
def plan_cam(t):
    """The plan's chalk dial where the close-up's dial was; then a glide after him."""
    return P.PlanCam.lerp(PLAN_P0, PLAN_P2, ease("inout", _u(t, T_GLIDE)))


def _dial_lens(c, t, cam):
    """The close-up's dial in a RED lens on the plan, shrinking into the plan's chalk dial."""
    u = _u(t, T_LENS)
    if u >= 1.0:
        return
    e = ease("inout", u)
    p = cam.to_view(P.DIAL_AT)
    k = lerp(1.0, 13.0 * cam.zoom / DIAL_CU_R, e)
    R = 1.22 * DIAL_CU_R * k
    c.save()
    c.new_path()
    bass.iris_path(c, p, R, seed=751, n=72)
    c.clip()
    c.translate(*p)
    c.scale(k, k)
    c.translate(-DIAL_CU[0], -DIAL_CU[1])
    shot_dial(c, t)
    c.restore()
    bass.ring(c, p, R, 4.0 + 6.0 * k, K.RED, seed=752, n=72, alpha=1.0 - clamp((u - 0.75) / 0.25))


def knight_hop(t):
    """(s, lift, drop): his arc length along the route, the hop's height 0..1 and the drop onto
    the paper before the first hop (1 still up .. 0 landed)."""
    t0, s0 = HOPS[0]
    if t < t0:
        return s0, 0.0, clamp((t0 - t) / 0.12)
    for (ta, sa), (tb, sb) in zip(HOPS, HOPS[1:]):
        if t < tb:
            air = min(0.17, 0.8 * (tb - ta))
            u = clamp((t - (tb - air)) / air)
            return lerp(sa, sb, ease("inout", u)), math.sin(math.pi * u), 0.0
    return HOPS[-1][1], 0.0, 0.0


def _plan_pieces(c, cam):
    for kind, p, col, edge, fc in PIECES_LOCKED:
        P.piece_on(c, cam, kind, p, PIECE_H, col, edge, facing=fc)


PIECES_LOCKED = [it for it in P.PIECES_A if it[0] != "knight"]


def shot_plan(c, t):
    cam = plan_cam(t)
    s, lift, drop = knight_hop(t)
    rung = t >= T_BELL

    def on_plan(cc):
        lead = min(ROUTE_L, s + 60.0)
        if t >= HOPS[0][0] - 0.05:
            K.route(cc, ROUTE, lead / ROUTE_L, K.RED, r=6.5, gap=22.0, head=26.0, seed=77, alpha=0.95)
        ring = 0.0
        if rung:
            ring = 24.0 * math.sin(2.0 * math.pi * 9.0 * (t - T_BELL)) * (0.6 + 0.4 * ease("out", clamp((t - T_BELL) / 0.1)))
        K.bell(cc, P.BELL_AT, 1.0 + 0.25 * math.sin(math.pi * clamp((t - T_BELL) / 0.2)) if rung else 1.0,
               K.RED if rung else K.PAPER, seed=120, ring=ring)

    P.table(c, cam, 1.0, 1.0, 0.0, on_plan=lambda cc: (P.draw_plan_a(cc, 1.0, prog={"bell": 0.0}), on_plan(cc)))
    _plan_pieces(c, cam)
    # the red knight: dropped onto the vault door, then hopping (top-down: bigger in the air)
    if t >= HOPS[0][0] - 0.12:
        p, _ = P.along(ROUTE, s)
        up = max(lift, drop)
        v = cam.to_view(p)
        r = KNIGHT_R * cam.zoom
        with cam.ground(c):
            off = 10.0 + 34.0 * up
            dx, dy = p[0] - P.LAMP_AT[0], p[1] - P.LAMP_AT[1]
            dd = math.hypot(dx, dy) or 1.0
            sc = (p[0] + dx / dd * off, p[1] + dy / dd * off)
            bass.fill_polys(c, [D.ellipse_pts(sc, KNIGHT_R * (1.05 + 0.25 * up), KNIGHT_R * 0.95, n=40)], K.INK,
                            0.4 * (1.0 - 0.5 * up))
        land = clamp((t - HOPS[0][0]) / 0.06) if drop <= 0.0 else 1.0
        squash = 1.0 - 0.06 * math.sin(math.pi * land) if t < HOPS[0][0] + 0.06 else 1.0
        K.piece_disc(c, v, r * (1.0 + 0.3 * up) * squash, K.RED, K.INK, 1.0, seed=88)
    # the alarm: red ripples over the plan from the bell, on every beat
    if rung:
        b = cam.to_view(P.BELL_AT)
        n = int((t - T_BELL) / K.BEAT) + 1
        for k in range(max(0, n - 3), n):
            K.ripple(c, b, t, T_BELL + k * K.BEAT, K.RED, n=3, every=0.12, life=1.1, r0=24.0, r1=560.0, width=8.0,
                     seed=740 + 3 * k, alpha=0.9)
    _dial_lens(c, t, cam)


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, K.DEEP)
    with f.screen() as c:
        if t < X_IN[0]:
            shot_vault(c, t)
        elif t < T_X_OUT[0]:
            shot_x(c, t, under=(lambda cc: shot_vault(cc, t)) if t < X_IN[0] + 4 * X_IN[1] + X_IN[2] else None)
        elif t < T_SLAM:
            shot_door(c, t)
            if t < T_X_OUT[1]:
                x_out(c, t)
        elif t < T_DIAL:
            Bk.fill_all(c, K.INK)
        elif t < T_PLAN:
            shot_dial(c, t)
        else:
            shot_plan(c, t)
        ft = FILM_T0 + t
        K.stopwatch(c, STOPWATCH[0], STOPWATCH[1], K.heist_beats(ft), hand=K.RED if ft >= K.HEIST_STOP else None)


# ============================================================================ cues
# the beats the mix looks up by name (aliases of the beats above)
T_LOOK = T_LOOK_BAGS[0]
T_SPLIT = T_X
T_RED = T_MOVES
T_SHUT = (T_PUSH, T_SLAM)
T_BOOM = T_SLAM
T_BOLTS = (12.04, 12.18)           # in the black: the rim's bolts shoot home, one after another
T_SPINS = tuple((round(T_DIAL_SPIN(b), 3), round(T_DIAL_SPIN(a), 3)) for a, b in reversed(S6.TURNS))
T_DIAL_RED = T_SPINS[0][0]
T_ROUTE_L = (HOPS[0][0], HOPS[-1][0])
T_HOPS = tuple(t for t, _ in HOPS)
T_ALARM = T_BELL


def _pan_x(fx):
    return round(clamp((fx - 540.0) / 540.0, -1.0, 1.0), 2)


def _pan_set(cam, p):
    return _pan_x(cam.to_frame(p)[0])


def cues(T):
    out = []
    # ---- the vault: each bar off the stack, handed over, into the sack
    for k, (t0, t1) in enumerate(T_SCOOPS):
        d = t1 - t0
        tl, ti = t0 + 0.22 * d, t0 + 0.64 * d
        bx = Bk._gold_layout()[TAKEN[k]][0]
        out.append(Cue(round(tl, 3), "a gold bar lifted off the stack: a clink of gold on gold", gain_db=-17 - (k % 2),
                       pan=_pan_set(cam_vault(tl), (bx, -20.0))))
        out.append(Cue(round(ti, 3), "a gold bar drops into the bag: a heavy muffled chink of gold on gold", gain_db=-16,
                       pan=_pan_set(cam_vault(ti), SACK_A)))
    out.append(Cue(T_BOX[0], "her deposit box's little door opens: a small latch click and a tiny hinge squeak",
                   gain_db=-19, pan=_pan_set(cam_vault(T_BOX[0]), RUBY_C), dur=T_BOX[1] - T_BOX[0]))
    out.append(Cue(T_GLINT[0], "a tiny red glint in the open box: a faint high ting", gain_db=-20,
                   pan=_pan_set(cam_vault(T_GLINT[0]), RUBY_C)))
    out.append(Cue(T_TAKE[0] + 0.25, "she lifts something small out of the box: the faintest tick of stone on steel",
                   gain_db=-30, pan=_pan_set(cam_vault(T_TAKE[0] + 0.25), RUBY_C)))
    out.append(Cue(T_POCKET[0] + 0.4, "she slips it into her coat pocket: a soft cloth rustle", gain_db=-26,
                   pan=_pan_set(cam_vault(T_POCKET[0] + 0.4), POCKET)))
    out.append(Cue(T_CINCH[0], "he pulls the bag's neck shut: canvas cinched tight on gold", gain_db=-20,
                   pan=_pan_set(cam_vault(T_CINCH[0]), SACK_A), dur=T_CINCH[1] - T_CINCH[0]))
    out.append(Cue(T_RISE[0] + 0.05, "a slow breath out: he straightens up over the gold",
                   gain_db=-22, pan=_pan_set(cam_vault(T_RISE[0]), (KNIGHT_AT, -100.0))))
    out.append(Cue(T_LOOK_BAGS[0], "his red look: a chalk sight line flicks down to the bags (a dry chalk tick)",
                   gain_db=-20, pan=_pan_set(cam_vault(T_LOOK_BAGS[0]), BAGS_AT)))
    out.append(Cue(T_TURN[0], "heel scuff: the Knight turns on his heel toward the door", gain_db=-22,
                   pan=_pan_set(cam_vault(T_TURN[0]), (KNIGHT_AT, 0.0))))
    out.append(Cue(T_LOOK_DOOR, "chalk tick: his red look flies to the open door (a red chalk line)",
                   gain_db=-19, pan=_pan_set(cam_vault(T_LOOK_DOOR), DOOR_AT)))
    # ---- the X
    for k, name in enumerate(X_ORDER):
        out.append(Cue(round(X_IN[0] + k * X_IN[1], 3),
                       f"the X-split: a panel slides in from the {name} (a paper whoosh and a snap)", gain_db=-14 - k,
                       pan={"top": 0.0, "right": 0.6, "bottom": 0.0, "left": -0.6}[name]))
    out.append(Cue(T_LIFT[0] + 0.05, "he heaves up the two heavy bags: a strained grunt, the gold shifting inside them",
                   gain_db=-17, pan=0.0))
    out.append(Cue(T_SHUT_BOX[1], "she shuts the little box: a small latch click", gain_db=-22, pan=-0.6))
    out.append(Cue(T_PAT[0] + 0.05, "she pats her coat pocket: a soft pat", gain_db=-26, pan=-0.6))
    out.append(Cue(T_PAT[0] + 0.12, "a tiny red glint in her pocket: a faint high ting", gain_db=-24, pan=-0.6))
    out.append(Cue(T_GLEAM[0] + 0.1, "a soft rising chime: the Cracker turns a bar of gold in the light and it gleams",
                   gain_db=-22, pan=0.6, dur=round(T_GLEAM[1] - T_GLEAM[0] - 0.1, 3)))
    out.append(Cue(T_MOVES, "he moves: the seams turn red (a low sting)", gain_db=-12, pan=0.0))
    for t, side, fx in Bk.footfalls(x_perfs()["knight"], T_MOVES, T_X_OUT[0]):
        out.append(Cue(t, "footstep: the Knight's heavy step on the steel floor, two full bags swinging", gain_db=-21,
                       pan=_pan_set(CAM_XT, (KX_TOP + fx * FS, 0.0))))
    out.append(Cue(T_X_OUT[0] + 0.05, "the X-split's panels fly off: a paper whoosh", gain_db=-15, pan=0.0,
                   dur=round(T_X_OUT[1] - T_X_OUT[0] - 0.05, 3)))           # they start to move visibly
    # ---- the door
    out.append(Cue(T_SHOVE[0] + 0.12, "he throws his weight against the vault door: a strained grunt", gain_db=-15,
                   pan=_pan_set(cam_door(T_SHOVE[0]), (700.0, -100.0))))     # as he leans into it
    out.append(Cue(T_SHUT[0], "the great door's hinge groans as he swings the door shut, faster and faster",
                   gain_db=-9, pan=_pan_set(cam_door(T_SHUT[0]), (Bk.HINGE_X, -110.0)), dur=T_SHUT[1] - T_SHUT[0]))
    for t, side, fx in Bk.footfalls(door_perfs()["knight"], T_SHOVE[0], T_SHOVE[1]):
        out.append(Cue(t, "footstep: the Knight's shoe plants hard on the steel floor as he lunges", gain_db=-22,
                       pan=_pan_set(cam_door(t), (_face_x(door_open_at(t)) + _push_reach(), 0.0))))
    for tb in (0.5 * (T_STEP_BACK[0] + T_STEP_BACK[1]), T_STEP_BACK[1]):
        out.append(Cue(round(tb, 3), "footstep: the Knight steps back on the steel floor", gain_db=-24,
                       pan=_pan_set(cam_door(tb), (_face_x(door_open_at(T_SHOVE[1])) + _push_reach() + 20.0, 0.0))))
    for who, (a, b) in T_TURN_IN.items():
        p = _pan_set(cam_door(a), (IN_X[who], -60.0))
        what = "the Cracker turns with a start: a gasp" if who == "cracker" else "she turns sharply: a coat's swish"
        out.append(Cue(a, f"inside the vault, {what} (muffled by the closing door)", gain_db=-22, pan=p))
        for tb in (b + 0.15, b + 0.3):
            whose = "the Cracker's" if who == "cracker" else "her"
            out.append(Cue(round(tb, 3), f"footstep: inside the vault, {whose} quick step toward the door", gain_db=-27,
                           pan=p))
    out.append(Cue(T_SLAM, "BOOM: the vault door slams shut; black", gain_db=-2, pan=0.0))
    n = Bk.N_BOLTS
    for k in range(n):
        tb = T_BOLTS[0] + (T_BOLTS[1] - T_BOLTS[0]) * k / (n - 1)
        a = math.radians(-90.0 + 15.0 + 30.0 * k)
        out.append(Cue(round(tb, 3), "in the dark, a heavy steel bolt shoots home into the door frame: one clack of a "
                                     "rolling run round the rim", gain_db=-14, pan=round(0.6 * math.cos(a), 2)))
    # ---- the dial, in red: s06's lock run backwards
    out.append(Cue(T_HAND_ON[0], "a gloved hand takes the dial's knob: a leather creak", gain_db=-24, pan=0.3))
    out.append(Cue(T_CLANK, "CLANK: the lock's bolt shoots home", gain_db=-6, pan=0.85))
    out.append(Cue(round(T_DIAL_SPIN(S6.T_FENCE + 0.16), 3), "the fence lifts off the gates: a dull clunk", gain_db=-13,
                   pan=0.0))
    out.append(Cue(T_DIAL_SPIN(S6.T_LINE[1]), "chalk scratch: the gates' chalk mark rubbed out",
                   gain_db=-21, pan=0.0, dur=T_DIAL_SPIN(S6.T_LINE[0]) - T_DIAL_SPIN(S6.T_LINE[1])))
    for (a, b), w in zip(T_SPINS, ("left", "right", "left")):
        out.append(Cue(a, f"the dial spins {w} in red: a fast run of ratchet ticks (the combination scrambled)",
                       gain_db=-15, pan=-0.26, dur=round(b - a, 3)))
    # ---- his L
    out.append(Cue(T_LENS[0] + 0.05, "cut to the plan: the red lens shrinks into the chalk dial (a soft paper whoosh)",
                   gain_db=-19, pan=-0.27, dur=round(T_LENS[1] - T_LENS[0] - 0.05, 3)))
    out.append(Cue(T_ROUTE_L[0], "his red route chalked along behind him: quick chalk dots", gain_db=-20,
                   pan=0.1, dur=T_ROUTE_L[1] - T_ROUTE_L[0]))
    for k, (t, s) in enumerate(HOPS):
        p, _ = P.along(ROUTE, s)
        what = "the red knight drops onto the vault door" if k == 0 else "the red knight hops along the L"
        out.append(Cue(t, f"{what}: a wooden piece taps the paper", gain_db=-15 if k else -13,
                       pan=_pan_x(plan_cam(t).to_view(p)[0])))
    out.append(Cue(K.HEIST_STOP - FILM_T0, "the stopwatch stops dead: its tick cut off, its hand turns red", gain_db=-14,
                   pan=0.72))
    out.append(Cue(T_BELL, "alarm bell: the bell on the side door rings and rings; red ripples over the plan",
                   gain_db=-6, pan=_pan_x(plan_cam(T_BELL).to_view(P.BELL_AT)[0]), dur=T.duration - T_BELL))
    return sorted(out, key=lambda q: q["t"])
