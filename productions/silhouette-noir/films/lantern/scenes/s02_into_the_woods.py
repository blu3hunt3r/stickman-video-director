"""s02 · INTO THE WOODS, as a Saul Bass cut-paper sequence (style test).

Flat paper field, black trunk bars sliding past at three speeds, one amber disc of lantern
light, the girl a hinged paper doll (on twos), red only for her scarf, her bow and the flame.

Beats (scene time, s):
   -0.5  the title's iris opens on the lantern's red flame; graphic pull back to the wood
    0-7  she walks right; trunks slide by
    7.0  she stops: her brother's wooden horse on the path. She looks down
    7.4  INSERT: the horse, big, in the amber disc; her arm reaches in and takes it
    9.0  back wide: she hugs the toy; 9.3 lifts the lantern high and looks ahead
   10.3  walks on, slower; the field darkens to night, the disc shrinks
   14.0  white eyes with red pupils cut open in the dark, one pair at a time; she stops, leans
         back, pulls the lantern in
   15.9  thrusts the lantern: the disc bursts in rings, the eyes snap shut
   16.7  she runs; trunks whip past
   18.2  two jagged black legs (The Man with the Golden Arm) stab down into the light
   19.45 the disc closes to the flame; 19.78 black
"""
import math
from functools import lru_cache

from engine import bass
from engine.core import clamp, lerp, ease, hash01, noise1
from engine.palette import PAPER, RED
from engine.timing import Cue
from films.lantern import doll
from films.lantern.scenes import s01_title as S1

FIELD = S1.FIELD                     # warm paper, same as the title
NIGHT = (0.105, 0.095, 0.088)
GREY = (0.58, 0.55, 0.50)
AMBER = (0.95, 0.66, 0.24)
IRIS = S1.FLAME
GY = 1590.0                          # ground line (screen y)
GX = 380.0                           # her usual screen x

T_STOP = 7.0
T_INSERT = (7.4, 9.0)
T_LIFT = 9.3
T_EYES = 14.0
T_THRUST = 15.9
T_RUN = 16.7
T_LEG = 18.2
T_CLOSE = 19.45
T_BLACK = 19.78
LEGS = [  # (start, grow time, tip dx from her, base)
    (T_LEG, 1.0, 330.0, (1240.0, -160.0)),
    (T_LEG + 0.45, 0.8, 600.0, (1300.0, 260.0)),
]

SPEED = [(-1.0, 230.0), (6.55, 230.0), (7.0, 0.0), (10.3, 0.0), (10.75, 165.0), (13.95, 165.0),
         (14.35, 0.0), (T_RUN, 0.0), (T_RUN + 0.2, 640.0), (17.85, 640.0), (18.2, 0.0), (40.0, 0.0)]


def k(t, t0, dur, e="inout"):
    return ease(e, clamp((t - t0) / dur))


def track(keys, t):
    """Piecewise eased keys [(t, v), ...] (smoothstep between keys)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-6)
            return lerp(v0, v1, u * u * (3 - 2 * u))
    return keys[-1][1]


def speed(t):
    for (t0, v0), (t1, v1) in zip(SPEED, SPEED[1:]):
        if t <= t1:
            return lerp(v0, v1, clamp((t - t0) / max(t1 - t0, 1e-6)))
    return 0.0


@lru_cache(maxsize=1)
def _table():
    """Distance walked and stride phase, integrated at 240 Hz from t = -1."""
    dt = 1.0 / 240.0
    d, ph, out = 0.0, 0.0, []
    for i in range(int(42 * 240)):
        t = -1.0 + i * dt
        v = speed(t)
        out.append((d, ph))
        stride = lerp(300.0, 540.0, clamp((v - 230.0) / 410.0))
        d += v * dt
        ph += v / stride * dt
    return out


def dist(t):
    i = clamp((t + 1.0) * 240.0, 0, len(_table()) - 2)
    a, b = int(i), int(i) + 1
    u = i - a
    return lerp(_table()[a][0], _table()[b][0], u), lerp(_table()[a][1], _table()[b][1], u)


def steps():
    """Footfalls (scene time, running?): every half stride cycle while moving."""
    out = []
    t, last = -0.5, None
    while t < T_BLACK:
        n = math.floor(dist(t)[1] * 2.0 + 0.25)
        if last is not None and n != last and speed(t) > 20:
            out.append((t, speed(t) > 400))
        last = n
        t += 1.0 / 240.0
    return out


# ----------------------------------------------------------------------------- her
def girl_x(t):
    return GX + 70.0 * k(t, T_RUN, 0.6) * (1 - k(t, T_LEG, 0.8)) - 30.0 * k(t, T_EYES + 0.3, 0.5) * (1 - k(t, T_THRUST, 0.2))


def pose(t):
    tq = bass.on_twos(t)
    v = speed(tq)
    run = v > 400.0
    p = doll.walk_pose(dist(tq)[1], stride=clamp(v / (640.0 if run else 210.0)), run=run)
    # the lantern arm
    p.sh_f = track([(-1, 26), (T_LIFT, 26), (T_LIFT + 0.4, 150), (T_LIFT + 1.1, 150), (T_LIFT + 1.6, 26),
                    (T_EYES + 0.3, 26), (T_EYES + 0.6, 8), (T_THRUST, 8), (T_THRUST + 0.12, 96),
                    (T_THRUST + 0.7, 96), (T_RUN, 40), (T_LEG + 0.2, 40), (T_LEG + 0.8, 62), (40, 62)], tq)
    p.el_f = track([(-1, 36), (T_LIFT, 36), (T_LIFT + 0.4, -8), (T_LIFT + 1.1, -8), (T_LIFT + 1.6, 36),
                    (T_EYES + 0.3, 36), (T_EYES + 0.6, 76), (T_THRUST, 76), (T_THRUST + 0.12, 0),
                    (T_THRUST + 0.7, 0), (T_RUN, 40), (40, 26)], tq)
    p.sh_f += 3.0 * noise1(tq * 9.0, seed=4) * k(tq, T_EYES + 0.4, 0.3) * (1 - k(tq, T_THRUST, 0.1))   # trembling
    if tq >= T_INSERT[1]:
        p.toy = True
        p.sh_b, p.el_b = 34.0 + 0.3 * p.sh_b, 100.0
    p.head = track([(-1, 0), (T_STOP - 0.4, 0), (T_STOP, -20), (T_INSERT[0], -20), (T_INSERT[1], 0), (T_LIFT + 0.3, 8),
                    (T_LIFT + 1.4, 8), (T_LIFT + 1.8, 0), (T_EYES, 0), (T_EYES + 0.3, 6), (T_THRUST + 0.6, 6),
                    (T_RUN, 0), (T_LEG + 0.5, 0), (T_LEG + 1.0, 22), (40, 22)], tq)
    p.lean += track([(-1, 0), (T_EYES + 0.2, 0), (T_EYES + 0.5, -7), (T_THRUST, -7), (T_THRUST + 0.15, 9),
                     (T_THRUST + 0.6, 0), (T_LEG + 0.3, 0), (T_LEG + 0.6, -5), (40, -5)], tq)
    return p


def lantern_angle(t):
    """Swing of the lantern on its bail (rad): lags her stride, kicks at the thrust and stops."""
    v = speed(t)
    ph = dist(t)[1]
    a = 0.16 * math.sin(2 * math.pi * ph * 2.0 - 1.2) * clamp(v / 230.0, 0, 1.6)
    for t0, amp in ((T_STOP, 0.22), (14.35, 0.18), (T_THRUST + 0.12, -0.45), (18.2, 0.35)):
        a += bass.settle(t, t0, amp=amp, freq=0.9, decay=1.6)
    return a


LANTERN = {
    "cap": bass.cut([(-30, -2), (30, -2), (38, 16), (-38, 16)], seed=31, amp=1.0),
    "ring": bass.cut([(-9, -18), (9, -18), (9, -2), (-9, -2)], seed=32, amp=0.6),
    "posts": [bass.cut([(x0, 14), (x0 + 7, 14), (x0 + 7, 92), (x0, 92)], seed=33 + i, amp=0.5)
              for i, x0 in enumerate((-36, -3.5, 29))],
    "base": bass.cut([(-40, 90), (40, 90), (34, 108), (-34, 108)], seed=36, amp=1.0),
    "glass": bass.cut([(-30, 14), (30, 14), (30, 92), (-30, 92)], seed=37, amp=0.6),
}


def lantern_geom(t, hand):
    a = lantern_angle(t)
    top = (hand[0] + 4.0, hand[1] + 14.0)
    bail = 46.0
    ring = (top[0] + math.sin(a) * bail, top[1] + math.cos(a) * bail)
    ca, sa = math.cos(-a), math.sin(-a)
    c = (ring[0] + 53 * sa * -1 if False else ring[0] + math.sin(a) * 53.0, ring[1] + math.cos(a) * 53.0)
    return top, ring, a, c


def draw_lantern(ctx, t, hand, ink, flick):
    top, ring, a, c = lantern_geom(t, hand)
    ctx.save()
    ctx.new_path()
    ctx.move_to(*top)
    ctx.line_to(*ring)
    ctx.set_line_width(5.0)
    ctx.set_source_rgb(*ink)
    ctx.stroke()
    ctx.translate(*ring)
    ctx.rotate(-a)
    bass.fill_polys(ctx, [LANTERN["glass"]], AMBER)
    r = 13.0 * flick
    bass.fill_polys(ctx, [S1.flame_pts((0.0, 66.0), r, 4.0 * noise1(bass.on_twos(t) * 2, seed=3), int(bass.on_twos(t) * 12) % 5)], RED)
    bass.fill_polys(ctx, [LANTERN["cap"], LANTERN["ring"], LANTERN["base"]] + LANTERN["posts"], ink)
    ctx.restore()
    return c


def flame_point(t, hand):
    _, ring, a, _ = lantern_geom(t, hand)
    return (ring[0] + math.sin(a) * 58.0, ring[1] + math.cos(a) * 58.0)


# ----------------------------------------------------------------------------- the wood
def darkness(t):
    return k(t, 9.6, 4.8, "inout")


def _bars(t, par, spacing, wr, seed, scroll):
    off = scroll * par
    out = []
    for i in range(int((off - 300) // spacing), int((off + 1400) // spacing) + 1):
        if hash01(seed, i) < 0.18:
            continue
        x = i * spacing + spacing * 0.7 * hash01(seed, i, 1) - off
        w = lerp(wr[0], wr[1], hash01(seed, i, 2))
        out.append((i, x, w))
    return out


@lru_cache(maxsize=2048)
def _trunk(i, w, seed, top, bot):
    """One cut-paper trunk in local x (centre 0): a bar with, sometimes, a dead bough stub."""
    polys = [bass.cut_rect(-w / 2, top, w / 2, bot, seed=seed * 1000 + i, amp=1.4)]
    if hash01(seed, i, 5) < 0.55:
        y = lerp(top + 260, bot - 420, hash01(seed, i, 6))
        sgn = 1 if hash01(seed, i, 7) < 0.5 else -1
        L = w * 1.4 + 70 * hash01(seed, i, 8)
        polys.append(bass.cut([(0, y), (sgn * L, y - 0.8 * L), (sgn * (L + 9), y - 0.8 * L + 13), (0, y + w * 0.45)],
                              seed=seed * 1000 + i + 7, amp=1.0))
    return polys


def draw_trunks(c, t, scroll, par, spacing, wr, seed, color, top=-60.0, avoid=None):
    jit = 1.5 * noise1(bass.on_twos(t) * 3.0, seed=seed)
    for i, x, w in _bars(t, par, spacing, wr, seed, scroll):
        if avoid is not None and abs(x - avoid[0]) < avoid[1] + w / 2:
            continue
        c.save()
        c.translate(x + jit, 0.0)
        bass.fill_polys(c, _trunk(i, round(w, 1), seed, top, GY + 40.0), color)
        c.restore()


@lru_cache(maxsize=4096)
def _tuft(i):
    n = 3 + int(hash01(71, i) * 3)
    polys = []
    for j in range(n):
        x = (j - n / 2) * 11 + 6 * hash01(71, i, j)
        h = 22 + 40 * hash01(72, i, j)
        lean = (hash01(73, i, j) - 0.5) * 30
        polys.append(bass.cut([(x - 5, 4), (x + lean, -h), (x + 5, 4)], seed=i * 13 + j, amp=0.5))
    return polys


def draw_ground(c, t, scroll, ink):
    bass.fill_polys(c, [bass.cut_rect(-60.0, GY, 1140.0, 2000.0, seed=81, amp=1.2)], ink)
    for i in range(int((scroll - 100) // 85), int((scroll + 1200) // 85) + 1):
        if hash01(70, i) < 0.4:
            continue
        x = i * 85 + 40 * hash01(74, i) - scroll
        c.save()
        c.translate(x, GY + 2)
        bass.fill_polys(c, _tuft(i), ink)
        c.restore()


def light_disc(c, center, r, color, t):
    seed = int(bass.on_twos(t) * 12.0) % 3
    bass.fill_polys(c, [bass.cut_ellipse(center, r, r, seed=seed, max_len=60.0)], color)


# ----------------------------------------------------------------------------- the eyes
EYES = [  # (screen x, y, size, opens at)
    (800.0, 1020.0, 1.00, T_EYES + 0.00),
    (950.0, 760.0, 0.80, T_EYES + 0.42),
    (760.0, 1360.0, 0.72, T_EYES + 0.74),
    (1000.0, 1180.0, 1.15, T_EYES + 1.02),
    (880.0, 520.0, 0.62, T_EYES + 1.30),
]


def almond(c, cx, cy, w, h, n=18):
    pts = []
    for i in range(n + 1):
        u = i / n
        x = lerp(-w, w, u)
        pts.append((cx + x, cy - h * math.sin(math.pi * u) ** 0.8))
    for i in range(n + 1):
        u = 1 - i / n
        x = lerp(-w, w, u)
        pts.append((cx + x, cy + h * math.sin(math.pi * u) ** 0.8))
    return pts


def draw_eyes(c, t):
    if t < T_EYES - 0.05 or t > T_THRUST + 0.6:
        return
    tq = bass.on_twos(t)
    for j, (x, y, s, t_in) in enumerate(EYES):
        o = clamp(bass.pop(tq, t_in, 0.25))
        o *= 1.0 - k(tq, T_THRUST + 0.08 + 0.04 * j, 0.1, "in3")
        ph = (tq * 0.55 + j * 0.31) % 1.0                  # an occasional blink
        o *= 1.0 - clamp(1.0 - abs(ph - 0.5) / 0.04)
        if o <= 0.02:
            continue
        look = -16.0 * s                                     # they all look at her
        for ex in (-52.0 * s, 52.0 * s):
            bass.fill_polys(c, [bass.scissor(almond(c, x + ex, y, 40.0 * s, 20.0 * s * o), seed=j, sag=0.5,
                                             amp=0.4, max_len=12.0)], PAPER)
            ph_ = 17.0 * s * o
            bass.fill_polys(c, [[(x + ex + look - 6.0 * s, y - ph_), (x + ex + look + 6.0 * s, y - ph_),
                                 (x + ex + look + 6.0 * s, y + ph_), (x + ex + look - 6.0 * s, y + ph_)]], RED)


# ----------------------------------------------------------------------------- shots
def render_insert(f, t):
    """The horse, big, in the amber disc; her arm reaches in from the top left and takes it."""
    ink = f.pal.ink
    c0 = (540.0, 1090.0)
    with f.screen() as c:
        c.rectangle(0, 0, 1080, 1920)
        c.set_source_rgb(*FIELD)
        c.fill()
        light_disc(c, c0, 520.0 * (1 + 0.012 * noise1(bass.on_twos(t) * 5, seed=2)), AMBER, t)
        # a few trunks behind, close and big
        for x, w in ((930.0, 90.0), (1040.0, 60.0)):
            bass.fill_polys(c, [bass.cut_rect(x - w / 2, -60.0, x + w / 2, 1500.0, seed=int(x), amp=1.4)], ink)
        bass.fill_polys(c, [bass.cut_rect(-60.0, 1470.0, 1140.0, 2000.0, seed=82, amp=1.2)], ink)
        tq = bass.on_twos(t)
        t0 = T_INSERT[0]
        grab = (470.0, 1290.0)
        reach = k(tq, t0 + 0.15, 0.55, "out3")
        lift = k(tq, t0 + 1.0, 0.5, "in3")
        hand = (lerp(-260.0, grab[0], reach) + 260.0 * lift, lerp(500.0, grab[1], reach) - 1900.0 * lift)
        toy_at = (560.0 + (hand[0] - grab[0]) * (lift > 0), 1472.0 + (hand[1] - grab[1]) * (lift > 0))
        tilt = -8.0 * lift
        doll.draw_toy(c, toy_at, ink, k=3.4, angle=tilt)
        shoulder = (-200.0, 140.0)
        arm = bass.capsule_pts(shoulder, hand, 62.0, 48.0)
        bass.fill_polys(c, [arm, bass.cut_ellipse(hand, 62.0, 68.0, seed=91)], ink)
        # her red scarf end flicks across the corner, a reminder whose arm this is
        bass.fill_polys(c, [bass.cut([(-40, 260 + 30 * reach), (220, 330 + 40 * reach), (260, 372 + 40 * reach),
                                      (-40, 330 + 30 * reach)], seed=93, amp=1.2)], RED)


def render(f, t, T):
    bass.bass_scene(f, field=FIELD, paper=0.8, vignette=0.16, mottle=0.05)
    if t >= T_BLACK:
        with f.screen() as c:
            c.rectangle(0, 0, 1080, 1920)
            c.set_source_rgb(0.0, 0.0, 0.0)
            c.fill()
        return
    if T_INSERT[0] <= t < T_INSERT[1]:
        render_insert(f, t)
        return
    ink = f.pal.ink
    d = darkness(t)
    scroll, _ = dist(t)
    p = pose(t)
    gx = girl_x(t)
    tq = bass.on_twos(t)
    fl = math.exp(-max(0.0, t - T_THRUST - 0.1) * 3.0) * k(t, T_THRUST, 0.1, "out3")
    flick = 1.0 + 0.04 * noise1(tq * 6.0, seed=7)
    # where her hand and the flame will be (for the light and for the opening zoom)
    hand = _hand(gx, p)
    flame = flame_point(t, hand)
    _, _, _, lc = lantern_geom(t, hand)
    close = k(t, T_CLOSE, T_BLACK - T_CLOSE, "in3")
    R = 470.0 * (1.0 - 0.28 * d) * (1.0 + 0.45 * fl) * flick * (1.0 + 0.10 * k(t, T_LIFT, 0.4) * (1 - k(t, T_LIFT + 1.2, 0.4)))
    R *= 1.0 - 0.97 * close

    with f.screen() as c:
        # opening: the iris showed the flame big at IRIS; a graphic pull back to the wide
        b = k(t, -0.5, 2.9, "inout3")
        if b < 1.0:
            z = math.exp(lerp(math.log(7.5), 0.0, b))
            ax, ay = lerp(IRIS[0], flame[0], b), lerp(IRIS[1], flame[1], b)
            c.translate(ax, ay)
            c.scale(z, z)
            c.translate(-flame[0], -flame[1])
        field = tuple(lerp(a, b_, d) for a, b_ in zip(FIELD, NIGHT))
        c.rectangle(-2000, -2000, 5080, 5920)
        c.set_source_rgb(*field)
        c.fill()
        far = tuple(lerp(a, b_, clamp(d * 1.15)) for a, b_ in zip(GREY, NIGHT))
        draw_trunks(c, t, scroll, 0.45, 150.0, (16.0, 44.0), 11, far)
        draw_trunks(c, t, scroll, 1.0, 330.0, (46.0, 110.0), 23, ink)
        # the light is a disc laid over the wood: inside it she stands clear on amber
        light_disc(c, lc, R, AMBER, t)
        if fl > 0.01:                                           # the burst: rings flung outward
            u = k(t, T_THRUST + 0.05, 0.7, "out3")
            bass.rings(c, lc, [R * (1.15 + 1.3 * u), R * (1.5 + 1.9 * u), R * (1.9 + 2.6 * u)],
                       [34 * (1 - u) + 2, 24 * (1 - u) + 2, 16 * (1 - u) + 2], AMBER, seed=5, alpha=1.0 - u * 0.7)
        draw_ground(c, t, scroll, ink)
        if t < T_INSERT[0]:                                      # the toy on the path
            doll.draw_toy(c, (dist(T_STOP)[0] + 650.0 - scroll, GY + 2.0), ink, k=0.8)
        doll.draw_girl(c, (gx, GY), p, ink, RED)
        draw_lantern(c, t, hand, ink, flick * (1 + 0.6 * fl) * (1 - 0.5 * close))
        for (t0, g, dx, base) in LEGS:
            if t >= t0:
                tip = (gx + dx, GY + 6.0)
                bass.jagged_arm(c, base, tip, ink, width=84.0, grow=ease("out3", clamp((t - t0) / g)),
                                jags=4, jag=0.9, claw=0.75, seed=int(dx))
        draw_trunks(c, t, scroll, 1.9, 1500.0, (150.0, 230.0), 37, ink, avoid=(gx + 120.0, 520.0))
        draw_eyes(c, t)


def _hand(gx, p):
    """The front hand's screen position without drawing (draw_girl on a throwaway surface)."""
    import cairo
    s = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    return doll.draw_girl(cairo.Context(s), (gx, GY), p, (0, 0, 0), (0, 0, 0))


def cues(T):
    return [Cue(-0.5, "night wind through trees", gain_db=-14, dur=20.0),
            Cue(T_INSERT[0] + 0.7, "small wooden toy picked up, wheels rattle", gain_db=-14),
            Cue(T_EYES, "eyes opening: soft wet clicks, a low breath", gain_db=-12, dur=1.6),
            Cue(T_THRUST + 0.05, "lantern flare whoosh", gain_db=-8),
            Cue(T_LEG + 1.0, "chitinous stab into the ground", gain_db=-6)]
