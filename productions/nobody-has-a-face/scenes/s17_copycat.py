"""S17 - Habits Can Be Learned (10.417 s) - the copycat.

"Case closed. Except... habits can be learned. Copied. Worn like a mask.
 And outside, it was still raining."

Shot plan (scene seconds)
  0.00-1.86  IN: his head ring (S16 OUT: r = 200 px at screen centre) becomes the top of a white
             umbrella seen straight from above; the camera pulls up: the precinct steps in the
             door's amber spill, a few umbrellas, and the police car - light bar dark - pulling
             away from the curb into the rain on "Case closed."
  1.86-2.12  whip down (vertical streak) to street level, high in the rain.
  2.12-3.50  crane down a long wet street (lamps receding to the vanishing point) to the curb:
             a crowd of identical figures under white umbrellas.
  3.50-6.90  push in on the one at the centre with no open umbrella: he raises a matchbook on
             "learned", strikes LEFT-handed on "Copied" (the same match_strike) - the amber flare
             lights his hollow head from below - and opens a RED umbrella on "Worn like a mask".
  6.90-10.42 the camera eases back to a static wide and holds still: he turns and walks away with a
             limp (short step, long step) up the street into the dark; the rain kills the flame on
             "raining"; the street sinks into darkness until only the red umbrella recedes.
             OUT: the red umbrella small near the top of the frame (~(575, 455)), swallowed by dark.
"""
import math

from engine import *
from scenes._lib_s16_s18 import (RING_R, Gait, Persp, cam_lerp, ek, log_zoom, rain_top,
                                 ring_to_umbrella, streak, tglob)

# ---------------------------------------------------------------- beats
T_WHIP0, T_WHIP1 = 1.86, 2.12
T_CRANE1 = 3.50
T_BACK0, T_BACK1 = 6.55, 7.50
T_TURN0, T_TURN1 = 6.82, 6.98
T_WALK = 6.95
T_LAST = 10.375                          # last frame (249 / 24)

# ================================================================ shot 1: top-down at the precinct
U0, U0_R = (540.0, 960.0), 60.0          # the ring becomes this umbrella
Z_TOP0 = RING_R / U0_R                   # 3.33: identical ring size at the cut
TOP_END = Camera(560.0, 1040.0, 0.95)
DOOR_X0, DOOR_X1, FACADE_Y = 492.0, 588.0, 700.0
STEPS = [730.0, 760.0, 790.0, 820.0, 850.0]
CURB_Y = 1062.0
TOP_LAMPS = [(170.0, 1046.0), (905.0, 1046.0)]
TOP_UMBRELLAS = [((372.0, 930.0), 56.0, 12.0, (-14.0, 4.0)), ((716.0, 902.0), 58.0, 30.0, (10.0, 6.0)),
                 ((858.0, 992.0), 55.0, 5.0, (-6.0, -3.0)), ((236.0, 1004.0), 57.0, 21.0, (-26.0, 2.0))]
CAR_Y = 1186.0


def _car_x(t):
    tt = max(0.0, t - 0.22)
    return 452.0 + 0.5 * 660.0 * tt * tt


def _top_cam(t):
    k = ek("inout3", 0.0, 1.78, t)
    c0 = Camera(U0[0], U0[1], Z_TOP0)
    return Camera(lerp(c0.x, TOP_END.x, k), lerp(c0.y, TOP_END.y, k), log_zoom(c0.zoom, TOP_END.zoom, k))


def _draw_top(f, t, reveal):
    """The precinct, its steps and the street seen from straight above."""
    cx = _car_x(t)
    lights = [Light.radial(p, 380, intensity=0.9) for p in TOP_LAMPS]
    lights.append(Light.poly([(DOOR_X0, FACADE_Y), (DOOR_X1, FACADE_Y), (650, 880), (430, 880)], 0.9))
    lights.append(Light.cone((cx + 250, CAR_Y), 0.0, 38, 560, intensity=0.9))
    lights = [Light(L_.kind, **dict(L_.kw, intensity=L_.kw["intensity"] * reveal)) for L_ in lights]
    with f.lit(lights, ambient=0.2 * reveal, soften=3.0):
        a = 1.0
        # precinct: roof edge, cornice, roof hatch and vents, the open door
        draw.line(f, (-400, FACADE_Y), (DOOR_X0, FACADE_Y), 3.4, WHITE, a)
        draw.line(f, (DOOR_X1, FACADE_Y), (1500, FACADE_Y), 3.4, WHITE, a)
        draw.line(f, (-400, FACADE_Y - 22), (1500, FACADE_Y - 22), 2.0, WHITE, a * 0.6)
        draw.rect(f, 250, 430, 150, 110, 2.4, WHITE, a * 0.6)
        draw.line(f, (250, 430), (400, 540), 1.4, WHITE, a * 0.35)
        for i in range(3):
            draw.circle(f, (700 + 70 * i, 520), 22, 2.0, WHITE, a * 0.5)
        # steps (top-down: parallel edges between two side walls)
        draw.line(f, (440, FACADE_Y), (440, 860), 2.6, WHITE, a)
        draw.line(f, (640, FACADE_Y), (640, 860), 2.6, WHITE, a)
        for y in STEPS:
            draw.line(f, (440, y), (640, y), 2.2, WHITE, a * 0.8)
        # sidewalk slabs, curb + gutter, lane dashes, far curb
        for i in range(-3, 14):
            draw.line(f, (i * 110.0, 870), (i * 110.0, CURB_Y - 6), 1.2, WHITE, a * 0.25)
        draw.line(f, (-400, CURB_Y), (1500, CURB_Y), 3.0, WHITE, a)
        draw.line(f, (-400, CURB_Y + 16), (1500, CURB_Y + 16), 1.6, WHITE, a * 0.5)
        for i in range(-3, 16):
            draw.line(f, (i * 120.0, 1300), (i * 120.0 + 64, 1300), 2.4, WHITE, a * 0.55)
        draw.line(f, (-400, 1520), (1500, 1520), 3.0, WHITE, a * 0.8)
        # lamp posts from above: a ring and an arm over the road
        for (x, y) in TOP_LAMPS:
            draw.circle(f, (x, y - 30), 9, 2.4, WHITE, a)
            draw.line(f, (x, y - 30), (x, y + 70), 3.0, WHITE, a)
        fx.ripples(f, t, -300, 1080, 1400, 1500, rate=0.9, seed=31, alpha=0.5, squash=1.0)
        fx.ripples(f, t + 3.1, -300, 880, 1400, 1050, rate=0.5, seed=37, alpha=0.4, squash=1.0)
        # the others leaving the precinct (white umbrellas from above)
        for i, (c, R, rot, v) in enumerate(TOP_UMBRELLAS):
            p = (c[0] + v[0] * t, c[1] + v[1] * t)
            props.umbrella_top(f, p, R, rot + 4 * math.sin(t * 1.3 + i), WHITE)
        # the police car pulls away from the curb - light bar dark, headlights on
        props.car_top(f, (cx, CAR_Y), angle=-4.0 * ek("inout", 0.2, 0.9, t) + 4.0 * ek("inout", 0.9, 1.6, t),
                      s=1.0, police=True, t=t, headlights=reveal, siren_on=0.0)
    # emissive lamp heads and the door's amber spill on the steps
    for (x, y) in TOP_LAMPS:
        draw.glow_dot(f, (x, y + 70), 150, AMBER, 0.75 * reveal)
    draw.gradient_fill(f, [(DOOR_X0, FACADE_Y), (DOOR_X1, FACADE_Y), (650, 880), (430, 880)],
                       [(0.0, AMBER, 0.22 * reveal), (1.0, AMBER, 0.0)], (540, FACADE_Y), (540, 880),
                       glow=0.4 * reveal)


def _shot_top(f, t, cam):
    f.set_camera(cam)
    reveal = ek("inout", 0.08, 0.75, t)
    _draw_top(f, t, reveal)
    ring_to_umbrella(f, U0, U0_R, ek("inout", 0.0, 0.42, t))
    rain_top(f, t, n=170, seed=31, alpha=0.5 * ek("inout", 0.1, 0.7, t), center=(540.0, 960.0))


# ================================================================ shots 2-4: the street
ST = Persp((560.0, 400.0), 1455.0, 0.88)  # static wide == world; front row feet at y 1455, s 0.88
CURB_K = 0.76                            # cross-street curb: road beyond, crowd on the near side
ROAD_X = 600.0
WALL_X = 930.0
WALL_H = 2400.0
LAMPS = [(-690.0, 0.62, 1), (690.0, 0.42, -1), (-690.0, 0.29, 1), (690.0, 0.20, -1),
         (-690.0, 0.14, 1), (690.0, 0.10, -1), (-690.0, 0.07, 1)]
NEAR_LAMP = (520.0, 1.10, -1)
# the crowd: (X, k, holds-with-left?) - three loose rows; the centre of rows B/C stays open
CROWD = [(-455.0, 1.0, 0), (-235.0, 1.0, 1), (205.0, 1.0, 0), (425.0, 1.0, 1),
         (-390.0, 0.885, 1), (-150.0, 0.885, 0), (150.0, 0.885, 1), (380.0, 0.885, 0),
         (-560.0, 0.80, 0), (-310.0, 0.80, 1), (300.0, 0.80, 0), (545.0, 0.80, 1)]
HE_X = -20.0                             # the copycat: front row, centre (screen x 540)
HE_LANE = 40.0                           # lateral position of his walk up the street
Z0 = 792.0                               # depth of the front row (steps of 100 -> rows B, C)
D_CURB = 230.0                           # walked distance at the cross-street curb
REC_E, REC_L = 100.0, 194.0              # stylised recession past the curb: the dark pulls him away


def _depth_k(d):
    """Depth factor after walking d units away: physical through the crowd, then a smooth
    log-space ramp (quadratic onset, then a constant shrink per step) up the dark street."""
    e = max(0.0, d - D_CURB)
    return Z0 / (Z0 + d) * math.exp(-(e * e / (e + REC_E)) / REC_L)


def _swallow(t):
    """0 -> 1: the street sinks into darkness after the flame dies."""
    return ek("inout", 8.95, 9.95, t)


W_CRANE0 = Camera(560.0, 270.0, 1.38)    # high in the rain, on the far end of the street
MED = Camera(540.0, 1190.0, 1.75)
MED2 = Camera(540.0, 1175.0, 1.98)
WIDE = Camera(540.0, 960.0, 1.0)


def _street_cam(t, beats):
    if t < T_CRANE1:
        k = ek("inout3", T_WHIP1 - 0.1, T_CRANE1, t)
        return cam_lerp(W_CRANE0, MED, k, kz=ek("inout", T_WHIP1, T_CRANE1, t))
    if t < T_BACK0:
        k = ek("inout", T_CRANE1, T_BACK0, t)
        cam = cam_lerp(MED, MED2, k)
        flare = pulse(t, beats[1], 0.02, 0.35)
        return cam.shaken(t, amp=2.0 + 7.0 * flare, rot_amp=0.12 + 0.4 * flare, freq=1.1, seed=5)
    k = ek("inout3", T_BACK0, T_BACK1, t)
    start = MED2.shaken(T_BACK0, amp=2.0, rot_amp=0.12, freq=1.1, seed=5)
    return cam_lerp(start, WIDE, k)


# ---------------------------------------------------------------- the copycat's performance
def _beats(T):
    return T.at("learned"), T.at("copied"), T.at("worn"), T.at("raining")


def _crowd_pose(i, t):
    X, k, left = CROWD[i]
    s = ST.s0 * k
    feet = ST.P(X, 0, k)
    p = rig.stand(feet[0], feet[1], facing=0, s=s)
    p = rig.breathe(p, t, amt=0.8, seed=40 + 3 * i)
    J = rig.solve(p)
    side = "l" if left else "r"
    sx = 1 if left else -1
    hand = (J["neck"][0] + sx * 8 * s, J["neck"][1] + 4 * s + 3 * math.sin(t * 1.1 + i))
    p = rig.reach(p, side, hand)
    return p, side, k


def _he_front(t, beats):
    """Front view at the curb: matchbook up, LEFT-hand strike, pocket, red umbrella up."""
    learned, copied, worn, _ = beats
    feet = ST.P(HE_X, 0, 1.0)
    s = ST.s0
    p = rig.stand(feet[0], feet[1], facing=0, s=s)
    p = rig.breathe(p, t, amt=0.8, seed=77)
    J = rig.solve(p)
    nx, ny = J["neck"]
    # head: bowed, looks down at the book, lifts with the flame, tips up under the canopy
    head = 10 * ek("inout", 3.2, learned, t) - 4 * ek("inout", copied, copied + 0.3, t) \
        - 8 * ek("inout", worn, worn + 0.6, t)
    p = p.copy(head=p.head + head)
    # RIGHT hand (screen-left): matchbook to the chest, pocket it, then the umbrella
    book = (nx - 30 * s, ny + 70 * s)
    rest_r = J["rh"]
    up_r = ek("inout3", learned - 0.35, learned + 0.15, t)
    r_t = lerp(rest_r, book, up_r)
    pocket = ek("inout", copied + 0.35, copied + 0.6, t)
    hip_r = (J["hip"][0] - 34 * s, J["hip"][1] - 6 * s)
    r_t = lerp(r_t, hip_r, pocket)
    grab = ek("inout", copied + 0.62, worn - 0.12, t)
    raise_ = (nx - 12 * s, ny + 2 * s)
    r_t = lerp(r_t, raise_, grab)
    p = rig.reach(p, "r", r_t)
    # LEFT hand (screen-right): to the book, tear, wind up, strike across the strip, hold up
    rest_l = J["lh"]
    tear = ek("inout", learned + 0.3, copied - 0.32, t)
    at_book = (book[0] + 26 * s, book[1] + 8 * s)
    l_t = lerp(rest_l, at_book, tear)
    wind = ek("out", copied - 0.3, copied - 0.1, t)
    l_t = lerp(l_t, (at_book[0] + 34 * s, at_book[1] + 14 * s), wind)
    strike = ek("out3", copied - 0.1, copied + 0.04, t)
    l_t = lerp(l_t, (book[0] - 6 * s, book[1] + 26 * s), strike)
    hold = ek("inout", copied + 0.06, copied + 0.45, t)
    l_t = lerp(l_t, (nx + 34 * s, ny + 36 * s), hold)
    lower = ek("inout", worn + 0.2, worn + 0.9, t)
    l_t = lerp(l_t, (nx + 50 * s, ny + 110 * s), lower)
    p = rig.reach(p, "l", l_t)
    return p


def _match_angle_front(t, beats):
    learned, copied, worn, _ = beats
    a = lerp(-80.0, -160.0, ek("out", copied - 0.1, copied + 0.04, t))   # dragged across the strip
    return lerp(a, -100.0, ek("inout", copied + 0.04, copied + 0.4, t))


# walk away: the same short step / long step (re-timed limp), facing right, up the lane
GAIT = Gait(0.0, 0.0, ST.s0, 1, limp=0.85, stride=0.9, arm=0.0, t0=T_WALK + 0.12, h0=1.0,
            cycle=0.78)                  # the engine's limp rhythm: quick stance on the LEFT leg
_G_X0 = GAIT.pose(T_WALK).x


def _he_walk(t, beats):
    """Side view walking away; returns (pose, depth k, walked distance)."""
    g = GAIT.pose(t)
    d = max(0.0, (g.x - _G_X0))
    k = _depth_k(d)
    feet = ST.P(HE_X + (HE_LANE - HE_X) * ek("inout", 0.0, 160.0, d), 0, k)
    s = ST.s0 * k
    p = g.copy(s=s)
    J1 = rig.solve(p.copy(x=0.0, y=0.0))
    low1 = max(J1["lf"][1], J1["rf"][1])
    p = p.copy(x=feet[0], y=feet[1] - low1)
    J = rig.solve(p)
    p = rig.reach(p, "r", (J["neck"][0] + 16 * s, J["neck"][1] - 2 * s))          # umbrella hand
    p = rig.reach(p, "l", (J["hip"][0] + 30 * s, J["hip"][1] - 20 * s))           # the match, low
    return p, k, d


def _he_pose(t, beats):
    if t < T_TURN0:
        return _he_front(t, beats), 1.0
    w, k, d = _he_walk(t, beats)
    if t < T_TURN1:
        return _he_front(T_TURN0, beats).blend(w, ek("inout", T_TURN0, T_TURN1, t)), 1.0
    return w, k


def _umbrella_state(t, beats, p, J):
    """(hand, angle, open_) of THE red umbrella."""
    learned, copied, worn, _ = beats
    s = p.s
    if t < copied + 0.62:
        # furled, hooked over his right forearm
        el, hd = J["re"], J["rh"]
        hook = (lerp(el[0], hd[0], 0.45), lerp(el[1], hd[1], 0.45))
        return hook, 92.0, 0.0
    hand = J["rh"]
    up = ek("inout3", copied + 0.7, worn - 0.02, t)          # swings up through the outside
    ang = lerp(95.0, 270.0, up) if t < T_TURN0 else lerp(270.0, 272.0, ek("inout", T_TURN0, T_TURN1, t))
    op = ease("outback", inv_lerp(worn - 0.02, worn + 0.42, t))
    return hand, ang, clamp(op, 0.0, 1.08)


def _flame_state(t, beats):
    """(lit 0..1, flare 0..1, smoke) of his match."""
    learned, copied, worn, raining = beats
    if t < copied - 0.02:
        return 0.0, 0.0, 0.0
    flare = pulse(t, copied, 0.03, 0.32)
    lit = ek("out", copied - 0.02, copied + 0.08, t)
    lit *= 1.0 - ek("in", raining - 0.15, raining + 0.12, t)
    smoke = ek("inout", raining, raining + 0.2, t) * (1 - ek("inout", raining + 0.5, raining + 1.4, t))
    return lit, flare, smoke


def _draw_street(f, t, T, beats, cam):
    learned, copied, worn, raining = beats
    sw = _swallow(t)
    hp, k_he = _he_pose(t, beats)
    J = rig.solve(hp)
    lit, flare, smoke = _flame_state(t, beats)
    m_ang = _match_angle_front(t, beats) if t < T_TURN1 else lerp(-60.0, -75.0, ek("inout", T_TURN1, 7.4, t))
    m_s = 0.95 * hp.s
    m_base = J["lh"]
    m_tip = (m_base[0] + math.cos(math.radians(m_ang)) * 52 * m_s,
             m_base[1] + math.sin(math.radians(m_ang)) * 52 * m_s)

    # ---------------- lights
    lights = []
    lamp_pts = []
    for (X, k, fc) in LAMPS:
        base = ST.P(X, 0, k)
        lp = (base[0] + fc * 120 * k, base[1] - 880 * k + 62 * k)
        lamp_pts.append((lp, k, base))
        lights.append(Light.cone(lp, 90, 62, 980 * k, intensity=1.0 - sw))
    nb = ST.P(NEAR_LAMP[0], 0, NEAR_LAMP[1])
    near_lp = (nb[0] - 120 * NEAR_LAMP[1], nb[1] - 880 * NEAR_LAMP[1] + 62 * NEAR_LAMP[1])
    lights.append(Light.cone(near_lp, 104, 58, 1150, intensity=0.95 * (1 - sw)))
    if lit > 0:
        lights.append(Light.radial(m_tip, (300 + 260 * flare) * hp.s, intensity=lit))
    ambient = lerp(0.16, 0.0, sw)

    # ---------------- light haze (accent) behind everything
    for (lp, k, base) in lamp_pts:
        fx.light_cone(f, lp, 90, 56, 900 * k, AMBER, 0.09 * (1 - sw), glow=0.3 * (1 - sw))
    fx.light_cone(f, near_lp, 104, 52, 1100, AMBER, 0.07 * (1 - sw), glow=0.25 * (1 - sw))

    order = sorted(range(len(CROWD)), key=lambda j: CROWD[j][1])
    behind = [i for i in order if CROWD[i][1] <= k_he + 1e-6]
    front = [i for i in order if CROWD[i][1] > k_he + 1e-6]

    def crowd(ids):
        for i in ids:
            p, side, k = _crowd_pose(i, t)
            Jc = rig.solve(p)
            rig.draw_figure(f, p)
            props.umbrella(f, Jc[side + "h"], angle=-90 + 3 * math.sin(t * 0.9 + i), R=118 * p.s, open_=1.0,
                           color=WHITE, t=t, seed=i, wobble=1.0)

    with f.lit(lights, ambient=ambient, soften=3.0):
        _draw_city(f, t, sw)
        for (X, k, fc) in LAMPS:
            props.streetlamp(f, ST.P(X, 0, k), height=880, s=k, on=1.0 - sw, facing=fc, t=t,
                             seed=int(k * 100), glow_r=260)
        props.streetlamp(f, nb, height=880, s=NEAR_LAMP[1], on=1.0 - sw, facing=-1, t=t, seed=3, glow_r=260)
        fx.rain(f, t, density=1.0, wind=6, seed=17, alpha=0.9)
        crowd(behind)
        rig.draw_figure(f, hp)
        if t < copied + 0.6:                                        # the matchbook in his right hand
            props.matchbook(f, (J["rh"][0] - 4 * hp.s, J["rh"][1] - 2 * hp.s), angle=8, s=0.17 * hp.s,
                            open_=1.0, n=10, missing={0, 1, 2, 3},
                            alpha=1.0 - ek("inout", copied + 0.4, copied + 0.6, t))
    rain_out = 0.35 * (1 - sw)
    if rain_out > 0.01:
        fx.rain(f, t + 0.37, density=0.5, wind=6, seed=29, alpha=rain_out)
    fx.splashes(f, t, ST.P(0, 0, 1.0)[1] + 2, -60, 1140, rate=0.8, seed=7, alpha=0.6 * (1 - sw))
    for (lp, k, base) in lamp_pts:                                  # wet reflections of the lamps
        gy = ST.P(0, 0, k)[1]
        fx.reflection(f, lp[0], gy, length=420 * k, width=60 * k, color=AMBER, alpha=0.4 * (1 - sw), t=t,
                      seed=int(k * 50))

    # ---------------- THE red umbrella and the match (accents, drawn over the light)
    uh, ua, uo = _umbrella_state(t, beats, hp, J)
    fade_end = 1.0 - 0.88 * ek("inout", 9.75, T_LAST, t)
    props.umbrella(f, uh, angle=ua, R=118 * hp.s, open_=uo, color=CRIMSON, t=t, seed=9,
                   wobble=0.6, alpha=fade_end)
    if t > T_TURN1 and k_he < 0.9:
        gy = J["lf"][1]
        fx.reflection(f, J["head"][0], gy + 4 * hp.s, length=380 * hp.s, width=90 * hp.s, color=CRIMSON,
                      alpha=0.5 * fade_end, t=t, seed=4)
    if t > copied - 0.05 and (lit > 0 or smoke > 0):
        props.match(f, m_base, angle=m_ang, length=52, s=m_s, lit=lit, flare=flare,
                    burnt=ek("inout", raining - 0.1, raining + 0.3, t), smoke_amt=smoke, t=tglob(T, t), seed=7)
    elif t > copied - 0.6 and t < copied:
        props.match(f, m_base, angle=m_ang, length=52, s=m_s, t=t, seed=7)
    if front:
        with f.lit(lights, ambient=ambient, soften=3.0):
            crowd(front)


def _draw_city(f, t, sw):
    """Receding street: curbs, centre dashes, sidewalks, facades with a few amber windows."""
    a = 1.0
    kmin = 0.012
    # cross-street curb the crowd stands behind, and the near sidewalk edge
    yc = ST.P(0, 0, CURB_K)[1]
    draw.line(f, (-300, yc), (1380, yc), 2.8, WHITE, a)
    draw.line(f, (-300, yc + 18), (1380, yc + 18), 1.4, WHITE, a * 0.45)
    # road edges and sidewalks receding to the vanishing point
    for sx in (-1, 1):
        draw.line(f, ST.P(sx * ROAD_X, 0, CURB_K), ST.P(sx * ROAD_X, 0, kmin), 2.6, WHITE, a * 0.9)
        draw.line(f, ST.P(sx * WALL_X, 0, CURB_K), ST.P(sx * WALL_X, 0, kmin), 2.2, WHITE, a * 0.7)
        draw.line(f, ST.P(sx * WALL_X, WALL_H, 1.2), ST.P(sx * WALL_X, WALL_H, kmin), 2.0, WHITE, a * 0.45)
        # facade bays and windows
        kk = 0.74
        bay = 0
        while kk > 0.05:
            k2 = kk / 1.32
            draw.line(f, ST.P(sx * WALL_X, 0, kk), ST.P(sx * WALL_X, WALL_H, kk), 1.8, WHITE, a * 0.5)
            for row in range(5):
                h0 = 380 + row * 380
                ka, kb = kk / 1.07, k2 * 1.07
                quad = [ST.P(sx * WALL_X, h0, ka), ST.P(sx * WALL_X, h0, kb),
                        ST.P(sx * WALL_X, h0 + 190, kb), ST.P(sx * WALL_X, h0 + 190, ka)]
                lit_w = hash01(91, sx, bay, row) < 0.22
                if lit_w:
                    draw.fill(f, quad, AMBER, 0.75 * (1 - sw), glow=0.7 * (1 - sw))
                else:
                    draw.stroke(f, quad, 1.4, WHITE, a * 0.45, closed=True)
            kk = k2
            bay += 1
    # centre-line dashes (perspective-correct lengths)
    kk = 0.74
    while kk > 0.03:
        k2 = kk / 1.16
        draw.line(f, ST.P(0, 0, kk), ST.P(0, 0, (kk + k2 * 2) / 3), 2.4 * max(0.35, kk), WHITE, a * 0.6)
        kk = k2 / 1.12
    fx.ripples(f, t, 120, ST.P(0, 0, 0.6)[1], 980, yc - 8, rate=0.7, seed=19, alpha=0.45)


def render(f, t, T):
    beats = _beats(T)
    if t < T_WHIP0:
        _shot_top(f, t, _top_cam(t))
        return
    if t < T_WHIP1:
        w = ek("inout", T_WHIP0, T_WHIP1, t)
        speed = math.sin(math.pi * inv_lerp(T_WHIP0, T_WHIP1, t))
        with streak(f, 0.0, 420.0 * speed):
            tc = _top_cam(t)
            _shot_top(f, t, Camera(tc.x, tc.y + 1920.0 * w / tc.zoom, tc.zoom))
            sc = _street_cam(t, beats)
            f.set_camera(Camera(sc.x, sc.y - 1920.0 * (1 - w) / sc.zoom, sc.zoom, sc.rot))
            _draw_street(f, t, T, beats, f.cam)
        return
    cam = _street_cam(t, beats)
    f.set_camera(cam)
    _draw_street(f, t, T, beats, cam)


def cues(T):
    learned, copied, worn, raining = _beats(T)
    c = [Cue(0.12, "car_door_close", gain_db=-9, pan=0.15),
         Cue(0.30, "car_away", gain_db=-6, pan=0.3, dur=2.4),
         Cue(T_WHIP0 + 0.02, "whoosh", gain_db=-12, size=0.5),
         Cue(learned - 0.05, "paper_rustle", gain_db=-16, pan=0.0),
         Cue(copied - 0.3, "paper_tear", gain_db=-13, pan=0.05),
         Cue(copied - 0.04, "match_strike", gain_db=-1, pan=0.05),
         Cue(copied + 0.02, "match_flare", gain_db=-5, pan=0.05),
         Cue(worn - 0.02, "umbrella_open", gain_db=-3, pan=-0.05),
         Cue(raining + 0.05, "flame_out", gain_db=-10, pan=0.05)]
    # his uneven steps receding up the street (wet), quieter with distance
    for (tt, side, foot) in GAIT.footfalls(T_WALK, T_LAST):
        d = max(0.0, foot[0] - _G_X0)
        k = _depth_k(d)
        gain = -4 + 20 * math.log10(max(k, 0.05)) - (5 if side == "l" else 0)
        c.append(Cue(tt, "footstep", gain_db=round(gain, 1), pan=0.05, weight=0.3 if side == "l" else 0.8, wet=1))
    return c


def motion_blur(t, T):
    copied = T.at("copied")
    if copied - 0.12 < t < copied + 0.05:          # the strike swipe
        return 3
    return 1
