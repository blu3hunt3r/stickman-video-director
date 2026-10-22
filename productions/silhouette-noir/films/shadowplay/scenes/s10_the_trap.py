"""s10 · THE TRAP (11.0 s, wordless). The handle turns, the door bursts open and hides her,
he charges the woman on the sheet and stabs her shadow; the sheet comes down on a paper doll.
She slips out, slams the door, turns the key. He hammers. The lamp crashes; dark; sirens.

A  0.00-1.22  CU in the room (the s09 angle, closer): the lever turns down to its stop
              (0.61, continuing s09's move), silence; 1.00 the door BURSTS open toward us and
              its leaf sweeps over her; he fills the bright doorway, the Golden-Arm knife up.
B  1.22-4.25  the room, wide: he runs at the woman's shadow on the sheet (the hall light
              lies across the floor through the doorway); stabs 2.02 and 2.42 punch slits of
              light through her; 2.86 a long rip; 3.02-3.62 the pins pop and the sheet slumps:
              only the show's paper woman on her rod, burning black in front of the bare bulb.
              He stands frozen.
C  4.25-5.08  wide on the door: she slips from behind the leaf, rounds it, takes the outer
              handle and runs out pulling the door after her: SLAM 5.00. He whips round
              (4.52) and charges; his weight hits the door (5.10).
D  5.08-5.55  insert, the hall side: the key turns, the bolt shoots home; his blows jolt it.
E  5.55-11.5  the hallway: she holds the door with her back while it jumps under his fists
              and the lever rattles; 6.62 the lamp CRASHES inside: the light under the door
              whirls, stutters, and the fuse takes everything (7.25). Dark: only her eyes.
              7.60 sirens: blue / red floods the hall window; 7.95-9.35 she slides down the
              door to the floor, the key in her fist, eyes wide. OUT: paper tear (10.5-11.5).
"""
import math
from functools import lru_cache

import cairo

from engine import draw, bass
from engine import figure as FG
from engine.core import clamp, ease, fbm1, hash01, lerp, noise1, siren
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import RED, PAPER, SHADOWPLAY as PAL
from engine.timing import Cue
from films.shadowplay import cast, sets
from films.shadowplay.sets_base import PX_M, BLUE, glow, glow_ellipse
from films.shadowplay.sets_props import lock_closeup, door_swing
from films.shadowplay.scenes import _lib_s08_s10 as L

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot
mix = L.sets_mix

R9 = L.Room9()
APT = R9.apt
ROOM = R9.r
DOOR = R9.door

LAMP_SET = (-0.55, 3.92)                  # s09: the lamp behind the sheet
DECOY = (-0.55, 1.62, 3.82)               # s09: the woman doll's pelvis, clamped before the bulb
WALL = (-1.76, 2.52)                      # s09: her place, flat on the wall at the door's hinge side
LEVER_IN = 0.45                           # the lever's turn at the cut from s09
DOOR_FEET = (110.0, 215.0)                # his feet under the door (door px from the hinge)

H_START = (-2.30, 1.73)                   # outside, at the handle (feet = DOOR_FEET)
H_DOOR = (-1.62, 1.80)                    # one long step: in the doorway
H_STAB = (-0.86, 3.24)                    # at the sheet, left of her shadow
H_HIT = (-1.50, 1.98)                     # at the slammed door

# ----------------------------------------------------------------------------- the beats
T_STOP = 0.61                             # the lever reaches its stop
T_BURST = 1.00
T_B = 1.22                                # cut: the room, wide
T_STAB = (2.02, 2.42)                     # the knife punches through the sheet
T_RIP = (2.82, 3.00)                      # the long downward rip
T_FALL = (3.02, 3.62)                     # the pins pop, the sheet slumps
T_TURN = 4.52                             # he hears her: whips round
T_C = 4.25                                # cut: her escape
T_GRAB = 4.60                             # her hand on the leaf's outer handle
T_SLAM = 5.00
T_D = 5.08                                # cut: the lock
T_KEY = (5.14, 5.34)                      # the key turns, the bolt shoots
T_E = 5.55                                # cut: the hallway
BLOWS = (5.12, 5.40, 5.64, 5.84, 6.02, 6.18, 6.33, 6.47)   # his fists on the door
T_CRASH = 6.62
T_DARK = 7.25
T_POLICE = 7.60
T_SLIDE = (7.95, 9.35)
T_END = 11.5


# ----------------------------------------------------------------------------- the door
def door_open(t):
    """Apartment 9's door (room side): closed; bursts open at T_BURST (bounces off its stop);
    pulled shut by her (T_GRAB .. T_SLAM)."""
    if t < T_BURST:
        return 0.0
    if t < T_BURST + 0.12:
        return 0.93 * ease("out", (t - T_BURST) / 0.12)
    if t < T_GRAB:
        dt = t - (T_BURST + 0.12)
        return 0.88 + 0.05 * math.cos(dt * 21.0) * math.exp(-dt * 7.0)
    return door_swing(t, [(T_GRAB, 0.88), (T_GRAB + 0.16, 0.66, "in"), (T_SLAM, 0.0, "slam")])


def lever(t):
    """The lever's turn (0..1 of 40 deg): continues s09's move to the stop, springs back."""
    if t < T_STOP:
        return LEVER_IN + (1.0 - LEVER_IN) * ease("out", t / T_STOP)
    if t < T_BURST:
        return 1.0
    return 1.0 - ease("out", (t - T_BURST) / 0.14)


def wall_x(Z):
    """World x of the left wall plane at depth Z (a figure billboard at Z left of it is outside)."""
    return ROOM.P(-ROOM.hw, 0.0, Z)[0]


def room_clip(Z):
    xw = wall_x(Z)

    def c(ctx):
        ctx.rectangle(xw, -1e5, 2e5, 2e5)
    return c


def hall_clip(Z):
    """The part of a figure that is outside the room, seen through the doorway."""
    xw = wall_x(Z)
    q = DOOR.opening_quad()

    def c(ctx):
        draw.poly(ctx, q)
        ctx.clip()
        ctx.new_path()
        ctx.rectangle(-1e5, -1e5, 1e5 + xw + 1.5, 2e5)
    return c


# ----------------------------------------------------------------------------- him
class Him:
    def __init__(self):
        w = L.Walker(cast.HIM, ROOM, H_START[0], H_START[1], 0.0, seed=101, t0=-1.0)
        a = w.a
        w.stand(0.97, idle=0.10)
        w.go(H_DOOR[0], H_DOOR[1], 0.30, gait="brisk", yaw=0.0)          # the shove and the step in
        self.t_run = w.cursor
        w.go(H_STAB[0], H_STAB[1], 0.62, gait="run")                       # at her
        self.t_arrive = w.cursor
        w.turn(-80.0, dur=0.14, via=-90.0)
        w.stand(T_TURN, idle=0.15)
        w.turn(160.0, dur=0.18, via=180.0)                                 # whips round
        w.go(H_HIT[0], H_HIT[1], T_SLAM + 0.10 - w.cursor, gait="run")
        w.stand(30.0, idle=0.3)
        self.w = w
        # the knife arm: one reach driven by wrist_world(t)
        a.reach("R", 0.90, T_TURN + 0.10, self._wrist_canon, fade=0.12, grip=1.0)
        # the left arm: out for balance while stabbing, then hanging
        a.arm("L", self.t_arrive - 0.1, T_FALL[1], fade=0.2, sh=24.0, abd=22.0, elbow=38.0, grip=0.8)
        a.pose_keys(self.t_arrive, T_RIP[1] + 0.1, fade=0.15, pitch=6.0)
        # frozen: the head drops a little to the doll
        a.key("head", [(T_FALL[1], 0.0), (T_FALL[1] + 0.4, 8.0), (T_TURN, 8.0)], fade=0.2)
        a.key("head_yaw", [(-1.0, 0.0), (T_TURN - 0.25, 0.0), (T_TURN - 0.05, 40.0)], fade=0.15)

    # wrist path in room 3-D (X, Y, Z), keyed
    def _keys(self):
        k = getattr(self, "_k", None)
        if k is not None:
            return k
        s1, s2 = T_STAB
        r0, r1 = T_RIP
        up = (-0.70, 2.30, 3.18)                     # raised above his right shoulder
        wind = (-0.75, 2.42, 3.10)
        k = [
            (s1 - 0.20, up), (s1 - 0.07, wind), (s1, (-0.58, 1.84, 3.42)), (s1 + 0.08, (-0.58, 1.82, 3.44)),
            (s2 - 0.20, up), (s2 - 0.07, wind), (s2, (-0.55, 2.02, 3.42)), (s2 + 0.08, (-0.55, 2.00, 3.44)),
            (r0 - 0.22, up), (r0 - 0.06, (-0.74, 2.46, 3.10)), (r0, (-0.60, 2.10, 3.42)),
            (r1, (-0.47, 1.22, 3.42)), (T_FALL[1], (-0.55, 1.10, 3.38)), (T_FALL[1] + 0.5, (-0.66, 1.00, 3.30)),
            (T_TURN, (-0.70, 0.92, 3.28)),
        ]
        self._k = k
        return k

    def wrist_world(self, t):
        """World (screen-plane) point the knife wrist goes to."""
        w = self.w
        if t < self.t_arrive - 0.05:
            # raising it in the doorway, high while he runs
            u = L.k_(t, 0.95, 0.22, "out")
            X, Z = w.ahead(t, 0.10 + 0.05 * u, 0.22)
            Y = lerp(1.05, 2.28, u)
            return ROOM.P(X, Y, Z)
        ks = self._keys()
        if t <= ks[0][0]:
            p = ks[0][1]
            # blend from the running pose into the first key
            X, Z = w.ahead(t, 0.12, 0.22)
            u = L.k_(t, self.t_arrive - 0.05, ks[0][0] - self.t_arrive + 0.05)
            return ROOM.P(lerp(X, p[0], u), lerp(2.28, p[1], u), lerp(Z, p[2], u))
        for i in range(1, len(ks)):
            if t <= ks[i][0]:
                t0, p0 = ks[i - 1]
                t1, p1 = ks[i]
                plunge = p1[2] > 3.4 and p0[2] < 3.3
                u = ease("in" if plunge else "inout", (t - t0) / (t1 - t0))
                return ROOM.P(*[lerp(a_, b_, u) for a_, b_ in zip(p0, p1)])
        return ROOM.P(*ks[-1][1])

    def _wrist_canon(self, t):
        return self.w.canon(t, self.wrist_world(t))

    def blade_rel(self, t):
        """Knife angle relative to the forearm: ice-pick down when raised, along the thrust
        when it goes in."""
        v = 150.0
        for ts in T_STAB + (T_RIP[0],):
            v = lerp(v, 70.0, L.env(t, ts - 0.06, ts, ts + 0.08, ts + 0.20))
        v = lerp(v, 60.0, L.env(t, T_RIP[0], T_RIP[1], T_FALL[1], T_FALL[1] + 0.3))
        return v

    def blade(self, t):
        """Visible blade length (the rest is through the sheet)."""
        b = 1.0
        for ts in T_STAB:
            b = min(b, 1.0 - 0.6 * L.env(t, ts - 0.02, ts, ts + 0.08, ts + 0.16, "out"))
        b = min(b, 1.0 - 0.6 * L.env(t, T_RIP[0] - 0.02, T_RIP[0], T_RIP[1], T_RIP[1] + 0.08, "out"))
        return b

    def mask(self, t):
        """His silhouette in the doorway's plane, blocking the hall light (Apartment9 door
        light mask: u 0 hinge .. 1 latch, v 0 floor .. 1 top)."""
        X, Z, _ = self.w.pos(t)
        k = clamp(1.0 - abs(X + 1.95) / 0.5)
        if k <= 0.02:
            return None
        z0, z1 = APT.DOOR_Z
        import numpy as np

        def sm(d, w_):
            return np.clip(1.0 - d / w_, 0.0, 1.0)

        def m(u, v):
            z = z1 - (z1 - z0) * u
            y = APT.DOOR_H * v
            dz = z - Z
            legs = sm(np.abs(np.abs(dz) - 0.08), 0.07) * (y < 0.92)
            body = sm(np.abs(dz), 0.19) * ((y >= 0.85) & (y < 1.58))
            head = sm(np.hypot(dz, (y - 1.70) * 0.9), 0.12)
            hat = sm(np.abs(dz), 0.17) * ((y > 1.78) & (y < 1.83)) + sm(np.abs(dz), 0.10) * ((y > 1.78) & (y < 1.93))
            ax = (y - 1.45) / 0.80                      # the raised right arm (his right = toward the latch)
            arm = sm(np.abs(dz - (-0.17 - 0.10 * ax)), 0.06) * ((y > 1.45) & (y < 2.27))
            return k * np.clip(legs + body + head + hat + arm, 0.0, 1.0)
        return m


@lru_cache(maxsize=1)
def _him():
    return Him()


# ----------------------------------------------------------------------------- her (the room)
class Her:
    def __init__(self):
        w = L.Walker(cast.HER, ROOM, WALL[0], WALL[1], 0.0, seed=91, t0=-2.0)
        a = w.a
        w.stand(T_C, idle=0.30)
        w.go(-0.86, 2.47, 0.30, gait="run", yaw=0.0)                 # out from behind the leaf
        self.t_edge = w.cursor
        w.go(-1.14, 1.95, 0.22, gait="run")                         # round its edge
        w.go(-2.28, 1.70, T_SLAM - 0.02 - w.cursor, gait="run")      # out, pulling the door after her
        w.stand(30.0, idle=0.4)
        self.w = w
        # flat on the wall (s09's end pose)
        tw = T_C + 0.02
        a.arm("L", -2.0, tw, fade=0.12, sh=-22.0, abd=16.0, elbow=18.0, grip=0.1)
        a.arm("R", -2.0, tw, fade=0.12, sh=-24.0, abd=14.0, elbow=16.0, grip=0.1)
        a.pose_keys(-2.0, tw, fade=0.12, pitch=-3.0, head=-7.0)
        a.key("head_yaw", [(-2.0, 74.0), (0.55, 74.0), (0.85, 64.0), (T_BURST + 0.02, 64.0), (T_BURST + 0.1, 80.0),
                           (T_C - 0.3, 80.0), (T_C, 30.0)], fade=0.12)
        # the burst: she flinches (hidden by the leaf a moment later)
        a.key("head", [(T_BURST, -7.0), (T_BURST + 0.06, 6.0), (T_BURST + 0.3, -2.0)], fade=0.08)
        a.eyes(-2.0, 30.0, fade=0.1, open=1.0)
        # the door: her right hand on the leaf's outer handle
        a.reach("R", T_GRAB, T_SLAM + 0.05, self._handle_canon, fade=0.10, grip=0.95)

    def handle_world(self, t):
        """The outer handle of the leaf (hall face) at the door's current opening."""
        op = door_open(t)
        ang = math.radians(100.0 * clamp(op))
        u0, v0 = DOOR.w - 34.0, DOOR.h * 0.46
        n = -26.0
        return DOOR.project(u0 * math.cos(ang) - n * math.sin(ang), u0 * math.sin(ang) + n * math.cos(ang), v0)

    def _handle_canon(self, t):
        return self.w.canon(t, self.handle_world(t))


@lru_cache(maxsize=1)
def _her():
    return Her()


# ----------------------------------------------------------------------------- the sheet
SLASHES = [
    # (t0, dur, (X0, Y0), (X1, Y1), width m, seed): cuts in the sheet (room X, Y on SHEET_Z)
    (T_STAB[0] - 0.01, 0.07, (-0.60, 1.86), (-0.44, 1.62), 0.040, 3),
    (T_STAB[1] - 0.01, 0.07, (-0.58, 2.06), (-0.38, 1.90), 0.036, 5),
    (T_RIP[0], T_RIP[1] - T_RIP[0], (-0.62, 2.16), (-0.40, 1.08), 0.050, 8),
]


def sheet_fall(t):
    return ease("in", (t - T_FALL[0]) / (T_FALL[1] - T_FALL[0]))


def sheet_hit(t):
    hit = None
    for ts, (X, Y) in ((T_STAB[0], (-0.52, 1.74)), (T_STAB[1], (-0.48, 1.98)), (T_RIP[0], (-0.52, 1.6))):
        if t >= ts - 0.01:
            p = ROOM.P(X, Y, L.SHEET_Z)
            hit = (ts, p[0], p[1], 1.6)
    return hit


def draw_slashes(f, t, ctx, sh):
    """Cut-paper slashes: lens-shaped slits through the lit sheet, light pouring through."""
    fall = sheet_fall(t)
    vis = 1.0 - clamp(fall * 2.2)
    if vis <= 0.01:
        return
    k = ROOM.ppm(L.SHEET_Z)
    live = []
    for (t0, dur, a, b, wm, seed) in SLASHES:
        if t < t0:
            continue
        u = ease("out", (t - t0) / dur)
        gape = 1.0 + 0.9 * L.k_(t, t0 + dur, 0.5, "out")
        p0 = ROOM.P(a[0], a[1], L.SHEET_Z)
        p1 = ROOM.P(b[0], b[1], L.SHEET_Z)
        pts = bass.slash_pts(p0, p1, wm * k * gape, u=u, tail=0.0, belly=0.42, seed=seed)
        if pts:
            live.append(pts)
    if not live:
        return
    ctx.save()
    sh.path(ctx, t, hit=sheet_hit(t), fall=fall)
    ctx.clip()
    for pts in live:
        draw.poly(ctx, pts)
        draw.fill(ctx, mix(HOT, (1.0, 1.0, 1.0), 0.25), vis)
    ctx.restore()
    with f.light(blur=6.0) as A:
        for pts in live:
            c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
            draw.poly(A, pts)
            draw.fill(A, HOT, 0.6 * vis)
            glow(A, c, 26.0, HOT, 0.35 * vis)
    with f.emit() as G:
        for pts in live:
            draw.poly(G, pts)
            draw.fill(G, HOT, 0.9 * vis)


# ----------------------------------------------------------------------------- drawing people
def _coat(lit):
    return L.her_look(clamp(0.13 + 0.40 * lit, 0.0, 0.6))


def draw_him(f, t, him, rims=(), clip=None, sk=None, M=None, flow=0.0):
    w = him.w
    look = L.him_look(flow)
    sk, M = L.draw_walker(f, t, w, look, rims=rims, eyes=0.0, clip=clip, sk=sk, M=M)
    sh, el, wr = [M.transform_point(*sk.j[n]) for n in ("shoulder_R", "elbow_R", "wrist_R")]
    arm, bl = L.golden_arm_polys(sh, el, wr, blade_rel=him.blade_rel(t), blade=him.blade(t))

    def _clip(c):
        if clip is not None:
            c.new_path()
            clip(c)
            c.clip()
    with f.layer() as Lc:
        Lc.save()
        _clip(Lc)
        L.fill_polys(Lc, arm + bl, INK)
        Lc.restore()
    with f.emit() as G:
        G.save()
        _clip(G)
        G.set_operator(cairo.OPERATOR_SOURCE)
        L.fill_polys(G, arm + bl, (0.0, 0.0, 0.0))
        G.restore()
    live = [r for r in rims if r[1] > 0.005]
    if live:
        with f.light() as A:
            A.save()
            _clip(A)
            for (col, a_, off) in live:
                L.polys_rim(A, arm, col, a_, off)
                L.polys_rim(A, bl, mix(col, (1, 1, 1), 0.3), min(1.0, a_ * 1.6), off)
            A.restore()
    return sk, M


def _split(f, t, z, draw_fn, near_door):
    """Room part as an item at depth z; the part outside the room goes through the doorway."""
    if not near_door:
        return [(z, lambda f_, t_: draw_fn(f_, t_, None))], []
    return [(z, lambda f_, t_: draw_fn(f_, t_, room_clip(z)))], [lambda: draw_fn(f, t, hall_clip(z))]


# ----------------------------------------------------------------------------- the room shots
def room_scene(f, t):
    him, her = _him(), _her()
    hw, sw = him.w, her.w
    dop = door_open(t)
    fall = sheet_fall(t)
    lamp = dict(X=LAMP_SET[0], Z=LAMP_SET[1], on=1.0, lift=0.0, tilt=0.0)
    b3 = R9.bulb3d(lamp)
    bulb_w = ROOM.P(*b3)
    hall_src = ROOM.P(-ROOM.hw - 1.1, 2.75, APT.DOOR_Z[0] - 0.7)
    exposed = clamp(fall * 1.4)

    # --- him
    hX, hZ, _ = hw.pos(t)
    hsk = hw.a.skeleton(t)
    hM = hw.matrix(t)
    hcen = hM.transform_point(*hsk.j["chest"])
    in_door = clamp(1.0 - abs(hX + 1.9) / 0.6) * clamp(dop * 3.0)
    run = L.env(t, him.t_run - 0.1, him.t_run + 0.1, him.t_arrive - 0.1, him.t_arrive + 0.1)
    run2 = L.env(t, T_TURN + 0.1, T_TURN + 0.25, T_SLAM + 0.1, T_SLAM + 0.3)
    hrims = [
        (mix(AMBER, HOT, 0.5), 0.75 * clamp(dop * 2.0) * lerp(0.35, 1.0, in_door), L.rim_offset(hcen, hall_src, 3.5)),
        (AMBER, 0.32 * (1.0 - exposed) * clamp((hZ - 2.4) / 0.6), (2.6, 0.0)),
        (AMBER, 0.32 * (1.0 - exposed) * clamp((hZ - 2.4) / 0.6), (-2.6, 1.0)),
        (mix(AMBER, HOT, 0.4), 0.55 * exposed * clamp((hZ - 2.4) / 0.6), L.rim_offset(hcen, bulb_w, 3.0)),
    ]

    def him_fn(f_, t_, clip):
        draw_him(f_, t_, him, rims=hrims, clip=clip, sk=hsk, M=hM, flow=max(run, run2))

    # --- her
    X, Z, _ = sw.pos(t)
    sk = sw.a.skeleton(t)
    M = sw.matrix(t)
    cen = M.transform_point(*sk.j["chest"])
    hall_lit = clamp(dop * 2.0) * clamp(1.0 - abs(Z - 1.75) / 0.9) * clamp(1.0 - (X + 1.9) / 1.4)
    look = _coat(max(hall_lit, 0.25 * exposed))
    rims = [
        (AMBER, 0.20 * (1.0 - exposed), (-2.2, 0.0)),                                       # the lit sheet
        (mix(AMBER, HOT, 0.4), 0.45 * exposed * clamp(1.0 - abs(X - b3[0]) / 2.0), L.rim_offset(cen, bulb_w, 3.0)),
        (mix(AMBER, HOT, 0.5), 0.6 * hall_lit, L.rim_offset(cen, hall_src, 3.0)),
        (mix(AMBER, HOT, 0.3), 0.18 * clamp(1.0 - t / 0.9), (2.0, -1.0)),                  # the leak at her feet
    ]
    yaw = sw.yaw_at(t)

    def her_fn(f_, t_, clip):
        L.draw_walker(f_, t_, sw, look, rims=rims, eyes=1.0, eye_open=1.0, eye_size=0.72, sk=sk, M=M, clip=clip)

    items = []
    hall_draws = []
    it, hd = _split(f, t, hZ, him_fn, hX < -1.55)
    items += it
    hall_draws += hd
    it, hd = _split(f, t, Z, her_fn, X < -1.5 and t > T_C)
    items += it
    hall_draws += hd

    # --- the decoy: the show's woman doll clamped before the bulb
    dstage = L.doll_stage(ROOM, DECOY[0], DECOY[1], DECOY[2], "woman", mirror=False)

    def doll_shape(c):
        L.doll_casters(c, dstage, "woman", mirror=False)

    def decoy_item(f_, t_):
        with f_.layer() as Lc:
            a = ROOM.P(DECOY[0], 1.02, DECOY[2])
            b = ROOM.P(LAMP_SET[0], 1.02, LAMP_SET[1])
            draw.capsule(Lc, a, b, 2.0, 2.0)
            draw.fill(Lc, INK)
            L.doll_object(Lc, dstage, INK, "woman", mirror=False)
        if exposed > 0.01:
            L.occlude_shape(f_, doll_shape)
            # the bulb burns round her edges
            with f_.light(blur=2.0) as A:
                A.push_group()
                doll_shape(A)
                A.set_operator(cairo.OPERATOR_DEST_OUT)
                A.save()
                A.translate(*L.rim_offset(ROOM.P(*DECOY), bulb_w, -2.0))
                doll_shape(A)
                A.restore()
                pat = A.pop_group()
                A.set_source_rgba(*mix(HOT, (1, 1, 1), 0.3), exposed)
                A.mask(pat)
    items.append((DECOY[2], decoy_item))

    def hall_fn(ctx):
        for fn in hall_draws:
            fn()

    feet = DOOR_FEET if t < T_BURST else ()
    door = dict(open=dop, hall=1.0, feet=feet, lever=lever(t), lever_rim=0.85 * (1.0 - L.k_(t, T_BURST, 0.2)),
                lever_rim_col=mix(AMBER, HOT, 0.3), lit=0.6 + 2.2 * clamp(dop * 1.5), mask=him.mask(t),
                hall_fn=hall_fn, spill=0.30)
    st = dict(lamp=lamp, cover=1.0, hit=sheet_hit(t), fall=fall, slashes=draw_slashes,
              rig=dict(woman=False, doll_col=mix(INK, mix(PAPER, AMBER, 0.35), 0.1)),
              casters=[(DECOY[2], doll_shape)], wall_casters=[], items=items, door=door, street=0.30,
              door_z=2.25 if dop > 0.12 else 99.0)
    R9.draw(f, t, st)
    f.post["bloom"] = 0.24


# ----------------------------------------------------------------------------- cameras
def _spline(t, keys):
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
    u = ease("inout", (t - k0[0]) / (k1[0] - k0[0]))
    return lerp(k0[1], k1[1], u), lerp(k0[2], k1[2], u), math.exp(lerp(math.log(k0[3]), math.log(k1[3]), u))


CAM_A = [(0.0, 52.0, 965.0, 3.30), (T_BURST, 40.0, 975.0, 3.55), (T_B, 30.0, 960.0, 3.05)]
CAM_B = [(T_B, 300.0, 960.0, 1.42), (1.62, 335.0, 930.0, 1.58), (2.00, 395.0, 880.0, 1.95), (3.00, 405.0, 870.0, 2.12),
         (3.70, 418.0, 856.0, 2.70), (T_C, 420.0, 852.0, 3.00)]
CAM_C = [(T_C, 215.0, 985.0, 1.62), (4.70, 175.0, 995.0, 1.70), (T_D, 120.0, 1000.0, 1.80)]


def kick(t, t0, amp, decay=9.0, freq=31.0):
    """A camera jolt at t0 (a damped shake)."""
    if t < t0:
        return 0.0
    dt = t - t0
    return amp * math.exp(-dt * decay) * math.sin(dt * freq)


def room_camera(t):
    if t < T_B:
        x, y, z = _spline(t, CAM_A)
        x += kick(t, T_BURST + 0.04, 9.0)
        y += kick(t, T_BURST + 0.04, 6.0, freq=27.0)
        return Camera(x, y, z).shaken(t, amp=1.2, rot_amp=0.03, freq=0.3, seed=1001)
    if t < T_C:
        x, y, z = _spline(t, CAM_B)
        for ts in T_STAB + (T_RIP[0],):
            y += kick(t, ts, 3.0, decay=14.0)
        return Camera(x, y, z).shaken(t, amp=2.0, rot_amp=0.05, freq=0.4, seed=1002)
    x, y, z = _spline(t, CAM_C)
    x += kick(t, T_SLAM, 10.0, decay=10.0)
    y += kick(t, T_SLAM, 6.0, decay=10.0, freq=24.0)
    return Camera(x, y, z).shaken(t, amp=2.0, rot_amp=0.05, freq=0.4, seed=1003)


# ----------------------------------------------------------------------------- D: the lock
def insert_scene(f, t):
    u = L.k_(t, T_KEY[0], T_KEY[1] - T_KEY[0], "inout")
    bolt = L.k_(t, T_KEY[1] - 0.08, 0.06, "in")
    x, y = 540.0, 960.0
    for tb in BLOWS:
        x += kick(t, tb, 14.0, decay=16.0, freq=40.0)
        y += kick(t, tb, 6.0, decay=16.0, freq=33.0)
    f.set_camera(Camera(x, y, 1.0).shaken(t, amp=1.5, rot_amp=0.05, freq=0.5, seed=1004))
    f.fill(INK)
    lit = 1.0
    for tb in BLOWS:
        lit -= 0.35 * L.k_(t, tb, 0.02) * (1.0 - L.k_(t, tb + 0.02, 0.12))
    with f.layer() as Lc:
        lock_closeup(Lc, f, (470.0, 1010.0), scale=2.4, bolt=bolt, key_turn=u, light=clamp(lit), t=t)
    # the hall bulb behind us: a warm sheen down the door face
    with f.light(blur=30.0) as A:
        glow_ellipse(A, (260.0, 640.0), 520.0, 900.0, AMBER, 0.10)
    with f.emit() as G:
        draw.circle(G, (470.0 + 150 * 2.4 + 5.0, 1010.0), 6.0)
        draw.fill(G, HOT, 0.5 * clamp(lit))
    f.post["bloom"] = 0.3


# ----------------------------------------------------------------------------- E: the hallway
HALL = sets.Hallway(origin=(540.0, 1640.0), scale=1.0)
HALL_FOOT = (488.0, 1652.0)               # her feet, her back to the door
HALL_YAW = 64.0


def hall_blows(t):
    """0..1 shake of the door under his fists."""
    v = 0.0
    for tb in BLOWS:
        if t >= tb:
            v = max(v, math.exp(-(t - tb) * 11.0))
    return v


def hall_shake(t):
    """Hallway.draw's own door jitter (world px), reproduced for what we draw on the door."""
    s = hall_blows(t)
    return s * (math.sin(t * 61.0) * 0.6 + noise1(t * 23.0, 4) * 0.4) * 3.0


class HerHall:
    """Her in the hallway (a 2-D Actor: feet on y = 0, 1 m = PX_M px)."""

    def __init__(self):
        a = Actor(cast.HER, None, x=0.0, ground=0.0, facing=HALL_YAW, t0=T_E - 1.0, seed=93)
        a.stand(until=T_SLIDE[0], idle=0.5)
        H = a.H
        hip0 = (cast.HER.hip - 0.006) * H
        sit_y = -0.115 * H

        def path(t):
            u = ease("inout", (t - T_SLIDE[0]) / (T_SLIDE[1] - T_SLIDE[0]))
            # she slides straight down the door (a small catch half way)
            u2 = clamp(u + 0.05 * math.sin(clamp(u) * math.pi * 2.0))
            return (lerp(0.0, -0.035 * H, u), lerp(-hip0, sit_y, u2))

        def pose(t, u):
            p = FG.Pose(0, 0, HALL_YAW)
            k = ease("inout", u)
            for s, ph in (("L", 0.0), ("R", 0.08)):
                kk = clamp(k * (1.0 + ph) - ph)
                p.legs[s] = dict(hip=lerp(3.0, 92.0 - 10 * ph, kk), abd=lerp(3.0, 7.0, kk),
                                 knee=lerp(4.0, 132.0, kk), ankle=lerp(0.0, -22.0, kk), toe=0.0)
            p.pitch = lerp(-3.0, -8.0, k)
            p.spine = [0.0, lerp(0.0, 6.0, k), lerp(0.0, 4.0, k)]
            p.head = lerp(-5.0, 2.0, k)
            for s in ("L", "R"):
                p.arms[s] = dict(sh=-20.0, abd=14.0, elbow=20.0, wrist=0.0, grip=0.3)
            return p
        a.free(T_SLIDE[1] - T_SLIDE[0], path, pose, at=T_SLIDE[0], end_x=0.0, blend=0.25)
        hold = pose(T_SLIDE[1], 1.0)
        end = path(T_SLIDE[1])

        def sat(t, u):
            p = pose(t, 1.0)
            br = math.sin(t * 5.2) * 1.2
            p.spine = [0.0, 6.0 + br, 4.0]
            return p
        a.free(T_END + 1.0 - T_SLIDE[1], lambda t: (end[0], end[1] + 0.003 * H * math.sin(t * 5.2)), sat,
               at=T_SLIDE[1], end_x=end[0], blend=0.05)
        # arms: palms flat on the door behind her while it jumps; the key fist to her chest after
        a.arm("L", T_E - 1.0, T_SLIDE[0] + 0.3, fade=0.2, sh=-30.0, abd=34.0, elbow=26.0, grip=0.1)
        a.arm("R", T_E - 1.0, T_CRASH + 0.25, fade=0.2, sh=-34.0, abd=30.0, elbow=30.0, grip=1.0)
        a.arm("R", T_CRASH + 0.35, T_END + 1.0, fade=0.35, sh=34.0, abd=10.0, elbow=128.0, grip=1.0)
        a.arm("L", T_SLIDE[0] + 0.5, T_END + 1.0, fade=0.5, sh=52.0, abd=8.0, elbow=70.0, grip=0.6)
        # head: to the lever when it rattles, back to us (and the dark) after
        a.key("head_yaw", [(T_E - 1.0, -10.0), (5.75, -10.0), (5.95, -34.0), (T_CRASH, -34.0),
                           (T_CRASH + 0.12, -6.0), (T_END + 1.0, -2.0)], fade=0.2)
        a.key("head", [(T_E - 1.0, -4.0), (T_CRASH, -4.0), (T_CRASH + 0.08, 6.0), (T_CRASH + 0.5, 0.0)], fade=0.15)
        # each blow jolts her off the door
        a.channel("x", lambda t: 3.2 * hall_blows(t) * math.sin((t - 5.0) * 70.0), T_E - 1.0, T_CRASH + 0.3,
                  mode="add")
        a.channel("pitch", lambda t: 3.5 * hall_blows(t), T_E - 1.0, T_CRASH + 0.3, mode="add")
        a.eyes(T_E - 1.0, T_END + 1.0, fade=0.1, open=1.0)
        self.a = a

    def matrix(self, t):
        return L.place_matrix(HALL_FOOT, 1.0, 0.0)


@lru_cache(maxsize=1)
def _herhall():
    return HerHall()


def hall_lever(ctx, t, turn, shake):
    """The lever on the hall side of door 9 (Hallway draws a round knob there)."""
    kx, ky = HALL.knob
    kx += shake
    th = math.radians(36.0 * clamp(turn))
    Lv = 74.0
    ca, sa = math.cos(th), math.sin(th)
    tip = (kx - Lv * ca, ky + Lv * sa)
    draw.circle(ctx, (kx, ky), 14.0)
    draw.fill(ctx, mix(INK, PAL.fog_at(1.0), 0.40))
    draw.capsule(ctx, (kx + 4 * ca, ky - 4 * sa), tip, 6.0, 5.0)
    draw.fill(ctx, mix(INK, PAL.fog_at(1.0), 0.45))
    return tip


def lever_hall(t):
    """He works the handle from inside: the outer lever jerks."""
    if t < T_E - 0.2 or t > T_CRASH:
        return 0.0
    v = 0.5 + 0.5 * math.sin(t * 23.0 + 1.3 * math.sin(t * 7.0))
    return clamp(v * 1.1) * (0.6 + 0.4 * noise1(t * 6.0, 21))


def hall_scene(f, t):
    hh = _herhall()
    a = hh.a
    # camera: on the door and her, pushing in as she sinks
    keys = [(T_E, 395.0, 1235.0, 1.20), (T_POLICE, 380.0, 1255.0, 1.24), (T_SLIDE[1], 450.0, 1410.0, 1.52),
            (T_END, 470.0, 1460.0, 1.86)]
    x, y, z = _spline(t, keys)
    for tb in BLOWS:
        x += kick(t, tb, 4.0, decay=14.0, freq=37.0)
    x += kick(t, T_CRASH, 7.0, decay=8.0, freq=29.0)
    f.set_camera(Camera(x, y, z).shaken(t, amp=1.6, rot_amp=0.04, freq=0.35, seed=1005))
    fuse = L.k_(t, T_DARK - 0.03, 0.05)
    room = 1.0 - fuse
    flick = L.env(t, T_CRASH, T_CRASH + 0.05, T_DARK - 0.05, T_DARK)
    bulb = 1.0 - fuse
    if T_CRASH < t < T_DARK:                          # the circuit stutters before it goes
        bulb *= 0.75 + 0.25 * (1.0 if noise1(t * 30.0, 8) > -0.2 else 0.0)
    police = L.k_(t, T_POLICE, 0.4, "out")
    shake = hall_blows(t)
    HALL.draw(f, t, room=room, room_flicker=flick, bulb=bulb, police=police, door_shake=shake, feet=())
    sh_x = hall_shake(t)
    with f.layer() as Lc:
        tip = hall_lever(Lc, t, lever_hall(t), sh_x)
    if bulb > 0.05:
        with f.light(blur=2.0) as A:
            kx, ky = HALL.knob
            draw.capsule(A, (kx + sh_x, ky - 5.0), tip, 1.6, 1.4)
            draw.fill(A, AMBER, 0.35 * bulb)
    # her
    sk = a.skeleton(t)
    M = hh.matrix(t)
    b, r = siren(t, rate=1.6)
    pol_b = police * b
    pol_r = police * r
    look = L.her_look(clamp(0.16 + 0.30 * bulb + 0.35 * pol_r, 0.0, 0.6))
    with f.layer() as Lc:
        L.draw_skeleton(Lc, sk, look, M)
    L.occlude_figure(f, 1.0, sk, look, M)
    cen = M.transform_point(*sk.j["chest"])
    win = ((HALL.window_rect[0] + HALL.window_rect[2]) / 2, (HALL.window_rect[1] + HALL.window_rect[3]) / 2)
    with f.light() as A:
        L.rim(A, sk, look, M, AMBER, 0.30 * bulb, L.rim_offset(cen, HALL.bulb_p, 3.0))
        L.rim(A, sk, look, M, mix(BLUE, (1, 1, 1), 0.2), 0.85 * pol_b, L.rim_offset(cen, win, 3.5))
        L.rim(A, sk, look, M, RED, 0.75 * pol_r, L.rim_offset(cen, win, 3.0))
        L.rim(A, sk, look, M, HOT, 0.35 * room * (1.0 - flick * 0.5), (0.0, -2.2))
    # the key in her fist
    hand = M.transform_point(*sk.j["hand_R"])
    fing = M.transform_point(*sk.j["fingers_R"])
    ang = math.atan2(fing[1] - hand[1], fing[0] - hand[0]) + math.radians(70.0)
    kb = (hand[0] + 9.0 * math.cos(ang), hand[1] + 9.0 * math.sin(ang))
    with f.layer() as Lc:
        draw.capsule(Lc, hand, (hand[0] + 14.0 * math.cos(ang - 1.1), hand[1] + 14.0 * math.sin(ang - 1.1)), 1.6, 1.4)
        draw.ellipse(Lc, kb, 4.2, 3.2, angle=math.degrees(ang))
        draw.fill(Lc, mix(INK, PAL.fog_at(1.0), 0.5))
    with f.light(blur=1.5) as A:
        glow(A, kb, 7.0, mix(BLUE, (1, 1, 1), 0.4), 0.7 * pol_b)
        glow(A, kb, 6.0, RED, 0.5 * pol_r)
        glow(A, kb, 5.0, AMBER, 0.4 * bulb)
    with f.layer() as Lc:
        L.draw_eyes(f, sk, look, Lc, M, par=1.0, glow_k=1.0, open_=1.0, size=1.0)
    f.post["bloom"] = 0.26


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    if t < T_D:
        f.set_camera(room_camera(t))
        room_scene(f, t)
    elif t < T_E:
        insert_scene(f, t)
    else:
        hall_scene(f, t)


def motion_blur(t, T):
    # the burst, the stabs and the slam (never across a cut)
    if T_BURST - 0.01 < t < T_BURST + 0.14:
        return 2
    for ts in T_STAB + (T_RIP[0],):
        if ts - 0.08 < t < ts + 0.03:
            return 2
    if T_SLAM - 0.12 < t < T_SLAM + 0.02:
        return 2
    return 1


def cues(T):
    return [
        Cue(0.0, "silence; the lever handle's slow metal creak continues", gain_db=-12, pan=-0.6),
        Cue(T_STOP, "the latch clicks free", gain_db=-10, pan=-0.6),
        Cue(T_BURST, "the door BURSTS open and bangs off its stop; hallway air", gain_db=-3, pan=-0.5),
        Cue(T_BURST + 0.02, "a muted brass stab (score)", gain_db=-8, pan=0.0),
        Cue(1.30, "heavy running footsteps across bare boards, his coat flapping", gain_db=-8, pan=-0.2),
        Cue(T_STAB[0], "the knife punches through the sheet: a cloth rip", gain_db=-6, pan=0.0),
        Cue(T_STAB[1], "the knife punches through the sheet again", gain_db=-6, pan=0.05),
        Cue(T_RIP[0], "a long tearing rip down the sheet", gain_db=-5, pan=0.05),
        Cue(T_FALL[0], "clothes pins pop off the wire one after another; the sheet slumps down", gain_db=-8,
            pan=-0.1),
        Cue(T_FALL[1], "the bare bulb's hum, nothing else", gain_db=-16, pan=0.0),
        Cue(4.30, "her quick soft footsteps behind him", gain_db=-14, pan=-0.5),
        Cue(T_TURN, "he whips round: coat swish", gain_db=-12, pan=-0.2),
        Cue(T_SLAM, "the door SLAMS", gain_db=-2, pan=-0.6),
        Cue(5.12, "his body hits the door from inside", gain_db=-6, pan=-0.3),
        Cue(T_KEY[0], "the key turns in the lock", gain_db=-8, pan=0.0),
        Cue(T_KEY[1], "the deadbolt shoots home: a hard metal clack", gain_db=-5, pan=0.0),
        Cue(5.40, "fists hammering on the door, the handle rattling (eight blows to 6.5)", gain_db=-4, pan=0.0),
        Cue(T_CRASH, "the lamp CRASHES inside: the bulb bursts, the stand clatters", gain_db=-3, pan=0.0),
        Cue(T_CRASH + 0.08, "an electric fizz and stutter", gain_db=-12, pan=0.0),
        Cue(T_DARK, "the fuse goes: a click, then total silence", gain_db=-10, pan=0.1),
        Cue(T_POLICE, "sirens arriving below, close; car doors", gain_db=-8, pan=-0.6),
        Cue(T_SLIDE[0], "her coat slides down the door; she sits on the floor", gain_db=-16, pan=0.0),
        Cue(9.5, "her breathing, shaking", gain_db=-18, pan=0.0),
    ]
