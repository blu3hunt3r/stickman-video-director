"""s06 FALSE TRAIL (78-94): out to the black band; backward, boot into print; onto the trunk; into
the reeds; the lie on the page.

  0.0-4.0   THE PAGE, straight down on the trail's line: carrying the girl, she walks north across the
            white ice (up the frame), her moon shadow trailing behind her. The shot opens with her
            already part way out (prints 0-10 down behind her, from the bank); she lays 11-18, one
            every 0.45 s (1.34 m/s), slowing for the last; the camera eases after her. She stops with
            her feet in prints 17 and 18 at the black band's edge (3.55) and stands.
  4.0-6.0   CU, PROFILE AT BOOT LEVEL, the river section (the trail lies on the cut): her two felt
            boots in their prints on the cut's snow, the white slab under them, the black water under
            that. Her right boot lifts straight up out of print 18 (4.3-4.45), leaving its hollow;
            it travels back past the other boot (4.6-5.1), the camera following; it hovers and finds
            print 16 (5.1-5.35) and lowers into its own hollow (5.35-5.55): a perfect fit (5.55), a
            faint ring. Hold (one soft crunch, deliberately quiet).
  6.0-10.0  THE PAGE, closer: she walks backward in her own prints toward the bank: left 17->15,
            right 16->14, left 15->13, right 14->12 (landing 6.95, 7.75, 8.55, 9.35); each reused
            print flashes with a small ring. Beside the trunk she steps sideways, west, up onto it
            (9.5-9.75) and turns on it to face the bank (9.72-9.97): no print.
  10.0-11.0 PROFILE, out on the ice: on the trunk, the trail's hollows in the cut beside her, she
            walks along it toward the bank (left), balancing, an arm out, the girl clinging.
  11.0-13.0 PROFILE, the bank: the last step up the trunk's end (11.0-11.28); down off its far side
            (11.32-11.85); a step into the reeds (11.85-12.05); she crouches (12.05-12.4); the girl
            slides off her back to her side (12.25-12.65); she pulls her coat round her (12.5-12.9).
            Reeds in front of them; no breath now.
  13.0-16.0 THE PAGE, rising from the reeds (13.0-15.0) to the whole lie: one line of prints out of
            the woods, up the bank and straight out across the ice to the black band; the bare trunk
            beside it; in the reeds two pairs of tiny eyes; at the bottom of the frame the guard's
            lantern pool comes out of the trees along the path (his clock: n -8.9 -> -5.3). The
            eyes go to it. Last frame: that view.

Handoffs: s05 ends on her eye (CU); s06 opens on the page. s06's last frame is the rising page's
end, Plan(12.0, 3.0, 74): the whole trail, the trunk, the eyes at W.HIDE (frame ~(207, 1367)),
the lantern's pool at the bottom (guard at map (13.6, -5.3), frame ~(659, 1575)); the trail's
end (13.31, 9.0) at ~(637, 516); s07 opens with him breaking out of the trees.
"""
import math
from functools import lru_cache

from engine import paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.thin_ice import cast as C, faces as F, kit as K, world as W
from films.thin_ice.scenes import _lib_s04_s07 as L

INK, NIGHT, SNOW, SHADOW, PAPER, AMBER = K.INK, K.NIGHT, K.SNOW, K.SHADOW, K.PAPER, K.AMBER
THIN, ICE, WATER, STEEL = K.THIN, K.ICE, K.WATER, K.STEEL
FT0 = 78.0                  # film time of the scene's first frame

# ---------------------------------------------------------------------------- beats (scene time)
SHOTS = ((0.0, "out"), (4.0, "boot"), (6.0, "back"), (10.0, "trunk"), (11.0, "bank"), (13.0, "lie"))
TRAIL = W.FALSE_TRAIL
T_LAND = {11: 0.28, 12: 0.73, 13: 1.18, 14: 1.63, 15: 2.08, 16: 2.53, 17: 3.0, 18: 3.55}   # prints laid
T_STOP = 3.55               # she stops at the band's edge, feet in prints 17 and 18
T_LIFT = (4.3, 4.45)        # her right boot lifts straight up out of print 18 (its hollow left)
T_CARRY = (4.6, 5.1)        # back past the other boot (the camera follows)
T_FIND = (5.1, 5.35)        # it hovers over print 16's hollow, finds it
T_LOWER = (5.35, 5.55)      # down into its own hollow
T_FIT = 5.55                # a perfect fit; hold
BACK = ((6.25, 6.95, "L", 17, 15), (7.05, 7.75, "R", 16, 14), (7.85, 8.55, "L", 15, 13),
        (8.65, 9.35, "R", 14, 12))           # the backtrack: (t0, t1, foot, from print, to print)
T_SIDE_L = (9.5, 9.75)      # her left foot steps sideways up onto the trunk
T_SIDE_R = (9.72, 9.97)     # her right foot follows; she turns to face the bank
T_TRUNK_WALK = 10.0         # along the trunk (profile)
T_STEP_UP = (11.0, 11.28)   # the bank: her last step up the trunk's end
T_DOWN_F = (11.32, 11.58)   # down off its far side: the far foot ...
T_DOWN_N = (11.6, 11.85)    # ... the near foot
T_INTO = (11.85, 12.05)     # a step into the reeds
T_CROUCH = (12.05, 12.4)    # she crouches
T_GIRL = (12.25, 12.65)     # the girl slides off her back to her side
T_WRAP = (12.5, 12.9)       # she pulls her coat round her
T_HUSH = 12.45              # no breath from here
T_RISE = (13.0, 15.0)       # the page rises
T_POOL = 14.35              # the lantern's pool comes into the frame at the bottom; the eyes go to it

# ---------------------------------------------------------------------------- places
LEAD = 0.3                  # her centre is this far behind the print a foot lands in (walking)
TRUNK_L = (W.TRUNK[0][0] + (5.92 - W.TRUNK[0][1]) / (W.TRUNK[1][1] - W.TRUNK[0][1]) * (W.TRUNK[1][0] - W.TRUNK[0][0]), 5.92)
TRUNK_R = (W.TRUNK[0][0] + (5.48 - W.TRUNK[0][1]) / (W.TRUNK[1][1] - W.TRUNK[0][1]) * (W.TRUNK[1][0] - W.TRUNK[0][0]), 5.48)
D_TRUNK = W.SECTION_X - 0.5 * (W.TRUNK[0][0] + W.TRUNK[1][0])     # the trunk's depth in the river view
U_TRUNK0 = 5.62             # her u on the trunk as the profile opens (where she stepped up)
HIDE_U, HIDE_D = L.HIDE_U, L.HIDE_D     # where she crouches in the profile, behind the trunk's end (a
GIRL_U, GIRL_D = L.GIRL_U, L.GIRL_D     # cheat: the page has them at W.HIDE); the girl, a little nearer

BEFORE = W.prints_before("s06")


def motion_blur(t, T):
    return 1


# ============================================================================ the walk out (the page)
@lru_cache(maxsize=1)
def _out_keys():
    """Her centre's n at each landing (Hermite keys, the last with zero speed)."""
    v = TRAIL[12][1] - TRAIL[11][1]
    ks = [(T_LAND[11] - 0.45, TRAIL[10][1] - LEAD)] + [(T_LAND[i], TRAIL[i][1] - LEAD) for i in range(11, 19)]
    tans = []
    for j, (tk, nk) in enumerate(ks):
        if j == len(ks) - 1:
            tans.append(0.0)
        elif j == 0:
            tans.append(v / 0.45)
        else:
            tans.append((ks[j + 1][1] - ks[j - 1][1]) / (ks[j + 1][0] - ks[j - 1][0]))
    return tuple(ks), tuple(tans)


def out_n(t):
    """Her centre's map n on the walk out."""
    ks, tans = _out_keys()
    if t <= ks[0][0]:
        return ks[0][1] + tans[0] * (t - ks[0][0])
    for (ta, na), (tb, nb), ma, mb in zip(ks, ks[1:], tans, tans[1:]):
        if t <= tb:
            h = tb - ta
            u = (t - ta) / h
            h00, h10 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u
            h01, h11 = -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
            return h00 * na + h10 * h * ma + h01 * nb + h11 * h * mb
    return ks[-1][1]


def _print_mid(i):
    return (TRAIL[i][0], TRAIL[i][1])


def out_feet(t):
    """Her two boots on the walk out: {side: (x, n, heading, lift)}; the planted one in the last
    print laid, the other swinging from the print behind to the next."""
    i = 10
    for k in range(11, 19):
        if t >= T_LAND[k]:
            i = k
    feet = {}
    side_i = "R" if i % 2 == 0 else "L"
    other = "L" if side_i == "R" else "R"
    pi = TRAIL[i]
    feet[side_i] = (pi[0], pi[1], pi[2], 0.0)
    if i >= 18:
        p = TRAIL[17]
        feet[other] = (p[0], p[1], p[2], 0.0)
        return feet
    t0 = T_LAND[i] if i >= 11 else T_LAND[11] - 0.45
    t1 = T_LAND[i + 1]
    a = ease("inout", clamp((t - t0 - 0.1 * (t1 - t0)) / (0.9 * (t1 - t0))))
    pa, pb = TRAIL[i - 1], TRAIL[i + 1]
    feet[other] = (lerp(pa[0], pb[0], a), lerp(pa[1], pb[1], a), lerp(pa[2], pb[2], a), math.sin(math.pi * a))
    return feet


def out_laid(t):
    return [p for i, p in enumerate(TRAIL) if i <= 10 or t >= T_LAND[i]]


def out_phase(t):
    """A stride phase for the figure from above (0.25 + i/2 as print i is laid)."""
    if t <= T_LAND[11]:
        return 0.25 + 5.5 - (T_LAND[11] - t) / 0.9
    for i in range(11, 18):
        if t <= T_LAND[i + 1]:
            return 0.25 + 0.5 * (i + (t - T_LAND[i]) / (T_LAND[i + 1] - T_LAND[i]))
    return 0.25 + 9.0


# ============================================================================ the backtrack (the page)
def _foot_at(print_i):
    p = TRAIL[print_i]
    return (p[0], p[1], p[2])


def back_feet(t):
    """{side: (x, n, heading, lift)} on the backtrack and the step onto the trunk."""
    cur = {"L": _foot_at(17), "R": _foot_at(16)}
    moving = None
    for (t0, t1, side, a, b) in BACK:
        if t >= t1:
            cur[side] = _foot_at(b)
        elif t > t0:
            k = ease("inout", (t - t0) / (t1 - t0))
            pa, pb = _foot_at(a), _foot_at(b)
            cur[side] = (lerp(pa[0], pb[0], k), lerp(pa[1], pb[1], k), lerp(pa[2], pb[2], k))
            moving = (side, math.sin(math.pi * k))
    out = {s: (v[0], v[1], v[2], 0.0) for s, v in cur.items()}
    if moving:
        s, lift = moving
        out[s] = out[s][:3] + (lift,)
    # sideways onto the trunk: left foot, then right; she pivots to face the bank
    kl = ease("inout", clamp((t - T_SIDE_L[0]) / (T_SIDE_L[1] - T_SIDE_L[0])))
    kr = ease("inout", clamp((t - T_SIDE_R[0]) / (T_SIDE_R[1] - T_SIDE_R[0])))
    if kl > 0.0:
        a = _foot_at(13)
        piv = clamp((t - T_SIDE_R[0]) / (T_SIDE_R[1] - T_SIDE_R[0]))
        out["L"] = (lerp(a[0], TRUNK_L[0], kl), lerp(a[1], TRUNK_L[1], kl), lerp(lerp(a[2], -130.0, kl), -172.0, piv),
                    math.sin(math.pi * kl) * 1.4)
    if kr > 0.0:
        a = _foot_at(12)
        out["R"] = (lerp(a[0], TRUNK_R[0], kr), lerp(a[1], TRUNK_R[1], kr), lerp(a[2], -175.0, kr),
                    math.sin(math.pi * kr) * 1.4)
    return out


def back_heading(t):
    """Her heading (degrees from north): north while she backs, turning west and round to face
    the bank as she steps onto the trunk."""
    return -180.0 * ease("inout", clamp((t - T_SIDE_L[0] - 0.05) / (T_SIDE_R[1] - T_SIDE_L[0] - 0.05)))


def back_phase(t):
    for k, (t0, t1, side, a, b) in enumerate(BACK):
        if t < t0:
            return 0.5 * k
        if t <= t1:
            return 0.5 * k + 0.5 * ease("inout", (t - t0) / (t1 - t0))
    return 2.0


# ============================================================================ the boot (profile CU)
SNOW_CU = 0.10              # the close-up's snow on the ice: deeper than the wide views' 5 cm, so the
SINK_CU = 0.07              # hollow her boot leaves reads as a boot's shape (a close-up's cheat)
CU_TOP = W.ICE_Z + SNOW_CU


def _boot_rest(i):
    """(u, z) of faces.boot's origin with the boot resting in print i (its sole in the hollow)."""
    return (TRAIL[i][1] - L.BOOT_MID * L.BOOT_M, CU_TOP - SINK_CU)


def near_boot(t):
    """Her right boot (near the camera, at the cut): (u, z, pitch) of faces.boot's origin. Straight
    up out of its print, back past the other boot, a hair too far, then exactly over its own hollow,
    straight down into it."""
    u18, z0 = _boot_rest(18)
    u16, _ = _boot_rest(16)
    lift = L.kk(t, T_LIFT[0], T_LIFT[1] - T_LIFT[0], "out")
    carry = L.kk(t, T_CARRY[0], T_CARRY[1] - T_CARRY[0])
    lower = L.kk(t, T_LOWER[0], T_LOWER[1] - T_LOWER[0])
    over = 0.022 * L.bump(t, T_FIND[0] - 0.08, T_FIND[1] - 0.02)
    u = lerp(u18, u16, carry) - over
    h = 0.13 * lift + 0.035 * L.bump(t, T_CARRY[0], T_CARRY[1]) - 0.03 * L.kk(t, T_FIND[0] - 0.05, 0.2) - 0.10 * lower
    if t >= T_LOWER[1]:
        h = 0.0
    pitch = -5.0 * L.kk(t, T_LIFT[0] + 0.05, 0.15) * (1.0 - L.kk(t, T_CARRY[1] - 0.12, 0.25))
    return u, z0 + h, pitch


def cam_boot(t):
    """Low on the cut, the boots on the snow above the white slab and the black water: holding on
    both boots, then following the right one back to its print (a slow push all through)."""
    k = L.kk(t, 4.0, 2.0)
    ppm = lerp(1150.0, 1250.0, k)
    u0 = lerp(8.69, TRAIL[16][1] + 0.03, L.kk(t, 4.5, 0.72))
    y_snow = lerp(760.0, 800.0, k)
    z0 = CU_TOP - (960.0 - y_snow) / ppm
    return W.Dio(u0, z0, ppm, CU_TOP + 0.95, 3.0)


def _hollow(cam, i):
    return L.notch_pts(cam, TRAIL[i][1], CU_TOP, SINK_CU)


def draw_boot(c, t):
    cam = cam_boot(t)
    W.draw_river(c, cam, t, trunk=False, reeds_on=False, far_trees=False)
    ns = [cam.u_at(-40.0) + (cam.u_at(1120.0) - cam.u_at(-40.0)) * i / 24.0 for i in range(25)]
    snow_band = [cam.px(n, CU_TOP) for n in ns] + [cam.px(n, W.ICE_Z) for n in ns[::-1]]
    # her left boot, planted in print 17 a hand's breadth behind the cut; the cut's snow in front
    # of its sole
    uf, zf = _boot_rest(17)
    at_f = cam.px(uf, zf, 0.1)
    s_f = cam.scale(0.1) * L.BOOT_M
    F.boot(c, at_f, s_f, "mother", 0.0, 1, rim=PAPER, rim_w=max(3.0, 4.0 * s_f))
    K.poly(c, snow_band, SNOW)
    # the hollows in the cut's snow: print 18 (left behind), 16 (waiting), 14
    for i in (14, 16, 18):
        K.poly(c, _hollow(cam, i), SHADOW)
    # the fit: a faint ring on the snow round the boot, behind it
    a = (t - T_FIT) / 0.6
    if 0.0 <= a < 1.0:
        r = lerp(0.16, 0.42, ease("out3", a)) * cam.ppm
        p = cam.px(TRAIL[16][1], CU_TOP, 0.05)
        K.band(c, [(p[0] + r * math.cos(th), p[1] + 0.13 * r * math.sin(th))
                   for th in [math.pi + math.pi * i / 24.0 for i in range(25)]], PAPER, max(2.0, 5.0 * (1.0 - a)),
               seed=7, alpha=0.8 * (1.0 - a))
    # her right boot
    s0 = cam.ppm * L.BOOT_M
    un, zn, pitch = near_boot(t)
    F.boot(c, cam.px(un, zn, 0.0), s0, "mother", pitch, 1, rim=PAPER, rim_w=max(3.0, 4.0 * s0))
    # the fit: its sole's seam glints round the hollow; a few grains jump
    a = (t - T_FIT) / 0.4
    if 0.0 <= a < 1.0:
        pts = _hollow(cam, 16)
        seam = [q for q in pts if q[1] > cam.px(0.0, CU_TOP - 0.004, 0.0)[1]]
        if len(seam) >= 2:
            K.band(c, seam, PAPER, max(2.0, 4.0 * (1.0 - a)), seed=3, alpha=0.9 * (1.0 - a) ** 1.4)
    _grains(c, cam, t, T_FIT - 0.02, [TRAIL[16][1] - 0.15, TRAIL[16][1] + 0.15])


def _grains(c, cam, t, t0, us, life=0.45):
    """A few grains of snow jumping off the hollow's lips as the boot settles (deliberately small)."""
    a = (t - t0) / life
    if not 0.0 <= a < 1.0:
        return
    tt = a * life
    for j, u in enumerate(us):
        for i in range(4):
            sgn = -1.0 if j == 0 else 1.0
            vx = sgn * (0.12 + 0.18 * hash01(j, i, 1))
            vz = 0.25 + 0.35 * hash01(j, i, 2)
            p = cam.px(u + vx * tt, CU_TOP + vz * tt - 4.9 * tt * tt, 0.0)
            r = cam.ppm * (0.004 + 0.004 * hash01(j, i, 3))
            if p[1] < cam.px(u, CU_TOP, 0.0)[1] + 2.0:
                K.dot(c, p, r, SNOW if i % 2 else PAPER, seed=j * 7 + i, alpha=0.95 * (1.0 - a))


# ============================================================================ on the trunk (profile)
@lru_cache(maxsize=1)
def _trunk_walk():
    return L.walker("mother", [(9.0, 0.0), (9.95, 0.6), (11.2, 0.6)], 0.34, lift=0.07, key="s06_trunk")


def _trunk_u(t):
    wk = _trunk_walk()
    return U_TRUNK0 - (wk.x(t) - wk.x(T_TRUNK_WALK)) * C.M_PER_UNIT["mother"]


def cam_trunk(t):
    """Out on the ice, the trunk under her feet and the trail's hollows in the cut beside her; she
    walks into the frame's space (left), the camera easing after her."""
    return L.dio(t, [(10.0, (5.3, 0.62, 330.0, 2.2, 6.0)), (11.0, (4.86, 0.62, 336.0, 2.2, 6.0))])


def _balance_pose(t, st):
    """Walking the trunk: small steps, looking down at her feet, her near arm out behind her for
    balance (it hunts), her far arm still under the girl's knee; her body wobbles."""
    wob = 3.0 * math.sin(t * 5.3) + 1.5 * math.sin(t * 8.9 + 1.0)
    lean = 7.0 + wob
    a1 = -42.0 + 14.0 * math.sin(t * 4.1 + 0.4)
    arms = {"near": ("ang", a1 - lean, 22.0 + 10.0 * math.sin(t * 3.3)), "far": C.carry_arms(t)["far"]}
    return C.walk_pose("mother", st, t=t, lean=lean, head=-13.0 + 2.0 * math.sin(t * 2.0), arms=arms, amp=0.4)


def draw_trunk(c, t):
    cam = cam_trunk(t)
    tt = K.twos(t)
    L.river(c, cam, t)
    L.trail_notches(c, cam)
    wk = _trunk_walk()
    st = wk.state(tt)
    u = _trunk_u(tt)
    pose = _balance_pose(tt, st)
    s = C.scale("mother", cam.scale(D_TRUNK))
    at = cam.px(u, W.trunk_top_z(u), D_TRUNK)
    gp = C.carried_pose(tt, -0.25, bounce=0.0)
    gp = pd.Pose(lean=gp.lean - 4.0 + 2.0 * math.sin(tt * 5.3), head=-8.0, crouch=0.0, arms=gp.arms, springs=gp.springs)
    jm, jg = L.piggyback(c, L.mirror_state(st), pose, at, s, -1, t=tt, rim=PAPER, edge=SNOW, girl_pose=gp)
    L.breath(c, jm, "mother", t, rate=0.55, seed=61, facing=-1, strength=0.8)
    L.breath(c, jg, "girl", t, rate=0.7, seed=62, facing=-1, strength=0.6, phase=0.4)


# ============================================================================ into the reeds (profile)
def _ground(u, on_trunk):
    return W.trunk_top_z(u) if on_trunk else W.land_z(u)


# her feet on the bank: keyframes per foot (t, u, on the trunk?, d); the foot lifts between keys
_FEET_BANK = {
    "near": ((11.0, -0.62, True, D_TRUNK), (11.28, -1.08, True, D_TRUNK), (11.6, -1.08, True, D_TRUNK),
             (11.85, -1.45, False, 1.85), (12.05, -1.45, False, 1.95)),
    "far": ((11.0, -0.85, True, D_TRUNK), (11.32, -0.85, True, D_TRUNK), (11.58, -1.25, False, 1.55),
            (11.85, -1.25, False, 1.55), (12.05, -1.0, False, 2.05)),
}


def _foot_bank(side, t):
    """(u, z, d, pitch) of a foot at t, lifting between its keys."""
    ks = _FEET_BANK[side]
    if t <= ks[0][0]:
        k0 = ks[0]
        if side == "near":                       # mid-swing as the shot opens
            return (k0[1], _ground(k0[1], k0[2]) + 0.06, k0[3], -10.0)
        return (k0[1], _ground(k0[1], k0[2]), k0[3], 0.0)
    for a, b in zip(ks, ks[1:]):
        if t <= b[0]:
            if abs(a[1] - b[1]) < 1e-6 and a[2] == b[2]:
                return (a[1], _ground(a[1], a[2]), a[3], 0.0)
            k = ease("inout", (t - a[0]) / (b[0] - a[0]))
            u = lerp(a[1], b[1], k)
            za, zb = _ground(a[1], a[2]), _ground(b[1], b[2])
            z = lerp(za, zb, k) + (0.1 + 0.6 * max(0.0, za - zb) * 0.3) * math.sin(math.pi * k)
            if side == "near" and a[0] == 11.0:
                z += 0.06 * (1.0 - k)
            return (u, z, lerp(a[3], b[3], k), -14.0 * math.sin(math.pi * k))
    b = ks[-1]
    return (b[1], _ground(b[1], b[2]), b[3], 0.0)


def _mother_bank(t):
    """(state, pose, root (u, z, d), carrying) on the bank, figure time t."""
    fn, ff = _foot_bank("near", t), _foot_bank("far", t)
    k_c = L.kk(t, T_CROUCH[0], T_CROUCH[1] - T_CROUCH[0])
    u = 0.5 * (fn[0] + ff[0])
    if t >= T_INTO[1]:
        u = lerp(u, HIDE_U, k_c)
    d = lerp(0.5 * (fn[2] + ff[2]), HIDE_D, k_c)
    z = max(fn[1], ff[1]) - 0.35 * abs(fn[1] - ff[1])
    if fn[2] > 1.2 and ff[2] > 1.2:
        z = 0.5 * (fn[1] + ff[1])
    m = C.M_PER_UNIT["mother"]
    Fm = C.fig("mother")
    feet = {}
    for side, (fu, fz, fd, fp) in (("near", fn), ("far", ff)):
        feet[side] = ((fu - u) / m, -(fz - z) / m, fp)          # states are in world x
    # the pelvis: lower as she steps down, deep in the crouch
    step_dn = L.bump(t, T_DOWN_F[0], T_DOWN_N[1]) * 0.08
    drop = step_dn + 0.42 * k_c
    st = dict(pelvis=(0.0, -Fm.leg * 0.965 + drop / m), feet=feet, phase=0.0, speed=0.0, run=0.0, stride=0.0,
              skirt=True)
    if k_c > 0.0:
        # kneeling: her back foot's toe digs in, her heel up
        n_, f_ = st["feet"]["near"], st["feet"]["far"]
        st["feet"] = {"near": n_, "far": (f_[0], f_[1], lerp(f_[2], 38.0, k_c))}
    k_g = L.kk(t, T_GIRL[0], 0.2)
    k_w = L.kk(t, T_WRAP[0], T_WRAP[1] - T_WRAP[0])
    watch = L.kk(t, 12.75, 0.25)
    look_dn = L.bump(t, 11.25, 12.05)
    lean = lerp(lerp(8.0, 14.0, look_dn), 30.0, k_c) - 6.0 * watch
    head = -14.0 * look_dn - 10.0 * k_c * (1.0 - watch) + 5.0 * watch
    carry = C.carry_arms(t)
    if t < T_GIRL[0]:
        arms = carry
        return st, C.still_pose("mother", t=t, arms=arms, lean=lean, head=head, breathe=0.5), (u, z, d), True
    # the girl comes down: her hands let go; then her near arm goes back round the girl, her far
    # hand to the ground
    near_rest = (lerp(carry["near"][1][0], 60.0, k_g), lerp(carry["near"][1][1], 10.0, k_g))
    far = (lerp(carry["far"][1][0], 92.0, k_g), lerp(carry["far"][1][1], 50.0, k_g))
    arms = {"near": ("rel", near_rest), "far": ("rel", far)}
    pose = C.still_pose("mother", t=t, arms=arms, lean=lean, head=head, breathe=0.25, gaze=-0.4 * watch)
    return st, pose, (u, z, d), t < T_GIRL[0]


def cam_bank(t):
    """The bank by the root plate: the trunk's end, the reeds; she comes down behind the trunk and
    the two of them crouch there, peering over it (a slow push in)."""
    return L.dio(t, [(11.0, (-0.9, 1.28, 480.0, 2.5, 6.0)), (13.0, (-1.06, 1.2, 540.0, 2.5, 6.0))])


def _wrap_point(jg, g_s, k, sh):
    """Where her hand takes the coat's edge round the girl (frame px): from her own shoulder, round
    behind the girl's back at the girl's shoulder height (below her head)."""
    gx = max(jg["neck"][0], jg["pelvis"][0], jg.get("back", jg["neck"])[0]) + 58.0 * g_s
    gy = jg["neck"][1] + 52.0 * g_s
    return (lerp(sh[0] + 30.0 * g_s, gx, k), lerp(sh[1] + 20.0 * g_s, gy, k))


def _rel_from_frame(p, st, pose, at, s, facing=-1):
    """The pelvis-frame point (figure units) that cast.draw puts at frame p (inverse frame_point)."""
    q0 = ((p[0] - at[0]) / s) * facing
    q1 = (p[1] - at[1]) / s - st["pelvis"][1] - pose.crouch
    return pd._rot((q0, q1), -pose.lean)


def _coat_wrap(c, jm, jg, g_s, k, ground_y):
    """Her coat pulled round the girl: a fold of it from her shoulder over the girl's back and down
    to the snow (the girl's head and scarf stay out above it), her mitten holding its edge."""
    if k <= 0.0:
        return
    sh, pel = jm["shoulder_near"], jm["pelvis"]
    s = jm["scale"]
    hand = _wrap_point(jg, g_s, k, sh)
    mid = (lerp(sh[0], hand[0], 0.5), lerp(sh[1], hand[1], 0.5) + 4.0 * s * k)
    h = ground_y - hand[1]
    # the fold hangs off her hand in a soft curve over the girl's back and tucks in at the snow
    side = [(hand[0] + 9.0 * s * k, hand[1] + 0.22 * h), (hand[0] + 7.0 * s * k, hand[1] + 0.55 * h),
            (hand[0] - 2.0 * s * k, hand[1] + 0.85 * h), (hand[0] - 9.0 * s * k, ground_y)]
    pts = [sh, mid, hand] + side + [(pel[0], ground_y), pel]
    rw = max(2.0, 4.0 * s)
    K.poly(c, [(x + L.LIGHT[0] * rw, y + L.LIGHT[1] * rw) for x, y in pts], PAPER)
    K.poly(c, pts, INK)
    F.mitten(c, (lerp(mid[0], hand[0], 0.55), lerp(mid[1], hand[1], 0.55)), (hand[0] + 10.0 * s, hand[1] + 26.0 * s),
             s * 0.2, rim=PAPER, rim_w=max(2.0, 3.0 * s), sleeve=False, edge=None, curl=0.6)


def draw_bank(c, t):
    cam = cam_bank(t)
    tt = K.twos(t)
    st, pose, (u, z, d), carrying = _mother_bank(tt)
    behind = d > D_TRUNK + 0.15
    W.draw_river(c, cam, t, trunk=False, reeds_on=False)
    L.river_woods(c, cam, t)
    L.trail_notches(c, cam)
    L.reeds(c, cam, far=2.0)
    hide = L.hide_reeds()
    L.reeds_rows(c, cam, [r for r in hide if r[1] >= d + 0.05])
    out = {}

    def figs(cc):
        s = C.scale("mother", cam.scale(d))
        at = cam.px(u, z, d)
        if carrying:
            gp = C.carried_pose(tt, -0.2)
            jm, jg = L.piggyback(cc, st, pose, at, s, -1, t=tt, rim=PAPER, edge=SNOW, girl_pose=gp)
        else:
            k = clamp((tt - T_GIRL[0]) / (T_GIRL[1] - T_GIRL[0]))
            gst, gpose, g_at, g_s = L.girl_off_back(k, cam, tt, (st, pose, at, s, u, d), (u + 0.3, d - 0.1),
                                                     (GIRL_U, GIRL_D), facing=-1, end_crouch=0.08, end_head=-2.0)
            front = k < 0.3
            jg = C.draw(cc, "girl", gst, gpose, g_at, g_s, -1, shift_root=False, rim=PAPER,
                        parts=("far_arm", "far_leg", "near_leg", "body") if front else C.PARTS)
            kw_ = L.kk(tt, T_WRAP[0], T_WRAP[1] - T_WRAP[0])
            pose_m = pose
            if kw_ > 0.0:
                # her near arm goes back round the girl to where her hand takes the coat's edge
                sh = C.frame_point("mother", st, pose, (-6.0, -246.0), at, s, -1)
                tgt = _rel_from_frame(_wrap_point(jg, g_s, kw_, sh), st, pose, at, s)
                cur = pose.arms["near"][1]
                arms = dict(pose.arms)
                arms["near"] = ("rel", (lerp(cur[0], tgt[0], kw_), lerp(cur[1], tgt[1], kw_)))
                pose_m = pd.Pose(lean=pose.lean, head=pose.head, crouch=pose.crouch, arms=arms, hold=pose.hold,
                                 springs=pose.springs, eye=pose.eye, gaze=pose.gaze)
            jm = C.draw(cc, "mother", st, pose_m, at, s, -1, rim=PAPER, edge=SNOW)
            if front:
                C.draw(cc, "girl", gst, gpose, g_at, g_s, -1, shift_root=False, parts=("near_arm",), edge=SNOW)
            jm["scale"] = s
            jg["scale"] = g_s
            _coat_wrap(cc, jm, jg, g_s, kw_, cam.px(u, W.land_z(u), d)[1] + 0.05 * cam.scale(d))
        out["m"], out["g"] = jm, jg

    if behind:
        figs(c)
    L.reeds_rows(c, cam, [r for r in hide if r[1] < d + 0.05], rim=True)
    W.draw_trunk_side(c, cam)
    if not behind:
        figs(c)
    jm, jg = out["m"], out["g"]
    if t < T_HUSH:
        L.breath(c, jm, "mother", t, pant=1.2, seed=63, facing=-1, strength=0.8)
        L.breath(c, jg, "girl", t, pant=1.6, seed=64, facing=-1, strength=0.6, phase=0.3)


# ============================================================================ the page
def _feet_draw(c, cam, feet):
    for side, (x, n, hdg, lift) in feet.items():
        L.top_boot(c, cam, x, n, hdg, 1 if side == "R" else -1, lift)


def cam_out(t):
    return L.plan(t, [(0.0, (13.05, 4.15, 140.0)), (4.0, (13.1, 5.95, 170.0))])


def draw_out(c, t):
    cam = cam_out(t)
    tt = K.twos(t)
    gn = L.guard_n_film(FT0 + t)
    page = L.prints_upto("s06", gn)
    W.draw_page(c, cam, FT0 + t, holes=("stone",))
    n = out_n(tt)
    p = cam.px((W.TRAIL_X, n))
    ph = out_phase(tt)
    spd = 1.0 - L.kk(tt, T_STOP - 0.1, 0.3)
    L.top_shadow(c, "mother", p, cam.ppm, phase=ph, speed=spd, carry=True)
    W.draw_prints(c, cam, list(page) + out_laid(tt))
    _feet_draw(c, cam, out_feet(tt))
    C.top(c, "mother", p, cam.screen_heading(0.0), cam.ppm, tt, phase=ph, speed=0.0, carry=True, shadow=False)


def cam_back(t):
    return L.plan(t, [(6.0, (12.95, 7.15, 215.0)), (10.0, (12.8, 6.35, 228.0))])


def _back_centre(feet):
    xs = [v[0] for v in feet.values()]
    ns = [v[1] for v in feet.values()]
    return (sum(xs) / len(xs), sum(ns) / len(ns))


def draw_back(c, t):
    cam = cam_back(t)
    tt = K.twos(t)
    gn = L.guard_n_film(FT0 + t)
    W.draw_page(c, cam, FT0 + t, holes=("stone",))
    feet = back_feet(tt)
    ctr = _back_centre(feet)
    p = cam.px(ctr)
    hdg = back_heading(tt)
    moving = any(v[3] > 0.05 for v in feet.values())
    L.top_shadow(c, "mother", p, cam.ppm, phase=back_phase(tt), speed=0.3 if moving else 0.0, carry=True)
    W.draw_prints(c, cam, list(L.prints_upto("s06", gn)) + list(TRAIL))
    for (t0, t1, side, a, b) in BACK:
        L.print_flash(c, cam, TRAIL[b], t, t1)
    _feet_draw(c, cam, feet)
    C.top(c, "mother", p, cam.screen_heading(hdg), cam.ppm, tt, phase=back_phase(tt), speed=0.0, carry=True,
          shadow=False)
    for (t0, t1, side, a, b) in BACK:
        L.print_ring(c, cam, TRAIL[b], t, t1)


RISE_END = W.Plan(12.0, 3.0, 74.0)
RISE_PPM = (230.0, 74.0)


def cam_lie(t):
    """Rising from the reeds: zoomed about the hiding place, which drifts down to the left as the
    page opens to the whole lie."""
    u = ease("inout", clamp((t - T_RISE[0]) / (T_RISE[1] - T_RISE[0])))
    ppm = math.exp(lerp(math.log(RISE_PPM[0]), math.log(RISE_PPM[1]), u))
    end = RISE_END.px(W.HIDE)
    sx, sy = lerp(540.0, end[0], u), lerp(960.0, end[1], u)
    x, n = W.HIDE
    return W.Plan(x - (sx - 540.0) / ppm, n + (sy - 960.0) / ppm, ppm)


_LIE_LOOKS = ((13.0, (0.45, -0.55)), (T_POOL, (0.45, -0.55)), (T_POOL + 0.18, (0.35, 0.75)))


def draw_lie(c, t):
    cam = cam_lie(t)
    tt = K.twos(t)
    gn = L.guard_n_film(FT0 + t)
    prints = list(L.prints_upto("s06", gn)) + list(TRAIL)
    W.draw_page(c, cam, FT0 + t, prints=prints, holes=("stone",))
    L.guard_top_clock(c, cam, FT0 + t, tt)
    look = L.track(t, _LIE_LOOKS)
    L.reed_eyes(c, cam, t, look=look, blink=13.7, look_girl=(look[0] * 0.8, look[1]))


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        shot = L.shot_of(t, SHOTS)
        {"out": draw_out, "boot": draw_boot, "back": draw_back, "trunk": draw_trunk, "bank": draw_bank,
         "lie": draw_lie}[shot](c, t)


# ============================================================================ cues
def cues(T):
    out = []
    out.append(Cue(0.0, "river_under_ice", gain_db=-22, dur=16.0, pan=0.0,
                   dc="the river under the ice: a low, steady, muffled rush of deep water, all through the scene"))
    out.append(Cue(0.0, "wind_open", gain_db=-27, dur=4.0, pan=0.0,
                   dc="a thin cold wind over the open river; snow hissing faintly across the ice"))
    for i in range(11, 19):
        tf = T_LAND[i]
        x = cam_out(tf).px((TRAIL[i][0], TRAIL[i][1]))[0]
        out.append(Cue(tf, "step_mother_ice", gain_db=-21 if i < 18 else -23, pan=L.pan_x(x),
                       dc="her felt boot on the thin snow over the ice: a soft, quick, dry crunch, hurrying"))
    out.append(Cue(0.2, "panting_carry", gain_db=-28, dur=3.4, pan=0.0,
                   dc="the mother breathing hard through her nose as she hurries, the girl on her back"))
    out.append(Cue(T_STOP + 0.05, "breath_stop", gain_db=-24, pan=0.0,
                   dc="she stops at the edge of the black band: one breath out, then still"))
    out.append(Cue(4.0, "close_quiet", gain_db=-34, dur=2.0, pan=0.0,
                   dc="close to the ice: the wind drops away; only the river's low rush under the slab"))
    out.append(Cue(T_LIFT[0], "boot_lift_snow", gain_db=-26, pan=0.15,
                   dc="her felt boot pulled straight up out of its print: a faint dry squeak of snow"))
    out.append(Cue(T_FIT, "crunch_soft", gain_db=-17, pan=0.0,
                   dc="one soft crunch, deliberately quiet: the boot settling exactly into its own print"))
    for k, (t0, t1, side, a, b) in enumerate(BACK):
        x = cam_back(t1).px((TRAIL[b][0], TRAIL[b][1]))[0]
        out.append(Cue(t1, "step_backtrack", gain_db=-23, pan=L.pan_x(x),
                       dc="a careful, muffled crunch, quieter than her walking: her boot set down into an old print"))
    out.append(Cue(6.2, "held_breath_carry", gain_db=-32, dur=3.4, pan=0.0,
                   dc="she breathes slow and shallow, concentrating; the girl perfectly still on her back"))
    out.append(Cue(T_SIDE_L[1] - 0.04, "trunk_step_up", gain_db=-20, pan=-0.2,
                   dc="her felt boot steps up onto the fallen trunk: a dull knock on frozen bark"))
    out.append(Cue(T_SIDE_R[1] - 0.04, "trunk_creak", gain_db=-22, pan=-0.2,
                   dc="the trunk takes her weight: a slow, low creak of frozen wood; snow sifting off it"))
    wk = _trunk_walk()
    for (tf, side, fx) in L.step_times(wk, 10.0, 11.0):
        x = cam_trunk(tf).px(_trunk_u(tf), W.trunk_top_z(_trunk_u(tf)), D_TRUNK)[0]
        out.append(Cue(tf, "step_on_bark", gain_db=-22, pan=L.pan_x(x),
                       dc="a careful step along the trunk: felt on frozen bark, a soft knock, the wood creaking"))
    out.append(Cue(10.3, "trunk_creak", gain_db=-26, pan=0.1,
                   dc="the trunk shifts a fraction under them: a long thin creak"))
    pb = L.pan_x(cam_bank(11.5).px(-1.4, 0.3, 1.3)[0])
    out.append(Cue(T_STEP_UP[1], "step_on_bark", gain_db=-22, pan=pb + 0.1,
                   dc="her last step up the trunk's end: felt on bark, a creak"))
    out.append(Cue(T_DOWN_F[1], "step_down_snow", gain_db=-19, pan=pb,
                   dc="she steps down off the trunk into the bank's snow: a deep soft crunch"))
    out.append(Cue(T_DOWN_N[1], "step_down_snow", gain_db=-21, pan=pb - 0.05,
                   dc="her other boot down into the snow beside it"))
    out.append(Cue(T_INTO[0], "reeds_rustle", gain_db=-20, dur=0.6, pan=pb - 0.1,
                   dc="dry frozen reeds brushing and rattling against her coat as she pushes in among them"))
    out.append(Cue(T_CROUCH[0], "crouch_rustle", gain_db=-22, pan=pb - 0.1,
                   dc="she drops to a crouch: her long coat rustles, a knee into the snow"))
    out.append(Cue(T_GIRL[0] + 0.05, "girl_slide_off", gain_db=-23, pan=pb,
                   dc="the girl slides down off her mother's back: coat against coat, a soft bump"))
    out.append(Cue(T_GIRL[0] + 0.3, "girl_boots_land", gain_db=-25, pan=pb + 0.05,
                   dc="the girl's small boots in the snow: two light crunches"))
    out.append(Cue(T_WRAP[0], "coat_wrap", gain_db=-22, pan=pb,
                   dc="the heavy coat pulled round the girl: a long soft rustle of wool"))
    out.append(Cue(T_HUSH, "breath_held", gain_db=-30, dur=0.6, pan=pb,
                   dc="their breathing stops: held; a reed ticks against another in the wind"))
    out.append(Cue(13.0, "wind_open", gain_db=-28, dur=3.0, pan=0.0,
                   dc="the wind over the open river again, the reeds hissing faintly"))
    out.append(Cue(13.6, "far_steps_hobnail", gain_db=-30, dur=2.4, pan=0.1,
                   dc="far off, coming nearer through the trees: heavy slow steps, hobnails crunching in deep snow"))
    out.append(Cue(T_POOL, "lantern_creak_far", gain_db=-30, pan=0.15,
                   dc="the lantern's bail creaking on its swing, still in the trees, coming"))
    out.append(Cue(15.2, "lantern_creak_far", gain_db=-28, pan=0.15,
                   dc="the lantern's creak again, nearer, at the edge of the trees"))
    return out
