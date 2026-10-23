"""s05 · SEEN (52-66): he turns; his eye; his look crosses the street and rings her window;
the mirror; the arm; lights off.

  0.00  HIS WINDOW, close. His back to the street, head bowed over what he has done. Paper
        ripples out of his head: he listens. His head comes round first (a look back over his
        shoulder), then his body follows, on twos, through a front view. His eye catches red.
  2.00  HIS EYE. A hooded stare springs wide open on her; her lit window is in his pupil; the
        pupil snaps small round it.
  3.50  THE LOOK. The wide night street: his red sight line zips to her window (0.3 s); the
        red marker ring draws round it (0.4 s). She flinches. The frame glides in on her.
  5.50  THE MIRROR. A red line splits the frame; her profile (hand at her mouth) slides in
        from the left, his (new: hat, brow, nose, chin, collar, red eye) from the right, eyes
        level. His dots cross the split into her eye. The halves press in on her heartbeat.
  8.00  THE ARM. The Bass arm shot on the night field (tb = 18.5 + (t - 8)): his jagged red
        arm grows across the street into her ringed window and snaps back; he steps out.
 11.00  LIGHTS OFF. The Bass off shot on the night field (tb = 21.5 + (t - 11)): in on her
        window, the cord, the negative flash; black. The dark street comes up out of the black;
        the red ring round her dark window is the brightest thing left, throbbing with her heart.
"""
import math

import cairo

from engine import bass
from engine.core import clamp, ease, lerp
from engine.palette import RED
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import gaze as G
from films.opposite_full import kit as K

INK, PAPER, AMBER, NIGHT = K.INK, K.PAPER, K.AMBER, K.NIGHT
W, H = K.W, K.H
k = K.k
twos = K.twos

# ----------------------------------------------------------------------------- beats (scene s)
T_LISTEN = 4 / 12.0        # paper ripples out of his head: he listens (beats of the turn fall on twos)
T_HEAD = 11 / 12.0         # his head comes round first: a look back over his shoulder
T_TURN = 14 / 12.0         # his body follows through two front drawings (on twos)
T_FACED = 16 / 12.0        # facing her
T_EYE = 2.0                # cut: his eye
T_OPEN = 2.15              # it springs open on her
T_PUPIL = 2.75             # the pupil snaps small round her window (stinger)
T_WIDE = 3.5               # cut: the wide street
T_LOOK = 3.6               # his red sight line zips across (0.3 s)
T_RING = 3.95              # the red marker ring draws round her window (0.4 s)
T_FLINCH = 4.35            # she flinches
T_MIRROR = 5.5             # the red split
T_PANELS = 5.62            # her half and his half slide in
T_DOTS = 6.05              # his dots cross the split into her eye
T_PRESS = (6.0, 6.5, 7.0, 7.5)     # the halves press in, on her heartbeat
T_ARM = 8.0                # the Bass arm shot: tb = 18.5 + (t - 8.0)
T_GROW = B.T_GROW - 10.5   # 8.8: his arm grows
T_GRAB = 9.5               # its claw in her window: the frame jumps in
T_RETRACT = B.T_RETRACT - 10.5     # 10.4: it snaps back
T_GONE = B.T_GONE - 10.5   # 10.75: he has stepped out of his window
T_OFF = 11.0               # the Bass off shot: tb = 21.5 + (t - 11.0)
T_PULL = B.T_PULL - 10.5   # 11.35: the cord; the negative flash
T_DARK = T_PULL + 2 / 24.0
T_HEART = 11.7             # the ring throbs with her heart in the dark
HEART_BPM = 132.0

TB = 10.5                  # beats 5 and 6: Bass time = scene time + TB
RING_C = (B.centre(B.HER_WIN)[0], B.centre(B.HER_WIN)[1])
RING_R = (101.0, 127.0)
HIS_X = B.HIS_WIN[0] + 92.0        # his feet in his window (the Bass place)
FLOOR = B.HIS_WIN[3] + 6.0


def cam(c, z, cx, cy):
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-cx, -cy)


def to_frame(c, dev):
    """Device point -> frame px (in the scene's unmoved screen context)."""
    return c.device_to_user(*dev)


# ============================================================================ 1. he turns
def his_turn_pose(t):
    """(st, pose, facing, head_facing, front) of his turn at scene time t, on twos: front is
    None, or the width of his front view (the in-between drawings)."""
    tt = twos(t)
    st, p = B.alone_pose(18.3 + 0.25 * tt)
    breathe = math.sin(2.0 * math.pi * tt / 2.6)
    if tt < T_TURN:
        # his back to the street: the performance mirrored to face into his room
        st = G.mirror_state(st, st["pelvis"][0])
        lift = k(tt, T_LISTEN, 0.3, "out3")
        p.head = lerp(-24.0, -6.0, lift)
        p.lean += 2.0 * (1.0 - lift) + 0.8 * breathe
        hf = -1 if tt >= T_HEAD else 1
        if hf < 0:
            p.head = 4.0
        return st, p, 1, hf, None
    if tt < T_FACED:                              # two front drawings: turning through, then square
        return st, p, -1, -1, (0.86 if tt < T_TURN + 1 / 12.0 else 1.0)
    # facing her: an overshoot toward her, then still; a slow lean in
    p.lean += 6.0 * (k(tt, T_FACED, 0.12, "out") - k(tt, T_FACED + 0.12, 0.3, "inout")) + 2.5 * k(tt, 1.5, 0.5)
    p.head = -4.0 * k(tt, 1.45, 0.4)
    return st, p, -1, -1, None


T_JUMP = 1.5               # the frame jumps in on him, on the beat
TURN_CAM = ((6.0, 738.0, 600.0), (6.45, 744.0, 596.0), (9.2, 754.0, 598.0))    # (zoom, centre x, y)


def draw_turn(c, t):
    u = k(t, 0.0, T_JUMP, "inout")
    j = k(t, T_JUMP, 0.07, "out5")
    (z0, x0, y0), (z1, x1, y1), (z2, x2, y2) = TURN_CAM
    z, cx, cy = lerp(z0, z1, u), lerp(x0, x1, u), lerp(y0, y1, u)
    z, cx, cy = lerp(z, z2 * (1.0 + 0.02 * k(t, T_JUMP, 0.5, "out")), j), lerp(cx, x2, j), lerp(cy, y2, j)
    c.save()
    cam(c, z, cx, cy)
    fig = B.figs()[1]
    st, p, facing, hf, front = his_turn_pose(t)
    anchors = {}

    def him(cc):
        cc.save()
        K.place(cc, HIS_X, FLOOR, B.WIN_FS)
        if front is not None:
            G.draw_man_front(cc, st["pelvis"][0], 0.0, 1.0, sx=front)
            anchors["head"] = cc.user_to_device(st["pelvis"][0], -640.0)
        else:
            o = G.draw_man(cc, fig, st, p, facing, head_facing=hf, eye=RED if hf < 0 else None,
                           hide=("near", "far"))
            anchors["head"] = cc.user_to_device(*o["head"])
        cc.restore()
    G.street(c, 18.6, him=him)
    c.restore()
    # he listens: paper ripples out of his head
    if "head" in anchors and T_LISTEN <= t < T_HEAD + 0.2:
        h = to_frame(c, anchors["head"])
        K.ripple(c, (h[0] - 10.0, h[1] - 40.0), t, T_LISTEN, PAPER, n=3, every=0.12, life=0.62, r0=24.0, r1=210.0,
                 width=8.0, seed=5)


# ============================================================================ 2. his eye
def reflect_her(tb):
    """Her lit window, small in his pupil."""
    def fn(c, ic, pr):
        w = 96.0
        h = w * (B.HER_WIN[3] - B.HER_WIN[1]) / (B.HER_WIN[2] - B.HER_WIN[0])
        r = (ic[0] - w / 2 - 3.0, ic[1] - h / 2 - 2.0, ic[0] + w / 2 - 3.0, ic[1] + h / 2 - 2.0)
        s = w / (B.HER_WIN[2] - B.HER_WIN[0])
        c.save()
        c.translate(r[0], r[1])
        c.scale(s, s)
        c.translate(-B.HER_WIN[0], -B.HER_WIN[1])
        bass.fill_polys(c, [bass.cut_rect(*B.HER_WIN, seed=int(B.HER_WIN[0] + B.HER_WIN[1]), amp=0.6)], AMBER)
        c.save()
        K.clip_rect(c, B.HER_WIN)
        G.her_window(c, tb)
        c.restore()
        c.restore()
    return fn


def draw_eye(c, t):
    z = lerp(1.0, 1.07, k(t, T_EYE, 1.5, "inout"))
    open_ = lerp(0.36, 1.0, k(t, T_OPEN, 0.14, "outback"))
    pupil = lerp(1.86, 1.2, k(t, T_PUPIL, 0.12, "outback"))
    look = 0.22 + 0.02 * math.sin(6.0 * t) * k(t, T_PUPIL + 0.2, 0.3)
    c.save()
    cam(c, z, 540.0, 960.0)
    G.his_eye(c, open_, look, pupil=pupil, reflect=reflect_her(18.4))
    c.restore()


# ============================================================================ 3. the look
def her_mark_pose(t):
    flinch = k(twos(t), T_FLINCH, 0.1, "outback") * (1.0 - 0.35 * k(twos(t), T_FLINCH + 0.25, 0.5))

    def fn(tb):
        return G.her_pose_mouth(tb, flinch=flinch, tremble=4.0, t=t)
    return fn


def wide_cam(t):
    u = k(t, T_FLINCH + 0.05, 1.05, "inout3")
    return lerp(1.28, 1.62, u), lerp(566.0, 374.0, u), lerp(884.0, 1062.0, u)


def his_window_figure(tb, eye_scale=2.4, anchors=None):
    """Him at his window facing her (the Bass place and performance) with a red eye."""
    def fn(cc):
        st, p = B.alone_pose(tb)
        cc.save()
        K.place(cc, HIS_X, FLOOR, B.WIN_FS)
        o = G.draw_man(cc, B.win_fig(1), st, p, -1, eye=RED, eye_scale=eye_scale, ow=10.0)
        if anchors is not None:
            anchors["eye"] = o["eye_dev"]
            anchors["shoulder"] = cc.user_to_device(*o["shoulder_near"])
        cc.restore()
    return fn


def draw_look(c, t, z=None):
    zz, cx, cy = wide_cam(t)
    tb = 18.3 + 0.12 * (t - T_WIDE)
    c.save()
    cam(c, zz, cx, cy)
    anchors = {}
    out = G.street(c, tb, her=lambda cc: G.her_window(cc, tb, her_mark_pose(t)),
                   him=his_window_figure(tb, anchors=anchors))
    eye = c.device_to_user(*anchors["eye"])
    her = c.device_to_user(*out["her_hand"])
    target = (her[0] + 4.0, her[1] - 6.0)
    K.sight_line(c, eye, target, t, T_LOOK, RED, dur=0.3, r=8.5, gap=27.0, head=31.0, march=34.0, seed=3)
    K.marker_ring(c, RING_C, RING_R[0], RING_R[1], k(t, T_RING, 0.4, "inout"), RED, width=15.0, seed=2)
    c.restore()


# ============================================================================ 4. the mirror
EYE_Y = 724.0
HER_PANEL = bass.orient(bass.cut_rect(-40.0, -40.0, 541.0, H + 40.0, seed=43, amp=1.2), True)
HIS_PANEL = bass.orient(bass.cut_rect(539.0, -40.0, W + 40.0, H + 40.0, seed=44, amp=1.2), True)
T_SEEN = T_DOTS + 0.45     # his dots reach her eye: her pupil snaps small


def heart_kick(t, beats):
    """0..1 thump of a heartbeat (lub, and a softer dub 0.16 s later) at each of `beats`."""
    out = 0.0
    for t0 in beats:
        out = max(out, bass._kick(t - t0), 0.6 * bass._kick(t - t0 - 0.16))
    return out


def mirror_layout(t):
    """(scale, her offset x, his offset x): the halves press in on each heartbeat."""
    press = sum(k(t, t0, 0.12, "outback") for t0 in T_PRESS) / len(T_PRESS)
    s = lerp(0.86, 0.97, press)
    gap = lerp(56.0, 18.0, press)                    # her nose, his brim, to the split
    her_ox = 540.0 - gap - 742.0 * s
    his_ox = 540.0 - gap + 6.0 - G.HAT_TIP * s
    return s, her_ox, his_ox


def _panel(c, half, panel, dx):
    """Clip to a half of the frame and to its panel, slid by dx."""
    c.new_path()
    c.rectangle(*half)
    c.clip()
    c.translate(dx, 0.0)
    c.new_path()
    bass.draw.poly(c, panel)
    c.clip()


def draw_her_half(c, t, s, ox, slide):
    oy = EYE_Y - B.EYE_P[1] * s
    c.save()
    _panel(c, (-10.0, -10.0, 550.0, H + 20.0), HER_PANEL, -slide)
    c.translate(ox, oy)
    c.scale(s, s)
    pupil = lerp(1.0, 0.55, k(t, T_SEEN, 0.1, "outback"))
    pc = G.draw_her_face(c, wide=1.7, lid=1.0, look=1.0, pupil=pupil)
    bass.fill_polys(c, [bass.cut_rect(300.0, 1940.0, 1400.0, 2600.0, seed=41, amp=0.5)], INK)
    tt = twos(t)
    wr = (B.W_MOUTH[0] + 2.5 * math.sin(tt * 53.0), B.W_MOUTH[1] + 2.5 * math.cos(tt * 41.0))
    polys, cuts = B.cu_hand(wr, B.A_MOUTH + 1.5 * math.sin(tt * 37.0), 0.0)
    B.draw_arm(c, wr, B.E_MOUTH, polys)
    B.cut_lines(c, cuts)
    dev = c.user_to_device(*pc)
    c.restore()
    return c.device_to_user(*dev)


def draw_his_half(c, t, s, ox, slide):
    oy = EYE_Y - G.HIS_EYE[1] * s
    c.save()
    _panel(c, (530.0, -10.0, 560.0, H + 20.0), HIS_PANEL, slide)
    c.translate(W, 0.0)
    c.scale(-1.0, 1.0)
    c.translate(ox, oy)
    c.scale(s, s)
    ic = G.draw_his_profile(c, look=1.0, lid=0.82)
    bass.fill_polys(c, [bass.cut_rect(300.0, 1940.0, 1400.0, 2600.0, seed=42, amp=0.5)], INK)
    dev = c.user_to_device(*ic)
    c.restore()
    return c.device_to_user(*dev)


def draw_mirror(c, t):
    s, her_ox, his_ox = mirror_layout(t)
    u = k(t, T_PANELS, 0.3, "outback")
    if u < 1.0:
        draw_look(c, t)
    her_eye = draw_her_half(c, t, s, her_ox, 600.0 * (1.0 - u))
    his_eye = draw_his_half(c, t, s, his_ox, 600.0 * (1.0 - u))
    # the split: a red line cut down the frame, throbbing with her heart
    cut = k(t, T_MIRROR, 0.12, "out3")
    wd = 16.0 * (1.0 + 0.6 * heart_kick(t, T_PRESS))
    bass.line_band(c, [(540.0, -30.0), (540.0, H + 30.0)], RED, width=wd, u=cut, seed=7)
    K.sight_line(c, (his_eye[0] - 24.0, his_eye[1]), (her_eye[0] + 16.0, her_eye[1]), t, T_DOTS, RED, dur=0.45,
                 r=9.5, gap=31.0, head=36.0, march=40.0, seed=4)


# ============================================================================ 5. the arm (Bass, ported)
def draw_arm(c, t):
    tb = t + TB
    shake = 3.5 * k(tb, B.T_GROW + 0.6, 0.1) * (1.0 - k(tb, B.T_RETRACT, 0.12))
    jump = k(t, T_GRAB, 0.07, "out5") * (1.0 - k(t, T_RETRACT, 0.1, "out5"))
    tt = twos(tb)
    c.save()
    cam(c, lerp(1.0, 1.14, jump), lerp(540.0, 520.0, jump), lerp(960.0, 900.0, jump))
    c.translate(shake * math.sin(tt * 61.0), shake * math.cos(tt * 47.0))
    anchors = {}
    him = his_alone(tb, anchors)
    G.street(c, tb, her=lambda cc: G.her_window(cc, tb), him=him)
    K.marker_ring(c, RING_C, RING_R[0], RING_R[1], 1.0, RED, width=15.0, seed=2)
    grow = k(tb, B.T_GROW, 0.7, "out3") * (1.0 - k(tb, B.T_RETRACT, 0.12, "in3"))
    if grow > 0 and "shoulder" in anchors:
        base, tip = B.arm_points(c.device_to_user(*anchors["shoulder"]))
        c.save()
        c.rectangle(-4000.0, -4000.0, base[0] + 1.0 + 4000.0, 8000.0)
        c.clip()
        bass.jagged_arm(c, base, tip, RED, width=38.0, grow=grow, jags=5, jag=1.0, claw=0.7, seed=4)
        c.restore()
        if tb < B.T_GONE:                      # his body over the root of the arm
            c.save()
            K.clip_rect(c, B.HIS_WIN)
            his_alone(tb, {})(c)
            c.restore()
    c.restore()


def his_alone(tb, anchors):
    """B.draw_him_alone with his red eye: while the red arm is out it is his arm."""
    def fn(cc):
        if tb >= B.T_GONE:
            return
        st, p = B.alone_pose(tb)
        cc.save()
        K.place(cc, B.HIS_WIN[0] + 92.0 + 260.0 * k(tb, B.T_RETRACT + 0.12, B.T_GONE - B.T_RETRACT - 0.14, "in3"),
                B.HIS_WIN[3] + 6.0, B.WIN_FS)
        o = G.draw_man(cc, B.win_fig(1), st, p, -1, eye=RED, eye_scale=2.4, ow=10.0,
                       hide=("near",) if B.red_arm_out(tb) else ())
        anchors["shoulder"] = cc.user_to_device(*o["shoulder_near"])
        cc.restore()
    return fn


# ============================================================================ 6. lights off (Bass, ported)
def ring_throb(t):
    """Her heart in the ring: (scale, width) on each lub-dub."""
    if t < T_HEART:
        return 1.0, 15.0
    beat = 60.0 / HEART_BPM
    ph = (t - T_HEART) % beat
    kick = max(bass._kick(ph), 0.6 * bass._kick(ph - 0.16))
    return 1.0 + 0.045 * kick, 15.0 * (1.0 + 0.55 * kick)


T_UP = 21.0 + 8 / 12.0     # (Bass time, on twos) her hand comes up past her face: one drawing
T_CORD = 21.75             # ... at the cord, arm straight up
T_TUG = 21.0 + 10 / 12.0   # ... she pulls it (the drawing before the light goes)


def _step(tb):
    """Bass time -> its twos drawing number (robust to float error)."""
    return int(round(twos(tb) * 12.0))


def her_cord_pose(tb, head=-10.0):
    """Up to the cord and pull, on twos: she straightens up off the glass to reach; the hand
    leaves her mouth, comes up past her face, takes the cord, pulls. Her far hand drops from
    her chest to her side as she goes (a snap, no in-between)."""
    tq = twos(tb)
    n = _step(tb)
    st, p = G.her_pose_mouth(tb) if n < _step(T_UP) - 1 else B.her_pose(tq)
    fig = B.win_fig(0)
    rise = k(tq, T_UP - 1 / 12.0, 0.25, "out3")
    p.lean = lerp(p.lean, 7.0, rise)
    p.head = lerp(p.head, head, rise)
    if n < _step(T_UP) - 1:
        return st, p
    p.arms["far"] = ("ang", -3.0 - p.lean, 16.0)     # drops to her side (angles are from the torso)
    if n < _step(T_UP):
        G.hand_to_mouth(fig, st, p, 1, 1.0)
    elif n < _step(T_CORD):
        m = G.mouth_of(fig, st, p, 1)
        p.arms["near"] = ("ik", (m[0] + 10.0, m[1] - 150.0))
    elif n < _step(T_TUG):
        p.arms["near"] = ("ang", -184.0, 4.0)
    else:
        p.arms["near"] = ("ang", -204.0, 22.0)
    return st, p


def draw_off(c, t):
    tb = t + TB
    p = k(tb, B.T_OFF, 0.35, "out5")
    z = lerp(1.0, 3.3, p)
    back = k(t, 12.1, 1.9, "inout")                   # out of the dark: a slow pull back
    z *= lerp(1.0, 0.68, back)
    cc = (B.centre(B.HER_WIN)[0], B.centre(B.HER_WIN)[1] - 10.0)
    dark_t = T_DARK
    dark = 0.0
    if t >= dark_t:
        dark = 1.0 - 0.3 * k(t, dark_t + 0.25, 0.9, "inout")
    c.save()
    c.translate(lerp(cc[0], 540.0, p), lerp(cc[1], 960.0, p))
    c.scale(z, z)
    c.translate(-cc[0], -cc[1])
    out = G.street(c, tb, her=lambda q: G.her_window(q, tb, her_cord_pose), dark=dark, moon=dark < 0.5)
    if not B.her_light_off(tb):
        x0, y0 = cord_end()
        hand = out.get("her_hand")
        end = c.device_to_user(*hand) if _step(tb) >= _step(T_CORD) and hand else (x0, y0)
        c.save()
        c.set_source_rgb(*INK)
        c.set_line_width(2.0)
        c.move_to(x0, B.HER_WIN[1])
        c.line_to(*end)
        c.stroke()
        c.restore()
    sc, wd = ring_throb(t)
    c.save()
    c.translate(*RING_C)
    c.scale(sc, sc)
    c.translate(-RING_C[0], -RING_C[1])
    K.marker_ring(c, RING_C, RING_R[0], RING_R[1], 1.0, RED, width=wd / sc, seed=2)
    c.restore()
    c.restore()
    if T_PULL <= t < T_DARK:
        c.save()
        c.set_operator(cairo.OPERATOR_DIFFERENCE)
        K.fill(c, (1.0, 1.0, 1.0))
        c.set_operator(cairo.OPERATOR_HSL_SATURATION)
        K.fill(c, (0.5, 0.5, 0.5))
        c.restore()


_CORD = {}


def cord_end():
    if "end" not in _CORD:
        surf = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, None)
        _CORD["end"] = G.her_window(cairo.Context(surf), T_CORD, her_cord_pose)
    return _CORD["end"]


# ============================================================================ the scene
def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        if t < T_EYE:
            draw_turn(c, t)
        elif t < T_WIDE:
            draw_eye(c, t)
        elif t < T_MIRROR:
            draw_look(c, t)
        elif t < T_ARM:
            draw_mirror(c, t)
        elif t < T_OFF:
            draw_arm(c, t)
        else:
            draw_off(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    return [
        Cue(0.0, "a low string swell under his breath", gain_db=-10, dur=2.0),
        Cue(T_LISTEN, "he listens: a held breath, a faint high harmonic", gain_db=-14),
        Cue(T_HEAD, "his head turns: coat collar rustle", gain_db=-16),
        Cue(T_TURN, "he turns: a low cello slide", gain_db=-12),
        Cue(T_OPEN, "his eye opens: a dry tick", gain_db=-12),
        Cue(T_PUPIL, "the pupil snaps small: stinger", gain_db=-5),
        Cue(T_LOOK, "his look zips across the street: zip", gain_db=-8),
        Cue(T_RING, "marker squeak round her window", gain_db=-9),
        Cue(T_RING + 0.05, "a low brass braam", gain_db=-5, dur=1.4),
        Cue(T_FLINCH, "her gasp, stifled", gain_db=-12),
        Cue(T_MIRROR, "the red split: a paper slash", gain_db=-8),
        Cue(T_PANELS, "the halves slam in: a low thud", gain_db=-8),
        Cue(T_PRESS[0], "her heartbeat under a sustained dissonance (one thud per press)", gain_db=-6,
            dur=T_ARM - T_PRESS[0]),
        Cue(T_DOTS, "his dots cross the split: a rising glass harmonic", gain_db=-12),
        Cue(T_GROW, "his arm grows across the street: braam", gain_db=-4),
        Cue(T_GRAB, "the claw at her window: string stab", gain_db=-6),
        Cue(T_RETRACT, "it snaps back: whip", gain_db=-8),
        Cue(T_PULL, "the light cord: click, all dark", gain_db=-6),
        Cue(T_HEART, "her heartbeat alone in the dark", gain_db=-8, dur=14.0 - T_HEART),
    ]
