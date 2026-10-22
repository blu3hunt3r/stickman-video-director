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
H_STAB = (-1.10, 3.22)                    # at the sheet, left of her shadow (the bulb clear of his head)
H_HIT = (-1.50, 1.98)                     # at the slammed door

# ----------------------------------------------------------------------------- the beats
T_STOP = 0.61                             # the lever reaches its stop
T_BURST = 1.00
T_B = 1.22                                # cut: the room, wide
T_STAB = (2.02, 2.42)                     # the knife punches through the sheet
T_RIP = (2.82, 3.00)                      # the long downward rip
T_FALL = (3.00, 3.42)                     # the torn piece drops off the wire
T_CURL = (3.00, 3.55)                     # the rest of the sheet swings back from the tear
RIP_X = (-0.57, -0.49)                    # the tear line: room X at the wire and at the hem
T_TURN = 5.00                             # the slam: he whips round
T_C = 4.15                                # cut: her escape
T_GRAB = 4.58                             # her hand on the leaf's outer handle
T_SLAM = 5.00
T_D = 5.08                                # cut: the lock
T_KEY = (5.14, 5.34)                      # the key turns, the bolt shoots
T_E = 5.55                                # cut: the hallway
BLOWS = (5.38, 5.60, 5.80, 5.98, 6.15, 6.30, 6.45)          # his weight, then his fists, on the door
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
        w.turn(-50.0, dur=0.14, via=-60.0)
        w.stand(T_TURN, idle=0.15)
        w.turn(160.0, dur=0.18, via=180.0)                                 # whips round
        w.go(H_HIT[0], H_HIT[1], BLOWS[0] - 0.02 - w.cursor, gait="run")
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
        up = (-0.98, 2.38, 3.12)                     # raised above his right shoulder
        wind = (-1.04, 2.50, 3.02)
        k = [
            (s1 - 0.22, up), (s1 - 0.08, wind), (s1, (-0.70, 1.92, 3.44)), (s1 + 0.09, (-0.70, 1.89, 3.45)),
            (s2 - 0.20, up), (s2 - 0.08, wind), (s2, (-0.68, 2.10, 3.44)), (s2 + 0.09, (-0.68, 2.07, 3.45)),
            (r0 - 0.24, up), (r0 - 0.07, (-1.00, 2.54, 3.05)), (r0, (-0.66, 2.36, 3.44)),
            (r1, (-0.60, 1.05, 3.44)), (T_FALL[1], (-0.70, 0.98, 3.40)), (T_FALL[1] + 0.6, (-0.86, 0.95, 3.32)),
            (T_TURN, (-0.90, 0.92, 3.30)),
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
        v = lerp(v, 25.0, L.env(t, T_RIP[0], T_RIP[1], T_TURN, T_TURN + 0.2))
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
        w.stand(T_C + 0.03, idle=0.30)
        w.go(-0.86, 2.46, 0.34, gait="brisk", yaw=0.0)               # out from behind the leaf
        self.t_edge = w.cursor
        w.go(-1.10, 2.02, 0.22, gait="brisk")                       # round its edge
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
    (T_STAB[0] - 0.02, 0.06, (-0.64, 1.97), (-0.42, 1.66), 0.075, 3),
    (T_STAB[1] - 0.02, 0.06, (-0.62, 2.15), (-0.38, 1.98), 0.065, 5),
    (T_RIP[0] - 0.01, T_RIP[1] - T_RIP[0] + 0.01, (-0.57, 2.40), (-0.50, 0.98), 0.085, 8),
]


def sheet_fall(t):
    """The torn left piece dropping off the wire (0..1)."""
    return ease("in", (t - T_FALL[0]) / (T_FALL[1] - T_FALL[0]))


def sheet_curl(t):
    return ease("out", (t - T_CURL[0]) / (T_CURL[1] - T_CURL[0]))


def sheet_hit(t):
    if t >= T_FALL[0]:
        return None
    hit = None
    for ts, (X, Y) in ((T_STAB[0], (-0.53, 1.80)), (T_STAB[1], (-0.50, 2.06)), (T_RIP[0], (-0.53, 1.7))):
        if t >= ts - 0.01:
            p = ROOM.P(X, Y, L.SHEET_Z)
            hit = (ts, p[0], p[1], 1.6)
    return hit


class TornSheet(L.Sheet):
    """The pulled sheet once the rip has run to the wire: the piece left of the tear drops off
    and piles on the floor; the right piece hangs on, its torn edge swinging back.
    outline() (shadows, light, clips) is the right piece; the left piece is drawn by draw()."""

    def __init__(self, base, drop, curl):
        L.Sheet.__init__(self, base.a, base.b, base.h, pins=base.pins, seed=base.seed)
        self.drop = drop
        self.curl = curl
        self.k = ROOM.ppm(L.SHEET_Z)
        self.rip = (ROOM.P(RIP_X[0], 1.5, L.SHEET_Z)[0], ROOM.P(RIP_X[1], 1.5, L.SHEET_Z)[0])
        self.floor = ROOM.P(0.0, 0.0, L.SHEET_Z)[1]

    def _edge(self, curl=True):
        """The torn edge, top -> bottom (world), cut-paper jagged."""
        xt, xb = self.rip
        y0, y1 = self.a[1], self.a[1] + self.h
        n = 18
        pts = []
        for i in range(n + 1):
            v = i / n
            x = lerp(xt, xb, v)
            if 0 < i < n:
                x += 0.018 * self.k * (1 if i % 2 else -1) * (0.5 + 0.9 * hash01(77, i))
            if curl:
                x += self.curl * (0.07 + 0.30 * v ** 1.4) * self.k
            pts.append((x, lerp(y0, y1, v) + (0.012 * self.k * hash01(78, i) if 0 < i < n else 0.0)))
        return pts

    def pin_points(self, fall=0.0):
        xt = self.rip[0] + self.curl * 0.07 * self.k
        return [p for p in L.Sheet.pin_points(self) if p[0] > xt + 8.0]

    def outline(self, t, sway=1.0, hit=None, fall=0.0, n_side=8, n_hem=12):
        a, b = self.a, self.b
        Wd = b[0] - a[0]
        sd = self.seed
        brz = sway * (0.010 * Wd * fbm1(t * 0.45, sd) + 0.004 * Wd * math.sin(t * 1.7 + sd))
        edge = self._edge()
        pts = [edge[0]]
        prev = edge[0]
        for p in self.pin_points():
            pts.append(((prev[0] + p[0]) / 2, (prev[1] + p[1]) / 2 + 0.035 * Wd / max(self.pins - 1, 1) * 1.6))
            pts.append(p)
            prev = p
        yt = b[1]
        for k in range(1, n_side + 1):
            u = k / n_side
            x = b[0] + brz * u * u + 0.006 * Wd * math.sin(u * 3 + t * 0.8 + sd)
            pts.append((x, lerp(yt, yt + self.h, u)))
        xe = edge[-1][0]
        for k in range(1, n_hem):
            u = k / n_hem
            pts.append((lerp(b[0], xe, u) + brz, b[1] + self.h + 0.012 * Wd * math.sin(u * 9.0 + t * 1.1 + sd)))
        return pts + edge[::-1]

    def left_piece(self):
        a = self.a
        return [a] + self._edge(curl=False) + [(a[0], a[1] + self.h)]

    def xf(self, pts):
        """The falling left piece's motion: it tips, drops and piles up on the floor."""
        d = self.drop
        dy = d * self.h * 1.25
        ang = math.radians(7.0 * d)
        ca, sa = math.cos(ang), math.sin(ang)
        cx, cy = self.rip[0], self.a[1]
        out = []
        for (x, y) in pts:
            rx = cx + (x - cx) * ca - (y - cy) * sa
            ry = cy + (x - cx) * sa + (y - cy) * ca + dy
            if ry > self.floor:
                ry = self.floor - 2.0 - (ry - self.floor) * 0.06
            out.append((rx, ry))
        return out

    def draw(self, f, t, ctx, light=None, level=1.0, back=True, base=None, sway=1.0, hit=None, fall=0.0,
             tears=(), folds=1.0, wire=True, pins=True):
        L.Sheet.draw(self, f, t, ctx, light=light, level=level, back=back, base=base, sway=sway, hit=None,
                     fall=0.0, tears=(), folds=folds, wire=wire, pins=pins)
        if self.drop >= 0.999:
            lp = self.xf(self.left_piece())
            draw.poly(ctx, lp)
            draw.fill(ctx, mix(INK, PAL.fog_at(1.0), 0.30))
            return
        lp = self.xf(self.left_piece())
        unlit = base or mix(INK, PAL.fog_at(1.0), 0.55)
        lk = clamp(level) * (1.0 - 0.7 * self.drop)
        hot = mix(unlit, HOT, lk)
        mid = mix(unlit, mix(AMBER, HOT, 0.45), lk)
        far = mix(unlit, mul(AMBER, 0.42), lk)
        lpnt = light or lp[0]
        Wd = self.b[0] - self.a[0]
        ctx.save()
        draw.poly(ctx, lp)
        ctx.clip_preserve()
        draw.radial(ctx, lpnt, 0, math.hypot(Wd, self.h) * 0.62, [(0, hot, 1), (0.28, mid, 1), (1, far, 1)])
        ctx.fill()
        # it folds as it falls
        draw.linear(ctx, (lp[0][0], 0), (lp[len(lp) // 2][0], 0),
                    [(0, INK, 0.15 + 0.4 * self.drop), (0.5, INK, 0.05), (1, INK, 0.3 * self.drop)])
        ctx.paint()
        ctx.restore()

    def shadow(self, ctx, t, casters, lamp=None, mag=1.0, soft=5.0, density=0.9, sway=1.0, hit=None, fall=0.0):
        """The shadow stays where the light throws it; the cloth falls out from under it."""
        L.Sheet.shadow(self, ctx, t, casters, lamp=lamp, mag=mag, soft=soft, density=density, sway=sway)
        if self.drop >= 0.999:
            return
        lp = self.xf(self.left_piece())
        xs = [p[0] for p in lp]
        ys = [p[1] for p in lp]
        L.shadow_screen(ctx, casters, region=lambda c: draw.poly(c, lp), bbox=(min(xs), min(ys), max(xs), max(ys)),
                        soft=soft, density=density, mag=mag, center=lamp)


def mul(c, k):
    return (c[0] * k, c[1] * k, c[2] * k)


def draw_slashes(f, t, ctx, sh):
    """Cut-paper slashes: lens-shaped slits through the lit sheet, light pouring through.
    On the torn sheet each slash is cut on both pieces (the left one falls away with its half)."""
    torn = isinstance(sh, TornSheet)
    k = ROOM.ppm(L.SHEET_Z)
    live = []
    for (t0, dur, a, b, wm, seed) in SLASHES:
        if t < t0:
            continue
        rip = seed == 8
        if rip and torn and sh.drop > 0.25:
            continue                         # the rip is the gap now
        u = ease("out", (t - t0) / dur)
        gape = 1.0 + 0.8 * L.k_(t, t0 + dur, 0.45, "out")
        p0 = ROOM.P(a[0], a[1], L.SHEET_Z)
        p1 = ROOM.P(b[0], b[1], L.SHEET_Z)
        pts = bass.slash_pts(p0, p1, wm * k * gape, u=u, tail=0.0, belly=0.42, seed=seed)
        if pts:
            live.append((pts, 1.0 - (clamp(sh.drop * 4.0) if (rip and torn) else 0.0)))
    if not live:
        return
    regions = [(None, lambda c: sh.path(c, t, hit=sheet_hit(t)))]
    if torn:
        lp = sh.xf(sh.left_piece())
        regions.append((sh.xf, lambda c: draw.poly(c, lp)))
    core = mix(HOT, (1.0, 1.0, 1.0), 0.3)
    drawn = []
    for (xf, region) in regions:
        vis = (1.0 - 0.8 * sh.drop) if xf is not None else (1.0 - 0.6 * (sh.curl if torn else 0.0))
        ctx.save()
        ctx.new_path()
        region(ctx)
        ctx.clip()
        for pts, a_ in live:
            q = xf(pts) if xf is not None else pts
            draw.poly(ctx, q)
            draw.fill(ctx, core, a_ * vis)
            drawn.append((q, a_ * vis, region))
        ctx.restore()
    with f.light(blur=5.0) as A:
        for q, a_, region in drawn:
            A.save()
            A.new_path()
            region(A)
            A.clip()
            draw.poly(A, q)
            draw.fill(A, HOT, 0.5 * a_)
            A.restore()
            c = (sum(p[0] for p in q) / len(q), sum(p[1] for p in q) / len(q))
            glow(A, c, 30.0, HOT, 0.30 * a_)
    with f.emit() as G:
        for q, a_, region in drawn:
            draw.poly(G, q)
            draw.fill(G, HOT, 0.9 * a_)


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
    lamp = dict(X=LAMP_SET[0], Z=LAMP_SET[1], on=1.0, lift=0.0, tilt=0.0, glow=lerp(1.0, 0.7, clamp(fall)),
                pool=lerp(1.0, 0.55, clamp(fall)))
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
    sheet_obj = TornSheet(R9.sheet_obj(1.0), fall, sheet_curl(t)) if t >= T_FALL[0] else None
    st = dict(lamp=lamp, cover=1.0, hit=sheet_hit(t), fall=fall, slashes=draw_slashes, sheet_obj=sheet_obj,
              caster_density=0.94 * (1.0 - 0.92 * sheet_curl(t)),
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


CAM_A = [(0.0, 52.0, 1045.0, 3.25), (T_BURST, 42.0, 1052.0, 3.45), (T_BURST + 0.16, 20.0, 985.0, 2.85),
         (T_B, 18.0, 980.0, 2.80)]
CAM_B = [(T_B, 300.0, 960.0, 1.42), (1.62, 318.0, 930.0, 1.58), (2.00, 368.0, 885.0, 1.95), (3.00, 376.0, 872.0, 2.10),
         (3.45, 410.0, 858.0, 2.95), (T_C, 424.0, 852.0, 3.45)]
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
LOCK_C = (470.0, 1010.0)                  # the lock's centre in the insert (world px, camera fixed)
LOCK_S = 2.4
# her pinch on the key's bow, in the key's own frame (x along the key from the keyhole, y across
# it; units of lock_closeup's scale; the bow spans x 40..170, |y| < 60): the thumb lies over the
# bow's face, the index finger curls round its end, the palm and the curled fingers sit beside it
PALM = [(28, -96), (70, -104), (124, -112), (150, -136), (140, -178), (96, -206), (40, -204), (6, -170), (4, -124)]
FINGERS = [((108, -96), (190, -66), (204, 0), 17, 14),          # index: round the bow's end
           ((128, -128), (176, -116), (172, -84), 15, 13),      # middle, curled
           ((112, -160), (150, -160), (146, -134), 14, 12)]     # ring, curled
THUMB = ((54, -98), (104, -50), (128, -14), 18, 15)
WRIST = (40, -170)
ELBOW_W = (-420.0, 1980.0)                # the forearm leaves the frame here (world px)


def _key_frame(u):
    a = math.radians(-90.0 + 90.0 * clamp(u))
    ca, sa = math.cos(a), math.sin(a)
    cx, cy = LOCK_C
    s = LOCK_S

    def K(x, y):
        return (cx + (x * ca - y * sa) * s, cy + (x * sa + y * ca) * s)
    return K


def _hand_polys(u):
    """Her right hand pinching the key (palm, curled fingers, thumb over the bow) and the
    forearm reaching in from below left, as polygons in world px."""
    K = _key_frame(u)
    s = LOCK_S
    polys = [[K(x, y) for x, y in PALM]]
    for (a, m, b, ra, rb) in FINGERS + [THUMB]:
        pa, pm, pb = K(*a), K(*m), K(*b)
        polys.append(_capsule_poly(pa, pm, ra * s, (ra + rb) * 0.5 * s))
        polys.append(_capsule_poly(pm, pb, (ra + rb) * 0.5 * s, rb * s))
    w = K(*WRIST)
    polys.append(_capsule_poly(w, ELBOW_W, 58.0, 150.0))
    return polys


def _capsule_poly(a, b, ra, rb, n=10):
    dx, dy = b[0] - a[0], b[1] - a[1]
    Ln = math.hypot(dx, dy) or 1.0
    ang = math.atan2(dy, dx)
    pts = []
    for i in range(n + 1):
        th = ang + math.pi / 2 + math.pi * i / n
        pts.append((a[0] + ra * math.cos(th), a[1] + ra * math.sin(th)))
    for i in range(n + 1):
        th = ang - math.pi / 2 + math.pi * i / n
        pts.append((b[0] + rb * math.cos(th), b[1] + rb * math.sin(th)))
    return pts


def _sleeve_poly(u):
    """The red cuff over the forearm's lower half."""
    w = _key_frame(u)(*WRIST)
    b = ELBOW_W
    dx, dy = b[0] - w[0], b[1] - w[1]
    Ln = math.hypot(dx, dy)
    nx, ny = -dy / Ln, dx / Ln

    def at(k, r):
        return (w[0] + dx * k + nx * r, w[1] + dy * k + ny * r)
    k0 = 0.36
    r0 = lerp(58.0, 150.0, k0) + 14.0
    return [at(k0 + 0.02, r0), at(k0, 0.0), at(k0 + 0.02, -r0), at(1.05, -170.0), at(1.05, 170.0)]


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
    cx, cy = LOCK_C
    s = LOCK_S
    gap_x = cx + 150 * s
    with f.layer() as Lc:
        lock_closeup(Lc, f, LOCK_C, scale=s, bolt=bolt, key_turn=u, light=clamp(lit), t=t)
    # the hall bulb behind her: a warm wash down the door face, brass on the escutcheon
    with f.light(blur=30.0) as A:
        glow_ellipse(A, (300.0, 560.0), 640.0, 1000.0, AMBER, 0.20)
        glow_ellipse(A, (cx - 30.0, cy - 120.0), 150.0, 260.0, AMBER, 0.16)
    # the deadbolt crosses the bright gap (lock_closeup's gap light would wash over it)
    bl = 90 * s * bolt
    if bolt > 0.0:
        with f.layer() as Lc:
            draw.rect(Lc, gap_x - 20 * s, cy - 22 * s, gap_x + bl, cy + 22 * s)
            draw.fill(Lc, mix(INK, PAL.fog_at(1.0), 0.18))
        with f.light(blur=2.0) as A:
            A.rectangle(gap_x - 20 * s, cy - 22 * s, 20 * s + bl, 3.0 * s)
            draw.fill(A, HOT, 0.45 * clamp(lit))
    # her hand turning the key; the red cuff of the coat
    polys = _hand_polys(u)
    with f.layer() as Lc:
        L.fill_polys(Lc, polys, INK)
        draw.poly(Lc, _sleeve_poly(u))
        draw.fill(Lc, mix(INK, RED, 0.62))
    with f.light(blur=1.5) as A:
        L.polys_rim(A, polys, HOT, 0.55 * clamp(lit), (-7.0, 3.0))            # the gap light, right
        L.polys_rim(A, [_sleeve_poly(u)], AMBER, 0.35, (6.0, 6.0))             # the bulb, above left
    with f.emit() as G:
        draw.circle(G, (gap_x + 5.0, cy), 6.0)
        draw.fill(G, HOT, 0.5 * clamp(lit) * (1.0 - bolt))
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
    return 1


def _motion_blur_unused(t, T):
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
        Cue(T_C + 0.05, "her quick soft footsteps behind him", gain_db=-14, pan=-0.5),
        Cue(T_TURN, "he whips round: coat swish", gain_db=-12, pan=-0.2),
        Cue(T_SLAM, "the door SLAMS", gain_db=-2, pan=-0.6),
        Cue(BLOWS[0], "his body slams into the door from inside", gain_db=-4, pan=0.0),
        Cue(T_KEY[0], "the key turns in the lock", gain_db=-8, pan=0.0),
        Cue(T_KEY[1], "the deadbolt shoots home: a hard metal clack", gain_db=-5, pan=0.0),
        Cue(BLOWS[1], "fists hammering on the door, the handle rattling (six blows to 6.45)", gain_db=-4, pan=0.0),
        Cue(T_CRASH, "the lamp CRASHES inside: the bulb bursts, the stand clatters", gain_db=-3, pan=0.0),
        Cue(T_CRASH + 0.08, "an electric fizz and stutter", gain_db=-12, pan=0.0),
        Cue(T_DARK, "the fuse goes: a click, then total silence", gain_db=-10, pan=0.1),
        Cue(T_POLICE, "sirens arriving below, close; car doors", gain_db=-8, pan=-0.6),
        Cue(T_SLIDE[0], "her coat slides down the door; she sits on the floor", gain_db=-16, pan=0.0),
        Cue(9.5, "her breathing, shaking", gain_db=-18, pan=0.0),
    ]
