"""s08 · FIRE (17.0 s): the fight in the clearing, the basket, the lantern, the burning web.

IN  hard cut on action from s07: the same performance carries on (s08 t = s07 t - 13.0); the
    wolf, mid-leap, crashes into Grandmother's face.
0.0-3.0   the fight: Grandmother flinches back, stabs; the wolf dodges and bites the leg stuck
          in the snow; a leg slams down at the girl - she is knocked flat, the basket flies.
3.0-9.2   low on the basket in the snow, the fight above and behind it. [basket@4.07] a blow
          beside it tips it over and it rolls; [Bread@5.65] the loaf tumbles out;
          [Wine@6.42] the bottle rolls out; [lantern@8.38] the lantern rolls out, glowing.
9.2-12.66 Grandmother pins the wolf. The girl gets up, takes the lantern and runs to the
          strands anchoring Grandmother's thread; [fire@12.66] she smashes it on them.
13.3-17.0 the fire races up the silk into the canopy and down toward the valley; Grandmother
          burns and recoils; the firelight fills the frame.
OUT flash (warm white): the fire flares to white.
"""
import math

from engine import atmos
from engine.timing import Cue
from films.red import sets as S
from films.red.scenes import _lib_s04_s08 as L

C = S.CLEARING_SET
MOOD = L.CL_MOOD
D = L.S08_DT
F8, G8 = L.F8, L.G8
T_SMASH = G8["smash"]

_CAM = L.CamPath([
    (0.0, 1050.0, 990.0, 0.95),
    (2.3, 1060.0, 1000.0, 0.95),
    (3.2, 990.0, 1395.0, 2.15),
    (8.5, 965.0, 1430.0, 2.6),
    (9.5, 930.0, 1150.0, 1.25),
    (10.6, 980.0, 1120.0, 1.15),
    (12.66, 1560.0, 1010.0, 0.82),
    (13.3, 1560.0, 990.0, 0.80),
    (15.0, 1600.0, 820.0, 0.62),
    (16.0, 1250.0, 600.0, 0.46),
    (17.0, 700.0, 400.0, 0.38),
    (17.5, 650.0, 380.0, 0.37),
])
SHAKES = [(0.0, 4.0, 0.25), (1.685, 2.5, 0.2), (2.385, 4.0, 0.25), (3.95, 2.0, 0.2), (5.5, 2.5, 0.2),
          (6.3, 2.0, 0.2), (8.25, 2.5, 0.2), (T_SMASH, 4.0, 0.35)]


def cam(t):
    c = _CAM(t)
    amp = 0.0
    for t0, a, tau in SHAKES:
        k = t - t0
        if 0.0 <= k < 6 * tau:
            amp = max(amp, a * math.exp(-k / tau))
    if amp > 0.05:
        c = c.shaken(t, amp=amp, rot_amp=0.0, freq=9.0, seed=8)
    return c


def burn():
    return C.ignite(D + T_SMASH)


def low_mist(t):
    """Alpha of the low mist behind the basket (the close-up, 3.2-8.5)."""
    return 0.55 * L.ss(2.5, 3.2, t) * (1.0 - L.ss(8.6, 9.6, t))


def render(f, t, T):
    t7 = t + D
    f.set_camera(cam(t))
    lant = L.lantern_state(t)
    fire = t >= T_SMASH
    B = burn() if fire else None
    lights = []
    if lant["shown"] and lant["lit"] > 0.02:
        lights.append((lant["pos"][0], lant["pos"][1], 420.0, 0.8 * lant["lit"]))
    C.draw_back(f, MOOD, era="web", t=t7)
    C.draw_plane(f, MOOD, era="web", t=t7, burn=B, lights=lights)
    f.haze(MOOD.mist, 0.38, y1=1480.0, feather=260.0, x0=-760.0, x1=1060.0, tex=0.6, tex_scale=0.8,
           scroll=(12.0, -2.0), seed=5)
    f.haze(MOOD.mist, 0.3, y1=1480.0, feather=160.0, x0=1905.0, x1=2075.0, tex=0.6, tex_scale=0.8,
           scroll=(12.0, -2.0), seed=6)
    lo = low_mist(t)
    if lo > 0.0:
        # low on the snow: mist pooled at the foot of the cottage, so the basket, the bread, the
        # bottle and her legs read as ink against it
        f.haze(MOOD.mist, lo, y0=1330.0, y1=1556.0, feather=110.0, x0=560.0, x1=1260.0, tex=0.5,
               tex_scale=1.2, scroll=(16.0, -1.0), seed=9)
    sp, g, w = L.cl_spider(), L.cl_girl(), L.cl_wolf()
    bk = L.basket_state(t)
    with f.layer() as c:
        sp.draw(f, t7, c, eye_scale=1.3)
        w.draw(f, t7, c)
        if not bk["held"]:
            _draw_basket_spill(f, c, t, bk)
        if lant["shown"] and lant["anchor"] is not None and t < L.LANTERN_GRAB_T:
            _draw_lantern(f, c, t, lant)
        front = bk["held"] and L.cl_basket(t7)[2]
        if bk["held"] and not front:
            L.draw_basket(c, bk["grip"], bk["angle"], f.pal.ink)
        g.draw(f, t7, c)
        if bk["held"] and front:
            L.draw_basket(c, bk["grip"], bk["angle"], f.pal.ink)
        if lant["shown"] and t >= L.LANTERN_GRAB_T:
            _draw_lantern(f, c, t, lant)
        if fire:
            S.lantern_burst(f, c, L.C_SMASH, t7, D + T_SMASH, MOOD, S.CLEARING, size=1.2)
    C.draw_front(f, MOOD, era="web", t=t7, burn=B, fire_strength=1.0)
    if fire:
        atmos.embers(f, L.ember_source(B), rate=70.0, life=(1.0, 2.6), rise=(110.0, 260.0), spread=40.0,
                     wind=25.0, gust=20.0, size=(1.2, 2.8), color=MOOD.lamp, t=t7, seed=11, t_start=D + T_SMASH)
        _flare(f, t)


def _flare(f, t):
    """The fire flares toward white at the end (under the flash to s09)."""
    a = 0.42 * L.ss(16.0, 17.5, t)
    if a <= 0.005:
        return
    import cairo
    with S.soft_layer(f, k=8, op="add", screen=True) as A:
        g = cairo.RadialGradient(540.0, 1150.0, 80.0, 540.0, 1100.0, 1500.0)
        g.add_color_stop_rgba(0, *MOOD.lamp, a)
        g.add_color_stop_rgba(1, *MOOD.lamp, 0.45 * a)
        A.set_source(g)
        A.paint()


def _draw_lantern(f, c, t, lant):
    S.Lantern(L.LANTERN_SIZE).draw(f, c, lant["anchor"], lant["angle"], lit=lant["lit"], t=t, mood=MOOD)
    if lant["lit"] > 0.02:
        x, y = lant["pos"]
        gy = float(S.CLEARING.ground_y(x))
        with S.soft_layer(f, 1.0, k=6, op="add", blur=30.0) as A:
            S.light_pool(A, (x, gy), 150.0, 30.0, MOOD.lamp, 0.32 * lant["lit"])
            S.glow(A, (x, y), 260.0, MOOD.lamp, 0.10 * lant["lit"])


def _draw_basket_spill(f, c, t, bk):
    ink = f.pal.ink
    tipped = t >= F8["roll"] + 0.05
    items = [n for n in ("bread", "bottle", "lantern") if t < L.SPILL[n][0]]
    L.draw_basket(c, bk["grip"], bk["angle"], ink, cloth=not tipped, items=tuple(items))
    if tipped:
        # the cloth slid out as it tipped over
        m = L.basket_mouth(t)
        u = L.ss(F8["roll"] + 0.05, F8["roll"] + 0.5, t)
        cx = m[0] - 30.0 * u
        gy = float(S.CLEARING.ground_y(cx))
        pts = [(cx - 26, gy - 2), (cx - 12, gy - 9 - 4 * (1 - u)), (cx + 6, gy - 7), (cx + 22, gy - 3), (cx + 4, gy + 1)]
        from engine import draw
        draw.smooth(c, pts, close=True, tension=0.4)
        draw.fill(c, ink)
        # the lantern still inside: a warm glow at the mouth
        if t < L.SPILL["lantern"][0]:
            a = 0.35 * L.ss(F8["roll"] + 0.3, F8["roll"] + 1.5, t) * (0.8 + 0.2 * S.flick(t, 41))
            with f.emit() as G:
                S.glow(G, m, 40.0, MOOD.lamp, a)
    bkt = S.Basket(L.BASKET_SIZE)
    from engine import draw
    for name in ("bread", "bottle"):
        st = L.item_state(name, t)
        if st is None:
            continue
        x, y, ang = st
        poly = bkt.item_poly(name)
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        draw.poly(c, [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in poly])
        draw.fill(c, ink)


def cues(T):
    return []
