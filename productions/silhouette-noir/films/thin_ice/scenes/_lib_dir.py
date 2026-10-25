"""THIN ICE: what the director's scenes share (s01-s03, s08-s12): the title and its crack, the
searchlight's clock, the fence view's space, figures from behind, and the river scenes' kit
(keyed cameras, a Dutch tilt, bodies that turn, water: bubbles, spray, the waterline, moonlight
shafts; the guard's hat and rifle as props).

The searchlight sweeps the zone between the fence and the woods on one clock for the whole film
(film time): its lit patch creeps over the crossing at film 19 (going east) and 25 (going west),
s02's two near misses, reversing with a clank at the east end of its swing in between (film 22).
Through s01 it sweeps the far west end of the zone, by the tower.
"""
import math
from contextlib import contextmanager
from functools import lru_cache

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from films.thin_ice import cast as C, kit as K, world as W

# ============================================================================ the searchlight's clock
SWEEP_P = 24.0          # s per full swing (there and back)
SWEEP_T_EAST = 22.0     # film time it reaches the east end of its swing
SWEEP_A = 20.0          # half the swing's width (m) ...
SWEEP_X0 = W.CROSS[0] - SWEEP_A * math.cos(2.0 * math.pi * 3.0 / SWEEP_P)   # ... about its middle: over the
#                         crossing 3 s either side of the east end (film 19, 25, 43, 49 ...); x 5.9 .. 45.9


def search_x(ft):
    """The searchlight patch's map x at film time ft."""
    return SWEEP_X0 + SWEEP_A * math.cos(2.0 * math.pi * (ft - SWEEP_T_EAST) / SWEEP_P)


def search_n(ft):
    """Its map n: 3 m inside the wire at the crossing (its edge slides over the drift there, a
    stride short of where they crouch), curving away from the wire toward the ends."""
    u = (search_x(ft) - W.CROSS[0]) / SWEEP_A
    return W.FENCE_N + 3.0 + 1.0 * u * u


def search_heading(ft):
    """Map heading (degrees from north) from the tower to the patch."""
    x, n = search_x(ft), search_n(ft)
    return math.degrees(math.atan2(x - W.TOWER[0], n - W.TOWER[1]))


# ============================================================================ the title
@lru_cache(maxsize=None)
def title_glyphs():
    return bass.title_glyphs("THIN\nICE", width=840.0, tracking=0.06, seed=11, rough=0.8, jitter=0.45, leading=1.12)


TITLE_C = (540.0, 880.0)


@lru_cache(maxsize=None)
def crack_line():
    """The title's crack: a jagged line across the whole frame, upper left to lower right,
    through the title (frame px)."""
    a, b = (-30.0, 600.0), (1110.0, 1170.0)
    n = 26
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    nx, ny = dy / L, -dx / L
    pts = []
    for i in range(n + 1):
        u = i / n
        j = 0.0 if i in (0, n) else 22.0 * K._sn(i, 401) + 9.0 * K._sn(i, 402)
        pts.append((a[0] + dx * u + nx * j, a[1] + dy * u + ny * j))
    return tuple(pts)


def crack_normal():
    a, b = crack_line()[0], crack_line()[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dy / L, -dx / L)          # pointing up and to the right (the upper floe's side)


@lru_cache(maxsize=None)
def crack_branches():
    """Short side cracks off the main one: (start index, polyline)."""
    out = []
    pts = crack_line()
    for k, i in enumerate((5, 9, 13, 17, 21)):
        p = pts[i]
        side = 1 if k % 2 == 0 else -1
        ang = math.radians(-26.6 + side * (50.0 + 20.0 * K._sn(k, 411)))
        L = 70.0 + 50.0 * hash01(k, 412)
        q = [p]
        for j in range(1, 4):
            u = j / 3.0
            q.append((p[0] + math.cos(ang) * L * u + 8.0 * K._sn(k, j, 413), p[1] + math.sin(ang) * L * u + 8.0 * K._sn(k, j, 414)))
        out.append((i, tuple(q)))
    return tuple(out)


def floe_regions(off, rot):
    """The two halves' clip polygons (upper/right, lower/left) for an opening `off` px each side
    and a rotation `rot` degrees each (upper turns -rot, lower +rot) about the title's centre."""
    pts = crack_line()
    n = crack_normal()
    up = [xf((p[0] + n[0] * 0.0, p[1] + n[1] * 0.0), off, -rot, +1) for p in pts]
    lo = [xf(p, off, rot, -1) for p in pts]
    upper = up + [xf((1400.0, -400.0), off, -rot, +1), xf((-400.0, -400.0), off, -rot, +1)]
    lower = lo + [xf((1400.0, 2400.0), off, rot, -1), xf((-400.0, 2400.0), off, rot, -1)]
    return upper, lower


def xf(p, off, rot, side):
    """A point of one floe, opened `off` px along the crack's normal (side +1 upper, -1 lower) and
    turned `rot` degrees about the title's centre."""
    n = crack_normal()
    cx, cy = TITLE_C
    a = math.radians(rot)
    x, y = p[0] - cx, p[1] - cy
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return (cx + x + n[0] * off * side, cy + y + n[1] * off * side)


def draw_title_floes(c, color, off=0.0, rot=0.0, alpha=1.0, letters=None):
    """The title's letters on their two floes (each clipped to its side of the crack, opened and
    turned). letters(i) -> (dx, dy, rot, alpha) per letter or None (hidden), for the assembly."""
    T = title_glyphs()
    upper, lower = floe_regions(off, rot)
    for region, side, r in ((upper, +1, -rot), (lower, -1, rot)):
        c.save()
        c.new_path()
        bass.draw.poly(c, region)
        c.clip()
        n = crack_normal()
        cx, cy = TITLE_C
        c.translate(cx + n[0] * off * side, cy + n[1] * off * side)
        c.rotate(math.radians(r))
        for i, g in enumerate(T):
            tr = letters(i) if letters is not None else (0.0, 0.0, 0.0, 1.0)
            if tr is None:
                continue
            dx, dy, gr, a = tr
            c.new_path()
            g.path(c, (0.0, 0.0), dx, dy, gr, 1.0, 1.0)
            bass._set(c, color, alpha * a)
            c.fill()
        c.restore()


def title_path(c, off=0.0, rot=0.0):
    """The title's outlines as the current path (both floes, opened): for the page's flood."""
    T = title_glyphs()
    n = crack_normal()
    cx, cy = TITLE_C
    c.new_path()
    for side, r in ((+1, -rot), (-1, rot)):
        c.save()
        c.translate(cx + n[0] * off * side, cy + n[1] * off * side)
        c.rotate(math.radians(r))
        for g in T:
            bass.path_polys(c, g.polys)
        c.restore()


# ============================================================================ small helpers
def pan_of(x):
    """A sound's pan from a frame x."""
    return round(clamp((x - 540.0) / 540.0, -1.0, 1.0) * 0.8, 3)


def beat(t, t0, dur=0.25, e="out3"):
    return ease(e, clamp((t - t0) / dur))


# ============================================================================ the fence view's space
# The fence set (world.draw_fence) is a camera about 4 m up and 4.7 m back from the wire, looking
# north: the posts' tops sit just under the horizon. Its backdrop (the woods' line, the tower, the
# hut) is a painted distance; figures on the near ground use this perspective.
FV_F = 757.0            # focal length (px)
FV_H = 4.0              # camera height (m)
FV_D = 4.73             # camera to the wire (m)
FV_Y0 = 600.0           # horizon (frame y at zoom 1)
FV_X = 40.5             # map x at the frame's centre line (the gap between the posts at 39 and 42)


def fv(x, d, z=0.0):
    """Frame point (zoom 1) of map x, d metres beyond the wire (negative: this side), z up."""
    k = FV_F / (FV_D + d)
    return (540.0 + (x - FV_X) * k, FV_Y0 + (FV_H - z) * k)


def fv_s(d):
    """px per metre at d metres beyond the wire (zoom 1)."""
    return FV_F / (FV_D + d)


# ---------------------------------------------------------------------------- fence-view helpers
def fv_par(d):
    """Parallax of a ground point d metres beyond the wire (the fence 1.0, the drift 1.3)."""
    return clamp(1.0 - 0.23 * d, 0.5, 1.45)


def fv_at(cam, x, d):
    """Frame point and px per metre of map x, d metres beyond the wire."""
    par = fv_par(d)
    return cam.xf(fv(x, d), par), fv_s(d) * cam.s(par)


def search_fv(ft):
    """The searchlight's patch on the zone, as the fence view paints it: (x, y, r) px at zoom 1."""
    x = search_x(ft)
    u = (x - W.CROSS[0]) / SWEEP_A
    return (540.0 + (x - FV_X) * 110.0, 1000.0 - 60.0 * u * u, 420.0)


def beam_fv(c, cam, sp, a=1.0):
    sx, sy, sr = sp
    K.beam(c, W.tower_lamp_px(cam), cam.xf((sx - sr * 0.75, sy), 0.5), cam.xf((sx + sr * 0.75, sy), 0.5), K.PAPER,
           alpha=0.12 * a)


def clip_drift(c, cam):
    pts = W.drift_poly(cam)
    c.new_path()
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    c.close_path()
    c.clip()


def post_shadows_on_drift(c, cam, ps, color):
    """The posts' long shadows carry on over the drift toward us."""
    a_ = clamp((ps - 0.3) / 0.7)
    if a_ <= 0.0:
        return
    c.save()
    clip_drift(c, cam)
    for x in W.POSTS:
        a = cam.xf((x, W.FENCE_Y), 1.0)
        b = cam.xf((x + 40.0, W.FENCE_Y + 700.0), 1.15)
        e = (a[0] + (b[0] - a[0]) * 2.4, a[1] + (b[1] - a[1]) * 2.4)
        w0, w1 = 16.0 * cam.s(1.15), 46.0 * cam.s(1.3)
        K.poly(c, [(b[0] - w0, b[1]), (b[0] + w0, b[1]), (e[0] + w1, e[1]), (e[0] - w1, e[1])], color, a_)
    c.restore()


SHADE_FV = lerp(W.SNOW, K.SHADOW, 0.9)


def shadow_fv(c, cam, x, d, h, w, color=SHADE_FV):
    """A figure's long moon shadow on the snow, falling back toward us (h: its height, m)."""
    ln = 1.5 * h
    K.poly(c, [fv_at(cam, x - w, d)[0], fv_at(cam, x + w, d)[0], fv_at(cam, x + w * 1.3 + 0.1 * ln, d - ln)[0],
               fv_at(cam, x - w * 1.3 + 0.1 * ln, d - ln)[0]], color)


# ============================================================================ figures from behind
def _e(cx, cy, rx, ry, n=22):
    return [(cx + rx * math.cos(6.283 * i / n), cy + ry * math.sin(6.283 * i / n)) for i in range(n)]


def _cap(a, b, ra, rb):
    return bass.capsule_pts(a, b, ra, rb, cap=4)


def _mix(a, b, u):
    return [(lerp(p[0], q[0], u), lerp(p[1], q[1], u)) for p, q in zip(a, b)]


_COAT_STAND = [(-0.29, 0.38), (0.29, 0.38), (0.19, 0.98), (0.235, 1.30), (0.17, 1.38), (-0.17, 1.38), (-0.235, 1.30),
               (-0.19, 0.98)]
_COAT_CROUCH = [(-0.38, 0.0), (0.38, 0.0), (0.37, 0.1), (0.33, 0.3), (0.27, 0.5), (0.22, 0.62), (0.15, 0.69),
                (-0.15, 0.69), (-0.22, 0.62), (-0.27, 0.5), (-0.33, 0.3), (-0.37, 0.1)]
_COAT_KNEEL = [(-0.33, 0.0), (0.33, 0.0), (0.3, 0.25), (0.2, 0.55), (0.215, 0.86), (0.17, 0.98), (-0.17, 0.98),
               (-0.215, 0.86), (-0.2, 0.55), (-0.3, 0.25)]
_COAT_FLAT = [(-0.24, 0.0), (-0.04, 0.0), (0.0, 0.045), (0.04, 0.0), (0.24, 0.0), (0.3, 0.08), (0.24, 0.16),
              (0.1, 0.2), (-0.1, 0.2), (-0.24, 0.16), (-0.3, 0.08)]


def back(c, who, at, s, pose="crouch", t=0.0, u=1.0, rim=None, rim_w=3.0, hand=None, color=K.INK, red=K.RED,
         wind=1.0):
    """The mother or the girl from behind, facing into the frame. at: the ground point under them
    (frame px); s: px per metre. pose 'stand', 'crouch' (u 0..1 from standing to squatting),
    'kneel', 'flat' (lying flat, boots toward us: the high camera sees a low mound), 'drop' (u 0..1
    from a squat down to flat), 'crawl' (on her belly, elbows working) and 'run' (u: the cycle's phase).
    hand: a frame point her right hand reaches for (the wire). rim: the moon's colour along the
    upper edges (it is in front of them, behind the fence) or None. Returns frame marks:
    head, top, nape, hand_r, base."""
    g = 1.0 if who == "mother" else 0.66
    polys, reds = [], []
    sway = 0.0
    dk = ease("inout", clamp(u)) if pose == "drop" else 0.0
    low = pose in ("flat", "crawl") or dk > 0.6
    if pose in ("stand", "crouch", "run", "drop"):
        k = {"stand": 0.0, "run": 0.0, "drop": 1.0}.get(pose, ease("inout", clamp(u)))
        bob = 0.03 * abs(math.sin(math.pi * 2.0 * u)) if pose == "run" else 0.0
        sq = lerp(1.0, 0.29, dk)                                                            # dropping flat
        coat = [(x * lerp(1.0, 0.85, dk), (y + bob) * sq) for x, y in _mix(_COAT_STAND, _COAT_CROUCH, k)]
        polys.append(coat)
        top_y = (lerp(1.38, 0.70, k) + bob) * sq
        if pose == "run":
            for side in (-1, 1):
                ph = math.sin(2.0 * math.pi * u + (0.0 if side < 0 else math.pi))
                kick = max(0.0, ph)
                foot = (0.09 * side, 0.02 + 0.32 * kick)
                polys.append(_cap((0.08 * side, 0.5 + bob), foot, 0.06, 0.05))
                polys.append(_e(foot[0], foot[1] - 0.01, 0.06, 0.05 + 0.03 * kick))       # the boot's sole, kicked up
                hy = 0.95 + bob + 0.1 * math.sin(2.0 * math.pi * u + (math.pi if side < 0 else 0.0))
                polys.append(_cap((0.2 * side, 1.28 + bob), (0.27 * side, hy), 0.05, 0.045))
        elif k < 0.9:
            for side in (-1, 1):
                polys.append(_cap((0.08 * side, lerp(0.5, 0.1, k)), (0.09 * side, 0.03), 0.055, 0.05))
                polys.append(_e(0.09 * side, 0.03, 0.065, 0.05))
                polys.append(_cap((0.2 * side, top_y - 0.08), (0.26 * side, lerp(0.82, 0.45, k)), 0.05, 0.045))
        head_c = (0.0, top_y + lerp(0.18, 0.12, k) * lerp(1.0, 0.5, dk))                    # hunched: the head drops
    elif pose == "kneel":
        polys.append(_COAT_KNEEL)
        polys.append(_cap((-0.2, 0.92), (-0.3, 0.08), 0.05, 0.045))                       # left hand on the snow
        top_y = 1.0
        head_c = (0.0, 1.18)
    elif pose == "flat":
        polys.append(_COAT_FLAT)                                                           # legs toward us
        top_y = 0.2
        head_c = (0.0, 0.26)
    else:   # crawl: flat on her belly, the elbows working by turns, the body wriggling after them
        sway = 0.025 * math.sin(2.0 * math.pi * u)
        polys.append([(x + sway * y / 0.23, y * 1.15) for x, y in _COAT_FLAT])
        for side in (-1, 1):
            el = 0.04 * math.sin(2.0 * math.pi * u + (math.pi if side < 0 else 0.0))
            polys.append(_e(0.27 * side + sway, 0.13 + el, 0.07, 0.065))                          # elbows
        top_y = 0.23
        head_c = (sway, 0.3)
    # head, from behind
    hx, hy = head_c
    if who == "mother":
        if low:
            polys.append(_e(hx, top_y + 0.02, 0.07, 0.04))                                 # the knot
            polys.append(_e(hx, hy, 0.095, 0.08))
        else:
            polys.append(_e(hx, top_y + 0.05, 0.075, 0.055))                               # the knot at her nape
            polys.append(_e(hx, hy, 0.1, 0.12))
            polys.append([(hx - 0.1, hy - 0.05), (hx + 0.1, hy - 0.05), (hx + 0.125, hy - 0.13),
                          (hx - 0.125, hy - 0.13)])                                        # the headscarf flaring out
    else:
        hr = 0.15                                                                          # her head is big for her size
        fl = wind * 0.04 * math.sin(t * 6.0)
        if low:
            hy = top_y + hr * 0.6
            polys.append(_e(hx, hy, hr * 0.95, hr * 0.8))
            polys.append(_e(hx, hy + hr * 0.75, 0.06, 0.05))
            reds.append(_e(hx, top_y + 0.01, 0.14, 0.05))
            if pose == "crawl":       # the scarf's end hangs down to the snow
                reds.append([(hx + 0.06, top_y), (hx + 0.12, top_y - 0.01), (0.17 + fl, 0.04), (0.11 + fl, 0.04)])
            else:                     # lying across her back
                reds.append([(hx + 0.05, top_y), (hx + 0.11, top_y - 0.01), (0.2 + fl, 0.06), (0.14 + fl, 0.05)])
        else:
            hy = top_y + 0.2
            polys.append(_e(hx, hy, hr, hr * 1.05))
            polys.append(_e(hx, hy + hr * 1.1, 0.065, 0.06))                               # the pompom
            wrap = _e(hx, top_y + 0.02, 0.16, 0.06)
            tail = [(hx + 0.04, top_y + 0.02), (hx + 0.1, top_y + 0.01), (hx + 0.15 + fl, top_y - 0.38),
                    (hx + 0.07 + fl * 0.7, top_y - 0.42)]
            reds += [wrap, tail]
        head_c = (hx, hy)
    # to frame px
    X = lambda p: (at[0] + p[0] * g * s, at[1] - p[1] * g * s)
    fp = [[X(p) for p in q] for q in polys]
    hand_px = None
    if hand is not None:
        sh = X((0.2, top_y - 0.06))
        fp.append(_cap(sh, hand, 0.05 * g * s, 0.045 * g * s))
        fp.append(_e(hand[0], hand[1], 0.055 * g * s, 0.06 * g * s))
        hand_px = hand
    if rim is not None:
        c.save()
        c.translate(0.0, -rim_w)
        K.polys(c, fp, rim)
        c.restore()
    K.polys(c, fp, color)
    if reds and color == K.INK:
        K.polys(c, [[X(p) for p in q] for q in reds], red)
    return {"head": X(head_c), "top": X((head_c[0], head_c[1] + 0.13)), "nape": X((head_c[0], top_y)),
            "hand_r": hand_px, "base": at}


def back_breath(c, head, s, t, rate=0.9, phase=0.0, stop=None, strength=1.0):
    """Breath seen from behind: pale puffs rising past the far side of the head and drifting east.
    stop: the time the puffs stop (a held breath)."""
    for k in range(3):
        n = math.floor((t - phase) / rate) - k
        t0 = phase + n * rate
        if stop is not None and t0 > stop:
            continue
        age = t - t0
        if age < 0.0 or age > 1.2:
            continue
        a = age / 1.2
        r = (0.05 + 0.12 * ease("out", a)) * s
        p = (head[0] + (0.06 + 0.22 * a) * s, head[1] - (0.12 + 0.2 * a) * s)
        K.disc(c, p, r, K.PAPER, seed=int(n) % 97, alpha=0.4 * strength * (1.0 - a) ** 1.4)


# ============================================================================ the river scenes (s08-s12)
# Profile views look west through the river's section (world.draw_river): north to the right,
# the moon up and to the right. Pages are plans (world.draw_page), north up.
LIGHT = (0.8, -0.6)
RIM = lerp(K.SNOW, K.PAPER, 0.4)              # the moon's edge on a figure
RIM_WET = lerp(K.WATER, K.PAPER, 0.55)        # ... under the water


def _seg(t, keys):
    """The keys either side of t and the eased fraction between them (the ease of the key moved
    toward: keys [(t, v), ...] or [(t, v, ease), ...])."""
    if t <= keys[0][0]:
        return keys[0], keys[0], 0.0
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            e = b[2] if len(b) > 2 else "inout"
            return a, b, ease(e, (t - a[0]) / max(b[0] - a[0], 1e-9))
    return keys[-1], keys[-1], 0.0


def track(t, keys):
    """A keyed value at t (a number or a tuple of numbers), eased between keys."""
    a, b, u = _seg(t, keys)
    if isinstance(a[1], tuple):
        return tuple(lerp(x, y, u) for x, y in zip(a[1], b[1]))
    return lerp(a[1], b[1], u)


def dio_at(t, keys):
    """A diorama camera eased between keys [(t, W.Dio(...)[, ease]), ...] (zoom in log space)."""
    a, b, u = _seg(t, keys)
    return W.dio_lerp(a[1], b[1], u)


def plan_at(t, keys):
    """A page camera eased between keys [(t, W.Plan(...)[, ease]), ...]."""
    a, b, u = _seg(t, keys)
    return W.plan_lerp(a[1], b[1], u)


def shake(t, t0, amp=14.0, dur=0.35):
    """A camera shake at t0 (px), dying out over dur."""
    u = (t - t0) / dur
    if u < 0.0 or u > 1.0:
        return (0.0, 0.0)
    a = amp * (1.0 - u) ** 2
    return (a * math.sin(t * 91.0), a * 0.6 * math.cos(t * 77.0))


@contextmanager
def tilted(c, deg):
    """A Dutch tilt: the frame turned `deg` about its centre and zoomed just enough that the
    turned frame stays inside what was drawn for it."""
    a = math.radians(abs(deg))
    k = math.cos(a) + (1920.0 / 1080.0) * math.sin(a)
    c.save()
    c.translate(540.0, 960.0)
    c.rotate(math.radians(deg))
    c.scale(k, k)
    c.translate(-540.0, -960.0)
    try:
        yield
    finally:
        c.restore()


def stance(who, step=0.0, spread=16.0, sink=0.0):
    """A standing state with the near foot `step` m ahead of the far one (the pelvis sinks a
    little in a long stance; `sink` m more)."""
    st = C.standing(who, 0.0, spread)
    m = C.M_PER_UNIT[who]
    h = step / m * 0.5
    F = C.fig(who)
    drop = F.leg * 0.965 - math.sqrt(max((F.leg * 0.95) ** 2 - h * h, 1.0)) + sink / m
    P = st["pelvis"]
    n, f = st["feet"]["near"], st["feet"]["far"]
    return dict(st, pelvis=(P[0], P[1] + max(drop, 0.0)), feet={"near": (n[0] + h, n[1], n[2]), "far": (f[0] - h, f[1], f[2])})


def free_state(who, near, far, pitch=(0.0, 0.0), skirt=True):
    """A state for a body off the ground (falling, swimming, clinging): its feet at `near` and
    `far` (m from the pelvis, x forward, y down), the pelvis where the root is drawn."""
    m = C.M_PER_UNIT[who]
    return dict(pelvis=(0.0, 0.0), feet={"near": (near[0] / m, near[1] / m, pitch[0]), "far": (far[0] / m, far[1] / m, pitch[1])},
                phase=0.0, speed=0.0, run=0.0, stride=0.0, skirt=skirt)


def figure(c, cam, who, st, pose, u, z, d=0.0, facing=1, roll=0.0, rim=RIM, light=LIGHT, **kw):
    """cast.draw at the diorama point (u, z, d), the whole body turned `roll` degrees (clockwise on
    screen) about its pelvis: a body falling, sinking, swimming; the moon's rim stays up and to
    the right. Returns the joints in frame px, 'scale' and 'pivot' (the pelvis)."""
    s = C.scale(who, cam.scale(d))
    at = cam.px(u, z, d)
    return figure_at(c, who, st, pose, at, s, facing, roll, rim, light, **kw)


def figure_at(c, who, st, pose, at, s, facing=1, roll=0.0, rim=RIM, light=LIGHT, **kw):
    """figure() at a frame point (the root) and a scale (px per figure unit)."""
    pv = (at[0], at[1] + s * (st["pelvis"][1] + pose.crouch))
    if abs(roll) < 1e-6:
        j = C.draw(c, who, st, pose, at, s, facing, rim=rim, light=light, **kw)
        j["pivot"] = pv
        return j
    a = math.radians(roll)
    lt = (light[0] * math.cos(a) + light[1] * math.sin(a), -light[0] * math.sin(a) + light[1] * math.cos(a))
    c.save()
    c.translate(*pv)
    c.rotate(a)
    c.translate(-pv[0], -pv[1])
    j = C.draw(c, who, st, pose, at, s, facing, rim=rim, light=lt, **kw)
    dev = {k: c.user_to_device(*v) for k, v in j.items() if isinstance(v, tuple)}
    c.restore()
    out = {k: c.device_to_user(*v) for k, v in dev.items()}
    out["scale"] = s
    out["pivot"] = pv
    return out


def turn_pt(p, pivot, deg):
    """p turned deg degrees (clockwise on screen) about pivot."""
    a = math.radians(deg)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + x * math.cos(a) - y * math.sin(a), pivot[1] + x * math.sin(a) + y * math.cos(a))


# ---------------------------------------------------------------------------- the guard's hat and rifle
@lru_cache(maxsize=None)
def _prop(kind):
    F = C.fig("guard")
    if kind == "hat":
        polys, pivot = [p for p, _ in F.head[3:6]], (8.0, -398.0)
    else:
        polys, pivot = [p for p, _ in F.torso[3:5]], (-55.0, -216.0)
    return pivot, tuple(tuple((x - pivot[0], y - pivot[1]) for x, y in q) for q in polys)


def prop_home(kind, st, pose, at, s, facing=1, roll=0.0, pivot=None):
    """Where the guard's hat or rifle sits on him (frame px of its pivot, its angle in degrees)
    when he is drawn by figure_at(..., at, s, facing, roll) with the head held straight."""
    pv, _ = _prop(kind)
    p = C.frame_point("guard", st, pose, pv, at, s, facing)
    ang = pose.lean * facing
    if roll and pivot is not None:
        p = turn_pt(p, pivot, roll)
        ang += roll
    return p, ang


def prop(c, kind, p, s, ang=0.0, facing=1, color=K.INK, rim=None, rim_w=2.5, light=LIGHT):
    """The guard's hat or rifle on its own: its pivot at p (frame px), s px per figure unit, turned
    ang degrees."""
    _, polys = _prop(kind)
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    out = [[(p[0] + (facing * x * ca - y * sa) * s, p[1] + (facing * x * sa + y * ca) * s) for x, y in q] for q in polys]
    if rim is not None:
        K.polys(c, [[(x + light[0] * rim_w, y + light[1] * rim_w) for x, y in q] for q in out], rim)
    K.polys(c, out, color)


# ---------------------------------------------------------------------------- water
def water_poly(cam, n0, n1, top=None, m=40):
    """The river's water in the section between n0 and n1 (frame px): from `top` (z; default the
    ice's top) down to the riverbed."""
    zt = W.ICE_Z if top is None else top
    ns = [n0 + (n1 - n0) * i / m for i in range(m + 1)]
    return [cam.px(n, zt) for n in ns] + [cam.px(n, W.bed_z(n)) for n in ns[::-1]]


def wash(c, cam, n0, n1, top=None, alpha=0.55):
    """A translucent layer of the river over whatever is in it (a body half under)."""
    K.poly(c, water_poly(cam, n0, n1, top), K.WATER, alpha)


def waterline(c, cam, n0, n1, t, z=None, seed=0, amp=1.0, alpha=0.8):
    """The water's surface in a hole: a thin PAPER line, lapping."""
    zz = W.ICE_Z if z is None else z
    m = 24
    pts = []
    for i in range(m + 1):
        n = n0 + (n1 - n0) * i / m
        w = 0.012 * amp * math.sin(n * 9.0 - t * 7.0 + seed) + 0.008 * amp * math.sin(n * 21.0 + t * 11.0)
        pts.append(cam.px(n, zz + w))
    K.band(c, pts, K.PAPER, max(1.5, 0.012 * cam.ppm), seed=seed, alpha=alpha)


def rings(c, p, t, t0, rx, ry, n=3, every=0.35, life=1.2, width=3.0, seed=0, alpha=0.7, color=K.PAPER):
    """Rings spreading on water from p (flat ellipses rx x ry at their widest), one every `every`
    s from t0."""
    if t < t0:
        return
    k = math.floor((t - t0) / every)
    for j in range(k - n + 1, k + 1):
        if j < 0:
            continue
        a = (t - t0 - j * every) / life
        if 0.0 <= a < 1.0:
            g = ease("out3", a)
            pts = [(p[0] + rx * g * math.cos(q), p[1] + ry * g * math.sin(q)) for q in [6.283 * i / 40 for i in range(41)]]
            K.band(c, pts, color, width * (1.0 - 0.7 * a), seed=seed + j, alpha=alpha * (1.0 - a))


def bubbles(c, src, t, t0, t1, top_y, ppm, rate=8.0, seed=0, rise=1.0, size=1.0, alpha=0.85, spread=0.05):
    """Bubbles rising from src(t) (frame px), born `rate` a second between t0 and t1: each wobbles
    up at about `rise` m/s, swelling a little, and is gone at top_y (the ice above)."""
    n = int((t1 - t0) * rate) + 1
    for i in range(n):
        tb = t0 + (i + 0.8 * hash01(seed, i)) / rate
        if tb > t or tb > t1:
            continue
        age = t - tb
        p0 = src(tb)
        v = rise * (0.7 + 0.6 * hash01(seed, i, 1)) * ppm
        y = p0[1] - v * age - 0.25 * ppm * age * age
        if y < top_y:
            continue
        wob = 0.04 * ppm * math.sin(age * (6.0 + 4.0 * hash01(seed, i, 2)) + 6.28 * hash01(seed, i, 3))
        x = p0[0] + spread * ppm * K._sn(seed, i, 5) * (1.0 + age) + wob
        r = (0.012 + 0.03 * hash01(seed, i, 4) ** 2) * ppm * size * (1.0 + 0.35 * age)
        if r > 6.0:
            bass.ring(c, (x, y), r, max(1.2, r * 0.28), K.PAPER, seed=seed + i, alpha=alpha)
            K.dot(c, (x + r * 0.3, y - r * 0.35), max(1.0, r * 0.22), K.PAPER, seed=seed + i, alpha=alpha)
        else:
            K.dot(c, (x, y), max(1.2, r), K.PAPER, seed=seed + i, alpha=alpha * 0.9)


def spray(c, p, t, t0, ppm, n=18, seed=0, power=1.0, life=0.8, spread=1.0, up=1.0, color=K.PAPER, alpha=0.95):
    """Water thrown up at p (frame px) at t0: drops flying up and out, falling back, gone."""
    a = (t - t0) / life
    if not 0.0 <= a < 1.0:
        return
    tt = a * life
    for i in range(n):
        ang = math.radians(-90.0 + 70.0 * spread * K._sn(seed, i, 1))
        v = (1.2 + 2.2 * hash01(seed, i, 2)) * power
        x = p[0] + math.cos(ang) * v * tt * ppm
        y = p[1] + (math.sin(ang) * v * up * tt + 4.9 * tt * tt) * ppm
        r = ppm * (0.012 + 0.03 * hash01(seed, i, 3)) * (1.0 - 0.3 * a)
        K.ellipse(c, (x, y), r * 0.8, r * 1.3, color, angle=math.degrees(ang) + 90.0, alpha=alpha * (1.0 - a) ** 1.2)


def shafts(c, top_l, top_r, length, t, strength=1.0, lean=0.55, seed=0):
    """Moonlight slanting down through a hole into the water (from the upper right to the lower
    left): flat wedges from the hole's span top_l..top_r (frame px), wavering a little."""
    for i in range(4):
        f = 1.0 - i / 4.0
        w = 0.15 * math.sin(t * (0.9 + 0.3 * i) + seed + i)
        a = (lerp(top_l[0], top_r[0], 0.5 - 0.5 * f), lerp(top_l[1], top_r[1], 0.5 - 0.5 * f))
        b = (lerp(top_l[0], top_r[0], 0.5 + 0.5 * f), lerp(top_l[1], top_r[1], 0.5 + 0.5 * f))
        dx = -lean * length * (1.0 + w * 0.3)
        spread_ = (b[0] - a[0]) * (0.35 + 0.25 * f)
        K.poly(c, [a, b, (b[0] + dx + spread_, b[1] + length), (a[0] + dx - spread_, a[1] + length)], K.PAPER,
               0.045 * strength * (0.6 + 0.4 * f))
