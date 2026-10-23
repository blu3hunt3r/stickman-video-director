"""s10 · OPPOSITE (116-136): he breaks into her room and finds it empty. At her open window,
over his shoulder: across the street, in his own lit window, she stands with his telephone
at her ear, looking back at him. Sirens. Window after window lights up and every look in
the city converges on him; the red ring closes round him; the camera pulls back to the
whole block."""
import math
from dataclasses import replace
from functools import lru_cache

from engine import bass, mocap as mc, paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import folk as F
from films.opposite_full import kit as K
from films.opposite_full import rooms as R
from films.opposite_full.scenes import s08_door as S08

k = K.k
HER_B, HIS_B = K.HER_B, K.HIS_B
FILM_T0 = 116.0

# ---------------------------------------------------------------- beats (scene time)
T_KICK = 0.1                      # a first kick: the door jumps on its chain
T_BURST = 0.5                     # the door bursts in, the chain snaps, its links fly
T_ROOM = 2.5                      # the empty room: he steps in ...
T_LOOK = (3.2, 3.9)               # ... stops, looks round ...
T_AT_WIN = 5.3                    # ... and crosses to the open window
T_OTS = 5.5                       # over his shoulder
T_HER_LOOK = 6.0                  # her look flies to him
T_HIS_LOOK = 6.4                  # his to her
T_SIREN = 9.5                     # the low angle up both facades: sirens
T_WAKE = 12.5                     # the section: the neighbours wake
T_LIGHTS = tuple(12.75 + 0.25 * i for i in range(7))
T_CITY = (13.0, 15.0)             # the far city lights up
T_CITY_LOOKS = 14.4
T_POLICE_LOOK = 15.3
T_RING = 16.0                     # the red ring closes round him
T_PULL = (16.5, 19.5)             # the pull back to the whole block
PULL_Z = 0.62

HIS_SPOT = 868.0                  # his pelvis x at her window (stage px), facing +1
WAKE_ORDER = ((HIS_B, 4), (HIS_B, 6), (HER_B, 5), (HIS_B, 3), (HER_B, 3), (HIS_B, 2), (HER_B, 2))
WAKERS = {(HER_B, 2): "bald", (HER_B, 3): "bun", (HER_B, 5): "curls", (HIS_B, 2): "curls", (HIS_B, 3): "bald",
          (HIS_B, 4): "bun", (HIS_B, 6): "cap"}


def her_room(t):
    """Her room tonight: dark, the window up, the curtain blowing in; the door shut on its
    chain until he breaks it, then wide, with the landing light behind him."""
    door = 0.0
    if t >= T_BURST:
        door = 1.0 - 0.1 * math.exp(-6.0 * (t - T_BURST)) * math.cos(14.0 * (t - T_BURST))
        door = min(door, 1.0) if t > T_BURST + 0.12 else lerp(0.0, 1.0, ease("out3", (t - T_BURST) / 0.12))
    elif t >= T_KICK:
        door = 0.07 * math.sin(math.pi * clamp((t - T_KICK) / 0.22))
    return R.Room(lit=False, window=1.0, wind=0.85 + 0.15 * math.sin(2.0 * math.pi * 0.4 * t), door=door,
                  chain="snapped" if t >= T_BURST else "on", hall=1.0, kettle=True, flame=False, mug=False,
                  film_t=FILM_T0 + t)


# ---------------------------------------------------------------- him
@lru_cache(maxsize=1)
def his_walk():
    C = mc.Clip.load
    man = B.figs()[1]
    return mc.Performance(man, [
        mc.Seg(C("104_02"), 0.3, 1.6, at=T_ROOM - 0.1, speed=1.15),                 # steps in
        mc.Seg(C("104_02"), 6.0, 6.3, at=T_LOOK[0], speed=0.4, travel=0.0, blend=0.3),   # stops, looks round
        mc.Seg(C("104_02"), 1.6, 3.65, at=T_LOOK[1], speed=1.35, blend=0.3),           # to the window
        mc.Seg(C("104_02"), 6.0, 6.3, at=T_AT_WIN - 0.15, speed=0.2, travel=0.0, blend=0.3),
    ], facing=1, x=0.0, near="Left")


def his_pose(t):
    """(state, pose, facing) of him in her room, stage units from his start in the doorway."""
    st, p = his_walk()(K.twos(t))
    facing = 1
    if T_LOOK[0] + 0.15 <= t < T_LOOK[1] - 0.1:          # he looks back at the door, then on
        u = (t - T_LOOK[0] - 0.15) / (T_LOOK[1] - T_LOOK[0] - 0.25)
        p.head = 10.0 * math.sin(math.pi * u)
        if 0.3 <= u < 0.7:
            facing = -1
    if t >= T_AT_WIN:                                    # at the glass: looking across and up
        p.head = lerp(p.head, 8.0, k(t, T_AT_WIN, 0.3))
    return st, p, facing


def draw_him_in_room(c, t, rim=K.STEEL):
    """Him in her room (stage px), in the dark: an ink cut-out with a cold edge."""
    st, p, facing = his_pose(t)
    x0 = R.X_DOOR - 40.0
    c.save()
    B.place(c, x0, R.FLOOR, R.FIG_S)
    if facing < 0:
        c.translate(2.0 * st["pelvis"][0], 0.0)
        c.scale(-1.0, 1.0)
    o = R.rim_cutout(c, B.figs()[1], st, p, facing=1, rim=rim, edge=K.DEEP)
    head = c.user_to_device(*o["head"])
    c.restore()
    return c.device_to_user(*head)


def him_at_window(c, rim):
    """Him standing at her window, looking out (stage px): his final place."""
    man = B.figs()[1]
    st = pd.standing(man, 0.0)
    p = pd.Pose(head=8.0, lean=2.0, arms={"near": ("ang", 6.0, 12.0), "far": ("ang", 4.0, 10.0)})
    c.save()
    B.place(c, HIS_SPOT, R.FLOOR, R.FIG_S)
    o = R.rim_cutout(c, man, st, p, facing=1, rim=rim, edge=K.DEEP)
    head = c.user_to_device(*o["head"])
    c.restore()
    return c.device_to_user(*head)


# ---------------------------------------------------------------- 0-2.5: the burst, from the floor
DOORWAY = S08.DOOR                            # her door, as s08 shows it from inside her room
THRESH = S08.BAR_Y
S08_T = 3.4                                   # s08's clock at our 0: his feet at the door, the handle still


def shake(t):
    """The frame jolts on the two blows, and settles."""
    dx = dy = 0.0
    for t0, amp in ((T_KICK, 9.0), (T_BURST, 22.0)):
        if t >= t0:
            e = amp * math.exp(-9.0 * (t - t0))
            dx += e * math.sin(53.0 * (t - t0))
            dy += 0.7 * e * math.cos(61.0 * (t - t0))
    return dx, dy


def leaf_quad(swing):
    """The door leaf, hinged on the doorway's left jamb, swung `swing` (0 shut .. 1 flung
    open toward us, against the wall off the left of the frame): (hinge top, free top, free
    bottom, hinge bottom)."""
    x0, y0, x1, y1 = DOORWAY
    th = math.radians(100.0 * swing)
    fx = x0 + (x1 - x0) * math.cos(th) - 760.0 * math.sin(th)
    fy0 = lerp(y0, y0 - 360.0, math.sin(th) ** 1.2)
    fy1 = lerp(y1, y1 + 560.0, math.sin(th) ** 1.2)
    return [(x0, y0), (fx, fy0), (fx, fy1), (x0, y1)]


MAN_H = 786.0                                  # his height in man_front's units, hat crown to heel
MAN_PARTS = (
    [(-36, 0), (-44, -8), (-58, -170), (-128, -176), (-150, -360), (-140, -560), (-118, -592), (-60, -612),
     (-30, -628), (30, -628), (60, -612), (118, -592), (140, -560), (150, -360), (128, -176), (58, -170),
     (44, -8), (36, 0), (14, 0), (6, -150), (-6, -150), (-14, 0)],                       # coat, collar, legs
    [(-34, -626), (-40, -680), (-28, -716), (0, -726), (28, -716), (40, -680), (34, -626)],    # head
    [(-122, -700), (-60, -716), (60, -716), (122, -700), (112, -688), (-112, -688)],           # brim
    [(-58, -712), (-52, -770), (-24, -786), (0, -776), (24, -786), (52, -770), (58, -712)],    # crown
)


def man_front(c, x, base, s, color):
    """Him, face on, in the doorway: hat, the turned-up collar, the long coat, legs apart."""
    bass.fill_polys(c, [bass.orient(bass.cut([(x + px * s, base + py * s) for px, py in part], seed=520 + i, amp=0.5), True)
                        for i, part in enumerate(MAN_PARTS)], color)


def man_shadow(c, x, base, reach, sway, color):
    """His shadow, thrown by the landing's light across the floor at us: the same cut-out laid
    flat and stretched, the feet at his feet, the hat at our end, growing as it comes nearer."""
    near = 1900.0
    def M(px, py):
        u = clamp(-py / MAN_H)
        return (x + px * (0.66 + 0.8 * u) + sway * u, base + (near - base) * reach * u ** 0.75)
    bass.fill_polys(c, [bass.orient(bass.cut([M(px, py) for px, py in part], seed=530 + i, amp=0.6), True)
                        for i, part in enumerate(MAN_PARTS)], color)


def bulb_swing(t):
    """The landing's bare bulb, set swinging by the crash: its angle (radians)."""
    if t < T_BURST:
        return 0.0
    d = t - T_BURST
    return 0.22 * math.exp(-0.7 * d) * math.sin(4.6 * d)


LINK_G = 3600.0                                # px/s^2


def _link(i):
    x0, y0 = DOORWAY[2] - 12.0, S08.CHAIN_Y
    vy = -300.0 - 500.0 * hash01(i, 402)
    floor_y = lerp(THRESH + 50.0, 1850.0, hash01(i, 403))
    t_land = (-vy + math.sqrt(vy * vy + 2.0 * LINK_G * (floor_y - y0))) / LINK_G
    vx = (lerp(170.0, 960.0, hash01(i, 401)) - x0) / t_land
    return x0, y0, vx, vy, floor_y, t_land


def chain_link(i, dt):
    """Where link i of the snapped chain is, dt after the burst."""
    x0, y0, vx, vy, floor_y, t_land = _link(i)
    if dt < t_land:
        return x0 + vx * dt, y0 + vy * dt + 0.5 * LINK_G * dt * dt
    d = dt - t_land
    v_land = vy + LINK_G * t_land
    hop = 0.18 * v_land * v_land / (2.0 * LINK_G) * abs(math.sin(math.pi * d / 0.16)) * math.exp(-6.0 * d)
    return x0 + vx * t_land + 0.25 * vx * (1.0 - math.exp(-4.0 * d)) / 4.0, floor_y - hop


def link_r(i, dt):
    """Its size: bigger as it comes nearer the lens."""
    _, _, _, _, floor_y, t_land = _link(i)
    end = lerp(8.0, 20.0, clamp((floor_y - THRESH) / (1850.0 - THRESH)))
    return lerp(6.0, end, clamp(dt / t_land))


def _quad_pt(q, u, v):
    """Bilinear point in the leaf quad q = (hinge top, free top, free bottom, hinge bottom)."""
    top = (lerp(q[0][0], q[1][0], u), lerp(q[0][1], q[1][1], u))
    bot = (lerp(q[3][0], q[2][0], u), lerp(q[3][1], q[2][1], u))
    return (lerp(top[0], bot[0], v), lerp(top[1], bot[1], v))


def draw_leaf(c, swing):
    """s08's leaf (teal-grey, two panels, the lever) swung open toward us on its hinge."""
    q = leaf_quad(swing)
    bass.fill_polys(c, [bass.orient(q, True)], S08.LEAF_C)
    x0, y0, x1, y1 = DOORWAY
    for y_a, y_b in ((320.0, 760.0), (880.0, 1240.0)):
        va, vb = (y_a - y0) / (y1 - y0), (y_b - y0) / (y1 - y0)
        ua, ub = 56.0 / (x1 - x0), 1.0 - 56.0 / (x1 - x0)
        panel = [_quad_pt(q, ua, va), _quad_pt(q, ub, va), _quad_pt(q, ub, vb), _quad_pt(q, ua, vb)]
        bass.fill_polys(c, [bass.orient(panel, True)], S08.PANEL_C)
    ku, kv = (B.KNOB[0] - x0) / (x1 - x0), (B.KNOB[1] - y0) / (y1 - y0)
    knob = _quad_pt(q, ku, kv)
    sx = math.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]) / (x1 - x0)
    K.dot(c, knob, 44.0 * max(sx, 0.3), S08.METAL, seed=104)


def draw_burst(c, t):
    dx, dy = shake(t)
    c.save()
    c.translate(dx, dy)
    x0, y0, x1, y1 = DOORWAY
    if t < T_BURST:
        # s08's door, shut on its chain, his feet in the light under it; the kick jolts it to the chain
        g = S08.G_MAX * (k(t, T_KICK, 0.05, "out3") - k(t, T_KICK + 0.16, 0.14, "in3"))
        S08.draw_door(c, S08_T + t, gap=g)
        if t >= T_KICK:
            links = S08.chain_links(g, S08_T + t)
            K.ripple(c, links[len(links) // 2][0], t, T_KICK + 0.04, K.PAPER, n=2, every=0.08, life=0.4, r0=18.0,
                     r1=104.0, width=3.2, seed=150, alpha=0.7)
        c.restore()
        return
    u = (t - T_BURST) / 0.13
    swing = ease("out3", clamp(u)) if u < 1.0 else 1.0 - 0.06 * math.exp(-7.0 * (t - T_BURST - 0.13)) * \
        abs(math.sin(16.0 * (t - T_BURST - 0.13)))
    step = k(t, 1.55, 0.6, "inout")                   # he takes a step in
    # her room, as s08 has it: the wall, the floor, the moonlight from the window behind us
    K.fill(c, S08.WALL_C)
    bass.fill_polys(c, [bass.cut_rect(-40.0, THRESH + 26.0, 1120.0, 1960.0, seed=99, amp=1.0)], S08.FLOOR_C)
    S08.moon_floor(c, S08_T + t)
    bass.fill_polys(c, [bass.cut_rect(x0 - 26.0, y0 - 26.0, x1 + 26.0, THRESH, seed=100, amp=1.2)], S08.FRAME_C)
    # the doorway open on the landing's light; the light thrown across her floor at us
    bass.fill_polys(c, [bass.cut_rect(x0, y0, x1, THRESH, seed=505, amp=0.3)], K.AMBER)
    bass.fill_polys(c, [bass.cut_rect(x0, THRESH - 190.0, x1, THRESH - 182.0, seed=506, amp=0.3)],
                    lerp(K.AMBER, K.INK, 0.25))
    wedge = [(x0, THRESH), (x1, THRESH), (x1 + 760.0, 2100.0), (x0 - 700.0, 2100.0)]
    bass.fill_polys(c, [bass.orient(wedge, True)], K.AMBER, 0.55 * clamp(swing * 1.4))
    # his long shadow, on the floor toward us, swaying with the bulb behind him
    foot_y = lerp(THRESH - 18.0, THRESH + 60.0, step)
    man_shadow(c, 540.0, foot_y, clamp(swing * 1.3), -520.0 * math.sin(bulb_swing(t)), K.INK)
    # him: a step behind the threshold he fits under the lintel; stepping over it he comes past the frame
    s_man = lerp(1.2, 1.46, step)
    if step < 0.35:
        c.save()
        K.clip_rect(c, (x0, y0, x1, THRESH + 200.0))
        man_front(c, 540.0, foot_y, s_man, K.INK)
        c.restore()
    else:
        man_front(c, 540.0, foot_y, s_man, K.INK)
    # the leaf, flung open toward us
    if swing < 0.999:
        draw_leaf(c, swing)
    # the chain's links, flying at us: they land across the floor, bounce, skid and lie there
    for i in range(9):
        K.dot(c, chain_link(i, t - T_BURST), link_r(i, t - T_BURST), lerp(K.STEEL, K.PAPER, 0.75), seed=410 + i)
    c.restore()


# ---------------------------------------------------------------- 2.5-5.5: the empty room
def room_cam(t):
    a = R.Cam(470.0, 1110.0, 1.0)
    b = R.Cam(620.0, 1130.0, 1.08)
    return R.cam_lerp(a, b, k(t, T_ROOM, T_OTS - T_ROOM, "inout"))


def draw_room(c, t):
    room = her_room(t)
    R.draw_stage(c, t, room, cam=room_cam(t), figures=lambda c2: draw_him_in_room(c2, t),
                 others=lambda c2, b, n, rect: F.asleep(c2, b, n, rect, t))


# ---------------------------------------------------------------- 5.5-9.5: over his shoulder
FACADE = lerp(K.INK, K.DEEP, 0.55)            # his building across the street, by night
OTS_EDGE = 700.0                              # its right-hand corner; beyond it, the sky and the far city
OTS_WIN = (268.0, 520.0, 568.0, 830.0)        # his window, lit, with her in it
OTS_FLOOR_H = 430.0                           # a storey of his building, in this view
HER_EYE_V = (424.0, 612.0)                    # her eye (the dolly zoom's centre: she holds still as the world swells)
HIS_HEAD_V = (842.0, 1408.0)                  # where his look leaves from, at the front of his hat
OTS_SWELL = (6.4, 1.9)                        # the dolly zoom: the far side swells as their eyes lock
T_MEET = 6.82                                 # the two looks meet, tip to tip
T_LOWER = 8.15                                # she lowers his receiver
T_SWEEP = 8.85                                # the first red light sweeps the facade from the street


def ots_zoom(t):
    return lerp(1.0, 1.3, k(t, OTS_SWELL[0], OTS_SWELL[1], "inout"))


def facade_windows():
    """His building's windows in this view: (rect, lit)."""
    out = []
    for row in range(-1, 4):
        y0 = OTS_WIN[1] + row * OTS_FLOOR_H
        for x0 in (OTS_WIN[0] - 440.0, OTS_WIN[0]):
            out.append(((x0, y0, x0 + 300.0, y0 + 310.0), row == 0 and x0 == OTS_WIN[0]))
    return out


def her_in_window(c, t, store):
    """Her, in his window, from the waist up: his receiver at her ear, its cord hanging; she
    lowers it when the call is made."""
    her = B.figs()[0]
    st = pd.standing(her, 0.0)
    d = k(t, T_LOWER, 0.55, "inout")
    near = ("ang", lerp(85.0, 18.0, d), lerp(155.0, 26.0, d))
    p = pd.Pose(head=lerp(-6.0, -2.0, d), lean=lerp(0.0, -3.0, d), arms={"near": near, "far": ("ang", 10.0, 24.0)},
                eye=1.0)
    p.hold["near"] = lambda c2, H: receiver_hold(c2, H, store)
    c.save()
    K.clip_rect(c, OTS_WIN)
    B.place(c, 400.0, 1025.0, 0.66)                  # the sill at her waist
    o = B.draw_cutout(c, her, st, p, K.INK, facing=1, edge=K.AMBER, outline=K.AMBER, ow=8.0)
    store["head"] = c.user_to_device(*o["head"])
    c.restore()


def cord(c, a, b, t, seed=0):
    """The receiver's coiled cord, from a down to the telephone below the sill at b."""
    pts = []
    n = 46
    for i in range(n + 1):
        u = i / n
        x = lerp(a[0], b[0], u)
        y = lerp(a[1], b[1], u) + 70.0 * math.sin(math.pi * u)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        w = 7.0 * math.sin(u * 2.0 * math.pi * 13.0 + 1.3 * t)
        pts.append((x - dy / L * w, y + dx / L * w))
    bass.line_band(c, pts, K.INK, width=4.0, seed=660 + seed)


def draw_far_side(c, t, store):
    """Everything across the street, zoomed about her eye."""
    K.fill(c, K.NIGHT)
    # the gap beyond his building: the moon, the far city low under it
    K.moon(c, (905.0, 470.0), r=60.0)
    c.save()
    K.clip_rect(c, (OTS_EDGE, -400.0, 1600.0, 2400.0))
    c.translate(0.0, 520.0)
    K.skyline(c, color=lerp(K.NIGHT, K.INK, 0.45))
    c.restore()
    # his building: the facade, its cornice line, the sills catching the moon
    bass.fill_polys(c, [bass.cut_rect(-400.0, -400.0, OTS_EDGE, 2400.0, seed=601)], FACADE)
    bass.line_band(c, [(OTS_EDGE - 2.0, -400.0), (OTS_EDGE - 2.0, 2400.0)], K.STEEL, width=5.0, seed=602)
    for (x0, y0, x1, y1), lit in facade_windows():
        bass.fill_polys(c, [bass.cut_rect(x0 - 16.0, y0 - 16.0, x1 + 16.0, y1 + 10.0, seed=int(x0 + y0) % 997)], K.INK)
        bass.fill_polys(c, [bass.cut_rect(x0, y0, x1, y1, seed=int(x0 * 3 + y0) % 991, amp=0.4)],
                        K.AMBER if lit else K.SHUT)
        bass.fill_polys(c, [bass.cut_rect(x0 - 30.0, y1 + 10.0, x1 + 30.0, y1 + 30.0, seed=int(x0 + 5 * y0) % 983,
                                          amp=0.4)], K.INK)
        bass.line_band(c, [(x0 - 30.0, y1 + 10.0), (x1 + 30.0, y1 + 10.0)], K.STEEL, width=3.0,
                       seed=int(x0 + 7 * y0) % 977)
        if not lit:
            # the sash's cross bars, dark on dark
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            bass.fill_polys(c, [bass.cut_rect(mx - 5.0, y0, mx + 5.0, y1, seed=611), bass.cut_rect(x0, my - 6.0, x1, my + 6.0,
                                                                                                    seed=612)],
                            lerp(K.SHUT, K.INK, 0.6))
    # inside his window: the lamp's warm ceiling, her, the receiver's cord going down to the phone
    x0, y0, x1, y1 = OTS_WIN
    bass.fill_polys(c, [bass.cut_rect(x0, y0, x1, y0 + 40.0, seed=621, amp=0.3)], lerp(K.AMBER, K.PAPER, 0.25))
    her_in_window(c, t, store)
    if "cord" in store:
        a = c.device_to_user(*store["cord"])
        c.save()
        K.clip_rect(c, OTS_WIN)
        cord(c, a, (x0 + 30.0, y1 + 40.0), t)
        c.restore()
    # the first of the police light, sweeping up the facade from the street
    if t >= T_SWEEP:
        u = (t - T_SWEEP) / (T_SIREN - T_SWEEP)
        for i, col in enumerate((RED, K.POLICE)):
            cx = lerp(-300.0, 1300.0, (u * 1.7 + 0.55 * i) % 1.0)
            w = [(cx - 160.0, 2400.0), (cx + 160.0, 2400.0), (cx + 520.0, -400.0), (cx - 40.0, -400.0)]
            bass.fill_polys(c, [bass.orient(w, True)], col, 0.16 * clamp(u * 3.0))


def draw_her_window_frame(c, t):
    """Her own window round the view (we stand in her dark room): the jambs, the raised sash's
    rail, the sill, and her curtain blowing in at the left."""
    rail = [bass.cut_rect(-40.0, 250.0, 1120.0, 318.0, seed=631)]
    bass.fill_polys(c, [bass.cut_rect(-40.0, -40.0, 1120.0, 250.0, seed=634)], K.INK, 0.35)          # the upper glass
    bass.fill_polys(c, rail, K.DEEP)
    bass.line_band(c, [(-40.0, 252.0), (1120.0, 252.0)], R.GLASS, width=3.0, seed=635)
    frame = [bass.cut_rect(-40.0, -40.0, 1120.0, 64.0, seed=630), bass.cut_rect(-40.0, 1736.0, 1120.0, 1960.0, seed=636),
             bass.cut_rect(-40.0, -40.0, 58.0, 1960.0, seed=632), bass.cut_rect(1026.0, -40.0, 1120.0, 1960.0, seed=633)]
    bass.fill_polys(c, frame, K.DEEP)
    bass.line_band(c, [(58.0, 1736.0), (1026.0, 1736.0)], R.GLASS, width=4.0, seed=637)
    # the curtain, billowing into the room
    pts = [(-40.0, 40.0), (70.0, 40.0)]
    for i in range(1, 25):
        y = 40.0 + i * (1740.0 - 40.0) / 24.0
        b = 70.0 + 60.0 * math.sin(y / 230.0 + 2.6 * t) + 40.0 * math.sin(y / 97.0 - 3.7 * t) + 90.0 * (y / 1740.0)
        pts.append((b, y))
    pts.append((-40.0, 1740.0))
    pts = [(1080.0 - x, y) for x, y in pts]          # it hangs at the right, as in her window's view
    bass.fill_polys(c, [bass.orient(bass.cut(pts, seed=638, amp=0.6), True)], lerp(K.NIGHT, K.PAPER, 0.25), 0.3)
    bass.line_band(c, pts[2:-1], R.GLASS, width=3.0, seed=639, alpha=0.8)


def draw_over_shoulder(c, t):
    """Through her window: his building across the street, his window lit, and her in it with
    his receiver at her ear, looking back at him; his hat and shoulders from behind, black
    against the sky. Her look flies to him; his, red, to her; they meet tip to tip, and the far
    side swells round her."""
    store = {}
    z = ots_zoom(t)
    c.save()
    c.translate(*HER_EYE_V)
    c.scale(z, z)
    c.translate(-HER_EYE_V[0], -HER_EYE_V[1])
    draw_far_side(c, t, store)
    c.restore()
    draw_her_window_frame(c, t)
    # the looks: from her eye and from him, to the point between them
    her_eye = c.device_to_user(*store["head"]) if "head" in store else HER_EYE_V
    her_eye = (her_eye[0] + 22.0, her_eye[1] + 4.0)
    m = (lerp(her_eye[0], HIS_HEAD_V[0], 0.5), lerp(her_eye[1], HIS_HEAD_V[1], 0.5))
    if t >= T_HER_LOOK:
        K.dotted(c, her_eye, m, K.PAPER, lead=k(t, T_HER_LOOK, 0.5, "out3"), r=7.5, gap=26.0, head=30.0,
                 phase=24.0 * (t - T_HER_LOOK), seed=71)
    draw_his_back(c, t)
    if t >= T_HIS_LOOK:
        K.dotted(c, HIS_HEAD_V, m, RED, lead=k(t, T_HIS_LOOK, T_MEET - T_HIS_LOOK, "out3"), r=8.5, gap=26.0,
                 head=32.0, phase=30.0 * (t - T_HIS_LOOK), seed=72)
    if t >= T_MEET:
        K.ripple(c, m, t, T_MEET, K.PAPER, n=2, every=0.2, life=0.8, r0=12.0, r1=120.0, width=6.0, seed=73)
        K.ripple(c, m, t, T_MEET + 0.1, RED, n=2, every=0.2, life=0.8, r0=12.0, r1=150.0, width=6.0, seed=74)


HANDSET = [(-15.0, -50.0), (8.0, -54.0), (15.0, -43.0), (9.0, -29.0), (5.0, 29.0), (15.0, 41.0), (10.0, 54.0),
           (-15.0, 51.0), (-21.0, 39.0), (-7.0, 29.0), (-6.0, -29.0), (-21.0, -40.0)]     # cups to the face side (-x)


def receiver_hold(c, H, store=None):
    """His telephone's receiver in her hand: the earpiece on her ear, the mouthpiece out past
    her chin (in profile, the part that shows). Drawn from the ear, along the jaw, whatever the
    hand is doing; while she lowers it, it follows the hand. store: gets the cord's end
    (device px)."""
    f = H["facing"]
    mx, my = H["mouth"]
    ear = (mx - 30.0 * f, my - 20.0)
    at_ear = (ear[0] + 46.0 * 0.62 * f, ear[1] + 46.0 * 0.78)
    hc = H["hc"]
    w = clamp((math.hypot(hc[0] - at_ear[0], hc[1] - at_ear[1]) - 30.0) / 60.0)     # 0 at her ear .. 1 in her hand
    a_ear = math.atan2(0.78, 0.62 * f) - math.pi / 2.0
    c.save()
    c.translate(lerp(at_ear[0], hc[0], w), lerp(at_ear[1], hc[1], w))
    c.rotate(lerp(a_ear, math.radians(-10.0 * f), w))
    c.scale(f, 1.0)
    edge = H.get("edge")
    if edge is not None:
        B.edged(c, [bass.orient(bass.cut(HANDSET, seed=640, amp=0.3), True)], K.INK, edge, 6.0)
    else:
        bass.fill_polys(c, [bass.orient(bass.cut(HANDSET, seed=640, amp=0.3), True)], K.INK)
    if store is not None:
        store["cord"] = c.user_to_device(-4.0, 52.0)
    c.restore()


def draw_his_back(c, t):
    """His hat and shoulders from behind, big, at the right of the frame: black against the
    night, the moon on his edges; they rise a little when he sees her; the police light
    catches them at the end."""
    j = 3.0 * math.sin(2.0 * math.pi * 0.25 * t) - 14.0 * k(t, T_HIS_LOOK, 0.3, "out")
    bx, by = 860.0, 1500.0 + j
    rim = K.STEEL
    if t >= T_SWEEP:
        rim = RED if strobe(t) else K.POLICE
    sh = [(bx - 380.0, 1980.0), (bx - 330.0, by + 150.0), (bx - 210.0, by + 60.0), (bx - 80.0, by + 30.0),
          (bx + 120.0, by + 30.0), (bx + 260.0, by + 70.0), (bx + 400.0, by + 160.0), (bx + 460.0, 1980.0)]
    B.edged(c, [bass.orient(bass.cut(sh, seed=650, amp=0.8), True)], K.INK, rim, 5.0)
    collar = [(bx - 130.0, by + 70.0), (bx - 100.0, by - 30.0), (bx + 140.0, by - 30.0), (bx + 170.0, by + 70.0)]
    B.edged(c, [bass.orient(bass.cut(collar, seed=652, amp=0.6), True)], K.INK, rim, 4.0)
    head = bass.draw.ellipse_pts((bx + 20.0, by - 60.0), 110.0, 130.0, n=64)
    bass.fill_polys(c, [bass.orient(head, True)], K.INK)
    brim = bass.draw.ellipse_pts((bx + 20.0, by - 150.0), 230.0, 46.0, n=64)
    B.edged(c, [bass.orient(brim, True)], K.INK, rim, 4.0)
    crown = [(bx - 110.0, by - 160.0), (bx - 96.0, by - 270.0), (bx - 30.0, by - 300.0), (bx + 20.0, by - 286.0),
             (bx + 70.0, by - 300.0), (bx + 136.0, by - 270.0), (bx + 150.0, by - 160.0)]
    B.edged(c, [bass.orient(bass.cut(crown, seed=651, amp=0.6), True)], K.INK, rim, 4.0)
    band = [(bx - 106.0, by - 196.0), (bx + 146.0, by - 196.0), (bx + 148.0, by - 166.0), (bx - 108.0, by - 166.0)]
    bass.fill_polys(c, [bass.orient(bass.cut(band, seed=653, amp=0.4), True)], lerp(K.INK, K.DEEP, 0.7))


# ---------------------------------------------------------------- 9.5-12.5: sirens, the low angle
def _f(v, a=1.7):
    return v * (1.0 + a) / (1.0 + a * v)


def facade(bl, br, tl, tr):
    def P(u, v):
        f = _f(v)
        x0, y0 = lerp(bl[0], br[0], u), lerp(bl[1], br[1], u)
        x1, y1 = lerp(tl[0], tr[0], u), lerp(tl[1], tr[1], u)
        return (lerp(x0, x1, f), lerp(y0, y1, f))
    return P


HER_F = facade((-160.0, 2000.0), (395.0, 2000.0), (335.0, 230.0), (462.0, 250.0))
HIS_F = facade((685.0, 2000.0), (1240.0, 2000.0), (622.0, 150.0), (760.0, 120.0))


def quad(P, u0, v0, u1, v1):
    return [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]


def strobe(t):
    """0 or 1: which half of the light bars is lit (they alternate, 4 times a second)."""
    return int(t * 8.0) % 2


def draw_sirens(c, t):
    lift = 70.0 * k(t, T_SIREN, 3.0, "inout")
    c.save()
    c.translate(0.0, lift)
    K.fill(c, K.NIGHT)
    K.moon(c, (545.0, 300.0), r=58.0)
    for P, floors, mine, seed in ((HER_F, 5, (K.HER_FLOOR, 1), 700), (HIS_F, 6, (K.HIS_FLOOR, 0), 720)):
        bass.fill_polys(c, [bass.orient(quad(P, 0.0, 0.0, 1.0, 1.0), True)], K.INK)
        for n in range(1, floors + 1):
            for col, (u0, u1) in enumerate(((0.16, 0.42), (0.58, 0.84))):
                v0, v1 = (n - 1) / floors + 0.05, n / floors - 0.07
                q = quad(P, u0, v0, u1, v1)
                lit = (n, col) == mine and P is HIS_F
                bass.fill_polys(c, [bass.orient(q, True)], K.AMBER if lit else K.SHUT)
                if (n, col) == mine:
                    who_in_window(c, q, t, her=P is HIS_F)
    # the light bars' beams sweep the facades
    for i, (lb, ph) in enumerate((((300.0, 1790.0), 0.0), ((800.0, 1800.0), 1.7))):
        a = math.radians(70.0 * math.sin(2.0 * math.pi * 0.55 * t + ph))
        col = RED if (i + strobe(t)) % 2 == 0 else K.POLICE
        for spread, al in ((math.radians(9.0), 0.22),):
            d0 = (math.sin(a - spread), -math.cos(a - spread))
            d1 = (math.sin(a + spread), -math.cos(a + spread))
            w = [lb, (lb[0] + d0[0] * 2600.0, lb[1] + d0[1] * 2600.0), (lb[0] + d1[0] * 2600.0, lb[1] + d1[1] * 2600.0)]
            bass.fill_polys(c, [bass.orient(w, True)], col, al)
    c.restore()
    # the cars, close, at the bottom of the frame
    for i, (x, w) in enumerate(((300.0, 470.0), (800.0, 480.0))):
        car(c, (x, 1920.0), w, t, i)


def who_in_window(c, q, t, her):
    """A bust in a window seen from below: her with the receiver (in his), him with his hat
    (in hers, dark: the sweeps catch him)."""
    xs = [p[0] for p in q]
    ys = [p[1] for p in q]
    cx, cy = sum(xs) / 4.0, sum(ys) / 4.0
    hgt = max(ys) - min(ys)
    s = hgt / 300.0
    c.save()
    c.new_path()
    bass.draw.poly(c, q)
    c.clip()
    c.translate(cx, cy + 0.5 * hgt)
    c.scale(s, s)
    body = [(-120.0, 0.0), (-110.0, -120.0), (-60.0, -170.0), (60.0, -170.0), (110.0, -120.0), (120.0, 0.0)]
    bass.fill_polys(c, [bass.orient(body, True)], K.INK)
    bass.fill_polys(c, [bass.orient(bass.draw.ellipse_pts((0.0, -225.0), 52.0, 62.0, n=40), True)], K.INK)
    if her:
        bob = [(-62.0, -230.0), (-50.0, -282.0), (0.0, -298.0), (50.0, -282.0), (62.0, -230.0), (54.0, -196.0),
               (-54.0, -196.0)]
        bass.fill_polys(c, [bass.orient(bob, True)], K.INK)
        bass.line_band(c, [(60.0, -150.0), (92.0, -200.0), (70.0, -246.0)], K.INK, width=26.0, seed=3)
    else:
        bass.fill_polys(c, [bass.orient([(-110.0, -262.0), (110.0, -262.0), (104.0, -248.0), (-104.0, -248.0)], True),
                            bass.orient([(-56.0, -262.0), (-48.0, -318.0), (48.0, -318.0), (56.0, -262.0)], True)],
                        K.INK)
    c.restore()


def car(c, base, w, t, i):
    """A police car end-on, close: body, cabin, the light bar flashing red and blue."""
    x, y = base
    h = w * 0.36
    body = [(x - w / 2, y + 10.0), (x - w / 2, y - h * 0.55), (x - w * 0.44, y - h * 0.68), (x + w * 0.44, y - h * 0.68),
            (x + w / 2, y - h * 0.55), (x + w / 2, y + 10.0)]
    cab = [(x - w * 0.36, y - h * 0.66), (x - w * 0.3, y - h * 1.08), (x + w * 0.3, y - h * 1.08), (x + w * 0.36, y - h * 0.66)]
    bass.fill_polys(c, [bass.orient(bass.cut(body, seed=760 + i, amp=0.6), True),
                        bass.orient(bass.cut(cab, seed=762 + i, amp=0.6), True)], K.INK)
    bar_y = y - h * 1.08 - 12.0
    on = strobe(t)
    for j, col in enumerate((RED, K.POLICE)):
        bx0 = x - w * 0.22 + j * w * 0.22
        lit = (j + on + i) % 2 == 0
        bass.fill_polys(c, [bass.cut_rect(bx0, bar_y - 14.0, bx0 + w * 0.22, bar_y + 4.0, seed=770 + j + 2 * i, amp=0.4)],
                        col if lit else lerp(col, K.INK, 0.7))
        if lit:
            K.dot(c, (bx0 + w * 0.11, bar_y - 5.0), w * 0.2, col, seed=780 + j, alpha=0.25)


# ---------------------------------------------------------------- 12.5-20: the neighbours, the ring, the pull back
def lit_at(t):
    lit = {(HIS_B, K.HIS_FLOOR): K.AMBER}
    for room, t0 in zip(WAKE_ORDER, T_LIGHTS):
        if t >= t0:
            lit[room] = K.AMBER
    return lit


def watcher_pose(b, n):
    """A neighbour at their window, looking toward his window (her room, storey 4)."""
    up = (K.HER_FLOOR - n) * (16.0 if b is HIS_B else 34.0)
    p = pd.Pose(lean=8.0 if b is HIS_B else 22.0, head=clamp(up, -40.0, 40.0),
                arms={"near": ("ang", 14.0, 40.0), "far": ("ang", 8.0, 30.0)})
    return p


def section_scene(t, heads):
    """people callback for the section: the watchers at their windows, her in his window,
    the woman on his floor, and the sleepers who have not woken yet. Collects heads."""
    lit = lit_at(t)

    def others(c, b, n, rect):
        fy = rect[3]
        if b is HIS_B and n == K.HIS_FLOOR:
            victim(c, fy)
            her = B.win_fig(0)
            p = pd.Pose(head=-8.0, arms={"near": ("ang", 85.0, 155.0), "far": ("ang", 12.0, 30.0)})
            p.hold["near"] = receiver_hold
            o = F.draw(c, her, pd.standing(her, 0.0), p, rect[0] + 30.0, fy, -1, K.AMBER)
            heads["her"] = o["head_at"]
            return
        if (b, n) in lit:
            t0 = dict(zip(WAKE_ORDER, T_LIGHTS))[(b, n)]
            fig = F.small(WAKERS[(b, n)])
            x = rect[2] - 30.0 if b is HER_B else rect[0] + 30.0
            pop = ease("outback", clamp((t - t0) / 0.2))
            p = watcher_pose(b, n)
            o = F.draw(c, fig, pd.standing(fig, 0.0), p, x, fy + 30.0 * (1.0 - pop), b.side, K.AMBER)
            heads[(b, n)] = o["head_at"]
        else:
            F.asleep(c, b, n, rect, t)
    return others


def victim(c, fy):
    """The woman on his floor, alive: lying where she fell, her head lifted a little."""
    fig = B.win_fig(2)
    p = pd.Pose(head=14.0, arms={"near": ("ang", 30.0, 40.0), "far": ("ang", -8.0, 6.0)})
    c.save()
    c.translate(782.0, fy - 7.0)
    c.rotate(math.radians(90.0))
    c.scale(F.SEC_FS, F.SEC_FS)
    B.draw_cutout(c, fig, pd.standing(fig, 0.0), p, K.INK, facing=-1, edge=K.AMBER, outline=K.AMBER, ow=10.0)
    c.restore()


@lru_cache(maxsize=1)
def city_eyes():
    """Lit windows of the far city that look at him: points in the street gap and over the roofs."""
    return ((470.0, 420.0), (560.0, 610.0), (640.0, 360.0), (520.0, 980.0), (610.0, 1210.0), (470.0, 1380.0),
            (900.0, 300.0), (160.0, 470.0))


def flank(c, t):
    """The block beyond the frame, for the pull back: two more houses, every window lit, some
    with a watcher in it. Returns the watchers' heads (section px)."""
    eyes = []
    for x0, x1, top, seed in ((-470.0, -60.0, 560.0, 900), (1120.0, 1560.0, 470.0, 920)):
        bass.fill_polys(c, [bass.cut_rect(x0, top, x1, K.GROUND + 4.0, seed=seed)], K.INK)
        y = top + 50.0
        row = 0
        while y + 120.0 < K.GROUND - 40.0:
            for col in range(3):
                wx = x0 + 40.0 + col * (x1 - x0 - 80.0) / 3.0
                bass.fill_polys(c, [bass.cut_rect(wx, y, wx + 70.0, y + 110.0, seed=seed + row * 3 + col, amp=0.6)],
                                K.AMBER)
                if hash01(seed + row * 3 + col, 5) < 0.42:
                    # a watcher: head and shoulders at the sill, against the light
                    cx, by = wx + 35.0 + (hash01(seed + row * 3 + col, 6) - 0.5) * 16.0, y + 110.0
                    sh = [(cx - 24.0, by), (cx - 21.0, by - 20.0), (cx - 12.0, by - 27.0), (cx + 12.0, by - 27.0),
                          (cx + 21.0, by - 20.0), (cx + 24.0, by)]
                    bass.fill_polys(c, [bass.orient(sh, True)], K.INK)
                    K.dot(c, (cx, by - 41.0), 12.5, K.INK, seed=seed + row * 3 + col)
                    eyes.append((cx, by - 43.0))
            y += 212.0
            row += 1
    return eyes


def pull(t):
    u = k(t, T_PULL[0], T_PULL[1] - T_PULL[0], "inout3")
    z = math.exp(lerp(0.0, math.log(PULL_Z), u))
    cy = lerp(960.0, 1010.0, u)
    return z, cy


def draw_watched(c, t, lines_off=None, ring=True):
    """The section, the watchers and the web of looks. lines_off: when the looks run home into
    him (s11); ring: draw the red ring. Returns his head in frame px (or None)."""
    def off(i):
        return None if lines_off is None else lines_off + 0.025 * i
    z, cy = pull(t)
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-540.0, -cy)
    heads = {}
    room = her_room(t)
    rim = RED if strobe(t) else K.POLICE
    his = {}

    def figures(c2):
        his["head"] = him_at_window(c2, rim)

    K.fill(c, K.NIGHT)
    if z < 0.999:                                 # the city beyond the frame
        c.save()
        for dx in (-1080.0, 1080.0):
            c.save()
            K.clip_rect(c, (-3000.0, -3000.0, -30.0, 4000.0) if dx < 0 else (1110.0, -3000.0, 5000.0, 4000.0))
            c.translate(dx, 0.0)
            K.skyline(c, lit=city_lit(t))
            c.restore()
        c.restore()
    people = R.section_people(t, room, figures, others=section_scene(t, heads))
    K.draw_section(c, t, lit=lit_at(t), people=people, open_windows={HER_B: {K.HER_FLOOR}},
                   open_doors={HER_B: {K.HER_FLOOR}}, street_doors=(HIS_B, HER_B), ladder=1.0, overturned=True,
                   beams={(HIS_B, K.HIS_FLOOR)}, sky_lit=city_lit(t), field=K.NIGHT)
    flank_eyes = []
    if z < 0.999:
        flank_eyes = flank(c, t)
        bass.fill_polys(c, [bass.cut_rect(-3000.0, K.GROUND, 4000.0, 4000.0, seed=930)], K.INK)
    # the police in the street
    for i, x in enumerate((470.0, 610.0)):
        car(c, (x, K.GROUND - 4.0), 120.0, t, i)
    # his head, in section px (him_at_window reports it in stage px)
    hh = his.get("head")
    if hh is not None:
        target = R.to_section(hh)
        # the looks: each watcher's, then the far city's, then the police's
        for i, (room_, t0) in enumerate(zip(WAKE_ORDER, T_LIGHTS)):
            p = heads.get(room_)
            if p is not None:
                K.sight_line(c, p, target, t, t0 + 0.2, color=K.PAPER, dur=0.45, r=6.0, gap=22.0, head=24.0,
                             march=26.0, seed=90 + i, off=off(i))
        for i, p in enumerate(city_eyes()):
            K.sight_line(c, p, target, t, T_CITY_LOOKS + 0.11 * i, color=K.PAPER, dur=0.5, r=5.0, gap=22.0, head=20.0,
                         march=26.0, seed=110 + i, alpha=0.85, off=off(i + 3))
        # the block beyond, as it comes into view: nearest first
        flank_eyes.sort(key=lambda p: abs(p[0] - target[0]))
        for i, p in enumerate(flank_eyes):
            K.sight_line(c, p, target, t, T_PULL[0] + 0.45 + 0.09 * i, color=K.PAPER, dur=0.55, r=5.0, gap=22.0,
                         head=20.0, march=26.0, seed=140 + i, alpha=0.8, off=off(i + 1))
        K.sight_line(c, (540.0, K.GROUND - 70.0), target, t, T_POLICE_LOOK, color=K.POLICE, dur=0.45, r=7.0, gap=24.0,
                     head=26.0, march=30.0, seed=130, off=off(2))
        if heads.get("her") is not None:
            K.sight_line(c, heads["her"], target, t, T_WAKE, color=K.PAPER, dur=0.01, r=7.0, gap=24.0, head=26.0,
                         march=26.0, seed=131, off=off(0))
        # the red ring closes round him
        if ring and t >= T_RING:
            K.marker_ring(c, (target[0] - 6.0, target[1] + 48.0), 48.0, 92.0, u=k(t, T_RING, 0.42, "out"), color=RED,
                          width=12.0, seed=7)
        hh = c.user_to_device(*target)
    c.restore()
    return c.device_to_user(*hh) if hh is not None else None


def city_lit(t):
    return k(t, T_CITY[0], T_CITY[1] - T_CITY[0], "inout")


# ---------------------------------------------------------------- the scene
def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        if t < T_ROOM:
            draw_burst(c, t)
        elif t < T_OTS:
            draw_room(c, t)
        elif t < T_SIREN:
            draw_over_shoulder(c, t)
        elif t < T_WAKE:
            draw_sirens(c, t)
        else:
            draw_watched(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    out = [Cue(T_KICK, "a kick: the door jumps on its chain", gain_db=-6),
           Cue(T_BURST, "the door bursts in: impact, the chain snaps, links jingle across the floor", gain_db=-3),
           Cue(T_ROOM, "the empty room: wind, the curtain flapping; his steps", gain_db=-12, dur=T_OTS - T_ROOM),
           Cue(T_HER_LOOK, "her look flies: a high held note", gain_db=-8, dur=T_SIREN - T_HER_LOOK),
           Cue(T_HIS_LOOK, "his look flies back: a low note under hers", gain_db=-8, dur=T_SIREN - T_HIS_LOOK),
           Cue(T_MEET, "the looks meet tip to tip: the two notes clash, a struck chime", gain_db=-6),
           Cue(T_LOWER, "she lowers his receiver: the cord rattles", gain_db=-16),
           Cue(T_SWEEP, "a siren, far off, rising", gain_db=-14, dur=T_SIREN - T_SWEEP),
           Cue(T_SIREN, "sirens rising, two cars", gain_db=-6, dur=20.0 - T_SIREN)]
    out += [Cue(t0, "a window lights up: one plucked note of the neighbours' melody", gain_db=-10) for t0 in T_LIGHTS]
    out += [Cue(T_CITY_LOOKS, "the city's looks: a rising swell", gain_db=-10, dur=T_RING - T_CITY_LOOKS),
            Cue(T_RING, "the red ring: the marker squeak, a stab", gain_db=-4),
            Cue(T_PULL[0], "resolution: the strings land on the major", gain_db=-8, dur=20.0 - T_PULL[0])]
    return out
