"""s08 · THE OTHER SIDE (14.5 s). From window 9 she sees her own window across the street,
lit. The man in the bowler stands in it with her binoculars, waves, and puts her light out.

One continuous shot. Camera(540, 960, 1) at t = 0, so world = screen on every layer.

0.0-0.8   IN (hard cut from s07): over her shoulder (three-quarter back, dim RED collar, rim
          light off the glass) through window 9's lower right pane: her building across the
          rainy street, her window 13 LIT in the middle of the pane.
0.8-6.3   L18 slow push (log zoom 1 -> 2.95) past her shoulder, through the wet glass, onto
          her window; window 9's sash and her head slide out of frame by ~2.5 s.
4.3-5.9   a man in a bowler walks into her lit window from the left, past her lamp,
          holding something at his chest.
5.9-6.35  he turns to face us. 6.05-6.4 her binoculars come up to his eyes.
[standing] 6.52  the lenses glint (cold, once).
7.4-7.9   lowers them to his waist.  8.0-9.4 raises his free arm and WAVES, slowly, twice.
9.4-11.1  L20 he just stands there; tilts his head at "windows".
11.6-13.31 L21 he reaches sideways for her lamp's pull chain, holds...
[watch]   13.31 pulls it: click, her window goes black.
13.55-14.1 two pinpoints in the black window: his eyes glint, once.
OUT       dip to black 0.75 s (centred on 14.5; the frame holds the dark window, camera
          creeping in, rain).
"""
import math
from functools import lru_cache

import cairo

from engine import atmos, draw
from engine.core import W, H, clamp, ease, fbm1, hash01, lerp, smoothstep
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import PAPER, SHADOWPLAY as PAL
from engine.timing import Cue
from films.shadowplay import cast, sets
from films.shadowplay.scenes import _lib_s08_s10 as L

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot
COLD = sets.mix(PAL.fog_at(1.0), PAL.rain, 0.45)

# ----------------------------------------------------------------------------- layout
P9 = 1.25                                    # window 9's wall: between her and the street
P_HER = 1.65                                 # her, over whose shoulder we look
NINE = sets.NineWindow((540.0, 1523.0), 1.6)
GX0, GY0, GX1, GY1 = NINE.glass              # 129..951 x 150..1193
SF = 0.40
WIN = (748.0, 935.0)                         # her window (13), centre at t = 0 (par 1)
HERS = sets.Facade(origin=(WIN[0], WIN[1] + 2730.0 * SF), scale=SF, variant="hers", seed=3)
HER_W = sets.HER_WINDOW if hasattr(sets, "HER_WINDOW") else 13
BLOCKS = sets.neighbours(HERS)
SKY = sets.Skyline(x0=-1500.0, x1=2700.0, base_y=1250.0, seed=11, scale=0.36, height=(1500.0, 2700.0), lit=0.05)
WR = HERS.window_rect(HER_W)
KM = HERS.person_h / 600.0                   # canonical (600 px = 1.75 m) -> world, in her room
FLOOR = HERS.floor_y(HER_W)
OTHERS = {9: 0.55, 17: 0.42, 2: 0.30, 24: 0.35}   # a few other lit windows on her building

Z_END = 2.95                                 # push target zoom (window ~300 x 380 px)
T_PUSH = (0.8, 6.3)
T_OFF = 13.31                                # fallback for [watch]


def _times(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:                    # noqa: BLE001
            return d
    return dict(standing=at("standing", 6.52), windows=at("windows", 10.30), watch=at("watch", T_OFF),
                women=at("women", 9.84))


# ----------------------------------------------------------------------------- camera
def camera(t, T=None):
    u = L.k_(t, T_PUSH[0], T_PUSH[1] - T_PUSH[0], "inout")
    creep = clamp((t - T_PUSH[1]) / 8.6)
    z = math.exp(lerp(0.0, math.log(Z_END), u)) * (1.0 + 0.085 * ease("out", creep))
    # her window glides from its spot in the pane to screen centre (a touch high for headroom)
    sx = lerp(WIN[0], 540.0, u)
    sy = lerp(WIN[1], 948.0, u)
    cx = WIN[0] - (sx - 540.0) / z
    cy = WIN[1] - (sy - 960.0) / z
    cam = Camera(cx, cy, z)
    return cam.shaken(t, amp=2.6, rot_amp=0.06, freq=0.32, seed=808)


# ----------------------------------------------------------------------------- her (OTS)
HER_K = 2.45                                 # canonical -> world at par P_HER


@lru_cache(maxsize=1)
def _her_actor():
    a = Actor(cast.HER, None, x=0.0, ground=0.0, facing=-52.0, seed=81)
    a.stand(until=30.0, at=-2.0, idle=0.6)
    a.key("head", [(-2.0, 7.0), (30.0, 7.0)])
    a.key("head_yaw", [(-2.0, 14.0), (30.0, 14.0)])
    a.arm("R", -2.0, 30.0, sh=8.0, abd=10.0, elbow=30.0)
    a.arm("L", -2.0, 30.0, sh=4.0, abd=8.0, elbow=18.0)
    return a


@lru_cache(maxsize=1)
def _her_anchor():
    """World foot point so that her head sits at (238, 1188) (at t = 0, zoom 1)."""
    sk = _her_actor().skeleton(0.0)
    hx, hy = sk.j["head"]
    return (238.0 - hx * HER_K, 1188.0 - hy * HER_K)


def _her_M():
    return L.place_matrix(_her_anchor(), HER_K, 0.0)


def _draw_her(f, t):
    cam = f.lcam(P_HER)
    # skip once she is off screen
    hx, hy = 238.0, 1188.0
    sx, sy = cam.to_screen((hx, hy))
    if sx < -700 or sy > H + 900:
        return
    a = _her_actor()
    sk = a.skeleton(t)
    M = _her_M()
    lk = L.her_look(0.42)
    plain = L.plain_look(lk)
    L.occlude_figure(f, P_HER, sk, plain, M)
    with f.layer(par=P_HER, blur=3.5) as Lc:
        L.draw_skeleton(Lc, sk, lk, M, color=INK)
    # two-tone rim: cold window light on her right edge, warm show lamp behind on her left
    with f.light(par=P_HER, blur=3.0) as A:
        L.rim(A, sk, plain, M, COLD, 0.55, (-7.0, 4.0))
        L.rim(A, sk, plain, M, AMBER, 0.18, (8.0, 2.0))


# ----------------------------------------------------------------------------- the man
@lru_cache(maxsize=1)
def _him_actor():
    a = Actor(cast.HIM, None, x=-540.0, ground=0.0, facing=1, seed=21)
    a.stand(until=4.3, at=-2.0, idle=0.4)
    a.walk(to=10.0, gait="walk")                       # 4.3 -> ~5.9, past her lamp
    t_turn = max(a.cursor, 5.85)
    a.turn(90.0, dur=0.45, at=t_turn, via=90.0)        # faces us
    a.stand(until=30.0, idle=0.25)
    # binoculars held at the chest while he walks in
    a.arm("L", -2.0, 6.05, sh=38.0, abd=6.0, elbow=96.0, grip=0.9)
    a.arm("R", -2.0, 6.05, sh=34.0, abd=6.0, elbow=100.0, grip=0.9)
    # up to his eyes (front view: elbows out)
    a.key("arm.L.sh", [(6.05, 38.0), (6.40, 78.0, "out3"), (7.40, 78.0), (7.90, 20.0, "inout"), (30.0, 20.0)])
    a.key("arm.L.abd", [(6.05, 6.0), (6.40, 46.0, "out3"), (7.40, 46.0), (7.90, 14.0, "inout"), (30.0, 14.0)])
    a.key("arm.L.elbow", [(6.05, 96.0), (6.40, 128.0, "out3"), (7.40, 128.0), (7.90, 70.0, "inout"), (30.0, 70.0)])
    a.key("arm.R.sh", [(6.05, 34.0), (6.40, 78.0, "out3"), (7.40, 78.0), (7.90, 10.0, "inout"), (8.0, 8.0),
                       (8.55, 40.0, "inout"), (9.35, 40.0), (9.95, 4.0, "inout"), (12.05, 4.0), (12.65, 22.0, "inout"),
                       (13.20, 22.0), (13.31, 14.0, "in"), (13.60, 10.0, "out"), (30.0, 6.0)])
    a.key("arm.R.abd", [(6.05, 6.0), (6.40, 46.0, "out3"), (7.40, 46.0), (7.90, 8.0, "inout"), (8.0, 8.0),
                        (8.55, 128.0, "inout"), (8.85, 112.0, "inout"), (9.15, 132.0, "inout"), (9.45, 114.0, "inout"),
                        (9.95, 8.0, "inout"), (12.05, 8.0), (12.65, 58.0, "inout"), (13.20, 58.0), (13.31, 50.0, "in"),
                        (13.60, 30.0, "out"), (30.0, 10.0)])
    a.key("arm.R.elbow", [(6.05, 100.0), (6.40, 128.0, "out3"), (7.40, 128.0), (7.90, 14.0, "inout"), (8.55, 26.0),
                          (9.45, 26.0), (9.95, 12.0, "inout"), (12.05, 12.0), (12.65, 28.0, "inout"), (30.0, 28.0)])
    # a slow head tilt on "windows", a look at the lamp before he reaches
    a.key("head_roll", [(9.9, 0.0), (10.5, -9.0, "inout"), (11.4, -9.0), (11.9, 0.0, "inout")])
    a.key("head_yaw", [(11.9, 0.0), (12.3, -38.0, "inout"), (13.10, -38.0), (13.45, 0.0, "inout")])
    return a


def _bino_view(sk):
    y = sk.pose.yaw % 360.0
    return "front" if 45.0 < y < 135.0 else "side"


def _bino_at(sk):
    a, b = sk.j["hand_L"], sk.j["hand_R"]
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def _man_M(win_cx):
    return L.place_matrix((win_cx, FLOOR), KM, 0.0)


def _chain_pt(win):
    """Her lamp's pull chain bead (world): just right of the shade, ~1.15 m up."""
    x0, y0, x1, y1 = win.rect
    w = x1 - x0
    lx = x0 + w * 0.18
    k = win.person_h / 1.75
    return (lx + 0.13 * k, win.floor_y - 1.17 * k), (lx + 0.13 * k, win.floor_y - 1.35 * k)


def _interior(T, W_):
    base = sets.her_room_interior(lamp=1.0, man=None, chair=True)

    def fn(ctx, win):
        t = win.t
        base(ctx, win)
        if win.mode != "direct":
            return
        # the lamp's pull chain
        (bx, by), (tx, ty) = _chain_pt(win)
        pull = 0.0
        if t > W_["watch"] - 0.06:
            pull = math.sin(math.pi * clamp((t - (W_["watch"] - 0.06)) / 0.22))
        by += pull * 0.06 * win.person_h
        ctx.new_path()
        ctx.move_to(tx, ty)
        ctx.line_to(bx, by)
        ctx.set_line_width(max(0.5, 0.004 * win.person_h))
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        draw.circle(ctx, (bx, by + 0.012 * win.person_h), 0.012 * win.person_h)
        draw.fill(ctx, INK)
        # the man
        a = _him_actor()
        if t < 4.25:
            return
        sk = a.skeleton(t)
        M = _man_M(win.cx)
        L.draw_skeleton(ctx, sk, L.him_look(0.15), M, color=INK)
        if t < 7.95:
            ctx.save()
            ctx.transform(M)
            view = _bino_view(sk)
            at = _bino_at(sk)
            if view == "front":
                sets.binoculars(ctx, (at[0], at[1] - 8.0), scale=1.05, view="front")
            else:
                sets.binoculars(ctx, (at[0] + 12.0, at[1]), angle=0.0, scale=1.05, view="side")
            ctx.restore()
        elif t < 30.0:
            # lowered: hanging from his left hand
            ctx.save()
            ctx.transform(M)
            h = sk.j["hand_L"]
            sets.binoculars(ctx, (h[0], h[1] + 26.0), angle=90.0, scale=1.05, view="pair")
            ctx.restore()
    return fn


def _lens_points(t):
    """World lens centres of the binoculars at his eyes (front view)."""
    sk = _him_actor().skeleton(t)
    M = _man_M((WR[0] + WR[2]) / 2)
    at = _bino_at(sk)
    sep = 15.0 * 1.05
    return [M.transform_point(at[0] - sep, at[1] - 8.0), M.transform_point(at[0] + sep, at[1] - 8.0)]


def _her_light(t, W_):
    return sets.switch(t, t_on=-30.0, t_off=W_["watch"], kind="bulb", seed=13)


def _glint(t, t0):
    if t < t0 - 0.08 or t > t0 + 0.9:
        return 0.0
    if t < t0:
        return ease("in", (t - (t0 - 0.08)) / 0.08)
    return math.exp(-(t - t0) / 0.16) + 0.25 * math.exp(-((t - t0 - 0.42) / 0.08) ** 2)


# ----------------------------------------------------------------------------- outside
def _outside(f, t, T, W_):
    lev = _her_light(t, W_)
    lit = {HER_W: lev}
    lit.update(OTHERS)
    sets.night_sky(f, t, glow_y=HERS.top_y + 40.0, spread=300.0, par=0.25, clouds=0.8)
    SKY.draw(f, t, layer=dict(par=0.45, blur=4.0, fog=0.72))
    f.haze(PAL.fog_at(0.9), 0.26, y0=HERS.top_y - 260, y1=HERS.top_y + 900, feather=500, par=0.6)
    sets.draw_blocks(f, t, BLOCKS, layer=dict(par=1.0, fog=0.30, blur=1.0))
    HERS.draw(f, t, layer=dict(par=1.0, fog=0.10, blur=0.6), lit=lit, interiors={HER_W: _interior(T, W_)},
              emit=0.55, halo=0.9)
    # the binocular glint, his eyes after the light goes out
    g = _glint(t, W_["standing"])
    if g > 0.01:
        sets.binocular_glints(f, _lens_points(t), scale=0.55, level=g, par=1.0)
    eyes = L.env(t, W_["watch"] + 0.26, W_["watch"] + 0.42, W_["watch"] + 0.62, W_["watch"] + 0.86, "inout")
    if eyes > 0.01:
        _dark_eyes(f, t, eyes)
    # rain in the street canyon, lit by her window
    win_c = ((WR[0] + WR[2]) / 2, (WR[1] + WR[3]) / 2)
    lights = [atmos.Glow(win_c, 120.0, 0.9 * lev, AMBER)]
    for i, l in OTHERS.items():
        r = HERS.window_rect(i)
        lights.append(atmos.Glow(((r[0] + r[2]) / 2, (r[1] + r[3]) / 2), 90.0, 0.5 * l, AMBER))
    atmos.rain(f, density=0.85, speed=2100.0, angle=6.0, t=t, seed=88, alpha=0.95, lit=lights, lit_gain=2.4,
               bands=(dict(par=0.7, n=380, w=1.0, len=0.7, speed=0.65, a=0.12, blur=0.0),
                      dict(par=1.0, n=230, w=1.0, len=1.0, speed=1.0, a=0.20, blur=0.0),
                      dict(par=1.12, n=70, w=1.4, len=1.3, speed=1.2, a=0.16, blur=1.0)))
    f.haze(PAL.fog_at(1.0), 0.08, y0=GY0, y1=GY1, feather=260)


def _dark_eyes(f, t, a):
    """Two pinpoints in the black window where his face is."""
    sk = _him_actor().skeleton(t)
    M = _man_M((WR[0] + WR[2]) / 2)
    e1, e2, r, w, front = L.FG.eye_points(sk, L.him_look())
    pts = [M.transform_point(*e1), M.transform_point(*e2)]
    rr = max(0.9, r * KM * 1.25)
    with f.layer(par=1.0) as c:
        for p in pts:
            draw.ellipse(c, p, rr, rr * 0.8)
            draw.fill(c, (1.0, 1.0, 0.97), a)
    with f.emit(par=1.0) as G:
        for p in pts:
            draw.glow_disc(G, p, rr * 7.0, (1.0, 1.0, 0.97), 0.55 * a)


# ----------------------------------------------------------------------------- window 9
def _sheet(c, t):
    """The show sheet, pulled aside, hanging bunched from the wire right of the glass."""
    s = NINE.s
    y0 = GY0 - 44 * s
    x0 = GX1 + 30 * s
    sway = 3.0 * s * fbm1(t * 0.3, 41)
    pts = [(x0 - 20 * s, y0), (x0 + 160 * s, y0 - 2 * s)]
    pts += [(x0 + 175 * s + sway, y0 + 300 * s), (x0 + 168 * s + sway * 1.5, y0 + 700 * s),
            (x0 + 185 * s + sway * 2, NINE.floor_y - 30 * s)]
    pts += [(x0 + 30 * s + sway * 2, NINE.floor_y - 40 * s), (x0 + 5 * s + sway, y0 + 640 * s),
            (x0 - 12 * s, y0 + 260 * s)]
    draw.smooth(c, pts, close=True, tension=0.35)


def _window9(f, t):
    NINE.draw(f, t, layer=dict(par=P9, blur=2.2), rain=1.0, room_light=0.55, condensation=0.0, outside_light=1.0)
    with f.layer(par=P9, blur=2.2) as c:
        _sheet(c, t)
        draw.fill(c, sets.mix(INK, sets.mix(PAPER, AMBER, 0.4), 0.16))
        # folds
        s = NINE.s
        for k, dx in enumerate((40, 80, 118, 150)):
            x = GX1 + 30 * s + dx * s
            c.move_to(x, GY0 - 40 * s)
            c.curve_to(x + 6 * s, GY0 + 300 * s, x - 4 * s, GY0 + 700 * s, x + 10 * s * (k % 2), NINE.floor_y - 40 * s)
        c.set_line_width(5.0 * s)
        c.set_source_rgba(*INK, 0.35)
        c.stroke()


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    W_ = _times(T)
    f.set_camera(camera(t, T))
    _outside(f, t, T, W_)
    _window9(f, t)
    _draw_her(f, t)
    f.post["bloom"] = 0.24


def motion_blur(t, T):
    return 1


def cues(T):
    W_ = _times(T)
    return [
        Cue(4.35, "muffled footsteps across the street, a floor creak (barely)", gain_db=-20, pan=0.3),
        Cue(W_["standing"], "binocular glint: a thin cold shimmer", gain_db=-10, pan=0.15),
        Cue(8.0, "rain on the glass swells (the wave)", gain_db=-14),
        Cue(W_["watch"], "light switch click, far, across the street", gain_db=-6, pan=0.2),
    ]
