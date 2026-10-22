"""s09 · NINETY SECONDS (14.0 s). Apartment 9. She builds the trap: the lamp behind the
sheet, the sheet pulled straight, the woman doll clamped in front of the bulb so that a
life-size woman's shadow stands on the sheet. Then she hides by the door. He is coming up.

One shot in the room (Room3D eye; the 2-D camera pans and pushes).

IN        (dip from black) the show lamp burns at its front place (she switched it on in s07);
          the sheet is bunched at the left end of its wire; she stands frozen at window 9,
          three-quarter back; the rig's dolls throw their shadows on the window wall.
0.62      "I" - she whips round.  0.9-2.0 to the lamp.  2.25 grabs it: the light moves.
2.4-3.3   carries it to the rig, yanks the woman doll off its rod (3.10).
3.3-5.9   carries the lamp in front of the table (the dolls' shadows sweep the wall), round
          the table's left end, behind the sheet line.  [light] 5.90 sets it down there.
6.2-7.7   takes the sheet's free edge and walks it across the room behind the wire
          ([sheet] 6.93): the sheet slides over the lamp and lights up from behind.
7.7-9.0   walks back behind the sheet toward the bulb: her giant shadow crosses the sheet;
          her shadow-hand lifts the doll in front of the bulb.  [believe] 9.04 clamps it;
          she steps back behind the lamp and her shadow swells away: only a life-size
          woman's shadow stands on the sheet (the show's woman doll, facing right).
9.4-11.1  out round the sheet's left end, across to the door's hinge side.
11.1-14   "So I gave him a show." flat against the wall, in the dark, eyes wide.
12.25     outside, the hall light clicks on: a line of light under the door.  Footsteps.
13.0-13.4 two feet slide into the line and stop.  13.5- the lever handle starts to turn.
OUT       (hard cut to s10) the lever turning (0.33 of its travel at 14.0).
"""
import math
from functools import lru_cache

from engine import draw
from engine.core import clamp, ease, fbm1, lerp, noise1
from engine.frame import Camera
from engine.palette import PAPER, SHADOWPLAY as PAL
from engine.timing import Cue
from films.shadowplay import cast, sets
from films.shadowplay.scenes import _lib_s08_s10 as L

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot
mix = L.sets_mix

R9 = L.Room9()
APT = R9.apt
ROOM = R9.r

LAMP0 = APT.LAMP_FRONT                    # (0.45, 2.15) where s07 left it, lit
LAMP_SET = (-0.55, 3.92)                  # behind the sheet: the decoy's bulb
DECOY = (-0.55, 1.62, 3.82)               # the woman doll's pelvis (rod top), 10 cm before the bulb
ROD_GRIP = 0.30                           # she holds the rod this far below the doll
W0 = (0.02, 3.98)                         # at window 9 (between the rig's two dolls, seen from here)
WALL = (-1.76, 2.52)                      # flat against the wall on the door's hinge side
DOOR_FEET = (110.0, 215.0)                # door px from the hinge where his feet stop
LEVER_OUT = 0.45                          # the lever's turn (0..1 of 40 deg) at the cut to s10


def _times(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:                 # noqa: BLE001
            return d
    return (at("light", 5.904), at("sheet", 6.926), at("believe", 9.039), at("show", 11.483))


TL0 = (5.904, 6.926, 9.039, 11.483)


# ----------------------------------------------------------------------------- her
class Her:
    def __init__(self, tl):
        LIGHT, SHEET, BELIEVE, SHOW_ = tl
        self.tl = tl
        self.t_lamp_grab = 2.25
        self.t_doll_grab = 3.10
        self.t_set = LIGHT
        self.t_edge = SHEET - 0.52           # her hand on the sheet's free edge
        self.t_pull = (SHEET - 0.23, SHEET + 0.78)
        self.t_clamp = BELIEVE
        w = L.Walker(cast.HER, ROOM, W0[0], W0[1], -75.0, seed=91, t0=-2.0)
        a = w.a
        w.stand(0.62, idle=0.12)
        w.turn(48.0, dur=0.28, via=0.0)                                  # whips round
        w.go(0.74, 3.30, 0.52, gait="brisk")                             # past the table's right end
        w.go(0.80, 2.44, 0.58, gait="brisk")                             # to the lamp
        w.turn(140.0, dur=0.22, via=90.0)                                # faces it
        w.stand(2.42)
        w.go(0.32, 2.30, 0.50, gait="brisk")                             # lamp in hand, to the rig
        w.turn(-90.0, dur=0.22, via=90.0)                                # faces the table
        w.stand(3.30)
        w.turn(178.0, dur=0.22, via=-90.0)
        w.go(-0.78, 2.34, 0.95, gait="brisk")                            # in front of the table
        w.go(-1.00, 3.22, 0.78, gait="brisk", yaw=-104.0)               # round its left end, into depth
        w.go(-0.92, 3.80, 0.50, gait="brisk", yaw=-82.0)
        w.stand(LIGHT + 0.16)                                            # sets the lamp
        w.go(-0.62, 3.70, 0.34, gait="walk")                             # to the bunched sheet's edge
        w.turn(0.0, dur=0.2, via=-90.0)
        w.stand(self.t_pull[0])
        w.go(1.22, 3.72, self.t_pull[1] - self.t_pull[0], gait="brisk", yaw=0.0)   # walks the sheet across
        w.stand(self.t_pull[1] + 0.12)
        w.turn(180.0, dur=0.26, via=-90.0)
        w.go(-0.22, 3.76, 0.72, gait="walk", yaw=180.0)                 # behind the sheet, toward the bulb
        w.stand(BELIEVE + 0.04)
        w.go(-0.16, 4.06, 0.36, gait="walk", yaw=180.0)                 # steps back behind the lamp
        w.go(-1.12, 4.05, 0.60, gait="brisk", yaw=180.0)                # behind the lamp, out past the sheet
        w.go(-1.30, 3.30, 0.50, gait="brisk")
        w.go(WALL[0], WALL[1], 0.60, gait="brisk")
        w.turn(0.0, dur=0.32, via=90.0)                                  # back to the wall
        self.t_wall = w.cursor
        w.stand(30.0, idle=0.35)
        self.w = w
        # ---- arms, head
        # the lamp: right hand on the pole
        a.reach("R", self.t_lamp_grab - 0.05, self.t_set - 0.02, self._lamp_hand, fade=0.22, grip=0.95)
        # the doll: left hand to the rig's rod, then carried, then to the clamp
        a.reach("L", self.t_doll_grab - 0.18, self.t_doll_grab + 0.12, self._rig_rod, fade=0.2, grip=0.95)
        a.arm("L", self.t_doll_grab + 0.30, BELIEVE - 0.80, fade=0.25, sh=12.0, abd=10.0, elbow=84.0, grip=0.95)
        a.reach("L", BELIEVE - 0.42, BELIEVE + 0.02, self._clamp_hand, fade=0.28, grip=0.95)
        # the sheet edge: right hand, trailing
        a.reach("R", self.t_edge, self.t_pull[1] + 0.05, self._edge_hand, fade=0.18, grip=0.9)
        # flat against the wall: palms back on it, chin up, head to the door
        tw = self.t_wall
        a.arm("L", tw - 0.1, 30.0, fade=0.3, sh=-22.0, abd=16.0, elbow=18.0, grip=0.1)
        a.arm("R", tw - 0.1, 30.0, fade=0.3, sh=-24.0, abd=14.0, elbow=16.0, grip=0.1)
        a.pose_keys(tw - 0.1, 30.0, fade=0.3, pitch=-3.0, head=-7.0)
        a.key("head_yaw", [(tw - 0.05, 0.0), (tw + 0.3, 62.0), (12.2, 62.0), (12.45, 74.0), (30.0, 74.0)],
              fade=0.3)
        # breath: the chest heaves after the run, then held when the light comes on
        a.channel("pitch", lambda t: 1.4 * math.sin(t * 6.3) * clamp((12.3 - t) / 1.0), tw, 30.0, mode="add",
                  fade=0.4)
        # the frozen start: a held breath; she whips round on "I"
        a.key("head_yaw", [(-2.0, 0.0), (0.62, 0.0)], fade=0.2)
        a.eyes(-2.0, 30.0, fade=0.1, open=1.0)

    # ---- prop positions (room) -------------------------------------------------------
    def lamp(self, t):
        """Lamp dict at t (room)."""
        w = self.w
        g0 = self.t_lamp_grab
        if t <= g0:
            return dict(X=LAMP0[0], Z=LAMP0[1], lift=0.0, tilt=0.0)
        X, Z = w.ahead(t, 0.16, 0.30)
        if t >= self.t_set:
            return dict(X=LAMP_SET[0], Z=LAMP_SET[1], lift=0.0, tilt=0.0)
        u = L.k_(t, g0, 0.22, "inout")                                   # lifted off its spot
        v = L.k_(t, self.t_set - 0.40, 0.40, "inout")                    # set on its mark
        Xc, Zc = lerp(LAMP0[0], X, u), lerp(LAMP0[1], Z, u)
        Xc, Zc = lerp(Xc, LAMP_SET[0], v), lerp(Zc, LAMP_SET[1], v)
        carry = u * (1.0 - v)
        lift = 0.05 * carry
        # it sways as she walks with it
        _, _, xr = w.pos(t)
        tilt = carry * (3.5 * math.sin(xr / 38.0) + 2.0 * fbm1(t * 1.3, 77))
        return dict(X=Xc, Z=Zc, lift=lift, tilt=tilt)

    def _lamp_hand(self, t):
        lp = self.lamp(t)
        p = ROOM.P(lp["X"], 1.02 + lp["lift"], lp["Z"])
        return self.w.canon(t, p)

    def _rig_rod(self, t):
        X, Z, w_, d, h = APT.TABLE
        rx, ry = APT.RODS["woman"]
        up = 0.12 * L.k_(t, self.t_doll_grab, 0.16, "out")
        return self.w.canon(t, ROOM.P(X + rx, ry - ROD_GRIP + up, Z))

    def _clamp_hand(self, t):
        X, Y, Z = DECOY
        return self.w.canon(t, ROOM.P(X, Y - ROD_GRIP, Z))

    def edge_X(self, t):
        """Room X of the sheet's free edge (it follows her trailing hand)."""
        x_b = APT.SHEET[0] + R9.BUNCH
        if t <= self.t_pull[0]:
            return x_b
        if t >= self.t_pull[1]:
            return APT.SHEET[2]
        X, Z, _ = self.w.pos(t)
        return clamp(X - 0.27, x_b, APT.SHEET[2])

    def cover(self, t):
        x_b = APT.SHEET[0] + R9.BUNCH
        return clamp((self.edge_X(t) - x_b) / (APT.SHEET[2] - x_b))

    def _edge_hand(self, t):
        xe = self.edge_X(t) if t > self.t_pull[0] else APT.SHEET[0] + R9.BUNCH + 0.01
        return self.w.canon(t, ROOM.P(xe, 1.38, L.SHEET_Z + 0.02))

    def doll(self, t, sk=None, M=None):
        """('rig' | 'hand' | 'clamp', stage, depth Z) of the woman doll at t."""
        if t < self.t_doll_grab:
            return "rig", None, APT.TABLE[1]
        if t >= self.t_clamp:
            X, Y, Z = DECOY
            return "clamp", L.doll_stage(ROOM, X, Y, Z, "woman", mirror=False), Z
        X, Z, _ = self.w.pos(t)
        if sk is None:
            sk = self.w.a.skeleton(t)
            M = self.w.matrix(t)
        hx, hy = M.transform_point(*sk.j["hand_L"])
        k = ROOM.ppm(Z)
        if t < self.t_doll_grab + 0.2:
            # still coming off its rod: blend from the rig's depth to her hand's
            Zd = lerp(APT.TABLE[1], Z, L.k_(t, self.t_doll_grab, 0.2))
        else:
            # held at her side, then reached out to the clamp in front of the bulb
            c0 = self.t_clamp - 0.42
            Zd = lerp(Z, DECOY[2], L.k_(t, c0 - 0.28, 0.28 + 0.30))
        kk = ROOM.ppm(Zd)
        pel = (hx, hy - ROD_GRIP * k)
        S_ = 0.45 * kk
        # the last moment: she settles it into the clamp
        u = L.k_(t, self.t_clamp - 0.30, 0.30, "inout")
        if u > 0.0:
            X0, Y0, Z0 = DECOY
            pd = ROOM.P(X0, Y0, Z0)
            pel = (lerp(pel[0], pd[0], u), lerp(pel[1], pd[1], u))
            S_ = lerp(S_, 0.45 * ROOM.ppm(Z0), u)
            Zd = lerp(Zd, Z0, u)
        st = L.doll_stage_at(pel, S_, "woman", mirror=False)
        return "hand", st, Zd


@lru_cache(maxsize=2)
def _her(tl):
    return Her(tl)


# ----------------------------------------------------------------------------- light, colour
def _coat(lit):
    """Her look; the red coat burns only where light falls on the side we see."""
    return L.her_look(clamp(0.13 + 0.30 * lit, 0.0, 0.48))


def _doll_col(lv, lamp_z, z):
    """A paper doll's tone: pale paper lit from the front, ink when the lamp is behind it."""
    front = clamp((z - lamp_z - 0.05) / 0.4)
    return mix(INK, mix(PAPER, AMBER, 0.35), clamp(0.08 + 0.55 * lv * front))


# ----------------------------------------------------------------------------- the door
def _door_state(t):
    hall = sets.switch(t, t_on=12.25, kind="bulb", seed=19, level=1.0)
    feet = ()
    if t > 12.9:
        u = L.k_(t, 12.95, 0.42, "out")
        f1 = lerp(430.0, DOOR_FEET[0], u)
        f2 = lerp(540.0, DOOR_FEET[1], L.k_(t, 12.95, 0.36, "out"))
        feet = (f1, f2)
    lever = LEVER_OUT * L.k_(t, 13.50, 0.50, "in")
    return dict(open=0.0, hall=hall, feet=feet, lever=lever, lever_rim=0.85, lever_rim_col=mix(AMBER, HOT, 0.3),
                lit=0.6)


# ----------------------------------------------------------------------------- camera
CAM = [  # (t, x, y, zoom)
    (-0.5, 548.0, 945.0, 1.78),
    (0.62, 548.0, 945.0, 1.78),
    (1.80, 610.0, 1000.0, 1.58),
    (2.70, 585.0, 990.0, 1.60),
    (3.60, 540.0, 985.0, 1.60),
    (4.50, 455.0, 975.0, 1.62),
    (5.70, 440.0, 950.0, 1.66),
    (6.60, 470.0, 930.0, 1.70),
    (7.50, 545.0, 920.0, 1.56),
    (8.40, 520.0, 893.0, 1.90),
    (9.20, 500.0, 882.0, 2.10),
    (10.20, 345.0, 955.0, 1.55),
    (11.30, 250.0, 1000.0, 1.45),
    (12.30, 232.0, 1004.0, 1.50),
    (14.10, 70.0, 1010.0, 2.25),
]


def _spline(t, keys):
    """Monotone-ish cubic through (t, x, y, log z) keys (Catmull-Rom tangents, clamped)."""
    if t <= keys[0][0]:
        k = keys[0]
        return k[1], k[2], k[3]
    if t >= keys[-1][0]:
        k = keys[-1]
        return k[1], k[2], k[3]
    i = 0
    while keys[i + 1][0] < t:
        i += 1
    k0, k1 = keys[i], keys[i + 1]
    km = keys[max(i - 1, 0)]
    kp = keys[min(i + 2, len(keys) - 1)]
    h = k1[0] - k0[0]
    u = (t - k0[0]) / h
    out = []
    for j in (1, 2, 3):
        f = (lambda v: math.log(v)) if j == 3 else (lambda v: v)
        p0, p1 = f(k0[j]), f(k1[j])
        m0 = (p1 - f(km[j])) / max(k1[0] - km[0], 1e-6) * h if i > 0 else 0.0
        m1 = (f(kp[j]) - p0) / max(kp[0] - k0[0], 1e-6) * h if i + 2 < len(keys) else 0.0
        # no overshoot past either key
        lo, hi = min(p0, p1), max(p0, p1)
        u2, u3 = u * u, u * u * u
        v = (2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1
        if (m0 * (p1 - p0) < 0) or (m1 * (p1 - p0) < 0):
            v = lerp(p0, p1, ease("inout", u))
        v = clamp(v, lo - 0.02 * abs(hi - lo), hi + 0.02 * abs(hi - lo)) if hi > lo else v
        out.append(math.exp(v) if j == 3 else v)
    return out[0], out[1], out[2]


def camera(t):
    x, y, z = _spline(t, CAM)
    return Camera(x, y, z).shaken(t, amp=2.0, rot_amp=0.04, freq=0.35, seed=909)


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    tl = _times(T)
    her = _her(tl)
    w = her.w
    f.set_camera(camera(t))
    lp = her.lamp(t)
    lamp = dict(lp, on=1.0)
    cover = her.cover(t)
    X, Z, _ = w.pos(t)
    sk = w.a.skeleton(t)
    M = w.matrix(t)
    b3 = R9.bulb3d(lamp)
    bulb_w = ROOM.P(*b3)
    dist = math.sqrt((X - b3[0]) ** 2 + (Z - b3[2]) ** 2)
    near = clamp(1.3 - dist / 1.6)
    front_lit = clamp((Z - lamp["Z"]) / 0.6) * near           # the bulb between us and her
    look = _coat(front_lit)
    plain = L.plain_look(look)
    kind, dstage, dz = her.doll(t, sk, M)

    def her_shape(c):
        L.draw_skeleton(c, sk, plain, M, color=(0, 0, 0))

    def doll_shape(c):
        L.doll_casters(c, dstage, "woman", mirror=False)

    # what throws shadows where
    wall_casters = []
    casters = []
    if Z < ROOM.zb - 0.05:
        wall_casters.append((Z, her_shape))
        if kind == "hand":
            wall_casters.append((dz, doll_shape))
    wall_casters.append((APT.TABLE[1], lambda c: R9.table_casters(c, woman=(kind == "rig"))))
    if kind in ("clamp", "hand") and L.SHEET_Z < dz < lamp["Z"] - 0.012:
        casters.append((dz, doll_shape))
    if L.SHEET_Z < Z < lamp["Z"] - 0.012:
        casters.append((Z, her_shape))

    # people and things by depth
    def her_item(f_, t_):
        lvl = 1.0
        rims = []
        cen = M.transform_point(*sk.j["chest"])
        # the bulb rims her on its side; stronger when it is behind her
        back = clamp((lamp["Z"] - Z + 0.3) / 0.6)
        rims.append((mix(AMBER, HOT, 0.4), (0.22 + 0.5 * back) * near * lvl, L.rim_offset(cen, bulb_w, 4.0)))
        # the lit sheet behind her (camera side of it)
        if Z < L.SHEET_Z and lamp["Z"] > L.SHEET_Z and cover > 0.3:
            rims.append((AMBER, 0.20 * cover, (0.0, -2.5)))
        yaw = w.yaw_at(t_)
        facing = math.cos(math.radians(yaw - 90.0))
        eyes = 0.0
        if facing > 0.25:
            eyes = 0.55 * clamp((facing - 0.25) / 0.4)
        if t_ > her.t_wall - 0.2:
            eyes = lerp(eyes, 1.0, L.k_(t_, her.t_wall - 0.2, 0.5))
        L.draw_walker(f_, t_, w, look, rims=rims, eyes=eyes, eye_open=1.0, eye_size=0.72, sk=sk)
        if kind == "hand":
            with f_.layer() as Lc:
                L.doll_object(Lc, dstage, _doll_col(1.0, lamp["Z"], Z), "woman", mirror=False)

    items = [(Z, her_item)]
    if kind == "clamp":
        def decoy_item(f_, t_):
            with f_.layer() as Lc:
                # the rod clamped to the lamp's pole by a short bracket
                X0, Y0, Z0 = DECOY
                a = ROOM.P(X0, 1.02, Z0)
                b = ROOM.P(LAMP_SET[0], 1.02, LAMP_SET[1])
                draw.capsule(Lc, a, b, 2.0, 2.0)
                draw.fill(Lc, INK)
                L.doll_object(Lc, dstage, INK, "woman", mirror=False)
        items.append((dz, decoy_item))

    st = dict(
        lamp=lamp, cover=cover, rig=dict(woman=(kind == "rig"), doll_col=_doll_col(1.0, lamp["Z"], APT.TABLE[1])),
        wall_casters=wall_casters, casters=casters, items=items, door=_door_state(t), street=0.30,
    )
    R9.draw(f, t, st)
    # a breath of dust in the bulb's light
    f.post["bloom"] = 0.24


def cues(T):
    LIGHT, SHEET, BELIEVE, SHOW_ = _times(T)
    return [
        Cue(0.62, "her heels pivot on bare boards: she whips round", gain_db=-14, pan=0.0),
        Cue(0.95, "fast footsteps across the room, heels, hurried", gain_db=-12, pan=0.15),
        Cue(2.25, "the lamp stand lifted: tripod feet scrape, the bulb's filament rings", gain_db=-10, pan=0.25),
        Cue(3.10, "the paper doll yanked off its rod: a dry wooden clack and a paper flutter", gain_db=-11, pan=0.05),
        Cue(LIGHT, "the lamp stand set down hard behind the sheet: a thud", gain_db=-8, pan=-0.15),
        Cue(SHEET - 0.4, "curtain rings / clothes pins rasp along the wire as the sheet is pulled across", gain_db=-9,
            pan=0.2),
        Cue(BELIEVE, "a small spring clamp snaps shut on the doll's rod", gain_db=-10, pan=-0.2),
        Cue(9.45, "her quick footsteps round the sheet, then still", gain_db=-14, pan=-0.4),
        Cue(11.15, "her back meets the wall: a soft bump; her held breathing", gain_db=-18, pan=-0.6),
        Cue(12.0, "far below: slow heavy footsteps start up the stairs", gain_db=-16, pan=-0.7),
        Cue(12.25, "outside the door the hallway timer light clicks on", gain_db=-12, pan=-0.75),
        Cue(13.35, "the footsteps stop outside the door. Silence", gain_db=-14, pan=-0.75),
        Cue(13.52, "the lever handle begins to turn: a slow metal creak", gain_db=-9, pan=-0.75),
    ]
