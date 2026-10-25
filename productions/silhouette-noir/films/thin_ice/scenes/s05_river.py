"""s05 RIVER (64-78): the river; the stone through the black ice; upstream the light sweeps; the
lantern coming; her idea.

  0.0-3.0   WIDE, the river section (looking west, north to the right): the near bank and the woods'
            edge (left), the white ice, the black band, the white ice again, the far bank with the
            farmhouse and its lit window, the moon low above it; the black water under the slab. The
            two tiny figures on the near bank by the fallen trunk's root plate; she hitches the girl
            up on her back (1.7-2.05). Far upstream the searchlight's patch slides over the ice. A
            slow push in (the river's low rush under the ice; an ice groan, 1.2).
  3.0-5.5   CLOSER: she crouches (3.1-3.6) and the girl slides down off her back to the snow
            (3.5-3.95) and stands by the fallen trunk's root plate; she straightens (3.95-4.35) and
            looks out across the ice to the black band (4.35, a sight line). She stoops and digs a
            stone out of the snow (5.0-5.15), comes up with it (5.15-5.27), draws back (5.27-5.36)
            and throws (release 5.4): the stone flies off to the right.
  5.5-6.5   THE BLACK ICE, the section closer: the stone arcs in from the left and punches straight
            through the black band (6.0, a clean crack and a plop): a white star of cracks runs out
            from it, one of them to the cut and down through the thin slab; the hole opens, water
            jumps, black water wells up round it; bubbles rise in the water; the cracks go dark as
            the water seeps into them.
  6.5-7.5   THE PAGE, straight down on it: the black disc in the black band, rings spreading from
            it; the welling water draining back; the fallen trunk's tip at the bottom of the frame.
  7.5-8.0   CLOSE: the ice booms away under them (7.45) and the girl flinches against her mother.
  8.0-10.0  THE PAGE pulls back and back (8.0-9.3, the hole drifting up to the right): the black
            band runs the length of the river, out of the frame downstream and upstream to its
            rounded end; beyond it the ice is white all across, and the searchlight's disc sweeps
            over it (across mid-river, going south, at 9.5). Below: the woods, the prints out of
            them to the bank, and deep in the trees the guard's lantern coming on along them.
  10.0-11.0 PROFILE, the woods' edge: among the trunks (left) the guard's lantern bobs, closer.
  11.0-12.0 PROFILE, the pair by the root plate: the girl hears it and turns (11.05-11.25), then
            her mother (11.25-11.5, paper turns); her look runs back to the lantern (11.5).
  12.0-14.0 CU HER EYES, face-on: from the lantern (left) to the black band (right, 12.25), to the
            trunk (right and down, 12.85), back to her own prints (left and down, 13.25); a blink
            (13.45) and the idea (13.55): the eyes open wide, then narrow, and the camera pushes in
            on one eye. Last frame: her eye.

Handoffs: s04 ends on her profile at the bank's edge (the river view, u -3.3, the root plate to
her right, the river ahead); s05 opens wide on the river section with the two tiny figures there.
s05's last frame is her eye (face-on, filling the frame); s06 opens on the page.
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
FT0 = 64.0                  # film time of the scene's first frame

# ---------------------------------------------------------------------------- beats (scene time)
SHOTS = ((0.0, "wide"), (3.0, "down"), (5.5, "hit"), (6.5, "disc"), (7.5, "flinch"), (8.0, "page"),
         (10.0, "lantern"), (11.0, "turn"), (12.0, "eyes"))
T_HITCH = (1.7, 2.05)       # she hitches the girl up on her back (wide)
T_GROAN0 = 1.2              # an ice groan (sound only)
T_CROUCH = (3.1, 3.6)       # she crouches to set the girl down
T_SLIDE = (3.5, 3.95)       # the girl slides down off her back to the snow
T_RISE = (3.95, 4.35)       # she straightens
T_LOOK = (4.35, 4.9)        # her look out across the ice to the black band
T_DIG = (5.0, 5.15)         # she stoops and digs a stone out of the snow
T_UP = (5.15, 5.27)         # up with it
T_WIND = (5.27, 5.36)       # draws back
T_RELEASE = 5.4             # throws
T_HIT = 6.0                 # the stone punches through the black ice
T_RINGS = 6.3               # the rings spread from the hole (the page)
T_GROAN = 7.45              # the ice booms away under them
T_FLINCH = 7.5              # the girl flinches
T_PULL = (8.0, 9.3)         # the page pulls back
T_SWEEP = 9.5               # the searchlight's disc crosses mid-river (film 73.5)
T_TURN_G = (11.05, 11.25)   # the girl hears it and turns
T_TURN_M = (11.25, 11.5)    # her mother turns
T_SEE = 11.5                # her look back to the lantern
T_BAND, T_TRUNK, T_PRINTS = 12.25, 12.85, 13.25     # her eyes: the band, the trunk, her prints
T_BLINK = 13.45
T_IDEA = 13.55

# ---------------------------------------------------------------------------- places (river view: u = map n,
# d = 13.2 - map x)
U_M, D_M = -3.3, 0.42       # where s04 left her, by the root plate: she stays there
U_G, D_G = -4.0, 1.05       # where the girl stands, behind her (the profile keeps the two of them and
                            # the root plate apart; the page shows them where the record has them)
P_M, P_G = (12.9, -2.75), (12.15, -2.9)     # ... on the page (map x, n)
HOLE_U, HOLE_D = W.STONE_HOLE[1], W.SECTION_X - W.STONE_HOLE[0]
Z_REL, ARC = 1.7, 2.6       # the stone leaves her hand this high; its arc rises this far over the chord
STONE_R = 0.065
G_D = 3.2                   # the guard among the trees in the profile (his clock's n; behind the cut)
FARM_U, FARM_D = W.FARM[1], W.SECTION_X - W.FARM[0]
BEFORE = W.prints_before("s05")


def motion_blur(t, T):
    return 1


# ============================================================================ the walkers
def _gu_walk():
    return L.walker("guard", [(-3.0, L.GUARD_V), (20.0, L.GUARD_V)], 0.76, lift=0.24, key="s05_gu")


@lru_cache(maxsize=1)
def _m_stand():
    """Her stance on the bank (as s04 left her: the near foot a little ahead)."""
    return L.stand_state("mother", spread=18.0, step=22.0)


def _gu_u(t):
    """The guard's u in the profile: his clock (the woods' path), his feet planted."""
    wk = _gu_walk()
    return L.guard_n_film(FT0 + 10.5) + (wk.x(t) - wk.x(10.5)) * C.M_PER_UNIT["guard"]


# ============================================================================ the mother
_M_HANG = ((24.0, -40.0), (16.0, -42.0))        # her hands hanging (her pelvis frame)
_M_KNEE = ((62.0, 34.0), (48.0, 30.0))          # her hands on her knees, crouched


def _rel_world(rel, lean, crouch, st):
    """A point of her pelvis frame in her figure's world units (root at the ground, pelvis x 0)."""
    q = pd._rot(rel, lean)
    return (q[0], st["pelvis"][1] + crouch + q[1])


def _arm_ang(a1, e, lean):
    """An "ang" arm spec for a world upper-arm angle a1 (0 down, 90 forward, 180 up)."""
    return ("ang", a1 - lean, e)


def _mother(t):
    """(state, pose, u, carrying) at figure time t."""
    if t < T_CROUCH[0]:
        st = _m_stand()
        h = L.bump(t, T_HITCH[0], T_HITCH[1])
        pose = C.still_pose("mother", t=t, arms=C.carry_arms(t), lean=4.0 + 4.0 * h, crouch=22.0 * h, head=-2.0 * h)
        return st, pose, U_M, True
    st = _m_stand()
    u = U_M
    if t < T_SLIDE[0]:
        k = L.kk(t, T_CROUCH[0], T_CROUCH[1] - T_CROUCH[0])
        pose = C.still_pose("mother", t=t, arms=C.carry_arms(t), lean=lerp(6.0, 16.0, k), crouch=lerp(0.0, 120.0, k),
                            head=-4.0 * k)
        return st, pose, u, True
    if t < T_DIG[0]:
        k = L.kk(t, T_CROUCH[0], T_CROUCH[1] - T_CROUCH[0])
        kr = L.kk(t, T_RISE[0], T_RISE[1] - T_RISE[0])
        kl = L.kk(t, T_SLIDE[0], 0.3)
        lean = lerp(lerp(6.0, 16.0, k), 3.0, kr)
        crouch = lerp(lerp(0.0, 120.0, k), 0.0, kr)
        carry = C.carry_arms(t)
        arms = {}
        for i, side in enumerate(("near", "far")):
            a = carry[side][1]
            b = _M_KNEE[i]
            p = (lerp(a[0], b[0], kl), lerp(a[1], b[1], kl))
            p = (lerp(p[0], _M_HANG[i][0], kr), lerp(p[1], _M_HANG[i][1], kr))
            arms[side] = ("rel", p)
        look = L.kk(t, T_LOOK[0] - 0.15, 0.25) * (1.0 - L.kk(t, T_LOOK[1], 0.2))
        head = lerp(-4.0, 0.0, kr) + 4.0 * look
        return st, C.still_pose("mother", t=t, arms=arms, lean=lean, crouch=crouch, head=head, gaze=0.6 * look), u, False
    # the stone
    hang_n = _rel_world(_M_HANG[0], 3.0, 0.0, st)
    ground = (128.0, -10.0)
    hold = {}
    if t < T_UP[0]:
        k = L.kk(t, T_DIG[0], T_DIG[1] - T_DIG[0])
        lean, crouch, head = lerp(3.0, 40.0, k), lerp(0.0, 76.0, k), lerp(0.0, -16.0, k)
        tgt = (lerp(hang_n[0], ground[0], k), lerp(hang_n[1], ground[1], k))
        near = ("ik", tgt)
        far = ("rel", (lerp(16.0, 70.0, k), lerp(-42.0, 20.0, k)))
        if t >= T_DIG[1] - 0.03:
            hold["near"] = C.hold_stone(2.0)
    elif t < T_WIND[0]:
        k = L.kk(t, T_UP[0], T_UP[1] - T_UP[0])
        lean, crouch, head = lerp(40.0, 0.0, k), lerp(76.0, 8.0, k), lerp(-16.0, 6.0, k)
        waist = (14.0, st["pelvis"][1] - 40.0)
        near = ("ik", (lerp(ground[0], waist[0], k), lerp(ground[1], waist[1], k)))
        far = ("rel", (lerp(70.0, 40.0, k), lerp(20.0, -60.0, k)))
        hold["near"] = C.hold_stone(2.0)
    elif t < T_RELEASE + 0.1:
        kw = L.kk(t, T_WIND[0], T_WIND[1] - T_WIND[0])
        kt = clamp((t - T_WIND[1]) / (T_RELEASE - T_WIND[1]))          # the whip, to the release
        kf = clamp((t - T_RELEASE) / 0.1)                               # the follow-through
        lean = lerp(lerp(0.0, -7.0, kw), 10.0, ease("in", kt)) + 6.0 * ease("out", kf)
        crouch = lerp(8.0, 0.0, kw)
        head = 6.0
        a1 = lerp(lerp(2.0, -150.0, kw), -235.0, ease("in", kt)) - 65.0 * ease("out", kf)
        e = lerp(lerp(5.0, 70.0, kw), 6.0, kt) + 6.0 * kf
        near = _arm_ang(a1, e, lean)
        far = _arm_ang(lerp(lerp(20.0, 72.0, kw), 30.0, kt) - 12.0 * kf, lerp(20.0, 10.0, kw), lean)
        if t < T_RELEASE:
            hold["near"] = C.hold_stone(2.0)
    else:
        # watching it go; then the hole
        k = L.kk(t, T_RELEASE + 0.1, 0.35)
        lean = lerp(16.0, 3.0, k)
        follow = L.kk(t, 5.55, 0.3) * (1.0 - L.kk(t, 5.85, 0.25))
        head = lerp(0.0, -4.0, L.kk(t, 5.9, 0.3)) + 7.0 * follow - 9.0 * L.kk(t, 7.56, 0.2) * (1.0 - L.kk(t, 8.4, 0.5))
        near = ("rel", (lerp(150.0, _M_HANG[0][0], k), lerp(-60.0, _M_HANG[0][1], k)))
        far = ("rel", (lerp(40.0, _M_HANG[1][0], k), lerp(30.0, _M_HANG[1][1], k)))
        crouch = 0.0
        if t >= 10.0:
            head = lerp(-4.0, 3.0, L.kk(t, T_TURN_M[0], 0.4))
        return st, C.still_pose("mother", t=t, arms={"near": near, "far": far}, lean=lean, head=head, gaze=0.5), u, False
    pose = C.still_pose("mother", t=t, arms={"near": near, "far": far}, hold=hold, lean=lean, crouch=crouch, head=head,
                        breathe=0.3)
    return st, pose, u, False


def _mother_sx(t):
    """Her paper turn back toward the woods (S5)."""
    return math.cos(math.pi * L.kk(t, T_TURN_M[0], T_TURN_M[1] - T_TURN_M[0]))


# ============================================================================ the girl
def _girl_slide(t, cam, at_m, s_m, st_m, pose_m):
    """The girl getting down off her mother's back: down to a crouch behind her mother's heels,
    then two steps back to where she stands. (state, pose, root, scale, k)."""
    k = clamp((t - T_SLIDE[0]) / (T_SLIDE[1] - T_SLIDE[0]))
    st, pose, pel, s = L.girl_off_back(k, cam, t, (st_m, pose_m, at_m, s_m, U_M, D_M), (U_M - 0.34, 0.62), (U_G, D_G))
    return st, pose, pel, s, k


def _girl(t):
    """(state, pose) standing by the root plate, from T_SLIDE's end."""
    st = L.stand_state("girl", spread=16.0)
    kf = L.kk(t, T_FLINCH, 0.12, "out")
    if t < T_FLINCH:
        follow = L.kk(t, 5.5, 0.3) * (1.0 - L.kk(t, 5.85, 0.25))
        head = 3.0 + 6.0 * follow - 4.0 * L.kk(t, 5.95, 0.3)
        return st, C.still_pose("girl", t=t, head=head, gaze=0.5)
    # the flinch: shoulders up, head down, eyes shut, hands to her chest; easing; then (unseen,
    # during the page) back to standing, watching
    relax = L.kk(t, 7.85, 0.5)
    rest = L.kk(t, 8.6, 0.8)
    kf = kf * (1.0 - rest)
    relax = relax * (1.0 - rest)
    lean = lerp(0.0, 13.0, kf) - 5.0 * relax
    head = lerp(-1.0, -22.0, kf) + 12.0 * relax + 3.0 * rest
    crouch = 26.0 * kf - 10.0 * relax
    eye = 1.0 - 0.9 * kf * (1.0 - L.kk(t, 7.72, 0.12))
    trem = 1.5 * math.sin(t * 31.0) * kf * (1.0 - relax)
    arms = {"near": ("rel", (lerp(20.0, 112.0, kf), lerp(-40.0, -150.0, kf) + trem)),
            "far": ("rel", (lerp(14.0, 96.0, kf), lerp(-42.0, -138.0, kf)))}
    if t >= 10.0:
        head = lerp(head, 5.0, L.kk(t, T_TURN_G[0], 0.3))
    return st, C.still_pose("girl", t=t, arms=arms, lean=lean, head=head, crouch=crouch, eye=eye, breathe=0.6)


def _girl_sx(t):
    return math.cos(math.pi * L.kk(t, T_TURN_G[0], T_TURN_G[1] - T_TURN_G[0]))


# ============================================================================ the pair in the river view
def _pair(c, cam, t, sx_m=1.0, sx_g=1.0):
    """The mother and the girl at figure time t through a river camera: (mother joints, girl
    joints)."""
    st, pose, u, carrying = _mother(t)
    s_m = C.scale("mother", cam.scale(D_M))
    at_m = cam.px(u, 0.0, D_M)
    kw = dict(rim=PAPER, edge=SNOW)
    if carrying:
        jm, jg = C.piggyback(c, st, pose, at_m, s_m, 1, t=t, look=0.2, **kw)
        jm["scale"] = s_m
        jg["scale"] = s_m * C.M_PER_UNIT["girl"] / C.M_PER_UNIT["mother"]
        return jm, jg
    if t < T_SLIDE[1]:
        gst, gpose, g_at, g_s, k = _girl_slide(t, cam, at_m, s_m, st, pose)
        front = k < 0.3
        jg = C.draw(c, "girl", gst, gpose, g_at, g_s, 1, shift_root=False,
                    parts=("far_arm", "far_leg", "near_leg", "body") if front else C.PARTS, **kw)
        jm = C.draw(c, "mother", st, pose, at_m, s_m, 1, **kw)
        if front:
            C.draw(c, "girl", gst, gpose, g_at, g_s, 1, shift_root=False, parts=("near_arm",), edge=SNOW)
        jm["scale"] = s_m
        jg["scale"] = g_s
        return jm, jg
    gst, gpose = _girl(t)
    jg = L.draw_fig(c, cam, "girl", gst, gpose, U_G, 0.0, D_G, sx=sx_g)
    jm = L.draw_fig(c, cam, "mother", st, pose, u, 0.0, D_M, sx=sx_m)
    return jm, jg


def _breaths(c, t, jm, jg, fm=1, fg=1, held=None):
    """Their breath: panting after the run, slowing; none once she has seen the lantern."""
    pant_m = lerp(1.5, 0.8, L.kk(t, 3.0, 3.0))
    if held is None or t < held:
        L.breath(c, jm, "mother", t, pant=pant_m, seed=51, facing=fm, strength=0.9)
    pant_g = 2.0 if t < T_FLINCH else 2.6
    L.breath(c, jg, "girl", t, pant=pant_g, seed=52, phase=0.3, strength=0.75, facing=fg)


# ============================================================================ the stone
def stone_at(t):
    """The stone in flight (u, z, d), from her hand to the black ice."""
    s = clamp((t - T_RELEASE) / (T_HIT - T_RELEASE))
    u = lerp(U_M + 0.42, HOLE_U, s)
    z = lerp(Z_REL, W.ICE_Z, s) + 4.0 * ARC * s * (1.0 - s)
    d = lerp(D_M, HOLE_D, s)
    return u, z, d


def _stone(c, cam, t):
    if not (T_RELEASE <= t < T_HIT):
        return
    u, z, d = stone_at(t)
    p = cam.px(u, z, d)
    r = max(8.0, STONE_R * cam.scale(d))
    trail = [cam.px(*stone_at(max(T_RELEASE, t - 0.016 * i))) for i in range(8, -1, -1)]
    if math.dist(trail[0], trail[-1]) > r:
        K.band(c, trail, PAPER, r * 1.4, seed=5, alpha=0.4, taper=(0.05, 1.0))
    K.dot(c, (p[0] + 0.8 * r * 0.3, p[1] - 0.6 * r * 0.3), r, PAPER, seed=7)
    K.dot(c, p, r, INK, seed=8)


def _hole_r(t):
    return W.STONE_R * L.kk(t, T_HIT - 0.02, 0.07, "out")


@lru_cache(maxsize=1)
def _star():
    """The cracks out of the stone's hole on the black ice (local metres: x along u, y deeper),
    and the one that runs to the cut (toward the camera)."""
    star = K.crack_tree((0.0, 0.0), 0.72, seed=65, branches=6, spread=70.0, heading=None, depth=1, jag=0.3, segs=6)
    cut = K.crack_tree((0.04, -0.28), 1.05, seed=66, heading=-97.0, depth=1, jag=0.3, segs=6)
    return star + cut, cut


@lru_cache(maxsize=1)
def _cut_cross():
    """Where the crack toward the camera reaches the cut (local x), and when (its growth 0..1)."""
    _, cut = _star()
    pts, t0, t1 = cut[0]
    L_ = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        if (a[1] + HOLE_D) * (b[1] + HOLE_D) <= 0.0:
            f = (a[1] + HOLE_D) / ((a[1] - b[1]) or 1e-9)
            x = lerp(a[0], b[0], f)
            g = (acc + math.dist(a, b) * f) / L_
            return x, lerp(t0, t1, g)
        acc += math.dist(a, b)
    return pts[-1][0], 1.0


def _puddle_pts(r, seed=63, n=28):
    return [(r * (1.0 + 0.16 * K._sn(seed, i)) * math.cos(6.2832 * i / n), r * (1.0 + 0.16 * K._sn(seed, i)) *
             math.sin(6.2832 * i / n)) for i in range(n)]


def _impact(c, cam, t):
    """The stone through the black ice, in section: cracks, the hole, the water."""
    xf = L.ice_xf(cam, HOLE_U, HOLE_D)
    sc = cam.scale(HOLE_D)
    y_cut = cam.px(HOLE_U, W.ICE_Z, 0.0)[1]
    g = L.kk(t, T_HIT - 0.02, 0.16, "out")
    wet = L.kk(t, 6.18, 0.3)
    col = lerp(PAPER, lerp(THIN, WATER, 0.55), wet)
    trees, _ = _star()
    c.save()
    c.new_path()
    c.rectangle(-200.0, -200.0, 1480.0, y_cut + 200.0)
    c.clip()
    K.crack(c, trees, g, col, width=max(2.0, 0.04 * sc), seed=64, xf=xf)
    c.restore()
    # the black water welling up round the hole
    rp = lerp(W.STONE_R, 0.6, L.kk(t, T_HIT + 0.04, 0.42, "out"))
    if t >= T_HIT + 0.04:
        K.poly(c, [xf(p) for p in _puddle_pts(rp)], lerp(WATER, THIN, 0.3), 0.95)
    r = _hole_r(t)
    if r > 0.01:
        K.poly(c, [xf(p) for p in _puddle_pts(r, 61, 22)], WATER)
        lift = 0.025 * L.bump(t, T_HIT, T_HIT + 0.35)
        for i, sh in enumerate(W.hole_shards(W.STONE_HOLE, r, 61)):
            K.poly(c, [cam.px(n, W.ICE_Z + lift * (0.5 + hash01(i, 3)), W.SECTION_X - x) for (x, n) in sh],
                   lerp(THIN, ICE, 0.35))
    # in the cut: the crack down through the thin slab; bubbles rise in the water
    xc, gc = _cut_cross()
    if g >= gc:
        uc = HOLE_U + xc
        z0, z1 = W.ICE_Z, W.slab_bottom(uc)
        pts = [cam.px(uc + 0.025 * K._sn(i, 67) * (i % 2 * 2 - 1), lerp(z0, z1 - 0.02, i / 4.0), 0.0) for i in range(5)]
        K.band(c, pts, lerp(PAPER, THIN, 0.6 * wet), max(1.6, 0.03 * cam.ppm), seed=68)
    for i in range(7):
        tb = T_HIT + 0.06 + 0.07 * i
        a = (t - tb) / 0.9
        if 0.0 <= a < 1.0:
            ub = HOLE_U - 0.25 + 0.5 * hash01(i, 71) + 0.06 * math.sin(a * 9.0 + i)
            zb = lerp(W.ICE_Z - 1.6 - 0.8 * hash01(i, 72), W.ICE_Z - W.THIN_T - 0.05, ease("out", a))
            p = cam.px(ub, zb, 0.0)
            K.dot(c, p, max(1.5, (0.025 + 0.02 * hash01(i, 73)) * cam.ppm), lerp(PAPER, WATER, 0.45), seed=i,
                  alpha=0.8 * (1.0 - a * a))
    # the crack, heard: one quick ring off the ice; water jumps out of the hole, chips of ice
    hp = xf((0.0, 0.0))
    K.ripple(c, hp, t, T_HIT, PAPER, n=1, life=0.35, r0=0.2 * sc, r1=1.6 * sc, width=max(2.0, 0.05 * sc), seed=70,
             alpha=0.85)
    L.puff(c, hp, t, T_HIT, sc, n=20, seed=67, color=WATER, life=0.55, spread=0.55, power=1.6)
    L.puff(c, hp, t, T_HIT, sc, n=10, seed=68, color=ICE, life=0.45, spread=1.0, power=0.9)


# ============================================================================ cameras
def cam_wide(t):
    return L.dio(t, [(0.0, (8.5, 14.0, 38.0, 31.0, 16.0)), (3.0, (8.0, 13.5, 40.0, 30.0, 16.0))])


def cam_down(t):
    return L.dio(t, [(3.0, (-2.6, 2.52, 230.0, 3.39, 5.0)), (4.3, (-2.55, 2.52, 236.0, 3.39, 5.0)),
                     (4.9, (-1.9, 2.98, 185.0, 4.28, 5.0)), (5.5, (-1.82, 2.98, 188.0, 4.28, 5.0))])


def cam_hit(t):
    """The stone's fall: pushing in after it, faster and faster, onto the black ice; then easing."""
    return L.dio(t, [(5.5, (11.4, 3.6, 72.0, 10.0, 10.0)), (6.0, (13.6, 2.4, 165.0, 6.2, 10.0), "in"),
                     (6.5, (14.0, 2.2, 190.0, 5.6, 10.0), "out")])


def cam_disc(t):
    return L.plan(t, [(6.5, (W.STONE_HOLE[0], W.STONE_HOLE[1], 150.0)), (7.5, (W.STONE_HOLE[0], W.STONE_HOLE[1], 172.0))])


def cam_flinch(t):
    return L.dio(t, [(7.5, (-3.77, 0.875, 560.0, 1.2, 6.0)), (8.0, (-3.79, 0.87, 575.0, 1.2, 6.0))])


PAGE_END = (914.0, 758.0)   # where the hole sits in the wide page
PAGE_PPM = (172.0, 18.5)


def cam_page(t):
    """The pull back: zoomed about the hole, which drifts up to the right as the map opens."""
    u = ease("inout", clamp((t - T_PULL[0]) / (T_PULL[1] - T_PULL[0])))
    ppm = math.exp(lerp(math.log(PAGE_PPM[0]), math.log(PAGE_PPM[1]), u))
    sx, sy = lerp(540.0, PAGE_END[0], u), lerp(960.0, PAGE_END[1], u)
    x, n = W.STONE_HOLE
    return W.Plan(x - (sx - 540.0) / ppm, n + (sy - 960.0) / ppm, ppm)


def cam_lantern(t):
    """Among the trees: the guard comes on along the path, his lantern swinging (he is alone in
    the frame: his clock's place, only his depth cheated behind the cut)."""
    u = L.guard_n_film(FT0 + 10.5)
    return L.dio(t, [(10.0, (u + 0.6, 4.43, 132.0, 6.36, 10.0)), (11.0, (u + 1.0, 4.4, 140.0, 6.3, 10.0))])


def cam_turn(t):
    return L.dio(t, [(11.0, (-3.9, 2.27, 255.0, 2.88, 6.0)), (12.0, (-4.0, 2.25, 266.0, 2.86, 6.0))])


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        shot = L.shot_of(t, SHOTS)
        {"wide": draw_wide, "down": draw_down, "hit": draw_hit, "disc": draw_disc, "flinch": draw_flinch,
         "page": draw_page, "lantern": draw_lantern, "turn": draw_turn, "eyes": draw_eyes}[shot](c, t)


def _search(t):
    x, n = L.search_cross(FT0 + t)
    return (x, n, 3.0)


def draw_wide(c, t):
    cam = cam_wide(t)
    tt = K.twos(t)
    moon = (cam.px(FARM_U, 0.0, FARM_D)[0] + 8.0, cam.horizon_y() - 150.0)
    L.river(c, cam, t, search=_search(t), moon_at=moon)
    jm, jg = _pair(c, cam, tt)
    _breaths(c, t, jm, jg)


def _band_point(cam):
    return cam.px(13.0, W.ICE_Z, 22.0)


def draw_down(c, t):
    cam = cam_down(t)
    tt = K.twos(t)
    L.river(c, cam, t, search=_search(t))
    jm, jg = _pair(c, cam, tt)
    _breaths(c, t, jm, jg)
    if t >= T_LOOK[0]:
        K.sight_line(c, jm["eye"], _band_point(cam), t, T_LOOK[0], off=T_LOOK[1], r=6.0, gap=22.0, head=24.0)
    _stone(c, cam, t)


def draw_hit(c, t):
    cam = cam_hit(t)
    r = _hole_r(t)
    holes = ((W.STONE_HOLE, r, 61),) if r > 0.01 else ()
    L.river(c, cam, t, holes=holes, search=_search(t))
    if t >= T_HIT:
        _impact(c, cam, t)
    _stone(c, cam, t)


def _page_hole(c, cam, t, rings=True):
    """The hole from above: the water welling round it draining back; the rings spreading."""
    rp = lerp(0.6, W.STONE_R + 0.03, L.kk(t, 6.6, 0.8))
    K.poly(c, cam.pts([(W.STONE_HOLE[0] + p[0], W.STONE_HOLE[1] + p[1]) for p in _puddle_pts(rp)]),
           lerp(WATER, THIN, 0.3), 0.95)
    W.draw_hole(c, cam, W.STONE_HOLE, W.STONE_R, 61)
    if rings:
        K.ripple(c, cam.px(W.STONE_HOLE), t, T_RINGS, PAPER, n=4, every=0.24, life=1.2, r0=0.4 * cam.ppm,
                 r1=2.6 * cam.ppm, width=max(1.5, 0.05 * cam.ppm), seed=69, alpha=0.9)


def draw_disc(c, t):
    cam = cam_disc(t)
    W.draw_page(c, cam, t, prints=BEFORE)
    _page_hole(c, cam, t)


def draw_flinch(c, t):
    cam = cam_flinch(t)
    tt = K.twos(t)
    L.river(c, cam, t)
    jm, jg = _pair(c, cam, tt)
    _breaths(c, t, jm, jg)


@lru_cache(maxsize=1)
def _river_prints():
    return tuple(W.RIVER_PRINTS)


def draw_page(c, t):
    cam = cam_page(t)
    tt = K.twos(t)
    gn = L.guard_n_film(FT0 + t)
    prints = L.prints_upto("s05", gn + 0.3) + _river_prints()
    W.draw_page(c, cam, t, prints=prints, holes=())
    _page_hole(c, cam, t, rings=t < 8.4)
    sx_, sn_, sr = _search(t)
    W.search_patch(c, cam, (sx_, sn_), sr, alpha=0.85, heading=L.search_heading(sx_, sn_))
    # the guard deep in the woods, coming on along their prints
    gx = L.guard_x(gn)
    hdg = math.degrees(math.atan2(L.guard_x(gn + 1.0) - gx, 1.0))
    ahead = (gx + 0.5 * math.sin(math.radians(hdg)), gn + 0.5 * math.cos(math.radians(hdg)))
    W.lamp_pool(c, cam, ahead, 1.9, 1.15, t, seed=5)
    C.top(c, "guard", cam.px((gx, gn)), cam.screen_heading(hdg), cam.ppm, tt, phase=(tt * L.GUARD_V / 1.52) % 1.0,
          speed=1.0, lantern=1.0)
    # the two of them at the bank
    C.top(c, "girl", cam.px(P_G), cam.screen_heading(0.0), cam.ppm, tt, speed=0.0)
    C.top(c, "mother", cam.px(P_M), cam.screen_heading(0.0), cam.ppm, tt, speed=0.0)


def _guard_fig(c, cam, t):
    """The guard among the trees, his lantern lit, its pool on the snow (the profile)."""
    tt = K.twos(t)
    wk = _gu_walk()
    st = wk.state(tt)
    u = _gu_u(tt)
    q = st["phase"] % 1.0
    sw = 7.0 * math.sin(2.0 * math.pi * q + 0.6) + 3.0 * math.sin(3.1 * tt)
    hold = C.hold_lantern(tt, 1.0, sw, 1.0)
    pose = C.walk_pose("guard", st, t=tt, lean=9.0, arms={"near": ("ang", 32.0, 38.0)}, hold={"near": hold})
    L.ground_glow(c, cam, u + 0.5, G_D, 2.2, 1.5, t, seed=3)
    r = 1.15 * cam.scale(G_D)
    return L.draw_fig(c, cam, "guard", st, pose, u, 0.0, G_D,
                      under=lambda cc, jj: K.glow(cc, jj["flame"], r, 1.3, t, seed=4))


def draw_lantern(c, t):
    cam = cam_lantern(t)
    out = {}

    def between(cc):
        out["guard"] = _guard_fig(cc, cam, t)

    L.river(c, cam, t, split_d=G_D, between=between)
    j = out.get("guard")
    if j is not None:
        L.breath(c, j, "guard", t, rate=0.75, seed=55, strength=0.9)


def _lantern_world(t):
    """Where his lantern hangs (u, z, d): for a look from the bank."""
    return (_gu_u(t) + 0.45, 1.0, G_D)


def draw_turn(c, t):
    """The two of them on the bank hear it; they turn, and she looks back at it."""
    cam = cam_turn(t)
    tt = K.twos(t)
    L.river(c, cam, t)
    sm, sg = _mother_sx(tt), _girl_sx(tt)
    jm, jg = _pair(c, cam, tt, sx_m=sm, sx_g=sg)
    _breaths(c, t, jm, jg, fm=1 if sm >= 0 else -1, fg=1 if sg >= 0 else -1, held=T_SEE)
    if t >= T_SEE:
        K.sight_line(c, jm["eye"], cam.px(*_lantern_world(t)), t, T_SEE, dur=0.35, r=6.0, gap=22.0, head=24.0)


# ---------------------------------------------------------------------------- her eyes
_LOOKS = ((12.0, (-0.8, 0.05)), (T_BAND, (-0.8, 0.05)), (T_BAND + 0.08, (0.85, -0.2)), (T_TRUNK, (0.85, -0.2)),
          (T_TRUNK + 0.08, (0.6, 0.6)), (T_PRINTS, (0.6, 0.6)), (T_PRINTS + 0.08, (-0.5, 0.75)), (T_IDEA, (-0.5, 0.75)),
          (T_IDEA + 0.1, (0.0, 0.0)), (13.75, (0.0, 0.0)), (13.9, (0.35, 0.1)))


def _eyes_state(t):
    look = L.track(t, [(a, b, "inout") for a, b in _LOOKS])
    blink = 1.0 - L.bump(t, T_BLINK, T_BLINK + 0.09)
    wide = L.kk(t, T_IDEA, 0.1, "out") * (1.0 - L.kk(t, 13.72, 0.2))
    narrow = L.kk(t, 13.72, 0.2)
    lid = blink * (1.0 + 0.12 * wide - 0.24 * narrow)
    fear = 0.12 + 0.4 * wide - 0.12 * narrow
    return look, lid, fear


def cam_eyes(t):
    """The strip of her face: s, and the frame x of its centre (pushing in on one eye)."""
    push = L.kk(t, 13.5, 0.5, "in")
    s = 2.85 + 0.2 * L.kk(t, 12.0, 1.5) + 2.0 * push
    x = lerp(540.0, 540.0 + 110.0 * s, ease("inout", L.kk(t, 13.4, 0.6)))
    return s, (x, 960.0 + 20.0 * push)


def draw_eyes(c, t):
    tt = K.twos(t)
    K.fill(c, INK)
    s, at = cam_eyes(t)
    look, lid, fear = _eyes_state(tt)
    F.eyes(c, "mother", at, s, look=look, lid=lid, fear=fear, edge=STEEL, t=tt)


# ============================================================================ cues
def _px_pan(p):
    return L.pan_x(p[0])


def cues(T):
    out = []
    out.append(Cue(0.0, "river_under_ice", gain_db=-20, dur=14.0, pan=0.2,
                   dc="the river under the ice: a low, steady, muffled rush of deep water, all through the scene"))
    out.append(Cue(0.0, "wind_open", gain_db=-28, dur=10.0, pan=0.0,
                   dc="a thin cold wind over the open river, a faint hiss of snow skating on the ice"))
    out.append(Cue(T_GROAN0, "ice_groan", gain_db=-24, dur=2.0, pan=0.5,
                   dc="far downstream the river ice groans: a long low wooden moan that dies away"))
    out.append(Cue(0.2, "panting", gain_db=-30, dur=3.0, pan=-0.6,
                   dc="tiny and far off on the bank, the two of them still breathing hard after the run"))
    out.append(Cue(T_HITCH[0] + 0.1, "hitch_far", gain_db=-30, pan=_px_pan(cam_wide(1.8).px(U_M, 0.0, D_M)),
                   dc="small and far off, she hitches the girl up on her back: a soft rustle"))
    pd_ = _px_pan(cam_down(4.0).px(U_M, 0.0, D_M))
    out.append(Cue(T_CROUCH[0], "crouch_rustle", gain_db=-22, pan=pd_,
                   dc="the mother crouches: her long coat rustles, a knee creaks into the snow"))
    out.append(Cue(T_SLIDE[0] + 0.05, "girl_slide_off", gain_db=-22, pan=pd_ - 0.05,
                   dc="the girl slides down off her mother's back: coat against coat, a soft bump"))
    out.append(Cue(T_SLIDE[0] + 0.25, "girl_boots_land", gain_db=-24, pan=pd_ - 0.1,
                   dc="the girl's small boots drop into the snow: two light crunches"))
    out.append(Cue(T_RISE[0], "rise_breath", gain_db=-24, pan=pd_,
                   dc="the mother straightens up with a long breath out"))
    out.append(Cue(T_LOOK[0], "breath_slows", gain_db=-28, dur=0.6, pan=pd_,
                   dc="her breathing slows and quiets as she looks out across the ice at the black band"))
    out.append(Cue(T_DIG[0], "dig_stone", gain_db=-20, pan=pd_ + 0.05,
                   dc="a mitten digs into crusted snow; a stone scraped loose from the frozen ground"))
    out.append(Cue(T_WIND[0], "throw_effort", gain_db=-22, pan=pd_,
                   dc="a short sharp breath of effort as she draws back and throws"))
    out.append(Cue(T_RELEASE, "stone_whoosh", gain_db=-24, dur=0.6, pan=0.3,
                   dc="the stone whirring through the cold air, away to the right"))
    ph = _px_pan(cam_hit(T_HIT).px(HOLE_U, W.ICE_Z, HOLE_D))
    out.append(Cue(T_HIT, "ice_crack_clean", gain_db=-10, pan=ph,
                   dc="the stone punches through the thin black ice: one clean, sharp crack, a little glassy ring after it"))
    out.append(Cue(T_HIT + 0.04, "stone_plop", gain_db=-14, pan=ph,
                   dc="a deep hollow plop as the stone drops into the black water under the ice"))
    out.append(Cue(T_HIT + 0.1, "water_welling", gain_db=-22, dur=0.8, pan=ph,
                   dc="black water welling up through the hole: a soft gurgle and slosh, bubbles rising"))
    out.append(Cue(6.5, "water_lap", gain_db=-26, dur=1.0, pan=0.0,
                   dc="small ripples lapping at the edge of the hole, from above, quiet"))
    out.append(Cue(T_GROAN, "ice_boom", gain_db=-14, dur=2.2, pan=0.0,
                   dc="the river ice answers: a long deep booming groan that runs away under the ice, close"))
    out.append(Cue(T_FLINCH, "girl_flinch", gain_db=-20, pan=_px_pan(cam_flinch(7.6).px(U_G, 1.0, D_G)),
                   dc="the girl's tiny startled gasp; her coat rustles as she presses against her mother"))
    out.append(Cue(8.0, "searchlight_hum", gain_db=-30, dur=2.0, pan=-0.6,
                   dc="far upstream, the searchlight's low electric hum as it sweeps the white ice"))
    out.append(Cue(8.6, "searchlight_clank", gain_db=-32, pan=-0.6,
                   dc="very far off, the searchlight's iron yoke clanks as it swings"))
    out.append(Cue(8.4, "far_steps", gain_db=-32, dur=1.6, pan=0.4,
                   dc="far away in the woods, slow heavy steps in deep snow, barely there"))
    for (tf, side, fx) in L.step_times(_gu_walk(), 10.0, 11.0):
        out.append(Cue(tf, "step_guard_hobnail", gain_db=-18, pan=_px_pan(cam_lantern(tf).px(_gu_u(tf), 0.0, G_D)),
                       dc="among the trees, the guard's hobnailed boots in deep snow: heavy, slow crunches"))
    for i in range(2):
        tc = 10.15 + 0.5 * i
        out.append(Cue(tc, "lantern_creak", gain_db=-22, pan=_px_pan(cam_lantern(tc).px(_gu_u(tc), 1.0, G_D)),
                       dc="the lantern's wire bail creaks on its swing; the glass rattles faintly"))
    out.append(Cue(10.0, "guard_breath", gain_db=-26, dur=1.0, pan=0.0,
                   dc="the guard's heavy breathing as he walks, a big man in the cold"))
    out.append(Cue(11.0, "lantern_creak_far", gain_db=-30, pan=-0.8,
                   dc="from the trees behind them, far but clear, the lantern's creak"))
    pl = _px_pan(cam_turn(11.3).px(U_M, 0.0, D_M))
    out.append(Cue(T_TURN_G[0], "girl_turn", gain_db=-26, pan=pl - 0.15,
                   dc="the girl turns toward the sound: a small rustle of her coat"))
    out.append(Cue(T_TURN_M[0], "coat_turn", gain_db=-24, pan=pl,
                   dc="the mother turns sharply: coat swish, a crunch of snow underfoot"))
    out.append(Cue(T_SEE, "breath_catch", gain_db=-22, pan=pl,
                   dc="the mother's breath catches and stops as she sees the lantern"))
    out.append(Cue(12.0, "held_silence", gain_db=-34, dur=1.5, pan=0.0,
                   dc="close and still: no breath; only the river's low rush under the ice"))
    out.append(Cue(T_IDEA, "idea_breath", gain_db=-20, pan=0.0,
                   dc="a small sharp intake of breath through the nose: she has an idea"))
    return out
