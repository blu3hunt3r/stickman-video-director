"""s10 · HIS OWN HAND: the logbook in the diver's gloves (10.0 s, one continuous shot).

IN  (dissolve from s09, 0.75 s): the captain's cabin, black, the helmet lamp on an open
    logbook held in both gloves, filling the lower half of the frame; the helmet port with
    his eyes above it; a cold glow from the hull opening far above behind his helmet.

Beats (scene-local s; L15 0.80-7.43):
  [father's@1.09]  a PHOTO slips from between the pages and floats down, tumbling
  1.75             his right glove catches it; lifts it up in front of his chest
  2.3-3.8          hold on the photo: the captain with the boy on his shoulders; the camera
                   leans in; his eyes on it, a slow blink (2.85-3.45)
  3.8-4.4          he tucks it into his breastplate
  [orders@4.92]    his left glove turns the page: a darker, heavier scrawl block
  5.6-6.9          the lamp light slides down the page; the camera leans in; on [hand@6.69]
                   his glove finger finds the SIGNATURE, a big looping flourish
  7.0-8.8          the camera pulls back and up: the pale WINCH LINE descends from the
                   opening above with its iron hook, swinging gently; it stops at his eye
                   level, at his right (screen left); he looks up at it (eyes up)
  9.15-10.0        he lowers the book, takes the hook in his right hand and swings it toward
                   frame right as he starts to turn right
OUT (hard cut on action): the hook swinging right, in his right glove.
"""
import functools
import math

import cairo
import numpy as np

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import PAPER, RED
from engine.timing import Cue
from films.salvage import cast
from films.salvage import sets as S
from films.salvage.scenes import _lib_s10_s13 as LIB

PAL = S.PAL
INK = PAL.ink
LIGHT = PAL.light
COLD = S.COLD
ss = smoothstep

# ----------------------------------------------------------------------------- beats
T_FATHER = 1.09
T_CATCH = 1.78
T_HOLD0, T_HOLD1 = 2.30, 3.80
T_BLINK = 2.85
T_TUCK0, T_TUCK1 = 3.85, 4.40
T_TURN0, T_TURN1 = 4.92, 5.55
T_SIGN = 6.69
T_LINE0, T_LINE1 = 7.00, 8.80
T_LOOK = 7.70
T_GRAB = 9.30
T_SWING = 9.55

# ----------------------------------------------------------------------------- the diver
X0 = -150.0                    # pelvis x (the cabin floor is y = CABIN_BOT)
FLOOR = S.CABIN_BOT
YAW = 72.0


@functools.lru_cache(maxsize=1)
def _diver():
    A = Actor(cast.DIVER, cast.diver(), x=X0, ground=FLOOR, facing=YAW, t0=-2.0, seed=10)
    A.stand(until=9.55, idle=0.5)
    A.turn(yaw=28.0, dur=0.9, at=9.55, via=60.0)
    A.stand(until=12.0, idle=0.4)
    # head: down to the book, up to the photo, down again, up at the line
    A.key("head", [(-1.0, 14.0), (1.9, 14.0), (2.4, 7.0), (3.8, 7.0), (4.3, 15.0), (6.9, 17.0), (7.6, 4.0),
                   (8.4, -9.0), (9.3, -6.0), (10.5, 0.0)], fade=0.0)
    A.key("spine", [(-1.0, 4.0), (7.0, 5.0), (8.2, 0.0), (10.5, 0.0)], fade=0.0)
    return A


DIVER = cast.DIVER
LOOK = cast.diver()


# ----------------------------------------------------------------------------- the book
# Book space: the spine's top at (0, 0), x across (pages -100..100), y down (0..128).
BOOK_S = 0.86                   # world px per book unit
SQUASH = 0.80                   # the pages tilt back toward his eyes


def _book_pose(t):
    """(centre (world), angle deg) of the book: held at his chest, drooping to one side
    while one glove is busy, lowered at the end."""
    cx = X0 + 4.0 + 3.0 * noise1(t * 0.3, 41)
    cy = 4806.0 + 3.0 * noise1(t * 0.35, 42)
    ang = 1.5 * noise1(t * 0.25, 43)
    one_hand_R = LIB.bump(t, T_FATHER + 0.35, T_CATCH, T_TUCK1, T_TUCK1 + 0.4)      # right glove busy
    one_hand_L = LIB.bump(t, T_TURN0 - 0.15, T_TURN0 + 0.15, T_TURN1, T_TURN1 + 0.35)
    ang += 5.0 * one_hand_R - 4.0 * one_hand_L
    cy += 10.0 * one_hand_R + 6.0 * one_hand_L
    low = ss(8.9, 9.6, t)
    cy += 210.0 * low
    cx += 40.0 * low
    ang += -14.0 * low
    return (cx, cy), ang


def _bk(t, u, v):
    """Book-space point (u, v) -> world at time t (affine: rotate, scale, squash)."""
    (cx, cy), ang = _book_pose(t)
    a = math.radians(ang)
    x, y = u * BOOK_S, (v - 64.0) * BOOK_S * SQUASH
    return (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))


def _book_frame(ctx, t):
    (cx, cy), ang = _book_pose(t)
    ctx.translate(cx, cy)
    ctx.rotate(math.radians(ang))
    ctx.scale(BOOK_S, BOOK_S * SQUASH)
    ctx.translate(0.0, -64.0)


def _turn_p(t):
    return ease("inout", clamp((t - T_TURN0) / (T_TURN1 - T_TURN0)))


# handwriting: squiggle rows in book units (cached)
def _word(x0, x1, base, h, seed, slant=0.25, loopy=0.6):
    pts = []
    n = max(4, int((x1 - x0) / 1.1))
    for i in range(n + 1):
        u = i / n
        th = u * (x1 - x0) / 2.2 * 2 * math.pi
        x = x0 + (x1 - x0) * u - loopy * 0.9 * math.sin(th)
        hh = h * (0.55 + 0.45 * hash01(seed, int(th / 6.283)))
        y = base - hh * (1 - math.cos(th)) / 2
        pts.append((x + slant * (base - y), y))
    return pts


@functools.lru_cache(maxsize=None)
def _script(page, style):
    """Lines of handwriting for a page: list of polylines (book units).
    style 'log': the father's neat entries; 'orders': the owner's heavy scrawl."""
    out = []
    side = -1 if page == "L" else 1
    xa, xb = (-92.0, -10.0) if side < 0 else (10.0, 92.0)
    seed = {"L": 11, "R": 23, "L2": 37, "R2": 51}[page if style == "log" else page + "2"]
    if style == "log":
        rows = 11 if page == "L" else 7               # the last entry stops mid-page
        for r in range(rows):
            base = 14.0 + r * 9.6
            x = xa + (6.0 if r == 0 else 0.0) + 3.0 * hash01(seed, r)
            end = xb - (0.0 if r < rows - 1 else 30.0 + 10 * hash01(seed, r, 9))
            k = 0
            while x < end - 6:
                wl = 6.0 + 12.0 * hash01(seed, r, k)
                x1 = min(x + wl, end)
                out.append(_word(x, x1, base, 4.2, seed * 100 + r * 10 + k, 0.22, 0.55))
                x = x1 + 2.6 + 1.5 * hash01(seed, r, k, 3)
                k += 1
        # a date line and a rule above the entry
        out.append([(xa, 7.0), (xb, 7.0)])
    else:
        rows = 8
        for r in range(rows):
            base = 16.0 + r * 10.4
            x = xa + 2.0 * hash01(seed, r)
            end = xb - (0.0 if r < rows - 1 else 26.0)
            k = 0
            while x < end - 6:
                wl = 9.0 + 16.0 * hash01(seed, r, k)
                x1 = min(x + wl, end)
                out.append(_word(x, x1, base, 6.4, seed * 100 + r * 10 + k, 0.42, 0.95))
                x = x1 + 3.2 + 2.0 * hash01(seed, r, k, 3)
                k += 1
    return out


@functools.lru_cache(maxsize=None)
def _signature():
    """The owner's signature (book units, on the right page): a big looping flourish and the
    underline that whips back under it."""
    pts = []
    n = 90
    for i in range(n + 1):
        u = i / n
        th = u * 5.2 * 2 * math.pi
        x = 26.0 + 52.0 * u - 4.2 * math.sin(th) + 3.0 * math.sin(u * 3.0)
        y = 111.0 - (6.0 + 9.0 * math.exp(-((u - 0.12) / 0.10) ** 2) + 5.0 * math.exp(-((u - 0.55) / 0.08) ** 2)) * \
            (1 - math.cos(th)) / 2
        pts.append((x + 0.35 * (111.0 - y), y))
    tail = [(78.0 + 6 * u, 111.0 + 6 * u * u) for u in (0.2, 0.4, 0.6, 0.8, 1.0)]
    under = [(84.0, 117.0), (60.0, 119.5), (34.0, 119.0), (20.0, 116.0)]
    return pts + tail + under


def _page_outline(side, lift=0.0):
    """Page polygon (book units). The pages rise a little toward the gutter."""
    s = 1.0 if side > 0 else -1.0
    top = [(s * 2.0, 3.0 - lift), (s * 30.0, 0.5 - lift * 0.4), (s * 70.0, -0.6), (s * 100.0, 0.0)]
    bot = [(s * 100.0, 126.0), (s * 70.0, 126.6), (s * 30.0, 127.5), (s * 2.0, 129.0)]
    return top + bot


def _page_fill(ctx, spot, power, k_base=0.36):
    """Paper lit by the helmet lamp: a warm pool around `spot` (book units)."""
    hot = LIB.mix(PAPER, LIGHT, 0.16)
    lit = S.lit_paper(0.78)
    dim = S.lit_paper(k_base)
    g = cairo.RadialGradient(spot[0], spot[1], 0, spot[0], spot[1], 150.0)
    g.add_color_stop_rgb(0.0, *LIB.mix(dim, hot, clamp(power)))
    g.add_color_stop_rgb(0.35, *LIB.mix(dim, lit, clamp(power)))
    g.add_color_stop_rgb(1.0, *dim)
    ctx.set_source(g)
    ctx.fill()


def _spot(t):
    """Where the lamp's pool sits on the open book (book units)."""
    return LIB.track([(-1.0, (40.0, 60.0)), (1.0, (42.0, 66.0)), (2.0, (-10.0, 80.0)), (4.6, (-8.0, 70.0)),
                      (5.3, (40.0, 40.0)), (6.5, (52.0, 100.0)), (7.0, (54.0, 108.0)), (8.0, (20.0, 90.0))], t)


def _script_paint(ctx, polys, width, alpha):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.new_path()
    for P in polys:
        ctx.move_to(*P[0])
        for q in P[1:]:
            ctx.line_to(*q)
    ctx.set_line_width(width)
    ctx.set_source_rgba(*INK, alpha)
    ctx.stroke()


def _draw_book(ctx, t, power):
    """The open logbook (and the page that turns on 'orders')."""
    p = _turn_p(t)
    turned = p >= 1.0
    spot = _spot(t)
    ctx.save()
    _book_frame(ctx, t)
    # cover: dark leather, a little wider than the pages
    S.round_rect(ctx, -105.0, -4.0, 105.0, 133.0, 5.0)
    ctx.set_source_rgb(*LIB.mix(INK, LIGHT, 0.05))
    ctx.fill()
    # the left page, then the right page
    for side in (-1, 1):
        draw.poly(ctx, _page_outline(side))
        _page_fill(ctx, spot, power)
    # writing
    if not turned:
        _script_paint(ctx, _script("L", "log"), 0.9, 0.55)
        _script_paint(ctx, _script("R", "log"), 0.9, 0.62)
    else:
        _script_paint(ctx, _script("L", "log"), 0.9, 0.45)
        _script_paint(ctx, _script("R", "orders"), 1.5, 0.86)
        sig = _signature()
        _script_paint(ctx, [sig], 1.7, 0.92)
    # the gutter shadow
    draw.linear(ctx, (-14, 0), (14, 0), [(0, INK, 0.0), (0.5, INK, 0.45), (1, INK, 0.0)])
    ctx.rectangle(-14, 0, 28, 130)
    ctx.fill()
    # the turning page (right -> left), lifted toward his eyes
    if 0.0 < p < 1.0:
        xe = 100.0 * math.cos(math.pi * p)
        lift = 10.0 * math.sin(math.pi * p)
        sh = 0.10 * math.sin(math.pi * p)
        pts = []
        for (x, y) in _page_outline(1):
            fx = x / 100.0
            X = fx * xe
            Y = y - lift * fx * fx - sh * (y - 64.0) * fx
            pts.append((X, Y))
        draw.poly(ctx, pts)
        shade = 0.55 + 0.45 * abs(math.cos(math.pi * p))
        ctx.set_source_rgb(*LIB.mix(S.lit_paper(0.25), S.lit_paper(0.75), shade))
        ctx.fill_preserve()
        ctx.set_source_rgba(*INK, 0.25)
        ctx.set_line_width(0.6)
        ctx.stroke()
        # its writing, squeezed with the page
        ctx.save()
        if abs(xe) > 4:
            ctx.scale(xe / 100.0, 1.0)
            ctx.translate(0.0, -lift * 0.5)
            polys = _script("R", "log") if p < 0.5 else [[(-x, y) for x, y in P] for P in _script("L", "log")]
            _script_paint(ctx, polys, 0.9, 0.5 * abs(math.cos(math.pi * p)))
        ctx.restore()
    ctx.restore()


def _thumbs(ctx, t, grips):
    """Gloved thumbs over the page edges (the mittens are the figure's own hands behind)."""
    ctx.save()
    _book_frame(ctx, t)
    for side, on in grips:
        if on <= 0.01:
            continue
        s = 1.0 if side == "L" else -1.0           # his left glove holds the right edge
        a = (s * 106.0, 58.0)
        b = (s * lerp(106.0, 90.0, on), 54.0)
        draw.capsule(ctx, a, b, 6.5, 5.2)
        ctx.set_source_rgb(*INK)
        ctx.fill()
    ctx.restore()


# ----------------------------------------------------------------------------- the photo
PHOTO_W, PHOTO_H = 60.0, 46.0


@functools.lru_cache(maxsize=1)
def _photo_people():
    """Skeletons of the captain (waist up) with the boy on his shoulders, photo-local."""
    cap = F.Pose(0.0, 0.0, 78.0)
    cap.head = 4.0
    for s, k in (("L", 1.0), ("R", -1.0)):
        cap.arms[s].update(sh=150.0, abd=34.0, elbow=58.0, grip=0.9)
    sk_c = F.solve(cap, cast.CAPTAIN)
    nk = sk_c.j["neck"]
    boy = F.Pose(nk[0] + 4.0, nk[1] - 30.0, 82.0)
    for s in ("L", "R"):
        boy.legs[s] = dict(hip=78.0, abd=34.0, knee=88.0, ankle=-5.0, toe=0.0)
        boy.arms[s].update(sh=160.0, abd=40.0, elbow=30.0, grip=0.5)
    boy.arms["L"].update(sh=172.0, abd=22.0, elbow=12.0)        # one arm up: a wave
    boy.head = -6.0
    sk_b = F.solve(boy, cast.BOY)
    return sk_c, sk_b


def draw_photo(ctx, f, c, ang, s=1.0, face=1.0, light=0.8, clip_y=None):
    """The photo at world centre c: a pale bordered print with the captain and the boy on
    his shoulders cut out in ink. face = cos of its spin about its vertical axis (< 0: the
    plain back shows). clip_y: hide what is above this world y (tucked away)."""
    ctx.save()
    if clip_y is not None:
        ctx.rectangle(c[0] - 400, clip_y, 800, 800)
        ctx.clip()
    ctx.translate(*c)
    ctx.rotate(math.radians(ang))
    ctx.scale(s * max(abs(face), 0.04), s)
    pale = S.lit_paper(light)
    S.round_rect(ctx, -PHOTO_W / 2, -PHOTO_H / 2, PHOTO_W / 2, PHOTO_H / 2, 1.2)
    ctx.set_source_rgb(*(pale if face > 0 else LIB.mix(pale, INK, 0.12)))
    ctx.fill()
    if face > 0:
        x0, y0, x1, y1 = -PHOTO_W / 2 + 3.5, -PHOTO_H / 2 + 3.5, PHOTO_W / 2 - 3.5, PHOTO_H / 2 - 7.5
        img = LIB.mix(pale, INK, 0.30)
        ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
        ctx.set_source_rgb(*img)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        sk_c, sk_b = _photo_people()
        k = 0.068
        ctx.translate(-4.0, y1 + 18.5)
        ctx.scale(k, k)
        ctx.translate(0.0, -sk_c.j["pelvis"][1] * 0.0)
        col = LIB.mix(INK, img, 0.10)
        F.draw_figure(None, sk_b, cast.boy(), ctx, color=col, eyes=False)
        F.draw_figure(None, sk_c, cast.captain(), ctx, color=col, eyes=False)
        ctx.restore()
    ctx.restore()


def _photo_state(t, hand_R):
    """(centre, angle, face, visible, tucked_clip) of the photo."""
    if t < T_FATHER:
        return None
    # free fall from between the pages (a slow falling leaf), until the glove closes on it
    t0 = T_FATHER
    p0 = _bk(t0, 30.0, 118.0)
    tau = min(t, T_CATCH) - t0
    fx = p0[0] - 70.0 * (1 - math.exp(-tau / 0.55)) - 12.0 * math.sin(4.2 * tau)
    fy = p0[1] + 52.0 * tau + 34.0 * tau * tau * 0.5
    fang = -10.0 - 26.0 * math.sin(3.4 * tau + 0.4)
    face = math.cos(0.9 + 2.6 * tau)
    if t <= T_CATCH:
        return (fx, fy), fang, face, None
    # in the glove: carried by the right hand
    hx, hy = hand_R
    u = ss(T_CATCH, T_HOLD0, t)
    face = lerp(math.cos(0.9 + 2.6 * (T_CATCH - t0)), 1.0, u)
    ang = lerp(fang, -4.0, u)
    c = (hx + lerp(fx - hx, 8.0, u), hy + lerp(fy - hy, -26.0, u))
    clip = None
    if t > T_TUCK0:
        clip = _corselet_bottom(t) - 2.0
    return c, ang, face, clip


# ----------------------------------------------------------------------------- hands
def _hand_targets(t, sk0):
    """World wrist targets (R, L) and thumb grips: on the book's edges, plus the acting."""
    gR = _bk(t, -112.0, 66.0)
    gL = _bk(t, 112.0, 62.0)
    # right glove: catches the photo, holds it up, tucks it away, back to the book
    if T_FATHER + 0.3 < t < T_TUCK1 + 0.45:
        st = _photo_free(T_CATCH)
        catch = (st[0] - 2.0, st[1] + 18.0)
        hold = (X0 - 46.0, 4742.0)
        tuck = (X0 - 30.0, _corselet_bottom(t) - 10.0)
        keys = [(T_FATHER + 0.3, gR), (T_CATCH, catch, "inout"), (T_HOLD0, hold, "inout"),
                (T_HOLD1, (hold[0] + 4.0, hold[1] - 6.0), "inout"), (T_TUCK0 + 0.1, (X0 - 34.0, 4778.0), "inout"),
                (T_TUCK1, tuck, "inout"), (T_TUCK1 + 0.45, gR, "inout")]
        gR = LIB.track(keys, t)
    # left glove: lifts the right page's edge and lays it over
    p = _turn_p(t)
    if T_TURN0 - 0.25 < t < T_TURN1 + 0.35:
        xe = 100.0 * math.cos(math.pi * p)
        edge = _bk(t, xe + 6.0, 64.0 - 10.0 * math.sin(math.pi * p))
        w = LIB.bump(t, T_TURN0 - 0.25, T_TURN0, T_TURN1, T_TURN1 + 0.35)
        gL = (lerp(gL[0], edge[0], w), lerp(gL[1], edge[1], w))
    # right glove: a finger on the signature at 'hand'
    if 6.05 < t < 7.35:
        w = LIB.bump(t, 6.05, 6.45, 7.0, 7.35)
        sig = _bk(t, lerp(30.0, 66.0, ss(6.4, 6.95, t)), 126.0)
        gR = (lerp(gR[0], sig[0], w), lerp(gR[1], sig[1], w))
    # the hook: reach up for it, then swing it right
    if t > 9.0:
        hk = _hook_eye(t)
        w = ss(9.0, T_GRAB, t)
        gR = (lerp(gR[0], hk[0], w), lerp(gR[1], hk[1] + 20.0, w))
    return gR, gL


def _photo_free(t):
    t0 = T_FATHER
    p0 = _bk(t0, 30.0, 118.0)
    tau = t - t0
    return (p0[0] - 70.0 * (1 - math.exp(-tau / 0.55)) - 12.0 * math.sin(4.2 * tau),
            p0[1] + 52.0 * tau + 17.0 * tau * tau)


def _corselet_bottom(t):
    sk = _skeleton_base(t)
    return lerp(sk.j["neck"][1], sk.j["chest"][1], 0.95)


@functools.lru_cache(maxsize=256)
def _skeleton_base(t):
    return F.solve(_diver().pose(t), DIVER)


# ----------------------------------------------------------------------------- the line + hook
LINE_X = X0 - 128.0


def _hook_eye(t):
    """The hook's eye (where the line is tied): lowered by the winch, swinging gently."""
    u = clamp((t - T_LINE0) / (T_LINE1 - T_LINE0))
    y_end = 4600.0
    y = lerp(3900.0, y_end, ease("out3", u))
    if t > T_LINE1:                                       # the winch brake: a small bounce
        tau = t - T_LINE1
        y += 9.0 * math.exp(-3.5 * tau) * math.sin(9.0 * tau)
    sw = 14.0 * math.sin(2.1 * (t - T_LINE0)) * math.exp(-0.25 * max(t - T_LINE1, 0.0)) * ss(T_LINE0, T_LINE0 + 0.6, t)
    x = LINE_X + sw + 5.0 * noise1(t * 0.4, 61)
    if t > T_GRAB:                                        # in his glove: carried, then swung
        hR = _wrist_R(t)
        w = ss(T_GRAB, T_GRAB + 0.12, t)
        x, y = lerp(x, hR[0], w), lerp(y, hR[1] - 20.0, w)
    return x, y


def _hook_angle(t):
    sw = 16.0 * math.cos(2.1 * (t - T_LINE0)) * math.exp(-0.25 * max(t - T_LINE1, 0.0))
    if t > T_SWING:
        sw = lerp(sw, -55.0, ss(T_SWING, 10.0, t))
    return sw


def _wrist_R(t):
    return _solved(t)[0].j["wrist_R"]


# ----------------------------------------------------------------------------- solve
@functools.lru_cache(maxsize=64)
def _solved(t):
    A = _diver()
    p = A.pose(t)
    sk0 = F.solve(p, DIVER)
    for s in ("R", "L"):
        p.arms[s].update(sh=26.0, abd=10.0, elbow=78.0)
    gR, gL = _hand_targets_safe(t, sk0)
    LIB.solve_arm(p, "R", gR, DIVER)
    LIB.solve_arm(p, "L", gL, DIVER)
    p.arms["R"]["grip"] = 0.75
    p.arms["L"]["grip"] = 0.75
    sk = F.solve(p, DIVER)
    return sk, p


def _hand_targets_safe(t, sk0):
    if t > T_GRAB:
        # the hook follows the wrist after the grab: solve toward the free hook's path
        hk = _hook_free(t)
        gR, gL = _hand_targets(min(t, T_GRAB - 1e-3), sk0)
        swing = ss(T_SWING, 10.0, t)
        tgt = (hk[0] + 260.0 * swing, hk[1] + 20.0 + 40.0 * swing)
        return tgt, gL
    return _hand_targets(t, sk0)


def _hook_free(t):
    u = clamp((t - T_LINE0) / (T_LINE1 - T_LINE0))
    y = lerp(3900.0, 4600.0, ease("out3", u))
    return LINE_X, y


# ----------------------------------------------------------------------------- camera
def camera(t):
    z = LIB.track([(-1.0, 3.75), (0.6, 3.75), (2.2, 3.95, "inout"), (3.4, 4.35, "inout"), (4.3, 4.05, "inout"),
                   (5.6, 4.05, "inout"), (6.8, 4.45, "inout"), (8.3, 2.55, "inout"), (10.2, 2.68, "inout")], t)
    cx = LIB.track([(-1.0, X0 - 6.0), (0.6, X0 - 6.0), (2.2, X0 - 14.0, "inout"), (3.4, X0 - 36.0, "inout"),
                    (4.3, X0 - 4.0, "inout"), (5.6, X0, "inout"), (6.8, X0 + 22.0, "inout"),
                    (8.3, X0 - 40.0, "inout"), (10.2, X0 - 20.0, "inout")], t)
    cy = LIB.track([(-1.0, 4712.0), (0.6, 4712.0), (2.2, 4724.0, "inout"), (3.4, 4716.0, "inout"),
                    (4.3, 4740.0, "inout"), (5.6, 4746.0, "inout"), (6.8, 4776.0, "inout"),
                    (8.3, 4660.0, "inout"), (10.2, 4652.0, "inout")], t)
    cam = Camera(cx, cy, z)
    return cam.shaken(t, amp=1.6 / z * 2.5, rot_amp=0.08, freq=0.45, seed=10)


# ----------------------------------------------------------------------------- render
INN = S.Interior()


def render(f, t, T):
    cam = f.set_camera(camera(t))
    view = S.InteriorView(f)
    sk, p = _solved(t)
    # --- the cabin, black; the cold light from the hull opening far above
    INN.draw(f, t, view, cold=1.0)
    INN.draw_mid(f, t, view, safe_door=1.0, safe_lit=0.25, dial_angle=0.0, chair=False)
    hc = costume.helmet_frame(sk)[0]
    sc = cam.to_screen(hc)
    LIB.screen_glow(f, (sc[0] + 40, sc[1] - 380), 900, COLD, 0.30, blur=40)
    LIB.screen_glow(f, (sc[0] + 10, sc[1] - 120), 420, COLD, 0.16, blur=30)
    # --- motes in the still water
    atmos.marine_snow(f, density=0.35, t=t, seed=10, sink=4.0, current=(2.0, 0.0), alpha=0.6)
    # --- the diver
    with f.layer() as L:
        F.draw_figure(f, sk, LOOK, L, eyes=False)
        # the photo, the book, the thumbs
        ph = _photo_state(t, _solved(t)[0].j["wrist_R"])
        behind = ph is not None and t < T_FATHER + 0.25
        if behind:
            draw_photo(L, f, ph[0], ph[1], 1.0, ph[2], 0.7)
        if t < 9.7:
            power = 0.95
            _draw_book(L, t, power)
            gR = 1.0 - LIB.bump(t, T_FATHER + 0.3, T_FATHER + 0.5, T_TUCK1 + 0.2, T_TUCK1 + 0.45)
            gR *= 1.0 - LIB.bump(t, 6.0, 6.2, 7.2, 7.4) * 0.0
            gL = 1.0 - LIB.bump(t, T_TURN0 - 0.25, T_TURN0 - 0.1, T_TURN1 + 0.1, T_TURN1 + 0.35)
            gR *= 1.0 - ss(8.95, 9.1, t)
            _thumbs(L, t, (("R", gR), ("L", gL)))
        if ph is not None and not behind:
            draw_photo(L, f, ph[0], ph[1], 1.0, ph[2], 0.8, clip_y=ph[3])
        # the near (right) glove on top of everything it holds
        F._hand(L, sk, "R", LOOK, p.arms["R"]["grip"])
        L.set_source_rgb(*INK)
        L.fill()
    # --- his eyes in the port
    look_x = LIB.track([(-1, -0.1), (1.2, -0.1), (1.8, -0.55, "inout"), (2.4, -0.35, "inout"), (3.8, -0.3),
                        (4.4, 0.2, "inout"), (5.0, 0.4, "inout"), (6.0, 0.35), (6.8, 0.25, "inout"),
                        (7.8, -0.75, "inout"), (9.2, -0.7), (9.8, 0.4, "inout")], t)
    look_y = LIB.track([(-1, 0.75), (1.2, 0.8), (1.9, 0.9, "inout"), (2.4, 0.55, "inout"), (3.8, 0.55),
                        (4.4, 0.8, "inout"), (6.8, 0.95, "inout"), (7.8, -0.85, "inout"), (9.0, -0.6),
                        (9.6, 0.0, "inout")], t)
    blink = 1.0 - LIB.bump(t, T_BLINK, T_BLINK + 0.22, T_BLINK + 0.42, T_BLINK + 0.72)
    with f.layer() as L:
        LIB.port_eyes(f, L, sk, (look_x, look_y), open_=blink, glow=1.0)
    # --- the line and the hook
    if t > T_LINE0 - 0.05:
        he = _hook_eye(t)
        with f.layer() as L:
            top = (LINE_X + 30.0, 3300.0)
            LIB.draw_pale(L, [top, ((top[0] + he[0]) / 2 + 3, (top[1] + he[1]) / 2), he], 5.0)
            S.draw_hook(L, he[0], he[1], angle=_hook_angle(t), s=1.35)
    # --- the lamp: warm spill on the book and his gloves
    lamp = costume.helmet_lamp(sk)[0]
    bc = _book_pose(t)[0]
    if t < 9.7:
        with f.light(blur=30) as A:
            draw.glow_disc(A, bc, 170, LIGHT, 0.10)
    INN.draw_front(f, t, view)


def cues(T):
    return [
        Cue(T.at("father's"), "photo slips from the pages, paper flutter", gain_db=-14),
        Cue(T_CATCH, "glove closes on the photo", gain_db=-16),
        Cue(T_TUCK0 + 0.3, "photo slid under the breastplate", gain_db=-18),
        Cue(T.at("orders"), "heavy page turn underwater", gain_db=-10),
        Cue(T.at("hand"), "low sting: the signature", gain_db=-8, dur=1.6),
        Cue(T_LINE0, "winch line paying out, distant creak through the hull", gain_db=-12, dur=1.8),
        Cue(T_LINE1, "winch brake, hook bounce clink", gain_db=-10),
        Cue(T_GRAB, "glove on iron", gain_db=-9),
        Cue(T_SWING, "hook swing, water whoosh", gain_db=-11),
    ]
