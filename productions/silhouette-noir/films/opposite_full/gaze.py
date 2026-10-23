"""OPPOSITE (the full Bass cut), animator C: HIS GAZE. What s05 SEEN and s08 DOOR share.

  * the street on the night field (the Bass elevation, re-lit for this film: his window stays
    lit, her window can be dark, the whole street can sink into the dark);
  * her in her window with her hand at her mouth (the Bass window performance, re-posed);
  * him in his window, drawn so his head can lead a turn (a look back over his shoulder) and
    his eye can catch the light red; his FRONT view, the in-between of the turn;
  * his eye in extreme close-up (the Bass eye, with a pupil that narrows round what it sees
    and lids that can narrow);
  * his PROFILE, the mirror of hers: a fedora with a snap brim, a heavy brow, a long nose, a
    hard chin, a turned-up collar, and a red-irised eye.

All drawing is in frame px (1080 x 1920, y down), a pure function of its arguments.
"""
import math
from functools import lru_cache

import cairo

from engine import bass
from engine import paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED
from films.opposite_bass import world as B
from films.opposite_full import kit as K

W, H = K.W, K.H
INK, PAPER, AMBER = K.INK, K.PAPER, K.AMBER
NIGHT, STEEL, DEEP, SHUT = K.NIGHT, K.STEEL, K.DEEP, K.SHUT
k = K.k
fill = K.fill


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


# ============================================================================ the street, at night
def window_colour(r, tb, his_lit=True, her_lit=None):
    """The street windows at Bass time tb, on the night field: unlit ones cold; his always lit
    (in this film he never leaves his lit room); hers lit until the cord (or as forced)."""
    if r == B.HIS_WIN:
        return AMBER if his_lit else SHUT
    if r == B.HER_WIN:
        lit = (not B.her_light_off(tb)) if her_lit is None else her_lit
        return AMBER if lit else SHUT
    return SHUT


def street(c, tb, his_lit=True, her_lit=None, her=None, him=None, dark=0.0, moon=True, city=True):
    """The Bass cut's two facades on the night field at Bass time tb.

    her(c): draws her in her window (clipped to it) while it is lit; default: her_window.
    him(c): draws him in his window (clipped to it); None: nobody.
    dark (0..1): the street sinks toward ink (after her light goes out): the field, the city
    and the moon darken, the lit windows too."""
    field = lerp(NIGHT, INK, 0.78 * dark)
    fill(c, field)
    if city:
        K.skyline(c, color=lerp(STEEL, INK, 0.8 * dark))
    if moon and dark < 0.98:
        K.moon(c, K.MOON_E, color=lerp(PAPER, field, dark))
    for j, Bk in enumerate((B.LEFT_B, B.RIGHT_B)):
        bass.fill_polys(c, [bass.cut_rect(*Bk, seed=20 + j)], INK)
    lit_her = (not B.her_light_off(tb)) if her_lit is None else her_lit
    for r in B.LEFT_WIN + B.RIGHT_WIN:
        col = window_colour(r, tb, his_lit, her_lit)
        if dark > 0.0:
            col = lerp(col, INK, (0.85 if col == AMBER else 0.6) * dark)
        bass.fill_polys(c, [bass.cut_rect(*r, seed=int(r[0] + r[1]))], col)
    out = {}
    if lit_her:
        c.save()
        K.clip_rect(c, B.HER_WIN)
        out["her_hand"] = (her or (lambda cc: her_window(cc, tb)))(c)
        c.restore()
    if him is not None:
        c.save()
        K.clip_rect(c, B.HIS_WIN)
        out["him"] = him(c)
        c.restore()
    return out


# ============================================================================ her, in her window
def mouth_of(fig, st, pose, facing, gap=0.0):
    """Where draw_cutout puts the figure's mouth (figure px), before drawing it."""
    P = (st["pelvis"][0], st["pelvis"][1] + pose.crouch)
    m = pd._rot((36.0, -32.0), -pose.head)
    q = pd._rot((fig.neck[0] + m[0], fig.neck[1] - gap * 1.2 + m[1]), pose.lean)
    return (P[0] + facing * q[0], P[1] + q[1])


def hand_to_mouth(fig, st, pose, facing, w=1.0, side="near", dx=4.0, dy=30.0):
    """Put her hand over her mouth: the wrist just under and in front of her lips, the elbow
    down at her chest (IK), blended in by w."""
    if w <= 0.0:
        return
    m = mouth_of(fig, st, pose, facing)
    tgt = (m[0] + facing * dx, m[1] + dy)
    if w >= 1.0:
        pose.arms[side] = ("ik", tgt)
        return
    # blend: solve the arm at the target, convert to angles, lerp with the current angles
    lean = pose.lean
    sh = pd._rot(fig.shoulder, lean)
    S = (st["pelvis"][0] + facing * sh[0], st["pelvis"][1] + pose.crouch + sh[1])
    el, wr = pd.ik2(S, tgt, fig.upper, fig.fore, forward=-facing)
    a1 = math.degrees(math.atan2(facing * (el[0] - S[0]), el[1] - S[1])) - lean
    a2 = math.degrees(math.atan2(facing * (wr[0] - el[0]), wr[1] - el[1])) - lean - a1
    cur = pose.arms.get(side, ("ang", 0.0, 0.0))
    if cur[0] != "ang":
        pose.arms[side] = ("ik", tgt)
        return
    pose.arms[side] = B._toward(cur, a1, a2, w)


def her_pose_mouth(tb, mouth=1.0, flinch=0.0, tremble=0.0, t=0.0):
    """Her window performance at Bass time tb with her near hand at her mouth until she
    reaches for the cord; flinch (0..1) recoils her from the street; tremble shakes the hand
    on twos."""
    st, p = B.her_pose(tb)
    fig = B.win_fig(0)
    if flinch > 0.0:
        p.lean -= 9.0 * flinch
        p.crouch += 10.0 * flinch
        p.head -= 6.0 * flinch
        st = dict(st)
        P = st["pelvis"]
        st["pelvis"] = (P[0] - 14.0 * flinch, P[1])
    reach = k(tb, B.T_OFF + 0.1, 0.25, "out3")
    w = mouth * (1.0 - reach)
    if w > 0.0 and tb < B.T_OFF + 0.35:
        hand_to_mouth(fig, st, p, 1, w)
        if tremble > 0.0 and p.arms["near"][0] == "ik":
            tt = B.twos(t)
            x, y = p.arms["near"][1]
            p.arms["near"] = ("ik", (x + tremble * math.sin(tt * 53.0), y + tremble * math.cos(tt * 41.0)))
    return st, p


def her_window(c, tb, pose=None):
    """Her, small in her window (the Bass framing), posed by pose(tb) -> (st, pose).
    Returns her near hand in device space."""
    st, p = (pose or her_pose_mouth)(tb)
    c.save()
    K.place(c, B.HER_WIN[0] + 32.0, B.HER_WIN[3] + 6.0, B.WIN_FS)
    o = B.draw_cutout(c, B.win_fig(0), st, p, INK, facing=1, edge=AMBER, outline=AMBER, ow=10.0)
    hand = c.user_to_device(*o["hand_near"])
    c.restore()
    return hand


# ============================================================================ him
def mirror_state(st, ax):
    """A walker state mirrored about x = ax (to draw a performance facing the other way)."""
    P = st["pelvis"]
    out = dict(st)
    out["pelvis"] = (2.0 * ax - P[0], P[1])
    out["feet"] = {s: (2.0 * ax - f[0], f[1], f[2]) for s, f in st["feet"].items()}
    return out


def _far_away(name, centre):
    return (1.0e5, 0.0, 0.0) if name == "head" else (0.0, 0.0, 0.0)


def draw_man(c, fig, st, pose, facing, head_facing=None, eye=RED, eye_w=1.0, eye_scale=1.0, edge=AMBER, ow=7.0,
             sx=1.0, hide=()):
    """Him, as the Bass cut draws him (separate pieces of cut paper), but his head drawn by
    hand: it can face the other way from his body (a look back over his shoulder), and his
    eye catches the light in `eye` (None: no eye), eye_scale times its size (it must still
    read when he is small). sx (0..1) squeezes him across his own pelvis (the half-turned
    drawings of a turn). Returns draw_cutout's anchors (figure px) and eye_dev, his eye in
    device space."""
    hf = facing if head_facing is None else head_facing
    P = (st["pelvis"][0], st["pelvis"][1] + pose.crouch)
    c.save()
    if sx != 1.0:
        c.translate(P[0], 0.0)
        c.scale(sx, 1.0)
        c.translate(-P[0], 0.0)
    o = B.draw_cutout(c, fig, st, pose, INK, facing=facing, burst=_far_away, edge=edge, outline=edge, ow=ow,
                      hide=hide)
    # the head, about the neck (where the body put it), facing hf
    q = pd._rot(fig.neck, pose.lean)
    nk = (P[0] + facing * q[0], P[1] + q[1])
    c.save()
    c.translate(*nk)
    c.scale(hf, 1.0)
    c.rotate(math.radians(pose.lean))
    c.rotate(math.radians(-pose.head))
    c.translate(-fig.neck[0], -fig.neck[1])
    for poly, _ in fig.head:
        bass.fill_polys(c, [poly], INK)
    eye_pt = None
    if fig.eye is not None:
        (ex, ey), rx, ry = fig.eye
        eye_pt = c.user_to_device(ex, ey)
        if eye is not None and eye_w > 0.02:
            bass.fill_polys(c, [bass.draw.ellipse_pts((ex + 1.0, ey), rx * 1.25 * eye_scale,
                                                      ry * 1.35 * eye_w * eye_scale, n=20)], eye)
    c.restore()
    # the near arm again over his head (draw_cutout drew it before our head)
    if "near" not in hide and _arm_over_head(fig, pose):
        B.draw_cutout(c, fig, st, pose, INK, facing=facing, burst=_only_near_arm, edge=edge, outline=edge, ow=ow,
                      hide=("far",))
    o["eye_dev"] = eye_pt
    c.restore()
    return o


def _arm_over_head(fig, pose):
    spec = pose.arms.get("near", ("ang", 0.0, 0.0))
    return spec[0] == "ang" and abs(spec[1]) > 100.0


def _only_near_arm(name, centre):
    keep = name in ("upper_near", "fore_near", "hand_near")
    return (0.0, 0.0, 0.0) if keep else (1.0e5, 0.0, 0.0)


# --- his front: the in-between of a turn. Figure px, feet on y = 0, facing us.
def _front_parts():
    s = 911
    cut = pd._cut
    parts = []
    # legs and shoes, a gap of light between them
    for sg in (-1.0, 1.0):
        parts.append(bass.orient(bass.capsule_pts((sg * 21.0, -300.0), (sg * 22.0, -24.0), 19.0, 13.5, cap=8), True))
        parts.append(cut([(sg * 6.0, -26.0), (sg * 36.0, -28.0), (sg * 44.0, -14.0), (sg * 44.0, 0.0), (sg * 4.0, 0.0),
                          (sg * 4.0, -16.0)], s + (1 if sg > 0 else 2)))
    # the coat: broad shoulders, long to the knee, a little flare at the hem
    parts.append(cut([(-24.0, -588.0), (24.0, -588.0), (70.0, -566.0), (78.0, -540.0), (70.0, -420.0), (64.0, -300.0),
                      (76.0, -140.0), (-76.0, -140.0), (-64.0, -300.0), (-70.0, -420.0), (-78.0, -540.0),
                      (-70.0, -566.0)], s + 3))
    # the collar turned up: two points beside his jaw
    parts.append(cut([(-46.0, -572.0), (-34.0, -628.0), (-16.0, -600.0), (0.0, -590.0), (16.0, -600.0), (34.0, -628.0),
                      (46.0, -572.0)], s + 4))
    # the face under the brim
    parts.append(pd._ellipse((0.0, -636.0), 30.0, 40.0, s + 5))
    # the hat: the brim (snapped down at the front: it dips in the middle) and the crown
    parts.append(cut([(-86.0, -674.0), (-40.0, -680.0), (40.0, -680.0), (86.0, -674.0), (80.0, -664.0), (30.0, -662.0),
                      (0.0, -654.0), (-30.0, -662.0), (-80.0, -664.0)], s + 6))
    parts.append(cut([(-44.0, -676.0), (44.0, -676.0), (38.0, -712.0), (16.0, -720.0), (0.0, -710.0), (-16.0, -720.0),
                      (-38.0, -712.0)], s + 7))
    return [bass.orient(p, True) for p in parts]


@lru_cache(maxsize=1)
def front_parts():
    return _front_parts()


def front_arms(spread=0.0):
    """His arms hanging at his sides, a hand's breadth off the coat (spread opens them)."""
    out = []
    for sg in (-1.0, 1.0):
        sh = (sg * 66.0, -552.0)
        el = (sg * (84.0 + 8.0 * spread), -430.0)
        wr = (sg * (94.0 + 14.0 * spread), -318.0)
        out.append(bass.orient(bass.capsule_pts(sh, el, 17.0, 14.0, cap=8), True))
        out.append(bass.orient(bass.capsule_pts(el, wr, 14.0, 11.0, cap=8), True))
        out.append(bass.orient(bass.capsule_pts(wr, (wr[0] + sg * 3.0, wr[1] + 30.0), 12.5, 10.0, cap=8), True))
    return out


def draw_man_front(c, x, floor_y, s, sx=1.0, edge=AMBER, ow=7.0):
    """Him facing us (the frontal in-between of his turn), feet at (x, floor_y), scale s."""
    c.save()
    c.translate(x, floor_y)
    c.scale(s * sx, s)
    bass.fill_polys(c, front_parts(), INK)
    B.edged(c, front_arms(), INK, edge, ow)
    c.restore()


# ============================================================================ his eye, extreme close-up
EYE_C = B.EYE_C


def almond(c0, w, h, open_=1.0, low=0.0, n=48):
    """The Bass eye opening, with a lower lid too: open_ lowers the upper lid toward the
    lower one; low (0..1) raises the lower lid (the eye narrows from both sides)."""
    top, bot = [], []
    for i in range(n + 1):
        u = i / n
        x = c0[0] - w / 2 + w * u
        s = math.sin(math.pi * u) ** 0.85
        yb = c0[1] + h * 0.18 + h * 0.32 * s * (1.0 - low)
        yt = c0[1] + h * 0.18 - h * 0.68 * s * open_
        top.append((x, min(yt, yb - 0.5 * s)))
        bot.append((x, yb))
    return top + bot[::-1][1:-1]


def his_eye(c, open_, look, pupil=1.0, iris=RED, skin=AMBER, low=0.0, reflect=None, glint=True, mirror=True,
            fine=1.0):
    """His eye (the Bass eye, the mirror of hers): an ink band across the face, an almond cut
    out of it, a red iris and an ink pupil (pupil 1 = the Bass size). reflect(c, ic, pr): what
    he sees, drawn into the pupil (clipped to it; ic, pr = its centre and radius). fine > 1
    cuts the circles with more, smaller snips, for a shot that dives into the eye."""
    fill(c, skin)
    band = bass.cut_rect(-40.0, EYE_C[1] - 330.0, W + 40.0, EYE_C[1] + 330.0, seed=31, amp=3.0)
    bass.fill_polys(c, [band], INK)
    if open_ <= 0.02:
        return
    lid = almond(EYE_C, 860.0, 420.0, max(open_, 0.0), low)
    c.push_group()
    fill(c, PAPER)
    ic = (EYE_C[0] + look * 150.0 * (-1 if mirror else 1), EYE_C[1] - 6.0)
    bass.fill_polys(c, [bass.ring_pts(ic, 168.0, seed=33, n=int(56 * fine), amp=0.9 / fine)], iris)
    pr = 70.0 * pupil
    pupil_pts = bass.ring_pts(ic, pr, seed=35, n=int(40 * fine), amp=0.6 / fine)
    bass.fill_polys(c, [pupil_pts], INK)
    if reflect is not None:
        c.save()
        c.new_path()
        bass.draw.poly(c, pupil_pts)
        c.clip()
        reflect(c, ic, pr)
        c.restore()
    if glint:
        gc = (ic[0] + (-92.0 if mirror else 92.0), ic[1] - 80.0)
        bass.fill_polys(c, [bass.ring_pts(gc, 18.0, seed=36, n=int(24 * fine), amp=0.816 / fine)], PAPER)
    inside = c.pop_group()
    c.save()
    c.new_path()
    bass.draw.poly(c, lid)
    c.clip()
    c.set_source(inside)
    c.paint()
    c.restore()


# ============================================================================ her face (the mirror's left half)
def draw_her_face(c, wide=1.0, lid=1.0, look=0.0, pupil=1.0, field=AMBER):
    """B.draw_her_profile, with her pupil free to snap small (pupil 1 = the Bass size).
    Returns the pupil's centre."""
    fill(c, field)
    bass.fill_polys(c, [bass.orient(B.PROFILE, True)], INK)
    B.edged(c, [bass.orient(B.BOB, True)], INK, field, 9.0)
    c0 = (B.EYE_P[0], B.EYE_P[1] - 10.0 * (wide - 1.0))
    eye = B.almond(c0, 84.0, 40.0 * wide, lid)
    bass.fill_polys(c, [eye], PAPER)
    pc = (B.EYE_P[0] + 20.0 + 8.0 * look, B.EYE_P[1] - 4.0 + 6.0 * (1.0 - lid))
    c.save()
    c.new_path()
    bass.draw.poly(c, eye)
    c.clip()
    bass.fill_polys(c, [bass.ring_pts(pc, 11.0 * (2.0 - wide * 0.6) * pupil, seed=312, n=20, amp=0.2)], INK)
    c.restore()
    top = eye[: len(eye) // 2 + 1]
    for f, L, a in ((0.86, 54.0, -36.0), (0.94, 52.0, -17.0)):
        b = top[int(f * (len(top) - 1))]
        tip = (b[0] + math.cos(math.radians(a)) * L, b[1] + math.sin(math.radians(a)) * L)
        bass.fill_polys(c, [bass.orient([(b[0] - 8.0, b[1] + 3.0), (b[0] + 8.0, b[1] + 2.0), tip], True)], INK)
    return pc


# ============================================================================ his profile (the mirror)
# Drawn facing RIGHT in the same frame as her PROFILE (her eye at B.EYE_P); the mirror shot
# flips it to face her. Cut from one sheet like hers: the back of his head, the brow over a
# deep eye, a long straight nose, hard lips, a jutting chin, his throat; the hat is its own
# piece laid over his head and the collar its own piece round his neck, each with a hairline
# of light between it and him (as her bob has).
HIS_FACE = bass.scissor([
    (300, 1960), (300, 1250), (316, 1120), (340, 1000), (352, 940), (340, 880), (318, 800), (312, 720), (330, 640),
    (384, 560), (400, 500), (440, 460), (530, 440), (610, 452), (628, 500), (640, 550), (648, 566), (666, 586),
    (684, 602), (694, 618), (690, 632), (670, 650), (662, 676), (672, 696), (692, 716), (712, 746), (730, 782),
    (748, 814), (762, 836), (758, 852), (736, 860), (716, 866), (722, 884), (730, 900), (714, 912), (724, 926),
    (718, 944), (702, 956), (716, 988), (726, 1018), (712, 1048), (674, 1068), (636, 1084), (620, 1110), (628, 1150),
    (622, 1200), (700, 1300), (900, 1420), (1200, 1500), (1200, 1960)],
    seed=331, sag=0.8, amp=1.0, max_len=60.0, corner=34.0)
HIS_HAT = bass.scissor([
    (268, 510), (300, 538), (340, 554), (382, 568), (450, 574), (520, 578), (600, 582), (644, 586), (700, 596),
    (740, 608), (776, 621), (784, 614), (778, 610), (740, 592), (700, 578), (644, 566), (638, 520), (630, 456),
    (618, 396), (604, 360), (578, 348), (548, 362), (512, 355), (466, 342), (428, 346), (408, 378), (396, 444),
    (388, 510), (382, 548), (340, 534), (300, 520), (270, 506)],
    seed=332, sag=0.7, amp=0.8, max_len=60.0, corner=30.0)
HAT_BAND = ((392, 526), (640, 528))          # the top of his hat band: a cut across the crown
HAT_TIP = 784.0                              # the front of his brim (the nearest he comes to her)
HIS_COLLAR = bass.scissor([
    (292, 2600), (292, 1250), (290, 1040), (296, 960), (310, 930), (360, 936), (420, 960), (480, 996), (540, 1040),
    (590, 1080), (624, 1114), (660, 1190), (720, 1290), (800, 1390), (950, 1480), (1210, 1560), (1210, 2600)],
    seed=333, sag=0.7, amp=0.8, max_len=60.0, corner=34.0)
HIS_EYE = (598.0, 668.0)


def draw_his_profile(c, look=1.0, lid=0.8, wide=1.0, low=0.0, glint=True, field=AMBER, fill_field=True):
    """His face facing right in her profile's frame (flip it to face her): field, face, collar,
    hat, the band cut, and the eye: an almond under his brow, the iris red."""
    if fill_field:
        fill(c, field)
    bass.fill_polys(c, [bass.orient(HIS_FACE, True)], INK)
    B.edged(c, [bass.orient(HIS_COLLAR, True)], INK, field, 8.0)
    B.edged(c, [bass.orient(HIS_HAT, True)], INK, field, 8.0)
    c.save()
    c.set_source_rgb(*field)
    c.set_line_width(5.0)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(*HAT_BAND[0])
    c.line_to(*HAT_BAND[1])
    c.stroke()
    c.restore()
    eye = almond(HIS_EYE, 86.0, 38.0 * wide, lid, low)
    bass.fill_polys(c, [eye], PAPER)
    c.save()
    c.new_path()
    bass.draw.poly(c, eye)
    c.clip()
    ic = (HIS_EYE[0] + 12.0 + 10.0 * look, HIS_EYE[1] - 3.0)
    bass.fill_polys(c, [bass.ring_pts(ic, 17.0, seed=334, n=28, amp=0.3)], RED)
    bass.fill_polys(c, [bass.ring_pts(ic, 7.0, seed=335, n=18, amp=0.2)], INK)
    if glint:
        bass.fill_polys(c, [bass.ring_pts((ic[0] + 7.0, ic[1] - 7.0), 2.8, seed=336, n=10, amp=0.1)], PAPER)
    c.restore()
    return (ic[0], ic[1])
