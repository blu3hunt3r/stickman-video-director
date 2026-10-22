"""s06 · CROSSING (13.0 s). Red enters the film: she takes the RED coat, runs down the
Vertigo stairwell, crosses the wet street, and the camera cranes up the building opposite
to window 9 (dark).

IN   slash from s05 (0.75 s, centred on 0): the red cut lies across the RED coat on its hook.
A  HER DOOR (-0.375 - 3.30)  HerEntry, her flat dark, cold window light on the wall.
     -0.38-0.30  her hands on the collar; 0.30 lifts it off the hook
     0.45-1.30   turns to us and swings it up over her head: it FLARES (cue 0.62), drops on her
                 shoulders 1.25; arms into the sleeves 1.30-1.55 (L14 "So I did...")
     1.62-2.25   collar up ("watcher" 1.90)
     2.18-2.80   turns and goes to the door; opens it on "never" (2.81): hall light floods in
     3.05-3.30   back to us, into the doorway ("does" 3.17)
B  STAIRWELL (3.30 - 4.72)   straight down the square spiral: dolly-zoom (cam 3.4 -> 1.15 m)
     + roll (-34 -> +38 deg); she bursts out of the landing door and runs down, red on the
     dark treads, the bottom lost in the dark.
C  STREET + CRANE (4.72 - 13.5)  cut on "crossed": the wet street in the rain, the facade
     opposite. She comes up out of the bottom of frame between two dark parked cars, crosses
     (red reflection broken by the rain), between the far cars, up the stoop and in (7.1).
     The camera (rolled +7 deg, unwinding the spiral by 5.8) cranes up from 6.5, past the lit
     windows (30 the crier, 19, 23, the dancer in 4) and stops on window 9, dark, at 12.5.
OUT  window shape (1.0 s, centred on 13.0): window 9 = screen rect (444, 840)-(636, 1080),
     held still from 12.5 to 13.5 (camera = Facade.camera_on(9, fill=0.125)).
"""
import math
from functools import lru_cache

from engine import atmos, draw
from engine.core import W, H, clamp, ease, lerp, hash01, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import RED, SHADOWPLAY as PAL
from engine.timing import Cue
from films.shadowplay import cast, sets
from films.shadowplay.scenes import _lib_s06_s07 as L

try:                                       # the window people of s01-s04 (other animator)
    from films.shadowplay.scenes import _lib_s02_s04 as WL
except Exception:                          # noqa: BLE001
    WL = None

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot
COLD = L.COLD

T_B = 3.30                     # cut: her doorway -> the stairwell
T_C = 4.72                     # cut: the stairwell -> the street ("crossed")
T_END = 12.5                   # the crane lands on window 9 (the shape window starts here)

# =========================================================================== A: her door
ENT = sets.HerEntry((540.0, 1800.0), 1.0)
OX, OY = ENT.o
HOOK = ENT.coat_hook                         # (120, 1200)
HER_X0 = HOOK[0] + 150.0                     # where she stands at the rack
DOOR_X = OX - 30.0                           # where she stops at the door
KNOB = (OX + 120.0, OY - 330.0)
T_OPEN = 2.81                                # "never"


def _door_open(t):
    return sets.door_swing(t, [(T_OPEN - 0.05, 0.0), (T_OPEN + 0.38, 0.62, "out3"), (T_B, 0.70, "inout")])


@lru_cache(maxsize=1)
def _her_a():
    a = Actor(cast.HER, L.her_look(coat=False), x=HER_X0, ground=OY, facing=-1, seed=61)
    a.stand(until=0.40, at=-2.0, idle=0.5)
    a.turn(90.0, dur=0.42, at=0.40, via=90.0)                # to us, swinging the coat over
    a.stand(until=2.18, idle=0.35)
    a.turn(0.0, dur=0.22, at=2.18, via=90.0)                 # to the door
    a.walk(to=DOOR_X, gait="brisk", at=2.30)
    a.stand(until=3.02, idle=0.2)
    a.turn(-90.0, dur=0.24, at=3.02, via=-90.0)              # her back to us, into the doorway
    a.walk(to=DOOR_X + 40.0, gait="brisk", yaw=-80.0, at=3.10)
    a.stand(until=8.0)
    # 1) hands on the collar at the hook, lift it off (reach, until the turn)
    grip = lambda t: L.keys2(t, [(0.28, (HOOK[0] + 4.0, HOOK[1] + 10.0)),
                                 (0.50, (HOOK[0] + 60.0, HOOK[1] - 22.0), "out3")])
    a.reach("L", -2.0, 0.46, grip, fade=0.12, grip=0.9)
    a.reach("R", -2.0, 0.46, lambda t: (grip(t)[0] + 14.0, grip(t)[1] + 4.0), fade=0.12, grip=0.9)
    # 2) facing us: arms swing up and out (the flare), then down to the shoulders
    for side in ("L", "R"):
        a.key("arm.%s.abd" % side, [(0.46, 30.0), (0.82, 128.0, "out3"), (1.02, 118.0), (1.26, 34.0, "inout"),
                                    (1.40, 22.0), (1.58, 10.0, "inout")], fade=0.12)
        a.key("arm.%s.sh" % side, [(0.46, 40.0), (0.82, 12.0, "out3"), (1.02, 16.0), (1.26, 34.0, "inout"),
                                   (1.40, -18.0, "inout"), (1.58, 4.0, "inout")], fade=0.12)
        a.key("arm.%s.elbow" % side, [(0.46, 60.0), (0.82, 14.0, "out3"), (1.02, 20.0), (1.26, 128.0, "inout"),
                                      (1.40, 40.0, "inout"), (1.58, 14.0, "inout")], fade=0.12)
    # 3) collar up: both hands to the neck, flick on "watcher", down
    for side in ("L", "R"):
        a.key("arm.%s.abd" % side, [(1.62, 10.0), (1.80, 30.0, "inout"), (2.02, 34.0), (2.22, 10.0, "inout")],
              fade=0.1)
        a.key("arm.%s.sh" % side, [(1.62, 4.0), (1.80, 36.0, "inout"), (1.90, 44.0, "out3"), (2.02, 40.0),
                                   (2.22, 6.0, "inout")], fade=0.1)
        a.key("arm.%s.elbow" % side, [(1.62, 14.0), (1.80, 142.0, "inout"), (1.90, 150.0, "out3"), (2.02, 146.0),
                                      (2.22, 16.0, "inout")], fade=0.1)
    a.key("head", [(1.70, 0.0), (1.92, -10.0, "out3"), (2.20, 4.0, "inout")], fade=0.15)
    # 4) the knob, then the door swings
    a.reach("R", 2.70, 3.00, KNOB, fade=0.14, grip=0.8)
    return a


def _her_look_a(t):
    if t < 1.47:
        return L.her_look(coat=False)
    flow = 0.85 * math.exp(-(t - 1.47) / 0.35)
    return L.her_look(coat=True, flow=flow)


@lru_cache(maxsize=1)
def _coat():
    a = _her_a()

    def collar(t):
        sk = a.skeleton(t)
        hl, hr = sk.j["hand_L"], sk.j["hand_R"]
        mid = ((hl[0] + hr[0]) / 2.0, (hl[1] + hr[1]) / 2.0 + 4.0)
        hook = (HOOK[0] + 6.0, HOOK[1] + 4.0)
        w = smoothstep(0.26, 0.40, t)
        p = (lerp(hook[0], mid[0], w), lerp(hook[1], mid[1], w))
        if t > 1.20:                                  # on her shoulders: the collar sits at her neck
            nk = sk.j["neck"]
            v = smoothstep(1.20, 1.40, t)
            p = (lerp(p[0], nk[0], v), lerp(p[1], nk[1] + 8.0, v))
        return p

    def spread(t):
        sk = a.skeleton(t)
        hl, hr = sk.j["hand_L"], sk.j["hand_R"]
        s = 0.5 * math.hypot(hl[0] - hr[0], hl[1] - hr[1])
        w = smoothstep(0.26, 0.40, t)
        s = lerp(16.0, max(16.0, s), w)
        if t > 1.20:
            s = lerp(s, 46.0, smoothstep(1.20, 1.40, t))
        return s
    return L.FlyingCoat(collar, spread, length=340.0, t0=-1.0, t1=3.5, seed=6)


def _camera_a(t):
    # on the coat at the rack (the slash crosses it), pan to the door as she goes
    p = L.k_(t, 2.05, 0.95, "inout")
    x = lerp(HOOK[0] + 30.0, DOOR_X + 10.0, p)
    y = lerp(HOOK[1] + 196.0, OY - 400.0, p)
    z = lerp(1.42, 1.22, p) * (1.0 + 0.03 * L.k_(t, 2.9, 0.5, "in"))
    rot = -3.5 * L.k_(t, 2.85, 0.5, "in")
    return Camera(x, y, z, rot).shaken(t, amp=2.0, rot_amp=0.05, freq=0.4, seed=61)


def _shot_a(f, t):
    f.set_camera(_camera_a(t))
    op = _door_open(t)
    hall = 0.55 + 0.45 * L.k_(t, T_OPEN, 0.3, "out")
    ENT.draw(f, t, coat=False, door_open=op, hall=hall, window=1.0)
    _window_rain(f, t)
    a = _her_a()
    sk = a.skeleton(t)
    coat = _coat()
    lk = _her_look_a(t)
    with f.layer() as Lc:
        # the coat: on its hook / lifted (the set's coat, rigid) -> flying cloth -> her costume
        if t < 0.62:
            nodes = coat.nodes(t)
            top, bot = nodes[0], nodes[-1]
            ang = math.degrees(math.atan2(-(bot[0] - top[0]), bot[1] - top[1]))
            al = 1.0 - L.k_(t, 0.52, 0.10, "inout")
            if al > 0.01:
                Lc.push_group()
                sets.red_coat(Lc, (top[0] - 6.0, top[1] - 4.0), 1.0, sway=ang, t=t, hook_too=False)
                Lc.pop_group_to_source()
                Lc.paint_with_alpha(al)
            if t > 0.52:
                coat.draw(Lc, t, alpha=L.k_(t, 0.52, 0.10, "inout"))
        elif t < 1.62:
            coat.draw(Lc, t, alpha=1.0 - L.k_(t, 1.47, 0.15, "inout"))
        # her (the door leaf and frame are already drawn: she steps into the bright doorway)
        if t < 3.05:
            a.draw(f, t, Lc, look=lk)
        else:
            # into the doorway: smaller with distance, swallowed by the glare
            k = 1.0 - 0.10 * L.k_(t, 3.05, 0.3, "in")
            Lc.save()
            ft = (sk.j["pelvis"][0], OY)
            Lc.translate(ft[0], ft[1] - 140.0 * (1.0 - k))
            Lc.scale(k, k)
            Lc.translate(-ft[0], -ft[1])
            a.draw(None, t, Lc, look=lk, eyes=False)
            Lc.restore()
    # the cold window light rims her left edge, the hall light her right as the door opens
    with f.light(blur=2.0) as A:
        L.rim(A, sk, L.plain(lk), None, COLD, 0.22, (7.0, 2.0))
        if op > 0.02:
            L.rim(A, sk, L.plain(lk), None, mix_hot(), 0.5 * op, (-6.0, 1.0))


def mix_hot():
    return sets.mix(AMBER, HOT, 0.5)


def _window_rain(f, t):
    """Rain running down her window throws wavering dark streaks into the cold light pane
    on the wall (the set draws the pane; this darkens trickles inside it)."""
    s = ENT.s
    ox, oy = OX, OY
    with f.layer(blur=1.5, alpha=0.55) as Lr:
        Lr.save()
        for (a0, a1) in ((0.0, 0.47), (0.53, 1.0)):
            xa, xb = ox - 1100 * s + 380 * s * a0, ox - 1100 * s + 380 * s * a1
            draw.poly(Lr, [(xa, oy - 1250 * s), (xb, oy - 1250 * s), (xb + 520 * s, oy - 260 * s),
                           (xa + 520 * s, oy - 260 * s)])
        Lr.clip()
        for k in range(22):
            u = hash01(66, k, 1)
            sp = 0.25 + 0.5 * hash01(66, k, 2)
            ph = (t * sp + hash01(66, k, 3)) % 1.0
            y0 = oy - 1250 * s + ph * 990 * s
            ln = (60 + 160 * hash01(66, k, 4)) * s
            pts = []
            for j in range(7):
                v = j / 6.0
                y = y0 - v * ln
                x = ox - 1100 * s + 380 * s * u + (y - (oy - 1250 * s)) * 520.0 / 990.0
                x += 4.0 * s * math.sin(y * 0.05 + k)
                pts.append((x, y))
            Lr.new_path()
            Lr.move_to(*pts[0])
            for p in pts[1:]:
                Lr.line_to(*p)
            Lr.set_line_width(3.0 * s)
            Lr.set_source_rgba(INK[0], INK[1], INK[2], 0.6)
            Lr.stroke()
            draw.circle(Lr, pts[0], 4.0 * s)
            draw.fill(Lr, INK, 0.6)
        Lr.restore()


# =========================================================================== B: the stairwell
SW = sets.Stairwell((540.0, 960.0), 1.0, floors=7, stretch=1.2, seed=6)
U0, U1 = 0.004, 0.047                         # her walking-line progress over the shot


def _b_v(t):
    return clamp((t - T_B) / (T_C - T_B))


def _b_cam(t):
    v = _b_v(t)
    cam_h, F = SW.vertigo(ease("inout", v), cam0=3.4, cam1=1.15, ref=2, focal0=600.0)
    roll = lerp(-34.0, 38.0, ease("inout", v))
    return cam_h, F, roll


def _b_her_u(t):
    return lerp(U0, U1, L.k_(t, T_B - 0.05, T_C - T_B + 0.05, "inout") * 0.82 + 0.18 * clamp((t - T_B) / (T_C - T_B)))


def _shot_b(f, t):
    f.set_camera(Camera(540.0, 960.0, 1.0))
    cam_h, F, roll = _b_cam(t)
    u = _b_her_u(t)
    pp = SW.path_point(u, cam_h, F, roll)
    per = 17.0 * 7.0                               # walking line (m) over the whole well
    dist = u * per
    phase = dist / 0.55 * math.pi
    du = (_b_her_u(t + 0.02) - _b_her_u(t - 0.02)) / 0.04
    flare = clamp(du * per / 3.0)

    def her(f_, t_):
        with f_.layer() as Lb:
            L.top_figure(Lb, pp["p"], pp["ppm"], pp["heading"], phase, coat=RED, flare=flare, rail=1)
    SW.draw(f, t, cam_h=cam_h, focal=F, roll=roll, hooks={pp["floor"]: her}, bottom=0.25, flicker=0.35)


# =========================================================================== C: the street, the crane
FAC = sets.Facade(origin=(540.0, 3940.0), scale=1.0)
BLOCKS = sets.neighbours(FAC)
SKY = sets.Skyline(x0=-1600.0, x1=2800.0, base_y=420.0, seed=6, scale=0.9, height=(330.0, 1000.0), lit=0.04)
ST = sets.Street(FAC.ground_y, depth=1000.0, seed=7)
LAMP = sets.Streetlamp((150.0, FAC.ground_y + 40.0), height=680.0, facing=1)
W9 = FAC.window_rect(9)
CAM_END = FAC.camera_on(9, fill=0.125)        # window 9 -> (444, 840)-(636, 1080)
CARS_FAR = [sets.Car((150.0, ST.lane_y(0.10)), scale=ST.depth_scale(0.10), facing=1, seed=3),
            sets.Car((1010.0, ST.lane_y(0.10)), scale=ST.depth_scale(0.10), facing=-1, seed=4)]
CARS_NEAR = [sets.Car((-60.0, ST.lane_y(0.97)), scale=ST.depth_scale(0.97), facing=1, seed=5),
             sets.Car((960.0, ST.lane_y(0.97)), scale=ST.depth_scale(0.97), facing=-1, seed=8)]
PERSON = 230.0                                # world px of an adult at the far curb
T_IN = 7.10                                   # she is through the door


def _lit():
    return dict(sets.NIGHT)


def _path_c(t):
    """Her feet (world) and depth fraction u along the crossing."""
    pts = [(4.60, (395.0, ST.near_y + 120.0)), (6.28, (530.0, ST.road_y + 6.0), "inout"),
           (6.52, (540.0, FAC.ground_y + 26.0), "linear"), (6.86, (540.0, FAC.stoop_top()[1]), "out"),
           (7.30, (546.0, FAC.stoop_top()[1] - 6.0), "inout")]
    p = L.keys2(t, pts)
    u = clamp((p[1] - ST.road_y) / (ST.near_y - ST.road_y), 0.0, 1.2)
    return p, u


def _her_scale(u, y):
    if y < FAC.ground_y + 1:
        return PERSON / cast.HER.height
    return ST.depth_scale(min(u, 1.0), near_scale=1.6) * (1.0 + 0.25 * max(0.0, u - 1.0)) * PERSON / cast.HER.height


@lru_cache(maxsize=1)
def _her_c():
    a = Actor(cast.HER, L.her_look(), x=0.0, ground=0.0, facing=-64.0, seed=63)
    a.walk(to=9000.0, gait="brisk", yaw=-64.0, at=3.5)
    a.key("head", [(3.5, 6.0), (30.0, 6.0)])
    return a


def _her_c_draw(f, t, color=None, ctx=None, refl=False):
    a = _her_c()
    sk = a.skeleton(t)
    p, u = _path_c(t)
    k = _her_scale(u, p[1])
    x_c = sk.j["pelvis"][0]
    M = L.place_matrix(p, k, x_c, 0.0)
    return sk, M


def _camera_c(t):
    # follow the crossing (rolled, unwinding the stairwell), then crane up to window 9
    f0 = L.k_(t, T_C, 1.6, "out")
    x0 = lerp(470.0, 520.0, f0)
    y0 = lerp(4470.0, 4330.0, f0)
    z0 = lerp(0.98, 0.90, f0)
    c = L.k_(t, 6.45, T_END - 6.45, "inout")
    x = lerp(x0, CAM_END.x, c)
    y = lerp(y0, CAM_END.y, c)
    z = math.exp(lerp(math.log(z0), math.log(CAM_END.zoom), c))
    rot = 7.0 * (1.0 - L.k_(t, T_C, 1.1, "out"))
    if t >= T_END:
        return Camera(CAM_END.x, CAM_END.y, CAM_END.zoom, 0.0)
    cam = Camera(x, y, z, rot)
    # a breath of handheld only while she crosses
    sh = 1.0 - L.k_(t, 6.0, 1.0, "inout")
    if sh > 0:
        cam = cam.shaken(t, amp=3.0 * sh, rot_amp=0.08 * sh, freq=0.5, seed=63)
    return cam


def _interiors():
    out = {}
    if WL is None:
        return out
    try:
        out[4] = lambda c, w: WL.draw_dancer(c, w, (7.4, 8.2))
        out[30] = lambda c, w: WL.draw_crier(c, w, (-10.0, -9.6))
        out[12] = lambda c, w: WL.draw_cat_lady(c, w, (-10.0, -9.5, -9.0))
    except Exception:                       # noqa: BLE001
        return {}
    return out


def _shot_c(f, t):
    cam = _camera_c(t)
    f.set_camera(cam)
    lit = _lit()
    vr = cam.view_rect(60)
    if vr[1] < FAC.roof_y + 200:
        sets.night_sky(f, t, glow_y=FAC.top_y + 200)
        SKY.draw(f, t, layer=dict(par=0.55, fog=0.55))
    sets.draw_blocks(f, t, BLOCKS, layer=dict(par=1.0, fog=0.25))
    ent = 1.0 + 0.6 * L.env(t, 6.80, 6.95, 7.05, 7.40)        # the lobby door opens for her
    FAC.draw(f, t, lit=lit, interiors=_interiors(), curtains={9: "sheet"}, emit=0.9, entrance=ent)
    srcs = FAC.light_sources(t, lit, entrance=ent) + [LAMP.light_source()]
    if vr[3] > FAC.ground_y - 40:
        ST.draw(f, t, sources=srcs, lamp_pools=[(LAMP.lantern[0], 1.0)], reflections=0.9)
    LAMP.draw(f, t)
    for c in CARS_FAR:
        c.draw(f, t, headlights=0.0)
    # her, with her red reflection broken in the wet road
    if t < T_IN + 0.05 and vr[3] > FAC.ground_y - 400:
        a = _her_c()
        sk, M = _her_c_draw(f, t)
        p, u = _path_c(t)
        lk = L.her_look()
        al = 1.0 - L.k_(t, 6.92, 0.18, "in")
        on_road = p[1] > ST.road_y
        if on_road:
            hh = cast.HER.height * M.xx
            bx = (p[0] - 0.45 * hh, p[1] - 1.05 * hh, p[0] + 0.45 * hh, p[1])
            ST.reflect(f, t, lambda c: L.draw_sk(c, sk, lk, M), p[1], bx, strength=0.6 * al, seed=6)
        with f.group(alpha=al) as Lg:
            L.draw_sk(Lg, sk, lk, M)
        L.occlude(f, 1.0, sk, lk, M)
        with f.light(blur=2.5) as A:
            L.rim(A, sk, L.plain(lk), M, AMBER, 0.35 * al, (5.0, 4.0))
    for c in CARS_NEAR:
        c.draw(f, t, headlights=0.0)
    f.haze(PAL.fog_at(0.85), 0.07, y0=3300, y1=5200, feather=500)
    atmos.rain(f, density=1.25, angle=8.0, wind=0.15, seed=6)


# =========================================================================== render
def render(f, t, T):
    if t < T_B:
        _shot_a(f, t)
    elif t < T_C:
        _shot_b(f, t)
    else:
        _shot_c(f, t)


def motion_blur(t, T):
    return 1


def cues(T):
    return [
        Cue(-0.30, "cloth: her hand closes on the coat collar, the hook creaks", -14, pan=-0.2),
        Cue(0.62, "the coat FLARES: a big heavy whoosh of cloth over her head", -4, pan=-0.1, dur=0.6),
        Cue(1.30, "coat lands on her shoulders, arms into sleeves (cloth rustle)", -10, dur=0.3),
        Cue(1.90, "collar flicked up (sharp cloth snap)", -12),
        Cue(2.30, "three quick heel steps on the boards", -12, pan=0.3, dur=0.5),
        Cue(T_OPEN, "door: latch, the door swings open; hallway hum rises", -6, pan=0.35, dur=0.5),
        Cue(T_B, "stairwell: heels racing down the spiral stairs, echoing up the well", -6, dur=1.4),
        Cue(T_B, "score: spiralling Vertigo arpeggio (stairwell)", -8, dur=1.42),
        Cue(T_C, "rain swells: outside, the wet street, rain drumming on parked cars", -4, dur=8.8),
        Cue(4.85, "her heels splash across the wet street", -10, pan=-0.1, dur=1.6),
        Cue(6.90, "the lobby door opens and thuds shut behind her", -14, pan=0.05),
        Cue(7.20, "crane up: rain hiss thins, a radio far up, the crier's sobs (window 30) pass", -16, dur=5.3),
    ]
