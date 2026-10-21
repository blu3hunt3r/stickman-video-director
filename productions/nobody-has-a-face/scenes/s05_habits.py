"""S05 - Habits (7.417 s).

"But here's what the academy never teaches. People can hide their faces.
 Nobody can hide their habits."

Shot plan (scene seconds; word hits come from T.at)
  0.00-1.00  IN: S04's thin smoke wisp keeps rising at screen centre and dissolves along the office
             ceiling while the camera eases out of S04's upward tilt (tight, almost black frame)
  0.45-2.15  crane/tilt DOWN into sets.office (inout3, pulling back): the wisp's source is revealed -
             a burnt match cooling in the ashtray on his desk (quiet plant); board, blinds throwing
             amber stripes, THE red umbrella furled on the coat rack by the door (in shadow, glow
             suppressed - visible, not emphasised), desk + lamp; the detective stands behind the desk
             at the window, back to camera (back view: his LEFT is screen-left)
  1.42-2.18  anticipation (weight shift, arm dips), then his LEFT hand reaches up and parts the lowest
             slats - an amber slit of street light
  2.24-3.42  push over his head into the slit; the blinds split open (foreground wipe) onto the wet
             street below: three identical passers-by under umbrellas, 3 parallax depths, rain
  3.42-5.10  "People can hide their faces." - slow crane down the street
  5.15 / 5.70 / 6.15  "Nobody" / "hide" / "habits": amber iris rings pop on each habit - a man
             checking his watch, a tapping foot, a hitch in the step - each with a rack focus
  6.36-6.48  the slats snap back shut (his hand lets go)
  6.50-6.625 whip down (motion streak) ... the cut hides inside the blur ...
  6.625-7.42 the whip lands on the desk insert. OUT: THE pocket watch at 3:07 lying on the desk,
             face centred at screen (540, 960), radius 300 px; camera fully settled from 7.10 s
"""
import math
from contextlib import nullcontext

from engine import *
from scenes._lib_s05_s07 import (ZTrack, cam_for, draw_back, reach_back, back_solve, glow_scaled,
                                 desk_insert, ring_pop, zlerp)

O = sets.OFFICE
WX, WY, WW, WH = O["window"]
SLATS = 13
GAP = WH / SLATS
TH = GAP * (0.85 - 0.6 * 0.55)                 # slat thickness at the office's default tilt
DET_X, DET_S = 950.0, 1.75                      # the detective behind the desk, under the window
PART_X, PART_HW = 890.0, 64.0                   # where his left hand parts the slats
SLAT_A, SLAT_B = 11, 12                         # the two slats pushed apart
GAP_C = (893.0, 902.0)                          # centre of the parted slit (push-in target)
LAMP_PT = (O["lamp"][0] - 88, O["lamp"][1] - 132)
ASHTRAY = (520.0, O["desk"][1] - 6)             # burnt match cooling here: source of the wisp

# street world (seen through the blinds)
FAR_Y, MID_Y, NEAR_Y = 800.0, 1118.0, 1450.0
LAMP_BASE = (998.0, NEAR_Y + 8)
DEPTHS = (0.86, 1.0, 1.14)


# ----------------------------------------------------------------------------- timing
class K:
    pass


def keys(T):
    k = K()
    k.raise0, k.raise1 = 1.42, 1.96
    k.part0, k.part1 = 1.96, 2.18
    k.push0, k.push1 = 2.24, 3.22
    k.split0, k.split1 = 2.92, 3.42
    k.ring1 = T.at("nobody")
    k.ring2 = T.at("hide", 1)
    k.ring3 = T.at("habits")
    k.close0, k.close1 = 6.36, 6.48
    k.whip0 = 6.50
    k.cut = 159 / FPS                            # 6.625 s - the cut hides inside the whip blur
    k.land = 7.10
    return k


def _bump(x):
    d = (x - PART_X) / PART_HW
    return 0.5 + 0.5 * math.cos(math.pi * d) if abs(d) < 1 else 0.0


def part_amount(t, k):
    """Slat bend in world px: the hand pushes it open, holds, then lets it snap back."""
    if t < k.part0:
        return 0.0
    if t < k.close0:
        return 21.0 * ease("out3", inv_lerp(k.part0, k.part1, t))
    u = inv_lerp(k.close0, k.close0 + 0.16, t)
    return 21.0 * (1 - ease("outelastic", u)) if u < 1 else 0.0


def split_amount(t, k):
    if t < k.split0:
        return 0.0
    if t < k.close0:
        return 1150.0 * ease("inout3", inv_lerp(k.split0, k.split1, t))
    return 1150.0 * (1 - ease("in3", inv_lerp(k.close0, k.close1, t)))


# ----------------------------------------------------------------------------- cameras
_TILT = Track([(0.0, (540.0, 446.0)), (0.45, (540.0, 420.0), "out3"), (2.15, (668.0, 1004.0), "inout3")])
_TILT_Z = ZTrack([(0.0, 1.92), (0.45, 1.9, "out3"), (2.15, 1.06, "inout3")])


def office_cam(t, k):
    if t <= k.push0:
        x, y = _TILT(t)
        return Camera(x, y, _TILT_Z(t))
    x0, y0 = _TILT(k.push0)
    z0 = _TILT_Z(k.push0)
    s0 = Camera(x0, y0, z0).to_screen(GAP_C)
    u = inv_lerp(k.push0, k.push1, t)
    z = zlerp(z0, 5.0, ease("inout3", u)) * (1 + 0.04 * max(0.0, t - k.push1))
    sp = lerp(s0, (540.0, 960.0), ease("inout3", u))
    if t > k.whip0:
        w = ease("in3", inv_lerp(k.whip0, k.cut, t))
        return cam_for((GAP_C[0], GAP_C[1] + 520 * w), sp, z * (1 - 0.12 * w))
    return cam_for(GAP_C, sp, z)


def street_cam(t, k):
    z = zlerp(0.9, 1.14, ease("out3", inv_lerp(2.5, 3.9, t))) * (1 + 0.04 * ease("inout", inv_lerp(3.9, 6.4, t)))
    y = lerp(1000.0, 1100.0, ease("inout", inv_lerp(2.5, 6.4, t)))
    x = lerp(560.0, 515.0, ease("inout", inv_lerp(2.5, 6.4, t)))
    return Camera(x, y, z)


# ----------------------------------------------------------------------------- the detective (office)
def detective(t, k):
    p = rig.stand(DET_X, O["floor_y"], facing=0, s=DET_S)
    p = rig.breathe(p, t, amt=0.9, seed=5)
    # anticipation: weight shifts, the arm dips, then the LEFT hand rises to the slats
    ant = ease("inout", inv_lerp(k.raise0, k.raise0 + 0.18, t)) * (1 - ease("inout", inv_lerp(k.raise0 + 0.18, k.raise1, t)))
    rest = p.copy(la=p.la - 5 * ant, lean=p.lean - 1.5 * ant)
    D = part_amount(t, k)
    up = reach_back(rest, "l", (PART_X - 2, WY + SLAT_B * GAP + 4 + 0.9 * D))
    up = up.copy(head=up.head + 4, lean=up.lean + 1.0)
    a = ease("outback", inv_lerp(k.raise0 + 0.12, k.raise1, t))
    if t > k.close0:                              # lets go: the hand drops back
        a *= 1 - ease("inout3", inv_lerp(k.close0 + 0.02, k.close0 + 0.42, t))
    return rest.blend(up, a)


# ----------------------------------------------------------------------------- office drawing
def _stripe_polys():
    """The stripe geometry sets.office throws through the blinds (reused for the light mask)."""
    quad = [(WX + 10, WY + 20), (WX + WW, WY + 10), (WX - 120, O["floor_y"] - 40), (WX - 520, O["floor_y"] + 30)]
    tl, tr, br, bl = quad
    out = []
    n, duty = 10, 0.45
    for i in range(n):
        a0, a1 = i / n, min(1.0, (i + duty) / n)
        out.append([lerp(tl, bl, a0), lerp(tr, br, a0), lerp(tr, br, a1), lerp(tl, bl, a1)])
    return quad, out


QUAD, STRIPES = _stripe_polys()
PHOTOS = ((385, 610, -4), (520, 596, 3), (630, 650, -2), (440, 742, 5))


def slat_edges(D, n=26):
    """Bent slat edges (slat A pushed up a little, slat B pushed down) across the parted region."""
    xs = [PART_X - PART_HW + 2 * PART_HW * i / n for i in range(n + 1)]
    ya, yb = WY + SLAT_A * GAP, WY + SLAT_B * GAP
    a_top = [(x, ya - 0.25 * D * _bump(x)) for x in xs]
    a_bot = [(x, ya + TH - 0.4 * D * _bump(x)) for x in xs]
    b_top = [(x, yb + D * _bump(x)) for x in xs]
    b_bot = [(x, yb + TH + 0.72 * D * _bump(x)) for x in xs]
    return a_top, a_bot, b_top, b_bot


def slit_poly(D):
    a_top, a_bot, b_top, b_bot = slat_edges(D)
    return a_bot + b_top[::-1]


def draw_parted_slats(f, D):
    """Swap the two straight slats around his fingers for bent ones."""
    x0, x1 = PART_X - PART_HW, PART_X + PART_HW
    y0 = WY + SLAT_A * GAP - 3
    y1 = WY + SLAT_B * GAP + TH + 3 + 0.75 * D
    draw.fill(f, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], BLACK, 1.0)
    with f.clipped(lambda c: c.rectangle(x0, y0, x1 - x0, y1 - y0 + 2)):
        props.blind_light(f, QUAD, n=10, duty=0.45, color=AMBER, alpha=0.16, glow=0.0)
    for e in slat_edges(D):
        draw.stroke(f, e, 2.0, WHITE, 0.9)
    cx = WX + WW * 0.8
    draw.line(f, (cx, y0), (cx, y1), 1.2, WHITE, 0.5)


def ember_amt(t):
    return 0.85 * (1 - smoothstep(0.6, 2.8, t)) + 0.12


def draw_office(f, t, k, cam):
    f.set_camera(cam)
    D = part_amount(t, k)
    p = detective(t, k)
    J = back_solve(p)
    slit = slit_poly(D)
    lights = [Light.poly(s, 0.8) for s in STRIPES]
    lights += [Light.rect(WX - 10, WY - 10, WX + WW + 10, WY + WH + 10, 0.55),
               Light.radial(LAMP_PT, 470, 0.95), Light.cone(LAMP_PT, 96, 74, 560, 0.9),
               Light.radial(ASHTRAY, 120, 0.6 * ember_amt(t))]
    if D > 0.5:
        k_open = clamp(D / 21.0)
        lights.append(Light.poly([(PART_X - PART_HW, GAP_C[1]), (PART_X + PART_HW, GAP_C[1]),
                                  (PART_X + 260, GAP_C[1] + 460), (PART_X - 200, GAP_C[1] + 460)], 0.75 * k_open))
    with f.lit(lights, ambient=0.2, soften=3.5):
        with glow_scaled(f, 0.4):                       # props in shadow do not glow
            sets.office(f, t, umbrella=True, lamp_on=0.0)
            for (px, py, ang) in PHOTOS:
                props.photo_card(f, (px, py), 82, 100, ang, alpha=0.75)
        if D > 0.05:
            draw_parted_slats(f, D)
        draw_back(f, p)
        # he stands BEHIND the desk: the desk front hides his legs
        x, ty, w, h = O["desk"]
        draw.fill(f, [(x - 22, ty + 2), (x + w + 22, ty + 2), (x + w + 22, ty + h + 4), (x - 22, ty + h + 4)], BLACK, 1.0)
        sets.desk(f)
        # ashtray with the burnt match the smoke rises from
        ax, ay = ASHTRAY
        draw.ellipse(f, (ax, ay), 40, 7, 0, 2.4, WHITE, 0.9)
        draw.line(f, (ax - 36, ay + 4), (ax - 30, ay + 6), 2.0, WHITE, 0.8)
    props.match(f, (ASHTRAY[0] - 22, ASHTRAY[1] - 3), angle=-8, length=46, s=0.55, burnt=1.0,
                ember=ember_amt(t), t=t, seed=3)
    if D > 0.5:                                         # street light pouring through the slit
        glow_k = clamp(D / 10) * (1 - smoothstep(k.push1 - 0.2, k.split1, t))
        if glow_k > 0.01:
            draw.fill(f, slit, AMBER, 0.55 * glow_k, glow=0.9 * glow_k)
    sets.desk_lamp(f, on=0.95 + 0.05 * flicker(t, 4, rate=6, depth=0.3), t=t)
    fx.light_cone(f, LAMP_PT, 96, 66, 520, AMBER, 0.07, glow=0.25)
    return J, slit, D


# ----------------------------------------------------------------------------- smoke wisp (IN)
def _curl(h, tg, strand):
    """Same curl law as S04's rising wisp (sinusoid + fbm, amplitude growing with height), scaled to
    this framing so the strands keep S04's on-screen size; driven by global film time so the curl
    phase continues straight across the S04 -> S05 cut."""
    amp = (3.0 + 0.058 * h) * (1.0 if strand == 0 else 0.7)
    lam = 90.0 + 0.54 * h
    ph = 4 * 1.7 + strand * 2.1
    return (amp * math.sin(2 * math.pi * h / lam - 2.3 * tg + ph)
            + 0.45 * amp * fbm1(h / 480.0 - 0.35 * tg, 4 + 11 * strand) + 4.0 * strand)


def smoke_wisp(f, t, T):
    """The S04 wisp, now rising from the ashtray: it hits the ceiling, spreads and dissolves."""
    top = O["ceil_y"] + 5
    base = (ASHTRAY[0] - 22 + 46 * 0.55 * math.cos(math.radians(-8)) * 0.82, ASHTRAY[1] - 6)
    tg = T.start + t
    a_hi = 0.34 * (1 - smoothstep(0.15, 1.2, t))          # upper wisp dissolves at the ceiling
    a_lo = 0.3 * (1 - smoothstep(1.2, 2.6, t))            # thread from the ember thins as it dies
    if max(a_hi, a_lo) <= 0.01:
        return
    n = 64
    H = base[1] - top
    for s in range(2):
        pts = []
        for i in range(n + 1):
            u = i / n
            h = H * u
            x = lerp(base[0], 540.0, smoothstep(0.0, 0.3, u)) + _curl(h, tg, s) * smoothstep(0.0, 0.12, u)
            pts.append((x, base[1] - h))
        spread = 1 + 1.7 * t
        side = -1 if s == 0 else 1
        xt = pts[-1][0]
        for j in range(1, 12):
            v = j / 11
            pts.append((xt + side * (30 + 110 * spread) * v, top + 12 * v * v + 6 * math.sin(v * 5 + t * 2 + s)))
        m = len(pts) - 1
        for i in range(m):
            u = i / m
            a = lerp(a_lo, a_hi, smoothstep(0.25, 0.6, u)) * (1.0 if s == 0 else 0.55)
            a *= 1 - smoothstep(0.84, 1.0, u) * (0.5 + 0.5 * smoothstep(0.0, 0.9, t))
            a *= smoothstep(0.0, 0.03, u)
            if a > 0.01:
                draw.line(f, pts[i], pts[i + 1], 2.0 * (1 - 0.3 * u), WHITE, a)


# ----------------------------------------------------------------------------- street (through the blinds)
def _hitch_time(t, period, a=0.82):
    """Walk time with a hesitation once per stride cycle (a hitch in the step)."""
    u = t / period
    fr = u - math.floor(u)
    return period * (math.floor(u) + fr - a * math.sin(2 * math.pi * fr) / (2 * math.pi))


def _walk_cycle_time(speed, s=1.0, limp=0.0):
    base = Pose(x=0, y=0, s=s, facing=1)
    pa = rig._walk_angles(base, 0.0, limp, 1.0, 1.0)
    pb = rig._walk_angles(base, 0.5, limp, 1.0, 1.0)
    cyc = abs(rig._foot_dx(pa, "l") - rig._foot_dx(pa, "r")) + abs(rig._foot_dx(pb, "r") - rig._foot_dx(pb, "l"))
    return cyc / speed


P3_SPEED, P3_S, P3_LIMP, P3_X0, P3_T0 = 112.0, 1.0, 0.25, -60.0, 2.0
TAP_HZ, TAP_T0 = 2.6, 3.2


def passers(t, k):
    """Three identical passers-by: (pose, umbrella-hand side)."""
    # P1, far sidewalk: checks his watch - twice (compulsively)
    p1 = rig.breathe(rig.stand(300, FAR_Y, facing=1, s=0.62), t, amt=1.0, seed=17)
    chk = 0.0
    for a, b in ((3.55, 4.35), (k.ring1 - 0.32, k.ring1 + 0.95)):
        chk = max(chk, ease("inout3", inv_lerp(a, a + 0.22, t)) * (1 - ease("inout3", inv_lerp(b - 0.2, b, t))))
    p1 = p1.blend(p1.copy(la=74, le=78, head=p1.head + 24), chk)
    # P2, traffic island: waiting to cross, his front foot taps
    p2 = rig.breathe(rig.stand(770, MID_Y, facing=-1, s=0.8), t, amt=1.0, seed=29)
    tap = max(0.0, math.sin(2 * math.pi * TAP_HZ * (t - TAP_T0))) ** 2 if t > TAP_T0 else 0.0
    p2 = rig.on_ground(p2.copy(ll=-4, lk=3, rl=10, rk=3), MID_Y).copy(rl=10 + 14 * tap, rk=3 + 40 * tap)
    # P3, near sidewalk: walks left -> right with a hitch in his step
    per = _walk_cycle_time(P3_SPEED, P3_S, P3_LIMP)
    p3 = rig.walk(_hitch_time(max(0.0, t - P3_T0), per), P3_X0, NEAR_Y, P3_SPEED, facing=1, s=P3_S, limp=P3_LIMP)
    return [(p1, "r"), (p2, "l"), (p3, "r")]


def _with_umbrella(p, side):
    J = rig.solve(p)
    return rig.reach(p, side, (J["hip"][0] + 20 * p.s * (p.facing or 1), J["hip"][1] - 172 * p.s))


def draw_street(f, t, k, cam, focus=None):
    """The wet street below his window. focus = blur radius per depth tier (rack focus)."""
    f.set_camera(cam)
    lp = (LAMP_BASE[0] - 120, LAMP_BASE[1] - 820 + 62)
    shop = (280.0, 690.0)
    ps = passers(t, k)
    lights = [Light.cone(lp, 100, 66, 1100, 1.0), Light.radial(lp, 260, 0.8), Light.radial(shop, 430, 0.85)]
    blur = focus if focus is not None else [0.0, 0.0, 0.0]
    Js = [None, None, None]
    with f.camera(cam.parallax(DEPTHS[0])):            # lit shop window behind P1 (emissive)
        draw.rect(f, 130, 610, 300, 140, 1, AMBER, 0.2, fill_it=True, glow=0.55)
    with f.lit(lights, ambient=0.3, soften=4):
        for tier in range(3):
            with (f.blurred(blur[tier]) if blur[tier] > 0.6 else nullcontext()), \
                    f.camera(cam.parallax(DEPTHS[tier])):
                if tier == 0:
                    draw.line(f, (-500, 450), (1600, 450), 2.0, WHITE, 0.4)
                    for xx in (110, 450, 470, 560, 880):
                        draw.line(f, (xx, 450), (xx, 766), 2.0, WHITE, 0.45)
                    draw.rect(f, 130, 610, 300, 140, 3.0, WHITE, 0.9)
                    draw.line(f, (280, 610), (280, 750), 1.6, WHITE, 0.6)
                    draw.rect(f, 470, 640, 90, 126, 2.6, WHITE, 0.8)
                    draw.stroke(f, [(110, 595), (130, 570), (440, 570), (460, 595)], 2.4, WHITE, 0.8)
                    draw.line(f, (-500, 766), (1600, 766), 3.0, WHITE, 0.9)
                    draw.line(f, (-500, 826), (1600, 826), 2.4, WHITE, 0.7)
                elif tier == 1:
                    for xx in range(-200, 1400, 240):
                        draw.line(f, (xx, 966), (xx + 110, 966), 3.0, WHITE, 0.32)
                    draw.stroke(f, [(600, MID_Y - 2), (612, MID_Y - 22), (1050, MID_Y - 22), (1062, MID_Y - 2)], 2.6, WHITE, 0.85)
                    draw.line(f, (592, MID_Y + 4), (1070, MID_Y + 4), 2.6, WHITE, 0.85)
                    draw.line(f, (950, MID_Y - 22), (950, MID_Y - 330), 3.0, WHITE, 0.85)
                    draw.rect(f, 932, MID_Y - 400, 36, 72, 2.4, WHITE, 0.85)
                    fx.puddle(f, (380, 1262), 120, 16, t, seed=4, alpha=0.6)
                    for xx in range(-200, 1400, 240):
                        draw.line(f, (xx + 60, 1300), (xx + 170, 1300), 3.0, WHITE, 0.25)
                else:
                    draw.line(f, (-500, 1392), (1600, 1392), 2.4, WHITE, 0.75)
                    draw.line(f, (-500, NEAR_Y + 10), (1600, NEAR_Y + 10), 3.2, WHITE, 0.95)
                    for xx in range(-400, 1500, 160):
                        draw.line(f, (xx, 1392), (xx + 18, NEAR_Y + 10), 1.4, WHITE, 0.25)
                    props.streetlamp(f, LAMP_BASE, height=820, facing=-1, t=t, on=0.0)
                pose, side = ps[tier]
                pose = _with_umbrella(pose, side)
                J = rig.draw_figure(f, pose)
                Js[tier] = J
                props.umbrella(f, J[side + "h"], angle=-90 + 3 * fbm1(t * 0.7, tier + 3), R=118 * pose.s, t=t,
                               wobble=0.6, seed=tier)
        fx.rain(f, t, density=0.85, wind=8, seed=23, alpha=0.9)
    with f.camera(cam.parallax(DEPTHS[2])):            # lamp + wet reflections (emissive)
        props.streetlamp(f, LAMP_BASE, height=820, facing=-1, t=t, glow_r=230)
        fx.reflection(f, lp[0], 1396, 120, 54, AMBER, 0.45, t, seed=3)
        fx.splashes(f, t, NEAR_Y + 8, -200, 1300, rate=0.7, seed=8, alpha=0.6)
    with f.camera(cam.parallax(DEPTHS[1])):
        fx.reflection(f, lp[0] - 40, 1010, 260, 70, AMBER, 0.32, t, seed=5)
        fx.reflection(f, 280, 836, 150, 150, AMBER, 0.22, t, seed=7)
    fx.light_cone(f, lp, 100, 60, 900, AMBER, 0.06, glow=0.25)
    # habit rings (graphic overlay, always sharp)
    for t0, tier, r in ((k.ring1, 0, 44), (k.ring2, 1, 52), (k.ring3, 2, 74)):
        J = Js[tier]
        c = {0: J["lh"], 1: J["rf"], 2: lerp(J["lk"], J["lf"], 0.35)}[tier]
        with f.camera(cam.parallax(DEPTHS[tier])):
            ring_pop(f, c, r, t, t0, seed=tier)


def street_focus(t, k):
    """Rack focus synced to the rings: blur radius per depth tier (focus pulls over 0.16 s)."""
    starts = (k.ring1 - 0.12, k.ring2 - 0.12, k.ring3 - 0.12)
    if t < starts[0]:
        return None
    amt = ease("inout", inv_lerp(starts[0], starts[0] + 0.16, t))
    if t > k.close0 - 0.25:
        amt *= 1 - ease("inout", inv_lerp(k.close0 - 0.25, k.close0, t))
    blur = []
    for i in range(3):
        w = ease("inout", inv_lerp(starts[i], starts[i] + 0.16, t))
        if i < 2:
            w *= 1 - ease("inout", inv_lerp(starts[i + 1], starts[i + 1] + 0.16, t))
        if i == 0:                               # the first focus tier is sharp from the start
            w = 1 - ease("inout", inv_lerp(starts[1], starts[1] + 0.16, t))
        blur.append(6.5 * (1 - w) * amt)
    return blur


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    k = keys(T)
    if t >= k.cut:                                   # the whip lands on the desk: THE pocket watch
        u = inv_lerp(k.cut, k.land, t)
        e = ease("out3", u)
        desk_insert(f, t, Camera(540.0, 960.0 - 760.0 * (1 - e), 1.0 + 0.14 * (1 - e)))
        if u < 0.45:                                 # the whip streak decays as it lands
            v = 3 * 760.0 * (1 - u) ** 2 / (k.land - k.cut) / FPS
            f.whip = (0.0, -min(260.0, 0.9 * v))
        return

    cam = f.set_camera(office_cam(t, k))
    dsplit = split_amount(t, k)
    D = part_amount(t, k)
    show_street = (t > 2.45 and D > 0.5) or dsplit > 0
    if show_street:
        scam = street_cam(t, k)
        focus = street_focus(t, k)
        if dsplit < 1100:                            # seen through the slit / the opening blinds
            slit = [cam.to_screen(p) for p in slit_poly(D)]

            def clip_path(c, slit=slit, half=dsplit):
                c.move_to(*slit[0])
                for q in slit[1:]:
                    c.line_to(*q)
                c.close_path()
                if half > 0.5:
                    c.rectangle(-10, 960 - half, W + 20, 2 * half)
            with f.screen(), f.clipped(clip_path):
                draw_street(f, t, k, scam, focus)
        else:
            draw_street(f, t, k, scam, focus)
        f.set_camera(cam)
    if dsplit < 1100:
        if dsplit > 0.5:                             # the blinds split: two halves slide apart
            for sgn in (-1, 1):
                def half_clip(c, sgn=sgn):
                    if sgn < 0:
                        c.rectangle(-10, -10, W + 20, 970 - dsplit)
                    else:
                        c.rectangle(-10, 960 + dsplit, W + 20, H + 20)
                with f.screen(), f.clipped(half_clip):
                    draw_office(f, t, k, cam.moved(0, -sgn * dsplit / cam.zoom))
            f.set_camera(cam)
        else:
            k_in = ease("inout", inv_lerp(0.0, 0.8, t))     # the office emerges from S04's darkness
            if k_in < 0.999:
                with f.alpha(lerp(0.1, 1.0, k_in)):
                    draw_office(f, t, k, cam)
                f.set_camera(cam)
            else:
                draw_office(f, t, k, cam)
    if t < 2.7:
        f.set_camera(cam)
        smoke_wisp(f, t, T)
    if k.whip0 < t < k.cut:
        f.whip = (0.0, -lerp(60.0, 300.0, ease("in3", inv_lerp(k.whip0, k.cut, t))))


def motion_blur(t, T):
    k = keys(T)
    if k.split0 + 0.08 < t < k.split1 - 0.05 or k.close0 < t < k.close1 + 0.02:
        return 2
    return 1


def cues(T):
    k = keys(T)
    c = [Cue(0.0, "ember_sizzle", gain_db=-24),
         Cue(k.raise0 + 0.05, "chair_creak", gain_db=-20, pan=0.35),
         Cue(k.part0 - 0.04, "blinds_rattle", gain_db=-6, pan=0.3),
         Cue(k.split0 + 0.05, "whoosh", gain_db=-14, size=0.35),
         Cue(k.ring1, "impact", gain_db=-13, size=0.2, pan=-0.3),
         Cue(k.ring2, "impact", gain_db=-13, size=0.2, pan=0.25),
         Cue(k.ring3, "impact", gain_db=-11, size=0.25, pan=-0.1),
         Cue(k.close0 + 0.06, "blinds_snap", gain_db=-4, pan=0.3),
         Cue(k.whip0, "whip", gain_db=-8)]
    # P2's tapping foot and P3's hitching footsteps, muffled through the window
    t = TAP_T0 + 0.25 / TAP_HZ
    while t < k.close0:
        c.append(Cue(t, "footstep", gain_db=-24, pan=0.3, weight=0.15, wet=1))
        t += 1 / TAP_HZ
    per = _walk_cycle_time(P3_SPEED, P3_S, P3_LIMP)
    prev, tt = None, P3_T0
    while tt < k.close0:
        n = math.floor(2 * _hitch_time(tt - P3_T0, per) / per)
        if prev is not None and n != prev and tt > 2.9:
            c.append(Cue(tt, "footstep", gain_db=-22 + (2 if n % 2 else 0), pan=-0.4 + 0.1 * (tt - 3), weight=0.5, wet=1))
        prev = n
        tt += 1 / 240
    return c
