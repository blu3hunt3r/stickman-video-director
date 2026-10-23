"""s01 · TITLE (0-12): the red dot ticks; the Bass title; night falls on the street; the two
buildings are cut open storey by storey, every room lit and lived in; the city goes to bed,
light by light, until only hers and his are lit; the camera pushes in on her room."""
import math
from functools import lru_cache

from engine import bass, mocap as mc, paperdoll as pd
from engine.core import clamp, ease, lerp
from engine.palette import RED
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import folk as F
from films.opposite_full import kit as K

k = K.k
HER_B, HIS_B = K.HER_B, K.HIS_B

# ---------------------------------------------------------------- beats (scene time; 120 bpm from 0)
T_DOT = (0.25, 0.5, 0.75)         # the red dot pops, then ticks larger twice
R_DOT = (20.0, 30.0, 42.0)
T_DOT_OUT = 0.85                  # ... and shrinks away by 1.0
T_TITLE = 1.0                     # the Bass title, at tb = t - T_TITLE
T_NIGHT = 5.4                     # the letters are windows now: night falls
T_BARS = 5.5                      # teal bars slide over the paper
T_CITY = 5.75                     # the far city rises behind
T_MOON = 6.0                      # the moon drops in
T_CUT = 6.5                       # the cutaway: the slabs open into the section, the lit windows into rooms
T_STOREY = tuple(7.0 + 0.25 * i for i in range(6))      # storey n snaps in at T_STOREY[n - 1], both buildings
T_OPEN = T_STOREY[-1] + 0.15      # the whole section is open
LIGHTS_OUT = ((HIS_B, 2), (HER_B, 5), (HIS_B, 6), (HER_B, 2), (HIS_B, 3), (HER_B, 3), (HIS_B, 4))
T_OUT = tuple(8.5 + 0.25 * i for i in range(len(LIGHTS_OUT)))
T_FRIDGE = T_OUT[2] - 0.2         # the fridge door shuts just before that light goes
T_TV_OFF = T_OUT[-1]              # the television, left on in the dark room, blinks out
T_NUMS = 10.25                    # her 4 turns paper, his 5 red
T_PUSH = (10.5, 12.0)             # push in on her room ...
PUSH = 3.2                        # ... this far, her floor landing on the side stage's floor line
STAGE_FLOOR = 1560.0

NUM_DIM = lerp(K.NIGHT, K.PAPER, 0.35)


# ---------------------------------------------------------------- 0-1: the red dot
def draw_dot(c, t):
    K.fill(c, K.INK)
    r = 0.0
    for t0, r1, r0 in zip(T_DOT, R_DOT, (0.0,) + R_DOT[:-1]):
        if t >= t0:
            r = lerp(r0, r1, ease("outback", clamp((t - t0) / 0.1)))
    r *= 1.0 - k(t, T_DOT_OUT, 0.15, "in3")
    if r > 0.5:
        K.dot(c, (540.0, 960.0), r, RED, seed=5)


# ---------------------------------------------------------------- 5.4-6.5: night falls
def draw_night(c, t):
    tb = t - T_TITLE
    K.fill(c, K.PAPER)
    u = k(t, T_BARS, 0.6, "linear")
    if u > 0.0:
        bass.bars(c, u, n=7, axis="h", colors=(K.NIGHT,), frm="alt", mode="slide", overlap=0.55, seed=11, bleed=3.0)
    rise = k(t, T_CITY, 0.5, "out3")
    if rise > 0.0:
        c.save()
        c.translate(0.0, 1150.0 * (1.0 - rise))
        K.skyline(c)
        c.restore()
    drop = k(t, T_MOON, 0.45, "outback")
    if drop > 0.0:
        K.moon(c, (K.MOON_E[0], lerp(-110.0, K.MOON_E[1], drop)))
    for j, Bk in enumerate((B.LEFT_B, B.RIGHT_B)):
        bass.fill_polys(c, [bass.cut_rect(*Bk, seed=20 + j)], K.INK)
    for r in B.LEFT_WIN + B.RIGHT_WIN:
        bass.fill_polys(c, [bass.cut_rect(*r, seed=int(r[0] + r[1]))], K.window_color(r, tb))


# ---------------------------------------------------------------- the lives in the rooms
@lru_cache(maxsize=1)
def perfs():
    C = mc.Clip.load
    man, vic = B.win_fig(1), B.win_fig(2)
    return dict(
        man=mc.Performance(man, [mc.Seg(C("80_48"), 1.0, 7.75, at=6.6, speed=0.55)], facing=1, near="Left"),
        vic=mc.Performance(vic, [mc.Seg(C("80_48"), 0.4, 7.9, at=6.6, speed=0.55)], facing=-1, near="Left"),
        stretch=mc.Performance(F.small("curls"), [mc.Seg(C("56_02"), 19.3, 23.0, at=7.2, speed=0.95, travel=0.0)],
                               facing=-1, near="Right"),
        sip=mc.Performance(F.small("bun"), [mc.Seg(C("137_26"), 6.2, 9.9, at=7.1, speed=0.95, travel=0.0)],
                           facing=-1, near="Right"),
    )


def lit_rooms(t):
    """{(building, storey): colour} of the rooms whose light is on at t."""
    lit = {(b, n): K.AMBER for b in (HER_B, HIS_B) for n in range(2, b.floors + 1)}
    for room, t0 in zip(LIGHTS_OUT, T_OUT):
        if t >= t0:
            del lit[room]
    return lit


def city_lit(t):
    """How much of the far city is lit: it comes on with the rooms and goes to bed with them."""
    on = 0.5 * k(t, T_STOREY[0], T_STOREY[-1] - T_STOREY[0] + 0.25)
    return on * (1.0 - sum(1 for t0 in T_OUT if t >= t0) / len(T_OUT))


def _out_at(b, n):
    for room, t0 in zip(LIGHTS_OUT, T_OUT):
        if room == (b, n):
            return t0
    return 99.0


def her_pose(t):
    """At the stove, waiting on the kettle: head down, a hand out toward it."""
    fig = B.win_fig(0)
    st = pd.standing(fig, 0.0)
    sway = math.sin(2.0 * math.pi * 0.3 * t)
    p = pd.Pose(lean=5.0 + 1.5 * sway, head=-10.0, arms={"near": ("ang", 34.0, 58.0), "far": ("ang", 18.0, 52.0)})
    return fig, st, p


def people(t, lit):
    P = perfs()
    t2 = K.twos(t)

    def fn(c, b, n, room):
        x0, y0, x1, y1 = room
        fy = y1
        L = lit.get((b, n))
        tt = min(t2, _out_at(b, n))               # once the light is off, they are still
        if b is HER_B and n == K.HER_FLOOR:
            fig, st, p = her_pose(tt)
            F.draw(c, fig, st, p, 232.0, fy, -1, L)
            B.steam(c, (187.0, fy - 62.0), tt, K.INK, alpha=0.9, scale=0.55)
        elif b is HIS_B and n == K.HIS_FLOOR:
            st, p = P["man"](tt)
            F.draw(c, B.win_fig(1), st, p, 758.0, fy, 1, L)
            st, p = P["vic"](tt)
            F.draw(c, B.win_fig(2), st, p, 866.0, fy, -1, L)
        elif b is HER_B and n == 2:               # the radio, and an old man nodding along to it
            fig = F.small("bald")
            p = pd.Pose(lean=-7.0, head=-2.0 + 5.0 * abs(math.sin(math.pi * 2.0 * tt)),
                        arms={"near": ("ang", 16.0, 74.0), "far": ("ang", 10.0, 70.0)})
            F.draw(c, fig, F.seated(fig, 0.0, -1, 36.0), p, 276.0, fy, -1, L)
            if L is not None:
                beat = math.floor(t / 0.5) * 0.5
                K.ripple(c, (204.0, fy - 66.0), t, beat, K.PAPER, n=2, every=0.12, life=0.45, r0=4.0, r1=26.0,
                         width=3.0, seed=n)
        elif b is HER_B and n == 3:               # the television, and a woman sunk in her chair
            tv_on = t < T_TV_OFF
            if tv_on:
                h = (math.floor(t * 12.0) * 0.618) % 1.0
                glow = lerp(K.STEEL, K.PAPER, 0.35 + 0.5 * h)
                bass.fill_polys(c, [bass.orient([(214.0, fy - 54.0), (236.0, fy - 66.0), (306.0, fy - 18.0),
                                                 (306.0, fy)], True)], K.PAPER, 0.10)
                bass.fill_polys(c, [bass.cut_rect(198.0, fy - 56.0, 230.0, fy - 31.0, seed=330, amp=0.4)], glow)
            elif t < T_TV_OFF + 0.12:                # it blinks out to a dot
                u = (t - T_TV_OFF) / 0.12
                bass.fill_polys(c, [bass.cut_rect(214.0 - 16.0 * (1 - u), fy - 44.0 - 1.5, 214.0 + 16.0 * (1 - u),
                                                  fy - 44.0 + 1.5, seed=331, amp=0.2)], K.PAPER)
            fig = F.small("bun")
            p = pd.Pose(lean=-11.0, head=-3.0, arms={"near": ("ang", 14.0, 66.0), "far": ("ang", 8.0, 62.0)})
            F.draw(c, fig, F.seated(fig, 0.0, -1, 36.0), p, 282.0, fy, -1, L)
        elif b is HER_B and n == 5:               # stretching, before bed
            st, p = P["stretch"](tt)
            F.draw(c, F.small("curls"), st, p, 292.0, fy, -1, L)
        elif b is HIS_B and n == 2:               # asleep already, the bedside lamp still on
            F.sleeper(c, 769.0, fy, tt, L)
        elif b is HIS_B and n == 3:               # a late supper
            fig = F.small("bald")
            spoon = 0.5 - 0.5 * math.cos(2.0 * math.pi * tt / 1.4)
            p = pd.Pose(lean=9.0, head=-6.0 + 4.0 * spoon,
                        arms={"near": ("ang", lerp(48.0, 22.0, spoon), lerp(44.0, 128.0, spoon)), "far": ("ang", 46.0, 46.0)})
            F.draw(c, fig, F.seated(fig, 0.0, -1, 27.0, reach=0.9), p, 822.0, fy, -1, L)
        elif b is HIS_B and n == 4:               # a nightcap at the window
            st, p = P["sip"](tt)
            p.hold["near"] = B.mug_hold(tt)
            F.draw(c, F.small("bun"), st, p, 744.0, fy, -1, L)
        elif b is HIS_B and n == 6:               # the fridge, at midnight
            fig = F.small("cap")
            shut = k(t, T_FRIDGE, 0.15, "out3")
            if L is not None and shut < 1.0:
                bass.fill_polys(c, [bass.cut_rect(733.0, fy - 99.0, 767.0, fy - 6.0, seed=360, amp=0.4)], K.PAPER)
                bass.fill_polys(c, [bass.orient([(767.0, fy - 99.0), (918.0, fy - 150.0), (918.0, fy),
                                                 (767.0, fy - 6.0)], True)], K.PAPER, 0.16)
            p = pd.Pose(lean=lerp(20.0, 2.0, shut), head=lerp(-14.0, 0.0, shut),
                        arms={"near": ("ang", lerp(76.0, 24.0, shut), lerp(14.0, 70.0, shut)),
                              "far": ("ang", lerp(40.0, 8.0, shut), lerp(30.0, 20.0, shut))})
            F.draw(c, fig, pd.standing(fig, 0.0), p, 804.0, fy, -1, L)
    return fn


# ---------------------------------------------------------------- 6.5-8.4: the cutaway
def band(b, n):
    """The slice of building b that storey n's cut opens (her fire escape with hers)."""
    x0 = b.x0 - 12.0
    x1 = K.ESCAPE_X[1] + 10.0 if b is HER_B else b.x1 + 12.0
    y0 = K.level(n + 1) if n < b.floors else b.roof - 240.0
    y1 = K.level(n) if n > 1 else K.GROUND + 12.0
    return x0, y0, x1, y1


def reveal_clip(c, t):
    """Clip to what the cut has opened by t (each storey wipes up from its floor)."""
    c.new_path()
    for i, t0 in enumerate(T_STOREY):
        u = k(t, t0, 0.12, "out3")
        if u <= 0.0:
            continue
        for b in (HER_B, HIS_B):
            if i + 1 <= b.floors:
                x0, y0, x1, y1 = band(b, i + 1)
                h = (y1 - y0) * u
                c.rectangle(x0, y1 - h, x1 - x0, h)
    c.clip()


def draw_morph(c, t):
    """The elevation becoming the section: the slabs take the sections' outlines, her lit
    window and his slide and open into their rooms, the dark windows close up."""
    m = k(t, T_CUT, 0.5, "inout3")
    tb = t - T_TITLE
    for j, (Bk, b) in enumerate(((B.LEFT_B, HER_B), (B.RIGHT_B, HIS_B))):
        tgt = (b.x0 - 6.0, b.roof - 26.0, b.x1 + 6.0, K.GROUND + 12.0)
        r = tuple(lerp(a, z, m) for a, z in zip(Bk, tgt))
        bass.fill_polys(c, [bass.cut_rect(*r, seed=20 + j)], K.INK)
        for wr in (B.LEFT_WIN if j == 0 else B.RIGHT_WIN):
            # the window rides its slab
            fx0, fy0 = (wr[0] - Bk[0]) / (Bk[2] - Bk[0]), (wr[1] - Bk[1]) / (Bk[3] - Bk[1])
            fx1, fy1 = (wr[2] - Bk[0]) / (Bk[2] - Bk[0]), (wr[3] - Bk[1]) / (Bk[3] - Bk[1])
            ride = (lerp(r[0], r[2], fx0), lerp(r[1], r[3], fy0), lerp(r[0], r[2], fx1), lerp(r[1], r[3], fy1))
            if wr == B.HER_WIN or wr == B.HIS_WIN:
                room = K.her_room() if wr == B.HER_WIN else K.his_room()
                q = tuple(lerp(a, z, m) for a, z in zip(wr, room))
                bass.fill_polys(c, [bass.cut_rect(*q, seed=int(wr[0] + wr[1]))], K.AMBER)
            else:
                s = 1.0 - k(t, T_CUT, 0.3, "in3")
                if s > 0.02:
                    cx, cy = (ride[0] + ride[2]) / 2.0, (ride[1] + ride[3]) / 2.0
                    hw, hh = (ride[2] - ride[0]) * s / 2.0, (ride[3] - ride[1]) * s / 2.0
                    bass.fill_polys(c, [bass.cut_rect(cx - hw, cy - hh, cx + hw, cy + hh, seed=int(wr[0] + wr[1]))],
                                    K.window_color(wr, tb))


def beams_at(t):
    """Only hers and his throw their light across the street (once the cut has opened them)."""
    return {(b, n) for b, n in ((HER_B, K.HER_FLOOR), (HIS_B, K.HIS_FLOOR)) if t >= T_STOREY[n - 1] + 0.06}


def draw_beams(c, lit, t):
    c.save()
    K.clip_rect(c, (K.STREET[0], 0.0, K.STREET[1], K.GROUND))
    for room in beams_at(t):
        K.beam(c, *room, lit[room])
    c.restore()


def draw_numbers(c, t):
    """The floor numbers pop in beside each storey as it opens; at T_NUMS hers turns paper
    and his red."""
    for b in (HER_B, HIS_B):
        x = b.x0 - 22.0 if b.side > 0 else b.x1 + 22.0
        for n in range(1, b.floors + 1):
            g = ease("outback", clamp((t - T_STOREY[n - 1] - 0.05) / 0.2))
            if g <= 0.01:
                continue
            col = NUM_DIM
            if (b, n) in ((HER_B, K.HER_FLOOR), (HIS_B, K.HIS_FLOOR)) and t >= T_NUMS:
                col = K.PAPER if b is HER_B else RED
                g *= 1.0 + 0.6 * (1.0 - ease("out3", clamp((t - T_NUMS) / 0.3)))
            K.numeral(c, str(n), (x, (K.level(n) + K.level(n + 1)) / 2.0), 40.0, col, seed=40 + n + b.seed, scale=g)


def draw_city(c, t):
    lit = lit_rooms(t)
    moon_at = tuple(lerp(a, z, k(t, T_CUT, 0.5, "inout3")) for a, z in zip(K.MOON_E, K.MOON_S))
    kw = dict(lit=lit, people=people(t, lit), sky_lit=city_lit(t), moon_at=moon_at)
    if t < T_OPEN:
        K.fill(c, K.NIGHT)
        K.skyline(c, lit=kw["sky_lit"])
        K.moon(c, moon_at)
        draw_morph(c, t)
        # the ground rises with the slabs
        bass.fill_polys(c, [bass.cut_rect(-20.0, lerp(1960.0, K.GROUND, k(t, T_CUT, 0.5, "inout3")), K.W + 20.0,
                                          K.H + 20.0, seed=900, amp=0.8)], K.INK)
        # her light and his, across the street (inside the opened storeys the section draws
        # them itself, under her fire escape)
        draw_beams(c, lit, t)
        if t >= T_STOREY[0]:
            c.save()
            reveal_clip(c, t)
            K.draw_section(c, t, beams=beams_at(t) or False, **kw)
            c.restore()
        up = k(t, T_STOREY[1], 0.3, "outback")
        if up > 0.0:                             # the street lamp grows out of the pavement
            c.save()
            c.translate(K.LAMP[0], K.GROUND)
            c.scale(1.0, up)
            c.translate(-K.LAMP[0], -K.GROUND)
            K.street(c, t, lamp_on=t >= T_STOREY[1] + 0.3)
            c.restore()
    else:
        K.draw_section(c, t, beams=beams_at(t), **kw)
    draw_numbers(c, t)


# ---------------------------------------------------------------- the scene
def push(t):
    """(fixed point, scale) of the push in on her room: it ends with her room centred and
    her floor on the side stage's floor line."""
    x0, y0, x1, y1 = K.her_room()
    cx, fy = (x0 + x1) / 2.0, y1
    # x' = fx + s (x - fx) must send cx to 540 and her floor to STAGE_FLOOR at s = PUSH
    fx = (540.0 - PUSH * cx) / (1.0 - PUSH)
    fyy = (STAGE_FLOOR - PUSH * fy) / (1.0 - PUSH)
    s = lerp(1.0, PUSH, k(t, T_PUSH[0], T_PUSH[1] - T_PUSH[0], "inout3"))
    return (fx, fyy), s


def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        if t < T_TITLE:
            draw_dot(c, t)
        elif t < T_NIGHT:
            B.draw_title_shot(c, t - T_TITLE)
        elif t < T_CUT:
            draw_night(c, t)
        else:
            (fx, fy), s = push(t)
            c.save()
            if s > 1.0001:
                c.translate(fx, fy)
                c.scale(s, s)
                c.translate(-fx, -fy)
            draw_city(c, t)
            c.restore()


def motion_blur(t, T):
    return 1


def cues(T):
    out = [Cue(t0, "the red dot ticks: a dry clock tick", gain_db=-8) for t0 in T_DOT]
    out.append(Cue(T_TITLE, "the Bass cut's title sound from its start (strips, the red cut at +2.0, the halves part)",
                   gain_db=-6))
    out += [Cue(T_BARS, "night falls: a low gong under the teal bars", gain_db=-8),
            Cue(T_CITY, "the city rises: a pizzicato descent", gain_db=-10),
            Cue(T_MOON, "the moon drops: a soft bell", gain_db=-12)]
    out += [Cue(t0, f"the cutaway: a click as storey {i + 1} opens (rising)", gain_db=-12) for i, t0 in enumerate(T_STOREY)]
    out += [Cue(T_STOREY[1], "the radio through the wall: a faint dance band, till the light goes", gain_db=-24,
                dur=T_OUT[3] - T_STOREY[1]),
            Cue(T_STOREY[2], "a television murmur, till it blinks out", gain_db=-26, dur=T_TV_OFF - T_STOREY[2])]
    out += [Cue(t0, f"light out ({'hers' if b is HER_B else 'his'} building, storey {n}): a plucked note, descending",
                gain_db=-10) for (b, n), t0 in zip(LIGHTS_OUT, T_OUT)]
    out += [Cue(T_FRIDGE, "the fridge door thumps shut", gain_db=-18),
            Cue(T_NUMS, "her 4 and his 5: two notes, hers high, his low", gain_db=-8),
            Cue(T_PUSH[0], "a rising tremolo into her room, to the cut", gain_db=-8, dur=T_PUSH[1] - T_PUSH[0])]
    return out
