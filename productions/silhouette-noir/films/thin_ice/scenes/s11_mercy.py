"""s11 MERCY (film 154-172, 18 s): the watch; the photograph and the girl; whistles; go; the
scarf given back; the lie; snow.

  A   0.0- 1.6  The section at the bank, s10's last frame, pushing in: he lies on his back on the
                slope, knees drawn up, shaking, his breath steaming; she gets up from the girl and
                stands between them, her hand up.
  B   1.6- 3.0  His glove goes inside his coat, fumbling; she flinches back and sweeps the girl
                behind her. Something small comes out in his glove and catches the moon.
  C   3.0- 5.6  CU: the watch in his shaking glove; the lid springs open (3.42); water runs out of
                the case; the hands have stopped at 12:31; in the lid, the wet photograph of a
                girl in a pompom hat. Push in on it.
  D   5.6- 6.6  Match cut: the girl, face on, the same size and place, looking at him; the moon
                behind her where the photograph's oval was.
  E   6.6- 7.7  CU: his face on the snow; he looks at her; he shuts the watch (7.3).
  F   7.7- 9.3  The river view, looking upstream, the woods on the left: whistles; lanterns come
                out of the trees; the mother spins round to them and the girl tucks in behind her;
                he comes up on an elbow on the far side of the root plate.
  G   9.3-11.6  Closer, the root plate between them: he is up on one knee; she turns back to him;
                he points upstream along the bank: go. The girl takes the red scarf from her
                mother's fist, crosses in front of the plate and holds it out to him. He takes it
                and winds it round her neck. Her mother has followed her.
  H  11.6-13.4  The mother turns, crouches, the girl climbs onto her back; she goes upstream into
                the dark, the girl looking back over her shoulder; he gets to his feet and watches.
  I  13.4-15.4  The page: the lanterns come down out of the woods at a run; she is a dark shape in
                the reeds going upstream, the red dot on her back; he walks to where the trail goes
                out and points along it to the hole; the searchlight comes down the river onto it.
  J  15.4-18.0  Behind them on the bank, the trail running out to the lit hole: he shakes his head.
                The lanterns lower; the guard beside him takes off his hat. The first snowflakes
                fall through the lantern light. Last frame: that.
"""
import math
from contextlib import contextmanager

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from engine.paperdoll import Pose
from engine.timing import Cue
from films.thin_ice import cast as C
from films.thin_ice import faces as F
from films.thin_ice import kit as K
from films.thin_ice import world as W
from films.thin_ice.scenes import _lib_dir as L
from films.thin_ice.scenes import _lib_s04_s07 as A
from films.thin_ice.scenes import s10_scarf as S10

SID = "s11"
FILM_T0 = K.film_start(SID)

T_RISE = (0.25, 0.9)          # she gets up from the girl
T_HUG = (0.1, 0.8)            # he draws his knees up and hugs himself
T_FUMBLE = (1.6, 2.6)         # his glove inside his coat
T_FLINCH = (1.85, 2.1)        # she flinches back, sweeping the girl behind her
T_OUT = (2.6, 2.95)           # the glove comes out: something small catches the moon
T_CU_W = 3.0
T_OPEN = (3.42, 3.56)         # the lid springs open
T_DRAIN = (3.6, 4.8)          # the water runs out of the case
T_PUSH = (4.55, 5.6)          # push in on the photograph
T_GIRL = 5.6                  # the match cut
T_BLINK = 6.15
T_FACE = 6.6
T_SHUT = (7.18, 7.3)          # he shuts the watch
T_RIVER = 7.7
T_WHISTLE = (7.8, 8.2, 8.62)  # three whistles from the trees
T_SPIN = (8.0, 8.26)          # the mother spins round to them
T_TUCK = (8.1, 8.6)           # the girl tucks in behind her
T_ELBOW = (8.25, 8.85)        # he comes up on an elbow
T_GO = 9.3
T_KNEE = (9.3, 9.8)           # up on one knee
T_TURN = (9.42, 9.68)         # she turns back to him
T_POINT = (9.85, 10.15)       # go
T_POINT_END = 10.35
T_GRAB = (9.95, 10.15)        # the girl takes the scarf from her mother's fist
T_CROSS = (10.15, 10.65)      # and crosses to him, holding it out
T_FOLLOW = (10.3, 10.95)      # her mother follows
T_TAKE = (10.65, 10.85)       # he takes it
T_WIND = (10.9, 11.55)        # and winds it round her neck
T_TURN2 = (11.6, 11.82)       # the mother turns round and crouches
T_LIFT = (11.82, 12.3)        # the girl climbs onto her back; up
T_AWAY = (12.3, 12.55)        # she turns away
T_LEAVE = (12.55, 13.4)       # upstream into the dark
T_STAND = (12.45, 12.95)      # he gets to his feet
T_PAGE = 13.4
T_POINT2 = (14.3, 14.6)       # he points along the trail at the hole
T_BANK = 15.4
T_SHAKE = (15.65, 16.45)      # he shakes his head
T_LOWER = (16.3, 16.85)       # the lanterns lower
T_HAT = (16.6, 17.3)          # the guard beside him takes off his hat
T_SNOW = 16.3                 # the first flakes
END = 18.0

PRINTS = W.prints_before(SID)
HOLES = W.holes_before(SID)
LIGHT_CU = (0.55, -0.85)
BG_CU = lerp(K.INK, K.NIGHT, 0.55)
GIRL_ST = C.standing("girl", 0.0, 16.0)      # as s10 stood her


def _k(t, span, e="inout"):
    if span[1] <= span[0]:
        return 1.0 if t >= span[0] else 0.0
    return ease(e, clamp((t - span[0]) / (span[1] - span[0])))


def _bump(t, t0, t1):
    u = (t - t0) / (t1 - t0)
    return math.sin(math.pi * u) if 0.0 < u < 1.0 else 0.0


def _mix(a, b, u):
    return tuple(lerp(x, y, u) for x, y in zip(a, b))


def _ik(hand, root, s, pivot=None, roll=0.0):
    """An arm's IK target for a hand at frame px `hand`: figure units from the root (the ground
    under a standing figure; the pelvis of a free-bodied one), x to screen right. For a figure
    turned `roll` about `pivot` the hand is turned back first."""
    if roll and pivot is not None:
        hand = L.turn_pt(hand, pivot, -roll)
    return ("ik", ((hand[0] - root[0]) / s, (hand[1] - root[1]) / s))


@contextmanager
def _turn(c, x, k):
    """A paper turn about the vertical line through frame x: k 1 (as drawn) .. 0 (edge on)."""
    c.save()
    c.translate(x, 0.0)
    c.scale(max(abs(k), 0.04), 1.0)
    c.translate(-x, 0.0)
    try:
        yield
    finally:
        c.restore()


def _dev(c, j):
    return {kk: c.user_to_device(*v) for kk, v in j.items() if isinstance(v, tuple)}


def _user(c, dev, s):
    out = {kk: c.device_to_user(*v) for kk, v in dev.items()}
    out["scale"] = s
    return out


def _px_m(j, who):
    return j["scale"] / C.M_PER_UNIT[who]


def _z_snow(n):
    return W.land_z(n) + 0.02


def _walk_step(dist, stride=0.85, amp=0.24):
    """A stance's step for someone who has walked `dist` m: the feet scissor, a stride each."""
    return amp * math.sin(2.0 * math.pi * dist / stride)


# ============================================================================ the figures in the section
def _mother(c, cam, tp, n, d, hands, lean=0.0, head=0.0, sink=0.0, step=0.15, facing=1, k=1.0, z=None, rim_w=None):
    """Her standing at n, d m behind the cut; hands world (n, z) targets; k: a paper turn (k < 0:
    she has turned round, facing the other way). tp: her breathing's clock."""
    s = C.scale("mother", cam.scale(d))
    at = cam.px(n, W.land_z(n) if z is None else z, d)
    st = L.stance("mother", step, sink=sink)
    hp = [cam.px(h[0], h[1], d) for h in hands]
    pose = C.still_pose("mother", lean=lean, head=head, t=tp, arms={"near": _ik(hp[0], at, s), "far": _ik(hp[1], at, s)})
    with _turn(c, at[0], k):
        dev = _dev(c, L.figure_at(c, "mother", st, pose, at, s, facing if k >= 0.0 else -facing, 0.0, rim=L.RIM,
                                  rim_w=rim_w))
    return _user(c, dev, s)


def _girl(c, cam, tp, n, d, crouch=0.0, lean=0.0, head=0.0, arms=None, hands=None, facing=1, scarf=False, k=1.0, z=None,
          step=None):
    """The girl standing at n, d m behind the cut. arms: paperdoll arm specs, or hands: world
    (n, z) targets for (near, far) (None for one leaves it hanging)."""
    s = C.scale("girl", cam.scale(d))
    at = cam.px(n, W.land_z(n) if z is None else z, d)
    a = dict(arms or {"near": ("ang", 20.0, 40.0), "far": ("ang", 12.0, 30.0)})
    for side, h in zip(("near", "far"), hands or (None, None)):
        if h is not None:
            a[side] = _ik(cam.px(h[0], h[1], d), at, s)
    st = GIRL_ST if step is None else L.stance("girl", step, 14.0)
    pose = C.still_pose("girl", lean=lean, head=head, crouch=crouch, t=tp, arms=a)
    with _turn(c, at[0], k):
        dev = _dev(c, L.figure_at(c, "girl", st, pose, at, s, facing if k >= 0.0 else -facing, 0.0, rim=L.RIM,
                                  red=K.RED if scarf else K.INK))
    return _user(c, dev, s)


H_HEAD_N = -1.45                # s10's end: his head up the bank, on his back
H_D = 0.55
H_PN = H_HEAD_N + 0.92          # his pelvis
LEGS_S10 = ((0.12, 0.88), (-0.04, 0.9))
LEGS_UP = ((-0.1, 0.62), (-0.13, 0.68))      # knees drawn up, boots on the snow
HANDS_S10 = ((H_PN - 0.1, _z_snow(H_PN - 0.1) + 0.12), (H_PN + 0.25, _z_snow(H_PN + 0.25) + 0.08))
HANDS_HUG = ((H_PN - 0.42, _z_snow(H_PN - 0.42) + 0.33), (H_PN - 0.55, _z_snow(H_PN - 0.55) + 0.3))


def _him_lying(c, cam, t, hands, legs, head=10.0, lean=8.0, shiver=0.0, rim_w=None):
    """Him on his back on the bank's slope, head up the bank (as s10 left him), shaking."""
    ft = FILM_T0 + t
    slope = math.degrees(math.atan2(_z_snow(H_HEAD_N) - _z_snow(H_PN), 0.92))
    pel = (H_PN, _z_snow(H_PN) + 0.17 + 0.035 * math.sin(ft * 9.0))
    roll = -90.0 + slope
    s = C.scale("guard", cam.scale(H_D))
    pv = cam.px(pel[0], pel[1], H_D)
    arms = {side: _ik(cam.px(h[0], h[1], H_D), pv, s, pv, roll) for side, h in zip(("near", "far"), hands)}
    st = L.free_state("guard_wet", legs[0], legs[1], (-50.0, -50.0), skirt=True)
    pose = Pose(lean=lean, head=head, arms=arms, springs=dict(C.REST), eye=1.0)
    c.save()
    c.translate(2.6 * shiver * math.sin(ft * 71.0), 1.8 * shiver * math.cos(ft * 83.0))
    j = L.figure(c, cam, "guard_wet", st, pose, pel[0], pel[1], H_D, 1, roll, rim=L.RIM, rim_w=rim_w)
    c.restore()
    return j


def _drips(c, top, s, t, n=4, seed=0, fall=0.5, spread=0.25):
    """Water dripping off him: drops falling `fall` m from about `top` (frame px), s px/m."""
    for i in range(n):
        ph = (t * (1.3 + 0.4 * hash01(seed, i)) + hash01(seed, i, 1)) % 1.0
        x = top[0] + (hash01(seed, i, 2) - 0.5) * spread * s
        y = top[1] + ph * ph * fall * s
        K.ellipse(c, (x, y), max(1.2, 0.012 * s), max(2.0, 0.022 * s), K.PAPER, alpha=0.75 * (1.0 - ph))


def _glint(c, p, r, a):
    """The moon catching something small: a disc and a four-point star."""
    if a <= 0.0:
        return
    K.disc(c, p, r, K.PAPER, seed=4, alpha=a)
    for ang in (0.0, 90.0):
        dx, dy = math.cos(math.radians(ang)) * 3.2 * r, math.sin(math.radians(ang)) * 3.2 * r
        K.band(c, [(p[0] - dx, p[1] - dy), p, (p[0] + dx, p[1] + dy)], K.PAPER, max(1.2, 0.35 * r), alpha=a,
               taper=(0.15, 0.15))


# ============================================================================ A, B: the bank (0-3)
CAM_A0 = W.Dio(-1.45, -0.2, 270.0, eye=0.9)           # s10's last camera
CAM_A1 = W.Dio(-1.7, 0.2, 300.0, eye=1.2)
M_N = S10.GIRL_N + 0.42                                # where s10 left her: crouched at the girl
G_N = S10.GIRL_N
M_D, G_D = S10.D_TRUNK - 0.25, 1.35
# s10 aimed her standing arms from her pelvis: its last frame's hands, as true targets
H_PEL0 = -L.stance("mother", 0.15, sink=0.32)["pelvis"][1] * C.M_PER_UNIT["mother"]
M_NEAR0 = (M_N + 0.3, 0.45 - H_PEL0)
M_FAR0 = (G_N + 0.1, 0.62 - H_PEL0)
SCARF0 = (G_N + 0.1, 0.62)                             # where s10 hung the scarf from


def _m_bank(t):
    """Her at the bank: n, sink, lean, head, near hand, far hand (n, z)."""
    rise = _k(t, T_RISE)
    fl = _k(t, T_FLINCH, "out3")
    n = M_N - 0.04 * rise - 0.22 * fl
    sink = lerp(0.32, 0.03, rise) + 0.1 * fl
    lean = lerp(26.0, 2.0, rise) - 9.0 * fl
    near = _mix(M_NEAR0, (n + 0.42 + 0.05 * fl, 1.02 + 0.06 * fl), rise)
    far = _mix(M_FAR0, (n - 0.3 - 0.12 * fl, 0.76 - 0.06 * fl), rise)
    return n, sink, lean, lerp(4.0, -2.0, rise), near, far


def _bank(c, t):
    ft = FILM_T0 + t
    cam = L.dio_at(t, [(0.0, CAM_A0), (T_CU_W, CAM_A1)])
    W.draw_river(c, cam, ft, holes=HOLES, moon_at=S10.MOON_SEC, trunk=False)
    # the girl: up from her crouch behind her mother, peeking round at him; swept back
    up = _k(t, (T_RISE[0] + 0.2, T_RISE[1] + 0.3))
    fl = _k(t, (T_FLINCH[0] + 0.04, T_FLINCH[1] + 0.12), "out3")
    arms = {"near": ("ang", lerp(60.0, 40.0, up), lerp(40.0, 34.0, up)),
            "far": ("ang", lerp(15.0, 22.0, up), lerp(60.0, 40.0, up))}
    gj = _girl(c, cam, 18.0 + t, G_N - 0.2 * fl, G_D, crouch=lerp(95.0, 16.0, up) + 36.0 * fl,
               lean=lerp(13.2, 5.0, up) + 7.0 * fl, head=lerp(2.4, 7.0, up) - 6.0 * fl, arms=arms)
    S10._trunk_sec(c, cam)
    # him: knees drawn up, hugging himself, shaking; his glove goes inside his coat; out again
    hug = _k(t, T_HUG)
    fum = _k(t, (T_FUMBLE[0], T_FUMBLE[0] + 0.25))
    out = _k(t, T_OUT, "out3")
    near, far = _mix(HANDS_S10[0], HANDS_HUG[0], hug), _mix(HANDS_S10[1], HANDS_HUG[1], hug)
    if fum > 0.0:
        jig = 0.025 * math.sin(ft * 23.0) * (1.0 - out)
        inside = (H_PN - 0.5 + jig, _z_snow(H_PN - 0.5) + 0.26 + 0.6 * jig)
        near = _mix(near, inside, fum)
        near = _mix(near, (H_PN - 0.72, _z_snow(H_PN - 0.72) + 0.62), out)
    legs = (_mix(LEGS_S10[0], LEGS_UP[0], hug), _mix(LEGS_S10[1], LEGS_UP[1], hug))
    hj = _him_lying(c, cam, t, (near, far), legs, head=lerp(10.0, 26.0, max(fum * 0.4, out)),
                    shiver=clamp(t / 0.4) * (1.0 - 0.5 * out), rim_w=4.5)
    # her: up from the girl, standing between them; the flinch
    n, sink, lean, head, nh, fh = _m_bank(t)
    j = _mother(c, cam, t, n, M_D, (nh, fh), lean=lean, head=head, sink=sink, rim_w=4.5)
    # the scarf hanging from her far hand (s10 hung it from her aim: it settles into her fist)
    m = _px_m(j, "mother")
    hp = _mix(cam.px(SCARF0[0], SCARF0[1], M_D), j["hand_far"], _k(t, (0.0, T_RISE[1])))
    S10.scarf_strip(c, [hp, (hp[0] + 0.02 * m, hp[1] + 0.3 * m),
                        (hp[0] + 0.05 * m * math.sin(ft * 2.0) - 0.1 * fl * m, hp[1] + 0.55 * m)],
                    ft, max(10.0, 0.06 * m), fringe=True, seed=10)
    S10._trunk_sec(c, cam, near=True, rim=L.RIM)
    if out > 0.0:
        h = hj["hand_near"]
        sc = cam.scale(H_D)
        _glint(c, (h[0] + 0.015 * sc, h[1] - 0.035 * sc), 0.03 * sc, clamp((out - 0.3) * 2.0))
    K.breath(c, hj["mouth"], 18.0 + t, pant=2.8, facing=1, s=1.5, phase=0.0, strength=1.0, seed=14)
    K.breath(c, j["mouth"], 18.0 + t, rate=0.55, facing=1, s=1.1, phase=0.4, strength=0.7 * (1.0 - fl), seed=15)
    K.breath(c, gj["mouth"], t, rate=1.1, facing=1, s=0.8, phase=0.25, strength=0.6 * up * (1.0 - fl), seed=16)


# ============================================================================ C: the watch (3.0-5.6)
W_AT = (700.0, 1030.0)
W_R = 215.0
PHOTO_AT = (W_AT[0] - 2.04 * W_R, W_AT[1])     # the open lid's photograph (faces.watch)
PUSH_Z = 3.15
PUSH_TO = (540.0, 975.0)
GIRL_AT = (PUSH_TO[0], PUSH_TO[1] + 0.05 * 0.74 * W_R * PUSH_Z)
GIRL_S = 0.74 * W_R * PUSH_Z / 470.0           # the photograph's girl, pushed in: the real girl's size


def _cu_watch(c, t):
    ft = FILM_T0 + t
    K.fill(c, BG_CU)
    K.glow(c, (980.0, 260.0), 1200.0, 0.45, ft, color=lerp(K.SNOW, K.PAPER, 0.5))
    k = _k(t, T_PUSH)
    Z = math.exp(lerp(0.0, math.log(PUSH_Z), k))
    c.save()
    c.translate(lerp(PHOTO_AT[0], PUSH_TO[0], k), lerp(PHOTO_AT[1], PUSH_TO[1], k))
    c.scale(Z, Z)
    c.translate(-PHOTO_AT[0], -PHOTO_AT[1])
    shake = 1.0 - 0.75 * k
    c.translate(3.0 * shake * math.sin(ft * 57.0), 2.4 * shake * math.cos(ft * 49.0))
    lid = _k(t, T_OPEN, "out3")
    c.translate(0.0, -10.0 * _bump(t, T_OPEN[0], T_OPEN[0] + 0.18))
    c.translate(0.0, 300.0 * (1.0 - _k(t, (T_CU_W, T_CU_W + 0.35), "out3")))
    F.glove(c, (1360.0, 1780.0), (530.0, 1210.0), 2.3, curl=0.3, rim=L.RIM, light=LIGHT_CU, rim_w=5.0)
    F.watch(c, W_AT, W_R, t=ft, lid=lid, hands=(12, 31), seconds=44, wet=1.0,
            drain=_k(t, T_DRAIN, "in") if t >= T_DRAIN[0] else 0.0, rim=L.RIM, light=LIGHT_CU)
    # his thumb pressing the crown as the lid goes
    press = _k(t, (T_OPEN[0] - 0.22, T_OPEN[0])) * (1.0 - _k(t, (T_OPEN[1], T_OPEN[1] + 0.3)))
    crown = (W_AT[0], W_AT[1] - 1.18 * W_R)
    F.glove(c, (1200.0, 470.0), (crown[0] + 80.0 - 24.0 * press, crown[1] + 6.0 + 12.0 * press), 1.5, curl=0.75,
            rim=L.RIM, light=LIGHT_CU, rim_w=4.0, thumb=1.0, flip=True)
    c.restore()
    # his breath drifting across the top
    K.breath(c, (-40.0, 360.0), t, rate=0.8, facing=1, s=3.0, phase=0.2, strength=0.6 * (1.0 - k), seed=21)


# ============================================================================ D: the girl (5.6-6.6)
def _cu_girl(c, t):
    ft = FILM_T0 + t
    K.fill(c, K.NIGHT)
    K.stars(c, ft, y1=1900.0)
    z = lerp(1.0, 1.05, _k(t, (T_GIRL, T_FACE), "linear"))
    K.moon(c, PUSH_TO, r=0.62 * W_R * PUSH_Z * z)          # where the photograph's oval was
    lid = 1.0
    if T_BLINK <= t < T_BLINK + 0.16:
        lid = abs(math.cos(math.pi * (t - T_BLINK) / 0.16))
    at = (GIRL_AT[0], GIRL_AT[1] + 5.0 * math.sin(ft * 1.6))
    F.front_girl(c, at, GIRL_S * z, scarf=None, look=(0.0, 0.2), lid=lid, t=ft, pompom=3.0 * math.sin(ft * 1.9))
    K.breath(c, (at[0], at[1] + 112.0 * GIRL_S * z), t, rate=1.1, facing=1, s=2.2, phase=T_GIRL + 0.2,
             strength=0.55, seed=22)


# ============================================================================ E: his face (6.6-7.7)
FACE_AT = (640.0, 1010.0)
FACE_S = 1.5


def _cu_face(c, t):
    ft = FILM_T0 + t
    K.fill(c, lerp(K.SNOW, K.NIGHT, 0.32))
    # the snow under his head: shadowed hollows and lumps
    for i in range(9):
        p = (1080.0 * hash01(i, 301), 1100.0 + 820.0 * hash01(i, 302))
        K.ellipse(c, p, 120.0 + 160.0 * hash01(i, 303), 26.0 + 20.0 * hash01(i, 304), lerp(K.SNOW, K.SHADOW, 0.5),
                  alpha=0.45)
    # his head on the snow, turned up toward her (to the left)
    c.save()
    c.translate(*FACE_AT)
    c.rotate(math.radians(-24.0 + 1.5 * math.sin(ft * 1.3)))
    c.translate(-FACE_AT[0], -FACE_AT[1])
    soft = _k(t, (T_FACE + 0.15, T_FACE + 0.6))
    m = F.guard(c, FACE_AT, FACE_S, look=0.5, lid=lerp(1.0, 0.62, soft), t=ft, facing=-1, rim=L.RIM, light=LIGHT_CU,
                hat=False, wet=1.0)
    # his greatcoat on down out of the frame (faces.guard stops it at the collar's foot)
    c.save()
    c.translate(*FACE_AT)
    c.scale(-FACE_S, FACE_S)
    c.translate(-400.0, -860.0)
    K.poly(c, [(613.0, 1040.0), (850.0, 1700.0), (-340.0, 1700.0), (-72.0, 1040.0)], K.INK)
    c.restore()
    mouth = c.user_to_device(*m["mouth"])
    c.restore()
    K.breath(c, c.device_to_user(*mouth), t, rate=0.7, facing=-1, s=2.0, phase=T_FACE + 0.3, strength=0.75, seed=23)
    # the watch in his glove at the bottom of the frame: he shuts it
    shut = _k(t, T_SHUT, "in")
    wa = (330.0, 1600.0 + 8.0 * _bump(t, T_SHUT[1], T_SHUT[1] + 0.15))
    F.glove(c, (-60.0, 1980.0), (360.0, 1690.0), 1.25, curl=0.35, rim=L.RIM, light=LIGHT_CU, rim_w=4.0)
    F.watch(c, wa, 118.0, t=ft, lid=1.0 - shut, hands=(12, 31), seconds=44, wet=0.6, rim=L.RIM, light=LIGHT_CU)
    F.glove(c, (900.0, 1960.0), (wa[0] + 150.0 - 120.0 * shut, wa[1] - 40.0), 1.1, curl=0.8, rim=L.RIM, light=LIGHT_CU,
            rim_w=3.5, flip=True)


# ============================================================================ the river view's layers
def _layered(c, cam, ft, figs):
    """The river view: W.draw_river (the searchlight far upstream at the crossing), then the
    woods' edge, the reeds, the root plate and the figures, all by depth: figs [(d, fn(c)), ...],
    each drawn d m behind the cut."""
    W.draw_river(c, cam, ft, holes=HOLES, reeds_on=False, trunk=False, search=L.cross_light(ft))
    items = sorted(list(figs) + [(S10.D_TRUNK, lambda cc: S10._trunk_sec(cc, cam))], key=lambda f: -f[0])
    bounds = [9999.0] + [d for d, _ in items] + [-99.0]
    for i in range(len(bounds) - 1):
        hi, lo = bounds[i], bounds[i + 1]
        A.river_woods(c, cam, ft, from_d=lo, upto_d=hi - 1e-6, shadows=(i == 0))
        A.reeds(c, cam, far=lo, near=hi)
        if i < len(items):
            items[i][1](c)
    S10._trunk_sec(c, cam, near=True, rim=L.RIM)


# the other guards with their lanterns, out of the trees: (n at T_RIVER, d, step phase, seed)
LAMPS = ((-9.2, 2.2, 0.0, 1), (-8.6, 3.2, 0.35, 2), (-9.6, 4.2, 0.6, 3))
LAMP_V = 1.25                   # walking in; at T_GO they stop at the trees' edge, searching
WHISTLES = (T_WHISTLE[2], T_WHISTLE[0], T_WHISTLE[1])     # who blows when


def _lamp_n(i, t):
    return LAMPS[i][0] + LAMP_V * (min(t, T_GO) - T_RIVER)


def _lamp_guard(c, cam, t, i):
    """One of the other guards with his lantern, coming out of the trees toward the bank (right)."""
    ft = FILM_T0 + t
    n, d, ph, seed = _lamp_n(i, t), LAMPS[i][1], LAMPS[i][2], LAMPS[i][3]
    pace = 1.0 if t < T_GO else 0.0
    q = (ph + 1.15 * (min(t, T_GO) - T_RIVER)) % 1.0
    sw_q = math.sin(2.0 * math.pi * q)
    st = L.stance("guard", 0.22 * pace * sw_q, 16.0)
    sw = 9.0 * pace * math.sin(2.0 * math.pi * q + 0.6) + 4.0 * math.sin(3.1 * ft + seed)
    raise_ = _k(t, (T_GO - 0.3, T_GO + 0.3))
    pose = C.still_pose("guard", lean=6.0 * pace, head=lerp(0.0, 8.0, raise_), t=ft + seed,
                        arms={"near": ("ang", lerp(48.0, 118.0, raise_), lerp(16.0, -4.0, raise_)),
                              "far": ("ang", -10.0 * pace * sw_q, 14.0)},
                        hold={"near": C.hold_lantern(ft, 1.0, sw, 1.0)})
    s = C.scale("guard", cam.scale(d))
    at = cam.px(n, W.land_z(n), d)
    at = (at[0], at[1] - 0.025 * cam.scale(d) * abs(sw_q) * pace)
    r = 0.7 * cam.scale(d)
    A.ground_glow(c, cam, n + 0.4, d + 0.2, 1.3, 0.8, ft, z=W.land_z(n), seed=seed, cut=True)
    j = C.draw(c, "guard", st, pose, at, s, 1, rim=L.RIM, light=L.LIGHT,
               under=lambda cc, jj: K.glow(cc, jj["flame"], r, 0.95, ft, seed=seed) if "flame" in jj else None)
    wh = WHISTLES[i]
    if wh - 0.3 <= t < wh + 0.9:
        C.whistle(c, j, ft, FILM_T0 + wh, 0.0035 * cam.scale(d), facing=1)
    return j


# ============================================================================ F: whistles (7.7-9.3)
CAM_F = W.Dio(-3.6, 1.4, 190.0, eye=3.0, D=4.0)
M_F = M_N - 0.26                                      # B's end
G_F0, G_F1 = (G_N - 0.2, G_D), (-2.85, 0.95)          # B's end; tucked in behind her mother


def _river(c, t):
    ft = FILM_T0 + t
    cam = CAM_F
    spin = _k(t, T_SPIN)
    tuck = _k(t, T_TUCK)
    elbow = _k(t, T_ELBOW)
    out = {}
    gn, gd = _mix(G_F0, G_F1, tuck)
    figs = [(LAMPS[i][1], lambda cc, i=i: _lamp_guard(cc, cam, t, i)) for i in range(3)]

    def girl(cc):
        out["girl"] = _girl(cc, cam, 18.0 + t, gn, gd, crouch=52.0 - 20.0 * tuck, lean=12.0, head=lerp(1.0, -8.0, spin),
                            z=W.land_z(gn) + 0.06 * _bump(t, T_TUCK[0], T_TUCK[1]), step=0.18 * _bump(t, T_TUCK[0], T_TUCK[1]),
                            arms={"near": ("ang", 40.0, 30.0), "far": ("ang", 22.0, 40.0)})

    def mother(cc):
        kk = math.cos(math.pi * spin)
        if spin < 0.5:
            hands = ((M_F + 0.47, 1.08), (M_F - 0.42, 0.7))
        else:      # turned round to the trees: her arm back, keeping the girl behind her
            hands = ((M_F - 0.4, 1.02), (M_F + 0.38, 0.74))
        j = _mother(cc, cam, ft, M_F, M_D, hands, lean=lerp(-7.0, 6.0, spin), head=lerp(-2.0, 4.0, spin), sink=0.12, k=kk)
        m = _px_m(j, "mother")
        hp = j["hand_far"]
        S10.scarf_strip(cc, [hp, (hp[0] + 0.02 * m, hp[1] + 0.3 * m), (hp[0] + 0.05 * m * math.sin(ft * 2.0), hp[1] + 0.55 * m)],
                        ft, max(8.0, 0.06 * m), fringe=True, seed=10)
        out["mother"] = j

    def him(cc):
        # up on an elbow: his near forearm onto the snow, chest and head up toward the trees
        hands = ((H_PN - 0.35 - 0.12 * elbow, _z_snow(H_PN - 0.35) + lerp(0.3, 0.03, elbow)),
                 (H_PN - 0.55, _z_snow(H_PN - 0.55) + 0.3 - 0.08 * elbow))
        out["him"] = _him_lying(cc, cam, t, hands, LEGS_UP, head=lerp(14.0, 44.0, elbow), lean=lerp(8.0, 40.0, elbow),
                                shiver=0.5 * (1.0 - elbow))

    figs += [(gd, girl), (M_D, mother), (H_D, him)]
    _layered(c, cam, ft, figs)
    K.breath(c, out["him"]["mouth"], t, pant=2.4, facing=1, s=1.1, phase=0.1, seed=24)
    K.breath(c, out["mother"]["mouth"], t, rate=0.9, facing=1 if spin < 0.5 else -1, s=1.0, phase=0.2,
             strength=0.0 if T_WHISTLE[0] < t < T_SPIN[1] + 0.4 else 0.7, seed=28)


# ============================================================================ G, H: go; the scarf; away (9.3-13.4)
CAM_G = W.Dio(-1.5, 0.8, 330.0, eye=1.6, D=4.0)
G_HIM = (-1.0, 0.55)            # up on one knee on the slope's top, the far side of the root plate
M_G0, M_G1 = (-2.95, 0.95), (-1.85, 0.9)       # her by the plate's near side; followed to the girl
G_G0, G_G1 = G_F1, (-1.58, 0.75)               # the girl tucked behind her; at him
# her way out from behind: straight away along the plate's edge, then in behind it and gone (the
# world's escape starts just behind the plate)
M_PATH = (M_G1, (-1.9, 1.5), (-2.45, 2.1))
M_GONE = M_PATH[-1]
UP_VP = (-1.6, 30.0)            # upstream along the bank, far off under the willows (n, d)


def _m_go(t):
    """Her in G-H: n, d, paper turn k, sink, lean, head, (near, far) hand targets, step."""
    f = _k(t, T_FOLLOW)
    n, d = _mix(M_G0, M_G1, f)
    step = _walk_step(1.1 * f) * (1.0 - _k(t, (T_FOLLOW[1] - 0.15, T_FOLLOW[1]))) + 0.15
    turn, turn2 = _k(t, T_TURN), _k(t, T_TURN2)
    k = lerp(-1.0, 1.0, turn) if t < T_TURN2[0] else lerp(1.0, -1.0, turn2)
    gn, gd = _mix(G_G0, G_G1, _k(t, T_CROSS))
    if t < T_TURN[0] + 0.13:          # still turned to the trees, her arm back keeping the girl behind her
        hands = ((n - 0.4, 1.02), (n + 0.38, 0.74))
    else:                             # turned back to him: her far fist on the girl's shoulder (the scarf in it)
        after = _k(t, (T_CROSS[0], T_CROSS[0] + 0.3)) * (1.0 - f)
        near = _mix((n + 0.3, 0.92), (n + 0.62, 0.98), after)                        # reaching after her
        far = _mix((G_G0[0] - 0.02, 0.8), (n + 0.2, 0.84), _k(t, (T_CROSS[0], T_CROSS[0] + 0.25)))
        if f > 0.0:
            near = _mix(near, (gn - 0.04, 0.78), _k(t, (T_FOLLOW[1] - 0.25, T_FOLLOW[1])))
        hands = (near, far)
    lean = lerp(-4.0, 4.0, turn) + 8.0 * _k(t, (T_CROSS[0], T_CROSS[0] + 0.3)) * (1.0 - f) + 6.0 * f
    sink = 0.04 + 0.26 * turn2
    head = lerp(4.0, -2.0, turn) + 6.0 * _k(t, T_POINT) * (1.0 - _k(t, (T_POINT_END, T_POINT_END + 0.3)))
    return n, d, k, sink, lean, head, hands, step


def _g_go(t):
    """The girl in G-H before she is on her mother's back: n, d, near hand target, step, head."""
    cross = _k(t, T_CROSS)
    n, d = _mix(G_G0, G_G1, cross)
    rest = (n + 0.06, 0.42)
    grab = _k(t, (T_GRAB[0], T_GRAB[1] - 0.04))                  # up to her mother's fist on her shoulder
    held = _k(t, (T_GRAB[1], T_CROSS[0] + 0.2))                  # the scarf held out in front of her
    drop = _k(t, (T_TAKE[1], T_TAKE[1] + 0.3))
    near = _mix(_mix(_mix(rest, (n - 0.02, 0.78), grab), (n + 0.34, 0.72), held), rest, drop)
    step = _walk_step(1.2 * cross, stride=0.55, amp=0.18) if 0.0 < cross < 1.0 else 0.06
    head = lerp(-6.0, 6.0, _k(t, T_TURN)) + 10.0 * _k(t, (T_CROSS[1] - 0.15, T_TAKE[1])) - 4.0 * _k(t, (T_WIND[1], T_TURN2[0]))
    return n, d, near, step, head


def _go(c, t):
    ft = FILM_T0 + t
    cam = CAM_G
    knee = _k(t, T_KNEE)
    point = _k(t, T_POINT, "out3") * (1.0 - _k(t, (T_POINT_END, T_POINT_END + 0.25)))
    wind = clamp((t - T_WIND[0]) / (T_WIND[1] - T_WIND[0]))
    lift = clamp((t - T_LIFT[0]) / (T_LIFT[1] - T_LIFT[0]))
    away = clamp((t - T_AWAY[0]) / (T_AWAY[1] - T_AWAY[0]))
    walk = clamp((t - T_LEAVE[0]) / (T_LEAVE[1] - T_LEAVE[0]))
    stand = _k(t, T_STAND)
    vp = cam.px(UP_VP[0], W.land_z(UP_VP[0]) + 0.6, UP_VP[1])
    out = {}
    carried = t >= T_LIFT[0]
    profile = away < 0.5
    w = ease("in", walk) * 0.3 + 0.7 * walk
    n_m, d_m = W.poly_at(M_PATH, w * W.poly_len(M_PATH))[0]

    def mother(cc):
        n, d, k, sink, lean, head, hands, step = _m_go(t)
        if not carried:
            out["mother"] = _mother(cc, cam, ft, n, d, hands, lean=lean, head=head, sink=sink, step=step, k=k)
            return
        s = C.scale("mother", cam.scale(d))
        at = cam.px(n, W.land_z(n), d)
        if profile:
            # the girl climbs onto her back and up she comes; then edge on
            u = _k(lift, (0.25, 1.0))
            st = L.stance("mother", 0.2, sink=0.3 * (1.0 - u))
            pose = C.still_pose("mother", lean=lerp(24.0, 8.0, u), head=-4.0, t=ft, arms=C.carry_arms(ft))
            with _turn(cc, at[0], math.cos(math.pi * away)):
                mj, gj = C.piggyback(cc, st, pose, at, s, -1, ft, rim=L.RIM, light=L.LIGHT, look=lerp(-10.0, 6.0, u))
                dev, gdev = _dev(cc, mj), _dev(cc, gj)
            out["mother"] = _user(cc, dev, s)
            out["girl"] = _user(cc, gdev, s)
        else:
            # from behind, going upstream past the plate into the dark
            sm = cam.scale(d_m)
            at = cam.px(n_m, W.land_z(n_m), d_m)
            with _turn(cc, at[0], clamp((away - 0.5) * 2.0)):
                out["back"] = _carry_back(cc, at, sm, t, max(0.0, t - T_LEAVE[0]) * 1.8)
            out["back_s"] = sm

    def girl(cc):
        n, d, near, step, head = _g_go(t)
        if t >= T_TURN2[0]:           # round to her mother's back as she turns and crouches
            u = _k(t, T_TURN2)
            n, d = lerp(n, M_G1[0] + 0.18, u), lerp(d, M_G1[1] - 0.02, u)
        out["girl"] = _girl(cc, cam, 18.0 + t, n, d, crouch=lerp(24.0, 6.0, _k(t, T_TURN)), lean=lerp(10.0, 3.0, _k(t, T_TURN)),
                            head=head, hands=(near, None), scarf=wind >= 1.0, step=step,
                            arms={"near": ("ang", 20.0, 30.0), "far": ("ang", lerp(30.0, 10.0, _k(t, T_TURN)), 24.0)})

    def him(cc):
        n, d = G_HIM
        z = W.land_z(n)
        s = C.scale("guard", cam.scale(d))
        if stand > 0.0:
            # up on his feet, watching them go
            at = cam.px(n, z, d)
            st = L.stance("guard", lerp(0.5, 0.2, stand), 16.0, sink=lerp(0.32, 0.0, stand))
            pose = C.still_pose("guard", lean=lerp(16.0, 2.0, stand), head=lerp(0.0, 10.0, stand), t=ft,
                                arms={"near": ("ang", 6.0, 12.0), "far": ("ang", -4.0, 10.0)})
            out["him"] = L.figure_at(cc, "guard_wet", st, pose, at, s, -1, 0.0, rim=L.RIM)
            return
        sc = cam.scale(d)
        rest_n = cam.px(n - 0.28, z + 0.62, d)
        rest_f = cam.px(n - 0.06, z + 0.56, d)
        down = cam.px(n - 0.38, z + 0.03, d)
        hn = _mix(down, rest_n, knee)
        hf = _mix((down[0] + 30.0, down[1]), rest_f, knee)
        # go: the near arm out along the bank, upstream
        sh = cam.px(n - 0.1, z + 1.22, d)
        dx, dy = vp[0] - sh[0], vp[1] - sh[1]
        ln = math.hypot(dx, dy) or 1.0
        hn = _mix(hn, (sh[0] + dx / ln * 0.74 * sc, sh[1] + dy / ln * 0.74 * sc), point)
        # the scarf held out to him: his glove to her mitten; then both gloves to her neck and round
        gj = out.get("girl")
        if gj:
            mit, nk = gj["hand_near"], gj["neck"]
            hn = _mix(hn, mit, _k(t, (T_TAKE[0] - 0.25, T_TAKE[0])))
            if t >= T_TAKE[1]:
                u = _k(t, (T_TAKE[1], T_WIND[0]))
                a = 2.0 * math.pi * 1.25 * wind
                r = 0.09 * sc
                back = _k(t, (T_WIND[1], T_WIND[1] + 0.3))
                loop_n = (nk[0] + r * math.cos(a), nk[1] + 0.3 * r * math.sin(a))
                loop_f = (nk[0] - r * math.cos(a), nk[1] - 0.3 * r * math.sin(a))
                hn = _mix(_mix(mit, loop_n, u), rest_n, back)
                hf = _mix(hf, loop_f, u * (1.0 - back))
        bend = _k(t, (T_TAKE[0] - 0.25, T_WIND[0])) * (1.0 - _k(t, (T_WIND[1], T_WIND[1] + 0.3)))
        out["him"] = _him_kneel(cc, cam, hn, hf, rise=knee, lean=lerp(36.0, 8.0, knee) + 14.0 * bend,
                                head=lerp(-10.0, 4.0, knee) + 10.0 * point + 8.0 * bend)

    # lantern light at the trees' edge, off to the left: on the snow and the woods behind them, not on them
    figs = [(G_HIM[1], him), (1.3, lambda cc: K.glow(cc, (-120.0, 1010.0), 520.0, 0.3, ft, ry=260.0, seed=33))]
    if not carried:
        figs += [(_m_go(t)[1], mother), (_g_go(t)[1] if t < T_TURN2[0] else M_G1[1] - 0.02, girl)]
    else:
        figs.append((M_G1[1] if profile else d_m, mother))
    _layered(c, cam, ft, figs)
    gj, mj, hj = out.get("girl"), out.get("mother"), out.get("him")
    _scarf_go(c, cam, t, ft, gj, mj, hj, wind)
    if hj:
        K.breath(c, hj["mouth"], t, rate=0.85, facing=-1, s=1.2, phase=0.15, strength=0.8, seed=25)
        if stand > 0.0:
            _drips(c, hj.get("hand_near", hj["mouth"]), cam.scale(G_HIM[1]), ft, n=3, seed=5, fall=0.6)
    if gj and not carried:
        K.breath(c, gj["mouth"], t, rate=1.2, facing=1, s=0.8, phase=0.4, strength=0.7, seed=26)
    if mj and profile:
        K.breath(c, mj["mouth"], t, rate=0.8, facing=1 if _m_go(t)[2] > 0.0 else -1, s=1.0, phase=0.1, strength=0.7,
                 seed=29)
    b = out.get("back")
    if b:
        L.back_breath(c, b["mother_head"], out["back_s"], ft, rate=0.9, strength=0.7)
    if point > 0.0 and hj:
        K.sight_line(c, hj["hand_near"], vp, ft, FILM_T0 + T_POINT[0] + 0.1, color=K.PAPER, dur=0.35,
                     off=FILM_T0 + T_POINT_END, r=5.0, gap=20.0, head=20.0)


def _scarf_go(c, cam, t, ft, gj, mj, hj, wind):
    """The red scarf in G: in her mother's fist; in the girl's mitten, held out; in his glove; wound
    round her neck (then it is the girl's own, drawn with her)."""
    if t >= T_WIND[1] or not (gj and hj):
        return
    sc = cam.scale(G_G1[1])
    m = sc
    w = max(8.0, 0.06 * m)
    if t < T_GRAB[1] and mj:
        hp = mj["hand_far"]
        if t > T_GRAB[0]:
            hp = _mix(hp, gj["hand_near"], _k(t, (T_GRAB[0] + 0.1, T_GRAB[1])))
        S10.scarf_strip(c, [hp, (hp[0] + 0.02 * m, hp[1] + 0.28 * m), (hp[0] + 0.04 * m * math.sin(ft * 2.0), hp[1] + 0.5 * m)],
                        ft, w, fringe=True, seed=10)
    elif t < T_TAKE[1]:
        hp = gj["hand_near"]
        sw = 0.04 * math.sin(ft * 5.0) * _bump(t, T_CROSS[0], T_CROSS[1])
        S10.scarf_strip(c, [hp, (hp[0] - 0.03 * m + sw * m, hp[1] + 0.26 * m), (hp[0] - 0.05 * m + 2.0 * sw * m, hp[1] + 0.48 * m)],
                        ft, w, fringe=True, seed=11)
    elif t < T_WIND[0]:
        hp = hj["hand_near"]
        S10.scarf_strip(c, [hp, (hp[0] + 0.02 * m, hp[1] + 0.26 * m), (hp[0] + 0.03 * m, hp[1] + 0.48 * m)], ft, w,
                        fringe=True, seed=12)
    else:
        hn, nk = hj["hand_near"], gj["neck"]
        k = clamp(wind)
        if k > 0.15:
            S10.scarf_strip(c, [(nk[0] - 0.09 * sc * k, nk[1] - 0.01 * sc), (nk[0], nk[1] + 0.03 * sc),
                                (nk[0] + 0.09 * sc * k, nk[1] - 0.01 * sc)], ft, w * 1.2, fringe=False, seed=13)
        S10.scarf_strip(c, [nk, (lerp(nk[0], hn[0], 0.5), max(nk[1], hn[1]) + 0.08 * sc), hn], ft, w, fringe=False, seed=14)
        S10.scarf_strip(c, [nk, (nk[0] - 0.02 * sc, nk[1] + 0.3 * sc * (1.0 - k) + 0.1 * sc)], ft, w, fringe=True, seed=15)


def _him_kneel(c, cam, hn, hf, rise=1.0, lean=8.0, head=0.0):
    """Him on one knee at G_HIM, facing left (rise 0: crouched low, 1: kneeling up); hands are
    frame px."""
    n, d = G_HIM
    z = W.land_z(n)
    pel = (n, z + lerp(0.36, 0.6, rise))
    s = C.scale("guard", cam.scale(d))
    pv = cam.px(pel[0], pel[1], d)
    near = (lerp(0.42, 0.4, rise), lerp(0.34, 0.58, rise))      # the near foot planted, its knee up
    far = (lerp(-0.2, -0.36, rise), lerp(0.34, 0.6, rise))      # the far knee down, toes dug in behind
    st = L.free_state("guard_wet", near, far, (0.0, -64.0), skirt=True)
    pose = Pose(lean=lean, head=head, arms={"near": _ik(hn, pv, s), "far": _ik(hf, pv, s)}, springs=dict(C.REST),
                eye=1.0)
    return L.figure(c, cam, "guard_wet", st, pose, pel[0], pel[1], d, -1, 0.0, rim=L.RIM)


def _carry_back(c, at, s, t, phase, rim=L.RIM):
    """Her from behind, walking away with the girl on her back, the girl's face turned back to us
    over her mother's shoulder (the red scarf round her neck). at: the ground under her, s px/m."""
    ft = FILM_T0 + t
    bob = 0.025 * abs(math.sin(2.0 * math.pi * phase))
    X = lambda p: (at[0] + p[0] * s, at[1] - (p[1] + bob) * s)
    polys = [[X(p) for p in L._COAT_STAND]]
    for side in (-1, 1):
        kick = max(0.0, math.sin(2.0 * math.pi * phase + (0.0 if side < 0 else math.pi)))
        foot = (0.09 * side, 0.02 + 0.14 * kick)
        polys.append(L._cap(X((0.08 * side, 0.4)), X(foot), 0.055 * s, 0.05 * s))
        polys.append(L._e(*X((foot[0], foot[1] - 0.01)), 0.06 * s, (0.05 + 0.02 * kick) * s))
    # the girl on her back: her coat over her mother's shoulders, her legs round her mother's hips
    polys.append([X(p) for p in ((-0.17, 0.98), (0.17, 0.98), (0.2, 1.2), (0.18, 1.46), (0.08, 1.55), (-0.08, 1.55),
                                 (-0.18, 1.46), (-0.2, 1.2))])
    for side in (-1, 1):
        knee = (0.27 * side, 1.02)
        polys.append(L._cap(X((0.1 * side, 1.05)), X(knee), 0.05 * s, 0.045 * s))
        polys.append(L._cap(X(knee), X((0.3 * side, 0.9)), 0.045 * s, 0.04 * s))
        polys.append(L._e(*X((0.31 * side, 0.88)), 0.045 * s, 0.035 * s))
        # her mother's arms hooked back under the girl's knees
        polys.append(L._cap(X((0.2 * side, 1.3)), X((0.25 * side, 1.04)), 0.05 * s, 0.045 * s))
    # her mother's head from behind: the headscarf, its knot at the nape
    polys.append(L._e(*X((0.0, 1.43)), 0.075 * s, 0.055 * s))
    polys.append(L._e(*X((0.0, 1.56)), 0.1 * s, 0.12 * s))
    if rim is not None:
        K.polys(c, [[(x, y - max(1.5, 0.012 * s)) for x, y in q] for q in polys], rim)
    K.polys(c, polys, K.INK)
    # the girl's head over her mother's right shoulder, turned back to us: the red round her neck
    hc = X((0.15, 1.72))
    fs = 0.105 * s / 150.0
    c.save()
    c.new_path()
    for i in range(40):
        a = 2.0 * math.pi * i / 40
        c.line_to(hc[0] + 210.0 * fs * math.cos(a), hc[1] - 60.0 * fs + 330.0 * fs * math.sin(a))
    c.close_path()
    c.clip()
    F.front_girl(c, hc, fs, scarf=K.RED, look=(0.15, 0.1), rim=rim, rim_w=max(1.2, 0.01 * s), t=ft,
                 pompom=4.0 * math.sin(2.0 * math.pi * phase))
    c.restore()
    return {"head": hc, "mother_head": X((0.0, 1.56))}


# ============================================================================ I: the page (13.4-15.4)
CAM_I0 = W.Plan(12.9, 0.6, 76.0)
CAM_I1 = W.Plan(12.6, 1.6, 80.0)
J_GUARDS = ((14.05, -2.35, -1), (14.75, -2.15, -1), (15.4, -1.95, -1))   # where they stop: (x, n, lantern side)
J_HAT = 0                                                                  # the one beside him takes his hat off
# their runs down out of the woods: world.GUARDS_PRINTS's routes, ending where J stands them
GUARD_ROUTES = (((10.5, -13.0), (12.6, -6.0), J_GUARDS[0][:2]), ((18.0, -14.0), (15.2, -6.0), J_GUARDS[1][:2]),
                ((22.0, -12.0), (17.0, -5.0), J_GUARDS[2][:2]))
GUARD_SEEDS = (16, 15, 17)
GUARD_LEFT = (2.0, 2.4, 2.8)    # metres of each route still to run at T_PAGE
GUARD_V = 2.4                   # at a run (m/s)
H_FROM = (W.SECTION_X - G_HIM[1], G_HIM[0])      # where H left him standing
H_TRAIL = (W.TRAIL_X, W.TRAIL_N[0] + 0.12)       # where the trail goes out from the bank
ESC = ((W.SECTION_X - M_GONE[1], M_GONE[0]),) + W.ESCAPE
ESC_LEAD = tuple(W.walk_prints([ESC[0], W.ESCAPE[0]], "mother", 0.6, 0.45, seed=13))   # from behind the plate
ESC_V = 1.1                     # her pace in the reeds (m/s)
SEARCH_TO = (13.4, 9.5, 3.4)    # the searchlight on the trail's end and the hole


def _guard_s(i, t):
    Lr = W.poly_len(GUARD_ROUTES[i])
    return min(Lr, Lr - GUARD_LEFT[i] + GUARD_V * (t - T_PAGE))


def _search(t):
    """The searchlight: off the crossing upstream, down the river onto the hole."""
    u = _k(t, (T_PAGE - 0.6, T_PAGE + 1.5), "out")
    return (lerp(-9.0, SEARCH_TO[0], u), lerp(11.5, SEARCH_TO[1], u), SEARCH_TO[2])


def _page(c, t):
    ft = FILM_T0 + t
    cam = L.plan_at(t, [(T_PAGE, CAM_I0), (T_BANK, CAM_I1)])
    (ex, en), edir = W.poly_at(ESC, ESC_V * (t - T_PAGE))
    esc_p = tuple(p for p in ESC_LEAD + W.ESCAPE_PRINTS if ex + 0.3 <= p[0])
    g_p = []
    for i, route in enumerate(GUARD_ROUTES):
        pts = W.walk_prints(list(route), "guard", 0.74, 0.5, seed=GUARD_SEEDS[i])
        g_p += pts[: max(0, int(_guard_s(i, t) / 0.74))]
    W.draw_page(c, cam, ft, prints=PRINTS + esc_p + tuple(g_p), holes=HOLES)
    sx, sn, sr = _search(t)
    K.lit_patch(c, cam.px((sx, sn)), sr * 1.3 * cam.ppm, sr * cam.ppm, alpha=0.55)
    L.hat_top(c, cam, ft)
    # her, the girl on her back, in the reeds going upstream: a dark shape and the red dot
    C.top(c, "mother", cam.px((ex, en)), math.degrees(math.atan2(-edir[1], edir[0])), cam.ppm, ft, phase=ft * 1.7,
          speed=0.8, carry=True)
    # the lanterns coming down out of the woods at a run
    hole = W.HOLES["guard"][0]
    for i, route in enumerate(GUARD_ROUTES):
        s_i = _guard_s(i, t)
        (gx, gn), gd = W.poly_at(route, s_i)
        arrived = s_i >= W.poly_len(route) - 1e-6
        hdg = math.degrees(math.atan2(-gd[1], gd[0]))
        if arrived:
            look = _k(t, (T_POINT2[0] + 0.1 * i, T_POINT2[1] + 0.25 + 0.1 * i))
            hdg = lerp(hdg, math.degrees(math.atan2(-(hole[1] - gn), hole[0] - gx)), look)
        p = cam.px((gx, gn))
        K.glow(c, (p[0] + 0.3 * cam.ppm, p[1] - 0.2 * cam.ppm), 1.5 * cam.ppm, 0.9, ft, seed=30 + i)
        C.top(c, "guard", p, hdg, cam.ppm, ft, phase=ft * 1.6 + i * 0.3, speed=0.0 if arrived else 1.0, lantern=1.0)
    # him: up from the slope to where the trail goes out; he points along it to the hole
    walk = _k(t, (T_PAGE, T_PAGE + 0.75))
    hp = _mix(H_FROM, H_TRAIL, walk)
    hdg = lerp(math.degrees(math.atan2(-(H_TRAIL[1] - H_FROM[1]), H_TRAIL[0] - H_FROM[0])), -90.0,
               _k(t, (T_PAGE + 0.5, T_PAGE + 0.9)))
    _top_him(c, cam, hp, hdg, ft, point=_k(t, T_POINT2, "out3"), phase=ft * 1.6, speed=0.8 if 0.0 < walk < 1.0 else 0.0)


def _top_him(c, cam, p, heading, ft, point=0.0, phase=0.0, speed=0.0):
    """Him from above like cast.top's guard, but bareheaded and without his rifle (both went into
    the river), a dark wet patch round his boots; point 0..1 his right arm out ahead."""
    ppm = cam.ppm
    q = cam.px(p)
    big = 1.18
    sw = math.sin(2.0 * math.pi * phase) * speed
    Ls = C.HEIGHT_M["guard"] * C.K_SHADOW
    legs = 0.47 * Ls
    sh = []
    for side in (-1, 1):
        off = 0.07 * big * side
        sh.append([(0.05 * sw * side, off - 0.035), (legs, off * 1.25 - 0.04), (legs, off * 1.25 + 0.04),
                   (0.05 * sw * side, off + 0.035)])
    sh.append([(legs * 0.92, -0.17 * big), (Ls * 0.83, -0.22 * big), (Ls * 0.88, -0.12 * big), (Ls * 0.88, 0.12 * big),
               (Ls * 0.83, 0.22 * big), (legs * 0.92, 0.17 * big)])
    sh.append(C._ell_m(Ls * 0.88 + 0.13, 0.0, 0.14, 0.1))
    K.polys(c, [C._xf(s_, q, 90.0, ppm) for s_ in sh], K.SHADOW)
    K.ellipse(c, q, 0.42 * ppm, 0.34 * ppm, lerp(K.SNOW, K.SHADOW, 0.8), alpha=0.7)
    sr, hem = (0.16, 0.29), (0.24, 0.31)
    ps = [C._ell_m(-0.02, 0.0, hem[0], hem[1]), C._ell_m(0.0, 0.0, sr[0], sr[1])]
    for side in (-1, 1):
        sh_p = (0.0, sr[1] * 0.85 * side)
        hand = (-0.16 * sw * side, sr[1] * 1.15 * side)
        if side == 1:
            hand = _mix(hand, (0.78, 0.2), point)
        ps.append(bass.capsule_pts(sh_p, hand, 0.05 * big, 0.045 * big, cap=4))
    ps.append(C._fluffy_m(0.02, 0.0, 0.105, 0.098, 3, bumps=7))       # his bare, cropped head
    K.polys(c, [C._xf(s_, q, heading, ppm) for s_ in ps], K.INK)


# ============================================================================ J: the lie (15.4-18.0)
CAM_J0 = L.Bank(13.65, -5.75, 0.0, 430.0, 2.85, eye=4.6, D=5.0, u0=0.0)
CAM_J1 = L.Bank(13.65, -5.45, 0.0, 455.0, 2.8, eye=4.5, D=5.0, u0=0.0)
J_HIM = H_TRAIL


def _guard_back(c, at, s, t, lamp_side=1, lamp_up=1.0, hat=1.0, hat_hand=0.0, wet=False, turn=0.0, bow=0.0,
                rim=L.RIM, seed=0, rifle=True):
    """A guard from behind, facing into the frame (at: the ground under him, s px per m): the
    greatcoat and its half belt, the ushanka (hat 0: off; hat_hand 0..1 his free hand up to it and
    down to his side with it), the lantern's arm (lamp_up 1: held out at his shoulder; 0: hanging),
    the rifle slung across his back. wet: him, bareheaded, no rifle; turn: his head turned (degrees;
    past half a turn his nose shows at the side); bow: his head lowered. Returns marks."""
    X = lambda p: (at[0] + p[0] * s, at[1] - p[1] * s)
    polys = []
    coat = [(-0.31, 0.36), (0.31, 0.36), (0.25, 0.75), (0.215, 1.02), (0.25, 1.32), (0.27, 1.46), (0.2, 1.53),
            (0.11, 1.58), (-0.11, 1.58), (-0.2, 1.53), (-0.27, 1.46), (-0.25, 1.32), (-0.215, 1.02), (-0.25, 0.75)]
    polys.append([X(p) for p in coat])
    polys.append([X(p) for p in ((-0.12, 1.56), (0.12, 1.56), (0.13, 1.67), (-0.13, 1.67))])        # the collar
    for side in (-1, 1):
        polys.append(L._cap(X((0.1 * side, 0.4)), X((0.1 * side, 0.05)), 0.07 * s, 0.065 * s))
        polys.append(L._e(*X((0.105 * side, 0.035)), 0.075 * s, 0.045 * s))
    marks = {}
    for side in (-1, 1):
        shp = (0.24 * side, 1.45)
        if side == lamp_side:
            hand = (lerp(0.31, 0.47, lamp_up) * side, lerp(0.82, 1.36, lamp_up))
            elbow = (lerp(0.3, 0.42, lamp_up) * side, lerp(1.12, 1.18, lamp_up))
        else:
            up = clamp(hat_hand)
            if up < 0.5:
                k_up = ease("inout", up * 2.0)
                hand = (lerp(0.29, 0.07, k_up) * side, lerp(0.84, 1.9, k_up))
                elbow = (lerp(0.3, 0.37, k_up) * side, lerp(1.15, 1.58, k_up))
            else:
                k_dn = ease("inout", (up - 0.5) * 2.0)
                hand = (lerp(0.07, 0.36, k_dn) * side, lerp(1.9, 1.0, k_dn))
                elbow = (lerp(0.37, 0.33, k_dn) * side, lerp(1.58, 1.2, k_dn))
        polys.append(L._cap(X(shp), X(elbow), 0.065 * s, 0.058 * s))
        polys.append(L._cap(X(elbow), X(hand), 0.058 * s, 0.05 * s))
        polys.append(L._e(*X(hand), 0.055 * s, 0.06 * s))
        marks["hand_%d" % side] = X(hand)
    # the head
    sn = math.sin(math.radians(turn))
    hx, hy = 0.012 * sn, 1.72 - 0.06 * bow
    if wet or hat < 1.0:
        polys.append(L._e(*X((hx, hy)), 0.098 * s, 0.118 * s))
        for side in (-1, 1):
            polys.append(L._e(*X((hx + 0.1 * side * math.cos(math.radians(turn)), hy - 0.01)), 0.024 * s, 0.042 * s))
        # cropped hair: a bumpy crown
        crown = [X((hx + 0.104 * math.cos(a) * (1.0 + 0.06 * K._sn(seed, i, 41)), hy + 0.125 * math.sin(a)))
                 for i, a in enumerate([math.pi * k_ / 14.0 for k_ in range(15)])]
        polys.append(crown)
        if abs(sn) > 0.62:
            # past half a turn his nose and moustache show at the side of his head
            sg = 1.0 if sn > 0.0 else -1.0
            k_ = clamp((abs(sn) - 0.62) / 0.3)
            x0 = hx + 0.09 * sg
            polys.append([X((x0, hy + 0.03)), X((x0 + sg * 0.045 * k_, hy - 0.02)), X((x0 + sg * 0.02 * k_, hy - 0.035)),
                          X((x0, hy - 0.03))])
            polys.append([X((x0, hy - 0.04)), X((x0 + sg * 0.04 * k_, hy - 0.05)), X((x0 + sg * 0.03 * k_, hy - 0.07)),
                          X((x0, hy - 0.07))])
    if not wet and hat > 0.0:
        hp = (hx, 1.84)
        if hat < 1.0:
            hd = marks["hand_%d" % (-lamp_side)]
            hp = ((hd[0] - at[0]) / s, (at[1] - hd[1]) / s + 0.05)
        fur = []
        for i in range(30):
            a = 2.0 * math.pi * i / 30
            b = 1.0 + 0.08 * (0.5 + 0.5 * math.cos(2.0 * math.pi * i / 3.0))
            fur.append(X((hp[0] + 0.155 * b * math.cos(a), hp[1] + 0.1 * b * math.sin(a))))
        polys.append(fur)
        if hat >= 1.0:
            polys.append([X(p) for p in ((-0.15, 1.71), (0.15, 1.71), (0.155, 1.8), (-0.155, 1.8))])    # the back flap
        polys.append(L._e(*X((hp[0], hp[1] + 0.1)), 0.05 * s, 0.025 * s))                              # the flaps tied on top
    if rifle and not wet:
        polys.append(L._cap(X((0.17, 2.02)), X((-0.15, 0.93)), 0.024 * s, 0.03 * s))
    if rim is not None:
        K.polys(c, [[(x, y - max(1.5, 0.011 * s)) for x, y in q] for q in polys], rim)
    K.polys(c, polys, K.INK)
    # the half belt and the vent catching a little light
    K.band(c, [X((-0.12, 1.02)), X((0.12, 1.02))], lerp(K.INK, K.STEEL, 0.7), max(1.5, 0.03 * s), seed=seed)
    K.band(c, [X((0.0, 0.37)), X((0.0, 0.8))], lerp(K.INK, K.STEEL, 0.45), max(1.0, 0.008 * s), seed=seed + 1)
    marks["head"] = X((hx, hy))
    marks["hem"] = X((0.0, 0.36))
    return marks


def _lie(c, t):
    ft = FILM_T0 + t
    cam = L.bank_at(t, [(T_BANK, CAM_J0), (END, CAM_J1, "out")])
    g_p = []
    for i, route in enumerate(GUARD_ROUTES):
        g_p += W.walk_prints(list(route), "guard", 0.74, 0.5, seed=GUARD_SEEDS[i])
    L.draw_bank(c, cam, ft, holes=HOLES, prints=PRINTS + tuple(g_p), moon_at=None, search=SEARCH_TO)
    # his ushanka floating in the hole
    hp = cam.px(L.HAT_AT[0] + 0.05 * math.sin(ft * 0.7), L.HAT_AT[1], W.ICE_Z - 0.02)
    hsc = cam.scale(*L.HAT_AT)
    K.ellipse(c, hp, 0.17 * hsc, 0.07 * hsc, K.INK)
    L.rings(c, hp, ft, 0.0, 0.4 * hsc, 0.14 * hsc, n=2, every=1.1, life=2.0, width=max(1.0, 0.01 * hsc), seed=9, alpha=0.4)
    lower = _k(t, T_LOWER)
    hat_k = clamp((t - T_HAT[0]) / (T_HAT[1] - T_HAT[0]))
    shake = clamp((t - T_SHAKE[0]) / (T_SHAKE[1] - T_SHAKE[0]))
    turn = 62.0 * math.sin(2.0 * math.pi * 1.5 * shake) * math.sin(math.pi * shake) if 0.0 < shake < 1.0 else 0.0
    bow = _k(t, (T_SHAKE[1] - 0.1, T_SHAKE[1] + 0.4))
    figs = [(cam.depth(x, n), i, x, n, side) for i, (x, n, side) in enumerate(J_GUARDS)]
    figs.append((cam.depth(*J_HIM), -1, J_HIM[0], J_HIM[1], 0))
    figs.sort(key=lambda f: -f[0])
    # the lanterns' light on the snow round their feet, first
    for (d, i, x, n, side) in figs:
        if i >= 0:
            s = cam.scale(x, n)
            K.glow(c, cam.px(x + 0.4 * side, n + 0.2, 0.0), 1.4 * s, lerp(0.85, 0.6, lower), ft, ry=0.45 * s, seed=40 + i)
    flames = []
    for (d, i, x, n, side) in figs:
        s = cam.scale(x, n)
        at = cam.px(x, n, 0.0)
        if i < 0:
            mk = _guard_back(c, at, s, t, wet=True, turn=turn, bow=bow, lamp_side=1, lamp_up=0.0, seed=3)
            _drips(c, mk["hem"], s, ft, n=6, seed=6, fall=0.36, spread=0.5)
            _drips(c, mk["hand_1"], s, ft, n=2, seed=7, fall=0.8, spread=0.05)
            _drips(c, mk["hand_-1"], s, ft, n=2, seed=8, fall=0.8, spread=0.05)
            L.back_breath(c, mk["head"], s, ft, rate=0.8, strength=0.8)
            continue
        if i == J_HAT:
            up = 1.0 - _k(t, (T_LOWER[0] - 0.1, T_LOWER[0] + 0.3))
            hat = 1.0 - _k(t, (T_HAT[0] + 0.2, T_HAT[0] + 0.32))
        else:
            up, hat = 1.0 - lower, 1.0
        mk = _guard_back(c, at, s, t, lamp_side=side, lamp_up=up, hat=hat, hat_hand=hat_k if i == J_HAT else 0.0,
                         seed=10 + i)
        sw = 5.0 * math.sin(2.2 * ft + i)
        hand = mk["hand_%d" % side]
        flames.append((K.lantern(c, (hand[0], hand[1] + 0.02 * s), s=0.0036 * s, lit=1.0, swing=sw, t=ft, seed=50 + i), s))
        L.back_breath(c, mk["head"], s, ft, rate=0.7 + 0.1 * i, phase=0.3 * i, strength=0.65)
    for fl, s in flames:
        K.glow(c, fl, 0.9 * s, 0.9, ft, seed=60)
    # the first snow, warmer where it falls through the lantern light
    fade = _k(t, (T_SNOW, T_SNOW + 1.2), "in")
    if fade > 0.0:
        dens = lambda tt: 0.55
        K.snow(c, ft, density=dens, n=200, wind=14.0, fall=0.8, seed=31, alpha=fade)
        for fl, s in flames:
            c.save()
            c.new_path()
            c.arc(fl[0], fl[1], 0.8 * s, 0.0, 2.0 * math.pi)
            c.clip()
            K.snow(c, ft, density=dens, n=200, wind=14.0, fall=0.8, seed=31, alpha=fade,
                   color=lerp(K.PAPER, K.AMBER, 0.4))
            c.restore()


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        if t < T_CU_W:
            _bank(c, t)
        elif t < T_GIRL:
            _cu_watch(c, t)
        elif t < T_FACE:
            _cu_girl(c, t)
        elif t < T_RIVER:
            _cu_face(c, t)
        elif t < T_GO:
            _river(c, t)
        elif t < T_PAGE:
            _go(c, t)
        elif t < T_BANK:
            _page(c, t)
        else:
            _lie(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    end = T.duration
    return [
        Cue(0.0, "wind_low", gain_db=-22, dur=T_RIVER, dc="the wind over the river, low and steady"),
        Cue(0.0, "his_breath", gain_db=-13, dur=3.0, pan=0.3, dc="his ragged, shaking breath (the recorded breath, slowed)"),
        Cue(0.1, "teeth_chatter", gain_db=-21, dur=2.5, pan=0.3, dc="his teeth chattering, small and fast"),
        Cue(T_RISE[0] + 0.1, "snow_step", gain_db=-16, pan=-0.3, dc="she gets up: a boot shifts in the snow"),
        Cue(T_FUMBLE[0] + 0.05, "cloth_rustle", gain_db=-14, dur=1.0, pan=0.3, dc="a wet glove fumbling inside a greatcoat"),
        Cue(T_FLINCH[0], "her_breath", gain_db=-12, pan=-0.3, dc="her sharp intake of breath as she flinches (recorded)"),
        Cue(T_FLINCH[0] + 0.03, "snow_scuff", gain_db=-16, pan=-0.4, dc="the girl's boots scuff back in the snow"),
        Cue(T_OPEN[0], "watch_click", gain_db=-10, dc="the watch's lid springs open: a small click. No tick: it has stopped"),
        Cue(T_DRAIN[0], "water_trickle", gain_db=-16, dur=1.2, dc="water trickling out of the watch case onto snow"),
        Cue(T_CU_W, "string_low", gain_db=-22, dur=T_RIVER - T_CU_W,
            dc="a low string chord, very quiet, under the watch and the girl's face (A minor, no movement)"),
        Cue(T_GIRL, "music_box_note", gain_db=-18, dc="one soft music-box note (E5), far away, on the match cut"),
        Cue(T_SHUT[1], "watch_click", gain_db=-8, dc="he shuts the watch: the lid's click, closer and final"),
        Cue(T_WHISTLE[0], "whistle", gain_db=-8, pan=-0.6, dc="a guard's whistle among the trees, close: two short blasts"),
        Cue(T_WHISTLE[1], "whistle", gain_db=-11, pan=-0.75, dc="a second whistle answers, a little further"),
        Cue(T_WHISTLE[2], "whistle", gain_db=-13, pan=-0.85, dc="a third"),
        Cue(T_RIVER, "snow_steps_guards", gain_db=-15, dur=T_PAGE - T_RIVER, pan=-0.6,
            dc="heavy boots in the snow among the trees, several men, coming closer, then stopping, searching"),
        Cue(T_RIVER, "lantern_creak", gain_db=-20, dur=1.6, pan=-0.6, dc="lanterns creaking on their bails as the men walk"),
        Cue(T_SPIN[0], "cloth_whip", gain_db=-14, pan=-0.2, dc="she spins round: her coat swings"),
        Cue(T_TUCK[0], "snow_scuff", gain_db=-17, pan=-0.2, dc="the girl's quick steps behind her mother"),
        Cue(T_KNEE[0], "grunt_knight", gain_db=-15, pan=0.2, dc="his effort as he gets up on one knee (a recorded grunt)"),
        Cue(T_POINT[0], "cloth_rustle", gain_db=-18, pan=0.2, dc="his wet sleeve as his arm goes out"),
        Cue(T_GRAB[0], "wool_slide", gain_db=-16, pan=-0.2, dc="the girl draws the wool scarf from her mother's fist"),
        Cue(T_CROSS[0], "snow_steps_girl", gain_db=-17, dur=T_CROSS[1] - T_CROSS[0], dc="small quick boots across the snow"),
        Cue(T_TAKE[0], "wool_slide", gain_db=-15, pan=0.1, dc="he takes the scarf from her mitten"),
        Cue(T_WIND[0], "wool_wind", gain_db=-14, dur=T_WIND[1] - T_WIND[0], dc="wool wound round a small neck, gently"),
        Cue(T_TURN2[0], "snow_step", gain_db=-14, dc="she turns and crouches; the girl climbs onto her back"),
        Cue(T_LEAVE[0], "snow_steps_mother", gain_db=-16, dur=T_LEAVE[1] - T_LEAVE[0], pan=-0.1,
            dc="her quick soft steps going away, into dry reeds"),
        Cue(T_LEAVE[0] + 0.3, "reeds_rustle", gain_db=-17, dur=1.0, pan=-0.2, dc="the reeds closing behind them"),
        Cue(T_STAND[0], "cloth_rustle", gain_db=-18, pan=0.2, dc="his wet greatcoat as he gets to his feet"),
        Cue(T_PAGE, "snow_steps_guards", gain_db=-10, dur=1.4, pan=0.1, dc="the guards arrive at a run, boots in snow, close now"),
        Cue(T_PAGE - 0.6, "searchlight_hum", gain_db=-22, dur=4.0, pan=-0.4, dc="the searchlight's motor; it swings down the river"),
        Cue(T_PAGE + 1.5, "searchlight_clank", gain_db=-24, pan=-0.2, dc="the searchlight's clank as it stops on the hole"),
        Cue(T_BANK, "string_low", gain_db=-18, dur=end - T_BANK,
            dc="a low chord under the lie: strings, A minor with the sixth (F) aching in it, swelling slowly"),
        Cue(T_LOWER[0], "lantern_creak", gain_db=-18, pan=0.2, dc="the lanterns lowered: bails creak"),
        Cue(T_HAT[0], "cloth_rustle", gain_db=-20, pan=0.15, dc="a fur hat taken off"),
        Cue(T_SNOW, "snow_shimmer", gain_db=-20, dur=end - T_SNOW,
            dc="the first snowflakes: a faint high shimmer (glass harmonics), very soft, to the end"),
        Cue(T_BANK, "water_drip", gain_db=-22, dur=end - T_BANK, pan=-0.05, dc="water dripping off his coat onto snow"),
    ]
