"""S02 - The City (9.042 s).

"It rains here most nights. Under an umbrella, every man looks the same.
 I'm the one they call when that becomes a problem."

Shot plan (scene seconds)
  A 0.00-2.78  IN: S01's head ring = the full moon (540, 960) r 260, same 15 px line. Cloud
               wisps cross it, rain starts; lens pull-back + crane down a canyon of towers
               (far / mid / near parallax, occluding silhouettes, fire escapes, wires), far sheet
               lightning on "most"; settle on the wet street; whip-tilt down (streaks + blur).
  B 2.78-5.35  the whip lands straight down on a crosswalk: a river of identical white umbrellas
               (sets.crowd_top) between lamp pools and headlight cones, rain falling away from
               the lens; slow-motion ramp on "same"; spiral dive + rack focus into one canopy.
  C 5.35-9.04  street level: a passer-by's canopy wipes off the lens revealing the detective
               limping in; he stops in the dark beside the lamp's cone, raises the matchbook and
               strikes with his LEFT hand on "I'm" - the flare lights his hollow head from below;
               one limping step into the light; push into the flame with a rack focus while the
               city falls away. OUT: flame mid-height at screen (540, 1150), ~100 px tall.
"""
import math

from engine import *
from engine.core import W, H, BLACK
from scenes import _lib_s02_s04 as L

# ----------------------------------------------------------------------------- timing
T_C0, T_C1 = 0.15, 2.40           # crane
T_W0, T_CUT1 = 2.45, 2.78         # whip tilt down -> cut to top-down
T_LAND = 3.12
T_DIVE0, T_CUT2 = 5.02, 5.35      # dive into a canopy -> cut to street level
T_STOP = 5.80                      # detective plants his last (limping) step
T_PUSH0, T_PUSH1 = 6.55, 8.85      # push into the flame


def _strike(T):
    return T.at("I'm")


# ============================================================================ shot A: moon + crane
D_SKY, D_FAR, D_MID, D_NEAR, D_RAIN, D_WIRE = 630.0, 1000.0, 1700.0, 2600.0, 1500.0, 3500.0
Z0, Z1 = 1.5, 1.0
MOON_C, MOON_R = (540.0, 330.0), L.S01_RING_R / Z0
WHIP_PX = 2600.0

WISPS = [  # sky-layer world: (y, x at t=0, speed px/s, half length, half thickness, phase)
    (392.0, 300.0, 64.0, 260.0, 20.0, 0.0),
    (262.0, 120.0, 88.0, 215.0, 15.0, 1.3),
    (476.0, 640.0, 52.0, 290.0, 22.0, 2.1),
]
MID_TOWERS = [(255.0, 205.0, 1160.0, 41, "water"), (628.0, 222.0, 1290.0, 43, "antenna"),
              (452.0, 150.0, 980.0, 47, "flat")]
NEAR_TOWERS = [(-180.0, 430.0, 2660.0, 61, "flat", 1), (832.0, 420.0, 2470.0, 63, "antenna", -1)]
G_FAR, G_MID, G_NEAR = 1560.0, 1660.0, 1770.0


def _crane(t):
    u = ease("inout3", inv_lerp(T_C0, T_C1, t))
    z = lerp(Z0, Z1, ease("inout", inv_lerp(T_C0, T_C1 + 0.1, t)))
    wp = WHIP_PX * ease("in3", inv_lerp(T_W0, T_CUT1, t))
    return u, z, wp


def _layer_cam(D, u, z, wp):
    return Camera(540.0, 960.0 - D * (1 - u) + wp / z, z)


def _wisp(f, y, xc, hl, ht, ph, alpha):
    """A thin streak of cloud: black body (it hides the moon where it passes) + 4 hairlines."""
    top = draw.bezier_pts((xc - hl, y), (xc - hl * 0.4, y - ht * 1.5), (xc + hl * 0.3, y - ht * 1.1), (xc + hl, y - 3), 18)
    bot = draw.bezier_pts((xc + hl, y - 3), (xc + hl * 0.35, y + ht * 1.1), (xc - hl * 0.5, y + ht * 0.9), (xc - hl, y), 18)
    L.black_poly(f, top + bot, alpha=0.92 * clamp(alpha))
    for j, (dy, a, l0, l1) in enumerate(((-0.6, 0.62, 0.04, 0.96), (-0.15, 0.4, 0.16, 0.9),
                                         (0.3, 0.5, 0.0, 0.74), (0.7, 0.28, 0.3, 1.0))):
        pts = []
        for i in range(21):
            k = l0 + (l1 - l0) * i / 20
            x = xc - hl + 2 * hl * k
            yy = y + dy * ht * math.sin(math.pi * k) + 3.5 * math.sin(k * 7 + ph + j)
            pts.append((x, yy))
        draw.stroke(f, pts, 1.7, WHITE, a * alpha)


def _walker(f, t, x0, ground, speed, facing, s, seed, alpha=1.0):
    p = rig.walk(t, x0, ground, speed, facing=facing, s=s)
    J = rig.solve(p)
    hand = (J["neck"][0] + facing * 22 * s, J["neck"][1] + 26 * s)
    p = rig.reach(p, "r", hand)
    J = rig.draw_figure(f, p, alpha=alpha)
    props.umbrella(f, J["rh"], angle=-90 + 4 * facing, R=118 * s, alpha=alpha, t=t, seed=seed, wobble=0.6)


def shot_a(f, t, T):
    u, z, wp = _crane(t)
    m = T.at("most") + 0.05                              # far sheet lightning on "most"
    flash = clamp(pulse(t, m, 0.02, 0.10) + 0.7 * pulse(t, m + 0.15, 0.02, 0.12))
    tg = L.tglob(T, t)

    # ---- sky: the moon (starts exactly as S01's ring: r 260 px, ~15.3 px line) + wisps
    with f.camera(_layer_cam(D_SKY, u, z, wp)):
        mw = lerp(L.S01_RING_W / Z0 ** 0.35, 7.5, ease("inout", inv_lerp(0.3, 2.4, t)))
        glow = 0.35 * ease("inout", inv_lerp(0.4, 1.6, t))
        draw.circle(f, MOON_C, MOON_R, mw, WHITE, 1.0, glow=glow)
        wa = ease("out", inv_lerp(0.0, 0.5, t))
        for (y, x0, v, hl, ht, ph) in WISPS:
            _wisp(f, y, x0 + v * t, hl, ht, ph, wa * (1 + 1.2 * flash))
        if flash > 0.02:                                # far sheet lightning on "most"
            L.bolt(f, (796, -320), (742, 700), seed=7, alpha=0.9 * flash, w=2.0, glow=0.3)

    # ---- far row (occluding: the bolt drops behind it)
    with f.camera(_layer_cam(D_FAR, u, z, wp)):
        L.far_row(f, G_FAR, 9, -260, 1340, 420, 900, t=tg, alpha=min(1.0, 0.3 + 0.6 * flash), lw=1.6,
                  lit=0.10, occlude=True)

    # ---- mid towers
    with f.camera(_layer_cam(D_MID, u, z, wp)):
        for (x, w, h, seed, roof) in MID_TOWERS:
            L.tower(f, x, G_MID, w, h, seed, t=tg, alpha=min(1.0, 0.58 + 0.4 * flash), lw=2.4, lit=0.17, roof=roof)

    # ---- rain between the layers
    with f.camera(_layer_cam(D_RAIN, u, z, wp)):
        ra = ease("inout", inv_lerp(0.2, 1.2, t))
        if ra > 0:
            fx.rain(f, t, density=lerp(0.35, 1.0, ra), alpha=0.85 * ra, seed=21)

    # ---- near canyon walls with fire escapes + the wet street
    with f.camera(_layer_cam(D_NEAR, u, z, wp)):
        for (x, w, h, seed, roof, side) in NEAR_TOWERS:
            L.tower(f, x, G_NEAR, w, h, seed, t=tg, alpha=1.0, lw=3.0, lit=0.2, roof=roof)
            face = x + w if side > 0 else x
            L.fire_escape(f, face, G_NEAR - h + 240, G_NEAR - 300, side=side, alpha=0.85, lw=2.4)
        draw.line(f, (-400, G_NEAR), (1480, G_NEAR), 3.4, WHITE, 1.0)
        draw.line(f, (-400, G_NEAR + 40), (1480, G_NEAR + 40), 2.0, WHITE, 0.6)
        for lx, fc in ((372.0, 1), (708.0, -1)):
            lp = props.streetlamp(f, (lx, G_NEAR), height=470, s=0.7, facing=fc, t=tg, glow_r=200)
            fx.light_cone(f, lp, 90, 46, 420, AMBER, 0.10)
            fx.reflection(f, lp[0], G_NEAR + 34, 150, 30, AMBER, 0.55, t, seed=int(lx))
        for (x0, v, fc, sd) in ((0, 68, 1, 1), (530, 60, -1, 2), (520, 60, 1, 3), (1090, 72, -1, 4)):
            _walker(f, t, x0, G_NEAR, v, fc, 0.36, sd, alpha=0.9)
        fx.splashes(f, t, G_NEAR, -100, 1180, rate=0.8, alpha=0.6)

    # ---- very near: sagging wires across the canyon (fast parallax, out of focus)
    with f.camera(_layer_cam(D_WIRE, u, z, wp)):
        with L.soft(f, 5.0):
            L.wire(f, (-200, -760), (1280, -640), sag=110, w=2.6, alpha=0.75)
            L.wire(f, (-200, -1260), (1280, -1330), sag=80, w=2.2, alpha=0.6)

    if t > T_W0:
        v = WHIP_PX * 3 * inv_lerp(T_W0, T_CUT1, t) ** 2 / (T_CUT1 - T_W0) / 24.0   # px / frame
        f.whip = (0.0, min(380.0, 0.75 * v))


# ============================================================================ shot B: top-down crowd
HERO_R = 56.0
CAR1 = ((1078.0, 712.0), 180.0)
CAR2 = ((2.0, 1208.0), 0.0)
LAMPS_TOP = [(212.0, 398.0), (868.0, 1528.0)]
S_CAR = 0.78


def _teff(t, T):
    s = T.at("same")
    return L.ramp_time(t, s - 0.25, s + 0.2, 0.3)


def _hero_pos(t, T):
    te = _teff(t, T)
    return (548.0 + 6 * fbm1(te * 0.4, 77), 1000.0 + 30.0 * (te - 5.1))


def _cam_b(t, T):
    land = ease("out3", inv_lerp(T_CUT1, T_LAND, t))
    off = 1500.0 * (1 - land)
    z = lerp(1.0, 1.2, ease("inout3", inv_lerp(T_CUT1, T_DIVE0 + 0.05, t)))
    rot = lerp(-11.0, 5.0, ease("inout3", inv_lerp(T_CUT1, T_DIVE0, t)))
    c = (540.0, 960.0 - off / z)
    kd = ease("in3", inv_lerp(T_DIVE0, T_CUT2, t))
    if kd > 0:
        hp = _hero_pos(t, T)
        kc = ease("inout", inv_lerp(T_DIVE0, T_CUT2 - 0.06, t))
        c = lerp(c, hp, kc)
        z = L.log_zoom(z, 26.0, kd)
        rot = rot + 38.0 * kd
    return Camera(c[0], c[1], z, rot)


def _road(f):
    for y in (470.0, 1450.0):
        o = -34 if y < 900 else 34
        draw.line(f, (-700, y), (1780, y), 3.2, WHITE, 0.9)
        draw.line(f, (-700, y + o), (1780, y + o), 1.8, WHITE, 0.5)
    for k in range(-6, 14):          # sidewalk seams
        x = k * 150.0
        draw.line(f, (x, 436), (x, 60), 1.2, WHITE, 0.18)
        draw.line(f, (x + 75, 1484), (x + 75, 1860), 1.2, WHITE, 0.18)
    for x0, x1 in ((-700, 290), (790, 1780)):           # lane divider, broken at the crosswalk
        draw.line(f, (x0, 960), (x1, 960), 2.2, WHITE, 0.45, dash=(26, 22))
    draw.line(f, (262, 965), (262, 1446), 3.0, WHITE, 0.6)   # stop lines
    draw.line(f, (818, 474), (818, 955), 3.0, WHITE, 0.6)
    for i in range(10):              # zebra bars (long axis along the road)
        draw.rect(f, 305, 490.0 + i * 96.0, 470, 46, 2.2, WHITE, 0.5)


def _lamp_top(f, c, tg, seed):
    fl = 0.92 + 0.08 * fbm1(tg * 4.0, seed)
    draw.line(f, c, (c[0] + (40 if c[0] < 540 else -40), c[1] + (-26 if c[1] < 900 else 26)), 3.0, WHITE, 0.9)
    draw.circle(f, c, 17, 2.6, WHITE, 0.95)
    draw.circle(f, c, 9, 1, AMBER, 0.95 * fl, fill_it=True, glow=1.2)
    draw.glow_dot(f, c, 160, AMBER, 0.7 * fl, core=False)


def shot_b(f, t, T):
    cam = _cam_b(t, T)
    f.set_camera(cam)
    tg = L.tglob(T, t)
    te = _teff(t, T)
    kd = ease("in3", inv_lerp(T_DIVE0, T_CUT2, t))

    (c1, a1), (c2, a2) = CAR1, CAR2
    f1 = (c1[0] - 262 * S_CAR, c1[1])
    f2 = (c2[0] + 262 * S_CAR, c2[1])
    lights = [Light.radial(c, 440, intensity=1.0) for c in LAMPS_TOP]
    lights += [Light.cone(f1, 180, 46, 860, intensity=0.95), Light.cone(f2, 0, 46, 860, intensity=0.95),
               Light.radial((540, 960), 640, intensity=0.45)]
    fx.light_cone(f, f1, 180, 38, 700, AMBER, 0.13, glow=0.4)
    fx.light_cone(f, f2, 0, 38, 700, AMBER, 0.13, glow=0.4)
    for c in LAMPS_TOP:
        fx.light_pool(f, c, 320, 320, AMBER, 0.14, glow=0.45)

    def ground():
        _road(f)
        fx.ripples(f, te, -300, 480, 300, 1440, rate=0.9, alpha=0.5, squash=0.82, seed=12)
        fx.ripples(f, te, 780, 480, 1380, 1440, rate=0.9, alpha=0.5, squash=0.82, seed=13)
        for pc, r in (((140, 640), 70), ((930, 1300), 90), ((-60, 860), 60)):
            fx.puddle(f, pc, r, r * 0.72, te, seed=int(pc[0]), alpha=0.55)
        props.car_top(f, c1, a1, s=S_CAR, headlights=1.0)
        props.car_top(f, c2, a2, s=S_CAR, headlights=1.0)
        sets.crowd_top(f, te, area=(312.0, -460.0, 768.0, 2380.0), n=60, seed=5, speed=74.0, R=(50.0, 62.0))

    with f.lit(lights, ambient=0.42, soften=4.0):
        with L.soft(f, 15.0 * kd):                 # rack focus onto the one canopy we dive into
            ground()
        L.hero_umbrella_top(f, _hero_pos(t, T), HERO_R, 12 + 14 * math.sin(te * 0.9),
                            opaque=ease("inout", inv_lerp(T_DIVE0 - 0.1, T_DIVE0 + 0.12, t)))
    for c in LAMPS_TOP:
        _lamp_top(f, c, tg, int(c[0]))

    L.rain_top(f, te, n=int(160 + 140 * kd), seed=31, alpha=0.5 + 0.3 * kd, life=0.34 - 0.16 * kd)

    if t < T_LAND + 0.05:
        k = 1 - inv_lerp(T_CUT1, T_LAND, t)
        f.whip = (0.0, 300.0 * k ** 2)


# ============================================================================ shot C: street level
LP_ANGLE, LP_SPREAD = 92.0, 40.0


def _lamp_point():
    x, y = L.LAMP_BASE
    top = (x, y - L.LAMP_H)
    return (x + 120.0, top[1] + 26.0 + 36.0)


def _walk_tau(t):
    """Walk clock chosen so T_STOP lands exactly on a double-support phase (rig.walk cycle math)."""
    base = Pose(x=0, y=0, s=1.0, facing=-1)
    pa = rig._walk_angles(base, 0.0, 0.5, 1.0, 1.0)
    pb = rig._walk_angles(base, 0.5, 0.5, 1.0, 1.0)
    cyc = abs(rig._foot_dx(pa, "l") - rig._foot_dx(pa, "r")) + abs(rig._foot_dx(pb, "r") - rig._foot_dx(pb, "l"))
    half = cyc / 2.0 / 96.0
    return 7 * half - (T_STOP - t)


def _walk_x0():
    p = L.det_walk_pose(_walk_tau(T_STOP), 0.0)
    return L.DET_STOP_X - p.x


def _det(t, T):
    """(pose, match state) of the detective in shot C."""
    tg = L.tglob(T, t)
    strike = _strike(T)
    if t < T_STOP:
        return L.det_walk_pose(_walk_tau(t), _walk_x0()), None
    stand = L.det_stand(L.DET_STOP_X)
    if t < L.T_STEP0:
        p_stop = L.det_walk_pose(_walk_tau(T_STOP), _walk_x0())
        k = ease("out3", inv_lerp(T_STOP, T_STOP + 0.24, t))
        p = p_stop.blend(stand, k)
        p = p.copy(lean=p.lean + 5.0 * math.sin(math.pi * k) * (1 - k))      # follow-through
    else:
        p = L.det_step_pose(t)
    p = rig.breathe(p, tg, amt=0.8, seed=5)
    J = rig.solve(p)
    M = (J["neck"][0] - 60.0, J["neck"][1] + 84.0)                          # matchbook in front

    # RIGHT hand raises the matchbook, pockets it at the hip, then hangs
    raise_k = ease("inout", inv_lerp(5.84, 6.0, t))
    hang = L.hang_target(J)
    pocket = (J["hip"][0] - 10.0, J["hip"][1] - 6.0)
    book_hold = (M[0] + 8, M[1] + 10)
    if t < 6.3:
        rh_t = lerp(J["rh"], book_hold, raise_k)
    elif t < 6.66:
        rh_t = lerp(book_hold, pocket, ease("inout", inv_lerp(6.3, 6.62, t)))
    else:
        rh_t = lerp(pocket, hang, ease("inout", inv_lerp(6.66, 7.05, t)))
    p = rig.reach(p, "r", rh_t)

    # LEFT hand: tear a match, swipe it down the striker, flick up -> flare on "I'm"
    tip_k = Track([(5.86, (M[0] + 30, M[1] + 60)), (5.97, (M[0] - 6, M[1] - 24), "out3"),
                   (6.015, (M[0] + 18, M[1] + 22), "inout"), (strike, (M[0] - 24, M[1] + 26), "in"),
                   (strike + 0.05, (M[0] - 56, M[1] - 6), "out")])
    ang_k = Track([(5.86, -80.0), (5.97, -82.0, "out3"), (6.015, 112.0, "inout"), (strike, 150.0, "in"),
                   (strike + 0.05, 232.0, "out"), (strike + 0.45, 360.0 + L.HOLD_ANGLE, "inout")])
    ang = ang_k(t)
    fin_hand = L.det_final()[1]
    if t < strike + 0.05:
        tip = tip_k(t)
        a = math.radians(ang)
        lh = (tip[0] - math.cos(a) * 52.0, tip[1] - math.sin(a) * 52.0)
        lh = lerp(J["lh"], lh, ease("inout", inv_lerp(5.80, 5.93, t)))
    else:
        tip_end = (M[0] - 56, M[1] - 6)
        a = math.radians(232.0)
        lh_end = (tip_end[0] - math.cos(a) * 52.0, tip_end[1] - math.sin(a) * 52.0)
        lh = lerp(lh_end, L.hold_target(p), ease("inout", inv_lerp(strike + 0.05, strike + 0.5, t)))
        lh = lerp(lh, fin_hand, ease("inout", inv_lerp(L.T_STEP1 - 0.25, L.T_STEP1 + 0.35, t)))
    p = rig.reach(p, "l", lh)
    lit = clamp((t - strike) / 0.05) if t >= strike else 0.0
    flare = pulse(t, strike, 0.025, 0.28)
    return p, dict(angle=ang, lit=lit, flare=flare, show=t >= 5.93, raise_k=raise_k)


def _lens_wipe(f, t):
    """Foreground wipe: we come out from under a passer-by's canopy (rim rises out of frame)."""
    k = ease("inout", inv_lerp(T_CUT2, T_CUT2 + 0.30, t))
    if k < 1:
        L.lens_canopy(f, lerp(2050.0, -280.0, k), xc=lerp(560.0, 420.0, k))


def _cam_c(t, T):
    z = lerp(1.04, 1.14, ease("out3", inv_lerp(T_CUT2, 6.6, t)))
    c = (lerp(600.0, 585.0, ease("inout", inv_lerp(T_CUT2, 6.6, t))),
         lerp(1060.0, 1135.0, ease("out3", inv_lerp(T_CUT2, 6.2, t))))
    cam = Camera(c[0], c[1], z)
    k = ease("inout3", inv_lerp(T_PUSH0, T_PUSH1, t))
    if k > 0:
        mid = L.det_final()[3]
        fs = lerp(cam.to_screen(mid), L.FLAME_SCREEN, k)
        cam = L.cam_put(mid, fs, L.log_zoom(z, L.CUT_ZOOM, k))
    kick = pulse(t, _strike(T), 0.02, 0.35)
    if kick > 0.01:
        cam = cam.shaken(t, amp=7 * kick, rot_amp=0.25 * kick, freq=6.0, seed=4)
    return cam


def shot_c(f, t, T):
    tg = L.tglob(T, t)
    p, m = _det(t, T)
    J = rig.solve(p)
    cam = _cam_c(t, T)
    f.set_camera(cam)

    lp = _lamp_point()
    end_k = ease("inout", inv_lerp(7.7, 8.85, t))           # the city falls away: only the flame
    blur_r = lerp(0.0, 13.0, ease("inout", inv_lerp(7.2, 8.6, t)))
    tip = None
    if m and m["show"]:
        a = math.radians(m["angle"])
        tip = (J["lh"][0] + math.cos(a) * 52.0, J["lh"][1] + math.sin(a) * 52.0)
    lights = [Light.cone(lp, LP_ANGLE, LP_SPREAD, 1300, intensity=lerp(0.92, 0.0, end_k)),
              Light.radial(lp, 160, intensity=0.8 * (1 - end_k))]
    if m and m["lit"] > 0 and tip is not None:
        lights.append(Light.radial(tip, 300 * (1 + 0.9 * m["flare"]), intensity=1.0))

    def background():
        with f.camera(cam.parallax(0.45)):
            sets.skyline(f, 1290, seed=12, x0=-500, x1=1600, t=tg, alpha=0.26, lw=1.6, lit=0.1, depth_scale=0.62)
        with f.camera(cam.parallax(0.72)):
            for (x, w, h, sd) in ((-120, 300, 760, 81), (230, 250, 900, 82), (520, 300, 680, 83), (860, 280, 840, 84)):
                L.tower(f, x, 1385, w, h, sd, t=tg, alpha=0.5, lw=2.2, lit=0.2, roof="flat")
            draw.line(f, (-600, 1385), (1700, 1385), 2.2, WHITE, 0.5)
            _walker(f, t, -60, 1385, 38, 1, 0.42, 7, alpha=0.65)
            _walker(f, t, 1180, 1385, 34, -1, 0.42, 8, alpha=0.65)
            fx.reflection(f, 380, 1400, 120, 24, AMBER, 0.3, t, seed=21)
            fx.reflection(f, 990, 1400, 120, 24, AMBER, 0.3, t, seed=22)

    def street():
        sets.street(f, L.ST_GROUND, x0=-600, x1=1700)
        props.streetlamp(f, L.LAMP_BASE, height=L.LAMP_H, facing=1, t=tg, on=1.0)
        fx.puddle(f, (300, 1592), 160, 20, t, seed=3, alpha=0.6)

    with f.alpha(lerp(1.0, 0.0, end_k)):
        with L.soft(f, blur_r):
            background()

    fx.light_cone(f, lp, LP_ANGLE, LP_SPREAD - 6, 1000, AMBER, lerp(0.11, 0.0, end_k), glow=0.35 * (1 - end_k))
    with f.lit(lights, ambient=lerp(0.2, 0.05, end_k), soften=3.0):
        with f.alpha(lerp(1.0, 0.0, end_k)):
            with L.soft(f, blur_r * 0.8):
                street()
        fx.rain(f, t, density=1.0, alpha=lerp(1.0, 0.0, end_k), seed=23)
        J = rig.draw_figure(f, p)
        if m and m["raise_k"] > 0 and t < 6.7:
            ba = clamp(1 - inv_lerp(6.54, 6.66, t))                       # slips into the pocket
            props.matchbook(f, (J["rh"][0] - 2, J["rh"][1] - 12), angle=-8, s=0.3, n=6, missing={0, 1}, alpha=ba)
    with f.alpha(lerp(1.0, 0.0, end_k)):
        fx.reflection(f, lp[0], L.ST_GROUND + 50, 200, 40, AMBER, 0.5, t, seed=5)
        fx.splashes(f, t, L.ST_GROUND, -200, 1300, rate=0.9, alpha=0.6)

    if m and m["show"]:
        props.match(f, J["lh"], angle=m["angle"], s=L.MATCH_S, lit=m["lit"], flare=m["flare"], t=tg, seed=1)
        if m["lit"] > 0:
            fx.light_pool(f, (J["lh"][0], L.ST_GROUND + 6), 120, 22, AMBER, 0.18 * m["lit"] * (1 - end_k))

    _lens_wipe(f, t)


# ============================================================================ module API
def render(f, t, T):
    tf = L.frame_t(t)                  # shot choice by frame time: motion blur never crosses a cut
    if tf < T_CUT1:
        shot_a(f, t, T)
    elif tf < T_CUT2:
        shot_b(f, t, T)
    else:
        shot_c(f, t, T)


def cues(T):
    s = _strike(T)
    return [
        Cue(T.at("most") + 0.12, "thunder", gain_db=-9, pan=0.35, distance=0.85),
        Cue(T_W0 + 0.1, "whip", gain_db=-6, pan=0.0),
        Cue(T_CUT1 + 0.02, "whoosh", gain_db=-12, size=0.5),
        Cue(T_CUT1 + 0.25, "crowd_walla", gain_db=-20, dur=T_CUT2 - T_CUT1 - 0.2),
        Cue(3.30, "footstep", gain_db=-22, pan=-0.2, weight=0.4, wet=1),
        Cue(3.71, "footstep", gain_db=-22, pan=0.2, weight=0.4, wet=1),
        Cue(4.14, "footstep", gain_db=-23, pan=-0.1, weight=0.4, wet=1),
        Cue(T_DIVE0 + 0.05, "whoosh", gain_db=-9, size=0.6),
        Cue(T_CUT2 + 0.02, "umbrella_flap", gain_db=-10, pan=-0.4),
        Cue(5.42, "footstep", gain_db=-11, pan=0.05, weight=0.85, wet=1),
        Cue(T_STOP - 0.02, "footstep", gain_db=-14, pan=0.05, weight=0.45, wet=1),
        Cue(5.95, "paper_tear", gain_db=-16, pan=-0.05),
        Cue(s - 0.035, "match_strike", gain_db=-2, pan=-0.05),
        Cue(s + 0.02, "match_flare", gain_db=-5, pan=-0.05),
        Cue(lerp(L.T_STEP0, L.T_STEP1, 0.40), "footstep", gain_db=-10, pan=-0.05, weight=0.85, wet=1),
        Cue(lerp(L.T_STEP0, L.T_STEP1, 0.78), "footstep", gain_db=-15, pan=-0.05, weight=0.35, wet=1),
    ]


def motion_blur(t, T):
    if T_W0 + 0.08 < t < T_CUT1 + 0.14:
        return 3
    if T_DIVE0 + 0.15 < t < T_CUT2:
        return 3
    s = _strike(T)
    if s - 0.06 < t < s + 0.06:
        return 3
    return 1
