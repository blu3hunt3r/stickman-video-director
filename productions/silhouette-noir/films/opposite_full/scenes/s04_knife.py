"""s04 · KNIFE (40-52): the Psycho cuts; the mug; her heart and the vertigo; the silent street.

  0.00  THE KNIFE (the Bass knife shot at tb = 14.0 + t, in his room as s03 left it: the
        counter, bare now; the lamp; the phone corner). THE knife is in his fist from the first
        frame (its bolster and the butt of its handle either side of his fist). He raises it;
        three stabs, each tearing the picture of her open on red; she comes apart and falls
        through the floor; 1.90 the bars close (his light goes out).
  2.50  THE MUG (the Bass mug shot at tb = 16.5 + (t - 2.5)): her gasp; the mug drops; her hand
        over her mouth; the smash below the frame.
  4.50  HER HORROR, the same shot. Her profile holds still, her hand over her mouth trembling on
        twos, while the amber behind her turns into a paper Vertigo spiral: two arms spin out of
        the point she stares at, then it turns and zooms without end (a logarithmic spiral:
        turning it IS zooming it, a fall that never lands), pushed on by every heartbeat. Red
        heartbeat rings thud out of her chest, 90 bpm rising to 140. From 4.60 the frame rolls
        to a -7 deg Dutch tilt.
  9.00  THE SILENT STREET. The night elevation: her window lit, her hand at her mouth; his
        window dark. 9.50 his light snaps on: he stands alone, his back to the street, head
        bowed. The frame eases in toward his window, to where s05 picks him up, closer.
"""
import math
from functools import lru_cache

import cairo

from engine import bass, paperdoll as pd
from engine.core import clamp, hash01, lerp
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import gaze as G
from films.opposite_full import his_room as HR
from films.opposite_full import kit as K

INK, PAPER, AMBER, RED = K.INK, K.PAPER, K.AMBER, B.RED
W, H = K.W, K.H
k = K.k
twos = K.twos

# ----------------------------------------------------------------------------- beats (scene s)
TB_KNIFE = 14.0            # the knife shot: Bass time = t + 14.0
T_STABS = tuple(round(s - TB_KNIFE, 3) for s in B.STABS)         # each stab lands (0.47, 0.75, 1.0)
T_CUTS = tuple(round(s - TB_KNIFE, 3) for s in B.T_SLASH)        # ... and tears her open (0.6, 0.85, 1.1)
T_FALL = round(B.T_SLASH[2] + 0.02 - TB_KNIFE, 3)                # 1.12: she comes apart, falls through the floor
T_BARS = round(B.T_BARS - TB_KNIFE, 3)                           # 1.9: the bars close: his light goes out
T_MUG = 2.5                # the mug shot: Bass time = 16.5 + (t - 2.5)
TB_MUG = 16.5
T_GASP = round(B.T_GASP - TB_MUG + T_MUG, 3)                     # 2.55
T_DROP = round(B.T_DROP - TB_MUG + T_MUG, 3)                     # 2.95
T_HAND = round(B.T_HAND - TB_MUG + T_MUG, 3)                     # 3.17: her hand over her mouth
T_SMASH = round(B.T_SMASH - TB_MUG + T_MUG, 3)                   # 3.6
T_HORROR = 4.5             # the spiral spins out behind her; her heart
T_SPUN = 5.7               # ... its arms are out past the frame
T_TILT = 4.6               # the frame rolls toward -7 deg
TILT = -7.0
HEART_BPM = (90.0, 140.0)  # rising over the horror
T_STREET = 9.0             # cut: the silent street
T_HIS_LIGHT = 9.5          # his light snaps on
END_CAM = (3.4, 736.0, 598.0)      # the last framing: his window; s05 opens closer on it (6.0 on (738, 600))


# ============================================================================ 1. the knife
def man_pose(tb):
    """The Bass cut's stabbing, with THE knife in his fist from the first frame."""
    st, p = B.man_pose(tb)
    p.hold["near"] = HR.fist_knife(lerp(35.0, 58.0, B.stab_at(tb)))
    return st, p


def knife_cam(c):
    """The Bass knife shot's frame (room_zoom from T_RAISE): 1.25 about (540, 1150)."""
    c.translate(540.0, 1150.0)
    c.scale(1.25, 1.25)
    c.translate(-540.0, -1150.0)


def knife_room(c, tb, parts):
    """His room for the knife shot: 'torn' (the wall, the set and her: what the knife cuts)
    or 'whole' (him and the floor her pieces fall behind)."""
    man, vic = B.figs()[1], B.figs()[2]
    gap = 8.0 + 6.0 * k(tb, 12.0, 2.0)
    c.save()
    knife_cam(c)
    if parts == "torn":
        HR.draw_wall(c)
        HR.draw_set(c, knife_on=False)
        c.save()
        B.place(c, B.VIC_X, HR.FLOOR, HR.FS)
        st, p = B.vic_pose(tb)
        B.draw_cutout(c, vic, st, p, INK, facing=-1, gap=gap, burst=B.vic_burst(tb), edge=AMBER, outline=AMBER)
        c.restore()
    else:
        c.save()
        B.place(c, B.MAN_X, HR.FLOOR, HR.FS)
        st, p = man_pose(tb)
        B.draw_cutout(c, man, st, p, INK, facing=1, gap=gap, edge=AMBER, outline=AMBER)
        c.restore()
        HR.draw_floor(c)
    c.restore()


def _group(c):
    """pop_group, its edges carried on past the frame: a torn half sliding along its cut
    shows more of the picture at the frame's edge, never the red behind it."""
    src = c.pop_group()
    src.set_extend(cairo.EXTEND_PAD)
    return src


def draw_knife_shot(c, t):
    """B.draw_knife_shot in his furnished room: each stab tears the picture of her (and her
    wall) open on red; he stands whole in front of the tear."""
    tb = TB_KNIFE + t
    c.push_group()
    knife_room(c, tb, "torn")
    src = _group(c)
    for j, (t0, p, ang) in enumerate(B.CUTS):
        if tb < t0:
            break
        c.push_group()
        B._split(c, src, tb, t0, p, ang, j)
        src = _group(c)
    c.set_source(src)
    c.paint()
    for t0, p, ang in B.CUTS:
        if t0 <= tb < t0 + 0.12:
            a = math.radians(ang)
            u = k(tb, t0, 0.06, "out3")
            tail = k(tb, t0 + 0.05, 0.07, "in")
            bass.slash(c, (p[0] - math.cos(a) * 1200, p[1] - math.sin(a) * 1200),
                       (p[0] + math.cos(a) * 1200, p[1] + math.sin(a) * 1200), PAPER, width=26.0, u=u, tail=tail)
    knife_room(c, tb, "whole")
    if tb >= B.T_BARS:
        bass.bars(c, k(tb, B.T_BARS, 0.5, "linear"), n=9, axis="h", colors=(INK,), frm="alt", mode="slide",
                  overlap=0.6, seed=8, bleed=3.0)


# ============================================================================ 3. her horror
@lru_cache(maxsize=1)
def heart_beats():
    """Her heartbeats over the horror: the rate rising from 90 to 140 bpm (each a lub; the dub
    follows). Scene times."""
    t0, t1 = T_HORROR, T_STREET
    b0, b1 = HEART_BPM
    out, t = [], t0 + 0.08
    while t < t1:
        out.append(round(t, 4))
        u = clamp((t - t0) / (t1 - t0))
        t += 60.0 / lerp(b0, b1, u ** 0.8)
    return tuple(out)


DUB = 0.24                 # the dub after each lub (s)
HEART_P = (676.0, 1660.0)  # her chest (profile px, before the close-up's shift)


def heart_rings(c, p, t, r0=70.0, r1=1500.0, width=32.0, life=1.5):
    """Red rings thudding out of p, a lub and a dub per beat, thinning as they go."""
    for j, tb in enumerate(heart_beats()):
        for i, off in enumerate((0.0, DUB)):
            a = (t - tb - off) / life
            if not 0.0 <= a <= 0.93:
                continue
            r = lerp(r0, r1, K.ease("out3", a))
            w = width * max(0.28, (1.0 - a) ** 1.3) * (1.0 if i == 0 else 0.6)
            bass.ring(c, p, r, w, RED, seed=200 + 7 * j + i, n=120)


def heart_kick(t, dur=0.16):
    """How far the heartbeats have pushed (each lub 1, each dub 0.45, eased in over dur)."""
    s = 0.0
    for tb in heart_beats():
        if t < tb:
            break
        s += K.ease("out3", clamp((t - tb) / dur)) + 0.45 * K.ease("out3", clamp((t - tb - DUB) / dur))
    return s


# --- the vertigo: a two-armed logarithmic spiral of paper on the amber. Each arm's band keeps
# the same share of the space between the arms at every radius, so the spiral looks the same at
# every scale: turning it zooms it, for ever. The arms are cut once (in their own frame) and
# only turned, so their edges never boil.
SPIRAL_C = (806.0, 690.0)  # frame px: in front of her eyes, where she stares
SP_GROW = 2.7              # radius growth per turn
SP_B = math.log(SP_GROW) / (2.0 * math.pi)
SP_R = (2.0, 2700.0)       # the arms run from here (the vanishing point) to past the frame
SP_DUTY = 0.48             # the paper's share of the band between the two arms (log radius)
SP_TAPER = 1.6             # rad: the growing tip narrows to a point
SP_SPIN = (0.9, 2.6)       # rad/s turning (and so zooming), slow to racing
SP_KICK = 0.42             # rad each heartbeat pushes it on


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


@lru_cache(maxsize=1)
def _vertigo_arm():
    """Samples (s, r_in, r_out, wobble_in, wobble_out) along one arm, s its own angle; chords
    stay short at every radius."""
    b = SP_B
    q = math.exp(b * math.pi * SP_DUTY)
    s, s1 = math.log(SP_R[0]) / b, math.log(SP_R[1]) / b
    out, j = [], 0
    while True:
        r = math.exp(b * s)
        out.append((s, r, r * q, _sn(11, j, 1), _sn(11, j, 2)))
        if s >= s1:
            break
        s = min(s1, s + min(0.09, 16.0 / (r * q)))
        j += 1
    return tuple(out)


def vertigo_polys(tip=None):
    """The two arms (frame-free: centre at 0, turned by the caller), drawn on up to s = tip."""
    polys = []
    for a in range(2):
        off = math.pi * a
        outer, inner = [], []
        for s, ri, ro, ja, jb in _vertigo_arm():
            if tip is not None and s > tip:
                break
            if tip is not None:
                ro = ri + (ro - ri) * clamp((tip - s) / SP_TAPER)
            amp = min(1.4, 0.004 * ri + 0.15)
            ang = -(s + off)
            ca, sa = math.cos(ang), math.sin(ang)
            outer.append(((ro + amp * ja) * ca, (ro + amp * ja) * sa))
            inner.append(((ri + amp * jb) * ca, (ri + amp * jb) * sa))
        if len(outer) > 2:
            polys.append(bass.orient(outer + inner[::-1], True))
    return polys


@lru_cache(maxsize=1)
def _vertigo_full():
    return vertigo_polys()


def spiral_turn(t):
    """The spiral's turn (rad, clockwise) at t: slow, then racing with her heart; each beat
    shoves it on."""
    d = max(0.0, t - T_HORROR)
    D = T_STREET - T_HORROR
    w0, w1 = SP_SPIN
    return w0 * d + (w1 - w0) * D * (d / D) ** 2.3 / 2.3 + SP_KICK * heart_kick(t)


def draw_spiral(c, t):
    """The amber behind her turns into the spiral: its two arms spin out of the point she
    stares at (4.5-5.7), then it turns and zooms without end while she stays still."""
    if t <= T_HORROR:
        return
    u = k(t, T_HORROR, T_SPUN - T_HORROR, "sine")
    s0, s1 = math.log(3.0) / SP_B, math.log(SP_R[1]) / SP_B
    polys = _vertigo_full() if u >= 1.0 else vertigo_polys(lerp(s0, s1 + SP_TAPER, u))
    c.save()
    c.translate(*SPIRAL_C)
    c.rotate(spiral_turn(t))
    bass.fill_polys(c, polys, PAPER)
    c.restore()


def her_profile(c, wide=1.0, lid=1.0, look=0.0):
    """B.draw_her_profile without its amber field (so the spiral shows behind her), her
    shoulders carried on below the frame (so the tilt never shows where they end)."""
    bass.fill_polys(c, [bass.orient([(300.0, 1940.0), (1200.0, 1580.0), (1700.0, 1500.0), (1700.0, 2600.0),
                                     (250.0, 2600.0)], True)], INK)
    bass.fill_polys(c, [bass.orient(B.PROFILE, True)], INK)
    B.edged(c, [bass.orient(B.BOB, True)], INK, AMBER, 9.0)
    c0 = (B.EYE_P[0], B.EYE_P[1] - 10.0 * (wide - 1.0))
    eye = B.almond(c0, 84.0, 40.0 * wide, lid)
    bass.fill_polys(c, [eye], PAPER)
    c.save()
    c.new_path()
    bass.draw.poly(c, eye)
    c.clip()
    bass.disc(c, (B.EYE_P[0] + 20.0 + 8.0 * look, B.EYE_P[1] - 4.0 + 6.0 * (1.0 - lid)), 11.0 * (2.0 - wide * 0.6), INK,
              seed=312)
    c.restore()
    top = eye[: len(eye) // 2 + 1]
    for f, L, a in ((0.86, 54.0, -36.0), (0.94, 52.0, -17.0)):
        b = top[int(f * (len(top) - 1))]
        tip = (b[0] + math.cos(math.radians(a)) * L, b[1] + math.sin(math.radians(a)) * L)
        bass.fill_polys(c, [bass.orient([(b[0] - 8.0, b[1] + 3.0), (b[0] + 8.0, b[1] + 2.0), tip], True)], INK)


def tremble(t, amp):
    """A shake on twos (the hand over her mouth)."""
    tt = twos(t)
    return amp * math.sin(tt * 53.0 + 0.7), amp * math.cos(tt * 41.0)


def roll_at(t):
    """The Dutch tilt (deg): rolled over 1.5 s, then a slow sway as she reels."""
    return TILT * k(t, T_TILT, 1.5, "inout") + 0.8 * math.sin(2.0 * (t - T_TILT)) * k(t, T_TILT + 1.0, 1.0)


def draw_horror(c, t):
    c.save()
    c.translate(540.0, 960.0)
    c.rotate(math.radians(roll_at(t)))
    c.translate(-540.0, -960.0)
    B.fill(c, AMBER)
    draw_spiral(c, t)
    c.save()
    c.translate(B.CU_DX, 0.0)
    heart_rings(c, HEART_P, t)
    her_profile(c, wide=1.7)
    # her hand over her mouth, trembling (on twos), harder as her heart races
    amp = lerp(2.5, 6.0, k(t, T_HORROR, T_STREET - T_HORROR, "in"))
    dx, dy = tremble(t, amp)
    wr = (B.W_MOUTH[0] + dx, B.W_MOUTH[1] + dy)
    polys, cuts = B.cu_hand(wr, B.A_MOUTH + 0.6 * dx, 0.0)
    B.draw_arm(c, wr, (B.E_MOUTH[0] + 0.4 * dx, B.E_MOUTH[1] + 0.4 * dy), polys)
    B.cut_lines(c, cuts)
    c.restore()
    c.restore()


# ============================================================================ 4. the silent street
STREET_C0 = (548.0, 872.0)           # the first framing: the whole street (zoom 1.22)
STREET_Z0 = 1.22
TB_STREET = 18.6                     # Bass time of the street (as s05 draws it)
HIS_X = B.HIS_WIN[0] + 92.0          # him in his window (the Bass place; s05 draws him here)
HIS_FLOOR = B.HIS_WIN[3] + 6.0
HER_X = B.HER_WIN[0] + 32.0          # her in hers
HER_FLOOR = B.HER_WIN[3] + 6.0


def street_cam(t):
    """Eased in from the whole street to his window (the window glides to the frame's middle
    while the zoom grows)."""
    u = k(t, T_STREET, 12.0 - T_STREET, "inout")
    z1, x1, y1 = END_CAM
    Z = STREET_Z0 * (z1 / STREET_Z0) ** u
    s0 = (540.0 + (x1 - STREET_C0[0]) * STREET_Z0, 960.0 + (y1 - STREET_C0[1]) * STREET_Z0)
    sx, sy = lerp(s0[0], 540.0, u), lerp(s0[1], 960.0, u)
    return Z, x1 - (sx - 540.0) / Z, y1 - (sy - 960.0) / Z


def his_back_pose(t):
    """Him alone, his back to the street, head bowed (exactly as s05 opens on him); he breathes."""
    st, p = B.alone_pose(18.3)
    st = G.mirror_state(st, st["pelvis"][0])
    tt = twos(t)
    p.head = -24.0
    p.lean += 2.0 + 0.8 * math.sin(2.0 * math.pi * (tt - 12.0) / 2.6)
    return st, p


def her_mouth_pose(t):
    """Her in her window, looking up across at his: her near hand over her mouth (the elbow
    down at her chest), trembling on twos; her other arm hanging, frozen."""
    fig = B.win_fig(0)
    st, p = B.her_pose(18.0)
    p.head = 8.0
    P = (st["pelvis"][0], st["pelvis"][1] + p.crouch)
    m = pd._rot((36.0, -32.0), -p.head)
    q = pd._rot((fig.neck[0] + m[0], fig.neck[1] + m[1]), p.lean)
    mouth = (P[0] + q[0], P[1] + q[1])
    dx, dy = tremble(t, 3.0)
    tgt = (mouth[0] + 4.0 + dx, mouth[1] + 30.0 + dy)
    sh = pd._rot(fig.shoulder, p.lean)
    S = (P[0] + sh[0], P[1] + sh[1])
    el, wr = pd.ik2(S, tgt, fig.upper, fig.fore, forward=1.0)        # the elbow forward and down
    a1 = math.degrees(math.atan2(el[0] - S[0], el[1] - S[1])) - p.lean
    a2 = math.degrees(math.atan2(wr[0] - el[0], wr[1] - el[1])) - p.lean - a1
    p.arms["near"] = ("ang", a1, a2)
    p.arms["far"] = ("ang", 5.0, 12.0)
    return st, p


def draw_street(c, t):
    Z, cx, cy = street_cam(t)
    lit = t >= T_HIS_LIGHT

    def her(cc):
        st, p = her_mouth_pose(t)
        cc.save()
        K.place(cc, HER_X, HER_FLOOR, B.WIN_FS)
        B.draw_cutout(cc, B.win_fig(0), st, p, INK, facing=1, edge=AMBER, outline=AMBER, ow=10.0)
        cc.restore()

    def him(cc):
        st, p = his_back_pose(t)
        cc.save()
        K.place(cc, HIS_X, HIS_FLOOR, B.WIN_FS)
        G.draw_man(cc, B.figs()[1], st, p, 1, head_facing=1, eye=None, hide=("near", "far"))
        cc.restore()

    c.save()
    c.translate(540.0, 960.0)
    c.scale(Z, Z)
    c.translate(-cx, -cy)
    G.street(c, TB_STREET, his_lit=lit, her=her, him=him if lit else None)
    c.restore()


# ============================================================================ the scene
def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        if t < T_MUG:
            draw_knife_shot(c, t)
        elif t < T_HORROR:
            B.draw_mug_shot(c, TB_MUG + (t - T_MUG))
        elif t < T_STREET:
            draw_horror(c, t)
        else:
            draw_street(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    out = [
        Cue(0.0, "the knife goes up: the Psycho shrieks begin", gain_db=-4),
    ]
    for i, (ts, tc) in enumerate(zip(T_STABS, T_CUTS)):
        out.append(Cue(ts, "stab %d: a shriek" % (i + 1), gain_db=-4))
        out.append(Cue(tc, "the picture tears: a paper rip on an impact", gain_db=-6))
    out += [
        Cue(T_CUTS[0], "her scream", gain_db=-3, dur=0.9),
        Cue(T_FALL, "she comes apart and falls: body fall", gain_db=-6),
        Cue(T_BARS, "the bars close: his light goes out (the strings cut off)", gain_db=-8),
        Cue(T_GASP, "her gasp", gain_db=-4),
        Cue(T_DROP, "the mug drops", gain_db=-14),
        Cue(T_HAND, "her hand over her mouth: a stifled cry", gain_db=-10),
        Cue(T_SMASH, "mug smash", gain_db=-5),
        Cue(T_HORROR, "a high held string under her heartbeat (the vertigo)", gain_db=-10, dur=T_STREET - T_HORROR),
    ]
    for tb in heart_beats():
        out.append(Cue(tb, "heartbeat (lub-dub)", gain_db=-6))
    out += [
        Cue(T_STREET, "silence: the night street", gain_db=-30, dur=12.0 - T_STREET),
        Cue(T_HIS_LIGHT, "his light switch: click", gain_db=-12),
        Cue(T_HIS_LIGHT + 0.3, "his breath, slow, close", gain_db=-14, dur=12.0 - T_HIS_LIGHT - 0.3),
    ]
    return out
