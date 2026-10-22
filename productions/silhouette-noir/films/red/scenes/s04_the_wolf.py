"""s04 · THE WOLF: the eyes in the thicket, the run, the wolf on the path (14.0 s).

IN (dissolve from s03, 1.0 s): the same walk as s03's end (one Actor timeline, the s02/s03
    walk shifted by DT = 29 s, its footfalls identical through 1.4 s): she walks right in
    profile at ~342 px/s, basket in her near (right) hand, feet at screen (540, 1350), camera
    L.s03_cam(t + 14) (zoom 1.0) until 1.0; mood L.s03_mood (mix(DAY, DEEP, 0.6), no light
    shafts), no snowfall. The black thickets of the deep forest line the far side of the path.
Beats (scene-local s):
    [wolf] 1.49  two glowing eyes open in the thicket behind her, on her left (far side);
                 they keep pace with her, sliding behind the trunks
    2.54-3.45    she stops and looks back over her shoulder; the eyes shut just before she
                 sees them
    3.45-6.4     she walks on, faster; glimpses of something huge moving between the trunks
                 in the thicket: a shoulder, a ruff, a tail
    [girls] 6.49 she RUNS (child_run, ~800 px/s); the camera tracks
    7.2-10.4     the eyes pace her on the left
    10.0-11.35   they surge past her and vanish ahead into the thicket
    11.3-12.6    the WOLF steps onto the path ahead out of the fog: huge, backlit (a fog glow
                 behind it, a pale halo round it), head low; snow starts falling again (8.6 on)
    12.06-12.46  she skids to a stop before its nose (heel slide, snow spray, skid marks); it
                 snarls (12.40); she pulls the basket back behind her, a hand up, sits back
    12.46-12.80  the settle: momentum carries her over her feet, she recoils and sinks to spring;
                 her eyes dart to the way out (toward us) just before she goes
OUT (whip "left" to s05, 0.5 s, from 13.75): on 12.80 she bolts off the path to the right,
    toward camera (yaw 24, onto the snow bank in front of the trail), right across its nose;
    its jaws slam shut on the air just behind her (13.36); it wheels after her on its forehand
    (13.45-13.90, the same timing as s05's turn) and gallops. The camera pushes in to zoom 1.0
    and accelerates right (763 px/s at 13.75, 910 from 14.0) into the whip.
    At 13.75 (= s05 -0.25): her feet at screen (696, 1437), running at 780 px/s; the wolf's
    root at screen x 325, mid-wheel (yaw 38), its muzzle beside her. Mood DEEP; snow 0.3.
"""
import math
from functools import lru_cache

import numpy as np

from engine import draw
from engine import figure as F
from engine.core import clamp, ease, hash01, lerp, noise1, smoothstep
from engine.creatures import Wolf, solve_quadruped, _head_pts, _EYE, _QTurn, _FRONT, D2R
from engine.frame import Camera
from engine.motion import Actor, GAITS, foot_ik
from engine.timing import Cue, SceneTiming
from films.red import sets as S
from films.red.scenes import _lib_s02_s06 as L

FOREST = S.FOREST
PATH = S.PATH
GIRL, H = L.GIRL, L.GH
DT, DX = 29.0, 800.0                    # s04 time = s02 time - 29, trail x = s02 street x + 800
X0 = L.S02_X0 + DX                      # where the shared walk starts (s04 t = -19.08)

# her performance (scene-local seconds)
N_WALK = 53                             # the shared walk, cut short: 53 steps, feet together 2.54
T_GO = 3.45                             # walks on, faster ...
X_JOG, X_RUN = 7700.0, 7960.0           # ... breaks into a jog, then the run: first flight on [girls]
T_SKID = 12.06                          # the landing she skids on (a run footfall, see girl())
SKID = 0.40                             # the slide
T_BOLT = 12.80                          # she bolts
YAW_BOLT = 24.0                         # her heading off the path: 24 deg toward camera
DZ = 86.0                               # how far toward camera (down the screen) she gets
HURRY = L.WALK.but(speed=1.2, step=0.40, lean=6.0, arm_swing=24.0, bob=0.016, crouch=0.04)
JOG = GAITS["child_run"].but(speed=1.6, step=0.58, duty=0.42, lean=9.0)
RUN = GAITS["child_run"]
BOLT = GAITS["child_run"].but(speed=2.25, step=0.82, lean=17.0, arm_swing=52.0, ramp_in=(0.95,))   # 780 px/s = s05
RUN_CARRY = dict(sh=24.0, elbow=70.0, abd=10.0, wrist=-8.0, grip=0.95)     # = s05's run carry
BEHIND = dict(sh=-34.0, elbow=22.0, abd=16.0, wrist=-6.0, grip=0.95)       # the basket hidden behind her


@lru_cache(maxsize=None)
def _W():
    T = SceneTiming("red", "s04")
    return dict(Then=T.at("Then"), wolf=T.at("wolf"), came=T.end("came"), And=T.at("And"),
                girls=T.at("girls"), girls_end=T.end("girls"))


# ----------------------------------------------------------------------------- ground
@lru_cache(maxsize=None)
def x_bolt():
    """Where the snow bank in front of the trail begins under her: just past the place her
    skid stops (planned on the plain trail: the same walk and run up to the skid)."""
    a = _base_actor(PATH.ground_y)
    x_s = a.root(T_SKID)[0]
    v0 = (a.root(T_SKID + 0.02)[0] - a.root(T_SKID - 0.02)[0]) / 0.04
    return x_s + 0.5 * v0 * SKID + 40.0


def ground(x):
    """Her footing: the trail, and past the place she stops, the snow bank in front of it
    (off the path toward the camera: DZ px lower on the screen)."""
    x = float(x)
    xb = x_bolt()
    y = float(PATH.ground_y(x))
    return y if x <= xb else y + DZ * smoothstep(xb, xb + 380.0, x)


# ----------------------------------------------------------------------------- the girl
def _walk_len():
    """The shared s02/s03 walk is 9600 px in 70 steps (first ramped 0.72, last 0.78): a
    walk of N_WALK steps at the same scale has identical footfalls until its own ramp-out."""
    Ln = L.WALK.step * GIRL.height
    s = 9600.0 / (Ln * (70 - 0.5))
    return s * Ln * (N_WALK - 0.5)


def _base_actor(g=None):
    a = Actor(GIRL, L.look_up(), x=X0, ground=g or ground, facing=-1, seed=7, name="red")
    a.stand(until=L.S02_TURN - DT, at=-40.0 - DT)
    a.turn(0.0, dur=0.5, at=L.S02_TURN - DT, via=90.0)
    a.walk(to=X0 + _walk_len(), gait=L.WALK, at=L.S02_GO - DT)
    L.smooth_walk(a)                    # (only the shared walk: as girl_base does)
    a.walk(path=[(X_JOG, HURRY, None), (X_RUN, JOG, None), (X_RUN + 9000.0, RUN, None)], at=T_GO)
    return a


class Skid:
    """The skid stop and the face-off (one Actor.free segment from T_SKID to T_BOLT): she
    lands on her lead foot, throws it forward and slides on its heel, sitting back; the
    trail foot swings through and slides too. The feet stop, her body pitches forward over
    them and settles; she stares at the wolf, then sinks to spring (anticipation)."""

    def __init__(self, a, t_s, t_b):
        Hh, b, g = a.H, a.body, a.g
        self.a, self.t_s, self.t_b = a, t_s, t_b
        run = a.segs[-1]
        i = int(np.argmin([abs(v - t_s) for v in run.lands]))
        self.lead = run.side[i]
        self.trail = "R" if self.lead == "L" else "L"
        self.x_s, self.y_s = a.root(t_s)
        self.v0 = (a.root(t_s + 0.02)[0] - a.root(t_s - 0.02)[0]) / 0.04
        sk = a.skeleton(t_s)
        self.f0 = {s: tuple(sk.j["ankle_" + s]) for s in ("L", "R")}
        self.m0 = self.v0 * SKID
        self.x_stop = self.x_s + 0.5 * self.m0          # constant deceleration to rest
        self.lead_x = self.x_stop + 0.27 * Hh           # where the feet end up
        self.trail_x = self.x_stop - 0.07 * Hh
        self.pitch0 = run.pose(t_s).pitch

    def x(self, t):
        u = clamp((t - self.t_s) / SKID)
        x = self.x_s + self.m0 * (u - 0.5 * u * u)
        # the body's momentum carries on a little when the feet stop, then rocks back
        v = t - self.t_s - SKID
        if v > 0:
            x += 14.0 * math.sin(math.pi * clamp(v / 0.42)) * (1.0 - 0.4 * clamp(v / 0.42))
            x -= 5.0 * smoothstep(0.0, 0.5, v)
        return x

    def crouch(self, t):
        """Pelvis lowered (fraction of height) from standing: sits back into the slide, is
        carried up over her feet when they stop, then sinks to spring (the anticipation)."""
        ts, tb = self.t_s, self.t_b
        te = ts + SKID
        c = lerp(0.03, 0.075, smoothstep(ts, ts + 0.2, t))
        c = lerp(c, 0.04, smoothstep(te - 0.05, te + 0.12, t))
        c = lerp(c, 0.095, smoothstep(te + 0.10, tb, t))
        return c

    def path(self, t):
        a, Hh, b = self.a, self.a.H, self.a.body
        x = self.x(t)
        gy = 0.5 * (a.g(x - 0.1 * Hh) + a.g(x + 0.1 * Hh))
        y = gy - (b.hip - self.crouch(t)) * Hh
        y += (self.y_s - y) * (1.0 - smoothstep(self.t_s, self.t_s + 0.14, t))
        y += 0.003 * Hh * math.sin(2 * math.pi * 1.6 * t) * smoothstep(self.t_s + SKID, self.t_s + SKID + 0.3, t)
        return x, y

    def _feet(self, t):
        a, Hh, g = self.a, self.a.H, self.a.g
        ts = self.t_s
        x = self.x(t)
        u = clamp((t - ts) / SKID)
        # lead: braced out in front, sliding on its heel (toes up), flat once stopped
        k = smoothstep(ts, ts + 0.16, t)
        lx = x + lerp(self.f0[self.lead][0] - self.x_s, self.lead_x - self.x_stop, k)
        if u >= 1.0:
            lx = self.lead_x
        th = 22.0 * smoothstep(ts, ts + 0.1, t) * (1.0 - smoothstep(ts + SKID - 0.05, ts + SKID + 0.15, t))
        lead = foot_ik(lx, th, "heel", 1.0, Hh, g)
        # trail: swings through and plants under her, then slides with her
        w = clamp((t - ts) / 0.26)
        we = ease("inout", w)
        tx_land = x - 0.07 * Hh if u < 1.0 else self.trail_x
        (ax0, ay0) = self.f0[self.trail]
        (ax1, ay1), p1 = foot_ik(tx_land, 0.0, "flat", 1.0, Hh, g)
        if w < 1.0:
            ax = lerp(ax0, ax1, we)
            ay = lerp(ay0, ay1, we) - 0.07 * Hh * math.sin(math.pi * we)
            trail = ((ax, ay), lerp(-20.0, p1, we))
        else:
            trail = ((ax1, ay1), p1)
        return {self.lead: lead, self.trail: trail}

    def pose(self, t, _u):
        ts, tb = self.t_s, self.t_b
        te = ts + SKID
        p = F.Pose(0.0, 0.0, 0.0)
        for s, ((ax, ay), pitch) in self._feet(t).items():
            p.legs[s] = {"ik": (ax, ay), "pitch": pitch, "toe": 0.0, "abd": 3.0}
        # sits back in the slide; momentum pitches her over her feet when they stop; she
        # recoils from the wolf (leaning away, sinking), then springs forward into the bolt
        keys = [(ts, self.pitch0), (ts + 0.15, -16.0), (te - 0.04, -12.0), (te + 0.10, 8.0),
                (te + 0.22, -3.0), (tb, 12.0)]
        p.pitch = _pw(keys, t)
        back = smoothstep(ts, ts + 0.15, t) * (1.0 - smoothstep(te - 0.05, te + 0.15, t))
        hunch = smoothstep(te, te + 0.3, t)
        p.spine = [-2.0 * back + 2.0 * hunch, -3.0 * back + 4.0 * hunch, -2.0 * back + 3.0 * hunch]
        p.head = -0.6 * p.pitch - 2.0 * hunch
        # the free (far, left) arm: thrown forward for balance, then drawn in, then back to drive
        fl = smoothstep(ts, ts + 0.14, t) * (1.0 - smoothstep(te + 0.02, te + 0.22, t))
        draw_in = smoothstep(te + 0.02, te + 0.22, t) * (1.0 - smoothstep(tb - 0.14, tb, t))
        drive = smoothstep(tb - 0.14, tb, t)
        p.arms["L"] = dict(sh=72.0 * fl + 34.0 * draw_in - 26.0 * drive, abd=10.0,
                           elbow=30.0 * fl + 118.0 * draw_in + 70.0 * drive, wrist=4.0, grip=0.4 + 0.5 * draw_in)
        p.arms["R"] = dict(RUN_CARRY)
        return p


def _pw(keys, t):
    """Piecewise eased keys [(t, v), ...] (holds outside)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, va), (tb, vb) in zip(keys, keys[1:]):
        if t <= tb:
            return lerp(va, vb, ease("inout", (t - ta) / max(tb - ta, 1e-6)))
    return keys[-1][1]


@lru_cache(maxsize=None)
def _skid():
    a = _base_actor()
    return Skid(a, T_SKID, T_BOLT)


@lru_cache(maxsize=None)
def girl():
    sk = _skid()
    a = sk.a
    a.free(T_BOLT - T_SKID, sk.path, sk.pose, at=T_SKID, end_x=sk.x(T_BOLT), blend=0.12)
    a.state["feet"] = {sk.lead: sk.lead_x, sk.trail: sk.trail_x}
    a.walk(path=[(sk.x_stop + 4000.0, BOLT, None)], at=T_BOLT, yaw=YAW_BOLT, blend=0.16)
    # the basket: carried at her side walking, held close running (as s05 holds it)
    L.carry(a, L.S02_TAKE - DT, 6.2, fade=0.3)
    a.arm("R", 6.2, 20.0, fade=0.35, **RUN_CARRY)
    # she stops and looks back over her shoulder (body turned a little toward us)
    a.key("head_yaw", [(2.58, 0.0), (2.86, 112.0, "out3"), (3.16, 106.0), (3.44, 0.0, "inout")], fade=0.12)
    a.key("head", [(2.58, 0.0), (2.86, -6.0), (3.16, -4.0), (3.44, 0.0)], fade=0.12)
    a.key("yaw", [(2.6, 0.0), (2.9, 20.0), (3.16, 18.0), (3.46, 0.0)], fade=0.12)
    # the face-off: she pulls the basket back behind her (and keeps it there, away from the
    # jaws, until she is past them); her eyes dart to the way out (toward us) a beat before
    # her body goes
    te = T_SKID + SKID
    a.arm("R", te - 0.12, W_SNAP, fade=0.14, **BEHIND)
    a.key("head_yaw", [(T_BOLT - 0.16, 0.0), (T_BOLT - 0.06, 38.0, "out3"), (T_BOLT + 0.12, 26.0),
                       (T_BOLT + 0.34, 0.0, "inout")], fade=0.06)
    a.key("yaw", [(T_BOLT - 0.12, 0.0), (T_BOLT + 0.04, 12.0), (T_BOLT + 0.22, YAW_BOLT)], fade=0.06,
          fade_out=0.1)
    a.blink(2.20)
    a.blink(3.30)
    a.blink(5.10)
    a.blink(9.30)
    a.blink(12.22)
    return a


# ----------------------------------------------------------------------------- the basket
@lru_cache(maxsize=None)
def swing():
    a = girl()

    def pivot(t):
        return L.basket_hand(a.skeleton(t), L.BASKET_SIDE)
    return L.HandSwing(pivot, length=60.0, t0=-7.0, t1=14.6, damping=4.2, gravity=3100.0, clip=2600.0,
                       limit=0.56)


# ----------------------------------------------------------------------------- her footprints
@lru_cache(maxsize=None)
def prints():
    """Every footfall on the trail (from the forest edge on); none off the path."""
    a = girl()
    fp = S.Footprints(fill_time=40.0)
    xb = x_bolt()
    for seg in a.segs:
        if type(seg).__name__ != "_Walk":
            continue
        for side, plants in seg.plants.items():
            for (x, tl, _lift, _g) in plants[1:]:
                if -18.0 <= tl <= 15.0 and x < xb:
                    fp.add(x + seg.d * 0.05 * a.H, tl, side=1 if side == L.BASKET_SIDE else -1, size=40.0)
    return fp


# ----------------------------------------------------------------------------- camera
@lru_cache(maxsize=None)
def _ref_track():
    """Her smoothed x on a 1/48 s grid (the camera follows this, not the stride surges)."""
    from scipy.ndimage import gaussian_filter1d
    a = girl()
    ts = np.arange(-1.5, 15.5, 1.0 / 48.0)
    xs = np.array([a.root(float(t))[0] for t in ts])
    xs = gaussian_filter1d(xs, 0.2 * 48.0, mode="nearest")
    return ts, xs


def ref_x(t):
    ts, xs = _ref_track()
    return float(np.interp(t, ts, xs))


# (t, screen x, screen y of the trail under her, zoom): tracking her, until the wolf
CAM_KEYS = [
    (1.00, 540.0, 1350.0, 1.00),
    (2.50, 600.0, 1345.0, 0.90),
    (3.40, 640.0, 1340.0, 0.86),
    (5.80, 610.0, 1345.0, 0.82),
    (7.20, 540.0, 1350.0, 0.80),
    (10.40, 520.0, 1350.0, 0.80),
    (11.70, 430.0, 1345.0, 0.77),
    (12.50, 400.0, 1345.0, 0.76),
    (13.00, 400.0, 1345.0, 0.76),
]
# the face-off and the bolt: the camera holds on the two of them (her at screen x ~400, the
# wolf filling the right of the frame), pushes in to zoom 1.0 as she bolts and accelerates
# right after her, into the whip
FACE_SX, FACE_Z = 400.0, 0.78
PUSH = (12.95, 0.80)                    # zoom FACE_Z -> 1.0
PAN = (13.08, 13.98, 900.0)             # the pan right: speed eases 0 -> 900 px/s over this
TRAIL_SY = 1345.0                       # the trail's line on the screen


@lru_cache(maxsize=None)
def _cam_keys():
    return L.CamPath(CAM_KEYS)


def _cam_track(t):
    k_ = _cam_keys()(t)
    x = ref_x(t)
    return L.cam_for((x, float(PATH.ground_y(x))), (k_.x, k_.y), k_.zoom)


def _pan_dist(t):
    """Distance the camera has panned right by t (speed PAN[2] * smoothstep(PAN[0], PAN[1]))."""
    a, b, v = PAN
    if t <= a:
        return 0.0
    T = b - a
    u = min(1.0, (t - a) / T)
    d = v * T * (u ** 3 - 0.5 * u ** 4)
    return d + (v * (t - b) if t > b else 0.0)


def _cam_end(t):
    z = FACE_Z * (1.0 / FACE_Z) ** L.k(t, *PUSH)
    x = _skid().x_stop + (540.0 - FACE_SX) / FACE_Z + 10.0 * (t - 12.4) + _pan_dist(t)
    return Camera(x, float(PATH.ground_y(x)) - (TRAIL_SY - 960.0) / z, z)


def camera(t):
    if t <= 1.0:
        return L.s03_cam(t + 14.0)
    c = L.cam_mix(L.s03_cam(t + 14.0), _cam_track(t), ease("inout", (t - 1.0) / 1.3))
    if t > 12.2:
        c = L.cam_mix(c, _cam_end(t), ease("inout", (t - 12.2) / 0.5))
    return c


# ----------------------------------------------------------------------------- the thicket
# The black thickets on the far side of the path, the whole length of the scene. (S.FOREST
# adds its own band, PATH_MARKS thicket 8200-11800, over it: denser there. Seed 13: no gaps
# in the brambles where the wolf walks; it is never seen whole in them.)
TH = S.Forest(terrain=PATH, seed=13, thicket=(4800.0, 13900.0))
PAR = TH.thicket_par                    # 0.9: the wolf in the thicket lives on this plane


def lcam(t, par=PAR):
    return camera(t).parallax(par)


def her_sx(t):
    return camera(t).to_screen((ref_x(t), 0.0))[0]


def layer_x(t, sx, par=PAR):
    """Layer x (plane par) that is at screen x sx at time t."""
    lc = lcam(t, par)
    return lc.x + (sx - 540.0) / lc.zoom


# ----------------------------------------------------------------------------- the wolf in the thicket
BW_OFF = 4.0                            # its clock: tau = t + BW_OFF (its actions start at t = -4)
BW_SIZE = 360.0                         # (on its plane: about her size on the screen)
# where its body (root) is on the screen, relative to her: (t, dx). Its head is ~340 px ahead
# of the root, so the eyes are ~dx + 340 from her.
BW_KEYS = [(-1.0, -710.0), (1.0, -700.0), (1.9, -680.0), (2.35, -665.0),     # pacing her ([wolf])
           (3.30, -655.0), (4.1, -690.0), (5.0, -600.0), (6.3, -500.0),        # the glimpses
           (7.2, -590.0), (8.6, -560.0), (9.4, -545.0), (10.0, -540.0),        # the run
           (10.6, -250.0), (11.3, 420.0)]                                      # it surges past her
BW_STOP = (2.35, 3.30)                  # it stops (and sinks into the brambles) as she stops
BW_GONE = (11.05, 11.35)                # it dives into the thicket ahead of her: gone


@lru_cache(maxsize=None)
def _bw_dx():
    return L.CamPath([(t_, dx, 0.0, 1.0) for t_, dx in BW_KEYS])


def bw_target(t):
    """Layer x of the thicket wolf's root at t (its screen offset from her, BW_KEYS)."""
    return layer_x(t, her_sx(t) + _bw_dx().x(t))


def _bw_build(shift):
    """The thicket wolf. Its run segments end on the BW_KEYS track every ~0.45 s; shift[j]
    moves segment j's end time (the run's speed ramps make it arrive a little late or early:
    bw() solves for the shifts so it arrives on time)."""
    w = Wolf(x=bw_target(-1.0) - 0.9 * BW_SIZE * 3.0, ground=TH.thicket_ground, facing=1, size=BW_SIZE, seed=3)
    G = {k_: dict(v) for k_, v in w.GAIT.items()}
    # a prowl: the walk on the stalk's low frame (hidden in the brambles, the eyes in them)
    G["stalk"] = dict(G["walk"], k=1.0, acc=2.0, dec=2.0,
                      pose=dict(hf=0.68, hh=0.72, neck=-6.0, head=-22.0, tail=-30.0, ears=0.8, ruff=0.4, arch=0.03))
    # prowling in the glimpses: as low, hackles up, the tail out level (its back, its ruff and
    # its tail show over the lower brambles; the head stays down in them)
    G["walk"] = dict(G["walk"], acc=2.4, dec=2.4,
                     pose=dict(hf=0.70, hh=0.73, neck=-10.0, head=-30.0, tail=-4.0, ears=0.7, ruff=1.0, arch=0.03))
    G["trot"] = dict(G["trot"], acc=4.0, dec=3.0,
                     pose=dict(hf=0.76, hh=0.77, neck=-4.0, head=-20.0, tail=-16.0, ears=0.4, ruff=0.7))
    G["gallop"] = dict(G["gallop"], acc=8.0, v=6.0)
    w.GAIT = G
    o = BW_OFF
    plan = []                           # (scene t the segment should end, its target x)

    def leg(t0, t1, kind=None, dt=0.45):
        n = max(1, int(round((t1 - t0) / dt)))
        for j in range(1, n + 1):
            ta, tb = t0 + (t1 - t0) * (j - 1) / n, t0 + (t1 - t0) * j / n
            xa, xb = bw_target(ta), bw_target(tb)
            v = abs(xb - xa) / (tb - ta) / BW_SIZE
            k_ = kind or ("walk" if v < 1.4 else "trot" if v < 3.2 else "gallop")
            i = len(plan)
            ta_s = ta + (shift[i - 1] if i > 0 and plan[-1][0] == ta else 0.0)
            getattr(w, k_)(to=xb, dur=max(0.15, tb + shift[i] - ta_s))
            plan.append((tb, xb))

    w.stalk(to=bw_target(-1.0), dur=3.0)          # (already pacing her in s03's last seconds)
    plan.append((-1.0, bw_target(-1.0)))
    leg(-1.0, BW_STOP[0], "stalk")
    w.stand(dur=0.5, low=3.0, head=-30.0, ears=0.9)
    w.at(BW_STOP[1] + o)
    leg(BW_STOP[1], 6.3, "walk")
    leg(6.3, 10.0)
    leg(10.0, 11.3, "gallop", dt=0.43)
    # its head turned to us (both eyes on her) while it paces her
    w.overlay("look", 1.2 + o, dur=1.4, turn=42.0)
    w.overlay("look", 6.0 + o, dur=4.2, turn=38.0)
    return w, plan


def _arrival(w, x, t_guess):
    """Scene time at which the wolf's root reaches x (searching near t_guess)."""
    ts = np.arange(t_guess - 1.2, t_guess + 1.2, 1.0 / 120.0)
    xs = np.array([w.state(float(t) + BW_OFF)["x"] for t in ts])
    j = int(np.argmax(xs >= x - 0.5)) if np.any(xs >= x - 0.5) else len(ts) - 1
    return float(ts[j])


@lru_cache(maxsize=None)
def bw():
    shift = [0.0] * 64
    for _ in range(4):
        w, plan = _bw_build(shift)
        worst = 0.0
        for i, (tk, xk) in enumerate(plan):
            if i == 0 or not (BW_STOP[1] < tk or tk <= BW_STOP[0]):
                continue
            err = _arrival(w, xk, tk) - tk
            shift[i] -= 0.8 * err
            worst = max(worst, abs(err))
        if worst < 0.03:
            break
    return w


def bw_eyes(t):
    """The eyes of the wolf in the thicket at scene t: [(pos (layer coords), visibility)], r, ang,
    openness."""
    w = bw()
    P = w.state(t + BW_OFF)
    R = solve_quadruped(w, P)
    front = R["sh"]
    if front < -0.35:
        return [], 0.0, 0.0
    Lh = w.PR["head"] * w.S
    s = 1.0 if R["cF"] >= 0 else -1.0
    near = _head_pts(R, [_EYE], Lh, hl=-0.085 * s)[0]
    far = _head_pts(R, [_EYE], Lh, hl=0.085 * s)[0]
    vis_far = smoothstep(0.22, 0.5, front)
    vis = clamp((front + 0.35) / 0.35) if front < 0 else 1.0
    ang = math.degrees(math.atan2(-R["hs"], R["hc"] * s))
    out = [((near[0], near[1]), vis)]
    if vis_far > 0.01:
        out.append(((far[0], far[1]), vis * vis_far))
    return out, 0.030 * Lh, ang


EYE_OPEN = [(1.42, 0.0), (1.53, 1.0), (2.74, 1.0), (2.82, 0.0), (5.86, 0.0), (6.0, 1.0), (11.05, 1.0),
            (11.22, 0.0)]


def eye_open(t):
    """Openness of the thicket wolf's eyes: they open on [wolf], shut just before she looks
    back, open again beside her (and she runs), and pace her until it surges ahead."""
    v = _pw_lin(EYE_OPEN, t)
    # a slow blink now and then
    k = math.floor(t / 2.3)
    tb = k * 2.3 + 2.3 * hash01(13, k, 77)
    if hash01(13, k, 78) < 0.5 and 0.0 <= t - tb < 0.2:
        v *= abs(math.cos((t - tb) / 0.2 * math.pi))
    return v


def _pw_lin(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, va), (tb, vb) in zip(keys, keys[1:]):
        if t <= tb:
            return lerp(va, vb, smoothstep(ta, tb, t))
    return keys[-1][1]


def _occlusion(f, t, sx, sy):
    """1 = the point (screen) is clear of the action-plane trunks, 0 = behind one."""
    cam = f.cam
    occ = 1.0
    for tr in FOREST._trees(f, FOREST.plane):
        x0 = (tr["x"] - cam.x) * cam.zoom + 540.0
        hw = 0.5 * tr["w"] * cam.zoom
        occ = min(occ, smoothstep(-2.0, 9.0, abs(sx - x0) - hw))
    return occ


def draw_bw_body(f, t, mood):
    """The wolf's body in the thicket (behind the brambles, in their dark)."""
    a = 1.0 - smoothstep(BW_GONE[0], BW_GONE[1], t)
    # it sinks into the brambles as she stops (and they hide it while she looks back)
    a *= 1.0 - smoothstep(BW_STOP[0] + 0.1, BW_STOP[0] + 0.4, t) * (1.0 - smoothstep(BW_STOP[1], BW_STOP[1] + 0.5, t))
    if t < 0.8 or a <= 0.0:
        return
    col = S.fogged(mood, 0.27)
    if a >= 1.0:
        with S.plane(f, PAR) as c:
            bw().draw(f, t + BW_OFF, c, color=col, eyes=False)
    else:
        with f.layer(par=PAR, alpha=a) as c:
            bw().draw(f, t + BW_OFF, c, color=col, eyes=False)


def draw_bw_eyes(f, t, mood):
    op = eye_open(t)
    if op <= 0.01:
        return
    eyes, r, ang = bw_eyes(t)
    col = (1.0, 1.0, 0.97)
    lc = f.lcam(PAR)
    flare = math.exp(-((t - 1.50) / 0.18) ** 2) + 0.6 * math.exp(-((t - 5.95) / 0.16) ** 2)
    with S.plane(f, PAR) as c:
        for e, v in eyes:
            draw.ellipse(c, e, r * 1.15, r * op * 0.85, ang - 8.0)
            draw.fill(c, col, v)
    with f.emit(par=PAR) as G:
        for e, v in eyes:
            sx, sy = lc.to_screen(e)
            k = v * op * _occlusion(f, t, sx, sy)
            if k > 0.01:
                draw.glow_disc(G, e, r * 6.0, col, 0.6 * k)
                if flare > 0.02:
                    draw.glow_disc(G, e, r * 11.0, col, 0.28 * k * flare)


# ----------------------------------------------------------------------------- the wolf on the path
W_GAP = 525.0                           # its root is this far past where she stops (her face at its nose)
W_OUT = (11.45, 12.45)                  # it steps out of the fog onto the path
W_TURN = (13.45, 0.45)                  # it wheels after her (s05 finishes the same turn at its -0.10)
W_SNAP = 13.36                          # its jaws slam shut on the air just behind her
W_PIVOT = 1.3                           # ... swinging its hindquarters round its forehand (1: withers fixed)


def x_wolf():
    return _skid().x_stop + W_GAP


class _Wheel(_QTurn):
    """The engine's turn, pivoting on the forehand instead of in place: the withers stay put
    while the hindquarters swing round behind (the root moves back by the chord), so the head
    follows her past its nose and it comes round already behind her."""
    kind = "wheel"

    def __init__(self, A, t0, state, dur=0.9, fade=0.2, base=None, via="front", pivot=1.0, **kw):
        _QTurn.__init__(self, A, t0, state, dur=dur, fade=fade, base=base, via=via, **kw)
        self.half = 0.5 * A.PR["chord"] * A.S * float(pivot)
        self.c0 = math.cos(self.y0 * D2R)
        for k_, (a_, _b) in self.sch.items():
            yF, yH = self._yaws(a_[1])
            self.mid[k_] = self._ideal_at(k_, yF if _FRONT[k_] else yH, self._root(a_[1]))
        x1 = self._root(1.0)
        self.legs1 = A._stand_legs(x1, self.y1)
        self.end_state = dict(self.end_state, x=x1, legs={k_: list(v) for k_, v in self.legs1.items()})

    def _root(self, u):
        yF, yH = self._yaws(u)
        return self.x0 + self.half * (self.c0 - math.cos(0.5 * (yF + yH) * D2R))

    def _ideal_at(self, k_, yaw, x):
        keep = self.x0
        self.x0 = x                     # (construction time only)
        try:
            return self._ideal(k_, yaw)
        finally:
            self.x0 = keep

    def pose(self, t):
        P = _QTurn.pose(self, t)
        P["x"] = self._root(clamp((t - self.t0) / self.dur))
        return P


class _PathWolf(Wolf):
    CLIPS = dict(Wolf.CLIPS, wheel=_Wheel)

    def wheel(self, dur=0.6, via="front", pivot=1.0):
        return self._add("wheel", dur=dur, via=via, pivot=pivot)


@lru_cache(maxsize=None)
def pw():
    X = x_wolf()
    w = _PathWolf(x=X + 290.0, ground=PATH.ground_y, facing=-1, size=330.0, seed=1)
    G = {k_: dict(v) for k_, v in w.GAIT.items()}
    G["walk"] = dict(G["walk"], acc=3.4, dec=3.4, pose=dict(G["stalk"]["pose"], hf=0.80, hh=0.80, neck=6.0))
    G["gallop"] = dict(G["gallop"], acc=7.0)
    w.GAIT = G
    w.stand(dur=W_OUT[0])
    w.walk(to=X, dur=W_OUT[1] - W_OUT[0] - 0.2)
    w.stand(dur=0.3, low=0.8, head=-16.0, ears=0.9)
    w.at(W_TURN[0])
    w.wheel(dur=W_TURN[1], via="front", pivot=W_PIVOT)
    w.gallop(to=X + 2400.0, dur=3.0)
    w.overlay("snarl", 12.40, dur=0.62, ears=-0.4, amount=0.75)
    w.overlay("look", 12.92, dur=0.50, turn=36.0)          # its head follows her across its nose ...
    w.overlay("bite", W_SNAP - 0.20, dur=0.28, n=1)          # ... and the jaws slam shut behind her
    return w


W_SHOW = 11.30                          # it is drawn from here (the thicket wolf is gone)


def pw_fog(t):
    """How deep in the fog the wolf on the path still is: it steps out of it, but some fog
    stays on it (it is backlit by the fog, and a little farther than she is)."""
    return lerp(0.9, 0.12, ease("inout", (t - W_SHOW) / 1.35))


def pw_light(t):
    """The backlight behind the wolf: up as it comes out of the fog, held through the face-off."""
    return L.k(t, W_SHOW, 1.0) * (1.0 - 0.35 * L.k(t, 13.3, 0.8))


def draw_pw(f, c, t, mood, eyes=True):
    pw().draw(f, t, c, color=mood.ink, eyes=eyes, breath=True)


def _halo_col(mood):
    return S.mix(mood.fog_at(1.0), S.SNOW, 0.45)


def glow_at(t, cam):
    """Screen position of the backdrop's hot spot: drifts behind the wolf as it appears."""
    k_ = L.k(t, 10.9, 1.4)
    if k_ <= 0.0:
        return (560.0, 820.0)
    x = x_wolf() + 80.0
    sx, sy = cam.to_screen((x, float(PATH.ground_y(x)) - 300.0))
    return (lerp(560.0, sx, k_), lerp(820.0, sy, k_))


def draw_backlight(f, t, mood):
    """Fog glowing behind the wolf (light from beyond it, scattered): additive, world-anchored."""
    k_ = pw_light(t)
    if k_ <= 0.01:
        return
    x = x_wolf() + 60.0
    c0 = (x, float(PATH.ground_y(x)) - 250.0)
    col = _halo_col(mood)
    with f.light(par=1.0, blur=30.0) as c:
        S.glow(c, c0, 640.0, col, 0.20 * k_)
        S.glow(c, (c0[0] - 60.0, c0[1] + 40.0), 300.0, col, 0.16 * k_)


def halo(f, fn, col, alpha, blur):
    """A soft glow of `col` around a silhouette, drawn before it: fn(c) draws the shape."""
    if alpha <= 0.01:
        return
    with f.layer(par=1.0, blur=blur, fog=1.0, fog_color=col, alpha=alpha) as c:
        fn(c)


def draw_path_wolf(f, t, mood):
    if t < W_SHOW:
        return
    fog = pw_fog(t)
    a_in = L.k(t, W_SHOW, 0.3)
    halo(f, lambda c: draw_pw(f, c, t, mood, eyes=False), _halo_col(mood), 0.55 * pw_light(t) * a_in, 16.0)
    with S.depth_layer(f, mood, 1.0, fog, blur=1.0 + 7.0 * smoothstep(0.15, 0.9, fog), alpha=a_in) as c:
        draw_pw(f, c, t, mood)


# ----------------------------------------------------------------------------- snow kicked up
PUFF = {
    "step": dict(n=5, up=(40.0, 150.0), spread=130.0, life=(0.25, 0.5), size=(4.0, 9.0), alpha=0.7, drift=-40.0),
    "skid": dict(n=9, up=(60.0, 220.0), spread=200.0, life=(0.3, 0.7), size=(5.0, 13.0), alpha=0.85, drift=260.0),
    "stop": dict(n=16, up=(80.0, 280.0), spread=260.0, life=(0.4, 0.9), size=(6.0, 15.0), alpha=0.9, drift=150.0),
    "foot": dict(n=8, up=(80.0, 260.0), spread=180.0, life=(0.3, 0.7), size=(5.0, 13.0), alpha=0.85, drift=-90.0),
    "paw": dict(n=7, up=(90.0, 300.0), spread=220.0, life=(0.35, 0.75), size=(6.0, 14.0), alpha=0.85, drift=0.0),
    "wheel": dict(n=10, up=(100.0, 340.0), spread=300.0, life=(0.4, 0.85), size=(6.0, 16.0), alpha=0.85,
                  drift=-120.0),
}


@lru_cache(maxsize=None)
def _puffs():
    """[(t0, x, y, kind)]: every burst of snow (her steps from the run on, the skid, the bolt,
    the wolf's paws)."""
    ev = []
    a = girl()
    for seg in a.segs:
        if type(seg).__name__ != "_Walk":
            continue
        for side, plants in seg.plants.items():
            for (x, tl, _lift, _g) in plants[1:]:
                run = 6.3 <= tl < T_SKID and seg.t0 < T_SKID
                bolt = seg.t0 >= T_BOLT and tl <= 14.6
                if run or bolt:
                    ev.append((tl, x, ground(x), "foot" if bolt else "step"))
    sk = _skid()
    for i in range(6):                  # the slide: spray off the lead heel
        tp = T_SKID + 0.02 + i * (SKID - 0.06) / 5.0
        lx = a.skeleton(tp).j["ankle_" + sk.lead][0] + 0.06 * a.H
        ev.append((tp, lx, ground(lx), "skid"))
    ev.append((T_SKID + SKID - 0.02, sk.lead_x + 0.05 * a.H, ground(sk.lead_x), "stop"))
    ev.append((T_BOLT + 0.02, sk.trail_x, ground(sk.trail_x), "foot"))     # the push-off
    w = pw()
    for (tau, _leg, x, _y, _z) in w.footprints(W_SHOW, 14.6):
        ev.append((tau, x, float(PATH.ground_y(x)), "paw"))
    for i, tp in enumerate((13.58, 13.70, 13.80, 13.88)):                  # the wheel: hindquarters slew
        pz = w.paws(tp)
        for leg in ("LH", "RH") if i % 2 == 0 else ("LF", "RF"):
            x = pz[leg][0]
            ev.append((tp, x, float(PATH.ground_y(x)), "wheel" if leg[1] == "H" else "paw"))
    return tuple(sorted(ev))


def draw_puffs(f, t, mood):
    col = S.mix(mood.snow, S.SNOW, 0.45)
    with S.plane(f, 1.0) as c:
        for i, (t0, x, y, kind) in enumerate(_puffs()):
            if t0 <= t <= t0 + 1.0:
                L.snow_puff(c, x - 14.0, x + 18.0, y + 4.0, t, t0, 400 + i, col, **PUFF[kind])


def draw_skid_marks(f, t, mood):
    """The two grooves her feet plough in the trail (the lead heel's long one)."""
    if t < T_SKID:
        return
    a, sk = girl(), _skid()
    col = S.mix(mood.snow_dark, mood.ink, 0.12)
    te = min(t, T_SKID + SKID)
    with S.plane(f, 1.0) as c:
        for side, x_end, yo, w_ in ((sk.lead, sk.lead_x, 7.0, 8.0), (sk.trail, sk.trail_x, 4.5, 6.0)):
            x0 = sk.f0[side][0] if side == sk.lead else sk.trail_x - 0.10 * a.H
            x1 = a.skeleton(te).j["ankle_" + side][0] + 0.05 * a.H if t < T_SKID + SKID else x_end + 0.05 * a.H
            if x1 - x0 < 6.0:
                continue
            n = 10
            top, bot = [], []
            for j in range(n + 1):
                x = lerp(x0, x1, j / n)
                y = float(PATH.snow_y(x)) + yo
                hh = w_ * 0.5 * (0.35 + 0.65 * j / n)
                top.append((x, y - hh))
                bot.append((x, y + hh))
            draw.poly(c, top + bot[::-1])
            draw.fill(c, col, 0.5)
            # the snow pushed up in front of the heel
            y1 = float(PATH.snow_y(x1)) + yo
            draw.ellipse(c, (x1 + 8.0, y1 - 2.0), 13.0, 5.0)
            draw.fill(c, mood.snow, 0.9)


# ----------------------------------------------------------------------------- light
def mood_at(t):
    import copy
    m = S.mood_mix(S.DAY, S.DEEP, 0.6 + 0.4 * L.k(t, 0.4, 2.6))
    m = copy.copy(m)
    m.shaft_a = 0.0                     # the hush goes on: no light shafts
    return m


def snow_density(t):
    """Snow begins to fall again as she runs, and is falling as s05 opens (0.3)."""
    return 0.3 * L.k(t, 8.6, 4.6)


# ----------------------------------------------------------------------------- render
def _draw_girl(f, c, t, mood):
    a = girl()
    sk = a.skeleton(t)
    grip = L.basket_hand(sk, L.BASKET_SIDE)
    ang = -math.degrees(swing().angle(t))
    L.draw_girl(f, c, sk, a.look)
    L.draw_basket(c, grip, ang, mood.ink)


def her_halo(t):
    """The fog between her and the wolf: a pale glow round her while she is in front of it."""
    return 0.32 * L.k(t, 12.86, 0.2) * (1.0 - L.k(t, 14.1, 0.3))


@lru_cache(maxsize=None)
def x_lip():
    """Where her ground leaves the trail's surface by the lip's sink (6 px): past here she is
    in front of the trail's snow bank, so the lip is drawn under her, not over her feet."""
    xb = x_bolt()
    xs = np.linspace(xb, xb + 380.0, 400)
    d = np.array([ground(x) - float(PATH.ground_y(x)) for x in xs])
    return float(xs[int(np.argmax(d >= 6.0))])


def render(f, t, T):
    cam = camera(t)
    f.set_camera(cam)
    mood = mood_at(t)

    def hook(f_, i, Ly):
        if i == 3:
            draw_bw_body(f_, t, mood)

    FOREST.draw_back(f, mood, glow=glow_at(t, cam), shafts=False, hook=hook)
    TH.draw_thicket(f, mood)
    draw_bw_eyes(f, t, mood)
    FOREST.draw_plane(f, mood)
    prints().draw(f, PATH, t, mood)
    draw_skid_marks(f, t, mood)
    draw_backlight(f, t, mood)
    draw_path_wolf(f, t, mood)
    xl = x_lip()
    PATH.draw_front(f, mood, x0=xl - 4.0, sink=6.0)          # the bank she runs out onto
    hk = her_halo(t)
    if hk > 0.01:
        halo(f, lambda c: _draw_girl(f, c, t, mood), _halo_col(mood), hk, 15.0)
    with f.layer() as c:
        _draw_girl(f, c, t, mood)
    PATH.draw_front(f, mood, x1=xl, sink=6.0)                # the trail's lip (her feet sink)
    draw_puffs(f, t, mood)
    sx = cam.to_screen((ref_x(t), 0.0))[0]
    hw = 230.0 * cam.zoom + 60.0
    clear = (sx - hw, sx + hw)
    if W_SHOW <= t:                     # keep the wolf on the path clear of foreground trunks too
        wx = cam.to_screen((pw().state(t)["x"], 0.0))[0]
        clear = (min(clear[0], wx - 1.2 * hw), max(clear[1], wx + 1.2 * hw))
    FOREST.draw_front(f, mood, lip=False, keep_clear=clear)
    L.snow(f, mood, density=snow_density(t), wind=30.0, gust=12.0, t=t, seed=41)


def motion_blur(t, T):
    """Sub-frames for the run, and more for the bolt, the wheel and the pan into the whip."""
    if 12.85 < t < 14.3:
        return 3
    return 2 if 6.4 < t <= 12.85 else 1


def cues(T):
    W = _W()
    return [
        Cue(-0.5, "forest hush (continues from s03): near silence, a breath of wind high up", -24, dur=9.0),
        Cue(0.5, "her footsteps in snow, steady walk (continuing s03's), stopping at 2.5", -15, dur=2.05),
        Cue(W["wolf"], "SYNC: the eyes open: a low cello/bass sting, a faint breathy shimmer", -10, pan=-0.6,
            dur=2.0),
        Cue(1.6, "something pacing her in the thicket: soft bramble rustle and snow crunch", -19, pan=-0.6,
            dur=1.0),
        Cue(2.55, "she stops and looks back: held breath; one far branch creak", -20, pan=-0.3, dur=0.9),
        Cue(T_GO, "her footsteps again, faster, quickening into a jog", -14, dur=3.04),
        Cue(4.1, "glimpses: heavy paws padding in the thicket, a low huff, a twig snaps", -15, pan=-0.6,
            dur=2.2),
        Cue(5.95, "the eyes flare again: a short low sting", -13, pan=-0.6),
        Cue(W["girls"], "SYNC: she RUNS: timpani hits, quick running feet in snow, panting breath", -8,
            dur=5.57),
        Cue(7.2, "the wolf pacing her: heavy bounding paws through brambles, low huffs", -13, pan=-0.6,
            dur=2.8),
        Cue(8.6, "the snow begins again: a soft rise of wind", -22, dur=5.4),
        Cue(10.0, "the wolf surges past her in the thicket: crashing brush, paws (pan left -> right)", -10,
            pan=-0.4, dur=1.3),
        Cue(11.45, "the wolf steps out onto the path ahead: heavy paw falls, a deep growl building", -11,
            pan=0.4, dur=1.0),
        Cue(T_SKID, "SYNC: the skid: a scraping slide in snow, a spray of snow, her gasp", -7, pan=-0.05,
            dur=SKID),
        Cue(12.40, "the snarl: a deep rumbling growl, lips peeling back", -8, pan=0.3, dur=0.62),
        Cue(T_BOLT, "she bolts: a sharp intake of breath, feet kicking snow", -10, pan=0.0),
        Cue(W_SNAP, "SYNC: the snap: jaws slam shut on air just behind her (a hard wet clack)", -5, pan=0.1),
        Cue(W_TURN[0], "the wolf wheels after her: paws scrabbling, snow thrown up", -10, pan=-0.1,
            dur=W_TURN[1]),
        Cue(13.75, "whip pan into s05: a fast whoosh; the chase music hits", -8, pan=0.3, dur=0.5),
    ]
