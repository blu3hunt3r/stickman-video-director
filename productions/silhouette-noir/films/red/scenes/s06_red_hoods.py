"""s06 · RED HOODS: the valley view (14.5 s).

IN  (hard cut from s05): VALLEY_VIEW.camera("start") = Camera(540, 1480, 1.25), DUSK. She
    stands on the crest at x = 540 (feet on crest_y + 8: screen ~(540, 1376)), back to camera,
    hood up (look_up), the basket hanging from her right hand; light snow (density 0.5).
Beats (scene-local s; L9 0.60-3.12, L10 4.00-6.69, L11 7.60-10.69):
    0.00-0.55       her POV over her shoulder: the valley in fog, the path's stakes winding
                    down to the clearing; she breathes
    0.55-4.55       the camera leaves her and travels down the path (push + tilt, weaving
                    with its bends; the near stakes and trees slide away with parallax)
    [house@4.46]    the cottage wrapped in web: the strands catch the light, dead still
    7.25-8.45       easing back out to the trees around it; [hoods@8.33] RED hoods appear,
                    spreading out from the cottage: many, swaying
    [winter@10.00]  pull back to the whole valley, every hood; she is small at the bottom
    10.72-11.28     Bass flatten: the view posterizes (3 inks, 2 inks) and paper bars wipe
                    the ink away; only the red is left: specks of hoods, her own triangle
    11.18-12.75     the specks rise into a row of 14 red triangles at the top; the row is
                    copied down, row after row, faster and faster: counting winters
    ~12.8           the last slot is hers: her triangle flies up into it (the next winter)
    ~13.1           the grid pulses once (a wave out from her slot)
    13.3-14.15      the triangles drift and snap onto s07's hoods (s07_hood_targets) while
                    s07's forest assembles round them as cut-paper ink bars
OUT (flatten, 1.0 s, 14.0-15.0): from 14.1 the frame is exactly s07's opening (t = 0)
    flattened to 2 inks: ink forest on PAPER, a red triangle on each of s07's 39 red hoods
    (centre / height from s07_hood_targets) and hers on the girl (670.5, 1312.2, h 113.9).
"""
import math
from functools import lru_cache

import cairo
import numpy as np

from engine import bass, draw
from engine.core import clamp, ease, lerp, hash01, noise1
from engine.frame import Camera, Frame
from engine.motion import Actor
from engine.palette import PAPER, RED
from engine.timing import Cue
from films.red import cast
from films.red import sets as S
from films.red.scenes import _lib_s02_s06 as L26

V = S.VALLEY_VIEW
INK = S.INK

# ----------------------------------------------------------------------------- timing
POSTER3 = 10.72                 # the live view flattens: 3 inks ...
POSTER2 = 10.86                 # ... 2 inks
BARS = (10.96, 0.32)            # paper bars wipe the ink away (alternate sides)
RISE = (11.27, 0.44)            # the specks rise into the top row (staggered over 0.16 s)
LEDGER = 11.73                  # the first copied row starts down
ROW_DUR = 0.14                  # each row's slide
WAVE = 4200.0                   # px/s: the pulse (and the release) spreading from her slot
DRIFT = 0.60                    # each triangle's drift into s07's hoods
INK_BARS = (13.46, 0.62)        # s07's forest assembles (cut-paper bars)
WIDE_T = 10.80                  # the camera lands on "wide"

COLS = 14
PITCH = 64.0
TRI_H = 48.0
TRI_R = 0.78                    # base / height of the grid triangles
HOOD_R = 0.58                   # ... of a hanging hood (they become hoods in s07)
GRID_Y0 = 330.0


def _k(t, t0, dur, e="inout"):
    if t <= t0:
        return 0.0
    if dur <= 0 or t >= t0 + dur:
        return 1.0
    return ease(e, (t - t0) / dur)


def _words(T):
    return dict(path=T.at("path"), house=T.at("house"), no=T.at("no"), red=T.at("red"),
                hoods=T.at("hoods"), winter=T.at("winter"))


# ----------------------------------------------------------------------------- mood, camera
def _mood(t):
    """DUSK (s05's end) darkening toward s07's clearing (mood_mix(DUSK, NIGHT, 0.55))."""
    return S.mood_mix(S.DUSK, S.NIGHT, 0.42 * ease("inout", clamp(t / 10.8)))


@lru_cache(maxsize=4)
def _campath(house):
    st, ho, hd, wd = V.camera("start"), V.camera("house"), V.camera("hoods"), V.camera("wide")
    keys = [(-1.0, st.x, st.y, st.zoom), (0.55, st.x, st.y - 2.0, st.zoom * 1.004),
            (2.25, 596.0, 1392.0, 1.72),                      # the far bend of the path
            (3.50, 588.0, 1188.0, 2.60),
            (house + 0.09, ho.x, ho.y, ho.zoom),              # the cottage: dead still
            (7.25, ho.x + 2.0, ho.y - 1.5, ho.zoom * 1.035),
            (8.45, hd.x, hd.y, hd.zoom),                      # the hood trees
            (9.95, hd.x + 6.0, hd.y + 6.0, hd.zoom * 0.93),
            (WIDE_T, wd.x, wd.y, wd.zoom)]                    # every hood
    return L26.CamPath(keys)


def _camera(t, w):
    return _campath(round(w["house"], 3))(min(t, WIDE_T))


# ----------------------------------------------------------------------------- the girl
GX = 540.0


def _ground(x):
    return V.crest_y(x) + 8.0


@lru_cache(maxsize=None)
def _girl():
    a = Actor(L26.GIRL, L26.look_up(), x=GX, ground=_ground, facing=-90.0, seed=7, name="red")
    a.stand(at=-3.0, until=16.0, idle=1.0)
    # the basket hangs from her right hand, arm down at her side
    a.arm("R", -3.0, 16.0, fade=0.0, sh=6.0, abd=10.0, elbow=14.0, wrist=-4.0, grip=0.9)
    a.arm("L", -3.0, 16.0, fade=0.0, sh=-4.0, abd=7.0, elbow=10.0)
    # she looks down into the valley, then a small recoil when she sees how many
    a.key("head", [(-3.0, 0.0), (0.7, 0.0), (2.4, 9.0), (10.15, 9.0), (10.55, -4.0, "out3"), (11.2, 2.0)],
          mode="add")
    a.key("pitch", [(-3.0, 0.0), (10.1, 0.0), (10.4, -4.5, "out3"), (11.1, -2.0)], mode="add")
    return a


def _girl_red(t, cam):
    """(centre, height) on screen of her red silhouette (hood + cloak)."""
    gy = _ground(GX)
    c = (GX - 10.0, gy - 216.0)
    sx, sy = cam.to_screen(c)
    return (sx, sy), 253.0 * cam.zoom


def _draw_girl(f, t, mood):
    a = _girl()
    with f.layer() as Lc:
        a.draw(f, t, Lc)
        sk = a.skeleton(t)
        L26.draw_basket(Lc, L26.basket_hand(sk, "R"), 2.0 * math.sin(0.9 * t), mood.ink)


# ----------------------------------------------------------------------------- live view
def _hoods(t, w):
    return _k(t, w["hoods"] - 0.08, 1.15, "out")


def _web_light(t, w):
    return 0.6 + 0.85 * _k(t, w["house"] - 0.2, 0.7, "out3") - 0.35 * _k(t, w["no"], 1.2, "inout")


def _live(f, t, w):
    mood = _mood(t)
    f.set_camera(_camera(t, w))
    V.draw(f, mood, t, hoods=_hoods(t, w), web_light=_web_light(t, w))
    _draw_girl(f, t, mood)
    L26.snow(f, mood, density=0.5, t=t, seed=6)
    return mood


# ----------------------------------------------------------------------------- the Bass part
@lru_cache(maxsize=None)
def _specks():
    """The hoods on screen when the view flattens: [(x, y, size)] sorted by x."""
    f = Frame(t=POSTER3, scale=0.25, pal=S.PAL)
    f.set_camera(V.camera("wide"))
    pos = V.hood_screen_positions(f, POSTER3)
    vis = [(x, y, s) for x, y, s in pos if 4 < x < 1076 and 4 < y < 1916]
    return tuple(sorted(vis))


@lru_cache(maxsize=None)
def _layout():
    """Grid slots, the speck -> column assignment, the row timing, her slot."""
    sp = _specks()
    n = len(sp) + 1                                          # every hood, and hers
    rows = int(math.ceil(n / float(COLS)))
    x0 = 540.0 - PITCH * (COLS - 1) / 2.0
    slots = [(x0 + PITCH * c, GRID_Y0 + PITCH * r) for r in range(rows) for c in range(COLS)][:n]
    # specks -> columns (x quantiles), each column's specks converge on its top slot
    col_of = [min(COLS - 1, int(i * COLS / len(sp))) for i in range(len(sp))]
    # rows: row r (>= 1) is copied down from row r - 1, ever faster
    starts = [RISE[0]]
    t = LEDGER
    for r in range(1, rows):
        starts.append(t)
        t += max(0.04, 0.10 * 0.84 ** (r - 1))
    her_slot = n - 1
    t_her = starts[-1] + ROW_DUR + 0.04
    jit = [((1.5 * (hash01(i, 11) - 0.5), 1.5 * (hash01(i, 12) - 0.5)), 3.0 * (hash01(i, 13) - 0.5))
           for i in range(n)]
    return dict(slots=slots, rows=rows, col_of=col_of, starts=starts, her=her_slot, t_her=t_her,
                t_land=t_her + 0.28, t_pulse=t_her + 0.30, jit=jit)


@lru_cache(maxsize=None)
def _tri_shape(seed, ratio):
    """A cut-paper triangle, height 1, centred on its bbox centre (unit coords)."""
    pts = bass.triangle_pts((0.0, 0.5), 1.0, 0.0, seed, ratio)
    return tuple(pts)


def _tri(c, h, seed, ratio=TRI_R, rot=0.0, sx=1.0):
    """Polygon of a triangle centred on c (bbox centre), height h."""
    base = _tri_shape(seed % 61, round(ratio, 2))
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in base:
        x *= h * sx
        y *= h
        out.append((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca))
    return out


@lru_cache(maxsize=None)
def _targets():
    """s07's hood targets (the girl first) and the grid -> target assignment."""
    try:
        from films.red.scenes._lib_s04_s08 import s07_hood_targets
        tg = s07_hood_targets()
    except Exception:                                        # noqa: BLE001 - s07 retuning
        tg = []
    if not tg:
        tg = [dict(id="girl", x=670.5, y=1312.2, h=113.9)]
    L = _layout()
    girl, hoods = tg[0], tg[1:]
    slots = L["slots"]
    n = len(slots) - 1
    assign = [0] * n
    if hoods:
        cap = int(math.ceil(n / float(len(hoods))))
        load = [0] * len(hoods)
        pairs = sorted(((slots[i][0] - h["x"]) ** 2 + (slots[i][1] - h["y"]) ** 2, i, j)
                       for i in range(n) for j, h in enumerate(hoods))
        done = [False] * n
        for d, i, j in pairs:
            if done[i] or load[j] >= cap:
                continue
            done[i] = True
            load[j] += 1
            assign[i] = j
    return girl, hoods, assign


def _grid_state(t):
    """[(centre, height, ratio, rot)] of every red triangle at t (the last one is hers)."""
    L = _layout()
    sp = _specks()
    slots, starts = L["slots"], L["starts"]
    out = []
    # the specks (until they have all risen): each column's specks converge on its top slot
    if t < RISE[0] + RISE[1] + 0.02:
        for i, (x, y, s) in enumerate(sp):
            c = L["col_of"][i]
            st = RISE[0] + 0.16 * (hash01(i, 3) * 0.6 + 0.4 * c / (COLS - 1.0))
            u = _k(t, st, RISE[1] - 0.16, "inout3")
            us = _k(t, st, RISE[1] - 0.16, "in3")
            (jx, jy), jr = L["jit"][c]
            tx, ty = slots[c][0] + jx, slots[c][1] + jy
            h = lerp(max(s * 1.1, 7.0), TRI_H, us)
            arc = -60.0 * math.sin(math.pi * u) * (0.5 + hash01(i, 5))
            out.append(((lerp(x, tx, u) + arc * 0.15 * (hash01(i, 6) - 0.5), lerp(y, ty, u) + arc),
                        h, lerp(HOOD_R, TRI_R, us), lerp(8.0 * (hash01(i, 7) - 0.5), jr, u), c))
    tri = []
    n = len(slots) - 1
    for i in range(n):
        r, c = divmod(i, COLS)
        if r == 0:
            if t < RISE[0] + RISE[1] + 0.02:
                continue                                     # still specks
            pos = slots[i]
        else:
            t0 = starts[r]
            if t < t0:
                continue
            u = _k(t, t0, ROW_DUR, "out3")
            pos = (slots[i][0], lerp(slots[i - COLS][1], slots[i][1], u))
        tri.append((i, pos))
    out_tri = []
    for i, pos in tri:
        (jx, jy), jr = L["jit"][i]
        out_tri.append(((pos[0] + jx, pos[1] + jy), TRI_H, TRI_R, jr, i))
    return out, out_tri


def _her_state(t, cam_wide):
    """Her triangle: (centre, height, ratio) or None before the bars reach her."""
    L = _layout()
    c0, h0 = _girl_red(t, cam_wide)
    slot = L["slots"][L["her"]]
    u = _k(t, L["t_her"], L["t_land"] - L["t_her"], "inout3")
    us = _k(t, L["t_her"], L["t_land"] - L["t_her"], "in3")
    c = (lerp(c0[0], slot[0], u), lerp(c0[1], slot[1], u) - 90.0 * math.sin(math.pi * u))
    return c, lerp(h0, TRI_H, us), lerp(0.62, TRI_R, us)


def _wave_t(c):
    """When the pulse wave (out from her slot) reaches screen point c."""
    L = _layout()
    her = L["slots"][L["her"]]
    return L["t_pulse"] + math.hypot(c[0] - her[0], c[1] - her[1]) / WAVE


def _pulse(t, c):
    """The single pulse: each triangle swells and settles as the wave passes (scale)."""
    tt = t - _wave_t(c)
    if tt <= 0.0 or tt > 0.5:
        return 1.0
    if tt < 0.06:
        return 1.0 + 0.26 * math.sin(0.5 * math.pi * tt / 0.06) ** 2
    return 1.0 + 0.26 * math.exp(-(tt - 0.06) / 0.07)


def _drift(i, c):
    """Start time of triangle i's drift into s07: released by the wave, a little random."""
    return _wave_t(c) + 0.17 + 0.06 * hash01(i, 21)


def _bass(f, t, w, clip=None):
    """Everything red on paper (and s07's ink forest arriving at the end). clip: polygons the
    red is limited to (the paper bars while they sweep in)."""
    L = _layout()
    girl, hoods, assign = _targets()
    specks, tris = _grid_state(t)
    polys = []
    if t >= INK_BARS[0]:
        _ink_bars(f, t)
    with f.screen() as c:
        for (pc, h, ratio, rot, col) in specks:
            polys.append(_tri(pc, h, col, ratio, rot))
        for (pc, h, ratio, rot, i) in tris:
            s = _pulse(t, pc)
            td = _drift(i, pc)
            if t > td:
                hd = hoods[assign[i]] if hoods else girl
                u = _k(t, td, DRIFT, "inout3")
                ug = _k(t, td + DRIFT * 0.5, DRIFT * 0.5, "out3")
                pc = (lerp(pc[0], hd["x"], u), lerp(pc[1], hd["y"], u))
                h = lerp(h, hd["h"], ug)
                ratio = lerp(ratio, HOOD_R, ug)
                rot = rot * (1.0 - u)
            polys.append(_tri(pc, h * s, i, ratio, rot))
        # hers: the last one counted; then the girl standing in the clearing (s07)
        hc, hh, hr = _her_state(t, V.camera("wide"))
        if t >= L["t_land"]:
            s = _pulse(t, hc)
            td = _drift(len(L["slots"]), hc) + 0.05
            if t > td:
                u = _k(t, td, DRIFT + 0.1, "inout3")
                hc = (lerp(hc[0], girl["x"], u), lerp(hc[1], girl["y"], u))
                hh = lerp(hh, girl["h"], u)
                hr = lerp(hr, 0.6, u)
            hh *= s
        polys.append(_tri(hc, hh, 999, hr, 0.0))
        if clip:
            c.save()
            c.new_path()
            for q in clip:
                draw.poly(c, q)
            c.clip()
        bass.fill_polys(c, [bass.orient(p, True) for p in polys], RED)
        if clip:
            c.restore()


# ----------------------------------------------------------------------------- s07's forest
@lru_cache(maxsize=4)
def _s07_ink(scale):
    """s07's opening frame (t = 0) flattened to 2 inks exactly as the flatten transition will
    show it; returned as an ink-on-transparent cairo surface (device px) or None."""
    try:
        from engine.render import render_scene
        from engine import transitions as TR
        img = render_scene("red", "s07", 0.0, scale)
        tones, _ = bass.poster_tones("red")
        flat = TR.flatten_image(img, tones, 2, "auto", True, 5)
    except Exception:                                        # noqa: BLE001 - s07 not renderable
        return None
    b, g, r = [flat[..., i].astype(np.float32) for i in range(3)]
    red = (r > 90) & (r > g * 2.2) & (r > b * 2.2)
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    lo = 0.2126 * INK[0] + 0.7152 * INK[1] + 0.0722 * INK[2]
    hi = 0.2126 * PAPER[0] + 0.7152 * PAPER[1] + 0.0722 * PAPER[2]
    a = np.clip((hi - lum) / (hi - lo), 0.0, 1.0)
    a[red] = 0.0
    h, wd = a.shape
    arr = np.zeros((h, wd, 4), np.uint8)
    A = (a * 255.0 + 0.5).astype(np.uint8)
    arr[..., 3] = A                                          # premultiplied ink
    arr[..., 0] = (INK[2] * a * 255.0).astype(np.uint8)
    arr[..., 1] = (INK[1] * a * 255.0).astype(np.uint8)
    arr[..., 2] = (INK[0] * a * 255.0).astype(np.uint8)
    surf = cairo.ImageSurface.create_for_data(memoryview(np.ascontiguousarray(arr)), cairo.FORMAT_ARGB32, wd, h,
                                              wd * 4)
    keep = cairo.ImageSurface(cairo.FORMAT_ARGB32, wd, h)
    cc = cairo.Context(keep)
    cc.set_source_surface(surf, 0, 0)
    cc.paint()
    return keep


@lru_cache(maxsize=None)
def _ink_rects():
    return bass.bar_rects((0.0, 0.0, 1080.0, 1920.0), 7, "h", None, 0.0, 17, irregular=0.4)


def _ink_bars(f, t):
    """s07's flattened forest slides in as horizontal cut-paper bars (alternate sides)."""
    surf = _s07_ink(f.scale)
    if surf is None:
        return
    rects = _ink_rects()
    n = len(rects)
    c = f.ctx
    sc = f.scale
    for i, (x0, y0, x1, y1) in enumerate(rects):
        st = INK_BARS[0] + (INK_BARS[1] - 0.38) * (i / max(1.0, n - 1.0))
        u = _k(t, st, 0.38, "out5")
        if u <= 0.0:
            continue
        side = -1.0 if i % 2 == 0 else 1.0
        dx = side * 1140.0 * (1.0 - u)
        c.save()
        c.identity_matrix()
        y0d, y1d = (y0 - (1.5 if i else 0)) * sc, (y1 + 1.5) * sc
        poly = bass.cut_rect(-40.0 + dx, y0 - 1.5, 1120.0 + dx, y1 + 1.5, seed=40 + i, amp=1.6)
        c.new_path()
        draw.poly(c, [(x * sc, y * sc) for x, y in poly])
        c.clip()
        c.set_source_surface(surf, dx * sc, 0.0)
        c.paint()
        c.restore()


# ----------------------------------------------------------------------------- paper bars
def _paper_bars(f, t):
    """Bass bars of PAPER sweep in over the posterized view (alternate sides). Returns the
    bars' polygons (screen px) where they are now."""
    out = []
    with f.screen() as c:
        rects = bass.bar_rects((0.0, 0.0, 1080.0, 1920.0), 8, "h", None, 0.0, 5, irregular=0.35)
        for i, (x0, y0, x1, y1) in enumerate(rects):
            st = BARS[0] + (BARS[1] - 0.2) * hash01(i, 77)
            u = _k(t, st, 0.2, "out3")
            if u <= 0:
                continue
            side = -1.0 if i % 2 == 0 else 1.0
            dx = side * 1160.0 * (1.0 - u)
            poly = bass.cut_rect(-40.0 + dx, y0 - 2.0, 1120.0 + dx, y1 + 2.0, seed=60 + i, amp=1.6)
            bass.fill_polys(c, [poly], PAPER)
            out.append(poly)
    return out


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    w = _words(T)
    live = t < BARS[0] + BARS[1] + 0.02
    if live:
        _live(f, t, w)
    else:
        f.fill(PAPER)
    # the flatten: posterize, then paper bars, then pure Bass
    if POSTER3 <= t < BARS[0] + BARS[1] + 0.02:
        f.post["poster"] = bass.poster(f.pal, 1.0, tones=3 if t < POSTER2 else 2, thr=(0.16, 0.42))
    if t >= BARS[0]:
        clip = _paper_bars(f, t) if live else None
        g = _k(t, BARS[0], BARS[1], "inout")
        f.post["vignette"] = lerp(f.pal.vignette, 0.16, g)
        f.post["paper"] = 0.75 * g
        f.post["bloom"] = f.post.get("bloom", 0.0) * (1.0 - g)
        _bass(f, t, w, clip)


def motion_blur(t, T):
    w = _words(T)
    if w["winter"] + 0.15 < t < WIDE_T - 0.1:        # the fast pull-back
        return 2
    return 1


def cues(T):
    w = _words(T)
    L = _layout()
    return [
        Cue(0.0, "high wind over the ridge, then the valley's hush under it", -16, dur=4.0),
        Cue(0.6, "a low string drone opens as the view falls away down the path", -18, dur=3.8),
        Cue(w["house"], "the web catches the light: a thin glassy shimmer (bowed glass)", -16, dur=1.8),
        Cue(w["no"], "the shimmer dies: dead air", -24),
        Cue(w["hoods"] - 0.05, "red hoods: the low choir drone for Grandmother breathes in", -12, dur=2.4),
        Cue(w["hoods"] + 0.2, "many threads creak softly as the hoods sway", -22, dur=1.6),
        Cue(w["winter"], "pull back: a deep whoosh of cold air", -11, dur=0.8),
        Cue(POSTER3, "the view flattens: a dry paper snap", -9),
        Cue(BARS[0], "paper bars slide in (scissor-cut swishes)", -12, dur=0.32),
        Cue(RISE[0], "the hoods lift: a pizzicato flutter rising", -12, dur=0.45),
        Cue(LEDGER, "counting winters: a soft paper tick per row, accelerating", -8, dur=L["starts"][-1] - LEDGER + 0.1),
        Cue(L["t_land"], "her triangle lands in the last slot: one clear wooden knock", -6),
        Cue(L["t_pulse"], "the grid pulses once: a single low heartbeat drum", -4),
        Cue(L["t_pulse"] + 0.17, "the triangles drift into the trees: a held breath of strings", -14, dur=0.9),
        Cue(INK_BARS[0], "the forest slides in: heavy paper bars", -12, dur=0.6),
    ]
