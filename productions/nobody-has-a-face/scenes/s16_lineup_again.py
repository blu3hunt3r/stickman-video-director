"""S16 - The Lineup, Again (8.292 s) - callback to S01.

"They put me in the lineup. The witness couldn't see my face. She didn't need to.
 She watched me walk."

Shot plan (scene seconds)
  0.00-0.60  IN: S15's cold burnt match keeps tumbling exactly where S15 left it (centre (540, 960),
             283.6 px, 76.6 deg = S15's last angle + 1 frame, 72 deg/s, camera roll -6 deg, room
             racked out of focus); the follow-cam decelerates and levels while real-time gravity
             takes over; it lands tip-first beside his LEFT foot, topples flat, two ash puffs.
  0.60-0.84  whip tilt up to the swinging bulb (S01's opening framing).
  0.84-2.30  "They put me in the lineup." - fast tilt down the amber cone (faster echo of S01) onto
             the height-chart wall: five identical figures, he stands at the CENTER position.
  2.30-3.15  "The witness..." - her huge trembling arm rises in the foreground (S01 design), finger
             wandering figure to figure; number one steps out of the line.
  3.15-5.55  THE WALK TEST: three low inserts on the taped walk line (hips down - no faces), one
             figure at a time, even gaits; every footfall sits on one 0.42 s metronome.
  5.55-8.29  "She watched me walk." - his legs in the same framing: short step, long step
             (limp 0.85, re-timed so the RHYTHM limps; amber "habit" rings mark where his feet
             land); the camera rises with him; the arm stops
             trembling and points on "walk"; the bulb stops swinging, the cone closes on him, the
             others sink into darkness; he turns to the glass; push into his hollow head.
             OUT: head ring centered at (540, 960), r = 200 px, black elsewhere.
"""
import math

from engine import *
from scenes._lib_s16_s18 import (RING_R, RING_S, Gait, cam_lerp, ek, log_zoom, puff, streak,
                                 witness_arm)

L = sets.LINEUP
FLOOR = L["floor_y"]
XS = L["xs"]
ANCHOR = L["bulb_anchor"]
CORD = L["cord"]

SWING_PERIOD = 3.2                       # S01
SWING_AMP = 14.0
SWING_T0 = 0.054                         # phase: the cone is sweeping over the match as it lands
Y_W, S_W = 1580.0, RING_S                # the taped walk line in front of the lineup
HEAD_R = rig.SEG["head_r"] * S_W
Z_END = RING_R / HEAD_R                  # ~5.25

# ---------------------------------------------------------------- beat times
T_WHIP0, T_WHIP1 = 0.60, 0.84
T_WIDE = 2.30
T_CUT1, T_CUT2, T_CUT3, T_HIS = 3.15, 3.95, 4.75, 5.55
T_RISE0, T_RISE1 = 5.92, 6.42
T_STOP = 6.71                            # his last (right) footfall, then he closes and stands
T_TURN0, T_TURN1 = 7.05, 7.35
T_PUSH0 = 7.00
METRO = 0.42                             # the others' even step

# ---------------------------------------------------------------- cameras
CAM_A = Camera(606.0, 1320.0, 5.0)       # floor insert (match lands)
CAM_BULB = Camera(540.0, 800.0, 3.0)     # S01 opening framing
WIDE = Camera(540.0, 1190.0, 1.34)       # S01 wide composition
WIDE2 = Camera(540.0, 1196.0, 1.38)
Z_INS = 4.8                              # walk-test inserts: hips down
INS_FLOOR_SCREEN = 1330.0                # walk line on screen in the inserts (heads out of frame)
MW = Camera(560.0, 1225.0, 1.52)         # medium-wide after the rise
INS_HAND = (520.0, 1600.0)               # the witness's hand in the low inserts (clear of the feet)

# ---------------------------------------------------------------- the falling match (continues S15)
# S15 ends following its burnt match: centre at screen (540, 960), 283.6 px long, tip down,
# screen angle 73.6 deg turning +3 deg/frame, camera zoom 3.5 on a 2x world with a -6 deg roll.
M_S = 0.95                                   # S15: match 1.9 for a 2.0 figure -> same proportion here
M_L = 52.0 * M_S                             # props.match length at this scale
M_LE = M_L * 0.82                            # burnt (curled) length == S15's MATCH_L at this scale
Z_FOLLOW, ROLL_FOLLOW = 283.6 / M_LE, -6.0   # ~7.0: identical on-screen size at the cut
M_A0 = 76.6 - ROLL_FOLLOW                    # world angle at our first frame (S15 last + 1 frame)
M_W = 72.0                                   # deg/s tumble (S15's rate at its end)
M_V0 = 243.0                                 # world px/s: S15's fall speed at its end, rescaled
G = 1930.0                                   # px/s^2 (344 px figure ~ 1.75 m): real time resumes
M_X = 604.0
C_Y = FLOOR - 3.6                            # where the curled tip touches the floor line
T_HIT = 0.29                                 # tip hits
T_SLAP = 0.46                                # the match has toppled flat
T_REST = 0.56


def _match_geom(base, a):
    """Tip (curl end) of props.match(burnt=1) and its centre, for a base point and angle."""
    d = (math.cos(math.radians(a)), math.sin(math.radians(a)))
    mid = (base[0] + d[0] * 0.72 * M_L, base[1] + d[1] * 0.72 * M_L)
    c = (math.cos(math.radians(a + 35)), math.sin(math.radians(a + 35)))
    tip = (mid[0] + c[0] * 0.22 * M_L, mid[1] + c[1] * 0.22 * M_L)
    return tip, (base[0] + d[0] * 0.45 * M_LE, base[1] + d[1] * 0.45 * M_LE)


def _base_from_tip(tip, a):
    """Base point that puts the curl end at `tip` for angle a (rigid match)."""
    t0, _ = _match_geom((0.0, 0.0), a)
    return (tip[0] - t0[0], tip[1] - t0[1])


A_HIT = M_A0 + M_W * T_HIT                   # ~103.5 deg: it lands tip first


def _free_centre(t):
    return (M_X + 7.0 * t, 0.0)


# solve the start height so that the curl end touches the floor exactly at T_HIT
_tip_hit, _c_hit = _match_geom((0.0, 0.0), A_HIT)
M_Y0 = (C_Y - (_tip_hit[1] - _c_hit[1])) - (M_V0 * T_HIT + 0.5 * G * T_HIT ** 2)
TIP_HIT = (M_X + 7.0 * T_HIT + (_tip_hit[0] - _c_hit[0]), C_Y)


def _match_state(t):
    """(base, angle) of the burnt match: free fall, tip-first hit, clockwise topple, rest."""
    if t < T_HIT:
        a = M_A0 + M_W * t
        c = (M_X + 7.0 * t, M_Y0 + M_V0 * t + 0.5 * G * t * t)
        d = (math.cos(math.radians(a)), math.sin(math.radians(a)))
        return (c[0] - d[0] * 0.45 * M_LE, c[1] - d[1] * 0.45 * M_LE), a
    if t < T_SLAP:
        u = (t - T_HIT) / (T_SLAP - T_HIT)
        a = A_HIT + (180.0 - A_HIT) * ease("in", u)           # falls over about its tip
        tip = (TIP_HIT[0] - 2.0 * u, C_Y - 6.0 * ease("in", u) - 3.0 * math.sin(math.pi * min(1.0, u * 2.0)))
        return _base_from_tip(tip, a), a
    u = clamp((t - T_SLAP) / (T_REST - T_SLAP))
    a = 180.0 - 2.0 * math.sin(math.pi * u) * (1 - u)          # tiny rock as it settles
    tip = (TIP_HIT[0] - 2.0, C_Y - 6.0 - 1.5 * math.sin(math.pi * u))
    return _base_from_tip(tip, a), a


T_SETTLE = 0.36                              # the follow-cam has settled on the floor insert


def _open_cam(t):
    """S15's follow-cam continued: it starts locked on the falling match (zoom ~7, -6 deg roll,
    same speed as the match), then decelerates on a Hermite curve that never overtakes it, so
    the match only drifts DOWN the frame as real-time gravity takes over; it levels out and
    pulls back to the floor insert."""
    u = clamp(t / T_SETTLE)
    D = CAM_A.y - M_Y0
    if t < T_SETTLE:
        c2 = (3 * D - 2 * M_V0 * T_SETTLE) / T_SETTLE ** 2
        c3 = (-2 * D + M_V0 * T_SETTLE) / T_SETTLE ** 3
        y = M_Y0 + M_V0 * t + c2 * t * t + c3 * t ** 3
    else:
        y = CAM_A.y
    k = ease("inout", u)
    x = lerp(M_X + 7.0 * t, CAM_A.x, k)
    z = log_zoom(Z_FOLLOW, CAM_A.zoom, k) * (1.0 + 0.05 * ek("inout", 0.30, T_WHIP0, t))
    return Camera(x, y, z, lerp(ROLL_FOLLOW, 0.0, ek("inout", 0.0, 0.42, t)))


# ---------------------------------------------------------------- the bulb
def _swing(t):
    amp = SWING_AMP * (1.0 - ek("out3", 6.38, 7.25, t))
    return amp * math.sin(2 * math.pi * (t - SWING_T0) / SWING_PERIOD)


def _bulb_center(swing):
    bdir = 90.0 - swing
    r = CORD + 46.0
    return (ANCHOR[0] + math.cos(math.radians(bdir)) * r, ANCHOR[1] + math.sin(math.radians(bdir)) * r), bdir


def _bulb_on(t):
    return 0.93 + 0.07 * flicker(t, 3, rate=12, depth=0.6)


# ---------------------------------------------------------------- figures
def _line_pose(k, t):
    p = rig.stand(XS[k], FLOOR, facing=0)
    p = p.copy(la=6 + 3 * (k % 2), ra=6 + 2 * ((k + 1) % 2))
    return rig.breathe(p, t, amt=0.9, seed=11 + 7 * k)


def _gait_at(x_mid, t_mid, facing, t0, h0, limp=0.0, d_left=METRO, d_right=METRO, t_stop=None):
    """A Gait whose hip is at x_mid at time t_mid."""
    g = Gait(0.0, Y_W, S_W, facing, limp=limp, t0=t0, h0=h0, d_left=d_left, d_right=d_right, t_stop=t_stop)
    dx = x_mid - g.pose(t_mid).x
    return Gait(dx, Y_W, S_W, facing, limp=limp, t0=t0, h0=h0, d_left=d_left, d_right=d_right, t_stop=t_stop)


# three insert walkers: (t_in, t_out, facing, first footfall, h at that footfall, hip x mid-insert)
INSERTS = [(T_CUT1, T_CUT2, 1, 3.27, 2.0, 500.0),
           (T_CUT2, T_CUT3, -1, 4.11, 3.0, 760.0),
           (T_CUT3, T_HIS, 1, 4.95, 2.0, 420.0)]
WALKERS = [_gait_at(xm, 0.5 * (a + b), fc, tf, h0) for (a, b, fc, tf, h0, xm) in INSERTS]
WALKER_SPOT = [0, 4, 1]                  # whose place in the line is empty during that insert

# the detective, the engine's limp (quick stance on the injured LEFT leg): L lands 5.58, R 5.91,
# L 6.38 - the bad step lands exactly on "walk" - R 6.71, then he closes and stands
X_END = 590.0                            # his mark: clear of the back row when she points
HIS_T0, HIS_DR, HIS_DL = 5.58, 0.33, 0.47
_g0 = Gait(0.0, Y_W, S_W, 1, limp=0.85, t0=HIS_T0, h0=2.0, d_left=HIS_DL, d_right=HIS_DR, t_stop=T_STOP)
_rf0 = rig.solve(_g0.pose(T_STOP))["rf"][0]
HIS = Gait(X_END + 10.0 - _rf0, Y_W, S_W, 1, limp=0.85, t0=HIS_T0, h0=2.0, d_left=HIS_DL, d_right=HIS_DR,
           t_stop=T_STOP)


HIS_FALLS = HIS.footfalls(T_HIS - 0.01, T_STOP + 0.01)


def _his_pose(t):
    """The detective: centre of the line until the walk test, then his walk, close, turn."""
    if t < T_HIS:
        return _line_pose(2, t)
    p = HIS.pose(t)
    if t > T_STOP:
        side = rig.breathe(rig.stand(X_END, Y_W, facing=1, s=S_W), t, amt=0.7, seed=29)
        p = p.blend(side, ek("inout", T_STOP, T_STOP + 0.3, t))
        if t > T_TURN0:
            front = rig.breathe(rig.stand(X_END, Y_W, facing=0, s=S_W), t, amt=0.7, seed=29)
            p = p.blend(front, ek("inout", T_TURN0, T_TURN1, t))
    return p


def _step_out_pose(t):
    """Number one turns and steps out of the line just before the first insert."""
    base = _line_pose(0, t)
    if t < 2.92 or t >= T_CUT1:
        return base
    g = Gait(0.0, FLOOR, 1.0, 1, t0=3.08, h0=1.0, d_left=METRO, d_right=METRO)
    dx = XS[0] - g.pose(2.92).x
    g = Gait(dx, FLOOR, 1.0, 1, t0=3.08, h0=1.0, d_left=METRO, d_right=METRO)
    return base.blend(g.pose(t), ek("inout", 2.92, 3.02, t))


# ---------------------------------------------------------------- camera
def _ins_cam(i, t):
    a, b, fc, tf, h0, xm = INSERTS[i]
    tm = 0.5 * (a + b)
    hx = WALKERS[i].pose(t).x
    cx = xm + 0.65 * (hx - xm)                     # track at 2/3 of the walker's speed
    cy = Y_W - (INS_FLOOR_SCREEN - 960.0) / Z_INS
    z = Z_INS * (1.0 + 0.03 * (t - tm))
    return Camera(cx, cy, z).shaken(t, amp=3.0, rot_amp=0.12, freq=0.9, seed=60 + i)


def _his_ins_cam(t):
    p = HIS.pose(min(t, T_STOP))
    cy = Y_W - (INS_FLOOR_SCREEN - 960.0) / Z_INS
    hx0 = HIS.pose(T_HIS).x
    cx = hx0 + 30.0 + 0.62 * (p.x - hx0)
    return Camera(cx, cy, Z_INS)


T_LAST = 8.25                            # last frame of the scene (198 / 24)


def _camera(t):
    if t < T_WHIP0:
        return _open_cam(t)
    if t < T_WIDE:
        if t < T_WHIP1:
            a = _open_cam(T_WHIP0)
            k = ek("inout3", T_WHIP0, T_WHIP1, t)
            return cam_lerp(a, CAM_BULB, k)
        k = ek("inout3", T_WHIP1 + 0.08, T_WIDE, t)
        drift = CAM_BULB.moved(dy=6.0 * ek("out", T_WHIP1, T_WHIP1 + 0.1, t))
        return cam_lerp(drift, WIDE, k).shaken(t, amp=2.0, rot_amp=0.12, freq=0.7, seed=21)
    if t < T_CUT1:
        k = ek("inout", T_WIDE, 3.6, t)
        return cam_lerp(WIDE, WIDE2, k).shaken(t, amp=2.2, rot_amp=0.15, freq=0.7, seed=21)
    if t < T_HIS:
        i = 0 if t < T_CUT2 else (1 if t < T_CUT3 else 2)
        return _ins_cam(i, t)
    if t < T_PUSH0:
        ins = _his_ins_cam(t)
        k = ek("inout", T_RISE0, T_RISE1, t)
        c = cam_lerp(ins, MW, ek("sine", T_RISE0, T_RISE1, t), kz=k)
        return c.shaken(t, amp=2.0 * (1 - k) + 1.2, rot_amp=0.1, freq=0.8, seed=71)
    # push into his head: the ring ends exactly at screen centre, r = 200 px
    head = rig.solve(_his_pose(t))["head"]
    k = ek("inout3", T_PUSH0, T_LAST, t)
    start = MW.shaken(T_PUSH0, amp=1.2, rot_amp=0.1, freq=0.8, seed=71)
    cam = Camera(lerp(start.x, head[0], k), lerp(start.y, head[1], ek("inout", T_PUSH0, T_LAST - 0.05, t)),
                 log_zoom(start.zoom, Z_END, k), lerp(start.rot, 0.0, k))
    return cam


# ---------------------------------------------------------------- drawing
def _walk_line(f, alpha=0.55):
    """The taped walk line: a floor line with short tape ticks (no numbers)."""
    draw.line(f, (-300, Y_W), (1380, Y_W), 2.6, WHITE, alpha)
    for i in range(-6, 30):
        x = i * 48.0
        draw.line(f, (x, Y_W + 6), (x + 22, Y_W + 6), 2.0, WHITE, alpha * 0.55)


def _room(f, t, lights, ambient, line=(), hidden=(), blur_back=0.0, back_alpha=1.0, dust_alpha=0.6,
          step_out=False, blur_all=0.0):
    """Lineup room + figures inside the noir light reveal (S01 look)."""
    if blur_all > 0.4:
        with f.blurred(blur_all):
            _room(f, t, lights, ambient, line, hidden, blur_back, back_alpha, dust_alpha, step_out)
        return
    def back():
        sets.lineup_room(f, glass=False, alpha=back_alpha)
        for k in range(5):
            if k == 2 or k in hidden:
                continue
            p = _step_out_pose(t) if (k == 0 and step_out) else _line_pose(k, t)
            rig.draw_figure(f, p, alpha=back_alpha)

    with f.lit(lights, ambient=ambient, soften=4.0):
        if blur_back > 0.4:
            with f.blurred(blur_back):
                back()
        else:
            back()
        _walk_line(f, 0.55 * back_alpha)
        if dust_alpha > 0:
            size = 2.2 * min(1.0, (1.4 / f.cam.zoom) ** 0.7)       # motes keep a sane size in close-ups
            fx.dust(f, t, (120, 640, 960, 1640), n=130, seed=17, alpha=dust_alpha, size=size)
        for p in line:
            rig.draw_figure(f, p)


def _streak_vec(t):
    """Vertical motion streak (screen px) for the whip up to the bulb and the rise with him."""
    if T_WHIP0 < t < T_WHIP1:
        return 0.0, -320.0 * (1.0 - abs(2 * ek("linear", T_WHIP0, T_WHIP1, t) - 1))
    if T_RISE0 < t < T_RISE1:
        return 0.0, 150.0 * math.sin(math.pi * ek("linear", T_RISE0, T_RISE1, t)) ** 2
    return 0.0, 0.0


def render(f, t, T):
    sx, sy = _streak_vec(t)
    with streak(f, sx, sy):
        _render(f, t, T)


def _render(f, t, T):
    cam = _camera(t)
    f.set_camera(cam)
    swing = _swing(t)
    bc, bdir = _bulb_center(swing)
    on = _bulb_on(t)

    # isolation: the cone closes on him, then the light shrinks to his head
    iso = ek("inout", 6.45, 7.35, t)
    focus = ek("inout", 7.30, 8.05, t)
    hisp = _his_pose(t)
    J = rig.solve(hisp)

    last = 1.0 - ek("inout", 7.95, 8.18, t)        # the lit picture hands over to the bare ring
    spread = lerp(74.0, 26.0, iso)
    lights = [Light.cone(bc, bdir, spread, 1100, intensity=on * (1 - focus)),
              Light.radial(bc, 260, intensity=0.7 * on * (1 - iso))]
    if t >= T_HIS:
        lights.append(Light.radial(J["head"], lerp(300.0, 1.5 * J["head_r"], focus), intensity=iso * last))
    ambient = lerp(0.12, 0.0, iso)

    haze = 0.11 * on * (1 - focus) * (1 - 0.5 * iso)
    if haze > 0.002:
        fx.light_cone(f, bc, bdir, lerp(70.0, 24.0, iso), 1050, AMBER, haze, glow=0.35 * on * (1 - focus))

    if t < T_CUT1:
        # ---------------- floor insert / whip / tilt / wide (S01 composition)
        rack = 7.0 * (1.0 - ek("inout", 0.04, 0.40, t))    # S15 ends racked onto the match
        _room(f, t, lights, ambient, line=[_line_pose(2, t)], step_out=True, blur_all=rack)
        if t < T_WHIP1 + 0.05:
            base, a = _match_state(t)
            props.match(f, base, angle=a, length=52, s=M_S, burnt=1.0, t=t, seed=7)
            tip, _ = _match_geom(base, a)
            puff(f, (TIP_HIT[0], C_Y - 2), t, T_HIT, seed=3, size=0.8, alpha=0.55)
            puff(f, (TIP_HIT[0] + 0.8 * M_LE, C_Y - 1), t, T_SLAP, seed=9, size=0.5, alpha=0.4)
    elif t < T_HIS:
        # ---------------- the walk test inserts
        i = 0 if t < T_CUT2 else (1 if t < T_CUT3 else 2)
        wp = WALKERS[i].pose(t)
        _room(f, t, lights, ambient, line=[wp], hidden=(WALKER_SPOT[i],), blur_back=12.0,
              back_alpha=0.45, dust_alpha=0.75)
    else:
        # ---------------- his walk, the point, isolation, push
        rise = ek("inout", T_RISE0, T_RISE1, t)
        _room(f, t, lights, ambient, line=[hisp], blur_back=12.0 * (1 - rise),
              back_alpha=lerp(0.45, 1.0, rise) * (1 - iso), dust_alpha=lerp(0.75, 0.6, rise) * (1 - iso))
        # amber "habit" rings where HIS feet land (the film's clue device, S05): short gap, long gap
        for (tt, side, foot) in HIS_FALLS:
            k = (t - tt) / 0.75
            if 0 <= k < 1:
                a_ring = (1 - k) ** 1.6 * (1.0 if side == "l" else 0.75) * (1 - iso)
                rx = (26 + 22 * ease("out3", k)) * S_W
                draw.ellipse(f, (foot[0], Y_W + 1), rx, rx * 0.22, 0, 2.4, AMBER, a_ring, glow=0.7 * a_ring)
        # the ring itself, crisp, as everything else goes black (S01 ending device)
        ring = ek("inout", 7.75, 8.15, t)
        if ring > 0:
            w = rig.FIG_LW * hisp.s ** 0.5
            draw.circle(f, J["head"], J["head_r"], w, WHITE, ring)

    # the bulb (S01 prop) - visible in the wide shots
    props.bulb(f, ANCHOR, CORD, swing=swing, on=on * (1 - focus), t=t, glow_r=150)

    # ---------------- the witness's arm (S01 design): her POV, unbroken from the wide through the
    # walk test (the finger trembles after each walker) to the point on "walk"
    w_walk = T.at("walk")
    if T_WIDE + 0.05 < t < T_CUT1:
        targets = Track([(2.36, 2.0), (2.62, 2.0), (2.78, 3.0, "out3"), (2.92, 3.0), (3.08, 0.0, "out3")])
        kf = targets(t)
        i0 = int(math.floor(kf))
        i1 = min(4, i0 + 1)
        h0 = rig.solve(_step_out_pose(t) if i0 == 0 else _line_pose(i0, t))["head"]
        h1 = rig.solve(_step_out_pose(t) if i1 == 0 else _line_pose(i1, t))["head"]
        tgt = cam.to_screen(lerp(h0, h1, kf - i0))
        witness_arm(f, t, tgt, rise=ek("out3", T_WIDE + 0.05, T_WIDE + 0.62, t),
                    hand_base=lerp((500.0, 1455.0), INS_HAND, ek("inout", 2.9, T_CUT1, t)))
    elif T_CUT1 <= t < T_HIS:
        i = 0 if t < T_CUT2 else (1 if t < T_CUT3 else 2)
        Jw = rig.solve(WALKERS[i].pose(t))
        witness_arm(f, t, cam.to_screen((Jw["neck"][0], Jw["neck"][1] + 30)), hand_base=INS_HAND)
    elif t >= T_HIS:
        tgt = cam.to_screen(J["head"])
        hb = lerp(INS_HAND, (700.0, 1585.0), ek("inout", T_RISE0, T_RISE1, t))
        tremble = 1.0 - ek("out", w_walk - 0.04, w_walk + 0.08, t)
        jab = ease("outback", inv_lerp(w_walk, w_walk + 0.22, t)) - ek("inout", 6.9, 7.3, t) * 0.4
        drop = ek("in3", 7.25, 7.85, t)
        witness_arm(f, t, tgt, rise=1.0, drop=drop, tremble=tremble, jab=jab, hand_base=hb)


def cues(T):
    w_walk = T.at("walk")
    c = [Cue(T_HIT, "impact", gain_db=-16, pan=0.1, size=0.05),        # the match: tip, then flat
         Cue(T_SLAP, "impact", gain_db=-19, pan=0.1, size=0.03),
         Cue(T_WHIP0 + 0.02, "whip", gain_db=-11)]
    # the bulb's cord creaks at each end of its swing (stops after "walk")
    for k in range(6):
        tc = SWING_T0 + SWING_PERIOD * (0.25 + 0.5 * k)
        if 0.7 < tc < 6.6:
            c.append(Cue(tc, "bulb_creak", gain_db=-17, pan=0.25 if k % 2 == 0 else -0.25))
    c.append(Cue(7.15, "bulb_creak", gain_db=-15, pan=0.0))
    # number one steps out
    c.append(Cue(3.08, "footstep", gain_db=-10, pan=-0.5, weight=0.5, wet=0))
    # the others: one even metronome across the three inserts
    for i, g in enumerate(WALKERS):
        a, b = INSERTS[i][0], INSERTS[i][1]
        for (tt, side, foot) in g.footfalls(a, b - 0.02):
            c.append(Cue(tt, "footstep", gain_db=-6, pan=0.15 if side == "r" else -0.15, weight=0.6, wet=0))
    # him: short step, long step - light on the bad LEFT foot, heavy on the right
    for (tt, side, foot) in HIS.footfalls(T_HIS - 0.01, T_STOP + 0.01):
        if side == "l":
            c.append(Cue(tt, "footstep", gain_db=-9, pan=0.0, weight=0.3, wet=0))
        else:
            c.append(Cue(tt, "footstep", gain_db=-3, pan=0.0, weight=0.85, wet=0))
    c.append(Cue(T_STOP + 0.28, "footstep", gain_db=-14, pan=0.0, weight=0.2, wet=0))   # closing step
    c.append(Cue(w_walk, "stinger", gain_db=-6))
    return c


def motion_blur(t, T):
    # the whip and the rise are smeared by the continuous streak (see _streak_vec); sub-frames
    # only for the fast part of the final push
    if 7.5 < t < 7.9:
        return 2
    return 1
