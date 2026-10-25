"""s02 CREW (12-28). Three hands set three pieces at the start of the route, and after each, the
face that goes with it, each in its own light, a lens on a leader line joining the face to its
piece on the plan:
  the Architect, her gloved hand, the white queen; her profile on the lamp's gold;
  the Cracker, an old hand in a shirt cuff, the gold bishop; his profile on steel, a glint;
  the Knight, a heavy hand that slams the red knight down (the others jump); his profile in the
  dark, lit red by his cigarette.
Then the table from the side under the swinging lamp, with time to read it (9-16): the three
pieces stand on the plan at her end. She leans in, talking low, and taps the plan beside them
twice: here (10.0, 10.5); the Cracker nods. His red look goes down to the X (11.5) and hers goes
across to him (12.5). She knows. She picks up the chalk (14.0), and the camera tilts down over
the table onto the plan (14-16), the pieces where they stand and her chalk coming in: s03 begins
on that frame.
"""
import math

from engine import bass
from engine import paperdoll as pd
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross import cast as C
from films.double_cross import faces as F
from films.double_cross import kit as K
from films.double_cross import plan as P

# shots
SHOTS = ((0.0, "table_q"), (1.5, "her"), (3.5, "table_b"), (4.5, "cracker"), (6.5, "table_k"), (7.5, "knight"),
         (9.0, "side"))
T_QUEEN = 1.0             # the queen is set (clack)
T_HER_CALL = 2.0          # the lens joins her to her piece
T_BISHOP = 4.0            # the bishop is set (clack)
T_CR_CALL = 5.0
T_GLINT = 5.5             # the light crosses his spectacles (ting)
T_KNIGHT = 7.0            # the knight slams down (thud); the others jump
T_DRAW = 8.0              # he draws on the cigarette (the ember flares)
T_KN_CALL = 7.9
T_EXHALE = 8.5
T_LEAN = (9.4, 9.95)      # she leans in over the plan, talking low ...
T_MURMUR = (9.25, 11.3)   # (her voice, murmured: the briefing begins)
T_TAPS = (10.0, 10.5)     # ... and taps it beside the pieces, twice: here
T_BACK = (10.7, 11.2)     # she straightens
T_NOD = 10.75             # the Cracker nods
T_HIS_LOOK = 11.5         # his red look to the X
T_HER_LOOK = 12.5         # her white look to him: she knows
T_REACH = 13.5            # she reaches for the chalk
T_CHALK = 14.0            # she has it
T_TILT = (14.0, 16.0)     # the camera tilts down over the table onto the plan (s03's first frame)

# where the pieces stand at the start of the route (plan px), round manhole A
Q_AT = (214.0, 1414.0)
B_AT = (290.0, 1424.0)
N_AT = (250.0, 1352.0)
CAM_A = P.PlanCam(268.0, 1376.0, 2.05, 46.0, -14.0)
CAM_A2 = P.PlanCam(258.0, 1384.0, 2.2, 44.0, -16.0)
PIECE_H = 100.0


def motion_blur(t, T):
    return 1


def shot_at(t):
    name, t0 = SHOTS[0][1], 0.0
    for s0, nm in SHOTS:
        if t >= s0:
            name, t0 = nm, s0
    return name, t0


# ============================================================================ the table, close
def table_cam(t):
    if t < 1.5:
        return P.PlanCam.lerp(P.TABLE, CAM_A, ease("inout3", clamp((t - 0.25) / 1.05)))
    u = clamp((t - 3.5) / 4.0)
    cam = P.PlanCam.lerp(CAM_A, CAM_A2, ease("inout", u))
    if T_KNIGHT <= t < T_KNIGHT + 0.35:                 # the slam shakes the table
        a = (1.0 - (t - T_KNIGHT) / 0.35) ** 2
        cam = P.PlanCam(cam.cx + 6.0 * a * math.sin(t * 90.0), cam.cy + 9.0 * a * math.sin(t * 77.0), cam.zoom,
                        cam.phi, cam.yaw)
    return cam


def _carry(t, t_set, start, lift0=230.0, dur=0.62, slam=False):
    """A piece carried in by a hand and set down at t_set: (offset along the way in, lift)."""
    u = clamp((t - (t_set - dur)) / dur)
    if slam:
        e = ease("in3", u)
        lift = lift0 * (1.0 - e)
    else:
        e = ease("inout3", u)
        lift = lift0 * (1.0 - ease("inout", clamp((u - 0.25) / 0.75)))
    return (1.0 - e), lift


def _hand_for(c, cam, who, kind, col, at, t, t_set, wrist, come_from, slam=False):
    """The hand bringing in one piece (before/at/after t_set) and the piece in it."""
    if t < t_set - 0.7 or t > t_set + 0.75:
        return False
    off, lift = _carry(t, t_set, come_from, slam=slam)
    p = (at[0] + come_from[0] * off, at[1] + come_from[1] * off)
    open_u = clamp((t - t_set - 0.04) / 0.18)
    leave = ease("in3", clamp((t - t_set - 0.25) / 0.5))
    if t < t_set:
        P.piece_on(c, cam, kind, p, PIECE_H, col, K.INK, lift=lift)
    v = cam.to_view(p)
    crown = (v[0], v[1] - (lift + PIECE_H * 0.96) * cam.zoom * cam.stand())
    if leave > 0.0:                                     # the hand withdraws the way it came, rising
        crown = (crown[0] + (wrist[0] - crown[0]) * leave * 0.8, crown[1] - 260.0 * leave + (wrist[1] - crown[1]) * leave * 0.3)
    F.hand(c, who, wrist, crown, 0.65 * cam.zoom * cam.stand(), open_u=open_u)     # hands: about 1.5 pieces tall
    return True


def _jump(t):
    """The queen and bishop jump when the knight slams down: lift (plan px) and a wobble."""
    if not (T_KNIGHT <= t < T_KNIGHT + 0.5):
        return 0.0, 0.0
    u = (t - T_KNIGHT) / 0.5
    return 26.0 * math.sin(math.pi * min(1.0, u / 0.55)) * (1.0 if u < 0.55 else 0.0) + \
        (6.0 * math.sin(math.pi * (u - 0.55) / 0.45) if u >= 0.55 else 0.0), 7.0 * math.sin(u * 14.0) * (1.0 - u)


def _plan_as_titled(c):
    """The plan as s01 leaves it: every part ruled in, the X on the vault."""
    P.draw_plan(c, bell=False)
    K.xmark(c, P.X_VAULT, 56.0, seed=20)


def table_shot(c, t):
    cam = table_cam(t)
    P.table(c, cam, 1.0, 1.0, 0.0, on_plan=_plan_as_titled)
    jl, jt = _jump(t)
    standing = []
    if t >= T_QUEEN:
        standing.append(("queen", Q_AT, K.PAPER, 1, jl, jt))
    if t >= T_BISHOP:
        standing.append(("bishop", B_AT, K.GOLD, -1, jl * 0.8, -jt))
    if t >= T_KNIGHT:
        standing.append(("knight", N_AT, K.RED, 1, 0.0, 0.0))
    for kind, p, col, fc, lift, tilt in sorted(standing, key=lambda it: cam.depth(it[1])):
        P.piece_on(c, cam, kind, p, PIECE_H, col, K.INK, facing=fc, lift=lift, tilt=tilt)
    # the hands, each coming from the side its owner sits on
    _hand_for(c, cam, "architect", "queen", K.PAPER, Q_AT, t, T_QUEEN, (-420.0, 900.0), (-420.0, -60.0))
    _hand_for(c, cam, "cracker", "bishop", K.GOLD, B_AT, t, T_BISHOP, (1500.0, 120.0), (360.0, -380.0))
    _hand_for(c, cam, "knight", "knight", K.RED, N_AT, t, T_KNIGHT, (1560.0, 700.0), (420.0, -120.0), slam=True)
    if T_KNIGHT <= t < T_KNIGHT + 0.6:                  # the slam: chalk dust off the paper
        v = cam.to_view(N_AT)
        for i in range(9):
            a = math.radians(-160.0 + 140.0 * i / 8.0)
            d = (40.0 + 150.0 * ease("out3", (t - T_KNIGHT) / 0.6)) * cam.zoom / 2.0
            K.dot(c, (v[0] + d * math.cos(a) * 1.4, v[1] + d * math.sin(a) * 0.5), 5.0 * (1.0 - (t - T_KNIGHT) / 0.6),
                  K.PAPER, seed=70 + i, alpha=0.8)


# ============================================================================ the faces
def _lens_of(piece_at, kind, col, fc):
    """What a callout's lens shows: that piece standing on the plan, close."""
    def inside(c, centre):
        cam = P.PlanCam(piece_at[0], piece_at[1] - 30.0, 2.6, 44.0, -14.0, fx=centre[0], fy=centre[1] + 40.0)
        K.fill(c, K.DEEP)
        P.table(c, cam, 1.0, 1.0, 0.0, on_plan=_plan_as_titled)
        P.piece_on(c, cam, kind, piece_at, PIECE_H, col, K.INK, facing=fc)
    return inside


def face_shot(c, t, who, t0):
    u = (t - t0) / 2.0
    if who == "her":
        K.fill(c, K.GOLD)
        s = lerp(1.22, 1.30, ease("inout", u))
        at = (lerp(630.0, 612.0, ease("inout", u)), 1590.0)
        look = lerp(0.1, 0.7, ease("inout", clamp((t - t0 - 0.3) / 0.6)))
        m = F.her(c, at, s, look=look, t=t)
        centre, ring, piece = (816.0, 360.0), K.PAPER, ("queen", Q_AT, K.PAPER, 1)
        tc = T_HER_CALL
    elif who == "cracker":
        K.fill(c, K.STEEL)
        s = lerp(1.24, 1.31, ease("inout", u))
        at = (lerp(600.0, 588.0, ease("inout", u)), 1600.0)
        glint = clamp((t - T_GLINT) / 0.4)
        m = F.cracker(c, at, s, look=0.3, glint=glint if 0.0 < glint < 1.0 else 0.0, t=t)
        centre, ring, piece = (830.0, 330.0), K.GOLD, ("bishop", B_AT, K.GOLD, -1)
        tc = T_CR_CALL
        if T_GLINT + 0.15 <= t < T_GLINT + 0.6:
            K.twinkle(c, (m["lens"][0] + 30.0, m["lens"][1] - 34.0), 46.0 * math.sin(math.pi * (t - T_GLINT - 0.15) / 0.45),
                      K.PAPER)
    else:
        K.fill(c, K.DEEP)
        u2 = (t - t0) / 1.5
        s = lerp(1.24, 1.32, ease("inout", u2))
        at = (lerp(460.0, 476.0, ease("inout", u2)), 1600.0)
        dr = clamp((t - (T_DRAW - 0.25)) / 0.9)
        m = F.knight(c, at, s, look=0.6, draw=dr, t=t, smoke=1.0)
        centre, ring, piece = (250.0, 330.0), K.RED, ("knight", N_AT, K.RED, 1)
        tc = T_KN_CALL
    cu = clamp((t - tc) / 0.35)
    if cu > 0.0:
        inside = _lens_of(piece[1], piece[0], piece[2], piece[3])
        K.callout(c, m["eye"], centre, 150.0, lambda cc: inside(cc, centre), u=cu, color=ring, ring_w=9.0, dot_r=8.0,
                  line_w=4.0, seed=31)


# ============================================================================ the table from the side
SIDE_FLOOR = 2010.0
SIDE_S = 1.95
TABLE_TOP = 1430.0
TABLE_X = (236.0, 852.0)
LAMP_PIVOT = (545.0, -80.0)
LAMP_LEN = 520.0
HER_X, KNIGHT_X, CRACKER_X = 116.0, 976.0, 700.0
# the plan on the table, edge-on, as a plan camera sees it (the tilt starts from this): its sheet
# spans the blue strip, the table's middle (plan y 1345) the pivot
SIDE_PC = P.PlanCam(545.0, 1345.0, 0.606, 0.0, 0.0, 540.0, TABLE_TOP - 4.0)
X_SIDE = (SIDE_PC.to_view(P.X_VAULT)[0], TABLE_TOP - 8.0)    # the X on the plan, seen edge-on
TAP_AT = (SIDE_PC.to_view(Q_AT)[0] - 24.0, TABLE_TOP - 4.0)  # where she taps: beside the pieces


def lamp_angle(t):
    return 4.5 * math.sin(2.0 * math.pi * (t - 9.0) / 2.6 + 0.6)


def _lamp(c, t):
    a = math.radians(lamp_angle(t))
    d = (math.sin(a), math.cos(a))
    shade = (LAMP_PIVOT[0] + d[0] * LAMP_LEN, LAMP_PIVOT[1] + d[1] * LAMP_LEN)
    # the light: a gold cone down onto the table, under the shade
    K.cone(c, shade, math.degrees(math.atan2(d[1], d[0])), 34.0, 1000.0, K.GOLD, alpha=0.2, steps=3)
    bass.line_band(c, [LAMP_PIVOT, shade], K.INK, width=6.0, seed=51)
    c.save()
    c.translate(*shade)
    c.rotate(-a)
    shade_pts = bass.orient([(-34.0, -40.0), (34.0, -40.0), (150.0, 56.0), (-150.0, 56.0)], True)
    bass.fill_polys(c, [shade_pts], K.INK)
    bass.line_band(c, [(-150.0, 56.0), (150.0, 56.0)], K.GOLD, width=8.0, seed=52)
    bass.fill_polys(c, [bass.draw.ellipse_pts((0.0, 62.0), 42.0, 16.0, n=24)], K.PAPER)
    c.restore()
    return shade


def _table(c):
    """The table side-on: the blueprint on its top, a heavy cloth hanging to the floor in front."""
    x0, x1 = TABLE_X
    bass.fill_polys(c, [bass.cut_rect(x0, TABLE_TOP, x1, SIDE_FLOOR + 40.0, seed=53, amp=0.6)], K.INK)
    bass.line_band(c, [(x0, TABLE_TOP + 2.0), (x1, TABLE_TOP + 2.0)], K.STEEL, width=4.0, seed=54, alpha=0.8)
    for x in (x0 + 4.0, x1 - 4.0):                       # the cloth's folds at the corners
        bass.line_band(c, [(x, TABLE_TOP + 10.0), (x + (6.0 if x < 500 else -6.0), SIDE_FLOOR)], K.DEEP, width=5.0,
                       seed=55 + int(x))
    # the blueprint on it, edge-on: a thin blue strip curling up at the far end
    bass.fill_polys(c, [bass.cut_rect(x0 + 16.0, TABLE_TOP - 7.0, x1 - 30.0, TABLE_TOP + 1.0, seed=56, amp=0.4)], K.BLUE)
    bass.line_band(c, [(x1 - 32.0, TABLE_TOP - 4.0), (x1 - 12.0, TABLE_TOP - 22.0), (x1 - 18.0, TABLE_TOP - 44.0),
                       (x1 - 34.0, TABLE_TOP - 46.0)], K.BLUE, width=7.0, seed=57)


def _people(c, t):
    """Her (left end of the table, facing right), the Cracker (behind it, bent over the plan,
    facing left), the Knight (right end, facing left). Returns their joints."""
    out = {}
    # the Cracker, behind the table: only his head and shoulders show above it; he nods
    st = C.standing("cracker")
    pose = pd.Pose(lean=24.0, head=-28.0 - 9.0 * math.sin(math.pi * clamp((t - T_NOD) / 0.4)))
    pose.arms["near"] = ("ang", 64.0, 40.0)
    pose.arms["far"] = ("ang", 70.0, 34.0)
    out["cracker"] = C.draw(c, "cracker", st, pose, CRACKER_X, SIDE_FLOOR + 250.0, SIDE_S * 0.92, -1, bg=K.DEEP, rim_w=5.0)
    _table(c)
    # her: standing; she leans in and taps the plan beside the pieces (here), straightens; later
    # she bends to take the chalk from the table's edge, and straightens with it
    st = C.standing("architect")
    pose = pd.Pose(head=-6.0 if t < T_HER_LOOK else 0.0)
    tap = ease("inout", clamp((t - T_LEAN[0]) / (T_LEAN[1] - T_LEAN[0]))) * \
        (1.0 - ease("inout", clamp((t - T_BACK[0]) / (T_BACK[1] - T_BACK[0]))))
    lift = 18.0 * (1.0 - max(math.exp(-((t - tt) / 0.08) ** 2) for tt in T_TAPS))   # the finger comes down twice
    reach = ease("inout", clamp((t - T_REACH) / 0.5)) * (1.0 - ease("inout", clamp((t - T_CHALK) / 0.45)))
    rest = (36.0, -290.0)
    tap_at = ((TAP_AT[0] - HER_X) / SIDE_S, (TAP_AT[1] - lift - SIDE_FLOOR) / SIDE_S)
    chalk_at = ((TABLE_X[0] + 40.0 - HER_X) / SIDE_S, (TABLE_TOP - 6.0 - SIDE_FLOOR) / SIDE_S)
    pose.lean = 24.0 * tap + 17.0 * reach
    pose.crouch = 26.0 * tap + 34.0 * reach
    pose.head -= 6.0 * tap
    target = (lerp(lerp(rest[0], tap_at[0], tap), chalk_at[0], reach), lerp(lerp(rest[1], tap_at[1], tap), chalk_at[1], reach))
    pose.arms["near"] = ("ik", target)
    pose.arms["far"] = ("ang", 8.0, 10.0)
    if t >= T_CHALK - 0.05:
        pose.hold["near"] = C.hold_chalk()
    out["architect"] = C.draw(c, "architect", st, pose, HER_X, SIDE_FLOOR, SIDE_S, 1, bg=K.DEEP, rim_w=5.0)
    # the Knight: heavy, still, smoking; his head goes down to the X
    st = C.standing("knight")
    pose = pd.Pose(head=-16.0 * ease("inout", clamp((t - (T_HIS_LOOK - 0.4)) / 0.4)))
    pose.arms["near"] = ("ang", -6.0, 16.0)
    pose.arms["far"] = ("ang", 4.0, 12.0)
    out["knight"] = C.draw(c, "knight", st, pose, KNIGHT_X, SIDE_FLOOR, SIDE_S, -1, bg=K.DEEP, rim_w=5.0)
    C.cigarette(c, out["knight"], t, SIDE_S * 0.6, facing=-1)
    return out


def tilt_cam(t):
    """The plan camera in the tilt: from the plan edge-on (SIDE_PC) up over the table to s03's
    first frame, the zoom geometric."""
    from films.double_cross.scenes import s03_plan as S3
    a, b = SIDE_PC, S3.cam_at(0.0)
    u = ease("inout", clamp((t - T_TILT[0]) / (T_TILT[1] - T_TILT[0])))
    v = [lerp(x, y, u) for x, y in zip(a.tuple(), b.tuple())]
    v[2] = math.exp(lerp(math.log(a.zoom), math.log(b.zoom), u))
    return P.PlanCam(*v)


def _pieces_on_table(c, cam):
    for kind, p, col, fc in sorted((("queen", Q_AT, K.PAPER, 1), ("bishop", B_AT, K.GOLD, -1), ("knight", N_AT, K.RED, 1)),
                                   key=lambda it: cam.depth(it[1])):
        P.piece_on(c, cam, kind, p, PIECE_H, col, K.INK, facing=fc, shadow=0.0)


def _side(c, t):
    """The table from the side, in frame px as the side shot frames it."""
    _lamp(c, t)
    heads = _people(c, t)
    if t < T_TILT[0]:
        _pieces_on_table(c, SIDE_PC)
    # the X, raised off the plan as a little chalk mark (we see the plan edge-on); it lies down
    # onto the plan as the camera starts to rise
    xu = clamp((t - (T_HIS_LOOK + 0.35)) / 0.3)
    down = 1.0 - ease("in", clamp((t - T_TILT[0]) / 0.25))
    xp = (X_SIDE[0], X_SIDE[1] - 46.0 * down)
    if down > 0.0:
        c.save()
        c.translate(xp[0], xp[1])
        c.scale(1.0, down)
        c.translate(-xp[0], -xp[1])
        K.xmark(c, xp, 40.0, xu, K.PAPER, width=8.0, seed=57)
        c.restore()
    if T_HIS_LOOK + 0.5 <= t < T_TILT[0]:
        K.ripple(c, xp, t, T_HIS_LOOK + 0.5, K.RED, n=1, life=0.6, r0=20.0, r1=70.0, width=4.0)
    his_eye = (heads["knight"]["head"][0] - 50.0, heads["knight"]["head"][1] + 78.0)
    her_eye = (heads["architect"]["head"][0] + 44.0, heads["architect"]["head"][1] + 78.0)
    K.sight_line(c, his_eye, (xp[0] + 26.0, xp[1] - 26.0), t, T_HIS_LOOK, K.RED, dur=0.45, r=9.0, gap=30.0,
                 head=34.0, seed=58)
    K.sight_line(c, her_eye, (his_eye[0] - 50.0, his_eye[1] + 6.0), t, T_HER_LOOK, K.PAPER, dur=0.5, r=9.0, gap=30.0,
                 head=34.0, seed=59)


def side_shot(c, t):
    K.fill(c, K.DEEP)
    if t < T_TILT[0]:
        _side(c, t)
        return
    # the tilt: the room stays pinned to the table's middle as the camera rises and pushes in,
    # and the plan opens up over it from edge-on; then the pieces, and her chalk coming in
    from films.double_cross.scenes import s03_plan as S3
    cam = tilt_cam(t)
    a0, a1 = SIDE_PC.to_view((SIDE_PC.cx, SIDE_PC.cy)), cam.to_view((SIDE_PC.cx, SIDE_PC.cy))
    k = cam.zoom / SIDE_PC.zoom
    c.save()
    c.translate(*a1)
    c.scale(k, k)
    c.translate(-a0[0], -a0[1])
    _side(c, t)
    c.restore()
    if cam.flat() < 1e-3:                    # the paper still edge-on: the strip is all there is
        _pieces_on_table(c, cam)
        return

    def on_plan(cc):
        P.draw_plan_a(cc, 1.0, S3.sweep(0.0), S3.plan_prog(0.0), S3.door_at(0.0))

    P.table(c, cam, 1.0, 1.0, 0.0, on_plan=on_plan)
    S3._draw_pieces(c, cam, 0.0)
    S3._chalk_hand(c, cam, t - T_TILT[1])


# ============================================================================ render
def render(f, t, T):
    name, t0 = shot_at(t)
    K.scene_setup(f, K.DEEP)
    with f.screen() as c:
        if name.startswith("table"):
            table_shot(c, t)
        elif name == "side":
            side_shot(c, t)
        else:
            face_shot(c, t, name, t0)


def cues(T):
    return [
        Cue(T_QUEEN - 0.6, "cloth: her sleeve comes in over the table", gain_db=-22, pan=-0.6),
        Cue(T_QUEEN, "clack: the white queen set on the plan (wood on paper on wood)", gain_db=-8, pan=-0.3),
        Cue(1.5, "cut to her profile: the theme's first phrase (vibraphone)", gain_db=-14),
        Cue(T_HER_CALL, "a soft chalk tick: the lens opens on her queen", gain_db=-18),
        Cue(T_BISHOP, "clack: the gold bishop set (a lighter, older hand)", gain_db=-9, pan=0.2),
        Cue(4.5, "cut to the Cracker: the theme's second phrase", gain_db=-14),
        Cue(T_CR_CALL, "a soft chalk tick: the lens opens on his bishop", gain_db=-18),
        Cue(T_GLINT, "ting: the light crosses his spectacles", gain_db=-12, pan=0.3),
        Cue(T_KNIGHT - 0.3, "a heavy sleeve swings in fast", gain_db=-16, pan=0.6),
        Cue(T_KNIGHT, "THUD: the red knight slammed down; the other pieces jump and rattle", gain_db=-4, pan=0.2),
        Cue(7.5, "cut to the Knight in the dark: a low muted trumpet note", gain_db=-14),
        Cue(T_DRAW, "the cigarette crackles as he draws on it", gain_db=-16, pan=-0.2),
        Cue(T_EXHALE, "he breathes the smoke out", gain_db=-20),
        Cue(9.0, "the table from the side: the lamp's chain creaks as it swings", gain_db=-22, dur=T_TILT[0] - 9.0),
        Cue(T_MURMUR[0], "her low voice: the briefing begins (a murmur, no words)", gain_db=-20, pan=-0.25,
            dur=T_MURMUR[1] - T_MURMUR[0]),
        Cue(T_TAPS[0], "her gloved finger taps the plan: here", gain_db=-16, pan=-0.35),
        Cue(T_TAPS[1], "her gloved finger taps the plan again", gain_db=-18, pan=-0.35),
        Cue(T_NOD, "the Cracker hums: hm (his voice, low)", gain_db=-22, pan=0.25),
        Cue(T_HIS_LOOK, "his look to the X: a low muted note, a semitone off", gain_db=-14),
        Cue(T_HER_LOOK, "her look to him: a low held note (she knows)", gain_db=-12, dur=T_TILT[0] - T_HER_LOOK),
        Cue(T_CHALK, "she picks up the chalk (a tiny scrape on the table)", gain_db=-16, pan=-0.6),
        Cue(T_TILT[0], "a rising paper whoosh: the camera tilts down over the table onto the plan", gain_db=-16,
            dur=T_TILT[1] - T_TILT[0]),
    ]
