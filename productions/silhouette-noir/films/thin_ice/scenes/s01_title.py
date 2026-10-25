"""s01 TITLE (0-14): snow; THIN ICE; the crack; the red thread; the crack becomes the river; the
map; the snow stops; push in on two figures at the fence.

  0.0-0.5   The NIGHT field; snow drifting down in three depths.
  0.5-2.25  THIN / ICE: hand-cut PAPER letters drop in, one per half beat (landing 0.75 .. 2.25),
            each with a paper bounce.
  2.5-4.0   Hold; snow falls through the title.
  4.0       THE CRACK: a jagged INK crack shoots across the whole title, upper left to lower right,
            in a quarter second, with side cracks. Shake.
  4.25-5.0  The two halves drift apart like floes; black water opens between them.
  5.0       A thin RED thread snaps taut across the gap and holds them (it had lain slack in it).
  5.5-6.5   The page floods out of the letters (the map, under cloud); the gap swings up and
            settles as the river's black band, the thread across it where the false trail will
            run; the white ice opens round it (6.0-6.5).
  6.5-8.0   The map pops in on the beats: the farmhouse and its window (6.5), the woods (6.75-
            7.5: crowns pop in, then snap together into one cut-paper canopy with the path pale
            through it), the fence (drawn as the map draws a border), the tower and its searchlight
            (7.0), the guardhouse (7.5); the thread fades (7.5-8.0) as two tiny figures appear at
            the fence, a red fleck at one's neck (8.0): the thread was the scarf.
  8.0-10.0  Hold on the map; the searchlight sweeps the far end of the zone, by the tower; snow
            falls on the page.
  10.0-11.0 The snow stops (the last flakes land; the wind drops). The moon stays behind the cloud
            until s02.
  11.0-14.0 Push in (eased, about 2.3 times) to everything they face in one frame, s02's layout seen
            from above: the woods and the path's mouth, the tower (its beam swung away west), the
            guardhouse window, the wire, the two of them with the red fleck, and their trail
            behind them. Cut.
"""
import math
from functools import lru_cache

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.thin_ice import cast as C
from films.thin_ice import kit as K
from films.thin_ice import world as W
from films.thin_ice.scenes import _lib_dir as L

FILM_T0 = 0.0
T_LAND = tuple(0.75 + 0.25 * i for i in range(7))     # each letter lands (T H I N I C E)
DROP = 0.5                                              # each letter's drop, landing at 0.7 of it
T_CRACK = 4.0
CRACK_DUR = 0.25
T_DRIFT = (4.25, 5.0)
T_THREAD = 5.0
T_FLOOD = (5.5, 6.3)
T_MORPH = (5.5, 6.5)
T_RIVER = (6.0, 6.5)
T_FARM = 6.5
T_WOODS = (6.75, 7.5)
T_FENCE = 7.0
T_HUT = 7.5
T_THREAD_OUT = (7.5, 8.0)
T_FIGS = 8.0
T_SNOW_STOP = (9.7, 10.0)
T_PUSH = (11.0, 14.0)

OPEN = 30.0            # px each floe drifts off the crack
TURN = 1.4             # degrees each turns
MAP = W.Plan(10.0, -48.0, 9.6)
# everything they face in one frame (s02's layout from above): the woods and the path's mouth, the
# tower left, the guardhouse right, the wire, the two of them, their trail behind them
END = W.Plan(43.0, -117.3, 22.0)
WOODS_KEEP = 1.0
CROWN = 1.0
# the way they came to the fence, half filled by the snow (older further back)
APPROACH = tuple(W.walk_prints([(31.0, -160.0), (33.4, -151.0), (36.4, -143.0), (39.0, -137.0), (40.0, -133.3)],
                               "mother", 0.6, 0.3, seed=31) +
                 W.walk_prints([(31.6, -160.0), (34.0, -151.0), (37.0, -143.0), (39.6, -137.0), (40.6, -133.2)],
                               "girl", 0.42, 0.3, seed=32))
# the two of them crouched behind the drift at the crossing, facing the fence (north)
MOTHER_AT = (40.0, -132.75)
GIRL_AT = (40.62, -132.6)


def _shake(t):
    u = (t - T_CRACK) / 0.35
    if u < 0.0 or u > 1.0:
        return (0.0, 0.0)
    a = 14.0 * (1.0 - u) ** 2
    return (a * math.sin(t * 91.0), a * 0.6 * math.cos(t * 77.0))


def _opening(t):
    """px each floe has drifted: out until the thread snaps taut at 5.0, a small recoil after."""
    if t < T_DRIFT[0]:
        return 0.0
    if t < T_THREAD:
        return OPEN * ease("out3", (t - T_DRIFT[0]) / (T_THREAD - T_DRIFT[0])) * 1.04
    k = t - T_THREAD
    return OPEN * (1.0 + 0.04 * math.exp(-6.0 * k) * math.cos(k * 26.0))


def _letter(t):
    """Per-letter transform while they drop in."""
    def fn(i):
        t0 = T_LAND[i] - 0.7 * DROP
        p = (t - t0) / DROP
        if p <= 0.0:
            return None
        p = clamp(p)
        q = 1.0 - bass._drop_ease(p)
        return (0.0, -1100.0 * q, 12.0 * K._sn(i, 31) * min(1.0, q * 3.0), 1.0)
    return fn


# ---------------------------------------------------------------------------- the crack and the band
@lru_cache(maxsize=None)
def _band_lines():
    """The river's band in the map camera, as two lines (upper = north edge, lower = south) of the
    crack's sample count, x mapped linearly from the crack's x."""
    pts = L.crack_line()
    xa = MAP.px((W.BAND_X0, 0.0))[0]
    up, lo = [], []
    for p in pts:
        X = lerp(xa, 1110.0, (p[0] + 30.0) / 1140.0)
        x = MAP.m((X, 0.0))[0]
        mid = 0.5 * (W.band_lo(x) + W.band_hi(x))
        half = 0.5 * (W.band_hi(x) - W.band_lo(x)) * W.band_taper(x)
        up.append(MAP.px((x, mid + half)))
        lo.append(MAP.px((x, mid - half)))
    return tuple(up), tuple(lo)


def _gap_lines(off):
    """The gap between the floes: the upper floe's edge and the lower floe's edge (frame px)."""
    pts = L.crack_line()
    up = [L.xf(p, off, -TURN * clamp(off / OPEN), +1) for p in pts]
    lo = [L.xf(p, off, TURN * clamp(off / OPEN), -1) for p in pts]
    return up, lo


def _gap(t):
    """The gap / band's two edges at time t (the morph from the crack to the river's band)."""
    up0, lo0 = _gap_lines(_opening(t))
    u = ease("inout", clamp((t - T_MORPH[0]) / (T_MORPH[1] - T_MORPH[0])))
    if u <= 0.0:
        return up0, lo0, 0.0
    up1, lo1 = _band_lines()
    up = [(lerp(a[0], b[0], u), lerp(a[1], b[1], u)) for a, b in zip(up0, up1)]
    lo = [(lerp(a[0], b[0], u), lerp(a[1], b[1], u)) for a, b in zip(lo0, lo1)]
    return up, lo, u


# where the thread is tied: the crack's sample nearest the frame x that maps onto the trail
@lru_cache(maxsize=None)
def _thread_i():
    up1, lo1 = _band_lines()
    X = MAP.px((W.TRAIL_X, 0.0))[0]
    return min(range(len(up1)), key=lambda i: abs(up1[i][0] - X))


def _draw_thread(c, t, up, lo, alpha=1.0, width=5.0):
    i = _thread_i()
    a, b = lo[i], up[i]
    if t < T_THREAD:
        # slack in the gap: a loose wave that straightens as the gap opens
        k = clamp((t - 4.45) / (T_THREAD - 4.45))
        if k <= 0.0:
            return
        amp = 9.0 * (1.0 - k)
    else:
        k = t - T_THREAD
        amp = 3.5 * math.exp(-9.0 * k) * math.sin(k * 60.0)        # the snap: a quick hum
    dx, dy = b[0] - a[0], b[1] - a[1]
    Ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / Ln, dx / Ln
    pts = []
    for j in range(13):
        u = j / 12.0
        w = amp * math.sin(math.pi * u) * math.sin(u * math.pi * 3.0 + t * 9.0)
        pts.append((a[0] + dx * u + nx * w, a[1] + dy * u + ny * w))
    K.band(c, pts, K.RED, width, seed=5, alpha=alpha)
    # its knots: a tiny RED dot at each floe's edge
    for p in (a, b):
        K.dot(c, p, width * 0.9, K.RED, alpha=alpha)


def _gap_edges(c, up, lo, a):
    """The floes' broken edges: white, like the crack, along both sides of the black water."""
    if a > 0.0:
        K.band(c, up, K.PAPER, 3.0, seed=13, alpha=a)
        K.band(c, lo, K.PAPER, 3.0, seed=14, alpha=a)


def _draw_crack(c, t):
    """The crack shooting across (4.0-4.25), with side cracks: white in the dark ice, black where it
    runs through the paper letters."""
    p = clamp((t - T_CRACK) / CRACK_DUR)
    pts = L.crack_line()
    n = len(pts) - 1
    m = p * n
    k = int(m)
    line = list(pts[:k + 1])
    if k < n:
        f = m - k
        line.append((lerp(pts[k][0], pts[k + 1][0], f), lerp(pts[k][1], pts[k + 1][1], f)))
    segs = []
    for i, br in L.crack_branches():
        if m > i:
            q = clamp((m - i) / 3.0)
            seg = list(br[:1 + int(q * (len(br) - 1))])
            if len(seg) > 1:
                segs.append((i, seg))
    for color, clip in ((K.PAPER, False), (K.INK, True)):
        c.save()
        if clip:
            L.title_path(c)
            c.clip()
        if len(line) > 1:
            K.band(c, line, color, 7.0, seed=3)
        for i, seg in segs:
            K.band(c, seg, color, 4.0, seed=i, taper=(1.0, 0.2))
        c.restore()


# ---------------------------------------------------------------------------- the map
def _cam(t):
    u = ease("inout", clamp((t - T_PUSH[0]) / (T_PUSH[1] - T_PUSH[0])))
    return W.plan_lerp(MAP, END, u)


def _grow(t):
    pop = lambda t0, d=0.3: clamp((t - t0) / d)
    return {"river": ease("out3", clamp((t - T_RIVER[0]) / (T_RIVER[1] - T_RIVER[0]))),
            "band": 1.0 if t >= T_MORPH[1] else 0.0,
            "farm": pop(T_FARM), "woods": clamp((t - T_WOODS[0]) / (T_WOODS[1] - T_WOODS[0])),
            "fence": ease("out3", pop(T_FENCE, 0.45)), "tower": pop(T_FENCE), "guardhouse": pop(T_HUT)}


def _draw_map(c, t, cam):
    g = _grow(t)
    # far off, the woods are one canopy with the path through it
    mass = clamp((t - (T_WOODS[1] - 0.05)) / 0.12)          # the crowns snap together into one shape
    W.draw_page(c, cam, t, moonlit=0.0, grow=g, shadows=0.0, farm_light=g["farm"], guardhouse_light=g["guardhouse"],
                reeds_on=g["river"] >= 1.0, trunk_on=g["river"] >= 1.0, scrap=False, woods_keep=WOODS_KEEP,
                crown_scale=CROWN, woods_mass_a=mass)
    _draw_border(c, cam, g["fence"], 1.0 - clamp((cam.ppm - 18.0) / 16.0))
    if cam.ppm > 16.0:
        for n0, n1, cov in ((-138.0, -132.0, 0.08), (-144.0, -138.0, 0.2), (-152.0, -144.0, 0.35), (-170.0, -152.0, 0.5)):
            W.draw_prints(c, cam, [q for q in APPROACH if n0 <= q[1] < n1], cover=cov, page=K.SNOW_DIM,
                          color=lerp(K.SHADOW_DIM, K.NIGHT, 0.3))
    # the searchlight's patch (from 7.0)
    sa = clamp((t - T_FENCE) / 0.4)
    if sa > 0.0:
        ft = FILM_T0 + t
        sp = (L.search_x(ft), L.search_n(ft))
        # the beam from the tower top (the map's shorthand: a pale wedge to the patch)
        d = (sp[0] - W.TOWER[0], sp[1] - W.TOWER[1])
        dl = math.hypot(*d) or 1.0
        side = (-d[1] / dl * 3.6, d[0] / dl * 3.6)
        K.beam(c, cam.px(W.TOWER), cam.px((sp[0] + side[0], sp[1] + side[1])),
               cam.px((sp[0] - side[0], sp[1] - side[1])), K.PAPER, alpha=0.16 * sa)
        W.search_patch(c, cam, sp, 4.2, alpha=0.8 * sa, heading=L.search_heading(ft))
    # the two of them, crouched behind the drift (from 8.0)
    fa = clamp((t - T_FIGS) / 0.25)
    if fa > 0.0:
        # the map draws them a little larger than life, like pins
        s = ease("outback", fa) * (1.0 + 0.6 * clamp((30.0 - cam.ppm) / 20.0))
        C.top(c, "mother", cam.px(MOTHER_AT), -90.0, cam.ppm * s, t, speed=0.0, crouch=0.8, shadow=False)
        C.top(c, "girl", cam.px(GIRL_AT), -90.0, cam.ppm * s, t, speed=0.0, crouch=0.8, shadow=False)
        # at the map's scale the scarf is a fleck: keep it visible
        K.dot(c, cam.px(GIRL_AT), max(4.5, 0.12 * cam.ppm) * ease("outback", fa), K.RED)


def _draw_border(c, cam, grow, a):
    """The fence as the map draws it: a bold line with a tick at every post (it grows out from
    the crossing like the fence itself)."""
    if grow <= 0.0 or a <= 0.0:
        return
    xa, xb = lerp(W.CROSS[0], W.FENCE_X[0], grow), lerp(W.CROSS[0], W.FENCE_X[1], grow)
    K.band(c, [cam.px((xa, W.FENCE_N)), cam.px((xb, W.FENCE_N))], K.INK, 4.5, seed=3, alpha=a)
    x = math.ceil(xa / 3.0) * 3.0
    while x <= xb:
        p = cam.px((x, W.FENCE_N))
        K.band(c, [(p[0], p[1] - 7.0), (p[0], p[1] + 7.0)], K.INK, 3.0, seed=int(x), alpha=a)
        x += 3.0


# ---------------------------------------------------------------------------- render
def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        sx, sy = _shake(t)
        c.translate(sx, sy)
        off = _opening(t)
        rot = TURN * clamp(off / OPEN)
        if t < T_FLOOD[0]:
            K.fill(c, K.NIGHT)
            if t >= T_DRIFT[0]:
                up, lo, _ = _gap(t)
                K.poly(c, up + lo[::-1], K.WATER)
                _gap_edges(c, up, lo, clamp((t - T_DRIFT[0]) / 0.15))
            L.draw_title_floes(c, K.PAPER, off, rot, letters=_letter(t) if t < T_LAND[-1] + 0.3 else None)
            if T_CRACK <= t < T_DRIFT[0] + 0.05:
                _draw_crack(c, t)
            if t >= 4.45:
                up, lo, _ = _gap(t)
                _draw_thread(c, t, up, lo)
            K.snow(c, FILM_T0 + t, n=170)
            return
        # ---- the page floods out of the letters; the gap becomes the band
        cam = _cam(t)
        flood = ease("in3", clamp((t - T_FLOOD[0]) / (T_FLOOD[1] - T_FLOOD[0])))
        if flood < 1.0:
            K.fill(c, K.NIGHT)
            c.push_group()
            _draw_map(c, t, cam)
            page = c.pop_group()
            L.title_path(c, off, rot)
            c.set_source(page)
            c.fill_preserve()
            c.set_line_width(2.0 + 2400.0 * flood)
            c.set_line_join(1)
            c.stroke()
            c.new_path()
        else:
            _draw_map(c, t, cam)
        up, lo, u = _gap(t)
        band_c = lerp(K.WATER, lerp(K.THIN, K.NIGHT, 0.2), u)
        if t < T_MORPH[1]:
            K.poly(c, up + lo[::-1], band_c)        # from here on the page draws the band
            _gap_edges(c, up, lo, 1.0 - u)
        ta = 1.0 - clamp((t - T_THREAD_OUT[0]) / (T_THREAD_OUT[1] - T_THREAD_OUT[0]))
        if ta > 0.0:
            _draw_thread(c, t, up, lo, alpha=ta, width=lerp(5.0, 3.0, u))
        la = 1.0 - clamp((t - 5.75) / 0.5)
        if la > 0.0:
            L.draw_title_floes(c, K.PAPER, off, rot, alpha=la)
        # snow: falling past the camera until the page is down, then on the page; it stops at 10
        if t < 6.5:
            K.snow(c, FILM_T0 + t, n=170, alpha=1.0 - clamp((t - 5.6) / 0.9))
        dens = K.snowfall(T_SNOW_STOP[0], T_SNOW_STOP[1])
        K.snow_top(c, FILM_T0 + t, density=dens, alpha=clamp((t - 5.6) / 0.9))


def motion_blur(t, T):
    return 1


def cues(T):
    out = [Cue(0.0, "wind_low", gain_db=-24, dur=T_SNOW_STOP[1] + 0.8, dc="a low winter wind, snow hiss (it drops at 10.0)")]
    for i, tl in enumerate(T_LAND):
        out.append(Cue(tl, "glass_tink", gain_db=-16, pan=round((i % 4 - 1.5) * 0.25, 2), note=i,
                       dc="a crisp glassy tink: a paper letter lands (a rising run of seven)"))
    out.append(Cue(2.5, "ice_groan", gain_db=-14, dur=1.5, dc="a deep ice groan under the title"))
    out.append(Cue(T_CRACK, "ice_crack", gain_db=-4, dc="THE CRACK: a sharp split, then a dispersive 'pew' (lake ice)"))
    out.append(Cue(T_CRACK + 0.05, "ice_pew", gain_db=-10, dur=0.4, dc="dispersive ice chirp, high to low"))
    out.append(Cue(T_DRIFT[0], "floe_grind", gain_db=-20, dur=0.75, dc="two floes grinding apart; water lapping"))
    out.append(Cue(T_THREAD, "thread_ping", gain_db=-12, dur=2.5, dc="a single high harmonic, held: the red thread snaps taut"))
    out.append(Cue(T_FLOOD[0], "paper_flood", gain_db=-20, dur=0.8, dc="a soft paper whoosh: the page spreads"))
    for k, (tt, what) in enumerate(((T_FARM, "the farmhouse"), (T_WOODS[0], "the woods"), (T_FENCE, "the fence and tower"),
                                    (T_HUT, "the guardhouse"), (T_FIGS, "the two figures"))):
        out.append(Cue(tt, "pluck", gain_db=-15, note=k, dc=f"a plucked string note, rising: {what} pops onto the map"))
    out.append(Cue(T_FENCE, "searchlight_hum", gain_db=-30, dur=14.0 - T_FENCE,
                   dc="the searchlight's motor, far: a low hum"))
    out.append(Cue(T_SNOW_STOP[1], "hush", gain_db=-22, dur=4.0,
                   dc="the snow stops: the wind falls away to a still, cold quiet (a faint high air tone)"))
    out.append(Cue(T_PUSH[0], "push_swell", gain_db=-22, dur=3.0, dc="a slow low string swell under the push in"))
    return out
