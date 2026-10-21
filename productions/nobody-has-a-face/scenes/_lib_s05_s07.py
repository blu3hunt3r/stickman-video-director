"""Shared helpers for S05 (habits), S06 (three-oh-seven) and S07 (left hand).

Everything is a pure function of its arguments (frames render in parallel, in any order).
Only engine primitives are used to draw; figures always go through rig.draw_figure.
"""
import math
from contextlib import contextmanager

from engine import *
from engine.props import _xf

# ----------------------------------------------------------------------------- camera
class ZTrack:
    """Track for zoom values, interpolated in log space (perceptually even push / pull)."""

    def __init__(self, keys):
        self.tr = Track([(k[0], math.log(k[1])) + tuple(k[2:]) for k in keys])

    def __call__(self, t):
        return math.exp(self.tr(t))


def zlerp(a, b, k):
    return math.exp(lerp(math.log(a), math.log(b), k))


def cam_for(world_pt, screen_pt, zoom, rot=0.0):
    """Camera (no roll) that maps world_pt to screen_pt at the given zoom."""
    return Camera(world_pt[0] - (screen_pt[0] - W / 2) / zoom,
                  world_pt[1] - (screen_pt[1] - H / 2) / zoom, zoom, rot)


# ----------------------------------------------------------------------------- back view
@contextmanager
def mirrored(f, x0):
    """Mirror everything drawn inside about the world vertical line x = x0 (main + glow)."""
    for c in (f.ctx, f.g):
        c.save()
        c.translate(x0, 0)
        c.scale(-1, 1)
        c.translate(-x0, 0)
    try:
        yield
    finally:
        f.g.restore()
        f.ctx.restore()


def _mx(p, x0):
    return (2 * x0 - p[0], p[1])


def back_solve(p):
    """Joints of a BACK-VIEW figure: the front-view rig mirrored about its hip, so his LEFT
    limbs (rig side 'l') are on screen-LEFT, as seen from behind."""
    J = rig.solve(p)
    out = dict(J)
    for k, v in J.items():
        if k in ("up", "head_dir"):
            out[k] = (-v[0], v[1])
        elif isinstance(v, tuple) and len(v) == 2:
            out[k] = _mx(v, p.x)
    return out


def draw_back(f, p, alpha=1.0):
    """Draw the figure seen from behind (rig.draw_figure under a mirror transform)."""
    with mirrored(f, p.x):
        rig.draw_figure(f, p, alpha=alpha)
    return back_solve(p)


def reach_back(p, side, target):
    """rig.reach for a back-view figure (target in world coordinates)."""
    return rig.reach(p, side, _mx(target, p.x))


# ----------------------------------------------------------------------------- glow control
@contextmanager
def glow_scaled(f, k):
    """Scale the emissive (glow-layer) contribution of everything drawn inside by k.
    Used to keep accent props that sit in shadow from glowing (they are pigment, not light)."""
    f.g.push_group()
    try:
        yield
    finally:
        pat = f.g.pop_group()
        if k > 0:
            f.g.set_source(pat)
            f.g.paint_with_alpha(clamp(k))


# ----------------------------------------------------------------------------- the pocket watch
WATCH_C = (540.0, 960.0)        # S05 OUT / S06 IN: face centre on screen
WATCH_R = 300.0                 # on-screen radius at the cut
WATCH_W = 6.5                   # on-screen rim width at the cut


def stripe_quads(c, angle, n, period, duty, length, offset=0.0):
    """Parallel light bands (blind light) centred on c, running along `angle` (deg)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    out = []
    for i in range(n):
        o = (i - (n - 1) / 2 + offset) * period
        w = period * duty
        p0 = (c[0] + px * (o - w / 2), c[1] + py * (o - w / 2))
        p1 = (c[0] + px * (o + w / 2), c[1] + py * (o + w / 2))
        out.append([(p0[0] - ux * length, p0[1] - uy * length), (p0[0] + ux * length, p0[1] + uy * length),
                    (p1[0] + ux * length, p1[1] + uy * length), (p1[0] - ux * length, p1[1] - uy * length)])
    return out


def desk_insert(f, t, cam, lamp=1.0, stripes=1.0):
    """Top-down macro of the desk: THE pocket watch stopped at 3:07, chain, blind-light bands.
    In this insert world the watch sits at WATCH_C with radius WATCH_R, so a camera
    Camera(540, 960, 1) frames it exactly at the S05/S06 cut."""
    f.set_camera(cam)
    c, r = WATCH_C, WATCH_R
    bands = stripe_quads((c[0] + 40, c[1] - 30), -32, 7, 205, 0.42, 1500, offset=0.15)
    lights = [Light.poly(q, 0.9 * stripes) for q in bands]
    lights.append(Light.radial((c[0] + 380, c[1] - 700), 1250, 0.55 * lamp))
    for q in bands:
        draw.fill(f, q, AMBER, 0.055 * stripes, glow=0.18 * stripes)
    with f.lit(lights, ambient=0.3, soften=5):
        # the desk: far edge, a blank file folder corner, a pencil - quiet line props
        draw.line(f, (-300, 150), (1400, 120), 3.0, WHITE, 0.7)
        draw.line(f, (-300, 172), (1400, 142), 1.6, WHITE, 0.35)
        folder = [(-140, 1480), (420, 1600), (330, 2100), (-230, 1980)]
        draw.stroke(f, folder, 3.0, WHITE, 0.8, closed=True)
        draw.stroke(f, [(-120, 1515), (405, 1628)], 1.8, WHITE, 0.45)
        draw.line(f, (905, 1330), (1180, 1590), 4.5, WHITE, 0.85)
        draw.line(f, (905, 1330), (890, 1312), 2.4, WHITE, 0.85)
        # the watch, face up, chain coiled away to the upper left
        props.clock_face(f, c, r, 3, 7, w=WATCH_W, style="pocket",
                         chain=((330, 420), (60, 520), (-60, 900)))
    # cold glint on the crystal (light, not paint)
    gl = 0.22 + 0.06 * math.sin(t * 1.3)
    draw.arc(f, c, r * 0.86, 200, 238, 3.0, WHITE, gl, glow=0.35)
    draw.arc(f, c, r * 0.80, 205, 222, 2.0, WHITE, gl * 0.7)


# ----------------------------------------------------------------------------- habit rings
def ring_pop(f, c, r, t, t0, w=4.5, hold_alpha=1.0, seed=0):
    """Amber iris ring that pops around a clue at t0 (outback), with an echo ring and a slow
    rotating dashed outer ring while it holds."""
    if t < t0:
        return
    k = ease("outback", inv_lerp(t0, t0 + 0.24, t))
    a = clamp((t - t0) / 0.06) * hold_alpha
    rr = r * (0.35 + 0.65 * k)
    draw.circle(f, c, rr, w, AMBER, a, glow=0.9)
    e = inv_lerp(t0, t0 + 0.45, t)
    if e < 1:
        draw.circle(f, c, rr * (1 + 0.55 * e), 2.0, AMBER, a * (1 - e) * 0.8, glow=0.5)
    if k > 0.5:
        n = 40
        rot = (t - t0) * 40 + 360 * hash01(seed, 7)
        pts = [(c[0] + rr * 1.16 * math.cos(math.radians(rot + 360 * i / n)),
                c[1] + rr * 1.16 * math.sin(math.radians(rot + 360 * i / n))) for i in range(n + 1)]
        draw.stroke(f, pts, 1.6, AMBER, a * 0.55, dash=(10, 12))


# ----------------------------------------------------------------------------- top-down weather
def rain_top(f, t, n=120, seed=3, alpha=0.45, vp=(540.0, 960.0), life=(0.32, 0.55), slow=1.0):
    """Rain seen from straight above (screen space): short streaks falling AWAY from the
    camera, converging toward the vanishing point, ending on the pavement."""
    with f.screen():
        ctx = f.ctx
        ctx.new_path()
        for i in range(n):
            per = life[0] + (life[1] - life[0]) * hash01(seed, i)
            ph = hash01(seed, i, 1)
            cyc = math.floor(t * slow / per + ph)
            tau = t * slow / per + ph - cyc
            gx = -60 + 1200 * hash01(seed, i, int(cyc), 2)
            gy = -60 + 2040 * hash01(seed, i, int(cyc), 3)
            k0 = 1.0 + 0.9 * (1 - tau) ** 1.6          # distance factor from the vanishing point
            k1 = 1.0 + 0.9 * (1 - min(1.0, tau + 0.10)) ** 1.6
            p0 = (vp[0] + (gx - vp[0]) * k0, vp[1] + (gy - vp[1]) * k0)
            p1 = (vp[0] + (gx - vp[0]) * k1, vp[1] + (gy - vp[1]) * k1)
            ctx.move_to(*p0)
            ctx.line_to(*p1)
        ctx.set_line_width(f.lw(1.7))
        ctx.set_source_rgba(1, 1, 1, alpha)
        ctx.stroke()


def pavement_top(f, t, alpha=1.0, seed=21, ripple_box=(-40.0, -40.0, 1120.0, 1960.0), ripple_rate=0.55):
    """Wet pavement from straight above: faint slab joints, a few puddles with rain rings."""
    for k in range(-3, 10):
        y = -120 + k * 250
        draw.line(f, (-400, y), (1480, y + 26), 1.3, WHITE, 0.10 * alpha)
    for k in range(-2, 8):
        x = -60 + k * 210 + 30 * hash01(seed, k)
        draw.line(f, (x, -400), (x - 30, 2320), 1.1, WHITE, 0.07 * alpha)
    for i, (cx, cy, rx, ry) in enumerate(((230, 610, 120, 70), (820, 1190, 150, 86), (420, 1560, 100, 60),
                                          (900, 380, 90, 52))):
        draw.ellipse(f, (cx, cy), rx, ry, 8 * (hash01(seed, i) - 0.5), 1.8, WHITE, 0.32 * alpha)
        draw.ellipse(f, (cx + 6, cy + 4), rx * 0.82, ry * 0.78, 8 * (hash01(seed, i) - 0.5), 1.0, WHITE,
                     0.14 * alpha)
    x0, y0, x1, y1 = ripple_box
    fx.ripples(f, t, x0, y0, x1, y1, rate=ripple_rate, seed=seed + 3, alpha=0.42 * alpha, squash=0.92)


# ----------------------------------------------------------------------------- crowd (exit-capable)
def crowd_top_exit(f, t, area=(60.0, -200.0, 1020.0, 2120.0), n=46, seed=1, speed=70.0, R=(46.0, 60.0),
                   two_way=True, alpha=1.0, highlight=None, highlight_color=AMBER, highlight_amt=0.0,
                   exit_t0=None, exit_spread=0.6, exit_acc=1500.0, view=(0.0, 0.0, 1080.0, 1920.0),
                   exit_to_edge=False):
    """Exact replica of sets.crowd_top (same lanes, sizes, motion and look via
    props.umbrella_top) that can THIN OUT: from exit_t0 (+ a per-umbrella stagger) nobody
    new enters and the umbrellas in view hurry out of frame along their own direction.
    `view` is the visible world box used to decide who is still in frame at the exit time.
    exit_to_edge: from its exit time each umbrella heads for the nearest top/bottom edge
    (the crowd disperses) instead of keeping its lane direction.
    Returns [(x, y, R, i)] of the umbrellas drawn."""
    x0, y0, x1, y1 = area
    span = (y1 - y0) + 300
    out = []
    for i in range(n):
        lane = x0 + (x1 - x0) * hash01(seed, i)
        r = R[0] + (R[1] - R[0]) * hash01(seed, i, 1)
        d = 1 if (not two_way or hash01(seed, i, 2) < 0.6) else -1
        v = speed * (0.75 + 0.5 * hash01(seed, i, 3))
        te = None if exit_t0 is None else exit_t0 + exit_spread * hash01(seed, i, 41)
        if te is not None and t > te:
            ye = y0 - 150 + ((hash01(seed, i, 4) * span + d * v * te) % span)
            if not (view[1] - r < ye < view[3] + r):
                continue                                     # was off frame: never re-enters
            dt = t - te
            de = d
            if exit_to_edge:
                de = -1 if ye < 0.5 * (view[1] + view[3]) else 1
            y = ye + d * v * dt + de * 0.5 * exit_acc * (0.6 + 0.8 * hash01(seed, i, 43)) * dt * dt
        else:
            y = y0 - 150 + ((hash01(seed, i, 4) * span + d * v * t) % span)
        if y < view[1] - 2 * r or y > view[3] + 2 * r:
            continue
        x = lane + 10 * fbm1(t * 0.4 + i, seed + i)
        rot = 22.5 * hash01(seed, i, 5) + 6 * fbm1(t * 0.5, seed + 3 * i)
        out.append((x, y, r, i))
        hl = highlight is not None and highlight(i, x, y) and highlight_amt > 0
        if hl:
            props.umbrella_top(f, (x, y), r, rot, WHITE, alpha=alpha * (1 - highlight_amt))
            props.umbrella_top(f, (x, y), r, rot, highlight_color, fill_alpha=0.35, alpha=alpha * highlight_amt)
        else:
            props.umbrella_top(f, (x, y), r, rot, WHITE, alpha=alpha)
    return out


# ----------------------------------------------------------------------------- sparks
def sparks(f, t, t0, origin, n=16, seed=4, speed=260.0, slow=1.0, life=0.9, grav=380.0, s=1.0):
    """Ignition sparks thrown from `origin` at t0 (slow = time scale for slow motion)."""
    if t < t0:
        return
    tau = (t - t0) * slow
    for k in range(n):
        lf = life * (0.5 + 0.7 * hash01(seed, k, 9))
        if tau > lf:
            continue
        a = math.radians(-160 + 140 * hash01(seed, k))
        v = speed * s * (0.35 + 0.9 * hash01(seed, k, 1))
        vx, vy = math.cos(a) * v, math.sin(a) * v
        x = origin[0] + vx * tau
        y = origin[1] + vy * tau + 0.5 * grav * s * tau * tau
        dt = 0.035
        x2 = origin[0] + vx * max(0.0, tau - dt)
        y2 = origin[1] + vy * max(0.0, tau - dt) + 0.5 * grav * s * max(0.0, tau - dt) ** 2
        fade = (1 - tau / lf) ** 1.2
        draw.line(f, (x2, y2), (x, y), 2.2, AMBER, fade, glow=1.0)


# ----------------------------------------------------------------------------- matchbook extras
MB_W, MB_H = 170.0, 92.0


def matchbook_slot(c, angle, s, i, n=10):
    """Base (on the book's top edge) and top of match slot i of props.matchbook."""
    x = -MB_W / 2 + 14 + i * (MB_W - 28) / (n - 1)
    base, top = _xf([(x, 0), (x, -60.0)], c, angle, s)
    return base, top


def stub_glow(f, c, angle, s, idx, amt, n=10):
    """Amber glow on torn stubs (indices idx) of a props.matchbook drawn at c/angle/s."""
    if amt <= 0:
        return
    for i in idx:
        x = -MB_W / 2 + 14 + i * (MB_W - 28) / (n - 1)
        a, b = _xf([(x, 0), (x, -8)], c, angle, s)
        draw.line(f, a, b, 3.4, AMBER, amt, glow=1.2)
        draw.glow_dot(f, b, 26 * s, AMBER, 0.55 * amt, core=False)


def striker_pts(c, angle, s):
    """The striker strip (hatched band) of props.matchbook, left and right ends."""
    return _xf([(-MB_W / 2 + 14, MB_H - 10), (MB_W / 2 - 14, MB_H - 10)], c, angle, s)
