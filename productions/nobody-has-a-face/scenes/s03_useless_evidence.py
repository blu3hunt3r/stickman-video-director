"""S03 - Useless Evidence (11.917 s).

"You'd think crimes get solved with faces, fingerprints, and witnesses.
 Here, our hands are lines, our faces are circles... and every witness describes everyone."

Shot plan (scene seconds)
  A 0.00-2.20  IN: the same match flame as S02's last frame (flame mid-height at (540, 1150),
               ~100 px, same pose / camera / flicker phase). His RIGHT hand raises a magnifying
               glass into the flame's light; the camera eases back; the lens insert (f.clipped,
               2.2x) shows his own LEFT hand: just the end of a line.
  B 2.20-5.62  9:16 triptych, panels slide in on "faces" / "fingerprints" / "witnesses":
               a mugshot of an empty circle head under a sweeping light, a brush dusting a glass
               that reveals one straight line, three identical witnesses shrugging in cascade.
  C 5.62-9.04  top-down: a hand inks and stamps a booking card on "hands" - the print is a line
               ("lines"); cut to a sketch artist's pencil drawing one circle (draw-on) landing on
               "circles".
  D 9.04-11.92 fast pull back: the sketch is one of dozens of identical circle sketches on the
               precinct wall; foreground witnesses point at different sketches on "describes";
               OUT: whip tilt UP into black (streaks + motion blur).
"""
import math

from engine import *
from engine.core import W, H, BLACK
from scenes import _lib_s02_s04 as L

T_B = 2.15         # panel 1 starts sliding in
T_C = 5.62         # panels gone: ink-stamp shot
T_C2 = 7.38        # cut to the sketch
T_D = 9.04         # pull back
T_WHIP = 11.42     # whip tilt up into black

PANELS = [(90.0, 250.0, 990.0, 640.0), (90.0, 665.0, 990.0, 1055.0), (90.0, 1080.0, 990.0, 1470.0)]


# ============================================================================ shot A: flame + lens
MAG = 2.2


def _cam_a(t):
    k = ease("inout3", inv_lerp(0.25, 1.7, t))
    mid = L.det_final()[3]
    return L.cam_put(mid, lerp(L.FLAME_SCREEN, (522.0, 1010.0), k), L.log_zoom(L.CUT_ZOOM, 2.55, k))


def _magnifier_state(t):
    """Lens center (world), lens radius, handle angle; the RIGHT hand holds the handle end."""
    p0, hand_l, tip, mid = L.det_final()
    k = ease("out3", inv_lerp(0.2, 1.15, t))
    glide = ease("inout", inv_lerp(1.05, 2.0, t))
    target = lerp((hand_l[0] + 38.0, hand_l[1] + 34.0), (hand_l[0] + 4.0, hand_l[1] + 2.0), glide)
    start = (hand_l[0] + 120.0, hand_l[1] + 300.0)
    c = lerp(start, target, k)
    ang = lerp(78.0, 52.0, k)
    return c, 58.0, ang


def _scene_a(f, t, T, tg, cam, mag=False):
    """Detective holding the lit match in the dark precinct (drawn normally or magnified)."""
    p0, hand_l, tip, mid = L.det_final()
    p = L.det_hold_pose(tg)
    mc, mr, mang = _magnifier_state(t)
    h_end = (mc[0] + math.cos(math.radians(mang)) * mr * 2.3, mc[1] + math.sin(math.radians(mang)) * mr * 2.3)
    if t > 0.18:
        p = rig.reach(p, "r", lerp(L.hang_target(rig.solve(p)), h_end, ease("out3", inv_lerp(0.18, 0.5, t))))
    lights = [Light.radial(tip, 300, intensity=1.0)]                 # = S02's last light rig
    lw = rig.FIG_LW * (MAG ** 0.65 if mag else 1.0)
    room = ease("inout", inv_lerp(0.3, 1.4, t))                 # precinct desk edge emerges
    with f.lit(lights, ambient=0.05, soften=3.0):
        if room > 0:
            draw.line(f, (200, 1440), (900, 1440), 3.0 * (MAG ** 0.65 if mag else 1), WHITE, 0.55 * room)
            draw.line(f, (200, 1452), (900, 1452), 1.6 * (MAG ** 0.65 if mag else 1), WHITE, 0.3 * room)
        J = rig.draw_figure(f, p, lw=lw)
    props.match(f, J["lh"], angle=L.HOLD_ANGLE, s=L.MATCH_S, lit=1.0, t=tg, seed=1)
    return J, (mc, mr, mang)


def shot_a(f, t, T, fade=1.0):
    tg = L.tglob(T, t)
    cam = _cam_a(t)
    f.set_camera(cam)
    with f.alpha(fade):
        J, (mc, mr, mang) = _scene_a(f, t, T, tg, cam)
        p0, hand_l, tip, mid = L.det_final()
        if t > 0.2:
            # lens insert: 2.2x view of his own LEFT hand - no fingers, no prints: a line.
            sc = cam.to_screen(mc)
            cam_m = L.cam_put(mc, sc, cam.zoom * MAG)
            ri = mr * 0.9
            with f.clipped(lambda c: c.arc(mc[0], mc[1], ri, 0, 2 * math.pi)):
                L.black_poly(f, [(mc[0] - ri, mc[1] - ri), (mc[0] + ri, mc[1] - ri), (mc[0] + ri, mc[1] + ri), (mc[0] - ri, mc[1] + ri)])
                with f.camera(cam_m):
                    _scene_a(f, t, T, tg, cam_m, mag=True)
            with f.lit([Light.radial(tip, 360, intensity=1.0)], ambient=0.35, soften=3.0):
                props.magnifier(f, mc, r=mr, angle=mang, w=3.4)
            draw.arc(f, mc, mr * 0.78, 200, 245, 2.2, WHITE, 0.55)            # glass glints
            draw.arc(f, mc, mr * 0.66, 205, 228, 1.6, WHITE, 0.35)


# ============================================================================ shot B: triptych
def _panel_cam(box, dx):
    return Camera(540.0 - box[0] - dx, 960.0 - box[1], 1.0)


def _slide(t, t_land, side, dur=0.24):
    t0 = t_land - dur
    k = ease("out3", inv_lerp(t0, t_land, t))
    out = ease("in3", inv_lerp(T_C - 0.3, T_C - 0.02, t))
    return side * 1150.0 * (1 - k) - side * 1150.0 * out, k > 0 and out < 1


def _panel_faces(f, t, tg):
    """Mugshot: an empty circle head in front of the lineup height chart; a light sweeps it."""
    sweep = lerp(-160.0, 1080.0, ease("inout", inv_lerp(2.3, 3.7, t)))
    push = ease("inout", inv_lerp(2.3, 3.3, t))
    lights = [Light.radial((sweep, 190.0), 300, intensity=1.0), Light.radial((450.0, 200.0), 420, intensity=0.35)]
    with f.lit(lights, ambient=0.5, soften=4.0):
        for i in range(12):
            v = 22.0 + i * 32.0
            draw.line(f, (16, v), (884, v), 2.2 if i % 3 == 0 else 1.2, WHITE, 0.62 if i % 3 == 0 else 0.34)
        s = lerp(2.35, 2.55, push)
        p = Pose(x=450, y=0, s=s, facing=0, la=11, ra=11, ll=5, rl=5)
        J0 = rig.solve(p)
        p = p.copy(y=158.0 - J0["head"][1])
        p = rig.breathe(p, tg, amt=0.6, seed=31)
        rig.draw_figure(f, p)
    fx.light_cone(f, (sweep - 140, -80), 68, 28, 420, AMBER, 0.12, glow=0.3)


def _panel_prints(f, t, tg):
    """A brush dusts a glass: the only print it reveals is one straight line."""
    base = (300.0, 376.0)
    tumb_h = 320.0
    line_top, line_len = (322.0, 120.0), 140.0
    strokes = Track([(3.33, (470.0, 120.0)), (3.52, (345.0, 150.0), "inout"), (3.70, (330.0, 210.0), "inout"),
                     (3.86, (342.0, 268.0), "inout"), (4.02, (330.0, 236.0), "inout"), (4.30, (420.0, 120.0), "inout"),
                     (4.9, (470.0, 100.0), "inout")])
    tip = strokes(t)
    rev = ease("inout", inv_lerp(3.45, 4.0, t))
    with f.lit([Light.radial((tip[0] - 10, tip[1] + 30), 260, intensity=1.0), Light.radial((330, 200), 260, 0.7)],
               ambient=0.5, soften=4.0):
        draw.line(f, (40, base[1]), (860, base[1]), 2.6, WHITE, 0.7)
        L.tumbler(f, base, h=tumb_h, w=215)
        if rev > 0:
            draw.line(f, line_top, (line_top[0], line_top[1] + line_len * rev), 7.0, WHITE, 0.95)
        # dust motes falling from the bristles
        for i in range(26):
            per = 0.5 + 0.4 * hash01(5, i)
            ph = (t / per + hash01(5, i, 1)) % 1.0
            t_emit = t - ph * per
            if t_emit < 3.36 or t_emit > 4.3:
                continue
            e = strokes(t_emit)
            x = e[0] + (hash01(5, i, 2) - 0.5) * 50 + 10 * ph
            y = e[1] + 20 + 160 * ph * ph
            draw.circle(f, (x, y), 1.8 + 1.2 * hash01(5, i, 3), 1, WHITE, 0.7 * (1 - ph), fill_it=True)
    L.brush(f, tip, angle=-36.0, s=1.25, splay=1.0 + 0.25 * math.sin(t * 18))


def _panel_witnesses(f, t, tg, T):
    """Three identical witnesses shrug, one after another."""
    w0 = T.at("witnesses")
    bulb = (450.0, -70.0)
    with f.lit([Light.cone(bulb, 90, 110, 640, intensity=1.0)], ambient=0.5, soften=4.0):
        for i, x in enumerate((165.0, 450.0, 735.0)):
            p = Pose(x=x, y=0, s=1.55, facing=0, la=7, ra=7, ll=5, rl=5, le=8, re=8)
            J0 = rig.solve(p)
            p = p.copy(y=128.0 - J0["head"][1])
            ts = w0 + 0.11 * i - 0.05
            ant = math.exp(-((t - (ts - 0.06)) / 0.06) ** 2)          # anticipation dip
            k = ease("outback", inv_lerp(ts, ts + 0.3, t)) * (1 - ease("inout", inv_lerp(5.05, 5.45, t)))
            shrug = p.copy(la=24, le=112, ra=24, re=112, head=(-1) ** i * 12.0, lean=(-1) ** (i + 1) * 2.0)
            q = p.blend(shrug, k).copy(y=p.y + 6 * ant - 8 * clamp(k))
            q = rig.breathe(q, tg + i, amt=0.7, seed=40 + i)
            rig.draw_figure(f, q)
    props.bulb(f, (450.0, -260.0), 150, swing=3 * math.sin(t * 1.7), on=1.0, t=t, glow_r=180)


def shot_b(f, t, T):
    tg = L.tglob(T, t)
    lands = [T.at("faces"), T.at("fingerprints"), T.at("witnesses")]
    fns = [lambda: _panel_faces(f, t, tg), lambda: _panel_prints(f, t, tg), lambda: _panel_witnesses(f, t, tg, T)]
    for i, (box, tl) in enumerate(zip(PANELS, lands)):
        side = -1 if i != 1 else 1
        dx, vis = _slide(t, tl, side)
        if not vis:
            continue
        x0, y0, x1, y1 = box
        with f.screen():
            L.panel_frame(f, (x0 + dx, y0, x1 + dx, y1))
            with f.clipped(lambda c, x0=x0, y0=y0, x1=x1, y1=y1: c.rectangle(x0 + dx + 3, y0 + 3, x1 - x0 - 6, y1 - y0 - 6)):
                with f.camera(_panel_cam(box, dx)):
                    fns[i]()


# ============================================================================ shot C1: the stamp
CARD_C, CARD_ANG = (600.0, 1030.0), -4.0
PAD_C = (240.0, 760.0)
STAMP_SCREEN_SHOULDER = (-260.0, -520.0)


def _stamp_hand(t, T, box_c):
    """Hand point (world) + lift 0..1 for the inking / stamping action."""
    h = T.at("hands")
    pad = (PAD_C[0] + 10, PAD_C[1])
    keys = Track([(T_C, (120.0, 420.0)), (5.86, pad, "out3"), (6.02, (pad[0] + 14, pad[1] + 6), "inout"),
                  (h - 0.02, (box_c[0] + 8, box_c[1] + 34), "inout"), (6.70, (box_c[0] + 10, box_c[1] + 36), "inout"),
                  (7.05, (60.0, 380.0), "in3")])
    lift = Track([(T_C, 1.0), (5.86, 0.0, "out3"), (6.0, 0.0), (6.16, 1.0, "out"), (h - 0.02, 0.0, "in3"),
                  (6.72, 0.0), (6.95, 1.0, "in")])
    return keys(t), lift(t)


def _cam_c1(t, T):
    k = ease("inout3", inv_lerp(6.8, 7.36, t))
    shake = pulse(t, T.at("hands"), 0.015, 0.18)
    cam = Camera(lerp(560.0, 470.0, k), lerp(980.0, 1040.0, k), L.log_zoom(1.25, 2.1, k))
    if shake > 0.01:
        cam = cam.shaken(t, amp=9 * shake, rot_amp=0.2 * shake, freq=9.0, seed=8)
    return cam


def shot_c1(f, t, T):
    cam = _cam_c1(t, T)
    f.set_camera(cam)
    tg = L.tglob(T, t)
    h = T.at("hands")
    lamp = (600.0, 880.0)
    fx.light_pool(f, lamp, 520, 520, AMBER, 0.10, glow=0.3)
    with f.lit([Light.radial(lamp, 700, intensity=1.0)], ambient=0.14, soften=4.0):
        draw.line(f, (-300, 1430), (1400, 1380), 3.0, WHITE, 0.7)                 # desk edge
        draw.line(f, (-300, 1452), (1400, 1402), 1.6, WHITE, 0.35)
        L.ink_pad(f, PAD_C)
        boxes = L.print_card(f, CARD_C, angle=CARD_ANG)
        box_c = boxes[1]
        # the print: one straight line where the "fingers" should be
        pk = ease("out", inv_lerp(6.74, 6.92, t))
        if pk > 0:
            p0 = (box_c[0] + 8, box_c[1] + 34)
            sh_w = _cam_c1(h, T).to_world(STAMP_SCREEN_SHOULDER)        # the print lies along the forearm
            ux, uy = vnorm((sh_w[0] - p0[0], sh_w[1] - p0[1]))
            p1 = (p0[0] + ux * 78, p0[1] + uy * 78)
            draw.line(f, p0, lerp(p0, p1, 1.0), 10.0, WHITE, 0.92 * pk)
            for i in range(7):
                q = lerp(p0, p1, hash01(9, i))
                draw.circle(f, (q[0] + (hash01(9, i, 1) - 0.5) * 30, q[1] + (hash01(9, i, 2) - 0.5) * 20),
                            1.4 + 1.6 * hash01(9, i, 3), 1, WHITE, 0.6 * pk, fill_it=True)
            glint = pulse(t, T.at("lines"), 0.03, 0.35)
            if glint > 0.02:
                draw.line(f, p0, p1, 10.0, AMBER, 0.6 * glint, glow=0.8 * glint)
    hand, lift = _stamp_hand(t, T, box_c)
    # the arm of an off-frame figure; nearer to the lens (bigger, softer) when lifted
    hs = cam.to_screen(hand)
    hs = (hs[0] - 50 * lift, hs[1] - 70 * lift)
    with L.soft(f, 6.0 * lift, alpha=1.0 - 0.12 * lift):
        L.offscreen_arm(f, hs, STAMP_SCREEN_SHOULDER, side="l", lw_px=15.0 * (1 + 0.3 * lift))
    ring = pulse(t, h, 0.02, 0.25)
    if ring > 0.02:
        draw.circle(f, (box_c[0] + 8, box_c[1] + 34), 30 + 60 * (1 - ring), 2.0, WHITE, 0.5 * ring)


# ============================================================================ shot C2: the sketch
SHEET_C = (540.0, 900.0)
CIRCLE_C = (SHEET_C[0], SHEET_C[1] - L.SKETCH_H * 0.08)


def _draw_k(t, T):
    return ease("inout", inv_lerp(T.at("faces", 1) + 0.02, T.at("circles") + 0.28, t))


def _pencil_tip(t, T):
    k = _draw_k(t, T)
    a = math.radians(-120.0 + 360.0 * k * 1.06)
    on = (CIRCLE_C[0] + math.cos(a) * 82, CIRCLE_C[1] + math.sin(a) * 82)
    a0 = math.radians(-120.0)
    start = (CIRCLE_C[0] + math.cos(a0) * 82, CIRCLE_C[1] + math.sin(a0) * 82)
    approach = ease("out3", inv_lerp(T_C2, T.at("faces", 1) + 0.02, t))
    leave = ease("inout", inv_lerp(T.at("circles") + 0.34, 8.95, t))
    p = lerp((start[0] + 260, start[1] + 120), start, approach) if k <= 0 else on
    return lerp(p, (on[0] + 300, on[1] + 260), leave), leave


def _wall_cam(t, T):
    """C2 close-up on the sheet -> D fast pull back -> whip tilt up into black."""
    k = ease("inout", inv_lerp(T_D + 0.04, 10.25, t))
    push = ease("inout", inv_lerp(T_C2, T_D, t))
    z0 = lerp(2.15, 2.35, push)
    z = L.log_zoom(z0, 0.36, k)
    y = lerp(SHEET_C[1] + 10, SHEET_C[1] + 160, k)
    w = ease("in3", inv_lerp(T_WHIP, T.duration, t))
    y -= 7600.0 * w
    return Camera(SHEET_C[0], y, z), w


SHEET_GRID = [(i, j) for j in range(-7, 8) for i in range(-4, 5)]


def _sheet_pose(i, j):
    c = (SHEET_C[0] + i * 340.0 + (hash01(3, i, j) - 0.5) * 26, SHEET_C[1] + j * 430.0 + (hash01(4, i, j) - 0.5) * 22)
    ang = 0.0 if (i, j) == (0, 0) else (hash01(5, i, j) - 0.5) * 7.0
    return c, ang


WIT_X = (150.0, 345.0, 540.0, 735.0, 930.0)
WIT_TARGETS = [(1, 0), (-4, 1), (3, 0), (-2, -1), (0, 1)]          # one sketch each (grid i, j)


def _wall_light(t, T, i, j):
    """Amber accent on a sketch: pointed at by a witness, or the wave on "everyone"."""
    a = 0.0
    d = T.at("describes")
    for n, tg_ in enumerate(WIT_TARGETS):
        if tg_ == (i, j):
            ta = d - 0.12 + 0.07 * n
            a = max(a, ease("out3", inv_lerp(ta + 0.12, ta + 0.32, t)) * (1 - ease("inout", inv_lerp(11.2, 11.5, t))))
    e = T.at("everyone")
    dist = math.hypot(i * 340.0, j * 430.0)
    a = max(a, 0.85 * pulse(t, e + dist / 4200.0, 0.06, 0.32))
    return a


def shot_wall(f, t, T):
    tg = L.tglob(T, t)
    cam, w = _wall_cam(t, T)
    f.set_camera(cam)
    kp = ease("inout", inv_lerp(T_D + 0.04, 10.25, t))
    light_r = lerp(700.0, 1750.0, kp)
    lights = [Light.radial((SHEET_C[0], SHEET_C[1] + 100), light_r, intensity=1.0)]
    k_draw = _draw_k(t, T)
    rack = ease("inout", inv_lerp(9.65, 10.1, t))
    hl = []
    with f.lit(lights, ambient=lerp(0.3, 0.14, kp), soften=4.0):
        with L.soft(f, 4.5 * rack * (1 - w)):
            if kp > 0:
                draw.line(f, (-2600, SHEET_C[1] + 7.6 * 430), (3700, SHEET_C[1] + 7.6 * 430), 3.0, WHITE, 0.6)
            for (i, j) in SHEET_GRID:
                c, ang = _sheet_pose(i, j)
                if (i, j) == (0, 0):
                    L.sketch_sheet(f, c, ang, k=k_draw)
                elif abs(i) <= 1 and abs(j) <= 1 or kp > 0.001:
                    L.sketch_sheet(f, c, ang, alpha=0.9)
                if t > 9.9:
                    a = _wall_light(t, T, i, j)
                    if a > 0.02:
                        hl.append((c, ang, a))
    for c, ang, a in hl:                                   # accents stay bright (not in the lit group)
        w2, h2 = L.SKETCH_W / 2, L.SKETCH_H / 2
        pts = L._xf([(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)], c, ang)
        draw.stroke(f, pts, 3.0, AMBER, a, closed=True, glow=0.6 * a)
        L.sketch_circle(f, L._xf([(0, -L.SKETCH_H * 0.08)], c, ang)[0], 82.0, 1.0, a, ang)
    if t < T_D + 0.2:
        tip, leave = _pencil_tip(t, T)
        ang = -38.0
        L.pencil(f, tip, angle=ang, length=300.0, alpha=1.0)
        grip = (tip[0] + math.cos(math.radians(ang)) * 92, tip[1] + math.sin(math.radians(ang)) * 92)
        gs = cam.to_screen(grip)
        L.offscreen_arm(f, gs, (1620.0, gs[1] + 120.0), side="l", lw_px=14.0, flip=True)
    _witnesses_fg(f, t, T, w, cam)
    if w > 0:
        v = 7600.0 * cam.zoom * 3 * inv_lerp(T_WHIP, T.duration, t) ** 2 / (T.duration - T_WHIP) / 24.0
        f.whip = (0.0, min(420.0, 0.7 * v))


def _witnesses_fg(f, t, T, w, cam):
    """Near layer (screen space): five identical witnesses, each pointing at a different sketch."""
    rise = ease("out3", inv_lerp(9.25, 10.05, t))
    if rise <= 0:
        return
    d = T.at("describes")
    e = T.at("everyone")
    dy = lerp(900.0, 0.0, rise) + 2600.0 * ease("in3", inv_lerp(T_WHIP, T.duration, t))
    cam_end, _ = _wall_cam(10.6, T)
    with f.screen():
        with L.soft(f, lerp(5.0, 0.0, ease("inout", inv_lerp(9.6, 10.1, t)))):
            for i, x in enumerate(WIT_X):
                p = Pose(x=x, y=0, s=1.15, facing=0, la=7, ra=7, ll=5, rl=5)
                J0 = rig.solve(p)
                p = p.copy(y=1330.0 - J0["head"][1] + dy + 10 * (i % 2))
                p = rig.breathe(p, t + 3 * i, amt=0.8, seed=60 + i)
                J = rig.solve(p)
                ta = d - 0.12 + 0.07 * i
                k = ease("outback", inv_lerp(ta, ta + 0.26, t))
                c, _a = _sheet_pose(*WIT_TARGETS[i])
                ts = cam_end.to_screen(c)
                aim = math.degrees(math.atan2(ts[1] - J["shoulder"][1], ts[0] - J["shoulder"][0]))
                aim += (14.0 if i % 2 else -14.0) * ease("inout", inv_lerp(e, e + 0.3, t))   # "everyone": they waver
                side = "r" if ts[0] < J["shoulder"][0] else "l"       # front view: right arm is screen-left
                L_ = 127.0 * p.s
                tgt = (J["shoulder"][0] + math.cos(math.radians(aim)) * L_, J["shoulder"][1] + math.sin(math.radians(aim)) * L_)
                p = p.blend(rig.reach(p, side, tgt), clamp(k)) if k < 1 else rig.reach(p, side, tgt)
                rig.draw_figure(f, p, alpha=0.85)


# ============================================================================ module API
def render(f, t, T):
    tf = L.frame_t(t)
    if tf < T_C:
        fade = lerp(1.0, 0.32, ease("inout", inv_lerp(T_B + 0.02, T_B + 0.3, t)))
        fade *= 1.0 - ease("inout", inv_lerp(T.at("witnesses") - 0.1, T.at("witnesses") + 0.2, t))
        if fade > 0.001:
            shot_a(f, t, T, fade)
        if tf >= T_B:
            shot_b(f, t, T)
    elif tf < T_C2:
        shot_c1(f, t, T)
    else:
        shot_wall(f, t, T)


def cues(T):
    h = T.at("hands")
    return [
        Cue(0.24, "whoosh", gain_db=-20, size=0.15),
        Cue(T.at("faces") - 0.22, "whoosh", gain_db=-15, size=0.3, pan=-0.4),
        Cue(T.at("faces") + 0.01, "camera_shutter", gain_db=-14),
        Cue(T.at("fingerprints") - 0.22, "whoosh", gain_db=-15, size=0.3, pan=0.4),
        Cue(3.40, "brush_swish", gain_db=-10, pan=0.1),
        Cue(3.72, "brush_swish", gain_db=-11, pan=0.05),
        Cue(3.98, "brush_swish", gain_db=-12, pan=0.1),
        Cue(T.at("witnesses") - 0.22, "whoosh", gain_db=-15, size=0.3, pan=-0.4),
        Cue(T_C - 0.28, "whoosh", gain_db=-14, size=0.35),
        Cue(5.86, "impact", gain_db=-16, size=0.08),
        Cue(h - 0.01, "impact", gain_db=-9, size=0.25),
        Cue(6.76, "paper_rustle", gain_db=-16),
        Cue(T.at("faces", 1), "pencil_scratch", gain_db=-9, dur=T.at("circles") + 0.3 - T.at("faces", 1)),
        Cue(T_D + 0.02, "whoosh", gain_db=-12, size=0.45),
        Cue(T_D + 0.1, "paper_rustle", gain_db=-14),
        Cue(T_WHIP + 0.02, "whip", gain_db=-5),
    ]


def motion_blur(t, T):
    if t > T_WHIP + 0.06:
        return 3
    for tl in (T.at("faces"), T.at("fingerprints"), T.at("witnesses")):
        if tl - 0.2 < t < tl - 0.03:
            return 4
    if T_C - 0.25 < t < T_C - 0.02:
        return 4
    if T_D + 0.15 < t < 9.85:
        return 2
    return 1
