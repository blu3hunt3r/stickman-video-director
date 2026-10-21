"""S10 - The Thread (10.083 s).

"Then I found the thread. All four victims sat on the jury that freed the Holloway killer.
 The man who murdered my partner."

Shot plan (scene-relative seconds)
  A 0.00-2.10  IN: the frame is full of crimson (S09's canopy) = an extreme macro of a red
               string; pull back + unroll until it resolves into a taut red string on the
               office evidence board (sets.OFFICE board, the four victim photos of S05). His
               LEFT hand (arm entering from the right) presses the pin home on "thread".
  B 2.10-4.30  four strings shoot from the victims to a jury card (12 faceless heads in two
               rows); crimson X marks land on four heads on "four"; the light narrows onto the
               card while the camera pushes in.
  C 4.30-4.95  smash cut, courtroom: the judge's arm lifts the gavel and slams it on "freed".
  D 4.95-6.40  tall courthouse doors swing open: one identical figure, backlit, walks out into
               the rain - free.
  E 6.40-10.08 flashback (dimmer lines, slight blur): alley in the rain, the partner holds up
               the blue badge; a muzzle flash from the dark; he falls on "murdered"; the badge
               clatters away; the detective lunges, is hit, and goes down clutching his LEFT
               leg; his pocket watch hits the ground and the glass cracks at 3:07.
               OUT: top-down, the badge spins to a stop on the wet ground - bright blue glint
               (upper right, where S11's blue police light opens).
"""
import math

from engine import *
from scenes import _lib_s08_s10 as L

OF = sets.OFFICE
BC = (500.0, 665.0)

# ----------------------------------------------------------------------------- the board
PHOTOS = (((385.0, 610.0), -4.0), ((520.0, 596.0), 3.0), ((630.0, 650.0), -2.0), ((440.0, 742.0), 5.0))
PH_W, PH_H = 82.0, 100.0           # = S05's four victim photos (same spots, same cards)


def _on_photo(i, lx, ly):
    (cx, cy), a = PHOTOS[i]
    r = math.radians(a)
    return (cx + lx * math.cos(r) - ly * math.sin(r), cy + lx * math.sin(r) + ly * math.cos(r))


PIN_TOP = [_on_photo(i, 0.0, -PH_H / 2 + 6) for i in range(4)]
A1 = _on_photo(0, 30.0, 38.0)       # victim 1, lower-right corner pin
A3 = _on_photo(2, -30.0, 40.0)      # victim 3, lower-left corner: pinned on "thread"
P2B = _on_photo(1, 0.0, 44.0)
P3B = _on_photo(2, 8.0, 44.0)
P4R = _on_photo(3, 36.0, -6.0)
STR_DIR = math.degrees(math.atan2(A3[1] - A1[1], A3[0] - A1[0]))
Z_H = 3.2                           # macro band hands over to props.red_string at this zoom
STR_W = 2.6 * Z_H ** -0.65          # physical string width (world) = engine stroke at Z_H
PS = lerp(A1, A3, 0.55)             # the point of the string the macro opens on
BOARD_CAM = (500.0, 668.0, 2.55)

JC = (595.0, 768.0)
JW, JH = 150.0, 84.0


def _head_c(row, i):
    return (542.5 + 21.0 * i, 752.0 if row == 0 else 784.0)


CONV = [(A1, (0, 1)), (P2B, (0, 4)), (P3B, (1, 5)), (P4R, (1, 2))]   # victim -> juror


T_THREAD = 1.197
U_STR = vnorm(vec(A1, A3))


def _hand_target(t):
    """His LEFT hand draws the string taut along its own axis and presses the pin home on
    'thread' (the string end is the hand until then, so the macro always sits on the string)."""
    if t < T_THREAD:
        d = 38.0 - 10.0 * ease("inout", inv_lerp(0.0, 0.9, t)) - 28.0 * ease("in", inv_lerp(0.9, T_THREAD, t))
        return (A3[0] + U_STR[0] * d, A3[1] + U_STR[1] * d)
    if t < 1.32:
        return (A3[0] - 1.5 * pulse(t, T_THREAD, 0.02, 0.06), A3[1])
    k = ease("in", inv_lerp(1.32, 1.85, t))
    return lerp(A3, (A3[0] + 460, A3[1] + 140), k)


def _arm_pose(t, hand):
    p = Pose(x=842.0, y=1054.0, s=3.0, facing=-1, la=40, le=30, ra=-10, re=10)
    p = rig.breathe(p, t, amt=0.6, seed=23)
    return rig.reach(p, "l", hand)


# ----------------------------------------------------------------------------- cameras
def _cam_a(t):
    if t <= 1.25:
        z = L.zlerp(1100.0, 3.3, ease("inout", inv_lerp(0.0, 1.25, t)))
    else:
        z = L.zlerp(3.3, BOARD_CAM[2], ease("inout", inv_lerp(1.25, 2.1, t)))
    rot = lerp(90.0 - STR_DIR, 0.0, ease("inout", inv_lerp(0.05, 1.35, t)))
    sp_end = Camera(*BOARD_CAM).to_screen(PS)
    sp = lerp((540.0, 960.0), sp_end, ease("inout", inv_lerp(0.25, 2.1, t)))
    return L.cam_anchor(PS, sp, z, rot)


def _cam_b(t):
    z = L.zlerp(BOARD_CAM[2], 6.2, ease("inout3", inv_lerp(2.16, 4.3, t)))
    c = lerp(BOARD_CAM[:2], (JC[0], JC[1] - 4), ease("inout", inv_lerp(2.16, 3.7, t)))
    cam = Camera(c[0], c[1], z)
    return cam.shaken(t, amp=1.6, rot_amp=0.06, freq=0.6, seed=31)


# ----------------------------------------------------------------------------- board drawing
def _jury_card(f, t, T, pulse_k=0.0):
    x0, y0 = JC[0] - JW / 2, JC[1] - JH / 2
    draw.rect(f, x0, y0, JW, JH, 2.6, WHITE, 1.0)
    draw.rect(f, x0 + 6, y0 + 6, JW - 12, JH - 12, 1.2, WHITE, 0.45)
    for row in (0, 1):
        for i in range(6):
            c = _head_c(row, i)
            r = 6.4 if row == 0 else 7.0
            a = 0.92 + 0.08 * pulse_k
            draw.circle(f, c, r, 1.8, WHITE, a)
            draw.stroke(f, draw.bezier_pts((c[0] - 9, c[1] + r + 7), (c[0] - 5, c[1] + r + 1),
                                           (c[0] + 5, c[1] + r + 1), (c[0] + 9, c[1] + r + 7), 6),
                        1.6, WHITE, 0.8 * a)
        yy = _head_c(row, 0)[1] + 16
        draw.line(f, (x0 + 10, yy), (x0 + JW - 10, yy), 1.4, WHITE, 0.5)
    props.pin(f, (JC[0], y0 + 5), s=0.6)


def _x_mark(f, c, k, s=1.0):
    if k <= 0:
        return
    d = 8.6 * s
    k1, k2 = clamp(k * 2), clamp(k * 2 - 1)
    a0, a1 = (c[0] - d, c[1] - d), (c[0] + d, c[1] + d)
    draw.line(f, a0, lerp(a0, a1, k1), 3.0, CRIMSON, 1.0, glow=0.7)
    if k2 > 0:
        b0, b1 = (c[0] + d, c[1] - d), (c[0] - d, c[1] + d)
        draw.line(f, b0, lerp(b0, b1, k2), 3.0, CRIMSON, 1.0, glow=0.7)


def _string_band(f, t, cam, end, alpha=1.0):
    """The macro string: a physically-sized crimson band with twisted fibres (z > Z_H)."""
    z = cam.zoom
    ux, uy = vnorm(vec(A1, end))
    px, py = -uy, ux
    h = STR_W / 2
    Ln = vlen(vec(A1, end))
    quad = [(A1[0] + px * h, A1[1] + py * h), (end[0] + px * h, end[1] + py * h),
            (end[0] - px * h, end[1] - py * h), (A1[0] - px * h, A1[1] - py * h)]
    hi = clamp(inv_lerp(math.log(30.0), math.log(1100.0), math.log(z)))
    draw.fill(f, quad, CRIMSON, alpha * lerp(1.0, 0.983, hi))
    # emissive halo like props.red_string's (2.2x wide), damped at extreme macro (= S09's canopy)
    g = lerp(0.7, 0.1, hi) * alpha
    gw = h + min(0.55 * STR_W, 26.0 / z)        # a thin halo on screen, = red_string's glow at Z_H
    gq = [(A1[0] + px * gw, A1[1] + py * gw), (end[0] + px * gw, end[1] + py * gw),
          (end[0] - px * gw, end[1] - py * gw), (A1[0] - px * gw, A1[1] - py * gw)]
    f.g.move_to(*gq[0])
    for q in gq[1:]:
        f.g.line_to(*q)
    f.g.close_path()
    f.g.set_source_rgba(CRIMSON[0], CRIMSON[1], CRIMSON[2], min(1.0, g))
    f.g.fill()
    # twisted fibres and edge shading resolve the crimson field into a cord
    fa = clamp(inv_lerp(0.04, 0.3, t)) * 0.36 * alpha
    pitch = 0.62 * STR_W
    if fa > 0 and z > 14:
        fa *= clamp((pitch * z - 10) / 40)
        vx0, vy0, vx1, vy1 = L.view_bounds(cam, 0)
        us = [((cx - A1[0]) * ux + (cy - A1[1]) * uy) for cx, cy in ((vx0, vy0), (vx1, vy0), (vx0, vy1), (vx1, vy1))]
        u0, u1 = max(0.0, min(us) - STR_W), min(Ln, max(us) + STR_W)
        wline = 0.07 * STR_W * z ** 0.65
        m0, m1 = int(u0 / pitch), int(u1 / pitch) + 1
        for m in range(m0, m1 + 1):
            uc = m * pitch
            p0 = (A1[0] + ux * (uc - 0.32 * STR_W) - px * h, A1[1] + uy * (uc - 0.32 * STR_W) - py * h)
            p1 = (A1[0] + ux * (uc + 0.32 * STR_W) + px * h, A1[1] + uy * (uc + 0.32 * STR_W) + py * h)
            draw.line(f, p0, p1, wline, BLACK, fa)
        for side in (-1, 1):
            e0 = (A1[0] + px * h * 0.86 * side, A1[1] + py * h * 0.86 * side)
            e1 = (end[0] + px * h * 0.86 * side, end[1] + py * h * 0.86 * side)
            draw.line(f, e0, e1, 0.16 * STR_W * z ** 0.65, BLACK, fa * 0.8)


def _board_shot(f, t, T):
    if t < 2.1:
        cam = _cam_a(t)
    else:
        cam = _cam_b(t)
    f.set_camera(cam)
    z = cam.zoom
    tf = T.at("four")
    xts = [tf + 0.1 * k for k in range(4)]
    spot = ease("inout", inv_lerp(2.6, 3.6, t))
    hand = _hand_target(t)
    end = hand if t < T_THREAD else A3
    # noir light: blind stripes across the board, lamp bounce, then a spot on the jury card
    bands = L.stripes((560.0, 640.0), 128.0, 7, 64.0, 0.5, 600.0, offset=0.1 * math.sin(t * 0.4))
    lights = [Light.poly(q, 0.75 * (1 - 0.55 * spot)) for q in bands]
    lights += [Light.radial(BC, 420, 0.5 * (1 - 0.6 * spot)), Light.radial(JC, 150, 0.95 * spot),
               Light.radial(PS, 90, 1.0)]
    if t < 1.9:
        lights.append(Light.radial(hand, 160, 0.8))
    amb = lerp(0.3, 0.14, spot)
    for q in bands:
        draw.fill(f, q, AMBER, 0.035 * (1 - spot), glow=0.08 * (1 - spot))
    with f.lit(lights, ambient=amb, soften=3.0):
        draw.line(f, (-300.0, OF["ceil_y"]), (1380.0, OF["ceil_y"]), 2.4, WHITE, 0.6)
        props.board(f, *OF["board"])
        props.blinds(f, *OF["window"], slats=13, tilt=0.55)
        for (c, a) in PHOTOS:
            props.photo_card(f, c, PH_W, PH_H, angle=a, pinned=True)
        _jury_card(f, t, T, pulse_k=pulse(t, T.at("jury"), 0.04, 0.4))
        if t < 1.9:
            rig.draw_figure(f, _arm_pose(t, hand))
    # crimson accents (pigment, kept readable): the old web, the found thread, pins
    props.red_string(f, [PIN_TOP[3], A1], sag=0.06, t=t)
    props.red_string(f, [PIN_TOP[0], PIN_TOP[1]], sag=0.05, t=t + 0.5)
    vib = 1.2 * pulse(t, T_THREAD, 0.01, 0.35)
    if z > Z_H:
        _string_band(f, t, cam, end)
    else:
        props.red_string(f, [A1, end], sag=0.0, vib=vib, t=t)
    props.pin(f, A1, s=0.72)
    if t < T_THREAD:
        props.pin(f, hand, s=0.72)
    else:
        pp = pulse(t, T_THREAD, 0.01, 0.12)
        props.pin(f, A3, s=0.72 * (1 + 0.45 * pp))
        if pp > 0.02:
            draw.circle(f, A3, 6 + 20 * (1 - pp), 1.2, WHITE, 0.8 * pp)
    # "All four victims sat on the jury": strings converge, X marks on "four"
    if t > 2.05:
        for k, (src, (row, i)) in enumerate(CONV):
            hc = _head_c(row, i)
            pin_pt = (hc[0], hc[1] - 10.5)
            g = ease("out3", inv_lerp(2.10 + 0.06 * k, 2.42 + 0.04 * k, t))
            if g > 0:
                props.red_string(f, [src, pin_pt], sag=0.03 * (1 - g) + 0.01, grow=g, t=t + k,
                                 vib=0.6 * pulse(t, 2.42 + 0.04 * k, 0.01, 0.25))
                props.pin(f, src, s=0.6)
            if g >= 1:
                props.pin(f, pin_pt, s=0.55)
            _x_mark(f, hc, ease("out", inv_lerp(xts[k], xts[k] + 0.09, t)))
            xp = pulse(t, xts[k], 0.02, 0.2)
            if xp > 0.02:
                draw.circle(f, hc, 9 + 18 * (1 - xp), 1.6, CRIMSON, 0.7 * xp, glow=0.5 * xp)


# ----------------------------------------------------------------------------- C: the gavel
T_GAVEL = 4.30
BLOCK = (590.0, 1190.0)             # top centre of the sound block (sits on the bench top)
BENCH_Y = 1214.0
GAV_S = 1.6
JUDGE = (1085.0, 1120.0, 3.5)       # hip x, y, scale (head and shoulder stay off frame right)


def _gavel_c(hand, ang):
    L_ = 140 * GAV_S
    return (hand[0] + L_ * math.sin(math.radians(ang)), hand[1] - L_ * math.cos(math.radians(ang)))


def _gavel_state(t, T):
    """(hand, angle) of the gavel: rises (anticipation) -> slams on 'freed' -> small recoil."""
    tf = T.at("freed")
    hit = (BLOCK[0] + 140 * GAV_S, BLOCK[1] - 40 * GAV_S)
    mid, up = (hit[0] + 12, hit[1] - 70), (hit[0] + 42, hit[1] - 170)
    if t < tf - 0.072:
        k = ease("out", inv_lerp(T_GAVEL, tf - 0.1, t))
        hand = lerp(mid, up, k)
        ang = lerp(-52.0, -6.0, k)
    elif t < tf:
        k = ease("in3", inv_lerp(tf - 0.072, tf, t))
        hand = lerp(up, hit, k)
        ang = lerp(-6.0, -90.0, k)
    else:
        r = pulse(t, tf, 0.03, 0.12)
        hand = (hit[0], hit[1] - 22 * r)
        ang = -90.0 + 14 * r
    return hand, ang


def _gavel_shot(f, t, T):
    tf = T.at("freed")
    imp = pulse(t, tf, 0.01, 0.18)
    cam = Camera(560.0, 1010.0, lerp(1.5, 1.62, ease("out", inv_lerp(T_GAVEL, 4.95, t))))
    cam = cam.shaken(t, amp=2.0 + 16 * imp, rot_amp=0.1 + 0.8 * imp, freq=2.0 + 8 * imp, seed=41)
    f.set_camera(cam)
    hand, ang = _gavel_state(t, T)
    judge = Pose(x=JUDGE[0], y=JUDGE[1], s=JUDGE[2], facing=-1, lean=-6, la=-10, le=10)
    judge = rig.breathe(judge, t, amt=0.5, seed=5)
    judge = rig.reach(judge, "r", hand)
    lamp = (590.0, 430.0)
    lights = [Light.cone(lamp, 90, 50, 900, intensity=1.0 + 0.3 * imp), Light.radial(BLOCK, 260, 0.7),
              Light.full(0.25 * imp)]
    fx.light_cone(f, lamp, 90, 46, 820, AMBER, 0.09, glow=0.25)
    with f.lit(lights, ambient=0.07, soften=4.0):
        for k in range(-2, 9):
            xx = 40.0 + k * 150.0
            draw.line(f, (xx, 250.0), (xx, BENCH_Y), 1.6, WHITE, 0.32)
        draw.line(f, (-200.0, 330.0), (1300.0, 330.0), 2.2, WHITE, 0.4)
        fx.dust(f, t, (380.0, 560.0, 800.0, 1180.0), n=46, seed=12, alpha=0.45, size=1.6)
        rig.draw_figure(f, judge)
        props.gavel(f, _gavel_c(hand, ang), angle=ang, s=GAV_S)
        # bench (its front panel hides the judge's lower body) + the sound block on it
        top = BENCH_Y
        draw.fill(f, [(-300.0, top), (1400.0, top), (1400.0, 2200.0), (-300.0, 2200.0)], BLACK, 1.0)
        draw.line(f, (-300.0, top), (1400.0, top), 4.0, WHITE, 0.95)
        draw.line(f, (-300.0, top + 40), (1400.0, top + 40), 1.8, WHITE, 0.5)
        for k in range(-3, 8):
            draw.rect(f, -120.0 + k * 230.0, top + 70, 190.0, 300.0, 1.4, WHITE, 0.3)
        bw, bh = 56.0, 24.0
        draw.fill(f, [(BLOCK[0] - bw, BLOCK[1]), (BLOCK[0] + bw, BLOCK[1]), (BLOCK[0] + bw, BLOCK[1] + bh),
                      (BLOCK[0] - bw, BLOCK[1] + bh)], BLACK, 1.0)
        draw.ellipse(f, BLOCK, bw, 10, 0, 2.6, WHITE, 0.95)
        draw.line(f, (BLOCK[0] - bw, BLOCK[1]), (BLOCK[0] - bw, BLOCK[1] + bh), 2.6, WHITE, 0.95)
        draw.line(f, (BLOCK[0] + bw, BLOCK[1]), (BLOCK[0] + bw, BLOCK[1] + bh), 2.6, WHITE, 0.95)
        draw.stroke(f, [(BLOCK[0] - bw + 56 * (1 - math.cos(math.pi * q / 12)), BLOCK[1] + bh + 10 * math.sin(math.pi * q / 12))
                        for q in range(13)], 2.6, WHITE, 0.95)
    if imp > 0.02:
        k = 1 - imp
        draw.ellipse(f, (BLOCK[0], BLOCK[1] - 4), 60 + 230 * k, 12 + 40 * k, 0, 3.0, WHITE, 0.8 * imp)
        for q in range(8):
            a = math.radians(-160 + 140 * q / 7)
            d0, d1 = 70 + 120 * k, 110 + 210 * k
            draw.line(f, (BLOCK[0] + math.cos(a) * d0, BLOCK[1] - 10 + math.sin(a) * d0 * 0.5),
                      (BLOCK[0] + math.cos(a) * d1, BLOCK[1] - 10 + math.sin(a) * d1 * 0.5), 2.4, WHITE, 0.7 * imp)


# ----------------------------------------------------------------------------- D: the doors
T_DOORS = 4.95
DOOR = (370.0, 420.0, 340.0, 780.0)          # doorway x, y, w, h  (two tall leaves)
LANDING = 1200.0
FIG_S = 0.95


def _doors_open(t):
    return ease("inout", inv_lerp(T_DOORS + 0.02, T_DOORS + 0.36, t))


def _freed_pose(t):
    """The Holloway killer: backlit in the doorway, then walks out into the rain (to the right)."""
    t_walk = 5.42
    if t < t_walk:
        p = rig.stand(540.0, LANDING, facing=0, s=FIG_S)
        return rig.breathe(p, t, amt=1.0, seed=9)
    p = rig.walk(t - t_walk, 540.0, LANDING, 250.0, facing=1, s=FIG_S, limp=0.0, arm=0.9)
    # out from under the portico he lifts his head into the rain: free
    up = ease("inout", inv_lerp(5.95, 6.3, t))
    return p.copy(head=p.head - 16 * up, lean=p.lean - 3 * up)


def _doors_shot(f, t, T, alpha=1.0):
    k = inv_lerp(T_DOORS, 6.4, t)
    cam = Camera(540.0, lerp(880.0, 905.0, ease("inout", k)), lerp(0.98, 1.07, ease("inout", k)))
    cam = cam.shaken(t, amp=2.5, rot_amp=0.12, freq=0.7, seed=44)
    f.set_camera(cam)
    op = _doors_open(t)
    dx, dy, dw, dh = DOOR
    inside = [(dx, dy), (dx + dw, dy), (dx + dw, dy + dh), (dx, dy + dh)]
    spill = [(dx, dy + dh), (dx + dw, dy + dh), (dx + dw + 260, 1460.0), (dx - 160, 1460.0)]
    lights = [Light.poly(inside, 0.95 * op), Light.poly(spill, 0.7 * op), Light.radial((1010.0, 520.0), 520, 0.55)]
    if op > 0:
        draw.fill(f, inside, AMBER, 0.2 * op, glow=0.55 * op)
        draw.gradient_fill(f, spill, [(0.0, AMBER, 0.12 * op), (1.0, AMBER, 0.0)], (540.0, dy + dh),
                           (540.0, 1460.0), glow=0.2 * op)
    with f.lit(lights, ambient=0.17, soften=4.0):
        # portico: pediment, entablature, two pairs of tall columns, steps
        draw.stroke(f, [(40.0, 300.0), (540.0, 120.0), (1040.0, 300.0)], 3.2, WHITE, 0.9, closed=True)
        draw.line(f, (20.0, 330.0), (1060.0, 330.0), 3.0, WHITE, 0.9)
        for cx in (110.0, 230.0, 850.0, 970.0):
            draw.rect(f, cx - 34, 330.0, 68.0, 26.0, 2.4, WHITE, 0.85)
            draw.line(f, (cx - 24, 356.0), (cx - 24, LANDING), 2.6, WHITE, 0.85)
            draw.line(f, (cx + 24, 356.0), (cx + 24, LANDING), 2.6, WHITE, 0.85)
            draw.line(f, (cx, 370.0), (cx, LANDING - 14), 1.2, WHITE, 0.35)
        draw.rect(f, dx - 14, dy - 14, dw + 28, dh + 14, 3.2, WHITE, 0.95)
        for i, yy in enumerate((LANDING, LANDING + 44, LANDING + 88, LANDING + 132)):
            draw.line(f, (-60.0 - 40 * i, yy), (1140.0 + 40 * i, yy), 2.8 - 0.4 * i, WHITE, 0.85)
        # the two door leaves swing open (hinged at the outer jambs)
        half = dw / 2
        for side in (-1, 1):
            hinge = dx if side < 0 else dx + dw
            free = hinge - side * half * (1 - 0.82 * op)
            sk = 26 * op
            leaf = [(hinge, dy), (free, dy + sk), (free, dy + dh - sk), (hinge, dy + dh)]
            draw.stroke(f, leaf, 3.0, WHITE, 0.95, closed=True)
            if op < 0.95:
                ix0, ix1 = min(hinge, free), max(hinge, free)
                pw = (ix1 - ix0) * 0.62
                pc = (ix0 + ix1) / 2
                draw.rect(f, pc - pw / 2, dy + 60, pw, dh * 0.38, 1.6, WHITE, 0.55 * (1 - op))
                draw.rect(f, pc - pw / 2, dy + dh * 0.5, pw, dh * 0.38, 1.6, WHITE, 0.55 * (1 - op))
        if t > T_DOORS + 0.12:
            rig.draw_figure(f, _freed_pose(t), alpha=alpha)
        fx.rain(f, t, density=1.0, wind=6, seed=33, alpha=0.9)
    fx.splashes(f, t, LANDING + 132, -100.0, 1180.0, rate=0.8, alpha=0.6)


# ----------------------------------------------------------------------------- E: the alley
T_FB = 6.40
GROUND = 1340.0
P_X, D_X, ACT_S = 600.0, 300.0, 1.05
MUZZLE = (812.0, 742.0)             # from the dark, up on a fire-escape landing (top right)
T_SHOT1, T_SHOT2 = 7.88, 8.24
T_WATCH_DROP, T_WATCH_HIT = 8.30, 8.655
T_MACRO_W, T_MACRO_B = 8.64, 9.20


def _partner_pose(t, T):
    tm = T.at("murdered")
    p0 = rig.stand(P_X, GROUND, facing=1, s=ACT_S, la=-8, ra=-6)
    up = ease("outback", inv_lerp(6.85, 7.25, t))
    p0 = p0.copy(ra=lerp(-6.0, 98.0, up), re=lerp(8.0, -6.0, up), lean=lerp(0.0, 4.0, up), head=-4 * up)
    p0 = rig.breathe(p0, t, amt=0.8, seed=13)
    jolt = pulse(t, T_SHOT1 + 0.02, 0.03, 0.18)
    p0 = p0.copy(lean=p0.lean - 12 * jolt, head=p0.head - 10 * jolt)
    if t < tm:
        return p0
    buck = rig.on_ground(Pose(x=P_X + 10, y=0, s=ACT_S, facing=1, lean=26, head=18, la=20, le=40,
                              ra=60, re=30, ll=50, lk=95, rl=38, rk=80), GROUND)
    lie = Pose(x=P_X, y=GROUND - 20, s=ACT_S, facing=1, lean=84, head=6, la=128, le=20,
               ra=100, re=30, ll=-84, lk=-8, rl=-76, rk=-14)
    if t < tm + 0.15:
        return p0.blend(buck, ease("out", inv_lerp(tm, tm + 0.15, t)))
    k = ease("in", inv_lerp(tm + 0.15, tm + 0.37, t))
    p = buck.blend(lie, k)
    b = pulse(t, tm + 0.37, 0.01, 0.08)
    return p.copy(y=p.y - 6 * b)


def _det_pose(t, T):
    d0 = rig.stand(D_X, GROUND, facing=1, s=ACT_S, la=58, le=72, ra=-6, re=10, head=14)
    d0 = rig.breathe(d0, t, amt=0.8, seed=19)
    st = pulse(t, T_SHOT1 + 0.03, 0.03, 0.2)
    d1 = d0.copy(lean=-6 * st, head=lerp(14.0, -6.0, clamp(st * 2)))
    if t < 8.0:
        return d1
    lunge = rig.on_ground(Pose(x=D_X + 85, y=0, s=ACT_S, facing=1, lean=24, head=6, la=30, le=26,
                               ra=-28, re=18, ll=34, lk=16, rl=-30, rk=26), GROUND)
    kneel = Pose(x=D_X + 100, y=GROUND - rig.SEG["thigh"] * ACT_S - 4, s=ACT_S, facing=1, lean=22, head=10,
                 ra=76, re=4, ll=72, lk=78, rl=4, rk=96)
    if t < T_SHOT2 + 0.04:
        return d1.blend(lunge, ease("inout", inv_lerp(8.0, T_SHOT2 + 0.04, t)))
    k = ease("in", inv_lerp(T_SHOT2 + 0.04, 8.52, t))
    p = lunge.blend(kneel, k)
    # the LEFT hand clutches the LEFT knee as he goes down (origin of the limp)
    J = rig.solve(p)
    grab = clamp(inv_lerp(T_WATCH_DROP - 0.02, 8.46, t))
    if grab > 0:
        tgt = (J["lk"][0] - 6, J["lk"][1] + 8)
        p = p.blend(rig.reach(p, "l", tgt), ease("out", grab))
    return p


def _watch_drop_pos(t, T):
    """The pocket watch slips from his LEFT hand at T_WATCH_DROP and falls to the ground."""
    p = _det_pose(T_WATCH_DROP, T)
    h = rig.solve(p)["lh"]
    tau = t - T_WATCH_DROP
    y = h[1] + 60 * tau + 0.5 * 2300 * tau * tau
    return (h[0] + 70 * tau, min(GROUND - 8, y))


def _alley(f, t, T, flash):
    """Side-view alley set: back wall courses, a drainpipe, a hanging lamp, wet ground."""
    draw.line(f, (-300.0, GROUND), (1380.0, GROUND), 3.2, WHITE, 0.9)
    for k in range(8):
        yy = 560.0 + k * 86.0
        draw.line(f, (-300.0, yy), (1380.0, yy), 1.2, WHITE, 0.22)
        for q in range(-2, 9):
            xx = q * 170.0 + (85.0 if k % 2 else 0.0)
            draw.line(f, (xx, yy), (xx, yy + 86.0), 1.0, WHITE, 0.16)
    draw.line(f, (150.0, 300.0), (150.0, GROUND), 3.0, WHITE, 0.6)
    draw.line(f, (172.0, 300.0), (172.0, GROUND), 1.6, WHITE, 0.4)
    draw.rect(f, 790.0, 1200.0, 150.0, 140.0, 2.4, WHITE, 0.55)          # a crate in the dark
    draw.line(f, (790.0, 1200.0), (940.0, 1340.0), 1.4, WHITE, 0.35)
    draw.line(f, (760.0, 790.0), (1200.0, 790.0), 2.6, WHITE, 0.5)        # fire-escape landing
    draw.line(f, (760.0, 760.0), (1200.0, 760.0), 1.6, WHITE, 0.35)
    for q in range(9):
        draw.line(f, (770.0 + q * 50.0, 760.0), (770.0 + q * 50.0, 790.0), 1.2, WHITE, 0.3)
    draw.line(f, (790.0, 790.0), (700.0, 1060.0), 2.0, WHITE, 0.35)       # its ladder
    draw.line(f, (820.0, 790.0), (730.0, 1060.0), 2.0, WHITE, 0.35)
    fx.puddle(f, (520.0, GROUND + 40), 150, 16, t, seed=4, alpha=0.6)
    fx.ripples(f, t, -100.0, GROUND + 10, 1180.0, GROUND + 120, rate=0.9, alpha=0.45, squash=0.25)


def _alley_shot(f, t, T, blur=2.2, dim=0.72):
    cam = Camera(lerp(520.0, 540.0, ease("inout", inv_lerp(T_FB, 8.6, t))), 1130.0,
                 lerp(1.42, 1.62, ease("inout", inv_lerp(T_FB, 8.6, t))))
    f1 = pulse(t, T_SHOT1, 0.01, 0.07)
    f2 = pulse(t, T_SHOT2, 0.01, 0.06)
    flash = max(f1, 0.7 * f2)
    cam = cam.shaken(t, amp=3.0 + 14 * flash, rot_amp=0.2 + 0.7 * flash, freq=1.0 + 6 * flash, seed=52)
    f.set_camera(cam)
    lamp_pt = (520.0, 640.0)
    lights = [Light.cone(lamp_pt, 90, 62, 900, intensity=0.95), Light.radial(MUZZLE, 900, 1.0 * flash),
              Light.full(0.42 * flash)]
    with f.blurred(blur):
        fx.light_cone(f, lamp_pt, 90, 58, 820, AMBER, 0.09, glow=0.25)
        with f.lit(lights, ambient=0.1, soften=4.0):
            _alley(f, t, T, flash)
            draw.line(f, (lamp_pt[0], 300.0), (lamp_pt[0], lamp_pt[1] - 40), 2.2, WHITE, 0.8)
            draw.stroke(f, [(lamp_pt[0] - 42, lamp_pt[1]), (lamp_pt[0] - 16, lamp_pt[1] - 40),
                            (lamp_pt[0] + 16, lamp_pt[1] - 40), (lamp_pt[0] + 42, lamp_pt[1])], 2.6, WHITE, 0.9)
            fx.rain(f, t, density=1.0, wind=8, seed=61, alpha=0.9)
            pp = _partner_pose(t, T)
            Jp = rig.draw_figure(f, pp, alpha=dim)
            pd = _det_pose(t, T)
            Jd = rig.draw_figure(f, pd, alpha=dim)
        draw.circle(f, lamp_pt, 12, 1, AMBER, 0.9, fill_it=True, glow=1.0)
        draw.glow_dot(f, lamp_pt, 200, AMBER, 0.55, core=False)
        fx.splashes(f, t, GROUND, -100.0, 1180.0, rate=0.9, alpha=0.55)
    # accents stay vivid in the memory: THE badge, the muzzle flash, the watch
    tm = T.at("murdered")
    if t < tm + 0.02:
        hand = Jp["rh"]
        ang_b = -70 + 0.6 * (pp.ra - 98)
        props.badge(f, (hand[0] + 6, hand[1] - 22), s=0.34, angle=ang_b * 0.15, glint=0.5 * pulse(t, 7.25, 0.05, 0.5))
    else:
        bp, ba = _badge_fly(t, T, Jp)
        props.badge(f, bp, s=0.34, angle=ba)
    if t < T_WATCH_DROP:
        wh = Jd["lh"]
        props.clock_face(f, (wh[0] + 4, wh[1] - 12), 11, 3, 7, w=1.8, style="pocket")
    else:
        props.clock_face(f, _watch_drop_pos(t, T), 11, 3, 7, w=1.8, style="pocket")
    for ts, k in ((T_SHOT1, 1.0), (T_SHOT2, 0.7)):
        fl = pulse(t, ts, 0.01, 0.05)
        if fl > 0.03:
            # a revolver aimed down-left from the dark (mirrored so it stays upright)
            with L.mirrored_x(f, MUZZLE[0]):
                a = 28.0
                grip = (MUZZLE[0] - 110 * math.cos(math.radians(a)) - 34 * math.sin(math.radians(a)),
                        MUZZLE[1] - 110 * math.sin(math.radians(a)) + 34 * math.cos(math.radians(a)))
                props.revolver(f, grip, angle=a, s=1.0, alpha=0.9 * fl, flash=k * fl, seed=int(ts * 10))


def _badge_fly(t, T, Jp):
    """Badge path after the partner is hit: flies, clatters at 8.45 s, slides and spins."""
    tm = T.at("murdered")
    t0 = tm + 0.02
    p0 = (P_X + 70.0, GROUND - 330.0)
    tau = t - t0
    vx, vy, g = 150.0, -150.0, 4000.0
    t_land = (-vy + math.sqrt(vy * vy + 2 * g * (GROUND - 6 - p0[1]))) / g
    if tau < t_land:
        return (p0[0] + vx * tau, p0[1] + vy * tau + 0.5 * g * tau * tau), 260 * tau
    tb = tau - t_land
    x = p0[0] + vx * t_land + 90 * (1 - math.exp(-tb * 3.5))
    bounce = 26 * abs(math.sin(min(tb, 0.2) / 0.2 * math.pi)) * (1 if tb < 0.2 else 0)
    return (x, GROUND - 6 - bounce), 260 * t_land + 900 * (1 - math.exp(-tb * 2.2))


def badge_land_t(T):
    tm = T.at("murdered")
    vy, g = -150.0, 4000.0
    p0y = GROUND - 330.0
    return tm + 0.02 + (-vy + math.sqrt(vy * vy + 2 * g * (GROUND - 6 - p0y))) / g


# ----------------------------------------------------------------------------- E2/E3 macros
def _wet_top(f, t, cam, alpha=1.0):
    L.slabs_top(f, t, alpha=alpha, box=L.view_bounds(cam, 200))
    L.ripples_top(f, t, L.view_bounds(cam, 40), rate=0.25, seed=71, alpha=0.4 * alpha)


def _watch_shot(f, t, T):
    hit = T_WATCH_HIT
    imp = pulse(t, hit, 0.01, 0.2)
    sc = 1.18 - 0.18 * ease("in", inv_lerp(T_MACRO_W, hit, t)) + 0.04 * math.sin(clamp((t - hit) / 0.12) * math.pi) * (t > hit)
    cam = Camera(540.0, 960.0, lerp(1.0, 1.1, ease("out", inv_lerp(hit, T_MACRO_B, t))))
    cam = cam.shaken(t, amp=2 + 14 * imp, rot_amp=0.2 + 0.8 * imp, freq=3 + 6 * imp, seed=61)
    f.set_camera(cam)
    c = (548.0, 930.0)
    r = 255.0 * sc
    lights = [Light.radial((c[0] - 120, c[1] - 200), 760, 1.0), Light.full(0.2 * imp)]
    with f.blurred(1.6):
        with f.lit(lights, ambient=0.14, soften=3.0):
            _wet_top(f, t, cam, alpha=0.9)
            chain = ((c[0] - 60, c[1] - r - 140), (c[0] - 260, c[1] - r - 60), (c[0] - 330, c[1] - r + 120))
            props.clock_face(f, c, r, 3, 7, w=5.0, style="pocket", second=41 if t > hit else 41 + 6 * (t - T_MACRO_W),
                             chain=chain, alpha=0.95)
            L.crack_lines(f, c, r, ease("out3", inv_lerp(hit, hit + 0.08, t)), seed=7, alpha=0.95, w=2.2)
        if imp > 0.02:
            draw.circle(f, c, r * (1.05 + 0.6 * (1 - imp)), 2.2, WHITE, 0.6 * imp)
            for q in range(10):
                a = math.radians(q * 36 + 10)
                d = r * (1.1 + 0.9 * (1 - imp))
                draw.circle(f, (c[0] + math.cos(a) * d, c[1] + math.sin(a) * d), 4 * imp + 1, 1, WHITE,
                            0.8 * imp, fill_it=True)
    L.rain_top_vp(f, t, n=90, seed=13, alpha=0.3)


def _badge_rest_angle():
    return 8.0


def _badge_state(t):
    """Top-down spin: fast spin decaying to a stop at T_STOP, a short rattle, then rest."""
    tau = t - T_MACRO_B
    T_STOP = 0.56
    w0 = 980.0
    if tau < T_STOP:
        ang = _badge_rest_angle() - 0.5 * w0 * T_STOP + w0 * tau - 0.5 * (w0 / T_STOP) * tau * tau
        wob = 0.0
    else:
        ang = _badge_rest_angle()
        wob = 7.0 * math.exp(-(tau - T_STOP) * 9.0) * math.sin((tau - T_STOP) * 38.0)
    k = ease("out", clamp(tau / T_STOP))
    pos = lerp((505.0, 820.0), (560.0, 760.0), k)
    return pos, ang + wob


T_GLINT = 9.80


def _badge_shot(f, t, T):
    cam = Camera(552.0, 985.0, lerp(1.04, 1.12, ease("inout", inv_lerp(T_MACRO_B, T.duration, t))))
    cam = cam.shaken(t, amp=2.0, rot_amp=0.1, freq=0.8, seed=63)
    f.set_camera(cam)
    pos, ang = _badge_state(t)
    s = 3.4
    glint = ease("out3", inv_lerp(T_GLINT, T_GLINT + 0.14, t))
    lights = [Light.radial(pos, 620, 1.0), Light.radial((700.0, 560.0), 420, 0.6 * glint)]
    with f.blurred(1.2):
        with f.lit(lights, ambient=0.12, soften=3.0):
            _wet_top(f, t, cam, alpha=0.85)
    fx.light_pool(f, pos, 300, 300, BLUE, 0.1 + 0.08 * glint, glow=0.3)
    fx.reflection(f, pos[0], pos[1] + 160 * s / 3.4, 160, 140, BLUE, 0.25, t, seed=5)
    with L.glow_scaled(f, 0.35):
        props.badge(f, pos, s=s, angle=ang, glint=glint)
    if glint > 0:
        gp = (pos[0] + 112, pos[1] - 132)
        tw = 0.85 + 0.15 * math.sin((t - T_GLINT) * 26)
        draw.glow_dot(f, gp, 360 * glint, BLUE, 0.95 * glint * tw, core=False)
        for q, L_ in ((0, 230), (90, 230), (45, 110), (135, 110)):
            a = math.radians(q + 8)
            d = L_ * glint * tw
            draw.line(f, (gp[0] - math.cos(a) * d, gp[1] - math.sin(a) * d),
                      (gp[0] + math.cos(a) * d, gp[1] + math.sin(a) * d), 2.6, BLUE, 0.95 * glint, glow=1.2)
        draw.circle(f, gp, 9 * glint, 1, WHITE, glint, fill_it=True, glow=1.0)
    L.rain_top_vp(f, t, n=90, seed=17, alpha=0.28)


# ----------------------------------------------------------------------------- entry points
def render(f, t, T):
    if t < T_GAVEL:
        _board_shot(f, t, T)
    elif t < T_DOORS:
        _gavel_shot(f, t, T)
    elif t < T_FB:
        _doors_shot(f, t, T)
    elif t < T_FB + 0.36:
        # into the memory: rack-defocus out of the present, refocus into the alley
        k = ease("inout", inv_lerp(T_FB, T_FB + 0.36, t))
        with f.alpha(1 - k):
            with f.blurred(2 + 14 * k):
                _doors_shot(f, t, T)
        with f.alpha(k):
            _alley_shot(f, t, T, blur=2.2 + 12 * (1 - k))
    elif t < T_MACRO_W:
        _alley_shot(f, t, T)
    elif t < T_MACRO_B:
        _watch_shot(f, t, T)
    else:
        _badge_shot(f, t, T)


def cues(T):
    tf, tfr, tm = T.at("four"), T.at("freed"), T.at("murdered")
    c = [Cue(0.05, "whoosh", gain_db=-14, size=0.5),
         Cue(T_THREAD - 0.01, "photo_pin", gain_db=-4, pan=0.2),
         Cue(T_THREAD + 0.01, "string_twang", gain_db=-6, pan=0.15),
         Cue(2.10, "string_tighten", gain_db=-7, pan=0.0)]
    for k in range(4):
        c.append(Cue(2.40 + 0.04 * k, "photo_pin", gain_db=-12 - k, pan=-0.1 + 0.08 * k))
        c.append(Cue(tf + 0.1 * k, "brush_swish", gain_db=-8, pan=0.05 * k))
    c += [Cue(T_GAVEL - 0.02, "whoosh", gain_db=-12, size=0.4),
          Cue(tfr - 0.005, "gavel", gain_db=-1),
          Cue(T_DOORS + 0.02, "door_open", gain_db=-8, pan=0.0),
          Cue(T_DOORS + 0.02, "door_creak", gain_db=-14, pan=0.1)]
    for i, tc in enumerate((5.52, 5.80, 6.08, 6.36)):
        c.append(Cue(tc, "footstep", gain_db=-12, pan=0.2 + 0.08 * i, weight=0.6, wet=1 if tc > 6.0 else 0))
    c += [Cue(T_FB - 0.2, "reverse_swell", gain_db=-10, dur=0.56),
          Cue(T_SHOT1, "gunshot_far", gain_db=-3, pan=0.6),
          Cue(T_SHOT2, "gunshot_far", gain_db=-8, pan=0.6),
          Cue(8.05, "footstep_run", gain_db=-10, pan=-0.2),
          Cue(tm + 0.36, "body_fall", gain_db=-4, pan=0.1),
          Cue(badge_land_t(T), "badge_clatter", gain_db=-5, pan=0.3),
          Cue(8.50, "land_thud", gain_db=-9, pan=-0.1),
          Cue(T_WATCH_HIT - 0.005, "watch_crack", gain_db=-2),
          Cue(T_WATCH_HIT + 0.04, "clock_stop", gain_db=-10),
          Cue(T_MACRO_B + 0.55, "badge_clatter", gain_db=-13, pan=0.1)]
    return c


def motion_blur(t, T):
    tfr = T.at("freed")
    if tfr - 0.075 < t < tfr + 0.01:
        return 4
    return 1
