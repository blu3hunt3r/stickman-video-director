"""s07 HUNTER (94-108): he reads the trail past the reeds; the prints end; the far light; he steps
onto the black ice.

  0.0-3.0   PROFILE, the river view at the woods' edge (looking west, north to the right): the guard
            strides out of the trees toward us, his lantern held high (0.0-1.0); at the top of the
            bank he swings it down to the snow (1.0-1.3) and finds the trail (1.2-1.8: he slows,
            stooping, the lantern sweeping over the prints); he swings it out in front (1.8-2.2) and
            goes after them down the bank toward the ice (to 3.0). His breath; his lantern's pool
            slides over the snow.
  3.0-5.0   THE PAGE: his lantern's pool moves along her prints off the bank and out across the white
            ice beside the trunk; close by, in the reeds, two pairs of eyes follow it.
  5.0-7.0   CU IN THE REEDS, face-on: the mother's eyes above, the girl's below, the mother's mitten
            over the girl's mouth, the red scarf under it. The lantern's light slides across them,
            left to right (5.3-6.7); no breath; the heartbeat (PAPER rings, 104 bpm from 5.05).
  7.0-9.0   THE PAGE, the end of the trail: the pool comes up the prints to the black band and stops
            where they stop (8.65); he holds the lantern out over the band (8.7-9.0): no prints
            anywhere on it.
  9.0-11.5  PROFILE at the band's edge: he raises the lantern (9.1-9.55) and looks across the black
            band to the far bank's lit window (a sight line, 9.6); down at the black ice at his feet
            (10.25-10.55), up again (10.7-10.95); he steps onto it, his right boot (11.0-11.4).
  11.5-12.5 PROFILE, the hiding place by the root plate: the mother crouched over the girl, her near
            mitten over the girl's mouth (as in the close-up); she half rises out of the reeds
            (11.6-11.95), that mitten going out toward him (11.68-12.05), her other mitten to her
            own mouth: a gasp, stifled (11.72). The girl crouched in front of her looks out at him.
  12.5-14.0 CU HIS BOOT ON THE BLACK ICE, low at the band's edge (the white ice's cut at the left
            bottom, the band dark under the moon): a fine PAPER crack runs out from the heel
            (12.85-13.6; the ice sings). Last frame: the boot and the crack.

His walk: his clock has him at map n -5.3 as the scene opens (s06's last frame); he hurries along
the trail (1.9 m/s at his fastest), laying W.GUARD_ICE[0..16] as he goes, and stops with his right
boot in the last of them (n 9.25) and his left brought up beside it at the band's edge (13.5,
9.6: a closing step the record doesn't hold); his right boot then goes onto the band, in
W.GUARD_ICE[17] (13.42, 10.35) at 11.4, his body coming over between his feet (13.5, 9.98).

Handoffs: s06 ends on the page (the guard's lantern pool at the bottom of the frame, at (13.6,
-5.3)); s07 opens in profile with him striding out of the trees from there. s07's last frame is the
CU: his right boot on the black band at (13.42, 10.35), heading north, the crack from its heel; his
left boot at (13.5, 9.6); s08 opens on the page with his second step.
"""
import math
from functools import lru_cache

import cairo

from engine import paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.thin_ice import cast as C, faces as F, kit as K, world as W
from films.thin_ice.scenes import _lib_s04_s07 as L

INK, NIGHT, SNOW, SHADOW, PAPER, AMBER, RED = K.INK, K.NIGHT, K.SNOW, K.SHADOW, K.PAPER, K.AMBER, K.RED
THIN, ICE, WATER, STEEL = K.THIN, K.ICE, K.WATER, K.STEEL
FT0 = 94.0                  # film time of the scene's first frame

# ---------------------------------------------------------------------------- beats (scene time)
SHOTS = ((0.0, "out"), (3.0, "pass"), (5.0, "eyes"), (7.0, "end"), (9.0, "look"), (11.5, "rise"), (12.5, "boot"))
T_FIND = (1.0, 1.8)         # the lantern down to the snow: he finds the trail
T_FOLLOW = 1.9              # after it, down the bank, the lantern out in front
T_LIGHT = (5.3, 6.7)        # the lantern's light slides across their eyes
T_HEART = (5.05, 7.0)       # the heartbeat
HEART_BPM = 104.0
T_STOP = 8.65               # he stops where the prints stop
T_OVER = (8.7, 9.0)         # he holds the lantern out over the band
T_RAISE = (9.1, 9.55)       # he raises the lantern
T_SIGHT = 9.6               # his look across the band to the far window
T_DOWN = (10.25, 10.55)     # down at the black ice at his feet
T_UP = (10.7, 10.95)        # up again
T_STEP = (11.0, 11.4)       # his right boot onto the black band (lands at 11.4)
T_RISE = (11.6, 11.95)      # in the reeds she half rises
T_MITT = (11.68, 12.05)     # a mitten out toward him
T_GASP = 11.72              # stifled
T_CRACK = (12.85, 13.6)     # the fine crack runs out from his heel

# ---------------------------------------------------------------------------- the walk
GUARD_N0 = L.guard_n_film(FT0)       # -5.3: his clock as the scene opens
GI = W.GUARD_ICE
N_CLOSE, X_CLOSE = 9.6, 13.5         # his left boot's closing step at the band's edge (not in the record)
N_BAND = GI[17][1]                   # 10.35: his right boot on the band
N_STOP = 0.5 * (GI[16][1] + N_CLOSE)
_SPEED = ((0.0, 1.25), (0.55, 1.85), (0.9, 1.85), (1.2, 0.7), (1.8, 0.7), (2.2, 1.95), (7.9, 1.95), (T_STOP, 0.0))
M_G = C.M_PER_UNIT["guard"]


def motion_blur(t, T):
    return 1


@lru_cache(maxsize=1)
def _speed_keys():
    """His speed (m/s): the shape above, scaled so he stops at N_STOP."""
    dist = sum(0.5 * (va + vb) * (tb - ta) for (ta, va), (tb, vb) in zip(_SPEED, _SPEED[1:]))
    k = (N_STOP - GUARD_N0) / dist
    return tuple([(-3.0, L.GUARD_V)] + [(t, v * k) for t, v in _SPEED] + [(20.0, 0.0)])


def _walker():
    return L.walker("guard", list(_speed_keys()), 0.74, lift=0.11, key="s07_guard")


def gu_n(t):
    """His map n (his body) at scene time t."""
    wk = _walker()
    return GUARD_N0 + (wk.x(min(t, T_STOP + 0.3)) - wk.x(0.0)) * M_G


def gu_speed(t):
    return _walker().speed(t) * M_G if t < T_STOP else 0.0


@lru_cache(maxsize=1)
def _line():
    """His body's line on the page: midway between consecutive prints, from his last prints in the
    woods out along his prints on the ice to the band's edge."""
    feet = [(p[0], p[1]) for p in W.GUARD_WOODS if p[1] > -9.6] + [(p[0], p[1]) for p in GI[:17]] + [(X_CLOSE, N_CLOSE)]
    return tuple(((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5) for a, b in zip(feet, feet[1:]))


def gu_x(n):
    pts = _line()
    if n <= pts[0][1]:
        return L.guard_x(n) + (pts[0][0] - L.guard_x(pts[0][1]))
    for a, b in zip(pts, pts[1:]):
        if n <= b[1]:
            return lerp(a[0], b[0], (n - a[1]) / max(b[1] - a[1], 1e-6))
    return pts[-1][0]


def gu_hdg(n):
    """His heading (degrees from north), smoothed along his line."""
    return math.degrees(math.atan2(gu_x(n + 0.6) - gu_x(n - 0.6), 1.2))


@lru_cache(maxsize=1)
def _laid_t():
    return L.land_times(GI[:17], gu_n, -1.0, 9.5, lead=0.3)


def _prints(t):
    """The page's prints at t: everything before s07, his woods prints as far as he has come, and
    his prints out across the ice as he lays them."""
    gn = gu_n(t)
    laid = [p for p, ti in zip(GI[:17], _laid_t()) if t >= ti]
    return list(L.prints_upto("s07", gn + 0.3)) + laid


# ============================================================================ 1. out of the trees (0-3)
D_WOODS = 3.2               # his depth among the trees in the profile (s05's cheat) ...
D_OPEN = 0.2                # ... and out on the bank (just behind the cut: clear of the root plate)
OUT_TREES = ((-6.7, 1.45, 12.5, 8901), (-7.25, 2.6, 14.0, 8902), (-8.4, 0.95, 11.0, 8903), (-9.1, 3.9, 13.5, 8904),
             (-6.05, 4.6, 12.0, 8905))     # the woods' last trunks by his path (profile only: u, d, h, seed)


def gu_d_out(n):
    """... coming out toward the cut as he breaks out of the trees."""
    return lerp(D_WOODS, D_OPEN, L.kk(n, -5.45, 2.0))


def cam_out(t):
    return L.dio(t, [(0.0, (-4.5, 1.51, 250.0, 3.2, 4.0)), (1.2, (-2.3, 1.5, 252.0, 3.2, 4.0)),
                     (1.85, (-2.05, 1.46, 254.0, 3.15, 4.0)), (3.0, (-0.4, 1.0, 258.0, 3.0, 4.0))])


def _out_trees(c, cam, from_d=None, upto_d=None):
    snow_c = SNOW
    for (u, d, h, i) in sorted(OUT_TREES, key=lambda r: -r[1]):
        if (from_d is not None and d < from_d) or (upto_d is not None and d >= upto_d):
            continue
        base = cam.px(u, 0.0, d)
        if -300.0 < base[0] < 1380.0:
            L._trunk(c, cam, u, d, h, i, snow_c)


def _arm_out(t):
    """His lantern arm (a1, a2), lean and head through the first shot."""
    hi = (156.0, -6.0, 5.0, 6.0)         # held high, striding out of the trees
    low = (34.0, 28.0, 24.0, -28.0)      # down at the prints
    fwd = (70.0, 12.0, 9.0, -10.0)       # out in front, following them
    k1 = L.kk(t, T_FIND[0], 0.3)
    k2 = L.kk(t, T_FOLLOW - 0.1, 0.4)
    v = [lerp(lerp(a, b, k1), c_, k2) for a, b, c_ in zip(hi, low, fwd)]
    sweep = 8.0 * math.sin(9.0 * (t - T_FIND[0])) * L.bump(t, T_FIND[0] + 0.2, T_FIND[1])
    return v[0] + sweep, v[1], v[2], v[3]


def _guard_out(c, cam, t, tt, n, d):
    wk = _walker()
    st, z = L.on_ground(wk.state(tt), n, M_G, W.land_z)
    a1, a2, lean, head = _arm_out(tt)
    q = st["phase"] % 1.0
    calm = L.kk(tt, T_FIND[0], 0.3)
    sw = 8.0 * math.sin(2.0 * math.pi * q + 0.6) * (1.0 - 0.6 * calm) + 3.0 * math.sin(3.1 * tt)
    hold = C.hold_lantern(tt, 1.0, sw, 1.0)
    pose = C.walk_pose("guard", st, t=tt, lean=lean, head=head, arms={"near": ("ang", a1, a2)}, hold={"near": hold})
    ul = n + lerp(0.3, 0.6, calm)
    L.ground_glow(c, cam, ul, d, lerp(1.4, 1.1, calm), lerp(0.55, 0.85, calm), t, z=W.land_z(ul), seed=3, cut=True)
    r = 0.6 * cam.scale(d)
    return L.draw_fig(c, cam, "guard", st, pose, n, z, d, rim_w=max(2.5, 0.011 * cam.scale(d)),
                      under=lambda cc, jj: K.glow(cc, jj["flame"], r, 0.95, t, seed=4))


def draw_out(c, t):
    cam = cam_out(t)
    tt = K.twos(t)
    n = gu_n(tt)
    d = gu_d_out(n)
    W.draw_river(c, cam, FT0 + t, reeds_on=False, trunk=False)
    L.river_woods(c, cam, t, from_d=d)
    _out_trees(c, cam, from_d=d)
    L.reeds(c, cam, far=d)
    L.trail_notches(c, cam)
    if d < D_TRUNK:
        W.draw_trunk_side(c, cam)
    j = _guard_out(c, cam, t, tt, n, d)
    L.river_woods(c, cam, t, upto_d=d - 1e-6, shadows=False)
    _out_trees(c, cam, upto_d=d)
    L.reeds(c, cam, near=d)
    if d >= D_TRUNK:
        W.draw_trunk_side(c, cam)
    L.breath(c, j, "guard", t, rate=0.62, seed=71, strength=0.9)


D_TRUNK = W.SECTION_X - 0.5 * (W.TRUNK[0][0] + W.TRUNK[1][0])


# ============================================================================ 2. past the reeds (3-5), 4. the end (7-9)
def cam_pass(t):
    return L.plan(t, [(3.0, (10.55, 0.6, 112.0)), (5.0, (10.7, 1.6, 118.0))])


def cam_end(t):
    return L.plan(t, [(7.0, (13.15, 7.55, 112.0)), (9.0, (13.25, 8.95, 134.0))])


def _guard_top(c, cam, tt, ahead=0.55, side=0.3):
    """The guard on the page, his lantern's pool ahead of him on his right."""
    n = gu_n(tt)
    x = gu_x(n)
    hdg = gu_hdg(n)
    h = math.radians(hdg)
    fwd, right = (math.sin(h), math.cos(h)), (math.cos(h), -math.sin(h))
    lamp = (x + fwd[0] * ahead + right[0] * side, n + fwd[1] * ahead + right[1] * side)
    W.lamp_pool(c, cam, lamp, 1.3, 0.6, tt, seed=5)
    spd = clamp(gu_speed(tt) / 1.6)
    C.top(c, "guard", cam.px((x, n)), cam.screen_heading(hdg), cam.ppm, tt, phase=_walker().state(tt)["phase"] % 1.0,
          speed=spd, lantern=1.0)
    return x, n


def _eyes_on(cam, gx, gn, gain=0.9):
    """The pupils' offset toward the guard (frame directions)."""
    a, b = cam.px(W.HIDE), cam.px((gx, gn))
    dx, dy = b[0] - a[0], b[1] - a[1]
    L_ = math.hypot(dx, dy) or 1.0
    return (gain * dx / L_, gain * dy / L_)


def draw_pass(c, t):
    cam = cam_pass(t)
    tt = K.twos(t)
    W.draw_page(c, cam, FT0 + t, prints=_prints(tt), holes=("stone",))
    gx, gn = _guard_top(c, cam, tt)
    look = _eyes_on(cam, gx, gn)
    L.reed_eyes(c, cam, t, look=look, look_girl=(look[0] * 0.9, look[1] * 0.9))


def draw_end(c, t):
    cam = cam_end(t)
    tt = K.twos(t)
    W.draw_page(c, cam, FT0 + t, prints=_prints(tt), holes=("stone",))
    _guard_top(c, cam, tt, ahead=lerp(0.55, 1.35, L.kk(tt, T_OVER[0], T_OVER[1] - T_OVER[0])))


# ============================================================================ 3. the eyes in the reeds (5-7)
EYE_S = 0.78
EYES_M = (540.0, 600.0)     # the mother's eyes (the strip's centre)
EYES_G = (540.0, 1180.0)    # the girl's
CU_FIELD = lerp(K.SNOW_DIM, NIGHT, 0.45)     # the reed bed behind them, in the trees' shadow


def _light_x(t):
    """The lantern light's slab: its centre line's frame x at the top of the frame (it leans)."""
    k = clamp((t - T_LIGHT[0]) / (T_LIGHT[1] - T_LIGHT[0]))
    return lerp(-520.0, 1640.0, ease("inout", k))


def _slab(cx, half, lean=0.28):
    return [(cx - half, -20.0), (cx + half, -20.0), (cx + half - lean * 1960.0, 1940.0), (cx - half - lean * 1960.0, 1940.0)]


@lru_cache(maxsize=1)
def _cu_reed_list():
    out = []
    for i in range(46):
        x = -40.0 + 1160.0 * hash01(i, 611)
        h = 700.0 + 900.0 * hash01(i, 612)
        w = 7.0 + 12.0 * hash01(i, 613)
        out.append((x, h, w, 0.06 * K._sn(i, 614), i))
    return tuple(out)


def _cu_reeds(c, t):
    """The reed bed behind them: dark blades and seed heads against the shadowed snow."""
    for (x, h, w, lean, i) in _cu_reed_list():
        sway = 4.0 * math.sin(1.1 * t + i)
        top = (x + lean * h + sway, 1940.0 - h)
        K.band(c, [(x, 1940.0), top], lerp(INK, CU_FIELD, 0.35), w, seed=i, taper=(1.0, 0.35))
        if i % 4 == 0:
            K.ellipse(c, (top[0], top[1] + 40.0), w * 1.1, 44.0, lerp(INK, CU_FIELD, 0.35))


def _girl_lower(c, t):
    """Below the girl's eyes: the rest of her face, the red scarf wound up to her chin, her coat."""
    y0 = EYES_G[1] + 250.0 * EYE_S
    K.poly(c, [(-20.0, y0 - 2.0), (1100.0, y0 - 2.0), (1100.0, 1940.0), (-20.0, 1940.0)], INK)
    fl = 5.0 * math.sin(t * 3.0)
    top = [(-20.0, 1668.0), (300.0, 1684.0), (540.0, 1690.0), (800.0, 1680.0), (1100.0, 1656.0)]
    bot = [(1100.0, 1766.0 + fl), (800.0, 1790.0 + fl), (540.0, 1800.0), (300.0, 1794.0), (-20.0, 1776.0)]
    K.poly(c, top + bot, RED)                                                                       # wound up to her chin
    K.band(c, [(-20.0, 1724.0), (300.0, 1740.0), (540.0, 1745.0), (800.0, 1736.0), (1100.0, 1712.0)], INK, 3.0,
           seed=3, alpha=0.3)                                                                       # a fold


def draw_eyes(c, t):
    ft = FT0 + t
    tt = K.twos(t)
    K.fill(c, CU_FIELD)
    lx = _light_x(t)
    # the light on the snow behind them
    for half, a in ((300.0, 0.10), (210.0, 0.12), (120.0, 0.14)):
        K.poly(c, _slab(lx, half), AMBER, a)
    _cu_reeds(c, t)
    # their eyes follow the lantern: from the left, past, away to the right
    k = clamp((t - T_LIGHT[0] + 0.25) / (T_LIGHT[1] - T_LIGHT[0] + 0.3))
    look_m = (lerp(-0.75, 0.85, ease("inout", k)), 0.1)
    kg = clamp((t - T_LIGHT[0] + 0.05) / (T_LIGHT[1] - T_LIGHT[0] + 0.3))
    look_g = (lerp(-0.7, 0.8, ease("inout", kg)), -0.05)
    lid_g = 1.0
    if 6.78 <= tt < 6.94:                      # the girl blinks once the light has gone by
        lid_g = abs(math.cos(math.pi * (tt - 6.78) / 0.16))
    _girl_lower(c, t)
    for who, at, look, lid, fear in (("mother", EYES_M, look_m, 1.0, 0.75), ("girl", EYES_G, look_g, lid_g, 0.9)):
        F.eyes(c, who, at, EYE_S, look=look, lid=lid, fear=fear, edge=STEEL, t=ft)
        # the lantern's light on them: the whites go warm inside the slab, a warm wash on the face
        c.save()
        c.new_path()
        D_ = _slab(lx, 170.0)
        c.move_to(*D_[0])
        for p in D_[1:]:
            c.line_to(*p)
        c.close_path()
        c.clip()
        F.eyes(c, who, at, EYE_S, look=look, lid=lid, fear=fear, edge=STEEL, t=ft, light=(AMBER, 0.55))
        y0, y1 = at[1] - 250.0 * EYE_S, at[1] + 260.0 * EYE_S
        c.restore()
        if who == "girl":
            y1 = 1940.0
        for half, a in ((240.0, 0.06), (150.0, 0.08)):
            c.save()
            c.new_path()
            c.rectangle(-20.0, y0, 1120.0, y1 - y0)
            c.clip()
            K.poly(c, _slab(lx, half), AMBER, a)
            c.restore()
    # her mitten over the girl's mouth (the mother's hand, from the left)
    mg = (EYES_G[0] + 40.0, EYES_G[1] + 330.0)
    wrist, tip = (-160.0, mg[1] + 150.0), (mg[0] + 120.0, mg[1] - 10.0)
    for ox, oy in ((-3.0, 0.0), (3.0, 0.0), (0.0, -3.0), (0.0, 3.0)):          # cut out round its edge
        F.mitten(c, (wrist[0] + ox, wrist[1] + oy), (tip[0] + ox, tip[1] + oy), 1.35, rim=None, color=STEEL, edge=None,
                 thumb=0.7, curl=0.2)
    F.mitten(c, wrist, tip, 1.35, rim=PAPER, light=(0.8, -0.6), rim_w=8.0, thumb=0.7, curl=0.2, edge=STEEL)
    # her heart, through both of them
    L.heart_rings(c, (540.0, 900.0), t, T_HEART[0], T_HEART[1], bpm=HEART_BPM, alpha=0.3, r1=900.0, width=10.0)


# ============================================================================ 5. the far light; the step (9-11.5)
def cam_look(t):
    return L.dio(t, [(9.0, (10.5, 0.4, 296.0, 1.5, 3.0)), (11.5, (10.58, 0.38, 306.0, 1.5, 3.0))])


def _guard_look(t):
    """(state, pose, root u, root z) at the band's edge."""
    Fg = C.fig("guard")
    ks = L.kk(t, T_STEP[0], T_STEP[1] - T_STEP[0])
    kp = L.kk(t, T_STEP[0] - 0.05, 0.5)
    u = lerp(N_STOP, 0.5 * (N_CLOSE + N_BAND), kp)
    z = W.ICE_Z + W.SNOW_T
    # the right (near) boot swings from the last print onto the band, heel first
    un = lerp(GI[16][1], N_BAND, ks)
    zg = z if ks < 0.75 else lerp(z, W.ICE_Z, (ks - 0.75) / 0.25)
    lift = 0.085 * math.sin(math.pi * ks ** 0.8)
    pn = -15.0 * L.bump(ks, -0.3, 0.45) + 14.0 * L.bump(ks, 0.55, 1.08)
    pf = -12.0 * L.kk(t, T_STEP[0] + 0.22, 0.25)
    dip = 0.02 * L.bump(t, T_STEP[1] - 0.1, T_STEP[1] + 0.3) - 0.008 * L.bump(ks, 0.15, 0.75)
    st = dict(pelvis=(0.0, -Fg.leg * 0.965 + dip / M_G),
              feet={"near": ((un - u) / M_G, -(zg + lift - z) / M_G, pn), "far": ((N_CLOSE - u) / M_G, 0.0, pf)},
              phase=0.0, speed=0.0, run=0.0, stride=0.0)
    kr = L.kk(t, T_RAISE[0], T_RAISE[1] - T_RAISE[0])
    kd = L.kk(t, T_DOWN[0], T_DOWN[1] - T_DOWN[0]) * (1.0 - L.kk(t, T_UP[0], T_UP[1] - T_UP[0]))
    kw = L.bump(t, T_STEP[0] - 0.05, T_STEP[1] + 0.35)
    a1 = lerp(62.0, 142.0, kr) - 36.0 * kd - 20.0 * kw
    a2 = lerp(14.0, -12.0, kr) + 12.0 * kd
    head = lerp(-8.0, 9.0, kr) - 30.0 * kd - 18.0 * kw
    lean = lerp(7.0, 2.0, kr) + 10.0 * kd + 7.0 * kw
    sw = 4.0 * math.sin(2.6 * t) * (1.0 - 0.5 * kr) + 6.0 * L.bump(t, T_RAISE[0], T_RAISE[1] + 0.4)
    hold = C.hold_lantern(t, 1.0, sw, 1.0)
    pose = C.still_pose("guard", t=t, lean=lean, head=head, breathe=0.6,
                        arms={"near": ("ang", a1, a2), "far": ("ang", lerp(-3.0, 22.0, kw), lerp(10.0, 24.0, kw))},
                        hold={"near": hold})
    return st, pose, u, z


def draw_look(c, t):
    cam = cam_look(t)
    tt = K.twos(t)
    W.draw_river(c, cam, FT0 + t, reeds_on=False, trunk=False)
    L.river_woods(c, cam, t)
    L.reeds(c, cam)
    L.trail_notches(c, cam)
    W.draw_trunk_side(c, cam)
    st, pose, u, z = _guard_look(tt)
    d = L.RIVER_D_MIN
    L.ground_glow(c, cam, u + 0.35, d + 0.3, 1.15, 0.6, t, z=W.ICE_Z, seed=6, cut=True)
    r = 0.55 * cam.scale(d)
    j = L.draw_fig(c, cam, "guard", st, pose, u, z, d, under=lambda cc, jj: K.glow(cc, jj["flame"], r, 0.8, t, seed=7))
    L.breath(c, j, "guard", t, rate=0.85, seed=73, strength=0.85)
    K.sight_line(c, j["eye"], L.far_window(cam), t, T_SIGHT, color=PAPER, dur=0.5, off=T_DOWN[0] + 0.05, r=6.0,
                 gap=22.0, head=24.0)


# ============================================================================ 6. she half rises (11.5-12.5)
def cam_rise(t):
    return L.dio(t, [(11.5, (-0.92, 1.18, 520.0, 2.4, 6.0)), (12.5, (-0.97, 1.2, 545.0, 2.4, 6.0))])


def _girl_mouth(cam, t):
    """Where the girl's mouth is in frame px (her figure drawn to a scratch pixel for its joints)."""
    cc = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    st, pose = _girl_rise(t)
    return L.draw_fig(cc, cam, "girl", st, pose, L.GIRL_U, W.land_z(L.GIRL_U), L.GIRL_D, rim=None)["mouth"]


def _mother_rise(t, cam):
    """Her near mitten over the girl's mouth (as in the close-up) until the mitten goes out toward
    him (T_MITT); the far mitten comes up to her own mouth on the gasp."""
    Fm = C.fig("mother")
    m = C.M_PER_UNIT["mother"]
    kr = L.kk(t, T_RISE[0], T_RISE[1] - T_RISE[0])
    km = L.kk(t, T_MITT[0], T_MITT[1] - T_MITT[0])
    kg = L.kk(t, T_GASP - 0.1, 0.15)
    jolt = 0.035 * L.bump(t, T_GASP - 0.03, T_GASP + 0.2)
    drop = lerp(0.52, 0.2, kr) - jolt
    st = dict(pelvis=(0.0, -Fm.leg * 0.965 + drop / m),
              feet={"near": (0.15 / m, 0.0, 0.0), "far": (-0.17 / m, 0.0, lerp(38.0, 16.0, kr))},
              phase=0.0, speed=0.0, run=0.0, stride=0.0, skirt=True)
    lean = lerp(40.0, 14.0, kr) + 4.0 * km
    # the near wrist: just behind the girl's mouth (figure units from her root), then out ahead
    at = cam.px(L.HIDE_U, W.land_z(L.HIDE_U), L.HIDE_D)
    s = C.scale("mother", cam.scale(L.HIDE_D))
    sg = cam.scale(L.GIRL_D)
    gm = _girl_mouth(cam, t)
    w0 = ((gm[0] - 0.06 * sg - at[0]) / s, (gm[1] + 0.035 * sg - at[1]) / s)
    q = pd._rot(Fm.shoulder, lean)
    sh = (st["pelvis"][0] + q[0], st["pelvis"][1] + q[1])
    a1, a2 = math.radians(80.0 + lean), math.radians(84.0 + lean)
    el = (sh[0] + math.sin(a1) * Fm.upper, sh[1] + math.cos(a1) * Fm.upper)
    w1 = (el[0] + math.sin(a2) * Fm.fore, el[1] + math.cos(a2) * Fm.fore)
    arms = {"near": ("ik", (lerp(w0[0], w1[0], km), lerp(w0[1], w1[1], km) - 0.04 / m * math.sin(math.pi * km))),
            "far": ("ang", lerp(-28.0, 22.0, kg), lerp(24.0, 138.0, kg))}
    pose = C.still_pose("mother", t=t, lean=lean, head=lerp(-4.0, 7.0, kr) + 30.0 * jolt, arms=arms, breathe=0.0)
    return st, pose


def _girl_rise(t):
    Fg = C.fig("girl")
    m = C.M_PER_UNIT["girl"]
    st = dict(pelvis=(0.0, -Fg.leg * 0.965 + 0.25 / m),
              feet={"near": (0.1 / m, 0.0, 0.0), "far": (-0.1 / m, 0.0, 20.0)},
              phase=0.0, speed=0.0, run=0.0, stride=0.0, skirt=True)
    look = L.kk(t, T_RISE[0] + 0.1, 0.25)
    pose = C.still_pose("girl", t=t, lean=lerp(24.0, 16.0, look), head=lerp(-4.0, 10.0, look), breathe=0.0,
                        arms={"near": ("ang", 48.0, 70.0), "far": ("ang", 40.0, 76.0)})
    return st, pose


def draw_rise(c, t):
    cam = cam_rise(t)
    tt = K.twos(t)
    W.draw_river(c, cam, FT0 + t, trunk=False, reeds_on=False)
    L.river_woods(c, cam, t)
    L.trail_notches(c, cam)
    L.reeds(c, cam, far=2.0)
    hide = L.hide_reeds()
    stir = tt if T_RISE[0] <= tt else None
    L.reeds_rows(c, cam, [r for r in hide if r[1] >= L.HIDE_D + 0.05], t=stir)
    st, pose = _mother_rise(tt, cam)
    mz = W.land_z(L.HIDE_U)
    L.draw_fig(c, cam, "mother", st, pose, L.HIDE_U, mz, L.HIDE_D, rim=PAPER, parts=C.PARTS[:-1])
    L.reeds_rows(c, cam, [r for r in hide if L.GIRL_D + 0.02 <= r[1] < L.HIDE_D + 0.05], t=stir)
    gst, gpose = _girl_rise(tt)
    L.draw_fig(c, cam, "girl", gst, gpose, L.GIRL_U, W.land_z(L.GIRL_U), L.GIRL_D, rim=PAPER)
    # her near arm reaches round the girl (over her mouth), so it lies over her
    L.draw_fig(c, cam, "mother", st, pose, L.HIDE_U, mz, L.HIDE_D, rim=PAPER, parts=("near_arm",))
    L.reeds_rows(c, cam, [r for r in hide if r[1] < L.GIRL_D + 0.02], rim=True, t=stir)
    W.draw_trunk_side(c, cam)


# ============================================================================ 7. his boot on the black ice (12.5-14)
BOOT_G_L = 0.30                         # his boot's sole (m): faces.boot's guard sole spans 302 units
BOOT_G_M = BOOT_G_L / 302.0
BOOT_G_MID = 55.0                       # the sole's middle, boot units from faces.boot's origin
D_BOOT = 0.06                           # the boot just behind the cut (a close-up's cheat: in front of it, really)
HEEL_U = N_BAND - (BOOT_G_MID + 96.0) * BOOT_G_M + 0.025    # where the crack starts: under his heel
_COAT_UP = ((-130.0, -630.0), (120.0, -630.0), (96.0, -2600.0), (-150.0, -2600.0))   # the greatcoat on up


def cam_boot(t):
    """Low on the ice at the band's edge, close on his right boot; a slow push in."""
    k = L.kk(t, 12.5, 1.5, "out")
    ppm = lerp(1420.0, 1500.0, k)
    top_y = 1380.0
    z0 = W.ICE_Z + (top_y - 960.0) / ppm
    u0 = lerp(10.27, 10.26, k)
    return W.Dio(u0, z0, ppm, eye=W.ICE_Z + 0.5, D=2.0)


@lru_cache(maxsize=1)
def _crack_trees():
    """The crack, in metres on the ice's surface (u, d): from under his heel out ahead under the
    boot toward the middle of the band, a branch back toward the band's edge, one to the cut."""
    o = (HEEL_U, D_BOOT + 0.015)
    main = K.crack_tree(o, 0.8, seed=71, heading=14.0, depth=2, jag=0.3, segs=8)
    back = K.crack_tree(o, 0.24, seed=72, heading=150.0, depth=1, jag=0.32, segs=6)
    near = ((((o[0], o[1]), (o[0] - 0.006, o[1] * 0.55), (o[0] + 0.004, 0.0)), 0.0, 1.0),)
    return main, back, near


def _face_crack(cam, u_top):
    """The crack down the band's cut face (the thin slab) from where the near branch meets it."""
    return [cam.px(u_top + 0.008 * K._sn(i, 75) + 0.006 * (i / 5.0), W.ICE_Z - W.THIN_T * 0.98 * i / 5.0, 0.0)
            for i in range(6)]


def _coat_up(c, at, s):
    """His greatcoat going on up out of the frame above the boot's hem (faces.boot's frame)."""
    c.save()
    c.translate(*at)
    c.scale(s, s)
    pts = list(_COAT_UP)
    c.save()
    c.translate(0.8 * 4.0 / s, -0.6 * 4.0 / s)
    K.poly(c, pts, PAPER)
    c.restore()
    K.poly(c, pts, INK)
    c.restore()


def draw_boot(c, t):
    cam = cam_boot(t)
    tt = K.twos(t)
    K.fill(c, NIGHT)
    K.stars(c, FT0 + t, y1=cam.horizon_y() - 30.0)
    W.draw_river(c, cam, FT0 + t, reeds_on=False, trunk=False, sky=False)
    # his lantern's pool on the ice round his boot (the lantern's up in his hand, out of the frame)
    L.ground_glow(c, cam, N_BAND - 0.05, 0.45, 0.6, 0.75, t, z=W.ICE_Z, seed=8)
    # the crack: out over the surface from his heel, and down the cut's face
    g = ease("out3", clamp((t - T_CRACK[0]) / (T_CRACK[1] - T_CRACK[0])))
    w = max(1.6, 0.0028 * cam.ppm)
    if g > 0.0:
        main, back, near = _crack_trees()
        xf = lambda p: cam.px(p[0], W.ICE_Z, p[1])
        K.crack(c, main, g, PAPER, width=w, seed=11, xf=xf)
        K.crack(c, back, clamp(g * 1.4 - 0.25), PAPER, width=w * 0.8, seed=12, xf=xf)
        K.crack(c, near, clamp(g * 4.0), PAPER, width=w * 0.9, seed=13, xf=xf)
        gf = clamp(g * 3.0 - 0.6)
        if gf > 0.0:
            face = _face_crack(cam, near[0][0][-1][0])
            n_ = max(2, int(round(1 + gf * (len(face) - 1))))
            K.band(c, face[:n_], PAPER, w * 0.85, seed=14, taper=(1.0, 0.3))
    # his right boot on the band, the greatcoat over it
    sc = cam.scale(D_BOOT) * BOOT_G_M
    at = cam.px(N_BAND - BOOT_G_MID * BOOT_G_M, W.ICE_Z, D_BOOT)
    at = (at[0], at[1] + 1.5 * L.bump(tt, 12.66, 12.9))      # his weight settles
    F.boot(c, at, sc, who="guard", pitch=0.0, rim=PAPER, light=(0.8, -0.6), rim_w=4.0, hem=True)
    _coat_up(c, at, sc)


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        shot = L.shot_of(t, SHOTS)
        {"out": draw_out, "pass": draw_pass, "eyes": draw_eyes, "end": draw_end, "look": draw_look,
         "rise": draw_rise, "boot": draw_boot}[shot](c, t)


# ============================================================================ cues
def _step_times(t0, t1):
    wk = _walker()
    return [tf for (tf, side, fx) in L.step_times(wk, t0, t1)]


def cues(T):
    out = []
    out.append(Cue(0.0, "river_under_ice", gain_db=-24, dur=14.0, pan=0.0,
                   dc="the river under the ice: a low, steady, muffled rush of deep water, all through the scene"))
    out.append(Cue(0.0, "wind_open", gain_db=-27, dur=3.0, pan=0.0,
                   dc="the cold wind at the woods' edge; branches creak above"))
    for tf in _step_times(0.0, 2.95):
        n = gu_n(tf)
        x = cam_out(tf).px(n, W.land_z(n), gu_d_out(n))[0]
        on_slope = n > -W.BANK
        out.append(Cue(tf, "step_guard_hobnail", gain_db=-15 if tf < T_FIND[0] or tf > T_FOLLOW else -18,
                       pan=L.pan_x(x),
                       dc="the guard's heavy hobnailed boot in the snow, hurrying: a hard crunch"
                       + ("; sliding a little down the bank" if on_slope else "")))
    out.append(Cue(0.15, "lantern_creak", gain_db=-18, pan=-0.3,
                   dc="the lantern held high swings on its wire bail: a creak, the glass rattling"))
    out.append(Cue(0.0, "guard_breath_heavy", gain_db=-20, dur=3.0, pan=-0.2,
                   dc="the guard's breath, heavy and quick through his moustache as he hurries"))
    out.append(Cue(T_FIND[0], "lantern_swing_down", gain_db=-19, pan=0.0,
                   dc="he swings the lantern down to the snow: the bail clanks, the flame gutters"))
    out.append(Cue(T_FIND[0] + 0.35, "guard_sniff", gain_db=-24, pan=0.0,
                   dc="a short grunt through his nose: he has found the trail"))
    out.append(Cue(T_FOLLOW + 0.1, "lantern_creak", gain_db=-20, pan=0.2,
                   dc="the lantern swings out in front of him again: a creak"))
    for tf in _step_times(3.0, 4.95):
        cam = cam_pass(tf)
        n = gu_n(tf)
        x = cam.px((gu_x(n), n))[0]
        out.append(Cue(tf, "step_guard_ice", gain_db=-20, pan=L.pan_x(x),
                       dc="his hobnails on the thin snow over the ice: a hard, quick crunch with a hollow ring under it"))
    out.append(Cue(3.6, "lantern_creak", gain_db=-22, pan=0.2, dc="the lantern's bail creaks as he walks"))
    out.append(Cue(4.5, "lantern_creak", gain_db=-23, pan=0.3, dc="the lantern's bail creaks again, moving away"))
    for i, tb in enumerate(L.heart_beats(T_HEART[0], T_HEART[1] - 0.05, HEART_BPM)):
        out.append(Cue(tb, "heartbeat", gain_db=-8, pan=0.0,
                       dc="her heartbeat, close and loud: lub-dub at 104 bpm, one beat per cue (the dub 0.24 s after)"))
    out.append(Cue(5.0, "steps_passing", gain_db=-24, dur=2.0, pan=-0.4,
                   dc="his steps on the ice passing a few metres away, left to right, going on; the lantern's creak"))
    out.append(Cue(5.0, "reed_tick", gain_db=-34, pan=0.3, dc="a dry reed ticks against another in the wind: nothing else"))
    for tf in _step_times(7.0, T_STOP + 0.05):
        cam = cam_end(tf)
        n = gu_n(tf)
        x = cam.px((gu_x(n), n))[0]
        out.append(Cue(tf, "step_guard_ice", gain_db=-21, pan=L.pan_x(x),
                       dc="his hobnails on the snow over the ice, slowing"))
    out.append(Cue(T_STOP, "boots_stop", gain_db=-20, pan=0.0,
                   dc="he stops: a scrape of hobnails, his boots planted together"))
    out.append(Cue(T_OVER[0], "lantern_creak", gain_db=-20, pan=0.05,
                   dc="the lantern held out over the black band swings and settles on its bail"))
    out.append(Cue(T_STOP + 0.2, "silence_wind", gain_db=-30, dur=2.6, pan=0.0,
                   dc="nothing but a thin wind over the open river, and the river's rush under the slab"))
    out.append(Cue(T_RAISE[0], "lantern_raise", gain_db=-19, pan=-0.35,
                   dc="he lifts the lantern high: the bail creaks, the glass chimes"))
    out.append(Cue(9.0, "guard_breath", gain_db=-24, dur=2.5, pan=-0.35,
                   dc="the guard's breath slowing, heavy, steaming in the cold"))
    out.append(Cue(T_SIGHT, "far_dog", gain_db=-36, pan=0.6,
                   dc="very far across the river, from the farmhouse, a dog barks twice, faint"))
    out.append(Cue(T_STEP[1], "step_bare_ice", gain_db=-16, pan=-0.2,
                   dc="his hobnailed boot set down on bare black ice: a hard, ringing click, then a faint tick"))
    out.append(Cue(T_RISE[0], "reeds_rustle", gain_db=-20, pan=-0.1,
                   dc="dry frozen reeds rattle as she half rises among them"))
    out.append(Cue(T_GASP, "gasp_stifled", gain_db=-18, pan=-0.1,
                   dc="the mother's sharp intake of breath, smothered at once by her mitten"))
    out.append(Cue(12.75, "ice_tick", gain_db=-26, pan=0.1,
                   dc="his weight settles on the band: a tiny dry tick in the ice"))
    out.append(Cue(T_CRACK[0], "ice_sing", gain_db=-12, dur=1.3, pan=0.1,
                   dc="the ice sings: a long dispersive 'pew', a falling metallic whistle running out through the thin "
                      "slab and away under the river"))
    return out
