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
    (2.4, 975.0, 1005.0, 0.97),
    (3.2, 975.0, 1395.0, 2.15),
    (8.8, 950.0, 1432.0, 2.62),
    (9.7, 850.0, 1170.0, 1.25),
    (10.6, 980.0, 1120.0, 1.15),
    (12.66, 1560.0, 1010.0, 0.82),
    (13.3, 1580.0, 990.0, 0.80),
    (14.3, 1800.0, 930.0, 0.68),
    (15.4, 1820.0, 860.0, 0.60),
    (16.2, 1480.0, 700.0, 0.50),
    (17.0, 800.0, 470.0, 0.40),
    (17.5, 750.0, 450.0, 0.395),
])
FLASH_RGB = (1.0, 0.93, 0.85)       # the timeline's flash into s09
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
    # silk stays alight 1.6 s (default 0.75): the clearing is still burning when it flares
    return C.ignite(D + T_SMASH, burn_time=1.6)


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
    if fire:
        _spider_fire(f, sp, t7)
    C.draw_front(f, MOOD, era="web", t=t7, burn=B, fire_strength=1.0)
    if fire:
        atmos.embers(f, L.ember_source(B), rate=70.0, life=(1.0, 2.6), rise=(110.0, 260.0), spread=40.0,
                     wind=25.0, gust=20.0, size=(1.2, 2.8), color=MOOD.lamp, t=t7, seed=11, t_start=D + T_SMASH)
        _flare(f, t, B)


def _spider_fire(f, sp, t7):
    """Grandmother burning: flames along the top of her abdomen and head, and on four legs."""
    from engine.creatures import solve_spider
    P = sp.state(t7)
    b = float(P.get("burn", 0.0))
    if b <= 0.02:
        return
    S_ = sp.S
    cy = math.cos(math.radians(P["yaw"]))
    pa = math.radians(P["pitch"])
    cp, sn = math.cos(pa), math.sin(pa)

    def bw(fw, up):
        f_, u_ = fw * S_, up * S_
        return (P["x"] + (f_ * cp - u_ * sn) * cy, P["y"] - (f_ * sn + u_ * cp))
    atmos.flames(f, (bw(-0.80, 0.14), bw(-0.10, 0.20)), height=0.40 * S_ * b, t=t7, seed=23, intensity=1.2 * b,
                 color=MOOD.lamp, wind=-20.0)
    atmos.flames(f, (bw(0.02, 0.12), bw(0.30, 0.08)), height=0.18 * S_ * b, t=t7, seed=29, intensity=b,
                 color=MOOD.lamp, licks=False)
    R = solve_spider(sp, P)
    for i in (1, 2, 5, 6):
        hip, kn, an, tip = R["legs"][i]
        atmos.flames(f, (tuple(kn[:2]), tuple(an[:2])), height=0.09 * S_ * b, t=t7, seed=31 + i,
                     intensity=0.8 * b, color=MOOD.lamp, licks=False, glow=0.5)


def _flare(f, t, B):
    """The fire flares toward white at the end: the bloom spreads, the exposure lifts, the
    vignette opens and the frame washes toward the flash colour (the cut's flash completes it)."""
    w1 = L.ss(15.6, 17.0, t)
    if w1 <= 0.0:
        return
    w2 = L.ss(16.0, 17.0, t) ** 1.5
    w3 = L.ss(16.3, 17.0, t) ** 2
    P = f.post
    P["bloom"] += 0.7 * w1
    P["bloom_threshold"] -= 0.22 * w1
    P["exposure"] *= 1.0 + 0.45 * w2
    P["vignette"] *= 1.0 - 0.6 * w2
    if 0.3 * w3 > P["flash"]:
        P["flash"] = 0.3 * w3
        P["flash_color"] = FLASH_RGB
    col = tuple(L.lerp(a, b, w2) for a, b in zip(MOOD.lamp, FLASH_RGB))
    with S.soft_layer(f, 1.0, k=8, op="add", blur=60.0) as A:
        for (x, y, r, s_) in B.light_sources(t + D, n=4, radius=1100.0):
            S.glow(A, (x, y), 1.6 * r, col, 0.22 * s_ * w1)


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
    from engine import draw
    for name in ("bread", "bottle"):
        st = L.item_state(name, t)
        if st is None:
            continue
        x, y, ang = st
        poly = L.item_poly(name)
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        draw.poly(c, [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in poly])
        draw.fill(c, ink)


def cues(T):
    return [
        Cue(0.0, "wolf slams into the spider's face: heavy body impact, snarl", gain_db=-1, pan=0.1),
        Cue(0.25, "wolf jaws snapping at the spider's eyes", gain_db=-6, pan=0.15),
        Cue(F8["dodge"], "wolf scrabbles back in the snow, snarl", gain_db=-7, pan=0.1),
        Cue(F8["stabA"] + 0.385, "spider leg spears into the snow: thud, crunch", gain_db=-3, pan=0.15),
        Cue(1.85, "wolf bites the stuck leg: chitin crack, spider hiss", gain_db=-3, pan=0.2),
        Cue(F8["knock"], "spider leg slams down by the girl: impact, her cry, she is thrown flat", gain_db=-2,
            pan=-0.45),
        Cue(F8["fly"], "basket flung away: wicker creak, whoosh", gain_db=-10, pan=-0.2),
        Cue(2.88, "basket thumps down in the snow", gain_db=-8, pan=0.0),
        Cue(3.5, "wolf lands from its lunge, snarling", gain_db=-5, pan=0.35),
        Cue(F8["roll"], "spider leg stabs the snow beside the basket", gain_db=-4, pan=0.3),
        Cue(T.at("basket"), "basket tips over: wicker thump, things shifting inside", gain_db=-6, pan=0.05),
        Cue(F8["bread"], "spider leg strikes the wolf: wolf yelps", gain_db=-4, pan=0.5),
        Cue(T.at("Bread"), "loaf tumbles out onto the snow: soft thump", gain_db=-9, pan=-0.05),
        Cue(F8["wine"], "spider leg stabs the snow", gain_db=-5, pan=0.3),
        Cue(T.at("Wine"), "wine bottle slides out: clink on the wicker, glass rolling on snow", gain_db=-8,
            pan=-0.15, dur=0.8),
        Cue(7.41, "wolf lunges again, snarling", gain_db=-5, pan=0.5),
        Cue(F8["lantern"], "spider leg stab, close", gain_db=-5, pan=0.4),
        Cue(T.at("lantern"), "lantern rolls out: tin rattle, glass, the flame flutters up", gain_db=-6,
            pan=0.0, dur=0.7),
        Cue(G8["up0"], "girl scrambles up in the snow, quick breaths", gain_db=-12, pan=-0.3, dur=0.9),
        Cue(F8["pin"], "spider pins the wolf: legs slam down, wolf yelps", gain_db=-3, pan=0.6),
        Cue(10.0, "pinned wolf snarling and snapping", gain_db=-8, pan=0.55, dur=2.6),
        Cue(G8["grab"], "her hand closes on the lantern's ring: tin clink", gain_db=-10, pan=-0.05),
        Cue(10.82, "running footsteps in snow, the lantern rattling", gain_db=-8, pan=-0.1, dur=1.5),
        Cue(T.at("fire"), "lantern smashed on the silk: glass shatter, oil fire WHOOSH", gain_db=0, pan=0.15),
        Cue(T_SMASH + 0.15, "fire racing along the silk: crackling roar building", gain_db=-3, pan=0.1,
            dur=4.0),
        Cue(F8["burnt"], "spider screeches, rearing off the wolf", gain_db=-2, pan=0.6),
        Cue(F8["burn1"], "the fire reaches the spider: shriek, sizzle", gain_db=-1, pan=0.7),
        Cue(15.0, "spider death rattle: legs clattering, burning", gain_db=-4, pan=0.6, dur=2.0),
        Cue(15.8, "the fire roar swells into the flash", gain_db=0, pan=0.0, dur=1.2),
    ]
