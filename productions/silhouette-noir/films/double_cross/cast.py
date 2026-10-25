"""DOUBLE CROSS: the cast. Four cut-paper silhouettes in profile and a cat.

    fig = C.fig("architect")                  # 'architect', 'knight', 'cracker', 'guard'
    perf = C.perf("knight", [C.Seg(C.clip("17_08"), 1.0, 4.0, at=0.0)], facing=1)
    st, pose = perf(t)
    out = C.draw(c, "knight", st, pose, x, floor_y, s=0.5, facing=1, bg=K.NAVY)
    C.cigarette(c, out, t)                    # the Knight's ember, at his mouth

Every figure is INK with a rim of its colour on the lit side (C.RIM: the Architect PAPER, the
Knight RED, the Cracker GOLD, the Guard STEEL): the figure is laid down once in the rim colour,
nudged toward the light, then in INK on top. `bg` (the colour behind them) edges the near arm
and leg so a limb across the body still reads.

Figure units: origin at the pelvis, y up negative, facing +x, about 660 (the Architect) to 730
(the Knight) tall; B.place(c, x, floor_y, s) scales them to px. Props held in a hand go in
pose.hold[side] = C.hold_flashlight() etc.
"""
import math
from dataclasses import replace
from functools import lru_cache

from engine import bass, draw as D, mocap as mc, paperdoll as pd
from engine.core import clamp, hash01, lerp
from films.double_cross import kit as K
from films.opposite_bass import world as B

Seg = mc.Seg
RIM = {"architect": K.PAPER, "knight": K.RED, "cracker": K.GOLD, "guard": K.STEEL}
PIECE = {"architect": ("queen", K.PAPER), "knight": ("knight", K.RED), "cracker": ("bishop", K.GOLD),
         "guard": ("pawn", K.INK)}


def clip(name):
    return mc.Clip.load(name)


def _cut(pts, seed, amp=0.35):
    return pd._cut(pts, seed, amp=amp)


def _ell(c, rx, ry, seed):
    return pd._ellipse(c, rx, ry, seed)


# ============================================================================ the figures
@lru_cache(maxsize=None)
def fig(who):
    if who == "architect":
        f = pd.woman(None, 7)
        s = 7100
        torso = [
            # the trench coat: padded shoulders, cinched at the belt, flaring to the knee
            (_cut([(-30, -262), (34, -262), (44, -238), (46, -200), (36, -150), (33, -112), (44, -60), (60, 142),
                   (-54, 142), (-42, -60), (-30, -112), (-36, -150), (-42, -200), (-40, -240)], s + 1), "ink"),
            # the belt, and its tie hanging at the back
            (_cut([(-36, -122), (40, -122), (41, -102), (-37, -102)], s + 2), "ink"),
            (_cut([(-34, -114), (-50, -78), (-44, -74), (-30, -104)], s + 3), "ink"),
            # the turned-up collar, standing behind her neck
            (_cut([(-26, -258), (-22, -294), (-6, -286), (12, -268), (26, -258), (20, -246), (-20, -246)], s + 4), "ink"),
            (_cut([(-6, -282), (14, -282), (14, -254), (-6, -254)], s + 5), "ink"),
        ]
        head = [
            (_ell((8, -318), 36, 43, s + 6), "ink"),
            # the profile: brow, nose, lips, chin
            (_cut([(30, -346), (44, -334), (46, -322), (55, -308), (45, -304), (47, -297), (43, -292), (44, -286),
                   (34, -278), (20, -282)], s + 7), "ink"),
            # hair swept back smooth over the crown
            (_cut([(-28, -346), (-10, -364), (12, -366), (32, -356), (42, -340), (26, -346), (4, -350), (-14, -340),
                   (-30, -322)], s + 8), "ink"),
            # the low chignon at the nape, and the pencil through it
            (_ell((-36, -300), 21, 18, s + 9), "ink"),
            (_cut([(-79, -340), (-70, -336), (-14, -294), (-18, -289), (-72, -330)], s + 10, amp=0.15), "ink"),
        ]
        return replace(f, name=who, torso=torso, head=head, eye=((32.0, -324.0), 4.5, 5.0))
    if who == "knight":
        f = pd.man(None, 7)
        s = 7200
        torso = [
            # a heavy coat to mid-thigh, square and wide
            (_cut([(-54, -278), (60, -278), (76, -222), (72, -120), (68, -40), (76, 84), (-68, 84), (-60, -40),
                   (-64, -120), (-70, -222)], s + 1), "ink"),
            # the collar turned up round a thick neck
            (_cut([(-42, -304), (6, -320), (36, -304), (50, -274), (-48, -272)], s + 2), "ink"),
        ]
        head = [
            (_ell((10, -338), 40, 45, s + 3), "ink"),
            # a broken nose, a heavy jaw
            (_cut([(34, -366), (50, -350), (52, -340), (62, -328), (52, -322), (54, -312), (50, -300), (40, -292),
                   (14, -292)], s + 4), "ink"),
            # the flat cap: a soft crown pulled forward, a short peak
            (_cut([(-38, -352), (-34, -378), (-10, -392), (24, -394), (50, -382), (58, -368), (82, -362), (80, -354),
                   (46, -352), (-38, -346)], s + 5), "ink"),
        ]
        return replace(f, name=who, torso=torso, head=head, leg_w=(48.0, 38.0, 30.0), arm_w=(38.0, 30.0, 23.0),
                       hand_r=18.0, eye=((38.0, -344.0), 5.0, 2.6))
    if who == "cracker":
        f = pd.man(None, 8)
        s = 7300
        torso = [
            # a long narrow frock coat to the knee; the shoulders slope
            (_cut([(-30, -258), (30, -266), (42, -214), (36, -110), (40, -20), (46, 136), (-42, 136), (-34, -20),
                   (-30, -110), (-42, -212)], s + 1), "ink"),
            (_cut([(-6, -296), (18, -296), (20, -258), (-8, -258)], s + 2), "ink"),
        ]
        head = [
            (_ell((10, -334), 33, 41, s + 3), "ink"),
            # a long nose, a thin chin
            (_cut([(32, -356), (42, -344), (58, -326), (44, -322), (44, -312), (38, -300), (28, -296), (14, -298)],
                  s + 4), "ink"),
            # the bowler: a round dome over a narrow curled brim
            (_cut([(-30, -360), (-28, -384), (-14, -400), (10, -405), (32, -397), (42, -381), (44, -362)], s + 5), "ink"),
            (_cut([(-44, -366), (-36, -362), (54, -362), (62, -368), (60, -358), (-46, -356)], s + 6), "ink"),
        ]
        # thin and old: narrow limbs, a little shorter; the spectacle lens is his eye
        return replace(f, name=who, torso=torso, head=head, thigh=140.0, shin=134.0, leg_w=(28.0, 22.0, 17.0),
                       arm_w=(22.0, 18.0, 14.0), hand_r=13.0, eye=((34.0, -338.0), 8.0, 8.0))
    if who == "guard":
        f = pd.man(None, 9)
        s = 7400
        torso = [
            # a uniform tunic to the hip, belted, a holster at the back
            (_cut([(-46, -272), (52, -272), (64, -214), (62, -120), (56, -40), (58, 22), (-52, 22), (-50, -60),
                   (-56, -214)], s + 1), "ink"),
            (_cut([(-56, -40), (64, -40), (64, -22), (-56, -22)], s + 2), "ink"),
            (_cut([(-56, -34), (-72, -28), (-68, 12), (-52, 8)], s + 3), "ink"),
            (_cut([(-14, -302), (22, -302), (24, -268), (-16, -268)], s + 4), "ink"),
        ]
        head = [
            (_ell((10, -338), 38, 45, s + 5), "ink"),
            (_cut([(36, -362), (48, -346), (56, -332), (48, -326), (50, -314), (44, -302), (34, -296), (14, -296)],
                  s + 6), "ink"),
            # the peaked cap: a flat top wider than the head, a band, the peak
            (_cut([(-34, -356), (-44, -384), (-30, -392), (52, -394), (60, -384), (50, -360)], s + 7), "ink"),
            (_cut([(46, -364), (80, -352), (78, -346), (44, -354)], s + 8), "ink"),
        ]
        return replace(f, name=who, torso=torso, head=head, eye=((38.0, -342.0), 5.0, 3.0))
    raise ValueError(who)


def perf(who, segs, facing=1, x=0.0, near="Right"):
    return mc.Performance(fig(who), segs, facing=facing, x=x, near=near)


def standing(who, x=0.0, spread=16.0):
    return pd.standing(fig(who), x, spread)


# ============================================================================ drawing
def draw(c, who, st, pose, x, floor_y, s=0.5, facing=1, bg=K.NAVY, rim=None, rim_w=4.0, light=(-0.6, -0.8),
         color=K.INK, hide=(), ow=6.0, eye=True):
    """Draw `who` at state st / pose (figure units) standing on floor_y at frame x, scale s.
    rim: the rim colour (default C.RIM[who]; False for none), laid rim_w px toward `light`
    (a unit vector, frame px). bg edges the near arm and leg. Returns draw_cutout's joints
    (frame px): 'head', 'mouth', 'hand_near', 'hand_far', 'pelvis', ..."""
    F = fig(who)
    rim = RIM[who] if rim is None else rim
    if not eye:
        pose.eye = 0.0
    if rim:
        c.save()
        c.translate(light[0] * rim_w, light[1] * rim_w)
        B.place(c, x, floor_y, s)
        holds = pose.hold
        pose.hold = {k: _rimmed(fn, rim) for k, fn in holds.items()}
        B.draw_cutout(c, F, st, pose, rim, facing=facing, hide=hide)
        pose.hold = holds
        c.restore()
    c.save()
    B.place(c, x, floor_y, s)
    out = B.draw_cutout(c, F, st, pose, color, facing=facing, edge=bg, hide=hide, outline=bg, ow=ow)
    joints = {k: c.user_to_device(*v) for k, v in out.items() if isinstance(v, tuple) and len(v) == 2}
    c.restore()
    return {k: c.device_to_user(*v) for k, v in joints.items()}


def _rimmed(fn, rim):
    def g(c, info):
        fn(c, dict(info, rim=rim))
    return g


# ============================================================================ props
def hold_flashlight(on=True):
    """A flashlight in the fist, pointing along the forearm. The beam is the scene's (K.cone from
    the lens, which this stores in info['lens'] via the returned dict)."""
    where = {}

    def fn(c, info):
        hc, u, n = info["hc"], info["u"], info["n"]
        col = info.get("rim") or K.INK
        L, r = 64.0, 11.0
        a = (hc[0] - u[0] * 20.0, hc[1] - u[1] * 20.0)
        b = (hc[0] + u[0] * (L - 20.0), hc[1] + u[1] * (L - 20.0))
        bass.fill_polys(c, [bass.orient(bass.capsule_pts(a, b, r * 0.8, r * 1.15, cap=4), True)], col)
        if on and not info.get("rim"):
            lens = (b[0] + u[0] * 4.0, b[1] + u[1] * 4.0)
            bass.fill_polys(c, [D.ellipse_pts(lens, 4.0, r * 1.05, n=16, angle=math.degrees(math.atan2(u[1], u[0])))],
                            K.PAPER)
            where["lens"] = c.user_to_device(*lens)
            where["dir"] = c.user_to_device_distance(*u)
    fn.where = where
    return fn


def lens_at(c, hold):
    """The flashlight's lens and beam angle (deg) in the caller's px, after the figure is drawn."""
    w = hold.where
    if "lens" not in w:
        return None, 0.0
    p = c.device_to_user(*w["lens"])
    d = c.device_to_user_distance(*w["dir"])
    return p, math.degrees(math.atan2(d[1], d[0]))


def hold_chalk():
    """A stick of chalk between finger and thumb (the Architect)."""
    def fn(c, info):
        hc, u = info["hc"], info["u"]
        col = K.PAPER if not info.get("rim") else info["rim"]
        a = (hc[0] + u[0] * 6.0, hc[1] + u[1] * 6.0)
        b = (hc[0] + u[0] * 34.0, hc[1] + u[1] * 34.0)
        bass.fill_polys(c, [bass.orient(bass.capsule_pts(a, b, 5.0, 5.0, cap=3), True)], col)
    return fn


def hold_case(w=150.0, h=96.0):
    """A heavy case hanging from the fist (the Knight carries the gold)."""
    def fn(c, info):
        hc = info["hc"]
        col = info.get("rim") or K.INK
        x0, y0 = hc[0] - w / 2.0, hc[1] + 14.0
        bass.fill_polys(c, [bass.cut_rect(x0, y0, x0 + w, y0 + h, seed=91, amp=0.6)], col)
        bass.fill_polys(c, [bass.orient(bass.capsule_pts((hc[0] - 22.0, hc[1] + 16.0), (hc[0] + 22.0, hc[1] + 16.0),
                                                         5.0, 5.0, cap=3), True)], col)
        if not info.get("rim"):
            for i in (0.3, 0.7):
                bass.fill_polys(c, [bass.cut_rect(x0 + w * i - 4.0, y0 + 6.0, x0 + w * i + 4.0, y0 + 16.0, seed=92, amp=0.2)],
                                K.GOLD, 0.9)
    return fn


def cigarette(c, out, t, s=0.5, facing=1, glow=True):
    """The Knight's cigarette at his mouth: a short paper stick and its RED ember, which glows
    brighter when he draws on it (every few seconds)."""
    m = out.get("mouth")
    if m is None:
        return
    L = 34.0 * s
    tip = (m[0] + facing * L, m[1] + 4.0 * s)
    K.band(c, [m, tip], K.PAPER, max(2.0, 7.0 * s), seed=3, alpha=0.9)
    pull = 0.5 + 0.5 * max(0.0, math.sin(t * 1.3)) ** 6
    if glow:
        bass.fill_polys(c, [D.circle_pts(tip, 16.0 * s * (0.7 + pull), n=20)], K.RED, 0.18 + 0.2 * pull)
    K.dot(c, tip, max(2.2, 6.0 * s), K.RED, seed=4)


def spectacles(c, out, s=0.5):
    """Not drawn: the Cracker's spectacle lens is his eye (fig.eye, a PAPER disc)."""
    return None


# ============================================================================ the cat
def cat(c, p, s=1.0, t=0.0, facing=1, mode="walk", eyes=1.0, color=K.INK, rim=None, seed=0):
    """A small black cat at p (its feet line), about 120 px nose to rump at s = 1. mode: 'walk'
    (legs scissor on twos), 'sit' (upright, tail curled), 'arch' (back up, fur on end: startled).
    eyes: 0..1 open; the eyes are GOLD."""
    tt = K.twos(t)
    c.save()
    c.translate(*p)
    c.scale(s * facing, s)
    polys = []
    if mode == "sit":
        body = [(-30.0, 0.0), (-36.0, -24.0), (-26.0, -52.0), (-6.0, -66.0), (12.0, -60.0), (20.0, -36.0),
                (18.0, -4.0), (30.0, 0.0)]
        head_c = (10.0, -78.0)
        tail = [(-28.0, -2.0), (-50.0, 0.0), (-60.0, -10.0), (-52.0, -22.0), (-46.0, -12.0), (-52.0, -6.0),
                (-30.0, -8.0)]
        polys += [body, tail]
    else:
        arch = 1.0 if mode == "arch" else 0.0
        back = -46.0 - 26.0 * arch
        body = [(-46.0, -30.0), (-40.0, back + 6.0), (-10.0, back - 4.0 * arch), (24.0, back + 6.0), (44.0, -36.0),
                (40.0, -22.0), (-40.0, -20.0)]
        polys.append(body)
        # legs: four thin capsules scissoring on twos
        ph = tt * 7.0
        for i, (hx, sgn) in enumerate(((-36.0, 1.0), (-30.0, -1.0), (30.0, 1.0), (36.0, -1.0))):
            sw = 10.0 * math.sin(ph + (0.0 if sgn > 0 else math.pi)) if mode == "walk" else 0.0
            polys.append(bass.capsule_pts((hx, -24.0), (hx + sw, 0.0), 4.0, 3.2, cap=3))
        head_c = (50.0, back + 4.0 - 6.0 * arch)
        sway = 10.0 * math.sin(tt * 2.6 + seed)
        up = 1.0 if mode == "arch" else 0.6
        tail = [(-40.0, -38.0)]
        for k in range(1, 7):
            f = k / 6.0
            tail.append((-40.0 - 34.0 * f + sway * f * f, -38.0 - 40.0 * up * f + 16.0 * f * f))
        polys.append(bass.capsule_pts(tail[0], tail[-1], 4.5, 3.0, cap=3))
        for a, b in zip(tail, tail[1:]):
            polys.append(bass.capsule_pts(a, b, 4.2, 4.2, cap=3))
        if arch:
            for k in range(7):                        # fur on end
                x = -36.0 + 10.0 * k
                y = back + 4.0 - 10.0 * math.sin(math.pi * k / 6.0)
                polys.append([(x - 4.0, y + 4.0), (x, y - 9.0), (x + 4.0, y + 4.0)])
    head = D.circle_pts(head_c, 15.0, n=24)
    ears = [[(head_c[0] - 12.0, head_c[1] - 6.0), (head_c[0] - 8.0, head_c[1] - 24.0), (head_c[0] - 1.0, head_c[1] - 12.0)],
            [(head_c[0] + 2.0, head_c[1] - 12.0), (head_c[0] + 9.0, head_c[1] - 25.0), (head_c[0] + 13.0, head_c[1] - 6.0)]]
    polys += [head] + ears
    polys = [bass.orient(q, True) for q in polys]
    if rim:
        c.save()
        c.translate(-2.0, -2.0)
        bass.fill_polys(c, polys, rim)
        c.restore()
    bass.fill_polys(c, polys, color)
    if eyes > 0.02:
        for dx in (-2.0, 8.0):
            e = (head_c[0] + dx, head_c[1] - 2.0)
            bass.fill_polys(c, [D.ellipse_pts(e, 3.4, 3.4 * eyes, n=12)], K.GOLD)
            bass.fill_polys(c, [D.ellipse_pts(e, 0.9, 3.0 * eyes, n=8)], K.INK)
    c.restore()
