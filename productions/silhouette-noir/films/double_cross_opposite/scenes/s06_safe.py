"""s06 SAFE (80-94). The vault door, the stethoscope, the dial from straight on, the bolts, the gold.

  The door (0-3): s05's last frame, matched on the dial in her small light (the same pool, the same
    cut). The camera glides back off it to the great round door in the dark: she holds the light
    on the dial, the Knight stands with his back to them watching the way they came, and the
    Cracker steps in from the right, goes down on one knee, sets his stethoscope to the steel
    (a tock) and takes the knob.
  The stethoscope (3-4.5): extreme close-up. Its bell on the steel under the dial's edge, the
    tube up to his ear (his profile, cut like a cameo): the lock's soft ticks run up the tube as
    AMBER beads and ring in his ear.
  The dial (4.5-10): straight on, filling the frame, its hand-cut numerals. His fingers on the
    knob turn it right, left, right, an AMBER loop arrow sweeping round with each turn; at each
    gate a click and a ripple off the index (low, mid, high); the fence drops (9.5, CLUNK) and the
    lock's bolt draws back (the dial a little left).
  The gold (10-14): the door again. He lets the stethoscope go, gets up off his knee onto the
    wheel and turns it: the twelve bolts withdraw round the rim; he heaves, backs out of its way,
    and the door swings open toward us (the circle narrows to an ellipse), AMBER flooding out
    over the three of them as her light clicks off and the Knight turns to it. Three looks go in:
    RED to the gold (12.5), AMBER to the gold (13.0), PAPER to the deposit boxes (13.5).

The door is bank.vault_door (north-looking set px: its hinge on the right). The cast stand at
FIG_V, DOUBLE CROSS's cheat at the door (it is a giant); s07 shares it.
"""
import math
from functools import lru_cache

import cairo

from engine import bass
from engine import draw as D
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import faces as F
from films.double_cross_opposite import kit as K

k = K.k
W, H = K.W, K.H
INK, PAPER, AMBER, RED, STEEL = K.INK, K.PAPER, K.AMBER, K.RED, K.STEEL

FILM_T0 = 80.0
FIG_V = 0.27                       # the cast at the vault door (FIG_S x 1.35: the door is a giant)
RS = FIG_V / Bk.FIG_S              # their props and rims scale with them
RIM_W = 4.0

# ---------------------------------------------------------------------------- beats
T_PULL = (0.5, 2.25)               # the camera glides back off the dial to the door
T_STEP_IN = (0.5, 1.1)             # the Cracker steps in from the right ...
T_KNEEL = (1.05, 1.55)             # ... goes down on one knee ...
T_PIECE = (1.5, 1.95)              # ... sets the chest-piece to the steel (the tock) ...
T_KNOB = (2.0, 2.45)               # ... and takes the knob
T_ECU = 3.0                        # cut: the stethoscope, close
T_TICKS = (3.5, 4.0)               # soft ticks in the lock: AMBER beads up the tube to his ear
T_TUBE = 0.3                       # a tick's run up the tube
T_DIAL = 4.5                       # cut: the dial, straight on
T_HAND_IN = (4.5, 4.72)            # his fingers come onto the knob
TURNS = ((4.75, 6.0), (6.25, 7.5), (7.75, 9.0))    # right, left, right
GATES = (6.0, 7.5, 9.0)            # a gate under the fence: a click (low, mid, high) and a ripple
DIAL_AT = (0.0, 210.0, -90.0, 60.0)   # the dial (deg clockwise) at rest and at each gate
T_FENCE = 9.5                      # CLUNK: the fence drops into the gates
T_BOLT = (9.6, 9.95)               # the lock's bolt draws back (the dial a little left)
T_DOOR = 10.0                      # cut: the door
T_LET_GO = (10.0, 10.3)            # he lets the chest-piece go: it drops on its tube
T_RISE = (10.0, 10.45)             # up off his knee, his hand to a spoke of the wheel
T_WHEEL = (10.45, 11.0)            # the wheel turns; the twelve bolts withdraw round the rim
T_HEAVE = (11.0, 11.25)            # he heaves on it
T_SWING = (11.1, 12.9)             # the door swings open, gold flooding out
T_LIGHT_OFF = 11.3                 # her light clicks off
T_BACK = (11.3, 11.9)              # he backs out of the door's way
T_TURN_K = (11.4, 11.65)           # the Knight turns from the way they came to the gold
T_REST = T_SWING[1]                # the door comes to rest against its stop
T_LOOKS = (("knight", 12.5), ("cracker", 13.0), ("architect", 13.5))   # RED, AMBER: the gold; PAPER: the boxes
T_PUSH = (11.5, 14.0)              # the camera eases in on the gold

# ---------------------------------------------------------------------------- places (north-looking set px)
KNIGHT_X = 382.0                   # his pelvis: at the left, his back to them, watching the way they came
HER_X = 420.0                      # hers: her light on the dial (her hand out of s05's frame)
CR_X = (654.0, 580.0, 660.0)       # the Cracker's: in from the right, at the dial (kneeling), backed off
PIECE_AT = (553.0, -120.0)         # the chest-piece on the steel, under the dial (as the close-up has it)
KNOB_GRIP = (549.0, -154.0)        # his fingers on the knob (its lower edge)
SPOKE = -18.0                      # the wheel's spoke he takes (deg; the wheel turns it up)
WHEEL_TURN = 45.0
LIGHT_AT = (Bk.DIAL_C[0] + 2.0, Bk.DIAL_C[1] + 4.0)    # her light's pool on the dial (s05's)
LIGHT_R = 30.0
FACE_D = lerp(STEEL, INK, 0.45)    # the door's steel in the dark (s05's)
OPENING = Bk.VDOOR_C
GOLD_AT = (548.0, -44.0)           # the gold seen through the door (vault_through's stack)
BOXES_AT = (572.0, -172.0)         # the deposit boxes on its far wall
DARK0 = ((1.02, 0.92), (1.3, 0.75), (2.0, 0.7), (3.2, 0.7))     # INK steps beyond her pool (x LIGHT_R, alpha): s05's
DARK1 = ((1.05, 0.42), (1.45, 0.38), (2.1, 0.42), (3.4, 0.5))   # ... and once the eyes are used to it

# ---------------------------------------------------------------------------- cameras
CAM_DIAL = Bk.Cam(Bk.DIAL_C[0], Bk.DIAL_C[1], 7.0)     # s05's last frame
CAM_DOOR = Bk.Cam(528.0, -128.0, 3.2)                  # the door and the three of them
CAM_GOLD = Bk.Cam(522.0, -120.0, 3.3)                  # in a little on the gold

# ---------------------------------------------------------------------------- the close-ups (frame px)
ECU_DIAL = (128.0, 372.0)          # the stethoscope: the dial's lower right corner, top left ...
ECU_DIAL_R = 330.0
ECU_PIECE = (352.0, 1112.0)        # ... the bell on the steel ...
ECU_PIECE_R = 88.0
ECU_FACE = (812.0, 2060.0)         # ... his profile at the right, facing it (its neck anchor) ...
ECU_FACE_S = 1.55
ECU_JOIN = (640.0, 1650.0)         # ... where the tube from his ear meets the one to the bell
DIAL_P = (540.0, 900.0)            # the dial, straight on
DIAL_RF = 372.0
LOOP_R = DIAL_RF * 1.27            # the loop arrows round it
KNOB_R = DIAL_RF * 0.36


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


def _lerp2(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))


# ============================================================================ the lock and the door
def dial_angle(t):
    """The dial (degrees clockwise) at t: still, then right, left, right, then the little turn
    left that draws the lock's bolt."""
    a = DIAL_AT[0]
    for (t0, t1), a1 in zip(TURNS, DIAL_AT[1:]):
        if t < t0:
            return a
        if t < t1:
            return lerp(a, a1, _seek((t - t0) / (t1 - t0)))
        a = a1
    return a - 40.0 * ease("inout", _u(t, T_BOLT))


def turn_of(t):
    """(k, u) of the turn in progress or just made (u its progress), or (None, 0)."""
    for i, (t0, t1) in enumerate(TURNS):
        nxt = TURNS[i + 1][0] if i + 1 < len(TURNS) else T_FENCE
        if t0 <= t < nxt:
            return i, _seek((t - t0) / (t1 - t0))
    return None, 0.0


def wheel_at(t):
    return WHEEL_TURN * ease("inout", _u(t, T_WHEEL))


def bolts_at(t):
    return _u(t, T_WHEEL)


def door_open(t):
    return ease("inout", _u(t, T_SWING))


def _spoke(ang, opened=0.0):
    """The spoke he holds (set px), the wheel turned by ang degrees and the door opened."""
    th = math.radians(88.0 * opened)
    fc = Bk.HINGE_X + (Bk.WHEEL_C[0] - Bk.HINGE_X) * math.cos(th)
    a = math.radians(SPOKE + ang)
    return (fc + Bk.WHEEL_R * math.cos(a) * math.cos(th), Bk.WHEEL_C[1] + Bk.WHEEL_R * math.sin(a))


# ============================================================================ the crew at the door
@lru_cache(maxsize=None)
def perfs():
    d = {}
    d["knight"] = C.perf("knight", [_seg("17_08", 5.7, 6.0, 0.0, 0.03, travel=0.0)], facing=1)
    d["architect"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 0.0, 0.12, travel=0.0, lean=-3.0)], facing=1)
    d["cracker"] = C.perf("cracker", [
        _seg("104_02", 5.7, 7.3, 0.0, 0.12, travel=0.0, lean=12.0),
        _seg("23_03", 3.72, 3.8, T_KNEEL[0], 0.02, travel=0.0, blend=T_KNEEL[1] - T_KNEEL[0]),
        _seg("104_02", 5.7, 7.3, T_RISE[0], 0.12, travel=0.0, lean=8.0, blend=T_RISE[1] - T_RISE[0])], facing=-1)
    return d


def _dry(who, st, pose, x, facing):
    """A figure's joints (set px) without drawing it."""
    surf = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    return C.draw(cairo.Context(surf), who, st, pose, x, 0.0, FIG_V, facing, rim=False)


def _reach(who, st, pose, x, facing, side, target):
    """Set an arm (as angles) so the hand lands on target (set px), the elbow bent down and forward
    (the paperdoll's own IK can throw it up behind)."""
    fg = C.fig(who)
    sh = _dry(who, st, pose, x, facing)["shoulder_" + side]
    l1, l2 = fg.upper * FIG_V, (fg.fore + 0.55 * fg.hand_r) * FIG_V
    dx, dy = target[0] - sh[0], target[1] - sh[1]
    d = clamp(math.hypot(dx, dy), abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    th = math.atan2(dy, dx)
    al = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2.0 * l1 * d), -1.0, 1.0))
    els = [(sh[0] + l1 * math.cos(th + sg * al), sh[1] + l1 * math.sin(th + sg * al)) for sg in (1.0, -1.0)]
    el = max(els, key=lambda q: q[1])
    wr = (sh[0] + d * math.cos(th), sh[1] + d * math.sin(th))
    a1 = math.degrees(math.atan2(facing * (el[0] - sh[0]), el[1] - sh[1]))
    a2 = math.degrees(math.atan2(facing * (wr[0] - el[0]), wr[1] - el[1]))
    pose.arms[side] = ("ang", a1 - pose.lean, a2 - a1)


def _shift(st, dx):
    """A state moved dx figure units along x (pelvis and feet)."""
    feet = {side: (f[0] + dx, f[1], f[2]) for side, f in st["feet"].items()}
    return dict(st, feet=feet, pelvis=(st["pelvis"][0] + dx, st["pelvis"][1]))


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


def _aim_bent(who, st, pose, x, facing, target, upper=28.0):
    """Her near arm bent, the upper arm hanging `upper` degrees forward, the forearm (and the light
    in her fist) pointing at target (set px)."""
    fg = C.fig(who)
    sh = _dry(who, st, pose, x, facing)["shoulder_near"]
    a1 = upper + pose.lean
    el = (sh[0] + facing * math.sin(math.radians(a1)) * fg.upper * FIG_V,
          sh[1] + math.cos(math.radians(a1)) * fg.upper * FIG_V)
    a2 = math.degrees(math.atan2(facing * (target[0] - el[0]), target[1] - el[1]))
    pose.arms["near"] = ("ang", upper, a2 - a1)


def knight_at(tt):
    """(st, pose, x, sx): his back to them, watching the way they came; he turns to the gold."""
    st, pose = perfs()["knight"](tt)
    x = KNIGHT_X - st["pelvis"][0] * FIG_V
    e = ease("inout", _u(tt, T_TURN_K))
    sx = -math.cos(math.pi * e)
    pose.hold["far"] = Bk.hold_sack(0.0, seed=7, floor=0.0)
    g = door_open(tt)
    pose.lean -= 4.0 * ease("inout", clamp((tt - T_SWING[0] - 0.4) / 1.2))       # he straightens to it
    pose.head -= 5.0 * g
    return st, pose, x, sx


def her_at(tt):
    """(st, pose, x, light_on): her light held on the dial; off and lowered when the gold comes."""
    st, pose = perfs()["architect"](tt)
    x = HER_X - st["pelvis"][0] * FIG_V
    on = tt < T_LIGHT_OFF
    lower = ease("inout", clamp((tt - T_LIGHT_OFF - 0.05) / 0.35))
    if lower < 1.0:
        nat = dict(pose.arms)
        _aim_bent("architect", st, pose, x, 1, LIGHT_AT)
        if lower > 0.0:
            a, b = pose.arms["near"], nat["near"]
            pose.arms["near"] = ("ang", lerp(a[1], b[1], lower), lerp(a[2], b[2], lower))
    pose.lean -= 3.0 * ease("inout", clamp((tt - T_SWING[0] - 0.3) / 1.2))
    pose.head -= 5.0 * door_open(tt)
    return st, pose, x, on


def cracker_at(tt):
    """(st, pose, x, piece): in, down on one knee at the dial, the chest-piece to the steel, the
    knob; up onto the wheel, turning it, the heave; backing off. piece: the chest-piece (set px)."""
    st, pose = perfs()["cracker"](tt)
    x = CR_X[0] - perfs()["cracker"](0.0)[0]["pelvis"][0] * FIG_V
    din = (CR_X[0] - CR_X[1]) / FIG_V
    if tt < T_STEP_IN[1]:
        st = _stepped(st, _u(tt, T_STEP_IN), din, -1)
    else:
        st = _shift(st, -din)
    if tt >= T_BACK[0]:
        st = _stepped(st, _u(tt, T_BACK), -(CR_X[2] - CR_X[1]) / FIG_V, -1)
    kneel = ease("inout", _u(tt, T_KNEEL)) * (1.0 - ease("inout", _u(tt, T_RISE)))
    pose.lean -= 17.0 * kneel                          # up on his knee, under the dial
    pose.head += 6.0 * kneel
    heave = math.sin(math.pi * _u(tt, T_HEAVE))
    pose.lean -= 12.0 * heave
    j = _dry("cracker", st, pose, x, -1)
    hang_n, hang_f = j["hand_near"], j["hand_far"]
    neck = (lerp(j["head"][0], j["shoulder_near"][0], 0.55) + 3.0 * RS, lerp(j["head"][1], j["shoulder_near"][1], 0.7))
    hang_piece = (neck[0] - 2.0 * RS, neck[1] + 30.0 * RS)
    # the far hand: the chest-piece up to the steel, held there, let go at the cut to the door
    u_set, u_go = ease("inout", _u(tt, T_PIECE)), ease("in", _u(tt, T_LET_GO))
    if u_set > 0.0 and u_go < 1.0:
        held = _lerp2(hang_f, PIECE_AT, u_set)
        tgt = _lerp2(held, hang_f, ease("inout", _u(tt, T_LET_GO)))
        _reach("cracker", st, pose, x, -1, "far", tgt)
        piece = _lerp2(held, hang_piece, u_go) if u_go > 0.0 else held
    else:
        piece = hang_piece
    # the near hand: the knob; then a spoke, round with it, the heave, let go
    tgt = None
    if T_KNOB[0] <= tt < T_DOOR:
        tgt = _lerp2(hang_n, KNOB_GRIP, ease("inout", _u(tt, T_KNOB)))
    elif T_DOOR <= tt < T_HEAVE[1] + 0.3:
        sp = _spoke(wheel_at(tt), door_open(tt))
        tgt = _lerp2(KNOB_GRIP, sp, ease("inout", _u(tt, (T_RISE[0], T_RISE[0] + 0.3))))
        if tt >= T_HEAVE[1]:
            tgt = _lerp2(sp, hang_n, ease("inout", (tt - T_HEAVE[1]) / 0.3))
    if tgt is not None:
        _reach("cracker", st, pose, x, -1, "near", tgt)
    return st, pose, x, piece


# ============================================================================ light and dark
def _darkness(c, cam, eyes, a=1.0):
    """The dark at the door: INK laid over it in cut steps beyond her pool (no blur), black as s05
    left it, then less so as the eyes get used to it (eyes 0..1). a scales it (the gold's light
    lifts it)."""
    if a <= 0.0:
        return
    p = cam.to_frame(LIGHT_AT)
    for i, ((r0, a0), (r1, a1)) in enumerate(zip(DARK0, DARK1)):
        bass.hole(c, p, lerp(r0, r1, eyes) * LIGHT_R * cam.zoom, INK, seed=640 + i,
                  rect=(-20.0, -20.0, W + 20.0, H + 20.0), n=96, alpha=lerp(a0, a1, eyes) * a)


def _her_pool(c, cam, t, dial, a=1.0):
    """Her small light on the dial: the door's face shows in its pool (as in s05)."""
    if a <= 0.0:
        return
    with cam.on(c):
        c.save()
        c.new_path()
        bass.iris_path(c, LIGHT_AT, LIGHT_R, seed=61, n=72)
        c.clip()
        Bk.door_face(c, t, dial=dial, face=FACE_D)
        c.restore()
        K.pool(c, LIGHT_AT, LIGHT_R * 1.15, LIGHT_R * 1.15, PAPER, alpha=0.16 * a, steps=4)


def _gold_gap(c, cam, t, g):
    """The crack of the opening the swinging door uncovers, gold through the dark (it is the light:
    the dark is not laid on it)."""
    th = math.radians(88.0 * g)
    cs, sn = math.cos(th), math.sin(th)
    fc = Bk.HINGE_X + (Bk.VDOOR_C[0] - Bk.HINGE_X) * cs
    left = fc - Bk.DOOR_T * sn - Bk.VDOOR_R * cs          # the swung leaf's nearest edge
    x0 = Bk.VDOOR_C[0] - Bk.VDOOR_R - 4.0
    seal = ease("out", clamp(g / 0.1)) * (1.0 - clamp((g - 0.3) / 0.2))
    if seal > 0.0:                                        # the seal breaks: light round the free edge
        cx, cy = Bk.VDOOR_C
        arc = [(cx + Bk.VDOOR_R * math.cos(math.radians(a)), cy + Bk.VDOOR_R * math.sin(math.radians(a)))
               for a in range(96, 266, 6)]
        with cam.on(c):
            K.pool(c, (cx - Bk.VDOOR_R + 6.0, cy), 46.0, 110.0, AMBER, alpha=0.3 * seal, steps=3)
            K.band(c, arc, AMBER, 7.0 * seal, seed=655, taper=(0.2, 0.2), alpha=0.95)
    if left <= x0:
        return
    with cam.on(c):
        c.save()
        c.new_path()
        c.arc(Bk.VDOOR_C[0], Bk.VDOOR_C[1], Bk.VDOOR_R - 0.5, 0.0, 2.0 * math.pi)
        c.clip()
        c.new_path()
        c.rectangle(x0, Bk.VDOOR_C[1] - Bk.VDOOR_R - 4.0, left - x0, 2.0 * Bk.VDOOR_R + 8.0)
        c.clip()
        Bk.vault_through(c, t)
        c.restore()


# ============================================================================ the door shots
def cam_a(t):
    return Bk.Cam.toward(CAM_DIAL, CAM_DOOR, ease("inout", _u(t, T_PULL)), Bk.DIAL_C)


def cam_d(t):
    return Bk.Cam.toward(CAM_DOOR, CAM_GOLD, ease("inout", _u(t, T_PUSH)), OPENING)


def _flipped(c, who, st, pose, x, sx, rim, rim_w, light=(-0.6, -0.8)):
    """Draw a figure (built facing +x) paper-turned by sx about its pelvis, in set px; returns its
    joints in set px."""
    xp = x + st["pelvis"][0] * FIG_V
    if abs(sx) < 0.03:
        sx = math.copysign(0.03, sx)
    c.save()
    c.translate(xp, 0.0)
    c.scale(sx, 1.0)
    c.translate(-xp, 0.0)
    j = C.draw(c, who, st, pose, x, 0.0, FIG_V, 1, bg=INK, rim=rim, rim_w=rim_w,
               light=(light[0] * math.copysign(1.0, sx), light[1]))
    dev = {kk: c.user_to_device(*v) for kk, v in j.items()}
    c.restore()
    return {kk: c.device_to_user(*v) for kk, v in dev.items()}


def shot_door(c, t, cam):
    """The great door and the three of them: in the dark by her light, then in the gold's."""
    tt = K.twos(t)
    g = door_open(t)
    dial = dial_angle(t)
    Bk.vault_door(c, cam, t, open=g, bolts=bolts_at(t), wheel=wheel_at(t), dial=dial, light="gold",
                  inside=lambda cc: Bk.vault_through(cc, t), face=FACE_D, glow=g)
    on = t < T_LIGHT_OFF
    dk = 1.0 - ease("inout", clamp(g * 2.2))
    _darkness(c, cam, ease("inout", _u(t, (0.6, 2.2))), dk)
    if g > 0.0 and dk > 0.0:
        _gold_gap(c, cam, t, g)
    if on:
        _her_pool(c, cam, t, dial)
    rim_w = RIM_W / cam.zoom
    out = {}
    with cam.on(c):
        cst, cpose, cx, piece = cracker_at(tt)
        kst, kpose, kx, ksx = knight_at(tt)
        ast, apose, ax, _ = her_at(tt)
        fl = C.hold_flashlight(on=on)
        apose.hold["near"] = fl
        if g > 0.0:
            for st, x in ((cst, cx), (ast, ax), (kst, kx)):
                Bk.spill_shadow(c, x + st["pelvis"][0] * FIG_V, g)
        jc = C.draw(c, "cracker", cst, cpose, cx, 0.0, FIG_V, -1, bg=INK, rim_w=rim_w)
        ear = (jc["head"][0] + 2.0 * RS, jc["head"][1] + 3.0 * RS)
        Bk.stethoscope(c, ear, piece, 0.42 * RS, INK, rim=lerp(INK, AMBER, 0.75))
        ja = C.draw(c, "architect", ast, apose, ax, 0.0, FIG_V, 1, bg=INK, rim_w=rim_w)
        jk = _flipped(c, "knight", kst, kpose, kx, ksx, None, rim_w)
        out = {"cracker": (jc, -1), "architect": (ja, 1), "knight": (jk, 1 if ksx >= 0 else -1)}
    lens, _ = C.lens_at(c, fl)
    if on and lens is not None:
        K.dot(c, lens, 2.2 * cam.zoom, PAPER, seed=651)
    # the three looks into the vault
    for who, t0 in T_LOOKS:
        if t < t0:
            continue
        j, fc = out[who]
        eye = cam.to_frame((j["head"][0] + fc * 3.0 * RS, j["head"][1] - 1.0 * RS))
        tgt = cam.to_frame(BOXES_AT if who == "architect" else GOLD_AT)
        col = {"knight": RED, "cracker": AMBER, "architect": PAPER}[who]
        K.sight_line(c, eye, tgt, t, t0, col, dur=0.4, march=26.0, r=6.0, gap=23.0, head=26.0,
                     seed=660 + len(who))


# ============================================================================ the stethoscope, close
def _ecu_tube(ear):
    """The tube in the close-up: from his ear down past his jaw to the join, and on to the bell."""
    a = F.spline([ear, (ear[0] - 30.0, ear[1] + 170.0), (ear[0] - 120.0, ECU_JOIN[1] - 60.0), ECU_JOIN], n=8,
                 closed=False)
    b = F.spline([ECU_JOIN, (ECU_JOIN[0] - 150.0, ECU_JOIN[1] + 10.0), (ECU_PIECE[0] + 120.0, ECU_PIECE[1] + 260.0),
                  (ECU_PIECE[0] + 40.0, ECU_PIECE[1] + 70.0), ECU_PIECE], n=8, closed=False)
    return a, b


def shot_ecu(c, t):
    """The bell on the steel, the tube up to his ear; the lock's ticks run up it."""
    K.fill(c, FACE_D)
    K.pool(c, (430.0, 1050.0), 760.0, 820.0, PAPER, alpha=0.2, steps=4)
    Bk.dial_face(c, ECU_DIAL, ECU_DIAL_R, dial_angle(t), color=PAPER, face=INK, bezel=lerp(FACE_D, PAPER, 0.2),
                 seed=1192, numerals=True)
    # his profile at the right, facing the bell (a cameo, mirrored)
    c.save()
    c.translate(ECU_FACE[0], 0.0)
    c.scale(-1.0, 1.0)
    c.translate(-ECU_FACE[0], 0.0)
    marks = F.cracker(c, ECU_FACE, ECU_FACE_S, look=0.5, t=t, field=lerp(FACE_D, PAPER, 0.12))
    c.restore()
    ear = (2.0 * ECU_FACE[0] - marks["ear"][0], marks["ear"][1])
    a, b = _ecu_tube(ear)
    for pts in (b, a):
        bass.line_band(c, pts, INK, width=30.0, seed=671)
        bass.line_band(c, pts, AMBER, width=19.0, seed=672)
    bass.fill_polys(c, [D.circle_pts(ear, 22.0, n=24)], INK)
    bass.fill_polys(c, [D.circle_pts(ear, 15.0, n=20)], AMBER)
    p, r = ECU_PIECE, ECU_PIECE_R
    bass.fill_polys(c, [D.circle_pts((p[0] + 10.0, p[1] + 12.0), r * 1.08, n=48)], INK, 0.5)    # its shadow on the steel
    bass.fill_polys(c, [D.circle_pts(p, r * 1.08, n=48)], INK)
    bass.fill_polys(c, [D.circle_pts(p, r, n=48)], AMBER)
    bass.fill_polys(c, [D.circle_pts(p, r * 0.74, n=40)], lerp(AMBER, INK, 0.35))
    bass.fill_polys(c, [D.circle_pts(p, r * 0.5, n=32)], INK)
    bass.ring(c, (p[0] - 6.0, p[1] - 6.0), r * 0.86, 5.0, lerp(AMBER, PAPER, 0.5), seed=673, n=48, alpha=0.7)
    # the ticks: a ring off the bell, a bead running up the tube, a ripple in his ear
    tube = b[::-1] + a[1:][::-1]
    L = K.poly_len(tube)
    for i, t0 in enumerate(T_TICKS):
        if t0 <= t < t0 + 0.6:
            K.ripple(c, p, t, t0, AMBER, n=2, every=0.1, life=0.5, r0=r * 1.1, r1=r * 2.2, width=6.0,
                     seed=680 + i, alpha=0.9)
        u = (t - t0) / T_TUBE
        if 0.0 <= u < 1.0:
            for kk in range(3):
                q, _ = K.poly_at(tube, L * clamp(ease("in", u) - 0.06 * kk))
                K.dot(c, q, (16.0 - 4.0 * kk), lerp(AMBER, PAPER, 0.6), seed=684 + kk, alpha=0.95 - 0.25 * kk)
        K.ripple(c, ear, t, t0 + T_TUBE, AMBER, n=3, every=0.1, life=0.6, r0=26.0, r1=150.0 - 30.0 * i, width=6.0,
                 seed=690 + i, alpha=0.9)


# ============================================================================ the dial, straight on
def _knob_hand(c, t, dial):
    """His fingers on the knob from the lower right, working it as it turns (they rock with it)."""
    on = ease("out3", _u(t, T_HAND_IN))
    if on <= 0.0:
        return
    k_, u = turn_of(t)
    rock = 14.0 * math.sin(math.radians(dial) * 3.0) if k_ is not None else 0.0
    a = math.radians(-12.0 + rock)
    grip = (DIAL_P[0] + KNOB_R * 0.98 * math.cos(a), DIAL_P[1] + KNOB_R * 0.98 * math.sin(a))
    back = 600.0 * (1.0 - on)
    wa = a + math.radians(38.0)
    wrist = (grip[0] + 900.0 * math.cos(wa) + back, grip[1] + 900.0 * math.sin(wa) + back * 0.6)
    grip = (grip[0] + back, grip[1] + back * 0.6)
    F.hand(c, "cracker", wrist, grip, 1.45, open_u=clamp(1.0 - on * 2.0))


def _loops(c, t):
    """An AMBER loop arrow round the dial for each turn, sweeping with it (anticlockwise for the
    left turn), gone after its gate."""
    for i, (t0, t1) in enumerate(TURNS):
        if not t0 <= t < GATES[i] + 0.45:
            continue
        u = _seek((t - t0) / (t1 - t0))
        fade = 1.0 - clamp((t - GATES[i] - 0.15) / 0.3)
        sweep = abs(DIAL_AT[i + 1] - DIAL_AT[i])
        c.save()
        if i == 1:                                     # left: mirrored, so it sweeps anticlockwise
            c.translate(DIAL_P[0], 0.0)
            c.scale(-1.0, 1.0)
            c.translate(-DIAL_P[0], 0.0)
        bass.loop_arrow(c, DIAL_P, LOOP_R, AMBER, width=26.0, u=u, rot=0.0, sweep=sweep, head=2.2, seed=700 + i,
                        alpha=0.95 * fade)
        c.restore()


def shot_dial(c, t):
    """The dial filling the frame on the door's steel in her light; his fingers; the turns."""
    dial = dial_angle(t)
    K.fill(c, FACE_D)
    K.pool(c, (DIAL_P[0], DIAL_P[1] + 40.0), 640.0, 760.0, PAPER, alpha=0.2, steps=4)
    for i, (rr, al) in enumerate(((620.0, 0.35), (760.0, 0.4), (900.0, 0.45))):
        bass.hole(c, (DIAL_P[0], DIAL_P[1] + 40.0), rr, INK, seed=710 + i, rect=(-20.0, -20.0, W + 20.0, H + 20.0),
                  n=96, alpha=al)
    Bk.dial_face(c, DIAL_P, DIAL_RF, dial, color=PAPER, face=INK, bezel=lerp(FACE_D, PAPER, 0.2), seed=1192,
                 numerals=True)
    _loops(c, t)
    top = (DIAL_P[0], DIAL_P[1] - DIAL_RF * 1.17)
    for i, t0 in enumerate(GATES):                      # a gate: the click's ripple off the index
        if t0 <= t < t0 + 0.8:
            K.ripple(c, top, t, t0, AMBER, n=2, every=0.12 - 0.02 * i, life=0.6 - 0.05 * i, r0=20.0,
                     r1=230.0 - 40.0 * i, width=7.0, seed=720 + i, alpha=0.95)
    if T_FENCE <= t < T_FENCE + 1.0:                    # CLUNK: the fence drops
        K.ripple(c, DIAL_P, t, T_FENCE, AMBER, n=3, every=0.1, life=0.7, r0=KNOB_R, r1=DIAL_RF * 1.6, width=9.0,
                 seed=730, alpha=0.9)
    _knob_hand(c, t, dial)


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, INK)
    with f.screen() as c:
        if t < T_ECU:
            shot_door(c, t, cam_a(t))
        elif t < T_DIAL:
            shot_ecu(c, t)
        elif t < T_DOOR:
            shot_dial(c, t)
        else:
            shot_door(c, t, cam_d(t))


# ============================================================================ cues
def _cam(t):
    return cam_a(t) if t < T_ECU else cam_d(t)


def _pan(t, p):
    return round(clamp((_cam(t).to_frame(p)[0] - 540.0) / 540.0, -1.0, 1.0) * 0.8, 3)


def cues(T):
    out = [Cue(0.0, "vault_tone", gain_db=-28, dur=T_SWING[0],
               desc="the dead hush at the vault door: close room tone, the beat's tick underneath"),
           Cue(T_KNEEL[0] + 0.2, "knee_down", gain_db=-27, pan=_pan(T_KNEEL[0], (CR_X[1], -40.0)),
               desc="the old man goes down on one knee on the steel floor: a soft knock and a cloth rustle"),
           Cue(T_PIECE[1], "steth_tock", gain_db=-20, pan=_pan(T_PIECE[1], PIECE_AT),
               dc="the stethoscope's chest-piece touches the steel door: a tiny metallic tock"),
           Cue(T_KNOB[1], "knob_tick", gain_db=-26, pan=_pan(T_KNOB[1], KNOB_GRIP),
               dc="fingers settle on the dial's knurled knob: a faint tick")]
    for i, (tb, xb) in enumerate(((0.5 * (T_STEP_IN[0] + T_STEP_IN[1]), 0.5 * (CR_X[0] + CR_X[1])),
                                  (T_STEP_IN[1], CR_X[1]))):
        out.append(Cue(round(tb, 3), "crew_step", gain_db=-24 - i, pan=_pan(tb, (xb, 0.0)),
                       dc="a soft step on a steel-plated floor"))
    # the stethoscope, close
    for i, t0 in enumerate(T_TICKS):
        out.append(Cue(t0, "steth_tick", gain_db=-22 - 2 * i, pan=-0.3,
                       desc="through the stethoscope: a soft tick inside the lock, close in his ear"))
    # the dial
    out.append(Cue(T_HAND_IN[0] + 0.1, "knob_tick", gain_db=-27, pan=0.2,
                   dc="fingers settle on the dial's knurled knob: a faint tick"))
    for (t0, t1), w in zip(TURNS, ("right", "left", "right")):
        out.append(Cue(t0, "dial_spin", gain_db=-20, pan=0.0, dur=round(t1 - t0, 3),
                       dc=f"the dial spins {w}: a fast run of fine ratchet ticks slowing to a creep (heard close "
                          f"through the stethoscope)"))
    for t0, pitch in zip(GATES, ("LOW", "MID", "HIGH")):
        out.append(Cue(t0, "gate_click", gain_db=-9, pan=0.0,
                       dc=f"a gate falls under the fence: a single crisp lock click, pitched {pitch} (intimate, in "
                          f"his ear)"))
    out.append(Cue(T_FENCE, "fence_clunk", gain_db=-5, pan=0.0, dc="CLUNK: the fence drops into the lined-up gates"))
    out.append(Cue(T_BOLT[0], "lock_bolt", gain_db=-13, pan=0.2, dc="the lock's bolt draws back: a short heavy metal slide"))
    # the door
    out.append(Cue(T_LET_GO[0] + 0.2, "piece_drop", gain_db=-26, pan=_pan(T_LET_GO[0] + 0.2, PIECE_AT),
                   dc="the chest-piece drops on its tube and taps his coat"))
    out.append(Cue(T_WHEEL[0], "wheel_ratchet", gain_db=-11, pan=_pan(T_WHEEL[0], Bk.WHEEL_C),
                   dur=round(T_WHEEL[1] - T_WHEEL[0], 3), dc="the great wheel turns: a slow heavy iron ratchet"))
    for kk in range(Bk.N_BOLTS):                    # the rolling run: each bolt as it comes out
        s = kk / float(Bk.N_BOLTS) * 0.72
        tb = T_WHEEL[0] + (s + 0.14) * (T_WHEEL[1] - T_WHEEL[0])
        a = math.radians(-90.0 + 15.0 + 30.0 * kk)
        p = (Bk.VDOOR_C[0] + Bk.VDOOR_R * math.cos(a), Bk.VDOOR_C[1] + Bk.VDOOR_R * math.sin(a))
        out.append(Cue(round(tb, 3), "bolt_clack", gain_db=-15, pan=_pan(tb, p),
                       dc="a heavy steel bolt withdraws from the door frame: one clack of a rolling run round the rim"))
    out.append(Cue(T_HEAVE[0], "heave_breath", gain_db=-20, pan=_pan(T_HEAVE[0], (CR_X[1], -150.0)),
                   dc="the old man heaves on the wheel: a strained breath"))
    out.append(Cue(T_SWING[0], "hinge_groan", gain_db=-9, pan=_pan(T_SWING[0], (Bk.HINGE_X, -110.0)),
                   dur=round(T_SWING[1] - T_SWING[0], 3),
                   dc="the vault door's great hinge groans as the door swings slowly open"))
    out.append(Cue(T_SWING[0] + 0.1, "string_swell", gain_db=-8, dur=round(T.duration - T_SWING[0] - 0.1, 3),
                   desc="a string swell (the score's strings, D minor rising): gold light floods out of the vault "
                        "over the three of them"))
    out.append(Cue(T_LIGHT_OFF, "flashlight_click", gain_db=-24, pan=_pan(T_LIGHT_OFF, (HER_X, -100.0)),
                   desc="her small light clicks off: the gold is light enough"))
    for i, tb in enumerate((0.5 * (T_BACK[0] + T_BACK[1]), T_BACK[1])):
        out.append(Cue(round(tb, 3), "step_back", gain_db=-26, pan=_pan(tb, (CR_X[2], 0.0)),
                       dc="a soft step back on the steel floor"))
    out.append(Cue(T_TURN_K[0], "coat_swish", gain_db=-24, pan=_pan(T_TURN_K[0], (KNIGHT_X, -100.0)),
                   desc="the Knight turns from the way they came to the light: a heavy coat's swish"))
    out.append(Cue(T_REST, "door_thud", gain_db=-14, pan=_pan(T_REST, (Bk.HINGE_X, -110.0)),
                   dc="the open door settles against its stop: a deep soft thud"))
    notes = {"knight": "his low C# (a cello, plucked)", "cracker": "a middle note (a viola, plucked)",
             "architect": "her high D (a violin, plucked)"}
    what = {"knight": "the gold", "cracker": "the gold", "architect": "the deposit boxes"}
    for who, t0 in T_LOOKS:
        out.append(Cue(t0, "look_note", gain_db=-16, pan=_pan(t0, {"knight": (KNIGHT_X, -150.0),
                                                                  "cracker": (CR_X[2], -150.0),
                                                                  "architect": (HER_X, -150.0)}[who]),
                       desc=f"a look goes in to {what[who]}: {notes[who]} over the swell"))
    return sorted(out, key=lambda q: q["t"])
