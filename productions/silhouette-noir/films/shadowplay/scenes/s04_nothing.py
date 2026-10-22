"""s04 · NOTHING: the police in apartment 9 find an empty room; outside, a cop's torch finds
HER in her window instead.

A  0.0-5.6  inside apartment 9 (sets.Apartment9, emptied: no lamp, sheet, table or rig).
     0.15  the door bursts open: hall light, a cop's silhouette in the doorway, his torch
           beam cuts in; the police strobe washes blue / red through the window.
     [police@0.985] a second torch from the hall. The beams search, then land on nothing:
     [body@2.704]  torch 1 on the bare floor where she fell;
     [blood@3.516] torch 2 on the bare back wall where the sheet hung;
     [woman@4.48]  torch 1 on the bare window; torch 2 joins it.
B  5.6-12.0 outside: her building ('hers' facade) seen from window 9's side of the street.
     5.6-7.0  crane down her facade (dark windows, the strobe washing it) to the street: the
              police car at the near curb, light bar strobing, a cop beside it.
     [L10 6.2] 7.15 the cop raises his torch; the beam climbs the facade, the camera with
              it, and finds HER window: she stands in it, caught, eyes on the street.
     [dreamed@8.963] she steps back into the dark; the beam holds on the empty window.
     9.6   the torch drops; the camera pulls back down to the street; the cop walks off left,
           the police car pulls away right, its strobe sliding over the wet street and
           fading.
OUT (bars, 2 horizontal, 1.0 s at 11.0-12.0) a calm, mostly dark frame: her building, every
     window on her floor dark, the empty wet street, rain.
"""
import math

from engine import draw
from engine import figure as FIG
from engine.core import clamp, lerp, smoothstep, fbm1, noise1
from engine.frame import Camera
from engine.motion import Actor
from engine.timing import Cue
from films.shadowplay import cast, sets
from films.shadowplay.scenes import _lib_s02_s04 as L

INK = sets.INK
CUT_T = 5.6
APT = sets.Apartment9(origin=(540.0, 880.0), scale=1.0)
HERS = sets.Facade(origin=(540.0, 3940.0), scale=1.0, variant="hers")
HERS_BLOCKS = sets.neighbours(HERS)
HW = sets.HER_WINDOW                                  # 13
HWR = HERS.window_rect(HW)
HWC = HERS.window_center(HW)
HERS_LIT = {2: 0.55, 7: 0.45, 17: 0.8, 24: 0.6, 29: 0.5, 31: 0.75, 38: 0.5}


def _words(T):
    return dict(police=T.at("police"), body=T.at("body"), blood=T.at("blood"), woman=T.at("woman"),
                year=T.at("year"), they=T.at("They"), dreamed=T.at("dreamed"), it=T.at("it"))


def _ease_keys(keys, t):
    """Piecewise eased interpolation of tuples: keys [(t, value, ease), ...]."""
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        t0, v0 = keys[i - 1][0], keys[i - 1][1]
        t1, v1 = keys[i][0], keys[i][1]
        if t <= t1:
            e = keys[i][2] if len(keys[i]) > 2 else "inout"
            k = L.kseg(t, t0, t1, e)
            return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
    return keys[-1][1]


# ============================================================================= A: apartment 9
def door_open(t):
    return sets.door_swing(t, [(0.15, 0.0), (0.30, 1.0, "out3"), (0.55, 0.84, "inout"), (0.9, 0.88, "inout")])


def _torch_targets(w):
    body, blood, woman = w["body"], w["blood"], w["woman"]
    t1 = [(0.30, (-0.6, 0.5, 3.4)), (1.05, (0.9, 1.4, 4.2)), (1.8, (0.5, 0.25, 3.8)),
          (body - 0.28, (-0.35, 0.05, 3.3)), (body, (0.05, 0.0, 3.05), "out3"), (woman - 0.35, (0.0, 0.05, 3.1)),
          (woman, (0.02, 1.62, 4.2), "out3"), (CUT_T + 0.5, (0.05, 1.66, 4.2))]
    t2 = [(w["police"] - 0.05, (-1.2, 2.3, 2.8)), (1.7, (-0.3, 2.0, 4.2)), (2.5, (1.3, 1.2, 3.4)),
          (blood - 0.3, (0.2, 1.9, 4.2)), (blood, (-0.82, 1.45, 4.2), "out3"), (woman + 0.15, (-0.8, 1.5, 4.2)),
          (woman + 0.55, (-0.12, 1.45, 4.2), "inout"), (CUT_T + 0.5, (-0.1, 1.42, 4.2))]
    return t1, t2


def _settle(t, t_land, amp=0.04):
    """A small overshoot wobble after a beam lands (metres)."""
    dt = t - t_land
    if dt < 0 or dt > 0.8:
        return 0.0
    return amp * math.exp(-dt * 6.0) * math.sin(dt * 18.0)


COP1_X, COP1_Z = -1.55, 1.78          # in the doorway
TORCH_Y = 1.38


def torches(t, w):
    """[dict(pos, dir, cone, power)] for Apartment9.draw, and the torch-1 3D pos/target."""
    t1, t2 = _torch_targets(w)
    out = []
    if t >= 0.27:
        on = smoothstep(0.27, 0.36, t)
        step = smoothstep(0.35, 1.3, t)
        pos = (COP1_X + 0.25 * step, TORCH_Y + 0.02 * math.sin(t * 7.0) * (1 - step), COP1_Z + 0.1 * step)
        tg = _ease_keys(t1, t)
        tg = (tg[0] + _settle(t, w["body"]) + 0.012 * fbm1(t * 1.7, 5), tg[1] + _settle(t, w["woman"], 0.03),
              tg[2])
        out.append(dict(pos=pos, dir=tuple(b - a for a, b in zip(pos, tg)), cone=7.5, power=2.8 * on, reach=6.0,
                        target=tg))
    if t >= w["police"] - 0.1:
        on = smoothstep(w["police"] - 0.1, w["police"] + 0.05, t)
        pos = (-1.75, 1.55, 1.42)
        tg = _ease_keys(t2, t)
        tg = (tg[0] + _settle(t, w["blood"], 0.05) + 0.012 * fbm1(t * 1.5, 9), tg[1] + 0.01 * fbm1(t * 2.0, 11), tg[2])
        out.append(dict(pos=pos, dir=tuple(b - a for a, b in zip(pos, tg)), cone=6.5, power=2.3 * on, reach=6.0,
                        target=tg))
    return out


@L.lru_cache(maxsize=2)
def cop_in_door():
    x, fy, k = APT.place(COP1_X, COP1_Z)
    a = Actor(cast.COP, cast.cop(), x=x - 40.0, ground=fy, facing=0.0, scale=1.84 * k * 343.0 / 630.0 / 1.0 * (600.0 / 343.0) / 1.75,
              seed=41)
    a.stand(0.35, at=-1.0)
    a.walk(to=x + 30.0, at=0.35, speed=90.0)
    a.stand(until=20.0)
    return a


def _cop_torch_hand(a, t, tl):
    """Arm of the cop in the door raised toward the torch's screen direction."""
    sk = a.skeleton(t)
    return sk


def draw_apartment(f, t, T, w):
    cam = _ease_keys([(0.0, (470.0, 960.0, 0.96)), (1.6, (470.0, 960.0, 0.96)),
                      (w["body"] + 0.3, (500.0, 1010.0, 1.0), "inout"),
                      (w["blood"] + 0.3, (455.0, 955.0, 1.03), "inout"),
                      (w["woman"] + 0.4, (520.0, 905.0, 1.10), "inout"), (CUT_T, (528.0, 900.0, 1.13))], t)
    f.set_camera(Camera(*cam))
    tl = torches(t, w)
    op = door_open(t)
    hall = 0.75 * smoothstep(0.12, 0.3, t) + 0.15

    def people(f_, t_):
        if t_ < 0.2:
            return
        a = cop_in_door()
        with f_.layer() as Lc:
            a.draw(f_, t_, Lc, eyes=False)
            if tl:
                pos, tg = tl[0]["pos"], tl[0]["target"]
                o = APT.P(*pos)
                e = APT.P(*tg)
                ang = math.degrees(math.atan2(e[1] - o[1], e[0] - o[0]))
                sets.flashlight(Lc, (o[0] - 30.0 * math.cos(math.radians(ang)), o[1] - 30.0 * math.sin(math.radians(ang))),
                                ang, scale=0.5)
    APT.draw(f, t, lamp=0.0, lamp_stand=False, sheet=False, table=False, rig=False, door_open=op, hall=hall,
             police=1.0, street=0.3, flashlights=[dict(pos=d["pos"], dir=d["dir"], cone=d["cone"], power=d["power"],
                                                       reach=d["reach"]) for d in tl],
             hooks={"after_door": people})
    f.haze(sets.PAL.fog_at(1.0), 0.04)


# ============================================================================= B: her building
def street_cam(t, w):
    """Camera on her building from the street (facade units)."""
    return Camera(*_ease_keys([(CUT_T, (548.0, 1500.0, 0.86)), (7.05, (600.0, 3560.0, 0.80), "inout"),
                               (7.25, (600.0, 3560.0, 0.80)), (8.25, (548.0, 1330.0, 0.95), "inout3"),
                               (9.65, (548.0, 1300.0, 0.97), "inout"), (11.0, (600.0, 2780.0, 0.52), "inout3"),
                               (12.2, (602.0, 2800.0, 0.515), "out")], t))


ST_DEPTH = 760.0
CAR_U = 0.62
COP_X = 250.0
COP_U = 0.95
CAR_X0 = 860.0


def car_x(t):
    """The police car pulls away right after the cop is done (eased start)."""
    dt = t - 10.25
    if dt <= 0:
        return CAR_X0
    return CAR_X0 + 260.0 * dt * dt + 60.0 * dt


@L.lru_cache(maxsize=2)
def street_cop(st_key, raise_t=7.15, lower_t=9.6):
    st = sets.Street(HERS.ground_y, depth=ST_DEPTH, seed=5)
    gy = st.lane_y(COP_U)
    sc = 233.0 * st.depth_scale(COP_U) / 600.0 * 1.06
    a = Actor(cast.COP, cast.cop(), x=COP_X, ground=gy, facing=0.0, scale=sc, seed=43)
    a.stand(until=lower_t + 0.45, at=-1.0)
    a.walk(to=COP_X - 900.0, at=lower_t + 0.45, speed=150.0, turn=0.5)
    # the torch arm: low (pool on the street) -> up at her window -> down
    a.key("arm.R.sh", [(raise_t - 0.1, 28.0), (raise_t + 0.45, 168.0, "out3"), (lower_t, 166.0),
                       (lower_t + 0.35, 30.0, "inout")], fade=0.2)
    a.key("arm.R.elbow", [(raise_t - 0.1, 12.0), (raise_t + 0.45, 4.0), (lower_t + 0.35, 12.0)], fade=0.2)
    a.key("head", [(raise_t - 0.2, 0.0), (raise_t + 0.5, -32.0, "out3"), (lower_t, -30.0), (lower_t + 0.4, 0.0)],
          fade=0.2)
    return a, st


def beam_target(t, w):
    """Where the cop's torch points (facade world): the street at his feet, up the facade,
    onto her window, held, then down."""
    raise_t, lower_t = 7.15, 9.6
    gx, gy = COP_X + 140.0, HERS.ground_y + 330.0
    keys = [(raise_t, (gx, gy)), (raise_t + 0.4, (430.0, 2700.0), "in3"), (7.9, (610.0, 1650.0), "inout"),
            (8.2, (HWC[0] + 8.0, HWC[1] - 10.0), "out3"), (lower_t, (HWC[0] + 4.0, HWC[1] - 8.0)),
            (lower_t + 0.4, (gx + 200.0, gy), "in3")]
    p = _ease_keys(keys, t)
    wob = 1.0 if t < 8.2 else 0.3
    return (p[0] + 14.0 * wob * fbm1(t * 1.4, 17), p[1] + 10.0 * wob * fbm1(t * 1.2, 19))


def caught(t, w):
    """How much of her window the beam holds (0..1)."""
    return smoothstep(8.05, 8.25, t) * (1.0 - smoothstep(9.6, 9.85, t))


@L.lru_cache(maxsize=2)
def her_at_window(dreamed=8.963):
    x0, y0, x1, y1 = HWR
    sc = HERS.person_h / cast.HER.height
    a = Actor(cast.HER, cast.her(), x=(x0 + x1) / 2 - 12.0, ground=HERS.floor_y(HW), facing=90.0, scale=sc, seed=44)
    a.stand(until=40.0, at=-5.0, idle=0.3)
    a.key("arm.R.sh", [(-5.0, 6.0), (40.0, 6.0)], fade=0.0)
    a.key("head", [(-5.0, 14.0), (40.0, 14.0)], fade=0.0)        # looking down at the street
    return a


def step_back(t, dreamed):
    return L.kseg(t, dreamed, dreamed + 0.45, "inout")


def draw_her_window(f, t, w):
    """Window 13 caught in the torch beam: the pool of light inside, her shadow thrown up
    the wall behind her, her silhouette with the eyes catching the light, the sash bars."""
    lv = caught(t, w)
    if lv <= 0.005:
        return
    x0, y0, x1, y1 = HWR
    ww, wh = x1 - x0, y1 - y0
    k_back = step_back(t, w["dreamed"])
    a = her_at_window(w["dreamed"])
    tgt = beam_target(t, w)
    col = sets.mix(sets.HOT, (1.0, 1.0, 1.0), 0.35)
    # the pool of torch light in the room (on the drapes and the back wall)
    with f.light(blur=6.0) as A:
        A.save()
        A.rectangle(x0, y0, ww, wh)
        A.clip()
        sets.glow_ellipse(A, (tgt[0], tgt[1] - 0.06 * wh), 0.62 * ww, 0.55 * wh, col, 1.05 * lv)
        sets.glow_ellipse(A, (tgt[0], tgt[1]), 0.30 * ww, 0.28 * wh, col, 0.6 * lv)
        A.restore()
    # her: she steps back, out of the light (smaller, lower, swallowed by the dark)
    ax, ay = a.state["x"], HERS.floor_y(HW)
    s_back = lerp(1.0, 0.82, k_back)
    vis = 1.0 - smoothstep(0.55, 1.0, k_back)
    with f.layer(alpha=1.0) as Lh:
        Lh.save()
        Lh.rectangle(x0, y0, ww, wh)
        Lh.clip()
        # her shadow, big on the wall behind her (the torch is far below her)
        if vis > 0.01:
            Lh.save()
            Lh.translate(ax + 18.0, ay - 40.0)
            Lh.scale(1.45 * s_back, 1.45 * s_back)
            Lh.translate(-ax, -ay)
            a.draw(f, t, Lh, eyes=False, color=None) if False else a.draw(f, t, Lh, eyes=False)
            Lh.restore()
            draw.rgba(Lh, INK, 0.0)
        Lh.restore()
    with f.layer(alpha=0.42 * vis) as Ls:
        Ls.save()
        Ls.rectangle(x0, y0, ww, wh)
        Ls.clip()
        Ls.translate(ax + 18.0, ay - 40.0)
        Ls.scale(1.45 * s_back, 1.45 * s_back)
        Ls.translate(-ax, -ay)
        a.draw(f, t, Ls, eyes=False)
        Ls.restore()
    with f.layer() as Lf:
        Lf.save()
        Lf.rectangle(x0, y0, ww, wh)
        Lf.clip()
        Lf.translate(ax, ay)
        Lf.scale(s_back, s_back)
        Lf.translate(-ax, -ay + 0.10 * HERS.person_h * k_back)
        a.draw(f, t, Lf, eyes=False)
        Lf.restore()
        # the sash bars (the facade's frame for this window), over her and the light
        cx, ym = (x0 + x1) / 2, y0 + wh * 0.5
        for (a0, b0, a1, b1) in ((x0, y0, x0 + 8, y1), (x1 - 8, y0, x1, y1), (x0, y0, x1, y0 + 9),
                                 (x0, y1 - 11, x1, y1), (x0, ym - 6, x1, ym + 5), (cx - 3, y0, cx + 3, y1)):
            draw.rect(Lf, a0, b0, a1, b1)
        draw.fill(Lf, INK)
    if vis > 0.01:
        sk = a.skeleton(t)
        look = cast.her()
        with f.layer() as Le:
            Le.translate(ax, ay)
            Le.scale(s_back, s_back)
            Le.translate(-ax, -ay + 0.10 * HERS.person_h * k_back)
            FIG.draw_eyes(f, sk, look, Le, emit=False, alpha=lv * vis)
    # glare of the torch on the glass
    with f.light(blur=3.0) as A:
        sets.glow(A, (tgt[0] - 0.12 * ww, tgt[1] + 0.18 * wh), 0.16 * ww, col, 0.55 * lv)


def draw_street(f, t, T, w):
    cam = street_cam(t, w)
    f.set_camera(cam)
    a, st = street_cop(ST_DEPTH)
    sets.night_sky(f, t)
    f.set_camera(cam)
    sets.draw_blocks(f, t, HERS_BLOCKS, layer=dict(par=1.0, fog=0.28))
    lit = dict(HERS_LIT)
    lit[HW] = 0.0
    HERS.draw(f, t, lit=lit, shops=(0.0, 0.0), halo=0.9, emit=0.8)
    car = sets.PoliceCar((car_x(t), st.lane_y(CAR_U)), scale=st.depth_scale(CAR_U), facing=1)
    away = smoothstep(10.4, 12.0, t)
    lights = 1.0 - 0.35 * away
    wash = (1.0 - 0.75 * away)
    sets.strobe_wash(f, t, car, (HERS.x0, 1000.0, HERS.x1, HERS.ground_y), k=1.6 * wash)
    draw_her_window(f, t, w)
    lamp = sets.Streetlamp((HERS.x0 + 300.0, HERS.ground_y + 40.0), height=680.0, facing=1)
    srcs = HERS.light_sources(t, lit) + [lamp.light_source()] + car.light_sources(t, lights)
    st.draw(f, t, sources=srcs, lamp_pools=[(lamp.lantern[0], 1.0)], reflections=0.9)
    lamp.draw(f, t)
    car.draw(f, t, lights=lights, wash=1.8 * wash)
    # the cop and his torch
    sk = a.skeleton(t)
    hand = sk.j["hand_R"]
    tg = beam_target(t, w)
    ang = math.degrees(math.atan2(tg[1] - hand[1], tg[0] - hand[0]))
    raise_t, lower_t = 7.15, 9.6
    st.reflect(f, t, lambda c: a.draw(f, t, c, eyes=False), a.state["x"] if False else st.lane_y(COP_U),
               (sk.j["pelvis"][0] - 120, sk.j["head"][1] - 80, sk.j["pelvis"][0] + 120, st.lane_y(COP_U)), strength=0.5)
    with f.layer() as Lc:
        a.draw(f, t, Lc, eyes=False)
        lens = sets.flashlight(Lc, hand, ang, scale=0.55)
    on = 1.0 - smoothstep(lower_t + 0.5, lower_t + 0.8, t)
    if on > 0.01:
        length = math.hypot(tg[0] - lens[0], tg[1] - lens[1])
        sets.flashlight_beam(f, lens, ang, length=length, spread=2.6 if t > raise_t + 0.3 else 9.0, level=1.6 * on, t=t,
                             scale=1.3, dust=0.6, hit=t < raise_t + 0.2 or t > lower_t + 0.3)
    f.haze(sets.PAL.fog_at(0.85), 0.16, y0=3450.0, y1=4700.0, feather=500.0)
    rig = L.Rig(900.0, 18.0, 0.0, 16.0, cam.x, cam.y)
    L.rain(f, t, rig, density=1.1)


# ============================================================================= scene
def render(f, t, T):
    w = _words(T)
    if t < CUT_T:
        draw_apartment(f, t, T, w)
    else:
        draw_street(f, t, T, w)


def motion_blur(t, T):
    if 7.3 < t < 8.2 or 9.8 < t < 10.9:
        return 2
    return 1


def cues(T):
    w = _words(T)
    return [
        Cue(0.15, "door kicked open: wood crack, slam against the wall, hall echo", gain_db=-4, pan=-0.6),
        Cue(0.3, "torch clicks on; heavy boots on floorboards", gain_db=-10, pan=-0.5),
        Cue(0.4, "police siren far below, muffled through the glass, strobe hum", gain_db=-18, dur=5.0),
        Cue(w["police"], "second torch clicks on; radio crackle in the hall", gain_db=-14, pan=-0.7),
        Cue(w["body"], "a boot stops: creak of the bare floor", gain_db=-14),
        Cue(w["blood"], "torch beam sweeps the wall: cloth rustle of a sleeve", gain_db=-18, pan=-0.2),
        Cue(w["woman"], "rain against the bare window, close", gain_db=-12),
        Cue(CUT_T, "outside: rain hiss, siren loop close, idling engine", gain_db=-8, dur=4.0),
        Cue(7.15, "torch raised: click, a cop's grunt", gain_db=-14, pan=-0.3),
        Cue(8.2, "the beam finds her: a sharp string sting", gain_db=-10),
        Cue(w["dreamed"], "she steps back: floorboard creak (inside, far)", gain_db=-20),
        Cue(9.6, "torch clicks off; footsteps away on wet pavement", gain_db=-14, pan=-0.6),
        Cue(10.25, "police car pulls away: engine rev, tyres hiss on the wet street", gain_db=-8, pan=0.5, dur=1.8),
    ]
