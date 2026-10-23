"""s02 · INTO THE WOODS: the girl walks into the forest with her lantern (style test).

Look: Limbo sepia-grey fog, black trunks, the lantern's amber pool of light around her.
She is big in frame (about a third of the height), the camera tracks her in profile.

Beats (scene time, s):
   -0.5  iris opens out of the title's flame onto the lantern flame; pull back to reveal her
    0-7  she walks into the wood
    7    stops: her brother's wooden horse on the path. Crouches, picks it up, holds it close
    9.3  lifts the lantern high and looks into the dark ahead. He came this way
   10.3  walks on, slower; the wood darkens around the light
   14.0  eyes open in the dark beyond the light. She stops, pulls the lantern in, trembles
   15.9  thrusts the lantern at them: the flame flares, the eyes snap shut and pull back
   16.7  she hurries on (runs), stops for breath
   18.2  a long jointed leg lowers out of the dark at the edge of the light; she looks up.
   19.78 a second leg lands: cut to black.
"""
import math
from functools import lru_cache

from engine import draw
from engine.core import clamp, lerp, ease, noise1
from engine.frame import Camera
from engine.motion import Actor
from engine.physics import Pendulum
from engine.timing import Cue
from films.lantern import cast, sets

ZOOM = 1.45
FEET_Y = 1580.0            # her feet on screen
IRIS = (540.0, 1040.0)     # where s01's flame sits: the iris opens here
X0 = -220.0
X_TOY = 2330.0
X_EYES = 3040.0            # where she stops when the eyes open
X_RUN = X_EYES + 520.0            # where she stops after running
LEG_X = X_RUN + 250.0      # where the leg's tip lands

T_STOP = 7.0
T_LIFT = 9.3
T_EYES = 14.0
T_THRUST = 15.9
T_LEG = 18.2
T_BLACK = 19.78          # hard cut to black, just after the second leg lands


def k(t, t0, dur, e="inout"):
    return ease(e, clamp((t - t0) / dur))


@lru_cache(maxsize=1)
def girl():
    a = Actor(cast.GIRL, cast.girl(), x=X0, ground=sets.ground_y, facing=1, t0=-1.5, seed=4)
    a.walk(to=X_TOY - 130, gait="child_walk")                    # ends near T_STOP
    a.stand(until=T_STOP + 0.45)
    a.stand(until=T_STOP + 1.85, crouch=0.42, blend=0.35)         # crouch for the toy
    a.stand(until=T_LIFT + 1.0)
    a.walk(to=X_EYES, gait="child_walk", speed=0.62)              # slower, deeper
    a.stand(until=T_THRUST + 0.8)
    a.walk(to=X_RUN, gait="child_run")
    a.stand(until=40.0)
    # the lantern arm (R): held forward; raised to look; pulled in; thrust; carried running
    sh = [(-4.0, 38), (T_LIFT, 38), (T_LIFT + 0.6, 112, "out3"), (T_LIFT + 1.2, 112), (T_LIFT + 1.9, 40, "inout"),
          (T_EYES + 0.5, 40), (T_EYES + 0.9, 24, "out3"), (T_THRUST, 24), (T_THRUST + 0.22, 92, "out5"),
          (T_THRUST + 0.8, 92), (T_THRUST + 1.1, 46, "inout"), (T_LEG + 0.8, 46), (T_LEG + 1.4, 70, "inout"),
          (40.0, 70)]
    el = [(-4.0, 28), (T_LIFT, 28), (T_LIFT + 0.6, 14, "out3"), (T_LIFT + 1.2, 14), (T_LIFT + 1.9, 28, "inout"),
          (T_EYES + 0.5, 28), (T_EYES + 0.9, 62, "out3"), (T_THRUST, 62), (T_THRUST + 0.22, 4, "out5"),
          (T_THRUST + 0.8, 4), (T_THRUST + 1.1, 32, "inout"), (40.0, 32)]
    a.key("arm.R.sh", sh, fade=0.01)
    a.key("arm.R.elbow", el, fade=0.01)
    # fear: the lantern hand trembles while the eyes watch
    a.channel("arm.R.wrist", lambda t: -10 + 7 * noise1(t * 11.0, seed=8) * k(t, T_EYES + 0.4, 0.4)
              * (1 - k(t, T_THRUST, 0.2)), -4.0, 40.0, mode="set", fade=0.01)
    a.arm("R", -4.0, 40.0, fade=0.01, abd=6, grip=1.0)
    # the toy: reach down for it, then hug it to her chest with the left arm
    a.reach("L", T_STOP + 0.55, T_STOP + 1.55, toy_ground(), fade=0.4, grip=1.0)
    a.arm("L", T_STOP + 1.55, 40.0, fade=0.45, sh=22, abd=4, elbow=112, wrist=-6, grip=1.0)
    # where she looks
    a.look_at(T_STOP - 0.6, T_STOP + 1.4, toy_ground(), fade=0.4)
    a.look_at(T_LIFT + 0.2, T_LIFT + 1.6, (X_TOY + 900, -420), fade=0.4)
    a.look_at(T_EYES + 0.2, T_THRUST + 0.7, (X_EYES + 430, -330), fade=0.25)
    a.look_at(T_LEG + 0.7, 40.0, (LEG_X + 60, -620), fade=0.6)
    # leaning back from the eyes; breathing after the run
    a.key("pitch", [(T_EYES + 0.3, 0), (T_EYES + 0.8, -9, "out3"), (T_THRUST, -9), (T_THRUST + 0.2, 8, "out5"),
                    (T_THRUST + 0.7, 0)], fade=0.3)
    a.channel("pitch", lambda t: 9 + 3 * math.sin((t - T_LEG) * 7.0) * (1 - k(t, T_LEG + 0.5, 0.8)),
              T_LEG - 0.2, T_LEG + 0.9, mode="set", fade=0.3)
    a.blink(3.1)
    a.blink(T_LIFT + 1.5)
    a.blink(T_EYES + 1.2, dur=0.2)
    return a


def toy_ground():
    return (X_TOY, sets.ground_y(X_TOY) - 22.0)


@lru_cache(maxsize=1)
def lantern_swing():
    A = girl()

    def pivot(t):
        # the gait jitters the wrist frame to frame; a short box filter keeps the swing physical
        pts = [A.joint(t + i * 0.025, "wrist_R") for i in (-2, -1, 0, 1, 2)]
        return (sum(p[0] for p in pts) / 5.0, sum(p[1] for p in pts) / 5.0)
    return Pendulum(pivot, length=46.0, t0=-3.5, t1=24.0, damping=3.0, gravity=1800.0, dt=1.0 / 120.0)


# ----------------------------------------------------------------------------- camera
@lru_cache(maxsize=4096)
def _track_x(tq):
    A = girl()
    xs = [A.root(tq + i * 0.12)[0] for i in range(-5, 6)]
    return sum(xs) / len(xs)


def track(t):
    """The tracking camera: smoothed x, a lead into the dark at the eyes, a push in at the end."""
    x = _track_x(round(t * 24.0) / 24.0)
    lead = 150.0 + 70.0 * k(t, T_EYES - 0.4, 1.2) * (1 - k(t, T_THRUST + 0.6, 1.0)) - 40.0 * k(t, T_LEG - 0.6, 1.6)
    zoom = ZOOM * (1.0 + 0.10 * k(t, T_LEG, 2.6, "inout")) * (1.0 + 0.04 * k(t, T_EYES, 1.6) * (1 - k(t, T_THRUST, 0.4)))
    gy = sets.ground_y(x)
    y = gy - (FEET_Y - 960.0) / zoom - 140.0 * k(t, T_LEG + 0.4, 2.0, "inout")
    return Camera(x + lead, y, zoom)


def camera(t):
    cam = track(t)
    # opening: start on the flame where the title's iris opened, pull back to the track
    b = k(t, -0.2, 3.4, "inout3")
    if b >= 1.0:
        return cam
    z0 = 4.2
    zoom = math.exp(lerp(math.log(z0), math.log(cam.zoom), b))
    # glide the lantern's screen position from the iris centre to its place in the track
    _, lt, _ = lantern_points(t)
    s_end = cam.to_screen(lt)
    sx, sy = lerp(IRIS[0], s_end[0], b), lerp(IRIS[1], s_end[1], b)
    return Camera(lt[0] - (sx - 540.0) / zoom, lt[1] - (sy - 960.0) / zoom, zoom)


# ----------------------------------------------------------------------------- lantern
def lantern_points(t):
    """Hand (bail), body center, swing angle."""
    A = girl()
    hand = A.joint(t, "wrist_R")
    th = lantern_swing().angle(t)
    th = 0.8 * math.tanh(th / 0.8)          # the bail stops a full swing over
    L = 46.0
    c = (hand[0] + math.sin(th) * L, hand[1] + math.cos(th) * L)
    return hand, c, th


def draw_lantern(ctx, ink, t):
    hand, c, th = lantern_points(t)
    ca, sa = math.cos(-th), math.sin(-th)

    def R(px, py):            # lantern-local (y down from the ring) -> world
        return (c[0] + px * ca - py * sa, c[1] + px * sa + py * ca)
    ctx.new_path()
    ctx.move_to(*hand)
    ctx.line_to(*R(0, -30))
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(3.0)
    ctx.stroke()
    parts = [
        [R(-13, -30), R(13, -30), R(17, -22), R(-17, -22)],          # cap
        [R(-6, -38), R(6, -38), R(6, -30), R(-6, -30)],                # ring knob
        [R(-17, -22), R(-14, -22), R(-14, 18), R(-17, 18)],            # left post
        [R(14, -22), R(17, -22), R(17, 18), R(14, 18)],                # right post
        [R(-1.5, -22), R(1.5, -22), R(1.5, 18), R(-1.5, 18)],          # middle post
        [R(-19, 18), R(19, 18), R(16, 26), R(-16, 26)],                # base
    ]
    for p in parts:
        draw.poly(ctx, p)
    ctx.set_source_rgb(*ink)
    ctx.fill()


def flare(t):
    return math.exp(-max(0.0, t - T_THRUST - 0.12) * 3.2) * k(t, T_THRUST, 0.12, "out3")


def darkness(t):
    return k(t, 9.6, 5.0, "inout") * (1 - 0.6 * flare(t)) + 0.15 * k(t, T_LEG, 1.5)


# ----------------------------------------------------------------------------- the toy
def _toy_polys():
    """Her brother's wooden horse on wheels, local coords (origin on the ground, 1 = px)."""
    P = []
    P.append(draw.ellipse_pts((0, -40), 27, 12, n=24))                                  # body
    P.append([(14, -48), (24, -76), (34, -82), (46, -74), (44, -68), (32, -66), (26, -44)])  # neck, head
    P.append([(24, -78), (27, -90), (31, -80)])                                          # ear
    P.append([(-26, -46), (-40, -38), (-44, -24), (-34, -36), (-24, -36)])              # tail
    for lx in (-18, -8, 10, 19):
        P.append([(lx - 3, -34), (lx + 3, -34), (lx + 3, -16), (lx - 3, -16)])          # legs
    P.append([(-32, -17), (32, -17), (32, -10), (-32, -10)])                             # board
    for wx in (-22, 22):
        P.append(draw.circle_pts((wx, -7), 7.5, n=16))                                   # wheels
    return P


TOY = _toy_polys()


def toy_xform(t):
    """(x, y, angle deg) of the toy: on the path, then in her left hand."""
    gx, gy = X_TOY, sets.ground_y(X_TOY)
    if t < T_STOP + 1.3:
        return gx, gy, 0.0
    w = girl().joint(t, "wrist_L")
    u = k(t, T_STOP + 1.3, 0.25)
    return lerp(gx, w[0] + 6, u), lerp(gy, w[1] + 34, u), lerp(0.0, -14.0, u)


def draw_toy(ctx, ink, t):
    x, y, a = toy_xform(t)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.radians(a))
    ctx.scale(0.8, 0.8)
    for p in TOY:
        draw.poly(ctx, p)
    ctx.set_source_rgb(*ink)
    ctx.fill()
    ctx.restore()


# ----------------------------------------------------------------------------- the eyes
EYES = [  # (dx from X_EYES, y, size, appear at, seed)
    (420.0, -300.0, 1.00, T_EYES + 0.00, 1),
    (560.0, -620.0, 0.80, T_EYES + 0.45, 2),
    (380.0, -60.0, 0.75, T_EYES + 0.75, 3),
    (660.0, -250.0, 1.15, T_EYES + 1.05, 4),
    (520.0, -880.0, 0.65, T_EYES + 1.30, 5),
]


def eye_state(t, e):
    dx, y, s, t_in, seed = e
    opn = k(t, t_in, 0.25, "out3")
    shut = k(t, T_THRUST + 0.10 + 0.05 * seed, 0.12, "in3")
    back = k(t, T_THRUST + 0.10, 0.8, "out3")
    ph = (t * 0.6 + seed * 0.37) % 1.0                       # an occasional blink
    blink = 1.0 - clamp(1.0 - abs(ph - 0.5) / 0.03)
    o = opn * blink * (1 - shut)
    x = X_EYES + dx + 260.0 * back + 6.0 * noise1(t * 0.8, seed=seed)
    return x, y + 4.0 * noise1(t * 0.7, seed=seed + 9), s * (1 - 0.4 * back), o


def draw_eye_bodies(f, t):
    """Soft black masses the eyes sit in (darker than the dark around them)."""
    if t < T_EYES - 0.3 or t > T_THRUST + 1.4:
        return
    with f.layer(blur=34.0) as L:
        for e in EYES:
            x, y, s, o = eye_state(t, e)
            a = k(t, e[3] - 0.3, 0.6) * (1 - k(t, T_THRUST + 0.15, 0.9))
            if a <= 0:
                continue
            draw.ellipse(L, (x - 10 * s, y + 70 * s), 120 * s, 190 * s)
            L.set_source_rgba(*sets.INK, 0.8 * a)
            L.fill()


def draw_eyes(f, t):
    if t < T_EYES - 0.1 or t > T_THRUST + 1.2:
        return
    with f.emit() as G:
        for e in EYES:
            x, y, s, o = eye_state(t, e)
            if o <= 0.01:
                continue
            for ex in (-14 * s, 14 * s):
                draw.ellipse(G, (x + ex, y), 8.0 * s, 5.5 * s * o)
                G.set_source_rgba(1.0, 0.97, 0.88, 0.95)
                G.fill()
                draw.glow_disc(G, (x + ex, y), 30 * s, (1.0, 0.95, 0.8), a=0.35 * o)


# ----------------------------------------------------------------------------- the leg
LEGS = [  # (tip x offset from LEG_X, lands at, hip offset): two of its legs, the body off right in the dark
    (0.0, T_LEG, (700.0, -430.0)),
    (380.0, T_LEG + 0.30, (760.0, -330.0)),
]


def leg_points(t, leg):
    """Hip (off frame right, in the dark), knee (the high point), tip: a two-bone leg."""
    dx0, t_in, (hx, hy) = leg
    hip = (LEG_X + hx, hy)
    land = (LEG_X + dx0, sets.ground_y(LEG_X + dx0) + 4.0)
    u = k(t, t_in, 1.25, "inout3")
    tap = 10.0 * math.sin(clamp((t - t_in - 1.25) / 0.5) * math.pi)
    hover = (land[0] + 260.0, -1600.0)
    tip = (lerp(hover[0], land[0], u) - 25.0 * k(t, t_in + 1.6, 1.5, "inout"), lerp(hover[1], land[1], u) - tap)
    L1, L2 = 760.0, 900.0
    dx, dy = tip[0] - hip[0], tip[1] - hip[1]
    d = clamp(math.hypot(dx, dy), abs(L1 - L2) + 1.0, L1 + L2 - 1.0)
    a = math.atan2(dy, dx)
    cb = clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1.0, 1.0)
    # the knee stays on one side of the hip-tip line (above it: a spider's knee is its high point)
    ka = a + math.acos(cb)
    knee = (hip[0] + math.cos(ka) * L1, hip[1] + math.sin(ka) * L1)
    return hip, knee, tip


def draw_leg(t, L):
    for leg in LEGS:
        if t < leg[1] - 0.1:
            continue
        hip, knee, tip = leg_points(t, leg)

        def seg(a, b, wa, wb, n=12):
            pts = [(lerp(a[0], b[0], i / (n - 1)), lerp(a[1], b[1], i / (n - 1))) for i in range(n)]
            return draw.ribbon(pts, [lerp(wa, wb, i / (n - 1)) for i in range(n)])
        polys = [seg(hip, knee, 84, 58), seg(knee, tip, 58, 8, n=16), draw.ellipse_pts(knee, 46, 40, n=20)]
        for (p0, p1, wa, n_) in ((hip, knee, 40.0, 10), (knee, tip, 34.0, 14)):   # bristles, pointing down the leg
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            for i in range(1, n_):
                u = i / float(n_)
                p = (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u))
                for sgn in (-1, 1):
                    n = ang + sgn * 0.45
                    ln = wa * (1 - u * 0.55)
                    q = (p[0] + math.cos(n) * ln, p[1] + math.sin(n) * ln)
                    w = 3.5 * (1 - u * 0.5)
                    nx, ny = -math.sin(ang) * w, math.cos(ang) * w
                    polys.append([(p[0] - nx, p[1] - ny), q, (p[0] + nx, p[1] + ny)])
        for p in polys:
            draw.poly(L, p)
        L.set_source_rgb(*sets.INK)
        L.fill()


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    pal = f.pal
    cam = camera(t)
    f.set_camera(cam.shaken(t, amp=2.0 + 4.0 * k(t, T_EYES, 0.6) * (1 - k(t, T_THRUST + 1.5, 1.0)),
                            rot_amp=0.08, freq=0.5, seed=7))
    A = girl()
    forest = sets.FOREST
    d = darkness(t)
    forest.draw_back(f, shafts=1.0 - 0.8 * d)
    if d > 0:                              # the far wood sinks into the dark
        with f.screen() as S:
            S.rectangle(0, 0, 1080, 1920)
            S.set_source_rgba(*pal.ink, 0.38 * d)
            S.fill()
    forest.draw_plane(f)
    draw_eye_bodies(f, t)
    hand, lc, th = lantern_points(t)
    fl = flare(t)
    gutter = 0.25 * k(t, T_LEG + 1.4, 0.4) * (0.6 + 0.4 * noise1(t * 9.0, seed=5))
    flick = (0.92 + 0.08 * noise1(t * 7.0, seed=3) + 0.04 * noise1(t * 23.0, seed=4)) * (1 + 0.8 * fl) * (1 - gutter)
    reach = 1.0 - 0.18 * d

    # the pool of warm light in the fog around the lantern (behind her: lights the air)
    with f.light(par=1.0, blur=40.0, alpha=0.85) as Lg:
        draw.glow_disc(Lg, lc, 520.0 * flick * reach, pal.light, a=0.55)
        draw.glow_disc(Lg, lc, 190.0 * flick, pal.light, a=0.55)
    held = t >= T_STOP + 1.3
    with f.layer() as L:
        if not held:
            draw_toy(L, pal.ink, t)
        A.draw(f, t, L)
        if held:
            draw_toy(L, pal.ink, t)
        draw_lantern(L, pal.ink, t)
        draw_leg(t, L)
    with f.emit() as G:
        ca, sa = math.cos(-th), math.sin(-th)

        def R(px, py):
            return (lc[0] + px * ca - py * sa, lc[1] + px * sa + py * ca)
        for x0, x1 in ((-14, -1.5), (1.5, 14)):
            draw.poly(G, [R(x0, -22), R(x1, -22), R(x1, 18), R(x0, 18)])
            G.set_source_rgba(*pal.light, min(1.0, 0.85 * flick))
            G.fill()
        draw.glow_disc(G, R(0, 2), 11.0 * flick, pal.flame, a=1.0, core=0.3)
    forest.draw_canopy(f)
    forest.draw_front(f)
    # the dark beyond the lantern's reach: a soft radial falloff centred on the light
    sx, sy = cam.to_screen(lc)
    zs = cam.zoom / ZOOM
    r0 = (260.0 - 70.0 * d + 160.0 * fl) * zs * flick
    r1 = (1250.0 - 380.0 * d + 300.0 * fl) * zs
    with f.screen() as S:
        draw.radial(S, (sx, sy), r0, max(r1, r0 + 50), [(0.0, pal.ink, 0.0), (0.6, pal.ink, 0.14 + 0.30 * d),
                                                         (1.0, pal.ink, 0.42 + 0.45 * d)])
        S.rectangle(0, 0, 1080, 1920)
        S.fill()
    draw_eyes(f, t)
    if t >= T_BLACK:
        with f.screen() as S:
            S.rectangle(0, 0, 1080, 1920)
            S.set_source_rgb(0.0, 0.0, 0.0)
            S.fill()


def cues(T):
    return [Cue(-0.5, "forest night ambience, distant wind", gain_db=-14, dur=20.5),
            Cue(0.0, "lantern creak on its bail, slow swing", gain_db=-20, dur=20.0),
            Cue(T_STOP + 1.3, "small wooden toy picked up, wheels rattle", gain_db=-16),
            Cue(T_EYES, "low breathing in the dark, something large", gain_db=-14, dur=2.0),
            Cue(T_THRUST + 0.1, "lantern flame flares with a whoosh", gain_db=-10),
            Cue(T_THRUST + 0.8, "child running on leaves", gain_db=-14, dur=1.3),
            Cue(T_LEG + 1.2, "single heavy tap of a chitinous leg on wood", gain_db=-8)]
