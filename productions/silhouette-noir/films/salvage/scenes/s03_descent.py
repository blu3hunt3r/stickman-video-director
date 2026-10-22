"""s03 · SALVAGE: the title on the waterline, then the long way down (14.0 s, mostly wordless).

IN  (scroll 'up' from s02, 1.25 s): split composition at late dusk, waterline at screen
    y ~760 (the camera still tilting down, settling by 0.45). Above: the stern of the boat,
    the ladder over the transom, the davit and lantern, the moon at upper right. Below: aqua.
    The diver is on the ladder (profile, facing the boat) at screen x ~620, the red hose
    looping from the stern to his helmet.

Beats (scene-local s):
  0.30       he lets go of the rail and drops; 0.64 his boots hit the water: crown splash,
             spray, a burst of bubbles from the suit; the helmet goes under at ~2.0
  1.5-2.6    S A L V A G E: hand-cut PAPER letters (150 px tall on screen) drop one by one
             (0.12 s apart) onto the waterline, each with a little splash, and float there
             bobbing: crisp above the water, refracted and wobbling below it
  2.4-6.0    sinking, he turns from profile to face us
  5.0        the camera starts down after him; the title slides up out of frame; zoom out
  6-10       the descent column: rock shelves slide past, the dusk rays thin out and die
             (gone by ~9.6), marine snow thickens, the water darkens toward ink
  8.0-10.5   a school of fish sweeps across him, parting around his helmet
  10.7-11.3  he reaches up to the helmet lamp; CLICK at 11.30 (stutter, then on)
  [Meridian@10.8] L6 begins
  11.6-12.6  the beam finds the silt far below: the spot lands on [calm@12.57]
  13.4-14.5  the volume of the beam and its glare dim so the spot carries the flatten
OUT (flatten, 1.0 s): ink-dark water, the diver at upper centre looking down (helmet at
    ~(540, 380), pelvis ~(540, 520)), his beam straight down to a bright elliptical spot on
    the silt centred at screen (540, 1250), ~260 x 120, drifting up ~45 px/s (the s04 moon
    rises from there). The red hose runs up from his helmet out of the top of frame.

Depth is compressed: the camera covers ~4.4k world px, a 'virtual depth' (x ~1.8 at the
end) drives the water colour, and the seabed is the sets' DeepWorld drawn through a camera
shifted down by DELTA so the real silt (~9000) sits under him at Y_S.
"""
import math

import cairo
import numpy as np

from engine import atmos, bass, costume, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.creatures import FishSchool
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import PAPER
from engine.timing import Cue
from films.salvage import cast
from films.salvage import sets as S
from films.salvage.scenes import _lib_s01_s03_s16 as LIB

PAL = S.PAL
INK = PAL.ink
D2R = math.pi / 180.0

# ============================================================================= timing
T_LET = 0.30                    # lets go of the rail
G_AIR = 3000.0                  # px/s^2
T_TITLE = 1.50                  # first letter starts falling
TITLE_GAP = 0.12
TITLE_FALL = 0.40
T_DESC = 5.0                    # the camera starts down
T_CLICK = 11.30                 # lamp switch
T_END = 14.0


def _beats(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:
            return d
    return dict(mer=at("Meridian", 10.821), calm=at("calm", 12.574), night=at("night", 13.166))


# ============================================================================= the boat
BOAT = S.Boat()
DUSK = 0.25
BRIGHT = lerp(0.62, 1.0, DUSK)
MOON = (612.0, 598.0)           # screen x, height above the horizon (the waterline here):
MOON_R = 74.0                   # ... right behind his helmet while he stands on the ladder


def _rung(t, i):
    return BOAT.ladder(t)["rungs"][i]


def _rail_grip(t, dx):
    """A hand-hold on the stern rail near the ladder (world)."""
    x = BOAT.ladder(t)["top"][0] - 12.0 + dx
    return (x, BOAT.deck_y(x, t) - S.RAIL_H + 6.0)


# ============================================================================= the diver
H_PEL = 300.0                   # pelvis -> helmet top (front or profile)
_R1 = _rung(0.0, 0)             # upper boot on the top rung (~180 above the water), lower on rung 1
X_L = _R1[0] + 60.0             # pelvis while on the ladder (standing tall at the stern)
Y_L = _R1[1] - 288.0
G_FALL = 2600.0                 # the drop (boots already dragging in the water)
Y_E = -40.0                     # pelvis height when his body hits the water (the splash)
TAU_E = math.sqrt(2.0 * (Y_E - Y_L) / G_FALL)
T_HIT = T_LET + TAU_E           # ~0.78
V_E = G_FALL * TAU_E            # entry speed (~1240 px/s)
K_W = 1.7                       # water braking (1/s)
T_TOE = T_LET + math.sqrt(2.0 * 118.0 / G_FALL)     # the lower boot touches the water


def _v_term(t):
    """Steady sink speed (px/s): slow on the split, heavier for the descent, easing off
    above the silt."""
    return 150.0 + 270.0 * smoothstep(5.0, 7.5, t) - 220.0 * smoothstep(11.6, 13.8, t)


_DT = 1.0 / 240.0
_TGRID = np.arange(T_HIT, 15.2 + _DT, _DT)


def _build_sink():
    tau = _TGRID - T_HIT
    vt = np.array([_v_term(float(s)) for s in _TGRID])
    v = vt + (V_E - 150.0) * np.exp(-K_W * tau)
    y = Y_E + np.concatenate([[0.0], np.cumsum(0.5 * (v[1:] + v[:-1]) * _DT)])
    return y


_SINK = _build_sink()


def pelvis_y(t):
    if t <= T_LET:
        return Y_L + 1.5 * math.sin(2.1 * t)
    if t <= T_HIT:
        tau = t - T_LET
        return Y_L + 0.5 * G_FALL * tau * tau
    i = (min(t, _TGRID[-1] - 1e-6) - T_HIT) / _DT
    k = int(i)
    u = i - k
    return float(_SINK[k] * (1 - u) + _SINK[min(k + 1, len(_SINK) - 1)] * u)


def pelvis_x(t):
    push = 46.0 * ease("out", (t - T_LET) / 0.6) if t > T_LET else 0.0
    drift = 70.0 * smoothstep(2.0, 9.0, t) + 9.0 * math.sin(0.41 * t + 0.6) * smoothstep(1.5, 3.5, t)
    return X_L + push + drift


def _path(t):
    return (pelvis_x(t), pelvis_y(t))


def _yaw(t):
    return lerp(180.0, 90.0, ease("inout", (t - 2.4) / 3.6))


def _ladder_pose(t):
    p = F.Pose(X_L, Y_L, 180.0)
    r1, r2 = _rung(t, 0), _rung(t, 1)
    p.legs["L"] = {"ik": (r1[0] + 17.0, r1[1] - 19.0), "pitch": 4.0, "toe": 0.0, "abd": 3.0}
    p.legs["R"] = {"ik": (r2[0] + 16.0, r2[1] - 19.0), "pitch": 0.0, "toe": 0.0, "abd": 3.0}
    p.pitch = -5.0
    p.spine = [1.0, 1.0, 2.0]
    p.head = 2.0 + 1.5 * math.sin(1.7 * t)
    for s in ("L", "R"):
        p.arms[s] = dict(sh=48.0, abd=8.0, elbow=24.0, wrist=0.0, grip=0.95)
    p.eyes = dict(open=1.0, glow=1.0, look=0.0)
    return p


def _drop_pose(t):
    """Dropping and sinking: legs together, the water shoves his arms up as he plunges, then
    a heavy relaxed hang."""
    p = F.Pose(0.0, 0.0, _yaw(t))
    tau = t - T_LET
    up = smoothstep(T_HIT - 0.05, T_HIT + 0.22, t) * (1.0 - smoothstep(T_HIT + 0.5, T_HIT + 2.1, t))
    air = smoothstep(T_LET, T_LET + 0.2, t) * (1.0 - smoothstep(T_HIT - 0.05, T_HIT + 0.15, t))
    wob = smoothstep(1.8, 4.0, t)
    br = math.sin(2 * math.pi * t / 3.9)
    for s, sg in (("L", 1.0), ("R", -1.0)):
        a = p.arms[s]
        sh = 8.0 + 5.0 * noise1(t * 0.35, 11 + sg)
        sh = lerp(sh, 34.0 + 6.0 * sg, air)
        a["sh"] = lerp(sh, 52.0 + 10.0 * sg, up)
        a["abd"] = lerp(22.0 + 5.0 * noise1(t * 0.3, 21 + sg) + 2.0 * br, 30.0, max(up, air))
        a["elbow"] = lerp(26.0 + 6.0 * noise1(t * 0.28, 31 + sg), 44.0, max(up, air))
        a["wrist"] = 8.0
        a["grip"] = 0.2
    for s, ph in (("L", 0.0), ("R", 1.9)):
        p.legs[s] = dict(hip=lerp(3.0, 7 + 5 * math.sin(t * 0.9 + ph), wob), abd=lerp(2.0, 6.0, wob),
                         knee=lerp(5.0, 14 + 7 * math.sin(t * 0.9 + ph + 0.7), wob), ankle=-10, toe=0)
    p.pitch = -7.0 * smoothstep(0.0, 0.3, tau) * (1.0 - smoothstep(0.6, 1.9, tau)) + 1.5 * noise1(t * 0.25, 41)
    p.spine = [0.8 * br, 0.0, -0.6 * br]
    p.head = 3.0 + 2.0 * noise1(t * 0.2, 51) + 9.0 * smoothstep(6.0, 9.0, t) + 16.0 * smoothstep(11.2, 12.4, t)
    p.head_roll = 1.5 * noise1(t * 0.22, 61)
    p.eyes = dict(open=1.0, glow=1.0, look=0.0)
    return p


def _pose(t, u):
    if t <= T_LET:
        return _ladder_pose(t)
    w = smoothstep(T_LET, T_LET + 0.2, t)
    d = _drop_pose(t)
    if w >= 1.0:
        return d
    a = _ladder_pose(T_LET)
    d.x, d.y = pelvis_x(t), pelvis_y(t)
    a.x, a.y = d.x, d.y
    return F.blend(a, d, w, cast.DIVER)


def _make_diver():
    A = Actor(cast.DIVER, cast.diver(), x=X_L, ground=1e6, facing=180, seed=9, name="diver")
    A.free(16.5, _path, _pose, at=-1.0)
    return A


DIVER0 = _make_diver()          # no reaches: the lamp target
DIVER = _make_diver()
_LAMP0 = LIB.Sampled(lambda t: costume.helmet_lamp(DIVER0.skeleton(t))[0], 10.0, 12.2, 48)
DIVER.reach("L", -2.0, T_LET - 0.04, lambda t: _rail_grip(t, -22.0), fade=0.12, grip=1.0)
DIVER.reach("R", -2.0, T_LET - 0.02, lambda t: _rail_grip(t, 8.0), fade=0.12, grip=1.0)
DIVER.reach("R", 10.98, 11.36, lambda t: (_LAMP0(t)[0] - 10.0, _LAMP0(t)[1] - 6.0), fade=0.26, grip=0.6)

_INLET = LIB.Sampled(lambda t: costume.helmet_inlet(DIVER.skeleton(t)), -1.0, 15.0, 120)
_VALVE = LIB.Sampled(lambda t: LIB.helmet_valve(DIVER.skeleton(t)), -1.0, 15.0, 60)
_LAMP = LIB.Sampled(lambda t: costume.helmet_lamp(DIVER.skeleton(t))[0], -1.0, 15.0, 60)
_CHEST = LIB.Sampled(lambda t: DIVER.skeleton(t).j["chest"], -1.0, 15.0, 60)


def _suit_src(te):
    """Where the plunge's air comes out: around his legs, never above the surface."""
    x, y = pelvis_x(te), pelvis_y(te) + 90.0
    return (x + 10.0, max(y, S.sea_y(x, te) + 40.0))


# ============================================================================= the hose
def _hose_current(t, x, y):
    if y < S.sea_y(x, t) - 4.0:
        return (0.0, 1100.0)                       # in the air it falls
    return (30.0 + 12.0 * math.sin(0.37 * t + y / 900.0), 0.0)


def _hose_len(t):
    """Paid out by the tender: the straight distance plus a hanging loop of slack."""
    ex, ey = BOAT.hose_exit(t)
    ix, iy = _INLET(t)
    d = math.hypot(ix - ex, iy - ey)
    return d * (1.0 + 0.05 * smoothstep(0.0, 3000.0, d)) + 130.0 - 40.0 * smoothstep(0.0, 1500.0, d)


HOSE = LIB.hose_rope(BOAT.hose_exit, _INLET, 600.0, n=52, t0=-1.0, t1=14.8, current=_hose_current,
                     length_fn=_hose_len, gravity=(0.0, 120.0), drag=1.8, stiffness=0.3, iters=12)


# ============================================================================= camera
Z0 = 0.85
CX0 = X_L - 80.0 / Z0                     # the diver at screen x ~620 on the ladder
CY0 = (H / 2 - 760.0) / Z0                # waterline at screen y 760
Z_MID, Z_END = 0.48, 0.50
SY_MID = 860.0                            # pelvis screen y while descending
SY_END = 520.0                            # ... and at the end (the camera tilts down to the silt)


def _zoom(t):
    z = Z0
    if t > T_DESC:
        z = math.exp(lerp(math.log(Z0), math.log(Z_MID), ease("inout", (t - T_DESC) / 4.4)))
    if t > 10.4:
        z *= math.exp(lerp(0.0, math.log(Z_END / Z_MID), ease("inout", (t - 10.4) / 3.2)))
    return z


_SY5 = H / 2 + (pelvis_y(T_DESC) - CY0) * Z0


def _cam_y(t):
    if t < 0.45:
        u = clamp((t + 0.625) / 1.075)
        return CY0 - 170.0 * (1.0 - u) ** 3
    if t <= T_DESC:
        return CY0
    z = _zoom(t)
    sy = lerp(_SY5, SY_MID, ease("inout", (t - T_DESC) / 4.2))
    sy = lerp(sy, SY_END, ease("inout", (t - 10.8) / 2.9))
    follow = pelvis_y(t) - (sy - H / 2) / z
    return lerp(CY0, follow, smoothstep(T_DESC, T_DESC + 1.3, t))


def _cam_x(t):
    if t <= T_DESC:
        return CX0
    tx = pelvis_x(t) + 2.0
    return lerp(CX0, tx, smoothstep(T_DESC, T_DESC + 4.0, t))


def camera(t):
    return Camera(_cam_x(t), _cam_y(t), _zoom(t))


# the seabed: the spot (straight below the lamp) lands at screen y 1250 at t = T_END
Y_S = _cam_y(T_END) + (1250.0 - H / 2) / _zoom(T_END)
DELTA = S.seabed_y(pelvis_x(T_END), 0.0) - Y_S


# ============================================================================= water colour
def _vdepth(y):
    """Virtual depth: the compressed descent reads as the full 27 m."""
    y = max(y, 0.0)
    return y * (1.0 + 0.85 * smoothstep(500.0, 4400.0, y))


def _wcol(y, t):
    """Water colour at world depth y and time t: the physical colour at the virtual depth,
    lifted toward the house haze while descending (so silhouettes read against it), then
    sinking toward ink near the bottom."""
    v = _vdepth(y)
    c = S.water_at(v, BRIGHT)
    h = 0.5 * smoothstep(5.3, 7.0, t) * (1.0 - 0.6 * smoothstep(9.5, 12.5, t))
    if h > 0.0:
        c = S.mix(c, S.haze_at(v, 0.5 + 0.45 * smoothstep(9.0, 13.0, t)), h)
    dk = 0.5 * smoothstep(10.5, 13.5, t)
    if dk > 0.0:
        c = S.mix(c, INK, dk)
    return c


def _water(f, t):
    """The water section below the (wavy) surface, coloured by virtual depth."""
    x0, y0, x1, y1 = f.cam.view_rect(200)
    if y1 < -60:
        return
    ya, yb = max(y0 - 50, -60.0), max(y1, 0.0) + 10
    n = 16
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


# ============================================================================= the deep world
# The sets' world is built at real depth; ours is compressed. The rock shelves of the
# descent column are drawn through a camera DELTA_REEF deeper than ours, the seabed through
# one DELTA deeper (so the real silt lands at Y_S under him).
DELTA_REEF = 900.0
BED = S.DeepWorld(wreck=None, reef=False, debris=False, front=())
COLUMN = S.DeepWorld(wreck=None, reef=S.REEF + S.REEF_FRONT, debris=False, front=())


def _view(f, cam, t, shift):
    f.set_camera(Camera(cam.x, cam.y + shift, cam.zoom))
    v = S.View(f, murk=0.55, down_fog=1.15)
    v.bg = lambda Y: _wcol(Y - shift, t)
    return v


def _paint(f, world, t, cam, shift, a, front=False, strips=True):
    if a <= 0.0:
        return
    view = _view(f, cam, t, shift)
    P = world.painter(f, t, view)
    if not strips:
        P.items = [it for it in P.items if it[0] not in S.STRIPS]
    c = f.ctx
    c.push_group()
    if front:
        P.render(f, view, True, bins=((-1e9, 16.0),))
    else:
        P.render(f, view, False)
    c.pop_group_to_source()
    c.paint_with_alpha(a)
    f.set_camera(cam)


def _reef_a(t):
    return smoothstep(5.9, 7.4, t) * (1.0 - smoothstep(11.4, 12.6, t))


def _bed_a(t):
    return smoothstep(10.6, 12.0, t)


# ============================================================================= the splash
SPRAY = S.mix(PAL.moon, PAL.surface, 0.35)


def _splash(f, t, xs, t0, n, scale, seed):
    """Spray thrown up at (xs, surface) at t0: ballistic droplets, streaked along their
    velocity, falling back into the sea."""
    tau0 = t - t0
    if tau0 < 0.0 or tau0 > 1.7 * math.sqrt(scale):
        return
    c = f.ctx
    c.new_path()
    g = 2600.0
    big, small = [], []
    for i in range(n):
        te = 0.22 * scale * hash01(seed, i, 1) ** 1.5
        tau = tau0 - te
        if tau <= 0.0:
            continue
        side = 1.0 if hash01(seed, i, 2) < 0.5 else -1.0
        r0 = hash01(seed, i, 3)
        x0 = xs + side * (10.0 + 70.0 * scale * r0)
        vx = side * (60.0 + 380.0 * hash01(seed, i, 4)) * scale ** 0.5
        vy = -(300.0 + 1050.0 * hash01(seed, i, 5) ** 1.4) * scale ** 0.5
        x = x0 + vx * tau
        y = S.sea_y(x0, t0) + vy * tau + 0.5 * g * tau * tau
        if y > S.sea_y(x, t) + 4.0:
            continue
        r = (1.3 + 4.2 * hash01(seed, i, 6) ** 3) * (0.55 + 0.45 * scale)
        vyt = vy + g * tau
        sp = math.hypot(vx, vyt)
        (big if r > 2.6 else small).append((x, y, r, r * (1.0 + min(sp / 420.0, 2.6)), math.atan2(vyt, vx)))
    for grp, al in ((big, 0.62), (small, 0.9)):
        if not grp:
            continue
        for x, y, r, L, ang in grp:
            c.save()
            c.translate(x, y)
            c.rotate(ang)
            c.scale(L, r)
            c.new_sub_path()
            c.arc(0, 0, 1.0, 0, 2 * math.pi)
            c.restore()
        c.set_source_rgba(*SPRAY, al)
        c.fill()


def _crown(f, t, xs, t0, scale, seed):
    """The crown of the splash: tongues of water thrown up around the plunge, leaning
    outward, then sinking back into the sea."""
    tau = t - t0
    Tc = 0.8 * math.sqrt(scale)
    if tau <= 0.0 or tau >= Tc:
        return
    c = f.ctx
    k = tau / Tc
    nf = 7
    for j in range(nf):
        u = j / (nf - 1) - 0.5                      # -0.5 .. 0.5 across the crown
        side = 1.0 if u >= 0 else -1.0
        h = hash01(seed, j, 1)
        bx = xs + u * 2.0 * (40.0 + 95.0 * ease("out", k)) * scale
        L = scale * (90.0 + 170.0 * h) * (1.0 - 0.5 * abs(u) * 2.0) * math.sin(math.pi * min(1.0, k * 1.15)) ** 0.8
        if L < 4.0:
            continue
        ang = -90.0 + u * 2.0 * (14.0 + 22.0 * h) + 5.0 * (hash01(seed, j, 2) - 0.5)
        S.blade(c, (bx, S.sea_y(bx, t) + 8.0), ang, L, (10.0 + 6.0 * h) * scale, 3.0,
                bend=side * (6.0 + 24.0 * k), n=8)
    c.set_source_rgba(*SPRAY, 0.72 * (1.0 - smoothstep(0.45, 1.0, k)))
    c.fill()


def _foam(f, t, xs, t0, width, seed, k=1.0):
    """White water churned up on the surface, spreading and fading, the aerated cloud under
    it and ripples running away along the surface."""
    tau = t - t0
    if tau < 0.0 or tau > 2.8:
        return
    a = (1.0 - smoothstep(0.4, 2.7, tau)) * k
    w = width * (0.35 + 0.9 * ease("out", tau / 1.4))
    pts = S.sea_pts(xs - w, xs + w, t, step=6.0)
    top, bot = [], []
    for x, y in pts:
        u = (x - xs) / w
        env = max(0.0, 1.0 - u * u) ** 0.6
        lump = 0.5 + 0.5 * noise1(x / 23.0 + 2.0 * tau, seed)
        top.append((x, y - (2.0 + 7.0 * lump) * env * (1.0 - 0.5 * smoothstep(0.0, 1.5, tau))))
        bot.append((x, y + (3.0 + 6.0 * noise1(x / 31.0 + tau, seed + 3)) * env))
    c = f.ctx
    c.new_path()
    draw.poly(c, top + bot[::-1])
    c.set_source_rgba(*SPRAY, 0.8 * a)
    c.fill()
    with f.light(blur=24) as A:
        draw.ellipse(A, (xs, 90.0 + 80.0 * tau), w * 0.7, 130.0 + 70.0 * tau)
        draw.fill(A, PAL.surface, 0.26 * a)
    with f.light(blur=2.0) as A:
        for sgn in (-1.0, 1.0):
            for j, sp in enumerate((310.0, 200.0)):
                xr = xs + sgn * (w * 0.6 + sp * tau)
                ys = S.sea_y(xr, t)
                S.line(A, [(xr - 24, ys + 1), (xr, ys - 1.5), (xr + 24, ys + 1)], 2.6, PAL.moon,
                       0.5 * a * (1.0 - 0.4 * j))


# ============================================================================= the title
TITLE_H = 142.0 / Z0
TITLE = bass.title_glyphs("SALVAGE", height=TITLE_H, tracking=0.035, seed=3)
TITLE_X = CX0 - 4.0
BELOW = S.mix(PAPER, PAL.surface, 0.42)


def _letter_state(t, i, g):
    """(dy, rot, alpha) of letter i: falls in, plunges, bobs, then floats on the swell."""
    t0 = T_TITLE + TITLE_GAP * i
    if t < t0:
        return None
    u = (t - t0) / TITLE_FALL
    x = TITLE_X + g.pivot[0]
    sea = S.sea_y(x, t)
    tilt0 = (hash01(i, 21) - 0.5) * 30.0
    if u < 1.0:
        dy = -1100.0 * (1.0 - u) ** 2
        rot = tilt0 * (1.0 - u)
    else:
        tau = t - t0 - TITLE_FALL
        dy = 0.26 * TITLE_H * math.exp(-3.4 * tau) * math.sin(2 * math.pi * 1.25 * tau + 0.15)
        rot = bass.settle(t, t0 + TITLE_FALL, amp=-tilt0 * 0.35, freq=1.1, decay=2.6)
        rot += 1.6 * math.sin(1.3 * t + 1.7 * i) * smoothstep(0.0, 1.0, tau)
        rot += math.degrees(math.atan(S.sea_slope(x, t))) * 0.8
    return dy + sea, rot


def _title(f, t):
    vis = t >= T_TITLE and f.cam.y - H / 2 / f.cam.zoom < 260.0
    if not vis:
        return
    c = f.ctx
    x0, y0, x1, y1 = f.cam.view_rect(100)
    surf = S.sea_pts(x0, x1, t, step=8.0)
    phase = 2.6 * t
    for i, g in enumerate(TITLE):
        st = _letter_state(t, i, g)
        if st is None:
            continue
        dy, rot = st
        at = (TITLE_X, 0.0)
        # above the surface: crisp PAPER
        c.save()
        c.new_path()
        c.move_to(x0, y0)
        c.line_to(x1, y0)
        for p in surf[::-1]:
            c.line_to(*p)
        c.close_path()
        c.clip()
        c.new_path()
        g.path(c, at, 0.0, dy, rot)
        c.set_source_rgb(*PAPER)
        c.fill()
        c.restore()
        # below: refracted bands, tinted toward the water
        bh = TITLE_H * 0.17
        for b in range(7):
            ya = b * bh - 6.0
            c.save()
            c.new_path()
            for j, p in enumerate(surf):
                (c.move_to if j == 0 else c.line_to)(p[0], p[1] + max(ya, 0.0))
            for p in surf[::-1]:
                c.line_to(p[0], p[1] + ya + bh + (0.6 if b < 6 else 1e4))
            c.close_path()
            c.clip()
            c.new_path()
            sh = 7.0 * math.sin(1.9 * b + phase + 0.7 * i) + 3.0 * math.sin(3.1 * b - 1.3 * phase)
            g.path(c, at, sh, dy + 2.0 + 1.5 * b, rot, 1.0 + 0.02 * math.sin(phase + b), 1.0)
            c.set_source_rgba(*BELOW, 0.78 - 0.06 * b)
            c.fill()
            c.restore()


def _title_splashes(f, t):
    for i, g in enumerate(TITLE):
        th = T_TITLE + TITLE_GAP * i + TITLE_FALL
        if 0.0 <= t - th < 1.0:
            _splash(f, t, TITLE_X + g.pivot[0], th, 12, 0.35, 70 + i)


# ============================================================================= fish
def _school_path(t):
    cx, cy = _CHEST(min(max(t, 7.0), 11.4))
    u = (t - 9.25) / 1.8
    return (cx + 2300.0 * u / (1.0 + 0.15 * abs(u)), cy - 420.0 * u + 60.0)


SCHOOL = FishSchool(_school_path, n=110, seed=4, size=105.0, spread=(640.0, 240.0), swirl=0.5, wander=0.18,
                    depth=0.4)


def _fish(f, t):
    if not 7.2 < t < 11.4:
        return
    sk_c = _CHEST(t)
    hc = _LAMP(t)
    avoid = [(sk_c[0], sk_c[1] + 30.0, 175.0), (hc[0], hc[1] + 60.0, 120.0)]
    col = S.mix(INK, _wcol(f.cam.y, t), 0.18)
    with f.layer() as L:
        SCHOOL.draw(f, t, L, avoid=avoid, color=col, glint=True)


# ============================================================================= the lamp
def _lamp_on(t):
    if t < T_CLICK:
        return 0.0
    tau = t - T_CLICK
    if tau < 0.07:
        return 0.85
    if tau < 0.13:
        return 0.12
    return min(1.0, 0.75 + 0.25 * smoothstep(0.13, 0.5, tau))


HALF = 8.6                      # beam half angle (deg): the spot is ~260 x 120 px at the cut
SPOT = S.mix(PAL.light, (1.0, 0.97, 0.9), 0.3)


def _dim(t):
    """The beam's volume and glare fade before the flatten so only the spot is left to
    become the paper moon of s04."""
    return 1.0 - 0.85 * smoothstep(12.9, 13.62, t)


def _beam(f, t, b):
    """The lamp's cone, drawn BEHIND him (his silhouette cuts the bright throat of the
    beam), a warm spill around his helmet and shoulders, and the spot on the silt."""
    k = _lamp_on(t)
    if k <= 0.0:
        return None
    ap = _LAMP(t)
    ang = 90.0 + 2.2 * noise1(t * 0.35, 77) * (1.0 - smoothstep(12.6, 13.4, t))
    dim = _dim(t)
    dist = Y_S - ap[1]
    cone = atmos.beam(f, ap, ang, length=max(400.0, dist + 60.0), half_angle=HALF,
                      intensity=0.5 * k * dim, falloff=0.75, soft=0.5, core=0.55, fog=0.4,
                      pool=0.0, dust=0.5 * k * dim, glare=0.0, t=t, seed=5)
    with f.light(blur=40) as A:
        draw.glow_disc(A, (ap[0], ap[1] + 120.0), 420.0, PAL.light, 0.10 * k * dim)
        draw.glow_disc(A, (ap[0], ap[1] + 60.0), 170.0, PAL.light, 0.10 * k * dim)
    _spot(f, t, ap, ang, dist, k * smoothstep(11.6, b["calm"], t))
    return cone


def _spot(f, t, ap, ang, dist, a):
    """The light pool on the silt: a warm flat-topped ellipse where the cone meets the
    floor (y = Y_S); it carries the flatten into s04's moon."""
    if a <= 0.0 or dist <= 0.0:
        return
    cx = ap[0] + dist * math.tan((ang - 90.0) * D2R)
    rx = dist * math.tan(HALF * D2R) * 1.04
    ry = rx * 0.46
    with f.light(blur=5) as A:
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1.0)
        for u, al in ((0.0, 1.0), (0.55, 0.92), (0.8, 0.7), (0.93, 0.28), (1.0, 0.0)):
            g.add_color_stop_rgba(u, *SPOT, 0.86 * a * al)
        A.save()
        A.translate(cx, Y_S)
        A.scale(rx, ry)
        A.set_source(g)
        A.arc(0, 0, 1.0, 0, 2 * math.pi)
        A.fill()
        A.restore()
    with f.light(blur=30) as A:
        draw.ellipse(A, (cx, Y_S), rx * 1.5, ry * 1.6)
        draw.fill(A, PAL.light, 0.12 * a)


def _lamp_head(f, t):
    k = _lamp_on(t)
    if k <= 0.0:
        return
    atmos.lamp(f, _LAMP(t), radius=9.0, intensity=0.95 * k * _dim(t), halo=4.5, core=0.3, t=t, seed=6)


# ============================================================================= render
def render(f, t, T):
    b = _beats(T)
    cam = camera(t)
    f.set_camera(cam)
    z = cam.zoom
    top_y = cam.y - H / 2 / z
    surface = top_y < 120.0
    # --- sky and far sea (only while the surface is in view)
    if surface and S.horizon_y(f) > -10:
        S.night_sky(f, t, moon=MOON, moon_r=MOON_R, dusk=DUSK, veil=0.3)
        S.far_sea(f, t, moon_x=MOON[0], dusk=DUSK)
    _water(f, t)
    if surface:
        S.surface_glow(f, t, bright=BRIGHT)
    # --- light from above: a band toward the surface, the dusk rays
    deep_k = smoothstep(800.0, 3800.0, cam.y)
    under = smoothstep(500.0, 1300.0, cam.y)
    LIB.screen_band(f, -10, 1000, PAL.surface, 0.16 * (1.0 - deep_k) * under, 0.0)
    ray_i = 0.42 * (1.0 - smoothstep(6.6, 9.6, t))
    if ray_i > 0.0:
        atmos.underwater_rays(f, surface_y=0.0, t=t, spacing=170.0, angle=97.0, fan=10.0, length=3000.0,
                              intensity=ray_i, density=0.62, seed=8, blur=16)
    # --- the descent column
    _paint(f, BED, t, cam, DELTA, _bed_a(t))
    _paint(f, COLUMN, t, cam, DELTA_REEF, _reef_a(t), strips=False)
    # --- backlight behind him (keeps the silhouette reading in the dark water)
    ps = cam.to_screen(_CHEST(t))
    LIB.screen_glow(f, (ps[0], ps[1] - 60.0), 820.0, PAL.surface,
                    0.13 * under * (1.0 - 0.75 * deep_k) * (1.0 - 0.6 * smoothstep(11.2, 12.5, t)))
    _fish(f, t)
    cone = _beam(f, t, b)
    # --- the action plane
    with f.layer() as L:
        if surface:
            BOAT.draw(L, t, pump_angle=12.0, winch_angle=0.0, hose_coil=0.55)
        LIB.draw_hose(L, HOSE.points(t), LIB.HOSE_W, color=S.mix(S.RED, INK, 0.75 * smoothstep(13.2, 13.62, t)))
        DIVER.draw(f, t, L)
    if surface:
        S.water_front(f, t, alpha=0.10, bright=BRIGHT)
        BOAT.draw_lights(f, t, lantern=1.0, window=0.0, masthead=1.0)
        xh = pelvis_x(T_HIT)
        _splash(f, t, pelvis_x(T_TOE) - 18.0, T_TOE, 14, 0.3, 10)
        _crown(f, t, xh, T_HIT, 1.0, 13)
        _splash(f, t, xh + 6.0, T_HIT, 110, 1.0, 11)
        _splash(f, t, xh - 20.0, T_HIT + 0.16, 50, 0.65, 12)
        _foam(f, t, xh, T_HIT, 150.0, 5)
        _title_splashes(f, t)
        for i, g in enumerate(TITLE):
            th = T_TITLE + TITLE_GAP * i + TITLE_FALL
            _foam(f, t, TITLE_X + g.pivot[0], th, 70.0, 20 + i, k=0.45)
    _title(f, t)
    # --- bubbles
    if t > T_HIT:
        atmos.exhale(f, _suit_src, T_HIT + 0.04, n=80, t=t, seed=31, size=(2.0, 15.0), rise=(320.0, 560.0),
                     spread=130.0, current=10.0, surface=22.0, height=2600.0, alpha=0.9)
        atmos.exhale(f, _CHEST, T_HIT + 0.9, n=40, t=t, seed=34, size=(1.8, 12.0), rise=(300.0, 520.0),
                     spread=90.0, current=10.0, surface=22.0, height=2600.0, alpha=0.9)
        atmos.exhale(f, _VALVE, 2.1, n=40, t=t, seed=32, size=(1.8, 12.0), rise=(300.0, 480.0),
                     spread=50.0, current=10.0, surface=22.0, height=2600.0, alpha=0.9)
        for i, te in enumerate(EXHALES):
            atmos.exhale(f, _VALVE, te, n=24, t=t, seed=40 + i, size=(1.8, 11.0), rise=(280.0, 460.0),
                         spread=44.0, current=12.0, surface=22.0, height=3200.0, alpha=0.9)
        atmos.bubbles(f, _VALVE, rate=4.5, t=t, seed=33, rise=(260.0, 420.0), size=(1.6, 6.5), spread=8.0,
                      current=12.0, surface=22.0, height=3600.0, alpha=0.9, t_start=2.25)
    _lamp_head(f, t)
    # --- marine snow, then the near rock edges
    snow = 0.35 + 0.95 * smoothstep(600.0, 3400.0, cam.y)
    snow *= 1.0 - 0.9 * smoothstep(12.9, 13.62, t)
    atmos.marine_snow(f, density=snow, t=t, seed=6, sink=8.0, current=(7.0, 0.0), alpha=0.8, lit=cone)
    _paint(f, COLUMN, t, cam, DELTA_REEF, 0.8 * _reef_a(t), front=True, strips=False)
    f.post["vignette"] = lerp(f.post["vignette"], 0.5, deep_k)


EXHALES = (3.1, 6.2, 8.9)


def motion_blur(t, T):
    if T_LET < t < T_HIT + 0.45:
        return 3
    return 1


def cues(T):
    b = _beats(T)
    cs = [
        Cue(-0.6, "boots on the ladder rungs, gear creaking (over the stern)", gain_db=-14, pan=0.25, dur=0.8),
        Cue(T_LET, "he lets go of the rail: brass gear rattle", gain_db=-12, pan=0.2),
        Cue(T_HIT, "heavy splash: the diver plunges in", gain_db=-4, pan=0.2, dur=1.2),
        Cue(T_HIT + 0.12, "underwater whoomp: bubble burst, the world goes muffled", gain_db=-8, dur=1.6),
        Cue(T_TITLE + TITLE_FALL, "title letters plop onto the water one by one (seven soft paper taps)",
            gain_db=-12, dur=TITLE_GAP * 6 + 0.3),
        Cue(T_DESC, "descent drone swells (low D), muffled sea; slow free-flow hiss", gain_db=-10, dur=9.0),
        Cue(8.0, "fish school sweeps past: a soft water rush and flutter", gain_db=-12, pan=-0.2, dur=2.5),
        Cue(T_CLICK, "lamp switch CLICK (key sync hit), filament buzz", gain_db=-3, dur=0.3),
        Cue(T_CLICK + 0.15, "lamp hum, low warm tone", gain_db=-16, dur=2.6),
        Cue(b["calm"], "sub swell as the light lands on the silt", gain_db=-12, dur=1.4),
    ]
    for te in EXHALES:
        cs.append(Cue(te, "diver exhale: bubble burst from the helmet", gain_db=-11, dur=1.2))
    return cs
