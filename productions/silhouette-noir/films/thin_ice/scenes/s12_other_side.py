"""s12 OTHER SIDE (film 172-188, 16 s): the crossing in falling snow; the farmhouse door; the
lullaby; the page goes blank; the red thread.

  1   0.0- 4.0  The river view, looking upstream, in falling snow. The guards stand where s11 left
                them, on the south bank at the head of the false trail: lanterns lowered, one with
                his hat off, him wet through and hunched; the searchlight's beam rests on them
                from the upper left. Far out on the white ice beyond them the mother crosses with
                the girl on her back (profile, small, moving right), her prints filling behind her.
  2   4.0- 7.0  The far bank: the farmhouse, its window lit, smoke from the chimney. The latch
                lifts (4.25) and the door swings in (4.3): warm light falls across the snow. The
                farm woman in her shawl waves them in (4.6-5.95) and steps back; the mother climbs
                the last of the bank into the light and goes in (6.0); the door is pushed shut
                (6.6-6.95).
  3   7.0- 9.5  The window from outside in falling snow: inside, the girl's silhouette (the red
                scarf) lifts the music box's lid (7.1) and it plays, the whole lullaby this time,
                the box alone at first; her mother stands behind her. A slow push in.
  4   9.5-12.5  The page, the camera rising: the snow fills every mark on the river (the false
                trail, the holes, his drag mark, the trampled bank, the guards' prints, her real
                prints upstream and across) and the page goes white (12.35). The strings have come
                in under the box in A major (9.5).
  5  12.5-16.0  The title re-forms on the white: THIN ICE, cracked, the red thread across the
                crack, and holds. The snow settles into the letters and the crack (13.7-14.5) until
                only the thread is left, a slow push in on it. Black at 15.75, held to the end.
                Silence.
"""
import math
from functools import lru_cache

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.thin_ice import cast as C, faces as F, kit as K, world as W
from films.thin_ice.scenes import _lib_dir as LD
from films.thin_ice.scenes import _lib_s04_s07 as L

INK, NIGHT, STEEL, SNOW, SHADOW = K.INK, K.NIGHT, K.STEEL, K.SNOW, K.SHADOW
ICE, THIN, WATER, PAPER, AMBER, RED = K.ICE, K.THIN, K.WATER, K.PAPER, K.AMBER, K.RED
SID = "s12"
FT0 = K.film_start(SID)          # 172.0
MOONLIT = 0.35                   # under the snow clouds: no moon, the page dim

# ---------------------------------------------------------------------------- beats (scene time)
T_CROSS = 0.0
T_FARM = 4.0
T_WINDOW = 7.0
T_PAGE = 9.5
T_TITLE = 12.5
T_BLACK = 15.75
SHOTS = ((T_CROSS, "cross"), (T_FARM, "farm"), (T_WINDOW, "window"), (T_PAGE, "page"), (T_TITLE, "title"),
         (T_BLACK, "black"))

# ---------------------------------------------------------------------------- 1. the crossing
ICE_TOP = W.ICE_Z + W.SNOW_T
CROSS_X = -32.0                         # her line across the white ice (W.CROSSING)
D_CROSS = W.SECTION_X - CROSS_X         # 45.2 m behind the river view's cut
N0 = 0.2                                # her body's n at t = 0: just out from the south bank
V_CROSS = 1.2                           # m/s
STEP = 0.6
M_M = C.M_PER_UNIT["mother"]
FILL_S = 9.0                            # s for the falling snow to fill a print
# the guards where s11 leaves them, on the south bank at the head of the false trail, looking out
# at the hole (off the frame, right): (who, n, d, lantern, hat in hand, head, phase). The three
# with their lanterns lowered, one with his hat off (drawn bareheaded); him, wet through, nearest
# the ice. Cheated a metre or two upstream of s11's places, to stand behind the cut.
GUARDS = (("guard", -3.1, 0.95, True, False, -12.0, 0.0),
          ("guard", -2.55, 0.3, True, False, -6.0, 2.3),
          ("guard_wet", -1.95, 1.0, True, True, -26.0, 1.1),
          ("guard_wet", -1.2, 0.25, False, False, -32.0, 0.6))
# the slung rifle (cast's guard, pelvis frame), for the guard drawn bareheaded: guard_wet has none
RIFLE = (((-74.0, -468.0), (-60.0, -468.0), (-58.0, -452.0), (-44.0, -128.0), (-62.0, -128.0)),
         ((-64.0, -140.0), (-44.0, -140.0), (-30.0, 22.0), (-58.0, 36.0), (-68.0, 18.0)))


def motion_blur(t, T):
    return 1


def _walker():
    return L.walker("mother", [(-20.0, V_CROSS), (20.0, V_CROSS)], STEP, lift=0.07, key="s12_cross")


def cross_n(t):
    wk = _walker()
    return N0 + (wk.x(t) - wk.x(0.0)) * M_M


def cam_cross(t):
    k = L.kk(t, 0.0, 4.0, "inout")
    ppm, D = 110.0, 100.0
    y_ice, y_h = 1500.0, 785.0
    e = (y_ice - y_h) / ppm
    return W.Dio(lerp(1.05, 1.25, k), ICE_TOP + (y_ice - 960.0) / ppm, ppm, eye=ICE_TOP + e, D=D)


@lru_cache(maxsize=1)
def cross_prints():
    """Her prints across the white ice, as her walker lays them: (n, side, t laid). The ones
    before the shot run back to the south bank at the same stride."""
    wk = _walker()
    out = [(N0 + (fx - wk.x(0.0)) * M_M, side, t) for t, side, fx in L.step_times(wk, -2.5, 4.2)]
    first = min(out, key=lambda p: p[0])
    n, side, tl = first
    while n > W.bank_s(CROSS_X) + 0.3:
        n -= STEP
        side = "far" if side == "near" else "near"
        tl -= STEP / V_CROSS
        out.append((n, side, tl))
    return tuple(sorted(out))


def _band_poly(cam):
    """The black band behind the cut, as draw_river draws it (frame px)."""
    pts_l, pts_r = [], []
    for d in W._depths():
        x = W.SECTION_X - d
        if x < W.BAND_X0:
            break
        tp = W.band_taper(x)
        mid = 0.5 * (W.band_lo(x) + W.band_hi(x))
        half = 0.5 * (W.band_hi(x) - W.band_lo(x)) * tp
        pts_l.append(cam.px(mid - half, W.ICE_Z, d))
        pts_r.append(cam.px(mid + half, W.ICE_Z, d))
    return pts_l + pts_r[::-1]


def _river_polys(cam):
    """The river's white ice and its two banks' slopes behind the cut, as draw_river lays them."""
    ds = W._depths()
    xs = [W.SECTION_X - d for d in ds]
    bs = [W.bank_s(x) for x in xs]
    bn = [W.bank_n(x) for x in xs]
    river = [cam.px(b, W.ICE_Z, d) for b, d in zip(bn, ds)][::-1] + [cam.px(b, W.ICE_Z, d) for b, d in zip(bs, ds)]
    north = [cam.px(b, W.ICE_Z, d) for b, d in zip(bn, ds)] + [cam.px(b + W.BANK, 0.0, d) for b, d in zip(bn, ds)][::-1]
    south = [cam.px(b, W.ICE_Z, d) for b, d in zip(bs, ds)] + [cam.px(b - W.BANK, 0.0, d) for b, d in zip(bs, ds)][::-1]
    return river, north, south


def _hole_far_half(cam, centre=W.HOLE_BIG, r=W.HOLE_R[1]):
    """The part of the big hole behind the cut (d >= 0), on the ice (frame px)."""
    d0 = W.SECTION_X - centre[0]
    pts = []
    for i in range(41):
        a = math.pi * i / 40.0
        n = centre[1] + r * math.cos(a)
        d = d0 + r * math.sin(a)
        if d >= 0.0:
            pts.append(cam.px(n, ICE_TOP, d))
    half = math.sqrt(max(r * r - d0 * d0, 0.0))
    return [cam.px(centre[1] + half, ICE_TOP, 0.0)] + pts + [cam.px(centre[1] - half, ICE_TOP, 0.0)]


def hold_hat(size=1.0):
    """His ushanka held by its crown in a lowered fist."""
    def fn(c, info):
        hc = info["hc"]
        col = info.get("rim") or INK
        p = (hc[0] + 4.0, hc[1] + 30.0 * size)
        bass.fill_polys(c, [bass.orient(bass.ring_pts(p, 40.0 * size, seed=21, n=14, amp=5.0), True)], col)
        bass.fill_polys(c, [bass.orient([(p[0] - 46.0 * size, p[1] + 6.0), (p[0] + 46.0 * size, p[1] + 6.0),
                                         (p[0] + 40.0 * size, p[1] + 34.0 * size),
                                         (p[0] - 40.0 * size, p[1] + 34.0 * size)], True)], col)
    return fn


BEAM_ON = (-2.2, 0.6, 2.0)              # the searchlight's patch on the bank round the guards (n, d, r)


def _beam_geo(cam):
    """The searchlight's beam onto the guards: its apex off the frame, up and left (the tower, far
    to the south), and where it meets the bank (frame px)."""
    n, d, r = BEAM_ON
    a = cam.px(n - r, 0.0, d)
    b = cam.px(n + r, 0.0, d)
    return (-450.0, -520.0), a, b


@lru_cache(maxsize=1)
def _shore_tree_list():
    """Spruces along both shores far upstream, where the river runs out to the horizon."""
    out = []
    for i in range(150):
        side = -1 if i % 2 == 0 else 1
        d = 150.0 + 450.0 * hash01(i, 311) ** 0.8
        x = W.SECTION_X - d
        if side > 0:
            n = W.bank_n(x) + W.BANK + 1.0 + 20.0 * hash01(i, 312)
        else:
            n = W.bank_s(x) - W.BANK - 1.0 - 20.0 * hash01(i, 312)
        out.append((n, d, 9.0 + 7.0 * hash01(i, 313), i))
    return tuple(sorted(out, key=lambda r: -r[1]))


def _shore_trees(c, cam):
    far = lerp(NIGHT, STEEL, 0.34)
    for (n, d, h, i) in _shore_tree_list():
        base = cam.px(n, 0.0, d)
        if base[0] < -150.0 or base[0] > 1230.0:
            continue
        sc = cam.scale(d)
        W.spruce_side(c, base, h * sc, h * 0.42 * sc, lerp(lerp(STEEL, NIGHT, 0.2), far, clamp((d - 150.0) / 450.0)),
                      seed=i + 200)


def _haze(c, hy):
    """Snow haze over the far shore: a flat band of night a shade paler, its top cut unevenly."""
    pts = [(x, hy - 120.0 - 14.0 * math.sin(x * 0.0071 + 1.3) - 6.0 * math.sin(x * 0.023 + 0.4))
           for x in range(-30, 1131, 40)]
    K.poly(c, pts + [(1130.0, hy + 4.0), (-30.0, hy + 4.0)], lerp(NIGHT, STEEL, 0.28))


def _guard_pose(who, lit, hat, head, ph, tt):
    """A guard standing over the hole, his lantern lowered; his hat held to his chest; him (no
    lantern), hugging himself, wet through."""
    b = math.sin(tt * 0.9 + ph)
    holds = {}
    arms = {"near": ("ang", 3.0 + 1.0 * b, 8.0), "far": ("ang", -2.0, 6.0)}
    if lit:
        holds["near"] = C.hold_lantern(tt + ph, 1.0, 2.0 * math.sin(tt * 1.1 + ph), 1.0)
    if hat:
        arms["far"] = ("ang", 22.0, 118.0)
        holds["far"] = hold_hat()
    if not lit:
        arms = {"near": ("ang", 6.0 + 0.8 * b, 14.0), "far": ("ang", 2.0, 12.0)}
    return C.still_pose("guard", t=tt + ph, head=head, arms=arms, hold=holds, lean=4.0 if lit else 14.0,
                        crouch=0.0 if lit else 12.0)


def draw_cross(c, t):
    ft = FT0 + t
    cam = cam_cross(t)
    tt = K.twos(t)
    hy = cam.horizon_y()
    K.fill(c, NIGHT)
    _haze(c, hy)
    W.draw_river(c, cam, ft, moonlit=MOONLIT, holes=("stone", "guard"), sky=False, stars_on=False, farm_light=1.0,
                 far_trees=False, trunk=False)
    snow_c = lerp(K.SNOW_DIM, SNOW, MOONLIT)
    ice_c = lerp(lerp(K.ICE_DIM, ICE, MOONLIT), snow_c, 0.5)       # fresh snow on the white ice
    thin_c = lerp(lerp(THIN, NIGHT, 0.2), THIN, MOONLIT)
    river, north, south = _river_polys(cam)
    K.poly(c, river, ice_c)
    K.poly(c, north, lerp(snow_c, SHADOW, 0.3))
    K.poly(c, south, snow_c)
    # the fresh snow dusts the black band
    K.poly(c, _band_poly(cam), lerp(thin_c, ice_c, 0.45))
    K.poly(c, _hole_far_half(cam), WATER)
    _shore_trees(c, cam)
    W._far_trees(c, cam, hy, MOONLIT)
    W._reeds_side(c, cam, MOONLIT)
    W.draw_trunk_side(c, cam)
    # her trail across the white ice: dashes at this grazing angle, filling with snow behind her
    s_m = cam.scale(D_CROSS)
    print_c = lerp(ice_c, THIN, 0.55)
    for (n, side, tl) in cross_prints():
        age = t - tl
        if age < 0.0:
            continue
        a = 1.0 - clamp(age / FILL_S) ** 0.8
        if a <= 0.02:
            continue
        lat = 0.09 if side == "near" else -0.09
        p = cam.px(n, ICE_TOP, D_CROSS - lat)
        K.ellipse(c, (p[0] + 0.04 * s_m, p[1] + 1.0), 0.14 * s_m * (1.0 - 0.3 * (1.0 - a)), max(2.2, 0.035 * s_m),
                  print_c, alpha=a)
    # the mother, carrying the girl
    wk = _walker()
    st = wk.state(tt)
    n = cross_n(tt)
    s = C.scale("mother", s_m)
    at = cam.px(n, ICE_TOP, D_CROSS)
    K.ellipse(c, (at[0] + 0.05 * s_m, at[1] + 1.5), 0.42 * s_m, max(2.5, 0.05 * s_m), lerp(ice_c, SHADOW, 0.8),
              alpha=0.8)
    pose = C.walk_pose("mother", st, t=tt, arms=C.carry_arms(tt), lean=6.0, head=-4.0)
    L.piggyback(c, st, pose, at, s, 1, t=tt, rim=None, edge=lerp(ice_c, INK, 0.5))
    # the searchlight's beam rests on the guards at the hole
    apex, ba, bb = _beam_geo(cam)
    K.beam(c, apex, ba, bb, PAPER, alpha=0.3)
    c.save()
    L.above_cut(c, cam)
    bn, bd, br = BEAM_ON
    K.poly(c, L._ground_ring(cam, bn, bd, br * 1.15, br * 0.9, 0.0, 40), PAPER, 0.22)
    K.poly(c, L._ground_ring(cam, bn, bd, br, br * 0.75, 0.0, 40), PAPER, 0.5)
    c.restore()
    # the guards, lanterns lowered (far ones first)
    for (who, gn, gd, lit, hat, head, ph) in sorted(GUARDS, key=lambda g: -g[2]):
        gs = C.scale(who, cam.scale(gd))
        gat = cam.px(gn, W.land_z(gn), gd)
        gst = L.stand_state("guard", spread=14.0)
        gpose = _guard_pose(who, lit, hat, head, ph, tt)

        def under(c_, j, lit=lit, hat=hat, gd=gd, gn=gn, ph=ph, gst=gst, gpose=gpose, gat=gat, gs=gs):
            if lit and "flame" in j:
                L.ground_glow(c_, cam, gn + 0.2, gd + 0.1, 0.7, strength=0.9, t=tt + ph, seed=int(ph * 10), cut=True)
                K.glow(c_, j["flame"], 0.32 * cam.scale(gd), 0.8, t=tt + ph, seed=int(ph * 7))
            if hat:
                K.polys(c_, [[C.frame_point("guard", gst, gpose, q, gat, gs, 1) for q in poly] for poly in RIFLE], INK)
        C.draw(c, who, gst, gpose, gat, gs, 1, rim=PAPER, rim_w=2.5, light=(-0.85, -0.5), under=under)
    # snow: thick, drifting right; lit where it falls through the beam (it falls behind the cut)
    c.save()
    L.above_cut(c, cam)
    K.snow(c, ft, n=260, wind=26.0)
    c.new_path()
    bass.draw.poly(c, [apex, ba, bb])
    c.clip()
    K.snow(c, ft, n=240, wind=26.0, seed=41, size=1.1)
    c.restore()


# ---------------------------------------------------------------------------- 2. the farmhouse door
# An elevation looking west, north to the right, on the far bank: the house's long south wall seen
# obliquely (it recedes up and to the left), its door and its window facing the river. The bank
# and the house are drawn closer together than on the map (the bank's top is 1.6 m from the door).
T_LATCH = 4.25                  # the latch lifts
T_OPEN = (4.3, 4.65)            # the door swings in; the light falls across the snow
T_WAVE = (4.6, 5.95)            # the farm woman waves them in
T_BACK = (5.95, 6.25)           # she steps back to let them in
T_SHUT = (6.6, 6.95)            # the door closes
N_ICE, N_TOP = 31.3, 33.4       # the bank's slope (cheated close to the door)
N_WALL, N_NWALL = 35.0, 41.0    # the house's south and north walls
DEPTH_DOOR = 3.1                # the door's centre, m west of the house's east wall (W.FARM_DOOR)
DOOR_W, DOOR_H = 1.05, 2.05
WIN = (4.05, 5.05, 0.95, 1.95)  # the window: depths and heights on the south wall
WALL_H, RIDGE_H, RIDGE_N = 3.2, 5.7, 38.0
HOUSE_D = 9.0                   # east wall (0) to west wall (9)
V_FARM = 1.35
N_FARM0 = 32.35                 # her n at 4.0 (half way up the slope)
OX, OY = -0.75, 0.24            # the oblique: one metre of depth (westward) on screen, per metre


class Obl:
    """The farm elevation: (n, z, depth) -> frame px; depth in m west of the house's east wall.
    The door's threshold (n = N_WALL, z = 0, depth = DEPTH_DOOR) sits at frame (x0, y0)."""

    def __init__(self, x0, y0, s):
        self.x0, self.y0, self.s = x0, y0, s

    def px(self, n, z, depth=DEPTH_DOOR):
        dd = depth - DEPTH_DOOR
        return (self.x0 + (n - N_WALL) * self.s + dd * OX * self.s, self.y0 - z * self.s - dd * OY * self.s)


def cam_farm(t):
    k = L.kk(t, T_FARM, 3.0, "inout")
    return Obl(lerp(720.0, 700.0, k), lerp(1490.0, 1470.0, k), lerp(138.0, 150.0, k))


DEPTH_CUT = -1.2                # the elevation's cut, in front of the house's east wall


def farm_bed(n):
    """The riverbed under the ice near the north bank (cheated close, like the bank)."""
    u = clamp((N_ICE - n) / 7.0)
    return W.ICE_Z - 0.3 - 2.6 * math.sin(0.5 * math.pi * u) ** 0.8 - 0.15 * math.sin(n * 1.7)


def farm_ground(n):
    if n <= N_ICE:
        return W.ICE_Z
    if n >= N_TOP:
        return 0.0
    return lerp(W.ICE_Z, 0.0, ease("inout", (n - N_ICE) / (N_TOP - N_ICE)))


def _farm_walker():
    return L.walker("mother", [(-10.0, V_FARM), (20.0, V_FARM)], 0.55, lift=0.07, key="s12_farm")


def farm_n(t):
    wk = _farm_walker()
    return N_FARM0 + (wk.x(t) - wk.x(T_FARM)) * M_M


@lru_cache(maxsize=1)
def farm_prints():
    """Her prints over the last of the ice, up the bank and to the threshold, as her walker lays
    them: (n, side, t laid)."""
    wk = _farm_walker()
    out = [(N_FARM0 + (fx - wk.x(T_FARM)) * M_M, side, t) for t, side, fx in L.step_times(wk, T_FARM - 6.0, T_WINDOW)]
    return tuple(p for p in sorted(out) if p[0] < N_WALL - 0.2)


def door_angle(t):
    """Degrees the door has swung in (0 shut)."""
    # hinged on the doorway's near side, it swings in out of sight behind the jamb; pushed shut, it
    # comes back into view across the light and slows as it closes
    return 84.0 * L.kk(t, T_OPEN[0], T_OPEN[1] - T_OPEN[0], "out3") * (1.0 - L.kk(t, T_SHUT[0], T_SHUT[1] - T_SHUT[0], "out"))


def _door_quad(cam, d0, d1, z0=0.0, z1=DOOR_H, n=N_WALL):
    return [cam.px(n, z0, d1), cam.px(n, z0, d0), cam.px(n, z1, d0), cam.px(n, z1, d1)]


def _opening(cam):
    return _door_quad(cam, DEPTH_DOOR - DOOR_W / 2.0, DEPTH_DOOR + DOOR_W / 2.0)


def _clip_through_door(c, cam):
    """Clip to what is seen of a figure at the door's depth: all of it outside the wall, and
    through the doorway what is inside."""
    o = _opening(cam)            # far-bottom, near-bottom, near-top, far-top
    xw = cam.px(N_WALL, 0.0)[0]
    # the doorway's top and bottom edges where they cross the wall line at the figure's depth
    def at_x(p, q, x):
        u = (x - p[0]) / (q[0] - p[0])
        return (x, lerp(p[1], q[1], u))
    top_w, bot_w = at_x(o[3], o[2], xw), at_x(o[0], o[1], xw)
    pts = [(-200.0, -200.0), (xw, -200.0), top_w, o[2], o[1], bot_w, (xw, 2200.0), (-200.0, 2200.0)]
    c.new_path()
    bass.draw.poly(c, pts)
    c.clip()


def _spill(cam, k, reach=3.9, spread=0.42):
    """The door's light on the snow, from the threshold out over the bank (k: how open)."""
    if k <= 0.0:
        return []
    lo, hi = [], []
    m = 16
    for i in range(m + 1):
        u = i / m
        n = N_WALL - reach * u
        z = farm_ground(n) + 0.01
        w = (DOOR_W / 2.0) * (0.3 + 0.7 * k) + spread * reach * u * k
        lo.append(cam.px(n, z, DEPTH_DOOR - w))
        hi.append(cam.px(n, z, DEPTH_DOOR + w))
    return lo + hi[::-1]


def _farm_trees():
    out = []
    for i in range(16):
        n = 34.5 + 20.0 * (i + 0.5 * hash01(i, 301)) / 16.0
        dep = 15.0 + 11.0 * hash01(i, 302)
        h = 4.6 + 3.4 * hash01(i, 303)
        out.append((n, dep, h, i))
    return sorted(out, key=lambda r: -r[1])


def _smoke(c, cam, t):
    top = cam.px(RIDGE_N + 0.3, RIDGE_H + 1.1, 6.2)
    for j in range(6):
        u = ((t * 0.32 + j / 6.0) % 1.0)
        p = (top[0] + 70.0 * u + 12.0 * math.sin(t * 1.3 + j), top[1] - 260.0 * u)
        r = (0.12 + 0.5 * u) * cam.s
        K.disc(c, p, r, lerp(NIGHT, STEEL, 0.55), seed=j + int(t * 0.32 + j / 6.0) * 7, alpha=0.55 * (1.0 - u))


def _farm_cut(c, cam, snow_c):
    """The front of the elevation: the land's snow and earth, the bank, the ice slab over the
    water, the riverbed."""
    nl = N_WALL + (-60.0 - cam.px(N_WALL, 0.0, DEPTH_CUT)[0]) / cam.s
    nr = N_WALL + (1140.0 - cam.px(N_WALL, 0.0, DEPTH_CUT)[0]) / cam.s
    P = lambda n, z: cam.px(n, z, DEPTH_CUT)
    ns = [nl + (nr - nl) * i / 160.0 for i in range(161)]
    top = [(n, farm_bed(n) if n < N_ICE else farm_ground(n) - (W.LAND_SNOW if n >= N_TOP else 0.0)) for n in ns]
    K.poly(c, [P(n, z) for n, z in top] + [(1140.0, 2000.0), (-60.0, 2000.0)], INK)
    # the water under the ice, the slab, its snow
    wn = [n for n in ns if n < N_ICE] + [N_ICE]
    if len(wn) > 1:
        K.poly(c, [P(n, W.ICE_Z) for n in wn] + [P(n, farm_bed(n)) for n in wn[::-1]], WATER)
        K.poly(c, [P(n, W.ICE_Z) for n in wn] + [P(n, W.ICE_Z - W.ICE_T) for n in wn[::-1]], lerp(ICE, INK, 0.28))
        K.poly(c, [P(n, W.ICE_Z + W.SNOW_T) for n in wn] + [P(n, W.ICE_Z) for n in wn[::-1]], snow_c)
    # the bank's slope and the land: snow over earth
    sl = [N_ICE + (N_TOP - N_ICE) * i / 20.0 for i in range(21)]
    K.poly(c, [P(n, farm_ground(n)) for n in sl] + [P(n, farm_ground(n) - 0.3) for n in sl[::-1]], SHADOW)
    ln = [N_TOP + (nr - N_TOP) * i / 30.0 for i in range(31)]
    K.poly(c, [P(n, 0.0) for n in ln] + [P(n, -W.LAND_SNOW) for n in ln[::-1]], SHADOW)


def _above_farm_cut(c, cam):
    nl = N_WALL + (-60.0 - cam.px(N_WALL, 0.0, DEPTH_CUT)[0]) / cam.s
    nr = N_WALL + (1140.0 - cam.px(N_WALL, 0.0, DEPTH_CUT)[0]) / cam.s
    ns = [nl + (nr - nl) * i / 80.0 for i in range(81)]
    pts = [(-60.0, -60.0), (1140.0, -60.0)] + [cam.px(n, farm_ground(n) + (W.SNOW_T if n < N_ICE else 0.0), DEPTH_CUT)
                                              for n in ns[::-1]]
    c.new_path()
    bass.draw.poly(c, pts)
    c.clip()


def draw_farm(c, t):
    ft = FT0 + t
    cam = cam_farm(t)
    tt = K.twos(t)
    snow_c = lerp(K.SNOW_DIM, SNOW, MOONLIT)
    ice_c = lerp(lerp(K.ICE_DIM, ICE, MOONLIT), snow_c, 0.35)
    wall_c = lerp(INK, STEEL, 0.28)
    end_c = lerp(INK, STEEL, 0.16)
    K.fill(c, NIGHT)
    FAR = 26.0
    # the ground behind the cut: the land, the bank's slope, the ice, to the trees
    K.poly(c, [cam.px(N_TOP, 0.0, DEPTH_CUT), cam.px(80.0, 0.0, DEPTH_CUT), cam.px(80.0, 0.0, FAR),
               cam.px(N_TOP, 0.0, FAR)], snow_c)
    ns = [N_ICE + (N_TOP - N_ICE) * i / 16.0 for i in range(17)]
    K.poly(c, [cam.px(n, farm_ground(n), DEPTH_CUT) for n in ns] + [cam.px(n, farm_ground(n), FAR) for n in ns[::-1]],
           lerp(snow_c, SHADOW, 0.3))
    K.poly(c, [cam.px(-20.0, W.ICE_Z, DEPTH_CUT), cam.px(N_ICE, W.ICE_Z, DEPTH_CUT), cam.px(N_ICE, W.ICE_Z, FAR),
               cam.px(-20.0, W.ICE_Z, FAR)], ice_c)
    for (n, dep, h, i) in _farm_trees():
        base = cam.px(n, 0.0, dep)
        W.spruce_side(c, base, h * cam.s, h * 0.4 * cam.s, lerp(lerp(STEEL, INK, 0.35), NIGHT, 0.3 * (dep - 13.0) / 20.0),
                      seed=i + 40, snow=lerp(snow_c, NIGHT, 0.3), snow_alpha=0.8)
    # her trail across the ice and up the bank, laid as she walks, filling behind her
    print_c = lerp(ice_c, THIN, 0.5)
    for (n, side, tl) in farm_prints():
        age = tt - tl
        if age < 0.0:
            continue
        a = 1.0 - clamp(age / FILL_S) ** 0.8
        if a <= 0.02:
            continue
        lat = 0.09 if side == "near" else -0.09
        p = cam.px(n, farm_ground(n) + 0.03, DEPTH_DOOR - lat)
        K.ellipse(c, p, 0.14 * cam.s * (1.0 - 0.3 * (1.0 - a)), max(2.2, 0.035 * cam.s), print_c, alpha=a)
    # the window's light on the snow
    win_spill = [cam.px(N_WALL, 0.01, WIN[0] + 0.1), cam.px(N_WALL, 0.01, WIN[1] - 0.1),
                 cam.px(N_WALL - 2.4, farm_ground(N_WALL - 2.4) + 0.01, WIN[1] + 0.6),
                 cam.px(N_WALL - 2.4, farm_ground(N_WALL - 2.4) + 0.01, WIN[0] - 0.6)]
    K.poly(c, win_spill, AMBER, 0.16)
    # the door's light falls across the snow
    ang = door_angle(t)
    k = math.sin(math.radians(ang))
    if k > 0.0:
        K.poly(c, _spill(cam, k), AMBER, 0.24)
        K.poly(c, _spill(cam, k, reach=3.2, spread=0.25), AMBER, 0.28)
    # the house: the east gable end (just in frame), the south wall, the roof under snow
    e0 = [cam.px(N_WALL, 0.0, 0.0), cam.px(N_NWALL, 0.0, 0.0), cam.px(N_NWALL, WALL_H, 0.0),
          cam.px(RIDGE_N, RIDGE_H, 0.0), cam.px(N_WALL, WALL_H, 0.0)]
    K.poly(c, e0, end_c)
    K.poly(c, [cam.px(N_WALL, 0.0, 0.0), cam.px(N_WALL, 0.0, HOUSE_D), cam.px(N_WALL, WALL_H, HOUSE_D),
               cam.px(N_WALL, WALL_H, 0.0)], wall_c)
    ev = 0.35
    roof = [cam.px(N_WALL - ev, WALL_H - 0.25, -ev), cam.px(N_WALL - ev, WALL_H - 0.25, HOUSE_D + ev),
            cam.px(RIDGE_N, RIDGE_H, HOUSE_D + ev), cam.px(RIDGE_N, RIDGE_H, -ev)]
    K.poly(c, roof, snow_c)
    K.band(c, [roof[1], roof[0]], INK, max(3.0, 0.1 * cam.s), seed=5)
    K.band(c, [roof[0], roof[3]], INK, max(3.0, 0.1 * cam.s), seed=6)
    # the chimney, its smoke
    ch = [cam.px(RIDGE_N - 0.3, RIDGE_H - 0.4, 6.0), cam.px(RIDGE_N + 0.3, RIDGE_H - 0.4, 6.0),
          cam.px(RIDGE_N + 0.3, RIDGE_H + 1.1, 6.0), cam.px(RIDGE_N - 0.3, RIDGE_H + 1.1, 6.0)]
    _smoke(c, cam, ft)
    K.poly(c, ch, wall_c)
    K.poly(c, [ch[3], ch[2], (ch[2][0], ch[2][1] - 0.12 * cam.s), (ch[3][0], ch[3][1] - 0.12 * cam.s)], snow_c)
    # the window, lit, its cross of glazing bars
    wq = _door_quad(cam, WIN[0], WIN[1], WIN[2], WIN[3])
    K.poly(c, wq, AMBER)
    mx = [cam.px(N_WALL, 0.5 * (WIN[2] + WIN[3]), WIN[0]), cam.px(N_WALL, 0.5 * (WIN[2] + WIN[3]), WIN[1])]
    my = [cam.px(N_WALL, WIN[2], 0.5 * (WIN[0] + WIN[1])), cam.px(N_WALL, WIN[3], 0.5 * (WIN[0] + WIN[1]))]
    K.band(c, mx, wall_c, max(3.0, 0.07 * cam.s), seed=7)
    K.band(c, my, wall_c, max(3.0, 0.07 * cam.s), seed=8)
    K.band(c, wq + [wq[0]], INK, max(3.0, 0.08 * cam.s), seed=9)
    K.band(c, [cam.px(N_WALL - 0.12, WIN[2] - 0.04, WIN[0] - 0.15), cam.px(N_WALL - 0.12, WIN[2] - 0.04, WIN[1] + 0.15)],
           snow_c, max(4.0, 0.1 * cam.s), seed=10)
    K.glow(c, cam.px(N_WALL, 1.45, 0.5 * (WIN[0] + WIN[1])), 1.1 * cam.s, 0.5, t=tt, seed=3)
    # the doorway: warm inside once the door swings in, the door itself turning on its hinge
    op = _opening(cam)
    if ang > 0.5:
        K.poly(c, op, AMBER)
        a = math.radians(ang)
        d_h = DEPTH_DOOR - DOOR_W / 2.0
        free = (N_WALL + DOOR_W * math.sin(a), d_h + DOOR_W * math.cos(a))
        panel = [cam.px(N_WALL, 0.0, d_h), cam.px(free[0], 0.0, free[1]), cam.px(free[0], DOOR_H, free[1]),
                 cam.px(N_WALL, DOOR_H, d_h)]
        c.save()
        c.new_path()
        bass.draw.poly(c, op)
        c.clip()
        K.poly(c, panel, lerp(INK, AMBER, 0.12))
        c.restore()
    else:
        K.poly(c, op, lerp(INK, STEEL, 0.1))
    # the farm woman in the doorway, waving them in, then stepping back inside
    back = L.kk(t, T_BACK[0], T_BACK[1] - T_BACK[0], "inout")
    show = L.kk(t, T_OPEN[0] + 0.12, 0.2, "out")
    if show > 0.0 and t < T_SHUT[1]:
        wn = N_WALL - 0.05 + 0.75 * back
        wst = L.stand_state("farmwife", spread=12.0)
        # she beckons: her arm out toward them, the hand curling back to her, again and again
        e = clamp(2.5 * L.bump(t, T_WAVE[0], T_WAVE[1]))
        sw = math.sin((t - T_WAVE[0]) * 2.0 * math.pi * 1.6)
        arms = {"near": ("ang", lerp(12.0, 74.0, e) + 6.0 * sw * e, lerp(14.0, 62.0 + 46.0 * sw, e)),
                "far": ("ang", 30.0, 60.0)}
        wpose = C.still_pose("farmwife", t=tt, head=-6.0, arms=arms, lean=lerp(-6.0, 4.0, back))
        c.save()
        _clip_through_door(c, cam)
        C.draw(c, "farmwife", wst, wpose, cam.px(wn, 0.0), C.scale("farmwife", cam.s) * lerp(0.6, 1.0, show), -1,
               edge=None)
        c.restore()
    # the mother carrying the girl: up the bank, into the light, through the door
    wk = _farm_walker()
    st = wk.state(tt)
    n = farm_n(tt)
    st2, z_root = L.on_ground(st, n, M_M, farm_ground, 1)
    s = C.scale("mother", cam.s)
    slope = clamp((N_TOP - n) / (N_TOP - N_ICE))
    pose = C.walk_pose("mother", st, t=tt, arms=C.carry_arms(tt), lean=6.0 + 10.0 * slope, head=4.0 * (1.0 - slope))
    at = cam.px(n, z_root)
    c.save()
    _clip_through_door(c, cam)
    lit = clamp((n - (N_WALL - 3.4)) / 1.2) * clamp(ang / 40.0)
    L.piggyback(c, st2, pose, at, s, 1, t=tt, rim=lerp(AMBER, PAPER, 0.25) if lit > 0.05 else None,
                rim_w=2.5 * lit + 0.5, light=(0.9, -0.3), edge=lerp(snow_c, INK, 0.5))
    c.restore()
    # the door's frame over all of it
    K.band(c, [op[0], op[3], op[2], op[1]], INK, max(3.0, 0.09 * cam.s), seed=11)
    _farm_cut(c, cam, snow_c)
    # snow, and the flakes caught in the door's light
    c.save()
    _above_farm_cut(c, cam)
    K.snow(c, ft, n=230, wind=20.0, seed=13)
    c.restore()
    if k > 0.0:
        c.save()
        sp = _spill(cam, k, reach=3.6, spread=0.3)
        top = [cam.px(N_WALL, DOOR_H, DEPTH_DOOR + DOOR_W / 2.0), cam.px(N_WALL, DOOR_H, DEPTH_DOOR - DOOR_W / 2.0)]
        vol = [op[1], op[2]] + [sp[0], sp[len(sp) // 2 - 1]][::-1]
        c.new_path()
        bass.draw.poly(c, [top[0], top[1], sp[len(sp) // 2], sp[len(sp) // 2 + 1], sp[-1]])
        c.clip()
        K.snow(c, ft, n=160, wind=20.0, seed=29, color=lerp(AMBER, PAPER, 0.35), alpha=0.9 * k)
        c.restore()


# ---------------------------------------------------------------------------- 3. the window
# The farmhouse window from outside in the falling snow: through the glazing bars, the girl's
# silhouette (the RED scarf at her neck) opens the music box on the table; her mother beside her.
T_LID = 7.1                     # the lid springs open (the girl's hand lifts it)
NOTES = (7.25, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0)
NOTE_NAMES = ("E5", "C#5", "D5", "B4", "C#5", "A4", "B4", "E4", "A4", "C#5", "B4", "G#4", "A4")
T_STRINGS = 9.5                 # the strings come in under the box, in A major
WIN_BOX = (70.0, 250.0, 1010.0, 1630.0)     # the window's opening (frame px, before the push)
WIN_MULLION, WIN_TRANSOM = 525.0, 790.0
TABLE_Y = 1440.0
BOX_AT = (566.0, TABLE_Y)       # the music box's front (her side) bottom corner; its hinge is at the back,
BOX_S = 1.3                     # far enough inside the pane for the open lid to show


FRAME_W, BAR_W = 40.0, 28.0


def _win_xf(t):
    """The slow push in on the box: (scale, centre)."""
    k = L.kk(t, T_WINDOW, T_PAGE - T_WINDOW, "inout")
    return lerp(1.0, 1.08, k), (600.0, 1200.0)


def _panes():
    x0, y0, x1, y1 = WIN_BOX
    fw, bw = FRAME_W, BAR_W
    out = []
    for (ta, tb) in ((y0 + fw, WIN_TRANSOM - bw / 2.0), (WIN_TRANSOM + bw / 2.0, y1 - fw)):
        out.append((x0 + fw, ta, WIN_MULLION - bw / 2.0, tb))
        out.append((WIN_MULLION + bw / 2.0, ta, x1 - fw, tb))
    return out


def _clip_panes(c):
    c.new_path()
    for (a, b, cc, d) in _panes():
        c.rectangle(a, b, cc - a, d - b)
    c.clip()


def box_open(t):
    return ease("outback", clamp((t - T_LID) / 0.16))


def draw_window(c, t):
    ft = FT0 + t
    tt = K.twos(t)
    snow_c = lerp(K.SNOW_DIM, SNOW, MOONLIT)
    wall_c = lerp(INK, STEEL, 0.24)
    sc, ctr = _win_xf(t)
    K.fill(c, wall_c)
    c.save()
    c.translate(ctr[0], ctr[1])
    c.scale(sc, sc)
    c.translate(-ctr[0], -ctr[1])
    x0, y0, x1, y1 = WIN_BOX
    # the boards of the wall
    for i in range(14):
        y = -200.0 + 160.0 * i
        K.band(c, [(-200.0, y), (1300.0, y + 6.0)], lerp(wall_c, INK, 0.35), 4.0, seed=60 + i)
    # the snow on the ground under the window, the window's light on it
    gy = 1720.0
    K.poly(c, [(x, gy + 14.0 * math.sin(x * 0.011 + 1.0)) for x in range(-220, 1321, 40)] + [(1320.0, 2300.0), (-220.0, 2300.0)],
           snow_c)
    for (a, b, cc, d) in _panes():
        k = (b - y0) / (y1 - y0)
        K.poly(c, [(a - 40.0 - 120.0 * k, gy + 40.0 + 260.0 * (1.0 - k) * 0.4), (cc - 30.0 - 120.0 * k, gy + 40.0 + 260.0 * (1.0 - k) * 0.4),
                   (cc + 30.0 - 150.0 * k, gy + 120.0 + 300.0 * (1.0 - k) * 0.4), (a - 10.0 - 150.0 * k, gy + 120.0 + 300.0 * (1.0 - k) * 0.4)],
               AMBER, 0.18)
    # inside: the warm room
    c.save()
    _clip_panes(c)
    K.poly(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], AMBER)
    # the lamp on its shelf, its light
    K.glow(c, (790.0, 560.0), 300.0, 0.45, t=tt, color=PAPER, seed=4)
    K.poly(c, [(560.0, 690.0), (1000.0, 690.0), (1000.0, 712.0), (560.0, 712.0)], INK)
    lamp = [(752.0, 690.0), (828.0, 690.0), (818.0, 664.0), (800.0, 652.0), (806.0, 610.0), (816.0, 560.0), (806.0, 512.0),
            (774.0, 512.0), (764.0, 560.0), (774.0, 610.0), (780.0, 652.0), (762.0, 664.0)]
    K.poly(c, lamp, INK)
    K.poly(c, [(778.0, 600.0), (802.0, 600.0), (810.0, 562.0), (802.0, 524.0), (778.0, 524.0), (770.0, 562.0)],
           lerp(AMBER, PAPER, 0.5))
    fl = 1.0 + 0.06 * math.sin(tt * 17.0)
    K.ellipse(c, (790.0, 566.0 - 4.0 * fl), 7.0 * fl, 16.0 * fl, PAPER)
    # the mother standing behind her, looking down at the box
    F.mother(c, (215.0, 1045.0), 0.86, look=0.7, lid=0.0, down=0.9, t=tt, rim=None, edge=None)
    # the girl, the music box on the table, her hand on its lid
    F.girl(c, (335.0, 1395.0), 0.8, look=0.8, lid=0.0, down=0.6, t=tt, rim=None, edge=None,
           pompom=2.0 * math.sin(tt * 2.0))
    K.poly(c, [(x0, TABLE_Y), (x1, TABLE_Y), (x1, y1), (x0, y1)], INK)
    ou = box_open(t)
    spin = 3.0 * max(0.0, t - T_LID)
    bw_ = 220.0 * BOX_S
    c.save()
    c.translate(BOX_AT[0] + bw_, BOX_AT[1])
    c.scale(-1.0, 1.0)             # its hinge at the back, away from her: the lid swings up away from her
    F.music_box(c, (0.0, 0.0), BOX_S, open_u=ou, t=ft, spin=spin, rim=None)
    c.restore()
    # her hand on the lid's front edge: she lifts it, it springs, she draws back to the table's edge
    latch = (BOX_AT[0] + 6.0, BOX_AT[1] - 104.0 * BOX_S)
    lift = 16.0 * L.bump(t, T_LID - 0.08, T_LID + 0.22)
    rest = (BOX_AT[0] - 40.0, TABLE_Y - 22.0)
    back = L.kk(t, T_LID + 0.12, 0.55, "inout")
    tip = (lerp(latch[0], rest[0], back), lerp(latch[1] - lift, rest[1], back))
    F.mitten(c, (405.0, 1372.0), tip, 0.4, rim=None, edge=None, thumb=0.6, curl=0.3)
    # each note: a ring of light off the box
    top = (BOX_AT[0] + 110.0 * BOX_S, BOX_AT[1] - 160.0 * BOX_S)
    for tn in NOTES:
        u = clamp((t - tn) / 0.6)
        if 0.0 < u < 1.0:
            K.ellipse(c, top, 80.0 + 320.0 * u, 30.0 + 120.0 * u, PAPER, alpha=0.24 * (1.0 - u))
    c.restore()
    # the frame and its glazing bars, snow on the sill and in the corners of the panes
    fw, bw = FRAME_W, BAR_W
    frame = [[(x0, y0), (x1, y0), (x1, y0 + fw), (x0, y0 + fw)], [(x0, y1 - fw), (x1, y1 - fw), (x1, y1), (x0, y1)],
             [(x0, y0), (x0 + fw, y0), (x0 + fw, y1), (x0, y1)], [(x1 - fw, y0), (x1, y0), (x1, y1), (x1 - fw, y1)],
             [(WIN_MULLION - bw / 2, y0), (WIN_MULLION + bw / 2, y0), (WIN_MULLION + bw / 2, y1), (WIN_MULLION - bw / 2, y1)],
             [(x0, WIN_TRANSOM - bw / 2), (x1, WIN_TRANSOM - bw / 2), (x1, WIN_TRANSOM + bw / 2), (x0, WIN_TRANSOM + bw / 2)]]
    K.polys(c, frame, INK)
    for (a, b, cc, d) in _panes():
        K.poly(c, [(a, d), (a + 46.0, d - 4.0), (a + 110.0, d - 12.0), (cc - 90.0, d - 8.0), (cc - 30.0, d - 20.0), (cc, d - 28.0),
                   (cc, d)], snow_c)
    xm = WIN_MULLION
    sill = [(x0 - 50.0, y1 + 30.0), (x1 + 50.0, y1 + 30.0), (x1 + 50.0, y1 - 4.0), (x1 + 20.0, y1 - 18.0),
            (xm + 160.0, y1 - 22.0), (xm - 80.0, y1 - 14.0), (x0 + 30.0, y1 - 20.0), (x0 - 50.0, y1 - 6.0)]
    K.poly(c, [(x0 - 50.0, y1 + 30.0), (x1 + 50.0, y1 + 30.0), (x1 + 50.0, y1 + 58.0), (x0 - 50.0, y1 + 58.0)], INK)
    K.poly(c, sill, snow_c)
    K.poly(c, [(x0 - 40.0, y0 - 40.0), (x1 + 40.0, y0 - 40.0), (x1 + 40.0, y0), (x0 - 40.0, y0)], INK)
    K.poly(c, [(x0 - 40.0, y0 - 40.0), (x0 - 10.0, y0 - 58.0), (xm, y0 - 64.0), (x1 + 20.0, y0 - 56.0), (x1 + 40.0, y0 - 40.0)],
           snow_c)
    c.restore()
    # the snow falling past the window
    K.snow(c, ft, n=240, wind=18.0, seed=53, size=1.15)


# ---------------------------------------------------------------------------- 4. the page
# Straight down on the river, the camera rising: the snow fills every mark on the page (the false
# trail, the hole, his drag mark, the trampled bank, the guards' prints, her real prints upstream
# and across) and then the page itself goes white.
PAGE_W = lerp(SNOW, PAPER, 0.45)            # the blank page
CAM_P0 = W.Plan(12.6, 8.2, 74.0)            # close on the hole, the drag mark, the trail's end
CAM_P1 = W.Plan(-9.0, 13.0, 15.0)           # the whole river: the trail to the crossing and the farmhouse
T_RISE = (9.75, 11.9)
T_FILL = (9.6, 11.7)                        # the marks fill
T_BLANK = (11.4, 12.35)                     # the page goes white
DRAG_PTS = ((13.26, 10.1), (13.0, 9.5), (12.75, 8.85))


def cam_page(t):
    return W.plan_lerp(CAM_P0, CAM_P1, L.kk(t, T_RISE[0], T_RISE[1] - T_RISE[0], "inout3"))


@lru_cache(maxsize=1)
def page_prints():
    return tuple(W.prints_before(SID)) + tuple(W.CROSSING_PRINTS)


def draw_page(c, t):
    ft = FT0 + t
    cam = cam_page(t)
    moon = 0.45
    page_c = lerp(K.SNOW_DIM, SNOW, moon)
    cov = ease("inout", clamp((t - T_FILL[0]) / (T_FILL[1] - T_FILL[0])))
    W.draw_page(c, cam, ft, moonlit=moon, prints=(), cover=cov, holes=(), shadows=0.0, farm_light=1.0, door=0.0)
    W.draw_prints(c, cam, page_prints(), cover=cov, page=page_c, color=lerp(SHADOW, THIN, 0.45))
    # the band and the holes fill with snow
    hole_c = lerp(WATER, page_c, cov)
    for name in ("stone", "guard"):
        centre, r, seed = W.HOLES[name]
        K.poly(c, cam.pts(W.hole_poly(centre, r, seed)), hole_c)
        for sh in W.hole_shards(centre, r, seed):
            K.poly(c, cam.pts(sh), lerp(lerp(THIN, ICE, 0.35), page_c, cov))
    # his ushanka, still floating in the hole (s11), goes under with it
    if cov < 1.0:
        c.push_group()
        LD.hat_top(c, cam, ft)
        c.pop_group_to_source()
        c.paint_with_alpha(1.0 - cov)
    # his drag mark, wet, from the hole's south edge to the trunk's tip
    K.band(c, cam.pts(DRAG_PTS), lerp(lerp(THIN, WATER, 0.25), page_c, cov), max(2.0, 0.42 * cam.ppm), seed=17,
           alpha=0.75 * (1.0 - cov), taper=(1.0, 0.6))
    # the snow covering the river: the ice, the band, the trunk, the reeds go under it, then the page
    x0, x1, n0, n1 = cam.bounds(3.0)
    xs = [x0 + (x1 - x0) * i / 40.0 for i in range(41)]
    band = [(x, W.band_lo(x)) for x in xs if x >= W.BAND_X0] + [(x, W.band_hi(x)) for x in xs[::-1] if x >= W.BAND_X0]
    if len(band) > 2:
        K.poly(c, cam.pts(band), page_c, 0.55 * cov)
    # and over all of it, the woods and the reeds too, the snow lies thicker until the page is white
    blank = ease("inout", clamp((t - T_BLANK[0]) / (T_BLANK[1] - T_BLANK[0])))
    K.fill(c, lerp(page_c, PAGE_W, blank), alpha=clamp(0.55 * cov + 0.45 * blank))
    # the falling snow, seen from above
    K.snow_top(c, ft, n=200, wind=(20.0, 8.0), alpha=1.0 - 0.6 * blank)


# ---------------------------------------------------------------------------- 5. the title
# On the white page the title re-forms, written in the snow like the prints: THIN ICE, cracked,
# the black water in the crack, the red thread across it. The snow settles into the letters and
# the crack until only the thread is left; a slow push in on it. Black at 15.75.
T_FORM = (12.5, 12.85)
T_SETTLE = (13.7, 14.5)
TITLE_INK = lerp(SHADOW, THIN, 0.35)


def _s1():
    from films.thin_ice.scenes import s01_title as S1
    return S1


def thread_ends():
    S1 = _s1()
    up, lo = S1._gap_lines(S1.OPEN)
    i = S1._thread_i()
    return lo[i], up[i]


def _title_xf(t):
    """The push in on the thread: (scale, the thread's midpoint, how far it has drifted to the
    frame's centre)."""
    a, b = thread_ends()
    mid = (0.5 * (a[0] + b[0]), 0.5 * (a[1] + b[1]))
    k1 = L.kk(t, T_FORM[0], T_SETTLE[0] + 0.3 - T_FORM[0], "inout")
    k2 = L.kk(t, T_SETTLE[0] + 0.25, T_BLACK - T_SETTLE[0] - 0.25, "inout")
    return 1.0 + 0.12 * k1 + 2.3 * k2, mid, k2


def draw_title(c, t):
    ft = FT0 + t
    S1 = _s1()
    K.fill(c, PAGE_W)
    sc, mid, k = _title_xf(t)
    c.save()
    # the thread's midpoint drifts to the frame's centre as the push gathers
    c.translate(lerp(mid[0], 540.0, k), lerp(mid[1], 940.0, k))
    c.scale(sc, sc)
    c.translate(-mid[0], -mid[1])
    form = ease("out3", clamp((t - T_FORM[0]) / (T_FORM[1] - T_FORM[0])))
    settle = ease("inout", clamp((t - T_SETTLE[0]) / (T_SETTLE[1] - T_SETTLE[0])))
    off, rot = S1.OPEN, S1.TURN
    up, lo = S1._gap_lines(off)
    gap_a = form * (1.0 - settle)
    if gap_a > 0.0:
        K.poly(c, up + lo[::-1], lerp(WATER, PAGE_W, settle), gap_a)
    if form * (1.0 - settle) > 0.0:
        letters = lambda i: (0.0, 18.0 * (1.0 - ease("out3", clamp((t - T_FORM[0] - 0.04 * i) / 0.25))), 0.0,
                             clamp((t - T_FORM[0] - 0.04 * i) / 0.2))
        LD.draw_title_floes(c, lerp(TITLE_INK, PAGE_W, settle), off, rot, alpha=1.0 - settle * settle, letters=letters)
    # flakes settling into the letters and the crack
    if settle > 0.0:
        for j in range(160):
            tj = T_SETTLE[0] + (T_SETTLE[1] - T_SETTLE[0]) * hash01(j, 501) * 0.9
            if t < tj:
                continue
            p = (60.0 + 960.0 * hash01(j, 502), 560.0 + 700.0 * hash01(j, 503))
            K.disc(c, p, 3.0 + 6.0 * hash01(j, 504), PAGE_W, seed=j, alpha=0.9 * (1.0 - settle) + 0.1)
    # the red thread, holding: the last thing on the page
    a, b = lo[S1._thread_i()], up[S1._thread_i()]
    ta = clamp((t - (T_FORM[0] + 0.12)) / 0.15)
    if ta > 0.0:
        K.band(c, [a, b], RED, 5.0, seed=5, alpha=ta)
        for q in (a, b):
            K.dot(c, q, 4.5, RED, alpha=ta)
    c.restore()
    K.snow_top(c, ft, n=120, wind=(16.0, 6.0), density=K.snowfall(T_SETTLE[0], T_SETTLE[1] + 0.1),
               alpha=0.8 * (1.0 - settle) + 0.2)


def render(f, t, T):
    K.scene_setup(f, NIGHT)
    with f.screen() as c:
        if t < T_FARM:
            draw_cross(c, t)
        elif t < T_WINDOW:
            draw_farm(c, t)
        elif t < T_PAGE:
            draw_window(c, t)
        elif t < T_TITLE:
            draw_page(c, t)
        elif t < T_BLACK:
            draw_title(c, t)
        else:
            K.fill(c, INK)


def _pan(x):
    return round(clamp((x - 540.0) / 540.0, -1.0, 1.0), 2)


def cues(T):
    out = [
        # 1. the crossing
        Cue(T_CROSS, "wind_low", gain_db=-20, dur=T_FARM - T_CROSS,
            dc="the wind over the open river in falling snow: a steady soft gust and the hiss of the flakes"),
        Cue(T_CROSS, "searchlight_hum", gain_db=-26, dur=T_FARM - T_CROSS, pan=-0.6,
            dc="the searchlight's motor, far off to the left (the tower), steady: its beam rests on the guards"),
        Cue(T_CROSS + 0.4, "lantern_creak", gain_db=-28, dur=2.5, pan=-0.65,
            dc="the guards' lowered lanterns creak on their bails, small and far"),
    ]
    wk = _walker()
    for (tp, side, fx) in L.step_times(wk, T_CROSS, T_FARM - 0.02):
        x = cam_cross(tp).px(N0 + (fx - wk.x(0.0)) * M_M, ICE_TOP, D_CROSS)[0]
        out.append(Cue(tp, "snow_step_mother", gain_db=-26, pan=_pan(x),
                       dc="her boot in the fresh snow on the ice, soft and quick, far off: she carries the girl"))
    # 2. the farmhouse door
    out += [
        Cue(T_FARM, "wind_low", gain_db=-24, dur=T_WINDOW - T_FARM,
            dc="the wind, softer on the far bank in the lee of the house; the snow falling"),
        Cue(T_FARM + 0.1, "her_breath", gain_db=-22, dur=1.8, pan=-0.3,
            dc="her breath, tired, as she climbs the bank with the girl on her back (a recorded breath)"),
        Cue(T_LATCH, "door_latch", gain_db=-14, pan=0.3, dc="the farmhouse door's iron latch lifts: a cold clack"),
        Cue(T_OPEN[0], "door_creak", gain_db=-16, dur=T_OPEN[1] - T_OPEN[0] + 0.1, pan=0.3,
            dc="the door swings in on stiff hinges: a creak"),
        Cue(T_OPEN[0], "room_tone_warm", gain_db=-20, dur=T_SHUT[1] - T_OPEN[0], pan=0.3,
            dc="the warm room through the open door: a stove's soft crackle, muffled; it comes up as the door "
               "opens and is cut off when it shuts"),
        Cue(T_WAVE[0], "cloth_rustle", gain_db=-24, dur=T_WAVE[1] - T_WAVE[0], pan=0.3,
            dc="the farm woman's shawl as she waves them in (no voice)"),
        Cue(T_SHUT[1] - 0.02, "door_shut", gain_db=-12, pan=0.3,
            dc="the door shuts: a soft wooden thud and the latch dropping; the room's warmth is cut off"),
    ]
    fk = _farm_walker()
    for (tp, side, fx) in L.step_times(fk, T_FARM, T_SHUT[0]):
        n = N_FARM0 + (fx - fk.x(T_FARM)) * M_M
        if n > N_WALL + 1.2:
            continue
        x = cam_farm(tp).px(n, farm_ground(n))[0]
        if n > N_WALL - 0.1:
            out.append(Cue(tp, "boot_wood", gain_db=-20, pan=_pan(x),
                           dc="her boot on the boards inside the door, in the warm room"))
        else:
            out.append(Cue(tp, "snow_step_mother", gain_db=-16, pan=_pan(x),
                           dc="her boot in the fresh snow, climbing the bank to the door"))
    # 3. the window: the lullaby, all of it this time; the strings under it from 9.5
    out += [
        Cue(T_WINDOW, "wind_low", gain_db=-28, dur=T_PAGE - T_WINDOW,
            dc="outside the window: the snow falling, the wind faint"),
        Cue(T_LID, "music_box_lid", gain_db=-14,
            dc="the music box's lid springs open under her mitten: a small wooden click and the spring's buzz"),
    ]
    tune = " ".join(NOTE_NAMES)
    for i, tn in enumerate(NOTES):
        last = i == len(NOTES) - 1
        out.append(Cue(tn, "music_box", gain_db=-10, note=i, dur=round(min(1.0, T_BLACK - tn), 3),
                       dc=f"the lullaby on the music box in A major, the whole tune this time, a note a beat ({tune}): "
                          f"note {i + 1} of {len(NOTES)}, {NOTE_NAMES[i]}"
                          + (f"; left ringing under the strings' last chord, cut at {T_BLACK}" if last else "")))
    out.append(Cue(T_STRINGS, "strings_resolve", gain_db=-16, dur=T_BLACK - T_STRINGS,
                   dc="the strings come in under the music box in A major, warm and slow (A, D, E, A under the tune); "
                      f"the final A major chord lands with the last note (13.0) and holds under the title and "
                      f"the thread; it stops dead at {T_BLACK}"))
    # 4. the page: the snow covers every mark
    out += [
        Cue(T_PAGE, "snow_hiss", gain_db=-26, dur=T_TITLE - T_PAGE,
            dc="the snow falling over the whole river, from above: a soft even hiss that thins as the marks fill "
               "and the page goes white"),
        Cue(T_BLANK[0], "paper_flood", gain_db=-24, dur=T_BLANK[1] - T_BLANK[0],
            dc="a soft paper whoosh, very quiet: the page goes blank"),
    ]
    # 5. the title, the thread; then silence
    out += [
        Cue(T_FORM[0], "paper_settle", gain_db=-24, dur=T_FORM[1] - T_FORM[0],
            dc="the title forms on the white: a faint papery rustle as the letters settle, one after another"),
        Cue(T_FORM[0] + 0.12, "thread_ping", gain_db=-18, dur=round(T_BLACK - T_FORM[0] - 0.12, 3),
            dc=f"the red thread: s01's single high harmonic, very soft, held under the last chord; it stops at {T_BLACK}"),
        Cue(T_SETTLE[0], "snow_settle", gain_db=-30, dur=T_SETTLE[1] - T_SETTLE[0],
            dc="the snow settling over the title: the faintest hiss, dying away"),
        Cue(T_BLACK, "cut_to_silence", gain_db=-120,
            dc=f"BLACK: every sound stops dead here; digital silence to the end of the film (nothing runs past {T_BLACK})"),
    ]
    return sorted(out, key=lambda c: c["t"])
