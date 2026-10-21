"""S12 - The Trap (10.458 s) - the stakeout; deliberate stillness, then the blackout.

IN : match cut - S11's amber ember dot at screen center becomes the juror's lit window
     (sets.apartment, juror window (2,2)) at screen (540, 960), same warm halo.
Beat 1  0.00-2.64 "One juror was left."  hold on her window, tilt/crane down the facade to the
                  street: his parked car (props.car_side) in the foreground, his silhouette inside.
Beat 2  2.64-5.49 "Friday, the forecast said rain."  slow dolly toward the car (parallax), the rain
                  thickens; on "rain" lightning (fx.lightning + Light.full flash) - rain doubles.
Beat 3  5.49-9.70 "...watched the clock crawl toward three-oh-seven."  inside the car from the back
                  seat: wipers sweep the glass as foreground wipes, her amber window beyond, THE red
                  umbrella glimpsed on the back seat in a lightning flicker; dashboard clock macro
                  3:05 -> 3:06 on "crawl"; profile two-shot, rack focus head -> clock, 3:07 lands on
                  "seven", his head drops.
OUT: SMASH TO BLACK at 9.70 s, pure black to the end of the scene.
"""
import math

from engine import *
from . import _lib_s11_s13 as L

T_BLACK = 9.70


def _cuts(T):
    return [0.0, T.at("Friday"), T.at("So"), T.at("clock"), T.at("three"), T_BLACK, T.duration]


def _car_occluder(f, alpha=1.0):
    """Black silhouette of the car body + wheels so the far street does not show through it."""
    s, m, x, g = L.CAR["s"], L.CAR["facing"], L.CAR["x"], L.CAR["ground"]
    body = [(-260, -40), (-250, -75), (-200, -88), (-150, -95), (-112, -160), (-40, -178), (60, -176),
            (118, -150), (150, -104), (230, -96), (262, -78), (268, -42), (250, -30), (-250, -30)]
    pts = [(x + px * s * m, g - 36 * s + py * s) for px, py in body]
    draw.fill(f, pts, BLACK, alpha)
    for wxl in (-170, 168):
        draw.circle(f, (x + wxl * s * m, g - 36 * s), 36 * s, 1, BLACK, alpha, fill_it=True)


def _street(f, t, cam_far, cam_near, lights, ambient, rain_d, flash=0.0, bolt=None, nod=0.0, others=1.0):
    (wx, wy), _ = L.juror_window()
    win_sx = cam_far.to_screen((wx, wy))[0]
    with f.lit(lights + ([Light.full(flash)] if flash > 0 else []), ambient=ambient):
        with f.camera(cam_far):
            if bolt is not None and flash > 0.05:
                fx.lightning(f, bolt[0], bolt[1], seed=7, alpha=min(1.0, flash * 1.4), w=4.6, branches=3)
            far = L.street_far(f, t, juror_on=1.0, others=others)
            fx.splashes(f, t, L.STREET_GROUND + 4, -600, 1700, rate=0.8)
        with f.camera(cam_near):
            with (f.alpha(others) if others < 0.999 else L._null()):
                L.street_near(f, t, win_x=cam_near.to_world((win_sx, 0))[0])
            _car_occluder(f)
            win = L.car_window_poly("front")
            with (f.alpha(others) if others < 0.999 else L._null()):
                with f.clipped(lambda c: (c.move_to(*win[0]), [c.line_to(*q) for q in win[1:]], c.close_path())):
                    rig.draw_figure(f, L.driver_pose(t, nod=nod), alpha=0.9)
                L.car(f, t)
                fx.splashes(f, t, L.CAR["ground"] + 40, -600, 1700, rate=1.0, seed=8)
        fx.rain(f, t, density=rain_d, wind=6, seed=31)
    return far


# ----------------------------------------------------------------------------- A: her window
def shot_window(f, t, T, lt, dur):
    (wx, wy), _ = L.juror_window()
    k = ease("inout3", inv_lerp(0.4, dur, lt))
    cam = Camera(lerp(wx, 560, k), lerp(wy, 1330, k), lerp(0.95, 0.56, k), 0.0)
    f.set_camera(cam)
    amb = lerp(0.02, 0.2, ease("inout", inv_lerp(0.15, 1.2, lt)))
    lamp = (L.LAMP_BASE[0] - 120, L.LAMP_BASE[1] - 820 + 62)
    lights = [Light.radial((wx, wy), 300, 1.0), Light.cone(lamp, 92, 76, 1000, 0.9),
              Light.radial((L.CAR["x"] - 60, L.CAR["ground"] - 250), 520, 0.5)]
    others = ease("inout", inv_lerp(0.25, 1.15, lt))
    _street(f, t, cam, cam, lights, amb, rain_d=lerp(0.45, 0.75, k), others=others)
    # match-cut halo: the ember's warm glow lingers on her window, then settles
    halo = lerp(0.62, 0.0, ease("out3", inv_lerp(0.0, 1.0, lt)))
    if halo > 0:
        draw.glow_dot(f, (wx, wy), 105 / max(cam.zoom, 0.5), AMBER, halo, core=False)


# ----------------------------------------------------------------------------- B: lightning
def shot_lightning(f, t, T, lt, dur):
    t_rain = T.at("rain") - T.at("Friday")
    k = ease("inout", lt / dur)
    shake = 7.0 * pulse(lt, t_rain + 0.05, 0.03, 0.35)
    cam_near = Camera(lerp(560, 512, k), lerp(1330, 1700, k), lerp(0.56, 0.95, k), 0.0).shaken(
        t, amp=1.5 + shake, rot_amp=0.12 + 0.2 * shake / 7, freq=1.1, seed=21)
    cam_far = Camera(lerp(560, 552, k), lerp(1330, 1395, k), lerp(0.56, 0.61, k), 0.0).shaken(
        t, amp=1.0 + shake * 0.5, rot_amp=0.12, freq=1.1, seed=21)
    flash = L.flash_env(lt, t_rain, peaks=((0.0, 1.0), (0.12, 0.62), (0.27, 0.4)), decay=0.07)
    rain_d = lerp(0.75, 0.95, k) + 0.85 * smoothstep(t_rain - 0.05, t_rain + 0.5, lt)
    lamp = (L.LAMP_BASE[0] - 120, L.LAMP_BASE[1] - 820 + 62)
    (wx, wy), _ = L.juror_window()
    lights = [Light.radial((wx, wy), 260, 0.9), Light.cone(lamp, 92, 76, 1000, 0.9)]
    f.set_camera(cam_far)
    # the near light must be expressed in the far camera's world: map through screen space
    sx, sy = cam_near.to_screen((L.CAR["x"] - 60, L.CAR["ground"] - 250))
    lights.append(Light.radial(cam_far.to_world((sx, sy)), 520 * cam_near.zoom / cam_far.zoom, 0.5))
    bolt = ((1060, -640), (815, 200))
    _street(f, t, cam_far, cam_near, lights, 0.18, rain_d, flash=flash, bolt=bolt)


# ----------------------------------------------------------------------------- C1: in the car
def _outside(f, t, cam_out, blur=7.0, juror_on=1.0, others=0.45):
    with f.camera(cam_out):
        if blur >= 6:
            with f.blurred(blur):
                L.street_far(f, t, juror_on=juror_on, reflections=False, others=others)
        else:
            L.street_far(f, t, juror_on=juror_on, reflections=False, others=others)
        fx.rain(f, t, density=1.2, wind=6, seed=33, alpha=0.7)


def _ws_path(c):
    c.move_to(*L.WS[0])
    for q in L.WS[1:]:
        c.line_to(*q)
    c.close_path()


def _dash(f, t, minute, alpha=1.0):
    cx, cy = L.CLOCK_IN
    draw.glow_dot(f, (cx, cy), 120, AMBER, 0.35, core=False)
    draw.circle(f, (cx, cy), L.CLOCK_R * 1.18, 3.0, WHITE, alpha * 0.85)
    props.clock_face(f, (cx, cy), L.CLOCK_R, 3, minute, w=2.2, style="dash", alpha=alpha)
    for dx in (110, 190):
        draw.circle(f, (cx + dx, cy + 14), 8, 2.0, WHITE, alpha * 0.6)       # knobs


def _driver_back(t, nod=0.0):
    """Back view, seated behind the wheel (interior coords): only head and neck clear the bench."""
    p = Pose(x=170, y=1400, s=3.2, facing=0, la=24, le=10, ra=24, re=10, ll=8, lk=10, rl=8, rk=10)
    p = rig.breathe(p, t, amt=0.8, seed=22)
    return p.copy(head=p.head + 22 * nod, lean=p.lean + 6 * nod, y=p.y + 26 * nod)


def shot_interior(f, t, T, lt, dur):
    k = ease("inout3", lt / dur)
    cam = Camera(lerp(548, 585, k), lerp(925, 885, k), lerp(1.0, 1.085, k), lerp(-0.6, 0.4, k)).shaken(
        t, amp=1.2, rot_amp=0.08, freq=0.35, seed=41)
    f.set_camera(cam)
    t0 = T.at("So")
    t_fl = T.at("building") - T.at("So")
    flick = L.flash_env(lt, t_fl, peaks=((0.0, 0.8), (0.1, 0.5), (0.2, 0.32)), decay=0.06)
    lights = [Light.poly(L.WS, 0.5), Light.radial(L.CLOCK_IN, 170, 0.9), Light.radial((170, 880), 300, 0.5)]
    if flick > 0:
        lights.append(Light.full(flick))
    (wx, wy), _ = L.juror_window()
    cam_out = Camera(wx - (700 - 540) / 0.5, wy - (515 - 960) / 0.5, 0.5, 0.0)
    with f.lit(lights, ambient=0.2):
        with f.clipped(_ws_path):
            _outside(f, t, cam_out, blur=7.0)
            if flick > 0.05:
                with f.camera(cam_out):
                    fx.lightning(f, (1200, -500), (1080, 250), seed=11, alpha=flick * 0.8, w=2.6)
        L.windshield_drops(f, t, t0=t0)
        L.interior_frame(f)
        L.draw_wipers(f, t, t0=t0)
        _dash(f, t, 5)
        draw.ellipse(f, (185, 1062), 178, 44, 0, 3.4, WHITE, 0.9)          # steering wheel rim
        rig.draw_figure(f, _driver_back(t))
        L.bench_seat(f)
        # the back seat right next to the lens: THE red umbrella, out of focus (a glimpse)
        with f.blurred(7):
            props.umbrella(f, (1075, 1440), angle=191, R=215, open_=0.0, color=CRIMSON)
    draw.glow_dot(f, L.CLOCK_IN, 70, AMBER, 0.25, core=False)


# ----------------------------------------------------------------------------- C2: clock macro
def shot_clock(f, t, T, lt, dur):
    k = ease("inout3", lt / dur)
    cam = Camera(540, 975, lerp(1.0, 1.06, k), lerp(-1.2, 0.3, k)).shaken(t, amp=0.8, rot_amp=0.05, freq=0.3, seed=51)
    f.set_camera(cam)
    c = (540.0, 1010.0)
    r = 270.0
    minute = 5 + L.tick_step(t, T.at("crawl"))
    t0 = T.at("So")
    # beyond the dash: the wet windshield, wipers passing (soft)
    with f.blurred(14):
        with f.camera(Camera(540, 1650, 1.25, 0.0)):
            L.windshield_drops(f, t, t0=t0, alpha=0.6)
            L.draw_wipers(f, t, t0=t0, alpha=0.7)
            (wx, wy), _ = L.juror_window()
        draw.glow_dot(f, (760, 330), 60, AMBER, 0.7, core=True)          # her window, far, defocused
    draw.line(f, (-200, 600), (1300, 600), 3.0, WHITE, 0.55)              # dash top edge
    draw.line(f, (-200, 640), (1300, 640), 1.6, WHITE, 0.35)
    draw.line(f, (-200, 1420), (1300, 1420), 2.0, WHITE, 0.4)
    draw.glow_dot(f, c, 520, AMBER, 0.2, core=False)                     # dash lamp
    draw.circle(f, c, r * 1.16, 4.0, WHITE, 0.85)                        # chrome bezel
    draw.circle(f, c, r * 1.07, 1.6, WHITE, 0.5)
    props.clock_face(f, c, r, 3, minute, w=6.0, style="dash")
    # a slow glint across the glass
    g = (lt * 0.6) % 1.0
    draw.line(f, (c[0] - r * 0.7 + 60 * g, c[1] - r * 0.45), (c[0] - r * 0.35 + 60 * g, c[1] - r * 0.75), 3.0, WHITE, 0.25)


# ----------------------------------------------------------------------------- C3: the nod
def _profile_set(f, t, alpha=1.0):
    """Car interior seen in profile from the passenger side (nose left) - screen coords."""
    draw.bezier(f, (-60, 250), (300, 215), (800, 215), (1140, 250), 3.0, WHITE, alpha * 0.8)
    draw.stroke(f, [(175, 262), (455, 262), (190, 905), (-90, 905)], 3.0, WHITE, alpha, closed=True)
    draw.line(f, (470, 262), (210, 905), 8.0, WHITE, alpha * 0.9)                       # A-pillar
    draw.stroke(f, [(520, 270), (1000, 270), (1000, 800), (560, 800)], 2.4, WHITE, alpha * 0.6, closed=True)
    draw.line(f, (1010, 262), (1010, 1500), 7.0, WHITE, alpha * 0.8)                    # B-pillar
    draw.bezier(f, (-90, 905), (180, 920), (420, 960), (560, 1010), 3.0, WHITE, alpha)  # dash top
    draw.bezier(f, (-90, 960), (160, 980), (380, 1010), (520, 1060), 1.6, WHITE, alpha * 0.5)


def _driver_profile(t, nod):
    p = rig.sit(790, 1000, facing=-1, s=2.8)
    p = rig.breathe(p, t, amt=0.7, seed=23)
    p = p.copy(head=8 + 50 * nod, lean=4 + 27 * nod)
    p = rig.reach(p, "l", (500, 820 + 40 * nod))
    p = rig.reach(p, "r", (478, 905 + 30 * nod))
    return p


def shot_nod(f, t, T, lt, dur):
    t_seven = T.at("seven") - T.at("three")
    t_oh = T.at("oh") - T.at("three")
    k = ease("inout3", lt / dur)
    cam = Camera(lerp(560, 545, k), lerp(900, 925, k), lerp(1.0, 1.05, k), lerp(0.4, -0.4, k))
    f.set_camera(cam)
    # sleep fights back once, then wins as 3:07 lands
    nod = (0.45 * ease("inout", inv_lerp(0.0, t_oh - 0.05, lt))
           - 0.4 * ease("out3", inv_lerp(t_oh - 0.05, t_oh + 0.08, lt))
           + 0.95 * ease("in3", inv_lerp(t_seven - 0.02, t_seven + 0.42, lt)))
    nod = clamp(nod, 0.0, 1.0)
    minute = 6 + L.tick_step(t, T.at("seven"))
    # rack focus: his head -> the clock before the tick
    rk = ease("inout3", inv_lerp(t_oh - 0.12, t_oh + 0.1, lt))
    b_head = lerp(0.0, 13.0, rk)
    b_clock = lerp(11.0, 0.0, rk)
    clock_c, clock_r = (330.0, 1165.0), 172.0
    (wx, wy), _ = L.juror_window()
    cam_out = Camera(wx - (250 - 540) / 0.48, wy - (470 - 960) / 0.48, 0.48, 0.0)
    lights = [Light.radial(clock_c, 420, 0.9), Light.radial((720, 600), 460, 0.6),
              Light.poly([(175, 262), (455, 262), (190, 905), (-90, 905)], 0.6)]
    with f.lit(lights, ambient=0.2):
        with f.clipped(lambda c: (c.move_to(175, 262), c.line_to(455, 262), c.line_to(190, 905),
                                  c.line_to(-90, 905), c.close_path())):
            _outside(f, t, cam_out, blur=8.0)
        with f.clipped(lambda c: c.rectangle(520, 270, 480, 530)):
            fx.rain(f, t, density=0.9, wind=4, seed=35, alpha=0.5)
        _profile_set(f, t)
        drv = _driver_profile(t, nod)
        if b_head >= 6:
            with f.blurred(b_head):
                draw.ellipse(f, (470, 860), 26, 175, 18, 3.0, WHITE, 0.9)     # wheel rim, edge-on
                rig.draw_figure(f, drv)
        else:
            draw.ellipse(f, (470, 860), 26, 175, 18, 3.0, WHITE, 0.9)
            rig.draw_figure(f, drv)
        if b_clock >= 6:
            with f.blurred(b_clock):
                draw.circle(f, clock_c, clock_r * 1.16, 4.0, WHITE, 0.85)
                props.clock_face(f, clock_c, clock_r, 3, minute, w=4.6, style="dash")
        else:
            draw.circle(f, clock_c, clock_r * 1.16, 4.0, WHITE, 0.85)
            props.clock_face(f, clock_c, clock_r, 3, minute, w=4.6, style="dash")
    draw.glow_dot(f, clock_c, 330, AMBER, 0.2, core=False)


# ----------------------------------------------------------------------------- main
SHOTS = [shot_window, shot_lightning, shot_interior, shot_clock, shot_nod]


def render(f, t, T):
    if t >= T_BLACK:
        return                       # SMASH TO BLACK: nothing is drawn (pure black frame)
    i, lt, t0, t1 = L.shot_of(t, _cuts(T)[:-1])
    SHOTS[i](f, t, T, lt, t1 - t0)


def cues(T):
    t_in = T.at("So")
    return [
        Cue(T.at("rain") + 0.02, "thunder", gain_db=0.0, pan=0.25, distance=0.15),       # the strike on "rain"
        Cue(t_in, "wipers", gain_db=-7, pan=0.0, dur=T_BLACK - t_in - 0.02, period=L.WIPE_P),
        Cue(T.at("building"), "thunder", gain_db=-11, pan=0.4, distance=0.85),           # far flicker: the umbrella
        Cue(T.at("clock"), "clock_ticking", gain_db=-11, pan=0.05, dur=T_BLACK - T.at("clock") - 0.02, bpm=60),
        Cue(T.at("clock"), "heartbeat", gain_db=-10, pan=0.0, dur=T_BLACK - T.at("clock") - 0.02, bpm=54),
        Cue(T.at("crawl"), "clock_tick", gain_db=-3, pan=0.05),                          # 3:06
        Cue(T.at("seven"), "clock_tick", gain_db=-1, pan=-0.1),                          # 3:07 - then silence
    ]
