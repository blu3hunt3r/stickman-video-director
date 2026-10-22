"""s10 · HIS OWN HAND: the logbook in the diver's gloves (10.0 s, one continuous shot).

IN  (dissolve from s09, 0.75 s): the captain's cabin, black, the helmet lamp on an open
    logbook held in both gloves, filling the lower half of the frame; the helmet port with
    his eyes above it; a cold glow from the hull opening far above behind his helmet.

Beats (scene-local s; L15 0.80-7.43):
  [father's@1.09]  a PHOTO slips from between the pages and floats down, tumbling
  1.78             his right glove catches it; lifts it up in front of his chest
  2.3-3.8          hold on the photo: the captain with the boy on his shoulders; the camera
                   leans in; his eyes on it, a slow blink (2.85-3.55)
  3.8-4.45         he slides it up under his breastplate
  [orders@4.92]    his left glove turns the page: a darker, heavier scrawl block
  5.6-6.9          the lamp light slides down the page; the camera leans in; on [hand@6.69]
                   his glove finds the SIGNATURE, a big looping flourish
  7.0-8.8          the camera pulls back and up: the pale WINCH LINE descends from the
                   opening above with its iron hook, swinging gently; it stops at his eye
                   level, at his right (screen left); he looks up at it (eyes up)
  9.0-10.0         he lowers the book, takes the hook in his right glove and swings it toward
                   frame right as he starts to turn right
OUT (hard cut on action): the hook swinging right, in his right glove.
"""
import functools
import math

import cairo

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import PAPER
from engine.timing import Cue
from films.salvage import cast
from films.salvage import sets as S
from films.salvage.scenes import _lib_s10_s13 as LIB

PAL = S.PAL
INK = PAL.ink
LIGHT = PAL.light
COLD = S.COLD
ss = smoothstep
mix = LIB.mix

# ----------------------------------------------------------------------------- beats
T_FATHER = 1.09
T_CATCH = 1.80
T_HOLD0, T_HOLD1 = 2.30, 3.80
T_BLINK = 2.85
T_LOWER = 4.02                  # the photo is below the breastplate's edge
T_TUCK1 = 4.42
T_TURN0, T_TURN1 = 4.92, 5.52
T_SIGN = 6.69
T_LINE0, T_LINE1 = 7.00, 8.80
T_GRAB = 9.32
T_SWING = 9.40                  # the hook goes back, down past his hip and out to frame right

# ----------------------------------------------------------------------------- the diver
X0 = 100.0                     # pelvis x: in front of the open safe, on her old port side (the floor)
FLOOR = S.CABIN_BOT
YAW = 72.0
DIVER = cast.DIVER
LOOK = cast.diver()


@functools.lru_cache(maxsize=1)
def _diver():
    A = Actor(DIVER, LOOK, x=X0, ground=FLOOR, facing=YAW, t0=-2.0, seed=10)
    A.stand(until=9.45, idle=0.5)
    A.turn(yaw=18.0, dur=0.62, at=9.45, via=50.0)
    A.stand(until=12.0, idle=0.4)
    # the helmet nods down to the book, up to the photo, up at the line
    A.key("head", [(-1.0, 12.0), (1.9, 12.0), (2.4, 6.0), (3.8, 6.0), (4.4, 13.0), (6.9, 15.0), (7.7, 2.0),
                   (8.4, -8.0), (9.3, -5.0), (10.5, 0.0)], fade=0.0)
    A.key("spine", [(-1.0, 4.0), (7.0, 5.0), (8.2, 0.0), (10.5, 0.0)], fade=0.0)
    return A


# ----------------------------------------------------------------------------- the book
# Book space: the top of the spine at (0, 0), x across the spread (-100..100), y down (0..128)
BOOK_S = 0.86                   # world px per book unit
SQUASH = 0.80                   # the spread tilts back toward his eyes


def _book_pose(t):
    """(centre (world), angle deg) of the book: held at his chest, sagging to one side
    while a glove is busy, lowered at the end."""
    cx = X0 + 4.0 + 2.5 * noise1(t * 0.3, 41)
    cy = 4808.0 + 2.5 * noise1(t * 0.35, 42)
    ang = 1.2 * noise1(t * 0.25, 43)
    busy_R = LIB.bump(t, T_FATHER + 0.3, T_FATHER + 0.7, T_TUCK1, T_TUCK1 + 0.45)
    busy_L = LIB.bump(t, T_TURN0 - 0.2, T_TURN0 + 0.1, T_TURN1, T_TURN1 + 0.35)
    busy_S = LIB.bump(t, 6.0, 6.35, 7.05, 7.4)
    ang += 4.5 * busy_R - 3.5 * busy_L + 2.5 * busy_S
    cy += 8.0 * busy_R + 5.0 * busy_L
    low = ease("inout", clamp((t - 8.95) / 0.7))
    return (cx + 50.0 * low, cy + 230.0 * low), ang - 16.0 * low


def _bk(t, u, v):
    """Book-space point (u, v) -> world at time t."""
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


def _word(x0, x1, base, h, seed, slant, loopy, lw):
    """One cursive word (book units): a chain of letters, each an arch (n, m), a small loop
    (e), a tall loop (l, h, b), a descender (g, y) or an oval (o, a), plus i-dots and t-bars.
    Returns a list of polylines (the word and its dots/bars)."""
    n = max(2, int(round((x1 - x0) / lw)))
    step = (x1 - x0) / n
    a = step / (2 * math.pi)
    pts = [(x0 - 0.4 * step, base + 0.2 * h)]
    extra = []
    for i in range(n):
        r = hash01(seed, i)
        hj = 0.85 + 0.3 * hash01(seed, i, 2)
        if r < 0.30:
            kind, hh, b = "arch", h * hj, 0.55 * a
        elif r < 0.52:
            kind, hh, b = "loop", h * 0.85 * hj, 1.9 * a * loopy
        elif r < 0.66:
            kind, hh, b = "tall", h * 2.3 * hj, 2.1 * a * loopy
        elif r < 0.76 and i > 0:
            kind, hh, b = "desc", -h * 1.5 * hj, 1.8 * a * loopy
        elif r < 0.90:
            kind, hh, b = "oval", h * 0.9 * hj, 0.0
        else:
            kind, hh, b = "arch", h * hj, 0.3 * a
        xs = x0 + i * step
        if kind == "oval":                 # a closed oval, then the connector out of it
            cx, cy, rx, ry = xs + 0.55 * step, base - hh * 0.5, 0.36 * step, hh * 0.5
            for k in range(10):
                th = math.pi * 0.5 + 2 * math.pi * k / 9.0
                pts.append((cx + rx * math.cos(th) * -1.0, cy - ry * math.sin(th)))
            pts.append((xs + step, base))
        else:
            for k in range(8):
                u = k / 7.0
                th = u * 2 * math.pi
                pts.append((xs + a * th - b * math.sin(th), base - hh * (1 - math.cos(th)) / 2))
        if kind == "arch" and hash01(seed, i, 5) < 0.18:          # an i-dot
            extra.append([(xs + 0.4 * step, base - 2.2 * h), (xs + 0.55 * step, base - 2.3 * h)])
        if kind == "tall" and hash01(seed, i, 6) < 0.35:          # a t-bar
            extra.append([(xs - 0.3 * step, base - 1.5 * h), (xs + 1.1 * step, base - 1.6 * h)])
    out = [pts] + extra
    return [[(x + slant * (base - y), y) for x, y in P] for P in out]


@functools.lru_cache(maxsize=None)
def _script(page, style):
    """Handwriting for one page (book units): 'log' = the father's neat entries (the last
    one stops mid-page), 'orders' = the owner's heavy scrawl."""
    out = []
    side = -1 if page == "L" else 1
    xa, xb = (-91.0, -11.0) if side < 0 else (11.0, 91.0)
    seed = {"L": 11, "R": 23}[page] + (40 if style == "orders" else 0)
    if style == "log":
        rows = 11 if page == "L" else 6
        h, slant, loopy, lw, gap, dy, y0 = 2.1, 0.25, 1.0, 2.1, 2.6, 9.4, 15.5
    else:
        rows = 8
        h, slant, loopy, lw, gap, dy, y0 = 3.1, 0.50, 1.25, 2.9, 3.4, 10.6, 18.0
    for r in range(rows):
        base = y0 + r * dy
        x = xa + (7.0 if r == 0 and style == "log" else 0.0) + 2.5 * hash01(seed, r)
        end = xb - (0.0 if r < rows - 1 else 26.0 + 12 * hash01(seed, r, 9))
        k = 0
        while x < end - 5:
            wl = (5.0 if style == "log" else 8.0) + 13.0 * hash01(seed, r, k)
            x1 = min(x + wl, end)
            out.extend(_word(x, x1, base, h, seed * 1000 + r * 37 + k, slant, loopy, lw))
            x = x1 + gap + 1.6 * hash01(seed, r, k, 3)
            k += 1
    if style == "log":
        out.append([(xa, 7.5), (xb, 7.5)])                       # the date rule
    return out


@functools.lru_cache(maxsize=None)
def _signature():
    """The owner's signature (book units, bottom of the right page): a tall looping capital,
    a run of shrinking loops, and a long underline that whips back under the name."""
    cap = [(14.0, 121.0), (16.5, 110.0), (19.0, 99.0), (22.0, 95.5), (24.0, 99.0), (23.0, 109.0), (21.5, 119.0),
           (24.5, 108.0), (28.5, 98.0), (31.5, 96.0), (33.0, 100.5), (31.5, 111.0), (30.5, 119.5), (33.5, 116.0)]
    run = []
    x = 36.0
    for i in range(8):
        h = 9.0 * (1.0 - 0.06 * i) * (1.6 if i in (2, 5) else 1.0)
        for k in range(7):
            u = k / 7.0
            th = u * 2 * math.pi
            run.append((x + 5.2 * u - 2.6 * math.sin(th) + 0.34 * h * (1 - math.cos(th)) / 2,
                        117.5 - h * (1 - math.cos(th)) / 2))
        x += 5.2
    tail = [(x + 3.0, 116.0), (x + 7.0, 110.0), (x + 9.0, 107.0), (x + 8.0, 112.0), (x + 2.0, 120.5),
            (x - 14.0, 124.6), (54.0, 126.2), (30.0, 125.4), (17.0, 123.0), (11.0, 119.5)]
    return cap + run + tail


def _page_outline(side):
    s = 1.0 if side > 0 else -1.0
    top = [(s * 2.0, 3.2), (s * 20.0, 1.0), (s * 55.0, -0.4), (s * 100.0, 0.2)]
    bot = [(s * 100.0, 126.4), (s * 55.0, 127.0), (s * 20.0, 127.8), (s * 2.0, 129.4)]
    return top + bot


def _page_fill(ctx, spot, power):
    """Paper lit by the helmet lamp: a warm pool around `spot` (book units)."""
    hot = mix(PAPER, LIGHT, 0.20)
    lit = S.lit_paper(0.80)
    dim = S.lit_paper(0.34)
    g = cairo.RadialGradient(spot[0], spot[1], 0, spot[0], spot[1], 140.0)
    g.add_color_stop_rgb(0.0, *mix(dim, hot, clamp(power)))
    g.add_color_stop_rgb(0.32, *mix(dim, lit, clamp(power)))
    g.add_color_stop_rgb(1.0, *dim)
    ctx.set_source(g)
    ctx.fill()


def _spot(t):
    """The centre of the lamp's pool on the open book (book units): it follows his reading."""
    return LIB.track([(-1.0, (40.0, 56.0)), (1.0, (44.0, 62.0)), (2.0, (-12.0, 84.0)), (4.4, (-6.0, 72.0)),
                      (5.3, (46.0, 34.0)), (6.6, (54.0, 104.0)), (7.0, (54.0, 110.0)), (8.2, (16.0, 86.0))], t)


def _ink_lines(ctx, polys, width, alpha):
    ctx.new_path()
    for P in polys:
        ctx.move_to(*P[0])
        for q in P[1:]:
            ctx.line_to(*q)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_width(width)
    ctx.set_source_rgba(*INK, alpha)
    ctx.stroke()


def _draw_book(ctx, t, power=1.0):
    """The open logbook (and the page that turns on 'orders')."""
    p = _turn_p(t)
    turned = p >= 0.5
    spot = _spot(t)
    ctx.save()
    _book_frame(ctx, t)
    S.round_rect(ctx, -105.0, -4.5, 105.0, 133.5, 4.0)                 # the leather cover
    ctx.set_source_rgb(*mix(INK, LIGHT, 0.06))
    ctx.fill()
    for side in (-1, 1):
        draw.poly(ctx, _page_outline(side))
        _page_fill(ctx, spot, power)
    # the page block's edge under the right page (thickness)
    if not turned:
        _ink_lines(ctx, _script("L", "log"), 0.75, 0.58)
        _ink_lines(ctx, _script("R", "log"), 0.75, 0.62)
    else:
        _ink_lines(ctx, _script("R", "orders"), 1.35, 0.90)
        ctx.new_path()
        draw.smooth(ctx, _signature(), close=False, tension=0.5)
        ctx.set_line_width(1.9)
        ctx.set_source_rgba(*INK, 0.95)
        ctx.stroke()
    draw.linear(ctx, (-15, 0), (15, 0), [(0, INK, 0.0), (0.5, INK, 0.5), (1, INK, 0.0)])     # the gutter
    ctx.rectangle(-15, -2, 30, 133)
    ctx.fill()
    if 0.0 < p < 1.0:                                                   # the turning page
        c = math.cos(math.pi * p)
        lift = 12.0 * math.sin(math.pi * p)
        pts = []
        for (x, y) in _page_outline(1):
            fx = x / 100.0
            pts.append((fx * 100.0 * c, y - lift * fx * (2 - fx) - 0.12 * math.sin(math.pi * p) * (y - 64.0) * fx))
        draw.poly(ctx, pts)
        ctx.set_source_rgb(*mix(S.lit_paper(0.30), S.lit_paper(0.78), 0.4 + 0.6 * abs(c)))
        ctx.fill()
        if abs(c) > 0.06:
            ctx.save()
            ctx.translate(0.0, -lift * 0.6)
            ctx.scale(c, 1.0)
            if p < 0.5:
                _ink_lines(ctx, _script("R", "log"), 0.75 / max(abs(c), 0.3), 0.55 * abs(c))
            ctx.restore()
    ctx.restore()


def _thumbs(ctx, t, grips):
    """Gloved thumbs over the page edges (the mittens behind are the figure's own hands)."""
    ctx.save()
    _book_frame(ctx, t)
    for side, on in grips:
        if on <= 0.02:
            continue
        s = -1.0 if side == "R" else 1.0            # his right glove holds the left edge
        y = 66.0 if side == "R" else 60.0
        a = (s * 108.0, y + 2.0)
        b = (s * lerp(108.0, 91.0, on), y - 3.0)
        draw.capsule(ctx, a, b, 7.0, 5.6)
        ctx.set_source_rgb(*INK)
        ctx.fill()
    ctx.restore()


def _sig_thumb(ctx, t):
    """His left glove's thumb slides down the page edge and stops under the signature."""
    w = LIB.bump(t, SIG0, SIG0 + 0.3, SIG1 - 0.3, SIG1)
    u = ease("inout", clamp((t - (SIG0 + 0.25)) / 0.8))
    ctx.save()
    _book_frame(ctx, t)
    y = lerp(60.0, 124.0, u)
    tip = lerp(91.0, 84.0, u)
    a = (108.0, y + 3.0)
    b = (lerp(108.0, tip, w), y - 1.0)
    draw.capsule(ctx, a, b, 7.0, 5.4)
    ctx.set_source_rgb(*INK)
    ctx.fill()
    ctx.restore()


# ----------------------------------------------------------------------------- the photo
PHOTO_W, PHOTO_H = 78.0, 60.0


@functools.lru_cache(maxsize=1)
def _photo_people():
    """The captain (waist up) with the boy on his shoulders: skeletons in photo units.
    The boy straddles his father's neck, shins hanging either side of the cap; the father
    holds his ankles; the boy waves one arm."""
    boy = F.Pose(0.0, 0.0, 86.0)
    for s in ("L", "R"):
        boy.legs[s] = dict(hip=84.0, abd=40.0, knee=96.0, ankle=-8.0, toe=0.0)
    boy.arms["L"].update(sh=172.0, abd=20.0, elbow=18.0, grip=0.4)     # waving
    boy.arms["R"].update(sh=100.0, abd=62.0, elbow=40.0, grip=0.6)     # out to the side
    boy.head = -4.0
    cap = F.Pose(0.0, 0.0, 84.0)
    cap.head = 2.0
    sk0 = F.solve(cap, cast.CAPTAIN)
    # sit the boy on the shoulders: his pelvis just above the father's neck
    nk = sk0.j["neck"]
    boy.x, boy.y = nk[0] + 2.0, nk[1] - 34.0
    sk_b = F.solve(boy, cast.BOY)
    for s, a in (("L", "ankle_L"), ("R", "ankle_R")):
        cap.arms[s].update(sh=40.0, abd=24.0, elbow=110.0, grip=0.9)
        LIB.solve_arm(cap, s, sk_b.j[a], cast.CAPTAIN)
    sk_c = F.solve(cap, cast.CAPTAIN)
    return sk_c, sk_b


def draw_photo(ctx, c, ang, face=1.0, light=0.8, hide=None):
    """The photo at world centre c: a pale bordered print with the captain and the boy on
    his shoulders cut out in ink. face = cos of its spin about its vertical axis (< 0: the
    plain back). hide(ctx) appends a path the photo is NOT drawn over (tucked away)."""
    ctx.save()
    if hide is not None:
        ctx.new_path()
        ctx.rectangle(c[0] - 500, c[1] - 500, 1000, 1000)
        hide(ctx)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.clip()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.translate(*c)
    ctx.rotate(math.radians(ang))
    ctx.scale(max(abs(face), 0.04), 1.0)
    pale = S.lit_paper(light)
    ctx.new_path()
    S.round_rect(ctx, -PHOTO_W / 2, -PHOTO_H / 2, PHOTO_W / 2, PHOTO_H / 2, 1.0)
    ctx.set_source_rgb(*(pale if face > 0 else mix(pale, INK, 0.15)))
    ctx.fill()
    if face > 0:
        x0, y0, x1, y1 = -PHOTO_W / 2 + 3.6, -PHOTO_H / 2 + 3.6, PHOTO_W / 2 - 3.6, PHOTO_H / 2 - 9.0
        img = mix(pale, INK, 0.16)
        ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
        g = cairo.RadialGradient(0.0, (y0 + y1) / 2 - 4, 4.0, 0.0, (y0 + y1) / 2, PHOTO_W * 0.62)
        g.add_color_stop_rgb(0.0, *mix(img, pale, 0.35))
        g.add_color_stop_rgb(1.0, *mix(img, INK, 0.22))
        ctx.set_source(g)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        hy = lerp(y0, y1, 0.58)                          # the sea behind them
        ctx.rectangle(x0, hy, x1 - x0, y1 - hy)
        ctx.set_source_rgba(*INK, 0.10)
        ctx.fill()
        sk_c, sk_b = _photo_people()
        top = min(sk_b.j["wrist_L"][1], sk_b.j["crown"][1]) - 12.0
        bot = sk_c.j["waist"][1] + 10.0
        k = (y1 - y0) * 0.96 / (bot - top)
        ctx.translate(0.0, y1)
        ctx.scale(k, k)
        ctx.translate(-sk_c.j["neck"][0], -bot)
        col = mix(INK, img, 0.06)
        F.draw_figure(None, sk_b, cast.boy(), ctx, color=col, eyes=False)
        # a hair of paper between the father's cap and the boy (two cut-out pieces)
        ctx.new_path()
        for fn, _c, _eo in costume.pieces(sk_c, cast.captain())["head"]:
            fn(ctx)
        draw.smooth(ctx, F.head_outline(sk_c), close=True, tension=0.5)
        ctx.set_line_width(11.0)
        ctx.set_source_rgb(*mix(img, pale, 0.2))
        ctx.stroke()
        F.draw_figure(None, sk_c, cast.captain(), ctx, color=col, eyes=False)
        ctx.restore()
    ctx.restore()


def _photo_free(t):
    """Where the photo floats after slipping out from between the pages (a slow falling
    leaf): (centre, angle, face)."""
    tau = max(t - T_FATHER, 0.0)
    p0 = _bk(T_FATHER, -4.0, 120.0)
    x = p0[0] - 92.0 * (1 - math.exp(-tau / 0.6)) - 10.0 * math.sin(4.0 * tau)
    y = p0[1] + 30.0 * tau + 28.0 * tau * tau
    ang = -8.0 - 24.0 * math.sin(3.2 * tau + 0.3)
    face = math.cos(1.9 * tau * tau + 0.6 * tau)
    return (x, y), ang, face


HOLD_OFF = (6.0, -62.0)                          # photo centre relative to the right wrist (held from below)


def _photo_state(t, wR):
    """(centre, angle, face, tucked) of the photo, or None while it is not in the water."""
    if t < T_FATHER or t >= T_TUCK1:
        return None
    if t <= T_CATCH:
        c, ang, face = _photo_free(t)
        return c, ang, face, False
    c0, a0, f0 = _photo_free(T_CATCH)
    u = ease("inout", clamp((t - T_CATCH - 0.16) / (T_HOLD0 + 0.08 - T_CATCH - 0.16)))
    held = (wR[0] + HOLD_OFF[0], wR[1] + HOLD_OFF[1])
    d0 = (c0[0] - _wrist_target(T_CATCH)[0][0] - HOLD_OFF[0], c0[1] - _wrist_target(T_CATCH)[0][1] - HOLD_OFF[1])
    c = (held[0] + d0[0] * (1 - u), held[1] + d0[1] * (1 - u))
    ang = lerp(a0, -3.0 + 1.5 * math.sin(1.3 * t), u)
    face = lerp(f0, 1.0, u)
    return c, ang, face, t > T_LOWER


def lerp2(a, b, u):
    return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u


# ----------------------------------------------------------------------------- the hook
LINE_X = X0 - 124.0
HOOK_Y = 4598.0


def _hook_free(t):
    """The hook's eye, lowered by the winch through the opening far above, swinging."""
    u = clamp((t - T_LINE0) / (T_LINE1 - T_LINE0))
    y = lerp(3880.0, HOOK_Y, ease("out3", u))
    if t > T_LINE1:                                       # the winch brake: a small bounce
        tau = t - T_LINE1
        y += 10.0 * math.exp(-3.0 * tau) * math.sin(10.0 * tau)
    env = ss(T_LINE0, T_LINE0 + 0.8, t) * (0.55 + 0.45 * math.exp(-0.4 * max(t - T_LINE1, 0.0)))
    x = LINE_X + 16.0 * math.sin(2.0 * (t - T_LINE0)) * env + 4.0 * noise1(t * 0.4, 61)
    return x, y


def _hook_angle(t):
    env = ss(T_LINE0, T_LINE0 + 0.8, t)
    a = -14.0 * math.cos(2.0 * (t - T_LINE0) + 0.4) * env
    if t > T_GRAB:
        # held by the eye: it trails the arc of his arm and is flung out ahead of it at the end
        held = LIB.track([(T_GRAB, 8.0), (T_GRAB + 0.15, 4.0, "inout"), (9.58, 12.0, "inout"),
                          (9.84, 34.0, "inout"), (10.0, -40.0, "inout"), (10.2, -62.0, "out")], t)
        a = lerp(a, held, ss(T_GRAB, T_GRAB + 0.12, t))
    return a


def _swing_hand(t):
    """The right wrist's arc after the grab: drawn back, down past his hip, out to frame right."""
    u = clamp((t - T_SWING) / 0.80)
    g = u * u * (3.0 - 2.0 * u)
    th = math.radians(185.0 - 210.0 * g)
    return X0 - 30.0 + 140.0 * math.cos(th), 4705.0 + 140.0 * math.sin(th)


# ----------------------------------------------------------------------------- the gloves
def _wrist_target(t):
    """World wrist targets (R, L): the book's edges, plus the acting beats."""
    gR = _bk(t, -116.0, 70.0)
    gL = _bk(t, 116.0, 64.0)
    # right glove: catches the photo, holds it up, lowers it, slides it under the breastplate
    if T_FATHER + 0.3 < t < T_TUCK1 + 0.5:
        cf = _photo_free(T_CATCH)[0]
        catch = (cf[0] - HOLD_OFF[0], cf[1] - HOLD_OFF[1])
        hold = (X0 - 14.0 - HOLD_OFF[0], 4708.0 - HOLD_OFF[1])
        low = (X0 - 10.0 - HOLD_OFF[0], 4796.0 - HOLD_OFF[1])
        tuck = (X0 - 8.0 - HOLD_OFF[0], 4704.0 - HOLD_OFF[1])
        gR = LIB.track([(T_FATHER + 0.3, gR), (T_CATCH, catch, "inout"), (T_CATCH + 0.16, catch),
                        (T_HOLD0 + 0.08, hold, "inout"),
                        (T_HOLD1, (hold[0] + 2.0, hold[1] - 3.0), "inout"), (T_LOWER, low, "inout"),
                        (T_TUCK1, tuck, "inout"), (T_TUCK1 + 0.5, _bk(t, -116.0, 70.0), "inout")], t)
    # left glove: lifts the right page's edge and lays it over
    if T_TURN0 - 0.3 < t < T_TURN1 + 0.4:
        p = _turn_p(t)
        c = math.cos(math.pi * p)
        edge = _bk(t, 100.0 * c + 9.0, 62.0 - 18.0 * math.sin(math.pi * p))
        w = LIB.bump(t, T_TURN0 - 0.3, T_TURN0, T_TURN1, T_TURN1 + 0.4)
        gL = (lerp(gL[0], edge[0], w), lerp(gL[1], edge[1], w))
    # left glove: slides down the page edge and under the signature at 'hand'
    if SIG0 < t < SIG1:
        w = LIB.bump(t, SIG0, SIG0 + 0.45, SIG1 - 0.4, SIG1)
        u = ease("inout", clamp((t - (SIG0 + 0.35)) / 0.75))
        sig = _bk(t, 116.0, lerp(64.0, 128.0, u))
        gL = (lerp(gL[0], sig[0], w), lerp(gL[1], sig[1], w))
    # the hook: reach up for it, close on it, swing it right
    if t > 8.95:
        hk = _hook_free(min(t, T_GRAB))
        reach = (hk[0] + 4.0, hk[1] + 30.0)
        w = ease("inout", clamp((t - 8.95) / (T_GRAB - 8.95)))
        gR = (lerp(gR[0], reach[0], w), lerp(gR[1], reach[1], w))
        if t > T_GRAB:
            arc = _swing_hand(t)
            w = ss(T_GRAB, T_SWING + 0.25, t)
            gR = (lerp(reach[0], arc[0], w), lerp(reach[1], arc[1], w))
    return gR, gL


SIG0, SIG1 = 6.05, 7.45


@functools.lru_cache(maxsize=64)
def _solved(t):
    p = _diver().pose(t)
    for s in ("R", "L"):
        p.arms[s].update(sh=26.0, abd=10.0, elbow=78.0)
    gR, gL = _wrist_target(t)
    LIB.solve_arm(p, "R", gR, DIVER)
    LIB.solve_arm(p, "L", gL, DIVER)
    p.arms["R"]["grip"] = 0.8
    p.arms["L"]["grip"] = 0.8
    return F.solve(p, DIVER), p


def _hook_eye(t):
    if t <= T_GRAB:
        return _hook_free(t)
    sk = _solved(t)[0]
    hand = lerp2(sk.j["wrist_R"], sk.j["fingers_R"], 0.45)
    hk = _hook_free(T_GRAB)
    w = ss(T_GRAB - 0.05, T_GRAB + 0.1, t)
    return lerp(hk[0], hand[0], w), lerp(hk[1], hand[1], w)


# ----------------------------------------------------------------------------- camera
def camera(t):
    z = LIB.track([(-1.0, 4.30), (0.7, 4.30), (1.8, 4.10, "inout"), (2.7, 4.85, "inout"), (3.7, 5.00, "inout"),
                   (4.5, 4.35, "inout"), (5.7, 4.35, "inout"), (6.8, 5.10, "inout"), (8.3, 3.05, "inout"),
                   (9.4, 3.0, "inout"), (10.2, 2.85, "inout")], t)
    cx = LIB.track([(-1.0, X0 - 2.0), (0.7, X0 - 2.0), (1.8, X0 - 34.0, "inout"), (2.7, X0 - 14.0, "inout"),
                    (3.7, X0 - 12.0, "inout"), (4.5, X0 - 2.0, "inout"), (5.7, X0, "inout"), (6.8, X0 + 30.0, "inout"),
                    (8.3, X0 - 40.0, "inout"), (9.45, X0 - 30.0, "inout"), (10.25, X0 + 60.0, "inout")], t)
    cy = LIB.track([(-1.0, 4722.0), (0.7, 4722.0), (1.8, 4790.0, "inout"), (2.7, 4684.0, "inout"),
                    (3.7, 4680.0, "inout"), (4.5, 4738.0, "inout"), (5.7, 4744.0, "inout"),
                    (6.8, 4800.0, "inout"), (8.3, 4668.0, "inout"), (10.2, 4660.0, "inout")], t)
    return Camera(cx, cy, z).shaken(t, amp=0.9, rot_amp=0.05, freq=0.45, seed=10)


# ----------------------------------------------------------------------------- render
INN = S.Interior()


def _corselet_path(sk):
    pieces = costume._helmet(sk, LOOK)
    return pieces[0][0]


def render(f, t, T):
    cam = f.set_camera(camera(t))
    view = S.InteriorView(f)
    sk, p = _solved(t)
    hc = costume.helmet_frame(sk)[0]
    # --- the cabin, black, and the cold light from the opening far above, behind him
    INN.draw(f, t, view, cold=1.0)
    INN.draw_mid(f, t, view, safe_door=0.7, safe_lit=0.2, chair=False)
    sc = cam.to_screen(hc)
    LIB.screen_glow(f, (sc[0] - 160, sc[1] - 700), 1000, COLD, 0.16, blur=40)
    # the cold shaft from the opening far above (the line will come down through it)
    shaft = atmos.beam(f, (LINE_X + 6.0, 3450.0), 90.0, length=1900.0, half_angle=3.3, color=COLD,
                       intensity=0.46, falloff=0.25, soft=0.8, core=0.45, fog=0.28, pool=0.0, dust=0.25,
                       glare=0.0, t=t, seed=12)
    atmos.marine_snow(f, density=0.3, t=t, seed=10, sink=3.0, current=(2.0, 0.0), alpha=0.5, lit=shaft,
                      lit_gain=2.5)
    # --- the diver, the photo, the book, his gloves
    wR = sk.j["wrist_R"]
    ph = _photo_state(t, wR)
    with f.layer() as L:
        F.draw_figure(f, sk, LOOK, L, eyes=False)
        # the photo is held between his chest and the book (his forearm is behind the book)
        if ph is not None:
            hide = (lambda c, sk=sk: _corselet_path(sk)(c)) if ph[3] else None
            draw_photo(L, ph[0], ph[1], ph[2], 0.62 if t < T_FATHER + 0.3 else 0.84, hide=hide)
            if t > T_CATCH:                                  # his thumb over the photo's edge
                a = (wR[0] + 6.0, wR[1] - 26.0)
                draw.capsule(L, a, (a[0] + 12.0, a[1] - 13.0), 6.0, 5.0)
                L.set_source_rgb(*INK)
                L.fill()
        if t < 9.75:
            _draw_book(L, t, 1.0)
            gR = 1.0 - LIB.bump(t, T_FATHER + 0.3, T_FATHER + 0.45, T_TUCK1 + 0.3, T_TUCK1 + 0.5)
            gR *= 1.0 - ss(8.95, 9.1, t)
            gL = 1.0 - LIB.bump(t, T_TURN0 - 0.3, T_TURN0 - 0.15, T_TURN1 + 0.2, T_TURN1 + 0.4)
            gL *= 1.0 - LIB.bump(t, SIG0, SIG0 + 0.05, SIG1 - 0.05, SIG1)
            _thumbs(L, t, (("R", gR), ("L", gL)))
        if t > 8.9:                                          # the arm goes up for the hook
            F._arm_path(L, sk, "R", LOOK)
            F._hand(L, sk, "R", LOOK, p.arms["R"]["grip"])
            L.set_source_rgb(*INK)
            L.fill()
        if SIG0 < t < SIG1:                                  # his left thumb runs down to the name
            _sig_thumb(L, t)
    # --- his eyes in the port
    look_x = LIB.track([(-1, -0.05), (1.2, -0.05), (1.8, -0.55, "inout"), (2.4, -0.30, "inout"), (3.8, -0.30),
                        (4.4, 0.10, "inout"), (5.1, 0.35, "inout"), (6.0, 0.30), (6.8, 0.22, "inout"),
                        (7.9, -0.70, "inout"), (9.2, -0.65), (9.8, 0.45, "inout")], t)
    look_y = LIB.track([(-1, 0.80), (1.2, 0.85), (1.9, 0.95, "inout"), (2.4, 0.62, "inout"), (3.8, 0.62),
                        (4.4, 0.85, "inout"), (6.8, 0.95, "inout"), (7.9, -0.85, "inout"), (9.0, -0.55),
                        (9.6, 0.0, "inout")], t)
    blink = 1.0 - LIB.bump(t, T_BLINK, T_BLINK + 0.24, T_BLINK + 0.42, T_BLINK + 0.70)
    with f.layer() as L:
        LIB.port_eyes(f, L, sk, (look_x, look_y), open_=blink, glow=1.0, halo=0.8, halo_r=2.6)
    # --- the winch line and its hook
    if t > T_LINE0 - 0.05:
        he = _hook_eye(t)
        top = (LINE_X + 26.0, 3400.0)
        with f.layer() as L:
            mid = ((top[0] + he[0]) / 2 + 2.0, (top[1] + he[1]) / 2)
            LIB.draw_pale(L, [top, mid, he], 4.5, mix(LIB.LINE_C, INK, 0.12))
            LIB.draw_hook_rim(L, he[0], he[1], angle=_hook_angle(t), s=1.3, rim_a=0.42)
    # --- the helmet lamp: a small warm glare; its spill on the book and the gloves
    lp = costume.helmet_lamp(sk)[0]
    with f.emit() as G:
        draw.glow_disc(G, lp, 9.0, LIGHT, 0.32)
    with f.layer() as L:
        draw.circle(L, lp, 1.9)
        L.set_source_rgb(*mix(LIGHT, (1, 1, 1), 0.6))
        L.fill()
    if t < 9.75:
        bc = _bk(t, *_spot(t))
        with f.light(blur=30) as A:
            draw.glow_disc(A, bc, 150, LIGHT, 0.12)
    INN.draw_front(f, t, view)


def cues(T):
    return [
        Cue(T.at("father's"), "photo slips from the pages, paper flutter", gain_db=-14),
        Cue(T_CATCH, "glove closes on the photo", gain_db=-16),
        Cue(T_LOWER + 0.1, "photo slid under the breastplate", gain_db=-18),
        Cue(T.at("orders"), "heavy page turn underwater", gain_db=-10),
        Cue(T.at("hand"), "low sting: the signature", gain_db=-8, dur=1.6),
        Cue(T_LINE0, "winch line paying out, distant creak through the hull", gain_db=-12, dur=1.8),
        Cue(T_LINE1, "winch brake, hook bounce clink", gain_db=-10),
        Cue(T_GRAB, "glove on iron", gain_db=-9),
        Cue(T_SWING, "hook swing, water whoosh", gain_db=-11),
    ]
