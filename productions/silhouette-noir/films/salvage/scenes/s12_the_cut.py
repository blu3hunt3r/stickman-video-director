"""s12 · THE CUT: on deck at night under a high moon (9.5 s).

IN  (scroll 'down' = ascent from s11, window -0.625..0.625; our bottom edge meets s11's top
    edge): still rising through night water. Zoom 0.55 and camera x locked so the pale line
    leaves the bottom edge at screen x 470 and the red hose at x ~598-618 (it follows s11's
    top-edge wander, _IN_DX); the hose comes down the near side of the hull, crosses under
    the line between 900 and 1950 px deep and runs on to its right, as in s11. The water
    colour of the bottom edge follows s11's compressed night water (_vscale/_bright) with
    s11's top glow mirrored (_in_glow). -0.625: waterline at screen y -377 (all water);
    0.625: waterline y 787, the stern and the client at top left.
Beats (scene-local s; L17 0.8-7.279: He waited until the line went [tight@3.343]. [Then@5.073]
he cut [mine@6.408], [cut@6.025]):
  1.00        the lens breaks the surface (waterline through frame centre); the camera
              settles to the stern working deck by 2.05 (zoom 0.85): the moon at (430, 400)
              with his fedora biting its lower left (crown ~(448, 446)); donkey engine and
              belt turning the pump flywheels; the line goes down from the davit at x ~930
  1.75, 3.68  he draws on the cigar (ember flares, smoke)
  3.343       [tight] the slack line snaps straight and rings, the winch drum jolts back,
              the davit nods, a 3 px shudder; he looks up at the block
  3.98-4.52   he takes the cigar from his mouth, bows and lays it on the rail (4.52, a tap;
              screen ~(466, 854)); it keeps smoking there
  5.073-5.43  [Then] his right hand goes to the knife; it is drawn along +handle_dir
  5.47        the knife's second and LAST glint (blade tip, screen ~(498, 787)); the camera
              has pushed in (zoom 1.10 by 5.85)
  5.70-5.92   his left hand takes the hose at the rail and lifts a bight of it clear of the
              winch, against the sky
  6.025       [cut] the slash (moonlit arc, 2 px shudder) through the bight just outboard of
              his fist (screen ~(570, 860)): butt-cut ends
  6.03-6.385  the diver's end is snatched back along its own path over the rail and down the
              hull (kinematic), then falls free (physics); splash 6.625 at the hull
  6.125       he lets the pump end drop: it whips back onto the deck and flops there, the
              pump's air hissing out of it (to ~10 s)
  6.40-6.62   [mine] his left hand goes to the crank; from 6.62 he cranks, calm, bent over
              the winch (s14's pose); the knife hangs in his right hand
  7.30-8.9    the camera tilts down over the side after the sinking end (waterline through
              centre 7.94, out of the top 8.58), zoom 1.25 by 8.9; bubbles from the end
OUT (scroll 'up' = descent into s13, window 9.0-10.0; our bottom edge meets s13's top
    edge): open water under the hull. The slack hose hangs from its end (screen (784, 821)
    at 9.0, (713, 1011) at 9.5, (641, 1147) at 10.0) in one loose bend to the bottom edge at
    x 533 (held there through the window, eased onto s13's slope, _guide_out). No pale line
    in frame after the push-in (it is right of x 1200). The bottom band carries s13's
    top-edge haze (_out_band) and s13's lamp beam is continued up across the seam
    (_out_beam).
Sound: line snap + winch creak, cigar tap, knife shing, the slash, the hiss; the diver's air
stops at the cut; the winch ratchet; the deck goes muffled as we go under.
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


def _lerp2(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))


# ============================================================================= timing
_T = SceneTiming("salvage", "s12")
T_TIGHT = _T.at("tight")            # 3.343: the line snaps taut
T_THEN = _T.at("Then")              # 5.073: his hand goes to the knife
T_CUT = _T.at("cut")                # 6.025: the slash
T_MINE = _T.at("mine")              # 6.408: he starts cranking
T_BREAK = 1.00                      # the lens breaks the surface (waterline through frame centre)
T_PUFF = 1.75                       # a long, slow draw on the cigar while he waits
T_PUFF2 = 3.68                      # ...and a short pleased one when the line goes tight
T_HAND = 3.98                       # his hand comes up to the cigar
T_TAKE = 4.14                       # the cigar leaves his mouth
T_SET = 4.52                        # ...and touches down on the rail (tap)
T_GRAB = 5.26                       # his right hand closes on the knife's grip
T_OUTK = 5.43                       # the blade clears the sheath
T_GLINT = 5.47                      # the knife's second and last glint
T_HOLD = 5.70                       # his left hand closes on the hose at the rail
T_LIFT = 5.92                       # ...and has lifted a bight of it clear of the winch
T_LETGO = T_CUT + 0.10              # he lets the hissing pump end drop
T_CRANK = 6.62                      # the first turn of the crank
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
CUT_X = 606.0                       # the hose goes over the top rail here
GRAB_L = (597.0, -292.0)            # where his left hand takes the hose (just inboard of the rail)
LIFT_L = (572.0, -512.0)            # ...and where it holds the bight up, clear of the winch


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
        w0, w1, r = 50.0, 145.0, 1.0
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
            draw.circle(L, _lerp2(pa, pb, u), 4.0)
            L.set_source_rgb(*INK)
            L.fill()
    L.restore()


def _exhaust_pt(t):
    return BOAT.to_world((373.0, -366.0), t)


def _boat_mask(G, t):
    BOAT.draw(G, t, color=(0.0, 0.0, 0.0), pump_angle=pump_angle(t), winch_angle=winch_angle(t), hose=False,
              hook=False, rail=True, lantern=True)


# ============================================================================= the line
X_LEAN = 55.0                       # how far the current leans the line out at depth
DX_HOSE = 236.0                     # at depth the hose runs this far right of the line (s11)
Y_DEEP = 6400.0                     # the hose and line are drawn this far down


def _line_x0(y, t):
    """The taut line's x at world depth y (leaning out with the current below the hull)."""
    return BOAT.sheave(t)[0] + X_LEAN * ss(0.0, 2600.0, y)


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
                env = ss(0.0, 220.0, y) * (1.0 - ss(1300.0, 2000.0, y))
                x += sl * env * (52.0 * math.sin(y / 250.0 - 1.1 * t + 0.6) + 22.0 * math.sin(y / 120.0 + 1.6 * t))
                x += sl * 16.0 * ss(-40.0, 120.0, y) * (1.0 - ss(120.0, 400.0, y))
        if ring:
            d = y - sh[1]
            x += ring * math.sin(math.pi * clamp(d / 1300.0)) * (1.0 - 0.6 * clamp(d / 1300.0))
        out.append((x, y))
    return out


def _draw_line(L, t, cam):
    pts = _line_pts(t)
    if t < 8.4:
        LIB.draw_hose(L, pts, LINE_W, color=PALE)
        return
    # going down into the dark: the line fades out well above the bottom edge (s13 has none)
    yb = cam.y + (H / 2) / cam.zoom
    y1 = yb - 300.0 / cam.zoom
    y0 = y1 - 600.0 / cam.zoom
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


# ============================================================================= the client
BODY = cast.CLIENT
HB = copy.copy(BODY)                # the same body, its forearm reaching to the middle of the fist
HB.forearm = BODY.forearm + 0.55 * BODY.hand * BODY.hand_scale
STAND = (BODY.hip - 0.006) * BODY.height        # pelvis height over the deck, standing


def _crank_w(t):
    return ss(6.28, T_CRANK, t)


def _pitch(t):
    """Forward bend at the hips (deg): still; a slow bow to lay the cigar down; leaning to
    take the hose; bent over the crank (s14's pose, bobbing with the crank)."""
    p = track([(-1.0, 3.0), (T_TAKE - 0.05, 3.0), (T_SET - 0.02, 38.0, "inout"), (T_SET + 0.12, 38.0),
               (5.02, 5.0, "inout"), (5.42, 6.0), (T_HOLD, 26.0, "inout"), (T_LIFT, 15.0, "inout"),
               (5.985, 13.0), (6.05, 21.0, "in"), (6.14, 23.0, "out"), (12.0, 23.0)], t)
    a = math.radians(crank_deg(t))
    return lerp(p, 42.0 + 12.0 * math.sin(a), _crank_w(t))


def _crouch(t):
    """Pelvis drop (px): the knees give for the bow and the reach."""
    return track([(-1.0, 0.0), (T_TAKE - 0.05, 0.0), (T_SET - 0.02, 40.0, "inout"), (T_SET + 0.12, 40.0),
                  (5.02, 2.0, "inout"), (5.42, 4.0), (T_HOLD, 22.0, "inout"), (T_LIFT, 9.0, "inout"),
                  (6.05, 14.0), (12.0, 14.0)], t)


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
    # the near arm ends up hanging with the knife (as s14's far arm), the far one cranks
    p.arms["R"] = dict(sh=lerp(-3.0, -26.0, w), abd=7.0, elbow=lerp(14.0, 26.0, w), wrist=lerp(4.0, 8.0, w),
                       grip=lerp(0.45, 1.0, w))
    p.arms["L"] = dict(sh=-6.0, abd=6.0, elbow=14.0, wrist=6.0, grip=0.4)
    p.eyes = dict(open=1.0, glow=0.9, look=0.0)
    return p


def _line_entry(t):
    sh = BOAT.sheave(t)
    return (sh[0] + 30.0, 40.0)


def _rail_pt(lx, t, dy=0.0):
    return BOAT.to_world((lx, rail_top_l(lx) + dy), t)


def _lhand_target(t):
    """Target for the middle of his LEFT fist (world) and its weight: down to the hose at
    the rail, the bight lifted clear of the winch, held while it hisses, dropped; then the
    crank (from [mine])."""
    if t < 5.38:
        return None, 0.0
    grab = BOAT.to_world(GRAB_L, t)
    lift = BOAT.to_world(LIFT_L, t)
    sk = _base_sk(round(t, 5))
    pel = sk.j["pelvis"]
    rest = (pel[0] + 10.0, pel[1] + 70.0)
    if t < T_HOLD:
        u = ease("inout", clamp((t - 5.38) / (T_HOLD - 5.38)))
        return _lerp2(rest, grab, u), ss(5.38, 5.52, t)
    if t < T_LIFT:
        u = ease("inout", (t - T_HOLD) / (T_LIFT - T_HOLD))
        mid = (lerp(grab[0], lift[0], 0.5) + 10.0, lerp(grab[1], lift[1], 0.5))
        return _lerp2(_lerp2(grab, mid, u), _lerp2(mid, lift, u), u), 1.0
    if t < T_LETGO:
        # held up; the jerk of the slash and the hissing stub shake it a little
        sh = 4.0 * math.exp(-max(0.0, t - T_CUT) / 0.12) * (t > T_CUT)
        return (lift[0] + sh * noise1(t * 40.0, 2), lift[1] + 2.0 * (t > T_CUT) + sh * noise1(t * 37.0, 5)), 1.0
    g = crank_grip(t)
    tgt = (g[0] - 4.0, g[1] - 2.0)
    u = ease("inout", clamp((t - T_LETGO - 0.04) / (T_CRANK - T_LETGO - 0.06)))
    open_ = (lift[0] + 4.0, lift[1] + 10.0)
    return _lerp2(open_, tgt, u), 1.0


def _cut_world(t):
    """Where the blade crosses the lifted hose: just outboard of his left fist (from the
    fist's TARGET, so the right hand's path does not depend on the solved left arm)."""
    lift = BOAT.to_world(LIFT_L, t)
    rail = BOAT.to_world((CUT_X, rail_top_l(CUT_X) - 5.0), t)
    d = (rail[0] - lift[0], rail[1] - lift[1])
    ln = math.hypot(*d) or 1.0
    return (lift[0] + d[0] / ln * 34.0 + 3.0, lift[1] + d[1] / ln * 34.0)


DRAW_LEN = 162.0 * K.KNIFE_S        # how far the grip travels to pull the blade clear


def _rhand_target(t):
    """(target for the middle of his RIGHT fist (world) or None, weight)."""
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
        return _lerp2(_lerp2(at_mouth, mid, u), _lerp2(mid, on_rail, u), u), 1.0
    if t < T_SET + 0.1:
        return on_rail, 1.0
    kw, kp = _knife_sheath(t)
    grip = kp["grip"]
    hd = kp["handle_dir"]
    if t < T_THEN:
        w = 1.0 - ss(T_SET + 0.1, T_SET + 0.55, t)
        lift = (on_rail[0] - 6.0, on_rail[1] - 26.0)
        return track2([(T_SET + 0.1, on_rail), (T_SET + 0.3, lift), (T_SET + 0.55, rest)], t), w
    if t < T_GRAB:
        u = ease("inout", (t - T_THEN) / (T_GRAB - T_THEN))
        return _lerp2(rest, grip, u), ss(T_THEN - 0.04, T_THEN + 0.1, t)
    if t < T_OUTK:
        u = ease("in", (t - T_GRAB) / (T_OUTK - T_GRAB))
        return (grip[0] + hd[0] * DRAW_LEN * u, grip[1] + hd[1] * DRAW_LEN * u), 1.0
    out = (grip[0] + hd[0] * DRAW_LEN, grip[1] + hd[1] * DRAW_LEN)
    sh = sk.j["shoulder_R"]
    ready = (sh[0] + 70.0, sh[1] + 70.0)
    c = _cut_world(t)
    cocked = (c[0] - 74.0, c[1] - 92.0)
    through = (c[0] + 38.0, c[1] + 62.0)
    hang = (pel[0] + 30.0, pel[1] + 120.0)
    keys = [(T_OUTK, out), (5.62, (out[0] + 16.0, out[1] - 24.0), "out"), (5.80, ready, "inout"),
            (T_LIFT, (ready[0] + 4.0, ready[1] - 6.0)), (5.985, cocked, "inout"), (6.05, through, "in"),
            (6.14, (through[0] + 12.0, through[1] + 16.0), "out")]
    if t <= 6.14:
        return track2(keys, t), 1.0
    # the knife comes down to hang at his side (the arm's own pose takes over)
    return _lerp2(keys[-1][1], hang, ease("inout", clamp((t - 6.14) / 0.45))), 1.0 - ss(6.4, 6.75, t)


@functools.lru_cache(maxsize=1)
def _client():
    A = Actor(BODY, cast.client(), x=-606.0, ground=1e6, facing=1, seed=12, name="client")
    A.free(16.0, _c_path, _c_pose, at=-2.0)
    # where he looks: the line where it goes into the water; up at the block when it goes
    # tight; down at the rail; the knife; the hose and the cut; the dropped hose; then up
    # the line while he cranks
    A.look_at(-2.0, T_TIGHT - 0.1, _line_entry, fade=0.4, amount=0.75)
    A.look_at(T_TIGHT + 0.06, 3.85, lambda t: BOAT.sheave(t), fade=0.22, amount=0.8)
    A.look_at(4.0, 4.75, lambda t: _rail_pt(CIGAR_X, t), fade=0.25, amount=0.9)
    A.look_at(5.10, 5.36, lambda t: (_c_path(t)[0] + 48.0, _c_path(t)[1] - 40.0), fade=0.15, amount=0.7)
    A.look_at(5.44, 5.72, lambda t: BOAT.to_world(GRAB_L, t), fade=0.15, amount=1.0)
    A.look_at(5.76, 6.18, lambda t: _cut_world(t), fade=0.12, amount=1.0)
    A.look_at(6.24, 6.62, lambda t: BOAT.to_world((560.0, deck_l(560.0)), t), fade=0.12, amount=0.7)
    A.look_at(6.86, 16.0, lambda t: (BOAT.sheave(t)[0], BOAT.sheave(t)[1] + 380.0), fade=0.5, amount=0.6)
    A.blink(2.62)
    A.blink(T_TIGHT + 0.12, dur=0.12)
    A.blink(6.70, dur=0.24)
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


def _apply_arm(p, side, target, w, grip):
    if target is None or w <= 0.0:
        return
    q = arm_ik(p.copy(), side, target, HB)
    for k in ("sh", "elbow"):
        p.arms[side][k] = lerp(p.arms[side][k], q.arms[side][k], w)
    p.arms[side]["wrist"] = lerp(p.arms[side].get("wrist", 0.0), 0.0, w)
    if grip is not None:
        p.arms[side]["grip"] = lerp(p.arms[side].get("grip", 0.3), grip, w)


@functools.lru_cache(maxsize=160)
def _solved(t):
    p = _base_pose(t).copy()
    tr, wr = _rhand_target(t)
    _apply_arm(p, "R", tr, wr, 0.95)
    tl, wl = _lhand_target(t)
    grip_l = 1.0 if (T_HOLD - 0.04 < t < T_LETGO or t > T_CRANK - 0.08) else 0.55
    _apply_arm(p, "L", tl, wl, grip_l)
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
    w = sk.j["wrist_R"]
    a_hang = math.degrees(math.atan2(h[1] - w[1], h[0] - w[0])) - 35.0
    a = track([(T_GRAB, a_sheath), (T_OUTK, a_sheath), (5.62, a_sheath - 30.0, "out"), (5.80, -32.0, "inout"),
               (T_LIFT, -36.0), (5.985, -98.0, "inout"), (6.05, 38.0, "in"), (6.14, 62.0, "out"), (12.0, 62.0)], t)
    return h, lerp(a, a_hang, ss(6.14, 6.6, t))


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


# ============================================================================= the hose
def _deck_run_l():
    """Pump outlet -> along the deck in front of the engine and the winch -> the foot of the
    riser by the rail (boat-local)."""
    ox, oy = SB.PUMP["outlet"]
    pts = [(ox + 20.0, oy), (ox + 36.0, oy + 9.0), (ox + 52.0, deck_l(ox + 52.0) - 9.0), (ox + 70.0, deck_l(ox + 70.0) - 5.5)]
    x = ox + 92.0
    while x < 556.0:
        pts.append((x, deck_l(x) - 5.0))
        x += 22.0
    pts += [(566.0, deck_l(566.0) - 6.0), (577.0, deck_l(577.0) - 16.0)]
    return pts


def _riser_l(top):
    """The foot of the riser -> `top` (where it goes over the rail, or his fist)."""
    a = (577.0, deck_l(577.0) - 16.0)
    return K.bezier(a, (586.0, deck_l(586.0) - 48.0), (top[0] - 6.0, top[1] + 70.0), top, n=12)[1:]


def _over_l():
    """Over the top rail and down the outside of the hull to the water (local)."""
    ry = rail_top_l(CUT_X) - 5.0
    x = CUT_X
    return [(x, ry), (x + 7.0, ry - 1.0), (x + 13.0, ry + 3.5), (x + 17.0, ry + 15.0), (x + 19.5, -270.0),
            (x + 21.0, -220.0), (x + 22.5, -160.0), (x + 23.5, -100.0), (x + 24.5, -40.0), (x + 25.5, 20.0),
            (x + 26.5, 80.0)]


DECK_RUN = _deck_run_l()
OVER = _over_l()
RAIL_PT = OVER[0]


def _fist_l(t):
    """His left fist in boat-local coordinates (the solved skeleton)."""
    return BOAT.to_local(client_sk(t).j["hand_L"], t)


def _lift_k(t):
    return ss(T_HOLD - 0.02, T_HOLD + 0.05, t)


def _bight_l(t):
    """(inboard part, outboard part) of the hose, local, while his fist holds a bight of it:
    deck -> riser -> fist -> down to the rail -> over. Split at the cut point (34 px
    outboard of the fist)."""
    f = _fist_l(t)
    top = _lerp2(RAIL_PT, f, _lift_k(t))
    up = DECK_RUN + _riser_l(top)
    down = K.bezier(top, (top[0] + 18.0, top[1] + 26.0), (RAIL_PT[0] - 6.0, RAIL_PT[1] - 40.0), RAIL_PT, n=10)
    # the cut: 34 px along the run down from the fist
    acc = 0.0
    for i in range(1, len(down)):
        seg = math.hypot(down[i][0] - down[i - 1][0], down[i][1] - down[i - 1][1])
        if acc + seg >= 34.0:
            u = (34.0 - acc) / seg
            c = _lerp2(down[i - 1], down[i], u)
            return up + down[1:i] + [c], [c] + down[i:] + OVER[1:]
        acc += seg
    return up + down[1:], down[-1:] + OVER[1:]


# through the IN scroll s11's hose wanders a little at its top edge: the offset (world px, at
# our zoom) that keeps ours on it at our bottom edge (sampled against s11's _hose_pts)
_IN_DX = ((-0.625, 32.5), (-0.5, 16.2), (-0.375, 4.9), (-0.25, -1.4), (-0.125, -4.0), (0.0, -4.0),
          (0.125, -2.8), (0.25, -0.1), (0.375, 5.2), (0.5, 11.8), (0.625, 18.0))


def _in_dx(t):
    if t >= 1.0:
        return 0.0
    v = float(np.interp(t, [a for a, b in _IN_DX], [b for a, b in _IN_DX]))
    return v * (1.0 - ss(T_LOCK, 1.0, t))


def _hose_water(t, p0):
    """World: from p0 (on the hull's side under the waterline) down under the hull, across
    under the line to its right-hand side, then on down into the dark (s11's set-up)."""
    out = []
    y0 = p0[1]
    ys = np.concatenate([np.linspace(y0 + 40.0, 860.0, 16), np.linspace(900.0, 2000.0, 30),
                         np.linspace(2100.0, Y_DEEP, 22)])
    for y in ys:
        u = ss(900.0, 1950.0, y)
        top = p0[0] - 24.0 * ss(y0, 860.0, y) + 7.0 * math.sin(0.5 * t + y / 310.0) * ss(y0, y0 + 300.0, y)
        x = lerp(top, _line_x0(y, t) + DX_HOSE, u)
        x += 12.0 * math.sin(0.45 * t + y / 520.0) * math.sin(math.pi * clamp((y - y0) / 2400.0))
        x += _in_dx(t) * ss(1500.0, 1950.0, y)
        out.append((x, y))
    return out


def _w(pts, t):
    return [BOAT.to_world(p, t) for p in pts]


def _hose_pre(t):
    """(inboard piece, outboard piece) of the hose before the cut (world): pump -> the cut
    point, the cut point -> the deep."""
    if t < T_HOLD - 0.02:
        inner, outer = DECK_RUN + _riser_l(RAIL_PT), [RAIL_PT] + OVER[1:]
    else:
        inner, outer = _bight_l(t)
    outer = _w(outer, t)
    return _w(inner, t), outer + _hose_water(t, outer[-1])


# --- the diver's end at the cut: the weight of the hose below snatches it back along its own
# path, over the rail and down the side (kinematic), then it falls free (physics, below)
T_REL = T_CUT + 0.36                # the end is down the side of the hull: physics takes over
SLIDE_V0 = 300.0                    # px/s: the recoil at the cut
SLIDE_A = 2600.0                    # px/s^2: the hanging hose drags it over the rail


def _slide(t):
    tau = max(0.0, t - T_CUT)
    return SLIDE_V0 * tau + 0.5 * SLIDE_A * tau * tau


def _slide_v(t):
    return SLIDE_V0 + SLIDE_A * max(0.0, t - T_CUT)


@functools.lru_cache(maxsize=1)
def _out_l():
    """The outboard piece as it lay when cut (boat-local): the cut point -> down to the rail
    -> over -> down the hull to under the waterline."""
    return _bight_l(T_CUT)[1]


def _slid(t, r):
    """The outboard piece at time t with its first r px gone back over the rail (world, the
    end first)."""
    pts = _w(_out_l(), t)
    P = np.asarray(pts + _hose_water(t, pts[-1]), np.float64)
    seg = np.hypot(P[1:, 0] - P[:-1, 0], P[1:, 1] - P[:-1, 1])
    s = np.concatenate([[0.0], np.cumsum(seg)])
    i = int(np.clip(np.searchsorted(s, r, side="right"), 1, len(P) - 1))
    u = clamp((r - s[i - 1]) / max(seg[i - 1], 1e-9))
    p0 = P[i - 1] + (P[i] - P[i - 1]) * u
    return [tuple(p0)] + [tuple(p) for p in P[i:]]


def _resample(pts, n):
    P = np.asarray(pts, np.float64)
    seg = np.linalg.norm(P[1:] - P[:-1], axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    u = np.linspace(0.0, s[-1], n)
    return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], axis=1), float(s[-1]), s


class _MediumRope(Rope):
    """physics.Rope (its verlet + red-black constraint solve, bending stiffness and
    collisions, unchanged) with a per-node medium: accel(t, P, V) -> (n, 2) accelerations
    (gravity, drag and current that differ in air and water; the jet of air out of an open
    hose end), and an optional HOLD: node `hold[0]` pinned to hold[1](t) until hold[2]."""

    def __init__(self, n, length, a, b=None, accel=None, hold=None, v0=None, **kw):
        Rope.__init__(self, n, length, a, b, **kw)
        self.accel = accel
        self.hold = hold
        self.v0 = v0                    # (n, 2) initial node velocities (default: at rest)

    def _simulate(self):
        n, dt = self.n, self.dt
        steps = int(math.ceil((self.t1 - self.t0) / dt)) + 2
        P = np.array(self.init(self.t0), np.float64)
        prev = P.copy() if self.v0 is None else P - np.asarray(self.v0, np.float64) * dt
        frames = np.empty((steps, n, 2), np.float64)
        for k in range(steps):
            t = self.t0 + k * dt
            vel = (P - prev) / dt
            acc = self.accel(t, P, vel)
            new = P + vel * dt + acc * dt * dt
            prev, P = P, new
            rest = self._rest(t)
            pa = np.array(self.a(t), np.float64)
            inv = np.ones((n, 1))
            inv[0] = 0.0
            ph = None
            if self.hold is not None and t < self.hold[2]:
                hi = self.hold[0]
                inv[hi] = 0.0
                ph = np.array(self.hold[1](t), np.float64)
            for _ in range(self.iters):
                P[0] = pa
                if ph is not None:
                    P[hi] = ph
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
            P[0] = pa
            if ph is not None:
                P[hi] = ph
            if self.collide is not None:
                # sliding friction on the deck, once per step
                on = P[:, 1] >= self.collide(P[:, 0], P[:, 1]) - 0.5
                if on.any():
                    prev[on, 0] = P[on, 0] - (P[on, 0] - prev[on, 0]) * FRICTION
            frames[k] = P
        self._frames = frames


# --- the pump end, on deck (boat-local coordinates: the deck stays put in them)
DECK_N = 48
FRICTION = 0.94                     # x velocity kept per 1/240 s step by a node on the deck
_DECK_X = np.arange(-200.0, 1000.0, 4.0)
_DECK_Y = np.array([deck_l(float(x)) for x in _DECK_X])


def _deck_floor(x, y):
    return np.interp(x, _DECK_X, _DECK_Y) - 5.0


def _deck_accel(t, P, V):
    acc = np.zeros_like(P)
    acc[:, 1] = 2400.0
    acc -= 1.4 * V
    tau = t - T_CUT
    if tau > 0.02:
        # the pump keeps blowing: the jet out of the open end shoves it about (it whips)
        e = P[-1] - P[-3]
        e /= (np.linalg.norm(e) + 1e-9)
        nrm = np.array([-e[1], e[0]])
        k = ss(0.02, 0.1, tau) * (1.0 - 0.5 * ss(1.2, 3.5, tau))
        kr = k * (1.0 - 0.85 * ss(0.5, 0.9, tau))        # the shove back eases once it is down
        wob = math.sin(2.0 * math.pi * 2.9 * tau) + 0.7 * math.sin(2.0 * math.pi * 5.3 * tau + 1.0)
        acc[-1] += -2600.0 * kr * e + 4200.0 * k * wob * nrm
        acc[-2] += -1000.0 * kr * e + 1800.0 * k * wob * nrm
        acc[-3] += k * (900.0 * wob * nrm)
    return acc


@functools.lru_cache(maxsize=1)
def _deck_rope():
    inner = BOAT_LOCAL_INNER_AT_CUT()
    P0, L, s = _resample(inner, DECK_N)
    # the node nearest his fist is held until he lets go
    fi = _fist_l(T_CUT)
    hi = int(np.argmin(np.hypot(P0[:, 0] - fi[0], P0[:, 1] - fi[1])))
    a = tuple(P0[0])
    return _MediumRope(DECK_N, L, lambda t: a, None, accel=_deck_accel, hold=(hi, _fist_l, T_LETGO), t0=T_CUT,
                       t1=T_END + 0.3, dt=1.0 / 240.0, collide=_deck_floor, iters=12, stiffness=0.35,
                       init=lambda t0: P0)


def BOAT_LOCAL_INNER_AT_CUT():
    return _bight_l(T_CUT)[0]


# --- the diver's end, over the side (world coordinates)
WATER_N = 170
G_AIR = 2600.0
G_WATER = 560.0
Q_DRAG = 0.0015                     # quadratic drag in the water (1/px)
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
    drag = 0.25 * (1.0 - w) + 1.6 * w
    y = P[:, 1]
    # a slow set toward the bow in the upper water (the slack hose drifts back under the
    # hull) with a shear that folds it into loose S-bends; nothing at depth
    shear = (1.0 - _ssv(1800.0, 2800.0, y))
    cur = (-46.0 + 60.0 * np.sin(y / 330.0 - 0.9 * t) + 26.0 * np.sin(y / 140.0 + 1.7 * t + 1.0)) * w * shear
    # ...and a quadratic term in the water: the plunge off the side is checked quickly
    dr = drag + Q_DRAG * w * np.hypot(V[:, 0] - cur, V[:, 1])
    acc = np.empty_like(P)
    acc[:, 0] = -dr * (V[:, 0] - cur)
    acc[:, 1] = g - dr * V[:, 1]
    return acc


@functools.lru_cache(maxsize=1)
def _water_rope():
    """From T_REL: the slid piece, the deep end pinned, the free end falling with the speed
    it was snatched at (that speed fades out with depth: the slack piles in below)."""
    pts = list(reversed(_slid(T_REL, _slide(T_REL))))     # the deep end (pinned) -> the free end
    P0, L, s = _resample(pts, WATER_N)
    tan = np.zeros_like(P0)
    tan[1:-1] = P0[:-2] - P0[2:]
    tan[-1] = P0[-2] - P0[-1]
    tan /= (np.linalg.norm(tan, axis=1)[:, None] + 1e-9)
    depth = P0[:, 1] - _sea_np(P0[:, 0], T_REL)
    v0 = tan * (_slide_v(T_REL) * (1.0 - _ssv(250.0, 2600.0, depth)))[:, None]
    a = tuple(P0[0])
    return _MediumRope(WATER_N, L, lambda t: a, None, accel=_water_accel, t0=T_REL, t1=T_END + 0.4,
                       dt=1.0 / 180.0, iters=10, stiffness=0.3, init=lambda t0: P0, v0=v0)


def hose_end(t):
    """World point of the severed (diver's) end."""
    if t < T_CUT:
        return _hose_pre(t)[1][0]
    if t < T_REL:
        return _slid(t, _slide(t))[0]
    return tuple(_water_rope().points(t)[-1])


def _hose_in_pts(t):
    if t < T_CUT:
        return _hose_pre(t)[0]
    return _w(_deck_rope().points(t), t)


def _hose_out_pts(t):
    if t < T_CUT:
        return _hose_pre(t)[1]
    if t < T_REL:
        return _slid(t, _slide(t))
    return [tuple(p) for p in reversed(_water_rope().points(t))]


def _hose_x_at(t, y):
    """x where the (cut) hose first crosses depth y going down from its end, or None."""
    P = _water_rope().points(t)[::-1]
    for a, b in zip(P, P[1:]):
        if (a[1] - y) * (b[1] - y) <= 0.0 and a[1] != b[1]:
            u = (y - a[1]) / (b[1] - a[1])
            return a[0] + (b[0] - a[0]) * u
    return None


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


# ============================================================================= camera
CAM_DECK = (-432.0, -174.0, 0.85)   # wide on the stern working deck (moon top left)
CAM_CUT = (-505.0, -392.0, 1.10)    # pushed in on him, the winch and the rail
Z_IN = 0.55                         # s11's zoom at the cut
Z_OUT = 1.25
X_OUT_HOSE = 533.0                  # where the hose leaves the bottom edge (s13 picks it up there)
T_LOCK = 0.625                      # end of the scroll window: the line/hose locked to s11's

# camera height while rising: knots (t, y, vy)
_RISE_Y = [(T_A, 2430.0, -1550.0), (0.0, 1300.0, -2050.0), (T_BREAK, 0.0, -560.0), (2.05, CAM_DECK[1], 0.0)]


def _rise(t):
    y = herm_keys(_RISE_Y, t)
    z = math.exp(lerp(math.log(Z_IN), math.log(CAM_DECK[2]), ease("inout", clamp((t - T_LOCK) / (2.05 - T_LOCK)))))
    yb = y + (H / 2) / z
    xl = _line_x0(yb, t) + (540.0 - 470.0) / z         # the line at screen x 470 on the bottom edge
    x = lerp(xl, CAM_DECK[0], ease("inout", clamp((t - T_LOCK) / (2.05 - T_LOCK))))
    return x, y, z


def _deck_cam(t):
    x = track([(2.05, CAM_DECK[0]), (4.6, CAM_DECK[0] - 6.0), (5.85, CAM_CUT[0], "inout"), (7.3, CAM_CUT[0] + 4.0)], t)
    y = track([(2.05, CAM_DECK[1]), (4.6, CAM_DECK[1] - 10.0), (5.85, CAM_CUT[1], "inout"), (7.3, CAM_CUT[1] + 6.0)], t)
    z = math.exp(track([(2.05, math.log(CAM_DECK[2])), (4.6, math.log(CAM_DECK[2] * 1.01)),
                        (5.85, math.log(CAM_CUT[2]), "inout"), (7.3, math.log(CAM_CUT[2] * 1.01))], t))
    return x, y, z


@functools.lru_cache(maxsize=1)
def _end_track():
    """The severed end's depth, sampled and smoothed (for the camera to follow it down)."""
    ts = np.arange(T_CUT, T_END + 0.41, 1.0 / 24.0)
    ys = np.array([hose_end(float(t))[1] for t in ts])
    k = np.ones(7) / 7.0
    ysm = np.convolve(np.pad(ys, 3, mode="edge"), k, mode="valid")
    return ts, ysm


def _end_y(t):
    ts, ys = _end_track()
    return float(np.interp(t, ts, ys))


def _down_z(t):
    return math.exp(track([(T_TILT, math.log(CAM_CUT[2] * 1.01)), (8.9, math.log(Z_OUT), "inout"),
                           (12.0, math.log(Z_OUT))], t))


def _down_y(t):
    """Down over the side after the sinking end, which then sinks away down the frame."""
    y0 = _deck_cam(T_TILT)[1]
    off = track([(T_TILT, -260.0), (8.6, -150.0, "inout"), (T_END + 0.2, 160.0, "inout")], t)
    yf = _end_y(t) - off
    return lerp(y0, yf, ease("inout", clamp((t - T_TILT) / 1.5)))


def _out_track_x(t, z):
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
    return sum(xs) / len(xs) - (X_OUT_HOSE - W / 2) / z


def _cam3(t):
    if t < 2.05:
        return _rise(t)
    if t < T_TILT:
        return _deck_cam(t)
    y = _down_y(t)
    z = _down_z(t)
    x0 = _deck_cam(T_TILT)[0]
    w = ss(7.9, 9.0, t)
    x = lerp(x0, _out_track_x(t, z), w) if w > 0.0 else x0
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
def _s11_u(t):
    return clamp((t + 10.0 - 7.30) / (10.625 + 0.4 - 7.30))


def _s11_vdepth(t):
    """Virtual depth of s11's top edge at the paired time (its compressed night water)."""
    vy = lerp(1750.0, 760.0, ss(0.1, 0.95, _s11_u(t)))
    return vy - 475.0


def _vscale(t):
    """Depth compression of the water colour: while rising from s11 our bottom edge carries
    s11's top-edge colour; it relaxes to true night water as we reach the deck."""
    if t >= 2.2:
        return 1.0
    x, y, z = _rise(min(t, 2.05))
    yb = y + (H / 2) / z
    v0 = clamp(_s11_vdepth(min(t, T_LOCK)) / max(yb, 1.0), 0.05, 1.0)
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


# ============================================================================= effects
def _ember_flare(f, sk, t):
    """The ember is a few px at this zoom: when he draws on it a warm halo blooms (s14)."""
    k = _flare(t)
    if k <= 0.01 or t >= T_TAKE:
        return
    atmos.lamp(f, _mouth(sk), radius=5.0, intensity=k, halo=7.0, core=0.0, flicker="ember", t=t, seed=21)


def _smoke(f, t, sk):
    if t < T_TAKE + 0.3:
        m = _mouth(sk)
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
        if tt < 5.98:
            continue
        h, a = _knife_hand(tt, client_sk(tt))
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
    """The pump's air blowing out of the open end: a faint flickering fan of mist and
    droplets."""
    tau = t - T_CUT
    if tau < 0.02 or tau > 4.0:
        return
    P = _hose_in_pts(t)
    e, e2 = P[-1], P[-3]
    d = (e[0] - e2[0], e[1] - e2[1])
    ln = math.hypot(*d) or 1.0
    d = (d[0] / ln, d[1] / ln)
    n = (-d[1], d[0])
    k = ss(0.02, 0.1, tau) * (1.0 - 0.6 * ss(1.0, 4.0, tau))
    col = mix(PAL.moon, PAL.surface, 0.3)
    with f.light(blur=2.5) as A:
        for i in range(10):
            h1, h2 = hash01(31, i, 1), hash01(31, i, 2)
            ph = (t * (5.0 + 3.0 * h1) + h2) % 1.0
            sp = (h1 - 0.5) * 0.9
            L0 = 6.0 + 70.0 * ph
            dx, dy = d[0] + n[0] * sp, d[1] + n[1] * sp
            a = (e[0] + dx * L0, e[1] + dy * L0)
            b = (e[0] + dx * (L0 + 14.0 + 10.0 * h2), e[1] + dy * (L0 + 14.0 + 10.0 * h2))
            S.line(A, [a, b], 1.3, col, 0.36 * k * (1.0 - ph))


def _end_under(te):
    p = hose_end(te)
    return (p[0], max(p[1], S.sea_y(p[0], te) + 6.0))


_END_S = LIB.Sampled(_end_under, T_CUT, T_END + 0.4, hz=48.0)


@functools.lru_cache(maxsize=1)
def _splash_t():
    """When (and where) the falling end hits the water."""
    for i in range(1, 240):
        te = T_CUT + i / 120.0
        p = hose_end(te)
        if p[1] > S.sea_y(p[0], te):
            return te, p[0]
    return T_CUT + 0.6, hose_end(T_CUT + 0.6)[0]


def _end_bubbles(f, t):
    """The last of the air in the hose leaving the cut end as it sinks."""
    ts, xs = _splash_t()
    if t < ts:
        return
    atmos.bubbles(f, _END_S, rate=9.0, t=t, seed=46, rise=(200.0, 330.0), size=(1.5, 6.0), spread=6.0,
                  current=10.0, surface=4.0, height=1600.0, alpha=0.7, t_start=ts + 0.05, t_end=ts + 1.8)
    atmos.bubbles(f, _END_S, rate=2.5, t=t, seed=47, rise=(180.0, 260.0), size=(1.2, 3.5), spread=4.0,
                  current=10.0, surface=4.0, height=1600.0, alpha=0.6, t_start=ts + 1.8, t_end=T_END)


def _in_glow(f, t):
    """s11's moonlight glow sits on its top edge through the scroll: continue it across our
    bottom edge (mirrored), fading as we leave the window."""
    a = 0.30 * ss(0.5, 1.0, _s11_u(min(t, T_LOCK))) * (1.0 - ss(T_LOCK, 1.3, t))
    if a > 0.003:
        LIB10.screen_glow(f, (600.0, H + 320.0), 1100.0, mix(PAL.moon, PAL.mid, 0.35), a, blur=40)


# s13 (finished) opens deep by the wreck: its camera depth over our OUT window (sampled from
# its camera()) and its backdrop's murk. Its top edge shows the far haze at cy - (H/2)/BG_SPAN.
_S13_CY = ((9.0, 8042.1), (9.25, 8168.6), (9.5, 8262.6), (9.75, 8324.1), (10.0, 8353.3))
S13_MURK = 0.34


def _out_band(f, t):
    """Going down, the water below lightens toward the haze round the diver's lamp: a band
    rising into our bottom edge that carries s13's top-edge haze by the scroll."""
    k = ss(8.1, 9.0, t)
    if k <= 0.0:
        return
    cy = float(np.interp(t, [a for a, b in _S13_CY], [b for a, b in _S13_CY]))
    col = S.haze_at(cy - (H / 2) / S.BG_SPAN, S13_MURK)
    with f.screen() as G:
        draw.linear(G, (0, H * 0.40), (0, H), [(0.0, col, 0.0), (0.5, col, 0.35 * k), (0.8, col, 0.8 * k),
                                               (1.0, col, k)])
        G.paint()
        # s13's right half is darker at its top (the shadow under the wreck's quarter)
        dk = mix(INK, PAL.deep, 0.5)
        hg = cairo.LinearGradient(0, 0, W, 0)
        for u, a in ((0.0, 0.0), (0.31, 0.0), (0.47, 0.30), (0.86, 0.30), (1.0, 0.40)):
            hg.add_color_stop_rgba(u, dk[0], dk[1], dk[2], a * k)
        vg = cairo.LinearGradient(0, H * 0.55, 0, H)
        vg.add_color_stop_rgba(0.0, 0, 0, 0, 0.0)
        vg.add_color_stop_rgba(1.0, 0, 0, 0, 1.0)
        G.set_source(hg)
        G.mask(vg)


# ...and the beam of his helmet lamp, which reaches s13's top edge from s13 time ~ -0.4:
# (s13 time, lamp screen x, y, angle, s13 zoom, length), sampled from its _beam()
_S13_BEAM = ((-0.5, 441.4, 1429.4, -72.0, 1.1160, 1300.0), (-0.25, 440.0, 1300.8, -72.0, 1.1579, 1300.0),
             (0.0, 439.1, 1198.3, -72.0, 1.1891, 1300.0), (0.25, 438.6, 1128.0, -72.0, 1.2095, 1300.0),
             (0.5, 438.3, 1093.9, -72.0, 1.2191, 1300.0))


# ...and the slope of its hose just under its top edge (screen dx per px down), sampled
_S13_SLOPE = ((-0.5, 0.17), (-0.25, 0.25), (0.0, 0.36), (0.25, 0.53), (0.5, 0.43))


def _guide_out(pts, t, cam):
    """Over the last second the hose's tail is eased (in screen space, the bottom 420 px) onto
    the line it continues along in s13: through X_OUT_HOSE on the bottom edge, on s13's slope,
    so the join is one loose bend and not a kink."""
    k = ss(8.6, 9.0, t)
    if k <= 0.0:
        return pts
    sl = float(np.interp(t - 9.5, [a for a, b in _S13_SLOPE], [b for a, b in _S13_SLOPE]))
    out = []
    for p in pts:
        sx, sy = cam.to_screen(p)
        w = k * ss(H - 420.0, H + 60.0, sy)
        if w > 0.0:
            p = cam.to_world((lerp(sx, X_OUT_HOSE + sl * (sy - H), w), sy))
        out.append(p)
    return out


def _out_beam(f, t, cam):
    """Continue s13's lamp beam up across our bottom edge during the scroll: the same cone,
    its apex one frame height below ours."""
    tau = t - 9.5
    if tau < -0.5:
        return None
    rows = np.array(_S13_BEAM)
    sx, sy, ang, z13, ln = (float(np.interp(tau, rows[:, 0], rows[:, i])) for i in range(1, 6))
    apex = cam.to_world((sx, sy + H))
    return atmos.beam(f, apex, ang - cam.rot, length=ln * z13 / cam.zoom, half_angle=11.0, color=LIGHT,
                      intensity=0.6, falloff=0.8, soft=0.5, core=0.55, fog=0.4, dust=0.45, glare=0.0, t=t,
                      seed=7, pool=0.0)


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
    _out_band(f, t)
    sk = client_sk(t)
    look = _client_look(t)
    # silhouettes keep the moon and the lamps behind them
    K.emit_mask(f, [lambda G: _boat_mask(G, t)])
    K.figure_mask(f, sk, look)
    kw = K.knife_on_belt(sk)
    cap = cairo.LINE_CAP_BUTT if t >= T_CUT else cairo.LINE_CAP_ROUND
    with f.layer() as L:
        _draw_line(L, t, cam)
        BOAT.draw(L, t, pump_angle=pump_angle(t), winch_angle=winch_angle(t), hose=False, hook=False, rail=False)
        _draw_engine(L, t)
        _stroke(L, _hose_in_pts(t), HOSE_W, RED, cap=cap)
        F.draw_figure(f, sk, look, L)
        if t < T_GRAB:
            S.draw_knife(L, **kw)
        else:
            _draw_sheath(L, kw)
            h, a = _knife_hand(t, sk)
            _draw_knife_blade(L, h, a, t < 5.56)
        if T_TAKE <= t < T_SET:
            c, ang = _cigar_hand(sk)
            _draw_cigar(L, f, c, ang, 0.55)
        _draw_rail(L, t)
        if t >= T_SET:
            _draw_cigar(L, f, _cigar_rail(t), 2.0, 0.55 + 0.08 * noise1(t * 1.3, 2))
        _stroke(L, _guide_out(_hose_out_pts(t), t, cam), HOSE_W, RED, cap=cap)
    S.water_front(f, t, alpha=0.08, bright=_bright(t))
    BOAT.draw_lights(f, t, lantern=1.0, window=0.5, masthead=1.0)
    _ember_flare(f, sk, t)
    _smoke(f, t, sk)
    if T_OUTK - 0.1 < t < T_GLINT + 0.45:
        h, a = _knife_hand(t, sk)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        S.knife_glint(f, (h[0] + ca * 164.0 * K.KNIFE_S, h[1] + sa * 164.0 * K.KNIFE_S), t, T_GLINT, dur=0.36,
                      size=0.75)
    _slash(f, t)
    _hiss(f, t)
    ts, xs = _splash_t()
    LIB.splash(f, t, xs, ts, 16, 0.5, 12)
    _end_bubbles(f, t)
    _out_beam(f, t, cam)
    if top_y > -500:
        atmos.marine_snow(f, density=0.45 * ss(-500.0, 300.0, top_y), t=t, seed=12, sink=5.0, current=(9.0, 0.0),
                          alpha=0.55)
    if t < 1.2:
        c1, c2 = camera(t - 0.02), camera(t + 0.02)
        LIB10.streaks(f, t, (0.0, (c2.y - c1.y) / 0.04), n=110, seed=13, alpha=0.45 * (1.0 - ss(0.4, 1.1, t)),
                      size=1.3)
        _in_glow(f, t)
    vig = 0.55
    if 0.7 <= t <= 8.9:
        vig = lerp(0.55, 0.46, ss(0.7, 1.5, t) * (1.0 - ss(8.3, 8.9, t)))
    f.post["vignette"] = vig


def motion_blur(t, T):
    if t < 0.75:
        return 3
    if T_TIGHT - 0.02 < t < T_TIGHT + 0.12 or 5.97 < t < T_REL + 0.06:
        return 3
    return 1


def cues(T):
    ts, _ = _splash_t()
    return [
        Cue(-0.6, "rising through night water (s11's ascent goes on): a muffled rush", gain_db=-12, dur=1.6),
        Cue(T_BREAK, "the lens breaks the surface: water sheeting off, the night air opening up", gain_db=-8,
            dur=0.8),
        Cue(0.9, "on deck: the donkey engine's slow chuff and belt slap, the pump flywheels turning, swell "
            "slaps on the hull, a light wind", gain_db=-14, pan=-0.2, dur=6.9),
        Cue(0.9, "the diver's air going down the hose: the pump's steady wheeze (it STOPS dead at the cut)",
            gain_db=-18, pan=0.1, dur=T_CUT - 0.9),
        Cue(T_PUFF - 0.35, "the client draws on his cigar: a soft crackle of the ember", gain_db=-16, pan=-0.2),
        Cue(T_PUFF2 - 0.12, "a second, shorter draw on the cigar", gain_db=-19, pan=-0.2),
        Cue(T_TIGHT, "the line SNAPS taut: a low twang through the line, the winch creaks and its pawl clacks, "
            "the davit groans", gain_db=-6, pan=0.35, dur=0.9),
        Cue(T_SET, "the cigar laid on the rail: a small wooden tap", gain_db=-16, pan=-0.1),
        Cue(T_GRAB + 0.01, "the knife drawn: a leather whisper, then a steel SHING as it clears the sheath",
            gain_db=-6, dur=0.25),
        Cue(T_GLINT, "the glint: a faint high shimmer", gain_db=-20),
        Cue(T_HOLD, "he takes up the hose: rubber creaks as the bight lifts off the winch", gain_db=-14, dur=0.25),
        Cue(T_CUT - 0.035, "THE CUT: a fast whoosh into a wet rubber CHUK as the hose parts", gain_db=-3, dur=0.2),
        Cue(T_CUT + 0.02, "AIR HISS: the pump end blows free, a loud raw hiss, slapping on the deck boards as it "
            "whips, settling to a steady hiss", gain_db=-6, pan=0.05, dur=3.6),
        Cue(T_CUT + 0.08, "the cut end snatched back over the rail: a rubbery slither over the gunwale",
            gain_db=-12, pan=0.15, dur=0.35),
        Cue(ts, "the cut end slaps into the sea by the hull: a small splash", gain_db=-12, pan=0.15),
        Cue(T_CRANK, "he cranks the winch, calm: the ratchet clicking, steady", gain_db=-10, pan=-0.05, dur=3.0),
        Cue(ts + 0.05, "the last air out of the cut end: a short string of bubbles, then nothing", gain_db=-16,
            dur=1.8),
        Cue(7.94, "under the waterline: the deck sounds muffle and drop away (low-pass sweep), a low "
            "underwater hum", gain_db=-10, dur=2.1),
    ]
