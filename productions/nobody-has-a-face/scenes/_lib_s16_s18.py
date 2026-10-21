"""Shared helpers for S16 (The Lineup, Again), S17 (Habits Can Be Learned) and S18 (Your Verdict).

Everything here is a pure function of its arguments (no state between frames).
Only white line art + the three story accents (AMBER light/clues, CRIMSON killer, BLUE law).
"""
import math
from contextlib import contextmanager

import cairo
import numpy as np

from engine import *
from engine.core import W, H
from engine.frame import _array_to_surface, _surface_to_array

# ----------------------------------------------------------------------------- boundary numbers
RING_R = 200.0                                   # S16 OUT / S17 IN: head ring radius on screen
RING_S = 1.12                                    # the detective's scale when the push ends (walk line)
RING_W = rig.FIG_LW * RING_S ** 0.5 * (RING_R / (rig.SEG["head_r"] * RING_S)) ** 0.35   # ~14 px on screen


# ----------------------------------------------------------------------------- math / camera
def ek(name, t0, t1, t):
    """Eased 0..1 progress of t through [t0, t1]."""
    return ease(name, inv_lerp(t0, t1, t))


def log_zoom(z0, z1, k):
    """Zoom interpolation that feels linear to the eye (constant relative speed)."""
    return math.exp(lerp(math.log(z0), math.log(z1), k))


def cam_put(world_pt, screen_pt, zoom, rot=0.0):
    """Camera that shows world_pt at screen_pt with the given zoom/roll."""
    dx, dy = (screen_pt[0] - W / 2) / zoom, (screen_pt[1] - H / 2) / zoom
    if rot:
        dx, dy = rotate((dx, dy), -rot)
    return Camera(world_pt[0] - dx, world_pt[1] - dy, zoom, rot)


def cam_lerp(a, b, k, kz=None):
    """Blend two cameras (position linear, zoom logarithmic)."""
    kz = k if kz is None else kz
    return Camera(lerp(a.x, b.x, k), lerp(a.y, b.y, k), log_zoom(a.zoom, b.zoom, kz), lerp(a.rot, b.rot, k))


def tglob(T, t):
    """Global film time (keeps flicker / breathing noise continuous across scene cuts)."""
    return T.start + t


# ----------------------------------------------------------------------------- re-timed walk
def limp_stance(limp):
    """Fraction of rig.walk's cycle spent on the injured LEFT leg (mirrors engine/rig.py walk():
    m = 0.5 - 0.10 * limp; the left foot lands at phase n, the right foot at n + m)."""
    return 0.5 - 0.10 * limp


class Gait:
    """rig.walk (planted feet, the engine's own limp) driven by an explicit footfall schedule.

    Every landing gets an exact time, so footfalls can sit on narration words, cuts and SFX
    cues. h counts landings: the LEFT foot lands at even h, the right foot at odd h. h is
    mapped onto rig.walk's phase (left lands at P = n, right at P = n + m), and the walk is
    evaluated as rig.walk(t=0, speed=0, phase0=P), so the pose, knee curve and planted feet
    are exactly the engine's.
      d_right: duration of the interval that ends with the RIGHT foot landing (the stance on
               the injured left leg - quick when limping)
      d_left : duration of the interval that ends with the LEFT foot landing
    Pass cycle=seconds instead to use the engine's natural limp ratio (m : 1 - m)."""

    def __init__(self, x0, ground_y, s=1.0, facing=1, limp=0.0, stride=1.0, arm=1.0, lean=0.0,
                 head=0.0, t0=0.0, h0=0.0, d_left=None, d_right=None, cycle=0.84, t_stop=None):
        self.x0, self.gy, self.s, self.facing = x0, ground_y, s, facing
        self.limp, self.stride, self.arm, self.lean, self.head = limp, stride, arm, lean, head
        self.m = limp_stance(limp)
        self.dr = d_right if d_right is not None else cycle * self.m
        self.dl = d_left if d_left is not None else cycle * (1.0 - self.m)
        self.t0, self.h0 = t0, h0
        self.t_stop = t_stop

    def _dur(self, j):
        # interval [j, j+1) ends with the RIGHT foot landing when j+1 is odd
        return self.dr if (j + 1) % 2 == 1 else self.dl

    def h(self, t):
        if self.t_stop is not None:
            t = min(t, self.t_stop)
        rem = t - self.t0
        h = self.h0
        if rem >= 0:
            for _ in range(400):
                j = math.floor(h)
                d = self._dur(j)
                need = (j + 1 - h) * d
                if rem < need:
                    return h + rem / d
                rem -= need
                h = j + 1
            return h
        for _ in range(400):                      # run the schedule backwards
            j = math.ceil(h) - 1
            d = self._dur(j)
            need = (h - j) * d
            if -rem < need:
                return h + rem / d
            rem += need
            h = j
        return h

    def phase(self, h):
        """Landing coordinate h -> rig.walk phase P."""
        n = math.floor(h / 2.0)
        e = h - 2 * n
        return n + (self.m * e if e < 1.0 else self.m + (1.0 - self.m) * (e - 1.0))

    def _walk(self, P):
        return rig.walk(0.0, self.x0, self.gy, 0.0, facing=self.facing, s=self.s, limp=self.limp,
                        stride=self.stride, arm=self.arm, lean=self.lean, head=self.head, phase0=P)

    def pose(self, t):
        return self._walk(self.phase(self.h(t)))

    def footfalls(self, t_from, t_to):
        """[(time, side, foot_point)] for every heel strike in [t_from, t_to]."""
        out = []
        h = self.h(t_from)
        j = math.floor(h) + 1
        t = t_from + (j - h) * self._dur(j - 1)
        for _ in range(200):
            if t > t_to or (self.t_stop is not None and t > self.t_stop + 1e-6):
                break
            side = "l" if j % 2 == 0 else "r"
            J = rig.solve(self._walk(self.phase(j + 1e-4)))
            out.append((t, side, J[side + "f"]))
            t += self._dur(j)
            j += 1
        return out


# ----------------------------------------------------------------------------- IK with the other elbow
def reach_out(p, side, target):
    """Like rig.reach, but bends the elbow the other way (outward/down) - e.g. a hand holding a
    match in front of the chest with the elbow out, instead of the arm folding across the body."""
    J = rig.solve(p)
    sl, sr = (p.facing, p.facing) if p.facing in (1, -1) else (1, -1)
    sign = sl if side == "l" else sr
    ua, eb = rig._ik(J["shoulder"], target, rig.SEG["upper"] * p.s, rig.SEG["fore"] * p.s, sign, knee=True)
    return p.copy(**{side + "a": ua, side + "e": -eb})        # forearm = upper + bend for arms


# ----------------------------------------------------------------------------- the witness's arm
def witness_arm(f, t, target_screen, rise=1.0, drop=0.0, tremble=1.0, jab=0.0, alpha=0.9,
                seed=41, blur=4.0, hand_base=(500.0, 1455.0)):
    """The witness's huge out-of-focus foreground arm (S01 design, screen space):
    shoulder below the bottom-right corner, forearm aimed at `target_screen`.
    tremble 0..1 scales the shake; jab 0..1 pushes the hand toward the target (the decisive point)."""
    if rise <= 0.001 or alpha <= 0:
        return
    tgt = target_screen
    shoulder = (1010.0, 2260.0)
    tr = (tremble * (10 * fbm1(t * 7.5, seed) + 4 * noise1(t * 21, seed + 2)),
          tremble * 8 * fbm1(t * 6.5, seed + 6))
    hand = (hand_base[0] + 0.2 * (tgt[0] - 540) + tr[0], hand_base[1] + tr[1])
    ux, uy = vnorm((tgt[0] - hand[0], tgt[1] - hand[1]))
    hand = (hand[0] + ux * 46 * jab, hand[1] + uy * 46 * jab)
    hand = (lerp(shoulder[0], hand[0], rise), lerp(shoulder[1], hand[1], rise) + 560 * drop)
    elbow = (hand[0] - ux * 300, hand[1] - uy * 300)
    with f.screen():
        with f.blurred(blur):
            draw.stroke(f, [shoulder, elbow, hand], 24.0, WHITE, alpha)


# ----------------------------------------------------------------------------- rain seen from above
def rain_top(f, t, n=170, seed=31, alpha=0.5, center=(540.0, 960.0), life=0.3, w=1.8, reach=1.0):
    """Rain seen from straight above (screen space): drops fall away from the camera, so their
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
            r0 = Rm * (0.22 + 0.78 * math.sqrt(hash01(seed, i, int(cyc), 3)))
            r = r0 * (1 - 0.55 * tau)
            L = 8 + 64 * (r / Rm) * (1 - tau)
            ux, uy = math.cos(a), math.sin(a)
            x1, y1 = cx + ux * r, cy + uy * r
            ctx.move_to(x1, y1)
            ctx.line_to(x1 - ux * L, y1 - uy * L)
        ctx.set_line_width(w)
        ctx.set_source_rgba(1, 1, 1, alpha)
        ctx.stroke()


# ----------------------------------------------------------------------------- motion streak
def _box_axis(arr, length, axis):
    """Continuous motion streak: centred box filter of `length` px along one axis (zero-filled)."""
    L = int(round(abs(length)))
    if L < 2:
        return arr
    n = arr.shape[axis]
    h = L // 2
    shape = list(arr.shape)
    shape[axis] = n + L + 1
    P = np.zeros(shape, np.float32)
    sl = [slice(None)] * arr.ndim
    sl[axis] = slice(h + 1, h + 1 + n)
    P[tuple(sl)] = arr
    C = np.cumsum(P, axis=axis, dtype=np.float32)
    hi = [slice(None)] * arr.ndim
    lo = [slice(None)] * arr.ndim
    hi[axis] = slice(L, L + n)
    lo[axis] = slice(0, n)
    return (C[tuple(hi)] - C[tuple(lo)]) / L


def _shift_avg(arr, dx, dy):
    """Average of arr smeared along (dx, dy) device px, zero-filled (no wrap)."""
    if abs(dx) < 0.5:
        return _box_axis(arr, dy, 0)
    if abs(dy) < 0.5:
        return _box_axis(arr, dx, 1)
    n = int(clamp(math.hypot(dx, dy) / 5.0, 6, 40))
    h, w = arr.shape[:2]
    acc = np.zeros(arr.shape, np.float32)
    for i in range(n):
        u = i / (n - 1) - 0.5
        ox, oy = int(round(dx * u)), int(round(dy * u))
        ys0, ys1 = max(0, -oy), min(h, h - oy)
        xs0, xs1 = max(0, -ox), min(w, w - ox)
        if ys1 > ys0 and xs1 > xs0:
            acc[ys0 + oy:ys1 + oy, xs0 + ox:xs1 + ox] += arr[ys0:ys1, xs0:xs1]
    return acc / n


@contextmanager
def streak(f, dx, dy):
    """Directional motion streak (screen px) for whip pans, drawn around everything inside.

    Replaces f.whip: Frame.finish() builds that streak with np.roll, which wraps content
    around the frame edges (a lamp glow at the top reappears at the bottom). Here the line
    layer and the glow layer are each smeared along (dx, dy) in float, zero-filled."""
    if abs(dx) + abs(dy) < 2.0:
        yield
        return
    f.ctx.push_group()
    f.g.push_group()
    try:
        yield
    finally:
        for c, (w, h), k in ((f.g, (f.gw, f.gh), f.scale * f.gw / f.pw), (f.ctx, (f.pw, f.ph), f.scale)):
            pat = c.pop_group()                     # restores the pre-push CTM == pattern matrix
            ctm = cairo.Matrix(*c.get_matrix())
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
            tc = cairo.Context(surf)
            tc.set_matrix(ctm)
            tc.set_source(pat)
            tc.paint()
            arr = _surface_to_array(surf).astype(np.float32)
            out = _array_to_surface(_shift_avg(arr, dx * k, dy * k))
            c.save()
            c.identity_matrix()
            c.set_source_surface(out, 0, 0)
            c.paint()
            c.restore()


# ----------------------------------------------------------------------------- the ring -> umbrella match cut
def umbrella_top_edge(c, R, rot=0.0, ribs=8):
    """Scalloped rim + rib tips of props.umbrella_top (identical geometry)."""
    tips = [(c[0] + math.cos(math.radians(rot + 360 * i / ribs)) * R,
             c[1] + math.sin(math.radians(rot + 360 * i / ribs)) * R) for i in range(ribs)]
    edge = []
    for i in range(ribs):
        a, b = tips[i], tips[(i + 1) % ribs]
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        mm = (m[0] + (c[0] - m[0]) * 0.10, m[1] + (c[1] - m[1]) * 0.10)
        edge += draw.bezier_pts(a, mm, mm, b, 5)[:-1]
    return edge, tips


def ring_to_umbrella(f, c, R, k, ring_r_screen=RING_R, ring_w_screen=RING_W, rot=0.0):
    """Morph a bare head ring (S16 OUT) into props.umbrella_top seen from above.
    k = 0: the ring exactly (radius / line width in screen px); k = 1: the real prop."""
    if k >= 1.0:
        props.umbrella_top(f, c, R, rot, WHITE)
        return
    z = f.cam.zoom
    edge, tips = umbrella_top_edge(c, R, rot)
    rr = ring_r_screen / z
    pts = []
    for p in edge:
        a = math.atan2(p[1] - c[1], p[0] - c[0])
        q = (c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr)
        pts.append(lerp(q, p, k))
    w0 = ring_w_screen / z ** 0.35                  # draw widths are "screen px at zoom 1"
    draw.stroke(f, pts, lerp(w0, 2.6, k), WHITE, 1.0, closed=True)
    for tp in tips:
        draw.line(f, c, lerp(c, tp, ease("out", k)), 1.8, WHITE, 0.7 * k)
    draw.circle(f, c, 3.0, 1, WHITE, k, fill_it=True)


# ----------------------------------------------------------------------------- one-point perspective street
class Persp:
    """A static one-point-perspective street drawn in world == screen coordinates.
    P(X, h, k): lateral X and height h (units at depth k = 1) at depth factor k (1 = near row,
    0 = the vanishing point). Things at depth k are drawn at scale k (figures at s0 * k)."""

    def __init__(self, vp, ground_y, s0):
        self.vp, self.yg, self.s0 = vp, ground_y - vp[1], s0

    def P(self, X, h, k):
        return (self.vp[0] + X * k, self.vp[1] + (self.yg - h) * k)

    def k_of_y(self, y):
        return (y - self.vp[1]) / self.yg


# ----------------------------------------------------------------------------- small fx
def puff(f, c, t, t0, seed=0, size=1.0, alpha=0.55):
    """A tiny impact puff: a few short curls that bloom and fade (smoke / dust)."""
    k = (t - t0) / 0.7
    if k <= 0 or k >= 1:
        return
    for i in range(5):
        a = -90 + (hash01(seed, i) - 0.5) * 150
        d = size * (6 + 22 * ease("out3", k)) * (0.6 + 0.6 * hash01(seed, i, 1))
        p = (c[0] + math.cos(math.radians(a)) * d, c[1] + math.sin(math.radians(a)) * d - 10 * size * k)
        r = size * (2.5 + 5 * k) * (0.7 + 0.5 * hash01(seed, i, 2))
        draw.arc(f, p, r, a - 120, a + 60, 1.4, WHITE, alpha * (1 - k) ** 1.5)


def black_rect(f, x, y, w, h):
    f.ctx.set_source_rgb(0, 0, 0)
    f.ctx.rectangle(x, y, w, h)
    f.ctx.fill()


def black_poly(f, pts):
    f.ctx.set_source_rgb(0, 0, 0)
    f.ctx.move_to(*pts[0])
    for p in pts[1:]:
        f.ctx.line_to(*p)
    f.ctx.close_path()
    f.ctx.fill()
