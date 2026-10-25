"""s01 · TITLE (0-14): the red dot ticks in the black; the Bass title, DOUBLE over CROSS, and a
paper strip and a red one slash across into an X; the halves part and the letters fly into the
street's windows (DOUBLE's E is the crew's window, CROSS's O the bank's clock); night falls; the
street is cut open storey by storey, then down to the sewer and the vault's gold; the city goes
to bed light by light, till three lights are left in a line down across the street (the crew's
room, the guard's lamp, the gold); the camera pushes in on the crew's room, to s02's first frame."""
import math
from functools import lru_cache

from engine import bass, paperdoll as pd
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import folk as FO
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import room as R
from films.double_cross_opposite import street as St

k = K.k
INK, PAPER, AMBER, RED, NIGHT, STEEL, DEEP, SHUT = K.INK, K.PAPER, K.AMBER, K.RED, K.NIGHT, K.STEEL, K.DEEP, K.SHUT
W, H = K.W, K.H
C0 = (W / 2.0, H / 2.0)

# ---------------------------------------------------------------- beats (scene time = film time; 120 bpm from 0)
T_DOT = (0.25, 0.5, 0.75)             # the red dot pops, then ticks larger twice
R_DOT = (16.0, 24.0, 32.0)
T_DOT_OUT = 0.85                      # ... and shrinks away by 1.0
T_TITLE = 1.0                         # the title shot: Psycho's strips race at tb = t - T_TITLE
T_LEAD = 1.125                        # three frames of black first
T_WORDS = ((1.3, 1.0), (1.55, 1.0))   # DOUBLE, CROSS assemble: (start, duration)
T_STRIPS = (2.75, 3.0)                # the paper strip lands, then the red one across it: an X
STRIP_IN = 0.24                       # each slashes in over this long, landing on its beat
STRIP_W = 118.0
T_PART = 3.4                          # the X lifts off; the halves part, letter by letter, into windows
FLY = 0.55
STAGGER = 0.035
T_FLOOD = 4.1                         # paper floods in round the two slabs
T_MORPH = 4.3                         # the letters become windows (each over MORPH_DUR, staggered)
MORPH_DUR = 0.55
T_NIGHT = 5.5                         # night falls: teal bars over the paper; the windows snap
T_CITY = 5.75                         # the far city rises
T_MOON = 6.0                          # the moon drops in
T_CUT = 6.5                           # the cutaway (the moon slides over the bank)
T_STOREY = (6.75, 7.0, 7.25, 7.5, 7.75)       # the tenement's storeys 1..5 open; the bank's hall, offices with 1, 2, 3
T_LAMP = 7.0                          # the street lamp grows out of the pavement, and lights
T_UNDER = (8.0, 1.0)                  # the road opens down to the sewer: (start, duration)
T_VAULT = 8.5                         # the vault opens on its gold
T_SECTION = 9.0                       # everything is open
OUT_ORDER = (5, 2, 3)                 # the city goes to bed: these storeys' lights go out ...
T_OUT = (9.0, 9.5, 10.0)              # ... on these beats
T_CITY_OUT = 10.5                     # the far city's last lights
T_FOUR = 10.75                        # the crew's 4 turns paper
T_PUSH = (11.5, 2.5)                  # the push in on the crew's room, to s02's first frame (R.S01_END)

CLOCK_BANK = (11, 57)                 # the bank's clock on the elevation
CAR = dict(lights=0.0)                # the Knight's car at the bank's curb, parked
NUM_DIM = lerp(NIGHT, PAPER, 0.35)
_DIAG = math.atan2(H, W)              # the frame's diagonal (the X's arms)


def motion_blur(t, T):
    return 1


# ---------------------------------------------------------------- 0-1: the red dot
def draw_dot(c, t):
    K.fill(c, INK)
    r = 0.0
    for t0, r1, r0 in zip(T_DOT, R_DOT, (0.0,) + R_DOT[:-1]):
        if t >= t0:
            r = lerp(r0, r1, ease("outback", clamp((t - t0) / 0.1)))
    r *= 1.0 - k(t, T_DOT_OUT, 0.15, "in3")
    if r > 0.5:
        K.dot(c, C0, r, RED, seed=5)


# ---------------------------------------------------------------- 1-5.5: the title
WORDS = (("DOUBLE", (540.0, 282.0), 520.0), ("CROSS", (540.0, 1640.0), 480.0))


@lru_cache(maxsize=None)
def glyphs(w):
    word, _, width = WORDS[w]
    return bass.title_glyphs(word, width=width, tracking=0.06, seed=7, rough=0.8, jitter=0.6)


@lru_cache(maxsize=1)
def destinations():
    """Where each letter lands: [("rect", r) | ("disc", (centre, r))] per word. DOUBLE fills the
    tenement's storeys 5 and 4 (its E is the crew's window); CROSS the bank's top storey, its O
    the clock in the pediment."""
    ten = [("rect", St.ten_window_e(n, j)) for n in (5, 4) for j in range(3)]
    top = sorted((key[2], r) for key, r in St.elevation_windows() if key[:2] == ("bank", 3))
    bank = [("rect", top[0][1]), ("rect", top[1][1]), ("disc", (St.CLOCK_E, 24.0)), ("rect", top[2][1]),
            ("rect", top[3][1])]
    return ten, bank


LETTER_KEYS = {("ten", 5, 0), ("ten", 5, 1), ("ten", 5, 2), ("ten", 4, 0), ("ten", 4, 1), ("ten", 4, 2),
               ("bank", 3, 0), ("bank", 3, 1), ("bank", 3, 2), ("bank", 3, 3)}


def _dest_geom(d):
    """(centre, height, outline) of a destination."""
    kind, v = d
    if kind == "rect":
        r = v
        return ((r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0), r[3] - r[1], B.rect_pts(r)
    (cx, cy), rr = v
    ring = [(cx + rr * math.cos(2.0 * math.pi * i / 96), cy + rr * math.sin(2.0 * math.pi * i / 96)) for i in range(96)]
    return (cx, cy), 2.0 * rr, ring


def _letter_start(w, i):
    return T_PART + STAGGER * i + 0.1 * w


def letter_contours(w, i, t):
    """Letter i of word w in frame px at t: flown from the title toward its window."""
    T = glyphs(w)
    g = T[i]
    at = WORDS[w][1]
    centre, dh, _ = _dest_geom(destinations()[w][i])
    u = k(t, _letter_start(w, i), FLY, "inout3")
    gh = g.bbox[3] - g.bbox[1]
    s = lerp(1.0, dh / gh, u)
    pw = (at[0] + g.pivot[0], at[1] + g.pivot[1])
    pos = (lerp(pw[0], centre[0], u), lerp(pw[1], centre[1], u))
    return [[(pos[0] + (x - g.pivot[0]) * s, pos[1] + (y - g.pivot[1]) * s) for x, y in cont] for cont in g.polys]


def _shrink(p, s):
    if s <= 0.02:
        return None
    cx = sum(x for x, _ in p) / len(p)
    cy = sum(y for _, y in p) / len(p)
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in p]


def draw_letters(c, t):
    for w in (0, 1):
        for i in range(len(glyphs(w))):
            polys = letter_contours(w, i, t)
            m = k(t, T_MORPH + 0.04 * i + 0.1 * w, MORPH_DUR, "inout3")
            if m <= 0.0:
                bass.fill_polys(c, polys, PAPER, evenodd=True)
                continue
            outer = max(polys, key=lambda p: abs(bass.poly_area(p)))
            _, _, target = _dest_geom(destinations()[w][i])
            shape = bass.morph_outline(outer, target, m, n=120)
            holes = [_shrink(p, 1.0 - clamp(m * 2.2)) for p in polys if p is not outer]
            bass.fill_polys(c, [bass.orient(shape, True)] + [bass.orient(h, False) for h in holes if h], PAPER)


def draw_words(c, t):
    """DOUBLE and CROSS assembling from cut strips (the Bass cut's split), then held."""
    for w, (t0, dur) in enumerate(T_WORDS):
        if t < t0:
            continue
        split = 1.0 - k(t, t0, dur, "out5")
        bass.draw_title(c, glyphs(w), WORDS[w][1], PAPER, anim="split" if split > 0.0 else None, u=split, strips=6,
                        angle=0.0, dist=1100.0, irregular=0.5, ease="linear", seed=5 + w)


def _strip_poly(a, b, w, seed):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    n = (-dy / L * w / 2.0, dx / L * w / 2.0)
    pts = [(a[0] + n[0], a[1] + n[1]), (b[0] + n[0], b[1] + n[1]), (b[0] - n[0], b[1] - n[1]), (a[0] - n[0], a[1] - n[1])]
    return bass.orient(bass.cut(pts, seed=seed, amp=0.9, seg=(60.0, 180.0)), True)


def draw_x(c, t):
    """The paper strip along one diagonal, the red one across it: each slashes in along its own
    axis, landing on its beat with a settle; at T_PART each carries on along its axis and off."""
    for i, (t0, col) in enumerate(((T_STRIPS[0], PAPER), (T_STRIPS[1], RED))):
        if t < t0 - STRIP_IN:
            continue
        ang = _DIAG if i == 0 else math.pi - _DIAG
        d = (math.cos(ang), math.sin(ang))
        L = 1350.0
        p = clamp((t - (t0 - STRIP_IN)) / STRIP_IN)
        off = -(1.0 - ease("outback", p)) * 2400.0 + k(t, T_PART + 0.06 * i, 0.3, "in3") * 2700.0
        if off > 2650.0:
            continue
        a = (C0[0] - d[0] * L + d[0] * off, C0[1] - d[1] * L + d[1] * off)
        b = (C0[0] + d[0] * L + d[0] * off, C0[1] + d[1] * L + d[1] * off)
        bass.fill_polys(c, [_strip_poly(a, b, STRIP_W, 70 + i)], col)


@lru_cache(maxsize=1)
def slab_polys():
    """The two buildings as flat slabs (the elevation's outlines) and the ground they stand on."""
    b = St.TEN
    ten = [St._r(b.x0, b.roof, b.x1, St.GROUND + 4.0, 1101, 0.6)] + St._ten_shell()[-2:]
    bank = St._bank_face_polys()[0][0]
    ground = [St._r(-20.0, St.GROUND, W + 20.0, H + 20.0, 1102, 0.8),
              St._r(b.x0, St.GROUND - 30.0, b.x1, St.GROUND + 30.0, 1103, 0.3),          # no seams at their feet
              St._r(St.BANK[0], St.GROUND - 30.0, St.BANK[1], St.GROUND + 30.0, 1104, 0.3)]
    return ten + bank + ground


def draw_title_shot(c, t):
    K.fill(c, INK)
    if t < T_LEAD:
        return
    flood = k(t, T_FLOOD, 0.4, "linear")
    if flood > 0.0:
        bass.bars(c, flood, n=6, axis="v", colors=(PAPER,), frm="alt", mode="slide", overlap=0.5, seed=4, bleed=3.0)
        bass.fill_polys(c, slab_polys(), INK)
    tb = t - T_TITLE
    if tb < 1.6:
        B.draw_strips(c, tb)
    if t < T_PART:
        draw_words(c, t)
    else:
        draw_letters(c, t)
    draw_x(c, t)


# ---------------------------------------------------------------- 5.5-6.5: night falls
def night_colour(key):
    if key[0] == "ten":
        return AMBER if key[1] >= 2 else SHUT
    return St.LOW_LAMP if key[1] == 1 else SHUT


def windows_at(t):
    """{key: rgb} for every window on the elevation: the letters' paper until each snaps to its
    night colour (the tenement's lit, the bank's dark, the hall's low lamp); the windows that
    were not letters come out of the dark at the same snaps."""
    out = {}
    for i, (key, r) in enumerate(St.elevation_windows()):
        ts = T_NIGHT + 0.05 + 0.06 * ((i * 5) % 8)
        out[key] = night_colour(key) if t >= ts else (PAPER if key in LETTER_KEYS else INK)
    return out


def lit_rooms(t):
    """{("ten", n): AMBER} for the neighbours still up at t (the crew's room is always lit)."""
    lit = {("ten", n): AMBER for n in (2, 3, 5)}
    for n, t0 in zip(OUT_ORDER, T_OUT):
        if t >= t0:
            del lit[("ten", n)]
    return lit


def city_lit(t):
    on = 0.5 * k(t, T_CITY, 1.0)
    steps = sum(1 for t0 in T_OUT + (T_CITY_OUT,) if t >= t0)
    return on * (1.0 - steps / 4.0)


def draw_faces(c, t, windows):
    lit_ten = {key: v for key, v in windows.items() if key[0] == "ten"}
    lit_bank = {key: v for key, v in windows.items() if key[0] == "bank"}
    St.ten_face(c, t, lit_ten)
    St.bank_face(c, t, lit_bank, low=1.0, clock=CLOCK_BANK)


def draw_night(c, t):
    K.fill(c, PAPER)
    u = k(t, T_NIGHT, 0.6, "linear")
    if u > 0.0:
        bass.bars(c, u, n=7, axis="h", colors=(NIGHT,), frm="alt", mode="slide", overlap=0.55, seed=11, bleed=3.0)
    rise = k(t, T_CITY, 0.5, "out3")
    if rise > 0.0:
        c.save()
        c.translate(0.0, 1150.0 * (1.0 - rise))
        K.skyline(c, lit=city_lit(t))
        c.restore()
    drop = k(t, T_MOON, 0.45, "outback")
    if drop > 0.0:
        K.moon(c, (St.MOON_E[0], lerp(-110.0, St.MOON_E[1], drop)))
    draw_faces(c, t, windows_at(t))
    St.street_ground(c, t, under=0.0)
    St.car_rear(c, St.CAR_C, t, **CAR)


# ---------------------------------------------------------------- 6.5-9: the cutaway
def bands(t):
    """[(x0, y0, x1, y1, t_open)] the strips of the street the cut opens (each wipes up from its
    floor), the tenement's storeys and the bank's, the vault last."""
    b = St.TEN
    out = []
    for n in range(1, b.floors + 1):
        y0 = St.level(n + 1) if n < b.floors else b.roof - 240.0
        y1 = St.level(n) if n > 1 else St.GROUND + 12.0
        out.append((b.x0 - 12.0, y0, b.x1 + 12.0, y1, T_STOREY[n - 1]))
    x0, x1 = St.BANK[0] - 40.0, St.BANK[1] + 20.0
    out.append((x0, St.bank_level(2), St.VAULT[0], St.GROUND + 40.0, T_STOREY[0]))          # the hall
    out.append((x0, St.bank_level(3), x1, St.bank_level(2), T_STOREY[1]))
    out.append((x0, St.PED_APEX[1] - 24.0, x1, St.bank_level(3), T_STOREY[2]))
    out.append((St.VAULT[0] - 2.0, St.bank_level(2), x1, St.GROUND + 40.0, T_VAULT))          # the vault
    return out


def reveal_clip(c, t):
    c.new_path()
    for x0, y0, x1, y1, t0 in bands(t):
        u = k(t, t0, 0.12, "out3")
        if u <= 0.0:
            continue
        h = (y1 - y0) * u
        c.rectangle(x0, y1 - h, x1 - x0, h)
    c.clip()


def under_at(t):
    return k(t, T_UNDER[0], T_UNDER[1], "linear")


def beams_at(t):
    """The lit tenement storeys whose rooms the cut has opened throw their light over the street."""
    return {n for n in (2, 3, 4, 5) if (n == St.CREW_FLOOR or ("ten", n) in lit_rooms(t)) and t >= T_STOREY[n - 1] + 0.06}


def grown_lamp(c, t):
    """The street lamp grows out of the pavement (T_LAMP) and lights."""
    up = k(t, T_LAMP, 0.3, "outback")
    if up <= 0.0:
        return
    c.save()
    c.translate(St.LAMP_X, St.GROUND)
    c.scale(1.0, up)
    c.translate(-St.LAMP_X, -St.GROUND)
    St.lamp(c, on=1.0 if t >= T_LAMP + 0.3 else 0.0)
    c.restore()


def moon_at(t):
    m = k(t, T_CUT, 0.5, "inout3")
    return (lerp(St.MOON_E[0], St.MOON_S[0], m), lerp(St.MOON_E[1], St.MOON_S[1], m))


def gold_glow(t):
    return k(t, T_VAULT, 0.5, "out3")


# ---------------------------------------------------------------- the lives in the rooms
def old_man(c, t, rect):
    """Storey 2, lit: the old man in his armchair, nodding along to his radio (ripples on the beat)."""
    x0, _, _, fy = rect
    f = FO.small("bald")
    tt = K.twos(t)
    p = pd.Pose(lean=-7.0, head=-2.0 + 5.0 * abs(math.sin(math.pi * 2.0 * tt)),
                arms={"near": ("ang", 16.0, 74.0), "far": ("ang", 10.0, 70.0)})
    seat_x = x0 + St.TEN_SETS[2][-1][1]
    FO.draw(c, f, FO.seated(f, 0.0, -1, 36.0), p, seat_x + 6.0, fy, -1, AMBER)
    beat = math.floor(t / 0.5) * 0.5
    K.ripple(c, (x0 + St.TEN_SETS[2][0][1], fy - 62.0), t, beat, PAPER, n=2, every=0.12, life=0.45, r0=4.0, r1=22.0,
             width=2.6, seed=2)


def guard_at_desk(c, t):
    """The guard at his desk under his lamp, reading, his back to the hatch's corner."""
    x = St.DESK_X - 50.0
    bass.fill_polys(c, St._furn("chair_l", x, St.FEET, 0.9), INK)
    hand = ((St.DESK_X - 20.0 - x) / St.FIG_S, (St.FEET - 46.0 - St.FEET) / St.FIG_S)
    tt = K.twos(t)
    pose = pd.Pose(lean=12.0, head=-18.0 + 2.0 * math.sin(2.0 * math.pi * 0.2 * tt),
                   arms={"near": ("ik", hand), "far": ("ik", (hand[0] - 30.0, hand[1] + 6.0))})
    St.fig(c, "guard", R.seated("guard"), pose, x, St.FEET, 1, None)
    bass.fill_polys(c, [St._r(St.DESK_X - 26.0, St.FEET - 47.6, St.DESK_X - 2.0, St.FEET - 45.6, 1110, 0.1)],
                    lerp(PAPER, AMBER, 0.25))                 # his newspaper on the desk


def lives(t):
    lit = lit_rooms(t)

    def fn(c, where, n, rect):
        if where == "hall":
            guard_at_desk(c, t)
            C.cat(c, St.CAT_SEAT, s=0.24, t=t, facing=-1, mode="sit", eyes=1.0)
        elif where == "ten":
            up = ("ten", n) in lit
            if n == 2 and up:
                old_man(c, t, rect)
            else:
                St.neighbour(c, n, t, "up" if up else "asleep")
    return fn


def crew(t):
    return lambda c, rect: R.crew_rest(c, t, rect)


def draw_numbers(c, t):
    """The floor numbers pop in beside the stairs as each storey opens; the crew's 4 turns paper.
    They shrink away as the push begins (s02 has none)."""
    gone = 1.0 - k(t, T_PUSH[0], 0.25, "in3")
    if gone <= 0.0:
        return
    for n in range(1, St.TEN.floors + 1):
        g = ease("outback", clamp((t - T_STOREY[n - 1] - 0.05) / 0.2))
        if g <= 0.01:
            continue
        col = NUM_DIM
        if n == St.CREW_FLOOR and t >= T_FOUR:
            col = PAPER
            g *= 1.0 + 0.6 * (1.0 - ease("out3", clamp((t - T_FOUR) / 0.3)))
        K.numeral(c, str(n), ((St.TEN.stair[0] + St.TEN.stair[1]) / 2.0, St.level(n + 1) + 46.0), 36.0, col,
                  seed=40 + n, scale=g * gone)


def shimmer(c, t):
    """Two glints on the gold as the vault opens."""
    for i, (t0, dx) in enumerate(((T_VAULT + 0.25, -10.0), (T_VAULT + 0.75, 14.0))):
        u = k(t, t0, 0.12, "out3") * (1.0 - k(t, t0 + 0.18, 0.2, "in3"))
        if u > 0.0:
            K.twinkle(c, (St.GOLD_STACKS[1] + dx, St.FEET - 18.0), 11.0, PAPER, u=u, rot=12.0 * i)


def section(c, t, cam, clip=False):
    """The street in section through cam (R.draw_stage): everyone in their rooms."""
    lit = lit_rooms(t)

    def overlay(cc):
        draw_numbers(cc, t)
        shimmer(cc, t)

    R.draw_stage(c, t, cam=cam, crew=crew(t), others=lives(t), lit_extra=lit, sky_lit=city_lit(t), moon_at=moon_at(t),
                 under=under_at(t), gold_glow=gold_glow(t), beams=False if clip else beams_at(t), car=CAR,
                 lamp_on=1.0, overlay=overlay)


def draw_cutaway(c, t):
    """The elevation with the section showing through wherever the cut has opened it."""
    K.fill(c, NIGHT)
    K.skyline(c, lit=city_lit(t))
    K.moon(c, moon_at(t))
    draw_faces(c, t, windows_at(t))
    St.street_ground(c, t, under=under_at(t))
    c.save()
    c.rectangle(St.STREET[0], 0.0, St.STREET[1] - St.STREET[0], St.GROUND)
    c.clip()
    for n in sorted(beams_at(t)):
        St.beam(c, n, AMBER)
    c.restore()
    grown_lamp(c, t)
    St.car_rear(c, St.CAR_C, t, **CAR)
    if t >= T_STOREY[0]:
        c.save()
        reveal_clip(c, t)
        section(c, t, (C0, 1.0), clip=True)
        c.restore()
    draw_numbers(c, t)


# ---------------------------------------------------------------- the scene
def push(t):
    """(centre, zoom) of the push in on the crew's room: from the whole street to R.S01_END,
    exactly where s02 begins."""
    return R.cam_lerp((C0, 1.0), R.S01_END, k(t, T_PUSH[0], T_PUSH[1], "inout3"))


def render(f, t, T):
    K.scene_setup(f, INK if t < T_NIGHT else NIGHT)
    with f.screen() as c:
        if t < T_TITLE:
            draw_dot(c, t)
        elif t < T_NIGHT:
            draw_title_shot(c, t)
        elif t < T_CUT:
            draw_night(c, t)
        elif t < T_SECTION:
            draw_cutaway(c, t)
        else:
            section(c, t, push(t))


def cues(T):
    out = [Cue(t0, "the red dot ticks: a dry clock tick", gain_db=-8) for t0 in T_DOT]
    out += [Cue(T_TITLE + 0.13, "the title's strips race across the black: a run of fast string stabs", gain_db=-10,
                dur=1.4),
            Cue(T_WORDS[0][0], "DOUBLE assembles from cut strips: a paper rustle snapping together", gain_db=-12),
            Cue(T_WORDS[1][0], "CROSS assembles: a paper rustle snapping together, lower", gain_db=-12),
            Cue(T_STRIPS[0] - STRIP_IN, "the paper strip slashes across: whoosh-thud", gain_db=-6, pan=-0.2),
            Cue(T_STRIPS[1] - STRIP_IN, "the red strip crosses it: whoosh-thud, lower and harder", gain_db=-5, pan=0.2),
            Cue(T_PART, "the X lifts off and the halves part: a paper tear and a swish", gain_db=-9),
            Cue(T_FLOOD, "paper floods in round the buildings: a soft rush", gain_db=-14),
            Cue(T_MORPH, "the letters become windows: small paper snaps, one per letter", gain_db=-14, dur=0.9),
            Cue(T_NIGHT, "night falls: a low gong under the teal bars", gain_db=-8),
            Cue(T_CITY, "the city rises: a pizzicato descent", gain_db=-10),
            Cue(T_MOON, "the moon drops: a soft bell", gain_db=-12)]
    out += [Cue(t0, f"the cutaway: a click as storey {i + 1} opens (rising)", gain_db=-12) for i, t0 in enumerate(T_STOREY)]
    out += [Cue(T_LAMP + 0.3, "the street lamp comes on: a tick and a low hum", gain_db=-18),
            Cue(T_STOREY[1], "the radio through the wall: a faint dance band, till its light goes", gain_db=-24,
                dur=T_OUT[1] - T_STOREY[1]),
            Cue(T_UNDER[0], "the road opens down: stone sliding, a hollow drip far below", gain_db=-12),
            Cue(T_VAULT, "the vault and its gold: a deep cello note and a soft string shimmer", gain_db=-8, dur=1.5)]
    out += [Cue(t0, f"light out (storey {n}): a plucked note, descending", gain_db=-10) for n, t0 in zip(OUT_ORDER, T_OUT)]
    out += [Cue(T_CITY_OUT, "the far city goes dark: a last low pluck", gain_db=-12),
            Cue(T_FOUR, "the crew's 4 turns paper: one high pizzicato note", gain_db=-10),
            Cue(T_PUSH[0], "a rising tremolo into the crew's room, to the cut", gain_db=-8, dur=T_PUSH[1])]
    return out
