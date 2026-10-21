"""S15 - Blue Lights (11.208 s).

IN : opens in blue - a police strobe at full blue; his real hollow head sits exactly where the
     reflected head ended s14 (screen (540, 920), r ~197): the mirror's face becomes his.
0-3.45  "The blue lights came seven minutes later.": blue/crimson strobe stripes through the
        blinds (sets.office window_light alternating on core.siren with afterglow, stripes_offset
        sweeping) wash over him; slow pull-back reveals the office; he settles (slow exhale).
3.45-5.15 "My own precinct.": top-down, three police cars (props.car_top police=True) pull in and
        brake in a fan in front of the building, light bars strobing on the wet street.
5.15-6.78 "I didn't run.": inside - flashlights sweep behind the door glass, the door bursts open
        (door_light=BLUE), two figures with BLUE flashlight beams; on "run" the beams pin him.
6.78-9.75 "Where do you run, when the man you're chasing...": medium shot, beams from the left,
        strobes from the right; he slowly raises both hands in two goes (forearms first, elbows low,
        then all the way up; target = rig.hands_up with the elbows opened, see L.surrender).
9.75-end "is you?": the burnt match slips from his LEFT hand and tumbles in slow motion through
        the beams (one beam drops to follow it); the camera follows it down, racking the room out.
OUT (s16 continues it exactly): the cold burnt match centred at screen (540, 960), 283.6 px long
     (zoom 3.5), screen angle ~73 deg (curled tip down), tumbling clockwise ~72 deg/s and falling
     ~486 world px/s (slow motion), camera roll -6 deg, background racked to ~7 px blur.
"""
import math

from engine import *
from scenes import _lib_s14_s15 as L


def _K(T):
    return dict(blue=T.at("blue"), seven=T.at("seven"), later_end=T.end("later"),
                my=T.at("my"), precinct=T.at("precinct"), precinct_end=T.end("precinct"),
                i=T.at("i"), run=T.at("run"), run_end=T.end("run"),
                where=T.at("where"), chasing=T.at("chasing"), is_=T.at("is"), you=T.at("you", 1),
                end=T.duration)


C_TOP = 3.45          # cut to the top-down street (in the pause between "later." and "My")
C_DOOR = 5.15         # cut back inside, facing the door (in the pause between "precinct." and "I")


def _c_hands(K):
    return K["where"] - 0.02


SLOWMO = 0.35


def _tau(t, K):
    """Story time: slows to 35 % once the match slips (strobes, dust, rain all slow down)."""
    s = K["is_"]
    return t if t < s else s + (t - s) * SLOWMO


# ============================================================================ the room
HIM_X = 600.0


def _him(t, K):
    """He stands in the open floor in front of his desk, facing the room (front view)."""
    p = L.detective_rest(HIM_X, 2.0)
    p = p.copy(la=12.0, le=26.0, ra=9.0, re=10.0)                 # left hand loosely holds the match
    settle = ease("inout3", inv_lerp(0.6, 3.3, t))                # slow exhale: knees soften, shoulders sink
    p = p.copy(ra=p.ra - 3 * settle, la=p.la - 3 * settle, head=-5.0 * settle, lean=1.2 * settle,
               lk=p.lk + 7 * settle, rk=p.rk + 7 * settle, ll=p.ll + 2 * settle, rl=p.rl + 2 * settle)
    p = rig.on_ground(p, L.FLOOR)
    # hands up, reluctantly, in two goes: forearms rise first (elbows low, palms out) ... then all the way
    k1 = ease("inout3", inv_lerp(6.95, 7.95, t))
    k2 = ease("inout3", inv_lerp(8.3, 9.3, t))
    if k1 > 0:
        mid = p.copy(la=30.0, le=100.0, ra=30.0, re=100.0)
        p = p.blend(mid, k1)
        if k2 > 0:
            p = p.blend(L.surrender(p), k2)
    slip = pulse(t, K["is_"], 0.04, 0.5)                          # fingers open: the hand gives a little
    p = p.copy(le=p.le - 7 * slip, head=p.head - 3.0 * ease("inout3", inv_lerp(9.3, 10.6, t)))
    return rig.breathe(p, t, 0.55, seed=31)


def _match_angle(J):
    return L.forearm_angle(J, "l") + 10.0


MATCH_S = 1.9
MATCH_L = 52.0 * MATCH_S * 0.82      # burnt match length (curled tip); centre = base + dir * 0.45 * MATCH_L
# OUT state (s16 continues it exactly - keep these in step with s16's opening):
#   match centre at screen (540, 960), 283.6 px long (zoom 3.5), screen angle ~73.6 deg (tip down),
#   tumbling clockwise ~72 deg/s, falling 486 world px/s, camera roll -6 deg, room racked out of focus.
END_ZOOM, END_ROLL = 3.5, -6.0
FALL_G = 330.0                       # slow motion (real time would be ~3900 px/s^2 for a 2.0 figure)


def _dir(a):
    return (math.cos(math.radians(a)), math.sin(math.radians(a)))


def _match_state(t, K):
    """(base, angle, falling, ember) of the burnt match: in his left hand, then tumbling in slow
    motion. Seven minutes on, it is cold (no ember)."""
    ts = K["is_"]
    if t < ts:
        J = rig.solve(_him(t, K))
        return J["lh"], _match_angle(J), False, 0.0
    J = rig.solve(_him(ts, K))
    a0 = _match_angle(J)
    d0 = _dir(a0)
    c0 = (J["lh"][0] + d0[0] * MATCH_L * 0.45, J["lh"][1] + d0[1] * MATCH_L * 0.45)
    dt = t - ts
    c = (c0[0] + 14.0 * dt, c0[1] + 6.0 * dt + 0.5 * FALL_G * dt * dt)
    ang = a0 + 105.0 * dt + 14.0 * math.sin(2.4 * dt)
    d = _dir(ang)
    return (c[0] - d[0] * MATCH_L * 0.45, c[1] - d[1] * MATCH_L * 0.45), ang, True, 0.0


def _match_center(t, K):
    b, a, _, _ = _match_state(t, K)
    d = _dir(a)
    return (b[0] + d[0] * MATCH_L * 0.45, b[1] + d[1] * MATCH_L * 0.45)


# ---------------------------------------------------------------------------- the police
COP = dict(  # x0 -> x1 in ONE deliberate step between t0 and t1 (stride chosen so it is one step)
    a=dict(s=2.0, floor=L.FLOOR, x0=130.0, x1=262.0, t0=5.95, t1=6.55, stride=0.56),
    b=dict(s=1.6, floor=L.FLOOR - 34.0, x0=46.0, x1=140.0, t0=6.1, t1=6.7, stride=0.62),  # deeper in the hall
)
COP_S = {k: v["s"] for k, v in COP.items()}


def _door_open(t):
    return ease("outback", inv_lerp(5.43, 5.82, t))


def _cop(t, which):
    """Cop A is in the doorway when it bursts open, then takes one step into the room;
    cop B steps into the doorway behind him."""
    c = COP[which]
    s, fl = c["s"], c["floor"]
    if t <= c["t0"]:
        p = rig.stand(c["x0"], fl, facing=1, s=s, lean=4.0)
    elif t < c["t1"]:
        speed = (c["x1"] - c["x0"]) / (c["t1"] - c["t0"])
        p = rig.walk(t - c["t0"], c["x0"], fl, speed, facing=1, s=s, stride=c["stride"], arm=0.5, lean=1.0)
    else:
        speed = (c["x1"] - c["x0"]) / (c["t1"] - c["t0"])
        w = rig.walk(c["t1"] - c["t0"], c["x0"], fl, speed, facing=1, s=s, stride=c["stride"], arm=0.5, lean=1.0)
        st = rig.stand(w.x, fl, facing=1, s=s, lean=4.0)
        p = w.blend(st, ease("inout", inv_lerp(c["t1"], c["t1"] + 0.35, t)))
    return rig.breathe(p, t, 0.5, seed=50 if which == "a" else 57)


def cop_footfalls():
    return [COP["a"]["t1"], COP["a"]["t1"] + 0.3, COP["b"]["t1"]]


def _beam(t, K, which, p):
    """Flashlight hand point and beam angle (deg): a searching sweep, then pinned on him."""
    J = rig.solve(p)
    sh = J["shoulder"]
    aim = (HIM_X, 1015.0) if which == "a" else (HIM_X + 8, 935.0)
    if which == "a" and t > K["is_"]:            # the beam drops to follow the falling match
        mc = _match_center(t - 0.12, K)
        aim = lerp(aim, mc, ease("inout3", inv_lerp(K["is_"] + 0.05, K["is_"] + 0.75, t)))
    pin_t = K["run"] - 0.12 if which == "a" else 6.4
    sweep = -12.0 + 16.0 * math.sin(2.3 * t + (0.0 if which == "a" else 1.7))
    target = math.degrees(math.atan2(aim[1] - sh[1], aim[0] - sh[0]))
    k = ease("out3", inv_lerp(pin_t, pin_t + 0.22, t))
    ang = lerp(target + sweep, target, k) + 0.6 * fbm1(t * 1.1, 9 if which == "a" else 13)
    hand = (sh[0] + 150.0 * math.cos(math.radians(ang)), sh[1] + 150.0 * math.sin(math.radians(ang)))
    return hand, ang


def _cops(f, t, K, draw_it=True):
    """Draw the two figures + flashlights (draw_it) and return [(lens, angle, intensity)]."""
    beams = []
    o = _door_open(t)
    if o <= 0.02:
        return beams
    x, y, w, h = L.DOOR
    ww = w * (1 - 0.82 * o)
    for which in ("b", "a"):
        if which == "b" and t < COP["b"]["t0"]:
            continue
        p = _cop(t, which)
        hand, ang = _beam(t, K, which, p)
        p = rig.reach(p, "r", hand)
        alpha = 0.9 if which == "b" else 1.0
        on = clamp(o * 1.5) if which == "a" else smoothstep(COP["b"]["t0"], COP["b"]["t0"] + 0.2, t)
        fs = 1.6 * COP_S[which] / 2.0
        J = rig.solve(p)
        d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        lens = (J["rh"][0] + d[0] * 30 * fs, J["rh"][1] + d[1] * 30 * fs)
        if draw_it:
            # in the hallway they only show inside the door opening; cop A then steps through it
            through = 0.0 if which == "b" else ease("inout", inv_lerp(COP["a"]["t0"], COP["a"]["t0"] + 0.35, t))
            ext = 3000.0 * through
            with f.clipped(lambda c, ww=ww, ext=ext: c.rectangle(x + ww - ext * 0.02, y - 4 - ext,
                                                                 w - ww + ext, h + 8 + ext)):
                rig.draw_figure(f, p, alpha=alpha)
                L.flashlight(f, J["rh"], ang, on=on, s=fs, alpha=alpha)
        beams.append((lens, ang, on * (0.8 if which == "b" else 1.0)))
    return beams


def _beam_haze(f, beams, length=1150.0, hits=()):
    for lens, ang, k in beams:
        if k > 0:
            fx.light_cone(f, lens, ang, 15.0, length, BLUE, 0.26 * k, glow=0.55)
            fx.light_cone(f, lens, ang, 6.0, length * 0.8, BLUE, 0.2 * k, glow=0.45)
            draw.glow_dot(f, lens, 70, BLUE, 0.9 * k, core=False)
    for c, k in hits:                       # where a beam lands on him
        if k > 0:
            draw.glow_dot(f, c, 120, BLUE, 0.45 * k, core=False)


def _beam_lights(beams, length=1250.0, k_all=1.0):
    return [Light.cone(lens, ang, 17.0, length, intensity=1.2 * k * k_all) for lens, ang, k in beams if k > 0]


# ---------------------------------------------------------------------------- strobes
def _strobe(t, K):
    b, r = L.strobe(_tau(t, K))
    k = 1.0 - 0.75 * smoothstep(K["is_"] + 0.2, K["is_"] + 1.1, t)
    return b * k, r * k


def _room(f, t, K, door=0.0, him=True, match=True, board=True, mid=None):
    """The office under police strobes: colored blind stripes, the board as s14 left it, him."""
    tau = _tau(t, K)
    b, r = _strobe(t, K)
    col, v = (BLUE, b) if b >= r else (CRIMSON, r)
    off = (tau * 0.55) % 1.0
    wx, wy, ww, wh = L.WINDOW
    draw.rect(f, wx, wy, ww, wh, 1, col, 0.16 * v, fill_it=True, glow=1.1 * v)
    draw.glow_dot(f, (wx + ww * 0.5, wy + wh * 0.5), 420, col, 0.45 * v, core=False)
    sets.office(f, t, lamp_on=0.0, door_open=door, door_light=BLUE if door > 0 else None,
                window_light=col, window_light_alpha=0.05 + 0.3 * v, stripes_offset=off, board=True)
    if board:
        L.board_after(f, t, glass_color=col, glass_v=v)
    if mid is not None:          # e.g. beam haze: behind the figures, never painted over them
        mid()
    J = None
    if him:
        J = rig.draw_figure(f, _him(t, K))
    return J, (col, v, off)


def _room_lights(t, K, extra=(), strength=1.0):
    b, r = _strobe(t, K)
    v = max(b, r)
    off = (_tau(t, K) * 0.55) % 1.0
    lights = [Light.poly(q, (0.18 + 0.8 * v) * strength) for q in L.stripe_quads(off)]
    wx, wy, ww, wh = L.WINDOW
    lights.append(Light.rect(wx - 20, wy - 20, wx + ww + 20, wy + wh + 20, 0.3 + 0.6 * v))
    return lights + list(extra)


def _draw_match(f, t, K, beams=()):
    base, ang, falling, ember = _match_state(t, K)
    props.match(f, base, angle=ang, length=52, s=MATCH_S, burnt=1.0, ember=ember, t=t, seed=7)  # ember 0
    if falling:     # catches the blue beams as it tumbles through them
        d = _dir(ang)
        c = (base[0] + d[0] * MATCH_L * 0.45, base[1] + d[1] * MATCH_L * 0.45)
        glint = 0.0
        for lens, a, k in beams:
            dx, dy = c[0] - lens[0], c[1] - lens[1]
            da = abs((math.degrees(math.atan2(dy, dx)) - a + 180) % 360 - 180)
            glint = max(glint, k * clamp(1 - da / 8.5))
        if glint > 0:
            draw.glow_dot(f, c, 80, BLUE, 0.55 * glint, core=False)


# ============================================================================ shot 1: strobes
def _cam_strobe(t, K):
    k = ease("inout3", inv_lerp(0.25, C_TOP, t))
    drift = 0.02 * inv_lerp(0.0, 0.25, t)
    return Camera(lerp(600.0, 585.0, k), lerp(953.8, 1012.0, k), lerp(2.9 * (1 - drift), 1.3, k), lerp(0.0, -1.5, k))


def _shot_strobe(f, t, K):
    f.set_camera(_cam_strobe(t, K))
    head = rig.solve(_him(t, K))["head"]
    # the blue flash that opens the scene catches his head first: the ring carries over from s14
    key = Light.radial(head, 170, 0.9 * (1 - smoothstep(0.05, 0.8, t)))
    with f.lit(_room_lights(t, K, [key]), ambient=0.16):
        J, _ = _room(f, t, K)
        _draw_match_in_hand(f, t, K)


def _draw_match_in_hand(f, t, K):
    _draw_match(f, t, K)


# ============================================================================ shot 2: top-down street
CARS = [  # (P0, P1, P3, final angle, t_start, t_stop, siren phase)
    ((450.0, -700.0), (450.0, 560.0), (330.0, 1250.0), 125.0, 3.27, 4.28, 0.00),
    ((600.0, -900.0), (600.0, 480.0), (560.0, 1270.0), 92.0, 3.33, 4.52, 0.21),
    ((660.0, -1100.0), (660.0, 420.0), (800.0, 1240.0), 55.0, 3.42, 4.78, 0.43),
]
CAR_S = 0.62


def _car(t, spec):
    P0, P1, P3, a, t0, t1, ph = spec
    d = (math.cos(math.radians(a)), math.sin(math.radians(a)))
    P2 = (P3[0] - d[0] * 330.0, P3[1] - d[1] * 330.0)
    u = ease("out3", inv_lerp(t0, t1, t))

    def B(s):
        m = 1 - s
        return (m ** 3 * P0[0] + 3 * m * m * s * P1[0] + 3 * m * s * s * P2[0] + s ** 3 * P3[0],
                m ** 3 * P0[1] + 3 * m * m * s * P1[1] + 3 * m * s * s * P2[1] + s ** 3 * P3[1])
    c = B(u)
    e = 1e-3
    p0, p1 = B(max(0.0, u - e)), B(min(1.0, u + e))
    ang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])) if u < 1 else a
    nose_dip = 3.0 * pulse(t, t1 - 0.05, 0.03, 0.25)        # brake dive
    return c, ang, nose_dip, ph


def _street(f, t):
    a = 0.9
    # vertical road coming down from the top into the street (T junction), rounded corners
    for x, sgn in ((300.0, -1), (780.0, 1)):
        draw.line(f, (x, -1600), (x, 940), 3.0, WHITE, a)
        draw.arc(f, (x + sgn * 60.0, 940.0), 60.0, 0 if sgn < 0 else 90, 90 if sgn < 0 else 180, 3.0, WHITE, a)
        x2 = x + sgn * 60.0
        draw.line(f, (x2, 1000), (x2 + sgn * 1400, 1000), 3.0, WHITE, a)
    for k in range(-16, 10):
        y0 = k * 120.0
        if y0 > 900:
            break
        draw.line(f, (540, y0), (540, y0 + 60), 2.2, WHITE, 0.45)
    for k in range(-12, 13):
        x0 = 540 + k * 120.0
        if 260 < x0 < 800:
            continue
        draw.line(f, (x0, 1220), (x0 + 60, 1220), 2.2, WHITE, 0.4)
    draw.line(f, (-1000, 1440), (2100, 1440), 3.4, WHITE, 0.9)          # curb
    draw.line(f, (-1000, 1452), (2100, 1452), 1.6, WHITE, 0.5)
    draw.line(f, (-1000, 1570), (2100, 1570), 3.4, WHITE, 0.9)          # building line
    for i in range(4):                                                  # front steps
        yy = 1570 + 22 * (i + 1)
        draw.line(f, (470 - 8 * i, yy), (650 + 8 * i, yy), 2.2, WHITE, 0.6)
    draw.line(f, (470, 1570), (440, 1670), 2.2, WHITE, 0.6)
    draw.line(f, (650, 1570), (680, 1670), 2.2, WHITE, 0.6)
    for c, rx, ry, sd in (((420, 760), 70, 40, 1), ((700, 1330), 90, 34, 2), ((180, 1300), 60, 28, 3),
                          ((640, 300), 54, 36, 4), ((930, 1150), 64, 30, 5)):
        fx.puddle(f, c, rx, ry, t, seed=sd, alpha=0.5)
    fx.ripples(f, t, 0, -400, 1100, 1430, rate=0.9, seed=12, alpha=0.38, squash=1.0)


def _cam_top(t, K):
    k = ease("inout3", inv_lerp(C_TOP, C_DOOR, t))
    return Camera(lerp(562.0, 560.0, k), lerp(880.0, 1215.0, k), lerp(0.92, 1.4, k), lerp(-7.0, -1.5, k))


def _car_lights(f, c, ang, t, alpha=1.0, halo=True):
    """The light bar + headlights of props.car_top (same geometry), so the halos can be drawn once
    while the car body is smeared."""
    b, r = siren(t)
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    loc = lambda x, y: (c[0] + (x * ca - y * sa) * CAR_S, c[1] + (x * sa + y * ca) * CAR_S)
    lb, lr = loc(-20, -34), loc(-20, 34)
    draw.circle(f, lb, 12 * CAR_S, 1, BLUE, (0.35 + 0.65 * b) * alpha, fill_it=True, glow=1.4 * b)
    draw.circle(f, lr, 12 * CAR_S, 1, CRIMSON, (0.35 + 0.65 * r) * alpha, fill_it=True, glow=1.4 * r)
    if halo:
        if b > 0:
            draw.glow_dot(f, lb, 320 * CAR_S, BLUE, 0.5 * b, core=False)
        if r > 0:
            draw.glow_dot(f, lr, 320 * CAR_S, CRIMSON, 0.4 * r, core=False)
        for side in (-1, 1):
            draw.glow_dot(f, loc(256, side * 52), 44 * CAR_S, AMBER, 0.7)


def _shot_top(f, t, K):
    f.set_camera(_cam_top(t, K))
    cars = [_car(t, c) for c in CARS]
    lights = []
    for (c, ang, dip, ph) in cars:
        b, r = siren(t + ph)
        lights.append(Light.radial(c, 360, 0.25 + 0.6 * max(b, r)))
        d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        nose = (c[0] + d[0] * 165, c[1] + d[1] * 165)
        lights.append(Light.cone(nose, ang, 44, 520, 0.7))
    with f.lit(lights, ambient=0.42):
        _street(f, t)
        for spec, (c, ang, dip, ph) in zip(CARS, cars):
            d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
            nose = (c[0] + d[0] * 165, c[1] + d[1] * 165)
            fx.light_cone(f, nose, ang, 40, 460, AMBER, 0.13, glow=0.4)
            b, r = siren(t + ph)
            col, v = (BLUE, b) if b >= r else (CRIMSON, r)
            fx.light_pool(f, c, 300, 300, col, 0.16 * (0.35 + v), glow=0.5)
            # motion streak along the car's own path (2 frames of travel), body only
            p0, p1 = _car(t - 1.0 / 24, spec)[0], _car(t + 1.0 / 24, spec)[0]
            travel = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * _cam_top(t, K).zoom
            k = 1 if travel < 10 else min(12, 2 + int(travel / 14))
            for i in range(k):
                ts = t + (2.0 / 24) * ((i + 0.5) / k - 0.5) if k > 1 else t
                ci, ai, di, _ = _car(ts, spec)
                dd = (math.cos(math.radians(ai)), math.sin(math.radians(ai)))
                cc = (ci[0] + dd[0] * di, ci[1] + dd[1] * di)
                props.car_top(f, cc, ai, CAR_S, police=False, t=t + ph, alpha=1.0 / k, headlights=0.0)
                _car_lights(f, cc, ai, t + ph, alpha=1.0 / k, halo=False)
            _car_lights(f, (c[0] + d[0] * dip, c[1] + d[1] * dip), ang, t + ph, alpha=0.0, halo=True)


# ============================================================================ shot 3: the door
def _hits(t, K):
    """Where the two beams land on him once pinned (soft blue glow on his chest / head)."""
    ka = ease("out3", inv_lerp(K["run"] - 0.12, K["run"] + 0.1, t)) * (1 - smoothstep(K["is_"], K["is_"] + 0.5, t))
    kb = ease("out3", inv_lerp(6.4, 6.65, t))
    return [((HIM_X, 1015.0), ka), ((HIM_X + 8, 935.0), 0.8 * kb)]


def _cam_door(t, K):
    k = ease("inout", inv_lerp(C_DOOR, _c_hands(K), t))
    hit = pulse(t, 5.45, 0.02, 0.25)
    return Camera(lerp(392.0, 410.0, k), lerp(1060.0, 1050.0, k), lerp(1.12, 1.2, k), 0.0).shaken(
        t, amp=1.5 + 7 * hit, rot_amp=0.08 + 0.3 * hit, seed=33)


def _shot_door(f, t, K):
    f.set_camera(_cam_door(t, K))
    o = _door_open(t)
    beams = _cops(f, t, K, draw_it=False)
    x, y, w, h = L.DOOR
    extra = _beam_lights(beams)
    if o > 0:
        ww = w * (1 - 0.82 * o)
        extra.append(Light.rect(x + ww - 10, y - 10, x + w + 10, y + h, 1.0 * clamp(o)))
        extra.append(Light.poly([(x + w, y + h - 140), (x + w + 560 * o, y + h), (x + w, y + h)], 0.5 * clamp(o)))
        extra.append(Light.radial((x + w + 30, y + h * 0.35), 300, 0.55 * clamp(o)))
    hits = _hits(t, K)
    extra += [Light.radial(c, 150, 0.9 * k) for c, k in hits if k > 0]
    with f.lit(_room_lights(t, K, extra), ambient=0.14):
        _room(f, t, K, door=max(0.0, o), mid=lambda: _beam_haze(f, beams, hits=hits))
        _draw_match_in_hand(f, t, K)
        if o <= 0.02:      # before it opens: flashlights moving behind the door glass, light under the door
            px, py, pw, ph = x + 26, y + 30, w - 52, h * 0.42
            a_in = smoothstep(C_DOOR, C_DOOR + 0.1, t)
            with f.clipped(lambda c: c.rectangle(px, py, pw, ph)):
                for j, (fr, ph0) in enumerate(((7.0, 0.0), (5.3, 2.1))):
                    gx = px + pw * (0.5 + 0.55 * math.sin(fr * t + ph0))
                    band = [(gx - 26, py - 10), (gx + 14, py - 10), (gx + 34, py + ph + 10), (gx - 6, py + ph + 10)]
                    draw.fill(f, band, BLUE, 0.35 * a_in, glow=1.0 * a_in)
            v = 0.5 + 0.5 * math.sin(9.0 * t)
            draw.line(f, (x + 8, y + h - 3), (x + w - 8, y + h - 3), 3.0, BLUE, 0.4 + 0.5 * v, glow=0.9 * v)
        _cops(f, t, K)
        fx.dust(f, t, (150, 700, 900, 1300), n=70, seed=5, alpha=0.5)


# ============================================================================ shots 4-5: hands up, the match
def _cam_hands(t, K):
    ch = _c_hands(K)
    k = ease("inout", inv_lerp(ch, K["is_"], t))
    cam = Camera(lerp(622.0, 640.0, k), lerp(1000.0, 975.0, k), lerp(1.8, 2.2, k), lerp(-1.5, -3.5, k))
    f_k = ease("inout3", inv_lerp(K["is_"] + 0.05, K["is_"] + 0.85, t))
    if f_k > 0:
        mc = _match_center(t, K)
        cam = Camera(lerp(cam.x, mc[0], f_k), lerp(cam.y, mc[1], f_k), lerp(cam.zoom, END_ZOOM, f_k),
                     lerp(cam.rot, END_ROLL, f_k))
    return cam


def _shot_hands(f, t, K):
    f.set_camera(_cam_hands(t, K))
    beams = _cops(f, t, K, draw_it=False)
    focus = ease("inout3", inv_lerp(K["is_"] + 0.1, K["is_"] + 0.8, t))       # rack focus room -> match
    amb = lerp(0.12, 0.05, focus)
    hits = _hits(t, K)
    extra = _beam_lights(beams, k_all=1.0 - 0.6 * focus) + [Light.radial(c, 150, 0.9 * k) for c, k in hits if k > 0]
    with f.lit(_room_lights(t, K, extra, strength=1.0 - 0.6 * focus), ambient=amb):
        if focus > 0.01:
            with f.blurred(7.0 * focus):
                _room(f, t, K)
            _beam_haze(f, beams, hits=hits)
        else:
            _room(f, t, K, mid=lambda: _beam_haze(f, beams, hits=hits))
        fx.dust(f, _tau(t, K), (300, 650, 1000, 1500), n=130, seed=8, alpha=0.6)
        if t < K["is_"]:
            _draw_match_in_hand(f, t, K)
    if t >= K["is_"]:
        _draw_match(f, t, K, beams)          # the hero: crisp, outside the light mask


# ============================================================================ entry points
def render(f, t, T):
    K = _K(T)
    if t < C_TOP:
        _shot_strobe(f, t, K)
    elif t < C_DOOR:
        _shot_top(f, t, K)
    elif t < _c_hands(K):
        _shot_door(f, t, K)
    else:
        _shot_hands(f, t, K)


def cues(T):
    K = _K(T)
    c = [
        Cue(0.0, "siren_approach", gain_db=-6, pan=0.3, dur=4.9),
        Cue(CARS[0][5] - 0.32, "car_brake", gain_db=-6, pan=-0.45),
        Cue(CARS[1][5] - 0.32, "car_brake", gain_db=-5, pan=0.0),
        Cue(CARS[2][5] - 0.32, "car_brake", gain_db=-6, pan=0.45),
        Cue(4.86, "car_door_close", gain_db=-9, pan=-0.35),
        Cue(5.02, "car_door_close", gain_db=-10, pan=0.4),
        Cue(5.43, "door_open", gain_db=-3, pan=-0.55),
        Cue(5.78, "radio_static", gain_db=-11, pan=-0.6),
        Cue(8.55, "radio_static", gain_db=-16, pan=-0.6),
        Cue(K["is_"] + 0.02, "whoosh", gain_db=-17, pan=0.2, size=0.15),
        Cue(K["is_"] + 0.05, "reverse_swell", gain_db=-9, dur=K["end"] - K["is_"] - 0.05),
    ]
    for tt in (5.0, 5.15, 5.3):                                  # boots in the hallway, before the door
        c.append(Cue(tt, "footstep", gain_db=-13, pan=-0.6, weight=0.75, wet=1))
    for tt, g in zip(cop_footfalls(), (-8, -12, -12)):          # the step into the room, B behind him
        c.append(Cue(tt, "footstep", gain_db=g, pan=-0.5, weight=0.8, wet=1))
    return c


def motion_blur(t, T):
    half = 0.25 / FPS + 1e-4                       # sub-frames span t +- half (engine shutter 0.5/FPS)
    if any(t - half < c <= t + half for c in (C_TOP, C_DOOR, _c_hands(_K(T)), T.at("is"))):
        return 1                                    # never blend across a cut
    return 1                        # the cars are smeared in-scene along their own paths
