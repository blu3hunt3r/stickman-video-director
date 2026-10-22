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
from engine.palette import RED
from engine.physics import Rope
from engine.timing import Cue, SceneTiming
from films.salvage import cast
from films.salvage import sets as S
from films.salvage import sets_boat as SB
from films.salvage.scenes import _lib_s01_s03_s16 as LIB
from films.salvage.scenes import _lib_s02_s12 as K

PAL = S.PAL
INK = PAL.ink
LIGHT = PAL.light
D2R = math.pi / 180.0
ss = smoothstep
mix = S.mix


def _ssv(e0, e1, x):
    """smoothstep for numpy arrays."""
    u = np.clip((np.asarray(x, np.float64) - e0) / (e1 - e0), 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)

# ============================================================================= timing
_T = SceneTiming("salvage", "s12")
T_WAITED = _T.at("waited")          # 1.021
T_TIGHT = _T.at("tight")            # 3.343: the line snaps taut
T_THEN = _T.at("Then")              # 5.073: he draws the knife
T_CUT = _T.at("cut")                # 6.025: the slash
T_MINE = _T.at("mine")              # 6.408: he starts cranking
T_PUFF = 1.55                       # a slow draw on the cigar while he waits
T_PUFF2 = 3.62                      # ...and a pleased one when the line goes tight
T_TAKE = 4.05                       # the cigar leaves his mouth
T_SET = 4.56                        # ...and touches the rail
T_GRAB = 5.30                       # his hand closes on the knife
T_OUTK = 5.50                       # the blade clears the sheath
T_GLINT = 5.56                      # the knife's last glint
T_CRANK = 6.82                      # the first turn of the crank
T_TILT = 7.30                       # the camera starts down over the side
T_END = 10.0                        # last handle frame (9.5 + 0.5)

MOON = LIB.NIGHT_MOON
MOON_R = LIB.NIGHT_MOON_R
BRIGHT = LIB.NIGHT_BRIGHT
PALE = LIB.PALE
HOSE_W = 10.0
LINE_W = 5.0                        # LIB.PALE line, 5 px (as s14)


# ============================================================================= the boat
def _load(t):
    """The bell's dead weight coming onto the davit when the line goes tight: 0 .. 1 with a
    little overshoot (the stern nods down and settles)."""
    tau = t - T_TIGHT
    if tau <= 0.0:
        return 0.0
    return (1.0 - math.exp(-tau / 0.07)) * (1.0 + 0.55 * math.exp(-tau / 0.45) * math.sin(2.0 * math.pi * 1.7 * tau))


class _Tender(S.Boat):
    """The diving tender riding the swell, plus the load: the stern dips when the line takes
    the weight."""

    def pose(self, t):
        x, y, ang = S.Boat.pose(self, t)
        k = _load(t)
        return x, y + 2.0 * k, ang + 0.5 * k


BOAT = _Tender()
OUTLET = (SB.PUMP["outlet"][0] + 22.0, SB.PUMP["outlet"][1])        # where the hose leaves the pump
PULLEY = (-132.0, -300.0, 26.0)                                        # engine pulley on the wheelhouse
X_C = 432.0                         # the client's pelvis (boat-local x), at the winch
CIGAR_X = 514.0                     # he sets the cigar on the top rail here
CUT_X = 600.0                       # the hose goes over the top rail here: the cut
RAIL_TOP = -SB.RAIL_H - 3.5         # top face of the top rail above the deck line


def deck_l(x):
    return SB.deck_local(x)


def rail_top_l(x):
    return deck_l(x) + RAIL_TOP


def pump_angle(t):
    return 150.0 * t


# the crank: handle angle (deg, clockwise) on the winch gear; the drum turns with it
CRANK0 = 205.0


def crank_deg(t):
    """Crank handle angle: at rest, a jolt back when the line takes the load, then turned
    calmly from T_CRANK (~0.4 turn/s)."""
    a = CRANK0
    tau = t - T_TIGHT
    if tau > 0.0:
        a -= 7.0 * (1.0 - math.exp(-tau / 0.05)) * math.exp(-tau / 0.9) + 2.0 * (1.0 - math.exp(-tau / 0.3))
    tc = t - T_CRANK
    if tc > 0.0:
        w0, w1 = 70.0, 150.0
        r = 1.2
        a += w1 * tc - (w1 - w0) * r * (1.0 - math.exp(-tc / r))
    return a


def winch_angle(t):
    return -2.0 * crank_deg(t)


def crank_grip(t):
    """World point of the crank handle (where his left hand closes)."""
    gx, gy, gr = SB.WINCH["gear"]
    a = math.radians(-winch_angle(t) * 0.5)
    return BOAT.to_world((gx + math.cos(a) * 62.0, gy + math.sin(a) * 62.0), t)


def _draw_rail(L, t):
    """The near railing (the boat draws it last; here it goes in front of the client)."""
    pose = BOAT.pose(t)
    BOAT._begin(L, pose)
    L.new_path()
    S.put(L, S.shape("boat_rail", SB._railing))
    S.paint(L, INK)
    L.restore()


def _belt_pts(n=24):
    """The drive belt from the engine pulley (wheelhouse) to the near flywheel: the two
    strands, computed in the flywheels' own plane (both discs squashed alike)."""
    q = SB.PUMP["squash"]
    cx, cy, R = SB.PUMP["box"][0], SB.PUMP["axle_y"], SB.PUMP["R"] - 4.0
    px, py, r = PULLEY
    c1 = np.array([0.0, cy])
    c2 = np.array([(px - cx) / q, py])
    d = c2 - c1
    L = np.linalg.norm(d)
    ux = d / L
    nrm = np.array([-ux[1], ux[0]])
    out = []
    for s in (1.0, -1.0):
        # external tangent: the normal offset satisfies (R - r) / L = cos(phi)
        cphi = (R - r) / L
        sphi = math.sqrt(max(0.0, 1.0 - cphi * cphi))
        nv = cphi * ux * -1.0 + s * sphi * nrm
        nv = -nv
        a = c1 + nv * R
        b = c2 + nv * r
        out.append(((cx + a[0] * q, a[1]), (cx + b[0] * q, b[1])))
    return out


BELT = _belt_pts()


def _draw_belt(L, t):
    pose = BOAT.pose(t)
    BOAT._begin(L, pose)
    q = SB.PUMP["squash"]
    px, py, r = PULLEY
    for a, b in BELT:
        L.move_to(*a)
        L.line_to(*b)
    L.set_line_width(4.0)
    L.set_source_rgb(*INK)
    L.stroke()
    # the pulley on its bracket, foreshortened like the flywheels
    L.save()
    L.translate(px, py)
    L.scale(q, 1.0)
    L.arc(0.0, 0.0, r + 2.0, 0.0, 2.0 * math.pi)
    L.restore()
    draw.poly(L, [(px - 4.0, py - 6.0), (-176.0, py - 16.0), (-176.0, py + 16.0), (px - 4.0, py + 6.0)])
    L.set_source_rgb(*INK)
    L.fill()
    L.restore()


# ============================================================================= water colour
Y_DEEP = 6000.0                     # the hose and line are drawn this far down


def _vscale(t):
    """Depth compression for the water colour (1 = true night water): the rise from s11 runs
    ahead of the camera, as s11's own ascent does, and settles to true depth on deck."""
    return LIB.track([(-1.0, 0.22), (0.55, 0.13, "inout"), (2.7, 1.0, "inout")], t)


def _wcol(y, t):
    return S.water_at(max(y, 0.0) * _vscale(t), BRIGHT)


def _water(f, t):
    """The water section below the (wavy) surface, coloured by (compressed) depth."""
    x0, y0, x1, y1 = f.cam.view_rect(200)
    if y1 < -60:
        return
    ya, yb = max(y0 - 50, -60.0), max(y1, 0.0) + 10
    n = 18
    stops = [(lerp(ya, yb, i / (n - 1)), _wcol(lerp(ya, yb, i / (n - 1)), t)) for i in range(n)]
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
X_LEAN = 55.0                       # how far the current leans the line out at depth


def _line_x0(y, t):
    """The taut line's x at world depth y (it leans out with the current below the hull)."""
    sx = BOAT.sheave(t)[0]
    return sx + X_LEAN * ss(0.0, 2600.0, y)


def _slack(t):
    return 1.0 - ss(T_TIGHT - 0.07, T_TIGHT + 0.03, t)


def _line_pts(t):
    """The pale lifting line from the sheave down into the dark: a lazy slack belly (the
    current) until [tight], then straight, ringing for a moment."""
    sh = BOAT.sheave(t)
    sl = _slack(t)
    tau = t - T_TIGHT
    ring = 0.0
    if tau > 0.0:
        ring = 10.0 * math.exp(-tau / 0.32) * math.sin(2.0 * math.pi * 8.5 * tau) * min(1.0, tau / 0.02)
    n = 64
    out = []
    for i in range(n + 1):
        u = i / n
        y = sh[1] + (Y_DEEP - sh[1]) * u ** 1.7
        d = y - sh[1]
        x = _line_x0(y, t)
        if sl > 0.0:
            x += sl * (88.0 + 14.0 * math.sin(0.6 * t)) * math.sin(math.pi * clamp(d / 2600.0)) ** 1.2
            x += sl * 10.0 * math.sin(d / 260.0 - 1.3 * t) * ss(0.0, 400.0, d)
        if ring:
            x += ring * math.sin(math.pi * clamp(d / 1100.0)) * (1.0 - 0.5 * clamp(d / 1100.0))
        out.append((x, y))
    return out


# ============================================================================= the hose
DX_HOSE = 242.0                     # at depth the hose runs this far right of the line (s11)


def _deck_run_l():
    """Pump outlet -> along the deck -> up behind the rail to the top of the rail (local)."""
    ox, oy = OUTLET
    pts = [(ox, oy), (ox + 14.0, oy + 7.0), (ox + 30.0, deck_l(ox + 30.0) - 9.0), (ox + 50.0, deck_l(ox + 50.0) - 5.5)]
    x = ox + 70.0
    while x < 562.0:
        pts.append((x, deck_l(x) - 5.0))
        x += 18.0
    ry = rail_top_l(CUT_X) - 5.0
    pts += [(570.0, deck_l(570.0) - 7.0), (578.0, deck_l(578.0) - 18.0), (585.0, -205.0), (591.0, -248.0),
            (595.5, -285.0), (598.5, ry + 12.0), (CUT_X, ry)]
    return pts


def _over_l():
    """From the cut point over the top rail and down the outside of the hull (local)."""
    ry = rail_top_l(CUT_X) - 5.0
    x = CUT_X
    return [(x, ry), (x + 6.0, ry - 1.5), (x + 12.0, ry + 3.0), (x + 16.5, ry + 16.0), (x + 19.5, -275.0),
            (x + 21.5, -225.0), (x + 23.0, -170.0), (x + 24.0, -110.0), (x + 25.0, -50.0), (x + 26.0, 10.0),
            (x + 27.0, 70.0)]


DECK_RUN = _deck_run_l()
OVER = _over_l()


def _hose_water(t, p0):
    """World: from p0 (on the hull side under the waterline) down under the hull, bending
    right across the line, then on down its right side into the dark."""
    out = []
    y0 = p0[1]
    ys = np.concatenate([np.linspace(y0 + 40.0, 1400.0, 30), np.linspace(1500.0, Y_DEEP, 36)])
    for y in ys:
        u = ss(y0 + 150.0, 2900.0, y)
        u = u * u * (3.0 - 2.0 * u)
        top = p0[0] + 6.0 * math.sin(0.5 * t + y / 300.0) * ss(y0, y0 + 300.0, y)
        x = lerp(top, _line_x0(y, t) + DX_HOSE, u)
        x += 18.0 * math.sin(0.45 * t + y / 520.0) * math.sin(math.pi * clamp((y - y0) / 3000.0))
        out.append((x, y))
    return out


def _w(pts, t):
    return [BOAT.to_world(p, t) for p in pts]


def _hose_pre(t):
    """(deck piece, outside piece) of the uncut hose, world coords; the deck piece runs pump ->
    cut point, the outside piece cut point -> the deep."""
    deck = _w(DECK_RUN, t)
    over = _w(OVER, t)
    return deck, over + _hose_water(t, over[-1])


def _resample(pts, n):
    P = np.asarray(pts, np.float64)
    seg = np.linalg.norm(P[1:] - P[:-1], axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    u = np.linspace(0.0, s[-1], n)
    return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], axis=1), float(s[-1])


class _MediumRope(Rope):
    """physics.Rope (same verlet + red-black constraint solver, stiffness and collisions) with
    a per-node medium: accel(t, P, V) -> (n, 2) acceleration (gravity, drag and current that
    differ in air and in water, the jet of air out of an open hose end, an impulse)."""

    def __init__(self, n, length, a, b=None, accel=None, **kw):
        Rope.__init__(self, n, length, a, b, **kw)
        self.accel = accel

    def _simulate(self):
        n, dt = self.n, self.dt
        steps = int(math.ceil((self.t1 - self.t0) / dt)) + 2
        P = np.array(self.init(self.t0), np.float64)
        prev = P.copy()
        frames = np.empty((steps, n, 2), np.float64)
        released = False
        for k in range(steps):
            t = self.t0 + k * dt
            vel = (P - prev) / dt
            acc = self.accel(t, P, vel)
            new = P + vel * dt + acc * dt * dt
            prev, P = P, new
            rest = self._rest(t)
            pa = np.array(self.a(t), np.float64)
            pin_b = self.b is not None and not released
            if pin_b and self.release is not None and self.release(t):
                released = True
                pin_b = False
            pb = np.array(self.b(t), np.float64) if pin_b else None
            inv = np.ones((n, 1))
            inv[0] = 0.0
            if pin_b:
                inv[-1] = 0.0
            for _ in range(self.iters):
                P[0] = pa
                if pin_b:
                    P[-1] = pb
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
                        prev[hit, 0] = P[hit, 0] - (P[hit, 0] - prev[hit, 0]) * 0.55
            P[0] = pa
            if pin_b:
                P[-1] = pb
            frames[k] = P
        self._frames = frames


# --- the pump end, on deck (boat-local coordinates: the deck is still in them)
DECK_N = 40
_DECK_X = np.arange(-200.0, 1000.0, 4.0)
_DECK_Y = np.array([deck_l(float(x)) for x in _DECK_X])


def _deck_floor(x, y):
    return np.interp(x, _DECK_X, _DECK_Y) - 5.0


def _deck_accel(t, P, V):
    n = len(P)
    acc = np.zeros_like(P)
    acc[:, 1] = 2400.0
    acc -= 1.1 * V
    tau = t - T_CUT
    idx = np.linspace(0.0, 1.0, n)
    if 0.0 <= tau < 0.075:
        # the cut releases the pull of the hanging hose: its last run springs back inboard, up
        w = (_ssv(0.5, 1.0, idx) ** 1.5)[:, None]
        acc += w * np.array([-34000.0, -15000.0]) * (1.0 - tau / 0.075)
    if tau > 0.12:
        # the air: the pump blows out of the open end; the jet's push snakes the end around
        e = P[-1] - P[-4]
        e /= (np.linalg.norm(e) + 1e-9)
        nrm = np.array([-e[1], e[0]])
        k = ss(0.12, 0.3, tau) * (1.0 - 0.45 * ss(1.5, 3.5, tau))
        wob = math.sin(2.0 * math.pi * 3.1 * tau) + 0.6 * math.sin(2.0 * math.pi * 5.3 * tau + 1.0)
        acc[-1] += k * (-5200.0 * e + 2600.0 * wob * nrm)
        acc[-2] += k * (-2000.0 * e + 1200.0 * wob * nrm)
    return acc


@functools.lru_cache(maxsize=1)
def _deck_rope():
    P0, L = _resample(DECK_RUN, DECK_N)
    a = tuple(P0[0])
    return _MediumRope(DECK_N, L, lambda t: a, None, accel=_deck_accel, t0=T_CUT, t1=T_END + 0.2,
                       dt=1.0 / 240.0, collide=_deck_floor, iters=12, stiffness=0.35, init=lambda t0: P0)


# --- the diver's end, over the side (world coordinates)
WATER_N = 150
G_AIR = 2600.0
G_WATER = 520.0
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
    drag = 0.35 * (1.0 - w) + 1.8 * w
    y = P[:, 1]
    cur = (30.0 + 70.0 * np.sin(y / 430.0 - 0.8 * t) + 30.0 * np.sin(y / 170.0 + 1.9 * t + 1.0)) * w
    acc = np.empty_like(P)
    acc[:, 0] = -drag * (V[:, 0] - cur)
    acc[:, 1] = g - drag * V[:, 1]
    return acc


@functools.lru_cache(maxsize=1)
def _water_rope():
    deck, out = _hose_pre(T_CUT)
    pts = list(reversed(out))                     # deep end -> the cut
    P0, L = _resample(pts, WATER_N)
    a = tuple(P0[0])
    return _MediumRope(WATER_N, L, lambda t: a, None, accel=_water_accel, t0=T_CUT, t1=T_END + 0.2,
                       dt=1.0 / 180.0, iters=10, stiffness=0.3, init=lambda t0: P0)


def hose_end(t):
    """World point of the severed (diver's) end."""
    if t < T_CUT:
        return BOAT.to_world(OVER[0], t)
    return _water_rope().points(t)[-1]


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


def _hose_deck_pts(t):
    if t < T_CUT:
        return _w(DECK_RUN, t)
    return _w(_deck_rope().points(t), t)


def _hose_out_pts(t):
    if t < T_CUT:
        return _hose_pre(t)[1]
    return list(reversed(_water_rope().points(t)))


# ============================================================================= the client
BODY = cast.CLIENT
HB = copy.copy(BODY)                # same body, the forearm reaching to the middle of the fist
HB.forearm = BODY.forearm + 0.55 * BODY.hand * BODY.hand_scale
YAW = 6.0
FOOT_F, FOOT_B = X_C + 26.0, X_C - 24.0


def _pitch(t):
    """Forward bend at the hips (deg): still; a bow to set the cigar down; the lean into the
    cut; leaning over the winch to crank (bobbing with the crank)."""
    p = LIB.track([(-1.0, 3.0), (3.8, 3.0), (4.05, 9.0, "inout"), (4.52, 47.0, "inout"), (4.66, 46.0),
                   (5.08, 6.0, "inout"), (5.32, 7.0), (5.62, 12.0, "inout"), (5.95, 36.0, "inout"),
                   (6.05, 44.0, "out"), (6.22, 41.0, "inout"), (6.62, 20.0, "inout"), (7.05, 28.0, "inout"),
                   (12.0, 28.0)], t)
    if t > T_CRANK - 0.2:
        a = math.radians(crank_deg(t))
        p += 6.0 * math.cos(a) * ss(T_CRANK - 0.2, T_CRANK + 0.5, t)
    return p


def _crouch(t):
    """Pelvis drop (px): knees give for the bow and the cut."""
    return LIB.track([(-1.0, 0.0), (4.05, 0.0), (4.52, 46.0, "inout"), (4.66, 44.0), (5.08, 2.0, "inout"),
                      (5.62, 4.0), (5.95, 26.0, "inout"), (6.05, 34.0, "out"), (6.22, 30.0), (6.62, 10.0, "inout"),
                      (7.05, 16.0, "inout"), (12.0, 16.0)], t)


def _c_path(t):
    pitch = math.radians(_pitch(t))
    lx = X_C - 0.30 * 175.0 * math.sin(pitch)
    breathe = 1.4 * math.sin(2.0 * math.pi * t / 3.8)
    ly = deck_l(X_C) - (BODY.hip - 0.006) * BODY.height + _crouch(t) + breathe
    return BOAT.to_world((lx, ly), t)


def _c_pose(t, u):
    x, y = _c_path(t)
    p = F.Pose(x, y, YAW)
    p.pitch = _pitch(t)
    p.spine = [2.0, 3.0, 2.0 + 0.6 * math.sin(2.0 * math.pi * t / 3.8)]
    p.neck = 2.0
    p.head = -0.80 * p.pitch + 4.0 + 1.2 * noise1(t * 0.2, 5)
    ang = BOAT.angle(t)
    for s, fx in (("R", FOOT_F), ("L", FOOT_B)):
        wx, wy = BOAT.to_world((fx, deck_l(fx)), t)
        p.legs[s] = {"ik": (wx, wy - 0.043 * BODY.height), "pitch": -ang, "toe": 0.0, "abd": 3.0}
    p.arms["R"] = dict(sh=-2.0, abd=7.0, elbow=16.0, wrist=4.0, grip=0.45)
    p.arms["L"] = dict(sh=-6.0, abd=6.0, elbow=14.0, wrist=6.0, grip=0.4)
    p.eyes = dict(open=1.0, glow=0.95, look=0.0)
    return p


def _line_entry(t):
    return (_line_x0(0.0, t) + 40.0, 0.0)


@functools.lru_cache(maxsize=1)
def _client():
    A = Actor(BODY, cast.client(), x=-612.0, ground=1e6, facing=YAW, seed=12, name="client")
    A.free(14.0, _c_path, _c_pose, at=-1.5)
    # where he looks: the line where it goes into the water; up the line when it goes tight;
    # down at the rail; the hose; up the line again while he cranks
    A.look_at(-1.5, T_TIGHT - 0.15, _line_entry, fade=0.4, amount=0.9)
    A.look_at(T_TIGHT + 0.05, 3.75, lambda t: BOAT.sheave(t), fade=0.25, amount=0.7)
    A.look_at(3.95, 4.75, lambda t: BOAT.to_world((CIGAR_X, rail_top_l(CIGAR_X)), t), fade=0.3, amount=1.0)
    A.look_at(5.05, 5.30, lambda t: (_c_path(t)[0] + 48.0, _c_path(t)[1] - 40.0), fade=0.18, amount=0.8)  # the knife
    A.look_at(5.55, 6.45, lambda t: BOAT.to_world((CUT_X, rail_top_l(CUT_X)), t), fade=0.25, amount=1.0)
    A.look_at(6.75, 12.0, lambda t: (BOAT.sheave(t)[0], BOAT.sheave(t)[1] + 260.0), fade=0.5, amount=0.8)
    A.blink(2.72)
    A.blink(6.62, dur=0.3)
    A.blink(8.4)
    return A


@functools.lru_cache(maxsize=256)
def _base_pose(t):
    return _client().pose(t)


def _base_sk(t):
    return F.solve(_base_pose(round(t, 5)), BODY)


# --- his right hand: the cigar, the knife
def _mouth(sk):
    return F.head_point(sk, 0.86, 0.22, front_x=0.16, front_y=0.20)


def _cigar_rail(t):
    """World centre of the cigar lying on the top rail."""
    return BOAT.to_world((CIGAR_X, rail_top_l(CIGAR_X) - 3.6), t)


def _cut_pt(t):
    return BOAT.to_world((CUT_X + 3.0, rail_top_l(CUT_X) - 5.0), t)


def _knife_sheath(t):
    """(kw, points) of the sheathed knife on his belt (from the pose without arm IK)."""
    kw = K.knife_on_belt(_base_sk(t))
    return kw, K.knife_points(kw)


DRAW_LEN = 151.0 * K.KNIFE_S        # blade length: how far the handle travels to clear it


def _r_hand(t):
    """(target for the middle of his right fist (world) or None, weight)."""
    sk = _base_sk(t)
    rest = (sk.j["pelvis"][0] + 20.0, sk.j["pelvis"][1] + 60.0)
    if t < 3.55 or t > 12.0:
        return None, 0.0
    m = _mouth(sk)
    at_mouth = (m[0] - 6.0, m[1] + 8.0)
    rail = _cigar_rail(t)
    on_rail = (rail[0] - 4.0, rail[1] - 10.0)
    if t < T_TAKE:
        w = ss(3.55, T_TAKE - 0.05, t)
        return at_mouth, w
    if t < T_SET:
        u = ease("inout", (t - T_TAKE) / (T_SET - T_TAKE))
        mid = (lerp(at_mouth[0], on_rail[0], 0.5) + 30.0, lerp(at_mouth[1], on_rail[1], 0.5))
        a = lerp(at_mouth, mid, u) if u < 0.5 else None
        p = (lerp(lerp(at_mouth[0], mid[0], u), lerp(mid[0], on_rail[0], u), u),
             lerp(lerp(at_mouth[1], mid[1], u), lerp(mid[1], on_rail[1], u), u))
        return p, 1.0
    if t < 4.70:
        return (on_rail[0], on_rail[1] - 6.0 * ss(4.60, 4.70, t)), 1.0
    kw, kp = _knife_sheath(t)
    grip = kp["grip"]
    hd = kp["handle_dir"]
    if t < T_THEN:
        # the hand drifts back to his side
        w = 1.0 - ss(4.70, 5.02, t)
        p = (lerp(rest[0], on_rail[0], w), lerp(rest[1], on_rail[1] - 6.0, w))
        return p, max(w, ss(4.95, T_THEN, t) * 0.0)
    if t < T_GRAB:
        u = ease("inout", (t - T_THEN) / (T_GRAB - T_THEN))
        p = (lerp(rest[0], grip[0], u), lerp(rest[1], grip[1], u))
        return p, ss(T_THEN - 0.05, T_THEN + 0.12, t)
    if t < T_OUTK:
        u = ease("in", (t - T_GRAB) / (T_OUTK - T_GRAB))
        return (grip[0] + hd[0] * DRAW_LEN * u, grip[1] + hd[1] * DRAW_LEN * u), 1.0
    out = (grip[0] + hd[0] * DRAW_LEN, grip[1] + hd[1] * DRAW_LEN)
    sh = sk.j["shoulder_R"]
    raised = (sh[0] + 95.0, sh[1] + 40.0)
    cut = _cut_pt(t)
    over = (cut[0] - 70.0, cut[1] - 150.0)
    cocked = (cut[0] - 92.0, cut[1] - 175.0)
    through = (cut[0] + 36.0, cut[1] + 70.0)
    low = (sk.j["pelvis"][0] + 30.0, sk.j["pelvis"][1] + 85.0)
    keys = [(T_OUTK, out), (5.78, raised, "out"), (5.90, over, "inout"), (5.975, cocked, "inout"),
            (6.045, through, "in"), (6.16, (through[0] + 14.0, through[1] + 22.0), "out"),
            (6.75, low, "inout"), (12.0, low)]
    return LIB_track2(keys, t), 1.0


def LIB_track2(keys, t):
    """track() for 2D points."""
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


def _l_hand(t):
    """Target for his left fist: the crank handle from [mine]."""
    if t < T_MINE - 0.05:
        return None, 0.0
    g = crank_grip(t)
    return (g[0] - 4.0, g[1] - 2.0), ss(T_MINE - 0.05, T_CRANK - 0.05, t)


def _apply_arm(p, side, target, w, grip):
    if target is None or w <= 0.0:
        return
    q = arm_ik(p.copy(), side, target, HB)
    for k in ("sh", "elbow"):
        p.arms[side][k] = lerp(p.arms[side][k], q.arms[side][k], w)
    p.arms[side]["wrist"] = lerp(p.arms[side].get("wrist", 0.0), 0.0, w)
    if grip is not None:
        p.arms[side]["grip"] = lerp(p.arms[side].get("grip", 0.3), grip, w)


@functools.lru_cache(maxsize=96)
def _solved(t):
    p = _base_pose(t).copy()
    tr, wr = _r_hand(t)
    _apply_arm(p, "R", tr, wr, 0.9)
    tl, wl = _l_hand(t)
    _apply_arm(p, "L", tl, wl, 0.95)
    return F.solve(p, BODY)


def client_sk(t):
    return _solved(round(t, 5))


def _ember(t):
    """The cigar's glow (0.5 idle .. 1.5 drawn on)."""
    e = 0.55 + 0.08 * noise1(t * 0.9, 9)
    e += 0.85 * LIB.bump(t, T_PUFF - 0.3, T_PUFF + 0.35, T_PUFF + 0.6, T_PUFF + 2.2)
    e += 0.7 * LIB.bump(t, T_PUFF2 - 0.12, T_PUFF2 + 0.12, T_PUFF2 + 0.25, T_PUFF2 + 1.6)
    return e


def _client_look(t):
    lk = cast.client(ember=_ember(t), coat_flow=0.16 + 0.08 * noise1(t * 0.5, 4))
    if t >= T_TAKE:
        lk.extras = []
    return lk


def _knife_in_hand(t, sk):
    """(grip, angle (deg, blade direction), drawn) of the knife once his hand has it."""
    kw, kp = _knife_sheath(t)
    hd = kp["handle_dir"]
    a_sheath = math.degrees(math.atan2(-hd[1], -hd[0]))
    h = sk.j["hand_R"]
    a = LIB.track([(T_GRAB, a_sheath), (T_OUTK, a_sheath), (5.78, -78.0, "inout"), (5.90, -60.0, "inout"),
                   (5.975, -95.0, "inout"), (6.045, 35.0, "in"), (6.16, 62.0, "out"), (6.75, 98.0, "inout"),
                   (12.0, 98.0)], t)
    a += 2.0 * noise1(t * 0.7, 21) * ss(6.8, 7.4, t)
    return h, a


# ============================================================================= camera
def _herm(t, t0, y0, v0, t1, y1, v1):
    D = t1 - t0
    u = clamp((t - t0) / D)
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1
    h10 = u ** 3 - 2 * u ** 2 + u
    h01 = -2 * u ** 3 + 3 * u ** 2
    h11 = u ** 3 - u ** 2
    return h00 * y0 + h10 * D * v0 + h01 * y1 + h11 * D * v1


T_A = -0.625                        # first handle frame
T_SETTLE = 2.7                      # the rise has settled on the deck
Z_RISE = 0.55                       # s11's zoom at the cut
Y0, V0 = 2300.0, 1900.0
DECK_CAM = (-470.0, -385.0, 0.86)


def _logz(a, b, u):
    return math.exp(lerp(math.log(a), math.log(b), u))


def _rise(t):
    z = _logz(Z_RISE, DECK_CAM[2], ease("inout", clamp((t - 0.45) / (T_SETTLE - 0.45))))
    y = _herm(t, T_A, Y0, -V0, T_SETTLE, DECK_CAM[1], 0.0)
    xl = _line_x0(y + (H / 2) / Z_RISE, t) + (540.0 - 470.0) / Z_RISE        # the line at x 470 at the bottom
    x = lerp(xl, DECK_CAM[0], ease("inout", clamp((t - 0.5) / (T_SETTLE - 0.5))))
    return x, y, z


def _deck(t):
    x = LIB.track([(T_SETTLE, DECK_CAM[0]), (4.8, -478.0, "inout"), (5.9, -505.0, "inout"), (7.3, -500.0)], t)
    y = LIB.track([(T_SETTLE, DECK_CAM[1]), (4.8, -400.0, "inout"), (5.9, -455.0, "inout"), (7.3, -450.0)], t)
    z = LIB.track([(T_SETTLE, DECK_CAM[2]), (4.8, 0.90, "inout"), (5.9, 1.04, "inout"), (7.3, 1.02)], t)
    return x, y, z


def _follow(t):
    """Down over the side with the severed end: it leads the frame, then sinks away above us
    as the camera keeps going down."""
    e = hose_end(min(t, T_END + 0.15))
    z = LIB.track([(T_TILT, 1.02), (8.6, 0.86, "inout"), (T_END, 0.80, "inout")], t)
    lead = LIB.track([(T_TILT, 0.0), (8.4, 120.0, "inout"), (T_END, 520.0, "in")], t)
    return e[0] + 30.0, e[1] + lead, z


def _cam3(t):
    if t < T_SETTLE:
        return _rise(t)
    if t < T_TILT:
        return _deck(t)
    a = _deck(T_TILT)
    b = _follow(t)
    w = ease("inout", clamp((t - T_TILT) / 1.5))
    return lerp(a[0], b[0], w), lerp(a[1], b[1], w), _logz(a[2], b[2], w)


def _shake(t):
    a = 0.0
    for tk, s, d in ((T_TIGHT, 3.0, 0.28), (T_CUT, 2.2, 0.2)):
        if t >= tk:
            a += s * math.exp(-(t - tk) / d)
    return a


def camera(t):
    x, y, z = _cam3(t)
    cam = Camera(x, y, z)
    a = _shake(t)
    if a > 0.05:
        k = a / z
        cam = Camera(x + k * noise1(t * 31.0, 3), y + k * noise1(t * 29.0, 7), z)
    return cam.shaken(t, amp=1.2, rot_amp=0.03, freq=0.35, seed=12)


# ============================================================================= drawing helpers
def _draw_cigar(ctx, f, c, ang, ember, smoke_t=None):
    """The cigar as a prop: ink capsule (31 px) with its ember (emissive) at the +ang end."""
    L = 0.36 * BODY.head * BODY.height
    r = 0.006 * BODY.height
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    a = (c[0] - ca * L / 2, c[1] - sa * L / 2)
    b = (c[0] + ca * L / 2, c[1] + sa * L / 2)
    draw.capsule(ctx, a, b, r, r * 0.92)
    ctx.set_source_rgb(*INK)
    ctx.fill()
    with f.emit() as G:
        draw.circle(G, b, r * (0.8 + 0.4 * ember))
        G.set_source_rgba(*LIGHT, min(1.0, 0.6 + 0.4 * ember))
        G.fill()
    draw.circle(ctx, b, r * 0.75)
    ctx.set_source_rgba(*mix(LIGHT, (1.0, 0.9, 0.7), 0.4), clamp(0.55 + 0.35 * ember))
    ctx.fill()
    return b


def _smoke(f, t, src, t0, alpha=0.18):
    """A thin wisp of cigar smoke curling up from the ember on the rail (moonlit)."""
    if t < t0:
        return
    k = ss(t0, t0 + 0.8, t)
    col = mix(PAL.moon, PAL.sky_bottom, 0.3)
    with f.light(blur=3.0) as A:
        for j in range(3):
            pts = []
            ph = t * 0.9 + 2.1 * j
            for i in range(22):
                v = i / 21.0
                hgt = 230.0 * v
                x = src[0] + (14.0 + 8.0 * j) * math.sin(3.0 * v + ph) * v + 40.0 * v * v + 6.0 * noise1(v * 3 + t * 0.5, j)
                pts.append((x, src[1] - 4.0 - hgt))
            A.new_path()
            draw.smooth(A, pts, close=False)
            A.set_line_width(1.6 + 2.2 * j)
            A.set_source_rgba(*col, alpha * k / (1.0 + j))
            A.stroke()


# ============================================================================= render
def render(f, t, T):
    cam = f.set_camera(camera(t))
    top_y = cam.view_rect(0)[1]
    # the night look shared with s14/s15: sea_world with the lib's moon; while we are still
    # rising from s11 the water body is re-laid with the compressed night-water gradient
    rising = _vscale(t) < 0.999
    S.sea_world(f, t, moon=MOON, moon_r=MOON_R, dusk=0.0, veil=0.25, glow=not rising)
    if rising:
        _water(f, t)
        S.surface_glow(f, t, bright=BRIGHT)
    # moonlight hanging in the water
    atmos.underwater_rays(f, surface_y=0.0, t=t, spacing=190.0, angle=95.0, fan=8.0, length=2200.0,
                          intensity=0.2, density=0.55, seed=14, blur=18, color=mix(PAL.moon, PAL.surface, 0.5))
    # --- action plane
    sk = client_sk(t)
    with f.layer() as L:
        _stroke(L, _line_pts(t), LINE_W, PALE)
        BOAT.draw(L, t, pump_angle=pump_angle(t), winch_angle=winch_angle(t), hose=False, hook=False,
                  rail=False)
        _draw_belt(L, t)
        deck = _hose_deck_pts(t)
        _stroke(L, deck, HOSE_W, RED, cap=cairo.LINE_CAP_BUTT if t >= T_CUT else cairo.LINE_CAP_ROUND)
        F.draw_figure(f, sk, _client_look(t), L)
        if t < T_GRAB:
            S.draw_knife(L, **K.knife_on_belt(sk))
        else:
            kw = K.knife_on_belt(sk)
            L.save()
            L.translate(kw["x"], kw["y"])
            L.rotate(math.radians(kw["angle"]))
            L.scale(-kw["s"], kw["s"])
            L.new_path()
            L.append_path(S.shape("sheath", __import__("films.salvage.sets_props", fromlist=["_sheath"])._sheath))
            L.restore()
            L.set_source_rgb(*INK)
            L.fill()
            g, a = _knife_in_hand(t, sk)
            S.draw_knife(L, g[0], g[1], angle=a, s=K.KNIFE_S, flip=False)
        if T_TAKE <= t < T_SET:
            h = sk.j["fingers_R"]
            _draw_cigar(L, f, h, -10.0, 0.6)
        _draw_rail(L, t)
        if t >= T_SET:
            _draw_cigar(L, f, _cigar_rail(t), 4.0, 0.5 + 0.06 * noise1(t * 1.3, 2))
        out = _hose_out_pts(t)
        _stroke(L, out, HOSE_W, RED, cap=cairo.LINE_CAP_BUTT if t >= T_CUT else cairo.LINE_CAP_ROUND)
    S.water_front(f, t, alpha=0.08, bright=BRIGHT)
    BOAT.draw_lights(f, t, lantern=1.0, window=0.5, masthead=1.0)
    if t >= T_SET:
        _smoke(f, t, _cigar_rail(t), T_SET + 0.2)
    if T_OUTK - 0.1 < t < T_GLINT + 0.5:
        g, a = _knife_in_hand(t, sk)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        gp = (g[0] + ca * 0.46 * 164.0 - sa * 0.46 * -8.0, g[1] + sa * 0.46 * 164.0 + ca * 0.46 * -8.0)
        S.knife_glint(f, gp, t, T_GLINT, dur=0.35, size=0.8)
    if top_y > -400:
        atmos.marine_snow(f, density=0.5 * ss(-400.0, 400.0, top_y), t=t, seed=12, sink=5.0, current=(9.0, 0.0),
                          alpha=0.6)
    f.post["vignette"] = lerp(f.post["vignette"], 0.42, 0.5)


def motion_blur(t, T):
    if 5.96 < t < 6.12:
        return 3
    return 1


def cues(T):
    return [
        Cue(-0.6, "rising through night water toward the surface: muffled rush", gain_db=-12, dur=1.6),
    ]
