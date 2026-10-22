"""Shared helpers for SALVAGE s01 (red_line), s03 (descent) and s16 (sea_keeps).

Everything here is a pure function of its arguments (plus caches of deterministic data):
  * Sampled            cache an expensive function of time on a grid, interpolate between
  * hose_rope / draw_hose   the red air hose (physics.Rope with the bible's settings) and its
                       smooth filled band
  * fedora_pts         the client's fedora as a prop outline (costume._HATS), any yaw/tilt
  * helmet_valve       where the exhaust bubbles leave the Mark V helmet
  * line_band_pts      the Bass red line (bass.curl_pts) with an optional sag profile
  * crew               the 31 paper tick-figures hanging on the line (s01)
  * screen_glow        soft screen-space light pools (backlight behind a silhouette)
  * post_blend         interpolate Frame.post between a Bass setup and a live setup
"""
import bisect
import math

import cairo
import numpy as np

from engine import bass, costume, draw
from engine.core import H, W, clamp, hash01, lerp, noise1, smoothstep
from engine.palette import PAPER, RED, SALVAGE
from engine.physics import Rope

INK = SALVAGE.ink
D2R = math.pi / 180.0


# ----------------------------------------------------------------------------- time sampling
class Sampled:
    """fn(t) -> tuple/float sampled on [t0, t1] at `hz`, linearly interpolated (built lazily,
    once per process). Use it for things the rope simulation or a particle emitter asks for
    many times (a helmet point from an Actor skeleton)."""

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
    """Piecewise interpolation through [(t, value, ease_into_key)] (values: floats)."""
    from engine.core import ease
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            t0, v0 = keys[i - 1][0], keys[i - 1][1]
            t1, v1 = keys[i][0], keys[i][1]
            e = keys[i][2] if len(keys[i]) > 2 else "inout"
            return lerp(v0, v1, ease(e, (t - t0) / max(t1 - t0, 1e-9)))
    return keys[-1][1]


def integ(fn, a, b, n=48):
    """Simpson integral of fn over [a, b] (camera travel from a speed curve)."""
    if b == a:
        return 0.0
    if n % 2:
        n += 1
    h = (b - a) / n
    s = fn(a) + fn(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * fn(a + i * h)
    return s * h / 3.0


# ----------------------------------------------------------------------------- the red hose
HOSE_W = 10.0           # bible: ~10 px thick at zoom 1


def hose_rope(a, b, length, n=40, t0=-2.0, t1=20.0, current=None, collide=None, release=None,
              length_fn=None, init=None, gravity=(0.0, 60.0), drag=1.8, stiffness=0.3, iters=14):
    """The air hose as physics.Rope with the bible's settings (stiffness 0.3, gravity ~(0, 60),
    drag ~1.8, a current toward +x)."""
    cur = current if current is not None else (lambda t, x, y: (34.0 + 14.0 * math.sin(0.37 * t + y / 900.0), 0.0))
    return Rope(n, length, a, b, t0=t0, t1=t1, gravity=gravity, drag=drag, current=cur, collide=collide,
                release=release, length_fn=length_fn, iters=iters, stiffness=stiffness, init=init)


def draw_hose(ctx, pts, width=HOSE_W, color=RED, alpha=1.0):
    """The hose as one smooth filled band (a round-capped stroke of a Catmull-Rom curve)."""
    if len(pts) < 2:
        return
    ctx.save()
    ctx.new_path()
    if len(pts) >= 3:
        draw.smooth(ctx, pts, close=False, tension=0.5)
    else:
        draw.poly(ctx, pts, close=False)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*color[:3], alpha)
    ctx.stroke()
    ctx.restore()


def polyline_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def cut_polyline(pts, s0, s1):
    """Sub-polyline between arc lengths s0 < s1."""
    out = []
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L <= 1e-9:
            continue
        lo, hi = acc, acc + L
        if hi >= s0 and lo <= s1:
            u0 = clamp((s0 - lo) / L)
            u1 = clamp((s1 - lo) / L)
            pa = (lerp(a[0], b[0], u0), lerp(a[1], b[1], u0))
            pb = (lerp(a[0], b[0], u1), lerp(a[1], b[1], u1))
            if not out:
                out.append(pa)
            out.append(pb)
        acc = hi
    return out


# ----------------------------------------------------------------------------- diver helpers
def helmet_valve(sk):
    """World point just above the helmet's top valve (where the exhaust bubbles leave)."""
    c, R, vp, vr, inlet = costume.helmet_frame(sk)
    w = sk.side_w
    fwd = 1.0 if math.cos((sk.pose.yaw + sk.pose.head_yaw) * D2R) >= 0 else -1.0
    return (c[0] + fwd * R * 0.35 * (1 - w) - 0.18 * R * w, c[1] - R * 1.05)


def port_center(sk):
    """Centre of the helmet's front glass (the port the eyes glow through)."""
    c, R, vp, vr, inlet = costume.helmet_frame(sk)
    fwd = 1.0 if math.cos((sk.pose.yaw + sk.pose.head_yaw) * D2R) >= 0 else -1.0
    w = sk.side_w
    port_c = lerp((c[0] + fwd * R * 0.98, vp[1]), vp, w)
    return lerp(vp, port_c, 0.5), vr


# ----------------------------------------------------------------------------- the fedora prop
_FED_PROF, _FED_FRONT = costume._HATS["fedora"]
_FED_PIVOT = (0.0, 0.80)          # head units: middle of the brim


def fedora_pts(c, size, yaw=0.0, tilt=0.0):
    """The client's fedora as a world outline. c = middle of the brim (world), size = head
    height px (the client's ~86 at zoom 1), yaw: 0 = profile facing right, 90 = front,
    180 = profile facing left (blends like costume does), tilt: degrees (clockwise)."""
    w = abs(math.sin(yaw * D2R))
    fac = 1.0 if math.cos(yaw * D2R) >= 0 else -1.0
    ca, sa = math.cos(tilt * D2R), math.sin(tilt * D2R)
    out = []
    for (px, py), (qx, qy) in zip(_FED_PROF, _FED_FRONT):
        x = lerp(px * fac, qx, w) - _FED_PIVOT[0]
        y = -(lerp(py, qy, w) - _FED_PIVOT[1])          # head units, y down
        out.append((c[0] + (x * ca - y * sa) * size, c[1] + (x * sa + y * ca) * size))
    return out


def draw_fedora(ctx, c, size, yaw=0.0, tilt=0.0, color=INK, alpha=1.0):
    pts = fedora_pts(c, size, yaw, tilt)
    ctx.new_path()
    draw.poly(ctx, pts)
    ctx.set_source_rgba(*color[:3], alpha)
    ctx.fill()
    return pts


# ----------------------------------------------------------------------------- the Bass red line
def line_band_pts(c, length, width, u, rot=0.0, seed=0, n=160, up=True, sag=None, scale=1.0):
    """bass.curl_pts (a straight cut band that curls into a ring) plus: sag(x) -> dy added to
    the band while it is straight (u == 0), and a uniform scale about c."""
    polys = bass.curl_pts(c, length, width, u, rot=rot, seed=seed, n=n, up=up)
    if sag is not None and u <= 0.0:
        polys = [[(x, y + sag(x)) for x, y in P] for P in polys]
    if scale != 1.0:
        polys = [[(c[0] + (x - c[0]) * scale, c[1] + (y - c[1]) * scale) for x, y in P] for P in polys]
    return polys


def fill_polys(ctx, polys, color, alpha=1.0):
    bass.fill_polys(ctx, polys, color, alpha)


# ----------------------------------------------------------------------------- 31 crew cut-outs
def crew_layout(n=31, x0=74.0, x1=1006.0, seed=41):
    """The 31 men on the line: x, height, kind, flip, swing seed. The captain is last."""
    out = []
    kinds = ("man", "worker", "man", "man", "worker")
    for i in range(n):
        u = (i + 0.5) / n
        x = lerp(x0, x1, u) + 3.0 * (hash01(seed, i, 1) - 0.5)
        h = 63.0 + 7.0 * (hash01(seed, i, 2) - 0.5)
        kind = "captain" if i == n - 1 else kinds[int(hash01(seed, i, 3) * len(kinds)) % len(kinds)]
        if i == n - 1:
            h = 68.0
        out.append(dict(i=i, x=x, h=h, kind=kind, flip=hash01(seed, i, 4) < 0.5, seed=seed * 31 + i))
    return out


def draw_hanging_cutout(ctx, kind, peg, height, color, angle=0.0, scale=1.0, flip=False, seed=0, alpha=1.0):
    """A cut-out man hanging from `peg` (the top of his head), rotated by angle (deg) about
    the peg and scaled about it (pop-on)."""
    if scale <= 0.01:
        return
    ctx.save()
    ctx.translate(peg[0], peg[1])
    if angle:
        ctx.rotate(angle * D2R)
    ctx.scale(scale, scale)
    top = 103.0 if kind == "captain" else 100.0
    bass.draw_cutout(ctx, kind, (0.0, height * top / 100.0), height, color, seed=seed, flip=flip, alpha=alpha)
    ctx.restore()


# ----------------------------------------------------------------------------- light helpers
def screen_glow(f, c, r, color, a, par=0.0, blur=30.0, core=0.0):
    """A soft additive pool of light in SCREEN space (a backlight behind a silhouette)."""
    with f.light(par=par, blur=blur) as A:
        A.save()
        A.identity_matrix()
        A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
        draw.glow_disc(A, c, r, color, a, core)
        A.restore()


def screen_band(f, y0, y1, color, a0, a1, blur=0.0):
    """Additive vertical gradient band (screen space): a0 at y0 -> a1 at y1."""
    with f.light(par=0.0, blur=blur) as A:
        A.save()
        A.identity_matrix()
        A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
        draw.linear(A, (0, y0), (0, y1), [(0, color, a0), (1, color, a1)])
        A.rectangle(0, min(y0, y1), W, abs(y1 - y0))
        A.fill()
        A.restore()


# ----------------------------------------------------------------------------- post blending
BASS_POST = dict(paper=0.75, vignette=0.16, bloom=0.0, flicker=0.006, grain=0.045)


def post_blend(f, k, bass_post=None):
    """k = 1: Bass print (paper fibres, light vignette, no bloom); k = 0: the live defaults."""
    if k <= 0.0:
        return
    bp = bass_post or BASS_POST
    for key, v in bp.items():
        f.post[key] = lerp(f.post[key], v, clamp(k))


# ----------------------------------------------------------------------------- misc
def lerp2(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


def ss(a, b, x):
    return smoothstep(a, b, x)


def wobble(t, seed, amp=1.0, rate=0.3):
    return amp * noise1(t * rate, seed)
