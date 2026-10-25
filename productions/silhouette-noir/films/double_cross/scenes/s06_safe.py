"""s06 SAFE (66-80). The vault door, the stethoscope, the lock's gates, the bolts, the gold.
  The door (0-3): s05's last frame, matched on the dial: the plan's chalk ring and tick on it
    (step 4) fade off the real dial as the camera pulls back to the great round door. The Cracker
    steps in from the right, presses his stethoscope to the steel beside the dial and takes the
    knob; the Architect and the Knight wait behind him.
  The lock (3-10): the dial in close-up, his profile listening at the right; the door's face under
    it is cut away to show the lock in chalk: three wheels with their gates, the fence, the bolt.
    The dial turns right, left, right; on the beats 4.5, 6.5 and 8.5 a gate comes up under the
    fence (a click, low, mid, high: a dot pops in the gate and the click runs up the tube into his
    ear). The three dots are joined (9.0, step 4 circled), the fence drops (9.5, CLUNK; his
    spectacles glint) and the bolt draws back.
  The gold (10-14): the door again. He turns the wheel and the twelve bolts withdraw round the rim
    (a rolling run); he heaves, backs out of the way, and the door swings open toward us (11-13),
    the circle narrowing to an ellipse, gold flooding out over the three of them.

s07 reuses lock_state() and closeup() (the dial and the lock run backwards in RED) and the door's
cameras (its slam rhymes with this opening).
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
from films.double_cross import shots as S

FILM_T0 = K.film_start("s06")
STOPWATCH = ((930.0, 190.0), 62.0)
FIG_V = 0.27                       # the cast at the vault door: FIG_S x 1.35 (the door is a giant)
RS = FIG_V / Bk.FIG_S              # their props and rims scale with them

# ---------------------------------------------------------------------------- beats
T_MARK = (0.35, 0.95)              # step 4's chalk ring and tick fade off the real dial
T_PULL = (0.5, 2.6)                # the camera pulls back off the dial to the door
T_STEP_IN = (0.9, 1.7)             # the Cracker steps in from the right ...
T_PIECE = (1.5, 2.1)               # ... sets the chest-piece to the steel ...
T_KNOB = (1.9, 2.5)                # ... and takes the knob
T_CU = 3.0                         # cut: the dial and the lock
T_CUTAWAY = (3.0, 3.4)             # the door's face cut away under the dial
T_CHALK = (3.05, 3.65)             # the lock drawn on
TURNS = ((3.5, 4.5), (4.8, 6.5), (6.8, 8.5))   # right, left, right
GATES = (4.5, 6.5, 8.5)            # a gate up under the fence (clicks low, mid, high) ...
GATE_WHEEL = (2, 1, 0)             # ... of the far wheel, the middle one, the near one
DIAL_AT = (0.0, 210.0, -90.0, 60.0)   # the dial (deg clockwise) at rest and at each gate: s03's turns, R 210 L 300 R 150
T_TUBE = 0.2                       # a click's run up the tube to his ear
T_LINE = (8.85, 9.3)               # the three dots joined
T_FOUR = 9.0                       # step 4 circled
T_FENCE = 9.5                      # the fence drops: CLUNK
T_GLINT = (9.5, 9.9)               # his spectacles catch the light
T_BOLT = (9.6, 9.95)               # the lock's bolt draws back (the dial a little left)
T_WIDE = 10.0                      # cut: the door
T_LET_GO = (10.0, 10.3)            # the chest-piece let go
T_GRIP = (10.0, 10.2)              # his hand to the wheel
T_WHEEL = (10.2, 10.9)             # the wheel turns; the twelve bolts withdraw round the rim
T_HEAVE = (10.9, 11.15)            # he heaves on it
T_SWING = (11.0, 13.0)             # the door swings open, gold floods out
T_BACK = (11.15, 11.75)            # he backs out of its way
T_PUSH = (11.2, 14.0)              # the camera eases in on the gold
T_REST = 13.0                      # the door comes to rest

# ---------------------------------------------------------------------------- places (set px)
CR_X = (672.0, 620.0)              # the Cracker: in from the right to the dial ...
CR_BACK = 684.0                    # ... and back out of the door's way
ARCH_X = (440.0, 482.0)            # the Architect and the Knight wait out of the dial's frame, and
KNIGHT_X = (398.0, 436.0)          # step up into the gold when the door opens
T_DRAWN = {"architect": (11.55, 12.25), "knight": (11.75, 12.45)}
PIECE_AT = (568.0, -146.0)         # the chest-piece on the steel beside the dial
KNOB_GRIP = (551.0, -159.0)        # his fingers on the knob
SPOKE = -18.0                      # the wheel spoke he takes (deg; it turns up to -90)
WHEEL_TURN = -45.0

# ---------------------------------------------------------------------------- cameras
CAM_DIAL = Bk.Cam(Bk.DIAL_C[0], Bk.DIAL_C[1], 7.0)     # s05's last frame
CAM_WIDE = Bk.Cam(528.0, -128.0, 2.9)                  # the door, the three of them
CAM_GOLD = Bk.Cam(540.0, -118.0, 3.3)                  # in on the gold
OPENING = (Bk.VDOOR_C[0], Bk.VDOOR_C[1])

# the close-up (frame px): the dial at the top left, his profile at the right, the lock below
CU_DIAL = (400.0, 560.0)
CU_ZOOM = 11.0
CAM_CU = Bk.Cam(Bk.DIAL_C[0] + (540.0 - CU_DIAL[0]) / CU_ZOOM, Bk.DIAL_C[1] + (960.0 - CU_DIAL[1]) / CU_ZOOM, CU_ZOOM)
WINDOW = (40.0, 1030.0, 1040.0, 1830.0)        # the face cut away
LOCK_AT = (560.0, 1440.0)
LOCK_S = 1.3
PROFILE_AT = (905.0, 1095.0)       # his profile (facing left): its anchor and scale
PROFILE_S = 0.56
CU_PIECE = (690.0, 905.0)          # the chest-piece on the steel
FOUR_AT = (950.0, 1240.0)


def motion_blur(t, T):
    return 1


def _seg(name, s0, s1, at, speed=1.0, **kw):
    return C.Seg(C.clip(name), s0, s1, at=at, speed=speed, **kw)


def _u(t, span):
    return clamp((t - span[0]) / (span[1] - span[0]))


def _seek(u):
    """A safecracker's turn: quick off the mark, then creeping onto the number."""
    u = clamp(u)
    return 1.0 - (1.0 - u) ** 3 * (1.0 + 3.0 * u)


# ============================================================================ the lock
def dial_angle(t):
    """The dial (degrees clockwise) at s06 time t: still, then right, left, right, then the little
    turn left that draws the bolt."""
    a = DIAL_AT[0]
    for (t0, t1), a1 in zip(TURNS, DIAL_AT[1:]):
        if t < t0:
            return a
        if t < t1:
            return lerp(a, a1, _seek((t - t0) / (t1 - t0)))
        a = a1
    return a - 40.0 * ease("inout", _u(t, T_BOLT))


def lock_state(t):
    """The lock at s06 time t: dict(dial, wheels, dots, line, fence, bolt) for Bk.lock_cutaway and
    the dial. Each wheel turns with the dial until its gate comes up under the fence (the far
    wheel on the first turn, the middle one on the second, the near one on the last), then waits."""
    a = dial_angle(t)
    wheels, dots = [], []
    for i in range(3):
        k = GATE_WHEEL.index(i)
        wheels.append(0.0 if t >= GATES[k] else a - DIAL_AT[k + 1])
        dots.append(clamp((t - GATES[k]) / 0.22))
    return dict(dial=a, wheels=tuple(wheels), dots=tuple(dots), line=ease("inout", _u(t, T_LINE)),
                fence=clamp((t - T_FENCE) / 0.16), bolt=_u(t, T_BOLT))


def _axle_end():
    s = LOCK_S
    return (LOCK_AT[0] + Bk.LOCK_WHEELS[0] * s - Bk.LOCK_R * s - 50.0 * s, LOCK_AT[1])


def _tube_pts(ear):
    """The stethoscope's tube in the close-up: from his ear, under his jaw, across to the steel."""
    y = (ear[0] - 80.0, WINDOW[1] - 22.0)
    return F.spline([ear, (ear[0] - 22.0, ear[1] + 110.0), y, (CU_PIECE[0] + 70.0, WINDOW[1] - 14.0),
                     (CU_PIECE[0] + 6.0, CU_PIECE[1] + 30.0), CU_PIECE], n=8, closed=False)


def closeup(c, t, lock=None, color=K.PAPER, profile=True, face=None, cut=None, chalk=None, zoom=1.0,
            clicks=GATES, glint=0.0, four=0.0):
    """The dial in close-up over the lock cut away in chalk (frame px; whole frame). lock: a
    lock_state() dict (default: this scene's at t). color: the chalk and the dial's ticks (RED for
    s07). profile: his listening profile and the stethoscope. cut / chalk: how far the face is cut
    away and the lock drawn on (default: this scene's beats). zoom: a slow push about the frame's
    middle. clicks: the times the gates' clicks ripple (and run up the tube). four: step 4's circle."""
    lock = lock or lock_state(t)
    cut = ease("out3", _u(t, T_CUTAWAY)) if cut is None else cut
    chalk = _u(t, T_CHALK) if chalk is None else chalk
    c.save()
    if zoom != 1.0:
        c.translate(540.0, 960.0)
        c.scale(zoom, zoom)
        c.translate(-540.0, -960.0)
    Bk.vault_door(c, CAM_CU, t, dial=lock["dial"], dial_color=color, face=face, numerals=True)
    # the face cut away: black, edged in chalk as it opens downward
    x0, y0, x1, y1 = WINDOW
    yb = lerp(y0, y1, cut)
    if cut > 0.0:
        Bk.rect(c, (x0, y0, x1, yb), K.INK, seed=601, amp=0.5)
        K.chalk_line(c, [(x0, y0), (x1, y0)], clamp(cut * 3.0), 5.0, color, seed=602, alpha=0.85)
        K.chalk_line(c, [(x0, y0), (x0, yb)], 1.0, 4.0, color, seed=603, alpha=0.6)
        K.chalk_line(c, [(x1, y0), (x1, yb)], 1.0, 4.0, color, seed=604, alpha=0.6)
        if cut >= 1.0:
            K.chalk_line(c, [(x0, y1), (x1, y1)], 1.0, 4.0, color, seed=605, alpha=0.6)
    gates = None
    if chalk > 0.0:
        c.save()
        c.new_path()
        c.rectangle(x0 + 4.0, y0 + 4.0, (x1 - x0 - 8.0) * ease("out", chalk), yb - y0 - 8.0)
        c.clip()
        out = Bk.lock_cutaway(c, LOCK_AT, LOCK_S, lock["wheels"], dots=lock["dots"], line=lock["line"],
                              fence=lock["fence"], bolt=lock["bolt"], color=color, alpha=0.95, seed=611)
        gates = out["gates"]
        c.restore()
        # the spindle: from the wheels' axle up to the dial
        a, b = _axle_end(), CU_DIAL
        L = math.dist(a, b)
        stop = (b[0] - (b[0] - a[0]) / L * CU_ZOOM * Bk.DIAL_R * 1.25, b[1] - (b[1] - a[1]) / L * CU_ZOOM * Bk.DIAL_R * 1.25)
        K.dashes(c, [a, stop], color, 4.0, 20.0, 13.0, ease("out", chalk), seed=612, alpha=0.6)
    # the clicks: a ripple out of each gate as it comes up
    if gates is not None:
        for k, t0 in enumerate(clicks):
            if t0 is None or not t0 <= t < t0 + 1.0:
                continue
            g = gates[GATE_WHEEL[k]]
            K.ripple(c, g, t, t0, color, n=2, every=0.12, life=0.6, r0=10.0, r1=70.0 - 8.0 * k, width=5.0,
                     seed=620 + k, alpha=0.9)
    if four > 0.0:
        K.circled(c, "4", FOUR_AT, 40.0, four, color, width=5.0, seed=13, alpha=0.95)
    if profile:
        _listener(c, t, clicks, glint, color)
    c.restore()


def _listener(c, t, clicks, glint, color):
    """His profile at the right, facing the dial, the stethoscope from his ear to the steel; each
    click runs up the tube as a bead of chalk and rings in his ear."""
    c.save()
    c.new_path()
    c.rectangle(0.0, 0.0, 1080.0, WINDOW[1] - 2.0)
    c.clip()
    c.save()
    c.translate(PROFILE_AT[0], 0.0)
    c.scale(-1.0, 1.0)
    c.translate(-PROFILE_AT[0], 0.0)
    marks = F.cracker(c, PROFILE_AT, PROFILE_S, look=0.15, glint=glint, t=t, field=K.STEEL)
    c.restore()
    ear = (2.0 * PROFILE_AT[0] - marks["ear"][0], marks["ear"][1])
    tube = _tube_pts(ear)
    bass.line_band(c, tube, K.INK, width=15.0, seed=631)
    bass.line_band(c, tube, K.GOLD, width=9.0, seed=632)
    bass.fill_polys(c, [D.circle_pts(CU_PIECE, 30.0, n=32)], K.INK)
    bass.fill_polys(c, [D.circle_pts(CU_PIECE, 24.0, n=28)], K.GOLD)
    bass.fill_polys(c, [D.circle_pts(CU_PIECE, 12.0, n=20)], K.INK)
    c.restore()
    L = K.poly_len(tube)
    for k, t0 in enumerate(clicks):
        if t0 is None:
            continue
        a = (t - t0) / T_TUBE
        if 0.0 <= a < 1.0:                         # the click running up the tube
            p, _ = K.poly_at(tube[::-1], L * ease("in", a))
            K.dot(c, p, 9.0, K.PAPER, seed=640 + k, alpha=0.95)
        K.ripple(c, ear, t, t0 + T_TUBE, color, n=2, every=0.12 - 0.02 * k, life=0.6 - 0.05 * k,
                 r0=14.0, r1=100.0 - 16.0 * k, width=5.0, seed=650 + k, alpha=0.85)


# ============================================================================ the crew at the door
@lru_cache(maxsize=None)
def perfs():
    d = {}
    d["architect"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 0.0, 0.12, travel=0.0, lean=-3.0)], facing=1)
    d["knight"] = C.perf("knight", [_seg("17_08", 5.7, 6.0, 0.0, 0.03, travel=0.0)], facing=1)
    d["cracker"] = C.perf("cracker", [_seg("104_02", 5.7, 7.3, 0.0, 0.12, travel=0.0, lean=12.0)], facing=-1)
    return d


def _dry(who, st, pose, x, facing):
    """A figure's joints (set px) without drawing it."""
    surf = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    return C.draw(cairo.Context(surf), who, st, pose, x, 0.0, FIG_V, facing, rim=False)


def _stepped(st, u, dist, fc, lift=18.0):
    """Two half steps, the far foot then the near, carrying a standing pose `dist` figure units
    along facing fc (negative: backing away), u 0..1."""
    if u <= 0.0:
        return st
    feet = dict(st["feet"])
    a = ease("inout", clamp(u * 2.0))
    b = ease("inout", clamp(u * 2.0 - 1.0))
    for side, v in (("far", a), ("near", b)):
        x, h, p = feet[side]
        up = lift * math.sin(math.pi * v) if 0.0 < v < 1.0 else 0.0
        feet[side] = (x + fc * dist * v, min(h, -up), p + 14.0 * math.sin(math.pi * v))
    px, py = st["pelvis"]
    m = 0.5 * (a + b)
    return dict(st, feet=feet, pelvis=(px + fc * dist * m, py - 5.0 * math.sin(math.pi * 2.0 * m) ** 2))


def _ik(p, x):
    return ("ik", ((p[0] - x) / FIG_V, p[1] / FIG_V))


def door_open(t):
    return ease("inout", _u(t, T_SWING))


def wheel_at(t):
    return WHEEL_TURN * ease("inout", _u(t, T_WHEEL))


def bolts_at(t):
    return _u(t, T_WHEEL)


def _spoke(ang, opened=0.0):
    """Where the spoke he holds is (set px), the wheel turned by ang degrees and the door opened."""
    th = math.radians(88.0 * opened)
    fc = Bk.HINGE_X + (Bk.WHEEL_C[0] - Bk.HINGE_X) * math.cos(th)
    a = math.radians(SPOKE + ang)
    return (fc + Bk.WHEEL_R * math.cos(a) * math.cos(th), Bk.WHEEL_C[1] + Bk.WHEEL_R * math.sin(a))


def cracker_at(t, tt):
    """(st, pose, x, facing, piece): the Cracker at the dial, facing west. piece: where his
    chest-piece is (set px), held to the door or hanging on its tube."""
    st, pose = perfs()["cracker"](tt)
    x = CR_X[0]
    st = _stepped(st, _u(tt, T_STEP_IN), (CR_X[0] - CR_X[1]) / FIG_V, -1)
    st = _stepped(st, _u(tt, T_BACK), -(CR_BACK - CR_X[1]) / FIG_V, -1)
    lean = 3.0 * ease("inout", _u(tt, T_KNOB)) * (1.0 - ease("inout", _u(tt, T_GRIP)))
    lean -= 14.0 * math.sin(math.pi * _u(tt, T_HEAVE))
    pose.lean += lean
    j = _dry("cracker", st, pose, x, -1)
    hang_n, hang_f = j["hand_near"], j["hand_far"]
    neck = (lerp(j["head"][0], j["shoulder_near"][0], 0.55) - 3.0 * RS, lerp(j["head"][1], j["shoulder_near"][1], 0.7))
    hang_piece = (neck[0], neck[1] + 34.0 * RS)
    # the far hand: the chest-piece up to the steel, held there, let go when he turns to the wheel
    u_set, u_go = ease("inout", _u(tt, T_PIECE)), ease("inout", _u(tt, T_LET_GO))
    if u_set > 0.0 and u_go < 1.0:
        tgt = (lerp(lerp(hang_f[0], PIECE_AT[0], u_set), hang_f[0], u_go),
               lerp(lerp(hang_f[1], PIECE_AT[1], u_set), hang_f[1], u_go))
        pose.arms["far"] = _ik(tgt, x)
        piece = tgt if u_go <= 0.0 else (lerp(tgt[0], hang_piece[0], u_go), lerp(tgt[1], hang_piece[1], u_go))
    else:
        piece = hang_piece
    # the near hand: the knob, then the wheel's spoke, round with it, heave, let go
    tgt = None
    if tt >= T_KNOB[0] and tt < T_GRIP[0]:
        k = ease("inout", _u(tt, T_KNOB))
        tgt = (lerp(hang_n[0], KNOB_GRIP[0], k), lerp(hang_n[1], KNOB_GRIP[1], k))
    elif tt >= T_GRIP[0] and tt < T_HEAVE[1] + 0.3:
        sp = _spoke(wheel_at(tt), door_open(tt))
        k = ease("inout", _u(tt, T_GRIP))
        tgt = (lerp(KNOB_GRIP[0], sp[0], k), lerp(KNOB_GRIP[1], sp[1], k))
        if tt >= T_HEAVE[1]:
            g = ease("inout", (tt - T_HEAVE[1]) / 0.3)
            tgt = (lerp(sp[0], hang_n[0], g), lerp(sp[1], hang_n[1], g))
    if tgt is not None:
        pose.arms["near"] = _ik(tgt, x)
    return st, pose, x, -1, piece


def crew_rows(t, tt):
    """[(who, st, pose, x, facing, piece)] back to front."""
    d = perfs()
    rows = []
    for who, (x, x1) in (("knight", KNIGHT_X), ("architect", ARCH_X)):
        st, pose = d[who](tt)
        st = _stepped(st, _u(tt, T_DRAWN[who]), (x1 - x) / FIG_V, 1)
        pose.lean -= 4.0 * ease("inout", clamp((tt - T_SWING[0] - 0.3) / 1.2))      # they straighten as it opens
        pose.head -= 6.0 * ease("inout", clamp((tt - T_SWING[0] - 0.2) / 1.0))
        if who == "knight":
            pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)
        rows.append((who, st, pose, x, 1, None))
    st, pose, x, fc, piece = cracker_at(t, tt)
    rows.append(("cracker", st, pose, x, fc, piece))
    return rows


def _draw_crew(c, cam, t, tt, rows=None):
    g = door_open(t)
    rim_w = 4.0 / cam.zoom
    for who, st, pose, x, fc, piece in rows or crew_rows(t, tt):
        rim = lerp(C.RIM[who], K.GOLD, 0.85 * ease("inout", clamp(g * 1.6)))
        light = (lerp(-0.6, 0.0, g), lerp(-0.8, -1.0, g))
        j = C.draw(c, who, st, pose, x, 0.0, FIG_V, fc, bg=K.INK, rim=rim, rim_w=rim_w * (1.0 + 0.6 * g),
                   light=light)
        if who == "cracker":
            ear = (j["head"][0] + 2.0 * RS, j["head"][1] + 3.0 * RS)
            Bk.stethoscope(c, ear, piece, RS, K.INK, rim=rim)


# ============================================================================ the shots
def cam_a(t):
    return Bk.Cam.toward(CAM_DIAL, CAM_WIDE, ease("inout", _u(t, T_PULL)), Bk.DIAL_C)


def cam_c(t):
    return Bk.Cam.toward(CAM_WIDE, CAM_GOLD, ease("inout", _u(t, T_PUSH)), OPENING)


def _door(c, t, tt, cam):
    lk = lock_state(t)
    g = door_open(t)
    Bk.vault_door(c, cam, t, open=g, bolts=bolts_at(t), wheel=wheel_at(t), dial=lk["dial"], light="gold",
                  inside=lambda cc: Bk.vault_through(cc, t))
    rows = crew_rows(t, tt)
    with cam.on(c):
        if g > 0.0:
            for who, st, pose, x, fc, piece in rows:
                Bk.spill_shadow(c, x + st["pelvis"][0] * FIG_V, g)
        _draw_crew(c, cam, t, tt, rows)


def _marks(c, t, cam):
    """Step 4's chalk on the dial, as s05 left it (seeds and sizes the same), fading off."""
    a = 0.9 * (1.0 - ease("inout", _u(t, T_MARK)))
    if a <= 0.0:
        return
    with cam.on(c):
        K.dot(c, Bk.DIAL_C, 4.0, K.PAPER, seed=1097, alpha=a / 0.9)
    p = cam.to_frame(Bk.DIAL_C)
    r = (Bk.DIAL_R + 8.0) * cam.zoom
    w = 2.5 * cam.zoom * 0.45
    K.chalk_circle(c, p, r, 1.0, w, K.PAPER, seed=137, alpha=a)
    K.chalk_line(c, [p, (p[0] + 0.5 * r * 0.6, p[1] - 0.5 * r * 0.8)], 1.0, w, K.PAPER, seed=138, alpha=a)


INSERTS = (S.Flash(T_SWING[0], 2, K.GOLD),)          # the seal breaks: gold, flat


def render(f, t, T):
    S.play(f, t, T, render_plain, INSERTS)


def render_plain(f, t, T):
    K.scene_setup(f, K.DEEP)
    tt = K.twos(t)
    with f.screen() as c:
        if t < T_CU:
            cam = cam_a(t)
            _door(c, t, tt, cam)
            _marks(c, t, cam)
        elif t < T_WIDE:
            closeup(c, t, zoom=1.0 + 0.05 * ease("inout", (t - T_CU) / (T_WIDE - T_CU)),
                    glint=_u(t, T_GLINT) if t < T_GLINT[1] else 0.0, four=clamp((t - T_FOUR) / 0.45))
        else:
            _door(c, t, tt, cam_c(t))
        K.stopwatch(c, STOPWATCH[0], STOPWATCH[1], K.heist_beats(FILM_T0 + t))


# ============================================================================ cues
def _pan_x(fx):
    return round(clamp((fx - 540.0) / 540.0, -1.0, 1.0), 2)


def _pan(t, p):
    cam = cam_a(t) if t < T_CU else cam_c(t)
    return _pan_x(cam.to_frame(p)[0])


def cues(T):
    out = []
    # the door: his two steps in (far foot, then near), the chest-piece on the steel, the knob
    mid = 0.5 * (T_STEP_IN[0] + T_STEP_IN[1])
    out.append(Cue(mid, "a soft step on a steel-plated floor: the Cracker steps up to the vault door", gain_db=-24,
                   pan=_pan(mid, (CR_X[0], 0.0))))
    out.append(Cue(T_STEP_IN[1], "a soft step on a steel-plated floor", gain_db=-25,
                   pan=_pan(T_STEP_IN[1], (CR_X[1], 0.0))))
    out.append(Cue(T_PIECE[1], "the stethoscope's chest-piece touches the steel door: a tiny metallic tock",
                   gain_db=-20, pan=_pan(T_PIECE[1], PIECE_AT)))
    out.append(Cue(T_KNOB[1], "fingers settle on the dial's knurled knob: a faint tick", gain_db=-26,
                   pan=_pan(T_KNOB[1], KNOB_GRIP)))
    # the lock
    out.append(Cue(T_CU, "a paper cut and a chalk sketch: the door's face is cut away and the lock is drawn in "
                         "(quick chalk strokes)", gain_db=-18, dur=T_CHALK[1] - T_CU))
    words = ("right", "left", "right")
    for (t0, t1), w in zip(TURNS, words):
        out.append(Cue(t0, f"the dial spins {w}: a fast run of fine ratchet ticks slowing to a creep (heard close "
                           f"through the stethoscope)", gain_db=-20, pan=-0.26, dur=t1 - t0))
    for k, (t0, pitch) in enumerate(zip(GATES, ("LOW", "MID", "HIGH"))):
        out.append(Cue(t0, f"a gate falls under the fence: a single crisp lock click, pitched {pitch} (intimate, in "
                           f"his ear)", gain_db=-9, pan=0.15))
    out.append(Cue(T_LINE[0], "a quick chalk stroke: the three dots joined in one straight line", gain_db=-18, pan=0.0))
    out.append(Cue(T_FOUR, "a chalk circle: step 4", gain_db=-20, pan=0.76))
    out.append(Cue(T_FENCE, "CLUNK: the fence drops into the lined-up gates", gain_db=-5, pan=0.0))
    out.append(Cue(T_GLINT[0] + 0.05, "a glint on his spectacles: a tiny bright ting", gain_db=-22, pan=0.7))
    out.append(Cue(T_BOLT[0], "the lock's bolt draws back: a short heavy metal slide", gain_db=-13, pan=0.6))
    # the door
    out.append(Cue(T_LET_GO[0] + 0.15, "the chest-piece drops on its tube and taps his coat", gain_db=-26,
                   pan=_pan(T_LET_GO[0] + 0.15, PIECE_AT)))
    out.append(Cue(T_WHEEL[0], "the great wheel turns: a slow heavy iron ratchet", gain_db=-11,
                   pan=_pan(T_WHEEL[0], Bk.WHEEL_C), dur=T_WHEEL[1] - T_WHEEL[0]))
    for k in range(Bk.N_BOLTS):                     # the rolling run: each bolt as it comes out
        s = k / float(Bk.N_BOLTS) * 0.72
        tb = T_WHEEL[0] + (s + 0.14) * (T_WHEEL[1] - T_WHEEL[0])
        a = math.radians(-90.0 + 15.0 + 30.0 * k)
        p = (Bk.VDOOR_C[0] + Bk.VDOOR_R * math.cos(a), Bk.VDOOR_C[1] + Bk.VDOOR_R * math.sin(a))
        out.append(Cue(round(tb, 3), "a heavy steel bolt withdraws from the door frame: one clack of a rolling run "
                                     "round the rim", gain_db=-15, pan=_pan(tb, p)))
    out.append(Cue(T_HEAVE[0], "the old man heaves on the wheel: a strained breath", gain_db=-20,
                   pan=_pan(T_HEAVE[0], (CR_X[1], -150.0))))
    out.append(Cue(T_SWING[0], "the vault door's great hinge groans as the door swings slowly open", gain_db=-9,
                   pan=_pan(T_SWING[0], (Bk.HINGE_X, -110.0)), dur=T_SWING[1] - T_SWING[0]))
    out.append(Cue(T_SWING[0] + 0.1, "a brass swell: gold light floods out of the vault", gain_db=-8,
                   dur=T.duration - T_SWING[0] - 0.1))
    for k, tb in enumerate((T_BACK[0] + 0.5 * (T_BACK[1] - T_BACK[0]), T_BACK[1])):
        out.append(Cue(tb, "a soft step back on the steel floor", gain_db=-26, pan=_pan(tb, (CR_BACK, 0.0))))
    for who, (x0, x1) in (("architect", ARCH_X), ("knight", KNIGHT_X)):      # drawn to the gold: two steps each
        t0, t1 = T_DRAWN[who]
        for tb, xb in ((0.5 * (t0 + t1), 0.5 * (x0 + x1)), (t1, x1)):
            out.append(Cue(tb, f"a soft step on the steel floor: the {who} steps toward the open vault", gain_db=-27,
                           pan=_pan(tb, (xb, 0.0))))
    out.append(Cue(T_REST, "the open door settles against its stop: a deep soft thud", gain_db=-14,
                   pan=_pan(T_REST, (Bk.HINGE_X, -110.0))))
    return out
