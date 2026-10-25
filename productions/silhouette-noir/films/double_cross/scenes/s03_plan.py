"""s03 PLAN (24-40). Her chalk draws Plan A, and the three pieces hop along it in file, landing
on the beat:
  (1) down manhole A, along the sewer and up the branch to the store-room hatch;
  (2) through the store room to the corridor. The Cracker's old hand sets the guard there (a
      black pawn); she sweeps his light out from it, and a timing ring goes round him;
  (3) the pieces cross the lit corridor one at a time, each in a dark gap of the sweep;
  (4) the bishop goes to the vault door. A lens shows the dial turned right, left, right; the
      door swings open, the route runs in to the X, and the queen and bishop go in.
Then the Knight's own red hand lifts his piece off the route and slams it down out by the
street. Everyone looks there: the others jump, and the vault door claps shut on them (an omen).
In that same instant her hand, lifting away from the vault, touches the sewer line under it and
leaves a dot (the plant, never pointed at; s09 rewinds to this frame).
  (5) She draws the way out along the street to him, his car, and a little bell on the side
      door.
The plan is done. The camera starts to tilt down into it, and s04 carries on the move from
P.HANDOFF_34.
"""
import math

from engine import bass
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross import faces as F
from films.double_cross import kit as K
from films.double_cross import plan as P
from films.double_cross.scenes.s02_crew import B_AT, N_AT, PIECE_H, Q_AT

# ---------------------------------------------------------------------------- beats
T_CHEVRON = 0.5                 # tap: the 'down here' chevron on manhole A
# her chalk along the way in: (t0, t1, s0, s1) along P.ROUTE_IN
DRAW_IN = ((1.0, 2.6, 0.0, 450.0), (2.6, 3.6, 450.0, 735.0), (5.5, 6.3, 735.0, 990.0), (8.05, 8.4, 990.0, None))
DRAW_OUT = (11.5, 12.4)         # (5): manhole A along the street to the car (P.ROUTE_OUT[6:])
NUMERALS = (("n1", 0.75), ("n2", 2.7), ("n3", 5.5), ("n4", 5.95), ("n5", 12.0))
T_PAWN = 4.5                    # the Cracker sets the guard on his post (clack)
T_CONE = (5.0, 5.3)             # she sweeps his light out from the pawn
T_RING = (5.2, 6.0)             # the timing ring round him
SWEEP_T0 = 5.0                  # the light swings 32 degrees each way, a full swing per 2 s:
SWEEP_AMP = 32.0                # dark at the crossing on 6.5, 7.5, 8.5 ... (the gaps)
T_SETTLE = (13.4, 15.0)         # the plan is done: the light settles on the corridor
T_DIAL = 6.85                   # the dial is chalked at the vault door
T_LENS = (7.0, 8.06)            # a lens on the dial
TURNS = ((7.12, 1.0, 210.0), (7.37, -1.0, 300.0), (7.62, 1.0, 150.0))   # right, left, right
T_CLICK = 8.0                   # clunk: the door swings open
T_X = 8.4                       # the route reaches the X
T_GRAB = 10.2                   # the red hand snatches the knight off the route
T_THUD = 10.75                  # ... and slams it down by the street; the vault door claps shut;
T_DOT = T_THUD                  # her chalk touches the sewer line under the vault: the dot
T_MURMUR = (0.1, 10.7)          # the briefing, murmured over the plan (no words), up to his slam
T_CAR = 12.45
T_BELL = 13.0
T_TILT = 14.0                   # the camera begins the tilt down (s04 continues it)

HOP = 0.3                       # a hop lands on its beat
D1 = (540.0, 782.0)             # at the vault door, on the dial
D2 = (540.0, 842.0)             # the corridor's mouth, just out of the light
QUEEN_IN, BISHOP_IN, KNIGHT_CAR = (p for kind, p, *_ in P.PIECES_A if kind != "pawn")
COLOURS = {kind: (col, edge, fc) for kind, _, col, edge, fc in P.PIECES_A}


def _r(s):
    return K.poly_at(P.ROUTE_IN, s)[0]


# where each piece lands, and when: they move up in file, one hop a beat
HOPS = {
    "bishop": ((0.0, B_AT), (1.5, _r(120)), (2.0, _r(240)), (2.5, _r(360)), (3.0, _r(480)), (3.5, _r(600)),
               (4.0, _r(715)), (6.5, D2), (7.0, D1), (8.5, BISHOP_IN)),
    "queen": ((0.0, Q_AT), (1.5, _r(56)), (2.0, _r(176)), (2.5, _r(296)), (3.0, _r(416)), (3.5, _r(536)),
              (4.0, _r(651)), (7.0, _r(715)), (7.5, D2), (8.5, D1), (9.0, QUEEN_IN)),
    "knight": ((0.0, N_AT), (2.0, _r(112)), (2.5, _r(232)), (3.0, _r(352)), (3.5, _r(472)), (4.0, _r(587)),
               (7.0, _r(651)), (8.0, _r(715)), (8.5, D2), (9.5, D1)),
}

# the camera: one glide over the plan through these, ending on the tilt into s04
CAM_KEYS = ((0.0, (305.0, 1345.0, 2.4, 64.0, -10.0)),
            (2.6, (410.0, 1200.0, 2.0, 68.0, -9.0)),
            (4.2, (390.0, 1010.0, 1.8, 70.0, -7.0)),
            (6.5, (480.0, 860.0, 1.7, 72.0, -6.0)),
            (8.4, (500.0, 740.0, 1.68, 72.0, -6.0)),
            (10.1, (610.0, 1010.0, 1.12, 72.0, -6.0)),
            (11.6, (590.0, 1230.0, 1.12, 72.0, -6.0)),
            (T_TILT, (556.0, 1090.0, 1.04, 72.0, -6.0)),
            (16.0, P.HANDOFF_34.tuple()[:5]))
END_RATE = (2.0, 30.0, 0.055, -15.0, 0.0)   # still moving at the cut: phi falling 15 deg/s

LENS_C = (868.0, 520.0)
LENS_R = 150.0
LAMP_H = 700.0                   # the lamp's height over the table (plan px), for the hands' shadows


def motion_blur(t, T):
    return 1


# ============================================================================ the camera
def _hermite(keys, t, end_rate):
    ts = [k[0] for k in keys]
    ps = [k[1] for k in keys]
    n = len(keys)

    def tangent(i):
        if i == 0:
            return tuple(0.5 * (b - a) / (ts[1] - ts[0]) for a, b in zip(ps[0], ps[1]))
        if i == n - 1:
            return end_rate
        return tuple((b - a) / (ts[i + 1] - ts[i - 1]) for a, b in zip(ps[i - 1], ps[i + 1]))

    t = clamp(t, ts[0], ts[-1])
    i = max(j for j in range(n - 1) if ts[j] <= t)
    dt = ts[i + 1] - ts[i]
    u = (t - ts[i]) / dt
    h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    return tuple(h00 * a + h10 * dt * ma + h01 * b + h11 * dt * mb
                 for a, b, ma, mb in zip(ps[i], ps[i + 1], tangent(i), tangent(i + 1)))


def cam_at(t):
    cx, cy, zoom, phi, yaw = _hermite(CAM_KEYS, t, END_RATE)
    if T_THUD <= t < T_THUD + 0.35:                     # the slam jolts the table
        a = (1.0 - (t - T_THUD) / 0.35) ** 2
        cx, cy = cx + 5.0 * a * math.sin(t * 90.0), cy + 8.0 * a * math.sin(t * 77.0)
    return P.PlanCam(cx, cy, zoom, phi, yaw)


# ============================================================================ the chalk
def _drawn(t, segs, total):
    s = 0.0
    for t0, t1, s0, s1 in segs:
        s1 = total if s1 is None else s1
        if t >= t0:
            s = lerp(s0, s1, ease("inout", clamp((t - t0) / (t1 - t0))) if t < t1 else 1.0)
    return s


def s_in(t):
    return _drawn(t, DRAW_IN, P.route_len(P.ROUTE_IN))


OUT_ROUTE = P.ROUTE_OUT[6:]


def s_out(t):
    return _drawn(t, ((DRAW_OUT[0], DRAW_OUT[1], 0.0, None),), P.route_len(OUT_ROUTE))


def sweep(t):
    """The guard's light: its angle (degrees) at t."""
    amp = SWEEP_AMP * ease("inout", clamp((t - SWEEP_T0) / 0.5))
    amp *= 1.0 - ease("inout", clamp((t - T_SETTLE[0]) / (T_SETTLE[1] - T_SETTLE[0])))
    return amp * math.sin(math.pi * (t - SWEEP_T0))


def door_at(t):
    """The vault door's swing on the plan: it opens on the click and claps shut at the thud."""
    if t < T_THUD:
        return ease("out3", clamp((t - T_CLICK) / 0.35))
    shut = 1.0 - ease("in", clamp((t - T_THUD) / 0.17))
    bounce = 0.07 * math.sin(math.pi * clamp((t - T_THUD - 0.17) / 0.2))
    return shut + bounce


def plan_prog(t):
    g = {"in": s_in(t) / P.route_len(P.ROUTE_IN), "out": s_out(t) / P.route_len(OUT_ROUTE),
         "chevron": clamp((t - (T_CHEVRON - 0.08)) / 0.2), "cone": clamp((t - T_CONE[0]) / (T_CONE[1] - T_CONE[0])),
         "ring": clamp((t - T_RING[0]) / (T_RING[1] - T_RING[0])), "dial": clamp((t - T_DIAL) / 0.2),
         "car": clamp((t - T_CAR) / 0.4), "bell": clamp((t - T_BELL) / 0.3), "dot": clamp((t - T_DOT) / 0.18)}
    for name, t0 in NUMERALS:
        g[name] = clamp((t - t0) / 0.45)
    return g


def _ring_hand(c, t):
    """The timing ring's hand: a dot running round it once a swing (plan px)."""
    a = SWEEP_AMP and abs(sweep(t)) / SWEEP_AMP
    live = clamp((t - T_RING[1]) / 0.3) * (1.0 - ease("inout", clamp((t - T_SETTLE[0]) / (T_SETTLE[1] - T_SETTLE[0]))))
    if live <= 0.0:
        return
    ang = math.radians(-90.0 + 180.0 * (t - SWEEP_T0))
    p = (P.GUARD_POST[0] + P.RING_R * math.cos(ang), P.GUARD_POST[1] + P.RING_R * math.sin(ang))
    K.dot(c, p, 6.0 + 2.0 * a, K.PAPER, seed=139, alpha=0.9 * live)


# ============================================================================ the pieces
def _hop_state(sched, t):
    """(point, lift, tilt) of a piece hopping through its schedule."""
    for (_, a), (t1, b) in zip(sched, sched[1:]):
        if t < t1 - HOP:
            return a, 0.0, 0.0
        if t < t1:
            u = (t - (t1 - HOP)) / HOP
            e = ease("inout", u)
            d = math.dist(a, b)
            lean = 0.0 if abs(b[0] - a[0]) < 10.0 else (1.0 if b[0] > a[0] else -1.0)
            return ((lerp(a[0], b[0], e), lerp(a[1], b[1], e)), (22.0 + 0.25 * d) * math.sin(math.pi * u),
                    8.0 * lean * math.sin(math.pi * u))
    return sched[-1][1], 0.0, 0.0


def _jolt(t):
    """The others jump when the knight is slammed down: (lift, wobble)."""
    if not (T_THUD <= t < T_THUD + 0.5):
        return 0.0, 0.0
    u = (t - T_THUD) / 0.5
    lift = 22.0 * math.sin(math.pi * min(1.0, u / 0.55)) if u < 0.55 else 5.0 * math.sin(math.pi * (u - 0.55) / 0.45)
    return lift, 6.0 * math.sin(u * 14.0) * (1.0 - u)


def knight_carry(t):
    """The red knight in his own hand, (point, lift), from T_GRAB until it lands at T_THUD."""
    if t >= T_THUD:
        return KNIGHT_CAR, 0.0
    if t < T_GRAB + 0.1:
        return D1, 18.0 * ease("out", clamp((t - T_GRAB) / 0.1))
    u = (t - (T_GRAB + 0.1)) / (T_THUD - T_GRAB - 0.1)
    e = ease("inout", u)
    return (lerp(D1[0], KNIGHT_CAR[0], e), lerp(D1[1], KNIGHT_CAR[1], e)), 18.0 * (1.0 - u) + 230.0 * math.sin(math.pi * u)


def piece_states(t):
    """[(kind, point, lift, tilt)] for every piece on (or over) the plan at t."""
    out = []
    jl, jt = _jolt(t)
    for kind in ("bishop", "queen", "knight"):
        if kind == "knight" and t >= T_GRAB:
            p, lift = knight_carry(t)
            out.append((kind, p, lift, 0.0))
            continue
        p, lift, tilt = _hop_state(HOPS[kind], t)
        if kind == "bishop":                            # working the dial: right, left, right
            for t0, d, _ in TURNS:
                tilt += 6.0 * d * math.sin(math.pi * clamp((t - t0) / 0.24))
        if kind != "knight":
            lift, tilt = lift + jl * (1.0 if kind == "queen" else 0.8), tilt + jt * (1.0 if kind == "queen" else -1.0)
        out.append((kind, p, lift, tilt))
    if t >= T_PAWN:
        out.append(("pawn", P.GUARD_POST, jl * 0.6, -jt * 0.5))
    return out


def _draw_pieces(c, cam, t):
    for kind, p, lift, tilt in sorted(piece_states(t), key=lambda it: cam.depth(it[1])):
        col, edge, fc = COLOURS[kind]
        P.piece_on(c, cam, kind, p, PIECE_H, col, edge, facing=fc, lift=lift, tilt=tilt)


def _dust(c, cam, t):
    """Chalk dust jumps off the paper round the slammed knight."""
    if not (T_THUD <= t < T_THUD + 0.6):
        return
    v = cam.to_view(KNIGHT_CAR)
    u = (t - T_THUD) / 0.6
    for i in range(9):
        a = math.radians(-160.0 + 140.0 * i / 8.0)
        d = (40.0 + 150.0 * ease("out3", u)) * cam.zoom / 2.0
        K.dot(c, (v[0] + d * math.cos(a) * 1.4, v[1] + d * math.sin(a) * 0.5), 5.0 * (1.0 - u), K.PAPER, seed=70 + i,
              alpha=0.8)


# ============================================================================ the hands
# her chalk tip: (t0, t1, kind, args). "route": along a route between arc lengths; "go": from one
# (point, z) to another on an arc (bump: how high it lifts on the way)
def _her_moves():
    door, x = P.VAULT_DOOR, P.X_VAULT
    return (
        (-0.6, 0.45, "go", ((-80.0, 1520.0), 260.0, P.MANHOLE_A, 6.0, 0.0)),
        (0.45, 0.6, "go", (P.MANHOLE_A, 6.0, P.MANHOLE_A, 0.0, 0.0)),
        (0.6, 1.0, "go", (P.MANHOLE_A, 0.0, P.MANHOLE_A, 3.0, 8.0)),
        (1.0, 3.6, "route_in", None),
        (3.6, 4.2, "go", (_r(735), 0.0, (430.0, 1040.0), 90.0, 20.0)),
        (4.2, 4.85, "go", ((430.0, 1040.0), 90.0, (410.0, 1010.0), 80.0, 0.0)),
        (4.85, 5.0, "go", ((410.0, 1010.0), 80.0, (292.0, 900.0), 2.0, 0.0)),
        (5.0, 5.3, "go", ((292.0, 900.0), 0.0, (568.0, 900.0), 0.0, 0.0)),        # the light, swept out
        (5.3, 5.5, "go", ((568.0, 900.0), 0.0, _r(735), 0.0, 22.0)),
        (5.5, 6.3, "route_in", None),
        (6.3, 6.8, "go", (door, 0.0, (380.0, 760.0), 90.0, 10.0)),
        (6.8, 7.7, "go", ((380.0, 760.0), 90.0, (372.0, 744.0), 96.0, 0.0)),
        (7.7, 8.05, "go", ((372.0, 744.0), 96.0, door, 0.0, 0.0)),
        (8.05, 8.4, "route_in", None),
        (8.4, 8.5, "go", (x, 0.0, x, 4.0, 0.0)),
        (8.5, 9.0, "go", (x, 4.0, (505.0, 510.0), 70.0, 10.0)),
        (9.0, 10.45, "go", ((505.0, 510.0), 70.0, (498.0, 520.0), 74.0, 0.0)),
        (10.45, T_DOT, "go", ((498.0, 520.0), 74.0, P.DOT, 0.0, 0.0)),            # down past the vault ...
        (T_DOT, 11.5, "go", (P.DOT, 0.0, P.MANHOLE_A, 0.0, 320.0)),               # ... and away, round to (5)
        (11.5, 12.4, "route_out", None),
        (12.4, 12.6, "go", (P.CAR, 0.0, P.CAR, 6.0, 0.0)),
        (12.6, 13.0, "go", (P.CAR, 6.0, P.BELL_AT, 0.0, 60.0)),
        (13.0, 13.3, "go", (P.BELL_AT, 0.0, P.BELL_AT, 8.0, 0.0)),
        (13.3, 14.2, "go", (P.BELL_AT, 8.0, (-300.0, 1350.0), 420.0, 0.0)),
    )


HER_MOVES = _her_moves()


def her_tip(t):
    """Her chalk tip: (plan point, height over the paper), or None when her hand is away."""
    for t0, t1, kind, a in HER_MOVES:
        if not (t0 <= t < t1):
            continue
        if kind == "route_in":
            return K.poly_at(P.ROUTE_IN, s_in(t))[0], 0.0
        if kind == "route_out":
            return K.poly_at(OUT_ROUTE, s_out(t))[0], 0.0
        p0, z0, p1, z1, bump = a
        u = (t - t0) / (t1 - t0)
        e = ease("inout", u)
        return (lerp(p0[0], p1[0], e), lerp(p0[1], p1[1], e)), lerp(z0, z1, e) + bump * math.sin(math.pi * u)
    return None


def _shadowed(c, cam, ground, hz, draw_fn):
    """A hand and its shadow on the paper, cast away from the lamp (hz: its height, plan px)."""
    if hz < 600.0:
        dx, dy = ground[0] - P.LAMP_AT[0], ground[1] - P.LAMP_AT[1]
        d = math.hypot(dx, dy) or 1.0
        k = 10.0 + hz * 0.32
        sp = cam.to_view((ground[0] + dx / d * k, ground[1] + dy / d * k))
        gp = cam.to_view(ground, hz)
        c.save()
        c.push_group()
        c.translate(sp[0] - gp[0], sp[1] - gp[1])
        draw_fn(c)
        mask = c.pop_group()
        c.set_source_rgba(*K.INK, 0.3 * clamp(1.0 - hz / 600.0))
        c.mask(mask)
        c.restore()
    draw_fn(c)


def _hand_scale(cam):
    """Hands are about one and a half pieces tall."""
    return 0.65 * cam.zoom * cam.stand()


def _chalk_hand(c, cam, t):
    st = her_tip(t)
    if st is None:
        return
    tip, z = st
    if z < 0.5 and any(t0 <= t < t1 for t0, t1, kind, _ in HER_MOVES if kind.startswith("route")):
        tip = (tip[0] + 1.2 * math.sin(t * 61.0), tip[1] + 1.2 * math.sin(t * 47.0))      # the chalk's chatter
    s = _hand_scale(cam)
    bottom = cam.to_view(tip, z)
    L = 95.0 * s                                        # the chalk, leaning back toward her arm
    grip = (bottom[0] - 0.5 * L, bottom[1] - 0.87 * L)
    wrist = cam.to_view((tip[0] - 1400.0, tip[1] + 300.0), 420.0)

    def draw_fn(cc):
        bass.line_band(cc, [bottom, grip], K.PAPER, width=max(4.0, 15.0 * s), seed=161)
        F.hand(cc, "architect", wrist, grip, s)
    _shadowed(c, cam, tip, z + 60.0, draw_fn)


def _piece_hand(c, cam, who, p, lift, open_u, from_off):
    """A hand holding (or just letting go of) a piece's crown at plan point p, raised lift."""
    v = cam.to_view(p)
    crown = (v[0], v[1] - (lift + PIECE_H * 0.96) * cam.zoom * cam.stand())
    wrist = cam.to_view((p[0] + from_off[0], p[1] + from_off[1]), 420.0)
    _shadowed(c, cam, p, lift + PIECE_H, lambda cc: F.hand(cc, who, wrist, crown, _hand_scale(cam), open_u=open_u))


def _cracker_hand(c, cam, t):
    """His old hand brings the black pawn down onto the guard post from the far side."""
    if not (T_PAWN - 0.7 <= t < T_PAWN + 0.8):
        return
    come = (90.0, -360.0)
    if t < T_PAWN:
        u = clamp((t - (T_PAWN - 0.62)) / 0.62)
        e = ease("inout3", u)
        p = (P.GUARD_POST[0] + come[0] * (1.0 - e), P.GUARD_POST[1] + come[1] * (1.0 - e))
        lift = 230.0 * (1.0 - ease("inout", clamp((u - 0.25) / 0.75)))
        P.piece_on(c, cam, "pawn", p, PIECE_H, K.INK, K.PAPER, lift=lift)
        _piece_hand(c, cam, "cracker", p, lift, 0.0, (250.0, -1400.0))
        return
    open_u = clamp((t - T_PAWN - 0.04) / 0.18)
    leave = ease("in3", clamp((t - T_PAWN - 0.25) / 0.55))
    p = (P.GUARD_POST[0] + come[0] * leave, P.GUARD_POST[1] + come[1] * leave * 1.6)
    _piece_hand(c, cam, "cracker", p, 260.0 * leave, open_u, (250.0, -1400.0))


def _knight_hand(c, cam, t):
    """His heavy hand: in from his side, the knight snatched off the route, slammed down by the
    street, let go, gone."""
    if not (T_GRAB - 0.4 <= t < T_THUD + 0.65):
        return
    off = (1400.0, 260.0)
    if t < T_GRAB:
        u = ease("out3", clamp((t - (T_GRAB - 0.4)) / 0.4))
        p = (lerp(D1[0] + 380.0, D1[0], u), lerp(D1[1] + 90.0, D1[1], u))
        _piece_hand(c, cam, "knight", p, 180.0 * (1.0 - u), 1.0 - clamp((t - (T_GRAB - 0.08)) / 0.08), off)
        return
    if t < T_THUD:
        p, lift = knight_carry(t)
        _piece_hand(c, cam, "knight", p, lift, 0.0, off)
        return
    open_u = clamp((t - T_THUD - 0.03) / 0.12)
    leave = ease("in3", clamp((t - T_THUD - 0.15) / 0.5))
    p = (KNIGHT_CAR[0] + 520.0 * leave, KNIGHT_CAR[1] - 80.0 * leave)
    _piece_hand(c, cam, "knight", p, 300.0 * leave, open_u, off)


# ============================================================================ the lens on the dial
def dial_rot(t):
    return sum(d * deg * ease("inout3", clamp((t - t0) / 0.24)) for t0, d, deg in TURNS)


def _dial_face(t):
    def fn(c):
        K.fill(c, K.BLUE)
        cx, cy = LENS_C
        for i in range(-3, 4):                              # the sheet's grid, close
            g = 46.0 * i
            bass.line_band(c, [(cx + g, cy - 160.0), (cx + g, cy + 160.0)], K.PAPER, width=1.5, seed=170 + i, alpha=0.12)
            bass.line_band(c, [(cx - 160.0, cy + g), (cx + 160.0, cy + g)], K.PAPER, width=1.5, seed=180 + i, alpha=0.12)
        R = 92.0
        rot = dial_rot(t)
        K.chalk_circle(c, LENS_C, R, 1.0, 6.0, K.PAPER, seed=140)
        for i in range(40):
            a = math.radians(rot + 9.0 * i - 90.0)
            r0 = R - (22.0 if i % 5 == 0 else 13.0)
            bass.line_band(c, [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                               (cx + (R - 6.0) * math.cos(a), cy + (R - 6.0) * math.sin(a))], K.PAPER,
                           width=3.5 if i % 5 == 0 else 2.2, seed=141 + i)
        for i, txt in enumerate(("0", "10", "20", "30")):
            a = math.radians(rot + 90.0 * i - 90.0)
            K.numeral(c, txt, (cx + (R - 42.0) * math.cos(a), cy + (R - 42.0) * math.sin(a)), 20.0, K.PAPER,
                      seed=150 + i, rot=rot + 90.0 * i)
        K.chalk_circle(c, LENS_C, 24.0, 1.0, 4.0, K.PAPER, seed=155)
        K.arrowhead(c, (cx, cy - R - 2.0), (0.0, 1.0), 20.0, K.GOLD, seed=156)       # the index
        for k, (t0, d, _) in enumerate(TURNS):              # each turn: a gold arrow round the dial, and its count
            u = ease("out", clamp((t - t0) / 0.24))
            if u <= 0.0:
                continue
            mid = -30.0 + 120.0 * k
            a0, a1 = mid - 34.0 * d, mid + 34.0 * d
            pts = [(cx + (R + 24.0) * math.cos(math.radians(lerp(a0, a1, u * j / 12.0))),
                    cy + (R + 24.0) * math.sin(math.radians(lerp(a0, a1, u * j / 12.0)))) for j in range(13)]
            K.chalk_line(c, pts, 1.0, 5.0, K.GOLD, seed=160 + k)
            ae = math.radians(lerp(a0, a1, u))
            K.arrowhead(c, pts[-1], (-math.sin(ae) * d, math.cos(ae) * d), 18.0, K.GOLD, seed=163 + k)
            K.numeral(c, str(k + 1), (cx + (R + 52.0) * math.cos(math.radians(mid)), cy + (R + 52.0) * math.sin(math.radians(mid))),
                      20.0, K.GOLD, seed=166 + k, scale=ease("outback", clamp((t - t0) / 0.2)))
        if t >= T_CLICK:                                    # click: it gives
            f = 1.0 - clamp((t - T_CLICK) / 0.25)
            K.dot(c, LENS_C, 24.0 + 30.0 * (1.0 - f), K.GOLD, seed=169, alpha=0.8 * f)
    return fn


def _lens(c, cam, t):
    u = min(clamp((t - T_LENS[0]) / 0.3), 1.0 - clamp((t - T_LENS[1]) / 0.16))
    if u <= 0.0:
        return
    K.callout(c, cam.to_view(P.DIAL_AT), LENS_C, LENS_R, _dial_face(t), u=u, color=K.GOLD, ring_w=9.0, dot_r=8.0,
              line_w=4.0, seed=33)


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, K.DEEP)
    cam = cam_at(t)
    prog, ang, door = plan_prog(t), sweep(t), door_at(t)

    def on_plan(c):
        P.draw_plan_a(c, 1.0, ang, prog, door)
        _ring_hand(c, t)

    with f.screen() as c:
        P.table(c, cam, 1.0, 1.0, 0.0, on_plan=on_plan)
        if T_X <= t < T_X + 0.6:                            # the route's arrow lands on the X
            K.ripple(c, cam.to_view(P.X_VAULT), t, T_X, K.PAPER, n=1, life=0.5, r0=26.0 * cam.zoom,
                     r1=70.0 * cam.zoom, width=4.0)
        _draw_pieces(c, cam, t)
        _dust(c, cam, t)
        _cracker_hand(c, cam, t)
        _knight_hand(c, cam, t)
        _chalk_hand(c, cam, t)
        _lens(c, cam, t)


def cues(T):
    out = [Cue(0.0, "cut to the plan from above: the theme carries on, light and quick (pizzicato bass, brushes)",
               gain_db=-16),
           Cue(T_CHEVRON, "chalk tap: the 'down here' chevron on manhole A", gain_db=-10, pan=-0.4),
           Cue(T_MURMUR[0], "the briefing, murmured over the plan (their low voices, no words)", gain_db=-20,
               dur=T_MURMUR[1] - T_MURMUR[0])]
    for name, t0 in NUMERALS:
        out.append(Cue(t0, f"a soft chalk tick: the circled step {name[1]} pops in", gain_db=-19))
    for t0, t1, _, _ in DRAW_IN + ((DRAW_OUT[0], DRAW_OUT[1], 0, 0),):
        out.append(Cue(t0, "chalk dotting along the route (a quick dry run of taps)", gain_db=-17, dur=t1 - t0))
    landings = {}
    for sched in HOPS.values():
        for t0, _ in sched[1:]:
            landings[t0] = landings.get(t0, 0) + 1
    for t0, n in sorted(landings.items()):
        out.append(Cue(t0, f"wooden clack: {n} chess piece{'s' if n > 1 else ''} land{'' if n > 1 else 's'} on the plan "
                           "(the file hops on the beat)", gain_db=-12 + 2 * (n - 1)))
    out += [Cue(T_PAWN - 0.6, "an old man's sleeve and cuff come in from the far side", gain_db=-22, pan=0.3),
            Cue(T_PAWN, "clack: the Cracker sets the black pawn (the guard) on his post", gain_db=-9, pan=-0.3),
            Cue(T_CONE[0], "a soft swish: she sweeps the guard's light out from his post", gain_db=-16, pan=-0.2),
            Cue(T_RING[0], "chalk circling the pawn: the timing ring, four ticks", gain_db=-18, dur=T_RING[1] - T_RING[0])]
    for k in range(9):                                      # the swing's extremes: a low metronome tock
        out.append(Cue(SWEEP_T0 + 0.5 + k, "a low wooden tock: the guard's light at the end of its swing (the timing)",
                       gain_db=-21, pan=-0.3))
    out += [Cue(T_LENS[0], "a soft chalk tick: the lens opens on the vault dial", gain_db=-18, pan=0.4)]
    for t0, d, _ in TURNS:
        out.append(Cue(t0, f"a safe dial's ratchet turning {'right' if d > 0 else 'left'} (fine clicks)", gain_db=-13,
                       pan=0.4, dur=0.24))
    out += [Cue(T_CLICK, "CLUNK: the bolt draws back; the vault door swings open (a heavy hinge sigh)", gain_db=-8),
            Cue(T_X, "chalk tap: the arrow lands on the X; a bright accent in the score", gain_db=-11),
            Cue(T_GRAB - 0.35, "a heavy sleeve swings in fast from the right", gain_db=-15, pan=0.6),
            Cue(T_GRAB, "the red knight snatched up off the paper (a wooden scrape)", gain_db=-14, pan=0.2),
            Cue(T_THUD, "THUD: the red knight slammed down by the street; the pieces rattle; the vault door claps shut",
                gain_db=-4, pan=0.3),
            Cue(T_DOT, "a soft chalk tap under the thud: the dot (buried in the mix, never heard over it)",
                gain_db=-26, pan=-0.2),
            Cue(T_CAR, "a chalk 'tock': the car drawn by the street", gain_db=-13, pan=0.5),
            Cue(T_BELL, "a tiny chalk scratch: a bell on the side door (no ring)", gain_db=-18, pan=0.5),
            Cue(13.6, "the plan is done: the theme lands on a held chord", gain_db=-14, dur=2.4),
            Cue(T_TILT + 0.4, "a rising paper whoosh: the camera tilts down into the plan (it carries into s04)",
                gain_db=-12, dur=T.duration - T_TILT - 0.4)]
    return out
