"""s02 · CASH: the evening of the dive. He takes the money from a man who never asks his name.
(15.0 s, surface at late dusk; the moon over the stern exactly as in s03: (612, 598 above the
horizon), r 74, veil 0.3.)

IN  (scroll 'down' from s01, 1.5 s, -0.75..0.75): s01's rising camera one screen higher
    (s01.camera(10 + t) shifted up by H/zoom), so the seam is exact: the red hose and the
    bubbles run up through x ~520-640 and burst at the waterline (screen y ~619 at -0.75,
    ~521 at 0.75), the hull's underside dark against the bright skin of the surface.
Beats (scene-local s; words from the timeline):
  0.0-2.05    the camera keeps rising through the waterline and swings out to a wide of the
              boat on the swell; the present's hose and bubbles dissolve (0.9-1.9): this is
              the evening before
  2.05-3.2    push in on the stern working deck: the diver (suited, bare-headed, the bonnet
              in his lap) sits on the pump box; the client stands at the winch, cigar
  2.52-[paid 3.02]  the client's hand goes into his coat, the envelope comes out, held out
  4.54-[Cash 5.26]  the diver reaches and takes it; holds it up; 6.12-6.44 tucks it away
  [L4 7.0]-8.0  the client turns away to the sea; the camera finds his profile on the moon
              (8.1); 7.9-8.62 the diver gets up with the bonnet
  [name 8.50] the client draws on the cigar: the ember flares; smoke drifts off
  8.62-11.26  the diver walks aft behind him (lead boots), the hose paying out off the coil,
              to forward of the davit post (headroom)
  11.56-12.34 he lifts the bonnet over his head (it eclipses the moon to a crescent,
              ~12.2-12.6); 12.34-13.19 lowers it on; the wind presses the client's coat
              back from 11.6
  12.39-13.49 [plan] the push-in to the client's belt (knife pommel at screen (470, 840),
              zoom 1.55); [using 13.59] the glint
  13.28-[it 14.08] the client reaches over with both hands (13.28) and turns the bonnet home
              (13.86): CLANK on [it] with a camera jolt; the port glass darkens (14.11-14.25)
              and the diver's eyes glow behind it (14.24-14.38)
  14.22-14.84 the diver swings round the davit post onto the ladder; the camera pulls back
              and tilts down (14.30-15.5) into s03's composition
OUT (scroll 'up' into s03, 1.25 s, 14.375..15.625): from 14.84 the diver and the hose are
    s03's own (s03.DIVER.pose(t - 15), s03.HOSE.points(t - 15)) and from 15.5 the camera is
    s03's (s03.camera(t - 15)), so the last frames ARE s03's composition: the diver on the
    ladder (helmet at screen ~(654, 206) at 15.5, on the moon at (612, 162)), waterline 760.
    The client still stands at the winch (head at screen ~(244, 119); s03 does not draw him).
"""
import functools
import math

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor, arm_ik
from engine.timing import Cue
from films.salvage import cast
from films.salvage import sets as S
from films.salvage import sets_boat as SB
from films.salvage.scenes import _lib_s01_s03_s16 as LIB
from films.salvage.scenes import _lib_s02_s12 as K

PAL = S.PAL
INK = PAL.ink
RED = S.RED
ss = smoothstep
D2R = math.pi / 180.0

# ----------------------------------------------------------------------------- world (as s03)
BOAT = S.Boat()
DUSK = 0.25
BRIGHT = lerp(0.62, 1.0, DUSK)
MOON = (612.0, 598.0)          # screen x, height above the horizon (s03: behind his helmet)
MOON_R = 74.0
VEIL = 0.3
B_IN = 0.86                    # s01's water brightness (the seam)


@functools.lru_cache(maxsize=1)
def _s01():
    from films.salvage.scenes import s01_red_line as M
    return M


@functools.lru_cache(maxsize=1)
def _s03():
    from films.salvage.scenes import s03_descent as M
    return M


def deck_rest(x):
    """Deck height at world x with the boat at rest (the frame the figures are animated in)."""
    return SB.deck_local(x - BOAT.x)


def on_boat(p, t):
    """Rest-frame point -> world at t (rides the swell with the boat)."""
    return BOAT.to_world((p[0] - BOAT.x, p[1]), t)


def boat_shift(p, t):
    w = on_boat(p, t)
    return (w[0] - p[0], w[1] - p[1])


def _shift_pose(p, d):
    p.x += d[0]
    p.y += d[1]
    for s in ("L", "R"):
        lg = p.legs[s]
        if "ik" in lg:
            lg["ik"] = (lg["ik"][0] + d[0], lg["ik"][1] + d[1])
    return p


# ----------------------------------------------------------------------------- beats
_FALLBACK = dict(l3=1.2, paid=3.023, advance=3.685, cash=5.264, l4=7.0, name=8.497, l5=10.0, name2=11.649,
                 dont=12.555, plan=12.926, using=13.588, it=14.076, l5_end=14.424)


def _beats(T):
    b = dict(_FALLBACK)
    try:
        b.update(paid=T.at("paid"), advance=T.at("advance"), cash=T.at("Cash"), name=T.at("name"),
                 name2=T.at("name", 1), dont=T.at("don't", 1), plan=T.at("plan"), using=T.at("using"),
                 it=T.at("it"))
    except Exception:
        pass
    for k, n in (("l3", 3), ("l4", 4), ("l5", 5)):
        try:
            b[k] = T.line(n)[0]
            if n == 5:
                b["l5_end"] = T.line(n)[1]
        except Exception:
            pass
    return b


def _key(b):
    return tuple(sorted((k, round(v, 4)) for k, v in b.items()))


# ----------------------------------------------------------------------------- the people
LOOK_BARE = cast.diver(helmet=False)
LOOK_HELM = cast.diver()
GLASS = cast.GLASS
GLASS_LIT = S.mix(GLASS, PAL.moon, 0.15)          # the empty bonnet's port catches the sky

SEAT = (-850.0, -386.0)          # diver's pelvis on the pump lid (rest frame)
FEET_SEAT = {"R": (-724.0, deck_rest(-724.0) - 27.0), "L": (-750.0, deck_rest(-750.0) - 27.0)}
X_UP = -812.0                    # where he stands up
X_STOP = -318.0                  # where he puts the bonnet on: forward of the davit post (headroom)
CLIENT_X = -530.0                # the client stands at the winch
ENV_T = (-632.0, -552.0)         # where the envelope is held out (rest frame)
CARRY = (84.0, -104.0)           # bonnet centre relative to the pelvis while carried (facing +x)


class Rig:
    """Everything that depends on the beat times (built once per process per timeline)."""

    def __init__(self, b):
        self.b = b
        s03 = _s03()
        self.bonnet = K.Bonnet(s03.DIVER.skeleton(-1.0), LOOK_HELM)
        cash, it = b["cash"], b["it"]
        # --- times
        self.t_env0 = b["paid"] - 0.50          # hand into the coat
        self.t_env1 = b["paid"] - 0.20          # envelope comes out
        self.t_grab0 = cash - 0.72              # the diver reaches
        self.t_tuck0, self.t_tuck1 = cash + 0.86, cash + 1.18
        self.t_turn0, self.t_turn1 = b["l4"], b["l4"] + 1.0
        self.t_up0 = max(self.t_tuck1 + 0.4, self.t_turn0 + 0.9)      # gets up once the client has turned away
        self.t_up1 = self.t_up0 + 0.72
        # --- diver: seated -> stands with the bonnet -> walks aft (rest frame)
        ref = Actor(cast.DIVER, LOOK_BARE, x=X_UP, ground=deck_rest, facing=1, t0=-2.0, seed=21)
        ref.stand(40.0, at=-2.0, idle=0.6)
        self.ref_stand = ref
        A = Actor(cast.DIVER, LOOK_BARE, x=SEAT[0], ground=deck_rest, facing=1, t0=-2.0, seed=21, name="diver")
        A0 = Actor(cast.DIVER, LOOK_BARE, x=SEAT[0], ground=deck_rest, facing=1, t0=-2.0, seed=21)
        for act in (A, A0):
            act.free(self.t_up1 + 2.0, self._seat_path, self._seat_pose, at=-2.0, end_x=X_UP, blend=0.3)
            act.walk(to=X_STOP, gait="heavy", speed=0.45, at=self.t_up1, blend=0.3)
            act.stand(until=40.0, idle=0.4)
        self.diver, self.diver0 = A, A0
        self.t_arrive = A.segs[-1].t0
        self.t_lift0 = max(self.t_arrive + 0.3, b["l5"] + 0.35)
        self.t_lift1 = self.t_lift0 + 0.78
        self.t_low1 = self.t_lift1 + 0.85
        self.t_reach0, self.t_twist0 = it - 0.80, it - 0.22
        self.t_free0 = it + 0.04
        self.t_sw0 = it + 0.14                  # the swing onto the ladder
        self.t_sw1 = self.t_sw0 + 0.62
        # head: up at the client while he is paid, down at the envelope, up at the client as he
        # turns away, ahead on the walk; back as the bonnet goes up, a nod as it comes down
        for act in (A, A0):
            act.key("head", [(-2.0, -7.0), (b["paid"] - 0.3, -7.0), (b["paid"] + 0.4, 2.0), (cash - 0.5, 4.0),
                             (cash + 0.6, 14.0), (self.t_tuck1, 10.0), (self.t_tuck1 + 0.5, -5.0),
                             (self.t_up0, -3.0), (self.t_up1, 4.0), (self.t_lift0, 4.0), (self.t_lift1, -8.0),
                             (self.t_low1 - 0.2, 6.0), (self.t_low1 + 0.3, 3.0), (40.0, 3.0)], fade=0.0)
            act.key("pitch", [(self.t_lift0 - 0.2, 0.0), (self.t_lift1, -6.0), (self.t_low1, 2.0),
                              (self.t_low1 + 0.4, 0.0)], mode="add", fade=0.0)
        # arms: the R (near) hand reaches for the envelope, holds it up, tucks it in; the L hand
        # keeps the bonnet in his lap; both carry it from the rise, lift it over his head and
        # lower it on, then let go
        A.reach("R", self.t_grab0, cash, self._env_far_end, fade=0.42, grip=0.9)
        A.reach("R", cash, cash + 0.5, self._env_far_end, fade=0.0, grip=0.95)
        A.reach("R", cash + 0.5, self.t_tuck0, self._env_hold, fade=0.34, grip=0.95)
        A.reach("R", self.t_tuck0, self.t_tuck1, self._tuck_pt, fade=0.18, grip=0.8)
        A.reach("L", -2.0, self.t_low1 + 0.05, lambda t: self._grip(t, "L"), fade=0.35, grip=0.9)
        A.reach("R", self.t_tuck1 + 0.12, self.t_low1 + 0.12, lambda t: self._grip(t, "R"), fade=0.35, grip=0.9)
        A.arm("L", self.t_low1 + 0.05, 40.0, fade=0.45, sh=8.0, abd=12.0, elbow=26.0, grip=0.35)
        A.arm("R", self.t_low1 + 0.12, 40.0, fade=0.45, sh=-2.0, abd=12.0, elbow=22.0, grip=0.35)
        A.blink(1.9)
        A.blink(cash + 1.4)
        A.blink(self.t_up1 + 1.6)
        # --- client: at the winch, facing the diver; turns away to the sea on L4
        C = Actor(cast.CLIENT, cast.client(), x=CLIENT_X, ground=deck_rest, facing=-1, t0=-2.0, seed=3,
                  name="client")
        C0 = Actor(cast.CLIENT, cast.client(), x=CLIENT_X, ground=deck_rest, facing=-1, t0=-2.0, seed=3)
        for act in (C, C0):
            act.stand(until=self.t_turn0, idle=0.35)
            act.turn(yaw=0.0, dur=self.t_turn1 - self.t_turn0, at=self.t_turn0, via=-90.0)
            act.stand(until=40.0, idle=0.35)
            act.key("head", [(-2.0, 9.0), (cash + 0.4, 9.0), (cash + 1.0, 2.0), (self.t_turn1, 0.0),
                             (b["name"] - 0.3, 0.0), (b["name"] + 0.05, -6.0), (b["name"] + 0.7, -2.0),
                             (b["l5"], 3.0), (self.t_reach0, 4.0), (it - 0.1, 7.0), (it + 0.7, 3.0), (40.0, 3.0)],
                    fade=0.0)
            act.key("spine", [(-2.0, 0.0), (self.t_reach0, 0.0), (it - 0.25, 2.5), (it + 0.6, 0.5), (40.0, 0.5)],
                    fade=0.0)
        self.client, self.client0 = C, C0
        # the envelope: hand into the coat, out, held out; released after Cash
        C.reach("L", self.t_env0, self.t_env1, self._coat_pocket, fade=0.26, grip=0.7)
        C.reach("L", self.t_env1, cash + 0.06, ENV_T, fade=0.24, grip=0.9)
        # the lock: both hands on the bonnet (he faces +x: near = R)
        C.reach("R", self.t_reach0, self.t_free0, lambda t: self._bonnet_grip(t, "R"), fade=0.40, grip=0.95)
        C.reach("L", self.t_reach0 + 0.08, self.t_free0, lambda t: self._bonnet_grip(t, "L"), fade=0.40,
                grip=0.95)
        C.eyes(-2.0, 40.0, fade=0.0, glow=0.32)
        # --- framing points (world): his head on the moon (L4), the bonnet at the top of the
        # lift (L5), the knife (plan/using), the helmet at the lock
        tn = b["name"]
        self.head_pro = on_boat(C0.skeleton(tn).j["head"], tn)
        self.over_pt = on_boat(self.bonnet_rest(self.t_lift1)[0], self.t_lift1)
        tu = b["using"]
        self.knife_pt = on_boat(K.knife_points(K.knife_on_belt(C0.skeleton(tu)))["pommel"], tu)
        self.helm_pt = on_boat(costume.helmet_frame(A0.skeleton(it))[0], it)

    # ---------------------------------------------------------------- diver base motion
    def _seat_path(self, t):
        u = ease("inout", (t - self.t_up0) / (self.t_up1 - self.t_up0))
        sy = self.ref_stand.pose(t).y
        return (lerp(SEAT[0], X_UP, u), lerp(SEAT[1], sy, u) - 26.0 * math.sin(math.pi * u))

    def _seat_pose(self, t, u_):
        x, y = self._seat_path(t)
        p = F.Pose(x, y, 0.0)
        br = math.sin(2.0 * math.pi * t / 3.6)
        p.legs["R"] = {"ik": FEET_SEAT["R"], "pitch": 0.0, "toe": 0.0, "abd": 3.0}
        p.legs["L"] = {"ik": FEET_SEAT["L"], "pitch": 0.0, "toe": 0.0, "abd": 3.0}
        p.pitch = 9.0 + 1.0 * br
        p.spine = [4.0, 3.0 + 0.8 * br, 2.0]
        p.head = -4.0
        p.arms["R"] = dict(sh=24.0, abd=8.0, elbow=72.0, wrist=0.0, grip=0.45)
        p.arms["L"] = dict(sh=18.0, abd=8.0, elbow=62.0, wrist=0.0, grip=0.6)
        p.eyes = dict(open=1.0, glow=1.0, look=0.0)
        w = ease("inout", (t - self.t_up0) / (self.t_up1 - self.t_up0))
        if w <= 0.0:
            return p
        q = self.ref_stand.pose(t)
        q.x, q.y = x, y
        bl = F.blend(p, q, w, cast.DIVER)
        bl.pitch += 22.0 * math.sin(math.pi * w)       # lean forward to get up
        bl.x, bl.y = x, y
        return bl

    # ---------------------------------------------------------------- bonnet placement
    def _pel0(self, t):
        return self.diver0.skeleton(t).j["pelvis"]

    def bonnet_rest(self, t):
        """(centre, angle, flip) of the bonnet in the rest frame while he is on deck."""
        sk = self.diver0.skeleton(t)
        R = self.bonnet.R
        pel = sk.j["pelvis"]
        if t < self.t_lift0:
            knee = sk.j["knee_R"]
            lap = (lerp(pel[0], knee[0], 0.58) + 4.0, lerp(pel[1], knee[1], 0.58) - R * 0.96)
            fx = math.cos(sk.pose.yaw * D2R)
            walking = ss(self.t_up1, self.t_up1 + 0.4, t) * (1.0 - ss(self.t_arrive - 0.3, self.t_arrive + 0.1, t))
            bob = 4.0 * math.sin(2.0 * math.pi * (t - self.t_up1) / 1.6) * walking
            carry = (pel[0] + fx * CARRY[0], pel[1] + CARRY[1] + bob)
            w = ease("inout", (t - (self.t_up0 - 0.05)) / (self.t_up1 - self.t_up0 + 0.1))
            c = (lerp(lap[0], carry[0], w), lerp(lap[1], carry[1], w) - 30.0 * math.sin(math.pi * w))
            return c, 6.0 * (1.0 - w), True
        hc = costume.helmet_frame(sk)[0]
        carry = (pel[0] + CARRY[0], pel[1] + CARRY[1])
        over = (hc[0] + 8.0, hc[1] - 2.3 * R)
        if t < self.t_lift1:
            u = ease("inout", (t - self.t_lift0) / (self.t_lift1 - self.t_lift0))
            c = (lerp(carry[0], over[0], u) + 46.0 * math.sin(math.pi * u), lerp(carry[1], over[1], u))
            return c, 10.0 * u, True
        if t < self.t_low1:
            u = ease("inout", (t - self.t_lift1) / (self.t_low1 - self.t_lift1))
            return (lerp(over[0], hc[0], u), lerp(over[1], hc[1], u)), 10.0 + 1.0 * u, True
        return hc, self.twist(t), True

    def _grip(self, t, side):
        """The diver's hands on the bonnet (rest frame): under it while it is carried, either
        side of the rim while it goes up and comes down."""
        c, ang, fl = self.bonnet_rest(t)
        R = self.bonnet.R
        w = ss(self.t_lift0 - 0.35, self.t_lift0, t)
        if side == "R":
            ox, oy = lerp(0.30, 0.72, w), lerp(0.92, 0.68, w)
        else:
            ox, oy = lerp(-0.62, -0.72, w), lerp(0.70, 0.68, w)
        return (c[0] + ox * R, c[1] + oy * R)

    def twist(self, t):
        """Bonnet roll (deg): lowered on 1/8 turn off, turned home on [it] (with a seat bump)."""
        it = self.b["it"]
        if t < self.t_twist0:
            return 11.0
        if t < it:
            return lerp(11.0, -0.6, ease("in", (t - self.t_twist0) / (it - self.t_twist0)))
        u = t - it
        return -0.6 * math.exp(-u / 0.05) * math.cos(2 * math.pi * 9.0 * u)

    # ---------------------------------------------------------------- envelope
    def _coat_pocket(self, t):
        sk = self.client0.skeleton(t)
        ch, nk = sk.j["chest"], sk.j["neck"]
        return (lerp(ch[0], nk[0], 0.3) - 26.0, lerp(ch[1], nk[1], 0.3) + 6.0)

    def _env_far_end(self, t):
        """The diver's grip on the envelope: its far (left) end while the client holds it (the
        client's rest frame mapped into the diver's, so the hands meet on the swell)."""
        u = ease("inout", (t - self.t_env1) / 0.42)
        p = self._coat_pocket(t)
        hand = (lerp(p[0], ENV_T[0], u) + 6.0, lerp(p[1], ENV_T[1], u) + 10.0)
        dc = boat_shift((CLIENT_X, -500.0), t)
        dd = boat_shift((SEAT[0], -500.0), t)
        return (hand[0] - 72.0 + dc[0] - dd[0], hand[1] + 6.0 + dc[1] - dd[1])

    def _env_hold(self, t):
        pel = self._pel0(t)
        return (pel[0] + 108.0, pel[1] - 214.0)

    def _tuck_pt(self, t):
        ch = self.diver0.skeleton(t).j["chest"]
        return (ch[0] + 34.0, ch[1] + 10.0)

    # ---------------------------------------------------------------- the lock
    def _bonnet_grip(self, t, side):
        """The client's hands on the bonnet (in HIS rest frame): near (R) hand on its flank
        toward him, far (L) hand over its crown; they turn with it."""
        c, ang, fl = self.bonnet_rest(t)
        R = self.bonnet.R
        a = math.radians(ang)
        loc = (-1.02 * R, 0.20 * R) if side == "R" else (-0.40 * R, -0.94 * R)
        w = (c[0] + loc[0] * math.cos(a) - loc[1] * math.sin(a), c[1] + loc[0] * math.sin(a) + loc[1] * math.cos(a))
        dd = boat_shift((X_STOP, -500.0), t)
        dc = boat_shift((CLIENT_X, -500.0), t)
        return (w[0] + dd[0] - dc[0], w[1] + dd[1] - dc[1])


@functools.lru_cache(maxsize=2)
def _rig_for(key):
    return Rig(dict(key))


def rig(T):
    return _rig_for(_key(_beats(T)))


# ============================================================================= camera
WIDE = (-760.0, 150.0, 0.50)
MW = (-660.0, -430.0, 0.95)
MW_ENV = (-716.0, -470.0, 1.10)
Z_PRO, Z_TWO_W, Z_TWO, Z_BELT, Z_CLANK = 1.20, 1.08, 1.25, 1.55, 1.4
T_IN = 0.75
T_WIDE = 2.05
T_S03 = 15.5                   # from here on the camera is s03's own (s03.camera(t - 15))


def _cam_in(t):
    """s01's rising camera one screen higher: the IN's exact seam (t <= T_IN)."""
    c = _s01().camera(10.0 + t)
    return (c.x, c.y - H / c.zoom, c.zoom)


def _lz(c):
    return (c[0], c[1], math.log(c[2]))


def _frame_on(p, sx, sy, z):
    """Camera (x, y, zoom) that puts world point p at screen (sx, sy) at zoom z."""
    return (p[0] - (sx - W / 2) / z, p[1] - (sy - H / 2) / z, z)


def _nudge(c, dx, dy, kz=1.0):
    return (c[0] + dx, c[1] + dy, c[2] * kz)


@functools.lru_cache(maxsize=2)
def _cam_keys_for(key):
    rg = _rig_for(key)
    b = rg.b
    s03 = _s03()
    c15, c15b = s03.camera(T_S03 - 15.0), s03.camera(T_S03 - 15.0 + 0.02)
    v15 = ((c15b.x - c15.x) / 0.02, (c15b.y - c15.y) / 0.02, 0.0)
    end = _lz((c15.x, c15.y, c15.zoom))
    a, z = _cam_in(T_IN - 0.02), _cam_in(T_IN)
    v_in = ((z[0] - a[0]) / 0.02, (z[1] - a[1]) / 0.02, (math.log(z[2]) - math.log(a[2])) / 0.02)
    drift = (6.0, -5.0, 0.008)
    hz = H / 2 - MOON[1]                                  # the moon's screen y (eye level at mid frame)
    pro = _frame_on(rg.head_pro, MOON[0] + 4.0, hz + 8.0, Z_PRO)          # his profile on the moon
    two_w = _frame_on(rg.over_pt, MOON[0] + 26.0, hz + 22.0, Z_TWO_W)     # the two of them, wider
    two = _frame_on(rg.over_pt, MOON[0] + 26.0, hz + 22.0, Z_TWO)         # the bonnet eclipses it
    belt = _frame_on(rg.knife_pt, 470.0, H / 2 - 120.0, Z_BELT)           # the knife over the horizon
    clank = _frame_on(rg.helm_pt, 650.0, 600.0, Z_CLANK)                  # the lock, the eyes
    t_two, t_belt, t_clank = rg.t_lift1 + 0.05, b["using"] - 0.1, b["it"] + 0.22
    lt, lb, lc = _lz(two), _lz(belt), _lz(clank)
    v_two = tuple(0.55 * (q - p) / (t_belt - t_two) for p, q in zip(lt, lb))
    v_clank = tuple(0.35 * (q - p) / (T_S03 - t_clank) for p, q in zip(lc, end))
    v_w = tuple(0.5 * (q - p) / (t_two - rg.t_arrive) for p, q in zip(_lz(two_w), lt))
    return [
        (T_IN, _lz(z), v_in),
        (T_WIDE, _lz(WIDE), (40.0, -90.0, 0.06)),
        (3.2, _lz(MW), drift),
        (b["cash"] - 0.3, _lz(_nudge(MW, -10.0, -16.0, 1.02)), drift),
        (b["cash"] + 0.75, _lz(MW_ENV), (0.0, 0.0, 0.0)),
        (rg.t_turn0 + 0.1, _lz(_nudge(MW_ENV, 8.0, -4.0)), (8.0, 0.0, 0.0)),
        (rg.t_turn1 + 0.1, _lz(pro), (4.0, -2.0, 0.004)),
        (b["name"] + 0.35, _lz(_nudge(pro, 3.0, -2.0, 1.005)), (8.0, 0.0, 0.0)),
        (b["name"] + 1.2, _lz(_nudge(two_w, -26.0, 6.0, 0.99)), (10.0, -2.0, 0.004)),
        (rg.t_arrive, _lz(two_w), v_w),
        (t_two, lt, v_two),
        (t_belt, lb, (-4.0, 2.0, 0.01)),
        (b["using"] + 0.12, _lz(_nudge(belt, -1.0, 1.0, 1.002)), (0.0, 0.0, 0.0)),
        (t_clank, lc, v_clank),
        (T_S03, end, v15),
    ]


def camera_at(t, rg):
    if t <= T_IN:
        x, y, z = _cam_in(t)
        cam = Camera(x, y, z)
    elif t >= T_S03:
        c = _s03().camera(t - 15.0)
        cam = Camera(c.x, c.y, c.zoom)
    else:
        keys = _cam_keys_for(_key(rg.b))
        x, y, lz = keys[-1][1]
        for (t0, p0, v0), (t1, p1, v1) in zip(keys, keys[1:]):
            if t <= t1:
                x, y, lz = K.hermite(p0, v0, p1, v1, t0, t1, t)
                break
        cam = Camera(x, y, math.exp(lz))
    # the CLANK: a small jolt
    it = rg.b["it"]
    if it - 0.02 < t < it + 0.5:
        u = max(t - it, 0.0)
        j = 3.0 * math.exp(-u / 0.09) * math.sin(2 * math.pi * 11.0 * u)
        cam = Camera(cam.x + 0.4 * j / cam.zoom, cam.y + j / cam.zoom, cam.zoom)
    return cam


# ============================================================================= the hose
_KX, _KY = SB.HOSE["coil"]
N_HOSE = 72


def _coil_amount(t, rg):
    return lerp(0.92, 0.55, ss(rg.t_up1, rg.t_sw1, t))


def _deck_run_local():
    """The boat's own deck run, coil -> stern exit (local)."""
    ex, ey = SB.HOSE["exit"]
    return [(_KX + 55.0, -166.0), (600.0, -166.0), (840.0, -172.0), (ex, ey)]


def _hose_in(t):
    """IN: the hose of the present (s01's rope) up through the water to the stern exit."""
    pts = _s01().HOSE.points(min(10.0 + t, 11.45))
    E = BOAT.hose_exit(t)
    keep = sorted([p for p in pts if p[1] > 760.0], key=lambda p: p[1])      # shallow -> deep
    if len(keep) < 3:
        return []
    J, J2 = keep[0], keep[2]
    d = (J[0] - J2[0], J[1] - J2[1])
    L = math.hypot(*d) or 1.0
    d = (d[0] / L, d[1] / L)
    top = K.bezier(E, (E[0] + 12.0, E[1] + 210.0), (J[0] + d[0] * 380.0, J[1] + d[1] * 380.0), J, n=28)
    return top + keep[1:]


def _trail_pts(c_in, pel_x):
    """The free hose (rest frame) from the coil to the inlet c_in: lying on the deck behind
    the diver (pelvis at pel_x, facing +x) and hanging from the bonnet's inlet down his back."""
    kx = _KX + BOAT.x
    w = ss(kx - 40.0, kx + 120.0, pel_x)          # 0: he is forward of the coil (seated), 1: aft of it
    q = lerp(c_in[0] + 40.0, max(min(pel_x, c_in[0]) - 85.0, kx + 30.0), w)
    n = max(2, int(abs(q - kx) / 40.0))
    lie = []
    for i in range(n + 1):
        x = lerp(kx + (14.0 if q > kx else -14.0), q, i / n)
        lie.append((x, deck_rest(x) - 5.0))
    lie[0] = (lie[0][0], deck_rest(kx) - 12.0)
    qd = lie[-1]
    h = max(qd[1] - c_in[1], 10.0)
    run = clamp((q - kx) / 40.0, -1.0, 1.0)               # the way it runs along the deck
    s = clamp((c_in[0] - qd[0]) / 30.0, -1.0, 1.0)
    up = K.bezier(qd, (qd[0] + run * min(0.25 * h, 60.0), qd[1]), (c_in[0] - s * 40.0, c_in[1] + 0.5 * h), c_in,
                  n=20)
    return lie + up[1:]


def _hose_world(t, rg, inlet, pel_x):
    """The free hose (world) from the coil to the helmet's inlet: trailing over the deck behind
    him while he is on deck; through the swing it settles onto the boat's own deck run to the
    stern exit and loops up to him, becoming s03's simulated hose."""
    pose = BOAT.pose(t)
    w_l = ss(rg.t_sw0, rg.t_sw1 - 0.05, t)
    trail = None
    if w_l < 1.0:
        d = boat_shift(inlet, t)
        trail = K.resample([on_boat(p, t) for p in _trail_pts((inlet[0] - d[0], inlet[1] - d[1]), pel_x - d[0])],
                           N_HOSE)
    if w_l <= 0.0:
        return trail
    run = [BOAT.to_world(p, t, pose) for p in _deck_run_local()]
    E = run[-1]
    loop = K.bezier(E, (E[0] + 30.0, E[1] + 190.0), (inlet[0] + 40.0, inlet[1] + 260.0), inlet, n=40)
    w_s = ss(rg.t_sw1 - 0.3, rg.t_sw1, t)
    if w_s > 0.0:
        a = K.resample(loop, 52)
        bb = K.resample(_s03().HOSE.points(t - 15.0), 52)
        loop = [(lerp(p[0], q[0], w_s), lerp(p[1], q[1], w_s)) for p, q in zip(a, bb)]
    lad = K.resample(run + loop[1:], N_HOSE)
    if trail is None:
        return lad
    return [(lerp(p[0], q[0], w_l), lerp(p[1], q[1], w_l)) for p, q in zip(trail, lad)]


# ============================================================================= the diver
def _diver_state(t, rg):
    """(pose (world), look, bonnet (c, ang, flip) world or None, on the ladder side of the rail)."""
    it = rg.b["it"]
    if t >= rg.t_sw0:
        return _swing_state(t, rg)
    p = rg.diver.pose(t)
    d = boat_shift((p.x, p.y), t)
    _shift_pose(p, d)
    look = LOOK_BARE
    bon = None
    if t < it:
        c, ang, fl = rg.bonnet_rest(t)
        bon = ((c[0] + d[0], c[1] + d[1]), ang, fl)
    else:
        look = _helm_look(t, rg)
    # eyes: shut as the bonnet comes over, open behind the glass once it is home and dark
    op = 1.0 - ss(rg.t_lift1 - 0.25, rg.t_lift1, t) + ss(it + 0.16, it + 0.30, t)
    p.eyes = dict(p.eyes, open=clamp(op) * p.eyes.get("open", 1.0), glow=1.0, look=0.0)
    return p, look, bon, False


def _helm_look(t, rg):
    it = rg.b["it"]
    if t >= it + 0.2:
        return LOOK_HELM
    lk = cast.diver()
    lk.opts = dict(lk.opts, glass=S.mix(GLASS_LIT, GLASS, ss(it + 0.03, it + 0.17, t)))
    return lk


def _swing_state(t, rg):
    """Round the davit post onto the ladder (world): a hand on the post, turning toward us,
    ducking, the boots finding the rungs; s03's own diver from t_sw1."""
    s03 = _s03()
    t0, t1 = rg.t_sw0, rg.t_sw1
    q = s03.DIVER.pose(t - 15.0)
    if t >= t1:
        return q, LOOK_HELM, None, True
    u = clamp((t - t0) / (t1 - t0))
    e = ease("inout", u)
    p0 = rg.diver.pose(t)                      # standing on deck, as he was
    _shift_pose(p0, boat_shift((p0.x, p0.y), t))
    sk0 = F.solve(p0, cast.DIVER)
    qe = s03.DIVER.pose(t1 - 15.0)              # where he lands
    p = F.Pose(lerp(p0.x, qe.x, e), lerp(p0.y, qe.y, e) + 40.0 * math.sin(math.pi * e), lerp(0.0, 180.0, e))
    # boots: R first to the lower rung, then L to the top rung (arcs over the rail's end)
    r1, r2 = s03._rung(t, 0), s03._rung(t, 1)
    fR0 = p0.legs["R"]["ik"] if "ik" in p0.legs["R"] else sk0.j["ankle_R"]
    fL0 = p0.legs["L"]["ik"] if "ik" in p0.legs["L"] else sk0.j["ankle_L"]
    fR1 = (r2[0] + 16.0, r2[1] - 19.0)
    fL1 = (r1[0] + 17.0, r1[1] - 19.0)
    uR = ease("inout", clamp((u - 0.05) / 0.55))
    uL = ease("inout", clamp((u - 0.35) / 0.55))
    fR = (lerp(fR0[0], fR1[0], uR), lerp(fR0[1], fR1[1], uR) - 90.0 * math.sin(math.pi * uR))
    fL = (lerp(fL0[0], fL1[0], uL), lerp(fL0[1], fL1[1], uL) - 70.0 * math.sin(math.pi * uL))
    p.legs["R"] = {"ik": fR, "pitch": 0.0, "toe": 0.0, "abd": 3.0}
    p.legs["L"] = {"ik": fL, "pitch": 0.0, "toe": 0.0, "abd": 3.0}
    duck = math.sin(math.pi * clamp((u - 0.05) / 0.8))
    p.pitch = 24.0 * duck - 5.0 * e
    p.spine = [1.0, 1.0 + 5.0 * duck, 2.0]
    p.head = 10.0 * duck + 2.0
    # hands: R takes the davit post and swings him round it, then both find the rail
    post = BOAT.to_world((SB.DAVIT["base"][0] - 24.0, -560.0), t)
    gL, gR = s03._rail_grip(t, -22.0), s03._rail_grip(t, 8.0)
    hR0, hL0 = sk0.j["hand_R"], sk0.j["hand_L"]
    a = ease("inout", clamp(u / 0.3))
    b_ = ease("inout", clamp((u - 0.55) / 0.35))
    tR = (lerp(lerp(hR0[0], post[0], a), gR[0], b_), lerp(lerp(hR0[1], post[1], a), gR[1], b_))
    c_ = ease("inout", clamp((u - 0.2) / 0.55))
    tL = (lerp(hL0[0], gL[0], c_), lerp(hL0[1], gL[1], c_))
    for side, tgt in (("R", tR), ("L", tL)):
        p.arms[side] = dict(sh=20.0, abd=10.0, elbow=30.0, wrist=0.0, grip=0.95)
        p = arm_ik(p, side, tgt, cast.DIVER, False)
    p.eyes = dict(open=1.0, glow=1.0, look=0.0)
    w0 = 1.0 - ss(0.0, 0.22, u)
    if w0 > 0.0:
        p = F.blend(p, p0, w0, cast.DIVER)
    w1 = ss(0.78, 1.0, u)
    if w1 > 0.0:
        p = F.blend(p, q, w1, cast.DIVER)
    return p, LOOK_HELM, None, u > 0.45


# ============================================================================= render
def render(f, t, T):
    rg = rig(T)
    b = rg.b
    cam = camera_at(t, rg)
    f.set_camera(cam)
    hz = S.horizon_y(f)
    a_in = 1.0 - ss(0.9, 1.9, t)                  # the present (hose, bubbles) dissolves
    bright = lerp(B_IN, BRIGHT, ss(0.6, 2.4, t))
    end = t >= rg.t_sw1
    # --- sky, far sea, water
    if hz > -10:
        S.night_sky(f, t, moon=MOON, moon_r=MOON_R, dusk=DUSK, veil=VEIL)
        S.far_sea(f, t, moon_x=MOON[0], dusk=DUSK)
    S.underwater(f, t, bright=bright)
    S.surface_glow(f, t, bright=bright)
    _in_light(f, t, a_in)
    _rays(f, t)
    # --- the boat (the emissive buffer cleared behind her), her lights
    coil = _coil_amount(t, rg)
    K.emit_mask(f, [lambda G: _boat_path(G, t)])
    with f.layer() as L:
        BOAT.draw(L, t, pump_angle=12.0, winch_angle=0.0, hose_coil=coil if end else 1.0, hose=end, rail=False)
        if not end:
            _deck_hose_local(L, t, coil)
    BOAT.draw_lights(f, t, lantern=1.0, window=0.0, masthead=1.0)
    # --- the people (masks first: their silhouettes hide the moon and the lantern glow)
    dp, dlook, bon, ladder = _diver_state(t, rg)
    dsk = F.solve(dp, cast.DIVER)
    clook = _client_look(t, rg)
    cp = rg.client.pose(t)
    _shift_pose(cp, boat_shift((cp.x, cp.y), t))
    csk = F.solve(cp, cast.CLIENT)
    kw = K.knife_on_belt(csk)
    kp = K.knife_points(kw)
    flap = K.coat_flap(csk, clook, _flap_open(t, rg), t, cover=kp["pommel"])
    K.figure_mask(f, csk, clook)
    K.figure_mask(f, dsk, dlook)
    K.emit_mask(f, [lambda G: draw.poly(G, flap), lambda G: S.draw_knife(G, **dict(kw, color=(0.0, 0.0, 0.0)))])
    inlet = rg.bonnet.inlet(*bon) if bon is not None else costume.helmet_inlet(dsk)
    hose = None if end else _hose_world(t, rg, inlet, dp.x)
    with f.layer() as L:
        if hose and not ladder:
            LIB.draw_hose(L, hose, 9.5)
        if not ladder:
            _draw_diver(f, L, t, rg, dsk, dlook, bon)
    if bon is not None:                          # the bonnet hides his eyes and the moon behind it
        with f.emit() as G:
            rg.bonnet.draw(G, bon[0], bon[1], bon[2], path_only=True)
    with f.layer() as L:
        _draw_client(f, L, csk, clook, kw, flap)
        _draw_envelope(L, t, rg, csk, dsk, front=True)
        _draw_rail(L, t)
        if end:
            LIB.draw_hose(L, _s03().HOSE.points(t - 15.0), LIB.HOSE_W)
        elif hose and ladder:
            LIB.draw_hose(L, hose, 9.5)
        if ladder:
            _draw_diver(f, L, t, rg, dsk, dlook, bon)
    S.water_front(f, t, alpha=0.10, bright=bright)
    # --- the present underwater: hose and bubbles (IN)
    if a_in > 0.0:
        _in_hose_bubbles(f, t, a_in)
    # --- smoke, the glint
    _smoke(f, t, rg, csk)
    S.knife_glint(f, kp["glint"], t, b["using"], dur=0.36, size=0.8)
    f.post["vignette"] = lerp(f.post["vignette"], 0.42, ss(12.2, 13.4, t) * (1.0 - ss(14.1, 15.0, t)))


# ----------------------------------------------------------------------------- drawing
def _boat_path(G, t):
    BOAT.draw(G, t, color=(0.0, 0.0, 0.0), pump_angle=12.0, hose=False, rail=True, lantern=True)


def _draw_rail(L, t):
    BOAT._begin(L, BOAT.pose(t))
    L.new_path()
    S.put(L, S.shape("boat_rail", SB._railing))
    S.paint(L, INK)
    L.restore()


def _deck_hose_local(L, t, coil):
    """Pump -> coil (as the boat draws it) and the coil itself (local frame)."""
    BOAT._begin(L, BOAT.pose(t))
    ox_, oy_ = SB.PUMP["outlet"]
    S.line(L, [(ox_ + 18, oy_), (ox_ + 40, oy_ + 18), (_KX - 52, -168)], 9.0, RED)
    L.new_path()
    S.put(L, S.shape("coil", SB._hose_coil), _KX, _KY, 0.0, 1.0, sy=0.35 + 0.65 * clamp(coil))
    S.paint(L, RED)
    L.restore()


def _draw_diver(f, L, t, rg, sk, look, bon):
    _draw_envelope(L, t, rg, None, sk, front=False)      # being tucked away: behind his chest
    F.draw_figure(f, sk, look, L)
    if look is LOOK_BARE:
        for fn, col, eo in K.corselet(sk, LOOK_HELM):
            L.new_path()
            fn(L)
            L.set_source_rgb(*INK)
            L.fill()
    if bon is not None:
        rg.bonnet.draw(L, bon[0], bon[1], bon[2], color=INK, glass=GLASS_LIT)


def _draw_client(f, L, sk, look, kw, flap):
    facing_right = math.cos(sk.pose.yaw * D2R) >= 0
    if not facing_right:
        S.draw_knife(L, **kw)
    F.draw_figure(f, sk, look, L)
    if facing_right:
        S.draw_knife(L, **kw)
    L.new_path()
    draw.poly(L, flap)
    L.set_source_rgb(*INK)
    L.fill()


def _draw_envelope(L, t, rg, csk, dsk, front=True):
    cash = rg.b["cash"]
    if t < rg.t_env1 - 0.06 or t > rg.t_tuck1 + 0.05:
        return
    s = 0.55
    if t < cash:
        if not front or csk is None:
            return
        h = csk.j["fingers_L"]
        k = ss(rg.t_env1 - 0.06, rg.t_env1 + 0.1, t)
        S.draw_envelope(L, h[0] - 30.0, h[1] + 2.0, angle=180.0 - 25.0 * (1 - k), s=s * lerp(0.7, 1.0, k), pale=0.35)
        return
    if dsk is None:
        return
    if front == (t > rg.t_tuck0):
        return
    h = dsk.j["fingers_R"]
    ang = lerp(180.0, 110.0, ss(cash + 0.2, cash + 0.7, t))
    ang = lerp(ang, 95.0, ss(rg.t_tuck0, rg.t_tuck1, t))
    sc = s * (1.0 - 0.35 * ss(rg.t_tuck0, rg.t_tuck1, t))
    a = math.radians(ang)
    S.draw_envelope(L, h[0] - 32.0 * math.cos(a), h[1] - 32.0 * math.sin(a), angle=ang, s=sc, pale=0.35)


def _client_look(t, rg):
    b = rg.b
    e = 1.0 + 0.6 * ss(b["name"] - 0.25, b["name"] + 0.02, t) * (1.0 - ss(b["name"] + 0.25, b["name"] + 1.1, t))
    e += 0.08 * math.sin(2.7 * t) + 0.05 * noise1(t * 1.3, 9)
    return cast.client(ember=e, coat_flow=_wind(t, rg))


def _wind(t, rg):
    b = rg.b
    g = ss(b["l5"] + 1.6, b["plan"] - 0.12, t) * (1.0 - 0.35 * ss(b["it"] + 0.2, 15.5, t))
    return 0.95 * g + 0.10 * g * noise1(t * 2.1, 17)


def _flap_open(t, rg):
    b = rg.b
    return ss(b["l5"] + 2.0, b["plan"] - 0.08, t) * (1.0 - 0.25 * ss(b["it"] + 0.3, 15.5, t))


def _smoke(f, t, rg, csk):
    b = rg.b
    mouth = F.head_point(csk, 0.86, 0.22, front_x=0.16, front_y=0.20)
    w = _wind(t, rg)
    K.smoke(f, t, mouth, b["name"] + 0.42, 0.7, n=7, wind=(-30.0 - 60.0 * w, -16.0), seed=5, alpha=0.13)
    K.smoke(f, t, mouth, 1.0, 0.25, n=3, wind=(30.0, -12.0), seed=8, alpha=0.08)
    K.smoke(f, t, mouth, b["l5"] + 0.3, 0.3, n=3, wind=(-40.0, -10.0), seed=9, alpha=0.08)


# ----------------------------------------------------------------------------- light under water
def _in_light(f, t, a_in):
    """s01's light (the bright band toward the surface, its rays) continued above its frame."""
    if a_in <= 0.0:
        return
    s = 10.0 + t
    rk = ss(8.4, 10.6, s)
    wl = S.waterline_screen_y(f)
    if wl < H and t < 1.9:
        a_seam = 0.297 * rk
        y0 = max(wl, 0.0)
        a_top = min(0.45, a_seam + 0.30 * rk / 1110.0 * (H - y0))
        LIB.screen_band(f, y0, H, PAL.surface, a_top * a_in, a_seam * a_in)
    atmos.underwater_rays(f, surface_y=0.0, t=s, spacing=150.0, angle=95.0, fan=10.0, length=4200.0,
                          intensity=0.55 * rk * a_in, density=0.6, seed=4, blur=16)


def _rays(f, t):
    """s03's dusk rays (on s03's clock), taking over from s01's as we leave the water."""
    k = ss(0.9, 2.2, t)
    if k <= 0.0:
        return
    atmos.underwater_rays(f, surface_y=0.0, t=t - 15.0, spacing=170.0, angle=97.0, fan=10.0, length=3000.0,
                          intensity=0.42 * k, density=0.62, seed=8, blur=16)


def _in_hose_bubbles(f, t, a_in):
    s01 = _s01()
    s = 10.0 + t
    pts = _hose_in(t)
    if pts:
        with f.layer() as L:
            LIB.draw_hose(L, pts, LIB.HOSE_W, alpha=a_in)
    atmos.bubbles(f, s01._VALVE, rate=5.5, t=s, seed=11, rise=(260.0, 430.0), size=(1.6, 6.5), spread=8.0,
                  current=14.0, height=3400.0, alpha=0.95 * a_in, surface=0.0)
    for i, te in enumerate(s01.EXHALES):
        atmos.exhale(f, s01._VALVE, te, n=26, t=s, seed=50 + i, size=(1.8, 12.0), rise=(280.0, 460.0),
                     spread=44.0, current=14.0, height=3400.0, alpha=0.95 * a_in, surface=0.0)


# ============================================================================= extras
def motion_blur(t, T):
    """Sub-frames by how fast the frame moves (px per frame at the corners)."""
    rg = rig(T)
    c0, c1 = camera_at(t - 1.0 / 48.0, rg), camera_at(t + 1.0 / 48.0, rg)
    v = 0.0
    for sx in (0.0, W):
        for sy in (0.0, H):
            wx, wy = c0.x + (sx - W / 2) / c0.zoom, c0.y + (sy - H / 2) / c0.zoom
            v = max(v, math.hypot((wx - c1.x) * c1.zoom + W / 2 - sx, (wy - c1.y) * c1.zoom + H / 2 - sy))
    if rg.t_sw0 < t < rg.t_sw1:              # the swing itself is fast
        v = max(v, 30.0)
    return 1 if v < 10.0 else 2 if v < 24.0 else 3 if v < 45.0 else 4


def cues(T):
    b = _beats(T)
    rg = rig(T)
    it = b["it"]
    return [
        Cue(-0.75, "rising whoosh continues: bubbles rolling up toward the light", gain_db=-10, dur=1.3),
        Cue(0.25, "bubbles burst at the surface (soft pops); the muffled world opens to air", gain_db=-10, dur=1.2),
        Cue(0.55, "surface ambience at dusk: swell slapping the hull, rope and davit creak, light wind, "
                  "distant gulls", gain_db=-14, dur=14.0),
        Cue(rg.t_env0, "paper rustle: an envelope drawn from inside a coat", gain_db=-14, pan=0.2),
        Cue(b["paid"], "the envelope held out (a soft thick-paper tap)", gain_db=-16, pan=0.05),
        Cue(b["cash"], "the envelope taken: thick paper in a canvas glove", gain_db=-11, pan=-0.15),
        Cue(rg.t_tuck0, "envelope tucked into the canvas suit (rustle)", gain_db=-15, pan=-0.25),
        Cue(rg.t_turn0, "the client turns away: heavy coat rustle", gain_db=-16, pan=0.1),
        Cue(rg.t_up0, "the diver stands: canvas creak, brass breastplate knock", gain_db=-13, pan=-0.3),
        Cue(b["name"], "cigar draw: the ember crackles", gain_db=-12, pan=0.1),
        Cue(b["name"] + 0.45, "slow exhale of smoke", gain_db=-18, pan=0.1),
        Cue(rg.t_up1, "lead-boot footsteps on the deck planks, slow and heavy", gain_db=-12, pan=-0.2,
            dur=rg.t_arrive - rg.t_up1),
        Cue(rg.t_lift0, "the helmet bonnet lifted overhead and lowered on: brass creak, hose scuff",
            gain_db=-14, pan=0.25, dur=rg.t_low1 - rg.t_lift0),
        Cue(b["l5"] + 1.6, "wind gust off the sea: coat flapping", gain_db=-12, dur=2.6),
        Cue(b["using"], "knife glint: a bright high shimmer", gain_db=-14, pan=0.05),
        Cue(rg.t_reach0 + 0.3, "hands on the helmet: brass scraping as it turns on the breastplate", gain_db=-13,
            pan=0.25, dur=it - rg.t_reach0 - 0.3),
        Cue(it, "HELMET CLANK (key sync hit): the bonnet locks home", gain_db=-2, pan=0.25),
        Cue(it + 0.12, "inside the helmet: the first breath, free-flow air hiss starts", gain_db=-12, pan=0.3,
            dur=1.5),
        Cue(rg.t_sw0, "he swings onto the ladder: a hand slaps the davit post, boots on the rungs, gear creak",
            gain_db=-12, pan=0.45, dur=rg.t_sw1 - rg.t_sw0 + 0.3),
    ]
