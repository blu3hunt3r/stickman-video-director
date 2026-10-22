"""s02 · THE HOOD: the village at night. The mother ties the hood and gives the basket, the
village shuts its doors, and the girl walks out through the gate (15.0 s).

IN (ink from s01, 1.25 s): Camera(-1640, 898.8, 0.92), still until 0.7. The girl stands in her
    mother's warm doorway, feet at screen (540, 1500), head top ~1175; her red cloak (hood
    DOWN, bunched on her back) spans ~1215-1400. A dark, blurred snowbank fills the frame
    below y ~1505-1530 (s01's black ground bleeds into it). The mother already kneels at
    the left (screen x ~300-480), a silhouette in the door's halo.
0.7-3.4   crane up and in to the two-shot (zoom 1.3); the bank sinks out of the frame.
[tied]    the mother's hands go to the hood; [red]-[hood] she pulls it up over the girl's head
          (3.38-3.88): a small red triangle in the night; [chin] she ties it (tugs).
[and]     she bows to the basket waiting on the snow, [gave] lifts it, [basket] gives it: the
          girl takes it in her right hand (5.45-5.70). The mother's hand rests on her shoulder.
8.45-9.35 the mother rises and turns her face away; her eyes close on [grandmother].
9.42      the girl turns to the street (via the camera) and walks right, 342 px/s, for good.
          The camera pulls back to the street and the houses up the hill: villagers stand in
          three lit doorways; the doors shut on [didn't] (m3), [know] (n3) and [yet] (m4).
10.05     the mother steps back into her doorway (a silhouette in the light); at 12.4 she
          opens her eyes and looks after her.
13.3-14.3 the girl looks back once; the mother lifts her hand (13.55).
OUT (dissolve to s03, 1.5 s): tracking camera at zoom 0.42, the girl walking right with her
    feet at screen (540, ~1350); she reaches the gate (x 0) at t 15.0 and is at x ~260 by
    15.75.
"""
import math
from functools import lru_cache

from engine import atmos, draw
from engine import figure as F
from engine.core import clamp, ease, fbm1, lerp, smoothstep
from engine.frame import Camera
from engine.motion import Actor, GAITS
from engine.timing import Cue, SceneTiming
from films.red import cast
from films.red import sets as S
from films.red.scenes import _lib_s02_s06 as L

V = S.VILLAGE
G = S.PATH.ground_y
MOOD = S.NIGHT
DOOR = V.door_x                         # -1650: the mother's door
GD = float(G(DOOR))                     # 1485.8
XG = L.S02_X0                           # the girl stands in the doorway
XM = -1850.0                            # the mother's pelvis while she kneels
XS = -1785.0                            # where she stands once she has risen
XB = -1768.0                            # the basket, waiting on the snow
MB = cast.MOTHER
MH = MB.height
R0, R1 = 8.45, 9.35                     # the mother rises
PICK = 4.88                             # her hand closes on the basket's handle
STEP_IN = 10.05                         # the mother steps back into her doorway
C0 = Camera(XG, float(G(XG)) - 540.0 / 0.92, 0.92)      # the IN
TWO = (-1785.0, GD - 650.0 / 1.3, 1.30)                   # the two-shot (ground at y 1610)
TRACK_Z = 0.42                          # the OUT: feet at y 1350
BANK_PAR = 3.0
INK = MOOD.ink


@lru_cache(maxsize=None)
def _W():
    T = SceneTiming("red", "s02")
    return dict(tied=T.at("tied"), red=T.at("red"), hood=T.at("hood"), chin=T.at("chin"),
                and_=T.at("and"), gave=T.at("gave"), basket=T.at("basket"), gm=T.at("grandmother", 1),
                didnt=T.at("didn't", 1), know=T.at("know"), yet=T.at("yet"))


def _seg(t, segs):
    """Piecewise target: segs = [(t0, t1, A, B, ease)]: A(t) -> B(t) over [t0, t1]; before the
    first segment A of the first, after the last B of the last."""
    if t <= segs[0][0]:
        return segs[0][2](t)
    for (t0, t1, A, B, e) in segs:
        if t <= t1:
            if t < t0:
                return A(t)
            u = ease(e, (t - t0) / max(t1 - t0, 1e-6))
            if u <= 0.0:
                return A(t)
            if u >= 1.0:
                return B(t)
            a, b = A(t), B(t)
            return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))
    return segs[-1][3](t)


# ----------------------------------------------------------------------------- the girl
def hood_u(t):
    """Hood raise 0 (down, on her back) .. 1 (up), pulled up on 'red hood'."""
    W = _W()
    return ease("inout", (t - (W["red"] - 0.06)) / 0.50)


def _girl_keys(a):
    a.key("head", [(0.4, 0.0), (1.0, -12.0), (2.9, -10.0), (3.4, -16.0), (4.6, -12.0), (8.4, -12.0),
                   (8.95, -26.0), (9.30, -24.0), (9.60, 0.0)], fade=0.3)
    a.key("head_yaw", [(13.15, 0.0), (13.55, 132.0), (14.0, 132.0), (14.40, 0.0)], fade=0.05)
    a.key("spine", [(2.9, 0.0), (3.4, 4.0), (4.5, 3.0), (4.9, 0.0)], fade=0.2)
    a.blink(2.1)
    a.blink(7.4)
    a.blink(12.6)
    return a


@lru_cache(maxsize=None)
def girl_ref():
    """The girl without her basket reach (the mother's hands read her head and shoulders
    from this one, so the two Actors never ask each other)."""
    return _girl_keys(L.girl_base())


@lru_cache(maxsize=None)
def girl():
    a = _girl_keys(L.girl_base())
    W = _W()
    a.reach(L.BASKET_SIDE, W["basket"] - 0.02, L.S02_TAKE + 0.05,
            target=lambda t: _handle_for_girl(t), fade=0.22, grip=0.95)
    L.carry(a, L.S02_TAKE, 60.0, fade=0.3)
    return a


# ----------------------------------------------------------------------------- the mother
def _kneel(t):
    """Kneeling on both knees in the snow (toes tucked), facing right, hands on her thighs."""
    g = float(G(XM))
    br = 1.6 * math.sin(2.0 * math.pi * t / 3.6)
    p = F.Pose(XM, g - 0.272 * MH + br, 0.0)
    p.legs["L"] = {"ik": (XM - 0.215 * MH, g - 0.085 * MH), "pitch": -62.0, "toe": 55.0, "abd": 3.0}
    p.legs["R"] = {"ik": (XM - 0.215 * MH - 8.0, g - 0.085 * MH), "pitch": -62.0, "toe": 55.0, "abd": 3.0}
    p.pitch = 14.0
    p.head = 8.0
    for s in ("L", "R"):
        p.arms[s].update(sh=26.0, elbow=52.0, abd=8.0, wrist=-12.0, grip=0.35)
    return p


@lru_cache(maxsize=None)
def _stand_y():
    a = Actor(MB, cast.mother(), x=XS, ground=G, facing=1)
    a.stand(dur=5.0, at=0.0, idle=0.0)
    return a.root(2.0)[1]


def _rise(t):
    """8.45-9.35: the far foot steps forward, she pushes up off it, the near foot joins."""
    u = clamp((t - R0) / (R1 - R0))
    p = _kneel(R0)
    g, gs = float(G(XM)), float(G(XS))
    o = 0.022 * MH
    a = ease("inout", u / 0.40)
    b = ease("inout", (u - 0.25) / 0.75)
    c = ease("inout", (u - 0.48) / 0.47)
    py0, py1 = g - 0.272 * MH, _stand_y()
    p.x = lerp(XM, XS, lerp(0.12 * a, 1.0, b))
    p.y = lerp(py0 - 0.02 * MH * a, py1, b)
    k0 = (XM - 0.215 * MH, g - 0.085 * MH)
    fL = (XS + o, gs - 0.039 * MH)
    fR = (XS - o, gs - 0.039 * MH)
    p.legs["L"] = {"ik": (lerp(k0[0], fL[0], a), lerp(k0[1], fL[1], a) - 0.07 * MH * math.sin(math.pi * a)),
                   "pitch": lerp(-62.0, 0.0, a), "toe": lerp(55.0, 0.0, a), "abd": 3.0}
    p.legs["R"] = {"ik": (lerp(k0[0] - 8.0, fR[0], c), lerp(k0[1], fR[1], c) - 0.06 * MH * math.sin(math.pi * c)),
                   "pitch": lerp(-62.0, 0.0, c), "toe": lerp(55.0, 0.0, c), "abd": 3.0}
    p.pitch = 14.0 + 18.0 * a * (1.0 - b) - 12.0 * b
    p.head = lerp(8.0, 2.0, b)
    for s in ("L", "R"):
        p.arms[s].update(sh=lerp(26.0, -2.0, b), elbow=lerp(52.0, 14.0, b), abd=lerp(8.0, 5.0, b),
                         wrist=lerp(-12.0, 0.0, b), grip=0.3)
    return p


def _mother_pose(t, u):
    return _kneel(t) if t < R0 else _rise(t)


def _mother_path(t):
    p = _mother_pose(t, 0.0)
    return (p.x, p.y)


def _rim(sk, u):
    """Where the hands hold the hood: the rim of its opening at raise u."""
    pts = L._hood_pts(sk, u)
    return (0.5 * (pts[0][0] + pts[13][0]), 0.5 * (pts[0][1] + pts[13][1]))


def _chin(sk):
    return F.head_point(sk, 0.24, 0.02)


def _m_target(side):
    """The mother's wrist target over time (side 'R' near, 'L' far, a little behind)."""
    W = _W()
    off = (0.0, 0.0) if side == "R" else (10.0, 8.0)
    gr = girl_ref()

    def sk(t):
        return gr.skeleton(t)

    def at_shoulder(t):
        s = sk(t)
        x, y = s.j["shoulder_L"]
        return (x - 20.0 + off[0], y + 22.0 + off[1])

    def at_nape(t):
        x, y = _rim(sk(t), 0.0)
        return (x - 6.0 + off[0], y + 10.0 + off[1])

    def at_rim(t):
        x, y = _rim(sk(t), hood_u(t))
        return (x - 12.0 + off[0], y + 12.0 + off[1])

    def at_chin(t):
        x, y = _chin(sk(t))
        q = clamp((t - W["chin"]) / 0.45)
        tug = 7.0 * math.sin(2 * math.pi * 3.2 * (t - W["chin"])) * math.sin(math.pi * q) * (1 if side == "R" else -1)
        return (x - 26.0 + off[0] + 0.4 * tug, y + 18.0 + off[1] + tug)

    def at_handle(t):
        return (XB - 4.0, float(G(XB)) - 84.0 - 10.0)

    def lift(t):
        """The basket's handle rising from the snow to where she offers it (an arc)."""
        u = ease("inout", (t - PICK) / (W["basket"] - PICK))
        x0, y0 = at_handle(t)
        x1, y1 = (-1702.0, 1268.0)
        return (lerp(x0, x1, u), lerp(y0, y1, u) - 40.0 * math.sin(math.pi * u))

    def offer(t):
        return (-1702.0, 1268.0 + 2.0 * math.sin(4.0 * (t - W["basket"])))

    if side == "R":
        segs = [(0.0, 0.1, at_shoulder, at_shoulder, "inout"),
                (W["tied"] - 0.20, W["tied"] + 0.26, at_shoulder, at_nape, "inout"),
                (W["red"] - 0.10, W["red"] - 0.04, at_nape, at_rim, "inout"),
                (W["hood"] + 0.12, W["chin"] - 0.04, at_rim, at_chin, "inout"),
                (W["and_"] - 0.05, PICK - 0.02, at_chin, at_handle, "inout"),
                (PICK - 0.02, W["basket"], at_handle, lift, "linear"),
                (W["basket"], W["basket"] + 0.01, lift, offer, "linear"),
                (L.S02_TAKE + 0.22, L.S02_TAKE + 0.55, offer, at_shoulder, "inout")]
    else:
        segs = [(0.0, 0.1, at_shoulder, at_shoulder, "inout"),
                (W["tied"] - 0.14, W["tied"] + 0.30, at_shoulder, at_nape, "inout"),
                (W["red"] - 0.08, W["red"] - 0.02, at_nape, at_rim, "inout"),
                (W["hood"] + 0.14, W["chin"] - 0.02, at_rim, at_chin, "inout")]

    def target(t):
        return _seg(t, segs)
    return target


@lru_cache(maxsize=None)
def mother():
    W = _W()
    m = Actor(MB, cast.mother(), x=XM, ground=G, facing=1, seed=11, name="mother")
    m.free(R1 + 40.0, path=_mother_path, pose=_mother_pose, at=-40.0, end_x=XS, blend=0.25)   # to R1
    m.stand(until=STEP_IN, idle=0.6)
    m.walk(to=DOOR - 6.0, gait=GAITS["stroll"].but(speed=0.36), at=STEP_IN)     # into her doorway
    m.stand(until=60.0)
    # leaning in to the girl, bowing to the basket
    m.key("pitch", [(0.0, 14.0), (W["tied"] - 0.25, 14.0), (W["tied"] + 0.1, 24.0), (W["hood"] + 0.2, 26.0),
                    (W["chin"] + 0.3, 22.0), (W["and_"] + 0.06, 46.0), (PICK + 0.04, 52.0),
                    (W["basket"] - 0.1, 22.0), (L.S02_TAKE + 0.3, 17.0), (8.15, 14.0)], fade=0.3)
    m.look_at(-1.0, 8.2, target=lambda t: girl_ref().skeleton(t).j["head"], fade=0.3)
    m.reach("R", -1.0, 8.15, target=_m_target("R"), fade=0.35, grip=0.85)
    m.reach("L", -1.0, W["and_"], target=_m_target("L"), fade=0.3, grip=0.8)
    # she rises, turns her face away; her eyes close on "grandmother"
    m.key("head_yaw", [(8.80, 0.0), (9.25, 74.0), (12.30, 74.0), (12.85, 0.0)], fade=0.15)
    m.key("head", [(8.80, 4.0), (9.25, 18.0), (12.30, 18.0), (12.85, -4.0)], fade=0.15)
    m.key("eyes.open", [(W["gm"] - 0.04, 1.0), (W["gm"] + 0.20, 0.0), (12.45, 0.0), (12.75, 1.0)], fade=0.04)
    # she lifts her hand when the girl looks back
    m.arm("R", 13.55, 15.0, fade=0.4, sh=122.0, elbow=30.0, abd=14.0, wrist=-12.0, grip=0.05)
    m.blink(1.7)
    m.blink(6.8)
    return m


# ----------------------------------------------------------------------------- the basket
def _handle_for_girl(t):
    """Her wrist target while she takes the basket: just below the mother's grip."""
    sk = mother().skeleton(t)
    x, y = L.basket_hand(sk, "R")
    return (x + 10.0, y + 14.0)


@lru_cache(maxsize=None)
def _swing():
    """Basket swing from the girl's walk (a light pendulum on her hand)."""
    return L.basket_pendulum(0.0, 0.0)


def basket(t, skm, skg):
    """(grip, angle, owner) of the basket: 'ground', 'mother' or 'girl'."""
    W = _W()
    ground = (XB, float(G(XB)) - 84.0)
    if t < PICK:
        return ground, 0.0, "ground"
    mh = L.basket_hand(skm, "R")
    gh = L.basket_hand(skg, L.BASKET_SIDE)
    if t < L.S02_TAKE:
        w = smoothstep(PICK, PICK + 0.12, t)
        ang = 16.0 * math.sin(2 * math.pi * 1.3 * (t - PICK)) * math.exp(-2.5 * (t - PICK)) * w
        return (lerp(ground[0], mh[0], w), lerp(ground[1], mh[1], w)), ang, "mother"
    w = smoothstep(L.S02_TAKE, L.S02_TAKE + 0.16, t)
    g = (lerp(mh[0], gh[0], w), lerp(mh[1], gh[1], w))
    ang = 10.0 * math.sin(2 * math.pi * 1.4 * (t - L.S02_TAKE)) * math.exp(-2.2 * (t - L.S02_TAKE))
    if t > L.S02_GO - 0.5:
        ang -= math.degrees(_swing().angle(t))
    return g, ang, "girl"


# ----------------------------------------------------------------------------- villagers
VILLAGERS = {"m3": ("f", 31), "n3": ("m", 32), "m4": ("m", 33)}


@lru_cache(maxsize=None)
def _villager(did, x, y, sc):
    kind, seed = VILLAGERS[did]
    body = cast.VILLAGER_F if kind == "f" else cast.VILLAGER_M
    look = cast.villager_f() if kind == "f" else cast.villager_m("flatcap" if did == "n3" else "watch")
    k = (0.86 if kind == "m" else 0.9) * 609.0 * sc / body.height
    a = Actor(body, look, x=x, ground=y, facing=90.0, scale=k, seed=seed, name=did)
    a.stand(dur=80.0, at=-20.0, idle=0.7)
    a.key("head", [(9.6, 0.0), (10.2, 6.0)], fade=0.4)
    return a


def _door_figures(f):
    def hook(ctx, d, o, t, tm):
        if d["id"] not in VILLAGERS or o <= 0.02:
            return
        a = _villager(d["id"], round(d["x"], 2), round(d["y"], 2), d["sc"])
        sk = a.skeleton(t)
        F.draw_figure(f, sk, a.look, ctx, color=tm.ink, eyes=False)
        e1, e2, r, w, front = F.eye_points(sk, a.look)
        for e in (e1, e2):
            draw.ellipse(ctx, e, r * 0.95, r * 0.95)
            draw.fill(ctx, (0.96, 0.94, 0.86), 0.9)
        with f.emit(par=d["par"]) as Gl:
            for e in (e1, e2):
                draw.glow_disc(Gl, e, r * 6.0, (1.0, 0.96, 0.85), 0.55)
    return hook


# ----------------------------------------------------------------------------- camera
@lru_cache(maxsize=None)
def _campath():
    return L.CamPath([
        (-1.0, C0.x, C0.y, C0.zoom),
        (0.70, C0.x, C0.y, C0.zoom),
        (3.40, TWO[0], TWO[1], TWO[2]),
        (6.30, -1772.0, 1000.0, 1.36),
        (8.25, -1768.0, 992.0, 1.30),
        (9.30, -1690.0, 860.0, 0.80),
        (10.45, -1010.0, 645.0, 0.445),
        (11.90, -820.0, 612.0, 0.425),
    ])


def track(t):
    """The OUT camera: on the girl's mean walking x, her feet at screen y 1350."""
    x = L.walk_x(t)
    return Camera(x, float(G(x)) - 390.0 / TRACK_Z, TRACK_Z)


def camera(t):
    c = _campath()(t)
    w = ease("inout", (t - 12.15) / 2.45)
    if w > 0:
        c = L.cam_mix(c, track(t), w)
    return c


# ----------------------------------------------------------------------------- pieces
def _halo(f, t):
    """The door's warm light hanging in the snowy air around the opening (behind them)."""
    fl = S.flick(t, V.door.seed, rate=4.0, depth=0.12)
    with f.light(par=1.0, blur=36.0) as A:
        S.glow(A, (DOOR - 25.0, GD - 300.0), 420.0, MOOD.lamp, 0.22 * fl)
        S.glow(A, (DOOR - 190.0, GD - 260.0), 300.0, MOOD.lamp, 0.13 * fl)


@lru_cache(maxsize=None)
def _bank_pts():
    """The dark snowbank right in front of the lens at the IN (layer par 3): its top edge
    sits just under the girl's feet (screen y 1505-1530)."""
    cam = C0.parallax(BANK_PAR)
    pts = [(-700.0, 2600.0)]
    for i in range(41):
        sx = -700.0 + i * (2500.0 / 40.0)
        sy = 1517.0 + 11.0 * fbm1(sx / 260.0, 41) + 6.0 * fbm1(sx / 70.0, 42)
        pts.append((sx, sy))
    pts.append((1800.0, 2600.0))
    return [cam.to_world(p) for p in pts]


def _bank(f, t):
    if t > 3.4:
        return
    with f.layer(par=BANK_PAR, blur=22.0) as c:
        draw.smooth(c, _bank_pts(), close=True, tension=0.3)
        draw.fill(c, S.mix(INK, MOOD.snow_dark, 0.12))


def _doors():
    W = _W()
    return V.door_schedule({"m3": W["didnt"], "n3": W["know"], "m4": W["yet"]}, dur=0.22)


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    W = _W()
    cam = camera(t)
    f.set_camera(cam)
    f.post["bloom"] = lerp(0.07, 0.14, smoothstep(9.6, 10.6, t))
    V.draw_back(f, MOOD, doors=_doors(), door_figures=_door_figures(f), t=t)
    # the doorway's bloom is added over everything: keep it low while they stand in it
    V.draw_plane(f, MOOD, door_open=1.0, door_light=1.0, t=t, door_glow=lerp(0.15, 0.35, smoothstep(9.6, 10.6, t)))
    _halo(f, t)
    m, g = mother(), girl()
    skm = m.skeleton(t)
    skg = g.skeleton(t)
    grip, ang, owner = basket(t, skm, skg)
    look_g = L.look_hood(hood_u(t))
    near_basket = owner == "mother" or (owner == "girl" and t > L.S02_TURN + 0.12)
    with f.layer() as c:
        F.draw_figure(f, skm, m.look, c)
        if owner == "ground" or not near_basket:
            L.draw_basket(c, grip, ang, INK)
        F.draw_figure(f, skg, look_g, c)
        if t < 8.6:               # her near hand stays in front of the girl (hood, shoulder)
            L.draw_arm(c, skm, "R", m.look, INK)
        if near_basket:
            L.draw_basket(c, grip, ang, INK)
    V.draw_front(f, MOOD, door_light=0.7)
    lit = atmos.Glow((DOOR, GD - 300.0), 260.0, 1.3, MOOD.lamp)
    L.snow(f, MOOD, density=0.85, wind=26.0, gust=12.0, t=t, seed=21, lit=lit)
    _bank(f, t)


def cues(T):
    W = _W()
    return [
        Cue(-0.6, "village night ambience: wind, a distant dog, a creaking sign; fire crackle from the open door", -12, dur=16.0),
        Cue(W["tied"], "cloth rustle: the hood ribbons gathered", -14),
        Cue(W["red"] + 0.02, "soft wool swish: the hood pulled up over her head", -10, dur=0.5),
        Cue(W["chin"], "ribbon tied under the chin: two small tugs", -16, dur=0.4),
        Cue(PICK, "wicker creak: the basket lifted from the snow", -12),
        Cue(W["basket"] + 0.1, "the basket handed over: wicker creak, a bottle clinks softly", -12),
        Cue(R0, "the mother rises: knees out of the snow, skirt rustle", -15, dur=0.9),
        Cue(L.S02_GO, "small footsteps in snow, walking away (continue under the doors)", -13, dur=5.8),
        Cue(W["didnt"], "door closes (wooden, latch), up the hill left", -6, pan=-0.1),
        Cue(W["know"], "door closes, nearer, heavier", -5, pan=0.25),
        Cue(W["yet"], "door closes, far right, with a bolt", -7, pan=0.55),
        Cue(13.55, "a hush: wind only", -16, dur=2.2),
    ]
