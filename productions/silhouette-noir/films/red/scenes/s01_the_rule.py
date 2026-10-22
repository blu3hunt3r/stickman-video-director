"""s01 · THE RULE: Saul Bass opening, the path seen from above (9.0 s, flat graphic).

0.05-1.35 PAPER field. A black cut-paper line (the path, top-down, 18 px) draws itself from
          the top of the frame to the bottom, winding gently down the centre.
[child]   a small RED triangle (the hood seen from above) pops in at the top of the line and
          glides down along it, its point leading.
[rule]    short black stakes pop up along both sides of the line, top to bottom (outback).
[Never]   black thicket blots grow beside the path; pairs of white eyes open in them.
[leave]   the triangle stops.          [path] the eyes blink out.
7.30-7.95 the plane turns: the view rotates a quarter turn and the path straightens into a
          ground line at y 1500 (the travel direction becomes screen right). The right-hand
          stakes stand up as posts, the right-hand thickets settle as bushes, and the black
          ground grows down from the line. 7.95-8.30 the triangle rights itself and becomes the
          girl's hood: legs and the basket pop in under it, feet on the line at x 540.
OUT (ink, 1.25 s): PAPER sky above y 1500, black ground below; ink bushes and posts on the
    line; the girl (hood cut-out, 330 px, RED cloak) standing at (540, 1500).
"""
import math
from functools import lru_cache

from engine import bass
from engine.core import W, H, clamp, ease, hash01, lerp
from engine.palette import PAPER, RED, RED_FILM
from engine.timing import Cue

INK = RED_FILM.ink
EYE = (1.0, 1.0, 0.97)
CX = 540.0
Y_STOP = 980.0                    # where the triangle stops (plane y)
GROUND = (540.0, 1500.0)          # where that point lands after the turn
HOOD_H = 330.0
STAKE_GAP = 118.0


def _k(t, t0, dur, e="out3"):
    if t <= t0:
        return 0.0
    if t >= t0 + dur:
        return 1.0
    return ease(e, (t - t0) / dur)


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


def _words(T):
    return dict(child=T.at("child"), rule=T.at("rule"), never=T.at("never"), leave=T.at("leave"),
                path=T.at("path"))


# ----------------------------------------------------------------------------- the path
def _meander(y):
    return 92.0 * math.sin(y / 265.0 + 0.4) + 30.0 * math.sin(y / 118.0 + 1.3)


def _px(y, straight):
    return CX + (1.0 - straight) * (_meander(y) - _meander(Y_STOP) * 0.0)


def _tangent(y, straight):
    d = 2.0
    return math.atan2(2 * d, _px(y + d, straight) - _px(y - d, straight))   # angle of (dx, dy)


def _path_pts(straight, y0=-60.0, y1=H + 60.0, step=12.0):
    n = int((y1 - y0) / step)
    return [(_px(y0 + i * step, straight), y0 + i * step) for i in range(n + 1)]


# ----------------------------------------------------------------------------- pieces
@lru_cache(maxsize=8)
def _thicket(seed, rx, ry):
    """A thicket: three or four overlapping bristly lobes (plane units: x = across the path,
    y = along it), centred on (0, 0). Turned upright it reads as a low bush."""
    lobes = []
    m = 3 + int(hash01(seed, 9) * 2)
    for q in range(m):
        f = (q / (m - 1.0)) * 2.0 - 1.0
        cy = f * ry * 0.48
        cx = rx * (0.12 * _sn(seed, q, 1) - 0.18 * (1.0 - abs(f)))
        lx = rx * (0.62 + 0.25 * hash01(seed, q, 2)) * (1.0 - 0.25 * abs(f))
        ly = ry * (0.36 + 0.12 * hash01(seed, q, 3))
        n = 34
        pts = []
        for i in range(n):
            a = 2 * math.pi * (i + 0.3 * _sn(seed, q, i, 5)) / n
            r = 1.0 + (0.17 if i % 2 else -0.05) * (0.5 + hash01(seed, q, i, 4))
            if i % 2 and hash01(seed, q, i, 6) < 0.22:
                r += 0.22                                      # an odd long thorn
            pts.append((cx + lx * r * math.cos(a), cy + ly * r * math.sin(a)))
        lobes.append(bass.orient(bass.cut(pts, seed=seed * 7 + q, amp=1.0, seg=(10.0, 26.0)), True))
    return lobes


#: thickets: (plane y, side (+1 right / -1 left), offset from the line, rx (across), ry (along))
THICKETS = ((690.0, -1, 190.0, 92.0, 190.0), (800.0, 1, 165.0, 70.0, 190.0), (1100.0, -1, 200.0, 96.0, 200.0),
            (1180.0, 1, 160.0, 66.0, 170.0), (560.0, 1, 200.0, 60.0, 150.0), (1320.0, -1, 190.0, 80.0, 150.0))


def _hood_parts():
    parts = bass.cutout_parts("hood", 3)
    cloak = [p for r, p in parts if r == "accent"]
    body = [p for r, p in parts if r != "accent"]
    return cloak, body


def _hood_y(t, W_):
    """Plane y of the triangle: pops at the top of the line, glides down, stops on [leave]."""
    t0, t1 = W_["child"] + 0.1, W_["leave"]
    u = clamp((t - t0) / (t1 - t0))
    u = u * u * (3.0 - 2.0 * u) * 0.25 + u * 0.75          # a gentle start, still moving at the stop
    return lerp(70.0, Y_STOP, u)


# ----------------------------------------------------------------------------- scene
def render(f, t, T):
    W_ = _words(T)
    bass.bass_scene(f, field=PAPER, paper=0.75, vignette=0.14)
    turn = _k(t, 7.3, 0.65, "inout3")
    straight = _k(t, 7.25, 0.6, "inout3")
    stand = _k(t, 7.5, 0.5, "out3")               # posts stand up, bushes settle
    pstop = (_px(Y_STOP, straight), Y_STOP)
    cpos = (lerp(pstop[0], GROUND[0], turn), lerp(pstop[1], GROUND[1], turn))
    with f.screen() as c:
        c.save()
        c.translate(*cpos)
        c.rotate(math.radians(-90.0 * turn))
        c.translate(-pstop[0], -pstop[1])
        _plane(c, f, t, W_, straight, stand, turn)
        c.restore()
        g = _k(t, 7.78, 0.3, "out5")              # the black ground slides up to the line
        if g > 0:
            y0 = lerp(H + 40.0, GROUND[1] - 1.0, g)
            bass.fill_polys(c, [bass.cut_rect(-40.0, y0, W + 40.0, H + 400.0, seed=21, amp=1.2)], INK)
        _hood(c, f, t, W_, straight, turn, pstop, cpos)


def _plane(c, f, t, W_, straight, stand, turn):
    gone = _k(t, 7.3, 0.4, "in3")                 # the left-hand side folds away under the ground
    # thickets: grow on [Never]; the right-hand ones settle onto the line as bushes
    for j, (yp, side, off, rx, ry) in enumerate(THICKETS):
        g = _k(t, W_["never"] - 0.04 + 0.08 * j, 0.32, "outback")
        if side < 0:
            g *= 1.0 - gone
        if g <= 0:
            continue
        o = lerp(off, rx * 0.5, stand) if side > 0 else off
        x0 = _px(yp, straight)
        cx = x0 + side * o
        c.save()
        c.translate(cx, yp)
        c.scale(g, g)
        bass.fill_polys(c, _thicket(11 + j, rx, ry), INK)
        c.restore()
        _eyes(c, f, t, W_, j, (cx, yp), side)
    # stakes on both sides: pop on [rule], top to bottom
    n = 0
    y = 40.0
    while y < H:
        far = abs(y - Y_STOP) < 80.0
        for side in (-1, 1):
            if far and side > 0:
                continue
            p = bass.pop(t, W_["rule"] - 0.03 + 0.022 * n, 0.24)
            if side < 0:
                p *= 1.0 - gone
            if p <= 0:
                continue
            x = _px(y, straight)
            a = _tangent(y, straight)
            nx, ny = math.cos(a - math.pi / 2), math.sin(a - math.pi / 2)   # plane +x side (sky, once turned)
            if side < 0:
                nx, ny = -nx, -ny
            inner = lerp(40.0, 8.0, stand) if side > 0 else 40.0
            L = (lerp(34.0, 150.0, stand) if side > 0 else 34.0) * p
            wdt = lerp(11.0, 14.0, stand) if side > 0 else 11.0
            ax, ay = x + nx * inner, y + ny * inner
            bx, by = x + nx * (inner + L), y + ny * (inner + L)
            tx, ty = -ny * wdt / 2.0, nx * wdt / 2.0
            bass.fill_polys(c, [bass.orient([(ax + tx, ay + ty), (bx + tx, by + ty), (bx - tx, by - ty),
                                             (ax - tx, ay - ty)], True)], INK)
        n += 1
        y += STAKE_GAP
    # the path line itself (drawn on 0.05-1.35, top to bottom)
    u = _k(t, 0.05, 1.3, "inout")
    band = bass.line_pts(_path_pts(straight), 18.0, u, seed=7)
    if band:
        bass.fill_polys(c, [band], INK)


def _eyes(c, f, t, W_, j, at, side):
    """A pair of white eyes in thicket j: open after [Never], blink out on [path]."""
    t0 = W_["never"] + 0.22 + 0.1 * ((j * 3) % 6)
    op = _k(t, t0, 0.12, "out3") * (1.0 - _k(t, W_["path"] + 0.035 * j, 0.07, "in"))
    if op <= 0.01:
        return
    ex, ey = at[0] - side * 18.0, at[1] - 22.0 + 30.0 * _sn(5, j)
    for d in (-13.0, 13.0):
        c.save()
        c.translate(ex + d, ey)
        c.scale(5.8, 4.4 * op)
        c.arc(0.0, 0.0, 1.0, 0.0, 2 * math.pi)
        c.restore()
        c.set_source_rgb(*EYE)
        c.fill()
    with f.emit() as g:
        for d in (-13.0, 13.0):
            g.arc(ex + d, ey, 16.0, 0.0, 2 * math.pi)
            g.set_source_rgba(*EYE, 0.45 * op)
            g.fill()


def _hood(c, f, t, W_, straight, turn, pstop, cpos):
    """The RED triangle: top-down hood gliding down the path, then the girl on the ground."""
    pop = bass.pop(t, W_["child"] - 0.03, 0.26)
    if pop <= 0:
        return
    cloak, body = _hood_parts()
    yp = _hood_y(t, W_)
    xp = _px(yp, straight)
    tang = math.degrees(_tangent(yp, straight))           # direction of travel (down the path)
    stop_rock = bass.settle(t, W_["leave"], amp=7.0, freq=3.2, decay=7.0)
    # plane -> screen for the hood's own position
    a = math.radians(-90.0 * turn)
    dx, dy = xp - pstop[0], yp - pstop[1]
    sx = cpos[0] + dx * math.cos(a) - dy * math.sin(a)
    sy = cpos[1] + dx * math.sin(a) + dy * math.cos(a)
    ang_top = tang + 90.0 + stop_rock - 90.0 * turn       # the cloak's tip leads (local tip = up)
    right = _k(t, 7.95, 0.36, "outback")                  # rights itself, grows into the girl
    k_top, k_side = 0.85, HOOD_H / 100.0
    k = lerp(k_top, k_side, right) * pop
    ang = lerp(ang_top, 0.0, right)
    # the cloak's centre (local (0, -62)) travels from the path to above the feet at GROUND
    cen = (lerp(sx, GROUND[0], right), lerp(sy, GROUND[1] - 62.0 * k_side, right))
    sway = right * 1.3 * math.sin(2.0 * math.pi * (t - 8.3) / 2.3) * _k(t, 8.3, 0.6, "inout")   # a breath of wind
    c.save()
    c.translate(*cen)
    c.rotate(math.radians(ang))
    c.scale(k, k)
    c.translate(0.0, 62.0)
    c.translate(0.0, -25.0)                       # the cloak sways about its hem
    c.rotate(math.radians(sway))
    c.translate(0.0, 25.0)
    bass.fill_polys(c, cloak, RED)
    c.restore()
    legs = bass.pop(t, 8.12, 0.24)
    if legs > 0:
        c.save()
        c.translate(GROUND[0], GROUND[1] + 2.0)
        c.scale(k_side * legs, k_side * legs)
        bass.fill_polys(c, body, INK)
        c.restore()


def cues(T):
    W_ = _words(T)
    return [
        Cue(0.05, "a black paper line is drawn down the page (soft brush / paper slide)", -9, dur=1.3),
        Cue(W_["child"], "paper pop: the red hood appears", -6),
        Cue(W_["child"] + 0.1, "small soft footsteps on snow, receding along the path", -14, dur=4.3),
        Cue(W_["rule"], "a row of wooden stakes knocked in, quick taps top to bottom", -7, dur=1.0),
        Cue(W_["never"], "thickets rustle and bristle", -6, dur=0.6),
        Cue(W_["never"] + 0.22, "eyes open in the dark: a low breath", -10, dur=0.6),
        Cue(W_["leave"], "the footsteps stop", -12),
        Cue(W_["path"], "the eyes blink out: soft tick", -12),
        Cue(7.30, "the page turns over to a side view: paper whoosh", -6, dur=0.65),
        Cue(7.78, "the ground slams up into place: deep paper thump", -4),
        Cue(7.95, "paper pop: the hood stands up, the girl", -6),
    ]
