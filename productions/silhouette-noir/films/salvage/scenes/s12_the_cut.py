"""s12 · THE CUT: on deck at night under a high moon (9.5 s).

(draft: the docstring is finalised after QA)
"""
import copy
import functools
import math

import cairo
import numpy as np

from engine import atmos, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor, arm_ik
from engine.physics import Rope
from engine.timing import Cue, SceneTiming
from films.salvage import cast
from films.salvage import sets as S
from films.salvage import sets_boat as SB
from films.salvage import sets_props as SPROPS
from films.salvage.scenes import _lib_s01_s03_s16 as LIB
from films.salvage.scenes import _lib_s02_s12 as K
from films.salvage.scenes import _lib_s10_s13 as LIB10

PAL = S.PAL
INK = PAL.ink
LIGHT = PAL.light
RED = S.RED
D2R = math.pi / 180.0
ss = smoothstep
mix = S.mix
track = LIB.track


def _ssv(e0, e1, x):
    """smoothstep for numpy arrays."""
    u = np.clip((np.asarray(x, np.float64) - e0) / (e1 - e0), 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)


def track2(keys, t):
    """track() for 2D points: [(t, (x, y), ease_into_key)]."""
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            t0, v0 = keys[i - 1][0], keys[i - 1][1]
            t1, v1 = keys[i][0], keys[i][1]
            e = keys[i][2] if len(keys[i]) > 2 else "inout"
            u = ease(e, (t - t0) / max(t1 - t0, 1e-9))
            return (lerp(v0[0], v1[0], u), lerp(v0[1], v1[1], u))
    return keys[-1][1]


def herm(t, k0, k1):
    """Cubic Hermite between knots (t, value, velocity per second)."""
    t0, y0, v0 = k0
    t1, y1, v1 = k1
    D = t1 - t0
    u = clamp((t - t0) / D)
    return ((2 * u ** 3 - 3 * u ** 2 + 1) * y0 + (u ** 3 - 2 * u ** 2 + u) * D * v0
            + (-2 * u ** 3 + 3 * u ** 2) * y1 + (u ** 3 - u ** 2) * D * v1)


def herm_keys(keys, t):
    if t <= keys[0][0]:
        return keys[0][1] + keys[0][2] * (t - keys[0][0])
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            return herm(t, a, b)
    return keys[-1][1] + keys[-1][2] * (t - keys[-1][0])


# ============================================================================= timing
_T = SceneTiming("salvage", "s12")
T_TIGHT = _T.at("tight")            # 3.343: the line snaps taut
T_THEN = _T.at("Then")              # 5.073: his hand goes to the knife
T_CUT = _T.at("cut")                # 6.025: the slash
T_MINE = _T.at("mine")              # 6.408: the knife changes hands, he starts cranking
T_BREAK = 1.00                      # the lens breaks the surface (waterline through frame centre)
T_PUFF = 1.75                       # a long, slow draw on the cigar while he waits
T_PUFF2 = 3.68                      # ...and a short pleased one when the line goes tight
T_HAND = 3.98                       # his hand comes up to the cigar
T_TAKE = 4.14                       # the cigar leaves his mouth
T_SET = 4.52                        # ...and touches down on the rail (tap)
T_GRAB = 5.26                       # his hand closes on the knife's grip
T_OUTK = 5.43                       # the blade clears the sheath
T_GLINT = 5.47                      # the knife's second and last glint
T_CRANK = 6.86                      # the first turn of the crank
T_TILT = 7.30                       # the camera starts down over the side
T_A = -0.625                        # first handle frame
T_END = 10.0                        # last handle frame (9.5 + 0.5)

MOON = LIB.NIGHT_MOON
MOON_R = LIB.NIGHT_MOON_R
BRIGHT = LIB.NIGHT_BRIGHT
PALE = LIB.PALE
HOSE_W = LIB.HOSE_W
LINE_W = 5.0                        # the pale line, as s14 draws it


# ============================================================================= the boat
def _nod(t):
    """The stern nods down when the line takes the weight, and comes back (transient)."""
    tau = t - T_TIGHT
    if tau <= 0.0:
        return 0.0
    return (1.0 - math.exp(-tau / 0.05)) * math.exp(-tau / 0.55) * (1.0 + 0.45 * math.sin(2.0 * math.pi * 1.6 * tau))


def _jerk(t):
    """The block kicks on the davit when the line snaps taut (deg)."""
    tau = t - T_TIGHT
    if tau <= 0.0:
        return 0.0
    return 5.0 * math.exp(-tau / 0.35) * math.sin(2.0 * math.pi * 2.3 * tau) * min(1.0, tau / 0.03)


class _Tender(S.Boat):
    """The diving tender (as s14's), plus the jolt of the load coming on the line."""

    def pose(self, t):
        x, y, ang = S.Boat.pose(self, t)
        k = _nod(t)
        return x, y + 3.0 * k, ang + 0.6 * k

    def _block_swing(self, t):
        return S.Boat._block_swing(self, t) + _jerk(t)


BOAT = _Tender()
Q = SB.PUMP["squash"]
X_C = 450.0                         # the client's pelvis while cranking (boat-local; s14: world -612)
FEET = (492.0, 432.0)               # near (R) and far (L) foot, boat-local (s14: -570 / -630 world)
CIGAR_X = 532.0                     # he lays the cigar on the top rail here
CUT_X = 606.0                       # the hose goes over the top rail here: the cut


def deck_l(x):
    return SB.deck_local(x)


def rail_top_l(x):
    """Top face of the top rail (boat-local y)."""
    return deck_l(x) - SB.RAIL_H - 3.5


def pump_angle(t):
    return 150.0 * t


def crank_deg(t):
    """Crank handle angle (deg, clockwise on screen) on the winch gear: at rest, a jolt back
    when the line takes the weight, then turned calmly from T_CRANK (~0.4 turn/s)."""
    a = 205.0
    tau = t - T_TIGHT
    if tau > 0.0:
        a -= 9.0 * (1.0 - math.exp(-tau / 0.04)) * math.exp(-tau / 0.8) + 2.0 * (1.0 - math.exp(-tau / 0.3))
    tc = t - T_CRANK
    if tc > 0.0:
        w0, w1, r = 60.0, 150.0, 1.1
        a += w1 * tc - (w1 - w0) * r * (1.0 - math.exp(-tc / r))
    return a


def winch_angle(t):
    return -2.0 * crank_deg(t)


def crank_grip(t):
    """World point of the crank handle."""
    gx, gy, gr = SB.WINCH["gear"]
    a = math.radians(crank_deg(t))
    return BOAT.to_world((gx + math.cos(a) * 62.0, gy + math.sin(a) * 62.0), t)


def _draw_rail(L, t):
    """The near railing, drawn in front of the client (Boat.draw draws it last otherwise)."""
    BOAT._begin(L, BOAT.pose(t))
    L.new_path()
    S.put(L, S.shape("boat_rail", SB._railing))
    S.paint(L, INK)
    L.restore()


# --- the donkey engine that drives the air pump by a belt (not in the boat set: drawn here)
ENG_PUL = (306.0, -226.0, 22.0)     # engine pulley (x, y, r): squashed like the flywheels
PUMP_PUL = (262.0, -336.0, 30.0)    # pulley on the pump's crankshaft, outboard of the flywheel


def _engine(c):
    """A squat single-cylinder donkey engine on a skid (boat-local)."""
    S.round_rect(c, 292.0, -172.0, 388.0, -156.0, 4.0)                 # skid
    S.round_rect(c, 304.0, -232.0, 378.0, -160.0, 8.0)                 # crankcase
    S.round_rect(c, 326.0, -276.0, 360.0, -228.0, 4.0)                 # cylinder
    for k in range(4):                                                  # cooling fins
        y = -272.0 + 10.0 * k
        S.round_rect(c, 320.0, y, 366.0, y + 5.0, 2.0)
    S.round_rect(c, 322.0, -290.0, 364.0, -276.0, 4.0)                 # head
    draw.poly(c, S.oriented([(366.0, -262.0), (373.0, -262.0), (377.0, -352.0), (369.0, -352.0)]))  # exhaust
    S.round_rect(c, 363.0, -362.0, 383.0, -350.0, 3.0)
    draw.poly(c, S.oriented([(300.0, -232.0), (312.0, -232.0), (312.0, -218.0), (300.0, -218.0)]))  # shaft boss


def _belt_strands():
    """The two straight runs of the belt between the pulleys, worked out in the pulleys'
    own (foreshortened) plane: external tangents of two circles."""
    (ax, ay, ra), (bx, by, rb) = PUMP_PUL, ENG_PUL
    c1 = np.array([0.0, ay])
    c2 = np.array([(bx - ax) / Q, by])
    d = c2 - c1
    L = float(np.linalg.norm(d))
    u = d / L
    n = np.array([-u[1], u[0]])
    out = []
    for s in (1.0, -1.0):
        k = (ra - rb) / L
        h = math.sqrt(max(0.0, 1.0 - k * k))
        nv = k * u + s * h * n
        p1 = c1 + nv * ra
        p2 = c2 + nv * rb
        out.append(((ax + p1[0] * Q, p1[1]), (ax + p2[0] * Q, p2[1])))
    return out


BELT = _belt_strands()


def _draw_engine(L, t):
    BOAT._begin(L, BOAT.pose(t))
    L.new_path()
    S.put(L, S.shape("s12_engine", _engine))
    for (x, y, r) in (PUMP_PUL, ENG_PUL):
        L.save()
        L.translate(x, y)
        L.scale(Q, 1.0)
        L.new_sub_path()
        L.arc(0.0, 0.0, r + 3.0, 0.0, 2.0 * math.pi)
        L.restore()
    S.paint(L, INK)
    for a, b in BELT:
        L.move_to(*a)
        L.line_to(*b)
    L.set_line_width(4.5)
    L.set_line_cap(cairo.LINE_CAP_BUTT)
    L.set_source_rgb(*INK)
    L.stroke()
    # the belt's laced joint running along the strands (it shows the drive turning)
    (a0, b0), (a1, b1) = BELT
    l0 = math.hypot(b0[0] - a0[0], b0[1] - a0[1])
    l1 = math.hypot(b1[0] - a1[0], b1[1] - a1[1])
    loop = l0 + l1 + 2.0 * math.pi * 0.5 * (PUMP_PUL[2] + ENG_PUL[2]) * Q * 1.6
    s = (t * 95.0) % loop
    for (pa, pb, ln, s0) in ((a0, b0, l0, 0.0), (b1, a1, l1, loop * 0.5)):
        u = (s - s0) / ln
        if 0.05 < u < 0.95:
            p = (lerp(pa[0], pb[0], u), lerp(pa[1], pb[1], u))
            draw.circle(L, p, 4.0)
            L.set_source_rgb(*INK)
            L.fill()
    L.restore()


def _exhaust_pt(t):
    return BOAT.to_world((373.0, -366.0), t)


def _boat_mask(G, t):
    BOAT.draw(G, t, color=(0.0, 0.0, 0.0), pump_angle=pump_angle(t), winch_angle=winch_angle(t), hose=False,
              hook=False, rail=True, lantern=True)


# ============================================================================= camera
CAM_DECK = (-432.0, -174.0, 0.85)   # wide on the stern working deck (moon top left)
CAM_CUT = (-505.0, -455.0, 1.10)    # pushed in on him, the winch and the rail
Z_IN = 0.55                         # s11's zoom at the cut
X_LEAN = 55.0                       # how far the current leans the line out at depth
DX_HOSE = 236.0                     # at depth the hose runs this far right of the line (s11)
Y_DEEP = 6400.0                     # the hose and line are drawn this far down

# camera height while rising: knots (t, y, vy)
_RISE_Y = [(T_A, 2430.0, -1550.0), (0.0, 1300.0, -2050.0), (T_BREAK, 0.0, -560.0), (2.05, CAM_DECK[1], 0.0)]


def _line_x0(y, t):
    """The taut line's x at world depth y (leaning out with the current below the hull)."""
    return BOAT.sheave(t)[0] + X_LEAN * ss(0.0, 2600.0, y)


def _rise(t):
    y = herm_keys(_RISE_Y, t)
    z = math.exp(lerp(math.log(Z_IN), math.log(CAM_DECK[2]), ease("inout", clamp((t - 0.15) / 1.9))))
    yb = y + (H / 2) / z
    xl = _line_x0(yb, t) + (540.0 - 470.0) / z         # the line at screen x 470 on the bottom edge
    x = lerp(xl, CAM_DECK[0], ease("inout", clamp((t - 0.2) / 1.85)))
    return x, y, z


def _deck_cam(t):
    x = track([(2.05, CAM_DECK[0]), (4.6, CAM_DECK[0] - 6.0), (5.95, CAM_CUT[0], "inout"), (7.3, CAM_CUT[0] + 4.0)], t)
    y = track([(2.05, CAM_DECK[1]), (4.6, CAM_DECK[1] - 10.0), (5.95, CAM_CUT[1], "inout"), (7.3, CAM_CUT[1] + 6.0)], t)
    z = math.exp(track([(2.05, math.log(CAM_DECK[2])), (4.6, math.log(CAM_DECK[2] * 1.01)),
                        (5.95, math.log(CAM_CUT[2]), "inout"), (7.3, math.log(CAM_CUT[2] * 1.01))], t))
    return x, y, z


Z_OUT = 1.25
X_OUT_HOSE = 533.0                  # where the hose leaves the bottom edge (s13 picks it up there)


def _down_keys():
    y0 = _deck_cam(T_TILT)[1]
    return [(T_TILT, y0, 0.0), (8.55, 520.0, 760.0), (T_END + 0.2, 1300.0, 380.0)]


def _down_y(t):
    return herm_keys(_down_keys(), t)


def _down_z(t):
    return math.exp(track([(T_TILT, math.log(CAM_CUT[2] * 1.01)), (8.9, math.log(Z_OUT), "inout"),
                           (12.0, math.log(Z_OUT))], t))


def _cam3(t):
    if t < 2.05:
        return _rise(t)
    if t < T_TILT:
        return _deck_cam(t)
    y = _down_y(t)
    z = _down_z(t)
    x0 = _deck_cam(T_TILT)[0]
    w = ss(T_TILT + 0.6, 9.0, t)
    x = x0
    if w > 0.0:
        xh = _out_track_x(t, y, z)
        x = lerp(x0, xh, w)
    return x, y, z


def _shake(t):
    """Short shudders (<= 4 px): the line snapping taut, the cut."""
    a = 0.0
    for tk, s, d in ((T_TIGHT, 3.2, 0.3), (T_CUT, 2.0, 0.18)):
        if t >= tk:
            a += s * math.exp(-(t - tk) / d)
    return a


def camera(t):
    x, y, z = _cam3(t)
    a = _shake(t)
    if a > 0.05:
        k = a / z
        x += k * noise1(t * 31.0, 3)
        y += k * noise1(t * 29.0, 7)
    return Camera(x, y, z).shaken(t, amp=1.0, rot_amp=0.03, freq=0.35, seed=12)


# ============================================================================= water colour
def _s11_vdepth(t):
    """Virtual depth of s11's top edge at the paired time (its compressed night water)."""
    tau = t + 10.0
    u = clamp((tau - 7.30) / (10.625 + 0.4 - 7.30))
    vy = lerp(1750.0, 760.0, ss(0.1, 0.95, u))
    return vy - 475.0


def _vscale(t):
    """Depth compression of the water colour: while rising from s11 our bottom edge carries
    s11's top-edge colour; it relaxes to true night water as we reach the deck."""
    if t >= 2.2:
        return 1.0
    x, y, z = _rise(min(t, 2.05))
    yb = y + (H / 2) / z
    v0 = clamp(_s11_vdepth(min(t, 0.625)) / max(yb, 1.0), 0.05, 1.0)
    return lerp(v0, 1.0, ss(0.5, 2.2, t))


def _bright(t):
    return lerp(0.55, BRIGHT, ss(0.3, 1.6, t))


def _water(f, t):
    """The water section below the (wavy) surface coloured by (compressed) depth."""
    x0, y0, x1, y1 = f.cam.view_rect(200)
    if y1 < -60:
        return
    vs, br = _vscale(t), _bright(t)
    ya, yb = max(y0 - 50, -60.0), max(y1, 0.0) + 10
    n = 18
    stops = [(lerp(ya, yb, i / (n - 1)), S.water_at(max(lerp(ya, yb, i / (n - 1)), 0.0) * vs, br)) for i in range(n)]
    c = f.ctx
    c.new_path()
    if ya < 80:
        pts = S.sea_pts(x0, x1, t, step=max(6.0, (x1 - x0) / 160))
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        c.line_to(x1, yb)
        c.line_to(x0, yb)
        c.close_path()
    else:
        c.rectangle(x0, ya, x1 - x0, yb - ya)
    span = (yb - ya) or 1.0
    draw.linear(c, (0, ya), (0, yb), [((y - ya) / span, col, 1.0) for y, col in stops])
    c.fill()


# ============================================================================= the line
def _slack(t):
    return 1.0 - ss(T_TIGHT - 0.06, T_TIGHT + 0.02, t)


def _line_pts(t):
    """The pale lifting line from the sheave into the dark: hanging slack in lazy S-bends
    (the current) until [tight], then straight, ringing for a moment."""
    sh = BOAT.sheave(t)
    sl = _slack(t)
    tau = t - T_TIGHT
    ring = 0.0
    if tau > 0.0:
        ring = 9.0 * math.exp(-tau / 0.3) * math.sin(2.0 * math.pi * 9.0 * tau) * min(1.0, tau / 0.02)
    n = 80
    out = []
    for i in range(n + 1):
        u = i / n
        y = sh[1] + (Y_DEEP - sh[1]) * u ** 1.8
        x = _line_x0(max(y, 0.0), t) if y > 0 else sh[0]
        if sl > 0.0:
            if y < 0.0:
                x += sl * 16.0 * math.sin(math.pi * clamp((y - sh[1]) / (0.0 - sh[1])))
            else:
                env = ss(0.0, 220.0, y) * (1.0 - ss(1300.0, 2600.0, y))
                x += sl * env * (52.0 * math.sin(y / 250.0 - 1.1 * t + 0.6) + 22.0 * math.sin(y / 120.0 + 1.6 * t))
                x += sl * 16.0 * ss(-40.0, 120.0, y) * (1.0 - ss(120.0, 400.0, y))
        if ring:
            d = y - sh[1]
            x += ring * math.sin(math.pi * clamp(d / 1300.0)) * (1.0 - 0.6 * clamp(d / 1300.0))
        out.append((x, y))
    return out


def _draw_line(L, t, cam):
    pts = _line_pts(t)
    if t < 8.6:
        LIB.draw_hose(L, pts, LINE_W, color=PALE)
        return
    # going down into the dark: the line fades out above the bottom edge (s13 has none)
    yb = cam.y + (H / 2) / cam.zoom
    y1 = yb - 260.0 / cam.zoom
    y0 = y1 - 700.0 / cam.zoom
    L.save()
    L.new_path()
    draw.smooth(L, pts, close=False, tension=0.5)
    L.set_line_width(LINE_W)
    L.set_line_cap(cairo.LINE_CAP_ROUND)
    g = cairo.LinearGradient(0.0, y0, 0.0, y1)
    g.add_color_stop_rgba(0.0, PALE[0], PALE[1], PALE[2], 1.0)
    g.add_color_stop_rgba(1.0, PALE[0], PALE[1], PALE[2], 0.0)
    L.set_source(g)
    L.stroke()
    L.restore()


# ============================================================================= the hose
def _deck_run_l():
    """Pump outlet -> along the deck in front of the engine and the winch -> up behind the
    rail -> the top of the rail at CUT_X (boat-local)."""
    ox, oy = SB.PUMP["outlet"]
    pts = [(ox + 20.0, oy), (ox + 36.0, oy + 9.0), (ox + 52.0, deck_l(ox + 52.0) - 9.0), (ox + 70.0, deck_l(ox + 70.0) - 5.5)]
    x = ox + 92.0
    while x < 556.0:
        pts.append((x, deck_l(x) - 5.0))
        x += 22.0
    ry = rail_top_l(CUT_X) - 5.0
    pts += [(566.0, deck_l(566.0) - 6.0), (577.0, deck_l(577.0) - 16.0), (586.0, deck_l(586.0) - 44.0),
            (593.0, -248.0), (598.5, -284.0), (602.5, ry + 9.0), (CUT_X, ry)]
    return pts


def _over_l():
    """From the cut over the top rail and down the outside of the hull to the water (local)."""
    ry = rail_top_l(CUT_X) - 5.0
    x = CUT_X
    return [(x, ry), (x + 7.0, ry - 1.0), (x + 13.0, ry + 3.5), (x + 17.0, ry + 15.0), (x + 19.5, -270.0),
            (x + 21.0, -220.0), (x + 22.5, -160.0), (x + 23.5, -100.0), (x + 24.5, -40.0), (x + 25.5, 20.0),
            (x + 26.5, 80.0)]


DECK_RUN = _deck_run_l()
OVER = _over_l()


def _hose_water(t, p0):
    """World: from p0 (on the hull's side under the waterline) down under the hull, then
    across under the line to its right-hand side and on down into the dark (s11's set-up)."""
    out = []
    y0 = p0[1]
    ys = np.concatenate([np.linspace(y0 + 40.0, 1500.0, 26), np.linspace(1560.0, 3600.0, 34),
                         np.linspace(3700.0, Y_DEEP, 14)])
    for y in ys:
        u = ss(1450.0, 3450.0, y)
        top = p0[0] - 30.0 * ss(y0, 1400.0, y) + 7.0 * math.sin(0.5 * t + y / 310.0) * ss(y0, y0 + 300.0, y)
        x = lerp(top, _line_x0(y, t) + DX_HOSE, u)
        x += 16.0 * math.sin(0.45 * t + y / 520.0) * math.sin(math.pi * clamp((y - y0) / 3400.0))
        out.append((x, y))
    return out


def _w(pts, t):
    return [BOAT.to_world(p, t) for p in pts]


def _hose_pre(t):
    """(deck piece, outside piece) of the hose before the cut (world): pump -> cut point,
    cut point -> the deep."""
    over = _w(OVER, t)
    return _w(DECK_RUN, t), over + _hose_water(t, over[-1])


def _resample(pts, n):
    P = np.asarray(pts, np.float64)
    seg = np.linalg.norm(P[1:] - P[:-1], axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    u = np.linspace(0.0, s[-1], n)
    return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], axis=1), float(s[-1])


class _MediumRope(Rope):
    """physics.Rope (its verlet + red-black constraint solve, bending stiffness and
    collisions, unchanged) with a per-node medium: accel(t, P, V) -> (n, 2) accelerations
    (gravity, drag and current that differ in air and water; the jet of air out of an open
    hose end; the recoil of the cut)."""

    def __init__(self, n, length, a, b=None, accel=None, **kw):
        Rope.__init__(self, n, length, a, b, **kw)
        self.accel = accel

    def _simulate(self):
        n, dt = self.n, self.dt
        steps = int(math.ceil((self.t1 - self.t0) / dt)) + 2
        P = np.array(self.init(self.t0), np.float64)
        prev = P.copy()
        frames = np.empty((steps, n, 2), np.float64)
        inv = np.ones((n, 1))
        inv[0] = 0.0
        for k in range(steps):
            t = self.t0 + k * dt
            vel = (P - prev) / dt
            acc = self.accel(t, P, vel)
            new = P + vel * dt + acc * dt * dt
            prev, P = P, new
            rest = self._rest(t)
            pa = np.array(self.a(t), np.float64)
            for _ in range(self.iters):
                P[0] = pa
                for parity in (0, 1):
                    i0 = np.arange(parity, n - 1, 2)
                    d = P[i0 + 1] - P[i0]
                    L = np.linalg.norm(d, axis=1)[:, None] + 1e-9
                    diff = (L - rest) / L
                    wa, wb = inv[i0], inv[i0 + 1]
                    sw = wa + wb
                    sw[sw == 0] = 1.0
                    P[i0] += d * diff * wa / sw
                    P[i0 + 1] -= d * diff * wb / sw
                if self.stiffness > 0 and n > 2:
                    for grp in ((0, 1), (2, 3)):
                        i0 = np.array([i for i in range(n - 2) if i % 4 in grp], dtype=int)
                        if len(i0) == 0:
                            continue
                        d = P[i0 + 2] - P[i0]
                        L = np.linalg.norm(d, axis=1)[:, None] + 1e-9
                        diff = np.minimum((L - 2 * rest) / L, 0.0) * self.stiffness
                        wa, wb = inv[i0], inv[i0 + 2]
                        sw = wa + wb
                        sw[sw == 0] = 1.0
                        P[i0] += d * diff * wa / sw
                        P[i0 + 2] -= d * diff * wb / sw
                if self.collide is not None:
                    ym = self.collide(P[:, 0], P[:, 1])
                    hit = P[:, 1] > ym
                    if hit.any():
                        P[hit, 1] = ym[hit]
                        prev[hit, 0] = P[hit, 0] - (P[hit, 0] - prev[hit, 0]) * 0.5
            P[0] = pa
            frames[k] = P
        self._frames = frames


# --- the pump end, on deck (boat-local coordinates: the deck stays put in them)
DECK_N = 44
_DECK_X = np.arange(-200.0, 1000.0, 4.0)
_DECK_Y = np.array([deck_l(float(x)) for x in _DECK_X])


def _deck_floor(x, y):
    return np.interp(x, _DECK_X, _DECK_Y) - 5.0


def _deck_accel(t, P, V):
    n = len(P)
    acc = np.zeros_like(P)
    acc[:, 1] = 2400.0
    acc -= 1.2 * V
    tau = t - T_CUT
    idx = np.linspace(0.0, 1.0, n)
    if 0.0 <= tau < 0.07:
        # the cut lets go of the hanging hose's pull: the last run springs back inboard
        w = (_ssv(0.55, 1.0, idx) ** 1.5)[:, None]
        acc += w * np.array([-30000.0, -9000.0]) * (1.0 - tau / 0.07)
    if tau > 0.1:
        # the pump keeps blowing: the jet out of the open end shoves it about (it whips)
        e = P[-1] - P[-4]
        e /= (np.linalg.norm(e) + 1e-9)
        nrm = np.array([-e[1], e[0]])
        k = ss(0.1, 0.25, tau) * (1.0 - 0.5 * ss(1.2, 3.5, tau))
        wob = math.sin(2.0 * math.pi * 2.7 * tau) + 0.7 * math.sin(2.0 * math.pi * 4.9 * tau + 1.0)
        acc[-1] += k * (-5600.0 * e + 3600.0 * wob * nrm)
        acc[-2] += k * (-2400.0 * e + 1600.0 * wob * nrm)
        acc[-3] += k * (900.0 * wob * nrm)
    return acc


@functools.lru_cache(maxsize=1)
def _deck_rope():
    P0, L = _resample(DECK_RUN, DECK_N)
    a = tuple(P0[0])
    return _MediumRope(DECK_N, L, lambda t: a, None, accel=_deck_accel, t0=T_CUT, t1=T_END + 0.3,
                       dt=1.0 / 240.0, collide=_deck_floor, iters=12, stiffness=0.35, init=lambda t0: P0)


# --- the diver's end, over the side (world coordinates)
WATER_N = 170
G_AIR = 2600.0
G_WATER = 470.0
_SW = np.array(S.SWELL)


def _sea_np(x, t):
    y = np.zeros_like(x)
    for A, Lw, Tp, ph, d in _SW:
        y += A * np.sin(2.0 * math.pi * (x / Lw - d * t / Tp) + ph)
    return y


def _water_accel(t, P, V):
    sea = _sea_np(P[:, 0], t)
    w = np.clip((P[:, 1] - sea + 4.0) / 10.0, 0.0, 1.0)
    g = G_AIR * (1.0 - w) + G_WATER * w
    drag = 0.25 * (1.0 - w) + 1.7 * w
    y = P[:, 1]
    # a slow set toward the bow in the upper water (the slack hose drifts back under the
    # hull), with shear that folds it into loose S-bends; nothing at depth
    shear = (1.0 - _ssv(1800.0, 2800.0, y))
    cur = (-38.0 + 46.0 * np.sin(y / 360.0 - 0.9 * t) + 22.0 * np.sin(y / 150.0 + 1.7 * t + 1.0)) * w * shear
    acc = np.empty_like(P)
    acc[:, 0] = -drag * (V[:, 0] - cur)
    acc[:, 1] = g - drag * V[:, 1]
    return acc


@functools.lru_cache(maxsize=1)
def _water_rope():
    deck, out = _hose_pre(T_CUT)
    pts = list(reversed(out))                     # the deep end (pinned) -> the cut end (free)
    P0, L = _resample(pts, WATER_N)
    a = tuple(P0[0])
    return _MediumRope(WATER_N, L, lambda t: a, None, accel=_water_accel, t0=T_CUT, t1=T_END + 0.4,
                       dt=1.0 / 180.0, iters=10, stiffness=0.3, init=lambda t0: P0)


def hose_end(t):
    """World point of the severed (diver's) end."""
    if t < T_CUT:
        return BOAT.to_world(OVER[0], t)
    return tuple(_water_rope().points(t)[-1])


def _hose_deck_pts(t):
    if t < T_CUT:
        return _w(DECK_RUN, t)
    return _w(_deck_rope().points(t), t)


def _hose_out_pts(t):
    if t < T_CUT:
        return _hose_pre(t)[1]
    return [tuple(p) for p in reversed(_water_rope().points(t))]


def _hose_x_at(t, y):
    """x where the (cut) hose first crosses depth y going down from its end, or None."""
    P = _water_rope().points(t)[::-1]
    for a, b in zip(P, P[1:]):
        if (a[1] - y) * (b[1] - y) <= 0.0 and a[1] != b[1]:
            u = (y - a[1]) / (b[1] - a[1])
            return a[0] + (b[0] - a[0]) * u
    return None


def _out_track_x(t, y, z):
    """Camera x that puts the hose on the bottom edge at X_OUT_HOSE (smoothed over 0.5 s)."""
    xs = []
    for dt in (-0.24, -0.12, 0.0, 0.12, 0.24):
        tt = clamp(t + dt, T_CUT + 0.6, T_END + 0.2)
        yb = _down_y(tt) + (H / 2) / _down_z(tt)
        x = _hose_x_at(tt, yb)
        if x is not None:
            xs.append(x)
    if not xs:
        return _deck_cam(T_TILT)[0]
    xh = sum(xs) / len(xs)
    return xh - (X_OUT_HOSE - W / 2) / z


def _stroke(ctx, pts, width, color, cap=cairo.LINE_CAP_ROUND, alpha=1.0):
    if len(pts) < 2:
        return
    ctx.save()
    ctx.new_path()
    if len(pts) >= 3:
        draw.smooth(ctx, pts, close=False, tension=0.5)
    else:
        draw.poly(ctx, pts, close=False)
    ctx.set_line_width(width)
    ctx.set_line_cap(cap)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(color[0], color[1], color[2], alpha)
    ctx.stroke()
    ctx.restore()


# ============================================================================= the client
BODY = cast.CLIENT
HB = copy.copy(BODY)                # the same body, its forearm reaching to the middle of the fist
HB.forearm = BODY.forearm + 0.55 * BODY.hand * BODY.hand_scale
STAND = (BODY.hip - 0.006) * BODY.height        # pelvis height over the deck, standing


def _crank_w(t):
    return ss(6.42, 6.86, t)


def _pitch(t):
    """Forward bend at the hips (deg): still; a slow bow to lay the cigar down; the lean
    into the cut; bent over the crank (s14's pose, bobbing with the crank)."""
    p = track([(-1.0, 3.0), (T_TAKE - 0.05, 3.0), (T_SET - 0.02, 38.0, "inout"), (T_SET + 0.12, 38.0),
               (5.02, 5.0, "inout"), (5.55, 6.0), (5.92, 30.0, "inout"), (6.03, 40.0, "in"), (6.16, 41.0, "out"),
               (6.42, 34.0, "inout"), (12.0, 34.0)], t)
    a = math.radians(crank_deg(t))
    return lerp(p, 42.0 + 12.0 * math.sin(a), _crank_w(t))


def _crouch(t):
    """Pelvis drop (px): the knees give for the bow and the cut."""
    return track([(-1.0, 0.0), (T_TAKE - 0.05, 0.0), (T_SET - 0.02, 40.0, "inout"), (T_SET + 0.12, 40.0),
                  (5.02, 2.0, "inout"), (5.55, 4.0), (5.92, 28.0, "inout"), (6.03, 36.0, "in"), (6.16, 38.0, "out"),
                  (12.0, 38.0)], t)


def _c_path(t):
    pitch = math.radians(_pitch(t))
    a = math.radians(crank_deg(t))
    w = _crank_w(t)
    lx = lerp(456.0 - 12.0 * math.sin(pitch), X_C + 12.0 * math.cos(a), w)
    breathe = 1.3 * math.sin(2.0 * math.pi * t / 3.9)
    ly_stand = deck_l(lx) - STAND + _crouch(t) + breathe
    ly_crank = deck_l(lx) - 276.0 + 25.0 * math.sin(a)
    return BOAT.to_world((lx, lerp(ly_stand, ly_crank, w)), t)


def _c_pose(t, u):
    x, y = _c_path(t)
    p = F.Pose(x, y, 0.0)
    p.pitch = _pitch(t)
    w = _crank_w(t)
    p.spine = [lerp(2.0, 4.0, w), lerp(3.0, 6.0, w), lerp(2.0, 4.0, w) + 0.6 * math.sin(2.0 * math.pi * t / 3.9)]
    p.neck = 2.0
    p.head = -0.86 * p.pitch + 3.0 + 1.0 * noise1(t * 0.2, 5)
    for s, fx in (("R", FEET[0]), ("L", FEET[1])):
        wx, wy = BOAT.to_world((fx, deck_l(fx)), t)
        p.legs[s] = {"ik": (wx, wy - 0.043 * BODY.height), "pitch": 0.0, "toe": 0.0, "abd": 3.0}
    p.arms["R"] = dict(sh=-3.0, abd=7.0, elbow=14.0, wrist=4.0, grip=0.45)
    p.arms["L"] = dict(sh=lerp(-6.0, -28.0, w), abd=6.0, elbow=lerp(14.0, 24.0, w), wrist=lerp(6.0, 8.0, w),
                       grip=0.4)
    p.eyes = dict(open=1.0, glow=0.9, look=0.0)
    return p


def _line_entry(t):
    sh = BOAT.sheave(t)
    return (sh[0] + 30.0, 40.0)


def _rail_pt(lx, t, dy=0.0):
    return BOAT.to_world((lx, rail_top_l(lx) + dy), t)


@functools.lru_cache(maxsize=1)
def _client():
    A = Actor(BODY, cast.client(), x=-606.0, ground=1e6, facing=1, seed=12, name="client")
    A.free(16.0, _c_path, _c_pose, at=-2.0)
    # where he looks: the line where it goes into the water; up at the block when it goes
    # tight; down at the rail; the knife; the cut; then up the line while he cranks
    A.look_at(-2.0, T_TIGHT - 0.1, _line_entry, fade=0.4, amount=0.75)
    A.look_at(T_TIGHT + 0.06, 3.85, lambda t: BOAT.sheave(t), fade=0.22, amount=0.8)
    A.look_at(4.0, 4.75, lambda t: _rail_pt(CIGAR_X, t), fade=0.25, amount=0.9)
    A.look_at(5.10, 5.40, lambda t: (_c_path(t)[0] + 48.0, _c_path(t)[1] - 40.0), fade=0.15, amount=0.7)
    A.look_at(5.55, 6.35, lambda t: _rail_pt(CUT_X, t), fade=0.2, amount=1.0)
    A.look_at(6.75, 16.0, lambda t: (BOAT.sheave(t)[0], BOAT.sheave(t)[1] + 380.0), fade=0.5, amount=0.6)
    A.blink(2.62)
    A.blink(T_TIGHT + 0.12, dur=0.12)
    A.blink(6.55, dur=0.24)
    A.blink(8.3)
    return A


@functools.lru_cache(maxsize=512)
def _base_pose(t):
    return _client().pose(t)


@functools.lru_cache(maxsize=512)
def _base_sk(t):
    return F.solve(_base_pose(t), BODY)


def _mouth(sk):
    return F.head_point(sk, 0.86, 0.22, front_x=0.16, front_y=0.20)


def _cigar_rail(t):
    """World centre of the cigar lying on the top rail."""
    return BOAT.to_world((CIGAR_X, rail_top_l(CIGAR_X) - 3.8), t)


def _knife_sheath(t):
    kw = K.knife_on_belt(_base_sk(round(t, 5)))
    return kw, K.knife_points(kw)


DRAW_LEN = 162.0 * K.KNIFE_S        # how far the grip travels to pull the blade clear


def _cut_pt(t):
    return BOAT.to_world((CUT_X + 2.0, rail_top_l(CUT_X) - 5.0), t)


def _r_hand(t):
    """(target for the middle of his right fist (world) or None, weight)."""
    if t < T_HAND - 0.2:
        return None, 0.0
    sk = _base_sk(round(t, 5))
    pel = sk.j["pelvis"]
    rest = (pel[0] + 16.0, pel[1] + 70.0)
    m = _mouth(sk)
    at_mouth = (m[0] - 4.0, m[1] + 9.0)
    cg = _cigar_rail(t)
    on_rail = (cg[0] - 2.0, cg[1] - 9.0)
    if t < T_TAKE:
        return at_mouth, ss(T_HAND - 0.2, T_HAND + 0.1, t)
    if t < T_SET:
        u = ease("inout", (t - T_TAKE) / (T_SET - T_TAKE))
        mid = (lerp(at_mouth[0], on_rail[0], 0.5) + 26.0, lerp(at_mouth[1], on_rail[1], 0.45))
        p = (lerp(lerp(at_mouth[0], mid[0], u), lerp(mid[0], on_rail[0], u), u),
             lerp(lerp(at_mouth[1], mid[1], u), lerp(mid[1], on_rail[1], u), u))
        return p, 1.0
    if t < T_SET + 0.1:
        return on_rail, 1.0
    kw, kp = _knife_sheath(t)
    grip = kp["grip"]
    hd = kp["handle_dir"]
    if t < T_THEN:
        # back to his side
        w = 1.0 - ss(T_SET + 0.1, T_SET + 0.55, t)
        lift = (on_rail[0] - 6.0, on_rail[1] - 26.0)
        p = track2([(T_SET + 0.1, on_rail), (T_SET + 0.3, lift), (T_SET + 0.55, rest)], t)
        return p, w
    if t < T_GRAB:
        u = ease("inout", (t - T_THEN) / (T_GRAB - T_THEN))
        return (lerp(rest[0], grip[0], u), lerp(rest[1], grip[1], u)), ss(T_THEN - 0.04, T_THEN + 0.1, t)
    if t < T_OUTK:
        u = ease("in", (t - T_GRAB) / (T_OUTK - T_GRAB))
        return (grip[0] + hd[0] * DRAW_LEN * u, grip[1] + hd[1] * DRAW_LEN * u), 1.0
    out = (grip[0] + hd[0] * DRAW_LEN, grip[1] + hd[1] * DRAW_LEN)
    sh = sk.j["shoulder_R"]
    ready = (sh[0] + 92.0, sh[1] + 62.0)
    cut = _cut_pt(t)
    cocked = (cut[0] - 70.0, cut[1] - 150.0)
    through = (cut[0] + 30.0, cut[1] + 58.0)
    handoff = (pel[0] + 58.0, pel[1] + 6.0)
    keys = [(T_OUTK, out), (5.62, (out[0] + 14.0, out[1] - 30.0), "out"), (5.80, ready, "inout"),
            (5.955, cocked, "inout"), (6.045, through, "in"), (6.14, (through[0] + 10.0, through[1] + 14.0), "out"),
            (6.40, handoff, "inout"), (6.47, handoff)]
    if t <= 6.47:
        return track2(keys, t), 1.0
    g = crank_grip(t)
    tgt = (g[0] - 6.0, g[1] - 2.0)
    u = ss(6.47, T_CRANK - 0.02, t)
    return (lerp(handoff[0], tgt[0], u), lerp(handoff[1], tgt[1], u)), 1.0


def _l_hand(t):
    """Target for his left fist: it takes the knife at [mine], then hangs with it."""
    if t < 6.12 or t > 6.95:
        return None, 0.0
    sk = _base_sk(round(t, 5))
    pel = sk.j["pelvis"]
    handoff = (pel[0] + 50.0, pel[1] + 10.0)
    return handoff, ss(6.12, 6.38, t) * (1.0 - ss(6.5, 6.95, t))


def _apply_arm(p, side, target, w, grip):
    if target is None or w <= 0.0:
        return
    q = arm_ik(p.copy(), side, target, HB)
    for k in ("sh", "elbow"):
        p.arms[side][k] = lerp(p.arms[side][k], q.arms[side][k], w)
    p.arms[side]["wrist"] = lerp(p.arms[side].get("wrist", 0.0), 0.0, w)
    if grip is not None:
        p.arms[side]["grip"] = lerp(p.arms[side].get("grip", 0.3), grip, w)


@functools.lru_cache(maxsize=128)
def _solved(t):
    p = _base_pose(t).copy()
    tr, wr = _r_hand(t)
    _apply_arm(p, "R", tr, wr, 0.95)
    tl, wl = _l_hand(t)
    _apply_arm(p, "L", tl, wl, 0.95)
    if t > 6.4:
        p.arms["L"]["grip"] = 1.0
    return F.solve(p, BODY)


def client_sk(t):
    return _solved(round(t, 5))


def _ember(t):
    """The cigar's glow (0.55 idle .. 1.5 drawn on)."""
    e = 0.55 + 0.08 * noise1(t * 0.9, 9)
    e += 0.95 * LIB.bump(t, T_PUFF - 0.35, T_PUFF + 0.15, T_PUFF + 0.55, T_PUFF + 2.0)
    e += 0.6 * LIB.bump(t, T_PUFF2 - 0.12, T_PUFF2 + 0.06, T_PUFF2 + 0.2, T_PUFF2 + 1.2)
    return e


def _flare(t):
    return 0.85 * LIB.bump(t, T_PUFF - 0.35, T_PUFF + 0.15, T_PUFF + 0.55, T_PUFF + 2.0) \
        + 0.5 * LIB.bump(t, T_PUFF2 - 0.12, T_PUFF2 + 0.06, T_PUFF2 + 0.2, T_PUFF2 + 1.2)


def _client_look(t):
    lk = cast.client(ember=_ember(t), coat_flow=0.16 + 0.08 * noise1(t * 0.5, 4))
    if t >= T_TAKE:
        lk.extras = []
    return lk


def _knife_hand(t, sk):
    """(grip point, blade direction (deg)) of the drawn knife in his right hand."""
    kw, kp = _knife_sheath(t)
    hd = kp["handle_dir"]
    a_sheath = math.degrees(math.atan2(-hd[1], -hd[0]))      # blade back down the sheath
    h = sk.j["hand_R"]
    a = track([(T_GRAB, a_sheath), (T_OUTK, a_sheath), (5.62, a_sheath - 25.0, "out"), (5.80, 20.0, "inout"),
               (5.955, -60.0, "inout"), (6.045, 62.0, "in"), (6.14, 80.0, "out"), (6.40, 96.0, "inout"),
               (12.0, 96.0)], t)
    return h, a


def _draw_knife_blade(L, h, a, flip):
    """Draw the knife with its blade pointing along world angle a (deg) from grip h."""
    if flip:
        return S.draw_knife(L, h[0], h[1], angle=a - 180.0, s=K.KNIFE_S, flip=True)
    return S.draw_knife(L, h[0], h[1], angle=a, s=K.KNIFE_S, flip=False)


def _draw_sheath(L, kw):
    """The empty sheath on his belt (the knife is out)."""
    L.save()
    L.translate(kw["x"], kw["y"])
    L.rotate(math.radians(kw["angle"]))
    L.scale(-kw["s"] if kw.get("flip") else kw["s"], kw["s"])
    L.new_path()
    L.append_path(S.shape("sheath", SPROPS._sheath))
    L.restore()
    L.set_source_rgb(*INK)
    L.fill()


def _knife_left(L, sk):
    """The knife hanging in his far hand while he cranks (as s14 draws it)."""
    w = sk.j["wrist_L"]
    h = sk.j["hand_L"]
    ang = math.degrees(math.atan2(h[1] - w[1], h[0] - w[0])) - 35.0
    S.draw_knife(L, h[0], h[1], angle=ang, s=K.KNIFE_S)


def _draw_cigar(L, f, c, ang, ember):
    """The cigar as a prop: an ink capsule with its ember (emissive) at the +ang end."""
    ln = 30.0
    r = 0.006 * BODY.height
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    a = (c[0] - ca * ln / 2, c[1] - sa * ln / 2)
    b = (c[0] + ca * ln / 2, c[1] + sa * ln / 2)
    draw.capsule(L, a, b, r, r * 0.92)
    L.set_source_rgb(*INK)
    L.fill()
    with f.emit() as G:
        draw.circle(G, b, r * (0.8 + 0.4 * ember))
        G.set_source_rgba(*LIGHT, min(1.0, 0.6 + 0.4 * ember))
        G.fill()
    return b


def _cigar_hand(sk):
    """(centre, angle) of the cigar held in his right fingers."""
    w, h, fg = sk.j["wrist_R"], sk.j["hand_R"], sk.j["fingers_R"]
    ang = math.degrees(math.atan2(fg[1] - w[1], fg[0] - w[0]))
    return ((h[0] + fg[0]) / 2, (h[1] + fg[1]) / 2), ang - 70.0


# ============================================================================= effects
def _ember_flare(f, sk, t):
    """The ember is a few px at this zoom: when he draws on it a warm halo blooms (s14)."""
    k = _flare(t)
    if k <= 0.01 or t >= T_TAKE:
        return
    p = _mouth(sk)
    atmos.lamp(f, p, radius=5.0, intensity=k, halo=7.0, core=0.0, flicker="ember", t=t, seed=21)


def _smoke(f, t, sk):
    m = _mouth(sk) if t < T_TAKE + 0.3 else None
    if m is not None:
        K.smoke(f, t, m, T_PUFF + 0.75, 0.7, n=7, wind=(-34.0, -15.0), seed=5, alpha=0.12)
        K.smoke(f, t, m, T_PUFF2 + 0.35, 0.35, n=4, wind=(-30.0, -12.0), seed=8, alpha=0.08)
    # the cigar left burning on the rail: a thin thread of smoke going up
    if t > T_SET + 0.1:
        K.smoke(f, t, _cigar_rail(t), T_SET + 0.2, 8.0, n=34, wind=(-16.0, -38.0), seed=9, alpha=0.06, size=0.6)
    # the donkey engine's exhaust, a soft puff on each beat
    K.smoke(f, t, _exhaust_pt(t), -1.5, 12.0, n=28, wind=(-28.0, -30.0), seed=4, alpha=0.05, size=0.8)


def _slash(f, t):
    """A thin moonlit arc along the blade's stroke for a couple of frames."""
    if not (T_CUT - 0.04 < t < T_CUT + 0.09):
        return
    pts = []
    for i in range(10):
        tt = t - 0.07 + 0.07 * i / 9
        if tt < 5.95:
            continue
        sk = client_sk(tt)
        h, a = _knife_hand(tt, sk)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        L = 200.0 * K.KNIFE_S
        pts.append((h[0] + ca * L, h[1] + sa * L))
    if len(pts) < 3:
        return
    k = 1.0 - ss(T_CUT + 0.02, T_CUT + 0.09, t)
    with f.light(blur=1.5) as A:
        for i in range(len(pts) - 1):
            S.line(A, [pts[i], pts[i + 1]], 1.0 + 2.5 * i / len(pts), PAL.moon, 0.55 * k * (i + 1) / len(pts))


def _hiss(f, t):
    """The pump's air blowing out of the open end on deck: a faint flickering fan of mist
    and droplets."""
    tau = t - T_CUT
    if tau < 0.05 or tau > 4.0:
        return
    P = _hose_deck_pts(t)
    e, e2 = P[-1], P[-3]
    d = (e[0] - e2[0], e[1] - e2[1])
    ln = math.hypot(*d) or 1.0
    d = (d[0] / ln, d[1] / ln)
    n = (-d[1], d[0])
    k = ss(0.05, 0.15, tau) * (1.0 - 0.6 * ss(1.0, 4.0, tau))
    col = mix(PAL.moon, PAL.surface, 0.3)
    with f.light(blur=2.5) as A:
        for i in range(9):
            h1, h2 = hash01(31, i, 1), hash01(31, i, 2)
            ph = (t * (5.0 + 3.0 * h1) + h2) % 1.0
            sp = (h1 - 0.5) * 0.9
            L0 = 6.0 + 70.0 * ph
            dx, dy = d[0] + n[0] * sp, d[1] + n[1] * sp
            a = (e[0] + dx * L0, e[1] + dy * L0)
            b = (e[0] + dx * (L0 + 14.0 + 10.0 * h2), e[1] + dy * (L0 + 14.0 + 10.0 * h2))
            S.line(A, [a, b], 1.2, col, 0.32 * k * (1.0 - ph))


def _end_under(te):
    p = hose_end(te)
    return (p[0], max(p[1], S.sea_y(p[0], te) + 6.0))


_END_S = LIB.Sampled(_end_under, T_CUT, T_END + 0.4, hz=48.0)


def _end_bubbles(f, t):
    """The last of the air in the hose leaving the cut end as it sinks."""
    if t < T_CUT + 0.45:
        return
    atmos.bubbles(f, _END_S, rate=9.0, t=t, seed=46, rise=(200.0, 330.0), size=(1.5, 6.0), spread=6.0,
                  current=10.0, surface=4.0, height=1600.0, alpha=0.7, t_start=T_CUT + 0.55, t_end=T_CUT + 2.4)
    atmos.bubbles(f, _END_S, rate=2.5, t=t, seed=47, rise=(180.0, 260.0), size=(1.2, 3.5), spread=4.0,
                  current=10.0, surface=4.0, height=1600.0, alpha=0.6, t_start=T_CUT + 2.4, t_end=T_END)


@functools.lru_cache(maxsize=1)
def _splash_t():
    """When (and where) the falling end hits the water."""
    for i in range(1, 200):
        te = T_CUT + i / 120.0
        p = hose_end(te)
        if p[1] > S.sea_y(p[0], te):
            return te, p[0]
    return T_CUT + 0.5, hose_end(T_CUT + 0.5)[0]


# ============================================================================= render
def render(f, t, T):
    cam = f.set_camera(camera(t))
    top_y = cam.view_rect(0)[1]
    # the night look shared with s14/s15; while rising from s11 the water body is re-laid
    # with its compressed night-water gradient
    rising = _vscale(t) < 0.999 or _bright(t) < BRIGHT - 1e-3
    S.sea_world(f, t, moon=MOON, moon_r=MOON_R, dusk=0.0, veil=0.25, glow=not rising)
    if rising:
        _water(f, t)
        S.surface_glow(f, t, bright=_bright(t))
    atmos.underwater_rays(f, surface_y=0.0, t=t, spacing=190.0, angle=95.0, fan=8.0, length=1800.0,
                          intensity=0.16, density=0.5, seed=14, blur=18, color=mix(PAL.moon, PAL.surface, 0.5))
    sk = client_sk(t)
    look = _client_look(t)
    # silhouettes keep the moon and the lamps behind them
    K.emit_mask(f, [lambda G: _boat_mask(G, t)])
    K.figure_mask(f, sk, look)
    kw = K.knife_on_belt(sk)
    with f.layer() as L:
        _draw_line(L, t, cam)
        BOAT.draw(L, t, pump_angle=pump_angle(t), winch_angle=winch_angle(t), hose=False, hook=False, rail=False)
        _draw_engine(L, t)
        cap = cairo.LINE_CAP_BUTT if t >= T_CUT else cairo.LINE_CAP_ROUND
        _stroke(L, _hose_deck_pts(t), HOSE_W, RED, cap=cap)
        if t >= T_MINE:
            _knife_left(L, sk)                       # far hand: behind him
        F.draw_figure(f, sk, look, L)
        if t < T_GRAB:
            S.draw_knife(L, **kw)
        else:
            _draw_sheath(L, kw)
            if t < T_MINE:
                h, a = _knife_hand(t, sk)
                _draw_knife_blade(L, h, a, t < 5.56)
        if T_TAKE <= t < T_SET:
            c, ang = _cigar_hand(sk)
            _draw_cigar(L, f, c, ang, 0.55)
        _draw_rail(L, t)
        if t >= T_SET:
            _draw_cigar(L, f, _cigar_rail(t), 2.0, 0.55 + 0.08 * noise1(t * 1.3, 2))
        _stroke(L, _hose_out_pts(t), HOSE_W, RED, cap=cap)
    S.water_front(f, t, alpha=0.08, bright=_bright(t))
    BOAT.draw_lights(f, t, lantern=1.0, window=0.5, masthead=1.0)
    _ember_flare(f, sk, t)
    _smoke(f, t, sk)
    if T_OUTK - 0.1 < t < T_GLINT + 0.45:
        h, a = _knife_hand(t, sk)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        gp = (h[0] + ca * 164.0 * K.KNIFE_S, h[1] + sa * 164.0 * K.KNIFE_S)
        S.knife_glint(f, gp, t, T_GLINT, dur=0.36, size=0.75)
    _slash(f, t)
    _hiss(f, t)
    ts, xs = _splash_t()
    LIB.splash(f, t, xs, ts, 16, 0.5, 12)
    _end_bubbles(f, t)
    if top_y > -500:
        atmos.marine_snow(f, density=0.45 * ss(-500.0, 300.0, top_y), t=t, seed=12, sink=5.0, current=(9.0, 0.0),
                          alpha=0.55)
    if t < 1.2:
        c1, c2 = camera(t - 0.02), camera(t + 0.02)
        vy = (c2.y - c1.y) / 0.04
        LIB10.streaks(f, t, (0.0, vy), n=110, seed=13, alpha=0.45 * (1.0 - ss(0.4, 1.1, t)), size=1.3)
    vig = 0.55 if (t < 0.7 or t > 8.9) else 0.46
    if 0.7 <= t <= 1.5:
        vig = lerp(0.55, 0.46, ss(0.7, 1.5, t))
    if 8.3 <= t <= 8.9:
        vig = lerp(0.46, 0.55, ss(8.3, 8.9, t))
    f.post["vignette"] = vig


def motion_blur(t, T):
    if t < 0.75:
        return 3
    if T_TIGHT - 0.02 < t < T_TIGHT + 0.12 or 5.95 < t < 6.14:
        return 3
    return 1


def cues(T):
    return [
        Cue(-0.6, "rising through night water (s11's ascent goes on): a muffled rush", gain_db=-12, dur=1.6),
    ]
