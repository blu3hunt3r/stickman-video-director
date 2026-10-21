"""Shared helpers for S08 (The Limp), S09 (The Red Umbrella) and S10 (The Jury).

Everything here is a pure function of its arguments (frames render in parallel).
Only shared engine props/sets are used for story objects; these helpers add camera math,
top-down rain, ground texture and small graphic devices (measuring tape, cracks, splashes).
"""
import math
from contextlib import contextmanager

from engine import *


# ----------------------------------------------------------------------------- camera math
def zlerp(z0, z1, k):
    """Zoom interpolation in log space (perceptually even push / pull)."""
    return math.exp(lerp(math.log(z0), math.log(z1), k))


def cam_anchor(world_pt, screen_pt, zoom, rot=0.0):
    """Camera with `zoom`/`rot` that puts world_pt exactly at screen_pt."""
    dx, dy = (screen_pt[0] - W / 2) / zoom, (screen_pt[1] - H / 2) / zoom
    a = math.radians(-rot)
    rx, ry = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
    return Camera(world_pt[0] - rx, world_pt[1] - ry, zoom, rot)


def view_bounds(cam, pad=0.0):
    pts = [cam.to_world(p) for p in ((0, 0), (W, 0), (0, H), (W, H))]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def screen_w(px, zoom):
    """Width argument that renders as `px` screen pixels at this zoom (cancels zoom**0.35)."""
    return px / (zoom ** 0.35)


# ----------------------------------------------------------------------------- rain, top-down
def rain_top_vp(f, t, n=120, seed=3, alpha=0.45, vp=(540.0, 960.0), life=(0.32, 0.55), slow=1.0):
    """Top-down rain in the same style as the S05-S07 crowd shots (scenes/_lib_s05_s07.rain_top),
    replicated here so the S07 -> S08 cut keeps an identical rain texture."""
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
            k0 = 1.0 + 0.9 * (1 - tau) ** 1.6
            k1 = 1.0 + 0.9 * (1 - min(1.0, tau + 0.10)) ** 1.6
            ctx.move_to(vp[0] + (gx - vp[0]) * k0, vp[1] + (gy - vp[1]) * k0)
            ctx.line_to(vp[0] + (gx - vp[0]) * k1, vp[1] + (gy - vp[1]) * k1)
        ctx.set_line_width(f.lw(1.7))
        ctx.set_source_rgba(1, 1, 1, alpha)
        ctx.stroke()


def slabs_top(f, t, alpha=1.0, seed=21, box=None):
    """Wet pavement from straight above in the S07 crowd look (slab joints, ellipse puddles,
    rain rings), extended over a larger world area for camera moves."""
    x0, y0, x1, y1 = box if box else (-400.0, -400.0, 1480.0, 2320.0)
    ctx = f.ctx
    ctx.new_path()
    for k in range(int(math.floor((y0 + 120) / 250)) - 1, int(math.ceil((y1 + 120) / 250)) + 2):
        y = -120 + k * 250
        ctx.move_to(x0, y + 26 * (x0 + 400) / 1880)
        ctx.line_to(x1, y + 26 * (x1 + 400) / 1880)
    ctx.set_line_width(f.lw(1.3))
    ctx.set_source_rgba(1, 1, 1, 0.10 * alpha)
    ctx.stroke()
    ctx.new_path()
    for k in range(int(math.floor((x0 + 60) / 210)) - 1, int(math.ceil((x1 + 60) / 210)) + 2):
        x = -60 + k * 210 + 30 * hash01(seed, k)
        ctx.move_to(x + 30 * (y0 + 400) / 2720, y0)
        ctx.line_to(x - 30 * (y1 + 400) / 2720 + 30 * 400 / 2720, y1)
    ctx.set_line_width(f.lw(1.1))
    ctx.set_source_rgba(1, 1, 1, 0.07 * alpha)
    ctx.stroke()
    for i, (cx, cy, rx, ry) in enumerate(((230, 610, 120, 70), (820, 1190, 150, 86), (420, 1560, 100, 60),
                                          (900, 380, 90, 52), (180, -260, 110, 64), (760, -620, 130, 72))):
        draw.ellipse(f, (cx, cy), rx, ry, 8 * (hash01(seed, i) - 0.5), 1.8, WHITE, 0.32 * alpha)
        draw.ellipse(f, (cx + 6, cy + 4), rx * 0.82, ry * 0.78, 8 * (hash01(seed, i) - 0.5), 1.0, WHITE,
                     0.14 * alpha)


def ripples_top(f, t, box, rate=0.2, seed=9, alpha=0.4, slowmo=1.0, w=1.5):
    """Circular rain rings on a wet surface seen from above (world box)."""
    x0, y0, x1, y1 = box
    n = int(abs((x1 - x0) * (y1 - y0)) / 9000 * rate)
    sm = max(slowmo, 0.05)
    for i in range(n):
        per = (0.55 + 0.7 * hash01(seed, i)) / sm
        u = t / per + hash01(seed, i, 1)
        cyc = math.floor(u)
        tau = u - cyc
        x = x0 + (x1 - x0) * hash01(seed, i, cyc, 2)
        y = y0 + (y1 - y0) * hash01(seed, i, cyc, 3)
        r = 4 + 30 * tau
        draw.circle(f, (x, y), r, w, WHITE, alpha * (1 - tau) ** 1.5)


# ----------------------------------------------------------------------------- crowd (replica)
def crowd_pos(i, t, area=(60.0, -200.0, 1020.0, 2120.0), n=46, seed=1, speed=70.0, R=(46.0, 60.0),
              two_way=True, red=None, slowmo=1.0):
    """Same math as sets.crowd_top for umbrella i -> (x, y, r, rot). Lets the camera track THE
    red umbrella that sets.crowd_top draws (kept in sync with engine/sets.py)."""
    x0, y0, x1, y1 = area
    span = (y1 - y0) + 300
    lane = x0 + (x1 - x0) * hash01(seed, i)
    r = R[0] + (R[1] - R[0]) * hash01(seed, i, 1)
    d = 1 if (not two_way or hash01(seed, i, 2) < 0.6) else -1
    v = speed * (0.75 + 0.5 * hash01(seed, i, 3)) * slowmo
    if red is not None and red.get("index") == i and red.get("reverse"):
        d = -1
    y = y0 - 150 + ((hash01(seed, i, 4) * span + d * v * t) % span)
    x = lane + 10 * fbm1(t * 0.4 + i, seed + i)
    rot = 22.5 * hash01(seed, i, 5) + 6 * fbm1(t * 0.5, seed + 3 * i)
    return x, y, r, rot


# ----------------------------------------------------------------------------- limp walk
class IKLimp:
    """Planted-foot limp walk solved with rig.plant (IK), facing right. Feet are fixed on the
    ground while planted (no sliding by construction). The step that lands the LEFT foot is
    `short`, the one that lands the RIGHT foot is `long` (rig.walk's limp convention); the hip
    dips while the bad LEFT leg carries the weight. Real-time share of the LEFT stance = a.
    Pure function of t. Used for big close-ups: rig.walk(limp>0) snaps the left knee by
    12*limp deg at toe-off and pops the hip backwards (~44 px at s=6.6) at every stance switch."""

    def __init__(self, t0, x0, ground_y, rate, s, short, long, a=0.6, phase0=0.0,
                 dip=None, lift=None, lean=3.0):
        self.t0, self.x0, self.gy, self.rate, self.s = t0, x0, ground_y, rate, s
        self.S, self.Lg, self.a, self.phase0 = short, long, a, phase0
        self.C = short + long
        leg = (rig.SEG["thigh"] + rig.SEG["shin"]) * s
        self.reach = leg * 0.985                 # stance leg nearly straight (inverted pendulum)
        self.dip = dip if dip is not None else 0.05 * leg
        self.lift = lift if lift is not None else 0.11 * leg
        self.lean = lean

    def tau(self, t):
        return self.phase0 + self.rate * (t - self.t0)

    def plant_times(self, t_from, t_to):
        out = []
        T0, T1 = self.tau(t_from), self.tau(t_to)
        for n in range(int(math.floor(T0)) - 1, int(math.ceil(T1)) + 1):
            for frac, side in ((0.0, "l"), (self.a, "r")):
                if T0 <= n + frac <= T1:
                    out.append((self.t0 + (n + frac - self.phase0) / self.rate, side))
        return sorted(out)

    def pose(self, t, arm=1.0):
        tau = self.tau(t)
        n = math.floor(tau)
        u = tau - n
        a = self.a
        XL = self.x0 + n * self.C
        XR = XL + self.Lg
        if u < a:                               # LEFT planted, right swings XR(n-1) -> XR(n)
            k = u / a
            lf = (XL, self.gy)
            ks = ease("inout", k)
            rf = (lerp(XR - self.C, XR, ks), self.gy - self.lift * math.sin(math.pi * k) ** 0.8)
            hip_x = lerp(XL - 0.5 * self.S, XL + 0.5 * self.Lg, k)
            dx = hip_x - lf[0]
            hip_y = self.gy - math.sqrt(max(1.0, self.reach ** 2 - dx * dx)) + self.dip * math.sin(math.pi * k)
        else:                                   # RIGHT planted, left swings XL(n) -> XL(n+1)
            k = (u - a) / (1 - a)
            rf = (XR, self.gy)
            ks = ease("inout", k)
            lf = (lerp(XL, XL + self.C, ks), self.gy - self.lift * 0.8 * math.sin(math.pi * k) ** 0.8)
            hip_x = lerp(XL + 0.5 * self.Lg, XL + self.C - 0.5 * self.S, k)
            dx = hip_x - rf[0]
            hip_y = self.gy - math.sqrt(max(1.0, self.reach ** 2 - dx * dx)) + 0.15 * self.dip * math.sin(math.pi * k)
        ph = (tau % 1.0)
        p = Pose(x=hip_x, y=hip_y, s=self.s, facing=1, lean=self.lean,
                 la=-14 * arm * math.cos(2 * math.pi * ph), ra=14 * arm * math.cos(2 * math.pi * ph),
                 le=16, re=16)
        p = rig.plant(p, "l", lf)
        p = rig.plant(p, "r", rf)
        return p


# ----------------------------------------------------------------------------- graphics
def tape(f, a, b, k, alpha=1.0, w=2.6, unit=16.5, major=5, tick=9.0, cap=18.0, color=WHITE):
    """Measuring line from a to b (world) drawn on to fraction k: tick marks, end caps,
    NO numbers. Ticks are spaced by `unit` so a longer gap visibly carries more ticks."""
    if k <= 0 or alpha <= 0:
        return
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    px, py = -uy, ux
    e = (a[0] + ux * L * k, a[1] + uy * L * k)
    draw.line(f, a, e, w, color, alpha)
    draw.line(f, (a[0] - px * cap, a[1] - py * cap), (a[0] + px * cap, a[1] + py * cap), w, color, alpha)
    n = int(L / unit)
    for m in range(1, n + 1):
        d = m * unit
        if d > L * k:
            break
        tl = tick * (1.9 if m % major == 0 else 1.0)
        q = (a[0] + ux * d, a[1] + uy * d)
        draw.line(f, q, (q[0] + px * tl, q[1] + py * tl), w * 0.62, color, alpha * 0.9)
    if k >= 1:
        draw.line(f, (b[0] - px * cap, b[1] - py * cap), (b[0] + px * cap, b[1] + py * cap), w, color, alpha)


def splash_side(f, c, k, s=1.0, alpha=0.85, seed=0, w=2.2):
    """Crown splash where a foot hits a wet ground line (side view). k = 0..1 life."""
    if not (0 <= k < 1):
        return
    a = alpha * (1 - k) ** 1.2
    for m in range(7):
        ang = -90 + (m - 3) * 24 + 8 * (hash01(seed, m) - 0.5)
        d0 = (10 + 50 * k) * s
        d1 = d0 + (16 + 26 * hash01(seed, m, 1)) * s * (1 - 0.5 * k)
        rr = math.radians(ang)
        p0 = (c[0] + math.cos(rr) * d0, c[1] + math.sin(rr) * d0 * 0.8 + 40 * s * k * k)
        p1 = (c[0] + math.cos(rr) * d1, c[1] + math.sin(rr) * d1 * 0.8 + 60 * s * k * k)
        draw.line(f, p0, p1, w, WHITE, a)
    draw.ellipse(f, (c[0], c[1] + 6 * s), (20 + 90 * k) * s, (5 + 16 * k) * s, 0, w * 0.8, WHITE, a * 0.7)


def crack_lines(f, c, r, k, seed=0, alpha=1.0, w=2.0):
    """Shattered-glass cracks radiating from an impact point near c, grown to fraction k."""
    if k <= 0:
        return
    imp = (c[0] + r * 0.28, c[1] - r * 0.22)
    for m in range(9):
        ang = m * 40 + 25 * (hash01(seed, m) - 0.5)
        L = r * (0.45 + 0.75 * hash01(seed, m, 1)) * k
        pts = [imp]
        segs = 4
        for q in range(1, segs + 1):
            d = L * q / segs
            jit = (hash01(seed, m, q) - 0.5) * 22
            rr = math.radians(ang + jit)
            pts.append((imp[0] + math.cos(rr) * d, imp[1] + math.sin(rr) * d))
        draw.stroke(f, pts, w, WHITE, alpha)
    if k > 0.4:
        kk = clamp((k - 0.4) / 0.6)
        draw.circle(f, imp, r * 0.12 * kk, w * 0.8, WHITE, alpha * 0.9)
        draw.arc(f, imp, r * 0.3 * kk, 200, 330, w * 0.7, WHITE, alpha * 0.7)


@contextmanager
def glow_scaled(f, k):
    """Scale the emissive (glow-layer) contribution of everything drawn inside by k. A prop
    that fills the whole frame would otherwise bloom into a washed-out pink."""
    f.g.push_group()
    try:
        yield
    finally:
        pat = f.g.pop_group()
        if k > 0:
            f.g.set_source(pat)
            f.g.paint_with_alpha(clamp(k))


@contextmanager
def mirrored_x(f, x0):
    """Mirror everything drawn inside about the world vertical line x = x0 (main + glow).
    Used to point a right-facing prop (the revolver) to the left without turning it upside down."""
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


def stripes(c, ang, n, period, duty, length, offset=0.0):
    """Parallel light bands (blind light) centred on c, running along `ang` (deg)."""
    a = math.radians(ang)
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


def fit_clip(f, c, r):
    """Clip helper for a circular window (world coords)."""
    return f.clipped(lambda ctx: ctx.arc(c[0], c[1], max(0.5, r), 0, 2 * math.pi))
