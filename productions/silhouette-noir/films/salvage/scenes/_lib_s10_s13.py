"""Shared helpers for SALVAGE s10 (own_hand), s11 (two_tugs) and s13 (one_breath).

Everything is a pure function of its arguments (plus caches of deterministic data):
  * Sampled / track / bump   time helpers (cache a function of t; eased keys; envelopes)
  * draw_hose / draw_pale    the red air hose and the pale lifting line as smooth bands
  * helmet_valve / port_center   Mark V helmet points (exhaust valve, the port glass)
  * port_eyes                Limbo eyes that can also look UP / DOWN inside the port
  * screen_glow / screen_band   soft screen-space light (backlight behind a silhouette)
  * pulses_offset            transverse kinks running along a line (the two tugs)
  * streaks                  particles smeared by a fast camera move (the ascents)
"""
import math

import cairo
import numpy as np

from engine import costume, draw
from engine import figure as F
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.palette import PAPER, RED, SALVAGE

PAL = SALVAGE
INK = PAL.ink
D2R = math.pi / 180.0


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# the pale lifting line: rope, pale against the dark water (a story object, like the hose)
LINE_C = mix(PAPER, PAL.surface, 0.30)
HOSE_W = 10.0
LINE_W = 6.0


# ----------------------------------------------------------------------------- time
class Sampled:
    """fn(t) -> tuple/float sampled on [t0, t1] at `hz`, linearly interpolated (built lazily,
    once per process). For things a rope simulation or an emitter asks for many times."""

    def __init__(self, fn, t0, t1, hz=60.0):
        self.fn, self.t0, self.t1, self.hz = fn, float(t0), float(t1), float(hz)
        self._tab = None

    def _build(self):
        n = int(math.ceil((self.t1 - self.t0) * self.hz)) + 2
        ts = self.t0 + np.arange(n) / self.hz
        self._tab = np.array([np.atleast_1d(np.asarray(self.fn(float(t)), np.float64)) for t in ts])

    def __call__(self, t):
        if self._tab is None:
            self._build()
        x = (min(max(t, self.t0), self.t1) - self.t0) * self.hz
        i = min(int(x), len(self._tab) - 2)
        u = x - i
        v = self._tab[i] * (1.0 - u) + self._tab[i + 1] * u
        return tuple(float(a) for a in v) if v.size > 1 else float(v[0])


def track(keys, t):
    """Piecewise interpolation through [(t, value, ease_into_key)]; values are floats or
    tuples (ease names: engine.core.ease)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            t0, v0 = keys[i - 1][0], keys[i - 1][1]
            t1, v1 = keys[i][0], keys[i][1]
            e = keys[i][2] if len(keys[i]) > 2 else "inout"
            u = ease(e, (t - t0) / max(t1 - t0, 1e-9))
            if isinstance(v0, tuple):
                return tuple(lerp(a, b, u) for a, b in zip(v0, v1))
            return lerp(v0, v1, u)
    return keys[-1][1]


def bump(t, t0, t1, t2, t3):
    """0 before t0, smooth rise to 1 at t1, hold, smooth fall to 0 at t3 (t2 = fall start)."""
    return smoothstep(t0, t1, t) * (1.0 - smoothstep(t2, t3, t))


def ss(a, b, x):
    return smoothstep(a, b, x)


# ----------------------------------------------------------------------------- bands
def stroke(ctx, pts, width, color, alpha=1.0, smooth=True):
    """A round-capped stroke through pts (Catmull-Rom smoothed when smooth)."""
    if len(pts) < 2:
        return
    ctx.save()
    ctx.new_path()
    if smooth and len(pts) >= 3:
        draw.smooth(ctx, pts, close=False, tension=0.5)
    else:
        draw.poly(ctx, pts, close=False)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(color[0], color[1], color[2], alpha)
    ctx.stroke()
    ctx.restore()


def draw_hose(ctx, pts, width=HOSE_W, color=RED, alpha=1.0):
    stroke(ctx, pts, width, color, alpha)


def draw_pale(ctx, pts, width=LINE_W, color=LINE_C, alpha=1.0):
    stroke(ctx, pts, width, color, alpha)


def polyline_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def resample(pts, n):
    """n points evenly spaced by arc length along a polyline."""
    P = np.asarray(pts, np.float64)
    if len(P) < 2:
        return [tuple(P[0])] * n
    seg = np.linalg.norm(P[1:] - P[:-1], axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    if s[-1] <= 1e-9:
        return [tuple(P[0])] * n
    u = np.linspace(0.0, s[-1], n)
    x = np.interp(u, s, P[:, 0])
    y = np.interp(u, s, P[:, 1])
    return list(zip(x.tolist(), y.tolist()))


def pulses_offset(s, t, hits, speed=1500.0, width=70.0, amp=22.0, decay=1.3):
    """Sideways offset of a line at arc length s (from the hands) for tug pulses: each hit
    (t0, gain) launches a kink that runs along the line at `speed` px/s and fades."""
    out = 0.0
    for t0, g in hits:
        tau = t - t0
        if tau <= 0.0:
            continue
        c = speed * tau
        d = (s - c) / width
        if abs(d) > 3.0:
            continue
        out += g * amp * math.exp(-d * d) * math.sin(2.2 * d) * math.exp(-decay * tau) * min(1.0, tau / 0.05)
    return out


# ----------------------------------------------------------------------------- the helmet
def helmet_valve(sk):
    """World point just above the helmet's top valve (where the exhaust bubbles leave)."""
    c, R, vp, vr, inlet = costume.helmet_frame(sk)
    w = sk.side_w
    fwd = 1.0 if math.cos((sk.pose.yaw + sk.pose.head_yaw) * D2R) >= 0 else -1.0
    return (c[0] + fwd * R * 0.35 * (1 - w) - 0.18 * R * w, c[1] - R * 1.05)


def port_center(sk):
    """(centre, radius) of the helmet's front glass (where the eyes glow)."""
    c, R, vp, vr, inlet = costume.helmet_frame(sk)
    fwd = 1.0 if math.cos((sk.pose.yaw + sk.pose.head_yaw) * D2R) >= 0 else -1.0
    w = sk.side_w
    port_c = lerp((c[0] + fwd * R * 0.98, vp[1]), vp, w)
    return (lerp(vp[0], port_c[0], 0.5), lerp(vp[1], port_c[1], 0.5)), vr


def port_eyes(f, ctx, sk, look=(0.0, 0.0), open_=1.0, glow=1.0, color=(1.0, 1.0, 0.97), size=1.0,
              halo=1.0, clip=True):
    """Limbo eyes in the helmet port that can look in any direction: look = (x, y) in
    -1..1 (+y = down) shifts both dots inside the glass. Draw after the figure (called
    with eyes=False). open_ 0..1 squashes them shut; glow dims them."""
    e1, e2, r, w, front = F.eye_points(sk)
    if front < -0.35 or open_ <= 0.02 or glow <= 0.01:
        return
    vis = clamp((front + 0.35) / 0.35) if front < 0 else 1.0
    (pc, pr) = port_center(sk)
    gx, gy = look[0] * pr * 0.30, look[1] * pr * 0.34
    r *= size
    pts = [(e1[0] + gx, e1[1] + gy), (e2[0] + gx, e2[1] + gy)]
    g = glow * vis
    ctx.save()
    if clip:
        draw.circle(ctx, pc, pr * 0.97)
        ctx.clip()
    for i, e in enumerate(pts):
        rr = r * (1.0 if i == 0 else lerp(0.82, 1.0, w))
        draw.ellipse(ctx, e, rr * 0.9, max(rr * clamp(open_), 0.3))
        draw.fill(ctx, color, clamp(g))
    ctx.restore()
    if f is not None and halo > 0:
        with f.emit() as G:
            for e in pts:
                draw.glow_disc(G, e, r * 5.5, color, 0.5 * g * clamp(open_) * halo)


# ----------------------------------------------------------------------------- arm solver
_ARM_KEYS = ("sh", "abd", "elbow")
_ARM_LIM = {"sh": (-80.0, 200.0), "abd": (-12.0, 95.0), "elbow": (0.0, 150.0)}


def solve_arm(p, side, target, body, iters=10, lam=6.0, tol=0.6):
    """Put the wrist of arm `side` on a world target in ANY view (motion.arm_ik works in the
    profile plane only): damped least squares on (sh, abd, elbow) through figure.solve,
    starting from the pose's current arm. Deterministic for a given pose and target."""
    arm = p.arms[side]
    x = np.array([arm.get(k, 0.0) for k in _ARM_KEYS], np.float64)
    tgt = np.asarray(target, np.float64)

    def wrist(xv):
        for k, v in zip(_ARM_KEYS, xv):
            arm[k] = float(v)
        return np.asarray(F.solve(p, body).j["wrist_" + side], np.float64)

    for _ in range(iters):
        w0 = wrist(x)
        err = tgt - w0
        if math.hypot(err[0], err[1]) < tol:
            break
        J = np.empty((2, 3))
        for j in range(3):
            d = np.zeros(3)
            d[j] = 1.0
            J[:, j] = wrist(x + d) - w0
        x = x + J.T @ np.linalg.solve(J @ J.T + lam * np.eye(2), err)
        for j, k in enumerate(_ARM_KEYS):
            lo, hi = _ARM_LIM[k]
            x[j] = min(max(x[j], lo), hi)
    wrist(x)
    return p


# ----------------------------------------------------------------------------- screen light
def _screen_ctx(A):
    A.save()
    A.identity_matrix()
    A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)


def screen_glow(f, c, r, color, a, par=0.0, blur=30.0, core=0.0, squash=1.0):
    """A soft additive pool of light in SCREEN space (a backlight behind a silhouette)."""
    if a <= 0.002:
        return
    with f.light(par=par, blur=blur) as A:
        _screen_ctx(A)
        if squash != 1.0:
            A.translate(c[0], c[1])
            A.scale(1.0, squash)
            A.translate(-c[0], -c[1])
        draw.glow_disc(A, c, r, color, a, core)
        A.restore()


def screen_band(f, y0, y1, color, a0, a1, blur=0.0, x0=0.0, x1=W):
    """Additive vertical gradient band (screen space): a0 at y0 -> a1 at y1."""
    if max(a0, a1) <= 0.002:
        return
    with f.light(par=0.0, blur=blur) as A:
        _screen_ctx(A)
        draw.linear(A, (0, y0), (0, y1), [(0, color, a0), (1, color, a1)])
        A.rectangle(x0, min(y0, y1), x1 - x0, abs(y1 - y0))
        A.fill()
        A.restore()


def screen_dark(f, c, r, a, blur=40.0, squash=1.0, color=None):
    """A soft pool of darkness painted over the frame (screen space, normal blend): deep
    shadow under a hull, a vignette around a subject."""
    if a <= 0.002:
        return
    col = color or INK
    with f.screen() as S:
        S.save()
        if squash != 1.0:
            S.translate(c[0], c[1])
            S.scale(1.0, squash)
            S.translate(-c[0], -c[1])
        draw.radial(S, c, 0, r, [(0, col, a), (0.55, col, a * 0.85), (1, col, 0.0)])
        S.arc(c[0], c[1], r, 0, 2 * math.pi)
        S.fill()
        S.restore()


# ----------------------------------------------------------------------------- particles
def streaks(f, t, vel, n=90, seed=3, color=None, alpha=0.5, size=1.6, depth=(0.35, 1.6), exposure=1.0 / 30.0,
            box_pad=200.0):
    """Floating specks smeared by the camera's motion: vel = (vx, vy) the camera velocity
    in world px/s at the action plane. Each speck sits at a random depth (parallax); its
    screen motion over `exposure` s is drawn as a soft streak. Screen space, additive."""
    col = color or mix(PAL.surface, (1.0, 1.0, 1.0), 0.3)
    cam = f.cam
    with f.light(par=0.0, blur=0.0) as A:
        _screen_ctx(A)
        A.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(n):
            par = lerp(depth[0], depth[1], hash01(seed, i, 1) ** 1.3)
            k = cam.zoom * par
            # world-anchored position in a tiled box that follows the camera (parallax)
            span_x, span_y = (W + 2 * box_pad), (H + 2 * box_pad)
            px = hash01(seed, i, 2) * span_x + 9.0 * math.sin(0.4 * t + 6.0 * hash01(seed, i, 5))
            py = hash01(seed, i, 3) * span_y + 14.0 * t * (0.5 + hash01(seed, i, 6))
            sx = (px - cam.x * k) % span_x - box_pad
            sy = (py - cam.y * k) % span_y - box_pad
            dx, dy = -vel[0] * k * exposure, -vel[1] * k * exposure
            r = size * (0.6 + 1.4 * hash01(seed, i, 4) ** 3) * par * f.scale ** 0
            a = alpha * (0.35 + 0.65 * hash01(seed, i, 7)) * min(1.0, 1.2 / (0.4 + abs(par - 1.0) * 1.5))
            L = math.hypot(dx, dy)
            A.set_line_width(max(r * 2.0, 0.8))
            A.move_to(sx, sy)
            A.line_to(sx + dx + 0.01, sy + dy + 0.01)
            A.set_source_rgba(col[0], col[1], col[2], clamp(a / (1.0 + L / (8.0 * r + 4.0)) ** 0.5 * 0.9))
            A.stroke()
        A.restore()
