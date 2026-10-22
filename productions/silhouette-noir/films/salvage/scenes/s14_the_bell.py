"""s14 · THE BELL: split level at night under a high moon. On deck the client cranks the winch,
pleased with himself; below the waterline the diver rises with his cut hose trailing, and the
load comes up the pale line beside him. On [bell@8.44] it breaks the surface: the Meridian's
BELL, water pouring off it. It is hauled up to the davit, swings and TOLLS for the first time in
thirty years. The client freezes. It swings back toward him (11.0 s).

IN  (scroll 'down' from s13 = an ascent, 1.0 s): split composition, waterline at screen y 700
    (the camera still rising, settled by ~0.9). Above: the stern of the boat, the client bent
    over the winch crank at screen x ~335 (fedora, trench, cigar ember), the davit and lantern,
    the moon (screen (430, 140)). Below: the pale line drops at x ~690 to the load, a dark,
    silt-shrouded mass at ~(690, 1800); the diver rises at left-centre ~(360, 1470), lamp beam
    up, the cut red hose trailing below him out of frame.

Beats (scene-local s):
  0-6.4      the client cranks steadily (bobbing with the crank); diver and load rise in
             parallel; [safe@3.67] he draws on the cigar (ember flares)
  5.5-8.3    he cranks faster (eager); 6.4-8.5 the camera cranes up and pushes in on the stern
  8.30       the crown loop breaks the surface ([bell@8.44]: shoulders out, then the flared
             mouth): water pours off it (sheets, then drips); foam where it left the sea
  8.8-9.75   hauled up to the davit, it starts to swing; the winch slows; the client lifts his
             head toward it
  9.75       the winch stops; the bell is at its outboard extreme: TOLL (1); the client freezes
             (the ember dies down); a 3 px shake
  10.90      it swings back over the stern toward him: TOLL (2), he flinches
OUT (hard cut on the second toll's echo): wide on the stern, the bell just past its inboard
    extreme and swinging right: crown loop ~(625, 830), lip centre ~(600, 1000) at zoom 0.66;
    the client straightening up at the winch (screen x ~225); the diver's helmet ~40 px under
    the surface by the ladder (screen ~(560, 1230)), lamp on.

The bell, the davit and the swell run on one clock shared with s15 (_lib: bell_state).
"""
import math

import numpy as np

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor
from engine.timing import Cue
from films.salvage import cast
from films.salvage import sets as S
from films.salvage.scenes import _lib_s01_s03_s16 as LIB

PAL = S.PAL
INK = PAL.ink
D2R = math.pi / 180.0

BOAT = S.Boat()
MOON = LIB.NIGHT_MOON
MOON_R = LIB.NIGHT_MOON_R
BRIGHT = LIB.NIGHT_BRIGHT
T_STOP = LIB.T_STOP                 # 9.75: the winch stops, TOLL 1
T_TOLL2 = LIB.TOLLS[1][0]           # 10.90


def _beats(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:
            return d
    return dict(safe=at("safe", 3.671), hauling=at("hauling", 2.765), bell=at("bell", 8.444))


T_BREAK = LIB.bell_break()          # ~8.30
T_CLEAR = 8.79                      # the lip leaves the water


# ============================================================================= camera
_CAM = [  # (t, x, y, zoom, ease into this key)
    (-0.5, -200.0, 900.0, 0.50),
    (0.9, -200.0, 520.0, 0.50, "out"),
    (5.9, -190.0, 475.0, 0.50, "inout"),
    (8.4, -205.0, -360.0, 1.02, "inout"),
    (9.75, -215.0, -430.0, 1.10, "inout"),
    (11.0, -165.0, -420.0, 0.86, "inout"),
]


def _cam_at(t):
    ks = _CAM
    if t <= ks[0][0]:
        return ks[0][1:4]
    for a, b in zip(ks, ks[1:]):
        if t <= b[0]:
            u = ease(b[4] if len(b) > 4 else "inout", (t - a[0]) / (b[0] - a[0]))
            z = math.exp(lerp(math.log(a[3]), math.log(b[3]), u))
            return lerp(a[1], b[1], u), lerp(a[2], b[2], u), z
    return ks[-1][1:4]


def _shake(t):
    """Short shudders on the tolls (<= 4 px)."""
    a = 0.0
    for tk, s in LIB.TOLLS[:2]:
        if t >= tk:
            a += 3.2 * s * math.exp(-(t - tk) / 0.25)
    return a


def camera(t):
    x, y, z = _cam_at(t)
    cam = Camera(x, y, z)
    a = _shake(t)
    if a > 0.05:
        k = a / z
        cam = Camera(x + k * noise1(t * 31.0, 3), y + k * noise1(t * 29.0, 7), z)
    return cam


# ============================================================================= the client
X_C = -612.0                        # pelvis x while cranking (feet at ~-600 / -636)
FEET_C = (-570.0, -630.0)           # front (near) and back foot x on deck


def _crank(t):
    """Crank angle (deg) and the grip (world)."""
    a = LIB.crank_deg(min(t, T_STOP))
    gx, gy = 604.0, -352.0
    r = math.radians(a)
    return a, BOAT.to_world((gx + math.cos(r) * 62.0, gy + math.sin(r) * 62.0), t)


def _rise_k(t):
    """0 bent over the crank .. 1 straightened up (after the freeze)."""
    return smoothstep(10.25, 11.6, t)


def _c_path(t):
    a = math.radians(_crank(t)[0])
    deck = BOAT.deck_y(X_C, t)
    k = _rise_k(t)
    bob = 1.0 - smoothstep(9.3, T_STOP, t)
    x = X_C + 12.0 * math.cos(a) * bob - 14.0 * k
    y = deck - 276.0 + 25.0 * math.sin(a) * bob
    y = lerp(y, deck - 318.0, k)
    return x, y


def _c_pose(t, u):
    a = math.radians(_crank(t)[0])
    bob = 1.0 - smoothstep(9.3, T_STOP, t)
    k = _rise_k(t)
    x, y = _c_path(t)
    p = F.Pose(x, y, 0.0)
    pitch = 42.0 + 12.0 * math.sin(a) * bob
    p.pitch = lerp(pitch, 6.0, k)
    p.spine = [4.0 * (1 - k), 6.0 * (1 - k), 4.0 * (1 - k) - 2.0 * k]
    # head: up toward the stern while cranking; pleased tilt on the puff
    puff = LIB.bump(t, 3.35, 3.65, 4.0, 4.6)
    p.head = -p.pitch * 0.88 - 6.0 * puff + 2.0 * noise1(t * 0.4, 5)
    for s, fx in (("R", FEET_C[0]), ("L", FEET_C[1])):
        dy = BOAT.deck_y(fx, t)
        p.legs[s] = {"ik": (fx + 6.0 * k * (1 if s == "L" else -1), dy - 0.043 * cast.CLIENT.height),
                     "pitch": 0.0, "toe": 0.0, "abd": 3.0}
    # the far arm hangs with the knife; the near one is on the crank (reach below)
    p.arms["L"] = dict(sh=lerp(-28.0, -6.0, k), abd=6.0, elbow=lerp(24.0, 16.0, k), wrist=8.0, grip=1.0)
    kr = smoothstep(10.2, 10.75, t)
    p.arms["R"] = dict(sh=lerp(60.0, 4.0, kr), abd=6.0, elbow=lerp(24.0, 16.0, kr), wrist=0.0, grip=lerp(1.0, 0.5, kr))
    p.eyes = dict(open=1.0, glow=0.9, look=0.0)
    return p


def _grip_target(t):
    a, g = _crank(t)
    # the wrist sits a little short of the handle (the fist closes round it)
    return (g[0] - 16.0, g[1] - 10.0)


CLIENT = Actor(cast.CLIENT, cast.client(), x=X_C, ground=1e6, facing=1, seed=12, name="client")
CLIENT.free(14.0, _c_path, _c_pose, at=-1.0)
CLIENT.reach("R", -1.0, 10.35, _grip_target, fade=0.35, grip=1.0)


def _bell_mid(t):
    st = LIB.bell_state(t, BOAT)
    return LIB.bell_point(st, (0.0, 80.0))


CLIENT.look_at(8.45, 13.0, _bell_mid, fade=0.5, amount=0.85)
CLIENT.blink(1.9)
CLIENT.blink(5.6)
CLIENT.blink(7.7)


def _ember(t, b):
    e = 0.55 + 0.1 * noise1(t * 0.7, 9)
    e += 0.95 * LIB.bump(t, b["safe"] - 0.25, b["safe"] + 0.05, b["safe"] + 0.45, b["safe"] + 1.6)
    e += 0.35 * LIB.bump(t, 7.2, 7.5, 7.7, 8.3)
    return e * (1.0 - 0.7 * smoothstep(T_STOP - 0.1, T_STOP + 0.9, t))


def _client_look(t, b):
    lk = cast.client(ember=_ember(t, b), coat_flow=0.18 + 0.1 * noise1(t * 0.5, 4))
    return lk


def _knife(L, sk, t):
    """The knife he cut the hose with, low in his far hand (drawn behind him)."""
    w = sk.j["wrist_L"]
    h = sk.j["hand_L"]
    ang = math.degrees(math.atan2(h[1] - w[1], h[0] - w[0])) - 35.0
    S.draw_knife(L, h[0], h[1], angle=ang, s=0.42)


# ============================================================================= the diver
H_TOP = 300.0                       # pelvis -> helmet top (head tilted back, rising)


def _top_depth(t):
    """Helmet-top depth below mean sea level: a steady rise, easing near the surface (breaks
    the surface at s15 ~0.3)."""
    if t <= 8.0:
        return 1500.0 - 110.0 * t
    D = 3.3
    u = min((t - 8.0) / D, 1.0)
    p0, m0, p1, m1 = 620.0, -110.0 * D, 0.0, -80.0 * D
    h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    v = h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1
    if t > 8.0 + D:
        v -= 80.0 * (t - 8.0 - D)
    return v


def _dv_x(t):
    return -560.0 + 290.0 * smoothstep(-0.5, 6.6, t) + 220.0 * smoothstep(8.2, 9.9, t)


def _dv_path(t):
    return _dv_x(t), _top_depth(t) + H_TOP


def _dv_pose(t, u):
    p = F.Pose(0.0, 0.0, 78.0 + 8.0 * noise1(t * 0.15, 3))
    kick = math.sin(2 * math.pi * t / 1.9)
    for s, ph in (("L", 0.0), ("R", math.pi)):
        k = math.sin(2 * math.pi * t / 1.9 + ph)
        p.legs[s] = dict(hip=6.0 + 9.0 * k, abd=4.0, knee=12.0 + 10.0 * max(0.0, k), ankle=-14.0, toe=0.0)
    # one hand up over the helmet (the ascent; the outboard one), the other easy at his side
    p.arms["L"] = dict(sh=148.0 + 5.0 * noise1(t * 0.3, 7), abd=14.0, elbow=28.0, wrist=6.0, grip=0.4)
    p.arms["R"] = dict(sh=14.0 + 6.0 * kick, abd=24.0, elbow=30.0, wrist=6.0, grip=0.3)
    p.pitch = -4.0 + 2.0 * noise1(t * 0.2, 11)
    p.spine = [0.0, -2.0, -3.0]
    p.head = -46.0 + 4.0 * noise1(t * 0.25, 13)
    p.eyes = dict(open=1.0, glow=1.0, look=0.0)
    return p


DIVER = Actor(cast.DIVER, cast.diver(helmet=True, weights=False, boots=False), x=-560.0, ground=1e6,
              facing=78.0, seed=9, name="diver")
DIVER.free(13.5, _dv_path, _dv_pose, at=-1.5)
DIVER.blink(4.4)

_INLET = LIB.Sampled(lambda t: costume.helmet_inlet(DIVER.skeleton(t)), -1.6, 11.6, 120)
_VALVE = LIB.Sampled(lambda t: LIB.helmet_valve(DIVER.skeleton(t)), -1.6, 11.6, 60)
def _lamp_flat(t):
    p, d, _ = costume.helmet_lamp(DIVER.skeleton(t))
    return (p[0], p[1], d[0], d[1])


_LAMP = LIB.Sampled(_lamp_flat, -1.6, 11.6, 60)


def _lamp_dir(t):
    v = _LAMP(t)
    return (v[0], v[1]), (v[2], v[3])


# ============================================================================= the cut hose
def _hose_current(t, x, y):
    return (26.0 + 10.0 * math.sin(0.37 * t + y / 700.0), -40.0 + 30.0 * math.sin(0.5 * t + y / 400.0))


def _hose_init(t0):
    a = _INLET(t0)
    n = 40
    out = []
    for i in range(n):
        s = i * 2300.0 / (n - 1)
        out.append((a[0] - 30.0 * math.sin(s / 300.0) - 0.05 * s, a[1] + s))
    return out


HOSE = LIB.hose_rope(_INLET, None, 2300.0, n=40, t0=-1.6, t1=11.6, current=_hose_current,
                     gravity=(0.0, 70.0), drag=1.6, stiffness=0.3, iters=10, init=_hose_init)


# ============================================================================= light
def _moon_screen(f):
    return (MOON[0], S.horizon_y(f) - MOON[1])


def _under_light(f, t):
    """Moonlight under the surface: faint rays and a soft band; a backlight pool behind the
    diver so his silhouette reads in the night water."""
    atmos.underwater_rays(f, surface_y=0.0, t=t, spacing=190.0, angle=95.0, fan=8.0, length=1800.0,
                          intensity=0.16, density=0.5, seed=14, blur=18, color=S.mix(PAL.moon, PAL.surface, 0.5))
    ps = f.cam.to_screen(DIVER.joint(t, "chest"))
    LIB.screen_glow(f, (ps[0], ps[1] - 80.0), 640.0 * f.cam.zoom / 0.5, PAL.surface, 0.10)


def _beam(f, t):
    """His helmet lamp, pointing up toward the surface (behind him)."""
    p, d = _lamp_dir(t)
    ang = math.degrees(math.atan2(d[1], d[0]))
    L = max(200.0, (p[1] - S.sea_y(p[0], t)) / max(0.2, -d[1]) + 40.0)
    atmos.beam(f, p, ang, length=L, half_angle=9.0, intensity=0.42, falloff=0.8, soft=0.5, core=0.5,
               fog=0.4, pool=0.0, dust=0.35, glare=0.0, t=t, seed=5)
    # where it meets the underside of the surface: a warm spot on the skin
    sx = p[0] + d[0] / max(0.2, -d[1]) * (p[1] - S.sea_y(p[0], t))
    with f.light(blur=14) as A:
        draw.glow_disc(A, (sx, S.sea_y(sx, t) + 10.0), 120.0, PAL.light, 0.12)


def _lamp_head(f, t):
    p, d = _lamp_dir(t)
    atmos.lamp(f, p, radius=8.0, intensity=0.9, halo=4.0, core=0.3, t=t, seed=6)


# ============================================================================= the bell
def _silt(L, st, t, k):
    """Silt and weed streaming off the load as it is hauled up (part of the dark mass)."""
    if k <= 0.0:
        return
    for i in range(22):
        h = hash01(77, i, 1)
        u = (hash01(77, i, 2) - 0.5) * 2.0
        lag = -110.0 + 380.0 * h
        p = LIB.bell_point(st, (u * 80.0 + 14.0 * math.sin(t * 0.9 + i), 120.0 + lag))
        r = (30.0 + 50.0 * hash01(77, i, 3)) * (0.7 + 0.6 * h)
        L.save()
        L.translate(p[0], p[1])
        L.scale(r, r * (1.2 + 0.8 * h))
        L.arc(0, 0, 1.0, 0, 2 * math.pi)
        L.restore()
        L.set_source_rgba(INK[0], INK[1], INK[2], 0.7 * k * (1.0 - 0.5 * h))
        L.fill()


def _sea_clip(c, x0, x1, t, below=True):
    pts = S.sea_pts(x0, x1, t, step=8.0)
    c.new_path()
    c.move_to(*pts[0])
    for q in pts[1:]:
        c.line_to(*q)
    yy = 1e5 if below else -1e5
    c.line_to(x1, yy)
    c.line_to(x0, yy)
    c.close_path()
    c.clip()


def _bell_under(f, t, st):
    """The load below the surface: a fogged, blurred dark mass shrouded in silt."""
    if st["lip_sea"] > 40.0:
        return
    top_d = st["top"][1]
    depth = max(0.0, top_d + 150.0)
    fog = (0.22 + 0.16 * smoothstep(0.0, 1600.0, depth) + 0.2 * (1.0 - smoothstep(7.7, 8.3, t))) \
        * (1.0 - 0.5 * smoothstep(7.9, 8.6, t))
    blur = lerp(3.0, 11.0, smoothstep(0.0, 1400.0, depth)) * f.cam.zoom / 0.5
    wc = S.water_at(depth, BRIGHT)
    x0, y0, x1, y1 = f.cam.view_rect(300)
    with f.layer(blur=blur, fog=fog, fog_color=wc) as L:
        L.save()
        _sea_clip(L, x0, x1, t, below=True)
        LIB.draw_bell_lit(L, st, (0.0, -1.0), f.cam.zoom, color=INK)
        _silt(L, st, t, 1.0 - smoothstep(8.2, 8.9, t))
        L.restore()


def _line(L, t, st):
    """The pale lifting line from the davit's sheave to the knot on the crown loop."""
    P, top = st["pivot"], st["top"]
    n = 14
    pts = []
    for i in range(n + 1):
        u = i / n
        bow = 18.0 * math.sin(math.pi * u) * smoothstep(400.0, 2000.0, st["line_len"])
        pts.append((lerp(P[0], top[0], u) + bow, lerp(P[1], top[1], u)))
    LIB.draw_hose(L, pts, 5.0, color=LIB.PALE)
    draw.circle(L, (top[0], top[1] + 4.0), 8.0)
    L.set_source_rgb(*INK)
    L.fill()


def _bell_air(L, f, t, st, md):
    """The bell above the surface: crisp ink, moonlit rim and wet sheen (flash on a toll)."""
    if st["top"][1] > S.sea_y(st["top"][0], t) + 10.0:
        return
    x0, y0, x1, y1 = f.cam.view_rect(300)
    wet = 1.0 - smoothstep(T_CLEAR, T_CLEAR + 3.0, t)
    rim = 0.30 + 0.25 * wet + 0.45 * clamp(st["ring"])
    sheen = 0.18 + 0.28 * wet + 0.30 * clamp(st["ring"])
    L.save()
    if st["lip_sea"] < 30.0:
        _sea_clip(L, x0, x1, t, below=False)
    LIB.draw_bell_lit(L, st, md, f.cam.zoom, rim=rim, sheen=sheen)
    L.restore()


def _bell_water(f, t, st):
    """Water sheeting off it as it leaves the sea, drips after, foam where it came out."""
    xb = st["top"][0]
    LIB.foam(f, t, xb + 10.0, T_BREAK - 0.05, 170.0, 7, k=0.9, life=3.4)
    LIB.foam(f, t, xb + 20.0, T_CLEAR - 0.05, 210.0, 8, k=1.0, life=3.0)
    LIB.splash(f, t, xb + 4.0, T_BREAK + 0.02, 40, 0.55, 31)
    LIB.splash(f, t, xb + 24.0, T_CLEAR, 60, 0.7, 32)
    if t > T_BREAK - 0.1:
        LIB.bell_pour(f, t, BOAT, T_CLEAR, rate=1.0, seed=5)
    # rivulets running down its flanks while it rises out of the sea (inside the silhouette)
    if T_BREAK < t < T_CLEAR + 1.6:
        k = smoothstep(T_BREAK, T_BREAK + 0.2, t) * (1.0 - smoothstep(T_CLEAR + 0.3, T_CLEAR + 1.6, t))
        c = f.ctx
        c.save()
        c.new_path()
        LIB.bell_path(c, st)
        c.clip()
        x0, y0, x1, y1 = f.cam.view_rect(300)
        _sea_clip(c, x0, x1, t, below=False)
        for j in range(9):
            side = 1.0 if j % 2 else -1.0
            u = 0.25 + 0.7 * hash01(5, j, 1)
            ph = hash01(5, j, 2) * 6.0
            pts = []
            for i in range(10):
                v = i / 9.0
                yy = lerp(30.0 + 20.0 * hash01(5, j, 3), 142.0, v)
                half = lerp(30.0, 64.0, clamp((yy - 30.0) / 112.0)) * (0.9 + 0.08 * u)
                xx = side * half * u + 2.0 * math.sin(yy / 9.0 + ph + 7.0 * t)
                pts.append(LIB.bell_point(st, (xx, yy)))
            LIB.draw_hose(c, pts, 1.6 / f.cam.zoom, color=LIB.MOONLIT, alpha=0.32 * k * (0.6 + 0.4 * u))
        c.restore()


def _deck_hose(L, t):
    """The pump end of the red hose, cut in s12, lying slack on deck by the winch."""
    pts = [(236.0, -196.0), (262.0, -184.0), (300.0, -168.0), (420.0, -166.0), (500.0, -167.0), (548.0, -171.0),
           (566.0, -166.0), (548.0, -160.0), (520.0, -163.0)]
    LIB.draw_hose(L, [BOAT.to_world(p, t) for p in pts], 9.0)


# ============================================================================= render
def render(f, t, T):
    b = _beats(T)
    cam = camera(t)
    f.set_camera(cam)
    S.sea_world(f, t, moon=MOON, moon_r=MOON_R, dusk=0.0, veil=0.25)
    ms = _moon_screen(f)
    _under_light(f, t)
    st = LIB.bell_state(t, BOAT)
    md = LIB.moon_dir_world(cam, LIB.bell_point(st, (0.0, 80.0)), ms)
    _bell_under(f, t, st)
    _beam(f, t)
    with f.layer() as L:
        BOAT.draw(L, t, pump_angle=150.0 * t, winch_angle=-2.0 * LIB.crank_deg(min(t, T_STOP)), hose=False,
                  hook=False)
        _deck_hose(L, t)
        sk = CLIENT.skeleton(t)
        _knife(L, sk, t)
        F.draw_figure(f, sk, _client_look(t, b), L)
        LIB.draw_hose(L, HOSE.points(t), LIB.HOSE_W)
        DIVER.draw(f, t, L)
        _line(L, t, st)
        _bell_air(L, f, t, st, md)
    S.water_front(f, t, alpha=0.08, bright=BRIGHT)
    BOAT.draw_lights(f, t, lantern=1.0, window=0.5, masthead=1.0)
    _bell_water(f, t, st)
    atmos.bubbles(f, _VALVE, rate=2.6, t=t, seed=33, rise=(240.0, 380.0), size=(1.5, 5.5), spread=8.0,
                  current=12.0, surface=6.0, height=2400.0, alpha=0.8)
    _lamp_head(f, t)
    f.post["vignette"] = lerp(f.post["vignette"], 0.38, 0.6)


def motion_blur(t, T):
    if T_BREAK - 0.1 < t < T_STOP + 0.15:
        return 3
    return 1


def cues(T):
    b = _beats(T)
    return [
        Cue(-0.5, "rising through night water: muffled sub, a heartbeat slowing, the diver's ascent",
            gain_db=-14, dur=2.0),
        Cue(0.2, "on deck: the winch ratchet clacking steadily, pump flywheel chuff, swell slaps on the hull",
            gain_db=-12, pan=-0.3, dur=8.0),
        Cue(b["safe"], "the client draws on his cigar: a soft crackle of the ember", gain_db=-16, pan=-0.35),
        Cue(5.6, "the cranking quickens (eager), the line creaks over the sheave", gain_db=-11, pan=-0.2, dur=2.6),
        Cue(T_BREAK, "something heavy breaks the surface: a deep sucking gulp of water", gain_db=-6, pan=0.25,
            dur=0.9),
        Cue(b["bell"], "water pouring off a great weight: sheets, then dripping", gain_db=-8, pan=0.25, dur=2.4),
        Cue(9.2, "the winch slows, the ratchet clicks spaced out", gain_db=-14, pan=-0.3, dur=0.6),
        Cue(T_STOP, "THE BELL TOLLS (tonic D): first time in thirty years; the winch pawl catches",
            gain_db=-2, pan=0.2, dur=4.0),
        Cue(T_TOLL2, "the bell TOLLS again as it swings back over the stern (slightly softer)", gain_db=-4,
            pan=0.05, dur=3.0),
        Cue(10.95, "the toll's echo rolls out over the water (carry through the hard cut)", gain_db=-10, dur=2.5),
    ]
