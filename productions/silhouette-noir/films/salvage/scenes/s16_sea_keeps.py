"""s16 · THE SEA KEEPS: the severed red hose and the client's fedora sink through moonlit
water to the wreck; the hat settles in the silt under the empty bell bracket, the hose lays
itself out straight along the seabed, the camera tilts down onto it and the frame flattens back
into the Bass red line on black, which slides out of frame left (16.0 s; the end of the film).

IN  (dip from black, 2.0 s centred on the cut; visible from ~0.12, full at 1.0): night water,
    moonlit rays from the top; the fedora (black, turning slowly, ~135 px wide) at screen
    (620, 780); the hose's brass coupling end at ~(330, 315), the hose snaking up and out of
    the top of the frame.

Beats (scene-local s):
  0-5.5      tracking them down (zoom 1.0 -> 0.84): the hat glides like a falling leaf, rocking
             and turning, air bubbling out of its crown (to 3.4); the hose snakes beside it
  [everything@2.87]  the moonlit rays thin out (to ~30 %; they still reach down)
  5.5-8.4    the camera cranes down and back (zoom 0.55): looking down on the wreck, which
             looms out of the murk below on [back@6.11] (fades in 6.1-7.6); the horizon sinks
             to the silt as we arrive at eye level
  8.4-12.6   the bottom: a slow push (0.55 -> 0.85); a pale pool of moonlight in the water
             behind the landing spot; the hat (moonlit rim) sinks past the EMPTY bell bracket
             (upper right) and lands in the silt on [revenge@10.98] at screen (700, 1440), with
             a puff of silt
  10.25      the hose's coupling touches down at the left (puff) and is drawn off left along
             the silt; the hose lies down and straightens, its free end curling by the hat
  12.6-13.84 the camera tilts down onto the hose (the horizon rises out of the top of the
             frame) and pushes in to zoom 1.4: the hose 14 px thick at screen y 960;
             13.25-13.7 it straightens into the s01 band; 13.3-13.7 the frame posterizes
             3 -> 2 -> 1 inks (keep red): the red line on black paper
  [me@13.84] the line slides out of frame left (in3, 0.86 s): the mirror of s01's draw-on
  14.7-16.0  black paper, fading to pure ink by 15.2 (black held the final 0.8 s)
"""
import math

import numpy as np

from engine import atmos, draw
from engine.core import H, W, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.palette import RED
from engine.timing import Cue
from films.salvage import sets as S
from films.salvage.scenes import _lib_s01_s03_s16 as LIB

PAL = S.PAL
INK = PAL.ink
D2R = math.pi / 180.0


def _beats(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:
            return d
    return dict(every=at("everything", 2.866), back=at("back", 6.105), justice=at("Justice", 8.6),
                revenge=at("revenge", 10.98), you=at("You", 13.244), me=at("me", 13.836))


# ============================================================================= the seabed
_SBX = np.arange(-6000.0, 4000.0, 8.0)
_SBY = np.array([S.seabed_y(float(x), 0.0) for x in _SBX])
SB_TOP = float(_SBY.min())


def silt(x):
    """Seabed height at the action plane (cached table of sets_deep.seabed_y)."""
    return float(np.interp(x, _SBX, _SBY))


# ============================================================================= the fedora
HAT_SIZE = 100.0                # head-height units (the client's is ~86 at zoom 1: a touch larger reads better)
X_LAND = -170.0                 # lands in the silt under the empty bell bracket (0, 7925)
T_HAT = 10.98                   # ... on 'revenge'
V_HAT = 300.0                   # sink speed (px/s)
Y_LAND = silt(X_LAND) - 0.06 * HAT_SIZE      # the brim's underside on the silt


def hat(t):
    """(centre of the brim (x, y), yaw, tilt) of the sinking fedora."""
    if t < T_HAT:
        tau = T_HAT - t
        w = 1.0 - math.exp(-tau / 0.9)                   # the leaf-glide fades as it slows down
        y = Y_LAND - V_HAT * tau + 30.0 * (1.0 - math.exp(-tau / 0.5))
        om = 1.35
        x = X_LAND - 105.0 * tau + 140.0 * math.sin(om * t + 0.4) * w
        tilt = -24.0 * math.cos(om * t + 0.4) * w + 4.0 * noise1(t * 0.5, 3)
        yaw = 25.0 + 23.0 * t
        return (x, y), yaw, tilt
    tau = t - T_HAT
    tilt_end = 7.0
    tilt0 = 4.0 * noise1(T_HAT * 0.5, 3)
    tilt = tilt_end + (tilt0 - tilt_end) * math.exp(-5.0 * tau) * math.cos(9.0 * tau)
    yaw = 25.0 + 23.0 * T_HAT + 23.0 * (1.0 - math.exp(-3.0 * tau)) / 3.0
    sink = 2.5 * (1.0 - math.exp(-4.0 * tau))           # it beds into the silt
    return (X_LAND, Y_LAND + sink - 12.0 * math.exp(-6.0 * tau) * math.sin(8.0 * tau)), yaw, tilt


def _hat_src(te):
    """Air leaking from under the crown in the first seconds."""
    (x, y), yaw, tilt = hat(te)
    return (x + 4.0, y - 0.55 * HAT_SIZE)


# ============================================================================= the hose
HOSE_L = 1500.0
T_TD = 10.25                    # its heavy cut end touches down
X_TD = -900.0


def _hose_a(t):
    """The heavy end (brass coupling) leading the hose down; then dragged along the silt."""
    if t < T_TD:
        tau = T_TD - t
        y = silt(X_TD) - 6.0 - 370.0 * tau + 40.0 * (1.0 - math.exp(-tau / 0.6))
        beside = X_LAND - 105.0 * (T_HAT - t) - 330.0          # ~330 px left of the hat's mean path
        x = lerp(beside, X_TD, smoothstep(6.0, T_TD, t))
        x += 100.0 * math.sin(1.05 * t + 1.3) * (1.0 - math.exp(-tau / 1.2))
        return (x, y)
    tau = t - T_TD
    x = X_TD - 700.0 * (1.0 - math.exp(-tau / 1.5)) - 30.0 * tau
    return (x, silt(x) - 6.0)


def _hose_current(t, x, y):
    return (46.0 + 16.0 * math.sin(0.33 * t + y / 800.0), 0.0)


def _collide(x, y):
    if y < SB_TOP - 40.0:
        return None
    return silt(x) - 6.0


def _hose_init(t0):
    ax, ay = _hose_a(t0)
    n = 44
    seg = HOSE_L / (n - 1)
    pts = []
    for i in range(n):
        u = i / (n - 1)
        ang = (-22.0 + 38.0 * math.sin(5.0 * u + 0.3)) * D2R
        if i == 0:
            pts.append((ax, ay))
        else:
            px, py = pts[-1]
            pts.append((px + seg * math.cos(ang), py + seg * math.sin(ang)))
    return pts


HOSE = LIB.hose_rope(_hose_a, None, HOSE_L, n=44, t0=-4.0, t1=16.0, current=_hose_current, collide=_collide,
                     init=_hose_init, gravity=(0.0, 600.0), drag=1.8, stiffness=0.3, iters=10)


# ============================================================================= camera
Z_TRACK = (1.0, 0.84)           # close on the hat while they sink (0 .. 5.5)
Z_BOT = (0.55, 0.85)            # the bottom framing: eye level with the silt, a slow push (T_BOT .. T_TILT0)
Z_END = 1.4                     # on the hose at the end: 14 px thick
T_BOT = 8.4
T_TILT0, T_TILT1 = 12.6, 13.84
LAND_S = (700.0, 1440.0)        # the hat's landing spot on screen in the bottom framing
X_HOSE_C = -800.0               # the hose's straight run, framed at the end
VP_HIGH, VP_EYE, VP_END = 250.0, 1600.0, -3000.0    # the horizon: looking down / eye level / tilted down


def _logz(a, b, u):
    return math.exp(lerp(math.log(a), math.log(b), u))


def _track(t):
    (hx, hy), _, _ = hat(t)
    z = _logz(Z_TRACK[0], Z_TRACK[1], smoothstep(0.0, 5.5, t))
    sx = lerp(620.0, 600.0, smoothstep(0.0, 5.0, t))
    sy = lerp(780.0, 620.0, smoothstep(0.0, 5.5, t))
    return hx - (sx - W / 2) / z, hy - (sy - H / 2) / z, z


def _bottom(t):
    z = _logz(Z_BOT[0], Z_BOT[1], ease("inout", (t - T_BOT) / (T_TILT0 - T_BOT)))
    sx, sy = LAND_S
    return X_LAND - (sx - W / 2) / z, Y_LAND - (sy - H / 2) / z, z


def _tilt_k(t):
    return ease("inout", (t - T_TILT0) / (T_TILT1 - T_TILT0))


def _cam3(t):
    """(x, y, zoom): track the hat; crane down to the bottom framing; tilt down onto the hose."""
    w = ease("inout", (t - 5.5) / (T_BOT - 5.5))
    if w <= 0.0:
        return _track(t)
    xb, yb, zb = _bottom(t)
    if w < 1.0:
        xt, yt, zt = _track(t)
        z = _logz(zt, zb, w)
        # blend the screen position of the landing spot, so the move reads as one crane
        st = ((X_LAND - xt) * zt + W / 2, (Y_LAND - yt) * zt + H / 2)
        sb = ((X_LAND - xb) * zb + W / 2, (Y_LAND - yb) * zb + H / 2)
        sx, sy = lerp(st[0], sb[0], w), lerp(st[1], sb[1], w)
        return X_LAND - (sx - W / 2) / z, Y_LAND - (sy - H / 2) / z, z
    k = _tilt_k(t)
    if k <= 0.0:
        return xb, yb, zb
    ax, ay = X_HOSE_C, silt(X_HOSE_C) - 6.0
    s0 = ((ax - xb) * zb + W / 2, (ay - yb) * zb + H / 2)
    z = _logz(zb, Z_END, k)
    sx, sy = lerp(s0[0], W / 2, k), lerp(s0[1], LINE_Y, k)
    return ax - (sx - W / 2) / z, ay - (sy - H / 2) / z, z


def camera(t):
    x, y, z = _cam3(t)
    return Camera(x, y, z)


def _vp_y(t):
    """Screen y of the horizon: high while we look down on the wreck, at the silt as we settle,
    above the frame as the camera tilts down onto the hose."""
    y = lerp(VP_HIGH, VP_EYE, ease("inout", (t - 6.0) / 2.6))
    return lerp(y, VP_END, _tilt_k(t))


# ============================================================================= world
WRECK = S.Wreck()
WORLD = S.DeepWorld(wreck=WRECK, reef=False, debris=True, front=())


def _world_a(t, b):
    return smoothstep(b["back"], b["back"] + 1.5, t)


def _view(f, t):
    eye = smoothstep(6.0, T_BOT, t)
    # no down-fog while the horizon races up in the tilt (it would brighten the near silt band by band)
    down = lerp(1.6, 0.9, eye) * (1.0 - smoothstep(12.5, 13.0, t))
    return S.View(f, murk=lerp(0.35, 0.5, eye), down_fog=down, vp=(W / 2, _vp_y(t)))


def _backdrop(f, t, b):
    rays = _rays(t, b)
    S.deep_backdrop(f, t, glow=[(560.0, 160.0, 1250.0, 0.55 + 0.45 * rays), (520.0, 900.0, 700.0, 0.25)],
                    murk=0.42 + 0.2 * smoothstep(4.0, 9.0, t))


def _rays(t, b):
    return 1.0 - 0.72 * smoothstep(b["every"], b["every"] + 1.7, t)        # thinned, never quite gone


def _moonlight(f, t, b):
    """The moonlit rays reaching down (over the wreck: light in the water in front of it), and
    a pale pool of it behind the hat's landing spot, so the black hat reads on the seabed."""
    cam = f.cam
    top = cam.y - H / 2 / cam.zoom
    atmos.underwater_rays(f, surface_y=top - 400.0, t=t, spacing=210.0, angle=94.0, fan=9.0,
                          length=3600.0, intensity=0.5 * _rays(t, b) * (1.0 - smoothstep(12.5, 13.1, t)),
                          color=S.mix(PAL.moon, PAL.surface, 0.4),
                          density=0.6, seed=12, blur=18)
    a = smoothstep(7.0, 9.5, t) * (1.0 - smoothstep(12.5, 13.1, t))
    if a > 0.0:
        col = S.mix(PAL.moon, PAL.surface, 0.55)
        with f.light(blur=40) as A:
            draw.glow_disc(A, (X_LAND + 10.0, Y_LAND - 230.0), 520.0, col, 0.16 * a)
            draw.glow_disc(A, (X_LAND + 10.0, Y_LAND - 120.0), 260.0, col, 0.12 * a)


def _world(f, t, b):
    a = _world_a(t, b)
    if a <= 0.0:
        return None
    view = _view(f, t)
    c = f.ctx
    c.push_group()
    WORLD.draw(f, t, view, wreck_kw=dict(bell=False))
    c.pop_group_to_source()
    c.paint_with_alpha(a)
    return view


def _puff(f, t, x, y, t0, scale, seed):
    """A soft cloud of silt kicked up where something settles."""
    tau = t - t0
    if tau < 0.0 or tau > 3.2:
        return
    a = smoothstep(0.0, 0.15, tau) * (1.0 - smoothstep(0.6, 3.2, tau)) * (1.0 - smoothstep(12.3, 12.9, t))
    col = S.mix(PAL.surface, PAL.fog_at(0.5), 0.5)
    with f.light(blur=14) as A:
        for i in range(7):
            ang = math.pi * (0.1 + 0.8 * hash01(seed, i, 1))
            d = scale * (30.0 + 120.0 * hash01(seed, i, 2)) * ease("out", tau / 1.4)
            r = scale * (40.0 + 50.0 * hash01(seed, i, 3)) * (0.5 + 0.6 * ease("out", tau / 1.8))
            px = x + math.cos(ang) * d * (1.0 if hash01(seed, i, 4) < 0.5 else -1.0)
            py = y - math.sin(ang) * d * 0.45 - 20.0 * scale * tau
            draw.glow_disc(A, (px, py), r, col, 0.16 * a)


# ============================================================================= the hose line
def _hose_screen(f, t):
    """The hose's points in screen space (for the morph into the Bass line)."""
    cam = f.cam
    return [cam.to_screen(p) for p in HOSE.points(t)]


def _draw_hose(f, t, k_line):
    """The rope (world) and, as k_line -> 1, its morph into the straight s01 band at y 960."""
    if k_line <= 0.0:
        with f.layer() as L:
            pts = HOSE.points(t)
            LIB.draw_hose(L, pts, LIB.HOSE_W)
            ax, ay = pts[0]
            bx, by = pts[1]
            ang = math.atan2(by - ay, bx - ax)
            L.save()
            L.translate(ax, ay)
            L.rotate(ang)
            draw.capsule(L, (-6.0, 0.0), (16.0, 0.0), 8.0, 8.0)       # the brass coupling
            L.set_source_rgb(*INK)
            L.fill()
            L.restore()
        return
    sp = _hose_screen(f, t)
    width = lerp(LIB.HOSE_W * f.cam.zoom, LINE_W, k_line)
    pts = [(x, lerp(y, LINE_Y, k_line)) for x, y in sp]
    # the far end (rising out of the frame) is folded onto the line too: extend it right
    if pts[-1][0] < W + 300:
        pts.append((W + 400.0, LINE_Y))
    if pts[0][0] > -300:
        pts.insert(0, (-400.0, LINE_Y))
    with f.screen() as Sc:
        LIB.draw_hose(Sc, pts, width)


# ============================================================================= the Bass ending
LINE_Y = 960.0
LINE_W = 14.0


def _band(f, t, b):
    """The s01 red line, its right end retreating out of frame left on [me]."""
    k = ease("in3", (t - b["me"]) / 0.86)
    if k >= 1.0:
        return
    xe = lerp(W + 220.0, -220.0, k)
    with f.screen() as Sc:
        Sc.save()
        Sc.new_path()
        draw.poly(Sc, [(-400, LINE_Y - 80), (xe - 9, LINE_Y - 80), (xe + 9, LINE_Y + 80), (-400, LINE_Y + 80)])
        Sc.clip()
        polys = LIB.line_band_pts((540.0, LINE_Y), 2.0 * math.pi * 230.0, LINE_W, 0.0, seed=7)
        LIB.fill_polys(Sc, polys, RED)
        Sc.restore()


def _poster(f, t):
    """Stepped Bass flatten: 3 inks, 2 inks, then ink only (reds always survive)."""
    if t < 13.3:
        return
    mid = S.mix(INK, PAL.surface, 0.22)
    if t < 13.5:
        lv = [(0.045, INK), (0.16, mid), (99.0, S.mix(INK, PAL.surface, 0.5))]
    elif t < 13.7:
        lv = [(0.07, INK), (99.0, mid)]
    else:
        lv = [(99.0, INK)]
    f.post["poster"] = dict(amount=1.0, levels=lv, keep_red=True)


# ============================================================================= render
def render(f, t, T):
    b = _beats(T)
    cam = camera(t)
    f.set_camera(cam)
    k_line = smoothstep(13.25, 13.7, t)
    if t < 13.7:
        _backdrop(f, t, b)
        view = _world(f, t, b)
        _moonlight(f, t, b)
        # the hat and its first bubbles, the snow, the hose
        (hx, hy), yaw, tilt = hat(t)
        with f.layer() as L:
            rim = (0.3 + 0.4 * smoothstep(7.0, 9.5, t)) * (1.0 - _tilt_k(t))
            if rim > 0.0:       # moonlight catching the crown and the brim from above
                LIB.draw_fedora(L, (hx, hy - 2.6 / cam.zoom), HAT_SIZE, yaw, tilt,
                                color=S.mix(PAL.moon, PAL.surface, 0.5), alpha=rim)
            LIB.draw_fedora(L, (hx, hy), HAT_SIZE, yaw, tilt, color=INK)
        atmos.bubbles(f, _hat_src, rate=2.2, t=t, seed=21, rise=(160.0, 260.0), size=(1.4, 5.0), spread=10.0,
                      current=20.0, height=2200.0, alpha=0.8, t_end=3.4)
        _puff(f, t, X_LAND, Y_LAND, T_HAT, 1.0, 3)
        _puff(f, t, _hose_a(T_TD + 0.05)[0], silt(_hose_a(T_TD + 0.05)[0]), T_TD, 0.7, 4)
        _draw_hose(f, t, k_line)
        snow = 1.0 - smoothstep(12.8, 13.4, t)
        if snow > 0.0:
            atmos.marine_snow(f, density=0.9 * snow, t=t, seed=16, sink=8.0, current=(-7.0, 0.0), alpha=0.75)
        f.post["vignette"] = lerp(f.post["vignette"], 0.45, smoothstep(6.0, 9.0, t))
    else:
        f.fill(INK)
        if t < b["me"] + 0.9:
            _band(f, t, b)
    _poster(f, t)
    # Bass paper toward the end, then pure black for the last 0.8 s
    LIB.post_blend(f, smoothstep(13.3, 13.84, t))
    if t > 14.6:
        f.post["paper"] = lerp(f.post["paper"], 0.0, smoothstep(14.6, 15.2, t))
        f.post["grain"] = lerp(f.post["grain"], 0.0, smoothstep(14.6, 15.2, t))


def motion_blur(t, T):
    b = _beats(T)
    if b["me"] < t < b["me"] + 0.9:
        return 3
    return 1


def cues(T):
    b = _beats(T)
    return [
        Cue(-1.0, "deep night-water ambience fades up under the bell's lingering toll", gain_db=-10, dur=3.0),
        Cue(0.3, "the severed hose drifting: slow rubbery creaks, a few bubbles from the hat", gain_db=-16,
            pan=-0.3, dur=6.0),
        Cue(b["every"], "the high shimmer of the moonlit rays thins away", gain_db=-16, dur=1.8),
        Cue(b["back"], "a long low groan of steel: the wreck looms far below", gain_db=-10, pan=0.4, dur=3.0),
        Cue(T_TD, "the hose's brass coupling touches the silt; the hose drags along the seabed", gain_db=-14,
            pan=-0.3, dur=2.6),
        Cue(T_HAT, "the fedora settles in the silt: a soft thud and a hiss of sediment", gain_db=-9, pan=0.1),
        Cue(13.3, "the world goes dry: the water drops out to paper-room silence", gain_db=-12, dur=0.6),
        Cue(b["me"], "paper strip slides out to the left (the mirror of the opening)", gain_db=-8, pan=-0.5,
            dur=0.86),
        Cue(b["me"] + 0.9, "silence; the last low note decays on black", gain_db=-14, dur=1.3),
    ]
