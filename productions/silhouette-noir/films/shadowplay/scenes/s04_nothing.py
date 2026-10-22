"""s04 · NOTHING · 11.5 s (+0.5 out handle): the police in apartment 9 find an empty room;
outside, a cop's torch finds HER in her window instead.

A  0.0-5.6  inside apartment 9 (sets.Apartment9, emptied: no lamp, sheet, table or rig), dark;
            the police strobe pulses blue / red through the window, hall light under the door.
     0.15   the door is kicked open (bangs on its stop 0.29, rebounds): hall light floods in;
            cop 1 in the doorway, his torch clicks on (0.27); he steps in (0.42-1.2).
     [police@0.985] cop 2's torch from the hall. The beams search, then land on nothing:
     [body@2.70]   torch 1 on the bare floor where she fell;
     [blood@3.52]  torch 2 on the bare back wall where the sheet hung;
     [woman@4.48]  torch 1 on the bare window, torch 2 joins it. Slow push on the window.
B  5.6-12.0 (cut on the window) outside, her building ('hers' facade) from window 9's side:
     5.6    her dark window 13 where window 9 was on screen; two faint eye glints in it.
     5.75-7.05 crane down her facade (the strobe washing it) to the street: the police car at
            the near curb, light bar strobing, a cop beside it, torch on the wet asphalt.
     [L10 6.2] 7.15 he raises the torch; the beam climbs the facade and the camera with it
            (7.25-8.25); 8.2 it finds HER window: her silhouette and her shadow on her wall,
            eyes lit. Slow push in.
     [dreamed@8.96] she steps back and aside, behind the drape, out of the light; the beam
            holds on the empty window.
     9.6    the torch drops; the camera pulls back to the whole building; the cop walks off
            left, the car pulls away right (from 9.85), its strobe sliding off the facade.
OUT 11.0-12.0 (bars, 2 horizontal): calm and mostly dark: her building, her window dark,
     the empty wet street, rain.
"""
import math
from functools import lru_cache

import numpy as np

from engine import atmos, draw
from engine import figure as FIG
from engine.core import clamp, lerp, smoothstep, fbm1, hash01
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import RED
from engine.timing import Cue
from films.shadowplay import cast, sets
from films.shadowplay.scenes import _lib_s02_s04 as L

INK = sets.INK
PAL = sets.PAL
TORCH = sets.mix(sets.HOT, (1.0, 1.0, 1.0), 0.25)       # police torch (warm-white incandescent)
CUT_T = 5.6


def _words(T):
    return (T.at("police"), T.at("body"), T.at("blood"), T.at("woman"), T.at("dreamed"))


def _cam_spline(keys):
    """Camera(t) through keys (t, (x, y, zoom)[, 'hold']); zoom interpolated in log space."""
    sp = L.Spline([(k[0], (k[1][0], k[1][1], math.log(k[1][2]))) + tuple(k[2:]) for k in keys])

    def cam(t):
        x, y, lz = sp(t)
        return Camera(x, y, math.exp(lz))
    return cam


def _aim_keys(keys, t):
    """Piecewise eased tuple keys [(t, value[, ease]), ...] (ease of the segment ending at a key)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        t1, v1 = keys[i][0], keys[i][1]
        if t <= t1:
            t0, v0 = keys[i - 1][0], keys[i - 1][1]
            k = L.kseg(t, t0, t1, keys[i][2] if len(keys[i]) > 2 else "inout")
            return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
    return keys[-1][1]


def _hand_target(a, t, aim, reach=0.31):
    """Where the torch hand goes: from the (approximate) shoulder toward `aim`, arm almost
    straight. Uses only the actor's root (no pose), so it can drive Actor.reach."""
    rx, ry = a.root(t)
    sx, sy = rx, ry - 0.29 * a.H
    dx, dy = aim[0] - sx, aim[1] - sy
    n = math.hypot(dx, dy) or 1.0
    return (sx + dx / n * reach * a.H, sy + dy / n * reach * a.H)


# ============================================================================= A: apartment 9
APT = sets.Apartment9(origin=(540.0, 880.0), scale=1.0)
ROOM = APT.room
DOOR_KEYS = [(0.15, 0.0), (0.29, 1.0, "out3"), (0.52, 0.84, "inout"), (0.95, 0.885, "inout")]
HALL_SRC = (-ROOM.hw - 1.1, 2.75, APT.DOOR_Z[0] - 0.7)      # Apartment9.lights' hallway bulb
LEAF_Z = APT.DOOR_Z[1] - 0.01                               # the open leaf stands about here
COP_HM = 1.84                                               # a cop is 1.84 m tall
COP1_Z, COP1_XH, COP1_X0, COP1_X1 = 1.74, -2.15, -1.84, -1.22   # hall -> doorway -> a step in
COP2_Z, COP2_XH, COP2_X = 2.00, -2.75, -2.10                # behind him, in the hall


def door_open(t):
    return sets.door_swing(t, DOOR_KEYS)


def to3d(p, Z):
    """A world point p seen at room depth Z -> room (X, Y, Z)."""
    d = Z - ROOM.E[2]
    return ((p[0] - ROOM.ox) * d / ROOM.F + ROOM.E[0], ROOM.E[1] - (p[1] - ROOM.oy) * d / ROOM.F, Z)


def ray_exit(pos, d):
    """Where the ray pos + s d (pos inside the room) meets a wall, the floor or the ceiling."""
    s = 1e9
    for i, (lo, hi) in enumerate(((-ROOM.hw, ROOM.hw), (0.0, ROOM.h), (-10.0, ROOM.zb))):
        if d[i] > 1e-9:
            s = min(s, (hi - pos[i]) / d[i])
        elif d[i] < -1e-9:
            s = min(s, (lo - pos[i]) / d[i])
    return tuple(pos[i] + d[i] * s for i in range(3))


def torch_aims(w):
    """3D aim points of the two torches: they search, then land on nothing."""
    police, body, blood, woman, _ = w
    t1 = [(0.27, (0.30, 2.30, 4.20)), (0.80, (1.05, 1.30, 4.20), "out3"), (1.50, (1.55, 0.0, 3.40)),
          (2.05, (0.85, 0.0, 2.40)), (body - 0.35, (-0.45, 0.0, 2.80)), (body, (0.05, 0.0, 3.15), "out3"),
          (woman - 0.40, (0.10, 0.0, 3.20)), (woman, (0.06, 1.62, 4.20), "out3"), (CUT_T + 0.5, (0.08, 1.66, 4.20))]
    t2 = [(police - 0.05, (1.40, 2.90, 3.10)), (police + 0.6, (1.90, 1.55, 3.70), "out3"),
          (2.25, (1.20, 2.15, 4.20)), (blood - 0.35, (0.65, 2.35, 4.20)), (blood, (-0.92, 1.42, 4.20), "out3"),
          (woman + 0.15, (-0.86, 1.46, 4.20)), (woman + 0.70, (-0.18, 1.50, 4.20), "inout"),
          (CUT_T + 0.5, (-0.14, 1.47, 4.20))]
    return t1, t2


def _settle(t, t_land, amp):
    """Overshoot wobble of a beam right after it lands (m)."""
    dt = t - t_land
    if dt < 0.0 or dt > 0.9:
        return 0.0
    return amp * math.exp(-dt * 6.5) * math.sin(dt * 17.0)


def aim_at(i, t, w):
    k1, k2 = torch_aims(w)
    if i == 0:
        X, Y, Z = _aim_keys(k1, t)
        X += _settle(t, w[1], 0.05) + 0.02 * fbm1(t * 1.6, 5)
        Y += _settle(t, w[3], 0.04)
        Z += 0.02 * fbm1(t * 1.3, 6)
    else:
        X, Y, Z = _aim_keys(k2, t)
        X += _settle(t, w[2], 0.06) + 0.015 * fbm1(t * 1.4, 9)
        Y += 0.015 * fbm1(t * 1.9, 11)
    return (X, Y, Z)


def _cop(X, Z, seed, k=1.0):
    gy = ROOM.P(0.0, 0.0, Z)[1]
    sc = k * COP_HM * ROOM.ppm(Z) / cast.COP.height
    return Actor(cast.COP, cast.cop(), x=ROOM.P(X, 0.0, Z)[0], ground=gy, facing=1, scale=sc, seed=seed)


@lru_cache(maxsize=2)
def cops(w):
    """Cop 1 kicks the door in and steps into the room; cop 2 comes up behind him and stays
    in the doorway. Actors in world px at their depths, torch arms aimed (Actor.reach)."""
    police = w[0]
    c1 = _cop(COP1_XH, COP1_Z, 41)
    c1.stand(until=0.16, at=-1.0, idle=0.3)
    c1.walk(to=ROOM.P(COP1_X0, 0.0, COP1_Z)[0], at=0.16, speed=380.0)
    c1.stand(until=0.56, idle=0.4)
    c1.walk(to=ROOM.P(COP1_X1, 0.0, COP1_Z)[0], at=0.56, speed=240.0)
    c1.stand(until=30.0, idle=0.5)
    c1.reach("R", 0.24, 30.0, lambda t: _hand_target(c1, t, ROOM.P(*aim_at(0, t, w))), fade=0.1)
    c2 = _cop(COP2_XH, COP2_Z, 42, 0.98)
    c2.stand(until=police - 0.45, at=-1.0, idle=0.3)
    c2.walk(to=ROOM.P(COP2_X, 0.0, COP2_Z)[0], at=police - 0.45, speed=300.0)
    c2.stand(until=30.0, idle=0.5)
    c2.reach("R", police - 0.15, 30.0, lambda t: _hand_target(c2, t, ROOM.P(*aim_at(1, t, w))), fade=0.15)
    return c1, c2


def _cop_X(a, t, Z):
    return to3d((a.root(t)[0], 0.0), Z)[0]


def torches(t, w):
    """Torch states (or None) from the cops' hands: 2D hand / angle / scale for the prop,
    3D pos / dir / hit for the room light and the beam."""
    c1, c2 = cops(w)
    out = []
    for i, (a, Z, t_on) in enumerate(((c1, COP1_Z, 0.27), (c2, COP2_Z, w[0] - 0.02))):
        if t < t_on - 0.3:
            out.append(None)
            continue
        sk = a.skeleton(t)
        hand = sk.j["hand_R"]
        aim = aim_at(i, t, w)
        a2 = ROOM.P(*aim)
        ang = math.degrees(math.atan2(a2[1] - hand[1], a2[0] - hand[0]))
        sc = 0.62 * ROOM.ppm(Z) / sets.PX_M
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        lens = (hand[0] + 59.0 * sc * ca, hand[1] + 59.0 * sc * sa)
        pos = to3d(lens, Z + 0.08)
        d = tuple(b - c for b, c in zip(aim, pos))
        hit = ray_exit(pos, d)
        lv = smoothstep(t_on, t_on + 0.05, t)
        out.append(dict(hand=hand, ang=ang, scale=sc, pos=pos, dir=d, hit=hit, level=lv, sk=sk))
    return out


def door_blockers(t, w):
    """Door-light blocker mask(u, v) for the light map: the cops' silhouettes seen from the
    hallway bulb, projected onto the doorway (u 0 hinge .. 1 free edge, v 0 floor .. 1 top)."""
    c1, c2 = cops(w)
    z0, z1 = APT.DOOR_Z
    sx, sy, sz = HALL_SRC
    shapes = []
    for a, Z in ((c1, COP1_Z), (c2, COP2_Z)):
        X = _cop_X(a, t, Z)
        s = (-ROOM.hw - sx) / (X - sx)
        uc = (z1 - (sz + s * (Z - sz))) / (z1 - z0)
        vh = (sy + s * (COP_HM - sy)) / APT.DOOR_H
        hw = 0.17 * s / (z1 - z0)
        shapes.append((uc, vh, hw, 0.11 * s / (z1 - z0), 0.13 * s / APT.DOOR_H))

    def mask(u, v):
        m = np.zeros_like(u)
        for uc, vh, hw, hr, vr in shapes:
            body = np.clip((hw - np.abs(u - uc)) / 0.03, 0, 1) * np.clip((vh - 1.6 * vr - v) / 0.02, 0, 1)
            head = np.clip(1.0 - ((u - uc) / hr) ** 2 - ((v - (vh - vr)) / vr) ** 2, 0, 1) * 4.0
            m = np.maximum(m, np.clip(np.maximum(body, head), 0, 1))
        return m
    return mask


def _shadow_xf(ctx, Zc, Zl, src=HALL_SRC):
    """Map a figure drawn at depth Zc to its shadow on the plane Z = Zl, cast by the point
    light src (a uniform scale in the picture: both planes face the camera)."""
    sx, sy, sz = src
    s = (Zl - sz) / (Zc - sz)
    dc, dl = Zc - ROOM.E[2], Zl - ROOM.E[2]
    m = s * dc / dl
    A = ROOM.ox + ROOM.F / dl * sx * (1.0 - s)
    B = ROOM.oy - ROOM.F / dl * (sy - ROOM.E[1]) * (1.0 - s)
    ctx.translate(A, B)
    ctx.scale(m, m)
    ctx.translate(-ROOM.ox, -ROOM.oy)


def _leaf_lit_clip(ctx, op):
    """The open leaf, below the line where the doorway's head shades it from the hall bulb."""
    draw.poly(ctx, APT.door.leaf_quad(op))
    ctx.clip()
    sx, sy, sz = HALL_SRC
    pts = []
    for X in (-ROOM.hw, -0.9):
        s = (-ROOM.hw - sx) / (X - sx)
        pts.append(ROOM.P(X, sy - (sy - APT.DOOR_H) / s, LEAF_Z))
    a, b = pts
    draw.poly(ctx, [a, b, (b[0], b[1] + 2000.0), (a[0], a[1] + 2000.0)])
    ctx.clip()


def _room_marks(f, t):
    """Floorboards, skirting, picture rail, plaster cracks: ink drawn over the room light, so
    they only show where a torch or the hall light falls (the bare room)."""
    P = ROOM.P
    hw, h, zb = ROOM.hw, ROOM.h, ROOM.zb
    zn = -1.2
    with f.layer() as K:
        K.set_line_cap(0)
        # floorboards (15 cm) running toward the window, with staggered butt joints
        X = -hw + 0.15
        i = 0
        while X < hw - 0.05:
            draw.poly(K, [P(X, 0, zb), P(X, 0, zn)], close=False)
            draw.stroke(K, INK, 1.6, 0.55)
            for j in range(4):
                z = zb - 0.4 - 1.35 * j - 0.9 * hash01(7, i, j)
                if z > zn:
                    draw.poly(K, [P(X, 0, z), P(X + 0.15, 0, z)], close=False)
                    draw.stroke(K, INK, 1.4, 0.45)
            X += 0.15
            i += 1
        # skirting and picture rail round the walls (broken by the door), back corners
        for Y, wd in ((0.12, 2.2), (2.25, 1.6)):
            draw.poly(K, [P(-hw, Y, zb), P(hw, Y, zb)], close=False)
            draw.poly(K, [P(hw, Y, zb), P(hw, Y, zn)], close=False)
            draw.poly(K, [P(-hw, Y, zb), P(-hw, Y, APT.DOOR_Z[1] + 0.05)], close=False)
            if Y > APT.DOOR_H:
                draw.poly(K, [P(-hw, Y, APT.DOOR_Z[1] + 0.05), P(-hw, Y, zn)], close=False)
            else:
                draw.poly(K, [P(-hw, Y, APT.DOOR_Z[0] - 0.05), P(-hw, Y, zn)], close=False)
            draw.stroke(K, INK, wd, 0.6)
        for X in (-hw, hw):
            draw.poly(K, [P(X, 0, zb), P(X, h, zb)], close=False)
        draw.poly(K, [P(-hw, 0, zb), P(hw, 0, zb)], close=False)
        draw.stroke(K, INK, 2.0, 0.5)
        # plaster cracks on the back wall
        for k, (cx, cy, ang, n) in enumerate(((-1.25, 1.95, 70.0, 5), (0.95, 1.10, 110.0, 4),
                                               (-0.55, 0.55, 80.0, 3), (1.35, 2.15, 60.0, 4))):
            pts = [P(cx, cy, zb)]
            x, y = cx, cy
            for j in range(n):
                a = math.radians(ang + 50.0 * (hash01(11, k, j) - 0.5))
                x += 0.11 * math.cos(a)
                y -= 0.11 * math.sin(a)
                pts.append(P(x, y, zb))
            draw.poly(K, pts, close=False)
            draw.stroke(K, INK, 1.2, 0.5)


def _window_glare(f, t, tl):
    """A torch on the bare window: the glass flares, the rain on it catches the light."""
    X0, Y0, X1, Y1 = APT.WINDOW
    zb = ROOM.zb
    k = ROOM.ppm(zb)
    r = APT.window_rect()
    hits = []
    for st in tl:
        if st is None or st["level"] <= 0.01:
            continue
        hx, hy, hz = st["hit"]
        if hz > zb - 0.02:
            inside = smoothstep(-0.25, 0.05, min(hx - X0, X1 - hx, hy - Y0, Y1 - hy))
            if inside > 0.01:
                hits.append((ROOM.P(hx, hy, hz), inside * st["level"]))
    if not hits:
        return
    with f.light(blur=3.0) as A:
        for p, lv in hits:
            sets.glow(A, p, 0.42 * k, TORCH, 0.42 * lv)
            sets.glow(A, p, 0.12 * k, TORCH, 0.5 * lv)
        A.save()
        A.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
        A.clip()
        wsum = sum(lv for _, lv in hits)

        def wgt(x, y):
            return min(1.0, sum(lv * math.exp(-((x - p[0]) ** 2 + (y - p[1]) ** 2) / (0.35 * k) ** 2)
                                for p, lv in hits))
        sets.rain_glints(A, t, r, color=TORCH, alpha=0.9 * min(1.0, wsum), density=7.0, seed=99, speed=120.0,
                         length=9.0, width=1.3, wind=0.0, weight=wgt)
        A.restore()


def draw_apartment(f, t, T, w):
    cam = _cam_spline([(0.0, (395.0, 1000.0, 1.10), "hold"), (0.9, (395.0, 1000.0, 1.10)),
                       (w[1] + 0.25, (432.0, 1015.0, 1.13)), (w[2] + 0.25, (440.0, 980.0, 1.17)),
                       (w[3] + 0.55, (505.0, 930.0, 1.27)), (CUT_T, (512.0, 922.0, 1.32))])(t)
    sh = 1.6 * smoothstep(0.1, 0.4, t)
    f.set_camera(cam.copy(x=cam.x + sh * fbm1(t * 0.9, 31), y=cam.y + sh * fbm1(t * 0.9, 37)))
    tl = torches(t, w)
    c1, c2 = cops(w)
    op = door_open(t)
    hall = 0.85
    lights = []
    extra = []
    for st in tl:
        if st is None or st["level"] <= 0.01:
            continue
        reach = math.sqrt(sum((a - b) ** 2 for a, b in zip(st["hit"], st["pos"])))
        lights.append(dict(pos=st["pos"], dir=st["dir"], cone=6.0, soft=5.0, color=TORCH, power=2.0 * st["level"],
                           reach=reach))
        # the hot spot on the surface: brighter and crisper than the beam in the air
        extra.append(dict(kind="spot", pos=st["pos"], dir=st["dir"], cone=5.5, soft=2.5, color=TORCH,
                          power=7.0 * st["level"], r0=0.2))

    def marks(f_, t_):
        _room_marks(f_, t_)

    def people(f_, t_):
        if t_ <= 0.15:
            return
        xclip = ROOM.P(-ROOM.hw, 0.0, APT.DOOR_Z[0])[0]
        # the hall light on the open leaf, and cop 1's shadow thrown on it
        with f_.light(blur=2.0) as A:
            A.save()
            _leaf_lit_clip(A, op)
            q = APT.door.leaf_quad(op)
            draw.linear(A, q[0], q[1], [(0, sets.mix(sets.AMBER, sets.HOT, 0.3), 0.42 * hall),
                                        (1, sets.AMBER, 0.20 * hall)])
            A.paint()
            A.restore()
        with f_.layer(blur=1.5) as S:
            S.save()
            _leaf_lit_clip(S, op)
            S.save()
            S.rectangle(xclip, -5000.0, 10000.0, 10000.0)
            S.clip()
            _shadow_xf(S, COP1_Z, LEAF_Z)
            S.push_group()
            c1.draw(None, t_, S, eyes=False)
            st = tl[0]
            if st is not None:
                sets.flashlight(S, st["hand"], st["ang"], scale=st["scale"])
            S.pop_group_to_source()
            S.paint_with_alpha(0.85)
            S.restore()
            S.restore()
        with f_.layer() as Lc:
            Lc.save()
            Lc.rectangle(xclip, -5000.0, 10000.0, 10000.0)       # behind the near jamb: hidden
            Lc.clip()
            c2.draw(f_, t_, Lc, eyes=False)
            st = tl[1]
            if st is not None and st["level"] > 0:
                sets.flashlight(Lc, st["hand"], st["ang"], scale=st["scale"])
            c1.draw(f_, t_, Lc, eyes=False)
            st = tl[0]
            if st is not None:
                sets.flashlight(Lc, st["hand"], st["ang"], scale=st["scale"])
            Lc.restore()
    APT.draw(f, t, lamp=0.0, lamp_stand=False, sheet=False, table=False, rig=False, door_open=op, hall=hall,
             door_mask=door_blockers(t, w), police=1.0, street=0.3, flashlights=lights, extra_lights=extra,
             hooks={"after_room": marks, "after_door": people}, dust=0.8)
    _window_glare(f, t, tl)
    f.haze(PAL.fog_at(1.0), 0.03)


# ============================================================================= B: her building
HERS = sets.Facade(origin=(540.0, 3940.0), scale=1.0, variant="hers")
HERS_BLOCKS = sets.neighbours(HERS)
HW = sets.HER_WINDOW                                     # 13: row 3, col 3
HWR = HERS.window_rect(HW)                               # (412, 1050, 668, 1370)
HWC = HERS.window_center(HW)                             # (540, 1210)
HERS_LIT = {2: 0.55, 7: 0.45, 17: 0.8, 24: 0.6, 29: 0.5, 31: 0.75, 38: 0.5}
ST = sets.Street(HERS.ground_y, depth=760.0, seed=5)
CAR_U, CAR_X0 = 0.62, 860.0
COP_U, COP_X = 0.86, 250.0
LAMP = sets.Streetlamp((-40.0, HERS.ground_y + 40.0), height=680.0, facing=1)
RAISE_T, FOUND_T, LOWER_T, CAR_GO = 7.2, 8.2, 9.75, 9.95
DARK_TOP, DARK_BOT = (0.062, 0.070, 0.098), (0.020, 0.024, 0.037)     # the facade's dark glass

street_cam = _cam_spline([(CUT_T, (540.0, 1326.0, 0.86), "hold"), (5.72, (540.0, 1326.0, 0.86)),
                          (6.8, (600.0, 3560.0, 0.80), "hold"), (7.3, (600.0, 3560.0, 0.80), "hold"),
                          (8.28, (546.0, 1300.0, 0.97)), (9.3, (536.0, 1236.0, 1.30), "hold"),
                          (9.8, (536.0, 1236.0, 1.30), "hold"), (11.0, (590.0, 2900.0, 0.50)),
                          (12.2, (594.0, 2930.0, 0.49))])


def car_at(t):
    x = CAR_X0
    if t > CAR_GO:
        dt = t - CAR_GO
        x += 110.0 * dt + 520.0 * dt * dt
    return sets.PoliceCar((x, ST.lane_y(CAR_U)), scale=ST.depth_scale(CAR_U), facing=1)


def beam_target(t):
    """Where the cop's torch points (facade world): the wet street ahead of him, up the
    facade, onto her window, held, then down."""
    hx, hy = HWC
    gx, gy = COP_X + 260.0, ST.lane_y(0.5)
    p = _aim_keys([(RAISE_T - 0.05, (gx, gy)), (RAISE_T + 0.4, (395.0, 2950.0), "in3"),
                   (7.93, (548.0, 1640.0), "inout"), (FOUND_T, (hx + 4.0, hy - 6.0), "out3"),
                   (LOWER_T, (hx + 2.0, hy - 4.0)), (LOWER_T + 0.38, (gx + 120.0, gy), "in3")], t)
    wob = 1.0 - 0.75 * smoothstep(FOUND_T - 0.1, FOUND_T + 0.2, t)
    return (p[0] + 12.0 * wob * fbm1(t * 1.3, 17), p[1] + 9.0 * wob * fbm1(t * 1.1, 19))


def torch_on(t):
    return 1.0 - smoothstep(LOWER_T + 0.42, LOWER_T + 0.5, t)


def caught(t):
    """The torch's pool on her window (0..1)."""
    return smoothstep(FOUND_T - 0.2, FOUND_T + 0.02, t) * (1.0 - smoothstep(LOWER_T, LOWER_T + 0.22, t))


@lru_cache(maxsize=1)
def street_cop():
    gy = ST.lane_y(COP_U)
    sc = 1.84 * L.K_F / cast.COP.height * ST.depth_scale(COP_U)
    a = Actor(cast.COP, cast.cop(), x=COP_X, ground=gy, facing=1, scale=sc, seed=43)
    a.stand(until=LOWER_T + 0.55, at=-1.0, idle=0.5)
    a.walk(to=COP_X - 1500.0, at=LOWER_T + 0.55, speed=1.5 * L.K_F * ST.depth_scale(COP_U), turn=0.4)
    a.reach("R", 4.0, LOWER_T + 0.45, lambda t: _hand_target(a, t, beam_target(t)), fade=0.3)
    a.look_at(RAISE_T, LOWER_T + 0.2, lambda t: beam_target(t), fade=0.45, amount=0.8)
    return a


HER_X = HWC[0] - 22.0
HER_FLOOR = HERS.floor_y(HW) - 12.0         # she stands right at the glass (eyes clear of the meeting rail)


@lru_cache(maxsize=1)
def her_at_window():
    sc = HERS.person_h / cast.HER.height
    a = Actor(cast.HER, cast.her(), x=HER_X, ground=HER_FLOOR, facing=90.0, scale=sc, seed=44)
    a.stand(until=40.0, at=-5.0, idle=0.35)
    a.key("head", [(-5.0, 9.0), (FOUND_T - 0.02, 9.0), (FOUND_T + 0.18, 2.0, "out3"), (40.0, 2.0)], fade=0.0)
    return a


def step_back(t, dreamed):
    return L.kseg(t, dreamed, dreamed + 0.5, "inout")


def _her_xf(ctx, k):
    """She steps back and aside (left, behind the drape): smaller, a little lower."""
    s = 1.0 - 0.10 * k
    ctx.translate(HER_X - 95.0 * k, HER_FLOOR + 6.0 * k)
    ctx.scale(s, s)
    ctx.translate(-HER_X, -HER_FLOOR)


def her_window(t, dreamed):
    """Interior of window 13 (drawn by the facade, under its drapes and sash): dark glass,
    the torch's pool on her back wall, her shadow thrown up it, her, her eyes."""
    a = her_at_window()
    look = a.look

    def fn(ctx, win):
        x0, y0, x1, y1 = win.rect
        ww, wh = x1 - x0, y1 - y0
        draw.linear(ctx, (0, y0), (0, y1), [(0, DARK_TOP, 1), (0.55, sets.mix(DARK_TOP, DARK_BOT, 0.7), 1),
                                            (1, DARK_BOT, 1)])
        ctx.paint()
        lv = caught(t)
        kb = step_back(t, dreamed)
        tgt = beam_target(t)
        if lv > 0.005:
            # the pool on her back wall (the beam rises: it lands above where it enters)
            pc = (tgt[0] + 0.05 * ww, tgt[1] - 0.12 * wh)
            draw.radial(ctx, pc, 0, 0.62 * wh, [(0, sets.mix(DARK_TOP, TORCH, 0.62 * lv), 1),
                                                (0.45, sets.mix(DARK_TOP, TORCH, 0.30 * lv), 1),
                                                (1, DARK_TOP, 0)])
            ctx.paint()
            # her shadow on the wall: up and to the right of her (the torch is low, left)
            ctx.save()
            ctx.translate(0.07 * ww * (1 - 0.6 * kb), -0.17 * wh * (1 - 0.6 * kb))
            ctx.translate(HER_X, HER_FLOOR - 0.5 * win.person_h)
            ctx.scale(1.10, 1.10)
            ctx.translate(-HER_X, -(HER_FLOOR - 0.5 * win.person_h))
            _her_xf(ctx, kb)
            ctx.push_group()
            a.draw(None, t, ctx, eyes=False)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(0.78 * lv * (1.0 - 0.8 * kb))
            ctx.restore()
        # her
        ctx.save()
        _her_xf(ctx, kb)
        sk = a.draw(None, t, ctx, eyes=False)
        ctx.restore()
        # her eyes: two faint glints in the dark, wide and bright in the torch
        vis = 1.0 - smoothstep(0.15, 0.55, kb)
        gl = (0.55 + 0.45 * lv) * vis
        if gl > 0.01:
            e1, e2, r, wgt, front = FIG.eye_points(sk, look)
            s = 1.0 - 0.10 * kb
            r *= 1.5 * s
            pts = [(HER_X - 95.0 * kb + s * (e[0] - HER_X), HER_FLOOR + 6.0 * kb + s * (e[1] - HER_FLOOR))
                   for e in (e1, e2)]
            for p in pts:
                draw.ellipse(ctx, p, r * 0.95, r)
                draw.fill(ctx, look.eye_color, gl)
            with win.f.emit() as G:
                for p in pts:
                    draw.glow_disc(G, p, r * 6.0, look.eye_color, 0.55 * gl)
    return fn


def draw_window_light(f, t):
    """The torch on and around her window: the hot spot on the brick, glare on the glass,
    rain caught in it (additive, over the facade)."""
    lv = caught(t)
    tgt = beam_target(t)
    up = smoothstep(RAISE_T + 0.1, RAISE_T + 0.5, t) * torch_on(t)
    x0, y0, x1, y1 = HWR
    ww, wh = x1 - x0, y1 - y0
    with f.light(blur=4.0) as A:
        if up > 0.01:
            sets.glow_ellipse(A, tgt, 165.0, 185.0, TORCH, 0.30 * up)
            sets.glow_ellipse(A, tgt, 80.0, 90.0, TORCH, 0.22 * up * (1.0 - 0.6 * lv))
        if lv > 0.01:
            A.save()
            A.rectangle(x0, y0, ww, wh)
            A.clip()
            sets.glow(A, (tgt[0] - 0.18 * ww, tgt[1] + 0.30 * wh), 0.20 * ww, TORCH, 0.5 * lv)
            A.restore()
            sets.rain_glints(A, t, (x0 - 0.6 * ww, y0 - 0.3 * wh, x1 + 0.6 * ww, y1 + 0.8 * wh),
                             color=TORCH, alpha=0.8 * lv, density=1.4, seed=313, speed=1250.0, length=34.0,
                             width=1.6, wind=0.14,
                             weight=lambda x, y: math.exp(-(((x - tgt[0]) / (0.9 * ww)) ** 2 +
                                                            ((y - tgt[1]) / (0.9 * wh)) ** 2)))


def draw_street(f, t, T, w):
    cam = street_cam(t)
    f.set_camera(cam)
    sets.night_sky(f, t, glow_y=HERS.top_y + 40.0, spread=300.0, par=0.25, clouds=0.8)
    sets.draw_blocks(f, t, HERS_BLOCKS, layer=dict(par=1.0, fog=0.25))
    lit = dict(HERS_LIT)
    lit[HW] = 0.021                     # 'lit' only so that her interior callback runs
    HERS.draw(f, t, lit=lit, interiors={HW: her_window(t, w[4])}, shops=(0.0, 0.0), halo=0.9, emit=0.8)
    car = car_at(t)
    gone = smoothstep(CAR_GO + 0.3, CAR_GO + 1.5, t)
    sets.strobe_wash(f, t, car, (HERS.x0, 1000.0, HERS.x1, HERS.ground_y), k=1.5 * (1.0 - 0.85 * gone))
    draw_window_light(f, t)
    srcs = HERS.light_sources(t, HERS_LIT) + [LAMP.light_source()] + car.light_sources(t, 1.0 - 0.4 * gone)
    ST.draw(f, t, sources=srcs, lamp_pools=[(LAMP.lantern[0], 1.0)], reflections=0.9)
    LAMP.draw(f, t)
    car.draw(f, t, lights=1.0 - 0.4 * gone, wash=1.8 * (1.0 - 0.7 * gone), headlights=0.75)
    # the cop, his reflection, his torch
    a = street_cop()
    gy = ST.lane_y(COP_U)
    sk = a.skeleton(t)
    px = sk.j["pelvis"][0]
    ST.reflect(f, t, lambda c: a.draw(None, t, c, eyes=False), gy,
               (px - 0.4 * a.H, gy - 1.05 * a.H, px + 0.4 * a.H, gy), strength=0.5)
    on = torch_on(t)
    tgt = beam_target(t)
    hand = sk.j["hand_R"]
    ang = math.degrees(math.atan2(tgt[1] - hand[1], tgt[0] - hand[0]))
    b, r = car.strobe(t)
    rim = sets.mix(sets.mix(L.COOL, sets.AMBER, 0.3), sets.BLUE, min(1.0, 1.2 * b))
    rim = sets.mix(rim, RED, min(1.0, 1.2 * r))
    with f.layer() as Lc:
        L.rimlit(f, Lc, lambda c: a.draw(None, t, c, eyes=False), rim=(rim, 0.5 + 0.4 * max(b, r)), d=2.0)
        lens = sets.flashlight(Lc, hand, ang if on > 0 else 100.0, scale=0.62 * a.H / cast.COP.height)
    cone = None
    if on > 0.01:
        dist = math.hypot(tgt[0] - lens[0], tgt[1] - lens[1])
        ux, uy = (tgt[0] - lens[0]) / dist, (tgt[1] - lens[1]) / dist
        stop = ((tgt[0] - uy * 400.0, tgt[1] + ux * 400.0), (tgt[0] + uy * 400.0, tgt[1] - ux * 400.0))
        half = lerp(9.0, 1.9, smoothstep(RAISE_T, RAISE_T + 0.5, t)) if t < LOWER_T else \
            lerp(1.9, 9.0, smoothstep(LOWER_T, LOWER_T + 0.4, t))
        cone = atmos.beam(f, lens, ang, length=dist / 0.62, half_angle=half, color=TORCH, intensity=0.42 * on,
                          falloff=0.55, soft=0.5, core=0.6, fog=0.35, stop=stop, pool=0.0, glare=0.8 * on, t=t,
                          seed=7)
    f.haze(PAL.fog_at(0.85), 0.12, y0=3500.0, y1=4900.0, feather=500.0)
    atmos.rain(f, density=1.0, angle=-8.0, t=t, seed=21, alpha=0.65, lit=cone, lit_gain=3.5, lit_color=TORCH)


# ============================================================================= scene
def render(f, t, T):
    w = _words(T)
    if t < CUT_T:
        draw_apartment(f, t, T, w)
    else:
        draw_street(f, t, T, w)


def motion_blur(t, T):
    if 0.15 < t < 0.42:
        return 3
    if 5.9 < t < 6.7 or 7.45 < t < 8.15 or 10.0 < t < 10.85:
        return 2
    return 1


def cues(T):
    police, body, blood, woman, dreamed = _words(T)
    return [
        Cue(0.0, "dark room: rain on the glass, a siren loop muffled far below, strobe hum", gain_db=-20, dur=5.6),
        Cue(0.15, "door kicked open: wood crack, slam against the wall stop, hall echo", gain_db=-4, pan=-0.6),
        Cue(0.27, "torch clicks on; heavy boots on bare floorboards", gain_db=-12, pan=-0.5),
        Cue(police - 0.02, "second torch clicks on; a police radio crackles in the hall", gain_db=-14, pan=-0.7),
        Cue(body, "a boot stops: the bare floor creaks", gain_db=-16),
        Cue(blood, "beam sweeps the wall: sleeve rustle", gain_db=-20, pan=-0.2),
        Cue(woman, "rain against the bare window, close", gain_db=-12),
        Cue(CUT_T, "outside: rain hiss, siren whoop close, idling engine", gain_db=-8, dur=4.0),
        Cue(RAISE_T, "torch raised: click of the switch, a cop's grunt", gain_db=-16, pan=-0.3),
        Cue(FOUND_T, "the beam finds her: a sharp string sting", gain_db=-10),
        Cue(dreamed, "she steps back: a floorboard creaks far inside", gain_db=-22),
        Cue(LOWER_T + 0.45, "torch clicks off; footsteps away on wet pavement", gain_db=-14, pan=-0.6),
        Cue(CAR_GO, "police car pulls away: engine rev, tyres hiss on the wet street", gain_db=-8, pan=0.5, dur=2.0),
    ]
