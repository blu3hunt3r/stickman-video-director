"""S11 - The Chase (10.167 s) - escalation, the film's action peak.

IN : blue police-light flicker at the far end of a vertical night alley (vanishing point high).
     (S10 ended on the partner's badge spinning to a stop with a blue glint.)
Beat 1  0.00-3.30  alley mouth: the detective (back view) heaving for breath; THE red umbrella
                   turns the corner at the far end; anticipation crouch, launch.
Beat 2  3.30-7.32  chase montage, ~1 s per cut, handheld: run toward camera (limp) / fire-escape
                   zigzag climb under a blue street flicker, red umbrella slips over the roof /
                   rooftop leap against the moon ring (speed ramp), red umbrella far below /
                   laundry sheets, blue police light, a sheet wipes the frame.
Beat 3  7.32-10.17 dead end, nobody. A burnt match still smoking; he picks it up with his LEFT
                   hand on "caught"; macro on "warm match", push in.
OUT: the amber ember dot alone, centered at screen (540, 960) on black.
"""
import math

from engine import *
from . import _lib_s11_s13 as L

SEED = 11


def _cuts(T):
    return [0.0, T.at("I"), T.at("red"), T.at("every"), T.end("town") - 0.42, T.at("All"),
            T.at("warm"), T.duration]


# ----------------------------------------------------------------------------- A: alley mouth
def shot_mouth(f, t, T, lt, dur):
    ez = L.ek(lt, 0, dur, 0, 120, "inout3")
    P = L.Persp(ex=0, ey=-600, ez=ez, F=1000, cx=540, cy=480)
    cam = Camera(540, 960, 1.0, L.ek(lt, 0, dur, -1.4, 0.3)).shaken(t, amp=3.0, rot_amp=0.25, freq=0.6, seed=11)
    f.set_camera(cam)
    G = L.alley_geom(seed=3, hw=450.0, L=4200.0)
    Lz = G["L"]
    b = L.police_blue(t, rate=1.45)
    src = P.p(620, -150, Lz + 380)
    far_ground = P.p(0, 0, Lz)
    lights = [Light.cone(P.p(0, -300, Lz), 91, 46, 1750, intensity=0.25 + 0.75 * b),
              Light.radial(src, 520, intensity=0.4 + 0.6 * b)]
    puddles = ((-120, 1000, 160), (230, 1650, 220), (-220, 2400, 180))
    # THE red umbrella turns the far corner (never a figure: just the canopy, bobbing as carried)
    u_pos = None
    t_u0, t_u1, t_u2 = 1.35, 2.15, 2.85
    if t_u0 <= lt <= t_u2 + 0.1:
        if lt < t_u1:
            k = ease("inout", inv_lerp(t_u0, t_u1, lt))
            UX, UZ = lerp(-200, 110, k), lerp(3480, 3980, k)
        else:
            k = ease("in", inv_lerp(t_u1, t_u2, lt))
            UX, UZ = lerp(110, 900, k), lerp(3980, 4520, k)
        bob = 10 * abs(math.sin(lt * 2 * math.pi * 1.6))
        u_pos = (UX, -250 - bob, UZ)
    xc = P.p(450, 0, Lz)[0]
    # the detective at the alley mouth (back view): heaving breath -> notices -> crouch -> launch
    t_crouch, t_go = 2.45, 2.92
    Zf = 800.0
    if lt < t_go:
        base = rig.stand(0, 0, facing=0, s=1.0, la=10, ra=10, ll=6, rl=6)
        heave = math.sin(2 * math.pi * 1.15 * lt)           # chest heaving after the run
        base = rig.breathe(base, t, amt=1.8, seed=4).copy(
            la=12 + 7 * heave, ra=12 + 7 * heave, le=10 + 8 * heave, re=10 + 8 * heave,
            lk=4 + 6 * (0.5 - 0.5 * heave), rk=4 + 6 * (0.5 - 0.5 * heave),      # knees give as he exhales
            head=-3 + 2.5 * math.sin(lt * 1.3) - 3 * heave)
        if lt > 1.9:
            k = ease("out3", inv_lerp(1.9, 2.1, lt))
            base = base.copy(head=lerp(base.head, 0, k), la=base.la + 8 * k, ra=base.ra + 8 * k)
        if lt > t_crouch:
            k = ease("inout3", inv_lerp(t_crouch, t_go, lt))
            base = base.blend(base.copy(ll=19, rl=19, lk=17, rk=17, la=26, le=-34, ra=26, re=-34), k)
        fig, fs = L.pose_at(P, 60, Zf, base)
    else:
        u = lt - t_go
        fig, fs = L.run_at(P, 60 + 260 * u, Zf + 1300 * u * u + 420 * u, 0.35 + 3.0 * u, facing=1,
                           limp=0.35, lean=18)
    with f.lit(lights, ambient=0.27):
        L.draw_cross_street(f, P, G, t)
        L.draw_alley(f, P, G, t, puddles=puddles)
        for i, (X, Z, r) in enumerate(puddles):
            L.puddle_ripples(f, P, t, X, Z, r, seed=40 + i, alpha=0.5)
        L.draw_can(f, P, -360, 1300, alpha=0.9)
        L.draw_box(f, P, 250, 420, 2150, 2400, 160, alpha=0.9)
        if u_pos is not None:
            hand = P.p(*u_pos)
            ku = P.k(u_pos[2])
            with f.clipped(lambda c: c.rectangle(-2000, -2000, xc + 2000, 6000)):
                props.umbrella(f, hand, angle=-90 + 6 * math.sin(lt * 5), R=135 * ku, color=CRIMSON,
                               t=t, wobble=0.5)
        fx.rain(f, t, density=1.0, wind=6, seed=21)
        L.figure_cut(f, fig, gap=6)
    fx.light_cone(f, P.p(0, -250, Lz), 90, 36, 1500, BLUE, 0.10 * b, glow=0.4)
    draw.glow_dot(f, src, 380, BLUE, 0.55 * b + 0.12, core=False)
    fx.reflection(f, far_ground[0], far_ground[1], 520, 70, BLUE, 0.5 * b + 0.1, t)
    door = [d for d in G["doors"] if d[2] < 0 and 1100 < d[1] < 2600]
    if door:
        L.wall_lamp(f, P, -450, -300, door[0][1], side=-1)


# ----------------------------------------------------------------------------- B1: run toward camera
def shot_run_to_cam(f, t, T, lt, dur):
    ez = L.ek(lt, 0, dur, 0.0, -560.0 * dur, "inout")          # the camera retreats ahead of him
    P = L.Persp(ex=0, ey=-250, ez=ez, F=1000, cx=540, cy=800, fog=5600)
    cam = Camera(540, 960, 1.0, L.ek(lt, 0, dur, 1.8, -1.2, "inout")).shaken(t, amp=11, rot_amp=1.0, freq=2.5, seed=12)
    f.set_camera(cam)
    G = L.alley_geom(seed=8, hw=420.0, L=4600.0, z0=-900.0)
    Lz = G["L"]
    b = L.police_blue(t + 0.25, rate=1.7)
    Zf = 1420.0 - 1450.0 * lt
    Xf = -230 + 430 * ease("inout", lt / dur)
    fig, fs = L.run_at(P, Xf, Zf, 0.15 + 3.2 * lt, facing=1, limp=0.35, lean=20, bounce=12)
    lamp_specs = [(420, -330, 1300, 1), (-420, -330, 2500, -1)]
    lights = [Light.cone(P.p(0, -260, Lz), 92, 40, 1900, intensity=0.3 + 0.7 * b)]
    for (X, Y, Z, side) in lamp_specs:
        lights.append(Light.radial(P.p(X, Y, Z), 420 * P.k(Z) ** 0.6, intensity=0.85))
    with f.lit(lights, ambient=0.32):
        L.draw_cross_street(f, P, G, t, seed=9)
        L.draw_alley(f, P, G, t, puddles=((140, 900, 180), (-200, 1900, 200)))
        L.draw_can(f, P, 330, 700, alpha=0.9)
        L.draw_box(f, P, -400, -250, 1500, 1700, 140)
        fx.rain(f, t, density=1.1, wind=-8, seed=22)
        L.figure_cut(f, fig, gap=7)
    for (X, Y, Z, side) in lamp_specs:
        L.wall_lamp(f, P, X, Y, Z, side=side)
    fx.light_cone(f, P.p(0, -200, Lz), 90, 40, 1700, BLUE, 0.09 * b, glow=0.4)
    draw.glow_dot(f, P.p(0, -150, Lz + 300), 300, BLUE, 0.5 * b + 0.1, core=False)


# ----------------------------------------------------------------------------- B2: fire escape climb
LAND = [1900.0, 1620.0, 1340.0, 1060.0, 780.0]
ROOF_Y = 560.0
FE_X0, FE_X1 = 250.0, 830.0
ST_A, ST_B = 330.0, 750.0


def _fire_escape_2d(f, alpha=1.0):
    draw.line(f, (70, ROOF_Y - 30), (70, 2400), 3.0, WHITE, alpha * 0.8)
    draw.line(f, (1010, ROOF_Y - 30), (1010, 2400), 3.0, WHITE, alpha * 0.8)
    draw.line(f, (40, ROOF_Y - 30), (1040, ROOF_Y - 30), 3.4, WHITE, alpha)       # parapet cap
    draw.line(f, (60, ROOF_Y), (1020, ROOF_Y), 2.0, WHITE, alpha * 0.7)
    for j, y in enumerate(LAND):
        for wx in (150, 900):
            draw.rect(f, wx - 50, y - 230, 100, 170, 1.6, WHITE, alpha * 0.45)
        draw.rect(f, 380, y - 240, 80, 150, 1.6, WHITE, alpha * 0.4)
        draw.rect(f, 620, y - 240, 80, 150, 1.6, WHITE, alpha * 0.4)
        # landing platform + railing
        draw.line(f, (FE_X0, y), (FE_X1, y), 3.0, WHITE, alpha)
        draw.line(f, (FE_X0, y + 12), (FE_X1, y + 12), 1.6, WHITE, alpha * 0.7)
        draw.line(f, (FE_X0, y - 82), (FE_X1, y - 82), 2.2, WHITE, alpha * 0.85)
        for k in range(11):
            x = FE_X0 + k * (FE_X1 - FE_X0) / 10
            draw.line(f, (x, y), (x, y - 82), 1.3, WHITE, alpha * 0.6)
        if j + 1 < len(LAND):
            y2 = LAND[j + 1]
            a, b = ((ST_A, y), (ST_B, y2)) if j % 2 == 0 else ((ST_B, y), (ST_A, y2))
            draw.line(f, a, b, 2.4, WHITE, alpha * 0.9)
            draw.line(f, (a[0], a[1] - 70), (b[0], b[1] - 70), 1.8, WHITE, alpha * 0.7)   # hand rail
            n = 9
            for k in range(1, n):
                u = k / n
                x = a[0] + (b[0] - a[0]) * u
                yy = a[1] + (b[1] - a[1]) * u
                draw.line(f, (x - 14, yy), (x + 14, yy), 1.6, WHITE, alpha * 0.6)


def shot_fire_escape(f, t, T, lt, dur):
    cy = L.ek(lt, 0, dur, 1150, 880, "inout")
    cam = Camera(L.ek(lt, 0, dur, 570, 510), cy, 0.82, L.ek(lt, 0, dur, -2.0, 1.4)).shaken(
        t, amp=9, rot_amp=0.8, freq=2.2, seed=13)
    f.set_camera(cam)
    b = L.police_blue(t + 0.6, rate=1.6)
    # climb: flight 2 (right-up), turn on the landing, flight 3 (left-up)
    t1, t2 = 0.47, 0.57
    s = 0.86
    if lt < t1:
        u = lt / t1
        x = ST_A + (ST_B - ST_A) * u
        slope = (LAND[3] - LAND[2]) / (ST_B - ST_A)
        y_at = lambda xx: LAND[2] + (min(max(xx, ST_A), ST_B) - ST_A) * slope
        p = L.run_limp(lt, 0, 0, 900, facing=1, s=s, limp=0.35, lean=26, bounce=6)
        p = p.copy(x=x, ll=p.ll + 16, rl=p.rl + 16)
        p = L.on_slope(p, y_at)
    elif lt < t2:
        k = (lt - t1) / (t2 - t1)
        fac = 1 if k < 0.5 else -1
        p = rig.stand(ST_B + 20 * (1 - 2 * k), LAND[3], facing=fac, s=s, lean=12, ll=10, lk=30, rl=-10, rk=20,
                      la=40, le=60, ra=-20, re=40)
    else:
        u = (lt - t2) / (dur - t2) * 0.9
        x = ST_B + (ST_A - ST_B) * u
        slope = (LAND[4] - LAND[3]) / (ST_A - ST_B)
        y_at = lambda xx: LAND[3] + (min(max(xx, ST_A), ST_B) - ST_B) * slope
        p = L.run_limp(lt, 0, 0, 900, facing=-1, s=s, limp=0.35, lean=26, bounce=6)
        p = p.copy(x=x, ll=p.ll + 16, rl=p.rl + 16)
        p = L.on_slope(p, y_at)
    lights = [Light.cone((540, 2350), -90, 52, 2300, intensity=0.3 + 0.7 * b),
              Light.radial((540, 1250), 900, intensity=0.25)]
    with f.lit(lights, ambient=0.25):
        _fire_escape_2d(f)
        fx.rain(f, t, density=1.1, wind=5, seed=23)
        L.figure_cut(f, p, gap=6)
    fx.light_cone(f, (540, 2350), -90, 50, 2000, BLUE, 0.11 * b, glow=0.5)
    # THE red umbrella slips over the roof parapet above him on "red umbrella" (canopy only)
    if lt < 0.75:
        k = ease("in", inv_lerp(0.05, 0.7, lt))
        hand = (640 + 260 * k, ROOF_Y - 70 + 210 * k)
        with f.clipped(lambda c: c.rectangle(-500, -2000, 2200, 2000 + ROOF_Y - 32)):
            props.umbrella(f, hand, angle=-88 + 10 * k, R=110, color=CRIMSON, t=t, wobble=0.6)


# ----------------------------------------------------------------------------- B3: rooftop leap
ROOF_A, ROOF_B = 1180.0, 1240.0
EDGE_A, EDGE_B = 430.0, 650.0


def _roofs(f, t, alpha=1.0):
    # roof A (left)
    draw.line(f, (-700, ROOF_A), (EDGE_A, ROOF_A), 3.6, WHITE, alpha)
    draw.line(f, (-700, ROOF_A + 22), (EDGE_A, ROOF_A + 22), 1.8, WHITE, alpha * 0.6)
    draw.line(f, (EDGE_A, ROOF_A), (EDGE_A, 2600), 3.0, WHITE, alpha * 0.85)
    for r in range(4):
        for c in range(3):
            draw.rect(f, EDGE_A - 120 - c * 170, ROOF_A + 120 + r * 210, 70, 110, 1.5, WHITE, alpha * 0.4)
    tx = -120.0                                          # water tower
    draw.rect(f, tx - 70, ROOF_A - 330, 140, 150, 2.6, WHITE, alpha * 0.85)
    draw.stroke(f, [(tx - 80, ROOF_A - 330), (tx, ROOF_A - 400), (tx + 80, ROOF_A - 330)], 2.6, WHITE, alpha * 0.85)
    for dx in (-60, 60):
        draw.line(f, (tx + dx, ROOF_A - 180), (tx + dx * 1.2, ROOF_A), 2.2, WHITE, alpha * 0.7)
    draw.line(f, (tx - 66, ROOF_A - 90), (tx + 66, ROOF_A - 90), 1.6, WHITE, alpha * 0.5)
    draw.rect(f, 200, ROOF_A - 120, 50, 120, 2.2, WHITE, alpha * 0.8)    # chimney
    # roof B (right)
    draw.line(f, (EDGE_B, ROOF_B), (1900, ROOF_B), 3.6, WHITE, alpha)
    draw.line(f, (EDGE_B, ROOF_B + 22), (1900, ROOF_B + 22), 1.8, WHITE, alpha * 0.6)
    draw.line(f, (EDGE_B, ROOF_B), (EDGE_B, 2600), 3.0, WHITE, alpha * 0.85)
    for r in range(4):
        for c in range(3):
            draw.rect(f, EDGE_B + 60 + c * 170, ROOF_B + 120 + r * 210, 70, 110, 1.5, WHITE, alpha * 0.4)
    draw.rect(f, 1180, ROOF_B - 170, 150, 170, 2.4, WHITE, alpha * 0.8)    # roof door box
    draw.line(f, (1000, ROOF_B), (1000, ROOF_B - 300), 2.0, WHITE, alpha * 0.7)   # antenna
    draw.line(f, (970, ROOF_B - 240), (1030, ROOF_B - 240), 1.8, WHITE, alpha * 0.6)
    # the gap: depth slot converging toward the street far below
    vp = (540, 1760)
    for x0, y0 in ((EDGE_A, ROOF_A), (EDGE_B, ROOF_B)):
        draw.line(f, (x0, y0 + 30), (lerp(x0, vp[0], 0.62), lerp(y0, vp[1], 0.62)), 1.4, WHITE, alpha * 0.35)


def shot_leap(f, t, T, lt, dur):
    t_off, t_land, t_go = 0.22, 0.68, 0.84
    x_off, x_land = 412.0, 720.0
    s = 1.0
    if lt < t_off:
        x = 92 + (x_off - 92) * lt / t_off
        p = L.run_limp(lt, 0, ROOF_A, 0, facing=1, s=s, limp=0.3, lean=18, phase0=0.2 + 3.3 * lt)
        p = p.copy(x=x)
        if lt > t_off - 0.08:     # plant and spring
            k = ease("inout", inv_lerp(t_off - 0.08, t_off, lt))
            p = p.blend(p.copy(lean=26, ll=30, lk=60, rl=-30, rk=40, la=60, le=30, ra=-50, re=40), k)
            p = rig.on_ground(p, ROOF_A)
    elif lt < t_land:
        u = L.speed_ramp((lt - t_off) / (t_land - t_off), slow=0.55)
        x = x_off + (x_land - x_off) * u
        y0 = ROOF_A - 150 * s
        y1 = ROOF_B - 150 * s
        y = lerp(y0, y1, u) - 4 * 260 * u * (1 - u)
        leap = Pose(x=x, y=y, s=s, facing=1, lean=22, head=-6, la=125, le=25, ra=-70, re=35,
                    ll=62, lk=18, rl=-42, rk=78)
        tuck = Pose(x=x, y=y, s=s, facing=1, lean=14, head=0, la=60, le=60, ra=-30, re=50,
                    ll=70, lk=70, rl=20, rk=90)
        p = leap.blend(tuck, ease("inout", clamp((u - 0.55) / 0.45)))
    elif lt < t_go:
        k = ease("out3", inv_lerp(t_land, t_land + 0.1, lt)) - 0.6 * ease("inout", inv_lerp(t_land + 0.07, t_go, lt))
        x = x_land + 60 * ease("out3", inv_lerp(t_land, t_go, lt))
        p = rig.stand(x, ROOF_B, facing=1, s=s, lean=lerp(10, 34, k), ll=lerp(20, 58, k), lk=lerp(30, 100, k),
                      rl=lerp(-10, -20, k), rk=lerp(20, 90, k), la=lerp(60, 30, k), le=50, ra=lerp(-40, -60, k), re=40)
    else:
        u = lt - t_go
        p = L.run_limp(u, 0, ROOF_B, 0, facing=1, s=s, limp=0.3, lean=18, phase0=0.1 + 3.3 * u)
        p = p.copy(x=x_land + 60 + 1250 * u)
    cx = L.ek(lt, 0, dur, 330, 820, "inout")
    zoom = 1.0 + 0.07 * math.sin(math.pi * clamp((lt - 0.15) / 0.6))
    cam = Camera(cx, 1000, zoom, L.ek(lt, 0, dur, -1.0, 1.2)).shaken(t, amp=5, rot_amp=0.4, freq=1.8, seed=14)
    f.set_camera(cam)
    # moon: far layer, almost fixed on screen (tiny parallax) - silhouette ring behind the leap
    mc = (562 - (cx - 560) * 0.06, 812)
    with f.screen():
        L.moon(f, mc, 300, alpha=0.95, t=t)
    with f.camera(Camera(cx * 0.45 + 300, 1000, 1.0)):
        L.cheap_skyline(f, 1500, -200, 1600, seed=5, alpha=0.22, lit=0.08, scale=0.8)
    _roofs(f, t)
    # the street far below, deep in the gap: THE red umbrella crossing (tiny)
    sy = 1440.0
    draw.line(f, (EDGE_A + 40, sy + 26), (EDGE_B - 40, sy + 26), 1.6, WHITE, 0.4)
    ux = EDGE_A + 35 + (EDGE_B - EDGE_A - 70) * ((lt + 0.15) / (dur + 0.3))
    with f.clipped(lambda c: c.rectangle(EDGE_A + 8, 1000, EDGE_B - EDGE_A - 16, 800)):
        props.umbrella(f, (ux, sy + 10), angle=-90, R=26, color=CRIMSON, t=t)
    fx.rain(f, lt * 0.55 + t * 0.45, density=0.9, wind=8, seed=24)
    L.figure_cut(f, p, gap=8)


# ----------------------------------------------------------------------------- B4: laundry sheets
GROUND_B4 = 1450.0


def _sheet2d(f, x0, x1, ytop, hang, t, seed=0, gust=1.0, alpha=1.0, blue=0.0, lead=0.0):
    """Hanging sheet seen face-on: pinned top edge, wavy billowing bottom, black fill (occludes)."""
    n = 9
    top = [(x0 + (x1 - x0) * i / n, ytop + 8 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    bot = []
    for i in range(n, -1, -1):
        u = i / n
        wav = 22 * gust * math.sin(2 * math.pi * (u * 1.4 + t * 1.2 + hash01(seed, 2)))
        sx = (14 + 30 * gust) * fbm1(t * 1.1 + u, seed + 5) - lead * 60 * u
        bot.append((x0 + (x1 - x0) * u + sx, ytop + hang + wav))
    pts = top + bot
    draw.fill(f, pts, BLACK, 1.0)
    if blue > 0:
        draw.fill(f, pts, BLUE, 0.10 * blue, glow=0.25 * blue)
    draw.stroke(f, pts, 2.6, WHITE, alpha, closed=True)
    for k in (2, 5, 7):
        a_, b_ = top[k], bot[n - k]
        draw.line(f, (a_[0] + 6, a_[1] + 40), (b_[0] - 6, b_[1] - 50), 1.3, WHITE, alpha * 0.3)
    for k in (1, n - 1):
        a_ = top[k]
        draw.line(f, (a_[0], a_[1] - 10), (a_[0], a_[1] + 24), 3.0, WHITE, alpha * 0.9)


def shot_laundry(f, t, T, lt, dur):
    xf = 270 + 1120 * lt                                           # he runs at a steady pace...
    cx = xf + L.ek(lt, 0, dur, 230, 90, "inout")                   # ...the camera eases from leading to tracking
    cam = Camera(cx, 960, 1.0, L.ek(lt, 0, dur, -1.5, 1.5)).shaken(t, amp=10, rot_amp=0.8, freq=2.3, seed=15)
    b = L.police_blue(t + 0.1, rate=1.8)
    src = (cx + 760, 640)
    fig = L.run_limp(lt, 0, GROUND_B4, 0, facing=1, s=1.15, limp=0.35, lean=20, phase0=0.4 + 3.0 * lt)
    fig = fig.copy(x=xf)
    lights = [Light.cone(src, 168, 64, 1700, intensity=0.2 + 0.8 * b),
              Light.radial((xf, 1200), 500, intensity=0.35)]
    f.set_camera(cam)
    with f.lit(lights, ambient=0.28):
        with f.camera(Camera(cx * 0.5 + 200, 960, 1.0, cam.rot)):        # back wall of the courtyard
            draw.line(f, (-600, 1300), (2400, 1300), 2.0, WHITE, 0.5)
            for i in range(-2, 9):
                x = i * 260
                draw.rect(f, x + 40, 620, 90, 150, 1.5, WHITE, 0.35)
                draw.rect(f, x + 40, 900, 90, 150, 1.5, WHITE, 0.35)
                if hash01(i, 77) < 0.25:
                    draw.rect(f, x + 40, 620, 90, 150, 1, AMBER, 0.5, fill_it=True, glow=0.4)
        with f.camera(Camera(cx * 0.82 + 100, 960, 1.0, cam.rot)):      # mid-ground laundry behind him
            draw.line(f, (-400, 560), (3000, 560 + 20), 1.6, WHITE, 0.7)
            for i in range(9):
                x0 = -200 + i * 380
                _sheet2d(f, x0, x0 + 230 + 40 * hash01(i, 3), 560, 330 + 60 * hash01(i, 4), t + i, seed=i,
                         gust=1.2, alpha=0.95, blue=b)
        draw.line(f, (-800, GROUND_B4), (3200, GROUND_B4), 3.2, WHITE, 1.0)
        for i in range(8):
            px = 200 + i * 330
            draw.ellipse(f, (px, GROUND_B4 + 40), 90, 12, 0, 1.4, WHITE, 0.35)
        fx.rain(f, t, density=1.0, wind=10, seed=25)
        L.figure_cut(f, fig, gap=6)
    fx.splashes(f, t, GROUND_B4, cx - 700, cx + 700, rate=1.2)
    fx.reflection(f, cx + 330, GROUND_B4 + 4, 300, 90, BLUE, 0.45 * b, t)
    fx.light_cone(f, src, 168, 60, 1500, BLUE, 0.12 * b, glow=0.5)
    draw.glow_dot(f, src, 300, BLUE, 0.55 * b + 0.1, core=False)
    # foreground sheets on a near line: a partial wipe, then the full wipe into the dead end
    with f.screen():
        x1 = lerp(1250, -700, ease("inout", inv_lerp(0.12, 0.62, lt)))
        _sheet2d(f, x1, x1 + 560, -60, 1330, t * 1.3, seed=31, gust=1.8, blue=b, lead=0.6)
        if lt > 0.6:
            xl = lerp(1200, -40, ease("in3", inv_lerp(0.66, dur, lt)) ** 0.8)
            _sheet2d(f, xl, xl + 1600, -80, 2150, t * 1.3, seed=32, gust=2.2, blue=b, lead=1.0)


# ----------------------------------------------------------------------------- C1: dead end
def shot_dead_end(f, t, T, lt, dur):
    t_caught = T.at("caught") - T.at("All")
    ez = L.ek(lt, 0, dur, -80, 520, "inout3")
    P = L.Persp(ex=L.ek(lt, 0, dur, 60, -110), ey=L.ek(lt, 0.6, dur, -540, -420), ez=ez, F=1000,
                cx=540, cy=560, fog=5200)
    cam = Camera(540, 960, 1.0, L.ek(lt, 0, dur, 1.2, -0.6)).shaken(
        t, amp=L.ek(lt, 0, 0.5, 9, 2.2), rot_amp=0.4, freq=1.4, seed=16)
    f.set_camera(cam)
    Zw = 1520.0
    G = L.alley_geom(seed=21, hw=420.0, L=Zw, z0=-300.0, fire=0.3)
    b = L.police_blue(t + 0.4, rate=1.5)
    Xs, Zs_ = -20.0, 1080.0
    eX, eZ = Xs - 118.0, Zs_ - 6.0
    ember = P.p(eX, -3, eZ)
    t_stop, t_back, t_turn = 0.36, 0.5, t_caught
    t_pick, t_rise = t_caught + 0.24, t_caught + 0.5
    if lt < t_stop:                                    # arrives running, up-left into the dead end
        u = lt / t_stop
        fig, fs = L.run_at(P, lerp(260, Xs, ease("out", u)), lerp(430, Zs_, ease("out", u)),
                           0.3 + 3.0 * lt, facing=-1, limp=0.35, lean=lerp(20, 8, u))
    elif lt < t_back:                                  # skid: weight thrown back, follow-through
        k = ease("out3", inv_lerp(t_stop, t_back, lt))
        base = rig.stand(0, 0, facing=-1, s=1.0, lean=lerp(-14, 2, k), ll=lerp(34, 8, k), lk=8,
                         rl=lerp(-26, -6, k), rk=14, la=lerp(50, 12, k), le=30, ra=lerp(-40, -10, k), re=30)
        fig, fs = L.pose_at(P, Xs, Zs_, base)
    elif lt < t_turn:                                  # nobody: faces the wall, heaving
        base = rig.stand(0, 0, facing=0, s=1.0, la=12, ra=12)
        heave = math.sin(2 * math.pi * 1.6 * lt)
        base = rig.breathe(base, t, amt=2.2, seed=6).copy(head=-5 + 4 * math.sin(lt * 7), la=12 + 5 * heave,
                                                           ra=12 + 5 * heave, lk=4 + 6 * (0.5 - 0.5 * heave),
                                                           rk=4 + 6 * (0.5 - 0.5 * heave))
        fig, fs = L.pose_at(P, Xs, Zs_, base)
    else:                                              # turns to the ember (his LEFT), crouches, LEFT hand takes it
        kc = ease("inout3", inv_lerp(t_turn + 0.04, t_pick, lt))
        kr = ease("inout3", inv_lerp(t_pick + 0.03, t_rise, lt))
        stand = rig.stand(0, 0, facing=-1, s=1.0, head=22, la=10, ra=-10)
        crouch = stand.copy(lean=52, head=26, ll=92, lk=146, rl=58, rk=128, ra=-30, re=50)
        up = stand.copy(lean=6, head=12, ll=6, lk=8, rl=-4, rk=8, ra=-12, re=20)
        base = stand.blend(crouch, kc) if lt < t_pick + 0.03 else crouch.blend(up, kr)
        base = rig.breathe(base, t, amt=1.0, seed=8)
        fig, fs = L.pose_at(P, Xs, Zs_, base)
        J = rig.solve(fig)
        face = (J["head"][0] - J["head_r"] * 1.6, J["head"][1] + J["head_r"] * 0.9)
        if lt < t_pick + 0.03:
            tgt = (lerp(J["lh"][0], ember[0], kc), lerp(J["lh"][1], ember[1], kc))
        else:
            tgt = (lerp(ember[0], face[0], kr), lerp(ember[1], face[1], kr))
        fig = rig.reach(fig, "l", tgt)
    J = rig.solve(fig)
    held = lt >= t_pick
    mb = J["lh"] if held else ember
    lights = [Light.cone((540, 2350), -90, 50, 2500, intensity=0.25 + 0.75 * b),
              Light.radial(mb, 420 * P.k(eZ) ** 0.5, intensity=0.95)]
    with f.lit(lights, ambient=0.25):
        L.draw_alley(f, P, G, t, puddles=((-190, 700, 150), (210, 1250, 140)))
        L.draw_dead_end(f, P, 420.0, Zw)
        L.draw_box(f, P, 220, 390, 1250, 1480, 200, alpha=0.9)
        L.draw_can(f, P, -330, 1380, alpha=0.9)
        fx.rain(f, t, density=1.0, wind=4, seed=26)
        L.figure_cut(f, fig, gap=6)
    ks = P.k(eZ)
    emb = 0.8 + 0.2 * math.sin(t * 9)
    if lt < 0.22:   # still behind the passing laundry sheet: no glow bleeding through it
        xr = lerp(1500, -260, ease("out", lt / 0.22))
        emb *= clamp((cam.to_screen(ember)[0] - xr) / 80.0)
    if not held:
        fx.light_pool(f, (ember[0], ember[1] + 4), 120 * ks, 30 * ks, AMBER, 0.22 * emb)
    tip = props.match(f, mb, angle=(-112 if held else -172), length=52, s=ks * 1.25, burnt=1.0,
                      ember=emb, smoke_amt=1.0, t=t, seed=3)
    draw.glow_dot(f, tip, 70 * ks, AMBER, 0.55 * emb, core=False)
    fx.light_cone(f, (540, 2350), -90, 46, 2100, BLUE, 0.08 * b, glow=0.4)
    if lt < 0.22:   # the laundry wipe completes: the near sheet's trailing edge leaves frame-left
        with f.screen():
            xr = lerp(1500, -260, ease("out", lt / 0.22))
            _sheet2d(f, xr - 1700, xr, -80, 2150, (T.at("All") + lt) * 1.3, seed=32, gust=2.2, blue=b, lead=1.0)


# ----------------------------------------------------------------------------- C2: macro "warm match"
def macro_ember_tip(base, angle, s):
    Lm = 52.0 * s
    a = math.radians(angle)
    mid = (base[0] + math.cos(a) * Lm * 0.72, base[1] + math.sin(a) * Lm * 0.72)
    a2 = math.radians(angle + 35)
    return (mid[0] + math.cos(a2) * Lm * 0.22, mid[1] + math.sin(a2) * Lm * 0.22)


def shot_macro(f, t, T, lt, dur):
    sm = 5.2
    hand = (600 + 10 * fbm1(t * 0.7, 3), 1210 + 8 * fbm1(t * 0.6, 4))
    ang = -101 + 3 * fbm1(t * 0.5, 5)
    tip = macro_ember_tip(hand, ang, sm)
    kc = ease("inout3", inv_lerp(0.0, dur - 0.45, lt))
    zoom = lerp(1.3, 1.8, ease("inout3", inv_lerp(0.0, dur - 0.3, lt)))
    cx = lerp(575, tip[0], kc)
    cy = lerp(1010, tip[1], kc)
    shake = 1.0 - ease("inout", inv_lerp(0.3, dur - 0.5, lt))
    cam = Camera(cx, cy, zoom, L.ek(lt, 0, dur, 2.5, 0.0)).shaken(t, amp=3.0 * shake, rot_amp=0.15 * shake,
                                                                  freq=0.9, seed=17)
    f.set_camera(cam)
    fade = ease("inout3", inv_lerp(dur - 1.05, dur - 0.32, lt))   # the world sinks to black, the ember stays
    warm = pulse(lt, 0.02, 0.06, 0.5)
    b = L.police_blue(t + 0.4, rate=1.5)
    if fade < 0.99:
        with f.alpha(1.0 - fade):
            with f.blurred(18):                       # the alley behind, deep out of focus (bokeh)
                with f.camera(Camera(540, 960, 1.0, 0)):
                    draw.glow_dot(f, (830, 430), 170, BLUE, 0.55 * b + 0.1, core=False)
                    draw.circle(f, (830, 430), 36, 1, BLUE, 0.45 * b + 0.15, fill_it=True)
                    draw.circle(f, (190, 330), 24, 1, AMBER, 0.55, fill_it=True)
                    draw.circle(f, (330, 1560), 18, 1, AMBER, 0.35, fill_it=True)
                    for i in range(9):
                        x = 40 + 120 * i + 40 * hash01(i, 1)
                        draw.line(f, (x, 0), (x + 30, 1920), 3.0, WHITE, 0.07)
            for i in range(7):                        # a few big soft raindrops crossing the lens
                ph = (t * (1.3 + 0.3 * hash01(i, 2)) + hash01(i, 3)) % 1.0
                k = int(t * (1.3 + 0.3 * hash01(i, 2)) + hash01(i, 3))
                x = cx - 450 + 900 * hash01(i, 4, k)
                y = cy - 900 + 1800 * ph
                draw.line(f, (x, y), (x + 10, y + 120), 3.0, WHITE, 0.13)
    # his LEFT arm (front view: the body stands off-frame to the right, the left arm reaches in)
    body = Pose(x=1250, y=1700 - 14 * 6.6 + 112 * 6.6, s=6.6, facing=0, la=8, le=12, ra=6, re=6)
    arm = rig.reach(body, "l", hand)
    lights = [Light.radial(tip, 560 * (1 + 0.3 * warm) * (1 - 0.7 * fade), intensity=1.0)]
    with f.lit(lights, ambient=0.15 * (1 - fade)):
        with f.alpha(1.0 - fade):
            J = rig.draw_figure(f, arm)
    em = clamp(0.72 + 0.28 * ease("out3", inv_lerp(0.0, 0.3, lt)) + 0.3 * warm, 0, 1)
    props.match(f, J["lh"], angle=ang, length=52, s=sm, burnt=1.0, ember=em * (1 - fade),
                smoke_amt=0.85 * (1 - fade), t=t, seed=3, alpha=1.0 - fade)
    if fade > 0:   # the ember alone, kept fully bright (same glow design as the match ember)
        e2 = em * (0.94 + 0.06 * math.sin(t * 6.0))
        draw.glow_dot(f, tip, 14 * sm, AMBER, 0.9 * e2 * fade)
        draw.circle(f, tip, 3.2 * sm, 1, AMBER, e2 * fade, fill_it=True, glow=0.8)
    if warm > 0.02:   # "warm": the ember breathes in, a soft bloom
        draw.glow_dot(f, tip, 160 * sm ** 0.5, AMBER, 0.35 * warm * (1 - fade), core=False)


# ----------------------------------------------------------------------------- main
SHOTS = [shot_mouth, shot_run_to_cam, shot_fire_escape, shot_leap, shot_laundry, shot_dead_end, shot_macro]


def render(f, t, T):
    cuts = _cuts(T)
    i, lt, t0, t1 = L.shot_of(t, cuts)
    SHOTS[i](f, t, T, lt, t1 - t0)


def _contacts(t_shot, lt0, lt1, phase0, rate):
    """Scene times of run-cycle foot contacts (rig.run plants a foot every half cycle)."""
    out = []
    k = math.ceil((phase0 + rate * lt0) * 2.0)
    while True:
        lt = (k * 0.5 - phase0) / rate
        if lt > lt1:
            break
        if lt >= lt0:
            out.append((t_shot + lt, k))
        k += 1
    return out


def cues(T):
    c = _cuts(T)
    C = []
    # A: the launch into the alley
    for i, (tt, k) in enumerate(_contacts(c[0], 2.92, c[1] - c[0], 0.35 - 3.0 * 2.92, 3.0)):
        C.append(Cue(tt, "footstep_run", gain_db=-9 + 2 * i, pan=0.15))
    # B1: running at the lens - steps grow louder, pass left -> right; the left foot lands heavier (limp)
    for i, (tt, k) in enumerate(_contacts(c[1], 0.0, c[2] - c[1], 0.15, 3.2)):
        C.append(Cue(tt, "footstep_run", gain_db=-10 + 2.0 * i + (1.5 if k % 2 else 0), pan=-0.35 + 0.16 * i))
    # B2: fire-escape steps ring out; a heavier clang on the turn at the landing
    for tt, k in _contacts(c[2], 0.0, 0.47, 0.0, 900 / (300 * 0.86)):
        C.append(Cue(tt, "metal_clang", gain_db=-9 + 2 * hash01(k, 3), pan=lerp(-0.3, 0.3, inv_lerp(c[2], c[2] + 0.47, tt))))
    C.append(Cue(c[2] + 0.48, "metal_clang", gain_db=-4, pan=0.3))
    for tt, k in _contacts(c[2], 0.57, c[3] - c[2] - 0.02, 0.0, 900 / (300 * 0.86)):
        C.append(Cue(tt, "metal_clang", gain_db=-9 + 2 * hash01(k, 4), pan=lerp(0.3, -0.3, inv_lerp(c[2] + 0.57, c[3], tt))))
    # B3: push-off, the leap through the air, the landing
    C.append(Cue(c[3] + 0.09, "footstep_run", gain_db=-7, pan=-0.3))
    C.append(Cue(c[3] + 0.2, "footstep_run", gain_db=-4, pan=-0.15))
    C.append(Cue(c[3] + 0.22, "whoosh", gain_db=-5, pan=0.0, size=0.7))
    C.append(Cue(c[3] + 0.68, "land_thud", gain_db=-2, pan=0.2))
    for tt, k in _contacts(c[3] + 0.84, 0.0, c[4] - c[3] - 0.84, 0.1, 3.3):
        C.append(Cue(tt, "footstep_run", gain_db=-7, pan=0.35))
    # B4: splashing run under the laundry, a sheet slaps past, the big one wipes the lens
    for tt, k in _contacts(c[4], 0.0, c[5] - c[4] - 0.12, 0.4, 3.0):
        C.append(Cue(tt, "footstep_run", gain_db=-8 + (1.5 if k % 2 else 0), pan=-0.1))
    C.append(Cue(c[4] + 0.3, "laundry_flap", gain_db=-6, pan=0.4))
    C.append(Cue(c[5] - 0.2, "laundry_flap", gain_db=-1, pan=0.2))
    C.append(Cue(c[5] - 0.14, "whoosh", gain_db=-8, pan=0.3, size=0.4))
    # C1: dead end - last strides, the skid, he picks up the warm match
    for tt, k in _contacts(c[5], 0.0, 0.3, 0.3, 3.0):
        C.append(Cue(tt, "footstep_run", gain_db=-7, pan=0.1))
    C.append(Cue(c[5] + 0.38, "footstep", gain_db=-3, pan=0.0, weight=1.0, wet=1))
    C.append(Cue(T.at("caught") + 0.24, "ember_sizzle", gain_db=-14, pan=-0.1))
    # C2: macro on "warm match"
    C.append(Cue(T.at("warm") + 0.02, "ember_sizzle", gain_db=-6, pan=0.05))
    C.append(Cue(T.at("match") + 0.5, "ember_sizzle", gain_db=-13, pan=0.0))
    return C


def motion_blur(t, T):
    cuts = _cuts(T)
    i, lt, t0, t1 = L.shot_of(t, cuts)
    if i == 3 and (0.14 < lt < 0.32 or 0.6 < lt < 0.74):
        return 5                       # leap take-off / landing (speed ramp extremes)
    if i == 4 and lt > t1 - t0 - 0.17:
        return 4                       # the big laundry sheet sweeping across the lens
    return 1
