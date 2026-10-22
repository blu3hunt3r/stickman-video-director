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
    10.4-11.2    they surge past her and vanish ahead
    11.6-12.3    the WOLF steps onto the path ahead out of the fog: huge, backlit, head low
    12.06-12.5   she skids to a stop at its nose (snow spray), the settle; it growls
OUT (whip "left" to s05, 0.5 s, from 13.75): she bolts off the path to the right, toward
    camera, ducking past its jaws (it snaps at her); it wheels after her (turn via the front,
    13.45-13.90, the same turn s05 finishes); the camera pushes in to zoom 1.0 and accelerates
    right into the whip. Mood DEEP.
"""
import math
from functools import lru_cache

import numpy as np

from engine import draw
from engine import figure as F
from engine.core import clamp, ease, hash01, lerp, noise1, smoothstep
from engine.creatures import Wolf, solve_quadruped, _head_pts, _EYE
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
SKID = 0.44                             # the slide
T_BOLT = 12.80                          # she bolts
YAW_BOLT = 24.0                         # her heading off the path: 24 deg toward camera
DZ = 86.0                               # how far toward camera (down the screen) she gets
HURRY = L.WALK.but(speed=1.2, step=0.40, lean=6.0, arm_swing=24.0, bob=0.016, crouch=0.04)
JOG = GAITS["child_run"].but(speed=1.6, step=0.58, duty=0.42, lean=9.0)
RUN = GAITS["child_run"]
BOLT = GAITS["child_run"].but(speed=2.35, step=0.82, lean=17.0, arm_swing=52.0, ramp_in=(0.62, 0.86))
RUN_CARRY = dict(sh=24.0, elbow=70.0, abd=10.0, wrist=-8.0, grip=0.95)     # = s05's run carry


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
        """Pelvis lowered (fraction of height) from standing."""
        a, ts, tb = self.a, self.t_s, self.t_b
        c = lerp(0.03, 0.075, smoothstep(ts, ts + 0.2, t))
        c = lerp(c, 0.035, smoothstep(ts + SKID + 0.05, ts + SKID + 0.4, t))
        c = lerp(c, 0.085, smoothstep(tb - 0.2, tb, t))
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
        keys = [(ts, self.pitch0), (ts + 0.16, -16.0), (te - 0.04, -12.0), (te + 0.14, 11.0), (te + 0.42, 3.0),
                (tb - 0.22, 4.0), (tb, 13.0)]
        p.pitch = _pw(keys, t)
        back = smoothstep(ts, ts + 0.15, t) * (1.0 - smoothstep(te - 0.05, te + 0.15, t))
        hunch = smoothstep(te, te + 0.4, t)
        p.spine = [-2.0 * back + 2.0 * hunch, -3.0 * back + 4.0 * hunch, -2.0 * back + 3.0 * hunch]
        p.head = -0.6 * p.pitch - 2.0 * hunch
        # the free (far, left) arm: thrown forward for balance, then drawn in, then back to drive
        fl = smoothstep(ts, ts + 0.14, t) * (1.0 - smoothstep(te + 0.05, te + 0.35, t))
        draw_in = smoothstep(te + 0.05, te + 0.35, t) * (1.0 - smoothstep(tb - 0.2, tb, t))
        drive = smoothstep(tb - 0.2, tb, t)
        p.arms["L"] = dict(sh=72.0 * fl + 28.0 * draw_in - 26.0 * drive, abd=10.0,
                           elbow=30.0 * fl + 92.0 * draw_in + 70.0 * drive, wrist=4.0, grip=0.4 + 0.3 * draw_in)
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
    a.blink(2.20)
    a.blink(3.30)
    a.blink(5.10)
    a.blink(9.30)
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


# (t, screen x, screen y of the trail under her, zoom)
CAM_KEYS = [
    (1.00, 540.0, 1350.0, 1.00),
    (2.50, 600.0, 1345.0, 0.90),
    (3.40, 640.0, 1340.0, 0.86),
    (5.80, 610.0, 1345.0, 0.82),
    (7.20, 540.0, 1350.0, 0.80),
    (10.40, 520.0, 1350.0, 0.80),
    (11.70, 400.0, 1345.0, 0.77),
    (12.50, 310.0, 1345.0, 0.76),
    (12.85, 320.0, 1350.0, 0.78),
    (13.75, 660.0, 1362.0, 1.00),
    (14.30, 520.0, 1362.0, 1.00),
]


@lru_cache(maxsize=None)
def _cam_keys():
    return L.CamPath(CAM_KEYS)


def _cam_own(t):
    k_ = _cam_keys()(t)
    x = ref_x(t)
    return L.cam_for((x, float(PATH.ground_y(x))), (k_.x, k_.y), k_.zoom)


def camera(t):
    if t <= 1.0:
        return L.s03_cam(t + 14.0)
    return L.cam_mix(L.s03_cam(t + 14.0), _cam_own(t), ease("inout", (t - 1.0) / 1.3))


# ----------------------------------------------------------------------------- light
def mood_at(t):
    import copy
    m = S.mood_mix(S.DAY, S.DEEP, 0.6 + 0.4 * L.k(t, 0.4, 2.6))
    m = copy.copy(m)
    m.shaft_a = 0.0                     # the hush goes on: no light shafts
    return m


# ----------------------------------------------------------------------------- render
def _draw_girl(f, c, t, mood):
    a = girl()
    sk = a.skeleton(t)
    grip = L.basket_hand(sk, L.BASKET_SIDE)
    ang = -math.degrees(swing().angle(t))
    L.draw_girl(f, c, sk, a.look)
    L.draw_basket(c, grip, ang, mood.ink)


def render(f, t, T):
    cam = camera(t)
    f.set_camera(cam)
    mood = mood_at(t)
    FOREST.draw_back(f, mood, shafts=False)
    FOREST.draw_plane(f, mood)
    prints().draw(f, PATH, t, mood)
    with f.layer() as c:
        _draw_girl(f, c, t, mood)
    sx = cam.to_screen((ref_x(t), 0.0))[0]
    hw = 230.0 * cam.zoom + 60.0
    FOREST.draw_front(f, mood, keep_clear=(sx - hw, sx + hw))


def motion_blur(t, T):
    return 2 if 6.4 < t < 14.3 else 1


def cues(T):
    return []
