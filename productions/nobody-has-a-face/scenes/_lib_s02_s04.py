"""Shared helpers for S02 (The City), S03 (Useless Evidence) and S04 (The Rain Murders).

Everything here is a pure function of its arguments (no state between frames).
Only white line art + the three story accents (AMBER light/clues, CRIMSON killer, BLUE law).
"""
import math
from contextlib import contextmanager

import cairo
import numpy as np
from scipy.ndimage import gaussian_filter

from engine import *
from engine.core import W, H, BLACK
from engine.frame import _surface_to_array, _array_to_surface

# ----------------------------------------------------------------------------- shared numbers
S01_RING_R = 260.0                               # S01 out: head ring radius on screen
S01_RING_W = rig.FIG_LW * (260.0 / rig.SEG["head_r"]) ** 0.35   # its on-screen line width (~15.3 px)

FLAME_SCREEN = (540.0, 1150.0)                   # S02 out / S03 in: flame mid-height on screen
FLAME_PX = 100.0                                 # flame height on screen at the cut
MATCH_S = 1.0                                    # canonical hand-held match scale (props.match)
FLAME_H_WORLD = 34.0 * 0.85 * MATCH_S            # props.flame mean drawn height (flicker avg ~0.85)
CUT_ZOOM = FLAME_PX / FLAME_H_WORLD              # ~3.46

# S02 street-level world (also used by S03's opening shot so the cut is pixel-continuous)
ST_GROUND = 1500.0
DET_STOP_X = 585.0                               # hip x where the detective stops under the lamp
LAMP_BASE = (262.0, ST_GROUND)
LAMP_H = 880.0


def tglob(T, t):
    """Global film time (keeps flame flicker / breathing continuous across scene cuts)."""
    return T.start + t


def frame_t(t):
    """Snap a (motion-blur sub-frame) time to its frame time, so shot cuts never blend."""
    return round(t * FPS) / FPS


def log_zoom(z0, z1, k):
    return math.exp(lerp(math.log(z0), math.log(z1), k))


def cam_put(world_pt, screen_pt, zoom, rot=0.0):
    """Camera that shows world_pt at screen_pt with the given zoom/roll."""
    dx, dy = (screen_pt[0] - W / 2) / zoom, (screen_pt[1] - H / 2) / zoom
    if rot:
        dx, dy = rotate((dx, dy), -rot)
    return Camera(world_pt[0] - dx, world_pt[1] - dy, zoom, rot)


def ramp_time(t, t0, t1, k):
    """Speed ramp: time runs at 1x before t0, eases to k-x speed by t1 (integral of smoothstep)."""
    if t <= t0:
        return t
    d = t1 - t0
    if t <= t1:
        x = (t - t0) / d
        return t - (1 - k) * d * (x ** 3 - 0.5 * x ** 4)
    return t - (1 - k) * (0.5 * d + (t - t1))


def smooth_siren(t, rate=1.6, phase=0.0):
    """siren() with a short exponential afterglow so edge glows pulse instead of popping."""
    b = r = 0.0
    for i in range(6):
        dt = i * 0.022
        w = math.exp(-dt / 0.05)
        sb, sr = siren(t - dt, rate, phase)
        b = max(b, sb * w)
        r = max(r, sr * w)
    return b, r


# ----------------------------------------------------------------------------- generic drawing
def clear_glow(f, pts, alpha=1.0):
    """Erase the emissive (glow) layer under an occluder. The engine adds the glow layer on top
    of everything at finish(), so without this, lamps/windows behind a black shape shine through."""
    g = f.g
    g.save()
    g.set_operator(cairo.OPERATOR_DEST_OUT)
    g.set_source_rgba(0, 0, 0, clamp(alpha))
    g.move_to(*pts[0])
    for p in pts[1:]:
        g.line_to(*p)
    g.close_path()
    g.fill()
    g.restore()


def black_poly(f, pts, alpha=1.0, glow_too=True):
    """Occluder: fill with the canvas color so far line art reads behind near shapes."""
    draw.fill(f, pts, BLACK, alpha)
    if glow_too:
        clear_glow(f, pts, alpha)


def black_rect(f, x, y, w, h):
    black_poly(f, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)])


def tower(f, x, ground_y, w, h, seed, t=0.0, alpha=1.0, lw=3.0, lit=0.16, roof="flat", occlude=True,
          window_alpha=0.45, cols=None, rows=None):
    """props.building with an opaque black body (so it hides the moon / farther towers)."""
    if occlude:
        black_rect(f, x, ground_y - h, w, h)
    return props.building(f, x, ground_y, w, h, seed=seed, lit=lit, t=t, alpha=alpha, lw=lw, roof=roof,
                          window_alpha=window_alpha, cols=cols, rows=rows)


def far_row(f, ground_y, seed, x0, x1, hmin, hmax, wmin=110.0, wmax=190.0, gap=14.0, t=0.0, alpha=0.3,
            lw=1.6, lit=0.1, occlude=False):
    """A row of distant towers with controlled heights (roof details included in hmax)."""
    x = x0
    i = 0
    roofs = ("flat", "antenna", "water", "flat")
    while x < x1:
        w = wmin + (wmax - wmin) * hash01(seed, i)
        roof = roofs[int(hash01(seed, i, 2) * 4)]
        extra = {"antenna": 140.0, "water": 120.0}.get(roof, 0.0)
        h = hmin + (hmax - hmin - extra) * hash01(seed, i, 1)
        tower(f, x, ground_y, w, h, seed * 100 + i, t=t, alpha=alpha, lw=lw, lit=lit, roof=roof, occlude=occlude,
              window_alpha=0.4)
        x += w + gap
        i += 1


def fire_escape(f, x_face, y_top, y_bot, side=1, alpha=0.85, lw=2.2, pitch=176.0, depth=96.0):
    """Zig-zag fire escape bolted to a tower face (side=+1 sticks out to the right)."""
    k = 0
    y = y_top
    while y < y_bot:
        xo = x_face + side * depth
        draw.line(f, (x_face, y), (xo, y), lw * 1.2, WHITE, alpha)                 # landing
        draw.line(f, (x_face, y - 34), (xo, y - 34), lw * 0.7, WHITE, alpha * 0.8)  # railing
        for j in range(4):
            xx = x_face + side * depth * (j + 1) / 4
            draw.line(f, (xx, y), (xx, y - 34), lw * 0.5, WHITE, alpha * 0.6)
        if y + pitch < y_bot:
            a = (x_face + side * depth * (0.15 if k % 2 else 0.85), y)
            b = (x_face + side * depth * (0.85 if k % 2 else 0.15), y + pitch)
            draw.line(f, a, b, lw * 0.9, WHITE, alpha * 0.9)
            for j in range(1, 7):                                                    # stair treads
                q = lerp(a, b, j / 7)
                draw.line(f, (q[0] - 7, q[1]), (q[0] + 7, q[1]), lw * 0.5, WHITE, alpha * 0.55)
        y += pitch
        k += 1


def bolt(f, a, b, seed=0, alpha=1.0, w=2.0, glow=0.35, branches=2):
    """Lightning (same jagged construction as fx.lightning) with a controllable glow so a far
    bolt can sit behind occluding towers without its emissive halo bleeding over them."""
    def jag(p, q, depth, s):
        pts = [p, q]
        disp = math.hypot(q[0] - p[0], q[1] - p[1]) * 0.18
        for d in range(depth):
            new = [pts[0]]
            for i in range(len(pts) - 1):
                m = ((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
                off = (hash01(s, d, i) - 0.5) * 2 * disp
                new += [(m[0] + off, m[1] + off * 0.2), pts[i + 1]]
            pts = new
            disp *= 0.55
        return pts
    main = jag(a, b, 6, seed)
    draw.stroke(f, main, w, WHITE, alpha, glow=glow, glow_w=w * 3)
    for k in range(branches):
        i = int(len(main) * (0.3 + 0.4 * hash01(seed, k, 9)))
        p = main[i]
        q = (p[0] + (hash01(seed, k, 3) - 0.5) * 260, p[1] + 140 + 120 * hash01(seed, k, 4))
        draw.stroke(f, jag(p, q, 4, seed + 50 + k), w * 0.6, WHITE, alpha * 0.8, glow=glow * 0.6)


def lens_canopy(f, rim_y, xc=540.0, alpha=1.0, blur=10.0, ribs=7):
    """Screen-space wipe: the underside of an umbrella right at the lens. Opaque black above
    a scalloped rim at rim_y, ribs converging to a far apex, the shaft hanging below."""
    if rim_y < -260:
        return
    apex = (xc, rim_y - 2600.0)
    span = 2400.0
    tips = [(xc - span / 2 + span * i / ribs, rim_y - 40.0 * abs(i - ribs / 2) / (ribs / 2)) for i in range(ribs + 1)]
    edge = []
    for i in range(ribs):
        a, b = tips[i], tips[i + 1]
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 70.0)
        edge += draw.bezier_pts(a, m, m, b, 8)[:-1]
    edge.append(tips[-1])
    with f.screen():
        body = edge + [(tips[-1][0], -900.0), (tips[0][0], -900.0)]
        black_poly(f, body, alpha)
        with f.blurred(blur):
            draw.stroke(f, edge, 7.0, WHITE, 0.75 * alpha)
            for tp in tips[1:-1]:
                draw.line(f, tp, lerp(tp, apex, 0.5), 4.0, WHITE, 0.35 * alpha)
            draw.line(f, (xc + 30, rim_y - 120), (xc + 30, rim_y + 820), 12.0, WHITE, 0.6 * alpha)


def wire(f, a, b, sag=60.0, w=1.6, alpha=0.6):
    pts = []
    for i in range(25):
        u = i / 24
        pts.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u + sag * 4 * u * (1 - u)))
    draw.stroke(f, pts, w, WHITE, alpha)


def umbrella_top_pts(c, R, rot, ribs=8):
    """Scalloped rim of props.umbrella_top (identical geometry) for black occlusion fills."""
    tips = [(c[0] + math.cos(math.radians(rot + 360 * i / ribs)) * R,
             c[1] + math.sin(math.radians(rot + 360 * i / ribs)) * R) for i in range(ribs)]
    edge = []
    for i in range(ribs):
        a, b = tips[i], tips[(i + 1) % ribs]
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        mm = (m[0] + (c[0] - m[0]) * 0.10, m[1] + (c[1] - m[1]) * 0.10)
        edge += draw.bezier_pts(a, mm, mm, b, 5)[:-1]
    return edge, tips


def hero_umbrella_top(f, c, R, rot, ferrule_px=7.0, alpha=1.0, opaque=1.0):
    """props.umbrella_top look (identical to the crowd's at normal zoom), but it can turn opaque
    (black canopy, glow cleared) and its ferrule stops growing past `ferrule_px` on screen, so the
    camera can dive right into it."""
    edge, tips = umbrella_top_pts(c, R, rot)
    if opaque > 0:
        black_poly(f, edge, opaque)
    draw.stroke(f, edge, 2.6, WHITE, alpha, closed=True)
    for tp in tips:
        draw.line(f, c, tp, 1.8, WHITE, alpha * 0.7)
    draw.circle(f, c, min(3.0, ferrule_px / max(f.cam.zoom, 1e-3)), 1, WHITE, alpha, fill_it=True)


def rain_top(f, t, n=150, seed=31, alpha=0.55, center=(540.0, 960.0), life=0.32, reach=1.0, w=2.0):
    """Rain seen from straight above (screen space): drops fall AWAY from the camera, so their
    streaks converge on the vanishing point and shrink as they recede."""
    with f.screen():
        ctx = f.ctx
        ctx.new_path()
        cx, cy = center
        Rm = math.hypot(W, H) * 0.62 * reach
        for i in range(n):
            ph = hash01(seed, i)
            per = life * (0.8 + 0.5 * hash01(seed, i, 1))
            cyc = math.floor(t / per + ph)
            tau = t / per + ph - cyc
            a = hash01(seed, i, int(cyc), 2) * 2 * math.pi
            r0 = Rm * (0.25 + 0.75 * math.sqrt(hash01(seed, i, int(cyc), 3)))
            r = r0 * (1 - 0.55 * tau)
            L = 10 + 70 * (r / Rm) * (1 - tau)
            ux, uy = math.cos(a), math.sin(a)
            x1, y1 = cx + ux * r, cy + uy * r
            ctx.move_to(x1, y1)
            ctx.line_to(x1 - ux * L, y1 - uy * L)
        ctx.set_line_width(w)
        ctx.set_source_rgba(1, 1, 1, alpha)
        ctx.stroke()


def flash_pop(f, k, src=(980.0, 260.0)):
    """White camera-flash pop: a soft wash of light from the flash side (no hard source blob)."""
    if k <= 0.01:
        return
    with f.screen():
        draw.glow_dot(f, src, 1250, WHITE, 0.32 * k, core=False)
        draw.glow_dot(f, src, 420, WHITE, 0.4 * k, core=False)


def strobe_edges(f, t, amt=1.0, rate=1.6, y=960.0, r=600.0, phase=0.0):
    """Police light bar glow pulsing at the left/right frame edges (siren blue / crimson)."""
    b, rr = smooth_siren(t, rate, phase)
    with f.screen():
        if b > 0.01:
            draw.glow_dot(f, (-160, y - 160), r, BLUE, 0.6 * b * amt, core=False)
        if rr > 0.01:
            draw.glow_dot(f, (W + 160, y + 160), r, CRIMSON, 0.5 * rr * amt, core=False)
    return b, rr


def curl_x(h, t, seed=0, strand=0):
    """Horizontal offset of a rising smoke wisp at height h (world px above its source)."""
    amp = (3.0 + 0.032 * h) * (1.0 if strand == 0 else 0.7)
    lam = 90.0 + 0.28 * h
    ph = seed * 1.7 + strand * 2.1
    return (amp * math.sin(2 * math.pi * h / lam - 2.3 * t + ph)
            + 0.45 * amp * fbm1(h / 260.0 - 0.35 * t, seed + 11 * strand) + 4.0 * strand)


def curl_wisp(f, x0, y0, t, height=1400.0, seed=0, alpha=0.6, w=2.0, strands=2, floor=0.32):
    """Thin curling smoke rising from (x0, y0) - stays readable high up (for a tilt-up)."""
    n = 70
    for s_ in range(strands):
        prev = None
        for i in range(n + 1):
            h = height * (i / n) ** 1.25
            q = (x0 + curl_x(h, t, seed, s_), y0 - h)
            if prev is not None:
                k = h / height
                a = alpha * (floor + (1 - floor) * math.exp(-h / 420.0)) * min(1.0, h / 18.0 + 0.2) * (1 - k ** 3)
                a *= 1.0 if s_ == 0 else 0.55
                draw.line(f, prev, q, w * (1 - 0.35 * k), WHITE, a)
            prev = q


# ----------------------------------------------------------------------------- the detective in S02/S03
def det_walk_pose(t, x0, speed=96.0, facing=-1, limp=0.5):
    return rig.walk(t, x0, ST_GROUND, speed, facing=facing, s=1.0, limp=limp)


def det_stand(x, facing=-1):
    return rig.stand(x, ST_GROUND, facing=facing)


def hold_target(p, J=None):
    """Where the LEFT hand holds the lit match (in front of the chest, below the chin)."""
    J = J or rig.solve(p)
    f_ = p.facing if p.facing else 1
    return (J["neck"][0] + f_ * 50.0, J["neck"][1] + 42.0)


HOLD_ANGLE = -97.0          # match angle while held up (facing left: up and slightly forward)


def match_geom(hand, angle=HOLD_ANGLE, s=MATCH_S):
    """Tip of the hand-held match and the flame's mid-height point (world)."""
    a = math.radians(angle)
    tip = (hand[0] + math.cos(a) * 52.0 * s, hand[1] + math.sin(a) * 52.0 * s)
    mid = (tip[0], tip[1] - 0.5 * FLAME_H_WORLD)
    return tip, mid


# one limping step to the left (S02), then he stands holding the lit match (S02 end = S03 start)
T_STEP0, T_STEP1 = 6.95, 7.80
STEP_LONG = 70.0            # RIGHT foot: long step
STEP_SHORT_GAP = 6.0        # LEFT (bad) foot lands short, just behind the right


def det_step_pose(t, t0=T_STEP0, t1=T_STEP1):
    """Hand-keyed planted-foot step (facing -1): long step with the RIGHT foot, short limping
    step with the LEFT foot; the hip dips and the head bobs when weight lands on the bad leg."""
    stand = det_stand(DET_STOP_X)
    J0 = rig.solve(stand)
    xl0, xr0 = J0["lf"][0], J0["rf"][0]
    g = ST_GROUND
    m1 = lerp(t0, t1, 0.40)             # right foot lands
    m2 = lerp(t0, t1, 0.78)             # left (bad) foot lands - the hitch
    kr = ease("inout", inv_lerp(t0, m1, t))
    kl = ease("inout", inv_lerp(m1 + 0.04, m2, t))
    xr_end = xr0 - STEP_LONG
    xl_end = xr_end + STEP_SHORT_GAP
    xr = lerp(xr0, xr_end, kr)
    yr = g - 30.0 * math.sin(math.pi * kr)
    xl = lerp(xl0, xl_end, kl)
    yl = g - 16.0 * math.sin(math.pi * kl)
    hk = ease("inout", inv_lerp(t0, t1, t))
    hip_x = stand.x + ((xr_end + xl_end) - (xr0 + xl0)) * 0.5 * hk
    dip = 10.0 * math.exp(-((t - m2 - 0.06) / 0.09) ** 2)
    rise = 5.0 * math.sin(math.pi * kr) * (1 - kl)
    p = stand.copy(x=hip_x, y=stand.y + dip - rise, lean=stand.lean + 4.0 * math.sin(math.pi * hk) + 0.4 * dip,
                   head=stand.head + 1.1 * dip)
    p = rig.plant(p, "r", (xr, yr))
    p = rig.plant(p, "l", (xl, yl))
    return p


_CACHE = {}


def det_final():
    """(pose, left-hand point, match tip, flame mid) of the detective at the S02 -> S03 cut
    (before breathing; breathing only moves lean/head - the hand is IK-locked)."""
    if "final" not in _CACHE:
        p = det_step_pose(100.0)
        hand = hold_target(p)
        tip, mid = match_geom(hand)
        _CACHE["final"] = (p, hand, tip, mid)
    return _CACHE["final"]


def hang_target(J, facing=-1):
    """Relaxed hanging hand (almost straight arm, a touch forward)."""
    return (J["shoulder"][0] + facing * 12.0, J["shoulder"][1] + 120.0)


def det_hold_pose(tg, hand=None):
    """Final stance with breathing; LEFT hand locked on the match point, RIGHT arm hanging."""
    p0, h, tip, mid = det_final()
    p = rig.breathe(p0, tg, amt=0.8, seed=5)
    p = rig.reach(p, "l", hand or h)
    p = rig.reach(p, "r", hang_target(rig.solve(p)))
    return p


@contextmanager
def soft(f, radius, alpha=1.0):
    """Like f.blurred() but never blurs at full resolution (>= 2x downsample): small radii
    (rack-focus ramps) cost ~1/4 of the engine version. No-op below 0.5 px."""
    if radius < 0.5:
        if alpha >= 0.999:
            yield
        else:
            with f.alpha(alpha):
                yield
        return
    ctx = f.ctx
    ctx.push_group()
    try:
        yield
    finally:
        pat = ctx.pop_group()
        ctm = cairo.Matrix(*ctx.get_matrix())
        r = radius * f.scale
        k = max(2, int(r / 3))
        sw, sh = max(1, f.pw // k), max(1, f.ph // k)
        down = cairo.Matrix(xx=sw / f.pw, yy=sh / f.ph)
        small = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
        sc = cairo.Context(small)
        sc.set_matrix(ctm.multiply(down))
        sc.set_source(pat)
        sc.paint()
        arr = _surface_to_array(small).astype(np.float32)
        sig = max(0.35, r / k)
        arr = gaussian_filter(arr, (sig, sig, 0))
        bp = cairo.SurfacePattern(_array_to_surface(arr))
        bp.set_matrix(cairo.Matrix(*ctx.get_matrix()).multiply(down))
        bp.set_filter(cairo.FILTER_BILINEAR)
        ctx.set_source(bp)
        ctx.paint_with_alpha(alpha)


# ----------------------------------------------------------------------------- S03 evidence props
def _xf(pts, c, ang=0.0, s=1.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (x * ca - y * sa) * s, c[1] + (x * sa + y * ca) * s) for x, y in pts]


def brush(f, tip, angle=-120.0, s=1.0, alpha=1.0, splay=1.0):
    """Fingerprint-dusting brush: long handle + fan of soft bristles ending at `tip`.
    angle points from the bristle tip toward the handle (degrees)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    base = (tip[0] + ux * 46 * s, tip[1] + uy * 46 * s)               # ferrule
    end = (tip[0] + ux * 250 * s, tip[1] + uy * 250 * s)              # handle end
    draw.line(f, base, end, 5.0, WHITE, alpha)
    draw.line(f, (base[0] + px * 9 * s, base[1] + py * 9 * s), (base[0] - px * 9 * s, base[1] - py * 9 * s), 3.0, WHITE, alpha)
    draw.circle(f, end, 6 * s, 2.4, WHITE, alpha)
    for i in range(9):
        k = (i - 4) / 4.0
        q = (tip[0] + px * k * 22 * s * splay - ux * 4 * s * (1 - k * k), tip[1] + py * k * 22 * s * splay - uy * 4 * s * (1 - k * k))
        b0 = (base[0] + px * k * 8 * s, base[1] + py * k * 8 * s)
        draw.line(f, b0, q, 1.6, WHITE, alpha * 0.85)


def tumbler(f, c, h=300.0, w=210.0, alpha=1.0):
    """Drinking glass in profile (tapered), with a rim ellipse and two glints. c = base center."""
    x, y = c
    top_w, bot_w = w, w * 0.8
    pts = [(x - top_w / 2, y - h), (x - bot_w / 2, y), (x + bot_w / 2, y), (x + top_w / 2, y - h)]
    draw.stroke(f, pts, 3.0, WHITE, alpha)
    draw.ellipse(f, (x, y - h), top_w / 2, 16, 0, 2.6, WHITE, alpha)
    draw.ellipse(f, (x, y - 10), bot_w / 2 - 6, 10, 0, 1.6, WHITE, alpha * 0.5)
    draw.line(f, (x - top_w * 0.32, y - h * 0.86), (x - bot_w * 0.3, y - h * 0.18), 2.0, WHITE, alpha * 0.45)
    draw.line(f, (x - top_w * 0.22, y - h * 0.8), (x - bot_w * 0.21, y - h * 0.42), 1.4, WHITE, alpha * 0.3)


def pencil(f, tip, angle=-40.0, length=300.0, s=1.0, alpha=1.0):
    """Sketch pencil: point at `tip`, body along `angle` (toward the eraser end)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    hw = 10.0 * s
    cone = 46.0 * s
    c0 = (tip[0] + ux * cone, tip[1] + uy * cone)
    e = (tip[0] + ux * length * s, tip[1] + uy * length * s)
    for sg in (1, -1):
        draw.line(f, tip, (c0[0] + px * hw * sg, c0[1] + py * hw * sg), 2.4, WHITE, alpha)
        draw.line(f, (c0[0] + px * hw * sg, c0[1] + py * hw * sg), (e[0] + px * hw * sg, e[1] + py * hw * sg), 2.6, WHITE, alpha)
    lead = (tip[0] + ux * 12 * s, tip[1] + uy * 12 * s)
    draw.fill(f, [tip, (lead[0] + px * 3 * s, lead[1] + py * 3 * s), (lead[0] - px * 3 * s, lead[1] - py * 3 * s)], WHITE, alpha)
    draw.line(f, (c0[0] + px * hw, c0[1] + py * hw), (c0[0] - px * hw, c0[1] - py * hw), 2.0, WHITE, alpha * 0.8)
    band = (e[0] - ux * 34 * s, e[1] - uy * 34 * s)
    draw.line(f, (band[0] + px * hw, band[1] + py * hw), (band[0] - px * hw, band[1] - py * hw), 2.2, WHITE, alpha)
    draw.line(f, (e[0] + px * hw, e[1] + py * hw), (e[0] - px * hw, e[1] - py * hw), 2.6, WHITE, alpha)
    draw.line(f, c0, (e[0] - ux * 34 * s, e[1] - uy * 34 * s), 1.2, WHITE, alpha * 0.45)


def ink_pad(f, c, w=230.0, h=140.0, alpha=1.0):
    x, y = c[0] - w / 2, c[1] - h / 2
    draw.rect(f, x, y, w, h, 3.0, WHITE, alpha, radius=14)
    draw.rect(f, x + 18, y + 18, w - 36, h - 36, 2.0, WHITE, alpha * 0.7, radius=8)
    for i in range(6):                                                  # inked felt hatching
        xx = x + 30 + i * (w - 60) / 5
        draw.line(f, (xx, y + 26), (xx - 22, y + h - 26), 1.2, WHITE, alpha * 0.3)


def print_card(f, c, w=560.0, h=320.0, angle=0.0, boxes=5, alpha=1.0):
    """Booking fingerprint card: a row of empty finger boxes. No text. Returns box centers."""
    corners = _xf([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], c, angle)
    draw.stroke(f, corners, 3.0, WHITE, alpha, closed=True)
    centers = []
    bw = (w - 60) / boxes
    for i in range(boxes):
        x0 = -w / 2 + 30 + i * bw
        q = _xf([(x0 + 6, -h / 2 + 70), (x0 + bw - 6, -h / 2 + 70), (x0 + bw - 6, h / 2 - 40), (x0 + 6, h / 2 - 40)], c, angle)
        draw.stroke(f, q, 2.0, WHITE, alpha * 0.75, closed=True)
        centers.append(_xf([(x0 + bw / 2, (-h / 2 + 70 + h / 2 - 40) / 2)], c, angle)[0])
    a, b = _xf([(-w / 2 + 30, -h / 2 + 40), (w / 2 - 30, -h / 2 + 40)], c, angle)
    draw.line(f, a, b, 1.4, WHITE, alpha * 0.4)
    return centers


SKETCH_W, SKETCH_H = 300.0, 390.0


def sketch_sheet(f, c, angle=0.0, alpha=1.0, k=1.0, circle_alpha=1.0, pin=True, lw=1.0):
    """A police sketch: blank sheet with one hand-drawn circle (k = draw-on progress 0..1)."""
    w, h = SKETCH_W, SKETCH_H
    corners = _xf([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], c, angle)
    draw.stroke(f, corners, 2.6 * lw, WHITE, alpha, closed=True)
    sketch_circle(f, _xf([(0, -h * 0.08)], c, angle)[0], 82.0, k, alpha * circle_alpha, angle, lw)
    if pin:
        draw.circle(f, _xf([(0, -h / 2 + 14)], c, angle)[0], 5.0, 1, WHITE, alpha * 0.9, fill_it=True)


def sketch_circle(f, c, r, k, alpha=1.0, rot=0.0, lw=1.0):
    """Two slightly offset pencil passes (sketchy), drawn on progressively (k 0..1)."""
    if k <= 0 or alpha <= 0:
        return
    a0 = -120.0 + rot
    draw.arc(f, c, r, a0, a0 + 360.0 * clamp(k * 1.06), 3.4 * lw, WHITE, alpha)
    k2 = clamp((k - 0.18) / 0.82)
    if k2 > 0:
        draw.arc(f, (c[0] + 3, c[1] - 2), r * 1.035, a0 + 25, a0 + 25 + 330.0 * k2, 1.6 * lw, WHITE, alpha * 0.6)


def panel_frame(f, box, alpha=1.0):
    """Screen-space triptych panel: opaque black body + thin white border."""
    x0, y0, x1, y1 = box
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    black_poly(f, pts, alpha)
    draw.stroke(f, pts, 3.0, WHITE, 0.9 * alpha, closed=True)


def offscreen_arm(f, hand, shoulder, side="l", lw_px=13.0, alpha=1.0, flip=False):
    """Close-up arm of an (off-frame) figure, in SCREEN px. The figure is a normal
    rig.draw_figure call whose body axis runs perpendicular to the arm at the shoulder, so
    its head and torso stay beyond the frame edge while the arm reaches in.
    Returns the solved joints mapped to screen space."""
    ux, uy = vnorm((shoulder[0] - hand[0], shoulder[1] - hand[1]))
    hx, hy = (-uy, ux) if not flip else (uy, -ux)                      # head direction on screen
    rot = math.degrees(math.atan2(hx, -hy))                             # local up -> (hx, hy)
    d = vlen((shoulder[0] - hand[0], shoulder[1] - hand[1]))
    s = max(0.5, d / 112.0)                                             # arm slightly bent
    cam = cam_put((0.0, 0.0), shoulder, 1.0, rot)
    with f.screen():
        with f.camera(cam):
            p = Pose(x=0.0, y=0.0, s=s, facing=1)
            J0 = rig.solve(p)
            p = p.copy(x=-J0["shoulder"][0], y=-J0["shoulder"][1])
            p = rig.reach(p, side, cam.to_world(hand))
            other = "r" if side == "l" else "l"
            J1 = rig.solve(p)
            p = rig.reach(p, other, (J1["shoulder"][0] + 20 * s, J1["shoulder"][1] + 112 * s))
            J = rig.draw_figure(f, p, alpha=alpha, lw=lw_px / (s ** 0.5))
    return {k: cam.to_screen(v) for k, v in J.items() if isinstance(v, tuple) and len(v) == 2}


# ----------------------------------------------------------------------------- S04 crime-scene kit
def _env(y, yc, half=720.0, fade=230.0):
    """Tile visibility envelope: 1 near the tile center, fading to 0 at its edges."""
    d = abs(y - yc)
    return clamp(1.0 - (d - half) / fade)


def cobbles(f, cx, cy, w=1500.0, h=1900.0, alpha=0.32, seed=1):
    """Top-down cobblestones: offset rows of rounded stones (fade toward the tile ends)."""
    sw, sh = 74.0, 50.0
    rows = int(h / (sh + 8))
    for r in range(rows):
        y = cy - h / 2 + r * (sh + 8)
        a = alpha * _env(y + sh / 2, cy)
        if a <= 0.01:
            continue
        off = (sw / 2) if r % 2 else 0.0
        n = int(w / (sw + 8)) + 2
        for c in range(n):
            x = cx - w / 2 - off + c * (sw + 8)
            jx = (hash01(seed, r, c) - 0.5) * 8
            draw.rect(f, x + jx, y, sw - 4 * hash01(seed, r, c, 1), sh, 1.4, WHITE, a * (0.75 + 0.25 * hash01(seed, r, c, 2)), radius=13)


def bridge_tile(f, cx, cy, t, h=1900.0, alpha=0.6, seed=2):
    """Top-down bridge deck: planks, a railing with posts on the right, dark water beyond."""
    rail_x = cx + 300.0
    for k in range(int(h / 44)):
        y = cy - h / 2 + k * 44.0
        a = alpha * 0.45 * _env(y, cy)
        if a > 0.01:
            draw.line(f, (cx - 760, y), (rail_x - 20, y), 1.3, WHITE, a)
    for dx, wdt in ((-20, 3.2), (0, 3.2), (36, 2.2)):
        pts = [(rail_x + dx, cy - h / 2 + 40), (rail_x + dx, cy + h / 2 - 40)]
        for i in range(24):
            y0 = lerp(pts[0][1], pts[1][1], i / 24)
            y1 = lerp(pts[0][1], pts[1][1], (i + 1) / 24)
            a = alpha * _env((y0 + y1) / 2, cy)
            if a > 0.01:
                draw.line(f, (rail_x + dx, y0), (rail_x + dx, y1), wdt, WHITE, a)
    for k in range(int(h / 120)):
        y = cy - h / 2 + 60 + k * 120.0
        a = alpha * _env(y, cy)
        if a > 0.01:
            draw.rect(f, rail_x - 26, y - 12, 26, 24, 2.0, WHITE, a)
    fx.ripples(f, t, rail_x + 70, cy - 700, rail_x + 760, cy + 700, rate=0.9, alpha=0.45 * alpha, squash=0.85, seed=seed)
    for k in range(9):                                                       # current lines on the river
        y = cy - 640 + k * 160 + 30 * math.sin(t * 0.8 + k)
        x0 = rail_x + 120 + 60 * hash01(seed, k)
        draw.line(f, (x0, y), (x0 + 120 + 80 * hash01(seed, k, 1), y + 6), 1.2, WHITE, 0.25 * alpha * _env(y, cy))


def stairs_tile(f, cx, cy, h=1900.0, alpha=0.6):
    """Top-down stairwell: two flights side by side with a landing, a U-shaped handrail."""
    x0, x1, xm = cx - 420.0, cx + 420.0, cx
    top, bot = cy - 620.0, cy + 560.0
    for k in range(17):
        y = lerp(top + 160, bot, k / 16)
        a = alpha * _env(y, cy)
        draw.line(f, (x0, y), (xm - 14, y), 2.0, WHITE, a)
        draw.line(f, (xm + 14, y + 36), (x1, y + 36), 2.0, WHITE, a * 0.8)
    draw.line(f, (x0, top), (x1, top), 2.6, WHITE, alpha)                        # landing edge
    draw.stroke(f, [(xm - 14, bot), (xm - 14, top + 150), (xm + 14, top + 150), (xm + 14, bot)], 3.4, WHITE, alpha)
    draw.stroke(f, [(x0 - 10, bot + 200), (x0 - 10, top - 120), (x1 + 10, top - 120), (x1 + 10, bot + 200)], 2.6, WHITE, alpha * 0.8)
    for k in range(10):                                                          # balusters
        y = lerp(top + 170, bot - 10, k / 9)
        draw.circle(f, (xm - 14, y), 4, 1.4, WHITE, alpha * 0.7)
        draw.circle(f, (xm + 14, y + 20), 4, 1.4, WHITE, alpha * 0.7)


def parking_tile(f, cx, cy, alpha=0.6, seed=4):
    """Top-down parking lot: slanted bay lines, wheel stops, a parked car's edge."""
    for k in range(-4, 6):
        y = cy - 140 + k * 230.0
        a = alpha * _env(y, cy)
        if a <= 0.01:
            continue
        draw.line(f, (cx - 520, y), (cx - 140, y - 120), 4.0, WHITE, a)
        draw.line(f, (cx + 160, y - 120), (cx + 540, y), 4.0, WHITE, a)
        draw.rect(f, cx - 500, y - 70, 70, 16, 1.8, WHITE, a * 0.7, radius=6)
    draw.line(f, (cx - 120, cy - 900), (cx - 120, cy + 900), 2.2, WHITE, alpha * 0.4, dash=(40, 30))
    props.car_top(f, (cx + 420, cy + 240), -90, s=0.62, alpha=alpha * 0.9)


def folder(f, c, angle=0.0, s=1.0, alpha=1.0, flat=1.0, ground_rot=None):
    """A blank case folder: tab at the top-left corner, a second (front cover) edge. No text.
    In the air: rotated by `angle` and squashed by `flat` (tumbling). Lying on the ground:
    pass ground_rot (rotation within the ground plane) - rotated first, then flattened into
    perspective by `flat`."""
    w, h = 76.0 * s, 54.0 * s
    back = [(-w / 2, -h / 2), (-w / 2 + w * 0.06, -h / 2 - 8 * s), (-w / 2 + w * 0.34, -h / 2 - 8 * s),
            (-w / 2 + w * 0.40, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    front = [(-w / 2 + 3 * s, -h / 2 + 7 * s), (w / 2 - 2 * s, -h / 2 + 7 * s), (w / 2, h / 2), (-w / 2, h / 2)]
    if ground_rot is not None:
        def T_(pts):
            q = _xf(pts, (0.0, 0.0), ground_rot)
            return [(c[0] + x, c[1] + y * flat) for x, y in q]
    else:
        def T_(pts):
            return _xf([(x, y * flat) for x, y in pts], c, angle)
    back, front = T_(back), T_(front)
    black_poly(f, back, alpha)
    draw.stroke(f, back, 2.4, WHITE, alpha, closed=True)
    draw.stroke(f, front[:2] + [front[2]], 1.8, WHITE, alpha * 0.8)


def flashlight(f, hand, angle, s=1.0, alpha=1.0, on=1.0, beam_len=900.0, spread=24.0, haze=0.13):
    """Police flashlight (BLUE beam = the law). Returns the lens point."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    back = (hand[0] - ux * 16 * s, hand[1] - uy * 16 * s)
    lens = (hand[0] + ux * 26 * s, hand[1] + uy * 26 * s)
    body = [(back[0] + px * 6 * s, back[1] + py * 6 * s), (lens[0] + px * 8 * s, lens[1] + py * 8 * s),
            (lens[0] - px * 8 * s, lens[1] - py * 8 * s), (back[0] - px * 6 * s, back[1] - py * 6 * s)]
    draw.stroke(f, body, 2.4, WHITE, alpha, closed=True)
    if on > 0:
        draw.circle(f, lens, 6 * s, 1, BLUE, on * alpha, fill_it=True, glow=1.2 * on)
        fx.light_cone(f, lens, angle, spread, beam_len, BLUE, haze * on, glow=0.4 * on)
    return lens


def fast_outline(f, polylines, head_c, head_r, body_w=46.0, line_px=5.0, alpha=0.95):
    """Vector stand-in for fx.chalk_outline during fast, motion-blurred moves (same silhouette:
    white union stroke, then a black inner stroke leaves only the edge)."""
    edge = line_px * f.cam.zoom ** 0.35 / max(f.cam.zoom, 1e-3)          # world units
    ctx = f.ctx
    for col, wd, rr in ((WHITE, body_w, head_r + body_w * 0.45), (BLACK, body_w - 2 * edge, head_r + body_w * 0.45 - edge)):
        ctx.save()
        ctx.set_source_rgba(col[0], col[1], col[2], alpha if col is WHITE else 1.0)
        ctx.set_line_width(wd)
        for pl in polylines:
            ctx.move_to(*pl[0])
            for p in pl[1:]:
                ctx.line_to(*p)
            ctx.stroke()
        ctx.new_sub_path()
        ctx.arc(head_c[0], head_c[1], rr, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
