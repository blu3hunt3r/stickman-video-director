"""s08 · THE OTHER SIDE (14.5 s). From window 9 she sees her own window across the street,
lit. The man in the bowler stands in it with her binoculars, waves, and puts her light out.

One continuous shot. Camera(540, 960, 1) at t = 0, so world = screen on every layer.

0.0-0.8   IN (hard cut from s07): over her shoulder (three-quarter back, dim RED collar, a
          cold rim off the glass, a warm one from the show lamp behind her) through window
          9's lower right pane: her building across the rainy street, her window LIT.
0.8-6.3   L18 slow push (log zoom 1 -> 3.6) past her shoulder, through the wet glass, onto
          her window; window 9's sash and her head slide out of frame by ~3 s.
4.3-5.9   a man in a bowler walks into her lit window from the left, behind her lamp, and
          stops in the right half of the window (clear of the muntin).
5.85-6.3  he turns to face us; 6.05-6.4 her binoculars come up to his eyes.
[standing] 6.52 the lenses glint, cold, once.
7.4-7.9   lowers them.   8.0-10.1 raises his free hand and WAVES, slowly (two sweeps).
9.95-11.9 L20 stands there; tilts his head at "windows".
11.95-13.3 L21 looks at her lamp, steps to it, reaches for its pull chain...
[watch]   13.31 pulls: click, her window goes black.
13.6-14.2 two pinpoints in the black window: his eyes glint, once.
OUT       dip to black 0.75 s centred on 14.5: the dark window, rain, camera still creeping.
"""
import math
from functools import lru_cache

import cairo

from engine import atmos, draw
from engine.core import H, clamp, ease, fbm1, lerp
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import PAPER, SHADOWPLAY as PAL
from engine.timing import Cue
from films.shadowplay import cast, sets
from films.shadowplay.sets_base import fill_path
from films.shadowplay.scenes import _lib_s08_s10 as L

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot
COLD = sets.mix(PAL.fog_at(1.0), PAL.rain, 0.45)

# ----------------------------------------------------------------------------- layout
P9 = 1.25                                    # window 9's wall: between her and the street
P_HER = 1.6                                  # her, over whose shoulder we look
NINE = sets.NineWindow((565.0, 1635.0), 1.9)
GX0, GY0, GX1, GY1 = NINE.glass              # 77..1053 x 5..1244 (lower right pane ~576..1023 x 649..1210)
SF = 0.40
WIN = (748.0, 935.0)                         # her window (13), centre (par 1)
HERS = sets.Facade(origin=(WIN[0], WIN[1] + 2730.0 * SF), scale=SF, variant="hers", seed=31)
HER_W = 13
BLOCKS = sets.neighbours(HERS)
SKY = sets.Skyline(x0=-1500.0, x1=2700.0, base_y=1150.0, seed=11, scale=0.36, height=(1500.0, 2700.0), lit=0.05)
WR = HERS.window_rect(HER_W)                 # 697..799 x 871..999
WCX = (WR[0] + WR[2]) / 2
FLOOR = HERS.floor_y(HER_W)
KM = HERS.person_h / 600.0 * 1.15            # canonical -> world for him (close to the glass)
KROOM = HERS.person_h / 1.75                 # world px per metre in her room
OTHERS = {9: 0.36, 17: 0.28, 2: 0.22, 24: 0.25}   # a few other lit windows on her building
FOG = 0.08                                   # facade layer fog (matched by the overlay)

Z_END = 3.6
T_PUSH = (0.8, 6.3)


def _fogged(c):
    return sets.mix(c, PAL.fog_at(FOG), FOG)


def _times(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:                    # noqa: BLE001
            return d
    return dict(standing=at("standing", 6.52), windows=at("windows", 10.30), watch=at("watch", 13.31))


# ----------------------------------------------------------------------------- camera
def camera(t):
    u = L.k_(t, T_PUSH[0], T_PUSH[1] - T_PUSH[0], "inout")
    creep = clamp((t - T_PUSH[1]) / 8.6)
    z = math.exp(lerp(0.0, math.log(Z_END), u)) * (1.0 + 0.09 * ease("out", creep))
    sx = lerp(WIN[0], 540.0, u)              # her window glides to screen centre
    sy = lerp(WIN[1], 930.0, u)
    cam = Camera(WIN[0] - (sx - 540.0) / z, WIN[1] - (sy - 960.0) / z, z)
    return cam.shaken(t, amp=2.4, rot_amp=0.05, freq=0.32, seed=808)


# ----------------------------------------------------------------------------- her (OTS)
HER_K = 3.7
HER_HEAD = (168.0, 1205.0)


@lru_cache(maxsize=1)
def _her_actor():
    a = Actor(cast.HER, None, x=0.0, ground=0.0, facing=-50.0, seed=81)
    a.stand(until=30.0, at=-2.0, idle=0.5)
    a.key("head", [(-2.0, -5.0), (30.0, -5.0)])
    a.key("head_yaw", [(-2.0, 10.0), (30.0, 10.0)])
    a.arm("R", -2.0, 30.0, sh=10.0, abd=8.0, elbow=34.0)
    a.arm("L", -2.0, 30.0, sh=6.0, abd=8.0, elbow=20.0)
    return a


@lru_cache(maxsize=1)
def _her_M():
    sk = _her_actor().skeleton(0.0)
    hx, hy = sk.j["head"]
    return L.place_matrix((HER_HEAD[0] - hx * HER_K, HER_HEAD[1] - hy * HER_K), HER_K, 0.0)


def _draw_her(f, t):
    sx, sy = f.lcam(P_HER).to_screen(HER_HEAD)
    if sx < -900 or sy > H + 1200:
        return
    sk = _her_actor().skeleton(t)
    M = _her_M()
    lk = L.her_look(0.34)
    plain = L.plain_look(lk)
    # the window light only reaches her head and the top of her shoulders: below that she is
    # ink (and so is most of the red coat: only its collar and shoulder catch the light)
    ysh = M.transform_point(*sk.j["shoulder_R"])[1]
    L.occlude_figure(f, P_HER, sk, plain, M)
    with f.layer(par=P_HER, blur=4.0) as c:
        L.draw_skeleton(c, sk, plain, M, color=INK)
        c.push_group()
        L.draw_skeleton(c, sk, lk, M, color=INK)
        pat = c.pop_group()
        g = cairo.LinearGradient(0, ysh - 50.0, 0, ysh + 150.0)
        g.add_color_stop_rgba(0.0, 0, 0, 0, 1.0)
        g.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
        c.set_source(pat)
        c.mask(g)
    with f.light(par=P_HER, blur=3.5) as A:
        A.save()
        A.rectangle(-2000, -2000, 6000, ysh + 2160.0)
        A.clip()
        L.rim(A, sk, plain, M, COLD, 0.55, (-9.0, 7.0))       # the glass, up and right of her
        L.rim(A, sk, plain, M, AMBER, 0.14, (10.0, 3.0))      # the show lamp behind her, left
        A.restore()


# ----------------------------------------------------------------------------- the man
X_STOP = 126.0          # canonical x (window centre = 0): the right half of the window
X_LAMP = -20.0          # where he stands to reach the chain


def _chain(t, W_):
    """Her lamp's pull chain: top and bead (world). The bead dips when he pulls."""
    lx = WR[0] + (WR[2] - WR[0]) * 0.18
    x = lx + 0.13 * KROOM
    top = FLOOR - 1.35 * KROOM
    bead = FLOOR - 1.17 * KROOM
    w0 = W_["watch"] - 0.07
    if t > w0:
        bead += 0.10 * KROOM * math.sin(math.pi * clamp((t - w0) / 0.24))
    return (x, top), (x, bead)


@lru_cache(maxsize=4)
def _him_actor(watch=13.31):
    a = Actor(cast.HIM, None, x=-430.0, ground=0.0, facing=1, seed=21)
    a.stand(until=4.3, at=-2.0, idle=0.3)
    a.walk(to=X_STOP, gait="walk")                     # 4.3 -> ~5.9, behind her lamp
    a.turn(90.0, dur=0.45, at=max(a.cursor, 5.85), via=90.0)
    a.stand(until=12.0, idle=0.25)
    a.walk(to=X_LAMP, gait="stroll", turn=0.3)         # two steps toward the lamp, facing left
    a.stand(until=watch + 0.12, idle=0.1)
    a.turn(90.0, dur=0.42)                             # back to us, in the dark
    a.stand(until=30.0, idle=0.15)
    # binoculars at the chest while he walks in, up to his eyes, lowered
    a.key("arm.L.sh", [(-2.0, 38.0), (6.05, 38.0), (6.40, 80.0, "out3"), (7.40, 80.0), (7.90, 20.0, "inout"),
                       (30.0, 20.0)])
    a.key("arm.L.abd", [(-2.0, 6.0), (6.05, 6.0), (6.40, 44.0, "out3"), (7.40, 44.0), (7.90, 12.0, "inout"),
                        (30.0, 12.0)])
    a.key("arm.L.elbow", [(-2.0, 96.0), (6.05, 96.0), (6.40, 130.0, "out3"), (7.40, 130.0), (7.90, 64.0, "inout"),
                          (30.0, 64.0)])
    a.key("arm.L.grip", [(-2.0, 0.9), (30.0, 0.9)])
    # the wave (front view): upper arm forward, forearm up, the whole arm swaying sideways
    a.key("arm.R.sh", [(-2.0, 34.0), (6.05, 34.0), (6.40, 80.0, "out3"), (7.40, 80.0), (7.90, 8.0, "inout"),
                       (8.0, 8.0), (8.50, 90.0, "inout"), (9.62, 90.0), (10.10, 4.0, "inout"), (12.0, 4.0)],
          fade_out=0.3)
    a.key("arm.R.abd", [(-2.0, 6.0), (6.05, 6.0), (6.40, 44.0, "out3"), (7.40, 44.0), (7.90, 8.0, "inout"),
                        (8.0, 8.0), (8.50, 45.0, "inout"), (8.78, 27.0, "inout"), (9.08, 57.0, "inout"),
                        (9.38, 27.0, "inout"), (9.62, 45.0, "inout"), (10.10, 8.0, "inout"), (12.0, 8.0)], fade_out=0.3)
    a.key("arm.R.elbow", [(-2.0, 100.0), (6.05, 100.0), (6.40, 130.0, "out3"), (7.40, 130.0), (7.90, 14.0, "inout"),
                          (8.0, 14.0), (8.50, 96.0, "inout"), (9.62, 96.0), (10.10, 12.0, "inout"), (12.0, 12.0)],
          fade_out=0.3)
    a.key("arm.R.grip", [(-2.0, 0.9), (7.4, 0.9), (7.9, 0.1), (9.95, 0.1), (10.3, 0.4)])
    # a slow head tilt on "windows"; he looks at her lamp before he goes to it
    a.key("head_roll", [(9.9, 0.0), (10.5, -10.0, "inout"), (11.4, -10.0), (11.9, 0.0, "inout")])
    a.key("head_yaw", [(11.85, 0.0), (12.2, -42.0, "inout"), (12.4, -42.0), (12.6, 0.0, "inout")], fade=0.2)
    # the reach: wrist to the chain bead, then the pull
    def target(t):
        (_, _), (bx, by) = _chain(t, dict(watch=watch))
        return ((bx - WCX) / KM, (by - FLOOR) / KM + 6.0)
    a.reach("R", 12.95, watch + 0.10, target, fade=0.32, grip=0.95)
    return a


def _bino(sk):
    a, b = sk.j["hand_L"], sk.j["hand_R"]
    at = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    y = sk.pose.yaw % 360.0
    return at, ("front" if 50.0 < y < 130.0 else "side")


def _man_M():
    return L.place_matrix((WCX, FLOOR), KM, 0.0)


def _lens_points(sk):
    at, view = _bino(sk)
    M = _man_M()
    sep = 15.0
    return [M.transform_point(at[0] - sep, at[1] - 10.0), M.transform_point(at[0] + sep, at[1] - 10.0)]


def _her_light(t, W_):
    return sets.switch(t, t_on=-30.0, t_off=W_["watch"], kind="bulb", seed=13, level=1.12)


def _glint(t, t0):
    if t < t0 - 0.08 or t > t0 + 1.0:
        return 0.0
    if t < t0:
        return ease("in", (t - (t0 - 0.08)) / 0.08)
    return math.exp(-(t - t0) / 0.15) + 0.22 * math.exp(-((t - t0 - 0.45) / 0.09) ** 2)


# ----------------------------------------------------------------------------- her room
def _lamp(c, lev, t, W_, chain=True):
    """Her floor lamp, left of the window from out here (the set's layout), with the pull
    chain he goes for."""
    x0, y0, x1, y1 = WR
    w = x1 - x0
    k = KROOM
    lx = x0 + w * 0.18
    draw.rect(c, lx - 0.015 * k, FLOOR - 1.37 * k, lx + 0.015 * k, FLOOR)
    draw.fill(c, _fogged(INK))
    shade = [(lx - 0.26 * k, FLOOR - 1.35 * k), (lx + 0.26 * k, FLOOR - 1.35 * k), (lx + 0.19 * k, FLOOR - 1.6 * k),
             (lx - 0.19 * k, FLOOR - 1.6 * k)]
    draw.poly(c, shade)
    draw.fill(c, _fogged(sets.mix(INK, sets.mix(AMBER, HOT, 0.45), 0.82 * clamp(lev))))
    if chain:
        (tx, ty), (bx, by) = _chain(t, W_)
        c.new_path()
        c.move_to(tx, ty)
        c.line_to(bx, by)
        c.set_line_width(0.55)
        draw.rgba(c, _fogged(INK))
        c.stroke()
        draw.circle(c, (bx, by + 0.6), 0.9)
        draw.fill(c, _fogged(INK))


def _chair(c, lev):
    x0, y0, x1, y1 = WR
    w = x1 - x0
    k = KROOM
    cx = x0 + w * 0.74
    fy = FLOOR
    ch = [(cx - 0.44 * k, fy), (cx - 0.48 * k, fy - 0.45 * k), (cx - 0.54 * k, fy - 0.8 * k), (cx - 0.34 * k, fy - 1.05 * k),
          (cx + 0.34 * k, fy - 1.05 * k), (cx + 0.54 * k, fy - 0.8 * k), (cx + 0.48 * k, fy - 0.45 * k), (cx + 0.44 * k, fy)]
    draw.smooth(c, ch, close=True, tension=0.28)
    draw.fill(c, sets.mix(INK, AMBER, 0.10 * clamp(lev)))


def _interior(c, win):
    """Facade interior callback: what stays behind him (the armchair)."""
    if win.mode == "direct":
        _chair(c, win.level)


def _drapes(c, t, lev):
    """Her drapes (tied back) and valance, redrawn over him (they hang at the glass)."""
    lx0, ly0 = HERS.to_local((WR[0], WR[1]))
    lx1, ly1 = HERS.to_local((WR[2], WR[3]))
    w, h = lx1 - lx0, ly1 - ly0
    dim = sets.mix((0.02, 0.02, 0.03), sets.mul(AMBER, 0.20), clamp(lev))
    c.save()
    c.transform(HERS.M)
    for s in (-1, 1):
        xa = lx0 if s < 0 else lx1
        xt = lx0 + w * 0.30 if s < 0 else lx1 - w * 0.30
        xk = lx0 + w * 0.10 if s < 0 else lx1 - w * 0.10
        xb = lx0 + w * 0.22 if s < 0 else lx1 - w * 0.22
        yk = ly0 + h * 0.60
        pts = [(xa, ly0), (xt, ly0), (lerp(xt, xk, 0.6), ly0 + h * 0.36), (xk, yk),
               (lerp(xk, xb, 0.55), ly0 + h * 0.8), (xb, ly1), (xa, ly1)]
        draw.smooth(c, pts, close=True, tension=0.35)
        draw.fill(c, _fogged(dim))
        draw.ellipse(c, (xk - s * 3, yk), 5, 7)
        draw.fill(c, _fogged(INK))
    pts = [(lx0, ly0), (lx1, ly0), (lx1, ly0 + h * 0.08)]
    for k in range(4):
        xa = lx1 - w * k / 4
        xb = lx1 - w * (k + 1) / 4
        pts.append(((xa + xb) / 2, ly0 + h * 0.13))
        pts.append((xb, ly0 + h * 0.08))
    draw.poly(c, pts)
    draw.fill(c, _fogged(INK))
    c.restore()


def _overlay(f, t, W_):
    """Him (and what hangs in front of him) on top of the facade's light pass: the window's
    halo would otherwise wash his silhouette out. 88 % ink keeps a breath of the wet air."""
    lev = _her_light(t, W_)
    a = _him_actor(W_["watch"])
    sk = a.skeleton(t)
    M = _man_M()
    look = L.him_look(0.12)
    vis = clamp(lev * 1.6)
    show_man = t > 4.2 and vis > 0.01
    if show_man:
        L.occlude_figure(f, 1.0, sk, look, M)
    with f.layer(par=1.0) as c:
        c.save()
        c.rectangle(WR[0], WR[1], WR[2] - WR[0], WR[3] - WR[1])
        c.clip()
        if show_man:
            c.push_group()
            L.draw_skeleton(c, sk, look, M, color=INK)
            at, view = _bino(sk)
            c.save()
            c.transform(M)
            if t < 7.95:
                if view == "front":
                    sets.binoculars(c, (at[0], at[1] - 10.0), scale=1.0, view="front")
                else:
                    sets.binoculars(c, (at[0] + 14.0, at[1] - 4.0), angle=0.0, scale=1.0, view="side")
            else:
                h = sk.j["hand_L"]
                sets.binoculars(c, (h[0] + 2.0, h[1] + 30.0), angle=90.0, scale=1.0, view="pair")
            c.restore()
            c.pop_group_to_source()
            c.paint_with_alpha(0.9 * vis)
        if lev > 0.01 or t < W_["watch"] + 0.5:
            _lamp(c, lev, t, W_)
        _drapes(c, t, lev)
        fill_path(c, HERS.d.frames, _fogged(INK), M=HERS.M)
        c.restore()
    # the lamp shade glows
    if lev > 0.01:
        lx = WR[0] + (WR[2] - WR[0]) * 0.18
        with f.emit(par=1.0) as G:
            draw.ellipse(G, (lx, FLOOR - 1.47 * KROOM), 0.22 * KROOM, 0.12 * KROOM)
            draw.fill(G, AMBER, 0.28 * lev)


def _dark_eyes(f, t, a, W_):
    """Two pinpoints in the black window where his face is."""
    sk = _him_actor(W_["watch"]).skeleton(t)
    M = _man_M()
    e1, e2, r, w, front = L.FG.eye_points(sk, L.him_look())
    pts = [M.transform_point(*e1), M.transform_point(*e2)]
    rr = max(0.55, r * KM * 1.1)
    with f.layer(par=1.0) as c:
        for p in pts:
            draw.ellipse(c, p, rr, rr * 0.75)
            draw.fill(c, (1.0, 1.0, 0.97), a)
    with f.emit(par=1.0) as G:
        for p in pts:
            draw.glow_disc(G, p, rr * 8.0, (1.0, 1.0, 0.97), 0.6 * a)


# ----------------------------------------------------------------------------- outside
def _outside(f, t, W_):
    lev = _her_light(t, W_)
    lit = {HER_W: lev}
    lit.update(OTHERS)
    sets.night_sky(f, t, glow_y=HERS.top_y + 40.0, spread=300.0, par=0.25, clouds=0.8)
    SKY.draw(f, t, layer=dict(par=0.45, blur=4.0, fog=0.72))
    f.haze(PAL.fog_at(0.9), 0.24, y0=HERS.top_y - 260, y1=HERS.top_y + 900, feather=500, par=0.6)
    sets.draw_blocks(f, t, BLOCKS, layer=dict(par=1.0, fog=0.42, blur=1.0), light=0.55)
    HERS.draw(f, t, layer=dict(par=1.0, fog=FOG, blur=0.0), lit=lit, interiors={HER_W: _interior},
              emit=0.5, halo=0.9)
    _overlay(f, t, W_)
    g = _glint(t, W_["standing"])
    if g > 0.01:
        sk = _him_actor(W_["watch"]).skeleton(t)
        sets.binocular_glints(f, _lens_points(sk), scale=0.5, level=g, par=1.0)
    eyes = L.env(t, W_["watch"] + 0.30, W_["watch"] + 0.48, W_["watch"] + 0.66, W_["watch"] + 0.92, "inout")
    if eyes > 0.01:
        _dark_eyes(f, t, eyes, W_)
    # rain in the street canyon, catching her window's light
    lights = [atmos.Glow(((WR[0] + WR[2]) / 2, (WR[1] + WR[3]) / 2 + 20.0), 110.0, 0.9 * lev, AMBER)]
    for i, l in OTHERS.items():
        r = HERS.window_rect(i)
        lights.append(atmos.Glow(((r[0] + r[2]) / 2, (r[1] + r[3]) / 2), 80.0, 0.45 * l, AMBER))
    atmos.rain(f, density=0.85, speed=2100.0, angle=6.0, t=t, seed=88, alpha=0.95, lit=lights, lit_gain=2.4,
               bands=(dict(par=0.7, n=380, w=1.0, len=0.7, speed=0.65, a=0.12, blur=0.0),
                      dict(par=1.0, n=230, w=1.0, len=1.0, speed=1.0, a=0.20, blur=0.0),
                      dict(par=1.12, n=70, w=1.4, len=1.3, speed=1.2, a=0.15, blur=1.0)))


# ----------------------------------------------------------------------------- window 9
def _sheet(c, t):
    """The show sheet, pulled aside: bunched on the wire right of the glass."""
    s = NINE.s
    y0 = GY0 - 44 * s
    x0 = GX1 + 30 * s
    sway = 3.0 * s * fbm1(t * 0.3, 41)
    pts = [(x0 - 20 * s, y0), (x0 + 160 * s, y0 - 2 * s), (x0 + 175 * s + sway, y0 + 300 * s),
           (x0 + 168 * s + sway * 1.5, y0 + 700 * s), (x0 + 185 * s + sway * 2, NINE.floor_y - 30 * s),
           (x0 + 30 * s + sway * 2, NINE.floor_y - 40 * s), (x0 + 5 * s + sway, y0 + 640 * s), (x0 - 12 * s, y0 + 260 * s)]
    draw.smooth(c, pts, close=True, tension=0.35)


def _window9(f, t):
    NINE.draw(f, t, layer=dict(par=P9, blur=2.0), rain=0.55, room_light=0.55, condensation=0.0, outside_light=1.0)
    with f.layer(par=P9, blur=2.0) as c:
        _sheet(c, t)
        draw.fill(c, sets.mix(INK, sets.mix(PAPER, AMBER, 0.4), 0.13))


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    W_ = _times(T)
    f.set_camera(camera(t))
    _outside(f, t, W_)
    _window9(f, t)
    _draw_her(f, t)
    f.post["bloom"] = 0.22


def cues(T):
    W_ = _times(T)
    return [
        Cue(4.35, "across the street: a floorboard, barely (he walks into her window)", gain_db=-22, pan=0.25),
        Cue(W_["standing"], "binocular glint: a thin cold shimmer", gain_db=-10, pan=0.1),
        Cue(W_["watch"], "light switch click, far, across the street", gain_db=-6, pan=0.1),
    ]
