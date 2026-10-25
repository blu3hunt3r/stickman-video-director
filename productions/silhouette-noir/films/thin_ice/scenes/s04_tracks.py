"""s04 TRACKS (48-64): the woods; the girl falls; carried; the small prints end; the guard reads it;
out to the river.

  0.0-3.0   THE WOODS, profile (looking west, north to the right): the mother pulls the girl by the
            hand through the deep snow between the trunks, wading, both panting. The searchlight
            crosses (0.4-3.0): its beam slants in high from the left, over the trees (the tower is
            behind them) and its lit patch slides over the snow among the trunks, their shadows cut
            out of it and swinging as it goes.
  3.0-5.0   CLOSER (a jump-in): the girl's boot plunges into the drift (3.25) and she pitches
            forward, down waist deep, face in the snow (3.5, a muffled fall; the snow puffs). Her
            mother turns back (3.55-3.85, a paper turn), steps to her and crouches (3.85-4.05),
            hauls her out under the arms (4.05-4.5) and swings round with her (4.5-4.8, a paper
            turn): the girl is on her back, piggyback. She hitches her up (4.8-5.0).
  5.0-8.0   THE PAGE, straight down: two lines of prints climb the frame side by side, big and small;
            at the trampled patch the small line ends; only the big prints go on, deeper and closer
            together. The mother, the girl's red scarf at her shoulder, climbs out of the top of the
            frame (7.1), her long moon shadow after her. The prints hold the frame.
  8.0-11.0  THE WOODS, profile: the guard comes on along their prints, his lantern bobbing among the
            trunks, its pool sliding over the snow; he reaches the trampled patch (9.6), squats and
            lowers the lantern on the place where the small prints end (9.6-10.0); the camera pushes
            in on him; his head comes up (10.05-10.3) and his look runs along the deeper prints
            (10.35, a sight line): he understands.
  11.0-14.0 WIDER, tracking: he rises (11.0-11.45) and goes on faster, heavy, the rifle across his
            back; far behind him, small lanterns wake among the trees (11.5, 12.0, 12.5).
  14.0-16.0 THE RIVER BANK (the river view): carrying the girl, she breaks out of the last trees onto
            the bank; ahead the white river, the black band, and far across them the farmhouse's
            lit window. She stops at the bank's edge (15.25). The camera eases in on her. Last
            frame: her profile at the bank's edge, the river ahead (right). s05 opens wide on it.

Handoffs: s03 ends on the guard going into the woods; s04 opens in the woods' profile with the
mother pulling the girl. s04's last frame is her profile on the bank (map n -3.3, by the root
plate), the river to the right; s05 opens wide on the river section.
"""
import math
from functools import lru_cache

from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.thin_ice import cast as C, kit as K, world as W
from films.thin_ice.scenes import _lib_s04_s07 as L

INK, NIGHT, SNOW, SHADOW, PAPER, AMBER = K.INK, K.NIGHT, K.SNOW, K.SHADOW, K.PAPER, K.AMBER

# ---------------------------------------------------------------------------- beats (scene time)
SHOTS = ((0.0, "woods"), (3.0, "fall"), (5.0, "page"), (8.0, "guard"), (11.0, "on"), (14.0, "bank"))
T_SEARCH = (0.4, 3.0)       # the searchlight's patch crosses the snow among the trunks
T_STUMBLE = 3.25            # her boot plunges into the drift
T_FALL = 3.5                # down, waist deep, face in the snow
T_TURN = (3.55, 3.85)       # the mother turns back (a paper turn)
T_STEP = (3.85, 4.05)       # she steps to her and crouches
T_HAUL = (4.05, 4.5)        # up out of the snow
T_SWING = (4.5, 4.8)        # she turns back the way she was going: the girl on her back
T_HITCH = (4.8, 5.0)
T_EXIT = 7.1                # she climbs out of the top of the page
T_ARRIVE = 9.6              # the guard reaches the trampled patch
T_CROUCH = (9.6, 10.0)
T_HEAD_UP = (10.05, 10.3)
T_LOOK = 10.35              # his look along the deeper prints
T_RISE = (11.0, 11.45)
T_FAR = (11.5, 12.0, 12.5)  # far lanterns wake among the trees
T_STOP = 15.25              # she stops at the bank's edge
MOON_WOODS = 0.72           # the snow under the trees, a little below the open page

# ---------------------------------------------------------------------------- places
U_FALL = -48.15             # where the girl goes down (the drift at the stumble), woods u = n
D_M, D_G, D_GU = L.D_PATH, L.D_GIRL, L.D_GUARD
SINK = {"mother": 0.3, "girl": 0.26, "guard": 0.3}     # how deep they wade (m)
U_GU_STOP = -48.85          # where the guard squats, the patch just ahead of him
U_PATCH = (-48.2, 0.85)     # the place where the small prints end (u, d)
U_BANK = -3.3               # where she stops on the bank (river view u = n)
D_BANK = 0.42               # her depth there (she is just in front of the root plate)
V_PAGE = 1.05               # her pace on the page (m/s)

# the record: WOODS_PRINTS is four runs: her prints to the stumble, the girl's, the trampled
# patch, her deep prints on from it
_NA = len(W.walk_prints(W.PATH, "mother", 0.62, 0.42, seed=5, s0=11.0 + 0.62, s1=W.S_STUMBLE))
_NB = len(W.walk_prints(W.GIRL_PATH, "girl", 0.44, 0.5, seed=6, s0=11.0 + 0.44, s1=W.S_STUMBLE - 0.3))
P_MOTHER = W.WOODS_PRINTS[:_NA]
P_GIRL = W.WOODS_PRINTS[_NA:_NA + _NB]
P_PATCH = W.WOODS_PRINTS[_NA + _NB:_NA + _NB + 9]
P_DEEP = W.WOODS_PRINTS[_NA + _NB + 9:]
BEFORE = W.prints_before("s04")

# far lanterns (u, d) waking behind him
FAR_LAMPS = ((T_FAR[0], -52.6, 30.0), (T_FAR[1], -50.2, 42.0), (T_FAR[2], -49.0, 22.0))
# trunks in front of her at the woods' edge (river view: u, d, width, seed)
BANK_FG = ((-5.15, 0.2, 0.44, 9101), (-8.2, 0.28, 0.4, 9102), (-11.4, 0.16, 0.46, 9103))


def motion_blur(t, T):
    return 1


# ============================================================================ the walkers
def _m_walk():
    return L.walker("mother", [(-3.0, 1.0), (3.2, 1.0), (3.45, 0.35), (3.6, 0.0)], 0.62, lift=0.26, key="s04_m")


def _g_walk():
    return L.walker("girl", [(-3.0, 1.0), (3.3, 1.0)], 0.44, lift=0.17, key="s04_g")


def _gu_walk():
    return L.walker("guard", [(5.0, 1.45), (9.25, 1.45), (9.6, 0.0), (11.1, 0.0), (11.55, 1.75), (16.0, 1.75)], 0.76,
                    lift=0.24, key="s04_gu")


def _f_walk():
    return L.walker("mother", [(10.0, 1.35), (14.85, 1.35), (15.25, 0.0)], 0.5, lift=0.12, key="s04_mf")


def _m_u(t):
    """The mother's u (woods) while she walks, before the fall."""
    wk = _m_walk()
    return -47.55 + (wk.x(min(t, 3.6)) - wk.x(3.4)) * C.M_PER_UNIT["mother"]


def _g_u(t):
    wk = _g_walk()
    return U_FALL - 0.05 + (wk.x(min(t, 3.3)) - wk.x(3.3)) * C.M_PER_UNIT["girl"]


def _gu_u(t):
    wk = _gu_walk()
    return U_GU_STOP + (wk.x(t) - wk.x(9.65)) * C.M_PER_UNIT["guard"]


def _f_u(t):
    wk = _f_walk()
    return U_BANK + (wk.x(t) - wk.x(15.6)) * C.M_PER_UNIT["mother"]


def _m_page_s(t):
    """Her arc length along the path on the page (from the stumble)."""
    return W.S_STUMBLE + 0.25 + V_PAGE * max(0.0, t - 5.0)


# ============================================================================ the record of prints
@lru_cache(maxsize=1)
def times_mother():
    return L.land_times(P_MOTHER, _m_u, -1.0, 3.6, lead=0.3)


@lru_cache(maxsize=1)
def times_girl():
    return L.land_times(P_GIRL, _g_u, -1.0, 3.3, lead=0.22)


@lru_cache(maxsize=1)
def times_patch():
    # the trampled patch is laid while she falls, is hauled out and lifted
    return tuple(T_FALL - 0.1 + 0.15 * i for i in range(len(P_PATCH)))


@lru_cache(maxsize=1)
def times_deep():
    def pos(t):
        return W.poly_at(W.PATH, _m_page_s(t))[0][1]
    ts = L.land_times(P_DEEP, pos, 4.9, 8.0, lead=0.25)
    # the rest of the way to the bank: laid while we are with the guard (she is off ahead)
    return tuple(min(x, 8.0) for x in ts)


def guard_n(t):
    """How far north the guard is (map n): off the page behind them before 8.0, then as he walks."""
    if t < 8.0:
        return -60.0
    return _gu_u(t)


def prints_at(t):
    out = list(BEFORE)
    out += W.lay(P_MOTHER, t, times_mother())
    out += W.lay(P_GIRL, t, times_girl())
    out += W.lay(P_PATCH, t, times_patch())
    out += W.lay(P_DEEP, t, times_deep())
    out += L.guard_woods_until(guard_n(t) + 0.35)
    return out


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, NIGHT)
    with f.screen() as c:
        sh = L.shot_of(t, SHOTS)
        if sh == "woods":
            draw_woods(c, t)
        elif sh == "fall":
            draw_fall(c, t)
        elif sh == "page":
            draw_page(c, t)
        elif sh == "guard":
            draw_guard(c, t)
        elif sh == "on":
            draw_on(c, t)
        else:
            draw_bank(c, t)


# ============================================================================ 0-3: the woods
def cam_woods(t):
    um, ug = _m_u(t), _g_u(t)
    return W.Dio(0.5 * (um + ug) + 0.75, 3.25, 225.0, eye=4.5, D=14.0)


def search_at(t):
    """The searchlight's patch (u, d, ru, rd, alpha) on the woods' snow: it slides in from deep
    among the trees, crosses behind them and away north, nearer."""
    u_ = ease("inout", clamp((t - T_SEARCH[0]) / (T_SEARCH[1] - T_SEARCH[0])))
    a = L.kk(t, T_SEARCH[0], 0.3) * (1.0 - L.kk(t, T_SEARCH[1] - 0.3, 0.3))
    return (lerp(-55.0, -45.0, u_), lerp(8.5, 3.6, u_), 3.4, 2.4, a)


def draw_woods(c, t):
    cam = cam_woods(t)
    L.woods(c, cam, t, moonlit=MOON_WOODS, search=search_at(t), beam=((-420.0, -260.0), 1.0), prints=prints_at(t),
            fg=False)
    _pair(c, cam, t)
    L.fg_layer(c, cam, lerp(K.SNOW_DIM, SNOW, MOON_WOODS))


# ============================================================================ 3-5: the fall
def cam_fall(t):
    return L.dio(t, [(3.0, (U_FALL + 0.5, 1.85, 320.0, 4.0, 14.0)), (5.0, (U_FALL + 0.62, 1.8, 336.0, 4.0, 14.0))])


def draw_fall(c, t):
    cam = cam_fall(t)
    L.woods(c, cam, t, moonlit=MOON_WOODS, prints=prints_at(t), fg=False)
    _pair(c, cam, t)
    L.fg_layer(c, cam, lerp(K.SNOW_DIM, SNOW, MOON_WOODS))


# ---------------------------------------------------------------------------- the pair (0-5)
def _snow_line(cam, d):
    return cam.px(0.0, 0.0, d)[1]


def _m_root(t):
    """The mother's root u (woods) and her own state's pelvis x offset (units) after she stops."""
    if t < 3.6:
        return _m_u(t)
    u0 = _m_u(3.6)
    return u0 - 0.28 * L.kk(t, T_STEP[0], T_STEP[1] - T_STEP[0])


def _mother_state(t):
    """(state, pose, sx, facing): the mother from 0 to 5 s. sx is the paper turn."""
    m = _m_walk()
    tug = L.kk(t, T_STUMBLE, 0.2, "out")
    if t < T_TURN[0]:
        st = m.state(t)
        pose = C.walk_pose("mother", st, t=t, lean=lerp(10.0, -3.0, tug),
                           arms={"near": ("ang", lerp(-60.0, -72.0, tug), lerp(10.0, 4.0, tug))})
        return st, pose, 1.0, 1
    mu = C.M_PER_UNIT["mother"]
    base = m.state(3.6)
    px0 = base["pelvis"][0]
    fn, ff = base["feet"]["near"], base["feet"]["far"]
    # the step to the girl: her root moves 0.28 m left, the near foot (leading, as she faces left)
    # steps out, the far one stays planted
    ks = L.kk(t, T_STEP[0], T_STEP[1] - T_STEP[0])
    sh = -0.28 / mu * ks
    lead = "near" if fn[0] <= ff[0] else "far"
    k_air = L.bump(t, T_STEP[0], T_STEP[1] - 0.04)
    feet = {"near": fn, "far": ff}
    lf = feet[lead]
    feet[lead] = (lf[0] - 0.62 / mu * ks, -40.0 * k_air, 18.0 * k_air)
    st = dict(base, pelvis=(px0 + sh, base["pelvis"][1]), feet=feet, phase=0.0, speed=0.0, run=0.0)
    if t < T_TURN[1]:
        k = L.kk(t, T_TURN[0], T_TURN[1] - T_TURN[0])
        sx = math.cos(math.pi * k)
        pose = C.still_pose("mother", t=t, lean=lerp(-3.0, 8.0, k),
                            arms={"near": ("ang", lerp(-72.0, 25.0, k), 18.0), "far": ("ang", lerp(4.0, 22.0, k), 18.0)})
        return st, pose, sx, 1
    if t < T_HAUL[0]:
        pose = C.still_pose("mother", t=t, lean=lerp(8.0, 30.0, ks), crouch=lerp(0.0, 128.0, ks), head=-14.0 * ks,
                            arms={"near": ("ang", lerp(25.0, 62.0, ks), 22.0), "far": ("ang", lerp(22.0, 55.0, ks), 26.0)})
        return st, pose, -1.0, 1
    kh = L.kk(t, T_HAUL[0], T_HAUL[1] - T_HAUL[0])
    if t < T_SWING[0]:
        pose = C.still_pose("mother", t=t, lean=lerp(30.0, -7.0, kh), crouch=lerp(128.0, 8.0, kh),
                            head=lerp(-14.0, 4.0, kh))
        return st, pose, -1.0, 1
    k = L.kk(t, T_SWING[0], T_SWING[1] - T_SWING[0])
    sx = -math.cos(math.pi * k)
    hitch = L.bump(t, T_HITCH[0], T_HITCH[1])
    pose = C.still_pose("mother", t=t, lean=lerp(-7.0, 7.0, k) + 3.0 * hitch, crouch=8.0 + 26.0 * hitch,
                        arms=C.carry_arms(t), head=lerp(4.0, 0.0, k))
    return st, pose, sx, 1


def _girl_u_z(t):
    """The girl's root (u, z) from 0 to 4.5 s (walking, falling, down, hauled up)."""
    if t < T_STUMBLE:
        ug = _g_u(t)
        return ug, -(SINK["girl"] + 0.08 * L.kk(t, 2.6, 0.6))
    u0 = _g_u(T_STUMBLE)
    zdown = -0.36
    if t < T_HAUL[0]:
        k = L.kk(t, T_STUMBLE, T_FALL - T_STUMBLE, "in")
        return u0 + 0.06 * k, lerp(-SINK["girl"] - 0.08, zdown, k)
    kh = L.kk(t, T_HAUL[0], T_HAUL[1] - T_HAUL[0])
    um = _m_root(t)
    return lerp(u0 + 0.06, um - 0.27, kh), lerp(zdown, 0.2, kh)


def _girl_pose(t, hand_tgt=None):
    """(state, pose) of the girl from 0 to 4.5 s; hand_tgt: her far hand's IK target (in her
    mother's hand) while they walk."""
    g = _g_walk()
    if t < T_STUMBLE:
        st = g.state(t)
        arms = {"far": ("ik", hand_tgt)} if hand_tgt else {}
        return st, C.walk_pose("girl", st, t=t, lean=6.0, arms=arms)
    st = dict(g.state(T_STUMBLE), skirt=False)
    # arm angles here are world angles from straight down (forward +) less the lean: a1 - lean
    if t < T_FALL:
        k = L.kk(t, T_STUMBLE, T_FALL - T_STUMBLE, "in")
        ln = lerp(6.0, 72.0, k)
        arms = {"near": ("ang", lerp(20.0, 112.0, k) - ln, 6.0)}
        arms["far"] = ("ik", hand_tgt) if (hand_tgt and t < 3.38) else ("ang", lerp(70.0, 100.0, k) - ln, 4.0)
        return st, C.walk_pose("girl", st, t=T_STUMBLE, lean=ln, head=-6.0 * k, arms=arms)
    if t < T_HAUL[0]:
        lift = L.kk(t, 3.72, 0.25)
        wig = 3.0 * math.sin(t * 17.0) * L.kk(t, 3.6, 0.1)
        ln = 72.0 + wig - 10.0 * lift
        # face down, arms out ahead on the snow; then she pushes up on them and lifts her face
        return st, C.still_pose("girl", t=t, lean=ln, head=lerp(-6.0, 30.0, lift),
                                arms={"near": ("ang", lerp(98.0, 62.0, lift) - ln, lerp(4.0, 20.0, lift)),
                                      "far": ("ang", lerp(104.0, 66.0, lift) - ln, lerp(2.0, 16.0, lift))})
    kh = L.kk(t, T_HAUL[0], T_HAUL[1] - T_HAUL[0])
    st2 = L.stand_state("girl", spread=20.0)
    st2["skirt"] = kh > 0.75
    # her legs come up out of the drift: feet hanging
    st2["feet"] = {"near": (8.0 + 10.0 * kh, -6.0 * kh, -22.0 * kh), "far": (-10.0 + 8.0 * kh, -2.0 * kh, -30.0 * kh)}
    ln = lerp(62.0, 2.0, kh)
    return st2, C.still_pose("girl", t=t, lean=ln, head=lerp(30.0, 8.0, kh),
                             arms={"near": ("ang", lerp(62.0, 120.0, kh) - ln, lerp(20.0, 34.0, kh)),
                                   "far": ("ang", lerp(66.0, 114.0, kh) - ln, lerp(16.0, 30.0, kh))})


def _pair(c, cam, t):
    tt = K.twos(t)
    snow_c = lerp(K.SNOW_DIM, SNOW, MOON_WOODS)
    sl_m, sl_g = _snow_line(cam, D_M), _snow_line(cam, D_G)
    st_m, pose_m, sx, _ = _mother_state(tt)
    um = _m_root(tt) if tt >= 3.6 else _m_u(tt)
    zm = -SINK["mother"]
    s_m = C.scale("mother", cam.scale(D_M))
    s_g = C.scale("girl", cam.scale(D_G))
    ug, zg = _girl_u_z(tt)
    at_g = cam.px(ug, zg, D_G)
    # ---- walking and falling: the mother first (she is deeper), then the girl
    if tt < T_HAUL[0]:
        facing_m = 1 if sx > 0 else -1
        if tt >= T_TURN[1]:
            sx = -1.0
        jm = L.draw_fig(c, cam, "mother", st_m, pose_m, um, zm, D_M, facing=1, sx=sx, snow_line=sl_m)
        tgt = None
        if tt < 3.38 and "hand_near" in jm:
            h = jm["hand_near"]
            tgt = ((h[0] - at_g[0]) / s_g, (h[1] - at_g[1]) / s_g)
        st_g, pose_g = _girl_pose(tt, tgt)
        jg = L.draw_fig(c, cam, "girl", st_g, pose_g, ug, zg, D_G, snow_line=sl_g)
        L.wade_lip(c, cam, jm, um, D_M, snow_c, seed=3)
        if tt < T_STUMBLE:
            L.wade_lip(c, cam, jg, ug, D_G, snow_c, seed=4)
        else:
            # down in the drift: the snow heaped round her middle
            xs = [jg["pelvis"][0], jg["head"][0] if "head" in jg else jg["pelvis"][0] + 40.0]
            L.wade_lip(c, cam, jg, ug, D_G, snow_c, seed=5, h=0.11, pad=0.12, xs=xs)
        _pair_breath(c, t, jm, jg, facing_m if tt < T_TURN[1] else -1)
    elif tt < T_SWING[0] or (sx < 0.0):
        # ---- the haul and the first half of the swing: she holds the girl against her chest
        at_m = cam.px(um, zm, D_M)
        c.save()
        k = L.turn_group(c, at_m[0], sx)
        c.new_path()
        c.rectangle(-400.0, -200.0, 1900.0, sl_m + 200.0)
        c.clip()
        lt = (L.LIGHT[0] / max(k, 0.3), L.LIGHT[1])
        st_g, pose_g = _girl_pose(min(tt, T_HAUL[1] - 1e-3))
        # her mother's hands under the girl's arms
        sh = C.frame_point("girl", st_g, pose_g, C.fig("girl").shoulder, at_g, s_g, 1)
        tgt = ((sh[0] - at_m[0]) / s_m, (sh[1] + 14.0 * s_g - at_m[1]) / s_m)
        pose_m.arms = dict(pose_m.arms, near=("ik", tgt), far=("ik", (tgt[0] + 10.0, tgt[1] + 6.0)))
        jm = C.draw(c, "mother", st_m, pose_m, at_m, s_m, -1, rim=PAPER, edge=snow_c, light=(-lt[0], lt[1]),
                    parts=("far_arm", "far_leg", "near_leg", "body"))
        c.restore()
        c.save()
        L.turn_group(c, at_m[0], sx)
        c.new_path()
        c.rectangle(-400.0, -200.0, 1900.0, sl_g + 200.0)
        c.clip()
        jg = C.draw(c, "girl", st_g, pose_g, at_g, s_g, 1, rim=PAPER, edge=snow_c, light=lt)
        jm2 = C.draw(c, "mother", st_m, pose_m, at_m, s_m, -1, rim=PAPER, edge=snow_c, light=(-lt[0], lt[1]),
                     parts=("near_arm",))
        jm = dict(jm, **{kk_: v for kk_, v in jm2.items() if kk_.endswith("near")})
        dev_m, dev_g = L.to_frame(c, jm), L.to_frame(c, jg)
        c.restore()
        jm, jg = L.from_device(c, dev_m), L.from_device(c, dev_g)
        jm["scale"], jg["scale"] = s_m, s_g
        if tt < T_HAUL[0] + 0.3:
            L.wade_lip(c, cam, jm, um, D_M, snow_c, seed=3)
        _pair_breath(c, t, jm, jg, -1)
    else:
        # ---- the second half of the swing and the hitch: piggyback
        at_m = cam.px(um, zm, D_M)
        c.save()
        k = L.turn_group(c, at_m[0], sx)
        c.new_path()
        c.rectangle(-400.0, -200.0, 1900.0, sl_m + 200.0)
        c.clip()
        lt = (L.LIGHT[0] / max(k, 0.3), L.LIGHT[1])
        jm, jg = C.piggyback(c, st_m, pose_m, at_m, s_m, 1, t=tt, rim=PAPER, edge=snow_c, light=lt, look=0.1)
        dev_m, dev_g = L.to_frame(c, jm), L.to_frame(c, jg)
        c.restore()
        jm, jg = L.from_device(c, dev_m), L.from_device(c, dev_g)
        jm["scale"] = s_m
        jg["scale"] = s_m * C.M_PER_UNIT["girl"] / C.M_PER_UNIT["mother"]
        L.wade_lip(c, cam, jm, um, D_M, snow_c, seed=3)
        _pair_breath(c, t, jm, jg, 1)
    # the snow thrown up as she goes down, and as she comes out
    ppm_g = cam.scale(D_G)
    L.puff(c, cam.px(_g_u(T_STUMBLE) + 0.12, 0.0, D_G), t, T_STUMBLE, ppm_g, n=8, seed=11, power=0.6, life=0.5)
    L.puff(c, cam.px(_g_u(T_STUMBLE) + 0.3, 0.0, D_G), t, T_FALL - 0.04, ppm_g, n=20, seed=12, power=1.2, spread=1.2)
    L.puff(c, cam.px(_g_u(T_STUMBLE) + 0.1, 0.0, D_G), t, T_HAUL[0] + 0.15, ppm_g, n=10, seed=13, power=0.7, life=0.6)


def _pair_breath(c, t, jm, jg, facing_m):
    """Breath: both panting as they wade; her gasp as she goes down; none with her face in the
    snow; the mother's long breath out as she lifts her."""
    if t < T_HAUL[0]:
        L.breath(c, jm, "mother", t, pant=1.6, seed=1, facing=facing_m)
    elif t < T_HAUL[1]:
        L.breath(c, jm, "mother", t, pant=0.9, seed=1, phase=T_HAUL[1] - 0.12, facing=facing_m, strength=1.3)
    else:
        L.breath(c, jm, "mother", t, pant=1.7, seed=1, phase=4.4, facing=1)
    if t < T_STUMBLE:
        L.breath(c, jg, "girl", t, pant=2.1, seed=2, phase=0.2)
    elif t < T_FALL:
        L.breath(c, jg, "girl", t, pant=1.0, seed=2, phase=T_STUMBLE + 0.03, strength=1.2)
    elif t < 3.75:
        pass
    else:
        L.breath(c, jg, "girl", t, pant=2.6, seed=2, phase=3.76, facing=1)


# ============================================================================ 5-8: the page
def cam_page(t):
    return L.plan(t, [(5.0, (21.2, -49.75, 196.0)), (8.0, (21.3, -50.65, 204.0))])


def draw_page(c, t):
    cam = cam_page(t)
    W.draw_page(c, cam, t, prints=prints_at(t))
    s = _m_page_s(t)
    p, dvec = W.poly_at(W.PATH, s)
    tt = K.twos(t)
    s2 = _m_page_s(tt)
    p2, dvec2 = W.poly_at(W.PATH, s2)
    C.top(c, "mother", cam.px(p2), cam.screen_heading(W.heading_of(dvec2)), cam.ppm, tt, phase=(s2 - W.S_STUMBLE) / 1.0,
          speed=1.0, carry=True, shadow_dir=90.0)


# ============================================================================ 8-11: the guard
def cam_guard(t):
    return L.dio(t, [(8.0, (-47.75, 2.9, 205.0, 4.2, 14.0)), (9.6, (-47.8, 2.85, 210.0, 4.2, 14.0)),
                     (10.6, (-48.05, 2.0, 292.0, 4.0, 14.0)), (11.0, (-47.95, 1.98, 296.0, 4.0, 14.0))])


def _guard_pose(t):
    """(state, pose, lantern hold, lantern pool (u, d, r, strength)) of the guard from 8 to 14 s."""
    wk = _gu_walk()
    st = wk.state(t)
    u = _gu_u(t)
    k_down = L.kk(t, T_CROUCH[0], T_CROUCH[1] - T_CROUCH[0]) * (1.0 - L.kk(t, T_RISE[0], T_RISE[1] - T_RISE[0]))
    k_up = L.kk(t, T_HEAD_UP[0], T_HEAD_UP[1] - T_HEAD_UP[0])
    q = st["phase"]
    walking = 1.0 - k_down
    sw = (8.0 * math.sin(2.0 * math.pi * q + 0.6) * clamp(st["speed"] / 300.0) + 3.0 * math.sin(t * 3.1)) * walking
    hold = C.hold_lantern(t, lit=1.0, swing=sw, size=1.0)
    after = L.kk(t, T_RISE[1], 0.4)
    if k_down > 0.0:
        pose = C.still_pose("guard", t=t, lean=lerp(9.0, 16.0, k_down), crouch=175.0 * k_down,
                            head=lerp(0.0, lerp(-30.0, 4.0, k_up), k_down),
                            arms={"near": ("ang", lerp(32.0, 58.0, k_down), lerp(38.0, 4.0, k_down)),
                                  "far": ("ang", lerp(-8.0, 36.0, k_down), lerp(14.0, 70.0, k_down))},
                            hold={"near": hold}, gaze=0.6 * k_up)
    else:
        pose = C.walk_pose("guard", st, t=t, lean=lerp(9.0, 14.0, after), arms={"near": ("ang", 32.0, 38.0)},
                           hold={"near": hold})
    # the pool on the snow: ahead of him walking; on the patch when he lowers it
    pool_u = lerp(u + 0.45, U_PATCH[0], k_down)
    pool_d = lerp(D_GU - 0.35, U_PATCH[1], k_down)
    pool = (pool_u, pool_d, lerp(1.7, 1.15, k_down), lerp(1.0, 1.5, k_down))
    return st, pose, hold, pool, u


def _draw_guard_fig(c, cam, t, st, pose, u):
    snow_c = lerp(K.SNOW_DIM, SNOW, MOON_WOODS)
    sl = _snow_line(cam, D_GU)
    r = 0.95 * cam.scale(D_GU)
    j = L.draw_fig(c, cam, "guard", st, pose, u, -SINK["guard"], D_GU, snow_line=sl,
                   under=lambda cc, jj: K.glow(cc, jj["flame"], r, 1.0, t, seed=4) if "flame" in jj else None)
    L.wade_lip(c, cam, j, u, D_GU, snow_c, seed=7)
    return j


def draw_guard(c, t):
    cam = cam_guard(t)
    tt = K.twos(t)
    st, pose, hold, pool, u = _guard_pose(tt)
    L.woods(c, cam, t, moonlit=MOON_WOODS, prints=prints_at(t), lamps=[pool], fg=False)
    j = _draw_guard_fig(c, cam, tt, st, pose, u)
    walking = 1.0 - L.kk(tt, T_CROUCH[0], 0.3)
    L.breath(c, j, "guard", t, rate=0.62, seed=21, strength=1.0, phase=0.3 if walking > 0.5 else 0.1)
    # his look along the deeper prints
    if "eye" in j:
        tgt = cam.px(-46.15, 0.0, L.wd(*_path_pt(-46.15)))
        K.sight_line(c, j["eye"], tgt, t, T_LOOK, color=PAPER, dur=0.45, off=10.9, off_dur=0.1, r=6.0, gap=22.0,
                     head=24.0)
    L.fg_layer(c, cam, lerp(K.SNOW_DIM, SNOW, MOON_WOODS))


def _path_pt(n):
    return (L.path_x(n), n)


# ============================================================================ 11-14: on, faster
def cam_on(t):
    u = _gu_u(t)
    k = L.kk(t, 11.0, 1.5)
    return W.Dio(u + lerp(0.8, 1.5, k), lerp(5.0, 5.2, k), lerp(172.0, 158.0, k), eye=3.4, D=14.0)


def draw_on(c, t):
    cam = cam_on(t)
    tt = K.twos(t)
    st, pose, hold, pool, u = _guard_pose(tt)
    far = []
    for (t0, fu, fd) in FAR_LAMPS:
        if t >= t0:
            s = L.kk(t, t0, 0.2) * (1.0 + 0.5 * L.bump(t, t0, t0 + 0.6))
            bob = 0.12 * math.sin((t - t0) * 7.0 + fd)
            far.append((fu + 0.35 * (t - t0), fd, s))
    L.woods(c, cam, t, moonlit=MOON_WOODS, prints=prints_at(t), lamps=[pool], far_lamps=far, fg=False)
    j = _draw_guard_fig(c, cam, tt, st, pose, u)
    L.breath(c, j, "guard", t, rate=0.75, seed=22, strength=1.0, phase=0.2)
    L.fg_layer(c, cam, lerp(K.SNOW_DIM, SNOW, MOON_WOODS))


# ============================================================================ 14-16: the bank
def cam_bank(t):
    return L.dio(t, [(14.0, (-3.0, 6.55, 118.0, 9.4, 5.0)), (14.9, (-2.95, 6.4, 121.0, 9.2, 5.0)),
                     (16.0, (-2.2, 2.66, 260.0, 4.6, 5.0))])


def draw_bank(c, t):
    cam = cam_bank(t)
    tt = K.twos(t)
    L.river(c, cam, t)
    wk = _f_walk()
    st = wk.state(tt)
    u = _f_u(tt)
    stop = L.kk(tt, T_STOP - 0.2, 0.5)
    if tt < T_STOP:
        pose = C.walk_pose("mother", st, t=tt, arms=C.carry_arms(tt), lean=lerp(9.0, 4.0, stop))
    else:
        pose = C.still_pose("mother", t=tt, arms=C.carry_arms(tt), lean=lerp(4.0, 2.0, stop), head=4.0 * stop)
    s = C.scale("mother", cam.scale(D_BANK))
    jm, jg = C.piggyback(c, st, pose, cam.px(u, 0.0, D_BANK), s, 1, t=tt, rim=PAPER, edge=SNOW, look=0.2 + 0.1 * stop)
    jm["scale"] = s
    jg["scale"] = s * C.M_PER_UNIT["girl"] / C.M_PER_UNIT["mother"]
    L.breath(c, jm, "mother", t, pant=1.5, seed=31)
    L.breath(c, jg, "girl", t, pant=2.0, seed=32, phase=0.3, strength=0.8)
    L.fg_layer(c, cam, SNOW, trunks=BANK_FG, tall=18.0)


# ============================================================================ cues
def _pan_woods(cam_fn, t, u, d, z=0.0):
    return L.pan_x(cam_fn(t).px(u, z, d)[0])


def cues(T):
    out = []
    # ---- 0-5: the woods
    out.append(Cue(0.0, "wind_pines", gain_db=-24, dur=5.0, pan=0.0,
                   dc="wind high in the pines, a slow cold hush; now and then snow sliding off a branch"))
    out.append(Cue(T_SEARCH[0], "searchlight_clank", gain_db=-22, pan=-0.6,
                   dc="far off behind them, the searchlight's iron yoke clanks as it swings round"))
    out.append(Cue(T_SEARCH[0], "searchlight_hum", gain_db=-28, dur=T_SEARCH[1] - T_SEARCH[0], pan=-0.4,
                   dc="the searchlight's motor, a low electric hum, distant, sweeping from left to right"))
    for (tf, side, fx) in L.step_times(_m_walk(), 0.0, 3.6):
        cam_fn = cam_woods if tf < 3.0 else cam_fall
        out.append(Cue(tf, "step_mother_deep", gain_db=-20, pan=_pan_woods(cam_fn, tf, _m_u(tf), D_M),
                       dc="the mother's felt boot wading through knee-deep snow: a soft deep crunch and drag"))
    for (tf, side, fx) in L.step_times(_g_walk(), 0.0, T_STUMBLE):
        cam_fn = cam_woods if tf < 3.0 else cam_fall
        out.append(Cue(tf, "step_girl_deep", gain_db=-25, pan=_pan_woods(cam_fn, tf, _g_u(tf), D_G),
                       dc="the girl's small boot in deep snow: a light, quick crunch, quicker than her mother's"))
    out.append(Cue(0.0, "panting", gain_db=-22, dur=3.5, pan=-0.1,
                   dc="both panting in the cold: the mother's quick breaths, the girl's quicker and higher, wordless"))
    pf = L.pan_x(cam_fall(T_FALL).px(U_FALL, 0.0, D_G)[0])
    out.append(Cue(T_STUMBLE, "girl_gasp", gain_db=-20, pan=pf, dc="the girl's small sharp gasp as her boot plunges in"))
    out.append(Cue(T_FALL, "muffled_fall", gain_db=-12, pan=pf,
                   dc="a muffled fall into deep powder: a soft heavy whump, snow hissing as it settles"))
    out.append(Cue(T_TURN[0], "coat_swish", gain_db=-24, pan=pf + 0.1, dc="the mother's long coat swishes as she turns back"))
    out.append(Cue(T_STEP[0] + 0.12, "step_mother_deep", gain_db=-20, pan=pf,
                   dc="one quick wading step back to her, a deep crunch"))
    out.append(Cue(T_HAUL[0], "haul_effort", gain_db=-17, pan=pf,
                   dc="the mother hauls her up: a held breath let out in effort, snow pouring off the girl's coat"))
    out.append(Cue(T_SWING[0], "lift_swing", gain_db=-18, pan=pf,
                   dc="the lift: coats rustling as she swings the girl round onto her back"))
    out.append(Cue(T_HITCH[0] + 0.1, "hitch", gain_db=-22, pan=pf,
                   dc="she hitches the girl higher on her back: a soft bump and a breath"))
    out.append(Cue(3.76, "girl_whimper_breath", gain_db=-24, dur=1.2, pan=pf,
                   dc="the girl's frightened quick breaths after the fall, close, no words"))
    # ---- 5-8: the page
    for i, ts in enumerate(times_deep()):
        if 5.0 <= ts <= T_EXIT:
            out.append(Cue(ts, "step_mother_heavy", gain_db=-24, pan=0.0,
                           dc="her steps from above, carrying the girl: deeper, slower, heavier crunches"))
    out.append(Cue(5.0, "wind_pines", gain_db=-26, dur=3.0, pan=0.0, dc="the wind in the pines, high and thin"))
    # ---- 8-14: the guard
    out.append(Cue(8.0, "wind_pines", gain_db=-25, dur=6.0, pan=0.0, dc="the wind in the pines"))
    gw = _gu_walk()
    for (tf, side, fx) in L.step_times(gw, 8.0, 14.0):
        cam_fn = cam_guard if tf < 11.0 else cam_on
        out.append(Cue(tf, "step_guard_hobnail", gain_db=-14 if tf > 11.4 else -17,
                       pan=_pan_woods(cam_fn, tf, _gu_u(tf), D_GU),
                       dc="the guard's hobnailed boot in deep snow: a heavy slow crunch with a faint iron grit"))
    for i in range(10):
        tc = 8.15 + 0.62 * i
        if tc < T_CROUCH[0] or T_RISE[1] < tc < 14.0:
            cam_fn = cam_guard if tc < 11.0 else cam_on
            out.append(Cue(tc, "lantern_creak", gain_db=-24, pan=_pan_woods(cam_fn, tc, _gu_u(tc) + 0.4, D_GU, 1.0),
                           dc="the lantern's wire bail creaks on its swing; the glass rattles faintly"))
    pg = _pan_woods(cam_guard, T_CROUCH[0], U_GU_STOP, D_GU)
    out.append(Cue(T_CROUCH[0], "crouch", gain_db=-20, pan=pg,
                   dc="the guard squats: his greatcoat creaks, his knees press into the snow"))
    out.append(Cue(T_CROUCH[1] - 0.1, "lantern_lowered", gain_db=-24, pan=pg + 0.1,
                   dc="the lantern lowered near the snow: a small tinny clink of its bail"))
    out.append(Cue(T_HEAD_UP[0], "guard_breath_stop", gain_db=-22, pan=pg,
                   dc="his breathing stops for a moment as he understands; then one slow breath out through the nose"))
    out.append(Cue(8.0, "guard_breath", gain_db=-24, dur=6.0, pan=-0.2,
                   dc="the guard's heavy breathing, a big man walking hard in the cold, slower than theirs"))
    out.append(Cue(T_RISE[0], "rise", gain_db=-20, pan=pg, dc="he rises: the coat and the rifle's sling creak"))
    out.append(Cue(11.3, "far_whistle", gain_db=-26, pan=-0.7,
                   dc="far off in the woods behind him, a whistle answers his, faint and thin"))
    for i, t0 in enumerate(T_FAR):
        out.append(Cue(t0, "far_lantern_wake", gain_db=-28 - 2 * i, pan=-0.6 + 0.15 * i,
                       dc="a far answering whistle and a distant voice-less call; a lantern lit among the trees"))
    # ---- 14-16: the bank
    out.append(Cue(14.0, "river_under_ice", gain_db=-22, dur=2.0, pan=0.4,
                   dc="the open bank: the wind drops; the river's low rush under the ice, a far groan of ice"))
    for (tf, side, fx) in L.step_times(_f_walk(), 14.0, T_STOP + 0.2):
        out.append(Cue(tf, "step_mother", gain_db=-20, pan=L.pan_x(cam_bank(tf).px(_f_u(tf), 0.0, D_BANK)[0]),
                       dc="the mother's felt boots on the open bank's snow, shallower now: a quick soft crunch"))
    out.append(Cue(T_STOP, "stop_breath", gain_db=-22, pan=L.pan_x(cam_bank(T_STOP).px(U_BANK, 0.0, D_BANK)[0]),
                   dc="she stops: one long panting breath out, the girl's quick breath behind her ear"))
    return out
