"""S13 - Blackout (10.917 s) - the turning point. No gore, no body: the dark window is the horror.

IN : pure black (S12 smashed to black at 3:07).
Beat 1  0.00-3.94 "I blinked. Just once."  black; the eyelid half-opens on "blinked" over a blurred
                  rainy frame and shuts; opens fully on "once" with a rack focus (blur 18 -> 0).
Beat 2  3.94-7.55 "Then I was standing in the rain. Her window was dark."  he stands in the rain beside
                  the open car door (props.car_side door_open=1) under the lamp, swaying; slow dutch
                  roll -8 deg -> +6 deg; tilt up the facade - her window (sets.apartment juror (2,2))
                  lands at screen center DARK on "dark", the same framing that opened S12 lit.
Beat 3  7.55-10.92 "And a burnt match was cooling in my left hand."  macro: his LEFT hand opens on a
                  burnt match (props.match burnt=1), the ember dies (1 -> 0), smoke; tilt down - at his
                  feet THE red umbrella lies open on the wet ground, rocking in the wind.
OUT: fast whip pan - the image streaks to the LEFT (camera pans right, f.whip + motion blur).
"""
import math

from engine import *
from . import _lib_s11_s13 as L

FIG = dict(x=298.0, ground=2050.0, s=1.6)
UMB = dict(x=505.0, ground=2096.0, R=150.0)


def _cuts(T):
    return [0.0, T.at("once"), T.at("And"), T.at("left"), T.duration]


def _detective(t, T, lift=0.0):
    """He stands beside the open door, dazed: heavy sway, head low; LEFT hand (screen-right) at his side.
    lift 0..1 raises the left forearm (the hand 'opens', palm up, on the burnt match)."""
    p = rig.stand(FIG["x"], FIG["ground"], facing=0, s=FIG["s"], la=7, le=8, ra=6, re=6, head=4)
    p = rig.breathe(p, t, amt=2.4, seed=31)
    sway = 2.2 * math.sin(t * 1.1) + 1.2 * fbm1(t * 0.4, 9)
    p = p.copy(lean=p.lean + sway)
    if lift > 0:
        k = ease("inout3", lift)
        p = p.copy(la=lerp(p.la, 16, k), le=lerp(p.le, 92, k))
    return p


def _left_hand_match(J, lift):
    """Match lying in the left hand: gripped along the forearm, then rolling across the open palm."""
    fa = math.degrees(math.atan2(J["lh"][1] - J["le"][1], J["lh"][0] - J["le"][0]))
    k = ease("inout3", clamp((lift - 0.35) / 0.65))
    ang = lerp(fa + 8, fa - 78, k)
    return ang


def _street(f, t, T, cam_far, cam_near, rain_d=1.4, lift=0.0, ember=1.0, gust=0.0, show_hand_glow=True,
            umb_vis=0.22, flash=0.0, env_blur=0.0, ambient=0.2, her=0.0, lamp_alpha=1.0):
    lamp = (L.LAMP_BASE[0] - 120, L.LAMP_BASE[1] - 820 + 62)
    p = _detective(t, T, lift)
    with f.camera(cam_near):
        J = rig.solve(p)
    win_light = L.car_window_poly("front")
    sx, sy = cam_near.to_screen(J["neck"])
    fig_far = cam_far.to_world((sx, sy))
    ix, iy = cam_near.to_screen(((win_light[0][0] + win_light[2][0]) / 2, (win_light[0][1] + win_light[2][1]) / 2))
    lights = [Light.cone(lamp, 128, 70, 1700, 0.95),
              Light.radial(fig_far, 520 * cam_near.zoom / cam_far.zoom, 0.55),
              Light.radial(cam_far.to_world((ix, iy)), 420 * cam_near.zoom / cam_far.zoom, 0.5)]
    if flash > 0:
        lights.append(Light.full(flash))
    if her > 0:
        (hx_, hy_), _ = L.juror_window()
        lights.append(Light.radial((hx_, hy_), 330, 0.85 * her))

    def env():
        with f.camera(cam_far):
            L.street_far(f, t, juror_on=0.0, lamp_alpha=lamp_alpha, frame_her=her)
            props.building(f, 1330, L.STREET_GROUND, 520, 1200, seed=93, lit=0.08, t=t, alpha=0.6,
                           lw=2.6, roof="water", cols=3, rows=7)
            draw.line(f, (1900, L.STREET_GROUND), (3400, L.STREET_GROUND), 3.0, WHITE, 1.0)
            props.streetlamp(f, (1450, L.STREET_GROUND + 20), height=470, facing=-1, t=t, on=1.0)
            fx.splashes(f, t, L.STREET_GROUND + 4, -600, 2600, rate=0.9)
        with f.camera(cam_near):
            L.street_near(f, t, juror_on=0.0)
            draw.line(f, (1900, L.CAR["ground"] + 40), (3400, L.CAR["ground"] + 40), 3.0, WHITE, 1.0)
            L.car(f, t, door_open=1.0, alpha=0.8)
            fx.light_pool(f, (330, L.CAR["ground"] + 30), 210, 34, AMBER, 0.14)    # spill from the open door
            # interior dome light spills from the open door
            draw.glow_dot(f, ((win_light[0][0] + win_light[2][0]) / 2, (win_light[0][1] + win_light[2][1]) / 2),
                          160, AMBER, 0.28, core=False)
            rock = 6.0 * math.sin(t * 2.3) + 9.0 * gust * math.sin(t * 6.1 + 0.6)
            with f.alpha(umb_vis):           # THE red umbrella, dropped open, upside down like a bowl
                L.umbrella_lying(f, UMB["x"] + 6 * rock, UMB["ground"], 90 + rock, UMB["R"], t=t)
            fx.splashes(f, t, FIG["ground"], -200, 1300, rate=1.4, seed=12)

    with f.lit(lights, ambient=ambient):
        L.rack(f, env_blur, env)
        with f.camera(cam_near):
            J = L.figure_cut(f, p, gap=6)
        fx.rain(f, t, density=rain_d, wind=8, seed=41)
    with f.camera(cam_near):
        ang = _left_hand_match(J, lift)
        tip = props.match(f, J["lh"], angle=ang, length=52, s=1.25, burnt=1.0, ember=ember,
                          smoke_amt=0.9 * ember, t=t, seed=5)
        if show_hand_glow and ember > 0:
            draw.glow_dot(f, tip, 60, AMBER, 0.45 * ember, core=False)
    return J, tip


# ----------------------------------------------------------------------------- A + B: wake up, the window
def _cams_B(t, T):
    t_tilt0, t_dark = T.at("rain") + 0.3, T.at("dark")
    rot = L.ek(t, T.at("once"), T.at("And"), -8.0, 6.0, "inout3")
    kt = ease("inout3", inv_lerp(t_tilt0, t_dark, t))
    (wx, wy), _ = L.juror_window()
    z_b = lerp(1.14, 1.24, ease("inout", inv_lerp(T.at("once"), t_tilt0, t)))
    push = ease("inout3", inv_lerp(t_dark, T.at("And") + 0.25, t))
    base = (420.0, 1770.0)
    zf = lerp(z_b, 3.1, kt) * (1 + 0.11 * push)
    far = Camera(lerp(base[0], wx, kt), lerp(base[1] - 95.0, wy, kt), zf, rot)   # far layer sits lower: parallax
    near = Camera(lerp(base[0], wx, kt), lerp(base[1], base[1] - (base[1] - wy) * 1.3, kt), lerp(z_b, 3.1, kt), rot)
    sway = 0.6 + 2.0 * (1 - kt)
    return far.shaken(t, amp=sway, rot_amp=0.15, freq=0.5, seed=7), near.shaken(t, amp=sway, rot_amp=0.15, freq=0.5, seed=7)


def shot_wake(f, t, T, lt, dur):
    t_bl, t_once = T.at("blinked"), T.at("once")
    if t < t_once:
        o = 0.0
        if t >= t_bl:
            o = (0.42 * ease("out3", inv_lerp(t_bl, t_bl + 0.22, t))
                 + 0.04 * math.sin((t - t_bl) * 26) * (1 - inv_lerp(t_bl + 0.2, t_bl + 0.45, t))
                 ) * (1 - ease("in3", inv_lerp(t_bl + 0.42, t_bl + 0.72, t)))
        if o <= 0.002:
            return                                    # eyes shut: pure black
        cf, cn = _cams_B(t_once, T)
        f.set_camera(cf)
        L.rack(f, 18.0, lambda: _street(f, t, T, cf, cn, rain_d=1.2, show_hand_glow=False))
        fx.eyelid(f, o)
        return
    shot_stand(f, t, T, lt, dur)


def shot_stand(f, t, T, lt, dur):
    t_once = T.at("once")
    o = ease("out3", inv_lerp(t_once, t_once + 0.38, t))
    blur = lerp(18.0, 0.0, ease("inout3", inv_lerp(t_once + 0.05, t_once + 0.95, t)))
    cf, cn = _cams_B(t, T)
    f.set_camera(cf)
    her = ease("inout", inv_lerp(T.at("dark") - 0.6, T.at("dark"), t))
    L.rack(f, blur, lambda: _street(f, t, T, cf, cn, rain_d=lerp(1.0, 1.45, inv_lerp(t_once, t_once + 2, t)),
                                     her=her, lamp_alpha=1.0 - 0.75 * her))
    if o < 1:
        fx.eyelid(f, o)


# ----------------------------------------------------------------------------- C: the left hand, the umbrella
def _match_angle(fore_deg, k):
    """The match gripped along the forearm (k=0) rolls across the opening palm (k=1)."""
    return lerp(fore_deg + 6, fore_deg - 82, ease("inout3", k))


def shot_macro(f, t, T, lt, dur):
    """Insert: his LEFT hand (front view: body off-frame left) turns up and opens on the burnt match;
    the ember cools and dies; the street behind is all bokeh."""
    t_and, t_cool, t_left = T.at("And"), T.at("cooling"), T.at("left")
    open_k = ease("inout3", inv_lerp(T.at("burnt") - 0.1, T.end("match") + 0.05, t))
    rise = ease("inout3", inv_lerp(t_and - 0.02, T.end("match") - 0.05, t))
    ember = 1.0 - ease("inout", inv_lerp(t_cool - 0.1, t_left - 0.02, t)) * 0.93
    ember *= 0.9 + 0.1 * math.sin(t * 11)
    sm = 7.0
    hand = (lerp(470, 600, rise) + 8 * fbm1(t * 0.6, 3), lerp(1330, 1020, rise) + 6 * fbm1(t * 0.5, 4))
    zoom = lerp(1.25, 1.42, ease("inout3", lt / dur))
    cam = Camera(lerp(540, 575, rise), lerp(1060, 960, rise), zoom, 6.0).shaken(t, amp=1.5, rot_amp=0.1, freq=0.5, seed=23)
    f.set_camera(cam)
    lamp_b = 0.85
    with f.blurred(18):                             # the wet street behind, deep out of focus
        with f.camera(Camera(540, 960, 1.0, 6.0)):
            draw.glow_dot(f, (860, 360), 230, AMBER, 0.55 * lamp_b, core=False)          # street lamp
            draw.circle(f, (860, 360), 40, 1, AMBER, 0.5, fill_it=True)
            draw.glow_dot(f, (230, 640), 150, AMBER, 0.35, core=False)                    # car dome light
            draw.circle(f, (520, 150), 26, 1, AMBER, 0.55, fill_it=True)                  # the light upstairs
            draw.line(f, (-100, 1480), (1200, 1440), 6, WHITE, 0.18)
            for i in range(10):
                x = 30 + 110 * i + 40 * hash01(i, 5)
                draw.line(f, (x, 0), (x + 60, 1920), 3, WHITE, 0.07)
    for i in range(8):                              # big soft raindrops crossing the lens
        sp = 1.2 + 0.4 * hash01(i, 2)
        ph = (t * sp + hash01(i, 3)) % 1.0
        k = int(t * sp + hash01(i, 3))
        x = cam.x - 420 + 840 * hash01(i, 4, k)
        y = cam.y - 800 + 1600 * ph
        draw.line(f, (x, y), (x + 14, y + 110), 3.0, WHITE, 0.14)
    body = Pose(x=-20, y=330 + 14 * sm - 112 * sm + 112 * sm, s=sm, facing=0, la=10, le=10, ra=8, re=6)
    body = body.copy(y=330 - 14 * sm + 112 * sm)    # left shoulder at (-20, 330): head far off-frame
    arm = rig.reach(body, "l", hand)
    J = rig.solve(arm)
    fore = math.degrees(math.atan2(J["lh"][1] - J["le"][1], J["lh"][0] - J["le"][0]))
    ang = _match_angle(fore, open_k)
    lights = [Light.radial(J["lh"], 600 * (0.35 + 0.65 * ember), intensity=1.0)]
    with f.lit(lights, ambient=0.14):
        rig.draw_figure(f, arm)
    tip = props.match(f, J["lh"], angle=ang, length=52, s=5.2, burnt=1.0, ember=ember,
                      smoke_amt=0.4 + 0.6 * ember, t=t, seed=5)
    draw.glow_dot(f, tip, 120, AMBER, 0.4 * ember, core=False)


def shot_reveal(f, t, T, lt, dur):
    """His LEFT hand at the top of the frame, tilt down: at his feet THE red umbrella, revealed by a
    lightning flicker, rocking in the wind. Then the whip."""
    t_whip = T.duration - 0.37
    ember = 0.07 * (1 - inv_lerp(T.at("left"), T.end("hand"), t))
    p = _detective(t, T, 1.0)
    J = rig.solve(p)
    hx, hy = J["lh"]
    kd = ease("inout3", inv_lerp(T.at("left") - 0.02, T.end("hand") + 0.05, t))
    cx = lerp(hx - 10, UMB["x"] - 60, kd)
    cy = lerp(hy + 120, 1975.0, kd)
    zoom = lerp(2.25, 1.5, kd)
    kw = ease("in3", inv_lerp(t_whip, T.duration, t))
    cx += 700.0 * kw
    cy -= 450.0 * kw
    cam = Camera(cx, cy, zoom, 6.0 + 2.0 * kw).shaken(t, amp=1.4, rot_amp=0.1, freq=0.6, seed=19)
    f.set_camera(cam)
    t_fl = T.at("hand") + 0.04
    flash = L.flash_env(t, t_fl, peaks=((0.0, 0.85), (0.1, 0.5), (0.22, 0.3)), decay=0.08)
    umb = lerp(0.22, 1.0, ease("out3", inv_lerp(t_fl - 0.02, t_fl + 0.12, t)))
    gust = ease("inout", inv_lerp(t_fl - 0.1, t_fl + 0.4, t))
    cam_far = cam.copy(y=cam.y - 95.0)       # far layer slightly lower (parallax, keeps lines off his head)
    if kw > 0:   # the umbrella streaks out of frame-left: fade it before it reaches the edge
        ux = cam.to_screen((UMB["x"], UMB["ground"] - 60))[0]
        umb *= clamp((ux - 220.0) / 320.0)
    _street(f, t, T, cam_far, cam, rain_d=1.35, lift=1.0, ember=ember, gust=gust, umb_vis=umb, flash=flash,
            ambient=0.2 + 0.25 * kw)
    if kw > 0:
        v = 3 * 700.0 * zoom * inv_lerp(t_whip, T.duration, t) ** 2 / (T.duration - t_whip) / 24.0
        f.whip = (-min(300.0, 1.6 * v), 0.0)


SHOTS = [shot_wake, shot_stand, shot_macro, shot_reveal]


def render(f, t, T):
    i, lt, t0, t1 = L.shot_of(t, _cuts(T))
    SHOTS[i](f, t, T, lt, t1 - t0)


def cues(T):
    return [
        Cue(0.0, "tinnitus", gain_db=-9, pan=0.0, dur=T.at("Then") + 0.3),
        Cue(T.at("standing") + 0.2, "door_creak", gain_db=-14, pan=0.25),                # open car door sways
        Cue(T.at("cooling") + 0.02, "ember_sizzle", gain_db=-8, pan=0.1),                 # the ember dies
        Cue(T.at("hand") + 0.04, "thunder", gain_db=-7, pan=-0.3, distance=0.55),         # the flicker reveal
        Cue(T.at("hand") - 0.1, "wind_gust", gain_db=-9, pan=0.2, dur=1.0),
        Cue(T.at("hand") + 0.12, "umbrella_flap", gain_db=-4, pan=0.15),                  # the umbrella rocks
        Cue(T.end("hand") + 0.05, "umbrella_flap", gain_db=-9, pan=0.15),
        Cue(T.duration - 0.37, "whip", gain_db=-2, pan=-0.2),
    ]


def motion_blur(t, T):
    return 5 if t > T.duration - 0.30 else 1          # whip: real sub-frame blur under the f.whip streak
