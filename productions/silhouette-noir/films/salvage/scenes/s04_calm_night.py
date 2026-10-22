"""s04 · CALM NIGHT: the crime as a Saul Bass paper story (14.0 s, flat graphic).

IN  (flatten from s03, 1.0 s): ink, and a PAPER moon at (540, 1250) shaped like the
    flattened lamp spot (an ellipse 260 x 120) that rounds into a disc as it rises.
0.0-1.0   the moon rises to (540, 520); teal sky bars and dark sea bars slide in from
          alternating sides; the MERIDIAN rides in on the surface bar and sails to centre.
[storm]   a jagged black storm cloud slams down over the moon; torn in two on the word's end.
[reef]    jagged black rocks rise from the bottom of the sea, and drop away.
[Every]   the ship jumps closer (600 -> 790 px long, outback) so the deck reads.
[lifeboat] eight PAPER lifeboats pop onto her deck, 0.12 s apart: still on board.
6.7-7.8   she tilts bow-down and slides down through the sea bars; 31 tiny PAPER crew
          cut-outs float down after her.
[inquiry] the card turns over to PAPER: black accusing arms slide in from both sides,
          pointing at an empty spot. [someone] the captain pops into it. [blame] they jab.
[chose]   six more arms close the ring. [captain] a RED target ring snaps around him.
13.3-14.0 the arms push in; a black hole opens and the captain falls into it.
OUT (ink, 1.25 s): PAPER field, 12 black arms converging on a black hole (r ~ 205 at
    (540, 1010)) inside the RED ring; the ink bleeds from the hole and the arms first.
"""
import math
from functools import lru_cache

from engine import bass
from engine.core import W, H, clamp, hash01, lerp
from engine.palette import PAPER, RED
from engine.timing import Cue

from ._lib_bass_scenes import (DEEP, FIBER, INK, SEA_HI, SEA_LO, TEAL, draw_meridian, fiber, k, put,
                               rock_polys, sn, storm_polys, tear_region)

HZ = 905.0                       # the horizon: top of the sea
MOON = (540.0, 520.0)
MOON_R = 150.0
TG = (540.0, 1010.0)             # where every hand points (the captain's chest)
CAPT_FOOT = (540.0, 1182.0)
CAPT_H = 340.0
SEA_COLS = [SEA_HI, DEEP, (0.040, 0.140, 0.165), SEA_LO, (0.032, 0.112, 0.135), (0.016, 0.052, 0.066)]


def _words(T):
    return dict(storm=T.at("storm"), storm_end=T.end("storm"), reef=T.at("reef"), reef_end=T.end("reef"),
                every=T.at("every"), life=T.at("lifeboat"), board_end=T.end("board"), inq=T.at("inquiry"),
                some=T.at("someone"),
                blame=T.at("blame"), chose=T.at("chose"), capt=T.at("captain"))


# ----------------------------------------------------------------------------- night card
def _moon(ctx, t):
    """Rises from the lamp spot (an ellipse at (540, 1250)) to (540, 520)."""
    rise = k(t, 0.0, 0.95, "inout3")
    y = lerp(1250.0, MOON[1], rise)
    r = lerp(130.0, MOON_R, k(t, 0.15, 0.8, "out3"))
    ry = lerp(60.0, r, k(t, 0.0, 0.42, "outback"))
    pts = bass.ring_pts((0.0, 0.0), 130.0, seed=41, n=72)
    ctx.save()
    ctx.translate(MOON[0], y)
    ctx.scale(r / 130.0, ry / 130.0)
    bass.fill_polys(ctx, [pts], PAPER)
    ctx.restore()


_SKY = ((-10.0, 236.0), (230.0, 466.0), (460.0, 700.0), (694.0, HZ + 30.0))


def _sky(ctx, t):
    """Four TEAL sky strips slide in from alternating sides (they overlap: no seams)."""
    for i, (y0, y1) in enumerate(_SKY):
        p = k(t, 0.04 + 0.07 * (3 - i), 0.42, "out5")
        if p <= 0:
            continue
        side = 1.0 if i % 2 == 0 else -1.0
        poly = bass.cut_rect(-60.0, y0, W + 60.0, y1, seed=200 + i, amp=1.4)
        put(ctx, [poly], TEAL, (side * (W + 260.0) * (1.0 - p), 0.0))


def _sea_rects():
    return bass.bar_rects((0.0, HZ, W, H + 20.0), 6, "h", (0.62, 1.0, 1.15, 0.9, 1.0, 1.2), 0.0, 5, irregular=0.0)


def _sea_bar(ctx, t, i, rects):
    """Sea bar i slides in (alternating sides) between 0.42 and 1.05 s, then drifts gently."""
    x0, y0, x1, y1 = rects[i]
    p = k(t, 0.42 + 0.085 * i, 0.5, "out5")
    if p <= 0:
        return 0.0
    side = -1.0 if i % 2 == 0 else 1.0
    off = side * (W + 300.0) * (1.0 - p) + 7.0 * math.sin(0.55 * t + i * 1.7) * p
    poly = bass.cut_rect(-60.0, y0 - (2.0 if i else 0.0), W + 60.0, y1 + 1.5, seed=300 + i, amp=1.6)
    put(ctx, [poly], SEA_COLS[i], (off, 0.0))
    return off


def _glade(ctx, t, rows):
    """Broken moonlight on the sea: short PAPER strips under the moon."""
    a = k(t, 1.05, 0.4, "out3")
    if a <= 0:
        return
    ys = (HZ + 40.0, HZ + 104.0, HZ + 180.0, HZ + 272.0, HZ + 384.0, HZ + 520.0)
    for j, y in enumerate(ys):
        if j not in rows:
            continue
        w = (190.0 - 26.0 * j) * (0.72 + 0.28 * math.sin(1.7 * t + j * 1.9)) * a
        x = MOON[0] + 26.0 * sn(6, j) + 9.0 * math.sin(0.8 * t + 2.0 * j)
        h = 13.0 - 1.4 * j
        poly = bass.cut_rect(x - w / 2, y, x + w / 2, y + h, seed=700 + j, amp=0.8)
        bass.fill_polys(ctx, [poly], PAPER, 0.92 - 0.08 * j)


SHIP_L0, SHIP_L1 = 600.0, 790.0                   # length before / after the push on [Every]


def _ship_state(t, W_):
    """(x, y, rot, length) of the Meridian's waterline midpoint."""
    ride = k(t, 0.42, 0.5, "out5")                 # rides in on the surface bar (from the left)
    sail = k(t, 0.42, 1.55, "out3")
    x = lerp(-620.0, 540.0, 0.55 * ride + 0.45 * sail)
    y = HZ + 8.0 + 3.0 * math.sin(1.9 * t)
    rot = 1.1 * math.sin(2.0 * math.pi * t / 3.3)
    L = lerp(SHIP_L0, SHIP_L1, k(t, W_["every"] - 0.04, 0.3, "outback"))
    tilt = k(t, 6.72, 0.5, "inout3")
    slide = k(t, 6.9, 1.0, "in3")
    rot += 23.0 * tilt + 9.0 * slide
    x += 240.0 * slide
    y += 1300.0 * slide + 26.0 * tilt
    return x, y, rot, L


def _crew(ctx, t, W_):
    """31 tiny PAPER crew cut-outs floating down after the ship."""
    kinds = ("man", "worker", "man", "worker", "man")
    top = _sea_rects()[0][3]                     # they slip out from under the surface bar
    for i in range(31):
        t0 = 6.96 + 0.026 * ((i * 17) % 31)
        if t < t0:
            continue
        dt = t - t0
        x0 = 250.0 + 600.0 * ((i * 11) % 31 + 0.5 * hash01(8, i)) / 31.0 + 60.0 * dt
        v = 110.0 + 240.0 * hash01(8, i, 1)
        y = top - 44.0 + v * dt
        x = x0 + 18.0 * math.sin(2.2 * dt + 6.0 * hash01(8, i, 2))
        rot = 40.0 * sn(8, i, 4) + 80.0 * sn(8, i, 5) * dt
        hh = 46.0 * (0.85 + 0.3 * hash01(8, i, 6))
        bass.draw_cutout(ctx, kinds[i % 5], (x, y), hh, PAPER, seed=900 + i, angle=rot,
                         flip=hash01(8, i, 7) < 0.5)


def _storm(ctx, t, W_):
    w0, w1 = W_["storm"], W_["storm_end"]
    if t < w0 - 0.06:
        return
    cloud, tear = storm_polys(3)
    drop = k(t, w0 - 0.06, 0.2, "outback")
    rip = k(t, w1, 0.42, "in3")
    if rip >= 1.0:
        return
    dy = -720.0 * (1.0 - drop)
    if rip <= 0.0:
        put(ctx, [cloud], INK, (0.0, dy))
        return
    for left in (True, False):
        sg = -1.0 if left else 1.0
        dx = sg * 760.0 * rip
        ddy = -260.0 * rip + 30.0 * rip * (0.0 if left else 1.0)
        rot = sg * 22.0 * rip
        ctx.save()
        ctx.translate(560.0 + dx, 300.0 + dy + ddy)
        ctx.rotate(rot * math.pi / 180.0)
        ctx.translate(-560.0, -300.0)
        ctx.new_path()
        bass.path_polys(ctx, [tear_region(tear, left)])
        ctx.clip()
        bass.fill_polys(ctx, [cloud], INK)
        ctx.restore()
        # the torn edge shows the white core of the paper (clipped to the cloud)
        ctx.save()
        ctx.translate(560.0 + dx, 300.0 + dy + ddy)
        ctx.rotate(rot * math.pi / 180.0)
        ctx.translate(-560.0, -300.0)
        ctx.new_path()
        bass.path_polys(ctx, [cloud])
        ctx.clip()
        fiber(ctx, tear, sg, seed=31 + (0 if left else 1), width=7.0, color=FIBER)
        ctx.restore()


def _reef(ctx, t, W_):
    up = k(t, W_["reef"] - 0.05, 0.3, "outback")
    down = k(t, W_["reef_end"], 0.34, "in3")
    if up <= 0 or down >= 1:
        return
    rocks = rock_polys(4)
    for i, r in enumerate(rocks):
        lag = 0.04 * ((i * 3) % 5)
        u1 = k(t, W_["reef"] - 0.05 + lag, 0.3, "outback")
        d1 = k(t, W_["reef_end"] + lag * 0.6, 0.34, "in3")
        dy = 760.0 * (1.0 - u1) + 900.0 * d1
        put(ctx, [r], INK, (0.0, dy))


def _night(ctx, t, W_):
    """The night card (everything before the turn), drawn in screen px."""
    bass.paper_field(ctx, INK)
    _sky(ctx, t)
    _moon(ctx, t)
    _storm(ctx, t, W_)
    rects = _sea_rects()
    for i in range(1, 6):
        _sea_bar(ctx, t, i, rects)
    _glade(ctx, t, (1, 2, 3, 4, 5))
    x, y, rot, L = _ship_state(t, W_)
    boats = [bass.pop(t, W_["life"] + 0.12 * i, 0.22) for i in range(8)]
    _crew(ctx, t, W_)
    if x > -900 and y < H + 700:
        draw_meridian(ctx, (x, y), L, INK, rot=rot, boats=boats, seed=2)
    _sea_bar(ctx, t, 0, rects)                    # the surface bar: the ship sinks behind it
    _glade(ctx, t, (0,))
    _reef(ctx, t, W_)


# ----------------------------------------------------------------------------- paper card
#: the accusing arms: (angle of the arm around TG in deg, knuckle distance, size, wave)
ARMS = [(180.0, 300.0, 300.0, 0), (0.0, 300.0, 300.0, 0), (158.0, 330.0, 290.0, 0), (22.0, 330.0, 290.0, 0),
        (202.0, 330.0, 290.0, 0), (-22.0, 330.0, 290.0, 0),
        (128.0, 360.0, 280.0, 1), (52.0, 360.0, 280.0, 1), (232.0, 360.0, 280.0, 1), (-52.0, 360.0, 280.0, 1),
        (-90.0, 470.0, 270.0, 1), (90.0, 420.0, 270.0, 1)]


@lru_cache(maxsize=16)
def _arm_polys(size, seed):
    """A pointing hand with a long sleeve, knuckles at (0, 0), pointing +x."""
    parts = bass.pointing_hand_pts((0.0, 0.0), size, 0.0, seed=seed)
    kk = size / 152.0
    sleeve = bass.cut([(-90.0 * kk, -12.5 * kk), (-1900.0, -16.0 * kk), (-1900.0, 16.0 * kk), (-90.0 * kk, 12.5 * kk)],
                      seed=seed + 5, amp=1.2, seg=(40.0, 120.0))
    return parts + [bass.orient(sleeve, True)]


def _arms(ctx, t, W_):
    for i, (phi, dist, size, wave) in enumerate(ARMS):
        t0 = (W_["inq"] - 0.02 + 0.07 * i) if wave == 0 else (W_["chose"] - 0.1 + 0.06 * (i - 6))
        p = k(t, t0, 0.38, "out5")
        if p <= 0:
            continue
        jab = k(t, W_["blame"] + 0.015 * i, 0.09, "out3") * (1.0 - k(t, W_["blame"] + 0.11 + 0.015 * i, 0.4, "inout"))
        push = 115.0 * k(t, 13.3 + 0.02 * (i % 4), 0.62, "in3") + 40.0 * max(0.0, t - 14.0)
        creep = 9.0 * clamp(t - W_["blame"] - 0.5, 0.0, W_["chose"] - W_["blame"] - 0.5) if wave == 0 else 0.0
        d = dist + (1100.0 * (1.0 - p)) - 48.0 * jab - push - creep
        a = math.radians(phi)
        cx, cy = TG[0] + d * math.cos(a), TG[1] + d * math.sin(a)
        point = phi + 180.0                              # point back at the target
        flip = math.cos(math.radians(point)) < -1e-3     # keep the thumb up on the left-pointing arms
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(math.radians(point))
        if flip:
            ctx.scale(1.0, -1.0)
        bass.fill_polys(ctx, _arm_polys(size, 60 + i), INK)
        ctx.restore()


def _captain(ctx, t, W_):
    p = bass.pop(t, W_["some"] - 0.04, 0.3)
    if p <= 0:
        return
    fall = k(t, 13.42, 0.5, "in3")
    if fall >= 1.0:
        return
    wob = 2.5 * math.sin(40.0 * (t - W_["blame"])) * math.exp(-6.0 * max(0.0, t - W_["blame"])) \
        if t > W_["blame"] else 0.0
    h = CAPT_H * p * (1.0 - 0.85 * fall)
    foot = (CAPT_FOOT[0], lerp(CAPT_FOOT[1], TG[1] + 40.0, fall))
    bass.draw_cutout(ctx, "captain", foot, h, INK, seed=7, angle=wob + 55.0 * fall)


def _hole(ctx, t):
    o = k(t, 13.3, 0.34, "outback")
    if o <= 0:
        return 0.0
    r = 205.0 * o + 22.0 * max(0.0, t - 14.0)
    bass.disc(ctx, TG, r, INK, seed=19, n=64)
    return r


def _ring(ctx, t, W_, hole_r):
    s = k(t, W_["capt"] - 0.03, 0.22, "outback")
    if s <= 0:
        return
    r = lerp(560.0, 232.0, s)
    if hole_r > 0:
        r = max(r, hole_r + 26.0)
    bass.ring(ctx, TG, r, 20.0, RED, seed=23, n=72)
    s2 = k(t, W_["capt"] + 0.06, 0.2, "outback")
    if s2 > 0 and hole_r < 150:
        bass.ring(ctx, TG, lerp(700.0, 300.0, s2), 9.0, RED, seed=24, n=84)


def _paper(ctx, t, W_):
    bass.paper_field(ctx, PAPER)
    hole_r = _hole(ctx, t)
    _captain(ctx, t, W_)
    _arms(ctx, t, W_)
    _ring(ctx, t, W_, hole_r)


# ----------------------------------------------------------------------------- scene
def render(f, t, T):
    W_ = _words(T)
    bass.bass_scene(f, field=INK, paper=0.7, vignette=0.2)
    turn = W_["inq"] - 0.1                      # the card turns over around [inquiry]
    half = 0.11
    with f.screen() as c:
        if t < turn:
            sx = math.cos(0.5 * math.pi * k(t, turn - half, half, "in"))
            c.save()
            c.translate(W / 2, 0.0)
            c.scale(max(sx, 1e-3), 1.0)
            c.translate(-W / 2, 0.0)
            c.rectangle(0, 0, W, H)
            c.clip()
            _night(c, t, W_)
            c.restore()
        else:
            sx = math.sin(0.5 * math.pi * k(t, turn, half, "out"))
            c.save()
            c.translate(W / 2, 0.0)
            c.scale(max(sx, 1e-3), 1.0)
            c.translate(-W / 2, 0.0)
            c.rectangle(0, 0, W, H)
            c.clip()
            _paper(c, t, W_)
            c.restore()


def cues(T):
    W_ = _words(T)
    return [
        Cue(0.0, "paper moon slides up (soft paper hiss)", -10, dur=0.95),
        Cue(0.42, "paper bars slide in, staggered swishes", -8, dur=0.7),
        Cue(W_["storm"], "paper snap: black storm cloud slams down", -2),
        Cue(W_["storm_end"], "paper tear: the storm is ripped away", -3),
        Cue(W_["reef"], "jagged paper rocks scrape up", -4),
        Cue(W_["reef_end"], "rocks drop away (paper flutter)", -8),
        Cue(W_["every"], "paper slap: the ship jumps closer", -7),
        Cue(W_["life"], "eight small paper pops, 0.12 s apart (lifeboats)", -6, dur=0.96),
        Cue(6.72, "the ship tilts: low wooden groan", -4),
        Cue(6.9, "the ship slides under: deep muffled whoosh", -3, dur=1.0),
        Cue(6.96, "tiny paper figures flutter down", -10, dur=0.9),
        Cue(W_["inq"] - 0.1, "card flip: the field turns to paper", -4),
        Cue(W_["inq"], "paper arms slide in from both sides", -6, dur=0.5),
        Cue(W_["some"], "paper pop: the captain appears", -5),
        Cue(W_["blame"], "arms jab: sharp paper thrust", -3),
        Cue(W_["chose"] - 0.1, "second wave of arms slides in", -6, dur=0.45),
        Cue(W_["capt"], "red ring snaps shut: hard stamp", 0),
        Cue(13.3, "a hole opens: hollow low thud, the figure falls away", -2, dur=0.7),
    ]
