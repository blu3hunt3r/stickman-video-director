"""s05 · DEEP SNOW: the chase up the ridge (14.5 s).

IN (whip from s04, 0.5 s; from t = -0.25): Camera zoom 1.0. She runs right on the trail
    (RIDGE x ~ -1245, feet at screen ~(700, 1450), ~780 px/s), the basket in her right (near)
    hand; the wolf behind her (x ~ -1690, screen x ~250) is turning after her. Mood DEEP.
Beats (scene-local s; L8 0.80-9.54):
    -0.25-1.53  the run along the end of the trail; the wolf finishes its turn and gallops
    [off] 1.53  she runs past the last of the path's markers and off the path, uphill
    1.5-4.9     up the slope in ever deeper snow (high knees, slowing); the wolf bounds after
                her and never closes; she glances back at it (~2.4-2.9)
    [ridge] 3.30 the camera cranes up the slope with them
    [snow] 5.165 she trips and falls face-down in the deep snow (a burst of snow); the basket
                flies out of her hand and lands on its side ahead of her
    5.5-6.4     she scrambles on hands and knees and grabs the basket back
    6.4-7.0     she twists round to sit facing the wolf, the basket clutched to her chest
    [stopped] 7.03 the wolf stops, a few body-lengths below her; [waited] 8.81 it sits
    9.45-12.3   she gets up and backs away up to the ridge top; ~11.0 the wolf lifts its head
                and looks past her, over the ridge
    12.3-13.05  she turns to look where it is looking: her back to us; the camera pushes in
                (to 14.05)
OUT (0.75 s dissolve to s06; this scene renders a 0.375 s handle to t = 14.875 with the end
    pose held): mood S.DUSK; she stands still on the crest (RIDGE x = X_END), back to camera
    (yaw -90), hood up, breathing, the basket hanging from her right hand at her side; camera
    zoom 1.25 with her feet (footing) at screen (540, 1376), as VALLEY_VIEW.camera("start")
    shows her in s06 (her joints match s06's girl within ~0.2 px through the dissolve); snow
    density 0.5.
"""
import math
from functools import lru_cache

import numpy as np

from engine import draw
from engine import figure as F
from engine.core import clamp, ease, hash01, lerp, noise1, smoothstep
from engine.creatures import Wolf
from engine.frame import Camera
from engine.motion import Actor, GAITS, arm_ik, foot_ik
from engine.timing import Cue, SceneTiming
from films.red import sets as S
from films.red.scenes import _lib_s02_s06 as L
from films.red.scenes._lib_s04_s08 import Steps, pchip, reach_y

R = S.RIDGE
SET = S.RIDGE_SET
GIRL, H = L.GIRL, L.GH
BODY = GIRL

WOLF_OFF = 3.0                          # the wolf's clock: tau = t + WOLF_OFF (its actions start at 0)
X0 = -3018.0                            # her x at t = -3 (calibrated: x(-0.25) = -1245)
X_END = 2520.0                          # where she ends, on the flat top of the ridge
END_FEET = (540.0, 1376.0)              # her feet (footing) on screen at the cut (s06 IN)
END_ZOOM = 1.25

# her performance (scene-local seconds)
TRIP = 4.93                             # she trips ...
HIT = 5.165                             # ... and hits the snow on [snow]
LIE1 = 5.50                             # pushes up onto hands and knees
CRAWL1 = 6.42                           # the scramble ends (two crawl cycles)
GRAB = 6.30                             # her right hand closes on the basket's handle
SIT = 7.02                              # sitting, facing the wolf ([stopped] 7.03)
RISE0, RISE1 = 9.45, 10.05              # gets up
BACK1 = 12.30                           # backed up to the top
TURN1 = 13.05                           # turned: back to camera
SINK = 10.0                             # her body sinks this far into the powder when down
HUG_R, HUG_L = (8.0, 100.0), (4.0, 108.0)     # the basket hugged to her chest (world phi, elbow)


@lru_cache(maxsize=None)
def _W():
    T = SceneTiming("red", "s05")
    return {w: T.at(w) for w in ("chased", "off", "path", "up", "ridge", "into", "deep", "snow", "And",
                                 "stopped", "waited")}


def sy(x):
    """Top of the snow."""
    return float(R.snow_y(x))


def gy(x):
    """Footing under the snow."""
    return float(R.ground_y(x))


PACK = (2380.0, 2500.0)                 # the wind-packed top of the ridge


def foot_y(x):
    """Her footing: the ground under the deep snow; on the wind-packed top of the ridge the
    crust, 6 px under the snow's surface (she stands on it at the end, as in s06)."""
    g = float(R.ground_y(x))
    w = smoothstep(PACK[0], PACK[1], x)
    if w <= 0.0:
        return g
    return g - w * (float(R.depth(x)) - 6.0)


def surf_deg(x, half=60.0):
    """Rise of the snow surface around x in degrees (+ = rising to the right)."""
    return math.degrees(math.atan2(sy(x - half) - sy(x + half), 2.0 * half))


def _chest(p):
    return p.pitch + sum(p.spine)


def _arm(p, s, phi, elbow=10.0, wrist=0.0, grip=0.4, abd=8.0):
    """Arm by its world angle phi (0 = hanging down, 90 = pointing forward, 180 = up)."""
    p.arms[s].update(sh=phi - _chest(p), elbow=elbow, wrist=wrist, grip=grip, abd=abd)


def _ik(p, s, target, grip=None, wrist=None, elbow_out=False):
    arm_ik(p, s, target, BODY, elbow_out)
    if grip is not None:
        p.arms[s]["grip"] = grip
    if wrist is not None:
        p.arms[s]["wrist"] = wrist


def _leg(p, s, ax, ay, pitch=0.0, toe=0.0, abd=4.0):
    p.legs[s] = {"ik": (ax, ay), "pitch": pitch, "toe": toe, "abd": abd}


def _lerp_pose(a, b, w):
    return F.blend(a, b, clamp(w), BODY)


# ----------------------------------------------------------------------------- the run
RUN = GAITS["child_run"]
SNOW_RUN = RUN.but(step=0.50, knee_lift=0.30, lift=0.20, lean=19.0, crouch=0.06, arm_swing=40.0)
WADE = RUN.but(step=0.40, duty=0.46, knee_lift=0.38, lift=0.27, lean=24.0, crouch=0.07, arm_swing=34.0,
               swing_lead=0.35)
RUN_PATH = [(0.0, RUN, 780.0 / H), (600.0, SNOW_RUN, 700.0 / H), (1300.0, SNOW_RUN, 600.0 / H),
            (4200.0, WADE, 490.0 / H)]


@lru_cache(maxsize=None)
def _run_dy(x0, sigma=0.10, rate=240.0):
    """(ts, dy): the smoothed-minus-raw pelvis height of the plain run (see _smooth_run)."""
    from scipy.ndimage import gaussian_filter1d
    a = Actor(GIRL, L.look_up(), x=x0, ground=foot_y, facing=1, seed=7, name="red")
    a.walk(path=RUN_PATH, at=-3.0)
    seg = a.segs[0]
    ts = np.arange(seg.t0, TRIP + 0.5, 1.0 / rate)
    raw = np.array([seg.root(float(t))[1] for t in ts])
    return ts, gaussian_filter1d(raw, sigma * rate, mode="nearest") - raw


def _smooth_run(a, x0):
    """engine.motion's walk pops the pelvis at footfalls (its leg-reach clamp), badly on this
    slope with running strides (60-160 px in a frame). Ride the pelvis on a Gaussian-smoothed
    copy of the walk's own heights instead: a steady crouched run; a planted foot that ends
    up out of reach hangs a little, under the deep snow."""
    seg = a.segs[0]
    ts, dy = _run_dy(x0)

    def fn(t, ts=ts, dy=dy):
        # an offset on the walk's own height; it fades out exactly as the fall's segment
        # (Actor.free at TRIP, blend 0.10) fades in over the walk
        return float(np.interp(t, ts, dy)) * (1.0 - smoothstep(TRIP, TRIP + 0.10, t))
    a.channel("y", fn, seg.t0, TRIP + 0.12, mode="add", fade=0.0)
    return a


def _run_actor(x0=X0):
    a = Actor(GIRL, L.look_up(), x=x0, ground=foot_y, facing=1, seed=7, name="red")
    a.walk(path=RUN_PATH, at=-3.0)
    return _smooth_run(a, x0)


# ----------------------------------------------------------------------------- the fall and after
class Tumble:
    """One free segment (Actor.free) from the trip to the top of the ridge: the fall
    face-down, the scramble to the basket, the twist round to sit facing the wolf, getting up
    and backing away on hand-planted steps. path(t) -> pelvis, pose(t, u) -> Pose."""

    def __init__(self, run):
        self.run = run
        p0 = run.pose(TRIP)
        self.p0 = p0
        self.x0, self.y0 = p0.x, p0.y
        xa, _ = run.root(TRIP - 0.04)
        xb, _ = run.root(TRIP + 0.04)
        self.v0 = (xb - xa) / 0.08
        sk0 = F.solve(p0, BODY)
        self.ank0 = {s: sk0.j["ankle_" + s] for s in ("L", "R")}
        # where things happen
        self.x_hit = self.x0 + 0.62 * self.v0 * (HIT - TRIP)
        self.x_lie = self.x_hit + 10.0
        self.x_crawl = self.x_lie + 110.0
        self.x_sit = self.x_crawl + 18.0
        self.x_stand = self.x_sit - 0.16 * H
        self.sl_lie = surf_deg(self.x_lie + 0.15 * H, 120.0)
        # the basket lands ahead of her, on its side along the slope, the handle downhill
        self.bk_x = self.x_lie + 0.86 * H
        sd = surf_deg(self.bk_x, 50.0)
        self.bk_ang = -(90.0 + sd)
        gx = self.bk_x - 46.0 * math.cos(math.radians(sd))
        self.bk_grip = (gx, sy(gx) - 21.0)
        self.sl_sit = surf_deg(self.x_sit, 90.0)
        # the backing away: steps up to X_END, feet together at the end
        o = 0.022 * H
        f0 = {"L": self.x_stand - 0.05 * H, "R": self.x_stand + 0.07 * H}
        ts = [10.38, 10.92, 11.42, 11.86, 12.12]
        xs = np.linspace(f0["R"], X_END - o, 5)[1:]
        plants = [(ts[0], "L", xs[0]), (ts[1], "R", xs[1]), (ts[2], "L", xs[2]), (ts[3], "R", xs[3]),
                  (ts[4], "L", X_END + o)]      # feet together at the end (Actor's L +o / R -o)
        self.feet_r = f0
        self.steps = Steps(foot_y, H, f0, plants, swing=0.36, lift=0.20, facing=-1.0)
        tx, xx = [RISE1 - 0.05], [self.x_stand]
        fx = dict(f0)
        for (t_, s_, x_) in plants:
            fx[s_] = x_
            tx.append(t_ + 0.12)
            xx.append(0.5 * (fx["L"] + fx["R"]) + 0.012 * H)
        xx[-1] = X_END
        tx.append(BACK1)
        xx.append(X_END)
        self.bx = pchip(tx, xx)
        self.plants = plants

    # ---------------------------------------------------------------- pelvis
    def _y_lie(self, x):
        return sy(x) - 0.07 * H + SINK

    def _y_crawl(self, x):
        return sy(x) - 0.20 * H + 6.0

    def _y_sit(self, x):
        return sy(x) - 0.085 * H + SINK

    def _y_stand(self, x, crouch=0.0):
        return foot_y(x) - (BODY.hip - 0.006 - crouch) * H

    def _crawl_x(self, t):
        u = clamp((t - (LIE1 + 0.10)) / (CRAWL1 - LIE1 - 0.10))
        surge = 0.5 - 0.5 * math.cos(2.0 * math.pi * 2.0 * u)          # two pulls
        base = ease("inout", u)
        return lerp(self.x_lie, self.x_crawl, 0.75 * base + 0.25 * (base + 0.08 * surge))

    def path(self, t):
        if t < HIT:
            u = (t - TRIP) / (HIT - TRIP)
            tau = t - TRIP
            dec = 0.38 * self.v0 / (HIT - TRIP)
            x = self.x0 + self.v0 * tau - 0.5 * dec * tau * tau
            y = lerp(self.y0, self._y_lie(self.x_hit), u ** 1.7) - 14.0 * math.sin(math.pi * clamp(u * 1.4))
            return x, y
        if t < LIE1:
            k_ = t - HIT
            x = lerp(self.x_hit, self.x_lie, ease("out", k_ / 0.25))
            bounce = 7.0 * math.exp(-10.0 * k_) * math.sin(math.pi * clamp(k_ / 0.16))
            return x, self._y_lie(x) + bounce
        if t < CRAWL1:
            x = self._crawl_x(t)
            w = ease("inout", (t - LIE1) / 0.22)
            bob = 4.0 * math.sin(2.0 * math.pi * 4.0 * (t - LIE1)) * w
            return x, lerp(self._y_lie(x), self._y_crawl(x), w) + bob
        if t < SIT:
            u = (t - CRAWL1) / (SIT - CRAWL1)
            x = lerp(self.x_crawl, self.x_sit, ease("inout", u))
            y = lerp(self._y_crawl(x), self._y_sit(x), ease("in", u))
            return x, y + 10.0 * math.sin(math.pi * clamp((u - 0.75) / 0.25)) * 0.4
        if t < RISE0:
            k_ = t - SIT
            x = self.x_sit + 12.0 * ease("inout", (t - 7.35) / 0.35)            # scoots back
            bounce = -5.0 * math.exp(-9.0 * k_) * math.sin(math.pi * clamp(k_ / 0.18))
            br = 1.6 * math.sin(2.0 * math.pi * (t - SIT) / 0.95)
            return x, self._y_sit(x) + bounce + br
        if t < RISE1:
            u = (t - RISE0) / (RISE1 - RISE0)
            xs = self.x_sit + 12.0
            x = lerp(xs, self.x_stand, ease("inout", clamp(u / 0.8)))
            y0 = self._y_sit(xs)
            y1 = self._y_stand(self.x_stand, 0.03)
            y = lerp(y0, y1, ease("inout", clamp((u - 0.15) / 0.85)))
            return x, y
        x = self.bx(t)
        feet = [self.steps.foot(s, t) for s in ("L", "R")]
        planted = [f_[0] for f_ in feet if f_[3]]
        crouch = 0.03 * (1.0 - smoothstep(BACK1 - 0.5, BACK1, t))
        y = self._y_stand(x, crouch)
        y = reach_y(BODY, H, x, y, planted)
        return x, y

    # ---------------------------------------------------------------- poses
    def _fall(self, t):
        u = clamp((t - TRIP) / (HIT - TRIP))
        x, y = self.path(t)
        p = self.p0.copy()
        p.x, p.y = x, y
        p.yaw = 0.0
        sl = self.sl_lie
        p.pitch = lerp(self.p0.pitch, 90.0 - sl, ease("in", u) * 0.92 + 0.08 * u)
        p.spine = [lerp(a_, b_, u) for a_, b_ in zip(self.p0.spine, [0.0, 4.0, -2.0])]
        p.head = lerp(self.p0.head, -24.0, ease("out", u))
        p.head_yaw = 0.0
        ca = math.cos(math.radians(sl))
        for i, s in enumerate(("L", "R")):
            ax, ay = self.ank0[s]
            stuck = s == "L"                         # this foot stays in the snow a moment
            bx = x - (0.47 + 0.03 * i) * H * ca
            by = self._y_lie(bx) + 0.02 * H
            w = ease("inout", clamp((u - (0.45 if stuck else 0.1)) / (0.55 if stuck else 0.8)))
            _leg(p, s, lerp(ax, bx, w), lerp(ay, by, w) - 0.08 * H * math.sin(math.pi * w) * (0 if stuck else 1),
                 pitch=lerp(0.0, -72.0, w), toe=0.0)
        # arms fly forward to break the fall (the right one flinging the basket away)
        _arm(p, "R", lerp(40.0, 92.0 + sl, ease("out", u)), elbow=lerp(60.0, 15.0, u), wrist=-10.0,
             grip=lerp(0.9, 0.3, smoothstep(0.65, 0.85, u)))
        _arm(p, "L", lerp(-20.0, 84.0 + sl, ease("out", u)), elbow=lerp(70.0, 25.0, u), wrist=-10.0, grip=0.4)
        return p

    def _lie(self, t):
        x, y = self.path(t)
        sl = self.sl_lie
        p = F.Pose(x, y, 0.0)
        k_ = t - HIT
        p.pitch = 90.0 - sl
        p.spine = [0.0, 4.0, -2.0]
        # face in the snow, then the head comes up, looking for the basket
        p.head = lerp(8.0, -38.0, ease("inout", (k_ - 0.08) / 0.24))
        ca = math.cos(math.radians(sl))
        for i, s in enumerate(("L", "R")):
            bx = x - (0.47 + 0.03 * i) * H * ca
            _leg(p, s, bx, self._y_lie(bx) + 0.02 * H, pitch=-72.0)
        # arms stretched out in front on the snow, then they come back under her to push
        push = ease("inout", (t - (LIE1 - 0.20)) / 0.20)
        _arm(p, "R", lerp(92.0 + sl, 30.0, push), elbow=lerp(15.0, 70.0, push), wrist=lerp(-10.0, 60.0, push),
             grip=0.3)
        _arm(p, "L", lerp(84.0 + sl, 22.0, push), elbow=lerp(25.0, 75.0, push), wrist=lerp(-10.0, 60.0, push),
             grip=0.3)
        return p

    def _lie_wrists(self):
        """The wrists where _lie leaves them at LIE1 (the crawl starts from there)."""
        if not hasattr(self, "_lw"):
            sk = F.solve(self._lie(LIE1 - 1e-6), BODY)
            self._lw = {s: tuple(sk.j["wrist_" + s]) for s in ("L", "R")}
        return self._lw

    def _hand_plants(self, s, t):
        """Crawl hand target (wrist) for side s: alternating pulls through the snow."""
        u = clamp((t - (LIE1 + 0.10)) / (CRAWL1 - LIE1 - 0.10))
        ph = 2.0 * u + (0.0 if s == "L" else 0.5)
        n = math.floor(ph)
        fr = ph - n
        reach = 0.27 * H
        x_body = self._crawl_x(t)
        step = 0.5 * (self.x_crawl - self.x_lie)
        x_a = self.x_lie + reach + n * step
        x_b = x_a + step
        e = ease("inout", clamp((fr - 0.55) / 0.45))
        hx = lerp(x_a, x_b, e)
        lift = 0.06 * H * math.sin(math.pi * clamp((fr - 0.55) / 0.45))
        hx = max(min(hx, x_body + 0.40 * H), x_body + 0.12 * H)
        return hx, sy(hx) + 8.0 - lift

    def _crawl(self, t):
        x, y = self.path(t)
        sl = self.sl_lie
        p = F.Pose(x, y, 0.0)
        w = ease("inout", (t - LIE1) / 0.22)
        p.pitch = lerp(90.0 - sl, 90.0 - sl - 10.0, w)
        p.spine = [3.0, 4.0, -2.0]
        p.head = lerp(-38.0, -44.0, w)
        ca = math.cos(math.radians(sl))
        u = clamp((t - (LIE1 + 0.10)) / (CRAWL1 - LIE1 - 0.10))
        for i, s in enumerate(("L", "R")):
            ph = 2.0 * u + (0.25 if s == "L" else 0.75)
            fr = ph - math.floor(ph)
            kick = 0.05 * H * math.sin(math.pi * clamp((fr - 0.5) / 0.5))
            lie_x = x - (0.47 + 0.03 * i) * H * ca
            kx = x - (0.23 + 0.03 * i) * H * ca - 0.04 * H * math.cos(2 * math.pi * fr)
            ax = lerp(lie_x, kx, w)
            ay = lerp(self._y_lie(lie_x) + 0.02 * H, sy(ax) + 0.01 * H, w) - kick * w
            _leg(p, s, ax, ay, pitch=lerp(-72.0, -78.0, w), toe=lerp(0.0, 30.0, w))
        wh = ease("inout", clamp((t - LIE1) / 0.30))
        for s in ("L", "R"):
            hx, hy = self._hand_plants(s, t)
            if wh < 1.0:                                   # from where the hands pushed her up
                lx, ly = self._lie_wrists()[s]
                hx, hy = lerp(lx, hx, wh), lerp(ly, hy, wh)
            if s == "R":                                   # the last reach: to the basket's handle
                k_ = smoothstep(GRAB - 0.24, GRAB, t)
                hx, hy = lerp(hx, self.bk_grip[0] - 14.0, k_), lerp(hy, self.bk_grip[1] - 5.0, k_)
            _ik(p, s, (hx, hy), grip=0.2, wrist=lerp(60.0, 70.0, w))
        if t > GRAB - 0.1:                                 # the right hand closes on the handle
            p.arms["R"]["grip"] = lerp(0.2, 0.95, smoothstep(GRAB - 0.1, GRAB + 0.05, t))
            p.arms["R"]["wrist"] = lerp(p.arms["R"]["wrist"], 10.0, smoothstep(GRAB - 0.1, GRAB + 0.1, t))
        return p

    def _sit_pose(self, t, x=None, y=None):
        """Sitting in the snow facing left (downhill, at the wolf), the basket hugged."""
        if x is None:
            x, y = self.path(t)
        p = F.Pose(x, y, 180.0)
        br = math.sin(2.0 * math.pi * (t - SIT) / 0.95)
        p.pitch = -6.0 + 1.5 * br
        p.spine = [5.0 - 1.2 * br, 4.0, 4.0 + 1.0 * br]
        p.head = 8.0
        sl = self.sl_sit
        for s, k_ in (("L", 0.0), ("R", 0.05)):
            ax = x - (0.33 + k_) * H
            _leg(p, s, ax, sy(ax) + 6.0 - 0.03 * H, pitch=18.0 + 0.5 * sl, toe=0.0)
        _arm(p, "R", HUG_R[0], elbow=HUG_R[1], wrist=4.0, grip=0.95, abd=10.0)
        _arm(p, "L", HUG_L[0], elbow=HUG_L[1], wrist=0.0, grip=0.8, abd=10.0)
        return p

    def _twist(self, t):
        u = clamp((t - CRAWL1) / (SIT - CRAWL1))
        x, y = self.path(t)
        a = self._crawl(CRAWL1)
        a.x, a.y = x, y
        b = self._sit_pose(t, x, y)
        e = ease("inout", u)
        p = _lerp_pose(a, b, e)
        p.yaw = 180.0 * e                      # through 90: her face swings past us
        p.head_yaw = 25.0 * math.sin(math.pi * e)
        return p

    def _rise(self, t):
        u = clamp((t - RISE0) / (RISE1 - RISE0))
        x, y = self.path(t)
        a = self._sit_pose(RISE0)
        p = a.copy()
        p.x, p.y = x, y
        lean = math.sin(math.pi * clamp(u / 0.9))
        p.pitch = lerp(a.pitch, 6.0, ease("inout", u)) + 26.0 * lean
        p.spine = [lerp(v, 2.0, u) for v in a.spine]
        p.head = lerp(8.0, -6.0, u) - 18.0 * lean        # eyes stay on the wolf
        f0 = self.feet_r
        for i, s in enumerate(("L", "R")):
            la = a.legs[s]["ik"]
            (bx, by), bp = foot_ik(f0[s], 0.0, "flat", -1.0, H, foot_y)
            w = ease("inout", clamp((u - 0.1 * i) / 0.55))
            _leg(p, s, lerp(la[0], bx, w), lerp(la[1], by, w) - 0.05 * H * math.sin(math.pi * w),
                 pitch=lerp(a.legs[s]["pitch"], bp, w))
        _arm(p, "R", HUG_R[0], elbow=HUG_R[1], wrist=4.0, grip=0.95, abd=10.0)
        _arm(p, "L", HUG_L[0], elbow=HUG_L[1], wrist=0.0, grip=0.8, abd=10.0)
        return p

    def _back(self, t):
        x, y = self.path(t)
        p = F.Pose(x, y, 180.0)
        end = smoothstep(BACK1 - 0.45, BACK1, t)
        br = math.sin(2.0 * math.pi * (t - SIT) / 1.1)
        p.pitch = lerp(6.0, 0.0, end) + 1.0 * br
        p.spine = [lerp(2.0, 0.0, end), 0.0, 1.0 * br]
        p.head = lerp(-6.0, 0.0, end)
        for s in ("L", "R"):
            (a_, pitch, toe, planted) = self.steps.foot(s, t)
            _leg(p, s, a_[0], a_[1], pitch=pitch, toe=toe, abd=3.0)
        # the basket comes down from her chest to hang in front of her (11.3-12.2)
        lo = ease("inout", (t - 11.3) / 0.9)
        _arm(p, "R", lerp(HUG_R[0], 14.0, lo), elbow=lerp(HUG_R[1], 16.0, lo), wrist=lerp(4.0, -4.0, lo),
             grip=0.95, abd=10.0)
        _arm(p, "L", lerp(HUG_L[0], -4.0, lo), elbow=lerp(HUG_L[1], 12.0, lo), wrist=0.0, grip=lerp(0.8, 0.3, lo),
             abd=lerp(10.0, 7.0, lo))
        return p

    def pose(self, t, u=None):
        if t < HIT:
            return self._fall(t)
        if t < LIE1:
            return self._lie(t)
        if t < CRAWL1:
            return self._crawl(t)
        if t < SIT:
            return self._twist(t)
        if t < RISE0:
            return self._sit_pose(t)
        if t < RISE1:
            return self._rise(t)
        return self._back(t)


@lru_cache(maxsize=None)
def tumble():
    return Tumble(_run_actor())


@lru_cache(maxsize=None)
def girl():
    a = _run_actor()
    tm = tumble()
    a.free(BACK1 - TRIP, tm.path, tm.pose, at=TRIP, end_x=X_END, blend=0.10)
    a.face(180.0)
    a.turn(270.0, dur=TURN1 - BACK1, at=BACK1, via=225.0)
    o = 0.022 * H                       # s06's stance (Actor(..., facing=-90)): L at x + o, R at x - o
    a.state["feet"] = {"L": X_END + o, "R": X_END - o}

    def sway(tt):                       # engine.motion._Stand's idle sway: s06 starts at its t = 0
        return 0.006 * H * noise1(tt * 0.22, a.seed + 1)
    a.state["x"] = X_END + sway(0.0) - sway(14.5 - 1.0 / 24.0)
    a.stand(until=20.0)
    # the basket in her right hand on the run (bent arm, held close)
    a.arm("R", -3.0, TRIP - 0.08, fade=0.08, sh=24.0, elbow=70.0, abd=10.0, wrist=-8.0, grip=0.95)
    # she glances back at the wolf
    a.key("head_yaw", [(2.30, 0.0), (2.55, 115.0, "out3"), (2.80, 110.0), (3.10, 0.0, "inout")], fade=0.1)
    a.key("head", [(2.30, 0.0), (2.55, -8.0), (2.80, -8.0), (3.10, 0.0)], fade=0.1)
    # eyes on the wolf while she sits, gets up and backs away
    a.look_at(SIT + 0.05, 11.75, lambda t: wolf_eye(t), fade=0.3, amount=0.9)
    # the basket hangs from her right hand at her side for the end (as s06 holds it)
    a.arm("R", TURN1 - 0.35, 20.0, fade=0.45, sh=6.0, abd=10.0, elbow=14.0, wrist=-4.0, grip=0.9)
    a.arm("L", TURN1 - 0.35, 20.0, fade=0.45, sh=-4.0, abd=7.0, elbow=10.0)
    a.eyes(HIT - 0.03, 5.40, fade=0.06, open=0.0)          # face down in the snow
    a.blink(1.1)
    a.blink(5.9)
    a.blink(8.2)
    a.blink(10.6)
    a.blink(12.05)
    return a


# ----------------------------------------------------------------------------- the basket
@lru_cache(maxsize=None)
def _run_swing():
    a = _run_actor()
    a.arm("R", -3.0, TRIP - 0.08, fade=0.08, sh=24.0, elbow=70.0, abd=10.0, wrist=-8.0, grip=0.95)

    def pivot(t):
        return L.basket_hand(a.skeleton(t), "R")
    return L.HandSwing(pivot, length=60.0, t0=-1.2, t1=TRIP + 0.2, damping=4.0, gravity=3100.0, clip=3000.0,
                       limit=0.6)


BK_REL = 5.08                           # the basket leaves her hand ...
BK_LAND = 5.42                          # ... and lands on its side in the snow ahead of her


@lru_cache(maxsize=None)
def _basket_flight():
    """Release point and velocity (her hand at BK_REL), landing spot (Tumble's)."""
    a = girl()
    g0 = L.basket_hand(a.skeleton(BK_REL), "R")
    g1 = L.basket_hand(a.skeleton(BK_REL + 0.02), "R")
    tm = tumble()
    return dict(p0=g0, v=((g1[0] - g0[0]) / 0.02, (g1[1] - g0[1]) / 0.02), grip1=tm.bk_grip, ang1=tm.bk_ang)


def basket_state(t, sk):
    """(grip (x, y), angle deg, front_arm) of the basket at t; front_arm: redraw her near arm
    over it (she hugs it)."""
    if t < TRIP - 0.05:
        return L.basket_hand(sk, "R"), -math.degrees(_run_swing().angle(t)), False
    if t < BK_REL:
        a0 = -math.degrees(_run_swing().angle(TRIP - 0.05))
        w = smoothstep(TRIP - 0.05, BK_REL, t)
        return L.basket_hand(sk, "R"), lerp(a0, -40.0, w), False
    bf = _basket_flight()
    g1, a1 = bf["grip1"], bf["ang1"]
    if t < BK_LAND:                     # flung ahead, tumbling, onto its side
        k_ = t - BK_REL
        u = k_ / (BK_LAND - BK_REL)
        x = bf["p0"][0] + lerp(bf["v"][0], 0.0, 0.4 * u) * k_
        x = lerp(x, g1[0], ease("in", u))
        y = lerp(bf["p0"][1], g1[1], u) - 120.0 * math.sin(math.pi * u)
        return (x, y), lerp(-40.0, a1, ease("out", u)), False
    if t < GRAB:
        settle = 3.0 * math.exp(-12.0 * (t - BK_LAND)) * math.sin(14.0 * (t - BK_LAND))
        return g1, a1 + settle, False
    # in her hand again: lifted off its side as she twists round, then hugged to her chest
    hand = L.basket_hand(sk, "R")
    w = smoothstep(GRAB, GRAB + 0.12, t)
    grip = (lerp(g1[0], hand[0], w), lerp(g1[1], hand[1], w))
    if t < SIT:
        ang = lerp(a1, 0.0, ease("inout", (t - CRAWL1) / 0.40))
        return grip, ang, t > CRAWL1 + 0.25
    if t < TURN1 - 0.3:
        sway = 3.0 * math.sin(2.0 * math.pi * (t - SIT) / 0.95)
        hang = ease("inout", (t - 11.3) / 0.9)
        return hand, sway * (1.0 - hang) + 4.0 * hang * math.sin(1.7 * (t - 11.3)), t < 11.9
    return hand, 2.0 * math.sin(0.9 * (t - 14.5)) * smoothstep(TURN1, 14.0, t), False


# ----------------------------------------------------------------------------- the wolf
WX0 = -1690.0                           # at t = -0.25 it is here, turning after her
W_STOP = 1480.0                         # where it stops on [stopped] (root x)
W_GAPS = [(0.9, 700.0), (2.1, 760.0), (3.3, 780.0), (4.55, 800.0)]    # (t, how far behind her)


@lru_cache(maxsize=None)
def _run_ref():
    return _run_actor()                 # a private copy: nothing adds to it


def _girl_run_x(t):
    return _run_ref().root(t)[0]


def _wolf(stop_to):
    w = Wolf(x=WX0, ground=R.ground_y, facing=-1, size=330.0, seed=1)
    G = {k_: dict(v) for k_, v in w.GAIT.items()}
    G["gallop"] = dict(G["gallop"], acc=7.0)            # off the mark fast ...
    G["trot"] = dict(G["trot"], acc=5.0)                # ... and pulls up hard when she falls
    G["stalk"] = dict(G["stalk"], acc=2.4, dec=2.4)
    w.GAIT = G
    o = WOLF_OFF
    w.stand(dur=-0.55 + o, look=10.0)
    w.turn(dur=0.45, via="front")
    tp = -0.10
    for tk, gap in W_GAPS:
        w.gallop(to=_girl_run_x(tk) - gap, dur=tk - tp)
        tp = tk
    w.trot(to=stop_to - 140.0, dur=5.45 - tp)
    w.stalk(to=stop_to, dur=_W()["stopped"] - 5.45)
    w.stand(dur=1.0, look=6.0)
    w.at(_W()["waited"] + o - 0.05)
    w.sit(dur=7.0, look=8.0)
    # a low growl as it stops; later it looks past her, up over the ridge
    w.overlay("snarl", 7.05 + o, dur=0.9, ears=0.6, amount=0.35)
    w.overlay("look", 11.05 + o, dur=4.0, turn=-24.0, head=6.0, neck=58.0)
    return w


@lru_cache(maxsize=None)
def wolf():
    to = W_STOP
    for _ in range(4):                  # the run overshoots its last target a little: aim short
        w = _wolf(to)
        run = [c for c in w.timeline() if c[2] == "run"][0]
        x_end = w.state(run[1] + 0.05)["x"]
        if abs(x_end - W_STOP) < 2.0:
            break
        to -= x_end - W_STOP
    return w


def wolf_eye(t):
    return wolf().head_points(t + WOLF_OFF)["eye"]


def draw_wolf(f, c, t, mood):
    wolf().draw(f, t + WOLF_OFF, c, color=mood.ink, breath=t > 5.0)


# ----------------------------------------------------------------------------- camera, light, weather
@lru_cache(maxsize=None)
def _ref_track():
    """Her smoothed x (the camera follows this, not the stride surges) on a 1/48 s grid."""
    from scipy.ndimage import gaussian_filter1d
    a = girl()
    ts = np.arange(-1.0, 15.5, 1.0 / 48.0)
    xs = np.array([a.root(float(t))[0] for t in ts])
    xs = gaussian_filter1d(xs, 0.22 * 48.0, mode="nearest")
    return ts, xs


def ref_x(t):
    ts, xs = _ref_track()
    return float(np.interp(t, ts, xs))


# camera keys: (t, her feet's screen x, screen y, zoom)
CAM_KEYS = [
    (-0.25, 700.0, 1450.0, 1.00),
    (0.70, 700.0, 1440.0, 0.80),
    (1.53, 690.0, 1440.0, 0.72),
    (3.30, 680.0, 1480.0, 0.64),
    (4.60, 660.0, 1540.0, 0.62),
    (5.40, 680.0, 1460.0, 0.66),
    (7.03, 760.0, 1300.0, 0.70),
    (9.40, 780.0, 1270.0, 0.78),
    (12.20, 800.0, 1290.0, 0.66),
    (14.05, END_FEET[0], END_FEET[1], END_ZOOM),
]


@lru_cache(maxsize=None)
def _cam_keys():
    return L.CamPath(CAM_KEYS)


def camera(t):
    k_ = _cam_keys()(t)
    x = ref_x(t)
    if t >= 13.5:                       # exact at the end: her feet at END_FEET
        x = lerp(x, X_END, smoothstep(13.5, 14.0, t))
    return L.cam_for((x, foot_y(x)), (k_.x, k_.y), k_.zoom)


def mood_at(t):
    return S.mood_mix(S.DEEP, S.DUSK, ease("inout", (t - 1.0) / 12.4))


def snow_density(t):
    return lerp(0.3, 0.5, ease("inout", (t - 6.0) / 7.0))


# ----------------------------------------------------------------------------- snow kicked up
PUFF = {
    "foot": dict(n=7, up=(70.0, 230.0), spread=170.0, life=(0.30, 0.65), size=(5.0, 12.0), alpha=0.85, drift=40.0),
    "paw": dict(n=6, up=(90.0, 300.0), spread=220.0, life=(0.35, 0.75), size=(6.0, 14.0), alpha=0.85, drift=40.0),
    "fall": dict(n=46, up=(160.0, 560.0), spread=460.0, life=(0.6, 1.5), size=(8.0, 22.0), alpha=0.95, drift=60.0),
    "cloud": dict(n=12, up=(30.0, 130.0), spread=260.0, life=(0.9, 1.7), size=(26.0, 58.0), alpha=0.32,
                  grav=60.0, drift=70.0),
    "small": dict(n=9, up=(60.0, 220.0), spread=200.0, life=(0.35, 0.8), size=(5.0, 13.0), alpha=0.85, drift=30.0),
    "sit": dict(n=18, up=(80.0, 300.0), spread=300.0, life=(0.45, 1.0), size=(6.0, 16.0), alpha=0.9, drift=40.0),
}


@lru_cache(maxsize=None)
def _puffs():
    """[(t0, x0, x1, kind)]: every burst of snow in the scene."""
    ev = []
    run = _run_actor()
    for seg in run.segs:
        if type(seg).__name__ != "_Walk":
            continue
        for side, plants in seg.plants.items():
            for (x, tl, _tlift, _g) in plants[1:]:
                if -0.6 < tl < TRIP and x > -400.0:
                    deep = clamp((float(R.depth(x)) - 15.0) / 60.0)
                    ev.append((tl, x - 10.0, x + 26.0, "foot" if deep > 0.25 else "small"))
    for (tau, _leg, x, _y, _z) in wolf().footprints():
        t = tau - WOLF_OFF
        if -0.6 < t < 7.8:
            ev.append((t, x - 16.0, x + 16.0, "paw"))
    tm = tumble()
    ev.append((HIT - 0.03, tm.x_hit - 0.30 * H, tm.x_hit + 0.65 * H, "fall"))
    ev.append((HIT, tm.x_hit - 0.20 * H, tm.x_hit + 0.50 * H, "cloud"))
    bx = tm.bk_x
    ev.append((BK_LAND, bx - 40.0, bx + 30.0, "small"))
    for tp, s_ in ((5.66, "L"), (5.89, "R"), (6.12, "L"), (6.33, "R")):
        hx = tm._hand_plants(s_, tp)[0]
        ev.append((tp, hx - 14.0, hx + 14.0, "small"))
    ev.append((SIT - 0.06, tm.x_sit - 0.42 * H, tm.x_sit + 0.08 * H, "sit"))
    ev.append((RISE0 + 0.30, tm.x_stand - 0.12 * H, tm.x_stand + 0.12 * H, "small"))
    for (tp, _s, x) in tm.plants:
        ev.append((tp, x - 16.0, x + 16.0, "small"))
    return sorted(ev)


def draw_puffs(f, t, mood):
    col = S.mix(mood.snow, S.SNOW, 0.45)
    act = [(i, e) for i, e in enumerate(_puffs()) if e[0] <= t <= e[0] + 1.8]
    if not act:
        return
    soft = [(i, e) for i, e in act if e[3] == "cloud"]
    if soft:                            # the powder cloud: soft, blurred
        with S.soft_layer(f, 1.0, k=3, blur=14.0) as c:
            for i, (t0, x0, x1, kind) in soft:
                L.snow_puff(c, x0, x1, sy(0.5 * (x0 + x1)) + 4.0, t, t0, 700 + i, col, **PUFF[kind])
    with S.plane(f, 1.0) as c:
        for i, (t0, x0, x1, kind) in act:
            if kind != "cloud":
                L.snow_puff(c, x0, x1, sy(0.5 * (x0 + x1)) + 4.0, t, t0, 700 + i, col, **PUFF[kind])


# ----------------------------------------------------------------------------- render
def _draw_girl(f, c, t, mood):
    a = girl()
    sk = a.skeleton(t)
    grip, ang, front = basket_state(t, sk)
    held = not (BK_REL <= t < GRAB)
    if not held:
        L.draw_basket(c, grip, ang, mood.ink)
    L.draw_girl(f, c, sk, a.look)
    if held:
        L.draw_basket(c, grip, ang, mood.ink)
        if front:
            L.draw_arm(c, sk, L.near_side(sk), a.look, a.look.ink or mood.ink)


def render(f, t, T):
    cam = camera(t)
    f.set_camera(cam)
    mood = mood_at(t)
    SET.draw_back(f, mood)
    SET.draw_plane(f, mood)
    SET.spindrift(f, mood, t, 1.0)       # behind them: the veils must not grey the silhouettes
    with f.layer() as c:
        draw_wolf(f, c, t, mood)
        _draw_girl(f, c, t, mood)
    hw = 260.0 * cam.zoom + 80.0
    sx = cam.to_screen((ref_x(t), 0.0))[0]
    SET.draw_front(f, mood, t=t, spindrift=0.0, sink=6.0, keep_clear=(sx - hw, sx + hw))
    draw_puffs(f, t, mood)
    L.snow(f, mood, density=snow_density(t), wind=34.0, gust=14.0, t=t, seed=51)


def motion_blur(t, T):
    """Sub-frames through the chase and the fall (fast legs, the gallop, the burst). The
    camera pans at up to 780 px/s early on: 4 taps keep the trunks and stakes from doubling."""
    if t < 5.6:
        return 4 if t < 1.6 else 3
    return 1


def cues(T):
    W = _W()
    return [
        Cue(-0.25, "the chase: pounding timpani, her quick panting breath, running feet in snow", -8, dur=5.5),
        Cue(0.1, "the wolf: heavy paws bounding in snow, breath, close behind", -12, pan=-0.4, dur=7.0),
        Cue(W["off"], "past the last path stake: a stake knocked, a dull wooden tock", -16, pan=0.1),
        Cue(HIT, "SYNC: she falls face-down in deep snow: a heavy whump, powder burst", -6),
        Cue(BK_LAND, "the basket lands in the snow: wicker creak, muffled", -14, pan=0.2),
        Cue(W["stopped"], "the wolf stops: the paws stop, one low growl", -12, pan=-0.3, dur=1.2),
        Cue(W["waited"], "the wolf sits: snow creak; silence but wind and her breath", -16, pan=-0.3),
        Cue(10.0, "wind across the ridge top, rising; spindrift hiss (through the dissolve)", -16, dur=4.875),
    ]
