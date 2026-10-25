"""THIN ICE: what the animator's scenes share (s04 TRACKS, s05 RIVER, s06 FALSE TRAIL, s07 HUNTER).

  * timing and camera keys (eased, on the beat);
  * the woods, looking west along the path (an extended copy of world.draw_woods): the
    searchlight's lit patch with the trunks' shadows cut out of it, the lantern's warm pool on
    the snow, far lanterns among the trees, the record of footprints seen on the snow, a few
    trunks in front of the path; wading figures sink into the deep snow (clipped at its surface);
  * the river view's extras: the woods' edge on the near bank, reeds in front of a figure, the
    lantern's pool on the ice, a far window that a look can reach;
  * figures: walkers in metres, a paper turn, the guard's lantern, breath;
  * the record of footprints as these scenes lay it (the guard's woods prints are laid as far as
    he has walked: s05 and s06 show them only behind his lantern);
  * sound: pan from a frame x.

Units: metres on the map; frame px (1080 x 1920) on screen.
"""
import math
from functools import lru_cache

import cairo

from engine import bass, draw as D, paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from films.thin_ice import cast as C, faces as F, kit as K, world as W

INK, NIGHT, STEEL, SNOW, SHADOW = K.INK, K.NIGHT, K.STEEL, K.SNOW, K.SHADOW
ICE, THIN, WATER, PAPER, AMBER, RED = K.ICE, K.THIN, K.WATER, K.PAPER, K.AMBER, K.RED
LIGHT = (0.8, -0.6)                 # the moon is up and to the right in every profile view


# ============================================================================ timing
def kk(t, t0, dur, e="inout"):
    """0..1 eased from t0 over dur."""
    return ease(e, clamp((t - t0) / dur)) if dur > 0 else (1.0 if t >= t0 else 0.0)


def bump(t, t0, t1, e="inout"):
    """0 -> 1 -> 0 between t0 and t1 (a sine hump)."""
    if t <= t0 or t >= t1:
        return 0.0
    return math.sin(math.pi * (t - t0) / (t1 - t0))


def track(t, keys):
    """Keyframed scalar: keys [(t, v), ...] or [(t, v, ease)], eased between keys."""
    if t <= keys[0][0]:
        return keys[0][1]
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            e = b[2] if len(b) > 2 else "inout"
            u = ease(e, (t - a[0]) / max(b[0] - a[0], 1e-9))
            va, vb = a[1], b[1]
            if isinstance(va, tuple):
                return tuple(lerp(x, y, u) for x, y in zip(va, vb))
            return lerp(va, vb, u)
    return keys[-1][1]


def shot_of(t, shots):
    """The name of the shot at t: shots [(t0, name), ...]."""
    name = shots[0][1]
    for t0, n in shots:
        if t >= t0:
            name = n
    return name


# ============================================================================ cameras
def dio(t, keys):
    """A diorama camera eased between keys [(t, (u0, z0, ppm, eye, D)[, ease]), ...]."""
    if t <= keys[0][0]:
        return W.Dio(*keys[0][1])
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            e = b[2] if len(b) > 2 else "inout"
            u = ease(e, (t - a[0]) / max(b[0] - a[0], 1e-9))
            return W.dio_lerp(W.Dio(*a[1]), W.Dio(*b[1]), u)
    return W.Dio(*keys[-1][1])


def plan(t, keys):
    """A plan camera eased between keys [(t, (x, n, ppm)[, ease]), ...]."""
    if t <= keys[0][0]:
        return W.Plan(*keys[0][1])
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            e = b[2] if len(b) > 2 else "inout"
            u = ease(e, (t - a[0]) / max(b[0] - a[0], 1e-9))
            return W.plan_lerp(W.Plan(*a[1]), W.Plan(*b[1]), u)
    return W.Plan(*keys[-1][1])


# ============================================================================ the path, in the woods view
D_PATH = 1.15        # the mother's line runs this far behind the woods' cut; the girl's 0.55 m
                     # nearer (she walks to her mother's right, east), the guard's 0.55 m deeper


@lru_cache(maxsize=1)
def _path_n():
    return tuple(p[1] for p in W.PATH), tuple(p[0] for p in W.PATH)


def path_x(n):
    """The path's x at map n (it runs north all the way)."""
    ns, xs = _path_n()
    if n <= ns[0]:
        return xs[0]
    for (n0, x0), (n1, x1) in zip(zip(ns, xs), zip(ns[1:], xs[1:])):
        if n <= n1:
            return lerp(x0, x1, (n - n0) / (n1 - n0))
    return xs[-1]


def wd(x, n):
    """A map point's depth behind the woods' cut (the cut follows the path)."""
    return D_PATH + path_x(n) - x


D_GIRL = D_PATH - W.GIRL_OFF
D_GUARD = D_PATH + 0.55


# ============================================================================ the woods (looking west)
@lru_cache(maxsize=1)
def fg_trunks():
    """Trunks between the woods' cut and the path (u, d, width m, seed): dark, close, sparse; kept
    clear of the places where the story stops (the stumble)."""
    out = []
    u = -120.0
    i = 0
    while u < -2.0:
        uu = u + 1.6 * K._sn(i, 501)
        if not (-51.5 < uu < -44.0):
            out.append((uu, 0.18 + 0.3 * hash01(i, 502), 0.34 + 0.12 * hash01(i, 503), 7000 + i))
        u += 5.2 + 3.0 * hash01(i, 504)
        i += 1
    return tuple(out)


def _ground_ring(cam, u, d, ru, rd, z=0.0, n=40):
    return [cam.px(u + ru * math.cos(a), z, d + rd * math.sin(a)) for a in [6.2832 * i / n for i in range(n)]]


def above_cut(c, cam, pad=40.0, n=64):
    """Clip to the frame above the river view's cut edge (the snow's top on its d = 0 plane)."""
    c.new_path()
    c.move_to(-pad, -pad)
    for i in range(n + 1):
        u = cam.u_at(-pad + (1080.0 + 2.0 * pad) * i / n)
        c.line_to(*cam.px(u, W.land_z(u), 0.0))
    c.line_to(1080.0 + pad, -pad)
    c.close_path()
    c.clip()


def ground_glow(c, cam, u, d, r, strength=1.0, t=0.0, z=0.0, color=AMBER, seed=0, steps=4, cut=False):
    """A lantern's warm pool on the ground plane of a diorama (r m), nested flat rings, added.
    cut: a river view's pool, kept off the cut's face (above_cut)."""
    if strength <= 0.01:
        return
    tt = K.twos(t)
    fl = 1.0 + 0.03 * math.sin(tt * 9.0 + seed) + 0.02 * K._sn(int(tt * 12), seed)
    c.save()
    if cut:
        above_cut(c, cam)
    c.set_operator(cairo.OPERATOR_ADD)
    for i in range(steps):
        f = (1.0 - i / steps)
        rr = r * fl * (0.35 + 0.65 * f)
        bass.fill_polys(c, [bass.orient(_ground_ring(cam, u, d, rr, rr * 0.8, z, 40), True)], color, 0.055 * strength)
    c.restore()


def tower_dir(u, d):
    """Unit direction (du, dd) on the ground of the woods view away from the tower (the
    searchlight's source, far to the left: south)."""
    su, sd = W.TOWER[1], wd(W.TOWER[0], W.TOWER[1])
    du, dd = u - su, d - sd
    L = math.hypot(du, dd) or 1.0
    return du / L, dd / L


def woods(c, cam, t=0.0, moonlit=1.0, search=None, lamps=(), far_lamps=(), prints=(), stars_on=True, fg=True,
          beam=None):
    """The woods, cut open along the path and seen from the east (looking west, north to the
    right). search: (u, d, ru, rd, alpha) the searchlight's lit patch on the snow, the trunks'
    shadows cut out of it; beam: (apex px, alpha) the beam down to it from the upper left.
    lamps: [(u, d, r_m, strength)] lantern pools on the snow; far_lamps: [(u, d, strength)] far
    lanterns among the trees; prints: footprint tuples (map) drawn on the snow. fg: the trunks
    between the cut and the path (call fg_layer after the figures instead: pass fg=False)."""
    hy = cam.horizon_y()
    snow_c = lerp(K.SNOW_DIM, SNOW, moonlit)
    K.fill(c, NIGHT)
    if stars_on:
        K.stars(c, t, y1=min(hy, 1920.0) - 30.0)
    K.poly(c, [(-50.0, hy - 1.0), (1130.0, hy - 1.0), (1130.0, 1970.0), (-50.0, 1970.0)], snow_c)
    shade_c = lerp(snow_c, SHADOW, 0.55)
    trees = W._wood_trees()
    # far pines and the near trees' moon shadows (south: to the left)
    for (u, d, h, i) in trees:
        base = cam.px(u, 0.0, d)
        sc = cam.scale(d)
        if base[0] < -400 or base[0] > 1480 or base[1] < hy - 4:
            continue
        col = lerp(INK, STEEL, clamp((d - 4.0) / 60.0) * 0.9)
        if d > 18.0:
            pine_side(c, base, h * sc, h * 0.36 * sc, col, seed=i)
            continue
        w = (0.28 + 0.12 * hash01(i, 4)) * sc
        L = h * W.SHADOW_K * 0.55
        sh = [cam.px(u - 0.1, 0.0, d - w / sc * 0.5), cam.px(u + 0.1, 0.0, d + w / sc * 0.5),
              cam.px(u - L, 0.0, d + 0.6), cam.px(u - L, 0.0, d - 0.6)]
        K.poly(c, sh, shade_c, 0.8)
    if search is not None:
        _search_woods(c, cam, search, snow_c, trees)
    for (u, d, s) in far_lamps:
        _far_lamp(c, cam, u, d, s, t)
    if prints:
        prints_side(c, cam, prints, snow_c)
    for (u, d, r, s) in lamps:
        ground_glow(c, cam, u, d, r, s, t, seed=int(u * 7) % 97)
    for (u, d, h, i) in trees:
        base = cam.px(u, 0.0, d)
        sc = cam.scale(d)
        if d > 18.0 or base[0] < -200 or base[0] > 1280 or base[1] < hy - 4:
            continue
        _trunk(c, cam, u, d, h, i, snow_c)
    if search is not None and beam is not None:
        _search_beam(c, cam, search, beam)
    # the cut: snow over earth
    u_l, u_r = cam.u_at(-80.0), cam.u_at(1160.0)
    ns = [u_l + (u_r - u_l) * i / 160.0 for i in range(161)]
    lo_z = cam.z_at(2000.0)
    K.poly(c, [cam.px(n, 0.0) for n in ns] + [cam.px(u_r, lo_z), cam.px(u_l, lo_z)], INK)
    K.poly(c, [cam.px(n, 0.0) for n in ns] + [cam.px(n, -W.snow_depth(n)) for n in ns[::-1]], SHADOW)
    if fg:
        fg_layer(c, cam, snow_c)


def pine_side(c, base, h, w, color, seed=0):
    """A far pine in profile: a bare trunk, the crown high up in drooping tiers (the canopy)."""
    trunk = [(base[0] - w * 0.045, base[1]), (base[0] + w * 0.045, base[1]), (base[0] + w * 0.02, base[1] - h),
             (base[0] - w * 0.02, base[1] - h)]
    ps = [trunk]
    tiers = 5
    for i in range(tiers):
        u0 = 0.52 + 0.48 * i / tiers
        u1 = 0.52 + 0.48 * (i + 1.7) / tiers
        y0 = base[1] - h * u0
        y1 = base[1] - h * min(1.0, u1)
        ww = w * 0.5 * (1.0 - 0.72 * i / tiers) * (0.8 + 0.4 * hash01(seed, i))
        ps.append([(base[0] - ww, y0 + h * 0.035), (base[0] - ww * 0.3, y0 - h * 0.008), (base[0], y1),
                   (base[0] + ww * 0.32, y0 - h * 0.01), (base[0] + ww, y0 + h * 0.04)])
    K.polys(c, ps, color)


def _trunk(c, cam, u, d, h, i, snow_c, col=None):
    base = cam.px(u, 0.0, d)
    sc = cam.scale(d)
    col = col or lerp(INK, STEEL, clamp((d - 4.0) / 60.0) * 0.9)
    w = (0.28 + 0.12 * hash01(i, 4)) * sc
    lean = 0.025 * K._sn(i, 6) * h * sc
    top = base[1] - h * sc
    K.poly(c, [(base[0] - w / 2, base[1] + 2), (base[0] + w / 2, base[1] + 2), (base[0] + w * 0.35 + lean, top),
               (base[0] - w * 0.35 + lean, top)], col)
    K.poly(c, [(base[0] + w * 0.12, base[1] - 0.3 * sc), (base[0] + w / 2, base[1] - 0.3 * sc),
               (base[0] + w * 0.38 + lean * 0.4, base[1] - h * sc * 0.45),
               (base[0] + w * 0.22 + lean * 0.4, base[1] - h * sc * 0.43)], lerp(snow_c, col, 0.35), 0.8)
    for j in range(3):
        by = base[1] - (0.35 + 0.12 * j + 0.05 * hash01(i, j, 7)) * h * sc
        bl = (0.8 + 0.7 * hash01(i, j, 5)) * sc
        sgn = 1 if (i + j) % 2 else -1
        bx = base[0] + lean * (base[1] - by) / max(h * sc, 1.0)
        K.band(c, [(bx, by), (bx + sgn * bl, by + 0.3 * sc), (bx + sgn * bl * 1.2, by + 0.55 * sc)], col,
               max(1.5, 0.06 * sc), seed=i * 5 + j, taper=(1.0, 0.2))
    K.ellipse(c, (base[0] + w * 0.3, base[1]), w * 0.9, max(2.0, 0.08 * sc), lerp(snow_c, PAPER, 0.25))


def fg_layer(c, cam, snow_c=SNOW, trunks=None, tall=16.0):
    """The trunks between the woods' cut and the path, in front of the walkers (or `trunks`:
    [(u, d, width m, seed)])."""
    for (u, d, w, i) in (trunks if trunks is not None else fg_trunks()):
        base = cam.px(u, 0.0, d)
        if base[0] < -150 or base[0] > 1230:
            continue
        sc = cam.scale(d)
        ww = w * sc
        lean = 0.02 * K._sn(i, 6) * 14.0 * sc
        top = base[1] - tall * sc
        K.poly(c, [(base[0] - ww / 2, base[1] + 3), (base[0] + ww / 2, base[1] + 3), (base[0] + ww * 0.4 + lean, top),
                   (base[0] - ww * 0.4 + lean, top)], INK)
        # the moonlit snow caught on its north side
        K.poly(c, [(base[0] + ww * 0.18, base[1] - 0.25 * sc), (base[0] + ww / 2, base[1] - 0.25 * sc),
                   (base[0] + ww * 0.42 + lean * 0.3, base[1] - 5.0 * sc), (base[0] + ww * 0.3 + lean * 0.3, base[1] - 4.8 * sc)],
               lerp(snow_c, INK, 0.3), 0.75)
        K.ellipse(c, (base[0] + ww * 0.25, base[1]), ww * 0.85, max(2.0, 0.07 * sc), lerp(snow_c, PAPER, 0.25))


def _search_woods(c, cam, sp, snow_c, trees):
    """The searchlight's patch on the woods' snow: PAPER over the moon's shadows, the trunks' long
    shadows cut out of it (they point away from the tower, to the right, and slide as the patch
    moves)."""
    uc, dc, ru, rd, a = sp
    if a <= 0.01:
        return
    outer = _ground_ring(cam, uc, dc, ru * 1.22, rd * 1.22, 0.0, 56)
    inner = _ground_ring(cam, uc, dc, ru, rd, 0.0, 56)
    K.poly(c, outer, PAPER, 0.5 * a)
    K.poly(c, inner, PAPER, 0.92 * a)
    c.save()
    c.new_path()
    D.poly(c, outer)
    c.clip()
    shade = lerp(snow_c, SHADOW, 0.2)
    for (u, d, h, i) in trees:
        if d > 30.0:
            continue
        # does its shadow reach the patch? (it runs to the right, ~16 m)
        if u > uc + ru * 1.3 or u < uc - ru * 1.3 - 9.0 or abs(d - dc) > rd * 1.3 + 0.8:
            continue
        du, dd = tower_dir(u, d)
        w = 0.28 + 0.12 * hash01(i, 4)
        L = 16.0
        px_, pd_ = -dd, du
        q = [cam.px(u + px_ * w * 0.5, 0.0, d + pd_ * w * 0.5), cam.px(u - px_ * w * 0.5, 0.0, d - pd_ * w * 0.5),
             cam.px(u + du * L - px_ * w * 0.9, 0.0, d + dd * L - pd_ * w * 0.9),
             cam.px(u + du * L + px_ * w * 0.9, 0.0, d + dd * L + pd_ * w * 0.9)]
        K.poly(c, q, shade, 0.95)
    for (u, d, w, i) in fg_trunks():
        if u > uc + ru * 1.3 or u < uc - ru * 1.3 - 16.0:
            continue
        du, dd = tower_dir(u, d)
        px_, pd_ = -dd, du
        L = 16.0
        q = [cam.px(u + px_ * w * 0.5, 0.0, d + pd_ * w * 0.5), cam.px(u - px_ * w * 0.5, 0.0, d - pd_ * w * 0.5),
             cam.px(u + du * L - px_ * w * 0.9, 0.0, d + dd * L - pd_ * w * 0.9),
             cam.px(u + du * L + px_ * w * 0.9, 0.0, d + dd * L + pd_ * w * 0.9)]
        K.poly(c, q, shade, 0.95)
    c.restore()


def _search_beam(c, cam, sp, beam):
    """The searchlight's beam in the air, from the upper left down to its patch (over the trunks:
    light hanging between them)."""
    uc, dc, ru, rd, a = sp
    apex, ba = beam
    if a * ba <= 0.01:
        return
    outer = _ground_ring(cam, uc, dc, ru * 1.1, rd * 1.1, 0.0, 40)
    # the two tangent points seen from the apex: the extreme angles
    ang = [math.atan2(p[1] - apex[1], p[0] - apex[0]) for p in outer]
    i0 = min(range(len(ang)), key=lambda k: ang[k])
    i1 = max(range(len(ang)), key=lambda k: ang[k])
    K.beam(c, apex, outer[i0], outer[i1], PAPER, alpha=0.16 * ba * a, steps=3)


def _far_lamp(c, cam, u, d, s, t):
    """A far lantern among the trees: a small warm glow and its flame (the other guards)."""
    p = cam.px(u, 1.0, d)
    sc = cam.scale(d)
    K.glow(c, p, max(6.0, 1.6 * sc), 0.9 * s, t, seed=int(d))
    K.dot(c, p, max(1.5, 0.07 * sc), lerp(AMBER, PAPER, 0.5), seed=int(u * 3) % 50, alpha=s)


def prints_side(c, cam, prints, page=SNOW, depth_of=None, z=0.0, alpha=1.0):
    """Footprints seen on the snow in a diorama (each outline laid on the ground plane):
    depth_of(x, n) -> d (default: the woods' path mapping)."""
    depth_of = depth_of or wd
    u_l, u_r = cam.u_at(-200.0), cam.u_at(1280.0)
    groups = {}
    for (x, n, hdg, kind, side, depth) in prints:
        if not (u_l - 1.0 <= n <= u_r + 1.0):
            continue
        col = lerp(SHADOW, THIN, 0.3 * depth)
        sc = 1.0 + 0.22 * depth
        L = K._PRINT[kind][0] * sc
        hx = x - math.sin(math.radians(hdg)) * L / 2.0
        hn = n - math.cos(math.radians(hdg)) * L / 2.0
        pts = [cam.px(pn, z, depth_of(px_, pn)) for px_, pn in K.print_world(kind, side, (hx, hn), hdg, sc)]
        groups.setdefault(col, []).append(pts)
    for col, ps in groups.items():
        K.polys(c, ps, col, alpha)


# ============================================================================ the river view's extras
def river_d(x):
    """A map point's depth behind the river view's cut (x = 13.2)."""
    return W.SECTION_X - x


@lru_cache(maxsize=1)
def edge_trees():
    """The woods' edge seen from the river view: the trees south of the bank that stand behind
    the cut (u = n, d = 13.2 - x, height, seed), far first."""
    out = []
    for (x, n, r, h, seed) in W.woods():
        d = W.SECTION_X - x
        if n < -60.0 or n > -5.0 or d < 0.6 or d > 70.0:
            continue
        out.append((n, d, h, seed))
    # a few more along the edge, near the path's mouth (the woods thin out to the bank)
    for i in range(14):
        n = -6.4 - 2.6 * i - 1.2 * hash01(i, 801)
        d = 0.9 + 9.0 * hash01(i, 802)
        if -9.0 < n < -5.0 and d < 2.5:
            d += 2.5
        out.append((n, d, 9.0 + 6.0 * hash01(i, 803), 8800 + i))
    return tuple(sorted(out, key=lambda r: -r[1]))


def river_woods(c, cam, t, moonlit=1.0, upto_d=None, from_d=None, shadows=True):
    """The woods' edge on the near bank in the river view (call after W.draw_river with
    reeds_on=False, trunk=False, then reeds() and W.draw_trunk_side). from_d / upto_d: only the
    trunks at least / at most that deep (a figure among the trees goes between two passes);
    shadows: the trees' moon shadows on the snow (draw them once, in the deep pass)."""
    hy = cam.horizon_y()
    snow_c = lerp(K.SNOW_DIM, SNOW, moonlit)
    shade_c = lerp(snow_c, SHADOW, 0.55)
    trees = edge_trees()

    def keep(d):
        return (upto_d is None or d <= upto_d) and (from_d is None or d >= from_d)

    for (u, d, h, i) in trees:
        base = cam.px(u, 0.0, d)
        sc = cam.scale(d)
        if base[0] < -300 or base[0] > 1380 or base[1] < hy - 4:
            continue
        if d > 22.0:
            if keep(d):
                W.spruce_side(c, base, h * sc, h * 0.4 * sc, lerp(lerp(STEEL, INK, 0.5), STEEL, clamp(d / 70.0)), seed=i)
            continue
        if not shadows:
            continue
        L = h * W.SHADOW_K * 0.55
        w = (0.28 + 0.12 * hash01(i, 4))
        K.poly(c, [cam.px(u - 0.1, 0.0, d - w * 0.5), cam.px(u + 0.1, 0.0, d + w * 0.5), cam.px(u - L, 0.0, d + 0.6),
                   cam.px(u - L, 0.0, d - 0.6)], shade_c, 0.8)
    for (u, d, h, i) in trees:
        if d > 22.0 or not keep(d):
            continue
        base = cam.px(u, 0.0, d)
        if base[0] < -200 or base[0] > 1280 or base[1] < hy - 4:
            continue
        _trunk(c, cam, u, d, h, i, snow_c)


def reeds(c, cam, moonlit=1.0, near=None, far=None):
    """The reeds behind the cut on the south bank (world's own), optionally only those nearer
    than `near` m or farther than `far` m (so a figure can hide among them)."""
    for (n, d, h, i) in W._reed_side_list():
        if near is not None and d >= near:
            continue
        if far is not None and d < far:
            continue
        base = cam.px(n, W.land_z(n), d)
        sc = cam.scale(d)
        top = (base[0] + 0.12 * sc * K._sn(i, 4), base[1] - h * sc)
        col = lerp(INK, STEEL, 0.15 * clamp(d / 10.0))
        K.band(c, [base, top], col, max(1.2, 0.035 * sc), seed=i, taper=(1.0, 0.3))
        if i % 3 == 0:
            K.ellipse(c, (top[0], top[1] + 0.08 * sc), max(1.0, 0.035 * sc), max(2.0, 0.12 * sc), col)


def river(c, cam, t, holes=(), search=None, woods_on=True, reeds_far=None, moonlit=1.0, split_d=None, between=None,
          **kw):
    """The river view with the woods' edge on the near bank: W.draw_river, then the edge's trunks,
    the reeds (those deeper than reeds_far; the nearer ones are drawn by the scene over its
    figures) and the fallen trunk. split_d / between(c): the trunks deeper than split_d, then
    between(c) (a figure among the trees), then the nearer trunks."""
    W.draw_river(c, cam, t, holes=holes, search=search, reeds_on=False, trunk=False, moonlit=moonlit, **kw)
    if woods_on:
        if split_d is None:
            river_woods(c, cam, t, moonlit)
        else:
            river_woods(c, cam, t, moonlit, from_d=split_d)
            if between is not None:
                between(c)
            river_woods(c, cam, t, moonlit, upto_d=split_d - 1e-6, shadows=False)
    elif between is not None:
        between(c)
    reeds(c, cam, moonlit, far=reeds_far)
    W.draw_trunk_side(c, cam)


# ============================================================================ figures
WALKERS = {}


def walker(who, speed, step, duty=0.62, lift=0.1, t0=-3.0, t1=20.0, key=None):
    """A planted-feet walker for `who`: speed [(t, m/s), ...], `step` m per step, foot lift m.
    Cached by key (or by its arguments)."""
    key = key or (who, tuple(speed), step, duty, lift, t0, t1)
    if key not in WALKERS:
        m = C.M_PER_UNIT[who]
        stride = 2.0 * step / m
        vt = max(v for _, v in speed) / m
        WALKERS[key] = pd.Walker(C.fig(who), x0=0.0, speed=[(t, v / m) for t, v in speed], t0=t0, t1=t1,
                                 walk=(stride, duty, lift / m), run=(stride * 1.6, 0.38, lift / m * 1.4),
                                 v_walk=max(vt * 0.8, 1.0), v_run=max(vt * 30.0, 2.0))
    return WALKERS[key]


def draw_fig(c, cam, who, st, pose, u, z, d, facing=1, sx=1.0, rim=PAPER, edge=SNOW, snow_line=None, under=None,
             lift=0.0, rim_w=None, parts=None):
    """Draw `who` through a diorama camera, root at (u, z, d), turned by sx (paper turn: -1..1, the
    figure facing +x scaled about its root; facing gives its direction when sx is 1). snow_line: a
    frame y below which the figure is hidden (wading in deep snow). parts: which of C.PARTS to draw
    (a limb laid over another figure is drawn in a second pass). Returns joints in frame px."""
    s = C.scale(who, cam.scale(d))
    at = cam.px(u, z, d)
    at = (at[0], at[1] - lift)
    k = abs(sx) if abs(sx) > 0.04 else 0.04
    f = facing * (1 if sx >= 0 else -1)
    c.save()
    if snow_line is not None:
        c.new_path()
        c.rectangle(-200.0, -200.0, 1480.0, snow_line + 200.0)
        c.clip()
    c.translate(at[0], 0.0)
    c.scale(k, 1.0)
    c.translate(-at[0], 0.0)
    j = C.draw(c, who, st, pose, at, s, f, rim=rim, edge=edge, light=(LIGHT[0] * (1 if k > 0 else -1) / max(k, 0.3),
                                                                       LIGHT[1]), under=under, rim_w=rim_w,
               parts=C.PARTS if parts is None else parts)
    dev = {kk_: c.user_to_device(*v) for kk_, v in j.items() if isinstance(v, tuple)}
    c.restore()
    out = {kk_: c.device_to_user(*v) for kk_, v in dev.items()}
    out["scale"] = s
    out["at"] = at
    return out


def breath(c, j, who, t, rate=0.5, pant=None, strength=1.0, facing=1, phase=0.0, seed=0):
    """Breath from a figure's mouth (joints j)."""
    if "mouth" not in j:
        return
    s = C.HEIGHT_M[who] / C.M_PER_UNIT[who] * j["scale"] / 600.0
    K.breath(c, j["mouth"], t, rate=rate, facing=facing, s=s, phase=phase, strength=strength, pant=pant, seed=seed)


def swing(t, amp=6.0, rate=6.0):
    return amp * math.sin(t * rate)


def stand_state(who, x=0.0, spread=16.0, step=0.0, pitch_back=0.0):
    """A standing state (feet planted, pelvis at rest) with the near foot `step` units ahead of the
    far one (a stance), the back foot's toe pitched down `pitch_back` degrees."""
    st = pd.standing(C.fig(who), x, spread)
    n, f = st["feet"]["near"], st["feet"]["far"]
    st["feet"] = {"near": (n[0] + step * 0.5, n[1], n[2]), "far": (f[0] - step * 0.5, f[1], -pitch_back)}
    return st


def step_times(wk, t0, t1):
    """[(t, side, foot x units)] of a walker's footfalls between t0 and t1 (the moment each sole
    plants)."""
    out = []
    for side, ev in wk.plants.items():
        for i, fx in ev[1:]:
            t = wk.t0 + i / pd.HZ
            if t0 <= t <= t1:
                out.append((t, side, fx))
    return sorted(out)


def wade_lip(c, cam, j, u, d, snow_c=SNOW, seed=0, h=0.075, pad=0.15, xs=None):
    """The snow heaped round a wading figure's legs where they go in (hides the clip's straight
    edge): a low lump of snow at the surface line across the legs, its top edge moonlit."""
    y0 = cam.px(u, 0.0, d)[1]
    sc = cam.scale(d)
    if xs is None:
        xs = [j[k][0] for k in ("knee_near", "knee_far", "ankle_near", "ankle_far", "pelvis") if k in j]
    if not xs:
        return
    x0, x1 = min(xs) - pad * sc, max(xs) + pad * sc
    n = 16
    top = []
    for i in range(n + 1):
        x = lerp(x0, x1, i / n)
        e = math.sin(math.pi * i / n) ** 0.55
        top.append((x, y0 - h * sc * e * (0.7 + 0.6 * hash01(seed, i, int(x0) // 40))))
    K.poly(c, top + [(x1, y0 + 4.0), (x0, y0 + 4.0)], snow_c)
    K.band(c, top[3:-3], lerp(snow_c, PAPER, 0.55), max(1.2, 0.014 * sc), seed=seed)


def puff(c, p, t, t0, ppm, n=16, seed=0, color=SNOW, life=0.8, spread=1.0, power=1.0):
    """Powder snow thrown up at p (frame px) at t0: lumps flying up and out, falling back,
    fading. ppm: px per metre there."""
    a = (t - t0) / life
    if not 0.0 <= a < 1.0:
        return
    tt = a * life
    for i in range(n):
        ang = math.radians(-90.0 + 75.0 * spread * K._sn(seed, i, 1))
        v = (0.7 + 1.3 * hash01(seed, i, 2)) * power
        x = p[0] + math.cos(ang) * v * tt * ppm
        y = p[1] + (math.sin(ang) * v * tt + 1.6 * tt * tt) * ppm
        r = ppm * (0.025 + 0.05 * hash01(seed, i, 3)) * (1.0 - 0.4 * a)
        K.dot(c, (x, y), r, color if i % 3 else PAPER, seed=seed * 31 + i, alpha=0.95 * (1.0 - a) ** 1.3)


def turn_group(c, at_x, sx):
    """Enter a paper turn about frame x at_x (use with c.save()/c.restore()): x scaled by |sx|."""
    k = max(abs(sx), 0.04)
    c.translate(at_x, 0.0)
    c.scale(k, 1.0)
    c.translate(-at_x, 0.0)
    return k


def to_frame(c, j):
    """Joints drawn inside a transform, as frame px (call while the transform is current)."""
    return {k: c.user_to_device(*v) for k, v in j.items() if isinstance(v, tuple) and len(v) == 2}


def from_device(c, dev):
    return {k: c.device_to_user(*v) for k, v in dev.items()}


def mirror_state(st):
    """A walker's state mirrored in x (it walks the other way: draw it with facing -1)."""
    out = dict(st)
    out["pelvis"] = (-st["pelvis"][0], st["pelvis"][1])
    out["feet"] = {k: (-v[0], v[1], v[2]) for k, v in st["feet"].items()}
    return out


def piggyback(c, st, pose, at, s, facing=1, t=0.0, rim=None, rim_w=None, light=(0.8, -0.6), edge=None, look=0.0,
              girl_pose=None, shift_root=True):
    """cast.piggyback, right for both facings: cast's leaves the girl's carried state unmirrored,
    so facing -1 sticks her legs out behind her mother instead of round her waist (states are in
    world x; only the body turns with facing). st: the mother's state in world x (mirror_state for
    a walker going left). Returns (mother joints, girl joints)."""
    rim_w = clamp(4.0 * s, 1.5, 3.5) if rim_w is None else rim_w
    q = st.get("phase", 0.0) % 1.0
    bounce = math.sin(4.0 * math.pi * q) * clamp(st.get("speed", 0.0) / 300.0)
    gp = C.frame_point("mother", st, pose, C.SEAT, at, s, facing, shift_root)
    sg = s * C.M_PER_UNIT["girl"] / C.M_PER_UNIT["mother"]
    gst = C.carried_state()
    if facing < 0:
        gst = mirror_state(gst)
    gpose = girl_pose or C.carried_pose(t, look, bounce=bounce)
    gpose = pd.Pose(lean=gpose.lean + pose.lean, head=gpose.head, crouch=gpose.crouch, arms=gpose.arms, hold=gpose.hold,
                    springs=gpose.springs, eye=gpose.eye, gaze=gpose.gaze)
    g_at = (gp[0], gp[1] - gst["pelvis"][1] * sg + 6.0 * bounce * sg)
    kw = dict(rim=rim, rim_w=rim_w, light=light, shift_root=False)
    girl = C.draw(c, "girl", gst, gpose, g_at, sg, facing, parts=("far_arm", "far_leg", "body"), **kw)
    seat = C.frame_point("girl", gst, gpose, (22.0, -18.0), g_at, sg, facing, False)
    if rim is not None:
        K.ellipse(c, (seat[0] + light[0] * rim_w, seat[1] + light[1] * rim_w), 80.0 * sg, 66.0 * sg, rim,
                  angle=gpose.lean * facing)
    K.ellipse(c, seat, 80.0 * sg, 66.0 * sg, INK, angle=gpose.lean * facing)
    mother = C.draw(c, "mother", st, pose, at, s, facing, edge=edge, shift_root=shift_root, rim=rim, rim_w=rim_w,
                    light=light)
    C.draw(c, "girl", gst, gpose, g_at, sg, facing, parts=("near_leg", "near_arm"), edge=edge or SNOW, shift_root=False)
    mother["scale"] = s
    girl["scale"] = sg
    return mother, girl


def girl_off_back(k, cam, t, mother, land, end, facing=1, end_crouch=0.0, end_head=3.0):
    """The girl getting down off her mother's back, k 0..1: she slides down to a crouch behind
    her mother's heels (the first 45%), then steps to where she ends (two steps).
    mother: (st, pose, at px, s px/unit, u, d) as the piggyback was drawn; land: (u, d) where she
    lands; end: (u, d) where she ends, end_crouch m lower than standing. Returns (state, pose,
    root px, scale) for C.draw(..., facing, shift_root=False)."""
    st_m, pose_m, at_m, s_m, u_m, d_m = mother
    Fg = C.fig("girl")
    mg = C.M_PER_UNIT["girl"]
    sg_c = s_m * mg / C.M_PER_UNIT["mother"]
    gst = C.carried_state()
    seat = C.frame_point("mother", st_m, pose_m, C.SEAT, at_m, s_m, facing)
    root_c = (seat[0], seat[1] - gst["pelvis"][1] * sg_c)
    ka = ease("inout", clamp(k / 0.45))
    kb = ease("inout", clamp((k - 0.45) / 0.55))
    z_stand = Fg.leg * 0.965 * mg
    (u_l, d_l), (u_e, d_e) = land, end
    u_p = lerp(lerp(u_m - 0.1 * facing, u_l, ka), u_e, kb)
    z_p = lerp(lerp(0.94, z_stand - 0.1, ka), z_stand - end_crouch, kb)
    d_p = lerp(lerp(d_m, d_l, ka), d_e, kb)
    w = ease("inout", clamp(k / 0.3))
    path = cam.px(u_p, z_p, d_p)
    pel = (lerp(seat[0], path[0], w), lerp(seat[1], path[1], w))
    s = lerp(sg_c, C.scale("girl", cam.scale(d_p)), w)
    fb = ease("inout", clamp(k / 0.42))
    steps = {"far": (0.5, 0.72, -0.05), "near": (0.7, 0.92, 0.05)}
    land_off = {"near": 0.05, "far": -0.03}
    feet = {}
    for side in ("near", "far"):
        fc = gst["feet"][side]
        p0 = (root_c[0] + fc[0] * facing * sg_c, root_c[1] + fc[1] * sg_c)
        a0, a1, off = steps[side]
        ks = ease("inout", clamp((k - a0) / (a1 - a0)))
        uf = lerp(u_l + land_off[side] * facing, u_e + off * facing, ks)
        p1 = cam.px(uf, 0.05 * bump(k, a0, a1), d_p)
        p = (lerp(p0[0], p1[0], fb), lerp(p0[1], p1[1], fb))
        # feet in the girl's figure units (x not mirrored by facing)
        feet[side] = ((p[0] - pel[0]) / s, (p[1] - pel[1]) / s, lerp(fc[2], 0.0, fb))
    st = dict(pelvis=(0.0, 0.0), feet=feet, phase=0.0, speed=0.0, run=0.0, stride=0.0, skirt=k > 0.6)
    a2 = ease("inout", clamp((k - 0.05) / 0.45))
    cp = C.carried_pose(t, 0.2)
    arms = {}
    for side, hang in (("near", (20.0, -40.0)), ("far", (14.0, -42.0))):
        r0 = cp.arms[side][1]
        arms[side] = ("rel", (lerp(r0[0], hang[0], a2), lerp(r0[1], hang[1], a2)))
    lean = lerp(lerp(cp.lean + pose_m.lean, 10.0, ka), 2.0 + 10.0 * clamp(end_crouch / 0.2), kb)
    head = lerp(lerp(0.2, -4.0, ka), end_head, kb)
    pose = pd.Pose(lean=lean, head=head, crouch=0.0, arms=arms,
                   springs=dict(C.REST, scarf=C.REST["scarf"] + lerp(28.0, 4.0, ka)))
    return st, pose, pel, s


# ============================================================================ the record of footprints
def land_times(prints, pos_of_t, t0, t1, lead=0.3, along=lambda p: p[1], dt=1.0 / 48.0):
    """When each print is laid: the first time the walker's position along its route (pos_of_t)
    passes the print's position along it (along(print)) less `lead` m. Prints behind the start
    are already there (-inf); prints never reached, never (inf)."""
    out = []
    ts = []
    t = t0
    while t <= t1 + 1e-9:
        ts.append((t, pos_of_t(t)))
        t += dt
    for p in prints:
        a = along(p) - lead
        if ts[0][1] >= a:
            out.append(-1e9)
            continue
        hit = 1e9
        for (ta, pa), (tb, pb) in zip(ts, ts[1:]):
            if pa < a <= pb:
                hit = ta + (tb - ta) * (a - pa) / max(pb - pa, 1e-9)
                break
        out.append(hit)
    return tuple(out)


def guard_woods_until(n):
    """The guard's woods prints as far north as n (he has walked that far)."""
    return tuple(p for p in W.GUARD_WOODS if p[1] <= n)


def prints_upto(sid, guard_n=None):
    """prints_before(sid), less the guard's woods prints north of guard_n (where his lantern is):
    s05 and s06 happen while he is still in the trees."""
    base = W.prints_before(sid)
    if guard_n is None:
        return base
    gw = set(W.GUARD_WOODS)
    return tuple(p for p in base if p not in gw or p[1] <= guard_n)


# ============================================================================ the guard's clock, the light's
# The guard comes on through the woods at a steady pace from the end of s04 (film 64) until he
# breaks out of the trees in s07 (film 94): s05 and s06 place his lantern by this clock.
GUARD_V = 1.2                 # m/s along the path
GUARD_N64 = -41.3             # where he is at film 64 (s04's last frame)


def guard_n_film(ft):
    """The guard's map n at film time ft (s05, s06, s07's start)."""
    return GUARD_N64 + GUARD_V * (ft - 64.0)


def guard_x(n):
    """His line through the woods: 0.55 m west of the path (W.GUARD_WOODS)."""
    return path_x(n) - 0.55


# The searchlight sweeps the white ice at the crossing, upstream (x = W.CROSSING_X): one swing
# across the river and back every SEARCH_P seconds (film time); it crosses mid-river, going
# south, at film 73.5 (s05's wide page).
SEARCH_P = 7.0
SEARCH_T0 = 70.0


def search_cross(ft):
    """(x, n) of the searchlight's patch at the crossing at film time ft."""
    a = 2.0 * math.pi * (ft - SEARCH_T0) / SEARCH_P
    return (W.CROSSING_X + 1.2 * math.sin(a * 0.5), 12.5 + 15.0 * math.sin(a))


def search_heading(x, n):
    """Map heading (degrees from north) from the tower to (x, n)."""
    return math.degrees(math.atan2(x - W.TOWER[0], n - W.TOWER[1]))


RIVER_D_MIN = 0.4             # figures standing in front of the river's cut are drawn just behind it


def rd(x):
    """A figure's depth in the river view (clamped just behind the cut)."""
    return max(RIVER_D_MIN, W.SECTION_X - x)


def ice_xf(cam, centre_u, d0, z=None):
    """A function mapping metres on the ice around (u, d0) (x along u, y along d) to frame px."""
    zz = W.ICE_Z if z is None else z

    def f(p):
        return cam.px(centre_u + p[0], zz, d0 + p[1])
    return f


# ============================================================================ the trail in the river view
# The false trail lies on the river view's cut (x = 13.2): her right foot's prints (x 13.3) are a
# hand's breadth in front of it, so the cut shows each of them as a boot-shaped hollow in its
# snow; the left foot's (x 13.1) lie just behind it, hidden by the cut's snow.
BOOT_L = 0.30                     # her felt boot's length (m): faces.boot's sole spans 264 units
BOOT_M = BOOT_L / 264.0           # metres per boot unit
BOOT_MID = 48.0                   # the sole's middle, boot units from faces.boot's origin
PRINT_SINK = 0.035                # how deep her boot sinks into the snow on the ice (m)
SNOW_TOP = W.ICE_Z + W.SNOW_T     # the snow's surface on the white ice (z)


def _clip_below(poly, y_min):
    """The part of a polygon with y >= y_min (Sutherland-Hodgman)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = a[1] >= y_min, b[1] >= y_min
        if ina:
            out.append(a)
        if ina != inb:
            u = (y_min - a[1]) / (b[1] - a[1])
            out.append((a[0] + (b[0] - a[0]) * u, y_min))
    return out


@lru_cache(maxsize=None)
def sole_notch(who="mother", depth_units=31.0):
    """The bottom of faces.boot's own outline (boot units, y up negative), the `depth_units`
    nearest the sole: the hollow her boot leaves in the snow, seen in section. A boot lowered into
    it fills it exactly."""
    return tuple(_clip_below(list(F._poly(F._BOOT[who], 951 + len(who))), -depth_units))


def notch_pts(cam, n_mid, z_top=SNOW_TOP, sink=PRINT_SINK, slope=0.0, who="mother"):
    """A print's hollow in the cut (frame px): the sole's shape, toe toward +u, its middle at
    n_mid, its sole `sink` m under the surface z_top; slope: the surface's angle (radians)."""
    ca, sa = math.cos(slope), math.sin(slope)
    out = []
    for x, y in sole_notch(who, round(sink / BOOT_M, 3)):
        a = (x - BOOT_MID) * BOOT_M               # along the surface
        h = -y * BOOT_M - sink                     # up from the surface
        out.append(cam.px(n_mid + a * ca - h * sa, z_top + a * sa + h * ca, 0.0))
    return out


def trail_notches(c, cam, prints=W.FALSE_TRAIL, skip=()):
    """The trail seen in the cut: each right-foot print a boot-shaped hollow in the cut's snow
    (SHADOW on the ice's snow; darker in the land's shaded snow)."""
    u_l, u_r = cam.u_at(-120.0), cam.u_at(1200.0)
    for i, (x, n, hdg, kind, side, depth) in enumerate(prints):
        if side != 1 or i in skip or not (u_l <= n <= u_r):
            continue
        if n > W.RIVER[0] + 0.02:
            K.poly(c, notch_pts(cam, n), SHADOW)
        else:
            dz = W.land_z(n + 0.05) - W.land_z(n - 0.05)
            K.poly(c, notch_pts(cam, n, W.land_z(n), slope=math.atan2(dz, 0.1)), lerp(SHADOW, INK, 0.35))


# ============================================================================ figures on the page
def top_shadow(c, who, p, ppm, phase=0.0, speed=0.0, carry=False, crouch=0.0, shadow_dir=90.0, shade=SHADOW,
               alpha=1.0):
    """cast.top's moon shadow alone (so boots can stand on the snow between it and the figure)."""
    big = {"mother": 1.0, "girl": 0.7, "guard": 1.18}[who]
    sw = math.sin(2.0 * math.pi * phase) * speed
    Ls = C.HEIGHT_M[who] * (1.0 - 0.45 * crouch) * C.K_SHADOW
    legs = 0.47 * Ls
    sh = []
    for side in (-1, 1):
        off = 0.07 * big * side
        stride = 0.05 * sw * side
        sh.append([(stride, off - 0.035), (legs, off * 1.25 - 0.04), (legs, off * 1.25 + 0.04), (stride, off + 0.035)])
    sh.append([(legs * 0.92, -0.17 * big), (Ls * 0.83, -0.22 * big), (Ls * 0.88, -0.12 * big), (Ls * 0.88, 0.12 * big),
               (Ls * 0.83, 0.22 * big), (legs * 0.92, 0.17 * big)])
    hr = (0.13 if who == "guard" else 0.1) * big
    sh.append(C._ell_m(Ls * 0.88 + hr * 1.3, 0.0, hr * 1.4, hr))
    if carry:
        sh.append(C._ell_m(Ls * 0.97 + 0.08, 0.13, 0.1, 0.08))
    K.polys(c, [C._xf(q, p, shadow_dir, ppm) for q in sh], shade, alpha)


def top_boot(c, cam, x, n, hdg, side, lift=0.0, who="mother", color=INK):
    """A boot from above on the page (a print's shape, a shade smaller than the print it makes):
    map (x, n) its middle, heading hdg (degrees from north)."""
    sc = 0.95 * (1.0 + 0.06 * lift)
    Lb = K._PRINT[who][0] * sc
    heel = (x - math.sin(math.radians(hdg)) * Lb / 2.0, n - math.cos(math.radians(hdg)) * Lb / 2.0)
    K.poly(c, cam.pts(K.print_world(who, side, heel, hdg, sc)), color)


def print_poly(cam, pr):
    """A print record's outline in frame px (as world.draw_prints draws it)."""
    x, n, hdg, kind, side, depth = pr
    sc = 1.0 + 0.22 * depth
    Lp = K._PRINT[kind][0] * sc
    heel = (x - math.sin(math.radians(hdg)) * Lp / 2.0, n - math.cos(math.radians(hdg)) * Lp / 2.0)
    return cam.pts(K.print_world(kind, side, heel, hdg, sc))


def print_flash(c, cam, pr, t, t0, life=0.3):
    """The step pulse's flash: the print lights up as a foot lands in it (draw it under the boot:
    its rim shows round the sole), fading over `life`."""
    a = (t - t0) / life
    if 0.0 <= a < 1.0:
        K.poly(c, print_poly(cam, pr), PAPER, 0.9 * (1.0 - a) ** 1.5)


def print_ring(c, cam, pr, t, t0, life=0.5):
    """The step pulse's ring out of a print (draw it over the figure)."""
    K.step_pulse(c, cam.px((pr[0], pr[1])), t, t0, PAPER, r0=0.16 * cam.ppm, r1=0.62 * cam.ppm, life=life,
                 width=max(2.0, 0.035 * cam.ppm), seed=int(pr[1] * 10) % 97)


def guard_top_clock(c, cam, ft, tt, pool=True):
    """The guard on the page at his clock (film time ft): on his line through the woods, heading
    north along it, his lantern's pool on the snow ahead of him."""
    gn = guard_n_film(ft)
    gx = guard_x(gn)
    hdg = math.degrees(math.atan2(guard_x(gn + 1.0) - gx, 1.0))
    if pool:
        ahead = (gx + 0.5 * math.sin(math.radians(hdg)), gn + 0.5 * math.cos(math.radians(hdg)))
        W.lamp_pool(c, cam, ahead, 1.9, 1.15, tt, seed=5)
    C.top(c, "guard", cam.px((gx, gn)), cam.screen_heading(hdg), cam.ppm, tt, phase=(tt * GUARD_V / 1.52) % 1.0,
          speed=1.0, lantern=1.0)
    return gx, gn


# The two of them hidden in the reeds, from above, as s08 draws them (the director's reed_eyes):
# the mother 0.3 m west of the hiding place, the girl 0.3 m east; two dark shapes under the reed
# tufts; two pairs of PAPER eyes (hers wider, the girl's rounder).
REED_PAIR = ((-0.3, 0.05, 0.36, 26.0, 12.0, 40.0), (0.3, -0.06, 0.28, 22.0, 17.0, 36.0))


def reed_eyes(c, cam, t, look=(0.0, -0.6), lid=1.0, blink=None, size=1.0, look_girl=None):
    """Two pairs of eyes in the reeds at W.HIDE. look: the pupils' offset (x right, y down);
    lid 0..1; blink: a time (a 0.18 s blink)."""
    k = size * max(1.0, cam.ppm / 110.0)
    for (dx, dn, r, w, h, gap) in REED_PAIR:
        cx, cy = cam.px((W.HIDE[0] + dx, W.HIDE[1] + dn))
        pts = [(cx + r * cam.ppm * (1.0 + 0.12 * K._sn(i, 531)) * math.cos(6.283 * i / 18),
                cy + r * cam.ppm * 0.8 * (1.0 + 0.12 * K._sn(i, 532)) * math.sin(6.283 * i / 18)) for i in range(18)]
        K.poly(c, pts, INK)
    W.draw_reeds(c, cam, (W.HIDE[0] - 0.9, W.HIDE[0] + 0.9, W.HIDE[1] - 0.7, W.HIDE[1] + 0.7))
    lid_ = lid
    if blink is not None and blink <= t < blink + 0.18:
        lid_ *= abs(math.cos(math.pi * (t - blink) / 0.18))
    for j, (dx, dn, r, w, h, gap) in enumerate(REED_PAIR):
        lk = look if (j == 0 or look_girl is None) else look_girl
        cx, cy = cam.px((W.HIDE[0] + dx, W.HIDE[1] + dn))
        for side in (-1, 1):
            x = cx + side * gap * 0.5 * k
            hh = h * k * lid_
            if hh < 1.5:
                continue
            K.ellipse(c, (x, cy), w * k * 0.5, hh * 0.5, PAPER)
            K.ellipse(c, (x + lk[0] * w * 0.2 * k, cy + lk[1] * hh * 0.22), h * 0.3 * k, min(hh, h * k) * 0.3, INK)


# ============================================================================ the hiding place in the profile
# The river view can't see the true hiding place (W.HIDE is 5.7 m behind the cut, deep in the
# reed bed), so the profile shots cheat it forward: the two of them crouch just right of the root
# plate, behind the trunk's end, among reeds of their own (s06's bank, s07's rise).
HIDE_U, HIDE_D = -1.25, 2.0         # the mother, in the profile
GIRL_U, GIRL_D = -0.88, 1.8         # the girl


@lru_cache(maxsize=1)
def hide_reeds():
    """Reeds round the hiding place in the profile (u, d, height, seed), far first: most behind the
    two of them, a few in front (clear of their faces)."""
    out = []
    for i in range(22):
        u = -2.0 + 1.75 * hash01(i, 901)
        d = 2.1 + 0.7 * hash01(i, 902)
        out.append((u, d, 0.8 + 0.7 * hash01(i, 903), 900 + i))
    for j, (u, d, h) in enumerate(((-1.95, 1.5, 1.15), (-1.66, 1.62, 1.0), (-1.5, 1.78, 0.78), (-1.06, 1.56, 0.92),
                                   (-0.62, 1.66, 1.08), (-0.42, 1.5, 0.86))):
        out.append((u, d, h, 940 + j))
    return tuple(sorted(out, key=lambda r: -r[1]))


def reeds_rows(c, cam, rows, rim=False, t=None):
    """Draw reed rows (u, d, height, seed) in a diorama camera; rim: their moonlit edges. t: they
    stir (a reed brushed as someone moves among them) -- None: still."""
    for (u, d, h, i) in rows:
        base = cam.px(u, W.land_z(u), d)
        sc = cam.scale(d)
        lean = 0.1 * K._sn(i, 4) + 0.03 * math.sin(1.3 * u + 0.7)
        if t is not None:
            lean += 0.025 * math.sin(2.1 * t + i)
        top = (base[0] + lean * sc, base[1] - h * sc)
        w = max(1.4, 0.03 * sc)
        if rim:
            rw = max(1.5, 0.006 * sc)
            K.band(c, [(base[0] + LIGHT[0] * rw, base[1]), (top[0] + LIGHT[0] * rw, top[1] + LIGHT[1] * rw)],
                   PAPER, w, seed=i, taper=(1.0, 0.3), alpha=0.8)
        K.band(c, [base, top], INK, w, seed=i, taper=(1.0, 0.3))
        if i % 3 == 0:
            hd = (top[0] - 0.01 * sc, top[1] + 0.07 * sc)
            if rim:
                K.ellipse(c, (hd[0] + LIGHT[0] * 2.0, hd[1] + LIGHT[1] * 2.0), max(1.2, 0.03 * sc), max(2.0, 0.1 * sc),
                          PAPER, alpha=0.8)
            K.ellipse(c, hd, max(1.2, 0.03 * sc), max(2.0, 0.1 * sc), INK)


# ============================================================================ the heartbeat ring
def heart_rings(c, p, t, t0, t1, bpm=104.0, alpha=0.32, r0=46.0, r1=700.0, width=9.0, life=1.3, seed=0):
    """Her heart (the bible's device for fear): PAPER rings thudding out of p, lub-dub, the first
    beat at t0, none born after t1 (the s09 look: s09's heart())."""
    beat = 60.0 / bpm
    k0 = int(math.floor((t - t0 - life) / beat)) - 1
    for k in range(max(0, k0), int(math.floor((t - t0) / beat)) + 1):
        for j, off in enumerate((0.0, 0.24)):
            tb = t0 + k * beat + off
            if tb > t1 or tb > t:
                continue
            a = (t - tb) / life
            if not 0.0 <= a <= 0.93:
                continue
            r = lerp(r0, r1, ease("out3", a))
            w = width * max(0.3, (1.0 - a) ** 1.3) * (1.0 if j == 0 else 0.6)
            bass.ring(c, p, r, w, PAPER, seed=seed + k * 7 + j, n=72, alpha=alpha)


def heart_beats(t0, t1, bpm=104.0):
    """The heartbeat's lub times between t0 and t1 (for the cues)."""
    beat = 60.0 / bpm
    out, k = [], 0
    while t0 + k * beat <= t1 + 1e-9:
        out.append(t0 + k * beat)
        k += 1
    return out


# ============================================================================ figures on uneven ground
def on_ground(st, u, m, ground, facing=1):
    """A walker's state (world-x units, root at its pelvis) set on uneven ground: each foot dropped
    or raised to the snow under it (ground(u) -> z), the root put on the lower foot's ground (the
    leg down the slope reaches, the other bends). Returns (state, root z)."""
    px = st["pelvis"][0]
    zs = {}
    for side, (fx, fy, fp) in st["feet"].items():
        zs[side] = ground(u + facing * (fx - px) * m)
    z_root = min(zs.values())
    feet = {side: (fx, fy - (zs[side] - z_root) / m, fp) for side, (fx, fy, fp) in st["feet"].items()}
    return dict(st, feet=feet), z_root


# ============================================================================ the far window
def far_window(cam):
    """The farmhouse's lit window across the river in the river view (frame px), as
    world._farmhouse_far draws it."""
    d = W.SECTION_X - W.FARM[0]
    base = cam.px(W.FARM[1] - 3.0, 0.0, d)
    sc = cam.scale(d)
    return (base[0] - 0.22 * 9.0 * sc, base[1] - 0.55 * 3.2 * sc)


# ============================================================================ sound
def pan_x(x):
    return round(clamp((x - 540.0) / 540.0, -1.0, 1.0) * 0.8, 3)
