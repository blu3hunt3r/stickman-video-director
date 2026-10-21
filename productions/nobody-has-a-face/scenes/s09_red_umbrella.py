"""S09 - The Red Umbrella (9.333 s).

"One witness remembered something. Not a face. A color. In a sea of umbrellas... one was red."

Shot plan (scene-relative seconds)
  A 0.00-3.30  IN: the amber interrogation bulb (props.bulb) centred on screen, flooding the
               frame (hard cut from S08's amber skylight at the same spot); pull back + tilt
               down its cone: the faceless witness seated at the table (front view), the
               detective standing in shadow at the right. The witness's trembling hand rises
               to the head ("remembered something").
  B 3.30-5.62  "Not a face": the hand drops, the head shakes no. "A color": the bulb stutters;
               in the dark frames the memory flashes inside the hollow head; the camera pushes
               into the head ring, which opens like an iris onto the memory.
  C 5.62-9.333 memory: top-down slow-motion river of white umbrellas on a crosswalk
               (sets.crowd_top slowmo, all walking down). On "red" ONE umbrella - already walking
               AGAINST the flow - blooms crimson (amount 0->1 in 0.25 s). Push in and roll into
               one panel of its canopy. OUT: crimson fills the whole frame.
"""
import math

from engine import *
from scenes import _lib_s08_s10 as L

# ----------------------------------------------------------------------------- the room (world)
ANCHOR = (540.0, 140.0)
CORD = 350.0
BULB = (540.0, ANCHOR[1] + CORD + 46.0)         # bulb centre at zero swing
FLOOR = 1279.0
TABLE_Y = 1080.0
TABLE_X0, TABLE_X1 = 250.0, 830.0
WALL_BASE = 1196.0
GLASS = (92.0, 404.0, 300.0, 470.0)             # one-way mirror on the back wall (x, y, w, h)
WIT_X, WIT_HIP, WIT_S = 540.0, 1128.0, 1.35
PANEL_BOTTOM = 1345.0
DET_X, DET_S = 872.0, 1.35

ROOM_CAM = Track([(0.0, (540.0, BULB[1], 5.4)), (0.30, (540.0, BULB[1] + 4, 5.25), "out"),
                  (2.05, (548.0, 915.0, 1.32), "inout3"), (3.30, (546.0, 930.0, 1.45), "inout"),
                  (4.85, (540.0, 945.0, 1.95), "inout")])
T_IRIS0, T_IRIS1 = 4.85, 5.62

# ----------------------------------------------------------------------------- the memory
MEM = dict(area=(-200.0, -300.0, 1280.0, 2220.0), n=117, seed=43, speed=120.0, R=(46.0, 60.0),
           two_way=False, slowmo=0.4)
RED_I = 103
MEM_T_OFF = 35.5                                 # crowd clock offset: THE umbrella centred on "red"


def _swing(t):
    return 3.2 * math.sin(2 * math.pi * t / 3.4 + 0.6)


def _bulb_c(t):
    a = math.radians(90 - _swing(t))
    return (ANCHOR[0] + math.cos(a) * (CORD + 46), ANCHOR[1] + math.sin(a) * (CORD + 46))


def _bulb_on(t, T):
    tc = T.at("color")
    for a, b, v in ((tc - 0.01, tc + 0.05, 0.06), (tc + 0.09, tc + 0.12, 0.35), (tc + 0.16, tc + 0.29, 0.04),
                    (tc + 0.33, tc + 0.36, 0.5)):
        if a <= t < b:
            return v
    return 0.94 + 0.06 * flicker(t, 5, rate=11, depth=0.5)


def _dark(t, T):
    """1 while the bulb is out (memory flashes inside the head)."""
    return 1.0 if _bulb_on(t, T) < 0.2 else 0.0


# ----------------------------------------------------------------------------- figures
def _witness(t, T):
    # seated (rig.sit) behind the table, front view; the table's front panel hides the legs
    p = rig.sit(WIT_X, WIT_HIP, facing=0, s=WIT_S, la=8, ra=8)
    p = rig.breathe(p, t, amt=0.8, seed=3)
    # head: listens, then shakes "no" on "Not a face" (front view: side-to-side tilt)
    t_no = T.at("not")
    sh = 0.0
    if t_no - 0.05 < t < t_no + 0.78:
        env = math.sin(math.pi * inv_lerp(t_no - 0.05, t_no + 0.78, t))
        sh = 11.0 * env * math.sin(2 * math.pi * 4.3 * (t - t_no + 0.05))
    think = 6.0 * ease("inout", inv_lerp(2.2, 2.8, t)) * (1 - ease("inout", inv_lerp(3.1, 3.4, t)))
    p = p.copy(head=p.head + sh - think)
    # hands rest on the table edge; the RIGHT hand (screen-left) rises trembling to the temple
    J = rig.solve(p)
    rest_r = (WIT_X - 70.0, TABLE_Y - 5.0)
    rest_l = (WIT_X + 72.0, TABLE_Y - 5.0)
    p = rig.reach(p, "l", rest_l)
    up = ease("out3", inv_lerp(1.62, 2.32, t)) * (1 - ease("inout", inv_lerp(3.22, 3.58, t)))
    antic = 0.25 * math.sin(math.pi * inv_lerp(1.38, 1.62, t))
    temple = (J["head"][0] - J["head_r"] * 1.05, J["head"][1] + J["head_r"] * 0.15)
    tr = 6.0 * up + 2.0
    trem = (tr * fbm1(t * 9.0, 41) + 1.5 * noise1(t * 23, 43), tr * fbm1(t * 8.0, 47))
    target = lerp((rest_r[0] - 12 * antic, rest_r[1] + 6 * antic), temple, up)
    target = (target[0] + trem[0], target[1] + trem[1])
    p = rig.reach(p, "r", target)
    drop = ease("out", inv_lerp(3.58, 3.75, t)) * (1 - ease("in", inv_lerp(3.75, 3.95, t)))
    return p.copy(re=p.re + 6 * drop)


def _detective(t, T):
    p = rig.stand(DET_X, FLOOR, facing=-1, s=DET_S, la=4, ra=-8, le=12, re=10)
    lean = 5.0 * ease("inout", inv_lerp(0.9, 2.0, t)) - 2.0 * ease("inout", inv_lerp(3.4, 4.2, t))
    p = p.copy(lean=lean, head=3.0 * ease("inout", inv_lerp(1.0, 2.0, t)))
    return rig.breathe(p, t, amt=1.0, seed=17)


# ----------------------------------------------------------------------------- room drawing
def _table(f):
    """Interrogation table seen from the front: a solid front panel hides the witness's legs."""
    panel = [(TABLE_X0, TABLE_Y), (TABLE_X1, TABLE_Y), (TABLE_X1, PANEL_BOTTOM), (TABLE_X0, PANEL_BOTTOM)]
    draw.fill(f, panel, BLACK, 1.0)
    draw.line(f, (TABLE_X0 - 26, TABLE_Y - 8), (TABLE_X1 + 26, TABLE_Y - 8), 4.0, WHITE, 0.95)
    draw.line(f, (TABLE_X0 - 26, TABLE_Y - 8), (TABLE_X0, TABLE_Y), 2.6, WHITE, 0.8)
    draw.line(f, (TABLE_X1 + 26, TABLE_Y - 8), (TABLE_X1, TABLE_Y), 2.6, WHITE, 0.8)
    draw.stroke(f, panel, 3.0, WHITE, 0.9, closed=True)
    draw.line(f, (TABLE_X0 + 20, TABLE_Y + 34), (TABLE_X1 - 20, TABLE_Y + 34), 1.6, WHITE, 0.4)


def _room(f, t, T):
    draw.line(f, (-400.0, WALL_BASE), (1480.0, WALL_BASE), 2.4, WHITE, 0.6)
    gx, gy, gw, gh = GLASS
    draw.rect(f, gx, gy, gw, gh, 3.0, WHITE, 0.55)
    draw.rect(f, gx + 12, gy + 12, gw - 24, gh - 24, 1.4, WHITE, 0.25)
    draw.line(f, (gx + 50, gy + 60), (gx + 170, gy + 190), 1.6, WHITE, 0.22)
    draw.line(f, (gx + 50, gy + 110), (gx + 120, gy + 180), 1.2, WHITE, 0.16)


def _memory(f, t, T, cam, alpha=1.0, red_k=0.0):
    """Top-down slow-motion river of umbrellas on a crosswalk (drawn with `cam`)."""
    tm = t + MEM_T_OFF
    with f.camera(cam):
        with f.alpha(alpha):
            x0, y0, x1, y1 = L.view_bounds(cam, 60)
            ctx = f.ctx
            ctx.new_path()
            for k in range(-4, 14):
                bx = -210.0 + k * 140.0
                if bx + 76 < x0 or bx > x1:
                    continue
                ctx.rectangle(bx, max(y0, -600.0), 76.0, min(y1, 2600.0) - max(y0, -600.0))
            ctx.set_line_width(f.lw(1.6))
            ctx.set_source_rgba(1, 1, 1, 0.1)
            ctx.stroke()
            L.ripples_top(f, t, (x0, y0, x1, y1), rate=0.16, seed=19, alpha=0.32, slowmo=0.4)
            sets.crowd_top(f, tm, area=MEM["area"], n=MEM["n"], seed=MEM["seed"], speed=MEM["speed"],
                           R=MEM["R"], two_way=MEM["two_way"], slowmo=MEM["slowmo"], alpha=0.86,
                           red=dict(index=RED_I, reverse=True, amount=red_k))
            if red_k > 0:
                x, y, r, rot = _red_state(t)
                props.umbrella_top(f, (x, y), r * 1.04, rot, CRIMSON, alpha=red_k)
    # rain thins away as the camera dives into the canopy: the cut frame is pure crimson
    L.rain_top_vp(f, t, n=110, seed=9, alpha=0.34 * alpha * (1 - ease("inout", inv_lerp(8.75, 9.15, t))),
                  slow=0.35)


def _red_state(t):
    return L.crowd_pos(RED_I, t + MEM_T_OFF, MEM["area"], MEM["n"], MEM["seed"], MEM["speed"], MEM["R"],
                       MEM["two_way"], dict(index=RED_I, reverse=True), MEM["slowmo"])


def _mem_base(t):
    """The memory's own camera: settles from a slight roll/zoom into the river."""
    k0 = ease("out3", inv_lerp(T_IRIS0, 7.5, t))
    return Camera(540.0, lerp(1000.0, 975.0, k0), lerp(1.22, 1.0, k0), lerp(-7.0, 0.0, k0))


def _mem_cam(t, T):
    tr = T.at("red")
    base = _mem_base(t)
    if t < tr + 0.2:
        return base.moved(dzoom=1.0 + 0.035 * pulse(t, tr, 0.03, 0.4))
    # push in on THE red umbrella and roll into one panel of its canopy
    x, y, r, rot = _red_state(t)
    R = r * 1.04
    phi0 = _red_state(tr + 0.2)[3] + 22.5
    k = ease("inout3", inv_lerp(tr + 0.2, 9.22, t))
    m = round((90.0 - phi0) / 45.0)
    phi = rot + 22.5 + 45.0 * m                      # panel bisector closest to "down"
    off = 0.56 * R * ease("inout", inv_lerp(tr + 0.45, 9.22, t))
    target = (x + off * math.cos(math.radians(phi)), y + off * math.sin(math.radians(phi)))
    z = L.zlerp(1.0 * (1 + 0.035 * pulse(t, tr, 0.03, 0.4)), 76.0, k)
    rot_c = lerp(0.0, 90.0 - phi, ease("inout", inv_lerp(tr + 0.35, 9.22, t)))
    start = base.to_screen((x, y))
    sp = lerp(start, (540.0, 960.0), ease("inout", inv_lerp(tr + 0.2, 8.6, t)))
    return L.cam_anchor(target, sp, z, rot_c)


# ----------------------------------------------------------------------------- shots
def _room_shot(f, t, T):
    x, y, z = ROOM_CAM(t)
    wit = _witness(t, T)
    Jw = rig.solve(wit)
    head, hr = Jw["head"], Jw["head_r"]
    if t > T_IRIS0:
        k = ease("in3", inv_lerp(T_IRIS0, T_IRIS1, t))
        z = L.zlerp(1.95, 34.0, k)
        kx = ease("inout", inv_lerp(T_IRIS0, T_IRIS0 + 0.45, t))
        x, y = lerp(x, head[0], kx), lerp(y, head[1], kx)
    cam = Camera(x, y, z)
    if 0.3 < t < T_IRIS0:
        cam = cam.shaken(t, amp=2.2, rot_amp=0.12, freq=0.6, seed=29)
    f.set_camera(cam)
    on = _bulb_on(t, T)
    room = 1.0 - ease("in", inv_lerp(4.98, 5.42, t))     # the room goes dark around the iris
    bc = _bulb_c(t)
    bdir = 90 - _swing(t)
    lights = [Light.cone(bc, bdir, 58, 980, intensity=on * room), Light.radial(bc, 280, intensity=0.8 * on * room),
              Light.radial((DET_X - 40, 900), 260, intensity=0.18 * on * room)]
    haze = ease("inout", inv_lerp(0.25, 1.4, t)) * room
    fx.light_cone(f, bc, bdir, 54, 900, AMBER, 0.1 * on * haze, glow=0.3 * on * haze)
    with f.lit(lights, ambient=(0.1 * on + 0.02) * room, soften=4.0):
        _room(f, t, T)
        fx.dust(f, t, (330.0, 600.0, 750.0, 1070.0), n=60, seed=7, alpha=0.5 * haze, size=2.0)
        rig.draw_figure(f, _detective(t, T), alpha=0.85)
        rig.draw_figure(f, wit)
        _table(f)
    with L.glow_scaled(f, room * lerp(0.62, 1.0, ease("inout", inv_lerp(0.1, 1.2, t)))):
        props.bulb(f, ANCHOR, CORD, swing=_swing(t), on=on, t=t, glow_r=230)
    # S08 -> S09: the amber flood around the bulb (same spot as S08's skylight) settles
    fl = 1 - ease("out", inv_lerp(0.0, 0.6, t))
    if fl > 0:
        draw.glow_dot(f, bc, 300.0, AMBER, 0.3 * fl, core=False)
    # memory inside the hollow head: flashes while the bulb is out, then the iris opens
    mem_a = max(0.85 * _dark(t, T), ease("inout", inv_lerp(4.72, 5.12, t)))
    if mem_a > 0 and t > 3.5:
        inner = hr - 0.5 * rig.FIG_LW * WIT_S ** 0.5 * cam.zoom ** (0.35 - 1)
        with L.fit_clip(f, head, inner):
            draw.circle(f, head, inner + 2, 1, BLACK, 1.0, fill_it=True, glow=1.0)
            # the memory is anchored to the head ring's centre and grows into the memory shot's
            # own camera exactly at T_IRIS1 (continuous handoff)
            mb = _mem_base(t)
            sf = lerp(0.36, 1.0, ease("inout", inv_lerp(T_IRIS0, T_IRIS1, t)))
            mc = L.cam_anchor((mb.x, mb.y), cam.to_screen(head), mb.zoom * sf, mb.rot)
            _memory(f, t, T, mc, alpha=mem_a)
        # the ring itself stays crisp on top of the memory
        w = rig.FIG_LW * WIT_S ** 0.5
        draw.circle(f, head, hr, w, WHITE, 1.0)


def _memory_shot(f, t, T):
    cam = _mem_cam(t, T)
    f.set_camera(cam)
    tr = T.at("red")
    red_k = ease("out3", inv_lerp(tr, tr + 0.25, t))
    # once the canopy fills the frame its emissive halo would wash crimson out to pink
    gk = 1.0 - 0.9 * ease("inout", inv_lerp(1.6, 9.0, cam.zoom))
    with L.glow_scaled(f, gk):
        _memory(f, t, T, cam, alpha=1.0, red_k=red_k)
    if red_k > 0:
        x, y, r, _ = _red_state(t)
        draw.glow_dot(f, (x, y), r * 3.2, CRIMSON, 0.55 * pulse(t, tr, 0.04, 0.5), core=False)


def render(f, t, T):
    if t < T_IRIS1:
        _room_shot(f, t, T)
    else:
        _memory_shot(f, t, T)


def cues(T):
    tc, tr = T.at("color"), T.at("red")
    c = [Cue(0.0, "bulb_hum", gain_db=-15, dur=T_IRIS1),
         Cue(0.95, "bulb_creak", gain_db=-19, pan=0.1),
         Cue(1.58, "chair_creak", gain_db=-14, pan=-0.05),
         Cue(3.22, "chair_creak", gain_db=-18, pan=-0.05),
         Cue(tc - 0.01, "bulb_flicker", gain_db=-7),
         Cue(tc + 0.15, "bulb_flicker", gain_db=-9),
         Cue(tc + 0.32, "bulb_flicker", gain_db=-11),
         Cue(T_IRIS0 - 0.1, "reverse_swell", gain_db=-9, dur=T_IRIS1 - T_IRIS0 + 0.1),
         Cue(T_IRIS1 - 0.02, "whoosh", gain_db=-14, size=0.4),
         Cue(tr, "stinger", gain_db=-3),
         Cue(tr, "sub_drop", gain_db=-6),
         Cue(tr + 0.25, "riser", gain_db=-16, dur=T.duration - tr - 0.25)]
    return c


def motion_blur(t, T):
    if 8.85 < t < 9.2:
        return 3
    return 1
