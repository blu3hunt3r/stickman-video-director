"""s10 SCARF (film 136-154, 18 s): the rescue along the trunk.

  A   0.0- 1.8  CU at the root plate: she sets the girl against the roots; her flat mitten: stay.
                She rises out of frame; the girl's eyes follow her up.
  B   1.8- 3.3  The section at the root: she steps up onto the trunk, drops flat on it and crawls
                out, down the bank; the girl peeks round the roots after her.
  C   3.3- 5.0  Behind her on the trunk, high: she crawls away from us along it toward the hole,
                where he clings; the false trail runs beside her into the hole.
  D   5.0- 7.1  The section at the tip: she winds the scarf's end round her wrist and throws: the
                red line flies out over the ice and falls short (6.4); his glove lunges for it and
                can't reach; the edge breaks under his other glove; he grips again.
  E   7.1- 8.7  She draws it back, edges out over the tip and throws again: it lands across his arm.
  E2  8.7- 9.4  CU at the edge, from above: his glove creeps onto the red and closes on it.
  F   9.4-10.1  The section: he winds it round his fist and heaves; his weight drags her along the
                trunk toward the hole.
  F2 10.1-10.9  CU: her boot slides along the bark and hooks behind the branch stub (10.25). It
                holds.
  G  10.9-14.0  The page: hand over hand, the red line taut. He comes up onto the edge; it breaks
                under his chest (11.75); he pushes on and slides out over the ice on his belly
                along the red line, leaving a wet track, to the trunk; she has him by the collar.
  H  14.0-15.4  The section at the tip: she drags him up onto the trunk; they work back along it.
  I  15.4-18.0  The section at the bank: off the trunk; he rolls onto his back in the snow,
                gasping, his breath steaming; she scrambles back to the girl at the roots, the
                scarf in her hand. Last frame: the three on the bank.
"""
import math
from functools import lru_cache

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from engine.paperdoll import Pose
from engine.timing import Cue
from films.thin_ice import cast as C
from films.thin_ice import faces as F
from films.thin_ice import kit as K
from films.thin_ice import world as W
from films.thin_ice.scenes import _lib_dir as L

SID = "s10"
FILM_T0 = K.film_start(SID)

T_ROOT = 1.8
T_OUT = 3.3
T_TIP = 5.0
T_CU_GRAB = 8.7
T_PULL = 9.4
T_CU_HOOK = 10.1
T_PAGE = 10.9
T_DRAG = 14.0
T_BANK = 15.4

T_PALM = (0.42, 0.66)         # her flat mitten comes up between them: stay
T_LEAVE = (1.3, 1.75)         # she rises out of frame
T_STEP_UP = (1.86, 2.2)       # onto the trunk
T_DOWN = (2.2, 2.62)          # down flat on it
T_UNWRAP = (5.0, 5.22)        # the scarf off her neck
T_WIND = (5.22, 5.52)         # its end round her far wrist
T_REL1 = 5.8                  # the first throw lets go ...
T_LAND1 = 6.39                # ... and falls short
T_LUNGE = (6.42, 6.6)         # his glove shoots out for it
T_CRUMBLE = 6.74              # the edge breaks under his other glove
T_REGRIP = 7.0
T_DRAW = (7.12, 7.5)          # she draws it back, hand over hand
T_EDGE = (7.5, 7.78)          # and edges out over the tip
T_REL2 = 8.0                  # the second throw ...
T_LAND2 = 8.48                # ... across his arm
T_CLOSE = (8.86, 9.02)        # his glove closes on the red
T_TUG = (9.06, 9.34)
T_FIST = (9.42, 9.68)         # he winds it round his fist
T_HEAVE = 9.72                # and heaves: his weight drags her toward the hole
T_HOOK = 10.38                # her boot hooks the stub
T_UP = (11.1, 11.55)          # his chest comes up onto the edge
T_BREAK = 11.75               # the edge breaks under him
T_PUSH = 12.0
T_SLIDE = (12.1, 13.5)        # he slides out over the ice on his belly
T_COLLAR = 13.62              # she has him by the collar
T_ONTO = (14.05, 14.8)        # up onto the trunk
T_BACK = (14.85, 15.4)        # working back along it
T_OFF = (15.4, 15.95)         # off the trunk
T_ROLL = (15.9, 16.45)        # he rolls onto his back
T_TO_GIRL = (16.3, 16.95)     # she scrambles back to the girl

PRINTS = W.prints_before(SID)
HOLES = W.holes_before(SID)
D_TRUNK = W.SECTION_X - 0.5 * (W.TRUNK[0][0] + W.TRUNK[1][0])    # the trunk's depth behind the cut (1.1 m)
TIP_N = W.TRUNK[1][1]
EDGE_S, EDGE_N = 10.104, 12.496     # the big hole's edges in the cut
MOON_SEC = (880.0, 360.0)
LIGHT_CU = (0.55, -0.85)
GIRL_N = -3.12                      # the girl, crouched against the root plate's south side


def _ik(pt, pv, roll, s):
    """A frame point as an 'ik' arm target for a figure drawn turned `roll` about its pelvis pv."""
    q = L.turn_pt(pt, pv, -roll)
    return ("ik", ((q[0] - pv[0]) / s, (q[1] - pv[1]) / s))


def _bm(p, pel, roll, facing=1):
    """A world point (n, z) in the body frame of a figure whose pelvis is at pel, turned `roll`
    degrees clockwise: metres (forward, down), as free_state places the feet."""
    dn, dz = p[0] - pel[0], p[1] - pel[1]
    a = math.radians(roll)
    x = dn * math.cos(a) - dz * math.sin(a)
    z = dn * math.sin(a) + dz * math.cos(a)
    return (facing * x, -z)


def _bump(t, t0, t1):
    """0 -> 1 -> 0 across [t0, t1]."""
    u = (t - t0) / (t1 - t0)
    return math.sin(math.pi * clamp(u)) if 0.0 < u < 1.0 else 0.0


def _px_per_m(j, who="mother"):
    return j["scale"] / C.M_PER_UNIT[who]


# ============================================================================ the scarf, drawn
SCARF_W = 0.15                     # its width (m)
STRIPE = lerp(K.RED, K.INK, 0.38)


def scarf_strip(c, pts, t, width, fringe=True, seed=0):
    """The red scarf along a polyline (frame px), its last point the free end: two knitted stripes
    near the end and a fringe of short strands swinging there (fringe=False: the end is in a fist)."""
    pts = [p for i, p in enumerate(pts) if i == 0 or math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) > 0.5]
    if len(pts) < 2:
        return
    K.band(c, pts, K.RED, width, seed=11 + seed, taper=(1.0, 1.0))
    if not fringe:
        return
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    L_ = math.hypot(bx - ax, by - ay) or 1.0
    ux, uy = (bx - ax) / L_, (by - ay) / L_
    nx, ny = -uy, ux
    for k, back in enumerate((0.55, 0.9)):
        cx, cy = bx - ux * width * back, by - uy * width * back
        K.band(c, [(cx - nx * width * 0.5, cy - ny * width * 0.5), (cx + nx * width * 0.5, cy + ny * width * 0.5)],
               STRIPE, width * 0.13, seed=31 + k)
    for i in range(6):
        off = (i / 5.0 - 0.5) * width * 0.85
        base = (bx + nx * off, by + ny * off)
        sw = 0.25 * math.sin(t * 6.0 + i * 1.3 + seed)
        ln = width * (0.55 + 0.2 * hash01(seed, i))
        tip = (base[0] + (ux + nx * sw) * ln, base[1] + (uy + ny * sw) * ln)
        K.band(c, [base, tip], K.RED, max(2.0, width * 0.09), seed=41 + i, taper=(1.0, 0.5))


def _wraps(c, p, r, ang=0.0, n=2):
    """The scarf's end wound round a wrist: red turns across it."""
    ca, sa = math.cos(ang), math.sin(ang)
    for k in range(n):
        off = (k - 0.5 * (n - 1)) * r * 0.75
        a = (p[0] + ca * off - sa * r, p[1] + sa * off + ca * r)
        b = (p[0] + ca * (off + r * 0.3) + sa * r, p[1] + sa * (off + r * 0.3) - ca * r)
        K.band(c, [a, b], K.RED, r * 0.55, seed=81 + k)


def _bundle(c, near, far, s_m, t=0.0):
    """The rest of the scarf bunched in her near hand, a loop hanging from it, a strand back to
    the wound wrist."""
    K.band(c, [far, near], K.RED, max(4.0, 0.045 * s_m), seed=83)
    K.ellipse(c, near, 0.08 * s_m, 0.05 * s_m, K.RED, angle=-20.0)
    K.ellipse(c, (near[0] + 0.03 * s_m, near[1] + 0.025 * s_m), 0.06 * s_m, 0.04 * s_m, K.RED, angle=35.0)
    sw = 0.03 * math.sin(t * 5.0)
    K.band(c, [near, (near[0] + (0.02 + sw) * s_m, near[1] + 0.12 * s_m), (near[0] + (0.07 + sw) * s_m, near[1] + 0.15 * s_m)],
           K.RED, max(3.0, 0.035 * s_m), seed=84, taper=(1.0, 0.7))


def _neck_scarf(c, j, who="mother", k=1.0):
    """The scarf loosely round her neck (B, D): a red collar and a short end hanging (k < 1: it
    is coming off)."""
    m = _px_per_m(j, who)
    nk, hd = j["neck"], j["head"]
    a = math.atan2(hd[1] - nk[1], hd[0] - nk[0])
    K.ellipse(c, nk, 0.075 * m * k, 0.045 * m, K.RED, angle=math.degrees(a) + 90.0)
    end = (nk[0] - 0.02 * m * math.cos(a), nk[1] + 0.16 * m * k)
    K.band(c, [nk, end], K.RED, 0.05 * m, seed=85, taper=(1.0, 0.8))


# ============================================================================ the trunk, in the section
# world.draw_trunk_side's trunk, its stubs split by side: the one her boot hooks stands out of
# the trunk's near (east) side, so she lies behind it; the others are behind her.
STUBS_SEC = ((0.2, 0.5, 70.0, False), (0.36, 0.7, 110.0, False), (0.55, 0.45, 60.0, False),
             ((W.STUB_N - W.TRUNK[0][1]) / (W.TRUNK[1][1] - W.TRUNK[0][1]), 0.17, 105.0, True))
STUB_W = 0.085                      # the hooking stub's thickness at its base (m)
PLATE_COL = lerp(K.INK, W.STEEL, 0.3)


def _trunk_pts():
    """The trunk's outline on the cut plane, its tip end ragged where the crown broke away."""
    top, bot = W.trunk_side_pts()
    (na, za), (nb, zb) = top[-1], bot[-1]
    h = za - zb
    tip = [(na + 0.05, za - 0.18 * h), (na - 0.03, za - 0.36 * h), (na + 0.09, za - 0.52 * h), (na + 0.01, za - 0.7 * h),
           (na + 0.06, za - 0.86 * h)]
    return top + tip + bot[::-1]


def _plate_sec(c, cam, d):
    """The root plate standing up at the trunk's root, edge on: a ragged disc of frozen earth with
    roots splaying out of it all round, snow lodged along its top, the moon on its edge."""
    n0 = W.TRUNK[0][1] - 0.25
    zc = W.land_z(W.TRUNK[0][1]) + 0.9
    out = []
    for i in range(40):
        a = 6.283 * i / 40
        rr = 1.0 + 0.13 * K._sn(i, 51) + 0.06 * K._sn(i, 52)
        out.append((n0 + 0.44 * rr * math.cos(a), zc + 1.2 * rr * math.sin(a)))
    pts = [cam.px(n, z, d) for n, z in out]
    sc = cam.scale(d)
    roots = []
    for j in range(17):
        a = 6.283 * (j + 0.4 * hash01(j, 53)) / 17
        if math.sin(a) < -0.75:                 # none down into the bank
            continue
        r0 = (n0 + 0.42 * math.cos(a), zc + 1.15 * math.sin(a))
        ln = 0.18 + 0.4 * hash01(j, 54)
        b = a + 0.45 * K._sn(j, 55)
        r1 = (r0[0] + ln * math.cos(b), r0[1] + ln * math.sin(b))
        mid = ((r0[0] + r1[0]) / 2 + 0.06 * K._sn(j, 56), (r0[1] + r1[1]) / 2 + 0.06 * K._sn(j, 57))
        roots.append(([cam.px(*r0, d), cam.px(*mid, d), cam.px(*r1, d)], max(1.5, (0.03 + 0.04 * hash01(j, 58)) * sc), j))
    for p, w, j in roots:
        K.band(c, [(x + 2.5, y - 2.5) for x, y in p], L.RIM, w, seed=500 + j, taper=(1.0, 0.1), alpha=0.6)
    K.poly(c, [(x + 3.0, y - 3.0) for x, y in pts], L.RIM, alpha=0.7)
    for p, w, j in roots:
        K.band(c, p, PLATE_COL, w, seed=500 + j, taper=(1.0, 0.1))
    K.poly(c, pts, PLATE_COL)
    # snow lodged along the top, the trunk's root end going into it, a few clods
    arc = [cam.px(n0 + 0.4 * math.cos(math.radians(a)), zc + 1.13 * math.sin(math.radians(a)), d) for a in range(35, 150, 8)]
    K.band(c, arc, lerp(W.SNOW, K.NIGHT, 0.3), max(2.0, 0.07 * sc), seed=510, taper=(0.3, 0.6))
    for k in range(5):
        a = math.radians(200.0 + 32.0 * k)
        K.ellipse(c, cam.px(n0 + 0.3 * math.cos(a), zc + 0.85 * math.sin(a), d), 0.05 * sc, 0.035 * sc,
                  lerp(PLATE_COL, K.INK, 0.5), angle=30.0 * k)


def _trunk_sec(c, cam, near=False, bend=0.0, color=K.INK, rim=None):
    d = D_TRUNK
    if not near:
        K.poly(c, [cam.px(n, z, d) for n, z in _trunk_pts()], color)
        _plate_sec(c, cam, d)
    for j, (u, ln, ang, is_near) in enumerate(STUBS_SEC):
        if is_near != near:
            continue
        n = lerp(W.TRUNK[0][1], W.TRUNK[1][1], u)
        z = W.trunk_top_z(n)
        a = math.radians(ang + (bend if is_near else 0.0))
        p0, p1 = cam.px(n, z - 0.05, d), cam.px(n + ln * math.cos(a), z + ln * math.sin(a), d)
        w = max(1.5, (STUB_W if is_near else 0.07) * cam.scale(d))
        tp = (1.0, 0.7) if is_near else (1.0, 0.35)
        if rim is not None:
            K.band(c, [(p0[0] + 2.5, p0[1] - 2.5), (p1[0] + 2.5, p1[1] - 2.5)], rim, w, seed=70 + j, taper=tp)
        K.band(c, [p0, p1], color, w, seed=70 + j, taper=tp)


# ============================================================================ the scarf, thrown
# A rope of points in the section's plane (n, z), 1.75 m long. Its end is wound round her far
# wrist; she throws the rest from her near hand. Verlet steps at 720 Hz, pinned at the wrist,
# landing on the trunk, the snow on the white ice, his forearm by the edge, the water.
SCARF_N = 30
SCARF_L = 1.75
SEG = SCARF_L / (SCARF_N - 1)
WRAP = 4                            # the points wound round her wrist
TT = W.trunk_top_z(8.4)             # the trunk's top by its tip
M_N1, M_N2 = 7.3, 7.55              # her pelvis for the first throw, and edged out for the second
WRIST_F = 1.02                      # her far wrist ahead of her pelvis, the arm out along the trunk
HAND_REL = 0.82                     # her near hand ahead of her pelvis as she lets go, up off the trunk
THROWS = {1: ((M_N1 + WRIST_F, TT + 0.04), (M_N1 + HAND_REL, TT + 0.5), (3.0, 1.6), False),
          2: ((M_N2 + WRIST_F, TT + 0.04), (M_N2 + HAND_REL + 0.01, TT + 0.52), (4.5, 2.0), True)}


def _ground(n, arm):
    if n <= TIP_N:
        return W.trunk_top_z(n) + 0.01
    if arm and 9.86 <= n <= 10.22:          # his forearm on the ice
        return W.ICE_Z + 0.1
    if n < W.BAND[0]:
        return W.ICE_Z + W.SNOW_T + 0.005
    if n < EDGE_S:
        return W.ICE_Z + 0.005
    return W.ICE_Z - 0.02


def _simulate(wrist, hand, vel, arm, t_len=1.0, drag=1.2, spread=0.25):
    dt = 1.0 / 720.0
    nf = SCARF_N - WRAP + 1
    dx, dz = hand[0] - wrist[0], hand[1] - wrist[1]
    m = max(1, int(math.hypot(dx, dz) / SEG))
    pts = [[wrist[0] + dx * i / m, wrist[1] + dz * i / m] for i in range(m + 1)]
    r, ang = 0.08, math.atan2(dz, dx) - math.pi / 2
    cx, cz = hand[0] - r * math.cos(ang), hand[1] - r * math.sin(ang)
    while len(pts) < nf:
        ang += SEG / r
        pts.append([cx + r * math.cos(ang), cz + r * math.sin(ang)])

    def relax():
        for i in range(nf - 1):
            a, b = pts[i], pts[i + 1]
            ex, ez = b[0] - a[0], b[1] - a[1]
            d = math.hypot(ex, ez) or 1e-9
            k = (d - SEG) / d
            if i == 0:
                b[0] -= ex * k
                b[1] -= ez * k
            else:
                a[0] += ex * k * 0.5
                a[1] += ez * k * 0.5
                b[0] -= ex * k * 0.5
                b[1] -= ez * k * 0.5
    for _ in range(60):
        relax()
    prev = []
    for i, p in enumerate(pts):
        w = 0.0 if i == 0 else (min(1.0, i / m) ** 2 if i <= m else 1.0 + spread * (i - m) / (nf - m))
        prev.append([p[0] - vel[0] * w * dt, p[1] - vel[1] * w * dt])
    out = []
    for step in range(int(t_len / dt) + 1):
        if step % 3 == 0:
            out.append(tuple((p[0], p[1]) for p in pts))
        for i in range(1, nf):
            p, q = pts[i], prev[i]
            vx, vz = (p[0] - q[0]) * (1.0 - drag * dt), (p[1] - q[1]) * (1.0 - drag * dt)
            q[0], q[1] = p[0], p[1]
            p[0] += vx
            p[1] += vz - 9.8 * dt * dt
        for _ in range(12):
            relax()
            for i in range(1, nf):
                p = pts[i]
                g = _ground(p[0], arm)
                if p[1] < g:
                    p[1] = g
                    q = prev[i]
                    q[0] = p[0] - (p[0] - q[0]) * 0.55
                    q[1] = min(q[1], p[1])
    return tuple(out)


@lru_cache(maxsize=None)
def _flight(k):
    wrist, hand, vel, arm = THROWS[k]
    return _simulate(wrist, hand, vel, arm)


def _flight_at(k, u):
    """Throw k's scarf u s after she lets go (between the 1/240 s samples)."""
    fr = _flight(k)
    x = clamp(u, 0.0, 1.0) * 240.0
    i = min(int(x), len(fr) - 2)
    a = x - i
    return [(lerp(p[0], q[0], a), lerp(p[1], q[1], a)) for p, q in zip(fr[i], fr[i + 1])]


def _arc(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return s


def _at_arc(pts, s, a):
    if a <= 0.0:
        return pts[0]
    for i in range(1, len(pts)):
        if a <= s[i]:
            u = (a - s[i - 1]) / max(s[i] - s[i - 1], 1e-9)
            return (lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u))
    return pts[-1]


def _pulls(u, n):
    """Hand over hand: n pulls across u 0..1, each quick then a pause to reach again."""
    k = min(int(u * n), n - 1)
    q = u * n - k
    return (k + ease("inout", clamp(q / 0.6))) / n


def _scarf_sec(t, hands):
    """The scarf in the section (D-F): its points (n, z) out from her far hand, and whether its
    end is free; None while it is bunched in her hand."""
    far = hands[1]
    if t < T_REL1 or T_DRAW[1] <= t < T_REL2:
        return None
    if t < T_DRAW[0]:
        pts = _flight_at(1, t - T_REL1)
    elif t < T_DRAW[1]:
        rest = _flight_at(1, 1.0)
        s = _arc(rest)
        r = s[-1] * _pulls((t - T_DRAW[0]) / (T_DRAW[1] - T_DRAW[0]), 2)
        pts = [_at_arc(rest, s, a - r) for a in s if a >= r]
        if len(pts) < 2:
            return None
    elif t < T_PULL:
        pts = _flight_at(2, t - T_REL2)
    else:
        # in his fist: from her far hand to it, the slack going out of it as he heaves
        g = _g_state(t)[2]
        sag = 0.07 * (1.0 - ease("out", clamp((t - T_PULL) / (T_HEAVE - T_PULL))))
        pts = [(lerp(far[0], g[0], i / 12.0), lerp(far[1], g[1], i / 12.0) - sag * math.sin(math.pi * i / 12.0))
               for i in range(13)]
        return pts, False
    return [far] + list(pts[1:]), True


# ============================================================================ her, in the section
M_LIFT = 0.12                       # her pelvis above the trunk's top, lying flat on it
M_FEET = 0.86                       # pelvis to boot soles, lying flat
M_HOOK = W.STUB_N - 0.07 + M_FEET   # her pelvis once her boot is hooked behind the stub
CRAWL_STEP = 0.77                   # metres she moves per crawl cycle (two pulls)


def _m_n(t):
    """Her pelvis's n along the trunk (D-H): still for the first throw, edged out for the second,
    dragged toward the hole by his weight till her boot hooks the stub, then working back."""
    return L.track(t, [(T_TIP, M_N1), (T_EDGE[0], M_N1), (T_EDGE[1], M_N2), (T_HEAVE, M_N2), (T_HOOK, M_HOOK, "in"),
                       (T_BACK[0], M_HOOK), (T_BACK[1], M_HOOK - 0.55)])


def _flat(n_p, lift=0.0):
    """Her pelvis (n, z) and roll, lying flat along the trunk at n_p."""
    zt = W.trunk_top_z(n_p)
    zh = W.trunk_top_z(n_p + 0.7)
    slope = math.degrees(math.atan2(zt - zh, 0.7))
    return (n_p, zt + M_LIFT / math.cos(math.radians(slope)) + lift), 90.0 + slope


def _legs_flat(kick=None):
    """Feet (body m) lying flat: trailing straight, or a crawl's knees drawing up by turns."""
    if kick is None:
        return (0.1, M_FEET - 0.02), (0.05, M_FEET)
    out = []
    for off in (0.0, 0.5):
        k = max(0.0, math.sin(2.0 * math.pi * (kick + off)))
        out.append((0.1 + 0.12 * k, M_FEET - 0.3 * k))
    return tuple(out)


def _crawl_hands(n_p, ph, reach=1.0, z_of=None):
    """Her hands working along the trunk in a belly crawl: each plants ahead and holds while the
    body slides up to it (so it stays put on the bark), then lifts and reaches again."""
    z_of = z_of or (lambda n: W.trunk_top_z(min(n, TIP_N)) + 0.03)
    out = []
    for off in (0.0, 0.5):
        q = (ph + off) % 1.0
        if q < 0.65:
            rel, lift = lerp(reach, reach - 0.5, q / 0.65), 0.0
        else:
            u = (q - 0.65) / 0.35
            rel, lift = lerp(reach - 0.5, reach, ease("inout", u)), 0.1 * math.sin(math.pi * u)
        out.append((n_p + rel, z_of(n_p + rel) + lift))
    return tuple(out)


def _throw_hand(t, t_rel, n_p, tt):
    """Her near hand through a throw from flat on her belly: drawn back and up beside her head,
    whipped forward and up to let go at t_rel, following through down onto the trunk."""
    return L.track(t, [(t_rel - 0.25, (n_p + 0.92, tt + 0.03)), (t_rel - 0.08, (n_p + 0.5, tt + 0.42)),
                       (t_rel, (n_p + HAND_REL, tt + 0.5), "in"), (t_rel + 0.25, (n_p + 1.06, tt + 0.06), "out")])


def _m_tip(t):
    """Her at the trunk's tip (D-F): pelvis, roll, hands (n, z), feet, head tilt."""
    n_p = _m_n(t)
    lift, head = 0.0, 76.0
    legs = _legs_flat()
    tt = W.trunk_top_z(min(n_p + WRIST_F, TIP_N))
    far = (n_p + WRIST_F, tt + 0.04)
    near = (n_p + 0.92, tt + 0.03)
    if t < T_UNWRAP[1]:
        # her near hand at her collar, drawing the scarf off her neck and forward
        u = ease("inout", clamp((t - T_UNWRAP[0]) / (T_UNWRAP[1] - T_UNWRAP[0])))
        near = (lerp(n_p + 0.52, n_p + 0.92, u), lerp(tt + 0.26, tt + 0.05, u))
        head = 66.0
    elif T_WIND[0] <= t < T_WIND[1]:
        u = (t - T_WIND[0]) / (T_WIND[1] - T_WIND[0])
        a = 4.0 * math.pi * ease("inout", u)
        near = (far[0] - 0.09 * math.cos(a), far[1] + 0.05 + 0.08 * math.sin(a))
        head = 58.0
    elif T_REL1 - 0.25 <= t < T_REL1 + 0.3:
        near = _throw_hand(t, T_REL1, n_p, tt)
        lift = 0.07 * _bump(t, T_REL1 - 0.25, T_REL1 + 0.3)
        head = 84.0
    elif T_DRAW[0] <= t < T_DRAW[1]:
        q = ((t - T_DRAW[0]) / (T_DRAW[1] - T_DRAW[0]) * 2.0) % 1.0
        if q < 0.6:
            near = (lerp(n_p + 1.14, n_p + 0.6, ease("inout", q / 0.6)), tt + 0.04)
        else:
            u = (q - 0.6) / 0.4
            near = (lerp(n_p + 0.6, n_p + 1.14, ease("inout", u)), tt + 0.04 + 0.1 * math.sin(math.pi * u))
    elif T_EDGE[0] <= t < T_EDGE[1]:
        ph = (n_p - M_N1) / CRAWL_STEP
        near, far = _crawl_hands(n_p, ph, reach=1.05)
        legs = _legs_flat(kick=ph)
    elif T_REL2 - 0.25 <= t < T_REL2 + 0.3:
        near = _throw_hand(t, T_REL2, n_p, tt)
        lift = 0.07 * _bump(t, T_REL2 - 0.25, T_REL2 + 0.3)
        head = 84.0
    elif t >= T_HEAVE:
        pull = ease("out", clamp((t - T_HEAVE) / 0.15))
        near = (n_p + 1.12 + 0.1 * pull, tt + 0.07)
        far = (n_p + WRIST_F + 0.12 * pull, tt + 0.05)
        head = lerp(76.0, 62.0, pull)
    pel, roll = _flat(n_p, lift)
    return pel, roll, (near, far), legs, head


def _draw_mother(c, cam, pel, roll, hands, legs, head=70.0, d=D_TRUNK, facing=1, rim=L.RIM, neck=False, lean=0.0,
                 stand=None):
    """Her in the section: free-bodied (lying, kneeling) about her pelvis, or standing (stand: a
    state from L.stance) at pel's n on the ground."""
    s = C.scale("mother", cam.scale(d))
    if stand is not None:
        at = cam.px(pel[0], pel[1], d)
        pv = (at[0], at[1] + s * stand["pelvis"][1])
        arms = {"near": _ik(cam.px(hands[0][0], hands[0][1], d), pv, roll, s),
                "far": _ik(cam.px(hands[1][0], hands[1][1], d), pv, roll, s)}
        pose = C.still_pose("mother", lean=lean, head=head, arms=arms)
        j = L.figure_at(c, "mother", stand, pose, at, s, facing, roll, rim=rim)
    else:
        pv = cam.px(pel[0], pel[1], d)
        arms = {"near": _ik(cam.px(hands[0][0], hands[0][1], d), pv, roll, s),
                "far": _ik(cam.px(hands[1][0], hands[1][1], d), pv, roll, s)}
        st = L.free_state("mother", legs[0], legs[1], pitch=(70.0, 70.0), skirt=True)
        pose = Pose(lean=lean, head=head, arms=arms, springs=dict(C.REST), eye=1.0)
        j = L.figure(c, cam, "mother", st, pose, pel[0], pel[1], d, facing, roll, rim=rim)
    if neck:
        _neck_scarf(c, j)
    return j


# ============================================================================ him, in the section
G_PELVIS = (10.58, -1.18)           # s08's end: in the hole at its near edge, facing her


def _g_state(t):
    """His pelvis (u, z), roll, near and far hands (n, z), head tilt in the section (D-F)."""
    bob = 0.02 * math.sin(t * 3.4)
    pel = (G_PELVIS[0], G_PELVIS[1] + bob)
    roll, head = 12.0, 10.0
    claw = 0.015 * math.sin(t * 6.0)
    hn = (EDGE_S - 0.05 + claw, W.ICE_Z + 0.03)
    hf = (EDGE_S - 0.16 - claw, W.ICE_Z + 0.03)
    # the lunge for the short throw: his near glove shoots out along the ice, short
    lu = ease("out3", clamp((t - T_LUNGE[0]) / (T_LUNGE[1] - T_LUNGE[0]))) * (1.0 - ease("inout", clamp((t - T_CRUMBLE) / 0.12)))
    if lu > 0.0:
        hn = (lerp(hn[0], 9.78, lu), lerp(hn[1], W.ICE_Z + 0.07, lu))
        pel = (pel[0] - 0.12 * lu, pel[1] + 0.06 * lu)
        roll += 18.0 * lu
        head += 12.0 * lu
    # the edge breaks under his far glove: he drops, scrabbles, grips again
    dip = _bump(t, T_CRUMBLE, T_REGRIP)
    if dip > 0.0:
        pel = (pel[0] + 0.05 * dip, pel[1] - 0.22 * dip)
        hf = (hf[0] + 0.1 * dip, hf[1] - 0.16 * dip)
        hn = (hn[0] + 0.05 * dip, hn[1] - 0.05 * dip)
        head += 30.0 * dip
    if t >= T_PULL:
        # his near fist on the scarf, winding it round, then heaving
        wind = clamp((t - T_FIST[0]) / (T_FIST[1] - T_FIST[0]))
        heave = ease("out", clamp((t - T_HEAVE) / 0.3))
        a = 2.0 * math.pi * 1.5 * wind
        hn = (9.98 + 0.03 * math.cos(a) * (1.0 - heave) + 0.12 * heave,
              W.ICE_Z + 0.06 + 0.03 * math.sin(a) * (1.0 - heave) + 0.05 * heave)
        pel = (pel[0] + 0.02 * heave, pel[1] + 0.1 * heave)
        roll -= 6.0 * heave
        head = 4.0
    return pel, roll, hn, hf, head


def _draw_guard(c, cam, t, pel, roll, hands, head=10.0, d=0.0, facing=-1, legs=None, rim=L.RIM):
    s = C.scale("guard", cam.scale(d))
    pv = cam.px(pel[0], pel[1], d)
    arms = {side: _ik(cam.px(hp[0], hp[1], d), pv, roll, s) for side, hp in zip(("near", "far"), hands)}
    if legs is None:
        legs = ((0.15 + 0.1 * math.sin(t * 6.0), 0.6), (-0.1 - 0.1 * math.sin(t * 6.0), 0.58))
    st = L.free_state("guard_wet", legs[0], legs[1], (-50.0, -50.0), skirt=True)
    pose = Pose(lean=8.0, head=head, arms=arms, springs=dict(C.REST), eye=1.0)
    return L.figure(c, cam, "guard_wet", st, pose, pel[0], pel[1], d, facing, roll, rim=rim)


def _crumble_piece(c, cam, t):
    """The bit of edge that breaks under his far glove (6.74): it tips into the water and sinks."""
    u = t - T_CRUMBLE
    if u < 0.0 or u > 0.9:
        return
    ang = math.radians(-70.0 * ease("out3", clamp(u / 0.25)))
    sink = 0.35 * ease("in", clamp(u / 0.9))
    hn, hz = EDGE_S - 0.02, W.ICE_Z - sink
    base = [(-0.13, 0.0), (0.0, 0.0), (0.0, -W.THIN_T), (-0.13, -W.THIN_T)]
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [cam.px(hn + x * ca - y * sa, hz + x * sa + y * ca) for x, y in base]
    K.poly(c, pts, lerp(W.THIN, K.WATER, clamp(u / 0.6)))


# ============================================================================ D, E, F: at the tip (5-8.7, 9.4-10.1)
CAM_D0 = W.Dio(8.95, -0.75, 255.0, eye=-0.1)
CAM_D1 = W.Dio(9.25, -0.75, 280.0, eye=-0.1)
CAM_F = W.Dio(9.4, -0.75, 280.0, eye=-0.1)


def _tip(c, t):
    ft = FILM_T0 + t
    if t < T_PULL:
        cam = L.dio_at(t, [(T_TIP, CAM_D0), (T_REL1 + 0.05, CAM_D0), (T_REL1 + 0.55, CAM_D1)])
    else:
        cam = L.dio_at(t, [(T_PULL, CAM_D1), (T_HOOK, CAM_F)])
    W.draw_river(c, cam, ft, holes=HOLES, moon_at=MOON_SEC, trunk=False)
    _trunk_sec(c, cam)
    pel, roll, hands, legs, head = _m_tip(t)
    j = _draw_mother(c, cam, pel, roll, hands, legs, head=head)
    s_m = _px_per_m(j)
    _trunk_sec(c, cam, near=True, rim=L.RIM)
    gp, groll, ghn, ghf, ghead = _g_state(t)
    gj = _draw_guard(c, cam, t, gp, groll, (ghn, ghf), head=ghead)
    L.wash(c, cam, EDGE_S, EDGE_N, alpha=0.62)
    L.waterline(c, cam, EDGE_S, EDGE_N, ft, seed=5, amp=2.5)
    _crumble_piece(c, cam, t)
    # the scarf: off her neck; its end wound round her far wrist; the rest bunched in her near
    # hand, or out on the ice
    nearp = j.get("hand_near", cam.px(hands[0][0], hands[0][1], D_TRUNK))
    farp = j.get("hand_far", cam.px(hands[1][0], hands[1][1], D_TRUNK))
    sc = _scarf_sec(t, hands)
    w = max(10.0, 0.06 * s_m)
    if t < T_UNWRAP[1]:
        k = clamp((t - T_UNWRAP[0]) / (T_UNWRAP[1] - T_UNWRAP[0]))
        _neck_scarf(c, j, k=1.0 - 0.8 * k)
        scarf_strip(c, [j["neck"], nearp], ft, w * 0.8, fringe=False, seed=1)
        K.ellipse(c, nearp, 0.05 * s_m * (0.5 + k), 0.035 * s_m * (0.5 + k), K.RED)
    elif sc is None:
        if t < T_WIND[1]:
            k = clamp((t - T_WIND[0]) / (T_WIND[1] - T_WIND[0]))
            _bundle(c, nearp, (lerp(nearp[0], farp[0], k), lerp(nearp[1], farp[1], k)), s_m, ft)
        else:
            _bundle(c, nearp, farp, s_m, ft)
    else:
        pts, free = sc
        dd = lambda n: lerp(D_TRUNK, 0.0, clamp((n - 8.4) / 1.6))
        scarf_strip(c, [cam.px(n, z, dd(n)) for n, z in pts], ft, w, fringe=free, seed=2)
        if not free:
            gh = cam.px(*ghn)
            K.ellipse(c, gh, 0.07 * s_m, 0.06 * s_m, K.INK)          # his fist over the wound end
    if t >= T_WIND[0] + 0.15:
        _wraps(c, farp, 0.045 * s_m, ang=math.radians(roll - 90.0))
    # spray: the scarf landing, the edge breaking
    for t0, n, pw in ((T_LAND1, 9.45, 0.5), (T_LAND2, 9.95, 0.6), (T_CRUMBLE, 10.02, 1.0)):
        L.spray(c, cam.px(n, W.ICE_Z + 0.02), t, t0, cam.ppm, n=14, seed=int(t0 * 10), power=pw, spread=0.8)
    # breath: his, ragged; hers held while she throws, let go after
    K.breath(c, gj["mouth"], t, pant=2.2, facing=-1, s=1.3, phase=0.1, strength=0.9, seed=8)
    if not (T_REL1 - 0.3 < t < T_REL1 + 0.4 or T_REL2 - 0.3 < t < T_REL2 + 0.4):
        K.breath(c, j["mouth"], t, rate=0.75, facing=1, s=1.2, phase=0.3, strength=0.75, seed=9)


# ============================================================================ E2: his glove closes on it (8.7-9.4)
CAM_E2 = W.Plan(12.93, 9.92, 1300.0)
ARM_SH = (13.12, 10.36)             # his near shoulder, in the water at the hole's edge (hole_guard's)


def _plan_scarf(t):
    """The scarf on the ice as it fell, from above (map points): from her wrist toward his glove."""
    a, b = (12.6, 8.57), (12.915, 10.01)
    pts = []
    for i in range(10):
        u = i / 9.0
        side = 0.05 * math.sin(u * 7.0 + 0.6) * (1.0 - u * 0.4)
        pts.append((lerp(a[0], b[0], u) + side, lerp(a[1], b[1], u)))
    return pts


def _glove_cu(c, t):
    ft = FILM_T0 + t
    cam = CAM_E2
    K.fill(c, W.ICE)
    x0, x1, n0, n1 = cam.bounds(0.3)
    K.poly(c, cam.pts([(x0, W.BAND[0]), (x1, W.BAND[0]), (x1, n1), (x0, n1)]), W.THIN)
    W.draw_hole(c, cam, W.HOLE_BIG, W.HOLE_R[1], 62)
    L.rings(c, cam.px((13.08, 10.3)), t, 0.0, 0.25 * cam.ppm, 0.08 * cam.ppm, n=3, every=0.5, life=1.4, width=3.0, seed=6,
            alpha=0.5)
    tug = ease("inout", clamp((t - T_TUG[0]) / (T_TUG[1] - T_TUG[0])))
    creep = ease("inout", clamp((t - 8.72) / 0.14))
    close = ease("out3", clamp((t - T_CLOSE[0]) / (T_CLOSE[1] - T_CLOSE[0])))
    claw = 0.5 + 0.5 * math.sin(ft * 7.0)
    tip = (12.93 - 0.03 * creep, 9.965 - 0.035 * creep + 0.12 * tug)
    wrist = (13.0 + 0.0 * creep, 10.13 + 0.12 * tug)
    # the scarf: its end under his glove, drawn along with it as he tugs
    pts = _plan_scarf(t)
    end = (tip[0] + 0.02, tip[1] + 0.03)
    pts = [(lerp(p[0], end[0], (i / 9.0) ** 2 * tug), lerp(p[1], end[1] - 0.12 * (1 - i / 9.0) * tug, (i / 9.0) ** 2 * tug) + 0.1 * tug * (i / 9.0))
           for i, p in enumerate(pts)]
    pts[-1] = end if tug > 0.0 else pts[-1]
    scarf_strip(c, cam.pts(pts), ft, SCARF_W * cam.ppm, fringe=close < 0.5, seed=4)
    # his arm out of the water onto the ice; the glove
    sh, wr = cam.px(ARM_SH), cam.px(wrist)
    K.band(c, [(sh[0] + 4.0, sh[1] - 4.0), (wr[0] + 4.0, wr[1] - 4.0)], L.RIM_WET, 0.13 * cam.ppm, seed=7, alpha=0.8)
    K.band(c, [sh, wr], K.INK, 0.13 * cam.ppm, seed=7)
    F.glove(c, cam.px(wrist), cam.px(tip), 0.0011 * cam.ppm, curl=close, spread=0.6 * (1.0 - close) * claw, rim=L.RIM_WET,
            light=(0.6, -0.8), rim_w=5.0, sleeve=False)
    if close > 0.0:
        L.spray(c, cam.px(tip), t, T_CLOSE[0] + 0.05, cam.ppm * 0.25, n=10, seed=21, power=0.4, spread=1.4)


# ============================================================================ F2: her boot hooks the stub (10.1-10.9)
CAM_F2 = W.Dio(7.3, -0.37, 900.0, eye=-0.3)
BOOT_PITCH = -70.0                  # her toes dug into the bark, the shin rising to her knee
BOOT_LEN = 0.27                     # the felt boot's sole (m); F.boot's is 264 units


def _boot_rot(p, pitch=BOOT_PITCH):
    """A point of F.boot's outline (boot units from its heel) as drawn at `pitch`."""
    a = math.radians(-pitch)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


def _bottom_z(n):
    _, bot = W.trunk_side_pts()
    for (na, za), (nb, zb) in zip(bot, bot[1:]):
        if na <= n <= nb:
            return lerp(za, zb, (n - na) / (nb - na))
    return bot[-1][1]


def _boot_cu(c, t):
    ft = FILM_T0 + t
    sx, sy = L.shake(t, T_HOOK, amp=18.0, dur=0.32)
    c.save()
    c.translate(sx, sy)
    cam = CAM_F2
    d = D_TRUNK
    sc = cam.scale(d)
    W.draw_river(c, cam, ft, holes=HOLES, moon_at=None, trunk=False, stars_on=True)
    _trunk_sec(c, cam)
    # the bark's grain, the moon along its top
    ns = [W.STUB_N - 0.9 + 0.06 * i for i in range(31)]
    for k, f in enumerate((0.3, 0.55, 0.78)):
        pts = [cam.px(n, lerp(W.trunk_top_z(n), _bottom_z(n), f) + 0.01 * K._sn(k, i, 64), d) for i, n in enumerate(ns)]
        K.band(c, pts, lerp(K.INK, W.STEEL, 0.2), max(2.0, 0.006 * sc), seed=620 + k, alpha=0.8)
    K.band(c, [cam.px(n, W.trunk_top_z(n) + 0.003, d) for n in ns], L.RIM, max(2.0, 0.005 * sc), seed=630, alpha=0.8)
    # her boot sliding along the bark toes first, scraping the snow off it; it slams into the stub
    s_b = BOOT_LEN * sc / 264.0
    pts = [_boot_rot(p) for p in F._BOOT["mother"]]
    low = max(pts, key=lambda p: p[1])
    front = max((p for p in pts if p[1] > low[1] - 60.0), key=lambda p: p[0])
    hook_x = cam.px(W.STUB_N, 0.0, d)[0] - 0.5 * STUB_W * sc - 0.012 * sc
    feet_n = _m_n(t) - M_FEET
    jolt = _bump(t, T_HOOK, T_HOOK + 0.16)
    quiver = 2.5 * math.sin(ft * 70.0) if t > T_HOOK + 0.22 else 0.0
    toe_x = hook_x + (feet_n - (M_HOOK - M_FEET)) * sc - 10.0 * jolt + quiver
    toe_n = cam.u0 + (toe_x - 540.0) / sc
    top_y = cam.px(toe_n, W.trunk_top_z(toe_n), d)[1]
    at = (toe_x - front[0] * s_b, top_y - low[1] * s_b)
    # the snow along the bark: ahead of the toe it lies; behind it, a few flecks left
    snow = lerp(W.SNOW, K.NIGHT, 0.2)
    ahead = [n for n in ns if n > toe_n]
    if len(ahead) > 1:
        K.band(c, [cam.px(n, W.trunk_top_z(n) + 0.01, d) for n in [toe_n] + ahead], snow, max(3.0, 0.02 * sc), seed=640,
               taper=(0.6, 1.0))
    for i in range(9):
        n = toe_n - 0.06 - 0.09 * i - 0.04 * hash01(i, 65)
        K.ellipse(c, cam.px(n, W.trunk_top_z(n) + 0.006, d), 0.012 * sc * (0.6 + hash01(i, 66)), 0.006 * sc, snow, alpha=0.8)
    # her leg in the long coat, up to the knee out of frame
    sdir = (math.sin(math.radians(-BOOT_PITCH)), -math.cos(math.radians(-BOOT_PITCH)))
    hem = _boot_rot((-4.0, -640.0))
    h0 = (at[0] + hem[0] * s_b - sdir[0] * 40.0, at[1] + hem[1] * s_b - sdir[1] * 40.0)
    h1 = (h0[0] + sdir[0] * 1600.0, h0[1] + sdir[1] * 1600.0)
    K.band(c, [(h0[0] + 4.0, h0[1] - 4.0), (h1[0] + 4.0, h1[1] - 4.0)], L.RIM, 216.0 * s_b, seed=650)
    K.band(c, [h0, h1], K.INK, 216.0 * s_b, seed=650)
    F.boot(c, at, s_b, who="mother", pitch=BOOT_PITCH + 5.0 * jolt, rim=L.RIM, light=(0.6, -0.8), rim_w=4.0, hem=True)
    # the snow heaped up before the toe, thrown off at the hook
    heap = clamp((t - T_CU_HOOK) / (T_HOOK - T_CU_HOOK)) * (1.0 if t < T_HOOK else 0.0)
    if heap > 0.0:
        K.ellipse(c, (toe_x + 0.015 * sc, top_y - 0.012 * sc), 0.03 * sc * heap, 0.018 * sc * heap, snow)
    bend = -9.0 * _bump(t, T_HOOK, T_HOOK + 0.22) + 3.0 * _bump(t, T_HOOK + 0.22, T_HOOK + 0.45)
    _trunk_sec(c, cam, near=True, bend=bend, rim=L.RIM)
    # bark chips and snow knocked off it
    L.spray(c, (hook_x, top_y - 0.05 * sc), t, T_HOOK, cam.ppm * 0.45, n=22, seed=31, power=1.0, spread=1.6)
    L.spray(c, (toe_x, top_y), t, T_CU_HOOK, cam.ppm * 0.2, n=8, seed=33, power=0.5, spread=0.8, life=0.4)
    c.restore()


# ============================================================================ C: behind her on the trunk (3.3-5.0)
def _trunk_x(n):
    (x0, n0), (x1, n1) = W.TRUNK
    return lerp(x0, x1, (n - n0) / (n1 - n0))


TRUNK_ANG = math.atan2(W.TRUNK[1][1] - W.TRUNK[0][1], W.TRUNK[1][0] - W.TRUNK[0][0])   # map angle, root to tip
TRUNK_ROT = 90.0 - math.degrees(TRUNK_ANG)       # turns the page so the trunk runs straight up the frame
CAM_C0 = W.Plan(12.9, 7.6, 235.0, rot=TRUNK_ROT)
CAM_C1 = W.Plan(12.95, 8.1, 262.0, rot=TRUNK_ROT)
C_N0 = 5.6                          # where she has got to along the trunk when we cut to her


def _top_crawl(head, ph):
    """Her hands working along the trunk in a belly crawl, from above (map points)."""
    out = []
    for side, off in ((-1.0, 0.0), (1.0, 0.5)):
        q = (ph + off) % 1.0
        rel = lerp(0.42, -0.05, q / 0.65) if q < 0.65 else lerp(-0.05, 0.42, ease("inout", (q - 0.65) / 0.35))
        n = head[1] + rel * math.sin(TRUNK_ANG)
        out.append((_trunk_x(n) + 0.19 * side, n))
    return tuple(out)


def _top_scarf(c, cam, head, ang):
    """The red scarf loosely round her neck, from above, an end trailing over her shoulder."""
    ux, un = math.cos(ang), math.sin(ang)
    P = lambda a, b: (head[0] + ux * a - un * b, head[1] + un * a + ux * b)
    K.poly(c, cam.pts([P(-0.17 + 0.07 * math.cos(6.283 * i / 16), 0.17 * math.sin(6.283 * i / 16)) for i in range(16)]),
           K.RED)
    K.band(c, cam.pts([P(-0.2, 0.12), P(-0.36, 0.21), P(-0.52, 0.18)]), K.RED, 0.06 * cam.ppm, seed=87, taper=(1.0, 0.8))


def _behind(c, t):
    """C, from above: the page turned so the trunk runs up the frame to the hole; she crawls up
    it toward him, the false trail beside her going into the hole."""
    ft = FILM_T0 + t
    u = (t - T_OUT) / (T_TIP - T_OUT)
    cam = L.plan_at(t, [(T_OUT, CAM_C0), (T_TIP, CAM_C1, "inout")])
    W.draw_page(c, cam, ft, prints=PRINTS, holes=HOLES, woods_on=False)
    n_p = lerp(C_N0, M_N1, u)
    head_n = n_p + 0.75
    head = (_trunk_x(head_n), head_n)
    ph = (n_p - C_N0) / CRAWL_STEP
    _top_body(c, cam, head, TRUNK_ANG, "mother", _top_crawl(head, ph), legs_k=ph)
    _top_scarf(c, cam, head, TRUNK_ANG)
    L.hole_guard(c, cam, t)
    L.hat_top(c, cam, t)


# ============================================================================ B: onto the trunk (1.8-3.3)
CAM_B = W.Dio(-1.25, -0.05, 280.0, eye=0.95)
B_STAND_N = -1.95


def _girl_sec(c, cam, t, n=GIRL_N, d=1.35, look=0.0, crouch=0.0, facing=1, hug=None):
    """The girl crouched against the root plate's south side, peeking out after her mother."""
    st = C.standing("girl", 0.0, 16.0)
    s = C.scale("girl", cam.scale(d))
    at = cam.px(n, W.land_z(n), d)
    arms = {"near": ("ang", 25.0, 70.0), "far": ("ang", 15.0, 60.0)}
    if hug is not None:
        arms["near"] = ("ang", 60.0, 40.0)
    pose = C.still_pose("girl", lean=10.0 + 8.0 * look, head=6.0 * look, arms=arms, crouch=lerp(70.0, 95.0, crouch), t=t)
    # her scarf is her mother's rope now: what is left round her neck is her dark collar
    return L.figure_at(c, "girl", st, pose, at, s, facing, 0.0, rim=L.RIM, red=K.INK)


def _m_root(t):
    """Her at the trunk's root (B): returns pel, roll, hands, legs, head, stand-state-or-None."""
    tops = W.trunk_top_z
    if t < T_STEP_UP[0]:
        st = L.stance("mother", 0.2)
        return (B_STAND_N, 0.0), 0.0, ((B_STAND_N + 0.3, 0.9), (B_STAND_N + 0.2, 0.85)), None, 6.0, st
    if t < T_DOWN[0]:
        # the step up: her near boot onto the trunk, then up onto it, crouched
        u = ease("inout", (t - T_STEP_UP[0]) / (T_STEP_UP[1] - T_STEP_UP[0]))
        n = lerp(B_STAND_N, -1.62, u)
        z = lerp(0.0, tops(-1.62), u)
        pel = (n, z + lerp(0.74, 0.6, u))
        near_f = (lerp(B_STAND_N + 0.15, -1.5, clamp(u * 1.6)), tops(-1.5) if u > 0.5 else lerp(0.0, tops(-1.5) + 0.15, u * 2.0))
        far_f = (lerp(B_STAND_N - 0.1, -1.72, u), lerp(0.0, tops(-1.72), clamp(u * 1.4 - 0.4)))
        roll = 8.0 * math.sin(math.pi * u)
        legs = (_bm(near_f, pel, roll), _bm(far_f, pel, roll))
        hands = ((pel[0] + 0.35, pel[1] + 0.2 + 0.1 * u), (pel[0] + 0.15, pel[1] + 0.1))
        return pel, roll, hands, legs, 0.0, None
    if t < T_DOWN[1]:
        # down: to her knees, her hands onto the bark ahead, and flat
        u = ease("inout", (t - T_DOWN[0]) / (T_DOWN[1] - T_DOWN[0]))
        (pn, pz), roll1 = _flat(-1.3)
        pel = (lerp(-1.62, pn, u), lerp(tops(-1.62) + 0.6, pz, u))
        roll = lerp(8.0, roll1, ease("in", u))
        knee_f = (lerp(-1.6, -1.3 - M_FEET * 0.9, u), lerp(tops(-1.6) + 0.02, tops(-2.0) + 0.1, u))
        legs = (_bm(knee_f, pel, roll), _bm((knee_f[0] - 0.05, knee_f[1]), pel, roll))
        if u < 0.5:
            legs = tuple((lerp(a[0], 0.25, 1.0 - 2.0 * u), lerp(a[1], 0.45, 1.0 - 2.0 * u)) for a in legs)
        hands = ((lerp(pel[0] + 0.45, -1.3 + 0.95, u), lerp(pel[1] + 0.1, tops(-0.35) + 0.03, u)),
                 (lerp(pel[0] + 0.35, -1.3 + 0.7, u), lerp(pel[1], tops(-0.6) + 0.03, u)))
        return pel, roll, hands, legs, lerp(0.0, 60.0, u), None
    # the crawl, down the bank and out
    n_p = -1.3 + 0.95 * (t - T_DOWN[1]) / 0.8
    ph = (n_p + 1.3) / CRAWL_STEP
    pel, roll = _flat(n_p)
    return pel, roll, _crawl_hands(n_p, ph), _legs_flat(kick=ph), 64.0, None


def _root(c, t):
    ft = FILM_T0 + t
    cam = CAM_B
    W.draw_river(c, cam, ft, holes=HOLES, moon_at=MOON_SEC, trunk=False)
    look = ease("inout", clamp((t - 2.3) / 0.4))
    _girl_sec(c, cam, t, look=look)
    _trunk_sec(c, cam)
    pel, roll, hands, legs, head, stand = _m_root(t)
    d = D_TRUNK - 0.1
    j = _draw_mother(c, cam, pel, roll, hands, legs, head=head, d=d, neck=True, stand=stand)
    _trunk_sec(c, cam, near=True, rim=L.RIM)
    K.breath(c, j["mouth"], t, rate=0.7, facing=1, s=1.1, phase=0.2, strength=0.7, seed=3)


# ============================================================================ G: the page: out along the red line (10.9-14.0)
CAM_G0 = W.Plan(12.98, 9.5, 330.0)
CAM_G1 = W.Plan(12.86, 9.2, 350.0)
M_TOP_HEAD = (12.64, M_HOOK + 0.8)                  # her head, lying on the trunk, hooked
DRAG_PATH = ((13.24, 10.02), (13.12, 9.72), (12.96, 9.42), (12.88, 9.22))


def _top_body(c, cam, head, ang, who, hands, rim=L.RIM, legs_k=0.0, color=K.INK, rim_w=3.0):
    """A body lying flat, from above: head at `head` (map), the body trailing behind it along
    map angle `ang` (radians, the direction from the feet to the head); hands: two map points."""
    big = {"mother": 1.0, "guard": 1.15}[who]
    ux, un = math.cos(ang), math.sin(ang)
    vx, vn = -un, ux
    P = lambda a, b: (head[0] + ux * a + vx * b, head[1] + un * a + vn * b)
    polys = []
    def ell(a, b, ra, rb, n=18):
        return [P(a + ra * math.cos(6.283 * i / n), b + rb * math.sin(6.283 * i / n)) for i in range(n)]
    polys.append(ell(-0.5, 0.0, 0.32, 0.22 * big))                # torso and coat
    polys.append(ell(-0.85, 0.0, 0.2, 0.17 * big))                # hips
    for side in (-1, 1):
        k = 0.06 * math.sin(6.283 * legs_k + (0.0 if side > 0 else math.pi))
        polys.append(bass.capsule_pts(P(-0.95, 0.08 * big * side), P(-1.62 + k, 0.11 * big * side), 0.065 * big, 0.055 * big,
                                      cap=4))
    sh = [P(-0.22, 0.2 * big * side) for side in (-1, 1)]
    for s_, h in zip(sh, hands):
        mid = ((s_[0] + h[0]) / 2 + vx * 0.08 * (1 if s_ is sh[1] else -1), (s_[1] + h[1]) / 2 + vn * 0.08 * (1 if s_ is sh[1] else -1))
        polys.append(bass.capsule_pts(s_, mid, 0.06 * big, 0.055 * big, cap=4))
        polys.append(bass.capsule_pts(mid, h, 0.055 * big, 0.05 * big, cap=4))
        polys.append([(h[0] + 0.06 * math.cos(6.283 * i / 10), h[1] + 0.05 * math.sin(6.283 * i / 10)) for i in range(10)])
    hr = 0.12 * big
    polys.append(ell(0.0, 0.0, hr, hr * 0.9))
    fp = [cam.pts(q) for q in polys]
    if rim is not None:
        K.polys(c, [[(x, y - rim_w) for x, y in q] for q in fp], rim)
    K.polys(c, fp, color)


def _hole_clip(c, cam, fn):
    """Draw fn() clipped to the big hole (what of him is in the water)."""
    c.save()
    pts = cam.pts(W.hole_poly(W.HOLE_BIG, W.HOLE_R[1], 62))
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    c.close_path()
    c.clip()
    fn()
    c.restore()


def _g_top(t):
    """His head (map) and body angle on the page (G)."""
    if t < T_UP[0]:
        return (13.3, 10.32 + 0.02 * math.sin(t * 3.0)), math.radians(-100.0)
    if t < T_BREAK:
        u = ease("out", clamp((t - T_UP[0]) / (T_UP[1] - T_UP[0])))
        return (lerp(13.3, 13.25, u), lerp(10.32, 9.98, u)), math.radians(-100.0)
    if t < T_SLIDE[0]:
        drop = _bump(t, T_BREAK, T_PUSH + 0.1)
        return (13.25 + 0.02 * drop, 9.98 + 0.2 * drop), math.radians(-100.0)
    u = ease("inout", clamp((t - T_SLIDE[0]) / (T_SLIDE[1] - T_SLIDE[0])))
    s_ = _arc(DRAG_PATH)
    p = _at_arc(DRAG_PATH, s_, s_[-1] * u)
    q = _at_arc(DRAG_PATH, s_, s_[-1] * u + 0.05)
    a = math.atan2(q[1] - p[1], q[0] - p[0]) if u < 0.99 else math.atan2(DRAG_PATH[-1][1] - DRAG_PATH[-2][1],
                                                                            DRAG_PATH[-1][0] - DRAG_PATH[-2][0])
    return p, a


def _page(c, t):
    ft = FILM_T0 + t
    cam = L.plan_at(t, [(T_PAGE, CAM_G0), (T_SLIDE[0], CAM_G0), (T_SLIDE[1], CAM_G1)])
    W.draw_page(c, cam, ft, prints=PRINTS, holes=HOLES, reeds_on=False, woods_on=False)
    head, ang = _g_top(t)
    # the wet track he leaves on the snow
    slide = ease("inout", clamp((t - T_SLIDE[0]) / (T_SLIDE[1] - T_SLIDE[0])))
    if slide > 0.0:
        hip = (head[0] - math.cos(ang) * 0.85, head[1] - math.sin(ang) * 0.85)
        K.band(c, cam.pts([(13.26, 10.1), hip]), lerp(W.THIN, K.WATER, 0.25), 0.42 * cam.ppm, seed=91, alpha=0.75)
    # the edge breaking under his chest: cracks run back into the ice, a slab tips into the water
    if t >= T_BREAK:
        u = clamp((t - T_BREAK) / 0.7)
        g = ease("out3", clamp((t - T_BREAK) / 0.1))
        for i in range(7):
            side = -1.0 if i < 4 else 1.0                 # out along the edge both ways from under his chest
            a = math.radians((180.0 if side < 0 else 0.0) + side * (-12.0 - 16.0 * (i % 4)) + 8.0 * K._sn(i, 61))
            ln = (0.32 + 0.38 * hash01(i, 62)) * g
            pts = [(13.26 + side * 0.18, 10.05)]
            for k in range(1, 5):
                r = ln * k / 4.0
                pts.append((pts[0][0] + r * math.cos(a) + 0.025 * K._sn(i, k, 63), pts[0][1] + r * math.sin(a)))
            K.band(c, cam.pts(pts), lerp(K.INK, W.THIN, 0.25), max(1.5, 0.014 * cam.ppm), seed=600 + i, taper=(1.0, 0.2))
        chunk = [(13.0, 10.07), (13.48, 10.03), (13.52, 10.3), (13.04, 10.32)]
        cx, cn = 13.26, 10.18
        k = 1.0 - 0.55 * ease("out", u)
        K.poly(c, cam.pts([(cx + (x - cx) * k, cn + (n - cn) * k + 0.1 * u) for x, n in chunk]), lerp(W.THIN, K.WATER, u),
               alpha=1.0 - 0.6 * u)
        L.spray(c, cam.px((13.26, 10.12)), t, T_BREAK, cam.ppm, n=30, seed=41, power=1.4, spread=1.5)
    # the red line: from her hands to his fist; she hauls hand over hand
    m_head = M_TOP_HEAD
    m_ang = math.radians(84.6)
    fist = (head[0] + math.cos(ang) * 0.5, head[1] + math.sin(ang) * 0.5)
    haul = (t - T_PAGE) * 2.2
    q = haul % 1.0
    lead = (lerp(m_head[0], fist[0], 0.55), lerp(m_head[1] + 0.35, fist[1], 0.55))
    back = (m_head[0] + 0.05, m_head[1] + 0.12)
    if slide >= 1.0:
        lead = back = fist
    ha = (lerp(lead[0], back[0], ease("inout", min(q / 0.6, 1.0))), lerp(lead[1], back[1], ease("inout", min(q / 0.6, 1.0))))
    hb = (lerp(back[0], lead[0], ease("inout", min(q / 0.6, 1.0))), lerp(back[1], lead[1], ease("inout", min(q / 0.6, 1.0))))
    scarf_strip(c, cam.pts([fist, (lerp(fist[0], back[0], 0.5), lerp(fist[1], back[1], 0.5)), back]), ft, 0.1 * cam.ppm,
                fringe=False, seed=6)
    # the slack she has hauled in, piling by her shoulder
    pile = clamp((t - T_PAGE) / (T_SLIDE[1] - T_PAGE))
    for k in range(1 + int(3 * pile)):
        p = (12.43 + 0.06 * k, m_head[1] - 0.3 - 0.08 * k)
        K.ellipse(c, cam.px(p), 0.12 * cam.ppm * (0.6 + 0.4 * pile), 0.05 * cam.ppm, K.RED, angle=20.0 + 30.0 * k)
    _top_body(c, cam, m_head, m_ang, "mother", (ha, hb))
    # him: what is in the water is under the water's skin
    g_hands = (fist, (fist[0] + 0.04, fist[1] + 0.05))
    _top_body(c, cam, head, ang, "guard", g_hands, rim=L.RIM_WET, legs_k=(t - T_PUSH) * 1.5 if t > T_PUSH else 0.0)

    def water():
        # what of him is in the hole is under the water's skin; the rings spread on it
        K.fill(c, K.WATER, alpha=0.55)
        if t >= T_BREAK:
            L.rings(c, cam.px((13.26, 10.4)), t, T_BREAK, 0.6 * cam.ppm, 0.6 * cam.ppm, n=3, every=0.3, life=1.2, width=3.0,
                    seed=7, alpha=0.6)
        if t >= T_PUSH:
            L.rings(c, cam.px((13.38, 11.0)), t, T_PUSH, 0.5 * cam.ppm, 0.5 * cam.ppm, n=4, every=0.25, life=1.0, width=3.0,
                    seed=9, alpha=0.5)
    _hole_clip(c, cam, water)
    L.hat_top(c, cam, t)


# ============================================================================ H: onto the trunk, and back (14.0-15.4)
CAM_H0 = W.Dio(9.05, -0.75, 290.0, eye=-0.1)
CAM_H1 = W.Dio(8.45, -0.75, 290.0, eye=-0.1)
H_M = [(T_DRAG, M_HOOK), (T_ONTO[0], M_HOOK), (T_ONTO[1], M_HOOK - 0.8), (T_BACK[0], M_HOOK - 0.8),
       (T_BACK[1], M_HOOK - 1.35)]                           # her pelvis: backing up the trunk, him in tow
H_G = [(T_DRAG, 9.22), (T_ONTO[0], 9.22), (T_ONTO[1], 8.62), (T_BACK[0], 8.62), (T_BACK[1], 8.07)]   # his head


def _g_surf(n):
    """What his body rests on at n in the section: the trunk, the snow on the ice, the water."""
    if n <= TIP_N:
        return W.trunk_top_z(n)
    if n < EDGE_S:
        return W.ICE_Z + W.SNOW_T
    return W.ICE_Z - 0.2


def _g_prone(head_n, surf=_g_surf, lift=0.0):
    """Him on his belly, head to the left at head_n, the body laid along `surf`: pelvis, roll and
    feet (body m); while his hips are over the hole his legs hang down into the water."""
    pn = head_n + 0.92
    hz = surf(head_n) + 0.12
    pz = surf(pn) + 0.16 + lift
    roll = -90.0 + math.degrees(math.atan2(hz - pz, 0.92))
    k = clamp((pn - EDGE_S + 0.1) / 0.35) if surf is _g_surf else 0.0
    feet = []
    for dn, dz in ((0.0, 0.0), (0.07, 0.04)):
        fn = pn + lerp(0.88, 0.42, k) + dn
        fz = lerp(surf(min(fn, EDGE_S - 0.01) if surf is _g_surf else fn) + 0.07, pz - 0.72, k) + dz
        feet.append(_bm((fn, fz), (pn, pz), roll))
    return (pn, pz), roll, tuple(feet)


def _drag(c, t):
    ft = FILM_T0 + t
    cam = L.dio_at(t, [(T_DRAG, CAM_H0), (T_BACK[0], CAM_H0), (T_BACK[1], CAM_H1)])
    W.draw_river(c, cam, ft, holes=HOLES, moon_at=MOON_SEC, trunk=False)
    _trunk_sec(c, cam)
    onto = ease("inout", clamp((t - T_ONTO[0]) / (T_ONTO[1] - T_ONTO[0])))
    n_p = L.track(t, H_M)
    pel, roll = _flat(n_p)
    # him: up over the trunk's tip after her, his legs coming out of the water; then along it
    head_n = L.track(t, H_G)
    gpel, groll, gfeet = _g_prone(head_n, lift=0.05 * _bump(t, T_ONTO[0], T_ONTO[1]))
    d_g = lerp(0.1, D_TRUNK - 0.15, onto)
    # her hands: both on his collar, hauling; then one on the collar, the other pushing on the bark
    collar = (head_n + 0.2, _g_surf(head_n) + 0.24)
    ph = (M_HOOK - n_p) / CRAWL_STEP
    if t < T_BACK[0]:
        hands = (collar, (head_n + 0.34, _g_surf(head_n + 0.34) + 0.2))
    else:
        hands = (collar, _crawl_hands(n_p, -ph, reach=0.7)[1])
    j = _draw_mother(c, cam, pel, roll, hands, _legs_flat(kick=-ph if t > T_ONTO[0] else None), head=70.0)
    _trunk_sec(c, cam, near=True, rim=L.RIM)
    g_hands = ((head_n - 0.35, _g_surf(head_n - 0.35) + 0.05), (head_n - 0.2, _g_surf(head_n - 0.2) + 0.04))
    gj = _draw_guard(c, cam, t, gpel, groll, g_hands, head=14.0, d=d_g, facing=-1, legs=gfeet)
    L.wash(c, cam, EDGE_S, EDGE_N, alpha=0.62)
    L.waterline(c, cam, EDGE_S, EDGE_N, ft, seed=5, amp=2.5)
    # the scarf between them, slack now: from her far wrist down onto the bark and up to his fist
    far = j.get("hand_far", cam.px(hands[1][0], hands[1][1], D_TRUNK))
    fist = gj.get("hand_near", cam.px(g_hands[0][0], g_hands[0][1], d_g))
    low = cam.px(0.5 * (hands[1][0] + g_hands[0][0]), _g_surf(0.5 * (hands[1][0] + g_hands[0][0])) + 0.02, D_TRUNK)
    scarf_strip(c, [far, (0.5 * (far[0] + low[0]), low[1]), (0.5 * (fist[0] + low[0]), low[1]), fist], ft,
                max(10.0, 0.06 * _px_per_m(j)), fringe=False, seed=8)
    K.breath(c, gj["mouth"], t, pant=2.6, facing=-1, s=1.4, phase=0.0, strength=1.0, seed=12)
    K.breath(c, j["mouth"], t, rate=0.6, facing=1, s=1.2, phase=0.2, strength=0.8, seed=13)


# ============================================================================ I: the bank (15.4-18.0)
CAM_I = W.Dio(-1.45, -0.2, 270.0, eye=0.9)


def _bank(c, t):
    ft = FILM_T0 + t
    cam = CAM_I
    W.draw_river(c, cam, ft, holes=HOLES, moon_at=MOON_SEC, trunk=False)
    off = ease("inout", clamp((t - T_OFF[0]) / (T_OFF[1] - T_OFF[0])))
    roll_u = clamp((t - T_ROLL[0]) / (T_ROLL[1] - T_ROLL[0]))
    to_girl = ease("inout", clamp((t - T_TO_GIRL[0]) / (T_TO_GIRL[1] - T_TO_GIRL[0])))
    # the girl, against the roots; she shrinks into her mother when she comes
    _girl_sec(c, cam, t, look=0.4 + 0.6 * (1.0 - to_girl), crouch=to_girl, hug=to_girl if to_girl > 0.3 else None)
    _trunk_sec(c, cam)
    # him: off the trunk's root end onto the snow of the bank, then over onto his back
    z_snow = lambda n: W.land_z(n) + 0.02
    d_g = 0.55
    head_n = lerp(-0.55, -1.45, off)
    if roll_u <= 0.0:
        z_of = (lambda n: max(W.trunk_top_z(n), z_snow(n))) if off < 0.5 else z_snow
        gpel, groll, gfeet = _g_prone(head_n, surf=z_of)
        gj = _draw_guard(c, cam, t, gpel, groll, ((head_n - 0.4, z_of(head_n - 0.4) + 0.03),
                                                  (head_n - 0.25, z_of(head_n - 0.25) + 0.03)),
                         head=14.0, d=d_g, facing=-1, legs=gfeet)
    else:
        # over onto his back: head up the bank, chest heaving
        k = ease("inout", roll_u)
        pn = head_n + 0.92
        z1, z2 = z_snow(head_n), z_snow(pn)
        slope = math.degrees(math.atan2(z1 - z2, 0.92))
        heave = 0.035 * math.sin(ft * 9.0)
        gpel = (pn, z2 + 0.17 + 0.1 * math.sin(math.pi * k) + heave)
        groll = -90.0 + slope
        flip = k >= 0.5
        squash = abs(1.0 - 2.0 * k)
        hands = ((pn - 0.35, z_snow(pn - 0.35) + 0.3 * (1 - squash) + 0.05), (pn + 0.1, z_snow(pn + 0.1) + 0.06))
        if flip:
            hands = ((pn - 0.1, z_snow(pn - 0.1) + 0.12), (pn + 0.25, z_snow(pn + 0.25) + 0.08))
        c.save()
        pv = cam.px(gpel[0], gpel[1], d_g)
        c.translate(pv[0], pv[1])
        c.scale(1.0, 0.55 + 0.45 * squash)
        c.translate(-pv[0], -pv[1])
        gj = _draw_guard(c, cam, t, gpel, groll if not flip else groll, hands, head=10.0 if flip else -30.0, d=d_g,
                         facing=1 if flip else -1, legs=((0.12, 0.88), (-0.04, 0.9)))
        c.restore()
    # her: backing off the trunk, standing, then over to the girl, crouching in front of her
    if t < T_OFF[1]:
        n = lerp(-1.25, -1.9, off)
        st = L.stance("mother", 0.25 * (1.0 - off), sink=0.25 * (1.0 - off))
        zg = lerp(W.trunk_top_z(-1.25), 0.0, off)
        hands = ((n + 0.4, zg + 0.75), (n + 0.15, zg + 0.6))
        j = _draw_mother(c, cam, (n, zg), 0.0, hands, None, head=-10.0, d=D_TRUNK - 0.25, stand=st, lean=18.0 * (1.0 - off))
    else:
        n = lerp(-1.9, GIRL_N + 0.42, to_girl)
        st = L.stance("mother", 0.15, sink=0.32 * to_girl)
        hands = ((n + 0.3, 0.55 - 0.1 * to_girl), (lerp(n - 0.1, GIRL_N + 0.1, to_girl), lerp(0.6, 0.62, to_girl)))
        j = _draw_mother(c, cam, (n, 0.0), 0.0, hands, None, head=4.0, d=D_TRUNK - 0.25, stand=st,
                         lean=lerp(6.0, 26.0, to_girl))
        # the scarf hanging from her far hand to the snow
        hp = cam.px(hands[1][0], hands[1][1], D_TRUNK - 0.25)
        m = _px_per_m(j)
        scarf_strip(c, [hp, (hp[0] + 0.02 * m, hp[1] + 0.3 * m), (hp[0] + 0.05 * m * math.sin(ft * 2.0), hp[1] + 0.55 * m)], ft,
                    max(10.0, 0.06 * m), fringe=True, seed=10)
    _trunk_sec(c, cam, near=True, rim=L.RIM)
    # his breath steaming up off the snow; hers
    K.breath(c, gj["mouth"], t, pant=2.8, facing=1 if roll_u >= 0.5 else -1, s=1.5, phase=0.0, strength=1.0, seed=14)
    K.breath(c, j["mouth"], t, rate=0.55, facing=1, s=1.1, phase=0.4, strength=0.7, seed=15)


# ============================================================================ A: stay (0-1.8)
A_M = (330.0, 1210.0)
A_G = (800.0, 1500.0)
A_MS, A_GS = 0.98, 0.86


def reed_blades(c, t, specs, color=K.INK):
    """Close-up reeds: (x_base, y_base, height, lean, width, seed) blades in frame px, swaying."""
    for (x, y, h, lean, w, seed) in specs:
        sway = 14.0 * math.sin(t * (1.1 + 0.4 * hash01(seed, 1)) + seed)
        tip = (x + lean * h + sway, y - h)
        mid = (x + 0.45 * lean * h + 0.4 * sway + 6.0 * K._sn(seed, 2), y - 0.5 * h)
        K.band(c, [(x, y), mid, tip], color, w, seed=seed, taper=(1.0, 0.12))


def _blade_specs(seed, n, x0, x1, y, h0, h1, w0, w1, lean=0.12):
    return [(x0 + (x1 - x0) * hash01(seed, i), y + 40.0 * hash01(seed, i, 2), lerp(h0, h1, hash01(seed, i, 3)),
             lean * K._sn(seed, i, 4), lerp(w0, w1, hash01(seed, i, 5)), seed * 100 + i) for i in range(n)]


REEDS_A = _blade_specs(13, 22, -40.0, 760.0, 1200.0, 240.0, 460.0, 6.0, 11.0)


def bust_base(c, at, s, x0, x1, y0, facing=1):
    """The rest of a close-up's body below its coat's edge (face units x0..x1 at y0), down out of
    frame."""
    X = lambda u: at[0] + facing * (u - 400.0) * s
    yb = at[1] + (y0 - 860.0 if x1 > 560 else y0 - 640.0) * s
    K.poly(c, [(X(x0), yb - 2.0), (X(x1), yb - 2.0), (X(x1 + 40.0), 2000.0), (X(x0 - 40.0), 2000.0)], K.INK)


def _plate_cu(c):
    """The root plate behind the girl: a ragged wall of frozen earth torn up with the tree, roots
    splaying out of its rim against the sky, snow caught in them."""
    col = lerp(K.INK, W.STEEL, 0.36)
    cx, cy, r = 1080.0, 1060.0, 640.0
    pts = []
    for i in range(90):
        a = 6.283 * i / 90
        rr = r * (1.0 + 0.05 * math.sin(a * 7.0 + 1.0) + 0.045 * K._sn(i, 41) + 0.02 * K._sn(i, 48))
        pts.append((cx + rr * math.cos(a) * 0.8, cy + rr * math.sin(a)))
    roots = []
    for j in range(24):
        a = math.radians(150.0 + 175.0 * j / 23.0 + 5.0 * K._sn(j, 42))
        p0 = (cx + 0.78 * r * math.cos(a), cy + 0.97 * r * math.sin(a))
        ln = r * (0.12 + 0.26 * hash01(j, 43))
        b = a + 0.45 * K._sn(j, 44)
        p1 = (p0[0] + ln * math.cos(b), p0[1] + ln * math.sin(b))
        mid = ((p0[0] + p1[0]) / 2 + 20.0 * K._sn(j, 45), (p0[1] + p1[1]) / 2 + 20.0 * K._sn(j, 46))
        w = 9.0 + 14.0 * hash01(j, 47)
        roots.append(([p0, mid, p1], w, j))
        if hash01(j, 49) > 0.5:                     # a rootlet off it
            q = (mid[0] + 0.5 * ln * math.cos(b - 0.7), mid[1] + 0.5 * ln * math.sin(b - 0.7))
            roots.append(([mid, q], w * 0.5, j + 50))
    for q, w, j in roots:
        K.band(c, [(x + 4.0, y - 4.0) for x, y in q], K.PAPER, w, seed=500 + j, taper=(1.0, 0.1), alpha=0.35)
    K.poly(c, [(x + 4.0, y - 4.0) for x, y in pts], K.PAPER, alpha=0.35)
    for q, w, j in roots:
        K.band(c, q, col, w, seed=500 + j, taper=(1.0, 0.1))
    K.poly(c, pts, col)
    # stones and clods in the earth; snow caught along the top
    for k in range(9):
        a = math.radians(170.0 + 160.0 * hash01(k, 70))
        rk = r * (0.35 + 0.5 * hash01(k, 71))
        K.ellipse(c, (cx + rk * math.cos(a) * 0.8, cy + rk * math.sin(a)), 30.0 + 30.0 * hash01(k, 72),
                  20.0 + 18.0 * hash01(k, 73), lerp(col, K.INK, 0.45), angle=60.0 * K._sn(k, 74))
    for k in range(7):
        a = math.radians(215.0 + 15.0 * k + 6.0 * K._sn(k, 75))
        p = (cx + 0.79 * r * math.cos(a), cy + 0.98 * r * math.sin(a))
        K.ellipse(c, p, 26.0 + 16.0 * hash01(k, 76), 9.0, lerp(W.SNOW, K.NIGHT, 0.3), angle=math.degrees(a) + 90.0)


def _m_red_cu(c, at, s, t=0.0, facing=1):
    """The girl's red scarf wound loosely round the mother's neck over her coat's collar, one end
    hanging down her front (her close-up, in F.mother's face units)."""
    c.save()
    c.translate(*at)
    c.scale(s * facing, s)
    c.translate(-400.0, -860.0)
    K.poly(c, [(206, 662), (300, 680), (404, 668), (456, 694), (444, 748), (350, 766), (236, 756), (190, 718)], K.RED)
    sw = 6.0 * math.sin(t * 2.3)
    K.poly(c, [(392, 716), (446, 712), (472 + sw, 910), (426 + sw, 918)], K.RED)
    for y in (868.0, 890.0):
        K.band(c, [(420 + sw, y + 6.0), (472 + sw, y)], STRIPE, 7.0, seed=int(y))
    c.restore()


def _stay(c, t):
    ft = FILM_T0 + t
    K.fill(c, K.NIGHT)
    K.stars(c, ft, y1=760.0)
    horizon = 900.0
    for i in range(18):
        x = -40.0 + 66.0 * i + 25.0 * K._sn(i, 71)
        h = 150.0 + 110.0 * hash01(i, 72)
        W.spruce_side(c, (x, horizon + 6.0), h, h * 0.42, lerp(W.STEEL, K.NIGHT, 0.35), seed=i + 40)
    K.poly(c, [(-60.0, horizon), (1140.0, horizon - 4.0), (1140.0, 2000.0), (-60.0, 2000.0)], lerp(W.SNOW, K.NIGHT, 0.45))
    reed_blades(c, t, REEDS_A, color=lerp(K.INK, W.STEEL, 0.32))
    _plate_cu(c)
    palm = ease("out3", clamp((t - T_PALM[0]) / (T_PALM[1] - T_PALM[0])))
    lower = ease("inout", clamp((t - 1.05) / 0.25))
    leave = ease("in", clamp((t - T_LEAVE[0]) / (T_LEAVE[1] - T_LEAVE[0])))
    rise = 1500.0 * leave
    # the girl, her back to the roots, looking at the mitten, then up after her mother
    look_up = ease("inout", clamp((t - T_LEAVE[0] - 0.05) / 0.3))
    bust_base(c, A_G, A_GS, -40.0, 620.0, 900.0, facing=-1)
    g = F.girl(c, A_G, A_GS, look=lerp(0.55, 0.85, look_up), down=lerp(0.15 + 0.3 * palm * (1.0 - lower), -0.75, look_up),
               fear=0.3, t=ft, facing=-1, rim=K.PAPER, light=LIGHT_CU, rim_w=5.0, scarf=0.0)
    K.breath(c, g["mouth"], t, rate=0.9, facing=-1, s=1.2, phase=0.2, strength=0.7, seed=4)
    # the mother, down on her knees to her; then up and gone
    m_at = (A_M[0], A_M[1] - rise)
    bust_base(c, m_at, A_MS, -60.0, 600.0, 1040.0)
    m = F.mother(c, m_at, A_MS, look=0.85, down=0.35 - 0.4 * leave, fear=0.35, t=ft, rim=K.PAPER, light=LIGHT_CU, rim_w=5.0)
    _m_red_cu(c, m_at, A_MS, ft)
    # her flat mitten up between them, against the snow: stay
    k = palm * (1.0 - lower)
    if k > 0.0:
        tip = (lerp(470.0, 590.0, k), lerp(1500.0, 965.0, k) - rise)
        F.mitten(c, (300.0, 1560.0 - rise), tip, 0.92, rim=K.PAPER, light=LIGHT_CU, thumb=1.0, curl=0.0, sleeve_w=0.9)
    K.breath(c, m["mouth"], t - 0.0, rate=1.1, facing=1, s=1.3, phase=0.5, strength=0.8, seed=5)


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        if t < T_ROOT:
            _stay(c, t)
        elif t < T_OUT:
            _root(c, t)
        elif t < T_TIP:
            _behind(c, t)
        elif t < T_CU_GRAB:
            _tip(c, t)
        elif t < T_PULL:
            _glove_cu(c, t)
        elif t < T_CU_HOOK:
            _tip(c, t)
        elif t < T_PAGE:
            _boot_cu(c, t)
        elif t < T_DRAG:
            _page(c, t)
        elif t < T_BANK:
            _drag(c, t)
        else:
            _bank(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    return [
        Cue(0.0, "wind_low", gain_db=-22, dur=18.0, dc="the wind over the river, low, all through"),
        Cue(0.0, "string_low", gain_db=-20, dur=T_HOOK,
            dc="a low string pedal (A2), tense, swelling slowly toward the hook; cut dead at the hook"),
        Cue(0.1, "her_breath", gain_db=-14, dc="her quick breath, close (a recorded breath)"),
        Cue(T_PALM[0], "cloth_rustle", gain_db=-18, dc="her sleeve: the flat mitten comes up"),
        Cue(0.9, "girl_breath", gain_db=-18, pan=0.3, dc="the girl's small frightened breath"),
        Cue(T_LEAVE[0], "cloth_rustle", gain_db=-16, dc="she gets up fast"),
        Cue(T_STEP_UP[0] + 0.1, "snow_step_mother", gain_db=-12, dc="her boot in the snow at the root"),
        Cue(T_STEP_UP[1] - 0.05, "wood_creak", gain_db=-10, dc="the trunk takes her weight: a long creak"),
        Cue(T_DOWN[1] - 0.1, "cloth_scrape", gain_db=-14, dc="her coat on the bark as she drops flat"),
        Cue(T_DOWN[1] + 0.2, "crawl_scrape", gain_db=-14, dur=1.0, dc="elbows and knees working along bark, quick"),
        Cue(T_OUT, "crawl_scrape", gain_db=-14, dur=1.7, dc="elbows working along the trunk, quick, a little further away"),
        Cue(T_OUT + 0.4, "panting_man", gain_db=-14, dur=1.6, pan=0.15, dc="his ragged panting ahead in the hole"),
        Cue(T_OUT + 0.8, "ice_groan", gain_db=-12, dc="the ice groans under the trunk: a deep, slow moan"),
        Cue(T_UNWRAP[0], "cloth_pull", gain_db=-16, dur=T_UNWRAP[1] - T_UNWRAP[0], dc="the scarf pulled off her neck"),
        Cue(T_WIND[0], "wool_wind", gain_db=-16, dur=T_WIND[1] - T_WIND[0], dc="wool wound tight round a wrist"),
        Cue(T_REL1 - 0.1, "cloth_whoosh", gain_db=-10, dc="the scarf thrown: a soft whoosh of wool"),
        Cue(T_LAND1, "cloth_slap", gain_db=-12, pan=0.2, dc="the scarf slaps down on the snow, short of him"),
        Cue(T_LUNGE[0], "grunt", gain_db=-10, pan=0.3, dc="his grunt as he lunges for it (a recorded grunt)"),
        Cue(T_CRUMBLE, "ice_crack_small", gain_db=-8, pan=0.3, dc="the edge snaps off under his glove"),
        Cue(T_CRUMBLE + 0.05, "splash_small", gain_db=-10, pan=0.3, dc="the piece and his arm into the water"),
        Cue(T_CRUMBLE + 0.1, "gasp_man", gain_db=-12, pan=0.3, dc="his gasp as he goes down and grabs on (a recorded gasp)"),
        Cue(T_DRAW[0], "cloth_slide", gain_db=-16, dur=0.38, dc="the scarf drawn back across the snow, hand over hand"),
        Cue(T_EDGE[0], "wood_creak", gain_db=-12, dc="the trunk creaks as she edges out"),
        Cue(T_REL2 - 0.1, "cloth_whoosh", gain_db=-8, dc="the second throw, harder"),
        Cue(T_LAND2, "cloth_slap", gain_db=-10, pan=0.25, dc="it lands across his arm"),
        Cue(T_CLOSE[0], "glove_grab", gain_db=-8, dc="the wet glove closes on the wool: a squeeze"),
        Cue(T_TUG[0], "cloth_stretch", gain_db=-12, dc="the scarf pulled tight"),
        Cue(T_FIST[0], "wool_wind", gain_db=-14, dur=0.26, dc="wool wound round a fist"),
        Cue(T_HEAVE, "grunt", gain_db=-8, pan=0.2, dc="his grunt as he heaves (a recorded grunt)"),
        Cue(T_HEAVE + 0.02, "cloth_stretch", gain_db=-10, dc="the scarf snaps taut"),
        Cue(T_HEAVE + 0.05, "body_slide_wood", gain_db=-10, dur=0.5, dc="her coat sliding fast along the bark"),
        Cue(T_HEAVE + 0.1, "gasp_b", gain_db=-12, dc="her gasp as she slides (a recorded gasp)"),
        Cue(T_HOOK, "wood_knock", gain_db=-4, dc="her boot hits the branch stub: a hard knock"),
        Cue(T_HOOK + 0.02, "wood_creak", gain_db=-8, dc="the stub bends and holds: a short sharp creak"),
        Cue(T_HOOK, "string_hit", gain_db=-10, dc="one short low string stab on the hook, then a silence"),
        Cue(T_PAGE, "cloth_pull", gain_db=-12, dur=2.6, dc="hand over hand on the wool, a steady rhythm, pulls every 0.45 s"),
        Cue(T_PAGE + 0.3, "her_breath", gain_db=-12, dur=2.0, dc="her breath straining with each pull (a recorded breath)"),
        Cue(T_UP[0], "water_heave", gain_db=-10, dc="he heaves his chest up out of the water: a pour of water"),
        Cue(T_BREAK, "ice_crack", gain_db=-6, dc="the edge breaks under his chest: a loud crack"),
        Cue(T_BREAK + 0.05, "splash_big", gain_db=-8, dc="he drops back into the water"),
        Cue(T_PUSH, "grunt", gain_db=-8, dc="his grunt as he pushes on (a recorded grunt)"),
        Cue(T_SLIDE[0], "ice_slide", gain_db=-10, dur=1.4, dc="a wet body sliding on snow and ice, long"),
        Cue(T_SLIDE[0], "string_rise", gain_db=-16, dur=3.2, dc="the strings come back: a slow rise under the slide"),
        Cue(T_COLLAR, "cloth_grab", gain_db=-10, dc="her hand grabs his wet collar"),
        Cue(T_ONTO[0] + 0.2, "wood_creak", gain_db=-10, dc="the trunk takes his weight too"),
        Cue(T_ONTO[0] + 0.3, "his_breath", gain_db=-10, dur=1.2, dc="his heavy breathing, close (a recorded breath)"),
        Cue(T_BACK[0], "crawl_scrape", gain_db=-14, dur=0.55, dc="the two of them working back along the bark"),
        Cue(T_OFF[0] + 0.1, "snow_step_mother", gain_db=-12, dc="her boots onto the snow of the bank"),
        Cue(T_OFF[1] - 0.15, "body_fall", gain_db=-10, dc="he rolls off the trunk into the snow (a recorded body fall)"),
        Cue(T_ROLL[0] + 0.3, "his_breath", gain_db=-8, dur=2.2, dc="his gasping on his back, steam in the cold (a recorded breath)"),
        Cue(T_TO_GIRL[0], "snow_step_mother", gain_db=-12, pan=-0.2, dc="she scrambles back through the snow"),
        Cue(T_TO_GIRL[1], "cloth_rustle", gain_db=-14, pan=-0.3, dc="she gathers the girl to her"),
        Cue(T_TO_GIRL[1] + 0.2, "string_high", gain_db=-20, dur=1.8, dc="one high held string note, uneasy: what now"),
    ]
