"""s10 CHECKMATE (148-166). The Knight gets away, the alarm calls the police, and the city closes
on him like a chessboard.
  The front street at night, the alarm bell ringing red high in the alley. The Knight bursts
    round the car's tail with two heavy sacks, heaves them in through the open rear door and
    slams it. Close on the car's nose: the engine coughs, the headlight flares, the car
    lurches off and the light fills the frame.
  The city from above: its blocks are the squares of a chessboard, with the blueprint of the
    bank in the middle. His car (red-edged) lurches out at the end of his red trail. The bell
    by the bank's side door rings red, and its rings run out over the city, one per beat. Four
    police cars wait dark down the four streets round him; as the first ring reaches each, its
    bar switches on, one per beat (W, N, E, S: exactly as she chalked them in Plan B), and the
    first one's lights, dead ahead, stop him. They slide in nose first like rooks, one per
    beat. A red marker ring closes round him: checkmate. The camera rolls (his panic).
  His face in the car window, washed red and blue, eyes darting.
  The street again, boxed in: a police car nose to nose with his, one nose to tail, the third's
    bar flashing over his roof from the alley, every lamp on him, the bell still ringing above.
    He shoves the door open and climbs out with a sack, looks east, looks west, lets the sack
    go (the gold spills on the road) and puts his hands up in the light.
  The pull-back: manhole B's lid slides off, two small chalk figures climb out and walk west
    along the back street, her white route lighting behind them. Then his red route and her
    white one straighten into two strokes crossing over the bank: an X.
"""
import math
from functools import lru_cache

import cairo

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
T_SPEED = (3.15, 3.55)           # his car lurches forward along the front street ...
T_BRAKE = 4.55                   # ... and stops dead: lights ahead (the first police car's)
T_RINGS = 3.0                    # the bell's rings run out over the city, one per beat ...
RING_V = 400.0                   # ... this fast (plan px / s)
RING_R0 = 30.0
RING_LIFE = 3.4
T_WAKE = (4.5, 5.0, 5.5, 6.0)    # as the first ring reaches each police car, its bar switches on ...
T_COPS = (6.0, 6.5, 7.0, 7.5)    # ... and it slides in nose first, one per beat
T_MATE = 8.0                     # the red ring: checkmate
T_ROLL = (8.0, 8.42)             # the camera rolls: his panic
T_FACE = (8.42, 9.2)
T_ARREST = 9.2                   # the street again: boxed in, hands up
T_BACK = 12.92                   # the pull-back
T_LID = (13.67, 13.97)           # manhole B's lid slides off
T_UP = (13.92, 14.17)            # she climbs out; he follows
T_LENS = (13.57, 15.57)          # a lens on manhole B: the two climbing out
T_X = (15.72, 16.92)             # the routes straighten into the X
T_END = 18.0
CAR_HOME = P.CAR
CAR_STOP = (P.CAR[0] - 30.0, P.CAR[1])
STREETS_X = tuple(120.0 + 837.0 * k for k in range(-3, 5))     # the north-south streets (centres)
STREETS_Y = tuple(280.0 + 1120.0 * k for k in range(-3, 5))    # the east-west streets
STREET_W = 100.0
CROSS_X = STREETS_X[4]           # the cross street at his car's tail (the alley's): N and S come down it
# each police car's rest, nose in, and its heading (degrees): W, N, E, S as in Plan B
COP_REST = (((CAR_STOP[0] - 120.0, CAR_STOP[1]), 0.0), ((CROSS_X, CAR_STOP[1] - 94.0), 90.0),
            ((CAR_STOP[0] + 120.0, CAR_STOP[1]), 180.0), ((CROSS_X, CAR_STOP[1] + 94.0), 270.0))
MATE_C = (CAR_STOP[0] + 15.0, CAR_STOP[1])     # the box's middle
BOARD_KEYS = ((T_BOARD, (930.0, 1240.0, 1.0, 0.0)), (3.1, (930.0, 1240.0, 1.0, 0.0)),
              (4.4, (1165.0, 1265.0, 0.6, 0.0)), (6.0, (1150.0, 1290.0, 0.58, 0.0)),
              (7.9, (MATE_C[0], MATE_C[1], 1.0, 0.0)), (T_FACE[0], (MATE_C[0], MATE_C[1], 1.16, -10.0)))
BACK_KEYS = ((T_BACK, (MATE_C[0], MATE_C[1], 1.2, 0.0)), (T_BACK + 1.3, (560.0, 920.0, 0.6, 0.0)),
             (T_BACK + 4.8, (548.0, 880.0, 0.56, 0.0)))
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
    """His car's centre on the plan: the lurch forward, a creep, and the dead stop at the lights
    ahead (its nose dips)."""
    u = ease("inout", clamp((t - T_SPEED[0]) / (T_SPEED[1] - T_SPEED[0])))
    x = lerp(CAR_HOME[0], CAR_STOP[0] + 10.0, u)
    x -= 10.0 * ease("in", clamp((t - T_SPEED[1]) / (T_BRAKE - T_SPEED[1])))
    a = clamp((t - T_BRAKE) / 0.3)
    if 0.0 < a < 1.0:
        x -= 8.0 * math.sin(math.pi * a) * (1.0 - a)
    return (x, CAR_HOME[1])


def _park(i):
    """Where police car i waits, dark, down its street: as far from the bell as the first ring
    has spread by T_WAKE[i]."""
    (rx, ry), ang = COP_REST[i]
    d = RING_R0 + RING_V * (T_WAKE[i] - T_RINGS)
    back = (-math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
    ox, oy = rx - P.BELL_AT[0], ry - P.BELL_AT[1]
    b = ox * back[0] + oy * back[1]
    s = -b + math.sqrt(b * b - (ox * ox + oy * oy - d * d))
    return (rx + back[0] * s, ry + back[1] * s)


PARK = tuple(_park(i) for i in range(4))


def cop_at(i, t):
    """(centre, heading degrees, how far in 0..1) of police car i: dark at PARK[i]; from a beat
    after its bar switches on, down its street to its rest, rocking on its nose as it stops."""
    rest, ang = COP_REST[i]
    t0 = T_WAKE[i] + 0.12
    u = clamp((t - t0) / (T_COPS[i] - t0))
    g = ease("inout3", u)
    p = (lerp(PARK[i][0], rest[0], g), lerp(PARK[i][1], rest[1], g))
    a = clamp((t - T_COPS[i]) / 0.3)
    if 0.0 < a < 1.0:
        k = 10.0 * math.sin(math.pi * a) * (1.0 - a)
        p = (p[0] + math.cos(math.radians(ang)) * k, p[1] + math.sin(math.radians(ang)) * k)
    return p, ang, u


def _alarm(c, t):
    """The bell by the side door, ringing on the board: its rings run out over the city, one per
    beat (where the first ring has got to, the alarm has been heard). They fade at checkmate."""
    fade = 1.0 - clamp((t - (T_MATE - 0.1)) / 0.3)
    for k in range(int((t - T_RINGS) / K.BEAT) + 1 if fade > 0.0 else 0):
        age = t - (T_RINGS + k * K.BEAT)
        if not 0.0 <= age < RING_LIFE:
            continue
        a = age / RING_LIFE
        bass.ring(c, P.BELL_AT, RING_R0 + RING_V * age, 12.0 * (1.0 - 0.6 * a), K.RED, seed=2300 + k,
                  alpha=0.85 * (1.0 - a) * fade)
    K.bell(c, P.BELL_AT, P.BELL_S * 1.25, K.RED, seed=2237, ring=18.0 * math.sin(2.0 * math.pi * 9.0 * t))


def _his_car(c, t, cam):
    p = car_at(t)
    K.route(c, HIS_ROUTE[:-1] + [p], 1.0, K.RED, r=6.5, gap=22.0, head=0.0, seed=5)
    if t >= T_SPEED[0] - 0.1:                              # the headlights, west
        K.cone(c, (p[0] - 52.0, p[1]), 180.0, 18.0, 300.0, K.PAPER, alpha=0.14, seed=9)
    K.car(c, p, 180.0, 0.9, K.INK, K.RED, ew=5.0)


def _bar_off(c, p, ang, s):
    """A police car's light bar, dark."""
    c.save()
    c.translate(*p)
    c.rotate(math.radians(ang))
    c.scale(s, s)
    bass.fill_polys(c, [bass.cut_rect(-6.0, -20.0, 6.0, 20.0, seed=85, amp=0.3)], lerp(K.INK, K.STEEL, 0.4))
    c.restore()


def _cops(c, t):
    """The four police cars: dark down their streets; the bar on (with a pop and a flash of rings)
    as the alarm reaches each; then sliding in nose first, like rooks, streaks behind."""
    for i in range(4):
        p, ang, u = cop_at(i, t)
        if 0.0 < u < 1.0:                                  # streaks behind it as it slides in
            q, _, _ = cop_at(i, t - 1.0 / 24.0)
            L = min(420.0, 0.2 * 24.0 * math.hypot(p[0] - q[0], p[1] - q[1]))
            back = (-math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
            for j in range(3 if L > 8.0 else 0):
                off = (j - 1) * 16.0
                n = (-back[1] * off, back[0] * off)
                a = (p[0] + back[0] * 70.0 + n[0], p[1] + back[1] * 70.0 + n[1])
                b = (a[0] + back[0] * L, a[1] + back[1] * L)
                K.chalk_line(c, [a, b], 1.0, 4.0, K.PAPER, seed=70 + i * 3 + j, alpha=0.45)
        if t < T_WAKE[i]:
            K.car(c, p, ang, 0.9, K.INK, K.STEEL, ew=3.5)
            _bar_off(c, p, ang, 0.9)
            continue
        w = clamp((t - T_WAKE[i]) / 0.3)
        col = K.POLICE if i % 2 == 0 else K.RED
        if w < 1.0:                                        # the bar switching on: a flash
            K.dot(c, p, 100.0 * (0.5 + 0.5 * w), col, seed=86 + i, alpha=0.55 * (1.0 - w))
        K.car(c, p, ang, 0.9, K.INK, K.PAPER, ew=4.0)
        K.police_lights(c, p, ang, t, s=0.9 * (1.0 + 0.8 * math.sin(math.pi * w)), beams=True, seed=80 + i)
        K.ripple(c, p, t, T_WAKE[i], col, n=2, every=0.14, life=0.55, r0=30.0, r1=240.0, width=10.0)
        if u >= 1.0:
            K.ripple(c, p, t, T_COPS[i], col, n=2, every=0.14, life=0.5, r0=20.0, r1=120.0, width=5.0)


def _ring(c, t):
    u = ease("out3", clamp((t - T_MATE) / 0.3))
    if u > 0.0:
        K.marker_ring(c, MATE_C, 212.0, 172.0, u, K.RED, width=16.0, seed=90)
    if t >= T_MATE + 0.3:
        K.ripple(c, MATE_C, t, T_MATE + 0.3, K.RED, n=2, every=0.2, life=0.7, r0=190.0, r1=360.0, width=6.0)


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


def _lens(c, t, cam):
    """A lens on manhole B while they climb out and walk off west (the board, closer)."""
    u = clamp((t - T_LENS[0]) / 0.3) * (1.0 - clamp((t - (T_LENS[1] - 0.25)) / 0.25))
    if u <= 0.0:
        return
    anchor = cam.to_view(P.MANHOLE_B)
    centre = (300.0, 330.0)

    def inside(cc):
        p, _ = walker_at(0, t)
        lx = min(P.MANHOLE_B[0] - 50.0, p[0] + 10.0) if p is not None else P.MANHOLE_B[0] - 50.0
        lc = P.PlanCam(lx, P.MANHOLE_B[1], 2.3, 90.0, 0.0, fx=centre[0], fy=centre[1])
        K.fill(cc, K.INK)
        with lc.ground(cc):
            draw_board(cc, t)
            _her_route(cc, t)
            _lid(cc, t)
            _walkers(cc, t)
    K.callout(c, anchor, centre, 210.0, inside, u=u, color=K.PAPER, ring_w=9.0, dot_r=8.0, line_w=4.0, seed=95)


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
        _alarm(c, t)
        _his_car(c, t, cam)
        _cops(c, t)
        _ring(c, t)
    if T_LENS[0] <= t < T_LENS[1]:
        _lens(c, t, cam)
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


# ============================================================================ the arrest (the street again)
T_DOOR = (9.62, 9.8)             # he shoves the driver's door open ...
T_CLIMB = (9.8, 10.3)            # ... and climbs out with a sack, into the light
T_LOOK_E = 10.5                  # a look east, at the car behind ...
T_LOOK_W = 10.82                 # ... and west again, at the one in front
T_DROP = 11.0                    # he lets the sack go: it thumps down and the gold spills
T_HANDS = (11.36, 11.72)         # hands up
HIS_X = Bk.CAR_X - 30.0          # his car, stopped (the board's lurch)
COP_W_X = HIS_X - Bk.CAR_L - 12.0      # a police car nose to his nose ...
COP_E_X = HIS_X + Bk.CAR_L + 12.0      # ... one nose to his tail ...
COP_N_X = CROSS_X                      # ... and one come down the alley, head on behind his car
T_CLOSE = 11.3                   # cut in close as the sack topples: the hands go up in the medium shot
ARREST_CAM = (Bk.Cam(HIS_X, -196.0, 1.8), Bk.Cam(HIS_X - 8.0, -172.0, 2.05))
SEAT = (HIS_X + 10.0, 210.0)     # in the driver's seat: his pelvis (set x), how far it sinks (fig units)
OUT_X = HIS_X - 16.0             # out on the road
CLOSE_CAM = (Bk.Cam(OUT_X - 4.0, -140.0, 3.2), Bk.Cam(OUT_X - 4.0, -136.0, 3.6))
_X0 = HIS_X - Bk.CAR_L / 2.0     # his car's nose
WINDOW = [(_X0 + 98.0, -84.0), (_X0 + 116.0, -90.0), (_X0 + 150.0, -90.0), (_X0 + 150.0, -60.0), (_X0 + 84.0, -60.0)]
DOOR_HOLE = [(_X0 + 84.0, -60.0), (_X0 + 98.0, -84.0), (_X0 + 116.0, -90.0), (_X0 + 150.0, -90.0),
             (_X0 + 150.0, -20.0), (_X0 + 84.0, -20.0)]


def arrest_cam(t):
    if t < T_CLOSE:
        return Bk.Cam.lerp(*ARREST_CAM, ease("inout", clamp((t - T_ARREST) / (T_CLOSE - T_ARREST))))
    return Bk.Cam.lerp(*CLOSE_CAM, ease("out", clamp((t - T_CLOSE) / (T_BACK - T_CLOSE))))


def arrest_knight(t):
    """(state, pose, x, facing, sack held) of the Knight in the arrest: sunk in the driver's seat,
    his head darting; out of the door with a sack, ducking under the roof; a look east and west;
    the sack let go; hands up (trembling)."""
    st = C.standing("knight")
    climb = ease("inout", clamp((t - T_CLIMB[0]) / (T_CLIMB[1] - T_CLIMB[0])))
    if t < T_CLIMB[0]:
        facing = (-1, 1, -1, -1, 1)[int((t - T_ARREST) / 0.17) % 5]
    else:
        facing = 1 if T_LOOK_E <= t < T_LOOK_W else -1
    hands = ease("outback", clamp((t - T_HANDS[0]) / (T_HANDS[1] - T_HANDS[0])))
    shake = 1.5 * math.sin(2.0 * math.pi * 7.0 * t) * clamp((t - T_HANDS[1]) / 0.2)
    look = 8.0 if T_LOOK_E - 0.1 <= t < T_LOOK_W + 0.2 else 0.0
    lean = 4.0 + 10.0 * (1.0 - climb) + 22.0 * math.sin(math.pi * climb)
    pose = pd.Pose(lean=lerp(lean, -4.0, hands), head=lerp(-6.0 + look, 8.0, hands), crouch=SEAT[1] * (1.0 - climb))
    let_go = ease("out", clamp((t - T_DROP) / 0.2))
    pose.arms["near"] = ("ang", lerp(8.0 + 8.0 * let_go, 156.0 + shake, hands), lerp(12.0, 16.0, hands))
    pose.arms["far"] = ("ang", lerp(lerp(64.0, 12.0, climb), 178.0 - shake, hands),
                        lerp(lerp(40.0, 16.0, climb), 2.0, hands))
    held = t < T_DROP
    if held:
        pose.hold = {"near": Bk.hold_sack(1.0, seed=43, floor=0.0)}
    return st, pose, lerp(SEAT[0], OUT_X, climb), facing, held


def _draw_knight(c, st, pose, x, facing, cam):
    """Him in the crossed lamps: lit white from the west, red (his own) from the east."""
    w = 5.0 / cam.zoom
    C.draw(c, "knight", st, pose, x, 0.0, Bk.FIG_S, facing, bg=K.NAVY, rim=K.PAPER, rim_w=w, light=(-1.0, -0.25))
    return C.draw(c, "knight", st, pose, x, 0.0, Bk.FIG_S, facing, bg=K.NAVY, rim=K.RED, rim_w=w, light=(1.0, -0.25))


def _beacon(c, p, t, seed, s=1.0):
    """A police car's roof light seen side on (set px, p the middle of its base): the red and blue
    halves flashing in turn, and their two turning beams sweeping the street."""
    blue_on = (t * 3.0 + hash01(seed, 9)) % 1.0 < 0.5
    rot = math.radians((t * 260.0 + 97.0 * seed) % 360.0)
    top = (p[0], p[1] - 6.0 * s)
    for col, off in ((K.POLICE, 0.0), (K.RED, math.pi)):
        a = rot + off
        L = 560.0 * abs(math.cos(a)) * s
        if L > 20.0:
            d = 1.0 if math.cos(a) > 0.0 else -1.0
            bass.fill_polys(c, [bass.orient([top, (top[0] + d * L, top[1] - 0.18 * L), (top[0] + d * L, top[1] + 0.18 * L)],
                                            True)], col, 0.14)
        if math.sin(a) < -0.85:                            # turned toward us: a flare
            Bk.disc(c, top, 46.0 * s, col, seed=seed + 3, n=24, alpha=0.3)
    Bk.rect(c, (p[0] - 14.0 * s, p[1] - 12.0 * s, p[0], p[1]), K.RED, seed=seed + 1, amp=0.3,
            alpha=0.45 if blue_on else 1.0)
    Bk.rect(c, (p[0], p[1] - 12.0 * s, p[0] + 14.0 * s, p[1]), K.POLICE, seed=seed + 2, amp=0.3,
            alpha=1.0 if blue_on else 0.45)
    Bk.disc(c, (p[0] + (7.0 if blue_on else -7.0) * s, top[1]), 24.0 * s, K.POLICE if blue_on else K.RED,
            seed=seed + 4, n=20, alpha=0.3)


def _cop_side(c, x, t, nose, seed):
    """A police car side on (set px), nose -1 west / +1 east: INK edged white, a white band along
    its doors, its headlight full on and thrown along the street, its bar flashing on the roof."""
    rim, shell, wins = Bk._car_polys()
    x0, x1 = -Bk.CAR_L / 2.0, Bk.CAR_L / 2.0
    c.save()
    c.translate(x, 0.0)
    c.scale(-nose, 1.0)                                    # the polygons are drawn nose west
    reach = 430.0
    bass.fill_polys(c, [bass.orient([(x0 + 4.0, -38.0), (x0 + 4.0, -26.0), (x0 - reach, 8.0), (x0 - reach, -80.0)],
                                    True)], K.PAPER, 0.08)
    bass.fill_polys(c, [bass.orient([(x0 + 4.0, -36.0), (x0 + 4.0, -28.0), (x0 - reach * 0.7, -10.0),
                                     (x0 - reach * 0.7, -52.0)], True)], K.PAPER, 0.08)
    bass.fill_polys(c, [rim], K.PAPER)
    bass.fill_polys(c, [shell], K.INK)
    bass.fill_polys(c, wins, Bk.GLASS)
    Bk.band(c, (x0 + 84.0, -46.0), (x1 - 34.0, -46.0), 9.0, K.PAPER, seed=seed)
    for i, wx in enumerate((x0 + 52.0, x1 - 50.0)):
        Bk.disc(c, (wx, -18.0), 20.0, K.INK, seed=seed + 1 + i, n=28)
        Bk.disc(c, (wx, -18.0), 8.0, K.STEEL, seed=seed + 3 + i, n=16)
    Bk.disc(c, (x0 + 4.0, -32.0), 7.0, K.PAPER, seed=seed + 5, n=14)
    Bk.disc(c, (x0 + 4.0, -32.0), 24.0, K.PAPER, seed=seed + 6, n=24, alpha=0.3)
    c.restore()
    _beacon(c, (x - nose * 15.0, -94.0), t, seed + 7)


def _cop_head_on(c, x, t):
    """The police car come down the alley, head on behind his car: hidden by it but for its roof
    and its bar."""
    body = [(x - 56.0, -10.0), (x - 56.0, -50.0), (x - 46.0, -64.0), (x - 38.0, -100.0), (x + 38.0, -100.0),
            (x + 46.0, -64.0), (x + 56.0, -50.0), (x + 56.0, -10.0)]
    Bk.poly(c, [(px, py - 3.0) for px, py in body], K.STEEL, seed=651)
    Bk.poly(c, body, K.INK, seed=652)
    Bk.poly(c, [(x - 33.0, -94.0), (x + 33.0, -94.0), (x + 40.0, -68.0), (x - 40.0, -68.0)], Bk.GLASS, seed=653)
    _beacon(c, (x, -100.0), t, 655)


def _driver_door(c, g):
    """The driver's door swinging open toward us on its front hinge: side on, it narrows to the
    hinge, its window going with it."""
    h = _X0 + 82.0
    if g >= 1.0:
        Bk.band(c, (h, -92.0), (h, -16.0), 5.0, K.INK, seed=662)
        return

    def sq(p):
        return (h + (p[0] - h) * (1.0 - g), p[1])
    Bk.poly(c, [sq(p) for p in [(h, -92.0), (_X0 + 152.0, -92.0), (_X0 + 152.0, -16.0), (h, -16.0)]], K.INK, seed=663,
            amp=0.2)
    Bk.poly(c, [sq(p) for p in WINDOW], Bk.GLASS, seed=664, amp=0.2)


@lru_cache(maxsize=1)
def _drop_from():
    """Where the sack hangs from his fist as he lets it go (set px)."""
    st, pose, x, facing, _ = arrest_knight(T_DROP - 1e-3)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
    return C.draw(cairo.Context(surf), "knight", st, pose, x, 0.0, Bk.FIG_S, facing, rim=False)["hand_near"]


def _dropped(c, t):
    """The sack let go: it drops, thumps down, topples west, and two gold bars slide out of its
    mouth onto the road, glinting in the lamps."""
    if t < T_DROP:
        return
    hx, hy = _drop_from()
    foot = min(-0.5, hy + 44.0)                            # the sack's foot as it hung
    k = t - T_DROP
    t_land = math.sqrt(2.0 * -foot / Bk.G_DRIP)
    y = min(0.0, foot + 0.5 * Bk.G_DRIP * k * k)
    tip = ease("outback", clamp((k - t_land) / 0.22))
    c.save()
    c.translate(hx - 20.0, y)
    c.rotate(math.radians(-84.0 * tip))
    Bk.sack(c, (20.0, 0.0), 1.0, s=1.0, color=K.INK, rim=K.RED, seed=43)
    c.restore()
    mouth = (hx - 20.0 - 46.0 * tip, -20.0 * tip + y)
    for j in range(2):
        u = ease("out3", clamp((k - t_land - 0.12 - 0.08 * j) / 0.3))
        if u <= 0.0:
            continue
        rest = (hx - 78.0 - 30.0 * j, 0.0)
        p = (lerp(mouth[0], rest[0], u), lerp(mouth[1], rest[1], u))
        Bk.bar(c, p, 0.9, angle=lerp(-30.0, -6.0 + 10.0 * j, u))
        g = clamp((k - t_land - 0.4 - 0.15 * j) / 0.35)
        if 0.0 < g < 1.0:
            K.twinkle(c, (p[0] + 4.0, p[1] - 8.0), 18.0, K.PAPER, u=math.sin(math.pi * g), rot=15.0 * j)


def arrest_shot(c, t):
    """The street, boxed in (north-looking): police cars nose to nose and nose to tail with his, a
    third head on in the alley behind it, every lamp and bar on him; the bell ringing above. He
    climbs out, looks round, lets the sack go and puts his hands up."""
    tt = K.twos(t)
    cam = arrest_cam(t)
    Bk.front_street(c, cam, t, bell=1.0, lamp=1.0, car_on=False)
    _bell_ripples(c, cam, t)
    st, pose, x, facing, held = arrest_knight(tt)
    g = ease("out", clamp((tt - T_DOOR[0]) / (T_DOOR[1] - T_DOOR[0])))
    free = ease("in", clamp((tt - T_CLIMB[0]) / 0.15))     # his clip opening out as he climbs out
    with cam.on(c):
        _cop_head_on(c, COP_N_X, tt)
        Bk.car(c, t, headlights=0.7, x=HIS_X)
        for k in (-1, 1):                                  # the alley car's lamps, glaring round his tail
            Bk.disc(c, (COP_N_X + 38.0 * k, -38.0), 54.0, K.PAPER, seed=660 + k, n=28, alpha=0.1)
        if g > 0.0:                                        # the dark of the car, the door open
            Bk.poly(c, DOOR_HOLE, K.DEEP, seed=661, amp=0.2)
        if free < 1.0:                                     # in the seat: through the glass, then the open door
            c.save()
            c.new_path()
            if free <= 0.0:
                bass.draw.poly(c, WINDOW if g <= 0.0 else DOOR_HOLE)
            else:
                r = (lerp(_X0 + 84.0, _X0 - 600.0, free), lerp(-90.0, -900.0, free), lerp(_X0 + 150.0, _X0 + 800.0, free),
                     lerp(-20.0, 400.0, free))
                c.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
            c.clip()
            _draw_knight(c, st, pose, x, facing, cam)
            c.restore()
        if g > 0.0:
            _driver_door(c, g)
        _cop_side(c, COP_W_X, tt, 1, 670)
        _cop_side(c, COP_E_X, tt, -1, 680)
        if free >= 1.0:
            _draw_knight(c, st, pose, x, facing, cam)
        _dropped(c, tt)
    blue = (tt * 3.0) % 1.0 < 0.5                          # the bars' light over everything, by turns
    K.pool(c, (160.0, 900.0) if blue else (920.0, 900.0), 640.0, 1000.0, K.POLICE, 0.07, steps=3)
    K.pool(c, (920.0, 900.0) if blue else (160.0, 900.0), 640.0, 1000.0, K.RED, 0.06, steps=3)
    K.pool(c, (540.0, 2250.0), 1000.0, 700.0, K.RED if blue else K.POLICE, 0.05, steps=3)   # the fourth, behind us


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
    if T_ARREST <= t < T_BACK:
        K.scene_setup(f, K.NAVY)
        with f.screen() as c:
            arrest_shot(c, t)
        return
    K.scene_setup(f, K.INK)
    with f.screen() as c:
        if T_FACE[0] <= t < T_FACE[1]:
            face_shot(c, t)
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
    out += [Cue(T_RINGS, "the alarm bell ringing on over the city, every ring rolling outward", gain_db=-12,
                dur=T_MATE - T_RINGS),
            Cue(T_BRAKE, "brakes screeching: his car stops dead", gain_db=-10, pan=-0.2)]
    for i, (tw, tc) in enumerate(zip(T_WAKE, T_COPS)):
        pan = (-0.7, 0.0, 0.7, 0.0)[i]
        out.append(Cue(tw, "a police car's lights switching on: a clunk and a siren whoop", gain_db=-9, pan=pan))
        out.append(Cue(tc - 0.2, "a police car sliding in: a muted trumpet stab and tyres", gain_db=-7, pan=pan))
    out += [Cue(T_WAKE[0], "sirens braiding together, rising", gain_db=-13, dur=T_BACK - T_WAKE[0]),
            Cue(T_MATE, "checkmate: a hard low stab and a choked cymbal", gain_db=-5),
            Cue(T_FACE[0], "a heartbeat thump; his breath catching", gain_db=-10, dur=T_FACE[1] - T_FACE[0]),
            Cue(T_ARREST, "the alarm bell ringing above the street; police engines idling round him", gain_db=-12,
                dur=T_BACK - T_ARREST),
            Cue(T_DOOR[0], "a car door shoved open", gain_db=-9, pan=-0.1),
            Cue(T_CLIMB[0] + 0.3, "a heavy step onto the cobbles", gain_db=-13),
            Cue(T_LOOK_E, "a sharp breath", gain_db=-15, pan=0.2),
            Cue(T_DROP + 0.12, "a heavy sack of gold thumps onto the cobbles; two bars clink out", gain_db=-8),
            Cue(T_HANDS[0], "his coat rustling as his hands go up; a held low string note", gain_db=-12,
                dur=T_BACK - T_HANDS[0]),
            Cue(T_LID[0], "an iron manhole cover dragged aside", gain_db=-12, pan=-0.2),
            Cue(T_UP[0] + 0.3, "two pairs of soft footsteps walking away on the cobbles", gain_db=-17, pan=-0.3,
                dur=T_X[0] - T_UP[0]),
            Cue(T_X[0], "two long strokes of chalk swelling into a held chord", gain_db=-10, dur=T_X[1] - T_X[0]),
            Cue(T_X[1], "the theme's last phrase, resolving", gain_db=-12, dur=T.duration - T_X[1])]
    return out
