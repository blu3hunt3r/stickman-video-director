"""S04 - The Rain Murders (9.667 s).

"So when the rain murders began, the department gave up fast.
 Four victims. Four rainy nights. One burnt match beside every body."

Shot plan (scene seconds)
  A 0.00-2.30  IN: whip DOWN out of black (streaks + motion blur) onto a top-down chalk outline on
               wet cobbles; rain falling away from the lens, ripples, siren blue/crimson pulsing at
               the frame edges, a cop's blue flashlight beam sweeping the body; slow push + roll.
  B 2.30-4.40  ground level: the cop's blue beam on the outline; on "gave up" he drops a blank
               folder into a puddle (splash, ripples) and walks off on "fast" (even, brisk gait);
               handheld push into the abandoned folder.
  C 4.40-6.77  vertical scroll montage through four places - cobbles, bridge rail, stairwell,
               parking lines - each outline landing with a white camera-flash pop on
               "Four" / "victims" / "Four" / "nights"; a small ember glows by every right hand.
  D 6.77-9.67  low macro on "One": the burnt match by the outline's hand, ember glowing, smoke
               curling; a raindrop sizzles it on "burnt"; four 0.25 s inserts of the same match
               at each scene on "beside every body". OUT: tilt up following the smoke wisp,
               kept at screen x = 540.
"""
import math

from engine import *
from engine.core import W, H, BLACK
from scenes import _lib_s02_s04 as L

T_LAND = 0.42
T_B = 2.30
T_C = 4.40
T_TILT = 8.52
TILE = 1900.0


def _d_start(T):
    return T.at("One")


# ============================================================================ outlines
OUTLINES = [  # (x, y, s, rot) in the scroll strip (tile k centered at y = 960 + k * TILE)
    (540.0, 985.0, 1.5, -28.0),
    (470.0, 960.0 + TILE, 1.5, 76.0),
    (520.0, 960.0 + 2 * TILE + 40, 1.5, 160.0),
    (560.0, 960.0 + 3 * TILE - 20, 1.5, -112.0),
]
_OCACHE = {}


def _outline(k):
    if k not in _OCACHE:
        x, y, s, rot = OUTLINES[k]
        _OCACHE[k] = rig.lying(x, y, s=s, rot=rot)
    return _OCACHE[k]


def _match_spot(k):
    """Where the burnt match lies: just past the outline's RIGHT hand."""
    lines, hc, hr = _outline(k)
    sh, el, hand = lines[2]
    ux, uy = vnorm((hand[0] - el[0], hand[1] - el[1]))
    base = (hand[0] + ux * 58 - uy * 26, hand[1] + uy * 58 + ux * 26)
    ang = math.degrees(math.atan2(uy, ux)) + 38.0
    return base, ang


def _crime_tile(f, k, t, flash_amt, fast=False):
    """Ground texture + chalk outline + puddles + the small ember of tile k."""
    cy = 960.0 + k * TILE
    if k == 0:
        L.cobbles(f, 540.0, cy, alpha=0.32, seed=1)
    elif k == 1:
        L.bridge_tile(f, 540.0, cy, t, alpha=0.62)
    elif k == 2:
        L.stairs_tile(f, 540.0, cy, alpha=0.62)
    else:
        L.parking_tile(f, 540.0, cy, alpha=0.62)
    for i, (dx, dy, r) in enumerate(((-300, 380, 80), (290, -420, 64), (330, 520, 54))):
        fx.puddle(f, (540 + dx, cy + dy), r, r * 0.74, t, seed=k * 10 + i, alpha=0.5)
    fx.ripples(f, t, 80, cy - 760, 1000, cy + 760, rate=0.55, alpha=0.4, squash=0.85, seed=20 + k)
    lines, hc, hr = _outline(k)
    if fast:
        L.fast_outline(f, lines, hc, hr)
    else:
        fx.chalk_outline(f, lines, hc, hr, seed=7 + k)


def _tile_ember(f, k, t, amt=1.0):
    base, ang = _match_spot(k)
    tip = props.match(f, base, angle=ang, s=0.9, burnt=1.0, ember=0.0, t=t, seed=k)
    fl = 0.75 + 0.25 * fbm1(t * 3.0, 40 + k)
    draw.glow_dot(f, tip, 34, AMBER, 0.9 * amt * fl)
    draw.circle(f, tip, 3.4, 1, AMBER, amt, fill_it=True, glow=0.8 * amt)


def _edge_lights(f, cam, t, amt=1.0):
    """f.lit lights matching the screen-edge siren glows."""
    b, r = L.smooth_siren(t)
    out = []
    if b > 0.02:
        out.append(Light.radial(cam.to_world((-140, 800)), 900 / cam.zoom, intensity=0.75 * b * amt))
    if r > 0.02:
        out.append(Light.radial(cam.to_world((W + 140, 1120)), 900 / cam.zoom, intensity=0.6 * r * amt))
    return out


# ============================================================================ shot A: whip down onto victim 1
def _cam_a(t):
    land = ease("out3", inv_lerp(0.0, T_LAND, t))
    off = 2300.0 * (1 - land)
    k = ease("inout3", inv_lerp(T_LAND - 0.1, T_B, t))
    z = lerp(1.0, 1.14, k)
    rot = lerp(-5.0, 2.0, k)
    return Camera(540.0, 960.0 - off, z, rot), land


def shot_a(f, t, T):
    cam, land = _cam_a(t)
    f.set_camera(cam)
    m = T.at("murders")
    sweep = Track([(0.2, -158.0), (m + 0.05, -128.0, "inout3"), (T_B, -114.0, "inout")])(t)
    apex = (1120.0, 1760.0)
    lights = [Light.cone(apex, sweep, 22, 1500, intensity=0.95), Light.radial((540, 985), 560, intensity=0.4)]
    lights += _edge_lights(f, cam, t, land ** 2)
    fx.light_cone(f, apex, sweep, 18, 1300, BLUE, 0.12 * land, glow=0.35)
    with f.lit(lights, ambient=0.28, soften=4.0):
        _crime_tile(f, 0, t, 0.0)
    _tile_ember(f, 0, t, land)
    L.rain_top(f, t, n=150, seed=41, alpha=0.5 * land)
    L.strobe_edges(f, t, amt=land ** 2)
    if t < T_LAND:
        k = 1 - inv_lerp(0.0, T_LAND, t)
        f.whip = (0.0, 380.0 * k ** 1.5)


# ============================================================================ shot B: the cop gives up
GB = 1430.0                     # the cop's ground line (feet)
COP_X = 655.0
PUDDLE = (560.0, 1466.0)


def _flat_outline():
    if "flat" not in _OCACHE:
        lines, hc, hr = rig.lying(0.0, 0.0, s=1.5, rot=12.0)
        sq = 0.24
        cx, cy = 400.0, 1492.0

        def P(q):
            return (cx + q[0], cy + q[1] * sq)
        _OCACHE["flat"] = ([[P(q) for q in pl] for pl in lines], P(hc), hr * 0.5)
    return _OCACHE["flat"]


def _cop(t, T):
    """(pose, flashlight hand/angle, folder state)."""
    g = T.at("gave")
    fast = T.at("fast")
    stand = rig.stand(COP_X, GB, facing=-1)
    stand = rig.breathe(stand, t, amt=0.9, seed=70)
    J = rig.solve(stand)
    if t < fast + 0.04:
        p = stand
        fl_hand = (J["neck"][0] - 52, J["neck"][1] + 64)
        fl_ang = 146.0 + 4 * fbm1(t * 0.7, 71)
        p = rig.reach(p, "r", fl_hand)
        hold = (J["hip"][0] - 40, J["hip"][1] - 26)
        rel = ease("out3", inv_lerp(g, g + 0.18, t))
        p = rig.reach(p, "l", lerp(hold, (J["hip"][0] - 10, J["hip"][1] + 22), rel))
        Jp = rig.solve(p)
        return p, (Jp["rh"], fl_ang), dict(hold=Jp["lh"], released=t >= g)
    # turns away and walks off (even, brisk gait - not the detective)
    tau = t - (fast + 0.04)
    w = rig.walk(tau, COP_X, GB, 230.0, facing=1, s=1.0)
    k = ease("out", inv_lerp(0.0, 0.16, tau))
    st = rig.stand(COP_X, GB, facing=1)
    p = st.blend(w, k)
    Jw = rig.solve(p)
    fl_hand = (Jw["neck"][0] + 48, Jw["neck"][1] + 66)
    p = rig.reach(p, "r", fl_hand)
    Jp = rig.solve(p)
    return p, (Jp["rh"], 44.0 + 6 * math.sin(tau * 9)), dict(hold=None, released=True)


def _folder_state(t, T, hold):
    """(position, screen angle, squash, seconds since landing, ground rotation or None)."""
    g = T.at("gave")
    land_t = g + 0.26
    if t < g:
        return hold, 8.0, 1.0, 0.0, None
    if t < land_t:
        k = inv_lerp(g, land_t, t)
        p = (lerp(hold[0], PUDDLE[0] + 10, k), hold[1] + (PUDDLE[1] - 4 - hold[1]) * k * k)
        return p, lerp(8.0, 64.0, k), lerp(1.0, 0.45, k * k), 0.0, None
    since = t - land_t
    drift = (PUDDLE[0] + 10 + 5 * math.sin(since * 1.6), PUDDLE[1] - 3)
    return drift, 0.0, 0.24, since, 22.0 + 5 * math.sin(since * 1.2)


def _cam_b(t, T):
    k = ease("inout", inv_lerp(3.3, T_C, t))
    c = lerp((612.0, 1240.0), (570.0, 1405.0), k)
    cam = Camera(c[0], c[1], L.log_zoom(1.5, 2.15, k))
    return cam.shaken(t, amp=5.0, rot_amp=0.25, freq=0.9, seed=33)


def shot_b(f, t, T):
    cam = _cam_b(t, T)
    f.set_camera(cam)
    p, (fl_hand, fl_ang), fs = _cop(t, T)
    a = math.radians(fl_ang)
    lens = (fl_hand[0] + math.cos(a) * 26, fl_hand[1] + math.sin(a) * 26)
    lights = [Light.cone(lens, fl_ang, 26, 900, intensity=1.0), Light.radial((560, 1400), 520, intensity=0.3)]
    b, r = L.smooth_siren(t)
    lights += [Light.radial((900, 1180), 700, intensity=0.5 * b), Light.radial((900, 1180), 700, intensity=0.4 * r)]

    with L.soft(f, 7.0):                                     # far: police car + buildings, out of focus
        with f.camera(cam.parallax(0.6)):
            for (x, w_, h, sd) in ((-80, 260, 820, 91), (230, 230, 640, 92), (520, 300, 900, 93), (880, 260, 700, 94)):
                L.tower(f, x, 1230, w_, h, sd, t=t, alpha=0.35, lw=2.0, lit=0.14)
            props.car_side(f, 900, 1236, s=0.42, facing=-1, police=True, t=t, headlights=1.0, alpha=0.7)
    with f.lit(lights, ambient=0.2, soften=3.5):
        draw.line(f, (-400, 1236), (1500, 1236), 2.0, WHITE, 0.45)
        lines, hc, hr = _flat_outline()
        fx.chalk_outline(f, lines, hc, hr, body_w=40.0, seed=3)
        draw.ellipse(f, PUDDLE, 135, 17, 0, 2.0, WHITE, 0.6)
        fx.rain(f, t, density=0.9, seed=51)
        J = rig.draw_figure(f, p)
    props.match(f, (318.0, 1500.0), angle=176, s=0.7, burnt=1.0, t=t)          # (plant) by the hand
    draw.glow_dot(f, (282.0, 1499.0), 20, AMBER, 0.75 * (0.8 + 0.2 * fbm1(t * 3, 5)))
    L.flashlight(f, fl_hand, fl_ang, s=1.0, beam_len=820, spread=22, haze=0.2)
    # the blank folder: held, dropped, floating in the puddle
    pos, ang, flat, since, grot = _folder_state(t, T, fs["hold"] or (560, 1300))
    L.folder(f, pos, ang, s=1.0, flat=flat, ground_rot=grot)
    if since > 0:
        k = clamp(since / 0.32)
        for i in range(7):                                     # splash crown
            sa = math.radians(-160 + 140 * i / 6)
            r0 = 30 + 70 * k
            pa = (PUDDLE[0] + 10 + math.cos(sa) * r0, PUDDLE[1] - 6 + math.sin(sa) * r0 * 0.35 - 30 * math.sin(math.pi * k))
            pb = (PUDDLE[0] + 10 + math.cos(sa) * (r0 + 16), PUDDLE[1] - 6 + math.sin(sa) * (r0 + 16) * 0.35 - 44 * math.sin(math.pi * k))
            if k < 1:
                draw.line(f, pa, pb, 2.0, WHITE, 0.8 * (1 - k))
        for i in range(3):
            tau = since - 0.12 * i
            if tau > 0:
                rr = 20 + 160 * tau
                draw.ellipse(f, (PUDDLE[0] + 10, PUDDLE[1] - 2), rr, rr * 0.13, 0, 1.6, WHITE, 0.6 * math.exp(-tau * 1.8))
    fx.splashes(f, t, GB, -200, 1300, rate=0.9, alpha=0.6)
    fx.light_pool(f, (430, 1490), 220, 30, BLUE, 0.16, glow=0.5)              # the beam's pool on the body
    with f.camera(cam.parallax(0.6)):
        fx.reflection(f, 878, 1250, 140, 30, BLUE, 0.55 * b, t, seed=9)
        fx.reflection(f, 922, 1250, 140, 30, CRIMSON, 0.5 * r, t, seed=10)
    L.strobe_edges(f, t, amt=0.8)


# ============================================================================ shot C: the scroll montage
def _landings(T):
    return [T.at("Four"), T.at("victims") + 0.04, T.at("Four", 1), T.at("nights")]


def _cam_c(t, T):
    ld = _landings(T)
    ys = [960.0 + k * TILE for k in range(4)]
    rots = [-4.0, 3.0, -2.5, 4.0]
    # settle into tile 0 from just above (we cut in on the move)
    y = lerp(ys[0] - 260.0, ys[0], ease("out3", inv_lerp(T_C, ld[0], t)))
    rot = rots[0]
    for k in range(1, 4):
        t0 = ld[k - 1] + (0.06 if k == 1 else 0.14)
        kk = ease("inout3", inv_lerp(t0, ld[k], t))
        y = lerp(y, ys[k], kk) if t >= t0 else y
        rot = lerp(rot, rots[k], kk) if t >= t0 else rot
    z = 1.0
    push = ease("inout", inv_lerp(ld[3] + 0.05, _d_start(T), t))
    if push > 0:
        base, ang = _match_spot(3)
        y = lerp(y, base[1], push)
        x = lerp(540.0, base[0], push)
        z = L.log_zoom(1.0, 1.9, push)
        return Camera(x, y, z, rot)
    return Camera(540.0, y, z, rot)


def _speed_c(t, T):
    c0 = _cam_c(t - 0.01, T)
    c1 = _cam_c(t + 0.01, T)
    return abs(c1.y - c0.y) / 0.02 * c1.zoom              # screen px / s


def shot_c(f, t, T):
    cam = _cam_c(t, T)
    f.set_camera(cam)
    ld = _landings(T)
    flash = 0.0
    for i, tl in enumerate(ld):
        flash = max(flash, (1.0 if i % 2 == 0 else 0.75) * pulse(t, tl, 0.015, 0.2))
    lights = [Light.radial((540, cam.y), 800, intensity=0.6)] + _edge_lights(f, cam, t)
    ambient = 0.3 + 0.7 * flash
    y0, y1 = cam.y - 980 / cam.zoom, cam.y + 980 / cam.zoom
    fast = _speed_c(t, T) > 1800
    with f.lit(lights, ambient=min(1.0, ambient), soften=4.0):
        for k in range(4):
            cy = 960.0 + k * TILE
            if cy + 1000 > y0 and cy - 1000 < y1:
                _crime_tile(f, k, t, flash, fast=fast)
    for k in range(4):
        cy = 960.0 + k * TILE
        if cy + 1000 > y0 and cy - 1000 < y1:
            _tile_ember(f, k, t, 1.0)
    L.rain_top(f, t, n=150, seed=43, alpha=0.5)
    L.strobe_edges(f, t)
    srcs = [(1260.0, 120.0), (-180.0, 200.0), (1260.0, 1500.0), (-180.0, 1420.0)]
    for i, tl in enumerate(ld):
        L.flash_pop(f, (1.0 if i % 2 == 0 else 0.75) * pulse(t, tl, 0.015, 0.2), src=srcs[i])
    v = _speed_c(t, T)
    if v > 300:
        f.whip = (0.0, min(360.0, v / 24.0 * 0.6))


# ============================================================================ shot D: the burnt match
MG = 1300.0                     # macro ground line (pavement horizon at the match)
EMBER = (520.0, 1294.0)


def _ember_amt(t, T):
    b = T.at("burnt")
    base = 0.8 + 0.2 * fbm1(t * 2.6, 81)
    return base + 0.9 * pulse(t, b + 0.03, 0.03, 0.25)


def _inserts(T):
    s0 = T.at("beside") - 0.07
    return [s0 + 0.25 * i for i in range(4)]


def _place(t, T):
    ins = _inserts(T)
    for i in range(3, -1, -1):
        if t >= ins[i]:
            return i
    return -1


def _ember_tip():
    base = (EMBER[0] + 58.0, EMBER[1] + 6.0)
    a = math.radians(186.0)
    L_ = 52.0 * (1 - 0.18)
    mid = (base[0] + math.cos(a) * 52.0 * 0.72, base[1] + math.sin(a) * 52.0 * 0.72)
    curl = (mid[0] + math.cos(math.radians(186.0 + 35)) * 52.0 * 0.22, mid[1] + math.sin(math.radians(186.0 + 35)) * 52.0 * 0.22)
    return base, curl


def _wisp_x(y_world, t, T):
    """x of the smoke wisp at a given height (the tilt keeps the wisp centered on x = 540)."""
    base, tip = _ember_tip()
    return tip[0] + L.curl_x(max(0.0, tip[1] - 3 - y_world), L.tglob(T, t), seed=4)


def _cam_d(t, T):
    d0 = _d_start(T)
    k = ease("inout", inv_lerp(d0, T_TILT, t))
    z = lerp(3.9, 4.4, k)
    pl = _place(t, T)
    if 0 <= pl < 3:
        z *= 1.0 + 0.035 * (pl + 1)
    kt = ease("inout", inv_lerp(T_TILT, T.duration, t))     # tilt up with the smoke, settling on the cut
    tilt = kt
    z = lerp(z, 3.0, kt)
    base, tip = _ember_tip()
    y0 = tip[1] - (1180.0 - 960.0) / z                          # ember low-center, smoke rises up the frame
    y = lerp(y0, tip[1] - 860.0, tilt)
    x = lerp(tip[0] + 6.0, _wisp_x(y, t, T), ease("inout", inv_lerp(T_TILT, T_TILT + 0.35, t)))
    return Camera(x, y, z)


def _macro_place(f, pl, t):
    """Background detail that tells the four places apart (same framing, same match)."""
    a = 0.55
    if pl <= 0:                # cobbles: rows of flattened stones receding to the horizon
        y = MG + 4.0
        for r in range(7):
            hgt = 5.0 + 4.0 * r
            wdt = 26.0 + 16.0 * r
            for c in range(-12, 13):
                x = 520 + c * (wdt + 4) + ((wdt + 4) / 2 if r % 2 else 0)
                draw.rect(f, x - wdt / 2, y, wdt, hgt, 1.0 + 0.25 * r, WHITE, 0.16 + 0.05 * r, radius=hgt * 0.45)
            y += hgt + 3.0
    elif pl == 1:              # bridge: rail posts and a top rail behind
        for c in range(-4, 6):
            x = 420 + c * 70
            draw.line(f, (x, MG - 4), (x, MG - 170), 2.4, WHITE, a)
        draw.line(f, (100, MG - 170), (1000, MG - 170), 3.0, WHITE, a)
        draw.line(f, (100, MG - 120), (1000, MG - 120), 1.6, WHITE, a * 0.6)
    elif pl == 2:              # stairwell: the match on a step edge, the next step below
        draw.line(f, (100, MG + 4), (720, MG + 4), 3.0, WHITE, 0.8)
        draw.line(f, (720, MG + 4), (720, MG + 74), 2.6, WHITE, 0.8)
        draw.line(f, (720, MG + 74), (1100, MG + 74), 3.0, WHITE, 0.7)
        draw.line(f, (100, MG - 70), (1000, MG - 70), 1.6, WHITE, 0.35)
        draw.line(f, (-100, MG - 150), (1000, MG - 150), 1.2, WHITE, 0.25)
    else:                      # parking: painted bay line under the match, a tire behind
        draw.stroke(f, [(380, MG + 2), (640, MG + 2), (700, MG + 60), (330, MG + 60)], 2.4, WHITE, 0.7, closed=True)
        draw.line(f, (360, MG + 30), (668, MG + 30), 1.0, WHITE, 0.3)
        draw.circle(f, (700, MG - 70), 72, 4.0, WHITE, 0.6)
        draw.circle(f, (700, MG - 70), 30, 2.4, WHITE, 0.5)


def _macro_chalk():
    """Chalk outline of the victim's forearm + hand, lying flat beside the match."""
    if "macro" not in _OCACHE:
        y = MG + 20.0
        _OCACHE["macro"] = ([[(EMBER[0] + 760.0, y + 8.0), (EMBER[0] + 92.0, y)]], (EMBER[0] + 3000.0, y), 1.0)
    return _OCACHE["macro"]


def shot_d(f, t, T):
    cam = _cam_d(t, T)
    f.set_camera(cam)
    pl = _place(t, T)
    e = _ember_amt(t, T)
    b, r = L.smooth_siren(t, rate=1.3)
    # far bokeh: police lights + a lamp, deep out of focus (emissive only)
    for (x, col, amt, rr) in ((300.0, BLUE, b, 120), (380.0, CRIMSON, r, 110), (860.0, AMBER, 0.55, 90), (-60.0, AMBER, 0.4, 80)):
        if amt > 0.02:
            draw.glow_dot(f, (x, MG - 120), rr, col, 0.55 * amt, core=False)
    lights = [Light.radial(EMBER, 260, intensity=1.0), Light.radial((300, MG - 100), 420, intensity=0.35 * b)]
    with f.lit(lights, ambient=min(1.0, 0.18 + 0.7 * pulse(t, _d_start(T) + 0.01, 0.015, 0.2)), soften=3.0):
        draw.line(f, (-400, MG), (1500, MG), 2.0, WHITE, 0.5)
        _macro_place(f, pl, t)
        lines, hc, hr = _macro_chalk()
        fx.chalk_outline(f, lines, hc, hr, body_w=24.0, line_px=4.0, seed=11)
        fx.splashes(f, t, MG + 30, 200, 900, rate=1.1, alpha=0.6, size=0.7)
    with f.camera(Camera(540, 960 + (cam.y - EMBER[1]) * 0.3, 1.25)):
        with L.soft(f, 3.0):
            fx.rain(f, t, density=0.8, alpha=0.5, seed=61)
    base = (EMBER[0] + 58.0, EMBER[1] + 6.0)
    tip = props.match(f, base, angle=186.0, s=1.0, burnt=1.0, t=t, seed=3)
    draw.glow_dot(f, tip, 70, AMBER, 0.75 * e)
    draw.glow_dot(f, tip, 22, AMBER, 1.0 * min(1.0, e))
    draw.circle(f, tip, 4.0, 1, AMBER, min(1.0, e), fill_it=True, glow=1.0)
    fx.reflection(f, tip[0], MG + 4, 60, 18, AMBER, 0.55 * min(1.0, e), t, seed=2)
    hiss = pulse(t, T.at("burnt") + 0.03, 0.02, 0.2)
    if hiss > 0.03:                                              # the raindrop that hits it
        for i in range(6):
            sa = math.radians(-170 + 160 * i / 5)
            draw.line(f, (tip[0] + math.cos(sa) * 8, tip[1] - 2 + math.sin(sa) * 4),
                      (tip[0] + math.cos(sa) * (16 + 20 * (1 - hiss)), tip[1] - 2 + math.sin(sa) * 9 - 14 * hiss),
                      1.6, WHITE, 0.9 * hiss)
    one = pulse(t, _d_start(T) + 0.01, 0.015, 0.2)              # evidence photo on "One"
    if one > 0.01:
        L.flash_pop(f, 0.8 * one, src=(1260.0, 600.0))
    puff = 1.0 + 0.8 * pulse(t, T.at("burnt") + 0.05, 0.05, 0.5)
    L.curl_wisp(f, tip[0], tip[1] - 3, L.tglob(T, t), height=2300.0, seed=4, alpha=min(0.95, 0.68 * puff), w=2.3,
                floor=0.55)


# ============================================================================ module API
def render(f, t, T):
    tf = L.frame_t(t)
    if tf < T_B:
        shot_a(f, t, T)
    elif tf < T_C:
        shot_b(f, t, T)
    elif tf < _d_start(T):
        shot_c(f, t, T)
    else:
        shot_d(f, t, T)


def cues(T):
    ld = _landings(T)
    g = T.at("gave")
    fast = T.at("fast")
    c = [
        Cue(0.0, "whoosh", gain_db=-10, size=0.5),
        Cue(0.55, "radio_static", gain_db=-16, pan=0.3),
        Cue(T_B + 0.06, "radio_static", gain_db=-13, pan=0.15),
        Cue(g + 0.01, "paper_rustle", gain_db=-12, pan=0.05),
        Cue(g + 0.26, "footstep", gain_db=-11, pan=0.0, weight=0.2, wet=1),
    ]
    for i in range(3):                                         # the cop walks off: even steps
        c.append(Cue(fast + 0.16 + 0.27 * i, "footstep", gain_db=-12 - 2 * i, pan=0.25 + 0.2 * i, weight=0.6, wet=1))
    for i, tl in enumerate(ld):
        c.append(Cue(tl - 0.01, "camera_shutter", gain_db=-6 if i % 2 == 0 else -9, pan=(-0.2 if i % 2 else 0.2)))
        if i:
            c.append(Cue(tl - 0.3, "whoosh", gain_db=-16, size=0.25))
    c += [Cue(_d_start(T), "camera_shutter", gain_db=-7, pan=0.2),
          Cue(_d_start(T) + 0.03, "ember_sizzle", gain_db=-10),
          Cue(T.at("burnt") + 0.02, "ember_sizzle", gain_db=-4)]
    for tl in _inserts(T):
        c.append(Cue(tl, "ember_sizzle", gain_db=-17))
    return c


def motion_blur(t, T):
    if t < T_LAND - 0.08:
        return 3
    if T_TILT + 0.25 < t < T.duration - 0.3:
        return 2
    if T_C <= t < _d_start(T) and _speed_c(t, T) > 2500:
        return 2
    return 1
