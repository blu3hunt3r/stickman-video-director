"""S08 - The Limp (8.375 s).

"His footprints told me more. Short step, long step. He walked with a limp.
 Now it was a quarter of the city."

Shot plan (scene-relative seconds)
  A 0.00-2.75  IN: S07's straight-down camera (Camera(540, 960, 1)) over the same wet pavement
               (slab joints, puddles, rain rings, top-down rain). The last white umbrellas walk
               out of frame and uncover a trail of wet footprints running up the frame; a
               match-light pool (Light.radial) enters from the bottom and follows the prints.
  B 2.75-4.58  push in: a white measuring tape (ticks, no numbers) draws the SHORT gap on
               "Short", the LONG gap on "long"; the short-long rhythm then pulses up the trail.
  C 4.58-5.80  low side insert: the detective's own legs (cropped by darkness, his LEFT hand
               holding the match) walking the same short-long rhythm. No comment.
  D 5.80-8.375 back top-down, pull up through the city into a white-line street map; the amber
               half (from S07) shrinks to the top-left quadrant on "quarter"; push into the
               amber quadrant until amber light floods the frame around a round lit skylight
               centred on screen -> hard cut to S09's amber bulb at the same spot.
"""
import math

from engine import *
from scenes import _lib_s08_s10 as L

# ----------------------------------------------------------------------------- the trail
TRAIL_X = 540.0
FP_S = 1.55
SHORT, LONG = 200.0, 310.0          # the step that lands the LEFT foot is the short one
Y0 = 2160.0
MEASURE = 6                         # prints 6->7 = short gap, 7->8 = long gap
TAPE_X = TRAIL_X + 165.0


def _heel(c, ang, side, s=FP_S):
    lat = -8 if side == "l" else 8
    a = math.radians(ang + 90)
    x, y = lat * 0.1 * s, 22 * s
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def _make_prints():
    out = []
    y = Y0
    for k in range(24):
        side = "r" if k % 2 == 0 else "l"
        lat = 33.0 if side == "r" else -33.0
        x = TRAIL_X + lat + 7 * (hash01(31, k) - 0.5)
        ang = -90 + (4 if side == "r" else -4) + 6 * (hash01(31, k, 1) - 0.5)
        out.append(dict(c=(x, y), side=side, ang=ang, heel=_heel((x, y), ang, side)))
        y -= SHORT if side == "r" else LONG
    return out


PRINTS = _make_prints()
H6, H7, H8 = (PRINTS[MEASURE + k]["heel"] for k in range(3))
Y_MID = 0.5 * (H6[1] + H8[1])
POOL_Y = PRINTS[MEASURE + 1]["c"][1] + 30

# ----------------------------------------------------------------------------- city grid (map)
GX0, GPX = 2040.0, 3000.0           # vertical street centerlines
GY0, GPY = 2600.0, 4000.0           # horizontal street centerlines
STW = 960.0                         # curb to curb
WALK_W = 230.0                      # sidewalk
PLAZA = (-1, -1)                    # the paved block the trail crosses (x -480..1560)
PARK = (3, 0)
MAP_C = (8040.0, 10600.0)           # map framing: the "half"/"quarter" streets cross at centre
MAP_Z = 0.045
X_AMB, Y_AMB = MAP_C                # amber half: x < X_AMB ; quarter: also y < Y_AMB
TARGET_BLOCK = (0, -1)
TARGET = (3540.0, 600.0)            # round lit skylight inside the quadrant (-> S09's bulb)
TARGET_R = 80.0
END_Z = 2.3
TRAIL_PT = (TRAIL_X, 420.0)

# ----------------------------------------------------------------------------- shot times
T_C = 4.583
T_D = 5.80
T_PULL1 = 6.62
T_PUSH0 = 7.0

CAM_AB = Track([(0.0, (540.0, 960.0, 1.0)), (0.45, (540.0, 955.0, 1.0), "inout"),
                (3.30, (556.0, Y_MID - 10, 1.40), "inout3"), (3.95, (556.0, Y_MID - 24, 1.43), "inout"),
                (4.60, (548.0, Y_MID - 330, 1.36), "inout3")])

# the last umbrellas of S07's crowd: (x, y) at t=0, vy px/s, R, rot
EXITERS = [(250.0, 170.0, -300.0, 52.0, 9.0), (842.0, 310.0, -290.0, 56.0, 20.0),
           (705.0, 1690.0, 290.0, 54.0, 3.0), (300.0, 1830.0, 260.0, 50.0, 14.0),
           (958.0, 1260.0, 330.0, 49.0, 30.0)]


def _pool(t):
    k = ease("out3", inv_lerp(0.25, 3.30, t))
    y = lerp(2300.0, POOL_Y, k)
    if t > 3.95:
        y = lerp(POOL_Y, POOL_Y - 330, ease("inout3", inv_lerp(3.95, 4.60, t)))
    x = 552.0 + 22 * fbm1(t * 0.8, 5) + 8 * (1 - k)
    return (x, y)


def _pool_on(t):
    return ease("out", inv_lerp(0.18, 0.5, t))


# ----------------------------------------------------------------------------- shot A/B
def _pavement(f, t, cam, detail=1.0):
    bx = L.view_bounds(cam, 80)
    L.slabs_top(f, t, alpha=detail, box=(bx[0] - 200, bx[1] - 200, bx[2] + 200, bx[3] + 200))
    fx.ripples(f, t, bx[0], bx[1], bx[2], bx[3], rate=0.5 * detail, seed=24, alpha=0.42 * detail,
               squash=0.92)


def _prints(f, alpha=0.9):
    for p in PRINTS:
        if p["c"][1] > -2600:
            props.footprint(f, p["c"], p["ang"], p["side"], s=FP_S, alpha=alpha, w=2.4, wet=1.0)


def _print_sheen(f, t, pool, pool_r, on, pulse_t0, T):
    """Amber sheen on wet prints caught by the match light + the rhythm pulse (clue amber)."""
    ts, tl_ = T.at("short"), T.at("long")
    for k, p in enumerate(PRINTS):
        c = p["c"]
        d = math.hypot(c[0] - pool[0], c[1] - pool[1])
        lf = on * clamp(1 - d / pool_r) ** 1.4
        pk = 0.0
        if MEASURE <= k <= MEASURE + 2:
            tk = ts if k < MEASURE + 2 else tl_
            pk = max(pk, pulse(t, tk, 0.03, 0.55))
        if k >= MEASURE + 2 and pulse_t0 is not None:
            tk = pulse_t0 + (PRINTS[MEASURE + 2]["c"][1] - c[1]) / 1150.0
            pk = max(pk, pulse(t, tk, 0.03, 0.32))
        a = 0.55 * lf + 0.9 * pk
        if a > 0.01:
            props.footprint(f, c, p["ang"], p["side"], s=FP_S * 1.03, alpha=min(1.0, a), w=2.6,
                            color=AMBER, wet=0.0)


def _tapes(f, t, T, alpha=1.0, full=False):
    ts, tl_ = T.at("short"), T.at("long")
    k1 = 1.0 if full else ease("out3", inv_lerp(ts, ts + 0.32, t))
    k2 = 1.0 if full else ease("out3", inv_lerp(tl_, tl_ + 0.42, t))
    if k1 <= 0:
        return
    for h, kk in ((H6, k1), (H7, k1), (H8, k2)):
        if kk > 0:
            draw.line(f, (h[0] + 16, h[1]), (lerp(h[0] + 16, TAPE_X - 8, kk), h[1]), 1.4, WHITE,
                      0.55 * alpha, dash=(5, 6))
    L.tape(f, (TAPE_X, H6[1]), (TAPE_X, H7[1]), k1, alpha=alpha)
    if k2 > 0:
        L.tape(f, (TAPE_X, H7[1]), (TAPE_X, H8[1]), k2, alpha=alpha)


def _match_top(f, t, c, on):
    """The match seen from above: a short stick and a flame dot (the light source)."""
    if on <= 0:
        return
    fl = 0.85 + 0.15 * fbm1(t * 9, 3)
    tip = (c[0] + 10, c[1] + 26)
    draw.line(f, (tip[0] + 16, tip[1] + 44), tip, 2.4, WHITE, 0.8 * on)
    draw.circle(f, tip, 7 * fl, 1, AMBER, on, fill_it=True, glow=1.2)
    draw.circle(f, tip, 3.5, 1, WHITE, 0.9 * on, fill_it=True)
    draw.glow_dot(f, tip, 150 * fl, AMBER, 0.7 * on, core=False)


def _shot_ab(f, t, T):
    x, y, z = CAM_AB(t)
    cam = Camera(x, y, z)
    if t > 0.3:
        cam = cam.shaken(t, amp=2.0 * clamp((t - 0.3) / 0.5), rot_amp=0.08, freq=0.5, seed=8)
    f.set_camera(cam)
    on = _pool_on(t)
    pool = _pool(t)
    pool_r = 400.0
    ambient = lerp(0.62, 0.11, ease("inout", inv_lerp(0.15, 1.3, t)))
    lights = [Light.radial(pool, pool_r, intensity=on, hard=0.25)] if on > 0 else []
    pulse_t0 = 4.02 if t > 3.9 else None

    fx.light_pool(f, pool, 330, 330, AMBER, 0.13 * on, glow=0.35 * on)
    with f.lit(lights, ambient=ambient, soften=3.0):
        _pavement(f, t, cam)
        _prints(f)
    _print_sheen(f, t, pool, pool_r, on, pulse_t0, T)
    _tapes(f, t, T)
    # the last umbrellas of the crowd leave (unlit: continuity with S07's last frame)
    for i, (ux, uy, vy, R, rot) in enumerate(EXITERS):
        yy = uy + vy * t + 0.5 * 260 * t * t * (1 if vy > 0 else -1)
        if -200 < yy < 2300:
            props.umbrella_top(f, (ux + 8 * fbm1(t * 0.5, 40 + i), yy), R, rot + 5 * fbm1(t * 0.4, 50 + i))
    _match_top(f, t, pool, on)
    L.rain_top_vp(f, t, n=120, seed=3, alpha=lerp(0.45, 0.3, clamp(t / 1.5)))


# ----------------------------------------------------------------------------- shot C (insert)
INS_S = 6.6
INS_GROUND = 1462.0
INS_RATE = 1.1634                   # walk cycles per second
INS_STANCE_L = 0.60                 # LEFT stance share: short step quick, long step slow
INS_SHORT, INS_LONG = 600.0, 900.0  # same short-long ratio as the killer's prints (~0.65)
INS_LIMP_HIT = 5.47                 # the heavy RIGHT step lands on "limp"
INS_PHASE0 = 1.0 + INS_STANCE_L - INS_RATE * (INS_LIMP_HIT - T_C)
INS_WALK = L.IKLimp(T_C, 0.0, INS_GROUND, INS_RATE, s=INS_S, short=INS_SHORT, long=INS_LONG,
                    a=INS_STANCE_L, phase0=INS_PHASE0)
INS_SPEED = INS_RATE * (INS_SHORT + INS_LONG)


def _ins_pose(tl):
    p = INS_WALK.pose(T_C + tl, arm=0.8)
    # LEFT hand carries the lit match low, by the thigh (steady, a little sway)
    return p.copy(la=6 + 3 * math.sin(tl * 7.0), le=34 + 3 * math.sin(tl * 5.0 + 1))


INS_HIP0 = _ins_pose(0.0).x


def ins_plants(t_from, t_to):
    """Scene times of the insert's foot plants in [t_from, t_to] -> [(t, side)]."""
    return INS_WALK.plant_times(t_from, t_to)


def _shot_c(f, t, T):
    tl = t - T_C
    p = _ins_pose(tl)
    J0 = rig.solve(p)
    cam_x = INS_HIP0 + 230.0 + 0.8 * INS_SPEED * tl + 40 * ease("out", inv_lerp(0, 1.2, tl))
    cam = Camera(cam_x, 960.0, 1.0).shaken(t, amp=5.0, rot_amp=0.25, freq=1.1, seed=12)
    f.set_camera(cam)
    hand = J0["lh"]
    ang = -64.0
    ms = 2.4
    tip = (hand[0] + math.cos(math.radians(ang)) * 52 * ms, hand[1] + math.sin(math.radians(ang)) * 52 * ms)
    fl = 0.9 + 0.1 * fbm1(t * 8, 2)
    # far side of the street + distant lamps (parallax depth, out of focus)
    far = cam.parallax(0.4)
    with f.camera(far):
        for i in range(-3, 8):
            bx = 300.0 + i * 640.0 + 260 * hash01(4, i)
            by = 330.0 + 160 * hash01(4, i, 1)
            draw.glow_dot(f, (bx, by), 230, AMBER, 0.42, core=False)
            draw.circle(f, (bx, by), 26, 1, AMBER, 0.18, fill_it=True)
        draw.line(f, (far.x - 900, 1388.0), (far.x + 900, 1388.0), 2.0, WHITE, 0.25)
    lights = [Light.radial((tip[0] - 40, tip[1] + 60), 640 * fl, intensity=1.0, hard=0.2),
              Light.radial((tip[0] - 120, INS_GROUND - 60), 700, intensity=0.9)]
    fx.light_pool(f, (tip[0], INS_GROUND + 12), 560, 44, AMBER, 0.22 * fl, glow=0.45)
    with f.lit(lights, ambient=0.0, soften=3.0):
        draw.line(f, (cam.x - 800, INS_GROUND), (cam.x + 800, INS_GROUND), 3.4, WHITE, 0.95)
        fx.ripples(f, t, cam.x - 700, INS_GROUND + 14, cam.x + 700, INS_GROUND + 130, rate=1.1,
                   alpha=0.5, squash=0.25)
        fx.rain(f, t, density=1.0, wind=9, seed=21, alpha=1.0)
        J = rig.draw_figure(f, p)
        for (tp, side) in ins_plants(T_C - 0.4, T_D):
            k = (t - tp) / 0.34
            if 0 <= k < 1:
                L.splash_side(f, (J[side + "f"][0], INS_GROUND), k, s=2.4, seed=int(tp * 100))
    fx.reflection(f, tip[0], INS_GROUND, 230, 210, AMBER, 0.6, t, seed=3)
    props.match(f, J["lh"], angle=ang, s=ms, lit=1.0, t=t, seed=4)


# ----------------------------------------------------------------------------- shot D (map)
def _block(i, j):
    return (GX0 + i * GPX + STW / 2, GY0 + j * GPY + STW / 2,
            GX0 + (i + 1) * GPX - STW / 2, GY0 + (j + 1) * GPY - STW / 2)


def _river_band(half):
    pts = draw.bezier_pts((-26000.0, 33000.0), (-6000.0, 19000.0), (14000.0, 28000.0),
                          (40000.0, 15500.0), 40)
    pl, pr = [], []
    for i in range(len(pts)):
        a, b = (pts[i], pts[i + 1]) if i + 1 < len(pts) else (pts[i - 1], pts[i])
        dx, dy = b[0] - a[0], b[1] - a[1]
        ll = math.hypot(dx, dy)
        nx, ny = -dy / ll, dx / ll
        pl.append((pts[i][0] + nx * half, pts[i][1] + ny * half))
        pr.append((pts[i][0] - nx * half, pts[i][1] - ny * half))
    return pts, pl, pr


RIVER, RIVER_L, RIVER_R = _river_band(1250.0)


def _map(f, t, cam, amber_k, edge_y, flood):
    z = cam.zoom
    x0, y0, x1, y1 = L.view_bounds(cam, 400)
    i0, i1 = int(math.floor((x0 - GX0) / GPX)) - 1, int(math.ceil((x1 - GX0) / GPX)) + 1
    j0, j1 = int(math.floor((y0 - GY0) / GPY)) - 1, int(math.ceil((y1 - GY0) / GPY)) + 1
    mapk = clamp(inv_lerp(0.35, 0.08, z))          # 0 street-level look -> 1 clean map look
    wc = L.screen_w(2.6, z)
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            bx0, by0, bx1, by1 = _block(i, j)
            cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
            a_on = amber_k if (amber_k > 0 and cx < X_AMB and cy < edge_y) else 0.0
            if a_on > 0:
                fa = 0.2 + (0.1 if (i, j) == TARGET_BLOCK else 0.05) * flood
                # a block that fills the frame must not bloom into yellow: damp its glow
                gk = 0.3 * a_on * (1.0 - 0.75 * clamp(inv_lerp(0.35, 1.6, z)))
                draw.rect(f, bx0, by0, bx1 - bx0, by1 - by0, 1, AMBER, fa * a_on, fill_it=True,
                          radius=110, glow=gk)
            col = AMBER if a_on > 0.5 else WHITE
            draw.rect(f, bx0, by0, bx1 - bx0, by1 - by0, wc, col, 0.95, radius=110)
            ix0, iy0, ix1, iy1 = bx0 + WALK_W, by0 + WALK_W, bx1 - WALK_W, by1 - WALK_W
            if (i, j) in (PLAZA, TARGET_BLOCK):
                continue
            if (i, j) == PARK:
                draw.rect(f, ix0, iy0, ix1 - ix0, iy1 - iy0, wc * 0.6, col, 0.45, radius=200)
                for q in range(9):
                    tx = ix0 + (ix1 - ix0) * (0.18 + 0.64 * hash01(61, q))
                    ty = iy0 + (iy1 - iy0) * (0.15 + 0.7 * hash01(61, q, 1))
                    draw.circle(f, (tx, ty), 120 + 60 * hash01(61, q, 2), wc * 0.6, col, 0.45)
                continue
            draw.rect(f, ix0, iy0, ix1 - ix0, iy1 - iy0, wc * 0.6, col, 0.5)
            nl = 1 + int(hash01(17, i, j) * 3)
            for q in range(nl):
                if hash01(17, i, j, q) < 0.5:
                    xx = ix0 + (ix1 - ix0) * (0.25 + 0.5 * hash01(17, i, j, q, 1))
                    draw.line(f, (xx, iy0), (xx, iy1), wc * 0.45, col, 0.35)
                else:
                    yy = iy0 + (iy1 - iy0) * (0.25 + 0.5 * hash01(17, i, j, q, 1))
                    draw.line(f, (ix0, yy), (ix1, yy), wc * 0.45, col, 0.35)
    # river (occludes the blocks it crosses)
    if mapk > 0:
        draw.fill(f, RIVER_L + RIVER_R[::-1], BLACK, 1.0)
        draw.stroke(f, RIVER_L, wc, WHITE, 0.9 * mapk)
        draw.stroke(f, RIVER_R, wc, WHITE, 0.9 * mapk)
        for q in range(2, len(RIVER) - 3, 2):
            a, b = RIVER[q], RIVER[q + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ll = math.hypot(dx, dy)
            for off in (-520.0, 380.0):
                nx, ny = -dy / ll * off, dx / ll * off
                sh = 0.25 + 0.3 * hash01(5, q, int(off))
                draw.line(f, (a[0] + nx + dx * sh, a[1] + ny + dy * sh),
                          (a[0] + nx + dx * (sh + 0.45), a[1] + ny + dy * (sh + 0.45)), wc * 0.6, WHITE,
                          0.4 * mapk)
    # amber outline of the search area: left half, bottom edge slides up on "quarter"
    if amber_k > 0:
        yb = min(edge_y, y1 + 4000)
        pts = [(x0 - 4000, y0 - 4000), (X_AMB, y0 - 4000), (X_AMB, yb), (x0 - 4000, yb)]
        draw.stroke(f, pts, L.screen_w(3.4, z), AMBER, 0.95 * amber_k, closed=True, glow=0.9 * amber_k)


def _cam_d(t, T):
    tq = T.at("quarter")
    if t < T_PUSH0:
        k = ease("inout", inv_lerp(T_D, T_PULL1, t))
        z = L.zlerp(1.40, MAP_Z, k)
        s0 = Camera(552.0, Y_MID - 20, 1.40).to_screen(TRAIL_PT)
        s1 = Camera(MAP_C[0], MAP_C[1], MAP_Z).to_screen(TRAIL_PT)
        cam = L.cam_anchor(TRAIL_PT, lerp(s0, s1, ease("inout", k)), z)
        if t > T_PULL1:                              # settle: a breath of drift on the map
            cam = cam.moved(dzoom=1.0 + 0.04 * (t - T_PULL1))
    else:
        k = ease("in", inv_lerp(T_PUSH0, T.duration, t))
        z0 = MAP_Z * (1.0 + 0.04 * (T_PUSH0 - T_PULL1))
        z = L.zlerp(z0, END_Z, k)
        s0 = Camera(MAP_C[0], MAP_C[1], z0).to_screen(TARGET)
        cam = L.cam_anchor(TARGET, lerp(s0, (540.0, 960.0), ease("inout", inv_lerp(T_PUSH0, 8.05, t))), z)
    pk = pulse(t, tq, 0.02, 0.25)                    # impact on "quarter"
    return cam.shaken(t, amp=10 * pk, rot_amp=0.3 * pk, freq=9, seed=4)


def _shot_d(f, t, T):
    tq = T.at("quarter")
    cam = _cam_d(t, T)
    f.set_camera(cam)
    zz = cam.zoom
    street = clamp(inv_lerp(0.42, 0.85, zz)) if t < T_PUSH0 else 0.0   # street detail fades as we rise
    amber_k = ease("inout", inv_lerp(6.18, 6.55, t))
    edge = 1e9
    if t >= tq:
        bottom = cam.to_world((540, 2100))[1]
        edge = lerp(max(bottom, Y_AMB + 1), Y_AMB, ease("out3", inv_lerp(tq, tq + 0.28, t)))
    flood = ease("in", inv_lerp(7.6, T.duration, t))
    pool = (556.0, POOL_Y)

    lights = [Light.radial(pool, 400.0, hard=0.25)]
    with f.lit(lights, ambient=lerp(0.11, 1.0, 1 - street), soften=3.0):
        if street > 0:
            _pavement(f, t, cam, detail=street)
            _prints(f)
        _map(f, t, cam, amber_k, edge, flood)
    if street > 0:
        with f.alpha(street):
            _print_sheen(f, t, pool, 400.0, 1.0, None, T)
            _tapes(f, t, T, full=True)
    # the match light shrinks to a "you are here" ember on the map
    fx.light_pool(f, pool, 330, 330, AMBER, 0.13, glow=0.35)
    here = (pool[0] + 10, pool[1] + 26)
    draw.glow_dot(f, here, max(150.0, 34.0 / zz), AMBER, 0.85)
    mk = clamp(inv_lerp(0.3, 0.12, zz)) * (1 - clamp(inv_lerp(7.2, 7.6, t)))
    if mk > 0:
        draw.circle(f, here, 7.0 / zz, 1, AMBER, mk, fill_it=True, glow=1.0)
        ring = ((t - 6.3) % 0.9) / 0.9
        draw.circle(f, here, (10 + 26 * ring) / zz, L.screen_w(2.2, zz), AMBER, mk * (1 - ring), glow=0.6)
    # the round lit skylight inside the quadrant that the push dives into
    tg = clamp(inv_lerp(6.9, 7.3, t))
    if tg > 0:
        fl = 0.94 + 0.06 * fbm1(t * 6, 9)
        draw.circle(f, TARGET, TARGET_R * 1.25, L.screen_w(2.4, zz), AMBER, tg * 0.8)
        draw.circle(f, TARGET, TARGET_R, 1, AMBER, tg * fl * (0.85 + 0.15 * flood), fill_it=True, glow=0.9)
        draw.glow_dot(f, TARGET, lerp(1500.0, 520.0, clamp(zz / 1.5)) * (1 + 0.5 * flood), AMBER,
                      (0.5 + 0.1 * flood) * tg * fl, core=False)
    if street > 0.02:
        L.rain_top_vp(f, t, n=100, seed=3, alpha=0.3 * street)


# ----------------------------------------------------------------------------- entry points
def render(f, t, T):
    if t < T_C:
        _shot_ab(f, t, T)
    elif t < T_D:
        _shot_c(f, t, T)
    else:
        _shot_d(f, t, T)


def cues(T):
    c = [Cue(0.0, "crowd_walla", gain_db=-20, dur=1.1),
         Cue(0.22, "match_strike", gain_db=-6, pan=0.05),
         Cue(0.27, "match_flare", gain_db=-9)]
    # the detective follows the prints off-screen: uneven wet steps (quiet plant)
    for i, tc in enumerate((0.55, 0.78, 1.25, 1.47, 1.95, 2.16)):
        c.append(Cue(tc, "footstep", gain_db=-13 + (0 if i % 2 else -3), pan=0.1,
                     weight=0.45 if i % 2 == 0 else 0.75, wet=1))
    c += [Cue(T.at("short") - 0.02, "tape_measure", gain_db=-6, pan=0.2),
          Cue(T.at("long") - 0.02, "tape_measure", gain_db=-5, pan=0.25)]
    # the insert: his own steps, the same short-long rhythm (LEFT = light quick step)
    for tp, side in ins_plants(T_C, T_D):
        c.append(Cue(tp, "footstep", gain_db=-5 if side == "r" else -9, pan=-0.1,
                     weight=0.8 if side == "r" else 0.4, wet=1))
    c += [Cue(T_C - 0.01, "whoosh", gain_db=-16, size=0.25),
          Cue(T_D - 0.02, "whoosh", gain_db=-9, size=0.7),
          Cue(T.at("quarter"), "impact", gain_db=-6, size=0.6),
          Cue(T_PUSH0, "riser", gain_db=-12, dur=T.duration - T_PUSH0)]
    return c


def motion_blur(t, T):
    if 5.86 < t < 6.5:
        return 6
    if t > 8.12:
        return 3
    return 1
