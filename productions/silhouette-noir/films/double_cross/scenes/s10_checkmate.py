"""s10 CHECKMATE (124-136). The Knight gets away, and the city closes on him like a chessboard.
  The front street at night, the alarm bell ringing red high in the alley. The Knight bursts
    round the car's tail with two heavy sacks, heaves them in through the open rear door and
    slams it. Close on the car's nose: the engine coughs, the headlight flares, the car
    lurches off and the light fills the frame.
  The city from above: its blocks are the squares of a chessboard, with the blueprint of the
    bank in the middle. His car (red-edged) lurches out at the end of his red trail. From the
    four ends of the streets four police cars slide in nose first like rooks, one per beat
    (W, N, E, S: exactly as she chalked them in Plan B), bars flashing. A red marker ring
    closes round him: checkmate. The camera rolls (his panic).
  His face in the car window, washed red and blue, eyes darting.
  Behind the bank, the back street (full frame, north-looking, the ground cut open below it):
    the wall across the street flickers red and blue above the bank's roof shadow. Up manhole
    B's shaft she climbs, shoves the lid up and slides it aside, steps out and walks off west
    under the street lamp; the Cracker climbs out after her. Her white route lights behind them.
  The board again, pulling back: two small figures walking west from manhole B. Then his red
    route and her white one straighten into two strokes crossing over the bank: an X.
"""
import math

from engine import bass
from engine import paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.double_cross import bank as Bk
from films.double_cross import cast as C
from films.double_cross import faces as F
from films.double_cross import kit as K
from films.double_cross import plan as P
from films.double_cross import shots as S

# ============================================================================ the street
T_RUN = 0.2                      # he bursts round the car's tail (the mocap's run and stop)
T_HEAVE = (0.95, 1.12)           # both sacks swung up ...
T_THROW = (1.12, 1.26)           # ... and flung in
T_SLAM = (1.32, 1.42)            # he slams the rear door
T_NOSE = 1.46                    # close on the car's nose
T_COUGH = (1.62, 1.86)           # the engine coughs twice ...
T_LIGHTS = 2.02                  # ... the headlight flares, the engine catches
T_LURCH = (2.5, 2.9)             # the car lurches off west
T_FLASH = (2.68, 2.92)           # the light fills the frame
STREET_CAM = Bk.Cam(1010.0, -232.0, 2.5)
NOSE_CAM = Bk.Cam(838.0, -66.0, 7.2)
STOP_X = 1052.0                  # where he stops, at the open rear door
DOOR_IN = (1005.0, -54.0)        # the rear door's opening (set px)

# ============================================================================ the board
T_BOARD = 2.92
T_SPEED = (3.15, 3.55)           # his car lurches forward along the front street
T_COPS = (4.0, 4.5, 5.0, 5.5)    # the police slide in, one per beat
T_MATE = 6.0                     # the red ring: checkmate
T_ROLL = (6.0, 6.42)             # the camera rolls: his panic
T_FACE = (6.42, 7.2)
T_BACK = 7.2                     # cut from his face to the back street: her way out
T_ESC = (7.2, 9.5)               # the escape, full frame
T_LID = (7.6, 7.88)              # she slides manhole B's lid off east (it rose on her hand from 7.47)
CLIMB = {"architect": (7.2, 0.0, 7.47, 36.0, 7.88, 8.06),      # (t0, h0, t at the lid, h, t1, out on the road)
         "cracker": (7.95, 0.0, 8.35, 36.0, 8.65, 8.86)}
T_GO = {"architect": 8.12, "cracker": 8.98}                     # they set off west, in file
T_BOARD_BACK = 9.5               # the board again, pulling back
T_UP = (8.6, 8.9)                # on the board: when the two small walkers are out (in file, west)
T_X = (10.0, 11.2)               # the routes straighten into the X
CAR_HOME = P.CAR
CAR_STOP = (P.CAR[0] - 30.0, P.CAR[1])
# (direction from his car, distance at rest, approach angle of travel): W, N, E, S as in Plan B
COPS = (((-1.0, 0.0), 100.0), ((0.0, -1.0), 82.0), ((1.0, 0.0), 100.0), ((0.0, 1.0), 82.0))
COP_RUN = 2300.0                 # how far down its street each police car starts
STREETS_X = tuple(120.0 + 837.0 * k for k in range(-3, 5))     # the north-south streets (centres)
STREETS_Y = tuple(280.0 + 1120.0 * k for k in range(-3, 5))    # the east-west streets
STREET_W = 100.0
BOARD_KEYS = ((2.92, (560.0, 1150.0, 0.36, 0.0)), (3.6, (690.0, 1260.0, 0.42, 0.0)),
              (5.9, (900.0, 1400.0, 1.0, 0.0)), (6.42, (900.0, 1400.0, 1.16, -10.0)))
BACK_KEYS = ((T_BOARD_BACK, (420.0, 560.0, 1.3, 0.0)), (10.35, (556.0, 900.0, 0.6, 0.0)),
             (12.0, (548.0, 880.0, 0.56, 0.0)))
WALK_V = 150.0                   # plan px / s: two small figures walking west
HER_ROUTE = P.ROUTE_B
HIS_ROUTE = list(P.ROUTE_KNIGHT) + [CAR_STOP]
X_CENTRE = (540.0, 960.0)
X_HALF = 1180.0                  # the X's strokes reach past the frame's corners
_DIAG = math.atan2(K.H, K.W)

LIGHT_SQ = lerp(K.NAVY, K.STEEL, 0.5)
DARK_SQ = lerp(K.INK, K.NAVY, 0.45)
ROAD = lerp(K.INK, K.NAVY, 0.15)


def motion_blur(t, T):
    return 1


# ============================================================================ the street (north-looking)
_PERF = {}


def _run():
    if "run" not in _PERF:
        cl = C.clip("16_08")
        p = C.perf("knight", [C.Seg(cl, 0.0, 1.75, at=T_RUN)], facing=-1)
        travel = p(T_RUN + 1.75)[0]["pelvis"][0] - p(T_RUN)[0]["pelvis"][0]
        _PERF["run"] = (p, STOP_X - travel * Bk.FIG_S)
    return _PERF["run"]


def knight_state(t):
    """(state, pose, x0, sacks) of the Knight on the street: x0 the set x he is drawn at; sacks:
    'held' (in his fists), or 'thrown' (in the air), or None."""
    p, x0 = _run()
    st, pose = p(max(t, T_RUN))
    heave = ease("inout", clamp((t - T_HEAVE[0]) / (T_HEAVE[1] - T_HEAVE[0])))
    drop = ease("inout", clamp((t - T_THROW[1]) / 0.2))
    slam = clamp((t - (T_SLAM[0] - 0.08)) / 0.12)
    # the arms: hanging with the weight (a little swing in the run), up to the door, then down
    sw = 10.0 * math.sin(2.0 * math.pi * 3.0 * (t - T_RUN)) * (1.0 - heave)
    sh = lerp(8.0 + sw, 112.0, heave) * (1.0 - drop) + 14.0 * drop
    el = lerp(14.0, 34.0, heave) * (1.0 - drop) + 20.0 * drop
    pose.arms["near"] = ("ang", sh + 4.0, el)
    pose.arms["far"] = ("ang", sh - 4.0, el + 6.0)
    pose.lean = pose.lean + 26.0 * heave * (1.0 - drop) + 8.0 * drop
    if slam > 0.0:                                         # the near hand shoves the door to
        g = math.sin(math.pi * slam)
        pose.arms["near"] = ("ang", lerp(14.0, 96.0, g), lerp(20.0, 8.0, g))
        pose.lean = pose.lean + 10.0 * g
    sacks = "held" if t < T_THROW[0] else ("thrown" if t < T_SLAM[0] else None)
    if sacks == "held":
        pose.hold = {"near": Bk.hold_sack(1.0, seed=41), "far": Bk.hold_sack(1.0, seed=42)}
    return st, pose, x0, sacks


def _door(t):
    return 1.0 - ease("in", clamp((t - T_SLAM[0]) / (T_SLAM[1] - T_SLAM[0])))


def _bell_ripples(c, cam, t):
    with cam.on(c):
        for k in range(int((t + 0.5) / 0.5) + 1):
            K.ripple(c, Bk.BELL_SET, t, k * 0.5 - 0.5, K.RED, n=1, life=0.6, r0=14.0, r1=120.0, width=4.0)


def street_shot(c, t):
    cam = STREET_CAM
    shake = 3.0 * math.sin(t * 90.0) * clamp(1.0 - (t - T_SLAM[0]) / 0.15) if t >= T_SLAM[0] else 0.0
    if shake:
        cam = Bk.Cam(cam.x, cam.y + shake / cam.zoom, cam.zoom)
    Bk.front_street(c, cam, t, bell=1.0, car_door=_door(t), lamp=1.0)
    _bell_ripples(c, cam, t)
    st, pose, x0, sacks = knight_state(K.twos(t))
    with cam.on(c):
        out = C.draw(c, "knight", st, pose, x0, 0.0, Bk.FIG_S, -1, bg=K.NAVY, rim_w=4.0 / cam.zoom,
                     light=(0.5, -0.85))
        if sacks == "thrown":                              # two sacks flying in at the door
            u = ease("in", clamp((K.twos(t) - T_THROW[0]) / (T_THROW[1] - T_THROW[0])))
            for k, side in enumerate(("hand_near", "hand_far")):
                h = cam.to_set(cam.to_frame(out[side])) if side in out else (STOP_X - 30.0, -80.0)
                h = out.get(side, h)
                p = (lerp(h[0], DOOR_IN[0] + 10.0 * k, u), lerp(h[1] + 34.0, DOOR_IN[1] + 22.0, u) - 26.0 * math.sin(math.pi * u))
                Bk.sack(c, p, 1.0, s=1.0 - 0.3 * u, color=K.INK, rim=K.RED, seed=41 + k)


def _exhaust(c, cam, t):
    """Two coughs: puffs of smoke rolling out of the tail pipe (set px)."""
    tail = (Bk.CAR_X + Bk.CAR_L / 2.0 + 6.0, -16.0)
    with cam.on(c):
        for k, t0 in enumerate((T_COUGH[0], T_COUGH[1], T_LIGHTS + 0.1)):
            a = (t - t0) / 0.7
            if 0.0 <= a < 1.0:
                for j in range(3):
                    r = (6.0 + 16.0 * ease("out3", a)) * (1.0 - 0.2 * j)
                    p = (tail[0] + 20.0 * a + 14.0 * j * a, tail[1] - 12.0 * a - 6.0 * j * a)
                    K.dot(c, p, r, K.STEEL, seed=60 + k * 5 + j, alpha=0.55 * (1.0 - a))


def nose_shot(c, t):
    on = clamp((t - T_LIGHTS) / 0.25)
    cough = 0.0
    for t0 in T_COUGH:
        if t0 <= t < t0 + 0.16:
            cough = 2.5 * math.sin(math.pi * (t - t0) / 0.16)
    lurch = ease("in", clamp((t - T_LURCH[0]) / (T_LURCH[1] - T_LURCH[0])))
    cam = Bk.Cam(NOSE_CAM.x, NOSE_CAM.y + cough / NOSE_CAM.zoom, NOSE_CAM.zoom)
    Bk.front_street(c, cam, t, bell=1.0, headlights=on, lamp=1.0, car_x=Bk.CAR_X - 220.0 * lurch)
    _exhaust(c, cam, t)
    f = clamp((t - T_FLASH[0]) / (T_FLASH[1] - T_FLASH[0]))
    if f > 0.0:
        K.fill(c, K.PAPER, alpha=ease("in", f))


# ============================================================================ the board (plan px, from above)
def _keyed(keys, t):
    v = keys[-1][1] if t >= keys[-1][0] else keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if a <= t < b:
            u = ease("inout3", (t - a) / (b - a))
            v = (lerp(va[0], vb[0], u), lerp(va[1], vb[1], u), math.exp(lerp(math.log(va[2]), math.log(vb[2]), u)),
                 lerp(va[3], vb[3], u))
            break
    return P.PlanCam(v[0], v[1], v[2], 90.0, v[3])


def board_cam(t):
    return _keyed(BOARD_KEYS if t < T_BACK else BACK_KEYS, t)


def _blocks():
    """[(rect, kind)]: the city's blocks between its streets; kind 'light', 'dark' or 'bank'."""
    out = []
    h = STREET_W / 2.0
    for i, (xa, xb) in enumerate(zip(STREETS_X, STREETS_X[1:])):
        for j, (ya, yb) in enumerate(zip(STREETS_Y, STREETS_Y[1:])):
            r = (xa + h, ya + h, xb - h, yb - h)
            bank = abs(xa - 120.0) < 1.0 and abs(ya - 280.0) < 1.0
            out.append((r, "bank" if bank else ("light" if (i + j) % 2 == 0 else "dark")))
    return out


BLOCKS = _blocks()


def _roofs(r, seed):
    """A few rooftops in a block: cut rectangles inset from its edges."""
    x0, y0, x1, y1 = r
    out = []
    n = 2 + int(hash01(seed, 1) * 3)
    for k in range(n):
        w = (x1 - x0) * (0.22 + 0.3 * hash01(seed, k, 2))
        hgt = (y1 - y0) * (0.16 + 0.22 * hash01(seed, k, 3))
        x = x0 + 40.0 + (x1 - x0 - 80.0 - w) * hash01(seed, k, 4)
        y = y0 + 40.0 + (y1 - y0 - 80.0 - hgt) * hash01(seed, k, 5)
        out.append((x, y, x + w, y + hgt))
    return out


def draw_board(c, t, dim=0.0):
    """The city as a chessboard (plan px): the roads, the blocks in light and dark squares with
    their rooftops, and the bank's block as the blueprint, the plan's walls chalked on it."""
    K.fill(c, ROAD)
    for x in STREETS_X:                                    # the roads' centre lines
        K.dashes(c, [(x, STREETS_Y[0] - 600.0), (x, STREETS_Y[-1] + 600.0)], K.PAPER, 3.0, 26.0, 30.0, seed=7,
                 alpha=0.18)
    for y in STREETS_Y:
        K.dashes(c, [(STREETS_X[0] - 600.0, y), (STREETS_X[-1] + 600.0, y)], K.PAPER, 3.0, 26.0, 30.0, seed=8,
                 alpha=0.18)
    for k, (r, kind) in enumerate(BLOCKS):
        x0, y0, x1, y1 = r
        if kind == "bank":
            bass.fill_polys(c, [bass.cut_rect(x0 - 10.0, y0 - 10.0, x1 + 10.0, y1 + 10.0, seed=300, amp=0.8)], K.BLUE)
            c.save()
            c.rectangle(x0 - 10.0, y0 - 10.0, x1 - x0 + 20.0, y1 - y0 + 20.0)
            c.clip()
            P.draw_plan(c, u={"streets": 0.0, "sewer": 0.0, "manholes": 0.0})
            c.restore()
            continue
        col = LIGHT_SQ if kind == "light" else DARK_SQ
        bass.fill_polys(c, [bass.cut_rect(x0, y0, x1, y1, seed=310 + k, amp=0.8)], col)
        roof = lerp(col, K.INK, 0.28) if kind == "light" else lerp(col, K.STEEL, 0.22)
        for i, rr in enumerate(_roofs(r, 320 + k)):
            bass.fill_polys(c, [bass.cut_rect(*rr, seed=330 + k * 7 + i, amp=0.5)], roof)
        K.chalk_rect(c, r, 1.0, 3.0, K.PAPER, seed=340 + k, alpha=0.22)
    for p in (P.MANHOLE_A, P.MANHOLE_B):
        P.manhole(c, p, 20.0, 1.0, K.PAPER, seed=350, alpha=0.6)
    if dim > 0.0:
        K.fill(c, K.NAVY, alpha=dim)


def car_at(t):
    """His car's centre on the plan."""
    u = ease("inout", clamp((t - T_SPEED[0]) / (T_SPEED[1] - T_SPEED[0])))
    jolt = 0.0
    if t >= T_COPS[0]:                                     # braking hard as the first car blocks him
        a = clamp((t - T_COPS[0]) / 0.3)
        jolt = 10.0 * math.sin(math.pi * a) * (1.0 - a)
    return (lerp(CAR_HOME[0], CAR_STOP[0], u) + jolt, CAR_HOME[1])


def cop_at(i, t):
    """(centre, heading degrees, arrived 0..1) of police car i."""
    (dx, dy), d1 = COPS[i]
    k = t - T_COPS[i] + 0.36
    u = clamp(k / 0.36)
    run = COP_RUN * (1.0 - ease("outback", u)) if u < 1.0 else 0.0
    d = d1 + run
    cx, cy = CAR_STOP
    p = (cx + dx * d, cy + dy * d)
    return p, math.degrees(math.atan2(-dy, -dx)), u


def _his_car(c, t, cam):
    p = car_at(t)
    K.route(c, HIS_ROUTE[:-1] + [p], 1.0, K.RED, r=6.5, gap=22.0, head=0.0, seed=5)
    if t >= T_SPEED[0] - 0.1:                              # the headlights, west
        K.cone(c, (p[0] - 52.0, p[1]), 180.0, 18.0, 300.0, K.PAPER, alpha=0.14, seed=9)
    K.car(c, p, 180.0, 0.9, K.INK, K.RED, ew=5.0)


def _cops(c, t):
    for i in range(4):
        if t < T_COPS[i] - 0.36:
            continue
        p, ang, u = cop_at(i, t)
        if u < 1.0:                                        # streaks behind it as it slides in
            back = (-math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
            for j in range(3):
                off = (j - 1) * 16.0
                n = (-back[1] * off, back[0] * off)
                a = (p[0] + back[0] * 70.0 + n[0], p[1] + back[1] * 70.0 + n[1])
                b = (a[0] + back[0] * 420.0 * (1.0 - u), a[1] + back[1] * 420.0 * (1.0 - u))
                K.chalk_line(c, [a, b], 1.0, 4.0, K.PAPER, seed=70 + i * 3 + j, alpha=0.45)
        K.car(c, p, ang, 0.9, K.INK, K.PAPER, ew=4.0)
        K.police_lights(c, p, ang, t, s=0.9, beams=u >= 1.0, seed=80 + i)
        if u >= 1.0:
            K.ripple(c, p, t, T_COPS[i], K.POLICE if i % 2 == 0 else K.RED, n=2, every=0.14, life=0.5, r0=20.0,
                     r1=120.0, width=5.0)


def _ring(c, t):
    u = ease("out3", clamp((t - T_MATE) / 0.3))
    if u > 0.0:
        K.marker_ring(c, CAR_STOP, 168.0, 132.0, u, K.RED, width=16.0, seed=90)
    if t >= T_MATE + 0.3:
        K.ripple(c, CAR_STOP, t, T_MATE + 0.3, K.RED, n=2, every=0.2, life=0.7, r0=150.0, r1=300.0, width=6.0)


# ============================================================================ the pull-back
def _lid(c, t):
    u = ease("inout", clamp((t - T_LID[0]) / (T_LID[1] - T_LID[0])))
    if u > 0.0:
        bass.fill_polys(c, [bass.ring_pts(P.MANHOLE_B, 21.0, seed=361, n=24)], K.INK)
        p = (P.MANHOLE_B[0] + 48.0 * u, P.MANHOLE_B[1] - 16.0 * u)          # slid off east: they go west
        K.dot(c, p, 22.0, lerp(K.STEEL, K.INK, 0.3), seed=362)
        K.chalk_circle(c, p, 22.0, 1.0, 3.0, K.PAPER, seed=363, alpha=0.6)


def walker_at(k, t):
    """(position, shown 0..1) of the small figure k (0 her, 1 the Cracker) in the back street:
    single file along her route, west."""
    t0 = T_UP[k]
    if t < t0:
        return None, 0.0
    g = ease("outback", clamp((t - t0) / 0.25))
    s = max(0.0, t - t0 - 0.2) * WALK_V
    return (P.MANHOLE_B[0] - 4.0 - s, P.MANHOLE_B[1]), g


def _walkers(c, t):
    """Two small figures seen from above, walking west: INK, rimmed in their colours (her chalk,
    his gold); her chignon and her match, his bowler's brim."""
    for k in (1, 0):
        p, g = walker_at(k, t)
        if p is None:
            continue
        rim = K.PAPER if k == 0 else K.GOLD
        ph = 2.0 * math.pi * 2.2 * K.twos(t) + math.pi * k
        for side in (-1.0, 1.0):                           # the arms swinging
            a = (p[0] + 8.0 * math.sin(ph) * side, p[1] + side * 17.0 * g)
            K.dot(c, a, 7.0 * g, rim, seed=370 + k)
            K.dot(c, a, 5.2 * g, K.INK, seed=371 + k)
        Bk.ellipse(c, p, 12.0 * g, 21.0 * g, rim, n=28)    # the shoulders
        Bk.ellipse(c, p, 10.0 * g, 19.0 * g, K.INK, n=28)
        head = (p[0] - 3.0, p[1])
        if k == 1:                                         # his bowler: brim and crown
            K.dot(c, head, 13.5 * g, K.GOLD, seed=373)
            K.dot(c, head, 11.5 * g, K.INK, seed=374)
            K.chalk_circle(c, head, 7.0 * g, 1.0, 2.0, K.GOLD, seed=375, alpha=0.8)
        else:
            K.dot(c, (head[0] + 9.0 * g, head[1]), 5.5 * g, K.PAPER, seed=376)      # the chignon
            K.dot(c, (head[0] + 9.0 * g, head[1]), 4.0 * g, K.INK, seed=377)
            K.dot(c, head, 10.0 * g, K.PAPER, seed=378)
            K.dot(c, head, 8.2 * g, K.INK, seed=379)
            m = (p[0] - 20.0 * g, p[1] - 13.0 * g)                                  # the match
            K.match_light(c, m, t, 80.0, 0.9, seed=381)
            K.dot(c, m, 3.5 * g, K.GOLD, seed=382)


def _her_route(c, t):
    """Plan B's white route: underground to manhole B (already walked), then lit behind her."""
    L_under = K.poly_len(HER_ROUTE[:3])
    L = K.poly_len(HER_ROUTE)
    if t < T_BACK + 0.4:
        return
    u_under = ease("inout", clamp((t - (T_BACK + 0.4)) / 0.5))
    p, _ = walker_at(0, t)
    s = L_under * u_under
    if p is not None:
        s = max(s, L_under + (P.MANHOLE_B[0] - p[0]))
    K.route(c, HER_ROUTE, clamp(s / L), K.PAPER, solid=True, width=7.0, head=26.0, seed=380)


# ============================================================================ her way out (north-looking)
HOLE = P.MANHOLE_B[0]            # set x = plan x: the back street runs west, to the left
SHAFT = (HOLE - 22.0, HOLE + 22.0)
FOOT = 170.0                     # the shaft's foot: the branch pipe, seen end on below it
PIPE_C, PIPE_R = (HOLE, 214.0), 42.0
LID_W = 52.0
LAMP_AT = 330.0                  # the street lamp, west of the hole: she walks in under it
LAMP_S = 0.72
ROOF = -205.0                    # the bank's roof line, its shadow across the wall: above, the police light
ROUTE_H = -30.0                  # her route at shin height (as s09 left it, up out of the shaft)
WALK_SET = 0.2 * 430.0           # set px / s
ESC_CAMS = (Bk.Cam(398.0, -65.0, 3.4), Bk.Cam(352.0, -65.0, 3.4))
WINDOWS = ((196.0, 246.0), (366.0, 416.0), (520.0, 570.0), (690.0, 740.0))


def esc_cam(t):
    return Bk.Cam.lerp(ESC_CAMS[0], ESC_CAMS[1], ease("inout", clamp((t - T_ESC[0]) / (T_ESC[1] - T_ESC[0]))))


_ESC_WALK = {}


def _esc_walker(who):
    if who not in _ESC_WALK:
        t0 = T_GO[who]
        _ESC_WALK[who] = pd.Walker(C.fig(who), 0.0, speed=((t0, 0.0), (t0 + 0.3, 430.0), (13.0, 430.0)), t0=t0 - 1.0,
                                   t1=13.0)
    return _ESC_WALK[who]


def climb_h(who, t):
    """How far up the rungs `who` has climbed at t (set px): to the lid, a pause on it, then out."""
    t0, h0, tl, hl, t1, tout = CLIMB[who]
    if t < tl:
        return lerp(h0, hl, clamp((t - t0) / (tl - t0)))
    if t < t1 - 0.18:
        return hl + 6.0 * clamp((t - tl) / 0.3)
    return lerp(hl + 6.0, FOOT - 12.0, ease("inout", clamp((t - (t1 - 0.18)) / (tout - t1 + 0.18))))


def esc_state(who, t):
    """(x, floor y, state, pose) of `who` in the back street, drawn facing east and mirrored about x
    (so they face west): up the rungs, out onto the road, then walking west."""
    t0, h0, tl, hl, t1, tout = CLIMB[who]
    x_rungs = HOLE + (4.0 if who == "architect" else -4.0)
    if t < tout:
        h = climb_h(who, t)
        st, pose = Bk.ladder_pose(who, max(0.0, h), 1)
        if who == "architect" and tl - 0.05 <= t < t1:              # her near hand flat on the lid, shoving
            pose.arms["near"] = ("ik", (40.0, -(h * 5.0) - 640.0))
        if t >= t1 - 0.18:                                          # out: both hands on the road, pushing up
            road = -FOOT / Bk.FIG_S + 10.0
            pose.arms["near"] = ("ik", (150.0, road))
            pose.arms["far"] = ("ik", (-110.0, road))
        below = 0.0 if who == "architect" else 90.0 * (1.0 - ease("out", clamp((t - t0) / 0.3)))   # up out of the pipe
        return x_rungs, FOOT + below, st, pose
    wk = _esc_walker(who)
    st = wk.state(max(t, T_GO[who] - 0.5))
    rise = clamp((t - tout) / 0.22)
    pose = pd.Pose(lean=lerp(22.0, 4.0, rise), head=lerp(10.0, -6.0, rise), crouch=110.0 * (1.0 - ease("out", rise)))
    pose.arms["near"] = ("ang", lerp(40.0, 10.0, rise), 22.0)
    pose.arms["far"] = ("ang", lerp(-10.0, 4.0, rise), 16.0)
    return x_rungs - 8.0, 0.0, st, pose


def esc_steps(who):
    """[(t, set x)]: their footfalls on the back street, on into the board's pull-back (the cues)."""
    wk = _esc_walker(who)
    x0 = HOLE + (4.0 if who == "architect" else -4.0) - 8.0
    return [(tt, x0 - fx * Bk.FIG_S) for tt, side, fx in Bk.footfalls(lambda u: (wk.state(u), None), T_GO[who],
                                                                       T_X[0])]


def rung_times(who):
    """When a boot comes down on the next rung (one a rung of the climb)."""
    t0, h0, tl, hl, t1, tout = CLIMB[who]
    out, k = [], int(h0 // Bk.RUNG_STEP) + 1
    for i in range(1, 241):
        t = t0 + (tout - t0) * i / 240.0
        if climb_h(who, t) >= k * Bk.RUNG_STEP:
            out.append(round(t, 3))
            k += 1
    return out


def _lid_b(c, t):
    """Manhole B's lid: pushed up off its seat on her hand, slid off east, dropped on the road."""
    lift = 9.0 * ease("out", clamp((t - (T_LID[0] - 0.13)) / 0.13)) * (1.0 - ease("in", clamp((t - T_LID[1]) / 0.06)))
    slide = 60.0 * ease("inout", clamp((t - T_LID[0]) / (T_LID[1] - T_LID[0])))
    x0 = HOLE - LID_W / 2.0 + slide
    Bk.rect(c, (x0, -6.0 - lift, x0 + LID_W, -0.5 - lift), lerp(K.STEEL, K.INK, 0.25), amp=0.2)
    Bk.band(c, (x0 + 2.0, -6.5 - lift), (x0 + LID_W - 2.0, -6.5 - lift), 1.6, lerp(K.STEEL, K.PAPER, 0.35), seed=5011)


def _back_street(c, t):
    """The set (set px): the wall across the back street, police light above the bank's roof
    shadow, a door, windows, a drainpipe; the lamp; the road; the ground cut open under it,
    manhole B's shaft and the branch pipe end on."""
    x0, x1 = -300.0, 1300.0
    Bk.rect(c, (x0, -900.0, x1, 0.0), lerp(K.INK, K.NAVY, 0.55), amp=0.0)            # the wall
    for k in range(9):                                                                # its courses
        y = -40.0 - 52.0 * k
        Bk.band(c, (x0, y), (x1, y), 1.4, lerp(K.INK, K.NAVY, 0.3), seed=5020 + k)
    for i, (wa, wb) in enumerate(WINDOWS):
        lit = i == 2
        Bk.rect(c, (wa, -300.0, wb, -228.0), lerp(K.INK, K.GOLD, 0.35) if lit else K.INK, amp=0.3)
        Bk.band(c, ((wa + wb) / 2.0, -300.0), ((wa + wb) / 2.0, -228.0), 2.0, lerp(K.INK, K.NAVY, 0.5), seed=5030 + i)
        Bk.band(c, (wa - 5.0, -225.0), (wb + 5.0, -225.0), 3.0, lerp(K.NAVY, K.STEEL, 0.4), seed=5034 + i)
    Bk.rect(c, (226.0, -122.0, 278.0, -6.0), K.INK, amp=0.3)                        # a back door, shut
    Bk.band(c, (222.0, -125.0), (282.0, -125.0), 3.0, lerp(K.NAVY, K.STEEL, 0.4), seed=5038)
    Bk.band(c, (566.0, -900.0), (566.0, -8.0), 4.0, lerp(K.INK, K.STEEL, 0.4), seed=5039)   # the drainpipe
    tt = K.twos(t)                                           # the police at the front: their light over the roof
    blue = (tt * 3.0) % 1.0 < 0.5
    with Bk.clipped(c, (x0, -900.0, x1, ROOF + 6.0 * math.sin(tt * 2.0))):
        sweep = lerp(-200.0, 1200.0, (tt * 1.5) % 1.0)
        K.pool(c, (sweep, ROOF - 70.0), 300.0, 120.0, K.POLICE if blue else K.RED, 0.26, steps=4)
        K.pool(c, (sweep - 620.0, ROOF - 90.0), 240.0, 100.0, K.RED if blue else K.POLICE, 0.16, steps=3)
    Bk.band(c, (x0, ROOF), (x1, ROOF + 12.0), 2.0, lerp(K.INK, K.NAVY, 0.2), seed=5040)
    Bk.rect(c, (x0, -12.0, x1, 0.0), lerp(K.NAVY, K.STEEL, 0.35), amp=0.0)           # the far pavement
    Bk.band(c, (x0, -12.0), (x1, -12.0), 2.0, lerp(K.STEEL, K.PAPER, 0.2), seed=5041)
    c.save()
    c.translate(LAMP_AT, 0.0)
    c.scale(LAMP_S, LAMP_S)
    c.translate(-Bk.LAMP_X, 0.0)
    Bk.street_lamp(c, 1.0, 1.0)
    c.restore()
    # the ground in section: earth, the road slab, the shaft and its rungs, the pipe end on
    Bk.rect(c, (x0, 0.0, x1, 900.0), Bk.EARTH, amp=0.0)
    Bk.rect(c, (x0, 2.0, x1, Bk.ROAD), Bk.SLAB, amp=0.0)
    Bk.disc(c, PIPE_C, PIPE_R + 9.0, Bk.LINING, seed=5050)
    Bk.disc(c, PIPE_C, PIPE_R, Bk.TUNNEL, seed=5051)
    with Bk.clipped(c, (PIPE_C[0] - PIPE_R - 2.0, PIPE_C[1] + 22.0, PIPE_C[0] + PIPE_R + 2.0, PIPE_C[1] + PIPE_R + 2.0)):
        Bk.disc(c, PIPE_C, PIPE_R, K.INK, seed=5052)                                 # the water in it
    Bk.rect(c, (SHAFT[0], -1.0, SHAFT[1], FOOT + 8.0), Bk.TUNNEL, amp=0.0)
    Bk._rungs(c, SHAFT[0], SHAFT[1], 4.0, FOOT, seed=5053)
    Bk.band(c, (x0, 1.0), (x1, 1.0), 4.0, lerp(K.STEEL, K.NAVY, 0.25), seed=5054)   # the road's surface
    for xx in (SHAFT[0], SHAFT[1]):
        Bk.band(c, (xx, 0.0), (xx, FOOT), 2.0, lerp(K.STEEL, K.NAVY, 0.3), seed=5055 + int(xx) % 7)


def _esc_route(c, t):
    """Her white route: lit up the shaft to the street already (s09 lit it), then west along the
    street behind her at shin height."""
    pts = [(HOLE, FOOT + 20.0), (HOLE, ROUTE_H)]
    if t >= T_GO["architect"]:
        x, _, st, _ = esc_state("architect", t)
        pts.append((min(HOLE - 1.0, x - st["pelvis"][0] * Bk.FIG_S + 30.0), ROUTE_H))
    K.route(c, pts, 1.0, K.PAPER, solid=True, width=3.4, head=13.0, r=3.0, seed=5060)


def _esc_fig(c, who, t, cam):
    """Drawn facing east and mirrored about x (so facing west), rimmed toward the lamp; in the
    shaft, clipped to it."""
    x, y, st, pose = esc_state(who, t)
    with cam.on(c):
        c.new_path()
        c.rectangle(-1000.0, -2000.0, 3000.0, 2000.0)                 # above the road ...
        c.rectangle(SHAFT[0] + 1.0, 0.0, SHAFT[1] - SHAFT[0] - 2.0, FOOT + 70.0)   # ... and down the shaft
        c.clip()
        c.translate(x, 0.0)
        c.scale(-1.0, 1.0)
        c.translate(-x, 0.0)
        C.draw(c, who, st, pose, x, y, Bk.FIG_S, 1, bg=K.INK, rim_w=4.0 / cam.zoom, light=(0.6, -0.8))


def escape_shot(c, t):
    cam = esc_cam(t)
    K.fill(c, K.INK)
    with cam.on(c):
        _back_street(c, t)
        _esc_route(c, t)
    for who in ("cracker", "architect"):
        if t >= CLIMB[who][0]:
            _esc_fig(c, who, t, cam)
    with cam.on(c):
        _lid_b(c, t)
    f = 1.0 - clamp((t - T_ESC[0]) / 0.12)                  # out of his red and blue
    if f > 0.0:
        K.fill(c, K.INK, alpha=f)


def _resample(pts, n):
    L = K.poly_len(pts)
    return [K.poly_at(pts, L * i / (n - 1))[0] for i in range(n)]


def _x_strokes(c, t, cam):
    """The two routes, his red and her white, straightening into two strokes crossing over the
    bank (frame px): hers top left to bottom right, his top right to bottom left."""
    m = ease("inout3", clamp((t - T_X[0]) / (T_X[1] - T_X[0])))
    n = 40
    for i, (route, col, ang) in enumerate(((HER_ROUTE, K.PAPER, _DIAG), (HIS_ROUTE, K.RED, math.pi - _DIAG))):
        src = [cam.to_view(p) for p in _resample(route, n)]
        d = (math.cos(ang), math.sin(ang))
        a = (X_CENTRE[0] + d[0] * X_HALF, X_CENTRE[1] + d[1] * X_HALF)     # the route's start ...
        b = (X_CENTRE[0] - d[0] * X_HALF, X_CENTRE[1] - d[1] * X_HALF)     # ... and its end
        if i == 1:
            a, b = b, a
        pts = []
        for j, p in enumerate(src):
            q = (lerp(a[0], b[0], j / (n - 1)), lerp(a[1], b[1], j / (n - 1)))
            pts.append((lerp(p[0], q[0], m), lerp(p[1], q[1], m)))
        bass.line_band(c, pts, col, width=lerp(8.0, 64.0, m), seed=390 + i, alpha=clamp(m * 3.0))


def board_shot(c, t):
    cam = board_cam(t)
    K.fill(c, K.INK)
    dim = 0.55 * ease("inout", clamp((t - T_X[0]) / 0.8))
    with cam.ground(c):
        draw_board(c, t, dim)
        if t >= T_BACK:
            _her_route(c, t)
            _lid(c, t)
            _walkers(c, t)
        _his_car(c, t, cam)
        _cops(c, t)
        _ring(c, t)
    if t >= T_X[0]:
        _x_strokes(c, t, cam)
    f = 1.0 - clamp((t - T_BOARD) / 0.3)                   # out of the headlight's white
    if f > 0.0:
        K.fill(c, K.PAPER, alpha=ease("in", f))


# ============================================================================ his face
def face_shot(c, t):
    """His face in the car's side window, washed red and blue by turns; the frame rolled."""
    K.fill(c, K.INK)
    tt = K.twos(t)
    blue = (tt * 3.0) % 1.0 < 0.5
    wash, other = (K.POLICE, K.RED) if blue else (K.RED, K.POLICE)
    u = clamp((t - T_FACE[0]) / (T_FACE[1] - T_FACE[0]))
    c.save()
    c.translate(540.0, 960.0)
    c.rotate(math.radians(-12.0 + 4.0 * u))
    c.scale(1.0 + 0.06 * u, 1.0 + 0.06 * u)
    c.translate(-540.0, -960.0)
    win = bass.cut_rect(70.0, 560.0, 1010.0, 1360.0, seed=400, amp=1.0)
    bass.fill_polys(c, [bass.cut_rect(30.0, 520.0, 1050.0, 1400.0, seed=401, amp=1.0)], lerp(K.STEEL, K.INK, 0.4))
    bass.fill_polys(c, [win], K.DEEP)
    c.save()
    c.new_path()
    bass.draw.poly(c, win)
    c.clip()
    K.pool(c, (900.0 if blue else 180.0, 700.0), 700.0, 700.0, wash, 0.32, steps=4)
    looks = (-0.8, 0.9, -0.5, 0.95, -0.9)
    s = 1.15
    at = (520.0 + (480.0 - 400.0) * s, 880.0 + (860.0 - 284.0) * s)     # his eye at (520, 880)
    F.knight(c, at, s, look=looks[int(tt * 6.0) % len(looks)], draw=0.0, t=t, field=K.DEEP, rim=wash, back=other,
             smoke=0.5)
    # the light bars' sweep across the glass
    x = lerp(-300.0, 1400.0, (tt * 1.5) % 1.0)
    bass.fill_polys(c, [bass.orient([(x, 520.0), (x + 160.0, 520.0), (x - 80.0, 1400.0), (x - 240.0, 1400.0)], True)],
                    wash, 0.16)
    c.restore()
    c.restore()


# ============================================================================ render
def _headlight_frame(t):
    """The dark headlight in the close shot of the car's nose (frame px)."""
    return NOSE_CAM.to_frame((Bk.CAR_X - Bk.CAR_L / 2.0 + 4.0, -32.0))


INSERTS = (S.Punch(T_COUGH[0], 5, _headlight_frame, 4.5, seed=101),    # the first cough: the dead lamp, close
         S.Flash(T_MATE - 2.0 / 24.0, 2, K.INK))                    # black, then checkmate


def render(f, t, T):
    S.play(f, t, T, render_plain, INSERTS)


def render_plain(f, t, T):
    if t < T_NOSE:
        K.scene_setup(f, K.NAVY)
        with f.screen() as c:
            street_shot(c, t)
        return
    if t < T_BOARD:
        K.scene_setup(f, K.NAVY)
        with f.screen() as c:
            nose_shot(c, t)
        return
    K.scene_setup(f, K.INK)
    with f.screen() as c:
        if T_FACE[0] <= t < T_FACE[1]:
            face_shot(c, t)
        elif T_ESC[0] <= t < T_ESC[1]:
            escape_shot(c, t)
        else:
            board_shot(c, t)


def cues(T):
    out = [Cue(0.0, "the alarm bell ringing hard, high in the alley", gain_db=-10, pan=0.5, dur=T_NOSE),
           Cue(T_RUN, "heavy running footsteps on cobbles, coming in fast from the right", gain_db=-10, pan=0.6,
               dur=0.75),
           Cue(T_RUN + 0.85, "a skidding stop", gain_db=-12, pan=0.4),
           Cue(T_HEAVE[0], "a grunt of effort", gain_db=-14, pan=0.4),
           Cue(T_THROW[1], "two heavy sacks of gold thumped into the back seat: a dull clank", gain_db=-8, pan=0.35),
           Cue(T_SLAM[0], "a car door slammed hard", gain_db=-6, pan=0.3),
           Cue(T_COUGH[0], "a starter motor grinding, the engine coughing twice", gain_db=-9,
               dur=T_LIGHTS - T_COUGH[0]),
           Cue(T_LIGHTS, "the headlight clicks on with a bright swell; the engine catches and roars", gain_db=-7,
               dur=T_LURCH[1] - T_LIGHTS),
           Cue(T_LURCH[0], "tyres squealing as the car lurches off", gain_db=-8, pan=-0.4),
           Cue(T_FLASH[0], "a white whoosh", gain_db=-12),
           Cue(T_SPEED[0], "the engine racing away", gain_db=-14, dur=0.8)]
    for i, tc in enumerate(T_COPS):
        pan = (-0.7, 0.0, 0.7, 0.0)[i]
        out.append(Cue(tc - 0.2, "a police car sliding in: a muted trumpet stab and a siren whoop", gain_db=-7,
                       pan=pan))
    out += [Cue(T_COPS[0] + 0.05, "brakes screeching", gain_db=-11, pan=-0.2),
            Cue(T_COPS[0], "sirens braiding together, rising", gain_db=-13, dur=T.duration - T_COPS[0]),
            Cue(T_MATE, "checkmate: a hard low stab and a choked cymbal", gain_db=-5),
            Cue(T_FACE[0], "a heartbeat thump; his breath catching", gain_db=-10, dur=T_FACE[1] - T_FACE[0]),
            Cue(T_BACK, "cut to the back street: night air, the sirens far off behind the bank; a drip down the shaft",
                gain_db=-22, dur=T_ESC[1] - T_BACK),
            Cue(CLIMB["architect"][2], "an iron clunk: manhole B's lid knocked up off its seat", gain_db=-13, pan=0.25),
            Cue(T_LID[0], "an iron manhole cover dragged aside", gain_db=-12, pan=0.3),
            Cue(T_X[0], "two long strokes of chalk swelling into a held chord", gain_db=-10, dur=T_X[1] - T_X[0]),
            Cue(T_X[1], "the theme's last phrase, resolving", gain_db=-12, dur=T.duration - T_X[1])]
    for who in ("architect", "cracker"):                    # up the rungs, then away west on the cobbles
        for tt in rung_times(who):
            out.append(Cue(tt, "a boot on an iron rung (a soft clank in the shaft)", gain_db=-23 if who == "architect" else -21,
                           pan=0.25))
        for tt, x in esc_steps(who):
            cam = esc_cam(tt) if tt < T_ESC[1] else None
            pan = clamp((cam.to_frame((x, 0.0))[0] / K.W) * 2.0 - 1.0, -0.8, 0.8) if cam else -0.3
            out.append(Cue(tt, f"a soft footstep on the cobbles ({'hers' if who == 'architect' else 'the Cracker'})",
                           gain_db=-19 if who == "architect" else -18, pan=pan))
    return out
