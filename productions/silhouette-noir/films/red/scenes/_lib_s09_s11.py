"""Shared helpers for RED s09 DAWN, s10 MONSTER and s11 GRANDMOTHER'S HOUSE.

    CamPath     keyed camera (x, y, zoom) with per-key eases, zoom interpolated in log space
    kneel()     Actor segment: go down onto both knees (IK legs, feet planted), then kneel
    WolfRig     a Wolf evaluated on its own clock (scene t + offset) + head points (muzzle,
                eye) for reaches and glows
    cane()      Old Red's cane, a prop line from her hand to the snow
    taper()     a lighting taper with a small flame (emissive)
    rim()       a warm rim light on a silhouette (offset copy drawn behind it)
    forest_edge trunks for the s10 forest edge (the village set stops at the gate)
    Bass ending s01's path meander, the cut-paper band and the red hood triangle (the s11
                ending rhymes with s01 exactly: same line, same triangle, same paper)

Everything is a pure function of t and integer seeds.
"""
import copy
import math
from functools import lru_cache

from engine import bass, draw
from engine.core import clamp, ease, hash01, lerp, noise1
from engine.creatures import Wolf, solve_quadruped, _head_pts, _EYE
from engine.figure import Pose
from engine.frame import Camera
from films.red.sets_common import glow, mix, SNOW

D2R = math.pi / 180.0


def k01(t, t0, dur, e="inout"):
    """0 before t0, 1 after t0 + dur, eased in between."""
    if t <= t0:
        return 0.0
    if t >= t0 + dur:
        return 1.0
    return ease(e, (t - t0) / dur)


# ============================================================================ camera
class CamPath:
    """keys: [(t, x, y, zoom), (t, x, y, zoom, ease), ...] - the ease shapes the move INTO
    that key from the previous one (default inout). Zoom moves in log space, so a push-in
    feels even. Holds before the first and after the last key."""

    def __init__(self, keys):
        self.keys = [(k[0], k[1], k[2], math.log(k[3]), k[4] if len(k) > 4 else "inout") for k in keys]

    def at(self, t):
        K = self.keys
        if t <= K[0][0]:
            k = K[0]
            return Camera(k[1], k[2], math.exp(k[3]))
        for a, b in zip(K, K[1:]):
            if t <= b[0]:
                u = ease(b[4], (t - a[0]) / max(b[0] - a[0], 1e-6))
                return Camera(lerp(a[1], b[1], u), lerp(a[2], b[2], u), math.exp(lerp(a[3], b[3], u)))
        k = K[-1]
        return Camera(k[1], k[2], math.exp(k[3]))


# ============================================================================ kneeling
def kneel(actor, t0, dur, x=None, t_in=1.0, lean=14.0, head=8.0, delay=(0.0, 0.22), spread=0.05,
          arms=(18.0, 38.0)):
    """Go down onto both knees from standing, starting at t0 (t_in seconds), and kneel until
    t0 + dur. x: the pelvis x when kneeling (default: where the actor stands). Feet stay
    planted until the knees take the weight, then fold back under (shins flat on the snow).
    lean/head: trunk pitch and head nod when down. delay: when each leg (far, near) starts
    to fold (fractions of t_in). Channels (reach, look_at, key) layer on top as usual."""
    A = actor
    st = A.state
    yaw = st["yaw"]
    d = 1.0 if math.cos(yaw * D2R) >= 0 else -1.0
    Hh, b, g = A.H, A.body, A.g
    x0 = st["x"]
    xk = x0 if x is None else float(x)
    feet = dict(st["feet"])
    y_st = g(x0) - (b.hip - 0.006) * Hh
    y_kn = g(xk) - (b.thigh + 0.028) * Hh
    seed = A.seed

    def path(t):
        u = ease("inout", clamp((t - t0) / t_in))
        xx = lerp(x0, xk, u)
        yy = lerp(y_st, y_kn, u) + 0.018 * Hh * math.sin(math.pi * u)
        yy += 0.0025 * Hh * math.sin(2 * math.pi * t / 3.3 + seed) * u          # breathing
        return xx, yy

    def pose(t, u_):
        u = clamp((t - t0) / t_in)
        ue = ease("inout", u)
        p = Pose(0.0, 0.0, yaw)
        for i, s in enumerate(("L", "R")):
            w = ease("inout", clamp((u - delay[i]) / 0.62))
            fx0 = feet[s]
            a0 = (fx0, g(fx0) - b.ankle_h * Hh)
            off = (spread * Hh) * (1 if i else -1) * 0.5
            kx = xk - d * 0.90 * b.shin * Hh + d * off
            a1 = (kx, g(kx) - 0.048 * Hh)
            lift = 0.035 * Hh * math.sin(math.pi * w)
            p.legs[s] = {"ik": (lerp(a0[0], a1[0], w), lerp(a0[1], a1[1], w) - lift),
                         "pitch": lerp(0.0, -168.0, ease("in", w)), "toe": 0.0, "abd": 3.0}
        br = math.sin(2 * math.pi * t / 3.3 + seed)
        p.pitch = lean * ue
        p.spine = [2.0 * ue + 0.5 * br * ue, 3.0 * ue, 3.0 * ue - 0.6 * br * ue]
        p.head = head * ue + 1.2 * noise1(t * 0.2, seed + 4) * ue
        for s, k in (("L", 1.0), ("R", 0.85)):
            p.arms[s] = dict(sh=lerp(4.0, arms[0] * k, ue), abd=6.0, elbow=lerp(12.0, arms[1], ue), wrist=6.0, grip=0.35)
        return p

    return A.free(dur, path, pose, at=t0, end_x=xk, blend=0.25)


# ============================================================================ the wolf
class WolfRig:
    """A Wolf evaluated on its own clock: wolf time = scene t + off (so it can already be
    lying when the scene starts). head(t) -> dict(tip, bridge, eye, crown) world points."""

    def __init__(self, wolf, off=0.0):
        self.w = wolf
        self.off = float(off)

    def wt(self, t):
        return t + self.off

    def draw(self, f, t, ctx, **kw):
        return self.w.draw(f, self.wt(t), ctx, **kw)

    def head(self, t):
        return _wolf_head(self.w, round(self.wt(t), 5))


_HEAD_CACHE = {}


def _wolf_head(w, wt):
    key = (id(w), wt)
    r = _HEAD_CACHE.get(key)
    if r is None:
        P = w.state(wt)
        R = solve_quadruped(w, P)
        Lh = w.PR["head"] * w.S
        tip, nose, bridge, eye, crown, chin = _head_pts(
            R, [(1.0, 0.02), (0.90, 0.075), (0.78, 0.10), _EYE, (0.2, 0.25), (0.75, -0.1)], Lh)
        r = dict(tip=tip, nose=nose, bridge=bridge, eye=eye, crown=crown, chin=chin, P=P)
        if len(_HEAD_CACHE) > 256:
            _HEAD_CACHE.clear()
        _HEAD_CACHE[key] = r
    return r


def eye_flare(f, pos, amount, size=1.0, color=(1.0, 0.97, 0.9)):
    """A soft emissive bloom on an opening eye (on top of the wolf's own eye dot)."""
    if amount <= 0.01:
        return
    with f.emit() as G:
        glow(G, pos, 15.0 * size, color, 0.4 * amount)
        glow(G, pos, 42.0 * size, color, 0.14 * amount)


# ============================================================================ props
def cane(ctx, hand, ground, length, lean=8.0, color=(0.012, 0.012, 0.012), width=7.0, d=1.0):
    """Old Red's cane: a thin stick from the hand (crook handle over the fist) to the snow.
    If the snow is within reach the tip rests on it (the cane tilts to fit); otherwise it
    hangs at `lean` deg. d: the facing (+1 right, -1 left): the crook curls toward it."""
    hx, hy = hand
    gy = ground(hx)
    drop = gy - hy
    if 0 < drop < length:
        s = math.sqrt(max(length * length - drop * drop, 0.0))
        tip = (hx + d * s * 0.6, ground(hx + d * s * 0.6))
        dx, dy = tip[0] - hx, tip[1] - hy
        n = math.hypot(dx, dy) or 1.0
        tip = (hx + dx / n * length, hy + dy / n * length)
    else:
        a = lean * D2R
        tip = (hx + d * math.sin(a) * length, hy + math.cos(a) * length)
    top = (hx, hy - 0.06 * length)
    # the shaft (tapered), the crook (an arc over the fist) and the ferrule
    nx, ny = tip[0] - top[0], tip[1] - top[1]
    L = math.hypot(nx, ny) or 1.0
    px, py = -ny / L, nx / L
    w0, w1 = width * 0.55, width * 0.42
    draw.poly(ctx, [(top[0] + px * w0, top[1] + py * w0), (tip[0] + px * w1, tip[1] + py * w1),
                    (tip[0] - px * w1, tip[1] - py * w1), (top[0] - px * w0, top[1] - py * w0)])
    draw.fill(ctx, color)
    ctx.save()
    ctx.set_line_width(width)
    cx = top[0] + d * 0.05 * length
    if d > 0:
        ctx.arc(cx, top[1], 0.05 * length, math.pi, 2 * math.pi)
    else:
        ctx.arc_negative(cx, top[1], 0.05 * length, 0.0, -math.pi)
    ctx.set_source_rgb(*color)
    ctx.stroke()
    ctx.restore()
    return tip


def taper(f, ctx, hand, angle, length=58.0, flame=1.0, t=0.0, mood=None, color=(0.012, 0.012, 0.012)):
    """A lighting taper held in the fist, pointing at `angle` deg (0 = up, + toward +x),
    with a small flame at its tip (emissive). Returns the flame position."""
    a = angle * D2R
    tip = (hand[0] + math.sin(a) * length, hand[1] - math.cos(a) * length)
    ctx.save()
    ctx.set_line_width(4.0)
    ctx.move_to(hand[0] - math.sin(a) * 6, hand[1] + math.cos(a) * 6)
    ctx.line_to(*tip)
    ctx.set_source_rgb(*color)
    ctx.stroke()
    ctx.restore()
    if flame > 0.01:
        fl = flame * (0.85 + 0.15 * noise1(t * 9.0, 77))
        fx, fy = tip[0] + math.sin(a) * 6, tip[1] - math.cos(a) * 6 - 4
        lamp = mood.lamp if mood is not None else (1.0, 0.62, 0.26)
        draw.ellipse(ctx, (fx, fy), 4.2 * fl, 9.0 * fl)
        draw.fill(ctx, mix(SNOW, lamp, 0.25))
        with f.emit() as G:
            glow(G, (fx, fy), 26.0, lamp, 0.8 * fl)
            glow(G, (fx, fy), 80.0, lamp, 0.22 * fl)
        return (fx, fy)
    return tip


def rim_look(look):
    """A copy of a Look with every costume color removed (for one-color passes)."""
    lk = copy.copy(look)
    lk.colors = {}
    return lk


def rim(f, par, fn, dx, dy, color, alpha=1.0, blur=3.0):
    """Warm rim light: fn(ctx, color) draws the silhouette in one color; it is drawn offset
    by (dx, dy) toward the light, softly, BEFORE the real silhouette covers all but its edge."""
    with f.layer(par=par, blur=blur, alpha=alpha) as c:
        c.save()
        c.translate(dx, dy)
        fn(c, color)
        c.restore()


# ============================================================================ s10 forest edge
@lru_cache(maxsize=4)
def edge_trunks(seed=5, x0=1150.0, x1=4200.0):
    """Tall winter trunks for the forest edge beyond the gate: [(x, width, lean, branches)]."""
    out = []
    x = x0
    k = 0
    while x < x1:
        w = 46.0 + 40.0 * hash01(seed, k, 1)
        lean = (hash01(seed, k, 2) - 0.5) * 3.0
        br = []
        for j in range(3 + int(hash01(seed, k, 3) * 3)):
            h = 380.0 + 260.0 * j + 120.0 * hash01(seed, k, j, 4)
            side = 1 if hash01(seed, k, j, 5) > 0.5 else -1
            br.append((h, side, 140.0 + 200.0 * hash01(seed, k, j, 6), 30.0 + 30.0 * hash01(seed, k, j, 7)))
        out.append((x, w, lean, tuple(br)))
        x += 230.0 + 260.0 * hash01(seed, k, 8) * (1.0 + 0.8 * (x - x0 < 500))
        k += 1
    return tuple(out)


def draw_trunks(c, trunks, ground, color, top=-3000.0, snow=None):
    """Fill the trunks (+ bare branches and a little snow on them) on a plane context."""
    for (x, w, lean, br) in trunks:
        gy = ground(x)
        tl = math.tan(lean * D2R)
        hb = gy - top
        draw.poly(c, [(x - w / 2, gy + 30), (x - w * 0.34 + tl * hb, top), (x + w * 0.34 + tl * hb, top),
                      (x + w / 2, gy + 30)])
        for (h, side, L, ang) in br:
            px = x + tl * h
            py = gy - h
            a = (90.0 - ang) * D2R
            ex, ey = px + side * math.cos(a) * L, py - math.sin(a) * L
            r = w * 0.10
            draw.poly(c, [(px, py - r), (ex, ey), (px, py + r * 1.6)])
    draw.fill(c, color)
    if snow is not None:
        for (x, w, lean, br) in trunks:
            gy = ground(x)
            draw.ellipse(c, (x, gy + 6), w * 1.35, w * 0.32)
        draw.fill(c, snow)


# ============================================================================ the Bass ending (s01 rhyme)
CX = 540.0              # s01's path centre line
Y_STOP = 980.0          # where s01's triangle stops on [leave]
HOOD_K = 0.85           # s01's top-down hood scale


def meander(y):
    """s01's path meander (identical formula: the s11 ending lands exactly on s01's line)."""
    return 92.0 * math.sin(y / 265.0 + 0.4) + 30.0 * math.sin(y / 118.0 + 1.3)


def path_x(y):
    return CX + meander(y)


def path_pts(y0=-60.0, y1=Y_STOP, step=12.0):
    n = max(1, int((y1 - y0) / step))
    return [(path_x(y0 + (y1 - y0) * i / n), y0 + (y1 - y0) * i / n) for i in range(n + 1)]


def path_tangent_deg(y):
    """Direction of travel down s01's path at y (degrees, atan2 of (dx, dy))."""
    d = 2.0
    return math.degrees(math.atan2(2 * d, path_x(y + d) - path_x(y - d)))


@lru_cache(maxsize=2)
def hood_cloak():
    """s01's red triangle: the 'accent' parts of bass.cutout_parts('hood', 3)."""
    return [p for r, p in bass.cutout_parts("hood", 3) if r == "accent"]


def draw_triangle(c, pos, ang_deg, k, color, rock=0.0):
    """The cloak triangle as s01 draws it: centre `pos`, local tip up rotated by ang_deg
    (s01: travel tangent + 90), scale k (s01: 0.85), the local centre at (0, -62)."""
    c.save()
    c.translate(*pos)
    c.rotate(math.radians(ang_deg + rock))
    c.scale(k, k)
    c.translate(0.0, 62.0)
    bass.fill_polys(c, hood_cloak(), color)
    c.restore()


def resample(pts, n):
    """n points evenly spaced by arc length along a polyline."""
    if len(pts) < 2:
        return [pts[0]] * n if pts else []
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    tot = sum(seg) or 1.0
    out = []
    i, acc = 0, 0.0
    for k in range(n):
        s = tot * k / (n - 1)
        while i < len(seg) - 1 and acc + seg[i] < s:
            acc += seg[i]
            i += 1
        u = (s - acc) / (seg[i] or 1.0)
        a, b_ = pts[i], pts[i + 1]
        out.append((a[0] + (b_[0] - a[0]) * u, a[1] + (b_[1] - a[1]) * u))
    return out


def smooth_pts(pts, passes=2):
    """Chaikin corner cutting (keeps the ends)."""
    for _ in range(passes):
        if len(pts) < 3:
            return pts
        out = [pts[0]]
        for a, b_ in zip(pts, pts[1:]):
            out.append((0.75 * a[0] + 0.25 * b_[0], 0.75 * a[1] + 0.25 * b_[1]))
            out.append((0.25 * a[0] + 0.75 * b_[0], 0.25 * a[1] + 0.75 * b_[1]))
        out.append(pts[-1])
        pts = out
    return pts

