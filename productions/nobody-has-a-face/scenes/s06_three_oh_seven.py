"""S06 - Three-Oh-Seven (7.0 s).

"The killer only worked in the rain. Always at seven minutes past three.
 Like he was keeping an appointment."

Shot plan (scene seconds; word hits come from T.at)
  0.000-0.417  IN: THE pocket watch on the desk, identical to S05's last frame - face centred at
               screen (540, 960), r = 300 px, 3:07
  0.417        MATCH CUT on a clock tick: a street clock in the rain, same face size and position
  0.42-2.37    "The killer only worked in the rain." - slow-motion rain streaks across the face, drops
               crown on the rim and slide down the glass; slow pull-back reveals the post, the
               streetlamp light and the wet street (eased, log-space zoom)
  2.37-3.90    "Always at seven minutes past three." - stacked 9:16 montage: four panels slide in on
               "Always" / "seven" / "minutes" / "past" (tower, stairwell wall clock, station clock, a
               clock on a wet wall), every one at 3:07; each panel drifts on its own (parallax)
  3.90         "three": the bell tolls - every face flashes, shock rings, the panels punch in
  4.37-5.30    "Like he was keeping an appointment": every minute hand ticks in sync (stuck at 3:07)
  5.30-5.62    the four faces converge on centre and merge into one: his pocket watch (clock stops)
  5.62-6.55    pull back: the watch is in his LEFT hand (front view: screen-right), he stands in his
               dark office, blind stripes across him
  6.18-6.66    he slips it into his coat pocket at the hip without a glance (head stays level); his
               right hand rests on the desk edge
  6.36-6.98    OUT: the light closes on his left hand at the pocket; the frame darkens on the hand
               (last frame: hand at screen ~(529, 1211), camera Camera(680, 1100, 1.9))
"""
import math
from contextlib import nullcontext

from engine import *
from engine.timing import SceneTiming
from scenes._lib_s05_s07 import cam_for, zlerp, desk_insert, glow_scaled

O = sets.OFFICE
S05_DUR = SceneTiming("s05").duration
CUT = 10 / FPS                                   # 0.417 s: match cut on a tick
SC = (540.0, 960.0)                              # street clock centre (world W2)
SR = 300.0
GROUND = 2440.0

DET_X, DET_S = 650.0, 1.75                       # S06 end: he stands behind the desk, facing us
WATCH_REST = (712.0, 1100.0)                     # watch centre while held in his left hand
WATCH_RW = 24.0                                  # its radius in the office world
POCKET = (668.0, 1232.0)                         # where the left hand slips it away (coat pocket, hip)
DESK_REST = (588.0, 1287.0)                      # his right hand rests on the desk edge

PANEL_Y = (395.0, 707.0, 1019.0, 1331.0)         # panel centres (screen)
PANEL_X = (430.0, 650.0, 430.0, 650.0)           # clock x inside each panel (zigzag)
PANEL_H = 290.0
PANEL_R = 104.0                                   # clock radius on screen inside a panel


class K:
    pass


def keys(T):
    k = K()
    k.p_in = (T.at("always"), T.at("seven"), T.at("minutes"), T.at("past"))
    k.toll = T.at("three")
    k.ticks = (T.at("like"), T.at("keeping"), T.at("appointment"))
    k.merge0 = k.ticks[2] + 0.02
    k.merge1 = k.merge0 + 0.32
    k.pull1 = k.merge1 + 0.93
    k.pocket0, k.pocket1 = 6.18, 6.66
    k.dark0, k.dark1 = 6.36, 6.98
    return k


def tick_twitch(t, k):
    """Minute-hand twitch on each synchronized tick: jumps a minute, springs back (stuck at 3:07)."""
    v = 0.0
    for tk in k.ticks:
        if tk <= t < tk + 0.35:
            u = t - tk
            v = max(v, clamp(u / 0.03) * (1 - ease("out3", inv_lerp(0.07, 0.3, u))))
    return v


# ----------------------------------------------------------------------------- street clock (W2)
def _clock_rain_fx(f, t, c, r, slow=0.3):
    """Drops crowning on the clock's rim and sliding down the glass, in slow motion."""
    rim = r * 1.12
    for i in range(14):
        per = 1.1 + 0.9 * hash01(5, i)
        ph = hash01(5, i, 1)
        cyc = math.floor(t * slow / per * 3 + ph)
        tau = (t * slow / per * 3 + ph) - cyc
        if tau > 0.55:
            continue
        a = math.radians(205 + 130 * hash01(5, i, int(cyc), 2))
        p = (c[0] + rim * math.cos(a), c[1] + rim * math.sin(a))
        nx, ny = math.cos(a), math.sin(a)
        k = tau / 0.55
        h = 26 * math.sin(math.pi * k)
        w = 10 + 18 * k
        tx, ty = -ny, nx
        for sgn in (-1, 1):
            q0 = (p[0] + tx * sgn * w * 0.3, p[1] + ty * sgn * w * 0.3)
            q1 = (p[0] + tx * sgn * w + nx * h, p[1] + ty * sgn * w + ny * h)
            draw.line(f, q0, q1, 2.0, WHITE, 0.75 * (1 - k))
        for d in range(3):
            da = (d - 1) * 0.5
            dist = (20 + 30 * k) * (1 + 0.3 * d)
            dp = (p[0] + (nx + tx * da) * dist, p[1] + (ny + ty * da) * dist + 40 * k * k)
            draw.circle(f, dp, 2.4, 1, WHITE, 0.7 * (1 - k), fill_it=True)
    for i in range(7):                      # drops sliding down the glass
        per = 2.4 + 1.6 * hash01(9, i)
        ph = hash01(9, i, 1)
        cyc = math.floor(t * slow * 2 / per + ph)
        tau = t * slow * 2 / per + ph - cyc
        x = c[0] + (hash01(9, i, int(cyc), 3) - 0.5) * r * 1.3
        y0 = c[1] - r * 0.75 + r * 0.3 * hash01(9, i, int(cyc), 4)
        y = y0 + r * 1.1 * tau ** 1.6
        if (x - c[0]) ** 2 + (y - c[1]) ** 2 > (r * 0.95) ** 2:
            continue
        a = 0.55 * math.sin(math.pi * tau)
        draw.line(f, (x, y - 50 * tau), (x, y), 1.4, WHITE, a * 0.45)
        draw.ellipse(f, (x, y), 4.2, 5.4, 0, 1, WHITE, a, fill_it=True)


def street_clock_cam(t):
    u = inv_lerp(CUT, 2.55, t)
    e = ease("inout", u)
    z = zlerp(1.0, 0.6, e)
    return cam_for((SC[0], SC[1] + 300 * e), (540.0, 960.0 + 120 * e * 0.0), z)


def draw_street_clock(f, t, cam, alpha=1.0):
    f.set_camera(cam)
    lamp = (1260.0, 360.0)
    lights = [Light.cone(lamp, 142, 54, 2200, 1.0), Light.radial((SC[0] + 150, SC[1] - 120), 520, 0.5)]
    with f.alpha(alpha) if alpha < 0.999 else nullcontext():
        with f.camera(cam.parallax(0.62)):
            for i, (bx, bw, bh) in enumerate(((-420, 360, 2300), (40, 300, 2700), (420, 380, 2100), (900, 340, 2500))):
                props.building(f, bx, GROUND + 400, bw, bh, seed=60 + i, lit=0.05, t=t, alpha=0.28, lw=2.0)
        fx.light_cone(f, lamp, 142, 50, 2100, AMBER, 0.07, glow=0.3)
        with f.lit(lights, ambient=0.3, soften=4):
            # the post, collar, base and finial
            cx = SC[0]
            draw.line(f, (cx - 24, SC[1] + SR * 1.12 + 40), (cx - 24, GROUND - 120), 4.0, WHITE, 0.95)
            draw.line(f, (cx + 24, SC[1] + SR * 1.12 + 40), (cx + 24, GROUND - 120), 4.0, WHITE, 0.95)
            draw.rect(f, cx - 50, SC[1] + SR * 1.12 + 6, 100, 34, 3.4, WHITE, 0.95)
            for yy in (SC[1] + 700, SC[1] + 760):
                draw.rect(f, cx - 36, yy, 72, 18, 3.0, WHITE, 0.8)
            draw.stroke(f, [(cx - 24, GROUND - 120), (cx - 70, GROUND - 20), (cx - 90, GROUND),
                            (cx + 90, GROUND), (cx + 70, GROUND - 20), (cx + 24, GROUND - 120)], 3.6, WHITE, 0.95)
            draw.line(f, (cx, SC[1] - SR * 1.12), (cx, SC[1] - SR * 1.12 - 60), 4.0, WHITE, 0.95)
            draw.circle(f, (cx, SC[1] - SR * 1.12 - 78), 18, 3.4, WHITE, 0.95)
            draw.line(f, (-1400, GROUND), (2400, GROUND), 3.4, WHITE, 0.9)
            draw.line(f, (-1400, GROUND + 70), (2400, GROUND + 70), 2.4, WHITE, 0.6)
            draw.circle(f, SC, SR * 1.12 + 3, 1, BLACK, 1.0, fill_it=True)     # opaque dial
            props.clock_face(f, SC, SR, 3, 7, w=6.5, style="wall")
            _clock_rain_fx(f, t, SC, SR)
            fx.rain(f, t, density=1.0, wind=6, seed=31, slowmo=0.22, alpha=1.0)
        fx.splashes(f, t * 0.35, GROUND, -900, 2000, rate=0.6, seed=12, alpha=0.6, size=2.0)
        fx.reflection(f, 880, GROUND + 6, 300, 120, AMBER, 0.35, t, seed=2)


# ----------------------------------------------------------------------------- montage panels
def _panel_clock(f, c, r, style, minute, pulse):
    draw.circle(f, c, r * (1.15 if style == "tower" else 1.12) + 3, 1, BLACK, 1.0, fill_it=True)
    props.clock_face(f, c, r, 3, minute, w=3.4, style=style)
    if pulse > 0.01:
        draw.circle(f, c, r * (1.2 if style != "pocket" else 1.0), 4.0, AMBER, 0.85 * pulse, glow=1.0)


def panel_tower(f, t, minute, pulse):
    c = (0.0, 0.0)
    for i, (bx, bw, top) in enumerate(((-760, 240, 60), (-500, 170, 10), (330, 210, 40), (560, 260, 85))):
        draw.stroke(f, [(bx, 400), (bx, top), (bx + bw, top), (bx + bw, 400)], 2.2, WHITE, 0.4)
        for j in range(3):
            wx = bx + 30 + j * (bw - 60) / 2
            on = hash01(7, i, j) < 0.35
            draw.rect(f, wx - 10, top + 34, 20, 26, 1 if on else 1.4, AMBER if on else WHITE,
                      0.55 if on else 0.25, fill_it=on, glow=0.5 if on else 0.0)
    draw.glow_dot(f, c, 230, AMBER, 0.18, core=False)
    for sx in (-1, 1):
        draw.line(f, (sx * 170, -520), (sx * 170, 700), 3.4, WHITE, 0.9)
        draw.line(f, (sx * 200, -170), (sx * 200, 700), 2.4, WHITE, 0.6)
    draw.line(f, (-230, -170), (230, -170), 3.0, WHITE, 0.9)
    draw.line(f, (-230, -194), (230, -194), 2.0, WHITE, 0.7)
    draw.stroke(f, [(-210, -194), (0, -520), (210, -194)], 3.0, WHITE, 0.9)
    _panel_clock(f, c, 100, "tower", minute, pulse)
    fx.rain(f, t, density=0.55, wind=10, seed=41, alpha=0.7)


def panel_stair(f, t, minute, pulse):
    c = (40.0, -10.0)
    bulb = props.bulb(f, (-300, -260), 120, swing=6 * math.sin(t * 1.9), on=1.0, s=0.8, t=t, glow_r=220)
    fx.light_cone(f, bulb, 70, 70, 520, AMBER, 0.1, glow=0.3)
    steps = []
    x, y = -620.0, 320.0
    for i in range(9):
        steps += [(x, y), (x, y - 46)]
        x += 70
        y -= 46
        steps.append((x, y))
    draw.stroke(f, steps, 2.6, WHITE, 0.75)
    draw.line(f, (-640, 200), (40, -246), 3.0, WHITE, 0.8)
    for i in range(10):
        xx = -600 + i * 68
        y_rail = 200 - (xx + 640) * (446 / 680)
        y_step = 320 - 46 * int((xx + 620) / 70) - 10
        draw.line(f, (xx, y_rail), (xx, y_step), 1.6, WHITE, 0.55)
    _panel_clock(f, c, 96, "wall", minute, pulse)


def panel_station(f, t, minute, pulse):
    c = (0.0, 10.0)
    # a lit train streams past behind the hanging clock
    for i in range(9):
        wx = ((i * 260 - t * 900) % 2340) - 1170
        draw.rect(f, wx, -40, 170, 64, 1, AMBER, 0.32, fill_it=True, glow=0.45)
        draw.rect(f, wx, -40, 170, 64, 1.6, WHITE, 0.3)
    for yy in (-58, 42):
        draw.line(f, (-1200, yy), (1200, yy), 2.0, WHITE, 0.35)
    for k_ in range(5):                                  # speed lines
        yy = -50 + 24 * k_
        x0 = ((k_ * 410 - t * 1500) % 2400) - 1200
        draw.line(f, (x0, yy), (x0 + 220, yy), 1.2, WHITE, 0.3)
    # platform: canopy beam, columns, edge
    draw.line(f, (-1200, -126), (1200, -126), 5.0, WHITE, 0.85)
    for x in (-760, -380, 380, 760):
        draw.line(f, (x, -126), (x, 160), 3.2, WHITE, 0.8)
        draw.rect(f, x - 14, -126, 28, 14, 2.0, WHITE, 0.8)
    for sx in (-30, 30):
        draw.line(f, (sx, -126), (sx * 0.7, c[1] - 104), 2.6, WHITE, 0.85)
    draw.line(f, (-1200, 120), (1200, 120), 3.4, WHITE, 0.85)
    draw.line(f, (-1200, 132), (1200, 132), 1.6, WHITE, 0.5)
    _panel_clock(f, c, 100, "wall", minute, pulse)


def panel_wetwall(f, t, minute, pulse):
    c = (-60.0, -10.0)
    for row in range(-5, 7):
        yy = row * 44
        draw.line(f, (-900, yy), (900, yy), 1.4, WHITE, 0.28)
        off = 60 if row % 2 else 0
        for xx in range(-900 + off, 900, 120):
            draw.line(f, (xx, yy), (xx, yy + 44), 1.2, WHITE, 0.22)
    draw.line(f, (330, -400), (330, 400), 3.0, WHITE, 0.75)
    draw.line(f, (356, -400), (356, 400), 3.0, WHITE, 0.75)
    for i in range(9):                                  # rivulets running down the wall
        x = -560 + 130 * i + 40 * hash01(3, i)
        y = -300 + ((t * 120 * (0.6 + 0.6 * hash01(3, i, 1)) + 600 * hash01(3, i, 2)) % 700)
        draw.line(f, (x, y - 90), (x + 3, y), 1.4, WHITE, 0.5)
        draw.ellipse(f, (x + 3, y), 3.5, 4.5, 0, 1, WHITE, 0.75, fill_it=True)
    fx.light_cone(f, (700, -500), 135, 40, 1100, AMBER, 0.08, glow=0.3)
    _panel_clock(f, c, 98, "wall", minute, pulse)
    fx.rain(f, t, density=0.5, wind=12, seed=43, alpha=0.6)


PANELS = (panel_tower, panel_stair, panel_station, panel_wetwall)
PANEL_CLOCK = (((0.0, 0.0), 100.0, "tower"), ((40.0, -10.0), 96.0, "wall"),
               ((0.0, 10.0), 100.0, "wall"), ((-60.0, -10.0), 98.0, "wall"))


def panel_cam(i, t, k, punch):
    """Camera of panel i: maps its local world so the clock sits at the panel centre."""
    (cx, cy), r, _ = PANEL_CLOCK[i]
    z = PANEL_R / r * (1 + 0.05 * ease("inout", inv_lerp(k.p_in[i], k.merge0, t))) * (1 + 0.05 * punch)
    drift = (0, 0)
    if i == 1:
        drift = (0, -30 * ease("inout", inv_lerp(k.p_in[i], k.merge0, t)))
    if i == 2:
        drift = (-50 * ease("inout", inv_lerp(k.p_in[i], k.merge0, t)), 0)
    side = 1 if i % 2 == 0 else -1
    slide = side * 1150 * (1 - ease("out3", inv_lerp(k.p_in[i], k.p_in[i] + 0.3, t)))
    return cam_for((cx + drift[0], cy + drift[1]), (PANEL_X[i] + slide, PANEL_Y[i]), z), slide


def draw_montage(f, t, k):
    tw = tick_twitch(t, k)
    minute = 7 + tw
    toll = pulse(t, k.toll, 0.03, 0.55)
    tick_p = max([pulse(t, tk, 0.02, 0.18) for tk in k.ticks] + [0.0])
    for i, fn in enumerate(PANELS):
        if t < k.p_in[i]:
            continue
        cam, slide = panel_cam(i, t, k, toll + 0.4 * tick_p)
        y0 = PANEL_Y[i] - PANEL_H / 2
        with f.screen(), f.clipped(lambda c, y0=y0, s=slide: c.rectangle(s, y0, W, PANEL_H)):
            with f.camera(cam):
                fn(f, t, minute, max(toll, 0.6 * tick_p))
                # shock ring on the bell
                if toll > 0.02:
                    (cx, cy), r, _ = PANEL_CLOCK[i]
                    e = clamp((t - k.toll) / 0.6)
                    draw.circle(f, (cx, cy), r * (1.25 + 1.3 * e), 3.0, AMBER, 0.6 * (1 - e), glow=0.7)
        with f.screen():
            draw.line(f, (slide, y0), (slide + W, y0), 1.6, WHITE, 0.35)
            draw.line(f, (slide, y0 + PANEL_H), (slide + W, y0 + PANEL_H), 1.6, WHITE, 0.35)


def draw_merge(f, t, k):
    """The four faces fly to centre and fuse (screen space)."""
    u = ease("inout3", inv_lerp(k.merge0, k.merge1, t))
    env = 1 - clamp((t - k.merge0) / 0.12)
    if env > 0:
        with f.alpha(env):
            draw_montage(f, t, k)
    with f.screen():
        for i in range(4):
            (cx, cy), r, style = PANEL_CLOCK[i]
            c = lerp((PANEL_X[i], PANEL_Y[i]), (540.0, 960.0), u)
            rr = lerp(PANEL_R, 260.0, u)
            a = 1.0 if i == 3 else (1 - 0.6 * u)
            props.clock_face(f, c, rr, 3, 7, w=3.4 + 2.6 * u, style=style, alpha=a)
        fl = pulse(t, k.merge1 - 0.04, 0.03, 0.25)
        if fl > 0.01:
            draw.circle(f, (540, 960), 260 * 1.15, 6.0, WHITE, 0.5 * fl, glow=1.2)


# ----------------------------------------------------------------------------- office: his watch
def detective_end(t, k):
    p = rig.stand(DET_X, O["floor_y"], facing=0, s=DET_S)
    p = rig.breathe(p, t, amt=0.8, seed=12)
    J = rig.solve(p)
    u = ease("inout3", inv_lerp(k.pocket0, k.pocket1, t))
    hand = lerp((WATCH_REST[0] - 2, WATCH_REST[1] + WATCH_RW + 4), (POCKET[0] + 6, POCKET[1]), u)
    hand = (hand[0] + 1.5 * fbm1(t * 0.8, 3), hand[1] + 1.5 * fbm1(t * 0.8, 7))
    p = rig.reach(p, "l", hand)
    p = rig.reach(p, "r", DESK_REST)          # right hand rests on the desk edge
    # head level and still - he never looks at the watch
    return p.copy(head=p.head * 0.4), u


def watch_cam(t, k):
    """From the merged face (r 260 px at centre) pull back to a medium shot of him."""
    z0 = 260.0 / WATCH_RW
    e = ease("inout3", inv_lerp(k.merge1, k.pull1, t))
    final = Camera(680.0, 1100.0, 1.9)
    sp_end = final.to_screen(WATCH_REST)
    z = zlerp(z0, 1.9, e)
    return cam_for(WATCH_REST, lerp((540.0, 960.0), sp_end, e), z)


def draw_office_end(f, t, k):
    cam = f.set_camera(watch_cam(t, k))
    p, u = detective_end(t, k)
    dk = ease("inout", inv_lerp(k.dark0, k.dark1, t))
    J = rig.solve(p)
    hand = J["lh"]
    stripes_k = 1 - dk
    lights = [Light.radial(hand, lerp(520, 150, dk), 0.95)]
    if stripes_k > 0.01:
        lights += [Light.rect(O["window"][0] - 10, O["window"][1] - 10, O["window"][0] + O["window"][2] + 10,
                              O["window"][1] + O["window"][3] + 10, 0.5 * stripes_k),
                   Light.radial((842, 1158), 460, 0.8 * stripes_k),
                   Light.cone((900, 520), 120, 40, 1100, 0.8 * stripes_k)]
    with f.lit(lights, ambient=0.2 * (1 - dk), soften=4):
        with glow_scaled(f, 0.4 * (1 - dk)):
            sets.office(f, t, umbrella=True, lamp_on=0.0, window_light_alpha=0.16 * stripes_k)
        rig.draw_figure(f, p)
        x, ty, w, h = O["desk"]
        draw.fill(f, [(x - 22, ty + 2), (x + w + 22, ty + 2), (x + w + 22, ty + h + 4), (x - 22, ty + h + 4)], BLACK, 1.0)
        sets.desk(f)
        sets.desk_lamp(f, on=0.95 * (1 - dk), t=t)
        # the watch in his left hand (slips away at the pocket). Drawn in screen space so the
        # prop keeps S05's proportions (its centre cap is sized in world units).
        wa = 1 - ease("in", inv_lerp(k.pocket1 - 0.2, k.pocket1, t))
        if wa > 0.01:
            sc = 1 - 0.35 * u
            wc = (hand[0] + 2, hand[1] - (WATCH_RW + 4) * sc)
            ch = ((wc[0] + 14, wc[1] - 70), (POCKET[0] + 30, POCKET[1] - 40), (POCKET[0] - 4, POCKET[1] + 4))
            z = cam.zoom
            sc_c = cam.to_screen(wc)
            ch_s = tuple(cam.to_screen(q) for q in ch)
            with f.screen():
                props.clock_face(f, sc_c, WATCH_RW * sc * z, 3, 7, w=2.8 * z ** 0.35, style="pocket", alpha=wa,
                                 chain=ch_s)
    if dk < 0.99:
        fx.light_cone(f, (842, 1158), 96, 66, 520, AMBER, 0.07 * (1 - dk), glow=0.25)


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    k = keys(T)
    if t < CUT:                                     # continuation of S05's last shot
        desk_insert(f, S05_DUR + t, Camera(540.0, 960.0, 1.0))
        return
    if t < k.merge0:
        bg = 1 - ease("inout", inv_lerp(k.p_in[0] - 0.05, k.p_in[0] + 0.45, t))
        if bg > 0.01:
            if t >= k.p_in[0] - 0.05:
                with f.blurred(6.0 + 6.0 * (1 - bg)):
                    draw_street_clock(f, t, street_clock_cam(t), alpha=bg)
            else:
                draw_street_clock(f, t, street_clock_cam(t))
        f.set_camera(Camera())
        draw_montage(f, t, k)
        return
    if t < k.merge1:
        draw_merge(f, t, k)
        return
    draw_office_end(f, t, k)


def motion_blur(t, T):
    k = keys(T)
    for a in k.p_in:
        if a + 0.02 < t < a + 0.2:
            return 2
    return 1


def cues(T):
    k = keys(T)
    c = [Cue(CUT - 0.01, "clock_tick", gain_db=-3),
         Cue(CUT + 0.05, "thunder", gain_db=-20, distance=0.9)]
    for i, a in enumerate(k.p_in):
        c.append(Cue(a - 0.03, "whoosh", gain_db=-16, size=0.25, pan=0.5 if i % 2 == 0 else -0.5))
    c.append(Cue(k.toll, "bell_toll", gain_db=-3, count=3))
    for tk in k.ticks:
        c.append(Cue(tk, "clock_tick", gain_db=-5))
    c.append(Cue(k.merge1 - 0.04, "clock_stop", gain_db=-4))
    return c
