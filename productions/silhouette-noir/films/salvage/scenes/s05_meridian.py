"""s05 · THE MERIDIAN: the seabed, the wreck looms (13.5 s).

IN  (ink from s04, 1.25 s centred on the cut): near-black water; the diver sinks the last
    metre, his lamp (the first glow) at screen ~(540, 1010) where s04's black hole was, the
    beam sweeping the silt below him.
Beats (scene-local s):
  0.50        he lands feet-first; silt billows from his boots (knees absorb, settle)
  0.9-1.45    he turns to profile, facing right
  [For@1.40]  L8 begins; he walks right (heavy gait); the beam rakes the silt ahead
  4.15-4.9    the beam lifts off the silt, crosses the dark under the stern and lands on a
              WALL: riveted plates, on [look@4.91]
  4.0-6.4     the camera cranes back and up: the MERIDIAN on her side, colossal; the diver
              tiny at the bottom, his beam a small fan climbing her name; peak on [deep@6.37]
  6.4-9.4     "Too expensive": the beam wanders up the name and across the plates
  9.4-12.6    the camera eases in on the bell hanging from its bracket, swaying
  [convenient@11.56]  the beam drops onto the bell: bronze; the clapper strikes, a dull note
  12.85-13.75 he swings the lamp right along the hull; the camera whips with it
OUT (whip left, 0.5 s): the camera pans right fast (the world streams left), the beam
    leading along the hull's bottom.
"""
import math

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor
from engine.timing import Cue
from films.salvage import cast
from films.salvage import sets as S
from films.salvage.scenes import _lib_s05_s06_s08 as LIB

PAL = S.PAL
INK = PAL.ink
D2R = math.pi / 180.0


def _beats(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:
            return d
    return dict(for_=at("For", 1.4), look=at("look", 4.906), deep=at("deep", 6.369),
                expensive=at("expensive", 8.122), conv=at("convenient", 11.561))


# ============================================================================= the set
WRECK = S.Wreck()
WORLD = S.DeepWorld(wreck=WRECK, reef=False, front=((-2500.0, -1300.0, 1), (1700.0, -2000.0, 2)))
Z_PLATE = -110.0                       # the transom's plane
TRANSOM = WRECK.transom()              # world (x, y, z)

# ============================================================================= the diver
X_LAND = -1150.0
X_STOP = -650.0
T_TD = 0.50                            # touchdown
T_WALK = 1.45
Y_STAND = S.seabed_y(X_LAND + 6.0) - (cast.DIVER.hip - 0.006) * 620.0


def _land_y(t):
    """Pelvis height while sinking onto the silt: ~150 px/s easing to ~70 px/s at touchdown."""
    tau = T_TD - t
    return Y_STAND - (70.0 * tau + 35.0 * tau * tau)


def _land_path(t):
    tau = max(T_TD - t, 0.0)
    return (X_LAND + 6.0 - 26.0 * tau - 6.0 * tau * tau, _land_y(min(t, T_TD)))


def _land_pose(t, u):
    p = F.Pose(0.0, 0.0, 32.0)
    tau = max(T_TD - t, 0.0)
    reach = smoothstep(1.4, 0.0, tau)                  # legs straighten toward the silt
    for s, ph in (("L", 0.0), ("R", 1.7)):
        p.legs[s] = dict(hip=lerp(9 + 4 * math.sin(t * 1.3 + ph), 5.0 + (2.0 if s == "L" else -1.0), reach),
                         abd=4, knee=lerp(18 + 6 * math.sin(t * 1.3 + ph + 0.8), 7.0, reach), ankle=-8, toe=0)
    for s, sg in (("L", 1.0), ("R", -1.0)):
        p.arms[s] = dict(sh=16.0 + 6.0 * sg + 4.0 * noise1(t * 0.4, 3 + sg), abd=24.0 + 4.0 * noise1(t * 0.3, 5 + sg),
                         elbow=32.0, wrist=6.0, grip=0.25)
    p.pitch = 3.0 + 2.0 * noise1(t * 0.3, 7)
    p.spine = [1.0, 0.5, 0.0]
    p.head = 14.0
    p.eyes = dict(open=1.0, glow=1.0, look=0.2)
    return p


def _make_diver():
    A = Actor(cast.DIVER, cast.diver(), x=X_LAND, ground=S.seabed_y, facing=32.0, seed=5, name="diver")
    A.free(T_TD + 2.2, _land_path, _land_pose, at=-2.2, blend=0.3)
    A.stand(until=0.95)
    A.turn(0.0, dur=0.5, via=16.0)
    A.walk(to=X_STOP, gait="heavy", at=T_WALK)
    A.stand(until=16.0)
    # the landing: knees absorb, the body settles forward then recovers
    A.key("y", [(T_TD - 0.02, 0.0), (T_TD + 0.22, 34.0, "out"), (T_TD + 0.85, 0.0, "inout")], mode="add")
    A.key("pitch", [(T_TD - 0.02, 0.0), (T_TD + 0.25, 7.0, "out"), (T_TD + 0.9, 0.0, "inout")], mode="add")
    A.key("arm.L.sh", [(T_TD - 0.05, 0.0), (T_TD + 0.2, 14.0, "out"), (T_TD + 0.9, 0.0, "inout")], mode="add")
    A.key("arm.R.sh", [(T_TD - 0.05, 0.0), (T_TD + 0.2, 10.0, "out"), (T_TD + 0.9, 0.0, "inout")], mode="add")
    # the swing at the end: lean back (anticipation), then turn away along the hull
    A.key("yaw", [(12.70, 0.0), (12.95, 6.0, "inout"), (13.45, -24.0, "inout"), (14.2, -26.0)], mode="add")
    A.key("pitch", [(12.70, 0.0), (12.92, -4.0, "inout"), (13.35, 5.0, "inout"), (14.2, 3.0)], mode="add")
    return A


DIVER = _make_diver()
_XD = LIB.Sampled(lambda t: DIVER.root(t)[0], -2.5, 14.5, 60)
_PEL = LIB.Sampled(lambda t: DIVER.root(t), -2.5, 14.5, 60)


# ============================================================================= aim of the lamp
# The lamp's aim is a world point (x, y, z); the beam's real stop is ray-cast against the
# silt, the transom and (when aimed at it) the bell.
def _silt(x, z=0.0):
    return (x, S.seabed_y(x), z)


NAME_M = (835.0, 7700.0, Z_PLATE)                # just above the "M" (her name runs up the plate)
NAME_MID = (1020.0, 7270.0, Z_PLATE)
NAME_TOP = (1215.0, 6800.0, Z_PLATE)
PLATES = (1520.0, 7050.0, Z_PLATE)
CORNER = (520.0, 8085.0, Z_PLATE)


def _bell_c(t):
    """World centre of the bell's body (x, y, z) this frame."""
    bp = WRECK.bell_pose(t, *_bell_state(t))
    a = math.radians(bp["angle"])
    s = WRECK.BELL_SCALE
    cx, cy, cz = bp["crown"]
    return (cx - math.sin(a) * 90.0 * s, cy + math.cos(a) * 90.0 * s, cz)


def _lerp3(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u))


def _aim(t):
    """(kind, world point): where the lamp points. kind: 'free' or 'bell'."""
    xd = _XD(t)
    nz = 22.0 * noise1(t * 0.55, 31)
    if t < T_WALK:
        # sweeping the silt as he sinks; looking down at his landing; then ahead
        x = xd + LIB.track([(-1.2, -420.0), (-0.35, -260.0, "inout"), (T_TD + 0.05, 190.0, "inout"),
                            (T_TD + 0.5, 210.0, "inout"), (T_WALK, 400.0, "inout")], t) \
            + nz * smoothstep(T_TD + 0.4, T_WALK, t)
        return "free", _silt(x)
    if t < 4.15:
        x = xd + lerp(380.0, 600.0, smoothstep(T_WALK, 4.15, t)) + nz
        return "free", _silt(x)
    if t < 4.9:
        a = _silt(_XD(4.15) + 600.0)
        u = ease("inout", (t - 4.15) / 0.75)
        return "free", _lerp3(a, NAME_M, u)
    if t < 7.4:
        u = ease("inout", (t - 4.9) / 2.5)
        p = _lerp3(NAME_M, NAME_MID, u)
        return "free", (p[0] + 0.5 * nz, p[1] + nz, p[2])
    if t < 9.3:
        u = ease("inout", (t - 7.4) / 1.9)
        p = _lerp3(NAME_MID, NAME_TOP, u) if u < 1 else NAME_TOP
        return "free", (p[0] + 0.5 * nz, p[1] + nz, p[2])
    if t < 10.5:
        u = ease("inout", (t - 9.3) / 1.2)
        p = _lerp3(NAME_TOP, PLATES, u)
        return "free", (p[0], p[1] + nz, p[2])
    if t < 11.0:
        u = ease("inout", (t - 10.5) / 0.5)
        return "free", _lerp3(PLATES, CORNER, u)
    b = _bell_c(t)
    if t < 11.56:
        u = ease("inout", (t - 11.0) / 0.56)
        return "bell", _lerp3(CORNER, b, u)
    if t < 12.85:
        return "bell", (b[0] + 6.0 * noise1(t * 0.9, 5), b[1] + 6.0 * noise1(t * 0.8, 6), b[2])
    # the swing right along the hull (leads the whip)
    u = (t - 12.85) / 0.9
    e = clamp(u) ** 2.2
    p0 = (b[0], b[1], b[2])
    p1 = (700.0, 8120.0, Z_PLATE)
    p2 = (4200.0, 7600.0, Z_PLATE)
    if e < 0.25:
        return "free", _lerp3(p0, p1, e / 0.25)
    return "free", _lerp3(p1, p2, min((e - 0.25) / 0.75, 1.6))


def _look_target(t):
    k, p = _aim(t)
    return (p[0], p[1])


DIVER.look_at(-3.0, 15.0, _look_target, fade=0.05)

_LAMP = LIB.Sampled(lambda t: costume.helmet_lamp(DIVER.skeleton(t))[0], -2.5, 14.5, 60)
_INLET = LIB.Sampled(lambda t: costume.helmet_inlet(DIVER.skeleton(t)), -2.5, 14.5, 120)
_VALVE = LIB.Sampled(lambda t: LIB.helmet_valve(DIVER.skeleton(t)), -2.5, 14.5, 60)
_CHEST = LIB.Sampled(lambda t: DIVER.skeleton(t).j["chest"], -2.5, 14.5, 60)

LIB.ACTORS["s05"] = (DIVER, S.seabed_y)


# ============================================================================= the bell
def _bell_state(t, b=None):
    """(bell_angle, clapper): the slow sway in the current; on [convenient] the clapper
    swings across and strikes the lip (a dull note), the bell rocks after it."""
    conv = 11.561 if b is None else b
    ang, cl = S.bell_swing(t, seed=1, amp=6.0, period=5.4)
    k = t - (conv - 0.45)
    if k > 0.0:
        # a slow push of the current, the clapper lags, strikes at `conv`, bounces off
        ang += 3.5 * math.sin(math.pi * clamp(k / 1.3)) * math.exp(-0.25 * k)
        s = t - conv
        if s < 0.0:
            cl += -25.0 * ease("in", clamp((t - (conv - 0.45)) / 0.45))
        else:
            cl += -25.0 * math.exp(-2.4 * s) * math.cos(9.0 * s)
            ang += 2.0 * math.exp(-1.2 * s) * math.sin(4.2 * s)
    return ang, cl


# ============================================================================= camera
def _follow_x(t):
    return sum(_XD(t - 0.08 * i) for i in range(8)) / 8.0


Z_OPEN = 0.9
LN = math.log


def _open_cam(t):
    """Locked on his sinking body: the lamp near screen (540, 1010)."""
    px, py = _PEL(min(t, T_TD + 0.3))
    return (px + 18.0, py - 236.0, LN(Z_OPEN))


WIDE = (250.0, 7250.0, LN(0.30))
BELLSHOT = (-312.0, 8250.0, LN(0.62))


WALL = (120.0, 8130.0, LN(0.56))        # [look]: the plates fill the upper right


def _cam_keys(t):
    # follow while he walks
    zf = LN(Z_OPEN) + (LN(0.80) - LN(Z_OPEN)) * ease("inout", (t - 1.0) / 3.0)
    xf = _follow_x(t) + 160.0
    yf = lerp(_open_cam(T_TD + 0.3)[1], 9066.0 - 650.0 / math.exp(zf), smoothstep(0.8, 3.8, t))
    if t < 3.6:
        return (xf, yf, zf)
    a = (xf, yf, zf)
    # pan right with the lifting beam, easing back: the wall
    u = ease("inout", (t - 3.6) / 1.45)
    wl = (lerp(a[0], WALL[0], u), lerp(a[1], WALL[1], u), lerp(a[2], WALL[2], u))
    if t < 4.75:
        return wl
    # crane back and up: the reveal, peaking on [deep]
    u = ease("inout", (t - 4.75) / 1.7)
    return_w = (lerp(wl[0], WIDE[0], u), lerp(wl[1], WIDE[1], u), lerp(wl[2], WIDE[2], u))
    if t < 6.45:
        return return_w
    drift = (WIDE[0] - 45.0 * smoothstep(6.45, 9.4, t), WIDE[1] + 40.0 * smoothstep(6.45, 9.4, t),
             WIDE[2] + 0.05 * smoothstep(6.45, 9.4, t))
    if t < 9.4:
        return drift
    u = ease("inout", (t - 9.4) / 3.2)
    c = (lerp(drift[0], BELLSHOT[0], u), lerp(drift[1], BELLSHOT[1], u), lerp(drift[2], BELLSHOT[2], u))
    if t < 12.85:
        return c
    w = (t - 12.85) / 0.9
    return (c[0] + 3000.0 * clamp(w, 0, 1.4) ** 2.6, c[1] - 120.0 * clamp(w, 0, 1.4) ** 2, c[2] + 0.08 * clamp(w, 0, 1.4))


def _cam(t):
    k = _cam_keys(t)
    w = smoothstep(-0.1, 1.5, t)
    if w < 1.0:
        o = _open_cam(t)
        k = (lerp(o[0], k[0], w), lerp(o[1], k[1], w), lerp(o[2], k[2], w))
    return Camera(k[0], k[1], math.exp(k[2]))


def _vp(t, cam):
    """Vanishing point (screen): the eye level near the frame centre in the close shots; low
    for the reveal (a rising-front lens: she towers)."""
    k = smoothstep(3.9, 6.4, t) * (1.0 - 0.45 * smoothstep(9.4, 12.6, t))
    return (540.0, lerp(1000.0, 1150.0, k))


# ============================================================================= light
def _murk(t):
    m = lerp(0.93, 0.80, smoothstep(0.5, 3.6, t))
    return lerp(m, 0.30, smoothstep(3.9, 6.4, t)) + 0.08 * smoothstep(9.4, 12.6, t)


def _dark(t):
    return 0.72 * (1.0 - smoothstep(3.7, 6.2, t)) * (1.0 - 0.2 * smoothstep(0.6, 3.5, t))


def _glow(t):
    k = smoothstep(3.9, 6.4, t) * (1.0 - 0.25 * smoothstep(9.4, 12.6, t))
    g = [(540.0, -60.0, 900.0, 0.16 * (1.0 - k) * smoothstep(-0.6, 2.5, t))]
    if k > 0.0:
        g += [(300.0, 560.0, 1250.0, 1.3 * k), (250.0, 1450.0, 520.0, 0.7 * k)]
    return g


HALF = 12.0                                       # the cone's half angle


def _beam(f, t, view):
    """Ray-cast the lamp's axis against the silt, the transom and the bell; draw the cone,
    its pool and what the pool reveals. Returns (cone, pool point or None)."""
    lamp = _LAMP(t)
    kind, aim = _aim(t)
    tgt = view.Pp(aim) if aim[2] != 0.0 else (aim[0], aim[1])
    d = LIB.unit(tgt[0] - lamp[0], tgt[1] - lamp[1])
    hits = []
    g = LIB.ray_ground(lamp, d, S.seabed_y, smax=4200.0)
    if g is not None:
        hits.append((g[0], "silt", g[1]))
    poly = [view.Pp(p) for p in TRANSOM]
    if kind != "bell" and LIB.inside(tgt, poly):
        hits.append((math.hypot(tgt[0] - lamp[0], tgt[1] - lamp[1]), "wall", tgt))
    else:
        h = LIB.ray_poly(lamp, d, poly)
        if h is not None:
            hits.append((h[0], "wall", h[1]))
    b = None
    if kind == "bell":
        b = WRECK.bell_screen(view, t, *_bell_state(t))
        bc = view.Pp(_bell_c(t))
        r = 62.0 * b["s"]
        # ray vs the bell's body (a disc)
        ox, oy = lamp[0] - bc[0], lamp[1] - bc[1]
        bq = ox * d[0] + oy * d[1]
        cq = ox * ox + oy * oy - r * r
        disc = bq * bq - cq
        if disc >= 0.0:
            s = -bq - math.sqrt(disc)
            if s > 0.0:
                hits.append((s, "bell", (lamp[0] + d[0] * s, lamp[1] + d[1] * s)))
    hits.sort(key=lambda h: h[0])
    on = _lamp_power(t)
    if not hits:
        cone = LIB.lamp_beam(f, t, lamp, (lamp[0] + d[0] * 2600.0, lamp[1] + d[1] * 2600.0), stop=None,
                             half=HALF, intensity=0.66 * on, reach=2600.0, dust=0.45, seed=5)
        return cone, None, b
    s, what, p = hits[0]
    if what == "silt":
        cone = LIB.lamp_beam(f, t, lamp, p, stop=LIB.surface_line(S.seabed_y, p[0], 400.0), half=HALF,
                             intensity=0.66 * on, pool=1.0 * on, squash=0.42, dust=0.45, seed=5)
        if cone.hit is not None:
            hx, hy, dist, cosi = cone.hit
            rx = dist * cone.tanh / max(cosi, 0.25)
            LIB.silt_detail(f, t, (hx, hy), rx * 1.1, rx * 0.42 * 1.1, on * min(1.0, 600.0 / max(dist, 1.0)),
                            S.seabed_y, seed=3)
    elif what == "wall":
        cone = LIB.lamp_beam(f, t, lamp, p, stop="perp", half=HALF, intensity=0.68 * on, pool=0.75 * on,
                             squash=1.35, dust=0.45, seed=5)
        r = max(s * math.tan(HALF * D2R) * 2.1, 90.0)
        fall = clamp(1.0 - s / 3600.0) ** 0.7 * on
        LIB.transom_lit(f, view, WRECK, p, r, fall)
    else:
        cone = LIB.lamp_beam(f, t, lamp, p, stop="perp", half=HALF, intensity=0.62 * on, pool=0.35 * on,
                             squash=1.0, dust=0.45, seed=5)
    return cone, (what, p, s), b


def _lamp_power(t):
    """The lamp's output (a hint of a brown-out as he lands, a tiny flicker)."""
    return 1.0 - 0.10 * math.exp(-((t - T_TD - 0.05) / 0.06) ** 2) + 0.025 * noise1(t * 7.0, 99)


# ============================================================================= the hose
def _hose_top(t):
    return (_XD(t) + 160.0, 2600.0)


def _hose_len(t):
    a = _hose_top(t)
    b = _INLET(t)
    return math.hypot(b[0] - a[0], b[1] - a[1]) + 260.0


HOSE = LIB.hose_rope(_hose_top, _INLET, 6400.0, n=64, t0=-3.0, t1=14.4, length_fn=_hose_len,
                     current=lambda t, x, y: (30.0 + 12.0 * math.sin(0.37 * t + y / 900.0), 0.0), iters=12)


# ============================================================================= silt
def _puffs():
    out = [(X_LAND - 10.0, S.seabed_y(X_LAND - 10.0), T_TD + 0.02, 2.2, 11),
           (X_LAND + 30.0, S.seabed_y(X_LAND + 30.0), T_TD + 0.06, 1.8, 12)]
    for i, (tf, x, s) in enumerate(LIB.footfalls("s05", 0.6, 14.0)):
        out.append((x, S.seabed_y(x), tf, 1.0, 40 + i))
    return out


_PUFFS = None


def _light_at_fn(t, lamp, pool):
    def fn(x, y):
        k = 0.30 * math.exp(-((x - lamp[0]) ** 2 + (y - lamp[1]) ** 2) / (700.0 ** 2))
        if pool is not None and pool[0] == "silt":
            px, py = pool[1]
            k += 0.9 * math.exp(-((x - px) ** 2 + (y - py) ** 2) / (420.0 ** 2))
        return min(k, 1.0)
    return fn


# ============================================================================= render
def render(f, t, T):
    global _PUFFS
    b = _beats(T)
    cam = _cam(t)
    f.set_camera(cam)
    murk = _murk(t)
    S.deep_backdrop(f, t, glow=_glow(t), murk=murk)
    view = S.View(f, murk=murk, vp=_vp(t, cam))
    wk = dict(bell_angle=_bell_state(t)[0], clapper=_bell_state(t)[1])
    WORLD.draw(f, t, view=view, wreck_kw=wk)
    # the dark: near-black water until the reveal opens it up
    f.darken(_dark(t), screen=True)
    LIB.far_rays(f, t, 0.10 + 0.12 * smoothstep(3.9, 6.4, t))
    lamp = _LAMP(t)
    # warm spill of the lamp in the water around him (backlights his silhouette)
    with f.light(blur=40) as A:
        draw.glow_disc(A, (lamp[0] + 40.0, lamp[1] + 90.0), 380.0, PAL.light, 0.075)
        draw.glow_disc(A, (lamp[0] + 10.0, lamp[1] + 30.0), 150.0, PAL.light, 0.09)
    cone, pool, bs = _beam(f, t, view)
    if bs is not None and pool is not None and pool[0] == "bell":
        LIB.bell_lit(f, bs, lamp, _lamp_power(t) * smoothstep(11.42, 11.6, t), S.draw_bell)
    # a cool backlight from the far haze behind him (keeps his silhouette reading in the dark)
    ch = cam.to_screen(_CHEST(t))
    LIB.screen_glow(f, (ch[0], ch[1] - 40.0), 560.0 * cam.zoom / 0.9, PAL.surface, 0.10 * (1.0 - smoothstep(4.0, 6.0, t)))
    with f.layer() as L:
        LIB.draw_hose(L, HOSE.points(t), LIB.HOSE_W)
        DIVER.draw(f, t, L)
    if _PUFFS is None:
        _PUFFS = _puffs()
    LIB.silt_puffs(f, t, _PUFFS, _light_at_fn(t, lamp, pool))
    atmos.lamp(f, lamp, radius=9.0, intensity=0.95 * _lamp_power(t), halo=4.5, core=0.3, t=t, seed=6)
    # breath
    atmos.breathing(f, _VALVE, period=4.2, phase=-1.4, n=16, t=t, seed=31, size=(1.6, 9.0), rise=(260.0, 420.0),
                    spread=40.0, current=18.0, height=1500.0, alpha=0.6, lit=cone)
    atmos.bubbles(f, _VALVE, rate=2.0, t=t, seed=33, rise=(240.0, 380.0), size=(1.4, 4.5), spread=8.0,
                  current=18.0, height=1200.0, alpha=0.5, lit=cone)
    atmos.marine_snow(f, density=0.85, t=t, seed=6, sink=8.0, current=(9.0, 0.0), alpha=0.8, lit=cone)
    WORLD.draw_front(f, t, view, wreck_kw=wk)
    f.post["vignette"] = lerp(f.post["vignette"], 0.5, 0.8)


def motion_blur(t, T):
    if t > 12.95:
        return 4
    return 1


def cues(T):
    b = _beats(T)
    return [
        Cue(-0.3, "deep water: low drone, the free-flow hiss of his helmet", gain_db=-14, dur=2.5),
        Cue(T_TD, "boots land in the silt: a soft heavy thud, silt hiss", gain_db=-8),
        Cue(T_WALK + 0.35, "heavy boot steps in silt (slow, muffled), brass gear creak", gain_db=-12, dur=3.0),
        Cue(4.15, "the lamp lifts: low swell", gain_db=-14, dur=0.8),
        Cue(b["look"], "the beam hits steel: a deep metallic groan of the hull", gain_db=-9, dur=2.0),
        Cue(b["deep"], "the reveal: sub swell, the wreck's mass", gain_db=-8, dur=2.4),
        Cue(9.6, "the bell's chain creaks in the current", gain_db=-16, dur=1.6),
        Cue(b["conv"], "a dull, muffled ship's bell note underwater (tonic D)", gain_db=-6, dur=3.5),
        Cue(13.05, "whip: a rush of water as he swings the lamp", gain_db=-10, dur=0.7),
    ]
