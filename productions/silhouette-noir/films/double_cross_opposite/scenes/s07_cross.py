"""s07 CROSS (94-114). The gold, the ruby, his look, the door shut on them (his POV), the red dial,
the second ring, the side door and the bell.

  The vault (0-1.5, 4.0-11.5), in the gold's light: bank.vault drawn mirrored, so the vault has the
    street section's layout (its door on the LEFT wall, the hall beyond it). By the door the Knight,
    crouched over two sacks, drops bars into the second while the Cracker, kneeling at the last of
    the gold, hands them over; beyond them, at the deposit wall, she opens one small box (0.35-1.5).
  The ruby (1.5-4.0): close on the open box: a ruby on a dark cushion, glowing RED; it glints. Her
    gloved hand comes in (2.0), finger and thumb close on it (2.5-2.7), lift it into the light
    (2.7-3.3), where it flares (3.0), and take it away (3.65-4.0).
  Back on her (4.0-4.6): she slips it into her coat pocket, her back to them. No one sees. The
    Cracker gets up off his knee and turns to the boxes; the camera eases over to the Knight.
  His look (6.0-9.0): he pulls the second sack shut and stands over the two; his RED look goes to
    the sacks (6.4), back over his shoulder to the open door (7.1), then to the two of them, their
    backs turned (7.6), and holds.
  He heaves up both sacks (9.2) and steps out through the door (9.0-11.5).
  His POV (11.5-14.0): the great door from the corridor, his gloved hands on its edge: he drives it
    shut with a lunge; through the narrowing gap the two turn round, too late (the Cracker starts
    back; she only stands, and is the last thing the slot shows); the gap narrows to a slot of gold
    and closes on the bar line (14.0): BOOM, black.
  The dial (14.25-15.0): s06's dial, close, in RED: his gloved hand on the knob; CLANK, the lock's
    bolt home; he spins it (a RED loop arrow); lets go.
  The section (15.0-17.0): the bank cut open, 12:04 on its clock. The single RED marker ring closes
    round the vault with the two tiny figures in it (15.3); his RED footstep dots run left across
    the hall to the side door (15.5-16.75), the sacks swinging.
  The alarm (17.0-20.0): the side door from the street bursts open (17.0, BANG, the frame shakes for
    one frame) and he charges out with the sacks and runs left for his car; over the door the bell
    rings RED, a ripple on every beat; the camera pushes in on the bell (17.7-20.0).
"""
import math
from functools import lru_cache

import cairo

from engine import bass
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import faces as F
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import street as St
from films.double_cross_opposite.scenes import s06_safe as S6

k = K.k
W, H = K.W, K.H
INK, PAPER, AMBER, RED, STEEL, DEEP, NIGHT = K.INK, K.PAPER, K.AMBER, K.RED, K.STEEL, K.DEEP, K.NIGHT

FILM_T0 = 94.0
FS = Bk.FIG_S                      # the cast in the vault (bank.py's scale)
FV = S6.FIG_V                      # ... and at the great door (s06's cheat)
RIM_W = 4.0

# ---------------------------------------------------------------------------- beats: the vault
T_SCOOPS = ((0.1, 0.8), (0.9, 1.6), (2.4, 3.1), (3.2, 3.9))   # a bar from the Cracker's hands into the sack
T_REACH = (0.35, 0.95)             # her hand to the little box's door ...
T_BOX = (0.95, 1.5)                # ... it opens
T_PUSH_HER = (0.85, 1.5)           # the camera eases in on her
T_RUBY = (1.5, 4.0)                # cut in close on the open box
T_GLINT = (1.5, 1.95)              # something RED glints in it
T_IN_HAND = (2.0, 2.5)             # her gloved hand comes in, open ...
T_PINCH = (2.5, 2.7)               # ... finger and thumb close on it ...
T_LIFT_R = (2.7, 3.3)              # ... she lifts it into the light ...
T_FLARE = 3.0                      # ... where it flares ...
T_AWAY = (3.65, 4.0)               # ... and her hand takes it away
T_POCKET = (4.0, 4.6)              # back on her: into her coat pocket, her back to them
T_CR_UP = (4.75, 5.2)              # the Cracker gets up off his knee ...
T_CR_TURN = (5.25, 5.45)           # ... and turns to the boxes (his back to the Knight)
T_TO_HIM = (5.0, 5.9)              # the camera eases over to the Knight
T_CINCH = (5.65, 6.05)             # he pulls the second sack's neck shut ...
T_RISE = (6.0, 6.4)                # ... and stands over the two
T_LOOK_SACKS = (6.4, 6.85)         # his RED look: the two full sacks (on, off) ...
T_HEAD_BACK = 7.0                  # ... his head snaps round over his shoulder ...
T_LOOK_DOOR = (7.1, 7.45)          # ... to the open door ...
T_HEAD_FWD = 7.5                   # ... and back ...
T_LOOK_TWO = (7.6, 8.75)           # ... to the two of them, their backs turned: held
T_PAN_TWO = (7.5, 8.1)             # (his look carries the camera over to them)
T_STOOP = (8.75, 9.15)             # he stoops to the sacks' necks ...
T_HEAVE = (9.2, 9.6)               # ... heaves them up (his grunt) ...
T_TURN_OUT = (9.6, 9.8)            # ... turns to the door (a cut-paper turn) ...
T_WALK = (9.8, 11.5)               # ... and steps out through it
T_POV = 11.5                       # cut: his POV through the closing door

# ---------------------------------------------------------------------------- beats: the door, the dial
T_HANDS_ON = (11.5, 11.62)         # his hands come onto the door's edge ...
T_SHOVE = (11.6, 13.1)             # ... he drives it (his grunt, held) ...
T_LET_GO = (13.1, 13.3)            # ... lets go; it swings on, faster and faster
T_SWING = (11.6, 14.0)             # the door's swing to the slam
T_TURN_IN = {"cracker": (12.6, 12.78), "architect": (12.95, 13.13)}   # the two inside turn: too late
T_LUNGE_IN = (12.8, 13.1)          # the Cracker starts back: a recoil, his hands coming up
T_SLAM = 14.0                      # BOOM on the bar line: black
T_BOLTS = (14.04, 14.18)           # in the black the rim's bolts shoot home
T_DIAL_IN = 14.25                  # the dial, close, in RED
T_KNOB_ON = (14.25, 14.33)         # his gloved hand onto the knob ...
T_CLANK = 14.4                     # ... a little turn: CLANK, the lock's bolt shoots home ...
T_SPIN = (14.45, 14.95)            # ... he spins it ...
T_KNOB_OFF = (14.6, 14.74)         # ... lets go and is gone

# ---------------------------------------------------------------------------- beats: the section, the alarm
T_SECTION = 15.0
T_RING = (15.3, 0.4)               # THE SECOND RED MARKER RING closes round the vault
T_RUN = (15.5, 16.75)              # his RED footstep dots: from the vault door across the hall to the side door
T_SIDE = 17.0                      # the side door bursts open: BANG, the bell
T_BELL_PUSH = (17.7, 20.0)         # the camera pushes in on the ringing bell
T_END = 20.0
RUN_STEPS = tuple(T_RUN[0] + 0.25 * i for i in range(6))   # his footstep dots, on the eighth notes

# ---------------------------------------------------------------------------- the same beats by the names the score reads
T_HAND = T_IN_HAND[0]
T_CLOSE = T_PINCH[0]
T_LIFT = T_LIFT_R
T_LOOK = 6.0                       # his look: his low note, a cello pedal (on the bar line) ...
T_INVERSION = 6.0                  # ... under THE THEME inverted, four bars, its last D on the BOOM
T_SHUT = (T_SHOVE[0], T_SLAM)
T_BOOM = T_SLAM
T_DIAL = T_SPIN                    # (the red dial spun)
T_DOTS = T_RUN
T_BANG = T_SIDE

# ---------------------------------------------------------------------------- the vault (mirrored set px: x' = VM - x)
VM = 1080.0                        # bank.vault is east-looking (its door at the right): drawn mirrored
DOOR_X = (VM - Bk.VDOOR_U[1], VM - Bk.VDOOR_U[0])        # the door's opening in the vault's west wall (380, 410)
ROOM_X = (VM - Bk.VAULT_IN[1], VM - Bk.VAULT_IN[0])      # the room (410, 620)
KNIGHT_AT = 410.0                  # the Knight, crouched by the door over the sacks, facing in (right)
SACK_A = (444.0, 0.0)              # the sack he fills (in front)
SACK_B = (428.0, 0.0)              # the full one beside it (behind)
CRACK_AT = 532.0                   # the Cracker, kneeling at the last of the gold, facing the Knight
CRACK_UP_DX = 2.0                  # ... standing (his pelvis moves a little as he gets up)
HER_AT = 570.0                     # her, at the deposit wall, facing it (right): her back to them
HAND_OVER = (478.0, -62.0)         # where a bar passes from the Cracker's hand to the Knight's
STACK = ((486.0, -9.0), (519.0, 0.0), (497.0, 0.0), (475.0, 0.0))   # the last four bars, in the order taken
BOX = (578.0, -138.0, 610.0, -104.0)                     # her box: column 0, row 2 of the deposit wall
BOX_C = ((BOX[0] + BOX[2]) / 2.0, (BOX[1] + BOX[3]) / 2.0)
RUBY_SEAT = (BOX_C[0] + 1.0, BOX[3] - 7.0)               # the ruby on its cushion in the box
POCKET = (HER_AT + 7.0, -64.0)     # her coat pocket
SACKS_AT = (438.0, -30.0)          # his looks: the two sacks ...
DOOR_AT = (338.0, -112.0)          # ... the great door, open outside ...
TWO_AT = (548.0, -112.0)           # ... the two of them
_, _, _, _, GOLD_C, GOLD_EDGE, GOLD_SHINE = Bk._palette(None)
CUSHION = lerp(RED, INK, 0.72)

CAM_V0 = Bk.Cam(505.0, -112.0, 4.6)        # the vault: the three of them, the door
CAM_HER = Bk.Cam(566.0, -112.0, 6.6)       # in on her at the box
CAM_HIM = Bk.Cam(432.0, -106.0, 4.6)       # over to him, the sacks, the door
CAM_TWO = Bk.Cam(498.0, -108.0, 4.7)       # his look carries the camera to the two of them
CAM_OUT = Bk.Cam(420.0, -110.0, 4.6)       # he goes: out through the door

# ---------------------------------------------------------------------------- the ruby, close
RUBY_CAM = (Bk.Cam(RUBY_SEAT[0], RUBY_SEAT[1] - 4.0, 15.0), Bk.Cam(RUBY_SEAT[0] - 1.0, RUBY_SEAT[1] - 6.0, 17.0))
RUBY_SET_R = 4.4                   # the ruby's radius on its cushion (set px)

# ---------------------------------------------------------------------------- his POV (north-looking set px, s06's door)
CAM_P0 = Bk.Cam(548.0, -104.0, 4.3)        # the door, its edge, the gap of gold
CAM_P1 = Bk.Cam(476.0, -108.0, 6.2)        # in on the narrowing gap
P_PUSH = (12.3, 13.9)              # the camera's glide in on the gap
IN_S = FV * 0.64                   # the two inside, beyond the door, toward the far wall
IN_FEET = -32.0
IN_X = {"architect": 466.0, "cracker": 528.0}     # she is the last thing the slot shows
LUNGE_D = -4.0                     # the Cracker's recoil (set px, along his facing)
HAND_L = 27.0                      # his hands on the door's edge: wrist to fingertip (set px)
DIAL_END = S6.DIAL_AT[-1] - 40.0   # the dial as s06 left it
SPIN_DEG = 400.0                   # his spin: a turn and a bit, left (fast, never a blur of numerals)
SWING_P = 2.4                      # the door's swing: faster and faster ...
G_SHUT = 0.29                      # ... to where, seen from here, its leaf meets the frame (25 deg): BOOM

# ---------------------------------------------------------------------------- the section (section px)
SEC_C0, SEC_Z0 = (842.0, 1032.0), 2.1      # the bank cut open, roof to cellar, side door to vault
SEC_C1, SEC_Z1 = (842.0, 1048.0), 2.16     # a slow push (the side door and the ring stay in)
CLOCK = (12, 19)                   # the bank's clock: a minute before s08 and s09's 12:20
RING_C = (St.PLACES["vault"][0] - 6.0, St.PLACES["vault"][1] + 8.0)
RING_R = (108.0, 112.0)
CR_SEC = St.VAULT_IN[0] + 18.0     # the Cracker in the dark at the door ...
HER_SEC = St.TRAP_C - 4.0          # ... and her, on the tile (as s08 has them)
RUN_FROM = (St.VAULT[0] - 12.0, St.FEET)   # his run: from outside the vault door ...
RUN_TO = (St.HALL[0] + 8.0, St.FEET)       # ... across the hall to the side door

# ---------------------------------------------------------------------------- the alarm (bank_front set px)
SD = St.SIDE_DOOR_F
SD_BELL = St.BELL_F
SD_CAM0 = Bk.Cam(96.0, -132.0, 4.7)        # the side door, the bell over it, the pavement, the car's tail
SD_CAM1 = Bk.Cam(SD_BELL[0], SD_BELL[1] + 6.0, 9.0)   # in on the ringing bell
SD_LIGHT = St.LOW_LAMP                     # the guard's lamp in the hall, seen through the open door
SHAKE = (16.0, -11.0)                      # the BANG's one-frame jolt (frame px)
SD_IN = 8.0                                # he is just inside the doorway as it bursts open (set px)


def motion_blur(t, T):
    return 1


def _seg(name, s0, s1, at, speed=1.0, **kw):
    return C.Seg(C.clip(name), s0, s1, at=at, speed=speed, **kw)


def _u(t, span):
    return clamp((t - span[0]) / (span[1] - span[0]))


def _lerp2(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))


def _arc2(a, b, u, h):
    """a to b along a little arc lifted h px."""
    p = _lerp2(a, b, u)
    return (p[0], p[1] - h * math.sin(math.pi * clamp(u)))


def _dry(who, st, pose, x, facing, s=FS):
    """A figure's joints (set px) without drawing it."""
    surf = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    return C.draw(cairo.Context(surf), who, st, pose, x, 0.0, s, facing, rim=False)


def _reach(who, st, pose, x, facing, side, target, s=FS, up=False):
    """Set an arm (as angles) so the hand lands on target (set px), the elbow bent down (or up)."""
    fg = C.fig(who)
    sh = _dry(who, st, pose, x, facing, s)["shoulder_" + side]
    l1, l2 = fg.upper * s, (fg.fore + 0.55 * fg.hand_r) * s
    dx, dy = target[0] - sh[0], target[1] - sh[1]
    d = clamp(math.hypot(dx, dy), abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    th = math.atan2(dy, dx)
    al = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2.0 * l1 * d), -1.0, 1.0))
    els = [(sh[0] + l1 * math.cos(th + sg * al), sh[1] + l1 * math.sin(th + sg * al)) for sg in (1.0, -1.0)]
    el = min(els, key=lambda q: q[1]) if up else max(els, key=lambda q: q[1])
    wr = (sh[0] + d * math.cos(th), sh[1] + d * math.sin(th))
    a1 = math.degrees(math.atan2(facing * (el[0] - sh[0]), el[1] - sh[1]))
    a2 = math.degrees(math.atan2(facing * (wr[0] - el[0]), wr[1] - el[1]))
    pose.arms[side] = ("ang", a1 - pose.lean, a2 - a1)


def _paper(u):
    """sx of a cut-paper turn u 0..1: 1, squashed edge-on, -1 (mirrored) past the middle."""
    return math.cos(math.pi * ease("inout", clamp(u)))


def _fig(c, who, st, pose, x, facing, s, rim_w, sx=1.0, back=False, bg=INK, rim=None, light=(-0.6, -0.8)):
    """Draw a figure (its state built facing `facing`) paper-turned by sx about its pelvis (in set px).
    back: its head turned round over its shoulder (the head piece flipped about its middle).
    Returns its joints (set px, as drawn) and where its eye looks from."""
    xp = x + st["pelvis"][0] * s
    sxx = sx if abs(sx) >= 0.03 else math.copysign(0.03, sx)
    lt = (light[0] * math.copysign(1.0, sxx), light[1])
    c.save()
    c.translate(xp, 0.0)
    c.scale(sxx, 1.0)
    c.translate(-xp, 0.0)
    if not back:
        j = C.draw(c, who, st, pose, x, 0.0, s, facing, bg=bg, rim=rim, rim_w=rim_w, light=lt)
        eye = (j["head"][0] + facing * 3.0 * s / FS, j["head"][1] - 1.0 * s / FS)
    else:
        jd = _dry(who, st, pose, x, facing, s)
        hx, hy = jd["head"]
        yn = lerp(hy, jd["shoulder_near"][1], 0.62)
        c.save()
        c.rectangle(-1e4, yn, 2e4, 2e4)
        c.clip()
        j = C.draw(c, who, st, pose, x, 0.0, s, facing, bg=bg, rim=rim, rim_w=rim_w, light=lt)
        c.restore()
        c.save()
        c.rectangle(-1e4, -2e4, 2e4, 2e4 + yn)
        c.clip()
        c.translate(hx, 0.0)
        c.scale(-1.0, 1.0)
        c.translate(-hx, 0.0)
        C.draw(c, who, st, pose, x, 0.0, s, facing, bg=bg, rim=rim, rim_w=rim_w, light=(-lt[0], lt[1]))
        c.restore()
        eye = (hx - facing * 3.0 * s / FS, hy - 1.0 * s / FS)
    pts = dict(j, eye=eye)
    dev = {kk: c.user_to_device(*v) for kk, v in pts.items()}
    c.restore()
    out = {kk: c.device_to_user(*v) for kk, v in dev.items()}
    return out


# ============================================================================ the vault: performances
@lru_cache(maxsize=None)
def perfs():
    d = {}
    d["knight"] = C.perf("knight", [
        _seg("26_10", 1.1, 1.2, 0.0, 0.02, travel=0.0),                                   # crouched at the sacks
        _seg("26_10", 3.2, 3.6, T_RISE[0], 0.4 / (T_RISE[1] - T_RISE[0]), travel=0.0, blend=0.25),   # up over them
        _seg("17_08", 5.7, 6.0, T_RISE[1] + 0.05, 0.08, travel=0.0, blend=0.3),          # standing
        _seg("26_10", 3.0, 3.06, T_STOOP[0], 0.06 / (T_STOOP[1] - T_STOOP[0]), travel=0.0,
             blend=T_STOOP[1] - T_STOOP[0]),                                              # down to the necks
        _seg("26_10", 3.06, 3.6, T_HEAVE[0], 0.54 / (T_HEAVE[1] - T_HEAVE[0]), travel=0.0, blend=0.08),   # the heave
        _seg("17_08", 5.7, 6.0, T_HEAVE[1], 0.1, travel=0.0, blend=0.25)], facing=1)
    d["knight_out"] = C.perf("knight", [
        _seg("17_08", 5.7, 6.0, 0.0, 0.1, travel=0.0),
        _seg("17_08", 1.5, 4.0, T_WALK[0], 0.95, blend=0.3)], facing=-1)
    d["architect"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 0.0, 0.1, travel=0.0, lean=-2.0)], facing=1)
    d["cracker"] = C.perf("cracker", [
        _seg("23_03", 3.7, 4.0, 0.0, 0.07, travel=0.0),
        _seg("104_02", 5.7, 7.3, T_CR_UP[0], 0.12, travel=0.0, lean=8.0, blend=T_CR_UP[1] - T_CR_UP[0])], facing=-1)
    return d


def _scoop(t):
    """(phase, k) of the scoop at t: phase 0..1 through scoop k, or (None, None)."""
    for kk, (t0, t1) in enumerate(T_SCOOPS):
        if t0 <= t < t1:
            return (t - t0) / (t1 - t0), kk
    return None, None


def bars_left(t):
    """The bars still on the stack at t (indices into STACK)."""
    return [i for i, (t0, t1) in enumerate(T_SCOOPS) if t < t0 + 0.22 * (t1 - t0)]


def sack_fill(t):
    """The second sack fills a bar at a time (nearly full when we come in)."""
    n = sum(1 for (t0, t1) in T_SCOOPS if t >= t0 + 0.64 * (t1 - t0))
    return 0.62 + 0.08 * n + 0.06 * ease("inout", _u(t, T_CINCH))


def _bar_pos(i):
    x, y = STACK[i]
    return (x, y - 4.5)


def cracker_vault(t, tt):
    """(st, pose, x, sx, bar): kneeling, he lifts each bar off the stack and hands it over; up off his
    knee; turns to the boxes."""
    st, pose = perfs()["cracker"](tt)
    x = CRACK_AT + CRACK_UP_DX * k(tt, T_CR_UP[0], T_CR_UP[1] - T_CR_UP[0])
    bar = None
    if tt < T_CR_UP[0]:
        j = _dry("cracker", st, pose, x, -1)
        rest = (j["hand_near"][0] + 2.0, j["hand_near"][1] + 8.0)
        ph, kk = _scoop(tt)
        if ph is not None:
            src = _bar_pos(kk)
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
            dip = math.sin(math.pi * clamp(ph / 0.5))
            pose.lean += 5.0 * dip
            pose.head -= 4.0 * dip
            _reach("cracker", st, pose, x, -1, "near", tgt)
        pose.arms["far"] = ("ang", 18.0, 40.0)
    sx = _paper(_u(tt, T_CR_TURN))
    return st, pose, x, sx, bar


def knight_vault(t, tt):
    """(st, pose, x, bar, holding): crouched at the sacks, taking each bar and dropping it in; he pulls
    the second sack shut and stands; stoops to the necks and heaves the two up."""
    st, pose = perfs()["knight"](tt)
    x = KNIGHT_AT
    mouth = (SACK_A[0] + 1.0, -40.0)
    bar = None
    holding = tt >= T_HEAVE[0]
    if tt < T_RISE[0] + 0.1:
        ph, kk = _scoop(tt)
        far = (mouth[0] + 6.0, mouth[1] - 2.0)
        tgt = mouth
        if ph is not None:
            if ph < 0.4:
                tgt = _lerp2(mouth, HAND_OVER, ease("inout", ph / 0.4))
            elif ph < 0.52:
                tgt = HAND_OVER
            elif ph < 0.64:
                tgt = _arc2(HAND_OVER, mouth, ease("inout", (ph - 0.52) / 0.12), 8.0)
                bar = tgt
            pose.lean += 4.0 * math.sin(math.pi * clamp(ph / 0.6))
        cu = ease("inout", _u(tt, T_CINCH))
        if cu > 0.0:                                   # both hands up the sack's neck: pulled shut
            tgt = (mouth[0] - 2.0, mouth[1] - 9.0 * cu)
            far = (mouth[0] + 3.0, mouth[1] - 11.0 * cu)
        let = ease("inout", _u(tt, (T_RISE[0] - 0.05, T_RISE[0] + 0.1)))
        if let < 1.0:
            j = _dry("knight", st, pose, x, 1)
            n0, f0 = pose.arms["near"], pose.arms["far"]
            _reach("knight", st, pose, x, 1, "near", tgt)
            _reach("knight", st, pose, x, 1, "far", far)
            if let > 0.0:
                for side, nat in (("near", n0), ("far", f0)):
                    a = pose.arms[side]
                    pose.arms[side] = ("ang", lerp(a[1], nat[1], let), lerp(a[2], nat[2], let))
    elif tt < T_STOOP[0]:
        bow = k(tt, T_LOOK_SACKS[0] - 0.15, 0.3) * (1.0 - k(tt, T_LOOK_SACKS[1], 0.25))
        pose.head -= 16.0 * bow                        # his face down to the sacks
        pose.lean += 4.0 * bow
    else:
        # the necks: hands down onto them, then up with them
        necks = ((SACK_A[0] + 1.0, -44.0), (SACK_B[0] + 1.0, -44.0))
        if not holding:
            g = ease("inout", _u(tt, (T_STOOP[0] + 0.1, T_STOOP[1])))
            j = _dry("knight", st, pose, x, 1)
            for side, nk in (("near", necks[0]), ("far", necks[1])):
                _reach("knight", st, pose, x, 1, side, _lerp2(j["hand_" + side], nk, g))
        else:
            j = _dry("knight", st, pose, x, 1)
            px = x + st["pelvis"][0] * FS
            lift = ease("inout", _u(tt, T_HEAVE))
            up_n, up_f = (px + 12.0, -60.0), (px - 9.0, -62.0)
            _reach("knight", st, pose, x, 1, "near", _lerp2(necks[0], up_n, lift))
            _reach("knight", st, pose, x, 1, "far", _lerp2(necks[1], up_f, lift))
            pose.lean += 5.0 * lift
            pose.hold["near"] = Bk.hold_sack(1.0, seed=41, floor=0.0)
            pose.hold["far"] = Bk.hold_sack(1.0, seed=42, floor=0.0)
    return st, pose, x, bar, holding


@lru_cache(maxsize=1)
def _out_x():
    """The walk-out perf's x so its pelvis starts where the heave left his."""
    st, _ = perfs()["knight"](T_TURN_OUT[0])
    st2, _ = perfs()["knight_out"](T_TURN_OUT[0])
    return KNIGHT_AT + st["pelvis"][0] * FS - st2["pelvis"][0] * FS


def knight_out(tt):
    """(st, pose, x): turned to the door, the two sacks swinging at his sides, out through it."""
    st, pose = perfs()["knight_out"](tt)
    x = _out_x()
    px = x + st["pelvis"][0] * FS
    walk = clamp((tt - T_WALK[0]) / 0.3)
    sw = 3.0 * math.sin(2.0 * math.pi * (tt - T_WALK[0]) * 1.05) * walk
    _reach("knight", st, pose, x, -1, "near", (px - 12.0 - sw, -60.0))
    _reach("knight", st, pose, x, -1, "far", (px + 9.0 + sw, -62.0))
    pose.hold["near"] = Bk.hold_sack(1.0, seed=41, floor=0.0)
    pose.hold["far"] = Bk.hold_sack(1.0, seed=42, floor=0.0)
    pose.lean += 5.0 + 4.0 * walk                      # heavy: he leans into the walk
    return st, pose, x


def her_vault(t, tt):
    """(st, pose, ruby): at the deposit wall, the little box, the ruby into her pocket."""
    st, pose = perfs()["architect"](tt)
    x = HER_AT
    j = _dry("architect", st, pose, x, 1)
    rest = j["hand_near"]
    x0, y0, x1, y1 = BOX
    edge = (x0 + 2.0, (y0 + y1) / 2.0)
    ruby = None
    if tt < T_REACH[0]:
        tgt = None
    elif tt < T_BOX[0]:
        tgt = _lerp2(rest, edge, ease("inout", _u(tt, T_REACH)))
    elif tt < T_POCKET[0]:
        g = box_open(tt)
        fx = BOX[2] - 1.5 - (BOX[2] - BOX[0] - 3.0) * math.cos(math.radians(100.0 * g))
        tgt = (min(fx, x1 - 9.0), edge[1])
        if tt >= T_AWAY[0]:                            # (in the close-up she took it)
            tgt = _lerp2(tgt, RUBY_SEAT, ease("inout", _u(tt, T_AWAY)))
    elif tt < T_POCKET[1]:
        tgt = _arc2(RUBY_SEAT, POCKET, ease("inout", _u(tt, T_POCKET)), -6.0)
        if tt < T_POCKET[1] - 0.08:
            ruby = tgt
    else:
        tgt = _lerp2(POCKET, rest, ease("inout", clamp((tt - T_POCKET[1]) / 0.45)))
    if tgt is not None:
        _reach("architect", st, pose, x, 1, "near", tgt)
    reach = k(tt, T_REACH[0], 0.4) * (1.0 - k(tt, T_POCKET[0], 0.4))
    pose.lean += 6.0 * reach
    pose.head += 4.0 * reach - 5.0 * k(tt, T_POCKET[0], 0.2) * (1.0 - k(tt, T_POCKET[1], 0.3))
    return st, pose, ruby


def box_open(t):
    return ease("inout", _u(t, T_BOX))


def glint_at(t):
    """The ruby's glint in the open box: up, held, gone once she has it."""
    return ease("out", _u(t, T_GLINT)) * (1.0 - clamp((t - T_PINCH[1]) / 0.08))


def cam_vault(t):
    if t < T_RUBY[0]:
        return Bk.Cam.toward(CAM_V0, CAM_HER, ease("inout", _u(t, T_PUSH_HER)) * 0.55, BOX_C)
    if t < T_TO_HIM[0]:
        return CAM_HER
    if t < T_PAN_TWO[0]:
        return Bk.Cam.lerp(CAM_HER, CAM_HIM, ease("inout", _u(t, T_TO_HIM)))
    if t < T_HEAVE[0]:
        return Bk.Cam.lerp(CAM_HIM, CAM_TWO, ease("inout", _u(t, T_PAN_TWO)))
    return Bk.Cam.lerp(CAM_TWO, CAM_OUT, ease("inout", clamp((t - T_HEAVE[0]) / 1.6)))


# ============================================================================ the vault: drawing
def vault_m(c, cam, t, **kw):
    """bank.vault mirrored (door on the left), seen through `cam` (in the mirrored set px)."""
    c.save()
    c.translate(W, 0.0)
    c.scale(-1.0, 1.0)
    Bk.vault(c, Bk.Cam(VM - cam.x, cam.y, cam.zoom), t, **kw)
    c.restore()


def _box(c, t, g, glint, ruby_in):
    """Her box in the deposit wall (set px): its little door hinged on the right; inside, the ruby on
    a dark cushion."""
    x0, y0, x1, y1 = BOX
    if g <= 0.0:
        return
    Bk.rect(c, (x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5), INK, amp=0.0)
    Bk.ellipse(c, (RUBY_SEAT[0], RUBY_SEAT[1] + 2.4), 7.5, 2.6, CUSHION, n=24)
    if ruby_in:
        K.dot(c, RUBY_SEAT, 2.2, RED, seed=711)
        if glint > 0.0:
            K.twinkle(c, (RUBY_SEAT[0] + 0.6, RUBY_SEAT[1] - 0.6), 9.0, lerp(RED, PAPER, 0.35), u=glint,
                      rot=12.0 + 30.0 * K.twos(t), alpha=0.95)
    wdt = (x1 - x0 - 3.0) * math.cos(math.radians(100.0 * g))
    hx = x1 - 1.5
    pts = [(hx, y0 + 1.5), (hx - wdt, y0 + 1.5 - 3.0 * g), (hx - wdt, y1 - 1.5 + 3.0 * g), (hx, y1 - 1.5)]
    if abs(wdt) > 0.5:
        bass.fill_polys(c, [bass.orient(pts, True)], lerp(Bk.GOLD_BOX, PAPER, 0.15) if wdt < 0 else Bk.GOLD_BOX)


def _draw_bars(c, idx):
    for i in idx:
        Bk.bar(c, STACK[i], 1.0, color=GOLD_C, edge=GOLD_EDGE, shine=GOLD_SHINE)


def _bar_in_hand(c, p, ang=0.0, s=0.9):
    Bk.bar(c, (p[0], p[1] + 4.5 * s / 0.9), s, angle=ang, color=GOLD_C, edge=INK, shine=GOLD_SHINE)


def _ruby_in_hand(c, p, t, size=1.0):
    K.dot(c, p, 2.2 * size, RED, seed=712)
    K.twinkle(c, p, 7.0 * size, RED, u=1.0, rot=15.0 + 30.0 * K.twos(t), alpha=0.9)


def shot_vault(c, t):
    tt = K.twos(t)
    cam = cam_vault(t)
    vault_m(c, cam, t, light=None, door=0.0, box=0.0, glint=0.0, gold=0.0)
    rim_w = RIM_W / cam.zoom
    bg = Bk.GOLD_BOX
    marks = {}
    with cam.on(c):
        _box(c, t, box_open(t), glint_at(t), t < T_PINCH[1])
        # beyond the gold: her, at the deposit wall
        st, pose, ruby = her_vault(t, tt)
        C.draw(c, "architect", st, pose, HER_AT, 0.0, FS, 1, bg=bg, rim_w=rim_w)
        if ruby is not None:
            _ruby_in_hand(c, ruby, t, 0.8)
        # the full sack, then the Cracker
        if tt < T_HEAVE[0]:
            Bk.sack(c, SACK_B, 1.0, 1.0, INK, rim=RED, seed=42)
        cst, cpose, cx, csx, cbar = cracker_vault(t, tt)
        jc = _fig(c, "cracker", cst, cpose, cx, -1, FS, rim_w, sx=csx, bg=bg)
        # the Knight
        if tt < T_TURN_OUT[0]:
            kst, kpose, kx, kbar, holding = knight_vault(t, tt)
            back = T_HEAD_BACK <= tt < T_HEAD_FWD
            jk = _fig(c, "knight", kst, kpose, kx, 1, FS, rim_w, back=back, bg=bg)
            marks["eye"] = jk["eye"]
            if kbar is not None:
                _bar_in_hand(c, kbar, -10.0)
        else:
            kst, kpose, kx = knight_out(tt)
            sx = -_paper(_u(tt, T_TURN_OUT))
            _fig(c, "knight", kst, kpose, kx, -1, FS, rim_w, sx=sx, bg=bg)
        if tt < T_HEAVE[0]:
            Bk.sack(c, SACK_A, sack_fill(tt), 1.0, INK, rim=RED, seed=41)
        _draw_bars(c, bars_left(tt))
        if cbar is not None:
            _bar_in_hand(c, cbar, 8.0)
    # his looks: the sacks, the door (over his shoulder), the two of them
    eye = marks.get("eye")
    if eye is not None:
        fe = cam.to_frame(eye)
        if T_LOOK_SACKS[0] <= t < T_HEAD_BACK:
            K.sight_line(c, fe, cam.to_frame(SACKS_AT), t, T_LOOK_SACKS[0], RED, dur=0.3, off=T_LOOK_SACKS[1],
                         off_dur=0.12, march=24.0, r=6.5, gap=23.0, head=26.0, seed=71)
        elif T_LOOK_DOOR[0] <= t < T_HEAD_FWD:
            K.sight_line(c, fe, cam.to_frame(DOOR_AT), t, T_LOOK_DOOR[0], RED, dur=0.3, off=T_LOOK_DOOR[1],
                         off_dur=0.05, march=26.0, r=6.5, gap=23.0, head=26.0, seed=72)
        elif T_LOOK_TWO[0] <= t < T_STOOP[0] + 0.2:
            K.sight_line(c, fe, cam.to_frame(TWO_AT), t, T_LOOK_TWO[0], RED, dur=0.4, off=T_LOOK_TWO[1],
                         off_dur=0.2, march=26.0, r=7.0, gap=24.0, head=28.0, seed=73)


# ============================================================================ the ruby, close (1.5-4.0)
def ruby_cam(t):
    return Bk.Cam.lerp(RUBY_CAM[0], RUBY_CAM[1], ease("inout", _u(t, T_RUBY)))


def ruby_close(t, cam):
    """(centre, radius) of the ruby in the close-up (frame px): on its cushion; lifted out toward us
    in her fingers, into the light; then away to the lower left with her hand."""
    seat = cam.to_frame(RUBY_SEAT)
    lift = ease("inout", _u(t, T_LIFT_R))
    away = ease("in", _u(t, T_AWAY))
    p = (seat[0] - 60.0 * lift - 620.0 * away, seat[1] - 240.0 * lift + 900.0 * away)
    return p, RUBY_SET_R * cam.zoom * (1.0 + 0.4 * lift + 0.25 * away)


def _gem(c, p, r, rot=0.0, flash=0.0):
    """The ruby, its table to us: a cut octagon, the crown's facets lit from the top left, the table
    in the middle, a highlight."""
    n = 8
    outer = [(p[0] + r * math.cos(rot + 2.0 * math.pi * i / n), p[1] + r * math.sin(rot + 2.0 * math.pi * i / n))
             for i in range(n)]
    inner = [(p[0] + 0.56 * (q[0] - p[0]), p[1] + 0.56 * (q[1] - p[1])) for q in outer]
    bass.fill_polys(c, [bass.orient([(p[0] + 1.08 * (q[0] - p[0]), p[1] + 1.08 * (q[1] - p[1])) for q in outer], True)],
                    INK)
    light = math.radians(-135.0)
    for i in range(n):
        j = (i + 1) % n
        mid = rot + 2.0 * math.pi * (i + 0.5) / n
        b = 0.5 + 0.5 * math.cos(mid - light)
        col = lerp(lerp(RED, INK, 0.55), lerp(RED, PAPER, 0.4), b)
        bass.fill_polys(c, [bass.orient([outer[i], outer[j], inner[j], inner[i]], True)], col)
    bass.fill_polys(c, [bass.orient(inner, True)], lerp(RED, PAPER, 0.1 + 0.55 * flash))
    hl = (p[0] - 0.3 * r, p[1] - 0.26 * r)
    bass.fill_polys(c, [bass.orient([(hl[0] - 0.16 * r, hl[1] + 0.04 * r), (hl[0] + 0.02 * r, hl[1] - 0.14 * r),
                                     (hl[0] + 0.1 * r, hl[1] - 0.06 * r), (hl[0] - 0.08 * r, hl[1] + 0.12 * r)], True)],
                    PAPER, 0.9)
    for q in outer:                                      # the facets' cut lines
        bass.line_band(c, [q, (p[0] + 0.56 * (q[0] - p[0]), p[1] + 0.56 * (q[1] - p[1]))], lerp(RED, INK, 0.6),
                       width=max(1.0, 0.035 * r), seed=713)


def _ruby_hand(c, t, p, r):
    """Her gloved hand: in from the lower left, open; finger and thumb close on the ruby's crown; up
    into the light with it, then away."""
    come = ease("out3", _u(t, T_IN_HAND))
    if come <= 0.0:
        return
    off = 1.0 - come
    grip = (p[0] + 0.1 * r - 560.0 * off, p[1] - 0.72 * r + 640.0 * off)
    wrist = (grip[0] - 760.0, grip[1] + 700.0)
    s = 1.9 * (1.0 + 0.3 * ease("inout", _u(t, T_LIFT_R)))
    F.hand(c, "architect", wrist, grip, s, open_u=1.0 - 0.85 * ease("inout", _u(t, T_PINCH)))


def shot_ruby(c, t):
    """Close on the open box in the deposit wall: the ruby on its cushion, glowing; it glints; her
    gloved fingers take it up into the light, where it flares, and away."""
    cam = ruby_cam(t)
    vault_m(c, cam, t, light=None, door=0.0, box=0.0, glint=0.0, gold=0.0)
    seat = cam.to_frame(RUBY_SEAT)
    r0 = RUBY_SET_R * cam.zoom
    with cam.on(c):
        _box(c, t, 1.0, 0.0, False)
    Bk.ellipse(c, (seat[0], seat[1] + 0.9 * r0), 2.0 * r0, 0.55 * r0, CUSHION, n=48)
    p, r = ruby_close(t, cam)
    K.pool(c, p, 3.4 * r, 3.4 * r, RED, 0.12, steps=4)
    flash = math.sin(math.pi * clamp((t - T_FLARE) / 0.4)) if t >= T_FLARE else 0.0
    _gem(c, p, r, math.radians(22.5 + 25.0 * ease("inout", _u(t, (T_LIFT_R[0], T_AWAY[0])))), flash)
    g = math.sin(math.pi * _u(t, (T_GLINT[0] + 0.05, T_GLINT[1] + 0.1)))
    if g > 0.0:                                          # it glints in the box
        K.twinkle(c, (p[0] + 0.3 * r, p[1] - 0.3 * r), 2.2 * r * g, lerp(RED, PAPER, 0.45), rot=15.0 + 40.0 * g)
    f = (t - T_FLARE) / 0.45
    if 0.0 < f < 1.0:                                    # up in the light it flares
        K.twinkle(c, (p[0] - 0.25 * r, p[1] - 0.3 * r), 3.4 * r * math.sin(math.pi * f), PAPER, rot=20.0 * f)
    _ruby_hand(c, t, p, r)


# ============================================================================ his POV: the door shut on them (11.5-14.0)
def door_open_at(t):
    """The great door (1 open, as s06 left it .. 0 shut): it swings faster and faster; the gap closes
    (its leaf meets the frame as we see it) on the slam, and we cut to black."""
    return G_SHUT + (1.0 - G_SHUT) * (1.0 - _u(t, T_SWING) ** SWING_P)


def leaf_left(g):
    """The swung leaf's nearest (left) edge, set px: the right side of the gap."""
    th = math.radians(88.0 * g)
    cs, sn = math.cos(th), math.sin(th)
    fc = Bk.HINGE_X + (Bk.VDOOR_C[0] - Bk.HINGE_X) * cs
    return fc - Bk.DOOR_T * sn - Bk.VDOOR_R * cs


def cam_pov(t):
    lunge = Bk.Cam(CAM_P0.x - 6.0, CAM_P0.y + 2.0, CAM_P0.zoom * 1.06)
    a = Bk.Cam.lerp(CAM_P0, lunge, ease("outback", _u(t, (T_SHOVE[0], T_SHOVE[0] + 0.3))))
    return Bk.Cam.toward(a, CAM_P1, ease("inout", _u(t, P_PUSH)), (Bk.VDOOR_C[0] - Bk.VDOOR_R + 20.0, -110.0))


@lru_cache(maxsize=None)
def in_perfs():
    d = {}
    d["architect"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 9.0, 0.1, travel=0.0, lean=-2.0)], facing=1)
    d["cracker"] = C.perf("cracker", [_seg("104_02", 5.7, 7.3, 9.0, 0.12, travel=0.0, lean=8.0)], facing=1)
    d["cracker_b"] = C.perf("cracker", [_seg("104_02", 5.7, 7.3, 9.0, 0.12, travel=0.0, lean=8.0)], facing=-1)
    return d


def _stepped(st, u, dist, fc, lift=18.0):
    """Two half steps, the far foot then the near, carrying a standing pose `dist` figure units
    along facing fc, u 0..1."""
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


def inside_rows(t, tt):
    """[(who, st, pose, x, facing, sx)]: the two inside, beyond the door, their backs to it; they turn
    round, too late: the Cracker starts back, hands coming up; she only stands."""
    rows = []
    for who in ("architect", "cracker"):
        a, b = T_TURN_IN[who]
        e = ease("inout", _u(tt, (a, b)))
        x = IN_X[who]
        if who == "cracker" and e >= 0.5:
            st, pose = in_perfs()["cracker_b"](tt)
            st = _stepped(st, _u(tt, T_LUNGE_IN), LUNGE_D / IN_S, -1, lift=8.0)
            up = k(tt, T_LUNGE_IN[0] - 0.05, 0.16, "outback")
            pose.lean -= 9.0 * up
            pose.head -= 6.0 * up
            pose.arms["near"] = ("ang", 4.0 + 12.0 * up, 12.0 + 44.0 * up)
            pose.arms["far"] = ("ang", 2.0 + 8.0 * up, 12.0 + 38.0 * up)
            rows.append((who, st, pose, x, -1, -math.cos(math.pi * e)))
            continue
        st, pose = in_perfs()[who](tt)
        if who == "architect":
            pose.head += 4.0 * k(tt, b, 0.3)
        rows.append((who, st, pose, x, 1, math.cos(math.pi * e)))
    return rows


def _inside(c, t, tt):
    """Inside the vault through the gap: its far wall in the gold's light, the floor, the two of them
    (the gold is in his sacks)."""
    Bk.vault_through(c, t, light="gold", gold=-1.0)
    c.save()
    c.translate(0.0, IN_FEET)
    for who, st, pose, x, fc, sx in inside_rows(t, tt):
        _fig(c, who, st, pose, x, fc, IN_S, 1.6, sx=sx, bg=Bk.GOLD_BOX, rim=None, light=(-0.6, -0.8))
    c.restore()


# a gloved hand seen from the back, flat on the steel, fingers up (hand units: the wrist at (0, 0), the
# middle fingertip at (0, -190)); the thumb on the -x side (his right hand; mirrored for his left)
_GB_PALM = [(-34.0, 4.0), (-44.0, -50.0), (-47.0, -94.0), (-26.0, -106.0), (0.0, -108.0), (24.0, -105.0),
            (45.0, -96.0), (42.0, -48.0), (34.0, 4.0)]
_GB_FINGERS = (((-34.0, -96.0), -98.0, 76.0, 21.0), ((-11.0, -102.0), -92.0, 88.0, 22.0),
               ((12.0, -101.0), -86.0, 82.0, 21.0), ((33.0, -93.0), -79.0, 64.0, 19.0))
_GB_THUMB = ((-38.0, -34.0), -142.0, 70.0, 25.0)


def _capsule(b, ang, L, w, n=8):
    """A rounded finger from base b, `ang` degrees, length L, width w."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    r = w / 2.0
    e = (b[0] + ux * (L - r), b[1] + uy * (L - r))
    pts = [(b[0] - uy * r, b[1] + ux * r)]
    for i in range(n + 1):
        th = a + math.pi / 2.0 - math.pi * i / n
        pts.append((e[0] + r * math.cos(th), e[1] + r * math.sin(th)))
    pts.append((b[0] + uy * r, b[1] - ux * r))
    return pts


def _glove_back(c, wrist, ang, s, arm_to, right=True, rim_off=(-4.0, -2.0)):
    """His gloved hand flat on the door, seen from behind: fingers toward `ang` (deg, frame), s px per
    hand unit, the forearm running from the wrist off the frame to `arm_to`; RED rim on the side
    toward the gold's light (left)."""
    hand = [bass.orient(_GB_PALM, True)]
    for b0, a0, L, w in _GB_FINGERS + (_GB_THUMB,):
        hand.append(bass.orient(_capsule(b0, a0, L, w), True))
    dx, dy = arm_to[0] - wrist[0], arm_to[1] - wrist[1]
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d, dx / d
    w0, w1 = 50.0 * s, 210.0 * s
    back = (wrist[0] - dx / d * 10.0 * s, wrist[1] - dy / d * 10.0 * s)
    arm = bass.orient([(back[0] + nx * w0, back[1] + ny * w0), (arm_to[0] + nx * w1, arm_to[1] + ny * w1),
                       (arm_to[0] - nx * w1, arm_to[1] - ny * w1), (back[0] - nx * w0, back[1] - ny * w0)], True)
    for col, off in ((RED, rim_off), (INK, (0.0, 0.0))):
        bass.fill_polys(c, [bass.orient([(x + off[0], y + off[1]) for x, y in arm.copy()], True)], col)
        c.save()
        c.translate(wrist[0] + off[0], wrist[1] + off[1])
        c.rotate(math.radians(ang + 90.0))
        c.scale(s if right else -s, s)
        bass.fill_polys(c, hand, col)
        c.restore()


def _push_hands(c, t, cam, g):
    """His gloved hands flat on the door's free edge (it faces him, the door swung wide), his arms
    from the lower right: the shove; then they let go and drop away."""
    on = ease("out3", _u(t, T_HANDS_ON))
    off = ease("in", _u(t, T_LET_GO))
    if on <= 0.0 or off >= 1.0:
        return
    th = math.radians(88.0 * g)
    mid = leaf_left(g) + 0.5 * Bk.DOOR_T * math.sin(th)        # the middle of the edge's face
    s = HAND_L / 190.0 * cam.zoom
    back = (1.0 - on) * 620.0 + off * 760.0
    rows = ((-128.0, -96.0, (W + 60.0, H + 330.0), False, 4.0), (-66.0, -101.0, (W + 260.0, H + 140.0), True, 0.0))
    for hy, ang, arm_to, right, dx in rows:                     # his left hand (higher), then his right
        p = cam.to_frame((mid + dx, hy))
        p = (p[0] + back * 0.5, p[1] + back)
        _glove_back(c, p, ang, s, (arm_to[0], arm_to[1] + back), right=right)


def shot_pov(c, t):
    """His POV: the great door from the corridor, his hands on its edge driving it shut; the gap of
    gold narrows on the two inside and closes."""
    tt = K.twos(t)
    cam = cam_pov(t)
    g = door_open_at(t)
    Bk.vault_door(c, cam, t, open=g, bolts=1.0, wheel=S6.WHEEL_TURN, dial=DIAL_END, light="gold",
                  inside=lambda cc: _inside(cc, t, tt), face=S6.FACE_D, glow=g)
    _push_hands(c, t, cam, g)


# ============================================================================ the dial, in RED (14.25-15.0)
def red_dial(t):
    """The dial (degrees clockwise): as s06 left it; a little right (the lock's bolt shoots home);
    then spun hard left (the combination scrambled), running down."""
    a = DIAL_END + 40.0 * ease("inout", _u(t, (T_KNOB_ON[1], T_CLANK)))
    return a - SPIN_DEG * ease("out", _u(t, T_SPIN))


def _red_hand(c, t, dial):
    """His gloved hand on the knob from the lower right: the little turn, the flick, let go, gone."""
    on = ease("out3", _u(t, T_KNOB_ON))
    if on <= 0.0:
        return
    gone = ease("in", _u(t, T_KNOB_OFF))
    flick = ease("out", _u(t, (T_SPIN[0], T_SPIN[0] + 0.1)))
    let = ease("inout", _u(t, (T_SPIN[0] + 0.08, T_SPIN[0] + 0.18)))
    turn = 40.0 * ease("inout", _u(t, (T_KNOB_ON[1], T_CLANK))) - 70.0 * flick
    a = math.radians(-12.0 + 0.6 * turn)
    p = S6.DIAL_P
    rk = S6.KNOB_R * (0.98 + 0.25 * let)
    grip = (p[0] + rk * math.cos(a), p[1] + rk * math.sin(a))
    back = 640.0 * (1.0 - on) + 700.0 * gone
    wa = a + math.radians(40.0)
    wrist = (grip[0] + 900.0 * math.cos(wa) + back, grip[1] + 900.0 * math.sin(wa) + back * 0.6)
    grip = (grip[0] + back, grip[1] + back * 0.6)
    F.hand(c, "knight", wrist, grip, 1.15, open_u=clamp(1.0 - on * 2.0) + 0.9 * let)


def shot_dial(c, t):
    """s06's dial, close, in the dark: his gloved hand, CLANK, the spin."""
    dial = red_dial(t)
    p = S6.DIAL_P
    K.fill(c, S6.FACE_D)
    for i, (rr, al) in enumerate(((560.0, 0.5), (700.0, 0.6), (860.0, 0.7))):
        bass.hole(c, (p[0], p[1] + 40.0), rr, INK, seed=760 + i, rect=(-20.0, -20.0, W + 20.0, H + 20.0), n=96,
                  alpha=al)
    Bk.dial_face(c, p, S6.DIAL_RF, dial, color=RED, face=INK, bezel=lerp(S6.FACE_D, PAPER, 0.16), seed=1192,
                 numerals=True)
    u = ease("out", _u(t, T_SPIN))
    if 0.0 < u and t < T_SPIN[1] + 0.12:                # the spin: a RED loop arrow, anticlockwise
        c.save()
        c.translate(p[0], 0.0)
        c.scale(-1.0, 1.0)
        c.translate(-p[0], 0.0)
        bass.loop_arrow(c, p, S6.LOOP_R, RED, width=26.0, u=u, rot=-40.0, sweep=320.0, head=2.2, seed=770,
                        alpha=0.95 * (1.0 - clamp((t - T_SPIN[1]) / 0.12)))
        c.restore()
    if T_CLANK <= t < T_CLANK + 0.8:                    # CLANK: the lock's bolt shoots home
        K.ripple(c, p, t, T_CLANK, RED, n=3, every=0.08, life=0.5, r0=S6.KNOB_R, r1=S6.DIAL_RF * 1.6, width=9.0,
                 seed=771, alpha=0.95)
    _red_hand(c, t, dial)


# ============================================================================ the section (15.0-17.0)
def sec_view(t):
    u = ease("inout", _u(t, (T_SECTION, T_SIDE)))
    z = math.exp(lerp(math.log(SEC_Z0), math.log(SEC_Z1), u))
    return (lerp(SEC_C0[0], SEC_C1[0], u), lerp(SEC_C0[1], SEC_C1[1], u)), z


@lru_cache(maxsize=None)
def sec_perfs():
    d = {}
    d["knight"] = C.perf("knight", [_seg("17_08", 5.7, 6.0, 0.0, 0.08, travel=0.0),
                                    _seg("16_08", 0.22, 1.75, T_RUN[0] - 0.1, 1.05, travel=0.0, blend=0.12),
                                    _seg("17_08", 5.7, 6.0, T_RUN[1] + 0.02, 0.08, travel=0.0, blend=0.15)],
                         facing=-1)
    d["architect"] = C.perf("architect", [_seg("104_02", 5.7, 7.3, 9.0, 0.1, travel=0.0)], facing=-1)
    d["cracker"] = C.perf("cracker", [_seg("104_02", 5.7, 7.3, 9.0, 0.12, travel=0.0, lean=10.0)], facing=-1)
    return d


def run_x(t):
    """His pelvis x on the hall's floor (section px): outside the vault door, then the run (steady)."""
    return lerp(RUN_FROM[0], RUN_TO[0], _u(t, T_RUN))


@lru_cache(maxsize=1)
def run_steps():
    """(points, times): his footstep dots, one on each eighth note of the run, where he is."""
    pts = [(run_x(tl) + (2.5 if i % 2 else -2.5), St.FEET - 2.5) for i, tl in enumerate(RUN_STEPS)]
    return pts, list(RUN_STEPS)


def _sec_knight(c, t, tt):
    st, pose = sec_perfs()["knight"](tt)
    x = run_x(tt)
    sw = 9.0 * math.sin(2.0 * math.pi * 2.4 * (tt - T_RUN[0])) * (1.0 if T_RUN[0] <= tt < T_RUN[1] else 0.0)
    pose.arms["near"] = ("ang", 10.0 + sw, 14.0)
    pose.arms["far"] = ("ang", 4.0 - sw, 20.0)
    pose.lean += 7.0
    pose.hold = {"near": Bk.hold_sack(1.0, seed=41), "far": Bk.hold_sack(1.0, seed=42)}
    St.fig(c, "knight", st, pose, x - st["pelvis"][0] * St.FIG_S, St.FEET, facing=-1, lit=None)


def shot_section(c, t):
    tt = K.twos(t)
    centre, z = sec_view(t)

    def people(cc, where, n, rect):
        if where == "vault":
            st, pose = sec_perfs()["cracker"](tt)
            St.fig(cc, "cracker", st, pose, CR_SEC, St.FEET, facing=-1, lit=None)
            st, pose = sec_perfs()["architect"](tt)
            St.fig(cc, "architect", st, pose, HER_SEC, St.FEET, facing=-1, lit=None)
        elif where == "hall":
            _sec_knight(cc, t, tt)

    c.save()
    St.zoom_on(c, centre, z)
    St.draw_section(c, FILM_T0 + t, lit={}, people=people, hall_lamp=1.0, vault_lit=0.0, gold_glow=0.0, gold=0.0,
                    ruby_box=1.0, ruby=False, vault_door=0.0, side_door=0.0, hatch=0.0, lid_a=1.0,
                    car=dict(lights=0.0), clock=CLOCK, bank_clock=CLOCK)
    pts, times = run_steps()
    K.step_dots(c, pts, times, t, RED, r=4.6, seed=781)
    u = k(t, T_RING[0], T_RING[1], "inout")
    if u > 0.0:
        K.marker_ring(c, RING_C, RING_R[0], RING_R[1], u, RED, width=14.0 / z, seed=782)
    c.restore()


# ============================================================================ the alarm: the side door (17.0-20.0)
def sd_cam(t):
    cam = Bk.Cam.toward(SD_CAM0, SD_CAM1, ease("inout", _u(t, T_BELL_PUSH)), SD_BELL)
    if T_SIDE - 0.5 / 24.0 <= t < T_SIDE + 0.5 / 24.0:   # the BANG: one frame's jolt (that frame only)
        cam = Bk.Cam(cam.x - SHAKE[0] / cam.zoom, cam.y - SHAKE[1] / cam.zoom, cam.zoom)
    return cam


@lru_cache(maxsize=1)
def _sd_run():
    """(perf, x0): his run out of the side door, his pelvis in the doorway as it bursts open."""
    perf = C.perf("knight", [_seg("16_08", 0.0, 1.75, T_SIDE, 1.0)], facing=-1)
    return perf, (SD[0] + SD[2]) / 2.0 + SD_IN - perf(T_SIDE)[0]["pelvis"][0] * FS


def sd_knight(tt):
    perf, x0 = _sd_run()
    st, pose = perf(max(tt, T_SIDE))
    sw = 10.0 * math.sin(2.0 * math.pi * 2.4 * (tt - T_SIDE))
    pose.arms["near"] = ("ang", 12.0 + sw, 14.0)
    pose.arms["far"] = ("ang", 4.0 - sw, 20.0)
    pose.lean = pose.lean + 6.0
    pose.hold = {"near": Bk.hold_sack(1.0, seed=41), "far": Bk.hold_sack(1.0, seed=42)}
    return st, pose, x0


def side_door_u(t):
    """The side door, flung open: the cut finds its leaf a third of the way round, and on the next
    frame it is back against the wall (bank_front puts the outback on it)."""
    return clamp((t - T_SIDE) / 0.16 + 0.1)


def shot_side(c, t):
    """The side door from the street: flung open, the Knight out with the sacks and away left for his
    car; over the door the bell rings RED, a ripple on every beat; the camera pushes in on it."""
    tt = K.twos(t)
    cam = sd_cam(t)

    def runner(cc):
        if T_SIDE + 0.03 <= t and tt < T_SIDE + 1.4:          # behind the leaf on the BANG's frame
            st, pose, x0 = sd_knight(tt)
            C.draw(cc, "knight", st, pose, x0, 0.0, FS, -1, bg=NIGHT, rim_w=RIM_W / cam.zoom, light=(0.6, -0.8))

    St.bank_front(c, cam, FILM_T0 + t, clock=CLOCK, bell_ring=1.0, side_door=side_door_u(t), low=1.0, guard_x=None,
                  car=True, car_x=St.CAR_FX, lid=1.0, extra=runner, inside_lit=SD_LIGHT)
    b = cam.to_frame((SD_BELL[0], SD_BELL[1] + 2.0))
    n = int((t - T_SIDE) / K.BEAT) + 1
    for kk in range(max(0, n - 3), n):                    # the alarm: a RED ripple off the bell on every beat
        K.ripple(c, b, t, T_SIDE + kk * K.BEAT, RED, n=3, every=0.12, life=1.1, r0=26.0 * cam.zoom, r1=760.0,
                 width=9.0, seed=790 + 3 * kk, alpha=0.9)


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, INK)
    with f.screen() as c:
        if T_RUBY[0] <= t < T_RUBY[1]:
            shot_ruby(c, t)
        elif t < T_POV:
            shot_vault(c, t)
        elif t < T_SLAM:
            shot_pov(c, t)
        elif t < T_DIAL_IN:
            K.fill(c, INK)
        elif t < T_SECTION:
            shot_dial(c, t)
        elif t < T_SIDE:
            shot_section(c, t)
        else:
            shot_side(c, t)


def _pan_f(fx):
    return round(clamp((fx - 540.0) / 540.0, -1.0, 1.0), 2)


def _pan_v(t, p):
    """Pan of a place in the vault (mirrored set px) as the vault's camera sees it at t."""
    return _pan_f(cam_vault(t).to_frame(p)[0])


GRUNT = "films/double_cross/audio/gen/grunt_knight.mp3"     # the Knight's own voice take (DOUBLE CROSS)
WALK_STEPS = ((10.08, "near"), (10.72, "far"), (11.45, "near"))   # his feet on the steel, out of the vault
SD_STEPS = (17.31, 17.62, 17.79, 18.25)                          # his run, out of the side door


def cues(T):
    out = []
    # ---- the vault: each bar off the stack, handed over, into the sack (faint under the ruby, close)
    for kk, (t0, t1) in enumerate(T_SCOOPS):
        d = t1 - t0
        tl, ti = round(t0 + 0.22 * d, 3), round(t0 + 0.64 * d, 3)
        close = T_RUBY[0] <= tl < T_RUBY[1]
        out.append(Cue(tl, "gold_clink", gain_db=(-25 if close else -17) - (kk % 2),
                       pan=-0.3 if close else _pan_v(tl, _bar_pos(kk)),
                       dc="a gold bar lifted off the stack: a clink of gold on gold"))
        out.append(Cue(ti, "gold_drop", gain_db=-24 if close else -16, pan=-0.3 if close else _pan_v(ti, SACK_A),
                       dc="a gold bar drops into the bag: a heavy muffled chink of gold on gold"))
    out.append(Cue(T_BOX[0], "box_open", gain_db=-19, pan=_pan_v(T_BOX[0], BOX_C), dur=round(T_BOX[1] - T_BOX[0], 3),
                   dc="her deposit box's little door opens: a small latch click and a tiny hinge squeak"))
    # ---- the ruby, close
    out.append(Cue(T_RUBY[0], "ruby_close", gain_db=-24, pan=0.0,
                   dc="cut in close on the open box: a ruby on a dark cushion, glowing red"))
    out.append(Cue(1.72, "ruby_glint", gain_db=-20, pan=0.05, dc="a tiny red glint in the open box: a faint high ting"))
    out.append(Cue(T_IN_HAND[0], "glove_creak", gain_db=-26, pan=-0.4, dc="her gloved hand comes in: a soft leather creak"))
    out.append(Cue(round(T_PINCH[0] + 0.1, 3), "ruby_tick", gain_db=-24, pan=0.0,
                   dc="her finger and thumb close on the ruby: a tiny tick of stone on leather"))
    out.append(Cue(T_LIFT_R[0], "string_harmonic", gain_db=-22, pan=0.0, dur=round(T_LIFT_R[1] - T_LIFT_R[0], 3),
                   dc="she lifts it out into the light: a soft rising string harmonic"))
    out.append(Cue(T_FLARE, "ruby_shimmer", gain_db=-18, pan=-0.05,
                   dc="the ruby flares in the light: a bright glassy shimmer (not the celesta)"))
    out.append(Cue(T_AWAY[0], "cloth_swish", gain_db=-24, pan=-0.5, dc="her hand takes it away: a quick cloth swish"))
    tp = round(T_POCKET[0] + 0.4, 3)
    out.append(Cue(tp, "pocket_rustle", gain_db=-26, pan=_pan_v(tp, POCKET),
                   dc="she slips it into her coat pocket: a soft cloth rustle"))
    # ---- the Cracker up off his knee, turned to the boxes; the sack shut
    out.append(Cue(T_CR_UP[0], "knee_up", gain_db=-27, pan=_pan_v(T_CR_UP[0], (CRACK_AT, -40.0)),
                   desc="the old man gets up off his knee on the steel floor: a cloth rustle, a creak of old joints"))
    out.append(Cue(T_CR_TURN[1], "crew_step", gain_db=-26, pan=_pan_v(T_CR_TURN[1], (CRACK_AT, 0.0)),
                   dc="a soft step on a steel-plated floor"))
    out.append(Cue(T_CINCH[0], "sack_cinch", gain_db=-20, pan=_pan_v(T_CINCH[0], SACK_A),
                   dur=round(T_CINCH[1] - T_CINCH[0], 3), dc="he pulls the bag's neck shut: canvas cinched tight on gold"))
    out.append(Cue(round(T_RISE[0] + 0.05, 3), "knight_breath", gain_db=-22,
                   pan=_pan_v(T_RISE[0], (KNIGHT_AT, -100.0)), dc="a slow breath out: he straightens up over the gold"))
    # ---- his look: his low note, a cello pedal; the theme inverted, low, its last D on the BOOM
    out.append(Cue(T_LOOK, "his_note", gain_db=-14, pan=0.2, dur=3.0,
                   desc="his look: his low note, C# on the cellos, held as a pedal (the bar line)"))
    out.append(Cue(T_INVERSION, "theme_inverted", gain_db=-12, pan=-0.1, dur=round(T_SLAM - T_INVERSION, 3),
                   desc="THE THEME in mirror inversion, low and dark on cellos and basses: four bars, its last D "
                        "landing on the BOOM"))
    looks = ((T_LOOK_SACKS[0], SACKS_AT, "the two full sacks"), (T_LOOK_DOOR[0], DOOR_AT, "the open door"),
             (T_LOOK_TWO[0], TWO_AT, "the two of them, their backs turned"))
    for t0, p, what in looks:
        out.append(Cue(t0, "look_tick", gain_db=-22, pan=_pan_v(t0, p),
                       desc=f"his red look flies to {what}: a soft dry tick, a plucked low C# under the cellos"))
    out.append(Cue(T_HEAD_BACK, "collar_creak", gain_db=-27, pan=_pan_v(T_HEAD_BACK, (KNIGHT_AT, -110.0)),
                   desc="his head snaps round over his shoulder: a leather collar's creak"))
    # ---- he heaves both sacks (his grunt) and steps out through the door
    out.append(Cue(T_HEAVE[0], "grunt", gain_db=-17, pan=_pan_v(T_HEAVE[0], (KNIGHT_AT, -100.0)), take=GRUNT,
                   cut=(5.06, 5.76), dc="he heaves up the two heavy bags: a strained grunt, the gold shifting inside them"))
    out.append(Cue(T_TURN_OUT[0], "heel_scuff", gain_db=-22, pan=_pan_v(T_TURN_OUT[0], (KNIGHT_AT, 0.0)),
                   dc="heel scuff: the Knight turns on his heel toward the door"))
    for tw, side in WALK_STEPS:
        out.append(Cue(tw, "knight_step", gain_db=-21, pan=_pan_v(tw, (_out_x() + perfs()["knight_out"](tw)[0]["feet"][side][0] * FS, 0.0)),
                       dc="footstep: the Knight's heavy step on the steel floor, two full bags swinging"))
    # ---- his POV: the door driven shut on them
    out.append(Cue(T_HANDS_ON[0], "glove_slap", gain_db=-18, pan=0.45,
                   desc="his gloved palms slap flat on the great door's steel edge"))
    out.append(Cue(T_SWING[0], "hinge_groan", gain_db=-9, pan=0.5, dur=round(T_SWING[1] - T_SWING[0], 3),
                   dc="the great door's hinge groans as he swings the door shut, faster and faster"))
    out.append(Cue(round(T_SHOVE[0] + 0.06, 3), "lunge_step", gain_db=-22, pan=0.3,
                   dc="footstep: the Knight's shoe plants hard on the steel floor as he lunges"))
    out.append(Cue(round(T_SHOVE[0] + 0.12, 3), "grunt", gain_db=-15, pan=0.3, take=GRUNT, cut=(0.10, 1.64),
                   dc="he throws his weight against the vault door: a strained grunt"))
    a, b = T_TURN_IN["cracker"]
    out.append(Cue(a, "inside_gasp", gain_db=-22, pan=_pan_f(cam_pov(a).to_frame((IN_X["cracker"], -60.0))[0]),
                   dc="inside the vault, the Cracker turns with a start: a gasp (muffled by the closing door)"))
    out.append(Cue(round(0.5 * (T_LUNGE_IN[0] + T_LUNGE_IN[1]), 3), "inside_step", gain_db=-27,
                   pan=_pan_f(cam_pov(T_LUNGE_IN[0]).to_frame((IN_X["cracker"], -60.0))[0]),
                   desc="footstep: inside the vault, the Cracker's startled half step back (muffled by the closing door)"))
    a, b = T_TURN_IN["architect"]
    out.append(Cue(a, "inside_swish", gain_db=-25, pan=_pan_f(cam_pov(a).to_frame((IN_X["architect"], -60.0))[0]),
                   desc="inside the vault, she turns round, unhurried: a coat's soft swish (muffled by the closing door)"))
    out.append(Cue(round(T_LET_GO[0] + 0.15, 3), "step_back", gain_db=-24, pan=0.4,
                   dc="footstep: the Knight steps back on the steel floor"))
    out.append(Cue(T_SLAM, "boom", gain_db=-2, pan=0.0, dc="BOOM: the vault door slams shut; black"))
    n = Bk.N_BOLTS
    for kk in range(n):
        tb = round(T_BOLTS[0] + (T_BOLTS[1] - T_BOLTS[0]) * kk / (n - 1), 3)
        an = math.radians(-90.0 + 15.0 + 30.0 * kk)
        out.append(Cue(tb, "bolt_clack", gain_db=-14, pan=round(0.6 * math.cos(an), 2),
                       dc="in the dark, a heavy steel bolt shoots home into the door frame: one clack of a rolling run "
                          "round the rim"))
    # ---- the dial, in red
    out.append(Cue(T_KNOB_ON[0], "knob_creak", gain_db=-24, pan=0.3, dc="a gloved hand takes the dial's knob: a leather creak"))
    out.append(Cue(T_CLANK, "clank", gain_db=-6, pan=0.1, dc="CLANK: the lock's bolt shoots home"))
    out.append(Cue(T_SPIN[0], "dial_spin", gain_db=-15, pan=0.0, dur=round(T_SPIN[1] - T_SPIN[0], 3),
                   dc="the dial spins left in red: a fast run of ratchet ticks (the combination scrambled)"))
    # ---- the section: the second ring; his run to the side door, a dot on every eighth note
    out.append(Cue(T_RING[0], "marker_squeak", gain_db=-11, pan=_pan_f(540.0 + (RING_C[0] - SEC_C0[0]) * SEC_Z0),
                   dur=T_RING[1], desc="THE SECOND RED MARKER RING drawn round the vault: a felt marker's squeak"))
    out.append(Cue(T_RING[0], "low_stab", gain_db=-10, pan=0.0,
                   desc="a low string stab under the ring: the two of them locked in"))
    for i, ts in enumerate(RUN_STEPS):
        out.append(Cue(round(ts, 3), "run_step", gain_db=-15 - (i % 2),
                       pan=_pan_f(540.0 + (run_x(ts) - sec_view(ts)[0][0]) * sec_view(ts)[1]),
                       desc="footstep: the Knight's heavy run across the hall's stone floor, two full bags swinging "
                            "(on a red dot)"))
    out.append(Cue(round(T_RUN[0] + 0.1, 3), "bags_swing", gain_db=-21, pan=-0.2, dur=round(T_RUN[1] - T_RUN[0], 3),
                   dc="the two bags swing, the gold clinking in them"))
    # ---- the alarm: the side door, the bell; the push in on the bell
    out.append(Cue(T_SIDE, "bang", gain_db=-4, pan=0.05,
                   dc="BANG: the side door flung open against the wall, the alarm bell right over it"))
    out.append(Cue(T_SIDE, "alarm_bell", gain_db=-6, pan=0.05, dur=round(T_END - T_SIDE, 3),
                   desc="alarm bell: the bell over the side door rings and rings, loud, a red ripple on every beat"))
    perf, x0 = _sd_run()
    for ts in SD_STEPS:
        xf = sd_cam(ts).to_frame((x0 + perf(ts)[0]["pelvis"][0] * FS, 0.0))[0]
        out.append(Cue(ts, "run_step", gain_db=-18 if xf > 0.0 else -22, pan=_pan_f(xf),
                       dc="footstep: the Knight's heavy run on the alley's cobbles, two full bags swinging"))
    out.append(Cue(round(T_SIDE + 0.1, 3), "bags_swing", gain_db=-20, pan=-0.4, dur=0.9,
                   dc="the two bags swing, the gold clinking in them"))
    out.append(Cue(T_BELL_PUSH[0], "bell_push", gain_db=-10, pan=0.0, dur=round(T_BELL_PUSH[1] - T_BELL_PUSH[0], 3),
                   dc="the camera pushes in on the ringing bell (the bell louder, nearer)"))
    return sorted(out, key=lambda q: q["t"])
