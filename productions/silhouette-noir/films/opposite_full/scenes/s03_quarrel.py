"""s03 · QUARREL (26-40): along her look into his window; the quarrel; the knife ringed; her
eye; his hand takes the knife.

  0.00  ALONG HER LOOK. The night street; her paper dots run from her eye to his lit window.
        We fly along them: the dots rush past, huge, and his amber window grows until it is
        the frame. Inside it the room opens up (it is further away than the glass).
  1.50  THE QUARREL, in his room (his_room's stage: the phone corner, the lamp, the counter
        with THE knife on it). Both cut-outs argue (mocap 80_48); red zigzags fly mouth to
        face on the shouts; the frame jumps closer on the beat.
  3.50  THE RED MARKER RING draws round the knife (0.4 s).
  5.50  He stops shouting. His RED sight line goes to the knife and holds; the frame jumps
        back to show what he is looking at.
  6.25  She winds up; 6.50 she slaps him: a paper starburst at his cheek, his head snaps
        back, the frame jumps in. 6.85 she turns her back on him.
  8.00  HER EYE (the Bass eye shot at tb = 8.5 + (t - 8)): his room in her iris, the red ring
        in it. She blinks; 9.50 we dive into the reflection.
 10.00  THE KNIFE INSERT, low along the counter top: the knife huge in its ring, beyond it,
        small, her back and him behind her. 10.45 he turns and walks out of the picture.
 11.50  His hand comes in from above, a claw; 11.75 it lands on the handle; 11.95 the
        fingers close round it.
 12.20  The knife lifts out of the frame; the ring snaps in two and its arcs fall away.
 13.00  The empty counter. 13.30 she turns round, toward where he went. Cut.
"""
import math
from functools import lru_cache

from engine import bass, mocap as mc
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import his_room as HR
from films.opposite_full import kit as K

INK, PAPER, AMBER, RED = K.INK, K.PAPER, K.AMBER, B.RED
W, H = K.W, K.H
k = K.k
twos = K.twos

# ----------------------------------------------------------------------------- beats (scene s)
T_LAND = 1.5               # the window has become the frame: the room
SHOUTS = ((1.625, "man"), (2.125, "vic"), (2.375, "man"), (2.875, "vic"), (3.125, "man"), (3.875, "vic"),
          (4.125, "man"), (4.375, "vic"), (4.875, "man"), (5.125, "vic"), (5.875, "vic"), (6.125, "vic"))
T_RING = 3.5               # the red marker ring round the knife (0.4 s)
T_LOOK = 5.5               # his red look at the knife, held
T_LOOK_OFF = 6.42          # ... knocked off by the slap
T_WIND = 6.17              # she winds up
T_SLAP = 6.5               # the slap
T_TURN = 6.85              # she turns her back on him
T_LOOK_AGAIN = 7.4         # his head goes down to the knife again
T_EYE = 8.0                # cut: her eye (Bass tb = 8.5 + (t - 8))
TB_EYE = 8.5
T_BLINK = 9.12
T_DIVE = 9.5               # into the reflection
T_INSERT = 10.0            # cut: the knife insert
T_EXIT = 10.45             # he turns and walks out of the picture
T_HAND = 11.5              # his hand comes into frame
T_GRIP = 11.75             # ... lands on the handle
T_CLOSE = 11.95            # ... the fingers closed round it
T_LIFT = 12.2              # the knife lifts; the ring snaps
T_EMPTY = 13.0             # the empty counter
T_SHE_TURNS = 13.3         # she turns round

# the frame jumps closer on the beat: (t, zoom, stage centre x, y)
JUMPS = ((T_LAND, 1.00, 600.0, 1080.0), (2.0, 1.07, 616.0, 1062.0), (2.5, 1.14, 632.0, 1046.0),
         (3.0, 1.21, 650.0, 1030.0), (4.0, 1.30, 606.0, 1004.0), (4.5, 1.38, 628.0, 990.0),
         (5.0, 1.47, 596.0, 978.0), (T_LOOK, 1.16, 652.0, 1030.0), (T_SLAP, 1.55, 500.0, 940.0),
         (7.0, 1.28, 632.0, 1020.0))


# ============================================================================ the couple
D = (B.VIC_X - B.MAN_X) / HR.FS          # 300 figure units between them on the stage


@lru_cache(maxsize=1)
def _perfs():
    man_p, vic_p = HR.quarrel_perfs()
    her, man, vic = B.figs()
    C = mc.Clip.load
    back = mc.Performance(vic, [mc.Seg(C("80_48"), 8.6, 9.4, at=T_TURN, speed=0.22)], facing=1, near="Right")
    walk = mc.Performance(man, [mc.Seg(C("104_02"), 1.0, 4.0, at=T_EXIT + 0.08, speed=1.15)], facing=-1, near="Left")
    return man_p, vic_p, back, walk


def _slap_snap(tt):
    """His head, snapped back by the slap (on the drawing after the blow), slowly coming round."""
    if tt < T_SLAP + 0.08:
        return 0.0
    return lerp(1.0, 0.3, k(tt, T_SLAP + 0.12, 0.7, "out"))


def man_state(t):
    """(st, pose, facing) of him at scene time t (on twos), placed units."""
    tt = twos(t)
    man_p, _, _, walk = _perfs()
    if tt >= T_EXIT:
        st, p = walk(tt)
        x0 = man_p(T_EXIT - 0.01)[0]["pelvis"][0]
        st = HR.shifted(st, x0 - walk(T_EXIT + 0.08)[0]["pelvis"][0])
        return st, p, -1
    st, p = man_p(tt)
    w = k(tt, T_LOOK - 0.17, 0.17, "out")
    p.head = lerp(p.head, -15.0, w)                  # down, at the knife
    p.head -= 9.0 * k(tt, T_LOOK_AGAIN, 0.25, "inout")     # ... and once she has turned away, again
    sn = _slap_snap(tt)
    if sn > 0.0:
        p.head += 30.0 * sn
        p.lean -= 7.0 * sn
        st = HR.shifted(st, -10.0 * sn)
    return st, p, 1


def _cheek(st, p):
    man = B.figs()[1]
    return HR.cheek_point(man, st, p, 1, 0.0)


SLAP_WRIST = (30.0, 10.0)        # her wrist at the blow, from his cheek (her palm on it)


@lru_cache(maxsize=1)
def _slap_target():
    """Her wrist at the blow (in her placed units): his cheek just before it lands."""
    st_m, p_m, _ = man_state(T_SLAP - 0.01)
    ch = _cheek(st_m, p_m)
    return (ch[0] - D + SLAP_WRIST[0], ch[1] + SLAP_WRIST[1])


@lru_cache(maxsize=1)
def _slap_step():
    """How far she must step in for her hand to reach his cheek (placed units, < 0: toward him)."""
    vic = B.figs()[2]
    _, vic_p, _, _ = _perfs()
    st, p = vic_p(T_SLAP)
    sh = (st["pelvis"][0] - vic.shoulder[0], st["pelvis"][1] + p.crouch + vic.shoulder[1])
    need = math.dist(sh, _slap_target()) - 0.93 * (vic.upper + vic.fore)
    return -max(0.0, need)


def vic_state(t):
    """(st, pose, facing, squeeze) of her at scene time t (on twos), placed units. squeeze
    (0..1) narrows her across her pelvis: the drawing between two facings."""
    tt = twos(t)
    _, vic_p, back, _ = _perfs()
    step = _slap_step()
    if tt < T_TURN:
        st, p = vic_p(tt)
        dx = step * k(tt, T_WIND, 0.25, "out")
        st = HR.shifted(st, dx)
        if tt >= T_WIND:
            # the slap: wind up (the hand back by her ear), strike (on the beat), follow through, drop
            if tt < T_SLAP - 0.09:
                w = k(tt, T_WIND, 0.16, "out")
                p.arms["near"] = B._toward(p.arms["near"], 162.0, 118.0, w)
            elif tt < T_SLAP:
                p.arms["near"] = ("ang", 118.0, 34.0)
            elif tt < T_SLAP + 0.08:
                p.arms["near"] = ("ik", _slap_target())
            elif tt < T_SLAP + 0.16:
                p.arms["near"] = ("ang", 26.0, 2.0)                    # swung on through, down past him
            else:
                w = k(tt, T_SLAP + 0.16, 0.16, "out")
                p.arms["near"] = B._toward(("ang", 26.0, 2.0), 10.0, 18.0, w)
            p.lean += 7.0 * k(tt, T_WIND, 0.2) * (1.0 - k(tt, T_SLAP + 0.1, 0.3))     # into the blow
        sq = 0.55 if tt >= T_TURN - 1 / 12.0 else 0.0
        return st, p, -1, sq
    st, p = back(tt)
    x_turn = HR.shifted(vic_p(T_TURN - 0.01)[0], step)["pelvis"][0]
    st = HR.shifted(st, x_turn - back(T_TURN)[0]["pelvis"][0] + 28.0 * k(tt, T_TURN + 0.1, 0.45, "inout"))
    # her back to him, head down
    p.head = -12.0 + 2.0 * math.sin(tt * 2.1)
    if tt >= T_SHE_TURNS:
        # she turns round, toward where he went: a breath held, the arms come undone
        st, p = vic_p(8.0)
        st = HR.shifted(st, x_turn + 28.0 - vic_p(8.0)[0]["pelvis"][0])
        p.lean -= 4.0 * k(tt, T_SHE_TURNS, 0.25, "out")
        p.head = 6.0 * k(tt, T_SHE_TURNS, 0.3, "out")
        return st, p, -1, (0.55 if tt < T_SHE_TURNS + 1 / 12.0 else 0.0)
    sq = 0.55 if tt < T_TURN + 1 / 12.0 else 0.0
    return st, p, 1, sq


def gap_at(t):
    return 8.0 + 6.0 * k(t, 2.0, 4.0)


def draw_couple(c, t, man_x, vic_x, floor, s, ow=7.0):
    """Both of them at scene time t, placed at man_x / vic_x on `floor` at scale s (any layout).
    Returns their mouths, his eye and cheek, in the units of c."""
    her, man, vic = B.figs()
    gap = gap_at(t)
    out = {}
    st, p, fv, sq = vic_state(t)
    c.save()
    B.place(c, vic_x, floor, s)
    if sq > 0.0:
        px = st["pelvis"][0]
        c.translate(px, 0.0)
        c.scale(1.0 - sq, 1.0)
        c.translate(-px, 0.0)
    o = B.draw_cutout(c, vic, st, p, INK, facing=fv, gap=gap, edge=AMBER, outline=AMBER, ow=ow)
    out["vic_mouth"] = (vic_x + o["mouth"][0] * s, floor + o["mouth"][1] * s)
    c.restore()
    st, p, fm = man_state(t)
    c.save()
    B.place(c, man_x, floor, s)
    o = B.draw_cutout(c, man, st, p, INK, facing=fm, gap=gap, edge=AMBER, outline=AMBER, ow=ow)
    c.restore()
    out["man_mouth"] = (man_x + o["mouth"][0] * s, floor + o["mouth"][1] * s)
    e = HR.eye_point(man, st, p, fm, gap)
    out["man_eye"] = (man_x + e[0] * s, floor + e[1] * s)
    ch = HR.cheek_point(man, st, p, fm, gap)
    out["man_cheek"] = (man_x + ch[0] * s, floor + ch[1] * s)
    return out


def shouts(c, t, m, width=20.0, amp=26.0):
    """Red zigzags from one mouth into the other's face, one per shout."""
    for j, (t0, who) in enumerate(SHOUTS):
        if not t0 <= t < t0 + 0.4:
            continue
        a, b = (m["man_mouth"], m["vic_mouth"]) if who == "man" else (m["vic_mouth"], m["man_mouth"])
        d = math.dist(a, b) or 1.0
        e = ((b[0] - a[0]) / d, (b[1] - a[1]) / d)
        B.bolt(c, (a[0] + e[0] * 14.0, a[1] + e[1] * 14.0), (b[0] - e[0] * 30.0, b[1] - e[1] * 30.0 - 8.0), t, t0,
               dur=0.36, width=width, seed=40 + j, amp=amp, n=5)


def starburst(c, p, r, color, seed=0, n=11, rot=0.0):
    """A cut-paper starburst: n uneven spikes round p."""
    pts = []
    for i in range(2 * n):
        a = math.radians(rot + 180.0 * i / n + 7.0 * HR._sn(seed, i, 1))
        rr = r * (1.0 if i % 2 == 0 else 0.42) * (1.0 + (0.22 if i % 2 == 0 else 0.08) * HR._sn(seed, i, 2))
        pts.append((p[0] + rr * math.cos(a), p[1] + rr * math.sin(a)))
    bass.fill_polys(c, [bass.orient(pts, True)], color)


def slap_burst(c, t, p, s=1.0):
    """The slap: a paper starburst at his cheek (graphics on ones), there and gone."""
    if not T_SLAP <= t < T_SLAP + 0.42:
        return
    d = t - T_SLAP
    g = lerp(0.8, 1.0, ease("outback", clamp(d / 0.07))) * (1.0 - ease("in3", clamp((d - 0.22) / 0.2)))
    if g <= 0.02:
        return
    starburst(c, p, 70.0 * s * g, PAPER, seed=7, n=11, rot=-12.0 + 40.0 * d)
    starburst(c, p, 30.0 * s * g, RED, seed=8, n=7, rot=20.0 - 60.0 * d)


# ============================================================================ the room (stage px)
def quarrel_cam(t):
    z, cx, cy = JUMPS[0][1:]
    for (t1, z1, x1, y1) in JUMPS[1:]:
        u = k(t, t1 - 1 / 24.0, 0.07, "out5")           # landed on the beat's own frame
        z, cx, cy = lerp(z, z1, u), lerp(cx, x1, u), lerp(cy, y1, u)
    # the landing: the fly's momentum carries the frame a hair further in, then it settles
    z *= 1.0 + 0.022 * math.sin(math.pi * k(t, T_LAND, 0.3, "out"))
    # her back to him: the frame creeps in on the two of them and the knife
    g = k(t, 7.0 + 1 / 24.0, T_EYE - 7.0, "inout")
    z *= 1.0 + 0.07 * g
    cx += 20.0 * g
    return z, cx, cy


KNIFE_EYE = (HR.KNIFE_AT[0] + 46.0, HR.KNIFE_AT[1] - 9.0)     # where his look lands on the knife


def draw_room(c, t, z, cx, cy, ring_w=14.0, notes=True):
    """His room at scene time t through the stage camera, with the quarrel's annotations."""
    anchors = {}

    def figures(cc):
        anchors.update(draw_couple(cc, t, B.MAN_X, B.VIC_X, HR.FLOOR, HR.FS))

    def after(cc):
        if not notes:
            return
        shouts(cc, t, anchors)
        if t >= T_LOOK:
            K.sight_line(cc, anchors["man_eye"], KNIFE_EYE, t, T_LOOK, RED, dur=0.3, off=T_LOOK_OFF, off_dur=0.16,
                         march=36.0, r=8.0, gap=27.0, head=30.0, seed=3)
        slap_burst(cc, t, anchors["man_cheek"])

    HR.stage(c, z, cx, cy, figures=figures, after=after, ring_u=k(t, T_RING, 0.4, "inout"), ring_w=ring_w)
    return anchors


def draw_quarrel(c, t):
    z, cx, cy = quarrel_cam(t)
    draw_room(c, t, z, cx, cy)


# ============================================================================ 1. along her look
WIN_C = B.centre(B.HIS_WIN)
FLY_Z = (1.15, 11.0)
FLY_C0 = (548.0, 880.0)                  # the street, framed as s02 left it
IN0 = (0.205 / HR.FS, 581.0, 1007.0)     # the room inside his window at first: the Bass framing (WIN_FS)
IN1 = (1.0 / FLY_Z[1], 600.0, 1080.0)    # ... and at the landing: exactly the quarrel's first frame
TB_STREET = 8.0                          # Bass time for the street's windows (both lit)
TB_HER = 9.0                             # ... and for her, small in her window, the mug at her chest


def _her_eye():
    st, p = B.her_pose(TB_HER)
    e = HR.eye_point(B.win_fig(0), st, p, 1, 0.0)
    return (B.HER_WIN[0] + 32.0 + e[0] * B.WIN_FS, B.HER_WIN[3] + 6.0 + e[1] * B.WIN_FS)


LOOK_END = (B.HIS_WIN[0] - 10.0, 604.0)


def fly(t):
    """(street zoom, street centre, room-in-window (scale, cx, cy)) at t."""
    u = clamp(t / T_LAND)
    v = ease("in", u)
    Z = FLY_Z[0] * (FLY_Z[1] / FLY_Z[0]) ** v
    s0 = (540.0 + (WIN_C[0] - FLY_C0[0]) * FLY_Z[0], 960.0 + (WIN_C[1] - FLY_C0[1]) * FLY_Z[0])
    g = ease("inout", u)
    sx, sy = lerp(s0[0], 540.0, g), lerp(s0[1], 960.0, g)
    cx, cy = WIN_C[0] - (sx - 540.0) / Z, WIN_C[1] - (sy - 960.0) / Z
    si = IN0[0] * (IN1[0] / IN0[0]) ** v
    return Z, (cx, cy), (si, lerp(IN0[1], IN1[1], v), lerp(IN0[2], IN1[2], v))


def draw_fly(c, t):
    Z, (cx, cy), (si, ix, iy) = fly(t)
    c.save()
    c.translate(540.0, 960.0)
    c.scale(Z, Z)
    c.translate(-cx, -cy)
    K.draw_elevation(c, TB_STREET, figures=False)
    c.save()
    K.clip_rect(c, B.HER_WIN)
    B.draw_her_window(c, TB_HER)
    c.restore()
    # his window: the room behind the glass, further away than the glass (it opens up as we come)
    win = bass.cut_rect(*B.HIS_WIN, seed=int(B.HIS_WIN[0] + B.HIS_WIN[1]))
    x0, y0, x1, y1 = B.HIS_WIN
    B.fill(c, INK, (x0 - 4.0, y0 - 4.0, x1 + 4.0, y1 + 4.0))     # under the room: no amber left at its edge
    # the room drawn whole into its own layer and laid in through the window once (clipping
    # each piece would leave a hairline of the wall round the ink floor)
    c.push_group()
    c.save()
    c.translate(WIN_C[0], WIN_C[1])
    c.scale(si, si)
    c.translate(-540.0, -960.0)
    draw_room(c, t, 1.0, ix, iy)
    c.restore()
    room = c.pop_group()
    c.save()
    c.new_path()
    bass.draw.poly(c, win)
    c.clip()
    c.set_source(room)
    c.paint()
    c.restore()
    # her look, dot by dot, into his window
    K.sight_line(c, _her_eye(), LOOK_END, t, -1.0, PAPER, march=30.0, seed=2)
    c.restore()


# ============================================================================ 3. her eye
def reflect(t, z):
    """His room in her iris at scene time t (the ring drawn thick enough to read small)."""
    def fn(c, r):
        c.push_group()
        s = (r[2] - r[0]) / W
        c.translate(r[0], r[1])
        c.scale(s, s)
        draw_room(c, t, 1.0, 600.0, 1080.0, ring_w=max(14.0, 3.2 / (s * z)), notes=False)
        room = c.pop_group()
        c.save()
        K.clip_rect(c, (r[0] - 0.6, r[1] - 0.6, r[2] + 0.6, r[3] + 0.6))
        c.set_source(room)
        c.paint()
        c.restore()
    return fn


def draw_eye_shot(c, t):
    tb = TB_EYE + (t - T_EYE)
    look = lerp(-0.25, 0.42, k(tb, B.T_EYE + 0.35, 0.16, "outback")) + 0.03 * math.sin(7.0 * tb)
    blink = 1.0 - (k(t, T_BLINK, 0.06, "in") - k(t, T_BLINK + 0.12, 0.08, "out"))
    open_ = min(k(tb, B.T_EYE - 0.05, 0.18, "out3"), blink)
    dive = k(t, T_DIVE, T_INSERT - T_DIVE - 1 / 24.0, "in3")
    z = math.exp(math.log(W / 104.0) * dive)
    ic = (B.EYE_C[0] + look * 150.0, B.EYE_C[1] - 6.0)
    pan = k(t, T_DIVE, 0.3, "out")
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-lerp(540.0, ic[0], pan), -lerp(960.0, ic[1], pan))
    B.draw_eye(c, tb, open_, look, INK, reflect=reflect(t, z))
    c.restore()


# ============================================================================ 4. the knife insert
INS_LINE = 1330.0                         # the counter's top edge (frame px): eye level, nearly
INS_S = 3.3                               # the knife, huge
KNIFE_O = (382.0, INS_LINE - 11.5 * INS_S)     # its origin (the front of the grip): the handle on the line
INS_RING = ((548.0, INS_LINE - 36.0), 452.0, 112.0, 30.0)     # centre, rx, ry, width
INS_FS = 0.92                             # the two of them, small, beyond the counter
INS_FLOOR = 1462.0                        # their floor (hidden behind the counter)
INS_MAN_X, INS_VIC_X = 262.0, 566.0
INS_LAMP = (430.0, 520.0)


def ins_cam(t):
    z = lerp(1.0, 1.05, k(t, T_INSERT, T_LIFT - T_INSERT, "inout")) + 0.03 * k(t, T_LIFT, 0.08, "out5")
    return z


def draw_counter_front(c):
    """The counter, seen low and close: the top's edge catching the lamp, drawers, knobs."""
    y = INS_LINE
    bass.fill_polys(c, [bass.cut_rect(-60.0, y, W + 60.0, H + 60.0, seed=1801, amp=1.2)], INK)
    seams = [[(-20.0, y + 58.0), (W + 20.0, y + 58.0)],
             [(-20.0, y + 318.0), (W + 20.0, y + 318.0)],
             [(214.0, y + 64.0), (214.0, y + 312.0)],
             [(742.0, y + 64.0), (742.0, y + 312.0)],
             [(478.0, y + 326.0), (478.0, H + 20.0)]]
    HR.cut_lines(c, seams, 5.0)
    for i, p in enumerate(((112.0, y + 186.0), (478.0, y + 186.0), (902.0, y + 186.0), (420.0, y + 460.0),
                           (536.0, y + 460.0))):
        bass.disc(c, p, 13.0, AMBER, seed=1810 + i, n=16)
    # the top's front edge: a line of lamp light along it
    HR.cut_lines(c, [[(-20.0, y + 3.0), (W + 20.0, y + 3.0)]], 5.0)


def draw_ins_lamp(c):
    x, y = INS_LAMP
    bass.fill_polys(c, [bass.orient([(x - 64.0, y + 10.0), (x + 64.0, y + 10.0), (x + 560.0, INS_LINE),
                                     (x - 560.0, INS_LINE)], True)], PAPER, 0.085)
    bass.fill_polys(c, [bass.orient([(x - 3.0, -40.0), (x + 3.0, -40.0), (x + 3.0, y - 96.0), (x - 3.0, y - 96.0)], True),
                        HR.P([(-16.0, -100.0), (16.0, -100.0), (22.0, -78.0), (94.0, -8.0), (100.0, 4.0), (-100.0, 4.0),
                              (-94.0, -8.0), (-22.0, -78.0)], x, y, 1.0, seed=1820, amp=0.4, max_len=30.0)], INK)
    c.save()
    c.new_path()
    c.rectangle(x - 110.0, y + 3.0, 220.0, 80.0)
    c.clip()
    bass.disc(c, (x, y + 4.0), 28.0, PAPER, seed=1821, n=30)
    c.restore()


# --- his hand, from above: the back of his right hand, the fingers curling down over the near
# face of the handle (an amber edge where they cross the ink), the thumb along the far side
# toward the bolster. Frame px relative to the middle of the knuckle row (x right, y down).
# (name, knuckle x, width, open length, shut length, knuckle y): little finger first, a man's
# hand: the middle finger longest, the little finger short and slim.
_FINGERS = (("little", -80.0, 33.0, 76.0, 48.0, 8.0), ("ring", -42.0, 39.0, 92.0, 56.0, 1.0),
            ("middle", 0.0, 42.0, 100.0, 60.0, -2.0), ("index", 42.0, 41.0, 92.0, 57.0, 1.0))
_SPREAD = (-11.0, -4.0, 3.0, 9.0)                # deg the open fingers fan
WRIST = (-18.0, -186.0)                          # the wrist, above the knuckles and a little left
ARM_DIR = (-0.56, -0.83)                         # the forearm, up and left out of the frame


@lru_cache(maxsize=1)
def _hand_back():
    """The back of his hand: the little-finger edge long and straight, the thumb side swelling
    over the root of the thumb, the knuckle row a shallow arch."""
    return HR.P([(-98.0, 10.0), (-99.0, -30.0), (-92.0, -92.0), (-80.0, -146.0), (-66.0, -178.0), (-40.0, -194.0),
                 (6.0, -198.0), (34.0, -186.0), (54.0, -160.0), (74.0, -116.0), (86.0, -74.0), (84.0, -36.0),
                 (66.0, -4.0), (44.0, -10.0), (0.0, -14.0), (-42.0, -10.0), (-80.0, -2.0)],
                seed=1830, amp=0.25, max_len=22.0, sag=0.3)


def hand_pieces(close):
    """(back of the hand, knuckles, fingers, thumb, seams) for close 0 (open, reaching) .. 1 (shut
    round the handle), knuckle row at (0, 0)."""
    knuckles, fingers, tips = [], [], []
    for i, (_, x, w, Lo, Ls, ky) in enumerate(_FINGERS):
        L = lerp(Lo, Ls, ease("inout", close))
        a = math.radians(90.0 - _SPREAD[i] * (1.0 - close))
        x0 = x * lerp(1.05, 1.0, close)
        base = (x0, ky)
        tip = (x0 + math.cos(a) * L, ky + math.sin(a) * L)
        r0 = w * 0.5
        r1 = r0 * lerp(0.80, 0.98, close)            # shut, the end is the knuckle of the curled finger
        fingers.append(bass.orient(bass.capsule_pts(base, tip, r0, r1, cap=10), True))
        knuckles.append(bass.orient(bass.draw.ellipse_pts((x0, ky - 4.0), r0 + 3.0, 15.0, n=22), True))
        tips.append((base, tip, r0, r1))
    # the thumb: out of its root on the side of the hand, its tip down on the top of the handle
    # (shut); reaching, it stands a little off the hand, ready
    tb = (64.0, -74.0)
    tt = (lerp(124.0, 116.0, close), lerp(-30.0, -10.0, close))
    thumb = bass.orient(bass.capsule_pts(tb, tt, 22.0, 16.5, cap=10), True)
    # the cuts between the fingers: from just under the knuckles to where the fingers part
    seams = []
    if close > 0.6:                                  # only once the fingers lie together
        for (b0, t0, r00, _), (b1, t1, r10, _) in zip(tips, tips[1:]):
            x = 0.5 * (b0[0] + r00 + b1[0] - r10)
            y0 = 0.5 * (b0[1] + b1[1]) + 12.0
            y1 = 0.5 * (t0[1] + t1[1]) - 4.0
            if y1 > y0 + 6.0:
                seams.append([(x, y0), (0.5 * (t0[0] + t1[0]), y1)])
    return _hand_back(), knuckles, fingers, thumb, seams


def draw_hand(c, at, close, rot=0.0):
    """His hand, knuckle row at `at`, with its shirt cuff and coat sleeve up out of the frame."""
    back, knuckles, fingers, thumb, seams = hand_pieces(close)
    c.save()
    c.translate(*at)
    c.rotate(math.radians(rot))
    wx, wy = WRIST
    ax, ay = ARM_DIR
    nx, ny = -ay, ax

    def band(d0, d1, h0, h1):
        p0 = (wx + ax * d0, wy + ay * d0)
        p1 = (wx + ax * d1, wy + ay * d1)
        return [(p0[0] + nx * h0, p0[1] + ny * h0), (p1[0] + nx * h1, p1[1] + ny * h1),
                (p1[0] - nx * h1, p1[1] - ny * h1), (p0[0] - nx * h0, p0[1] - ny * h0)]
    wrist = bass.orient(bass.capsule_pts((wx - ax * 20.0, wy - ay * 20.0), (wx + ax * 40.0, wy + ay * 40.0), 62.0, 64.0,
                                         cap=8), True)
    bass.fill_polys(c, [wrist], INK)
    bass.fill_polys(c, [HR.P(band(16.0, 44.0, 70.0, 74.0), seed=1840, amp=0.3, max_len=30.0)], PAPER)    # the cuff
    bass.fill_polys(c, [HR.P(band(42.0, 1700.0, 92.0, 132.0), seed=1841, amp=0.6, max_len=80.0)], INK)   # the sleeve
    B.edged(c, [thumb], INK, AMBER, 6.0)
    B.edged(c, fingers, INK, AMBER, 6.0)
    bass.fill_polys(c, [back] + knuckles, INK)
    HR.cut_lines(c, seams, 4.0)
    c.restore()


def hand_at(t):
    """(knuckle line position, close, rotation) of his hand at t; None before it comes in."""
    tt = twos(t)
    if tt < T_HAND:
        return None
    rest = (KNIFE_O[0] - 38.0 * INS_S, KNIFE_O[1] - 10.5 * INS_S - 6.0)
    come = ease("out3", clamp((tt - T_HAND) / (T_GRIP - T_HAND)))
    start = (rest[0] - 520.0, rest[1] - 760.0)
    x, y = lerp(start[0], rest[0], come), lerp(start[1], rest[1], come)
    close = ease("inout", clamp((tt - (T_GRIP - 0.09)) / (T_CLOSE - T_GRIP + 0.09)))
    squeeze = 3.0 * k(tt, T_CLOSE, 0.1, "out")
    y -= squeeze
    lift = max(0.0, tt - T_LIFT)
    rot = -4.0 * (1.0 - come)
    if lift > 0.0:
        y -= 260.0 * lift + 5200.0 * lift * lift
        x -= 140.0 * lift
        rot -= 26.0 * min(1.0, lift / 0.3)
    return (x, y), close, rot


def ring_insert(c, t):
    (cx, cy), rx, ry, w = INS_RING
    if t < T_LIFT:
        HR.ring(c, 1.0, center=(cx, cy), rx=rx, ry=ry, width=w)
        return
    d = t - T_LIFT
    left, right = HR.ring_halves(center=(cx, cy), rx=rx, ry=ry, width=w)
    for side, pieces in ((-1.0, left), (1.0, right)):
        pop = ease("outback", clamp(d / 0.08))
        dx = side * (34.0 * pop + 150.0 * d)
        dy = -26.0 * pop + 0.5 * 5600.0 * d * d
        rot = side * (9.0 * pop + 70.0 * d + 120.0 * d * d)
        pc = (cx + side * rx * 0.62, cy)
        c.save()
        c.translate(pc[0] + dx, pc[1] + dy)
        c.rotate(math.radians(rot))
        c.translate(-pc[0], -pc[1])
        bass.fill_polys(c, pieces, RED)
        c.restore()


def draw_insert(c, t):
    z = ins_cam(t)
    c.save()
    c.translate(540.0, 1150.0)
    c.scale(z, z)
    c.translate(-540.0, -1150.0)
    B.fill(c, AMBER)
    draw_ins_lamp(c)
    # beyond the counter, small: her back, and him behind her (then he is gone)
    draw_couple(c, t, INS_MAN_X, INS_VIC_X, INS_FLOOR, INS_FS, ow=8.0)
    draw_counter_front(c)
    hand = hand_at(t)
    if hand is None or twos(t) < T_LIFT:
        HR.knife(c, KNIFE_O, 0.0, INS_S)
    else:
        (x, y), close, rot = hand
        rest = (KNIFE_O[0] - 38.0 * INS_S, KNIFE_O[1] - 10.5 * INS_S - 6.0)
        c.save()
        c.translate(x, y)
        c.rotate(math.radians(rot))
        c.translate(-rest[0], -rest[1])
        HR.knife(c, KNIFE_O, 0.0, INS_S)
        c.restore()
    if t < T_LIFT + 0.9:
        ring_insert(c, t)
    if hand is not None:
        (x, y), close, rot = hand
        if y > -400.0:
            draw_hand(c, (x, y), close, rot)
    c.restore()


# ============================================================================ the scene
def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        if t < T_LAND:
            draw_fly(c, t)
        elif t < T_EYE:
            draw_quarrel(c, t)
        elif t < T_INSERT:
            draw_eye_shot(c, t)
        else:
            draw_insert(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    out = [
        Cue(0.0, "whoosh: along her look, into his window", gain_db=-8, dur=T_LAND),
        Cue(T_LAND, "the quarrel, close now: both voices, the strings driving in sixteenths", gain_db=-6,
            dur=T_EYE - T_LAND),
    ]
    for t0, who in SHOUTS:
        out.append(Cue(t0, "his shout" if who == "man" else "her shout", gain_db=-9))
    out += [
        Cue(T_RING, "the ring: a high harmonic sting and a marker squeak", gain_db=-7),
        Cue(T_LOOK, "his look locks on the knife: a low string note, the quarrel drops away under it", gain_db=-9,
            dur=T_SLAP - T_LOOK),
        Cue(T_WIND, "her breath in", gain_db=-14),
        Cue(T_SLAP, "slap", gain_db=-4),
        Cue(T_TURN, "she turns away: skirt, heels", gain_db=-14),
        Cue(T_EYE, "tremolo strings (her eye)", gain_db=-8, dur=T_INSERT - T_EYE),
        Cue(T_BLINK, "a dry tick (the blink)", gain_db=-18),
        Cue(T_DIVE, "into the reflection: a rising whoosh", gain_db=-12, dur=T_INSERT - T_DIVE),
        Cue(T_INSERT, "the insert: near silence, a low held note", gain_db=-14, dur=14.0 - T_INSERT),
        Cue(T_EXIT + 0.2, "his steps, two, three, going", gain_db=-14, dur=0.8),
        Cue(T_HAND, "coat sleeve rustle", gain_db=-14),
        Cue(T_CLOSE, "his grip: a creak of the handle in his fist", gain_db=-10),
        Cue(T_LIFT, "scrape of the knife off the counter, a low thud", gain_db=-6),
        Cue(T_LIFT + 0.02, "the ring snaps: a paper snap", gain_db=-10),
        Cue(T_SHE_TURNS, "her breath catches", gain_db=-12),
    ]
    return out
