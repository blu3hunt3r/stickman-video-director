"""s01 · THE LINE: a red Bass line on black paper. 31 paper men hang from it and drop off one
by one; the line curls into a ring - a helmet port - and the port opens on the diver sinking
through dark water, eyes glowing. The camera pulls back, then rises with his bubbles and the
red hose toward the evening surface (scroll up into s02).

Beats (scene-local s, synced to T):
  0.12-1.0   the red line draws itself in from the left edge at y 960 (out3)
  [men]      31 paper tick-figures pop on under it like clothes pegs (left -> right)
  [down]..[Meridian]  they let go one after another and fall out of the frame; the last is the
             captain (peaked cap), on [Meridian]
  4.25-5.05  the line curls into a ring, centre (540, 900), r 230 (the helmet port)
  5.12-5.75  inside the ring the black irises open on live water: the port glass, marine snow
  [later]    the eyes open behind the glass
  6.0-8.6    pull back (zoom ~9 -> 0.62): the ring IS his faceplate; he sinks, upright, eyes
             glowing, the red hose rising out of frame, bubbles streaming from the exhaust
  8.3-10.75  the camera tilts up and follows the bubbles; he sinks out of the bottom; the water
             lightens toward the surface. OUT: still rising ~300 px/s (screen), hose and
             bubbles vertical through x ~560.
"""
import math

from engine import atmos, bass, costume, draw
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.motion import Actor, dangle
from engine.palette import PAPER, RED
from engine.timing import Cue
from films.salvage import cast
from films.salvage.scenes import _lib_s01_s03_s16 as LIB
from films.salvage.sets_common import PAL, water_at
from films.salvage.sets_surface import underwater

INK = PAL.ink
LINE_Y = 960.0
LINE_W = 14.0
RING_C = (540.0, 900.0)
RING_R = 230.0
LINE_L = 2.0 * math.pi * RING_R          # the band closes into a ring of radius RING_R
SEED = 7
CREW = LIB.crew_layout(31)

T_CURL0, T_CURL1 = 4.25, 5.05             # line -> ring
T_IRIS0, T_IRIS1 = 5.12, 5.75             # the black opens inside the ring
T_LIVE = 5.10                             # live world starts being drawn
T_PULL0, T_PULL1 = 6.0, 8.6               # pull back
T_RISE0 = 8.3                             # the camera starts to rise
V_RISE = 370.0                            # world px/s once rising (zoom ~0.8 -> ~300 px/s screen)
Z1, Z2 = 0.62, 0.82                       # zoom after the pull back; gentle push-in while rising


# ============================================================================= timing
def _beats(T):
    try:
        men, down, mer = T.at("men"), T.at("down"), T.at("Meridian")
        later = T.at("later")
    except KeyError:
        men, down, mer, later = 1.825, 2.521, 3.299, 6.136
    return dict(men=men, down=down, mer=mer, later=later)


# ============================================================================= the diver
Y0 = 3000.0                               # pelvis depth at t = 0 (dark teal water)


def _sink_y(t):
    """Pelvis depth: a slow steady sink that gets heavier after 'I went down'."""
    extra = LIB.integ(lambda s: 190.0 * smoothstep(7.8, 9.2, s), 7.5, max(t, 7.5), 24) if t > 7.5 else 0.0
    return Y0 + 58.0 * t + extra


def _path(t):
    return (7.0 * math.sin(0.42 * t + 0.6) + 3.0 * noise1(t * 0.3, 4), _sink_y(t))


def _pose(t, u):
    p = dangle(DIVER, t, 90.0)
    br = math.sin(2 * math.pi * t / 3.7)
    for s, sg in (("L", 1.0), ("R", -1.0)):
        a = p.arms[s]
        a["sh"] = 6.0 * sg + 4.0 * noise1(t * 0.35, 11 + sg)
        a["abd"] = 22.0 + 5.0 * noise1(t * 0.3, 21 + sg) + 2.0 * br
        a["elbow"] = 26.0 + 6.0 * noise1(t * 0.28, 31 + sg)
        a["wrist"] = 8.0
        a["grip"] = 0.15
    for s, ph in (("L", 0.0), ("R", 1.9)):
        p.legs[s] = dict(hip=7 + 5 * math.sin(t * 0.9 + ph), abd=6.0, knee=14 + 7 * math.sin(t * 0.9 + ph + 0.7),
                         ankle=-10, toe=0)
    p.pitch = 1.5 * noise1(t * 0.25, 41)
    p.spine = [0.8 * br, 0.0, -0.6 * br]
    p.head = 3.0 + 2.0 * noise1(t * 0.2, 51)
    p.head_roll = 1.5 * noise1(t * 0.22, 61)
    # eyes: closed behind the dark glass, open on 'later', one slow blink
    op = smoothstep(5.98, 6.3, t)
    bl = (t - 7.35) / 0.16
    if 0.0 < bl < 1.0:
        op *= abs(1.0 - 2.0 * bl) ** 0.8
    p.eyes = dict(open=op, glow=1.0, look=0.0)
    return p


DIVER = Actor(cast.DIVER, cast.diver(), x=0.0, ground=1e6, facing=90, seed=5, name="diver")
DIVER.free(14.0, _path, _pose, at=-1.5)

_PORT = LIB.Sampled(lambda t: LIB.port_center(DIVER.skeleton(t))[0], -1.5, 11.5, 48)
_VALVE = LIB.Sampled(lambda t: LIB.helmet_valve(DIVER.skeleton(t)), -1.5, 11.5, 48)
_INLET = LIB.Sampled(lambda t: costume.helmet_inlet(DIVER.skeleton(t)), -1.5, 11.5, 120)
_VR = LIB.port_center(DIVER.skeleton(6.0))[1]
Z0 = (RING_R - LINE_W / 2.0) / _VR        # the ring's inner edge sits on the port glass

HOSE_UP = 3400.0
EXHALES = (6.42, 8.02, 9.38)             # exhale bursts (the second on 'went down')


def _hose_a(t):
    x, y = _INLET(t)
    return (x + 14.0 + 22.0 * math.sin(0.23 * t), y - HOSE_UP)


HOSE = LIB.hose_rope(_hose_a, _INLET, HOSE_UP * 1.003 + 10.0, n=48, t0=-1.5, t1=11.5,
                     current=lambda t, x, y: (9.0 + 6.0 * math.sin(0.4 * t + y / 700.0), 0.0))


# ============================================================================= camera
def _zoom(t):
    if t <= T_PULL0:
        return Z0
    k = ease("inout", (t - T_PULL0) / (T_PULL1 - T_PULL0))
    z = math.exp(lerp(math.log(Z0), math.log(Z1), k))
    return z * math.exp(lerp(0.0, math.log(Z2 / Z1), ease("inout", (t - 8.5) / 2.25)))


def _cam_follow(t):
    """Camera centre that keeps the port at its framing point (Bass match, then pull back)."""
    z = _zoom(t)
    px, py = _PORT(t)
    k = ease("inout", (t - T_PULL0) / (T_PULL1 - T_PULL0))
    sx, sy = lerp(540.0, 520.0, k), lerp(900.0, 830.0, k)
    return px - (sx - W / 2) / z, py - (sy - H / 2) / z


def _cam_vy(s):
    """World vertical speed of the camera after T_RISE0: from following his sink to rising."""
    h = 0.02
    follow = (_cam_follow(s + h)[1] - _cam_follow(s - h)[1]) / (2 * h)
    return lerp(follow, -V_RISE, smoothstep(T_RISE0, T_RISE0 + 1.2, s))


def camera(t):
    z = _zoom(t)
    x, y = _cam_follow(t)
    if t > T_RISE0:
        y = _cam_follow(T_RISE0)[1] + LIB.integ(_cam_vy, T_RISE0, t, 24)
    return Camera(x, y, z)


# ============================================================================= Bass layer
def _sag(t, b):
    """Line sag profile at time t: each hanging man pulls it down ~2 px; when he lets go the
    line springs back with a little ripple (a wave runs along it as they fall)."""
    terms = []
    for c in CREW:
        on = b["men"] + 0.012 + c["i"] * (0.42 / 30.0)
        off = b["down"] + (b["mer"] - b["down"]) * c["i"] / 30.0
        if t < on:
            continue
        if t < off:
            s = 2.4 * clamp(bass.pop(t, on, 0.24), 0.0, 1.3)
        else:
            tau = t - off
            if tau > 0.9:
                continue
            s = 2.4 * math.exp(-8.0 * tau) * math.cos(2 * math.pi * 5.5 * tau)
        terms.append((c["x"], s))
    if not terms:
        return None

    def sag(x):
        return sum(s * math.exp(-((x - cx) / 27.0) ** 2) for cx, s in terms)
    return sag


def _draw_crew(ctx, t, b):
    for c in CREW:
        i = c["i"]
        on = b["men"] + 0.012 + i * (0.42 / 30.0)
        off = b["down"] + (b["mer"] - b["down"]) * i / 30.0
        if t < on:
            continue
        sc = bass.pop(t, on, 0.24)
        swing = bass.settle(t, on, amp=7.0 * (1 if hash01(i, 5) < 0.5 else -1), freq=1.6, decay=2.6)
        swing += 1.2 * math.sin(2.3 * t + i)
        peg = (c["x"], LINE_Y + LINE_W / 2.0 - 1.5)
        if t >= off:
            tau = t - off
            g = 4300.0
            dy = 0.5 * g * tau * tau + 18.0 * tau
            if peg[1] + dy > H + 40:
                continue
            dx = (hash01(i, 7) - 0.5) * 70.0 * tau
            swing += (hash01(i, 8) - 0.5) * 2 * (25.0 + 30.0 * hash01(i, 9)) * tau + 6.0 * tau
            peg = (peg[0] + dx, peg[1] + dy)
        LIB.draw_hanging_cutout(ctx, c["kind"], peg, c["h"], PAPER, angle=swing, scale=sc, flip=c["flip"],
                                seed=c["seed"])


def _line_state(t):
    """(u_curl, centre, scale) of the red band."""
    k = (t - T_CURL0) / (T_CURL1 - T_CURL0)
    u = ease("inout3", k)
    cy = lerp(LINE_Y, RING_C[1], ease("inout", k))
    sc = 1.0 + bass.settle(t, T_CURL1, amp=0.035, freq=3.2, decay=8.0) if t >= T_CURL1 else 1.0
    return u, (RING_C[0], cy), sc


def _draw_line(ctx, t, b):
    u, c, sc = _line_state(t)
    sag = _sag(t, b) if u <= 0.0 else None
    polys = LIB.line_band_pts(c, LINE_L, LINE_W, u, seed=SEED, sag=sag, scale=sc)
    # draw-on from the left edge: a slanted scissor cut travels right
    k = ease("out3", (t - 0.12) / 0.88)
    if k < 1.0:
        xf = lerp(-220.0, W + 220.0, k)
        ctx.save()
        ctx.new_path()
        draw.poly(ctx, [(-400, LINE_Y - 80), (xf + 9, LINE_Y - 80), (xf - 9, LINE_Y + 80), (-400, LINE_Y + 80)])
        ctx.clip()
        LIB.fill_polys(ctx, polys, RED)
        ctx.restore()
    else:
        LIB.fill_polys(ctx, polys, RED)


def _ring_screen(t, cam):
    """Screen centre and scale of the ring once the camera starts pulling back (it rides the
    port: the Bass ring IS the faceplate)."""
    if t <= T_PULL0:
        return RING_C, 1.0
    p = cam.to_screen(_PORT(t))
    return p, cam.zoom / Z0


# ============================================================================= live world
def _live(f, t, cam):
    f.set_camera(cam)
    z = cam.zoom
    # water: depth-anchored section, a little darker than daylight (evening)
    underwater(f, t, bright=0.86)
    # backlight: a soft pool of brighter water behind him, the surface glow growing as we rise
    ps = cam.to_screen(DIVER.root(t))
    LIB.screen_glow(f, (ps[0], ps[1] - 120), 900.0, PAL.surface, 0.11)
    rise_k = smoothstep(8.4, 10.6, t)
    if rise_k > 0:
        LIB.screen_band(f, -10, 1100, PAL.surface, 0.30 * rise_k, 0.0, blur=0)
        atmos.underwater_rays(f, surface_y=0.0, t=t, spacing=150.0, angle=95.0, fan=10.0, length=4200.0,
                              intensity=0.55 * rise_k, density=0.6, seed=4, blur=16)
    # far snow, then the hose (behind the helmet), the diver, bubbles
    snow = 0.55 + 0.45 * smoothstep(1.5, 0.6, z)
    with f.layer() as L:
        LIB.draw_hose(L, HOSE.points(t), LIB.HOSE_W)
        sk = DIVER.draw(f, t, L)
    # the port glass catches the light from above: a soft sheen on its upper half
    pc, vr = LIB.port_center(sk)
    with f.light(blur=3.0) as A:
        draw.ellipse(A, (pc[0] - 0.22 * vr, pc[1] - 0.42 * vr), 0.56 * vr, 0.30 * vr, -18.0)
        draw.fill(A, PAL.surface, 0.10)
    atmos.bubbles(f, _VALVE, rate=5.5, t=t, seed=11, rise=(260.0, 430.0), size=(1.6, 6.5), spread=8.0,
                  current=14.0, height=3400.0, alpha=0.95)
    for i, te in enumerate(EXHALES):
        atmos.exhale(f, _VALVE, te, n=26, t=t, seed=50 + i, size=(1.8, 12.0), rise=(280.0, 460.0), spread=44.0,
                     current=14.0, height=3400.0, alpha=0.95)
    atmos.marine_snow(f, density=snow, t=t, seed=3, sink=9.0, current=(7.0, 0.0), alpha=0.85)


def _port_specks(f, t):
    """A few big out-of-focus specks drifting past the lens while we look into the port."""
    a = smoothstep(T_IRIS0, T_IRIS0 + 0.3, t) * (1.0 - smoothstep(6.05, 6.5, t))
    if a <= 0.0:
        return
    with f.light(par=0.0, blur=5.0) as A:
        A.save()
        A.identity_matrix()
        A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
        for i in range(11):
            x = 540 + 520 * (hash01(i, 71) - 0.5) + (hash01(i, 72) - 0.4) * 60.0 * (t - 5.0)
            y = 900 + 420 * (hash01(i, 73) - 0.5) - (8.0 + 22.0 * hash01(i, 74)) * (t - 5.0)
            r = 5.0 + 16.0 * hash01(i, 75) ** 2
            al = (0.10 + 0.20 * hash01(i, 76)) * a * (0.7 + 0.3 * math.sin(3.0 * t + i))
            draw.glow_disc(A, (x, y), r, PAL.surface, al, core=0.55)
        A.restore()


# ============================================================================= render
def render(f, t, T):
    b = _beats(T)
    live = t >= T_LIVE
    k_bass = 1.0 - smoothstep(5.0, 6.6, t)          # post: Bass print -> live
    cam = camera(t) if live else None
    if live:
        _live(f, t, cam)
        _port_specks(f, t)
    else:
        f.fill(INK)
    # the Bass paper: black with (once it irises) a cut hole inside the ring
    paper_a = 1.0 - smoothstep(T_PULL0, T_PULL0 + 0.45, t)
    rc, rk = _ring_screen(t, cam) if live else (RING_C, 1.0)
    with f.screen() as S:
        if live and paper_a > 0.0:
            r = (RING_R - LINE_W / 2.0 + 1.0) * ease("out3", (t - T_IRIS0) / (T_IRIS1 - T_IRIS0)) * rk
            S.save()
            S.new_path()
            S.rectangle(-50, -50, W + 100, H + 100)
            if r > 0.5:
                pts = draw.cut_circle(rc, r, seed=SEED + 3, n=56)
                draw.poly(S, pts[::-1])
            S.set_fill_rule(1)
            S.set_source_rgba(*INK, paper_a)
            S.fill()
            S.restore()
        if t < 4.9:
            _draw_crew(S, t, b)
        ring_a = 1.0 - smoothstep(6.15, 6.85, t)
        if ring_a > 0.0:
            if rk == 1.0 and rc == RING_C:
                if ring_a >= 1.0:
                    _draw_line(S, t, b)
                else:
                    S.push_group()
                    _draw_line(S, t, b)
                    S.pop_group_to_source()
                    S.paint_with_alpha(ring_a)
            else:
                u, c, sc = _line_state(t)
                polys = LIB.line_band_pts(c, LINE_L, LINE_W, u, seed=SEED, scale=sc)
                polys = [[(rc[0] + (x - RING_C[0]) * rk, rc[1] + (y - RING_C[1]) * rk) for x, y in P] for P in polys]
                LIB.fill_polys(S, polys, RED, ring_a)
    LIB.post_blend(f, k_bass)
    if not live:
        f.post["glow"] = 1.0


def motion_blur(t, T):
    # the falling men and the fast part of the pull back
    if 2.5 < t < 4.1:
        return 3
    return 1


def cues(T):
    b = _beats(T)
    cs = [
        Cue(0.12, "paper strip slides in (red line drawn on)", gain_db=-8, pan=-0.4, dur=0.9),
        Cue(b["men"], "31 paper figures clipped onto the line (quick ticks, left to right)", gain_db=-12,
            pan=-0.3, dur=0.45),
        Cue(b["down"], "paper figures dropping away one by one (soft flutters, left to right)", gain_db=-10,
            pan=-0.5, dur=b["mer"] - b["down"] + 0.6),
        Cue(b["mer"], "last figure (the captain) falls - low muffled boom", gain_db=-9, pan=0.5),
        Cue(T_CURL0, "paper curl swish: the line rolls into a ring", gain_db=-10, dur=T_CURL1 - T_CURL0),
        Cue(T_CURL1, "ring closes - soft paper snap", gain_db=-8),
        Cue(T_IRIS0, "iris opens: muffled underwater ambience fades in", gain_db=-6, dur=1.0),
        Cue(T_PULL0, "diver free-flow air hiss + slow deep drone (sustained)", gain_db=-10, dur=4.75),
    ]
    for te in EXHALES:
        cs.append(Cue(te, "diver exhale: bubble burst from the helmet", gain_db=-9, dur=1.2))
    cs.append(Cue(T_RISE0, "rising whoosh, bubbles rolling upward toward the surface", gain_db=-9, dur=2.4))
    return cs
