"""s07 · CROSSING (76-90): the section, dark. Her paper footsteps come down the fire escape
while his red ones cross the street to her door: the near miss, him right under her
platform, listening. He goes in, and the race is mirrored: he climbs her stairs while she
drops to the street, crosses it and climbs his. Their two ways cross in an X. He ends at
her door, she at his."""
import math
from functools import lru_cache

from engine import bass, paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import folk as F
from films.opposite_full import kit as K

k = K.k
HER_B, HIS_B = K.HER_B, K.HIS_B
PAVE = K.GROUND - 8.0            # footsteps on the street
LOBBY = K.GROUND - K.SLAB / 2 - 8.0    # ... and on a ground-floor floor

# ---------------------------------------------------------------- beats (scene time)
T_STOP = 1.9                      # both stop: the near miss
T_LISTEN = 2.1                    # he listens: rings spread up from him
T_LENS1 = (2.3, 3.9)              # the callout: her shoes on the grating, his hat below
T_HORN = 3.6                      # a far car horn releases it
T_IN = 4.0                        # he goes in at her street door
T_LADDER = 4.5                    # her drop ladder comes down
T_LENS2 = (7.8, 9.8)              # the callout: Vertigo's stairwell, his hand on the rail
T_X = 12.0                        # their two ways, crossing
T_RINGS = 12.4                    # a ring round each of them

DOT_R = 8.0
NUM_DIM = lerp(K.NIGHT, K.PAPER, 0.35)
BULB = lerp(K.DEEP, K.AMBER, 0.6)


def _lift(pts, dy=-8.0):
    return [(x, y + dy) for x, y in pts]


def walk(route, step, t0, t1):
    """Footsteps along a polyline: points about `step` apart (the last one on the end) and
    the times they land, evenly from t0 to t1. Also the time each vertex is reached."""
    segs = [(a, b, math.dist(a, b)) for a, b in zip(route, route[1:])]
    L = sum(d for _, _, d in segs) or 1.0
    n = max(1, round(L / step))
    pts, times = [], []
    for i in range(n + 1):
        s = L * i / n
        for a, b, d in segs:
            if s <= d or (a, b, d) == segs[-1]:
                u = clamp(s / d) if d > 0 else 1.0
                pts.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u)))
                break
            s -= d
        times.append(lerp(t0, t1, i / n))
    at, s = [t0], 0.0
    for _, _, d in segs:
        s += d
        at.append(lerp(t0, t1, s / L))
    return pts, times, at


@lru_cache(maxsize=1)
def paths():
    """Both routes as footsteps: {'his'|'hers': (points, times)}, and when each reaches
    each storey's landing."""
    his_stairs = _lift(HER_B.stair_route(1, K.HER_FLOOR))
    legs_his = [
        walk([(622.0, PAVE), (398.0, PAVE)], 32.0, 0.1, T_STOP),                       # across to her door
        walk([(398.0, PAVE), (372.0, PAVE), (330.0, LOBBY), (his_stairs[0][0], LOBBY)], 32.0, T_IN, T_IN + 0.9),
        walk(his_stairs, 30.0, T_IN + 1.0, 11.3),                                       # up her stairs, creeping
        walk([his_stairs[-1], (142.0, his_stairs[-1][1])], 16.0, 11.4, 11.55),           # to her door
    ]
    her_stairs = _lift(HIS_B.stair_route(1, K.HIS_FLOOR))
    esc = _lift(K.escape_route(K.HER_FLOOR, 2), -6.0)
    drop_x = K.ESCAPE_X[1] - 19.0
    legs_her = [
        walk(esc, 28.0, 0.1, T_STOP),                                                   # down the fire escape
        walk([esc[-1], (drop_x, esc[-1][1])], 20.0, T_LADDER + 0.2, T_LADDER + 0.3),
        walk([(drop_x, esc[-1][1] + 10.0), (drop_x, PAVE)], 24.0, T_LADDER + 0.35, T_LADDER + 0.95),   # the ladder
        walk([(drop_x, PAVE), (707.0, PAVE)], 34.0, T_LADDER + 1.0, T_LADDER + 2.0),    # across the street, running
        walk([(707.0, PAVE), (730.0, LOBBY), (her_stairs[0][0], LOBBY)], 32.0, T_LADDER + 2.05, T_LADDER + 2.6),
        walk(her_stairs, 30.0, T_LADDER + 2.7, 11.35),                                  # up his stairs, running
        walk([her_stairs[-1], (938.0, her_stairs[-1][1])], 16.0, 11.45, 11.6),          # to his door
    ]
    out = {}
    for name, legs, b, stairs_leg in (("his", legs_his, HER_B, 2), ("hers", legs_her, HIS_B, 5)):
        pts, times = [], []
        for p, ts, _ in legs:
            pts += p
            times += ts
        # the landings: route vertex 0, 2, 4 ... of the stair leg are landings 1, 2, 3 ...
        at = legs[stairs_leg][2]
        landings = {n + 1: at[2 * n] for n in range(len(at) // 2 + 1) if 2 * n < len(at)}
        out[name] = (pts, times, landings)
    return out


def head(name, t):
    """Where a walker is at t (their last footstep) and the index of that step."""
    pts, times, _ = paths()[name]
    i = max(0, sum(1 for ti in times if ti <= t) - 1)
    return pts[i], i


# ---------------------------------------------------------------- the section, dark
def people(t):
    def fn(c, b, n, room):
        if b is K.HIS_B and n == K.HIS_FLOOR:
            victim(c, room[3])
        else:
            F.asleep(c, b, n, room, t)
    return fn


def victim(c, fy):
    """The woman in his room, lying on her back where she fell, a small flat pool by her."""
    bass.fill_polys(c, [bass.orient(bass.cut([(842.0, fy - 1.0), (872.0, fy - 5.0), (905.0, fy - 4.0), (918.0, fy - 1.0)],
                                             seed=74, amp=0.4), True)], RED)
    fig = B.win_fig(2)
    p = pd.Pose(head=6.0, arms={"near": ("ang", 16.0, 10.0), "far": ("ang", -8.0, 6.0)})
    p.eye = 0.0
    c.save()
    c.translate(782.0, fy - 7.0)
    c.rotate(math.radians(90.0))
    c.scale(F.SEC_FS, F.SEC_FS)
    B.draw_cutout(c, fig, pd.standing(fig, 0.0), p, K.INK, facing=-1, edge=K.AMBER, outline=K.AMBER, ow=10.0)
    c.restore()


def bulbs(c):
    """A dim bulb over each landing of both stairwells."""
    for b in (HER_B, HIS_B):
        for n in range(1, b.floors + 1):
            x = b.landing(n)[0]
            y = K.level(n + 1) + K.SLAB / 2 + 22.0
            bass.fill_polys(c, [bass.orient([(x - 1.0, y - 22.0), (x + 1.0, y - 22.0), (x + 1.0, y), (x - 1.0, y)], True)],
                            K.SHUT)
            K.dot(c, (x, y + 3.0), 26.0, K.AMBER, seed=n, alpha=0.07)
            K.dot(c, (x, y + 3.0), 4.5, BULB, seed=n + 10)


def numbers(c, t):
    """Her building's numbers turn red as he passes each landing; his turn paper as she does."""
    P = paths()
    for b, who, col in ((HER_B, "his", RED), (HIS_B, "hers", K.PAPER)):
        x = b.x0 - 22.0 if b.side > 0 else b.x1 + 22.0
        landings = P[who][2]
        for n in range(1, b.floors + 1):
            c_ = NUM_DIM
            g = 1.0
            t0 = landings.get(n)
            if t0 is not None and t >= t0:
                c_ = col
                g = 1.0 + 0.5 * (1.0 - ease("out3", clamp((t - t0) / 0.3)))
            K.numeral(c, str(n), (x, (K.level(n) + K.level(n + 1)) / 2.0), 40.0, c_, seed=40 + n + b.seed, scale=g)


def trail(c, name, t, col):
    pts, times, _ = paths()[name]
    K.step_dots(c, pts, times, t, col, r=DOT_R, seed=11 if name == "his" else 23)
    if t >= times[0]:
        p, i = head(name, t)
        if name == "hers" and T_STOP <= t < T_LADDER + 0.3:          # trembling, right over him
            j = int(t * 12.0)
            p = (p[0] + 2.2 * (hash01(j, 1) * 2 - 1), p[1] + 1.6 * (hash01(j, 2) * 2 - 1))
        K.dot(c, p, DOT_R * 1.7, col, seed=31)
        bass.ring(c, p, DOT_R * 2.9, 3.0, col, seed=32, alpha=0.55)


# ---------------------------------------------------------------- the callouts
def _shoe(c, heel, toe, w, seed):
    """One of her pumps from above, heel to toe: a pointed sole, the foot in it, the ankle."""
    dx, dy = toe[0] - heel[0], toe[1] - heel[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux

    def P(a, b):
        return (heel[0] + ux * a * L + nx * b * w, heel[1] + uy * a * L + ny * b * w)
    sole = [P(0.0, 0.0), P(0.04, -0.42), P(0.2, -0.5), P(0.55, -0.56), P(0.78, -0.42), P(0.95, -0.14), P(1.0, 0.0),
            P(0.95, 0.12), P(0.78, 0.4), P(0.55, 0.54), P(0.2, 0.48), P(0.04, 0.4)]
    B.edged(c, [bass.orient(bass.cut(sole, seed=seed, amp=0.3), True)], K.INK, K.PAPER, 5.0)
    throat = [P(0.62, -0.34), P(0.7, 0.0), P(0.62, 0.34)]
    bass.line_band(c, throat, K.PAPER, width=3.0, seed=seed + 1)
    ank = bass.ring_pts(P(0.18, 0.0), 0.3 * w, seed=seed + 2, n=32, amp=0.4)
    B.edged(c, [ank], K.INK, K.PAPER, 3.5)


def grating_view(cx, cy, r, t):
    """Looking down through her platform's grating: her shoes on the iron, close, and far
    below, in the lamp's light, the top of his hat."""
    def inside(c):
        K.fill(c, K.AMBER, (cx - r, cy - r, cx + r, cy + r))
        # him, far below: shoulders, the brim, a red band round the crown; he turns his head
        hx, hy = cx + 0.22 * r, cy + 0.3 * r
        turn = 16.0 * math.sin(2.0 * math.pi * 0.3 * (t - T_LENS1[0])) + 10.0
        sh = bass.draw.ellipse_pts((hx - 0.02 * r, hy + 0.06 * r), 0.42 * r, 0.17 * r, n=48, angle=turn)
        bass.fill_polys(c, [bass.orient(sh, True)], K.INK)
        brim = bass.draw.ellipse_pts((hx, hy), 0.24 * r, 0.21 * r, n=56, angle=turn)
        B.edged(c, [bass.orient(brim, True)], K.INK, K.AMBER, 4.0)
        band = bass.draw.ellipse_pts((hx, hy), 0.15 * r, 0.125 * r, n=48, angle=turn)
        bass.fill_polys(c, [bass.orient(band, True)], RED)
        crown = bass.draw.ellipse_pts((hx, hy), 0.12 * r, 0.095 * r, n=40, angle=turn)
        bass.fill_polys(c, [bass.orient(crown, True)], K.INK)
        # the grating: iron bars, a diamond lattice, between her and him
        bars = []
        sp, w = 0.34 * r, 0.05 * r
        for d in (1.0, -1.0):
            for i in range(-7, 8):
                o = i * sp
                bars.append(bass.line_pts([(cx - 1.6 * r, cy + o - d * 1.6 * r), (cx + 1.6 * r, cy + o + d * 1.6 * r)],
                                          width=w, seed=60 + i + (0 if d > 0 else 30)))
        bass.fill_polys(c, bars, K.INK)
        # her shoes on the iron, close, toes to the street; they tremble
        j = int(t * 12.0)
        jx, jy = 0.014 * r * (hash01(j, 7) * 2 - 1), 0.014 * r * (hash01(j, 8) * 2 - 1)
        _shoe(c, (cx - 0.86 * r + jx, cy - 0.5 * r + jy), (cx - 0.18 * r + jx, cy - 0.3 * r + jy), 0.27 * r, 71)
        _shoe(c, (cx - 0.7 * r + jx, cy - 0.92 * r + jy), (cx - 0.02 * r + jx, cy - 0.66 * r + jy), 0.27 * r, 74)
    return inside


def well_view(cx, cy, r, t):
    """Vertigo's stairwell, from above: the flights go round and down to a lit square far
    below, and the well stretches as he looks; his gloved hand slides along the rail."""
    def inside(c):
        K.fill(c, K.INK, (cx - r, cy - r, cx + r, cy + r))
        u = clamp((t - T_LENS2[0]) / (T_LENS2[1] - T_LENS2[0]))
        zoom = lerp(1.0, 1.45, ease("inout", u))
        cols = (K.STEEL, K.DEEP, K.NIGHT, K.SHUT, K.DEEP, K.SHUT, K.DEEP, K.INK)
        for i in range(8):
            s = 1.15 * r * (0.72 ** i) * zoom ** (1.0 + 0.35 * i)
            a = math.radians(9.0 * i + 22.0 * u)
            sq = [(cx + s * (math.cos(a + q) - math.sin(a + q)) / 1.414,
                   cy + s * (math.sin(a + q) + math.cos(a + q)) / 1.414) for q in (0.0, math.pi / 2, math.pi, 1.5 * math.pi)]
            bass.fill_polys(c, [bass.orient(sq, True)], cols[i])
            inner = [(lerp(x, cx, 0.12), lerp(y, cy, 0.12)) for x, y in sq]
            bass.line_band(c, inner + inner[:1], K.PAPER, width=max(1.5, 0.035 * s), seed=80 + i, alpha=0.85)
        s = 1.15 * r * (0.72 ** 8) * zoom ** 3.8
        K.fill(c, K.AMBER, (cx - s * 0.4, cy - s * 0.4, cx + s * 0.4, cy + s * 0.4))
        # his hand on the outer rail, sliding a little, the sleeve from the lens edge
        hx, hy = cx - 0.6 * r + 0.08 * r * ease("inout", u), cy + 0.42 * r
        bass.line_band(c, [(cx - 1.2 * r, cy + 0.95 * r), (hx - 0.05 * r, hy + 0.06 * r)], K.INK, width=0.24 * r, seed=90)
        fist = bass.ring_pts((hx, hy), 0.11 * r, seed=91, n=36, amp=0.5)
        B.edged(c, [fist], K.INK, K.STEEL, 3.0)
        for f in range(4):
            fx = hx + 0.03 * r + 0.05 * r * f - 0.06 * r
            K.dot(c, (fx, hy - 0.1 * r + 0.012 * r * f), 0.035 * r, K.INK, seed=92 + f)
    return inside


# ---------------------------------------------------------------- the X and the rings
def crossing(c, t):
    """Where each went in and where each ended up: two arrows across the street, an X."""
    his0, hers0 = (707.0, K.GROUND - 24.0), (K.ESCAPE_X[1] - 19.0, K.GROUND - 24.0)
    his1, _ = head("his", 99.0)
    hers1, _ = head("hers", 99.0)
    K.arrow(c, his0, (his1[0] + 30.0, his1[1] + 8.0), RED, width=11.0, head=38.0, u=k(t, T_X, 0.4, "out3"), seed=41)
    K.arrow(c, hers0, (hers1[0] - 30.0, hers1[1] + 8.0), K.PAPER, width=11.0, head=38.0,
            u=k(t, T_X + 0.15, 0.4, "out3"), seed=42)


def rings(c, t):
    if t < T_RINGS:
        return
    g = ease("outback", clamp((t - T_RINGS) / 0.3))
    for name, col, t0 in (("his", RED, T_RINGS), ("hers", K.PAPER, T_RINGS + 0.1)):
        p, _ = head(name, t)
        gg = ease("outback", clamp((t - t0) / 0.3))
        if gg > 0.0:
            bass.ring(c, p, 34.0 * gg, 6.0, col, seed=51 if name == "his" else 52, n=48)
    if g > 0.0:
        p, _ = head("hers", t)
        K.heartbeat(c, p, t, color=K.PAPER, bpm=132.0, r0=14.0, r1=80.0, width=4.0, life=0.8, seed=53)


# ---------------------------------------------------------------- the camera
CAM = ((0.0, (470.0, 1300.0, 1.55)), (T_STOP, (468.0, 1310.0, 1.62)), (T_IN, (440.0, 1380.0, 2.0)),
       (T_IN + 1.3, (540.0, 960.0, 1.0)), (T_X, (540.0, 960.0, 1.0)), (14.0, (540.0, 990.0, 1.07)))


def camera(t):
    for (t0, a), (t1, b) in zip(CAM, CAM[1:]):
        if t <= t1:
            u = ease("inout3" if t1 - t0 < 2.0 else "inout", clamp((t - t0) / (t1 - t0)))
            return tuple(lerp(x, y, u) for x, y in zip(a, b))
    return CAM[-1][1]


def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        cx, cy, z = camera(t)
        c.translate(540.0, 960.0)
        c.scale(z, z)
        c.translate(-cx, -cy)
        lit = {(HIS_B, K.HIS_FLOOR): K.AMBER}
        K.draw_section(c, t, lit=lit, people=people(t), open_windows={HER_B: {K.HER_FLOOR}},
                       street_doors=(HIS_B, HER_B) if t >= T_IN else (HIS_B,),
                       ladder=k(t, T_LADDER, 0.3, "outback"), overturned=True, beams={(HIS_B, K.HIS_FLOOR)})
        bulbs(c)
        numbers(c, t)
        trail(c, "his", t, RED)
        trail(c, "hers", t, K.PAPER)
        # the near miss: he listens; a far horn lets them go
        if T_LISTEN <= t < T_IN:
            p, _ = head("his", t)
            for j in range(3):
                K.ripple(c, (p[0], p[1] - 40.0), t, T_LISTEN + 0.55 * j, RED, n=1, life=1.3, r0=20.0, r1=240.0,
                         width=5.0, seed=60 + j)
        if t >= T_HORN:
            K.ripple(c, (cx + 540.0 / z - 10.0, K.GROUND - 30.0), t, T_HORN, K.PAPER, n=2, every=0.18,
                     life=0.6, r0=6.0, r1=70.0, width=4.0, seed=70)
        crossing(c, t)
        rings(c, t)
        # the callouts (in world px, so they ride the camera)
        if T_LENS1[0] <= t < T_LENS1[1] + 0.3:
            u = k(t, T_LENS1[0], 0.3, "out3") * (1.0 - k(t, T_LENS1[1], 0.3, "in3"))
            anchor, _ = head("hers", t)
            ctr, r = (578.0, 1270.0), 92.0
            K.callout(c, anchor, ctr, r, grating_view(ctr[0], ctr[1], r, t), u=u, color=K.PAPER, ring_w=5.0, dot_r=0.0,
                      line_w=2.5, seed=81)
        if T_LENS2[0] <= t < T_LENS2[1] + 0.3:
            u = k(t, T_LENS2[0], 0.3, "out3") * (1.0 - k(t, T_LENS2[1], 0.3, "in3"))
            anchor, _ = head("his", t)
            ctr, r = (560.0, 1110.0), 150.0
            K.callout(c, anchor, ctr, r, well_view(ctr[0], ctr[1], r, t), u=u, color=RED, ring_w=8.0, dot_r=0.0,
                      line_w=4.0, seed=82)


def motion_blur(t, T):
    return 1


def cues(T):
    P = paths()
    out = []
    for name, sfx, g in (("his", "his footstep (red dot lands): slow, heavy, careful", -12),
                         ("hers", "her footstep (paper dot lands): quick, light; iron on the fire escape", -14)):
        for ti in P[name][1]:
            out.append(Cue(ti, sfx, gain_db=g, pan=-0.3 if name == "his" else 0.3))
    out += [Cue(T_STOP, "both stop: silence; one held breath", gain_db=-10),
            Cue(T_LISTEN, "a heartbeat under the silence (her)", gain_db=-12, dur=T_HORN - T_LISTEN),
            Cue(T_HORN, "a far car horn releases it", gain_db=-16, pan=0.8),
            Cue(T_IN, "her street door opens and closes behind him", gain_db=-12),
            Cue(T_LADDER, "the drop ladder slides down: iron clang", gain_db=-8),
            Cue(T_LADDER + 0.4, "the race: a canon of plucked notes, his slow (a semitone a landing), hers quick",
                gain_db=-10, dur=11.6 - T_LADDER - 0.4),
            Cue(T_LENS2[0], "Vertigo: a swirling string figure under the stairwell callout", gain_db=-10,
                dur=T_LENS2[1] - T_LENS2[0]),
            Cue(T_X, "the X: two notes cross (a falling and a rising)", gain_db=-8),
            Cue(T_RINGS, "the rings: a held chord, her heartbeat on top", gain_db=-10, dur=14.0 - T_RINGS)]
    return out
